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
import hashlib
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

from build_framework_pipeline import (
    BEGIN_MARKER,
    END_MARKER,
    FRAMEWORK_MD_REL,
    PIPELINE_YAML_REL,
    load_pipeline_data,
    render_generated_region,
    source_path,
    validate_pipeline_data,
)


ROOT = Path.cwd()
# framework-pipeline.md is a governance source file in atomics; it is compiled into
# the runtime-dispatch-gate bundle (not as a standalone runtime file). This dev-time
# validator reads the canonical atomics source directly.
SKILL_PATH = ROOT / "atomics" / "skill" / "SKILL.md"
ATOMICS_REFERENCES_ROOT = ROOT / "atomics" / "skill" / "references"
REFERENCES_ROOT = ATOMICS_REFERENCES_ROOT
FRAMEWORK_PATH = ROOT / FRAMEWORK_MD_REL
FRAMEWORK_YAML_PATH = ROOT / PIPELINE_YAML_REL
RECURSIVE_STATE_PATH = ATOMICS_REFERENCES_ROOT / "diagnostics" / "recursive-state-transitions.md"
COMPILED_DISPATCH_GATE_PATH = ROOT / "skill" / "references" / "runtime-dispatch-gate.md"
# module-catalogue.json and coverage-scope.yaml are runtime metadata copies; read from skill/
CATALOGUE_PATH = ROOT / "skill" / "references" / "diagnostics" / "module-catalogue.json"
COVERAGE_PATH = ATOMICS_REFERENCES_ROOT / "diagnostics" / "coverage-scope.yaml"

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
    "DIAGNOSTIC REDUCTION - PHASE 2 AXES + MANDATORY PASSES",
    "DIAGNOSTIC IR - FORMATION + DISPATCH GATE",
    "GATE BLOCKED",
    "GATE OPEN",
    "ROUTING PRECEDENCE",
    "SELECTED CURRENT LIVE BURDEN",
    "OPERATIVE SUBMOVE(S)",
    "BURDEN LANDED",
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
    r"\[background\s+topic\s+appears\]\s*->\s*\[argument\s+bank\s*/\s*citation\s+dump\]",
    r"\[tradition\s+label\s+appears\]\s*->\s*\[tradition-specific\s+answer\]",
    r"\[pattern\s+print\s+emitted\]\s*->\s*\[PF\s*/\s*routing\s+precedence\s+bypassed\]",
    r"\[bounded\s+move\s+rendered\]\s*->\s*\[STOP\s+without\s+post-render\s+gate\]",
    r"\[route\s+itinerary\s+formed\s+before\s+diagnostic\s+reduction\]\s*->\s*\[current\s+bounded\s+operator\]",
    r"\[Current\s+bounded\s+operator:\s*FPD\s*->\s*M1\s*->\s*DO-8\s*->\s*M8\s*->\s*restoration\]\s*->\s*\[valid\s+live\s+burden\]",
    r"\[Burden-1\s+operative\s+submoves\]\s*->\s*\[\"?Pass\s+1\s*/\s*Pass\s+2\s*/\s*Pass\s+3\"?\s+recursion\]",
    r"\[restoration\s*/\s*pastoral\s+note\]\s*->\s*\[before\s+state\s+re-read\]",
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generated_region(text: str) -> str:
    pattern = re.compile(
        rf"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}",
        flags=re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(0) if match else ""


def strip_generated_region(text: str) -> str:
    pattern = re.compile(
        rf"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}",
        flags=re.DOTALL,
    )
    return pattern.sub("", text)


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
        candidate = ROOT / "atomics" / "skill" / ref.removeprefix("skill/")
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


def check_l_check_frontmatter(
    path: Path,
    data: dict[str, Any] | None,
    expected: dict[str, str],
    errors: list[str],
) -> None:
    if data is None:
        return
    for field, value in expected.items():
        if data.get(field) != value:
            errors.append(f"{rel(path)}: {field} must be {value!r}, found {data.get(field)!r}")

    if data.get("verification_status") == "L_check":
        missing = [field for field in VERIFICATION_FLAGS if field not in data]
        false_flags = [field for field in VERIFICATION_FLAGS if data.get(field) is not True]
        if missing:
            errors.append(f"{rel(path)}: L_check verification missing {', '.join(missing)}")
        if false_flags:
            errors.append(f"{rel(path)}: L_check verification requires true {', '.join(false_flags)}")


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
            if expected_path:
                # Catalogue paths use the compiled runtime layout (skill/references/...).
                # When checking against atomics source, also try the atomics-prefixed path.
                canonical_resolved = (ROOT / expected_path).resolve()
                atomics_resolved = (ROOT / "atomics" / expected_path).resolve()
                if canonical_resolved != path and atomics_resolved != path:
                    errors.append(f"{rel(path)}: catalogue path mismatch for id {module_id}")
    return referenced


def check_coverage_alignment(text: str, claim_ids: set[str], owner_ids: set[str], non_runtime: set[str], errors: list[str]) -> None:
    if "framework-pipeline" not in owner_ids or "governance:framework-pipeline" not in claim_ids:
        errors.append("coverage-scope.yaml: governance:framework-pipeline must map to owner framework-pipeline")
    if "recursive-state-transitions" not in owner_ids or "governance:recursive-state-transitions" not in claim_ids:
        errors.append("coverage-scope.yaml: governance:recursive-state-transitions must map to owner recursive-state-transitions")

    for ref in sorted(code_refs_in_text(text)):
        if ref not in claim_ids and ref not in non_runtime:
            errors.append(f"coverage-scope drift: framework/recursive validation surface references {ref} but coverage-scope has no claim")


def check_forbidden_shortcuts(text: str, errors: list[str]) -> None:
    section = section_text(text, "Forbidden Shortcut Paths")
    if not section:
        errors.append("missing section: ## Forbidden Shortcut Paths")
        return
    for pattern in FORBIDDEN_SHORTCUT_PATTERNS:
        if not re.search(pattern, section, flags=re.IGNORECASE):
            errors.append(f"missing forbidden shortcut matching /{pattern}/")


def check_recursive_reference(text: str, errors: list[str]) -> None:
    section = section_text(text, "Recursive State-Transition Reference")
    if not section:
        errors.append("missing section: ## Recursive State-Transition Reference")
        return
    if "recursive-state-transitions.md" not in section:
        errors.append("recursive state-transition reference must point to recursive-state-transitions.md")
    if "does not independently define" not in section:
        errors.append("framework recursive reference must disclaim independent state-model ownership")


def check_recursive_owner(text: str, errors: list[str]) -> None:
    required_tokens = [
        "STOP / HOLD / RECURSE / PARTIAL",
        "P7-restoration-stops.md",
        "diagnostic-ir.md",
        "output-release.md",
        "diagnostic-render-contract.md",
        "routing-precedence.md",
        "no premature STOP",
        "same-response RECURSE trigger checklist",
        "PARTIAL",
        "State Carry Table",
        "Held means traversal-delayed, not response-delayed",
        "Recursion is not argument dump",
        "one live burden",
    ]
    for token in required_tokens:
        if token.lower() not in text.lower():
            errors.append(f"{rel(RECURSIVE_STATE_PATH)}: missing recursive owner token {token!r}")
    for state in ["STOP", "HOLD", "RECURSE", "PARTIAL"]:
        if not re.search(rf"\b{state}\b", text):
            errors.append(f"{rel(RECURSIVE_STATE_PATH)}: recursive owner missing {state}")


def load_framework_pipeline_yaml(errors: list[str]) -> dict[str, Any]:
    if not FRAMEWORK_YAML_PATH.exists():
        errors.append(f"missing file: {rel(FRAMEWORK_YAML_PATH)}")
        return {}
    try:
        data = load_pipeline_data(ROOT)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        errors.append(f"{rel(FRAMEWORK_YAML_PATH)}: YAML parse error: {exc}")
        return {}
    errors.extend(validate_pipeline_data(data, ROOT))
    return data


def check_generated_block_fresh(framework_text: str, pipeline_data: dict[str, Any], errors: list[str]) -> None:
    if not pipeline_data:
        return
    actual = generated_region(framework_text)
    if not actual:
        errors.append(f"{rel(FRAMEWORK_PATH)}: generated framework pipeline block is missing")
        return
    expected = render_generated_region(pipeline_data).rstrip()
    if actual.rstrip() != expected:
        errors.append(
            f"{rel(FRAMEWORK_PATH)}: generated framework pipeline block is stale; "
            "run python tools/build_framework_pipeline.py"
        )


def _flatten_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).lower()


