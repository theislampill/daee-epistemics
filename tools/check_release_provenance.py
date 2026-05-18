#!/usr/bin/env python3
"""Validate local release package provenance without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


HASH_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$")


FIELD_ALIASES = {
    "package_sha256": ("package_sha256", "asset_sha256", "zip_sha256"),
    "package_size": ("package_size", "asset_size", "zip_size"),
    "entry_count": ("package_entry_count", "entry_count"),
    "build_manifest_sha256": (
        "build_manifest_sha256",
        "manifest_sha256",
        "build_manifest_hash",
    ),
    "compiled_module_map_sha256": (
        "compiled_module_map_sha256",
        "compiled_map_sha256",
        "compiled_module_map_hash",
    ),
}


def read_json(path: Path, errors: list[str]) -> dict[str, object]:
    if not path.exists():
        errors.append(f"provenance file is absent: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path}: provenance payload must be a JSON object")
        return {}
    return value


def sha256(path: Path, errors: list[str], label: str) -> str | None:
    if not path.exists():
        errors.append(f"{label} is absent: {path}")
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def provenance_field(
    payload: dict[str, object], canonical: str, errors: list[str], required: bool = True
) -> object | None:
    for name in FIELD_ALIASES.get(canonical, (canonical,)):
        if name in payload:
            return payload[name]
    if required:
        aliases = ", ".join(FIELD_ALIASES.get(canonical, (canonical,)))
        errors.append(f"provenance missing required field: {aliases}")
    return None


def normalize_hash(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    match = HASH_RE.search(value)
    return match.group(0).upper() if match else None


def normalize_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\d+", value.replace(",", ""))
        return int(match.group(0)) if match else None
    return None


def zip_entry_count(path: Path, errors: list[str]) -> int | None:
    if not path.exists():
        errors.append(f"package file is absent: {path}")
        return None
    try:
        with ZipFile(path) as zf:
            return len(zf.namelist())
    except BadZipFile:
        errors.append(f"package is not a readable .skill/.zip archive: {path}")
        return None


def clean_table_value(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_markdown_tables(path: Path, errors: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        errors.append(f"release artifacts document is absent: {path}")
        return []
    tables: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = TABLE_ROW_RE.match(line)
        if not match:
            if current:
                tables.append(current)
                current = {}
            continue
        key = clean_table_value(match.group(1)).lower()
        value = clean_table_value(match.group(2))
        if key in {"field", "---"} or set(key) <= {"-"}:
            continue
        current[key] = value
    if current:
        tables.append(current)
    return tables


def check_required_fields(payload: dict[str, object], errors: list[str]) -> None:
    for field in ("version", "contract_version", "source_commit"):
        if not payload.get(field):
            errors.append(f"provenance missing required field: {field}")
    if payload.get("raw_atomics_packaged") is not False:
        errors.append("provenance must record raw_atomics_packaged: false")
    if payload.get("forbidden_roots_absent") is not True:
        errors.append("provenance must record forbidden_roots_absent: true")
    for field in FIELD_ALIASES:
        provenance_field(payload, field, errors)


def compare_hash(label: str, actual: str | None, expected: object, errors: list[str]) -> None:
    if actual is None:
        return
    if expected is None:
        return
    expected_hash = normalize_hash(expected)
    if expected_hash is None:
        errors.append(f"provenance {label} is not a SHA256 hash")
        return
    if actual != expected_hash:
        errors.append(f"{label} mismatch: actual {actual}, provenance {expected_hash}")


def compare_int(label: str, actual: int | None, expected: object, errors: list[str]) -> None:
    if actual is None:
        return
    if expected is None:
        return
    expected_int = normalize_int(expected)
    if expected_int is None:
        errors.append(f"provenance {label} is not an integer")
        return
    if actual != expected_int:
        errors.append(f"{label} mismatch: actual {actual}, provenance {expected_int}")


def check_release_artifacts_doc(
    path: Path, package_path: Path, package_sha: str, payload: dict[str, object], errors: list[str]
) -> None:
    tables = parse_markdown_tables(path, errors)
    if not tables:
        return
    package_name = package_path.name
    matching = [table for table in tables if table.get("package filename") == package_name]
    if not matching:
        print(f"release artifacts note: no table for {package_name}; contradiction check skipped")
        return
    table = matching[0]
    doc_sha = normalize_hash(table.get("sha256"))
    if doc_sha and doc_sha != package_sha:
        errors.append(f"{path}: SHA256 contradicts package/provenance: {doc_sha} != {package_sha}")
    doc_size = normalize_int(table.get("size"))
    package_size = normalize_int(provenance_field(payload, "package_size", errors, required=False))
    if doc_size is not None and package_size is not None and doc_size != package_size:
        errors.append(f"{path}: size contradicts provenance: {doc_size} != {package_size}")
    doc_entries = normalize_int(table.get("entries"))
    entry_count = normalize_int(provenance_field(payload, "entry_count", errors, required=False))
    if doc_entries is not None and entry_count is not None and doc_entries != entry_count:
        errors.append(f"{path}: entry count contradicts provenance: {doc_entries} != {entry_count}")
    doc_manifest = normalize_hash(table.get("generated runtime manifest sha256"))
    prov_manifest = normalize_hash(
        provenance_field(payload, "build_manifest_sha256", errors, required=False)
    )
    if doc_manifest and prov_manifest and doc_manifest != prov_manifest:
        errors.append(f"{path}: build-manifest SHA256 contradicts provenance")


def check_smoke_root(root: Path, package_sha: str, errors: list[str]) -> None:
    if not root.exists():
        errors.append(f"smoke root is absent: {root}")
        return
    found_hashes: set[str] = set()
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            found_hashes.update(match.group(0).upper() for match in HASH_RE.finditer(text))
    if not found_hashes:
        errors.append(f"{root}: no package SHA256 evidence found")
    elif package_sha not in found_hashes:
        errors.append(f"{root}: smoke package SHA does not match provenance/package SHA256")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--package", required=True, dest="package_path", type=Path)
    parser.add_argument("--manifest", default=Path("skill/build-manifest.json"), type=Path)
    parser.add_argument("--compiled-map", default=Path("skill/compiled-module-map.json"), type=Path)
    parser.add_argument("--release-artifacts", type=Path)
    parser.add_argument("--smoke-root", type=Path)
    args = parser.parse_args(argv)

    errors: list[str] = []
    payload = read_json(args.provenance, errors)
    if payload:
        check_required_fields(payload, errors)

    package_sha = sha256(args.package_path, errors, "package")
    package_size = args.package_path.stat().st_size if args.package_path.exists() else None
    entry_count = zip_entry_count(args.package_path, errors)
    manifest_sha = sha256(args.manifest, errors, "build manifest")
    compiled_map_sha = sha256(args.compiled_map, errors, "compiled module map")

    if payload:
        compare_hash(
            "package SHA256",
            package_sha,
            provenance_field(payload, "package_sha256", errors, required=False),
            errors,
        )
        compare_int(
            "package size",
            package_size,
            provenance_field(payload, "package_size", errors, required=False),
            errors,
        )
        compare_int(
            "entry count",
            entry_count,
            provenance_field(payload, "entry_count", errors, required=False),
            errors,
        )
        compare_hash(
            "build-manifest SHA256",
            manifest_sha,
            provenance_field(payload, "build_manifest_sha256", errors, required=False),
            errors,
        )
        compare_hash(
            "compiled-module-map SHA256",
            compiled_map_sha,
            provenance_field(payload, "compiled_module_map_sha256", errors, required=False),
            errors,
        )

    if args.release_artifacts and package_sha and payload:
        check_release_artifacts_doc(args.release_artifacts, args.package_path, package_sha, payload, errors)
    if args.smoke_root and package_sha:
        check_smoke_root(args.smoke_root, package_sha, errors)

    if errors:
        print("release provenance check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("release provenance check: PASS")
    print(f"- package: {args.package_path}")
    print(f"- package SHA256: {package_sha}")
    print(f"- package size: {package_size}")
    print(f"- package entries: {entry_count}")
    print(f"- build-manifest SHA256: {manifest_sha}")
    print(f"- compiled-module-map SHA256: {compiled_map_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
