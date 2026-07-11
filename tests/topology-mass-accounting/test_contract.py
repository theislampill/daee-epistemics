from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent
MODULE = ROOT / "tools" / "topology_mass_accounting.py"


def external_obligation_ids(path: Path) -> list[str]:
    if path.parent.name == "valid":
        upstream_name = "duplicate.json" if path.name == "proved-duplicate-discharge.json" else "nonempty.json" if path.name == "compact-fully-paid.json" else "empty.json"
        upstream = json.loads((FIXTURES / "upstream" / upstream_name).read_text(encoding="utf-8"))
        return upstream["obligation_ids"]
    if path.name == "self-rehashed-obligation-omission.json":
        return ["O1", "O2"]
    record = json.loads(path.read_text(encoding="utf-8"))
    return [item["obligation_id"] for item in record.get("obligations", []) if isinstance(item, dict) and isinstance(item.get("obligation_id"), str)]


def external_inventory_hash(path: Path) -> str:
    if path.name in {"self-attested-arbitrary-evidence.json","ghost-pressure-burden-source.json"}:
        return json.loads(path.read_text(encoding="utf-8"))["staged_handoff_sha256"]
    upstream_name = "duplicate.json" if path.name == "proved-duplicate-discharge.json" else "nonempty.json" if path.name == "compact-fully-paid.json" else "empty.json"
    upstream = FIXTURES / "upstream" / upstream_name
    return hashlib.sha256(upstream.read_bytes()).hexdigest() if path.parent.name == "valid" else "2" * 64


def evidence_authority(path: Path, module):
    record=json.loads(path.read_text(encoding="utf-8"))
    if not record.get("obligations"):
        name="evidence-empty.json"
    elif path.name in {"proved-duplicate-discharge.json","duplicate-without-decision.json"}:
        name="evidence-duplicate.json"
    else:
        name="evidence-compact.json"
    value=json.loads((FIXTURES/"upstream"/name).read_text(encoding="utf-8"))
    return value,module.canonical_sha256(value)


