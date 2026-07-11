from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent
MODULE = ROOT / "tools" / "owner_obligation_coverage.py"
O1 = "O-cd7aade8cee23cb05b941960"
O2 = "O-1dee4014868741cd5ac38818"


def external_obligation_ids(path: Path) -> list[str]:
    if path.name in {"proved-derivative-integration.json", "duplicate-derivative-id-last-row-wins.json", "fabricated-derivative-absent-upstream.json"}:
        return [O1, "O-6979f78443c0b7e6e5f13ed6"]
    if path.name == "self-rehashed-obligation-omission.json":
        return [O1, O2]
    if path.name == "declared-obligation-id-not-derived.json":
        return ["O1"]
    return [O1]


def external_route_inputs(path: Path) -> tuple[list[str], list[str]]:
    return (["P1", "P2"], ["BP1"]) if path.name in {"proved-derivative-integration.json", "duplicate-derivative-id-last-row-wins.json", "fabricated-derivative-absent-upstream.json"} else (["P1"], ["BP1"])


def derivative_authority(path: Path) -> tuple[list[dict], str]:
    if path.name == "proved-derivative-integration.json":
        name = "derivatives-valid.json"
    elif path.name == "duplicate-derivative-id-last-row-wins.json":
        name = "derivatives-duplicate.json"
    else:
        name = "derivatives-empty.json"
    rows = json.loads((FIXTURES / "upstream" / name).read_text(encoding="utf-8"))
    digest = hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return rows, digest


