#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_field_witness_convergence as convergence
import check_formal_reread_state_semantics as formal_reread
import check_graph_completeness as graph_completeness
import check_live_default_witness_contract as live_default
import check_manual_smoke_render_contract as manual_smoke
import check_mrp_generated_burden as mrp_generated
import check_nla_decode_semantic_faithfulness as nla
import check_owner_activation_ordering as owner_ordering
import build_staged_governed_output as assembly
import run_staged_current_skill_smoke as runner
import staged_current_witness as current_witness
from closure_witness_lib import (
    extract_embedded_field_witness,
    extract_field_witness,
    public_graph_integrity_diagnostics,
)
from witness_artifact_roles import validate_role


FIXTURE = Path(__file__).parent / "valid" / "minimal-stages.json"
HISTORICAL = ROOT / "tests" / "witness-artifact-roles" / "valid" / "historical-compatibility" / "legacy-public-graph.json"
RETAINED_REPLAY = ROOT / "tests" / "staged-runtime-handshake" / "valid" / "retained-a9-science-source.json"
CURRENT_TRIPLET = ROOT / "tests" / "witness-artifact-roles" / "valid" / "current-triplet" / "public-graph.json"


class StagedCurrentWitnessRoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stages = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def scaffold(self, stages: list[dict] | None = None) -> str:
        return runner.stage07_field_witness_section_scaffold(stages or self.stages)

    def graph(self, stages: list[dict] | None = None) -> dict:
        payload = extract_embedded_field_witness(self.scaffold(stages))
        graph = extract_field_witness(payload)
        self.assertIsInstance(graph, dict)
        return graph

    def current_output(self, stages: list[dict] | None = None) -> str:
        return (
            "## Layer A Compact DSL / Diagnostic IR\n"
            "Initial burden set: [¹B]\n"
            "Restorative Response\n"
            "The bounded criterion is restored.\n"
            "Closing Formulation\n"
            "The bounded formulation closes before the proof tail.\n"
            + self.scaffold(stages)
        )

    def live_default_output(self, stages: list[dict] | None = None) -> str:
        return (
            "NOETIC FIELD EXECUTION\n"
            "field: BOUNDED NOETIC FIELD\n"
            "user task: RESPOND\n"
            "external source request: NONE EXPLICIT\n"
            "authority frame: LIVE\n"
            "state: COMPLETE\n\n"
            "Layer A / DSL/IR\n"
            "- Initial burden set: [¹B]\n"
            "- ∇ route: ¹B executes under the selected definition anchor.\n"
            "- Field diagnostics: ∇·B: neutral; ∇×κ: null\n"
            "- LoopBreak: not needed\n"
            "- R(H,Δ): held set empty; no live remainder; next pass COMPLETE.\n\n"
            "Restorative Response\n"
            "The bounded criterion is restored.\n\n"
            "Closing Formulation\n"
            "The bounded formulation closes before the proof tail.\n\n"
            + self.scaffold(stages)
        )

    def held_edge_stages(self) -> list[dict]:
        stages = copy.deepcopy(self.stages)
        stages[0]["burden_floor"] = ["B1", "B2"]
        stages[0]["burden_floor_details"].append({"id": "B2", "label": "dependent_scope"})
        stage05 = stages[2]
        stage05["terminal_states"]["B2"] = "held-with-reason"
        stage05["dependency_graph_edges"] = [
            {"source": "B1", "target": "B2", "type": "held_burden_activation"}
        ]
        stage05["no_new_resultant_proof"] = {
            "proved": False,
            "unresolved_burdens": ["B2"],
        }
        stage05["per_burden_reread"] = [
            assembly.self_test_per_burden_entry("B1", next_burden_id="B2"),
            runner.self_test_reread_hold_entry("B2"),
        ]
        return stages

    def retained_projected_output(self) -> str:
        retained = json.loads(RETAINED_REPLAY.read_text(encoding="utf-8"))
        stages = retained["stages"]
        stage07 = next(row for row in stages if row["id"] == "stage-07-release-output")
        source = (ROOT / stage07["release_output"]["path"]).read_text(
            encoding="utf-8", errors="replace"
        )
        return "".join(
            runner.stage07_mrp_reread_section_scaffold(stages)
            if role == "mrp_reread_terminal"
            else runner.stage07_field_witness_section_scaffold(stages)
            if role == "field_witness_nar"
            else text
            for _section_id, role, text in runner.split_text_for_compiled_self_test(source)
        )

    def replace_final_field_witness(self, text: str, graph: dict) -> str:
        prefix, marker, _payload = text.rpartition("\nfield_witness\n")
        self.assertTrue(marker)
        return prefix + marker + json.dumps(graph, ensure_ascii=False, indent=2) + "\n"

    def test_new_stage07_output_is_current_public_graph(self) -> None:
        graph = self.graph()
        self.assertEqual(validate_role(graph, "public_graph", "current"), [])
        self.assertEqual(
            convergence.public_graph_contract_diagnostics(graph, compatibility="current"),
            [],
        )
        self.assertEqual(
            convergence.convergence_errors(
                Path("staged-current-witness-role.md"),
                self.current_output(),
                compatibility="current",
            ),
            [],
        )

    def test_current_projection_is_derived_from_stage04_and_stage05(self) -> None:
        graph = self.graph()
        self.assertEqual(graph["schema_version"], "public-field-witness-v1")
        self.assertEqual(
            [(row["body_ref"], row["burden_id"], row["owner_id"], row["operation"]) for row in graph["owner_activations"]],
            [("¹B₁", "B1", "M7", "definition-anchor")],
        )
        self.assertEqual(graph["terminal_states"]["B1"]["state"], "landed")
        self.assertEqual(graph["normalized_activation_record"]["per_burden"][0]["activation_ordinals"], [0])

    def test_b_la_dependency_is_not_misclassified_as_generated_burden(self) -> None:
        stages = self.held_edge_stages()

        graph = self.graph(stages)
        self.assertEqual(graph["B_LA"], ["B1", "B2"])
        self.assertEqual(graph["B_MRP"], [])
        self.assertEqual(graph["generated_burdens"], [])
        self.assertEqual(validate_role(graph, "public_graph", "current"), [])
        self.assertEqual(public_graph_integrity_diagnostics(graph, compatibility="current"), [])
        self.assertEqual(
            convergence.public_graph_contract_diagnostics(graph, compatibility="current"),
            [],
        )
        self.assertEqual(
            next(node for node in graph["nodes"] if node["id"] == "B2")["parent_id"],
            "B1",
        )
        self.assertEqual(graph_completeness.graph_edges(graph), ["B1->B2"])
        self.assertEqual(graph_completeness.resultant_edges(graph), ["B1->B2"])
        self.assertEqual(
            formal_reread.resultants_by_source(graph)["B1"]["target"],
            "B2",
        )
        rows = graph_completeness.condition_rows(
            Path("current-held-b-la-positive.md"),
            self.current_output(stages),
            graph,
        )
        self.assertTrue(rows["graph_structure"]["pass"], rows)

    def test_current_held_projection_preserves_stage05_route(self) -> None:
        stages = self.held_edge_stages()

        graph = self.graph(stages)
        self.assertEqual(graph["mrp_resultants"][0]["route"], "RECURSE")
        self.assertEqual(
            formal_reread.state_semantics_errors(
                Path("current-held-stage05-route.md"),
                graph,
            ),
            [],
        )

    def test_current_generated_triplet_is_positive_and_event_bound(self) -> None:
        graph = json.loads(CURRENT_TRIPLET.read_text(encoding="utf-8"))
        self.assertEqual(validate_role(graph, "public_graph", "current"), [])
        self.assertEqual(public_graph_integrity_diagnostics(graph, compatibility="current"), [])
        self.assertEqual(
            convergence.public_graph_contract_diagnostics(graph, compatibility="current"),
            [],
        )

        drifted = copy.deepcopy(graph)
        drifted["generated_burdens"][0]["event_id"] = drifted["coverage_proof"][
            "provenance_event_dag"
        ]["nodes"][0]
        diagnostics = public_graph_integrity_diagnostics(
            drifted,
            compatibility="current",
        )
        self.assertTrue(
            diagnostics
            and diagnostics[0]["failure_subcode"] == "witness-graph-generated-event",
            diagnostics,
        )

    def test_current_generated_projection_is_positive_and_source_bound(self) -> None:
        stages = copy.deepcopy(self.stages)
        stage05 = stages[2]
        stage05["terminal_states"]["B2"] = "held-with-reason"
        stage05["generated_burdens"] = [
            {
                "id": "B2",
                "generated_by": "MRP(B1)",
                "generation_depth": 1,
                "terminal_state": "held-with-reason",
            }
        ]
        stage05["dependency_graph_edges"] = [
            {"source": "B1", "target": "B2", "type": "generated_burden_instantiation"}
        ]
        stage05["no_new_resultant_proof"] = {
            "proved": False,
            "unresolved_burdens": ["B2"],
        }
        b1_reread = stage05["per_burden_reread"][0]
        b1_reread.update(
            {
                "target": "B1 generated source",
                "pressure_activations": {
                    key: "cleared after bounded reread"
                    for key in assembly.PER_BURDEN_PRESSURE_KEY_ORDER
                },
                "finding": "genuine-dependent",
                "route_result_type": "generated_burden_instantiation",
                "mrp_resultant": "B2 generated",
                "graph_delta": "B1->B2",
                "route": "RECURSE",
            }
        )
        b2_reread = copy.deepcopy(b1_reread)
        b2_reread.update(
            {
                "burden_id": "B2",
                "route_result_type": "no_new_resultant",
                "mrp_resultant": "stable -> no new graph edge; STOP",
                "graph_delta": "none",
                "route": "STOP",
            }
        )
        stage05["per_burden_reread"].append(b2_reread)

        graph = self.graph(stages)
        self.assertEqual(graph["B_MRP"], ["B2"])
        generated = graph["generated_burdens"][0]
        generated_node = next(node for node in graph["nodes"] if node["id"] == "B2")
        self.assertEqual(generated["source"], "B1")
        self.assertEqual(generated_node["parent_id"], "B1")
        self.assertEqual(generated["generation_depth"], 1)
        self.assertEqual(generated_node["generation_depth"], 1)
        self.assertEqual(graph["mrp_resultants"][0]["type"], "generated_burden_instantiation")
        self.assertIn(
            generated["event_id"],
            graph["coverage_proof"]["provenance_event_dag"]["nodes"],
        )
        self.assertEqual(validate_role(graph, "public_graph", "current"), [])
        self.assertEqual(public_graph_integrity_diagnostics(graph, compatibility="current"), [])
        self.assertEqual(
            convergence.public_graph_contract_diagnostics(graph, compatibility="current"),
            [],
        )

    def test_current_generated_fanout_preserves_pair_identity(self) -> None:
        stages = copy.deepcopy(self.stages)
        stage05 = stages[2]
        stage05["terminal_states"].update(
            {"B2": "held-with-reason", "B3": "held-with-reason"}
        )
        stage05["generated_burdens"] = [
            {
                "id": burden,
                "generated_by": "MRP(B1)",
                "generation_depth": 1,
                "terminal_state": "held-with-reason",
            }
            for burden in ("B2", "B3")
        ]
        stage05["dependency_graph_edges"] = [
            {"source": "B1", "target": burden, "type": "generated_burden_instantiation"}
            for burden in ("B2", "B3")
        ]
        stage05["no_new_resultant_proof"] = {
            "proved": False,
            "unresolved_burdens": ["B2", "B3"],
        }
        b1_reread = stage05["per_burden_reread"][0]
        b1_reread.update(
            {
                "target": "B1 fanout source",
                "pressure_activations": {
                    key: "cleared after bounded reread"
                    for key in assembly.PER_BURDEN_PRESSURE_KEY_ORDER
                },
                "finding": "genuine-dependent",
                "route_result_type": "generated_burden_instantiation",
                "mrp_resultant": "B2 and B3 generated",
                "graph_delta": "B1->B2; B1->B3",
                "route": "RECURSE",
                "route_gradient": "generated new B2 and B3 absent from B_LA",
            }
        )
        for burden in ("B2", "B3"):
            reread = copy.deepcopy(b1_reread)
            reread.update(
                {
                    "burden_id": burden,
                    "target": f"{burden} generated burden",
                    "finding": "stable",
                    "route_result_type": "no_new_resultant",
                    "mrp_resultant": "stable -> no new graph edge; STOP",
                    "graph_delta": "none",
                    "route": "STOP",
                    "route_gradient": "held partial STOP",
                }
            )
            stage05["per_burden_reread"].append(reread)

        graph = self.graph(stages)
        self.assertEqual(
            [(row["source"], row["target"]) for row in graph["mrp_resultants"]],
            [("B1", "B2"), ("B1", "B3")],
        )
        self.assertEqual(validate_role(graph, "public_graph", "current"), [])
        self.assertEqual(public_graph_integrity_diagnostics(graph, compatibility="current"), [])
        self.assertEqual(
            formal_reread.state_semantics_errors(
                Path("current-generated-fanout.md"),
                graph,
            ),
            [],
        )
        text = (
            "\n\n".join(
                assembly.render_mrp_block(entry)
                for entry in stage05["per_burden_reread"]
            )
            + "\n\nfield_witness\n"
            + json.dumps(graph, ensure_ascii=False, indent=2)
            + "\n"
        )
        blocks = mrp_generated.parse_mrps(text)
        self.assertTrue(blocks)
        self.assertEqual(
            mrp_generated.field_witness_mrp_resultant_errors(
                Path("current-generated-fanout.md"),
                text,
                blocks,
            ),
            [],
        )
        convergence_errors = convergence.convergence_errors(
            Path("current-generated-fanout.md"),
            text,
            compatibility="current",
        )
        self.assertFalse(
            any("mrp_resultants source/target identities" in error for error in convergence_errors),
            convergence_errors,
        )

        ambiguous = copy.deepcopy(graph)
        ambiguous["edges"].append(
            {
                "from": "B2",
                "to": "B3",
                "relation_class": "noetic_dependency",
                "kind": "generated_burden_instantiation",
            }
        )
        ambiguous["coverage_proof"]["dependency_graph"]["edges"].append(
            {"from": "B2", "to": "B3"}
        )
        diagnostics = public_graph_integrity_diagnostics(
            ambiguous,
            compatibility="current",
        )
        self.assertTrue(
            diagnostics
            and diagnostics[0]["failure_subcode"]
            == "witness-graph-node-parent-ambiguous",
            diagnostics,
        )

    def test_stage06_owner_drift_fails_closed(self) -> None:
        drifted = copy.deepcopy(self.stages)
        drifted[-1]["normalized_activation_record"]["per_burden"][0]["owner_id"] = "different-owner"
        with self.assertRaises(runner.HarnessError):
            self.graph(drifted)

    def test_current_projection_rejects_generated_burden_with_multiple_sources(self) -> None:
        stages = copy.deepcopy(self.stages)
        stages[0]["burden_floor"] = ["B1", "B2"]
        stages[0]["burden_floor_details"].append({"id": "B2", "label": "second_source"})
        stages[2]["terminal_states"].update(
            {"B2": "landed", "B3": "held-with-reason"}
        )
        stages[2]["generated_burdens"] = [
            {
                "id": "B3",
                "generated_by": "MRP(B1)",
                "generation_depth": 1,
                "terminal_state": "held-with-reason",
            }
        ]
        stages[2]["dependency_graph_edges"] = [
            {"source": "B1", "target": "B3", "type": "generated_burden_instantiation"},
            {"source": "B2", "target": "B3", "type": "generated_burden_instantiation"},
        ]
        for burden in ("B2", "B3"):
            reread = copy.deepcopy(stages[2]["per_burden_reread"][0])
            reread["burden_id"] = burden
            stages[2]["per_burden_reread"].append(reread)
        with self.assertRaisesRegex(
            runner.HarnessError,
            "exactly one incoming generated-burden edge",
        ):
            runner.stage07_current_projection(stages)

    def test_current_projection_rejects_generated_source_declaration_drift(self) -> None:
        stages = copy.deepcopy(self.stages)
        stages[0]["burden_floor"] = ["B1", "B2"]
        stages[0]["burden_floor_details"].append({"id": "B2", "label": "edge_source"})
        stages[2]["terminal_states"].update(
            {"B2": "landed", "B3": "held-with-reason"}
        )
        stages[2]["generated_burdens"] = [
            {
                "id": "B3",
                "generated_by": "MRP(B1)",
                "generation_depth": 1,
                "terminal_state": "held-with-reason",
            }
        ]
        stages[2]["dependency_graph_edges"] = [
            {"source": "B2", "target": "B3", "type": "generated_burden_instantiation"}
        ]
        for burden in ("B2", "B3"):
            reread = copy.deepcopy(stages[2]["per_burden_reread"][0])
            reread["burden_id"] = burden
            stages[2]["per_burden_reread"].append(reread)
        with self.assertRaisesRegex(
            runner.HarnessError,
            "declared source B1 does not match unique incoming source B2",
        ):
            runner.stage07_current_projection(stages)

    def test_current_projection_rejects_unsupported_multi_parent_b_la(self) -> None:
        stages = copy.deepcopy(self.stages)
        stages[0]["burden_floor"] = ["B1", "B2", "B3"]
        stages[0]["burden_floor_details"].extend(
            [
                {"id": "B2", "label": "second_source"},
                {"id": "B3", "label": "fan_in_target"},
            ]
        )
        stages[2]["terminal_states"].update({"B2": "landed", "B3": "landed"})
        stages[2]["dependency_graph_edges"] = [
            {"source": "B1", "target": "B3", "type": "held_burden_activation"},
            {"source": "B2", "target": "B3", "type": "held_burden_activation"},
        ]
        for burden in ("B2", "B3"):
            reread = copy.deepcopy(stages[2]["per_burden_reread"][0])
            reread["burden_id"] = burden
            stages[2]["per_burden_reread"].append(reread)
        with self.assertRaisesRegex(
            runner.HarnessError,
            "at most one incoming dependency edge while parent_id is singular",
        ):
            runner.stage07_current_projection(stages)

    def test_current_projection_rejects_generated_burden_edge_kind_drift(self) -> None:
        stages = copy.deepcopy(self.stages)
        stages[2]["terminal_states"]["B2"] = "held-with-reason"
        stages[2]["generated_burdens"] = [
            {
                "id": "B2",
                "generated_by": "MRP(B1)",
                "generation_depth": 1,
                "terminal_state": "held-with-reason",
            }
        ]
        stages[2]["dependency_graph_edges"] = [
            {"source": "B1", "target": "B2", "type": "generated_burden_instantiation"}
        ]
        b2_reread = copy.deepcopy(stages[2]["per_burden_reread"][0])
        b2_reread["burden_id"] = "B2"
        stages[2]["per_burden_reread"].append(b2_reread)
        historical = runner.stage07_historical_field_witness_payload(stages)
        historical["edges"][0]["type"] = "held_burden_activation"
        stage04 = runner.stage_by_id(stages, "stage-04-burden-execution-act")
        stage05 = runner.stage_by_id(stages, "stage-05-mrp-reread-terminal-state")
        stage06 = runner.stage_by_id(stages, "stage-06-field-witness-nar")
        with self.assertRaisesRegex(
            current_witness.CurrentWitnessError,
            "incoming edge must be generated_burden_instantiation",
        ):
            current_witness.build_current_projection(
                historical=historical,
                stage04=stage04,
                stage05=stage05,
                stage06=stage06,
                act_details=runner.stage04_act_details_by_ref(stage04),
                entries=runner.stage05_per_burden_entries(stage05),
                field_witness_body_refs=runner.list_field(stage06, "field_witness_body_refs"),
                owner_activation_refs=runner.list_field(stage06, "owner_activations"),
                owner_details=runner.stage06_owner_activation_details_by_ref(stage06),
            )

    def test_current_fingerprint_changes_with_source_delta(self) -> None:
        baseline = self.graph()["activation_lifecycle_fingerprint_sha256"]
        changed = copy.deepcopy(self.stages)
        changed[1]["act_rows"][0] = changed[1]["act_rows"][0].replace(
            "definition-anchored", "definition-scope-bounded"
        )
        changed[-1]["normalized_activation_record"]["per_burden"][0]["delta_result"] = "definition-scope-bounded"
        self.assertNotEqual(
            baseline,
            self.graph(changed)["activation_lifecycle_fingerprint_sha256"],
        )

    def test_live_default_consistency_uses_current_contract(self) -> None:
        errors: list[str] = []
        live_default.check_field_witness_consistency(
            Path("staged-current-witness-role.md"), self.current_output(), errors
        )
        self.assertEqual(errors, [])

    def test_full_live_default_checker_uses_current_public_graph_fixture(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-current-live-default-") as tmp:
            path = Path(tmp) / "staged-current-witness-role.md"
            path.write_text(self.live_default_output(), encoding="utf-8")
            self.assertEqual(live_default.check(path), [])

    def test_retained_replay_details_project_to_current_public_graph(self) -> None:
        retained = json.loads(RETAINED_REPLAY.read_text(encoding="utf-8"))
        graph = self.graph(retained["stages"])
        self.assertEqual(graph["schema_version"], "public-field-witness-v1")
        self.assertEqual(validate_role(graph, "public_graph", "current"), [])
        self.assertEqual(
            [row["body_ref"] for row in graph["owner_activations"]],
            ["¹B₁", "¹B₂"],
        )

    def test_retained_compiled_projection_converges_as_current(self) -> None:
        self.assertEqual(
            convergence.convergence_errors(
                Path("retained-compiled-current.md"),
                self.retained_projected_output(),
                compatibility="current",
            ),
            [],
        )

    def test_retained_compiled_projection_passes_current_nla_join(self) -> None:
        self.assertEqual(
            nla.nla_decode_errors(
                Path("retained-compiled-current.md"), self.retained_projected_output()
            ),
            [],
        )

    def test_retained_compiled_projection_passes_current_formal_reread_join(self) -> None:
        self.assertEqual(
            formal_reread.formal_semantics_errors(
                Path("retained-compiled-current.md"), self.retained_projected_output()
            ),
            [],
        )

    def test_retained_compiled_projection_passes_current_mrp_resultant_join(self) -> None:
        retained = json.loads(RETAINED_REPLAY.read_text(encoding="utf-8"))
        stage07 = next(
            row for row in retained["stages"] if row["id"] == "stage-07-release-output"
        )
        source = (ROOT / stage07["release_output"]["path"]).read_text(
            encoding="utf-8", errors="replace"
        )
        blocks = mrp_generated.parse_mrps(source)
        self.assertTrue(blocks)
        self.assertEqual(
            mrp_generated.field_witness_mrp_resultant_errors(
                Path("retained-compiled-current.md"),
                self.retained_projected_output(),
                blocks,
            ),
            [],
        )

    def test_current_mrp_resultant_join_rejects_reread_and_edge_split_drift(self) -> None:
        retained = json.loads(RETAINED_REPLAY.read_text(encoding="utf-8"))
        stage07 = next(
            row for row in retained["stages"] if row["id"] == "stage-07-release-output"
        )
        source = (ROOT / stage07["release_output"]["path"]).read_text(
            encoding="utf-8", errors="replace"
        )
        blocks = mrp_generated.parse_mrps(source)
        projected = self.retained_projected_output()
        baseline = extract_field_witness(extract_embedded_field_witness(projected))
        self.assertTrue(blocks)
        self.assertIsInstance(baseline, dict)

        route_drift = copy.deepcopy(baseline)
        route_drift["reread_records"][0]["route_result_type"] = "hold_partial"
        route_errors = mrp_generated.field_witness_mrp_resultant_errors(
            Path("retained-compiled-current-route-drift.md"),
            self.replace_final_field_witness(projected, route_drift),
            blocks,
        )
        self.assertTrue(any("reread_records[B1] route_result_type" in error for error in route_errors))

        extra_resultant = copy.deepcopy(baseline)
        extra_resultant["mrp_resultants"].append(
            {
                "source": "B1",
                "target": "B1",
                "type": "no_new_resultant",
                "route": "STOP",
            }
        )
        resultant_errors = mrp_generated.field_witness_mrp_resultant_errors(
            Path("retained-compiled-current-resultant-drift.md"),
            self.replace_final_field_witness(projected, extra_resultant),
            blocks,
        )
        self.assertTrue(
            any("names non-edge-producing sources: B1" in error for error in resultant_errors)
        )

    def test_current_formal_reread_join_rejects_record_drift(self) -> None:
        projected = self.retained_projected_output()
        graph = extract_field_witness(extract_embedded_field_witness(projected))
        self.assertIsInstance(graph, dict)
        graph["reread_records"][0]["route_result_type"] = "hold_partial"
        errors = formal_reread.formal_semantics_errors(
            Path("retained-compiled-current-reread-drift.md"),
            self.replace_final_field_witness(projected, graph),
        )
        self.assertTrue(
            any("route_result_type does not match reread_records" in error for error in errors),
            errors,
        )

    def test_current_nla_join_rejects_identity_and_source_hash_drift(self) -> None:
        projected = self.retained_projected_output()
        baseline = extract_field_witness(extract_embedded_field_witness(projected))
        self.assertIsInstance(baseline, dict)
        mutations = (
            ("owner_id", "M7", "owner_id does not decode"),
            ("semantic_body_sha256", "0" * 64, "semantic_body_sha256 does not match"),
        )
        for field, value, expected in mutations:
            with self.subTest(field=field):
                graph = copy.deepcopy(baseline)
                graph["owner_activations"][0][field] = value
                errors = nla.nla_decode_errors(
                    Path("retained-compiled-current-drift.md"),
                    self.replace_final_field_witness(projected, graph),
                )
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_assembly_does_not_apply_historical_mirror_normalization_to_current_graph(self) -> None:
        retained = json.loads(RETAINED_REPLAY.read_text(encoding="utf-8"))
        stages = retained["stages"]
        section = runner.stage07_field_witness_section_scaffold(stages)
        original = extract_field_witness(extract_embedded_field_witness(section))
        stage05 = next(row for row in stages if row["id"] == "stage-05-mrp-reread-terminal-state")
        entries = {
            row["burden_id"]: row for row in runner.stage05_per_burden_entries(stage05)
        }
        normalized, _event = assembly.normalize_section_scaffold(
            "field-witness-nar",
            "field_witness_nar",
            section,
            entry_by_burden=entries,
        )
        self.assertEqual(
            extract_field_witness(extract_embedded_field_witness(normalized)),
            original,
        )

    def test_current_owner_ordering_rejects_projection_drift(self) -> None:
        graph = self.graph()
        graph["owner_activation_ordering"]["rows"][0]["body_ref"] = "B1_drift"
        report = owner_ordering.current_activation_report(
            Path("current-owner-ordering-drift.md"),
            graph,
            [],
        )
        self.assertTrue(
            any("must exactly project activation ordinals/body_refs" in error for error in report.errors),
            report.errors,
        )

    def test_current_dependency_graph_rejects_non_burden_nodes_and_endpoints(self) -> None:
        baseline = self.graph()
        mutations = (
            ("node", lambda graph: graph["coverage_proof"]["dependency_graph"]["nodes"].append("X")),
            (
                "edge",
                lambda graph: graph["coverage_proof"]["dependency_graph"]["edges"].append(
                    {"from": "B1", "to": "X"}
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                graph = copy.deepcopy(baseline)
                mutate(graph)
                text = self.replace_final_field_witness(self.current_output(), graph)
                errors = convergence.convergence_errors(
                    Path(f"current-dependency-{label}.md"),
                    text,
                    compatibility="current",
                )
                self.assertTrue(
                    any("dependency_graph" in error for error in errors),
                    errors,
                )
                rows = graph_completeness.condition_rows(
                    Path(f"current-dependency-{label}.md"),
                    text,
                    graph,
                )
                self.assertFalse(rows["graph_structure"]["pass"], rows)

    def test_current_identity_rejects_wrong_node_origin_and_type(self) -> None:
        graph = self.graph()
        graph["nodes"][0]["origin"] = "B_MRP"
        graph["nodes"][0]["type"] = "generated_burden"
        text = self.replace_final_field_witness(self.current_output(), graph)
        errors = convergence.convergence_errors(
            Path("current-node-origin-drift.md"),
            text,
            compatibility="current",
        )
        self.assertTrue(
            any("node B1 origin/type" in error for error in errors),
            errors,
        )

    def test_current_identity_rejects_dependency_parent_drift(self) -> None:
        stages = self.held_edge_stages()

        graph = self.graph(stages)
        next(node for node in graph["nodes"] if node["id"] == "B2")["parent_id"] = "B2"
        text = self.replace_final_field_witness(self.current_output(stages), graph)
        errors = convergence.convergence_errors(
            Path("current-dependency-parent-drift.md"),
            text,
            compatibility="current",
        )
        self.assertTrue(any("dependency parent_id" in error for error in errors), errors)
        rows = graph_completeness.condition_rows(
            Path("current-dependency-parent-drift.md"),
            text,
            graph,
        )
        self.assertFalse(rows["graph_structure"]["pass"], rows)

    def test_current_identity_rejects_extra_terminal_keys(self) -> None:
        baseline = extract_field_witness(
            extract_embedded_field_witness(self.retained_projected_output())
        )
        self.assertIsInstance(baseline, dict)
        for terminal_id in ("X", "B99"):
            with self.subTest(terminal_id=terminal_id):
                graph = copy.deepcopy(baseline)
                graph["terminal_states"][terminal_id] = {
                    "state": "landed",
                    "cycle_id": "C-extra",
                }
                graph["coverage_proof"]["terminal_states"][terminal_id] = "landed"
                text = self.replace_final_field_witness(
                    self.retained_projected_output(),
                    graph,
                )
                errors = convergence.convergence_errors(
                    Path(f"current-extra-terminal-{terminal_id}.md"),
                    text,
                    compatibility="current",
                )
                self.assertTrue(
                    any("terminal identities" in error for error in errors),
                    errors,
                )
                rows = graph_completeness.condition_rows(
                    Path(f"current-extra-terminal-{terminal_id}.md"),
                    text,
                    graph,
                )
                self.assertFalse(rows["graph_structure"]["pass"], rows)

    def test_current_identity_rejects_terminal_cycle_role_drift(self) -> None:
        graph = self.graph()
        graph["terminal_states"]["B1"]["cycle_id"] = "C-drift"
        text = self.replace_final_field_witness(self.current_output(), graph)
        errors = convergence.convergence_errors(
            Path("current-terminal-cycle-role-drift.md"),
            text,
            compatibility="current",
        )
        self.assertTrue(any("terminal cycle identity" in error for error in errors), errors)
        rows = graph_completeness.condition_rows(
            Path("current-terminal-cycle-role-drift.md"),
            text,
            graph,
        )
        self.assertFalse(rows["graph_structure"]["pass"], rows)

    def test_current_identity_rejects_duplicate_dependency_edges(self) -> None:
        stages = self.held_edge_stages()

        graph = self.graph(stages)
        graph["edges"].append(copy.deepcopy(graph["edges"][0]))
        dependency_edges = graph["coverage_proof"]["dependency_graph"]["edges"]
        dependency_edges.append(copy.deepcopy(dependency_edges[0]))
        text = self.replace_final_field_witness(self.current_output(stages), graph)
        errors = convergence.convergence_errors(
            Path("current-duplicate-dependency-edge.md"),
            text,
            compatibility="current",
        )
        self.assertTrue(
            any("duplicate dependency edge" in error for error in errors),
            errors,
        )
        rows = graph_completeness.condition_rows(
            Path("current-duplicate-dependency-edge.md"),
            text,
            graph,
        )
        self.assertFalse(rows["graph_structure"]["pass"], rows)

    def test_current_identity_rejects_edge_resultant_kind_drift(self) -> None:
        stages = self.held_edge_stages()

        graph = self.graph(stages)
        graph["edges"][0]["kind"] = "generated_burden_instantiation"
        text = self.replace_final_field_witness(self.current_output(stages), graph)
        errors = convergence.convergence_errors(
            Path("current-edge-resultant-kind-drift.md"),
            text,
            compatibility="current",
        )
        self.assertTrue(any("edge kind" in error for error in errors), errors)
        rows = graph_completeness.condition_rows(
            Path("current-edge-resultant-kind-drift.md"),
            text,
            graph,
        )
        self.assertFalse(rows["graph_structure"]["pass"], rows)

    def test_current_identity_rejects_extra_provenance_event(self) -> None:
        graph = self.graph()
        event_graph = graph["coverage_proof"]["provenance_event_dag"]
        event_graph["nodes"].append("E-" + "f" * 64)
        event_graph["roots"].append("E-" + "f" * 64)
        text = self.replace_final_field_witness(self.current_output(), graph)
        errors = convergence.convergence_errors(
            Path("current-extra-provenance-event.md"),
            text,
            compatibility="current",
        )
        self.assertTrue(
            any("provenance event identities" in error for error in errors),
            errors,
        )
        rows = graph_completeness.condition_rows(
            Path("current-extra-provenance-event.md"),
            text,
            graph,
        )
        self.assertFalse(rows["graph_structure"]["pass"], rows)

    def test_current_reread_and_nar_reject_duplicate_burden_rows(self) -> None:
        projected = self.retained_projected_output()
        baseline = extract_field_witness(extract_embedded_field_witness(projected))
        self.assertIsInstance(baseline, dict)
        retained = json.loads(RETAINED_REPLAY.read_text(encoding="utf-8"))
        stage07 = next(
            row for row in retained["stages"] if row["id"] == "stage-07-release-output"
        )
        source = (ROOT / stage07["release_output"]["path"]).read_text(
            encoding="utf-8", errors="replace"
        )
        blocks = mrp_generated.parse_mrps(source)
        self.assertTrue(blocks)

        duplicate_reread = copy.deepcopy(baseline)
        duplicate_reread["reread_records"].append(
            copy.deepcopy(duplicate_reread["reread_records"][0])
        )
        reread_text = self.replace_final_field_witness(projected, duplicate_reread)
        convergence_errors = convergence.convergence_errors(
            Path("current-duplicate-reread.md"),
            reread_text,
            compatibility="current",
        )
        self.assertTrue(
            any("reread_records burden order" in error for error in convergence_errors),
            convergence_errors,
        )
        formal_errors = formal_reread.formal_semantics_errors(
            Path("current-duplicate-reread.md"),
            reread_text,
        )
        self.assertTrue(
            any("reread_records burden order" in error for error in formal_errors),
            formal_errors,
        )
        mrp_errors = mrp_generated.field_witness_mrp_resultant_errors(
            Path("current-duplicate-reread.md"),
            reread_text,
            blocks,
        )
        self.assertTrue(
            any("duplicate burden_id" in error for error in mrp_errors),
            mrp_errors,
        )

        duplicate_nar = copy.deepcopy(baseline)
        duplicate_nar["normalized_activation_record"]["per_burden"].append(
            copy.deepcopy(duplicate_nar["normalized_activation_record"]["per_burden"][0])
        )
        nar_text = self.replace_final_field_witness(projected, duplicate_nar)
        nar_errors = convergence.convergence_errors(
            Path("current-duplicate-nar.md"),
            nar_text,
            compatibility="current",
        )
        self.assertTrue(
            any("NAR burden order" in error for error in nar_errors),
            nar_errors,
        )

        edge_stages = self.held_edge_stages()
        duplicate_resultant = self.graph(edge_stages)
        duplicate_resultant["mrp_resultants"].append(
            copy.deepcopy(duplicate_resultant["mrp_resultants"][0])
        )
        resultant_text = self.replace_final_field_witness(projected, duplicate_resultant)
        resultant_convergence = convergence.convergence_errors(
            Path("current-duplicate-resultant.md"),
            resultant_text,
            compatibility="current",
        )
        self.assertTrue(
            any("mrp_resultants source/target identities" in error for error in resultant_convergence),
            resultant_convergence,
        )
        resultant_formal = formal_reread.formal_semantics_errors(
            Path("current-duplicate-resultant.md"),
            resultant_text,
        )
        self.assertTrue(
            any("mrp_resultants source/target identities" in error for error in resultant_formal),
            resultant_formal,
        )
        resultant_mrp = mrp_generated.field_witness_mrp_resultant_errors(
            Path("current-duplicate-resultant.md"),
            resultant_text,
            blocks,
        )
        self.assertTrue(
            any("duplicate source/target" in error for error in resultant_mrp),
            resultant_mrp,
        )

    def test_current_assembled_output_passes_graph_and_manual_contracts(self) -> None:
        retained = json.loads(RETAINED_REPLAY.read_text(encoding="utf-8"))
        stages = retained["stages"]
        stage05 = next(row for row in stages if row["id"] == "stage-05-mrp-reread-terminal-state")
        stage07 = next(row for row in stages if row["id"] == "stage-07-release-output")
        source_path = ROOT / stage07["release_output"]["path"]
        source = source_path.read_text(encoding="utf-8", errors="replace")
        sections = [
            (
                section_id,
                role,
                runner.stage07_mrp_reread_section_scaffold(stages)
                if role == "mrp_reread_terminal"
                else runner.stage07_field_witness_section_scaffold(stages)
                if role == "field_witness_nar"
                else text,
            )
            for section_id, role, text in runner.split_text_for_compiled_self_test(source)
        ]
        with tempfile.TemporaryDirectory(
            prefix="staged-current-graph-", dir=ROOT / ".daee" / "validation"
        ) as temp:
            manifest = assembly.manifest_for_sections(
                Path(temp),
                case_id="staged-current-graph-contract",
                source_input=source_path.relative_to(ROOT).as_posix(),
                section_specs=sections,
                per_burden_reread=runner.stage05_per_burden_entries(stage05),
            )
            record = runner.assemble_compiled_manifest(manifest, root=ROOT)
            output_path = ROOT / record["output"]["path"]
            output_text = output_path.read_text(encoding="utf-8", errors="replace")
            report, errors = graph_completeness.graph_report(output_path)
            manual_errors = manual_smoke.check_text(output_path, output_text)
            owner_ordering_errors = owner_ordering.activation_report(
                output_path,
                require_plan=True,
            ).errors
        self.assertEqual(errors, [])
        self.assertIsInstance(report, dict)
        self.assertTrue(report["graph_valid"], report)
        self.assertEqual(manual_errors, [])
        self.assertEqual(owner_ordering_errors, [])

    def test_historical_adapter_remains_explicit_and_non_current(self) -> None:
        historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
        current_diagnostics = validate_role(historical, "public_graph", "current")
        historical_diagnostics = validate_role(historical, "public_graph", "historical")
        self.assertTrue(current_diagnostics)
        self.assertTrue(
            historical_diagnostics
            and historical_diagnostics[0].failure_subcode == "witness-role-historical-public-adapter"
        )


if __name__ == "__main__":
    unittest.main()
