#!/usr/bin/env python3
"""Schema-light graph-completeness capstone checker.

This is the B.1 boundary checker. It composes the existing source-owned
validators and computes a collapse-positive condition report without trusting
model-authored booleans. The formal B.2 collapse-certificate schema is a later
lane.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from closure_witness_lib import (
    BURDEN_ID_RE,
    extract_embedded_field_witness,
    extract_field_witness,
    field_witness_ledger,
    field_witness_mrp_resultants,
    normalize_burden_id,
    parse_closure_witness,
    status_head,
)
from check_field_witness_convergence import (
    CLOSED_TERMINAL_STATES,
    LIVE_TERMINAL_STATES,
    canonical_register,
    convergence_errors,
    coverage,
    diagnostic_status,
    generation_depth_errors,
    graph_nodes,
    terminal_payloads,
)
from check_formal_reread_state_semantics import formal_semantics_errors
from check_formal_reread_state_semantics import normalized_loopbreak_ground
from check_collapse_certificate_schema import REGISTERS as CERTIFICATE_REGISTERS
from check_collapse_certificate_schema import certificate_errors
from check_mrp_generated_burden import (
    GENERIC_ACT_VALUE_RE,
    activation_land_target,
    activation_pressure_matches,
    contribution_names_land,
    graph_burden_id,
    graph_normalized_text,
    graph_submove_id,
    parse_act_records,
    section_has_real_land,
    strict_owner_family,
    submove_block_index,
    submove_block_ref_owner,
    check_text as mrp_generated_errors,
    visible_keywords,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "graph-completeness"
FORMALISM_NEUTRAL_INVALID_DIR = ROOT / "tests" / "formalism-path-neutral" / "invalid"
CHECKER_VERSION = "check_graph_completeness.py:b1-schema-light"
DEFAULT_SKILL_VERSION = "0.4.3.0"
ESCAPE_ROUTE_TYPES = {
    "closure-boundary-immunity",
    "proof-carousel",
    "total-system-exhaustion",
    "doubt-churn",
    "moral-tribunal",
    "authority-order-recoil",
    "hidden-framework-recoil",
    "restoration-recoil",
}
ESCAPE_ROUTE_DISPOSITIONS = {
    "generated",
    "generated-burden",
    "generated-burden-instantiation",
    "held",
    "hold",
    "partial",
    "recurse",
    "loopbreak",
    "landed",
    "non-load-bearing",
    "non-load-bearing-proof",
}
MRP_TRACKS = {"primary", "restoration"}
DIVERGENCE_POSITIVE_STATES = {"non-neutral", "positive"}
CURL_LIVE_STATES = {"non-null", "held", "unresolved"}
NO_NEW_RESULTANT_TYPES = {"no-new-resultant", "none", "stable"}
EMPTY_B_LIVE_STATES = {"empty", "none", "[]", "0"}
RESTORATION_RECOIL_SUBTYPE_OWNERS = {
    "fitrah-recoil": {"P1", "R2"},
    "authority-return-recoil": {"SOURCE"},
    "worship-frame-recoil": {"P1", "R2", "P7"},
    "scope-protest": {"P7", "M8"},
    "uptake-guarantee-recoil": {"P7"},
}
RESTORATION_RECOIL_OWNER_OPTIONAL_DISPOSITIONS = {
    "held",
    "hold",
    "partial",
    "loopbreak",
    "non-load-bearing",
    "non-load-bearing-proof",
}
OWNER_FAMILY_TOKENS = {
    "SOURCE",
    "FPD",
    "M1",
    "M1-P",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "M7",
    "M8",
    "M9",
    "P1",
    "P2",
    "P3",
    "P4",
    "P5",
    "P6",
    "P7",
    "R1",
    "R2",
    "R3",
}
FITRAH_ORIENTATION_RE = re.compile(r"(?i)\b(?:fitrah|fiṭrah|fitri|fiṭrī|tawhid|tawḥīd|N_fiṭrī|N_fitri)\b")
AQL_ORIENTATION_RE = re.compile(
    r"(?i)\b(?:aql|ʿaql|sound reason|sarih|ṣarīḥ|aqli|reason orientation|"
    r"reason is hono[u]?red|reason serve[s]? truth|reason as a created capacity)\b"
)
ESCAPE_STATE_EVIDENCE_RE = re.compile(
    r"(?i)(?:\bDelta\b|Δ|R\(H,\s*(?:Delta|Δ)\)|route-gradient|∇|divergence|curl|"
    r"register|Reg\b|B_live|dependency|graph|commitment|framework|post[- ]Land|"
    r"after Land|landed delta|reread|field pressure)"
)
PREVOICED_ONLY_RE = re.compile(
    r"(?i)\b(?:likely objection|pre[- ]?voiced|user might say|anticipated reply|"
    r"stock response|possible objection|someone might say|would object)\b"
)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalized_input_text(text: str) -> str:
    """Canonical B.4 D0 normalization before certificate fingerprinting."""
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\s+", " ", text).strip().lower()


def input_fingerprint_for_text(text: str) -> str:
    normalized = normalized_input_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def input_fingerprint_for_path(path: Path) -> str:
    return input_fingerprint_for_text(read_text(path))


def expand_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        raw = str(path)
        if any(char in raw for char in "*?["):
            matches = sorted(Path(match) for match in glob.glob(raw))
            expanded.extend(matches or [path])
        else:
            expanded.append(path)
    return expanded


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def list_values(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def formal_reread_states(field_witness: dict[str, Any]) -> list[dict[str, Any]]:
    raw = field_witness.get("formal_reread_states")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def normalized_token(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", "-")


def normalized_owner_family_token(value: Any) -> str:
    raw = str(value or "").strip().strip("[]")
    if not raw:
        return ""
    family = strict_owner_family(raw)
    if family:
        return family
    token = raw.upper().replace("_", "-").replace(" ", "-")
    if token in OWNER_FAMILY_TOKENS:
        return token
    return token


def route_owner_families(route: dict[str, Any], state: dict[str, Any] | None = None) -> set[str]:
    families: set[str] = set()
    for source in (route, state or {}):
        for key in ("owner", "owner_id", "owner-id", "owner_family", "owner-family"):
            token = normalized_owner_family_token(source.get(key))
            if token:
                families.add(token)
        for key in (
            "owners",
            "owner_ids",
            "owner-ids",
            "owner_families",
            "owner-families",
            "owner_route",
            "owner-route",
        ):
            raw = source.get(key)
            values = raw if isinstance(raw, list) else re.split(r"[,;/+]|\s+and\s+", str(raw or ""))
            for value in values:
                token = normalized_owner_family_token(value)
                if token:
                    families.add(token)
    return families


ASCII_TO_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def burden_aliases(value: str) -> list[str]:
    aliases = [value]
    match = re.fullmatch(r"B(\d+)", value)
    if match:
        aliases.append(f"{match.group(1).translate(ASCII_TO_SUP)}B")
    return unique(aliases)


def mrp_errors_for_burden(errors: list[str], burden: str) -> list[str]:
    aliases = [alias for alias in burden_aliases(normalize_burden_id(burden)) if alias]
    matched: list[str] = []
    for error in errors:
        surface = str(error)
        for alias in aliases:
            if re.fullmatch(r"B\d+", alias):
                if re.search(rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])", surface):
                    matched.append(error)
                    break
                continue
            if alias in surface:
                matched.append(error)
                break
    return matched


def submove_target_token(ref: str) -> str:
    text = str(ref or "").strip()
    match = re.fullmatch(r"(B\d+)(?:[_\.]\d+)", text)
    if match:
        return match.group(1)
    match = re.fullmatch(r"(?P<target>.+?)(?:[₀₁₂₃₄₅₆₇₈₉]+|[_\.]\d+)", text)
    return match.group("target") if match else ""


def public_execution_text(text: str) -> str:
    match = re.search(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\s*$", text)
    return text[: match.start()] if match else text


def section_after_heading(text: str, heading: str) -> str:
    pattern = re.compile(rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(heading)}\s*$")
    match = pattern.search(text)
    if not match:
        return ""
    next_heading = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:Restorative Response|Closing Formulation|Closure/Reconstruction Witness|field_witness|Legend)\s*$",
        text[match.end() :],
    )
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end() : end]


def restoration_orientation_present(text: str) -> bool:
    surface = "\n".join(
        (
            section_after_heading(text, "Restorative Response"),
            section_after_heading(text, "Closing Formulation"),
        )
    )
    return bool(FITRAH_ORIENTATION_RE.search(surface) and AQL_ORIENTATION_RE.search(surface))


def keywords_recoverable(label: Any, body: str, *, minimum: int = 2) -> bool:
    keywords = visible_keywords(str(label or ""))
    if not keywords:
        return False
    words = set(re.findall(r"[a-z0-9][a-z0-9']{3,}", re.sub(r"[-_/]", " ", graph_normalized_text(body).lower())))
    hits = sum(1 for keyword in keywords if keyword in words)
    return hits >= min(len(keywords), minimum)


def initial_burdens(field_witness: dict[str, Any]) -> list[str]:
    raw = coverage(field_witness).get("initial_burden_set")
    if isinstance(raw, list):
        return unique(
            normalize_burden_id(str(item))
            for item in raw
            if isinstance(item, str) and BURDEN_ID_RE.fullmatch(normalize_burden_id(item))
        )
    return field_witness_ledger(field_witness)["B_LA"]


def graph_edges(field_witness: dict[str, Any]) -> list[str]:
    graph = coverage(field_witness).get("dependency_graph")
    raw_edges = graph.get("edges") if isinstance(graph, dict) else field_witness.get("edges")
    edges: list[tuple[str, str]] = []
    if not isinstance(raw_edges, list):
        return edges
    for item in raw_edges:
        source: Any
        target: Any
        if isinstance(item, dict):
            source = item.get("from")
            target = item.get("to")
        elif isinstance(item, list) and len(item) == 2:
            source, target = item
        else:
            continue
        source_id = normalize_burden_id(str(source or ""))
        target_id = normalize_burden_id(str(target or ""))
        if BURDEN_ID_RE.fullmatch(source_id) and BURDEN_ID_RE.fullmatch(target_id):
            edges.append((source_id, target_id))
    return unique([f"{source}->{target}" for source, target in edges])


def dependency_roots(field_witness: dict[str, Any]) -> list[str]:
    graph = coverage(field_witness).get("dependency_graph")
    raw_roots = graph.get("roots") if isinstance(graph, dict) else []
    if not isinstance(raw_roots, list):
        return []
    return unique(
        normalize_burden_id(str(item))
        for item in raw_roots
        if BURDEN_ID_RE.fullmatch(normalize_burden_id(str(item)))
    )


def resultant_edges(field_witness: dict[str, Any]) -> list[str]:
    edges: list[str] = []
    for resultant in field_witness_mrp_resultants(field_witness):
        graph = str(resultant.get("graph") or "").replace("→", "->")
        for match in re.finditer(r"\b(B\d+)\b\s*->\s*\b(B\d+)\b", graph):
            source = normalize_burden_id(match.group(1))
            target = normalize_burden_id(match.group(2))
            edges.append(f"{source}->{target}")
    return unique(edges)


def terminal_state_map(field_witness: dict[str, Any]) -> dict[str, str]:
    return {
        burden: payload.get("state", "")
        for burden, payload in terminal_payloads(field_witness).items()
    }


def graph_contract_strict(path: Path) -> bool:
    try:
        return path.resolve().is_relative_to(FIXTURE_ROOT.resolve())
    except AttributeError:
        try:
            path.resolve().relative_to(FIXTURE_ROOT.resolve())
            return True
        except ValueError:
            return False


def generated_burden_tracks(field_witness: dict[str, Any]) -> dict[str, str]:
    tracks: dict[str, str] = {}
    raw = field_witness.get("generated_burdens")
    if isinstance(raw, dict):
        for raw_burden, raw_payload in raw.items():
            burden = normalize_burden_id(str(raw_burden))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            payload = raw_payload if isinstance(raw_payload, dict) else {}
            tracks[burden] = normalized_token(payload.get("track"))
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            burden = normalize_burden_id(str(item.get("id") or item.get("burden") or item.get("target") or ""))
            if BURDEN_ID_RE.fullmatch(burden):
                tracks[burden] = normalized_token(item.get("track"))

    raw_nodes = field_witness.get("nodes")
    if isinstance(raw_nodes, list):
        for item in raw_nodes:
            if not isinstance(item, dict):
                continue
            burden = normalize_burden_id(str(item.get("id") or ""))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            if str(item.get("type") or "").strip() != "generated_burden" and "generated_by" not in item:
                continue
            track = normalized_token(item.get("track"))
            if track or burden not in tracks:
                tracks[burden] = track
    return tracks


def generated_burden_sources(field_witness: dict[str, Any]) -> dict[str, str]:
    sources: dict[str, str] = {}
    raw = field_witness.get("generated_burdens")
    if isinstance(raw, dict):
        for raw_burden, raw_payload in raw.items():
            burden = normalize_burden_id(graph_burden_id(raw_burden))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            payload = raw_payload if isinstance(raw_payload, dict) else {"generated_by": raw_payload}
            source = generated_source_id(payload.get("generated_by"))
            if source:
                sources[burden] = source
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            burden = normalize_burden_id(graph_burden_id(item.get("id") or item.get("burden") or item.get("target")))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            source = generated_source_id(item.get("generated_by"))
            if source:
                sources[burden] = source

    raw_nodes = field_witness.get("nodes")
    if isinstance(raw_nodes, list):
        for item in raw_nodes:
            if not isinstance(item, dict):
                continue
            burden = normalize_burden_id(graph_burden_id(item.get("id")))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            if str(item.get("type") or "").strip() != "generated_burden" and "generated_by" not in item:
                continue
            source = generated_source_id(item.get("generated_by"))
            if source and burden not in sources:
                sources[burden] = source
    return sources


def generated_source_id(value: Any) -> str:
    match = re.search(r"(?i)\bMRP\((?P<source>[^)]+)\)", str(value or ""))
    if not match:
        return ""
    return normalize_burden_id(graph_burden_id(match.group("source")))


def state_burden_id(value: Any) -> str:
    burden = normalize_burden_id(graph_burden_id(value))
    if BURDEN_ID_RE.fullmatch(burden):
        return burden
    match = re.search(r"\bB\d+\b", str(value or ""))
    return normalize_burden_id(match.group(0)) if match else ""


def state_non_load_bearing(value: dict[str, Any]) -> bool:
    if value.get("non_load_bearing") is True or value.get("non-load-bearing") is True:
        return True
    haystack = " ".join(
        str(value.get(key) or "")
        for key in (
            "route",
            "route_gradient",
            "mrp_resultant",
            "preemption_basis",
            "basis",
            "reason",
            "post_break_reread",
        )
    )
    return bool(re.search(r"(?i)\bnon[- ]load[- ]bearing\b|\bnot load[- ]bearing\b", haystack))


def state_hold_partial_recurse(value: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(value.get(key) or "")
        for key in (
            "route",
            "route_gradient",
            "mrp_resultant",
            "preemption_basis",
            "post_break_reread",
        )
    )
    return bool(re.search(r"(?i)\b(?:HOLD|PARTIAL|RECURSE|held-with-reason|carried-RECURSE|carried-PARTIAL)\b", haystack))


def state_terminal_accounted(burden: str, terminals: dict[str, str]) -> bool:
    return terminals.get(burden, "") in CLOSED_TERMINAL_STATES | LIVE_TERMINAL_STATES


def track_contract_required(path: Path, field_witness: dict[str, Any]) -> bool:
    ledgers = field_witness_ledger(field_witness)
    if ledgers["B_MRP"]:
        return True
    cov = coverage(field_witness)
    if isinstance(cov.get("mrp_tracks"), dict):
        return True
    return bool(generated_burden_tracks(field_witness))


def restoration_generated_targets(field_witness: dict[str, Any]) -> set[str]:
    targets: set[str] = set()
    generated_dispositions = {"generated", "generated-burden", "generated-burden-instantiation"}
    for state in formal_reread_states(field_witness):
        checked = state.get("escape_routes_checked")
        if not isinstance(checked, list):
            continue
        for route in checked:
            if not isinstance(route, dict):
                continue
            route_type = normalized_token(route.get("type") or route.get("escape_route") or route.get("route_type"))
            disposition = normalized_token(route.get("disposition") or route.get("terminal") or route.get("route"))
            if route_type != "restoration-recoil" or route.get("live") is not True:
                continue
            if disposition not in generated_dispositions:
                continue
            target = normalize_burden_id(
                str(route.get("target_burden") or route.get("generated_burden") or route.get("target") or "")
            )
            if BURDEN_ID_RE.fullmatch(target):
                targets.add(target)
    return targets


def two_track_mrp_errors(path: Path, field_witness: dict[str, Any]) -> list[str]:
    errors: list[str] = graph_checker_self_errors()
    ledgers = field_witness_ledger(field_witness)
    terminals = terminal_state_map(field_witness)
    tracks = generated_burden_tracks(field_witness)
    restoration_targets = restoration_generated_targets(field_witness)
    strict = track_contract_required(path, field_witness)
    prefix = f"{rel(path)}: "

    for burden, track in sorted(tracks.items()):
        if track and track not in MRP_TRACKS:
            errors.append(prefix + f"B_MRP burden {burden} has non-canonical track {track}")

    for burden in ledgers["B_MRP"]:
        track = tracks.get(burden, "")
        if strict and not track:
            errors.append(prefix + f"B_MRP burden {burden} lacks generated_burdens track primary|restoration")
            continue
        if track and track not in MRP_TRACKS:
            continue
        if track:
            state = terminals.get(burden, "")
            if state not in CLOSED_TERMINAL_STATES | LIVE_TERMINAL_STATES:
                errors.append(prefix + f"{track} track burden {burden} lacks terminal/HOLD/PARTIAL accounting")

    for target in sorted(restoration_targets):
        track = tracks.get(target, "")
        if target not in ledgers["B_MRP"]:
            errors.append(prefix + f"restoration-recoil generated target {target} is not in B_MRP")
        elif track != "restoration":
            errors.append(prefix + f"restoration-recoil generated target {target} must be track restoration, got {track or '<missing>'}")

    for burden, track in sorted(tracks.items()):
        if track == "restoration" and burden not in restoration_targets:
            errors.append(prefix + f"restoration track burden {burden} lacks live restoration-recoil generated-route evidence")

    return errors


def live_registers_covered(field_witness: dict[str, Any]) -> list[str]:
    def certificate_register_subset(values: list[str]) -> list[str]:
        covered: list[str] = []
        for value in values:
            register = canonical_register(value)
            if register in CERTIFICATE_REGISTERS:
                covered.append(register)
        return unique(covered)

    cov = coverage(field_witness)
    diagnostic = cov.get("diagnostic_completeness")
    if isinstance(diagnostic, dict):
        values = list_values(diagnostic.get("live_registers"))
        if values:
            return certificate_register_subset(values)
    normalized = field_witness.get("normalized_activation_record")
    if isinstance(normalized, dict):
        values = list_values(normalized.get("live_registers"))
        if values:
            return certificate_register_subset(values)
    return []


def max_generation_depth(field_witness: dict[str, Any]) -> int:
    value = coverage(field_witness).get("max_generation_depth")
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    depths = [0]
    raw = field_witness.get("generated_burdens")
    items = raw.values() if isinstance(raw, dict) else raw if isinstance(raw, list) else []
    for item in items:
        if isinstance(item, dict):
            depth = item.get("generation_depth")
            if isinstance(depth, int) and not isinstance(depth, bool) and depth >= 0:
                depths.append(depth)
    return max(depths)


def verified_activation_targets(field_witness: dict[str, Any]) -> list[str]:
    targets: list[str] = []
    raw = field_witness.get("owner_activations")
    if not isinstance(raw, list):
        return targets
    terminals = terminal_state_map(field_witness)
    for item in raw:
        if not isinstance(item, dict):
            continue
        target = normalize_burden_id(str(item.get("target") or item.get("source") or ""))
        if BURDEN_ID_RE.fullmatch(target) and terminals.get(target) in CLOSED_TERMINAL_STATES:
            targets.append(target)
    return unique(targets)


def owner_activation_payloads(field_witness: dict[str, Any], target: str) -> list[dict[str, Any]]:
    raw = field_witness.get("owner_activations")
    if not isinstance(raw, list):
        return []
    payloads: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        item_target = normalize_burden_id(str(item.get("target") or item.get("source") or ""))
        if item_target == target:
            payloads.append(item)
    return payloads


def activation_has_required_fields(item: dict[str, Any]) -> bool:
    required = ("owner", "operation", "pressure", "body_ref", "delta", "land")
    return all(str(item.get(key) or "").strip() for key in required)


def hold_partial_nodes(field_witness: dict[str, Any]) -> list[dict[str, str]]:
    nodes: list[dict[str, str]] = []
    for burden, payload in terminal_payloads(field_witness).items():
        state = payload.get("state", "")
        if state not in {"held-with-reason"} | LIVE_TERMINAL_STATES:
            continue
        reason = payload.get("reason") or payload.get("detail") or payload.get("status") or state
        item = {"id": burden, "reason": str(reason).strip()}
        if state:
            item["state"] = state
        nodes.append(item)
    return nodes


def loopbreak_grounds(field_witness: dict[str, Any]) -> list[str]:
    grounds: list[str] = []
    for item in formal_reread_states(field_witness):
        route = str(item.get("route") or "")
        route_type = str(item.get("route_result_type") or "").strip().lower()
        if route_type != "loopbreak" and "LoopBreak" not in route:
            continue
        ground = normalized_loopbreak_ground(item.get("loopbreak_ground"))
        if ground:
            grounds.append(ground)
    return grounds


def field_input_fingerprints(field_witness: dict[str, Any]) -> list[str]:
    candidates: list[Any] = [
        field_witness.get("input_fingerprint"),
        field_witness.get("input_hash"),
        field_witness.get("input_sha256"),
    ]
    provenance = field_witness.get("provenance")
    if isinstance(provenance, dict):
        candidates.extend(
            [
                provenance.get("input_fingerprint"),
                provenance.get("input_hash"),
                provenance.get("input_sha256"),
            ]
        )
    result: list[str] = []
    for value in candidates:
        text = str(value or "").strip()
        if re.fullmatch(r"[A-Fa-f0-9]{64}", text):
            result.append(text.lower())
    return unique(result)


def field_input_fingerprint(field_witness: dict[str, Any]) -> str:
    values = field_input_fingerprints(field_witness)
    return values[0] if values else ""


def field_skill_version(field_witness: dict[str, Any]) -> str:
    provenance = field_witness.get("provenance")
    candidates = [field_witness.get("skill_version")]
    if isinstance(provenance, dict):
        candidates.extend([provenance.get("skill_version"), provenance.get("version")])
    for value in candidates:
        text = str(value or "").strip()
        if text:
            return text
    return DEFAULT_SKILL_VERSION


def model_claims_positive(field_witness: dict[str, Any], text: str) -> bool:
    if field_witness.get("collapse_complete") is True:
        return True
    cov = coverage(field_witness)
    if cov.get("coverage_complete") is True:
        return True
    witness = parse_closure_witness(text)
    if witness and witness.closure_claims_positive:
        return True
    return bool(
        re.search(
            r"(?i)\bcollapse_positive\s*[:=]\s*true\b|\bcoverage_complete\s*[:=]\s*true\b|"
            r"\bclosure\.status\s*=\s*COMPLETE\b",
            text,
        )
    )


def root_activation_semantic_errors(text: str, primary: str, item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not activation_has_required_fields(item):
        return ["root owner activation lacks required owner/operation/pressure/body_ref/delta/land fields"]

    source = graph_burden_id(item.get("source"))
    target = graph_burden_id(item.get("target"))
    if source and source != primary:
        errors.append(f"source {source} does not name primary root {primary}")
    if target != primary:
        errors.append(f"target {target or '<missing>'} does not name primary root {primary}")

    public_text = public_execution_text(text)
    records, parse_errors = parse_act_records(public_text)
    errors.extend(parse_errors)
    body_ref = graph_submove_id(item.get("body_ref"))
    matching_records_by_line = {
        record.record: record
        for record in records
        if graph_submove_id(record.body_ref) == body_ref
    }
    matching_records = list(matching_records_by_line.values())
    if len(matching_records) != 1:
        errors.append(f"body_ref {body_ref or '<missing>'} must match exactly one visible ACT record")
        return errors

    record = matching_records[0]
    record_family = strict_owner_family(record.owner)
    item_family = strict_owner_family(str(item.get("owner") or ""))
    if not item_family:
        errors.append("field_witness owner is not catalogue-backed")
    elif record_family and item_family != record_family:
        errors.append("field_witness owner does not match visible ACT owner family")
    operation = str(item.get("operation") or "").strip()
    if GENERIC_ACT_VALUE_RE.fullmatch(operation) or operation != record.operation:
        errors.append("field_witness operation does not match visible ACT operation")
    if not activation_pressure_matches(record.pi, item.get("pressure")):
        errors.append("field_witness pressure does not match visible ACT pressure")
    delta_text = graph_normalized_text(item.get("delta")).lower()
    if graph_normalized_text(record.delta_result).lower() not in delta_text:
        errors.append("field_witness delta does not include visible ACT delta result")
    item_land_target = graph_burden_id(activation_land_target(item.get("land")))
    if item_land_target != primary:
        errors.append(f"field_witness land targets {item_land_target or '<missing>'}, not Land({primary})")
    record_land_targets = [graph_burden_id(value) for value in re.findall(r"(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+B|B\d+)", record.land)]
    if primary not in record_land_targets:
        errors.append(f"visible ACT Land clause does not target Land({primary})")
    record_target = graph_submove_id(record.body_ref).split("_", 1)[0]
    if record_target != primary:
        errors.append(f"visible ACT body_ref {graph_submove_id(record.body_ref)} does not belong to {primary}")

    raw_target = submove_target_token(record.body_ref)
    blocks = (
        submove_block_index(public_text, raw_target).get(graph_submove_id(record.body_ref), [])
        if raw_target
        else []
    )
    if len(blocks) != 1:
        errors.append(f"visible ACT body_ref {record.body_ref} must dereference to exactly one submove block")
        return errors
    block = blocks[0]
    _block_ref, block_owner = submove_block_ref_owner(block)
    block_family = strict_owner_family(block_owner)
    if record_family and block_family != record_family:
        errors.append("dereferenced body owner does not match visible ACT owner family")
    if not keywords_recoverable(record.pi, block):
        errors.append("visible ACT pressure is not recoverable from dereferenced body")
    if not keywords_recoverable(record.operation, block, minimum=1):
        errors.append("visible ACT operation is not recoverable from dereferenced body")
    if not keywords_recoverable(record.delta_result, block):
        errors.append("visible ACT delta result is not recoverable from dereferenced body")
    aliases = unique(burden_aliases(primary) + burden_aliases(graph_burden_id(raw_target)) + [raw_target])
    if not any(section_has_real_land(public_text, alias) for alias in aliases if alias):
        errors.append(f"no visible Land/HOLD line for primary root aliases {aliases}")
    if not any(contribution_names_land(block, alias) for alias in aliases if alias):
        errors.append(f"dereferenced body lacks Contribution-to-Land for primary root aliases {aliases}")
    return errors


def primary_root_verification(
    text: str,
    field_witness: dict[str, Any],
    terminals: dict[str, str],
    mrp_errors: list[str],
    convergence: list[str],
) -> tuple[bool, str]:
    ledgers = field_witness_ledger(field_witness)
    initials = initial_burdens(field_witness)
    primary = initials[0] if initials else ledgers["B_LA"][0] if ledgers["B_LA"] else ""
    roots = dependency_roots(field_witness)
    edges = graph_edges(field_witness)
    incoming = [edge for edge in edges if edge.endswith(f"->{primary}")]
    activations = owner_activation_payloads(field_witness, primary)
    complete_activation = any(activation_has_required_fields(item) for item in activations)
    semantic_activation_errors: list[str] = []
    semantic_activation = False
    for item in activations:
        found = root_activation_semantic_errors(text, primary, item)
        if not found:
            semantic_activation = True
            break
        semantic_activation_errors.extend(found)
    root_convergence_errors = [
        error
        for error in convergence
        if "owner activation" in error or "landed terminal" in error or "body_ref" in error
    ]
    root_mrp_errors = mrp_errors_for_burden(mrp_errors, primary)
    checks = {
        "primary_named": bool(primary),
        "in_B_LA": primary in ledgers["B_LA"],
        "not_in_B_MRP": primary not in ledgers["B_MRP"],
        "in_roots": primary in roots,
        "no_incoming_edges": not incoming,
        "terminal_landed": terminals.get(primary) == "landed",
        "has_complete_owner_activation": complete_activation,
        "has_semantic_root_activation": semantic_activation,
        "mrp_act_evidence_passes": not root_mrp_errors,
        "convergence_root_evidence_passes": not root_convergence_errors,
    }
    basis = (
        f"primary={primary or '<missing>'}; roots={roots}; incoming={incoming}; "
        f"terminal={terminals.get(primary, '<missing>')}; "
        f"activation_count={len(activations)}; semantic_errors={unique(semantic_activation_errors)}; "
        f"root_mrp_errors={root_mrp_errors}; checks={checks}"
    )
    return all(checks.values()), basis


def escape_route_checklist_count(field_witness: dict[str, Any]) -> int:
    count = 0
    for state in formal_reread_states(field_witness):
        checked = state.get("escape_routes_checked")
        if isinstance(checked, list):
            count += 1
    return count


def escape_route_accounting_errors(field_witness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ledgers = field_witness_ledger(field_witness)
    b_total = set(ledgers["B_total"])
    terminals = terminal_state_map(field_witness)
    for state_index, state in enumerate(formal_reread_states(field_witness), start=1):
        checked = state.get("escape_routes_checked")
        if checked is None:
            continue
        if not isinstance(checked, list):
            errors.append(f"formal_reread_states[{state_index}].escape_routes_checked must be a list")
            continue
        for route_index, route in enumerate(checked, start=1):
            prefix = f"formal_reread_states[{state_index}].escape_routes_checked[{route_index}]"
            if not isinstance(route, dict):
                errors.append(f"{prefix} must be an object")
                continue
            route_type = normalized_token(
                route.get("type") or route.get("escape_route") or route.get("route_type")
            )
            if route_type not in ESCAPE_ROUTE_TYPES:
                errors.append(f"{prefix}.type {route_type or '<missing>'} is not a canonical escape-route type")
                continue
            live = route.get("live")
            if not isinstance(live, bool):
                errors.append(f"{prefix}.live must be true or false")
            basis = str(route.get("basis") or route.get("proof") or route.get("reason") or "").strip()
            if not basis:
                errors.append(f"{prefix}.basis is required")
            disposition = normalized_token(
                route.get("disposition") or route.get("terminal") or route.get("route")
            )
            non_load = route.get("non_load_bearing") is True or route.get("non-load-bearing") is True
            if route_type == "restoration-recoil":
                subtype = normalized_token(
                    route.get("subtype") or route.get("restoration_subtype") or route.get("recoil_subtype")
                )
                if not subtype:
                    errors.append(f"{prefix}: restoration-recoil requires canonical subtype")
                elif subtype not in RESTORATION_RECOIL_SUBTYPE_OWNERS:
                    errors.append(f"{prefix}: restoration-recoil subtype {subtype} is not canonical")
                elif (
                    live is True
                    and not non_load
                    and disposition not in RESTORATION_RECOIL_OWNER_OPTIONAL_DISPOSITIONS
                ):
                    families = route_owner_families(route, state)
                    allowed = RESTORATION_RECOIL_SUBTYPE_OWNERS[subtype]
                    if not families:
                        errors.append(
                            f"{prefix}: live restoration-recoil requires owner_family/owners matching subtype "
                            "or HOLD/PARTIAL/non-load-bearing proof"
                        )
                    elif not families & allowed:
                        errors.append(
                            f"{prefix}: live restoration-recoil subtype {subtype} owner families "
                            f"{sorted(families)} do not match allowed {sorted(allowed)}"
                        )
            if live is not True:
                continue
            target = normalize_burden_id(
                str(
                    route.get("target_burden")
                    or route.get("generated_burden")
                    or route.get("burden")
                    or route.get("target")
                    or ""
                )
            )
            if non_load:
                continue
            if disposition not in ESCAPE_ROUTE_DISPOSITIONS:
                errors.append(f"{prefix}: live escape route lacks typed disposition")
                continue
            if disposition in {"generated", "generated-burden", "generated-burden-instantiation"}:
                if target not in b_total:
                    errors.append(f"{prefix}: generated live escape route target {target or '<missing>'} not in B_total")
            elif target and target not in b_total:
                errors.append(f"{prefix}: disposition target {target} not in B_total")
            elif target and target in terminals and terminals[target] not in CLOSED_TERMINAL_STATES | LIVE_TERMINAL_STATES:
                errors.append(f"{prefix}: disposition target {target} has unrecognized terminal state")
    return errors


def c8_proof_required(path: Path, field_witness: dict[str, Any]) -> bool:
    return any(
        normalized_token(state.get("route_result_type")) in NO_NEW_RESULTANT_TYPES
        or normalized_token(state.get("route")) == "stop"
        or "no_new_resultant_proof" in state
        for state in formal_reread_states(field_witness)
    )


def no_new_resultant_terminal_proof_errors(path: Path, field_witness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ledgers = field_witness_ledger(field_witness)
    b_total = set(ledgers["B_total"])
    terminals = terminal_state_map(field_witness)
    require_proof = c8_proof_required(path, field_witness)
    field_divergence = status_head(diagnostic_status(field_witness, "divergence_check", "del_dot_B", "del-dot B"))
    field_curl = status_head(diagnostic_status(field_witness, "curl_check", "del_cross_kappa", "del-cross kappa"))
    prefix = f"{rel(path)}: "

    for state_index, state in enumerate(formal_reread_states(field_witness), start=1):
        route_type = normalized_token(state.get("route_result_type"))
        route = normalized_token(state.get("route"))
        if route_type not in NO_NEW_RESULTANT_TYPES and route != "stop":
            continue
        label = f"{prefix}formal_reread_states[{state_index}].no_new_resultant_proof"
        proof = state.get("no_new_resultant_proof")
        if proof is None and not require_proof:
            continue
        if not isinstance(proof, dict):
            errors.append(f"{label} must be an object")
            continue
        if proof.get("stop_licensed") is not True:
            errors.append(f"{label}.stop_licensed must be true")

        field_state = proof.get("field_state_at_stop")
        if not isinstance(field_state, dict):
            errors.append(f"{label}.field_state_at_stop must be an object")
        else:
            divergence = status_head(str(field_state.get("divergence") or ""))
            curl = status_head(str(field_state.get("curl") or ""))
            state_divergence = status_head(str(state.get("divergence_state") or ""))
            state_curl = status_head(str(state.get("curl_state") or ""))
            if divergence != "neutral":
                errors.append(f"{label}.field_state_at_stop.divergence must be neutral")
            if state_divergence and divergence != state_divergence:
                errors.append(f"{label}.field_state_at_stop.divergence must match formal state {state_divergence}")
            if field_divergence and divergence != field_divergence:
                errors.append(f"{label}.field_state_at_stop.divergence must match field diagnostics {field_divergence}")
            if curl not in {"null", "resolved"}:
                errors.append(f"{label}.field_state_at_stop.curl must be null or resolved")
            if state_curl and curl != state_curl:
                errors.append(f"{label}.field_state_at_stop.curl must match formal state {state_curl}")
            if field_curl and curl != field_curl:
                errors.append(f"{label}.field_state_at_stop.curl must match field diagnostics {field_curl}")
            b_live = normalized_token(field_state.get("b_live"))
            if b_live not in EMPTY_B_LIVE_STATES:
                errors.append(f"{label}.field_state_at_stop.b_live must be empty")
            elif any(terminals.get(burden, "") not in CLOSED_TERMINAL_STATES for burden in b_total):
                errors.append(f"{label}.field_state_at_stop.b_live is empty but B_total is not fully closed")
            residual = field_state.get("kappa_residual")
            if not (isinstance(residual, int) and not isinstance(residual, bool) and residual == 0):
                errors.append(f"{label}.field_state_at_stop.kappa_residual must be integer 0")

        checked = proof.get("escape_routes_checked")
        if not isinstance(checked, list):
            errors.append(f"{label}.escape_routes_checked must be a list")
            continue
        seen: list[str] = []
        for route_index, route_item in enumerate(checked, start=1):
            route_label = f"{label}.escape_routes_checked[{route_index}]"
            if not isinstance(route_item, dict):
                errors.append(f"{route_label} must be an object")
                continue
            route_kind = normalized_token(
                route_item.get("type") or route_item.get("escape_route") or route_item.get("route_type")
            )
            seen.append(route_kind)
            if route_kind not in ESCAPE_ROUTE_TYPES:
                errors.append(f"{route_label}.type {route_kind or '<missing>'} is not a canonical escape-route type")
                continue
            if route_kind == "restoration-recoil":
                subtype = normalized_token(
                    route_item.get("subtype")
                    or route_item.get("restoration_subtype")
                    or route_item.get("recoil_subtype")
                )
                if not subtype:
                    errors.append(f"{route_label}: restoration-recoil requires canonical subtype")
                elif subtype not in RESTORATION_RECOIL_SUBTYPE_OWNERS:
                    errors.append(f"{route_label}: restoration-recoil subtype {subtype} is not canonical")
            live = route_item.get("live")
            if not isinstance(live, bool):
                errors.append(f"{route_label}.live must be true or false")
            basis = str(route_item.get("basis") or route_item.get("proof") or route_item.get("reason") or "").strip()
            if not basis:
                errors.append(f"{route_label}.basis is required")
            if live is not True:
                continue
            non_load = route_item.get("non_load_bearing") is True or route_item.get("non-load-bearing") is True
            disposition = normalized_token(
                route_item.get("disposition") or route_item.get("terminal") or route_item.get("route")
            )
            if non_load or disposition in {"non-load-bearing", "non-load-bearing-proof"}:
                continue
            if disposition not in ESCAPE_ROUTE_DISPOSITIONS:
                errors.append(f"{route_label}: live escape route lacks typed disposition")
                continue
            target = normalize_burden_id(
                str(
                    route_item.get("target_burden")
                    or route_item.get("generated_burden")
                    or route_item.get("burden")
                    or route_item.get("target")
                    or ""
                )
            )
            if target not in b_total:
                errors.append(f"{route_label}: live escape route target {target or '<missing>'} not in B_total")
            elif not state_terminal_accounted(target, terminals):
                errors.append(f"{route_label}: live escape route target {target} lacks terminal/HOLD/PARTIAL accounting")

        duplicates = sorted({item for item in seen if item and seen.count(item) > 1})
        missing = sorted(ESCAPE_ROUTE_TYPES - set(seen))
        extra = sorted(item for item in set(seen) - ESCAPE_ROUTE_TYPES if item)
        if duplicates:
            errors.append(f"{label}.escape_routes_checked duplicates canonical route(s): {', '.join(duplicates)}")
        if missing:
            errors.append(f"{label}.escape_routes_checked missing canonical route(s): {', '.join(missing)}")
        if extra:
            errors.append(f"{label}.escape_routes_checked has non-canonical route(s): {', '.join(extra)}")
    return errors


def terminal_stop_state_count(field_witness: dict[str, Any]) -> int:
    total = 0
    for state in formal_reread_states(field_witness):
        route_type = normalized_token(state.get("route_result_type"))
        route = normalized_token(state.get("route"))
        if route_type in NO_NEW_RESULTANT_TYPES or route == "stop":
            total += 1
    return total


def terminal_stop_proof_count(field_witness: dict[str, Any]) -> int:
    return sum(
        1
        for state in formal_reread_states(field_witness)
        if isinstance(state.get("no_new_resultant_proof"), dict)
    )


def terminal_stop_proof_complete(field_witness: dict[str, Any], conditions: dict[str, dict[str, Any]]) -> bool:
    stop_count = terminal_stop_state_count(field_witness)
    proof_count = terminal_stop_proof_count(field_witness)
    return bool(conditions["no_new_resultant_terminal_proof"]["pass"] and proof_count >= stop_count)


def explicit_generated_hold_open(
    field_witness: dict[str, Any],
    *,
    graph_edge_set: set[str],
    resultant_edge_set: set[str],
    divergence_curl_errors: list[str],
    formal_errors: list[str],
) -> bool:
    ledgers = field_witness_ledger(field_witness)
    b_mrp = set(ledgers["B_MRP"])
    if not b_mrp or divergence_curl_errors or formal_errors:
        return False
    cov = coverage(field_witness)
    if cov.get("coverage_complete") is not False:
        return False
    terminals = terminal_state_map(field_witness)
    generated_sources = generated_burden_sources(field_witness)
    open_generated: list[str] = []
    for burden in sorted(b_mrp):
        state = terminals.get(burden, "")
        if state not in LIVE_TERMINAL_STATES | {"held-with-reason"}:
            continue
        source = generated_sources.get(burden, "")
        edge = f"{source}->{burden}" if source else ""
        if not edge or edge not in graph_edge_set or edge not in resultant_edge_set:
            return False
        open_generated.append(burden)
    return bool(open_generated)


def diagnostics_mentions_all(status: str, marker: str, burdens: list[str]) -> bool:
    text = str(status or "")
    if marker.lower() not in text.lower():
        return False
    return all(re.search(rf"\b{re.escape(burden)}\b", text) for burden in burdens)


def formal_hold_state_for_burden(state: dict[str, Any], burden: str) -> bool:
    if state_burden_id(state.get("source_burden")) != burden:
        return False
    route_type = normalized_token(state.get("route_result_type"))
    route = normalized_token(state.get("route"))
    if route_type not in {"hold-partial", "held-burden-activation", "loopbreak"} and route not in {
        "hold",
        "partial",
        "recurse",
    }:
        if not state_hold_partial_recurse(state):
            return False
    divergence = status_head(str(state.get("divergence_state") or ""))
    curl = status_head(str(state.get("curl_state") or ""))
    return divergence in DIVERGENCE_POSITIVE_STATES or curl in CURL_LIVE_STATES


def explicit_b_la_hold_open(
    field_witness: dict[str, Any],
    *,
    divergence_curl_errors: list[str],
    formal_errors: list[str],
) -> bool:
    if divergence_curl_errors or formal_errors:
        return False
    cov = coverage(field_witness)
    if cov.get("coverage_complete") is not False:
        return False
    ledgers = field_witness_ledger(field_witness)
    b_la = set(ledgers["B_LA"])
    b_mrp = set(ledgers["B_MRP"])
    terminals = terminal_state_map(field_witness)
    open_b_la = sorted(
        burden
        for burden in b_la
        if burden not in b_mrp and terminals.get(burden, "") in LIVE_TERMINAL_STATES | {"held-with-reason"}
    )
    if not open_b_la:
        return False
    curl = diagnostic_status(field_witness, "curl_check", "del_cross_kappa", "del-cross kappa")
    divergence = diagnostic_status(field_witness, "divergence_check", "del_dot_B", "del-dot B")
    if not diagnostics_mentions_all(curl, "b_la_hold_open", open_b_la):
        return False
    if not (
        diagnostics_mentions_all(divergence, "unresolved_burdens", open_b_la)
        or diagnostics_mentions_all(divergence, "b_la_hold_open", open_b_la)
    ):
        return False
    states = formal_reread_states(field_witness)
    return all(any(formal_hold_state_for_burden(state, burden) for state in states) for burden in open_b_la)


def graph_checker_self_errors() -> list[str]:
    sigma_field_witness = {
        "coverage_proof": {
            "diagnostic_completeness": {
                "live_registers": ["xi", "sigma", "mu", "Omega", "kappa"],
            }
        },
        "normalized_activation_record": {
            "live_registers": ["xi", "sigma", "mu", "Omega", "kappa"],
        },
    }
    sigma_filtered = live_registers_covered(sigma_field_witness)
    if sigma_filtered != ["xi", "mu", "Omega", "kappa"]:
        return [
            "checker self-canary: certificate hard-register coverage did not filter sigma "
            f"from live_registers_covered, got {sigma_filtered}"
        ]
    sigma_only_field_witness = {
        "coverage_proof": {"diagnostic_completeness": {"live_registers": ["sigma"]}},
        "normalized_activation_record": {"live_registers": ["xi"]},
    }
    if live_registers_covered(sigma_only_field_witness):
        return ["checker self-canary: sigma-only diagnostic coverage fell through to hard-register coverage"]
    sigma_certificate = {
        "input_fingerprint": "0" * 64,
        "skill_version": DEFAULT_SKILL_VERSION,
        "collapse_positive": True,
        "coverage_complete": True,
        "divergence_state": "neutral",
        "curl_state": "null",
        "diagnostic_completeness": True,
        "live_registers_covered": sigma_filtered,
        "max_generation_depth": 0,
        "loopbreak_count": 0,
        "loopbreak_grounds": [],
        "verified_activations": ["B1"],
        "hold_partial_nodes": [],
        "primary_track_closed": True,
        "restoration_track_closed": True,
        "divergence_positive_addressed": True,
        "curl_resolved": True,
        "terminal_stop_proof_complete": True,
        "terminal_stop_proof_count": 1,
        "restoration_endpoint_reached": True,
        "checker_version": CHECKER_VERSION,
        "timestamp": "2026-05-30T00:00:00Z",
    }
    found = certificate_errors(sigma_certificate)
    if found:
        return [f"checker self-canary: sigma-filtered certificate failed schema: {error}" for error in found]

    primary_root_text = """## Layer B - Bounded Governed Response