def _owner_support_text(source: str, errors: list[str]) -> str:
    path = source_path(ROOT, source)
    if not path.is_file():
        errors.append(f"{rel(FRAMEWORK_YAML_PATH)}: support owner missing: {source}")
        return ""
    text = read_text(path, errors)
    if path.resolve() == FRAMEWORK_PATH.resolve():
        text = strip_generated_region(text)
    return text


def check_yaml_support_claims(pipeline_data: dict[str, Any], errors: list[str]) -> None:
    support_claims = pipeline_data.get("support_claims") if pipeline_data else {}
    if not isinstance(support_claims, dict):
        return
    for claim_id, claim in support_claims.items():
        owners = claim.get("owners") if isinstance(claim, dict) else None
        if not isinstance(owners, list):
            continue
        for owner in owners:
            if not isinstance(owner, dict):
                continue
            source = owner.get("source")
            tokens = owner.get("tokens") or []
            if not isinstance(source, str) or not isinstance(tokens, list):
                continue
            owner_text = _flatten_whitespace(_owner_support_text(source, errors))
            for token in tokens:
                if not isinstance(token, str):
                    continue
                if _flatten_whitespace(token) not in owner_text:
                    errors.append(
                        f"{rel(FRAMEWORK_YAML_PATH)}: support claim {claim_id!r} "
                        f"is not backed by {source}: missing token {token!r}"
                    )