def load_module():
    if not MODULE.exists():
        return None
    spec = importlib.util.spec_from_file_location("owner_obligation_coverage", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OwnerObligationCoverageTests(unittest.TestCase):
    def test_executed_and_explicit_disposition_neighbors(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "owner_obligation_coverage implementation missing")
        for path in sorted((FIXTURES / "valid").glob("*.json")):
            with self.subTest(path=path.name):
                pressures, partitions = external_route_inputs(path)
                derivatives, digest = derivative_authority(path)
                self.assertEqual(module.validate_owner_obligation_coverage(json.loads(path.read_text(encoding="utf-8")), upstream_obligation_ids=external_obligation_ids(path), upstream_pressure_ids=pressures, upstream_partition_decision_ids=partitions, upstream_derivative_inventory=derivatives, upstream_derivative_inventory_sha256=digest), [])

    def test_active_invalids_fail_for_pinned_reason(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "owner_obligation_coverage implementation missing")
        for expectation_path in sorted((FIXTURES / "invalid").glob("*.expectation.json")):
            expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
            path = expectation_path.with_name(expectation["fixture"])
            pressures, partitions = external_route_inputs(path)
            derivatives, digest = derivative_authority(path)
            findings = module.validate_owner_obligation_coverage(json.loads(path.read_text(encoding="utf-8")), upstream_obligation_ids=external_obligation_ids(path), upstream_pressure_ids=pressures, upstream_partition_decision_ids=partitions, upstream_derivative_inventory=derivatives, upstream_derivative_inventory_sha256=digest)
            with self.subTest(path=path.name):
                self.assertTrue(findings, "invalid owner-obligation fixture survived")
                self.assertEqual(findings[0]["failure_class"], expectation["expected_failure_class"])
                self.assertEqual(findings[0]["failure_subcode"], expectation["expected_failure_subcode"])
                required = {"schema","fixture","kind","expected_checker_id","expected_exit_category","expected_exit_code","expected_earliest_stage","expected_failure_class","expected_downstream_invalidated","required_diagnostic_markers","forbidden_artifacts","provenance"}
                self.assertTrue(required <= set(expectation))
                self.assertEqual(expectation["schema"], "daee-negative-fixture-expectation-v1")
                self.assertEqual(expectation["kind"], "invalid-single-signature")
                self.assertEqual(expectation["expected_checker_id"], "owner-obligation-coverage")
                rendered = json.dumps(findings[0], sort_keys=True).lower()
                for marker in expectation["required_diagnostic_markers"]:
                    self.assertIn(marker.lower(), rendered)
                for forbidden in expectation["forbidden_artifacts"]:
                    self.assertFalse(any(candidate.name == Path(forbidden).name for candidate in FIXTURES.rglob("*")))

    def test_stable_id_is_order_independent_for_pressure_set(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "owner_obligation_coverage implementation missing")
        left = module.stable_obligation_id("B1", ["P2", "P1"], "owner-a", "operate-a")
        right = module.stable_obligation_id("B1", ["P1", "P2"], "owner-a", "operate-a")
        self.assertEqual(left, right)

    def test_distinct_or_unresolved_cohesion_cannot_execute_without_repartition(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "owner_obligation_coverage implementation missing")
        path = FIXTURES / "valid" / "executed-exactly-once.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["owner_routes"][0]["same_burden_cohesion"]["tau_relation"] = "distinct"
        derivatives, digest = derivative_authority(path)
        findings = module.validate_owner_obligation_coverage(record, upstream_obligation_ids=[O1], upstream_pressure_ids=["P1"], upstream_partition_decision_ids=["BP1"], upstream_derivative_inventory=derivatives, upstream_derivative_inventory_sha256=digest)
        self.assertTrue(findings, "distinct cohesion executed without repartition or hold")
        self.assertEqual(findings[0]["failure_subcode"], "cohesion-repartition-required")

    def test_arbitrary_finite_owner_set_has_no_submove_limit(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "owner_obligation_coverage implementation missing")
        routes=[]; acts=[]; dispositions=[]; obligation_ids=[]; pressure_ids=[]; partition_ids=[]
        for index in range(1,24):
            pressure_id=f"P{index}"; partition_id=f"BP{index}"; owner=f"owner-{index}"; operation=f"operate-{index}"; burden=f"B{index}"
            obligation_id=module.stable_obligation_id(burden,[pressure_id],owner,operation)
            obligation_ids.append(obligation_id);pressure_ids.append(pressure_id);partition_ids.append(partition_id)
            routes.append({"obligation_id":obligation_id,"burden_id":burden,"pressure_ids":[pressure_id],"partition_decision_id":partition_id,"owner_id":owner,"operation":operation,"register_axis":"axis-a","execution_class":"required","route_status":"executable","trigger":None,"owner_body_status":"loaded","same_burden_cohesion":{"target_family_relation":"same","tau_relation":"same","source_frame_relation":"same","claim_cluster_relation":"same","restoration_vector_relation":"same","already_handled":False},"basis":"The independently routed transition is executable."})
            acts.append({"obligation_id":obligation_id,"burden_id":burden,"pressure_ids":[pressure_id],"owner_id":owner,"operation":operation,"register_axis":"axis-a","body_ref":f"{burden}_1"})
            dispositions.append({"obligation_id":obligation_id,"burden_id":burden,"disposition":"executed","body_ref":f"{burden}_1","satisfied_by_obligation_id":None,"trigger_evidence":None,"basis":"The exact ACT executed once.","gate":None,"next_action":None})
        record={"topology_contract":"input-pressure-v1","upstream_obligation_ids":obligation_ids,"upstream_obligation_set_sha256":module.obligation_set_sha256(obligation_ids),"owner_routes":routes,"act_row_details":acts,"owner_execution_dispositions":dispositions,"partition_derivative_mappings":[],"stage04_status":"pass","downstream_release_state":"OPEN"}
        derivatives, digest = derivative_authority(FIXTURES / "valid" / "executed-exactly-once.json")
        self.assertEqual(module.validate_owner_obligation_coverage(record,upstream_obligation_ids=obligation_ids,upstream_pressure_ids=pressure_ids,upstream_partition_decision_ids=partition_ids,upstream_derivative_inventory=derivatives,upstream_derivative_inventory_sha256=digest),[])

    def test_duplicate_derivative_rejection_is_order_invariant(self) -> None:
        module=load_module();path=FIXTURES/"invalid"/"duplicate-derivative-id-last-row-wins.json";record=json.loads(path.read_text(encoding="utf-8"));record["partition_derivative_mappings"].reverse();derivatives=list(reversed(derivative_authority(path)[0]));digest=hashlib.sha256(json.dumps(derivatives,ensure_ascii=False,sort_keys=True,separators=(",", ":")).encode("utf-8")).hexdigest()
        findings=module.validate_owner_obligation_coverage(record,upstream_obligation_ids=external_obligation_ids(path),upstream_pressure_ids=["P1","P2"],upstream_partition_decision_ids=["BP1"],upstream_derivative_inventory=derivatives,upstream_derivative_inventory_sha256=digest)
        self.assertEqual(findings[0]["failure_subcode"],"derivative-decision-duplicate")


if __name__ == "__main__":
    unittest.main()
