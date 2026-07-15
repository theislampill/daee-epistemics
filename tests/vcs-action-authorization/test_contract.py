#!/usr/bin/env python3
"""Contract tests for immutable one-use VCS action authorization custody."""
from __future__ import annotations

import unittest
import sys
import subprocess
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
    @staticmethod
    def _tracking_repository(root: Path, branch: str) -> tuple[Path, Path, str, str]:
        remote = root / "remote.git"
        local = root / "local"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "init", "-b", branch, str(local)],
            check=True,
            capture_output=True,
        )
        for key, value in (
            ("user.email", "tracking@example.invalid"),
            ("user.name", "Tracking Canary"),
        ):
            subprocess.run(
                ["git", "-C", str(local), "config", key, value],
                check=True,
                capture_output=True,
            )
        tracked = local / "tracked.txt"
        tracked.write_text("predecessor\n", encoding="utf-8", newline="\n")
        subprocess.run(
            ["git", "-C", str(local), "add", "tracked.txt"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(local), "commit", "-m", "tracking predecessor"],
            check=True,
            capture_output=True,
        )
        predecessor = subprocess.run(
            ["git", "-C", str(local), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        tracked.write_text("source\n", encoding="utf-8", newline="\n")
        subprocess.run(
            ["git", "-C", str(local), "add", "tracked.txt"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(local), "commit", "-m", "tracking source"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(local), "remote", "add", "origin", str(remote)],
            check=True,
            capture_output=True,
        )
        head = subprocess.run(
            ["git", "-C", str(local), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return remote, local, head, predecessor

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

    def test_absent_ref_authorization_pairs_null_old_with_create_mode(self) -> None:
        value, _raw, error = checker._load(
            FIXTURE_ROOT / "valid/exact-nonforce-branch-push.json"
        )
        self.assertIsNone(error)
        assert value is not None
        observed = checker._fixture_observation()
        value["remote_update_mode"] = "exact-absent-lease-create"
        value["expected_old_remote_oid"] = None
        observed.update(
            {
                "remote_oid": None,
                "old_object_type": None,
                "fast_forward": False,
            }
        )
        self.assertEqual([], checker.validate_authorization(value, observed))

        wrong_old = dict(value)
        wrong_old["expected_old_remote_oid"] = "1" * 40
        self.assertTrue(checker.validate_schema_subset(wrong_old, checker._schema()))
        wrong_mode = dict(value)
        wrong_mode["remote_update_mode"] = "exact-old-lease-fast-forward"
        self.assertTrue(checker.validate_schema_subset(wrong_mode, checker._schema()))

    def test_absent_ref_jit_presence_is_a_collision_even_at_intended_oid(self) -> None:
        calls = []
        finding = checker.guarded_push_update(
            {
                "target_ref": "refs/heads/new",
                "remote_name": "origin",
                "remote_update_mode": "exact-absent-lease-create",
                "expected_old_remote_oid": None,
                "local_commit": "3" * 40,
                "force": False,
            },
            observation={
                "remote_oid": "3" * 40,
                "fast_forward": False,
                "replace_objects_disabled": True,
                "shallow": False,
                "grafts_present": False,
                "old_object_type": "commit",
                "new_object_type": "commit",
            },
            transport=lambda **kwargs: calls.append(kwargs),
        )
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual("remote-ref-present", finding.failure_subcode)
        self.assertEqual([], calls)

        absent_observation = {
            "remote_oid": None,
            "replace_objects_disabled": True,
            "shallow": False,
            "grafts_present": False,
            "old_object_type": None,
            "new_object_type": "commit",
        }
        authorization = {
            "target_ref": "refs/heads/new",
            "remote_name": "origin",
            "remote_update_mode": "exact-absent-lease-create",
            "expected_old_remote_oid": None,
            "local_commit": "3" * 40,
            "force": False,
        }
        missing_tracking = checker.guarded_push_update(
            authorization,
            observation=absent_observation,
            transport=lambda **_kwargs: {
                "mode": "exact-absent-lease-create",
                "applied": True,
                "actual_old_oid": None,
                "new_oid": "3" * 40,
            },
        )
        self.assertIsNotNone(missing_tracking)
        assert missing_tracking is not None
        self.assertEqual("transport-tracking", missing_tracking.failure_subcode)

        missing_local_cas_proof = checker.guarded_push_update(
            authorization,
            observation=absent_observation,
            transport=lambda **_kwargs: {
                "mode": "exact-absent-lease-create",
                "applied": True,
                "actual_old_oid": None,
                "new_oid": "3" * 40,
                "tracking_established": True,
                "upstream_ref": "refs/remotes/origin/new",
                "upstream_oid": "3" * 40,
            },
        )
        self.assertIsNotNone(missing_local_cas_proof)
        assert missing_local_cas_proof is not None
        self.assertEqual("transport-tracking", missing_local_cas_proof.failure_subcode)

        applied = checker.guarded_push_update(
            authorization,
            observation=absent_observation,
            transport=lambda **_kwargs: {
                "mode": "exact-absent-lease-create",
                "applied": True,
                "actual_old_oid": None,
                "new_oid": "3" * 40,
                "tracking_established": True,
                "upstream_ref": "refs/remotes/origin/new",
                "upstream_oid": "3" * 40,
                "tracking_update_mode": "exact-local-ref-cas",
                "tracking_previous_oid": None,
            },
        )
        self.assertIsNone(applied)
        raced = checker.guarded_push_update(
            authorization,
            observation=absent_observation,
            transport=lambda **_kwargs: {
                "mode": "exact-absent-lease-create",
                "applied": False,
                "actual_old_oid": "2" * 40,
                "new_oid": "2" * 40,
            },
        )
        self.assertIsNotNone(raced)
        assert raced is not None
        self.assertEqual("remote-moved-at-cas", raced.failure_subcode)

    def test_absent_ref_success_establishes_and_reports_local_tracking(self) -> None:
        branch = "codex/v0.4.6.0-runtime-footprint-b11"
        target_ref = f"refs/heads/{branch}"
        expected_upstream = f"refs/remotes/origin/{branch}"
        with tempfile.TemporaryDirectory(prefix="daee-absent-ref-tracking-") as directory:
            root = Path(directory)
            _remote, local, head, _predecessor = self._tracking_repository(root, branch)

            with mock.patch.object(checker, "ROOT", local):
                result = checker.git_guarded_push_transport(
                    remote_name="origin",
                    target_ref=target_ref,
                    expected_old_oid=None,
                    new_oid=head,
                    force=False,
                    atomic=True,
                    mode="exact-absent-lease-create",
                )

            self.assertTrue(result["applied"], result)
            self.assertTrue(result.get("tracking_established"), result)
            self.assertEqual(expected_upstream, result["upstream_ref"])
            self.assertEqual(head, result["upstream_oid"])
            actual_upstream = subprocess.run(
                ["git", "-C", str(local), "rev-parse", "--symbolic-full-name", "@{upstream}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            actual_upstream_oid = subprocess.run(
                ["git", "-C", str(local), "rev-parse", "@{upstream}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(expected_upstream, actual_upstream)
            self.assertEqual(head, actual_upstream_oid)

    def test_absent_ref_tracking_rejects_symbolic_remote_tracking_ref(self) -> None:
        branch = "codex/v0.4.6.0-runtime-footprint-b11-symbolic"
        target_ref = f"refs/heads/{branch}"
        tracking_ref = f"refs/remotes/origin/{branch}"
        victim_ref = "refs/heads/tracking-victim"
        with tempfile.TemporaryDirectory(prefix="daee-absent-ref-symbolic-") as directory:
            root = Path(directory)
            _remote, local, head, predecessor = self._tracking_repository(root, branch)
            subprocess.run(
                ["git", "-C", str(local), "update-ref", victim_ref, predecessor],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(local), "symbolic-ref", tracking_ref, victim_ref],
                check=True,
                capture_output=True,
            )

            with mock.patch.object(checker, "ROOT", local):
                result = checker.git_guarded_push_transport(
                    remote_name="origin",
                    target_ref=target_ref,
                    expected_old_oid=None,
                    new_oid=head,
                    force=False,
                    atomic=True,
                    mode="exact-absent-lease-create",
                )

            self.assertFalse(result["applied"], result)
            self.assertFalse(result.get("tracking_established"), result)
            victim_oid = subprocess.run(
                ["git", "-C", str(local), "rev-parse", victim_ref],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            symbolic_target = subprocess.run(
                ["git", "-C", str(local), "symbolic-ref", tracking_ref],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(predecessor, victim_oid)
            self.assertEqual(victim_ref, symbolic_target)
            remote_rows = subprocess.run(
                ["git", "ls-remote", "--refs", "origin", target_ref],
                cwd=local,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual("", remote_rows)

    def test_absent_ref_tracking_uses_local_ref_compare_and_swap(self) -> None:
        branch = "codex/v0.4.6.0-runtime-footprint-b11-local-cas"
        target_ref = f"refs/heads/{branch}"
        tracking_ref = f"refs/remotes/origin/{branch}"
        zero_oid = "0" * 40
        with tempfile.TemporaryDirectory(prefix="daee-absent-ref-local-cas-") as directory:
            root = Path(directory)
            _remote, local, head, predecessor = self._tracking_repository(root, branch)
            original_run = subprocess.run
            injected = False

            def racing_run(command, *args, **kwargs):
                nonlocal injected
                if (
                    not injected
                    and command[:2] == ["git", "update-ref"]
                    and tracking_ref in command
                ):
                    injected = True
                    original_run(
                        ["git", "update-ref", "--no-deref", tracking_ref, predecessor, zero_oid],
                        cwd=local,
                        check=True,
                        capture_output=True,
                    )
                return original_run(command, *args, **kwargs)

            with (
                mock.patch.object(checker, "ROOT", local),
                mock.patch.object(checker.subprocess, "run", side_effect=racing_run),
            ):
                result = checker.git_guarded_push_transport(
                    remote_name="origin",
                    target_ref=target_ref,
                    expected_old_oid=None,
                    new_oid=head,
                    force=False,
                    atomic=True,
                    mode="exact-absent-lease-create",
                )

            self.assertTrue(injected)
            self.assertTrue(result["applied"], result)
            self.assertFalse(result.get("tracking_established"), result)
            tracking_oid = original_run(
                ["git", "-C", str(local), "rev-parse", tracking_ref],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(predecessor, tracking_oid)

    def test_absent_ref_tracking_rejects_incompatible_upstream_config(self) -> None:
        branch = "codex/v0.4.6.0-runtime-footprint-b11-config"
        target_ref = f"refs/heads/{branch}"
        with tempfile.TemporaryDirectory(prefix="daee-absent-ref-config-") as directory:
            root = Path(directory)
            _remote, local, head, _predecessor = self._tracking_repository(root, branch)
            subprocess.run(
                ["git", "-C", str(local), "config", f"branch.{branch}.remote", "wrong-remote"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(local), "config", f"branch.{branch}.merge", "refs/heads/wrong"],
                check=True,
                capture_output=True,
            )

            with mock.patch.object(checker, "ROOT", local):
                result = checker.git_guarded_push_transport(
                    remote_name="origin",
                    target_ref=target_ref,
                    expected_old_oid=None,
                    new_oid=head,
                    force=False,
                    atomic=True,
                    mode="exact-absent-lease-create",
                )

            self.assertFalse(result["applied"], result)
            self.assertFalse(result.get("tracking_established"), result)
            configured_remote = subprocess.run(
                ["git", "-C", str(local), "config", "--get", f"branch.{branch}.remote"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            configured_merge = subprocess.run(
                ["git", "-C", str(local), "config", "--get", f"branch.{branch}.merge"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual("wrong-remote", configured_remote)
            self.assertEqual("refs/heads/wrong", configured_merge)
            remote_rows = subprocess.run(
                ["git", "ls-remote", "--refs", "origin", target_ref],
                cwd=local,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual("", remote_rows)

    def test_absent_ref_transport_uses_server_empty_lease_and_rejects_races(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-absent-ref-cas-") as directory:
            root = Path(directory)
            created_branch = "authorized-create"
            remote, local, head, competitor = self._tracking_repository(root, created_branch)
            created_ref = f"refs/heads/{created_branch}"
            request = {
                "remote_name": "origin",
                "target_ref": created_ref,
                "expected_old_oid": None,
                "new_oid": head,
                "force": False,
                "atomic": True,
                "mode": "exact-absent-lease-create",
            }
            with mock.patch.object(checker, "ROOT", local):
                created = checker.git_guarded_push_transport(**request)
                self.assertTrue(created["applied"], created)
                self.assertIsNone(created["actual_old_oid"])
                self.assertEqual(head, created["new_oid"])
                self.assertEqual(
                    f"--force-with-lease={created_ref}:", created["lease_argument"]
                )

                same_oid_collision = checker.git_guarded_push_transport(**request)
                self.assertFalse(same_oid_collision["applied"], same_oid_collision)
                self.assertEqual(head, same_oid_collision["new_oid"])

                raced_branch = "raced-create"
                raced_ref = f"refs/heads/{raced_branch}"
                subprocess.run(
                    ["git", "-C", str(local), "switch", "-c", raced_branch],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "push", str(remote), f"{competitor}:{raced_ref}"],
                    cwd=local,
                    check=True,
                    capture_output=True,
                )
                raced = checker.git_guarded_push_transport(
                    **{**request, "target_ref": raced_ref}
                )
                self.assertFalse(raced["applied"], raced)
                remote_oid = subprocess.run(
                    ["git", "--git-dir", str(remote), "rev-parse", raced_ref],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                self.assertEqual(competitor, remote_oid)

                existing_branch = "existing-fast-forward"
                existing_ref = f"refs/heads/{existing_branch}"
                subprocess.run(
                    ["git", "-C", str(local), "switch", "-c", existing_branch],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "push", str(remote), f"{competitor}:{existing_ref}"],
                    cwd=local,
                    check=True,
                    capture_output=True,
                )
                existing = checker.git_guarded_push_transport(
                    **{
                        **request,
                        "target_ref": existing_ref,
                        "expected_old_oid": competitor,
                        "mode": "exact-old-lease",
                    }
                )
                self.assertTrue(existing["applied"], existing)
                self.assertEqual(competitor, existing["actual_old_oid"])
                self.assertEqual(head, existing["new_oid"])
                self.assertEqual(
                    f"--force-with-lease={existing_ref}:{competitor}",
                    existing["lease_argument"],
                )

    def test_absent_ref_claim_replay_and_receipt_remain_fail_closed(self) -> None:
        value, _raw, error = checker._load(
            FIXTURE_ROOT / "valid/exact-nonforce-branch-push.json"
        )
        self.assertIsNone(error)
        assert value is not None
        observed = checker._fixture_observation()
        value["remote_update_mode"] = "exact-absent-lease-create"
        value["expected_old_remote_oid"] = None
        observed.update(
            {
                "remote_oid": None,
                "old_object_type": None,
                "fast_forward": False,
            }
        )
        raw = checker.canonical_json_bytes(value)
        with tempfile.TemporaryDirectory(prefix="daee-absent-ref-receipt-") as directory:
            custody = Path(directory)
            claim_path = custody / "claims/create.claim.json"
            receipt_path = custody / "receipts/create.receipt.json"
            claim, finding = checker.consume_authorization(
                value,
                raw,
                observed,
                custody_root=custody,
                claim_target=claim_path,
                claimed_at=observed["now"],
            )
            self.assertIsNone(finding)
            self.assertIsNotNone(claim)
            _replayed, replay = checker.consume_authorization(
                value,
                raw,
                observed,
                custody_root=custody,
                claim_target=claim_path,
                claimed_at=observed["now"],
            )
            self.assertIsNotNone(replay)
            assert replay is not None
            self.assertEqual("authorization-replay", replay.failure_subcode)

            wrong_remote = {
                **observed,
                "remote_oid": "2" * 40,
                "result_commit_oid": value["local_commit"],
                "result_tree_oid": value["local_tree"],
            }
            _receipt, wrong_finding = checker.finalize_authorization(
                value,
                raw,
                claim_path,
                "PASS",
                wrong_remote,
                custody_root=custody,
                receipt_target=receipt_path,
                finalized_at=observed["now"],
            )
            self.assertIsNotNone(wrong_finding)
            self.assertFalse(receipt_path.exists())

            final_observed = {
                **observed,
                "remote_oid": value["local_commit"],
                "result_commit_oid": value["local_commit"],
                "result_tree_oid": value["local_tree"],
            }
            _receipt, missing_upstream = checker.finalize_authorization(
                value,
                raw,
                claim_path,
                "PASS",
                final_observed,
                custody_root=custody,
                receipt_target=receipt_path,
                finalized_at=observed["now"],
            )
            self.assertIsNotNone(missing_upstream)
            assert missing_upstream is not None
            self.assertEqual("push-upstream", missing_upstream.failure_subcode)
            self.assertFalse(receipt_path.exists())

            final_observed.update(
                {
                    "upstream_ref": f"refs/remotes/{value['remote_name']}/{value['target_branch']}",
                    "upstream_oid": value["local_commit"],
                }
            )
            receipt, final_finding = checker.finalize_authorization(
                value,
                raw,
                claim_path,
                "PASS",
                final_observed,
                custody_root=custody,
                receipt_target=receipt_path,
                finalized_at=observed["now"],
            )
            self.assertIsNone(final_finding)
            self.assertIsNotNone(receipt)
            assert receipt is not None
            self.assertEqual(value["local_commit"], receipt["observed_remote_oid"])

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
