#!/usr/bin/env python3
"""Permanent Task 3b contract for exact-SHA CI and Linux A01 custody."""
from __future__ import annotations

import base64
import copy
import contextlib
import json
import hashlib
import importlib
import ctypes
import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
HERE = Path(__file__).resolve().parent
CHECKER = TOOLS / "check_ci_readback.py"
LINUX_WRITER = TOOLS / "write_linux_a01_evidence.py"
TASK7_WRITER = TOOLS / "write_task7_deterministic_evidence.py"
SCHEMA = ROOT / "schema" / "ci-readback.schema.json"
EXPECTATION_SCHEMA = ROOT / "schema" / "negative-fixture-expectation.schema.json"
VALID = HERE / "valid" / "required-checks-bound-to-pushed-sha.json"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from contract_validation import validate_schema_definition, validate_schema_subset  # noqa: E402


REQUIRED_NEGATIVES = {
    "green-checks-for-another-sha",
    "pull-request-run-substitution",
    "manual-release-workflow-substitution",
    "workflow-blob-drift",
    "workflow-job-drift",
    "github-app-drift",
    "check-set-snapshot-drift",
    "failed-required-job",
    "skipped-required-job",
    "duplicate-required-job",
    "missing-linux-a01",
    "failed-linux-a01",
    "local-head-drift",
    "upstream-drift",
    "live-remote-drift",
    "dirty-source",
    "shallow-history",
    "rewritten-non-descendant",
    "same-tree-different-parents",
    "replace-object-present",
    "graft-present",
    "carrier-blob-drift",
    "migration-carrier-drift",
    "source-binding-drift",
    "wrong-vcs-action-receipt",
    "replayed-vcs-action-receipt",
    "duplicate-json-key",
    "receipt-path-escape",
    "receipt-publication-collision",
    "cas-predecessor-mismatch",
    "missing-linux-a01-artifact",
    "linux-a01-artifact-hash-drift",
    "linux-a01-artifact-wrong-run",
    "expired-linux-a01-artifact",
    "missing-deterministic-verdict",
    "deterministic-verdict-hash-drift",
    "deterministic-verdict-path-escape",
    "failed-deterministic-verdict",
    "deterministic-verdict-live-drift",
    "check-run-name-drift",
    "missing-nonclaims",
    "mutated-nonclaim",
    "extra-nonclaim",
    "wrong-provider",
    "extra-run-artifact",
    "upstream-ref-drift",
    "self-attested-task7-evidence",
    "noop-task7-role-command",
    "wrong-source-task7-evidence",
    "replayed-task7-evidence",
    "full-local-ci-timeout-command-drift",
    "forged-full-local-ci-pass-marker",
    "task7-execution-profile-drift",
    "task7-removed-environment-name-profile-drift",
}


