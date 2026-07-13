#!/usr/bin/env python3
"""No-subprocess contract tests for the canonical Gate 14 input preflight."""
from __future__ import annotations

import contextlib
import io
import inspect
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_no_model_preflight as preflight  # noqa: E402
import run_local_ci as local_ci  # noqa: E402
import smoke_matrix_registry as registry_owner  # noqa: E402


CANARY_SCRIPT = "tests/no-model-preflight/test_contract.py"


def _process_is_running(pid: int) -> bool:
    if os.name == "nt":
        import ctypes

        process = ctypes.windll.kernel32.OpenProcess(0x101000, False, pid)
        if not process:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code)):
                return False
            return exit_code.value == 259
        finally:
            ctypes.windll.kernel32.CloseHandle(process)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_for_process_exit(pid: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while _process_is_running(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    return not _process_is_running(pid)


def _force_kill_canary(pid: int) -> None:
    if not _process_is_running(pid):
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            check=False,
            timeout=5,
        )
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    _wait_for_process_exit(pid)


class Gate14RegistryContractTests(unittest.TestCase):
    def row_loader(self):
        loader = getattr(preflight, "load_five_smoke_preflight_rows", None)
        self.assertIsNotNone(
            loader,
            "Gate 14 must expose a registry-owned five-smoke row loader",
        )
        return loader

    def test_rows_match_exact_canonical_order(self) -> None:
        loader = self.row_loader()
        if loader is None:
            return
        expected = tuple(
            (row["case_id"], row["input_path"])
            for row in registry_owner.load_registry()["cases"]
        )
        self.assertEqual(loader(), expected)
        self.assertEqual(len(expected), 5)

    def test_gate14_runs_exact_registry_order_without_subprocesses(self) -> None:
        parameters = inspect.signature(
            preflight.gate_five_smoke_input_preflight,
        ).parameters
        self.assertIn("step_runner", parameters)
        if "step_runner" not in parameters:
            return
        commands: list[str] = []

        def record_step(command: str) -> preflight.StepResult:
            commands.append(command)
            return preflight.StepResult(
                command=command,
                argv=[],
                returncode=0,
                stdout="",
                stderr="",
                duration_sec=0.0,
            )

        passed, steps, repair_lane = preflight.gate_five_smoke_input_preflight(
            step_runner=record_step,
            timestamp="20000101-000000",
        )
        rows = self.row_loader()()
        expected_commands = [
            "python tools/run_staged_current_skill_smoke.py --preflight-input-only "
            f"--case-name {case_id} --raw-input-path {input_path} "
            f"--run-dir .daee/no-model-preflight/20000101-000000-{case_id}-input-preflight"
            for case_id, input_path in rows
        ]
        self.assertTrue(passed)
        self.assertEqual(commands, expected_commands)
        self.assertEqual(len(steps), 6)
        self.assertTrue(repair_lane)

    def test_registry_tuple_drift_is_registry_identity_failure(self) -> None:
        loader = self.row_loader()
        if loader is None:
            return
        registry = json.loads(registry_owner.DEFAULT_REGISTRY.read_text(encoding="utf-8"))
        registry["cases"][0]["case_id"] += "-drift"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "registry_identity"):
                loader(path, ROOT)
            parameters = inspect.signature(
                preflight.gate_five_smoke_input_preflight,
            ).parameters
            self.assertIn("registry_path", parameters)
            if "registry_path" not in parameters:
                return
            passed, steps, _ = preflight.gate_five_smoke_input_preflight(
                registry_path=path,
                registry_root=ROOT,
                step_runner=lambda command: self.fail(
                    f"registry drift reached subprocess step: {command}",
                ),
            )
            self.assertFalse(passed)
            self.assertEqual(len(steps), 1)
            self.assertIn("registry_identity", steps[0].stderr)

    def test_same_length_input_drift_is_registry_input_hash_failure(self) -> None:
        loader = self.row_loader()
        if loader is None:
            return
        registry = registry_owner.load_registry()
        with tempfile.TemporaryDirectory() as directory:
            mirror = Path(directory)
            for row in registry["cases"]:
                source = ROOT / row["input_path"]
                target = mirror / row["input_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            first = mirror / registry["cases"][0]["input_path"]
            raw = first.read_bytes()
            replacement = b"X" if raw[:1] != b"X" else b"Y"
            first.write_bytes(replacement + raw[1:])
            with self.assertRaisesRegex(ValueError, "registry_input_hash"):
                loader(registry_owner.DEFAULT_REGISTRY, mirror)
            parameters = inspect.signature(
                preflight.gate_five_smoke_input_preflight,
            ).parameters
            self.assertIn("registry_root", parameters)
            if "registry_root" not in parameters:
                return
            passed, steps, _ = preflight.gate_five_smoke_input_preflight(
                registry_path=registry_owner.DEFAULT_REGISTRY,
                registry_root=mirror,
                step_runner=lambda command: self.fail(
                    f"input hash drift reached subprocess step: {command}",
                ),
            )
            self.assertFalse(passed)
            self.assertEqual(len(steps), 1)
            self.assertIn("registry_input_hash", steps[0].stderr)

    def test_builtin_self_test_covers_gate14_without_subprocesses(self) -> None:
        output = io.StringIO()
        with mock.patch.object(
            preflight.subprocess,
            "run",
            side_effect=AssertionError("self-test must not invoke subprocesses"),
        ), contextlib.redirect_stdout(output):
            result = preflight.run_self_test()
        self.assertEqual(result, 0)
        text = output.getvalue()
        self.assertIn("Gate 14 derives exactly five ordered registry rows", text)
        self.assertIn("Gate 14 rejects registry identity drift", text)
        self.assertIn("Gate 14 rejects input hash drift", text)

    def test_gate16_requires_exit_one_with_matching_failure_class(self) -> None:
        sidecar = ROOT / preflight.STABLE_EXPLAIN_FIXTURE
        expected = json.loads(
            sidecar.with_name(f"{sidecar.stem}.expected-explain.json").read_text(encoding="utf-8")
        )
        stdout = json.dumps({"failure_class": expected["failure_class"]}) + "\n"

        for returncode, expected_passed in ((0, False), (1, True)):
            with self.subTest(returncode=returncode), mock.patch.object(
                preflight,
                "run_owned_command",
                return_value=local_ci.OwnedCommandResult([], returncode, stdout.encode(), b"", False),
            ) as owned_run:
                passed, steps, _repair_lane = preflight.gate_first_failed_checker_reporting()
            self.assertEqual(passed, expected_passed)
            self.assertEqual(steps[0].returncode, returncode)
            self.assertEqual(owned_run.call_count, 1)

    def test_gate16_routes_owned_timeout_into_truthful_failed_step(self) -> None:
        timed_out = preflight.StepResult(
            command="gate16 canary",
            argv=[],
            returncode=local_ci.TIMEOUT_EXIT_CODE,
            stdout="",
            stderr="TIMEOUT",
            duration_sec=0.0,
            timed_out=True,
        )
        with mock.patch.object(preflight, "run_step", return_value=timed_out) as run_step:
            passed, steps, _repair_lane = preflight.gate_first_failed_checker_reporting()
        self.assertFalse(passed)
        self.assertEqual(steps, [timed_out])
        self.assertTrue(steps[0].timed_out)
        self.assertEqual(run_step.call_count, 1)

    def test_gate17_composes_exact_runtime_and_parity_commands(self) -> None:
        expected = [
            "python tools/check_runtime_context_delivery.py --self-test",
            "python tools/check_runtime_context_delivery.py --fixtures tests/runtime-context-delivery",
            "python tools/check_producer_checker_parity.py --self-test",
            "python tools/check_producer_checker_parity.py --registry tools/producer-contract-registry.json",
            "python tools/check_package_harness_parity.py --self-test",
            "python tests/runtime-call-context-adapter/test_contract.py",
        ]
        with mock.patch.object(
            preflight,
            "steps_all_pass",
            return_value=(True, []),
        ) as composed:
            passed, _steps, repair = preflight.gate_runtime_context_and_producer_parity()
        self.assertTrue(passed)
        self.assertTrue(repair)
        composed.assert_called_once_with(expected)

    def test_a16_gate_table_is_explicit_and_contiguous(self) -> None:
        self.assertEqual([gate.number for gate in preflight.GATES], list(range(1, 26)))
        self.assertEqual(
            [gate.name for gate in preflight.GATES[17:]],
            [
                "tracked-source + checkpoint contracts",
                "exact-SHA CI/readback contracts",
                "VCS action-authorization contracts",
                "release action-authorization contracts",
                "candidate package custody",
                "source + candidate maturity",
                "evidence retention + export",
                "reviewed-campaign no-dispatch orchestration",
            ],
        )

    def test_a16_gates_compose_exact_no_model_commands(self) -> None:
        expected = {
            preflight.gate_tracked_source_and_checkpoint_contracts: [
                "python tools/check_source_provenance.py --self-test",
                "python tests/source-provenance/test_contract.py",
                "python tools/check_source_provenance.py --tracked-only",
            ],
            preflight.gate_exact_sha_ci_readback_contracts: [
                "python tools/check_ci_readback.py --self-test",
                "python -B tests/ci-readback/test_contract.py",
            ],
            preflight.gate_vcs_action_authorization_contracts: [
                "python tools/check_vcs_action_authorization.py --self-test",
                "python tests/vcs-action-authorization/test_contract.py",
            ],
            preflight.gate_release_action_authorization_contracts: [
                "python tools/check_release_action_authorization.py --self-test",
                "python tests/release-action-authorization/test_contract.py",
            ],
            preflight.gate_candidate_package_custody: [
                "python tools/build_candidate_package_record.py --self-test",
                "python tests/artifact-tree/test_contract.py",
                "python tests/candidate-build/test_contract.py",
            ],
            preflight.gate_source_and_candidate_maturity: [
                "python tools/check_no_model_candidate_maturity.py --self-test",
                "python tests/no-model-candidate-maturity/test_contract.py",
                "python tests/no-model-candidate-maturity/test_candidate_maturity.py",
            ],
            preflight.gate_evidence_retention_and_export: [
                "python tools/check_evidence_retention_manifest.py --self-test",
                "python tools/export_cycle_evidence_bundle.py --self-test",
                "python tests/evidence-retention/test_contract.py",
            ],
            preflight.gate_reviewed_campaign_no_dispatch: [
                "python tools/reviewed_campaign_orchestrator.py --self-test",
                "python tests/reviewed-campaign-orchestration/test_contract.py",
            ],
        }
        for gate, commands in expected.items():
            with self.subTest(gate=gate.__name__), mock.patch.object(
                preflight,
                "steps_all_pass",
                return_value=(True, []),
            ) as composed:
                passed, _steps, repair = gate()
                self.assertTrue(passed)
                self.assertTrue(repair)
                composed.assert_called_once_with(commands)

    def test_preflight_contract_self_test_is_wired_into_local_ci(self) -> None:
        self.assertIn(
            "python tools/run_no_model_preflight.py --self-test",
            local_ci.COMMANDS,
        )

    def test_preflight_python_steps_use_exact_isolated_profile_and_sanitized_environment(self) -> None:
        completed = local_ci.OwnedCommandResult([], 0, b"ok", b"", False)
        inherited = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": "attacker",
            "PYTHONHOME": "attacker",
            "__PYVENV_LAUNCHER__": "attacker",
        }
        with mock.patch.dict(os.environ, inherited, clear=True), mock.patch.object(
            preflight, "run_owned_command", return_value=completed
        ) as run:
            result = preflight.run_step("python tools/probe.py")
        self.assertEqual(
            run.call_args.args[0],
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
        child_env = run.call_args.kwargs["env"]
        self.assertFalse(any(key.upper().startswith("PYTHON") for key in child_env))
        self.assertNotIn("__PYVENV_LAUNCHER__", child_env)
        self.assertEqual(run.call_args.kwargs["cwd"], ROOT)
        self.assertTrue(run.call_args.kwargs["capture_output"])
        self.assertEqual(run.call_args.kwargs["timeout_seconds"], preflight.DEFAULT_TIMEOUT_SEC)
        self.assertEqual(result.execution_profile["profile_id"], local_ci.PYTHON_EXECUTION_PROFILE_ID)

    def test_timeout_terminates_real_child_and_grandchild_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            child_pid_path = temporary / "child.pid"
            grandchild_pid_path = temporary / "grandchild.pid"
            survival_marker = temporary / "unique-survival.marker"
            command = (
                f'python {CANARY_SCRIPT} --timeout-canary-child '
                f'"{child_pid_path}" "{grandchild_pid_path}" "{survival_marker}"'
            )
            result = preflight.run_step(command, timeout=1)
            self.assertTrue(result.timed_out)
            self.assertEqual(result.returncode, local_ci.TIMEOUT_EXIT_CODE)
            self.assertTrue(child_pid_path.exists())
            self.assertTrue(grandchild_pid_path.exists())
            child_pid = int(child_pid_path.read_text(encoding="utf-8"))
            grandchild_pid = int(grandchild_pid_path.read_text(encoding="utf-8"))
            try:
                self.assertTrue(_wait_for_process_exit(child_pid))
                self.assertTrue(_wait_for_process_exit(grandchild_pid))
                self.assertFalse(survival_marker.exists())
            finally:
                _force_kill_canary(child_pid)
                _force_kill_canary(grandchild_pid)

    def test_timeout_stops_next_command_in_same_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "same-gate-next-command.marker"
            commands = [
                f"python {CANARY_SCRIPT} --timeout-canary-sleep",
                f'python {CANARY_SCRIPT} --timeout-canary-write "{marker}"',
            ]
            passed, steps = preflight.steps_all_pass(commands, timeout=1)
            self.assertFalse(passed)
            self.assertEqual(len(steps), 1)
            self.assertTrue(steps[0].timed_out)
            self.assertFalse(marker.exists())

    def test_timeout_stops_every_later_gate_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "later-gate-command.marker"

            def timeout_gate() -> tuple[bool, list[preflight.StepResult], str]:
                step = preflight.run_step(
                    f"python {CANARY_SCRIPT} --timeout-canary-sleep",
                    timeout=1,
                )
                return False, [step], "timeout canary"

            def later_gate() -> tuple[bool, list[preflight.StepResult], str]:
                passed, steps = preflight.steps_all_pass(
                    [f'python {CANARY_SCRIPT} --timeout-canary-write "{marker}"']
                )
                return passed, steps, "must not run after timeout"

            gates = [
                preflight.Gate(1, "timeout gate", timeout_gate),
                preflight.Gate(2, "later gate", later_gate),
            ]
            with mock.patch.object(preflight, "GATES", gates), contextlib.redirect_stdout(io.StringIO()):
                result = preflight.run_full_sweep(None)
            self.assertEqual(result, 1)
            self.assertFalse(marker.exists())

    def test_teardown_failure_is_timeout_and_stops_every_later_gate_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            marker = temporary / "later-gate-after-teardown-failure.marker"
            report_path = temporary / "native-report.json"
            calls = 0

            def owned_runner(*_args, **_kwargs) -> local_ci.OwnedCommandResult:
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise RuntimeError(
                        "timed-out owned process tree root 424242 is still running"
                    )
                marker.write_text("later gate started", encoding="utf-8")
                return local_ci.OwnedCommandResult([], 0, b"", b"", False)

            def timeout_gate() -> tuple[bool, list[preflight.StepResult], str]:
                step = preflight.run_step("python tools/timeout-custody-canary.py")
                return False, [step], "timeout teardown canary"

            def later_gate() -> tuple[bool, list[preflight.StepResult], str]:
                step = preflight.run_step("python tools/later-gate-canary.py")
                return True, [step], "must not start after timeout teardown failure"

            gates = [
                preflight.Gate(1, "timeout teardown failure", timeout_gate),
                preflight.Gate(2, "later gate", later_gate),
            ]
            with mock.patch.object(preflight, "GATES", gates), mock.patch.object(
                preflight,
                "run_owned_command",
                side_effect=owned_runner,
            ), contextlib.redirect_stdout(io.StringIO()):
                result = preflight.run_full_sweep(report_path)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(result, 1)
            self.assertEqual(calls, 1)
            self.assertFalse(marker.exists())
            self.assertEqual(report["decision"], preflight.NOT_AUTHORIZED_TOKEN)
            self.assertFalse(report["complete"])
            self.assertEqual(report["gate_count"], 1)
            step = report["gates"][0]["steps"][0]
            self.assertEqual(step["returncode"], local_ci.TIMEOUT_EXIT_CODE)
            self.assertTrue(step["timed_out"])
            self.assertIn("owned process-tree teardown failed", step["stdout_tail"])

    def test_unrelated_owned_runner_runtime_error_is_not_classified_as_timeout(self) -> None:
        with mock.patch.object(
            preflight,
            "run_owned_command",
            side_effect=RuntimeError("unrelated owned runner failure"),
        ), self.assertRaisesRegex(RuntimeError, "unrelated owned runner failure"):
            preflight.run_step("python tools/unrelated-runtime-error-canary.py")

    def test_native_report_binds_complete_gate_command_and_profile_identity_atomically(self) -> None:
        results = []
        for gate in preflight.GATES:
            command = f"python tools/gate_{gate.number}.py"
            step = preflight.StepResult(
                command=command,
                argv=[],
                returncode=0,
                stdout="",
                stderr="",
                duration_sec=0.0,
                execution_profile=local_ci.execution_profile_for(command),
            )
            results.append(preflight.GateResult(gate.name, True, "", [step]))
        report = preflight.build_native_report(results)
        self.assertTrue(report["complete"])
        self.assertEqual(report["gate_count"], 25)
        self.assertEqual(report["command_count"], 25)
        self.assertEqual(report["python_execution_profile_id"], local_ci.PYTHON_EXECUTION_PROFILE_ID)
        commands = [step["command"] for gate in report["gates"] for step in gate["steps"]]
        self.assertEqual(report["command_set_sha256"], local_ci.command_list_sha256(commands))
        self.assertEqual(report["execution_plan_sha256"], local_ci.execution_plan_sha256(commands))
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "native.json"
            preflight.publish_native_report(target, report)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), report)

    def test_native_report_completion_follows_semantic_gates_and_timeouts(self) -> None:
        def passing_results_with_expected_nonzero() -> list[preflight.GateResult]:
            results = []
            for gate in preflight.GATES:
                command = f"python tools/gate_{gate.number}.py"
                if gate.number == 16:
                    command = (
                        "python tools/check_staged_runtime_handshake.py --explain-stage-failure "
                        f"--records {preflight.STABLE_EXPLAIN_FIXTURE}"
                    )
                step = preflight.StepResult(
                    command=command,
                    argv=[],
                    returncode=1 if gate.number == 16 else 0,
                    stdout="",
                    stderr="",
                    duration_sec=0.0,
                    execution_profile=local_ci.execution_profile_for(command),
                )
                results.append(preflight.GateResult(gate.name, True, "", [step]))
            return results

        with self.subTest("expected nonzero inside a passing gate is complete"):
            results = passing_results_with_expected_nonzero()
            report = preflight.build_native_report(results)
            self.assertEqual(report["decision"], preflight.AUTHORIZED_TOKEN)
            self.assertTrue(report["complete"])

        with self.subTest("timeout remains incomplete"):
            results = passing_results_with_expected_nonzero()
            results[15].steps[0].timed_out = True
            report = preflight.build_native_report(results)
            self.assertFalse(report["complete"])
            self.assertEqual(report["decision"], preflight.NOT_AUTHORIZED_TOKEN)
            self.assertTrue(report["gates"][15]["steps"][0]["timed_out"])

        with self.subTest("semantic gate failure remains incomplete"):
            results = passing_results_with_expected_nonzero()
            results[15].passed = False
            self.assertFalse(preflight.build_native_report(results)["complete"])

    def test_task7_shared_commands_are_unique_and_directly_wired(self) -> None:
        self.assertEqual(len(local_ci.COMMANDS), len(set(local_ci.COMMANDS)))
        required = [
            "python tools/check_source_provenance.py --self-test",
            "python tools/check_source_provenance.py --tracked-only",
            "python -B tests/source-provenance/test_contract.py",
            "python tools/check_ci_readback.py --self-test",
            "python -B tests/ci-readback/test_contract.py",
            "python tools/check_vcs_action_authorization.py --self-test",
            "python -B tests/vcs-action-authorization/test_contract.py",
            "python tools/check_release_action_authorization.py --self-test",
            "python -B tests/release-action-authorization/test_contract.py",
            "python tools/build_candidate_package_record.py --self-test",
            "python tests/artifact-tree/test_contract.py",
            "python tests/candidate-build/test_contract.py",
            "python tools/check_no_model_candidate_maturity.py --self-test",
            "python tests/no-model-candidate-maturity/test_contract.py",
            "python tests/no-model-candidate-maturity/test_candidate_maturity.py",
            "python tools/check_evidence_retention_manifest.py --self-test",
            "python tools/export_cycle_evidence_bundle.py --self-test",
            "python tests/evidence-retention/test_contract.py",
            "python tools/reviewed_campaign_orchestrator.py --self-test",
            "python tests/reviewed-campaign-orchestration/test_contract.py",
            "python tools/render_andon_closure_ledger.py --check",
        ]
        missing = [command for command in required if command not in local_ci.COMMANDS]
        self.assertEqual(missing, [])

    def test_ci_registry_accounts_for_required_task2_through_task7_integration_commands(self) -> None:
        registry = json.loads((TOOLS / "ci_registry.json").read_text(encoding="utf-8"))
        expected = {
            "task2-source-provenance-contract": "python -B tests/source-provenance/test_contract.py",
            "task3a-vcs-authorization-contract": "python -B tests/vcs-action-authorization/test_contract.py",
            "task3a-release-authorization-contract": "python -B tests/release-action-authorization/test_contract.py",
            "task3b-ci-readback-contract": "python -B tests/ci-readback/test_contract.py",
            "task3b-linux-evidence-writer-self-test": "python tools/write_linux_a01_evidence.py --self-test",
            "task3b-task7-evidence-writer-self-test": "python tools/write_task7_deterministic_evidence.py --self-test",
            "task4-candidate-builder-self-test": "python tools/build_candidate_package_record.py --self-test",
            "task4-artifact-tree-contract": "python tests/artifact-tree/test_contract.py",
            "task4-candidate-build-contract": "python tests/candidate-build/test_contract.py",
            "task4-smoke-protocol-contract": "python tests/smoke-matrix/test_protocol.py",
            "task5-retention-exporter-self-test": "python tools/export_cycle_evidence_bundle.py --self-test",
            "task5-retention-contract": "python tests/evidence-retention/test_contract.py",
            "task5-source-preflight-contract": "python tests/no-model-candidate-maturity/test_contract.py",
            "task5-candidate-maturity-contract": "python tests/no-model-candidate-maturity/test_candidate_maturity.py",
            "task6-reviewed-campaign-self-test": "python tools/reviewed_campaign_orchestrator.py --self-test",
            "task6-reviewed-campaign-contract": "python tests/reviewed-campaign-orchestration/test_contract.py",
            "task7-no-model-preflight-self-test": "python tools/run_no_model_preflight.py --self-test",
            "task7-closure-ledger-renderer-check": "python tools/render_andon_closure_ledger.py --check",
        }
        self.assertEqual(registry.get("required_integration_commands"), expected)


