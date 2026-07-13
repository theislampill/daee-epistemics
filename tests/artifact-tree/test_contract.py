#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import artifact_tree  # noqa: E402
import build_candidate_package_record as candidate_record  # noqa: E402
import check_package_harness_parity as package_parity  # noqa: E402
import check_runtime_context_delivery as runtime_context  # noqa: E402
import check_smoke_matrix_manifest as smoke_manifest  # noqa: E402


def expected_digest(rows: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for relative, payload in sorted(rows):
        encoded = relative.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
        digest.update(hashlib.sha256(payload).digest())
    return digest.hexdigest()


class ArtifactTreeContractTests(unittest.TestCase):
    def test_named_framed_path_file_digest_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "nested").mkdir()
            (root / "z.txt").write_bytes(b"z\n")
            (root / "nested" / "a.txt").write_bytes(b"a\n")

            receipt = artifact_tree.build_tree_receipt(root)

            self.assertEqual("daee-tree-sha256-v1", receipt["algorithm"])
            self.assertEqual(2, receipt["file_count"])
            self.assertEqual(
                expected_digest([("nested/a.txt", b"a\n"), ("z.txt", b"z\n")]),
                receipt["tree_sha256"],
            )
            self.assertEqual(
                ["nested/a.txt", "z.txt"],
                [row["path"] for row in receipt["files"]],
            )

    def test_content_or_path_change_changes_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "a.txt"
            path.write_bytes(b"one")
            first = artifact_tree.tree_sha256(root)
            path.write_bytes(b"two")
            second = artifact_tree.tree_sha256(root)
            path.rename(root / "b.txt")
            third = artifact_tree.tree_sha256(root)
            self.assertEqual(3, len({first, second, third}))

    def test_symlink_or_reparse_content_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            target = Path(outside) / "target.txt"
            target.write_bytes(b"outside")
            link = root / "link.txt"
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "symlink|reparse"):
                artifact_tree.tree_sha256(root)

    def test_empty_tree_has_named_digest_not_implicit_file_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt = artifact_tree.build_tree_receipt(root)
            self.assertEqual(hashlib.sha256().hexdigest(), receipt["tree_sha256"])
            self.assertEqual([], receipt["files"])

    def test_all_candidate_consumers_share_the_named_algorithm(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "skill").mkdir()
            (root / "skill" / "SKILL.md").write_bytes(b"---\n---\n")
            expected = artifact_tree.tree_sha256(root)

            candidate_digest, candidate_rows = candidate_record._tree_receipt(root)

            self.assertEqual(expected, candidate_digest)
            self.assertEqual(expected, package_parity.tree_sha(root))
            self.assertEqual(expected, runtime_context.tree_sha(root))
            self.assertEqual(expected, smoke_manifest._tree_digest(root))
            self.assertEqual(["skill/SKILL.md"], [row["path"] for row in candidate_rows])

    def test_candidate_extraction_receipt_names_the_algorithm(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "candidate.zip"
            with zipfile.ZipFile(archive, "w") as payload:
                payload.writestr("SKILL.md", "---\n---\n")
            receipt = candidate_record.safe_extract_zip(
                archive,
                root / "candidate",
                declared_total_bytes=8,
                max_total_bytes=32,
                allowed_root=root,
            )
            self.assertEqual(
                "daee-tree-sha256-v1", receipt["tree_digest_algorithm"]
            )


if __name__ == "__main__":
    unittest.main()
