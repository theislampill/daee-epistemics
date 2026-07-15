#!/usr/bin/env python3
"""Contract tests for versioned Task 7 deterministic-evidence namespaces."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import check_task7_deterministic_evidence_namespace as checker  # noqa: E402
import write_task7_deterministic_evidence as writer  # noqa: E402
from a16_immutable_custody import CustodyError  # noqa: E402
from contract_validation import validate_schema_definition  # noqa: E402


LEGACY_FILE_COUNT = 124
LEGACY_MANIFEST_SHA256 = "c3af8e69825492bba78b3a3736b84486c05ca43d1f1c308a8d75820ceadcd89a"
LEGACY_SOURCE_FREEZE_SHA256 = "a8f313ab821729af503ce39538b98c77ac5b2e5db940b938c6afd654b1501300"


class Task7EvidenceNamespaceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree_oid = "4" * 40
        self.files = [
            {
                "path": writer.PRODUCER_PATH,
                "blob_oid": "a" * 40,
                "byte_count": 12,
                "raw_sha256": "b" * 64,
            },
            {
                "path": "tests/empty.txt",
                "blob_oid": "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
                "byte_count": 0,
                "raw_sha256": hashlib.sha256(b"").hexdigest(),
            },
        ]
        self.branch11 = writer.namespace_contract(writer.DEFAULT_NAMESPACE_ID)

    def assert_failure(self, finding: checker.Finding | None, failure_class: str) -> None:
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual(finding.failure_class, failure_class, finding)

    def branch11_freeze(self) -> dict[str, object]:
        return writer.build_source_freeze(
            self.tree_oid,
            self.files,
            namespace_id=writer.DEFAULT_NAMESPACE_ID,
        )

    def validate_branch11(
        self,
        freeze: dict[str, object],
        *,
        artifact_path: Path | None = None,
        observed_tree_oid: str | None = None,
        observed_files: list[dict[str, object]] | None = None,
    ) -> checker.Finding | None:
        return checker.validate_source_freeze_namespace(
            freeze,
            namespace_id=writer.DEFAULT_NAMESPACE_ID,
            artifact_path=artifact_path or ROOT / self.branch11.source_freeze_rel,
            observed_tree_oid=observed_tree_oid or self.tree_oid,
            observed_files=observed_files or copy.deepcopy(self.files),
            root=ROOT,
        )

    def test_schema_uses_only_repo_native_supported_keywords(self) -> None:
        validate_schema_definition(
            json.loads(checker.SCHEMA_PATH.read_text(encoding="utf-8"))
        )

    def test_legacy_branch10_bytes_and_paths_remain_unchanged(self) -> None:
        legacy = writer.namespace_contract(writer.LEGACY_NAMESPACE_ID)
        current = writer.namespace_contract(writer.DEFAULT_NAMESPACE_ID)
        self.assertNotEqual(legacy.evidence_rel, current.evidence_rel)
        self.assertFalse(
            current.evidence_rel.as_posix().startswith(legacy.evidence_rel.as_posix() + "/")
        )
        count, digest = checker.directory_manifest_digest(ROOT / legacy.evidence_rel)
        self.assertEqual((count, digest), (LEGACY_FILE_COUNT, LEGACY_MANIFEST_SHA256))
        source_freeze = ROOT / legacy.source_freeze_rel
        self.assertEqual(hashlib.sha256(source_freeze.read_bytes()).hexdigest(), LEGACY_SOURCE_FREEZE_SHA256)
        writer.validate_source_freeze(
            json.loads(source_freeze.read_text(encoding="utf-8")),
            writer.LEGACY_NAMESPACE_ID,
        )

    def test_branch11_freeze_binds_exact_allowlisted_namespace(self) -> None:
        freeze = self.branch11_freeze()
        self.assertEqual(freeze["evidence_namespace"], writer.DEFAULT_NAMESPACE_ID)
        self.assertEqual(freeze["namespace_version"], 1)
        self.assertEqual(freeze["generation"], "branch11")
        self.assertEqual(freeze["evidence_root"], self.branch11.evidence_rel.as_posix())
        self.assertIsNone(self.validate_branch11(freeze))

    def test_cross_namespace_substitution_is_rejected(self) -> None:
        legacy = writer.build_source_freeze(
            self.tree_oid,
            self.files,
            namespace_id=writer.LEGACY_NAMESPACE_ID,
        )
        self.assert_failure(
            self.validate_branch11(legacy),
            "cross-namespace-substitution",
        )

    def test_branch_and_ref_mismatch_are_rejected(self) -> None:
        for field, value in (
            ("branch", "codex/v0.4.6.0-runtime-footprint-b10"),
            ("ref", "refs/heads/codex/v0.4.6.0-runtime-footprint-b10"),
        ):
            with self.subTest(field=field):
                freeze = self.branch11_freeze()
                freeze[field] = value
                self.assert_failure(self.validate_branch11(freeze), "branch-mismatch")

    def test_tree_drift_is_rejected(self) -> None:
        self.assert_failure(
            self.validate_branch11(self.branch11_freeze(), observed_tree_oid="5" * 40),
            "tree-drift",
        )

    def test_tree_path_drift_is_rejected(self) -> None:
        observed = copy.deepcopy(self.files)
        observed[-1]["path"] = "tests/substituted.txt"
        self.assert_failure(
            self.validate_branch11(self.branch11_freeze(), observed_files=observed),
            "path-drift",
        )

    def test_tree_hash_drift_is_rejected(self) -> None:
        observed = copy.deepcopy(self.files)
        observed[-1]["raw_sha256"] = "c" * 64
        self.assert_failure(
            self.validate_branch11(self.branch11_freeze(), observed_files=observed),
            "hash-drift",
        )

    def test_namespace_path_substitution_is_rejected(self) -> None:
        substituted = ROOT / writer.namespace_contract(writer.LEGACY_NAMESPACE_ID).source_freeze_rel
        self.assert_failure(
            self.validate_branch11(self.branch11_freeze(), artifact_path=substituted),
            "namespace-path-substitution",
        )

    def test_branch11_producer_command_is_namespace_and_path_bound(self) -> None:
        command = writer.producer_command("no-model-preflight", writer.DEFAULT_NAMESPACE_ID)
        self.assertEqual(
            command[command.index("--evidence-namespace") + 1],
            writer.DEFAULT_NAMESPACE_ID,
        )
        self.assertIn(self.branch11.source_freeze_rel.as_posix(), command)
        self.assertIn(
            (self.branch11.evidence_rel / writer.ROLE_FILE_BY_KIND["no-model-preflight"]).as_posix(),
            command,
        )
        with self.assertRaisesRegex(ValueError, "exact source-bound producer"):
            writer.validate_role_command(
                writer.producer_command("no-model-preflight", writer.LEGACY_NAMESPACE_ID),
                "no-model-preflight",
                writer.PRODUCER_PATH,
                namespace_id=writer.DEFAULT_NAMESPACE_ID,
            )

    def test_writer_build_modes_require_explicit_allowlisted_namespace(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ROOT / writer.PRODUCER_PATH),
                "--build-freeze",
                "--tree",
                self.tree_oid,
                "--out",
                self.branch11.source_freeze_rel.as_posix(),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("build modes require --evidence-namespace", completed.stderr)

    def test_create_once_replay_is_rejected_without_overwrite(self) -> None:
        value = {"schema": "probe", "complete": True}
        with tempfile.TemporaryDirectory(prefix="daee-task7-namespace-replay-") as temporary:
            root = Path(temporary)
            target = root / "source-freeze.json"
            writer._publish(root, target, value)
            original = target.read_bytes()
            with self.assertRaises(CustodyError) as caught:
                writer._publish(root, target, {"schema": "different", "complete": True})
            self.assertEqual(caught.exception.subcode, "claim-replay")
            self.assertEqual(target.read_bytes(), original)

    def integration_freeze(self) -> tuple[dict[str, object], list[dict[str, object]]]:
        rows: list[dict[str, object]] = [
            {
                "path": "schema/example.json",
                "status": "tracked-change",
                "sha256": "a" * 64,
                "bytes": 10,
            },
            {
                "path": "tools/example.py",
                "status": "untracked",
                "sha256": "b" * 64,
                "bytes": 20,
            },
        ]
        value: dict[str, object] = {
            "schema_version": "daee-b11-final-integration-freeze-v1",
            "created_at_utc": "2026-07-14T01:44:57.8783624Z",
            "branch": self.branch11.branch,
            "base_head": "2ddd4d9efab2b437331b3f5d6247cb8f02abcfdf",
            "upstream": None,
            "intended_push_target": "origin/codex/v0.4.6.0-runtime-footprint-b11",
            "scope": "Complete non-ignored dirty source set.",
            "source_path_count": len(rows),
            "aggregate_sha256": checker.integration_aggregate(rows),
            "paths": rows,
            "stability": {
                "source_writers_stopped": True,
                "source_bytes_must_match_each_path_sha256": True,
                "aggregate_canonicalization": (
                    "UTF-8(path + TAB + lowercase sha256 + LF), paths sorted by ordinal code-unit order"
                ),
            },
            "nonclaims": [
                "This freeze is not terminal A01-A16 closure.",
                "This freeze is not exact-SHA GitHub CI evidence.",
                "This freeze is not candidate maturity.",
                "This freeze authorizes no model execution.",
            ],
        }
        return value, copy.deepcopy(rows)

    def test_integration_freeze_native_readback_accepts_exact_rows(self) -> None:
        freeze, rows = self.integration_freeze()
        finding = checker.validate_integration_freeze(
            freeze,
            actual_rows=rows,
            current_branch=self.branch11.branch,
            current_head=freeze["base_head"],
        )
        self.assertIsNone(finding)

    def test_integration_freeze_path_and_hash_drift_are_rejected(self) -> None:
        for label, mutate, expected in (
            (
                "path",
                lambda rows: rows.__setitem__(0, {**rows[0], "path": "schema/substituted.json"}),
                "integration-path-drift",
            ),
            (
                "hash",
                lambda rows: rows.__setitem__(0, {**rows[0], "sha256": "c" * 64}),
                "integration-hash-drift",
            ),
        ):
            with self.subTest(label=label):
                freeze, rows = self.integration_freeze()
                mutate(rows)
                self.assert_failure(
                    checker.validate_integration_freeze(
                        freeze,
                        actual_rows=rows,
                        current_branch=self.branch11.branch,
                        current_head=freeze["base_head"],
                    ),
                    expected,
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
