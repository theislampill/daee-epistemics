#!/usr/bin/env python3
"""Validate and consume exact immutable commit/push action authorizations."""
from __future__ import annotations

import argparse
import getpass
import json
import os
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from a16_immutable_custody import (
    CustodyError,
    append_claim_before_cas,
    canonical_json_bytes,
    iter_immutable_records,
    publish_json_idempotent,
    publish_terminal_receipt,
    read_cas_pointer,
    sha256_bytes,
)
from contract_validation import PathCustodyError, resolve_repo_path, validate_schema_subset
from source_provenance import DuplicateObjectKey, strict_json_loads


ROOT = Path(__file__).resolve().parents[1]
RUN_REL = Path(".IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5")
AUTH_ROOT = ROOT / RUN_REL / "evidence/vcs-action/authorizations"
CUSTODY_ROOT = ROOT / RUN_REL / "evidence/vcs-action"
SCHEMA_PATH = ROOT / "schema/vcs-action-authorization.schema.json"
EXPECTATION_SCHEMA_PATH = ROOT / "schema/negative-fixture-expectation.schema.json"
FIXTURE_ROOT = ROOT / "tests/vcs-action-authorization"
CHECKER_ID = "vcs-action-authorization"
DOWNSTREAM = ["commit", "push", "exact-sha-ci", "candidate-package", "release-action"]
ACTIONS = {"commit-countermeasure": "commit-authorization", "push-countermeasure": "push-authorization"}


@dataclass(frozen=True)
class Finding:
    failure_class: str
    failure_subcode: str
    message: str


def diagnostic(finding: Finding, artifact: str) -> dict[str, Any]:
    return {
        "artifact": artifact,
        "checker_id": CHECKER_ID,
        "downstream_invalidated": DOWNSTREAM,
        "earliest_stage": "control-plane",
        "exit_category": "structural-rejection",
        "exit_code": 1,
        "failure_class": finding.failure_class,
        "failure_subcode": finding.failure_subcode,
        "message": finding.message,
    }


def _load(path: Path) -> tuple[dict[str, Any] | None, bytes, Finding | None]:
    try:
        raw = path.read_bytes()
        value = strict_json_loads(raw, label=str(path))
    except DuplicateObjectKey as exc:
        return None, b"", Finding("malformed_json", "duplicate-key", f"duplicate JSON object key nonce: {exc}")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return None, b"", Finding("malformed_json", "malformed-json", str(exc))
    if not isinstance(value, dict):
        return None, raw, Finding("authorization_family", "root-shape", "VCS authorization root must be an object")
    return value, raw, None


def _schema() -> dict[str, Any]:
    value = strict_json_loads(SCHEMA_PATH.read_bytes(), label=str(SCHEMA_PATH))
    if not isinstance(value, dict):
        raise ValueError("VCS authorization schema root must be an object")
    return value


def _parse_time(value: Any, field: str) -> tuple[datetime | None, Finding | None]:
    try:
        parsed = datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None, Finding("validity_window", "timestamp", f"{field} must be RFC3339 UTC seconds")
    return parsed, None


def _expected_locator(value: dict[str, Any], leaf: str) -> str:
    area = "claims" if leaf == "claim" else "receipts"
    suffix = "claim" if leaf == "claim" else "receipt"
    return (RUN_REL / "evidence/vcs-action" / area / f"{value['authorization_id']}.{suffix}.json").as_posix()


def resolve_live_authorization_path(candidate: Path, *, authority_root: Path = AUTH_ROOT) -> Path:
    """Resolve an issued manifest strictly beneath the protected authority root."""

    root = authority_root.resolve(strict=True)
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"resolved authorization leaves protected root: {candidate} -> {resolved}") from exc
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError("authorization must be one resolved regular file")
    return resolved


def find_existing_action_records(custody_root: Path, authorization_sha256: str, nonce: str) -> list[tuple[Path, dict[str, Any], str]]:
    """Search only immutable claim/receipt namespaces, never authorization inputs."""

    matches: list[tuple[Path, dict[str, Any], str]] = []
    for namespace in ("claims", "receipts"):
        root = custody_root / namespace
        if not root.is_dir():
            continue
        for row in iter_immutable_records(root):
            record = row[1]
            if record.get("schema") not in {"vcs-action-claim-v1", "vcs-action-receipt-v1"}:
                continue
            if record.get("authorization_sha256") == authorization_sha256 or record.get("nonce") == nonce:
                matches.append(row)
    return matches


def result_requires_live_observation(result: str) -> bool:
    return result == "PASS"


def resolve_live_custody_path(locator: str, namespace: str, *, must_exist: bool) -> Path:
    """Resolve an exact claim/receipt locator beneath its fixed live namespace."""

    target = resolve_repo_path(
        ROOT, locator, must_exist=must_exist, expect_file=must_exist
    )
    namespace_root = (CUSTODY_ROOT / namespace).resolve()
    try:
        target.relative_to(namespace_root)
    except ValueError as exc:
        raise PathCustodyError(
            f"{namespace} locator leaves fixed VCS custody namespace: {locator}",
            subcode="custody-namespace",
        ) from exc
    return target


def hash_commit_message_file(path: Path) -> str:
    raw = path.read_bytes()
    if not raw or raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise ValueError("commit message bytes must be BOM-free UTF-8/LF with exactly one final LF")
    raw.decode("utf-8")
    return sha256_bytes(raw)


