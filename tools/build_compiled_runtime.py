#!/usr/bin/env python3
"""Build the generated compiled daee-epistemics runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from compiled_runtime_lib import (
    BUNDLE_MAPPING_VERSION,
    BUNDLE_SOURCES,
    COMPILER_VERSION,
    EXTRA_INPUTS,
    GENERATED_WARNING,
    OUTPUT_ROOT_REL,
    RUNTIME_METADATA_COPIES,
    SOURCE_ROOT_REL,
    canonical_source_rel,
    build_section,
    catalogue_by_id,
    clean_compiled_dir,
    load_source_doc,
    out_dir,
    posix_rel,
    repo_root,
    sha256_file,
    source_path_for,
    source_rel_from_legacy,
)


def validate_sources(root: Path) -> list[str]:
    errors: list[str] = []
    seen_paths: set[str] = set()
    seen_ids: dict[str, str] = {}
    catalogue = catalogue_by_id(root)

    for bundle_path, sources in BUNDLE_SOURCES.items():
        if bundle_path != bundle_path.replace("\\", "/"):
            errors.append(f"bundle path must use POSIX separators: {bundle_path}")
        for rel_path in sources:
            source_path = source_path_for(root, rel_path)
            if rel_path in seen_paths:
                errors.append(f"source appears in more than one compiled bundle: {rel_path}")
                continue
            seen_paths.add(rel_path)
            if not source_path.is_file():
                errors.append(f"source file missing: {rel_path}")
                continue
            try:
                doc = load_source_doc(root, rel_path)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{rel_path}: cannot read front matter: {exc}")
                continue
            for field in ("id", "module_class", "canonical_path"):
                if not doc.frontmatter.get(field):
                    errors.append(f"{rel_path}: missing front matter field {field}")
            if doc.canonical_path != canonical_source_rel(rel_path):
                errors.append(f"{rel_path}: canonical_path mismatch: {doc.canonical_path!r}")
            if doc.module_id in seen_ids:
                errors.append(
                    f"module id appears in multiple compiled sources: {doc.module_id} "
                    f"({seen_ids[doc.module_id]}, {rel_path})"
                )
            seen_ids[doc.module_id] = rel_path

    for module_id, entry in catalogue.items():
        path = entry["path"]
        if module_id not in seen_ids:
            errors.append(f"catalogue module is absent from compiled mapping: {module_id} ({path})")
        elif source_rel_from_legacy(seen_ids[module_id]) != source_rel_from_legacy(path):
            errors.append(
                f"catalogue module path mismatch for {module_id}: "
                f"compiled {seen_ids[module_id]}, catalogue {path}"
            )

    for rel_path in EXTRA_INPUTS:
        if not source_path_for(root, rel_path).is_file():
            errors.append(f"extra input missing: {rel_path}")
    for rel_path in RUNTIME_METADATA_COPIES:
        if not source_path_for(root, rel_path).is_file():
            errors.append(f"runtime metadata input missing: {rel_path}")
    return errors


def generated_skill_text(root: Path) -> str:
    skill_path = source_path_for(root, "skill/SKILL.md")
    source_text = skill_path.read_text(encoding="utf-8")
    sections = source_text.split("---", 2)
    if len(sections) >= 3 and source_text.startswith("---"):
        frontmatter = f"---{sections[1]}---\n"
        body = sections[2].lstrip("\r\n")
    else:
        frontmatter = ""
        body = source_text

    instructions = f"""{GENERATED_WARNING}
# Compiled Runtime Routing Addendum

Canonical atomized source remains under `atomics/skill/`. This generated runtime is the low-call Claude package root built from that source.

## Compiled Runtime Path Resolution

This compiled runtime package does not contain every atomized source file as a standalone runtime file.

When this SKILL.md or a routing table names an atomized source path such as:

`references/tactics/M9-predication-mode.md`

treat that path as a canonical source identity, not as a literal runtime file-load target.

Resolve the original module ID or source path through:

`compiled-module-map.json`

then load the containing runtime bundle and section, for example:

`references/omnibus/OMNIBUS-tactics.md` -> section `MODULE_ID: M9-predication-mode`.

Do not attempt to load missing atomized files from the compiled package.

Do not use omnibus filenames as `matched_modules`.

Use original module IDs in `matched_modules` and `source_basis`.

Bundle co-location means availability, not activation.

Load path for substantive cases:

1. `references/runtime-foundation.md`
2. `references/runtime-diagnostic-core.md`
3. `references/runtime-phase2-passes.md`
4. `references/runtime-dispatch-gate.md`
5. `references/runtime-output-governance.md`

Use `references/omnibus/*.md` only after V1, Phase 2, and the Diagnostic IR authorize the original source module owner.

Compiled-runtime rules:

- Treat inherited atomized/source paths in the tables below as original source module references, not literal files to chase inside this package.
- Resolve an inherited path by normalizing it to `atomics/skill/...`, finding that entry in `compiled-module-map.json`, loading the listed `bundle_path`, and using only the section whose `<!-- MODULE_ID: ... -->` matches the map entry.
- Do not load missing atomized/source paths literally. If a path cannot be resolved by `compiled-module-map.json` or by a copied runtime metadata file under `references/diagnostics/`, hold it as a runtime resolution failure.
- Bundle names never appear in `matched_modules`.
- Every `matched_modules` entry uses the original module ID from `module-catalogue.json`.
- Every module-backed `source_basis` entry cites the original module ID and the compiled bundle section that was used.
- Bundle co-location does not activate sibling sections.
- Preserve post-render gate discipline: every bounded move must retain the `STOP`, `HOLD`, `RECURSE`, or `PARTIAL` decision model from the diagnostic IR and output governance.
- If a generated bundle conflicts with `atomics/skill/`, the atomized source wins and this runtime must be rebuilt.

Routing governance invariants:

- diagnosis before answer.
- IR before routing.
- routing before render.
- post-render gate.
- STOP / HOLD / RECURSE / PARTIAL.
- bundle availability is not activation.
- matched_modules use original module IDs.
- source_basis records original module or section.

The generated bundle map is `compiled-module-map.json`.

---

"""
    return frontmatter + instructions + body.rstrip() + "\n"


def build() -> int:
    root = repo_root()
    errors = validate_sources(root)
    if errors:
        print("compiled-runtime build: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    compiled_root = clean_compiled_dir(root)
    source_map: dict[str, dict[str, str]] = {}
    generated_files: list[str] = []

    skill_out = compiled_root / "SKILL.md"
    skill_out.write_text(generated_skill_text(root), encoding="utf-8", newline="\n")
    generated_files.append(posix_rel(skill_out, root))

    for bundle_rel, sources in BUNDLE_SOURCES.items():
        bundle_out = compiled_root / bundle_rel
        bundle_out.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            GENERATED_WARNING.rstrip(),
            "",
            f"# {Path(bundle_rel).stem}",
            "",
            "This generated bundle is a runtime read view. Section presence does not imply active dispatch.",
        ]
        for rel_path in sources:
            doc = load_source_doc(root, rel_path)
            lines.append(build_section(doc).rstrip())
            source_map[doc.module_id] = {
                "module_id": doc.module_id,
                "module_class": doc.module_class,
                "canonical_path": doc.canonical_path,
                "source": doc.rel_path,
                "source_sha256": doc.sha256,
                "bundle_path": bundle_rel,
            }
        bundle_out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
        generated_files.append(posix_rel(bundle_out, root))

    runtime_metadata_copies: dict[str, str] = {}
    for rel_path in RUNTIME_METADATA_COPIES:
        source_path = source_path_for(root, rel_path)
        runtime_rel = source_rel_from_legacy(rel_path)
        metadata_out = compiled_root / runtime_rel
        metadata_out.parent.mkdir(parents=True, exist_ok=True)
        metadata_out.write_bytes(source_path.read_bytes())
        generated_files.append(posix_rel(metadata_out, root))
        runtime_metadata_copies[runtime_rel] = canonical_source_rel(rel_path)

    compiled_map = {
        "generated": True,
        "generated_warning": "GENERATED FILE. Do not edit directly. Canonical atomized source lives under atomics/skill/. Regenerate with tools/build_compiled_runtime.py.",
        "compiler_version": COMPILER_VERSION,
        "bundle_mapping_version": BUNDLE_MAPPING_VERSION,
        "runtime_metadata_copies": runtime_metadata_copies,
        "modules": dict(sorted(source_map.items())),
    }
    map_out = compiled_root / "compiled-module-map.json"
    map_out.write_text(json.dumps(compiled_map, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    generated_files.append(posix_rel(map_out, root))

    extra_inputs = {
        canonical_source_rel(rel_path): sha256_file(source_path_for(root, rel_path))
        for rel_path in EXTRA_INPUTS
    }
    manifest_out = compiled_root / "build-manifest.json"
    generated_files_with_manifest = sorted([*generated_files, posix_rel(manifest_out, root)])
    manifest = {
        "generated": True,
        "compiler_version": COMPILER_VERSION,
        "bundle_mapping_version": BUNDLE_MAPPING_VERSION,
        "canonical_source_root": SOURCE_ROOT_REL,
        "output_root": OUTPUT_ROOT_REL,
        "generated_files": generated_files_with_manifest,
        "bundles": {
            bundle_rel: [canonical_source_rel(source_rel) for source_rel in sources]
            for bundle_rel, sources in BUNDLE_SOURCES.items()
        },
        "runtime_metadata_copies": runtime_metadata_copies,
        "sources": dict(sorted(source_map.items())),
        "extra_inputs": extra_inputs,
        "generated_warning": "GENERATED FILE. Do not edit directly. Canonical atomized source lives under atomics/skill/. Regenerate with tools/build_compiled_runtime.py.",
    }
    manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    print("compiled-runtime build: PASS")
    print(f"Output: {out_dir(root).relative_to(root).as_posix()}")
    print(f"Bundles: {len(BUNDLE_SOURCES)}")
    print(f"Compiled source sections: {len(source_map)}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
