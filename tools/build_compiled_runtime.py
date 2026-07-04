#!/usr/bin/env python3
"""Build the generated compiled daee-epistemics runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from build_framework_pipeline import build as build_framework_pipeline
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
    normalize_runtime_surface_text,
    out_dir,
    posix_rel,
    repo_root,
    sha256_file,
    source_path_for,
    source_rel_from_legacy,
)

DEV_ONLY_GENERATED_ROOTS = {"data", "scripts", "tests"}
MANUAL_CONTRACT_REL = "skill/references/rubrics/non-droppable-manual-contract.md"


def canonical_package_files_from_generated(generated_files: list[str]) -> list[str]:
    """Return generated runtime files that belong in the canonical user-facing package."""
    selected: list[str] = []
    for item in generated_files:
        if not item.startswith(f"{OUTPUT_ROOT_REL}/"):
            continue
        rel = item[len(f"{OUTPUT_ROOT_REL}/"):]
        if rel.split("/", 1)[0] in DEV_ONLY_GENERATED_ROOTS:
            continue
        selected.append(item)
    return sorted(selected)


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
            expected_canonical_path = f"{OUTPUT_ROOT_REL}/{source_rel_from_legacy(rel_path)}"
            if doc.canonical_path != expected_canonical_path:
                errors.append(
                    f"{rel_path}: canonical_path mismatch: "
                    f"{doc.canonical_path!r} != {expected_canonical_path!r}"
                )
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

    instructions = source_path_for(root, MANUAL_CONTRACT_REL).read_text(encoding="utf-8")
    # The manual contract carries operative front matter (required by
    # check_frontmatter / check_coverage / check_stub_integrity on the source),
    # but that metadata must not be inlined as visible runtime content — doing so
    # shifts the compiled top-contract and breaks the manual-render 120-line check.
    # Strip it here, mirroring the main-skill front-matter split above.
    if instructions.startswith("---"):
        mc_sections = instructions.split("---", 2)
        if len(mc_sections) >= 3:
            instructions = mc_sections[2].lstrip("\r\n")
    mandate_marker = "# EXECUTION MANDATE - DEFAULT MODE"
    invariant_marker = "# Default Output Surface Invariant"
    addendum_marker = "# Compiled Runtime Routing Addendum"
    mandate_idx = instructions.find(mandate_marker)
    invariant_idx = instructions.find(invariant_marker)
    addendum_idx = instructions.find(addendum_marker)
    if mandate_idx == -1 or invariant_idx == -1 or addendum_idx == -1 or not (mandate_idx < invariant_idx < addendum_idx):
        ordered_instructions = instructions
    else:
        pre_mandate = instructions[:mandate_idx].strip()
        mandate_body = instructions[mandate_idx + len(mandate_marker) : invariant_idx].strip()
        invariant_body = instructions[invariant_idx + len(invariant_marker) : addendum_idx].strip()
        addendum_section = instructions[addendum_idx:].strip()
        ordered_instructions = "\n\n".join(
            [
                mandate_marker,
                "Default mode suppresses raw visible IR but does not suppress recursive execution.",
                invariant_marker,
                "Default visible frame order: Layer A -> Layer B -> State/noetic re-read -> Restorative Response -> Closing Formulation.",
                "Mandatory MRP block fields include Route-gradient:, MRP route result type:, Field diagnostics:, and LoopBreak:.",
                "# Non-Droppable Default Manual Contract",
                pre_mandate,
                "# Default Output Surface Invariant Details",
                invariant_body,
                "# Default Mode Execution Details",
                mandate_body,
                addendum_section,
            ]
        )
    return frontmatter + normalize_runtime_surface_text(ordered_instructions + "\n\n" + body.rstrip()) + "\n"


def build() -> int:
    root = repo_root()
    framework_status = build_framework_pipeline()
    if framework_status != 0:
        return framework_status

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
                "source": doc.source_rel_path,
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

    canonical_runtime_metadata_copies = {
        runtime_rel: source_rel
        for runtime_rel, source_rel in runtime_metadata_copies.items()
        if runtime_rel.split("/", 1)[0] not in DEV_ONLY_GENERATED_ROOTS
    }

    compiled_map = {
        "generated": True,
        "generated_warning": "GENERATED FILE. Do not edit directly. Canonical atomized source lives under atomics/skill/. Regenerate with tools/build_compiled_runtime.py.",
        "compiler_version": COMPILER_VERSION,
        "bundle_mapping_version": BUNDLE_MAPPING_VERSION,
        "runtime_metadata_copies": canonical_runtime_metadata_copies,
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
    canonical_package_files = canonical_package_files_from_generated(generated_files_with_manifest)
    manifest = {
        "generated": True,
        "compiler_version": COMPILER_VERSION,
        "bundle_mapping_version": BUNDLE_MAPPING_VERSION,
        "canonical_source_root": SOURCE_ROOT_REL,
        "output_root": OUTPUT_ROOT_REL,
        "generated_files": generated_files_with_manifest,
        "canonical_package_files": canonical_package_files,
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
