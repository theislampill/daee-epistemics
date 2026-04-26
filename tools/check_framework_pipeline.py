#!/usr/bin/env python3
"""
Validate the framework-pipeline ASCII audit surface against repo metadata.

Run from repo root:
  python tools/check_framework_pipeline.py

This is a development-time validator. It does not provide runtime authority for
the packaged skill.
"""

from __future__ import annotations

import json
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
SKILL_PATH = ROOT / "skill" / "SKILL.md"
REFERENCES_ROOT = ROOT / "skill" / "references"
FRAMEWORK_PATH = REFERENCES_ROOT / "diagnostics" / "framework-pipeline.md"
CATALOGUE_PATH = REFERENCES_ROOT / "diagnostics" / "module-catalogue.json"
COVERAGE_PATH = REFERENCES_ROOT / "diagnostics" / "coverage-scope.yaml"

VERIFICATION_FLAGS = [
    "direct_read_verified",
    "failure_conditions_present",
    "ir_consequences_present",
    "minimal_pairs_present",
    "hold_release_rules_present",
    "compiled_runtime_eligible",
    "operator_pack_eligible",
]

REQUIRED_NODES = [
    "ALWAYS-LOAD BACKGROUND",
    "V1 DIAGNOSTIC GATE",
    "PHASE 1: LISTENING",
    "PHASE 2: AXIS CLASSIFICATION + MANDATORY PASSES",
    "DIAGNOSTIC IR - FORMATION + DISPATCH GATE",
    "GATE BLOCKED",
    "GATE OPEN",
    "OUTPUT GOVERNANCE",
    "OUTPUT-RELEASE RUBRIC",
    "DIAGNOSTIC RENDER CONTRACT",
    "RESTORATION TRACE",
    "POST-RENDER RE-ENTRY GATE",
    "BOTTOM-LINE SYNTHESIS / NEXT MOVE",
]

GATE_CHECK_PATTERNS = [
    r"Mandatory\s+minimum\s+fields\s+populated",
    r"Consistency\s+rules\s+pass",
    r"routing-precedence\.md\s+suppression\s+rules",
    r"P7\s+stops\s+checked",
    r"Architectural\s+integrity\s+check\s+passed",
    r"Concealment\s+x\s+orientation\s+matrix\s+permits\s+content\s+now",
]

FORBIDDEN_SHORTCUT_PATTERNS = [
    r"\[INPUT\]\s*->\s*\[direct\s+doctrinal\s+rebuttal\]",
    r"\[IR\s+formed\s+retrospectively\]\s*->\s*\[counts\s+as\s+gate\s+pass\]",
    r"\[landed\s+move\]\s*->\s*\[stack\s+next\s+argument\s+immediately\]",
    r"\[source-audit-derived\s+topic\s+appears\]\s*->\s*\[argument\s+bank\s*/\s*citation\s+dump\]",
    r"\[tradition\s+label\s+appears\]\s*->\s*\[tradition-specific\s+answer\]",
    r"\[pattern\s+print\s+emitted\]\s*->\s*\[PF\s*/\s*routing\s+precedence\s+bypassed\]",
    r"\[bounded\s+move\s+rendered\]\s*->\s*\[STOP\s+without\s+post-render\s+gate\]",
]

CODE_REF_RE = re.compile(
    r"(?<![A-Za-z0-9-])("
    r"NS-\d+|DO-\d+|RT-\d+|PF-\d+|M\d+-P|[PEMFVR]\d+"
    r")(?![A-Za-z0-9-])"
)
RANGE_RE = re.compile(
    r"(?<![A-Za-z0-9-])(?:(?P<prefix1>NS|DO|RT|PF)-|(?P<prefix2>[PEMFVR]))"
    r"(?P<start>\d+)-(?P<end>\d+)(?![A-Za-z0-9-])"
)
FILE_REF_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"((?:skill/)?(?:references/)?(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.md)"
)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read {rel(path)}: {exc}")
        return ""