def _run_timeout_canary_mode() -> int | None:
    if len(sys.argv) >= 2 and sys.argv[1] == "--timeout-canary-child":
        child_pid_path = Path(sys.argv[2])
        grandchild_pid_path = Path(sys.argv[3])
        survival_marker = Path(sys.argv[4])
        child_pid_path.write_text(str(os.getpid()), encoding="utf-8")
        subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--timeout-canary-grandchild",
                str(grandchild_pid_path),
                str(survival_marker),
            ]
        )
        time.sleep(30)
        return 0
    if len(sys.argv) >= 2 and sys.argv[1] == "--timeout-canary-grandchild":
        grandchild_pid_path = Path(sys.argv[2])
        survival_marker = Path(sys.argv[3])
        grandchild_pid_path.write_text(str(os.getpid()), encoding="utf-8")
        time.sleep(10)
        survival_marker.write_text("grandchild survived timeout", encoding="utf-8")
        time.sleep(20)
        return 0
    if len(sys.argv) >= 2 and sys.argv[1] == "--timeout-canary-sleep":
        time.sleep(30)
        return 0
    if len(sys.argv) >= 3 and sys.argv[1] == "--timeout-canary-write":
        Path(sys.argv[2]).write_text("started", encoding="utf-8")
        return 0
    return None


if __name__ == "__main__":
    canary_result = _run_timeout_canary_mode()
    if canary_result is None:
        unittest.main()
    raise SystemExit(canary_result)
