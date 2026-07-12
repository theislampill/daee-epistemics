#!/usr/bin/env python3
"""Parse Closure/Reconstruction Witness blocks and field_witness sidecars.

This module is intentionally dependency-free and structural. It makes rendered
coverage auditable; it does not grade live noetic competence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUPERSCRIPT_DIGITS = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
}
BURDEN_ID_RE = re.compile(r"(?:\bB\d+\b|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\b)")
HEADING_RE = re.compile(r"(?im)^\s*(?:#{2,5}\s*)?Closure/Reconstruction Witness\b")
NEXT_HEADING_RE = re.compile(
    r"(?m)^\s*(?:#{2,5}\s+\S|Restorative Response\b|Closing Formulation\b|field_witness\b)"
)
KNOWN_FIELD_RE = re.compile(
    "(?i)^\s*(?:[-*]\s*)?(?:"
    "N frames|Registers|Burden dependency graph|\u2207\u00b7B|\u2207\u00b7T|\u2207\u00d7\u03ba|\u2207\u00d7T|"
    "del[- ]dot\s*B|del[- ]dot\s*T|del[- ]cross\s*kappa|del[- ]cross\s*T|"
    "\U0001d49e\(\u03a8\u1d3a\)|C\(PsiN\)|T_lang"
    ")\s*:"
)
REGISTERS_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Registers\s*:\s*(?P<body>\S.*)$")
INITIAL_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Initial burden set\s*:\s*\[(?P<body>[^\]]*)\]")
LEDGER_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:𝔅_(?:LA|MRP|total)\s*\(\s*)?"
    r"(?P<key>B_LA|B_MRP|B_total)\s*\)?\s*(?:=|:)\s*(?P<body>.*)$"
)
TERMINAL_HEADER_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Terminal states\s*:\s*$")
TERMINAL_INLINE_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Terminal states\s*:\s*(?P<body>\S.*)$")
TERMINAL_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<burden>B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\s*:\s*"
    r"(?P<state>[A-Za-z-]+)\b(?:\s*/\s*(?P<detail>.*))?$"
)
GRAPH_HEADER_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Burden dependency graph\s*:\s*(?P<body>.*)$")
DIVERGENCE_RE = re.compile("(?im)^\s*(?:[-*]\s*)?(?:\u2207\u00b7B|\u2207\u00b7T|del[- ]dot\s*B|del[- ]dot\s*T)\s*:\s*(?P<body>\S.*)$")
CURL_RE = re.compile("(?im)^\s*(?:[-*]\s*)?(?:\u2207\u00d7\u03ba|\u2207\u00d7T|del[- ]cross\s*kappa|del[- ]cross\s*T)\s*:\s*(?P<body>\S.*)$")
CLOSURE_RE = re.compile("(?im)^\s*(?:[-*]\s*)?`?(?:\U0001d49e\(\u03a8\u1d3a\)|C\(PsiN\))`?\s*:\s*(?P<body>\S.*)$")
TRANSFER_RE = re.compile(
    "(?im)^\s*(?:[-*]\s*)?`?T_lang\s*:\s*(?:\u03a8\u1d3a|PsiN)\s*(?:\u21e2|->)\s*"
    "(?:\u03a8\u1d35|PsiI)`?(?:\s+(?:coupling|boundary|coupling boundary))?\s*:\s*(?P<body>\S.*)$"
)
MRP_RESULTANT_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?MRP\((?P<source>B\d+|[^\s\)]+B)\)\s*:\s*"
    r"(?P<body>.+)$"
)

ARROW_RE = re.compile("\s*(?:\u2192|->)\s*")
PARALLEL_RE = re.compile("\s*(?:\u2225|\|\|)\s*")
ROOT_RE = re.compile(r"(?P<node>B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\s*\(root\)")


ALLOWED_TERMINAL_STATES = {
    "landed",
    "discharged-as-derivative",
    "held-with-reason",
    "carried-PARTIAL",
    "carried-RECURSE",
    "cleared",
}


@dataclass
class ClosureWitness:
    block: str
    initial_burdens: list[str]
    ledger_la: list[str]
    ledger_mrp: list[str]
    ledger_total: list[str]
    registers: str
    terminal_states: dict[str, dict[str, str]]
    duplicate_terminal_states: list[str]
    graph_text: str
    edges: list[tuple[str, str]]
    roots: list[str]
    parallel: list[tuple[str, str]]
    parallel_groups: list[list[str]]
    mrp_resultants: list[dict[str, str]]
    divergence: str
    curl: str
    closure: str
    transfer: str

    @property
    def missing_terminal_states(self) -> list[str]:
        return [burden for burden in self.initial_burdens if burden not in self.terminal_states]

    @property
    def coverage_complete(self) -> bool:
        return bool(self.initial_burdens) and not self.missing_terminal_states and not self.duplicate_terminal_states

    @property
    def divergence_neutral(self) -> bool:
        first = status_head(self.divergence)
        return first == "neutral"

    @property
    def curl_null_or_resolved(self) -> bool:
        first = status_head(self.curl)
        return first in {"null", "resolved"}

    @property
    def collapse_positive(self) -> bool:
        return self.coverage_complete and self.divergence_neutral and self.curl_null_or_resolved

    @property
    def closure_claims_positive(self) -> bool:
        return bool(re.search(r"(?i)\b(?:positive|complete|completed|closed|stop|collapse)\b", self.closure))

    @property
    def graph_nodes(self) -> list[str]:
        return graph_nodes(self.edges, self.roots, self.parallel_groups)


def status_head(value: str) -> str:
    return re.split(r"\s*/\s*|;|,", value.strip().lower(), maxsplit=1)[0].strip()


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def normalize_burden_id(value: str) -> str:
    """Normalize public burden notation (`¹B`) to machine graph notation (`B1`)."""
    value = value.strip()
    if re.fullmatch(r"B\d+", value):
        return value
    if re.fullmatch(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+B", value):
        digits = "".join(SUPERSCRIPT_DIGITS[ch] for ch in value[:-1])
        return f"B{digits}"
    return value


def burden_ids(value: str) -> list[str]:
    return [normalize_burden_id(match.group(0)) for match in BURDEN_ID_RE.finditer(value)]


def clean_visible_ledger_body(body: str) -> str:
    """Remove provenance source aliases from visible ledger membership lines."""

    cleaned = re.sub(r"\[generated-by:\s*MRP\([^\)]*\)\]", "", str(body), flags=re.IGNORECASE)
    cleaned = re.sub(r"\bMRP\([^\)]*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:B_|𝔅_)(?:LA|MRP|total)\b", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def extract_closure_witness_block(text: str) -> str | None:
    match = HEADING_RE.search(text)
    if not match:
        return None
    start = match.end()
    next_heading = NEXT_HEADING_RE.search(text, start)
    end = next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def parse_burden_list(body: str) -> list[str]:
    return burden_ids(body)


def parse_visible_ledgers(block: str) -> dict[str, list[str]]:
    ledgers = {"B_LA": [], "B_MRP": [], "B_total": []}
    for match in LEDGER_RE.finditer(block):
        key = match.group("key")
        ledgers[key] = unique(parse_burden_list(clean_visible_ledger_body(match.group("body"))))
    if not ledgers["B_total"] and (ledgers["B_LA"] or ledgers["B_MRP"]):
        ledgers["B_total"] = unique(ledgers["B_LA"] + ledgers["B_MRP"])
    return ledgers


def parse_terminal_states(block: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    lines = block.splitlines()
    states: dict[str, dict[str, str]] = {}
    duplicates: list[str] = []
    in_terminal = False
    for line in lines:
        inline_match = TERMINAL_INLINE_RE.match(line)
        if inline_match:
            inline_state = TERMINAL_LINE_RE.match(inline_match.group("body"))
            if inline_state:
                burden = normalize_burden_id(inline_state.group("burden"))
                if burden in states and burden not in duplicates:
                    duplicates.append(burden)
                states[burden] = {
                    "state": inline_state.group("state"),
                    "detail": (inline_state.group("detail") or "").strip(),
                }
            continue
        if TERMINAL_HEADER_RE.match(line):
            in_terminal = True
            continue
        if in_terminal and KNOWN_FIELD_RE.match(line):
            break
        if not in_terminal:
            continue
        if not line.strip():
            continue
        match = TERMINAL_LINE_RE.match(line)
        if not match:
            continue
        burden = normalize_burden_id(match.group("burden"))
        if burden in states and burden not in duplicates:
            duplicates.append(burden)
        states[burden] = {
            "state": match.group("state"),
            "detail": (match.group("detail") or "").strip(),
        }
    return states, duplicates


def _strip_list_prefix(line: str) -> str:
    return re.sub(r"^\s*(?:[-*]\s*)?", "", line).strip()


def extract_graph_text(block: str) -> str:
    lines = block.splitlines()
    for index, line in enumerate(lines):
        match = GRAPH_HEADER_RE.match(line)
        if not match:
            continue
        chunks: list[str] = []
        body = match.group("body").strip()
        if body:
            chunks.append(body)
        for next_line in lines[index + 1 :]:
            if KNOWN_FIELD_RE.match(next_line):
                break
            if re.match(r"^\s*#{1,6}\s+\S", next_line):
                break
            stripped = _strip_list_prefix(next_line)
            if not stripped:
                continue
            if "B" not in stripped:
                break
            chunks.append(stripped)
        return "\n".join(chunks).strip()
    return ""


def parse_graph(graph_text: str) -> tuple[list[tuple[str, str]], list[str], list[tuple[str, str]], list[list[str]]]:
    edges: list[tuple[str, str]] = []
    roots: list[str] = []
    parallel_pairs: list[tuple[str, str]] = []
    parallel_groups: list[list[str]] = []
    for segment in re.split(r"[;\n]+", graph_text):
        segment = _strip_list_prefix(segment)
        if not segment:
            continue
        roots.extend(normalize_burden_id(node) for node in ROOT_RE.findall(segment))
        for piece in ARROW_RE.split(segment):
            if not PARALLEL_RE.search(piece):
                continue
            group = unique(burden_ids(piece))
            if len(group) >= 2 and group not in parallel_groups:
                parallel_groups.append(group)
                for left_index, left in enumerate(group):
                    for right in group[left_index + 1 :]:
                        pair = (left, right)
                        if pair not in parallel_pairs:
                            parallel_pairs.append(pair)
        chain = ARROW_RE.split(segment)
        if len(chain) < 2:
            continue
        for left, right in zip(chain, chain[1:]):
            sources = unique(burden_ids(left))
            targets = unique(burden_ids(right))
            for source in sources:
                for target in targets:
                    edge = (source, target)
                    if source != target and edge not in edges:
                        edges.append(edge)
    return edges, unique(roots), parallel_pairs, parallel_groups


def parse_key_value_body(body: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for chunk in body.split(";"):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        values[key.strip().lower()] = value.strip()
    return values


def normalize_graph_value(value: str) -> str:
    value = value.strip()
    if not value or value.lower() == "none":
        return "none"
    edges, roots, _parallel, groups = parse_graph(value)
    parts = [f"{source}->{target}" for source, target in edges]
    parts.extend(f"root:{root}" for root in roots)
    parts.extend("||".join(group) for group in groups)
    return ";".join(parts) if parts else value


def parse_mrp_resultants(block: str) -> list[dict[str, str]]:
    resultants: list[dict[str, str]] = []
    for match in MRP_RESULTANT_LINE_RE.finditer(block):
        body = parse_key_value_body(match.group("body"))
        resultants.append(
            {
                "source": normalize_burden_id(match.group("source")),
                "type": body.get("type", ""),
                "finding": body.get("finding", ""),
                "graph": normalize_graph_value(body.get("graph", "")),
                "route": body.get("route", ""),
            }
        )
    return resultants


def graph_nodes(edges: list[tuple[str, str]], roots: list[str], parallel_groups: list[list[str]]) -> list[str]:
    values = list(roots)
    for source, target in edges:
        values.extend([source, target])
    for group in parallel_groups:
        values.extend(group)
    return unique(values)


def has_cycle(nodes: list[str], edges: list[tuple[str, str]]) -> bool:
    graph = {node: [] for node in nodes}
    for source, target in edges:
        graph.setdefault(source, []).append(target)
        graph.setdefault(target, [])
    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(node: str) -> bool:
        if node in permanent:
            return False
        if node in temporary:
            return True
        temporary.add(node)
        for target in graph.get(node, []):
            if visit(target):
                return True
        temporary.remove(node)
        permanent.add(node)
        return False

    return any(visit(node) for node in list(graph))


def graph_validation_errors(
    *,
    initial_burdens: list[str],
    terminal_states: dict[str, dict[str, str]],
    graph_text: str,
    edges: list[tuple[str, str]],
    roots: list[str],
    parallel_groups: list[list[str]],
) -> list[str]:
    errors: list[str] = []
    nodes = graph_nodes(edges, roots, parallel_groups)
    terminal_ids = set(terminal_states)
    initial_ids = set(initial_burdens)
    graph_ids = set(nodes)

    if graph_text and not nodes:
        errors.append("Burden dependency graph contains no parseable burden nodes")
    for node in nodes:
        if node not in terminal_ids:
            errors.append(f"Burden dependency graph node {node} lacks terminal state")
    for burden in sorted(initial_ids | terminal_ids):
        terminal_payload = terminal_states.get(burden, {})
        detail = terminal_payload.get("detail", "") if isinstance(terminal_payload, dict) else ""
        if burden not in graph_ids and "non-graph" not in detail.lower():
            errors.append(f"Burden dependency graph missing burden {burden}")
    for source, target in edges:
        if source not in graph_ids:
            errors.append(f"Burden dependency graph edge source {source} is not declared")
        if target not in graph_ids:
            errors.append(f"Burden dependency graph edge target {target} is not declared")
    indegree = {node: 0 for node in nodes}
    for _source, target in edges:
        indegree[target] = indegree.get(target, 0) + 1
    for root in roots:
        if indegree.get(root, 0) != 0:
            errors.append(f"Burden dependency graph root {root} has an upstream dependency")
    for node, degree in indegree.items():
        if degree == 0 and node not in roots:
            errors.append(f"Burden dependency graph node {node} has no upstream dependency but is not marked (root)")
    if has_cycle(nodes, edges):
        errors.append("Burden dependency graph contains a cycle")
    return errors


def parse_closure_witness(text: str) -> ClosureWitness | None:
    block = extract_closure_witness_block(text)
    if block is None:
        return None
    initial_match = INITIAL_RE.search(block)
    initial = parse_burden_list(initial_match.group("body")) if initial_match else []
    ledgers = parse_visible_ledgers(block)
    terminal_states, duplicates = parse_terminal_states(block)
    graph_text = extract_graph_text(block)
    edges, roots, parallel, parallel_groups = parse_graph(graph_text)
    mrp_resultants = parse_mrp_resultants(block)
    registers_match = REGISTERS_RE.search(block)
    divergence_match = DIVERGENCE_RE.search(block)
    curl_match = CURL_RE.search(block)
    closure_match = CLOSURE_RE.search(block)
    transfer_match = TRANSFER_RE.search(block)
    return ClosureWitness(
        block=block,
        initial_burdens=initial,
        ledger_la=ledgers["B_LA"],
        ledger_mrp=ledgers["B_MRP"],
        ledger_total=ledgers["B_total"],
        registers=registers_match.group("body").strip() if registers_match else "",
        terminal_states=terminal_states,
        duplicate_terminal_states=duplicates,
        graph_text=graph_text,
        edges=edges,
        roots=roots,
        parallel=parallel,
        parallel_groups=parallel_groups,
        mrp_resultants=mrp_resultants,
        divergence=divergence_match.group("body").strip() if divergence_match else "",
        curl=curl_match.group("body").strip() if curl_match else "",
        closure=closure_match.group("body").strip() if closure_match else "",
        transfer=transfer_match.group("body").strip() if transfer_match else "",
    )


def closure_witness_errors(witness: ClosureWitness | None) -> list[str]:
    if witness is None:
        return ["missing Closure/Reconstruction Witness block"]
    errors: list[str] = []
    if not witness.initial_burdens:
        errors.append("Closure/Reconstruction Witness missing Initial burden set")
    if len(set(witness.initial_burdens)) != len(witness.initial_burdens):
        errors.append("Initial burden set contains duplicate burden IDs")
    if not witness.terminal_states:
        errors.append("Closure/Reconstruction Witness missing Terminal states")
    for burden in witness.missing_terminal_states:
        errors.append(f"Terminal states missing initial burden {burden}")
    for burden in witness.duplicate_terminal_states:
        errors.append(f"Terminal states contains duplicate burden {burden}")
    for burden, payload in witness.terminal_states.items():
        state = payload.get("state", "")
        if state not in ALLOWED_TERMINAL_STATES:
            errors.append(f"Terminal state for {burden} uses unsupported state {state!r}")
        if not payload.get("detail"):
            errors.append(f"Terminal state for {burden} lacks operator/reason/detail")
    if not witness.graph_text:
        errors.append("Closure/Reconstruction Witness missing Burden dependency graph")
    else:
        errors.extend(
            graph_validation_errors(
                initial_burdens=witness.initial_burdens,
                terminal_states=witness.terminal_states,
                graph_text=witness.graph_text,
                edges=witness.edges,
                roots=witness.roots,
                parallel_groups=witness.parallel_groups,
            )
        )
    if not witness.divergence:
        errors.append("Closure/Reconstruction Witness missing ∇·B status")
    elif not (witness.divergence_neutral or re.search(r"(?i)\bnon-neutral\b.+\S", witness.divergence)):
        errors.append("∇·B status must be neutral or non-neutral with target-explicit status")
    if not witness.curl:
        errors.append("Closure/Reconstruction Witness missing ∇×κ status")
    elif not (
        witness.curl_null_or_resolved
        or re.search(r"(?i)\bnon-null\b.+\S", witness.curl)
        or re.search(r"(?i)\bunresolved\b.+\S", witness.curl)
    ):
        errors.append("∇×κ status must be null, resolved, or non-null/unresolved with target-explicit status")
    if not witness.closure:
        errors.append("Closure/Reconstruction Witness missing 𝒞(Ψᴺ) status")
    if witness.closure_claims_positive and not witness.collapse_positive:
        errors.append(
            "positive/complete 𝒞(Ψᴺ) claim requires coverage_complete and neutral ∇·B plus null/resolved ∇×κ"
        )
    if not witness.transfer:
        errors.append("Closure/Reconstruction Witness missing T_lang boundary")
    elif not re.search(r"(?i)\b(?:partial|attempt|coupling|boundary|language-mediated)\b", witness.transfer):
        errors.append("T_lang boundary must remain partial coupling / public-boundary language")
    if witness.transfer and re.search(r"(?i)\b(?:guarantees|ensures|proves|achieves)\b.{0,50}\b(?:uptake|acceptance|conversion)\b", witness.transfer):
        errors.append("T_lang boundary must not claim uptake, acceptance, or conversion")
    return errors


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def extract_balanced_json_extent(text: str, start_index: int) -> tuple[int, int, str] | None:
    """Return the exact complete JSON extent beginning after ``start_index``."""
    source = str(text or "")
    opener_match = re.search(r"[\{\[]", source[start_index:])
    if not opener_match:
        return None
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
                return json_start, index + 1, source[json_start : index + 1]
    return None


TERMINAL_SECTION_PATTERNS = {
    "restorative": re.compile(r"(?im)^\s*(?:#{1,6}\s*)?Restorative Response\s*$"),
    "closing": re.compile(r"(?im)^\s*(?:#{1,6}\s*)?Closing Formulation\s*$"),
    "closure_witness": re.compile(r"(?im)^\s*(?:#{1,6}\s*)?Closure/Reconstruction Witness\s*$"),
    "field_witness": re.compile(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\s*$"),
}


def _terminal_diagnostic(subcode: str, message: str) -> dict[str, Any]:
    return {
        "failure_class": "witness-order",
        "failure_subcode": subcode,
        "earliest_stage": "07",
        "downstream_invalidated": ["08"],
        "message": message,
    }


def terminal_public_order_diagnostics(text: str) -> list[dict[str, Any]]:
    """Validate the complete inline public tail and final JSON extent.

    Closing Formulation is the final human formulation before the proof tail; it
    is deliberately not treated as literal EOF.
    """
    source = str(text or "")
    matches = {name: list(pattern.finditer(source)) for name, pattern in TERMINAL_SECTION_PATTERNS.items()}
    labels = {
        "restorative": "Restorative Response",
        "closing": "Closing Formulation",
        "closure_witness": "Closure/Reconstruction Witness",
        "field_witness": "field_witness",
    }
    for name in ("restorative", "closing", "closure_witness", "field_witness"):
        if not matches[name]:
            return [_terminal_diagnostic("terminal-order-missing-section", f"missing terminal section {labels[name]}")]
        if len(matches[name]) != 1:
            return [_terminal_diagnostic("terminal-order-duplicate-section", f"duplicate terminal section {labels[name]}")]
    restorative = matches["restorative"][0]
    closing = matches["closing"][0]
    closure = matches["closure_witness"][0]
    field = matches["field_witness"][0]
    if restorative.start() > closing.start():
        return [_terminal_diagnostic("terminal-order-restorative-after-closing", "Restorative Response must precede Closing Formulation")]
    if closure.start() < closing.start():
        return [_terminal_diagnostic("terminal-order-closure-before-closing", "Closure/Reconstruction Witness must follow Closing Formulation")]
    if field.start() < closure.start():
        return [_terminal_diagnostic("terminal-order-field-before-closure", "field_witness must follow Closure/Reconstruction Witness")]
    extent = extract_balanced_json_extent(source, field.end())
    if extent is None:
        return [_terminal_diagnostic("terminal-order-invalid-field-json", "incomplete or missing field_witness JSON")]
    _, json_end, raw_json = extent
    try:
        decoded = json.loads(raw_json)
    except json.JSONDecodeError:
        return [_terminal_diagnostic("terminal-order-invalid-field-json", "incomplete or invalid field_witness JSON")]
    if not isinstance(decoded, dict):
        return [_terminal_diagnostic("terminal-order-invalid-field-json", "field_witness JSON must be one object")]
    trailing = source[json_end:]
    cleaned = re.sub(r"^\s*```\s*", "", trailing, count=1)
    if cleaned.strip():
        if re.match(r"^\s*[\{\[]", cleaned):
            return [_terminal_diagnostic("terminal-order-duplicate-field-json", "duplicate field_witness JSON after the final object")]
        return [_terminal_diagnostic("terminal-order-content-after-inline-field", "trailing content is forbidden after final JSON")]
    return []


def _directed_cycle(nodes: set[str], edges: list[tuple[str, str]]) -> bool:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for source, target in edges:
        adjacency.setdefault(source, []).append(target)
        adjacency.setdefault(target, [])
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in adjacency.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in adjacency)


def public_graph_integrity_diagnostics(field_witness: Any, *, compatibility: str = "current") -> list[dict[str, Any]]:
    """Enforce current graph identity and distinguish event DAG from noetic graph."""
    if not isinstance(field_witness, dict):
        return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-not-object", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "public graph must be an object"}]
    b_la = field_witness.get("B_LA", [])
    b_mrp = field_witness.get("B_MRP", [])
    b_total = field_witness.get("B_total", [])
    if isinstance(b_la, list) and isinstance(b_mrp, list) and set(b_la).intersection(b_mrp):
        return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-burden-identity", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "B_LA and B_MRP must be disjoint"}]
    if isinstance(b_la, list) and isinstance(b_mrp, list) and isinstance(b_total, list) and b_total != list(dict.fromkeys(b_la + b_mrp)):
        return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-burden-identity", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "B_total must equal B_LA plus B_MRP in order"}]
    coverage = field_witness.get("coverage_proof", {})
    if compatibility == "current":
        burden_ids = {str(burden) for burden in b_total} if isinstance(b_total, list) else set()
        root_terminals = field_witness.get("terminal_states")
        coverage_terminals = coverage.get("terminal_states") if isinstance(coverage, dict) else None
        root_terminal_ids = (
            {str(burden) for burden in root_terminals}
            if isinstance(root_terminals, dict)
            else set()
        )
        coverage_terminal_ids = (
            {str(burden) for burden in coverage_terminals}
            if isinstance(coverage_terminals, dict)
            else set()
        )
        if root_terminal_ids != burden_ids or coverage_terminal_ids != burden_ids:
            return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-terminal-identity", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "root and coverage terminal identities must each equal B_total"}]
        reread_records = field_witness.get("reread_records")
        nar = field_witness.get("normalized_activation_record")
        nar_rows = nar.get("per_burden") if isinstance(nar, dict) else None
        reread_by_burden = {
            str(row.get("burden_id")): row
            for row in (reread_records if isinstance(reread_records, list) else [])
            if isinstance(row, dict) and row.get("burden_id")
        }
        nar_by_burden = {
            str(row.get("burden_id")): row
            for row in (nar_rows if isinstance(nar_rows, list) else [])
            if isinstance(row, dict) and row.get("burden_id")
        }
        for burden in b_total:
            root_terminal = root_terminals.get(burden)
            if not isinstance(root_terminal, dict) or root_terminal.get("state") != coverage_terminals.get(burden):
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-terminal-state", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"root terminal state for {burden} must equal coverage terminal state"}]
            cycle_id = root_terminal.get("cycle_id")
            reread = reread_by_burden.get(str(burden), {})
            nar_row = nar_by_burden.get(str(burden), {})
            if (
                not isinstance(cycle_id, str)
                or not cycle_id
                or reread.get("cycle_id") != cycle_id
                or nar_row.get("cycle_id") != cycle_id
                or reread.get("terminal_state") != root_terminal.get("state")
            ):
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-terminal-cycle", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"terminal cycle identity for {burden} must agree across root, reread, and NAR records"}]
        root_edges = field_witness.get("edges")
        dependency_graph = coverage.get("dependency_graph") if isinstance(coverage, dict) else None
        coverage_edges = (
            dependency_graph.get("edges")
            if isinstance(dependency_graph, dict)
            else None
        )
        root_edge_ids = [
            (str(edge.get("from")), str(edge.get("to")))
            for edge in root_edges
            if isinstance(root_edges, list) and isinstance(edge, dict)
        ]
        coverage_edge_ids = [
            (str(edge.get("from")), str(edge.get("to")))
            for edge in coverage_edges
            if isinstance(coverage_edges, list) and isinstance(edge, dict)
        ]
        for label, edge_ids in (("root", root_edge_ids), ("coverage", coverage_edge_ids)):
            if len(edge_ids) != len(set(edge_ids)):
                duplicate = next(edge for edge in edge_ids if edge_ids.count(edge) > 1)
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-duplicate-edge", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"dependency_graph {label} contains duplicate dependency edge {duplicate[0]}->{duplicate[1]}"}]
        root_edge_endpoints_are_burdens = all(
            source in burden_ids and target in burden_ids
            for source, target in root_edge_ids
        )
        if root_edge_endpoints_are_burdens and root_edge_ids != coverage_edge_ids:
            return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-edge-parity", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "dependency_graph root and coverage edge identities must match exactly in order"}]
        resultants_by_pair = {
            (str(row.get("source")), str(row.get("target"))): row
            for row in field_witness.get("mrp_resultants", [])
            if isinstance(row, dict) and row.get("source") and row.get("target")
        }
        for edge in root_edges if isinstance(root_edges, list) and root_edge_endpoints_are_burdens else []:
            if not isinstance(edge, dict):
                continue
            pair = (str(edge.get("from")), str(edge.get("to")))
            resultant = resultants_by_pair.get(pair)
            edge_kind = str(edge.get("kind") or "").strip().lower().replace("-", "_")
            resultant_kind = str(resultant.get("type") or "").strip().lower().replace("-", "_") if resultant is not None else ""
            if edge_kind == "generated_resultant":
                edge_kind = "generated_burden_instantiation"
            if resultant_kind == "generated_resultant":
                resultant_kind = "generated_burden_instantiation"
            if resultant is not None and edge_kind != resultant_kind:
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-edge-resultant-kind", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"dependency_graph edge kind for {pair[0]}->{pair[1]} must equal its MRP resultant type"}]
    nodes = field_witness.get("nodes", [])
    node_id_list = [str(row.get("id")) for row in nodes if isinstance(row, dict) and row.get("id")]
    if len(node_id_list) != len(set(node_id_list)):
        duplicate = next(node for node in node_id_list if node_id_list.count(node) > 1)
        return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-duplicate-node", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"duplicate node identity {duplicate}"}]
    node_ids = set(node_id_list)
    if compatibility == "current" and isinstance(b_total, list) and node_ids != set(b_total):
        return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-dangling-node", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"graph node identities {sorted(node_ids)} must equal B_total {sorted(set(b_total))}"}]
    if compatibility == "current":
        node_by_id = {
            str(row.get("id")): row
            for row in nodes
            if isinstance(row, dict) and row.get("id")
        }
        current_edges = field_witness.get("edges", [])
        current_edge_endpoints_are_nodes = all(
            isinstance(edge, dict)
            and edge.get("from") in node_ids
            and edge.get("to") in node_ids
            for edge in current_edges
        ) if isinstance(current_edges, list) else False
        incoming_by_target: dict[str, list[str]] = {}
        for edge in current_edges if isinstance(current_edges, list) else []:
            if isinstance(edge, dict) and edge.get("from") and edge.get("to"):
                incoming_by_target.setdefault(str(edge["to"]), []).append(str(edge["from"]))
        for burden in b_total if isinstance(b_total, list) and current_edge_endpoints_are_nodes else []:
            incoming = incoming_by_target.get(str(burden), [])
            if len(incoming) > 1:
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-node-parent-ambiguous", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"node {burden} has multiple incoming dependency parents but current parent_id is singular"}]
            expected_parent = incoming[0] if incoming else None
            if node_by_id.get(str(burden), {}).get("parent_id") != expected_parent:
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-node-parent", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"node {burden} dependency parent_id must equal its unique incoming source"}]
        for burden in b_la if isinstance(b_la, list) else []:
            node = node_by_id.get(str(burden), {})
            if node.get("origin") != "B_LA" or node.get("type") != "burden":
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-node-origin", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"node {burden} origin/type must be B_LA/burden"}]
        generated_by_id = {
            str(row.get("id")): row
            for row in field_witness.get("generated_burdens", [])
            if isinstance(row, dict) and row.get("id")
        }
        for burden in b_mrp if isinstance(b_mrp, list) else []:
            node = node_by_id.get(str(burden), {})
            if node.get("origin") != "B_MRP" or node.get("type") != "generated_burden":
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-node-origin", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"node {burden} origin/type must be B_MRP/generated_burden"}]
            generated = generated_by_id.get(str(burden), {})
            if not generated or node.get("parent_id") != generated.get("source"):
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-node-parent", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"generated node {burden} parent_id must equal generated_burdens source"}]
    for edge in field_witness.get("edges", []) if isinstance(field_witness.get("edges"), list) else []:
        if isinstance(edge, dict) and (edge.get("from") not in node_ids or edge.get("to") not in node_ids):
            return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-dangling-edge", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"edge {edge.get('from')}->{edge.get('to')} references missing node"}]
    generated_list = [str(row.get("id")) for row in field_witness.get("generated_burdens", []) if isinstance(row, dict)]
    if len(generated_list) != len(set(generated_list)):
        duplicate = next(node for node in generated_list if generated_list.count(node) > 1)
        return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-duplicate-generated-burden", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"duplicate generated burden identity {duplicate}"}]
    generated = set(generated_list)
    if compatibility == "current" and generated != set(b_mrp):
        return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-generated-identity", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "generated_burdens identities must equal B_MRP"}]
    event_graph = coverage.get("provenance_event_dag", {}) if isinstance(coverage, dict) else {}
    if isinstance(event_graph, dict):
        raw_event_nodes = event_graph.get("nodes", [])
        raw_event_roots = event_graph.get("roots", [])
        raw_event_edges = event_graph.get("edges", [])
        event_node_list = [str(node) for node in raw_event_nodes] if isinstance(raw_event_nodes, list) else []
        event_root_list = [str(node) for node in raw_event_roots] if isinstance(raw_event_roots, list) else []
        event_edges = [
            (str(edge.get("from")), str(edge.get("to")))
            for edge in (raw_event_edges if isinstance(raw_event_edges, list) else [])
            if isinstance(edge, dict)
        ]
        event_nodes = set(event_node_list)
        if compatibility == "current":
            dependency_graph = coverage.get("dependency_graph", {}) if isinstance(coverage, dict) else {}
            dependency_roots = dependency_graph.get("roots", []) if isinstance(dependency_graph, dict) else []
            dependency_edges = dependency_graph.get("edges", []) if isinstance(dependency_graph, dict) else []
            if len(event_node_list) != len(set(event_node_list)) or len(event_node_list) != len(b_total):
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-event-identity", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "provenance event identities must be unique with B_total cardinality"}]
            if (
                len(event_root_list) != len(set(event_root_list))
                or len(event_root_list) != len(dependency_roots if isinstance(dependency_roots, list) else [])
                or any(root not in event_nodes for root in event_root_list)
            ):
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-event-root-cardinality", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "provenance event root identities must be unique members with dependency-root cardinality"}]
            if (
                len(event_edges) != len(set(event_edges))
                or len(event_edges) != len(dependency_edges if isinstance(dependency_edges, list) else [])
            ):
                return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-event-edge-cardinality", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "provenance event edges must be unique with dependency-edge cardinality"}]
            for generated_row in field_witness.get("generated_burdens", []):
                if not isinstance(generated_row, dict):
                    continue
                burden = str(generated_row.get("id") or "")
                if burden in b_total:
                    expected_event = event_node_list[b_total.index(burden)]
                    if generated_row.get("event_id") != expected_event:
                        return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-generated-event", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": f"generated burden {burden} event_id must match its terminal cycle event"}]
        if any(source not in event_nodes or target not in event_nodes for source, target in event_edges):
            return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-dangling-event", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "provenance event edge references a missing event node"}]
        if _directed_cycle(event_nodes, event_edges):
            return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-event-dag-cycle", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "provenance event DAG must be acyclic; noetic dependency cycles are a distinct relation"}]
    t_lang = field_witness.get("T_lang")
    if compatibility == "current" and (not isinstance(t_lang, dict) or t_lang.get("projection") != "partial_coupling" or t_lang.get("uptake_guaranteed") is not False):
        return [{"failure_class": "witness-graph", "failure_subcode": "witness-graph-t-lang-overclaim", "earliest_stage": "07", "downstream_invalidated": ["08"], "message": "T_lang must remain partial coupling with non-guaranteed uptake"}]
    return []


def extract_embedded_field_witness(text: str) -> dict[str, Any] | None:
    match = re.search(r"(?:^|\n)\s*(?:#{1,6}\s*)?field_witness\b", str(text or ""), re.IGNORECASE)
    if not match:
        return None
    raw_json = extract_balanced_json_from(text, match.start())
    if not raw_json:
        return None
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        return None


def extract_field_witness(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("field_witness"), dict):
        return payload["field_witness"]
    if "coverage_proof" in payload and "field_diagnostics" in payload:
        return payload
    if any(key in payload for key in ("nodes", "edges", "ledger", "B_LA", "B_MRP", "B_total")):
        return payload
    return None


def field_witness_ledger(field_witness: dict[str, Any] | None) -> dict[str, list[str]]:
    ledgers = {"B_LA": [], "B_MRP": [], "B_total": []}
    if not isinstance(field_witness, dict):
        return ledgers
    ledger = field_witness.get("ledger")
    if not isinstance(ledger, dict):
        ledger = field_witness
    for key in ledgers:
        value = ledger.get(key)
        if isinstance(value, list):
            ledgers[key] = unique(
                normalize_burden_id(str(item))
                for item in value
                if isinstance(item, str) and BURDEN_ID_RE.fullmatch(item.strip())
            )
    return ledgers


def field_witness_mrp_resultants(field_witness: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(field_witness, dict):
        return []
    raw = field_witness.get("mrp_resultants")
    if not isinstance(raw, list):
        reread = field_witness.get("reread_pressure")
        if isinstance(raw, dict):
            raw = [
                {"source": source, **item} if isinstance(item, dict) else {"source": source, "type": str(item)}
                for source, item in raw.items()
            ]
        elif isinstance(reread, dict) and any(str(key).startswith(("MRP(", "B")) for key in reread.keys()):
            raw = [
                {"source": source, **item} if isinstance(item, dict) else {"source": source, "type": str(item)}
                for source, item in reread.items()
            ]
        elif isinstance(reread, dict):
            source = reread.get("target_burden_id", "")
            raw = [
                {
                    "source": source,
                    "type": reread.get("route_result_type", ""),
                    "finding": reread.get("finding", ""),
                    "graph": reread.get("graph_delta", {}),
                    "route": reread.get("route", ""),
                }
            ]
        else:
            return []
    resultants: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        source = item.get("source") or item.get("target_burden_id") or item.get("from") or item.get("id") or ""
        source = re.sub(r"^MRP\((.*)\)$", r"\1", str(source))
        graph_value = item.get("graph")
        if graph_value is None:
            graph_value = item.get("graph_delta")
        if isinstance(graph_value, dict):
            if "from" in graph_value and "to" in graph_value:
                graph = f"{normalize_burden_id(str(graph_value.get('from')))}->{normalize_burden_id(str(graph_value.get('to')))}"
            elif "edges_added" in graph_value and isinstance(graph_value["edges_added"], list):
                pairs = []
                for edge in graph_value["edges_added"]:
                    if isinstance(edge, dict):
                        pairs.append(f"{normalize_burden_id(str(edge.get('from', '')))}->{normalize_burden_id(str(edge.get('to', '')))}")
                graph = ";".join(pair for pair in pairs if pair != "->") or "none"
            else:
                graph = "none"
        elif isinstance(graph_value, str):
            graph = normalize_graph_value(graph_value)
        else:
            graph = "none"
        resultants.append(
            {
                "source": normalize_burden_id(source),
                "type": str(item.get("type") or item.get("route_result_type") or ""),
                "finding": str(item.get("finding") or ""),
                "graph": graph,
                "route": str(item.get("route") or ""),
            }
        )
    return resultants


def field_witness_graph_errors(field_witness: dict[str, Any] | None) -> list[str]:
    if field_witness is None:
        return ["field_witness JSON missing"]
    errors: list[str] = []
    ledgers = field_witness_ledger(field_witness)
    if ledgers["B_MRP"] and not ledgers["B_total"]:
        errors.append("field_witness ledger has B_MRP but missing B_total")
    for generated in ledgers["B_MRP"]:
        if generated in ledgers["B_LA"]:
            errors.append(f"field_witness marks baseline burden {generated} as generated")
    if ledgers["B_total"]:
        expected_total = unique(ledgers["B_LA"] + ledgers["B_MRP"])
        if ledgers["B_total"] != expected_total:
            errors.append("field_witness B_total must equal B_LA plus B_MRP in order")
    for index, resultant in enumerate(field_witness_mrp_resultants(field_witness)):
        if not resultant.get("source"):
            errors.append(f"field_witness.mrp_resultants[{index}] missing source")
        if not resultant.get("type"):
            errors.append(f"field_witness.mrp_resultants[{index}] missing type")
        if not resultant.get("route"):
            errors.append(f"field_witness.mrp_resultants[{index}] missing route")
    coverage = field_witness.get("coverage_proof")
    if not isinstance(coverage, dict):
        return errors + ["field_witness.coverage_proof missing"]
    graph = coverage.get("dependency_graph")
    if not isinstance(graph, dict):
        return errors + ["field_witness.coverage_proof.dependency_graph missing"]
    initial = coverage.get("initial_burden_set")
    terminals = coverage.get("terminal_states")
    if not isinstance(initial, list):
        initial = []
    if not isinstance(terminals, dict):
        terminals = {}
    nodes = graph.get("nodes")
    roots = graph.get("roots")
    edges_payload = graph.get("edges")
    parallel_groups = graph.get("parallel_groups")
    if not isinstance(nodes, list) or not all(isinstance(node, str) and BURDEN_ID_RE.fullmatch(node) for node in nodes):
        errors.append("field_witness.coverage_proof.dependency_graph.nodes must be B-id array")
        nodes = []
    if len(set(nodes)) != len(nodes):
        errors.append("field_witness.coverage_proof.dependency_graph.nodes must be unique")
    if not isinstance(roots, list) or not all(isinstance(node, str) and BURDEN_ID_RE.fullmatch(node) for node in roots):
        errors.append("field_witness.coverage_proof.dependency_graph.roots must be B-id array")
        roots = []
    if not isinstance(edges_payload, list):
        errors.append("field_witness.coverage_proof.dependency_graph.edges must be array")
        edges_payload = []
    edges: list[tuple[str, str]] = []
    for index, edge in enumerate(edges_payload):
        if isinstance(edge, dict):
            if not {"from", "to"}.issubset(set(edge)):
                errors.append(f"field_witness.coverage_proof.dependency_graph.edges[{index}] must have from/to")
                continue
            source = edge.get("from")
            target = edge.get("to")
        elif isinstance(edge, list) and len(edge) == 2:
            source, target = edge
        else:
            errors.append(f"field_witness.coverage_proof.dependency_graph.edges[{index}] must be from/to object or pair")
            continue
        if not isinstance(source, str) or not BURDEN_ID_RE.fullmatch(source):
            errors.append(f"field_witness.coverage_proof.dependency_graph.edges[{index}].from must be B-id")
            continue
        if not isinstance(target, str) or not BURDEN_ID_RE.fullmatch(target):
            errors.append(f"field_witness.coverage_proof.dependency_graph.edges[{index}].to must be B-id")
            continue
        edges.append((source, target))
    groups: list[list[str]] = []
    if not isinstance(parallel_groups, list):
        parallel_groups = []
    if isinstance(parallel_groups, list):
        for index, group in enumerate(parallel_groups):
            if not isinstance(group, list) or len(group) < 2 or not all(isinstance(node, str) and BURDEN_ID_RE.fullmatch(node) for node in group):
                errors.append(f"field_witness.coverage_proof.dependency_graph.parallel_groups[{index}] must contain at least two B-ids")
                continue
            groups.append(group)
    if not isinstance(graph.get("acyclic"), bool):
        errors.append("field_witness.coverage_proof.dependency_graph.acyclic must be boolean")
    graph_node_set = set(nodes)
    implied_nodes = set(item for item in initial if isinstance(item, str))
    implied_nodes.update(str(node) for node in terminals if isinstance(node, str))
    implied_nodes.update(ledgers["B_LA"])
    implied_nodes.update(ledgers["B_MRP"])
    implied_nodes.update(ledgers["B_total"])
    implied_nodes.update(roots)
    for source, target in edges:
        implied_nodes.update((source, target))
    for group in groups:
        implied_nodes.update(group)
    implied_nodes = {node for node in implied_nodes if BURDEN_ID_RE.fullmatch(node)}
    if graph_node_set and implied_nodes and graph_node_set != implied_nodes:
        missing = sorted(implied_nodes - graph_node_set)
        extra = sorted(graph_node_set - implied_nodes)
        if missing:
            errors.append(f"field_witness.coverage_proof.dependency_graph.nodes missing implied burdens: {', '.join(missing)}")
        if extra:
            errors.append(f"field_witness.coverage_proof.dependency_graph.nodes has extra burdens not in ledgers/terminals/edges: {', '.join(extra)}")
    graph_text = "; ".join(
        [f"{root} (root)" for root in roots]
        + [f"{source} → {target}" for source, target in edges]
        + [" ∥ ".join(group) for group in groups]
    )
    terminal_states = terminals if isinstance(terminals, dict) else {}
    errors.extend(
        graph_validation_errors(
            initial_burdens=[item for item in initial if isinstance(item, str)],
            terminal_states=terminal_states,
            graph_text=graph_text,
            edges=edges,
            roots=roots,
            parallel_groups=groups,
        )
    )
    actual_acyclic = not has_cycle(graph_nodes(edges, roots, groups), edges)
    if isinstance(graph.get("acyclic"), bool) and graph["acyclic"] != actual_acyclic:
        errors.append("field_witness.coverage_proof.dependency_graph.acyclic does not match parsed graph")
    return errors


def nested_field_diagnostic_status(diagnostics: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = diagnostics.get(key)
        if isinstance(value, str) and value.strip():
            return value
    nested_values: list[str] = []
    for value in diagnostics.values():
        if not isinstance(value, dict):
            continue
        for key in keys:
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                nested_values.append(nested)
                break
    return nested_values[-1] if nested_values else ""


def compare_visible_to_field_witness(witness: ClosureWitness, field_witness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    coverage = field_witness.get("coverage_proof") if isinstance(field_witness, dict) else None
    ledgers = field_witness_ledger(field_witness)
    if witness.ledger_la and ledgers["B_LA"] and ledgers["B_LA"] != witness.ledger_la:
        errors.append("visible witness B_LA does not match field_witness ledger.B_LA")
    if witness.ledger_mrp and not ledgers["B_MRP"]:
        errors.append("visible witness has B_MRP but field_witness ledger.B_MRP is missing")
    elif witness.ledger_mrp and ledgers["B_MRP"] != witness.ledger_mrp:
        errors.append("visible witness B_MRP does not match field_witness ledger.B_MRP")
    if witness.ledger_total and not ledgers["B_total"]:
        errors.append("visible witness has B_total but field_witness ledger.B_total is missing")
    elif witness.ledger_total and ledgers["B_total"] != witness.ledger_total:
        errors.append("visible witness B_total does not match field_witness ledger.B_total")
    for generated in ledgers["B_MRP"]:
        if generated in ledgers["B_LA"]:
            errors.append(f"field_witness marks baseline burden {generated} as generated")
    visible_mrp = witness.mrp_resultants
    sidecar_mrp = field_witness_mrp_resultants(field_witness)
    if visible_mrp and not sidecar_mrp:
        errors.append("visible witness has MRP resultants but field_witness omits them")
    elif visible_mrp and sidecar_mrp:
        visible_set = {
            (item.get("source", ""), item.get("type", ""), item.get("graph", ""), item.get("route", ""))
            for item in visible_mrp
        }
        sidecar_set = {
            (item.get("source", ""), item.get("type", ""), item.get("graph", ""), item.get("route", ""))
            for item in sidecar_mrp
        }
        if visible_set != sidecar_set:
            errors.append("visible witness MRP resultants do not match field_witness MRP resultants")
    if not isinstance(coverage, dict):
        return errors + ["field_witness.coverage_proof missing for visible consistency check"]
    graph = coverage.get("dependency_graph")
    if not isinstance(graph, dict):
        return errors + ["field_witness.coverage_proof.dependency_graph missing for visible consistency check"]
    if coverage.get("initial_burden_set") != witness.initial_burdens:
        errors.append("visible witness initial burden set does not match field_witness.coverage_proof.initial_burden_set")
    terminal_payload = coverage.get("terminal_states")
    if isinstance(terminal_payload, dict):
        for burden, visible_payload in witness.terminal_states.items():
            sidecar_payload = terminal_payload.get(burden)
            if isinstance(sidecar_payload, str):
                state, _, detail = sidecar_payload.partition("/")
                sidecar_payload = {"state": state.strip(), "detail": detail.strip()}
            if not isinstance(sidecar_payload, dict):
                errors.append(f"field_witness missing terminal state for visible burden {burden}")
                continue
            if sidecar_payload.get("state") != visible_payload.get("state"):
                errors.append(f"terminal state mismatch for {burden}: visible {visible_payload.get('state')!r} vs field_witness {sidecar_payload.get('state')!r}")
    side_edges = []
    for edge in graph.get("edges", []):
        if isinstance(edge, dict):
            side_edges.append((edge.get("from"), edge.get("to")))
        elif isinstance(edge, list) and len(edge) == 2:
            side_edges.append((edge[0], edge[1]))
    if set(side_edges) != set(witness.edges):
        errors.append("visible witness dependency edges do not match field_witness dependency_graph.edges")
    if set(graph.get("roots", [])) != set(witness.roots):
        errors.append("visible witness roots do not match field_witness dependency_graph.roots")
    side_groups = {tuple(group) for group in graph.get("parallel_groups", []) if isinstance(group, list)}
    visible_groups = {tuple(group) for group in witness.parallel_groups}
    if side_groups != visible_groups:
        errors.append("visible witness parallel groups do not match field_witness dependency_graph.parallel_groups")
    diagnostics = field_witness.get("field_diagnostics") if isinstance(field_witness.get("field_diagnostics"), dict) else {}
    if not coverage.get("divergence_check"):
        coverage["divergence_check"] = nested_field_diagnostic_status(
            diagnostics, "del_dot_B", "del_dot_T", "∇·T", "∇·B"
        )
    if not coverage.get("curl_check"):
        coverage["curl_check"] = nested_field_diagnostic_status(
            diagnostics, "del_cross_kappa", "del_cross_T", "∇×T", "∇×κ"
        )
    if status_head(str(coverage.get("divergence_check", ""))) != status_head(witness.divergence):
        errors.append("visible ∇·B status does not match field_witness.coverage_proof.divergence_check")
    if status_head(str(coverage.get("curl_check", ""))) != status_head(witness.curl):
        errors.append("visible ∇×κ status does not match field_witness.coverage_proof.curl_check")
    return errors
