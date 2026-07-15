#!/usr/bin/env python3
"""Create and verify the exact Git-bound Stage07 execution-tooling manifest."""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import checker_execution_snapshot as checker_snapshot
import contract_validation
import run_staged_current_skill_smoke as stage_runner


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_RELATIVE = "schema/execution-tooling-manifest.schema.json"
SCHEMA = "daee-stage07-execution-tooling-manifest-v1"
KIND = "execution-tooling-manifest"
PROFILE = "stage07-release"
AGGREGATE_ALGORITHM = "sha256-domain-canonical-json-stage07-tooling-v1"
AGGREGATE_DOMAIN = b"daee-stage07-execution-tooling-manifest-v1\0"
GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ExecutionToolingManifestError(RuntimeError):
    """Fail-closed tooling-manifest construction or verification error."""


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable_bytes(path: Path, label: str) -> bytes:
    try:
        first = path.read_bytes()
        second = path.read_bytes()
    except OSError as exc:
        raise ExecutionToolingManifestError(f"{label} cannot be read") from exc
    if first != second:
        raise ExecutionToolingManifestError(f"{label} changed during validation")
    return first


def _contained(
    root: Path,
    value: str | Path,
    label: str,
    *,
    must_exist: bool,
    expect_file: bool = False,
) -> Path:
    try:
        return contract_validation.resolve_repo_path(
            root,
            value,
            must_exist=must_exist,
            expect_file=expect_file,
        )
    except (contract_validation.PathCustodyError, OSError) as exc:
        raise ExecutionToolingManifestError(f"{label} leaves repository custody") from exc