def check_yaml_required_nodes(pipeline_data: dict[str, Any], chart: str, errors: list[str]) -> None:
    if not pipeline_data:
        return
    nodes = pipeline_data.get("nodes") or []
    labels_by_id = {node.get("id"): node.get("label") for node in nodes if isinstance(node, dict)}
    chart_lower = chart.lower()
    for node_id in pipeline_data.get("required_order") or []:
        label = labels_by_id.get(node_id)
        if not isinstance(label, str):
            errors.append(f"{rel(FRAMEWORK_YAML_PATH)}: required_order node {node_id!r} lacks a label")
            continue
        if label.lower() not in chart_lower:
            errors.append(f"generated chart missing YAML required node {node_id}: {label}")


def check_yaml_edges(pipeline_data: dict[str, Any], chart: str, errors: list[str]) -> None:
    if not pipeline_data:
        return
    for edge in pipeline_data.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        edge_text = f"{edge.get('from')} -> {edge.get('to')}"
        if edge_text.lower() not in chart.lower():
            errors.append(f"generated chart missing YAML edge: {edge_text}")
    if "post_render_gate -> v1_diagnostic_gate" not in chart:
        errors.append("generated chart must show RECURSE returning through state re-read to V1")
    if "not topic transition" not in chart:
        errors.append("generated chart must explicitly reject topic transition as recursion")