def extract_frontmatter(path: Path, errors: list[str]) -> tuple[dict[str, Any] | None, str]:
    text = read_text(path, errors)
    if not text:
        return None, ""
    if not text.startswith("---"):
        errors.append(f"{rel(path)}: missing YAML front matter")
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{rel(path)}: malformed YAML front matter")
        return None, text
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        errors.append(f"{rel(path)}: YAML parse error: {exc}")
        return None, text
    if not isinstance(data, dict):
        errors.append(f"{rel(path)}: front matter is not a mapping")
        return None, text
    return data, text


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def first_text_fence(text: str) -> str:
    match = re.search(r"```text\s*\n(.*?)\n```", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else ""


def section_text(text: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def subsection_between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    end = text.find(end_marker, start + len(start_marker))
    if end == -1:
        return text[start:]
    return text[start:end]


def markdown_section(text: str, heading: str) -> str:
    pattern = rf"^###\s+{re.escape(heading)}\s*$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^###\s+", text[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def markdown_section_prefix(text: str, heading_prefix: str) -> str:
    pattern = rf"^###\s+{re.escape(heading_prefix)}.*$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^###\s+", text[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def table_file_refs(section: str) -> list[str]:
    refs: list[str] = []
    for match in re.finditer(r"`([^`]+\.md)`", section):
        refs.append(match.group(1).strip())
    return refs


def normalize_ref(ref: str) -> str:
    ref = ref.replace("\\", "/").strip("`.,;:)(")
    if ref.startswith("skill/references/"):
        ref = ref.removeprefix("skill/references/")
    elif ref.startswith("references/"):
        ref = ref.removeprefix("references/")
    return ref


def ref_mentioned(text: str, ref: str) -> bool:
    normalized_ref = normalize_ref(ref).lower()
    normalized_text = text.replace("\\", "/").lower()
    return normalized_ref in normalized_text or Path(normalized_ref).name in normalized_text


def parse_mandatory_passes(skill_text: str) -> list[tuple[str, str]]:
    section = markdown_section_prefix(skill_text, "V1 Phase 2 Mandatory Passes")
    passes: list[tuple[str, str]] = []
    for line in section.splitlines():
        match = re.search(r"\|\s*(\[P-[A-D]\])[^|]*\|\s*`([^`]+\.md)`", line)
        if match:
            passes.append((match.group(1), match.group(2)))
    return passes


def resolve_reference(raw_ref: str, errors: list[str]) -> Path | None:
    ref = normalize_ref(raw_ref)
    if ref == "SKILL.md":
        if SKILL_PATH.exists():
            return SKILL_PATH
        errors.append("stale referenced file: SKILL.md not found")
        return None
    if ref.startswith("skill/"):
        candidate = ROOT / ref
        if candidate.exists():
            return candidate
    if "/" in ref:
        candidate = REFERENCES_ROOT / ref
        if candidate.exists():
            return candidate
        errors.append(f"stale referenced file: {raw_ref} not found")
        return None

    matches = sorted(REFERENCES_ROOT.rglob(ref))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        errors.append(f"stale referenced file: {raw_ref} not found")
        return None
    locations = ", ".join(rel(path) for path in matches)
    errors.append(f"ambiguous referenced file shorthand {raw_ref}: {locations}")
    return None


def load_all_frontmatter(errors: list[str]) -> dict[Path, dict[str, Any]]:
    by_path: dict[Path, dict[str, Any]] = {}
    for path in sorted(REFERENCES_ROOT.rglob("*.md")):
        data, _text = extract_frontmatter(path, errors)
        if data is not None:
            by_path[path.resolve()] = data
    return by_path


def load_catalogue(errors: list[str]) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(read_text(CATALOGUE_PATH, errors))
    except json.JSONDecodeError as exc:
        errors.append(f"{rel(CATALOGUE_PATH)}: JSON parse error: {exc}")
        return {}
    modules = payload.get("modules")
    if not isinstance(modules, list):
        errors.append(f"{rel(CATALOGUE_PATH)}: expected top-level modules list")
        return {}
    catalogue: dict[str, dict[str, Any]] = {}
    for entry in modules:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            errors.append(f"{rel(CATALOGUE_PATH)}: malformed module entry {entry!r}")
            continue
        catalogue[entry["id"]] = entry
    return catalogue


def load_coverage_scope(errors: list[str]) -> tuple[set[str], set[str], set[str]]:
    try:
        payload = yaml.safe_load(read_text(COVERAGE_PATH, errors))
    except yaml.YAMLError as exc:
        errors.append(f"{rel(COVERAGE_PATH)}: YAML parse error: {exc}")
        return set(), set(), set()
    if not isinstance(payload, dict):
        errors.append(f"{rel(COVERAGE_PATH)}: expected mapping")
        return set(), set(), set()

    claim_ids: set[str] = set()
    owner_ids: set[str] = set()
    non_runtime: set[str] = set()
    for item in payload.get("known_non_runtime_references", []) or []:
        if isinstance(item, dict) and isinstance(item.get("claim_id"), str):
            non_runtime.add(item["claim_id"])
    for item in payload.get("scope_claims", []) or []:
        if not isinstance(item, dict):
            continue
        claim_id = item.get("claim_id")
        if isinstance(claim_id, str):
            claim_ids.add(claim_id)
        aliases = item.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        for alias in aliases:
            if isinstance(alias, str):
                claim_ids.add(alias)
        owner_id = item.get("owner_id")
        if item.get("in_scope") is True and isinstance(owner_id, str):
            owner_ids.add(owner_id)
    return claim_ids, owner_ids, non_runtime


def expand_range(prefix: str, start: int, end: int) -> list[str]:
    if end < start or end - start > 200:
        return []
    if prefix in {"NS", "DO", "RT", "PF"}:
        return [f"{prefix}-{num}" for num in range(start, end + 1)]
    return [f"{prefix}{num}" for num in range(start, end + 1)]


def code_refs_in_text(text: str) -> set[str]:
    refs: set[str] = set()
    consumed: list[tuple[int, int]] = []
    for match in RANGE_RE.finditer(text):
        prefix = match.group("prefix1") or match.group("prefix2")
        refs.update(expand_range(prefix, int(match.group("start")), int(match.group("end"))))
        consumed.append(match.span())

    def in_range(index: int) -> bool:
        return any(start <= index < end for start, end in consumed)

    for match in CODE_REF_RE.finditer(text):
        if not in_range(match.start()):
            refs.add(match.group(1))
    return refs


def check_framework_frontmatter(data: dict[str, Any] | None, errors: list[str]) -> None:
    if data is None:
        return
    expected = {
        "id": "framework-pipeline",
        "module_class": "governance",
        "canonical_path": "skill/references/diagnostics/framework-pipeline.md",
    }
    for field, value in expected.items():
        if data.get(field) != value:
            errors.append(f"{rel(FRAMEWORK_PATH)}: {field} must be {value!r}, found {data.get(field)!r}")

    if data.get("verification_status") == "L_check":
        missing = [field for field in VERIFICATION_FLAGS if field not in data]
        false_flags = [field for field in VERIFICATION_FLAGS if data.get(field) is not True]
        if missing:
            errors.append(f"{rel(FRAMEWORK_PATH)}: L_check verification missing {', '.join(missing)}")
        if false_flags:
            errors.append(f"{rel(FRAMEWORK_PATH)}: L_check verification requires true {', '.join(false_flags)}")


def check_legacy_blockquote(text: str, errors: list[str]) -> None:
    if not text.startswith("---"):
        return
    parts = text.split("---", 2)
    if len(parts) < 3:
        return
    non_empty = 0
    for offset, line in enumerate(parts[2].splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        non_empty += 1
        if non_empty > 25:
            break
        lowered = stripped.lower()
        if lowered.startswith(("> role:", "> use when:", "> do not use when:", "> output:")):
            errors.append(
                f"{rel(FRAMEWORK_PATH)}: legacy post-YAML blockquote metadata at body line {offset}: {line}"
            )


def check_required_nodes(chart: str, errors: list[str]) -> None:
    for node in REQUIRED_NODES:
        if node.lower() not in chart.lower():
            errors.append(f"missing ASCII chart node: {node}")


def check_always_load(skill_text: str, chart: str, errors: list[str]) -> None:
    section = markdown_section(skill_text, "Always Load")
    refs = table_file_refs(section)
    if not refs:
        errors.append("skill/SKILL.md: Always Load table not found or has no .md refs")
        return
    for ref in refs:
        if not ref_mentioned(chart, ref):
            errors.append(f"Always Load drift: {ref} appears in skill/SKILL.md but not in framework chart")


def check_mandatory_passes(skill_text: str, chart: str, errors: list[str]) -> None:
    passes = parse_mandatory_passes(skill_text)
    expected_labels = ["[P-A]", "[P-B]", "[P-C]", "[P-D]"]
    if [label for label, _ref in passes] != expected_labels:
        errors.append("skill/SKILL.md: mandatory pass table does not list [P-A] through [P-D] in order")
        return

    chart_section = subsection_between(chart, "MANDATORY PASSES - run in sequence:", "Specialty markers")
    if not chart_section:
        errors.append("framework chart: mandatory pass subsection not found")
        return

    last_pos = -1
    chart_pass_labels = re.findall(r"\[P-[A-Z]\]", chart_section)
    for label, ref in passes:
        filename = Path(ref).name
        pattern = re.compile(rf"{re.escape(label)}\s+{re.escape(filename)}", re.IGNORECASE)
        match = pattern.search(chart_section)
        if not match:
            errors.append(f"missing mandatory pass {label} {filename}")
            continue
        if match.start() <= last_pos:
            errors.append(f"mandatory pass order drift at {label} {filename}")
        last_pos = match.start()

    extra = sorted(set(chart_pass_labels) - set(expected_labels))
    if extra:
        errors.append(f"framework chart implies unsupported mandatory pass label(s): {', '.join(extra)}")


def check_gate_checks(chart: str, errors: list[str]) -> None:
    for pattern in GATE_CHECK_PATTERNS:
        if not re.search(pattern, chart, flags=re.IGNORECASE):
            errors.append(f"missing diagnostic IR gate check matching /{pattern}/")


def check_referenced_files(text: str, by_path: dict[Path, dict[str, Any]], catalogue: dict[str, dict[str, Any]], errors: list[str]) -> set[Path]:
    referenced: set[Path] = set()
    for raw_ref in sorted(set(FILE_REF_RE.findall(text))):
        path = resolve_reference(raw_ref, errors)
        if path is not None:
            referenced.add(path.resolve())

    for path in sorted(referenced):
        data = by_path.get(path)
        if data is None:
            continue
        module_id = data.get("id")
        if data.get("catalogue_registered") is True and module_id not in catalogue:
            errors.append(f"{rel(path)}: referenced file is catalogue_registered but id is absent from module-catalogue.json")
        if data.get("catalogue_registered") is False:
            continue
        if data.get("catalogue_registered") is True and module_id in catalogue:
            expected_path = catalogue[module_id].get("path")
            if expected_path and (ROOT / expected_path).resolve() != path:
                errors.append(f"{rel(path)}: catalogue path mismatch for id {module_id}")
    return referenced


def check_coverage_alignment(text: str, claim_ids: set[str], owner_ids: set[str], non_runtime: set[str], errors: list[str]) -> None:
    if "framework-pipeline" not in owner_ids or "governance:framework-pipeline" not in claim_ids:
        errors.append("coverage-scope.yaml: governance:framework-pipeline must map to owner framework-pipeline")

    for ref in sorted(code_refs_in_text(text)):
        if ref not in claim_ids and ref not in non_runtime:
            errors.append(f"coverage-scope drift: framework-pipeline references {ref} but coverage-scope has no claim")


def check_forbidden_shortcuts(text: str, errors: list[str]) -> None:
    section = section_text(text, "Forbidden Shortcut Paths")
    if not section:
        errors.append("missing section: ## Forbidden Shortcut Paths")
        return
    for pattern in FORBIDDEN_SHORTCUT_PATTERNS:
        if not re.search(pattern, section, flags=re.IGNORECASE):
            errors.append(f"missing forbidden shortcut matching /{pattern}/")


def check_recursive_section(text: str, errors: list[str]) -> None:
    section = section_text(text, "Recursive State-Transition View")
    if not section:
        errors.append("missing section: ## Recursive State-Transition View")
        return
    for state in ["STOP", "HOLD", "RECURSE", "PARTIAL"]:
        if not re.search(rf"\b{state}\b", section):
            errors.append(f"recursive state-transition section missing {state}")
    if "P7-restoration-stops.md" not in section:
        errors.append("recursive state-transition section must reference P7-restoration-stops.md")


def main() -> int:
    errors: list[str] = []

    if not FRAMEWORK_PATH.exists():
        print("framework-pipeline: FAIL")
        print(f"- missing file: {rel(FRAMEWORK_PATH)}")
        return 1

    framework_data, framework_text = extract_frontmatter(FRAMEWORK_PATH, errors)
    skill_text = read_text(SKILL_PATH, errors)
    catalogue = load_catalogue(errors)
    by_path = load_all_frontmatter(errors)
    claim_ids, owner_ids, non_runtime = load_coverage_scope(errors)

    chart = first_text_fence(framework_text)
    if not chart:
        errors.append(f"{rel(FRAMEWORK_PATH)}: first ```text ASCII chart block not found")
    normalized_chart = normalize_text(chart)
    validation_surface = "\n".join(
        [
            chart,
            section_text(framework_text, "Forbidden Shortcut Paths"),
            section_text(framework_text, "Recursive State-Transition View"),
        ]
    )

    check_framework_frontmatter(framework_data, errors)
    check_legacy_blockquote(framework_text, errors)
    check_required_nodes(normalized_chart, errors)
    check_always_load(skill_text, normalized_chart, errors)
    check_mandatory_passes(skill_text, normalized_chart, errors)
    check_gate_checks(normalized_chart, errors)
    check_referenced_files(validation_surface, by_path, catalogue, errors)
    check_coverage_alignment(validation_surface, claim_ids, owner_ids, non_runtime, errors)
    check_forbidden_shortcuts(framework_text, errors)
    check_recursive_section(framework_text, errors)

    if errors:
        print("framework-pipeline: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("framework-pipeline: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
