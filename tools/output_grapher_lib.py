#!/usr/bin/env python3
"""Parse daee-epistemics outputs into a lightweight collapse graph."""

from __future__ import annotations

from dataclasses import dataclass, field
import html
import json
import re
from pathlib import Path
from typing import Any


SUP_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUB_DIGITS = "₀₁₂₃₄₅₆₇₈₉"
SUP_TO_INT = {char: str(index) for index, char in enumerate(SUP_DIGITS)}
SUB_TO_INT = {char: str(index) for index, char in enumerate(SUB_DIGITS)}
INT_TO_SUP = {str(index): char for index, char in enumerate(SUP_DIGITS)}
INT_TO_SUB = {str(index): char for index, char in enumerate(SUB_DIGITS)}

CANONICAL_BURDEN_RE = re.compile(fr"([{SUP_DIGITS}]+)B(?![{SUB_DIGITS}])")
CANONICAL_SUBMOVE_RE = re.compile(fr"([{SUP_DIGITS}]+)B([{SUB_DIGITS}]+)(?:\[([^\]\n]+)\])?")
CANONICAL_EDGE_RE = re.compile(fr"([{SUP_DIGITS}]+)B\s*→\s*([{SUP_DIGITS}]+)B")
ASCII_BURDEN_RE = re.compile(r"\bB(\d+)\b")
ASCII_EDGE_RE = re.compile(r"\bB(\d+)\s*->\s*B(\d+)\b")
ASCII_CHAIN_TOKEN_RE = re.compile(r"\bB(\d+)\b")
ASCII_SUBMOVE_RE = re.compile(r"\bB(\d+)_(\d+)\s*(?:\[([^\]\n]+)\])?")
BAD_SUBSCRIPT_BURDEN_RE = re.compile(fr"\bB([{SUB_DIGITS}]+)\b")
BURDEN_HEADING_RE = re.compile(r"^(?:#+\s*)?Burden\s+(\d+)\b", re.IGNORECASE)
LAND_RE = re.compile(fr"\b(Land|HOLD)\(([{SUP_DIGITS}]+)B\)", re.IGNORECASE)
ASCII_LAND_RE = re.compile(r"\b(Land|HOLD)\(B(\d+)\)", re.IGNORECASE)
MRP_RE = re.compile(fr"\bMRP\(([{SUP_DIGITS}]+)B\)")
ASCII_MRP_RE = re.compile(r"\bMRP\(B(\d+)\)")
ASCII_MRP_LINE_RE = re.compile(r"^\s*MRP\(B(\d+)\)", re.IGNORECASE)
MRP_BLOCK_RE = re.compile(r"\[\s*Mid-Reread Pressure\s*\]", re.IGNORECASE)
MRP_TARGET_RE = re.compile(r"^\s*Target:\s*B(\d+)\b", re.IGNORECASE)
MRP_REREAD_TARGET_RE = re.compile(r"R\(H,Delta\)\s*B(\d+)\b", re.IGNORECASE)
ASCII_RESULTANT_RE = re.compile(r"\bMRP resultant:\s*B(\d+)\s+licenses\s*(STOP|HOLD|RECURSE|LoopBreak)", re.IGNORECASE)
TERMINAL_TABLE_RE = re.compile(r"^\s*B(\d+)\s*:\s*(landed|held|partial|loopbreak|closed|discharged)", re.IGNORECASE)
ROUTE_RE = re.compile(r"\bRoute:\s*(STOP|HOLD|RECURSE|LoopBreak(?:\(∇×T\))?|LoopBreak)", re.IGNORECASE)
RESULT_TYPE_RE = re.compile(
    r"\b(held_burden_activation|generated_burden_instantiation|no_new_resultant|loopbreak|hold_partial)\b"
)
RESULTANT_RE = re.compile(r"\b(Finding|MRP resultant|Resultant|Result type):\s*([^\n;]+)", re.IGNORECASE)
FIELD_STATE_RE = re.compile(r"∇·B\s*:\s*([^;\n]+)", re.IGNORECASE)
CURL_STATE_RE = re.compile(r"∇×κ\s*:\s*([^;\n]+)", re.IGNORECASE)


