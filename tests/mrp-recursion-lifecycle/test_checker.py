from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent
CHECKER = ROOT / "tools" / "check_mrp_recursion_lifecycle.py"
LIBRARY = ROOT / "tools" / "mrp_recursion_lib.py"
STATE_V2_VALID = ROOT / "tests" / "state-capsule-v2" / "valid"


def run_checker(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(CHECKER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )


def canonical_self_hash(value: dict[str, object], field: str) -> str:
    body = {key: item for key, item in value.items() if key != field}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_state_v2(name: str) -> dict[str, object]:
    return json.loads((STATE_V2_VALID / name).read_text(encoding="utf-8"))


def with_stale_state_v2_signature(payload: dict[str, object]) -> dict[str, object]:
    stale = copy.deepcopy(payload)
    cycle = stale["burden_cycles"][0]
    reread = cycle["reread"]
    history_row = stale["reread_signature_history"][0]
    stale_a07_signature = "0" * 64
    capsules = {row["capsule_id"]: row for row in stale["operation_capsules"]}
    stale_reread_signature = canonical_hash({
        "a07_reducer_signature_sha256": stale_a07_signature,
        "performed_operation_capsule_sha256s": [
            capsules[value]["operation_capsule_sha256"]
            for value in cycle["operation_capsule_ids"]
        ],
        "land_record_sha256": cycle["land"]["record_sha256"],
        "land_event_sha256": cycle["land"]["event_sha256"],
        "post_land_delta_sha256": cycle["post_land_delta"]["delta_sha256"],
        "post_land_delta_event_sha256": cycle["post_land_delta"]["event_sha256"],
    })
    reread["a07_reducer_signature_sha256"] = stale_a07_signature
    reread["reread_signature_sha256"] = stale_reread_signature
    reread["record_sha256"] = canonical_self_hash(reread, "record_sha256")
    cycle["cycle_sha256"] = canonical_self_hash(cycle, "cycle_sha256")
    history_row["a07_reducer_signature_sha256"] = stale_a07_signature
    history_row["reread_signature_sha256"] = stale_reread_signature
    stale["reread_signature_history_sha256"] = canonical_hash(stale["reread_signature_history"])
    return stale


def validate_in_process(payload: dict[str, object]):
    tools = str(ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    from mrp_recursion_lib import validate_lifecycle_record

    return validate_lifecycle_record(payload)


class MrpRecursionLifecycleCheckerTests(unittest.TestCase):
    def test_fixture_suite_passes(self) -> None:
        result = run_checker()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("valid", result.stdout)
        self.assertIn("invalid", result.stdout)

    def test_every_valid_fixture_has_stable_pass_explanation(self) -> None:
        for fixture in sorted((FIXTURES / "valid").glob("*.json")):
            with self.subTest(fixture=fixture.name):
                first = run_checker("--fixture", str(fixture), "--explain")
                second = run_checker("--fixture", str(fixture), "--explain")
                self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
                self.assertEqual(first.stdout, second.stdout)
                payload = json.loads(first.stdout)
                self.assertEqual(payload["status"], "PASS")
                self.assertEqual(payload["checker_id"], "mrp-recursion-lifecycle")

    def test_every_invalid_fixture_matches_plan11_expectation(self) -> None:
        for sidecar in sorted((FIXTURES / "invalid").glob("*.expectation.json")):
            with self.subTest(sidecar=sidecar.name):
                expectation = json.loads(sidecar.read_text(encoding="utf-8"))
                fixture = sidecar.with_name(expectation["fixture"])
                result = run_checker("--fixture", str(fixture), "--explain")
                self.assertEqual(result.returncode, expectation["expected_exit_code"], result.stdout + result.stderr)
                diagnostic = json.loads(result.stdout)
                self.assertEqual(diagnostic["checker_id"], expectation["expected_checker_id"])
                self.assertEqual(diagnostic["exit_category"], expectation["expected_exit_category"])
                self.assertEqual(diagnostic["earliest_stage"], expectation["expected_earliest_stage"])
                self.assertEqual(diagnostic["failure_class"], expectation["expected_failure_class"])
                self.assertEqual(diagnostic.get("failure_subcode"), expectation.get("expected_failure_subcode"))
                self.assertEqual(diagnostic["downstream_invalidated"], expectation["expected_downstream_invalidated"])
                rendered = json.dumps(diagnostic, sort_keys=True)
                for marker in expectation["required_diagnostic_markers"]:
                    self.assertIn(marker, rendered)
                for artifact in expectation["forbidden_artifacts"]:
                    self.assertFalse((ROOT / artifact).exists(), artifact)

    def test_self_test_includes_mutation_and_unbounded_capacity_proofs(self) -> None:
        result = run_checker("--self-test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("mutation/right-reason", result.stdout)
        self.assertIn("depth=12", result.stdout)
        self.assertIn("width=21", result.stdout)

    def test_lifecycle_partitions_are_explicit_and_non_conflated(self) -> None:
        fixture = FIXTURES / "valid" / "preempted-then-activated.json"
        result = run_checker("--fixture", str(fixture), "--explain")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        partitions = json.loads(result.stdout)["lifecycle_partitions"]
        self.assertEqual(
            set(partitions),
            {"candidate", "held", "preempted", "active", "landed", "generated", "partial", "recurse", "closure_candidate", "complete"},
        )
        self.assertIn("K-pre", partitions["preempted"])
        self.assertIn("B1", partitions["active"])
        self.assertIn("B2", partitions["recurse"])
        self.assertIn("B3", partitions["closure_candidate"])
        self.assertEqual(partitions["complete"], [])

    def test_library_has_no_orchestration_imports(self) -> None:
        source = LIBRARY.read_text(encoding="utf-8")
        for forbidden in ("subprocess", "socket", "urllib", "requests", "pathlib", "open(", "os.system"):
            self.assertNotIn(forbidden, source)

    def test_historical_raw_complete_is_never_release_bearing(self) -> None:
        fixture = FIXTURES / "valid" / "historical-raw-complete-nonpromotable.json"
        compatibility = run_checker("--fixture", str(fixture), "--explain")
        self.assertEqual(compatibility.returncode, 0, compatibility.stdout + compatibility.stderr)
        compatibility_payload = json.loads(compatibility.stdout)
        self.assertEqual(compatibility_payload["validation_profile"], "historical-raw-complete-v1")
        self.assertFalse(compatibility_payload["promotion_eligible"])

        release = run_checker("--fixture", str(fixture), "--release-bearing", "--explain")
        self.assertEqual(release.returncode, 1, release.stdout + release.stderr)
        release_payload = json.loads(release.stdout)
        self.assertEqual(release_payload["failure_subcode"], "historical_non_promotable")

    def test_same_burden_changed_state_reread_is_licensed(self) -> None:
        fixture = FIXTURES / "valid" / "same-burden-changed-state-reread.json"
        result = run_checker("--fixture", str(fixture), "--explain")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        diagnostic = json.loads(result.stdout)
        self.assertEqual(diagnostic["B_LA"], ["B1"])
        self.assertEqual(diagnostic["cycle_count"], 2)
        self.assertEqual(len(diagnostic["reread_signature_history"]), 2)
        self.assertEqual(len({row[2] for row in diagnostic["reread_signature_history"]}), 2)

    def test_repeated_state_and_stale_policy_hash_fail_for_their_exact_reason(self) -> None:
        expected = {
            "repeated-signature-silently-retries.json": "repeated_state_detected",
            "resource-policy-hash-mutation.json": "resource_policy_hash_mismatch",
            "same-burden-cycle-replayed.json": "same_burden_replay",
            "state-v2-ambiguous-candidate-disposition.json": "state_v2_candidate_disposition_delta",
        }
        for name, subcode in expected.items():
            with self.subTest(name=name):
                result = run_checker("--fixture", str(FIXTURES / "invalid" / name), "--explain")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["failure_subcode"], subcode)

    def test_state_v2_adapter_preserves_raw_stop_and_generated_depth(self) -> None:
        baseline = validate_in_process(load_state_v2("composed-all-plan-fields.json"))
        self.assertTrue(baseline.valid, baseline.findings)
        self.assertEqual(baseline.terminal_disposition, "STOP")
        self.assertEqual(baseline.b_la, ("B1",))
        self.assertNotIn("COMPLETE", dict(baseline.cycle_exits).values())

        generated = validate_in_process(load_state_v2("generated-child-of-generated-parent.json"))
        self.assertTrue(generated.valid, generated.findings)
        self.assertEqual(generated.b_mrp, ("B2", "B3"))
        self.assertEqual(generated.maximum_generation_depth, 2)
        self.assertEqual(generated.event_dag_edges, (("C1", "C2"), ("C2", "C3")))

        cyclic_noetic = validate_in_process(load_state_v2("cyclic-noetic-loopbreak.json"))
        self.assertTrue(cyclic_noetic.valid, cyclic_noetic.findings)
        self.assertEqual(cyclic_noetic.terminal_disposition, "HOLD")
        self.assertEqual(cyclic_noetic.event_dag_edges, ())

    def test_current_state_v2_exemplar_preserves_rich_signature_history(self) -> None:
        payload = load_state_v2("composed-all-plan-fields.json")
        state = validate_in_process(payload)
        self.assertTrue(state.valid, state.findings)
        self.assertEqual(
            state.reread_signature_history,
            tuple(
                (row["cycle_id"], row["raw_exit_event_id"], row["a07_reducer_signature_sha256"])
                for row in payload["reread_signature_history"]
            ),
        )

    def test_stale_state_v2_signature_fails_at_reread_signature_boundary(self) -> None:
        current = load_state_v2("composed-all-plan-fields.json")
        state = validate_in_process(with_stale_state_v2_signature(current))
        self.assertFalse(state.valid)
        self.assertEqual(state.findings[0].subcode, "state_v2_reread_signature_mismatch")

    def test_state_v2_adapter_fails_closed_at_each_native_cycle_boundary(self) -> None:
        mutations = {
            "state_v2_route_invalid": lambda p: p["burden_cycles"][0].pop("route_gradient"),
            "state_v2_obligation_invalid": lambda p: p["owner_routes"].pop(0),
            "state_v2_act_row_invalid": lambda p: p["act_row_details"].pop(0),
            "state_v2_disposition_invalid": lambda p: p["owner_execution_dispositions"].pop(0),
            "state_v2_obligation_state_invalid": lambda p: p["owner_obligation_state"]["declared_ids"].pop(0),
            "state_v2_operation_event_invalid": lambda p: p["burden_cycles"][0]["operation_events"].pop(),
            "state_v2_land_invalid": lambda p: p["burden_cycles"][0].pop("land"),
            "state_v2_post_land_invalid": lambda p: p["burden_cycles"][0].pop("post_land_delta"),
            "state_v2_reread_invalid": lambda p: p["burden_cycles"][0].pop("reread"),
            "state_v2_raw_exit_invalid": lambda p: p["burden_cycles"][0]["reread"].pop("raw_exit"),
        }
        for expected_subcode, mutate in mutations.items():
            with self.subTest(expected_subcode=expected_subcode):
                payload = copy.deepcopy(load_state_v2("composed-all-plan-fields.json"))
                mutate(payload)
                state = validate_in_process(payload)
                self.assertFalse(state.valid)
                self.assertEqual(state.findings[0].subcode, expected_subcode)

    def test_state_v2_adapter_accepts_exact_plan04_plan05_and_all_candidate_dispositions(self) -> None:
        names = [
            "composed-all-plan-fields.json",
            "multi-operation-capsule-cycle.json",
            "candidate-disposition-activate-held.json",
            "candidate-disposition-instantiate-generated.json",
            "candidate-disposition-defer-preempted.json",
            "candidate-disposition-non-load-bearing.json",
            "candidate-disposition-hold-partial.json",
            "unknown-candidate-kind-held.json",
            "cyclic-noetic-loopbreak.json",
            "generated-child-of-generated-parent.json",
            "low-topology.json",
            "overlapping-candidate-hyperedges.json",
            "stage05-stop-closure-candidate.json",
        ]
        for name in names:
            with self.subTest(name=name):
                state = validate_in_process(load_state_v2(name))
                self.assertTrue(state.valid, state.findings)

    def test_state_v2_unknown_candidate_kind_is_fail_closed_unless_held(self) -> None:
        payload = load_state_v2("unknown-candidate-kind-held.json")
        candidate = payload["burden_cycles"][0]["reread"]["raw_exit"]["candidate_events"][0]
        candidate["disposition"] = "non_load_bearing"
        candidate["candidate_event_sha256"] = canonical_self_hash(candidate, "candidate_event_sha256")
        state = validate_in_process(payload)
        self.assertFalse(state.valid)
        self.assertEqual(state.findings[0].subcode, "state_v2_candidate_kind_delta")

    def test_state_v2_native_operation_hash_covers_local_delta(self) -> None:
        payload = load_state_v2("composed-all-plan-fields.json")
        payload["operation_capsules"][0]["delta"]["result"] = "tampered without operation self-hash update"
        state = validate_in_process(payload)
        self.assertFalse(state.valid)
        self.assertEqual(state.findings[0].subcode, "state_v2_operation_hash_mismatch")

    def test_reread_signature_is_semantic_delta_sensitive_and_custody_neutral(self) -> None:
        tools = str(ROOT / "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        from mrp_recursion_lib import _reread_state_signature

        event = {
            "exit_disposition": "RECURSE",
            "field_diagnostics": [
                {"diagnostic_id": "D1", "operator": "curl", "target": "B1", "status": "live", "basis_refs": ["basis:curl"], "delta_ref": "D"},
                {"diagnostic_id": "D2", "operator": "divergence", "target": "B1", "status": "neutral", "basis_refs": ["basis:div"], "delta_ref": "D"},
            ],
            "noetic_dependency_graph": {"graph_id": "G1", "nodes": ["A", "B"], "edges": [{"from": "A", "to": "B"}]},
        }
        semantics = {
            "operation_capsules": [{
                "capsule_id": "OC1", "body_ref": "body-1", "body_sha256": "1" * 64,
                "owner_id": "owner", "operation": "repair", "register_axis": "Omega",
                "before_state": {"state_id": "before-1", "state": "before"},
                "performed_operation": {"mechanism": "repair", "application": "apply repair"},
                "after_state": {"state_id": "after-1", "state": "after"},
                "delta": {"delta_id": "delta-1", "carrier": "B1", "result": "changed", "recoverability_evidence": [{"after_state_path": "state", "value": "after"}]},
                "residual": {"status": "none", "pressure_ids": [], "basis": "none"},
                "land_contribution": {"decision": "contributes", "delta_ref": "delta-1", "basis": "supports Land"},
            }],
            "land": {"record_id": "land-1", "status": "landed", "contribution_refs": ["capsule:OC1#land_contribution"]},
            "post_land_delta": {"delta_id": "post-1", "basis_refs": ["basis:post"]},
        }
        common = dict(b_la=["B1"], b_mrp=[], burden_terminal_states={"B1": "landed"}, candidate_history={}, live_candidates=set(), live_obligations=set())
        baseline = _reread_state_signature(**common, event=event, cycle_semantics=semantics)

        custody_only = copy.deepcopy(semantics)
        custody_only["operation_capsules"][0].update({"capsule_id": "OC9", "body_ref": "body-9"})
        custody_only["operation_capsules"][0]["before_state"]["state_id"] = "before-9"
        custody_only["operation_capsules"][0]["after_state"]["state_id"] = "after-9"
        custody_only["operation_capsules"][0]["delta"]["delta_id"] = "delta-9"
        custody_only["land"]["record_id"] = "land-9"
        custody_only["land"]["contribution_refs"] = ["capsule:OC9#land_contribution"]
        custody_only["post_land_delta"]["delta_id"] = "post-9"
        self.assertEqual(baseline, _reread_state_signature(**common, event=event, cycle_semantics=custody_only))

        changed = copy.deepcopy(semantics)
        changed["operation_capsules"][0]["delta"]["result"] = "materially different"
        self.assertNotEqual(baseline, _reread_state_signature(**common, event=event, cycle_semantics=changed))

        graph_changed = copy.deepcopy(event)
        graph_changed["noetic_dependency_graph"]["edges"].append({"from": "B", "to": "A"})
        self.assertNotEqual(baseline, _reread_state_signature(**common, event=graph_changed, cycle_semantics=semantics))

    def test_reread_signature_canonicalizes_diagnostic_and_graph_edge_permutations(self) -> None:
        tools = str(ROOT / "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        from mrp_recursion_lib import _reread_state_signature

        event = {
            "exit_disposition": "RECURSE",
            "field_diagnostics": [
                {"operator": "curl", "target": "B1", "status": "live", "basis_refs": ["b", "a"], "delta_ref": "D"},
                {"operator": "divergence", "target": "B1", "status": "neutral", "basis_refs": ["c"], "delta_ref": "D"},
            ],
            "noetic_dependency_graph": {"nodes": ["B", "A"], "edges": [{"from": "B", "to": "A"}, {"from": "A", "to": "B"}]},
        }
        common = dict(b_la=["B1"], b_mrp=[], burden_terminal_states={"B1": "landed"}, candidate_history={}, live_candidates=set(), live_obligations=set(), cycle_semantics={})
        baseline = _reread_state_signature(**common, event=event)
        permuted = copy.deepcopy(event)
        permuted["field_diagnostics"].reverse()
        permuted["field_diagnostics"][1]["basis_refs"].reverse()
        permuted["noetic_dependency_graph"]["nodes"].reverse()
        permuted["noetic_dependency_graph"]["edges"].reverse()
        self.assertEqual(baseline, _reread_state_signature(**common, event=permuted))


if __name__ == "__main__":
    unittest.main()
