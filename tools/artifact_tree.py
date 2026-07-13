#!/usr/bin/env python3
"""Shared extracted/package tree identity for Branch 10 custody records."""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Any


TREE_DIGEST_ALGORITHM = "daee-tree-sha256-v1"
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _is_reparse(path: Path) -> bool:
    try:
        observed = path.lstat()
    except OSError as exc:
        raise ValueError(f"tree entry cannot be inspected: {path}") from exc
    return path.is_symlink() or bool(
        getattr(observed, "st_file_attributes", 0) & _REPARSE_POINT
    )


def _file_rows(root: Path) -> list[dict[str, Any]]:
    base = root.resolve(strict=True)
    if not base.is_dir():
        raise ValueError("tree root must be a directory")
    if _is_reparse(root):
        raise ValueError("tree root must not be a symlink or reparse point")

    rows: list[dict[str, Any]] = []

    def visit(directory: Path) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise ValueError(f"tree directory cannot be read: {directory}") from exc
        for entry in entries:
            path = Path(entry.path)
            if _is_reparse(path):
                raise ValueError(f"tree contains symlink or reparse content: {path}")
            try:
                if entry.is_dir(follow_symlinks=False):
                    visit(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    raise ValueError(f"tree contains non-regular content: {path}")
                before = path.stat(follow_symlinks=False)
                payload = path.read_bytes()
                after = path.stat(follow_symlinks=False)
            except OSError as exc:
                raise ValueError(f"tree file cannot be read: {path}") from exc
            identity_before = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            )
            identity_after = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            )
            if identity_before != identity_after or len(payload) != after.st_size:
                raise ValueError(f"tree file changed during custody read: {path}")
            relative = path.relative_to(base).as_posix()
            rows.append(
                {
                    "path": relative,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )

    visit(base)
    rows.sort(key=lambda row: row["path"])
    return rows


def build_tree_receipt(root: Path) -> dict[str, Any]:
    """Return the named framed-path/file-digest identity and its exact inventory."""
    rows = _file_rows(root)
    digest = hashlib.sha256()
    for row in rows:
        relative = row["path"].encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(bytes.fromhex(row["sha256"]))
    return {
        "algorithm": TREE_DIGEST_ALGORITHM,
        "tree_sha256": digest.hexdigest(),
        "file_count": len(rows),
        "files": rows,
    }


def tree_sha256(root: Path) -> str:
    return str(build_tree_receipt(root)["tree_sha256"])