def guarded_push_update(value: dict[str, Any], *, observation: dict[str, Any], transport: Any) -> Finding | None:
    """Execute one injected exact-old lease only after full-history FF proof."""

    if value.get("force") is not False:
        return Finding("force_forbidden", "force", "guarded push requires force=false")
    guards = {
        "remote_oid": value.get("expected_old_remote_oid"), "fast_forward": True,
        "replace_objects_disabled": True, "shallow": False, "grafts_present": False,
        "old_object_type": "commit", "new_object_type": "commit",
    }
    for field, expected in guards.items():
        if observation.get(field) != expected:
            return Finding("remote_drift", f"guard-{field.replace('_','-')}", f"guarded push {field} must equal {expected!r}")
    result = transport(
        remote_name=value["remote_name"], target_ref=value["target_ref"],
        expected_old_oid=value["expected_old_remote_oid"], new_oid=value["local_commit"],
        force=False, atomic=True, mode="exact-old-lease",
    )
    if not isinstance(result, dict) or result.get("mode") != "exact-old-lease":
        return Finding("remote_drift", "transport-proof", "guarded transport returned no exact-old lease proof")
    if result.get("applied") is not True:
        return Finding("remote_drift", "remote-moved-at-cas", f"remote moved at exact-old CAS: {result.get('actual_old_oid')}")
    if result.get("actual_old_oid") != value["expected_old_remote_oid"] or result.get("new_oid") != value["local_commit"]:
        return Finding("remote_drift", "transport-binding", "server CAS receipt old/new OIDs differ from authorization")
    return None


def git_guarded_push_transport(**request: Any) -> dict[str, Any]:
    """Production transport; not called by self-tests or this Task 3a run."""

    ref = request["target_ref"]; expected = request["expected_old_oid"]; new = request["new_oid"]
    command = ["git", "push", "--atomic", "--porcelain", f"--force-with-lease={ref}:{expected}", request["remote_name"], f"{new}:{ref}"]
    env = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}
    result = subprocess.run(command, cwd=ROOT, capture_output=True, env=env, check=False)
    lines = subprocess.run(["git", "ls-remote", "--refs", request["remote_name"], ref], cwd=ROOT, capture_output=True, env=env, check=False)
    remote = lines.stdout.decode("utf-8", errors="replace").split()
    actual = remote[0] if remote else None
    return {"mode":"exact-old-lease", "applied":result.returncode == 0 and actual == new,
            "actual_old_oid":expected if result.returncode == 0 else actual, "new_oid":actual,
            "exit_code":result.returncode, "stdout":result.stdout.decode("utf-8", errors="replace"),
            "stderr":result.stderr.decode("utf-8", errors="replace")}