def _sup_to_int(raw: str) -> int:
    digits = "".join(SUP_TO_INT.get(char, "") for char in raw)
    return int(digits) if digits else 0


def _sub_to_int(raw: str) -> int:
    digits = "".join(SUB_TO_INT.get(char, "") for char in raw)
    return int(digits) if digits else 0


def burden_token(index: int | str) -> str:
    raw = str(index)
    return "".join(INT_TO_SUP[digit] for digit in raw if digit in INT_TO_SUP) + "B"


def submove_token(burden: int | str, submove: int | str) -> str:
    return burden_token(burden) + "".join(INT_TO_SUB[digit] for digit in str(submove) if digit in INT_TO_SUB)


def normalize_burden_token(raw: str) -> str:
    raw = raw.strip()
    if re.fullmatch(fr"[{SUP_DIGITS}]+B", raw):
        return raw
    match = re.fullmatch(r"B(\d+)", raw)
    if match:
        return burden_token(match.group(1))
    return raw


@dataclass
class GraphNode:
    id: str
    kind: str
    label: str
    line: int = 0
    excerpt: str = ""
    owner: str = ""
    status: str = ""
    route: str = ""
    generated_by: str = ""


@dataclass
class GraphEdge:
    source: str
    target: str
    kind: str
    line: int = 0
    backed_by: str = ""
    excerpt: str = ""


@dataclass
class ParseResult:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    initial_burdens: list[str] = field(default_factory=list)
    burdens: list[str] = field(default_factory=list)
    generated_burdens: dict[str, str] = field(default_factory=dict)
    submoves: dict[str, list[str]] = field(default_factory=dict)
    terminals: dict[str, str] = field(default_factory=dict)
    mrp: dict[str, dict[str, Any]] = field(default_factory=dict)
    graph_edges: list[tuple[str, str, int, str]] = field(default_factory=list)
    closure_complete: bool = False
    has_layer_a: bool = False
    has_banner: bool = False
    has_restoration: bool = False
    legacy_aliases: list[str] = field(default_factory=list)
    visible_vs_field_witness: list[str] = field(default_factory=list)

    @property
    def reconstructible(self) -> bool:
        return not self.errors


def add_node(result: ParseResult, node: GraphNode) -> None:
    if node.id not in result.nodes:
        result.nodes[node.id] = node


def add_edge(result: ParseResult, edge: GraphEdge) -> None:
    if not any(existing.source == edge.source and existing.target == edge.target and existing.kind == edge.kind for existing in result.edges):
        result.edges.append(edge)


def burden_sort_key(token: str) -> int:
    match = re.match(fr"([{SUP_DIGITS}]+)B", token)
    return _sup_to_int(match.group(1)) if match else 9999


def extract_burdens(line: str, result: ParseResult, line_no: int) -> list[str]:
    found: list[str] = []
    for match in CANONICAL_BURDEN_RE.finditer(line):
        token = match.group(0)
        if token not in found:
            found.append(token)
    for match in ASCII_BURDEN_RE.finditer(line):
        token = burden_token(match.group(1))
        if token not in found:
            found.append(token)
        alias = match.group(0)
        if alias not in result.legacy_aliases:
            result.legacy_aliases.append(alias)
            result.warnings.append(
                f"line {line_no}: parsed legacy alias {alias}; public canonical notation preferred"
            )
    for match in BAD_SUBSCRIPT_BURDEN_RE.finditer(line):
        result.warnings.append(
            f"line {line_no}: {match.group(0)} looks like subscript burden notation; use superscript-before-B for burdens"
        )
    return found


def warn_legacy(result: ParseResult, line_no: int, alias: str, canonical: str) -> None:
    if alias not in result.legacy_aliases:
        result.legacy_aliases.append(alias)
        result.warnings.append(
            f"line {line_no}: parsed legacy alias {alias}; public canonical notation preferred: {canonical}"
        )


