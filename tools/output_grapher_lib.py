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
ASCII_EDGE_RE = re.compile(r"\bB(\d+)\s*(?:->|→)\s*B(\d+)\b")
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
HIGH_LEVERAGE_HELD_ROUTE_RE = re.compile(
    r"(?i)\b(?:independent lordship|canon[- ]wide|textual criticism|epistemology of canon|"
    r"full Christology|source/proof-stack|source authority|proof[- ]stack|mystery shield|"
    r"worldview recoil|moral tribunal shift|authority-order|predication|source-worldview|"
    r"Christology|theology|hiddenness|metaphysics|epistemology|identity/worldview|"
    r"historical/transmission|transmission|source-authority|analogy[- ]stack|shubha|"
    r"shakk|rayb|moral protest|secular moral|source[- ]order|criterion)\b"
)
UNROUTED_HELD_ROUTE_RE = re.compile(
    r"(?i)\b(?:not released|unreleased|held beyond|beyond prompt|beyond bounded claim|"
    r"held outside scope|not worked)\b"
)
TERMINAL_CLOSURE_RE = re.compile(r"(?i)\b(?:STOP|closure|complete|collapse achieved|no remaining live problem)\b")
ROUTING_OR_BOUNDARY_PROOF_RE = re.compile(
    r"(?i)\b(?:held_burden_activation|generated_burden_instantiation|HOLD|PARTIAL|"
    r"coverage_complete\s*=\s*false|non[- ]load[- ]bearing|not load[- ]bearing|"
    r"not needed for (?:this|the) (?:scoped|bounded|local) claim|scope gate|"
    r"local closure only|partial closure)\b"
)


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