def _authority_file_protected(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    for protected in (path, path.parent):
        mode = protected.stat(follow_symlinks=False).st_mode
        if (mode & stat.S_IWRITE) if os.name == "nt" else (mode & 0o222):
            return False
    return True


def _path_findings(value: dict[str, Any]) -> list[Finding]:
    for row in value.get("scoped_paths", []):
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            continue
        try:
            resolve_repo_path(ROOT, row["path"], must_exist=False)
        except PathCustodyError as exc:
            message = f"scoped path {row['path']}: {exc}"
            if exc.subcode == "path-traversal":
                message = f"parent traversal is forbidden in scoped path {row['path']}"
            return [Finding("path_custody", exc.subcode, message)]
    for field in ("commit_message_path", "verification_verdict_path", "claim_locator", "action_receipt_locator"):
        raw = value.get(field)
        if not isinstance(raw, str):
            continue
        try:
            resolve_repo_path(ROOT, raw, must_exist=False)
        except PathCustodyError as exc:
            return [Finding("path_custody", exc.subcode, f"{field} {raw}: {exc}")]
    return []


def validate_authorization(value: dict[str, Any], observed: dict[str, Any]) -> list[Finding]:
    if value.get("schema") != "vcs-action-authorization-v1" or value.get("kind") not in ACTIONS.values():
        if value.get("kind") == "matrix-authorization":
            return [Finding("authorization_family", "matrix-substitution", "matrix-authorization cannot satisfy a VCS action gate")]
        return [Finding("authorization_family", "wrong-family", "record is not a VCS commit/push authorization")]
    kind = value.get("kind")
    action = value.get("action")
    if ACTIONS.get(str(action)) != kind:
        return [Finding("action_family", "action-family", f"{kind} cannot authorize {action}; commit-authorization and push-countermeasure are distinct")]
    if value.get("revoked") is True:
        return [Finding("authorization_revoked", "revoked", "revoked must remain false")]
    if kind == "push-authorization" and value.get("force") is not False:
        return [Finding("force_forbidden", "force", "force must be false for every push authorization")]
    path_issues = _path_findings(value)
    if path_issues:
        return path_issues
    ref_check = subprocess.run(["git", "check-ref-format", str(value.get("target_ref", ""))], cwd=ROOT, capture_output=True)
    if ref_check.returncode:
        return [Finding("ref_drift", "ref-format", f"target_ref is not a valid full Git ref: {value.get('target_ref')}")]
    issues = validate_schema_subset(value, _schema())
    if issues:
        issue = issues[0]
        return [Finding("schema_contract", f"schema-{issue.keyword.lower()}", f"{issue.path}: {issue.message}")]
    expected_allowed = [str(action)]
    expected_denied = (
        ["force-push", "publish", "push", "release", "tag"]
        if kind == "commit-authorization"
        else ["force-push", "publish", "release", "tag"]
    )
    if value["allowed_actions"] != expected_allowed or value["denied_actions"] != expected_denied:
        return [Finding("action_scope", "action-set", "allowed_actions must contain one exact action and denied tag/release/publish actions must be exact sorted unique")]
    paths = [row["path"] for row in value["scoped_paths"]]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        return [Finding("scope_drift", "scoped-path-order", "scoped_paths must be exact sorted unique paths")]
    if value["claim_locator"] != _expected_locator(value, "claim") or value["action_receipt_locator"] != _expected_locator(value, "receipt"):
        return [Finding("claim_locator", "claim-locator", "claim_locator/action receipt must be derived from authorization_id under fixed custody prefixes")]
    issued, finding = _parse_time(value["issued_at"], "issued_at")
    if finding:
        return [finding]
    not_before, finding = _parse_time(value["valid_not_before"], "valid_not_before")
    if finding:
        return [finding]
    not_after, finding = _parse_time(value["valid_not_after"], "valid_not_after")
    if finding:
        return [finding]
    now, finding = _parse_time(observed.get("now"), "observed now")
    if finding:
        return [finding]
    assert issued and not_before and not_after and now
    if not (issued <= not_before < not_after):
        return [Finding("validity_window", "window-order", "issued_at <= valid_not_before < valid_not_after is required")]
    if now < not_before:
        return [Finding("validity_window", "not-yet-valid", "valid_not_before is in the future; authorization is not yet valid")]
    if now > not_after:
        return [Finding("validity_window", "expired", "valid_not_after has passed; authorization is expired")]
    for field, failure_class, subcode in (
        ("repository", "repository_drift", "repository"),
        ("remote_name", "remote_drift", "remote-name"),
        ("target_branch", "branch_drift", "target-branch"),
        ("target_ref", "ref_drift", "target-ref"),
        ("writer_boundary_identity", "writer_boundary", "writer-identity"),
    ):
        if value[field] != observed.get(field):
            return [Finding(failure_class, subcode, f"{field}={value[field]!r} differs from observed writer/repository/branch/ref state {observed.get(field)!r}")]
    if value["expected_claim_predecessor_sha256"] != observed.get("claim_head_sha256"):
        return [Finding("cas_predecessor", "predecessor-mismatch", "expected_claim_predecessor_sha256 differs from the locked custody head")]
    if value["scoped_paths"] != observed.get("scoped_paths"):
        return [Finding("scope_drift", "scoped-paths", "scoped_paths differ from the exact staged/commit path-hash manifest")]
    for field, subcode, label in (
        ("staged_diff_sha256", "staged-diff", "staged diff"),
        ("commit_message_sha256", "commit-message", "message"),
        ("verification_verdict_sha256", "verification-verdict", "verification"),
    ):
        if value[field] != observed.get(field):
            return [Finding("scope_drift", subcode, f"{field} differs from observed {label} hash")]
    if kind == "commit-authorization":
        if value["parent_commit"] != observed.get("head_commit"):
            return [Finding("source_drift", "parent-commit", "parent_commit differs from observed HEAD")]
        if value["parent_tree"] != observed.get("head_tree"):
            return [Finding("source_drift", "parent-tree", "parent_tree differs from observed tree")]
        if value["staged_tree"] != observed.get("staged_tree"):
            return [Finding("source_drift", "staged-tree", "staged_tree differs from the staged tree")]
    else:
        if value.get("remote_update_mode") != "exact-old-lease-fast-forward":
            return [Finding("force_forbidden", "remote-update-mode", "push requires exact-old lease plus independently proved fast-forward transport")]
        if value["local_commit"] != observed.get("local_commit"):
            return [Finding("source_drift", "local-commit", "local_commit differs from the local commit")]
        if value["local_tree"] != observed.get("local_tree"):
            return [Finding("source_drift", "local-tree", "local_tree differs from the local tree")]
        if value["expected_old_remote_oid"] != observed.get("remote_oid"):
            return [Finding("remote_drift", "expected-old-remote-oid", "expected_old_remote_oid differs from reread remote ref")]
        for field, expected in (
            ("replace_objects_disabled", True),
            ("shallow", False),
            ("grafts_present", False),
            ("old_object_type", "commit"),
            ("new_object_type", "commit"),
        ):
            if observed.get(field) != expected:
                return [
                    Finding(
                        "remote_drift",
                        f"guard-{field.replace('_', '-')}",
                        f"full-history push guard {field} must equal {expected!r}",
                    )
                ]
        if observed.get("fast_forward") is not True:
            return [Finding("remote_drift", "non-fast-forward", "expected old remote OID is not an ancestor of local_commit")]
        if value["workflow_check_snapshot"] != observed.get("workflow_check_snapshot"):
            return [Finding("workflow_drift", "workflow-check-snapshot", "workflow/check snapshot differs from authorization-time state")]
        receipt_ref = value["commit_receipt"]
        try:
            receipt_path = resolve_repo_path(ROOT, receipt_ref["path"], must_exist=True, expect_file=True)
            receipt_raw = receipt_path.read_bytes()
            receipt = strict_json_loads(receipt_raw, label=str(receipt_path))
        except (PathCustodyError, OSError, ValueError, json.JSONDecodeError) as exc:
            return [Finding("commit_receipt", "receipt-read", f"commit receipt read failed: {exc}")]
        if sha256_bytes(receipt_raw) != receipt_ref["sha256"]:
            return [Finding("commit_receipt", "receipt-hash", "commit receipt hash differs")]
        receipt_schema_issues = validate_schema_subset(receipt, _schema())
        if receipt_schema_issues or receipt.get("schema") != "vcs-action-receipt-v1" or receipt.get("result") != "PASS":
            return [Finding("commit_receipt", "receipt-result", "commit receipt must be a schema-valid terminal PASS")]
        if receipt.get("observed_commit_oid") != value["local_commit"] or receipt.get("observed_tree_oid") != value["local_tree"]:
            return [Finding("commit_receipt", "receipt-source", "commit receipt commit/tree differ from push authorization")]
        for field in ("scoped_paths", "staged_diff_sha256", "commit_message_sha256", "verification_verdict_sha256"):
            if receipt.get(field) != value[field]:
                return [Finding("commit_receipt", f"receipt-{field.replace('_','-')}", f"commit receipt {field} differs")]
    return []


def _claim_id(authorization_sha256: str, nonce: str) -> str:
    return sha256_bytes(b"vcs-action-claim-v1\0" + bytes.fromhex(authorization_sha256) + b"\0" + nonce.encode("utf-8"))


def _receipt_id(claim_sha256: str, result: str) -> str:
    return sha256_bytes(b"vcs-action-receipt-v1\0" + bytes.fromhex(claim_sha256) + b"\0" + result.encode("ascii"))


def consume_authorization(
    value: dict[str, Any], raw: bytes, observed: dict[str, Any], *, custody_root: Path,
    claim_target: Path, claimed_at: str,
) -> tuple[dict[str, Any] | None, Finding | None]:
    findings = validate_authorization(value, observed)
    if findings:
        return None, findings[0]
    authorization_sha256 = sha256_bytes(raw)
    matching = find_existing_action_records(custody_root, authorization_sha256, value["nonce"])
    if matching:
        record_path, record, _record_digest = matching[0]
        head = read_cas_pointer(custody_root)
        adoptable = (
            len(matching) == 1
            and record_path.resolve() == claim_target.resolve()
            and record.get("schema") == "vcs-action-claim-v1"
            and record.get("authorization_sha256") == authorization_sha256
            and record.get("authorization_id") == value["authorization_id"]
            and record.get("nonce") == value["nonce"]
            and record.get("action") == value["action"]
            and record.get("predecessor_record_sha256") == value["expected_claim_predecessor_sha256"]
            and head["last_record_sha256"] == value["expected_claim_predecessor_sha256"]
        )
        if adoptable:
            try:
                append_claim_before_cas(custody_root, claim_target, record, expected_predecessor_sha256=value["expected_claim_predecessor_sha256"])
            except CustodyError as exc:
                return None, Finding("claim_custody", exc.subcode, str(exc))
            return record, None
        return None, Finding("authorization_replay", "authorization-replay", "authorization digest/nonce already has a claim or receipt")
    claim = {
        "schema": "vcs-action-claim-v1",
        "kind": "vcs-action-claim",
        "claim_id": _claim_id(authorization_sha256, value["nonce"]),
        "authorization_sha256": authorization_sha256,
        "authorization_id": value["authorization_id"],
        "nonce": value["nonce"],
        "action": value["action"],
        "claim_locator": value["claim_locator"],
        "action_receipt_locator": value["action_receipt_locator"],
        "writer_boundary_identity": value["writer_boundary_identity"],
        "claimed_at": claimed_at,
        "predecessor_record_sha256": value["expected_claim_predecessor_sha256"],
        "status": "CLAIMED",
        "terminal_claim": False,
    }
    if validate_schema_subset(claim, _schema()):
        return None, Finding("claim_schema", "claim-schema", "generated claim failed its schema")
    try:
        append_claim_before_cas(
            custody_root, claim_target, claim,
            expected_predecessor_sha256=value["expected_claim_predecessor_sha256"],
        )
    except CustodyError as exc:
        if exc.subcode == "publication-collision":
            return None, Finding("claim_collision", "claim-collision", "claim path contains different bytes")
        return None, Finding("claim_custody", exc.subcode, str(exc))
    return claim, None


def finalize_authorization(
    value: dict[str, Any], raw: bytes, claim_path: Path, result: str, observed: dict[str, Any],
    *, custody_root: Path, receipt_target: Path, finalized_at: str,
) -> tuple[dict[str, Any] | None, Finding | None]:
    try:
        claim_raw = claim_path.read_bytes()
        claim = strict_json_loads(claim_raw, label=str(claim_path))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, Finding("claim_custody", "claim-read", f"claim receipt read failed: {exc}")
    if validate_schema_subset(claim, _schema()) or claim.get("schema") != "vcs-action-claim-v1":
        return None, Finding("claim_custody", "claim-schema", "claim receipt is not a valid immutable VCS claim")
    authorization_sha256 = sha256_bytes(raw)
    if any(claim.get(field) != expected for field, expected in (
        ("authorization_sha256", authorization_sha256), ("authorization_id", value["authorization_id"]),
        ("nonce", value["nonce"]), ("action", value["action"]),
    )):
        return None, Finding("claim_custody", "claim-binding", "claim receipt differs from authorization")
    if result == "PASS":
        findings = validate_action_result(value, observed)
        if findings:
            return None, findings[0]
        if value["kind"] == "push-authorization" and observed.get("remote_oid") != value["local_commit"]:
            return None, Finding("remote_drift", "push-result", "PASS requires live remote ref to equal local_commit")
    claim_sha256 = sha256_bytes(claim_raw)
    receipt = {
        "schema": "vcs-action-receipt-v1", "kind": "vcs-action-receipt",
        "receipt_id": _receipt_id(claim_sha256, result), "claim_sha256": claim_sha256,
        "authorization_sha256": authorization_sha256, "authorization_id": value["authorization_id"],
        "nonce": value["nonce"], "action": value["action"], "result": result,
        "writer_boundary_identity": value["writer_boundary_identity"], "finalized_at": finalized_at,
        "observed_commit_oid": observed.get("result_commit_oid") if result == "PASS" else None,
        "observed_tree_oid": observed.get("result_tree_oid") if result == "PASS" else None,
        "observed_remote_oid": observed.get("remote_oid") if result == "PASS" and value["kind"] == "push-authorization" else None,
        "scoped_paths": value["scoped_paths"], "staged_diff_sha256": value["staged_diff_sha256"],
        "commit_message_sha256": value["commit_message_sha256"],
        "verification_verdict_sha256": value["verification_verdict_sha256"],
        "terminal": True, "terminal_claim": False,
    }
    if result == "PASS" and value["kind"] == "commit-authorization":
        if receipt["observed_commit_oid"] is None or receipt["observed_tree_oid"] != value["staged_tree"]:
            return None, Finding("action_result", "commit-result", "commit PASS requires observed commit and exact staged tree")
    if validate_schema_subset(receipt, _schema()):
        return None, Finding("receipt_schema", "receipt-schema", "generated action receipt failed its schema")
    try:
        publish_terminal_receipt(custody_root, receipt_target, receipt)
    except CustodyError as exc:
        return None, Finding("receipt_custody", exc.subcode, str(exc))
    return receipt, None


def validate_action_result(value: dict[str, Any], observed: dict[str, Any]) -> list[Finding]:
    for field, cls, sub in (
        ("repository", "repository_drift", "repository"),
        ("remote_name", "remote_drift", "remote-name"),
        ("target_branch", "branch_drift", "target-branch"),
        ("target_ref", "ref_drift", "target-ref"),
        ("writer_boundary_identity", "writer_boundary", "writer-identity"),
    ):
        if value[field] != observed.get(field):
            return [Finding(cls, sub, f"final {field} differs from the authorization")]
    if value["kind"] == "commit-authorization":
        if observed.get("result_parent_commits") != [value["parent_commit"]]:
            return [Finding("action_result", "commit-parent", "commit receipt requires exactly one authorized parent")]
        if observed.get("result_tree_oid") != value["staged_tree"]:
            return [Finding("action_result", "commit-tree", "committed tree differs from staged_tree")]
        for field in ("scoped_paths", "staged_diff_sha256", "commit_message_sha256", "verification_verdict_sha256"):
            if observed.get(field) != value[field]:
                return [Finding("action_result", f"commit-{field.replace('_','-')}", f"committed {field} differs from authorization")]
    else:
        if observed.get("local_commit") != value["local_commit"] or observed.get("local_tree") != value["local_tree"]:
            return [Finding("action_result", "push-local-source", "push final local commit/tree differ")]
        if observed.get("remote_oid") != value["local_commit"]:
            return [Finding("remote_drift", "push-result", "push PASS requires live remote ref to equal local_commit")]
    return []


def _git(*args: str, binary: bool = False) -> bytes | str:
    env = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, env=env, check=False)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip() or f"git {' '.join(args)} failed")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def _repository_name(remote_url: str) -> str:
    text = remote_url.rstrip("/")
    if text.endswith(".git"):
        text = text[:-4]
    if ":" in text and not text.startswith(("http://", "https://")):
        text = text.rsplit(":", 1)[-1]
    else:
        text = text.rsplit("/", 2)[-2] + "/" + text.rsplit("/", 1)[-1]
    return text