def ensure_mrp(result: ParseResult, burden: str, line_no: int, excerpt: str = "") -> dict[str, Any]:
    mrp_id = f"MRP({burden})"
    data = result.mrp.setdefault(
        burden,
        {"id": mrp_id, "line": line_no, "routes": [], "result_types": [], "edges": [], "pressure": []},
    )
    add_node(result, GraphNode(mrp_id, "mrp", mrp_id, line=line_no, excerpt=excerpt[:220]))
    add_edge(result, GraphEdge(f"R(H,Δ)@{burden}", mrp_id, "reread-mrp", line=line_no, excerpt=excerpt[:220]))
    return data


def record_dependency_edge(
    result: ParseResult,
    source: str,
    target: str,
    line_no: int,
    excerpt: str,
    current_mrp_burden: str = "",
) -> None:
    if not any(existing_source == source and existing_target == target for existing_source, existing_target, _line, _excerpt in result.graph_edges):
        result.graph_edges.append((source, target, line_no, excerpt[:220]))
    add_node(result, GraphNode(source, "burden", source))
    add_node(result, GraphNode(target, "burden", target))
    add_edge(result, GraphEdge(source, target, "dependency", line=line_no, excerpt=excerpt[:220]))
    if current_mrp_burden:
        data = ensure_mrp(result, current_mrp_burden, line_no, excerpt)
        if (source, target) not in data["edges"]:
            data["edges"].append((source, target))


