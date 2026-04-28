#!/usr/bin/env python3
"""Check that skill/ is fresh against canonical atomized sources."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from compiled_runtime_lib import (
    BUNDLE_MAPPING_VERSION,
    COMPILER_VERSION,
    GENERATED_WARNING,
    SECTION_FIELDS,
    fail_with_errors,
    out_dir,
    parse_compiled_sections,
    repo_root,
    sha256_file,
)


def main() -> int:
    root = repo_root()
    compiled_root = out_dir(root)
    errors: list[str] = []

    if not compiled_root.is_dir():
        return fail_with_errors("compiled-runtime freshness", ["skill runtime root is absent"])

    manifest_path = compiled_root / "build-manifest.json"
    if not manifest_path.is_file():
        return fail_with_errors("compiled-runtime freshness", ["build-manifest.json is absent"])

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail_with_errors("compiled-runtime freshness", [f"manifest JSON parse error: {exc}"])

    if manifest.get("compiler_version") != COMPILER_VERSION:
        errors.append(
            f"compiler version drift: manifest {manifest.get('compiler_version')!r}, tool {COMPILER_VERSION!r}"
        )
    if manifest.get("bundle_mapping_version") != BUNDLE_MAPPING_VERSION:
        errors.append(
            "bundle mapping version drift: "
            f"manifest {manifest.get('bundle_mapping_version')!r}, tool {BUNDLE_MAPPING_VERSION!r}"
        )

    metadata_copies = manifest.get("runtime_metadata_copies") or {}
    if not isinstance(metadata_copies, dict):
        errors.append("manifest runtime_metadata_copies must be a mapping")
        metadata_copies = {}
    metadata_generated_rels = {
        f"skill/{runtime_rel}" for runtime_rel in metadata_copies
    }

    for generated_rel in manifest.get("generated_files", []):
        path = root / generated_rel
        if not path.is_file():
            errors.append(f"generated file listed in manifest is absent: {generated_rel}")
            continue
        if (
            generated_rel not in metadata_generated_rels
            and path.suffix == ".md"
            and GENERATED_WARNING.strip() not in path.read_text(encoding="utf-8")
        ):
            errors.append(f"generated markdown lacks warning header: {generated_rel}")

    for rel_path, recorded_sha in sorted((manifest.get("extra_inputs") or {}).items()):
        path = root / rel_path
        if not path.is_file():
            errors.append(f"extra input missing: {rel_path}")
        elif sha256_file(path) != recorded_sha:
            errors.append(f"extra input stale: {rel_path}")

    for runtime_rel, source_rel in sorted(metadata_copies.items()):
        runtime_path = compiled_root / runtime_rel
        source_path = root / source_rel
        if not runtime_path.is_file():
            errors.append(f"runtime metadata copy missing: {runtime_rel}")
            continue
        if not source_path.is_file():
            errors.append(f"runtime metadata source missing: {source_rel}")
            continue
        if sha256_file(runtime_path) != sha256_file(source_path):
            errors.append(f"runtime metadata copy stale: {runtime_rel} from {source_rel}")

    sources = manifest.get("sources") or {}
    if not isinstance(sources, dict):
        errors.append("manifest sources must be a mapping")
        sources = {}

    seen_sections: dict[str, dict[str, str]] = {}
    for bundle_rel in (manifest.get("bundles") or {}).keys():
        bundle_path = compiled_root / bundle_rel
        if not bundle_path.is_file():
            errors.append(f"bundle missing: {bundle_rel}")
            continue
        for section in parse_compiled_sections(bundle_path):
            missing = [field for field in SECTION_FIELDS if not section.get(field)]
            if missing:
                errors.append(f"{bundle_rel}: compiled section missing {', '.join(missing)}")
                continue
            module_id = section["MODULE_ID"]
            if module_id in seen_sections:
                errors.append(f"duplicate compiled section for module id: {module_id}")
            seen_sections[module_id] = section
            source = section["SOURCE"]
            source_path = root / source
            if not source_path.is_file():
                errors.append(f"{bundle_rel}: source missing for section {module_id}: {source}")
                continue
            current_sha = sha256_file(source_path)
            if current_sha != section["SOURCE_SHA256"]:
                errors.append(f"{bundle_rel}: section hash stale for {module_id} ({source})")
            generated_body = section.get("GENERATED_BODY")
            if generated_body is not None:
                source_text = source_path.read_text(encoding="utf-8").rstrip()
                if generated_body.rstrip() != source_text:
                    errors.append(f"{bundle_rel}: generated body stale for {module_id} ({source})")
            manifest_entry = sources.get(module_id)
            if not manifest_entry:
                errors.append(f"{bundle_rel}: section absent from manifest sources: {module_id}")
            elif manifest_entry.get("source_sha256") != current_sha:
                errors.append(f"manifest source hash stale for {module_id}: {source}")

    for module_id, entry in sorted(sources.items()):
        if module_id not in seen_sections:
            errors.append(f"manifest source has no compiled section: {module_id} ({entry.get('source')})")

    return fail_with_errors("compiled-runtime freshness", errors)


if __name__ == "__main__":
    sys.exit(main())
