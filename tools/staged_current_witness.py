#!/usr/bin/env python3
"""Pure current Stage07 witness projection from validated staged records.

The staged runner remains a small consumer of this owner. Historical witness
objects are accepted only as an internal source projection; emitted release
objects always use the strict current public-graph schema.
"""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any

from closure_witness_lib import public_graph_integrity_diagnostics
from stage_projection_contract import (
    activation_lifecycle_fingerprint,
    canonical_json_sha256,
    projection_diagnostics,
)
from witness_artifact_roles import validate_role


class CurrentWitnessError(ValueError):
    pass


def _b_id(value: Any) -> str:
    text = str(value or "").strip()
    return text if re.fullmatch(r"B[1-9][0-9]*", text) else ""


def _declared_generated_source(record: dict[str, Any]) -> str:
    for key in ("source", "parent_id", "parent", "generated_from", "generated_by"):
        raw = record.get(key)
        direct = _b_id(raw)
        if direct:
            return direct
        match = re.search(r"(?i)\bMRP\((B[1-9][0-9]*)\)", str(raw or ""))
        if match:
            return _b_id(match.group(1))
    return ""


def _ordered_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _content_id(prefix: str, value: Any) -> str:
    return f"{prefix}-{canonical_json_sha256(value)}"


def _structured_nar(stage06: dict[str, Any]) -> dict[str, Any]:
    for key in ("normalized_activation_record", "normalized_activation_record_details"):
        value = stage06.get(key)
        if isinstance(value, dict) and isinstance(value.get("per_burden"), list):
            return value
    raise CurrentWitnessError(
        "Current Stage 07 witness projection requires a structured Stage 06 NAR; "
        "a boolean or missing NAR cannot mint a current public graph"
    )


