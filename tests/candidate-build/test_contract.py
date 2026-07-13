#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import check_smoke_matrix_manifest as contract  # noqa: E402
import build_candidate_package_record as builder  # noqa: E402
from a16_immutable_custody import canonical_json_bytes  # noqa: E402


SHA = "a" * 64
GIT = "b" * 40


def canonical_sha(value: dict, field: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    raw = (json.dumps(unsigned, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def ref(path: str, digest: str = SHA) -> dict[str, str]:
    return {"path": path, "sha256": digest}


def write_ref(root: Path, relative: str, payload: bytes) -> dict[str, str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return ref(relative, hashlib.sha256(payload).hexdigest())


def authorization() -> dict:
    value = {
        "schema": "daee-smoke-matrix-v1",
        "kind": "candidate-build-authorization",
        "authorization_id": "candidate-build-fixture",
        "action": "BUILD_EXECUTION_MINI_CANDIDATE",
        "one_use": True,
        "issued_at": "2026-07-12T00:00:00Z",
        "expires_at": "2026-07-13T00:00:00Z",
        "branch": "codex/v0.4.6.0-runtime-footprint-b10",
        "ref": "refs/heads/codex/v0.4.6.0-runtime-footprint-b10",
        "source_commit": GIT,
        "source_commit_receipt": ref("source-receipt.json"),
        "ci_readback": ref("ci-readback.json"),
        "source_preflight": ref("source-preflight.json"),
        "package_profile": "execution-mini",
        "candidate_id": "candidate-fixture",
        "custody_root": "candidate-custody",
        "candidate_root": "candidate-custody/candidates/candidate-fixture",
        "claim_path": "candidate-custody/claims/candidate-build-fixture.claim.json",
        "archive_name": "daee-epistemics-v0.4.6.0-execution-mini.skill.zip",
        "max_archive_bytes": 1048576,
        "max_extracted_bytes": 1048576,
        "max_archive_entries": 100,
        "input_registry": ref("tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json"),
        "validation_registry": ref("tools/validation-registry.json"),
        "producer_registry": ref("tools/producer-contract-registry.json"),
        "escape_registry": ref("tests/model-smoke-escape/registry.json"),
        "usage_writer": ref("tools/campaign_usage_ledger.py"),
        "review_protocol": ref("tests/smoke-matrix/reviewed-five-smoke-protocol.json"),
        "model_execution_authorized": False,
        "terminal_claim": False,
        "non_claims": [
            "candidate build is not candidate maturity",
            "candidate build is not model execution authorization",
            "candidate build is not owner acceptance",
        ],
    }
    value["authorization_sha256"] = canonical_sha(value, "authorization_sha256")
    return value


def build_claim(auth: dict) -> dict:
    value = {
        "schema": "daee-smoke-matrix-v1",
        "kind": "candidate-build-claim",
        "claim_id": "candidate-build-fixture-claim",
        "authorization_id": auth["authorization_id"],
        "authorization_sha256": auth["authorization_sha256"],
        "candidate_id": auth["candidate_id"],
        "claimed_at": "2026-07-12T00:01:00Z",
        "one_use": True,
        "terminal_claim": False,
    }
    value["claim_sha256"] = canonical_sha(value, "claim_sha256")
    return value


def candidate_record(auth: dict, claim: dict) -> dict:
    value = {
        "schema": "daee-smoke-matrix-v1",
        "kind": "candidate-package-record-bound",
        "candidate_id": auth["candidate_id"],
        "status": "READY_UNUSED",
        "branch": auth["branch"],
        "ref": auth["ref"],
        "source_commit": auth["source_commit"],
        "source_commit_receipt": auth["source_commit_receipt"],
        "ci_readback": auth["ci_readback"],
        "source_preflight": auth["source_preflight"],
        "package_profile": "execution-mini",
        "archive": {"path": auth["archive_name"], "sha256": SHA, "byte_count": 100},
        "extraction_receipt": ref("candidate-extraction-receipt.json"),
        "extracted_root": "extracted",
        "tree_digest_algorithm": "daee-tree-sha256-v1",
        "extracted_tree_sha256": SHA,
        "extracted_file_count": 4,
        "build_manifest": ref("extracted/build-manifest.json"),
        "skill_root": ref("extracted/SKILL.md"),
        "compiled_module_map": ref("extracted/compiled-module-map.json"),
        "cold_law_manifest": ref("extracted/cold-law-manifest.json"),
        "input_registry": auth["input_registry"],
        "validation_registry": auth["validation_registry"],
        "producer_registry": auth["producer_registry"],
        "escape_registry": auth["escape_registry"],
        "usage_writer": auth["usage_writer"],
        "review_protocol": auth["review_protocol"],
        "custody_root": auth["custody_root"],
        "candidate_root": auth["candidate_root"],
        "readiness_marker_path": "candidate-readiness.json",
        "build_authorization": ref("candidate-build-authorization.json"),
        "build_claim": ref("candidate-build-claim.json"),
        "build_authorization_sha256": auth["authorization_sha256"],
        "build_claim_sha256": claim["claim_sha256"],
        "claim_status": "UNCLAIMED",
        "promotion_eligible": False,
        "model_execution_authorized": False,
        "invalidation_conditions": [
            "source or CI receipt drift",
            "candidate byte drift",
            "registry or review protocol drift",
        ],
        "non_claims": [
            "READY_UNUSED is not candidate maturity",
            "READY_UNUSED is not model execution authorization",
            "READY_UNUSED is not owner acceptance",
        ],
    }
    value["record_sha256"] = canonical_sha(value, "record_sha256")
    return value


def matrix_authorization(record: dict) -> dict:
    value = {
        "schema": "daee-smoke-matrix-v1",
        "kind": "matrix-authorization",
        "authorization_id": "matrix-fixture",
        "action": "RUN_REVIEWED_FIVE_SMOKE",
        "one_use": True,
        "candidate_id": record["candidate_id"],
        "candidate_record": ref("candidate-record.json", record["record_sha256"]),
        "candidate_readiness": ref("candidate-readiness.json"),
        "candidate_maturity": ref("candidate-maturity.json"),
        "source_commit_receipt": record["source_commit_receipt"],
        "package_sha256": record["archive"]["sha256"],
        "package_tree_sha256": record["extracted_tree_sha256"],
        "tree_digest_algorithm": "daee-tree-sha256-v1",
        "input_registry": record["input_registry"],
        "review_protocol": record["review_protocol"],
        "producer_model": "gpt-5.5",
        "producer_reasoning_effort": "high",
        "cold_review_model": "gpt-5.6-sol",
        "cold_review_reasoning_effort": "xhigh",
        "optional_opus_authorized": False,
        "paid_execution_authorized": False,
    }
    value["authorization_sha256"] = canonical_sha(value, "authorization_sha256")
    return value


def matrix_claim(auth: dict) -> dict:
    value = {
        "schema": "daee-smoke-matrix-v1",
        "kind": "matrix-authorization-claim",
        "claim_id": "matrix-fixture-claim",
        "authorization_id": auth["authorization_id"],
        "authorization_sha256": auth["authorization_sha256"],
        "candidate_id": auth["candidate_id"],
        "claimed_at": "2026-07-12T00:02:00Z",
        "one_use": True,
    }
    value["claim_sha256"] = canonical_sha(value, "claim_sha256")
    return value


class CandidateBuildContractTests(unittest.TestCase):
    def test_tracked_review_protocol_is_exact_and_non_authorizing(self) -> None:
        path = ROOT / "tests/smoke-matrix/reviewed-five-smoke-protocol.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual([], contract.validate_manifest(value, root=ROOT))
        self.assertEqual(5, value["producer"]["cohort_size"])
        self.assertEqual(5, value["cold_review"]["cohort_size"])
        self.assertFalse(value["producer"]["paid_execution_authorized"])
        self.assertFalse(value["cold_review"]["paid_execution_authorized"])
        self.assertFalse(value["optional_opus"]["authorized"])

    def test_bound_candidate_family_validates(self) -> None:
        auth = authorization()
        claim = build_claim(auth)
        record = candidate_record(auth, claim)
        for value in (auth, claim, record):
            with self.subTest(kind=value["kind"]):
                self.assertEqual([], contract.validate_manifest(value, root=ROOT))

    def test_hash_drift_and_legacy_algorithm_fail_closed(self) -> None:
        auth = authorization()
        bad_auth = {**auth, "source_commit": "c" * 40}
        self.assertEqual(
            "authorization_content_hash",
            contract.validate_manifest(bad_auth, root=ROOT)[0]["failure_class"],
        )
        claim = build_claim(auth)
        record = candidate_record(auth, claim)
        legacy = {**record, "tree_digest_algorithm": "legacy-json-row-v0"}
        self.assertEqual(
            "schema_contract",
            contract.validate_manifest(legacy, root=ROOT)[0]["failure_class"],
        )
        drift = {**record, "candidate_id": "different"}
        self.assertEqual(
            "candidate_record_hash",
            contract.validate_manifest(drift, root=ROOT)[0]["failure_class"],
        )

    def test_matrix_authorization_family_binds_candidate_and_protocol(self) -> None:
        build_auth = authorization()
        record = candidate_record(build_auth, build_claim(build_auth))
        auth = matrix_authorization(record)
        claim = matrix_claim(auth)
        self.assertEqual([], contract.validate_manifest(auth, root=ROOT))
        self.assertEqual([], contract.validate_manifest(claim, root=ROOT))
        drift = {**auth, "package_tree_sha256": "f" * 64}
        self.assertEqual(
            "authorization_content_hash",
            contract.validate_manifest(drift, root=ROOT)[0]["failure_class"],
        )

    def _fake_build_authorization(self, root: Path) -> tuple[Path, dict]:
        auth = authorization()
        auth.update(
            custody_root="custody",
            candidate_root="custody/candidates/candidate-fixture",
            claim_path="custody/claims/candidate-build-fixture.claim.json",
            source_commit_receipt=write_ref(root, "evidence/source.json", b'{"status":"green"}\n'),
            ci_readback=write_ref(root, "evidence/ci.json", b'{"status":"green"}\n'),
            source_preflight=write_ref(root, "evidence/preflight.json", b'{"status":"green"}\n'),
            input_registry=write_ref(root, "registries/cases.json", b'{"cases":5}\n'),
            validation_registry=write_ref(root, "registries/validation.json", b'{"checkers":1}\n'),
            producer_registry=write_ref(root, "registries/producer.json", b'{"producer":1}\n'),
            escape_registry=write_ref(root, "registries/escape.json", b'{"escapes":0}\n'),
            usage_writer=write_ref(root, "tools/usage.py", b"# usage\n"),
            review_protocol=write_ref(root, "registries/review.json", b'{"protocol":"reviewed-five"}\n'),
        )
        auth["authorization_sha256"] = canonical_sha(auth, "authorization_sha256")
        path = root / "custody/authorizations/candidate-build-fixture.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(canonical_json_bytes(auth))
        return path, auth

    @staticmethod
    def _fake_archive(_root: Path, output: Path, profile: str = "execution-mini") -> tuple[int, str]:
        if profile != "execution-mini":
            raise AssertionError(profile)
        output.parent.mkdir(parents=True, exist_ok=True)
        files = {
            "SKILL.md": b"---\nname: fixture\n---\n",
            "build-manifest.json": b'{"schema":"fixture-build"}\n',
            "compiled-module-map.json": b'{"schema":"fixture-modules"}\n',
            "cold-law-manifest.json": b'{"schema":"fixture-cold-law"}\n',
        }
        with zipfile.ZipFile(output, "w") as archive:
            for name, payload in files.items():
                archive.writestr(name, payload)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        return len(files), digest.upper()

    def test_authorized_build_is_atomic_bound_and_one_use(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            auth_path, auth = self._fake_build_authorization(root)
            record = builder.build_authorized_candidate(
                repo_root=root,
                authorization_path=auth_path,
                now=datetime(2026, 7, 12, 0, 2, tzinfo=timezone.utc),
                archive_builder=self._fake_archive,
            )
            candidate_root = root / auth["candidate_root"]
            self.assertTrue(candidate_root.is_dir())
            self.assertEqual("READY_UNUSED", record["status"])
            self.assertEqual("daee-tree-sha256-v1", record["tree_digest_algorithm"])
            self.assertEqual([], contract.validate_manifest(record, root=ROOT))
            self.assertEqual(
                canonical_json_bytes(record),
                (candidate_root / "candidate-record.json").read_bytes(),
            )
            readiness = json.loads(
                (candidate_root / record["readiness_marker_path"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual("candidate-readiness-marker", readiness["kind"])
            self.assertEqual(record["record_sha256"], readiness["record_sha256"])
            self.assertEqual([], contract.validate_manifest(readiness, root=ROOT))
            self.assertEqual(
                record,
                builder.validate_candidate_readiness(candidate_root, repo_root=root),
            )
            extraction = json.loads(
                (candidate_root / "candidate-extraction-receipt.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual("extracted", extraction["destination"])
            self.assertTrue((candidate_root / extraction["destination"]).is_dir())
            self.assertTrue((root / auth["claim_path"]).is_file())
            self.assertFalse(any(candidate_root.parent.glob(".candidate-fixture.staging-*")))
            with self.assertRaisesRegex(ValueError, "claim|exists|replay"):
                builder.build_authorized_candidate(
                    repo_root=root,
                    authorization_path=auth_path,
                    now=datetime(2026, 7, 12, 0, 3, tzinfo=timezone.utc),
                    archive_builder=self._fake_archive,
                )

    def test_reference_drift_fails_before_claim_or_candidate_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            auth_path, auth = self._fake_build_authorization(root)
            (root / auth["source_preflight"]["path"]).write_bytes(b"drift\n")
            with self.assertRaisesRegex(ValueError, "reference|hash|drift"):
                builder.build_authorized_candidate(
                    repo_root=root,
                    authorization_path=auth_path,
                    now=datetime(2026, 7, 12, 0, 2, tzinfo=timezone.utc),
                    archive_builder=self._fake_archive,
                )
            self.assertFalse((root / auth["claim_path"]).exists())
            self.assertFalse((root / auth["candidate_root"]).exists())

    def test_archive_drift_at_publication_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            auth_path, auth = self._fake_build_authorization(root)
            original = builder._rename_directory_noreplace
            final_destination = root / auth["candidate_root"]

            def drift_before_publish(source: Path, destination: Path) -> None:
                if destination == final_destination:
                    archive = next(source.glob("*.skill.zip"))
                    archive.write_bytes(archive.read_bytes() + b"drift")
                original(source, destination)

            with patch.object(builder, "_rename_directory_noreplace", drift_before_publish):
                with self.assertRaisesRegex(ValueError, "archive.*readback.*drift"):
                    builder.build_authorized_candidate(
                        repo_root=root,
                        authorization_path=auth_path,
                        now=datetime(2026, 7, 12, 0, 2, tzinfo=timezone.utc),
                        archive_builder=self._fake_archive,
                    )
            self.assertTrue((root / auth["claim_path"]).is_file())
            self.assertFalse(
                (root / auth["candidate_root"] / "candidate-readiness.json").exists()
            )

    def test_archive_mutation_between_extraction_receipt_and_record_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            auth_path, auth = self._fake_build_authorization(root)
            original = builder.publish_extraction_receipt

            def mutate_after_receipt(receipt: dict, output: Path) -> None:
                original(receipt, output)
                archive = next(output.parent.glob("*.skill.zip"))
                archive.write_bytes(archive.read_bytes() + b"mid-build drift")

            with patch.object(builder, "publish_extraction_receipt", mutate_after_receipt):
                with self.assertRaisesRegex(ValueError, "archive.*snapshot.*drift"):
                    builder.build_authorized_candidate(
                        repo_root=root,
                        authorization_path=auth_path,
                        now=datetime(2026, 7, 12, 0, 2, tzinfo=timezone.utc),
                        archive_builder=self._fake_archive,
                    )
            self.assertTrue((root / auth["claim_path"]).is_file())
            self.assertFalse((root / auth["candidate_root"]).exists())

    def test_mutation_during_readiness_publication_cannot_leave_live_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            auth_path, auth = self._fake_build_authorization(root)
            original = builder.atomic_publish_bytes

            def mutate_at_marker(path: Path, payload: bytes) -> None:
                if path.name == "candidate-readiness.json":
                    archive = next(path.parent.glob("*.skill.zip"))
                    archive.write_bytes(archive.read_bytes() + b"late drift")
                original(path, payload)

            with patch.object(builder, "atomic_publish_bytes", mutate_at_marker):
                with self.assertRaisesRegex(ValueError, "archive.*drift"):
                    builder.build_authorized_candidate(
                        repo_root=root,
                        authorization_path=auth_path,
                        now=datetime(2026, 7, 12, 0, 2, tzinfo=timezone.utc),
                        archive_builder=self._fake_archive,
                    )
            candidate_root = root / auth["candidate_root"]
            self.assertTrue(candidate_root.is_dir())
            self.assertFalse((candidate_root / "candidate-readiness.json").exists())
            with self.assertRaisesRegex(ValueError, "readiness"):
                builder.validate_candidate_readiness(candidate_root, repo_root=root)

    def test_mid_build_bound_reference_drift_is_rejected_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            auth_path, auth = self._fake_build_authorization(root)

            def mutate_reference(
                repo_root: Path, output: Path, profile: str = "execution-mini"
            ) -> tuple[int, str]:
                result = self._fake_archive(repo_root, output, profile)
                (root / auth["source_preflight"]["path"]).write_bytes(b"mid-build drift\n")
                return result

            with self.assertRaisesRegex(ValueError, "source_preflight.*hash drift"):
                builder.build_authorized_candidate(
                    repo_root=root,
                    authorization_path=auth_path,
                    now=datetime(2026, 7, 12, 0, 2, tzinfo=timezone.utc),
                    archive_builder=mutate_reference,
                )
            self.assertTrue((root / auth["claim_path"]).is_file())
            self.assertFalse((root / auth["candidate_root"]).exists())
            self.assertFalse(any((root / "custody/candidates").glob(".*.staging-*")))

    def test_authorized_archive_size_extracted_size_and_entry_limits_are_independent(self) -> None:
        cases = (
            ("max_archive_bytes", 1, "archive.*byte limit"),
            ("max_extracted_bytes", 1, "extracted.*byte limit"),
            ("max_archive_entries", 1, "archive.*entry limit"),
        )
        for field, value, marker in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                auth_path, auth = self._fake_build_authorization(root)
                auth[field] = value
                auth["authorization_sha256"] = canonical_sha(
                    auth, "authorization_sha256"
                )
                auth_path.write_bytes(canonical_json_bytes(auth))
                with self.assertRaisesRegex(ValueError, marker):
                    builder.build_authorized_candidate(
                        repo_root=root,
                        authorization_path=auth_path,
                        now=datetime(2026, 7, 12, 0, 2, tzinfo=timezone.utc),
                        archive_builder=self._fake_archive,
                    )
                self.assertTrue((root / auth["claim_path"]).is_file())
                self.assertFalse((root / auth["candidate_root"]).exists())


if __name__ == "__main__":
    unittest.main()