def check_yaml_mandatory_passes(skill_text: str, pipeline_data: dict[str, Any], chart: str, errors: list[str]) -> None:
    if not pipeline_data:
        return
    expected = parse_mandatory_passes(skill_text)
    yaml_passes: list[tuple[str, str]] = []
    for node in pipeline_data.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        for item in node.get("mandatory_passes") or []:
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            file_ref = item.get("file")
            if isinstance(label, str) and isinstance(file_ref, str):
                yaml_passes.append((label, file_ref))
    if [label for label, _ref in yaml_passes] != [label for label, _ref in expected]:
        errors.append("framework-pipeline.yaml: mandatory pass labels drift from SKILL.md")
        return
    for (expected_label, expected_ref), (yaml_label, yaml_ref) in zip(expected, yaml_passes, strict=True):
        if expected_label != yaml_label or Path(expected_ref).name != Path(yaml_ref).name:
            errors.append(
                "framework-pipeline.yaml: mandatory pass drift: "
                f"expected {expected_label} {expected_ref}, found {yaml_label} {yaml_ref}"
            )
    last_pos = -1
    for label, ref in yaml_passes:
        marker = f"{label} {Path(ref).name}"
        pos = chart.find(marker)
        if pos == -1:
            errors.append(f"generated chart missing YAML mandatory pass: {marker}")
        elif pos <= last_pos:
            errors.append(f"generated chart mandatory pass order drift at {marker}")
        last_pos = pos


def check_yaml_gate_checks(pipeline_data: dict[str, Any], chart: str, errors: list[str]) -> None:
    if not pipeline_data:
        return
    for item in pipeline_data.get("gate_checks") or []:
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        owner = item.get("owner")
        if isinstance(owner, str) and not source_path(ROOT, owner).is_file():
            errors.append(f"framework-pipeline.yaml: gate check owner missing: {owner}")
        if isinstance(label, str) and label.lower() not in chart.lower():
            errors.append(f"generated chart missing YAML gate check: {label}")


def check_yaml_forbidden_shortcuts(pipeline_data: dict[str, Any], chart: str, framework_text: str, errors: list[str]) -> None:
    if not pipeline_data:
        return
    static_section = section_text(framework_text, "Forbidden Shortcut Paths")
    if not static_section:
        errors.append("missing section: ## Forbidden Shortcut Paths")
        return
    for item in pipeline_data.get("forbidden_shortcuts") or []:
        if not isinstance(item, dict):
            continue
        start = item.get("from")
        end = item.get("to")
        if not isinstance(start, str) or not isinstance(end, str):
            continue
        shortcut_text = f"[{start}] -> [{end}]"
        normalized_shortcut = re.sub(r"[`\"']", "", shortcut_text).lower()
        normalized_chart = re.sub(r"[`\"']", "", chart).lower()
        normalized_static = re.sub(r"[`\"']", "", static_section).lower()
        if normalized_shortcut not in normalized_chart:
            errors.append(f"generated chart missing YAML forbidden shortcut: {shortcut_text}")
        if normalized_shortcut not in normalized_static:
            errors.append(
                f"{rel(FRAMEWORK_YAML_PATH)}: forbidden shortcut {shortcut_text} "
                "is not backed by the framework-pipeline forbidden-shortcut section"
            )


def check_yaml_transitions(pipeline_data: dict[str, Any], chart: str, errors: list[str]) -> None:
    if not pipeline_data:
        return
    states = []
    for item in pipeline_data.get("transitions") or []:
        if not isinstance(item, dict):
            continue
        state = item.get("state")
        condition = item.get("condition")
        if isinstance(state, str):
            states.append(state)
            if not re.search(rf"\b{re.escape(state)}\b", chart):
                errors.append(f"generated chart missing transition state: {state}")
        if isinstance(condition, str) and condition.lower() not in chart.lower():
            errors.append(f"generated chart missing transition condition for {state}: {condition}")
    if states != ["STOP", "HOLD", "RECURSE", "PARTIAL"]:
        errors.append("framework-pipeline.yaml: transitions must be STOP, HOLD, RECURSE, PARTIAL in order")


