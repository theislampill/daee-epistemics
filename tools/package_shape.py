#!/usr/bin/env python3
"""Shared generated skill package-shape checks for the current release line."""

from __future__ import annotations

import json
import re
from pathlib import Path


CANONICAL_PACKAGE_ROOT_ENTRIES = {
    "SKILL.md",
    "README.md",
    "references",
    "compiled-module-map.json",
    "build-manifest.json",
    "cold-law-manifest.json",
}

CANONICAL_REQUIRED_ROOT_ENTRIES = {
    "SKILL.md",
    "README.md",
    "references",
    "compiled-module-map.json",
    "build-manifest.json",
    "cold-law-manifest.json",
}

DEV_ONLY_ROOT_ENTRIES = {
    "data",
    "scripts",
    "tests",
}

ALLOWED_ROOT_ENTRIES = CANONICAL_PACKAGE_ROOT_ENTRIES | DEV_ONLY_ROOT_ENTRIES
REQUIRED_ROOT_ENTRIES = CANONICAL_REQUIRED_ROOT_ENTRIES

DEV_ONLY_PACKAGE_PREFIXES = tuple(f"{entry}/" for entry in sorted(DEV_ONLY_ROOT_ENTRIES))

FORBIDDEN_ARTIFACT_NAMES = {
    "route_plan.json",
    "features.json",
    "validation.json",
    "reconstruction.json",
    "execution_verdict.json",
    "execution_prompt.md",
    "execution_blocked.md",
    "partial_banner.md",
    "retry_prompt.md",
    "output.simulated.md",
    "output.model.md",
}

