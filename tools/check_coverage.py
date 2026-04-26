#!/usr/bin/env python3
"""
check_coverage.py - Validate recognized coverage scope, not just YAML files.

Run from repo root:
  python tools/check_coverage.py
  python tools/check_coverage.py --report docs/generated/coverage-report.md

Convention used by this validator:
  - coverage-scope.yaml enumerates recognized scope claims and maps each
    in-scope claim to one packaged owner id.
  - Owner front matter carries runtime metadata plus verification/status
    metadata. Verification fields are validated when present. A manifest entry
    may require L_check explicitly with required_status.

The manifest is a validation surface. Diagnostic IR remains the runtime dispatch
authority; YAML and coverage-scope do not route live cases.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


ROOT = Path.cwd()
REFERENCES_ROOT = ROOT / "skill" / "references"
CATALOGUE_PATH = REFERENCES_ROOT / "diagnostics" / "module-catalogue.json"
MANIFEST_PATH = REFERENCES_ROOT / "diagnostics" / "coverage-scope.yaml"
TODO_PATH = ROOT / "TODO.md"

PUBLIC_ROUTER_FILES = [
    ROOT / "skill" / "SKILL.md",
    ROOT / "README.md",
    REFERENCES_ROOT / "case-library" / "INDEX.md",
    REFERENCES_ROOT / "case-library" / "profiles" / "INDEX.md",
    REFERENCES_ROOT / "tactics" / "INDEX.md",
    REFERENCES_ROOT / "techniques" / "INDEX.md",
    REFERENCES_ROOT / "procedures" / "INDEX.md",
    REFERENCES_ROOT / "diagnostics" / "INDEX.md",
    REFERENCES_ROOT / "module-codes.md",
]

VALID_MODULE_CLASS = {
    "tactic",
    "technique",
    "procedure",
    "diagnostic",
    "case-library",
    "case_library",
    "governance",
    "rubric",
}
VALID_OUTPUT_SHAPES = {
    "bounded-single-pass",
    "held-pending-upstream",
    "recursive-traversal-permitted",
    "pass-through",
}
VALID_LAYER_CONSTRAINT = {"layer-a-only", "layer-b-permitted", "layer-b-governed"}
VALID_VERIFICATION_STATUS = {"L_check", "L_tilde"}
REQUIRED_FIELDS = ["id", "module_class", "canonical_path", "contract_version"]
VERIFICATION_FLAGS = [
    "direct_read_verified",
    "failure_conditions_present",
    "ir_consequences_present",
    "minimal_pairs_present",
    "hold_release_rules_present",
    "compiled_runtime_eligible",
    "operator_pack_eligible",
]
DEPRECATED_FIELDS = {
    "load_class", "bundle", "execution_phase", "governs", "must_precede",
    "blocks_if_missing", "trigger_conditions", "operator_pack", "source_status",
    "direct_read_required",
}

CODE_REF_RE = re.compile(
    r"(?<![A-Za-z0-9-])("
    r"NS-\d+|DO-\d+|RT-\d+|PF-\d+|M\d+-P|[PEMFVR]\d+"
    r")(?![A-Za-z0-9-])"
)
RANGE_RE = re.compile(
    r"(?<![A-Za-z0-9-])(?:(?P<prefix1>NS|DO|RT|PF)-|(?P<prefix2>[PEMFVR]))"
    r"(?P<start>\d+)\.\.(?P<end>\d+)(?![A-Za-z0-9-])"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)


def extract_frontmatter(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"{rel(path)}: cannot read file: {exc}"]
    if not text.startswith("---"):
        return None, [f"{rel(path)}: no YAML front matter"]
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, [f"{rel(path)}: malformed YAML front matter"]
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        return None, [f"{rel(path)}: YAML parse error: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{rel(path)}: front matter is not a mapping"]
    return data, []


def check_enum(errors: list[str], path: Path, data: dict[str, Any], field: str, valid: set[str]) -> None:
    if field not in data:
        return
    value = data[field]
    values = value if isinstance(value, list) else [value]
    bad = [item for item in values if item not in valid]
    if bad:
        add_error(errors, f"{rel(path)}: {field} contains invalid value(s) {bad}; allowed {sorted(valid)}")


def check_deprecated_fields(errors: list[str], path: Path, data: dict[str, Any]) -> None:
    found = sorted(field for field in DEPRECATED_FIELDS if field in data)
    if found:
        add_error(
            errors,
            f"{rel(path)}: deprecated transitional frontmatter field(s): {', '.join(found)}",
        )


def has_l_check_fields(data: dict[str, Any]) -> bool:
    return data.get("verification_status") == "L_check" and all(
        data.get(field) is True for field in VERIFICATION_FLAGS
    )


def check_verification_fields(errors: list[str], path: Path, data: dict[str, Any]) -> None:
    present = [field for field in ["verification_status", *VERIFICATION_FLAGS] if field in data]
    if not present:
        return
    if "verification_status" not in data:
        add_error(errors, f"{rel(path)}: verification flag(s) present without verification_status")
    check_enum(errors, path, data, "verification_status", VALID_VERIFICATION_STATUS)
    for field in VERIFICATION_FLAGS:
        if field in data and not isinstance(data[field], bool):
            add_error(errors, f"{rel(path)}: {field} must be boolean when present")
    if data.get("verification_status") == "L_check":
        missing = [field for field in VERIFICATION_FLAGS if field not in data]
        if missing:
            add_error(errors, f"{rel(path)}: L_check verification missing required flag(s): {', '.join(missing)}")
        false_flags = [field for field in VERIFICATION_FLAGS if data.get(field) is not True]
        if false_flags:
            add_error(errors, f"{rel(path)}: L_check verification requires true flag(s): {', '.join(false_flags)}")


def load_frontmatter(errors: list[str]) -> tuple[dict[str, list[tuple[Path, dict[str, Any]]]], dict[Path, dict[str, Any]]]:
    by_id: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    by_path: dict[Path, dict[str, Any]] = {}
    for path in sorted(REFERENCES_ROOT.rglob("*.md")):
        data, file_errors = extract_frontmatter(path)
        errors.extend(file_errors)
        if data is None:
            continue

        for field in REQUIRED_FIELDS:
            if field not in data:
                add_error(errors, f"{rel(path)}: missing required field {field!r}")

        check_enum(errors, path, data, "module_class", VALID_MODULE_CLASS)
        check_enum(errors, path, data, "output_shapes", VALID_OUTPUT_SHAPES)
        check_enum(errors, path, data, "layer_constraint", VALID_LAYER_CONSTRAINT)
        check_verification_fields(errors, path, data)
        check_deprecated_fields(errors, path, data)

        stated_path = data.get("canonical_path")
        if stated_path and stated_path != rel(path):
            add_error(errors, f"{rel(path)}: canonical_path mismatch: {stated_path!r}")

        module_id = data.get("id")
        if isinstance(module_id, str):
            by_id.setdefault(module_id, []).append((path, data))
        by_path[path] = data

    for module_id, entries in sorted(by_id.items()):
        if len(entries) > 1:
            locations = ", ".join(rel(path) for path, _data in entries)
            add_error(errors, f"duplicate YAML id {module_id!r}: {locations}")

    return by_id, by_path


def load_catalogue(errors: list[str]) -> list[dict[str, Any]]:
    if not CATALOGUE_PATH.exists():
        add_error(errors, f"module catalogue missing: {rel(CATALOGUE_PATH)}")
        return []
    try:
        payload = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add_error(errors, f"{rel(CATALOGUE_PATH)}: JSON parse error: {exc}")
        return []
    modules = payload.get("modules")
    if not isinstance(modules, list):
        add_error(errors, f"{rel(CATALOGUE_PATH)}: expected top-level 'modules' list")
        return []
    return modules


def check_catalogue_alignment(
    errors: list[str],
    by_id: dict[str, list[tuple[Path, dict[str, Any]]]],
    by_path: dict[Path, dict[str, Any]],
    modules: list[dict[str, Any]],
) -> None:
    catalogue_ids: set[str] = set()
    for entry in modules:
        module_id = entry.get("id")
        path_text = entry.get("path")
        module_class = entry.get("module_class")
        if not isinstance(module_id, str) or not isinstance(path_text, str) or not isinstance(module_class, str):
            add_error(errors, f"{rel(CATALOGUE_PATH)}: malformed module entry {entry!r}")
            continue
        catalogue_ids.add(module_id)
        path = ROOT / path_text
        if not path.exists():
            add_error(errors, f"catalogue entry {module_id}: path does not exist: {path_text}")
            continue
        owners = by_id.get(module_id, [])
        if len(owners) != 1:
            add_error(errors, f"catalogue entry {module_id}: id appears {len(owners)} time(s) in YAML")
            continue
        owner_path, data = owners[0]
        if owner_path.resolve() != path.resolve():
            add_error(errors, f"catalogue entry {module_id}: path {path_text} != YAML file {rel(owner_path)}")
        if data.get("module_class") != module_class:
            add_error(errors, f"catalogue entry {module_id}: module_class {module_class!r} != YAML {data.get('module_class')!r}")
        if data.get("catalogue_registered", True) is not True:
            add_error(errors, f"catalogue entry {module_id}: YAML catalogue_registered must be true or omitted")

    for path, data in sorted(by_path.items(), key=lambda item: rel(item[0])):
        module_id = data.get("id")
        if module_id in catalogue_ids:
            continue
        module_class = data.get("module_class")
        if module_class in {"governance", "rubric"}:
            if data.get("catalogue_registered") is not False:
                add_error(errors, f"{rel(path)}: governance/rubric file outside catalogue must set catalogue_registered: false")
        elif data.get("catalogue_registered", True) is True:
            add_error(errors, f"{rel(path)}: non-governance file is not in module-catalogue.json")


def load_manifest(errors: list[str]) -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        add_error(errors, f"coverage manifest missing: {rel(MANIFEST_PATH)}")
        return {}
    try:
        payload = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        add_error(errors, f"{rel(MANIFEST_PATH)}: YAML parse error: {exc}")
        return {}
    if not isinstance(payload, dict):
        add_error(errors, f"{rel(MANIFEST_PATH)}: expected mapping")
        return {}
    if not isinstance(payload.get("scope_claims"), list):
        add_error(errors, f"{rel(MANIFEST_PATH)}: expected scope_claims list")
    return payload


def check_manifest_alignment(
    errors: list[str],
    by_id: dict[str, list[tuple[Path, dict[str, Any]]]],
    manifest: dict[str, Any],
) -> tuple[set[str], set[str], set[str]]:
    covered: set[str] = set()
    noncovered: set[str] = set()
    nonruntime: set[str] = set()
    seen_claims: set[str] = set()

    todo_text = TODO_PATH.read_text(encoding="utf-8") if TODO_PATH.exists() else ""
    if not todo_text:
        add_error(errors, "TODO.md is missing or empty")

    for item in manifest.get("known_non_runtime_references", []) or []:
        claim_id = item.get("claim_id")
        if isinstance(claim_id, str):
            nonruntime.add(claim_id)

    for item in manifest.get("scope_claims", []) or []:
        if not isinstance(item, dict):
            add_error(errors, f"{rel(MANIFEST_PATH)}: scope_claims item is not a mapping: {item!r}")
            continue
        claim_id = item.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            add_error(errors, f"{rel(MANIFEST_PATH)}: scope_claim missing claim_id: {item!r}")
            continue
        if claim_id in seen_claims:
            add_error(errors, f"{rel(MANIFEST_PATH)}: duplicate claim_id {claim_id}")
        seen_claims.add(claim_id)

        aliases = item.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        for alias in aliases:
            if isinstance(alias, str):
                seen_claims.add(alias)

        if item.get("in_scope") is False:
            status = item.get("status")
            if status not in {"needs-review", "out-of-scope"}:
                add_error(errors, f"{claim_id}: in_scope false requires status needs-review or out-of-scope")
            anchor = item.get("todo_anchor")
            if not isinstance(anchor, str) or anchor not in todo_text:
                add_error(errors, f"{claim_id}: TODO anchor {anchor!r} not found")
            noncovered.add(claim_id)
            for alias in aliases:
                if isinstance(alias, str):
                    noncovered.add(alias)
            continue

        if item.get("in_scope") is not True:
            add_error(errors, f"{claim_id}: in_scope must be true or false")
            continue

        owner_id = item.get("owner_id")
        if not isinstance(owner_id, str) or not owner_id:
            add_error(errors, f"{claim_id}: in-scope claim missing owner_id")
            continue
        owners = by_id.get(owner_id, [])
        if len(owners) != 1:
            add_error(errors, f"{claim_id}: owner_id {owner_id!r} appears {len(owners)} time(s) in YAML")
            continue
        owner_path, data = owners[0]
        if "TODO" in owner_path.parts:
            add_error(errors, f"{claim_id}: owner must be an operative file, not TODO")

        required_status = item.get("required_status")
        if required_status is not None:
            if required_status not in {"L_check", "L_equivalent"}:
                add_error(errors, f"{claim_id}: unsupported required_status {required_status!r}")
            elif not has_l_check_fields(data):
                add_error(
                    errors,
                    f"{claim_id}: owner {owner_id!r} does not satisfy L_check verification fields",
                )

        covered.add(claim_id)
        for alias in aliases:
            if isinstance(alias, str):
                covered.add(alias)

    return covered, noncovered, nonruntime


def expand_range(prefix: str, start: int, end: int) -> list[str]:
    if end < start or end - start > 200:
        return []
    if prefix in {"NS", "DO", "RT", "PF"}:
        return [f"{prefix}-{num}" for num in range(start, end + 1)]
    return [f"{prefix}{num}" for num in range(start, end + 1)]


def refs_in_text(text: str) -> list[tuple[str, int]]:
    refs: list[tuple[str, int]] = []
    consumed: list[tuple[int, int]] = []
    for match in RANGE_RE.finditer(text):
        prefix = match.group("prefix1") or match.group("prefix2")
        start = int(match.group("start"))
        end = int(match.group("end"))
        line = text.count("\n", 0, match.start()) + 1
        for ref in expand_range(prefix, start, end):
            refs.append((ref, line))
        consumed.append(match.span())

    def inside_consumed(index: int) -> bool:
        return any(start <= index < end for start, end in consumed)

    for match in CODE_REF_RE.finditer(text):
        if inside_consumed(match.start()):
            continue
        refs.append((match.group(1), text.count("\n", 0, match.start()) + 1))
    return refs


def check_overclaims(
    errors: list[str],
    covered: set[str],
    noncovered: set[str],
    nonruntime: set[str],
) -> list[tuple[str, str, int, str]]:
    findings: list[tuple[str, str, int, str]] = []
    known = covered | noncovered | nonruntime
    for path in PUBLIC_ROUTER_FILES:
        if not path.exists():
            add_error(errors, f"public/router file missing: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for ref, line in refs_in_text(text):
            if ref in covered:
                findings.append((ref, rel(path), line, "covered"))
            elif ref in nonruntime:
                findings.append((ref, rel(path), line, "non-runtime"))
            elif ref in noncovered:
                findings.append((ref, rel(path), line, "needs-review/out-of-scope"))
            elif ref not in known:
                add_error(errors, f"FAIL: {ref} appears in {rel(path)}:{line} but is not present in coverage-scope and has no owner")
    return findings


def write_report(
    report_path: Path,
    errors: list[str],
    manifest: dict[str, Any],
    overclaim_findings: list[tuple[str, str, int, str]],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    claims = manifest.get("scope_claims", []) or []
    in_scope = [item for item in claims if isinstance(item, dict) and item.get("in_scope") is True]
    non_scope = [item for item in claims if isinstance(item, dict) and item.get("in_scope") is False]
    lines = [
        "# Coverage Report",
        "",
        f"- Result: {'FAIL' if errors else 'PASS'}",
        f"- In-scope claims: {len(in_scope)}",
        f"- Needs-review/out-of-scope claims: {len(non_scope)}",
        f"- Public code references scanned: {len(overclaim_findings)}",
        "",
    ]
    if errors:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    lines.extend(["## Public References", ""])
    for ref, path, line, status in overclaim_findings:
        lines.append(f"- `{ref}` in `{path}:{line}` — {status}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate coverage scope claims")
    parser.add_argument("--report", help="Optional markdown report path")
    args = parser.parse_args()

    errors: list[str] = []

    if not REFERENCES_ROOT.is_dir():
        print("ERROR: skill/references not found. Run from repo root.")
        return 1

    by_id, by_path = load_frontmatter(errors)
    modules = load_catalogue(errors)
    check_catalogue_alignment(errors, by_id, by_path, modules)
    manifest = load_manifest(errors)
    covered, noncovered, nonruntime = check_manifest_alignment(errors, by_id, manifest)
    overclaim_findings = check_overclaims(errors, covered, noncovered, nonruntime)

    if args.report:
        write_report(ROOT / args.report, errors, manifest, overclaim_findings)

    claims = manifest.get("scope_claims", []) or []
    in_scope_count = sum(1 for item in claims if isinstance(item, dict) and item.get("in_scope") is True)
    scoped_out_count = sum(1 for item in claims if isinstance(item, dict) and item.get("in_scope") is False)

    print("Coverage validation")
    print("------------------------------------------------------------")
    print(f"Frontmatter files scanned:       {len(by_path)}")
    print(f"Module-catalogue entries:        {len(modules)}")
    print(f"Manifest in-scope claims:        {in_scope_count}")
    print(f"Manifest needs-review/out-scope: {scoped_out_count}")
    print(f"Public/router files scanned:     {len(PUBLIC_ROUTER_FILES)}")
    print(f"Public code references found:    {len(overclaim_findings)}")
    print("------------------------------------------------------------")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("RESULT: FAIL")
        return 1

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
