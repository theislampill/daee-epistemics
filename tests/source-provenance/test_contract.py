#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
SCHEMA = ROOT / "schema" / "source-binding.schema.json"
MODULE = TOOLS / "source_provenance.py"
CHECKER = TOOLS / "check_source_provenance.py"
CASES = Path(__file__).with_name("contract-cases.json")
CARRIERS = (
    "docs/audits/v0.4.6.0-wip-andon-closure-ledger.json",
    "docs/audits/v0.4.6.0-wip-andon-contract-registry.json",
    "docs/audits/v0.4.6.0-wip-architecture-decisions.json",
    "docs/audits/v0.4.6.0-wip-state-capsule-v2-migration-ledger.json",
)


def _decoy_binding_overrides(case: dict[str, object]) -> dict[str, bytes]:
    operation = case["operations"][0]
    decoy_property = str(operation["decoy_property"])
    drift_carrier = str(operation["drift_carrier"])
    overrides: dict[str, bytes] = {}
    for carrier in CARRIERS:
        document = json.loads((ROOT / carrier).read_text(encoding="utf-8"))
        binding = document["source_binding"]
        augmented = {decoy_property: {"source_binding": binding}, **document}
        text = json.dumps(augmented, indent=2, ensure_ascii=False) + "\n"
        if carrier == drift_carrier:
            marker = '\n  "source_binding": '
            value_start = text.index(marker) + len(marker)
            _value, value_length = json.JSONDecoder().raw_decode(text[value_start:])
            compact = json.dumps(binding, sort_keys=False, separators=(",", ":"), ensure_ascii=False)
            text = text[:value_start] + compact + text[value_start + value_length :]
        overrides[carrier] = text.encode("utf-8")
    return overrides


class SourceProvenanceContractTests(unittest.TestCase):
    def test_contract_owners_exist_before_behavior_is_claimed(self) -> None:
        required = [SCHEMA, MODULE, CHECKER, CASES]
        missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
        self.assertEqual([], missing, f"missing source-binding owner paths: {missing}")

    def test_schema_forbids_self_referential_identity(self) -> None:
        if not SCHEMA.is_file():
            self.skipTest("source-binding schema owner is not implemented yet")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual("daee-source-binding-v1", schema["properties"]["schema"]["const"])
        encoded = json.dumps(schema, sort_keys=True)
        for forbidden in ("current_head", "current_tree", "carrier_hashes", "receipt_sha256"):
            self.assertNotIn(forbidden, encoded)

    def test_permanent_mutation_matrix(self) -> None:
        if not CHECKER.is_file():
            self.skipTest("source-provenance checker owner is not implemented yet")
        fixture = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual("daee-source-provenance-test-cases-v1", fixture["schema"])
        invalid_ids = {case["case_id"] for case in fixture["invalid_cases"]}
        required = {
            "legacy-source-head-present",
            "missing-source-binding",
            "divergent-source-binding",
            "migration-only-binding-drift",
            "carrier-set-omission",
            "carrier-set-duplication",
            "wrong-checkpoint-commit",
            "missing-checkpoint-object",
            "checkpoint-object-is-not-commit",
            "wrong-checkpoint-tree",
            "workflow-identity-drift",
            "duplicate-json-key",
            "current-head-laundering",
            "top-level-binding-byte-drift-hidden-by-preceding-decoy",
        }
        self.assertEqual(required, invalid_ids)
        proc = subprocess.run(
            [sys.executable, str(CHECKER), "--self-test"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("14 invalid", proc.stdout)
        self.assertIn("predecessor HEAD without receipt", proc.stdout)

    def test_preceding_nested_decoy_cannot_hide_top_level_binding_byte_drift(self) -> None:
        if str(TOOLS) not in sys.path:
            sys.path.insert(0, str(TOOLS))
        import source_provenance

        fixture = json.loads(CASES.read_text(encoding="utf-8"))
        case = next(
            item
            for item in fixture["invalid_cases"]
            if item["case_id"] == "top-level-binding-byte-drift-hidden-by-preceding-decoy"
        )
        verdict, findings = source_provenance.validate_tracked_only(
            root=ROOT,
            carrier_overrides=_decoy_binding_overrides(case),
        )
        self.assertTrue(findings, f"false pass accepted differently formatted top-level binding: {verdict}")
        self.assertEqual("source_binding_divergence", findings[0].failure_class)
        self.assertIn("v0.4.6.0-wip-state-capsule-v2-migration-ledger.json", findings[0].message)

    def test_tracked_only_never_claims_current_head_or_receipt(self) -> None:
        if not CHECKER.is_file():
            self.skipTest("source-provenance checker owner is not implemented yet")
        proc = subprocess.run(
            [sys.executable, str(CHECKER), "--tracked-only", "--explain"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        verdict = json.loads(proc.stdout)
        self.assertEqual("TRACKED_SOURCE_BINDING_VALID", verdict["status"])
        self.assertFalse(verdict["current_head_compared"])
        self.assertFalse(verdict["current_head_ancestry_checked"])
        self.assertFalse(verdict["external_receipt_validated"])
        self.assertFalse(verdict["strict_successor_proven"])
        self.assertFalse(verdict["terminal_claim"])


if __name__ == "__main__":
    unittest.main()
