#!/usr/bin/env python3
"""Check derived semantics for field_witness.formal_reread_states[].

This checker sits between the strict MRP mirror check and full graph/register
convergence. It does not compute literal nabla/divergence/curl operators. It
does derive the local route semantics that are already machine-addressable:
held routes target B_LA, generated routes target B_MRP with provenance, STOP
has no graph edge, and LoopBreak claims name their post-break reread payload.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path
from typing import Any

from closure_witness_lib import (
    BURDEN_ID_RE,
    burden_ids,
    extract_embedded_field_witness,
    extract_field_witness,
    field_witness_graph_errors,
    field_witness_ledger,
    field_witness_mrp_resultants,
    normalize_burden_id,
    normalize_graph_value,
    public_graph_integrity_diagnostics,
    unique,
)
from check_mrp_generated_burden import (
    formal_reread_values_agree,
    graph_burden_id,
    graph_normalized_text,
    transition_values_agree,
)
from witness_artifact_roles import validate_role


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "formal-reread-state-semantics"

REQUIRED_STATE_FIELDS = {
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
OWNER_ROUTED_TYPES = {"held_burden_activation", "generated_burden_instantiation"}
STOP_TYPES = {"no_new_resultant", "none", "stable"}
LOOPBREAK_TYPES = {"loopbreak"}
HOLD_PARTIAL_TYPES = {"hold_partial"}
CLOSED_STATES = {"landed", "cleared", "discharged-as-derivative"}
HOLD_PARTIAL_TERMINAL_RE = re.compile(r"(?i)\b(?:hold|held|partial|carried[-_ ]?recurse)\b")
HOLD_PARTIAL_DETAIL_RE = re.compile(
    r"(?i)\b(?:HOLD|PARTIAL|held[-/ ]?partial|held[- ]with[- ]reason|"
    r"carried[-_ ]?PARTIAL|carried[-_ ]?RECURSE|partial[- ]real|held route)\b"
)
LICENSED_LOOPBREAK_GROUNDS = {
    "fitrah_ground",
    "sound_reason_ground",
    "necessary_knowledge",
    "direct_contradiction_exposure",
    "definition_discipline",
    "source_status_correction",
    "doubt_churn_boundary",
}
LOOPBREAK_GROUND_ALIASES = {
    "same-global-doubt-churn-repeats-after-every-proof": "doubt_churn_boundary",
    "doubt-churn-carousel": "doubt_churn_boundary",
    "skepticism-carousel": "doubt_churn_boundary",
    "recurring-repeated-that-too-could-be-fluctuation": "doubt_churn_boundary",
    "recurring-that-too-could-be-fluctuation": "doubt_churn_boundary",
    "that-too-could-be-fluctuation": "doubt_churn_boundary",
}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


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


def parse_field_witness(path: Path, text: str) -> tuple[dict[str, Any] | None, list[str]]:
    payload = extract_embedded_field_witness(text)
    if payload is None:
        return None, [f"{rel(path)}: field_witness parser-stable JSON payload missing"]
    field_witness = extract_field_witness(payload)
    if field_witness is None:
        return None, [f"{rel(path)}: field_witness object missing"]
    return field_witness, []


def canonical_text(value: Any) -> str:
    return re.sub(r"\s+", " ", graph_normalized_text(value).strip()).lower()


def state_value(state: dict[str, Any], key: str) -> str:
    return str(state.get(key) or "").strip()


def state_burden(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    burden = graph_burden_id(value)
    if BURDEN_ID_RE.fullmatch(burden):
        return burden
    ids = burden_ids(graph_normalized_text(value))
    return ids[0] if ids else burden


def has_raw_machine_burden(value: Any, burden: str) -> bool:
    if not BURDEN_ID_RE.fullmatch(burden):
        return False
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(burden)}(?![A-Za-z0-9_])", str(value or "")) is not None


def graph_edges_from_value(value: Any) -> list[tuple[str, str]]:
    normalized = normalize_graph_value(graph_normalized_text(value))
    edges: list[tuple[str, str]] = []
    if not normalized or normalized.lower() == "none":
        return edges
    for source, target in re.findall(r"(B\d+)->(B\d+)", normalized):
        edges.append((source, target))
    return unique_edges(edges)


def graph_values_agree(left: Any, right: Any) -> bool:
    left_text = graph_normalized_text(left).strip()
    right_text = graph_normalized_text(right).strip()
    left_edges = graph_edges_from_value(left_text)
    right_edges = graph_edges_from_value(right_text)
    if left_edges or right_edges:
        return set(left_edges) == set(right_edges)
    left_norm = normalize_graph_value(left_text).strip().lower()
    right_norm = normalize_graph_value(right_text).strip().lower()
    return left_norm == right_norm or transition_values_agree(left_norm, right_norm)


def unique_edges(edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str]] = []
    for edge in edges:
        if edge not in seen:
            seen.add(edge)
            result.append(edge)
    return result


def coverage(field_witness: dict[str, Any]) -> dict[str, Any]:
    value = field_witness.get("coverage_proof")
    return value if isinstance(value, dict) else {}


def coverage_edges(field_witness: dict[str, Any]) -> list[tuple[str, str]]:
    graph = coverage(field_witness).get("dependency_graph")
    if not isinstance(graph, dict):
        return []
    raw_edges = graph.get("edges")
    if not isinstance(raw_edges, list):
        return []
    edges: list[tuple[str, str]] = []
    for edge in raw_edges:
        source: Any
        target: Any
        if isinstance(edge, dict):
            source = edge.get("from")
            target = edge.get("to")
        elif isinstance(edge, list) and len(edge) == 2:
            source, target = edge
        else:
            continue
        source_id = normalize_burden_id(str(source or ""))
        target_id = normalize_burden_id(str(target or ""))
        if BURDEN_ID_RE.fullmatch(source_id) and BURDEN_ID_RE.fullmatch(target_id):
            edges.append((source_id, target_id))
    return unique_edges(edges)


def terminal_state_map(field_witness: dict[str, Any]) -> dict[str, str]:
    raw = coverage(field_witness).get("terminal_states")
    if not isinstance(raw, dict):
        raw = field_witness.get("terminal_states")
    if not isinstance(raw, dict):
        return {}
    result: dict[str, str] = {}
    for raw_burden, raw_state in raw.items():
        burden = normalize_burden_id(str(raw_burden))
        if not BURDEN_ID_RE.fullmatch(burden):
            continue
        if isinstance(raw_state, dict):
            state = str(raw_state.get("state") or raw_state.get("status") or "").strip()
        else:
            state = str(raw_state or "").partition("/")[0].strip()
        result[burden] = state
    return result


def generated_source(value: Any) -> str:
    match = re.search(r"(?i)\bMRP\((?P<source>[^)]+)\)", str(value or ""))
    if not match:
        return ""
    return normalize_burden_id(graph_burden_id(match.group("source").strip()))


def generated_burden_sources(field_witness: dict[str, Any]) -> dict[str, str]:
    sources: dict[str, str] = {}
    raw = field_witness.get("generated_burdens")
    if isinstance(raw, dict):
        for raw_burden, raw_payload in raw.items():
            burden = normalize_burden_id(graph_burden_id(raw_burden))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            generated_by = raw_payload.get("generated_by") if isinstance(raw_payload, dict) else raw_payload
            source = generated_source(generated_by)
            if source:
                sources[burden] = source
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            burden = normalize_burden_id(graph_burden_id(item.get("id") or item.get("burden") or item.get("target")))
            if not BURDEN_ID_RE.fullmatch(burden):
                continue
            source = (
                normalize_burden_id(graph_burden_id(item.get("source")))
                if field_witness.get("schema_version") == "public-field-witness-v1"
                else generated_source(item.get("generated_by"))
            )
            if source:
                sources[burden] = source
    return sources


def resultants_by_source(field_witness: dict[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    current = field_witness.get("schema_version") == "public-field-witness-v1"
    raw = field_witness.get("mrp_resultants")
    resultants = (
        [item for item in raw if isinstance(item, dict)]
        if current and isinstance(raw, list)
        else field_witness_mrp_resultants(field_witness)
    )
    for item in resultants:
        source = normalize_burden_id(graph_burden_id(item.get("source")))
        if source:
            result[source] = item
    return result


def reread_records_by_source(field_witness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = field_witness.get("reread_records")
    if not isinstance(raw, list):
        return {}
    records: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        source = normalize_burden_id(
            graph_burden_id(
                item.get("burden_id")
                if field_witness.get("schema_version") == "public-field-witness-v1"
                else item.get("source") or item.get("source_burden")
            )
        )
        if source:
            records[source] = item
    return records


def expected_release(state: dict[str, Any]) -> str:
    route = state_value(state, "route").upper()
    if route == "STOP":
        return "STOP"
    if route == "LOOPBREAK(∇×T)":
        return "LoopBreak(∇×T)"
    return state_burden(state, "next_burden")


def normalized_loopbreak_ground(value: Any) -> str:
    text = state_value({"value": value}, "value")
    if not text:
        return ""
    token = re.sub(r"[^A-Za-z0-9]+", "_", text.strip().lower()).strip("_")
    if token in LICENSED_LOOPBREAK_GROUNDS:
        return token
    dash_token = token.replace("_", "-")
    if "doubt-churn-carousel" in dash_token:
        return "doubt_churn_boundary"
    return LOOPBREAK_GROUND_ALIASES.get(dash_token, "")


def complete_claimed(field_witness: dict[str, Any]) -> bool:
    cov = coverage(field_witness)
    if cov.get("coverage_complete") is True:
        return True
    if field_witness.get("collapse_complete") is True:
        return True
    closure = field_witness.get("closure")
    text = " ".join(str(value) for value in closure.values()) if isinstance(closure, dict) else str(closure or "")
    return bool(re.search(r"(?i)\bcoverage_complete\s*=\s*true\b|\bstatus\s*=\s*COMPLETE\b", text))


def loopbreak_claimed(state: dict[str, Any]) -> bool:
    route_type = state_value(state, "route_result_type")
    if route_type in LOOPBREAK_TYPES:
        return True
    haystack = " ".join(
        state_value(state, key)
        for key in ("route", "mrp_resultant", "curl_state", "preemption_basis")
    )
    return bool(re.search(r"(?i)\bLoopBreak\b", haystack))


def has_hold_or_partial(state: dict[str, Any]) -> bool:
    haystack = " ".join(
        state_value(state, key)
        for key in ("route", "route_gradient", "mrp_resultant", "preemption_basis")
    )
    return bool(re.search(r"(?i)\b(?:HOLD|PARTIAL|RECURSE|bounded stop(?: condition)?)\b", haystack))


def has_hold_partial_detail(state: dict[str, Any]) -> bool:
    haystack = " ".join(
        state_value(state, key)
        for key in ("route_gradient", "mrp_resultant", "preemption_basis", "divergence_state", "curl_state")
    )
    return bool(HOLD_PARTIAL_DETAIL_RE.search(haystack))


def terminal_state_is_hold_partial(value: str) -> bool:
    return bool(HOLD_PARTIAL_TERMINAL_RE.search(value or ""))


def terminal_loopbreak_closure(state: dict[str, Any]) -> bool:
    if state_value(state, "route_result_type") not in LOOPBREAK_TYPES:
        return False
    if not has_hold_or_partial(state):
        return False
    if graph_normalized_text(state.get("graph_delta")).strip().lower() != "none":
        return False
    if state_value(state, "next_burden"):
        return False
    return formal_reread_values_agree(state.get("post_break_reread"), "R(H,Delta)")


def check_loopbreak_state(path: Path, index: int, state: dict[str, Any], b_total: set[str]) -> list[str]:
    if not loopbreak_claimed(state):
        return []
    label = f"{rel(path)}: formal_reread_states[{index}]"
    errors: list[str] = []
    curl = canonical_text(state.get("curl_state"))
    if curl not in {"held", "non-null"}:
        errors.append(f"{label}: LoopBreak requires diagnosed nonzero curl_state")
    required = ("loopbreak_target", "loopbreak_ground", "loopbreak_delta", "post_break_reread")
    missing = [key for key in required if not state_value(state, key)]
    if missing:
        errors.append(f"{label}: LoopBreak claim missing fields: {', '.join(missing)}")
        return errors
    target = state_burden(state, "loopbreak_target")
    if target not in b_total:
        errors.append(f"{label}: loopbreak_target {target!r} must be in B_total")
    ground = normalized_loopbreak_ground(state.get("loopbreak_ground"))
    if ground not in LICENSED_LOOPBREAK_GROUNDS:
        errors.append(
            f"{label}: loopbreak_ground must be one of {', '.join(sorted(LICENSED_LOOPBREAK_GROUNDS))}"
        )
    if not formal_reread_values_agree(state.get("post_break_reread"), "R(H,Delta)"):
        errors.append(f"{label}: post_break_reread must invoke R(H,Delta)")
    if not burden_ids(state_value(state, "loopbreak_delta")):
        errors.append(f"{label}: loopbreak_delta must name the affected burden")
    return errors


def state_semantics_errors(path: Path, field_witness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    prefix = f"{rel(path)}: "
    current = field_witness.get("schema_version") == "public-field-witness-v1"
    if current:
        role_diagnostics = validate_role(field_witness, "public_graph", "current")
        if role_diagnostics:
            return [
                prefix + f"{item.failure_subcode}: {item.message}"
                for item in role_diagnostics
            ]
        graph_diagnostics = public_graph_integrity_diagnostics(
            field_witness, compatibility="current"
        )
        if graph_diagnostics:
            return [
                prefix + f"{item['failure_subcode']}: {item['message']}"
                for item in graph_diagnostics
            ]
    else:
        errors.extend(prefix + error for error in field_witness_graph_errors(field_witness))

    ledgers = field_witness_ledger(field_witness)
    b_la = set(ledgers["B_LA"])
    b_mrp = set(ledgers["B_MRP"])
    b_total = set(ledgers["B_total"])
    if current:
        raw_records = field_witness.get("reread_records")
        record_rows = (
            [item for item in raw_records if isinstance(item, dict)]
            if isinstance(raw_records, list)
            else []
        )
        record_burdens = [str(item.get("burden_id") or "") for item in record_rows]
        if record_burdens != ledgers["B_total"]:
            errors.append(prefix + "current reread_records burden order must exactly equal B_total")
        record_cycles = [str(item.get("cycle_id") or "") for item in record_rows]
        if len(record_cycles) != len(set(record_cycles)):
            errors.append(prefix + "current reread_records cycle_id identities must be unique")
        raw_resultants = field_witness.get("mrp_resultants")
        resultant_rows = (
            [item for item in raw_resultants if isinstance(item, dict)]
            if isinstance(raw_resultants, list)
            else []
        )
        resultant_pairs = [
            (str(item.get("source") or ""), str(item.get("target") or ""))
            for item in resultant_rows
        ]
        if len(resultant_pairs) != len(set(resultant_pairs)):
            errors.append(prefix + "current mrp_resultants source/target identities must be unique")
    generated_sources = generated_burden_sources(field_witness)
    resultants = resultants_by_source(field_witness)
    current_resultants_by_source: dict[str, list[dict[str, Any]]] = {}
    if current:
        for row in resultant_rows:
            source = normalize_burden_id(graph_burden_id(row.get("source")))
            if source:
                current_resultants_by_source.setdefault(source, []).append(row)
    records = reread_records_by_source(field_witness)
    edges = set(coverage_edges(field_witness))
    terminals = terminal_state_map(field_witness)

    raw_states = field_witness.get("formal_reread_states")
    if not isinstance(raw_states, list) or not raw_states:
        return errors + [f"{rel(path)}: field_witness.formal_reread_states must be a non-empty list"]

    seen_sources: list[str] = []
    stop_seen = False
    for index, item in enumerate(raw_states, start=1):
        label = f"{rel(path)}: formal_reread_states[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label}: state must be a JSON object")
            continue
        missing = sorted(key for key in REQUIRED_STATE_FIELDS if not state_value(item, key))
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")
            continue

        source = state_burden(item, "source_burden")
        if not source:
            errors.append(f"{label}: source_burden must normalize to a B-id")
            continue
        seen_sources.append(source)
        if source not in b_total:
            errors.append(f"{label}: source_burden {source} is outside B_total")
        if f"Land({source})" not in graph_normalized_text(item.get("prior_land")):
            errors.append(f"{label}: prior_land must name Land({source})")
        if not has_raw_machine_burden(item.get("delta"), source):
            errors.append(f"{label}: delta must name {source}")
        if not formal_reread_values_agree(item.get("reread"), "R(H,Delta)"):
            errors.append(f"{label}: reread must invoke R(H,Delta)")

        route = state_value(item, "route").upper()
        route_type = state_value(item, "route_result_type")
        divergence = canonical_text(item.get("divergence_state"))
        curl = canonical_text(item.get("curl_state"))
        graph_edges = graph_edges_from_value(item.get("graph_delta"))
        resultant = resultants.get(source)
        current_resultants = current_resultants_by_source.get(source, [])
        record = records.get(source)
        if current:
            if record is None:
                errors.append(f"{label}: no field_witness.reread_records entry for {source}")
            else:
                if route_type != str(record.get("route_result_type") or ""):
                    errors.append(
                        f"{label}: route_result_type does not match reread_records[{source}]"
                    )
                if terminals.get(source, "") != str(record.get("terminal_state") or ""):
                    errors.append(
                        f"{label}: terminal state does not match reread_records[{source}]"
                    )
        if current and not current_resultants:
            if route_type in OWNER_ROUTED_TYPES:
                errors.append(f"{label}: no field_witness.mrp_resultants entry for {source}")
        elif current:
            if any(route_type != row.get("type") for row in current_resultants):
                errors.append(f"{label}: route_result_type does not match mrp_resultants[{source}].type")
            if any(route != str(row.get("route") or "").upper() for row in current_resultants):
                errors.append(f"{label}: route does not match mrp_resultants[{source}].route")
            resultant_edges = {
                (source, normalize_burden_id(graph_burden_id(row.get("target"))))
                for row in current_resultants
                if normalize_burden_id(graph_burden_id(row.get("target")))
            }
            if set(graph_edges) != resultant_edges:
                errors.append(
                    f"{label}: graph_delta does not match current mrp_resultants[{source}] targets"
                )
        elif resultant is None:
            errors.append(f"{label}: no field_witness.mrp_resultants entry for {source}")
        else:
            if route_type != resultant.get("type"):
                errors.append(f"{label}: route_result_type does not match mrp_resultants[{source}].type")
            if route != str(resultant.get("route") or "").upper():
                errors.append(f"{label}: route does not match mrp_resultants[{source}].route")
            if not graph_values_agree(item.get("graph_delta"), resultant.get("graph")):
                errors.append(f"{label}: graph_delta does not match mrp_resultants[{source}].graph")

        release = expected_release(item)
        if record is not None and "release_next" in record:
            record_release = graph_burden_id(record.get("release_next"))
            if not record_release:
                record_release = str(record.get("release_next") or "").strip().upper()
            if release and release != record_release:
                errors.append(f"{label}: reread_records release_next {record_release!r} does not match formal state {release!r}")

        if route_type in OWNER_ROUTED_TYPES:
            target = state_burden(item, "next_burden")
            if not target:
                errors.append(f"{label}: owner-routed formal state requires next_burden")
            elif graph_edges and (source, target) not in graph_edges:
                errors.append(f"{label}: graph_delta must contain edge {source}->{target}")
            elif edges and (source, target) not in edges:
                errors.append(f"{label}: coverage_proof.dependency_graph.edges must contain {source}->{target}")
            owner_route = item.get("owner_route")
            if not isinstance(owner_route, list) or not owner_route or any(not str(value).strip() for value in owner_route):
                errors.append(f"{label}: owner-routed formal state requires non-empty owner_route")
            if route == "STOP":
                errors.append(f"{label}: owner-routed formal state cannot use STOP route")

        if route_type == "held_burden_activation":
            target = state_burden(item, "next_burden")
            if target and target not in b_la:
                errors.append(f"{label}: held_burden_activation target {target} must be present in B_LA")
            if target and target in b_mrp:
                errors.append(f"{label}: held_burden_activation target {target} must not be a generated B_MRP node")
            gradient = graph_normalized_text(item.get("route_gradient"))
            if target and target not in burden_ids(gradient) and not re.search(r"(?i)\b(?:held|already|B_LA|initial)\b", gradient):
                errors.append(f"{label}: held route_gradient must name {target} or mark an already-held/B_LA route")

        elif route_type == "generated_burden_instantiation":
            target = state_burden(item, "next_burden")
            if target and target not in b_mrp:
                errors.append(f"{label}: generated_burden_instantiation target {target} must be present in B_MRP")
            if target and generated_sources.get(target) != source:
                errors.append(f"{label}: generated target {target} must have generated_by MRP({source}) provenance")
            if generated_source(item.get("generated_by")) != source:
                errors.append(f"{label}: generated state must set generated_by to MRP({source})")
            gradient = graph_normalized_text(item.get("route_gradient"))
            if target and target not in burden_ids(gradient):
                errors.append(f"{label}: generated route_gradient must name generated target {target}")
            if not re.search(r"(?i)\b(?:generated|new|MRP|absent|not present)\b", gradient):
                errors.append(f"{label}: generated route_gradient must mark the target as generated/new/absent from B_LA")

        elif route_type in STOP_TYPES:
            stop_seen = True
            if route != "STOP":
                errors.append(f"{label}: no_new_resultant formal state must use STOP route")
            if graph_normalized_text(item.get("graph_delta")).strip().lower() != "none":
                errors.append(f"{label}: STOP/no_new_resultant graph_delta must be none")
            if state_value(item, "next_burden"):
                errors.append(f"{label}: STOP/no_new_resultant must not set next_burden")
            if divergence != "neutral":
                errors.append(f"{label}: STOP requires neutral divergence_state, found {divergence!r}")
            if curl not in {"null", "resolved"} and not has_hold_or_partial(item):
                errors.append(f"{label}: STOP requires null/resolved curl_state unless HOLD/PARTIAL/LoopBreak is explicit")
        elif route_type in LOOPBREAK_TYPES:
            if route != "LOOPBREAK(∇×T)":
                errors.append(f"{label}: loopbreak formal state must use Route: LoopBreak(∇×T)")
            if graph_normalized_text(item.get("graph_delta")).strip().lower() != "none":
                errors.append(f"{label}: loopbreak formal state graph_delta must be none")
            if state_value(item, "next_burden"):
                errors.append(f"{label}: loopbreak formal state must not set next_burden")
            if not has_hold_or_partial(item):
                errors.append(f"{label}: loopbreak formal state requires explicit HOLD/PARTIAL accounting")
        elif route_type in HOLD_PARTIAL_TYPES:
            if route != "HOLD":
                errors.append(f"{label}: hold_partial formal state must use Route: HOLD")
            if graph_normalized_text(item.get("graph_delta")).strip().lower() != "none":
                errors.append(f"{label}: hold_partial formal state graph_delta must be none")
            if state_value(item, "next_burden"):
                errors.append(f"{label}: hold_partial formal state must not set next_burden")
            if not has_hold_partial_detail(item):
                errors.append(f"{label}: hold_partial formal state requires explicit HOLD/PARTIAL accounting")
            terminal = terminals.get(source, "")
            if not terminal or not HOLD_PARTIAL_TERMINAL_RE.search(terminal):
                errors.append(f"{label}: hold_partial source {source} must have HOLD/PARTIAL terminal accounting")
        else:
            errors.append(f"{label}: unsupported route_result_type {route_type!r}")

        if route == "STOP" and curl not in {"null", "resolved"} and not has_hold_or_partial(item):
            errors.append(f"{label}: STOP with non-null curl requires explicit LoopBreak/HOLD/PARTIAL accounting")
        errors.extend(check_loopbreak_state(path, index, item, b_total))
        if terminal_loopbreak_closure(item):
            stop_seen = True

    duplicate_sources = sorted({source for source in seen_sources if seen_sources.count(source) > 1})
    if duplicate_sources:
        errors.append(f"{rel(path)}: duplicate formal_reread_states source_burden values: {', '.join(duplicate_sources)}")
    expected_sources = set(records) if current else set(resultants)
    missing_sources = sorted(expected_sources - set(seen_sources))
    if missing_sources:
        owner = "reread_records" if current else "mrp_resultants"
        errors.append(
            f"{rel(path)}: formal_reread_states missing {owner} sources: {', '.join(missing_sources)}"
        )
    extra_sources = sorted(set(seen_sources) - expected_sources)
    if extra_sources:
        owner = "reread_records" if current else "mrp_resultants"
        errors.append(
            f"{rel(path)}: formal_reread_states name sources absent from {owner}: {', '.join(extra_sources)}"
        )

    if complete_claimed(field_witness):
        if not stop_seen:
            errors.append(f"{rel(path)}: complete closure requires a terminal STOP/no_new_resultant formal state")
        complete_hold_sources = sorted(
            state_burden(item, "source_burden")
            for item in raw_states
            if isinstance(item, dict) and state_value(item, "route_result_type") in HOLD_PARTIAL_TYPES
        )
        if complete_hold_sources:
            errors.append(
                f"{rel(path)}: complete closure cannot include HOLD/PARTIAL formal state(s): "
                f"{', '.join(complete_hold_sources)}"
            )
        for burden in ledgers["B_total"]:
            state = terminals.get(burden, "")
            if terminal_state_is_hold_partial(state):
                errors.append(f"{rel(path)}: complete closure terminal {burden}:{state} remains HOLD/PARTIAL")
                continue
            if state and state not in CLOSED_STATES:
                errors.append(f"{rel(path)}: complete closure terminal {burden}:{state} is not closed")

    for burden, source in generated_sources.items():
        if burden not in b_mrp:
            errors.append(f"{rel(path)}: generated_burdens lists {burden} outside B_MRP")
        if source not in b_total:
            errors.append(f"{rel(path)}: generated_burdens source {source} for {burden} is outside B_total")
    return errors


def formal_semantics_errors(path: Path, text: str) -> list[str]:
    field_witness, errors = parse_field_witness(path, text)
    if field_witness is None:
        return errors
    return errors + state_semantics_errors(path, field_witness)


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0

    for path in valid:
        found = formal_semantics_errors(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = formal_semantics_errors(path, read_text(path))
        if not found:
            errors.append(f"{rel(path)}: expected-invalid formal reread-state fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in expand_paths(args.outputs):
        if not path.exists():
            errors.append(f"{path}: output path not found")
            continue
        found = formal_semantics_errors(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("formal reread-state semantics check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("formal reread-state semantics check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
