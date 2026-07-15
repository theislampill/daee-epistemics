#!/usr/bin/env python3
"""Validate Task 7 evidence namespaces and Branch 11 integration-freeze readback."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import write_task7_deterministic_evidence as writer
from contract_validation import PathCustodyError, validate_schema_definition, validate_schema_subset
from source_provenance import DuplicateObjectKey, strict_json_loads


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema/task7-deterministic-evidence-namespace.schema.json"
INTEGRATION_FREEZE_REL = Path(
    ".IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5/"
    "reviews/branch11-final-integration-freeze.json"
)


@dataclass(frozen=True)
class Finding:
    failure_class: str
    message: str


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _schema() -> dict[str, Any]:
    value = strict_json_loads(SCHEMA_PATH.read_bytes(), label=str(SCHEMA_PATH))
    if not isinstance(value, dict) or not isinstance(value.get("$defs"), dict):
        raise ValueError("Task 7 evidence-namespace schema definitions are unavailable")
    validate_schema_definition(value)
    return value


def _schema_ref(name: str) -> dict[str, Any]:
    schema = _schema()
    return {"$defs": schema["$defs"], "$ref": f"#/$defs/{name}"}


def _schema_finding(value: Mapping[str, Any], definition: str) -> Finding | None:
    issues = validate_schema_subset(value, _schema_ref(definition))
    if not issues:
        return None
    first = issues[0]
    return Finding(
        "schema-contract",
        f"{definition} violation at {first.path}: {first.message}",
    )


def _resolve_artifact_path(root: Path, artifact_path: Path) -> Path:
    root_resolved = root.resolve(strict=True)
    candidate = artifact_path if artifact_path.is_absolute() else root_resolved / artifact_path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PathCustodyError(
            f"Task 7 namespace artifact leaves repository root: {artifact_path}",
            subcode="namespace-path-escape",
        ) from exc
    return resolved


def directory_manifest_digest(root: Path) -> tuple[int, str]:
    """Return path/size/content digest without modifying the immutable evidence root."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"Task 7 evidence namespace is not a directory: {root}")
    rows: list[bytes] = []
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in files:
        raw = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        rows.append(
            relative.encode("utf-8")
            + b"\t"
            + str(len(raw)).encode("ascii")
            + b"\t"
            + _sha(raw).encode("ascii")
            + b"\n"
        )
    return len(files), _sha(b"".join(rows))


def integration_aggregate(rows: Sequence[Mapping[str, Any]]) -> str:
    canonical = b"".join(
        str(row["path"]).encode("utf-8")
        + b"\t"
        + str(row["sha256"]).lower().encode("ascii")
        + b"\n"
        for row in sorted(rows, key=lambda item: str(item["path"]))
    )
    return _sha(canonical)