def extract_balanced_json_from(text: str, start_index: int) -> str:
    source = str(text or "")
    opener_match = re.search(r"[\{\[]", source[start_index:])
    if not opener_match:
        return ""
    json_start = start_index + opener_match.start()
    opener = source[json_start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    escaped = False
    for index in range(json_start, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return source[json_start : index + 1]
    return ""


def extract_embedded_field_witness(text: str) -> str:
    match = re.search(r"(?:^|\n)\s*(?:#+\s*)?field_witness\b", str(text or ""), re.IGNORECASE)
    if not match:
        return ""
    return extract_balanced_json_from(text, match.start())


def canonical_json(value: Any) -> Any:
    if isinstance(value, list):
        return [canonical_json(item) for item in value]
    if isinstance(value, dict):
        return {key: canonical_json(value[key]) for key in sorted(value)}
    return value


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
    body_burdens: list[str] = field(default_factory=list)
    ledger: dict[str, list[str]] = field(default_factory=lambda: {"B_LA": [], "B_MRP": [], "B_total": []})
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


def canonical_burden_indices(line: str) -> set[str]:
    indices: set[str] = set()
    for match in CANONICAL_BURDEN_RE.finditer(line):
        indices.add(str(_sup_to_int(match.group(1))))
    return indices


def allowed_paired_alias_context(line: str) -> bool:
    """Allow checker-owned ASCII IDs only when canonical notation is present too."""

    if re.search(r"(?i)^\s*LoopBreak\s*:", line):
        return True
    return bool(
        re.search(
            r"(?i)^\s*(?:Landed delta|Route-gradient|R\(H,Δ\)|R\(H,Delta\)|Target|"
            r"Field diagnostics|MRP resultant)\s*:",
            line,
        )
        or re.search(r"(?i)\b(?:Delta\(B\d+\)|B_LA|B_MRP|B_total|field_witness)\b", line)
    )


def extract_burdens(line: str, result: ParseResult, line_no: int) -> list[str]:
    found: list[str] = []
    for match in CANONICAL_BURDEN_RE.finditer(line):
        token = match.group(0)
        if token not in found:
            found.append(token)
    canonical_indices = canonical_burden_indices(line)
    paired_alias_context = allowed_paired_alias_context(line)
    for match in ASCII_BURDEN_RE.finditer(line):
        token = burden_token(match.group(1))
        if token not in found:
            found.append(token)
        alias = match.group(0)
        is_delta_alias = bool(
            re.search(rf"(?i)\bDelta\(\s*{re.escape(alias)}\s*\)", line)
        )
        is_paired_parser_alias = match.group(1) in canonical_indices or (paired_alias_context and is_delta_alias)
        if not is_paired_parser_alias and alias not in result.legacy_aliases:
            result.legacy_aliases.append(alias)
            result.warnings.append(
                f"line {line_no}: parsed legacy alias {alias}; public canonical notation preferred"
            )
    for match in BAD_SUBSCRIPT_BURDEN_RE.finditer(line):
        result.warnings.append(
            f"line {line_no}: {match.group(0)} looks like subscript burden notation; use superscript-before-B for burdens"
        )
    return found


def clean_visible_ledger_segment(segment: str) -> str:
    """Keep ledger membership tokens while removing provenance source aliases.

    A visible ledger line may say `⁸B [generated-by: MRP(⁷B)]`. The member is
    `⁸B`; `⁷B` is provenance and must not be backfilled into B_MRP. Likewise a
    union formula such as `𝔅_total = 𝔅_LA ∪ 𝔅_MRP` is a relation, not an
    explicit member list.
    """

    cleaned = re.sub(r"\[generated-by:\s*MRP\([^\)]*\)\]", "", str(segment), flags=re.IGNORECASE)
    cleaned = re.sub(r"\bMRP\([^\)]*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:B_|𝔅_)(?:LA|MRP|total)\b", "", cleaned, flags=re.IGNORECASE)
    return cleaned


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
        {
            "id": mrp_id,
            "line": line_no,
            "routes": [],
            "result_types": [],
            "edges": [],
            "pressure": [],
            "route_gradient": "",
            "divergence": "",
            "curl": "",
        },
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
    body_stop_match = re.search(
        r"(?:^|\n)\s*(?:#+\s*)?(?:Closure/Reconstruction Witness|Closure Witness|Reconstruction Witness|Closure audit|field_witness)\b",
        str(text or ""),
        re.IGNORECASE,
    )
    body_line_count = str(text or "")[: body_stop_match.start()].count("\n") + 1 if body_stop_match else len(lines)
    field_witness_match = re.search(r"(?:^|\n)\s*(?:#+\s*)?field_witness\b", str(text or ""), re.IGNORECASE)
    field_witness_line = (
        str(text or "")[: field_witness_match.start()].count("\n") + 1 if field_witness_match else 10**9
    )
    add_node(result, GraphNode("input", "input", "input", excerpt="pasted daee-epistemics output"))

    route_records: list[tuple[str, str, int]] = []
    mrp_line_for: dict[str, int] = {}
    last_burden = ""
    current_mrp_burden = ""
    pending_mrp_block = False

    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        if index >= field_witness_line:
            continue
        if not stripped:
            continue
        if re.match(
            r"(?i)^(?:#+\s*)?(?:Restorative Response|Closing Formulation|Closure/Reconstruction Witness|Closure Witness|Reconstruction Witness)\b",
            stripped,
        ):
            pending_mrp_block = False
            current_mrp_burden = ""
        if "NOETIC FIELD EXECUTION" in line or "governed execution" in line.lower():
            result.has_banner = True
        if "Layer A" in line or "DSL" in line and "IR" in line:
            result.has_layer_a = True
        if "coverage_complete=true" in line or "coverage_complete: true" in line:
            result.closure_complete = True
        if "restoration" in line.lower() or "T_lang" in line or "Ψᴺ ⇢ Ψᴵ" in line:
            result.has_restoration = True

        line_burdens = extract_burdens(line, result, index)
        ledger_line = re.search(r"^\s*(?:[-*]\s*)?(?:B_|𝔅_)(LA|MRP|total)\b", line, re.IGNORECASE)
        if ledger_line:
            key = "B_total" if ledger_line.group(1).lower() == "total" else f"B_{ledger_line.group(1).upper()}"
            ledger_segment = line[ledger_line.start() :]
            value_start = re.search(r"[=:]", ledger_segment)
            ledger_segment = (
                ledger_segment[value_start.end() :] if value_start else line[ledger_line.end() :]
            )
            next_ledger = re.search(r"\b(?:B_|𝔅_)(?:LA|MRP|total)\b", ledger_segment, re.IGNORECASE)
            if next_ledger and next_ledger.start() > 0:
                ledger_segment = ledger_segment[: next_ledger.start()]
            ledger_segment = clean_visible_ledger_segment(ledger_segment)
            for token in extract_burdens(ledger_segment, result, index):
                if token not in result.ledger[key]:
                    result.ledger[key].append(token)
        heading_match = BURDEN_HEADING_RE.match(stripped)
        if heading_match:
            heading_burden = burden_token(heading_match.group(1))
            line_burdens = [heading_burden] + [token for token in line_burdens if token != heading_burden]
        is_initial_line = bool(re.search(r"initial burden|burden inventory|initial set|held/live burden", line, re.I))
        is_heading = bool(re.match(r"^(#+\s*)?(Burden\s+\d+\b|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\b)", stripped))

        for token in line_burdens:
            if token not in result.burdens:
                result.burdens.append(token)
            if index <= body_line_count and token not in result.body_burdens:
                result.body_burdens.append(token)
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
            source_burden = (
                burden_token(_sup_to_int(generated_by.group(1)))
                if generated_by
                else burden_token(generated_by_ascii.group(1))
            )
            new_burden = next((token for token in line_burdens if token != source_burden), "")
            source_mrp = f"MRP({source_burden})"
            if new_burden:
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
            if "R(H,Delta)" in line and not allowed_paired_alias_context(line):
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
        if mrp_match and "generated-by" not in line:
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
            burden = current_mrp_burden or (last_burden if pending_mrp_block else "")
            if not burden and mrp_line_for:
                burden = sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0]
            if burden:
                current_mrp_burden = burden
                mrp_line_for[burden] = index
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
        if resultant_match and (mrp_line_for or current_mrp_burden or (pending_mrp_block and last_burden)):
            burden = current_mrp_burden or (last_burden if pending_mrp_block else "") or sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0]
            current_mrp_burden = burden
            mrp_line_for[burden] = index
            ensure_mrp(result, burden, index, stripped)["pressure"].append(resultant_match.group(2).strip())

        active_mrp_burden = (
            current_mrp_burden
            or (last_burden if pending_mrp_block else "")
            or (sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0] if mrp_line_for else "")
        )
        if active_mrp_burden and pending_mrp_block:
            route_gradient_match = re.search(r"(?i)^\s*Route-gradient\s*:\s*(?P<body>.+)$", line)
            field_state_match = FIELD_STATE_RE.search(line)
            curl_state_match = CURL_STATE_RE.search(line)
            if route_gradient_match:
                ensure_mrp(result, active_mrp_burden, index, stripped)["route_gradient"] = route_gradient_match.group("body").strip()
            if field_state_match:
                ensure_mrp(result, active_mrp_burden, index, stripped)["divergence"] = first_state(field_state_match.group(1))
            if curl_state_match:
                ensure_mrp(result, active_mrp_burden, index, stripped)["curl"] = first_state(curl_state_match.group(1))

        route_match = ROUTE_RE.search(line)
        if route_match:
            route = route_match.group(1)
            burden = current_mrp_burden or (last_burden if pending_mrp_block else "") or (line_burdens[0] if line_burdens else last_burden)
            if not burden and mrp_line_for:
                burden = sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0]
            current_mrp_burden = burden
            if burden:
                mrp_line_for[burden] = index
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
        in_body = index <= body_line_count

        for match in CANONICAL_EDGE_RE.finditer(line):
            source = burden_token(_sup_to_int(match.group(1)))
            target = burden_token(_sup_to_int(match.group(2)))
            edge_mrp = "" if (is_dependency_summary or not in_body) else current_mrp_burden or (sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0] if mrp_line_for else "")
            record_dependency_edge(result, source, target, index, stripped, edge_mrp)

        for match in ASCII_EDGE_RE.finditer(line):
            source = burden_token(match.group(1))
            target = burden_token(match.group(2))
            warn_legacy(result, index, match.group(0), f"{source} → {target}")
            edge_mrp = "" if (is_dependency_summary or not in_body) else current_mrp_burden or (sorted(mrp_line_for.items(), key=lambda item: item[1])[-1][0] if mrp_line_for else "")
            record_dependency_edge(result, source, target, index, stripped, edge_mrp)

        if "->" in line and "Burden dependency graph" in line and ";" not in line:
            chain = [burden_token(match.group(1)) for match in ASCII_CHAIN_TOKEN_RE.finditer(line)]
            for source, target in zip(chain, chain[1:]):
                warn_legacy(result, index, f"{source}->{target}", f"{source} → {target}")
                record_dependency_edge(result, source, target, index, stripped)

    result.burdens = sorted(set(result.burdens), key=burden_sort_key)
    result.initial_burdens = sorted(set(result.initial_burdens), key=burden_sort_key)

    validate_result(result, lines, route_records)
    embedded_field_witness = extract_embedded_field_witness(text)
    if embedded_field_witness:
        compare_field_witness(result, embedded_field_witness, "embedded field_witness")
    if field_witness_text:
        compare_field_witness(result, field_witness_text, "separate field_witness")
    compare_embedded_and_separate_witness(result, embedded_field_witness, field_witness_text or "")
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
            later_lines = lines[line_no:]
            closure_index = next(
                (
                    index
                    for index, line in enumerate(later_lines)
                    if re.search(r"^\s*(?:#{1,6}\s*)?Closure/Reconstruction Witness\b", line, re.I)
                ),
                -1,
            )
            later = "\n".join(later_lines[:closure_index] if closure_index >= 0 else later_lines)
            if re.search(r"Layer B|^#+\s*Burden\s+\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\s+\[generated-by", later, re.M):
                result.errors.append(f"line {line_no}: Route: STOP is followed by later burden / Layer B work")
    text = "\n".join(lines)
    validate_held_route_closure(result, lines, text)
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