def collect_live_observation(value: dict[str, Any]) -> dict[str, Any]:
    branch = str(_git("branch", "--show-current"))
    remote = value["remote_name"]
    head = str(_git("rev-parse", "HEAD"))
    head_tree = str(_git("rev-parse", "HEAD^{tree}"))
    verification = resolve_repo_path(ROOT, value["verification_verdict_path"], must_exist=True, expect_file=True)
    observation: dict[str, Any] = {
        "now": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository": _repository_name(str(_git("remote", "get-url", remote))), "remote_name": remote,
        "target_branch": branch, "target_ref": f"refs/heads/{branch}",
        "writer_boundary_identity": f"os-user:{getpass.getuser()}",
        "head_commit": head, "head_tree": head_tree,
        "verification_verdict_sha256": sha256_bytes(verification.read_bytes()),
        "claim_head_sha256": read_cas_pointer(CUSTODY_ROOT)["last_record_sha256"],
    }
    if value["kind"] == "commit-authorization":
        names = bytes(_git("diff", "--cached", "--name-only", "-z", binary=True)).split(b"\0")
        paths = [item.decode("utf-8") for item in names if item]
        observation["scoped_paths"] = [{"path": path, "sha256": sha256_bytes(bytes(_git("show", f":{path}", binary=True)))} for path in sorted(paths)]
        observation["staged_tree"] = str(_git("write-tree"))
        diff = bytes(_git("diff", "--cached", "--binary", "--full-index", "--no-ext-diff", "--no-color", binary=True))
        observation["staged_diff_sha256"] = sha256_bytes(diff)
        message_path = resolve_repo_path(
            ROOT, value["commit_message_path"], must_exist=True, expect_file=True
        )
        observation["commit_message_sha256"] = hash_commit_message_file(message_path)
    else:
        local = value["local_commit"]
        observation.update({"local_commit": str(_git("rev-parse", "HEAD")), "local_tree": str(_git("rev-parse", f"{local}^{{tree}}"))})
        rows = []
        for row in value["scoped_paths"]:
            rows.append({"path": row["path"], "sha256": sha256_bytes(bytes(_git("show", f"{local}:{row['path']}", binary=True)))})
        observation["scoped_paths"] = rows
        receipt_path = resolve_repo_path(ROOT, value["commit_receipt"]["path"], must_exist=True, expect_file=True)
        receipt = strict_json_loads(receipt_path.read_bytes(), label=str(receipt_path))
        observation["staged_diff_sha256"] = receipt["staged_diff_sha256"]
        message = bytes(_git("show", "-s", "--format=%B", local, binary=True)).rstrip(b"\r\n") + b"\n"
        observation["commit_message_sha256"] = sha256_bytes(message)
        lines = str(_git("ls-remote", "--refs", remote, value["target_ref"])).splitlines()
        observation["remote_oid"] = lines[0].split()[0] if lines else None
        shallow = str(_git("rev-parse", "--is-shallow-repository")) == "true"
        graft_path = Path(str(_git("rev-parse", "--git-path", "info/grafts")))
        if not graft_path.is_absolute():
            graft_path = ROOT / graft_path
        grafts_present = graft_path.is_file() and bool(graft_path.read_bytes().strip())
        remote_oid = observation["remote_oid"]
        observation.update(
            {
                "replace_objects_disabled": True,
                "shallow": shallow,
                "grafts_present": grafts_present,
                "old_object_type": str(_git("cat-file", "-t", str(remote_oid))) if remote_oid else None,
                "new_object_type": str(_git("cat-file", "-t", local)),
            }
        )
        env = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}
        ff = (
            remote_oid is not None
            and not shallow
            and not grafts_present
            and observation["old_object_type"] == "commit"
            and observation["new_object_type"] == "commit"
            and subprocess.run(
                ["git", "merge-base", "--is-ancestor", str(remote_oid), local],
                cwd=ROOT,
                capture_output=True,
                env=env,
                check=False,
            ).returncode
            == 0
        )
        observation["fast_forward"] = ff
        workflow = value["workflow_check_snapshot"]
        workflow_path = resolve_repo_path(ROOT, workflow["workflow_path"], must_exist=True, expect_file=True)
        observation["workflow_check_snapshot"] = {**workflow, "workflow_sha256": sha256_bytes(workflow_path.read_bytes()), "workflow_blob_oid": str(_git("rev-parse", f"{local}:{workflow['workflow_path']}"))}
    return observation


