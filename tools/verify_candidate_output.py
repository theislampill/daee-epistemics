#!/usr/bin/env python3
"""Create one custody-bound canonical checker-replay verdict for a captured output."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from check_captured_output_manifest import PublicationError, atomic_publish_bytes
from checker_execution_snapshot import create_execution_snapshot
from contract_validation import PathCustodyError, resolve_repo_path
from validation_registry import (
    canonical_sha256,
    diagnostic_adapter_map,
    profile_invocations,
    profile_map,
    sha256_bytes,
    snapshot_registry,
    validate_verdict,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILE_ID = "captured-output-structural"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _stream_bytes(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    return str(value).encode("utf-8", errors="replace")


def _repo_file(root: Path, path: Path, label: str) -> Path:
    try:
        return resolve_repo_path(root, path, must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        raise ValueError(f"{label} must be a repository-relative file: {exc}") from exc


def _write_private(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def _assert_bytes(path: Path, expected: bytes, label: str) -> None:
    if path.read_bytes() != expected:
        raise ValueError(f"{label} changed during candidate verification")


def _exact_checker_plan(registry: dict[str, Any], profile_id: str, plan: list[dict[str, Any]]) -> None:
    profile = profile_map(registry).get(profile_id)
    if profile is None:
        raise ValueError(f"unknown validation profile {profile_id}")
    required = [
        str(row["checker_id"])
        for row in profile["requirements"]
        if row["required"]
    ]
    observed = [
        str(row.get("checker_id") or "")
        for row in plan
        if row.get("invocation_kind") == "checker"
    ]
    if (
        not plan
        or len(observed) != len(plan)
        or len(observed) != len(set(observed))
        or observed != required
    ):
        raise ValueError("candidate verifier requires an exact non-empty checker plan")


def _adapter_for(registry: dict[str, Any], checker_id: str) -> dict[str, Any]:
    matches = [
        adapter
        for adapter_id, adapter in diagnostic_adapter_map(registry).items()
        if checker_id in adapter["checker_ids"]
    ]
    if len(matches) != 1:
        raise ValueError(f"{checker_id}: expected exactly one registered diagnostic adapter")
    return matches[0]


def _classification(
    checker_id: str,
    proc: Any | None,
    error: BaseException | None,
    registry: dict[str, Any],
) -> dict[str, Any]:
    stdout = _stream_bytes(getattr(proc, "stdout", getattr(error, "stdout", b"")))
    stderr = _stream_bytes(getattr(proc, "stderr", getattr(error, "stderr", b"")))
    common = {
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "diagnostic": None,
        "diagnostic_adapter_id": None,
        "timeout": False,
        "crash": False,
        "usage_error": False,
        "malformed_diagnostic": False,
        "downstream_invalidated": ["promotion", "scorecard"],
        "forbidden_artifact_readback": [],
        "expectation_status": "INDETERMINATE",
    }
    if isinstance(error, subprocess.TimeoutExpired):
        return {**common, "execution_status": "timeout", "exit_category": "timeout", "exit_code": None, "timeout": True}
    if isinstance(error, OSError):
        return {**common, "execution_status": "unavailable", "exit_category": "unavailable", "exit_code": None}
    if error is not None:
        return {**common, "execution_status": "crashed", "exit_category": "crash", "exit_code": -1, "crash": True}
    returncode = int(proc.returncode)
    if returncode == 0:
        return {
            **common,
            "execution_status": "completed",
            "exit_category": "accepted",
            "exit_code": 0,
            "downstream_invalidated": [],
            "expectation_status": "ACCEPTED",
        }
    if returncode == 1:
        combined = (stdout + b"\n" + stderr).decode("utf-8", errors="replace").strip()
        lowered = combined.lower()
        adapter = _adapter_for(registry, checker_id)
        markers = [str(marker) for marker in adapter["required_markers"]]
        if (
            not combined
            or "traceback" in lowered
            or "usage:" in lowered
            or "unrecognized argument" in lowered
            or any(marker not in combined for marker in markers)
        ):
            return {
                **common,
                "execution_status": "completed",
                "exit_category": "malformed-diagnostic",
                "exit_code": 1,
                "malformed_diagnostic": True,
            }
        adapter_id = str(adapter["adapter_id"])
        message = next(
            line.strip()
            for line in combined.splitlines()
            if all(marker in line for marker in markers)
        )
        return {
            **common,
            "execution_status": "completed",
            "exit_category": "structural-rejection",
            "exit_code": 1,
            "diagnostic_adapter_id": adapter_id,
            "diagnostic": {
                "diagnostic_id": f"{adapter_id}:{checker_id}",
                "earliest_stage": "07",
                "failure_class": "captured_output_structural",
                "failure_subcode": f"{checker_id}-structural-rejection",
                "message": message,
            },
            "expectation_status": "REJECTED_EXPECTED",
        }
    if returncode == 2:
        return {
            **common,
            "execution_status": "completed",
            "exit_category": "usage-error",
            "exit_code": 2,
            "usage_error": True,
        }
    return {
        **common,
        "execution_status": "crashed",
        "exit_category": "crash",
        "exit_code": returncode,
        "crash": True,
    }


def _aggregate(results: list[dict[str, Any]]) -> str:
    if not results:
        return "NOT_RUN"
    fallback: str | None = None
    for row in results:
        category = str(row["exit_category"])
        if category == "accepted":
            continue
        if category == "structural-rejection":
            if row.get("expectation_status") == "REJECTED_EXPECTED":
                return "FAIL_STRUCTURAL"
            fallback = "QUARANTINED_INCOMPLETE_EVIDENCE"
            continue
        if category in {"usage-error", "timeout", "crash", "malformed-diagnostic", "unavailable"}:
            return "INFRASTRUCTURE_ERROR"
        fallback = "QUARANTINED_INCOMPLETE_EVIDENCE"
    return fallback or "PASS_STRUCTURAL"


def verify(
    input_path: Path,
    output_path: Path,
    *,
    profile_id: str,
    verdict_id: str,
    source_commit: str,
    root: Path = ROOT,
    run_process: Callable[..., Any] = subprocess.run,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Run one exact registry profile against immutable private artifact custody."""

    if profile_id != PROFILE_ID:
        raise ValueError(f"candidate verifier supports only profile {PROFILE_ID}")
    if not verdict_id:
        raise ValueError("verdict_id must be non-empty")
    if not HEX40.fullmatch(source_commit):
        raise ValueError("source_commit must be an exact lowercase 40-hex commit")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    root = root.resolve(strict=True)
    input_file = _repo_file(root, input_path, "input")
    output_file = _repo_file(root, output_path, "output")
    if input_file == output_file:
        raise ValueError("input and output must be distinct repository files")
    input_bytes = input_file.read_bytes()
    output_bytes = output_file.read_bytes()
    registry_snapshot = snapshot_registry(root=root)
    unbound_plan = profile_invocations(registry_snapshot.value, PROFILE_ID, root=root)
    _exact_checker_plan(registry_snapshot.value, profile_id, unbound_plan)

    custody_parent = root / ".daee" / "validation" / "candidate-replay"
    custody_parent.mkdir(parents=True, exist_ok=True)
    started_at = _utc_now()
    started = time.monotonic()
    logical_argv = [
        "verify_candidate_output.py",
        "--profile", profile_id,
        "--input", input_file.relative_to(root).as_posix(),
        "--output", output_file.relative_to(root).as_posix(),
        "--verdict-id", verdict_id,
        "--source-commit", source_commit,
    ]
    launch_core = {"started_at": started_at, "argv_sha256": canonical_sha256(logical_argv)}
    results: list[dict[str, Any]] = []
    execution_manifest: dict[str, Any]
    with tempfile.TemporaryDirectory(prefix="replay-", dir=custody_parent) as temp:
        custody = Path(temp)
        frozen_input = custody / "input.snapshot"
        frozen_output = custody / "output.snapshot.md"
        _write_private(frozen_input, input_bytes)
        _write_private(frozen_output, output_bytes)
        _assert_bytes(frozen_input, input_bytes, "private input snapshot")
        _assert_bytes(frozen_output, output_bytes, "private output snapshot")
        plan = profile_invocations(
            registry_snapshot.value,
            PROFILE_ID,
            bindings={"output": str(frozen_output)},
            root=root,
        )
        _exact_checker_plan(registry_snapshot.value, profile_id, plan)
        execution = create_execution_snapshot(
            root=root,
            destination=custody / "execution",
            plan=plan,
            output_path=frozen_output,
        )
        plan = execution.bind_plan(plan, original_output=frozen_output)
        execution_manifest = execution.manifest
        frozen_sources: list[tuple[dict[str, Any], Path, bytes, Path]] = []
        for row in plan:
            checker_id = str(row["checker_id"])
            tool = _repo_file(root, Path(str(row["source_path"])), f"checker {checker_id}")
            expected_tool = tool.read_bytes()
            if sha256_bytes(expected_tool) != row["source_sha256"]:
                raise ValueError(f"{checker_id}: checker source changed during candidate verification")
            source_snapshot = execution.source_path(row)
            _assert_bytes(source_snapshot, expected_tool, f"private checker {checker_id} snapshot")
            frozen_sources.append((row, tool, expected_tool, source_snapshot))

        for row, tool, expected_tool, source_snapshot in frozen_sources:
            checker_id = str(row["checker_id"])
            command = execution.checker_command(row)
            proc: Any | None = None
            error: BaseException | None = None
            try:
                proc = run_process(
                    command,
                    cwd=execution.root,
                    capture_output=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except (subprocess.TimeoutExpired, OSError) as exc:
                error = exc
            except BaseException as exc:  # noqa: BLE001 - classified as crash evidence
                error = exc
            _assert_bytes(source_snapshot, expected_tool, f"private checker {checker_id} snapshot")
            _assert_bytes(tool, expected_tool, f"checker {checker_id}")
            _assert_bytes(input_file, input_bytes, "input artifact")
            _assert_bytes(output_file, output_bytes, "output artifact")
            _assert_bytes(registry_snapshot.canonical_path, registry_snapshot.data, "validation registry")
            outcome = _classification(checker_id, proc, error, registry_snapshot.value)
            results.append(
                {
                    "checker_id": checker_id,
                    "tool_path": str(row["source_path"]),
                    "tool_sha256": str(row["source_sha256"]),
                    "artifact_type": "output-md",
                    "artifact_sha256": sha256_bytes(output_bytes),
                    **outcome,
                }
            )
        _assert_bytes(frozen_input, input_bytes, "private input snapshot")
        _assert_bytes(frozen_output, output_bytes, "private output snapshot")
        for row, _tool, expected_tool, source_snapshot in frozen_sources:
            _assert_bytes(
                source_snapshot,
                expected_tool,
                f"private checker {row['checker_id']} snapshot",
            )
        execution.verify()
    for row in plan:
        tool = root / str(row["source_path"])
        if sha256_bytes(tool.read_bytes()) != row["source_sha256"]:
            raise ValueError(f"checker {row['checker_id']} changed during candidate verification")
    _assert_bytes(input_file, input_bytes, "input artifact")
    _assert_bytes(output_file, output_bytes, "output artifact")
    _assert_bytes(registry_snapshot.canonical_path, registry_snapshot.data, "validation registry")

    finished_at = _utc_now()
    completion_core = {
        "finished_at": finished_at,
        "duration_ms": max(0, int((time.monotonic() - started) * 1000)),
    }
    verdict = {
        "schema": "daee-checker-replay-verdict-v1",
        "verdict_id": verdict_id,
        "source_commit": source_commit,
        "selected_profile": profile_id,
        "registry_path": registry_snapshot.relative_path,
        "registry_sha256": registry_snapshot.sha256,
        "execution_snapshot": execution_manifest,
        "launch": {**launch_core, "record_sha256": canonical_sha256(launch_core)},
        "completion": {**completion_core, "record_sha256": canonical_sha256(completion_core)},
        "artifacts": [
            {
                "role": "input",
                "artifact_type": "input-output-pair",
                "path": input_file.relative_to(root).as_posix(),
                "sha256": sha256_bytes(input_bytes),
            },
            {
                "role": "output",
                "artifact_type": "output-md",
                "path": output_file.relative_to(root).as_posix(),
                "sha256": sha256_bytes(output_bytes),
            },
        ],
        "checker_results": results,
        "aggregate_status": _aggregate(results),
        "mutation_fault_id": None,
        "structural_non_claims": [
            "structural checker replay only",
            "not semantic truth or interlocutor uptake",
            "not model proof, provenance, candidate maturity, or release readiness",
        ],
    }
    findings = validate_verdict(verdict, registry_snapshot.value, root=root, verify_files=True)
    if findings:
        first = findings[0]
        raise ValueError(
            f"canonical replay verdict rejected [{first.failure_class}/{first.failure_subcode}] {first.message}"
        )
    return verdict


def failing_checkers(verdict: dict[str, Any]) -> list[str]:
    return [
        str(row["checker_id"])
        for row in verdict.get("checker_results", [])
        if row.get("exit_category") == "structural-rejection"
    ]


def publish_verdict(
    verdict: dict[str, Any],
    target: Path,
    *,
    root: Path = ROOT,
    fault_at: str | None = None,
) -> None:
    """Validate and atomically publish fresh verdict bytes without replacement."""

    root = root.resolve(strict=True)
    try:
        destination = resolve_repo_path(root, target, must_exist=False)
    except PathCustodyError as exc:
        raise ValueError(f"json-out must be repository-relative: {exc}") from exc
    protected = {
        resolve_repo_path(root, verdict["registry_path"], must_exist=True, expect_file=True),
        *(resolve_repo_path(root, row["path"], must_exist=True, expect_file=True) for row in verdict["artifacts"]),
        *(resolve_repo_path(root, row["tool_path"], must_exist=True, expect_file=True) for row in verdict["checker_results"]),
    }
    if destination in protected:
        raise ValueError("json-out collides with protected evidence")
    registry_snapshot = snapshot_registry(verdict["registry_path"], root=root)
    findings = validate_verdict(verdict, registry_snapshot.value, root=root, verify_files=True)
    if findings:
        first = findings[0]
        raise ValueError(f"verdict changed before publication [{first.failure_class}/{first.failure_subcode}]")
    data = (json.dumps(verdict, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    try:
        atomic_publish_bytes(destination, data, fault_at=fault_at)
    except PublicationError as exc:
        raise ValueError(str(exc)) from exc
    post_registry = snapshot_registry(verdict["registry_path"], root=root)
    post_findings = validate_verdict(verdict, post_registry.value, root=root, verify_files=True)
    if post_findings:
        first = post_findings[0]
        raise ValueError(f"verdict evidence changed during publication [{first.failure_class}/{first.failure_subcode}]")


def _source_commit(root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    value = proc.stdout.strip().lower()
    if proc.returncode != 0 or not HEX40.fullmatch(value):
        raise ValueError("could not derive exact source commit from repository HEAD")
    return value


def self_test() -> int:
    def accepted(_command: list[str], **_kwargs: Any) -> Any:
        return type("Completed", (), {"returncode": 0, "stdout": b"accepted\n", "stderr": b""})()

    verdict = verify(
        Path("tests/validation-integrity/artifacts/input.txt"),
        Path("tests/validation-integrity/artifacts/output.md"),
        profile_id=PROFILE_ID,
        verdict_id="candidate-self-test",
        source_commit="0" * 40,
        run_process=accepted,
    )
    checks = [
        ("canonical replay schema", verdict["schema"] == "daee-checker-replay-verdict-v1"),
        ("exact nonempty profile", len(verdict["checker_results"]) == 12),
        ("canonical verdict roundtrip", validate_verdict(verdict, snapshot_registry().value) == []),
    ]
    ok = all(passed for _name, passed in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"verify-candidate-output self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=[PROFILE_ID])
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--verdict-id")
    parser.add_argument("--source-commit")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    missing = [
        name
        for name, value in (
            ("--profile", args.profile),
            ("--input", args.input),
            ("--output", args.output),
            ("--json-out", args.json_out),
            ("--verdict-id", args.verdict_id),
        )
        if value is None
    ]
    if missing:
        parser.error("required argument(s): " + ", ".join(missing))
    try:
        head_commit = _source_commit(ROOT)
        if args.source_commit is not None and args.source_commit.lower() != head_commit:
            raise ValueError("explicit source commit does not match repository HEAD")
        source_commit = head_commit
        verdict = verify(
            args.input,
            args.output,
            profile_id=args.profile,
            verdict_id=args.verdict_id,
            source_commit=source_commit,
            timeout_seconds=args.timeout_seconds,
        )
        publish_verdict(verdict, args.json_out)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"candidate replay failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    if verdict["aggregate_status"] == "PASS_STRUCTURAL":
        return 0
    if verdict["aggregate_status"] == "FAIL_STRUCTURAL":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
