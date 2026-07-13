#!/usr/bin/env python3
"""Build or validate the combined exact source commit and GitHub CI receipt."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import yaml

from a16_immutable_custody import (
    CustodyError,
    append_claim_before_cas,
    canonical_json_bytes,
    iter_immutable_records,
    read_cas_pointer,
    resolve_contained_path,
    sha256_bytes,
)
from contract_validation import PathCustodyError, resolve_repo_path, validate_schema_subset
from run_local_ci import (
    PYTHON_EXECUTION_PROFILE_ID,
    command_list_sha256,
    execution_plan_sha256,
    execution_profile_for,
    parse_completion_stdout,
)
from run_no_model_preflight import (
    A16_GATE_COMMANDS,
    EXPECTED_GATE_COUNT,
    EXPECTED_GATE_RETURN_CODES,
    GATES as NO_MODEL_GATES,
)
from source_provenance import (
    BINDING_ID,
    BINDING_SCHEMA,
    CARRIER_PATHS,
    CHECKPOINT_COMMIT,
    CHECKPOINT_TREE,
    DuplicateObjectKey,
    _extract_source_binding_bytes,
    strict_json_loads,
    validate_tracked_only,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
RUN_REL = Path(".IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5")
RECEIPT_REL = RUN_REL / "receipts/source-commit"
RECEIPT_ROOT = ROOT / RECEIPT_REL
VCS_CUSTODY_ROOT = ROOT / RUN_REL / "evidence/vcs-action"
VCS_AUTH_ROOT = VCS_CUSTODY_ROOT / "authorizations"
SCHEMA_PATH = ROOT / "schema/ci-readback.schema.json"
VCS_SCHEMA_PATH = ROOT / "schema/vcs-action-authorization.schema.json"
EXPECTATION_SCHEMA_PATH = ROOT / "schema/negative-fixture-expectation.schema.json"
FIXTURE_ROOT = ROOT / "tests/ci-readback"
VALID_FIXTURE = FIXTURE_ROOT / "valid/required-checks-bound-to-pushed-sha.json"
CHECKER_ID = "ci-readback"
DOWNSTREAM = ["exact-sha-ci", "source-preflight", "candidate-package", "release-action"]
REPOSITORY = "theislampill/daee-epistemics"
REMOTE_URL = "https://github.com/theislampill/daee-epistemics.git"
BRANCH = "codex/v0.4.6.0-runtime-footprint-b10"
REMOTE_REF = f"refs/heads/{BRANCH}"
WORKFLOW_PATH = ".github/workflows/ci.yml"
WORKFLOW_NAME = "CI"
JOB_NAME = "runtime-checks"
CHECK_NAME = "CI / runtime-checks"
LINUX_STEP_NAME = "Linux A01 custody self-test"
LINUX_COMMAND = "python tools/check_captured_output_manifest.py --self-test"
LINUX_WRITER_STEP = "Emit Linux A01 evidence"
LINUX_ARTIFACT_NAME = "linux-a01-evidence"
LINUX_ARTIFACT_ENTRY = "linux-a01.json"
LINUX_CHECKER_PATH = "tools/check_captured_output_manifest.py"
LINUX_TEST_PATH = "tests/captured-output-custody/test_contract.py"
FULL_CI_COMMAND = "python -I -S -B tools/sanitized_python_bootstrap.py --script tools/run_local_ci.py --strict-pwsh --command-timeout-seconds 900"
LINUX_WRITER_BIND_COMMAND = (
    'test "$(git hash-object tools/write_linux_a01_evidence.py)" = '
    '"$(git rev-parse "${{ github.sha }}:tools/write_linux_a01_evidence.py")"'
)
FULL_CI_BIND_COMMAND = (
    'test "$(git hash-object tools/run_local_ci.py)" = '
    '"$(git rev-parse "${{ github.sha }}:tools/run_local_ci.py")" && '
    'test "$(git hash-object tools/sanitized_python_bootstrap.py)" = '
    '"$(git rev-parse "${{ github.sha }}:tools/sanitized_python_bootstrap.py")"'
)
LINUX_WRITER_COMMAND = (
    'python tools/write_linux_a01_evidence.py --out .ci-evidence/linux-a01.json '
    '--source-sha "${{ github.sha }}" --run-id "${{ github.run_id }}" '
    '--run-number "${{ github.run_number }}" --run-attempt "${{ github.run_attempt }}" '
    '--job-name runtime-checks --runner-label ubuntu-latest '
    '--runner-environment "${{ runner.environment }}"'
)
LINUX_UPLOAD_WITH = {
    "name": LINUX_ARTIFACT_NAME,
    "path": ".ci-evidence/linux-a01.json",
    "if-no-files-found": "error",
    "retention-days": 90,
}
EXPECTED_WORKFLOW_STEPS = [
    {"uses": "actions/checkout@v5", "with": {"fetch-depth": 0}},
    {"uses": "actions/setup-python@v6", "with": {"python-version": "3.11"}},
    {"name": "Install checker dependencies", "run": "python -m pip install --upgrade pip -r requirements-ci.txt"},
    {"name": "Verify tracked source binding and checkpoint", "run": "python tools/check_source_provenance.py --tracked-only"},
    {"name": LINUX_STEP_NAME, "run": LINUX_COMMAND},
    {"name": "Verify Linux A01 evidence writer source", "run": LINUX_WRITER_BIND_COMMAND},
    {"name": LINUX_WRITER_STEP, "run": LINUX_WRITER_COMMAND},
    {"name": "Upload Linux A01 evidence", "uses": "actions/upload-artifact@v4", "with": LINUX_UPLOAD_WITH},
    {"name": "Remove Linux A01 staging", "run": "rm -f .ci-evidence/linux-a01.json && rmdir .ci-evidence"},
    {"name": "Verify full CI executor source", "run": FULL_CI_BIND_COMMAND},
    {"name": "Build and verify runtime", "run": FULL_CI_COMMAND},
]
NON_CLAIMS = [
    "does-not-claim-deterministic-whole-branch-closure",
    "does-not-claim-candidate-maturity",
    "does-not-authorize-or-execute-model-provider-use",
    "does-not-record-owner-acceptance",
]
DETERMINISTIC_VERDICT_ROOT_REL = RUN_REL / "evidence/deterministic-verdicts"
DETERMINISTIC_VERDICT_SPECS = {
    "no_model_preflight": {
        "path": DETERMINISTIC_VERDICT_ROOT_REL / "no-model-preflight.json",
        "kind": "no-model-preflight",
        "status": "PASS",
    },
    "full_local_ci": {
        "path": DETERMINISTIC_VERDICT_ROOT_REL / "full-local-ci.json",
        "kind": "full-local-ci",
        "status": "PASS",
    },
    "generated_freshness_package": {
        "path": DETERMINISTIC_VERDICT_ROOT_REL / "generated-freshness-package.json",
        "kind": "generated-freshness-package",
        "status": "PASS",
    },
    "independent_whole_branch_review": {
        "path": DETERMINISTIC_VERDICT_ROOT_REL / "independent-whole-branch-review.json",
        "kind": "independent-whole-branch-review",
        "status": "ACCEPT",
    },
}
DETERMINISTIC_VERDICT_SCHEMA = "daee-task7-deterministic-evidence-v1"
TASK7_EVIDENCE_NON_CLAIMS = [
    "does-not-claim-final-source-commit",
    "does-not-claim-exact-sha-ci",
    "does-not-authorize-model-or-candidate",
]
TASK7_PRODUCER_PATH = "tools/write_task7_deterministic_evidence.py"
TASK7_SOURCE_FREEZE_REL = DETERMINISTIC_VERDICT_ROOT_REL / "source-freeze.json"
TASK7_REPORT_REL_BY_KIND = {
    spec["kind"]: DETERMINISTIC_VERDICT_ROOT_REL / "reports" / f"{spec['kind']}.json"
    for spec in DETERMINISTIC_VERDICT_SPECS.values()
}
TASK7_LOG_REL_BY_KIND = {
    spec["kind"]: DETERMINISTIC_VERDICT_ROOT_REL / "logs" / f"{spec['kind']}.json"
    for spec in DETERMINISTIC_VERDICT_SPECS.values()
}
TASK7_NO_MODEL_NATIVE_REPORT_REL = DETERMINISTIC_VERDICT_ROOT_REL / "native/no-model-preflight.json"
TASK7_FULL_LOCAL_CI_NATIVE_REPORT_REL = DETERMINISTIC_VERDICT_ROOT_REL / "native/full-local-ci.json"
TASK7_WHOLE_BRANCH_REVIEW_REL = RUN_REL / "reviews/task7-independent-whole-branch-review.json"
TASK7_REVIEW_AUTHORIZATION_REL = DETERMINISTIC_VERDICT_ROOT_REL / "authorizations/independent-reviewer.json"
TASK7_IMPLEMENTATION_OWNER_IDENTITY = "/root/task3b_ci_receipt"
TASK7_REVIEW_AUTHORIZATION_ISSUER = "/root"
TASK7_ROLE_CHECKS = {
    "generated-freshness-package": [
        ["python", "tools/build_framework_pipeline.py"],
        ["python", "tools/build_compiled_runtime.py"],
        ["python", "tools/check_compiled_runtime_freshness.py"],
        ["git", "diff", "--exit-code", "--", "skill/SKILL.md"],
        ["python", "tools/build_docs_index.py", "--check"],
        ["python", "tools/check_package_shape.py"],
        ["python", "tools/build_package_shape_inventory.py", "--check"],
    ],
    "no-model-preflight": [
        ["python", "tools/run_no_model_preflight.py", "--json", TASK7_NO_MODEL_NATIVE_REPORT_REL.as_posix()]
    ],
    "full-local-ci": [[
        "python",
        "tools/run_local_ci.py",
        "--strict-pwsh",
        "--command-timeout-seconds",
        "900",
        "--json",
        TASK7_FULL_LOCAL_CI_NATIVE_REPORT_REL.as_posix(),
    ]],
    "independent-whole-branch-review": [],
}
TASK7_TASK_IDENTITY_RE = re.compile(r"^/root(?:/[a-z0-9][a-z0-9_-]{0,63})*$")


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


def _schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = strict_json_loads(path.read_bytes(), label=str(path))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: schema root must be an object")
    return value


def _load_raw(path: Path) -> tuple[dict[str, Any] | None, bytes, Finding | None]:
    try:
        raw = path.read_bytes()
        value = strict_json_loads(raw, label=str(path))
    except DuplicateObjectKey as exc:
        return None, b"", Finding("malformed_json", "duplicate-key", f"duplicate JSON key rejected: {exc}")
    except (OSError, ValueError) as exc:
        return None, b"", Finding("malformed_json", "malformed-json", str(exc))
    if not isinstance(value, dict):
        return None, raw, Finding("receipt_contract", "root-shape", "receipt root must be an object")
    return value, raw, None


def _receipt_id(commit_sha: str, run_id: int, run_attempt: int) -> str:
    return hashlib.sha256(
        b"daee-source-commit-receipt-v1\0"
        + commit_sha.encode("ascii")
        + b"\0"
        + str(run_id).encode("ascii")
        + b"\0"
        + str(run_attempt).encode("ascii")
    ).hexdigest()


def _source_state_digest(source: Mapping[str, Any]) -> str:
    body = {key: copy.deepcopy(value) for key, value in source.items() if key != "state_digest_sha256"}
    return sha256_bytes(canonical_json_bytes(body))


def _carrier_binding_digest(source_binding: Mapping[str, Any], carriers: Sequence[Mapping[str, Any]]) -> str:
    return sha256_bytes(
        canonical_json_bytes({"source_binding": copy.deepcopy(source_binding), "carriers": copy.deepcopy(list(carriers))})
    )


def _resolve_parent(value: Any, dotted: str) -> tuple[Any, str]:
    tokens = dotted.split(".")
    parent = value
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    return parent, tokens[-1]


def _set_dotted(value: Any, dotted: str, replacement: Any) -> None:
    parent, token = _resolve_parent(value, dotted)
    if isinstance(parent, list):
        parent[int(token)] = copy.deepcopy(replacement)
    else:
        parent[token] = copy.deepcopy(replacement)


def _delete_dotted(value: Any, dotted: str) -> None:
    parent, token = _resolve_parent(value, dotted)
    if isinstance(parent, list):
        del parent[int(token)]
    else:
        del parent[token]


def _append_dotted(value: Any, dotted: str, addition: Any) -> None:
    parent, token = _resolve_parent(value, dotted)
    target = parent[int(token)] if isinstance(parent, list) else parent[token]
    target.append(copy.deepcopy(addition))


def _artifact(ref: Mapping[str, Any], *, root: Path = ROOT) -> tuple[dict[str, Any] | None, Finding | None]:
    path_value = ref.get("path") if isinstance(ref, Mapping) else None
    digest = ref.get("sha256") if isinstance(ref, Mapping) else None
    try:
        path = resolve_repo_path(root, str(path_value), must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        return None, Finding("vcs_evidence", exc.subcode, f"VCS evidence path rejected: {path_value}: {exc}")
    try:
        raw = path.read_bytes()
        value = strict_json_loads(raw, label=str(path))
    except DuplicateObjectKey as exc:
        return None, Finding("vcs_evidence", "duplicate-key", f"VCS evidence duplicate key: {exc}")
    except (OSError, ValueError) as exc:
        return None, Finding("vcs_evidence", "artifact-read", f"VCS evidence read failed: {exc}")
    if sha256_bytes(raw) != digest:
        return None, Finding("vcs_evidence", "artifact-hash", f"VCS evidence {path_value} raw SHA-256 differs")
    if not isinstance(value, dict):
        return None, Finding("vcs_evidence", "artifact-shape", f"VCS evidence {path_value} is not an object")
    return value, None


def _authorization_scope(
    authorization: Mapping[str, Any],
    repository: Mapping[str, Any],
    *,
    public_family: bool,
    label: str | None = None,
) -> Finding | None:
    if public_family:
        expected = {
            "repository": repository.get("full_name"),
            "remote_name": repository.get("remote_name"),
            "target_branch": repository.get("branch"),
            "target_ref": repository.get("ref"),
        }
        actual = {field: authorization.get(field) for field in expected}
    elif label == "commit":
        expected = {
            "repository": str(ROOT.resolve()),
            "branch": repository.get("branch"),
        }
        raw_repository = authorization.get("repository")
        try:
            actual_repository = str(Path(str(raw_repository)).resolve())
        except (OSError, ValueError):
            actual_repository = str(raw_repository)
        actual = {
            "repository": actual_repository,
            "branch": authorization.get("branch"),
        }
    else:
        expected = {
            "repository": repository.get("full_name"),
            "remote_name": repository.get("remote_name"),
            "branch": repository.get("branch"),
            "remote_ref": repository.get("ref"),
        }
        actual = {field: authorization.get(field) for field in expected}
    if actual != expected:
        return Finding(
            "vcs_evidence",
            "authorization-scope",
            f"VCS authorization repository/remote/branch/ref scope drifted: {actual} != {expected}",
        )
    return None


def _validate_public_action_chain(
    label: str,
    chain: Mapping[str, Any],
    source: Mapping[str, Any],
    repository: Mapping[str, Any],
    workflow: Mapping[str, Any],
    owner_required: Sequence[str],
) -> tuple[dict[str, Any] | None, Finding | None]:
    loaded: dict[str, dict[str, Any]] = {}
    for kind in ("authorization", "claim", "action_receipt"):
        value, finding = _artifact(chain.get(kind, {}))
        if finding:
            return None, finding
        assert value is not None
        loaded[kind] = value
    authorization = loaded["authorization"]
    claim = loaded["claim"]
    receipt = loaded["action_receipt"]
    public_family = authorization.get("schema") == "vcs-action-authorization-v1"
    legacy_family = authorization.get("schema") == "daee-vcs-durability-authorization-v1"
    if not (public_family or legacy_family):
        return None, Finding("vcs_evidence", "authorization-schema", f"{label} authorization schema is unsupported")

    scope_finding = _authorization_scope(
        authorization,
        repository,
        public_family=public_family,
        label=label,
    )
    if scope_finding:
        return None, scope_finding

    if public_family:
        vcs_schema = _schema(VCS_SCHEMA_PATH)
        for kind, value in loaded.items():
            issues = validate_schema_subset(value, vcs_schema)
            if issues:
                first = issues[0]
                return None, Finding("vcs_evidence", f"{kind}-schema", f"{label} {kind} schema failed at {first.path}: {first.message}")
        expected_kind = f"{label}-authorization"
        expected_action = f"{label}-countermeasure"
        if authorization.get("kind") != expected_kind or authorization.get("action") != expected_action:
            return None, Finding("vcs_evidence", "wrong-authorization", f"{label} authorization is for a different action")
        if claim.get("schema") != "vcs-action-claim-v1" or receipt.get("schema") != "vcs-action-receipt-v1":
            return None, Finding("vcs_evidence", "wrong-action-receipt", f"{label} action receipt family is wrong")
        if receipt.get("action") != expected_action:
            return None, Finding("vcs_evidence", "wrong-action-receipt", f"{label} action receipt is for {receipt.get('action')}, not {expected_action}")
        authorization_digest = chain["authorization"]["sha256"]
        claim_digest = chain["claim"]["sha256"]
        if any(
            value != chain.get(field)
            for field, value in (("authorization_id", authorization.get("authorization_id")), ("nonce", authorization.get("nonce")))
        ):
            return None, Finding("vcs_evidence", "authorization-identity", f"{label} authorization ID/nonce differs from receipt refs")
        if claim.get("authorization_sha256") != authorization_digest or receipt.get("authorization_sha256") != authorization_digest:
            return None, Finding("vcs_evidence", "authorization-hash", f"{label} claim/action receipt does not consume the authorization hash")
        if receipt.get("claim_sha256") != claim_digest:
            return None, Finding("vcs_evidence", "claim-hash", f"{label} action receipt does not consume the claim hash")
        for field in ("authorization_id", "nonce", "action"):
            expected = authorization.get(field)
            if claim.get(field) != expected or receipt.get(field) != expected:
                return None, Finding("vcs_evidence", "action-binding", f"{label} {field} differs across authorization/claim/action receipt")
        if receipt.get("result") != "PASS" or receipt.get("terminal") is not True or receipt.get("terminal_claim") is not False:
            return None, Finding("vcs_evidence", "action-result", f"{label} action receipt must be terminal PASS with terminal_claim=false")
        commit_sha = source["commit_sha"]
        tree_oid = source["tree_oid"]
        if receipt.get("observed_commit_oid") != commit_sha or receipt.get("observed_tree_oid") != tree_oid:
            return None, Finding("vcs_evidence", "action-source", f"{label} action receipt commit/tree differs from exact source")
        if label == "commit":
            if authorization.get("staged_tree") != tree_oid or authorization.get("parent_commit") not in source["parent_oids"]:
                return None, Finding("vcs_evidence", "commit-source", "commit authorization tree/raw parents differ from exact source")
        else:
            if authorization.get("local_commit") != commit_sha or authorization.get("local_tree") != tree_oid:
                return None, Finding("vcs_evidence", "push-source", "push authorization commit/tree differs from exact source")
            if receipt.get("observed_remote_oid") != commit_sha:
                return None, Finding("vcs_evidence", "push-remote", "push action receipt remote OID differs from exact source")
            snapshot = authorization.get("workflow_check_snapshot", {})
            if (
                snapshot.get("workflow_path") != workflow.get("path")
                or snapshot.get("workflow_name") != workflow.get("name")
                or snapshot.get("job_name") != JOB_NAME
                or snapshot.get("workflow_blob_oid") != workflow.get("blob_oid")
                or snapshot.get("workflow_sha256") != workflow.get("raw_sha256")
                or snapshot.get("required_checks") != list(owner_required)
            ):
                return None, Finding("vcs_evidence", "workflow-snapshot", "push authorization workflow/check snapshot drifted")
        return loaded, None

    expected_action = label
    if authorization.get("action") != expected_action or receipt.get("action") != expected_action:
        return None, Finding("vcs_evidence", "wrong-action-receipt", f"legacy {label} action receipt is for a different action")
    if receipt.get("result") != "PASS" or receipt.get("terminal_claim") is not False:
        return None, Finding("vcs_evidence", "action-result", f"legacy {label} action receipt must be PASS and nonterminal")
    if (
        chain.get("authorization_id") != authorization.get("authorization_id")
        or receipt.get("authorization_id") != authorization.get("authorization_id")
        or claim.get("authorization_id") != authorization.get("authorization_id")
    ):
        return None, Finding("vcs_evidence", "authorization-identity", f"legacy {label} authorization ID differs")
    if receipt.get("claim_path") != chain["claim"]["path"]:
        return None, Finding("vcs_evidence", "claim-path", f"legacy {label} receipt does not bind the exact claim path")
    if label == "commit":
        if receipt.get("commit_sha") != source["commit_sha"] or receipt.get("commit_tree") != source["tree_oid"]:
            return None, Finding("vcs_evidence", "commit-source", "legacy commit receipt source differs")
    else:
        if receipt.get("local_oid") != source["commit_sha"] or receipt.get("live_remote_oid") != source["commit_sha"]:
            return None, Finding("vcs_evidence", "push-source", "legacy push receipt exact OID equality differs")
        snapshot = authorization.get("workflow_check_snapshot", {})
        if (
            snapshot.get("workflow_path") != workflow.get("path")
            or snapshot.get("workflow_name") != workflow.get("name")
            or snapshot.get("job_name") != JOB_NAME
            or snapshot.get("workflow_blob_oid") != workflow.get("blob_oid")
            or snapshot.get("workflow_sha256") != workflow.get("raw_sha256")
            or snapshot.get("required_checks") != list(owner_required)
        ):
            return None, Finding("vcs_evidence", "workflow-snapshot", "legacy push authorization workflow/check snapshot drifted")
    return loaded, None


def _validate_vcs(value: Mapping[str, Any]) -> Finding | None:
    vcs = value["vcs"]
    commit_chain = vcs["commit"]
    push_chain = vcs["push"]
    if (
        commit_chain["authorization"]["path"] == push_chain["authorization"]["path"]
        or commit_chain["claim"]["path"] == push_chain["claim"]["path"]
    ):
        return Finding("vcs_evidence", "replayed-action-receipt", "commit and push replay the same authorization, claim, or action receipt")
    commit_loaded, finding = _validate_public_action_chain(
        "commit",
        commit_chain,
        value["source"],
        value["repository"],
        value["workflow"],
        value["required_checks"]["owner_required_set"],
    )
    if finding:
        return finding
    push_loaded, finding = _validate_public_action_chain(
        "push",
        push_chain,
        value["source"],
        value["repository"],
        value["workflow"],
        value["required_checks"]["owner_required_set"],
    )
    if finding:
        return finding
    assert commit_loaded is not None and push_loaded is not None
    push_authorization = push_loaded["authorization"]
    if push_authorization.get("schema") == "vcs-action-authorization-v1":
        commit_ref = push_authorization.get("commit_receipt", {})
        if commit_ref != commit_chain["action_receipt"]:
            return Finding("vcs_evidence", "wrong-action-receipt", "push authorization does not bind the exact commit action receipt")
        expected_old = push_authorization.get("expected_old_remote_oid")
    else:
        if (
            push_authorization.get("commit_receipt_path") != commit_chain["action_receipt"]["path"]
            or push_authorization.get("commit_receipt_sha256") != commit_chain["action_receipt"]["sha256"]
        ):
            return Finding("vcs_evidence", "wrong-action-receipt", "legacy push authorization does not bind the exact commit action receipt")
        expected_old = push_authorization.get("expected_old_remote_oid")
    if expected_old != vcs.get("expected_old_remote_oid") or expected_old != value["source"]["equality"]["expected_old_remote_oid"]:
        return Finding("vcs_evidence", "expected-old-remote", "VCS expected old remote OID differs from push authorization")
    return None


def _task7_schema_finding(value: Mapping[str, Any], definition: str, role: str) -> Finding | None:
    schema = _schema()
    issues = validate_schema_subset(value, {"$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"})
    if issues:
        first = issues[0]
        return Finding(
            "deterministic_verdicts",
            "evidence-schema",
            f"deterministic verdict {role} {definition} failed at {first.path}: {first.message}",
        )
    return None


def _task7_files_digest(files: Sequence[Mapping[str, Any]]) -> str:
    return sha256_bytes(canonical_json_bytes(list(files)))


def _task7_freeze_id(tree_oid: str, files_sha256: str) -> str:
    return sha256_bytes(
        b"daee-task7-precommit-source-freeze-v1\0"
        + tree_oid.encode("ascii")
        + b"\0"
        + files_sha256.encode("ascii")
    )


def _task7_command_digest(command: Sequence[str]) -> str:
    return sha256_bytes(canonical_json_bytes(list(command)))


def _task7_producer_command(kind: str) -> list[str]:
    role = next(
        (role for role, spec in DETERMINISTIC_VERDICT_SPECS.items() if spec["kind"] == kind),
        None,
    )
    if role is None:
        raise ValueError(f"unsupported Task 7 verdict kind {kind!r}")
    return [
        "python",
        TASK7_PRODUCER_PATH,
        "--build-verdict",
        "--kind",
        kind,
        "--source-freeze",
        TASK7_SOURCE_FREEZE_REL.as_posix(),
        "--out",
        DETERMINISTIC_VERDICT_SPECS[role]["path"].as_posix(),
    ]


def _task7_report_id(value: Mapping[str, Any]) -> str:
    body = {key: value[key] for key in value if key != "report_id"}
    return sha256_bytes(b"daee-task7-result-report-v2\0" + canonical_json_bytes(body))


def _task7_review_manifest(freeze: Mapping[str, Any]) -> dict[str, Any]:
    lines = b"".join(
        row["path"].encode("utf-8")
        + b"\0"
        + str(row["byte_count"]).encode("ascii")
        + b"\0"
        + row["raw_sha256"].encode("ascii")
        + b"\n"
        for row in freeze["files"]
    )
    return {
        "algorithm": "path-nul-byte-count-nul-sha256-lf-v1",
        "path_count": len(freeze["files"]),
        "byte_count": sum(row["byte_count"] for row in freeze["files"]),
        "aggregate_sha256": sha256_bytes(lines),
    }


def _task7_review_id(value: Mapping[str, Any]) -> str:
    body = {key: value[key] for key in value if key != "review_id"}
    return sha256_bytes(b"daee-task7-whole-branch-review-v1\0" + canonical_json_bytes(body))


def _task7_review_authorization_id(value: Mapping[str, Any]) -> str:
    body = {key: value[key] for key in value if key != "authorization_id"}
    return sha256_bytes(
        b"daee-task7-independent-review-authorization-v1\0" + canonical_json_bytes(body)
    )


def _task7_evidence_id(bundle: Mapping[str, Any]) -> str:
    return sha256_bytes(
        b"daee-task7-deterministic-evidence-v1\0"
        + bundle["kind"].encode("utf-8")
        + b"\0"
        + bundle["freeze_id"].encode("ascii")
        + b"\0"
        + bundle["command_sha256"].encode("ascii")
        + b"\0"
        + bundle["report"]["sha256"].encode("ascii")
        + b"\0"
        + bundle["log"]["sha256"].encode("ascii")
    )


def _task7_ref_artifact(
    ref: Mapping[str, Any], *, root: Path, role: str, label: str, json_value: bool
) -> tuple[Path | None, bytes, dict[str, Any] | None, Finding | None]:
    try:
        path = resolve_repo_path(root, str(ref.get("path", "")), must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        return None, b"", None, Finding(
            "deterministic_verdicts", exc.subcode, f"deterministic verdict {role} {label} path rejected: {exc}"
        )
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, b"", None, Finding(
            "deterministic_verdicts", "artifact-read", f"deterministic verdict {role} {label} read failed: {exc}"
        )
    if len(raw) != ref.get("byte_count") or sha256_bytes(raw) != ref.get("sha256"):
        return None, raw, None, Finding(
            "deterministic_verdicts",
            "artifact-hash",
            f"deterministic verdict {role} {label} byte_count/sha256 differs",
        )
    if not json_value:
        return path, raw, None, None
    try:
        parsed = strict_json_loads(raw, label=str(path))
    except DuplicateObjectKey as exc:
        return None, raw, None, Finding(
            "deterministic_verdicts", "duplicate-key", f"deterministic verdict {role} {label} duplicate key: {exc}"
        )
    except ValueError as exc:
        return None, raw, None, Finding(
            "deterministic_verdicts", "artifact-read", f"deterministic verdict {role} {label} JSON failed: {exc}"
        )
    if not isinstance(parsed, dict):
        return None, raw, None, Finding(
            "deterministic_verdicts", "artifact-shape", f"deterministic verdict {role} {label} is not an object"
        )
    return path, raw, parsed, None


def _task7_result_semantics(
    role: str,
    spec: Mapping[str, Any],
    bundle: Mapping[str, Any],
    report: Mapping[str, Any],
    command_log: Mapping[str, Any],
    freeze: Mapping[str, Any],
    *,
    root: Path,
) -> Finding | None:
    kind = str(spec["kind"])
    expected_producer_command = _task7_producer_command(kind)
    if bundle.get("checker", {}).get("path") != TASK7_PRODUCER_PATH or bundle.get("command") != expected_producer_command:
        return Finding(
            "deterministic_verdicts",
            "role-command",
            f"deterministic verdict {role} does not use its exact source-bound role producer",
        )
    expected_producer_profile = execution_profile_for(expected_producer_command)
    if bundle.get("execution_profile") != expected_producer_profile:
        return Finding("deterministic_verdicts", "execution-profile", f"deterministic verdict {role} producer profile drifted")
    if report.get("producer_command") != expected_producer_command:
        return Finding("deterministic_verdicts", "role-command", f"deterministic verdict {role} report producer command drifted")
    if report.get("producer_command_sha256") != _task7_command_digest(expected_producer_command):
        return Finding("deterministic_verdicts", "command-hash", f"deterministic verdict {role} report producer hash drifted")
    if report.get("producer_execution_profile") != expected_producer_profile:
        return Finding("deterministic_verdicts", "execution-profile", f"deterministic verdict {role} report producer profile drifted")
    if report.get("producer") != bundle.get("checker"):
        return Finding("deterministic_verdicts", "producer-identity", f"deterministic verdict {role} report producer identity drifted")
    if (
        report.get("kind") != kind
        or report.get("status") != spec["status"]
        or report.get("source_freeze_id") != freeze["freeze_id"]
        or report.get("expected_final_tree_oid") != freeze["expected_final_tree_oid"]
        or report.get("observed_at") != bundle.get("observed_at")
    ):
        return Finding("deterministic_verdicts", "report-status", f"deterministic verdict {role} contentful report identity drifted")
    if report.get("report_id") != _task7_report_id(report):
        return Finding("deterministic_verdicts", "report-id", f"deterministic verdict {role} report_id drifted")
    entries = command_log.get("entries")
    if command_log.get("kind") != kind or not isinstance(entries, list):
        return Finding("deterministic_verdicts", "command-log", f"deterministic verdict {role} command log identity drifted")
    expected_checks = TASK7_ROLE_CHECKS[kind]
    if [entry.get("command") for entry in entries if isinstance(entry, Mapping)] != expected_checks:
        return Finding("deterministic_verdicts", "role-command", f"deterministic verdict {role} executed check set drifted")
    observed_results: list[dict[str, Any]] = []
    decoded_stdout: list[bytes] = []
    for sequence, entry in enumerate(entries, 1):
        if not isinstance(entry, Mapping) or entry.get("sequence") != sequence or entry.get("exit_code") != 0:
            return Finding("deterministic_verdicts", "command-log", f"deterministic verdict {role} command log sequence/exit drifted")
        try:
            stdout = base64.b64decode(str(entry.get("stdout_base64", "")), validate=True)
            stderr = base64.b64decode(str(entry.get("stderr_base64", "")), validate=True)
        except (ValueError, TypeError) as exc:
            return Finding("deterministic_verdicts", "command-log", f"deterministic verdict {role} command log base64 failed: {exc}")
        command = entry["command"]
        expected_profile = execution_profile_for(command)
        if entry.get("execution_profile") != expected_profile:
            return Finding("deterministic_verdicts", "execution-profile", f"deterministic verdict {role} check profile drifted")
        decoded_stdout.append(stdout)
        observed_result = {
                "sequence": sequence,
                "command": command,
                "command_sha256": _task7_command_digest(command),
                "execution_profile": expected_profile,
                "exit_code": 0,
                "stdout_byte_count": len(stdout),
                "stdout_sha256": sha256_bytes(stdout),
                "stderr_byte_count": len(stderr),
                "stderr_sha256": sha256_bytes(stderr),
            }
        if kind == "full-local-ci":
            try:
                completion = parse_completion_stdout(stdout)
            except ValueError as exc:
                return Finding("deterministic_verdicts", "full-ci-result", f"full local CI completion rejected: {exc}")
            if (
                completion.get("executed_count") != completion.get("command_count")
                or completion.get("start_at_command") != 1
                or completion.get("end_at_command") != completion.get("command_count")
                or completion.get("strict_pwsh") is not True
                or completion.get("command_timeout_seconds") != 900
            ):
                return Finding("deterministic_verdicts", "full-ci-result", "full local CI completion boundary drifted")
            observed_result["completion"] = completion
        observed_results.append(observed_result)
    if report.get("executed_checks") != observed_results or report.get("check_count") != len(observed_results):
        return Finding("deterministic_verdicts", "command-log", f"deterministic verdict {role} report/log execution binding drifted")
    artifacts = report.get("evidence_artifacts")
    if not isinstance(artifacts, list):
        return Finding("deterministic_verdicts", "report-evidence", f"deterministic verdict {role} evidence_artifacts are missing")
    if kind == "no-model-preflight":
        if len(artifacts) != 1 or not decoded_stdout or b"MATRIX_AUTHORIZED_AFTER_PREFLIGHT" not in decoded_stdout[0]:
            return Finding("deterministic_verdicts", "preflight-result", "no-model preflight lacks its authorized command/report evidence")
        _path, _raw, native, finding = _task7_ref_artifact(
            artifacts[0], root=root, role=role, label="native no-model report", json_value=True
        )
        if finding:
            return finding
        assert native is not None
        gates = native.get("gates")
        if (
            native.get("schema") != "daee-no-model-preflight-report-v2"
            or native.get("decision") != "MATRIX_AUTHORIZED_AFTER_PREFLIGHT"
            or native.get("complete") is not True
            or not isinstance(gates, list)
            or len(gates) != EXPECTED_GATE_COUNT
            or native.get("gate_count") != EXPECTED_GATE_COUNT
            or native.get("python_execution_profile_id") != PYTHON_EXECUTION_PROFILE_ID
        ):
            return Finding("deterministic_verdicts", "preflight-result", "no-model preflight native report is incomplete")
        native_commands: list[str] = []
        for expected_gate, gate in zip(NO_MODEL_GATES, gates):
            expected = expected_gate.number
            expected_returncode = EXPECTED_GATE_RETURN_CODES.get(expected, 0)
            steps = gate.get("steps") if isinstance(gate, Mapping) else None
            if (
                not isinstance(gate, Mapping)
                or gate.get("number") != expected
                or gate.get("name") != expected_gate.name
                or gate.get("passed") is not True
                or not isinstance(steps, list)
                or not steps
                or any(
                    not isinstance(step, Mapping)
                    or step.get("returncode") != expected_returncode
                    or step.get("timed_out") is not False
                    or step.get("execution_profile") != execution_profile_for(str(step.get("command", "")))
                    for step in steps
                )
            ):
                return Finding("deterministic_verdicts", "preflight-result", f"no-model preflight gate {expected} is not proven PASS")
            expected_commands = A16_GATE_COMMANDS.get(expected_gate.name)
            if expected_commands is not None and [step.get("command") for step in steps] != list(expected_commands):
                return Finding("deterministic_verdicts", "preflight-result", f"no-model preflight gate {expected} command drift")
            native_commands.extend(str(step["command"]) for step in steps)
        if (
            native.get("command_count") != len(native_commands)
            or native.get("command_set_sha256") != command_list_sha256(native_commands)
            or native.get("execution_plan_sha256") != execution_plan_sha256(native_commands)
        ):
            return Finding("deterministic_verdicts", "preflight-result", "no-model preflight command/profile digest drifted")
    elif kind == "full-local-ci":
        if len(artifacts) != 1 or len(decoded_stdout) != 1 or len(observed_results) != 1 or "completion" not in observed_results[0]:
            return Finding("deterministic_verdicts", "full-ci-result", "full local CI lacks its exact structured completion")
        _path, _raw, native_completion, finding = _task7_ref_artifact(
            artifacts[0], root=root, role=role, label="native full-local-CI report", json_value=True
        )
        if finding:
            return finding
        assert native_completion is not None
        schema_finding = _task7_schema_finding(native_completion, "run_local_ci_completion", role)
        if schema_finding:
            return schema_finding
        if native_completion != observed_results[0]["completion"]:
            return Finding("deterministic_verdicts", "full-ci-result", "native full-local-CI report differs from stdout completion")
    elif kind == "generated-freshness-package":
        if artifacts or len(observed_results) != len(expected_checks):
            return Finding("deterministic_verdicts", "freshness-result", "generated/package freshness command cohort is incomplete")
    else:
        if observed_results or len(artifacts) != 2:
            return Finding("deterministic_verdicts", "review-result", "independent review evidence cohort is incomplete")
        _auth_path, _auth_raw, authorization, finding = _task7_ref_artifact(
            artifacts[0], root=root, role=role, label="independent reviewer authorization", json_value=True
        )
        if finding:
            return finding
        assert authorization is not None
        schema_finding = _task7_schema_finding(authorization, "task7_review_authorization", role)
        if schema_finding:
            return schema_finding
        _path, _raw, review, finding = _task7_ref_artifact(
            artifacts[1], root=root, role=role, label="independent whole-branch review", json_value=True
        )
        if finding:
            return finding
        assert review is not None
        schema_finding = _task7_schema_finding(review, "task7_whole_branch_review", role)
        if schema_finding:
            return schema_finding
        reviewer = review.get("reviewer")
        owner_identity = review.get("owner_identity")
        authorized_reviewer = authorization.get("reviewer_identity")
        if (
            not isinstance(reviewer, str)
            or TASK7_TASK_IDENTITY_RE.fullmatch(reviewer) is None
            or not isinstance(owner_identity, str)
            or TASK7_TASK_IDENTITY_RE.fullmatch(owner_identity) is None
            or owner_identity != TASK7_IMPLEMENTATION_OWNER_IDENTITY
            or reviewer == owner_identity
            or authorization.get("issuer_identity") != TASK7_REVIEW_AUTHORIZATION_ISSUER
            or authorization.get("implementation_owner_identity") != TASK7_IMPLEMENTATION_OWNER_IDENTITY
            or not isinstance(authorized_reviewer, str)
            or TASK7_TASK_IDENTITY_RE.fullmatch(authorized_reviewer) is None
            or authorized_reviewer in {TASK7_IMPLEMENTATION_OWNER_IDENTITY, TASK7_REVIEW_AUTHORIZATION_ISSUER}
            or reviewer != authorized_reviewer
            or authorization.get("expected_final_tree_oid") != freeze["expected_final_tree_oid"]
            or authorization.get("source_freeze_id") != freeze["freeze_id"]
            or authorization.get("authorization_id") != _task7_review_authorization_id(authorization)
            or review.get("review_authorization_id") != authorization.get("authorization_id")
            or review.get("review_authorization") != artifacts[0]
            or review.get("reviewed_tree_oid") != freeze["expected_final_tree_oid"]
            or review.get("source_freeze_id") != freeze["freeze_id"]
            or review.get("manifest") != _task7_review_manifest(freeze)
            or review.get("review_id") != _task7_review_id(review)
        ):
            return Finding("deterministic_verdicts", "review-result", "independent review identity/findings/freeze binding drifted")
        try:
            authorization_time = datetime.strptime(str(authorization["issued_at"]), "%Y-%m-%dT%H:%M:%SZ")
            review_time = datetime.strptime(str(review["reviewed_at"]), "%Y-%m-%dT%H:%M:%SZ")
            evidence_time = datetime.strptime(str(report["observed_at"]), "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return Finding("deterministic_verdicts", "review-result", "independent review timestamp is invalid")
        if authorization_time > review_time or review_time > evidence_time:
            return Finding("deterministic_verdicts", "review-result", "review authorization/review/evidence time order drifted")
    return None


def _validate_task7_bundle(
    role: str,
    spec: Mapping[str, Any],
    bundle: Mapping[str, Any],
    *,
    root: Path,
    source_tree_oid: str,
) -> Finding | None:
    schema_finding = _task7_schema_finding(bundle, "task7_deterministic_evidence", role)
    if schema_finding:
        return schema_finding
    if bundle.get("kind") != spec["kind"] or bundle.get("status") != spec["status"]:
        return Finding(
            "deterministic_verdicts", "artifact-identity", f"deterministic verdict {role} kind/status drifted"
        )
    if bundle.get("expected_final_tree_oid") != source_tree_oid:
        return Finding(
            "deterministic_verdicts",
            "wrong-source",
            f"deterministic verdict {role} expected final tree differs from receipt source tree",
        )
    if (
        bundle.get("checker", {}).get("path") != TASK7_PRODUCER_PATH
        or bundle.get("command") != _task7_producer_command(str(spec["kind"]))
    ):
        return Finding(
            "deterministic_verdicts",
            "role-command",
            f"deterministic verdict {role} does not use its exact source-bound role producer",
        )
    if bundle.get("command_sha256") != _task7_command_digest(bundle["command"]):
        return Finding("deterministic_verdicts", "command-hash", f"deterministic verdict {role} command hash drifted")
    if bundle.get("evidence_id") != _task7_evidence_id(bundle):
        return Finding("deterministic_verdicts", "evidence-id", f"deterministic verdict {role} evidence_id drifted")
    inner_paths = [bundle[name]["path"] for name in ("report", "log", "source_freeze")]
    if len(inner_paths) != len(set(inner_paths)):
        return Finding("deterministic_verdicts", "replayed-evidence", f"deterministic verdict {role} replays an inner artifact")
    _report_path, _report_raw, report, finding = _task7_ref_artifact(
        bundle["report"], root=root, role=role, label="report", json_value=True
    )
    if finding:
        return finding
    assert report is not None
    schema_finding = _task7_schema_finding(report, "task7_result_report", role)
    if schema_finding:
        return schema_finding
    if report.get("kind") != spec["kind"] or report.get("status") != spec["status"]:
        return Finding("deterministic_verdicts", "report-status", f"deterministic verdict {role} report kind/status drifted")
    _log_path, log_raw, command_log, finding = _task7_ref_artifact(
        bundle["log"], root=root, role=role, label="log", json_value=True
    )
    if finding:
        return finding
    if not log_raw:
        return Finding("deterministic_verdicts", "empty-log", f"deterministic verdict {role} log is empty")
    assert command_log is not None
    schema_finding = _task7_schema_finding(command_log, "task7_command_log", role)
    if schema_finding:
        return schema_finding
    _freeze_path, _freeze_raw, freeze, finding = _task7_ref_artifact(
        bundle["source_freeze"], root=root, role=role, label="source freeze", json_value=True
    )
    if finding:
        return finding
    assert freeze is not None
    schema_finding = _task7_schema_finding(freeze, "task7_source_freeze", role)
    if schema_finding:
        return schema_finding
    files = freeze["files"]
    paths = [row["path"] for row in files]
    if paths != sorted(paths) or len(paths) != len(set(paths)) or freeze["file_count"] != len(files):
        return Finding("deterministic_verdicts", "freeze-manifest", f"deterministic verdict {role} source freeze paths/count drifted")
    files_sha = _task7_files_digest(files)
    if freeze["files_sha256"] != files_sha or freeze["freeze_id"] != _task7_freeze_id(source_tree_oid, files_sha):
        return Finding("deterministic_verdicts", "freeze-identity", f"deterministic verdict {role} source freeze identity drifted")
    if (
        freeze["expected_final_tree_oid"] != source_tree_oid
        or bundle["freeze_id"] != freeze["freeze_id"]
        or bundle["expected_final_tree_oid"] != freeze["expected_final_tree_oid"]
    ):
        return Finding("deterministic_verdicts", "wrong-source", f"deterministic verdict {role} source freeze targets another tree")
    checker_rows = [row for row in files if row["path"] == bundle["checker"]["path"]]
    if len(checker_rows) != 1:
        return Finding("deterministic_verdicts", "checker-freeze", f"deterministic verdict {role} checker is absent from source freeze")
    checker_row = checker_rows[0]
    if any(bundle["checker"][field] != checker_row[field] for field in ("path", "blob_oid", "raw_sha256")):
        return Finding("deterministic_verdicts", "checker-freeze", f"deterministic verdict {role} checker identity differs from source freeze")
    return _task7_result_semantics(
        role,
        spec,
        bundle,
        report,
        command_log,
        freeze,
        root=root,
    )


def _validate_deterministic_verdicts(value: Mapping[str, Any], *, root: Path) -> Finding | None:
    verdicts = value.get("deterministic_verdicts")
    if not isinstance(verdicts, Mapping):
        return Finding("deterministic_verdicts", "missing", "deterministic_verdicts object is missing")
    missing = [role for role in DETERMINISTIC_VERDICT_SPECS if role not in verdicts]
    if missing:
        return Finding("deterministic_verdicts", "missing", f"deterministic verdict {missing[0]} is missing")
    source = value.get("source") if isinstance(value, Mapping) else None
    source_tree_oid = source.get("tree_oid") if isinstance(source, Mapping) else None
    if not isinstance(source_tree_oid, str):
        return Finding("deterministic_verdicts", "wrong-source", "receipt source tree is unavailable")
    seen_primary: set[tuple[str, str]] = set()
    shared_freeze: tuple[str, str, str] | None = None
    for role, spec in DETERMINISTIC_VERDICT_SPECS.items():
        ref = verdicts.get(role)
        if not isinstance(ref, Mapping):
            return Finding("deterministic_verdicts", "shape", f"deterministic verdict {role} reference is not an object")
        if ref.get("status") != spec["status"]:
            return Finding(
                "deterministic_verdicts",
                "status",
                f"deterministic verdict {role} status must be {spec['status']}, got {ref.get('status')}",
            )
        primary_identity = (str(ref.get("path")), str(ref.get("sha256")))
        if primary_identity in seen_primary:
            return Finding(
                "deterministic_verdicts", "replayed-evidence", f"deterministic verdict {role} replays another role bundle"
            )
        seen_primary.add(primary_identity)
        try:
            path = resolve_repo_path(root, str(ref.get("path", "")), must_exist=True, expect_file=True)
        except PathCustodyError as exc:
            return Finding(
                "deterministic_verdicts",
                exc.subcode,
                f"deterministic verdict {role} path rejected: {exc}",
            )
        try:
            raw = path.read_bytes()
            artifact = strict_json_loads(raw, label=str(path))
        except DuplicateObjectKey as exc:
            return Finding("deterministic_verdicts", "duplicate-key", f"deterministic verdict {role} duplicate key: {exc}")
        except (OSError, ValueError) as exc:
            return Finding("deterministic_verdicts", "artifact-read", f"deterministic verdict {role} read failed: {exc}")
        if len(raw) != ref.get("byte_count") or sha256_bytes(raw) != ref.get("sha256"):
            return Finding(
                "deterministic_verdicts",
                "artifact-hash",
                f"deterministic verdict {role} byte_count/sha256 differs from retained artifact",
            )
        if not isinstance(artifact, Mapping):
            return Finding("deterministic_verdicts", "artifact-shape", f"deterministic verdict {role} artifact is not an object")
        bundle_finding = _validate_task7_bundle(
            role, spec, artifact, root=root, source_tree_oid=source_tree_oid
        )
        if bundle_finding:
            return bundle_finding
        if ref.get("artifact_schema") != artifact.get("schema") or ref.get("kind") != artifact.get("kind"):
            return Finding(
                "deterministic_verdicts",
                "reference-identity",
                f"deterministic verdict {role} reference schema/kind differs from retained artifact",
            )
        current_freeze = (
            artifact["source_freeze"]["path"],
            artifact["source_freeze"]["sha256"],
            artifact["freeze_id"],
        )
        if shared_freeze is None:
            shared_freeze = current_freeze
        elif current_freeze != shared_freeze:
            return Finding(
                "deterministic_verdicts", "freeze-cohort", f"deterministic verdict {role} uses another source freeze"
            )
    return None


def _branch_protection_app(protection: Mapping[str, Any], app: Mapping[str, Any]) -> Finding | None:
    if protection.get("protected") is not True:
        return None
    app_id = app.get("id")
    for check in protection.get("checks", []):
        protected_app_id = check.get("app_id") if isinstance(check, Mapping) else None
        if protected_app_id is not None and protected_app_id != app_id:
            return Finding(
                "required_checks",
                "branch-protection-app",
                f"branch-protection check app_id {protected_app_id} differs from observed GitHub Actions app {app_id}",
            )
    return None


def _live_tree_files(source_sha: str) -> list[dict[str, Any]]:
    raw = _run_git(["ls-tree", "-r", "-l", "-z", "--full-tree", source_sha])
    metadata: list[tuple[str, int, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        header, path_raw = record.split(b"\t", 1)
        parts = header.decode("ascii").split()
        if len(parts) != 4 or not parts[3].isdigit():
            raise ValueError(f"malformed Task 7 final Git ls-tree record: {record!r}")
        _mode, object_type, oid, size_text = parts
        if object_type != "blob":
            raise ValueError(f"Task 7 final source freeze supports blobs only: {record!r}")
        path = path_raw.decode("utf-8", "strict")
        size = int(size_text)
        metadata.append((oid, size, path))
    completed = subprocess.run(
        ["git", "--no-replace-objects", "cat-file", "--batch"],
        cwd=ROOT,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
        input=("\n".join(oid for oid, _size, _path in metadata) + "\n").encode("ascii"),
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"Task 7 final git cat-file --batch failed: {completed.stderr.decode('utf-8', 'replace').strip()}")
    stream = io.BytesIO(completed.stdout)
    rows: list[dict[str, Any]] = []
    for oid, size, path in metadata:
        header = stream.readline().decode("ascii").strip().split()
        if len(header) != 3 or header[0] != oid or header[1] != "blob" or not header[2].isdigit():
            raise ValueError(f"Task 7 final git cat-file header drifted for {path}: {header}")
        blob = stream.read(int(header[2]))
        if stream.read(1) != b"\n" or len(blob) != size:
            raise ValueError(f"Task 7 final Git blob bytes drifted for {path}")
        rows.append({"path": path, "blob_oid": oid, "byte_count": len(blob), "raw_sha256": sha256_bytes(blob)})
    if stream.read():
        raise ValueError("Task 7 final git cat-file returned trailing bytes")
    return sorted(rows, key=lambda row: row["path"])


def _collect_deterministic_verdicts(source_sha: str, source_tree_oid: str) -> dict[str, dict[str, Any]]:
    verdicts: dict[str, dict[str, Any]] = {}
    for role, spec in DETERMINISTIC_VERDICT_SPECS.items():
        path = ROOT / spec["path"]
        try:
            raw = path.read_bytes()
            artifact = strict_json_loads(raw, label=str(path))
        except DuplicateObjectKey as exc:
            raise ValueError(f"deterministic verdict {role} duplicate key: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"deterministic verdict {role} is unavailable at {spec['path']}: {exc}") from exc
        if not isinstance(artifact, Mapping):
            raise ValueError(f"deterministic verdict {role} artifact is not an object")
        expected_identity = {
            "schema": DETERMINISTIC_VERDICT_SCHEMA,
            "kind": spec["kind"],
            "status": spec["status"],
            "terminal_claim": False,
        }
        if {field: artifact.get(field) for field in expected_identity} != expected_identity:
            raise ValueError(f"deterministic verdict {role} is not the required precommit Task 7 PASS/ACCEPT evidence")
        verdicts[role] = {
            "path": spec["path"].as_posix(),
            "byte_count": len(raw),
            "sha256": sha256_bytes(raw),
            "artifact_schema": artifact["schema"],
            "kind": artifact["kind"],
            "status": artifact["status"],
        }
    probe = {"source": {"tree_oid": source_tree_oid}, "deterministic_verdicts": verdicts}
    finding = _validate_deterministic_verdicts(probe, root=ROOT)
    if finding:
        raise ValueError(f"Task 7 deterministic evidence failed [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    first_path = ROOT / DETERMINISTIC_VERDICT_SPECS["no_model_preflight"]["path"]
    first_bundle = strict_json_loads(first_path.read_bytes(), label=str(first_path))
    freeze_path = resolve_repo_path(ROOT, first_bundle["source_freeze"]["path"], must_exist=True, expect_file=True)
    freeze = strict_json_loads(freeze_path.read_bytes(), label=str(freeze_path))
    if freeze["files"] != _live_tree_files(source_sha):
        raise ValueError("Task 7 complete precommit source freeze differs from the final source commit tree")
    return verdicts


def _validate_receipt_structure(value: Mapping[str, Any], *, root: Path = ROOT) -> list[Finding]:
    source = value.get("source") if isinstance(value, Mapping) else None
    locator = value.get("receipt_locator") if isinstance(value, Mapping) else None
    try:
        resolve_repo_path(root, str(locator), must_exist=False)
    except PathCustodyError as exc:
        return [Finding("receipt_custody", exc.subcode, f"receipt_locator escape rejected: {exc}")]
    deterministic_finding = _validate_deterministic_verdicts(value, root=root)
    if deterministic_finding:
        return [deterministic_finding]
    issues = validate_schema_subset(value, _schema())
    if issues:
        first = issues[0]
        return [Finding("receipt_schema", first.keyword.replace("_", "-"), f"{first.path}: {first.message}")]
    assert isinstance(source, Mapping)
    expected_locator = (RECEIPT_REL / f"{source['commit_sha']}.json").as_posix()
    if locator != expected_locator:
        return [Finding("receipt_custody", "locator-mismatch", f"receipt_locator {locator} does not equal commit-keyed {expected_locator}")]
    if value["receipt_id"] != _receipt_id(source["commit_sha"], value["run"]["id"], value["run"]["attempt"]):
        return [Finding("receipt_identity", "receipt-id", "receipt_id is not derived from exact source/run/attempt")]
    if source["state_digest_sha256"] != _source_state_digest(source):
        return [Finding("source_state", "state-digest", "clean source state digest differs from exact source/equality bytes")]
    parent_lines = [f"parent {oid}" for oid in source["parent_oids"]]
    if source["raw_parent_lines"] != parent_lines:
        return [Finding("lineage", "parent-drift", "raw parents differ from parent_oids; same-tree parent substitution is forbidden")]
    if [row["oid"] for row in value["lineage"]["parent_object_types"]] != source["parent_oids"]:
        return [Finding("lineage", "parent-object-types", "parent object-type rows differ from raw parents")]
    equality = source["equality"]
    if not (
        equality["local_head"]
        == equality["upstream_oid"]
        == equality["live_remote_oid"]
        == source["commit_sha"]
    ):
        return [Finding("source_equality", "exact-oid-equality", "local/upstream/live remote are not the exact source SHA")]
    if value["run"]["head_sha"] != source["commit_sha"]:
        return [Finding("ci_identity", "head-sha", "run head_sha is not the exact source SHA")]
    if value["run"]["head_branch"] != value["repository"]["branch"]:
        return [Finding("ci_identity", "head-branch", "run head branch differs from repository branch")]
    if value["run"]["check_suite_id"] != value["job"]["check_suite_id"]:
        return [Finding("ci_identity", "check-suite", "run/job check-suite IDs differ")]
    if value["job"]["check_run_id"] != value["required_checks"]["results"][0]["check_run_id"]:
        return [Finding("required_checks", "check-run", "required check and job check-run IDs differ")]
    if value["job"]["app"] != value["required_checks"]["results"][0]["app"]:
        return [Finding("ci_job", "app", "job/check-run GitHub Actions app identity differs")]
    protection_app_finding = _branch_protection_app(
        value["required_checks"]["branch_protection"], value["job"]["app"]
    )
    if protection_app_finding:
        return [protection_app_finding]
    binding = value["source_binding"]
    carriers = value["carriers"]
    if [row["path"] for row in carriers] != list(CARRIER_PATHS):
        return [Finding("carrier_identity", "carrier-set", "exact four carrier path order differs")]
    if len({row["blob_oid"] for row in carriers}) != 4:
        return [Finding("carrier_identity", "duplicate-blob", "carrier blob identities must be distinct")]
    if any(row["source_binding_raw_sha256"] != binding["raw_sha256"] for row in carriers):
        return [Finding("source_binding", "carrier-binding", "carrier source binding raw hashes differ")]
    if value["carrier_binding_digest"]["sha256"] != _carrier_binding_digest(binding, carriers):
        return [Finding("carrier_identity", "binding-digest", "carrier binding digest differs from exact carrier identities")]
    migration = value["migration_carrier"]
    migration_row = carriers[3]
    if any(migration[field] != migration_row[field] for field in ("path", "schema", "blob_oid", "raw_sha256")):
        return [Finding("carrier_identity", "migration-drift", "migration carrier identity differs from the exact fourth carrier")]
    predecessor = value["predecessor_receipt"]
    if predecessor["kind"] == "genesis":
        if value["predecessor_record_sha256"] is not None or predecessor["receipt_sha256"] is not None or value["custody_sequence"] != 1:
            return [Finding("receipt_custody", "genesis-mismatch", "genesis predecessor and custody sequence are inconsistent")]
    elif predecessor["receipt_sha256"] != value["predecessor_record_sha256"] or value["custody_sequence"] <= 1:
        return [Finding("receipt_custody", "predecessor-mismatch", "predecessor receipt does not match CAS predecessor")]
    evidence = value["linux_a01"]["evidence"]
    evidence_raw = canonical_json_bytes(evidence)
    artifact = value["linux_a01"]["artifact"]
    if value["artifact_inventory"] != [artifact]:
        return [Finding("artifact_inventory", "inventory-drift", "complete run artifact inventory differs from Linux A01 artifact")]
    if artifact["entry_byte_count"] != len(evidence_raw) or artifact["entry_sha256"] != sha256_bytes(evidence_raw):
        return [Finding("linux_a01", "artifact-hash", "Linux A01 artifact entry byte/hash identity differs from evidence JSON")]
    linux = value["linux_a01"]
    if not (
        linux["source_sha"] == evidence["source_sha"] == source["commit_sha"]
        and linux["run_id"] == evidence["run_id"] == value["run"]["id"]
        and evidence["run_number"] == value["run"]["number"]
        and evidence["run_attempt"] == value["run"]["attempt"]
        and linux["job_id"] == value["job"]["id"]
        and linux["check_run_id"] == value["job"]["check_run_id"]
    ):
        return [Finding("linux_a01", "artifact-run", "Linux A01 artifact source/run/job/check join differs")]
    for field in ("command", "checker", "contract_test", "suite_marker", "suite_test_count", "suite_status", "skipped_count", "substituted"):
        if linux[field] != evidence[field]:
            return [Finding("linux_a01", f"artifact-{field.replace('_', '-')}", f"Linux A01 artifact {field} differs from receipt evidence")]
    named_steps = [row for row in value["job"]["steps"] if row["name"] == LINUX_STEP_NAME]
    if len(named_steps) != 1 or named_steps[0] != linux["step"]:
        return [Finding("linux_a01", "named-step", "exactly one successful named Linux A01 custody step is required")]
    if linux["runner_label"] not in value["job"]["runner"]["labels"]:
        return [Finding("linux_a01", "runner-label", "Linux A01 ubuntu-latest runner label is absent from exact job")]
    if linux["job_log_sha256"] != value["job_log"]["sha256"]:
        return [Finding("linux_a01", "job-log-sha256", "Linux A01 retained job log SHA differs")]
    vcs_finding = _validate_vcs(value)
    return [vcs_finding] if vcs_finding else []


def _compare_live(value: Mapping[str, Any], observed: Mapping[str, Any]) -> Finding | None:
    if observed.get("provider") != value["provider"]:
        return Finding("ci_identity", "provider", f"CI provider drifted to {observed.get('provider')}")
    source = value["source"]
    observed_source = observed.get("source", {})
    clean = observed_source.get("clean_state", {})
    if clean.get("index_clean") is not True or clean.get("worktree_clean") is not True or clean.get("untracked_source_paths") != []:
        return Finding("source_state", "dirty-source", f"source worktree/index/untracked inventory is dirty: {clean}")
    expected_equality = source["equality"]
    actual_equality = observed_source.get("equality", {})
    if actual_equality.get("upstream_ref") != expected_equality.get("upstream_ref"):
        return Finding(
            "source_equality",
            "upstream-ref",
            f"upstream ref drifted: {actual_equality.get('upstream_ref')} != {expected_equality.get('upstream_ref')}",
        )
    for field, subcode, label in (
        ("local_head", "local-head", "local head"),
        ("upstream_oid", "upstream", "upstream exact source SHA"),
        ("live_remote_oid", "live-remote", "live remote exact source SHA"),
        ("expected_old_remote_oid", "expected-old-remote", "expected old remote from push authorization"),
    ):
        if actual_equality.get(field) != expected_equality.get(field):
            return Finding("source_equality", subcode, f"{label} drifted: {actual_equality.get(field)} != {expected_equality.get(field)}")
    actual_lineage = observed.get("lineage", {})
    if actual_lineage.get("shallow_repository") is not False or actual_lineage.get("full_history") is not True:
        return Finding("lineage", "shallow-history", "shallow repository cannot prove full history")
    if actual_lineage.get("strict_successor") is not True:
        return Finding("lineage", "strict-successor", "checkpoint strict successor ancestry is false")
    if actual_lineage.get("replace_ref_count") != 0 or actual_lineage.get("replace_objects_disabled") is not True:
        return Finding("lineage", "replace-object", "Git replace objects must be absent and disabled")
    if actual_lineage.get("grafts_present") is not False:
        return Finding("lineage", "graft", "Git graft substitution is forbidden")
    if actual_lineage.get("source_commit_object_type") != "commit":
        return Finding("lineage", "object-type", f"source object type {actual_lineage.get('source_commit_object_type')} is not commit")
    if observed_source.get("parent_oids") != source["parent_oids"] or observed_source.get("raw_parent_lines") != source["raw_parent_lines"]:
        return Finding("lineage", "parent-drift", "raw parents drifted under a same-tree different-parent substitution")
    actual_binding = observed.get("source_binding", {})
    if actual_binding.get("raw_sha256") != value["source_binding"]["raw_sha256"]:
        return Finding("source_binding", "raw-sha256", "source binding raw_sha256 drifted")
    actual_carriers = observed.get("carriers", [])
    if len(actual_carriers) != 4:
        return Finding("carrier_identity", "carrier-set", "exact four carrier live identities are required")
    for expected, actual in zip(value["carriers"], actual_carriers):
        if actual.get("blob_oid") != expected["blob_oid"]:
            return Finding("carrier_identity", "blob-oid", f"carrier {expected['path']} blob_oid drifted")
        if actual != expected:
            return Finding("carrier_identity", "carrier-drift", f"carrier {expected['path']} byte/SHA/schema identity drifted")
    if observed.get("migration_carrier", {}).get("status") != value["migration_carrier"]["status"]:
        return Finding("carrier_identity", "migration-status", f"migration status drifted to {observed.get('migration_carrier', {}).get('status')}")
    if observed.get("migration_carrier") != value["migration_carrier"]:
        return Finding("carrier_identity", "migration-drift", "migration carrier schema/status/hash drifted")
    actual_deterministic = observed.get("deterministic_verdicts")
    if not isinstance(actual_deterministic, Mapping):
        return Finding("deterministic_verdicts", "live-missing", "live deterministic Task 7 verdict readback is missing")
    if actual_deterministic != value["deterministic_verdicts"]:
        return Finding("deterministic_verdicts", "live-drift", "live deterministic Task 7 verdict path/hash/status readback drifted")
    actual_workflow = observed.get("workflow", {})
    if actual_workflow.get("blob_oid") != value["workflow"]["blob_oid"]:
        return Finding("workflow_identity", "blob-oid", "workflow blob_oid drifted")
    if actual_workflow != value["workflow"]:
        return Finding("workflow_identity", "workflow-drift", "workflow ID/name/path/blob/raw hash drifted")
    actual_run = observed.get("run", {})
    if actual_run.get("event") != value["run"]["event"]:
        return Finding("ci_identity", "event", f"run event {actual_run.get('event')} is not required push event {value['run']['event']}")
    if actual_run.get("head_sha") != value["run"]["head_sha"]:
        return Finding("ci_identity", "head-sha", "run head_sha is not the exact source SHA")
    if actual_run != value["run"]:
        return Finding("ci_identity", "run-drift", "run ID/number/attempt/branch/status/conclusion/timestamps drifted")
    actual_required = observed.get("required_checks", {})
    if "branch_protection" not in actual_required:
        return Finding("required_checks", "branch-protection-readback", "branch protection readback is missing")
    if actual_required.get("owner_required_set") != value["required_checks"]["owner_required_set"]:
        return Finding("required_checks", "check-set", f"owner-derived required check set drifted: {actual_required.get('owner_required_set')}")
    results = actual_required.get("results", [])
    names = [row.get("name") for row in results if isinstance(row, Mapping)]
    if len(names) != len(set(names)):
        return Finding("required_checks", "duplicate-required-check", f"duplicate required check {CHECK_NAME} observed")
    if actual_required != value["required_checks"]:
        return Finding("required_checks", "required-check-drift", "required check result or branch protection readback drifted")
    actual_job = observed.get("job", {})
    if actual_job.get("name") != value["job"]["name"]:
        return Finding("ci_job", "job-name", f"job {actual_job.get('name')} is not {JOB_NAME}")
    if actual_job.get("raw_check_run_name") != JOB_NAME:
        return Finding(
            "ci_job",
            "check-run-name",
            f"raw check-run name {actual_job.get('raw_check_run_name')} is not {JOB_NAME}",
        )
    if actual_job.get("app", {}).get("slug") != "github-actions":
        return Finding("ci_job", "app", f"job app {actual_job.get('app', {}).get('slug')} is not github-actions")
    if actual_job.get("conclusion") != "success":
        return Finding("ci_job", "job-conclusion", f"runtime-checks job conclusion is {actual_job.get('conclusion')}")
    if actual_job != value["job"]:
        return Finding("ci_job", "job-drift", "job/check-run/runner/steps/timestamps/URLs drifted")
    actual_linux = observed.get("linux_a01")
    if observed.get("artifact_inventory") != value["artifact_inventory"]:
        return Finding("artifact_inventory", "live-drift", "complete exact-run artifact inventory drifted")
    if not isinstance(actual_linux, Mapping):
        return Finding("linux_a01", "missing", "Linux A01 evidence is missing")
    if "artifact" not in actual_linux:
        return Finding("linux_a01", "artifact-missing", "Linux A01 structured artifact is missing")
    if actual_linux["artifact"].get("expired") is not False:
        return Finding("linux_a01", "artifact-expired", "Linux A01 artifact is expired")
    if actual_linux["artifact"].get("entry_sha256") != value["linux_a01"]["artifact"]["entry_sha256"]:
        return Finding("linux_a01", "artifact-hash", "Linux A01 artifact entry_sha256 drifted")
    if actual_linux.get("evidence", {}).get("run_id") != value["linux_a01"]["evidence"]["run_id"]:
        return Finding("linux_a01", "artifact-run", "Linux A01 artifact run_id differs")
    if actual_linux.get("step", {}).get("conclusion") != "success":
        return Finding("linux_a01", "step-conclusion", f"Linux A01 step conclusion is {actual_linux.get('step', {}).get('conclusion')}")
    if actual_linux.get("command") != LINUX_COMMAND:
        return Finding("linux_a01", "command-substitution", f"Linux A01 substitution detected; required {LINUX_COMMAND}")
    if actual_linux.get("runner_label") != "ubuntu-latest":
        return Finding("linux_a01", "runner-label", f"Linux A01 runner {actual_linux.get('runner_label')} is not ubuntu-latest")
    if actual_linux.get("checker", {}).get("raw_sha256") != value["linux_a01"]["checker"]["raw_sha256"]:
        return Finding("linux_a01", "checker-hash", "Linux A01 checker raw_sha256 drifted")
    if actual_linux.get("contract_test", {}).get("raw_sha256") != value["linux_a01"]["contract_test"]["raw_sha256"]:
        return Finding("linux_a01", "test-hash", "Linux A01 contract test raw_sha256 drifted")
    actual_log = observed.get("job_log", {})
    if actual_log.get("sha256") != value["job_log"]["sha256"]:
        return Finding("linux_a01", "job-log-sha256", "Linux A01 job log sha256 drifted")
    if actual_linux != value["linux_a01"]:
        return Finding("linux_a01", "evidence-drift", "Linux A01 artifact/step/suite/log evidence drifted")
    return None


def validate_receipt(
    value: Mapping[str, Any],
    *,
    root: Path = ROOT,
    live_observation: Mapping[str, Any] | None = None,
) -> list[Finding]:
    structural = _validate_receipt_structure(value, root=root)
    if structural:
        return structural
    if live_observation is not None:
        finding = _compare_live(value, live_observation)
        if finding:
            return [finding]
    return []


def _expectation_ok(path: Path, finding: Finding) -> tuple[bool, str]:
    expectation_path = path.with_name(f"{path.stem}.expectation.json")
    try:
        expectation = strict_json_loads(expectation_path.read_bytes(), label=str(expectation_path))
        expectation_schema = _schema(EXPECTATION_SCHEMA_PATH)
    except (OSError, ValueError) as exc:
        return False, f"{path.name}: expectation load failed: {exc}"
    issues = validate_schema_subset(expectation, expectation_schema)
    if issues:
        return False, f"{path.name}: expectation schema failed: {issues[0].message}"
    observed = diagnostic(finding, path.name)
    for expected_key, observed_key in (
        ("expected_checker_id", "checker_id"),
        ("expected_exit_category", "exit_category"),
        ("expected_exit_code", "exit_code"),
        ("expected_earliest_stage", "earliest_stage"),
        ("expected_failure_class", "failure_class"),
        ("expected_failure_subcode", "failure_subcode"),
        ("expected_downstream_invalidated", "downstream_invalidated"),
    ):
        if expectation[expected_key] != observed[observed_key]:
            return False, f"{path.name}: {expected_key} expected {expectation[expected_key]!r}, got {observed[observed_key]!r}"
    diagnostic_text = json.dumps(observed, sort_keys=True)
    for marker in expectation["required_diagnostic_markers"]:
        if marker not in diagnostic_text:
            return False, f"{path.name}: required marker {marker!r} absent from {diagnostic_text}"
    return True, ""


def _custody_scenario(value: dict[str, Any], operation: str) -> Finding:
    with tempfile.TemporaryDirectory(prefix="daee-ci-readback-custody-") as temporary:
        root = Path(temporary)
        target = root / f"{value['source']['commit_sha']}.json"
        if operation == "custody-precreate-collision":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(canonical_json_bytes({"different": True}))
            try:
                append_claim_before_cas(root, target, value, expected_predecessor_sha256=None)
            except CustodyError as exc:
                return Finding("receipt_custody", exc.subcode, f"create-once publication collision rejected: {exc}")
            return Finding("self_test", "unexpected-pass", "create-once collision survived")
        dummy = {"schema": "self-test-predecessor", "predecessor_record_sha256": None}
        append_claim_before_cas(root, root / "predecessor.json", dummy, expected_predecessor_sha256=None)
        try:
            append_claim_before_cas(root, target, value, expected_predecessor_sha256=None)
        except CustodyError as exc:
            return Finding("receipt_custody", exc.subcode, f"CAS predecessor mismatch rejected: {exc}")
        return Finding("self_test", "unexpected-pass", "CAS predecessor mismatch survived")


def self_test() -> tuple[list[str], int, int]:
    problems: list[str] = []
    base, _raw, finding = _load_raw(VALID_FIXTURE)
    if finding or base is None:
        return [f"valid fixture load failed: {finding}"], 0, 0
    valid_findings = validate_receipt(base, live_observation=copy.deepcopy(base))
    if valid_findings:
        problems.append(f"valid fixture rejected: {valid_findings[0].failure_class}/{valid_findings[0].failure_subcode}: {valid_findings[0].message}")
    invalid_paths = sorted(
        path
        for path in (FIXTURE_ROOT / "invalid").glob("*.json")
        if not path.name.endswith(".expectation.json")
    )
    for path in invalid_paths:
        try:
            fixture = strict_json_loads(path.read_bytes(), label=str(path))
        except (OSError, ValueError) as exc:
            problems.append(f"{path.name}: fixture load failed: {exc}")
            continue
        receipt = copy.deepcopy(base)
        observation = copy.deepcopy(base)
        raw_override: bytes | None = None
        custody_operation: str | None = None
        try:
            for operation in fixture.get("operations", []):
                op = operation.get("op")
                if op == "set":
                    _set_dotted(receipt, operation["path"], operation.get("value"))
                elif op == "delete":
                    _delete_dotted(receipt, operation["path"])
                elif op == "append":
                    _append_dotted(receipt, operation["path"], operation.get("value"))
                elif op == "observation-set":
                    _set_dotted(observation, operation["path"], operation.get("value"))
                elif op == "observation-delete":
                    _delete_dotted(observation, operation["path"])
                elif op == "observation-append":
                    _append_dotted(observation, operation["path"], operation.get("value"))
                elif op == "inject-duplicate-key":
                    raw_override = (
                        "{" + json.dumps(operation["key"]) + ":" + json.dumps(operation.get("value")) + "," + json.dumps(receipt)[1:]
                    ).encode("utf-8")
                elif op in {"custody-precreate-collision", "custody-head-predecessor-mismatch"}:
                    custody_operation = op
                else:
                    raise ValueError(f"unsupported fixture operation {operation!r}")
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"{path.name}: fixture operation failed: {exc}")
            continue
        if raw_override is not None:
            try:
                strict_json_loads(raw_override, label=path.name)
            except DuplicateObjectKey as exc:
                first = Finding("malformed_json", "duplicate-key", f"duplicate JSON key rejected: {exc}")
            except ValueError as exc:
                first = Finding("malformed_json", "malformed-json", str(exc))
            else:
                first = Finding("self_test", "unexpected-pass", "duplicate-key fixture survived")
        elif custody_operation:
            first = _custody_scenario(receipt, custody_operation)
        else:
            findings = validate_receipt(receipt, live_observation=observation)
            first = findings[0] if findings else Finding("self_test", "unexpected-pass", "invalid fixture survived")
        ok, message = _expectation_ok(path, first)
        if not ok:
            problems.append(message)
    return problems, 1, len(invalid_paths)


GitRunner = Callable[[Sequence[str], bool], bytes]


def _run_git(arguments: Sequence[str], binary: bool = False) -> bytes:
    env = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}
    completed = subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"git {' '.join(arguments)} failed: {completed.stderr.decode('utf-8', 'replace').strip()}")
    return completed.stdout


def _git_text(arguments: Sequence[str]) -> str:
    return _run_git(arguments).decode("utf-8", "strict").strip()


def _gh(arguments: Sequence[str], *, binary: bool = False, allow_404: bool = False) -> tuple[int, bytes]:
    completed = subprocess.run(["gh", *arguments], cwd=ROOT, capture_output=True, check=False)
    if completed.returncode == 0:
        return 200, completed.stdout
    stderr = completed.stderr.decode("utf-8", "replace")
    if allow_404 and "HTTP 404" in stderr:
        return 404, completed.stdout
    raise ValueError(f"authenticated gh {' '.join(arguments)} failed: {stderr.strip()}")


def _gh_json(endpoint: str, *, allow_404: bool = False) -> tuple[int, dict[str, Any]]:
    status, raw = _gh(["api", "--method", "GET", endpoint], allow_404=allow_404)
    if status == 404:
        return status, {}
    value = strict_json_loads(raw, label=f"gh api {endpoint}")
    if not isinstance(value, dict):
        raise ValueError(f"gh api {endpoint} did not return an object")
    return status, value


def _gh_auth() -> None:
    completed = subprocess.run(
        ["gh", "auth", "status", "--hostname", "github.com"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"authenticated gh credentials are unavailable: {completed.stderr.decode('utf-8', 'replace').strip()}")


def _remote_repository(remote_url: str) -> str:
    normalized = remote_url.strip()
    match = re.search(r"github\.com[/:]([^/]+/[^/]+?)(?:\.git)?$", normalized)
    if not match:
        raise ValueError(f"remote URL is not a GitHub repository: {remote_url}")
    return match.group(1)


def _git_object(source_sha: str, path: str) -> tuple[str, bytes]:
    blob_oid = _git_text(["rev-parse", f"{source_sha}:{path}"])
    if _git_text(["cat-file", "-t", blob_oid]) != "blob":
        raise ValueError(f"{path} is not a Git blob at {source_sha}")
    return blob_oid, _run_git(["show", f"{source_sha}:{path}"])


def _workflow_contract(raw: bytes) -> dict[str, Any]:
    try:
        workflow = yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"workflow YAML is invalid: {exc}") from exc
    if not isinstance(workflow, dict) or workflow.get("name") != WORKFLOW_NAME:
        raise ValueError("workflow name drifted from CI")
    if set(workflow) != {"name", True, "permissions", "jobs"}:
        raise ValueError("workflow top-level contract drifted")
    if workflow.get(True) != {"push": None, "pull_request": None}:
        raise ValueError("workflow triggers must be exactly push and pull_request")
    if workflow.get("permissions") != {"contents": "read"}:
        raise ValueError("workflow permissions must be exactly contents: read")
    if set(workflow.get("jobs", {})) != {JOB_NAME}:
        raise ValueError("workflow job set must contain only runtime-checks")
    job = workflow.get("jobs", {}).get(JOB_NAME)
    if not isinstance(job, dict) or job.get("runs-on") != "ubuntu-latest":
        raise ValueError("runtime-checks must run on ubuntu-latest")
    if job.get("continue-on-error") not in (None, False):
        raise ValueError("runtime-checks continue-on-error is forbidden")
    steps = job.get("steps", [])
    if not isinstance(steps, list) or any(not isinstance(row, dict) for row in steps):
        raise ValueError("workflow step set is malformed")
    if any(row.get("continue-on-error") not in (None, False) for row in steps):
        raise ValueError("workflow step continue-on-error is forbidden")
    by_name = {row.get("name"): row for row in steps if row.get("name")}
    if by_name.get(LINUX_WRITER_STEP, {}).get("run") != LINUX_WRITER_COMMAND:
        raise ValueError("Linux A01 evidence writer command/arguments drifted")
    upload = by_name.get("Upload Linux A01 evidence", {})
    if upload.get("uses") != "actions/upload-artifact@v4" or upload.get("with") != LINUX_UPLOAD_WITH:
        raise ValueError("Linux A01 artifact upload identity drifted")
    if set(job) != {"runs-on", "steps"} or steps != EXPECTED_WORKFLOW_STEPS:
        raise ValueError("workflow exact ordered step set drifted; executable substitution is forbidden")
    return workflow


def _a01_log(raw: bytes) -> tuple[bytes, int, str, int]:
    start_marker = f"##[group]Run {LINUX_COMMAND}".encode("utf-8")
    end_marker = f"##[group]Run {FULL_CI_COMMAND}".encode("utf-8")
    try:
        start = raw.index(start_marker)
        end = raw.index(end_marker, start + len(start_marker))
    except ValueError as exc:
        raise ValueError("job log does not retain the named Linux A01 command before full local CI") from exc
    segment = raw[start:end]
    text = segment.decode("utf-8", "replace")
    counts = re.findall(r"Ran ([0-9]+) tests? in ", text)
    if len(counts) != 1 or re.search(r"(?m)^.*\bOK\s*$", text) is None:
        raise ValueError("Linux A01 log segment lacks one exact suite count and OK marker")
    skipped = sum(int(value) for value in re.findall(r"skipped=([0-9]+)", text))
    if skipped:
        raise ValueError("Linux A01 log segment contains skipped tests")
    return segment, int(counts[0]), "OK", skipped


def _artifact_zip(raw: bytes) -> tuple[bytes, str]:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = archive.namelist()
            if names != [LINUX_ARTIFACT_ENTRY]:
                raise ValueError(f"Linux A01 artifact zip must contain exactly {LINUX_ARTIFACT_ENTRY}, got {names}")
            info = archive.getinfo(LINUX_ARTIFACT_ENTRY)
            if info.is_dir() or info.file_size <= 0:
                raise ValueError("Linux A01 artifact entry is not a nonempty file")
            evidence_raw = archive.read(info)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"Linux A01 artifact zip is invalid: {exc}") from exc
    return evidence_raw, sha256_bytes(raw)


def _lineage(source_sha: str) -> tuple[dict[str, Any], list[str], list[str]]:
    shallow = _git_text(["rev-parse", "--is-shallow-repository"]) == "true"
    replace_refs = [line for line in _git_text(["for-each-ref", "--format=%(refname)", "refs/replace"]).splitlines() if line]
    graft_path = Path(_git_text(["rev-parse", "--git-path", "info/grafts"]))
    if not graft_path.is_absolute():
        graft_path = ROOT / graft_path
    grafts_present = graft_path.is_file() and bool(graft_path.read_bytes().strip())
    if shallow:
        raise ValueError("shallow history cannot issue exact source receipt")
    if replace_refs:
        raise ValueError("Git replace refs are forbidden for exact source receipt")
    if grafts_present:
        raise ValueError("Git grafts are forbidden for exact source receipt")
    if source_sha == CHECKPOINT_COMMIT:
        raise ValueError("source SHA must be a strict successor of the checkpoint")
    ancestor = subprocess.run(
        ["git", "--no-replace-objects", "merge-base", "--is-ancestor", CHECKPOINT_COMMIT, source_sha],
        cwd=ROOT,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError("source SHA is not a strict full-history descendant of checkpoint")
    commit_raw = _run_git(["cat-file", "-p", source_sha]).decode("utf-8", "strict")
    tree_lines = [line for line in commit_raw.splitlines() if line.startswith("tree ")]
    parent_lines = [line for line in commit_raw.splitlines() if line.startswith("parent ")]
    if len(tree_lines) != 1 or not parent_lines:
        raise ValueError("source commit raw tree/parent headers are incomplete")
    parent_oids = [line.split(" ", 1)[1] for line in parent_lines]
    parent_types = []
    for oid in parent_oids:
        object_type = _git_text(["cat-file", "-t", oid])
        if object_type != "commit":
            raise ValueError(f"parent {oid} object type is {object_type}, not commit")
        parent_types.append({"oid": oid, "type": object_type})
    checkpoint_type = _git_text(["cat-file", "-t", CHECKPOINT_COMMIT])
    checkpoint_tree = _git_text(["show", "-s", "--format=%T", CHECKPOINT_COMMIT])
    source_type = _git_text(["cat-file", "-t", source_sha])
    tree_oid = tree_lines[0].split(" ", 1)[1]
    tree_type = _git_text(["cat-file", "-t", tree_oid])
    if checkpoint_type != "commit" or checkpoint_tree != CHECKPOINT_TREE or source_type != "commit" or tree_type != "tree":
        raise ValueError("checkpoint/source/tree Git object identities drifted")
    count = int(_git_text(["rev-list", "--count", f"{CHECKPOINT_COMMIT}..{source_sha}"]))
    return {
        "checkpoint_commit": CHECKPOINT_COMMIT,
        "checkpoint_tree": CHECKPOINT_TREE,
        "strict_successor": True,
        "commit_count_from_checkpoint": count,
        "full_history": True,
        "shallow_repository": False,
        "replace_objects_disabled": True,
        "replace_ref_count": 0,
        "grafts_present": False,
        "source_commit_object_type": source_type,
        "source_tree_object_type": tree_type,
        "checkpoint_object_type": checkpoint_type,
        "parent_object_types": parent_types,
    }, parent_lines, parent_oids


def _source_and_carriers(source_sha: str, remote: str, ref: str, expected_old: str) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    local_head = _git_text(["rev-parse", "HEAD"])
    if local_head != source_sha:
        raise ValueError(f"local HEAD {local_head} differs from requested source SHA {source_sha}")
    branch = _git_text(["branch", "--show-current"])
    if branch != BRANCH:
        raise ValueError(f"local branch {branch} differs from {BRANCH}")
    status_raw = _run_git(["status", "--porcelain=v2", "-z", "--untracked-files=all"])
    if status_raw:
        raise ValueError("dirty source index/worktree/untracked inventory blocks receipt")
    upstream_ref = _git_text(["rev-parse", "--symbolic-full-name", "@{upstream}"])
    upstream_oid = _git_text(["rev-parse", "@{upstream}"])
    remote_result = subprocess.run(
        ["git", "ls-remote", "--refs", remote, ref],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    if remote_result.returncode != 0:
        raise ValueError(f"git ls-remote failed: {remote_result.stderr.strip()}")
    rows = [line.split() for line in remote_result.stdout.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != ref:
        raise ValueError(f"git ls-remote did not return exactly {ref}")
    live_remote_oid = rows[0][0]
    if not (local_head == upstream_oid == live_remote_oid == source_sha):
        raise ValueError("local/upstream/live-remote exact source equality failed")
    lineage, parent_lines, parent_oids = _lineage(source_sha)
    tree_oid = _git_text(["show", "-s", "--format=%T", source_sha])
    clean = {
        "index_clean": True,
        "worktree_clean": True,
        "untracked_source_paths": [],
        "porcelain_v2_byte_count": len(status_raw),
        "porcelain_v2_sha256": sha256_bytes(status_raw),
    }
    equality = {
        "local_head": local_head,
        "upstream_ref": upstream_ref,
        "upstream_oid": upstream_oid,
        "live_remote_ref": ref,
        "live_remote_oid": live_remote_oid,
        "expected_old_remote_oid": expected_old,
        "all_equal": True,
    }
    source = {
        "commit_sha": source_sha,
        "tree_oid": tree_oid,
        "raw_parent_lines": parent_lines,
        "parent_oids": parent_oids,
        "clean_state": clean,
        "equality": equality,
    }
    source["state_digest_sha256"] = _source_state_digest(source)
    raw_by_path: dict[str, bytes] = {}
    carrier_rows: list[dict[str, Any]] = []
    parsed_by_path: dict[str, dict[str, Any]] = {}
    for path in CARRIER_PATHS:
        blob_oid, raw = _git_object(source_sha, path)
        parsed = strict_json_loads(raw, label=f"{source_sha}:{path}")
        if not isinstance(parsed, dict):
            raise ValueError(f"carrier {path} is not an object")
        raw_by_path[path] = raw
        parsed_by_path[path] = parsed
        binding_raw = _extract_source_binding_bytes(raw, carrier_path=path)
        carrier_rows.append(
            {
                "path": path,
                "schema": parsed.get("schema"),
                "blob_oid": blob_oid,
                "byte_count": len(raw),
                "raw_sha256": sha256_bytes(raw),
                "source_binding_raw_sha256": sha256_bytes(binding_raw),
            }
        )
    tracked, findings = validate_tracked_only(root=ROOT, carrier_overrides=raw_by_path)
    if findings or tracked is None:
        first = findings[0] if findings else None
        raise ValueError(f"exact source tracked binding failed: {first}")
    binding = {
        "schema": BINDING_SCHEMA,
        "binding_id": BINDING_ID,
        "canonical_path": CARRIER_PATHS[0],
        "raw_sha256": tracked["binding_sha256"],
    }
    if any(row["source_binding_raw_sha256"] != binding["raw_sha256"] for row in carrier_rows):
        raise ValueError("exact source carriers do not share one raw source binding hash")
    migration_value = parsed_by_path[CARRIER_PATHS[3]]
    migration = {
        "path": CARRIER_PATHS[3],
        "schema": migration_value.get("schema"),
        "status": migration_value.get("status"),
        "shared_integration_status": migration_value.get("shared_integration_status"),
        "blob_oid": carrier_rows[3]["blob_oid"],
        "raw_sha256": carrier_rows[3]["raw_sha256"],
    }
    workflow_blob, workflow_raw = _git_object(source_sha, WORKFLOW_PATH)
    _workflow_contract(workflow_raw)
    workflow_identity = {
        "blob_oid": workflow_blob,
        "raw_sha256": sha256_bytes(workflow_raw),
    }
    return source, lineage, carrier_rows, binding, {"migration": migration, "workflow": workflow_identity}


def _record_ref(path: Path) -> dict[str, str]:
    candidate: str | Path = path
    if path.is_absolute():
        try:
            candidate = path.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
        except ValueError as exc:
            raise ValueError(f"evidence path leaves repository root: {path}") from exc
    resolved = resolve_repo_path(ROOT, candidate, must_exist=True, expect_file=True)
    raw = resolved.read_bytes()
    strict_json_loads(raw, label=str(resolved))
    return {"path": resolved.relative_to(ROOT).as_posix(), "sha256": sha256_bytes(raw)}


def _find_by_digest(root: Path, digest: str, *, schemas: set[str]) -> Path:
    matches: list[Path] = []
    if root.is_dir():
        for path in sorted(root.rglob("*.json")):
            try:
                raw = path.read_bytes()
                value = strict_json_loads(raw, label=str(path))
            except (OSError, ValueError):
                continue
            if sha256_bytes(raw) == digest and isinstance(value, dict) and value.get("schema") in schemas:
                matches.append(path)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one evidence record for digest {digest}, found {len(matches)}")
    return matches[0]


def _find_legacy_authorization(root: Path, authorization_id: str, action: str) -> Path:
    matches: list[Path] = []
    for path in sorted(root.rglob("*.json")):
        try:
            value = strict_json_loads(path.read_bytes(), label=str(path))
        except (OSError, ValueError):
            continue
        if (
            isinstance(value, dict)
            and value.get("schema") == "daee-vcs-durability-authorization-v1"
            and value.get("authorization_id") == authorization_id
            and value.get("action") == action
        ):
            matches.append(path)
    if len(matches) != 1:
        raise ValueError(f"expected one legacy {action} authorization {authorization_id}, found {len(matches)}")
    return matches[0]


def _vcs_from_push_receipt(push_receipt_path: Path) -> tuple[dict[str, Any], str]:
    candidate: str | Path = push_receipt_path
    if push_receipt_path.is_absolute():
        try:
            candidate = push_receipt_path.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
        except ValueError as exc:
            raise ValueError(f"push receipt path leaves repository root: {push_receipt_path}") from exc
    path = resolve_repo_path(ROOT, candidate, must_exist=True, expect_file=True)
    push_receipt, raw, finding = _load_raw(path)
    if finding or push_receipt is None:
        raise ValueError(f"push receipt rejected: {finding}")
    schema = push_receipt.get("schema")
    if schema == "vcs-action-receipt-v1":
        if push_receipt.get("action") != "push-countermeasure" or push_receipt.get("result") != "PASS":
            raise ValueError("push receipt is not a terminal public push PASS")
        push_claim_path = _find_by_digest(VCS_CUSTODY_ROOT / "claims", push_receipt["claim_sha256"], schemas={"vcs-action-claim-v1"})
        push_claim = strict_json_loads(push_claim_path.read_bytes(), label=str(push_claim_path))
        push_auth_path = _find_by_digest(VCS_AUTH_ROOT, push_receipt["authorization_sha256"], schemas={"vcs-action-authorization-v1"})
        push_auth = strict_json_loads(push_auth_path.read_bytes(), label=str(push_auth_path))
        commit_ref = push_auth.get("commit_receipt", {})
        commit_receipt_path = resolve_repo_path(ROOT, commit_ref.get("path", ""), must_exist=True, expect_file=True)
        if sha256_bytes(commit_receipt_path.read_bytes()) != commit_ref.get("sha256"):
            raise ValueError("push authorization commit receipt hash drifted")
        commit_receipt = strict_json_loads(commit_receipt_path.read_bytes(), label=str(commit_receipt_path))
        commit_claim_path = _find_by_digest(VCS_CUSTODY_ROOT / "claims", commit_receipt["claim_sha256"], schemas={"vcs-action-claim-v1"})
        commit_claim = strict_json_loads(commit_claim_path.read_bytes(), label=str(commit_claim_path))
        commit_auth_path = _find_by_digest(VCS_AUTH_ROOT, commit_receipt["authorization_sha256"], schemas={"vcs-action-authorization-v1"})
        commit_auth = strict_json_loads(commit_auth_path.read_bytes(), label=str(commit_auth_path))
        commit_chain = {
            "authorization_id": commit_auth["authorization_id"],
            "nonce": commit_auth["nonce"],
            "authorization": _record_ref(commit_auth_path),
            "claim": _record_ref(commit_claim_path),
            "action_receipt": _record_ref(commit_receipt_path),
            "result": "PASS",
        }
        push_chain = {
            "authorization_id": push_auth["authorization_id"],
            "nonce": push_auth["nonce"],
            "authorization": _record_ref(push_auth_path),
            "claim": _record_ref(push_claim_path),
            "action_receipt": _record_ref(path),
            "result": "PASS",
        }
        return {"commit": commit_chain, "push": push_chain, "expected_old_remote_oid": push_auth["expected_old_remote_oid"]}, push_auth["expected_old_remote_oid"]
    if schema != "daee-vcs-durability-action-receipt-v1":
        raise ValueError(f"unsupported push receipt schema {schema!r}")
    if push_receipt.get("action") != "push" or push_receipt.get("result") != "PASS":
        raise ValueError("legacy durability push receipt is not PASS")
    run_root = ROOT / RUN_REL
    push_claim_path = resolve_repo_path(ROOT, push_receipt["claim_path"], must_exist=True, expect_file=True)
    push_auth_path = _find_by_digest(run_root, push_receipt["authorization_sha256"], schemas={"daee-vcs-durability-authorization-v1"})
    push_auth = strict_json_loads(push_auth_path.read_bytes(), label=str(push_auth_path))
    commit_receipt_path = resolve_repo_path(ROOT, push_auth["commit_receipt_path"], must_exist=True, expect_file=True)
    commit_receipt = strict_json_loads(commit_receipt_path.read_bytes(), label=str(commit_receipt_path))
    commit_claim_path = resolve_repo_path(ROOT, commit_receipt["claim_path"], must_exist=True, expect_file=True)
    commit_auth_path = _find_legacy_authorization(run_root, commit_receipt["authorization_id"], "commit")
    commit_auth = strict_json_loads(commit_auth_path.read_bytes(), label=str(commit_auth_path))
    def legacy_chain(auth: dict[str, Any], auth_path: Path, claim_path: Path, receipt_path: Path) -> dict[str, Any]:
        authorization_id = auth["authorization_id"]
        return {
            "authorization_id": authorization_id,
            "nonce": f"legacy-no-nonce-{authorization_id}",
            "authorization": _record_ref(auth_path),
            "claim": _record_ref(claim_path),
            "action_receipt": _record_ref(receipt_path),
            "result": "PASS",
        }
    old = push_auth["expected_old_remote_oid"]
    return {
        "commit": legacy_chain(commit_auth, commit_auth_path, commit_claim_path, commit_receipt_path),
        "push": legacy_chain(push_auth, push_auth_path, push_claim_path, path),
        "expected_old_remote_oid": old,
    }, old


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _strict_predecessor_source(
    previous_sha: str,
    current_sha: str,
    *,
    is_ancestor: Callable[[str, str], bool] | None = None,
) -> Finding | None:
    if previous_sha == current_sha:
        return Finding(
            "receipt_custody",
            "predecessor-source-replay",
            "predecessor receipt source SHA is the current source SHA, not a strict predecessor",
        )
    if is_ancestor is None:
        for label, oid in (("predecessor", previous_sha), ("current", current_sha)):
            if _git_text(["cat-file", "-t", oid]) != "commit":
                return Finding("receipt_custody", "predecessor-source-object", f"{label} source {oid} is not a commit")
        completed = subprocess.run(
            ["git", "--no-replace-objects", "merge-base", "--is-ancestor", previous_sha, current_sha],
            cwd=ROOT,
            env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
            capture_output=True,
            check=False,
        )
        if completed.returncode not in (0, 1):
            raise ValueError(
                "predecessor source ancestry query failed: "
                + completed.stderr.decode("utf-8", "replace").strip()
            )
        ancestor = completed.returncode == 0
    else:
        ancestor = is_ancestor(previous_sha, current_sha)
    if not ancestor:
        return Finding(
            "receipt_custody",
            "predecessor-source-ancestry",
            f"predecessor receipt source {previous_sha} is not an ancestor of current source {current_sha}",
        )
    return None


def collect_live_observation(
    *,
    repository: str,
    remote: str,
    ref: str,
    source_sha: str,
    vcs: Mapping[str, Any],
    expected_old: str,
) -> dict[str, Any]:
    if repository != REPOSITORY or remote != "origin" or ref != REMOTE_REF:
        raise ValueError("repository/remote/ref differ from the frozen source binding")
    remote_url = _git_text(["remote", "get-url", remote])
    if _remote_repository(remote_url) != repository:
        raise ValueError("Git remote repository differs from requested owner/repo")
    _gh_auth()
    source, lineage, carriers, binding, joined = _source_and_carriers(source_sha, remote, ref, expected_old)
    deterministic_verdicts = _collect_deterministic_verdicts(source_sha, source["tree_oid"])
    workflow_local = joined["workflow"]
    _status, workflow_api = _gh_json(f"repos/{repository}/actions/workflows/ci.yml")
    if workflow_api.get("name") != WORKFLOW_NAME or workflow_api.get("path") != WORKFLOW_PATH:
        raise ValueError("GitHub workflow API identity drifted")
    query = urllib.parse.urlencode(
        {"branch": BRANCH, "event": "push", "status": "completed", "head_sha": source_sha, "per_page": 100}
    )
    _status, runs_payload = _gh_json(f"repos/{repository}/actions/workflows/{workflow_api['id']}/runs?{query}")
    runs = [row for row in runs_payload.get("workflow_runs", []) if row.get("head_sha") == source_sha and row.get("event") == "push"]
    if len(runs) != 1:
        raise ValueError(f"exact source SHA must have exactly one completed push workflow run, found {len(runs)}")
    run_row = runs[0]
    run_id = int(run_row["id"])
    attempt = int(run_row.get("run_attempt", 1))
    _status, run_api = _gh_json(f"repos/{repository}/actions/runs/{run_id}")
    if int(run_api.get("run_attempt", 0)) != attempt:
        raise ValueError("workflow run attempt drifted between list and exact readback")
    _status, jobs_payload = _gh_json(f"repos/{repository}/actions/runs/{run_id}/attempts/{attempt}/jobs?filter=all&per_page=100")
    jobs = [row for row in jobs_payload.get("jobs", []) if row.get("name") == JOB_NAME]
    if len(jobs) != 1:
        raise ValueError(f"exact run must have one runtime-checks job, found {len(jobs)}")
    job_api = jobs[0]
    check_run_url = str(job_api.get("check_run_url", ""))
    check_match = re.search(r"/check-runs/([0-9]+)$", check_run_url)
    if not check_match:
        raise ValueError("runtime-checks job lacks exact check-run URL")
    check_run_id = int(check_match.group(1))
    _status, check_api = _gh_json(f"repos/{repository}/check-runs/{check_run_id}")
    _status, checks_payload = _gh_json(f"repos/{repository}/commits/{source_sha}/check-runs?filter=latest&per_page=100")
    required_rows = [row for row in checks_payload.get("check_runs", []) if row.get("name") == JOB_NAME]
    if len(required_rows) != 1 or int(required_rows[0].get("id", 0)) != check_run_id:
        raise ValueError("exact source has missing or duplicate required CI / runtime-checks check-run")
    if check_api.get("name") != JOB_NAME:
        raise ValueError(f"raw required check-run name {check_api.get('name')} is not {JOB_NAME}")
    check_suite_id = int(check_api.get("check_suite", {}).get("id", 0))
    if check_suite_id <= 0 or int(run_api.get("check_suite_id", 0)) != check_suite_id:
        raise ValueError("workflow run and check-run check-suite IDs differ")
    branch_endpoint = f"repos/{repository}/branches/{urllib.parse.quote(BRANCH, safe='')}/protection/required_status_checks"
    protection_status, protection_api = _gh_json(branch_endpoint, allow_404=True)
    if protection_status == 404:
        protection = {
            "endpoint": branch_endpoint,
            "http_status": 404,
            "protected": False,
            "strict": None,
            "contexts": [],
            "checks": [],
            "matches_owner_required_set": None,
        }
    else:
        contexts = sorted(protection_api.get("contexts", []))
        checks = sorted(
            ({"context": row.get("context"), "app_id": row.get("app_id")} for row in protection_api.get("checks", [])),
            key=lambda row: (str(row["context"]), -1 if row["app_id"] is None else int(row["app_id"])),
        )
        normalized = sorted(set(contexts + [str(row["context"]) for row in checks]))
        if normalized != [CHECK_NAME]:
            raise ValueError(f"protected branch required check set {normalized} differs from owner-derived {[CHECK_NAME]}")
        protection = {
            "endpoint": branch_endpoint,
            "http_status": 200,
            "protected": True,
            "strict": bool(protection_api.get("strict")),
            "contexts": contexts,
            "checks": checks,
            "matches_owner_required_set": True,
        }
    app_api = check_api.get("app", {})
    app = {"id": int(app_api.get("id", 0)), "slug": app_api.get("slug"), "name": app_api.get("name")}
    if app != {"id": app["id"], "slug": "github-actions", "name": "GitHub Actions"} or app["id"] <= 0:
        raise ValueError(f"required check-run app identity drifted: {app}")
    protection_app_finding = _branch_protection_app(protection, app)
    if protection_app_finding:
        raise ValueError(protection_app_finding.message)
    run = {
        "id": run_id,
        "number": int(run_api["run_number"]),
        "attempt": attempt,
        "event": run_api.get("event"),
        "head_branch": run_api.get("head_branch"),
        "head_sha": run_api.get("head_sha"),
        "check_suite_id": check_suite_id,
        "status": run_api.get("status"),
        "conclusion": run_api.get("conclusion"),
        "created_at": run_api.get("created_at"),
        "updated_at": run_api.get("updated_at"),
        "html_url": run_api.get("html_url"),
        "api_url": run_api.get("url"),
    }
    steps = [
        {
            "number": int(row["number"]),
            "name": row["name"],
            "status": row["status"],
            "conclusion": row["conclusion"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
        }
        for row in job_api.get("steps", [])
    ]
    if len({row["number"] for row in steps}) != len(steps) or any(row["status"] != "completed" or row["conclusion"] != "success" for row in steps):
        raise ValueError("runtime-checks contains duplicate, incomplete, failed, or skipped steps")
    job = {
        "id": int(job_api["id"]),
        "name": job_api.get("name"),
        "check_name": CHECK_NAME,
        "raw_check_run_name": check_api.get("name"),
        "check_run_id": check_run_id,
        "check_suite_id": check_suite_id,
        "app": app,
        "runner": {
            "name": job_api.get("runner_name"),
            "group_name": job_api.get("runner_group_name") or "GitHub Actions",
            "labels": sorted(job_api.get("labels", [])),
        },
        "status": job_api.get("status"),
        "conclusion": job_api.get("conclusion"),
        "started_at": job_api.get("started_at"),
        "completed_at": job_api.get("completed_at"),
        "html_url": job_api.get("html_url"),
        "api_url": job_api.get("url"),
        "check_run_url": check_run_url,
        "steps": steps,
    }
    if job["status"] != "completed" or job["conclusion"] != "success" or "ubuntu-latest" not in job["runner"]["labels"]:
        raise ValueError("runtime-checks exact job is not successful on ubuntu-latest")
    required_result = {
        "name": CHECK_NAME,
        "raw_check_run_name": check_api.get("name"),
        "check_run_id": check_run_id,
        "check_suite_id": check_suite_id,
        "app": app,
        "status": check_api.get("status"),
        "conclusion": check_api.get("conclusion"),
        "started_at": check_api.get("started_at"),
        "completed_at": check_api.get("completed_at"),
        "details_url": check_api.get("details_url"),
        "api_url": check_api.get("url"),
    }
    required_checks = {
        "derivation_source": "consumed-push-authorization",
        "owner_required_set": [CHECK_NAME],
        "branch_protection": protection,
        "results": [required_result],
    }
    log_endpoint = f"repos/{repository}/actions/jobs/{job['id']}/logs"
    _status, log_raw = _gh(["api", "--method", "GET", log_endpoint], binary=True)
    segment, test_count, suite_status, skipped_count = _a01_log(log_raw)
    _status, artifacts_payload = _gh_json(f"repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100")
    all_artifacts = artifacts_payload.get("artifacts", [])
    if len(all_artifacts) != 1 or all_artifacts[0].get("name") != LINUX_ARTIFACT_NAME:
        raise ValueError("exact run artifact inventory must contain only Linux A01 evidence")
    artifact_api = all_artifacts[0]
    if artifact_api.get("expired") is not False:
        raise ValueError("exact run must retain one unexpired Linux A01 evidence artifact")
    artifact_id = int(artifact_api["id"])
    _status, artifact_zip_raw = _gh(["api", "--method", "GET", f"repos/{repository}/actions/artifacts/{artifact_id}/zip"], binary=True)
    evidence_raw, zip_sha = _artifact_zip(artifact_zip_raw)
    evidence = strict_json_loads(evidence_raw, label=f"artifact {artifact_id}/{LINUX_ARTIFACT_ENTRY}")
    if not isinstance(evidence, dict):
        raise ValueError("Linux A01 artifact evidence root is not an object")
    checker_blob, checker_raw = _git_object(source_sha, LINUX_CHECKER_PATH)
    test_blob, test_raw = _git_object(source_sha, LINUX_TEST_PATH)
    checker = {"path": LINUX_CHECKER_PATH, "blob_oid": checker_blob, "raw_sha256": sha256_bytes(checker_raw)}
    contract_test = {"path": LINUX_TEST_PATH, "blob_oid": test_blob, "raw_sha256": sha256_bytes(test_raw)}
    expected_evidence = {
        "source_sha": source_sha,
        "run_id": run_id,
        "run_number": run["number"],
        "run_attempt": attempt,
        "job_name": JOB_NAME,
        "runner_os": "Linux",
        "runner_label": "ubuntu-latest",
        "step_name": LINUX_STEP_NAME,
        "command": LINUX_COMMAND,
        "checker": checker,
        "contract_test": contract_test,
        "suite_marker": LINUX_TEST_PATH,
        "suite_test_count": test_count,
        "suite_status": suite_status,
        "skipped_count": skipped_count,
        "substituted": False,
        "native_linux": True,
        "candidate_claim": False,
        "terminal_claim": False,
    }
    for field, expected in expected_evidence.items():
        if evidence.get(field) != expected:
            raise ValueError(f"Linux A01 artifact {field} differs from exact source/run/log join")
    named = [row for row in steps if row["name"] == LINUX_STEP_NAME]
    if len(named) != 1:
        raise ValueError("exact job lacks one named Linux A01 custody self-test step")
    artifact = {
        "name": LINUX_ARTIFACT_NAME,
        "id": artifact_id,
        "size_in_bytes": int(artifact_api["size_in_bytes"]),
        "expired": False,
        "created_at": artifact_api["created_at"],
        "expires_at": artifact_api["expires_at"],
        "api_url": artifact_api["url"],
        "archive_download_url": artifact_api["archive_download_url"],
        "zip_sha256": zip_sha,
        "entry_path": LINUX_ARTIFACT_ENTRY,
        "entry_byte_count": len(evidence_raw),
        "entry_sha256": sha256_bytes(evidence_raw),
    }
    linux = {
        "source_sha": source_sha,
        "run_id": run_id,
        "job_id": job["id"],
        "check_run_id": check_run_id,
        "runner_label": "ubuntu-latest",
        "step": named[0],
        "command": LINUX_COMMAND,
        "checker": checker,
        "contract_test": contract_test,
        "suite_marker": LINUX_TEST_PATH,
        "suite_test_count": test_count,
        "suite_status": suite_status,
        "skipped_count": skipped_count,
        "substituted": False,
        "artifact": artifact,
        "evidence": evidence,
        "job_log_sha256": sha256_bytes(log_raw),
        "log_segment_sha256": sha256_bytes(segment),
    }
    workflow = {
        "id": int(workflow_api["id"]),
        "name": workflow_api["name"],
        "path": workflow_api["path"],
        "blob_oid": workflow_local["blob_oid"],
        "raw_sha256": workflow_local["raw_sha256"],
        "html_url": workflow_api["html_url"],
    }
    observation = {
        "provider": "github-actions",
        "repository": {"full_name": repository, "remote_url": remote_url, "remote_name": remote, "branch": BRANCH, "ref": ref},
        "source": source,
        "lineage": lineage,
        "source_binding": binding,
        "carriers": carriers,
        "migration_carrier": joined["migration"],
        "carrier_binding_digest": {"algorithm": "sha256-canonical-json-carrier-binding-v1", "sha256": _carrier_binding_digest(binding, carriers)},
        "deterministic_verdicts": deterministic_verdicts,
        "vcs": copy.deepcopy(vcs),
        "workflow": workflow,
        "run": run,
        "required_checks": required_checks,
        "job": job,
        "job_log": {"download_endpoint": log_endpoint, "byte_count": len(log_raw), "sha256": sha256_bytes(log_raw)},
        "artifact_inventory": [artifact],
        "linux_a01": linux,
    }
    return observation


def _predecessor() -> tuple[str | None, dict[str, Any], int]:
    RECEIPT_ROOT.mkdir(parents=True, exist_ok=True)
    head = read_cas_pointer(RECEIPT_ROOT)
    digest = head["last_record_sha256"]
    if digest is None:
        return None, {"kind": "genesis", "receipt_path": None, "receipt_sha256": None}, 1
    matches = [row for row in iter_immutable_records(RECEIPT_ROOT) if row[2] == digest]
    if len(matches) != 1:
        raise ValueError(f"receipt custody head digest has {len(matches)} matching immutable records")
    path = matches[0][0]
    previous = strict_json_loads(path.read_bytes(), label=str(path))
    if not isinstance(previous, Mapping) or not isinstance(previous.get("source"), Mapping):
        raise ValueError("predecessor receipt lacks a source object")
    previous_sha = previous["source"].get("commit_sha")
    if not isinstance(previous_sha, str):
        raise ValueError("predecessor receipt lacks source.commit_sha")
    return (
        digest,
        {
            "kind": "receipt",
            "receipt_path": path.relative_to(ROOT).as_posix(),
            "receipt_sha256": digest,
            "source_commit_sha": previous_sha,
        },
        head["sequence"] + 1,
    )


def build_receipt(observation: Mapping[str, Any], *, out: Path) -> dict[str, Any]:
    source_sha = observation["source"]["commit_sha"]
    expected = (RECEIPT_REL / f"{source_sha}.json").as_posix()
    RECEIPT_ROOT.mkdir(parents=True, exist_ok=True)
    requested = out if out.is_absolute() else ROOT / out
    resolved = resolve_contained_path(RECEIPT_ROOT, requested)
    expected_path = (ROOT / expected).resolve()
    if resolved != expected_path:
        raise CustodyError(f"--out must equal commit-keyed locator {expected}", subcode="locator-mismatch")
    predecessor_digest, predecessor, sequence = _predecessor()
    if predecessor["kind"] == "receipt":
        predecessor_finding = _strict_predecessor_source(predecessor["source_commit_sha"], source_sha)
        if predecessor_finding:
            raise ValueError(
                f"[{predecessor_finding.failure_class}/{predecessor_finding.failure_subcode}] "
                f"{predecessor_finding.message}"
            )
    value = copy.deepcopy(dict(observation))
    value.update(
        {
            "schema": "daee-source-commit-receipt-v1",
            "receipt_id": _receipt_id(source_sha, value["run"]["id"], value["run"]["attempt"]),
            "status": "EXACT_SHA_CI_GREEN",
            "predecessor_record_sha256": predecessor_digest,
            "predecessor_receipt": predecessor,
            "custody_sequence": sequence,
            "receipt_locator": expected,
            "observed_at": _now(),
            "candidate_boundary": "exact-source-and-ci-proof-only-not-candidate-maturity",
            "non_claims": NON_CLAIMS,
            "terminal_claim": False,
        }
    )
    findings = validate_receipt(value, live_observation=observation)
    if findings:
        first = findings[0]
        raise ValueError(f"generated receipt failed [{first.failure_class}/{first.failure_subcode}]: {first.message}")
    append_claim_before_cas(
        RECEIPT_ROOT,
        resolved,
        value,
        expected_predecessor_sha256=predecessor_digest,
    )
    raw = resolved.read_bytes()
    if raw != canonical_json_bytes(value):
        raise CustodyError("receipt canonical JSON readback drifted", subcode="readback-drift")
    head = read_cas_pointer(RECEIPT_ROOT)
    if head["last_record_sha256"] != sha256_bytes(raw) or head["sequence"] != sequence:
        raise CustodyError("receipt CAS head readback drifted", subcode="pointer-readback")
    return value


def _validate_published(path: Path, value: Mapping[str, Any], raw: bytes) -> Finding | None:
    if raw != canonical_json_bytes(value):
        return Finding("receipt_custody", "noncanonical-json", "published receipt is not canonical final-LF JSON")
    try:
        expected = resolve_repo_path(ROOT, value["receipt_locator"], must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        return Finding("receipt_custody", exc.subcode, f"published receipt path rejected: {exc}")
    if path.resolve() != expected.resolve():
        return Finding("receipt_custody", "locator-mismatch", "published receipt path differs from receipt_locator")
    head = read_cas_pointer(RECEIPT_ROOT)
    digest = sha256_bytes(raw)
    if head["last_record_sha256"] != digest or head["sequence"] != value["custody_sequence"]:
        return Finding("receipt_custody", "predecessor-mismatch", "receipt is not the current exact CAS custody head")
    predecessor = value["predecessor_receipt"]
    if predecessor["kind"] == "receipt":
        try:
            previous = resolve_repo_path(ROOT, predecessor["receipt_path"], must_exist=True, expect_file=True)
        except PathCustodyError as exc:
            return Finding("receipt_custody", exc.subcode, f"predecessor receipt path rejected: {exc}")
        previous_raw = previous.read_bytes()
        if sha256_bytes(previous_raw) != predecessor["receipt_sha256"]:
            return Finding("receipt_custody", "predecessor-hash", "predecessor receipt raw SHA-256 drifted")
        try:
            previous_value = strict_json_loads(previous_raw, label=str(previous))
        except (DuplicateObjectKey, ValueError) as exc:
            return Finding("receipt_custody", "predecessor-read", f"predecessor receipt JSON failed: {exc}")
        previous_source = previous_value.get("source", {}) if isinstance(previous_value, Mapping) else {}
        if previous_source.get("commit_sha") != predecessor.get("source_commit_sha"):
            return Finding(
                "receipt_custody",
                "predecessor-source",
                "predecessor receipt source SHA differs from predecessor_receipt source_commit_sha",
            )
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true", help="run offline fixture and custody tests")
    mode.add_argument("--build", action="store_true", help="query Git/GitHub and create-once publish the exact receipt")
    mode.add_argument("--receipt", type=Path, help="validate one already-published receipt")
    parser.add_argument("--repository")
    parser.add_argument("--remote")
    parser.add_argument("--ref")
    parser.add_argument("--sha")
    parser.add_argument("--push-receipt", type=Path)
    parser.add_argument("--source-binding", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--require-status")
    parser.add_argument("--verify-live", action="store_true")
    parser.add_argument("--explain", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        if any(
            value not in (None, False)
            for value in (
                args.repository,
                args.remote,
                args.ref,
                args.sha,
                args.push_receipt,
                args.source_binding,
                args.out,
                args.require_status,
                args.verify_live,
            )
        ):
            parser.error("--self-test cannot be combined with build/live/receipt arguments")
        problems, valid_count, invalid_count = self_test()
        if problems:
            for problem in problems:
                print(f"FAIL: {problem}")
            print(f"ci readback self-test: FAIL ({len(problems)} problem(s))")
            return 1
        print(f"ci readback self-test: PASS ({valid_count} valid / {invalid_count} invalid; no external evidence written)")
        return 0
    if args.build:
        required = {
            "--repository": args.repository,
            "--remote": args.remote,
            "--ref": args.ref,
            "--sha": args.sha,
            "--push-receipt": args.push_receipt,
            "--source-binding": args.source_binding,
            "--out": args.out,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            parser.error(f"--build requires {', '.join(missing)}")
        if args.require_status is not None or args.verify_live:
            parser.error("--build cannot be combined with receipt validation flags")
        if args.source_binding.as_posix() != CARRIER_PATHS[0]:
            parser.error(f"--source-binding must be canonical carrier {CARRIER_PATHS[0]}")
        if re.fullmatch(r"[0-9a-f]{40}", args.sha) is None:
            parser.error("--sha must be a full lowercase Git OID")
        try:
            vcs, expected_old = _vcs_from_push_receipt(args.push_receipt)
            observation = collect_live_observation(
                repository=args.repository,
                remote=args.remote,
                ref=args.ref,
                source_sha=args.sha,
                vcs=vcs,
                expected_old=expected_old,
            )
            value = build_receipt(observation, out=args.out)
        except (CustodyError, OSError, PathCustodyError, ValueError) as exc:
            finding = Finding("live_readback", getattr(exc, "subcode", "live-build"), str(exc))
            print(json.dumps(diagnostic(finding, str(args.out)), sort_keys=True) if args.explain else f"ci readback build: FAIL [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
            return 1
        print(json.dumps(value, sort_keys=True) if args.explain else f"EXACT_SHA_CI_GREEN {value['receipt_locator']}")
        return 0
    if any(value is not None for value in (args.repository, args.remote, args.ref, args.sha, args.push_receipt, args.source_binding, args.out)):
        parser.error("build-only arguments cannot be used with --receipt")
    if (args.require_status is None) == (not args.verify_live):
        parser.error("--receipt requires exactly one of --require-status or --verify-live")
    value, raw, finding = _load_raw(args.receipt)
    if finding or value is None:
        assert finding is not None
        print(json.dumps(diagnostic(finding, str(args.receipt)), sort_keys=True) if args.explain else f"ci readback: FAIL [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
        return 1
    findings = validate_receipt(value)
    if not findings:
        custody = _validate_published(args.receipt, value, raw)
        if custody:
            findings = [custody]
    if not findings and args.require_status is not None and args.require_status != "EXACT_SHA_CI_GREEN":
        findings = [Finding("receipt_status", "required-status", f"unsupported required status {args.require_status}")]
    if not findings and args.verify_live:
        try:
            predecessor = value["predecessor_receipt"]
            if predecessor["kind"] == "receipt":
                predecessor_finding = _strict_predecessor_source(
                    predecessor["source_commit_sha"], value["source"]["commit_sha"]
                )
                if predecessor_finding:
                    findings = [predecessor_finding]
            if not findings:
                observation = collect_live_observation(
                    repository=value["repository"]["full_name"],
                    remote=value["repository"]["remote_name"],
                    ref=value["repository"]["ref"],
                    source_sha=value["source"]["commit_sha"],
                    vcs=value["vcs"],
                    expected_old=value["vcs"]["expected_old_remote_oid"],
                )
                findings = validate_receipt(value, live_observation=observation)
        except (OSError, ValueError) as exc:
            findings = [Finding("live_readback", "verify-live", str(exc))]
    if findings:
        first = findings[0]
        print(json.dumps(diagnostic(first, str(args.receipt)), sort_keys=True) if args.explain else f"ci readback: FAIL [{first.failure_class}/{first.failure_subcode}]: {first.message}")
        return 1
    if args.verify_live:
        print("EXACT_SHA_CI_GREEN")
    else:
        print("RECEIPT_STRUCTURALLY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
