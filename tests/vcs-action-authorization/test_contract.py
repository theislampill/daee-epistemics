#!/usr/bin/env python3
"""Contract tests for immutable one-use VCS action authorization custody."""
from __future__ import annotations

import unittest
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests" / "vcs-action-authorization"
sys.path.insert(0, str(ROOT / "tools"))
import check_vcs_action_authorization as checker
import a16_immutable_custody as custody_helper

VALID_FIXTURES = {
    "exact-countermeasure-commit.json",
    "exact-nonforce-branch-push.json",
}

INVALID_FIXTURES = {
    "authorization-replayed-different-claim-path.json",
    "branch-drift.json",
    "cas-predecessor-mismatch.json",
    "claim-collision.json",
    "duplicate-key.json",
    "expired.json",
    "force-enabled.json",
    "matrix-authorization-used-for-push.json",
    "not-yet-valid.json",
    "pass-receipt-missing-evidence.json",
    "path-escape.json",
    "ref-drift.json",
    "remote-head-moved-after-approval.json",
    "revoked.json",
    "writer-mismatch.json",
    "wrong-action-family.json",
    "wrong-diff.json",
    "wrong-message.json",
    "wrong-parent.json",
    "wrong-path-manifest.json",
    "wrong-tree.json",
}


class VcsActionAuthorizationContract(unittest.TestCase):
    def test_required_owner_files_exist(self) -> None:
        for relative in (
            "schema/vcs-action-authorization.schema.json",
            "tools/a16_immutable_custody.py",
            "tools/check_vcs_action_authorization.py",
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

    def test_live_boundary_replay_terminal_and_guarded_push_contracts(self) -> None:
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
            value, raw, error = checker._load(FIXTURE_ROOT / "valid/exact-countermeasure-commit.json")
            self.assertIsNone(error)
            assert value is not None
            (authority / "issued-authorization.json").write_bytes(raw)
            claim, claim_error = checker.consume_authorization(
                value,
                raw,
                checker._fixture_observation(),
                custody_root=custody,
                claim_target=custody / "claims/live-layout.claim.json",
                claimed_at="2026-07-12T12:00:00Z",
            )
            self.assertIsNone(claim_error)
            self.assertIsNotNone(claim)
        self.assertFalse(checker.result_requires_live_observation("FAILED"))
        self.assertFalse(checker.result_requires_live_observation("UNKNOWN"))
        self.assertTrue(checker.result_requires_live_observation("PASS"))
        calls = []
        finding = checker.guarded_push_update(
            {"target_ref":"refs/heads/x","remote_name":"origin","expected_old_remote_oid":"1"*40,"local_commit":"3"*40,"force":False},
            observation={"remote_oid":"1"*40,"fast_forward":True,"replace_objects_disabled":True,"shallow":False,"grafts_present":False,"old_object_type":"commit","new_object_type":"commit"},
            transport=lambda **kwargs: calls.append(kwargs) or {"applied":False,"actual_old_oid":"2"*40,"new_oid":None,"mode":"exact-old-lease"},
        )
        self.assertEqual("remote-moved-at-cas", finding.failure_subcode)
        self.assertEqual("1"*40, calls[0]["expected_old_oid"])
        applied = checker.guarded_push_update(
            {"target_ref":"refs/heads/x","remote_name":"origin","expected_old_remote_oid":"1"*40,"local_commit":"3"*40,"force":False},
            observation={"remote_oid":"1"*40,"fast_forward":True,"replace_objects_disabled":True,"shallow":False,"grafts_present":False,"old_object_type":"commit","new_object_type":"commit"},
            transport=lambda **_kwargs: {"applied":True,"actual_old_oid":"1"*40,"new_oid":"3"*40,"mode":"exact-old-lease"},
        )
        self.assertIsNone(applied)

    def test_lock_identity_and_commit_message_bytes_are_independent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock = root / ".writer.lock"
            with custody_helper.exclusive_writer_lock(root):
                self.assertTrue(lock.is_file())
            self.assertFalse(lock.exists())
            with mock.patch.object(custody_helper.os, "write", side_effect=OSError("injected lock write failure")):
                with self.assertRaisesRegex(OSError, "injected lock write failure"):
                    with custody_helper.exclusive_writer_lock(root):
                        self.fail("failed lock write must not enter the protected section")
            self.assertFalse(lock.exists())
            changed = root / "message.txt"
            changed.write_bytes(b"different message\n")
            self.assertNotEqual(
                checker.hash_commit_message_file(changed),
                checker.hash_commit_message_file(FIXTURE_ROOT / "support/commit-message.txt"),
            )

    def test_failed_finalize_does_not_collect_live_git_or_network_state(self) -> None:
        manifest = FIXTURE_ROOT / "valid/exact-countermeasure-commit.json"
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
                mock.patch.object(checker, "collect_final_observation", side_effect=AssertionError("collector called")) as collector,
                mock.patch.object(checker, "resolve_live_custody_path", side_effect=[claim, receipt]),
                mock.patch.object(checker, "finalize_authorization", return_value=({}, None)),
                redirect_stdout(StringIO()),
            ):
                result = checker.main(
                    [
                        "--manifest", str(manifest),
                        "--require-action", "commit-countermeasure",
                        "--finalize",
                        "--claim-receipt", value["claim_locator"],
                        "--action-receipt", value["action_receipt_locator"],
                        "--result", "FAILED",
                    ]
                )
            self.assertEqual(0, result)
            collector.assert_not_called()


if __name__ == "__main__":
    unittest.main()
