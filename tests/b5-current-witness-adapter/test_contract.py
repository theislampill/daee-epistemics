#!/usr/bin/env python3
"""Permanent no-model canaries for the current B.5 witness adapter."""
from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_b5_full_ir_projection_sidecar as builder
import check_nla_decode_semantic_faithfulness as nla_decode
from stage_projection_contract import canonical_json_sha256


def _load_finalizer_fixture_module():
    path = ROOT / "tests" / "single-call-stage-finalization" / "test_contract.py"
    spec = importlib.util.spec_from_file_location("single_call_finalizer_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load finalizer fixture module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FINALIZER_FIXTURE = _load_finalizer_fixture_module()
REQUIRED_STAGE_IDS = (
    "stage-02-layer-a-diagnostic-ir",
    "stage-04-burden-execution-act",
    "stage-05-mrp-reread-terminal-state",
    "stage-06-field-witness-nar",
)
PASSING_CERTIFICATE = {
    "collapse_positive": True,
    "coverage_complete": True,
    "diagnostic_completeness": True,
}


def current_fixture() -> tuple[dict, list, list[dict]]:
    output = FINALIZER_FIXTURE.current_output_bytes().decode("utf-8", errors="strict")
    path = ROOT / ".daee" / "b5-current-adapter-fixture.md"
    witness, witness_errors = nla_decode.parse_field_witness(path, output)
    if witness_errors or witness is None:
        raise AssertionError(witness_errors)
    records, record_errors = nla_decode.parse_act_records(nla_decode.public_execution_text(output))
    if record_errors or not records:
        raise AssertionError(record_errors)
    all_stages = FINALIZER_FIXTURE.canonical_stage_records()
    carriers = [
        copy.deepcopy(next(stage for stage in all_stages if stage.get("id") == stage_id))
        for stage_id in REQUIRED_STAGE_IDS
    ]
    return copy.deepcopy(witness), records, carriers


class CurrentB5WitnessAdapterContract(unittest.TestCase):
    def build(self, *, witness=None, records=None, carriers=None):
        fixture_witness, fixture_records, fixture_carriers = current_fixture()
        return builder.build_current_projection(
            fixture_witness if witness is None else witness,
            fixture_records if records is None else records,
            fixture_carriers if carriers is None else carriers,
            PASSING_CERTIFICATE,
        )

    def assert_rejected(self, expected: str, *, witness=None, carriers=None) -> None:
        projection, errors = self.build(witness=witness, carriers=carriers)
        self.assertIsNone(projection)
        self.assertTrue(
            any(expected in error for error in errors),
            f"expected {expected!r} in {errors!r}",
        )

    def test_real_current_compiled_a9_shape_builds_explicit_bound_adapter(self) -> None:
        witness, _records, carriers = current_fixture()
        projection, errors = self.build(witness=witness, carriers=carriers)
        self.assertEqual(errors, [])
        self.assertIsNotNone(projection)
        assert projection is not None
        adapter = projection["current_adapter"]
        self.assertEqual(adapter["schema"], "b5-current-public-field-witness-adapter-v1")
        self.assertEqual(adapter["public_field_witness_sha256"], canonical_json_sha256(witness))
        self.assertEqual(
            adapter["stage_carrier_sha256"],
            {stage["id"]: canonical_json_sha256(stage) for stage in carriers},
        )
        self.assertEqual(
            projection["diagnostic_completeness"]["schema"],
            "b5-current-checker-diagnostic-evidence-v1",
        )
        self.assertEqual(projection["proof_mode"]["mode"], "checker-owned-sidecar")
        self.assertEqual(
            [row["body_ref"] for row in projection["decoded_ir"]["per_burden"]],
            ["B1_1", "B1_2"],
        )
        self.assertNotIn("diagnostic_completeness", witness["coverage_proof"])

    def test_missing_duplicate_mixed_and_ambiguous_carriers_fail_closed(self) -> None:
        witness, _records, carriers = current_fixture()

        missing = [stage for stage in carriers if stage["id"] != REQUIRED_STAGE_IDS[0]]
        self.assert_rejected("missing required Stage02/04/05/06 carrier", carriers=missing)

        duplicate = copy.deepcopy(carriers)
        duplicate.append(copy.deepcopy(duplicate[1]))
        self.assert_rejected("duplicate Stage02/04/05/06 carrier", carriers=duplicate)

        mixed = copy.deepcopy(carriers)
        mixed[3]["normalized_activation_record_details"] = copy.deepcopy(
            witness["normalized_activation_record"]
        )
        self.assert_rejected("mixed current-public NAR used as rich Stage06 carrier", carriers=mixed)

        ambiguous_witness = copy.deepcopy(witness)
        ambiguous_witness["normalized_activation_record"]["per_burden"][0][
            "activation_ordinals"
        ] = [0, 0]
        self.assert_rejected("activation ordinals must partition", witness=ambiguous_witness)

    def test_current_carrier_identity_and_state_drift_fail_closed(self) -> None:
        witness, _records, carriers = current_fixture()

        mutations = (
            ("body_ref", lambda rows: rows[1]["act_row_details"][0].__setitem__("body_ref", "¹B₉")),
            ("burden_id", lambda rows: rows[1]["act_row_details"][0].__setitem__("burden_id", "B9")),
            ("owner_id", lambda rows: rows[1]["act_row_details"][0].__setitem__("owner_id", "M8")),
            ("operation", lambda rows: rows[1]["act_row_details"][0].__setitem__("operation", "consequence-trace")),
            ("delta_result", lambda rows: rows[1]["act_row_details"][0].__setitem__("delta_result", "drifted")),
            ("terminal_state", lambda rows: rows[2]["terminal_states"].__setitem__("B1", "hold_partial")),
            (
                "generation_depth",
                lambda rows: rows[3]["normalized_activation_record_details"]["per_burden"][0].__setitem__(
                    "generation_depth", 9
                ),
            ),
        )
        for expected, mutate in mutations:
            with self.subTest(expected=expected):
                drifted = copy.deepcopy(carriers)
                mutate(drifted)
                self.assert_rejected(expected, carriers=drifted)


if __name__ == "__main__":
    unittest.main()
