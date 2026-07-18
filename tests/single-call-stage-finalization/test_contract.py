#!/usr/bin/env python3
"""Permanent no-model tests for one captured single-call finalization.

The positive fixture is an existing retained A9 staged record and output.  No
provider or model is invoked by this suite.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import stat
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import finalize_single_call_stage_capture as finalizer
import run_staged_current_skill_smoke as stage_runner
import single_call_stage_envelope as envelope


NONCE = "0123456789abcdef0123456789abcdef"
CASE_ID = "a9-science-source"
CYCLE_ID = "b11-single-call-finalization-contract"
CANDIDATE_BINDING = {
    "candidate_id": "b10-2ddd4d9-candidate-01",
    "source_commit": "2ddd4d9efab2b437331b3f5d6247cb8f02abcfdf",
    "candidate_record_sha256": "1" * 64,
    "candidate_maturity_sha256": "2" * 64,
    "archive_sha256": "3" * 64,
    "package_tree_sha256": "4" * 64,
    "skill_sha256": "5" * 64,
    "build_manifest_sha256": "6" * 64,
}
FIXTURE_RECORD = (
    ROOT
    / "tests"
    / "staged-runtime-handshake"
    / "valid"
    / "retained-a9-science-source.json"
)
FIXTURE_INPUT = (
    ROOT
    / "tests"
    / "retained-proof-corpus"
    / "v0.4.3.0-schema-light"
    / "valid"
    / "sidecar-backed"
    / "cases"
    / "a9-science-source"
    / "input.txt"
)
FIXTURE_OUTPUT = FIXTURE_INPUT.with_name("output.md")
_CURRENT_OUTPUT_BYTES: bytes | None = None


def canonical_input_bytes() -> bytes:
    # The fixture's committed binding is LF; tolerate a Windows checkout's
    # single CRLF conversion while preserving the exact committed bytes here.
    return FIXTURE_INPUT.read_bytes().replace(b"\r\n", b"\n")


def canonical_stage_records() -> list[dict[str, object]]:
    source = json.loads(FIXTURE_RECORD.read_text(encoding="utf-8"))
    stages = copy.deepcopy(source["stages"][:6])
    stages[0]["input_digest"] = hashlib.sha256(canonical_input_bytes()).hexdigest()

    stage04 = stages[3]
    stage04["act_row_details"] = [
        {
            "act_row": stage04["act_rows"][0],
            "body_ref": "¹B₁",
            "burden_id": "B1",
            "owner_id": "source-status-repair",
            "operation": "source-order",
            "pressure": "scientific-explanations-only-knowledge-source",
            "delta": "Δ¹B",
            "delta_result": "science-source-bounded",
            "land": "Land(¹B)+",
            "register_axis": "σ",
        },
        {
            "act_row": stage04["act_rows"][1],
            "body_ref": "¹B₂",
            "burden_id": "B1",
            "owner_id": "M1",
            "operation": "self-grounding-test",
            "pressure": "only-science-counts-standard",
            "delta": "Δ¹B",
            "delta_result": "self-authorizing-standard-invalidated",
            "land": "Land(¹B)+",
            "register_axis": "H",
        },
    ]
    stages[4]["produces"] = [
        "terminal_states",
        "dependency_graph_edges",
        "no_new_resultant_proof",
        "per_burden_reread",
    ]
    stages[5]["produces"] = [
        "field_witness_body_refs",
        "nar_burdens",
        "owner_activations",
        "normalized_activation_record",
        "register_deltas",
    ]
    stages.append(
        {
            "id": "stage-07-release-output",
            "status": "pass",
            "produces": ["release_output", "release_terminal_states"],
            "requires": ["field_witness_body_refs", "nar_burdens"],
            "release_output_transport": "exact-tail-after-marker",
            "release_terminal_states": copy.deepcopy(stages[4]["terminal_states"]),
            "closure_claim": "complete",
            "output_is_full_governed_answer": True,
        }
    )
    return stages


def valid_payload() -> dict[str, object]:
    raw_input = canonical_input_bytes()
    return {
        "schema": "daee-single-call-stage-envelope-v1",
        "envelope_nonce": NONCE,
        "case_id": CASE_ID,
        "cycle_id": CYCLE_ID,
        "candidate_binding": copy.deepcopy(CANDIDATE_BINDING),
        "input_binding": {
            "sha256": hashlib.sha256(raw_input).hexdigest(),
            "byte_count": len(raw_input),
        },
        "stage_records": canonical_stage_records(),
        "stage08_request": {
            "id": "stage-08-verifier-sidecars",
            "status": "pending-checker",
            "owner": "private-source-bound-checker",
            "input": "exact-stage07-tail",
        },
        "non_claims": list(envelope.REQUIRED_NON_CLAIMS),
    }


def current_output_bytes() -> bytes:
    """Regenerate the current governed output from the retained A9 source.

    The A9 record remains the positive staged source, but its historically
    bound output predates the current/historical witness-role join.  The
    repository's own compiled-output path is the governed deterministic
    migration carrier used by the staged-runner self-test.
    """
    global _CURRENT_OUTPUT_BYTES
    if _CURRENT_OUTPUT_BYTES is not None:
        return _CURRENT_OUTPUT_BYTES
    case_dir = ROOT / ".daee" / "sf-fixture" / uuid.uuid4().hex[:12]
    stages = canonical_stage_records()
    source_text = FIXTURE_OUTPUT.read_text(encoding="utf-8", errors="strict")
    mrp_section = stage_runner.stage07_mrp_reread_section_scaffold(stages)
    witness_section = stage_runner.stage07_field_witness_section_scaffold(stages)
    sections = [
        (
            section_id,
            role,
            mrp_section
            if role == "mrp_reread_terminal"
            else witness_section
            if role == "field_witness_nar"
            else text,
        )
        for section_id, role, text in stage_runner.split_text_for_compiled_self_test(source_text)
    ]
    try:
        manifest = stage_runner.staged_output.manifest_for_sections(
            case_dir,
            case_id="single-call-finalization-current-a9",
            source_input=FIXTURE_OUTPUT.relative_to(ROOT).as_posix(),
            section_specs=sections,
            per_burden_reread=copy.deepcopy(stages[4]["per_burden_reread"]),
        )
        assembly = stage_runner.assemble_compiled_manifest(manifest, root=ROOT)
        output_path = ROOT / assembly["output"]["path"]
        _CURRENT_OUTPUT_BYTES = output_path.read_bytes()
        return _CURRENT_OUTPUT_BYTES
    finally:
        remove_tree(case_dir)


def encode_envelope(payload: dict[str, object] | None = None, *, output: bytes | None = None) -> bytes:
    body = json.dumps(
        payload or valid_payload(),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    tail = current_output_bytes() if output is None else output
    return (
        f"DAEE-SINGLE-CALL-ENVELOPE-V1 {NONCE}\n"
        f"BEGIN-STAGE-JSON {NONCE}\n"
    ).encode("ascii") + body + (
        f"\nEND-STAGE-JSON {NONCE}\n"
        f"BEGIN-FINAL-OUTPUT {NONCE}\n"
    ).encode("ascii") + tail


def remove_tree(path: Path) -> None:
    def make_writable(function, candidate, _exc):
        os.chmod(candidate, stat.S_IWRITE)
        function(candidate)

    if path.exists():
        shutil.rmtree(path, onerror=make_writable)


def snapshot_manifest_sha256(files: list[dict[str, object]]) -> str:
    raw = (
        json.dumps(files, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class SingleCallStageFinalizationContract(unittest.TestCase):
    def setUp(self) -> None:
        self.parent = ROOT / ".daee" / "sf-contract"
        self.parent.mkdir(parents=True, exist_ok=True)
        self.run_relative = Path(".daee") / "sf-contract" / uuid.uuid4().hex[:12]
        self.run_root = ROOT / self.run_relative

    def tearDown(self) -> None:
        remove_tree(self.run_root)

    def finalize(self, **overrides):
        payload = valid_payload()
        arguments = {
            "root": ROOT,
            "run_root": self.run_relative,
            "raw_envelope": encode_envelope(payload),
            "raw_input": canonical_input_bytes(),
            "expected_envelope_nonce": NONCE,
            "expected_case_id": CASE_ID,
            "expected_cycle_id": CYCLE_ID,
            "expected_candidate_binding": CANDIDATE_BINDING,
            "expected_input_binding": payload["input_binding"],
        }
        arguments.update(overrides)
        return finalizer.finalize_single_call_stage_capture(**arguments)

    def assert_rejected(self, code: str, **overrides) -> None:
        with self.assertRaises(finalizer.FinalizationError) as caught:
            self.finalize(**overrides)
        self.assertEqual(caught.exception.code, code, str(caught.exception))

    def test_finalization_is_checkout_bytecode_residue_neutral(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        residue_before = orchestrator.checkout_execution_residue_inventory(ROOT)
        self.assertEqual("PASS", residue_before["status"], residue_before)
        self.finalize()
        residue_after = orchestrator.checkout_execution_residue_inventory(ROOT)
        self.assertEqual(residue_before, residue_after)

    def test_retained_a9_capture_finalizes_with_exact_checker_owned_evidence(self) -> None:
        result = self.finalize()
        parsed = envelope.parse_single_call_stage_envelope(
            encode_envelope(),
            expected_envelope_nonce=NONCE,
            expected_case_id=CASE_ID,
            expected_cycle_id=CYCLE_ID,
            expected_candidate_binding=CANDIDATE_BINDING,
            expected_input_binding=valid_payload()["input_binding"],
        )

        self.assertEqual((self.run_root / "capture/raw-envelope.bin").read_bytes(), parsed.raw_bytes)
        self.assertEqual((self.run_root / "capture/raw-input.bin").read_bytes(), canonical_input_bytes())
        self.assertEqual((self.run_root / "capture/stage-json.bin").read_bytes(), parsed.stage_json_bytes)
        self.assertEqual((self.run_root / "capture/stage07-output.md").read_bytes(), parsed.final_output_bytes)
        producer_files = sorted((self.run_root / "stages/producer").glob("stage-*.json"))
        self.assertEqual(len(producer_files), 6)
        capsule_files = sorted((self.run_root / "state-capsules").glob("capsule-*.json"))
        self.assertEqual(len(capsule_files), 7)
        self.assertTrue((self.run_root / "checker-execution/stage07-release/.artifacts/output.snapshot.md").is_file())

        stage07 = json.loads(result.stage07_path.read_text(encoding="utf-8"))
        stage08 = json.loads(result.stage08_path.read_text(encoding="utf-8"))
        record = json.loads(result.record_path.read_text(encoding="utf-8"))
        manifest = json.loads(result.finalization_path.read_text(encoding="utf-8"))
        self.assertNotIn("release_output_transport", stage07)
        self.assertTrue(all(value == "pass" for value in stage07["release_validation"].values()))
        self.assertTrue(stage07["release_field_diagnostics"]["matches"])
        self.assertEqual(stage08["release_validation_policy"], stage07["release_validation_policy"])
        self.assertFalse(stage08["verifier_sidecars"]["b5_4_1"]["claimed"])
        self.assertEqual(
            stage08["verifier_sidecars"]["b5_4_1"]["role"],
            "checker-owned-final-verifier-built-but-not-retained",
        )
        proof_sidecars = stage08["verifier_sidecars"]["proof_sidecars"]["paths"]
        self.assertEqual(len(proof_sidecars), 5)
        carrier_path = self.run_root / "proof-sidecars" / f"capture-{NONCE}.b5-current-stage-carriers.json"
        self.assertTrue(carrier_path.is_file())
        b5_path = ROOT / stage08["verifier_sidecars"]["b5_4_1"]["path"]
        b5 = json.loads(b5_path.read_text(encoding="utf-8"))
        self.assertEqual(
            b5["projection"]["current_adapter"]["schema"],
            "b5-current-public-field-witness-adapter-v1",
        )
        self.assertFalse(
            b5["projection"]["current_adapter"]["historical_diagnostic_member_added"]
        )
        self.assertEqual([stage["id"] for stage in record["stages"]], list(finalizer.STAGE_ORDER))
        self.assertEqual(manifest["verdict"], "SINGLE_CALL_STRUCTURAL_FINALIZATION_PASS")
        self.assertEqual(manifest["bindings"]["candidate"], CANDIDATE_BINDING)
        self.assertEqual(manifest["capture"]["raw_envelope"]["sha256"], parsed.raw_sha256)
        self.assertEqual(manifest["capture"]["stage_json"]["start"], parsed.stage_json_start)
        self.assertEqual(manifest["capture"]["stage07_output"]["end"], parsed.final_output_end)
        self.assertEqual(
            manifest["non_claims"],
            {
                "not_semantic_truth": True,
                "not_campaign_success": True,
                "not_human_pre_disclosure_assessment": True,
                "not_cold_review": True,
                "not_release_or_owner_acceptance": True,
            },
        )
        self.assertEqual(
            manifest,
            finalizer.revalidate_single_call_stage_capture(
                root=ROOT,
                finalization_ref=finalizer._artifact(result.finalization_path, ROOT),
                expected_case_id=CASE_ID,
                expected_cycle_id=CYCLE_ID,
                expected_candidate_binding=CANDIDATE_BINDING,
                expected_input_binding=valid_payload()["input_binding"],
            ),
        )

    def _revalidate(self, result) -> dict[str, object]:
        return finalizer.revalidate_single_call_stage_capture(
            root=ROOT,
            finalization_ref=finalizer._artifact(result.finalization_path, ROOT),
            expected_case_id=CASE_ID,
            expected_cycle_id=CYCLE_ID,
            expected_candidate_binding=CANDIDATE_BINDING,
            expected_input_binding=valid_payload()["input_binding"],
        )

    def _rewrite_release_evidence(self, result, manifest, evidence) -> None:
        evidence_ref = manifest["checker_owned"]["release_validation_evidence"]
        evidence_raw = finalizer._json_bytes(evidence)
        (ROOT / evidence_ref["path"]).write_bytes(evidence_raw)
        evidence_ref.update(
            sha256=hashlib.sha256(evidence_raw).hexdigest(),
            byte_count=len(evidence_raw),
        )
        result.finalization_path.write_bytes(finalizer._json_bytes(manifest))

    def test_revalidation_rejects_zero_file_snapshot_manifest(self) -> None:
        result = self.finalize()
        manifest = json.loads(result.finalization_path.read_text(encoding="utf-8"))
        evidence_ref = manifest["checker_owned"]["release_validation_evidence"]
        evidence = json.loads((ROOT / evidence_ref["path"]).read_text(encoding="utf-8"))
        empty_snapshot = {
            "schema": "daee-checker-execution-snapshot-v1",
            "sha256": snapshot_manifest_sha256([]),
            "file_count": 0,
            "files": [],
        }
        evidence["snapshot_manifest"] = empty_snapshot
        manifest["release_validation"]["execution_snapshot"] = copy.deepcopy(empty_snapshot)
        self._rewrite_release_evidence(result, manifest, evidence)
        with self.assertRaises(finalizer.FinalizationError):
            self._revalidate(result)

    def test_revalidation_rejects_deleted_checker_hidden_from_snapshot_manifest(self) -> None:
        result = self.finalize()
        manifest = json.loads(result.finalization_path.read_text(encoding="utf-8"))
        evidence_ref = manifest["checker_owned"]["release_validation_evidence"]
        evidence = json.loads((ROOT / evidence_ref["path"]).read_text(encoding="utf-8"))
        checker_row = next(
            row for row in evidence["bound_plan"] if row["invocation_kind"] == "checker"
        )
        source_path = checker_row["source_path"]
        snapshot_root = ROOT / evidence["snapshot_root"]
        retained_checker = snapshot_root / source_path
        retained_checker.chmod(stat.S_IWRITE)
        retained_checker.unlink()
        files = [
            row for row in evidence["snapshot_manifest"]["files"] if row["path"] != source_path
        ]
        evidence["snapshot_manifest"]["files"] = files
        evidence["snapshot_manifest"]["file_count"] = len(files)
        evidence["snapshot_manifest"]["sha256"] = snapshot_manifest_sha256(files)
        manifest["release_validation"]["execution_snapshot"] = copy.deepcopy(
            evidence["snapshot_manifest"]
        )
        self._rewrite_release_evidence(result, manifest, evidence)
        with self.assertRaises(finalizer.FinalizationError):
            self._revalidate(result)

    def test_revalidation_reruns_checkers_instead_of_trusting_forged_pass_results(self) -> None:
        result = self.finalize()
        replay_failure = stage_runner.HarnessError("forced deterministic replay failure")
        with mock.patch.object(
            finalizer.stage_runner,
            "require_command_success",
            side_effect=replay_failure,
        ):
            with self.assertRaises(finalizer.FinalizationError):
                self._revalidate(result)

    def test_revalidation_rejects_bound_plan_argument_substitution(self) -> None:
        result = self.finalize()
        manifest = json.loads(result.finalization_path.read_text(encoding="utf-8"))
        evidence_ref = manifest["checker_owned"]["release_validation_evidence"]
        evidence = json.loads((ROOT / evidence_ref["path"]).read_text(encoding="utf-8"))
        checker_row = next(
            row for row in evidence["bound_plan"] if row["invocation_kind"] == "checker"
        )
        checker_row["arguments"][-1] = str(self.run_root / "substituted-output.md")
        self._rewrite_release_evidence(result, manifest, evidence)
        with self.assertRaises(finalizer.FinalizationError):
            self._revalidate(result)

    def test_revalidation_rejects_content_addressed_empty_handoff(self) -> None:
        result = self.finalize()
        manifest = json.loads(result.finalization_path.read_text(encoding="utf-8"))
        handoff_ref = manifest["checker_owned"]["staged_handoff_record"]
        target = ROOT / handoff_ref["path"]
        replacement = finalizer._json_bytes({})
        target.write_bytes(replacement)
        handoff_ref.update(
            sha256=hashlib.sha256(replacement).hexdigest(),
            byte_count=len(replacement),
        )
        result.finalization_path.write_bytes(finalizer._json_bytes(manifest))
        with self.assertRaises(finalizer.FinalizationError):
            self._revalidate(result)

    def test_revalidation_rejects_content_addressed_sidecar_substitution(self) -> None:
        result = self.finalize()
        manifest = json.loads(result.finalization_path.read_text(encoding="utf-8"))
        hashes_ref = manifest["checker_owned"]["proof_sidecars"][2]
        hashes_path = ROOT / hashes_ref["path"]
        hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
        hashes["artifacts"]["output"] = "0" * 64
        replacement = finalizer._sorted_json_bytes(hashes)
        hashes_path.write_bytes(replacement)
        hashes_ref.update(
            sha256=hashlib.sha256(replacement).hexdigest(),
            byte_count=len(replacement),
        )
        result.finalization_path.write_bytes(finalizer._json_bytes(manifest))
        with self.assertRaises(finalizer.FinalizationError):
            self._revalidate(result)

    def test_revalidation_rejects_duplicate_finalization_key(self) -> None:
        result = self.finalize()
        raw = result.finalization_path.read_bytes()
        duplicate = raw.replace(b'{\n  "schema":', b'{\n  "schema": "duplicate",\n  "schema":', 1)
        self.assertNotEqual(raw, duplicate)
        result.finalization_path.write_bytes(duplicate)
        with self.assertRaisesRegex(finalizer.FinalizationError, "duplicate JSON key"):
            self._revalidate(result)

    def test_rejects_input_binding_drift_before_creating_run_root(self) -> None:
        self.assert_rejected("input-binding", raw_input=canonical_input_bytes() + b"x")
        self.assertFalse(self.run_root.exists())

    def test_rejects_existing_or_escaping_run_root(self) -> None:
        self.run_root.mkdir(parents=True)
        self.assert_rejected("run-root-exists")
        remove_tree(self.run_root)
        self.assert_rejected("run-root-custody", run_root=Path("..") / "escape")

    def test_rejects_noncomplete_or_nonpassing_capture(self) -> None:
        payload = valid_payload()
        payload["stage_records"][1]["status"] = "held"
        payload["stage_records"][6]["closure_claim"] = "hold"
        self.assert_rejected("nonpassing-capture", raw_envelope=encode_envelope(payload))

    def test_output_mutation_during_private_validation_fails_closed(self) -> None:
        def mutate_output(*, output_path, **_kwargs):
            output_path.write_bytes(output_path.read_bytes() + b"mutation")
            return ({"visible_governed_output": "pass"}, {}, {})

        with mock.patch.object(finalizer, "_run_private_release_validation", side_effect=mutate_output):
            self.assert_rejected("output-drift")

    def test_capsule_validation_failure_is_fatal(self) -> None:
        with mock.patch.object(finalizer.stage_runner, "build_state_capsule", return_value={}):
            self.assert_rejected("capsule-validation")

    def test_release_validator_and_sidecar_failures_are_fatal(self) -> None:
        validator_failure = finalizer.FinalizationError("release-validation", "injected")
        with mock.patch.object(finalizer, "_run_private_release_validation", side_effect=validator_failure):
            self.assert_rejected("release-validation")
        remove_tree(self.run_root)
        sidecar_failure = finalizer.FinalizationError("sidecar-validation", "injected")
        with mock.patch.object(finalizer, "_build_checked_sidecars", side_effect=sidecar_failure):
            self.assert_rejected("sidecar-validation")


if __name__ == "__main__":
    unittest.main()
