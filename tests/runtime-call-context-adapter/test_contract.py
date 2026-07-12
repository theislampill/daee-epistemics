#!/usr/bin/env python3
"""Permanent Stage01/02 runtime-call preparation integration tests.

These tests exercise only deterministic pre-dispatch custody.  They never
invoke a model and do not claim state-capsule-v2 or release-bearing evidence.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from check_package_harness_parity import Failure as ParityFailure
from check_package_harness_parity import validate as validate_parity
from check_prompt_pack_budget import (
    BudgetViolation,
    build_prompt_pack_manifest_v2,
    validate_record as validate_prompt_pack,
)
from check_runtime_context_delivery import Failure as ContextFailure
from check_runtime_context_delivery import validate as validate_context
from runtime_call_context_adapter import (
    RuntimeCallPreparationError,
    materialize_execution_mini_package,
    prepare_runtime_call,
)


DEV_PACKAGE = ROOT / "skill"
V1_CAPSULE = (
    ROOT
    / "tests"
    / "state-capsule-fixtures"
    / "valid"
    / "multi-call-append"
    / "capsule-001.json"
)
EMPTY_VALIDATED_STATE = {
    "route_shards": [],
    "owner_module_ids": [],
    "cold_clause_ids": [],
    "live_pressure": False,
    "ambiguous": False,
}


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "runtime_call_context_runner_under_test",
        TOOLS / "run_staged_current_skill_smoke.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RuntimeCallContextAdapterContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package_tmp = tempfile.TemporaryDirectory(prefix="daee-execution-mini-")
        cls.package_root = materialize_execution_mini_package(
            ROOT,
            Path(cls.package_tmp.name) / "package",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.package_tmp.cleanup()
        scratch = ROOT / ".daee" / "runtime-call-context-test"
        if scratch.is_dir() and not any(scratch.iterdir()):
            scratch.rmdir()

    @staticmethod
    def raw_input(run_root: Path) -> Path:
        path = run_root / "source-input.md"
        if not path.exists():
            path.write_bytes(b"bounded neutral input\n")
        return path

    def same_run_v1_capsule(
        self,
        run_root: Path,
        *,
        case_id: str = "adapter-contract",
        stage: str = "01",
        input_digest: str | None = None,
    ) -> Path:
        raw_input = self.raw_input(run_root)
        payload = json.loads(V1_CAPSULE.read_text(encoding="utf-8"))
        payload["case_id"] = case_id
        payload["stage"] = stage
        payload["input_fingerprint"] = "sha256:" + (
            input_digest
            or __import__("hashlib").sha256(raw_input.read_bytes()).hexdigest()
        )
        capsule = run_root / "state-capsules" / "capsule-001.json"
        capsule.parent.mkdir(parents=True, exist_ok=True)
        capsule.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return capsule

    def prepare(
        self,
        run_root: Path,
        *,
        stage: str,
        call_index: int,
        previous_capsule: Path | None = None,
        limit: int = 500_000,
    ):
        raw_input = self.raw_input(run_root)
        harness_prompt = f"stage {stage} harness instructions\n"
        if stage == "02":
            harness_prompt += raw_input.read_text(encoding="utf-8")
        return prepare_runtime_call(
            package_root=self.package_root,
            repo_root=ROOT,
            run_dir=run_root,
            call_index=call_index,
            case_id="adapter-contract",
            stage=stage,
            raw_input_path=raw_input,
            previous_capsule_path=previous_capsule,
            harness_prompt=harness_prompt,
            validated_state=dict(EMPTY_VALIDATED_STATE),
            source_commit="4" * 40,
            effective_context_limit=limit,
        )

    def test_stage01_binds_raw_input_skill_and_kernel_clause_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            prepared = self.prepare(Path(td), stage="01", call_index=1)
            context = json.loads(prepared.context_path.read_text(encoding="utf-8"))
            parity = json.loads(prepared.parity_path.read_text(encoding="utf-8"))

            self.assertEqual(context["selection"]["selected_components"], ["raw-input", "package:SKILL.md"])
            self.assertTrue(context["state_capsule"]["bootstrap"])
            self.assertFalse(context["state_capsule"]["included"])
            self.assertEqual(parity["model_visible_clause_ids"], ["stage04.owner-act-execution"])
            self.assertEqual(validate_context(context, self.package_root, prepared.call_root)["status"], "pass")
            self.assertEqual(validate_parity(parity, self.package_root, prepared.call_root, ROOT)["status"], "pass")

    def test_stage02_binds_exact_validated_v1_capsule_and_diagnostic_components(self):
        with tempfile.TemporaryDirectory() as td:
            run_root = Path(td)
            capsule = self.same_run_v1_capsule(run_root)
            prepared = self.prepare(run_root, stage="02", call_index=2, previous_capsule=capsule)
            context = json.loads(prepared.context_path.read_text(encoding="utf-8"))
            parity = json.loads(prepared.parity_path.read_text(encoding="utf-8"))

            self.assertEqual(
                context["selection"]["selected_components"],
                [
                    "state-capsule",
                    "package:references/runtime-diagnostic-core.md",
                    "package:references/runtime-core-ir.md",
                ],
            )
            copied = prepared.call_root / context["state_capsule"]["path"]
            self.assertEqual(copied.read_bytes(), capsule.read_bytes())
            self.assertTrue(context["state_capsule"]["validated"])
            self.assertTrue(context["input"]["included"])
            self.assertIn(self.raw_input(run_root).read_bytes(), prepared.prompt_path.read_bytes())
            self.assertIn("historical-v1", " ".join(context["non_claims"]))
            self.assertEqual(parity["model_visible_clause_ids"], ["stage02.diagnostic-ir"])

            record = build_prompt_pack_manifest_v2(
                artifact_root=run_root,
                runtime_context_manifest_path=prepared.context_path,
                prompt_path=prepared.prompt_path,
                harness_frame_parts={
                    "harness:stage-prompt": "stage 02 harness instructions\nbounded neutral input\n"
                },
                includes_full_runtime=False,
                includes_prior_full_output=False,
            )
            validate_prompt_pack(record, 20_000, artifact_root=run_root)
            with self.assertRaises(BudgetViolation):
                build_prompt_pack_manifest_v2(
                    artifact_root=run_root,
                    runtime_context_manifest_path=prepared.context_path,
                    prompt_path=prepared.prompt_path,
                    harness_frame_parts={"harness:stage-prompt": "underreported"},
                    includes_full_runtime=False,
                    includes_prior_full_output=False,
                )

    def test_stage02_rejects_external_and_wrong_lineage_capsules(self):
        mutations = [
            ("external", None, None, None),
            ("wrong-stage", "adapter-contract", "02", None),
            ("wrong-case", "different-case", "01", None),
            ("wrong-input", "adapter-contract", "01", "f" * 64),
        ]
        for label, case_id, stage, digest in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as td:
                run_root = Path(td)
                capsule = (
                    V1_CAPSULE
                    if label == "external"
                    else self.same_run_v1_capsule(
                        run_root,
                        case_id=case_id or "adapter-contract",
                        stage=stage or "01",
                        input_digest=digest,
                    )
                )
                with self.assertRaises(RuntimeCallPreparationError):
                    self.prepare(run_root, stage="02", call_index=2, previous_capsule=capsule)

    def test_stage02_rejects_v2_until_a16_owner_integration(self):
        with tempfile.TemporaryDirectory() as td:
            run_root = Path(td)
            capsule = run_root / "state-capsules" / "capsule-001.json"
            capsule.parent.mkdir(parents=True)
            capsule.write_bytes((ROOT / "tests" / "state-capsule-v2" / "valid" / "low-topology.json").read_bytes())
            with self.assertRaisesRegex(RuntimeCallPreparationError, "v2.*unsupported"):
                self.prepare(run_root, stage="02", call_index=2, previous_capsule=capsule)

    def test_dev_skill_tree_is_not_accepted_as_execution_mini(self):
        with tempfile.TemporaryDirectory() as td:
            run_root = Path(td)
            raw_input = self.raw_input(run_root)
            with self.assertRaisesRegex(RuntimeCallPreparationError, "execution-mini"):
                prepare_runtime_call(
                    package_root=DEV_PACKAGE,
                    repo_root=ROOT,
                    run_dir=run_root,
                    call_index=1,
                    case_id="adapter-contract",
                    stage="01",
                    raw_input_path=raw_input,
                    previous_capsule_path=None,
                    harness_prompt="stage 01 harness instructions\n",
                    validated_state=dict(EMPTY_VALIDATED_STATE),
                    source_commit="4" * 40,
                    effective_context_limit=500_000,
                )

    def test_stage02_missing_capsule_fails_closed_before_call_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeCallPreparationError, "previous capsule"):
                self.prepare(Path(td), stage="02", call_index=2, previous_capsule=None)
            self.assertFalse((Path(td) / "runtime-calls" / "call-002-stage-02" / "context.json").exists())

    def test_prompt_tamper_is_rejected_by_both_context_and_parity(self):
        with tempfile.TemporaryDirectory() as td:
            prepared = self.prepare(Path(td), stage="01", call_index=1)
            record = build_prompt_pack_manifest_v2(
                artifact_root=Path(td),
                runtime_context_manifest_path=prepared.context_path,
                prompt_path=prepared.prompt_path,
                harness_frame_parts={"harness:stage-prompt": "stage 01 harness instructions\n"},
                includes_full_runtime=False,
                includes_prior_full_output=False,
            )
            prepared.prompt_path.write_bytes(prepared.prompt_path.read_bytes() + b"tamper")
            context = json.loads(prepared.context_path.read_text(encoding="utf-8"))
            parity = json.loads(prepared.parity_path.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(ContextFailure, "prompt bytes changed"):
                validate_context(context, self.package_root, prepared.call_root)
            with self.assertRaises(ParityFailure):
                validate_parity(parity, self.package_root, prepared.call_root, ROOT)

            with self.assertRaises(BudgetViolation):
                validate_prompt_pack(record, 20_000, artifact_root=Path(td))

    def test_over_budget_selected_context_fails_before_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeCallPreparationError, "over-budget-without-hold"):
                self.prepare(Path(td), stage="01", call_index=1, limit=1)

    def test_stage02_empty_clause_inventory_remains_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            run_root = Path(td)
            capsule = self.same_run_v1_capsule(run_root)
            prepared = self.prepare(run_root, stage="02", call_index=2, previous_capsule=capsule)
            parity = json.loads(prepared.parity_path.read_text(encoding="utf-8"))
            parity["model_visible_clause_ids"] = []
            with self.assertRaises(ParityFailure):
                validate_parity(parity, self.package_root, prepared.call_root, ROOT)

    @staticmethod
    def runner_args(runner, run_dir: Path):
        return SimpleNamespace(
            run_dir=run_dir,
            resume_run_dir=None,
            raw_input="bounded neutral input",
            raw_input_path=runner.DEFAULT_INPUT,
            replay_record=runner.DEFAULT_REPLAY_RECORD,
            case_name="adapter-contract",
            stop_after_stage="stage-01-intake",
            release_output_mode="single-output",
            target_output_kb=0,
            section_expansion_rounds=0,
            transport_retry_rounds=0,
            runtime_context_limit_bytes=500_000,
            model="fake-model",
        )

    def test_actual_runner_call_site_does_not_dispatch_when_preparation_fails(self):
        runner = load_runner()
        scratch = ROOT / ".daee" / "runtime-call-context-test"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as td:
            args = self.runner_args(runner, Path(td) / "run")
            with mock.patch.object(runner, "materialize_execution_mini_package", return_value=self.package_root), mock.patch.object(
                runner, "source_commit_for_runtime_context", return_value="4" * 40
            ), mock.patch.object(
                runner, "prepare_stage_runtime_call", side_effect=runner.HarnessError("bounded preparation failure")
            ), mock.patch.object(runner, "invoke_stage_call_with_transport_retry") as invoke, mock.patch.object(
                runner, "write_hash_record"
            ):
                self.assertEqual(runner.run_model_smoke(args, ROOT), 2)
                invoke.assert_not_called()

    def test_actual_runner_hashes_bound_context_parity_prompt_and_prompt_pack(self):
        runner = load_runner()
        scratch = ROOT / ".daee" / "runtime-call-context-test"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as td:
            run_dir = Path(td) / "run"
            args = self.runner_args(runner, run_dir)

            def fake_prepare(**kwargs):
                call_root = kwargs["run_dir"] / "runtime-calls" / "call-001-stage-01"
                call_root.mkdir(parents=True)
                prompt = call_root / "prompt.md"; prompt.write_text("bound prompt\n", encoding="utf-8")
                context = call_root / "context.json"; context.write_text("{}\n", encoding="utf-8")
                parity = call_root / "package-harness-parity.json"; parity.write_text("{}\n", encoding="utf-8")
                (call_root / "harness-stage-prompt.md").write_text(kwargs["harness_prompt"], encoding="utf-8")
                (call_root / "raw-input.bin").write_bytes(kwargs["raw_input_path"].read_bytes())
                return runner.PreparedRuntimeCall("bound prompt\n", call_root, prompt, context, parity)

            def fake_emit(**kwargs):
                kwargs["manifest_path"].write_text("{}\n", encoding="utf-8")
                return {}

            def fake_capsule(**kwargs):
                path = kwargs["run_dir"] / "state-capsules" / "capsule-001.json"
                path.parent.mkdir(parents=True, exist_ok=True); path.write_text("{}\n", encoding="utf-8")
                return path

            captured: dict[str, object] = {}

            def capture_hashes(*args, **kwargs):
                captured.update(kwargs)

            response = {
                "id": "stage-01-intake",
                "status": "pass",
                "input_digest": __import__("hashlib").sha256(b"bounded neutral input\n").hexdigest(),
            }
            with mock.patch.object(runner, "materialize_execution_mini_package", return_value=self.package_root), mock.patch.object(
                runner, "source_commit_for_runtime_context", return_value="4" * 40
            ), mock.patch.object(runner, "prepare_stage_runtime_call", side_effect=fake_prepare), mock.patch.object(
                runner, "emit_prompt_pack_manifest_v2", side_effect=fake_emit
            ), mock.patch.object(runner, "invoke_stage_call_with_transport_retry", return_value=response), mock.patch.object(
                runner, "write_state_capsule", side_effect=fake_capsule
            ), mock.patch.object(runner, "validate_replay_record"), mock.patch.object(
                runner, "write_hash_record", side_effect=capture_hashes
            ):
                self.assertEqual(runner.run_model_smoke(args, ROOT), 0)

            paths = {Path(path) for path in captured["stage_files"]}
            call_root = run_dir / "runtime-calls" / "call-001-stage-01"
            self.assertTrue(
                {
                    call_root / "context.json",
                    call_root / "package-harness-parity.json",
                    call_root / "prompt.md",
                    run_dir / "prompt-pack-manifest.jsonl",
                }.issubset(paths)
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
