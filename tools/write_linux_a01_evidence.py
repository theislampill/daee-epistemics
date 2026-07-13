#!/usr/bin/env python3
"""Run and create-once publish the native-Linux A01 CI evidence JSON."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Sequence

from a16_immutable_custody import CustodyError, claim_json_once, strict_snapshot
from contract_validation import PathCustodyError, resolve_repo_path, validate_schema_subset
from source_provenance import strict_json_loads


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "ci-readback.schema.json"
CHECKER_PATH = "tools/check_captured_output_manifest.py"
TEST_PATH = "tests/captured-output-custody/test_contract.py"
COMMAND = "python tools/check_captured_output_manifest.py --self-test"
STEP_NAME = "Linux A01 custody self-test"


def _git(arguments: Sequence[str], *, binary: bool = False) -> bytes | str:
    env = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}
    completed = subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=not binary,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", "replace") if binary else completed.stderr
        raise ValueError(f"git {' '.join(arguments)} failed: {stderr.strip()}")
    return completed.stdout


def _source_file_identity(source_sha: str, path: str) -> dict[str, str]:
    blob_oid = str(_git(["rev-parse", f"{source_sha}:{path}"])).strip()
    object_type = str(_git(["cat-file", "-t", blob_oid])).strip()
    if object_type != "blob":
        raise ValueError(f"{path} resolves to {object_type!r}, not blob")
    raw = bytes(_git(["show", f"{source_sha}:{path}"], binary=True))
    working = (ROOT / path).read_bytes()
    if working != raw:
        raise ValueError(f"{path} working bytes differ from exact source blob {blob_oid}")
    return {"path": path, "blob_oid": blob_oid, "raw_sha256": hashlib.sha256(raw).hexdigest()}


def _suite_result(stdout: bytes, stderr: bytes) -> tuple[int, str, int]:
    combined = stdout + b"\n" + stderr
    text = combined.decode("utf-8", "replace")
    matches = re.findall(r"(?m)^Ran ([0-9]+) tests? in ", text)
    if len(matches) != 1:
        raise ValueError("A01 self-test output must contain exactly one unittest count marker")
    if re.search(r"(?m)^OK(?:\s|$)", text) is None:
        raise ValueError("A01 self-test output is missing the exact OK status marker")
    skipped = [int(value) for value in re.findall(r"skipped=([0-9]+)", text)]
    skipped_count = sum(skipped)
    if skipped_count != 0:
        raise ValueError(f"A01 self-test skipped {skipped_count} test(s)")
    return int(matches[0]), "OK", 0


def _evidence_id(source_sha: str, run_id: int, run_attempt: int, job_name: str) -> str:
    return hashlib.sha256(
        b"daee-linux-a01-ci-evidence-v1\0"
        + source_sha.encode("ascii")
        + b"\0"
        + str(run_id).encode("ascii")
        + b"\0"
        + str(run_attempt).encode("ascii")
        + b"\0"
        + job_name.encode("utf-8")
    ).hexdigest()


def _evidence_schema() -> dict[str, Any]:
    schema = strict_json_loads(SCHEMA_PATH.read_bytes(), label=str(SCHEMA_PATH))
    if not isinstance(schema, dict) or not isinstance(schema.get("$defs"), dict):
        raise ValueError("ci-readback schema definitions are unavailable")
    return {"$defs": schema["$defs"], "$ref": "#/$defs/linux_a01_evidence"}


def build_evidence(
    *,
    source_sha: str,
    run_id: int,
    run_number: int,
    run_attempt: int,
    job_name: str,
    runner_label: str,
    runner_os: str,
    runner_arch: str,
    runner_name: str,
    runner_environment: str,
    stdout: bytes,
    stderr: bytes,
    checker: dict[str, str],
    contract_test: dict[str, str],
) -> dict[str, Any]:
    test_count, suite_status, skipped_count = _suite_result(stdout, stderr)
    value = {
        "schema": "daee-linux-a01-ci-evidence-v1",
        "evidence_id": _evidence_id(source_sha, run_id, run_attempt, job_name),
        "source_sha": source_sha,
        "run_id": run_id,
        "run_number": run_number,
        "run_attempt": run_attempt,
        "job_name": job_name,
        "runner_os": runner_os,
        "runner_arch": runner_arch,
        "runner_name": runner_name,
        "runner_environment": runner_environment,
        "runner_label": runner_label,
        "step_name": STEP_NAME,
        "command": COMMAND,
        "checker": checker,
        "contract_test": contract_test,
        "suite_marker": TEST_PATH,
        "suite_test_count": test_count,
        "suite_status": suite_status,
        "skipped_count": skipped_count,
        "substituted": False,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "native_linux": True,
        "candidate_claim": False,
        "terminal_claim": False,
    }
    issues = validate_schema_subset(value, _evidence_schema())
    if issues:
        first = issues[0]
        raise ValueError(f"generated Linux A01 evidence violates schema at {first.path}: {first.message}")
    return value


def _publish(root: Path, target: Path, value: dict[str, Any]) -> str:
    root.mkdir(parents=True, exist_ok=True)
    digest = claim_json_once(root, target, value)
    observed, _raw, observed_digest = strict_snapshot(target)
    if observed != value or observed_digest != digest:
        raise CustodyError("Linux A01 evidence readback mismatch", subcode="readback-drift")
    return digest


def self_test() -> int:
    source_sha = "3" * 40
    stdout = b".......................\n----------------------------------------------------------------------\nRan 23 tests in 1.000s\n\nOK\n"
    stderr = b""
    identity = lambda path, prefix: {  # noqa: E731 - compact deterministic fixture
        "path": path,
        "blob_oid": prefix * 40,
        "raw_sha256": prefix * 64,
    }
    value = build_evidence(
        source_sha=source_sha,
        run_id=1001,
        run_number=77,
        run_attempt=1,
        job_name="runtime-checks",
        runner_label="ubuntu-latest",
        runner_os="Linux",
        runner_arch="X64",
        runner_name="self-test-runner",
        runner_environment="github-hosted",
        stdout=stdout,
        stderr=stderr,
        checker=identity(CHECKER_PATH, "a"),
        contract_test=identity(TEST_PATH, "b"),
    )
    with tempfile.TemporaryDirectory(prefix="daee-linux-a01-writer-") as temporary:
        root = Path(temporary)
        target = root / "linux-a01.json"
        _publish(root, target, value)
        try:
            _publish(root, target, value)
        except CustodyError as exc:
            if exc.subcode != "claim-replay":
                print(f"linux A01 evidence writer self-test: FAIL (wrong replay subcode {exc.subcode})")
                return 1
        else:
            print("linux A01 evidence writer self-test: FAIL (create-once replay survived)")
            return 1
    print("linux A01 evidence writer self-test: PASS (schema, create-once, hash readback, replay rejection)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--run-number", type=int)
    parser.add_argument("--run-attempt", type=int)
    parser.add_argument("--job-name")
    parser.add_argument("--runner-label")
    parser.add_argument("--runner-environment")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        if any(
            value is not None
            for value in (
                args.out,
                args.source_sha,
                args.run_id,
                args.run_number,
                args.run_attempt,
                args.job_name,
                args.runner_label,
                args.runner_environment,
            )
        ):
            build_parser().error("--self-test cannot be combined with live evidence arguments")
        return self_test()
    missing = [
        name
        for name, value in (
            ("--out", args.out),
            ("--source-sha", args.source_sha),
            ("--run-id", args.run_id),
            ("--run-number", args.run_number),
            ("--run-attempt", args.run_attempt),
            ("--job-name", args.job_name),
            ("--runner-label", args.runner_label),
            ("--runner-environment", args.runner_environment),
        )
        if value is None
    ]
    if missing:
        build_parser().error(f"live evidence mode requires {', '.join(missing)}")
    if not sys.platform.startswith("linux") or os.environ.get("RUNNER_OS") != "Linux":
        print("linux A01 evidence: FAIL (native Linux GitHub runner is required)")
        return 1
    if args.runner_environment != "github-hosted":
        build_parser().error("--runner-environment must be github-hosted")
    if not re.fullmatch(r"[0-9a-f]{40}", str(args.source_sha)):
        build_parser().error("--source-sha must be a full lowercase Git OID")
    try:
        target = resolve_repo_path(ROOT, args.out, must_exist=False)
        head = str(_git(["rev-parse", "HEAD"])).strip()
        if head != args.source_sha:
            raise ValueError(f"source SHA {args.source_sha} differs from local HEAD {head}")
        checker_identity = _source_file_identity(args.source_sha, CHECKER_PATH)
        contract_test_identity = _source_file_identity(args.source_sha, TEST_PATH)
        completed = subprocess.run(
            [sys.executable, CHECKER_PATH, "--self-test"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise ValueError("native Linux A01 self-test failed during evidence emission")
        post_checker_identity = _source_file_identity(args.source_sha, CHECKER_PATH)
        post_contract_test_identity = _source_file_identity(args.source_sha, TEST_PATH)
        if post_checker_identity != checker_identity or post_contract_test_identity != contract_test_identity:
            raise ValueError("native Linux A01 checker/test source identity changed during execution")
        value = build_evidence(
            source_sha=args.source_sha,
            run_id=args.run_id,
            run_number=args.run_number,
            run_attempt=args.run_attempt,
            job_name=args.job_name,
            runner_label=args.runner_label,
            runner_os=os.environ["RUNNER_OS"],
            runner_arch=os.environ.get("RUNNER_ARCH", ""),
            runner_name=os.environ.get("RUNNER_NAME", ""),
            runner_environment=args.runner_environment,
            stdout=completed.stdout,
            stderr=completed.stderr,
            checker=checker_identity,
            contract_test=contract_test_identity,
        )
        digest = _publish(target.parent, target, value)
    except (CustodyError, OSError, PathCustodyError, ValueError) as exc:
        print(f"linux A01 evidence: FAIL ({exc})")
        return 1
    print(f"linux A01 evidence: PASS ({target.relative_to(ROOT).as_posix()} sha256={digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
