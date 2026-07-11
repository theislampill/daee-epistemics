from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent
MODULE = ROOT / "tools" / "operation_capsule_contract.py"
STANDALONE = ROOT / "schema" / "operation-capsule.schema.json"
FROZEN = ROOT / "schema" / "state-capsule-v2.schema.json"


def load_module():
    if not MODULE.exists():
        return None
    spec = importlib.util.spec_from_file_location("operation_capsule_contract", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def base_authority(module, path: Path | None = None):
    name="inventory-collapsed.json" if path is not None and path.name=="collapsed-two-obligations-one-capsule.json" else "inventory-two.json" if path is not None and path.name=="two-obligations-two-capsules.json" else "inventory-base.json"
    value = json.loads((FIXTURES / "upstream" / name).read_text(encoding="utf-8"))
    return value, module.canonical_sha256(value)


class OperationCapsuleContractTests(unittest.TestCase):
    def test_standalone_schema_exposes_primary_plan05_fields(self) -> None:
        self.assertTrue(STANDALONE.exists(), "standalone operation schema missing")
        standalone = json.loads(STANDALONE.read_text(encoding="utf-8"))["$defs"]["operation_capsule"]
        required = set(standalone["required"])
        primary = {"body_ref","burden_id","obligation_ids","pressure_ids","owner_id","operation","register_axis","before_state","performed_operation","after_state","delta","residual","land_contribution","source_contract_refs","operation_capsule_sha256"}
        self.assertTrue(primary <= required)

    def test_embedded_delta_is_reportable_without_freezing_provisional_state_shape(self) -> None:
        standalone = json.loads(STANDALONE.read_text(encoding="utf-8"))["$defs"]["operation_capsule"]
        frozen_doc = json.loads(FROZEN.read_text(encoding="utf-8"))
        embedded = frozen_doc.get("$defs", {}).get("operation_capsule", {})
        self.assertIsInstance(set(standalone["required"]) - set(embedded.get("required", [])), set)

    def test_fully_evidenced_operation_is_valid(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "operation_capsule_contract implementation missing")
        path = FIXTURES / "valid" / "fully-evidenced-operation.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("operation_capsules", record, "Plan05 requires the open-cardinality capsule collection")
        self.assertNotIn("capsule", record, "singular substitute wrapper is forbidden")
        authority, digest = base_authority(module, path)
        self.assertEqual(module.validate_operation_record(record, upstream_inventory=authority, upstream_inventory_sha256=digest), [])

    def test_open_cardinality_capsule_collection_has_no_singleton_limit(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "operation_capsule_contract implementation missing")
        record = json.loads((FIXTURES / "valid" / "fully-evidenced-operation.json").read_text(encoding="utf-8"))
        template = record["operation_capsules"][0]
        for index in range(2, 12):
            capsule = copy.deepcopy(template)
            capsule.update({"capsule_id":f"OC{index}","cycle_id":f"C{index}","body_ref":f"B{index}_1","burden_id":f"B{index}","obligation_ids":[f"O{index}"],"pressure_ids":[f"P{index}"],"owner_id":f"owner-{index}","operation":f"operate-{index}"})
            capsule["before_state"] = {"claim_state":f"before-{index}","source_pressure_ids":[f"P{index}"]}
            capsule["performed_operation"] = {"mechanism":f"apply transition {index}","application":f"apply the transition to P{index}"}
            capsule["after_state"] = {"claim_state":f"after-{index}","transition_marker":f"changed-{index}"}
            capsule["delta"] = {"delta_id":f"D{index}","carrier":f"Delta(B{index})","result":f"changed-{index}","recoverability_evidence":[{"after_state_path":"transition_marker","value":f"changed-{index}"}]}
            capsule["land_contribution"] = {"decision":"contributes","delta_ref":f"D{index}","basis":"the changed state contributes while Stage05 retains terminal authority"}
            content = f"body-{index}"
            capsule["body_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
            capsule["operation_capsule_sha256"] = module.operation_capsule_sha256(capsule)
            record["operation_capsules"].append(capsule)
            record["obligations"].append({"obligation_id":f"O{index}","burden_id":f"B{index}","owner_id":f"owner-{index}","operation":f"operate-{index}","register_axis":"axis-a","pressure_ids":[f"P{index}"]})
            record["pressures"].append({"pressure_id":f"P{index}"})
            record["owner_routes"].append({"obligation_id":f"O{index}","owner_id":f"owner-{index}","operation":f"operate-{index}","register_axis":"axis-a","burden_id":f"B{index}","pressure_ids":[f"P{index}"]})
            record["act_row_details"].append({"obligation_id":f"O{index}","body_ref":f"B{index}_1","burden_id":f"B{index}","owner_id":f"owner-{index}","operation":f"operate-{index}","register_axis":"axis-a","pressure_ids":[f"P{index}"]})
            record["cycles"].append({"cycle_id":f"C{index}","burden_id":f"B{index}","obligation_ids":[f"O{index}"],"operation_capsule_ids":[f"OC{index}"]})
            record["body_artifacts"][f"B{index}_1"] = {"content":content,"sha256":capsule["body_sha256"]}
            record["operation_capsule_hashes"][f"B{index}_1"] = capsule["operation_capsule_sha256"]
            refs = [f"capsule:OC{index}#before_state",f"route:O{index}#owner.operation",f"capsule:OC{index}#performed_operation",f"capsule:OC{index}#delta",f"capsule:OC{index}#residual",f"capsule:OC{index}#land_contribution"]
            record["events"].extend({"event_id":f"OC{index}-E{sequence}","capsule_id":f"OC{index}","sequence":sequence,"kind":kind,"ref":ref} for sequence,(kind,ref) in enumerate(zip(module.CHRONOLOGY,refs),1))
        authority={"obligation_ids":[f"O{index}" for index in range(1,12)],"pressure_ids":[f"P{index}" for index in range(1,12)],"cycle_ids":[f"C{index}" for index in range(1,12)]}
        self.assertEqual(module.validate_operation_record(record, upstream_inventory=authority, upstream_inventory_sha256=module.canonical_sha256(authority)), [])

    def test_active_invalids_fail_for_pinned_reason(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "operation_capsule_contract implementation missing")
        for expectation_path in sorted((FIXTURES / "invalid").glob("*.expectation.json")):
            expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
            fixture = expectation_path.with_name(expectation["fixture"])
            authority, digest = base_authority(module, fixture)
            findings = module.validate_operation_record(json.loads(fixture.read_text(encoding="utf-8")), upstream_inventory=authority, upstream_inventory_sha256=digest)
            with self.subTest(fixture=fixture.name):
                self.assertTrue(findings, "invalid operation survived")
                self.assertEqual(findings[0]["failure_class"], expectation["expected_failure_class"])
                self.assertEqual(findings[0]["failure_subcode"], expectation["expected_failure_subcode"])
                required = {"schema","fixture","kind","expected_checker_id","expected_exit_category","expected_exit_code","expected_earliest_stage","expected_failure_class","expected_downstream_invalidated","required_diagnostic_markers","forbidden_artifacts","provenance"}
                self.assertTrue(required <= set(expectation))
                self.assertEqual(expectation["schema"], "daee-negative-fixture-expectation-v1")
                self.assertEqual(expectation["kind"], "invalid-single-signature")
                self.assertEqual(expectation["expected_checker_id"], "operation-capsule-contract")
                self.assertEqual(expectation["expected_earliest_stage"], "04")
                self.assertEqual(expectation["expected_downstream_invalidated"], ["05","06","07","08"])
                rendered = json.dumps(findings[0], sort_keys=True).lower()
                for marker in expectation["required_diagnostic_markers"]:
                    self.assertIn(marker.lower(), rendered)
                for forbidden in expectation["forbidden_artifacts"]:
                    self.assertFalse(any(candidate.name == Path(forbidden).name for candidate in FIXTURES.rglob("*")))

    def test_duplicate_join_rows_and_unanchored_state_fail(self) -> None:
        module = load_module()
        base = json.loads((FIXTURES / "valid" / "fully-evidenced-operation.json").read_text(encoding="utf-8"))
        authority, digest = base_authority(module)
        for collection, subcode in (("obligations","obligation-row-duplicate"),("pressures","pressure-row-duplicate"),("owner_routes","owner-route-row-duplicate")):
            record=copy.deepcopy(base); record[collection].append(copy.deepcopy(record[collection][0]))
            findings=module.validate_operation_record(record,upstream_inventory=authority,upstream_inventory_sha256=digest)
            with self.subTest(collection=collection): self.assertEqual(findings[0]["failure_subcode"],subcode)
        record=copy.deepcopy(base); record["operation_capsules"][0]["before_state"]={"claim_state":"before"}; record["operation_capsules"][0]["operation_capsule_sha256"]=module.operation_capsule_sha256(record["operation_capsules"][0]); record["operation_capsule_hashes"]["B1_1"]=record["operation_capsules"][0]["operation_capsule_sha256"]
        findings=module.validate_operation_record(record,upstream_inventory=authority,upstream_inventory_sha256=digest)
        self.assertEqual(findings[0]["failure_subcode"],"before-state-pressure-anchor")

    def test_two_obligations_cannot_collapse_into_one_v1_capsule(self) -> None:
        module=load_module(); record=json.loads((FIXTURES/"valid"/"fully-evidenced-operation.json").read_text(encoding="utf-8"))
        obligation=copy.deepcopy(record["obligations"][0]); obligation["obligation_id"]="O2"; record["obligations"].append(obligation)
        route=copy.deepcopy(record["owner_routes"][0]); route["obligation_id"]="O2"; record["owner_routes"].append(route)
        record["operation_capsules"][0]["obligation_ids"].append("O2"); record["cycles"][0]["obligation_ids"].append("O2")
        record["operation_capsules"][0]["operation_capsule_sha256"]=module.operation_capsule_sha256(record["operation_capsules"][0]);record["operation_capsule_hashes"]["B1_1"]=record["operation_capsules"][0]["operation_capsule_sha256"]
        authority={"obligation_ids":["O1","O2"],"pressure_ids":["P1"],"cycle_ids":["C1"]}
        findings=module.validate_operation_record(record,upstream_inventory=authority,upstream_inventory_sha256=module.canonical_sha256(authority))
        self.assertEqual(findings[0]["failure_subcode"],"obligation-capsule-cardinality")


if __name__ == "__main__":
    unittest.main()
