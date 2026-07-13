#!/usr/bin/env python3
"""Export one authorization-bound evidence inventory into immutable A16 custody."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import stat
import tempfile
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from a16_immutable_custody import (
    CustodyError,
    canonical_json_bytes,
    exclusive_writer_lock,
    publish_json_idempotent,
    resolve_contained_path,
    sha256_bytes,
    strict_snapshot,
)
from check_captured_output_manifest import PublicationError, _rename_directory_noreplace
from check_evidence_retention_manifest import (
    INVENTORY_ALGORITHM,
    NON_CLAIMS,
    PUBLICATION_MODE,
    RETENTION_POLICY,
    SCHEMA_ID,
    TREE_ALGORITHM,
    _alias,
    _contained_regular_snapshot,
    _is_reparse,
    _pointer_chain_findings,
    _relative_path_error,
    content_hash,
    custody_root_fingerprint,
    inventory_sha256,
    retained_tree_sha256,
    validate_export,
    validate_manifest,
)
ROOT = Path(__file__).resolve().parents[1]
AUTH_SCHEMA = "daee-evidence-export-authorization-v1"
AUTH_KIND = "evidence-export-authorization"
MANIFEST_KINDS = {
    "candidate-readiness-final-manifest",
    "observation-cycle-export",
    "final-reviewed-cycle-manifest",
}
CLASSIFICATIONS = {
    "RESTRICTED_RAW", "SANITIZED_REVIEW", "PUBLIC_FINGERPRINT", "CONTROL_RECORD"
}
_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_HEX64 = re.compile(r"^[a-f0-9]{64}$")
_HEX40 = re.compile(r"^[a-f0-9]{40}$")
_TIME = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_AUTH_FIELDS = {
    "schema", "kind", "manifest_kind", "export_id", "scope_id", "one_use",
    "issued_at", "exported_at", "source_root", "evidence_custody_root",
    "staging_path", "claim_path", "final_path", "receipt_path", "pointer_path",
    "expected_pointer_sha256", "source_identity", "candidate_identity",
    "cycle_identity", "inventory_spec", "retention_policy",
    "model_execution_authorized", "terminal_claim", "non_claims",
    "authorization_sha256",
}
_SPEC_FIELDS = {
    "artifact_id", "source_path", "retained_path", "classification", "required",
    "expected_state",
}


class ExportError(ValueError):
    """Fail-closed evidence-export error with a stable diagnostic subcode."""

    def __init__(self, message: str, *, subcode: str) -> None:
        super().__init__(message)
        self.subcode = subcode


def _fail(message: str, subcode: str) -> ExportError:
    return ExportError(message, subcode=subcode)


def _canonical_ref(path: str, raw: bytes) -> dict[str, Any]:
    return {"path": path, "sha256": sha256_bytes(raw), "byte_count": len(raw)}


def _reject_reparse_chain(path: Path, *, label: str) -> None:
    current = Path(path.anchor)
    parts = path.parts[1:] if path.anchor else path.parts
    for part in parts:
        current /= part
        if not current.exists():
            break
        try:
            if _is_reparse(current):
                raise _fail(f"{label} traverses a symlink or reparse point: {current}", "root-reparse")
        except OSError as exc:
            raise _fail(f"{label} path custody inspection failed: {current}: {exc}", "root-resolution") from exc


def _ensure_absolute_root(raw: Any, *, label: str, must_exist: bool) -> Path:
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise _fail(f"{label} must be a nonempty absolute path", "root-shape")
    candidate = Path(raw)
    if not candidate.is_absolute():
        raise _fail(f"{label} must be absolute", "root-absolute")
    _reject_reparse_chain(candidate, label=label)
    try:
        resolved = candidate.resolve(strict=must_exist)
    except OSError as exc:
        raise _fail(f"{label} cannot be resolved: {exc}", "root-resolution") from exc
    if must_exist:
        if _is_reparse(resolved) or not resolved.is_dir():
            raise _fail(f"{label} must be a non-reparse directory", "root-directory")
    return resolved


def _ensure_custody_root(path: Path) -> Path:
    if path.exists():
        if _is_reparse(path) or not path.is_dir():
            raise _fail("evidence custody root is not a regular directory", "custody-root")
    else:
        parent = path.parent.resolve(strict=True)
        if _is_reparse(parent) or not parent.is_dir():
            raise _fail("evidence custody parent is not a regular directory", "custody-parent")
        try:
            os.mkdir(path, 0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise _fail(f"evidence custody root create-if-absent failed: {exc}", "custody-create") from exc
    resolved = path.resolve(strict=True)
    if resolved != path.resolve(strict=False) or _is_reparse(resolved) or not resolved.is_dir():
        raise _fail("evidence custody root identity changed during creation", "custody-root-identity")
    try:
        os.chmod(resolved, 0o700)
    except OSError as exc:
        raise _fail(f"evidence custody root could not be made private: {exc}", "custody-permissions") from exc
    return resolved


def _roots_disjoint(source: Path, custody: Path) -> None:
    try:
        source.relative_to(custody)
    except ValueError:
        pass
    else:
        raise _fail("source root must not be inside evidence custody", "root-overlap")
    try:
        custody.relative_to(source)
    except ValueError:
        pass
    else:
        raise _fail("evidence custody must not be inside source root", "root-overlap")


def _ensure_private_directory(root: Path, relative: str) -> Path:
    finding = _relative_path_error(relative, label="private directory")
    if finding:
        raise _fail(finding.message, finding.failure_subcode)
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.exists():
            if _is_reparse(current) or not current.is_dir():
                raise _fail(f"custody directory is not regular: {current}", "custody-directory")
        else:
            try:
                os.mkdir(current, 0o700)
            except FileExistsError:
                pass
            except OSError as exc:
                raise _fail(f"custody directory create failed: {current}: {exc}", "custody-directory") from exc
        try:
            os.chmod(current, 0o700)
        except OSError as exc:
            raise _fail(f"custody directory could not be made private: {current}: {exc}", "custody-permissions") from exc
    return resolve_contained_path(root, current, must_exist=True)


def _validate_existing_custody_chain(root: Path, relative: str) -> None:
    finding = _relative_path_error(relative, label="custody locator")
    if finding:
        raise _fail(finding.message, finding.failure_subcode)
    current = root
    parts = Path(relative).parts
    for index, part in enumerate(parts):
        current /= part
        try:
            current.lstat()
        except FileNotFoundError:
            return
        if _is_reparse(current):
            raise _fail(f"custody locator traverses symlink or reparse content: {current}", "custody-reparse")
        if index < len(parts) - 1 and not current.is_dir():
            raise _fail(f"custody locator parent is not a directory: {current}", "custody-directory")


def _stream_snapshot(path: Path) -> tuple[str, int]:
    if _is_reparse(path) or not path.is_file():
        raise _fail(f"source artifact is not a regular non-reparse file: {path}", "source-regular-file")
    before = path.stat(follow_symlinks=False)
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
    except OSError as exc:
        raise _fail(f"source artifact read failed: {path}: {exc}", "source-read") from exc
    after = path.stat(follow_symlinks=False)
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or size != after.st_size:
        raise _fail(f"source artifact changed during custody snapshot: {path}", "source-drift")
    return digest.hexdigest(), size


def _walk_source(root: Path) -> dict[str, tuple[Path, str, int]]:
    found: dict[str, tuple[Path, str, int]] = {}

    def visit(directory: Path) -> None:
        if _is_reparse(directory):
            raise _fail(f"source tree contains a symlink or reparse directory: {directory}", "source-reparse")
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise _fail(f"source directory read failed: {directory}: {exc}", "source-read") from exc
        for entry in entries:
            path = Path(entry.path)
            if _is_reparse(path):
                raise _fail(f"source tree contains symlink or reparse content: {path}", "source-reparse")
            if entry.is_dir(follow_symlinks=False):
                visit(path)
            elif entry.is_file(follow_symlinks=False):
                relative = path.relative_to(root).as_posix()
                finding = _relative_path_error(relative, label="source inventory path")
                if finding:
                    raise _fail(finding.message, finding.failure_subcode)
                found[relative] = (path, *_stream_snapshot(path))
            else:
                raise _fail(f"source tree contains non-regular content: {path}", "source-regular-file")

    visit(root)
    return found


def _identity_shape(value: Any, *, candidate: bool) -> None:
    if not isinstance(value, dict):
        raise _fail("source/candidate identity must be an object", "identity-shape")
    if candidate:
        keys = {"candidate_id", "candidate_record", "candidate_readiness", "package_sha256", "package_tree_sha256", "tree_digest_algorithm", "status"}
        if set(value) != keys or not _ID.fullmatch(str(value.get("candidate_id", ""))):
            raise _fail("candidate identity has the wrong closed shape", "candidate-identity")
        if value.get("status") != "READY_UNUSED" or value.get("tree_digest_algorithm") != "daee-tree-sha256-v1":
            raise _fail("candidate identity is not the exact unused candidate boundary", "candidate-state")
        if not _HEX64.fullmatch(str(value.get("package_sha256", ""))) or not _HEX64.fullmatch(str(value.get("package_tree_sha256", ""))):
            raise _fail("candidate package hashes are invalid", "candidate-hash")
        refs = (value.get("candidate_record"), value.get("candidate_readiness"))
    else:
        keys = {"repository", "branch", "ref", "commit_sha", "tree_sha", "source_commit_receipt", "ci_readback"}
        if set(value) != keys or value.get("ref") != f"refs/heads/{value.get('branch')}":
            raise _fail("source identity has the wrong closed branch/ref shape", "source-identity")
        if not _HEX40.fullmatch(str(value.get("commit_sha", ""))) or not _HEX40.fullmatch(str(value.get("tree_sha", ""))):
            raise _fail("source commit/tree OIDs are invalid", "source-oid")
        refs = (value.get("source_commit_receipt"), value.get("ci_readback"))
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) != {"path", "sha256", "byte_count"}:
            raise _fail("identity artifact reference has the wrong shape", "identity-reference")
        finding = _relative_path_error(ref.get("path"), label="identity reference path")
        if finding or not _HEX64.fullmatch(str(ref.get("sha256", ""))) or not isinstance(ref.get("byte_count"), int) or isinstance(ref.get("byte_count"), bool) or ref["byte_count"] < 0:
            raise _fail("identity artifact reference is invalid", "identity-reference")


def _validate_authorization(value: Any, raw: bytes) -> tuple[Path, Path, list[dict[str, Any]]]:
    if not isinstance(value, dict) or set(value) != _AUTH_FIELDS:
        raise _fail("evidence export authorization has the wrong closed shape", "authorization-shape")
    if value.get("schema") != AUTH_SCHEMA or value.get("kind") != AUTH_KIND:
        raise _fail("evidence export authorization family is unsupported", "authorization-family")
    if value.get("manifest_kind") not in MANIFEST_KINDS:
        raise _fail("evidence export manifest kind is unsupported", "manifest-kind")
    for field in ("export_id", "scope_id"):
        if not isinstance(value.get(field), str) or not _ID.fullmatch(value[field]):
            raise _fail(f"authorization {field} is invalid", "authorization-id")
    if value.get("one_use") is not True or value.get("terminal_claim") is not False:
        raise _fail("authorization must be one-use and nonterminal", "authorization-one-use")
    if value.get("model_execution_authorized") is not False or value.get("non_claims") != NON_CLAIMS:
        raise _fail("authorization exceeds the no-model/nonclaim boundary", "authorization-boundary")
    if value.get("retention_policy") != RETENTION_POLICY:
        raise _fail("authorization does not bind indefinite retention", "retention-policy")
    for field in ("issued_at", "exported_at"):
        if not isinstance(value.get(field), str) or not _TIME.fullmatch(value[field]):
            raise _fail(f"authorization {field} is invalid", "authorization-time")
    if value.get("authorization_sha256") != content_hash(value, "authorization_sha256"):
        raise _fail("authorization content hash differs from canonical bytes", "authorization-hash")
    if raw != canonical_json_bytes(value):
        raise _fail("authorization must use canonical final-LF JSON bytes", "authorization-canonical")
    _identity_shape(value.get("source_identity"), candidate=False)
    _identity_shape(value.get("candidate_identity"), candidate=True)

    cycle = value.get("cycle_identity")
    if value["manifest_kind"] == "candidate-readiness-final-manifest":
        if cycle is not None or value["scope_id"] != value["candidate_identity"]["candidate_id"]:
            raise _fail("candidate retention scope/cycle identity is invalid", "candidate-scope")
    else:
        if not isinstance(cycle, dict) or set(cycle) != {"cycle_id", "cycle_claim", "phase"}:
            raise _fail("cycle export identity has the wrong closed shape", "cycle-identity")
        expected_phase = "OBSERVATION" if value["manifest_kind"] == "observation-cycle-export" else "REVIEWED_FINAL"
        if cycle.get("cycle_id") != value["scope_id"] or cycle.get("phase") != expected_phase:
            raise _fail("cycle identity/scope/phase differs from manifest kind", "cycle-scope")
        cycle_ref = cycle.get("cycle_claim")
        if not isinstance(cycle_ref, dict) or set(cycle_ref) != {"path", "sha256", "byte_count"}:
            raise _fail("cycle claim reference has the wrong closed shape", "cycle-reference")
        finding = _relative_path_error(cycle_ref.get("path"), label="cycle claim reference path")
        if finding or not _HEX64.fullmatch(str(cycle_ref.get("sha256", ""))) or not isinstance(cycle_ref.get("byte_count"), int) or isinstance(cycle_ref.get("byte_count"), bool) or cycle_ref["byte_count"] < 0:
            raise _fail("cycle claim reference is invalid", "cycle-reference")

    export_id = value["export_id"]
    scope_id = value["scope_id"]
    expected = {
        "staging_path": f".staging/{export_id}",
        "claim_path": f"claims/{export_id}.json",
        "receipt_path": f"receipts/{export_id}.json",
        "pointer_path": f"pointers/{scope_id}/head.json",
    }
    for field in ("staging_path", "claim_path", "final_path", "receipt_path", "pointer_path"):
        finding = _relative_path_error(value.get(field), label=f"authorization.{field}")
        if finding:
            raise _fail(finding.message, finding.failure_subcode)
        if field in expected and value[field] != expected[field]:
            raise _fail(f"authorization {field} differs from deterministic locator", "authorization-locator")
    expected_final = (
        f"candidates/{value['candidate_identity']['candidate_id']}/retention/{export_id}"
        if value["manifest_kind"] == "candidate-readiness-final-manifest"
        else f"cycles/{value['cycle_identity']['cycle_id']}/exports/{export_id}"
    )
    if value["final_path"] != expected_final:
        raise _fail("authorization final path differs from exact candidate/cycle export locator", "authorization-locator")
    predecessor = value.get("expected_pointer_sha256")
    if predecessor is not None and (not isinstance(predecessor, str) or not _HEX64.fullmatch(predecessor)):
        raise _fail("expected pointer predecessor must be null or lowercase SHA-256", "pointer-predecessor")

    source_root = _ensure_absolute_root(value.get("source_root"), label="source_root", must_exist=True)
    custody_root = _ensure_absolute_root(value.get("evidence_custody_root"), label="evidence_custody_root", must_exist=False)
    _roots_disjoint(source_root, custody_root)
    specs = value.get("inventory_spec")
    if not isinstance(specs, list) or not specs:
        raise _fail("authorization inventory_spec must be a nonempty array", "inventory-shape")
    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    seen_retained: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for spec in specs:
        if not isinstance(spec, dict) or set(spec) != _SPEC_FIELDS:
            raise _fail("inventory specification row has the wrong closed shape", "inventory-shape")
        artifact_id = spec.get("artifact_id")
        if not isinstance(artifact_id, str) or not _ID.fullmatch(artifact_id) or artifact_id in seen_ids:
            raise _fail("inventory artifact IDs must be unique portable identifiers", "inventory-id")
        seen_ids.add(artifact_id)
        for field, seen in (("source_path", seen_sources), ("retained_path", seen_retained)):
            finding = _relative_path_error(spec.get(field), label=f"inventory.{artifact_id}.{field}")
            if finding:
                raise _fail(finding.message, finding.failure_subcode)
            alias = _alias(spec[field])
            if alias in seen:
                raise _fail(f"inventory {field} aliases another path", "inventory-path-alias")
            seen.add(alias)
        if spec.get("classification") not in CLASSIFICATIONS or not isinstance(spec.get("required"), bool) or spec.get("expected_state") not in {"PRESENT", "ABSENT"}:
            raise _fail("inventory row classification/required/state is invalid", "inventory-row")
        normalized.append(copy.deepcopy(spec))
    return source_root, custody_root, normalized


def _snapshot_inventory(source_root: Path, specs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, tuple[Path, str, int]]]:
    source_files = _walk_source(source_root)
    declared_present = {spec["source_path"] for spec in specs if spec["expected_state"] == "PRESENT"}
    unlisted = sorted(set(source_files) - declared_present)
    if unlisted:
        raise _fail(f"full inventory has unlisted source artifacts: {unlisted}", "inventory-unlisted")
    missing_declared = sorted(declared_present - set(source_files))
    if missing_declared:
        raise _fail(f"inventory declares PRESENT artifacts that are missing: {missing_declared}", "inventory-missing-present")
    rows: list[dict[str, Any]] = []
    for spec in specs:
        exists = spec["source_path"] in source_files
        expected = spec["expected_state"] == "PRESENT"
        if exists != expected:
            state = "present" if exists else "absent"
            raise _fail(f"inventory expected state drift for {spec['artifact_id']}: observed {state}", "inventory-state-drift")
        row = {
            "artifact_id": spec["artifact_id"],
            "source_path": spec["source_path"],
            "retained_path": spec["retained_path"],
            "classification": spec["classification"],
            "required": spec["required"],
            "present": exists,
            "sha256": None,
            "byte_count": None,
            "cas_object_path": None,
        }
        if exists:
            _path, digest, byte_count = source_files[spec["source_path"]]
            row.update(
                sha256=digest,
                byte_count=byte_count,
                cas_object_path=f"objects/sha256/{digest[:2]}/{digest}",
            )
        rows.append(row)
    rows.sort(key=lambda item: item["artifact_id"])
    return rows, source_files


def _copy_source_to_cas(source: Path, target: Path, expected_sha: str, expected_size: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if _is_reparse(target.parent) or not target.parent.is_dir():
        raise _fail("CAS object parent is not a regular directory", "cas-parent")
    if target.exists():
        observed_sha, observed_size = _stream_snapshot(target)
        if observed_sha != expected_sha or observed_size != expected_size:
            raise _fail(f"CAS object collision for {expected_sha}", "cas-collision")
        return
    temporary = target.parent / f".{target.name}.stage-{uuid.uuid4().hex}"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    digest = hashlib.sha256()
    size = 0
    before = source.stat(follow_symlinks=False)
    try:
        with source.open("rb") as read_handle, os.fdopen(descriptor, "wb", closefd=True) as write_handle:
            while chunk := read_handle.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
                write_handle.write(chunk)
            write_handle.flush()
            os.fsync(write_handle.fileno())
        after = source.stat(follow_symlinks=False)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise _fail(f"source changed while publishing CAS object: {source}", "source-drift")
        if digest.hexdigest() != expected_sha or size != expected_size:
            raise _fail(f"source bytes differ from frozen inventory: {source}", "source-drift")
        try:
            os.link(temporary, target)
        except FileExistsError:
            pass
        except OSError as exc:
            raise _fail(f"CAS no-replace publication failed: {exc}", "cas-publication") from exc
        observed_sha, observed_size = _stream_snapshot(target)
        if observed_sha != expected_sha or observed_size != expected_size:
            raise _fail(f"CAS object readback differs for {expected_sha}", "cas-readback")
    finally:
        temporary.unlink(missing_ok=True)


def _verify_source_snapshot(source_root: Path, frozen: dict[str, tuple[Path, str, int]]) -> None:
    current = _walk_source(source_root)
    if set(current) != set(frozen):
        raise _fail("source inventory changed before final publication", "source-drift")
    for relative, (_path, digest, size) in frozen.items():
        if current[relative][1:] != (digest, size):
            raise _fail(f"source artifact drifted before final publication: {relative}", "source-drift")


def _write_exact_new_or_resume(path: Path, raw: bytes, *, label: str) -> None:
    if path.exists():
        if _is_reparse(path) or not path.is_file() or path.read_bytes() != raw:
            raise _fail(f"{label} hash-equal resume collision at {path}", f"{label}-collision")
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise
    if path.read_bytes() != raw:
        raise _fail(f"{label} readback differs after create-if-absent", f"{label}-readback")


def _read_pointer(root: Path, relative: str) -> tuple[dict[str, Any] | None, bytes, str | None]:
    finding = _relative_path_error(relative, label="pointer head path")
    if finding:
        raise _fail(finding.message, finding.failure_subcode)
    lexical = root.joinpath(*PurePosixPath(relative).parts)
    try:
        lexical.lstat()
    except FileNotFoundError:
        return None, b"", None
    try:
        value, raw, file_sha = _contained_regular_snapshot(
            root,
            relative,
            label="pointer head",
        )
    except (CustodyError, OSError, ValueError) as exc:
        raise _fail(f"pointer head readback failed: {exc}", "pointer-readback") from exc
    required = {
        "schema", "scope_id", "sequence", "export_id", "manifest", "claim_receipt",
        "authorization_sha256", "source_commit", "candidate_id", "status",
        "predecessor_pointer_sha256", "pointer_sha256",
    }
    if set(value) != required or value.get("schema") != "daee-evidence-retention-pointer-v1":
        raise _fail("pointer head has the wrong closed shape", "pointer-shape")
    if value.get("pointer_sha256") != content_hash(value, "pointer_sha256"):
        raise _fail("pointer head content hash drifted", "pointer-hash")
    record_relative = f"pointers/{value['scope_id']}/records/{value['pointer_sha256']}.json"
    record_value, record_raw, record_file_sha = _contained_regular_snapshot(
        root,
        record_relative,
        label="current immutable pointer record",
    )
    if record_value != value or record_raw != raw or record_file_sha != file_sha:
        raise _fail("pointer head differs from immutable pointer record", "pointer-record-drift")
    return value, raw, file_sha


def _validate_complete_historical_receipts(root: Path, head: Mapping[str, Any]) -> None:
    current = dict(head)
    seen: set[str] = set()
    while True:
        pointer_sha = str(current.get("pointer_sha256"))
        if pointer_sha in seen:
            raise _fail("historical pointer receipt traversal encountered a cycle", "pointer-history-cycle")
        seen.add(pointer_sha)
        manifest_ref = current.get("manifest")
        if not isinstance(manifest_ref, dict):
            raise _fail("historical pointer lacks a manifest reference", "pointer-history-manifest")
        manifest_path = manifest_ref.get("path")
        finding = _relative_path_error(manifest_path, label="historical manifest path")
        if finding or not str(manifest_path).endswith("/manifest.json"):
            raise _fail("historical pointer has an invalid manifest locator", "pointer-history-manifest")
        final_directory = Path(str(PurePosixPath(str(manifest_path)).parent))
        findings = validate_export(root, final_directory)
        if findings:
            raise _fail(
                f"historical receipt chain is incomplete at {current.get('export_id')}: {findings[0].message}",
                "pointer-history-receipt",
            )
        predecessor = current.get("predecessor_pointer_sha256")
        if predecessor is None:
            return
        record_relative = f"pointers/{current['scope_id']}/records/{predecessor}.json"
        try:
            current, _raw, _file_sha = _contained_regular_snapshot(
                root,
                record_relative,
                label="historical immutable pointer record",
            )
        except (CustodyError, OSError, ValueError) as exc:
            raise _fail(f"historical pointer record readback failed: {exc}", "pointer-history-record") from exc


def _advance_pointer(
    root: Path,
    relative: str,
    pointer: dict[str, Any],
    current_raw: bytes,
    *,
    fault_at: str | None = None,
) -> tuple[bytes, str]:
    raw = canonical_json_bytes(pointer)
    record_relative = f"pointers/{pointer['scope_id']}/records/{pointer['pointer_sha256']}.json"
    record_path = resolve_contained_path(root, record_relative)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    _validate_existing_custody_chain(root, record_relative)
    publish_json_idempotent(root, record_path, pointer)
    record_value, record_raw, record_file_sha = _contained_regular_snapshot(
        root,
        record_relative,
        label="published immutable pointer record",
    )
    if record_value != pointer or record_raw != raw:
        raise _fail("immutable pointer record readback differs", "pointer-record-readback")
    _fault(fault_at, "pointer-record")

    _validate_existing_custody_chain(root, relative)
    head = resolve_contained_path(root, relative)
    if current_raw:
        if not head.exists() or head.read_bytes() != current_raw:
            raise _fail("pointer head changed before CAS advance", "pointer-cas-conflict")
        descriptor, temporary = tempfile.mkstemp(prefix=".head.", suffix=".tmp", dir=head.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            if head.read_bytes() != current_raw:
                raise _fail("pointer head changed during CAS advance", "pointer-cas-conflict")
            os.replace(temporary, head)
            temporary = ""
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
    else:
        try:
            publish_json_idempotent(root, head, pointer)
        except CustodyError as exc:
            raise _fail(f"pointer create-if-absent failed: {exc}", "pointer-cas-conflict") from exc
    if head.read_bytes() != raw:
        raise _fail("pointer head readback differs after CAS advance", "pointer-readback")
    return record_raw, record_file_sha


def _fault(fault_at: str | None, point: str) -> None:
    if fault_at in {point, f"after-{point}"}:
        raise RuntimeError(f"injected retention export failure after {point.replace('-', ' ')}")


def _claim(value: Mapping[str, Any], authorization_file_sha: str) -> dict[str, Any]:
    return {
        "schema": "daee-evidence-export-claim-v1",
        "kind": "evidence-export-claim",
        "export_id": value["export_id"],
        "scope_id": value["scope_id"],
        "manifest_kind": value["manifest_kind"],
        "authorization_sha256": value["authorization_sha256"],
        "authorization_file_sha256": authorization_file_sha,
        "source_commit": value["source_identity"]["commit_sha"],
        "candidate_id": value["candidate_identity"]["candidate_id"],
        "cycle_id": value["cycle_identity"]["cycle_id"] if value["cycle_identity"] else None,
        "claimed_at": value["issued_at"],
        "one_use": True,
        "model_execution_authorized": False,
        "terminal_claim": False,
        "non_claims": list(NON_CLAIMS),
    }


def _build_manifest(
    value: Mapping[str, Any], authorization_file_sha: str, claim_ref: Mapping[str, Any],
    rows: list[dict[str, Any]], custody_root: Path,
) -> dict[str, Any]:
    missing = sorted(row["artifact_id"] for row in rows if row["required"] and not row["present"])
    if missing and value["manifest_kind"] != "observation-cycle-export":
        raise _fail(f"final retention manifest has missing required artifacts: {missing}", "final-required-missing")
    completeness = "PARTIAL" if missing else "COMPLETE"
    status = "RETENTION_PARTIAL" if missing else "RETENTION_GREEN"
    manifest = {
        "schema": SCHEMA_ID,
        "kind": value["manifest_kind"],
        "status": status,
        "export_id": value["export_id"],
        "scope_id": value["scope_id"],
        "authorization_sha256": value["authorization_sha256"],
        "authorization_file_sha256": authorization_file_sha,
        "claim_receipt": copy.deepcopy(claim_ref),
        "source_identity": copy.deepcopy(value["source_identity"]),
        "candidate_identity": copy.deepcopy(value["candidate_identity"]),
        "cycle_identity": copy.deepcopy(value["cycle_identity"]),
        "inventory": copy.deepcopy(rows),
        "inventory_digest_algorithm": INVENTORY_ALGORITHM,
        "inventory_sha256": inventory_sha256(rows),
        "retained_tree_digest_algorithm": TREE_ALGORITHM,
        "retained_tree_sha256": retained_tree_sha256(rows),
        "cas_object_count": len({row["sha256"] for row in rows if row["present"]}),
        "retained_byte_count": sum(row["byte_count"] for row in rows if row["present"]),
        "cas_readback_status": "PASS",
        "publication_mode": PUBLICATION_MODE,
        "completeness": completeness,
        "missing_required_artifact_ids": missing,
        "retention_policy": copy.deepcopy(value["retention_policy"]),
        "custody": {
            "root_fingerprint_sha256": custody_root_fingerprint(custody_root),
            "object_store_path": "objects/sha256",
            "staging_path": value["staging_path"],
            "claim_path": value["claim_path"],
            "final_path": value["final_path"],
            "receipt_path": value["receipt_path"],
            "pointer_path": value["pointer_path"],
            "expected_pointer_sha256": value["expected_pointer_sha256"],
        },
        "exported_at": value["exported_at"],
        "model_execution_authorized": False,
        "terminal_claim": False,
        "non_claims": list(NON_CLAIMS),
    }
    manifest["manifest_sha256"] = content_hash(manifest, "manifest_sha256")
    findings = validate_manifest(manifest)
    if findings:
        finding = findings[0]
        raise _fail(f"generated manifest failed validation: {finding.message}", finding.failure_subcode)
    return manifest


def _final_exact(final: Path, manifest_raw: bytes, claim_raw: bytes) -> bool:
    if not final.exists():
        return False
    if _is_reparse(final) or not final.is_dir():
        raise _fail("final publication target is not a regular directory", "final-collision")
    entries = sorted(path.name for path in final.iterdir())
    if entries != ["export-claim.json", "manifest.json"]:
        raise _fail(f"final publication has partial/unexpected members: {entries}", "partial-publication")
    manifest_path = final / "manifest.json"
    claim_path = final / "export-claim.json"
    if _is_reparse(manifest_path) or _is_reparse(claim_path):
        raise _fail("final publication contains symlink or reparse JSON members", "final-reparse")
    if manifest_path.read_bytes() != manifest_raw or claim_path.read_bytes() != claim_raw:
        raise _fail("final publication collision differs from exact resumable bytes", "final-collision")
    return True


def _build_pointer(value: Mapping[str, Any], manifest: Mapping[str, Any], manifest_ref: Mapping[str, Any], claim_ref: Mapping[str, Any], sequence: int) -> dict[str, Any]:
    pointer = {
        "schema": "daee-evidence-retention-pointer-v1",
        "scope_id": value["scope_id"],
        "sequence": sequence,
        "export_id": value["export_id"],
        "manifest": copy.deepcopy(manifest_ref),
        "claim_receipt": copy.deepcopy(claim_ref),
        "authorization_sha256": value["authorization_sha256"],
        "source_commit": value["source_identity"]["commit_sha"],
        "candidate_id": value["candidate_identity"]["candidate_id"],
        "status": manifest["status"],
        "predecessor_pointer_sha256": value["expected_pointer_sha256"],
    }
    pointer["pointer_sha256"] = content_hash(pointer, "pointer_sha256")
    return pointer


def _build_receipt(
    value: Mapping[str, Any], manifest: Mapping[str, Any], manifest_ref: Mapping[str, Any],
    claim_ref: Mapping[str, Any], pointer_ref: Mapping[str, Any], authorization_file_sha: str,
) -> dict[str, Any]:
    receipt = {
        "schema": SCHEMA_ID,
        "kind": "evidence-export-receipt",
        "status": manifest["status"],
        "export_id": value["export_id"],
        "scope_id": value["scope_id"],
        "authorization_sha256": value["authorization_sha256"],
        "authorization_file_sha256": authorization_file_sha,
        "claim_receipt": copy.deepcopy(claim_ref),
        "manifest": copy.deepcopy(manifest_ref),
        "pointer_record": copy.deepcopy(pointer_ref),
        "source_identity": copy.deepcopy(value["source_identity"]),
        "candidate_identity": copy.deepcopy(value["candidate_identity"]),
        "cycle_identity": copy.deepcopy(value["cycle_identity"]),
        "completeness": manifest["completeness"],
        "object_count": manifest["cas_object_count"],
        "retained_byte_count": manifest["retained_byte_count"],
        "retained_tree_sha256": manifest["retained_tree_sha256"],
        "final_path": value["final_path"],
        "pointer_path": value["pointer_path"],
        "expected_pointer_sha256": value["expected_pointer_sha256"],
        "final_readback_status": "PASS",
        "pointer_readback_status": "PASS",
        "published_at": value["exported_at"],
        "one_use": True,
        "terminal": True,
        "terminal_claim": False,
        "model_execution_authorized": False,
        "non_claims": list(NON_CLAIMS),
    }
    receipt["receipt_sha256"] = content_hash(receipt, "receipt_sha256")
    return receipt


def export_evidence_bundle(authorization_path: Path, *, fault_at: str | None = None) -> dict[str, Any]:
    """Create or exactly resume one immutable retained-evidence export."""
    try:
        value, authorization_raw, authorization_file_sha = strict_snapshot(Path(authorization_path))
    except (CustodyError, OSError, ValueError) as exc:
        raise _fail(f"authorization read failed: {exc}", "authorization-read") from exc
    source_root, custody_requested, specs = _validate_authorization(value, authorization_raw)
    rows, frozen_source = _snapshot_inventory(source_root, specs)

    # Validate completeness before creating a claim for an impossible final export.
    missing = [row["artifact_id"] for row in rows if row["required"] and not row["present"]]
    if missing and value["manifest_kind"] != "observation-cycle-export":
        raise _fail(f"final retention manifest has missing required artifacts: {missing}", "final-required-missing")

    custody_root = _ensure_custody_root(custody_requested)
    _roots_disjoint(source_root, custody_root)
    with exclusive_writer_lock(custody_root):
        _validate_existing_custody_chain(custody_root, value["pointer_path"])
        current, current_raw, _current_file_sha = _read_pointer(custody_root, value["pointer_path"])
        if current is not None:
            pointer_findings = _pointer_chain_findings(custody_root, current)
            if pointer_findings:
                finding = pointer_findings[0]
                raise _fail(f"pointer predecessor chain failed: {finding.message}", finding.failure_subcode)
        predecessor = value["expected_pointer_sha256"]
        current_sha = current["pointer_sha256"] if current else None
        if current is not None and current_sha == predecessor:
            _validate_complete_historical_receipts(custody_root, current)
        adopting_current = False
        if current_sha != predecessor:
            adopting_current = bool(
                current
                and current.get("export_id") == value["export_id"]
                and current.get("authorization_sha256") == value["authorization_sha256"]
                and current.get("predecessor_pointer_sha256") == predecessor
            )
            if not adopting_current:
                raise _fail(
                    f"pointer CAS predecessor/replay mismatch: expected {predecessor}, observed {current_sha}",
                    "pointer-cas-replay",
                )
        if adopting_current and predecessor is not None:
            predecessor_relative = f"pointers/{current['scope_id']}/records/{predecessor}.json"
            try:
                predecessor_pointer, _raw, _file_sha = _contained_regular_snapshot(
                    custody_root,
                    predecessor_relative,
                    label="adopted pointer predecessor record",
                )
            except (CustodyError, OSError, ValueError) as exc:
                raise _fail(
                    f"historical pointer record readback failed before resume: {exc}",
                    "pointer-history-record",
                ) from exc
            if predecessor_pointer.get("pointer_sha256") != predecessor:
                raise _fail(
                    "adopted pointer predecessor record has the wrong content hash",
                    "pointer-history-record",
                )
            _validate_complete_historical_receipts(custody_root, predecessor_pointer)

        claim = _claim(value, authorization_file_sha)
        claim_path = resolve_contained_path(custody_root, value["claim_path"])
        _ensure_private_directory(custody_root, str(Path(value["claim_path"]).parent).replace("\\", "/"))
        _validate_existing_custody_chain(custody_root, value["claim_path"])
        try:
            publish_json_idempotent(custody_root, claim_path, claim)
            _claim_value, claim_raw, claim_file_sha = _contained_regular_snapshot(
                custody_root,
                value["claim_path"],
                label="create-once export claim",
            )
        except (CustodyError, OSError, ValueError) as exc:
            raise _fail(f"create-once export claim collision/readback failed: {exc}", "claim-collision") from exc
        if _claim_value != claim:
            raise _fail("create-once export claim differs from authorization", "claim-collision")
        claim_ref = _canonical_ref(value["claim_path"], claim_raw)
        _fault(fault_at, "claim")

        object_index = 0
        for row in rows:
            if not row["present"]:
                continue
            _ensure_private_directory(custody_root, str(Path(row["cas_object_path"]).parent).replace("\\", "/"))
            _validate_existing_custody_chain(custody_root, row["cas_object_path"])
            object_path = custody_root.joinpath(*PurePosixPath(row["cas_object_path"]).parts)
            source_path = frozen_source[row["source_path"]][0]
            _copy_source_to_cas(source_path, object_path, row["sha256"], row["byte_count"])
            object_index += 1
            if object_index == 1:
                _fault(fault_at, "first-object")

        manifest = _build_manifest(value, authorization_file_sha, claim_ref, rows, custody_root)
        findings = validate_manifest(manifest, custody_root=custody_root)
        if findings:
            finding = findings[0]
            raise _fail(f"CAS readback failed before manifest staging: {finding.message}", finding.failure_subcode)
        manifest_raw = canonical_json_bytes(manifest)
        final = resolve_contained_path(custody_root, value["final_path"])
        _ensure_private_directory(custody_root, str(Path(value["final_path"]).parent).replace("\\", "/"))
        final_exists = _final_exact(final, manifest_raw, claim_raw)
        if not final_exists:
            stage = resolve_contained_path(custody_root, value["staging_path"])
            _ensure_private_directory(custody_root, ".staging")
            if stage.exists():
                if _is_reparse(stage) or not stage.is_dir():
                    raise _fail("private staging path is not a regular directory", "staging-collision")
            else:
                os.mkdir(stage, 0o700)
            unexpected = sorted(path.name for path in stage.iterdir() if path.name not in {"export-claim.json", "manifest.json"})
            if unexpected:
                raise _fail(f"private staging contains unexpected residue: {unexpected}", "staging-collision")
            _write_exact_new_or_resume(stage / "export-claim.json", claim_raw, label="staging-claim")
            _write_exact_new_or_resume(stage / "manifest.json", manifest_raw, label="staging-manifest")
            _fault(fault_at, "stage")
            _verify_source_snapshot(source_root, frozen_source)
            try:
                _rename_directory_noreplace(stage, final)
            except PublicationError as exc:
                if not _final_exact(final, manifest_raw, claim_raw):
                    raise _fail(f"atomic final no-replace publication failed: {exc}", "final-collision") from exc
            if not _final_exact(final, manifest_raw, claim_raw):
                raise _fail("atomic final publication readback failed", "final-readback")
        else:
            _verify_source_snapshot(source_root, frozen_source)
        _fault(fault_at, "final")

        _manifest_value, final_manifest_raw, final_manifest_file_sha = _contained_regular_snapshot(
            custody_root,
            f"{value['final_path']}/manifest.json",
            label="final manifest",
        )
        if _manifest_value != manifest or final_manifest_raw != manifest_raw:
            raise _fail("final manifest readback differs from staged bytes", "final-readback")
        manifest_ref = _canonical_ref(f"{value['final_path']}/manifest.json", final_manifest_raw)

        if adopting_current:
            sequence = current["sequence"]
        else:
            sequence = (current["sequence"] if current else 0) + 1
        desired_pointer = _build_pointer(value, manifest, manifest_ref, claim_ref, sequence)
        _ensure_private_directory(custody_root, f"pointers/{value['scope_id']}/records")
        if adopting_current:
            if current != desired_pointer:
                raise _fail("existing pointer for this export differs from exact resumable pointer", "pointer-cas-replay")
            pointer_record_relative = f"pointers/{value['scope_id']}/records/{desired_pointer['pointer_sha256']}.json"
            _pointer_record, pointer_record_raw, pointer_record_file_sha = _contained_regular_snapshot(
                custody_root,
                pointer_record_relative,
                label="adopted immutable pointer record",
            )
        else:
            pointer_record_raw, pointer_record_file_sha = _advance_pointer(
                custody_root,
                value["pointer_path"],
                desired_pointer,
                current_raw,
                fault_at=fault_at,
            )
            pointer_record_relative = f"pointers/{value['scope_id']}/records/{desired_pointer['pointer_sha256']}.json"
        _fault(fault_at, "pointer")
        pointer_ref = {
            "path": pointer_record_relative,
            "sha256": pointer_record_file_sha,
            "byte_count": len(pointer_record_raw),
        }
        receipt = _build_receipt(value, manifest, manifest_ref, claim_ref, pointer_ref, authorization_file_sha)
        receipt_path = resolve_contained_path(custody_root, value["receipt_path"])
        _ensure_private_directory(custody_root, str(Path(value["receipt_path"]).parent).replace("\\", "/"))
        _validate_existing_custody_chain(custody_root, value["receipt_path"])
        try:
            publish_json_idempotent(custody_root, receipt_path, receipt)
        except (CustodyError, OSError, ValueError) as exc:
            raise _fail(f"create-once export receipt collision/readback failed: {exc}", "receipt-collision") from exc
        _fault(fault_at, "receipt")
        findings = validate_export(custody_root, final)
        if findings:
            finding = findings[0]
            raise _fail(f"complete export readback failed: {finding.message}", finding.failure_subcode)
        return manifest


def _self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="daee-retention-export-self-test-") as directory:
        root = Path(directory)
        source = root / "source"
        source.mkdir()
        (source / "artifact.txt").write_bytes(b"retention self-test\n")
        identity_payloads = {
            "receipts/source.json": b'{"status":"source"}\n',
            "receipts/ci.json": b'{"status":"ci"}\n',
            "candidates/self-test-candidate/record.json": b'{"status":"READY_UNUSED"}\n',
            "candidates/self-test-candidate/readiness.json": b'{"status":"READY"}\n',
        }
        identity_refs: dict[str, dict[str, Any]] = {}
        for relative, payload in identity_payloads.items():
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            identity_refs[relative] = {"path": relative, "sha256": sha256_bytes(payload), "byte_count": len(payload)}
        custody = root / "custody"
        value = {
            "schema": AUTH_SCHEMA,
            "kind": AUTH_KIND,
            "manifest_kind": "candidate-readiness-final-manifest",
            "export_id": "self-test-export",
            "scope_id": "self-test-candidate",
            "one_use": True,
            "issued_at": "2026-07-12T12:00:00Z",
            "exported_at": "2026-07-12T12:01:00Z",
            "source_root": str(source.resolve()),
            "evidence_custody_root": str(custody.resolve()),
            "staging_path": ".staging/self-test-export",
            "claim_path": "claims/self-test-export.json",
            "final_path": "candidates/self-test-candidate/retention/self-test-export",
            "receipt_path": "receipts/self-test-export.json",
            "pointer_path": "pointers/self-test-candidate/head.json",
            "expected_pointer_sha256": None,
            "source_identity": {
                "repository": "theislampill/daee-epistemics", "branch": "branch", "ref": "refs/heads/branch",
                "commit_sha": "a" * 40, "tree_sha": "b" * 40,
                "source_commit_receipt": identity_refs["receipts/source.json"],
                "ci_readback": identity_refs["receipts/ci.json"],
            },
            "candidate_identity": {
                "candidate_id": "self-test-candidate",
                "candidate_record": identity_refs["candidates/self-test-candidate/record.json"],
                "candidate_readiness": identity_refs["candidates/self-test-candidate/readiness.json"],
                "package_sha256": "1" * 64, "package_tree_sha256": "2" * 64,
                "tree_digest_algorithm": "daee-tree-sha256-v1", "status": "READY_UNUSED",
            },
            "cycle_identity": None,
            "inventory_spec": [
                {
                    "artifact_id": "artifact", "source_path": "artifact.txt", "retained_path": "artifact.txt",
                    "classification": "CONTROL_RECORD", "required": True, "expected_state": "PRESENT",
                },
                *[
                    {
                        "artifact_id": artifact_id,
                        "source_path": relative,
                        "retained_path": relative,
                        "classification": "CONTROL_RECORD",
                        "required": True,
                        "expected_state": "PRESENT",
                    }
                    for artifact_id, relative in (
                        ("source-commit-receipt", "receipts/source.json"),
                        ("ci-readback", "receipts/ci.json"),
                        ("candidate-record", "candidates/self-test-candidate/record.json"),
                        ("candidate-readiness", "candidates/self-test-candidate/readiness.json"),
                    )
                ],
            ],
            "retention_policy": copy.deepcopy(RETENTION_POLICY),
            "model_execution_authorized": False,
            "terminal_claim": False,
            "non_claims": list(NON_CLAIMS),
        }
        value["authorization_sha256"] = content_hash(value, "authorization_sha256")
        authorization = root / "authorization.json"
        authorization.write_bytes(canonical_json_bytes(value))
        manifest = export_evidence_bundle(authorization)
        resumed = export_evidence_bundle(authorization)
        if manifest != resumed or manifest["status"] != "RETENTION_GREEN":
            print("retention export self-test: FAIL")
            return 1
    print("retention export self-test: PASS (private temporary custody only; no model/candidate/cycle execution)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--authorization")
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        if args.authorization:
            parser.error("--self-test cannot consume a live authorization")
        return _self_test()
    if not args.authorization:
        parser.error("--authorization is required")
    try:
        manifest = export_evidence_bundle(Path(args.authorization))
    except (ExportError, CustodyError, OSError, ValueError) as exc:
        subcode = getattr(exc, "subcode", "export-failed")
        payload = {"checker_id": "evidence-retention-export", "status": "FAIL", "failure_subcode": subcode, "message": str(exc), "terminal_claim": False}
        print(json.dumps(payload, sort_keys=True) if args.explain else f"evidence retention export: FAIL [{subcode}]: {exc}")
        return 1
    payload = {"checker_id": "evidence-retention-export", "status": manifest["status"], "export_id": manifest["export_id"], "manifest_sha256": manifest["manifest_sha256"], "terminal_claim": False}
    print(json.dumps(payload, sort_keys=True) if args.explain else f"evidence retention export: PASS {manifest['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