FORBIDDEN_ARCHIVE_PREFIXES = (
    "skill/",
    "atomics/",
    "tools/",
    "docs/",
    "build/",
    ".git/",
    "smokes/",
    "level3-runs/",
    ".daee/",
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def skill_root(root: Path) -> Path:
    return root / "skill"


def load_manifest(root: Path) -> tuple[dict, list[str]]:
    path = skill_root(root) / "build-manifest.json"
    if not path.is_file():
        return {}, ["skill/build-manifest.json is absent"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"skill/build-manifest.json JSON parse error: {exc}"]
    if not isinstance(payload, dict):
        return {}, ["skill/build-manifest.json must be a JSON object"]
    return payload, []


def expected_package_files(root: Path, manifest: dict | None = None) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    if manifest is None:
        manifest, errors = load_manifest(root)
        if errors:
            return set(), errors
    generated_files = manifest.get("generated_files")
    if not isinstance(generated_files, list):
        return set(), ["manifest generated_files must be an array"]
    canonical_package_files = manifest.get("canonical_package_files")
    if canonical_package_files is None:
        package_file_items = generated_files
        field_name = "generated_files"
    elif isinstance(canonical_package_files, list):
        package_file_items = canonical_package_files
        field_name = "canonical_package_files"
    else:
        return set(), ["manifest canonical_package_files must be an array when present"]
    generated_set = {item for item in generated_files if isinstance(item, str)}
    expected: set[str] = set()
    seen: set[str] = set()
    for item in package_file_items:
        if not isinstance(item, str):
            errors.append(f"manifest {field_name} entry must be string: {item!r}")
            continue
        if item in seen:
            errors.append(f"manifest {field_name} duplicate: {item}")
        seen.add(item)
        if field_name == "canonical_package_files" and item not in generated_set:
            errors.append(f"manifest canonical_package_files entry absent from generated_files: {item}")
        if "\\" in item or item.startswith("/") or item.startswith("./"):
            errors.append(f"manifest {field_name} path must be normalized relative POSIX: {item}")
            continue
        if not item.startswith("skill/"):
            errors.append(f"manifest {field_name} path must start with skill/: {item}")
            continue
        rel = item[len("skill/"):]
        if not rel:
            errors.append(f"manifest {field_name} cannot include skill/ root")
            continue
        if rel.split("/", 1)[0] in DEV_ONLY_ROOT_ENTRIES:
            if field_name == "canonical_package_files":
                errors.append(f"manifest canonical_package_files must not include dev/harness path: {item}")
            continue
        if Path(rel).name in FORBIDDEN_ARTIFACT_NAMES:
            errors.append(f"manifest {field_name} must not include run artifact: {item}")
            continue
        expected.add(rel)
    return expected, errors


def is_python_cache(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}


def package_file_paths(root: Path) -> tuple[list[Path], list[str]]:
    manifest, errors = load_manifest(root)
    if errors:
        return [], errors
    expected, expected_errors = expected_package_files(root, manifest)
    errors.extend(expected_errors)
    paths: list[Path] = []
    base = skill_root(root)
    for rel in sorted(expected):
        path = base / rel
        if not path.is_file():
            errors.append(f"manifest package file is absent: skill/{rel}")
            continue
        if is_python_cache(path):
            errors.append(f"manifest must not list Python bytecode/cache file: skill/{rel}")
            continue
        paths.append(path)
    return paths, errors


def validate_manifest_shape(manifest: dict) -> list[str]:
    errors: list[str] = []
    expected_keys = {
        "generated",
        "compiler_version",
        "bundle_mapping_version",
        "canonical_source_root",
        "output_root",
        "generated_files",
        "canonical_package_files",
        "bundles",
        "runtime_metadata_copies",
        "sources",
        "extra_inputs",
        "generated_warning",
    }
    extra = sorted(set(manifest) - expected_keys)
    missing = sorted(expected_keys - set(manifest))
    if extra:
        errors.append("manifest has unknown top-level key(s): " + ", ".join(extra))
    if missing:
        errors.append("manifest missing top-level key(s): " + ", ".join(missing))
    if manifest.get("generated") is not True:
        errors.append("manifest generated must be true")
    if manifest.get("canonical_source_root") != "atomics/skill":
        errors.append("manifest canonical_source_root must be atomics/skill")
    if manifest.get("output_root") != "skill":
        errors.append("manifest output_root must be skill")
    for field in ("bundles", "runtime_metadata_copies", "sources", "extra_inputs"):
        if field in manifest and not isinstance(manifest[field], dict):
            errors.append(f"manifest {field} must be an object")
    for field in ("generated_files", "canonical_package_files"):
        if field in manifest and not isinstance(manifest[field], list):
            errors.append(f"manifest {field} must be an array")
    for field in ("compiler_version", "bundle_mapping_version", "generated_warning"):
        if field in manifest and not isinstance(manifest[field], str):
            errors.append(f"manifest {field} must be a string")
    for source_id, entry in (manifest.get("sources") or {}).items():
        if not isinstance(source_id, str) or not isinstance(entry, dict):
            errors.append(f"manifest source entry invalid: {source_id!r}")
            continue
        for required in ("module_id", "module_class", "canonical_path", "source", "source_sha256", "bundle_path"):
            if not isinstance(entry.get(required), str) or not entry[required]:
                errors.append(f"manifest source {source_id} missing string field {required}")
        sha = entry.get("source_sha256")
        if isinstance(sha, str) and not SHA256_RE.fullmatch(sha):
            errors.append(f"manifest source {source_id} has invalid SHA256: {sha!r}")
    return errors


def validate_compiled_map_shape(root: Path) -> list[str]:
    errors: list[str] = []
    path = skill_root(root) / "compiled-module-map.json"
    if not path.is_file():
        return ["skill/compiled-module-map.json is absent"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"skill/compiled-module-map.json JSON parse error: {exc}"]
    if not isinstance(payload, dict):
        return ["skill/compiled-module-map.json must be a JSON object"]
    expected_keys = {
        "generated",
        "generated_warning",
        "compiler_version",
        "bundle_mapping_version",
        "runtime_metadata_copies",
        "modules",
    }
    extra = sorted(set(payload) - expected_keys)
    missing = sorted(expected_keys - set(payload))
    if extra:
        errors.append("compiled map has unknown top-level key(s): " + ", ".join(extra))
    if missing:
        errors.append("compiled map missing top-level key(s): " + ", ".join(missing))
    if payload.get("generated") is not True:
        errors.append("compiled map generated must be true")
    modules = payload.get("modules")
    if not isinstance(modules, dict):
        errors.append("compiled map modules must be an object")
        return errors
    for module_id, entry in modules.items():
        if not isinstance(module_id, str) or not isinstance(entry, dict):
            errors.append(f"compiled map module entry invalid: {module_id!r}")
            continue
        for required in ("module_id", "module_class", "canonical_path", "source", "source_sha256", "bundle_path"):
            if not isinstance(entry.get(required), str) or not entry[required]:
                errors.append(f"compiled map module {module_id} missing string field {required}")
        if entry.get("module_id") != module_id:
            errors.append(f"compiled map module key/id mismatch: {module_id} != {entry.get('module_id')}")
        sha = entry.get("source_sha256")
        if isinstance(sha, str) and not SHA256_RE.fullmatch(sha):
            errors.append(f"compiled map module {module_id} has invalid SHA256: {sha!r}")
    return errors


def validate_skill_tree(root: Path) -> list[str]:
    errors: list[str] = []
    base = skill_root(root)
    if not base.is_dir():
        return ["skill/ runtime root is absent"]

    manifest, manifest_errors = load_manifest(root)
    errors.extend(manifest_errors)
    if manifest:
        errors.extend(validate_manifest_shape(manifest))
    errors.extend(validate_compiled_map_shape(root))

    actual_roots = {child.name for child in base.iterdir()}
    missing_roots = sorted(REQUIRED_ROOT_ENTRIES - actual_roots)
    unexpected_roots = sorted(actual_roots - ALLOWED_ROOT_ENTRIES)
    if missing_roots:
        errors.append("skill/ missing required root entry(s): " + ", ".join(missing_roots))
    if unexpected_roots:
        errors.append("skill/ has unexpected root entry(s): " + ", ".join(unexpected_roots))

    expected, expected_errors = expected_package_files(root, manifest or None)
    errors.extend(expected_errors)
    actual_packageable: set[str] = set()
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base).as_posix()
        if rel.startswith(DEV_ONLY_PACKAGE_PREFIXES):
            continue
        if is_python_cache(path):
            continue
        actual_packageable.add(rel)
    missing = sorted(expected - actual_packageable)
    unexpected = sorted(actual_packageable - expected)
    if missing:
        errors.append("manifest-listed package file(s) absent from skill/: " + ", ".join(f"skill/{item}" for item in missing[:20]))
    if unexpected:
        errors.append("unmanifested packageable file(s) under skill/: " + ", ".join(f"skill/{item}" for item in unexpected[:20]))
    return errors