def parse_output(text: str, field_witness_text: str | None = None) -> ParseResult:
    result = ParseResult()
    lines = text.splitlines()
    add_node(result, GraphNode("input", "input", "input", excerpt="pasted daee-epistemics output"))

    route_records: list[tuple[str, str, int]] = []
    mrp_line_for: dict[str, int] = {}
    last_burden = ""
    current_mrp_burden = ""
    pending_mrp_block = False

    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        if "NOETIC FIELD EXECUTION" in line or "governed execution" in line.lower():
            result.has_banner = True
        if "Layer A" in line or "DSL" in line and "IR" in line:
            result.has_layer_a = True
        if "coverage_complete=true" in line or "coverage_complete: true" in line:
            result.closure_complete = True
        if "restoration" in line.lower() or "T_lang" in line or "Ψᴺ ⇢ Ψᴵ" in line:
            result.has_restoration = True

        line_burdens = extract_burdens(line, result, index)
        heading_match = BURDEN_HEADING_RE.match(stripped)
        if heading_match:
            heading_burden = burden_token(heading_match.group(1))
            line_burdens = [heading_burden] + [token for token in line_burdens if token != heading_burden]
        is_initial_line = bool(re.search(r"initial burden|burden inventory|initial set|held/live burden", line, re.I))
        is_heading = bool(re.match(r"^(#+\s*)?(Burden\s+\d+\b|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\b)", stripped))

        for token in line_burdens:
            if token not in result.burdens:
                result.burdens.append(token)
            add_node(result, GraphNode(token, "burden", token, line=index, excerpt=stripped[:220]))
            if is_initial_line and token not in result.initial_burdens:
                result.initial_burdens.append(token)
            if is_heading:
                last_burden = token

        for match in CANONICAL_SUBMOVE_RE.finditer(line):
            burden = burden_token(_sup_to_int(match.group(1)))
            submove = submove_token(_sup_to_int(match.group(1)), _sub_to_int(match.group(2)))
            owner = (match.group(3) or "").strip()
            add_node(result, GraphNode(submove, "submove", submove, line=index, excerpt=stripped[:220], owner=owner))
            result.submoves.setdefault(burden, [])
            if submove not in result.submoves[burden]:
                result.submoves[burden].append(submove)
            add_node(result, GraphNode(burden, "burden", burden))
            add_edge(result, GraphEdge(burden, submove, "burden-submove", line=index, excerpt=stripped[:220]))

        for match in ASCII_SUBMOVE_RE.finditer(line):
            burden = burden_token(match.group(1))
            submove = submove_token(match.group(1), match.group(2))
            owner = (match.group(3) or "").strip()
            warn_legacy(result, index, match.group(0), f"{submove}[{owner}]" if owner else submove)
            if burden not in result.burdens:
                result.burdens.append(burden)
            add_node(result, GraphNode(burden, "burden", burden, line=index, excerpt=stripped[:220]))
            add_node(result, GraphNode(submove, "submove", submove, line=index, excerpt=stripped[:220], owner=owner))
            result.submoves.setdefault(burden, [])
            if submove not in result.submoves[burden]:
                result.submoves[burden].append(submove)
            add_edge(result, GraphEdge(burden, submove, "burden-submove", line=index, excerpt=stripped[:220]))
            last_burden = burden

        generated_by = MRP_RE.search(line)
        generated_by_ascii = ASCII_MRP_RE.search(line)
        if "generated-by" in line and line_burdens and (generated_by or generated_by_ascii):
            new_burden = line_burdens[0]
            source_mrp = (
                f"MRP({burden_token(_sup_to_int(generated_by.group(1)))})"
                if generated_by
                else f"MRP({burden_token(generated_by_ascii.group(1))})"
            )
            result.generated_burdens[new_burden] = source_mrp
            result.nodes[new_burden].generated_by = source_mrp

        land_match = LAND_RE.search(line)
        if land_match:
            burden = burden_token(_sup_to_int(land_match.group(2)))
            terminal = "HOLD" if land_match.group(1).upper() == "HOLD" else "Land"
            result.terminals[burden] = terminal
            land_id = f"{terminal}({burden})"
            add_node(result, GraphNode(land_id, "land" if terminal == "Land" else "terminal", land_id, line=index, excerpt=stripped[:220], status=terminal))
            add_node(result, GraphNode(burden, "burden", burden))
            add_edge(result, GraphEdge(burden, land_id, "burden-terminal", line=index, excerpt=stripped[:220]))
            last_burden = burden
        else:
            ascii_land_match = ASCII_LAND_RE.search(line)
            if ascii_land_match:
                burden = burden_token(ascii_land_match.group(2))
                terminal = "HOLD" if ascii_land_match.group(1).upper() == "HOLD" else "Land"
                result.terminals[burden] = terminal
                land_id = f"{terminal}({burden})"
                warn_legacy(result, index, ascii_land_match.group(0), land_id)
                add_node(result, GraphNode(land_id, "land" if terminal == "Land" else "terminal", land_id, line=index, excerpt=stripped[:220], status=terminal))
                add_node(result, GraphNode(burden, "burden", burden))
                add_edge(result, GraphEdge(burden, land_id, "burden-terminal", line=index, excerpt=stripped[:220]))
                last_burden = burden

        if "R(H,Δ)" in line or "R(H,Delta)" in line:
            if "R(H,Delta)" in line:
                result.warnings.append(f"line {index}: parsed legacy alias R(H,Delta); use R(H,Δ)")
            target = line_burdens[0] if line_burdens else last_burden
            reread_target = MRP_REREAD_TARGET_RE.search(line)
            if reread_target:
                target = burden_token(reread_target.group(1))
                warn_legacy(result, index, f"R(H,Delta) B{reread_target.group(1)}", f"R(H,Δ)@{target}")
            reread_id = f"R(H,Δ)@{target or index}"
            add_node(result, GraphNode(reread_id, "reread", "R(H,Δ)", line=index, excerpt=stripped[:220]))
            if target:
                add_edge(result, GraphEdge(f"Land({target})", reread_id, "land-reread", line=index, excerpt=stripped[:220]))

        if MRP_BLOCK_RE.search(line):
            pending_mrp_block = True
            current_mrp_burden = ""

        target_match = MRP_TARGET_RE.search(line)
        if pending_mrp_block and target_match:
            burden = burden_token(target_match.group(1))
            current_mrp_burden = burden
            mrp_line_for[burden] = index
            ensure_mrp(result, burden, index, stripped)
            warn_legacy(result, index, target_match.group(0).strip(), f"MRP({burden})")

        mrp_match = MRP_RE.search(line)
        if mrp_match:
            burden = burden_token(_sup_to_int(mrp_match.group(1)))
            current_mrp_burden = burden
            mrp_line_for[burden] = index
            ensure_mrp(result, burden, index, stripped)

        ascii_mrp_line_match = ASCII_MRP_LINE_RE.search(line)
        if ascii_mrp_line_match:
            burden = burden_token(ascii_mrp_line_match.group(1))
            current_mrp_burden = burden
            mrp_line_for[burden] = index
            ensure_mrp(result, burden, index, stripped)
            warn_legacy(result, index, ascii_mrp_line_match.group(0).strip(), f"MRP({burden})")

        result_type = RESULT_TYPE_RE.search(line)
        if result_type:
            burden = last_burden
            if current_mrp_burden:
                burden = current_mrp_burden
            if mrp_line_for:
                burden = sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0]
            if burden:
                ensure_mrp(result, burden, index, stripped)["result_types"].append(result_type.group(1))

        ascii_resultant_match = ASCII_RESULTANT_RE.search(line)
        if ascii_resultant_match:
            burden = burden_token(ascii_resultant_match.group(1))
            route = ascii_resultant_match.group(2)
            current_mrp_burden = burden
            mrp_line_for[burden] = index
            data = ensure_mrp(result, burden, index, stripped)
            data["pressure"].append(stripped)
            if route not in data["routes"]:
                data["routes"].append(route)
            route_id = f"Route:{route}@{burden}"
            add_node(result, GraphNode(route_id, "terminal", f"Route: {route}", line=index, excerpt=stripped[:220], route=route))
            add_edge(result, GraphEdge(f"MRP({burden})", route_id, "mrp-route", line=index, excerpt=stripped[:220]))

        resultant_match = RESULTANT_RE.search(line)
        if resultant_match and (mrp_line_for or current_mrp_burden):
            burden = current_mrp_burden or sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0]
            ensure_mrp(result, burden, index, stripped)["pressure"].append(resultant_match.group(2).strip())

        route_match = ROUTE_RE.search(line)
        if route_match:
            route = route_match.group(1)
            burden = line_burdens[0] if line_burdens else last_burden
            if current_mrp_burden:
                burden = current_mrp_burden
            if mrp_line_for:
                burden = sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0]
            route_records.append((burden, route, index))
            route_id = f"Route:{route}@{burden or index}"
            add_node(result, GraphNode(route_id, "terminal", f"Route: {route}", line=index, excerpt=stripped[:220], route=route))
            if burden:
                data = ensure_mrp(result, burden, index, stripped)
                if route not in data["routes"]:
                    data["routes"].append(route)
                add_edge(result, GraphEdge(f"MRP({burden})", route_id, "mrp-route", line=index, excerpt=stripped[:220]))

        terminal_table_match = TERMINAL_TABLE_RE.search(line)
        if terminal_table_match:
            burden = burden_token(terminal_table_match.group(1))
            raw_state = terminal_table_match.group(2).lower()
            terminal = "HOLD" if raw_state in {"held", "partial"} else "Land"
            result.terminals[burden] = terminal
            terminal_id = f"{terminal}({burden})"
            warn_legacy(result, index, f"B{terminal_table_match.group(1)}:", f"{burden}: terminal={terminal}")
            add_node(result, GraphNode(terminal_id, "land" if terminal == "Land" else "terminal", terminal_id, line=index, excerpt=stripped[:220], status=terminal))
            add_node(result, GraphNode(burden, "burden", burden))
            add_edge(result, GraphEdge(burden, terminal_id, "burden-terminal", line=index, excerpt=stripped[:220]))

        is_dependency_summary = bool(re.search(r"Burden dependency graph", line, re.I))

        for match in CANONICAL_EDGE_RE.finditer(line):
            source = burden_token(_sup_to_int(match.group(1)))
            target = burden_token(_sup_to_int(match.group(2)))
            edge_mrp = "" if is_dependency_summary else current_mrp_burden or (sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0] if mrp_line_for else "")
            record_dependency_edge(result, source, target, index, stripped, edge_mrp)

        for match in ASCII_EDGE_RE.finditer(line):
            source = burden_token(match.group(1))
            target = burden_token(match.group(2))
            warn_legacy(result, index, match.group(0), f"{source} → {target}")
            edge_mrp = "" if is_dependency_summary else current_mrp_burden or (sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0] if mrp_line_for else "")
            record_dependency_edge(result, source, target, index, stripped, edge_mrp)

        if "->" in line and "Burden dependency graph" in line and ";" not in line:
            chain = [burden_token(match.group(1)) for match in ASCII_CHAIN_TOKEN_RE.finditer(line)]
            for source, target in zip(chain, chain[1:]):
                warn_legacy(result, index, f"{source}->{target}", f"{source} → {target}")
                record_dependency_edge(result, source, target, index, stripped)

    result.burdens = sorted(set(result.burdens), key=burden_sort_key)
    result.initial_burdens = sorted(set(result.initial_burdens), key=burden_sort_key)

    validate_result(result, lines, route_records)
    if field_witness_text:
        compare_field_witness(result, field_witness_text)
    return result


