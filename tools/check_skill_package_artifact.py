#!/usr/bin/env python3
"""Validate a built daee-epistemics .skill package artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from check_compiled_skill_self_contained import check_package as check_self_contained_package
from package_shape import (
    AUDIT_FULL_EXTRA_REPO_ROOTS as AUDIT_FULL_EXTRA_ROOTS_FOR_ARTIFACT_CHECK,
    AUDIT_FULL_PROFILE,
    CANONICAL_REQUIRED_ROOT_ENTRIES,
    DEFAULT_PACKAGE_PROFILE,
    DEV_ONLY_ROOT_ENTRIES,
    EXECUTION_MINI_PROFILE,
    FORBIDDEN_ARCHIVE_PREFIXES,
    PACKAGE_PROFILES,
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


def validate_manifest_members(
    zf: ZipFile, names: list[str], errors: list[str], profile: str = DEFAULT_PACKAGE_PROFILE
) -> None:
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
    # audit-full ships extra repo-root directories (schema/tools/tests/docs)
    # on top of the skill/-relative canonical_package_files set; those are
    # legitimately not part of canonical_package_files, so exclude them from
    # the "extra" comparison for that profile only.
    if profile == AUDIT_FULL_PROFILE:
        actual_for_extra_check = {
            name for name in actual
            if name.split("/", 1)[0] not in AUDIT_FULL_EXTRA_ROOTS_FOR_ARTIFACT_CHECK
        }
    else:
        actual_for_extra_check = actual
    missing = sorted(expected - actual)
    extra = sorted(actual_for_extra_check - expected)
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


# audit-full's extra repo-root directories (schema/tools/tests/docs) legitimately
# reference atomics/, expansion/, and absolute-Windows source paths in ordinary
# dev/build/doc content -- that is not the "compiled runtime is self-contained"
# invariant tools/check_compiled_skill_self_contained.py exists to guard.
# That checker guards the model-facing compiled skill/ surface specifically, so
# for audit-full this re-packs just the canonical skill/-rooted members into a
# throwaway sub-archive and runs the same checker against that, instead of the
# full audit-full archive (which would false-positive on every historical
# docs/audits/*.md mention of atomics/ paths).
def _check_self_contained_for_profile(path: Path, profile: str) -> list[str]:
    if profile != AUDIT_FULL_PROFILE:
        return check_self_contained_package(path)

    try:
        with ZipFile(path) as zf:
            names = zf.namelist()
            canonical_names = [
                name for name in names
                if name and not name.endswith("/")
                and name.split("/", 1)[0] not in AUDIT_FULL_EXTRA_ROOTS_FOR_ARTIFACT_CHECK
            ]
            with tempfile.TemporaryDirectory(prefix="daee_selfcontained_") as tmpdir:
                sub_path = Path(tmpdir) / "canonical-subset.skill.zip"
                with ZipFile(sub_path, "w", ZIP_DEFLATED) as sub_zf:
                    for name in canonical_names:
                        sub_zf.writestr(name, zf.read(name))
                return [
                    f"(audit-full canonical subset) {error}"
                    for error in check_self_contained_package(sub_path)
                ]
    except BadZipFile:
        return [f"package is not a readable zip payload: {path}"]


def validate_package(
    path: Path, expect_version: str | None = None, profile: str = DEFAULT_PACKAGE_PROFILE
) -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    if profile not in PACKAGE_PROFILES:
        return [f"unknown package profile: {profile!r}"], {}
    if not path.is_file():
        return [f"package artifact is absent: {path}"], {}
    if expect_version and expect_version not in path.name:
        errors.append(f"package filename does not include expected version {expect_version}: {path.name}")

    # execution-mini keeps the strict forbidden-prefix list (tools/, docs/,
    # schema-adjacent dev roots, etc. must never appear). audit-full legitimately
    # ships tools/, tests/, schema/, docs/, so only the always-forbidden
    # prefixes (skill/, atomics/, build/, .git/, smokes/, level3-runs/, .daee/)
    # apply there.
    if profile == EXECUTION_MINI_PROFILE:
        forbidden_prefixes = FORBIDDEN_ARCHIVE_PREFIXES
    else:
        forbidden_prefixes = tuple(
            prefix for prefix in FORBIDDEN_ARCHIVE_PREFIXES
            if prefix.rstrip("/") not in AUDIT_FULL_EXTRA_ROOTS_FOR_ARTIFACT_CHECK
        )

    try:
        with ZipFile(path) as zf:
            names = zf.namelist()
            bad_prefixes = [
                name for name in names
                if name.startswith(forbidden_prefixes) or "\\" in name
            ]
            if bad_prefixes:
                errors.append("archive contains forbidden path(s): " + ", ".join(bad_prefixes[:20]))
            errors.extend(validate_archive_names(names, profile=profile))
            roots = {name.split("/", 1)[0] for name in names if name and not name.endswith("/")}
            required_roots = set(CANONICAL_REQUIRED_ROOT_ENTRIES)
            if profile == AUDIT_FULL_PROFILE:
                required_roots |= {"tools", "tests"}
            else:
                forbidden_roots_present = sorted(roots & {"tools", "tests", ".daee"})
                if forbidden_roots_present:
                    errors.append(
                        "execution-mini archive must not contain: " + ", ".join(forbidden_roots_present)
                    )
            missing_roots = sorted(required_roots - roots)
            if missing_roots:
                errors.append("archive missing required root(s): " + ", ".join(missing_roots))
            if any(name == ".daee" or name.startswith(".daee/") for name in names):
                errors.append("archive must not contain .daee run artifacts")
            validate_manifest_members(zf, names, errors, profile=profile)
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

    errors.extend(_check_self_contained_for_profile(path, profile))

    summary = {
        "package": str(path),
        "profile": profile,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else "",
        "size": path.stat().st_size if path.is_file() else 0,
        "entries": len(names) if path.is_file() else 0,
    }
    return errors, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Built .skill or .skill.zip artifact")
    parser.add_argument("--expect-version", default=None)
    parser.add_argument(
        "--profile",
        choices=PACKAGE_PROFILES,
        default=DEFAULT_PACKAGE_PROFILE,
        help="Package profile the artifact was built with (default: execution-mini).",
    )
    args = parser.parse_args(argv)

    errors, summary = validate_package(args.package, args.expect_version, profile=args.profile)
    if errors:
        print("skill package artifact validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("skill package artifact validation: PASS")
    print(f"- package: {summary['package']}")
    print(f"- profile: {summary['profile']}")
    print(f"- SHA256: {summary['sha256']}")
    print(f"- size: {summary['size']} bytes")
    print(f"- entries: {summary['entries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