def check_yaml_pass_shape_and_ttp(pipeline_data: dict[str, Any], chart: str, errors: list[str]) -> None:
    if not pipeline_data:
        return
    pass_shape = pipeline_data.get("pass_shape") or {}
    if isinstance(pass_shape, dict):
        sequence = pass_shape.get("sequence")
        if sequence != ["Layer A", "Layer B", "state re-read"]:
            errors.append("framework-pipeline.yaml: pass_shape.sequence must be Layer A -> Layer B -> state re-read")
        if "Layer A -> Layer B -> state re-read" not in chart:
            errors.append("generated chart missing Layer A -> Layer B -> state re-read pass shape")
        if pass_shape.get("recurse_repeats") is not True:
            errors.append("framework-pipeline.yaml: pass_shape.recurse_repeats must be true")
    ttp = pipeline_data.get("ttp_execution") or {}
    if isinstance(ttp, dict):
        sequence = ttp.get("sequence")
        if sequence != ["target", "operation", "result", "state re-read"]:
            errors.append("framework-pipeline.yaml: ttp_execution.sequence must be target -> operation -> result -> state re-read")
        if "target -> operation -> result -> state re-read" not in chart:
            errors.append("generated chart missing TTP execution shape")
    for token in [
        "DIAGNOSTIC REDUCTION",
        "ROUTING PRECEDENCE",
        "SELECTED CURRENT LIVE BURDEN",
        "OPERATIVE SUBMOVE(S)",
        "BURDEN LANDED",
        "current bounded operator is not a route chain",
        "operative submoves do not count as recursion",
        "burden landing precedes state re-read",
        "validated IR is runtime compiler state",
        "entry criteria: validated IR + owner + bounded target",
        "exit criteria: result + state delta + held-route recheck",
        "depth guard",
        "Layer A / Layer B release checks",
        "convergence through controlled state transitions",
        "if RECURSE: next input-anchored burden",
    ]:
        if token.lower() not in chart.lower():
            errors.append(f"generated chart missing route-chain-collapse guard: {token!r}")


def check_yaml_concept_ownership(pipeline_data: dict[str, Any], chart: str, errors: list[str]) -> None:
    if not pipeline_data:
        return
    required = {
        "ir_formation",
        "routing",
        "selected_live_burden",
        "render_shape",
        "output_release",
        "recursion",
        "framework_pipeline_audit_surface",
        "dsl_ir_representation",
        "meta_noetic_memetics_object_domain",
    }
    concepts = pipeline_data.get("concept_ownership") or []
    seen = {item.get("id") for item in concepts if isinstance(item, dict)}
    missing = sorted(required - seen)
    if missing:
        errors.append(f"framework-pipeline.yaml: missing concept ownership entries: {', '.join(missing)}")
    for item in concepts:
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        owner = item.get("owner")
        if isinstance(owner, str) and not source_path(ROOT, owner).is_file():
            errors.append(f"framework-pipeline.yaml: concept owner missing: {owner}")
        if isinstance(label, str) and label.lower() not in chart.lower():
            errors.append(f"generated chart missing concept ownership label: {label}")


def check_compiled_runtime_pipeline_surface(framework_text: str, errors: list[str]) -> None:
    if not COMPILED_DISPATCH_GATE_PATH.is_file():
        errors.append(f"compiled runtime dispatch gate missing: {rel(COMPILED_DISPATCH_GATE_PATH)}")
        return
    runtime_text = read_text(COMPILED_DISPATCH_GATE_PATH, errors)
    pattern = re.compile(
        r"<!-- SOURCE:\s*atomics/skill/references/diagnostics/framework-pipeline\.md\s*-->\s*\n"
        r"<!-- MODULE_ID:\s*framework-pipeline\s*-->\s*\n"
        r"<!-- MODULE_CLASS:\s*governance\s*-->\s*\n"
        r"<!-- CANONICAL_PATH:\s*atomics/skill/references/diagnostics/framework-pipeline\.md\s*-->\s*\n"
        r"<!-- SOURCE_SHA256:\s*(?P<sha>[0-9a-fA-F]+)\s*-->\s*\n\n"
        r"(?P<body>.*?)\n\n<!-- END_SOURCE:\s*framework-pipeline\s*-->",
        flags=re.DOTALL,
    )
    match = pattern.search(runtime_text)
    if not match:
        errors.append(f"{rel(COMPILED_DISPATCH_GATE_PATH)}: missing compiled framework-pipeline section")
        return
    current_sha = sha256_file(FRAMEWORK_PATH)
    if match.group("sha").lower() != current_sha:
        errors.append(
            f"{rel(COMPILED_DISPATCH_GATE_PATH)}: compiled framework-pipeline source hash is stale; "
            "run python tools/build_compiled_runtime.py"
        )
    if match.group("body").rstrip() != framework_text.rstrip():
        errors.append(
            f"{rel(COMPILED_DISPATCH_GATE_PATH)}: compiled framework-pipeline body is stale; "
            "run python tools/build_compiled_runtime.py"
        )
    expected_region = generated_region(framework_text)
    if expected_region and expected_region not in match.group("body"):
        errors.append(f"{rel(COMPILED_DISPATCH_GATE_PATH)}: compiled runtime lacks generated pipeline block")


