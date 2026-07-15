#!/usr/bin/env python3
"""Create-once Task 7 source freezes and deterministic verdict evidence."""
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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from unittest import mock

from a16_immutable_custody import CustodyError, canonical_json_bytes, claim_json_once, strict_snapshot
from contract_validation import PathCustodyError, resolve_repo_path, validate_schema_subset
from run_local_ci import (
    OwnedCommandResult,
    PYTHON_EXECUTION_PROFILE_ID,
    command_list_sha256,
    execution_argv_for,
    execution_environment_for,
    execution_profile_for,
    execution_plan_sha256,
    parse_completion_stdout,
    run_owned_command,
)
from run_no_model_preflight import (
    A16_GATE_COMMANDS,
    EXPECTED_GATE_COUNT,
    EXPECTED_GATE_RETURN_CODES,
    GATES as NO_MODEL_GATES,
)
from source_provenance import DuplicateObjectKey, strict_json_loads


ROOT = Path(__file__).resolve().parents[1]
RUN_REL = Path(".IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5")
SCHEMA_PATH = ROOT / "schema/ci-readback.schema.json"
NAMESPACE_SCHEMA_PATH = ROOT / "schema/task7-deterministic-evidence-namespace.schema.json"
LEGACY_NAMESPACE_ID = "branch10-v1"
DEFAULT_NAMESPACE_ID = "branch11-v1"


@dataclass(frozen=True)
class EvidenceNamespace:
    namespace_id: str
    namespace_version: int
    generation: str
    branch: str
    ref: str
    evidence_rel: Path
    source_freeze_schema: str
    source_freeze_definition: str
    record_namespace_flag: bool

    @property
    def evidence_root(self) -> Path:
        return ROOT / self.evidence_rel

    @property
    def source_freeze_rel(self) -> Path:
        return self.evidence_rel / "source-freeze.json"

    @property
    def whole_branch_review_rel(self) -> Path:
        suffix = "" if self.namespace_id == LEGACY_NAMESPACE_ID else f"-{self.namespace_id}"
        return RUN_REL / f"reviews/task7-independent-whole-branch-review{suffix}.json"


_LEGACY_BRANCH = "codex/v0.4.6.0-runtime-footprint-b10"
_BRANCH11 = "codex/v0.4.6.0-runtime-footprint-b11"
EVIDENCE_NAMESPACES = {
    LEGACY_NAMESPACE_ID: EvidenceNamespace(
        namespace_id=LEGACY_NAMESPACE_ID,
        namespace_version=1,
        generation="branch10",
        branch=_LEGACY_BRANCH,
        ref=f"refs/heads/{_LEGACY_BRANCH}",
        evidence_rel=RUN_REL / "evidence/deterministic-verdicts",
        source_freeze_schema="daee-task7-precommit-source-freeze-v1",
        source_freeze_definition="task7_source_freeze_v1_legacy",
        record_namespace_flag=False,
    ),
    DEFAULT_NAMESPACE_ID: EvidenceNamespace(
        namespace_id=DEFAULT_NAMESPACE_ID,
        namespace_version=1,
        generation="branch11",
        branch=_BRANCH11,
        ref=f"refs/heads/{_BRANCH11}",
        evidence_rel=RUN_REL / "evidence/deterministic-verdicts-b11-v1",
        source_freeze_schema="daee-task7-precommit-source-freeze-v2",
        source_freeze_definition="task7_source_freeze_v2",
        record_namespace_flag=True,
    ),
}


def namespace_contract(namespace_id: str) -> EvidenceNamespace:
    try:
        return EVIDENCE_NAMESPACES[namespace_id]
    except KeyError as exc:
        allowed = ", ".join(sorted(EVIDENCE_NAMESPACES))
        raise ValueError(f"unsupported Task 7 evidence namespace {namespace_id!r}; allowed: {allowed}") from exc


_DEFAULT_NAMESPACE = namespace_contract(DEFAULT_NAMESPACE_ID)
EVIDENCE_REL = _DEFAULT_NAMESPACE.evidence_rel
EVIDENCE_ROOT = _DEFAULT_NAMESPACE.evidence_root
BRANCH = _DEFAULT_NAMESPACE.branch
REF = _DEFAULT_NAMESPACE.ref
STATUS_BY_KIND = {
    "no-model-preflight": "PASS",
    "full-local-ci": "PASS",
    "generated-freshness-package": "PASS",
    "independent-whole-branch-review": "ACCEPT",
}
ROLE_FILE_BY_KIND = {
    "no-model-preflight": "no-model-preflight.json",
    "full-local-ci": "full-local-ci.json",
    "generated-freshness-package": "generated-freshness-package.json",
    "independent-whole-branch-review": "independent-whole-branch-review.json",
}
PRODUCER_PATH = "tools/write_task7_deterministic_evidence.py"
SOURCE_FREEZE_REL = EVIDENCE_REL / "source-freeze.json"
REPORT_REL_BY_KIND = {
    kind: EVIDENCE_REL / "reports" / f"{kind}.json" for kind in STATUS_BY_KIND
}
LOG_REL_BY_KIND = {
    kind: EVIDENCE_REL / "logs" / f"{kind}.json" for kind in STATUS_BY_KIND
}
NO_MODEL_NATIVE_REPORT_REL = EVIDENCE_REL / "native/no-model-preflight.json"
FULL_LOCAL_CI_NATIVE_REPORT_REL = EVIDENCE_REL / "native/full-local-ci.json"
WHOLE_BRANCH_REVIEW_REL = _DEFAULT_NAMESPACE.whole_branch_review_rel
REVIEW_AUTHORIZATION_REL = EVIDENCE_REL / "authorizations/independent-reviewer.json"
IMPLEMENTATION_OWNER_IDENTITY = "/root/task3b_ci_receipt"
REVIEW_AUTHORIZATION_ISSUER = "/root"
ROLE_CHECKS = {
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
        ["python", "tools/run_no_model_preflight.py", "--json", NO_MODEL_NATIVE_REPORT_REL.as_posix()]
    ],
    "full-local-ci": [[
        "python",
        "tools/run_local_ci.py",
        "--strict-pwsh",
        "--command-timeout-seconds",
        "900",
        "--json",
        FULL_LOCAL_CI_NATIVE_REPORT_REL.as_posix(),
    ]],
    "independent-whole-branch-review": [],
}


