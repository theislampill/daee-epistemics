#!/usr/bin/env python3
"""Create and revalidate one exact five-case producer structural completion.

The immutable live producer capture remains at ``producer/completion.json``.
This module only promotes five independently finalized per-case captures into a
separate create-once aggregate.  It performs no provider, assessment, review,
release, or owner-acceptance action.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

from contract_validation import PathCustodyError, resolve_repo_path, validate_schema_subset
from finalize_producer_capture_complete import CaptureFinalizationError, validate_capture_complete_record
import finalize_single_call_stage_capture as strict_finalizer


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "producer-structural-completion.schema.json"
CAPTURE_COMPLETION_PATH = "producer/completion.json"
STRUCTURAL_COMPLETION_PATH = "producer/structural-completion.json"
CANONICAL_CASE_IDS = (
    "gate88-secularism",
    "gate88-khaybar",
    "gate88-trinitarian-j173",
    "gate88-tst-lillard",
    "gate88-torah-quran-source-authentication",
)
NON_CLAIMS = {
    "not_human_pre_disclosure_assessment": True,
    "not_cold_review": True,
    "not_campaign_success": True,
    "not_release_or_owner_acceptance": True,
}
WINDOWS_DEVICES = {
    "CON", "PRN", "AUX", "NUL", "CLOCK$",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


class StructuralCompletionError(RuntimeError):
    """Fail-closed aggregate promotion or readback rejection."""


def _revalidate_live_producer_completion(
    root: Path,
    authorization_path: Path,
    completion: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
    # Lazy import avoids the deliberate assessment-barrier -> promotion edge
    # becoming a circular module-initialization dependency.
    import reviewed_campaign_orchestrator as campaign_orchestrator

    try:
        context = campaign_orchestrator.revalidate_live_producer_completion_context(
            root,
            authorization_path,
            completion,
        )
        auth = context["authorization"]
        finalizer_path = _regular_contained(
            root,
            auth["observation_finalizer_path"],
            "producer observation finalizer",
        )
        finalizer_raw = finalizer_path.read_bytes()
        if finalizer_path.read_bytes() != finalizer_raw:
            raise StructuralCompletionError("producer observation finalizer changed during readback")
        return context["completion"], {
            "authorization": auth,
            "authorization_sha256": context["authorization_sha256"],
            "bindings": context["bindings"],
            "output_contracts": context["producer_output_contracts"],
            "observation_finalizer": _artifact_ref(root, finalizer_path, finalizer_raw),
        }
    except campaign_orchestrator.CampaignError as exc:
        raise StructuralCompletionError(f"producer completion chain invalid: {exc}") from exc


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise StructuralCompletionError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _parse_json(raw: bytes, role: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StructuralCompletionError(f"{role} is not strict JSON") from exc
    if not isinstance(value, dict):
        raise StructuralCompletionError(f"{role} must be a JSON object")
    return value


def _portable_relative(value: object, role: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise StructuralCompletionError(f"{role} path is not canonical repository-relative text")
    if value.startswith("/") or value.endswith("/") or "//" in value:
        raise StructuralCompletionError(f"{role} path is not canonical repository-relative text")
    parts = value.split("/")
    for part in parts:
        stem = part.split(".", 1)[0].upper()
        if part in {"", ".", ".."} or ":" in part or part.endswith((".", " ")) or stem in WINDOWS_DEVICES:
            raise StructuralCompletionError(f"{role} path contains a forbidden component")
    return value


def _is_reparse(path: Path) -> bool:
    try:
        status = path.lstat()
    except OSError:
        return True
    attributes = getattr(status, "st_file_attributes", 0)
    return path.is_symlink() or bool(attributes & 0x400)


def _regular_contained(root: Path, relative: str, role: str, *, must_exist: bool = True) -> Path:
    canonical = _portable_relative(relative, role)
    try:
        path = resolve_repo_path(root, canonical, must_exist=must_exist, expect_file=must_exist)
    except PathCustodyError as exc:
        raise StructuralCompletionError(f"{role} path custody failure: {exc}") from exc
    if must_exist:
        cursor = root.resolve(strict=True)
        for part in canonical.split("/"):
            cursor = cursor / part
            if _is_reparse(cursor):
                raise StructuralCompletionError(f"{role} path contains a reparse point")
    return path


def _artifact_ref(root: Path, path: Path, raw: bytes) -> dict[str, object]:
    return {
        "path": path.resolve(strict=True).relative_to(root.resolve(strict=True)).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "byte_count": len(raw),
    }


def _load_ref(root: Path, ref: object, role: str, *, exact_path: str | None = None) -> tuple[Path, bytes]:
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256", "byte_count"}:
        raise StructuralCompletionError(f"{role} artifact ref shape invalid")
    relative = _portable_relative(ref.get("path"), role)
    if exact_path is not None and relative != exact_path:
        raise StructuralCompletionError(f"{role} locator substitution")
    path = _regular_contained(root, relative, role)
    first = path.read_bytes()
    second = path.read_bytes()
    if first != second:
        raise StructuralCompletionError(f"{role} changed during readback")
    if len(first) != ref.get("byte_count") or hashlib.sha256(first).hexdigest() != ref.get("sha256"):
        raise StructuralCompletionError(f"{role} content address mismatch")
    return path, first


def _schema() -> dict[str, Any]:
    return _parse_json(SCHEMA_PATH.read_bytes(), "producer structural completion schema")


def _validate_schema(value: dict[str, Any]) -> None:
    issues = validate_schema_subset(value, _schema())
    if issues:
        issue = issues[0]
        raise StructuralCompletionError(
            f"producer structural completion schema invalid at {issue.path}: {issue.keyword}: {issue.message}"
        )


def _capture_completion(
    root: Path,
    authorization_path: Path,
) -> tuple[dict[str, Any], dict[str, object], bytes, dict[str, object], dict[str, Any]]:
    path = _regular_contained(root, CAPTURE_COMPLETION_PATH, "producer capture completion")
    raw = path.read_bytes()
    value = _parse_json(raw, "producer capture completion")
    if raw != _canonical(value):
        raise StructuralCompletionError("producer capture completion must be canonical JSON")
    exact = {
        "schema": "reviewed-campaign-producer-completion-v1",
        "status": "PRODUCER_CAPTURE_COMPLETE",
        "execution_mode": "LIVE_CODEX",
        "test_only": False,
        "cold_review_authorized": False,
    }
    if any(value.get(key) != expected for key, expected in exact.items()):
        raise StructuralCompletionError("producer capture completion state invalid")
    for field in (
        "candidate_id", "source_commit", "cycle_id", "registry_sha256",
        "review_protocol", "review_protocol_sha256", "package_record_sha256",
        "candidate_maturity_sha256", "package_sha256", "package_tree_sha256",
        "authorization_sha256", "reservation_sha256", "settlement_sha256",
        "dispatch_manifest", "results",
    ):
        if field not in value:
            raise StructuralCompletionError(f"producer capture completion missing {field}")
    supplied_authorization = Path(authorization_path)
    authorization_absolute = Path(
        os.path.abspath(
            supplied_authorization
            if supplied_authorization.is_absolute()
            else root / supplied_authorization
        )
    )
    try:
        authorization_relative = authorization_absolute.relative_to(root.resolve(strict=True)).as_posix()
    except ValueError as exc:
        raise StructuralCompletionError("producer authorization escapes custody root") from exc
    held_authorization = _regular_contained(
        root,
        authorization_relative,
        "producer authorization",
    )
    authorization_raw = held_authorization.read_bytes()
    authorization_ref = _artifact_ref(root, held_authorization, authorization_raw)
    if value.get("authorization_sha256") != authorization_ref["sha256"]:
        raise StructuralCompletionError("producer completion authorization binding mismatch")
    revalidated, authority = _revalidate_live_producer_completion(
        root,
        held_authorization,
        value,
    )
    if revalidated != value or held_authorization.read_bytes() != authorization_raw:
        raise StructuralCompletionError("producer completion or authorization changed during validation")
    if (
        authority.get("authorization_sha256") != authorization_ref["sha256"]
        or authority.get("authorization", {}).get("candidate_id") != value["candidate_id"]
        or authority.get("authorization", {}).get("source_commit") != value["source_commit"]
    ):
        raise StructuralCompletionError("producer promotion authority differs from retained completion")
    return value, _artifact_ref(root, path, raw), raw, authorization_ref, authority


def _protocol_and_registry(
    root: Path,
    capture: dict[str, Any],
    authority: dict[str, Any],
) -> tuple[dict[str, object], dict[str, object], list[dict[str, Any]]]:
    auth = authority.get("authorization")
    if not isinstance(auth, dict):
        raise StructuralCompletionError("producer promotion authorization is unavailable")
    if capture.get("review_protocol") != auth.get("review_protocol"):
        raise StructuralCompletionError("review protocol differs from producer authorization")
    protocol_path, protocol_raw = _load_ref(root, auth.get("review_protocol"), "review protocol")
    protocol = _parse_json(protocol_raw, "review protocol")
    protocol_ref = _artifact_ref(root, protocol_path, protocol_raw)
    if protocol_ref["sha256"] != capture.get("review_protocol_sha256"):
        raise StructuralCompletionError("review protocol hash binding mismatch")
    if (
        protocol.get("schema") != "daee-smoke-matrix-v1"
        or protocol.get("kind") != "review-protocol"
        or protocol.get("protocol_id") != "reviewed-five-smoke-v1"
        or protocol.get("case_ids") != list(CANONICAL_CASE_IDS)
    ):
        raise StructuralCompletionError("review protocol canonical case binding mismatch")
    authorized_registry = auth.get("registry")
    if not isinstance(authorized_registry, dict):
        raise StructuralCompletionError("authorized input registry ref is unavailable")
    embedded_registry = protocol.get("input_registry")
    if (
        not isinstance(embedded_registry, dict)
        or set(embedded_registry) not in ({"path", "sha256"}, {"path", "sha256", "byte_count"})
        or embedded_registry.get("path") != authorized_registry.get("path")
        or embedded_registry.get("sha256") != authorized_registry.get("sha256")
    ):
        raise StructuralCompletionError("review protocol input registry differs from authorization")
    registry_path, registry_raw = _load_ref(root, authorized_registry, "input registry")
    registry = _parse_json(registry_raw, "input registry")
    registry_ref = _artifact_ref(root, registry_path, registry_raw)
    cases = registry.get("cases")
    if (
        registry.get("schema") != "daee-smoke-matrix-v1"
        or registry.get("kind") != "input-registry"
        or registry_ref["sha256"] != capture.get("registry_sha256")
        or not isinstance(cases, list)
        or [row.get("case_id") if isinstance(row, dict) else None for row in cases] != list(CANONICAL_CASE_IDS)
    ):
        raise StructuralCompletionError("input registry canonical case binding mismatch")
    return protocol_ref, registry_ref, cases


def _validate_finalization(
    root: Path,
    ref: object,
    *,
    case_id: str,
    capture: dict[str, Any],
    capture_record: dict[str, Any],
    capture_record_ref: dict[str, object],
    capture_tooling_manifest: dict[str, object],
    raw_result: dict[str, Any],
    registry_case: dict[str, Any],
    authority: dict[str, Any],
) -> dict[str, object]:
    path, raw = _load_ref(root, ref, f"{case_id} structural finalization")
    value = _parse_json(raw, f"{case_id} structural finalization")
    if (
        value.get("schema") != "daee-single-call-stage-finalization-v1"
        or value.get("verdict") != "SINGLE_CALL_STRUCTURAL_FINALIZATION_PASS"
        or value.get("case_id") != case_id
        or value.get("cycle_id") != capture["cycle_id"]
    ):
        raise StructuralCompletionError(f"{case_id} finalization identity or verdict mismatch")
    bindings = value.get("bindings")
    if not isinstance(bindings, dict):
        raise StructuralCompletionError(f"{case_id} finalization bindings missing")
    candidate = bindings.get("candidate")
    output_contracts = authority.get("output_contracts")
    output_contract = output_contracts.get(case_id) if isinstance(output_contracts, dict) else None
    authoritative_candidate = (
        output_contract.get("candidate_binding")
        if isinstance(output_contract, dict)
        else None
    )
    if (
        not isinstance(candidate, dict)
        or candidate.get("candidate_id") != capture["candidate_id"]
        or candidate.get("source_commit") != capture["source_commit"]
        or candidate != capture_record.get("candidate_binding")
        or candidate != authoritative_candidate
    ):
        raise StructuralCompletionError(f"{case_id} finalization candidate/source mismatch")
    if (
        bindings.get("input") != capture_record.get("input_binding")
        or not isinstance(output_contract, dict)
        or bindings.get("input") != output_contract.get("input_binding")
        or value.get("envelope_nonce") != output_contract.get("envelope_nonce")
        or capture_record.get("envelope_nonce") != output_contract.get("envelope_nonce")
    ):
        raise StructuralCompletionError(f"{case_id} finalization input binding mismatch")
    if bindings.get("capture_complete_record") != capture_record_ref:
        raise StructuralCompletionError(f"{case_id} finalization capture-record crosslink mismatch")
    if bindings.get("capture_input_refs") != capture_record.get("refs"):
        raise StructuralCompletionError(f"{case_id} finalization capture-input refs mismatch")
    auth = authority.get("authorization")
    authorized_tooling_manifest = auth.get("execution_tooling_manifest") if isinstance(auth, dict) else None
    if (
        not isinstance(capture_tooling_manifest, dict)
        or capture_tooling_manifest != authorized_tooling_manifest
        or bindings.get("execution_tooling_manifest") != authorized_tooling_manifest
    ):
        raise StructuralCompletionError(f"{case_id} execution-tooling manifest binding mismatch")
    captured = value.get("capture")
    refs = capture_record["refs"]
    retained_envelope = captured.get("raw_envelope") if isinstance(captured, dict) else None
    if (
        not isinstance(retained_envelope, dict)
        or any(
            retained_envelope.get(key) != refs["raw_output"].get(key)
            for key in ("sha256", "byte_count")
        )
    ):
        raise StructuralCompletionError(f"{case_id} finalization raw output mismatch")
    retained_input = captured.get("raw_input") if isinstance(captured, dict) else None
    if (
        not isinstance(retained_input, dict)
        or any(
            retained_input.get(key) != refs["raw_input"].get(key)
            for key in ("sha256", "byte_count")
        )
    ):
        raise StructuralCompletionError(f"{case_id} finalization raw input mismatch")
    result_output = raw_result.get("output")
    if (
        not isinstance(result_output, dict)
        or any(
            result_output.get(key) != refs["raw_output"].get(key)
            for key in ("sha256", "byte_count")
        )
    ):
        raise StructuralCompletionError(f"{case_id} producer/finalizer output mismatch")
    if (
        registry_case.get("raw_sha256") != refs["raw_input"]["sha256"]
        or registry_case.get("raw_bytes") != refs["raw_input"]["byte_count"]
    ):
        raise StructuralCompletionError(f"{case_id} registry input binding mismatch")
    expected_finalization_path = (
        f"{auth.get('structural_evidence_root')}/finalized/{case_id}/structural-finalization.json"
        if isinstance(auth, dict)
        else None
    )
    if ref.get("path") != expected_finalization_path:
        raise StructuralCompletionError(f"{case_id} structural finalization locator is not authorized")
    try:
        revalidated = strict_finalizer.revalidate_single_call_stage_capture(
            root=root,
            finalization_ref=ref,
            expected_case_id=case_id,
            expected_cycle_id=capture["cycle_id"],
            expected_candidate_binding=candidate,
            expected_input_binding=capture_record["input_binding"],
            expected_capture_complete_record=capture_record_ref,
            expected_capture_input_refs=capture_record["refs"],
            expected_execution_tooling_manifest=authorized_tooling_manifest,
        )
    except strict_finalizer.FinalizationError as exc:
        raise StructuralCompletionError(f"{case_id} retained Stage01-08 finalization invalid: {exc}") from exc
    if revalidated != value:
        raise StructuralCompletionError(f"{case_id} finalization dependency readback mismatch")
    return _artifact_ref(root, path, raw)


def _derive(
    root: Path,
    rows: object,
    authorization_path: Path,
) -> tuple[dict[str, Any], bytes]:
    capture, capture_ref, capture_raw, authorization_ref, authority = _capture_completion(
        root,
        authorization_path,
    )
    protocol_ref, registry_ref, registry_cases = _protocol_and_registry(root, capture, authority)
    raw_results = capture.get("results")
    if (
        not isinstance(raw_results, list)
        or len(raw_results) != 5
        or [row.get("case_id") if isinstance(row, dict) else None for row in raw_results] != list(CANONICAL_CASE_IDS)
        or any(
            not isinstance(row, dict)
            or row.get("capture_status") != "CAPTURED"
            or row.get("structural_status") != "UNVERIFIED"
            for row in raw_results
        )
    ):
        raise StructuralCompletionError("producer capture result set is not the exact canonical five")
    if not isinstance(rows, list) or len(rows) != 5:
        raise StructuralCompletionError("exactly five structural completion rows required")
    if any(not isinstance(row, dict) or set(row) != {"case_id", "capture_record", "structural_finalization"} for row in rows):
        raise StructuralCompletionError("structural completion row shape invalid")
    case_ids = [row["case_id"] for row in rows]
    if case_ids != list(CANONICAL_CASE_IDS) or len(set(case_ids)) != 5:
        raise StructuralCompletionError("structural completion rows differ from canonical case order")

    promoted_results: list[dict[str, Any]] = []
    for index, (row, raw_result, registry_case) in enumerate(zip(rows, raw_results, registry_cases), 1):
        case_id = str(row["case_id"])
        record_value = row["capture_record"]
        record_locator = record_value.get("path") if isinstance(record_value, dict) else None
        if (
            not isinstance(record_locator, str)
            or not record_locator.startswith("producer/capture-records/")
            or not record_locator.endswith(".producer-capture-complete.json")
        ):
            raise StructuralCompletionError(f"{case_id} capture record locator is not canonical")
        try:
            validated = validate_capture_complete_record(root=root, record_path=row["capture_record"]["path"])
        except (CaptureFinalizationError, KeyError, TypeError) as exc:
            raise StructuralCompletionError(f"{case_id} capture record invalid: {exc}") from exc
        record_ref = validated.get("record")
        payload = validated.get("payload")
        if record_ref != row["capture_record"] or not isinstance(payload, dict):
            raise StructuralCompletionError(f"{case_id} capture record ref substitution")
        if (
            payload.get("case_id") != case_id
            or payload.get("candidate_id") != capture["candidate_id"]
            or payload.get("source_commit") != capture["source_commit"]
            or payload.get("cycle_id") != capture["cycle_id"]
            or payload.get("refs", {}).get("producer_completion") != capture_ref
        ):
            raise StructuralCompletionError(f"{case_id} capture record identity mismatch")
        refs = payload["refs"]
        if (
            raw_result.get("capture_evidence") != refs["capture_evidence"]
            or raw_result.get("provider_receipt") != refs["provider_receipt"]
            or raw_result.get("provider_receipt_sha256") != refs["provider_receipt"]["sha256"]
        ):
            raise StructuralCompletionError(f"{case_id} raw capture refs differ")
        finalization_ref = _validate_finalization(
            root,
            row["structural_finalization"],
            case_id=case_id,
            capture=capture,
            capture_record=payload,
            capture_record_ref=record_ref,
            capture_tooling_manifest=validated.get("execution_tooling_manifest"),
            raw_result=raw_result,
            registry_case=registry_case,
            authority=authority,
        )
        if finalization_ref != row["structural_finalization"]:
            raise StructuralCompletionError(f"{case_id} finalization ref substitution")
        promoted_results.append(
            {
                "case_id": case_id,
                "capture_status": "CAPTURED",
                "structural_status": "PASS",
                "output": copy.deepcopy(raw_result["output"]),
                "capture_evidence": copy.deepcopy(raw_result["capture_evidence"]),
                "provider_receipt": copy.deepcopy(raw_result["provider_receipt"]),
                "provider_receipt_sha256": raw_result["provider_receipt_sha256"],
                "capture_record": copy.deepcopy(record_ref),
                "structural_finalization": copy.deepcopy(finalization_ref),
            }
        )

    aggregate = {
        "schema": "reviewed-campaign-producer-completion-v1",
        "kind": "producer-structural-completion-aggregate",
        "status": "PRODUCER_STRUCTURAL_COMPLETE",
        "execution_mode": "LIVE_CODEX",
        "test_only": False,
        "candidate_id": capture["candidate_id"],
        "source_commit": capture["source_commit"],
        "cycle_id": capture["cycle_id"],
        "capture_completion": capture_ref,
        "producer_authorization": authorization_ref,
        "observation_finalizer": copy.deepcopy(authority["observation_finalizer"]),
        "input_registry": registry_ref,
        "registry_sha256": capture["registry_sha256"],
        "review_protocol": protocol_ref,
        "review_protocol_sha256": capture["review_protocol_sha256"],
        "package_record_sha256": capture["package_record_sha256"],
        "candidate_maturity_sha256": capture["candidate_maturity_sha256"],
        "package_sha256": capture["package_sha256"],
        "package_tree_sha256": capture["package_tree_sha256"],
        "authorization_sha256": capture["authorization_sha256"],
        "reservation_sha256": capture["reservation_sha256"],
        "settlement_sha256": capture["settlement_sha256"],
        "dispatch_manifest": copy.deepcopy(capture["dispatch_manifest"]),
        "case_ids": list(CANONICAL_CASE_IDS),
        "results": promoted_results,
        "cold_review_authorized": False,
        "non_claims": copy.deepcopy(NON_CLAIMS),
    }
    _validate_schema(aggregate)
    return aggregate, capture_raw


def create_producer_structural_completion(
    custody_root: Path,
    rows: list[dict[str, object]],
    authorization_path: Path,
) -> dict[str, Any]:
    """Exclusively publish one aggregate after two complete stable read passes."""

    root = Path(os.path.abspath(custody_root)).resolve(strict=True)
    if not root.is_dir() or _is_reparse(root):
        raise StructuralCompletionError("custody root must be a regular directory")
    target = _regular_contained(root, STRUCTURAL_COMPLETION_PATH, "producer structural completion", must_exist=False)
    if target.exists():
        raise StructuralCompletionError("producer structural completion already exists; collision or replay forbidden")
    aggregate, capture_raw = _derive(
        root,
        copy.deepcopy(rows),
        authorization_path,
    )
    stable_aggregate, stable_capture_raw = _derive(
        root,
        copy.deepcopy(rows),
        authorization_path,
    )
    if stable_aggregate != aggregate or stable_capture_raw != capture_raw:
        raise StructuralCompletionError("promotion inputs changed before publication")
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = _canonical(aggregate)
    try:
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise StructuralCompletionError("producer structural completion collision or replay") from exc
    with os.fdopen(fd, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
        created_stat = os.fstat(handle.fileno())
        owned_identity = (created_stat.st_dev, created_stat.st_ino, created_stat.st_ctime_ns)
    try:
        if target.read_bytes() != raw:
            raise StructuralCompletionError("producer structural completion readback mismatch")
        if _regular_contained(root, CAPTURE_COMPLETION_PATH, "producer capture completion").read_bytes() != capture_raw:
            raise StructuralCompletionError("raw producer capture completion changed during promotion")
        return revalidate_producer_structural_completion(
            root,
            aggregate,
        )
    except BaseException as exc:
        try:
            if not target.exists():
                raise
            target_stat = target.lstat()
            target_identity = (target_stat.st_dev, target_stat.st_ino, target_stat.st_ctime_ns)
            if (
                _is_reparse(target)
                or not stat.S_ISREG(target_stat.st_mode)
                or target_identity != owned_identity
                or target.read_bytes() != raw
            ):
                raise StructuralCompletionError(
                    "post-publication validation failed and exact owned rollback is unsafe"
                ) from exc
            target.unlink()
            if target.exists():
                raise StructuralCompletionError(
                    "post-publication validation failed and exact owned rollback did not complete"
                ) from exc
        except StructuralCompletionError:
            raise
        except OSError as rollback_exc:
            raise StructuralCompletionError(
                "post-publication validation failed and exact owned rollback failed"
            ) from rollback_exc
        raise


def revalidate_producer_structural_completion(
    custody_root: Path,
    completion: dict[str, Any],
) -> dict[str, Any]:
    """Reopen the aggregate and all five capture/finalization dependency chains."""

    root = Path(os.path.abspath(custody_root)).resolve(strict=True)
    _validate_schema(completion)
    path = _regular_contained(root, STRUCTURAL_COMPLETION_PATH, "producer structural completion")
    raw = path.read_bytes()
    retained = _parse_json(raw, "producer structural completion")
    if raw != _canonical(retained) or retained != completion:
        raise StructuralCompletionError("producer structural completion exact readback mismatch")
    rows = [
        {
            "case_id": row["case_id"],
            "capture_record": row["capture_record"],
            "structural_finalization": row["structural_finalization"],
        }
        for row in retained["results"]
    ]
    expected, _capture_raw = _derive(
        root,
        rows,
        root / retained["producer_authorization"]["path"],
    )
    if retained != expected:
        raise StructuralCompletionError("producer structural completion differs from dependency readback")
    return copy.deepcopy(retained)


__all__ = [
    "CANONICAL_CASE_IDS",
    "CAPTURE_COMPLETION_PATH",
    "STRUCTURAL_COMPLETION_PATH",
    "StructuralCompletionError",
    "create_producer_structural_completion",
    "revalidate_producer_structural_completion",
]
