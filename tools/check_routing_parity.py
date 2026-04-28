#!/usr/bin/env python3
"""Phase 5 routing-parity and compiled path-resolution checker.

This checker is intentionally static. It proves that fixture expectations use
original module IDs, that those IDs still resolve to compiled bundle sections,
and that legacy atomized paths in the generated runtime are not missing-file
load risks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from compiled_runtime_lib import (
    SECTION_FIELDS,
    fail_with_errors,
    out_dir,
    parse_compiled_sections,
    repo_root,
    source_rel_from_legacy,
)


FIXTURE_DIR = Path("tests/routing-fixtures")
OMNIBUS_PREFIX = "OMNIBUS-"

CASE_CLASS_THRESHOLDS = {
    "simple": 5,
    "ordinary": 12,
    "complex": 20,
}

RUNTIME_PATH_RESOLUTION_TOKENS = [
    "## Compiled Runtime Path Resolution",
    "canonical source identity",
    "compiled-module-map.json",
    "Do not attempt to load missing atomized files",
    "Do not use omnibus filenames as `matched_modules`",
    "Bundle co-location means availability, not activation",
]

GLOBAL_GOVERNANCE_PHRASES = [
    "diagnosis before answer",
    "IR before routing",
    "routing before render",
    "post-render gate",
    "STOP / HOLD / RECURSE / PARTIAL",
    "bundle availability is not activation",
    "matched_modules use original module IDs",
    "source_basis records original module or section",
]

GOVERNANCE_ALIASES = {
    "diagnosis before answer": [
        "Diagnose noetic structure",
        "then respond",
    ],
    "IR before routing": [
        "The diagnostic IR must be formed",
        "before any content module is dispatched",
    ],
    "routing before render": [
        "render shape does not determine routing",
    ],
    "post-render gate": [
        "post-render gate",
    ],
    "STOP / HOLD / RECURSE / PARTIAL": [
        "STOP",
        "HOLD",
        "RECURSE",
        "PARTIAL",
    ],
    "bundle availability is not activation": [
        "Bundle co-location means availability, not activation",
    ],
    "matched_modules use original module IDs": [
        "matched_modules use original module IDs",
    ],
    "source_basis records original module or section": [
        "source_basis records original module or section",
    ],
    "criterion before evidence dump": [
        "criterion",
        "evidence",
        "dump",
    ],
    "semantic discipline before doctrinal release": [
        "semantic",
        "doctrinal-release pending predication clearance",
    ],
    "artifact vs authenticated transmission distinction": [
        "provenance",
        "content",
        "authority",
        "transmission",
    ],
    "no generic RT collapse": [
        "source-use",
        "transmission",
        "confirmed",
    ],
    "register-hold": [
        "register-hold",
    ],
    "no theodicy dump": [
        "no argument, no theodicy",
    ],
    "P7 stop/hold/recurse discipline": [
        "STOP",
        "HOLD",
        "RECURSE",
        "PARTIAL",
    ],
    "low confidence / underdetermined read": [
        "low-confidence",
        "underdetermined",
    ],
    "no confident NS/DO lock": [
        "No confident family-lock from thin basis",
    ],
    "claim_level": [
        "claim_level",
    ],
    "pattern_profile": [
        "pattern_profile",
    ],
    "semantic/tribunal gate before content release": [
        "semantic gate",
        "tribunal",
        "content release",
    ],
}

OWNER_CLUSTER_BUNDLES = {
    "runtime-foundation": "references/runtime-foundation.md",
    "diagnostic-core": "references/runtime-diagnostic-core.md",
    "phase2-passes": "references/runtime-phase2-passes.md",
    "dispatch-gate": "references/runtime-dispatch-gate.md",
    "output-governance": "references/runtime-output-governance.md",
    "profiles": "references/omnibus/OMNIBUS-profiles.md",
    "do-families": "references/omnibus/OMNIBUS-do-families.md",
    "rt-transmission": "references/omnibus/OMNIBUS-rt-transmission.md",
    "tactics": "references/omnibus/OMNIBUS-tactics.md",
    "techniques": "references/omnibus/OMNIBUS-techniques.md",
    "procedures": "references/omnibus/OMNIBUS-procedures.md",
    "specialty-diagnostics": "references/omnibus/OMNIBUS-specialty-diagnostics.md",
}

LEGACY_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"((?:atomics/skill/|skill/)?references/"
    r"(?:tactics|techniques|diagnostics|case-library|procedures|rubrics|omnibus)"
    r"/[A-Za-z0-9_./\[\]-]+\.(?:md|json|yaml))"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def is_module_id(value: str) -> bool:
    return not (
        value.startswith(OMNIBUS_PREFIX)
        or value.startswith("references/")
        or "/" in value
        or value.endswith((".md", ".json", ".yaml"))
    )


def normalized_ref(raw: str) -> str:
    return raw.replace("\\", "/").strip("`'\"()<>.,;:")


def runtime_file_set(compiled_root: Path) -> tuple[set[str], dict[str, list[str]]]:
    files: set[str] = set()
    by_basename: dict[str, list[str]] = {}
    for path in compiled_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(compiled_root).as_posix()
        files.add(rel)
        by_basename.setdefault(path.name, []).append(rel)
    return files, by_basename


def module_aliases(modules: dict[str, dict[str, str]]) -> tuple[dict[str, str], dict[str, list[str]]]:
    aliases: dict[str, str] = {}
    by_basename: dict[str, list[str]] = {}
    for module_id, entry in modules.items():
        source = entry.get("source", "")
        canonical_path = entry.get("canonical_path", "")
        source_rel = source_rel_from_legacy(source)
        candidates = {
            source,
            canonical_path,
            source_rel,
            f"skill/{source_rel}",
            f"atomics/skill/{source_rel}",
        }
        if source_rel.startswith("references/"):
            candidates.add(source_rel[len("references/"):])
        for candidate in candidates:
            if candidate:
                aliases[candidate] = module_id
        by_basename.setdefault(PurePosixPath(source_rel).name, []).append(module_id)
    return aliases, by_basename


def generated_bundle_paths(compiled_root: Path) -> list[Path]:
    paths = sorted(compiled_root.glob("references/runtime-*.md"))
    paths.extend(sorted((compiled_root / "references/omnibus").glob("OMNIBUS-*.md")))
    return [path for path in paths if path.is_file()]


def compiled_sections_by_module(
    compiled_root: Path,
    modules: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    bundle_rels = sorted({entry.get("bundle_path", "") for entry in modules.values() if entry.get("bundle_path")})
    for bundle_rel in bundle_rels:
        bundle_path = compiled_root / bundle_rel
        if not bundle_path.is_file():
            continue
        for section in parse_compiled_sections(bundle_path):
            module_id = section.get("MODULE_ID", "")
            if module_id:
                sections[module_id] = section
    return sections


def section_has_identity_markers(section: dict[str, str]) -> list[str]:
    return [field for field in SECTION_FIELDS if not section.get(field)]


def phrase_present(corpus: str, phrase: str) -> bool:
    if phrase.lower() in corpus.lower():
        return True
    tokens = GOVERNANCE_ALIASES.get(phrase)
    if not tokens:
        return False
    lowered = corpus.lower()
    return all(token.lower() in lowered for token in tokens)


def load_fixtures(root: Path, errors: list[str]) -> list[tuple[Path, dict[str, Any]]]:
    fixture_root = root / FIXTURE_DIR
    if not fixture_root.is_dir():
        errors.append(f"{FIXTURE_DIR.as_posix()} is absent")
        return []
    fixtures: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(fixture_root.glob("*.json")):
        try:
            fixture = read_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(root).as_posix()}: JSON parse error: {exc}")
            continue
        fixtures.append((path, fixture))
    if len(fixtures) < 10:
        errors.append(f"expected at least 10 routing fixtures, found {len(fixtures)}")
    return fixtures


def classify_runtime_ref(
    root: Path,
    compiled_root: Path,
    ref: str,
    runtime_files: set[str],
    runtime_basenames: dict[str, list[str]],
    modules: dict[str, dict[str, str]],
    aliases: dict[str, str],
    module_basenames: dict[str, list[str]],
    sections: dict[str, dict[str, str]],
    path_resolution_addendum_present: bool,
) -> tuple[str, str | None]:
    if "[" in ref or "]" in ref:
        return "source-identity-only", None

    runtime_ref = ref[len("skill/"):] if ref.startswith("skill/") else ref
    if ref.startswith("atomics/skill/"):
        runtime_ref = source_rel_from_legacy(ref)

    if runtime_ref in runtime_files:
        return "exists-in-runtime", None
    if "/" not in runtime_ref:
        matches = runtime_basenames.get(runtime_ref, [])
        if len(matches) == 1:
            return "exists-in-runtime", None

    module_id = aliases.get(ref) or aliases.get(runtime_ref)
    if module_id is None and "/" not in runtime_ref:
        matches = module_basenames.get(runtime_ref, [])
        if len(matches) == 1:
            module_id = matches[0]
    if module_id:
        section = sections.get(module_id)
        if section and not section_has_identity_markers(section):
            bundle_rel = modules.get(module_id, {}).get("bundle_path", "")
            if (compiled_root / bundle_rel).is_file():
                return "mapped-to-compiled-section", module_id

    source_candidate = root / "atomics/skill" / source_rel_from_legacy(ref)
    if path_resolution_addendum_present and source_candidate.exists():
        return "source-identity-only", None

    return "unresolved-risk", None


def audit_path_resolution(
    root: Path,
    compiled_root: Path,
    skill_text: str,
    modules: dict[str, dict[str, str]],
    sections: dict[str, dict[str, str]],
    errors: list[str],
) -> dict[str, int]:
    path_resolution_addendum_present = all(token in skill_text for token in RUNTIME_PATH_RESOLUTION_TOKENS)
    if not path_resolution_addendum_present:
        missing = [token for token in RUNTIME_PATH_RESOLUTION_TOKENS if token not in skill_text]
        errors.append("generated SKILL.md lacks compiled path-resolution addendum tokens: " + ", ".join(missing))

    runtime_files, runtime_basenames = runtime_file_set(compiled_root)
    aliases, module_basenames = module_aliases(modules)
    counts = {
        "exists-in-runtime": 0,
        "mapped-to-compiled-section": 0,
        "source-identity-only": 0,
        "unresolved-risk": 0,
    }
    seen: set[tuple[str, str]] = set()
    scan_paths = [compiled_root / "SKILL.md", *generated_bundle_paths(compiled_root)]
    for path in scan_paths:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(compiled_root).as_posix()
        for match in LEGACY_PATH_RE.finditer(text):
            ref = normalized_ref(match.group(1))
            key = (rel, ref)
            if key in seen:
                continue
            seen.add(key)
            classification, _module_id = classify_runtime_ref(
                root,
                compiled_root,
                ref,
                runtime_files,
                runtime_basenames,
                modules,
                aliases,
                module_basenames,
                sections,
                path_resolution_addendum_present,
            )
            counts[classification] += 1
            if classification == "unresolved-risk":
                errors.append(f"{rel}:{line_number(text, match.start())}: unresolved runtime path risk: {ref}")
    return counts


def check_module_mapping(
    module_id: str,
    context: str,
    compiled_root: Path,
    modules: dict[str, dict[str, str]],
    sections: dict[str, dict[str, str]],
    errors: list[str],
) -> str | None:
    entry = modules.get(module_id)
    if not entry:
        errors.append(f"{context}: module id missing from compiled-module-map.json: {module_id}")
        return None
    bundle_rel = entry.get("bundle_path", "")
    if not bundle_rel or not (compiled_root / bundle_rel).is_file():
        errors.append(f"{context}: mapped bundle missing for {module_id}: {bundle_rel}")
    section = sections.get(module_id)
    if not section:
        errors.append(f"{context}: mapped bundle lacks section for module id: {module_id}")
        return bundle_rel
    missing = section_has_identity_markers(section)
    if missing:
        errors.append(f"{context}: {module_id} section missing identity markers: {', '.join(missing)}")
    if section.get("MODULE_ID") != module_id:
        errors.append(f"{context}: {module_id} section MODULE_ID mismatch: {section.get('MODULE_ID')}")
    if section.get("SOURCE") != entry.get("source"):
        errors.append(f"{context}: {module_id} section/source map mismatch")
    if section.get("CANONICAL_PATH") != entry.get("canonical_path"):
        errors.append(f"{context}: {module_id} section canonical path mismatch")
    return bundle_rel


def check_fixtures(
    root: Path,
    compiled_root: Path,
    fixtures: list[tuple[Path, dict[str, Any]]],
    modules: dict[str, dict[str, str]],
    sections: dict[str, dict[str, str]],
    corpus: str,
    strict: bool,
    errors: list[str],
) -> dict[str, int]:
    stats = {
        "fixtures": len(fixtures),
        "required_modules": 0,
        "optional_modules": 0,
        "governance_phrases": 0,
    }
    for path, fixture in fixtures:
        rel = path.relative_to(root).as_posix()
        fixture_id = fixture.get("id")
        expected = fixture.get("expected")
        if not isinstance(fixture_id, str) or not fixture_id:
            errors.append(f"{rel}: missing fixture id")
            continue
        if not isinstance(expected, dict):
            errors.append(f"{rel}: missing expected object")
            continue
        context = f"{rel} ({fixture_id})"
        case_class = fixture.get("case_class")
        if case_class not in CASE_CLASS_THRESHOLDS:
            errors.append(f"{context}: unknown case_class {case_class!r}")
        expected_bundles = expected.get("expected_bundles") or []
        if not isinstance(expected_bundles, list):
            errors.append(f"{context}: expected_bundles must be a list")
            expected_bundles = []
        for bundle_rel in expected_bundles:
            if not isinstance(bundle_rel, str):
                errors.append(f"{context}: expected bundle is not a string")
                continue
            if not (compiled_root / bundle_rel).is_file():
                errors.append(f"{context}: expected bundle missing: {bundle_rel}")
        modeled_calls = 1 + len(set(expected_bundles))
        max_calls = expected.get("max_calls")
        if not isinstance(max_calls, int):
            errors.append(f"{context}: max_calls must be an integer")
        elif modeled_calls > max_calls:
            errors.append(f"{context}: modeled calls {modeled_calls} exceed fixture max_calls {max_calls}")
        threshold = CASE_CLASS_THRESHOLDS.get(case_class)
        if threshold is not None and modeled_calls > threshold:
            errors.append(f"{context}: modeled calls {modeled_calls} exceed {case_class} threshold {threshold}")
        if threshold is not None and isinstance(max_calls, int) and max_calls > threshold:
            errors.append(f"{context}: fixture max_calls {max_calls} exceed {case_class} threshold {threshold}")

        active_modules: list[str] = []
        for field in ("required_modules", "optional_modules"):
            values = expected.get(field) or []
            if not isinstance(values, list):
                errors.append(f"{context}: {field} must be a list")
                continue
            for module_id in values:
                if not isinstance(module_id, str):
                    errors.append(f"{context}: {field} contains a non-string module id")
                    continue
                if not is_module_id(module_id):
                    errors.append(f"{context}: {field} uses non-module matched_modules value: {module_id}")
                    continue
                active_modules.append(module_id)
                bundle_rel = check_module_mapping(module_id, context, compiled_root, modules, sections, errors)
                if bundle_rel and expected_bundles and bundle_rel not in expected_bundles:
                    errors.append(f"{context}: {module_id} maps to {bundle_rel}, absent from expected_bundles")
                stats["required_modules" if field == "required_modules" else "optional_modules"] += 1

        for forbidden in expected.get("forbidden_matched_modules") or []:
            if not isinstance(forbidden, str):
                errors.append(f"{context}: forbidden_matched_modules contains a non-string value")
                continue
            if forbidden in active_modules:
                errors.append(f"{context}: forbidden matched module appears active in fixture: {forbidden}")
            if (forbidden.startswith(OMNIBUS_PREFIX) or forbidden.startswith("references/omnibus/")) and forbidden in modules:
                errors.append(f"{context}: omnibus name appears as compiled module id: {forbidden}")

        for phrase in expected.get("required_governance") or []:
            if not isinstance(phrase, str):
                errors.append(f"{context}: required_governance contains a non-string value")
                continue
            stats["governance_phrases"] += 1
            if not phrase_present(corpus, phrase):
                errors.append(f"{context}: governance phrase not found in runtime corpus: {phrase!r}")

        decisions = expected.get("allowed_post_render_decisions") or []
        if not isinstance(decisions, list) or not decisions:
            errors.append(f"{context}: allowed_post_render_decisions must be a non-empty list")
        for decision in decisions:
            if decision not in {"STOP", "HOLD", "RECURSE", "PARTIAL"}:
                errors.append(f"{context}: invalid post-render decision: {decision!r}")

        if strict:
            for cluster in expected.get("owner_clusters") or []:
                if cluster not in OWNER_CLUSTER_BUNDLES:
                    errors.append(f"{context}: unknown strict owner cluster: {cluster}")
                    continue
                bundle_rel = OWNER_CLUSTER_BUNDLES[cluster]
                if not (compiled_root / bundle_rel).is_file():
                    errors.append(f"{context}: strict owner cluster bundle missing: {cluster} -> {bundle_rel}")
                    continue
                if not any(entry.get("bundle_path") == bundle_rel for entry in modules.values()):
                    errors.append(f"{context}: strict owner cluster has no mapped modules: {cluster}")
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="also validate fixture owner clusters")
    args = parser.parse_args(argv)

    root = repo_root()
    compiled_root = out_dir(root)
    errors: list[str] = []
    if not compiled_root.is_dir():
        return fail_with_errors("routing parity", ["skill runtime root is absent"])

    skill_path = compiled_root / "SKILL.md"
    map_path = compiled_root / "compiled-module-map.json"
    if not skill_path.is_file():
        return fail_with_errors("routing parity", ["skill/SKILL.md is absent"])
    if not map_path.is_file():
        return fail_with_errors("routing parity", ["skill/compiled-module-map.json is absent"])

    compiled_map = read_json(map_path)
    modules = compiled_map.get("modules") or {}
    if not isinstance(modules, dict) or not modules:
        errors.append("compiled-module-map.json has no modules mapping")
        modules = {}
    sections = compiled_sections_by_module(compiled_root, modules)

    for module_id in modules:
        if not is_module_id(module_id):
            errors.append(f"compiled-module-map.json uses non-module id as a module: {module_id}")

    skill_text = skill_path.read_text(encoding="utf-8")
    corpus_parts = [skill_text]
    for bundle_path in generated_bundle_paths(compiled_root):
        corpus_parts.append(bundle_path.read_text(encoding="utf-8"))
    corpus = "\n".join(corpus_parts)

    for phrase in GLOBAL_GOVERNANCE_PHRASES:
        if not phrase_present(corpus, phrase):
            errors.append(f"global governance phrase missing from runtime corpus: {phrase!r}")

    path_counts = audit_path_resolution(root, compiled_root, skill_text, modules, sections, errors)
    fixtures = load_fixtures(root, errors)
    fixture_stats = check_fixtures(root, compiled_root, fixtures, modules, sections, corpus, args.strict, errors)

    print("Routing parity summary")
    print("------------------------------------------------------------")
    print(f"Fixtures checked: {fixture_stats['fixtures']}")
    print(f"Required module assertions: {fixture_stats['required_modules']}")
    print(f"Optional module assertions: {fixture_stats['optional_modules']}")
    print(f"Governance phrase assertions: {fixture_stats['governance_phrases']}")
    print(f"Strict mode: {'on' if args.strict else 'off'}")
    print("Path-resolution status")
    for key in ("exists-in-runtime", "mapped-to-compiled-section", "source-identity-only", "unresolved-risk"):
        print(f"  {key}: {path_counts[key]}")
    print("------------------------------------------------------------")
    return fail_with_errors("routing parity", errors)


if __name__ == "__main__":
    sys.exit(main())