def _run_git(
    root: Path,
    arguments: Sequence[str],
    *,
    input_bytes: bytes | None = None,
) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "--no-replace-objects", *arguments],
            cwd=root,
            env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
            input=input_bytes,
            capture_output=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExecutionToolingManifestError(f"Git command unavailable or timed out: {' '.join(arguments)}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise ExecutionToolingManifestError(f"Git command failed: {' '.join(arguments)}: {detail}")
    return completed.stdout


def _git_commit_exists(root: Path, source_commit: str) -> None:
    if GIT_OID_RE.fullmatch(source_commit) is None:
        raise ExecutionToolingManifestError("source commit must be an exact lowercase 40-hex Git OID")
    object_type = _run_git(root, ["cat-file", "-t", source_commit]).decode("ascii", "strict").strip()
    if object_type != "commit":
        raise ExecutionToolingManifestError("source commit is not a Git commit")


def _source_tree(root: Path, source_commit: str) -> str:
    tree = _run_git(root, ["rev-parse", f"{source_commit}^{{tree}}"] ).decode("ascii", "strict").strip()
    if GIT_OID_RE.fullmatch(tree) is None:
        raise ExecutionToolingManifestError("source commit tree is not an exact Git tree OID")
    return tree


def _tree_index(root: Path, source_commit: str) -> dict[str, tuple[str, str, int]]:
    raw = _run_git(root, ["ls-tree", "-r", "-l", "-z", "--full-tree", source_commit])
    rows: dict[str, tuple[str, str, int]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            header, path_raw = record.split(b"\t", 1)
            mode, object_type, oid, size = header.decode("ascii").split()
            path = path_raw.decode("utf-8", "strict")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ExecutionToolingManifestError("Git tree contains a malformed path record") from exc
        if object_type != "blob" or not size.isdigit() or mode not in {"100644", "100755"}:
            continue
        if path in rows:
            raise ExecutionToolingManifestError(f"Git tree contains duplicate path: {path}")
        rows[path] = (mode, oid, int(size))
    return rows


def _governed_tree_paths(
    tree: Mapping[str, tuple[str, str, int]],
    membership: Mapping[str, object],
) -> list[str]:
    roots = [
        str(value).replace("\\", "/").rstrip("/")
        for key in ("snapshot_roots", "runtime_resources")
        for value in membership[key]
    ]
    return sorted(
        path
        for path in tree
        if any(path == root or path.startswith(f"{root}/") for root in roots)
    )


def _batch_blobs(root: Path, oids: Sequence[str]) -> list[bytes]:
    raw = _run_git(
        root,
        ["cat-file", "--batch"],
        input_bytes=("\n".join(oids) + "\n").encode("ascii"),
    )
    stream = io.BytesIO(raw)
    blobs: list[bytes] = []
    for expected_oid in oids:
        try:
            header = stream.readline().decode("ascii", "strict").strip().split()
        except UnicodeDecodeError as exc:
            raise ExecutionToolingManifestError("Git blob batch header is not ASCII") from exc
        if len(header) != 3 or header[0] != expected_oid or header[1] != "blob" or not header[2].isdigit():
            raise ExecutionToolingManifestError(f"Git blob batch header drifted for {expected_oid}")
        blob = stream.read(int(header[2]))
        if stream.read(1) != b"\n":
            raise ExecutionToolingManifestError(f"Git blob batch delimiter missing for {expected_oid}")
        blobs.append(blob)
    if stream.read():
        raise ExecutionToolingManifestError("Git blob batch returned trailing bytes")
    return blobs


def _plan_inventory(root: Path) -> tuple[list[dict[str, Any]], dict[str, Path], dict[str, object], list[str]]:
    output = root / ".daee" / "execution-tooling-manifest-stage07-output.md"
    try:
        plan = stage_runner.stage07_release_invocation_plan(root, output)
        sources = checker_snapshot.execution_snapshot_sources(root=root, plan=plan)
    except (OSError, ValueError, KeyError) as exc:
        raise ExecutionToolingManifestError(f"Stage07 tooling membership cannot be derived: {exc}") from exc
    runtime_resources = sorted({
        str(value).replace("\\", "/")
        for row in plan
        for value in row.get("runtime_resources", [])
    })
    membership: dict[str, object] = {
        "snapshot_roots": list(checker_snapshot.SNAPSHOT_ROOTS),
        "runtime_resources": runtime_resources,
    }
    result_order = [str(row["result_key"]) for row in plan]
    return plan, sources, membership, result_order


def _aggregate_payload(value: Mapping[str, Any]) -> dict[str, object]:
    return {
        "source_commit": value["source_commit"],
        "source_tree": value["source_tree"],
        "profile": value["profile"],
        "membership": value["membership"],
        "result_order": value["result_order"],
        "files": value["files"],
    }


def _aggregate_sha256(value: Mapping[str, Any]) -> str:
    return _sha256(AGGREGATE_DOMAIN + _canonical(_aggregate_payload(value)))


def _schema(root: Path) -> dict[str, Any]:
    path = _contained(root, SCHEMA_RELATIVE, "execution tooling schema", must_exist=True, expect_file=True)
    raw = _stable_bytes(path, "execution tooling schema")
    try:
        value = json.loads(raw.decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExecutionToolingManifestError("execution tooling schema is not strict JSON") from exc
    if not isinstance(value, dict):
        raise ExecutionToolingManifestError("execution tooling schema must be an object")
    return value


def _shape_errors(root: Path, manifest: object) -> None:
    try:
        issues = contract_validation.validate_schema_subset(manifest, _schema(root))
    except (contract_validation.SchemaDefinitionError, ValueError) as exc:
        raise ExecutionToolingManifestError(f"execution tooling schema is invalid: {exc}") from exc
    if issues:
        issue = issues[0]
        raise ExecutionToolingManifestError(
            f"execution tooling manifest shape invalid at {issue.path}: {issue.keyword}: {issue.message}"
        )


def build_execution_tooling_manifest(*, root: Path, source_commit: str) -> dict[str, Any]:
    """Build from the exact Git blobs and require the live bytes to match them."""

    source_root = root.resolve(strict=True)
    _git_commit_exists(source_root, source_commit)
    source_tree = _source_tree(source_root, source_commit)
    _plan, sources, membership, result_order = _plan_inventory(source_root)
    tree = _tree_index(source_root, source_commit)
    ordered_paths = sorted(sources)
    if ordered_paths != _governed_tree_paths(tree, membership):
        raise ExecutionToolingManifestError(
            "execution tooling file membership drift between source commit and working inventory"
        )
    missing = [path for path in ordered_paths if path not in tree]
    if missing:
        raise ExecutionToolingManifestError(f"execution tooling path absent from source commit: {missing[0]}")
    metadata = [tree[path] for path in ordered_paths]
    blobs = _batch_blobs(source_root, [oid for _mode, oid, _size in metadata])
    files: list[dict[str, object]] = []
    for path, source, (mode, oid, size), blob in zip(ordered_paths, (sources[path] for path in ordered_paths), metadata, blobs):
        if len(blob) != size:
            raise ExecutionToolingManifestError(f"Git blob byte count drifted for {path}")
        live = _stable_bytes(source, f"execution tooling source {path}")
        if live != blob:
            raise ExecutionToolingManifestError(f"execution tooling working byte drift at {path}")
        files.append({
            "path": path,
            "git_mode": mode,
            "blob_oid": oid,
            "byte_count": len(blob),
            "sha256": _sha256(blob),
        })
    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "kind": KIND,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "profile": PROFILE,
        "membership": membership,
        "result_order": result_order,
        "file_count": len(files),
        "aggregate_algorithm": AGGREGATE_ALGORITHM,
        "aggregate_sha256": "",
        "files": files,
    }
    manifest["aggregate_sha256"] = _aggregate_sha256(manifest)
    _shape_errors(source_root, manifest)
    return manifest


def validate_execution_tooling_manifest_identity(
    *,
    manifest: object,
    expected_source_commit: str,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    """Validate the authorization artifact itself without consulting live Git state."""

    _shape_errors(schema_root.resolve(strict=True), manifest)
    if not isinstance(manifest, dict):
        raise ExecutionToolingManifestError("execution tooling manifest must be an object")
    if manifest.get("source_commit") != expected_source_commit:
        raise ExecutionToolingManifestError("execution tooling source commit differs from authorization")
    files = manifest.get("files")
    if not isinstance(files, list) or manifest.get("file_count") != len(files):
        raise ExecutionToolingManifestError("execution tooling file count mismatch")
    if manifest.get("aggregate_algorithm") != AGGREGATE_ALGORITHM or manifest.get("aggregate_sha256") != _aggregate_sha256(manifest):
        raise ExecutionToolingManifestError("execution tooling aggregate mismatch")
    paths = [row.get("path") for row in files if isinstance(row, dict)]
    if (
        len(paths) != len(files)
        or paths != sorted(paths)
        or len(set(paths)) != len(paths)
        or len({str(path).casefold() for path in paths}) != len(paths)
    ):
        raise ExecutionToolingManifestError("execution tooling paths must be unique and sorted")
    return copy.deepcopy(manifest)


def verify_execution_tooling_manifest(
    *,
    root: Path,
    manifest: object,
    expected_source_commit: str,
    verify_git: bool = True,
) -> dict[str, Any]:
    """Verify shape, exact Stage07 membership, Git blobs, and current working bytes."""

    source_root = root.resolve(strict=True)
    validated = validate_execution_tooling_manifest_identity(
        manifest=manifest,
        expected_source_commit=expected_source_commit,
        schema_root=source_root,
    )
    files = validated["files"]
    paths = [row["path"] for row in files]
    _plan, sources, membership, result_order = _plan_inventory(source_root)
    if manifest.get("membership") != membership or manifest.get("result_order") != result_order:
        raise ExecutionToolingManifestError("execution tooling Stage07 profile membership drift")
    if paths != sorted(sources):
        raise ExecutionToolingManifestError("execution tooling file membership drift")
    if verify_git:
        _git_commit_exists(source_root, expected_source_commit)
        if manifest.get("source_tree") != _source_tree(source_root, expected_source_commit):
            raise ExecutionToolingManifestError("execution tooling source tree differs from source commit")
        tree = _tree_index(source_root, expected_source_commit)
        if paths != _governed_tree_paths(tree, membership):
            raise ExecutionToolingManifestError(
                "execution tooling file membership drift between source commit and working inventory"
            )
        missing = [path for path in paths if path not in tree]
        if missing:
            raise ExecutionToolingManifestError(f"execution tooling path absent from source commit: {missing[0]}")
        metadata = [tree[path] for path in paths]
        blobs = _batch_blobs(source_root, [oid for _mode, oid, _size in metadata])
    else:
        metadata = [(str(row["git_mode"]), str(row["blob_oid"]), int(row["byte_count"])) for row in files]
        blobs = [b""] * len(files)
    for row, path, (mode, oid, size), blob in zip(files, paths, metadata, blobs):
        if row["git_mode"] != mode or row["blob_oid"] != oid or row["byte_count"] != size:
            raise ExecutionToolingManifestError(f"execution tooling Git identity drift at {path}")
        if verify_git and (len(blob) != size or row["sha256"] != _sha256(blob)):
            raise ExecutionToolingManifestError(f"execution tooling Git blob drift at {path}")
        live = _stable_bytes(sources[path], f"execution tooling source {path}")
        if len(live) != row["byte_count"] or _sha256(live) != row["sha256"]:
            raise ExecutionToolingManifestError(f"execution tooling working byte drift at {path}")
    return validated


def execution_snapshot_projection(manifest: Mapping[str, Any]) -> list[dict[str, object]]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ExecutionToolingManifestError("execution tooling files are unavailable for snapshot projection")
    return [
        {"path": row["path"], "sha256": row["sha256"], "bytes": row["byte_count"]}
        for row in files
    ]


def verify_execution_snapshot_projection(
    manifest: Mapping[str, Any],
    snapshot_manifest: object,
) -> None:
    projected = execution_snapshot_projection(manifest)
    snapshot_payload = (
        json.dumps(projected, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    expected = {
        "schema": "daee-checker-execution-snapshot-v1",
        "sha256": hashlib.sha256(snapshot_payload).hexdigest(),
        "file_count": len(projected),
        "files": projected,
    }
    if snapshot_manifest != expected:
        raise ExecutionToolingManifestError("private execution snapshot differs from authorized tooling manifest")


def load_and_verify_execution_tooling_manifest(
    *,
    root: Path,
    manifest_ref: object,
    expected_source_commit: str,
    verify_git: bool = True,
) -> dict[str, Any]:
    source_root = root.resolve(strict=True)
    if not isinstance(manifest_ref, dict) or set(manifest_ref) != {"path", "byte_count", "sha256"}:
        raise ExecutionToolingManifestError("execution tooling manifest ref shape invalid")
    relative = manifest_ref.get("path")
    byte_count = manifest_ref.get("byte_count")
    digest = manifest_ref.get("sha256")
    if (
        not isinstance(relative, str)
        or not isinstance(byte_count, int)
        or isinstance(byte_count, bool)
        or byte_count < 1
        or not isinstance(digest, str)
        or SHA256_RE.fullmatch(digest) is None
    ):
        raise ExecutionToolingManifestError("execution tooling manifest ref values invalid")
    path = _contained(source_root, relative, "execution tooling manifest", must_exist=True, expect_file=True)
    raw = _stable_bytes(path, "execution tooling manifest")
    if len(raw) != byte_count or _sha256(raw) != digest:
        raise ExecutionToolingManifestError("execution tooling manifest content address mismatch")
    try:
        manifest = json.loads(raw.decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExecutionToolingManifestError("execution tooling manifest is not strict JSON") from exc
    if not isinstance(manifest, dict) or raw != _canonical(manifest):
        raise ExecutionToolingManifestError("execution tooling manifest must be canonical JSON")
    return verify_execution_tooling_manifest(
        root=source_root,
        manifest=manifest,
        expected_source_commit=expected_source_commit,
        verify_git=verify_git,
    )


def publish_execution_tooling_manifest(
    *,
    root: Path,
    source_commit: str,
    output_path: str | Path,
) -> dict[str, object]:
    """Create one immutable external authorization input; replacement is forbidden."""

    source_root = root.resolve(strict=True)
    manifest = build_execution_tooling_manifest(root=source_root, source_commit=source_commit)
    raw = _canonical(manifest)
    target = _contained(source_root, output_path, "execution tooling manifest output", must_exist=False)
    if not target.parent.is_dir():
        raise ExecutionToolingManifestError("execution tooling manifest output parent must already exist")
    try:
        with target.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ExecutionToolingManifestError("execution tooling manifest already exists") from exc
    except Exception:
        target.unlink(missing_ok=True)
        raise
    if _stable_bytes(target, "execution tooling manifest readback") != raw:
        target.unlink(missing_ok=True)
        raise ExecutionToolingManifestError("execution tooling manifest readback mismatch")
    return {
        "path": target.relative_to(source_root).as_posix(),
        "byte_count": len(raw),
        "sha256": _sha256(raw),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        ref = publish_execution_tooling_manifest(
            root=args.root,
            source_commit=args.source_commit,
            output_path=args.out,
        )
    except (ExecutionToolingManifestError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "status": "FAIL"}, sort_keys=True))
        return 1
    print(json.dumps({"manifest": ref, "status": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
