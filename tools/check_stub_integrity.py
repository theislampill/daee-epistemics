#!/usr/bin/env python3
"""Check canonical source integrity for future compiled stubs/maps."""

from __future__ import annotations

import sys

from compiled_runtime_lib import (
    LEGACY_SOURCE_ROOT_REL,
    SOURCE_ROOT_REL,
    catalogue_by_id,
    fail_with_errors,
    parse_frontmatter,
    repo_root,
    source_path_for,
    source_rel_from_legacy,
    source_root,
)


def main() -> int:
    root = repo_root()
    errors: list[str] = []
    atomics_root = source_root(root)
    references_root = atomics_root / "references"
    source_skill = atomics_root / "SKILL.md"
    if not source_skill.is_file():
        errors.append("atomics/skill/SKILL.md is absent")
    else:
        try:
            parse_frontmatter(source_skill.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"atomics/skill/SKILL.md: YAML front matter missing or invalid: {exc}")

    if not references_root.is_dir():
        return fail_with_errors("stub/source integrity", ["atomics/skill/references is absent"])

    for path in sorted(references_root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        source_relative = path.relative_to(atomics_root).as_posix()
        legacy_rel = f"{LEGACY_SOURCE_ROOT_REL}/{source_relative}"
        try:
            text = path.read_text(encoding="utf-8")
            data, _raw, _body = parse_frontmatter(text)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{rel}: YAML front matter missing or invalid: {exc}")
            continue
        if data.get("canonical_path") not in {rel, legacy_rel}:
            errors.append(f"{rel}: canonical_path mismatch: {data.get('canonical_path')!r}")
        if not data.get("id"):
            errors.append(f"{rel}: missing id")
        if not data.get("module_class"):
            errors.append(f"{rel}: missing module_class")

    for module_id, entry in sorted(catalogue_by_id(root).items()):
        rel = entry.get("path", "")
        path = source_path_for(root, rel)
        physical_rel = f"{SOURCE_ROOT_REL}/{source_rel_from_legacy(rel)}"
        if not path.is_file():
            errors.append(f"catalogue path missing for {module_id}: {rel}")
            continue
        try:
            data, _raw, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{rel}: catalogue source has invalid YAML: {exc}")
            continue
        if physical_rel != path.relative_to(root).as_posix():
            errors.append(f"{rel}: resolved source path mismatch: {physical_rel}")
        if data.get("id") != module_id:
            errors.append(f"{rel}: YAML id {data.get('id')!r} != catalogue id {module_id!r}")
        if data.get("module_class") != entry.get("module_class"):
            errors.append(
                f"{rel}: YAML class {data.get('module_class')!r} != catalogue class {entry.get('module_class')!r}"
            )

    return fail_with_errors("stub/source integrity", errors)


if __name__ == "__main__":
    sys.exit(main())
