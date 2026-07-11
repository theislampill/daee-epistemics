#!/usr/bin/env python3
"""Create one private, hash-attested local execution tree for checker runs."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from contract_validation import PathCustodyError, resolve_repo_path


SNAPSHOT_ROOTS = ("tools", "schema")
IGNORED_PARTS = {"__pycache__"}
CHECKER_SOURCE_BOOTSTRAP = r"""
import hashlib
from pathlib import Path
import sys

snapshot = Path(sys.argv[1])
logical_source = Path(sys.argv[2])
expected_sha256 = sys.argv[3]
source = snapshot.read_bytes()
if hashlib.sha256(source).hexdigest() != expected_sha256:
    raise SystemExit(86)
sys.argv = [str(logical_source), *sys.argv[4:]]
sys.path.insert(0, str(logical_source.parent))
namespace = {
    "__name__": "__main__",
    "__file__": str(logical_source),
    "__package__": None,
    "__spec__": None,
    "__cached__": None,
    "__loader__": None,
}
exec(compile(source, str(logical_source), "exec"), namespace, namespace)
"""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = (json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ) + "\n").encode("utf-8")
    return _sha256(payload)


def _regular_files(path: Path) -> Iterable[Path]:
    if path.is_symlink():
        raise ValueError(f"execution snapshot rejects symlink source: {path}")
    if path.is_file():
        yield path
        return
    for candidate in sorted(path.rglob("*")):
        if any(part in IGNORED_PARTS for part in candidate.parts):
            continue
        if candidate.suffix == ".pyc":
            continue
        if candidate.is_symlink():
            raise ValueError(f"execution snapshot rejects symlink source: {candidate}")
        if candidate.is_file():
            yield candidate


def _reject_symlink_components(source_root: Path, value: str | Path) -> None:
    raw = Path(value)
    lexical = raw if raw.is_absolute() else source_root / raw
    for candidate in (lexical, *lexical.parents):
        if candidate.is_symlink():
            raise ValueError(f"execution snapshot rejects symlink source: {candidate}")
        if candidate == source_root:
            break


def execution_snapshot_sources(
    *,
    root: Path,
    plan: list[dict[str, Any]],
) -> dict[str, Path]:
    """Return the exact repository files owned by one checker execution tree."""

    source_root = root.resolve(strict=True)
    sources: dict[str, Path] = {}
    for relative_root in SNAPSHOT_ROOTS:
        _reject_symlink_components(source_root, relative_root)
        source = resolve_repo_path(
            source_root,
            relative_root,
            must_exist=True,
            expect_dir=True,
        )
        for path in _regular_files(source):
            relative = path.relative_to(source_root).as_posix()
            sources[relative] = path

    for row in plan:
        for value in row.get("runtime_resources", []):
            _reject_symlink_components(source_root, value)
            try:
                source = resolve_repo_path(source_root, value, must_exist=True)
            except PathCustodyError as exc:
                raise ValueError(f"checker runtime resource is outside custody: {value}: {exc}") from exc
            for path in _regular_files(source):
                relative = path.relative_to(source_root).as_posix()
                sources[relative] = path
    return sources


@dataclass
class ExecutionSnapshot:
    source_root: Path
    root: Path
    output_path: Path
    output_bytes: bytes
    files: dict[str, bytes]
    manifest: dict[str, Any]

    def source_path(self, row: dict[str, Any]) -> Path:
        relative = str(row["source_path"])
        path = self.root / Path(relative)
        if not path.is_file():
            raise ValueError(f"checker source absent from execution snapshot: {relative}")
        expected = str(row["source_sha256"])
        if _sha256(path.read_bytes()) != expected:
            raise ValueError(f"checker source hash drift in execution snapshot: {relative}")
        return path

    def checker_command(
        self,
        row: dict[str, Any],
        *,
        python_executable: str = sys.executable,
    ) -> list[str]:
        source = self.source_path(row)
        return [
            python_executable,
            "-I",
            "-B",
            "-c",
            CHECKER_SOURCE_BOOTSTRAP,
            str(source),
            str(source),
            str(row["source_sha256"]),
            *[str(argument) for argument in row.get("arguments", [])],
        ]

    def bind_plan(
        self,
        plan: list[dict[str, Any]],
        *,
        original_output: Path,
    ) -> list[dict[str, Any]]:
        original_values = {
            str(original_output),
            os.fspath(original_output),
            str(original_output.resolve(strict=True)),
        }
        rebound: list[dict[str, Any]] = []
        for raw in plan:
            row = copy.deepcopy(raw)
            row["arguments"] = [
                str(self.output_path) if str(argument) in original_values else str(argument)
                for argument in row.get("arguments", [])
            ]
            rebound.append(row)
        return rebound

    def verify(self) -> None:
        for relative, expected in self.files.items():
            source = self.source_root / Path(relative)
            snapshot = self.root / Path(relative)
            if source.read_bytes() != expected:
                raise ValueError(f"live execution dependency changed during checker replay: {relative}")
            if snapshot.read_bytes() != expected:
                raise ValueError(f"private execution dependency changed during checker replay: {relative}")
        if self.output_path.read_bytes() != self.output_bytes:
            raise ValueError("private output snapshot changed during checker replay")


def create_execution_snapshot(
    *,
    root: Path,
    destination: Path,
    plan: list[dict[str, Any]],
    output_path: Path,
) -> ExecutionSnapshot:
    """Copy checker code, local modules, schemas, and declared data into custody."""

    source_root = root.resolve(strict=True)
    output = output_path.resolve(strict=True)
    try:
        output.relative_to(source_root)
    except ValueError as exc:
        raise ValueError("checker output must remain under the repository root") from exc

    snapshot_root = destination.resolve(strict=False)
    try:
        snapshot_root.relative_to(source_root)
    except ValueError as exc:
        raise ValueError("execution snapshot destination must remain under the repository root") from exc
    if snapshot_root.exists():
        raise ValueError(f"execution snapshot destination already exists: {snapshot_root}")
    snapshot_root.mkdir(parents=True)

    sources = execution_snapshot_sources(root=source_root, plan=plan)

    copied: dict[str, bytes] = {}
    manifest_files: list[dict[str, Any]] = []
    for relative in sorted(sources):
        source = sources[relative]
        data = source.read_bytes()
        if source.read_bytes() != data:
            raise ValueError(f"execution dependency changed during snapshot read: {relative}")
        target = snapshot_root / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if target.read_bytes() != data:
            raise ValueError(f"execution dependency snapshot readback failed: {relative}")
        try:
            target.chmod(0o444)
        except OSError:
            pass
        copied[relative] = data
        manifest_files.append(
            {
                "path": relative,
                "sha256": _sha256(data),
                "bytes": len(data),
            }
        )

    artifact_dir = snapshot_root / ".artifacts"
    artifact_dir.mkdir()
    frozen_output = artifact_dir / "output.snapshot.md"
    output_bytes = output.read_bytes()
    with frozen_output.open("xb") as handle:
        handle.write(output_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    if output.read_bytes() != output_bytes or frozen_output.read_bytes() != output_bytes:
        raise ValueError("output changed during execution snapshot creation")
    try:
        frozen_output.chmod(0o444)
    except OSError:
        pass

    manifest = {
        "schema": "daee-checker-execution-snapshot-v1",
        "sha256": _canonical_sha256(manifest_files),
        "file_count": len(manifest_files),
        "files": manifest_files,
    }
    snapshot = ExecutionSnapshot(
        source_root=source_root,
        root=snapshot_root,
        output_path=frozen_output,
        output_bytes=output_bytes,
        files=copied,
        manifest=manifest,
    )
    return snapshot