def validate_result(result: ParseResult, lines: list[str], route_records: list[tuple[str, str, int]]) -> None:
    if result.closure_complete and not result.initial_burdens:
        result.errors.append("initial burden set missing while closure claims coverage_complete=true")
    if result.closure_complete:
        for burden in result.initial_burdens or result.burdens:
            if burden not in result.terminals:
                result.errors.append(f"{burden} lacks terminal Land/HOLD accounting while closure claims complete")
    known = set(result.burdens) | set(result.initial_burdens)
    for source, target, line, _excerpt in result.graph_edges:
        if source not in known:
            result.errors.append(f"line {line}: dependency edge source {source} is unknown")
        if target not in known:
            result.errors.append(f"line {line}: dependency edge target {target} is unknown")
    for source, target, line, excerpt in result.graph_edges:
        if result.mrp and not any((source, target) in data.get("edges", []) for data in result.mrp.values()):
            result.errors.append(f"line {line}: dependency edge {source} → {target} lacks MRP/resultant backing")
    for burden, data in result.mrp.items():
        has_result = bool(data.get("routes") or data.get("result_types") or data.get("pressure") or data.get("edges"))
        if not has_result:
            result.errors.append(f"{data.get('id', f'MRP({burden})')} appears as a label with no resultant/route consequence")
    for burden in result.burdens:
        if burden in result.terminals and result.terminals[burden].lower() == "land" and not result.submoves.get(burden):
            result.warnings.append(f"{burden} lands without visible submoves")
    for burden, route, line_no in route_records:
        if route.upper() == "STOP":
            later = "\n".join(lines[line_no:])
            if re.search(r"Layer B|^#+\s*Burden\s+\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\s+\[generated-by", later, re.M):
                result.errors.append(f"line {line_no}: Route: STOP is followed by later burden / Layer B work")
    text = "\n".join(lines)
    field_states = [match.group(1).strip().lower() for match in FIELD_STATE_RE.finditer(text)]
    curl_states = [match.group(1).strip().lower() for match in CURL_STATE_RE.finditer(text)]
    if result.closure_complete and any(not state.startswith("neutral") for state in field_states) and not re.search(r"Route:\s*(HOLD|RECURSE)|HOLD\(", text, re.I):
        result.errors.append("coverage_complete=true while ∇·B is non-neutral without HOLD/RECURSE explanation")
    if result.closure_complete and any(not state.startswith("null") and "resolved" not in state for state in curl_states) and not re.search(r"LoopBreak|resolved|null", text, re.I):
        result.errors.append("coverage_complete=true while ∇×κ is non-null without LoopBreak/resolution")
    for match in re.finditer(r"T_lang[^\n]{0,180}guaranteed uptake", text, re.I):
        window = match.group(0).lower()
        if not re.search(r"\b(no|not|non|does not|without|denies|boundary)\b", window):
            result.errors.append("T_lang boundary appears to claim guaranteed uptake")


