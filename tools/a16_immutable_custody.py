#!/usr/bin/env python3
"""Shared A16 immutable JSON receipt and append-before-CAS custody primitives."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path, PureWindowsPath
from typing import Any, Iterator

from check_captured_output_manifest import PublicationError, atomic_publish_bytes
from source_provenance import DuplicateObjectKey, strict_json_loads


class CustodyError(ValueError):
    """Fail-closed A16 custody error with a stable diagnostic subcode."""

    def __init__(self, message: str, *, subcode: str) -> None:
        super().__init__(message)
        self.subcode = subcode


def canonical_json_bytes(value: Any) -> bytes:
    """Return canonical UTF-8 JSON with exactly one final LF."""

    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strict_snapshot(path: Path) -> tuple[dict[str, Any], bytes, str]:
    """Read one immutable JSON file once and reject noncanonical or duplicate-key bytes."""

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CustodyError(f"immutable JSON read failed: {path}: {exc}", subcode="read-failed") from exc
    try:
        value = strict_json_loads(raw, label=str(path))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        message = str(exc)
        subcode = "duplicate-key" if isinstance(exc, DuplicateObjectKey) else "malformed-json"
        raise CustodyError(f"immutable JSON rejected: {message}", subcode=subcode) from exc
    if not isinstance(value, dict):
        raise CustodyError("immutable JSON root must be an object", subcode="root-shape")
    if raw != canonical_json_bytes(value):
        raise CustodyError(
            f"immutable JSON is not canonical final-LF bytes: {path}",
            subcode="noncanonical-json",
        )
    return value, raw, sha256_bytes(raw)


def resolve_contained_path(root: Path, candidate: str | Path, *, must_exist: bool = False) -> Path:
    """Resolve a relative or absolute target and prove it stays beneath ``root``."""

    root_resolved = root.resolve(strict=True)
    raw = os.fspath(candidate)
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise CustodyError("path must be nonempty text", subcode="path-shape")
    windows = PureWindowsPath(raw)
    native = Path(raw)
    if not native.is_absolute() and (windows.is_absolute() or windows.drive):
        raise CustodyError(f"drive-qualified path is forbidden: {raw}", subcode="absolute-path")
    if ".." in PureWindowsPath(raw.replace("/", "\\")).parts:
        raise CustodyError(f"parent traversal is forbidden: {raw}", subcode="path-traversal")
    lexical = native if native.is_absolute() else root_resolved / native
    try:
        resolved = lexical.resolve(strict=must_exist)
    except FileNotFoundError as exc:
        raise CustodyError(f"required custody path is absent: {raw}", subcode="missing-path") from exc
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise CustodyError(
            f"custody path escapes root: {raw} -> {resolved}", subcode="path-escape"
        ) from exc
    return resolved


@contextmanager
def exclusive_writer_lock(root: Path) -> Iterator[None]:
    """Hold the one create-once writer lock for a custody root."""

    root.mkdir(parents=True, exist_ok=True)
    lock = resolve_contained_path(root, root / ".writer.lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise CustodyError("exclusive A16 writer lock is held", subcode="writer-lock") from exc
    acquired = None
    try:
        token = b"A16 immutable custody writer\n"
        if os.write(descriptor, token) != len(token):
            raise OSError("short writer-lock token write")
        os.fsync(descriptor)
        # Capture identity only after our own write/fsync has completed.  Some
        # filesystems update ctime for that write; a pre-write snapshot would
        # make an uncontended lock look replaced at release time.
        acquired = os.fstat(descriptor)
        yield
    finally:
        if acquired is None:
            acquired = os.fstat(descriptor)
        os.close(descriptor)
        try:
            current = lock.stat(follow_symlinks=False)
        except FileNotFoundError as exc:
            raise CustodyError(
                "writer lock disappeared before release",
                subcode="writer-lock-identity",
            ) from exc
        if (current.st_dev, current.st_ino, current.st_ctime_ns) != (
            acquired.st_dev,
            acquired.st_ino,
            acquired.st_ctime_ns,
        ):
            raise CustodyError(
                "writer lock identity changed; refusing to unlink competitor",
                subcode="writer-lock-identity",
            )
        lock.unlink()


def publish_json_idempotent(root: Path, target: Path, value: dict[str, Any]) -> tuple[str, bool]:
    """Publish no-replace; only byte-identical readback may resume successfully."""

    target = resolve_contained_path(root, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target = resolve_contained_path(root, target)
    raw = canonical_json_bytes(value)
    digest = sha256_bytes(raw)
    if target.exists():
        if not target.is_file() or target.read_bytes() != raw:
            raise CustodyError(
                f"immutable publication collision at {target}", subcode="publication-collision"
            )
        if sha256_bytes(target.read_bytes()) != digest:
            raise CustodyError("idempotent readback digest mismatch", subcode="readback-drift")
        return digest, False
    try:
        atomic_publish_bytes(target, raw)
    except PublicationError as exc:
        if not target.is_file() or target.read_bytes() != raw:
            raise CustodyError(
                f"immutable publication lost no-replace race: {target}",
                subcode="publication-collision",
            ) from exc
        return digest, False
    if target.read_bytes() != raw or sha256_bytes(target.read_bytes()) != digest:
        raise CustodyError("immutable publication readback mismatch", subcode="readback-drift")
    return digest, True


def claim_json_once(root: Path, target: Path, value: dict[str, Any]) -> str:
    """Create one claim exactly once; even byte-identical replay is rejected."""

    target = resolve_contained_path(root, target)
    if target.exists():
        raise CustodyError(f"claim already exists: {target}", subcode="claim-replay")
    digest, created = publish_json_idempotent(root, target, value)
    if not created:
        raise CustodyError(f"claim was already published: {target}", subcode="claim-replay")
    return digest


def read_cas_pointer(root: Path) -> dict[str, Any]:
    """Read and validate the mutable pointer to the immutable append chain."""

    pointer = resolve_contained_path(root, root / "head.json")
    if not pointer.exists():
        return {
            "schema": "a16-immutable-custody-head-v1",
            "sequence": 0,
            "last_record_sha256": None,
        }
    value, _raw, _digest = strict_snapshot(pointer)
    if set(value) != {"schema", "sequence", "last_record_sha256"}:
        raise CustodyError("custody pointer has unexpected fields", subcode="pointer-shape")
    if value.get("schema") != "a16-immutable-custody-head-v1":
        raise CustodyError("custody pointer schema mismatch", subcode="pointer-schema")
    sequence = value.get("sequence")
    last = value.get("last_record_sha256")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        raise CustodyError("custody pointer sequence is invalid", subcode="pointer-sequence")
    if last is not None and (
        not isinstance(last, str)
        or len(last) != 64
        or any(character not in "0123456789abcdef" for character in last)
    ):
        raise CustodyError("custody pointer digest is invalid", subcode="pointer-digest")
    if (sequence == 0) != (last is None):
        raise CustodyError("custody pointer genesis state is inconsistent", subcode="pointer-genesis")
    return value


def _advance_cas_pointer_locked(
    root: Path, *, expected_predecessor_sha256: str | None, new_record_sha256: str
) -> dict[str, Any]:
    """Advance the head after an immutable append, checking the exact predecessor."""

    current = read_cas_pointer(root)
    if current["last_record_sha256"] != expected_predecessor_sha256:
        raise CustodyError(
            "expected predecessor digest does not equal the custody head",
            subcode="predecessor-mismatch",
        )
    successor = {
        "schema": "a16-immutable-custody-head-v1",
        "sequence": current["sequence"] + 1,
        "last_record_sha256": new_record_sha256,
    }
    raw = canonical_json_bytes(successor)
    pointer = resolve_contained_path(root, root / "head.json")
    descriptor, temporary = tempfile.mkstemp(prefix=".head.", suffix=".tmp", dir=root)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        if read_cas_pointer(root) != current:
            raise CustodyError("custody head changed before CAS replace", subcode="cas-conflict")
        os.replace(temporary, pointer)
        temporary = ""
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    if read_cas_pointer(root) != successor:
        raise CustodyError("custody pointer readback mismatch", subcode="pointer-readback")
    return successor


def append_claim_before_cas(
    root: Path,
    target: Path,
    value: dict[str, Any],
    *,
    expected_predecessor_sha256: str | None,
) -> tuple[str, dict[str, Any]]:
    """Under one lock, append the immutable claim before advancing its CAS pointer."""

    with exclusive_writer_lock(root):
        current = read_cas_pointer(root)
        if current["last_record_sha256"] != expected_predecessor_sha256:
            raise CustodyError(
                "expected_claim_predecessor_sha256 differs from the locked custody head",
                subcode="predecessor-mismatch",
            )
        if value.get("predecessor_record_sha256") != expected_predecessor_sha256:
            raise CustodyError(
                "claim predecessor field differs from the locked custody head",
                subcode="claim-predecessor",
            )
        raw = canonical_json_bytes(value)
        digest = sha256_bytes(raw)
        target = resolve_contained_path(root, target)
        if target.exists():
            if not target.is_file() or target.read_bytes() != raw:
                raise CustodyError(
                    f"claim path contains different bytes: {target}",
                    subcode="publication-collision",
                )
            if current["last_record_sha256"] == digest:
                raise CustodyError("claim already advanced the custody head", subcode="claim-replay")
            # Exact append-before-head residue is the only safe claim adoption.
        else:
            digest = claim_json_once(root, target, value)
        pointer = _advance_cas_pointer_locked(
            root,
            expected_predecessor_sha256=expected_predecessor_sha256,
            new_record_sha256=digest,
        )
        return digest, pointer


def publish_terminal_receipt(root: Path, target: Path, value: dict[str, Any]) -> str:
    """Create one terminal receipt; FAILED and UNKNOWN are as final as PASS."""

    if value.get("result") not in {"PASS", "FAILED", "UNKNOWN"}:
        raise CustodyError("terminal receipt result is invalid", subcode="receipt-result")
    if value.get("terminal") is not True or value.get("terminal_claim") is not False:
        raise CustodyError("terminal receipt flags are invalid", subcode="receipt-terminal")
    with exclusive_writer_lock(root):
        target = resolve_contained_path(root, target)
        if target.exists():
            raise CustodyError("terminal receipt already exists", subcode="receipt-replay")
        digest, created = publish_json_idempotent(root, target, value)
        if not created:
            raise CustodyError("terminal receipt was already published", subcode="receipt-replay")
        return digest


def iter_immutable_records(root: Path) -> Iterator[tuple[Path, dict[str, Any], str]]:
    """Yield every canonical immutable JSON record beneath a custody root."""

    if not root.exists():
        return
    for path in sorted(root.rglob("*.json")):
        if path.name == "head.json" or path.name.startswith("."):
            continue
        resolved = resolve_contained_path(root, path, must_exist=True)
        value, _raw, digest = strict_snapshot(resolved)
        yield resolved, value, digest
