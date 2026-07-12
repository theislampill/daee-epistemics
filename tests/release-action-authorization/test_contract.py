#!/usr/bin/env python3
"""Contract tests for the locked release-package authorization boundary."""
from __future__ import annotations

import unittest
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests" / "release-action-authorization"
sys.path.insert(0, str(ROOT / "tools"))
import check_release_action_authorization as checker

VALID_FIXTURES = {"exact-release-package-build.json"}
INVALID_FIXTURES = {
    "duplicate-key.json",
    "expired.json",
    "extra-release-actions.json",
    "nonunique-output.json",
    "not-yet-valid.json",
    "pass-receipt-missing-evidence.json",
    "path-escape.json",
    "reusable-boolean.json",
    "revoked.json",
    "source-head-drift.json",
    "writer-mismatch.json",
    "wrong-action-family.json",
}


class ReleaseActionAuthorizationContract(unittest.TestCase):
    def test_required_owner_files_exist(self) -> None:
        for relative in (
            "schema/release-action-authorization.schema.json",
            "tools/a16_immutable_custody.py",
            "tools/check_release_action_authorization.py",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_plan17_named_fixture_family_is_complete(self) -> None:
        valid = FIXTURE_ROOT / "valid"
        invalid = FIXTURE_ROOT / "invalid"
        self.assertEqual(VALID_FIXTURES, {path.name for path in valid.glob("*.json")})
        fixtures = {
            path.name
            for path in invalid.glob("*.json")
            if not path.name.endswith(".expectation.json")
        }
        self.assertEqual(INVALID_FIXTURES, fixtures)
        expectations = {path.name for path in invalid.glob("*.expectation.json")}
        self.assertEqual(
            {Path(name).with_suffix(".expectation.json").name for name in INVALID_FIXTURES},
            expectations,
        )

    def test_live_boundary_replay_and_terminal_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            custody = Path(directory)
            authority = custody / "authorizations"
            outside = custody / "outside"
            authority.mkdir(); outside.mkdir()
            issued = outside / "issued.json"; issued.write_text("{}\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                checker.resolve_live_authorization_path(authority / ".." / "outside" / "issued.json", authority_root=authority)
            (authority / "input.json").write_text('{"nonce":"n","authorization_sha256":"a"}\n', encoding="utf-8")
            self.assertEqual([], checker.find_existing_action_records(custody, "a" * 64, "n"))
            value, raw, error = checker._load(FIXTURE_ROOT / "valid/exact-release-package-build.json")
            self.assertIsNone(error)
            assert value is not None
            (authority / "issued-authorization.json").write_bytes(raw)
            claim, claim_error = checker.consume_authorization(
                value,
                raw,
                checker._fixture_observed(),
                custody_root=custody,
                claim_target=custody / "claims/live-layout.claim.json",
                claimed_at="2026-07-12T12:00:00Z",
            )
            self.assertIsNone(claim_error)
            self.assertIsNotNone(claim)
        self.assertFalse(checker.result_requires_live_observation("FAILED"))
        self.assertFalse(checker.result_requires_live_observation("UNKNOWN"))
        self.assertTrue(checker.result_requires_live_observation("PASS"))

    def test_failed_finalize_does_not_collect_live_git_or_network_state(self) -> None:
        manifest = FIXTURE_ROOT / "valid/exact-release-package-build.json"
        value, _raw, error = checker._load(manifest)
        self.assertIsNone(error)
        assert value is not None
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claim = root / "claim.json"
            receipt = root / "receipt.json"
            with (
                mock.patch.object(checker, "resolve_live_authorization_path", return_value=manifest),
                mock.patch.object(checker, "_authority_file_protected", return_value=True),
                mock.patch.object(checker, "collect_live_observation", side_effect=AssertionError("collector called")) as collector,
                mock.patch.object(checker, "resolve_live_custody_path", side_effect=[claim, receipt]),
                mock.patch.object(checker, "finalize_authorization", return_value=({}, None)),
                redirect_stdout(StringIO()),
            ):
                result = checker.main(
                    [
                        "--manifest", str(manifest),
                        "--require-action", "build-release-package",
                        "--finalize",
                        "--claim-receipt", value["claim_locator"],
                        "--action-receipt", value["action_receipt_locator"],
                        "--result", "UNKNOWN",
                    ]
                )
            self.assertEqual(0, result)
            collector.assert_not_called()

    def test_pass_finalize_reads_the_exact_temp_output_package(self) -> None:
        manifest = FIXTURE_ROOT / "valid/exact-release-package-build.json"
        value, raw, error = checker._load(manifest)
        self.assertIsNone(error)
        assert value is not None
        observed = checker._fixture_observed()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claim_path = root / "claims/release.claim.json"
            _claim, claim_error = checker.consume_authorization(
                value,
                raw,
                observed,
                custody_root=root,
                claim_target=claim_path,
                claimed_at=observed["now"],
            )
            self.assertIsNone(claim_error)
            package = (
                root
                / value["output_directory"]
                / "daee-epistemics-v0.4.6.0-execution-mini.skill.zip"
            )
            package.parent.mkdir(parents=True)
            package.write_bytes(b"temp-only release package fixture\n")
            with mock.patch.object(checker, "ROOT", root):
                receipt, final_error = checker.finalize_authorization(
                    value,
                    raw,
                    claim_path,
                    "PASS",
                    custody_root=root,
                    receipt_target=root / "receipts/release.receipt.json",
                    finalized_at=observed["now"],
                )
            self.assertIsNone(final_error)
            self.assertIsNotNone(receipt)
            self.assertEqual(package.relative_to(root).as_posix(), receipt["package_path"])


if __name__ == "__main__":
    unittest.main()
