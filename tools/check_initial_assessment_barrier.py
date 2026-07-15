#!/usr/bin/env python3
"""Fail-closed validation for five human pre-disclosure assessments.

This checker never authors an assessment and never dispatches a model.  It
opens and re-reads the human-supplied artifacts, then binds them to one exact
structurally complete producer cohort and its checker-owned eight-stage
handoffs.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any

from contract_validation import PathCustodyError, resolve_repo_path, validate_schema_subset
from promote_producer_structural_completion import (
    StructuralCompletionError,
    revalidate_producer_structural_completion,
)


ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT_SCHEMA = ROOT / "schema" / "topology-initial-assessment.schema.json"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
HUMAN_ID_RE = re.compile(r"human:[a-z0-9][a-z0-9._-]*")
UTC_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
STAGE_ORDER = (
    "stage-01-intake",
    "stage-02-layer-a-diagnostic-ir",
    "stage-03-routing-owner-gate",
    "stage-04-burden-execution-act",
    "stage-05-mrp-reread-terminal-state",
    "stage-06-field-witness-nar",
    "stage-07-release-output",
    "stage-08-verifier-sidecars",
)


class AssessmentBarrierError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class HeldArtifact:
    role: str
    ref: dict[str, object]
    path: Path
    raw: bytes
    value: object | None


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def record_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _code(role: str, suffix: str) -> str:
    return f"ASSESSMENT_{role.upper().replace('-', '_')}_{suffix}"


def _is_reparse(path: Path) -> bool:
    try:
        status = path.lstat()
    except OSError as exc:
        raise AssessmentBarrierError("ASSESSMENT_PATH_CUSTODY", f"cannot inspect {path}") from exc
    return path.is_symlink() or bool(getattr(status, "st_file_attributes", 0) & 0x400)


def _portable_relative_path(value: object, role: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise AssessmentBarrierError(_code(role, "PATH_CUSTODY"), "portable relative path required")
    windows = PureWindowsPath(value)
    parts = value.split("/")
    if (
        value.startswith("/")
        or windows.is_absolute()
        or bool(windows.drive)
        or any(part in {"", ".", ".."} for part in parts)
        or any(":" in part for part in parts)
    ):
        raise AssessmentBarrierError(_code(role, "PATH_CUSTODY"), "portable relative path required")
    return value


def _strict_json_object(raw: bytes, role: str) -> dict[str, object]:
    def reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise AssessmentBarrierError(
                    _code(role, "JSON_DUPLICATE_KEY"),
                    f"duplicate JSON key: {key}",
                )
            value[key] = item
        return value

    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=reject_duplicate_pairs,
        )
    except AssessmentBarrierError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AssessmentBarrierError(_code(role, "JSON_INVALID"), "strict UTF-8 JSON required") from exc
    if not isinstance(value, dict):
        raise AssessmentBarrierError(_code(role, "JSON_OBJECT_REQUIRED"), "JSON object required")
    return value


def _load_artifact(root: Path, ref: object, role: str, *, json_required: bool) -> HeldArtifact:
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256", "byte_count"}:
        raise AssessmentBarrierError(_code(role, "REF_SHAPE"), "path/hash/byte_count ref required")
    expected_hash = ref.get("sha256")
    expected_bytes = ref.get("byte_count")
    if not isinstance(expected_hash, str) or SHA256_RE.fullmatch(expected_hash) is None:
        raise AssessmentBarrierError(_code(role, "REF_HASH"), "SHA-256 ref required")
    if not isinstance(expected_bytes, int) or isinstance(expected_bytes, bool) or expected_bytes < 0:
        raise AssessmentBarrierError(_code(role, "REF_BYTES"), "nonnegative byte count required")
    relative = _portable_relative_path(ref.get("path"), role)
    custody_root = root.resolve(strict=True)
    try:
        path = resolve_repo_path(custody_root, relative, must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        raise AssessmentBarrierError(_code(role, "PATH_CUSTODY"), str(exc)) from exc
    if _is_reparse(custody_root):
        raise AssessmentBarrierError(_code(role, "PATH_CUSTODY"), "custody root is reparse/symlink")
    current = custody_root
    for part in relative.split("/"):
        current = current / part
        if current.exists() and _is_reparse(current):
            raise AssessmentBarrierError(_code(role, "PATH_CUSTODY"), "reparse/symlink component")
    raw = path.read_bytes()
    if len(raw) != expected_bytes or hashlib.sha256(raw).hexdigest() != expected_hash:
        raise AssessmentBarrierError(_code(role, "CONTENT_ADDRESS"), "artifact hash/length readback differs")
    value: object | None = None
    if json_required:
        value = _strict_json_object(raw, role)
    return HeldArtifact(role, copy.deepcopy(ref), path, raw, value)


def _assert_stable(held: list[HeldArtifact]) -> None:
    for artifact in held:
        try:
            raw = artifact.path.read_bytes()
        except OSError as exc:
            raise AssessmentBarrierError(_code(artifact.role, "READBACK_DRIFT"), "artifact vanished") from exc
        if raw != artifact.raw or hashlib.sha256(raw).hexdigest() != artifact.ref["sha256"]:
            raise AssessmentBarrierError(_code(artifact.role, "READBACK_DRIFT"), "artifact changed during validation")


def _parse_utc(value: object, role: str) -> datetime:
    if not isinstance(value, str) or UTC_RE.fullmatch(value) is None:
        raise AssessmentBarrierError(_code(role, "TIME"), "second-precision RFC3339 UTC time required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AssessmentBarrierError(_code(role, "TIME"), "valid RFC3339 UTC time required") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise AssessmentBarrierError(_code(role, "TIME"), "UTC offset required")
    return parsed


def _require_unique_ids(rows: object, field: str, role: str) -> None:
    if not isinstance(rows, list):
        raise AssessmentBarrierError(_code(role, "SET"), "array required")
    identities = [row.get(field) if isinstance(row, dict) else None for row in rows]
    if any(not isinstance(identity, str) or not identity for identity in identities) or len(identities) != len(set(identities)):
        raise AssessmentBarrierError(_code(role, "SET"), f"unique nonempty {field} values required")


def _validate_protocol(root: Path, completion: dict[str, Any], expected_cases: list[str], held: list[HeldArtifact]) -> str:
    protocol = _load_artifact(root, completion.get("review_protocol"), "REVIEW_PROTOCOL", json_required=True)
    held.append(protocol)
    value = protocol.value
    assert isinstance(value, dict)
    if protocol.ref["sha256"] != completion.get("review_protocol_sha256"):
        raise AssessmentBarrierError("ASSESSMENT_REVIEW_PROTOCOL_BINDING", "completion protocol hash/ref differ")
    if value.get("schema") != "daee-smoke-matrix-v1" or value.get("kind") != "review-protocol" or value.get("protocol_id") != "reviewed-five-smoke-v1":
        raise AssessmentBarrierError("ASSESSMENT_REVIEW_PROTOCOL_CONTRACT", "review protocol identity differs")
    if value.get("case_ids") != expected_cases:
        raise AssessmentBarrierError("ASSESSMENT_REVIEW_PROTOCOL_CASE_BINDING", "review protocol case order differs")
    controls = value.get("human_initial_assessment")
    if not isinstance(controls, dict) or controls.get("required_count") != 5 or controls.get("all_hash_claimed_before_cold_review") is not True or controls.get("cold_review_disclosure_forbidden_before_claim") is not True:
        raise AssessmentBarrierError("ASSESSMENT_REVIEW_PROTOCOL_CONTRACT", "human assessment disclosure controls differ")
    return str(protocol.ref["sha256"])


def _validate_handoff(value: object, case_id: str) -> None:
    if not isinstance(value, dict) or value.get("schema") != "staged-runtime-handshake-v1" or value.get("case_id") != case_id:
        raise AssessmentBarrierError("ASSESSMENT_STAGED_HANDOFF_BINDING", "handoff identity differs")
    if value.get("stage_order") != list(STAGE_ORDER):
        raise AssessmentBarrierError("ASSESSMENT_STAGED_HANDOFF_BINDING", "handoff stage order differs")
    stages = value.get("stages")
    if not isinstance(stages, list) or len(stages) != 8:
        raise AssessmentBarrierError("ASSESSMENT_STAGED_HANDOFF_BINDING", "exactly eight stages required")
    if [row.get("id") if isinstance(row, dict) else None for row in stages] != list(STAGE_ORDER):
        raise AssessmentBarrierError("ASSESSMENT_STAGED_HANDOFF_BINDING", "handoff stage identities differ")
    if any(not isinstance(row, dict) or row.get("status") != "pass" for row in stages):
        raise AssessmentBarrierError("ASSESSMENT_STAGED_HANDOFF_BINDING", "all eight handoff stages must pass")


def _validate_finalization(
    root: Path,
    completion: dict[str, Any],
    result: dict[str, Any],
    assessment: dict[str, Any],
    held: list[HeldArtifact],
) -> None:
    case_id = str(result["case_id"])
    if assessment.get("structural_finalization") != result.get("structural_finalization"):
        raise AssessmentBarrierError("ASSESSMENT_STRUCTURAL_FINALIZATION_BINDING", "assessment/result finalization refs differ")
    finalization = _load_artifact(root, assessment.get("structural_finalization"), f"{case_id}_STRUCTURAL_FINALIZATION", json_required=True)
    held.append(finalization)
    value = finalization.value
    assert isinstance(value, dict)
    if value.get("schema") != "daee-single-call-stage-finalization-v1" or value.get("verdict") != "SINGLE_CALL_STRUCTURAL_FINALIZATION_PASS":
        raise AssessmentBarrierError("ASSESSMENT_STRUCTURAL_FINALIZATION_CONTRACT", "passing finalization required")
    if value.get("case_id") != case_id or value.get("cycle_id") != completion.get("cycle_id"):
        raise AssessmentBarrierError("ASSESSMENT_STRUCTURAL_FINALIZATION_BINDING", "finalization case/cycle differs")
    candidate = value.get("bindings", {}).get("candidate") if isinstance(value.get("bindings"), dict) else None
    if not isinstance(candidate, dict) or candidate.get("candidate_id") != completion.get("candidate_id") or candidate.get("source_commit") != completion.get("source_commit"):
        raise AssessmentBarrierError("ASSESSMENT_STRUCTURAL_FINALIZATION_BINDING", "finalization candidate/source differs")
    capture = value.get("capture")
    checker_owned = value.get("checker_owned")
    if not isinstance(capture, dict) or not isinstance(checker_owned, dict):
        raise AssessmentBarrierError("ASSESSMENT_STRUCTURAL_FINALIZATION_CONTRACT", "capture/checker evidence unavailable")
    final_output = capture.get("stage07_output")
    if not isinstance(final_output, dict) or set(final_output) != {"path", "sha256", "byte_count", "start", "end"}:
        raise AssessmentBarrierError("ASSESSMENT_STRUCTURAL_FINALIZATION_CONTRACT", "Stage07 output offsets are unavailable")
    start = final_output.get("start")
    end = final_output.get("end")
    byte_count = final_output.get("byte_count")
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
        or not isinstance(byte_count, int)
        or end < start
        or end - start != byte_count
    ):
        raise AssessmentBarrierError("ASSESSMENT_STRUCTURAL_FINALIZATION_CONTRACT", "Stage07 output offsets/length differ")
    finalizer_raw_capture = capture.get("raw_envelope")
    if not isinstance(finalizer_raw_capture, dict) or set(finalizer_raw_capture) != {"path", "sha256", "byte_count"}:
        raise AssessmentBarrierError("ASSESSMENT_STRUCTURAL_FINALIZATION_CONTRACT", "finalizer raw capture ref is invalid")
    expected_refs = {
        "input": capture.get("raw_input"),
        "output": {key: final_output[key] for key in ("path", "sha256", "byte_count")},
        "staged_handoff": checker_owned.get("staged_handoff_record"),
    }
    for label, expected in expected_refs.items():
        if assessment.get(label) != expected:
            raise AssessmentBarrierError(f"ASSESSMENT_{label.upper()}_BINDING", f"assessment/finalization {label} refs differ")
    if result.get("output") != assessment.get("raw_capture"):
        raise AssessmentBarrierError("ASSESSMENT_RAW_CAPTURE_BINDING", "producer output is not the finalized raw envelope")
    if not isinstance(assessment.get("raw_capture"), dict) or any(
        assessment["raw_capture"].get(key) != finalizer_raw_capture.get(key)
        for key in ("sha256", "byte_count")
    ):
        raise AssessmentBarrierError("ASSESSMENT_RAW_CAPTURE_BINDING", "producer/finalizer raw capture content differs")
    input_binding = value.get("bindings", {}).get("input") if isinstance(value.get("bindings"), dict) else None
    if not isinstance(input_binding, dict) or input_binding != {
        "sha256": assessment["input"]["sha256"],
        "byte_count": assessment["input"]["byte_count"],
    }:
        raise AssessmentBarrierError("ASSESSMENT_INPUT_BINDING", "finalizer input binding differs")
    raw_capture = _load_artifact(root, assessment.get("raw_capture"), f"{case_id}_RAW_CAPTURE", json_required=False)
    finalizer_capture = _load_artifact(root, finalizer_raw_capture, f"{case_id}_FINALIZER_RAW_CAPTURE", json_required=False)
    raw_input = _load_artifact(root, assessment.get("input"), f"{case_id}_INPUT", json_required=False)
    output = _load_artifact(root, assessment.get("output"), f"{case_id}_OUTPUT", json_required=False)
    handoff = _load_artifact(root, assessment.get("staged_handoff"), f"{case_id}_STAGED_HANDOFF", json_required=True)
    held.extend((raw_capture, finalizer_capture, raw_input, output, handoff))
    if raw_capture.raw != finalizer_capture.raw:
        raise AssessmentBarrierError("ASSESSMENT_RAW_CAPTURE_BINDING", "producer/finalizer raw capture bytes differ")
    _validate_handoff(handoff.value, case_id)


def validate_initial_assessment_set(
    custody_root: Path,
    producer_completion: dict[str, Any],
    assessments: list[dict[str, object]],
    *,
    claimant: str,
    claimed_utc: str | None = None,
) -> dict[str, Any]:
    root = Path(os.path.abspath(custody_root))
    if not root.is_dir() or _is_reparse(root):
        raise AssessmentBarrierError("ASSESSMENT_PATH_CUSTODY", "regular custody root required")
    completion = producer_completion
    if completion.get("execution_mode") == "LIVE_CODEX" and completion.get("status") == "PRODUCER_STRUCTURAL_COMPLETE":
        try:
            completion = revalidate_producer_structural_completion(root, completion)
        except StructuralCompletionError as exc:
            raise AssessmentBarrierError("PRODUCER_STRUCTURAL_AGGREGATE_INVALID", str(exc)) from exc
    if completion.get("schema") != "reviewed-campaign-producer-completion-v1" or completion.get("status") != "PRODUCER_STRUCTURAL_COMPLETE":
        raise AssessmentBarrierError("PRODUCER_STRUCTURAL_COMPLETION_REQUIRED", "structural completion required")
    if completion.get("execution_mode") != "LIVE_CODEX" or completion.get("test_only") is not False:
        raise AssessmentBarrierError("ASSESSMENT_PRODUCTION_COMPLETION_REQUIRED", "live non-test structural completion required")
    results = completion.get("results")
    if not isinstance(results, list) or len(results) != 5:
        raise AssessmentBarrierError("PRODUCER_STRUCTURAL_COMPLETION_REQUIRED", "exactly five results required")
    if any(
        not isinstance(row, dict)
        or not isinstance(row.get("case_id"), str)
        or not row.get("case_id")
        or row.get("structural_status") != "PASS"
        or row.get("capture_status") != "CAPTURED"
        for row in results
    ):
        raise AssessmentBarrierError("PRODUCER_STRUCTURAL_COMPLETION_REQUIRED", "all five captured results must structurally pass")
    expected_cases = [str(row["case_id"]) for row in results]
    if len(set(expected_cases)) != 5:
        raise AssessmentBarrierError("ASSESSMENT_CASE_BINDING", "five unique producer cases required")
    held: list[HeldArtifact] = []
    protocol_sha = _validate_protocol(root, completion, expected_cases, held)
    if not isinstance(claimant, str) or HUMAN_ID_RE.fullmatch(claimant) is None:
        raise AssessmentBarrierError("HUMAN_CLAIMANT_IDENTITY", "canonical human:* identity required")
    if not isinstance(assessments, list) or len(assessments) != 5:
        raise AssessmentBarrierError("ASSESSMENT_COUNT", "exact five assessments required")
    if any(not isinstance(row, dict) or set(row) != {"case_id", "assessment"} for row in assessments):
        raise AssessmentBarrierError("ASSESSMENT_ARTIFACT_REQUIRED", "production rows require case_id plus assessment artifact ref")
    if [row["case_id"] for row in assessments] != expected_cases:
        raise AssessmentBarrierError("ASSESSMENT_CASE_BINDING", "assessment case order differs")
    claim_time_text = claimed_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    claim_time = _parse_utc(claim_time_text, "CLAIM")
    completion_sha = record_sha256(completion)
    schema = json.loads(ASSESSMENT_SCHEMA.read_text(encoding="utf-8", errors="strict"))
    assessment_ids: list[str] = []
    for result, row in zip(results, assessments):
        case_id = str(result["case_id"])
        artifact = _load_artifact(root, row["assessment"], f"{case_id}_ARTIFACT", json_required=True)
        held.append(artifact)
        value = artifact.value
        assert isinstance(value, dict)
        if value.get("schema") != "daee-topology-initial-assessment-v2":
            raise AssessmentBarrierError("ASSESSMENT_SCHEMA_V2_REQUIRED", "production assessment v2 required")
        issues = validate_schema_subset(value, schema)
        if issues:
            issue = issues[0]
            raise AssessmentBarrierError("ASSESSMENT_SCHEMA_INVALID", f"{issue.path}: {issue.message}")
        if value.get("candidate_id") != completion.get("candidate_id"):
            raise AssessmentBarrierError("ASSESSMENT_CANDIDATE_BINDING", "candidate differs")
        if value.get("source_commit") != completion.get("source_commit"):
            raise AssessmentBarrierError("ASSESSMENT_SOURCE_BINDING", "source commit differs")
        if value.get("case_id") != case_id or value.get("cycle_id") != completion.get("cycle_id"):
            raise AssessmentBarrierError("ASSESSMENT_CASE_CYCLE_BINDING", "case/cycle differs")
        if value.get("producer_completion_sha256") != completion_sha:
            raise AssessmentBarrierError("ASSESSMENT_PRODUCER_COMPLETION_BINDING", "producer completion hash differs")
        if value.get("review_protocol_sha256") != protocol_sha:
            raise AssessmentBarrierError("ASSESSMENT_REVIEW_PROTOCOL_BINDING", "review protocol hash differs")
        if value.get("reviewer_identity_or_accountable_role") != claimant:
            raise AssessmentBarrierError("ASSESSMENT_HUMAN_IDENTITY_BINDING", "one exact human must author all five")
        if value.get("relationship_to_producer") != "independent" or not str(value.get("independence_basis", "")).strip():
            raise AssessmentBarrierError("ASSESSMENT_INDEPENDENCE_BINDING", "independent relationship and basis required")
        if _parse_utc(value.get("recorded_utc"), f"{case_id}_RECORDED") > claim_time:
            raise AssessmentBarrierError("ASSESSMENT_TIME_ORDER", "assessment cannot postdate aggregate claim")
        if value.get("verdict") != "PASS":
            raise AssessmentBarrierError("ASSESSMENT_PASS_REQUIRED", "all five initial assessments must pass")
        findings = value.get("findings")
        if not isinstance(findings, list) or any(isinstance(item, dict) and item.get("severity") == "material" for item in findings):
            raise AssessmentBarrierError("ASSESSMENT_MATERIAL_FINDING_OPEN", "material finding prevents disclosure")
        _require_unique_ids(value.get("question_answers"), "question_id", f"{case_id}_QUESTION")
        _require_unique_ids(findings, "finding_id", f"{case_id}_FINDING")
        assessment_ids.append(str(value["assessment_id"]))
        _validate_finalization(root, completion, result, value, held)
    if len(assessment_ids) != len(set(assessment_ids)):
        raise AssessmentBarrierError("ASSESSMENT_ID_SET", "assessment IDs must be unique")
    _assert_stable(held)
    return {
        "candidate_id": completion["candidate_id"],
        "source_commit": completion["source_commit"],
        "cycle_id": completion["cycle_id"],
        "producer_completion_sha256": completion_sha,
        "review_protocol_sha256": protocol_sha,
        "human_claimant": claimant,
        "claimed_utc": claim_time_text,
        "assessments": copy.deepcopy(assessments),
        "count": 5,
    }


def revalidate_assessment_claim(
    custody_root: Path,
    producer_completion: dict[str, Any],
    claim: dict[str, Any],
) -> dict[str, Any]:
    required = {
        "schema", "status", "candidate_id", "source_commit", "cycle_id",
        "producer_completion_sha256", "review_protocol_sha256", "human_claimant",
        "claimed_utc", "assessments", "count", "cold_review_disclosure_permitted",
    }
    if set(claim) != required or claim.get("schema") != "reviewed-campaign-initial-assessment-claim-v2":
        raise AssessmentBarrierError("ASSESSMENT_CLAIM_SHAPE", "production aggregate claim v2 required")
    if claim.get("status") != "ALL_FIVE_INITIAL_ASSESSMENTS_HASH_CLAIMED" or claim.get("count") != 5 or claim.get("cold_review_disclosure_permitted") is not True:
        raise AssessmentBarrierError("ASSESSMENT_CLAIM_REQUIRED_BEFORE_DISCLOSURE", "passing aggregate claim required")
    validated = validate_initial_assessment_set(
        custody_root,
        producer_completion,
        claim.get("assessments"),
        claimant=claim.get("human_claimant"),
        claimed_utc=claim.get("claimed_utc"),
    )
    for key in (
        "candidate_id", "source_commit", "cycle_id", "producer_completion_sha256",
        "review_protocol_sha256", "human_claimant", "claimed_utc", "assessments", "count",
    ):
        if claim.get(key) != validated.get(key):
            raise AssessmentBarrierError("ASSESSMENT_CLAIM_BINDING", f"claim {key} differs from readback")
    return validated