def compare_field_witness(result: ParseResult, raw_json: str) -> None:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        result.errors.append(f"field_witness JSON is invalid: {exc}")
        return
    if not isinstance(payload, dict):
        result.errors.append("field_witness JSON must be an object")
        return
    witness_nodes = {normalize_burden_token(str(item)) for item in payload.get("nodes", []) if isinstance(item, str)}
    visible_burdens = set(result.burdens)
    if witness_nodes and witness_nodes != visible_burdens:
        result.visible_vs_field_witness.append(
            f"node mismatch visible={sorted(visible_burdens, key=burden_sort_key)} field_witness={sorted(witness_nodes, key=burden_sort_key)}"
        )
    witness_edges: set[tuple[str, str]] = set()
    for edge in payload.get("edges", []):
        if isinstance(edge, dict):
            source = normalize_burden_token(str(edge.get("source", "")))
            target = normalize_burden_token(str(edge.get("target", "")))
            if source and target:
                witness_edges.add((source, target))
        elif isinstance(edge, (list, tuple)) and len(edge) == 2:
            witness_edges.add((normalize_burden_token(str(edge[0])), normalize_burden_token(str(edge[1]))))
    visible_edges = {(source, target) for source, target, _line, _excerpt in result.graph_edges}
    if witness_edges and witness_edges != visible_edges:
        result.visible_vs_field_witness.append(
            f"edge mismatch visible={sorted(visible_edges)} field_witness={sorted(witness_edges)}"
        )


