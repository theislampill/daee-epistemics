#!/usr/bin/env python3
"""Validate a built daee-epistemics .skill package artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from check_compiled_skill_self_contained import check_package as check_self_contained_package
from package_shape import (
    CANONICAL_REQUIRED_ROOT_ENTRIES,
    DEV_ONLY_ROOT_ENTRIES,
    FORBIDDEN_ARCHIVE_PREFIXES,
    validate_archive_names,
)


REQUIRED_CONTENT_TOKENS = {
    "MRP TTP id": "TTP-MRP-mid-reread-pressure",
    "Mid-Reread Pressure title": "Mid-Reread Pressure",
    "field_witness sidecar": "field_witness",
    "reread pressure sidecar hook": "reread_pressure",
    "closure graph root marker": "(root)",
    "closure graph dependency arrow": "→",
    "closure graph parallel marker": "∥",
    "active divergence gate": "∇·T",
    "active curl gate": "∇×T",
    "closure divergence field": "∇·B:",
    "closure curl field": "∇×κ:",
    "closure field": "𝒞(Ψᴺ):",
    "transfer boundary": "T_lang",
}

FORBIDDEN_MOJIBAKE_TOKENS = {
    "U+00E2 marker": "\u00e2",
    "U+00C2 marker": "\u00c2",
    "U+00C3 marker": "\u00c3",
    "U+00CE marker": "\u00ce",
    "U+00CF marker": "\u00cf",
    "U+00D0 marker": "\u00d0",
    "U+00F0 marker": "\u00f0",
    "replacement character": "\ufffd",
}


def read_member_text(zf: ZipFile, name: str, errors: list[str]) -> str:
    try:
        return zf.read(name).decode("utf-8")
    except KeyError:
        errors.append(f"archive missing required member: {name}")
    except UnicodeDecodeError:
        errors.append(f"archive member is not UTF-8 text: {name}")
    return ""


def load_json_member(zf: ZipFile, name: str, errors: list[str]) -> dict:
    text = read_member_text(zf, name, errors)
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"{name}: invalid JSON: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{name}: expected JSON object")
        return {}
    return payload


def archive_text_corpus(zf: ZipFile, names: list[str]) -> str:
    parts: list[str] = []
    for name in names:
        if not name.endswith((".md", ".json")):
            continue
        try:
            parts.append(zf.read(name).decode("utf-8", errors="replace"))
        except KeyError:
            continue
    return "\n".join(parts)


def validate_manifest_members(zf: ZipFile, names: list[str], errors: list[str]) -> None:
    manifest = load_json_member(zf, "build-manifest.json", errors)
    compiled_map = load_json_member(zf, "compiled-module-map.json", errors)
    if not manifest or not compiled_map:
        return

    canonical_files = manifest.get("canonical_package_files")
    if not isinstance(canonical_files, list):
        errors.append("build-manifest.json missing canonical_package_files array")
        return
    expected: set[str] = set()
    for item in canonical_files:
        if not isinstance(item, str) or not item.startswith("skill/"):
            errors.append(f"invalid canonical package file entry: {item!r}")
            continue
        rel = item[len("skill/"):]
        if rel.split("/", 1)[0] in DEV_ONLY_ROOT_ENTRIES:
            errors.append(f"canonical package file must not include dev root: {item}")
            continue
        expected.add(rel)
    actual = {name for name in names if name and not name.endswith("/")}
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append("archive missing manifest-listed member(s): " + ", ".join(missing[:20]))
    if extra:
        errors.append("archive contains member(s) not in canonical_package_files: " + ", ".join(extra[:20]))

    modules = compiled_map.get("modules")
    if not isinstance(modules, dict):
        errors.append("compiled-module-map.json missing modules object")
    elif "TTP-MRP-mid-reread-pressure" not in modules:
        errors.append("compiled-module-map.json missing TTP-MRP-mid-reread-pressure")

    sources = manifest.get("sources")
    if not isinstance(sources, dict):
        errors.append("build-manifest.json missing sources object")
    elif "TTP-MRP-mid-reread-pressure" not in sources:
        errors.append("build-manifest.json missing TTP-MRP-mid-reread-pressure source")


def validate_package(path: Path, expect_version: str | None = None) -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    if not path.is_file():
        return [f"package artifact is absent: {path}"], {}
    if expect_version and expect_version not in path.name:
        errors.append(f"package filename does not include expected version {expect_version}: {path.name}")

    try:
        with ZipFile(path) as zf:
            names = zf.namelist()
            bad_prefixes = [
                name for name in names
                if name.startswith(FORBIDDEN_ARCHIVE_PREFIXES) or "\\" in name
            ]
            if bad_prefixes:
                errors.append("archive contains forbidden path(s): " + ", ".join(bad_prefixes[:20]))
            errors.extend(validate_archive_names(names))
            roots = {name.split("/", 1)[0] for name in names if name and not name.endswith("/")}
            missing_roots = sorted(CANONICAL_REQUIRED_ROOT_ENTRIES - roots)
            if missing_roots:
                errors.append("archive missing required root(s): " + ", ".join(missing_roots))
            validate_manifest_members(zf, names, errors)
            corpus = archive_text_corpus(zf, names)
            for label, token in REQUIRED_CONTENT_TOKENS.items():
                if token not in corpus:
                    errors.append(f"missing packaged content token ({label}): {token}")
            for label, token in FORBIDDEN_MOJIBAKE_TOKENS.items():
                if token in corpus:
                    errors.append(f"packaged text contains likely mojibake token: {label}")
    except BadZipFile:
        errors.append(f"package is not a readable zip payload: {path}")
        names = []

    errors.extend(check_self_contained_package(path))

    summary = {
        "package": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else "",
        "size": path.stat().st_size if path.is_file() else 0,
        "entries": len(names) if path.is_file() else 0,
    }
    return errors, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Built .skill or .skill.zip artifact")
    parser.add_argument("--expect-version", default=None)
    args = parser.parse_args(argv)

    errors, summary = validate_package(args.package, args.expect_version)
    if errors:
        print("skill package artifact validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("skill package artifact validation: PASS")
    print(f"- package: {summary['package']}")
    print(f"- SHA256: {summary['sha256']}")
    print(f"- size: {summary['size']} bytes")
    print(f"- entries: {summary['entries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