def collect_final_observation(value: dict[str, Any]) -> dict[str, Any]:
    branch = str(_git("branch", "--show-current")); remote = value["remote_name"]
    common = {
        "repository": _repository_name(str(_git("remote", "get-url", remote))), "remote_name": remote,
        "target_branch": branch, "target_ref": f"refs/heads/{branch}",
        "writer_boundary_identity": f"os-user:{getpass.getuser()}",
    }
    if value["kind"] == "commit-authorization":
        commit = str(_git("rev-parse", "HEAD")); tree = str(_git("rev-parse", "HEAD^{tree}"))
        parents = str(_git("show", "-s", "--format=%P", commit)).split()
        names = bytes(_git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit, binary=True)).split(b"\0")
        paths = sorted(item.decode("utf-8") for item in names if item)
        rows = [{"path": path, "sha256": sha256_bytes(bytes(_git("show", f"{commit}:{path}", binary=True)))} for path in paths]
        diff = bytes(_git("diff", "--binary", "--full-index", "--no-ext-diff", "--no-color", value["parent_commit"], commit, binary=True))
        message = bytes(_git("show", "-s", "--format=%B", commit, binary=True)).rstrip(b"\r\n") + b"\n"
        verification = resolve_repo_path(ROOT, value["verification_verdict_path"], must_exist=True, expect_file=True)
        return {**common, "result_commit_oid": commit, "result_tree_oid": tree, "result_parent_commits": parents,
                "scoped_paths": rows, "staged_diff_sha256": sha256_bytes(diff), "commit_message_sha256": sha256_bytes(message),
                "verification_verdict_sha256": sha256_bytes(verification.read_bytes())}
    local = str(_git("rev-parse", "HEAD")); tree = str(_git("rev-parse", "HEAD^{tree}"))
    lines = str(_git("ls-remote", "--refs", remote, value["target_ref"])).splitlines()
    return {**common, "local_commit": local, "local_tree": tree, "remote_oid": lines[0].split()[0] if lines else None,
            "result_commit_oid": local, "result_tree_oid": tree}


