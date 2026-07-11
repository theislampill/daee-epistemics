from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent
MODULE = ROOT / "tools" / "topology_partition.py"


def load_module():
    if not MODULE.exists():
        return None
    spec = importlib.util.spec_from_file_location("topology_partition", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def derivative_authority(path: Path) -> tuple[list[dict], str]:
    name = "derivatives-valid.json" if path.name == "valid-derivative-merge.json" else "derivatives-empty.json"
    value = json.loads((FIXTURES / "upstream" / name).read_text(encoding="utf-8"))
    digest = hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return value, digest


def external_universe(path: Path) -> tuple[list[str], list[str]]:
    if path.name == "overlapping-ambiguity-loci.json":
        return ["N1", "N2", "N3"], ["P1", "P2"]
    if path.name in {"valid-merge.json", "valid-derivative-merge.json", "unreconstructible-merge.json", "upstream-pressure-omitted.json", "self-rehashed-upstream-omission.json", "merge-overlapping-pressure-sets-without-derivative.json", "distinct-registers-declared-compatible.json", "keep-distinct-with-merged-role.json", "invented-held-route-overlapping.json"}:
        return ["N1", "N2"], ["P1", "P2"]
    if path.name == "partition-identity-aliased.json":
        return ["N1", "N2"], ["P1"]
    return ["N1"], ["P1"]


class TopologyPartitionContractTests(unittest.TestCase):
    def assert_expectation_contract(self, expectation, findings) -> None:
        required = {"schema","fixture","kind","expected_checker_id","expected_exit_category","expected_exit_code","expected_earliest_stage","expected_failure_class","expected_downstream_invalidated","required_diagnostic_markers","forbidden_artifacts","provenance"}
        self.assertTrue(required <= set(expectation))
        self.assertEqual(expectation["schema"], "daee-negative-fixture-expectation-v1")
        self.assertEqual(expectation["kind"], "invalid-single-signature")
        self.assertEqual(expectation["expected_checker_id"], "topology-partition")
        self.assertEqual(expectation["expected_exit_category"], "validation-failure")
        self.assertEqual(expectation["expected_exit_code"], 1)
        self.assertEqual(expectation["expected_earliest_stage"], "02")
        self.assertEqual(expectation["expected_downstream_invalidated"], ["03","04","05","06","07","08"])
        rendered = json.dumps(findings[0], sort_keys=True).lower()
        for marker in expectation["required_diagnostic_markers"]:
            self.assertIn(marker.lower(), rendered)
        for forbidden in expectation["forbidden_artifacts"]:
            self.assertFalse(any(candidate.name == Path(forbidden).name for candidate in FIXTURES.rglob("*")))

    def test_valid_split_and_merge(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "topology_partition implementation missing")
        for path in sorted((FIXTURES / "valid").glob("*.json")):
            with self.subTest(path=path.name):
                candidates, pressures = external_universe(path)
                derivatives, derivative_hash = derivative_authority(path)
                self.assertEqual(module.validate_topology_partition(json.loads(path.read_text(encoding="utf-8")), upstream_candidate_ids=candidates, upstream_pressure_ids=pressures, upstream_derivative_inventory=derivatives, upstream_derivative_inventory_sha256=derivative_hash), [])

    def test_primary_plan03_candidate_and_pressure_rows_are_required(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "topology_partition implementation missing")
        record = json.loads((FIXTURES / "valid" / "valid-merge.json").read_text(encoding="utf-8"))
        del record["candidate_states"][0]["frame_token"]
        derivatives, derivative_hash = derivative_authority(FIXTURES / "valid" / "valid-merge.json")
        findings = module.validate_topology_partition(record, upstream_candidate_ids=["N1", "N2"], upstream_pressure_ids=["P1", "P2"], upstream_derivative_inventory=derivatives, upstream_derivative_inventory_sha256=derivative_hash)
        self.assertTrue(findings, "skeletal substitute-dialect rows survived")
        self.assertEqual(findings[0]["failure_subcode"], "candidate-shape")

    def test_active_invalids_fail_for_pinned_reason(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "topology_partition implementation missing")
        for expectation_path in sorted((FIXTURES / "invalid").glob("*.expectation.json")):
            expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
            path = expectation_path.with_name(expectation["fixture"])
            candidates, pressures = external_universe(path)
            derivatives, derivative_hash = derivative_authority(path)
            findings = module.validate_topology_partition(json.loads(path.read_text(encoding="utf-8")), upstream_candidate_ids=candidates, upstream_pressure_ids=pressures, upstream_derivative_inventory=derivatives, upstream_derivative_inventory_sha256=derivative_hash)
            with self.subTest(path=path.name):
                self.assertTrue(findings, "invalid partition fixture survived")
                self.assertEqual(findings[0]["failure_class"], expectation["expected_failure_class"])
                self.assertEqual(findings[0]["failure_subcode"], expectation["expected_failure_subcode"])
                self.assert_expectation_contract(expectation, findings)

    def test_derivative_merge_is_permutation_invariant(self) -> None:
        module=load_module();path=FIXTURES/"valid"/"valid-derivative-merge.json";record=json.loads(path.read_text(encoding="utf-8"));record["candidate_states"].reverse();derivatives,digest=derivative_authority(path)
        self.assertEqual(module.validate_topology_partition(record,upstream_candidate_ids=["N2","N1"],upstream_pressure_ids=["P2","P1"],upstream_derivative_inventory=derivatives,upstream_derivative_inventory_sha256=digest),[])


if __name__ == "__main__":
    unittest.main()