def split_mrp_source_blocks(lines: list[str]) -> list[str]:
    blocks: list[str] = []
    for index, line in enumerate(lines):
        if not re.match(r"^\s*\[Mid-Reread Pressure\]\s*$", line, re.IGNORECASE):
            continue
        end = len(lines)
        for cursor in range(index + 1, len(lines)):
            if re.match(
                r"^\s*(?:#{1,6}\s*)?(?:Burden\s+\d+|Restorative Response|Closing Formulation|Closure/Reconstruction Witness|field_witness)\b",
                lines[cursor],
                re.IGNORECASE,
            ):
                end = cursor
                break
        blocks.append("\n".join(lines[index + 1 : end]))
    return blocks


def validate_held_route_closure(result: ParseResult, lines: list[str], text: str) -> None:
    r_lines = [
        match.group(1)
        for match in re.finditer(r"(?im)^\s*(?:[-*]\s*)?R\(H,\s*(?:Δ|Delta)\)\s*:\s*(.+)$", text)
    ]
    closure_tail = ""
    for index, line in enumerate(lines):
        if re.match(r"^\s*(?:#{1,6}\s*)?Closure/Reconstruction Witness\b", line, re.IGNORECASE):
            closure_tail = "\n".join(lines[index:])
            break
    candidates = [item for item in [*r_lines, *split_mrp_source_blocks(lines), closure_tail] if item.strip()]
    if any(
        HIGH_LEVERAGE_HELD_ROUTE_RE.search(candidate)
        and UNROUTED_HELD_ROUTE_RE.search(candidate)
        and TERMINAL_CLOSURE_RE.search(candidate)
        and not ROUTING_OR_BOUNDARY_PROOF_RE.search(candidate)
        for candidate in candidates
    ):
        result.errors.append(
            "R(H,Δ) detected a pertinent high-leverage held route, but output claimed STOP/collapse without working, generating, HOLD/PARTIAL-routing, or proving non-load-bearing status"
        )