def _fixture_observation() -> dict[str, Any]:
    support = strict_json_loads((FIXTURE_ROOT / "support/observations.json").read_bytes(), label="VCS support observations")
    return dict(support["observed"])


def _expectation_ok(path: Path, finding: Finding) -> tuple[bool, str]:
    expectation_path = path.with_suffix(".expectation.json")
    if not expectation_path.is_file():
        return False, "missing same-stem expectation"
    expectation = strict_json_loads(expectation_path.read_bytes(), label=str(expectation_path))
    schema = strict_json_loads(EXPECTATION_SCHEMA_PATH.read_bytes(), label=str(EXPECTATION_SCHEMA_PATH))
    if validate_schema_subset(expectation, schema):
        return False, "expectation schema invalid"
    actual = diagnostic(finding, path.as_posix())
    for actual_key, expected_key in (("checker_id", "expected_checker_id"), ("exit_category", "expected_exit_category"), ("exit_code", "expected_exit_code"), ("earliest_stage", "expected_earliest_stage"), ("failure_class", "expected_failure_class"), ("failure_subcode", "expected_failure_subcode"), ("downstream_invalidated", "expected_downstream_invalidated")):
        if actual[actual_key] != expectation[expected_key]:
            return False, f"wrong reason {actual_key}: {actual[actual_key]!r}"
    text = json.dumps(actual, sort_keys=True)
    for marker in expectation["required_diagnostic_markers"]:
        if marker.lower() not in text.lower():
            return False, f"missing marker {marker!r}"
    return True, ""


