#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

try:
    import witness_artifact_roles as roles
    import check_field_witness_binding as binding
    import build_field_witness_envelope as builder
    import check_field_witness_convergence as convergence
    from closure_witness_lib import terminal_public_order_diagnostics
except (ImportError, AttributeError) as exc:  # expected RED before implementation
    print(f"witness-artifact-roles contract RED: missing implementation surface: {exc}")
    raise SystemExit(1)


class WitnessArtifactRoleContractTests(unittest.TestCase):
    def test_one_canonical_owner_per_role(self) -> None:
        self.assertEqual(roles.schema_path_for_role("public_graph"), ROOT / "schema" / "field-witness.schema.json")
        self.assertEqual(roles.schema_path_for_role("audit_envelope"), ROOT / "schema" / "field-witness-envelope.schema.json")
        self.assertEqual(roles.discriminator_for_role("artifact_binding"), "field-witness-artifact-binding-v1")

    def test_exact_inline_order_passes(self) -> None:
        text = (Path(__file__).parent / "valid" / "exact-inline-order.md").read_text(encoding="utf-8")
        self.assertEqual(terminal_public_order_diagnostics(text), [])

    def test_every_invalid_matches_same_stem_expectation(self) -> None:
        errors, counts = binding.run_fixture_suite(Path(__file__).parent)
        self.assertEqual(errors, [], "\n".join(errors))
        self.assertGreaterEqual(counts["invalid"], 9)
        self.assertGreaterEqual(counts["historical_envelopes"], 1)
        for expectation_path in (Path(__file__).parent / "invalid").glob("*.expectation.json"):
            expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
            self.assertEqual(expectation_path.name, Path(expectation["fixture"]).stem + ".expectation.json")

    def test_builder_uses_subordinate_binding_role(self) -> None:
        directory = Path(__file__).parent / "valid" / "current-triplet"
        graph = json.loads((directory / "public-graph.json").read_text(encoding="utf-8"))
        envelope = json.loads((directory / "audit-envelope.json").read_text(encoding="utf-8"))
        expected_binding = json.loads((directory / "artifact-binding.json").read_text(encoding="utf-8"))
        projection = dict(envelope)
        projection.pop("artifact_binding")
        actual = builder.build_artifact_binding(
            graph,
            projection,
            source_commit=expected_binding["source_commit"],
            output_sha256=expected_binding["output_sha256"],
            stage04_projection_sha256=expected_binding["stage04_projection_sha256"],
            stage06_projection_sha256=expected_binding["stage06_projection_sha256"],
            stage07_projection_sha256=expected_binding["stage07_projection_sha256"],
            act_rows_hash=expected_binding["act_rows_hash"],
            nar_hash=expected_binding["nar_hash"],
            owner_activation_ordering_hash=expected_binding["owner_activation_ordering_hash"],
            binding_status="current_bound",
        )
        self.assertEqual(actual, expected_binding)
        self.assertEqual(builder.attach_artifact_binding(projection, actual), envelope)

    def test_convergence_dispatches_current_and_historical_explicitly(self) -> None:
        directory = Path(__file__).parent / "valid"
        current = json.loads((directory / "current-triplet" / "public-graph.json").read_text(encoding="utf-8"))
        historical = json.loads((directory / "historical-compatibility" / "legacy-public-graph.json").read_text(encoding="utf-8"))
        self.assertEqual(convergence.public_graph_contract_diagnostics(current, compatibility="current"), [])
        self.assertEqual(convergence.public_graph_contract_diagnostics(historical, compatibility="historical"), [])
        self.assertTrue(convergence.public_graph_contract_diagnostics(historical, compatibility="current"))


if __name__ == "__main__":
    unittest.main()