def result_summary(result: ParseResult) -> dict[str, Any]:
    return {
        "burdens": result.burdens,
        "initial_burdens": result.initial_burdens,
        "submove_count": sum(len(items) for items in result.submoves.values()),
        "mrp_count": len(result.mrp),
        "generated_burdens": result.generated_burdens,
        "terminal_count": len(result.terminals),
        "closure_complete": result.closure_complete,
        "reconstructible": result.reconstructible,
        "errors": result.errors,
        "warnings": result.warnings + result.visible_vs_field_witness,
    }


def graph_html(result: ParseResult, title: str = "Output Collapse Grapher Result") -> str:
    nodes = list(result.nodes.values())
    positions: dict[str, tuple[int, int]] = {}
    width = 1390
    node_width = 170
    row_height = 72
    lane_gap = 46
    positions["input"] = (30, 40)
    y = 40
    burden_ids = result.burdens or [node.id for node in nodes if node.kind == "burden"]
    for burden in burden_ids:
        submoves = result.submoves.get(burden, [])
        lane_height = max(148, len(submoves) * row_height + lane_gap)
        positions[burden] = (220, y)
        for sub_index, submove in enumerate(submoves):
            positions[submove] = (410, y + sub_index * row_height)
        for terminal_id in (f"Land({burden})", f"HOLD({burden})"):
            if terminal_id in result.nodes:
                positions[terminal_id] = (620, y)
        reread_id = f"R(H,Δ)@{burden}"
        if reread_id in result.nodes:
            positions[reread_id] = (800, y)
        mrp_id = f"MRP({burden})"
        if mrp_id in result.nodes:
            positions[mrp_id] = (980, y)
        route_nodes = [node for node in nodes if node.kind == "terminal" and node.id.endswith(f"@{burden}")]
        for route_index, node in enumerate(route_nodes):
            positions[node.id] = (1160, y + route_index * row_height)
        y += lane_height
    unplaced = [node for node in nodes if node.id not in positions]
    for index, node in enumerate(unplaced):
        positions[node.id] = (30 + (index % 7) * 190, y + (index // 7) * row_height)
    height = max(220, y + 120)
    edge_lines = []
    for edge in result.edges:
        if edge.source not in positions or edge.target not in positions:
            continue
        sx, sy = positions[edge.source]
        tx, ty = positions[edge.target]
        edge_lines.append(
            f'<line x1="{sx + 170}" y1="{sy + 24}" x2="{tx}" y2="{ty + 24}" stroke="#64748b" stroke-width="1.6" marker-end="url(#arrow)"/>'
        )
    node_lines = []
    color = {
        "input": "#64748b",
        "burden": "#3b82f6",
        "submove": "#38bdf8",
        "land": "#22c55e",
        "reread": "#f59e0b",
        "mrp": "#a855f7",
        "terminal": "#eab308",
        "closure": "#22c55e",
    }
    for node in nodes:
        x, y = positions.get(node.id, (30, 30))
        fill = color.get(node.kind, "#64748b")
        if node.id in result.generated_burdens:
            fill = "#8b5cf6"
        if any(error for error in result.errors if node.id in error):
            fill = "#ef4444"
        raw_label = f"{node.label} [{node.owner}]" if node.kind == "submove" and node.owner else node.label
        label = html.escape(raw_label[:30])
        kind = html.escape(node.kind)
        node_lines.append(
            f'<g tabindex="0"><rect x="{x}" y="{y}" width="{node_width}" height="54" rx="8" fill="{fill}" opacity=".88"/>'
            f'<text x="{x + 10}" y="{y + 22}" fill="#fff" font-size="13" font-weight="700">{label}</text>'
            f'<text x="{x + 10}" y="{y + 42}" fill="#e2e8f0" font-size="10">{kind}</text><title>{html.escape(node.excerpt or node.id)}</title></g>'
        )
    node_rows = "\n".join(
        f"<tr><td>{html.escape(node.id)}</td><td>{html.escape(node.kind)}</td><td>{html.escape(node.owner)}</td><td>{html.escape(node.status or node.route)}</td><td>{html.escape(node.excerpt)}</td></tr>"
        for node in nodes
    )
    edge_rows = "\n".join(
        f"<tr><td>{html.escape(edge.source)}</td><td>{html.escape(edge.target)}</td><td>{html.escape(edge.kind)}</td><td>{html.escape(edge.excerpt)}</td></tr>"
        for edge in result.edges
    )
    validation_rows = "\n".join(f"<li class='error'>{html.escape(item)}</li>" for item in result.errors) or "<li>No hard errors.</li>"
    warning_rows = "\n".join(f"<li class='warn'>{html.escape(item)}</li>" for item in result.warnings + result.visible_vs_field_witness) or "<li>No warnings.</li>"
    verdict = "reconstructible" if result.reconstructible else "not reconstructible"
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body{{font-family:system-ui,Segoe UI,sans-serif;background:#0b1020;color:#e5e7eb;margin:24px}}
svg{{max-width:100%;background:#050914;border:1px solid #334155;border-radius:12px}}
table{{width:100%;border-collapse:collapse;margin:14px 0}}td,th{{border:1px solid #334155;padding:6px;vertical-align:top}}th{{background:#111827}}
.error{{color:#fecaca}}.warn{{color:#fde68a}}.summary{{display:flex;gap:10px;flex-wrap:wrap}}.pill{{border:1px solid #334155;border-radius:999px;padding:6px 10px;background:#111827}}
</style>
<h1>{html.escape(title)}</h1>
<div class="summary"><span class="pill">Verdict: {verdict}</span><span class="pill">Burdens: {len(result.burdens)}</span><span class="pill">Submoves: {sum(len(v) for v in result.submoves.values())}</span><span class="pill">MRP: {len(result.mrp)}</span></div>
<svg viewBox="0 0 {width} {height}" role="img" aria-label="Output collapse graph">
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>
{''.join(edge_lines)}
{''.join(node_lines)}
</svg>
<h2>Validation</h2><ul>{validation_rows}</ul><h2>Warnings</h2><ul>{warning_rows}</ul>
<h2>Nodes</h2><table><thead><tr><th>Node</th><th>Type</th><th>Owner/TTP</th><th>Status/route</th><th>Source excerpt</th></tr></thead><tbody>{node_rows}</tbody></table>
<h2>Edges</h2><table><thead><tr><th>Source</th><th>Target</th><th>Type</th><th>Source excerpt</th></tr></thead><tbody>{edge_rows}</tbody></table>
</html>"""
