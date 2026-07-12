#!/usr/bin/env python3
"""No-subprocess contract tests for the canonical Gate 14 input preflight."""
from __future__ import annotations

import contextlib
import io
import inspect
import json
import shutil
import sys
import tempfile
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

    def test_preflight_contract_self_test_is_wired_into_local_ci(self) -> None:
        self.assertIn(
            "python tools/run_no_model_preflight.py --self-test",
            local_ci.COMMANDS,
        )


if __name__ == "__main__":
    unittest.main()
