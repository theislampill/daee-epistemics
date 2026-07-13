#!/usr/bin/env python3
"""Contract tests for A16 evidence-retention and cycle-export custody."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_evidence_retention_manifest as checker
import export_cycle_evidence_bundle as exporter
from a16_immutable_custody import canonical_json_bytes


SHA = "a" * 64
OID = "b" * 40


def ref(path: str, digest: str = SHA, byte_count: int = 1) -> dict:
    return {"path": path, "sha256": digest, "byte_count": byte_count}


def write_source_ref(root: Path, path: str, payload: bytes) -> dict:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return ref(path, hashlib.sha256(payload).hexdigest(), len(payload))


def content_hash(value: dict, field: str) -> str:
    unsigned = {key: copy.deepcopy(item) for key, item in value.items() if key != field}
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def write_authorization(path: Path, value: dict) -> None:
    value["authorization_sha256"] = content_hash(value, "authorization_sha256")
    path.write_bytes(canonical_json_bytes(value))


def authorization(temp: Path, *, kind: str = "observation-cycle-export") -> tuple[Path, dict]:
    source = temp / "source"
    (source / "raw").mkdir(parents=True)
    (source / "control").mkdir()
    (source / "raw/prompt.txt").write_bytes(b"retained raw prompt\n")
    (source / "control/finalizer.json").write_bytes(b'{"status":"PARTIAL"}\n')
    source_receipt = write_source_ref(source, "receipts/source-commit.json", b'{"status":"CI_SOURCE_GREEN"}\n')
    ci_readback = write_source_ref(source, "receipts/ci-readback.json", b'{"status":"CI_GREEN"}\n')
    candidate_record = write_source_ref(source, "candidates/candidate-fixture/candidate-record.json", b'{"status":"READY_UNUSED"}\n')
    candidate_readiness = write_source_ref(source, "candidates/candidate-fixture/candidate-readiness.json", b'{"status":"READY"}\n')
    custody = temp / "custody"
    export_id = "export-fixture-001"
    scope_id = "cycle-fixture-001"
    cycle = None
    cycle_claim = None
    final_path = f"candidates/candidate-fixture/retention/{export_id}"
    if kind == "candidate-readiness-final-manifest":
        scope_id = "candidate-fixture"
    else:
        cycle_claim = write_source_ref(source, "claims/cycle-fixture-001.json", b'{"status":"CLAIMED"}\n')
        cycle = {
            "cycle_id": scope_id,
            "cycle_claim": cycle_claim,
            "phase": "OBSERVATION" if kind == "observation-cycle-export" else "REVIEWED_FINAL",
        }
        final_path = f"cycles/{scope_id}/exports/{export_id}"
    value = {
        "schema": "daee-evidence-export-authorization-v1",
        "kind": "evidence-export-authorization",
        "manifest_kind": kind,
        "export_id": export_id,
        "scope_id": scope_id,
        "one_use": True,
        "issued_at": "2026-07-12T12:00:00Z",
        "exported_at": "2026-07-12T12:01:00Z",
        "source_root": str(source.resolve()),
        "evidence_custody_root": str(custody.resolve()),
        "staging_path": f".staging/{export_id}",
        "claim_path": f"claims/{export_id}.json",
        "final_path": final_path,
        "receipt_path": f"receipts/{export_id}.json",
        "pointer_path": f"pointers/{scope_id}/head.json",
        "expected_pointer_sha256": None,
        "source_identity": {
            "repository": "theislampill/daee-epistemics",
            "branch": "codex/v0.4.6.0-runtime-footprint-b10",
            "ref": "refs/heads/codex/v0.4.6.0-runtime-footprint-b10",
            "commit_sha": OID,
            "tree_sha": "c" * 40,
            "source_commit_receipt": source_receipt,
            "ci_readback": ci_readback,
        },
        "candidate_identity": {
            "candidate_id": "candidate-fixture",
            "candidate_record": candidate_record,
            "candidate_readiness": candidate_readiness,
            "package_sha256": "d" * 64,
            "package_tree_sha256": "e" * 64,
            "tree_digest_algorithm": "daee-tree-sha256-v1",
            "status": "READY_UNUSED",
        },
        "cycle_identity": cycle,
        "inventory_spec": [
            {
                "artifact_id": "raw-prompt",
                "source_path": "raw/prompt.txt",
                "retained_path": "raw/prompt.txt",
                "classification": "RESTRICTED_RAW",
                "required": True,
                "expected_state": "PRESENT",
            },
            {
                "artifact_id": "observation-finalizer",
                "source_path": "control/finalizer.json",
                "retained_path": "control/finalizer.json",
                "classification": "CONTROL_RECORD",
                "required": True,
                "expected_state": "PRESENT",
            },
            {
                "artifact_id": "cold-review-packet",
                "source_path": "review/cold-review.json",
                "retained_path": "review/cold-review.json",
                "classification": "SANITIZED_REVIEW",
                "required": False,
                "expected_state": "ABSENT",
            },
            {
                "artifact_id": "source-commit-receipt",
                "source_path": source_receipt["path"],
                "retained_path": source_receipt["path"],
                "classification": "CONTROL_RECORD",
                "required": True,
                "expected_state": "PRESENT",
            },
            {
                "artifact_id": "ci-readback",
                "source_path": ci_readback["path"],
                "retained_path": ci_readback["path"],
                "classification": "CONTROL_RECORD",
                "required": True,
                "expected_state": "PRESENT",
            },
            {
                "artifact_id": "candidate-record",
                "source_path": candidate_record["path"],
                "retained_path": candidate_record["path"],
                "classification": "CONTROL_RECORD",
                "required": True,
                "expected_state": "PRESENT",
            },
            {
                "artifact_id": "candidate-readiness",
                "source_path": candidate_readiness["path"],
                "retained_path": candidate_readiness["path"],
                "classification": "CONTROL_RECORD",
                "required": True,
                "expected_state": "PRESENT",
            },
        ],
        "retention_policy": {
            "mode": "RETAIN_INDEFINITELY",
            "pruning_authorized": False,
            "separate_owner_authorization_required": True,
            "permanent_removal_residue_required": True,
        },
        "model_execution_authorized": False,
        "terminal_claim": False,
        "non_claims": [
            "retention export is not candidate maturity",
            "retention export is not model execution authorization",
            "retention export is not owner acceptance",
        ],
    }
    if cycle_claim is not None:
        value["inventory_spec"].append(
            {
                "artifact_id": "cycle-claim",
                "source_path": cycle_claim["path"],
                "retained_path": cycle_claim["path"],
                "classification": "CONTROL_RECORD",
                "required": True,
                "expected_state": "PRESENT",
            }
        )
    path = temp / "export-authorization.json"
    write_authorization(path, value)
    return path, value


class EvidenceRetentionContractTests(unittest.TestCase):
    def test_required_owner_files_exist(self) -> None:
        for relative in (
            "schema/evidence-retention-manifest.schema.json",
            "tools/export_cycle_evidence_bundle.py",
            "tools/check_evidence_retention_manifest.py",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_complete_export_retains_full_inventory_and_exact_absent_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            manifest = exporter.export_evidence_bundle(auth_path)
            custody = Path(auth["evidence_custody_root"])
            final = custody / auth["final_path"]
            self.assertTrue(final.is_dir())
            self.assertEqual([], checker.validate_export(custody, final))
            self.assertEqual(8, len(manifest["inventory"]))
            absent = next(row for row in manifest["inventory"] if row["artifact_id"] == "cold-review-packet")
            self.assertFalse(absent["present"])
            self.assertIsNone(absent["sha256"])
            self.assertIsNone(absent["cas_object_path"])
            self.assertEqual("COMPLETE", manifest["completeness"])
            self.assertEqual([], manifest["missing_required_artifact_ids"])
            for row in manifest["inventory"]:
                if row["present"]:
                    self.assertEqual(row["sha256"], (custody / row["cas_object_path"]).name)
            resumed = exporter.export_evidence_bundle(auth_path)
            self.assertEqual(manifest, resumed)

    def test_full_inventory_rejects_unlisted_source_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            (Path(auth["source_root"]) / "unlisted.txt").write_text("not inventoried\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inventory|unlisted"):
                exporter.export_evidence_bundle(auth_path)
            self.assertFalse((Path(auth["evidence_custody_root"]) / auth["final_path"]).exists())

    def test_path_escape_fails_before_claim_or_publication(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            auth["inventory_spec"][0]["source_path"] = "../escape.txt"
            write_authorization(auth_path, auth)
            with self.assertRaisesRegex(ValueError, "path|traversal|escape"):
                exporter.export_evidence_bundle(auth_path)
            custody = Path(auth["evidence_custody_root"])
            self.assertFalse((custody / auth["claim_path"]).exists())
            self.assertFalse((custody / auth["final_path"]).exists())

    def test_required_absent_artifact_is_only_legal_for_partial_observation(self) -> None:
        for kind, allowed in (
            ("observation-cycle-export", True),
            ("candidate-readiness-final-manifest", False),
            ("final-reviewed-cycle-manifest", False),
        ):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
                root = Path(directory)
                auth_path, auth = authorization(root, kind=kind)
                auth["inventory_spec"][2]["required"] = True
                write_authorization(auth_path, auth)
                if allowed:
                    manifest = exporter.export_evidence_bundle(auth_path)
                    self.assertEqual("PARTIAL", manifest["completeness"])
                    self.assertEqual(["cold-review-packet"], manifest["missing_required_artifact_ids"])
                else:
                    with self.assertRaisesRegex(ValueError, "required|complete|missing"):
                        exporter.export_evidence_bundle(auth_path)

    def test_tampered_cas_object_and_manifest_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            manifest = exporter.export_evidence_bundle(auth_path)
            custody = Path(auth["evidence_custody_root"])
            final = custody / auth["final_path"]
            present = next(row for row in manifest["inventory"] if row["present"])
            (custody / present["cas_object_path"]).write_bytes(b"tampered\n")
            findings = checker.validate_export(custody, final)
            self.assertTrue(any("hash" in item.failure_subcode or "identity" in item.failure_subcode for item in findings), findings)

            stored = json.loads((final / "manifest.json").read_text(encoding="utf-8"))
            stored["source_identity"]["commit_sha"] = "f" * 40
            (final / "manifest.json").write_bytes(canonical_json_bytes(stored))
            findings = checker.validate_export(custody, final)
            self.assertTrue(any("manifest" in item.failure_subcode or "hash" in item.failure_subcode for item in findings), findings)

    def test_candidate_retention_green_rejects_unretained_sentinel_identity_refs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, _auth = authorization(root, kind="candidate-readiness-final-manifest")
            manifest = exporter.export_evidence_bundle(auth_path)
            identity_paths = {
                manifest["source_identity"]["source_commit_receipt"]["path"],
                manifest["source_identity"]["ci_readback"]["path"],
                manifest["candidate_identity"]["candidate_record"]["path"],
                manifest["candidate_identity"]["candidate_readiness"]["path"],
            }
            mutated = copy.deepcopy(manifest)
            mutated["inventory"] = [row for row in mutated["inventory"] if row["source_path"] not in identity_paths]
            mutated["source_identity"]["source_commit_receipt"] = ref("missing/source-commit.json")
            mutated["source_identity"]["ci_readback"] = ref("missing/ci-readback.json")
            mutated["candidate_identity"]["candidate_record"] = ref("missing/candidate-record.json")
            mutated["candidate_identity"]["candidate_readiness"] = ref("missing/candidate-readiness.json")
            mutated["inventory_sha256"] = checker.inventory_sha256(mutated["inventory"])
            mutated["retained_tree_sha256"] = checker.retained_tree_sha256(mutated["inventory"])
            mutated["cas_object_count"] = len({row["sha256"] for row in mutated["inventory"] if row["present"]})
            mutated["retained_byte_count"] = sum(row["byte_count"] for row in mutated["inventory"] if row["present"])
            mutated["manifest_sha256"] = content_hash(mutated, "manifest_sha256")
            findings = checker.validate_manifest(mutated)
            self.assertTrue(any("identity" in item.failure_subcode for item in findings), findings)

    def test_candidate_identity_refs_require_exact_hash_byte_and_live_cas_proof(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root, kind="candidate-readiness-final-manifest")
            manifest = exporter.export_evidence_bundle(auth_path)
            mutated = copy.deepcopy(manifest)
            mutated["candidate_identity"]["candidate_record"]["byte_count"] += 1
            mutated["manifest_sha256"] = content_hash(mutated, "manifest_sha256")
            findings = checker.validate_manifest(mutated)
            self.assertTrue(any("identity" in item.failure_subcode for item in findings), findings)

            custody = Path(auth["evidence_custody_root"])
            candidate_path = manifest["candidate_identity"]["candidate_record"]["path"]
            row = next(item for item in manifest["inventory"] if item["source_path"] == candidate_path)
            (custody / row["cas_object_path"]).unlink()
            findings = checker.validate_export(custody, custody / auth["final_path"])
            self.assertTrue(any("identity" in item.failure_subcode or "cas" in item.failure_subcode for item in findings), findings)

    def test_cycle_retention_green_rejects_unretained_sentinel_identity_refs(self) -> None:
        for kind in ("observation-cycle-export", "final-reviewed-cycle-manifest"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
                root = Path(directory)
                auth_path, _auth = authorization(root, kind=kind)
                manifest = exporter.export_evidence_bundle(auth_path)
                references = [
                    manifest["source_identity"]["source_commit_receipt"],
                    manifest["source_identity"]["ci_readback"],
                    manifest["candidate_identity"]["candidate_record"],
                    manifest["candidate_identity"]["candidate_readiness"],
                    manifest["cycle_identity"]["cycle_claim"],
                ]
                identity_paths = {reference["path"] for reference in references}
                mutated = copy.deepcopy(manifest)
                mutated["inventory"] = [row for row in mutated["inventory"] if row["source_path"] not in identity_paths]
                mutated["source_identity"]["source_commit_receipt"] = ref("missing/source-commit.json")
                mutated["source_identity"]["ci_readback"] = ref("missing/ci-readback.json")
                mutated["candidate_identity"]["candidate_record"] = ref("missing/candidate-record.json")
                mutated["candidate_identity"]["candidate_readiness"] = ref("missing/candidate-readiness.json")
                mutated["cycle_identity"]["cycle_claim"] = ref("missing/cycle-claim.json")
                mutated["inventory_sha256"] = checker.inventory_sha256(mutated["inventory"])
                mutated["retained_tree_sha256"] = checker.retained_tree_sha256(mutated["inventory"])
                mutated["cas_object_count"] = len({row["sha256"] for row in mutated["inventory"] if row["present"]})
                mutated["retained_byte_count"] = sum(row["byte_count"] for row in mutated["inventory"] if row["present"])
                mutated["manifest_sha256"] = content_hash(mutated, "manifest_sha256")
                findings = checker.validate_manifest(mutated)
                self.assertTrue(any("identity" in item.failure_subcode for item in findings), findings)

    def test_cycle_claim_requires_exact_hash_byte_and_live_cas_proof(self) -> None:
        for kind in ("observation-cycle-export", "final-reviewed-cycle-manifest"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
                root = Path(directory)
                auth_path, auth = authorization(root, kind=kind)
                manifest = exporter.export_evidence_bundle(auth_path)
                mutated = copy.deepcopy(manifest)
                mutated["cycle_identity"]["cycle_claim"]["byte_count"] += 1
                mutated["manifest_sha256"] = content_hash(mutated, "manifest_sha256")
                findings = checker.validate_manifest(mutated)
                self.assertTrue(any("identity" in item.failure_subcode for item in findings), findings)

                custody = Path(auth["evidence_custody_root"])
                claim_path = manifest["cycle_identity"]["cycle_claim"]["path"]
                row = next(item for item in manifest["inventory"] if item["source_path"] == claim_path)
                (custody / row["cas_object_path"]).unlink()
                findings = checker.validate_export(custody, custody / auth["final_path"])
                self.assertTrue(any("identity" in item.failure_subcode or "cas" in item.failure_subcode for item in findings), findings)

    def test_partial_staging_resumes_only_when_every_byte_is_hash_equal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            with self.assertRaisesRegex(RuntimeError, "injected.*stage"):
                exporter.export_evidence_bundle(auth_path, fault_at="after-stage")
            custody = Path(auth["evidence_custody_root"])
            self.assertTrue((custody / auth["staging_path"]).is_dir())
            self.assertFalse((custody / auth["final_path"]).exists())
            (Path(auth["source_root"]) / "raw/prompt.txt").write_bytes(b"different bytes\n")
            with self.assertRaisesRegex(ValueError, "staging|resume|collision|hash"):
                exporter.export_evidence_bundle(auth_path)
            self.assertFalse((custody / auth["final_path"]).exists())
            self.assertFalse((custody / ".writer.lock").exists())

    def test_partial_cas_publication_leaves_no_final_and_exact_retry_completes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            with self.assertRaisesRegex(RuntimeError, "injected.*first object"):
                exporter.export_evidence_bundle(auth_path, fault_at="after-first-object")
            custody = Path(auth["evidence_custody_root"])
            self.assertTrue(any((custody / "objects/sha256").rglob("*")))
            self.assertFalse((custody / auth["final_path"]).exists())
            self.assertFalse((custody / auth["receipt_path"]).exists())
            self.assertFalse((custody / auth["pointer_path"]).exists())
            self.assertFalse((custody / ".writer.lock").exists())
            manifest = exporter.export_evidence_bundle(auth_path)
            self.assertEqual("RETENTION_GREEN", manifest["status"])
            self.assertEqual([], checker.validate_export(custody, custody / auth["final_path"]))

    def test_crash_after_final_directory_adopts_only_exact_final_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            with self.assertRaisesRegex(RuntimeError, "injected.*final"):
                exporter.export_evidence_bundle(auth_path, fault_at="after-final")
            custody = Path(auth["evidence_custody_root"])
            final = custody / auth["final_path"]
            self.assertTrue(final.is_dir())
            self.assertFalse((custody / auth["receipt_path"]).exists())
            self.assertFalse((custody / auth["pointer_path"]).exists())
            manifest = exporter.export_evidence_bundle(auth_path)
            self.assertEqual([], checker.validate_export(custody, final))
            self.assertEqual(manifest["manifest_sha256"], json.loads((final / "manifest.json").read_text(encoding="utf-8"))["manifest_sha256"])

    def test_orphaned_immutable_pointer_record_is_exactly_adopted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            with self.assertRaisesRegex(RuntimeError, "injected.*pointer record"):
                exporter.export_evidence_bundle(auth_path, fault_at="after-pointer-record")
            custody = Path(auth["evidence_custody_root"])
            records = list((custody / f"pointers/{auth['scope_id']}/records").glob("*.json"))
            self.assertEqual(1, len(records))
            self.assertFalse((custody / auth["pointer_path"]).exists())
            self.assertFalse((custody / auth["receipt_path"]).exists())
            manifest = exporter.export_evidence_bundle(auth_path)
            self.assertEqual("RETENTION_GREEN", manifest["status"])
            self.assertEqual([], checker.validate_export(custody, custody / auth["final_path"]))

    def test_new_export_cannot_advance_past_predecessor_missing_its_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            first_path, first = authorization(root)
            with self.assertRaisesRegex(RuntimeError, "injected.*pointer"):
                exporter.export_evidence_bundle(first_path, fault_at="after-pointer")
            custody = Path(first["evidence_custody_root"])
            first_pointer = json.loads((custody / first["pointer_path"]).read_text(encoding="utf-8"))
            self.assertFalse((custody / first["receipt_path"]).exists())

            second = copy.deepcopy(first)
            second["export_id"] = "export-fixture-002"
            second["staging_path"] = ".staging/export-fixture-002"
            second["claim_path"] = "claims/export-fixture-002.json"
            second["final_path"] = "cycles/cycle-fixture-001/exports/export-fixture-002"
            second["receipt_path"] = "receipts/export-fixture-002.json"
            second["expected_pointer_sha256"] = first_pointer["pointer_sha256"]
            second_path = root / "second-authorization.json"
            write_authorization(second_path, second)
            with self.assertRaisesRegex(ValueError, "predecessor|receipt|complete"):
                exporter.export_evidence_bundle(second_path)
            self.assertFalse((custody / second["claim_path"]).exists())

            exporter.export_evidence_bundle(first_path)
            exporter.export_evidence_bundle(second_path)
            self.assertEqual([], checker.validate_export(custody, custody / second["final_path"]))

    def test_create_once_receipt_collision_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            exporter.export_evidence_bundle(auth_path)
            receipt = Path(auth["evidence_custody_root"]) / auth["receipt_path"]
            receipt.write_bytes(b'{"tampered":true}\n')
            with self.assertRaisesRegex(ValueError, "receipt|collision|readback"):
                exporter.export_evidence_bundle(auth_path)
            self.assertEqual(b'{"tampered":true}\n', receipt.read_bytes())

    def test_stale_pointer_predecessor_is_rejected_without_second_claim(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            first_path, first = authorization(root)
            exporter.export_evidence_bundle(first_path)
            second = copy.deepcopy(first)
            second["export_id"] = "export-fixture-002"
            second["staging_path"] = ".staging/export-fixture-002"
            second["claim_path"] = "claims/export-fixture-002.json"
            second["final_path"] = "cycles/cycle-fixture-001/exports/export-fixture-002"
            second["receipt_path"] = "receipts/export-fixture-002.json"
            second_path = root / "second-authorization.json"
            write_authorization(second_path, second)
            with self.assertRaisesRegex(ValueError, "pointer|predecessor|CAS|replay"):
                exporter.export_evidence_bundle(second_path)
            custody = Path(second["evidence_custody_root"])
            self.assertFalse((custody / second["claim_path"]).exists())
            self.assertFalse((custody / second["final_path"]).exists())

    def test_exact_pointer_predecessor_advances_contiguous_immutable_chain(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            first_path, first = authorization(root)
            exporter.export_evidence_bundle(first_path)
            custody = Path(first["evidence_custody_root"])
            first_pointer = json.loads((custody / first["pointer_path"]).read_text(encoding="utf-8"))
            second = copy.deepcopy(first)
            second["export_id"] = "export-fixture-002"
            second["staging_path"] = ".staging/export-fixture-002"
            second["claim_path"] = "claims/export-fixture-002.json"
            second["final_path"] = "cycles/cycle-fixture-001/exports/export-fixture-002"
            second["receipt_path"] = "receipts/export-fixture-002.json"
            second["expected_pointer_sha256"] = first_pointer["pointer_sha256"]
            second_path = root / "second-authorization.json"
            write_authorization(second_path, second)
            exporter.export_evidence_bundle(second_path)
            second_pointer = json.loads((custody / second["pointer_path"]).read_text(encoding="utf-8"))
            self.assertEqual(2, second_pointer["sequence"])
            self.assertEqual(first_pointer["pointer_sha256"], second_pointer["predecessor_pointer_sha256"])
            self.assertEqual([], checker.validate_export(custody, custody / first["final_path"]))
            self.assertEqual([], checker.validate_export(custody, custody / second["final_path"]))

    def test_third_export_is_blocked_when_genesis_receipt_was_deleted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            first_path, first = authorization(root)
            exporter.export_evidence_bundle(first_path)
            custody = Path(first["evidence_custody_root"])
            first_pointer = json.loads((custody / first["pointer_path"]).read_text(encoding="utf-8"))

            second = copy.deepcopy(first)
            second["export_id"] = "export-fixture-002"
            second["staging_path"] = ".staging/export-fixture-002"
            second["claim_path"] = "claims/export-fixture-002.json"
            second["final_path"] = "cycles/cycle-fixture-001/exports/export-fixture-002"
            second["receipt_path"] = "receipts/export-fixture-002.json"
            second["expected_pointer_sha256"] = first_pointer["pointer_sha256"]
            second_path = root / "second-authorization.json"
            write_authorization(second_path, second)
            exporter.export_evidence_bundle(second_path)
            second_pointer = json.loads((custody / second["pointer_path"]).read_text(encoding="utf-8"))

            (custody / first["receipt_path"]).unlink()
            third = copy.deepcopy(second)
            third["export_id"] = "export-fixture-003"
            third["staging_path"] = ".staging/export-fixture-003"
            third["claim_path"] = "claims/export-fixture-003.json"
            third["final_path"] = "cycles/cycle-fixture-001/exports/export-fixture-003"
            third["receipt_path"] = "receipts/export-fixture-003.json"
            third["expected_pointer_sha256"] = second_pointer["pointer_sha256"]
            third_path = root / "third-authorization.json"
            write_authorization(third_path, third)
            with self.assertRaisesRegex(ValueError, "genesis|historical|receipt|complete"):
                exporter.export_evidence_bundle(third_path)
            self.assertFalse((custody / third["claim_path"]).exists())

    def test_after_pointer_resume_rejects_missing_genesis_receipt_before_publishing_current_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            first_path, first = authorization(root)
            exporter.export_evidence_bundle(first_path)
            custody = Path(first["evidence_custody_root"])
            first_pointer = json.loads((custody / first["pointer_path"]).read_text(encoding="utf-8"))

            second = copy.deepcopy(first)
            second["export_id"] = "export-fixture-002"
            second["staging_path"] = ".staging/export-fixture-002"
            second["claim_path"] = "claims/export-fixture-002.json"
            second["final_path"] = "cycles/cycle-fixture-001/exports/export-fixture-002"
            second["receipt_path"] = "receipts/export-fixture-002.json"
            second["expected_pointer_sha256"] = first_pointer["pointer_sha256"]
            second_path = root / "second-authorization.json"
            write_authorization(second_path, second)
            with self.assertRaisesRegex(RuntimeError, "injected.*pointer"):
                exporter.export_evidence_bundle(second_path, fault_at="after-pointer")
            advanced = json.loads((custody / second["pointer_path"]).read_text(encoding="utf-8"))
            self.assertEqual(second["export_id"], advanced["export_id"])
            self.assertFalse((custody / second["receipt_path"]).exists())

            (custody / first["receipt_path"]).unlink()
            with self.assertRaisesRegex(ValueError, "genesis|historical|receipt|complete"):
                exporter.export_evidence_bundle(second_path)
            self.assertFalse((custody / second["receipt_path"]).exists())

    def test_latest_export_validation_rejects_missing_genesis_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            first_path, first = authorization(root)
            exporter.export_evidence_bundle(first_path)
            custody = Path(first["evidence_custody_root"])
            first_pointer = json.loads((custody / first["pointer_path"]).read_text(encoding="utf-8"))

            second = copy.deepcopy(first)
            second["export_id"] = "export-fixture-002"
            second["staging_path"] = ".staging/export-fixture-002"
            second["claim_path"] = "claims/export-fixture-002.json"
            second["final_path"] = "cycles/cycle-fixture-001/exports/export-fixture-002"
            second["receipt_path"] = "receipts/export-fixture-002.json"
            second["expected_pointer_sha256"] = first_pointer["pointer_sha256"]
            second_path = root / "second-authorization.json"
            write_authorization(second_path, second)
            exporter.export_evidence_bundle(second_path)

            (custody / first["receipt_path"]).unlink()
            findings = checker.validate_export(custody, custody / second["final_path"])
            self.assertTrue(findings)
            self.assertIn("receipt", findings[0].failure_subcode)

    def test_manifest_path_escape_is_rejected_even_with_no_live_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, _auth = authorization(root)
            manifest = exporter.export_evidence_bundle(auth_path)
            mutated = copy.deepcopy(manifest)
            mutated["inventory"][0]["cas_object_path"] = "../outside"
            findings = checker.validate_manifest(mutated)
            self.assertTrue(any("path" in item.failure_subcode for item in findings), findings)

    def test_final_locator_cannot_hide_an_extra_mutable_level(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, _auth = authorization(root)
            manifest = exporter.export_evidence_bundle(auth_path)
            mutated = copy.deepcopy(manifest)
            mutated["custody"]["final_path"] = (
                f"cycles/{mutated['scope_id']}/exports/mutable/{mutated['export_id']}"
            )
            mutated["manifest_sha256"] = content_hash(mutated, "manifest_sha256")
            findings = checker.validate_manifest(mutated)
            self.assertTrue(any(item.failure_subcode == "final-locator" for item in findings), findings)

    def test_pointer_genesis_sequence_is_exact_not_merely_positive(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            exporter.export_evidence_bundle(auth_path)
            custody = Path(auth["evidence_custody_root"])
            final = custody / auth["final_path"]
            manifest = json.loads((final / "manifest.json").read_text(encoding="utf-8"))
            receipt = json.loads((custody / auth["receipt_path"]).read_text(encoding="utf-8"))
            pointer = json.loads((custody / auth["pointer_path"]).read_text(encoding="utf-8"))
            pointer["sequence"] = 7
            pointer["pointer_sha256"] = content_hash(pointer, "pointer_sha256")
            findings = checker._pointer_findings(pointer, manifest, receipt)
            self.assertTrue(any(item.failure_subcode == "pointer-sequence" for item in findings), findings)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink API unavailable")
    def test_symlinked_source_artifact_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
            root = Path(directory)
            auth_path, auth = authorization(root)
            source = Path(auth["source_root"])
            target = source / "raw/real.txt"
            target.write_text("real\n", encoding="utf-8")
            link = source / "raw/link.txt"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("host does not permit symlink creation")
            auth["inventory_spec"].extend(
                [
                    {"artifact_id": "real", "source_path": "raw/real.txt", "retained_path": "raw/real.txt", "classification": "CONTROL_RECORD", "required": True, "expected_state": "PRESENT"},
                    {"artifact_id": "link", "source_path": "raw/link.txt", "retained_path": "raw/link.txt", "classification": "CONTROL_RECORD", "required": True, "expected_state": "PRESENT"},
                ]
            )
            write_authorization(auth_path, auth)
            with self.assertRaisesRegex(ValueError, "symlink|reparse|regular"):
                exporter.export_evidence_bundle(auth_path)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink API unavailable")
    def test_required_json_member_reparse_substitution_is_rejected_when_supported(self) -> None:
        members = ("manifest", "claim", "receipt", "pointer-record", "pointer-head")
        capability_checked = False
        for member in members:
            with self.subTest(member=member), tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
                root = Path(directory)
                auth_path, auth = authorization(root)
                manifest = exporter.export_evidence_bundle(auth_path)
                custody = Path(auth["evidence_custody_root"])
                final = custody / auth["final_path"]
                receipt = json.loads((custody / auth["receipt_path"]).read_text(encoding="utf-8"))
                targets = {
                    "manifest": final / "manifest.json",
                    "claim": custody / auth["claim_path"],
                    "receipt": custody / auth["receipt_path"],
                    "pointer-record": custody / receipt["pointer_record"]["path"],
                    "pointer-head": custody / auth["pointer_path"],
                }
                original = targets[member]
                held = custody / "symlink-targets" / f"{member}.json"
                held.parent.mkdir(parents=True, exist_ok=True)
                original.replace(held)
                try:
                    original.symlink_to(held)
                except OSError:
                    if not capability_checked:
                        self.skipTest("host does not permit symlink creation")
                    raise
                capability_checked = True
                findings = checker.validate_export(custody, final)
                self.assertTrue(any("reparse" in item.failure_subcode or "symlink" in item.message.lower() for item in findings), findings)

    def test_required_json_member_reparse_signal_fails_closed(self) -> None:
        members = ("manifest", "claim", "receipt", "pointer-record", "pointer-head")
        for member in members:
            with self.subTest(member=member), tempfile.TemporaryDirectory(prefix="daee-retention-") as directory:
                root = Path(directory)
                auth_path, auth = authorization(root)
                exporter.export_evidence_bundle(auth_path)
                custody = Path(auth["evidence_custody_root"])
                final = custody / auth["final_path"]
                receipt = json.loads((custody / auth["receipt_path"]).read_text(encoding="utf-8"))
                target = {
                    "manifest": final / "manifest.json",
                    "claim": custody / auth["claim_path"],
                    "receipt": custody / auth["receipt_path"],
                    "pointer-record": custody / receipt["pointer_record"]["path"],
                    "pointer-head": custody / auth["pointer_path"],
                }[member]
                real_is_reparse = checker._is_reparse

                def injected(path: Path) -> bool:
                    return Path(path) == target or real_is_reparse(Path(path))

                with mock.patch.object(checker, "_is_reparse", side_effect=injected):
                    findings = checker.validate_export(custody, final)
                self.assertTrue(any("reparse" in item.failure_subcode or "symlink" in item.message.lower() for item in findings), findings)


if __name__ == "__main__":
    unittest.main()
