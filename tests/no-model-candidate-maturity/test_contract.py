#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_no_model_candidate_maturity_verdict as builder  # noqa: E402
import check_no_model_candidate_maturity as checker  # noqa: E402
from a16_immutable_custody import canonical_json_bytes  # noqa: E402


IMPLEMENTATION_OWNER = "/root/task5_retention"
AUTHORIZATION_ISSUER = "/root"


def artifact_ref(path: str) -> dict[str, object]:
    raw = (ROOT / path).read_bytes()
    return {"path": path, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def content_hash(value: dict, field: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    raw = (json.dumps(unsigned, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def authorization_id(value: dict) -> str:
    unsigned = {key: copy.deepcopy(item) for key, item in value.items() if key != "authorization_id"}
    return hashlib.sha256(
        b"daee-task5-independent-review-authorization-v1\0" + canonical_json_bytes(unsigned)
    ).hexdigest()


def review_freeze(value: dict) -> str:
    frozen = {
        key: copy.deepcopy(value[key])
        for key in (
            "kind", "review_id", "source", "ci_receipt", "registry_template",
            "escape_schema", "escape_checker", "review_protocol",
        )
    }
    return hashlib.sha256(
        b"daee-task5-live-escape-review-freeze-v1\0" + canonical_json_bytes(frozen)
    ).hexdigest()


def review_claim_locator(authorization_path: str, scope: str, review_id: str) -> str:
    parent = PurePosixPath(authorization_path).parent
    review_digest = hashlib.sha256(review_id.encode("utf-8")).hexdigest()
    return (parent / "claims" / f"{scope}-{review_digest}.claim.json").as_posix()


class NoModelCandidateMaturityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.temp_root = Path(self.temporary.name)
        self.ci_receipt = artifact_ref("tests/ci-readback/valid/required-checks-bound-to-pushed-sha.json")
        self.receipt = json.loads((ROOT / self.ci_receipt["path"]).read_text(encoding="utf-8"))
        self.protocol = artifact_ref("tests/smoke-matrix/reviewed-five-smoke-protocol.json")
        self.template = artifact_ref("tests/model-smoke-escape/registry.json")
        self.review_document = self._review_document()
        self.review = self._write_json("live-escape-independent-review.json", self.review_document)
        live_path = self.temp_root / "live-escape-registry.json"
        builder.publish_live_escape_registry(
            ROOT,
            live_path,
            ci_receipt=self.ci_receipt,
            review_protocol=self.protocol,
            independent_review=self.review,
            allow_test_fixture=True,
        )
        self.live_escape = artifact_ref(live_path.relative_to(ROOT).as_posix())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_json(self, name: str, value: dict) -> dict[str, object]:
        path = self.temp_root / name
        path.write_bytes((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        return artifact_ref(path.relative_to(ROOT).as_posix())

    def _source_identity(self) -> dict[str, str]:
        return {
            "repository": self.receipt["repository"]["full_name"],
            "remote_url": self.receipt["repository"]["remote_url"],
            "branch": self.receipt["repository"]["branch"],
            "ref": self.receipt["repository"]["ref"],
            "commit_sha": self.receipt["source"]["commit_sha"],
            "tree_oid": self.receipt["source"]["tree_oid"],
        }

    def _review_document(self) -> dict:
        value = {
            "schema": "daee-no-model-candidate-maturity-v1",
            "kind": "live-escape-independent-review",
            "review_id": "live-escape-fixture-review",
            "verdict": "ACCEPT",
            "accountable_owner": IMPLEMENTATION_OWNER,
            "independent_reviewer": "/root/task5_live_escape_reviewer",
            "source": self._source_identity(),
            "ci_receipt": self.ci_receipt,
            "registry_template": self.template,
            "escape_schema": artifact_ref("schema/model-smoke-escape.schema.json"),
            "escape_checker": artifact_ref("tools/check_model_smoke_escape_registry.py"),
            "review_protocol": self.protocol,
            "independent_from_owner": True,
            "reviewed_at": "2026-07-12T12:22:00Z",
            "terminal_claim": False,
            "model_execution_authorized": False,
            "non_claims": [
                "escape review is not candidate maturity",
                "escape review does not authorize model execution",
                "escape review is not owner acceptance",
            ],
        }
        authorization = {
            "schema": "daee-task5-independent-review-authorization-v1",
            "authorization_id": "",
            "issuer_identity": AUTHORIZATION_ISSUER,
            "implementation_owner_identity": IMPLEMENTATION_OWNER,
            "reviewer_identity": value["independent_reviewer"],
            "scope": "live-escape-review",
            "review_id": value["review_id"],
            "source": copy.deepcopy(value["source"]),
            "candidate": None,
            "freeze_sha256": review_freeze(value),
            "consumption_claim_path": review_claim_locator(
                (self.temp_root / "live-escape-review-authorization.json").relative_to(ROOT).as_posix(),
                "live-escape-review",
                value["review_id"],
            ),
            "issued_at": "2026-07-12T12:21:00Z",
            "one_use": True,
            "owner_acceptance": False,
            "model_execution_authorized": False,
            "terminal_claim": False,
        }
        authorization["authorization_id"] = authorization_id(authorization)
        self.review_authorization_document = authorization
        self.review_authorization = self._write_json("live-escape-review-authorization.json", authorization)
        value["review_authorization_id"] = authorization["authorization_id"]
        value["review_authorization"] = self.review_authorization
        value["review_sha256"] = content_hash(value, "review_sha256")
        return value

    def _assert_review_authorization_rejected(
        self,
        label: str,
        mutate_authorization=None,
        mutate_review=None,
    ) -> None:
        authorization = copy.deepcopy(self.review_authorization_document)
        review = copy.deepcopy(self.review_document)
        if mutate_authorization is not None:
            mutate_authorization(authorization)
            authorization["authorization_id"] = authorization_id(authorization)
        auth_ref = self._write_json(f"{label}-authorization.json", authorization)
        review["review_authorization_id"] = authorization["authorization_id"]
        review["review_authorization"] = auth_ref
        if mutate_review is not None:
            mutate_review(review)
        review["review_sha256"] = content_hash(review, "review_sha256")
        review_ref = self._write_json(f"{label}-review.json", review)
        with self.assertRaisesRegex(ValueError, "authorization|owner|reviewer|identity|source|freeze|timestamp|one.use|review"):
            builder.build_live_escape_registry(
                ROOT,
                ci_receipt=self.ci_receipt,
                review_protocol=self.protocol,
                independent_review=review_ref,
                allow_test_fixture=True,
            )

    def source_inputs(self) -> dict[str, object]:
        return {
            "ci_receipt": self.ci_receipt,
            "tracked_source_binding": artifact_ref("docs/audits/v0.4.6.0-wip-andon-closure-ledger.json"),
            "registries": {
                "input": artifact_ref("tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json"),
                "validation": artifact_ref("tools/validation-registry.json"),
                "producer": artifact_ref("tools/producer-contract-registry.json"),
                "escape": self.live_escape,
                "review_protocol": self.protocol,
            },
            "live_escape_review": self.review,
            "closure_evidence": {
                "closure_ledger": artifact_ref("docs/audits/v0.4.6.0-wip-andon-closure-ledger.json"),
                "contract_registry": artifact_ref("docs/audits/v0.4.6.0-wip-andon-contract-registry.json"),
                "architecture_ledger": artifact_ref("docs/audits/v0.4.6.0-wip-architecture-decisions.json"),
            },
        }

    def test_source_preflight_is_derived_create_once_and_live_validated(self) -> None:
        out = self.temp_root / "source-preflight.json"
        verdict = builder.publish_source_preflight(ROOT, self.source_inputs(), out, allow_test_fixture=True)
        self.assertEqual("NO_MODEL_SOURCE_PREFLIGHT_GREEN", verdict["status"])
        self.assertEqual(self.receipt["source_binding"], verdict["source_binding"])
        self.assertFalse(verdict["terminal_claim"])
        self.assertFalse(verdict["model_execution_authorized"])
        self.assertEqual([], checker.validate_verdict(verdict, root=ROOT, allow_test_fixture=True))
        with self.assertRaisesRegex(ValueError, "create-once|already exists|replay"):
            builder.publish_source_preflight(ROOT, self.source_inputs(), out, allow_test_fixture=True)

    def test_source_preflight_rejects_receipt_hash_drift(self) -> None:
        inputs = self.source_inputs()
        inputs["ci_receipt"]["sha256"] = "0" * 64  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "ci_receipt.*hash"):
            builder.build_source_preflight(ROOT, inputs, allow_test_fixture=True)

    def test_source_preflight_rejects_wrong_binding_carrier(self) -> None:
        inputs = self.source_inputs()
        inputs["tracked_source_binding"] = artifact_ref("docs/audits/v0.4.6.0-wip-andon-contract-registry.json")
        with self.assertRaisesRegex(ValueError, "binding.*canonical"):
            builder.build_source_preflight(ROOT, inputs, allow_test_fixture=True)

    def test_source_preflight_rejects_carrier_identity_drift(self) -> None:
        verdict = builder.build_source_preflight(ROOT, self.source_inputs(), allow_test_fixture=True)
        verdict["tracked_source_binding"]["sha256"] = "0" * 64
        verdict["verdict_sha256"] = content_hash(verdict, "verdict_sha256")
        findings = checker.validate_verdict(verdict, root=ROOT, allow_test_fixture=True)
        self.assertTrue(findings)
        self.assertEqual("source_binding", findings[0].failure_class)

    def test_source_preflight_rejects_source_binding_drift(self) -> None:
        verdict = builder.build_source_preflight(ROOT, self.source_inputs(), allow_test_fixture=True)
        verdict["source_binding"]["raw_sha256"] = "0" * 64
        verdict["verdict_sha256"] = content_hash(verdict, "verdict_sha256")
        findings = checker.validate_verdict(verdict, root=ROOT, allow_test_fixture=True)
        self.assertTrue(findings)
        self.assertEqual("source_binding", findings[0].failure_class)

    def test_source_preflight_rejects_role_substitution(self) -> None:
        inputs = self.source_inputs()
        substitute = artifact_ref("schema/model-smoke-escape.schema.json")
        inputs["registries"] = {key: substitute for key in inputs["registries"]}  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "canonical|role"):
            builder.build_source_preflight(ROOT, inputs, allow_test_fixture=True)

    def test_source_preflight_rejects_illustrative_escape_registry(self) -> None:
        inputs = self.source_inputs()
        inputs["registries"]["escape"] = self.template  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "LIVE_EVIDENCE|illustrative"):
            builder.build_source_preflight(ROOT, inputs, allow_test_fixture=True)

    def test_source_preflight_rejects_different_create_once_replay(self) -> None:
        out = self.temp_root / "source-preflight.json"
        builder.publish_source_preflight(ROOT, self.source_inputs(), out, allow_test_fixture=True)
        changed = self.source_inputs()
        changed["tracked_source_binding"]["sha256"] = "0" * 64  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "create-once|different|hash"):
            builder.publish_source_preflight(ROOT, changed, out, allow_test_fixture=True)

    def test_live_escape_registry_is_receipt_and_review_bound(self) -> None:
        value = json.loads((ROOT / self.live_escape["path"]).read_text(encoding="utf-8"))
        self.assertEqual("LIVE_EVIDENCE", value["registry_role"])
        self.assertEqual(
            [],
            checker.validate_live_escape_registry(
                value,
                root=ROOT,
                ci_receipt=self.ci_receipt,
                review_protocol=self.protocol,
                independent_review=self.review,
                allow_test_fixture=True,
            ),
        )

    def test_production_builder_rejects_tracked_ci_test_fixture(self) -> None:
        with self.assertRaisesRegex(ValueError, "test fixture|test-owned"):
            builder.build_live_escape_registry(
                ROOT,
                ci_receipt=self.ci_receipt,
                review_protocol=self.protocol,
                independent_review=self.review,
            )

    def test_production_builder_rejects_relocated_structural_ci_fixture(self) -> None:
        run_root = ROOT / ".IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5"
        with tempfile.TemporaryDirectory(dir=run_root) as tmp:
            temp_root = Path(tmp)
            receipt_path = temp_root / "relocated-receipt.json"
            receipt_path.write_bytes((ROOT / self.ci_receipt["path"]).read_bytes())
            relocated_receipt = artifact_ref(receipt_path.relative_to(ROOT).as_posix())
            review = copy.deepcopy(self.review_document)
            review["ci_receipt"] = relocated_receipt
            review["review_sha256"] = content_hash(review, "review_sha256")
            review_path = temp_root / "relocated-review.json"
            review_path.write_bytes((json.dumps(review, sort_keys=True, separators=(",", ":")) + "\n").encode())
            relocated_review = artifact_ref(review_path.relative_to(ROOT).as_posix())
            with self.assertRaisesRegex(ValueError, "locator|commit|Git"):
                builder.build_live_escape_registry(
                    ROOT,
                    ci_receipt=relocated_receipt,
                    review_protocol=self.protocol,
                    independent_review=relocated_review,
                )

    def test_live_escape_registry_rejects_fabricated_review_source(self) -> None:
        review = copy.deepcopy(self.review_document)
        review["source"]["commit_sha"] = "9" * 40
        review["review_sha256"] = content_hash(review, "review_sha256")
        bad_review = self._write_json("fabricated-source-review.json", review)
        with self.assertRaisesRegex(ValueError, "source|receipt"):
            builder.build_live_escape_registry(
                ROOT,
                ci_receipt=self.ci_receipt,
                review_protocol=self.protocol,
                independent_review=bad_review,
                allow_test_fixture=True,
            )

    def test_live_escape_review_requires_canonical_owner_issued_one_use_authorization(self) -> None:
        cases = (
            ("reviewer-whitespace", lambda a: a.__setitem__("reviewer_identity", " /root/task5_live_escape_reviewer"), lambda r: r.__setitem__("independent_reviewer", " /root/task5_live_escape_reviewer")),
            ("reviewer-case", lambda a: a.__setitem__("reviewer_identity", "/root/Task5_live_escape_reviewer"), lambda r: r.__setitem__("independent_reviewer", "/root/Task5_live_escape_reviewer")),
            ("reviewer-unicode", lambda a: a.__setitem__("reviewer_identity", "/root/task5_live_escape_reviewеr"), lambda r: r.__setitem__("independent_reviewer", "/root/task5_live_escape_reviewеr")),
            ("invented-owner", lambda a: a.__setitem__("implementation_owner_identity", "/root/invented_owner"), lambda r: r.__setitem__("accountable_owner", "/root/invented_owner")),
            ("owner-relabel", None, lambda r: r.__setitem__("accountable_owner", "/root/task5_retention_alias")),
            ("reviewer-mismatch", None, lambda r: r.__setitem__("independent_reviewer", "/root/different_reviewer")),
            ("authorization-replay", None, lambda r: r.__setitem__("review_id", "replayed-review-id")),
            ("source-tree-drift", lambda a: a["source"].__setitem__("tree_oid", "9" * 40), None),
            ("freeze-drift", lambda a: a.__setitem__("freeze_sha256", "9" * 64), None),
            ("time-order", lambda a: a.__setitem__("issued_at", "2026-07-12T12:23:00Z"), None),
            ("not-one-use", lambda a: a.__setitem__("one_use", False), None),
        )
        for label, mutate_authorization, mutate_review in cases:
            with self.subTest(label=label):
                self._assert_review_authorization_rejected(label, mutate_authorization, mutate_review)

    def test_live_escape_review_rejects_same_authorization_and_review_id_with_changed_reviewed_at(self) -> None:
        claim_path = ROOT / self.review_authorization_document["consumption_claim_path"]
        self.assertTrue(claim_path.is_file())
        claim_before = claim_path.read_bytes()
        changed = copy.deepcopy(self.review_document)
        changed["reviewed_at"] = "2026-07-12T12:22:01Z"
        changed["review_sha256"] = content_hash(changed, "review_sha256")
        changed_review = self._write_json("changed-reviewed-at-review.json", changed)
        with self.assertRaisesRegex(ValueError, "authorization|claim|consum|replay|review"):
            builder.build_live_escape_registry(
                ROOT,
                ci_receipt=self.ci_receipt,
                review_protocol=self.protocol,
                independent_review=changed_review,
                allow_test_fixture=True,
            )
        self.assertEqual(claim_before, claim_path.read_bytes())

    def test_live_escape_review_rejects_duplicated_authorization_locator(self) -> None:
        claim_path = ROOT / self.review_authorization_document["consumption_claim_path"]
        claim_before = claim_path.read_bytes()
        duplicate_authorization = self._write_json(
            "duplicate-live-escape-review-authorization.json",
            self.review_authorization_document,
        )
        changed = copy.deepcopy(self.review_document)
        changed["review_authorization"] = duplicate_authorization
        changed["review_sha256"] = content_hash(changed, "review_sha256")
        duplicate_review = self._write_json("duplicate-authorization-locator-review.json", changed)
        with self.assertRaisesRegex(ValueError, "authorization|claim|consum|collision|locator|replay"):
            builder.build_live_escape_registry(
                ROOT,
                ci_receipt=self.ci_receipt,
                review_protocol=self.protocol,
                independent_review=duplicate_review,
                allow_test_fixture=True,
            )
        self.assertEqual(claim_before, claim_path.read_bytes())

    def test_live_escape_review_consumption_claim_collision_is_not_overwritten(self) -> None:
        claim_path = ROOT / self.review_authorization_document["consumption_claim_path"]
        collision = b'{"collision":true}\n'
        claim_path.write_bytes(collision)
        with self.assertRaisesRegex(ValueError, "authorization|claim|consum|collision|drift|replay"):
            builder.build_live_escape_registry(
                ROOT,
                ci_receipt=self.ci_receipt,
                review_protocol=self.protocol,
                independent_review=self.review,
                allow_test_fixture=True,
            )
        self.assertEqual(collision, claim_path.read_bytes())

    def test_live_escape_registry_rejects_arbitrary_protocol_role(self) -> None:
        review = copy.deepcopy(self.review_document)
        review["review_protocol"] = artifact_ref("schema/model-smoke-escape.schema.json")
        review["review_sha256"] = content_hash(review, "review_sha256")
        bad_review = self._write_json("arbitrary-protocol-review.json", review)
        with self.assertRaisesRegex(ValueError, "protocol.*canonical|review"):
            builder.build_live_escape_registry(
                ROOT,
                ci_receipt=self.ci_receipt,
                review_protocol=review["review_protocol"],
                independent_review=bad_review,
                allow_test_fixture=True,
            )

    def test_live_escape_registry_rejects_unstructured_review_bytes(self) -> None:
        review = artifact_ref(
            ".IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5/reviews/task4-candidate-custody-independent-review.md"
        )
        with self.assertRaisesRegex(ValueError, "review.*JSON|schema"):
            builder.build_live_escape_registry(
                ROOT,
                ci_receipt=self.ci_receipt,
                review_protocol=self.protocol,
                independent_review=review,
                allow_test_fixture=True,
            )

    def test_live_escape_registry_rejects_sentinel_scope(self) -> None:
        value = json.loads((ROOT / self.live_escape["path"]).read_text(encoding="utf-8"))
        value["escapes"][0]["scope"]["source_sha256"] = "1" * 64
        findings = checker.validate_live_escape_registry(
            value,
            root=ROOT,
            ci_receipt=self.ci_receipt,
            review_protocol=self.protocol,
            independent_review=self.review,
            allow_test_fixture=True,
        )
        self.assertTrue(findings)
        self.assertEqual("escape_scope", findings[0].failure_class)

    def test_live_escape_registry_rejects_contradictory_nonclaims(self) -> None:
        value = json.loads((ROOT / self.live_escape["path"]).read_text(encoding="utf-8"))
        value["structural_non_claims"] = [
            "candidate is mature",
            "model execution authorized",
            "owner acceptance recorded",
        ]
        findings = checker.validate_live_escape_registry(
            value,
            root=ROOT,
            ci_receipt=self.ci_receipt,
            review_protocol=self.protocol,
            independent_review=self.review,
            allow_test_fixture=True,
        )
        self.assertTrue(findings)

    def test_live_escape_registry_rejects_authorization_replay_before_second_publication(self) -> None:
        out = self.temp_root / "second-live-escape-registry.json"
        with self.assertRaisesRegex(ValueError, "create-once|replay|already exists"):
            builder.publish_live_escape_registry(
                ROOT,
                out,
                ci_receipt=self.ci_receipt,
                review_protocol=self.protocol,
                independent_review=self.review,
                allow_test_fixture=True,
            )
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