def self_test() -> int:
    problems: list[str] = []
    observed = _fixture_observation()
    valid = sorted((FIXTURE_ROOT / "valid").glob("*.json"))
    invalid = sorted(path for path in (FIXTURE_ROOT / "invalid").glob("*.json") if not path.name.endswith(".expectation.json"))
    for path in valid:
        value, _raw, error = _load(path)
        findings = [error] if error else validate_authorization(value, observed)  # type: ignore[arg-type]
        if any(findings):
            problems.append(f"{path.name}: valid rejected: {next(item for item in findings if item)}")
    for path in invalid:
        value, raw, error = _load(path)
        finding = error
        if finding is None and path.name == "claim-collision.json":
            with tempfile.TemporaryDirectory(prefix="daee-vcs-claim-collision-") as directory:
                custody = Path(directory); target = custody / "claims/collision.claim.json"
                publish_json_idempotent(custody, target, {"schema": "competitor-v1"})
                _claim, finding = consume_authorization(value, raw, observed, custody_root=custody, claim_target=target, claimed_at=observed["now"])
        elif finding is None and value.get("schema") == "vcs-action-receipt-v1":
            issues = validate_schema_subset(value, _schema())
            if issues:
                issue = issues[0]
                finding = Finding(
                    "receipt_schema",
                    f"schema-{issue.keyword.lower()}",
                    f"terminal PASS receipt rejected: {issue.path}: {issue.message}",
                )
        elif finding is None:
            findings = validate_authorization(value, observed)
            finding = findings[0] if findings else None
        if finding is None:
            problems.append(f"{path.name}: invalid fixture survived")
            continue
        ok, problem = _expectation_ok(path, finding)
        if not ok:
            problems.append(f"{path.name}: {problem}; got {finding}")
    # Real create-once/replay and terminal FAILED/UNKNOWN behavior in temp custody only.
    value, raw, error = _load(FIXTURE_ROOT / "valid/exact-countermeasure-commit.json")
    if error is None:
        with tempfile.TemporaryDirectory(prefix="daee-vcs-claim-self-test-") as directory:
            custody = Path(directory); claim_path = custody / "claims/commit.claim.json"
            claim, first = consume_authorization(value, raw, observed, custody_root=custody, claim_target=claim_path, claimed_at=observed["now"])
            _again, replay = consume_authorization(value, raw, observed, custody_root=custody, claim_target=claim_path, claimed_at=observed["now"])
            if first or claim is None or replay is None or replay.failure_class != "authorization_replay":
                problems.append("create-once authorization replay was not rejected")
            receipt_path = custody / "receipts/commit.receipt.json"
            receipt, final_error = finalize_authorization(value, raw, claim_path, "FAILED", observed, custody_root=custody, receipt_target=receipt_path, finalized_at=observed["now"])
            _second, terminal_error = finalize_authorization(value, raw, claim_path, "UNKNOWN", observed, custody_root=custody, receipt_target=receipt_path, finalized_at=observed["now"])
            if final_error or receipt is None or terminal_error is None:
                problems.append("FAILED/UNKNOWN terminal receipt behavior failed")
        with tempfile.TemporaryDirectory(prefix="daee-vcs-append-adoption-") as directory:
            custody = Path(directory); claim_path = custody / "claims/commit.claim.json"
            auth_sha = sha256_bytes(raw)
            orphan = {
                "schema": "vcs-action-claim-v1", "kind": "vcs-action-claim",
                "claim_id": _claim_id(auth_sha, value["nonce"]),
                "authorization_sha256": auth_sha, "authorization_id": value["authorization_id"],
                "nonce": value["nonce"], "action": value["action"],
                "claim_locator": value["claim_locator"], "action_receipt_locator": value["action_receipt_locator"],
                "writer_boundary_identity": value["writer_boundary_identity"], "claimed_at": observed["now"],
                "predecessor_record_sha256": None, "status": "CLAIMED", "terminal_claim": False,
            }
            publish_json_idempotent(custody, claim_path, orphan)
            adopted, adoption_error = consume_authorization(value, raw, observed, custody_root=custody, claim_target=claim_path, claimed_at="2026-07-12T12:01:00Z")
            if adoption_error or adopted != orphan or read_cas_pointer(custody)["last_record_sha256"] != sha256_bytes(canonical_json_bytes(orphan)):
                problems.append("byte-identical append-before-head crash adoption failed")
        final_observed = {**observed, "result_commit_oid": "3" * 40, "result_tree_oid": value["staged_tree"], "result_parent_commits": [value["parent_commit"]]}
        if validate_action_result(value, final_observed):
            problems.append("exact one-parent/tree/message/scoped commit receipt validation failed")
        if not validate_action_result(value, {**final_observed, "result_parent_commits": [value["parent_commit"], "e" * 40]}):
            problems.append("multi-parent commit receipt was not rejected")
    orphan_expectations = [sidecar for sidecar in (FIXTURE_ROOT / "invalid").glob("*.expectation.json") if not sidecar.with_name(sidecar.name.replace(".expectation.json", ".json")).is_file()]
    if orphan_expectations:
        problems.append("orphan same-stem expectation exists")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print(f"VCS action authorization self-test: PASS ({len(valid)} valid, {len(invalid)} invalid; injected observations only; no live authority)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--manifest")
    parser.add_argument("--require-action", choices=sorted(ACTIONS))
    parser.add_argument("--consume-once", action="store_true")
    parser.add_argument("--claim-receipt")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--action-receipt")
    parser.add_argument("--result", choices=["PASS", "FAILED", "UNKNOWN"])
    parser.add_argument("--test-observations", help=argparse.SUPPRESS)
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args(argv)
    if args.consume_once and args.finalize:
        parser.error("--consume-once and --finalize are separate state transitions")
    if args.finalize and (not args.claim_receipt or not args.action_receipt or not args.result):
        parser.error("--finalize requires --claim-receipt --action-receipt --result")
    if args.self_test:
        if any((args.consume_once, args.finalize, args.manifest, args.claim_receipt, args.action_receipt, args.test_observations)):
            parser.error("--self-test cannot consume, finalize, or emit authority")
        return self_test()
    if not args.manifest or not args.require_action:
        parser.error("--manifest and --require-action are required")
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = ROOT / manifest
    finding: Finding | None = None
    value: dict[str, Any] | None = None
    raw = b""
    if args.consume_once or args.finalize:
        try:
            manifest = resolve_live_authorization_path(manifest)
        except (OSError, ValueError) as exc:
            finding = Finding(
                "authority_custody",
                "authorization-root",
                f"live authority must resolve beneath the protected A16 authorization root: {exc}",
            )
    else:
        try:
            manifest = manifest.resolve(strict=True)
        except OSError:
            pass
    if finding is None:
        value, raw, finding = _load(manifest)
    if finding is None and value is not None:
        if value.get("action") != args.require_action:
            finding = Finding("action_family", "required-action", "--require-action differs from immutable authorization")
        elif args.finalize:
            issues = validate_schema_subset(value, _schema())
            if issues:
                issue = issues[0]
                finding = Finding("schema_contract", f"schema-{issue.keyword.lower()}", f"{issue.path}: {issue.message}")
    if finding is None and value is not None and (args.consume_once or args.finalize):
        if not _authority_file_protected(manifest):
            finding = Finding("authority_custody", "writer-protection", "live authorization must be immutable at the owner-protected writer boundary")
    observed: dict[str, Any] = {}
    if finding is None and value is not None:
        if args.test_observations:
            if args.consume_once or args.finalize:
                parser.error("test observations are validation-only and cannot emit authority")
            try:
                manifest.relative_to((FIXTURE_ROOT).resolve())
            except ValueError:
                parser.error("test observations are accepted only for tracked test fixtures")
            support_path = Path(args.test_observations)
            if not support_path.is_absolute():
                support_path = ROOT / support_path
            support = strict_json_loads(support_path.read_bytes(), label=str(support_path))
            observed = dict(support["observed"])
        else:
            try:
                if args.finalize:
                    observed = collect_final_observation(value) if result_requires_live_observation(str(args.result)) else {}
                else:
                    observed = collect_live_observation(value)
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                finding = Finding("live_observation", "observation-failed", str(exc))
        if finding is None and not args.finalize:
            findings = validate_authorization(value, observed)
            finding = findings[0] if findings else None
        if finding is None and args.consume_once:
            if not args.claim_receipt or args.claim_receipt != value["claim_locator"]:
                finding = Finding("claim_locator", "claim-locator", "--claim-receipt must equal predetermined claim_locator")
            else:
                try:
                    claim_path = resolve_live_custody_path(args.claim_receipt, "claims", must_exist=False)
                except PathCustodyError as exc:
                    finding = Finding("claim_locator", exc.subcode, str(exc))
                else:
                    _claim, finding = consume_authorization(value, raw, observed, custody_root=CUSTODY_ROOT, claim_target=claim_path, claimed_at=observed["now"])
        if finding is None and args.finalize:
            if args.claim_receipt != value["claim_locator"]:
                finding = Finding("claim_locator", "claim-locator", "--claim-receipt must equal predetermined claim_locator")
            elif args.action_receipt != value["action_receipt_locator"]:
                finding = Finding("claim_locator", "receipt-locator", "--action-receipt must equal predetermined action_receipt_locator")
            else:
                try:
                    claim_path = resolve_live_custody_path(args.claim_receipt, "claims", must_exist=True)
                    receipt_path = resolve_live_custody_path(args.action_receipt, "receipts", must_exist=False)
                except PathCustodyError as exc:
                    finding = Finding("claim_locator", exc.subcode, str(exc))
                else:
                    _receipt, finding = finalize_authorization(value, raw, claim_path, args.result, observed, custody_root=CUSTODY_ROOT, receipt_target=receipt_path, finalized_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    if finding:
        payload = diagnostic(finding, str(manifest))
        print(json.dumps(payload, sort_keys=True) if args.explain else f"VCS action authorization: FAIL [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
        return 1
    print(json.dumps({"checker_id": CHECKER_ID, "status": "PASS"}, sort_keys=True) if args.explain else "VCS action authorization: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
