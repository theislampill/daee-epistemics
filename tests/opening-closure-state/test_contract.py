from __future__ import annotations

import importlib.util
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent
MODULE = ROOT / "tools" / "closure_state_lib.py"


def upstream_universe(path: Path) -> dict:
    empty_names = {"vacuous-empty-complete.json", "opening-complete-before-execution.json"}
    name = "empty.json" if path.name in empty_names else "nonempty.json"
    return json.loads((FIXTURES / "upstream" / name).read_text(encoding="utf-8"))


def load_module():
    if not MODULE.exists():
        return None
    spec = importlib.util.spec_from_file_location("closure_state_lib", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OpeningClosureStateTests(unittest.TestCase):
    def test_truthful_open_and_truthful_closure(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "closure_state_lib implementation missing")
        for path in sorted((FIXTURES / "valid").glob("*.json")):
            trace = json.loads(path.read_text(encoding="utf-8"))
            universe = upstream_universe(path)
            with self.subTest(path=path.name):
                self.assertEqual(module.validate_trace(trace, upstream_universe=universe, upstream_inventory_sha256=module.canonical_universe_sha256(universe)), [])
                authority = {"upstream_universe":universe,"upstream_inventory_sha256":module.canonical_universe_sha256(universe)}
                self.assertEqual(module.derive_closure_decision(trace, **authority), trace["proposed_closure_claim"])
                self.assertEqual(module.build_closure_witness_projection(trace, **authority)["derived_closure_decision"], trace["proposed_closure_claim"])

    def test_closure_universe_cannot_self_authorize_from_trace_rows(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "closure_state_lib implementation missing")
        trace = json.loads((FIXTURES / "valid" / "truthful-final-closure.json").read_text(encoding="utf-8"))
        findings = module.validate_trace(trace)
        self.assertTrue(findings, "closure trace self-authorized its own universe")
        self.assertEqual(findings[0]["failure_subcode"], "closure-universe-boundary-required")
        with self.assertRaises(module.ClosureUniverseAuthorityError) as derive_error:
            module.derive_closure_decision(trace)
        self.assertEqual(derive_error.exception.failure_subcode, "closure-universe-boundary-required")
        with self.assertRaises(module.ClosureUniverseAuthorityError) as projection_error:
            module.build_closure_witness_projection(trace)
        self.assertEqual(projection_error.exception.failure_subcode, "closure-universe-boundary-required")

    def test_hash_set_and_authoritative_empty_boundaries_are_distinct(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "closure_state_lib implementation missing")
        path = FIXTURES / "valid" / "truthful-final-closure.json"
        trace = json.loads(path.read_text(encoding="utf-8"))
        nonempty = upstream_universe(path)
        self.assertEqual(module.validate_trace(trace, upstream_universe=nonempty, upstream_inventory_sha256="0" * 64)[0]["failure_subcode"], "closure-universe-source-mismatch")
        with self.assertRaises(module.ClosureUniverseAuthorityError) as wrong_hash:
            module.derive_closure_decision(trace, upstream_universe=nonempty, upstream_inventory_sha256="0" * 64)
        self.assertEqual(wrong_hash.exception.failure_subcode, "closure-universe-source-mismatch")
        empty = json.loads((FIXTURES / "upstream" / "empty.json").read_text(encoding="utf-8"))
        self.assertEqual(module.validate_trace(trace, upstream_universe=empty, upstream_inventory_sha256=module.canonical_universe_sha256(empty))[0]["failure_subcode"], "closure-universe-mismatch")
        with self.assertRaises(module.ClosureUniverseAuthorityError) as wrong_set:
            module.build_closure_witness_projection(trace, upstream_universe=empty, upstream_inventory_sha256=module.canonical_universe_sha256(empty))
        self.assertEqual(wrong_set.exception.failure_subcode, "closure-universe-mismatch")
        empty_trace = json.loads((FIXTURES / "invalid" / "vacuous-empty-complete.json").read_text(encoding="utf-8"))
        empty_hash = module.canonical_universe_sha256(empty)
        empty_trace["authoritative_empty_universe"] = {"source_count":0,"source_inventory_sha256":empty_hash,"basis":"The independent prior-stage inventory is exactly empty."}
        self.assertEqual(module.validate_trace(empty_trace, upstream_universe=empty, upstream_inventory_sha256=empty_hash), [])

    def test_active_invalids_fail_for_pinned_reason(self) -> None:
        module = load_module()
        self.assertIsNotNone(module, "closure_state_lib implementation missing")
        for expectation_path in sorted((FIXTURES / "invalid").glob("*.expectation.json")):
            expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
            fixture = expectation_path.with_name(expectation["fixture"])
            universe = upstream_universe(fixture)
            findings = module.validate_trace(json.loads(fixture.read_text(encoding="utf-8")), upstream_universe=universe, upstream_inventory_sha256=module.canonical_universe_sha256(universe))
            with self.subTest(fixture=fixture.name):
                self.assertTrue(findings, "invalid closure trace survived")
                self.assertEqual(findings[0]["failure_class"], expectation["expected_failure_class"])
                self.assertEqual(findings[0]["failure_subcode"], expectation["expected_failure_subcode"])

    def test_diagnostics_and_obligations_fail_closed_independent_of_row_order(self) -> None:
        module=load_module();path=FIXTURES/"valid"/"truthful-final-closure.json";base=json.loads(path.read_text(encoding="utf-8"));universe=upstream_universe(path);digest=module.canonical_universe_sha256(universe)
        for operator,status in (("divergence","non-neutral"),("curl","non-null")):
            for prepend in (True,False):
                trace=copy.deepcopy(base);row={"operator":operator,"target":"B1","status":status,"basis_refs":["R1"],"delta_ref":"D0"}
                trace["diagnostics"].insert(0,row) if prepend else trace["diagnostics"].append(row)
                findings=module.validate_trace(trace,upstream_universe=universe,upstream_inventory_sha256=digest)
                with self.subTest(operator=operator,prepend=prepend): self.assertTrue(findings,"non-closed diagnostic was overwritten by row order")
        trace=copy.deepcopy(base);trace["diagnostics"][0]["target"]="GHOST"
        self.assertEqual(module.validate_trace(trace,upstream_universe=universe,upstream_inventory_sha256=digest)[0]["failure_subcode"],"diagnostic-target-unresolved")
        trace=copy.deepcopy(base);trace["diagnostics"].insert(0,{**trace["diagnostics"][0],"status":"non-neutral"})
        self.assertEqual(module.validate_trace(trace,upstream_universe=universe,upstream_inventory_sha256=digest)[0]["failure_subcode"],"diagnostic-conflict")
        for value,subcode in (("fabricated","obligation-disposition-invalid"),(None,"obligation-disposition-missing"),("held","complete-with-open-obligation")):
            trace=copy.deepcopy(base)
            if value is None: trace["owner_obligations"][0].pop("disposition")
            else: trace["owner_obligations"][0]["disposition"]=value
            findings=module.validate_trace(trace,upstream_universe=universe,upstream_inventory_sha256=digest)
            with self.subTest(disposition=value): self.assertEqual(findings[0]["failure_subcode"],subcode)


if __name__ == "__main__":
    unittest.main()