def report_rel(kind: str, namespace_id: str = DEFAULT_NAMESPACE_ID) -> Path:
    return namespace_contract(namespace_id).evidence_rel / "reports" / f"{kind}.json"


def log_rel(kind: str, namespace_id: str = DEFAULT_NAMESPACE_ID) -> Path:
    return namespace_contract(namespace_id).evidence_rel / "logs" / f"{kind}.json"


def native_report_rel(kind: str, namespace_id: str = DEFAULT_NAMESPACE_ID) -> Path:
    if kind not in {"no-model-preflight", "full-local-ci"}:
        raise ValueError(f"Task 7 {kind} has no native report")
    return namespace_contract(namespace_id).evidence_rel / "native" / f"{kind}.json"


def review_authorization_rel(namespace_id: str = DEFAULT_NAMESPACE_ID) -> Path:
    return namespace_contract(namespace_id).evidence_rel / "authorizations/independent-reviewer.json"


def role_checks(kind: str, namespace_id: str = DEFAULT_NAMESPACE_ID) -> list[list[str]]:
    if kind not in STATUS_BY_KIND:
        raise ValueError(f"unsupported Task 7 verdict kind {kind!r}")
    if namespace_id == DEFAULT_NAMESPACE_ID:
        return [list(command) for command in ROLE_CHECKS[kind]]
    if kind == "no-model-preflight":
        return [["python", "tools/run_no_model_preflight.py", "--json", native_report_rel(kind, namespace_id).as_posix()]]
    if kind == "full-local-ci":
        return [[
            "python",
            "tools/run_local_ci.py",
            "--strict-pwsh",
            "--command-timeout-seconds",
            "900",
            "--json",
            native_report_rel(kind, namespace_id).as_posix(),
        ]]
    return [list(command) for command in ROLE_CHECKS[kind]]
NON_CLAIMS = [
    "does-not-claim-final-source-commit",
    "does-not-claim-exact-sha-ci",
    "does-not-authorize-model-or-candidate",
]
TASK_IDENTITY_RE = re.compile(r"^/root(?:/[a-z0-9][a-z0-9_-]{0,63})*$")
TASK7_ROLE_OUTER_TIMEOUT_SECONDS = 7200


class Task7RoleTimeout(ValueError):
    def __init__(self, kind: str, command: Sequence[str], timeout_seconds: int | float) -> None:
        self.returncode = 124
        super().__init__(
            f"Task 7 {kind} check {list(command)!r} timed out after "
            f"{timeout_seconds}s with exit 124; owned process tree terminated"
        )


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _schema() -> dict[str, Any]:
    value = strict_json_loads(SCHEMA_PATH.read_bytes(), label=str(SCHEMA_PATH))
    if not isinstance(value, dict) or not isinstance(value.get("$defs"), dict):
        raise ValueError("ci-readback schema definitions are unavailable")
    return value


def _schema_ref(name: str) -> dict[str, Any]:
    schema = _schema()
    return {"$defs": schema["$defs"], "$ref": f"#/$defs/{name}"}


def _namespace_schema() -> dict[str, Any]:
    value = strict_json_loads(NAMESPACE_SCHEMA_PATH.read_bytes(), label=str(NAMESPACE_SCHEMA_PATH))
    if not isinstance(value, dict) or not isinstance(value.get("$defs"), dict):
        raise ValueError("Task 7 evidence-namespace schema definitions are unavailable")
    return value


def _namespace_schema_ref(name: str) -> dict[str, Any]:
    schema = _namespace_schema()
    return {"$defs": schema["$defs"], "$ref": f"#/$defs/{name}"}


def _validate(value: Mapping[str, Any], definition: str, *, label: str) -> None:
    issues = validate_schema_subset(value, _schema_ref(definition))
    if issues:
        first = issues[0]
        raise ValueError(f"{label} violates {definition} at {first.path}: {first.message}")


def _validate_namespace(value: Mapping[str, Any], definition: str, *, label: str) -> None:
    issues = validate_schema_subset(value, _namespace_schema_ref(definition))
    if issues:
        first = issues[0]
        raise ValueError(f"{label} violates {definition} at {first.path}: {first.message}")


def _git(arguments: Sequence[str], *, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=ROOT,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
        capture_output=True,
        text=not binary,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", "replace") if binary else completed.stderr
        raise ValueError(f"git {' '.join(arguments)} failed: {stderr.strip()}")
    return completed.stdout


def _files_digest(files: Sequence[Mapping[str, Any]]) -> str:
    return _sha(canonical_json_bytes(list(files)))


def _freeze_id(tree_oid: str, files_sha256: str, namespace_id: str = DEFAULT_NAMESPACE_ID) -> str:
    contract = namespace_contract(namespace_id)
    if namespace_id == LEGACY_NAMESPACE_ID:
        return _sha(
            b"daee-task7-precommit-source-freeze-v1\0"
            + tree_oid.encode("ascii")
            + b"\0"
            + files_sha256.encode("ascii")
        )
    return _sha(
        b"daee-task7-precommit-source-freeze-v2\0"
        + contract.namespace_id.encode("ascii")
        + b"\0"
        + str(contract.namespace_version).encode("ascii")
        + b"\0"
        + contract.generation.encode("ascii")
        + b"\0"
        + contract.evidence_rel.as_posix().encode("utf-8")
        + b"\0"
        + contract.branch.encode("utf-8")
        + b"\0"
        + contract.ref.encode("utf-8")
        + b"\0"
        + tree_oid.encode("ascii")
        + b"\0"
        + files_sha256.encode("ascii")
    )


def _command_digest(command: Sequence[str]) -> str:
    return _sha(canonical_json_bytes(list(command)))


def producer_command(kind: str, namespace_id: str = DEFAULT_NAMESPACE_ID) -> list[str]:
    if kind not in STATUS_BY_KIND:
        raise ValueError(f"unsupported Task 7 verdict kind {kind!r}")
    contract = namespace_contract(namespace_id)
    command = [
        "python",
        PRODUCER_PATH,
        "--build-verdict",
    ]
    if contract.record_namespace_flag:
        command.extend(["--evidence-namespace", namespace_id])
    command.extend([
        "--kind",
        kind,
        "--source-freeze",
        contract.source_freeze_rel.as_posix(),
        "--out",
        (contract.evidence_rel / ROLE_FILE_BY_KIND[kind]).as_posix(),
    ])
    return command


def validate_role_command(
    command: Sequence[str],
    kind: str,
    checker: str,
    *,
    namespace_id: str = DEFAULT_NAMESPACE_ID,
) -> None:
    if checker != PRODUCER_PATH or list(command) != producer_command(kind, namespace_id):
        raise ValueError(f"Task 7 {kind} must use its exact source-bound producer command")


def _evidence_id(
    kind: str,
    freeze_id: str,
    command_sha256: str,
    report_sha256: str,
    log_sha256: str,
) -> str:
    return _sha(
        b"daee-task7-deterministic-evidence-v1\0"
        + kind.encode("utf-8")
        + b"\0"
        + freeze_id.encode("ascii")
        + b"\0"
        + command_sha256.encode("ascii")
        + b"\0"
        + report_sha256.encode("ascii")
        + b"\0"
        + log_sha256.encode("ascii")
    )


def _artifact_ref(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "byte_count": len(raw),
        "sha256": _sha(raw),
    }


def _git_blob_oid(raw: bytes) -> str:
    payload = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    try:
        digest = hashlib.sha1(payload, usedforsecurity=False)
    except TypeError:  # pragma: no cover - older Python compatibility
        digest = hashlib.sha1(payload)
    return digest.hexdigest()


def _review_manifest(freeze: Mapping[str, Any]) -> dict[str, Any]:
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
        "aggregate_sha256": _sha(lines),
    }