def build_current_projection(
    *,
    historical: dict[str, Any],
    stage04: dict[str, Any],
    stage05: dict[str, Any],
    stage06: dict[str, Any],
    act_details: dict[str, dict[str, str]],
    entries: list[dict[str, Any]],
    field_witness_body_refs: list[str],
    owner_activation_refs: list[str],
    owner_details: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Derive one content-addressed Stage04-07 parity projection."""

    if not act_details:
        raise CurrentWitnessError("Current Stage 07 witness projection requires canonical Stage 04 ACT rows")
    body_refs = list(act_details)
    if field_witness_body_refs != body_refs:
        raise CurrentWitnessError(
            "Current Stage 07 witness projection Stage 06 field_witness_body_refs "
            "must exactly equal ordered Stage 04 ACT body_refs"
        )
    if owner_activation_refs != body_refs:
        raise CurrentWitnessError(
            "Current Stage 07 witness projection Stage 06 owner_activations "
            "must exactly equal ordered Stage 04 ACT body_refs"
        )

    nar06 = _structured_nar(stage06)
    rows06 = [
        row
        for row in nar06["per_burden"]
        if isinstance(row, dict) and str(row.get("owner_id") or "") != "MRP"
    ]
    expected_rows = [
        (detail["burden_id"], detail["owner"], detail["operation"], detail["delta_result"])
        for detail in act_details.values()
    ]
    actual_rows = [
        (
            _b_id(row.get("burden_id")),
            str(row.get("owner_id") or ""),
            str(row.get("operation") or ""),
            str(row.get("delta_result") or ""),
        )
        for row in rows06
    ]
    if actual_rows != expected_rows:
        raise CurrentWitnessError(
            "Current Stage 07 witness projection Stage 06 NAR activation identity differs "
            "from ordered Stage 04 owner/operation/delta rows"
        )
    for ref, detail in act_details.items():
        mirror = owner_details.get(ref)
        if mirror is None:
            continue
        for key, expected in (
            ("owner_id", detail["owner"]),
            ("operation", detail["operation"]),
            ("delta_result", detail["delta_result"]),
        ):
            actual = mirror.get(key)
            if actual is not None and str(actual) != expected:
                raise CurrentWitnessError(
                    f"Current Stage 07 witness projection Stage 06 {ref} {key} differs from Stage 04"
                )

    b_la = [_b_id(item) for item in historical.get("B_LA", []) if _b_id(item)]
    b_mrp = [_b_id(item) for item in historical.get("B_MRP", []) if _b_id(item)]
    b_total = [_b_id(item) for item in historical.get("B_total", []) if _b_id(item)]
    if b_total != _ordered_unique([*b_la, *b_mrp]):
        raise CurrentWitnessError("Current Stage 07 witness projection B_total must equal ordered B_LA plus B_MRP")
    raw_terminals = historical.get("terminal_states")
    if not isinstance(raw_terminals, dict):
        raise CurrentWitnessError("Current Stage 07 witness projection requires terminal states")
    terminals = {burden: str(raw_terminals.get(burden) or "") for burden in b_total}
    if any(not state for state in terminals.values()):
        raise CurrentWitnessError("Current Stage 07 witness projection has a burden without terminal state")

    raw_edges = historical.get("edges")
    edges = [
        {
            "from": _b_id(row.get("from")),
            "to": _b_id(row.get("to")),
            "kind": str(row.get("type") or "noetic-dependency"),
        }
        for row in raw_edges
        if isinstance(raw_edges, list) and isinstance(row, dict)
    ]
    if any(not row["from"] or not row["to"] for row in edges):
        raise CurrentWitnessError("Current Stage 07 witness projection contains an untyped dependency endpoint")
    incoming_edges_by_target: dict[str, list[dict[str, str]]] = {}
    for edge in edges:
        incoming_edges_by_target.setdefault(edge["to"], []).append(edge)
    incoming_source = {edge["to"]: edge["from"] for edge in edges}
    generated_records = {
        _b_id(row.get("id")): row
        for row in historical.get("generated_burdens", [])
        if isinstance(row, dict) and _b_id(row.get("id"))
    }
    for burden in b_mrp:
        incoming = incoming_edges_by_target.get(burden, [])
        if len(incoming) != 1:
            raise CurrentWitnessError(
                f"Current Stage 07 witness projection generated burden {burden} requires exactly one incoming generated-burden edge"
            )
        if incoming[0]["kind"] != "generated_burden_instantiation":
            raise CurrentWitnessError(
                f"Current Stage 07 witness projection generated burden {burden} incoming edge must be generated_burden_instantiation"
            )
        declared_source = _declared_generated_source(generated_records.get(burden, {}))
        if declared_source != incoming[0]["from"]:
            raise CurrentWitnessError(
                f"Current Stage 07 witness projection generated burden {burden} declared source {declared_source or '<missing>'} does not match unique incoming source {incoming[0]['from']}"
            )
    for burden in b_total:
        if burden not in b_mrp and len(incoming_edges_by_target.get(burden, [])) > 1:
            raise CurrentWitnessError(
                f"Current Stage 07 witness projection burden {burden} supports at most one incoming dependency edge while parent_id is singular"
            )

    entry_by_burden: dict[str, dict[str, Any]] = {}
    for entry in entries:
        burden = _b_id(entry.get("burden_id"))
        if not burden or burden in entry_by_burden:
            raise CurrentWitnessError(
                "Current Stage 07 witness projection requires one unique Stage 05 reread per burden"
            )
        entry_by_burden[burden] = entry
    missing = [burden for burden in b_total if burden not in entry_by_burden]
    if missing:
        raise CurrentWitnessError(
            f"Current Stage 07 witness projection lacks Stage 05 reread records for {missing}"
        )

    activations: list[dict[str, Any]] = []
    for ordinal, (ref, detail) in enumerate(act_details.items()):
        burden = detail["burden_id"]
        pressure_sha256 = canonical_json_sha256(
            {"burden_id": burden, "pressure": detail["pressure"]}
        )
        activations.append(
            {
                "ordinal": ordinal,
                "obligation_id": _content_id(
                    "O", {"body_ref": ref, "stage04_act_row": detail["row"]}
                ),
                "operation_capsule_id": _content_id(
                    "OC",
                    {
                        "owner": detail["owner"],
                        "operation": detail["operation"],
                        "body_ref": ref,
                    },
                ),
                "body_ref": ref,
                "burden_id": burden,
                "owner_id": detail["owner"],
                "operation": detail["operation"],
                "pressure_ids": [f"P-{pressure_sha256}"],
                "before_state_sha256": pressure_sha256,
                "performed_evidence_sha256": canonical_json_sha256(
                    {"stage04_act_row": detail["row"]}
                ),
                "resultant_sha256": canonical_json_sha256(
                    {
                        "delta": detail["delta"],
                        "delta_result": detail["delta_result"],
                        "land": detail["land"],
                        "terminal_state": terminals.get(burden),
                    }
                ),
                "residual_sha256": canonical_json_sha256(
                    {"burden_id": burden, "terminal_state": terminals.get(burden)}
                ),
                "land_contribution_sha256": canonical_json_sha256(
                    {"burden_id": burden, "land": detail["land"]}
                ),
                "semantic_body_sha256": hashlib.sha256(detail["row"].encode("utf-8")).hexdigest(),
            }
        )

    historical_nodes = {
        _b_id(row.get("id")): row
        for row in historical.get("nodes", [])
        if isinstance(row, dict) and _b_id(row.get("id"))
    }
    cycle_ids = {
        burden: _content_id(
            "C",
            {
                "burden_id": burden,
                "origin": "B_MRP" if burden in b_mrp else "B_LA",
                "terminal_state": terminals[burden],
                "reread": entry_by_burden[burden],
            },
        )
        for burden in b_total
    }
    cycles: list[dict[str, Any]] = []
    for burden in b_total:
        burden_activations = [row for row in activations if row["burden_id"] == burden]
        source = incoming_source.get(burden)
        if burden in b_mrp and source not in cycle_ids:
            raise CurrentWitnessError(
                f"Current Stage 07 witness projection generated burden {burden} lacks a source cycle"
            )
        depth = int(
            historical_nodes.get(burden, {}).get("generation_depth")
            or (1 if burden in b_mrp else 0)
        )
        cycles.append(
            {
                "cycle_id": cycle_ids[burden],
                "burden_id": burden,
                "origin": "B_MRP" if burden in b_mrp else "B_LA",
                "generation_depth": depth,
                "parent_cycle_id": cycle_ids.get(source) if source else None,
                "obligation_ids": [row["obligation_id"] for row in burden_activations],
                "operation_capsule_ids": [row["operation_capsule_id"] for row in burden_activations],
                "lifecycle_status": terminals[burden],
                "terminal_state": terminals[burden],
                "land_sha256": canonical_json_sha256(
                    {
                        "burden_id": burden,
                        "lands": [act_details[row["body_ref"]]["land"] for row in burden_activations],
                    }
                ),
                "reread_sha256": canonical_json_sha256(entry_by_burden[burden]),
                "resultant_sha256": canonical_json_sha256(
                    {
                        "burden_id": burden,
                        "activation_resultants": [row["resultant_sha256"] for row in burden_activations],
                        "reread": entry_by_burden[burden],
                        "terminal_state": terminals[burden],
                    }
                ),
            }
        )

    historical_graph = historical.get("coverage_proof", {}).get("dependency_graph", {})
    roots = [
        _b_id(item) for item in historical_graph.get("roots", []) if _b_id(item)
    ] if isinstance(historical_graph, dict) else []
    if not roots:
        targets = {row["to"] for row in edges}
        roots = [burden for burden in b_total if burden not in targets]
    noetic_graph = {
        "nodes": b_total,
        "edges": [{"from": row["from"], "to": row["to"]} for row in edges],
        "roots": roots,
    }
    event_ids = {
        cycle["burden_id"]: _content_id(
            "E", {"cycle_id": cycle["cycle_id"], "burden_id": cycle["burden_id"]}
        )
        for cycle in cycles
    }
    event_graph = {
        "nodes": [event_ids[burden] for burden in b_total],
        "edges": [
            {"from": event_ids[row["from"]], "to": event_ids[row["to"]]}
            for row in edges
        ],
        "roots": [event_ids[burden] for burden in roots],
    }
    coverage_complete = bool(historical.get("coverage_proof", {}).get("coverage_complete"))
    unresolved = [
        burden
        for burden in b_total
        if terminals[burden] not in {"landed", "cleared", "discharged-as-derivative"}
    ]
    if coverage_complete and unresolved:
        raise CurrentWitnessError("Current Stage 07 witness projection cannot close with unresolved terminal states")
    routes = [str(entry.get("route") or "").upper() for entry in entries]
    decision = (
        "COMPLETE"
        if coverage_complete
        else "RECURSE"
        if "RECURSE" in routes
        else "PARTIAL"
        if any("PARTIAL" in state.upper() for state in terminals.values())
        else "HOLD"
    )
    closure = {
        "opening_state": "OPEN",
        "derived_decision": decision,
        "initial_coverage_complete": all(burden in terminals for burden in b_la),
        "lifecycle_accounting_complete": set(terminals) == set(b_total),
        "collapse_positive": coverage_complete,
        "closure_confirmed": coverage_complete,
        "remaining_open_ids": unresolved,
        "divergence": "neutral" if coverage_complete else "non-neutral",
        "curl": "null" if coverage_complete else "held",
        "loopbreak": None,
    }
    nar = {
        "schema_version": "daee-nar-v2",
        "per_activation": [
            {
                "ordinal": row["ordinal"],
                "obligation_id": row["obligation_id"],
                "body_ref": row["body_ref"],
                "burden_id": row["burden_id"],
                "owner_id": row["owner_id"],
                "operation": row["operation"],
                "resultant_sha256": row["resultant_sha256"],
            }
            for row in activations
        ],
        "per_burden": [
            {
                "burden_id": burden,
                "cycle_id": cycle_ids[burden],
                "activation_ordinals": [
                    row["ordinal"] for row in activations if row["burden_id"] == burden
                ],
            }
            for burden in b_total
        ],
    }
    t_lang = {
        "projection": "partial_coupling",
        "uptake_guaranteed": False,
        "boundary": "Structural projection does not guarantee uptake.",
    }
    projection: dict[str, Any] = {
        "schema_version": "daee-stage-projection-v1",
        "projection_id": _content_id(
            "SP", {"stage04": stage04, "stage05": stage05, "stage06": stage06}
        ),
        "stage04": {"activation_lifecycle_fingerprint_sha256": "0" * 64, "activations": activations},
        "stage05": {
            "activation_lifecycle_fingerprint_sha256": "0" * 64,
            "burden_cycles": cycles,
            "provenance_event_dag": event_graph,
            "noetic_dependency_graph": noetic_graph,
            "closure_projection": closure,
        },
        "stage06": {
            "activation_lifecycle_fingerprint_sha256": "0" * 64,
            "activations": copy.deepcopy(activations),
            "burden_cycles": copy.deepcopy(cycles),
            "closure_projection": copy.deepcopy(closure),
            "normalized_activation_record": copy.deepcopy(nar),
        },
        "stage07": {
            "activation_lifecycle_fingerprint_sha256": "0" * 64,
            "activations": copy.deepcopy(activations),
            "burden_cycles": copy.deepcopy(cycles),
            "closure_projection": copy.deepcopy(closure),
            "normalized_activation_record": copy.deepcopy(nar),
            "semantic_body_hashes": {
                row["body_ref"]: row["semantic_body_sha256"] for row in activations
            },
            "T_lang": t_lang,
        },
        "non_claims": [
            "Structural parity does not establish semantic truth or guaranteed uptake.",
            "Stage04 ACT-row hashes do not establish full public-body provenance.",
        ],
    }
    fingerprint = activation_lifecycle_fingerprint(projection)
    for stage_name in ("stage04", "stage05", "stage06", "stage07"):
        projection[stage_name]["activation_lifecycle_fingerprint_sha256"] = fingerprint
    diagnostics = projection_diagnostics(projection)
    if diagnostics:
        first = diagnostics[0]
        raise CurrentWitnessError(
            f"Current Stage 07 projection failed {first['failure_subcode']}: {first['message']}"
        )
    return projection


def build_current_public_field_witness(
    historical: dict[str, Any], projection: dict[str, Any]
) -> dict[str, Any]:
    activations = projection["stage04"]["activations"]
    cycles = projection["stage05"]["burden_cycles"]
    cycle_by_burden = {row["burden_id"]: row for row in cycles}
    event_graph = projection["stage05"]["provenance_event_dag"]
    event_by_burden = {
        cycle["burden_id"]: event_graph["nodes"][index]
        for index, cycle in enumerate(cycles)
    }
    b_la = [row["burden_id"] for row in cycles if row["origin"] == "B_LA"]
    b_mrp = [row["burden_id"] for row in cycles if row["origin"] == "B_MRP"]
    b_total = [row["burden_id"] for row in cycles]
    dependency_graph = projection["stage05"]["noetic_dependency_graph"]
    historical_edges = {
        (_b_id(row.get("from")), _b_id(row.get("to"))): str(row.get("type") or "noetic-dependency")
        for row in historical.get("edges", [])
        if isinstance(row, dict)
    }
    edges = [
        {
            "from": row["from"],
            "to": row["to"],
            "relation_class": "noetic_dependency",
            "kind": historical_edges.get((row["from"], row["to"]), "noetic-dependency"),
        }
        for row in dependency_graph["edges"]
    ]
    nodes: list[dict[str, Any]] = []
    generated: list[dict[str, Any]] = []
    for cycle in cycles:
        node = {
            "id": cycle["burden_id"],
            "type": "generated_burden" if cycle["origin"] == "B_MRP" else "burden",
            "origin": cycle["origin"],
            "generation_depth": cycle["generation_depth"],
            "lifecycle_status": cycle["lifecycle_status"],
        }
        if cycle["parent_cycle_id"] is not None:
            parent = next(
                (row["burden_id"] for row in cycles if row["cycle_id"] == cycle["parent_cycle_id"]),
                None,
            )
            if parent is None:
                raise CurrentWitnessError(
                    f"Current public witness cycle {cycle['cycle_id']} has an unknown parent"
                )
            node["parent_id"] = parent
            if cycle["origin"] == "B_MRP":
                generated.append(
                    {
                        "id": cycle["burden_id"],
                        "source": parent,
                        "generation_depth": cycle["generation_depth"],
                        "event_id": event_by_burden[cycle["burden_id"]],
                    }
                )
        nodes.append(node)

    formal_by_burden = {
        _b_id(row.get("source_burden")): row
        for row in historical.get("formal_reread_states", [])
        if isinstance(row, dict) and _b_id(row.get("source_burden"))
    }
    resultants: list[dict[str, Any]] = []
    for edge in edges:
        target_cycle = cycle_by_burden[edge["to"]]
        if target_cycle["origin"] != "B_MRP" and edge["kind"] not in {
            "held_burden_activation",
            "held-burden-activation",
        }:
            continue
        expected_type = (
            "generated_burden_instantiation"
            if target_cycle["origin"] == "B_MRP"
            else edge["kind"].replace("-", "_")
        )
        formal_state = formal_by_burden.get(edge["from"], {})
        formal_type = str(formal_state.get("route_result_type") or "")
        formal_route = str(formal_state.get("route") or "").upper()
        if formal_type != expected_type or not formal_route:
            raise CurrentWitnessError(
                f"Current public witness edge {edge['from']}->{edge['to']} must preserve its Stage 05 route type and route"
            )
        resultants.append(
            {
                "source": edge["from"],
                "target": edge["to"],
                "type": formal_type,
                "route": formal_route,
            }
        )
    rereads = [
        {
            "burden_id": cycle["burden_id"],
            "cycle_id": cycle["cycle_id"],
            "route_result_type": str(
                formal_by_burden.get(cycle["burden_id"], {}).get("route_result_type")
                or "no_new_resultant"
            ),
            "terminal_state": cycle["terminal_state"],
        }
        for cycle in cycles
    ]
    closure = projection["stage05"]["closure_projection"]
    cycle_refs = [cycle["cycle_id"] for cycle in cycles]
    delta_ref = _content_id("D", {"cycles": cycles, "closure": closure})
    public_activations = [
        {
            "ordinal": row["ordinal"],
            "body_ref": row["body_ref"],
            "burden_id": row["burden_id"],
            "owner_id": row["owner_id"],
            "operation": row["operation"],
            "resultant_sha256": row["resultant_sha256"],
            "semantic_body_sha256": row["semantic_body_sha256"],
        }
        for row in activations
    ]
    graph = {
        "schema_version": "public-field-witness-v1",
        "B_LA": b_la,
        "B_MRP": b_mrp,
        "B_total": b_total,
        "nodes": nodes,
        "edges": edges,
        "generated_burdens": generated,
        "mrp_resultants": resultants,
        "reread_records": rereads,
        "formal_reread_states": historical.get("formal_reread_states", []),
        "field_diagnostics": {
            "divergence": {
                "operator": "div",
                "target": "field",
                "status": closure["divergence"],
                "basis_refs": cycle_refs,
                "delta_ref": delta_ref,
            },
            "curl": {
                "operator": "curl",
                "target": "dependency",
                "status": closure["curl"],
                "basis_refs": cycle_refs,
                "delta_ref": delta_ref,
                "cycle_refs": [] if closure["curl"] == "null" else cycle_refs,
                "loopbreak_ref": None,
            },
        },
        "terminal_states": {
            cycle["burden_id"]: {
                "state": cycle["terminal_state"],
                "cycle_id": cycle["cycle_id"],
            }
            for cycle in cycles
        },
        "closure": closure,
        "T_lang": projection["stage07"]["T_lang"],
        "non_claims": [
            "Structural validity does not establish semantic truth.",
            "T_lang is partial coupling and does not guarantee uptake.",
            "Stage04 ACT-row hashes do not establish full public-body provenance.",
        ],
        "owner_activations": public_activations,
        "owner_activation_ordering": {
            "rows": [
                {
                    "ordinal": row["ordinal"],
                    "body_ref": row["body_ref"],
                    "ordering_role": "required",
                    "ordering_group": None,
                }
                for row in public_activations
            ]
        },
        "normalized_activation_record": {
            "schema_version": "daee-nar-v2",
            "per_burden": projection["stage06"]["normalized_activation_record"]["per_burden"],
        },
        "coverage_proof": {
            "initial_burden_set": b_la,
            "terminal_states": {
                cycle["burden_id"]: cycle["terminal_state"] for cycle in cycles
            },
            "dependency_graph": dependency_graph,
            "provenance_event_dag": event_graph,
            "divergence_check": closure["divergence"],
            "curl_check": closure["curl"],
            "coverage_complete": closure["closure_confirmed"],
        },
        "activation_lifecycle_fingerprint_sha256": projection["stage07"][
            "activation_lifecycle_fingerprint_sha256"
        ],
    }
    role_errors = validate_role(graph, "public_graph", "current")
    if role_errors:
        first = role_errors[0]
        raise CurrentWitnessError(
            f"Current Stage 07 public witness failed {first.failure_subcode}: {first.message}"
        )
    integrity = public_graph_integrity_diagnostics(graph, compatibility="current")
    if integrity:
        first = integrity[0]
        raise CurrentWitnessError(
            f"Current Stage 07 public witness failed {first['failure_subcode']}: {first['message']}"
        )
    return graph