def validate_archive_names(names: list[str]) -> list[str]:
    errors: list[str] = []
    roots = {name.split("/", 1)[0] for name in names if name and not name.endswith("/")}
    missing_roots = sorted(CANONICAL_REQUIRED_ROOT_ENTRIES - roots)
    unexpected_roots = sorted(roots - CANONICAL_PACKAGE_ROOT_ENTRIES)
    if missing_roots:
        errors.append("archive missing required root entry(s): " + ", ".join(missing_roots))
    if unexpected_roots:
        errors.append("archive has unexpected root entry(s): " + ", ".join(unexpected_roots))
    forbidden_dev_roots = sorted(roots.intersection(DEV_ONLY_ROOT_ENTRIES))
    if forbidden_dev_roots:
        errors.append("canonical archive must not include dev/harness root entry(s): " + ", ".join(forbidden_dev_roots))
    bad = [
        name for name in names
        if name.startswith(FORBIDDEN_ARCHIVE_PREFIXES)
        or name.startswith("./")
        or "\\" in name
        or "/__pycache__/" in name
        or name.startswith("__pycache__/")
        or name.endswith((".pyc", ".pyo"))
        or Path(name).name in FORBIDDEN_ARTIFACT_NAMES
    ]
    if bad:
        errors.append("archive has invalid root, separator, or bytecode path(s): " + ", ".join(bad[:20]))
    return errors