def witness_string_parts(value: Any) -> list[str]:
    parts: list[str] = []
    if value is None:
        return parts
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        for item in value:
            parts.extend(witness_string_parts(item))
        return parts
    if isinstance(value, dict):
        for key, item in value.items():
            parts.append(str(key))
            parts.extend(witness_string_parts(item))
    return parts


def validate_field_witness_held_route_closure(result: ParseResult, payload: dict[str, Any], label: str) -> None:
    body = field_witness_body(payload)
    coverage = body.get("coverage_proof") if isinstance(body.get("coverage_proof"), dict) else {}
    closure = body.get("closure") if isinstance(body.get("closure"), dict) else {}
    candidate = "\n".join(witness_string_parts(body))
    closure_status = str(closure.get("status") or closure.get("verdict") or "")
    claims_closure = (
        bool(TERMINAL_CLOSURE_RE.search(candidate))
        or body.get("coverage_complete") is True
        or coverage.get("coverage_complete") is True
        or bool(re.search(r"complete|collapse achieved|STOP", closure_status, re.IGNORECASE))
    )
    if (
        claims_closure
        and HIGH_LEVERAGE_HELD_ROUTE_RE.search(candidate)
        and UNROUTED_HELD_ROUTE_RE.search(candidate)
        and not ROUTING_OR_BOUNDARY_PROOF_RE.search(candidate)
    ):
        result.errors.append(
            f"{label}: unresolved high-leverage held route is still load-bearing, but closure is marked complete/collapse achieved"
        )


