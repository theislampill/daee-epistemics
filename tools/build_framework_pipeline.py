#!/usr/bin/env python3
"""Generate the framework-pipeline ASCII chart from structured metadata."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - dev environment failure
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


PIPELINE_YAML_REL = "atomics/skill/references/diagnostics/framework-pipeline.yaml"
FRAMEWORK_MD_REL = "atomics/skill/references/diagnostics/framework-pipeline.md"
BEGIN_MARKER = "<!-- BEGIN GENERATED FRAMEWORK PIPELINE -->"
END_MARKER = "<!-- END GENERATED FRAMEWORK PIPELINE -->"

REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "scope",
    "generated_region",
    "nodes",
    "required_order",
    "edges",
    "gate_checks",
    "forbidden_shortcuts",
    "transitions",
    "pass_shape",
    "ttp_execution",
    "concept_ownership",
    "support_claims",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def posix_rel(path: Path, root: Path | None = None) -> str:
    base = root or repo_root()
    return path.relative_to(base).as_posix()


def source_path(root: Path, raw_path: str) -> Path:
    normalized = raw_path.replace("\\", "/")
    if normalized.startswith("atomics/skill/"):
        return root / normalized
    if normalized == "skill/SKILL.md":
        return root / "atomics/skill/SKILL.md"
    if normalized.startswith("skill/"):
        return root / "atomics/skill" / normalized.removeprefix("skill/")
    if normalized.startswith("references/"):
        return root / "atomics/skill" / normalized
    return root / normalized


def load_pipeline_data(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    path = root / PIPELINE_YAML_REL
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{PIPELINE_YAML_REL}: expected top-level mapping")
    return payload


def _is_list_of_dicts(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, dict) for item in value)


def _validate_owner(root: Path, raw_path: str, errors: list[str], context: str) -> None:
    path = source_path(root, raw_path)
    if not path.is_file():
        errors.append(f"{context}: owner source missing: {raw_path}")


def validate_pipeline_data(data: dict[str, Any], root: Path | None = None) -> list[str]:
    root = root or repo_root()
    errors: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - set(data))
    if missing:
        errors.append(f"{PIPELINE_YAML_REL}: missing top-level key(s): {', '.join(missing)}")

    extra = sorted(set(data) - REQUIRED_TOP_LEVEL_KEYS)
    if extra:
        errors.append(f"{PIPELINE_YAML_REL}: unsupported top-level key(s): {', '.join(extra)}")

    generated_region = data.get("generated_region")
    if not isinstance(generated_region, dict):
        errors.append("generated_region must be a mapping")
    else:
        if generated_region.get("begin") != BEGIN_MARKER:
            errors.append("generated_region.begin does not match generator marker")
        if generated_region.get("end") != END_MARKER:
            errors.append("generated_region.end does not match generator marker")

    nodes = data.get("nodes")
    if not _is_list_of_dicts(nodes):
        errors.append("nodes must be a list of mappings")
        nodes = []
    node_ids: set[str] = set()
    for index, node in enumerate(nodes):
        node_id = node.get("id")
        label = node.get("label")
        owner = node.get("owner")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"nodes[{index}]: missing id")
            continue
        if node_id in node_ids:
            errors.append(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
        if not isinstance(label, str) or not label:
            errors.append(f"node {node_id}: missing label")
        if not isinstance(owner, str) or not owner:
            errors.append(f"node {node_id}: missing owner")
        else:
            _validate_owner(root, owner, errors, f"node {node_id}")
        lines = node.get("lines", [])
        if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
            errors.append(f"node {node_id}: lines must be a list of strings")
        if "mandatory_passes" in node and not _is_list_of_dicts(node["mandatory_passes"]):
            errors.append(f"node {node_id}: mandatory_passes must be a list of mappings")

    required_order = data.get("required_order")
    if not isinstance(required_order, list) or not all(isinstance(item, str) for item in required_order):
        errors.append("required_order must be a list of node ids")
        required_order = []
    for node_id in required_order:
        if node_id not in node_ids:
            errors.append(f"required_order references unknown node: {node_id}")

    for section_name in ("edges", "gate_checks", "forbidden_shortcuts", "transitions", "concept_ownership"):
        section = data.get(section_name)
        if not _is_list_of_dicts(section):
            errors.append(f"{section_name} must be a list of mappings")
            continue
        for index, entry in enumerate(section):
            owner = entry.get("owner")
            if isinstance(owner, str):
                _validate_owner(root, owner, errors, f"{section_name}[{index}]")

    for index, edge in enumerate(data.get("edges", []) if isinstance(data.get("edges"), list) else []):
        start = edge.get("from")
        end = edge.get("to")
        if start not in node_ids:
            errors.append(f"edges[{index}]: unknown from node {start!r}")
        if end not in node_ids:
            errors.append(f"edges[{index}]: unknown to node {end!r}")

    support_claims = data.get("support_claims")
    if not isinstance(support_claims, dict):
        errors.append("support_claims must be a mapping")
        support_claims = {}
    for claim_id, claim in support_claims.items():
        if not isinstance(claim, dict):
            errors.append(f"support_claims.{claim_id}: must be a mapping")
            continue
        owners = claim.get("owners")
        if not _is_list_of_dicts(owners):
            errors.append(f"support_claims.{claim_id}.owners must be a list of mappings")
            continue
        for owner_index, owner in enumerate(owners):
            source = owner.get("source")
            tokens = owner.get("tokens")
            if not isinstance(source, str):
                errors.append(f"support_claims.{claim_id}.owners[{owner_index}]: missing source")
            else:
                _validate_owner(root, source, errors, f"support_claims.{claim_id}")
            if not isinstance(tokens, list) or not all(isinstance(token, str) for token in tokens):
                errors.append(f"support_claims.{claim_id}.owners[{owner_index}].tokens must be strings")

    declared_claims = set(support_claims) if isinstance(support_claims, dict) else set()
    for section_name in ("nodes", "edges", "gate_checks", "transitions", "concept_ownership"):
        for index, entry in enumerate(data.get(section_name, []) if isinstance(data.get(section_name), list) else []):
            claim = entry.get("support_claim")
            if isinstance(claim, str) and claim not in declared_claims:
                errors.append(f"{section_name}[{index}] references unknown support_claim: {claim}")

    for section_name in ("pass_shape", "ttp_execution"):
        entry = data.get(section_name)
        if not isinstance(entry, dict):
            errors.append(f"{section_name} must be a mapping")
            continue
        owner = entry.get("owner")
        if isinstance(owner, str):
            _validate_owner(root, owner, errors, section_name)
        else:
            errors.append(f"{section_name}: missing owner")
        sequence = entry.get("sequence")
        if not isinstance(sequence, list) or not all(isinstance(item, str) for item in sequence):
            errors.append(f"{section_name}.sequence must be a list of strings")
        claim = entry.get("support_claim")
        if isinstance(claim, str) and claim not in declared_claims:
            errors.append(f"{section_name} references unknown support_claim: {claim}")

    return errors


def _box(title: str, lines: list[str]) -> list[str]:
    content = [title, *lines]
    width = max(48, *(len(line) for line in content)) + 2
    rendered = ["+" + "-" * width + "+"]
    for index, line in enumerate(content):
        rendered.append("| " + line.ljust(width - 2) + " |")
        if index == 0 and lines:
            rendered.append("|" + " " * width + "|")
    rendered.append("+" + "-" * width + "+")
    return rendered


def _two_column_boxes(left_title: str, left_lines: list[str], right_title: str, right_lines: list[str]) -> list[str]:
    left = _box(left_title, left_lines)
    right = _box(right_title, right_lines)
    left_width = max(len(line) for line in left)
    right_width = max(len(line) for line in right)
    height = max(len(left), len(right))
    rows: list[str] = []
    for index in range(height):
        left_line = left[index] if index < len(left) else " " * left_width
        right_line = right[index] if index < len(right) else " " * right_width
        rows.append(left_line.ljust(left_width) + "  " + right_line.ljust(right_width))
    return rows


def _node_by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["id"]: node for node in data["nodes"]}


def _display_owner(raw_path: str) -> str:
    normalized = raw_path.replace("\\", "/")
    if normalized.startswith("skill/references/"):
        return normalized.removeprefix("skill/references/")
    if normalized == "skill/SKILL.md":
        return "SKILL.md"
    return normalized


def _node_lines(node: dict[str, Any]) -> list[str]:
    lines = list(node.get("lines") or [])
    if node.get("owner"):
        lines.append(f"owner: {_display_owner(node['owner'])}")
    passes = node.get("mandatory_passes") or []
    if passes:
        lines.append("")
        lines.append("MANDATORY PASSES - run in sequence:")
        for item in passes:
            file_name = Path(str(item["file"]).replace("\\", "/")).name
            lines.append(f"{item['label']} {file_name}")
            lines.append(f"  emit: {item['emits']}")
        lines.append("")
        lines.append("Specialty markers surface here only if present.")
    return lines


def render_chart(data: dict[str, Any]) -> str:
    nodes = _node_by_id(data)
    lines: list[str] = []
    order = list(data["required_order"])

    user_node = nodes["user_input"]
    lines.append(f"[{user_node['label']}]")
    lines.append("             |")
    lines.append("             v")

    for node_id in (
        "always_load",
        "v1_diagnostic_gate",
        "phase1_listening",
        "phase2_mandatory_passes",
        "diagnostic_ir",
        "selected_held_registers",
    ):
        node = nodes[node_id]
        lines.extend(_box(node["label"], _node_lines(node)))
        lines.append("             |")
        lines.append("             v")

    left = nodes["gate_blocked"]
    right = nodes["gate_open"]
    lines.append("       +-----+-----+")
    lines.append("       |           |")
    lines.append("       v           v")
    lines.extend(_two_column_boxes(left["label"], _node_lines(left), right["label"], _node_lines(right)))
    lines.append("       |           |")
    lines.append("       +-----+-----+")
    lines.append("             |")
    lines.append("             v")

    for node_id in (
        "routing_precedence",
        "selected_live_burden",
        "operative_submoves",
        "delta_transition",
        "burden_result",
        "output_governance",
        "output_release",
        "render_contract",
        "noetic_field_banner",
        "pass_shape",
        "bounded_layer_b",
        "post_render_gate",
        "restoration_trace",
        "bottom_line",
    ):
        node = nodes[node_id]
        lines.extend(_box(node["label"], _node_lines(node)))
        if node_id != "bottom_line":
            lines.append("             |")
            lines.append("             v")

    lines.append("")
    lines.append("RECURSION LOOP")
    lines.append("- post_render_gate -> v1_diagnostic_gate [RECURSE through state re-read, not topic transition]")
    lines.append("- one bounded live burden per burden-cycle")
    lines.append("- burden-cycle begins only after burden landing + state re-read")
    lines.append("- depth guard: no next operator without refreshed warrant")
    lines.append("- if RECURSE: next input-anchored burden is routed from refreshed state")
    lines.append("- STOP only with no eligible burden, or HOLD/PARTIAL reason")

    pass_shape = data["pass_shape"]
    pass_sequence = " -> ".join(pass_shape["sequence"])
    lines.append("")
    lines.append("PASS SHAPE")
    lines.append(f"- {pass_sequence}")
    if pass_shape.get("recurse_repeats") is True:
        lines.append("- RECURSE repeats the pass shape")
    for item in pass_shape.get("release_checks") or []:
        lines.append(f"- release check: {item}")

    ttp = data["ttp_execution"]
    lines.append("")
    lines.append("TTP EXECUTION")
    lines.append(f"- {' -> '.join(ttp['sequence'])}")
    for item in ttp.get("entry_criteria") or []:
        lines.append(f"- entry criteria: {item}")
    for item in ttp.get("exit_criteria") or []:
        lines.append(f"- exit criteria: {item}")
    for item in ttp.get("depth_guards") or []:
        lines.append(f"- depth guard: {item}")
    lines.append("- one selected live burden may contain multiple operative submoves")
    lines.append("- operative submoves do not count as recursion")

    lines.append("")
    lines.append("GATE CHECKS")
    for index, check in enumerate(data["gate_checks"], start=1):
        lines.append(f"{index}. {check['label']}")

    lines.append("")
    lines.append("TRANSITIONS")
    for item in data["transitions"]:
        lines.append(f"- {item['state']}: {item['condition']}")

    lines.append("")
    lines.append("EDGE INDEX")
    for edge in data["edges"]:
        label = f" [{edge['label']}]" if edge.get("label") else ""
        lines.append(f"- {edge['from']} -> {edge['to']}{label}")

    lines.append("")
    lines.append("FORBIDDEN SHORTCUTS (generated index)")
    for shortcut in data["forbidden_shortcuts"]:
        lines.append(f"- [{shortcut['from']}] -> [{shortcut['to']}]")

    lines.append("")
    lines.append("CONCEPT OWNERSHIP (owner-backed)")
    for concept in data["concept_ownership"]:
        lines.append(f"- {concept['label']}: {_display_owner(concept['owner'])}")

    # Touch order so schema drift is visible to the generated chart even if visual nodes are special-cased.
    lines.append("")
    lines.append("REQUIRED ORDER")
    lines.append("- " + " -> ".join(order))

    return "\n".join(lines).rstrip() + "\n"


def render_generated_region(data: dict[str, Any]) -> str:
    return f"{BEGIN_MARKER}\n```text\n{render_chart(data)}```\n{END_MARKER}\n"


def replace_generated_region(markdown: str, generated_region: str) -> tuple[str, bool]:
    if BEGIN_MARKER in markdown or END_MARKER in markdown:
        pattern = re.compile(
            rf"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}\n?",
            flags=re.DOTALL,
        )
        replaced, count = pattern.subn(generated_region, markdown)
        if count != 1:
            raise ValueError("generated region markers are malformed or duplicated")
        return replaced, replaced != markdown

    heading = "## Pipeline Audit Chart"
    heading_index = markdown.find(heading)
    if heading_index == -1:
        raise ValueError("missing section: ## Pipeline Audit Chart")
    after_heading = markdown[heading_index:]
    fence = re.search(r"```text\s*\n.*?\n```", after_heading, flags=re.DOTALL | re.IGNORECASE)
    if not fence:
        raise ValueError("missing text fence under ## Pipeline Audit Chart")
    start = heading_index + fence.start()
    end = heading_index + fence.end()
    replaced = markdown[:start] + generated_region.rstrip() + "\n" + markdown[end:].lstrip("\r\n")
    return replaced, True


def build() -> int:
    root = repo_root()
    yaml_path = root / PIPELINE_YAML_REL
    markdown_path = root / FRAMEWORK_MD_REL

    try:
        data = load_pipeline_data(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print("framework-pipeline build: FAIL")
        print(f"- {PIPELINE_YAML_REL}: {exc}")
        return 1

    errors = validate_pipeline_data(data, root)
    if errors:
        print("framework-pipeline build: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    try:
        markdown = markdown_path.read_text(encoding="utf-8")
        generated_region = render_generated_region(data)
        updated, changed = replace_generated_region(markdown, generated_region)
    except (OSError, ValueError) as exc:
        print("framework-pipeline build: FAIL")
        print(f"- {exc}")
        return 1

    if changed:
        markdown_path.write_text(updated, encoding="utf-8", newline="\n")

    print("framework-pipeline build: PASS")
    print(f"Source: {posix_rel(yaml_path, root)}")
    print(f"Output: {posix_rel(markdown_path, root)}")
    print(f"Changed: {'yes' if changed else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
