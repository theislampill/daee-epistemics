#!/usr/bin/env python3
"""Validate source identity boundaries inside compiled runtime bundles."""

from __future__ import annotations

import json
import sys

from compiled_runtime_lib import (
    SECTION_FIELDS,
    catalogue_by_id,
    canonical_source_rel,
    fail_with_errors,
    generated_markdown_files,
    out_dir,
    parse_compiled_sections,
    repo_root,
)


def main() -> int:
    root = repo_root()
    compiled_root = out_dir(root)
    errors: list[str] = []
    if not compiled_root.is_dir():
        return fail_with_errors("compiled module boundaries", ["skill runtime root is absent"])

    catalogue = catalogue_by_id(root)
    seen: dict[str, str] = {}
    metadata_rels: set[str] = set()
    manifest_path = compiled_root / "build-manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            metadata_copies = manifest.get("runtime_metadata_copies") or {}
            if isinstance(metadata_copies, dict):
                metadata_rels = set(metadata_copies)
        except json.JSONDecodeError as exc:
            errors.append(f"build-manifest.json parse error: {exc}")
    markdown_files = [
        path for path in generated_markdown_files(root)
        if path.relative_to(compiled_root).as_posix() != "SKILL.md"
        and path.relative_to(compiled_root).as_posix() not in metadata_rels
    ]

    for path in markdown_files:
        rel_bundle = path.relative_to(compiled_root).as_posix()
        sections = parse_compiled_sections(path)
        if not sections:
            errors.append(f"generated bundle has no compiled sections: {rel_bundle}")
            continue
        for section in sections:
            missing = [field for field in SECTION_FIELDS if not section.get(field)]
            if missing:
                errors.append(f"{rel_bundle}: section missing {', '.join(missing)}")
                continue
            module_id = section["MODULE_ID"]
            source = section["SOURCE"]
            if module_id in seen:
                errors.append(f"duplicate module id in compiled bundles: {module_id} ({seen[module_id]}, {rel_bundle})")
            seen[module_id] = rel_bundle
            if section["CANONICAL_PATH"] != source:
                errors.append(
                    f"{rel_bundle}: canonical path does not match source for {module_id}: "
                    f"{section['CANONICAL_PATH']} != {source}"
                )
            catalogue_entry = catalogue.get(module_id)
            if catalogue_entry:
                expected_source = canonical_source_rel(catalogue_entry.get("path", ""))
                if expected_source != source:
                    errors.append(
                        f"{rel_bundle}: catalogue path mismatch for {module_id}: "
                        f"{expected_source} != {source}"
                    )
                if catalogue_entry.get("module_class") != section["MODULE_CLASS"]:
                    errors.append(
                        f"{rel_bundle}: catalogue class mismatch for {module_id}: "
                        f"{catalogue_entry.get('module_class')} != {section['MODULE_CLASS']}"
                    )

    for module_id, entry in sorted(catalogue.items()):
        if module_id not in seen:
            errors.append(f"catalogue module lost in compiled runtime: {module_id} ({entry.get('path')})")

    return fail_with_errors("compiled module boundaries", errors)


if __name__ == "__main__":
    sys.exit(main())