⟦ACT ¹B₁[P7.boundary] :: π=finite answer scope boundary :: body_ref=¹B₁ :: Δ=Δ¹B:scope-boundary-named :: Land(¹B)+⟧

### ¹B₁[P7] — name the finite answer boundary
- Target: finite answer scope boundary.
- Operation: P7.boundary names the finite answer scope boundary and stop condition.
- Result: scope boundary named; the finite answer scope boundary is blocked from becoming an unbounded closure claim.
- Contribution-to-Land(¹B): P7 establishes Land(¹B) by naming the scope boundary and preserving the stop condition.

Land(¹B): landed.
"""
    primary_root_field_witness = {
        "B_LA": ["B1"],
        "B_MRP": ["B5"],
        "B_total": ["B1", "B5"],
        "owner_activations": [
            {
                "owner": "P7",
                "operation": "boundary",
                "pressure": "finite answer scope boundary",
                "body_ref": "B1_1",
                "delta": "Delta(B1)=scope-boundary-named",
                "land": "Land(B1)+",
                "source": "B1",
                "target": "B1",
            }
        ],
        "terminal_states": {"B1": "landed", "B5": "held-with-reason"},
        "coverage_proof": {
            "dependency_graph": {
                "roots": ["B1"],
                "nodes": ["B1", "B5"],
                "edges": [{"from": "B1", "to": "B5"}],
            },
        },
    }
    downstream_pass, downstream_basis = primary_root_verification(
        primary_root_text,
        primary_root_field_witness,
        {"B1": "landed", "B5": "held-with-reason"},
        ["synthetic-output.md: ACT ⁵B₂ record alone does not pass; dereferenced body is not owner-specific"],
        [],
    )
    if not downstream_pass:
        return [
            "checker self-canary: downstream MRP error incorrectly failed primary-root verification: "
            + downstream_basis
        ]
    root_fail, _root_basis = primary_root_verification(
        primary_root_text,
        primary_root_field_witness,
        {"B1": "landed", "B5": "held-with-reason"},
        ["synthetic-output.md: ACT ¹B₁ record alone does not pass; dereferenced body is not owner-specific"],
        [],
    )
    if root_fail:
        return ["checker self-canary: root-local MRP error did not fail primary-root verification"]

    field_witness = {
        "B_LA": ["B1"],
        "B_MRP": ["B2"],
        "B_total": ["B1", "B2"],
        "nodes": [
            {"id": "B1", "type": "burden", "state": "landed"},
            {
                "id": "B2",
                "type": "generated_burden",
                "state": "held-with-reason",
                "generated_by": "MRP(B1)",
                "generation_depth": 1,
            },
        ],
        "edges": [{"from": "B1", "to": "B2", "type": "generated_burden_instantiation"}],
        "generated_burdens": [
            {"id": "B2", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "primary"}
        ],
        "mrp_resultants": [
            {
                "source": "B1",
                "type": "generated_burden_instantiation",
                "finding": "genuine-dependent",
                "graph": "B1 -> B2",
                "route": "RECURSE",
            }
        ],
        "formal_reread_states": [
            {
                "source_burden": "B1",
                "route_result_type": "generated_burden_instantiation",
                "route": "RECURSE",
                "next_burden": "B2",
                "graph_delta": "B1 -> B2",
                "route_gradient": "generated B2 remains HOLD/PARTIAL/RECURSE after R(H,Delta)",
                "divergence_state": "non-neutral",
                "curl_state": "unresolved",
            }
        ],
        "field_diagnostics": {
            "divergence_check": "non-neutral / unresolved_burdens=[B2]",
            "curl_check": "unresolved / generated_burden_hold=[B2]",
        },
        "terminal_states": {"B1": "landed", "B2": "held-with-reason"},
        "coverage_proof": {
            "coverage_complete": False,
            "dependency_graph": {
                "nodes": ["B1", "B2"],
                "edges": [{"from": "B1", "to": "B2"}],
            },
        },
    }
    if not explicit_generated_hold_open(
        field_witness,
        graph_edge_set={"B1->B2"},
        resultant_edge_set={"B1->B2"},
        divergence_curl_errors=[],
        formal_errors=[],
    ):
        return ["checker self-canary: explicit generated-held open graph state was not accepted"]
    curl_state = certificate_curl_state("unresolved", open_hold_state=True)
    hold_nodes = hold_partial_nodes(field_witness)
    certificate = {
        "input_fingerprint": "0" * 64,
        "skill_version": DEFAULT_SKILL_VERSION,
        "collapse_positive": False,
        "coverage_complete": False,
        "divergence_state": "non-neutral",
        "curl_state": curl_state,
        "diagnostic_completeness": True,
        "live_registers_covered": [],
        "max_generation_depth": 1,
        "loopbreak_count": 0,
        "loopbreak_grounds": [],
        "verified_activations": ["B1"],
        "hold_partial_nodes": hold_nodes,
        "primary_track_closed": True,
        "restoration_track_closed": True,
        "divergence_positive_addressed": True,
        "curl_resolved": False,
        "terminal_stop_proof_complete": True,
        "terminal_stop_proof_count": 0,
        "restoration_endpoint_reached": False,
        "checker_version": CHECKER_VERSION,
        "timestamp": "2026-05-30T00:00:00Z",
    }
    if curl_state != "held":
        return ["checker self-canary: generated-held certificate curl_state was not canonicalized to held"]
    if certificate_coverage_complete({"coverage_completeness": {"pass": True}}, open_hold_state=True):
        return ["checker self-canary: generated-held certificate falsely reported coverage_complete"]
    if not hold_nodes:
        return ["checker self-canary: generated-held certificate omitted hold_partial_nodes"]
    found = certificate_errors(certificate)
    if found:
        return [f"checker self-canary: generated-held certificate failed schema: {error}" for error in found]

    b_la_hold_field_witness = {
        "B_LA": ["B1", "B2"],
        "B_MRP": [],
        "B_total": ["B1", "B2"],
        "nodes": [
            {"id": "B1", "type": "burden", "state": "landed"},
            {"id": "B2", "type": "burden", "state": "held-with-reason"},
        ],
        "formal_reread_states": [
            {
                "source_burden": "B2",
                "route_result_type": "hold_partial",
                "route": "HOLD",
                "route_gradient": "B_LA B2 remains HOLD/PARTIAL after R(H,Delta)",
                "divergence_state": "non-neutral",
                "curl_state": "unresolved",
            }
        ],
        "field_diagnostics": {
            "divergence_check": "non-neutral / unresolved_burdens=[B2]",
            "curl_check": "unresolved / b_la_hold_open=[B2]",
        },
        "terminal_states": {"B1": "landed", "B2": "held-with-reason"},
        "coverage_proof": {
            "coverage_complete": False,
            "dependency_graph": {"nodes": ["B1", "B2"], "edges": []},
        },
    }
    if not explicit_b_la_hold_open(
        b_la_hold_field_witness,
        divergence_curl_errors=[],
        formal_errors=[],
    ):
        return ["checker self-canary: explicit B_LA hold-open graph state was not accepted"]
    aliased_hold = json.loads(json.dumps(b_la_hold_field_witness))
    aliased_hold["field_diagnostics"]["curl_check"] = "unresolved / generated_burden_hold=[B2]"
    if explicit_b_la_hold_open(aliased_hold, divergence_curl_errors=[], formal_errors=[]):
        return ["checker self-canary: B_LA hold-open accepted generated_burden_hold alias"]
    if certificate_curl_state("unresolved", open_hold_state=True) != "held":
        return ["checker self-canary: B_LA hold-open certificate curl_state was not canonicalized to held"]
    if certificate_coverage_complete({"coverage_completeness": {"pass": True}}, open_hold_state=True):
        return ["checker self-canary: B_LA hold-open certificate falsely reported coverage_complete"]
    return []


def track_closure_flags(field_witness: dict[str, Any]) -> tuple[bool, bool]:
    ledgers = field_witness_ledger(field_witness)
    terminals = terminal_state_map(field_witness)
    tracks = generated_burden_tracks(field_witness)
    restoration_targets = restoration_generated_targets(field_witness)

    primary_burdens = set(ledgers["B_LA"])
    restoration_burdens = set(restoration_targets)
    for burden in ledgers["B_MRP"]:
        track = tracks.get(burden, "")
        if track == "restoration":
            restoration_burdens.add(burden)
        else:
            primary_burdens.add(burden)

    primary_closed = all(state_terminal_accounted(burden, terminals) for burden in primary_burdens)
    restoration_closed = all(state_terminal_accounted(burden, terminals) for burden in restoration_burdens)
    return primary_closed, restoration_closed


def divergence_curl_generated_burden_errors(path: Path, field_witness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ledgers = field_witness_ledger(field_witness)
    b_la = set(ledgers["B_LA"])
    b_mrp = set(ledgers["B_MRP"])
    terminals = terminal_state_map(field_witness)
    generated_sources = generated_burden_sources(field_witness)
    graph_edge_set = set(graph_edges(field_witness))
    prefix = f"{rel(path)}: "

    for index, state in enumerate(formal_reread_states(field_witness), start=1):
        label = f"{prefix}formal_reread_states[{index}]"
        source = state_burden_id(state.get("source_burden"))
        route_type = normalized_token(state.get("route_result_type"))
        route = normalized_token(state.get("route"))
        divergence = status_head(str(state.get("divergence_state") or ""))
        curl = status_head(str(state.get("curl_state") or ""))
        target = state_burden_id(state.get("next_burden"))
        non_load = state_non_load_bearing(state)
        hold_partial = state_hold_partial_recurse(state)

        if divergence in DIVERGENCE_POSITIVE_STATES:
            if route_type in {"no-new-resultant", "none", "stable"} or route == "stop":
                if not hold_partial and not non_load:
                    errors.append(f"{label}: positive ∇·B cannot STOP/no_new_resultant without generated, HOLD/PARTIAL/RECURSE, or non-load-bearing proof")
            elif route_type == "generated-burden-instantiation":
                if target not in b_mrp:
                    errors.append(f"{label}: positive ∇·B generated target {target or '<missing>'} must be in B_MRP")
                elif generated_sources.get(target) != source:
                    errors.append(f"{label}: positive ∇·B generated target {target} must have generated_by MRP({source}) provenance")
                elif f"{source}->{target}" not in graph_edge_set:
                    errors.append(f"{label}: positive ∇·B generated target {target} must have graph edge {source}->{target}")
                if target and not state_terminal_accounted(target, terminals):
                    errors.append(f"{label}: positive ∇·B generated target {target} lacks terminal/HOLD/PARTIAL accounting")
            elif route_type == "held-burden-activation":
                if target not in b_la:
                    errors.append(f"{label}: positive ∇·B held target {target or '<missing>'} must be in B_LA")
                if target and not state_terminal_accounted(target, terminals):
                    errors.append(f"{label}: positive ∇·B held target {target} lacks terminal/HOLD/PARTIAL accounting")
            elif route_type == "loopbreak":
                if not hold_partial and not non_load:
                    errors.append(f"{label}: positive ∇·B LoopBreak route must carry HOLD/PARTIAL/RECURSE or non-load-bearing proof")
            elif not hold_partial and not non_load:
                errors.append(f"{label}: positive ∇·B must generate, release held burden, LoopBreak, HOLD/PARTIAL/RECURSE, or prove non-load-bearing")

        if curl in CURL_LIVE_STATES:
            if route_type == "loopbreak":
                residual = str(state.get("post_break_reread") or "")
                residual_live = re.search(r"(?i)\b(?:non[- ]null|unresolved|held curl|curl remains|cycle remains)\b", residual)
                if residual_live and not hold_partial and not non_load:
                    errors.append(f"{label}: residual ∇×κ after LoopBreak must be HOLD/PARTIAL/RECURSE or non-load-bearing")
            elif not hold_partial and not non_load:
                errors.append(f"{label}: non-null ∇×κ requires LoopBreak, HOLD/PARTIAL/RECURSE, or non-load-bearing proof")

    return errors


def formalism_emergent_escape_route_errors(field_witness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for state_index, state in enumerate(formal_reread_states(field_witness), start=1):
        checked = state.get("escape_routes_checked")
        if not isinstance(checked, list):
            continue
        state_required = {
            "prior_land": state.get("prior_land"),
            "delta": state.get("delta"),
            "reread": state.get("reread"),
            "route_gradient": state.get("route_gradient"),
            "route_result_type": state.get("route_result_type"),
            "mrp_resultant": state.get("mrp_resultant"),
            "route": state.get("route"),
        }
        state_surface = " ".join(str(value or "") for value in state_required.values())
        for route_index, route in enumerate(checked, start=1):
            if not isinstance(route, dict) or route.get("live") is not True:
                continue
            prefix = f"formal_reread_states[{state_index}].escape_routes_checked[{route_index}]"
            missing_state = [key for key, value in state_required.items() if not str(value or "").strip()]
            if missing_state:
                errors.append(f"{prefix}: live escape route lacks post-Land state fields {missing_state}")
            basis = str(route.get("basis") or route.get("proof") or route.get("reason") or "").strip()
            basis_surface = f"{basis} {state_surface}"
            if not ESCAPE_STATE_EVIDENCE_RE.search(basis_surface):
                errors.append(f"{prefix}: live escape route basis does not cite post-Land/R(H,Delta) state evidence")
            if PREVOICED_ONLY_RE.search(basis) and not ESCAPE_STATE_EVIDENCE_RE.search(basis):
                errors.append(f"{prefix}: pre-voiced/stock objection basis is not formal MRP emergence")
            disposition = normalized_token(
                route.get("disposition") or route.get("terminal") or route.get("route")
            )
            route_type = normalized_token(state.get("route_result_type"))
            if disposition in {"generated", "generated-burden", "generated-burden-instantiation"}:
                if route_type != "generated-burden-instantiation":
                    errors.append(f"{prefix}: generated live escape route must emerge from generated_burden_instantiation state")
                target = normalize_burden_id(
                    str(route.get("target_burden") or route.get("generated_burden") or route.get("target") or "")
                )
                target_surface = " ".join(
                    str(state.get(key) or "")
                    for key in ("next_burden", "mrp_resultant", "graph_delta", "route_gradient")
                )
                if target and target not in target_surface:
                    errors.append(f"{prefix}: generated target {target} is not visible in route-gradient/resultant state")
    return errors


def condition_rows(path: Path, text: str, field_witness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ledgers = field_witness_ledger(field_witness)
    b_total = ledgers["B_total"]
    b_total_set = set(b_total)
    initials = initial_burdens(field_witness)
    terminals = terminal_state_map(field_witness)
    cov = coverage(field_witness)
    convergence = convergence_errors(path, text)
    mrp_errors = mrp_generated_errors(path, text, enforce_public_notation=False)
    formal_errors = formal_semantics_errors(path, text)
    graph_edge_set = set(graph_edges(field_witness))
    resultant_edge_set = set(resultant_edges(field_witness))

    coverage_complete = bool(initials) and set(initials).issubset(terminals)
    no_silent_live = all(
        state in CLOSED_TERMINAL_STATES or state in LIVE_TERMINAL_STATES
        for state in terminals.values()
    ) and set(b_total).issubset(terminals)
    divergence = diagnostic_status(field_witness, "divergence_check", "del_dot_B", "del-dot B")
    divergence_head = status_head(divergence)
    curl = diagnostic_status(field_witness, "curl_check", "del_cross_kappa", "del-cross kappa")
    curl_head = status_head(curl)
    generated_depth = not generation_depth_errors(path, field_witness, strict=True)
    primary_root_pass, primary_root_basis = primary_root_verification(
        text,
        field_witness,
        terminals,
        mrp_errors,
        convergence,
    )
    escape_route_errors = escape_route_accounting_errors(field_witness)
    escape_emergence_errors = formalism_emergent_escape_route_errors(field_witness)
    divergence_curl_errors = divergence_curl_generated_burden_errors(path, field_witness)
    no_new_proof_errors = no_new_resultant_terminal_proof_errors(path, field_witness)
    generated_hold_open = explicit_generated_hold_open(
        field_witness,
        graph_edge_set=graph_edge_set,
        resultant_edge_set=resultant_edge_set,
        divergence_curl_errors=divergence_curl_errors,
        formal_errors=formal_errors,
    )
    b_la_hold_open = explicit_b_la_hold_open(
        field_witness,
        divergence_curl_errors=divergence_curl_errors,
        formal_errors=formal_errors,
    )
    open_hold_state = generated_hold_open or b_la_hold_open
    track_errors = two_track_mrp_errors(path, field_witness)
    tracks = generated_burden_tracks(field_witness)
    restoration_targets = sorted(restoration_generated_targets(field_witness))
    escape_checklists = escape_route_checklist_count(field_witness)
    no_new_proof_count = terminal_stop_proof_count(field_witness)
    restoration_orientation = restoration_orientation_present(text)

    return {
        "diagnostic_completeness": {
            "pass": not any("diagnostic_completeness" in error or "live register" in error for error in convergence),
            "basis": "field_witness convergence live-register and diagnostic_completeness checks",
        },
        "coverage_completeness": {
            "pass": coverage_complete and not any("terminal state" in error for error in convergence),
            "basis": f"initial={initials}; terminal={sorted(terminals)}",
        },
        "activation_verification": {
            "pass": not mrp_errors and not any("owner activation" in error or "landed terminal" in error for error in convergence),
            "basis": "MRP/ACT/body_ref/Land checks plus convergence owner activation evidence",
        },
        "primary_root_verification": {
            "pass": primary_root_pass,
            "basis": primary_root_basis,
        },
        "typed_escape_route_accounting": {
            "pass": not escape_route_errors,
            "basis": (
                f"escape_routes_checked lists={escape_checklists}; "
                f"errors={escape_route_errors}; optional schema-light C.2 field until C.8 hard migration"
            ),
        },
        "formalism_emergent_escape_route_closure": {
            "pass": not escape_emergence_errors,
            "basis": (
                f"escape_routes_checked lists={escape_checklists}; "
                f"errors={escape_emergence_errors}; live routes must emerge from Land -> R(H,Delta), not pre-voicing"
            ),
        },
        "divergence_curl_generated_burden_rules": {
            "pass": not divergence_curl_errors,
            "basis": (
                f"errors={divergence_curl_errors}; positive ∇·B and non-null ∇×κ must force "
                "generated/held/LoopBreak/HOLD/PARTIAL/RECURSE/non-load-bearing accounting"
            ),
        },
        "no_new_resultant_terminal_proof": {
            "pass": not no_new_proof_errors,
            "basis": (
                f"no_new_resultant_proof count={no_new_proof_count}; errors={no_new_proof_errors}; "
                "terminal STOP/no_new_resultant requires structured escape-route and field-state proof"
            ),
        },
        "two_track_mrp_closure": {
            "pass": not track_errors,
            "basis": (
                f"B_MRP tracks={tracks}; restoration_generated_targets={restoration_targets}; "
                f"errors={track_errors}; B.2 primary/restoration certificate fields remain later"
            ),
        },
        "mrp_exhaustion": {
            "pass": no_silent_live and (divergence_head == "neutral" or open_hold_state),
            "basis": (
                f"divergence={divergence or '<missing>'}; terminals={terminals}; "
                f"generated_hold_open={generated_hold_open}; b_la_hold_open={b_la_hold_open}"
            ),
        },
        "curl_loopbreak_handling": {
            "pass": not formal_errors and (curl_head in {"null", "resolved"} or open_hold_state),
            "basis": (
                f"curl={curl or '<missing>'}; formal_reread_state_errors={len(formal_errors)}; "
                f"generated_hold_open={generated_hold_open}; b_la_hold_open={b_la_hold_open}"
            ),
        },
        "graph_structure": {
            "pass": (
                not any("dependency_graph" in error or "orphan" in error for error in convergence)
                and graph_edge_set.issubset(resultant_edge_set)
                and set(graph_nodes(field_witness)).issubset(b_total_set)
                and generated_depth
            ),
            "basis": f"graph_edges={sorted(graph_edge_set)}; resultant_edges={sorted(resultant_edge_set)}",
        },
        "witness_agreement": {
            "pass": not convergence,
            "basis": "Closure/Reconstruction Witness and field_witness convergence validator",
        },
        "model_claim_consistency": {
            "pass": not model_claims_positive(field_witness, text) or (not convergence and coverage_complete),
            "basis": "model-authored positive closure cannot override checker failures",
        },
        "restoration_endpoint_orientation": {
            "pass": restoration_orientation,
            "basis": "Restorative Response or Closing Formulation must carry fitrah/sound-reason orientation, not a heading-only endpoint",
        },
        "schema_light_boundary": {
            "pass": True,
            "basis": "C.2/C.3 escape-route checks remain optional; C.8 no_new_resultant_proof is graph-fixture strict, governed-output adoption remains later",
        },
        "generated_hold_open_state": {
            "pass": True,
            "active": generated_hold_open,
            "basis": "explicit generated B_MRP HOLD/PARTIAL/RECURSE is valid-open graph state, not collapse-positive proof",
        },
        "b_la_hold_open_state": {
            "pass": True,
            "active": b_la_hold_open,
            "basis": "explicit B_LA HOLD/PARTIAL/RECURSE is valid-open graph state, not collapse-positive proof",
        },
    }


def graph_report(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{rel(path)}: output path not found"]
    text = read_text(path)
    payload = extract_embedded_field_witness(text)
    field_witness = extract_field_witness(payload) if payload is not None else None
    if field_witness is None:
        return None, [f"{rel(path)}: field_witness object missing"]

    conditions = condition_rows(path, text, field_witness)
    failures = [name for name, row in conditions.items() if not row["pass"]]
    graph_valid = not failures
    generated_hold_open = bool(conditions.get("generated_hold_open_state", {}).get("active"))
    b_la_hold_open = bool(conditions.get("b_la_hold_open_state", {}).get("active"))
    open_hold_state = generated_hold_open or b_la_hold_open
    report = {
        "path": rel(path),
        "graph_valid": graph_valid,
        "collapse_positive": graph_valid and not open_hold_state,
        "conditions": conditions,
        "failures": failures,
        "boundary": "schema-light B.1 slice; not a B.2 collapse certificate",
    }
    return report, []


def certificate_curl_state(curl: str, *, open_hold_state: bool) -> str:
    if open_hold_state and curl == "unresolved":
        return "held"
    return curl


def certificate_coverage_complete(conditions: dict[str, dict[str, Any]], *, open_hold_state: bool) -> bool:
    return bool(conditions["coverage_completeness"]["pass"] and not open_hold_state)


def graph_certificate(
    path: Path,
    input_fingerprint: str = "",
    input_path: Path | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    text = read_text(path)
    payload = extract_embedded_field_witness(text)
    field_witness = extract_field_witness(payload) if payload is not None else None
    if field_witness is None:
        return None, [f"{rel(path)}: field_witness object missing"]
    report, errors = graph_report(path)
    if errors:
        return None, errors
    if report is None:
        return None, [f"{rel(path)}: graph report missing"]

    cov = coverage(field_witness)
    conditions = report["conditions"]
    generated_hold_open = bool(conditions.get("generated_hold_open_state", {}).get("active"))
    b_la_hold_open = bool(conditions.get("b_la_hold_open_state", {}).get("active"))
    open_hold_state = generated_hold_open or b_la_hold_open
    divergence = status_head(diagnostic_status(field_witness, "divergence_check", "del_dot_B", "del-dot B"))
    raw_curl = status_head(diagnostic_status(field_witness, "curl_check", "del_cross_kappa", "del-cross kappa"))
    curl = certificate_curl_state(raw_curl, open_hold_state=open_hold_state)
    grounds = loopbreak_grounds(field_witness)
    primary_track_closed, restoration_track_closed = track_closure_flags(field_witness)
    terminal_proof_count = terminal_stop_proof_count(field_witness)
    explicit_fingerprint = input_fingerprint.strip().lower()
    computed_fingerprint = input_fingerprint_for_path(input_path) if input_path is not None else ""
    if explicit_fingerprint and computed_fingerprint and explicit_fingerprint != computed_fingerprint:
        return None, [
            f"{rel(path)}: --input-fingerprint {explicit_fingerprint} does not match "
            f"computed B.4 fingerprint {computed_fingerprint} from {rel(input_path)}"
        ]
    field_fingerprints = field_input_fingerprints(field_witness)
    if computed_fingerprint:
        mismatches = [value for value in field_fingerprints if value != computed_fingerprint]
        if mismatches:
            return None, [
                f"{rel(path)}: field_witness input fingerprint(s) {mismatches} do not match "
                f"computed B.4 fingerprint {computed_fingerprint} from {rel(input_path)}"
            ]
    fingerprint = computed_fingerprint or explicit_fingerprint or field_input_fingerprint(field_witness)
    if not fingerprint:
        return None, [f"{rel(path)}: --input or --input-fingerprint is required for certificate emission"]

    certificate = {
        "input_fingerprint": fingerprint,
        "skill_version": field_skill_version(field_witness),
        "collapse_positive": bool(report["collapse_positive"]),
        "coverage_complete": certificate_coverage_complete(conditions, open_hold_state=open_hold_state),
        "divergence_state": divergence,
        "curl_state": curl,
        "diagnostic_completeness": bool(conditions["diagnostic_completeness"]["pass"]),
        "live_registers_covered": live_registers_covered(field_witness),
        "max_generation_depth": max_generation_depth(field_witness),
        "loopbreak_count": len(grounds),
        "loopbreak_grounds": grounds,
        "verified_activations": verified_activation_targets(field_witness),
        "hold_partial_nodes": hold_partial_nodes(field_witness),
        "primary_track_closed": bool(primary_track_closed and conditions["two_track_mrp_closure"]["pass"]),
        "restoration_track_closed": bool(restoration_track_closed and conditions["two_track_mrp_closure"]["pass"]),
        "divergence_positive_addressed": bool(conditions["divergence_curl_generated_burden_rules"]["pass"]),
        "curl_resolved": bool(
            conditions["curl_loopbreak_handling"]["pass"]
            and conditions["divergence_curl_generated_burden_rules"]["pass"]
            and curl in {"null", "resolved"}
        ),
        "terminal_stop_proof_complete": terminal_stop_proof_complete(field_witness, conditions),
        "terminal_stop_proof_count": terminal_proof_count,
        "restoration_endpoint_reached": bool(
            report["collapse_positive"]
            and conditions["restoration_endpoint_orientation"]["pass"]
        ),
        "checker_version": CHECKER_VERSION,
        "timestamp": "2026-05-30T00:00:00Z",
    }
    found = certificate_errors(certificate)
    if found:
        return None, [f"{rel(path)}: certificate validation failed: {error}" for error in found]
    return certificate, []


def direct_fixtures(root: Path, kind: str) -> list[Path]:
    base = root / kind
    if not base.exists():
        return []
    return sorted(base.glob("*.md"))


def paired_input_path(root: Path, fixture: Path) -> Path | None:
    candidate = root / "inputs" / f"{fixture.stem}.txt"
    return candidate if candidate.exists() else None


def run_fixture_suite(root: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    if not root.exists():
        return errors, valid_checked, invalid_checked

    for path in direct_fixtures(root, "valid"):
        report, found = graph_report(path)
        if found:
            errors.extend(found)
            continue
        if report and report["collapse_positive"]:
            valid_checked += 1
            input_path = paired_input_path(root, path)
            if input_path is not None:
                certificate, found = graph_certificate(path, input_path=input_path)
                if found:
                    errors.extend(found)
                elif certificate is None:
                    errors.append(f"{rel(path)}: expected-valid certificate fixture emitted no certificate")
        else:
            errors.append(f"{rel(path)}: expected-valid graph-completeness fixture failed")
            if report:
                errors.append(f"{rel(path)}: failures={report['failures']}")

    for path in direct_fixtures(root, "invalid"):
        report, found = graph_report(path)
        if found:
            invalid_checked += 1
            continue
        if report and report["collapse_positive"]:
            errors.append(f"{rel(path)}: expected-invalid graph-completeness fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in sorted(FORMALISM_NEUTRAL_INVALID_DIR.glob("graph-*.md")):
        report, found = graph_report(path)
        if found:
            invalid_checked += 1
            continue
        if report and report["collapse_positive"]:
            errors.append(f"{rel(path)}: expected-invalid neutral graph-completeness fixture unexpectedly passed")
        else:
            invalid_checked += 1
    return errors, valid_checked, invalid_checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    parser.add_argument("--json", action="store_true", help="Print schema-light condition reports as JSON.")
    parser.add_argument("--certificate", action="store_true", help="Print B.2 collapse certificate JSON for --outputs.")
    parser.add_argument(
        "--input",
        "--input-path",
        dest="input_path",
        type=Path,
        default=None,
        help="Raw D0 input path. B.4 normalization computes the certificate input_fingerprint from this file.",
    )
    parser.add_argument(
        "--input-fingerprint",
        default="",
        help="Transitional explicit SHA-256 D0 fingerprint. When --input is also supplied it must match the computed B.4 fingerprint.",
    )
    args = parser.parse_args()

    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0
    reports: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []

    suite_errors, valid_checked, invalid_checked = run_fixture_suite(args.root)
    errors.extend(suite_errors)

    for path in expand_paths(args.outputs):
        report, found = graph_report(path)
        if found:
            errors.extend(found)
            continue
        if report:
            reports.append(report)
            if report.get("graph_valid"):
                output_checked += 1
            else:
                errors.append(f"{rel(path)}: graph-completeness failures={report['failures']}")
            if args.certificate:
                certificate, found = graph_certificate(path, args.input_fingerprint, args.input_path)
                if found:
                    errors.extend(found)
                elif certificate:
                    certificates.append(certificate)

    if args.certificate and not args.outputs:
        errors.append("--certificate requires --outputs")

    if errors:
        print("graph-completeness check: FAIL")
        for error in errors:
            print(f"- {error}")
        if args.json and reports:
            print(json.dumps(reports, indent=2, sort_keys=True))
        return 1

    if args.certificate and certificates:
        payload: dict[str, Any] | list[dict[str, Any]]
        payload = certificates[0] if len(certificates) == 1 else certificates
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print("graph-completeness check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    if args.json and reports:
        print(json.dumps(reports, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
