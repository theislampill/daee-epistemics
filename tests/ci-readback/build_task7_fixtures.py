#!/usr/bin/env python3
"""Build/check the hash-linked contentful Task 7 receipt fixture cohort."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
HERE = Path(__file__).resolve().parent
SUPPORT = HERE / "support"
VALID = HERE / "valid/required-checks-bound-to-pushed-sha.json"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import write_task7_deterministic_evidence as writer  # noqa: E402
import check_ci_readback as checker  # noqa: E402
import run_local_ci as local_ci  # noqa: E402


ROLE_BY_KIND = {
    "no-model-preflight": "no_model_preflight",
    "full-local-ci": "full_local_ci",
    "generated-freshness-package": "generated_freshness_package",
    "independent-whole-branch-review": "independent_whole_branch_review",
}
OBSERVED_AT = "2026-07-12T12:00:00Z"


def full_local_ci_pass_stdout() -> bytes:
    return local_ci.completion_stdout(
        local_ci.build_completion(
            start_at_command=1,
            strict_pwsh=True,
            command_timeout_seconds=900,
        )
    )


def pretty(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def artifact_ref(path: Path, raw: bytes) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def artifact_ref_at(path: Path, raw: bytes) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def native_no_model_report() -> dict[str, Any]:
    gates = [
        {
            "number": gate.number,
            "name": gate.name,
            "passed": True,
            "repair_lane": "",
            "steps": [
                {
                    "command": command,
                    "execution_profile": local_ci.execution_profile_for(command),
                    "returncode": writer.EXPECTED_GATE_RETURN_CODES.get(gate.number, 0),
                    "duration_sec": 0.001,
                    "timed_out": False,
                    "stdout_tail": "",
                }
                for command in (
                    writer.A16_GATE_COMMANDS.get(gate.name)
                    or (f"in-process: legacy gate {gate.number}",)
                )
            ],
        }
        for gate in writer.NO_MODEL_GATES
    ]
    commands = [step["command"] for gate in gates for step in gate["steps"]]
    return {
        "schema": "daee-no-model-preflight-report-v2",
        "decision": "MATRIX_AUTHORIZED_AFTER_PREFLIGHT",
        "complete": True,
        "gate_count": len(gates),
        "command_count": len(commands),
        "command_set_sha256": local_ci.command_list_sha256(commands),
        "execution_plan_sha256": local_ci.execution_plan_sha256(commands),
        "python_execution_profile_id": local_ci.PYTHON_EXECUTION_PROFILE_ID,
        "gates": gates,
    }


def linux_a01_job_log() -> bytes:
    full_ci_command = checker.FULL_CI_COMMAND
    return (
        "2026-07-12T12:10:00Z ##[group]Run python -B tools/check_captured_output_manifest.py --self-test\n"
        "2026-07-12T12:10:00Z python -B tools/check_captured_output_manifest.py --self-test\n"
        "2026-07-12T12:10:01Z .......................\n"
        "2026-07-12T12:10:01Z ----------------------------------------------------------------------\n"
        "2026-07-12T12:10:01Z Ran 23 tests in 1.000s\n"
        "2026-07-12T12:10:01Z\n"
        "2026-07-12T12:10:01Z OK\n"
        "2026-07-12T12:10:01Z ##[endgroup]\n"
        f"2026-07-12T12:11:00Z ##[group]Run {full_ci_command}\n"
        f"2026-07-12T12:11:00Z {full_ci_command}\n"
        "2026-07-12T12:20:00Z local CI: PASS\n"
        "2026-07-12T12:20:00Z ##[endgroup]\n"
    ).encode("utf-8")


def review_authorization(freeze: Mapping[str, Any]) -> dict[str, Any]:
    value = {
        "schema": "daee-task7-independent-review-authorization-v1",
        "authorization_id": "0" * 64,
        "issuer_identity": writer.REVIEW_AUTHORIZATION_ISSUER,
        "implementation_owner_identity": writer.IMPLEMENTATION_OWNER_IDENTITY,
        "reviewer_identity": "/root/task3b_ci_receipt/task3b_requirements_audit",
        "scope": "independent-whole-branch-review",
        "reviewed_branch": writer.BRANCH,
        "expected_final_tree_oid": freeze["expected_final_tree_oid"],
        "source_freeze_id": freeze["freeze_id"],
        "issued_at": "2026-07-12T11:59:00Z",
        "one_use": True,
        "owner_acceptance": False,
        "candidate_claim": False,
        "terminal_claim": False,
    }
    value["authorization_id"] = writer._review_authorization_id(value)
    writer.validate_review_authorization(value, freeze)
    return value


def review_record(
    freeze: Mapping[str, Any], authorization: Mapping[str, Any], authorization_ref: Mapping[str, Any]
) -> dict[str, Any]:
    value = {
        "schema": "daee-task7-whole-branch-review-v1",
        "review_id": "0" * 64,
        "reviewer": authorization["reviewer_identity"],
        "owner_identity": writer.IMPLEMENTATION_OWNER_IDENTITY,
        "review_authorization_id": authorization["authorization_id"],
        "review_authorization": dict(authorization_ref),
        "independent_from_owner": True,
        "reviewed_branch": writer.BRANCH,
        "reviewed_tree_oid": freeze["expected_final_tree_oid"],
        "source_freeze_id": freeze["freeze_id"],
        "manifest": writer._review_manifest(freeze),
        "findings": {"critical": 0, "important": 0, "minor": 0},
        "verdict": "ACCEPT",
        "reviewed_at": OBSERVED_AT,
        "owner_acceptance": False,
        "candidate_claim": False,
        "terminal_claim": False,
    }
    value["review_id"] = writer._review_id(value)
    writer.validate_whole_branch_review(value, freeze, authorization, authorization_ref)
    return value


def role_results(kind: str) -> list[tuple[list[str], bytes, bytes]]:
    if kind == "no-model-preflight":
        return [(copy.deepcopy(writer.ROLE_CHECKS[kind][0]), b"MATRIX_AUTHORIZED_AFTER_PREFLIGHT\n", b"")]
    if kind == "full-local-ci":
        return [(copy.deepcopy(writer.ROLE_CHECKS[kind][0]), full_local_ci_pass_stdout(), b"")]
    if kind == "generated-freshness-package":
        return [(copy.deepcopy(command), b"PASS\n", b"") for command in writer.ROLE_CHECKS[kind]]
    return []


def build_expected() -> dict[Path, bytes]:
    expected: dict[Path, bytes] = {}
    namespace_id = writer.DEFAULT_NAMESPACE_ID
    contract = writer.namespace_contract(namespace_id)
    linux_log_path = SUPPORT / "linux-a01-job.log"
    linux_log_raw = linux_a01_job_log()
    linux_log_segment, _test_count, _status, _skipped = checker._a01_log(linux_log_raw)
    expected[linux_log_path] = linux_log_raw
    files = [
        {
            "path": writer.PRODUCER_PATH,
            "blob_oid": "a" * 40,
            "byte_count": 123,
            "raw_sha256": "b" * 64,
        },
        {
            "path": "docs/.nojekyll",
            "blob_oid": "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
            "byte_count": 0,
            "raw_sha256": hashlib.sha256(b"").hexdigest(),
        },
    ]
    freeze = writer.build_source_freeze("4" * 40, files)
    freeze_path = SUPPORT / "task7-source-freeze.json"
    freeze_raw = pretty(freeze)
    expected[freeze_path] = freeze_raw

    native_path = SUPPORT / "task7-no-model-preflight-native-report.json"
    native_raw = pretty(native_no_model_report())
    expected[native_path] = native_raw
    full_ci_native_path = SUPPORT / "task7-full-local-ci-native-report.json"
    full_ci_native_raw = pretty(
        local_ci.build_completion(
            start_at_command=1,
            strict_pwsh=True,
            command_timeout_seconds=900,
        )
    )
    expected[full_ci_native_path] = full_ci_native_raw
    authorization_path = SUPPORT / "task7-independent-review-authorization.json"
    authorization = review_authorization(freeze)
    authorization_raw = pretty(authorization)
    expected[authorization_path] = authorization_raw
    authorization_ref = artifact_ref_at(
        writer.review_authorization_rel(namespace_id), authorization_raw
    )
    review_path = SUPPORT / "task7-independent-whole-branch-review-record.json"
    review_raw = pretty(review_record(freeze, authorization, authorization_ref))
    expected[review_path] = review_raw

    producer = {key: files[0][key] for key in ("path", "blob_oid", "raw_sha256")}
    bundle_raw_by_kind: dict[str, bytes] = {}
    bundle_by_kind: dict[str, dict[str, Any]] = {}
    for kind in ROLE_BY_KIND:
        results = role_results(kind)
        log_path = SUPPORT / f"task7-{kind}.log"
        log_raw = pretty(writer.build_command_log(kind, results))
        expected[log_path] = log_raw
        evidence_artifacts: list[dict[str, Any]] = []
        if kind == "no-model-preflight":
            evidence_artifacts.append(
                artifact_ref_at(writer.native_report_rel(kind, namespace_id), native_raw)
            )
        elif kind == "full-local-ci":
            evidence_artifacts.append(
                artifact_ref_at(writer.native_report_rel(kind, namespace_id), full_ci_native_raw)
            )
        elif kind == "independent-whole-branch-review":
            evidence_artifacts.append(authorization_ref)
            evidence_artifacts.append(
                artifact_ref_at(contract.whole_branch_review_rel, review_raw)
            )
        report = writer.build_result_report(
            kind=kind,
            results=results,
            evidence_artifacts=evidence_artifacts,
            producer=producer,
            freeze=freeze,
            observed_at=OBSERVED_AT,
            namespace_id=namespace_id,
        )
        report_path = SUPPORT / f"task7-{kind}-report.json"
        report_raw = pretty(report)
        expected[report_path] = report_raw
        bundle = writer.build_evidence(
            kind=kind,
            command=writer.producer_command(kind, namespace_id),
            report=artifact_ref_at(writer.report_rel(kind, namespace_id), report_raw),
            log=artifact_ref_at(writer.log_rel(kind, namespace_id), log_raw),
            checker=producer,
            source_freeze=artifact_ref_at(contract.source_freeze_rel, freeze_raw),
            freeze=freeze,
            observed_at=OBSERVED_AT,
            namespace_id=namespace_id,
        )
        bundle_path = SUPPORT / f"task7-{kind}.json"
        bundle_raw = pretty(bundle)
        expected[bundle_path] = bundle_raw
        bundle_by_kind[kind] = bundle
        bundle_raw_by_kind[kind] = bundle_raw

    wrong_source = copy.deepcopy(bundle_by_kind["no-model-preflight"])
    wrong_source["expected_final_tree_oid"] = "5" * 40
    wrong_source_path = SUPPORT / "task7-wrong-source.json"
    wrong_source_raw = pretty(wrong_source)
    expected[wrong_source_path] = wrong_source_raw

    noop = copy.deepcopy(bundle_by_kind["no-model-preflight"])
    noop["checker"] = {
        "path": "tests/ci-readback/support/task7-verdict-checker.py",
        "blob_oid": "c" * 40,
        "raw_sha256": "d" * 64,
    }
    noop["command"] = ["python", "tests/ci-readback/support/task7-verdict-checker.py"]
    noop["command_sha256"] = writer._command_digest(noop["command"])
    noop["evidence_id"] = writer._evidence_id(
        noop["kind"],
        noop["freeze_id"],
        noop["command_sha256"],
        noop["report"]["sha256"],
        noop["log"]["sha256"],
    )
    noop_path = SUPPORT / "task7-noop-role-command.json"
    noop_raw = pretty(noop)
    expected[noop_path] = noop_raw

    timeout_drift_results = [
        (["python", "tools/run_local_ci.py", "--strict-pwsh"], full_local_ci_pass_stdout(), b"")
    ]
    timeout_drift_log_path = SUPPORT / "task7-full-local-ci-timeout-drift.log"
    timeout_drift_log_raw = pretty(writer.build_command_log("full-local-ci", timeout_drift_results))
    expected[timeout_drift_log_path] = timeout_drift_log_raw
    timeout_drift_report = writer.build_result_report(
        kind="full-local-ci",
        results=timeout_drift_results,
        evidence_artifacts=[],
        producer=producer,
        freeze=freeze,
        observed_at=OBSERVED_AT,
        namespace_id=namespace_id,
    )
    timeout_drift_report_path = SUPPORT / "task7-full-local-ci-timeout-drift-report.json"
    timeout_drift_report_raw = pretty(timeout_drift_report)
    expected[timeout_drift_report_path] = timeout_drift_report_raw
    timeout_drift_bundle = writer.build_evidence(
        kind="full-local-ci",
        command=writer.producer_command("full-local-ci", namespace_id),
        report=artifact_ref_at(
            writer.report_rel("full-local-ci", namespace_id), timeout_drift_report_raw
        ),
        log=artifact_ref_at(
            writer.log_rel("full-local-ci", namespace_id), timeout_drift_log_raw
        ),
        checker=producer,
        source_freeze=artifact_ref_at(contract.source_freeze_rel, freeze_raw),
        freeze=freeze,
        observed_at=OBSERVED_AT,
        namespace_id=namespace_id,
    )
    timeout_drift_bundle_path = SUPPORT / "task7-full-local-ci-timeout-drift.json"
    timeout_drift_bundle_raw = pretty(timeout_drift_bundle)
    expected[timeout_drift_bundle_path] = timeout_drift_bundle_raw

    command_count = len(local_ci.COMMANDS)
    forged_stdout = (
        f"run_local_ci: PASS ({command_count} command(s), indices 1-{command_count})\n"
    ).encode("ascii")
    forged_log = json.loads(expected[SUPPORT / "task7-full-local-ci.log"])
    forged_log["entries"][0]["stdout_base64"] = base64.b64encode(forged_stdout).decode("ascii")
    forged_log_path = SUPPORT / "task7-full-local-ci-forged-marker.log"
    forged_log_raw = pretty(forged_log)
    expected[forged_log_path] = forged_log_raw
    forged_report = json.loads(expected[SUPPORT / "task7-full-local-ci-report.json"])
    forged_result = forged_report["executed_checks"][0]
    forged_result.pop("completion", None)
    forged_result["stdout_byte_count"] = len(forged_stdout)
    forged_result["stdout_sha256"] = hashlib.sha256(forged_stdout).hexdigest()
    forged_report["report_id"] = writer._report_id(forged_report)
    forged_report_path = SUPPORT / "task7-full-local-ci-forged-marker-report.json"
    forged_report_raw = pretty(forged_report)
    expected[forged_report_path] = forged_report_raw
    forged_bundle = copy.deepcopy(bundle_by_kind["full-local-ci"])
    forged_bundle["report"] = artifact_ref_at(
        writer.report_rel("full-local-ci", namespace_id), forged_report_raw
    )
    forged_bundle["log"] = artifact_ref_at(
        writer.log_rel("full-local-ci", namespace_id), forged_log_raw
    )
    forged_bundle["evidence_id"] = writer._evidence_id(
        forged_bundle["kind"],
        forged_bundle["freeze_id"],
        forged_bundle["command_sha256"],
        forged_bundle["report"]["sha256"],
        forged_bundle["log"]["sha256"],
    )
    forged_bundle_path = SUPPORT / "task7-full-local-ci-forged-marker.json"
    forged_bundle_raw = pretty(forged_bundle)
    expected[forged_bundle_path] = forged_bundle_raw

    profile_log = json.loads(expected[SUPPORT / "task7-no-model-preflight.log"])
    profile_log["entries"][0]["execution_profile"]["python_flags"] = ["-I", "-B"]
    profile_log["entries"][0]["execution_profile"]["environment_policy"] = "inherit-v1"
    profile_log_path = SUPPORT / "task7-execution-profile-drift.log"
    profile_log_raw = pretty(profile_log)
    expected[profile_log_path] = profile_log_raw
    profile_report = json.loads(expected[SUPPORT / "task7-no-model-preflight-report.json"])
    profile_report["executed_checks"][0]["execution_profile"] = copy.deepcopy(
        profile_log["entries"][0]["execution_profile"]
    )
    profile_report["report_id"] = writer._report_id(profile_report)
    profile_report_path = SUPPORT / "task7-execution-profile-drift-report.json"
    profile_report_raw = pretty(profile_report)
    expected[profile_report_path] = profile_report_raw
    profile_bundle = copy.deepcopy(bundle_by_kind["no-model-preflight"])
    profile_bundle["report"] = artifact_ref_at(
        writer.report_rel("no-model-preflight", namespace_id), profile_report_raw
    )
    profile_bundle["log"] = artifact_ref_at(
        writer.log_rel("no-model-preflight", namespace_id), profile_log_raw
    )
    profile_bundle["evidence_id"] = writer._evidence_id(
        profile_bundle["kind"],
        profile_bundle["freeze_id"],
        profile_bundle["command_sha256"],
        profile_bundle["report"]["sha256"],
        profile_bundle["log"]["sha256"],
    )
    profile_bundle_path = SUPPORT / "task7-execution-profile-drift.json"
    profile_bundle_raw = pretty(profile_bundle)
    expected[profile_bundle_path] = profile_bundle_raw

    removed_name_log = json.loads(expected[SUPPORT / "task7-no-model-preflight.log"])
    removed_name_log["entries"][0]["execution_profile"]["removed_environment_names"] = [
        "pythonLocation"
    ]
    removed_name_log_path = SUPPORT / "task7-removed-environment-name-profile-drift.log"
    removed_name_log_raw = pretty(removed_name_log)
    expected[removed_name_log_path] = removed_name_log_raw
    removed_name_report = json.loads(expected[SUPPORT / "task7-no-model-preflight-report.json"])
    removed_name_report["executed_checks"][0]["execution_profile"] = copy.deepcopy(
        removed_name_log["entries"][0]["execution_profile"]
    )
    removed_name_report["report_id"] = writer._report_id(removed_name_report)
    removed_name_report_path = SUPPORT / "task7-removed-environment-name-profile-drift-report.json"
    removed_name_report_raw = pretty(removed_name_report)
    expected[removed_name_report_path] = removed_name_report_raw
    removed_name_bundle = copy.deepcopy(bundle_by_kind["no-model-preflight"])
    removed_name_bundle["report"] = artifact_ref_at(
        writer.report_rel("no-model-preflight", namespace_id), removed_name_report_raw
    )
    removed_name_bundle["log"] = artifact_ref_at(
        writer.log_rel("no-model-preflight", namespace_id), removed_name_log_raw
    )
    removed_name_bundle["evidence_id"] = writer._evidence_id(
        removed_name_bundle["kind"],
        removed_name_bundle["freeze_id"],
        removed_name_bundle["command_sha256"],
        removed_name_bundle["report"]["sha256"],
        removed_name_bundle["log"]["sha256"],
    )
    removed_name_bundle_path = SUPPORT / "task7-removed-environment-name-profile-drift.json"
    removed_name_bundle_raw = pretty(removed_name_bundle)
    expected[removed_name_bundle_path] = removed_name_bundle_raw

    receipt = json.loads(VALID.read_text(encoding="utf-8"))
    receipt["job_log"]["byte_count"] = len(linux_log_raw)
    receipt["job_log"]["sha256"] = hashlib.sha256(linux_log_raw).hexdigest()
    receipt["linux_a01"]["job_log_sha256"] = hashlib.sha256(linux_log_raw).hexdigest()
    receipt["linux_a01"]["log_segment_sha256"] = hashlib.sha256(linux_log_segment).hexdigest()
    for kind, role in ROLE_BY_KIND.items():
        raw = bundle_raw_by_kind[kind]
        receipt["deterministic_verdicts"][role] = {
            **artifact_ref_at(
                contract.evidence_rel / writer.ROLE_FILE_BY_KIND[kind], raw
            ),
            "artifact_schema": "daee-task7-deterministic-evidence-v1",
            "kind": kind,
            "status": writer.STATUS_BY_KIND[kind],
        }
    expected[VALID] = pretty(receipt)

    replay_path = HERE / "invalid/replayed-task7-evidence.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    no_model_path = SUPPORT / "task7-no-model-preflight.json"
    no_model_raw = bundle_raw_by_kind["no-model-preflight"]
    replay["operations"] = [
        {
            "op": "task7-artifact-substitute",
            "role": "full_local_ci",
            "source": no_model_path.relative_to(ROOT).as_posix(),
        }
    ]
    expected[replay_path] = pretty(replay)

    wrong_path = HERE / "invalid/wrong-source-task7-evidence.json"
    wrong = json.loads(wrong_path.read_text(encoding="utf-8"))
    wrong["operations"] = [
        {
            "op": "task7-artifact-substitute",
            "role": "no_model_preflight",
            "source": wrong_source_path.relative_to(ROOT).as_posix(),
        }
    ]
    expected[wrong_path] = pretty(wrong)

    noop_fixture_path = HERE / "invalid/noop-task7-role-command.json"
    noop_fixture = {
        "fixture_schema": "daee-checker-fixture-v1",
        "base": VALID.relative_to(ROOT).as_posix(),
        "operations": [
            {
                "op": "task7-artifact-substitute",
                "role": "no_model_preflight",
                "source": noop_path.relative_to(ROOT).as_posix(),
            },
        ],
    }
    expected[noop_fixture_path] = pretty(noop_fixture)

    timeout_drift_fixture_path = HERE / "invalid/full-local-ci-timeout-command-drift.json"
    timeout_drift_fixture = {
        "fixture_schema": "daee-checker-fixture-v1",
        "base": VALID.relative_to(ROOT).as_posix(),
        "operations": [
            {
                "op": "task7-artifact-substitute",
                "role": "full_local_ci",
                "source": timeout_drift_bundle_path.relative_to(ROOT).as_posix(),
            },
        ],
    }
    expected[timeout_drift_fixture_path] = pretty(timeout_drift_fixture)

    forged_fixture_path = HERE / "invalid/forged-full-local-ci-pass-marker.json"
    expected[forged_fixture_path] = pretty(
        {
            "fixture_schema": "daee-checker-fixture-v1",
            "base": VALID.relative_to(ROOT).as_posix(),
            "operations": [
                {
                    "op": "task7-artifact-substitute",
                    "role": "full_local_ci",
                    "source": forged_bundle_path.relative_to(ROOT).as_posix(),
                },
            ],
        }
    )
    profile_fixture_path = HERE / "invalid/task7-execution-profile-drift.json"
    expected[profile_fixture_path] = pretty(
        {
            "fixture_schema": "daee-checker-fixture-v1",
            "base": VALID.relative_to(ROOT).as_posix(),
            "operations": [
                {
                    "op": "task7-artifact-substitute",
                    "role": "no_model_preflight",
                    "source": profile_bundle_path.relative_to(ROOT).as_posix(),
                },
            ],
        }
    )
    removed_name_fixture_path = HERE / "invalid/task7-removed-environment-name-profile-drift.json"
    expected[removed_name_fixture_path] = pretty(
        {
            "fixture_schema": "daee-checker-fixture-v1",
            "base": VALID.relative_to(ROOT).as_posix(),
            "operations": [
                {
                    "op": "task7-artifact-substitute",
                    "role": "no_model_preflight",
                    "source": removed_name_bundle_path.relative_to(ROOT).as_posix(),
                },
            ],
        }
    )
    locator_fixture_path = HERE / "invalid/task7-primary-locator-substitution.json"
    expected[locator_fixture_path] = pretty(
        {
            "fixture_schema": "daee-checker-fixture-v1",
            "base": VALID.relative_to(ROOT).as_posix(),
            "operations": [
                {
                    "op": "set",
                    "path": "deterministic_verdicts.no_model_preflight.path",
                    "value": no_model_path.relative_to(ROOT).as_posix(),
                }
            ],
        }
    )
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    problems: list[str] = []
    for path, expected in build_expected().items():
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
        elif not path.is_file() or path.read_bytes() != expected:
            problems.append(path.relative_to(ROOT).as_posix())
    if problems:
        print("Task 7 fixture cohort: FAIL (drift: " + ", ".join(problems) + ")")
        return 1
    print(f"Task 7 fixture cohort: PASS ({len(build_expected())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