def process_is_running(pid: int) -> bool:
    if os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = ctypes.c_void_p
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == 259
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def wait_for_process_exit(pid: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_is_running(pid):
            return True
        time.sleep(0.05)
    return not process_is_running(pid)


def stop_test_process(pid: int) -> None:
    if not process_is_running(pid):
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
    else:
        try:
            os.kill(pid, 9)
        except OSError:
            pass


def write_owned_process_tree(root: Path) -> tuple[list[str], Path, Path]:
    child_pid = root / "child.pid"
    grandchild_pid = root / "grandchild.pid"
    grandchild = root / "grandchild.py"
    grandchild.write_text(
        "import os, sys, time\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='ascii')\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    child = root / "child.py"
    child.write_text(
        "import os, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='ascii')\n"
        "subprocess.Popen([sys.executable, sys.argv[2], sys.argv[3]])\n"
        "deadline = time.monotonic() + 5\n"
        "while not Path(sys.argv[3]).exists() and time.monotonic() < deadline:\n"
        "    time.sleep(0.01)\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    return [sys.executable, str(child), str(child_pid), str(grandchild), str(grandchild_pid)], child_pid, grandchild_pid


class CiReadbackContract(unittest.TestCase):
    def require_checker(self) -> None:
        if not CHECKER.is_file():
            self.skipTest("implementation gate: tools/check_ci_readback.py is not materialized")

    def test_01_checker_owner_is_materialized(self) -> None:
        self.assertTrue(CHECKER.is_file(), "Task 3b checker owner must exist")

    def test_02_linux_evidence_writer_owner_is_materialized(self) -> None:
        self.assertTrue(LINUX_WRITER.is_file(), "Task 3b Linux A01 evidence writer must exist")

    def test_03_task7_deterministic_evidence_writer_owner_is_materialized(self) -> None:
        self.assertTrue(TASK7_WRITER.is_file(), "Task 3b Task 7 deterministic evidence writer must exist")

    def test_schema_is_the_sole_combined_receipt_owner(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validate_schema_definition(schema)
        self.assertEqual(schema["properties"]["schema"]["const"], "daee-source-commit-receipt-v1")
        owners = []
        for path in sorted((ROOT / "schema").glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            if value.get("properties", {}).get("schema", {}).get("const") == "daee-source-commit-receipt-v1":
                owners.append(path.name)
        self.assertEqual(owners, ["ci-readback.schema.json"])

    def test_combined_receipt_has_fixed_nonclaims(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        expected = [
            "does-not-claim-deterministic-whole-branch-closure",
            "does-not-claim-candidate-maturity",
            "does-not-authorize-or-execute-model-provider-use",
            "does-not-record-owner-acceptance",
        ]
        self.assertIn("non_claims", schema["required"])
        self.assertEqual(schema["properties"]["non_claims"]["const"], expected)

    def test_combined_receipt_binds_provider_complete_artifact_inventory_and_exact_upstream(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertIn("provider", schema["required"])
        self.assertEqual(schema["properties"]["provider"], {"const": "github-actions"})
        self.assertIn("artifact_inventory", schema["required"])
        self.assertEqual(
            schema["properties"]["source"]["properties"]["equality"]["properties"]["upstream_ref"],
            {"const": "refs/remotes/origin/codex/v0.4.6.0-runtime-footprint-b10"},
        )
        source = CHECKER.read_text(encoding="utf-8")
        self.assertIn("len(all_artifacts) != 1", source)

    def test_valid_fixture_and_same_stem_expectations_are_complete(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        receipt = json.loads(VALID.read_text(encoding="utf-8"))
        self.assertEqual(validate_schema_subset(receipt, schema), [])
        evidence_path = HERE / "support" / "linux-a01.json"
        evidence_raw = evidence_path.read_bytes()
        self.assertEqual(receipt["linux_a01"]["evidence"], json.loads(evidence_raw))
        self.assertEqual(receipt["linux_a01"]["artifact"]["entry_byte_count"], len(evidence_raw))
        self.assertEqual(receipt["linux_a01"]["artifact"]["entry_sha256"], hashlib.sha256(evidence_raw).hexdigest())
        self.assertEqual(receipt["artifact_inventory"], [receipt["linux_a01"]["artifact"]])
        for role, ref in receipt["deterministic_verdicts"].items():
            with self.subTest(deterministic_verdict=role):
                artifact_path = ROOT / ref["path"]
                artifact_raw = artifact_path.read_bytes()
                artifact = json.loads(artifact_raw)
                self.assertEqual(ref["byte_count"], len(artifact_raw))
                self.assertEqual(ref["sha256"], hashlib.sha256(artifact_raw).hexdigest())
                self.assertEqual(ref["artifact_schema"], artifact["schema"])
                self.assertEqual(ref["kind"], artifact["kind"])
                self.assertEqual(ref["status"], artifact["status"])
        expectation_schema = json.loads(EXPECTATION_SCHEMA.read_text(encoding="utf-8"))
        fixtures = sorted((HERE / "invalid").glob("*.json"))
        fixtures = [path for path in fixtures if not path.name.endswith(".expectation.json")]
        self.assertGreaterEqual(len(fixtures), 30)
        stems = {path.stem for path in fixtures}
        self.assertTrue(REQUIRED_NEGATIVES <= stems)
        for fixture in fixtures:
            with self.subTest(fixture=fixture.name):
                value = json.loads(fixture.read_text(encoding="utf-8"))
                self.assertEqual(value.get("fixture_schema"), "daee-checker-fixture-v1")
                self.assertEqual(value.get("base"), VALID.relative_to(ROOT).as_posix())
                expectation_path = fixture.with_name(f"{fixture.stem}.expectation.json")
                self.assertTrue(expectation_path.is_file())
                expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
                self.assertEqual(validate_schema_subset(expectation, expectation_schema), [])
                self.assertEqual(expectation["fixture"], fixture.name)
                self.assertEqual(expectation["expected_checker_id"], "ci-readback")
        expectation_stems = {
            path.name[: -len(".expectation.json")]
            for path in (HERE / "invalid").glob("*.expectation.json")
        }
        self.assertEqual(stems, expectation_stems)

    def test_checker_self_test_closes_every_right_reason_fixture(self) -> None:
        self.require_checker()
        completed = subprocess.run(
            [sys.executable, "-B", str(CHECKER), "--self-test"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("ci readback self-test: PASS", completed.stdout)
        self.assertIn("1 valid", completed.stdout)
        self.assertIn(f"{len(list((HERE / 'invalid').glob('*.expectation.json')))} invalid", completed.stdout)

    def test_task7_native_preflight_validator_binds_all_a16_gate_commands(self) -> None:
        builder = importlib.import_module("build_task7_fixtures")
        checker = importlib.import_module("check_ci_readback")
        writer = importlib.import_module("write_task7_deterministic_evidence")
        preflight = importlib.import_module("run_no_model_preflight")
        runner = importlib.import_module("run_local_ci")
        gates = []
        for gate in preflight.GATES:
            commands = list(preflight.A16_GATE_COMMANDS.get(gate.name, ()))
            if not commands:
                commands = [f"in-process: legacy gate {gate.number}"]
            gates.append(
                {
                    "number": gate.number,
                    "name": gate.name,
                    "passed": True,
                    "repair_lane": "",
                    "steps": [
                        {
                            "command": command,
                            "execution_profile": runner.execution_profile_for(command),
                            "returncode": 1 if gate.number == 16 else 0,
                            "duration_sec": 0.001,
                            "timed_out": False,
                            "stdout_tail": "",
                        }
                        for command in commands
                    ],
                }
            )
        flattened = [step["command"] for gate in gates for step in gate["steps"]]
        value = {
            "schema": "daee-no-model-preflight-report-v2",
            "decision": "MATRIX_AUTHORIZED_AFTER_PREFLIGHT",
            "complete": True,
            "gate_count": len(gates),
            "command_count": len(flattened),
            "command_set_sha256": runner.command_list_sha256(flattened),
            "execution_plan_sha256": runner.execution_plan_sha256(flattened),
            "python_execution_profile_id": runner.PYTHON_EXECUTION_PROFILE_ID,
            "gates": gates,
        }
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            path = temp_root / "native.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            writer._validate_no_model_native_report(path)

            receipt = json.loads(VALID.read_text(encoding="utf-8"))
            bundle_ref = receipt["deterministic_verdicts"]["no_model_preflight"]
            bundle = json.loads((ROOT / bundle_ref["path"]).read_text(encoding="utf-8"))
            report = json.loads((ROOT / bundle["report"]["path"]).read_text(encoding="utf-8"))
            command_log = json.loads((ROOT / bundle["log"]["path"]).read_text(encoding="utf-8"))
            freeze = json.loads((ROOT / bundle["source_freeze"]["path"]).read_text(encoding="utf-8"))

            def readback_finding(native: dict[str, object]) -> object:
                raw = (json.dumps(native, indent=2) + "\n").encode("utf-8")
                path.write_bytes(raw)
                candidate_report = copy.deepcopy(report)
                candidate_report["evidence_artifacts"] = [
                    {
                        "path": path.relative_to(temp_root).as_posix(),
                        "byte_count": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }
                ]
                candidate_report["report_id"] = checker._task7_report_id(candidate_report)
                return checker._task7_result_semantics(
                    "no_model_preflight",
                    checker.DETERMINISTIC_VERDICT_SPECS["no_model_preflight"],
                    bundle,
                    candidate_report,
                    command_log,
                    freeze,
                    root=temp_root,
                )

            self.assertIsNone(readback_finding(value), "canonical Gate 16 exit 1 must be accepted downstream")
            gate16_step = value["gates"][15]["steps"][0]
            for returncode in (0, 2):
                with self.subTest(gate16_returncode=returncode):
                    gate16_step["returncode"] = returncode
                    path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "failed/substituted step"):
                        writer._validate_no_model_native_report(path)
                    finding = readback_finding(value)
                    self.assertIsNotNone(finding)
                    self.assertEqual(
                        (finding.failure_class, finding.failure_subcode, finding.message),
                        (
                            "deterministic_verdicts",
                            "preflight-result",
                            "no-model preflight gate 16 is not proven PASS",
                        ),
                    )
            gate16_step["returncode"] = 1
            value["gates"][0]["steps"][0]["returncode"] = 1
            finding = readback_finding(value)
            self.assertIsNotNone(finding)
            self.assertEqual(
                (finding.failure_class, finding.failure_subcode, finding.message),
                ("deterministic_verdicts", "preflight-result", "no-model preflight gate 1 is not proven PASS"),
            )
            value["gates"][0]["steps"][0]["returncode"] = 0
            value["gates"][-1]["steps"][0]["command"] += " --drift"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "command drift"):
                writer._validate_no_model_native_report(path)

            built = builder.native_no_model_report()
            for gate in built["gates"]:
                expected_returncode = preflight.EXPECTED_GATE_RETURN_CODES.get(gate["number"], 0)
                for step in gate["steps"]:
                    self.assertEqual(step["returncode"], expected_returncode)

    def test_cli_surface_has_no_fixture_injection_or_external_shortcut(self) -> None:
        self.require_checker()
        completed = subprocess.run(
            [sys.executable, "-B", str(CHECKER), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for marker in (
            "--self-test",
            "--build",
            "--repository",
            "--remote",
            "--ref",
            "--sha",
            "--push-receipt",
            "--source-binding",
            "--out",
            "--receipt",
            "--require-status",
            "--verify-live",
        ):
            self.assertIn(marker, completed.stdout)
        for forbidden in ("--observation", "--fixture-observation", "--skip-live", "--force"):
            self.assertNotIn(forbidden, completed.stdout)

    def test_live_collector_queries_workflow_runs_by_exact_head_sha(self) -> None:
        self.require_checker()
        source = CHECKER.read_text(encoding="utf-8")
        self.assertIn('"head_sha": source_sha', source)

    def test_live_collector_separates_owner_context_from_raw_check_run_name(self) -> None:
        self.require_checker()
        source = CHECKER.read_text(encoding="utf-8")
        self.assertIn('row.get("name") == JOB_NAME', source)
        self.assertIn('"raw_check_run_name": check_api.get("name")', source)

    def test_vcs_authorization_scope_is_bound_to_receipt_repository(self) -> None:
        self.require_checker()
        checker = importlib.import_module("check_ci_readback")
        receipt = json.loads(VALID.read_text(encoding="utf-8"))
        authorization = json.loads((HERE / "support" / "push-authorization.json").read_text(encoding="utf-8"))
        authorization["repository"] = "other-owner/other-repository"
        finding = checker._authorization_scope(authorization, receipt["repository"], public_family=True)
        self.assertIsNotNone(finding)
        self.assertEqual((finding.failure_class, finding.failure_subcode), ("vcs_evidence", "authorization-scope"))
        authorization = json.loads((HERE / "support" / "push-authorization.json").read_text(encoding="utf-8"))
        authorization["target_ref"] = "refs/heads/other-branch"
        finding = checker._authorization_scope(authorization, receipt["repository"], public_family=True)
        self.assertIsNotNone(finding)
        self.assertEqual((finding.failure_class, finding.failure_subcode), ("vcs_evidence", "authorization-scope"))

    def test_legacy_commit_scope_is_quarantined_to_checkout_and_branch(self) -> None:
        self.require_checker()
        checker = importlib.import_module("check_ci_readback")
        receipt = json.loads(VALID.read_text(encoding="utf-8"))
        authorization = {
            "schema": "daee-vcs-durability-authorization-v1",
            "repository": str(ROOT.resolve()),
            "branch": receipt["repository"]["branch"],
        }
        finding = checker._authorization_scope(
            authorization,
            receipt["repository"],
            public_family=False,
            label="commit",
        )
        self.assertIsNone(finding)
        authorization["branch"] = "other-branch"
        finding = checker._authorization_scope(
            authorization,
            receipt["repository"],
            public_family=False,
            label="commit",
        )
        self.assertIsNotNone(finding)
        self.assertEqual((finding.failure_class, finding.failure_subcode), ("vcs_evidence", "authorization-scope"))

    def test_predecessor_receipt_source_must_be_a_strict_ancestor(self) -> None:
        self.require_checker()
        checker = importlib.import_module("check_ci_readback")
        current = "3" * 40
        same = checker._strict_predecessor_source(current, current, is_ancestor=lambda _old, _new: True)
        self.assertIsNotNone(same)
        self.assertEqual((same.failure_class, same.failure_subcode), ("receipt_custody", "predecessor-source-replay"))
        rewritten = checker._strict_predecessor_source("2" * 40, current, is_ancestor=lambda _old, _new: False)
        self.assertIsNotNone(rewritten)
        self.assertEqual(
            (rewritten.failure_class, rewritten.failure_subcode),
            ("receipt_custody", "predecessor-source-ancestry"),
        )
        accepted = checker._strict_predecessor_source("2" * 40, current, is_ancestor=lambda _old, _new: True)
        self.assertIsNone(accepted)

    def test_live_workflow_contract_rejects_writer_and_upload_substitution(self) -> None:
        self.require_checker()
        checker = importlib.import_module("check_ci_readback")
        raw = (ROOT / ".github" / "workflows" / "ci.yml").read_bytes()
        writer_drift = raw.replace(b"--runner-label ubuntu-latest", b"--runner-label windows-latest")
        with self.assertRaisesRegex(ValueError, "writer"):
            checker._workflow_contract(writer_drift)
        upload_drift = raw.replace(
            b"path: .ci-evidence/linux-a01.json",
            b"path: .ci-evidence/substituted.json",
        )
        with self.assertRaisesRegex(ValueError, "artifact"):
            checker._workflow_contract(upload_drift)

    def test_live_workflow_contract_rejects_continue_on_error(self) -> None:
        self.require_checker()
        checker = importlib.import_module("check_ci_readback")
        raw = (ROOT / ".github" / "workflows" / "ci.yml").read_bytes()
        job_drift = raw.replace(b"runs-on: ubuntu-latest", b"runs-on: ubuntu-latest\n    continue-on-error: true")
        with self.assertRaisesRegex(ValueError, "continue-on-error"):
            checker._workflow_contract(job_drift)
        step_drift = raw.replace(
            b"run: python tools/check_source_provenance.py --tracked-only",
            b"run: python tools/check_source_provenance.py --tracked-only\n        continue-on-error: true",
        )
        with self.assertRaisesRegex(ValueError, "continue-on-error"):
            checker._workflow_contract(step_drift)

    def test_branch_protection_app_binding_rejects_foreign_app(self) -> None:
        self.require_checker()
        checker = importlib.import_module("check_ci_readback")
        protection = {
            "protected": True,
            "checks": [{"context": "CI / runtime-checks", "app_id": 999}],
        }
        finding = checker._branch_protection_app(protection, {"id": 15368})
        self.assertIsNotNone(finding)
        self.assertEqual(
            (finding.failure_class, finding.failure_subcode),
            ("required_checks", "branch-protection-app"),
        )

    def test_linux_writer_gets_explicit_github_hosted_runner_environment(self) -> None:
        workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
        writer_step = next(
            step
            for step in workflow["jobs"]["runtime-checks"]["steps"]
            if step.get("name") == "Emit Linux A01 evidence"
        )
        self.assertIn('--runner-environment "${{ runner.environment }}"', writer_step["run"])
        writer_source = LINUX_WRITER.read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--runner-environment")', writer_source)
        self.assertIn("runner_environment=args.runner_environment", writer_source)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["$defs"]["linux_a01_evidence"]["properties"]["runner_environment"],
            {"const": "github-hosted"},
        )

    def test_support_linux_a01_job_log_parses_the_exact_bounded_full_ci_marker(self) -> None:
        checker = importlib.import_module("check_ci_readback")
        raw = (HERE / "support/linux-a01-job.log").read_bytes()
        segment, test_count, status, skipped = checker._a01_log(raw)
        marker = f"##[group]Run {checker.FULL_CI_COMMAND}".encode("utf-8")
        self.assertEqual(raw.count(marker), 1)
        self.assertNotIn(marker, segment)
        self.assertEqual((test_count, status, skipped), (23, "OK", 0))

    def test_linux_writer_rejects_working_checker_bytes_that_differ_from_source_blob(self) -> None:
        writer = importlib.import_module("write_linux_a01_evidence")
        with tempfile.TemporaryDirectory(prefix="daee-linux-writer-working-bytes-") as temporary:
            root = Path(temporary)
            checker_path = root / "tools" / "checker.py"
            checker_path.parent.mkdir(parents=True)
            checker_path.write_bytes(b"mutated working bytes\n")
            with mock.patch.object(writer, "ROOT", root), mock.patch.object(
                writer,
                "_git",
                side_effect=["a" * 40, "blob", b"exact source bytes\n"],
            ):
                with self.assertRaisesRegex(ValueError, "working bytes"):
                    writer._source_file_identity("3" * 40, "tools/checker.py")
        writer_source = LINUX_WRITER.read_text(encoding="utf-8")
        before = writer_source.index("checker_identity = _source_file_identity")
        execution = writer_source.index("completed = subprocess.run", before)
        after = writer_source.index("post_checker_identity = _source_file_identity", execution)
        self.assertLess(before, execution)
        self.assertLess(execution, after)

    def test_linux_evidence_writer_self_test_is_offline_and_create_once(self) -> None:
        if not LINUX_WRITER.is_file():
            self.skipTest("implementation gate: Linux A01 evidence writer is not materialized")
        completed = subprocess.run(
            [sys.executable, "-B", str(LINUX_WRITER), "--self-test"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("linux A01 evidence writer self-test: PASS", completed.stdout)

    def test_task7_evidence_writer_self_test_is_offline_and_create_once(self) -> None:
        self.assertTrue(TASK7_WRITER.is_file(), "Task 7 evidence writer owner must exist")
        completed = subprocess.run(
            [sys.executable, "-B", str(TASK7_WRITER), "--self-test"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Task 7 deterministic evidence writer self-test: PASS", completed.stdout)
        self.assertIn("hash-object/path/output fail-closed rejection", completed.stdout)
        help_result = subprocess.run(
            [sys.executable, "-B", str(TASK7_WRITER), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        for forbidden in ("--command-json", "--report", "--log", "--checker"):
            self.assertNotIn(forbidden, help_result.stdout)

    def test_task7_writer_requires_frozen_checker_as_python_entrypoint(self) -> None:
        writer = importlib.import_module("write_task7_deterministic_evidence")
        with self.assertRaisesRegex(ValueError, "exact source-bound producer"):
            writer.validate_role_command(
                ["python", "tests/ci-readback/support/task7-verdict-checker.py"],
                "no-model-preflight",
                "tests/ci-readback/support/task7-verdict-checker.py",
            )
        writer.validate_role_command(
            writer.producer_command("no-model-preflight"),
            "no-model-preflight",
            writer.PRODUCER_PATH,
        )

    def test_task7_tree_parser_accepts_git_padded_blob_sizes(self) -> None:
        writer = importlib.import_module("write_task7_deterministic_evidence")
        oid = "a" * 40
        object_type, parsed_oid, size, path = writer.parse_tree_record(
            f"100644 blob {oid}     166\t.gitattributes".encode("utf-8")
        )
        self.assertEqual((object_type, parsed_oid, size, path), ("blob", oid, 166, ".gitattributes"))

    def test_task7_complete_source_freeze_accepts_real_zero_byte_blobs(self) -> None:
        writer = importlib.import_module("write_task7_deterministic_evidence")
        tree_oid = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        files = writer._tree_files(tree_oid)
        empty_paths = {row["path"] for row in files if row["byte_count"] == 0}
        self.assertIn("docs/.nojekyll", empty_paths)
        self.assertIn("tests/cold-law-fixtures/invalid/unexpected-advisory/ci_commands.txt", empty_paths)
        freeze = writer.build_source_freeze(tree_oid, files)
        self.assertEqual(freeze["file_count"], len(files))

    def test_task7_noop_checker_and_bare_report_cohort_is_rejected(self) -> None:
        self.require_checker()
        checker = importlib.import_module("check_ci_readback")
        receipt = json.loads(VALID.read_text(encoding="utf-8"))
        ref = receipt["deterministic_verdicts"]["no_model_preflight"]
        bundle = json.loads((ROOT / ref["path"]).read_text(encoding="utf-8"))
        bundle["checker"] = {
            "path": "tests/ci-readback/support/task7-verdict-checker.py",
            "blob_oid": "a" * 40,
            "raw_sha256": "b" * 64,
        }
        bundle["command"] = ["python", "tests/ci-readback/support/task7-verdict-checker.py"]
        finding = checker._validate_task7_bundle(
            "no_model_preflight",
            checker.DETERMINISTIC_VERDICT_SPECS["no_model_preflight"],
            bundle,
            root=ROOT,
            source_tree_oid=receipt["source"]["tree_oid"],
        )
        self.assertIsNotNone(finding)
        self.assertEqual(finding.failure_subcode, "role-command")
        bare = {
            "schema": "daee-task7-result-report-v1",
            "kind": "no-model-preflight",
            "status": "PASS",
            "terminal_claim": False,
        }
        report_finding = checker._task7_schema_finding(
            bare, "task7_result_report", "no_model_preflight"
        )
        self.assertIsNotNone(report_finding)

    def test_task7_same_owner_identity_alias_is_rejected(self) -> None:
        writer = importlib.import_module("write_task7_deterministic_evidence")
        checker = importlib.import_module("check_ci_readback")
        freeze = json.loads((HERE / "support/task7-source-freeze.json").read_text(encoding="utf-8"))
        review = json.loads(
            (HERE / "support/task7-independent-whole-branch-review-record.json").read_text(encoding="utf-8")
        )
        authorization_path = HERE / "support/task7-independent-review-authorization.json"
        authorization_raw = authorization_path.read_bytes()
        authorization = json.loads(authorization_raw)
        authorization_ref = {
            "path": authorization_path.relative_to(ROOT).as_posix(),
            "byte_count": len(authorization_raw),
            "sha256": hashlib.sha256(authorization_raw).hexdigest(),
        }
        review["owner_identity"] = review["reviewer"] + " "
        review["review_id"] = writer._review_id(review)
        with self.assertRaisesRegex(ValueError, "canonical|differ"):
            writer.validate_whole_branch_review(review, freeze, authorization, authorization_ref)
        finding = checker._task7_schema_finding(
            review, "task7_whole_branch_review", "independent_whole_branch_review"
        )
        self.assertIsNotNone(finding)
        forged_authorization = json.loads(json.dumps(authorization))
        forged_authorization["reviewer_identity"] = writer.IMPLEMENTATION_OWNER_IDENTITY
        forged_authorization["authorization_id"] = writer._review_authorization_id(forged_authorization)
        forged_ref = {
            "path": "tests/ci-readback/support/forged-review-authorization.json",
            "byte_count": 1,
            "sha256": "f" * 64,
        }
        forged_review = json.loads(
            (HERE / "support/task7-independent-whole-branch-review-record.json").read_text(encoding="utf-8")
        )
        forged_review["reviewer"] = writer.IMPLEMENTATION_OWNER_IDENTITY
        forged_review["owner_identity"] = writer.IMPLEMENTATION_OWNER_IDENTITY
        forged_review["review_authorization_id"] = forged_authorization["authorization_id"]
        forged_review["review_authorization"] = forged_ref
        forged_review["review_id"] = writer._review_id(forged_review)
        with self.assertRaisesRegex(ValueError, "distinct|differ"):
            writer.validate_whole_branch_review(
                forged_review, freeze, forged_authorization, forged_ref
            )

    def test_task7_actual_owner_cannot_relabel_itself_as_reviewer(self) -> None:
        writer = importlib.import_module("write_task7_deterministic_evidence")
        checker = importlib.import_module("check_ci_readback")
        freeze = json.loads((HERE / "support/task7-source-freeze.json").read_text(encoding="utf-8"))
        review = json.loads(
            (HERE / "support/task7-independent-whole-branch-review-record.json").read_text(encoding="utf-8")
        )
        authorization_path = HERE / "support/task7-independent-review-authorization.json"
        authorization_raw = authorization_path.read_bytes()
        authorization = json.loads(authorization_raw)
        authorization_ref = {
            "path": authorization_path.relative_to(ROOT).as_posix(),
            "byte_count": len(authorization_raw),
            "sha256": hashlib.sha256(authorization_raw).hexdigest(),
        }
        review["reviewer"] = "/root/task3b_ci_receipt"
        review["owner_identity"] = "/root/not_the_task3b_owner"
        review["review_id"] = writer._review_id(review)
        with self.assertRaisesRegex(ValueError, "owner|authorization"):
            writer.validate_whole_branch_review(review, freeze, authorization, authorization_ref)
        finding = checker._task7_schema_finding(
            review, "task7_whole_branch_review", "independent_whole_branch_review"
        )
        self.assertIsNotNone(finding)

    def test_task7_python_checks_use_the_running_interpreter_not_path_lookup(self) -> None:
        writer = importlib.import_module("write_task7_deterministic_evidence")
        completed = writer.OwnedCommandResult(
            args=[], returncode=0, stdout=b"role completed\n", stderr=b"", timed_out=False
        )
        with mock.patch.object(writer, "run_owned_command", return_value=completed) as run:
            writer._run_role_checks("full-local-ci")
        argv = run.call_args.args[0]
        self.assertEqual(
            argv,
            [
                sys.executable,
                "-I",
                "-S",
                "-B",
                str(TOOLS / "sanitized_python_bootstrap.py"),
                "--script",
                "tools/run_local_ci.py",
                "--strict-pwsh",
                "--command-timeout-seconds",
                "900",
                "--json",
                writer.FULL_LOCAL_CI_NATIVE_REPORT_REL.as_posix(),
            ],
        )
        child_env = run.call_args.kwargs["env"]
        self.assertFalse(any(key.upper().startswith("PYTHON") for key in child_env), child_env)

    def test_task7_role_python_profile_blocks_inherited_sitecustomize_pass_forgery(self) -> None:
        writer = importlib.import_module("write_task7_deterministic_evidence")
        with tempfile.TemporaryDirectory(prefix="daee-task7-python-env-") as temporary:
            root = Path(temporary)
            sentinel = root / "sitecustomize-ran"
            (root / "sitecustomize.py").write_text(
                "import os\n"
                "from pathlib import Path\n"
                f"Path({str(sentinel)!r}).write_text('injected', encoding='ascii')\n"
                "os.write(1, b'run_local_ci: PASS (172 command(s), indices 1-172)\\n')\n"
                "os._exit(0)\n",
                encoding="utf-8",
            )
            probe = root / "probe.py"
            probe.write_text("print('REAL_ROLE_EXECUTED')\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"PYTHONPATH": str(root), "PYTHONSTARTUP": str(root / "sitecustomize.py")}):
                with mock.patch.dict(writer.ROLE_CHECKS, {"full-local-ci": [["python", str(probe)]]}):
                    results = writer._run_role_checks("full-local-ci")
            self.assertFalse(sentinel.exists(), "inherited sitecustomize executed before the Task 7 role")
            self.assertEqual(results[0][1], b"REAL_ROLE_EXECUTED\r\n" if os.name == "nt" else b"REAL_ROLE_EXECUTED\n")

    def test_workflow_bootstrap_removes_and_records_setup_python_environment_names(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-setup-python-env-") as temporary:
            root = Path(temporary)
            sentinel = root / "sitecustomize-ran"
            (root / "sitecustomize.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(sentinel)!r}).write_text('injected', encoding='ascii')\n",
                encoding="utf-8",
            )
            probe = root / "safe_profile_probe.py"
            probe.write_text(
                "import json, os, sys, yaml\n"
                "from run_local_ci import execution_profile_for\n"
                "assert 'sitecustomize' not in sys.modules\n"
                "assert 'usercustomize' not in sys.modules\n"
                "assert not any(k.upper().startswith('PYTHON') or k.upper() == '__PYVENV_LAUNCHER__' for k in os.environ)\n"
                "print(json.dumps(execution_profile_for('python tools/probe.py'), sort_keys=True))\n",
                encoding="utf-8",
            )
            removed_names = [
                "pythonLocation",
                "Python_ROOT_DIR",
                "Python2_ROOT_DIR",
                "Python3_ROOT_DIR",
                "pYtHoNSecret",
                "__pyvenv_launcher__",
                "PYTHONPATH",
            ]
            child_env = dict(os.environ)
            child_env.update({name: f"secret-value-{index}" for index, name in enumerate(removed_names)})
            child_env["PYTHONPATH"] = str(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-B",
                    str(TOOLS / "sanitized_python_bootstrap.py"),
                    "--script",
                    str(probe),
                ],
                cwd=ROOT,
                env=child_env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse(sentinel.exists())
            profile = json.loads(completed.stdout)
            expected_process_names = [
                name.upper() if os.name == "nt" else name
                for name in removed_names
                if not (os.name == "nt" and name.upper() == "__PYVENV_LAUNCHER__")
            ]
            self.assertEqual(
                profile["removed_environment_names"],
                sorted(expected_process_names, key=lambda name: (name.upper(), name)),
            )
            for value in child_env.values():
                if isinstance(value, str) and value.startswith("secret-value-"):
                    self.assertNotIn(value, completed.stdout + completed.stderr)

    def test_bootstrap_places_stdlib_before_package_roots_without_processing_pth(self) -> None:
        bootstrap = importlib.import_module("sanitized_python_bootstrap")
        actual = bootstrap.sysconfig.get_paths()
        with tempfile.TemporaryDirectory(prefix="daee-bootstrap-root-order-") as temporary:
            root = Path(temporary)
            script_parent = root / "script-parent"
            system_purelib = root / "system-purelib"
            system_platlib = root / "system-platlib"
            user_purelib = root / "user-purelib"
            user_platlib = root / "user-platlib"
            for path in (script_parent, system_purelib, system_platlib, user_purelib, user_platlib):
                path.mkdir()
            shadow = user_purelib / "fractions.py"
            shadow.write_text("SHADOWED_STDLIB = True\n", encoding="utf-8")
            pth_sentinel = root / "pth-processed"
            (user_purelib / "attacker.pth").write_text(
                f"import pathlib; pathlib.Path({str(pth_sentinel)!r}).write_text('processed')\n",
                encoding="utf-8",
            )
            configured_paths = {
                "stdlib": actual["stdlib"],
                "platstdlib": actual["platstdlib"],
                "purelib": str(system_purelib),
                "platlib": str(system_platlib),
            }
            user_paths = {"purelib": str(user_purelib), "platlib": str(user_platlib)}
            inherited = [*sys.path, str(user_purelib), actual["stdlib"]]
            previous_fractions = sys.modules.pop("fractions", None)
            try:
                with mock.patch.object(bootstrap.sysconfig, "get_paths", return_value=configured_paths), mock.patch.object(
                    bootstrap.sysconfig,
                    "get_scheme_names",
                    return_value=("nt_user" if os.name == "nt" else "posix_user",),
                ), mock.patch.object(
                    bootstrap.sysconfig,
                    "get_path",
                    side_effect=lambda name, *, scheme: user_paths[name],
                ), mock.patch.object(sys, "path", inherited):
                    bootstrap._install_import_roots(script_parent)
                    first = list(sys.path)
                    bootstrap._install_import_roots(script_parent)
                    self.assertEqual(sys.path, first)
                    self.assertEqual(
                        first[:3],
                        [str(bootstrap.ROOT.resolve()), str(bootstrap.TOOLS.resolve()), str(script_parent.resolve())],
                    )
                    stdlib_roots = list(dict.fromkeys(
                        [str(Path(actual[name]).resolve()) for name in ("stdlib", "platstdlib")]
                    ))
                    package_roots = [
                        str(system_purelib.resolve()),
                        str(system_platlib.resolve()),
                        str(user_purelib.resolve()),
                        str(user_platlib.resolve()),
                    ]
                    self.assertTrue(
                        all(first.index(stdlib) < first.index(package) for stdlib in stdlib_roots for package in package_roots),
                        first,
                    )
                    self.assertEqual(len(first), len({os.path.normcase(path) for path in first}))
                    self.assertFalse(pth_sentinel.exists())
                    importlib.invalidate_caches()
                    fractions = importlib.import_module("fractions")
                    self.assertFalse(hasattr(fractions, "SHADOWED_STDLIB"))
                    self.assertNotEqual(Path(fractions.__file__).resolve(), shadow.resolve())
                    self.assertTrue(
                        any(Path(fractions.__file__).resolve().is_relative_to(Path(path)) for path in stdlib_roots)
                    )
            finally:
                sys.modules.pop("fractions", None)
                if previous_fractions is not None:
                    sys.modules["fractions"] = previous_fractions

    def test_bootstrap_fails_closed_on_invalid_system_or_user_sysconfig_paths(self) -> None:
        bootstrap = importlib.import_module("sanitized_python_bootstrap")
        actual = bootstrap.sysconfig.get_paths()
        valid = {
            "stdlib": actual["stdlib"],
            "platstdlib": actual["platstdlib"],
            "purelib": actual["purelib"],
            "platlib": actual["platlib"],
        }
        user_scheme = "nt_user" if os.name == "nt" else "posix_user"
        cases = {
            "missing-system-stdlib": ({**valid, "stdlib": None}, lambda name, *, scheme: actual[name]),
            "relative-user-purelib": (valid, lambda name, *, scheme: "relative/user" if name == "purelib" else actual[name]),
        }
        for name, (system_paths, user_path) in cases.items():
            with self.subTest(name=name), mock.patch.object(
                bootstrap.sysconfig, "get_paths", return_value=system_paths
            ), mock.patch.object(
                bootstrap.sysconfig, "get_scheme_names", return_value=(user_scheme,)
            ), mock.patch.object(
                bootstrap.sysconfig, "get_path", side_effect=user_path
            ), self.assertRaisesRegex(SystemExit, "invalid sysconfig"):
                bootstrap._install_import_roots(None)

    def test_bootstrap_deletion_is_case_insensitive_and_includes_pyvenv_launcher(self) -> None:
        bootstrap = importlib.import_module("sanitized_python_bootstrap")
        inherited = {
            "KEEP_ME": "retained",
            "pYtHoN_custom": "never-record-this-value",
            "__pyvenv_launcher__": "never-record-this-value-either",
        }
        with mock.patch.dict(os.environ, inherited, clear=True):
            removed = bootstrap._remove_inherited_python_environment()
            expected = ["PYTHON_CUSTOM", "__PYVENV_LAUNCHER__"] if os.name == "nt" else [
                "pYtHoN_custom",
                "__pyvenv_launcher__",
            ]
            self.assertEqual(removed, expected)
            self.assertEqual(dict(os.environ), {"KEEP_ME": "retained"})

    def test_local_ci_python_children_use_exact_profile_and_emit_bound_completion(self) -> None:
        runner = importlib.import_module("run_local_ci")
        completed = runner.OwnedCommandResult(args=[], returncode=0, stdout=None, stderr=None, timed_out=False)
        inherited = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": "attacker",
            "PYTHONHOME": "attacker",
            "__PYVENV_LAUNCHER__": "attacker",
        }
        output = io.StringIO()
        with mock.patch.object(runner, "COMMANDS", ["python -B tools/probe.py", "git status"]), mock.patch.object(
            runner, "run_owned_command", return_value=completed
        ) as run, mock.patch.dict(os.environ, inherited, clear=True), mock.patch.object(
            sys, "argv", ["run_local_ci.py", "--strict-pwsh", "--command-timeout-seconds", "9"]
        ), contextlib.redirect_stdout(output):
            self.assertEqual(runner.main(), 0)
        python_call, native_call = run.call_args_list
        self.assertEqual(
            python_call.args[0],
            [
                sys.executable,
                "-I",
                "-S",
                "-B",
                str(TOOLS / "sanitized_python_bootstrap.py"),
                "--script",
                "tools/probe.py",
            ],
        )
        self.assertFalse(any(key.upper().startswith("PYTHON") for key in python_call.kwargs["env"]))
        self.assertNotIn("__PYVENV_LAUNCHER__", python_call.kwargs["env"])
        self.assertEqual(native_call.args[0], ["git", "status"])
        with mock.patch.object(runner, "COMMANDS", ["python -B tools/probe.py", "git status"]):
            completion = runner.parse_completion_stdout(output.getvalue().encode("utf-8"))
        self.assertEqual(completion["command_count"], 2)
        self.assertEqual(completion["executed_count"], 2)
        self.assertEqual(completion["start_at_command"], 1)
        self.assertEqual(completion["end_at_command"], 2)
        self.assertTrue(completion["strict_pwsh"])
        self.assertEqual(completion["command_timeout_seconds"], 9)
        with self.assertRaises(ValueError):
            runner.parse_completion_stdout(b"run_local_ci: PASS (2 command(s), indices 1-2)\n")

    def test_local_ci_suffix_cli_reports_partial_to_stdout_and_json(self) -> None:
        runner = importlib.import_module("run_local_ci")
        completed = runner.OwnedCommandResult(args=[], returncode=0, stdout=None, stderr=None, timed_out=False)
        commands = ["first", "second", "third"]
        for start_at, expected_executed in ((2, 2), (3, 1)):
            with self.subTest(start_at=start_at), tempfile.TemporaryDirectory(
                prefix="daee-local-ci-partial-"
            ) as temporary:
                report_path = Path(temporary) / "completion.json"
                output = io.StringIO()
                with mock.patch.object(runner, "COMMANDS", commands), mock.patch.object(
                    runner, "argv_for", side_effect=lambda command: [command]
                ), mock.patch.object(
                    runner, "run_owned_command", return_value=completed
                ) as run, mock.patch.object(
                    sys,
                    "argv",
                    [
                        "run_local_ci.py",
                        "--start-at-command",
                        str(start_at),
                        "--json",
                        str(report_path),
                    ],
                ), contextlib.redirect_stdout(output):
                    self.assertEqual(runner.main(), 0)
                with mock.patch.object(runner, "COMMANDS", commands):
                    stdout_value = runner.parse_completion_stdout(output.getvalue().encode("utf-8"))
                json_value = json.loads(report_path.read_text(encoding="utf-8"))
                self.assertEqual(stdout_value, json_value)
                self.assertEqual(stdout_value["status"], "PARTIAL")
                self.assertIs(stdout_value["complete"], False)
                self.assertEqual(stdout_value["start_at_command"], start_at)
                self.assertEqual(stdout_value["end_at_command"], len(commands))
                self.assertEqual(stdout_value["executed_count"], expected_executed)
                self.assertEqual(run.call_count, expected_executed)

    def test_local_ci_completion_parser_rejects_forged_prefix_coverage(self) -> None:
        runner = importlib.import_module("run_local_ci")
        commands = ["first", "second", "third"]
        cases = {
            "suffix-claims-pass": {
                "status": "PASS",
                "complete": True,
                "start_at_command": 2,
                "executed_count": 2,
            },
            "full-run-claims-partial": {
                "status": "PARTIAL",
                "complete": False,
                "start_at_command": 1,
                "executed_count": 3,
            },
            "suffix-forges-skipped-prefix": {
                "status": "PARTIAL",
                "complete": False,
                "start_at_command": 2,
                "executed_count": 3,
            },
        }
        with mock.patch.object(runner, "COMMANDS", commands):
            for name, replacements in cases.items():
                with self.subTest(name=name):
                    forged = runner.build_completion(
                        start_at_command=1,
                        strict_pwsh=True,
                        command_timeout_seconds=9,
                        commands=commands,
                    )
                    forged.update(replacements)
                    forged["completion_id"] = runner._completion_id(forged)
                    with self.assertRaises(ValueError):
                        runner.parse_completion_stdout(runner.completion_stdout(forged))

    def test_local_ci_full_completion_remains_complete_pass(self) -> None:
        runner = importlib.import_module("run_local_ci")
        commands = ["first", "second", "third"]
        with mock.patch.object(runner, "COMMANDS", commands):
            value = runner.build_completion(
                start_at_command=1,
                strict_pwsh=True,
                command_timeout_seconds=9,
                commands=commands,
            )
            parsed = runner.parse_completion_stdout(runner.completion_stdout(value))
        self.assertEqual(parsed["status"], "PASS")
        self.assertIs(parsed["complete"], True)
        self.assertEqual(parsed["executed_count"], len(commands))
        self.assertEqual(parsed["start_at_command"], 1)
        self.assertEqual(parsed["end_at_command"], len(commands))

    def test_local_ci_schema_and_parser_enforce_exact_full_and_suffix_shapes(self) -> None:
        runner = importlib.import_module("run_local_ci")
        writer = importlib.import_module("write_task7_deterministic_evidence")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        completion_schema = {
            "$schema": schema["$schema"],
            "$ref": "#/$defs/run_local_ci_completion",
            "$defs": schema["$defs"],
        }

        full = runner.build_completion(
            start_at_command=1,
            strict_pwsh=True,
            command_timeout_seconds=900,
        )
        suffixes = [
            runner.build_completion(
                start_at_command=start_at,
                strict_pwsh=True,
                command_timeout_seconds=900,
            )
            for start_at in (2, len(runner.COMMANDS))
        ]
        self.assertEqual(validate_schema_subset(full, completion_schema), [])
        self.assertEqual(full["skip_count"], 0)
        for partial in suffixes:
            with self.subTest(valid_start=partial["start_at_command"]):
                self.assertEqual(partial["status"], "PARTIAL")
                self.assertIs(partial["complete"], False)
                self.assertEqual(partial["end_at_command"], partial["command_count"])
                self.assertEqual(partial["skip_count"], partial["start_at_command"] - 1)
                self.assertEqual(
                    partial["executed_count"],
                    partial["command_count"] - partial["start_at_command"] + 1,
                )
                self.assertEqual(validate_schema_subset(partial, completion_schema), [])
                self.assertEqual(
                    runner.parse_completion_stdout(runner.completion_stdout(partial)),
                    partial,
                )

        partial = suffixes[0]
        mutations = {
            "pass-suffix": {"status": "PASS", "complete": True},
            "partial-full": {"status": "PARTIAL", "complete": False, "start_at_command": 1},
            "executed-count-drift": {"executed_count": partial["executed_count"] + 1},
            "skip-count-drift": {"skip_count": partial["skip_count"] + 1},
            "end-drift": {"end_at_command": partial["end_at_command"] - 1},
            "command-count-drift": {"command_count": partial["command_count"] - 1},
            "command-list-identity-drift": {"command_list_sha256": "0" * 64},
            "execution-plan-identity-drift": {"execution_plan_sha256": "0" * 64},
        }
        for name, replacements in mutations.items():
            with self.subTest(invalid=name):
                forged = dict(partial)
                if name == "partial-full":
                    forged = dict(full)
                forged.update(replacements)
                forged["completion_id"] = runner._completion_id(forged)
                self.assertNotEqual(validate_schema_subset(forged, completion_schema), [])
                with self.assertRaises(ValueError):
                    runner.parse_completion_stdout(runner.completion_stdout(forged))

        with self.assertRaisesRegex(ValueError, "execution boundary drifted"):
            writer._command_result(
                1,
                writer.ROLE_CHECKS["full-local-ci"][0],
                runner.completion_stdout(partial),
                b"",
            )

    def test_sanitized_python_profile_rejects_dynamic_code_and_stdin_forms(self) -> None:
        runner = importlib.import_module("run_local_ci")
        for command in (["python", "-c", "print('x')"], ["python", "-"], ["python", "-m", "unknown_dynamic"]):
            with self.subTest(command=command), self.assertRaises(ValueError):
                runner.execution_argv_for(command)

    def test_windows_timeout_teardown_failures_are_structured_infrastructure_results(self) -> None:
        runner = importlib.import_module("run_local_ci")

        class FakeProcess:
            pid = 43120

            def __init__(self, *, wait_timeout: bool = False) -> None:
                self.returncode = None
                self.wait_timeout = wait_timeout
                self.communicate_calls = 0
                self.kill_calls = 0

            def communicate(self, timeout: float | None = None) -> tuple[bytes, bytes]:
                self.communicate_calls += 1
                if self.communicate_calls == 1:
                    raise subprocess.TimeoutExpired(["owned"], timeout, output=b"partial", stderr=b"")
                return b"complete", b""

            def poll(self) -> int | None:
                return self.returncode

            def kill(self) -> None:
                self.kill_calls += 1
                self.returncode = -9

            def wait(self, timeout: float | None = None) -> int:
                if self.wait_timeout:
                    self.wait_timeout = False
                    raise subprocess.TimeoutExpired(["owned"], timeout)
                if self.returncode is None:
                    self.returncode = 0
                return self.returncode

        cases = {
            "taskkill-nonzero": {
                "taskkill": subprocess.CompletedProcess(["taskkill"], 1, b"", b"denied"),
                "wait_timeout": False,
                "parent_maps": [{43121: 43120}, {}],
                "running": False,
                "marker": "taskkill-returncode",
            },
            "taskkill-spawn-failure": {
                "taskkill": FileNotFoundError("taskkill unavailable"),
                "wait_timeout": False,
                "parent_maps": [{43121: 43120}, {}],
                "running": False,
                "marker": "taskkill-spawn",
            },
            "taskkill-timeout": {
                "taskkill": subprocess.TimeoutExpired(["taskkill"], 0),
                "wait_timeout": False,
                "parent_maps": [{43121: 43120}, {}],
                "running": False,
                "marker": "taskkill-timeout",
            },
            "root-wait-timeout": {
                "taskkill": subprocess.CompletedProcess(["taskkill"], 0, b"", b""),
                "wait_timeout": True,
                "parent_maps": [{43121: 43120}, {}],
                "running": False,
                "marker": "root-wait-timeout",
            },
            "surviving-descendant": {
                "taskkill": subprocess.CompletedProcess(["taskkill"], 0, b"", b""),
                "wait_timeout": False,
                "parent_maps": [{43121: 43120}, {43121: 43120}],
                "running": lambda pid: pid == 43121,
                "marker": "surviving-pids",
            },
        }
        for name, case in cases.items():
            with self.subTest(name=name):
                process = FakeProcess(wait_timeout=case["wait_timeout"])
                taskkill = case["taskkill"]
                run_patch = (
                    mock.patch.object(runner.subprocess, "run", side_effect=taskkill)
                    if isinstance(taskkill, BaseException)
                    else mock.patch.object(runner.subprocess, "run", return_value=taskkill)
                )
                with mock.patch.object(runner.os, "name", "nt"), mock.patch.object(
                    runner.subprocess,
                    "CREATE_NEW_PROCESS_GROUP",
                    0x00000200,
                    create=True,
                ), mock.patch.object(
                    runner.subprocess, "Popen", return_value=process
                ) as popen, run_patch, mock.patch.object(
                    runner,
                    "_windows_process_parent_map",
                    side_effect=case["parent_maps"],
                    create=True,
                ), mock.patch.object(
                    runner,
                    "_windows_pid_is_running",
                    side_effect=case["running"] if callable(case["running"]) else None,
                    return_value=case["running"] if not callable(case["running"]) else mock.DEFAULT,
                    create=True,
                ), mock.patch.object(runner, "PROCESS_TREE_TERMINATION_GRACE_SECONDS", 0.0):
                    result = runner.run_owned_command(["owned"], timeout_seconds=1)
                self.assertEqual(popen.call_args.kwargs.get("creationflags"), 0x00000200)
                self.assertNotIn("start_new_session", popen.call_args.kwargs)
                self.assertEqual(result.returncode, 125)
                self.assertTrue(result.timed_out)
                self.assertTrue(result.teardown_failed)
                self.assertEqual(result.failure_kind, "PROCESS_TREE_TEARDOWN")
                self.assertIn(case["marker"], (result.stderr or b"").decode("utf-8"))

    def test_local_ci_cli_preserves_distinct_teardown_failure(self) -> None:
        runner = importlib.import_module("run_local_ci")
        result = runner.OwnedCommandResult(
            args=["owned"],
            returncode=125,
            stdout=b"",
            stderr=b"PROCESS_TREE_TEARDOWN taskkill-timeout",
            timed_out=True,
            teardown_failed=True,
            failure_kind="PROCESS_TREE_TEARDOWN",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(runner, "COMMANDS", ["owned"]), mock.patch.object(
            runner, "argv_for", return_value=["owned"]
        ), mock.patch.object(
            runner, "run_owned_command", return_value=result
        ), mock.patch.object(
            sys, "argv", ["run_local_ci.py", "--command-timeout-seconds", "1"]
        ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(runner.main(), 125)
        self.assertIn("PROCESS_TREE_TEARDOWN", stderr.getvalue())
        self.assertNotIn("FAILED (124)", stderr.getvalue())

    def test_local_ci_timeout_kills_owned_child_tree_and_never_runs_next_command(self) -> None:
        runner = importlib.import_module("run_local_ci")
        with tempfile.TemporaryDirectory(prefix="daee-local-ci-timeout-") as temporary:
            root = Path(temporary)
            first_argv, child_pid_path, grandchild_pid_path = write_owned_process_tree(root)
            next_marker = root / "next-command-ran"
            next_argv = [
                sys.executable,
                "-c",
                f"from pathlib import Path; Path({str(next_marker)!r}).write_text('ran', encoding='ascii')",
            ]
            pids: list[int] = []
            try:
                with mock.patch.object(runner, "COMMANDS", ["owned-tree", "later-command"]), mock.patch.object(
                    runner,
                    "argv_for",
                    side_effect=lambda command: first_argv if command == "owned-tree" else next_argv,
                ), mock.patch.object(
                    sys,
                    "argv",
                    ["run_local_ci.py", "--command-timeout-seconds", "1"],
                ):
                    exit_code = runner.main()
                self.assertEqual(exit_code, 124)
                self.assertTrue(child_pid_path.is_file())
                self.assertTrue(grandchild_pid_path.is_file())
                pids = [int(child_pid_path.read_text()), int(grandchild_pid_path.read_text())]
                self.assertTrue(all(wait_for_process_exit(pid) for pid in pids), pids)
                self.assertFalse(next_marker.exists())
            finally:
                for path in (child_pid_path, grandchild_pid_path):
                    if path.is_file():
                        stop_test_process(int(path.read_text()))

    def test_task7_outer_timeout_kills_owned_child_tree_and_propagates_124(self) -> None:
        writer = importlib.import_module("write_task7_deterministic_evidence")
        with tempfile.TemporaryDirectory(prefix="daee-task7-timeout-") as temporary:
            root = Path(temporary)
            argv, child_pid_path, grandchild_pid_path = write_owned_process_tree(root)
            logical = ["python", *argv[1:]]
            try:
                with mock.patch.dict(writer.ROLE_CHECKS, {"full-local-ci": [logical]}):
                    with self.assertRaises(writer.Task7RoleTimeout) as raised:
                        writer._run_role_checks("full-local-ci", timeout_seconds=1)
                self.assertEqual(raised.exception.returncode, 124)
                self.assertIn("timeout", str(raised.exception).lower())
                pids = [int(child_pid_path.read_text()), int(grandchild_pid_path.read_text())]
                self.assertTrue(all(wait_for_process_exit(pid) for pid in pids), pids)
            finally:
                for path in (child_pid_path, grandchild_pid_path):
                    if path.is_file():
                        stop_test_process(int(path.read_text()))

    def test_task7_contentful_fixture_cohort_is_reproducible(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(HERE / "build_task7_fixtures.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Task 7 fixture cohort: PASS", completed.stdout)

    def test_task7_generated_fixture_bytes_have_no_trailing_whitespace(self) -> None:
        generator = importlib.import_module("build_task7_fixtures")
        defects = []
        for path, raw in generator.build_expected().items():
            for line_number, line in enumerate(raw.splitlines(), 1):
                if line.endswith((b" ", b"\t")):
                    defects.append(f"{path.relative_to(ROOT).as_posix()}:{line_number}")
        self.assertEqual(defects, [])
        completed = subprocess.run(
            ["git", "diff", "--check", "--", "tests/ci-readback/build_task7_fixtures.py", "tests/ci-readback"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_task7_full_local_ci_fixture_uses_current_exact_command_count(self) -> None:
        runner = importlib.import_module("run_local_ci")
        log = json.loads((HERE / "support/task7-full-local-ci.log").read_text(encoding="utf-8"))
        self.assertEqual(len(log["entries"]), 1)
        stdout = base64.b64decode(log["entries"][0]["stdout_base64"], validate=True)
        count = len(runner.COMMANDS)
        completion = runner.parse_completion_stdout(stdout)
        self.assertEqual(completion["command_count"], count)
        self.assertEqual(completion["executed_count"], count)
        self.assertEqual(completion["command_list_sha256"], runner.command_list_sha256())
        self.assertEqual(completion["execution_plan_sha256"], runner.execution_plan_sha256())

    def test_workflow_rejects_executable_step_injected_before_full_ci(self) -> None:
        self.require_checker()
        checker = importlib.import_module("check_ci_readback")
        raw = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        needle = "      - name: Build and verify runtime\n"
        injected = (
            "      - name: Replace full CI verifier bytes\n"
            "        run: Set-Content tools/run_local_ci.py 'raise SystemExit(0)'\n\n"
            + needle
        )
        self.assertIn(needle, raw)
        with self.assertRaisesRegex(ValueError, "step set"):
            checker._workflow_contract(raw.replace(needle, injected, 1).encode("utf-8"))

    def test_workflow_is_full_history_read_only_and_has_named_linux_a01_join(self) -> None:
        self.require_checker()
        workflow_path = ROOT / ".github" / "workflows" / "ci.yml"
        raw = workflow_path.read_text(encoding="utf-8")
        workflow = yaml.safe_load(raw)
        self.assertEqual(workflow["name"], "CI")
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        job = workflow["jobs"]["runtime-checks"]
        self.assertEqual(job["runs-on"], "ubuntu-latest")
        steps = job["steps"]
        checkout = next(step for step in steps if step.get("uses") == "actions/checkout@v5")
        self.assertEqual(checkout.get("with", {}).get("fetch-depth"), 0)
        names = [step.get("name") for step in steps]
        self.assertLess(names.index("Verify tracked source binding and checkpoint"), names.index("Linux A01 custody self-test"))
        self.assertLess(names.index("Linux A01 custody self-test"), names.index("Verify Linux A01 evidence writer source"))
        self.assertLess(names.index("Verify Linux A01 evidence writer source"), names.index("Emit Linux A01 evidence"))
        self.assertLess(names.index("Emit Linux A01 evidence"), names.index("Upload Linux A01 evidence"))
        self.assertLess(names.index("Upload Linux A01 evidence"), names.index("Verify full CI executor source"))
        self.assertLess(names.index("Verify full CI executor source"), names.index("Build and verify runtime"))
        commands = {step.get("name"): step.get("run") for step in steps if step.get("name")}
        self.assertEqual(commands["Verify tracked source binding and checkpoint"], "python tools/check_source_provenance.py --tracked-only")
        self.assertEqual(commands["Linux A01 custody self-test"], "python tools/check_captured_output_manifest.py --self-test")
        self.assertIn("git hash-object tools/write_linux_a01_evidence.py", commands["Verify Linux A01 evidence writer source"])
        self.assertIn("git hash-object tools/run_local_ci.py", commands["Verify full CI executor source"])
        self.assertIn("git hash-object tools/sanitized_python_bootstrap.py", commands["Verify full CI executor source"])
        writer_command = commands["Emit Linux A01 evidence"]
        self.assertEqual(
            writer_command,
            'python tools/write_linux_a01_evidence.py --out .ci-evidence/linux-a01.json '
            '--source-sha "${{ github.sha }}" --run-id "${{ github.run_id }}" '
            '--run-number "${{ github.run_number }}" --run-attempt "${{ github.run_attempt }}" '
            '--job-name runtime-checks --runner-label ubuntu-latest '
            '--runner-environment "${{ runner.environment }}"',
        )
        upload = next(step for step in steps if step.get("name") == "Upload Linux A01 evidence")
        self.assertEqual(upload.get("uses"), "actions/upload-artifact@v4")
        self.assertEqual(upload.get("with", {}).get("name"), "linux-a01-evidence")
        self.assertEqual(upload.get("with", {}).get("path"), ".ci-evidence/linux-a01.json")
        self.assertEqual(upload.get("with", {}).get("if-no-files-found"), "error")
        self.assertEqual(upload.get("with", {}).get("retention-days"), 90)
        self.assertEqual(
            commands["Build and verify runtime"],
            "python -I -S -B tools/sanitized_python_bootstrap.py --script tools/run_local_ci.py --strict-pwsh --command-timeout-seconds 900",
        )
        lowered = raw.lower()
        for forbidden in ("openai", "anthropic", "model-runner", "codex exec", "provider call"):
            self.assertNotIn(forbidden, lowered)

    def test_scoped_and_global_owner_gates_cover_current_task3b_through_task6_paths(self) -> None:
        self.require_checker()
        registry_checker = importlib.import_module("check_andon_contract_registry")
        registry = json.loads(
            (ROOT / "docs" / "audits" / "v0.4.6.0-wip-andon-contract-registry.json").read_text(encoding="utf-8")
        )
        a14 = next(row for row in registry["contracts"] if row["andon_id"] == "A14")
        a16 = next(row for row in registry["contracts"] if row["andon_id"] == "A16")
        self.assertIn("schema/ci-readback.schema.json", a16["owned_schema_paths"])
        self.assertIn("tools/check_ci_readback.py", a16["owned_tool_paths"])
        self.assertIn("tools/write_task7_deterministic_evidence.py", a16["owned_tool_paths"])
        self.assertIn("tools/sanitized_python_bootstrap.py", a16["owned_tool_paths"])
        self.assertIn("tools/run_no_model_preflight.py", a16["owned_tool_paths"])
        self.assertIn("tools/run_local_ci.py", a16["owned_tool_paths"])
        self.assertIn("tests/ci-readback/test_contract.py", a16["owned_test_paths"])
        self.assertIs(registry["rules"].get("ci_readback_owner_paths_must_exist"), True)
        self.assertIs(registry["rules"].get("candidate_custody_owner_paths_must_exist"), True)
        self.assertIs(registry["rules"].get("candidate_maturity_owner_paths_must_exist"), True)
        self.assertIs(registry["rules"].get("reviewed_campaign_owner_paths_must_exist"), True)
        self.assertIs(registry["rules"].get("global_missing_owner_path_rejection"), True)
        self.assertNotIn("global_missing_owner_path_rejection_deferred_reason", registry["rules"])
        for row, expected in (
            (a16, registry_checker.CI_READBACK_OWNER_PATHS),
            (a14, registry_checker.CANDIDATE_CUSTODY_OWNER_PATHS),
            (a16, registry_checker.CANDIDATE_MATURITY_OWNER_PATHS),
            (a16, registry_checker.REVIEWED_CAMPAIGN_OWNER_PATHS),
        ):
            for field, required_paths in expected.items():
                self.assertTrue(set(required_paths) <= set(row[field]), (row["andon_id"], field))


if __name__ == "__main__":
    unittest.main()
