#!/usr/bin/env python3
"""Parse Closure/Reconstruction Witness blocks.

This module is intentionally dependency-free and structural. It makes rendered
coverage auditable; it does not grade live noetic competence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


BURDEN_ID_RE = re.compile(r"\bB\d+\b")
HEADING_RE = re.compile(r"(?im)^\s*(?:#{2,5}\s*)?Closure/Reconstruction Witness\b")
NEXT_HEADING_RE = re.compile(r"(?m)^\s*(?:#{2,5}\s+\S|Restorative Response\b|Closing Formulation\b)")
KNOWN_FIELD_RE = re.compile(
    r"(?i)^\s*(?:[-*]\s*)?(?:"
    r"N frames|Registers|Burden dependency graph|[∇\u2207]·B|[∇\u2207]×κ|"
    r"del[- ]dot\s*B|del[- ]cross\s*kappa|𝒞\(Ψᴺ\)|C\(PsiN\)|T_lang"
    r")\s*:"
)
INITIAL_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Initial burden set\s*:\s*\[(?P<body>[^\]]*)\]")
TERMINAL_HEADER_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Terminal states\s*:\s*$")
TERMINAL_INLINE_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Terminal states\s*:\s*(?P<body>\S.*)$")
TERMINAL_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<burden>B\d+)\s*:\s*"
    r"(?P<state>[A-Za-z-]+)\b(?:\s*/\s*(?P<detail>.*))?$"
)
GRAPH_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Burden dependency graph\s*:\s*(?P<body>\S.*)$")
DIVERGENCE_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:∇·B|del[- ]dot\s*B)\s*:\s*(?P<body>\S.*)$")
CURL_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:∇×κ|del[- ]cross\s*kappa)\s*:\s*(?P<body>\S.*)$")
CLOSURE_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?`?𝒞\(Ψᴺ\)`?\s*:\s*(?P<body>\S.*)$")
TRANSFER_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?`?T_lang\s*:\s*Ψᴺ\s*⇢\s*Ψᴵ`?"
    r"(?:\s+(?:coupling|boundary|coupling boundary))?\s*:\s*(?P<body>\S.*)$"
)
EDGE_RE = re.compile(r"\b(?P<src>B\d+)\b\s*(?:→|->)\s*(?P<targets>B\d+(?:\s*,\s*B\d+)*)")
ROOT_RE = re.compile(r"\b(?P<node>B\d+)\b\s*\(root\)")
PARALLEL_RE = re.compile(r"\b(?P<a>B\d+)\b\s*∥\s*\b(?P<b>B\d+)\b")


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
    terminal_states: dict[str, dict[str, str]]
    duplicate_terminal_states: list[str]
    graph_text: str
    edges: list[tuple[str, str]]
    roots: list[str]
    parallel: list[tuple[str, str]]
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
        first = _status_head(self.divergence)
        return first == "neutral"

    @property
    def curl_null_or_resolved(self) -> bool:
        first = _status_head(self.curl)
        return first in {"null", "resolved"}

    @property
    def collapse_positive(self) -> bool:
        return self.coverage_complete and self.divergence_neutral and self.curl_null_or_resolved

    @property
    def closure_claims_positive(self) -> bool:
        return bool(re.search(r"(?i)\b(?:positive|complete|completed|closed|stop|collapse)\b", self.closure))


def _status_head(value: str) -> str:
    return re.split(r"\s*/\s*|;|,", value.strip().lower(), maxsplit=1)[0].strip()


def extract_closure_witness_block(text: str) -> str | None:
    match = HEADING_RE.search(text)
    if not match:
        return None
    start = match.end()
    next_heading = NEXT_HEADING_RE.search(text, start)
    end = next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def parse_burden_list(body: str) -> list[str]:
    return BURDEN_ID_RE.findall(body)


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
                burden = inline_state.group("burden")
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
        burden = match.group("burden")
        if burden in states and burden not in duplicates:
            duplicates.append(burden)
        states[burden] = {
            "state": match.group("state"),
            "detail": (match.group("detail") or "").strip(),
        }
    return states, duplicates


def parse_graph(graph_text: str) -> tuple[list[tuple[str, str]], list[str], list[tuple[str, str]]]:
    edges: list[tuple[str, str]] = []
    roots = ROOT_RE.findall(graph_text)
    parallel = [(m.group("a"), m.group("b")) for m in PARALLEL_RE.finditer(graph_text)]
    for match in EDGE_RE.finditer(graph_text):
        src = match.group("src")
        for target in BURDEN_ID_RE.findall(match.group("targets")):
            edges.append((src, target))
    return edges, roots, parallel


def parse_closure_witness(text: str) -> ClosureWitness | None:
    block = extract_closure_witness_block(text)
    if block is None:
        return None
    initial_match = INITIAL_RE.search(block)
    initial = parse_burden_list(initial_match.group("body")) if initial_match else []
    terminal_states, duplicates = parse_terminal_states(block)
    graph_match = GRAPH_RE.search(block)
    graph_text = graph_match.group("body").strip() if graph_match else ""
    edges, roots, parallel = parse_graph(graph_text)
    divergence_match = DIVERGENCE_RE.search(block)
    curl_match = CURL_RE.search(block)
    closure_match = CLOSURE_RE.search(block)
    transfer_match = TRANSFER_RE.search(block)
    return ClosureWitness(
        block=block,
        initial_burdens=initial,
        terminal_states=terminal_states,
        duplicate_terminal_states=duplicates,
        graph_text=graph_text,
        edges=edges,
        roots=roots,
        parallel=parallel,
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