def parse_field_witness_payload(result: ParseResult, raw_json: str, label: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        result.errors.append(f"{label} JSON is invalid: {exc}")
        return None
    if not isinstance(payload, dict):
        result.errors.append(f"{label} JSON must be an object")
        return None
    return payload


def field_witness_body(payload: dict[str, Any]) -> dict[str, Any]:
    nested = payload.get("field_witness")
    return nested if isinstance(nested, dict) else payload


def field_witness_nodes(payload: dict[str, Any]) -> set[str]:
    body = field_witness_body(payload)
    raw_nodes = body.get("nodes")
    coverage = body.get("coverage_proof") if isinstance(body.get("coverage_proof"), dict) else {}
    graph = coverage.get("dependency_graph") if isinstance(coverage.get("dependency_graph"), dict) else {}
    graph_nodes = graph.get("nodes")
    if isinstance(graph_nodes, list):
        raw_nodes = graph_nodes
    if not isinstance(raw_nodes, list):
        return set()
    nodes: set[str] = set()
    for item in raw_nodes:
        if isinstance(item, str):
            token = normalize_burden_token(item)
            if re.fullmatch(fr"[{SUP_DIGITS}]+B", token):
                nodes.add(token)
        elif isinstance(item, dict):
            node_id = normalize_burden_token(str(item.get("id", "")))
            node_type = str(item.get("type", ""))
            if node_id and (node_type == "burden" or re.fullmatch(fr"[{SUP_DIGITS}]+B", node_id)):
                nodes.add(node_id)
    return nodes


def field_witness_edges(payload: dict[str, Any]) -> set[tuple[str, str]]:
    body = field_witness_body(payload)
    coverage = body.get("coverage_proof") if isinstance(body.get("coverage_proof"), dict) else {}
    graph = coverage.get("dependency_graph") if isinstance(coverage.get("dependency_graph"), dict) else {}
    raw_edges = graph.get("edges")
    if not isinstance(raw_edges, list):
        raw_edges = body.get("edges")
    if not isinstance(raw_edges, list):
        return set()
    witness_edges: set[tuple[str, str]] = set()
    for edge in raw_edges:
        if isinstance(edge, dict):
            source = edge.get("source", edge.get("from", ""))
            target = edge.get("target", edge.get("to", ""))
            source_token = normalize_burden_token(str(source))
            target_token = normalize_burden_token(str(target))
            if source_token and target_token:
                witness_edges.add((source_token, target_token))
        elif isinstance(edge, (list, tuple)) and len(edge) == 2:
            witness_edges.add((normalize_burden_token(str(edge[0])), normalize_burden_token(str(edge[1]))))
    return witness_edges


def normalize_witness_graph(value: str) -> str:
    raw = str(value or "").strip()
    if not raw or re.search(r"(?i)\b(?:none|no edge|no new graph edge|no-edge)\b", raw):
        return "none"
    match = ASCII_EDGE_RE.search(raw)
    if match:
        return f"{burden_token(match.group(1))}->{burden_token(match.group(2))}"
    match = CANONICAL_EDGE_RE.search(raw)
    if match:
        return f"{burden_token(_sup_to_int(match.group(1)))}->{burden_token(_sup_to_int(match.group(2)))}"
    return raw.replace(" → ", "->").replace("→", "->").replace(" ", "")


def first_state(value: Any) -> str:
    return re.split(r"\s*/\s*|;|,", str(value or "").strip(), maxsplit=1)[0].strip()


def field_witness_ledger(payload: dict[str, Any]) -> dict[str, list[str]]:
    body = field_witness_body(payload)
    source = body.get("ledger") if isinstance(body.get("ledger"), dict) else body
    ledger = {"B_LA": [], "B_MRP": [], "B_total": []}
    for key in ledger:
        value = source.get(key) if isinstance(source, dict) else None
        if isinstance(value, list):
            ledger[key] = [normalize_burden_token(str(item)) for item in value if isinstance(item, str)]
    generated = body.get("generated_burdens")
    if not ledger["B_MRP"]:
        if isinstance(generated, dict):
            ledger["B_MRP"] = [normalize_burden_token(str(item)) for item in generated.keys()]
        elif isinstance(generated, list):
            ledger["B_MRP"] = [normalize_burden_token(str(item)) for item in generated if isinstance(item, str)]
    return ledger


def field_witness_mrp_resultants(payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    body = field_witness_body(payload)
    raw = body.get("mrp_resultants")
    if not isinstance(raw, (list, dict)):
        raw = body.get("reread_pressure")
    if isinstance(raw, dict):
        raw = [
            {"source": source, **item} if isinstance(item, dict) else {"source": source, "type": str(item)}
            for source, item in raw.items()
        ]
    if not isinstance(raw, list):
        return {}
    resultants: dict[str, dict[str, str]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        source = item.get("source") or item.get("burden") or item.get("target") or item.get("id") or ""
        source_token = normalize_burden_token(str(source).replace("MRP(", "").replace(")", ""))
        if not source_token:
            continue
        graph_value = item.get("graph") if "graph" in item else None
        graph_delta = item.get("graph_delta")
        if isinstance(graph_value, dict):
            graph = (
                f"{normalize_burden_token(str(graph_value.get('source', graph_value.get('from', ''))))}->"
                f"{normalize_burden_token(str(graph_value.get('target', graph_value.get('to', ''))))}"
            )
        elif isinstance(graph_delta, dict):
            edges_added = graph_delta.get("edges_added")
            if isinstance(edges_added, list) and edges_added:
                edge = edges_added[0]
                if isinstance(edge, dict):
                    graph = (
                        f"{normalize_burden_token(str(edge.get('source', edge.get('from', ''))))}->"
                        f"{normalize_burden_token(str(edge.get('target', edge.get('to', ''))))}"
                    )
                elif isinstance(edge, (list, tuple)) and len(edge) == 2:
                    graph = f"{normalize_burden_token(str(edge[0]))}->{normalize_burden_token(str(edge[1]))}"
                else:
                    graph = str(graph_delta)
            else:
                graph = "none"
        elif graph_value is None:
            graph = "none"
        else:
            graph = normalize_witness_graph(str(graph_value))
        resultants[source_token] = {
            "type": str(item.get("type") or item.get("result_type") or item.get("resultant") or ""),
            "route": str(item.get("route") or item.get("next_route") or ""),
            "graph": graph,
        }
    return resultants


def field_witness_terminals(payload: dict[str, Any]) -> dict[str, str]:
    body = field_witness_body(payload)
    raw = body.get("terminal_states")
    if not isinstance(raw, (dict, list)):
        coverage = body.get("coverage_proof") if isinstance(body.get("coverage_proof"), dict) else {}
        raw = coverage.get("terminal_states")
    if not isinstance(raw, (dict, list)):
        burdens = body.get("burdens")
        if isinstance(burdens, dict):
            raw = {
                burden: value.get("terminal_state", value.get("terminal", value.get("state", "")))
                if isinstance(value, dict)
                else value
                for burden, value in burdens.items()
            }
    if not isinstance(raw, (dict, list)):
        return {}
    terminals: dict[str, str] = {}
    items: list[tuple[Any, Any]]
    if isinstance(raw, list):
        items = []
        for value in raw:
            if isinstance(value, dict):
                items.append((value.get("id") or value.get("notation") or value.get("burden") or "", value))
            else:
                items.append((value, value))
    else:
        items = list(raw.items())
    for burden, value in items:
        token = normalize_burden_token(str(burden))
        if isinstance(value, dict):
            state = str(value.get("state") or value.get("terminal") or "")
        else:
            state = str(value)
        if token and state:
            terminals[token] = state.lower()
    return terminals


def compare_formal_reread_states(
    result: ParseResult,
    body: dict[str, Any],
    visible_mrp: dict[str, dict[str, Any]],
    label: str,
) -> None:
    raw = body.get("formal_reread_states")
    if raw is None:
        return
    if not isinstance(raw, list):
        result.errors.append(f"{label}: field_witness.formal_reread_states must be a list")
        return

    seen: set[str] = set()
    if len(raw) != len(visible_mrp):
        result.errors.append(
            f"{label}: formal_reread_states count {len(raw)} does not match visible MRP count {len(visible_mrp)}"
        )
    for index, state in enumerate(raw, start=1):
        state_label = f"{label}: formal_reread_states[{index}]"
        if not isinstance(state, dict):
            result.errors.append(f"{state_label}: state must be an object")
            continue
        source = normalize_burden_token(str(state.get("source_burden") or state.get("source") or ""))
        if not source:
            result.errors.append(f"{state_label}: missing source_burden")
            continue
        if source in seen:
            result.errors.append(f"{state_label}: duplicate source_burden {source}")
        seen.add(source)
        visible = visible_mrp.get(source)
        if not visible:
            result.errors.append(f"{state_label}: source_burden {source} has no visible MRP block")
            continue

        visible_type = (visible.get("result_types") or [""])[-1]
        visible_route = (visible.get("routes") or [""])[-1]
        if state.get("route_result_type") and visible_type and state.get("route_result_type") != visible_type:
            result.errors.append(
                f"{state_label}: route_result_type mismatch visible={visible_type!r} field_witness={state.get('route_result_type')!r}"
            )
        if state.get("route") and visible_route and str(state.get("route")).upper() != visible_route.upper():
            result.errors.append(
                f"{state_label}: route mismatch visible={visible_route!r} field_witness={state.get('route')!r}"
            )

        visible_graphs = {f"{source_id}->{target_id}" for source_id, target_id in visible.get("edges", [])}
        state_graph = normalize_witness_graph(str(state.get("graph_delta") or state.get("graph") or ""))
        if visible_graphs and state_graph not in visible_graphs:
            result.errors.append(
                f"{state_label}: graph_delta mismatch visible={sorted(visible_graphs)} field_witness={state_graph!r}"
            )
        elif not visible_graphs and state_graph and state_graph != "none":
            result.errors.append(f"{state_label}: graph_delta must be none when visible MRP has no graph edge")

        visible_divergence = first_state(visible.get("divergence"))
        visible_curl = first_state(visible.get("curl"))
        state_divergence = first_state(state.get("divergence_state"))
        state_curl = first_state(state.get("curl_state"))
        if visible_divergence and state_divergence and visible_divergence != state_divergence:
            result.errors.append(
                f"{state_label}: divergence_state mismatch visible={visible_divergence!r} field_witness={state_divergence!r}"
            )
        if visible_curl and state_curl and visible_curl != state_curl:
            result.errors.append(
                f"{state_label}: curl_state mismatch visible={visible_curl!r} field_witness={state_curl!r}"
            )

    for burden in sorted(set(visible_mrp) - seen, key=burden_sort_key):
        result.errors.append(f"{label}: formal_reread_states missing visible MRP source {burden}")
    for burden in sorted(seen - set(visible_mrp), key=burden_sort_key):
        result.errors.append(f"{label}: formal_reread_states names non-visible MRP source {burden}")


def compare_field_witness(result: ParseResult, raw_json: str, label: str = "field_witness") -> None:
    payload = parse_field_witness_payload(result, raw_json, label)
    if payload is None:
        return
    validate_field_witness_held_route_closure(result, payload, label)
    witness_nodes = field_witness_nodes(payload)
    visible_burdens = set(result.body_burdens or result.burdens)
    if visible_burdens and not witness_nodes:
        result.errors.append(f"{label}: graphable output has visible burdens but field_witness omits graph nodes")
    elif witness_nodes and witness_nodes != visible_burdens:
        result.errors.append(
            f"{label}: node mismatch visible={sorted(visible_burdens, key=burden_sort_key)} field_witness={sorted(witness_nodes, key=burden_sort_key)}"
        )
    witness_edges = field_witness_edges(payload)
    visible_edges = {(source, target) for source, target, _line, _excerpt in result.graph_edges}
    if visible_edges and not witness_edges:
        result.errors.append(f"{label}: graphable output has visible dependency edges but field_witness omits graph edges")
    elif witness_edges and witness_edges != visible_edges:
        result.errors.append(
            f"{label}: edge mismatch visible={sorted(visible_edges)} field_witness={sorted(witness_edges)}"
        )
    ledger = field_witness_ledger(payload)
    visible_la = result.ledger.get("B_LA") or result.initial_burdens
    visible_mrp = result.ledger.get("B_MRP") or sorted(result.generated_burdens, key=burden_sort_key)
    visible_total = result.ledger.get("B_total") or result.burdens
    if ledger["B_MRP"]:
        for generated in ledger["B_MRP"]:
            if generated in ledger["B_LA"]:
                result.errors.append(f"{label}: field_witness marks baseline burden {generated} as generated")
    if result.generated_burdens and not ledger["B_MRP"]:
        result.errors.append(f"{label}: visible generated B_MRP appears in prose but field_witness omits B_MRP")
    if ledger["B_LA"] and visible_la and set(ledger["B_LA"]) != set(visible_la):
        result.errors.append(f"{label}: B_LA mismatch visible={visible_la} field_witness={ledger['B_LA']}")
    if ledger["B_MRP"] and visible_mrp and set(ledger["B_MRP"]) != set(visible_mrp):
        result.errors.append(f"{label}: B_MRP mismatch visible={visible_mrp} field_witness={ledger['B_MRP']}")
    if ledger["B_total"] and visible_total and set(ledger["B_total"]) != set(visible_total):
        result.errors.append(f"{label}: B_total mismatch visible={visible_total} field_witness={ledger['B_total']}")
    witness_mrp = field_witness_mrp_resultants(payload)
    visible_mrp = {
        burden: data
        for burden, data in result.mrp.items()
        if data.get("result_types") or data.get("routes") or data.get("edges")
    }
    if visible_mrp and not witness_mrp:
        result.errors.append(f"{label}: visible MRP resultants appear in prose but field_witness omits mrp_resultants")
    for burden, data in visible_mrp.items():
        witness = witness_mrp.get(burden)
        if not witness:
            result.errors.append(f"{label}: missing MRP resultant for visible MRP({burden})")
            continue
        visible_type = (data.get("result_types") or [""])[-1]
        visible_route = (data.get("routes") or [""])[-1]
        if visible_type and witness.get("type") and visible_type != witness["type"]:
            result.errors.append(
                f"{label}: MRP({burden}) type mismatch visible={visible_type!r} field_witness={witness['type']!r}"
            )
        if visible_route and witness.get("route") and visible_route.upper() != witness["route"].upper():
            result.errors.append(
                f"{label}: MRP({burden}) route mismatch visible={visible_route!r} field_witness={witness['route']!r}"
            )
        visible_graphs = {f"{source}->{target}" for source, target in data.get("edges", [])}
        witness_graph = witness.get("graph", "")
        if visible_graphs and (not witness_graph or witness_graph == "none"):
            result.errors.append(f"{label}: MRP({burden}) visible graph edge omitted from field_witness MRP resultant")
        elif visible_graphs and witness_graph and witness_graph != "none" and witness_graph not in visible_graphs:
            result.errors.append(
                f"{label}: MRP({burden}) graph mismatch visible={sorted(visible_graphs)} field_witness={witness_graph!r}"
            )
    compare_formal_reread_states(result, field_witness_body(payload), visible_mrp, label)
    witness_terminals = field_witness_terminals(payload)
    if result.terminals and not witness_terminals:
        result.errors.append(f"{label}: visible terminal states appear in prose but field_witness omits terminal_states")
    for burden, visible_state in result.terminals.items():
        witness_state = witness_terminals.get(burden, "")
        if not witness_state:
            result.errors.append(f"{label}: missing terminal state for visible {burden}")
            continue
        if visible_state == "Land" and not re.search(r"landed|cleared|discharged|held-with-reason", witness_state):
            result.errors.append(
                f"{label}: terminal mismatch for {burden}: visible Land but field_witness state={witness_state!r}"
            )
        if visible_state == "HOLD" and not re.search(r"hold|held|partial|carried", witness_state):
            result.errors.append(
                f"{label}: terminal mismatch for {burden}: visible HOLD but field_witness state={witness_state!r}"
            )


def compare_embedded_and_separate_witness(result: ParseResult, embedded: str, separate: str) -> None:
    if not embedded.strip() or not separate.strip():
        return
    try:
        embedded_payload = json.loads(embedded)
        separate_payload = json.loads(separate)
    except json.JSONDecodeError:
        return
    if canonical_json(embedded_payload) != canonical_json(separate_payload):
        result.errors.append("embedded field_witness and separate field_witness disagree")


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


def certificate_html(collapse_certificate: dict[str, Any] | None) -> str:
    if not collapse_certificate:
        return ""
    fields = [
        ("collapse_positive", collapse_certificate.get("collapse_positive")),
        ("coverage_complete", collapse_certificate.get("coverage_complete")),
        ("diagnostic_completeness", collapse_certificate.get("diagnostic_completeness")),
        ("divergence_state", collapse_certificate.get("divergence_state")),
        ("curl_state", collapse_certificate.get("curl_state")),
        ("max_generation_depth", collapse_certificate.get("max_generation_depth")),
        ("restoration_endpoint_reached", collapse_certificate.get("restoration_endpoint_reached")),
        ("input_fingerprint", collapse_certificate.get("input_fingerprint")),
        ("verified_activations", ", ".join(str(item) for item in collapse_certificate.get("verified_activations", []))),
        ("checker_version", collapse_certificate.get("checker_version")),
    ]
    rows = "\n".join(
        f"<tr><td>{html.escape(label)}</td><td>{html.escape(str(value))}</td></tr>"
        for label, value in fields
        if value not in (None, "")
    )
    return (
        "<section class=\"certificate-panel\">"
        "<h2>Collapse Certificate</h2>"
        "<p>Certificate-backed mode cross-checks this B.2 certificate against the output and raw input; graph reconstruction alone is not treated as proof.</p>"
        f"<table><tbody>{rows}</tbody></table>"
        "</section>"
    )


def certificate_svg_badge(collapse_certificate: dict[str, Any] | None, width: int) -> str:
    if not collapse_certificate:
        return ""
    status = "positive" if collapse_certificate.get("collapse_positive") is True else "not positive"
    coverage = "coverage=true" if collapse_certificate.get("coverage_complete") is True else "coverage=false"
    divergence = str(collapse_certificate.get("divergence_state") or "unknown")
    curl = str(collapse_certificate.get("curl_state") or "unknown")
    fingerprint = str(collapse_certificate.get("input_fingerprint") or "")
    short_fingerprint = fingerprint[:12] if fingerprint else "unbound"
    x = max(760, width - 570)
    return (
        '<g id="collapse-certificate-badge">'
        f'<rect x="{x}" y="20" width="535" height="58" rx="10" fill="#0f172a" stroke="#22c55e" stroke-width="1.4"/>'
        f'<text x="{x + 14}" y="43" fill="#dcfce7" font-size="14" font-weight="700">Collapse Certificate: {html.escape(status)} / {html.escape(coverage)}</text>'
        f'<text x="{x + 14}" y="65" fill="#bae6fd" font-size="11">∇·B={html.escape(divergence)}; ∇×κ={html.escape(curl)}; input={html.escape(short_fingerprint)}</text>'
        "</g>"
    )


def graph_html(
    result: ParseResult,
    title: str = "Output Collapse Grapher Result",
    collapse_certificate: dict[str, Any] | None = None,
) -> str:
    nodes = list(result.nodes.values())
    positions: dict[str, tuple[int, int]] = {}
    width = 1390
    node_width = 170
    row_height = 72
    lane_gap = 46
    y_start = 116 if collapse_certificate else 40
    positions["input"] = (30, y_start)
    y = y_start
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
    certificate_panel = certificate_html(collapse_certificate)
    certificate_badge = certificate_svg_badge(collapse_certificate, width)
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body{{font-family:system-ui,Segoe UI,sans-serif;background:#0b1020;color:#e5e7eb;margin:24px}}
svg{{max-width:100%;background:#050914;border:1px solid #334155;border-radius:12px}}
table{{width:100%;border-collapse:collapse;margin:14px 0}}td,th{{border:1px solid #334155;padding:6px;vertical-align:top}}th{{background:#111827}}
.error{{color:#fecaca}}.warn{{color:#fde68a}}.summary{{display:flex;gap:10px;flex-wrap:wrap}}.pill{{border:1px solid #334155;border-radius:999px;padding:6px 10px;background:#111827}}.certificate-panel{{border:1px solid #166534;background:#07130c;border-radius:12px;padding:14px;margin:14px 0}}.certificate-panel h2{{margin-top:0;color:#bbf7d0}}
</style>
<h1>{html.escape(title)}</h1>
<div class="summary"><span class="pill">Verdict: {verdict}</span><span class="pill">Burdens: {len(result.burdens)}</span><span class="pill">Submoves: {sum(len(v) for v in result.submoves.values())}</span><span class="pill">MRP: {len(result.mrp)}</span></div>
{certificate_panel}
<svg viewBox="0 0 {width} {height}" role="img" aria-label="Output collapse graph">
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>
{certificate_badge}
{''.join(edge_lines)}
{''.join(node_lines)}
</svg>
<h2>Validation</h2><ul>{validation_rows}</ul><h2>Warnings</h2><ul>{warning_rows}</ul>
<h2>Nodes</h2><table><thead><tr><th>Node</th><th>Type</th><th>Owner/TTP</th><th>Status/route</th><th>Source excerpt</th></tr></thead><tbody>{node_rows}</tbody></table>
<h2>Edges</h2><table><thead><tr><th>Source</th><th>Target</th><th>Type</th><th>Source excerpt</th></tr></thead><tbody>{edge_rows}</tbody></table>
</html>"""
