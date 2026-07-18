#!/usr/bin/env python3
"""Content-addressed live-capture bridge into the strict single-call finalizer."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping

import contract_validation
from credential_residue_scan_contract import valid_pass_credential_scan
import finalize_single_call_stage_capture as strict_finalizer


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "producer-capture-complete.schema.json"
RECORD_SUFFIX = ".producer-capture-complete.json"
SHA256_HEX = set("0123456789abcdef")


class CaptureFinalizationError(RuntimeError):
    """Fail-closed production capture/finalizer join error."""


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CaptureFinalizationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureFinalizationError(f"{label} is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise CaptureFinalizationError(f"{label} must be a JSON object")
    return value


def _schema() -> dict[str, Any]:
    return _parse_json(SCHEMA_PATH.read_bytes(), "producer capture schema")


def _validate_record_shape(payload: dict[str, Any]) -> None:
    issues = contract_validation.validate_schema_subset(payload, _schema())
    if issues:
        issue = issues[0]
        raise CaptureFinalizationError(
            f"capture record schema invalid at {issue.path}: {issue.keyword}: {issue.message}"
        )


def _relative_text(value: str | Path, label: str) -> str:
    raw = os.fspath(value)
    windows = PureWindowsPath(raw)
    native = Path(raw)
    if (
        not raw
        or "\x00" in raw
        or native.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or raw.startswith(("\\\\", "//"))
        or ".." in PureWindowsPath(raw.replace("/", "\\")).parts
    ):
        raise CaptureFinalizationError(f"{label} must be a contained repository-relative path")
    return raw


def _contained_existing(root: Path, value: str | Path, label: str) -> Path:
    try:
        return contract_validation.resolve_repo_path(
            root,
            _relative_text(value, label),
            must_exist=True,
            expect_file=True,
        )
    except (contract_validation.PathCustodyError, OSError) as exc:
        raise CaptureFinalizationError(f"{label} is outside retained file custody") from exc


def _contained_record_path(root: Path, value: str | Path) -> Path:
    candidate = Path(value)
    try:
        resolved = candidate.resolve(strict=True) if candidate.is_absolute() else _contained_existing(root, candidate, "record_path")
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise CaptureFinalizationError("record_path is outside retained repository custody") from exc
    if not resolved.is_file():
        raise CaptureFinalizationError("record_path is not a regular file")
    return resolved


def _stable_bytes(path: Path, label: str) -> bytes:
    try:
        first = path.read_bytes()
        second = path.read_bytes()
    except OSError as exc:
        raise CaptureFinalizationError(f"{label} cannot be read") from exc
    if first != second:
        raise CaptureFinalizationError(f"{label} changed during validation")
    return first


def _artifact_ref(root: Path, path: Path, raw: bytes | None = None) -> dict[str, object]:
    data = _stable_bytes(path, "artifact") if raw is None else raw
    try:
        relative = path.resolve(strict=True).relative_to(root).as_posix()
    except (OSError, ValueError) as exc:
        raise CaptureFinalizationError("artifact leaves repository custody") from exc
    return {"path": relative, "byte_count": len(data), "sha256": _sha256(data)}


def _load_ref(root: Path, ref: object, role: str) -> tuple[Path, bytes]:
    if not isinstance(ref, dict) or set(ref) != {"path", "byte_count", "sha256"}:
        raise CaptureFinalizationError(f"{role} artifact ref shape invalid")
    path_value = ref.get("path")
    byte_count = ref.get("byte_count")
    digest = ref.get("sha256")
    if (
        not isinstance(path_value, str)
        or not isinstance(byte_count, int)
        or isinstance(byte_count, bool)
        or byte_count < 0
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(char not in SHA256_HEX for char in digest)
    ):
        raise CaptureFinalizationError(f"{role} artifact ref values invalid")
    path = _contained_existing(root, path_value, role)
    raw = _stable_bytes(path, role)
    if len(raw) != byte_count or _sha256(raw) != digest:
        raise CaptureFinalizationError(f"{role} artifact custody mismatch")
    return path, raw


def _same_ref(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise CaptureFinalizationError(f"{label} artifact ref mismatch")


def _identity(value: Mapping[str, Any], payload: Mapping[str, Any], label: str, *, cycle_key: str) -> None:
    expected = {
        "candidate_id": payload["candidate_id"],
        "source_commit": payload["source_commit"],
        cycle_key: payload["cycle_id"],
        "case_id": payload["case_id"],
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise CaptureFinalizationError(f"{label} {key} mismatch")


def publish_capture_complete_record(
    *,
    root: Path,
    directory: str | Path,
    payload: Mapping[str, Any],
) -> Path:
    """Publish one immutable content-addressed per-case capture record."""

    source_root = root.resolve(strict=True)
    value = copy.deepcopy(dict(payload))
    _validate_record_shape(value)
    raw = _canonical(value)
    relative_dir = Path(_relative_text(directory, "directory"))
    try:
        target_dir = (source_root / relative_dir).resolve(strict=False)
        target_dir.relative_to(source_root)
    except (OSError, ValueError) as exc:
        raise CaptureFinalizationError("capture record directory leaves repository custody") from exc
    if target_dir.exists():
        if target_dir.is_symlink() or not target_dir.is_dir():
            raise CaptureFinalizationError("capture record directory is not a regular directory")
    else:
        parent = target_dir.parent.resolve(strict=True)
        try:
            parent.relative_to(source_root)
        except ValueError as exc:
            raise CaptureFinalizationError("capture record parent leaves repository custody") from exc
        target_dir.mkdir()
    target = target_dir / f"{_sha256(raw)}{RECORD_SUFFIX}"
    try:
        with target.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise CaptureFinalizationError("capture record already exists; replay is forbidden") from exc
    if _stable_bytes(target, "capture record readback") != raw:
        raise CaptureFinalizationError("capture record readback mismatch")
    return target


def _validated_inputs(root: Path, payload: dict[str, Any]) -> tuple[dict[str, bytes], dict[str, dict[str, Any]]]:
    refs = payload["refs"]
    raw: dict[str, bytes] = {}
    objects: dict[str, dict[str, Any]] = {}
    for role, ref in refs.items():
        _path, data = _load_ref(root, ref, role)
        raw[role] = data
        if role not in {"raw_input", "exact_prompt", "raw_output"}:
            objects[role] = _parse_json(data, role)

    completion = objects["producer_completion"]
    if (
        completion.get("schema") != "reviewed-campaign-producer-completion-v1"
        or completion.get("status") != "PRODUCER_CAPTURE_COMPLETE"
        or completion.get("execution_mode") != "LIVE_CODEX"
        or completion.get("test_only") is not False
        or completion.get("cold_review_authorized") is not False
    ):
        raise CaptureFinalizationError("producer completion is not an immutable live capture completion")
    for key in ("candidate_id", "source_commit", "cycle_id"):
        if completion.get(key) != payload[key]:
            raise CaptureFinalizationError(f"producer completion {key} mismatch")
    binding = payload["candidate_binding"]
    completion_binding = {
        "candidate_record_sha256": completion.get("package_record_sha256"),
        "candidate_maturity_sha256": completion.get("candidate_maturity_sha256"),
        "archive_sha256": completion.get("package_sha256"),
        "package_tree_sha256": completion.get("package_tree_sha256"),
    }
    for key, actual in completion_binding.items():
        if actual != binding.get(key):
            raise CaptureFinalizationError(f"producer completion candidate binding mismatch: {key}")
    results = completion.get("results")
    matches = [(index, row) for index, row in enumerate(results) if isinstance(row, dict) and row.get("case_id") == payload["case_id"]] if isinstance(results, list) else []
    if len(matches) != 1:
        raise CaptureFinalizationError("producer completion must contain exactly one selected case")
    result_index, result = matches[0]
    usage_reservation_shas = completion.get("producer_usage_reservation_sha256s")
    if (
        not isinstance(usage_reservation_shas, list)
        or len(usage_reservation_shas) != 5
        or len(set(usage_reservation_shas)) != 5
        or result_index >= len(usage_reservation_shas)
        or usage_reservation_shas[result_index] != payload["usage_reservation_sha256"]
    ):
        raise CaptureFinalizationError("producer completion usage reservation binding mismatch")
    if result.get("capture_status") != "CAPTURED" or result.get("structural_status") != "UNVERIFIED":
        raise CaptureFinalizationError("selected producer result is not unverified captured output")
    result_output = result.get("output")
    if (
        not isinstance(result_output, dict)
        or result_output.get("path") != f"producer/results/{payload['case_id']}.txt"
    ):
        raise CaptureFinalizationError("producer output locator mismatch")
    _result_output_path, result_output_raw = _load_ref(root, result_output, "producer output")
    if result_output_raw != raw["raw_output"]:
        raise CaptureFinalizationError("producer output bytes differ from captured raw output")
    _same_ref(result.get("capture_evidence"), refs["capture_evidence"], "producer capture evidence")
    _same_ref(result.get("provider_receipt"), refs["provider_receipt"], "producer provider receipt")
    if result.get("provider_receipt_sha256") != refs["provider_receipt"]["sha256"]:
        raise CaptureFinalizationError("producer provider receipt hash mismatch")

    capture = objects["capture_evidence"]
    if capture.get("schema") != "reviewed-campaign-live-capture-v1" or capture.get("status") != "CAPTURED":
        raise CaptureFinalizationError("capture evidence status invalid")
    _identity(capture, payload, "capture evidence", cycle_key="cycle_id") if "cycle_id" in capture else None
    for key in ("candidate_id", "source_commit", "case_id"):
        if capture.get(key) != payload[key]:
            raise CaptureFinalizationError(f"capture evidence {key} mismatch")
    for field, ref_role in (
        ("prompt", "exact_prompt"),
        ("raw_input", "raw_input"),
        ("runtime_context", "composite_runtime_context"),
        ("package_harness_parity", "package_harness_parity"),
        ("raw_output", "raw_output"),
        ("execution_custody", "execution_custody"),
    ):
        _same_ref(capture.get(field), refs[ref_role], f"capture evidence {field}")
    if capture.get("execution_custody_sha256") != refs["execution_custody"]["sha256"]:
        raise CaptureFinalizationError("capture execution custody hash mismatch")
    if capture.get("structural_status") != "UNVERIFIED":
        raise CaptureFinalizationError("capture evidence must remain structurally unverified")
    _path, credential_raw = _load_ref(root, capture.get("credential_residue_scan"), "credential_residue_scan")
    credential = _parse_json(credential_raw, "credential residue scan")
    expected_worker = f"producer-{result_index + 1:02d}"
    if (
        credential_raw != _canonical(credential)
        or not valid_pass_credential_scan(credential, expected_worker)
    ):
        raise CaptureFinalizationError("credential residue scan is not a valid bound PASS record")

    custody = objects["execution_custody"]
    if custody.get("schema") != "reviewed-campaign-execution-custody-v1" or custody.get("lane") != "producer":
        raise CaptureFinalizationError("execution custody lane invalid")
    _identity(custody, payload, "execution custody", cycle_key="cycle_or_review_batch_id")
    if custody.get("model") != "gpt-5.5" or custody.get("reasoning_effort") != "high":
        raise CaptureFinalizationError("execution custody model identity mismatch")
    if custody.get("usage_reservation_sha256") != payload["usage_reservation_sha256"]:
        raise CaptureFinalizationError("execution custody usage reservation mismatch")
    tooling_ref = custody.get("execution_tooling_manifest")
    if not isinstance(tooling_ref, dict) or set(tooling_ref) != {"path", "byte_count", "sha256"}:
        raise CaptureFinalizationError("execution custody tooling manifest ref invalid")
    expected_capture_bindings = {
        "raw_input": refs["raw_input"],
        "exact_prompt": refs["exact_prompt"],
        "composite_runtime_context": refs["composite_runtime_context"],
        "package_harness_parity": refs["package_harness_parity"],
    }
    if custody.get("capture_bindings") != expected_capture_bindings:
        raise CaptureFinalizationError("execution custody capture bindings mismatch")
    contract = custody.get("single_call_output_contract")
    if not isinstance(contract, dict):
        raise CaptureFinalizationError("execution custody output contract missing")
    expected_contract = {
        "schema": "daee-single-call-output-envelope-contract-v1",
        "envelope_nonce": payload["envelope_nonce"],
        "case_id": payload["case_id"],
        "cycle_id": payload["cycle_id"],
        "candidate_binding": payload["candidate_binding"],
        "input_binding": payload["input_binding"],
        "transport": "daee-single-call-stage-envelope-v1",
        "stage08_owner": "private-source-bound-checker",
    }
    if contract != expected_contract:
        raise CaptureFinalizationError("execution custody output contract mismatch")

    context = objects["composite_runtime_context"]
    if context.get("schema") != "daee-runtime-call-context-v1" or context.get("case_id") != payload["case_id"] or context.get("stage") != "01-08":
        raise CaptureFinalizationError("composite runtime context identity mismatch")
    runtime = context.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("source_commit") != payload["source_commit"]:
        raise CaptureFinalizationError("composite runtime context source mismatch")
    context_input = context.get("input")
    if not isinstance(context_input, dict) or context_input.get("sha256") != refs["raw_input"]["sha256"] or context_input.get("byte_count") != refs["raw_input"]["byte_count"]:
        raise CaptureFinalizationError("composite runtime context input mismatch")
    context_prompt = context.get("prompt")
    if not isinstance(context_prompt, dict) or context_prompt.get("sha256") != refs["exact_prompt"]["sha256"] or context_prompt.get("byte_count") != refs["exact_prompt"]["byte_count"]:
        raise CaptureFinalizationError("composite runtime context prompt mismatch")
    telemetry = context.get("budget_telemetry")
    if not isinstance(telemetry, dict) or not isinstance(telemetry.get("effective_context_limit"), int) or telemetry.get("effective_context_limit") < 1:
        raise CaptureFinalizationError("composite runtime context limit invalid")
    provider_settings = custody.get("provider_settings")
    command_timeout_seconds = (
        provider_settings.get("command_timeout_seconds")
        if isinstance(provider_settings, dict)
        else None
    )
    if (
        not isinstance(command_timeout_seconds, int)
        or isinstance(command_timeout_seconds, bool)
        or command_timeout_seconds < 1
    ):
        raise CaptureFinalizationError("authorization-bound command timeout invalid")
    if provider_settings.get("observation_protocol") != "concurrent-five-shared-deadline-v1":
        raise CaptureFinalizationError("authorization-bound concurrent observation protocol invalid")
    authorization_limit = (
        provider_settings.get("effective_context_limit_bytes")
        if isinstance(provider_settings, dict)
        else None
    )
    if (
        not isinstance(authorization_limit, int)
        or isinstance(authorization_limit, bool)
        or authorization_limit < 1
        or telemetry.get("effective_context_limit") != authorization_limit
        or not isinstance(telemetry.get("effective_context_bytes"), int)
        or telemetry.get("effective_context_bytes") > authorization_limit
    ):
        raise CaptureFinalizationError("authorization-bound context limit mismatch")
    if (
        runtime.get("package_sha256") != binding.get("package_tree_sha256")
        or runtime.get("skill_root_sha256") != binding.get("skill_sha256")
        or runtime.get("build_manifest_sha256") != binding.get("build_manifest_sha256")
    ):
        raise CaptureFinalizationError("composite runtime package binding mismatch")
    parity = objects["package_harness_parity"]
    if (
        parity.get("schema") != "daee-package-harness-parity-v1"
        or parity.get("classification") != "package-faithful"
        or parity.get("package_tree_sha256") != binding.get("package_tree_sha256")
    ):
        raise CaptureFinalizationError("package harness parity is not package-faithful")

    receipt = objects["provider_receipt"]
    for key, wanted in (
        ("candidate_id", payload["candidate_id"]),
        ("cycle_or_review_batch_id", payload["cycle_id"]),
        ("model", "gpt-5.5"),
        ("reasoning_effort", "high"),
        ("status", "COMPLETED"),
        ("terminal_transport_status", "COMPLETED"),
    ):
        if receipt.get(key) != wanted:
            raise CaptureFinalizationError(f"provider receipt {key} mismatch")
    if (
        receipt.get("subject_id") != f"producer:{payload['case_id']}"
        or receipt.get("case_id") not in {None, payload["case_id"]}
        or receipt.get("usage_reservation_sha256") != payload["usage_reservation_sha256"]
    ):
        raise CaptureFinalizationError("provider receipt case/subject/reservation mismatch")
    if capture.get("completion_identity", {}).get("provider_call_id") != receipt.get("provider_call_id"):
        raise CaptureFinalizationError("provider completion identity mismatch")

    if payload["input_binding"] != {"sha256": refs["raw_input"]["sha256"], "byte_count": refs["raw_input"]["byte_count"]}:
        raise CaptureFinalizationError("raw input binding mismatch")
    if binding.get("candidate_id") != payload["candidate_id"] or binding.get("source_commit") != payload["source_commit"]:
        raise CaptureFinalizationError("candidate binding identity mismatch")
    return raw, objects


def finalize_capture_complete_record(
    *,
    root: Path,
    record_path: str | Path,
    run_root: str | Path,
) -> strict_finalizer.FinalizedSingleCallCapture:
    """Revalidate one retained live capture and invoke only the strict deterministic core."""

    source_root = root.resolve(strict=True)
    validated = validate_capture_complete_record(root=source_root, record_path=record_path)
    payload = validated["payload"]
    record_ref = validated["record"]
    raw = validated["raw"]
    return strict_finalizer.finalize_single_call_stage_capture(
        root=source_root,
        run_root=run_root,
        raw_envelope=raw["raw_output"],
        raw_input=raw["raw_input"],
        expected_envelope_nonce=payload["envelope_nonce"],
        expected_case_id=payload["case_id"],
        expected_cycle_id=payload["cycle_id"],
        expected_candidate_binding=payload["candidate_binding"],
        expected_input_binding=payload["input_binding"],
        capture_complete_record=record_ref,
        capture_input_refs=copy.deepcopy(payload["refs"]),
        execution_tooling_manifest=copy.deepcopy(validated["execution_tooling_manifest"]),
    )


def validate_capture_complete_record(
    *,
    root: Path,
    record_path: str | Path,
) -> dict[str, Any]:
    """Reopen one per-case capture record and all of its retained input custody."""

    source_root = root.resolve(strict=True)
    held_record = _contained_record_path(source_root, record_path)
    record_raw = _stable_bytes(held_record, "capture complete record")
    payload = _parse_json(record_raw, "capture complete record")
    if _canonical(payload) != record_raw:
        raise CaptureFinalizationError("capture complete record is not canonical JSON")
    _validate_record_shape(payload)
    digest = _sha256(record_raw)
    if held_record.name != f"{digest}{RECORD_SUFFIX}":
        raise CaptureFinalizationError("capture complete record locator is not content-addressed")
    raw, objects = _validated_inputs(source_root, payload)
    tooling_ref = objects["execution_custody"]["execution_tooling_manifest"]
    return {
        "payload": copy.deepcopy(payload),
        "record": _artifact_ref(source_root, held_record, record_raw),
        "raw": {key: bytes(value) for key, value in raw.items()},
        "execution_tooling_manifest": copy.deepcopy(tooling_ref),
    }


__all__ = [
    "CaptureFinalizationError",
    "finalize_capture_complete_record",
    "publish_capture_complete_record",
    "validate_capture_complete_record",
    "strict_finalizer",
]
