#!/usr/bin/env python3
"""Build the generated compiled daee-epistemics runtime."""

from __future__ import annotations

import hashlib
import json
import re
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
MANUAL_CONTRACT_REL = "skill/references/rubrics/manual-contract-digest.md"
FULL_MANUAL_CONTRACT_REL = "skill/references/rubrics/non-droppable-manual-contract.md"

# Checker map: which output checker(s) enforce each cold-law clause once it is
# either inlined in the hot digest or loaded on demand from the cold source.
# advisory=True means no output checker exists today for that clause; it is
# flagged pending an owner decision (see clause.preamble-size-partial).
COLD_LAW_CHECKER_MAP: dict[str, dict[str, object]] = {
    "clause.preamble-size-partial": {
        "checkers": [],
        "load_when": "any mass/size PARTIAL route decision for hard/default manual output",
        "advisory": True,
    },
    "clause.banner": {
        "checkers": ["tools/check_manual_smoke_render_contract.py"],
        "load_when": "rendering the opening banner + Layer A/Layer B heading sequence",
        "advisory": False,
    },
    "clause.layer-a-ledger": {
        "checkers": ["tools/check_manual_smoke_render_contract.py"],
        "load_when": "rendering or closing the 𝔅_LA/𝔅_MRP/𝔅_total ledger and field_witness graph keys",
        "advisory": False,
    },
    "clause.concealment-mode": {
        "checkers": ["tools/check_concealment_mode.py"],
        "load_when": "rendering Layer A `Concealment mode:` for named-worldview or shubhah pressure",
        "advisory": False,
    },
    "clause.canonical-notation": {
        "checkers": ["tools/check_manual_smoke_render_contract.py"],
        "load_when": "rendering burden/submove notation, ACT rows, or the 𝔅/𝒞 ledger and closure symbols",
        "advisory": False,
    },
    "clause.mrp-block-grammar": {
        "checkers": [
            "tools/check_mid_reread_pressure.py",
            "tools/check_mrp_route_invariants.py",
        ],
        "load_when": "rendering any post-land [Mid-Reread Pressure] block",
        "advisory": False,
    },
    "clause.held-burden-activation": {
        "checkers": [
            "tools/check_mid_reread_pressure.py",
            "tools/check_mrp_route_invariants.py",
        ],
        "load_when": "an MRP route resolves to held_burden_activation or generated_burden_instantiation",
        "advisory": False,
    },
    "clause.owner-ttp-route": {
        "checkers": [
            "tools/check_owner_activation_ordering.py",
            "tools/check_ttp_operator_contracts.py",
        ],
        "load_when": "selecting/ordering owners or rendering an ACT records block for a burden",
        "advisory": False,
    },
    "clause.no-burden-shrink": {
        "checkers": ["tools/check_manual_smoke_render_contract.py"],
        "load_when": "a final MRP route considers no_new_resultant after baseline burdens land",
        "advisory": False,
    },
    "clause.proof-tail-order": {
        "checkers": ["tools/check_manual_smoke_render_contract.py"],
        "load_when": "rendering the Restorative Response / Closing Formulation / Closure witness tail",
        "advisory": False,
    },
    "clause.field-witness-spec": {
        "checkers": [
            "tools/check_field_witness_binding.py",
            "tools/check_ir_instance_integrity.py",
        ],
        "load_when": "emitting the final field_witness JSON payload",
        "advisory": False,
    },
    "clause.execution-mandate-detail": {
        "checkers": ["tools/check_manual_smoke_render_contract.py"],
        "load_when": "any default-mode execution needing the full mandate mechanics beyond the hot digest",
        "advisory": False,
    },
    "clause.output-surface-invariant": {
        "checkers": ["tools/check_metacompliance_current_canon.py"],
        "load_when": "verifying the default output surface against the full invariant text",
        "advisory": False,
    },
}

COLD_LAW_CLAUSE_START_RE = re.compile(r"^<!-- COLD-LAW-CLAUSE: (clause\.[a-z0-9-]+) -->$")
COLD_LAW_CLAUSE_END_RE = re.compile(r"^<!-- END-COLD-LAW-CLAUSE: (clause\.[a-z0-9-]+) -->$")


def build_cold_law_manifest(root: Path) -> dict[str, object]:
    """Parse clause anchors from the cold full contract and emit the manifest.

    Each clause's sha256 is computed over the exact text strictly between its
    START/END anchor comments (anchors excluded), so any future edit to a
    clause's substance is hash-detectable without depending on the anchors
    themselves.
    """
    path = source_path_for(root, FULL_MANUAL_CONTRACT_REL)
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    clauses: dict[str, dict[str, object]] = {}
    current: str | None = None
    current_start_line = 0
    buf: list[str] = []
    for index, line in enumerate(lines):
        start_match = COLD_LAW_CLAUSE_START_RE.match(line)
        if start_match:
            if current is not None:
                raise ValueError(f"nested cold-law-clause anchor at line {index + 1}: {current}")
            current = start_match.group(1)
            current_start_line = index + 2  # 1-indexed line following the anchor comment
            buf = []
            continue
        end_match = COLD_LAW_CLAUSE_END_RE.match(line)
        if end_match:
            clause_id = end_match.group(1)
            if clause_id != current:
                raise ValueError(
                    f"mismatched cold-law-clause end anchor at line {index + 1}: "
                    f"expected {current!r}, found {clause_id!r}"
                )
            span_text = "\n".join(buf)
            clauses[clause_id] = {
                "span_lines": [current_start_line, index],
                "sha256": hashlib.sha256(span_text.encode("utf-8")).hexdigest(),
            }
            current = None
            buf = []
            continue
        if current is not None:
            buf.append(line)
    if current is not None:
        raise ValueError(f"unclosed cold-law-clause anchor: {current}")

    missing_map_entries = sorted(set(clauses) - set(COLD_LAW_CHECKER_MAP))
    missing_clause_entries = sorted(set(COLD_LAW_CHECKER_MAP) - set(clauses))
    if missing_map_entries:
        raise ValueError(f"cold-law clauses without a checker-map entry: {missing_map_entries}")
    if missing_clause_entries:
        raise ValueError(f"checker-map entries without a cold-law clause anchor: {missing_clause_entries}")

    clause_table: dict[str, object] = {}
    for clause_id in sorted(clauses):
        entry = dict(clauses[clause_id])
        mapping = COLD_LAW_CHECKER_MAP[clause_id]
        entry["checkers"] = list(mapping["checkers"])
        entry["load_when"] = mapping["load_when"]
        entry["advisory"] = bool(mapping["advisory"])
        clause_table[clause_id] = entry

    return {
        "schema": "daee-cold-law-manifest-v1",
        "generated": True,
        "source": source_rel_from_legacy(FULL_MANUAL_CONTRACT_REL),
        "clauses": clause_table,
    }


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

    cold_law_manifest = build_cold_law_manifest(root)
    cold_law_out = compiled_root / "cold-law-manifest.json"
    cold_law_out.write_text(
        json.dumps(cold_law_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    generated_files.append(posix_rel(cold_law_out, root))

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
