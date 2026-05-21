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
NEXT_HEADING_RE = re.compile(r"(?m)^\s*(?:#{2,5}\s+\S|Restorative Response\b|Closing Formulation\b)")
KNOWN_FIELD_RE = re.compile(
    "(?i)^\s*(?:[-*]\s*)?(?:"
    "N frames|Registers|Burden dependency graph|\u2207\u00b7B|\u2207\u00b7T|\u2207\u00d7\u03ba|\u2207\u00d7T|"
    "del[- ]dot\s*B|del[- ]dot\s*T|del[- ]cross\s*kappa|del[- ]cross\s*T|"
    "\U0001d49e\(\u03a8\u1d3a\)|C\(PsiN\)|T_lang"
    ")\s*:"
)
REGISTERS_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Registers\s*:\s*(?P<body>\S.*)$")
INITIAL_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Initial burden set\s*:\s*\[(?P<body>[^\]]*)\]")
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
    registers: str
    terminal_states: dict[str, dict[str, str]]
    duplicate_terminal_states: list[str]
    graph_text: str
    edges: list[tuple[str, str]]
    roots: list[str]
    parallel: list[tuple[str, str]]
    parallel_groups: list[list[str]]
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
                if chunks:
                    break
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
        detail = terminal_states.get(burden, {}).get("detail", "")
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
    terminal_states, duplicates = parse_terminal_states(block)
    graph_text = extract_graph_text(block)
    edges, roots, parallel, parallel_groups = parse_graph(graph_text)
    registers_match = REGISTERS_RE.search(block)
    divergence_match = DIVERGENCE_RE.search(block)
    curl_match = CURL_RE.search(block)
    closure_match = CLOSURE_RE.search(block)
    transfer_match = TRANSFER_RE.search(block)
    return ClosureWitness(
        block=block,
        initial_burdens=initial,
        registers=registers_match.group("body").strip() if registers_match else "",
        terminal_states=terminal_states,
        duplicate_terminal_states=duplicates,
        graph_text=graph_text,
        edges=edges,
        roots=roots,
        parallel=parallel,
        parallel_groups=parallel_groups,
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


def extract_field_witness(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("field_witness"), dict):
        return payload["field_witness"]
    if "coverage_proof" in payload and "field_diagnostics" in payload:
        return payload
    return None


def field_witness_graph_errors(field_witness: dict[str, Any] | None) -> list[str]:
    if field_witness is None:
        return ["field_witness JSON missing"]
    errors: list[str] = []
    coverage = field_witness.get("coverage_proof")
    if not isinstance(coverage, dict):
        return ["field_witness.coverage_proof missing"]
    graph = coverage.get("dependency_graph")
    if not isinstance(graph, dict):
        return ["field_witness.coverage_proof.dependency_graph missing"]
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
        if not isinstance(edge, dict) or set(edge) != {"from", "to"}:
            errors.append(f"field_witness.coverage_proof.dependency_graph.edges[{index}] must have from/to only")
            continue
        source = edge.get("from")
        target = edge.get("to")
        if not isinstance(source, str) or not BURDEN_ID_RE.fullmatch(source):
            errors.append(f"field_witness.coverage_proof.dependency_graph.edges[{index}].from must be B-id")
            continue
        if not isinstance(target, str) or not BURDEN_ID_RE.fullmatch(target):
            errors.append(f"field_witness.coverage_proof.dependency_graph.edges[{index}].to must be B-id")
            continue
        edges.append((source, target))
    groups: list[list[str]] = []
    if not isinstance(parallel_groups, list):
        errors.append("field_witness.coverage_proof.dependency_graph.parallel_groups must be array")
    else:
        for index, group in enumerate(parallel_groups):
            if not isinstance(group, list) or len(group) < 2 or not all(isinstance(node, str) and BURDEN_ID_RE.fullmatch(node) for node in group):
                errors.append(f"field_witness.coverage_proof.dependency_graph.parallel_groups[{index}] must contain at least two B-ids")
                continue
            groups.append(group)
    if not isinstance(graph.get("acyclic"), bool):
        errors.append("field_witness.coverage_proof.dependency_graph.acyclic must be boolean")
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


def compare_visible_to_field_witness(witness: ClosureWitness, field_witness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    coverage = field_witness.get("coverage_proof") if isinstance(field_witness, dict) else None
    if not isinstance(coverage, dict):
        return ["field_witness.coverage_proof missing for visible consistency check"]
    graph = coverage.get("dependency_graph")
    if not isinstance(graph, dict):
        return ["field_witness.coverage_proof.dependency_graph missing for visible consistency check"]
    if coverage.get("initial_burden_set") != witness.initial_burdens:
        errors.append("visible witness initial burden set does not match field_witness.coverage_proof.initial_burden_set")
    terminal_payload = coverage.get("terminal_states")
    if isinstance(terminal_payload, dict):
        for burden, visible_payload in witness.terminal_states.items():
            sidecar_payload = terminal_payload.get(burden)
            if not isinstance(sidecar_payload, dict):
                errors.append(f"field_witness missing terminal state for visible burden {burden}")
                continue
            if sidecar_payload.get("state") != visible_payload.get("state"):
                errors.append(f"terminal state mismatch for {burden}: visible {visible_payload.get('state')!r} vs field_witness {sidecar_payload.get('state')!r}")
    side_edges = [(edge.get("from"), edge.get("to")) for edge in graph.get("edges", []) if isinstance(edge, dict)]
    if set(side_edges) != set(witness.edges):
        errors.append("visible witness dependency edges do not match field_witness dependency_graph.edges")
    if set(graph.get("roots", [])) != set(witness.roots):
        errors.append("visible witness roots do not match field_witness dependency_graph.roots")
    side_groups = {tuple(group) for group in graph.get("parallel_groups", []) if isinstance(group, list)}
    visible_groups = {tuple(group) for group in witness.parallel_groups}
    if side_groups != visible_groups:
        errors.append("visible witness parallel groups do not match field_witness dependency_graph.parallel_groups")
    if status_head(str(coverage.get("divergence_check", ""))) != status_head(witness.divergence):
        errors.append("visible ∇·B status does not match field_witness.coverage_proof.divergence_check")
    if status_head(str(coverage.get("curl_check", ""))) != status_head(witness.curl):
        errors.append("visible ∇×κ status does not match field_witness.coverage_proof.curl_check")
    return errors