def main() -> int:
    errors: list[str] = []

    if not FRAMEWORK_PATH.exists():
        print("framework-pipeline: FAIL")
        print(f"- missing file: {rel(FRAMEWORK_PATH)}")
        return 1
    if not FRAMEWORK_YAML_PATH.exists():
        print("framework-pipeline: FAIL")
        print(f"- missing file: {rel(FRAMEWORK_YAML_PATH)}")
        return 1
    if not RECURSIVE_STATE_PATH.exists():
        print("framework-pipeline: FAIL")
        print(f"- missing file: {rel(RECURSIVE_STATE_PATH)}")
        return 1

    pipeline_data = load_framework_pipeline_yaml(errors)
    framework_data, framework_text = extract_frontmatter(FRAMEWORK_PATH, errors)
    recursive_data, recursive_text = extract_frontmatter(RECURSIVE_STATE_PATH, errors)
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
            section_text(framework_text, "Recursive State-Transition Reference"),
            recursive_text,
        ]
    )

    check_l_check_frontmatter(
        FRAMEWORK_PATH,
        framework_data,
        {
            "id": "framework-pipeline",
            "module_class": "governance",
            "canonical_path": "skill/references/diagnostics/framework-pipeline.md",
        },
        errors,
    )
    check_l_check_frontmatter(
        RECURSIVE_STATE_PATH,
        recursive_data,
        {
            "id": "recursive-state-transitions",
            "module_class": "governance",
            "canonical_path": "skill/references/diagnostics/recursive-state-transitions.md",
        },
        errors,
    )
    check_generated_block_fresh(framework_text, pipeline_data, errors)
    check_yaml_support_claims(pipeline_data, errors)
    check_yaml_required_nodes(pipeline_data, normalized_chart, errors)
    check_yaml_edges(pipeline_data, normalized_chart, errors)
    check_yaml_mandatory_passes(skill_text, pipeline_data, normalized_chart, errors)
    check_yaml_gate_checks(pipeline_data, normalized_chart, errors)
    check_yaml_forbidden_shortcuts(pipeline_data, normalized_chart, framework_text, errors)
    check_yaml_transitions(pipeline_data, normalized_chart, errors)
    check_yaml_pass_shape_and_ttp(pipeline_data, normalized_chart, errors)
    check_yaml_concept_ownership(pipeline_data, normalized_chart, errors)
    check_legacy_blockquote(framework_text, errors)
    check_required_nodes(normalized_chart, errors)
    check_always_load(skill_text, normalized_chart, errors)
    check_mandatory_passes(skill_text, normalized_chart, errors)
    check_gate_checks(normalized_chart, errors)
    check_referenced_files(validation_surface, by_path, catalogue, errors)
    check_coverage_alignment(validation_surface, claim_ids, owner_ids, non_runtime, errors)
    check_forbidden_shortcuts(framework_text, errors)
    check_recursive_reference(framework_text, errors)
    check_recursive_owner(recursive_text, errors)
    check_compiled_runtime_pipeline_surface(framework_text, errors)

    if errors:
        print("framework-pipeline: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("framework-pipeline: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
