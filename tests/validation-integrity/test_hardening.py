#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from assert_expected_rejection import assert_rejection  # noqa: E402
from check_model_smoke_escape_registry import (  # noqa: E402
    _event_hash,
    build_case,
    validate_registry as validate_escape_registry,
)
from check_validation_registry import _base_verdict, _expectation_for  # noqa: E402
from contract_validation import (  # noqa: E402
    PathCustodyError,
    SchemaDefinitionError,
    resolve_repo_path,
    validate_schema_subset,
)
from validation_registry import (  # noqa: E402
    hydrate_fixture,
    load_registry,
    materialize_fixture,
    read_json,
    sha256_file,
    snapshot_registry,
    validate_registry,
    validate_verdict,
)


class ValidationHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry()
        cls.base = hydrate_fixture(_base_verdict("04", "act_body_ref", "body-ref-missing"), root=ROOT)

    def assert_failure(self, findings, failure_class: str) -> None:
        self.assertTrue(findings, f"expected {failure_class}, but mutation was accepted")
        self.assertEqual(failure_class, findings[0].failure_class, findings[0])

    def test_hardening_inventory_has_same_stem_expectations(self) -> None:
        inventory = read_json("tests/validation-integrity/hardening-inventory.json")
        fixture_root = ROOT / "tests/validation-integrity/hardening/invalid"
        for case_id in inventory["invalid"]:
            with self.subTest(case_id=case_id):
                payload = fixture_root / f"{case_id}.json"
                expectation = fixture_root / f"{case_id}.expectation.json"
                self.assertTrue(payload.is_file())
                self.assertTrue(expectation.is_file())
                self.assertEqual(case_id + ".json", json.loads(expectation.read_text(encoding="utf-8"))["fixture"])

    def test_verdict_schema_and_semantic_mutations_fail(self) -> None:
        cases = []
        value = copy.deepcopy(self.base); value.pop("launch"); cases.append(("missing-launch", value, "schema_contract"))
        value = copy.deepcopy(self.base); value["checker_results"].append(copy.deepcopy(value["checker_results"][0])); cases.append(("duplicate-result", value, "duplicate_checker_result"))
        value = copy.deepcopy(self.base); value["checker_results"][0].pop("stdout_sha256"); cases.append(("missing-stdout", value, "schema_contract"))
        value = copy.deepcopy(self.base); value["artifacts"].append(copy.deepcopy(value["artifacts"][0])); cases.append(("duplicate-role", value, "duplicate_artifact_role"))
        value = copy.deepcopy(self.base); duplicate = copy.deepcopy(value["artifacts"][0]); duplicate["role"] = "duplicate-input"; value["artifacts"].append(duplicate); cases.append(("duplicate-path", value, "duplicate_artifact_path"))
        value = copy.deepcopy(self.base); value["aggregate_status"] = "PASS_STRUCTURAL"; cases.append(("pass-over-rejection", value, "aggregate_status_mismatch"))
        value = copy.deepcopy(self.base); value["checker_results"][0].update({"exit_category":"accepted", "diagnostic":None, "expectation_status":"ACCEPTED"}); cases.append(("accepted-exit-one", value, "result_tuple_invalid"))
        value = copy.deepcopy(self.base); value["checker_results"][0]["forbidden_artifact_readback"].append(copy.deepcopy(value["checker_results"][0]["forbidden_artifact_readback"][0])); cases.append(("duplicate-forbidden", value, "duplicate_forbidden_readback_path"))
        for name, verdict, failure_class in cases:
            with self.subTest(name=name):
                self.assert_failure(validate_verdict(verdict, self.registry, root=ROOT, verify_files=True), failure_class)

    def test_registry_schema_and_uniqueness_mutations_fail(self) -> None:
        cases = []
        value = copy.deepcopy(self.registry); value["unexpected"] = True; cases.append(("unexpected-root", value, "schema_contract"))
        value = copy.deepcopy(self.registry); value["checkers"][0].pop("structural_non_claims"); cases.append(("missing-nonclaims", value, "schema_contract"))
        value = copy.deepcopy(self.registry); value["profiles"][0]["requirements"][0].pop("required"); cases.append(("missing-required-flag", value, "schema_contract"))
        value = copy.deepcopy(self.registry); value["checkers"].append(copy.deepcopy(value["checkers"][0])); cases.append(("duplicate-checker", value, "duplicate_checker_id"))
        value = copy.deepcopy(self.registry); value["consumers"].append(copy.deepcopy(value["consumers"][0])); cases.append(("duplicate-consumer", value, "duplicate_consumer_id"))
        value = copy.deepcopy(self.registry); value["profiles"].append(copy.deepcopy(value["profiles"][0])); cases.append(("duplicate-profile", value, "duplicate_profile_id"))
        value = copy.deepcopy(self.registry); value["checkers"][1]["aliases"] = [value["checkers"][0]["aliases"][0]]; cases.append(("duplicate-alias", value, "duplicate_checker_alias"))
        for name, registry, failure_class in cases:
            with self.subTest(name=name):
                self.assert_failure(validate_registry(registry, root=ROOT, scan_repo=False), failure_class)

    def test_registry_decoding_rejects_recursive_duplicate_keys(self) -> None:
        canonical = (ROOT / "tools/validation-registry.json").read_text(encoding="utf-8")
        duplicate = canonical.replace(
            '"checker_id":"act-surface-syntax"',
            '"checker_id":"conflicting-id","checker_id":"act-surface-syntax"',
            1,
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            scratch = Path(temp)
            intact_path = scratch / "intact.json"
            duplicate_path = scratch / "duplicate.json"
            intact_path.write_text(canonical, encoding="utf-8")
            duplicate_path.write_text(duplicate, encoding="utf-8")
            self.assertEqual(self.registry, load_registry(intact_path.relative_to(ROOT), root=ROOT))
            self.assertEqual(self.registry, snapshot_registry(intact_path.relative_to(ROOT), root=ROOT).value)
            for loader in (load_registry, snapshot_registry):
                with self.subTest(loader=loader.__name__):
                    with self.assertRaisesRegex(ValueError, "duplicate JSON object key: checker_id"):
                        loader(duplicate_path.relative_to(ROOT), root=ROOT)
            verdict = copy.deepcopy(self.base)
            verdict["registry_path"] = duplicate_path.relative_to(ROOT).as_posix()
            verdict["registry_sha256"] = sha256_file(duplicate_path)
            self.assert_failure(
                validate_verdict(verdict, self.registry, root=ROOT, verify_files=True),
                "malformed_registry",
            )

    def test_escape_schema_and_event_identity_mutations_fail(self) -> None:
        value = build_case("scoped-no"); value["unexpected"] = True
        self.assert_failure(validate_escape_registry(value), "schema_contract")

        value = build_case("renewed-no")
        value["events"][0]["event_id"] = "event-duplicate"
        value["events"][0]["event_hash"] = _event_hash(value["events"][0])
        value["events"][1]["event_id"] = "event-duplicate"
        value["events"][1]["previous_event_hash"] = value["events"][0]["event_hash"]
        value["events"][1]["event_hash"] = _event_hash(value["events"][1])
        self.assert_failure(validate_escape_registry(value), "duplicate_event_id")

        value = build_case("renewed-no")
        value["events"][1]["event_hash"] = value["events"][0]["event_hash"]
        self.assert_failure(validate_escape_registry(value), "duplicate_event_hash")

    def test_outside_artifact_and_registry_object_split_fail(self) -> None:
        outside_artifact = ROOT / "../../outputs/Sol/11_checker_fixture_and_promotion_integrity_plan.md"
        self.assertTrue(outside_artifact.is_file())
        value = copy.deepcopy(self.base)
        value["artifacts"][1]["path"] = "../../outputs/Sol/11_checker_fixture_and_promotion_integrity_plan.md"
        value["artifacts"][1]["sha256"] = sha256_file(outside_artifact)
        value["checker_results"][0]["artifact_sha256"] = value["artifacts"][1]["sha256"]
        self.assert_failure(validate_verdict(value, self.registry, root=ROOT, verify_files=True), "path_custody")

        outside_registry = ROOT / "../daee-v45-tag/schema/hard-smoke-manifest.schema.json"
        self.assertTrue(outside_registry.is_file())
        value = copy.deepcopy(self.base)
        value["registry_path"] = "../daee-v45-tag/schema/hard-smoke-manifest.schema.json"
        value["registry_sha256"] = sha256_file(outside_registry)
        self.assert_failure(validate_verdict(value, self.registry, root=ROOT, verify_files=True), "path_custody")

    def test_common_resolver_rejects_traversal_and_absolute_paths(self) -> None:
        with self.assertRaises(PathCustodyError):
            resolve_repo_path(ROOT, "../daee-v45-tag/schema/hard-smoke-manifest.schema.json")
        with self.assertRaises(PathCustodyError):
            resolve_repo_path(ROOT, ROOT / "tools/validation-registry.json")

    def test_mutation_base_and_forbidden_artifact_escape_fail(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as inside_dir, tempfile.TemporaryDirectory() as outside_dir:
            inside = Path(inside_dir)
            outside = Path(outside_dir) / "base.json"
            outside.write_text(json.dumps(self.base), encoding="utf-8")
            mutation = inside / "mutation.json"
            mutation.write_text(json.dumps({"fixture_schema":"daee-validation-integrity-mutation-v1", "base":str(outside), "operations":[]}), encoding="utf-8")
            with self.assertRaises((PathCustodyError, ValueError)):
                materialize_fixture(mutation.relative_to(ROOT), root=ROOT)

        verdict = copy.deepcopy(self.base)
        expectation = _expectation_for(verdict)
        expectation["forbidden_artifacts"] = ["../daee-v45-tag/forbidden.json"]
        verdict["checker_results"][0]["forbidden_artifact_readback"] = [{"path":"../daee-v45-tag/forbidden.json", "exists":False}]
        self.assert_failure(assert_rejection(expectation, verdict, self.registry, root=ROOT, artifact_root=ROOT), "path_custody")

    def test_checker_and_consumer_source_escape_fail(self) -> None:
        outside = ROOT / "../daee-v45-tag/schema/hard-smoke-manifest.schema.json"
        value = copy.deepcopy(self.registry)
        value["checkers"][0]["source_path"] = "../daee-v45-tag/schema/hard-smoke-manifest.schema.json"
        value["checkers"][0]["source_sha256"] = sha256_file(outside)
        self.assert_failure(validate_registry(value, root=ROOT, scan_repo=False), "path_custody")

        value = copy.deepcopy(self.registry)
        value["consumers"] = [{"consumer_id":"outside-consumer", "source_path":"../daee-v45-tag/schema/hard-smoke-manifest.schema.json", "source_sha256":sha256_file(outside), "profile_id":"scorecard", "policy_source":"registry"}]
        self.assert_failure(validate_registry(value, root=ROOT, scan_repo=True), "path_custody")

    def test_symlink_escape_when_supported(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as inside_dir, tempfile.TemporaryDirectory() as outside_dir:
            link = Path(inside_dir) / "outside-link"
            target = Path(outside_dir) / "target.json"
            target.write_text("{}\n", encoding="utf-8")
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            relative = link.relative_to(ROOT)
            with self.assertRaises(PathCustodyError):
                resolve_repo_path(ROOT, relative, must_exist=True, expect_file=True)

    def test_negative_expectation_schema_requires_subcode(self) -> None:
        schema = json.loads((ROOT / "schema/negative-fixture-expectation.schema.json").read_text(encoding="utf-8"))
        expectation = json.loads((ROOT / "tests/validation-integrity/valid/right-reason-stage04.verdict.expectation.json").read_text(encoding="utf-8"))
        expectation.pop("expected_failure_subcode")
        issues = validate_schema_subset(expectation, schema)
        self.assertTrue(issues, "expectation without subcode was accepted")
        self.assertEqual("required", issues[0].keyword)

    def test_schema_subset_fails_closed_on_unknown_features_and_refs(self) -> None:
        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset({}, {"type":"object", "unevaluatedProperties":False})
        with self.assertRaises(SchemaDefinitionError):
            validate_schema_subset({}, {"$ref":"#/$defs/missing", "$defs":{}})


if __name__ == "__main__":
    unittest.main()