def load_module():
    if not MODULE.exists():
        return None
    spec = importlib.util.spec_from_file_location("topology_mass_accounting", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TopologyMassAccountingTests(unittest.TestCase):
    def test_primary_plan06_valid_families_pass(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "topology_mass_accounting implementation missing")
        for path in sorted((FIXTURES / "valid").glob("*.json")):
            with self.subTest(path=path.name):
                authority,digest=evidence_authority(path,module)
                self.assertEqual(module.validate_accounting(json.loads(path.read_text(encoding="utf-8")), upstream_obligation_ids=external_obligation_ids(path), upstream_inventory_sha256=external_inventory_hash(path),evidence_authority=authority,evidence_authority_sha256=digest), [])

    def test_active_invalids_fail_without_crashing(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "topology_mass_accounting implementation missing")
        for expectation_path in sorted((FIXTURES / "invalid").glob("*.expectation.json")):
            expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
            path = expectation_path.with_name(expectation["fixture"])
            with self.subTest(path=path.name):
                try:
                    authority,digest=evidence_authority(path,module)
                    findings = module.validate_accounting(json.loads(path.read_text(encoding="utf-8")), upstream_obligation_ids=external_obligation_ids(path), upstream_inventory_sha256=external_inventory_hash(path),evidence_authority=authority,evidence_authority_sha256=digest)
                except Exception as exc:  # robustness is the behavior under test
                    self.fail(f"validator crashed instead of returning a structural finding: {exc!r}")
                self.assertTrue(findings, "invalid topology accounting fixture survived")
                self.assertEqual(findings[0]["failure_class"], expectation["expected_failure_class"])
                self.assertEqual(findings[0]["failure_subcode"], expectation["expected_failure_subcode"])

    def test_arbitrary_finite_wide_specimen_has_no_encoded_limit(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "topology_mass_accounting implementation missing")
        obligations = []
        evidence = []
        for index in range(37):
            ref = f"R{index}"
            content=f"validated capsule {index}"; artifact_hash=hashlib.sha256(content.encode("utf-8")).hexdigest()
            evidence.append({"evidence_id":ref,"evidence_type":"operation_capsule","artifact_id":f"OC{index}","artifact_sha256":artifact_hash,"validator_receipt_id":f"VR{index}"})
            obligations.append({"obligation_id":f"O{index}","kind":"owner_operation","origin_stage":"03","source_ids":[f"P{index}",f"B{index + 1}"],"allowed_dispositions":["satisfied"],"disposition":"satisfied","evidence_refs":[ref],"basis":"reconstructible operation evidence"})
        artifacts=[];receipts=[]
        for index,item in enumerate(evidence):
            content=f"validated capsule {index}"; artifacts.append({"artifact_id":item["artifact_id"],"content":content,"artifact_sha256":item["artifact_sha256"]})
            receipt={"receipt_id":f"VR{index}","evidence_id":item["evidence_id"],"artifact_id":item["artifact_id"],"artifact_sha256":item["artifact_sha256"],"evidence_type":item["evidence_type"],"validator_id":"operation-capsule-contract","verdict":"PASS"};receipt["receipt_sha256"]=module.canonical_sha256(receipt);receipts.append(receipt)
        authority={"source_ids":[source for obligation in obligations for source in obligation["source_ids"]],"artifacts":artifacts,"validator_receipts":receipts}
        record = module.build_accounting_record(case_id="neutral-wide", input_sha256="1"*64, staged_handoff_sha256="2"*64, output_sha256="3"*64, obligations=obligations, evidence_inventory=evidence, partition_decisions=[], advisory_metrics={"output_bytes":1})
        self.assertEqual(module.validate_accounting(record, upstream_obligation_ids=[item["obligation_id"] for item in obligations], upstream_inventory_sha256="2" * 64,evidence_authority=authority,evidence_authority_sha256=module.canonical_sha256(authority)), [])
        record["advisory_metrics"]["output_bytes"] = 10_000_000
        self.assertEqual(module.validate_accounting(record, upstream_obligation_ids=[item["obligation_id"] for item in obligations], upstream_inventory_sha256="2" * 64,evidence_authority=authority,evidence_authority_sha256=module.canonical_sha256(authority)), [])

    def test_satisfied_owner_operation_requires_operation_evidence_type(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "topology_mass_accounting implementation missing")
        path = FIXTURES / "valid" / "compact-fully-paid.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["evidence_inventory"][0]["evidence_type"] = "basis"
        authority,digest=evidence_authority(path,module)
        authority=json.loads(json.dumps(authority));authority["validator_receipts"][0]["evidence_type"]="basis";receipt=authority["validator_receipts"][0];receipt["receipt_sha256"]=module.canonical_sha256({key:value for key,value in receipt.items() if key!="receipt_sha256"});digest=module.canonical_sha256(authority)
        findings = module.validate_accounting(record, upstream_obligation_ids=["O1"], upstream_inventory_sha256=external_inventory_hash(path),evidence_authority=authority,evidence_authority_sha256=digest)
        self.assertTrue(findings, "generic typed evidence paid an owner operation")
        self.assertEqual(findings[0]["failure_subcode"], "evidence-kind-mismatch")

    def test_self_attested_evidence_and_ghost_sources_fail(self) -> None:
        module=load_module();path=FIXTURES/"valid"/"compact-fully-paid.json";base=json.loads(path.read_text(encoding="utf-8"));authority,digest=evidence_authority(path,module)
        record=json.loads(json.dumps(base));record["evidence_inventory"][0].update({"artifact_id":"FAKE","artifact_sha256":"4"*64,"validated":True})
        findings=module.validate_accounting(record,upstream_obligation_ids=["O1"],upstream_inventory_sha256=external_inventory_hash(path),evidence_authority=authority,evidence_authority_sha256=digest)
        self.assertEqual(findings[0]["failure_subcode"],"evidence-inventory-shape")
        record=json.loads(json.dumps(base));record["obligations"][0]["source_ids"].append("GHOST")
        findings=module.validate_accounting(record,upstream_obligation_ids=["O1"],upstream_inventory_sha256=external_inventory_hash(path),evidence_authority=authority,evidence_authority_sha256=digest)
        self.assertEqual(findings[0]["failure_subcode"],"source-inventory-join")


if __name__ == "__main__":
    unittest.main()
