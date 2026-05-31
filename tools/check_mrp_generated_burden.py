#!/usr/bin/env python3
"""Validate MRP generated-burden fixtures and public notation discipline.

This checker distinguishes ordinary held-burden activation from a genuinely
MRP-generated downstream burden. It is intentionally fixture-oriented: old
hosted smokes may retain parser aliases, while these fixtures encode the
public notation and route-result contract expected for new generated burdens.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from check_mid_reread_pressure import MrpBlock, first_state, mrp_refutation_content_errors, parse_mrps
from check_manual_smoke_render_contract import (
    GENERIC_CONTRIBUTION_RE,
    OPERATION_ACTION_RE,
    OPERATION_FAILURE_RE,
    OPERATION_MECHANISM_RE,
    OPERATION_SCOPE_RE,
    OPERATION_TEST_RE,
    OWNER_ROUTE_LINE_RE,
    OWNER_ROUTE_TOKEN_RE,
    STATE_CHANGE_RE,
    field_body,
    field_body_any,
    has_matched_owner_route,
    is_label_like_submove,
    contribution_explains_land,
    operation_acts_on_pressure,
    operation_body_has_state_delta,
    owner_family,
    owner_specific_operation_performed,
    sentence_count,
    submove_blocks,
    submove_owner,
    submove_operation_body,
    target_pressure_identifiable,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROUTE_TYPES = {
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "loopbreak",
    "hold_partial",
}
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUB = "₀₁₂₃₄₅₆₇₈₉"
TOKEN = rf"(?:[{SUP}]+B|B\d+)"
CANONICAL_TOKEN = rf"[{SUP}]+B"
EDGE_RE = re.compile(rf"(?P<src>{TOKEN})\s*(?:→|->)\s*(?P<dst>{TOKEN})")
INITIAL_RE = re.compile(r"(?im)^\s*[-*]?\s*Initial burden set\s*:\s*\[(?P<body>[^\]]*)\]")
HELD_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)*(?:Held burden set|Held routes|Held)\s*:"
    r"\s*(?:\[(?P<bracket>[^\]]*)\]|(?P<body>.+))$"
)
MRP_RESULTANT_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?MRP resultants?\s*:")
MRP_CLOSURE_RESULTANT_RE = re.compile(
    rf"(?is)MRP\((?P<src>{TOKEN})\)\s*:\s*type=(?P<route_type>[a-z_]+)\s*;"
    rf"\s*finding=(?P<finding>[^;]+)\s*;\s*graph=(?P<graph>[^;]+)\s*;"
    rf"\s*route=(?P<route>STOP|HOLD|RECURSE|LoopBreak\(∇×T\))"
)
COMMON_EXAMPLE_OWNERS = {"FPD", "M1", "M1-P", "M1P", "M8"}
M1_RECONSTRUCTIBLE_RE = re.compile(
    r"(?i)\b(?:self[- ]refutation|self[- ]grounding|internal contradiction|"
    r"own standard|own rule|own source[- ]appeal standard|own appeal to (?:Scripture|the source|the text|evidence)|"
    r"proof[- ]stack becomes circular|circular (?:protection|appeal|proof[- ]stack)|"
    r"appeal circular|pre-controls? every reading|by its own rule|cannot authorize its own|collapses under its own)\b"
)
P7_STOP_SCOPE_RE = re.compile(
    r"(?i)\b(?:STOP|HOLD|PARTIAL|stop condition|scope boundary|closure boundary|bounded stop|"
    r"bound(?:ed)? closure|bound the closure|bounded refutation|closure is licensed)\b"
)
P7_REOPEN_RE = re.compile(
    r"(?i)\b(?:reopen condition|reopen gate|would require|requires (?:a )?(?:new|fixed|stable)|"
    r"must be (?:stated|routed|worked)|new burden)\b"
)
P7_HELD_ROUTE_RE = re.compile(
    r"(?i)\b(?:held route|held material|held-with-reason|non[- ]load[- ]bearing|"
    r"not load[- ]bearing|unworked material|outside scope)\b"
)
SUBMOVE_REF = rf"(?:{TOKEN}(?:[{SUB}]+|[_\.]\d+))"
ACT_LINE_RE = re.compile(r"(?m)^\s*\u27e6ACT\b.*\u27e7\s*$")
ACT_RECORD_RE = re.compile(
    rf"(?m)^\s*(?P<record>\u27e6ACT\s+"
    rf"(?P<submove_ref>{SUBMOVE_REF})"
    rf"\[(?P<owner>[A-Za-z][A-Za-z0-9_/\-]*)\.(?P<operation>[A-Za-z][A-Za-z0-9_.\-/]*)\]"
    rf"\s*::\s*\u03c0=(?P<pi>[^\n]+?)"
    rf"\s*::\s*body_ref=(?P<body_ref>[^\s:]+)"
    rf"\s*::\s*\u0394=(?P<delta>[^:\s]+):(?P<delta_result>.+?)"
    rf"\s*::\s*(?P<land>Land\([^)\n]+\)\+?)\u27e7)\s*$"
)
DELTA_NAME_RE = re.compile(rf"^(?:\u0394(?:{CANONICAL_TOKEN}|\u03ba))$")
GENERIC_ACT_VALUE_RE = re.compile(
    r"(?i)^\s*(?:pressure|target|result|state change|delta|land|body|route|"
    r"burden|thing|move|operation|owner activation|matched owner|generic pressure)\s*$"
)
UNTRUSTED_ACTIVATION_SELF_CLAIMS = {
    "body_performs_operation",
    "body_ref_resolves",
    "delta_visible_in_body",
    "field_witness_mirror_agrees",
    "land_contribution_present",
    "owner_route_agrees",
    "pressure_found_in_body",
}
SOURCE_OWNED_ACT_OPERATIONS = {
    "M1": {
        "self-grounding-test": re.compile(
            r"(?is)\b(?:self[- ]grounding|own (?:rule|standard)|all[- ]trust[- ]withholding|"
            r"internal contradiction|cannot authorize its own|test(?:s|ed)? that rule)\b"
        ),
        "test": re.compile(
            r"(?is)\b(?:self[- ]grounding|own (?:rule|standard)|internal contradiction|"
            r"circular (?:protection|appeal)|own source[- ]appeal test|"
            r"test(?:s|ed)? (?:the|that) claim)\b"
        ),
    },
    "M7": {
        "definition-anchor": re.compile(
            r"(?is)\b(?:definition|define|anchor|carrier|what (?:is|counts as)|semantic boundary)\b"
        ),
        "define": re.compile(
            r"(?is)\b(?:definition|define|translation demand|admissibility rule|semantic boundary)\b"
        ),
    },
    "M8": {
        "consequence-trace": re.compile(
            r"(?is)\b(?:consequence|entailment|trace|follows|therefore|downstream|implication)\b"
        ),
    },
    "M9": {
        "predication-repair": re.compile(
            r"(?is)\b(?:predicat|category|predicate transfer|reliability|reliable|separate|separated)\b"
        ),
    },
    "P7": {
        "bound": re.compile(
            r"(?is)\b(?:bound|boundary|STOP|scope|held-with-reason|reopen condition|non[- ]load[- ]bearing)\b"
        ),
        "scope-boundary": re.compile(
            r"(?is)\b(?:scope|boundary|bounded|held-with-reason|anti[- ]fluctuation|reopen condition|PARTIAL)\b"
        ),
    },
    "SOURCE": {
        "source-order": re.compile(
            r"(?is)\b(?:source[- ]order|source status|warrant|authority|proof status|anti[- ]fluctuation)\b"
        ),
        "sort": re.compile(
            r"(?is)\b(?:source[- ]order|authority|criterion|sort|judging office|hidden authority transfer)\b"
        ),
    },
    "DOUBT_SKEPTICISM": {
        "method-distinction": re.compile(
            r"(?is)\b(?:doubt|skepticism|method|methodology|churn|carousel|distinguish|separate)\b"
        ),
        "methodology-distinction": re.compile(
            r"(?is)\b(?:doubt|skepticism|method|methodology|churn|carousel|distinguish|separate)\b"
        ),
    },
    "DO_CHRISTIAN": {
        "model-identification": re.compile(
            r"(?is)\b(?:model[- ]identification|which Trinitarian model|"
            r"model is operative|Social Trinitarian|Latin/psychological|"
            r"relative[- ]identity|mystery/apophatic|force varies by model)\b"
        ),
    },
}
LOOSE_OWNER_ALIASES = {
    "AUTHORITY",
    "BOUND",
    "BOUNDARY",
    "BOUNDED",
    "DEFINITION",
    "MRP",
    "OP",
    "OWNER",
    "PREMISE",
    "RESTORATION",
    "SCOPE",
    "SCOPE-BOUNDARY",
    "SOURCE",
    "STOP",
    "TESTIMONY",
    "TRANSMISSION",
    "TTP",
}
DOCUMENTED_OWNER_ALIASES = {
    "AUTHORITY-ORDER": "SOURCE",
    "AUTHORITY-ORDER-REPAIR": "SOURCE",
    "CRITERION-REVERSAL": "M1",
    "DEFINITION-DISCIPLINE": "M7",
    "DO-ATTRIBUTE-PRECISION": "DO_ATTRIBUTE",
    "DO-CHRISTIAN-EXTENSIONS": "DO_CHRISTIAN",
    "DO-SECOND-LOOP": "DO_SECOND_LOOP",
    "DOUBT-VS-SKEPTICISM": "DOUBT_SKEPTICISM",
    "FOREIGN-PREMISE-DETECTION": "FPD",
    "PROOF-METHOD-AUDIT": "PROOF_METHOD",
    "SOURCE-STATUS": "SOURCE",
    "SOURCE-STATUS-REPAIR": "SOURCE",
}
FAMILY_OPERATION_OWNER = {
    "DO_ATTRIBUTE": "do-attribute-precision",
    "DO_CHRISTIAN": "do-christian-extensions",
    "DO_SECOND_LOOP": "do-second-loop",
    "DOUBT_SKEPTICISM": "doubt-vs-skepticism",
    "PROOF_METHOD": "proof-method-audit",
}

BAD_PUBLIC_NOTATION: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ASCII graph edge", re.compile(r"\bB\d+\s*->\s*B\d+\b")),
    ("ASCII Land(Bn)", re.compile(r"\bLand\(B\d+\)")),
    ("ASCII R(H,Delta)", re.compile(r"R\(H,\s*Delta\)")),
    ("ASCII del-dot", re.compile(r"\bdel[- ]dot\b", re.IGNORECASE)),
    ("ASCII del-cross", re.compile(r"\bdel[- ]cross\b", re.IGNORECASE)),
    ("ASCII C(PsiN)", re.compile(r"\bC\(PsiN\)", re.IGNORECASE)),
    ("ASCII T_lang", re.compile(r"T_lang\s*:\s*PsiN\s*->\s*PsiI", re.IGNORECASE)),
    ("subscript burden token", re.compile(rf"\bB[{SUB}]+")),
    ("caret burden token", re.compile(r"\bB\^\d+")),
    ("ASCII submove token", re.compile(r"\bB\d+[_\.]\d+\b")),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def burden_tokens(value: str) -> list[str]:
    return re.findall(TOKEN, value)


def initial_burdens(text: str) -> set[str]:
    match = INITIAL_RE.search(text)
    if not match:
        return set()
    return set(burden_tokens(match.group("body")))


def initial_inventory_segment(text: str) -> str:
    """Return only the pre-Burden initial Layer A / inventory region.

    Later generated burden nodes may render local `held:` lines that mention the
    generated node itself. Those are not part of the initial held set and must
    not cause generated nodes to be misclassified as already held.
    """
    match = re.search(r"(?im)^\s*(?:#{1,6}\s*)?Burden\b", text)
    return text[: match.start()] if match else text


def held_burdens(text: str) -> set[str]:
    found: set[str] = set()
    for match in HELD_RE.finditer(initial_inventory_segment(text)):
        found.update(burden_tokens(match.group("bracket") or match.group("body") or ""))
    return found


def initial_or_held_burdens(text: str) -> set[str]:
    return initial_burdens(text) | held_burdens(text)


def block_target(block: MrpBlock) -> str:
    tokens = burden_tokens(block.target)
    return tokens[0] if tokens else ""


def block_edges(block: MrpBlock) -> list[tuple[str, str]]:
    return [(m.group("src"), m.group("dst")) for m in EDGE_RE.finditer(block.graph_delta + "\n" + block.mrp_resultant)]


def next_section(text: str, start: int) -> str:
    tail = text[start:]
    match = re.search(
        r"(?im)^[ \t]*(?:#{1,6}[ \t]*)?(?:Burden[ \t]+\d+[ \t]*(?:/|:)|"
        r"(?:Restorative Response|Closing Formulation|Closure/Reconstruction Witness|"
        r"Held-node Accounting|Held-node accounting|Closure Audit|"
        r"TTP/operator trace|TTP trace|field_witness|Technical Appendix)\b)",
        tail,
    )
    return tail[: match.start()] if match else tail


def generated_node_section(text: str, heading: re.Match[str], target: str) -> str:
    """Return the generated node section, including a local Layer A rendered before heading.

    Default governed output often renders "Layer A ... for ²B" immediately before
    the "Burden 2 / ²B [generated-by: ...]" heading. That is real Layer A
    accounting for the generated node and should not fail merely because the
    heading follows the re-entry header.
    """
    section = next_section(text, heading.end())
    prefix = text[: heading.start()]
    layer_matches = list(re.finditer(r"(?im)^\s*(?:#{1,6}\s*)?Layer A\b[^\n]*$", prefix))
    if not layer_matches:
        return section
    local_start = layer_matches[-1].start()
    local_layer = prefix[local_start : heading.start()]
    if heading.start() - local_start > 2500 or re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?Burden\s+\d+\b", local_layer
    ):
        return section
    if target in local_layer and re.search(r"(?im)^\s*[-*]\s*live noetic burden\s*:", local_layer):
        return local_layer + "\n" + section
    return section


def generated_heading(text: str, source: str, target: str) -> re.Match[str] | None:
    return re.search(
        rf"(?im)^\s*(?:#{{1,6}}\s*)?Burden\s+\d+\s*(?:/|:)\s*{re.escape(target)}[^\n]*"
        rf"\[generated-by:\s*MRP\({re.escape(source)}\)\]",
        text,
    )


def burden_heading(text: str, target: str) -> re.Match[str] | None:
    return re.search(
        rf"(?im)^[ \t]*(?:#{{1,6}}[ \t]*)?Burden[ \t]+\d+[ \t]*(?:/|:)[ \t]*{re.escape(target)}\b[^\n]*",
        text,
    )


def burden_node_section(text: str, target: str) -> str:
    heading = burden_heading(text, target)
    return next_section(text, heading.end()) if heading else ""


def owner_activation_route_section(section: str) -> str:
    """Return only the target node's incoming/local route-owner surface.

    A burden section includes its post-Land MRP block before the next burden
    heading. That outgoing MRP route belongs to the next node, so its
    Matched owner/TTP route line must not be required inside the already-landed
    target node.
    """
    match = re.search(r"(?im)^\s*\[Mid-Reread Pressure\]\s*$", section)
    return section[: match.start()] if match else section


def owner_submoves(section: str, target: str) -> list[str]:
    pattern = re.compile(
        rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(target)}(?:[{SUB}]+|[_\.]\d+)\s*"
        rf"\[([A-Za-z][A-Za-z0-9_.\-/]*)\](?:\s*\([^)]*\))?\s*(?:[-—:])"
    )
    return pattern.findall(section)


def owner_submove_lines(section: str, target: str) -> list[str]:
    pattern = re.compile(
        rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(target)}(?:[{SUB}]+|[_\.]\d+)\s*"
        rf"\[[A-Za-z][A-Za-z0-9_.\-/]*\](?:\s*\([^)]*\))?\s*(?:[-—:]).+$"
    )
    return [match.group(0).strip() for match in pattern.finditer(section)]


def complete_owner_submoves(section: str, target: str) -> list[str]:
    required = ("Target", "Operation", "Result", "Contribution-to-Land")
    complete: list[str] = []
    heading_re = re.compile(
        rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(target)}(?:[{SUB}]+|[_\.]\d+)\s*"
        rf"\[[A-Za-z][A-Za-z0-9_.\-/]*\](?:\s*\([^)]*\))?\s*(?:[-—:]).*$"
    )
    headings = list(heading_re.finditer(section))
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(section)
        block = section[match.start() : end]
        if (
            re.search(r"\bTarget\s*:", block, re.IGNORECASE)
            and re.search(r"\bOperation\s*:", block, re.IGNORECASE)
            and re.search(r"\bResult(?:/state-change)?\s*:", block, re.IGNORECASE)
            and re.search(r"\bContribution-to-Land(?:\([^)]*\))?\s*:", block, re.IGNORECASE)
        ):
            complete.append(match.group(0).strip())
    return complete


def complete_owner_submove_blocks(section: str, target: str) -> list[str]:
    complete: list[str] = []
    for block in submove_blocks(section, target):
        if (
            re.search(r"\bTarget\s*:", block, re.IGNORECASE)
            and re.search(r"\bOperation\s*:", block, re.IGNORECASE)
            and re.search(r"\bResult(?:/state-change)?\s*:", block, re.IGNORECASE)
            and re.search(r"\bContribution-to-Land(?:\([^)]*\))?\s*:", block, re.IGNORECASE)
        ):
            complete.append(block)
    return complete


@dataclass(frozen=True)
class ActRecord:
    record: str
    submove_ref: str
    owner: str
    operation: str
    pi: str
    body_ref: str
    delta: str
    delta_result: str
    land: str


@dataclass(frozen=True)
class CanonicalActivation:
    """Checker-normalized activation facts.

    This object is derived from the visible ACT row and then proven against
    the dereferenced Layer B body and field_witness mirror. It is not a second
    model-authored proof surface.
    """

    submove_ref: str
    owner: str
    operation: str
    pressure: str
    body_ref: str
    delta: str
    land: str


def canonical_activation_from_record(record: ActRecord) -> CanonicalActivation:
    return CanonicalActivation(
        submove_ref=record.submove_ref,
        owner=record.owner,
        operation=record.operation,
        pressure=record.pi,
        body_ref=record.body_ref,
        delta=record_delta_value(record),
        land=record.land,
    )


def render_act(canonical: CanonicalActivation) -> str:
    return (
        f"\u27e6ACT {canonical.submove_ref}[{canonical.owner}.{canonical.operation}] "
        f":: \u03c0={canonical.pressure} :: body_ref={canonical.body_ref} "
        f":: \u0394={canonical.delta} :: {canonical.land}\u27e7"
    )


def owner_alias_key(value: str) -> str:
    return re.sub(r"[\s_]+", "-", value.strip().strip("[]")).upper()


def catalogue_owner_aliases() -> dict[str, str]:
    aliases = dict(DOCUMENTED_OWNER_ALIASES)
    repo = Path(__file__).resolve().parents[1]
    for relative in (
        Path("atomics/skill/references/diagnostics/module-catalogue.json"),
        Path("atomics/skill/data/module-catalogue.json"),
    ):
        path = repo / relative
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        entries = data.get("modules") or data.get("owners") or []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            raw_aliases = [entry.get("id"), Path(str(entry.get("path", ""))).stem]
            raw_aliases.extend(entry.get("aliases") or [])
            family = next(
                (
                    owner_family(str(alias))
                    for alias in raw_aliases
                    if alias and owner_family(str(alias))
                ),
                "",
            )
            if not family:
                continue
            for alias in raw_aliases:
                if alias:
                    aliases.setdefault(owner_alias_key(str(alias)), family)
    return aliases


CATALOGUE_OWNER_ALIASES = catalogue_owner_aliases()
STRICT_OWNER_CODE_RE = re.compile(
    r"^(?:M1-P|M[1-9]|P[1-7]|V1[0-2]|V[1-9]|E[1-4]|F[1-3]|R[1-3]|FPD)(?:$|[-_./])"
)


def strict_owner_family(value: str) -> str:
    token = owner_alias_key(value)
    if token in LOOSE_OWNER_ALIASES:
        return ""
    family = CATALOGUE_OWNER_ALIASES.get(token)
    if family:
        return family
    if STRICT_OWNER_CODE_RE.match(token):
        return owner_family(token)
    return ""


def normalized_owner_token(value: str) -> str:
    token = value.strip().strip("[]").upper().replace(" ", "-")
    family = strict_owner_family(token)
    return family or token


def matched_owner_route_tokens(scope: str) -> set[str]:
    owners: set[str] = set()
    for match in OWNER_ROUTE_LINE_RE.finditer(scope):
        body = match.group("body")
        for bracket_body in re.findall(r"\[([^\]]+)\]", body):
            for item in re.split(r"[,;]", bracket_body):
                token = item.strip()
                if token:
                    owners.add(normalized_owner_token(token))
        for token_match in OWNER_ROUTE_TOKEN_RE.finditer(body):
            owners.add(normalized_owner_token(token_match.group(0)))
    return {owner for owner in owners if owner and owner not in {"NONE", "UNKNOWN"}}


def contribution_body(block: str) -> str:
    match = re.search(
        r"(?im)^\s*-?\s*Contribution-to-Land(?:\([^)]*\))?\s*:\s*(?P<body>.+)$",
        block,
    )
    return match.group("body").strip() if match else ""


def parse_act_records(section: str) -> tuple[list[ActRecord], list[str]]:
    records: list[ActRecord] = []
    errors: list[str] = []
    parsed_lines: set[str] = set()
    for match in ACT_RECORD_RE.finditer(section):
        parsed_lines.add(match.group(0).strip())
        records.append(
            ActRecord(
                record=match.group("record").strip(),
                submove_ref=match.group("submove_ref").strip(),
                owner=match.group("owner").strip(),
                operation=match.group("operation").strip(),
                pi=match.group("pi").strip(),
                body_ref=match.group("body_ref").strip(),
                delta=match.group("delta").strip(),
                delta_result=match.group("delta_result").strip(),
                land=match.group("land").strip(),
            )
        )
    for line_match in ACT_LINE_RE.finditer(section):
        line = line_match.group(0).strip()
        if line not in parsed_lines:
            errors.append(f"malformed ACT record {line!r}; expected compact ACT owner.operation/body_ref/Delta/Land syntax")
    return records, errors


def field_witness_object(text: str) -> tuple[dict[str, object] | None, str | None]:
    match = re.search(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\s*$", text)
    if not match:
        return None, "missing final field_witness owner activation mirror"
    payload = text[match.end() :].strip()
    fence = re.match(r"(?is)^```(?:json)?\s*(.*?)\s*```", payload)
    if fence:
        payload = fence.group(1).strip()
    start = payload.find("{")
    if start < 0:
        return None, "field_witness payload must be a JSON object"
    try:
        decoded, _end = json.JSONDecoder().raw_decode(payload[start:])
    except json.JSONDecodeError as exc:
        return None, f"field_witness payload is not parser-stable JSON: {exc.msg}"
    if not isinstance(decoded, dict):
        return None, "field_witness payload must be the field_witness object itself"
    if "field_witness" in decoded:
        return None, "field_witness payload must not be nested under a field_witness wrapper"
    return decoded, None


def normalized_transition_text(value: object) -> str:
    text = graph_normalized_text(value)
    text = text.replace("→", "->")
    return " ".join(text.split())


def transition_values_agree(expected: object, actual: object) -> bool:
    expected_text = normalized_transition_text(expected)
    actual_text = normalized_transition_text(actual)
    if not expected_text or not actual_text:
        return False
    return expected_text == actual_text or expected_text in actual_text or actual_text in expected_text


def formal_reread_values_agree(expected: object, actual: object) -> bool:
    expected_text = normalized_transition_text(expected)
    actual_text = normalized_transition_text(actual)
    if not re.match(r"R\(H,\s*(?:Delta|Δ)\)", expected_text):
        return False
    operator_only = re.fullmatch(r"R\(H,\s*(?:Delta|Δ)\)", expected_text)
    return bool(operator_only or transition_values_agree(expected_text, actual_text))


def formal_reread_state_errors(path: Path, text: str, blocks: list[MrpBlock]) -> list[str]:
    """Validate checker-readable reread transition state for every visible MRP block.

    The formal object is not trusted as proof. It is useful only when it agrees
    with visible Land/Delta/R(H,Delta), the MRP route/resultant, and the graph
    edge that dispatches the next owner-routed burden.
    """

    if not blocks:
        return []
    payload, parse_error = field_witness_object(text)
    if parse_error:
        return [f"{path}: {parse_error}"]
    assert payload is not None
    raw_states = payload.get("formal_reread_states")
    if isinstance(raw_states, list):
        states = raw_states
    else:
        return [f"{path}: field_witness.formal_reread_states must be a list with one state per visible MRP block"]

    errors: list[str] = []
    text_norm = normalized_transition_text(text)
    expected_sources = [graph_burden_id(block_target(block)) for block in blocks if block_target(block)]
    blocks_by_source = {source: block for source, block in zip(expected_sources, blocks) if source}
    if len(states) != len(expected_sources):
        errors.append(
            f"{path}: field_witness.formal_reread_states count {len(states)} "
            f"does not match visible MRP block count {len(expected_sources)}"
        )
    required = {
        "source_burden",
        "prior_land",
        "delta",
        "reread",
        "route_gradient",
        "divergence_state",
        "curl_state",
        "route_result_type",
        "mrp_resultant",
        "graph_delta",
        "preemption_basis",
        "route",
    }
    seen_sources: list[str] = []
    for index, state in enumerate(states, start=1):
        label = f"{path}: formal_reread_states[{index}]"
        if not isinstance(state, dict):
            errors.append(f"{label}: state must be a JSON object")
            continue
        source = graph_burden_id(state.get("source_burden"))
        if source:
            seen_sources.append(source)
        missing = sorted(key for key in required if not str(state.get(key, "")).strip())
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")
            continue
        block = blocks_by_source.get(source)
        if block is None:
            errors.append(f"{label}: source_burden {source!r} does not match a visible MRP Target")
            continue
        land_token = f"Land({source})"
        if land_token not in normalized_transition_text(state.get("prior_land")):
            errors.append(f"{label}: prior_land must name {land_token}")
        if land_token not in text_norm:
            errors.append(f"{label}: visible output lacks prior {land_token} before MRP emergence")
        if not transition_values_agree(state.get("delta"), block.landed_delta):
            errors.append(f"{label}: delta does not agree with visible Landed delta")
        if not formal_reread_values_agree(state.get("reread"), block.reread):
            errors.append(f"{label}: reread must invoke R(H,Delta) and agree with visible R(H,Delta) line")
        if not transition_values_agree(state.get("route_gradient"), block.route_gradient):
            errors.append(f"{label}: route_gradient does not agree with visible Route-gradient")
        if state.get("divergence_state") != first_state(block.divergence):
            errors.append(f"{label}: divergence_state does not agree with visible ∇·T")
        if state.get("curl_state") != first_state(block.curl):
            errors.append(f"{label}: curl_state does not agree with visible ∇×T")
        if state.get("route_result_type") != block.route_result_type:
            errors.append(f"{label}: route_result_type does not agree with visible MRP route result type")
        if not transition_values_agree(state.get("mrp_resultant"), block.mrp_resultant):
            errors.append(f"{label}: mrp_resultant does not agree with visible MRP resultant")
        if not transition_values_agree(state.get("graph_delta"), block.graph_delta):
            errors.append(f"{label}: graph_delta does not agree with visible Graph delta")
        if state.get("preemption_basis") != block.preemption_basis:
            errors.append(f"{label}: preemption_basis does not agree with visible Pre-emption basis")
        if state.get("route") != block.route:
            errors.append(f"{label}: route does not agree with visible Route")
        if block.route_result_type in {"generated_burden_instantiation", "held_burden_activation"}:
            edges = block_edges(block)
            if not edges:
                errors.append(f"{label}: owner-routed MRP transition requires a visible graph edge")
                continue
            target = graph_burden_id(edges[0][1])
            if graph_burden_id(state.get("next_burden")) != target:
                errors.append(f"{label}: next_burden must match graph target {target}")
            route = state.get("owner_route")
            if not isinstance(route, list) or not route or any(not str(item).strip() for item in route):
                errors.append(f"{label}: owner_route must list the next burden's source-owned owner/TTP route")
            if block.route_result_type == "generated_burden_instantiation":
                expected_source = f"MRP({source})"
                if graph_burden_id(state.get("generated_by")) != expected_source:
                    errors.append(f"{label}: generated_by must be {expected_source}")
    duplicate_sources = sorted({source for source in seen_sources if source and seen_sources.count(source) > 1})
    if duplicate_sources:
        errors.append(
            f"{path}: field_witness.formal_reread_states duplicate source_burden values: "
            f"{', '.join(duplicate_sources)}"
        )
    missing_sources = sorted(set(expected_sources) - set(seen_sources))
    if missing_sources:
        errors.append(
            f"{path}: field_witness.formal_reread_states missing visible MRP sources: "
            f"{', '.join(missing_sources)}"
        )
    extra_sources = sorted(set(seen_sources) - set(expected_sources))
    if extra_sources:
        errors.append(
            f"{path}: field_witness.formal_reread_states names non-visible MRP sources: "
            f"{', '.join(extra_sources)}"
        )
    return errors


def field_witness_mrp_resultant_errors(path: Path, text: str, blocks: list[MrpBlock]) -> list[str]:
    """Validate field_witness.mrp_resultants when the payload exposes that mirror.

    The visible MRP block remains the public transition. The machine mirror may
    not swap canonical route values for transport aliases such as
    LoopBreak(del-cross(T)).
    """

    if not blocks or "mrp_resultants" not in text:
        return []
    payload, parse_error = field_witness_object(text)
    if parse_error:
        return [f"{path}: {parse_error}"]
    assert payload is not None
    raw_resultants = payload.get("mrp_resultants")
    if not isinstance(raw_resultants, list):
        return [f"{path}: field_witness.mrp_resultants must be a list of objects"]
    resultants = [item for item in raw_resultants if isinstance(item, dict)]
    errors: list[str] = []
    if len(resultants) != len(raw_resultants):
        errors.append(f"{path}: field_witness.mrp_resultants entries must be JSON objects")
    by_source = {graph_burden_id(item.get("source")): item for item in resultants}
    expected_sources = [graph_burden_id(block_target(block)) for block in blocks if block_target(block)]
    for source, block in zip(expected_sources, blocks):
        label = f"{path}: field_witness.mrp_resultants MRP({source})"
        item = by_source.get(source)
        if item is None:
            errors.append(f"{label}: missing machine mirror for visible MRP block")
            continue
        if item.get("type") != block.route_result_type:
            errors.append(f"{label}: type does not agree with visible MRP route result type")
        if item.get("finding") != block.finding:
            errors.append(f"{label}: finding does not agree with visible Finding")
        if not transition_values_agree(item.get("graph"), block.graph_delta):
            errors.append(f"{label}: graph does not agree with visible Graph delta")
        if item.get("route") != block.route:
            errors.append(f"{label}: route does not agree with visible Route")
    missing_sources = sorted(set(expected_sources) - set(by_source))
    if missing_sources:
        errors.append(
            f"{path}: field_witness.mrp_resultants missing visible MRP sources: "
            f"{', '.join(missing_sources)}"
        )
    extra_sources = sorted(set(by_source) - set(expected_sources))
    if extra_sources:
        errors.append(
            f"{path}: field_witness.mrp_resultants names non-visible MRP sources: "
            f"{', '.join(extra_sources)}"
        )
    return errors


def closure_witness_section(text: str) -> str:
    tail = closure_tail(text)
    if not tail:
        return ""
    match = re.search(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\s*$", tail)
    return tail[: match.start()] if match else tail


def record_delta_value(record: ActRecord) -> str:
    return f"{record.delta}:{record.delta_result}"


def normalized_activation_value(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def activation_land_target(value: object) -> str:
    targets = land_targets(str(value or ""))
    return targets[0] if targets else ""


SUP_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
SUB_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
SUP_DIGIT_RE = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUB_DIGIT_RE = "₀₁₂₃₄₅₆₇₈₉"


def graph_burden_id(value: object) -> str:
    text = str(value or "").strip()
    mrp_match = re.fullmatch(r"MRP\((.+)\)", text)
    if mrp_match:
        inner = graph_burden_id(mrp_match.group(1))
        return f"MRP({inner})" if inner else ""
    if re.fullmatch(r"B\d+", text):
        return text
    match = re.fullmatch(rf"([{SUP_DIGIT_RE}]+)B", text)
    if match:
        return f"B{match.group(1).translate(SUP_DIGITS)}"
    return text


def graph_submove_id(value: object) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"B\d+(?:[_\.]\d+)?", text):
        return text.replace(".", "_")
    match = re.fullmatch(rf"([{SUP_DIGIT_RE}]+)B([{SUB_DIGIT_RE}]+)", text)
    if match:
        return f"B{match.group(1).translate(SUP_DIGITS)}_{match.group(2).translate(SUB_DIGITS)}"
    return text


def graph_normalized_text(value: object) -> str:
    text = str(value or "").strip()

    def replace_submove(match: re.Match[str]) -> str:
        return f"B{match.group(1).translate(SUP_DIGITS)}_{match.group(2).translate(SUB_DIGITS)}"

    def replace_burden(match: re.Match[str]) -> str:
        return f"B{match.group(1).translate(SUP_DIGITS)}"

    text = re.sub(rf"([{SUP_DIGIT_RE}]+)B([{SUB_DIGIT_RE}]+)", replace_submove, text)
    text = re.sub(rf"([{SUP_DIGIT_RE}]+)B", replace_burden, text)
    return text


def activation_pressure_matches(expected: str, actual: object) -> bool:
    expected_norm = normalized_activation_value(expected)
    actual_norm = normalized_activation_value(actual)
    if not expected_norm or GENERIC_ACT_VALUE_RE.fullmatch(expected_norm):
        return False
    if expected_norm == actual_norm:
        return True
    expected_words = set(visible_keywords(expected_norm))
    actual_words = set(visible_keywords(actual_norm))
    return bool(expected_words and expected_words <= actual_words)


def field_witness_owner_activation_errors(
    path: Path,
    text: str,
    source: str,
    target: str,
    records: list[ActRecord],
) -> list[str]:
    if not records:
        return []
    payload, parse_error = field_witness_object(text)
    if parse_error:
        return [f"{path}: {parse_error}"]
    assert payload is not None
    raw_activations = payload.get("owner_activations")
    if not isinstance(raw_activations, list):
        return [f"{path}: field_witness.owner_activations must mirror compact ACT records"]

    errors: list[str] = []
    activations = [item for item in raw_activations if isinstance(item, dict)]
    if len(activations) != len(raw_activations):
        errors.append(f"{path}: field_witness.owner_activations entries must be JSON objects")
    source_candidates = {
        graph_burden_id(source),
        graph_burden_id(f"MRP({source})"),
        source,
        f"MRP({source})",
    }
    for record in records:
        record_family = strict_owner_family(record.owner)
        record_delta = record_delta_value(record)
        matching_items = [
            item
            for item in activations
            if graph_submove_id(item.get("body_ref")) == graph_submove_id(record.body_ref)
            and graph_burden_id(item.get("source")) in source_candidates
        ]
        if not matching_items:
            errors.append(
                f"{path}: field_witness.owner_activations missing mirror for {record.body_ref} from MRP({source})"
            )
            continue
        matched = False
        item_failures: list[str] = []
        for item in matching_items:
            item_owner = str(item.get("owner", "")).strip()
            item_family = strict_owner_family(item_owner)
            item_operation = str(item.get("operation", "")).strip()
            item_delta = str(item.get("delta", "")).strip()
            item_land_target = activation_land_target(item.get("land"))
            item_target = str(item.get("target", "")).strip()
            local_errors: list[str] = []
            self_claims = sorted(UNTRUSTED_ACTIVATION_SELF_CLAIMS.intersection(item))
            if self_claims:
                local_errors.append(
                    "model-authored activation verification fields are not proof: "
                    + ", ".join(self_claims)
                )
            if not item_family:
                local_errors.append("owner is not catalogue-backed")
            elif record_family and item_family != record_family:
                local_errors.append(f"owner {item_owner!r} does not agree with ACT owner {record.owner!r}")
            if GENERIC_ACT_VALUE_RE.fullmatch(item_operation) or item_operation != record.operation:
                local_errors.append("operation does not match ACT operation")
            if not activation_pressure_matches(record.pi, item.get("pressure")):
                local_errors.append("pressure does not match ACT pi target")
            if graph_normalized_text(item_delta) != graph_normalized_text(record_delta):
                local_errors.append("delta does not match ACT Delta field")
            if item_target and graph_burden_id(item_target) != graph_burden_id(target):
                local_errors.append(f"target does not point to {target}")
            if graph_burden_id(item_land_target) != graph_burden_id(target):
                local_errors.append(f"land does not point to Land({target})")
            if not local_errors:
                matched = True
                break
            item_failures.extend(local_errors)
        if not matched:
            errors.append(
                f"{path}: field_witness.owner_activations mirror for {record.body_ref} disagrees with ACT: "
                f"{'; '.join(dict.fromkeys(item_failures))}"
            )
    return errors


def closure_owner_activation_errors(path: Path, text: str, records: list[ActRecord]) -> list[str]:
    if not records:
        return []
    section = closure_witness_section(text)
    if not section:
        return [f"{path}: Closure/Reconstruction Witness must mirror ACT owner activations"]
    if not re.search(r"(?im)^\s*[-*]?\s*Owner activations\s*:", section):
        return [f"{path}: Closure/Reconstruction Witness missing Owner activations ledger"]
    closure_records, parse_errors = parse_act_records(section)
    errors = [f"{path}: closure witness {message}" for message in parse_errors]
    closure_record_lines = {record.record for record in closure_records}
    for record in records:
        if record.record not in closure_record_lines:
            errors.append(f"{path}: Closure/Reconstruction Witness missing ACT mirror for {record.body_ref}")
    return errors


def submove_block_ref_owner(block: str) -> tuple[str, str]:
    heading = next((line.strip() for line in block.splitlines() if line.strip()), "")
    match = re.search(
        rf"(?P<ref>{SUBMOVE_REF})\s*\[(?P<owner>[A-Za-z][A-Za-z0-9_.\-/]*)\]",
        heading,
    )
    return (match.group("ref"), match.group("owner")) if match else ("", "")


def submove_block_index(section: str, target: str) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for block in complete_owner_submove_blocks(section, target):
        ref, _owner = submove_block_ref_owner(block)
        if ref:
            index.setdefault(ref, []).append(block)
    return index


def land_targets(value: str) -> list[str]:
    return re.findall(rf"Land\(({TOKEN})\)", value)


def section_has_real_land(section: str, target: str) -> bool:
    return bool(re.search(rf"(?im)^\s*(?:Land|HOLD)\({re.escape(target)}\)\s*:", section))


def contribution_names_land(block: str, target: str) -> bool:
    return bool(
        re.search(rf"(?im)^\s*-?\s*Contribution-to-Land\({re.escape(target)}\)\s*:", block)
        or re.search(rf"(?i)\bLand\({re.escape(target)}\)\b", contribution_body(block))
    )


def visible_keywords(value: str) -> list[str]:
    stop = {
        "after",
        "before",
        "body",
        "burden",
        "claim",
        "delta",
        "generic",
        "land",
        "local",
        "move",
        "operation",
        "owner",
        "pressure",
        "result",
        "route",
        "state",
        "target",
        "that",
        "this",
        "with",
    }
    normalized = re.sub(r"[-_/]", " ", value.lower())
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9']{3,}", normalized)
    return [word for word in words if word not in stop]


def pressure_visible_in_body(pressure: str, block: str) -> bool:
    if GENERIC_ACT_VALUE_RE.fullmatch(pressure):
        return False
    keywords = visible_keywords(pressure)
    if not keywords:
        return False
    normalized_block = re.sub(r"[-_/]", " ", block.lower())
    body_words = set(re.findall(r"[A-Za-z0-9][A-Za-z0-9']{3,}", normalized_block))
    hits = sum(1 for keyword in keywords if keyword in body_words)
    return hits >= min(len(keywords), 2)


def compact_record_shape(record: ActRecord) -> bool:
    if len(record.record) > 420:
        return False
    if sentence_count(record.pi) > 1 or sentence_count(record.delta_result) > 1:
        return False
    return True


def source_owned_operation_errors(record: ActRecord, family: str, block: str) -> list[str]:
    allowed = SOURCE_OWNED_ACT_OPERATIONS.get(family)
    if not allowed:
        return []
    operation = record.operation.strip()
    operation_key = operation.lower()
    if operation_key not in allowed:
        registered = ", ".join(sorted(allowed))
        return [
            f"ACT {record.submove_ref} operation {operation!r} is not a registered source-owned "
            f"operation for {record.owner!r}; expected one of: {registered}"
        ]
    if not allowed[operation_key].search(operation_payload(block)):
        return [
            f"ACT {record.submove_ref} operation {operation!r} is not performed in the dereferenced body"
        ]
    return []


def operation_payload(block: str) -> str:
    return " ".join(
        value
        for value in (
            field_body(block, "Target"),
            field_body_any(block, ("Operation", "What it does")),
            field_body_any(block, ("Result", "Result/state-change")),
            contribution_body(block),
            submove_operation_body(block),
        )
        if value
    )


def is_mrp_operation_shaped_submove(block: str) -> bool:
    target = field_body(block, "Target")
    operation = field_body_any(block, ("Operation", "What it does"))
    result = field_body_any(block, ("Result", "Result/state-change"))
    contribution = contribution_body(block)
    if not (target and operation and result and contribution):
        return False
    if not target_pressure_identifiable(target):
        return False
    if not contribution_explains_land(contribution):
        return False
    operation_body = submove_operation_body(block)
    if not operation_body:
        return False
    operation_text = " ".join((operation, operation_body))
    operation_scope = " ".join((operation_text, result, contribution))
    combined = " ".join((target, operation_text, result, contribution))
    owner = submove_owner(block)
    owner_performed = owner_specific_operation_performed(owner, operation_scope)
    if not (OPERATION_MECHANISM_RE.search(combined) or owner_performed):
        return False
    semantic_categories = sum(
        1
        for pattern in (OPERATION_SCOPE_RE, OPERATION_TEST_RE, OPERATION_FAILURE_RE)
        if pattern.search(combined)
    )
    if semantic_categories < 2 and not owner_performed:
        return False
    heading = next((line.strip() for line in block.splitlines() if line.strip()), "")
    if not OPERATION_ACTION_RE.search(f"{heading} {operation_text}"):
        return False
    if not owner_performed:
        return False
    if not STATE_CHANGE_RE.search(" ".join((result, contribution))):
        return False
    if GENERIC_CONTRIBUTION_RE.fullmatch(contribution.strip()):
        return False
    if not operation_acts_on_pressure(target, operation_text):
        return False
    if not operation_body_has_state_delta(operation_body, result, contribution):
        return False
    if is_label_like_submove(block):
        return False
    return True


def is_reconstructible_owner_operation(block: str) -> bool:
    if not is_mrp_operation_shaped_submove(block):
        return False
    family = strict_owner_family(submove_owner(block))
    payload = operation_payload(block)
    if family == "M1":
        return bool(M1_RECONSTRUCTIBLE_RE.search(payload))
    if family == "P7":
        signals = sum(
            bool(pattern.search(payload))
            for pattern in (P7_STOP_SCOPE_RE, P7_REOPEN_RE, P7_HELD_ROUTE_RE)
        )
        return signals >= 2
    return True


def is_reconstructible_for_act_family(family: str, block: str) -> bool:
    if not is_mrp_operation_shaped_submove(block):
        return False
    payload = operation_payload(block)
    if not owner_specific_operation_performed(FAMILY_OPERATION_OWNER.get(family, family), payload):
        return False
    if family == "M1":
        return bool(M1_RECONSTRUCTIBLE_RE.search(payload))
    if family == "P7":
        signals = sum(
            bool(pattern.search(payload))
            for pattern in (P7_STOP_SCOPE_RE, P7_REOPEN_RE, P7_HELD_ROUTE_RE)
        )
        return signals >= 2
    return True


def validate_act_record(
    record: ActRecord,
    target: str,
    route_owners: set[str],
    blocks_by_ref: dict[str, list[str]],
    section: str,
) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    valid_families: set[str] = set()
    record_family = strict_owner_family(record.owner)
    canonical = canonical_activation_from_record(record)
    rendered = render_act(canonical)
    if record.record != rendered:
        errors.append(
            f"ACT {record.submove_ref} does not match checker-rendered canonical ACT line"
        )
    if not record_family:
        errors.append(f"ACT owner {record.owner!r} is not a catalogue-backed owner alias")
    if not compact_record_shape(record):
        errors.append(f"ACT {record.submove_ref} must stay compact; put prose in the dereferenced body")
    if GENERIC_ACT_VALUE_RE.fullmatch(record.operation):
        errors.append(f"ACT {record.submove_ref} uses a generic operation alias")
    if record.submove_ref != record.body_ref:
        errors.append(
            f"ACT {record.submove_ref} body_ref must name the exact same submove token, not {record.body_ref!r}"
        )
    if not re.fullmatch(SUBMOVE_REF, record.body_ref):
        errors.append(f"ACT {record.submove_ref} body_ref {record.body_ref!r} is not a concrete submove reference")
    blocks = blocks_by_ref.get(record.body_ref, [])
    if len(blocks) != 1:
        errors.append(f"ACT {record.submove_ref} body_ref must dereference to exactly one Layer B submove block")
        return valid_families, errors

    block = blocks[0]
    _block_ref, block_owner = submove_block_ref_owner(block)
    block_family = strict_owner_family(block_owner)
    if record_family and block_family != record_family:
        errors.append(
            f"ACT {record.submove_ref} owner {record.owner!r} does not agree with submove owner {block_owner!r}"
        )
    if record_family and route_owners and record_family not in route_owners:
        errors.append(f"ACT {record.submove_ref} owner {record.owner!r} is not in the matched owner/TTP route")
    if not pressure_visible_in_body(record.pi, block):
        errors.append(f"ACT {record.submove_ref} pi target is missing, generic, or not visible in dereferenced body")
    if record_family:
        errors.extend(source_owned_operation_errors(record, record_family, block))
    if not DELTA_NAME_RE.fullmatch(record.delta):
        errors.append(f"ACT {record.submove_ref} Delta field must name Delta burden state or Delta-kappa")
    if GENERIC_ACT_VALUE_RE.fullmatch(record.delta_result) or not STATE_CHANGE_RE.search(record.delta_result):
        errors.append(f"ACT {record.submove_ref} Delta result must name a concrete burden-local state change")
    land_tokens = land_targets(record.land)
    if target not in land_tokens:
        errors.append(f"ACT {record.submove_ref} Land clause must point to Land({target})")
    if not section_has_real_land(section, target):
        errors.append(f"ACT {record.submove_ref} Land clause is fake; no real Land({target})/HOLD({target}) line exists")
    if not contribution_names_land(block, target):
        errors.append(f"ACT {record.submove_ref} dereferenced body lacks Contribution-to-Land({target})")

    result = field_body_any(block, ("Result", "Result/state-change"))
    contribution = contribution_body(block)
    state_surface = " ".join((record.delta_result, result, contribution, submove_operation_body(block)))
    if not STATE_CHANGE_RE.search(state_surface):
        errors.append(f"ACT {record.submove_ref} dereferenced result/contribution lacks burden-local state change")
    if record_family and not is_reconstructible_for_act_family(record_family, block):
        errors.append(f"ACT {record.submove_ref} record alone does not pass; dereferenced body is not owner-specific")

    if not errors and record_family:
        valid_families.add(record_family)
    return valid_families, errors


def act_activation_errors(
    path: Path,
    text: str,
    section: str,
    source: str,
    target: str,
    route_owners: set[str],
    route_kind: str,
) -> list[str]:
    errors: list[str] = []
    records, parse_errors = parse_act_records(section)
    errors.extend(f"{path}: {message}" for message in parse_errors)
    if route_owners and not records:
        errors.append(
            f"{path}: {route_kind} {target} missing ACT activation records for matched owner route"
        )
        return errors
    if not records:
        return errors

    blocks_by_ref = submove_block_index(section, target)
    valid_families: set[str] = set()
    for record in records:
        families, found = validate_act_record(record, target, route_owners, blocks_by_ref, section)
        valid_families.update(families)
        errors.extend(f"{path}: {message}" for message in found)

    errors.extend(closure_owner_activation_errors(path, text, records))
    errors.extend(field_witness_owner_activation_errors(path, text, source, target, records))

    missing = route_owners - valid_families
    if missing:
        errors.append(
            f"{path}: {route_kind} {target} ACT records did not prove routed owners: "
            f"{', '.join(sorted(missing))}"
        )
    return errors


def owner_activation_errors(
    path: Path,
    text: str,
    section: str,
    source: str,
    target: str,
    route_scope: str,
    route_kind: str,
    *,
    require_route: bool,
) -> list[str]:
    errors: list[str] = []
    has_route = has_matched_owner_route(route_scope)
    if require_route and not has_route:
        errors.append(f"{path}: MRP {route_kind} did not route {target} to matched source-owned TTPs")
    route_owners = matched_owner_route_tokens(route_scope)
    complete_blocks = complete_owner_submove_blocks(section, target)
    submove_owner_tokens = {
        normalized_owner_token(owner)
        for owner in (submove_owner(block) for block in complete_blocks)
        if owner
    }
    missing_route_owners = route_owners - submove_owner_tokens
    if route_owners and missing_route_owners:
        errors.append(
            f"{path}: {route_kind} route owners not activated in Layer B submoves for {target}: "
            f"{', '.join(sorted(missing_route_owners))}"
        )
    if route_owners and not complete_blocks:
        errors.append(
            f"{path}: {route_kind} {target} has a matched owner route but no complete owner-bearing operation body"
        )
    if route_owners:
        errors.extend(act_activation_errors(path, text, section, source, target, route_owners, route_kind))
    failed_owners = sorted(
        {
            normalized_owner_token(submove_owner(block))
            for block in complete_blocks
            if submove_owner(block) and not is_reconstructible_owner_operation(block)
        }
    )
    if failed_owners:
        errors.append(
            f"{path}: {route_kind} {target} names owner codes but does not execute owner-specific operations: "
            f"{', '.join(failed_owners)}"
        )
        errors.append(
            f"{path}: Code lookup is not owner activation; Land({target}) requires mechanism/action/state-delta operation mass"
        )
    return errors


def generated_node_has_post_land_mrp(section: str, target: str) -> bool:
    return bool(
        re.search(
            rf"(?is)(?:Land|HOLD)\({re.escape(target)}\)\s*:.*?\[Mid-Reread Pressure\].*?"
            rf"^\s*Target\s*:\s*{re.escape(target)}\b",
            section,
            re.MULTILINE,
        )
    )


def generated_node_has_terminal_stop(section: str, target: str) -> bool:
    return bool(
        re.search(
            rf"(?is)(?:Land|HOLD)\({re.escape(target)}\)\s*:.*?^\s*Route\s*:\s*STOP\b",
            section,
            re.MULTILINE,
        )
    )


def notation_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    public_text = re.split(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\s*$", text, maxsplit=1)[0]
    for label, pattern in BAD_PUBLIC_NOTATION:
        if pattern.search(public_text):
            errors.append(f"{path}: public generated-burden fixture uses forbidden {label}")
    return errors


def generated_burden_errors(path: Path, text: str, block: MrpBlock, *, enforce_public_notation: bool) -> list[str]:
    errors: list[str] = []
    source = block_target(block)
    edges = block_edges(block)
    if not source:
        return [f"{path}: generated_burden_instantiation target must name canonical burden"]
    if not edges:
        return [f"{path}: generated_burden_instantiation requires graph edge"]
    edge = edges[0]
    target = edge[1]
    if target in initial_burdens(text):
        errors.append(f"{path}: {target} is already in Initial burden set; classify as held_burden_activation")
    if target in held_burdens(text):
        errors.append(f"{path}: {target} is already in held inventory; classify as held_burden_activation")
    if block.route not in {"RECURSE", "HOLD"}:
        errors.append(f"{path}: generated_burden_instantiation must route RECURSE or HOLD")
    if block.preemption_basis == "none":
        errors.append(f"{path}: generated_burden_instantiation requires graph/commitment/framework-bound basis")
    if not block.route_gradient:
        errors.append(f"{path}: generated_burden_instantiation requires Route-gradient")
    elif not re.search(r"(?i)\b(?:generated|new|newly|resultant|not fully present|not present|MRP)\b", block.route_gradient):
        errors.append(f"{path}: generated_burden_instantiation Route-gradient must explain the newly surfaced resultant")
    elif not re.search(r"(?i)(?:Δ|Delta|xi|ξ|Omega|Ω|concealment|framework|dependency|burden-gradient|translation tribunal|admissibility|doctrine|mystery|immunity|shield|recoil|source-worldview|del[- ]dot|D3|D6)", block.route_gradient):
        errors.append(
            f"{path}: generated_burden_instantiation Route-gradient must name a post-Land field-pressure source, not only an imagined reply"
        )
    if enforce_public_notation and (
        not re.fullmatch(CANONICAL_TOKEN, source) or not re.fullmatch(CANONICAL_TOKEN, target)
    ):
        errors.append(f"{path}: generated graph edge must use canonical burden notation")
    heading = generated_heading(text, source, target)
    if not heading:
        errors.append(f"{path}: generated burden {target} must appear as a real node with [generated-by: MRP({source})]")
        return errors
    section = generated_node_section(text, heading, target)
    route_scope = block.body + "\n" + owner_activation_route_section(section)
    errors.extend(
        owner_activation_errors(
            path,
            text,
            section,
            source,
            target,
            route_scope,
            "generated burden",
            require_route=True,
        )
    )
    if not re.search(r"(?im)^\s*(?:#{1,6}\s*)?Layer A\b", section):
        errors.append(f"{path}: generated burden {target} missing Layer A accounting")
    if not re.search(r"(?im)^\s*(?:#{1,6}\s*)?Layer B\s*[-—]\s*Governed Operation Body\b", section):
        errors.append(f"{path}: generated burden {target} missing Layer B governed operation body")
    owners = owner_submoves(section, target)
    complete_submoves = complete_owner_submoves(section, target)
    if len(complete_submoves) < 2:
        errors.append(
            f"{path}: MRP({source}) recorded generated_burden_instantiation but no corresponding generated {target} with Layer B treatment was found in the output"
        )
        errors.append(
            f"{path}: generated burden {target} needs at least two owner-bearing submoves with Target/Operation/Result/Contribution-to-Land"
        )
    if owners and set(owners).issubset(COMMON_EXAMPLE_OWNERS):
        errors.append(f"{path}: generated burden {target} appears hardcoded to FPD/M1/M8 examples")
    if not re.search(rf"(?im)^\s*(?:Land|HOLD)\({re.escape(target)}\)\s*:", section):
        errors.append(f"{path}: generated burden {target} missing Land({target}) or HOLD({target})")
    elif not generated_node_has_post_land_mrp(section, target) and not generated_node_has_terminal_stop(section, target):
        errors.append(f"{path}: generated burden {target} missing post-land reread/MRP or explicit terminal STOP")
    closure_tail_text = closure_tail(text)
    if target not in closure_tail_text or f"MRP({source})" not in closure_tail_text:
        errors.append(f"{path}: closure witness must record generated node and MRP provenance")
    if not MRP_RESULTANT_RE.search(closure_tail_text):
        errors.append(f"{path}: closure witness missing MRP resultants ledger")
    return errors


def held_activation_errors(path: Path, text: str, block: MrpBlock) -> list[str]:
    errors: list[str] = []
    edges = block_edges(block)
    if not edges:
        errors.append(f"{path}: held_burden_activation requires graph provenance edge")
        return errors
    target = edges[0][1]
    if target not in initial_or_held_burdens(text):
        errors.append(f"{path}: held_burden_activation target {target} must be in Initial burden set or held inventory")
    if re.search(rf"{re.escape(target)}\s*\[generated-by:", text):
        errors.append(f"{path}: held_burden_activation target {target} is marked generated; classify the route as generated_burden_instantiation or remove the marker")
    if block.route not in {"RECURSE", "HOLD"}:
        errors.append(f"{path}: held_burden_activation must route RECURSE or HOLD")
    if not block.route_gradient:
        errors.append(f"{path}: held_burden_activation requires Route-gradient")
    elif not (
        re.search(r"(?i)\b(?:held|initial|already[- ]inventoried|already named|H\b)", block.route_gradient)
        or target in burden_tokens(block.route_gradient)
    ):
        errors.append(f"{path}: held_burden_activation Route-gradient must point to an already-held/initial burden")
    section = burden_node_section(text, target)
    if section:
        route_scope = block.body + "\n" + owner_activation_route_section(section)
        errors.extend(
            owner_activation_errors(
                path,
                text,
                section,
                block_target(block),
                target,
                route_scope,
                "held burden activation",
                require_route=True,
            )
        )
    return errors


def generated_marker_consistency_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for marker in re.finditer(rf"(?P<target>{TOKEN})\s*\[generated-by:\s*MRP\((?P<src>{TOKEN})\)\]", text):
        source = marker.group("src")
        target = marker.group("target")
        key = (source, target)
        if key in seen:
            continue
        seen.add(key)
        tail = closure_tail(text)
        closure_match = re.search(
            rf"MRP\({re.escape(source)}\)\s*:\s*type=generated_burden_instantiation;[^\n]*graph=[^;\n]*{re.escape(source)}\s*(?:→|->)\s*{re.escape(target)}",
            tail,
            re.IGNORECASE,
        )
        if not closure_match:
            errors.append(f"{path}: generated marker {target} [generated-by: MRP({source})] requires matching closure MRP generated resultant")
    return errors


def block_route_type_errors(path: Path, text: str, block: MrpBlock, *, enforce_public_notation: bool) -> list[str]:
    route_type = block.route_result_type.strip()
    if not route_type:
        return [f"{path}: MRP block missing MRP route result type"]
    if route_type not in ROUTE_TYPES:
        return [f"{path}: invalid MRP route result type {route_type!r}"]
    if route_type == "generated_burden_instantiation":
        return generated_burden_errors(path, text, block, enforce_public_notation=enforce_public_notation)
    if route_type == "held_burden_activation":
        return held_activation_errors(path, text, block)
    if route_type == "no_new_resultant" and EDGE_RE.search(block.graph_delta):
        return [f"{path}: no_new_resultant must not create graph edge"]
    if route_type == "loopbreak" and block.route != "LoopBreak(∇×T)":
        return [f"{path}: loopbreak route result type requires Route: LoopBreak(∇×T)"]
    if route_type == "hold_partial" and block.route != "HOLD":
        return [f"{path}: hold_partial route result type requires Route: HOLD"]
    return []


def closure_tail(text: str) -> str:
    match = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:Closure/Reconstruction Witness|Held-node Accounting|Held-node accounting|Closure Audit)\b",
        text,
    )
    return text[match.start() :] if match else ""


def closure_resultant_errors(path: Path, text: str) -> list[str]:
    """Validate held/generated route typing in the closure witness ledger.

    Some smoke outputs format compact MRP blocks with Markdown or omit visible route-type
    lines, but still print the machine-facing `MRP resultants` ledger. The ledger must
    obey the same lineage rule: an already-initialized node is held, not generated.
    """
    tail = closure_tail(text)
    if not tail or not MRP_RESULTANT_RE.search(tail):
        return []

    errors: list[str] = []
    initial = initial_burdens(text)
    held = held_burdens(text)
    initial_or_held = initial | held
    for match in MRP_CLOSURE_RESULTANT_RE.finditer(tail):
        source = match.group("src")
        route_type = match.group("route_type")
        graph = " ".join(match.group("graph").split())
        route = match.group("route")
        edges = [(m.group("src"), m.group("dst")) for m in EDGE_RE.finditer(graph)]
        label = f"{path}: closure MRP({source})"

        if route_type not in ROUTE_TYPES:
            errors.append(f"{label}: invalid MRP resultant type {route_type!r}")
            continue
        if route_type == "generated_burden_instantiation":
            if not edges:
                errors.append(f"{label}: generated_burden_instantiation requires graph edge")
                continue
            target = edges[0][1]
            if target in initial:
                errors.append(f"{label}: {target} is already in Initial burden set; classify as held_burden_activation")
            if target in held:
                errors.append(f"{label}: {target} is already in held inventory; classify as held_burden_activation")
            if route not in {"RECURSE", "HOLD"}:
                errors.append(f"{label}: generated_burden_instantiation must route RECURSE or HOLD")
        elif route_type == "held_burden_activation":
            if not edges:
                errors.append(f"{label}: held_burden_activation requires graph provenance edge")
                continue
            target = edges[0][1]
            if target not in initial_or_held:
                errors.append(f"{label}: held_burden_activation target {target} must be in Initial burden set or held inventory")
            if route not in {"RECURSE", "HOLD"}:
                errors.append(f"{label}: held_burden_activation must route RECURSE or HOLD")
        elif route_type == "no_new_resultant" and edges:
            errors.append(f"{label}: no_new_resultant must not create graph edge")
        elif route_type == "loopbreak" and route != "LoopBreak(∇×T)":
            errors.append(f"{label}: loopbreak route result type requires route LoopBreak(∇×T)")
        elif route_type == "hold_partial" and route != "HOLD":
            errors.append(f"{label}: hold_partial route result type requires route HOLD")
    return errors


def check_text(path: Path, text: str, *, enforce_public_notation: bool = True) -> list[str]:
    errors = notation_errors(path, text) if enforce_public_notation else []
    blocks = parse_mrps(text)
    if not blocks:
        errors.append(f"{path}: missing [Mid-Reread Pressure] block")
    route_types: set[str] = set()
    for block in blocks:
        if block.route_result_type:
            route_types.add(block.route_result_type)
        errors.extend(mrp_refutation_content_errors(block, f"{path}: MRP block"))
        errors.extend(block_route_type_errors(path, text, block, enforce_public_notation=enforce_public_notation))
    errors.extend(formal_reread_state_errors(path, text, blocks))
    errors.extend(field_witness_mrp_resultant_errors(path, text, blocks))
    errors.extend(generated_marker_consistency_errors(path, text))
    errors.extend(closure_resultant_errors(path, text))
    if path.parent.name == "valid" and path.name.startswith("generated-"):
        if "generated_burden_instantiation" not in route_types:
            errors.append(f"{path}: generated fixture must prove generated_burden_instantiation")
    if path.parent.name == "valid" and path.name.startswith("held-"):
        if "held_burden_activation" not in route_types:
            errors.append(f"{path}: held fixture must prove held_burden_activation")
    return errors


def candidate_review_warnings(path: Path, text: str) -> list[str]:
    """Return non-failing review signals for hard cases that never generate.

    This is intentionally advisory. Some exact user smokes correctly contain only
    input-anchored held burdens, but a long named-worldview route with only held
    activations should be surfaced for human review so over-inventory cannot hide
    missing generated-MRP behavior.
    """
    blocks = parse_mrps(text)
    if not blocks:
        return []
    route_types = {block.route_result_type for block in blocks if block.route_result_type}
    if "generated_burden_instantiation" in route_types:
        return []
    initial = initial_burdens(text)
    hard_theological = re.search(
        r"(?i)\b(?:field\s*:\s*(?:NAMED WORLDVIEW|MIXED NOETIC FIELD)|"
        r"Trinitarian|theological|authority frame\s*:\s*LIVE|source-worldview|named-worldview)\b",
        text,
    )
    if len(initial) >= 4 and hard_theological and route_types <= {"held_burden_activation", "no_new_resultant"}:
        return [
            f"{path}: Hard-compound case produced only held_burden_activation across all MRP cycles. Review whether post-land escape routes should have generated a new burden."
        ]
    return []


def required_hard_case_errors(path: Path, text: str) -> list[str]:
    """Fail reopened hard-theological smoke gates when B_MRP is empty.

    This is intentionally scoped to live/output files named as the reopened
    acceptance vehicles. Fixture-only checks still prove grammar; these output
    gates prove runtime behavior in the named hard theological cases.
    """
    stem = path.stem.lower()
    required = any(name in stem for name in ("trinitarian", "tst", "khaybar"))
    if not required:
        return []
    if "generated_burden_instantiation" in text and "[generated-by: MRP(" in text:
        return []
    return [
        f"{path}: required hard theological smoke must prove non-empty B_MRP with generated_burden_instantiation"
    ]


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def expand_output_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        raw = str(path)
        if any(char in raw for char in "*?["):
            matches = sorted(glob.glob(raw))
            if matches:
                expanded.extend(Path(match) for match in matches)
                continue
        expanded.append(path)
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("tests/mrp-generated-burden"))
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    parser.add_argument(
        "--show-advisories",
        action="store_true",
        help="print non-failing human-review advisories such as held-only hard-compound review signals",
    )
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0
    for path in valid:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
            warnings.extend(candidate_review_warnings(path, read_text(path)))
    for path in invalid:
        found = check_text(path, read_text(path))
        if not found:
            errors.append(f"{path}: expected-invalid generated-burden fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in expand_output_paths(args.outputs):
        if not path.exists():
            errors.append(f"{path}: output path not found")
            continue
        text = read_text(path)
        found = check_text(path, text, enforce_public_notation=False)
        found.extend(required_hard_case_errors(path, text))
        if found:
            errors.extend(found)
        else:
            output_checked += 1
            warnings.extend(candidate_review_warnings(path, text))

    if errors:
        print("MRP generated-burden check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("MRP generated-burden check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    if args.show_advisories and warnings:
        print("Advisories:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
