#!/usr/bin/env python3
"""Deterministically finalize one exact single-call staged capture.

This module performs no provider call.  It retains the model-authored envelope
unchanged, derives checker-owned Stage 07/08 evidence, and emits a structural
handoff record.  A passing result is not a semantic-truth, campaign, human
assessment, cold-review, release, or owner-acceptance claim.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping

import checker_execution_snapshot as checker_snapshot
from contract_validation import PathCustodyError, resolve_repo_path
import execution_tooling_manifest as tooling_manifest
import build_b5_full_ir_projection_sidecar as b5_sidecar
import build_retained_proof_sidecars as retained_sidecars
import check_staged_runtime_handshake as handshake
import run_staged_current_skill_smoke as stage_runner
import single_call_stage_envelope as stage_envelope


ROOT = Path(__file__).resolve().parents[1]
STAGE_ORDER = tuple(stage_runner.STAGE_ORDER)
FINALIZATION_VERDICT = "SINGLE_CALL_STRUCTURAL_FINALIZATION_PASS"
FINALIZATION_NON_CLAIMS = {
    "not_semantic_truth": True,
    "not_campaign_success": True,
    "not_human_pre_disclosure_assessment": True,
    "not_cold_review": True,
    "not_release_or_owner_acceptance": True,
}
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
NONCE_RE = re.compile(r"^[a-f0-9]{32}$")


class FinalizationError(RuntimeError):
    """Fail-closed error with a stable machine-facing reason code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class FinalizedSingleCallCapture:
    run_root: Path
    stage07_path: Path
    stage08_path: Path
    record_path: Path
    finalization_path: Path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Any) -> str:
    raw = (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return _sha256(raw)


def _repo_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve(strict=True).relative_to(root.resolve(strict=True)).as_posix()
    except (OSError, ValueError) as exc:
        raise FinalizationError("path-custody", f"artifact is not retained under the repository: {path}") from exc


def _artifact(path: Path, root: Path, *, data: bytes | None = None) -> dict[str, Any]:
    captured = path.read_bytes() if data is None else data
    if path.read_bytes() != captured:
        raise FinalizationError("artifact-drift", f"artifact changed during readback: {_repo_relative(path, root)}")
    return {
        "path": _repo_relative(path, root),
        "sha256": _sha256(captured),
        "byte_count": len(captured),
    }


def _write_exact(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise FinalizationError("artifact-exists", f"refusing to overwrite retained artifact: {path}") from exc
    except OSError as exc:
        raise FinalizationError("artifact-write", f"cannot retain artifact {path}: {exc}") from exc
    if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
        raise FinalizationError("artifact-readback", f"exact-byte readback failed: {path}")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _sorted_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _matches_text_writer_json(raw: bytes, value: Any, *, sort_keys: bool) -> bool:
    canonical = _sorted_json_bytes(value) if sort_keys else _json_bytes(value)
    return raw in {canonical, canonical.replace(b"\n", b"\r\n")}


def _write_json(path: Path, value: Any) -> bytes:
    raw = _json_bytes(value)
    _write_exact(path, raw)
    try:
        readback = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FinalizationError("artifact-readback", f"JSON readback failed for {path}: {exc}") from exc
    if readback != value:
        raise FinalizationError("artifact-readback", f"JSON value drifted during readback: {path}")
    return raw


def _assert_exact_file(path: Path, expected: bytes, *, code: str) -> None:
    try:
        actual = path.read_bytes()
    except OSError as exc:
        raise FinalizationError(code, f"cannot read retained file {path}: {exc}") from exc
    if path.is_symlink() or actual != expected or _sha256(actual) != _sha256(expected):
        raise FinalizationError(code, f"retained exact bytes changed: {path}")


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise FinalizationError("retained-json", f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _strict_json_value(raw: bytes, role: str) -> Any:
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_pairs,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FinalizationError("retained-json", f"{role} is not strict UTF-8 JSON") from exc
    return value


def _strict_json(raw: bytes, role: str) -> dict[str, Any]:
    value = _strict_json_value(raw, role)
    if not isinstance(value, dict):
        raise FinalizationError("retained-json", f"{role} must be one JSON object")
    return value


def _is_reparse(path: Path) -> bool:
    try:
        status = path.lstat()
    except OSError:
        return True
    return path.is_symlink() or bool(getattr(status, "st_file_attributes", 0) & 0x400)


def _portable_retained_path(value: object, role: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise FinalizationError("retained-path", f"{role} path is not portable relative text")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if (
        value.startswith("/")
        or value.endswith("/")
        or "//" in value
        or posix.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or any(part in {"", ".", ".."} or ":" in part or part.endswith((".", " ")) for part in posix.parts)
    ):
        raise FinalizationError("retained-path", f"{role} path is not portable relative text")
    return value


def _retained_ref(
    root: Path,
    value: object,
    role: str,
    *,
    expected_path: str | None = None,
    extra_keys: tuple[str, ...] = (),
) -> tuple[Path, bytes]:
    expected_keys = {"path", "sha256", "byte_count", *extra_keys}
    if not isinstance(value, Mapping) or set(value) != expected_keys:
        raise FinalizationError("retained-ref", f"{role} artifact reference shape is invalid")
    relative = _portable_retained_path(value.get("path"), role)
    if expected_path is not None and relative != expected_path:
        raise FinalizationError("retained-ref", f"{role} artifact locator substitution")
    byte_count = value.get("byte_count")
    digest = value.get("sha256")
    if (
        not isinstance(byte_count, int)
        or isinstance(byte_count, bool)
        or byte_count < 0
        or not isinstance(digest, str)
        or SHA256_RE.fullmatch(digest) is None
    ):
        raise FinalizationError("retained-ref", f"{role} artifact address is invalid")
    try:
        path = resolve_repo_path(root, relative, must_exist=True, expect_file=True)
    except (PathCustodyError, OSError) as exc:
        raise FinalizationError("retained-path", f"{role} artifact leaves retained custody") from exc
    cursor = root.resolve(strict=True)
    if _is_reparse(cursor):
        raise FinalizationError("retained-path", "retained root is a reparse point")
    for part in PurePosixPath(relative).parts:
        cursor = cursor / part
        if _is_reparse(cursor):
            raise FinalizationError("retained-path", f"{role} artifact crosses a reparse point")
    status = path.lstat()
    if not stat.S_ISREG(status.st_mode):
        raise FinalizationError("retained-path", f"{role} artifact is not a regular file")
    try:
        first = path.read_bytes()
        second = path.read_bytes()
    except OSError as exc:
        raise FinalizationError("retained-ref", f"{role} artifact cannot be read") from exc
    if first != second:
        raise FinalizationError("retained-ref", f"{role} artifact changed during readback")
    if len(first) != byte_count or _sha256(first) != digest:
        raise FinalizationError("retained-ref", f"{role} artifact content address mismatch")
    return path, first


def _retained_json_ref(
    root: Path,
    value: object,
    role: str,
    *,
    expected_path: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    path, raw = _retained_ref(root, value, role, expected_path=expected_path)
    parsed = _strict_json(raw, role)
    if raw != _json_bytes(parsed):
        raise FinalizationError("retained-json", f"{role} JSON is not canonical retained bytes")
    return path, parsed


def _resolve_fresh_run_root(root: Path, run_root: str | Path) -> Path:
    source_root = root.resolve(strict=True)
    requested = Path(run_root)
    try:
        if requested.is_absolute():
            resolved = requested.resolve(strict=False)
            resolved.relative_to(source_root)
            lexical = requested
        else:
            resolved = resolve_repo_path(source_root, requested)
            lexical = source_root / requested
    except (OSError, ValueError, PathCustodyError) as exc:
        raise FinalizationError("run-root-custody", f"run root must remain under the repository: {run_root}") from exc

    for candidate in (lexical, *lexical.parents):
        if candidate == source_root:
            break
        if candidate.is_symlink():
            raise FinalizationError("run-root-custody", f"run-root symlink component is forbidden: {candidate}")
    if resolved.exists():
        raise FinalizationError("run-root-exists", f"run root must be create-once and absent: {resolved}")
    return resolved


def _create_run_root(path: Path, root: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.resolve(strict=True).relative_to(root.resolve(strict=True))
        path.mkdir()
    except FileExistsError as exc:
        raise FinalizationError("run-root-exists", f"run root appeared before create-once materialization: {path}") from exc
    except (OSError, ValueError) as exc:
        raise FinalizationError("run-root-custody", f"cannot create contained run root {path}: {exc}") from exc
    if path.is_symlink() or not path.is_dir():
        raise FinalizationError("run-root-custody", f"created run root is not a regular directory: {path}")


def _validate_raw_input(raw_input: bytes, expected: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_input, bytes) or not raw_input:
        raise FinalizationError("input-binding", "raw input must be non-empty immutable bytes")
    actual = {"sha256": _sha256(raw_input), "byte_count": len(raw_input)}
    if dict(expected) != actual:
        raise FinalizationError("input-binding", "raw input hash/length does not equal the dispatch binding")
    return actual


def _require_passing_capture(parsed: stage_envelope.ParsedSingleCallEnvelope) -> list[dict[str, Any]]:
    stages = parsed.payload.get("stage_records")
    if not isinstance(stages, list):
        raise FinalizationError("nonpassing-capture", "stage records are unavailable")
    if any(not isinstance(stage, dict) or stage.get("status") != "pass" for stage in stages):
        raise FinalizationError("nonpassing-capture", "all seven producer stage declarations must be pass")
    stage07 = stages[-1]
    if stage07.get("closure_claim") != "complete" or stage07.get("output_is_full_governed_answer") is not True:
        raise FinalizationError("nonpassing-capture", "Stage07 must declare a complete full governed answer")
    probe = copy.deepcopy(stages)
    try:
        stage_runner.validate_incremental_handoffs(probe)
    except Exception as exc:
        raise FinalizationError("handoff-validation", f"producer handoff validation failed: {exc}") from exc
    if probe != stages:
        raise FinalizationError("handoff-rewrite", "producer handoffs require rewriting; captured bytes remain immutable")
    return copy.deepcopy(stages)


def _execute_private_release_plan(
    *,
    execution: checker_snapshot.ExecutionSnapshot,
    bound_plan: list[dict[str, Any]],
    per_burden_reread: list[dict[str, Any]],
) -> dict[str, str]:
    """Execute every Stage07 row against the retained output and checker tree."""

    frozen_output = execution.output_path

    def run_adapter(row: dict[str, Any]) -> None:
        adapter_id = row.get("adapter_id")
        if adapter_id == "visible-governed-output":
            errors = stage_runner.visible_governed_output_errors(frozen_output)
            if errors:
                raise stage_runner.HarnessError(
                    "visible governed output validation failed: " + "; ".join(errors)
                )
            return
        if adapter_id == "mrp-record-surface-parity":
            errors = stage_runner.staged_output.visible_block_parity_errors(
                frozen_output.read_text(encoding="utf-8", errors="strict"),
                per_burden_reread,
            )
            if errors:
                raise stage_runner.HarnessError(
                    "MRP record-surface parity failed: " + "; ".join(errors)
                )
            return
        raise stage_runner.HarnessError(f"unknown Stage07 in-process adapter {adapter_id!r}")

    def run_checker(row: dict[str, Any]) -> None:
        stage_runner.require_command_success(execution.checker_command(row), cwd=execution.root)

    return stage_runner.execute_release_invocation_plan(
        bound_plan,
        run_adapter=run_adapter,
        run_checker=run_checker,
    )


def _run_private_release_validation(
    *,
    root: Path,
    run_root: Path,
    output_path: Path,
    per_burden_reread: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
    """Run the exact Stage07 registry plan from one retained private tree."""

    output_bytes = output_path.read_bytes()
    try:
        plan = stage_runner.stage07_release_invocation_plan(root, output_path)
        policy = stage_runner.stage07_release_validation_policy(root)
        snapshot_parent = run_root / "checker-execution"
        snapshot_parent.mkdir(parents=True, exist_ok=True)
        execution = checker_snapshot.create_execution_snapshot(
            root=root,
            destination=snapshot_parent / "stage07-release",
            plan=plan,
            output_path=output_path,
        )
        bound_plan = execution.bind_plan(plan, original_output=output_path)
        results = _execute_private_release_plan(
            execution=execution,
            bound_plan=bound_plan,
            per_burden_reread=per_burden_reread,
        )
        expected_order = tuple(row["result_key"] for row in bound_plan)
        if tuple(results) != expected_order or list(results) != policy.get("result_order"):
            raise stage_runner.HarnessError("registry invocation order drifted during private execution")
        if any(value != "pass" for value in results.values()):
            raise stage_runner.HarnessError("private release validation returned a non-pass result")
        execution.verify()
        if output_path.read_bytes() != output_bytes:
            raise stage_runner.HarnessError("retained Stage07 output changed during private checker execution")
        evidence = {
            "schema": "daee-single-call-private-release-validation-v1",
            "snapshot_root": _repo_relative(execution.root, root),
            "snapshot_manifest": copy.deepcopy(execution.manifest),
            "frozen_output": _artifact(execution.output_path, root),
            "bound_plan": copy.deepcopy(bound_plan),
        }
        return results, policy, evidence
    except FinalizationError:
        raise
    except Exception as exc:
        raise FinalizationError("release-validation", f"private Stage07 validation failed: {exc}") from exc


def _checker_bound_stage07(
    declaration: dict[str, Any],
    *,
    root: Path,
    output_path: Path,
    results: dict[str, str],
    policy: dict[str, Any],
) -> dict[str, Any]:
    stage07 = copy.deepcopy(declaration)
    stage07.pop("release_output_transport", None)
    stage07["release_output"] = {
        "path": _repo_relative(output_path, root),
        "sha256": _sha256(output_path.read_bytes()).upper(),
    }
    stage07["release_validation"] = copy.deepcopy(results)
    stage07["release_validation_policy"] = copy.deepcopy(policy)
    diagnostics = stage_runner.build_release_field_diagnostics(output_path)
    if diagnostics.get("matches") is not True:
        raise FinalizationError("release-diagnostics", "visible and field-witness release diagnostics do not match")
    stage07["release_field_diagnostics"] = diagnostics
    return stage07


def _write_state_capsules(
    *,
    root: Path,
    run_root: Path,
    case_id: str,
    input_digest: str,
    raw_input_path: Path,
    output_path: Path,
    stages: list[dict[str, Any]],
) -> list[Path]:
    checker = stage_runner.check_state_capsule_module()
    try:
        schema = checker.load_schema()
    except Exception as exc:
        raise FinalizationError("capsule-validation", f"state-capsule schema is unavailable: {exc}") from exc
    paths: list[Path] = []
    capsules_dir = run_root / "state-capsules"
    capsules_dir.mkdir(parents=True, exist_ok=True)
    for index, stage in enumerate(stages, start=1):
        stage_id = str(stage.get("id"))
        try:
            payload = stage_runner.build_state_capsule(
                case_id=case_id,
                input_digest=input_digest,
                stage_id=stage_id,
                stages=copy.deepcopy(stages[:index]),
                raw_input_path=raw_input_path,
                output_path=output_path if index == len(stages) else None,
                run_dir=run_root,
                root=root,
            )
        except Exception as exc:
            raise FinalizationError("capsule-validation", f"capsule {index} build failed: {exc}") from exc
        path = capsules_dir / f"capsule-{index:03d}.json"
        label = path.relative_to(root).as_posix()
        errors = checker.validate_capsule_payload(label, payload, schema)
        raw = _json_bytes(payload)
        _warnings, size_failures = checker.capsule_size_errors(label, raw)
        errors.extend(size_failures)
        if errors:
            raise FinalizationError("capsule-validation", f"capsule {index} invalid: " + "; ".join(errors))
        _write_exact(path, raw)
        if checker.validate_capsule_file(path, schema):
            raise FinalizationError("capsule-validation", f"capsule {index} failed retained readback validation")
        paths.append(path)
    replay_errors = checker.replay_errors(capsules_dir, schema, artifact_path=output_path)
    if replay_errors:
        raise FinalizationError("capsule-replay", "; ".join(replay_errors))
    return paths


def _build_checked_sidecars(
    *,
    root: Path,
    run_root: Path,
    raw_input_path: Path,
    output_path: Path,
    prefix: str,
    stage_records: list[dict[str, Any]],
) -> list[Path]:
    output_bytes = output_path.read_bytes()
    out_dir = run_root / "proof-sidecars"
    out_dir.mkdir(parents=True, exist_ok=True)
    certificate = out_dir / f"{prefix}.collapse-certificate.json"
    grapher = out_dir / f"{prefix}.grapher.html"
    hashes = out_dir / f"{prefix}.hashes.json"
    carrier_path = out_dir / f"{prefix}.b5-current-stage-carriers.json"
    b5_path = out_dir / f"{prefix}.b5-full-ir-projection-sidecar.json"
    expected_ids = {
        "stage-02-layer-a-diagnostic-ir",
        "stage-04-burden-execution-act",
        "stage-05-mrp-reread-terminal-state",
        "stage-06-field-witness-nar",
    }
    expected_carriers = [
        stage for stage in stage_records if isinstance(stage, dict) and stage.get("id") in expected_ids
    ]
    try:
        for checker in (
            "check_nla_decode_semantic_faithfulness.py",
            "check_field_witness_convergence.py",
            "check_formal_reread_state_semantics.py",
        ):
            stage_runner.require_command_success(
                [
                    sys.executable,
                    "-B",
                    str(root / "tools" / checker),
                    "--outputs",
                    str(output_path),
                ],
                cwd=root,
            )
        stage_runner.require_command_success(
            [
                sys.executable,
                "-B",
                str(root / "tools" / "check_graph_completeness.py"),
                "--outputs",
                str(output_path),
                "--json",
            ],
            cwd=root,
        )
        stage_runner.require_command_success(
            [
                sys.executable,
                "-B",
                str(root / "tools" / "build_retained_proof_sidecars.py"),
                "--input",
                str(raw_input_path),
                "--output",
                str(output_path),
                "--out-dir",
                str(out_dir),
                "--prefix",
                prefix,
                "--force",
            ],
            cwd=root,
        )
        eligibility_errors = stage_runner.b5_projection_eligibility_errors(
            stage_runner.load_json(certificate)
        )
        if eligibility_errors:
            raise stage_runner.HarnessError(
                "B.5 full-IR projection ineligible: " + "; ".join(eligibility_errors)
            )
        _write_json(carrier_path, expected_carriers)
        stage_runner.require_command_success(
            [
                sys.executable,
                "-B",
                str(root / "tools" / "build_b5_full_ir_projection_sidecar.py"),
                "--input",
                str(raw_input_path),
                "--output",
                str(output_path),
                "--collapse-certificate",
                str(certificate),
                "--grapher-html",
                str(grapher),
                "--stage-carriers",
                str(carrier_path),
                "--out",
                str(b5_path),
            ],
            cwd=root,
        )
    except Exception as exc:
        raise FinalizationError("sidecar-validation", f"checker-owned sidecar build failed: {exc}") from exc
    paths = [certificate, grapher, hashes, carrier_path, b5_path]
    _assert_exact_file(output_path, output_bytes, code="output-drift")
    if len(paths) != 5 or len({path.resolve(strict=True) for path in paths}) != 5:
        raise FinalizationError("sidecar-validation", "sidecar builder did not return five unique retained current artifacts")
    for path in paths:
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(run_root.resolve(strict=True))
        except ValueError as exc:
            raise FinalizationError("sidecar-validation", f"sidecar escaped the fresh run root: {path}") from exc
        if path.is_symlink() or not path.is_file():
            raise FinalizationError("sidecar-validation", f"sidecar is absent or non-regular: {path}")
        _artifact(path, root)
    try:
        retained_carriers = json.loads(carrier_path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FinalizationError("sidecar-validation", f"B.5 current carrier JSON readback failed: {exc}") from exc
    if retained_carriers != expected_carriers:
        raise FinalizationError("sidecar-validation", "B.5 current carrier readback differs from validated stages")
    try:
        b5 = json.loads(b5_path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FinalizationError("sidecar-validation", f"B.5 sidecar JSON readback failed: {exc}") from exc
    if not isinstance(b5, dict) or b5.get("schema") != handshake.B5_SIDECAR_SCHEMA:
        raise FinalizationError("sidecar-validation", "B.5 sidecar schema identity is invalid")
    return paths


def _checker_owned_stage08(
    *,
    root: Path,
    policy: dict[str, Any],
    sidecar_paths: list[Path],
) -> dict[str, Any]:
    relative_paths = [_repo_relative(path, root) for path in sidecar_paths]
    return {
        "id": "stage-08-verifier-sidecars",
        "status": "pass",
        "produces": ["verifier_sidecars"],
        "requires": ["release_output"],
        "release_validation_policy": copy.deepcopy(policy),
        "verifier_sidecars": {
            "proof_sidecars": {"claimed": True, "paths": relative_paths},
            "b5_4_1": {
                "claimed": False,
                "path": relative_paths[-1],
                "builder": handshake.B5_SIDECAR_BUILDER,
                "schema": handshake.B5_SIDECAR_SCHEMA,
                "role": "checker-owned-final-verifier-built-but-not-retained",
                "non_claims": {"not_fresh_runtime_default_emission": True},
            },
        },
    }


def _validate_full_handoff_record(path: Path, record: dict[str, Any]) -> None:
    stages = record.get("stages")
    probe = copy.deepcopy(stages)
    try:
        stage_runner.validate_incremental_handoffs(probe)
    except Exception as exc:
        raise FinalizationError("handoff-validation", f"final handoff validation failed: {exc}") from exc
    if probe != stages:
        raise FinalizationError("handoff-rewrite", "final handoff record would require normalization")
    errors = handshake.record_errors(path, record)
    if errors:
        raise FinalizationError("handshake-validation", "; ".join(errors[:12]))


def _snapshot_source_inventory(
    *,
    root: Path,
    plan: list[dict[str, Any]],
) -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    try:
        sources = checker_snapshot.execution_snapshot_sources(root=root, plan=plan)
    except Exception as exc:
        raise FinalizationError(
            "private-custody",
            f"cannot reconstruct the Stage07 execution source inventory: {exc}",
        ) from exc
    captured: dict[str, bytes] = {}
    rows: list[dict[str, Any]] = []
    for relative in sorted(sources):
        source = sources[relative]
        try:
            first = source.read_bytes()
            second = source.read_bytes()
        except OSError as exc:
            raise FinalizationError(
                "private-custody",
                f"cannot reread Stage07 execution source: {relative}",
            ) from exc
        if first != second:
            raise FinalizationError(
                "private-custody",
                f"Stage07 execution source changed during inventory: {relative}",
            )
        captured[relative] = first
        rows.append({"path": relative, "sha256": _sha256(first), "bytes": len(first)})
    return captured, rows


def _snapshot_regular_files(snapshot_root: Path) -> set[str]:
    found: set[str] = set()
    try:
        candidates = sorted(snapshot_root.rglob("*"))
    except OSError as exc:
        raise FinalizationError("private-custody", "cannot enumerate retained execution snapshot") from exc
    for candidate in candidates:
        if _is_reparse(candidate):
            raise FinalizationError(
                "private-custody",
                f"retained execution snapshot contains a reparse point: {candidate}",
            )
        try:
            status = candidate.lstat()
        except OSError as exc:
            raise FinalizationError(
                "private-custody",
                f"cannot inspect retained execution snapshot entry: {candidate}",
            ) from exc
        if stat.S_ISDIR(status.st_mode):
            continue
        if not stat.S_ISREG(status.st_mode):
            raise FinalizationError(
                "private-custody",
                f"retained execution snapshot contains a non-regular file: {candidate}",
            )
        found.add(candidate.relative_to(snapshot_root).as_posix())
    return found


def _verify_execution_snapshot(
    *,
    root: Path,
    run_root: Path,
    evidence: dict[str, Any],
    original_output_path: Path,
    expected_output: bytes,
    per_burden_reread: list[dict[str, Any]],
    claimed_results: Mapping[str, str] | None = None,
    replay: bool = False,
) -> None:
    expected_evidence_keys = {
        "schema",
        "snapshot_root",
        "snapshot_manifest",
        "frozen_output",
        "bound_plan",
    }
    if (
        set(evidence) != expected_evidence_keys
        or evidence.get("schema") != "daee-single-call-private-release-validation-v1"
    ):
        raise FinalizationError("private-custody", "private execution evidence shape is invalid")

    snapshot_raw = evidence.get("snapshot_root")
    expected_snapshot = run_root / "checker-execution" / "stage07-release"
    if (
        not isinstance(snapshot_raw, str)
        or _portable_retained_path(snapshot_raw, "private execution snapshot")
        != _repo_relative(expected_snapshot, root)
    ):
        raise FinalizationError("private-custody", "private execution snapshot locator differs")
    try:
        snapshot_root = resolve_repo_path(root, snapshot_raw, must_exist=True, expect_dir=True)
    except (PathCustodyError, OSError) as exc:
        raise FinalizationError(
            "private-custody",
            f"private execution snapshot is unavailable: {exc}",
        ) from exc
    if _is_reparse(snapshot_root):
        raise FinalizationError("private-custody", "private execution snapshot is a reparse point")

    manifest = evidence.get("snapshot_manifest")
    if not isinstance(manifest, dict) or set(manifest) != {"schema", "sha256", "file_count", "files"}:
        raise FinalizationError("private-custody", "private execution manifest shape is invalid")
    files = manifest.get("files")
    if (
        manifest.get("schema") != "daee-checker-execution-snapshot-v1"
        or not isinstance(files, list)
        or not files
        or not isinstance(manifest.get("file_count"), int)
        or isinstance(manifest.get("file_count"), bool)
        or manifest.get("file_count") != len(files)
        or not isinstance(manifest.get("sha256"), str)
        or SHA256_RE.fullmatch(manifest["sha256"]) is None
    ):
        raise FinalizationError("private-custody", "private execution manifest identity or count is invalid")
    normalized_paths: list[str] = []
    for row in files:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "sha256", "bytes"}
            or not isinstance(row.get("sha256"), str)
            or SHA256_RE.fullmatch(row["sha256"]) is None
            or not isinstance(row.get("bytes"), int)
            or isinstance(row.get("bytes"), bool)
            or row["bytes"] < 0
        ):
            raise FinalizationError("private-custody", "private execution manifest row is invalid")
        normalized_paths.append(_portable_retained_path(row.get("path"), "execution source"))
    if normalized_paths != sorted(normalized_paths) or len(set(normalized_paths)) != len(normalized_paths):
        raise FinalizationError("private-custody", "private execution manifest paths are not unique and sorted")
    if manifest["sha256"] != _canonical_sha256(files):
        raise FinalizationError("private-custody", "private execution manifest hash is invalid")

    try:
        plan = stage_runner.stage07_release_invocation_plan(root, original_output_path)
    except Exception as exc:
        raise FinalizationError(
            "private-custody",
            f"cannot reconstruct the exact Stage07 invocation plan: {exc}",
        ) from exc
    source_bytes, expected_files = _snapshot_source_inventory(root=root, plan=plan)
    if files != expected_files:
        raise FinalizationError("private-custody", "private execution manifest is not the exact source inventory")

    frozen_output_path, frozen_output = _retained_ref(
        root,
        evidence.get("frozen_output"),
        "private frozen output",
        expected_path=_repo_relative(expected_snapshot / ".artifacts" / "output.snapshot.md", root),
    )
    if frozen_output != expected_output:
        raise FinalizationError("private-custody", "private frozen output differs from captured Stage07 bytes")
    expected_snapshot_files = set(source_bytes) | {".artifacts/output.snapshot.md"}
    if _snapshot_regular_files(snapshot_root) != expected_snapshot_files:
        raise FinalizationError("private-custody", "private execution snapshot file set is not exact")

    execution = checker_snapshot.ExecutionSnapshot(
        source_root=root,
        root=snapshot_root,
        output_path=frozen_output_path,
        output_bytes=expected_output,
        files=source_bytes,
        manifest=copy.deepcopy(manifest),
    )
    expected_bound_plan = execution.bind_plan(plan, original_output=original_output_path)
    if evidence.get("bound_plan") != expected_bound_plan:
        raise FinalizationError("private-custody", "private execution bound plan differs from exact Stage07 plan")
    try:
        execution.verify()
    except Exception as exc:
        raise FinalizationError("private-custody", f"private execution snapshot verification failed: {exc}") from exc

    if replay:
        if not isinstance(claimed_results, Mapping):
            raise FinalizationError("release-validation-replay", "claimed Stage07 results are unavailable")
        try:
            replayed = _execute_private_release_plan(
                execution=execution,
                bound_plan=expected_bound_plan,
                per_burden_reread=copy.deepcopy(per_burden_reread),
            )
            execution.verify()
        except Exception as exc:
            raise FinalizationError(
                "release-validation-replay",
                f"retained Stage07 validator replay failed: {exc}",
            ) from exc
        expected_order = tuple(row["result_key"] for row in expected_bound_plan)
        if (
            tuple(replayed) != expected_order
            or replayed != dict(claimed_results)
            or any(value != "pass" for value in replayed.values())
        ):
            raise FinalizationError(
                "release-validation-replay",
                "retained Stage07 validator replay differs from the claimed exact result set",
            )


def finalize_single_call_stage_capture(
    *,
    root: Path,
    run_root: str | Path,
    raw_envelope: bytes,
    raw_input: bytes,
    expected_envelope_nonce: str,
    expected_case_id: str,
    expected_cycle_id: str,
    expected_candidate_binding: Mapping[str, Any],
    expected_input_binding: Mapping[str, Any],
    capture_complete_record: Mapping[str, Any] | None = None,
    capture_input_refs: Mapping[str, Any] | None = None,
    execution_tooling_manifest: Mapping[str, Any] | None = None,
) -> FinalizedSingleCallCapture:
    """Finalize one exact producer capture into a fresh contained run root."""

    source_root = root.resolve(strict=True)
    capture_bindings = (
        capture_complete_record,
        capture_input_refs,
        execution_tooling_manifest,
    )
    if any(value is not None for value in capture_bindings) and not all(
        isinstance(value, Mapping) for value in capture_bindings
    ):
        raise FinalizationError(
            "capture-input-binding",
            "capture record, input refs, and execution-tooling manifest must be supplied together",
        )
    authorized_tooling: dict[str, Any] | None = None
    if execution_tooling_manifest is not None:
        source_commit = expected_candidate_binding.get("source_commit")
        if not isinstance(source_commit, str):
            raise FinalizationError("execution-tooling-manifest", "candidate source commit is unavailable")
        try:
            authorized_tooling = tooling_manifest.load_and_verify_execution_tooling_manifest(
                root=source_root,
                manifest_ref=execution_tooling_manifest,
                expected_source_commit=source_commit,
            )
        except tooling_manifest.ExecutionToolingManifestError as exc:
            raise FinalizationError("execution-tooling-manifest", str(exc)) from exc
    input_binding = _validate_raw_input(raw_input, expected_input_binding)
    try:
        parsed = stage_envelope.parse_single_call_stage_envelope(
            raw_envelope,
            expected_envelope_nonce=expected_envelope_nonce,
            expected_case_id=expected_case_id,
            expected_cycle_id=expected_cycle_id,
            expected_candidate_binding=expected_candidate_binding,
            expected_input_binding=expected_input_binding,
        )
    except stage_envelope.EnvelopeValidationError as exc:
        raise FinalizationError(f"envelope-{exc.code}", str(exc)) from exc
    producer_stages = _require_passing_capture(parsed)
    destination = _resolve_fresh_run_root(source_root, run_root)
    _create_run_root(destination, source_root)

    capture_dir = destination / "capture"
    raw_envelope_path = capture_dir / "raw-envelope.bin"
    raw_input_path = capture_dir / "raw-input.bin"
    stage_json_path = capture_dir / "stage-json.bin"
    output_path = capture_dir / "stage07-output.md"
    _write_exact(raw_envelope_path, parsed.raw_bytes)
    _write_exact(raw_input_path, raw_input)
    _write_exact(stage_json_path, parsed.stage_json_bytes)
    _write_exact(output_path, parsed.final_output_bytes)
    try:
        stage_envelope.verify_envelope_readback(parsed, raw_envelope_path.read_bytes())
    except stage_envelope.EnvelopeValidationError as exc:
        raise FinalizationError("capture-readback", str(exc)) from exc
    _assert_exact_file(output_path, parsed.final_output_bytes, code="output-drift")

    producer_dir = destination / "stages" / "producer"
    producer_paths: list[Path] = []
    for index, stage in enumerate(producer_stages[:6], start=1):
        path = producer_dir / f"stage-{index:02d}.json"
        _write_json(path, stage)
        producer_paths.append(path)

    per_burden = producer_stages[4].get("per_burden_reread")
    if not isinstance(per_burden, list):
        raise FinalizationError("release-validation", "Stage05 per_burden_reread is unavailable")
    results, policy, execution_evidence = _run_private_release_validation(
        root=source_root,
        run_root=destination,
        output_path=output_path,
        per_burden_reread=copy.deepcopy(per_burden),
    )
    if authorized_tooling is not None:
        try:
            tooling_manifest.verify_execution_snapshot_projection(
                authorized_tooling,
                execution_evidence.get("snapshot_manifest"),
            )
        except tooling_manifest.ExecutionToolingManifestError as exc:
            raise FinalizationError("execution-tooling-snapshot", str(exc)) from exc
    _assert_exact_file(output_path, parsed.final_output_bytes, code="output-drift")
    if list(results) != policy.get("result_order") or any(value != "pass" for value in results.values()):
        raise FinalizationError("release-validation", "private validator results do not match the canonical profile")

    execution_evidence_path = destination / "checker-execution" / "stage07-release-evidence.json"
    _write_json(execution_evidence_path, execution_evidence)
    stage07 = _checker_bound_stage07(
        producer_stages[6],
        root=source_root,
        output_path=output_path,
        results=results,
        policy=policy,
    )
    checker_stage_dir = destination / "stages" / "checker"
    stage07_path = checker_stage_dir / "stage-07-release-output.json"
    _write_json(stage07_path, stage07)

    first_seven = [*copy.deepcopy(producer_stages[:6]), copy.deepcopy(stage07)]
    capsule_paths = _write_state_capsules(
        root=source_root,
        run_root=destination,
        case_id=expected_case_id,
        input_digest=input_binding["sha256"],
        raw_input_path=raw_input_path,
        output_path=output_path,
        stages=first_seven,
    )
    _assert_exact_file(output_path, parsed.final_output_bytes, code="output-drift")

    sidecar_paths = _build_checked_sidecars(
        root=source_root,
        run_root=destination,
        raw_input_path=raw_input_path,
        output_path=output_path,
        prefix=f"capture-{parsed.envelope_nonce}",
        stage_records=copy.deepcopy(producer_stages[:6]),
    )
    _assert_exact_file(output_path, parsed.final_output_bytes, code="output-drift")
    stage08 = _checker_owned_stage08(root=source_root, policy=policy, sidecar_paths=sidecar_paths)
    stage08_path = checker_stage_dir / "stage-08-verifier-sidecars.json"
    _write_json(stage08_path, stage08)

    record_path = destination / "records" / "staged-handoff-record.json"
    model_scope = {
        "type": "focused-current-skill-smoke",
        "case_count": 1,
        "case_family": "candidate-bound-single-call-capture",
        "case_metadata_role": "custody_only_not_route_or_proof",
        "retained_replay_target": _repo_relative(stage_json_path, source_root),
    }
    record = stage_runner.base_record(
        expected_case_id,
        "staged-current-skill-smoke",
        not_model_smoke=False,
        model_scope_payload=model_scope,
    )
    record["stages"] = [*first_seven, copy.deepcopy(stage08)]
    _write_json(record_path, record)
    _validate_full_handoff_record(record_path, record)
    retained_record = json.loads(record_path.read_text(encoding="utf-8", errors="strict"))
    if retained_record != record:
        raise FinalizationError("handshake-readback", "staged handoff record changed after validation")
    _validate_full_handoff_record(record_path, retained_record)

    capture = {
        "raw_envelope": _artifact(raw_envelope_path, source_root, data=parsed.raw_bytes),
        "raw_input": _artifact(raw_input_path, source_root, data=raw_input),
        "stage_json": {
            **_artifact(stage_json_path, source_root, data=parsed.stage_json_bytes),
            "start": parsed.stage_json_start,
            "end": parsed.stage_json_end,
        },
        "stage07_output": {
            **_artifact(output_path, source_root, data=parsed.final_output_bytes),
            "start": parsed.final_output_start,
            "end": parsed.final_output_end,
        },
    }
    capture_manifest = {
        "schema": "daee-single-call-capture-offset-manifest-v1",
        "envelope_nonce": parsed.envelope_nonce,
        "capture": copy.deepcopy(capture),
    }
    capture_manifest_path = capture_dir / "capture-manifest.json"
    _write_json(capture_manifest_path, capture_manifest)

    _verify_execution_snapshot(
        root=source_root,
        run_root=destination,
        evidence=execution_evidence,
        original_output_path=output_path,
        expected_output=parsed.final_output_bytes,
        per_burden_reread=copy.deepcopy(per_burden),
    )
    _assert_exact_file(raw_envelope_path, parsed.raw_bytes, code="capture-drift")
    _assert_exact_file(raw_input_path, raw_input, code="input-drift")
    _assert_exact_file(stage_json_path, parsed.stage_json_bytes, code="capture-drift")
    _assert_exact_file(output_path, parsed.final_output_bytes, code="output-drift")
    for path in [*producer_paths, stage07_path, stage08_path, *capsule_paths, *sidecar_paths, record_path]:
        _artifact(path, source_root)

    binding_payload: dict[str, Any] = {
        "candidate": dict(expected_candidate_binding),
        "input": input_binding,
    }
    if capture_complete_record is not None:
        binding_payload["capture_complete_record"] = copy.deepcopy(dict(capture_complete_record))
        binding_payload["capture_input_refs"] = copy.deepcopy(dict(capture_input_refs))
        binding_payload["execution_tooling_manifest"] = copy.deepcopy(dict(execution_tooling_manifest))
    finalization = {
        "schema": "daee-single-call-stage-finalization-v1",
        "verdict": FINALIZATION_VERDICT,
        "case_id": expected_case_id,
        "cycle_id": expected_cycle_id,
        "envelope_nonce": parsed.envelope_nonce,
        "bindings": binding_payload,
        "capture": capture,
        "producer_stage_files": [_artifact(path, source_root) for path in producer_paths],
        "checker_owned": {
            "capture_manifest": _artifact(capture_manifest_path, source_root),
            "stage07": _artifact(stage07_path, source_root),
            "stage08": _artifact(stage08_path, source_root),
            "release_validation_evidence": _artifact(execution_evidence_path, source_root),
            "state_capsules": [_artifact(path, source_root) for path in capsule_paths],
            "proof_sidecars": [_artifact(path, source_root) for path in sidecar_paths],
            "staged_handoff_record": _artifact(record_path, source_root),
        },
        "release_validation": {
            "results": copy.deepcopy(results),
            "policy": copy.deepcopy(policy),
            "execution_snapshot": copy.deepcopy(execution_evidence["snapshot_manifest"]),
        },
        "non_claims": copy.deepcopy(FINALIZATION_NON_CLAIMS),
    }
    finalization_path = destination / "structural-finalization.json"
    _write_json(finalization_path, finalization)
    if json.loads(finalization_path.read_text(encoding="utf-8", errors="strict")) != finalization:
        raise FinalizationError("finalization-readback", "structural finalization readback drifted")
    _assert_exact_file(output_path, parsed.final_output_bytes, code="output-drift")

    return FinalizedSingleCallCapture(
        run_root=destination,
        stage07_path=stage07_path,
        stage08_path=stage08_path,
        record_path=record_path,
        finalization_path=finalization_path,
    )


def _revalidate_state_capsules(
    *,
    root: Path,
    run_root: Path,
    refs: object,
    case_id: str,
    input_digest: str,
    raw_input_path: Path,
    output_path: Path,
    stages: list[dict[str, Any]],
) -> None:
    if not isinstance(refs, list) or len(refs) != 7:
        raise FinalizationError("capsule-revalidation", "exactly seven retained state capsules are required")
    checker = stage_runner.check_state_capsule_module()
    try:
        schema = checker.load_schema()
    except Exception as exc:
        raise FinalizationError("capsule-revalidation", f"state-capsule schema is unavailable: {exc}") from exc
    capsule_dir = run_root / "state-capsules"
    for index, (ref, stage) in enumerate(zip(refs, stages), 1):
        expected_path = _repo_relative(capsule_dir / f"capsule-{index:03d}.json", root)
        path, raw = _retained_ref(root, ref, f"state capsule {index}", expected_path=expected_path)
        payload = _strict_json(raw, f"state capsule {index}")
        if raw != _json_bytes(payload):
            raise FinalizationError("capsule-revalidation", f"state capsule {index} is not canonical")
        try:
            expected = stage_runner.build_state_capsule(
                case_id=case_id,
                input_digest=input_digest,
                stage_id=str(stage.get("id")),
                stages=copy.deepcopy(stages[:index]),
                raw_input_path=raw_input_path,
                output_path=output_path if index == len(stages) else None,
                run_dir=run_root,
                root=root,
            )
        except Exception as exc:
            raise FinalizationError("capsule-revalidation", f"state capsule {index} cannot be rederived: {exc}") from exc
        if payload != expected:
            raise FinalizationError("capsule-revalidation", f"state capsule {index} differs from retained dependencies")
        errors = checker.validate_capsule_payload(path.relative_to(root).as_posix(), payload, schema)
        _warnings, size_errors = checker.capsule_size_errors(path.relative_to(root).as_posix(), raw)
        errors.extend(size_errors)
        errors.extend(checker.validate_capsule_file(path, schema))
        if errors:
            raise FinalizationError("capsule-revalidation", f"state capsule {index} invalid: {'; '.join(errors[:8])}")
    replay_errors = checker.replay_errors(capsule_dir, schema, artifact_path=output_path)
    if replay_errors:
        raise FinalizationError("capsule-revalidation", "; ".join(replay_errors[:8]))


def _revalidate_proof_sidecars(
    *,
    root: Path,
    run_root: Path,
    refs: object,
    nonce: str,
    raw_input_path: Path,
    output_path: Path,
    producer_stages: list[dict[str, Any]],
) -> list[Path]:
    if not isinstance(refs, list) or len(refs) != 5:
        raise FinalizationError("sidecar-revalidation", "exactly five retained proof sidecars are required")
    prefix = f"capture-{nonce}"
    expected_paths = [
        run_root / "proof-sidecars" / f"{prefix}.collapse-certificate.json",
        run_root / "proof-sidecars" / f"{prefix}.grapher.html",
        run_root / "proof-sidecars" / f"{prefix}.hashes.json",
        run_root / "proof-sidecars" / f"{prefix}.b5-current-stage-carriers.json",
        run_root / "proof-sidecars" / f"{prefix}.b5-full-ir-projection-sidecar.json",
    ]
    paths: list[Path] = []
    raws: list[bytes] = []
    for index, (ref, expected) in enumerate(zip(refs, expected_paths), 1):
        path, raw = _retained_ref(
            root,
            ref,
            f"proof sidecar {index}",
            expected_path=_repo_relative(expected, root),
        )
        paths.append(path)
        raws.append(raw)

    certificate = _strict_json(raws[0], "collapse certificate")
    if not _matches_text_writer_json(raws[0], certificate, sort_keys=True):
        raise FinalizationError("sidecar-revalidation", "collapse certificate is not canonical JSON")
    eligibility = stage_runner.b5_projection_eligibility_errors(certificate)
    if eligibility:
        raise FinalizationError("sidecar-revalidation", "; ".join(eligibility[:8]))

    try:
        grapher = raws[1].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise FinalizationError("sidecar-revalidation", "Grapher sidecar is not strict UTF-8") from exc
    if "Verdict: reconstructible" not in grapher or "No warnings." not in grapher:
        raise FinalizationError("sidecar-revalidation", "Grapher sidecar is not reconstructible and warning-clean")

    hashes = _strict_json(raws[2], "proof-sidecar hashes")
    if not _matches_text_writer_json(raws[2], hashes, sort_keys=True):
        raise FinalizationError("sidecar-revalidation", "proof-sidecar hashes are not canonical JSON")
    expected_hashes = {
        "schema_version": retained_sidecars.SCHEMA_VERSION,
        "input": _repo_relative(raw_input_path, root),
        "output": _repo_relative(output_path, root),
        "artifacts": {
            "input": retained_sidecars.sha256_artifact_bytes(raw_input_path.read_bytes()),
            "output": retained_sidecars.sha256_artifact_bytes(output_path.read_bytes()),
            "collapse_certificate": retained_sidecars.sha256_artifact_bytes(raws[0]),
            "grapher_html": retained_sidecars.sha256_artifact_bytes(raws[1]),
        },
    }
    if hashes != expected_hashes:
        raise FinalizationError("sidecar-revalidation", "proof-sidecar hash manifest differs from retained bytes")

    carriers = _strict_json_value(raws[3], "B.5 current stage carriers")
    if raws[3] != _json_bytes(carriers):
        raise FinalizationError("sidecar-revalidation", "B.5 current stage carriers are not canonical JSON")
    expected_ids = {
        "stage-02-layer-a-diagnostic-ir",
        "stage-04-burden-execution-act",
        "stage-05-mrp-reread-terminal-state",
        "stage-06-field-witness-nar",
    }
    expected_carriers = [
        stage for stage in producer_stages if isinstance(stage, dict) and stage.get("id") in expected_ids
    ]
    if carriers != expected_carriers:
        raise FinalizationError("sidecar-revalidation", "B.5 current stage carriers differ from Stage02/04/05/06")

    b5 = _strict_json(raws[4], "B.5 full-IR projection sidecar")
    if not _matches_text_writer_json(raws[4], b5, sort_keys=False):
        raise FinalizationError("sidecar-revalidation", "B.5 sidecar is not canonical JSON")
    field_witness, records, validated_certificate, errors = b5_sidecar.validate_inputs(
        raw_input_path,
        output_path,
        paths[0],
        paths[1],
    )
    if errors or field_witness is None or records is None or validated_certificate is None:
        raise FinalizationError("sidecar-revalidation", "; ".join(errors[:8]) or "B.5 inputs are unavailable")
    if field_witness.get("schema_version") != b5_sidecar.CURRENT_PUBLIC_WITNESS_SCHEMA:
        raise FinalizationError("sidecar-revalidation", "current Stage01-08 finalization requires the current public witness schema")
    projection, projection_errors = b5_sidecar.build_current_projection(
        field_witness,
        records,
        carriers,
        validated_certificate,
    )
    if projection_errors or projection is None:
        raise FinalizationError("sidecar-revalidation", "; ".join(projection_errors[:8]))
    expected_b5 = {
        "schema": b5_sidecar.SIDECAR_SCHEMA,
        "source": {
            "raw_input": _repo_relative(raw_input_path, root),
            "governed_output": _repo_relative(output_path, root),
            "collapse_certificate": _repo_relative(paths[0], root),
            "builder": b5_sidecar.BUILDER_PATH,
            "grapher_html": _repo_relative(paths[1], root),
        },
        "projection": projection,
    }
    if b5 != expected_b5:
        raise FinalizationError("sidecar-revalidation", "B.5 sidecar differs from deterministic retained reprojection")
    return paths


def revalidate_single_call_stage_capture(
    *,
    root: Path,
    finalization_ref: Mapping[str, Any],
    expected_case_id: str,
    expected_cycle_id: str,
    expected_candidate_binding: Mapping[str, Any],
    expected_input_binding: Mapping[str, Any],
    expected_capture_complete_record: Mapping[str, Any] | None = None,
    expected_capture_input_refs: Mapping[str, Any] | None = None,
    expected_execution_tooling_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Reopen and deterministically revalidate one complete retained Stage01-08 tree."""

    source_root = root.resolve(strict=True)
    capture_bindings = (
        expected_capture_complete_record,
        expected_capture_input_refs,
        expected_execution_tooling_manifest,
    )
    if any(value is not None for value in capture_bindings) and not all(
        isinstance(value, Mapping) for value in capture_bindings
    ):
        raise FinalizationError(
            "finalization-revalidation",
            "capture record, input refs, and execution-tooling manifest must be expected together",
        )
    authorized_tooling: dict[str, Any] | None = None
    if expected_execution_tooling_manifest is not None:
        source_commit = expected_candidate_binding.get("source_commit")
        if not isinstance(source_commit, str):
            raise FinalizationError("execution-tooling-manifest", "candidate source commit is unavailable")
        try:
            authorized_tooling = tooling_manifest.load_and_verify_execution_tooling_manifest(
                root=source_root,
                manifest_ref=expected_execution_tooling_manifest,
                expected_source_commit=source_commit,
            )
        except tooling_manifest.ExecutionToolingManifestError as exc:
            raise FinalizationError("execution-tooling-manifest", str(exc)) from exc
    finalization_path, finalization_raw = _retained_ref(
        source_root,
        finalization_ref,
        "single-call structural finalization",
    )
    if finalization_path.name != "structural-finalization.json":
        raise FinalizationError("finalization-revalidation", "structural finalization locator is not canonical")
    finalization = _strict_json(finalization_raw, "single-call structural finalization")
    if finalization_raw != _json_bytes(finalization):
        raise FinalizationError("finalization-revalidation", "structural finalization is not canonical JSON")
    expected_top = {
        "schema", "verdict", "case_id", "cycle_id", "envelope_nonce", "bindings",
        "capture", "producer_stage_files", "checker_owned", "release_validation", "non_claims",
    }
    if set(finalization) != expected_top:
        raise FinalizationError("finalization-revalidation", "structural finalization field set is incomplete")
    if (
        finalization.get("schema") != "daee-single-call-stage-finalization-v1"
        or finalization.get("verdict") != FINALIZATION_VERDICT
        or finalization.get("case_id") != expected_case_id
        or finalization.get("cycle_id") != expected_cycle_id
        or finalization.get("non_claims") != FINALIZATION_NON_CLAIMS
        or not isinstance(finalization.get("envelope_nonce"), str)
        or NONCE_RE.fullmatch(finalization["envelope_nonce"]) is None
    ):
        raise FinalizationError("finalization-revalidation", "structural finalization identity or verdict is invalid")

    bindings = finalization.get("bindings")
    expected_binding_keys = {"candidate", "input"}
    if expected_capture_complete_record is not None:
        expected_binding_keys.update({"capture_complete_record", "capture_input_refs", "execution_tooling_manifest"})
    if not isinstance(bindings, dict) or set(bindings) != expected_binding_keys:
        raise FinalizationError("finalization-revalidation", "structural finalization bindings are incomplete")
    if bindings.get("candidate") != dict(expected_candidate_binding) or bindings.get("input") != dict(expected_input_binding):
        raise FinalizationError("finalization-revalidation", "candidate or input binding differs")
    if expected_capture_complete_record is not None and bindings.get("capture_complete_record") != dict(expected_capture_complete_record):
        raise FinalizationError("finalization-revalidation", "capture-complete record crosslink differs")
    if expected_capture_input_refs is not None and bindings.get("capture_input_refs") != dict(expected_capture_input_refs):
        raise FinalizationError("finalization-revalidation", "capture input refs crosslink differs")
    if expected_execution_tooling_manifest is not None and bindings.get("execution_tooling_manifest") != dict(expected_execution_tooling_manifest):
        raise FinalizationError("finalization-revalidation", "execution-tooling manifest crosslink differs")

    run_root = finalization_path.parent
    capture = finalization.get("capture")
    if not isinstance(capture, dict) or set(capture) != {"raw_envelope", "raw_input", "stage_json", "stage07_output"}:
        raise FinalizationError("finalization-revalidation", "capture artifact set is incomplete")
    raw_envelope_path, raw_envelope = _retained_ref(
        source_root,
        capture["raw_envelope"],
        "raw envelope",
        expected_path=_repo_relative(run_root / "capture" / "raw-envelope.bin", source_root),
    )
    raw_input_path, raw_input = _retained_ref(
        source_root,
        capture["raw_input"],
        "raw input",
        expected_path=_repo_relative(run_root / "capture" / "raw-input.bin", source_root),
    )
    stage_json_path, stage_json = _retained_ref(
        source_root,
        capture["stage_json"],
        "stage JSON",
        expected_path=_repo_relative(run_root / "capture" / "stage-json.bin", source_root),
        extra_keys=("start", "end"),
    )
    output_path, output = _retained_ref(
        source_root,
        capture["stage07_output"],
        "Stage07 output",
        expected_path=_repo_relative(run_root / "capture" / "stage07-output.md", source_root),
        extra_keys=("start", "end"),
    )
    _validate_raw_input(raw_input, expected_input_binding)
    try:
        parsed = stage_envelope.parse_single_call_stage_envelope(
            raw_envelope,
            expected_envelope_nonce=finalization["envelope_nonce"],
            expected_case_id=expected_case_id,
            expected_cycle_id=expected_cycle_id,
            expected_candidate_binding=expected_candidate_binding,
            expected_input_binding=expected_input_binding,
        )
        stage_envelope.verify_envelope_readback(parsed, raw_envelope_path.read_bytes())
    except stage_envelope.EnvelopeValidationError as exc:
        raise FinalizationError("finalization-revalidation", f"retained envelope is invalid: {exc}") from exc
    if (
        stage_json != parsed.stage_json_bytes
        or output != parsed.final_output_bytes
        or capture["stage_json"].get("start") != parsed.stage_json_start
        or capture["stage_json"].get("end") != parsed.stage_json_end
        or capture["stage07_output"].get("start") != parsed.final_output_start
        or capture["stage07_output"].get("end") != parsed.final_output_end
    ):
        raise FinalizationError("finalization-revalidation", "retained envelope offsets or payload slices differ")
    producer_stages = _require_passing_capture(parsed)

    producer_refs = finalization.get("producer_stage_files")
    if not isinstance(producer_refs, list) or len(producer_refs) != 6:
        raise FinalizationError("finalization-revalidation", "exactly six retained producer stage files are required")
    retained_producer: list[dict[str, Any]] = []
    for index, (ref, expected_stage) in enumerate(zip(producer_refs, producer_stages[:6]), 1):
        _path, stage = _retained_json_ref(
            source_root,
            ref,
            f"producer stage {index}",
            expected_path=_repo_relative(run_root / "stages" / "producer" / f"stage-{index:02d}.json", source_root),
        )
        if stage != expected_stage:
            raise FinalizationError("finalization-revalidation", f"producer stage {index} differs from captured envelope")
        retained_producer.append(stage)

    release = finalization.get("release_validation")
    if not isinstance(release, dict) or set(release) != {"results", "policy", "execution_snapshot"}:
        raise FinalizationError("finalization-revalidation", "release-validation binding is incomplete")
    results = release.get("results")
    policy = release.get("policy")
    if not isinstance(results, dict) or not isinstance(policy, dict):
        raise FinalizationError("finalization-revalidation", "release-validation results or policy are invalid")
    current_policy = stage_runner.stage07_release_validation_policy(source_root)
    if policy != current_policy or list(results) != policy.get("result_order") or any(value != "pass" for value in results.values()):
        raise FinalizationError("finalization-revalidation", "release-validation profile or results differ")
    if authorized_tooling is not None:
        try:
            tooling_manifest.verify_execution_snapshot_projection(
                authorized_tooling,
                release.get("execution_snapshot"),
            )
        except tooling_manifest.ExecutionToolingManifestError as exc:
            raise FinalizationError("execution-tooling-snapshot", str(exc)) from exc

    checker_owned = finalization.get("checker_owned")
    expected_checker_keys = {
        "capture_manifest", "stage07", "stage08", "release_validation_evidence",
        "state_capsules", "proof_sidecars", "staged_handoff_record",
    }
    if not isinstance(checker_owned, dict) or set(checker_owned) != expected_checker_keys:
        raise FinalizationError("finalization-revalidation", "checker-owned artifact set is incomplete")
    capture_manifest_path, capture_manifest = _retained_json_ref(
        source_root,
        checker_owned["capture_manifest"],
        "capture offset manifest",
        expected_path=_repo_relative(run_root / "capture" / "capture-manifest.json", source_root),
    )
    del capture_manifest_path
    if capture_manifest != {
        "schema": "daee-single-call-capture-offset-manifest-v1",
        "envelope_nonce": finalization["envelope_nonce"],
        "capture": capture,
    }:
        raise FinalizationError("finalization-revalidation", "capture offset manifest differs")

    stage07_path, stage07 = _retained_json_ref(
        source_root,
        checker_owned["stage07"],
        "checker-owned Stage07",
        expected_path=_repo_relative(run_root / "stages" / "checker" / "stage-07-release-output.json", source_root),
    )
    expected_stage07 = _checker_bound_stage07(
        producer_stages[6],
        root=source_root,
        output_path=output_path,
        results=copy.deepcopy(results),
        policy=copy.deepcopy(policy),
    )
    if stage07 != expected_stage07:
        raise FinalizationError("finalization-revalidation", "checker-owned Stage07 differs from deterministic derivation")

    sidecar_paths = _revalidate_proof_sidecars(
        root=source_root,
        run_root=run_root,
        refs=checker_owned["proof_sidecars"],
        nonce=finalization["envelope_nonce"],
        raw_input_path=raw_input_path,
        output_path=output_path,
        producer_stages=retained_producer,
    )
    stage08_path, stage08 = _retained_json_ref(
        source_root,
        checker_owned["stage08"],
        "checker-owned Stage08",
        expected_path=_repo_relative(run_root / "stages" / "checker" / "stage-08-verifier-sidecars.json", source_root),
    )
    expected_stage08 = _checker_owned_stage08(root=source_root, policy=policy, sidecar_paths=sidecar_paths)
    if stage08 != expected_stage08:
        raise FinalizationError("finalization-revalidation", "checker-owned Stage08 differs from deterministic derivation")

    stages = [*retained_producer, stage07, stage08]
    handoff_path, handoff = _retained_json_ref(
        source_root,
        checker_owned["staged_handoff_record"],
        "staged handoff record",
        expected_path=_repo_relative(run_root / "records" / "staged-handoff-record.json", source_root),
    )
    if handoff.get("stages") != stages or handoff.get("case_id") != expected_case_id:
        raise FinalizationError("finalization-revalidation", "staged handoff record does not contain exact Stage01-08")
    _validate_full_handoff_record(handoff_path, handoff)

    _revalidate_state_capsules(
        root=source_root,
        run_root=run_root,
        refs=checker_owned["state_capsules"],
        case_id=expected_case_id,
        input_digest=str(expected_input_binding.get("sha256")),
        raw_input_path=raw_input_path,
        output_path=output_path,
        stages=stages[:7],
    )

    evidence_path, evidence = _retained_json_ref(
        source_root,
        checker_owned["release_validation_evidence"],
        "private release-validation evidence",
        expected_path=_repo_relative(run_root / "checker-execution" / "stage07-release-evidence.json", source_root),
    )
    del evidence_path
    if evidence.get("schema") != "daee-single-call-private-release-validation-v1":
        raise FinalizationError("finalization-revalidation", "private release-validation evidence schema differs")
    if evidence.get("snapshot_manifest") != release.get("execution_snapshot"):
        raise FinalizationError("finalization-revalidation", "private execution snapshot binding differs")
    per_burden = retained_producer[4].get("per_burden_reread")
    if not isinstance(per_burden, list):
        raise FinalizationError(
            "release-validation-replay",
            "retained Stage05 per_burden_reread is unavailable",
        )
    _verify_execution_snapshot(
        root=source_root,
        run_root=run_root,
        evidence=evidence,
        original_output_path=output_path,
        expected_output=output,
        per_burden_reread=copy.deepcopy(per_burden),
        claimed_results=results,
        replay=True,
    )
    _assert_exact_file(stage_json_path, parsed.stage_json_bytes, code="finalization-revalidation")
    _assert_exact_file(stage07_path, _json_bytes(stage07), code="finalization-revalidation")
    _assert_exact_file(stage08_path, _json_bytes(stage08), code="finalization-revalidation")
    return copy.deepcopy(finalization)


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FinalizationError("cli-input", f"cannot load {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise FinalizationError("cli-input", f"{label} must be one JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envelope", required=True, type=Path)
    parser.add_argument("--raw-input", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--envelope-nonce", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--cycle-id", required=True)
    parser.add_argument("--candidate-binding", required=True, type=Path)
    parser.add_argument("--input-binding", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = finalize_single_call_stage_capture(
            root=ROOT,
            run_root=args.run_root,
            raw_envelope=args.envelope.read_bytes(),
            raw_input=args.raw_input.read_bytes(),
            expected_envelope_nonce=args.envelope_nonce,
            expected_case_id=args.case_id,
            expected_cycle_id=args.cycle_id,
            expected_candidate_binding=_load_json_object(args.candidate_binding, "candidate binding"),
            expected_input_binding=_load_json_object(args.input_binding, "input binding"),
        )
    except (FinalizationError, OSError) as exc:
        print(f"single-call finalization: FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "PASS", "verdict": FINALIZATION_VERDICT, "run_root": str(result.run_root)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