def _paths(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    return [str(row.get("path", "")) for row in rows]


def validate_source_freeze_namespace(
    value: Mapping[str, Any],
    *,
    namespace_id: str,
    artifact_path: Path,
    observed_tree_oid: str,
    observed_files: Sequence[Mapping[str, Any]],
    root: Path = ROOT,
) -> Finding | None:
    """Validate one source freeze against a selected fixed namespace and tree readback."""
    try:
        contract = writer.namespace_contract(namespace_id)
    except ValueError as exc:
        return Finding("unsupported-namespace", str(exc))
    try:
        resolved = _resolve_artifact_path(root, artifact_path)
    except PathCustodyError as exc:
        return Finding("namespace-path-substitution", str(exc))
    expected_path = (root / contract.source_freeze_rel).resolve()
    if resolved != expected_path:
        return Finding(
            "namespace-path-substitution",
            f"{namespace_id} source freeze must be read from {contract.source_freeze_rel.as_posix()}",
        )

    if namespace_id == writer.LEGACY_NAMESPACE_ID:
        if value.get("schema") != contract.source_freeze_schema:
            return Finding("cross-namespace-substitution", "Branch 10 namespace received a non-legacy source freeze")
    else:
        if (
            value.get("schema") != contract.source_freeze_schema
            or value.get("evidence_namespace") != namespace_id
            or value.get("namespace_version") != contract.namespace_version
            or value.get("generation") != contract.generation
            or value.get("evidence_root") != contract.evidence_rel.as_posix()
        ):
            return Finding(
                "cross-namespace-substitution",
                f"source freeze does not bind exact namespace {namespace_id}",
            )
    if value.get("branch") != contract.branch or value.get("ref") != contract.ref:
        return Finding(
            "branch-mismatch",
            f"{namespace_id} requires branch/ref {contract.branch} / {contract.ref}",
        )
    try:
        writer.validate_source_freeze(value, namespace_id)
    except (OSError, ValueError) as exc:
        return Finding("freeze-identity-drift", str(exc))

    if value["expected_final_tree_oid"] != observed_tree_oid:
        return Finding(
            "tree-drift",
            "current staged tree differs from the namespace-bound source freeze",
        )

    frozen_files = list(value["files"])
    observed = sorted((dict(row) for row in observed_files), key=lambda row: row["path"])
    if _paths(frozen_files) != _paths(observed):
        return Finding(
            "path-drift",
            "Git tree path set differs from the namespace-bound source freeze",
        )
    for frozen, actual in zip(frozen_files, observed):
        if any(
            frozen[field] != actual.get(field)
            for field in ("blob_oid", "byte_count", "raw_sha256")
        ):
            return Finding(
                "hash-drift",
                f"Git tree content identity differs at {frozen['path']}",
            )
    return None


def validate_integration_freeze(
    value: Mapping[str, Any],
    *,
    actual_rows: Sequence[Mapping[str, Any]],
    current_branch: str,
    current_head: str,
) -> Finding | None:
    """Validate the ad hoc Branch 11 freeze against current dirty-source bytes."""
    schema_finding = _schema_finding(value, "branch11_integration_freeze")
    if schema_finding is not None:
        return schema_finding
    if value["branch"] != current_branch:
        return Finding("integration-branch-drift", "current branch differs from the integration freeze")
    if value["base_head"] != current_head:
        return Finding("integration-head-drift", "current HEAD differs from the integration freeze base_head")

    frozen_rows = list(value["paths"])
    frozen_paths = _paths(frozen_rows)
    if frozen_paths != sorted(frozen_paths) or len(frozen_paths) != len(set(frozen_paths)):
        return Finding("integration-path-drift", "integration freeze paths must be unique and ordinal-sorted")
    if value["source_path_count"] != len(frozen_rows):
        return Finding("integration-path-drift", "integration freeze source_path_count differs from paths")
    if value["aggregate_sha256"] != integration_aggregate(frozen_rows):
        return Finding("integration-hash-drift", "integration freeze aggregate_sha256 drifted")

    observed = sorted((dict(row) for row in actual_rows), key=lambda row: row["path"])
    if frozen_paths != _paths(observed):
        return Finding("integration-path-drift", "current non-ignored dirty source path set differs from freeze")
    for frozen, actual in zip(frozen_rows, observed):
        if frozen["status"] != actual.get("status"):
            return Finding("integration-status-drift", f"dirty status differs at {frozen['path']}")
        if frozen["bytes"] != actual.get("bytes") or frozen["sha256"] != actual.get("sha256"):
            return Finding("integration-hash-drift", f"dirty source bytes differ at {frozen['path']}")
    return None


def _git(arguments: Sequence[str], *, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=not binary,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", "replace") if binary else completed.stderr
        raise ValueError(f"git {' '.join(arguments)} failed: {stderr.strip()}")
    return completed.stdout


def current_integration_rows() -> list[dict[str, Any]]:
    raw = bytes(_git(["status", "--porcelain=v1", "-z", "--untracked-files=all"], binary=True))
    records = raw.split(b"\0")
    rows: list[dict[str, Any]] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2:3] != b" ":
            raise ValueError(f"malformed git status record: {record!r}")
        xy = record[:2].decode("ascii")
        path_text = record[3:].decode("utf-8", "strict")
        if "R" in xy or "C" in xy:
            if index >= len(records) or not records[index]:
                raise ValueError(f"rename/copy status lacks source path: {record!r}")
            index += 1
        path = ROOT / path_text
        if not path.is_file():
            raise ValueError(f"dirty source path is absent or not a regular file: {path_text}")
        data = path.read_bytes()
        rows.append(
            {
                "path": Path(path_text).as_posix(),
                "status": "untracked" if xy == "??" else "tracked-change",
                "sha256": _sha(data),
                "bytes": len(data),
            }
        )
    return sorted(rows, key=lambda row: row["path"])


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = strict_json_loads(path.read_bytes(), label=str(path))
    except DuplicateObjectKey as exc:
        raise ValueError(f"duplicate JSON key rejected: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} root must be an object")
    return value


def self_test() -> int:
    try:
        validate_schema_definition(_schema())
        legacy = writer.namespace_contract(writer.LEGACY_NAMESPACE_ID)
        current = writer.namespace_contract(writer.DEFAULT_NAMESPACE_ID)
        if legacy.evidence_rel == current.evidence_rel:
            raise ValueError("Branch 10 and Branch 11 evidence roots alias")
        files = [{"path": writer.PRODUCER_PATH, "blob_oid": "a" * 40, "byte_count": 1, "raw_sha256": "b" * 64}]
        freeze = writer.build_source_freeze("4" * 40, files, writer.DEFAULT_NAMESPACE_ID)
        finding = validate_source_freeze_namespace(
            freeze,
            namespace_id=writer.DEFAULT_NAMESPACE_ID,
            artifact_path=ROOT / current.source_freeze_rel,
            observed_tree_oid="4" * 40,
            observed_files=files,
        )
        if finding is not None:
            raise ValueError(f"[{finding.failure_class}] {finding.message}")
    except (OSError, PathCustodyError, ValueError) as exc:
        print(f"Task 7 evidence namespace self-test: FAIL ({exc})")
        return 1
    print("Task 7 evidence namespace self-test: PASS (2 fixed namespaces; native freeze readback)")
    return 0


def _run_source_freeze(path: Path, namespace_id: str) -> int:
    try:
        resolved = _resolve_artifact_path(ROOT, path)
        value = _load_object(resolved)
        observed_tree_oid = str(_git(["write-tree"])).strip()
        observed_files = writer._tree_files(observed_tree_oid)
        finding = validate_source_freeze_namespace(
            value,
            namespace_id=namespace_id,
            artifact_path=resolved,
            observed_tree_oid=observed_tree_oid,
            observed_files=observed_files,
        )
        if finding is None:
            writer._verify_worktree_freeze(value)
    except (OSError, PathCustodyError, ValueError) as exc:
        finding = Finding("source-readback", str(exc))
    if finding is not None:
        print(f"Task 7 evidence namespace: FAIL [{finding.failure_class}] {finding.message}")
        return 1
    print(f"Task 7 evidence namespace: PASS ({namespace_id}; {resolved.relative_to(ROOT).as_posix()})")
    return 0


def _run_integration_freeze(path: Path) -> int:
    try:
        resolved = _resolve_artifact_path(ROOT, path)
        if resolved != (ROOT / INTEGRATION_FREEZE_REL).resolve():
            raise ValueError(f"integration freeze must equal canonical path {INTEGRATION_FREEZE_REL.as_posix()}")
        value = _load_object(resolved)
        finding = validate_integration_freeze(
            value,
            actual_rows=current_integration_rows(),
            current_branch=str(_git(["branch", "--show-current"])).strip(),
            current_head=str(_git(["rev-parse", "HEAD"])).strip(),
        )
    except (OSError, PathCustodyError, ValueError) as exc:
        finding = Finding("integration-readback", str(exc))
    if finding is not None:
        print(f"Task 7 integration freeze: FAIL [{finding.failure_class}] {finding.message}")
        return 1
    print(f"Task 7 integration freeze: PASS ({resolved.relative_to(ROOT).as_posix()})")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--source-freeze", type=Path)
    mode.add_argument("--integration-freeze", type=Path)
    parser.add_argument("--evidence-namespace", choices=sorted(writer.EVIDENCE_NAMESPACES))
    args = parser.parse_args(argv)
    if args.self_test:
        if args.evidence_namespace is not None:
            parser.error("--self-test cannot be combined with --evidence-namespace")
        return self_test()
    if args.source_freeze is not None:
        if args.evidence_namespace is None:
            parser.error("--source-freeze requires --evidence-namespace")
        return _run_source_freeze(args.source_freeze, args.evidence_namespace)
    if args.evidence_namespace is not None:
        parser.error("--integration-freeze cannot be combined with --evidence-namespace")
    return _run_integration_freeze(args.integration_freeze)


if __name__ == "__main__":
    raise SystemExit(main())