def _review_id(value: Mapping[str, Any]) -> str:
    body = {key: value[key] for key in value if key != "review_id"}
    return _sha(b"daee-task7-whole-branch-review-v1\0" + canonical_json_bytes(body))


def _review_authorization_id(value: Mapping[str, Any]) -> str:
    body = {key: value[key] for key in value if key != "authorization_id"}
    return _sha(b"daee-task7-independent-review-authorization-v1\0" + canonical_json_bytes(body))


def _canonical_task_identity(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or TASK_IDENTITY_RE.fullmatch(value) is None:
        raise ValueError(f"Task 7 {field} must be one canonical lowercase agent task identity")
    return value


def validate_review_authorization(value: Mapping[str, Any], freeze: Mapping[str, Any]) -> None:
    reviewer = _canonical_task_identity(value.get("reviewer_identity"), field="authorized reviewer")
    _validate(value, "task7_review_authorization", label="Task 7 independent reviewer authorization")
    if value["issuer_identity"] != REVIEW_AUTHORIZATION_ISSUER:
        raise ValueError("Task 7 reviewer authorization issuer is not the exact external owner")
    if value["implementation_owner_identity"] != IMPLEMENTATION_OWNER_IDENTITY:
        raise ValueError("Task 7 reviewer authorization does not bind the exact implementation owner")
    if reviewer in {IMPLEMENTATION_OWNER_IDENTITY, REVIEW_AUTHORIZATION_ISSUER}:
        raise ValueError("Task 7 authorized reviewer must be distinct from owner and issuer")
    if value["expected_final_tree_oid"] != freeze["expected_final_tree_oid"]:
        raise ValueError("Task 7 reviewer authorization targets another tree")
    if value["source_freeze_id"] != freeze["freeze_id"]:
        raise ValueError("Task 7 reviewer authorization targets another source freeze")
    if value["authorization_id"] != _review_authorization_id(value):
        raise ValueError("Task 7 reviewer authorization_id drifted")


def validate_whole_branch_review(
    value: Mapping[str, Any],
    freeze: Mapping[str, Any],
    authorization: Mapping[str, Any],
    authorization_ref: Mapping[str, Any],
) -> None:
    reviewer = _canonical_task_identity(value.get("reviewer"), field="reviewer")
    owner = _canonical_task_identity(value.get("owner_identity"), field="owner_identity")
    _validate(value, "task7_whole_branch_review", label="Task 7 independent whole-branch review")
    validate_review_authorization(authorization, freeze)
    if owner != IMPLEMENTATION_OWNER_IDENTITY:
        raise ValueError("Task 7 whole-branch review does not bind the exact implementation owner")
    if reviewer != authorization["reviewer_identity"]:
        raise ValueError("Task 7 whole-branch reviewer differs from its owner-issued authorization")
    if value["review_authorization_id"] != authorization["authorization_id"]:
        raise ValueError("Task 7 whole-branch review authorization_id drifted")
    if value["review_authorization"] != dict(authorization_ref):
        raise ValueError("Task 7 whole-branch review authorization artifact binding drifted")
    if reviewer == owner:
        raise ValueError("Task 7 whole-branch reviewer must differ from the implementation owner")
    if value["reviewed_tree_oid"] != freeze["expected_final_tree_oid"]:
        raise ValueError("Task 7 whole-branch review targets another tree")
    if value["source_freeze_id"] != freeze["freeze_id"]:
        raise ValueError("Task 7 whole-branch review targets another source freeze")
    if value["manifest"] != _review_manifest(freeze):
        raise ValueError("Task 7 whole-branch review manifest differs from the complete source freeze")
    if value["review_id"] != _review_id(value):
        raise ValueError("Task 7 whole-branch review review_id drifted")
    authorization_time = datetime.strptime(authorization["issued_at"], "%Y-%m-%dT%H:%M:%SZ")
    review_time = datetime.strptime(value["reviewed_at"], "%Y-%m-%dT%H:%M:%SZ")
    if authorization_time > review_time:
        raise ValueError("Task 7 reviewer authorization postdates the completed review")


def _report_id(value: Mapping[str, Any]) -> str:
    body = {key: value[key] for key in value if key != "report_id"}
    return _sha(b"daee-task7-result-report-v2\0" + canonical_json_bytes(body))


def _command_result(sequence: int, command: Sequence[str], stdout: bytes, stderr: bytes) -> dict[str, Any]:
    value: dict[str, Any] = {
        "sequence": sequence,
        "command": list(command),
        "command_sha256": _command_digest(command),
        "execution_profile": execution_profile_for(command),
        "exit_code": 0,
        "stdout_byte_count": len(stdout),
        "stdout_sha256": _sha(stdout),
        "stderr_byte_count": len(stderr),
        "stderr_sha256": _sha(stderr),
    }
    if list(command) == ROLE_CHECKS["full-local-ci"][0]:
        completion = parse_completion_stdout(stdout)
        expected_count = completion["command_count"]
        if (
            completion.get("executed_count") != expected_count
            or completion.get("start_at_command") != 1
            or completion.get("end_at_command") != expected_count
            or completion.get("strict_pwsh") is not True
            or completion.get("command_timeout_seconds") != 900
        ):
            raise ValueError("full local-CI completion execution boundary drifted")
        value["completion"] = completion
    return value


def build_command_log(
    kind: str, results: Sequence[tuple[Sequence[str], bytes, bytes]]
) -> dict[str, Any]:
    value = {
        "schema": "daee-task7-command-log-v1",
        "kind": kind,
        "entries": [
            {
                "sequence": sequence,
                "command": list(command),
                "execution_profile": execution_profile_for(command),
                "exit_code": 0,
                "stdout_base64": base64.b64encode(stdout).decode("ascii"),
                "stderr_base64": base64.b64encode(stderr).decode("ascii"),
            }
            for sequence, (command, stdout, stderr) in enumerate(results, 1)
        ],
        "complete": True,
        "model_calls": 0,
        "terminal_claim": False,
    }
    _validate(value, "task7_command_log", label="Task 7 command log")
    return value


def build_result_report(
    *,
    kind: str,
    results: Sequence[tuple[Sequence[str], bytes, bytes]],
    evidence_artifacts: Sequence[Mapping[str, Any]],
    producer: Mapping[str, Any],
    freeze: Mapping[str, Any],
    observed_at: str,
    namespace_id: str = DEFAULT_NAMESPACE_ID,
) -> dict[str, Any]:
    command = producer_command(kind, namespace_id)
    value = {
        "schema": "daee-task7-result-report-v2",
        "report_id": "0" * 64,
        "kind": kind,
        "status": STATUS_BY_KIND[kind],
        "producer_command": command,
        "producer_command_sha256": _command_digest(command),
        "producer_execution_profile": execution_profile_for(command),
        "producer": dict(producer),
        "executed_checks": [
            _command_result(sequence, check, stdout, stderr)
            for sequence, (check, stdout, stderr) in enumerate(results, 1)
        ],
        "check_count": len(results),
        "evidence_artifacts": [dict(row) for row in evidence_artifacts],
        "source_freeze_id": freeze["freeze_id"],
        "expected_final_tree_oid": freeze["expected_final_tree_oid"],
        "observed_at": observed_at,
        "model_calls": 0,
        "candidate_claim": False,
        "terminal_claim": False,
        "non_claims": NON_CLAIMS,
    }
    value["report_id"] = _report_id(value)
    _validate(value, "task7_result_report", label="Task 7 result report")
    return value


def _load_json(path: Path, *, definition: str, label: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = strict_json_loads(raw, label=str(path))
    except DuplicateObjectKey as exc:
        raise ValueError(f"{label} duplicate key rejected: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} root must be an object")
    _validate(value, definition, label=label)
    return value, raw


def _load_source_freeze(path: Path, namespace_id: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = strict_json_loads(raw, label=str(path))
    except DuplicateObjectKey as exc:
        raise ValueError(f"Task 7 source freeze duplicate key rejected: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("Task 7 source freeze root must be an object")
    validate_source_freeze(value, namespace_id)
    return value, raw


def validate_source_freeze(
    value: Mapping[str, Any],
    namespace_id: str = DEFAULT_NAMESPACE_ID,
) -> None:
    contract = namespace_contract(namespace_id)
    _validate_namespace(
        value,
        contract.source_freeze_definition,
        label=f"Task 7 {namespace_id} source freeze",
    )
    if value["branch"] != contract.branch or value["ref"] != contract.ref:
        raise ValueError(f"Task 7 {namespace_id} source freeze branch/ref binding drifted")
    files = value["files"]
    paths = [row["path"] for row in files]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValueError("Task 7 source freeze paths must be unique and sorted")
    if value["file_count"] != len(files):
        raise ValueError("Task 7 source freeze file_count differs from files")
    files_digest = _files_digest(files)
    if value["files_sha256"] != files_digest:
        raise ValueError("Task 7 source freeze files_sha256 drifted")
    if value["freeze_id"] != _freeze_id(
        value["expected_final_tree_oid"],
        files_digest,
        namespace_id,
    ):
        raise ValueError("Task 7 source freeze freeze_id drifted")


def build_source_freeze(
    tree_oid: str,
    files: Sequence[Mapping[str, Any]],
    namespace_id: str = DEFAULT_NAMESPACE_ID,
) -> dict[str, Any]:
    contract = namespace_contract(namespace_id)
    files = sorted((dict(row) for row in files), key=lambda row: row["path"])
    files_sha256 = _files_digest(files)
    value = {
        "schema": contract.source_freeze_schema,
        "freeze_id": _freeze_id(tree_oid, files_sha256, namespace_id),
        "branch": contract.branch,
        "ref": contract.ref,
        "expected_final_tree_oid": tree_oid,
        "manifest_algorithm": "sha256-canonical-json-source-files-v1",
        "file_count": len(files),
        "files_sha256": files_sha256,
        "files": files,
        "complete": True,
        "model_calls": 0,
        "terminal_claim": False,
    }
    if namespace_id != LEGACY_NAMESPACE_ID:
        value = {
            "schema": value["schema"],
            "freeze_id": value["freeze_id"],
            "evidence_namespace": contract.namespace_id,
            "namespace_version": contract.namespace_version,
            "generation": contract.generation,
            "evidence_root": contract.evidence_rel.as_posix(),
            **{key: item for key, item in value.items() if key not in {"schema", "freeze_id"}},
        }
    validate_source_freeze(value, namespace_id)
    return value


def parse_tree_record(record: bytes) -> tuple[str, str, int, str]:
    header, path_raw = record.split(b"\t", 1)
    parts = header.decode("ascii").split()
    if len(parts) != 4 or not parts[3].isdigit():
        raise ValueError(f"malformed Git ls-tree record: {record!r}")
    _mode, object_type, oid, size = parts
    return object_type, oid, int(size), path_raw.decode("utf-8", "strict")


def _batch_blobs(oids: Sequence[str]) -> list[bytes]:
    completed = subprocess.run(
        ["git", "--no-replace-objects", "cat-file", "--batch"],
        cwd=ROOT,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
        input=("\n".join(oids) + "\n").encode("ascii"),
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"git cat-file --batch failed: {completed.stderr.decode('utf-8', 'replace').strip()}")
    stream = io.BytesIO(completed.stdout)
    blobs: list[bytes] = []
    for expected_oid in oids:
        header = stream.readline().decode("ascii").strip().split()
        if len(header) != 3 or header[0] != expected_oid or header[1] != "blob" or not header[2].isdigit():
            raise ValueError(f"unexpected git cat-file --batch header for {expected_oid}: {header}")
        blob = stream.read(int(header[2]))
        if stream.read(1) != b"\n":
            raise ValueError(f"git cat-file --batch delimiter missing for {expected_oid}")
        blobs.append(blob)
    if stream.read():
        raise ValueError("git cat-file --batch returned trailing bytes")
    return blobs


def _tree_files(tree_oid: str) -> list[dict[str, Any]]:
    if str(_git(["cat-file", "-t", tree_oid])).strip() != "tree":
        raise ValueError(f"{tree_oid} is not a Git tree")
    raw = bytes(_git(["ls-tree", "-r", "-l", "-z", "--full-tree", tree_oid], binary=True))
    metadata: list[tuple[str, int, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        object_type, oid, size, path = parse_tree_record(record)
        if object_type != "blob":
            raise ValueError(f"Task 7 source freeze supports blobs only: {record!r}")
        metadata.append((oid, size, path))
    if not metadata:
        raise ValueError("Task 7 source freeze cannot be empty")
    blobs = _batch_blobs([oid for oid, _size, _path in metadata])
    rows: list[dict[str, Any]] = []
    for (oid, size, path), blob in zip(metadata, blobs):
        if len(blob) != size:
            raise ValueError(f"Git blob size drifted for {path}")
        rows.append({"path": path, "blob_oid": oid, "byte_count": len(blob), "raw_sha256": _sha(blob)})
    return rows


def _parse_hash_object_results(raw: bytes, expected_count: int) -> list[str]:
    if not raw.endswith(b"\n"):
        raise ValueError("git hash-object --stdin-paths returned an unterminated result")
    observed_oids = raw[:-1].split(b"\n")
    if len(observed_oids) != expected_count:
        raise ValueError(
            "git hash-object --stdin-paths result count drifted: "
            f"expected {expected_count}, got {len(observed_oids)}"
        )
    decoded: list[str] = []
    for oid_raw in observed_oids:
        try:
            oid = oid_raw.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError("git hash-object --stdin-paths returned a non-ASCII OID") from exc
        if re.fullmatch(r"[0-9a-f]{40}", oid) is None:
            raise ValueError(f"git hash-object --stdin-paths returned an invalid blob OID: {oid!r}")
        decoded.append(oid)
    return decoded


def _hash_object_paths(paths: Sequence[str]) -> list[str]:
    completed = subprocess.run(
        ["git", "--no-replace-objects", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
        input="".join(f"{path}\n" for path in paths).encode("utf-8"),
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(
            "git hash-object --stdin-paths failed: "
            f"{completed.stderr.decode('utf-8', 'replace').strip()}"
        )
    return _parse_hash_object_results(completed.stdout, len(paths))


def _verify_worktree_freeze(freeze: Mapping[str, Any]) -> None:
    observed_tree_oid = str(_git(["write-tree"])).strip()
    if observed_tree_oid != freeze["expected_final_tree_oid"]:
        raise ValueError(
            "staged Git tree differs from Task 7 freeze: "
            f"expected {freeze['expected_final_tree_oid']}, got {observed_tree_oid}"
        )

    paths: list[str] = []
    for row in freeze["files"]:
        path = row["path"]
        if "\r" in path or "\n" in path:
            raise ValueError(f"Task 7 source path contains unsupported CR/LF: {path!r}")
        resolve_repo_path(ROOT, path, must_exist=True, expect_file=True)
        paths.append(path)

    observed_oids = _hash_object_paths(paths)
    for row, oid in zip(freeze["files"], observed_oids):
        if oid != row["blob_oid"]:
            raise ValueError(f"working source content differs from Task 7 freeze at {row['path']}")


def _validate_no_model_native_report(path: Path) -> None:
    value = strict_json_loads(path.read_bytes(), label=str(path))
    if not isinstance(value, dict) or value.get("schema") != "daee-no-model-preflight-report-v2":
        raise ValueError("no-model preflight native report schema drifted")
    if value.get("decision") != "MATRIX_AUTHORIZED_AFTER_PREFLIGHT" or value.get("complete") is not True:
        raise ValueError("no-model preflight native report is not authorized")
    gates = value.get("gates")
    if (
        not isinstance(gates, list)
        or len(gates) != EXPECTED_GATE_COUNT
        or value.get("gate_count") != EXPECTED_GATE_COUNT
        or value.get("python_execution_profile_id") != PYTHON_EXECUTION_PROFILE_ID
    ):
        raise ValueError(f"no-model preflight native report must retain all {EXPECTED_GATE_COUNT} gates")
    commands: list[str] = []
    for expected_gate, gate in zip(NO_MODEL_GATES, gates):
        expected = expected_gate.number
        if (
            not isinstance(gate, dict)
            or gate.get("number") != expected
            or gate.get("name") != expected_gate.name
            or gate.get("passed") is not True
        ):
            raise ValueError(f"no-model preflight native report gate {expected} is not PASS")
        steps = gate.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"no-model preflight native report gate {expected} lacks executed steps")
        expected_returncode = EXPECTED_GATE_RETURN_CODES.get(expected, 0)
        if any(
            not isinstance(step, dict)
            or step.get("returncode") != expected_returncode
            or step.get("timed_out") is not False
            or step.get("execution_profile") != execution_profile_for(str(step.get("command", "")))
            for step in steps
        ):
            raise ValueError(
                f"no-model preflight native report gate {expected} has a failed/substituted step "
                f"(expected exit {expected_returncode})"
            )
        expected_commands = A16_GATE_COMMANDS.get(expected_gate.name)
        if expected_commands is not None and [step.get("command") for step in steps] != list(expected_commands):
            raise ValueError(f"no-model preflight native report gate {expected} command drift")
        commands.extend(str(step["command"]) for step in steps)
    if (
        value.get("command_count") != len(commands)
        or value.get("command_set_sha256") != command_list_sha256(commands)
        or value.get("execution_plan_sha256") != execution_plan_sha256(commands)
    ):
        raise ValueError("no-model preflight native report command/profile digest drifted")


def _run_role_checks(
    kind: str,
    *,
    namespace_id: str = DEFAULT_NAMESPACE_ID,
    timeout_seconds: int | float = TASK7_ROLE_OUTER_TIMEOUT_SECONDS,
) -> list[tuple[list[str], bytes, bytes]]:
    results: list[tuple[list[str], bytes, bytes]] = []
    for command in role_checks(kind, namespace_id):
        execution_argv = execution_argv_for(command)
        completed = run_owned_command(
            execution_argv,
            cwd=ROOT,
            capture_output=True,
            timeout_seconds=timeout_seconds,
            env=execution_environment_for(command),
        )
        if completed.timed_out:
            raise Task7RoleTimeout(kind, command, timeout_seconds)
        if completed.returncode != 0:
            raise ValueError(
                f"Task 7 {kind} check {command!r} failed with exit {completed.returncode}: "
                f"{completed.stderr.decode('utf-8', 'replace').strip()}"
            )
        results.append((list(command), completed.stdout, completed.stderr))
    return results


def build_evidence(
    *,
    kind: str,
    command: Sequence[str],
    report: Mapping[str, Any],
    log: Mapping[str, Any],
    checker: Mapping[str, Any],
    source_freeze: Mapping[str, Any],
    freeze: Mapping[str, Any],
    observed_at: str,
    namespace_id: str = DEFAULT_NAMESPACE_ID,
) -> dict[str, Any]:
    if kind not in STATUS_BY_KIND:
        raise ValueError(f"unsupported Task 7 verdict kind {kind!r}")
    validate_role_command(
        command,
        kind,
        str(checker.get("path", "")),
        namespace_id=namespace_id,
    )
    command_sha256 = _command_digest(command)
    value = {
        "schema": "daee-task7-deterministic-evidence-v1",
        "evidence_id": _evidence_id(
            kind,
            freeze["freeze_id"],
            command_sha256,
            report["sha256"],
            log["sha256"],
        ),
        "kind": kind,
        "status": STATUS_BY_KIND[kind],
        "command": list(command),
        "command_sha256": command_sha256,
        "execution_profile": execution_profile_for(command),
        "exit_code": 0,
        "report": dict(report),
        "log": dict(log),
        "checker": dict(checker),
        "source_freeze": dict(source_freeze),
        "freeze_id": freeze["freeze_id"],
        "expected_final_tree_oid": freeze["expected_final_tree_oid"],
        "observed_at": observed_at,
        "model_calls": 0,
        "candidate_claim": False,
        "terminal_claim": False,
        "non_claims": NON_CLAIMS,
    }
    _validate(value, "task7_deterministic_evidence", label="Task 7 deterministic evidence")
    return value


def _publish(root: Path, target: Path, value: dict[str, Any]) -> str:
    root.mkdir(parents=True, exist_ok=True)
    digest = claim_json_once(root, target, value)
    observed, _raw, observed_digest = strict_snapshot(target)
    if observed != value or observed_digest != digest:
        raise CustodyError("Task 7 deterministic evidence readback mismatch", subcode="readback-drift")
    return digest


def _write_log_once(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        if os.write(descriptor, raw) != len(raw):
            raise OSError("short Task 7 log write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def self_test() -> int:
    global ROOT

    with tempfile.TemporaryDirectory(prefix="daee-task7-clean-filter-") as temporary:
        repo = Path(temporary)

        def temp_git(*arguments: str) -> str:
            completed = subprocess.run(
                ["git", "--no-replace-objects", *arguments],
                cwd=repo,
                env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                print(
                    "Task 7 deterministic evidence writer self-test: FAIL "
                    f"(temporary git {' '.join(arguments)}: {completed.stderr.strip()})"
                )
                raise ValueError("temporary Git setup failed")
            return completed.stdout.strip()

        temp_git("init", "--quiet")
        temp_git("config", "core.autocrlf", "false")
        attributes_path = repo / ".gitattributes"
        sample_path = repo / "sample.txt"
        attributes_raw = b"*.txt text eol=lf\n"
        sample_lf = b"alpha\nbeta\n"
        sample_crlf = b"alpha\r\nbeta\r\n"
        attributes_path.write_bytes(attributes_raw)
        sample_path.write_bytes(sample_lf)
        temp_git("add", "--", ".gitattributes", "sample.txt")
        original_root = ROOT
        try:
            ROOT = repo
            expected_tree = temp_git("write-tree")
            clean_filter_freeze = build_source_freeze(expected_tree, _tree_files(expected_tree))
            sample_path.write_bytes(sample_crlf)
            try:
                _verify_worktree_freeze(clean_filter_freeze)
            except ValueError as exc:
                print(
                    "Task 7 deterministic evidence writer self-test: FAIL "
                    f"(clean-filter portability: {exc})"
                )
                return 1

            sample_path.write_bytes(b"alpha\r\nactual drift\r\n")
            try:
                _verify_worktree_freeze(clean_filter_freeze)
            except ValueError as exc:
                if "sample.txt" not in str(exc):
                    print(
                        "Task 7 deterministic evidence writer self-test: FAIL "
                        f"(content drift rejected for wrong reason: {exc})"
                    )
                    return 1
            else:
                print("Task 7 deterministic evidence writer self-test: FAIL (content drift survived)")
                return 1

            sample_path.write_bytes(sample_crlf)
            attributes_path.write_bytes(attributes_raw + b"# staged index drift\n")
            temp_git("add", "--", ".gitattributes")
            attributes_path.write_bytes(attributes_raw)
            try:
                _verify_worktree_freeze(clean_filter_freeze)
            except ValueError as exc:
                if "staged Git tree" not in str(exc):
                    print(
                        "Task 7 deterministic evidence writer self-test: FAIL "
                        f"(index drift rejected for wrong reason: {exc})"
                    )
                    return 1
            else:
                print("Task 7 deterministic evidence writer self-test: FAIL (index drift survived)")
                return 1

            attributes_path.write_bytes(attributes_raw)
            temp_git("add", "--", ".gitattributes")

            def expect_rejection(label: str, expected: str, operation: Callable[[], Any]) -> bool:
                try:
                    operation()
                except ValueError as exc:
                    if str(exc) == expected:
                        return True
                    print(
                        "Task 7 deterministic evidence writer self-test: FAIL "
                        f"({label} rejected for wrong reason: {exc})"
                    )
                    return False
                print(f"Task 7 deterministic evidence writer self-test: FAIL ({label} survived)")
                return False

            failed_hash_object = subprocess.CompletedProcess(
                ["git", "--no-replace-objects", "hash-object", "--stdin-paths"],
                7,
                b"",
                b"forced hash-object failure\n",
            )
            with mock.patch.object(subprocess, "run", return_value=failed_hash_object):
                if not expect_rejection(
                    "hash-object failure",
                    "git hash-object --stdin-paths failed: forced hash-object failure",
                    lambda: _hash_object_paths(["sample.txt"]),
                ):
                    return 1

            output_canaries = (
                (
                    "unterminated hash-object output",
                    b"a" * 40,
                    "git hash-object --stdin-paths returned an unterminated result",
                ),
                (
                    "count-drifted hash-object output",
                    b"a" * 40 + b"\n" + b"b" * 40 + b"\n",
                    "git hash-object --stdin-paths result count drifted: expected 1, got 2",
                ),
                (
                    "non-ASCII hash-object output",
                    b"\xff" * 40 + b"\n",
                    "git hash-object --stdin-paths returned a non-ASCII OID",
                ),
                (
                    "malformed hash-object output",
                    b"not-an-oid\n",
                    "git hash-object --stdin-paths returned an invalid blob OID: 'not-an-oid'",
                ),
            )
            for label, raw, expected in output_canaries:
                if not expect_rejection(label, expected, lambda raw=raw: _parse_hash_object_results(raw, 1)):
                    return 1

            missing_path_freeze = copy.deepcopy(clean_filter_freeze)
            missing_path_freeze["files"][-1]["path"] = "missing.txt"
            if not expect_rejection(
                "missing frozen path",
                "required path does not exist: missing.txt",
                lambda: _verify_worktree_freeze(missing_path_freeze),
            ):
                return 1

            crlf_path_freeze = copy.deepcopy(clean_filter_freeze)
            crlf_path_freeze["files"][-1]["path"] = "sample.txt\r\n"
            if not expect_rejection(
                "CR/LF frozen path",
                "Task 7 source path contains unsupported CR/LF: 'sample.txt\\r\\n'",
                lambda: _verify_worktree_freeze(crlf_path_freeze),
            ):
                return 1
        finally:
            ROOT = original_root

    files = [
        {
            "path": PRODUCER_PATH,
            "blob_oid": "a" * 40,
            "byte_count": 12,
            "raw_sha256": "b" * 64,
        },
        {
            "path": "tests/empty.txt",
            "blob_oid": "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
            "byte_count": 0,
            "raw_sha256": _sha(b""),
        },
    ]
    freeze = build_source_freeze("4" * 40, files)
    results = [(["python", "tools/run_no_model_preflight.py", "--json", NO_MODEL_NATIVE_REPORT_REL.as_posix()], b"MATRIX_AUTHORIZED_AFTER_PREFLIGHT\n", b"")]
    command_log = build_command_log("no-model-preflight", results)
    producer = {"path": PRODUCER_PATH, "blob_oid": "a" * 40, "raw_sha256": "b" * 64}
    report_value = build_result_report(
        kind="no-model-preflight",
        results=results,
        evidence_artifacts=[{"path": NO_MODEL_NATIVE_REPORT_REL.as_posix(), "byte_count": 12, "sha256": "c" * 64}],
        producer=producer,
        freeze=freeze,
        observed_at="2026-07-12T12:00:00Z",
    )
    if command_log["entries"][0]["sequence"] != 1 or report_value["check_count"] != 1:
        print("Task 7 deterministic evidence writer self-test: FAIL (contentful report/log)")
        return 1
    evidence = build_evidence(
        kind="no-model-preflight",
        command=producer_command("no-model-preflight"),
        report={"path": "report.json", "byte_count": 12, "sha256": "c" * 64},
        log={"path": "run.log", "byte_count": 12, "sha256": "d" * 64},
        checker=producer,
        source_freeze={"path": "source-freeze.json", "byte_count": 12, "sha256": "e" * 64},
        freeze=freeze,
        observed_at="2026-07-12T12:00:00Z",
    )
    with tempfile.TemporaryDirectory(prefix="daee-task7-evidence-writer-") as temporary:
        root = Path(temporary)
        target = root / "no-model-preflight.json"
        _publish(root, target, evidence)
        try:
            _publish(root, target, evidence)
        except CustodyError as exc:
            if exc.subcode != "claim-replay":
                print(f"Task 7 deterministic evidence writer self-test: FAIL ({exc.subcode})")
                return 1
        else:
            print("Task 7 deterministic evidence writer self-test: FAIL (replay survived)")
            return 1
    print(
        "Task 7 deterministic evidence writer self-test: PASS "
        "(schema, freeze identity, clean-filter portability, content/index drift rejection, "
        "hash-object/path/output fail-closed rejection, create-once, replay rejection)"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--build-freeze", action="store_true")
    mode.add_argument("--build-verdict", action="store_true")
    parser.add_argument("--evidence-namespace", choices=sorted(EVIDENCE_NAMESPACES))
    parser.add_argument("--tree")
    parser.add_argument("--kind", choices=sorted(STATUS_BY_KIND))
    parser.add_argument("--source-freeze", type=Path)
    parser.add_argument("--out", type=Path)
    return parser


def _canonical_target(path: Path, expected: Path) -> Path:
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve()
    if resolved != (ROOT / expected).resolve():
        raise ValueError(f"--out must equal canonical create-once path {expected.as_posix()}")
    return resolved


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        if any(
            value is not None
            for value in (
                args.evidence_namespace,
                args.tree,
                args.kind,
                args.source_freeze,
                args.out,
            )
        ):
            parser.error("--self-test cannot be combined with build arguments")
        return self_test()
    if args.evidence_namespace is None:
        parser.error("build modes require --evidence-namespace")
    namespace_id = args.evidence_namespace
    contract = namespace_contract(namespace_id)
    try:
        if args.build_freeze:
            if args.tree is None or args.out is None:
                parser.error("--build-freeze requires --tree and --out")
            if any(value is not None for value in (args.kind, args.source_freeze)):
                parser.error("verdict arguments cannot be used with --build-freeze")
            if re.fullmatch(r"[0-9a-f]{40}", args.tree) is None:
                parser.error("--tree must be a full lowercase Git tree OID")
            target = _canonical_target(args.out, contract.source_freeze_rel)
            value = build_source_freeze(
                args.tree,
                _tree_files(args.tree),
                namespace_id=namespace_id,
            )
            digest = _publish(contract.evidence_root, target, value)
            print(f"Task 7 source freeze: PASS ({target.relative_to(ROOT).as_posix()} sha256={digest})")
            return 0
        required = {"--kind": args.kind, "--source-freeze": args.source_freeze, "--out": args.out}
        missing = [name for name, value in required.items() if value is None]
        if missing or args.tree is not None:
            parser.error(f"--build-verdict requires {', '.join(missing) if missing else 'no --tree'}")
        expected_out = contract.evidence_rel / ROLE_FILE_BY_KIND[args.kind]
        target = _canonical_target(args.out, expected_out)
        freeze_path = resolve_repo_path(ROOT, args.source_freeze, must_exist=True, expect_file=True)
        expected_freeze = (ROOT / contract.source_freeze_rel).resolve()
        if freeze_path.resolve() != expected_freeze:
            raise ValueError(f"--source-freeze must be canonical {contract.source_freeze_rel}")
        freeze, freeze_raw = _load_source_freeze(freeze_path, namespace_id)
        checker_rows = [row for row in freeze["files"] if row["path"] == PRODUCER_PATH]
        if len(checker_rows) != 1:
            raise ValueError("Task 7 role-bound producer is absent or duplicated in the complete source freeze")
        checker = {key: checker_rows[0][key] for key in ("path", "blob_oid", "raw_sha256")}
        checker_path = resolve_repo_path(ROOT, PRODUCER_PATH, must_exist=True, expect_file=True)
        checker_raw = checker_path.read_bytes()
        if len(checker_raw) != checker_rows[0]["byte_count"] or _sha(checker_raw) != checker["raw_sha256"]:
            raise ValueError("Task 7 producer working bytes differ from the precommit source freeze")
        _verify_worktree_freeze(freeze)
        report_path = (ROOT / report_rel(args.kind, namespace_id)).resolve()
        log_path = (ROOT / log_rel(args.kind, namespace_id)).resolve()
        if report_path.exists() or log_path.exists() or target.exists():
            raise CustodyError("Task 7 verdict cohort already exists", subcode="claim-replay")
        evidence_artifacts: list[dict[str, Any]] = []
        if args.kind == "no-model-preflight":
            native_path = (ROOT / native_report_rel(args.kind, namespace_id)).resolve()
            if native_path.exists():
                raise CustodyError("Task 7 native no-model report already exists", subcode="claim-replay")
        elif args.kind == "full-local-ci":
            native_path = (ROOT / native_report_rel(args.kind, namespace_id)).resolve()
            if native_path.exists():
                raise CustodyError("Task 7 native full-local-CI report already exists", subcode="claim-replay")
        elif args.kind == "independent-whole-branch-review":
            authorization_path = resolve_repo_path(
                ROOT,
                review_authorization_rel(namespace_id),
                must_exist=True,
                expect_file=True,
            )
            authorization_value, _authorization_raw = _load_json(
                authorization_path,
                definition="task7_review_authorization",
                label="Task 7 independent reviewer authorization",
            )
            authorization_ref = _artifact_ref(authorization_path)
            review_path = resolve_repo_path(
                ROOT,
                contract.whole_branch_review_rel,
                must_exist=True,
                expect_file=True,
            )
            review_value, _review_raw = _load_json(
                review_path,
                definition="task7_whole_branch_review",
                label="Task 7 independent whole-branch review",
            )
            validate_whole_branch_review(
                review_value,
                freeze,
                authorization_value,
                authorization_ref,
            )
            evidence_artifacts.append(authorization_ref)
            evidence_artifacts.append(_artifact_ref(review_path))
        results = _run_role_checks(args.kind, namespace_id=namespace_id)
        if args.kind == "no-model-preflight":
            _validate_no_model_native_report(native_path)
            evidence_artifacts.append(_artifact_ref(native_path))
        elif args.kind == "full-local-ci":
            native_value, _native_raw = _load_json(
                native_path,
                definition="run_local_ci_completion",
                label="Task 7 native full-local-CI report",
            )
            completion = parse_completion_stdout(results[0][1])
            if native_value != completion:
                raise ValueError("Task 7 native full-local-CI report differs from stdout completion")
            evidence_artifacts.append(_artifact_ref(native_path))
        _verify_worktree_freeze(freeze)
        if checker_path.read_bytes() != checker_raw:
            raise ValueError("Task 7 producer working bytes changed during verifier execution")
        post_freeze, post_freeze_raw = _load_source_freeze(freeze_path, namespace_id)
        if post_freeze_raw != freeze_raw or post_freeze != freeze:
            raise ValueError("Task 7 source freeze changed during verifier execution")
        observed_at = _now()
        if args.kind == "independent-whole-branch-review":
            review_time = datetime.strptime(review_value["reviewed_at"], "%Y-%m-%dT%H:%M:%SZ")
            evidence_time = datetime.strptime(observed_at, "%Y-%m-%dT%H:%M:%SZ")
            if review_time > evidence_time:
                raise ValueError("Task 7 whole-branch review cannot postdate its evidence observation")
        command_log = build_command_log(args.kind, results)
        _publish(contract.evidence_root, log_path, command_log)
        report_value = build_result_report(
            kind=args.kind,
            results=results,
            evidence_artifacts=evidence_artifacts,
            producer=checker,
            freeze=freeze,
            observed_at=observed_at,
            namespace_id=namespace_id,
        )
        _publish(contract.evidence_root, report_path, report_value)
        source_freeze_ref = _artifact_ref(freeze_path)
        report_ref = _artifact_ref(report_path)
        log_ref = _artifact_ref(log_path)
        value = build_evidence(
            kind=args.kind,
            command=producer_command(args.kind, namespace_id),
            report=report_ref,
            log=log_ref,
            checker=checker,
            source_freeze=source_freeze_ref,
            freeze=freeze,
            observed_at=observed_at,
            namespace_id=namespace_id,
        )
        digest = _publish(contract.evidence_root, target, value)
    except Task7RoleTimeout as exc:
        print(f"Task 7 deterministic evidence: TIMEOUT ({exc})")
        return exc.returncode
    except (CustodyError, OSError, PathCustodyError, ValueError) as exc:
        print(f"Task 7 deterministic evidence: FAIL ({exc})")
        return 1
    print(f"Task 7 deterministic evidence: PASS ({target.relative_to(ROOT).as_posix()} sha256={digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
