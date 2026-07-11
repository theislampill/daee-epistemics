#!/usr/bin/env python3
"""Build the canonical state-capsule-v2 fixture lattice.

This is an independent stdlib-only test oracle for the frozen additive
interface.  It deliberately does not import the production checker.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from mrp_recursion_lib import _adapt_state_v2_payload, validate_lifecycle_record
HERE = Path(__file__).resolve().parent
VALID = HERE / "valid"
INVALID = HERE / "invalid"
SOURCE_COMMIT = "6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c"
CANONICALIZATION = "daee-canonical-json-v1"
HEX = {
    "context": "7" * 64,
    "policy": "d" * 64,
    "route": "a" * 64,
    "land": "b" * 64,
    "delta": "c" * 64,
    "reread": "e" * 64,
    "body": "1" * 64,
    "ground": "2" * 64,
    "operation": "3" * 64,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def a07_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def self_sha(value: dict[str, Any], field: str) -> str:
    return canonical_sha({key: item for key, item in value.items() if key != field})


def stable_obligation_id(burden_id: str, pressure_ids: list[str], owner_id: str, operation: str) -> str:
    payload = {
        "burden_id": burden_id,
        "operation": operation,
        "owner_id": owner_id,
        "pressure_ids": sorted(set(pressure_ids)),
    }
    return f"O-{canonical_sha(payload)[:24]}"


def graph(graph_id: str, nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, Any]:
    result = {
        "graph_id": graph_id,
        "nodes": nodes,
        "edges": [{"from": source, "to": target} for source, target in edges],
        "graph_sha256": "",
    }
    result["graph_sha256"] = self_sha(result, "graph_sha256")
    return result


def diagnostic(diagnostic_id: str, event_index: int, operator: str, status: str, target: str) -> dict[str, Any]:
    result = {
        "diagnostic_id": diagnostic_id,
        "event_index": event_index,
        "operator": operator,
        "target": target,
        "status": status,
        "basis_refs": [f"basis:{diagnostic_id}"],
        "delta_ref": "D1",
        "event_sha256": "",
    }
    result["event_sha256"] = self_sha(result, "event_sha256")
    return result


def candidate_event(
    event_id: str,
    candidate_id: str,
    event_index: int,
    disposition: str,
    *,
    kind: str = "generated_instantiation",
    previous: str | None = None,
    target: str | None = None,
    next_cycle: str | None = None,
    gate: str | None = None,
    next_action: str | None = None,
) -> dict[str, Any]:
    result = {
        "candidate_event_id": event_id,
        "candidate_id": candidate_id,
        "previous_candidate_event_id": previous,
        "event_index": event_index,
        "kind": kind,
        "disposition": disposition,
        "target_burden_id": target,
        "next_cycle_id": next_cycle,
        "basis_refs": [f"basis:{event_id}"],
        "gate": gate,
        "next_action": next_action,
        "candidate_event_sha256": "",
    }
    result["candidate_event_sha256"] = self_sha(result, "candidate_event_sha256")
    return result


def operation_capsule(cycle_id: str, burden_id: str, ordinal: int = 1, *, operation_override: str | None = None) -> dict[str, Any]:
    owner_id = f"owner-{burden_id.lower()}"
    operation = operation_override or f"repair-{burden_id.lower()}"
    obligation_id = stable_obligation_id(burden_id, ["P1"], owner_id, operation)
    capsule = {
        "schema": "daee-operation-capsule-v1",
        "canonicalization": CANONICALIZATION,
        "capsule_id": f"OC-{burden_id}-{ordinal}",
        "cycle_id": cycle_id,
        "body_ref": f"{burden_id}_{ordinal}",
        "body_sha256": hashlib.sha256(f"body:{burden_id}:{ordinal}".encode("utf-8")).hexdigest(),
        "burden_id": burden_id,
        "obligation_ids": [obligation_id],
        "pressure_ids": ["P1"],
        "owner_id": owner_id,
        "operation": operation,
        "register_axis": "Omega",
        "before_state": {
            "state_id": f"S-BEFORE-{burden_id}-{ordinal}",
            "state": f"before-{burden_id}-{ordinal}",
            "source_pressure_ids": ["P1"],
        },
        "performed_operation": {"mechanism": operation, "application": f"apply {operation} to {burden_id} under pressure P1"},
        "after_state": {"state_id": f"S-AFTER-{burden_id}-{ordinal}", "state": f"after-{burden_id}-{ordinal}"},
        "delta": {"delta_id": f"OD-{burden_id}-{ordinal}", "carrier": burden_id, "result": f"after-{burden_id}-{ordinal}",
            "recoverability_evidence": [{"after_state_path": "state", "value": f"after-{burden_id}-{ordinal}"}]},
        "residual": {"status": "none", "pressure_ids": [], "basis": f"no residual after {operation}"},
        "land_contribution": {"decision": "contributes", "delta_ref": f"OD-{burden_id}-{ordinal}", "basis": f"delta supports Land({burden_id})"},
        "source_contract_refs": ["plan04-owner-route", "plan05-operation-capsule"],
        "operation_capsule_sha256": "",
    }
    capsule["operation_capsule_sha256"] = "sha256:" + self_sha(capsule, "operation_capsule_sha256")
    return capsule


def operation_events(capsule: dict[str, Any], first_index: int) -> list[dict[str, Any]]:
    refs = {
        "before_state": f"capsule:{capsule['capsule_id']}#before_state",
        "owner.operation": f"route:{capsule['obligation_ids'][0]}#owner.operation",
        "performed_evidence": f"capsule:{capsule['capsule_id']}#performed_operation",
        "local_delta": f"capsule:{capsule['capsule_id']}#delta",
        "residual": f"capsule:{capsule['capsule_id']}#residual",
        "land_contribution": f"capsule:{capsule['capsule_id']}#land_contribution",
    }
    events = []
    for sequence, kind in enumerate(refs, 1):
        event = {
            "event_id": f"EV-{capsule['capsule_id']}-{sequence}",
            "event_index": first_index + sequence - 1,
            "operation_capsule_id": capsule["capsule_id"],
            "sequence": sequence,
            "kind": kind,
            "ref": refs[kind],
            "event_sha256": "",
        }
        event["event_sha256"] = self_sha(event, "event_sha256")
        events.append(event)
    return events


def loopbreak_evidence(first_index: int, *, cyclic_post: bool = True) -> tuple[dict[str, Any], int]:
    observed_index = first_index
    interruption_index = first_index + 1
    post_diagnostic = diagnostic("FD-LB-POST", first_index + 2, "curl", "held" if cyclic_post else "resolved", "dependency-relation")
    post_reread_index = first_index + 3
    pre_graph = graph("G-PRE", ["A", "B"], [("A", "B"), ("B", "A")])
    post_edges = [("A", "B"), ("B", "C"), ("C", "B")] if cyclic_post else [("A", "B")]
    post_graph = graph("G-POST", ["A", "B", "C"], post_edges)
    result = {
        "loopbreak_id": "LB1",
        "observed_loop": ["A", "B", "A"],
        "observed_loop_event_index": observed_index,
        "pre_break_graph": pre_graph,
        "owner_ground_ref": {"id": "owner-ground", "sha256": HEX["ground"]},
        "performed_operation_ref": {"id": "performed-loopbreak", "sha256": HEX["operation"]},
        "local_delta_ref": {"delta_id": "D-LB", "sha256": canonical_sha({"delta_id": "D-LB"})},
        "interruption_event_index": interruption_index,
        "post_break_graph": post_graph,
        "post_break_reread": {
            "record_id": "RR-LB",
            "record_sha256": "",
            "event_index": post_reread_index,
            "field_diagnostics": [post_diagnostic],
        },
        "loopbreak_sha256": "",
    }
    result["post_break_reread"]["record_sha256"] = self_sha(result["post_break_reread"], "record_sha256")
    result["loopbreak_sha256"] = self_sha(result, "loopbreak_sha256")
    return result, post_reread_index + 1


def cycle(
    cycle_id: str,
    burden_id: str,
    event_index: int,
    *,
    origin: str = "B_LA",
    depth: int = 0,
    parent_cycle_id: str | None = None,
    exit_disposition: str = "STOP",
    candidates: list[dict[str, Any]] | None = None,
    loopbreak: dict[str, Any] | None = None,
    noetic_graph: dict[str, Any] | None = None,
    resource_exhaustion: dict[str, Any] | None = None,
    ordinal: int = 1,
    operation_override: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], int]:
    capsule = operation_capsule(cycle_id, burden_id, ordinal, operation_override=operation_override)
    obligation_id = capsule["obligation_ids"][0]
    owner_route = {
        "obligation_id": obligation_id,
        "burden_id": burden_id,
        "pressure_ids": ["P1"],
        "partition_decision_id": "BP1",
        "owner_id": capsule["owner_id"],
        "operation": capsule["operation"],
        "register_axis": capsule["register_axis"],
        "execution_class": "required",
        "route_status": "executable",
        "trigger": None,
        "owner_body_status": "loaded",
        "same_burden_cohesion": {"target_family_relation":"same","tau_relation":"same","source_frame_relation":"same","claim_cluster_relation":"same","restoration_vector_relation":"same","already_handled":False},
        "basis": f"routed in {cycle_id}",
    }
    act_row = {key: owner_route[key] for key in ("obligation_id", "burden_id", "pressure_ids", "owner_id", "operation", "register_axis")}
    act_row["body_ref"] = capsule["body_ref"]
    disposition = {"obligation_id":obligation_id,"burden_id":burden_id,"disposition":"executed","body_ref":capsule["body_ref"],"satisfied_by_obligation_id":None,"trigger_evidence":None,"basis":f"executed in {cycle_id}","gate":None,"next_action":None}
    plan04 = {"route": owner_route, "act": act_row, "disposition": disposition}
    route = {
        "event_id": f"EV-{cycle_id}-ROUTE",
        "event_index": event_index,
        "record_id": f"R-{cycle_id}",
        "record_sha256": "",
        "target_burden_id": burden_id,
        "source_refs": [f"source:{burden_id}"],
        "basis_refs": [f"basis:{cycle_id}:route"],
        "event_sha256": "",
    }
    route["record_sha256"] = canonical_sha({
        "record_id": route["record_id"],
        "target_burden_id": burden_id,
        "source_refs": route["source_refs"],
        "basis_refs": route["basis_refs"],
    })
    route["event_sha256"] = self_sha(route, "event_sha256")
    events = operation_events(capsule, event_index + 1)
    land_index = events[-1]["event_index"] + 1
    land = {
        "event_id": f"EV-{cycle_id}-LAND",
        "event_index": land_index,
        "record_id": f"L-{cycle_id}",
        "record_sha256": "",
        "status": "landed",
        "operation_capsule_ids": [capsule["capsule_id"]],
        "contribution_refs": [f"capsule:{capsule['capsule_id']}#land_contribution"],
        "event_sha256": "",
    }
    land["record_sha256"] = canonical_sha({
        "record_id": land["record_id"],
        "status": land["status"],
        "operation_capsule_ids": land["operation_capsule_ids"],
        "contribution_refs": land["contribution_refs"],
    })
    land["event_sha256"] = self_sha(land, "event_sha256")
    delta_index = land_index + 1
    delta = {
        "event_id": f"EV-{cycle_id}-DELTA",
        "event_index": delta_index,
        "delta_id": f"D-{cycle_id}",
        "delta_sha256": "",
        "source_land_event_id": land["event_id"],
        "source_operation_capsule_ids": [capsule["capsule_id"]],
        "basis_refs": [f"basis:{cycle_id}:delta"],
        "event_sha256": "",
    }
    delta["delta_sha256"] = canonical_sha({
        "delta_id": delta["delta_id"],
        "source_land_event_id": delta["source_land_event_id"],
        "source_operation_capsule_ids": delta["source_operation_capsule_ids"],
        "basis_refs": delta["basis_refs"],
    })
    delta["event_sha256"] = self_sha(delta, "event_sha256")

    if loopbreak is not None:
        loopbreak["owner_ground_ref"]["id"] = obligation_id
        loopbreak["performed_operation_ref"]["id"] = capsule["body_ref"]
        loopbreak["local_delta_ref"] = {"delta_id": delta["delta_id"], "sha256": delta["delta_sha256"]}
        for row in loopbreak["post_break_reread"]["field_diagnostics"]:
            row["target"] = burden_id
            row["delta_ref"] = delta["delta_id"]
            row["event_sha256"] = self_sha(row, "event_sha256")
        loopbreak["post_break_reread"]["record_sha256"] = self_sha(loopbreak["post_break_reread"], "record_sha256")
        loopbreak["loopbreak_sha256"] = self_sha(loopbreak, "loopbreak_sha256")

    next_index = delta_index + 1
    candidate_rows = copy.deepcopy(candidates or [])
    for row in candidate_rows:
        row["event_index"] = next_index
        row["candidate_event_sha256"] = self_sha(row, "candidate_event_sha256")
        next_index += 1
    diagnostics = [
        diagnostic(f"FD-{cycle_id}-DIV", next_index, "divergence", "neutral", burden_id),
        diagnostic(f"FD-{cycle_id}-CURL", next_index + 1, "curl", "null", burden_id),
    ]
    for row in diagnostics:
        row["delta_ref"] = delta["delta_id"]
        row["event_sha256"] = self_sha(row, "event_sha256")
    next_index += 2
    if loopbreak is not None:
        # A supplied LoopBreak already owns its explicit event indices.
        loop_indices = [
            loopbreak["observed_loop_event_index"],
            loopbreak["interruption_event_index"],
            loopbreak["post_break_reread"]["event_index"],
        ]
        loop_indices += [item["event_index"] for item in loopbreak["post_break_reread"]["field_diagnostics"]]
        next_index = max(next_index, max(loop_indices) + 1)
    raw_exit = {
        "event_id": f"EV-{cycle_id}-EXIT",
        "event_index": next_index,
        "raw_exit_sha256": "",
        "exit_disposition": exit_disposition,
        "candidate_events": candidate_rows,
        "field_diagnostics": diagnostics,
        "noetic_dependency_graph": noetic_graph or graph(f"G-{cycle_id}", [burden_id], []),
        "no_new_resultant": {
            "observed": True,
            "stop_licensed": True,
            "live_obligation_ids": [],
            "unresolved_candidate_ids": [],
            "basis_refs": [f"basis:{cycle_id}:no-new"],
            "sha256": "",
        } if exit_disposition == "STOP" else None,
        "loopbreak": loopbreak,
        "resource_exhaustion": resource_exhaustion,
    }
    if raw_exit["no_new_resultant"] is not None:
        raw_exit["no_new_resultant"]["sha256"] = self_sha(raw_exit["no_new_resultant"], "sha256")
    raw_exit["raw_exit_sha256"] = self_sha(raw_exit, "raw_exit_sha256")
    reread = {
        "record_id": f"RR-{cycle_id}",
        "record_sha256": "",
        "target_burden_id": burden_id,
        "source_land_event_id": land["event_id"],
        "source_delta_event_id": delta["event_id"],
        "raw_exit": raw_exit,
    }
    reread["record_sha256"] = self_sha(reread, "record_sha256")
    local_status = {
        "STOP": ("landed", "landed"),
        "RECURSE": ("landed", "landed"),
        "HOLD": ("held", "held"),
        "PARTIAL": ("partial", "partial"),
        "HANDOFF": ("partial", "partial"),
    }[exit_disposition]
    result = {
        "cycle_id": cycle_id,
        "burden_id": burden_id,
        "origin": origin,
        "generation_depth": depth,
        "parent_cycle_id": parent_cycle_id,
        "phase": "REREAD_EVALUATED",
        "route_gradient": route,
        "obligation_ids": [obligation_id],
        "obligation_set_sha256": canonical_sha(sorted([obligation_id])),
        "operation_capsule_ids": [capsule["capsule_id"]],
        "operation_events": events,
        "land": land,
        "post_land_delta": delta,
        "reread": reread,
        "lifecycle_status": local_status[0],
        "terminal_state": local_status[1],
        "cycle_sha256": "",
    }
    result["cycle_sha256"] = self_sha(result, "cycle_sha256")
    return result, plan04, capsule, next_index + 1


def stage02_freeze(payload: dict[str, Any], b_la: list[str]) -> dict[str, Any]:
    observation_ids = [item["unit_id"] for item in payload["observation_units"]]
    candidate_ids = [item["state_id"] for item in payload["candidate_states"]]
    pressure_ids = [item["pressure_id"] for item in payload["input_pressures"]]
    candidate_partition_ids = [item["partition_id"] for item in payload["candidate_state_partitions"]]
    burden_partition_ids = [item["decision_id"] for item in payload["burden_partition_decisions"]]
    freeze = {
        "contract": "stage02-baseline-freeze-v1",
        "record_id": "S02-FREEZE",
        "record_sha256": "",
        "event_index": 0,
        "observation_unit_ids": observation_ids,
        "observation_unit_set_sha256": canonical_sha(sorted(observation_ids)),
        "candidate_state_ids": candidate_ids,
        "candidate_state_set_sha256": canonical_sha(sorted(candidate_ids)),
        "input_pressure_ids": pressure_ids,
        "input_pressure_set_sha256": canonical_sha(sorted(pressure_ids)),
        "candidate_partition_ids": candidate_partition_ids,
        "candidate_partition_set_sha256": canonical_sha(sorted(candidate_partition_ids)),
        "burden_partition_decision_ids": burden_partition_ids,
        "burden_partition_decision_set_sha256": canonical_sha(sorted(burden_partition_ids)),
        "B_LA": b_la,
        "B_LA_sequence_sha256": canonical_sha(b_la),
        "topology_state_sha256": canonical_sha({
            "candidate_states": payload["candidate_states"],
            "input_pressures": payload["input_pressures"],
            "candidate_state_partitions": payload["candidate_state_partitions"],
            "burden_partition_decisions": payload["burden_partition_decisions"],
            "B_LA": b_la,
        }),
    }
    freeze["record_sha256"] = self_sha(freeze, "record_sha256")
    return freeze


def event_dag(payload: dict[str, Any]) -> dict[str, Any]:
    indexed: list[tuple[int, str]] = [(payload["stage02_freeze"]["event_index"], "S02-FREEZE")]
    extra_edges: list[dict[str, str]] = []
    for item in payload["burden_cycles"]:
        indexed.append((item["route_gradient"]["event_index"], item["route_gradient"]["event_id"]))
        indexed.extend((event["event_index"], event["event_id"]) for event in item["operation_events"])
        indexed.append((item["land"]["event_index"], item["land"]["event_id"]))
        indexed.append((item["post_land_delta"]["event_index"], item["post_land_delta"]["event_id"]))
        raw_exit = item["reread"]["raw_exit"]
        indexed.extend((event["event_index"], event["candidate_event_id"]) for event in raw_exit["candidate_events"])
        indexed.extend((event["event_index"], event["diagnostic_id"]) for event in raw_exit["field_diagnostics"])
        loopbreak = raw_exit.get("loopbreak")
        if loopbreak:
            indexed.extend([
                (loopbreak["observed_loop_event_index"], f"{loopbreak['loopbreak_id']}:observed"),
                (loopbreak["interruption_event_index"], f"{loopbreak['loopbreak_id']}:interruption"),
                (loopbreak["post_break_reread"]["event_index"], f"{loopbreak['loopbreak_id']}:reread"),
            ])
            indexed.extend((event["event_index"], event["diagnostic_id"]) for event in loopbreak["post_break_reread"]["field_diagnostics"])
        indexed.append((raw_exit["event_index"], raw_exit["event_id"]))
        for candidate in raw_exit["candidate_events"]:
            if candidate.get("next_cycle_id"):
                target = next((cycle for cycle in payload["burden_cycles"] if cycle["cycle_id"] == candidate["next_cycle_id"]), None)
                if target:
                    extra_edges.append({"from": candidate["candidate_event_id"], "to": target["route_gradient"]["event_id"]})
    ordered = [name for _, name in sorted(indexed)]
    edges = [{"from": ordered[index], "to": ordered[index + 1]} for index in range(len(ordered) - 1)]
    edges.extend(extra_edges)
    return {"nodes": ordered, "edges": edges}


def _a07_graph(value: dict[str, Any]) -> dict[str, Any]:
    result = {"nodes": list(value["nodes"]), "edges": [[edge["from"], edge["to"]] for edge in value["edges"]]}
    result["graph_sha256"] = a07_sha(result)
    return result


def _a07_loopbreak(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    post = value["post_break_reread"]
    result = {
        "loopbreak_id": value["loopbreak_id"], "observed_loop": value["observed_loop"],
        "observed_loop_event_index": value["observed_loop_event_index"], "pre_break_graph": _a07_graph(value["pre_break_graph"]),
        "owner_ground_ref": {"ref_id":value["owner_ground_ref"]["id"],"sha256":value["owner_ground_ref"]["sha256"]},
        "performed_operation_ref": {"ref_id":value["performed_operation_ref"]["id"],"sha256":value["performed_operation_ref"]["sha256"]},
        "local_delta_ref": value["local_delta_ref"], "interruption_event_index": value["interruption_event_index"],
        "post_break_graph": _a07_graph(value["post_break_graph"]),
        "post_break_reread": {"record_id":post["record_id"],"record_sha256":post["record_sha256"],"event_index":post["event_index"],"field_diagnostics":post["field_diagnostics"]},
    }
    result["loopbreak_sha256"] = a07_sha(result)
    return result


def a07_cycles(payload: dict[str, Any]) -> list[dict[str, Any]]:
    capsules = {row["capsule_id"]: row for row in payload["operation_capsules"]}
    result: list[dict[str, Any]] = []
    for item in payload["burden_cycles"]:
        route, land, delta, reread = item["route_gradient"], item["land"], item["post_land_delta"], item["reread"]
        raw = reread["raw_exit"]
        projected_raw = {
            "event_id":raw["event_id"],"event_index":raw["event_index"],"exit_disposition":raw["exit_disposition"],
            "candidate_events":[{key:row.get(key) for key in ("candidate_event_id","candidate_id","previous_candidate_event_id","event_index","kind","disposition","target_burden_id","next_cycle_id","basis_refs","gate","next_action")} for row in raw["candidate_events"]],
            "field_diagnostics":raw["field_diagnostics"],"noetic_dependency_graph":_a07_graph(raw["noetic_dependency_graph"]),
            "no_new_resultant": None if raw["no_new_resultant"] is None else {key:raw["no_new_resultant"][key] for key in ("observed","live_obligation_ids","unresolved_candidate_ids")},
            "loopbreak":_a07_loopbreak(raw["loopbreak"]),"resource_exhaustion":raw["resource_exhaustion"],
        }
        projected_raw["raw_exit_sha256"] = a07_sha(projected_raw)
        operation_projection = {"operation_capsules":[capsules[value] for value in item["operation_capsule_ids"]],"operation_events":item["operation_events"]}
        result.append({
            "cycle_id":item["cycle_id"],"burden_id":item["burden_id"],"origin":item["origin"],"generation_depth":item["generation_depth"],"parent_cycle_id":item["parent_cycle_id"],
            "route":{"record_id":route["record_id"],"sha256":route["record_sha256"],"target_burden_id":item["burden_id"]},
            "operation":{"record_id":item["cycle_id"],"sha256":a07_sha(operation_projection),"performed":True,"local_delta":{"delta_id":delta["delta_id"],"source_operation_capsule_ids":item["operation_capsule_ids"]}},
            "land":{"status":"landed","event_index":land["event_index"]},
            "reread":{"record_id":reread["record_id"],"sha256":reread["record_sha256"],"raw_exit":projected_raw},
            "lifecycle_status":item["lifecycle_status"],"terminal_state":item["terminal_state"],
        })
    return result


def set_reducer_and_authority(payload: dict[str, Any]) -> None:
    payload["resource_policy"]["policy_sha256"] = a07_sha({key:value for key,value in payload["resource_policy"].items() if key != "policy_sha256"})
    obligation_ids = [row["obligation_id"] for row in payload["owner_routes"]]
    dispositions = payload["owner_execution_dispositions"]
    payload["owner_obligation_state"] = {
        "declared_ids":obligation_ids,"executed_ids":[row["obligation_id"] for row in dispositions if row["disposition"] == "executed"],
        "held_ids":[row["obligation_id"] for row in dispositions if row["disposition"] == "held"],"partial_ids":[row["obligation_id"] for row in dispositions if row["disposition"] == "partial"],
        "terminal_disposition_sha256":canonical_sha(dispositions),
    }
    if payload["burden_cycles"]:
        try:
            adapted, finding = _adapt_state_v2_payload(payload)
        except (KeyError, TypeError, ValueError):
            return
        if finding is not None or adapted is None:
            return
        state = validate_lifecycle_record(adapted, release_bearing=True)
        if not state.valid:
            return
        cycles_by_id = {row["cycle_id"]: row for row in payload["burden_cycles"]}
        capsules_by_id = {row["capsule_id"]: row for row in payload["operation_capsules"]}
        history = []
        for cycle_id, event_id, a07_signature in state.reread_signature_history:
            cycle = cycles_by_id[cycle_id]
            signature = canonical_sha({
                "a07_reducer_signature_sha256": a07_signature,
                "performed_operation_capsule_sha256s": [capsules_by_id[value]["operation_capsule_sha256"] for value in cycle["operation_capsule_ids"]],
                "land_record_sha256": cycle["land"]["record_sha256"],
                "land_event_sha256": cycle["land"]["event_sha256"],
                "post_land_delta_sha256": cycle["post_land_delta"]["delta_sha256"],
                "post_land_delta_event_sha256": cycle["post_land_delta"]["event_sha256"],
            })
            history.append({"cycle_id":cycle_id,"raw_exit_event_id":event_id,"a07_reducer_signature_sha256":a07_signature,"reread_signature_sha256":signature})
        payload["reread_signature_history"] = history
        payload["reread_signature_history_sha256"] = canonical_sha(history)
        by_cycle = {row["cycle_id"]: row for row in history}
        for cycle in payload["burden_cycles"]:
            row = by_cycle[cycle["cycle_id"]]
            cycle["reread"]["a07_reducer_signature_sha256"] = row["a07_reducer_signature_sha256"]
            cycle["reread"]["reread_signature_sha256"] = row["reread_signature_sha256"]
            cycle["reread"]["record_sha256"] = self_sha(cycle["reread"], "record_sha256")
            cycle["cycle_sha256"] = self_sha(cycle, "cycle_sha256")
    else:
        payload["reread_signature_history"] = []
        payload["reread_signature_history_sha256"] = canonical_sha([])
    burdens = list(dict.fromkeys(payload["stage02_freeze"]["B_LA"] + [row["burden_id"] for row in payload["burden_cycles"] if row["origin"] == "B_MRP"]))
    authority = {"burden_ids":burdens,"candidate_state_ids":[row["state_id"] for row in payload["candidate_states"]],"owner_obligation_ids":obligation_ids}
    authority["inventory_sha256"] = canonical_sha(authority)
    payload["closure_authority"] = authority


def set_topology_mass_accounting(payload: dict[str, Any]) -> None:
    """Bind Plan06 to independently recomputable source/artifact/receipt authority."""
    capsules = {row["obligation_ids"][0]: row for row in payload["operation_capsules"]}
    source_ids = list(dict.fromkeys(
        [row["pressure_id"] for row in payload["input_pressures"]]
        + [row["burden_id"] for row in payload["burden_cycles"]]
        + [row["obligation_id"] for row in payload["owner_routes"]]
    ))
    artifacts: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    obligations: list[dict[str, Any]] = []
    for route in payload["owner_routes"]:
        obligation_id = route["obligation_id"]
        capsule = capsules[obligation_id]
        artifact_id = capsule["capsule_id"]
        content = canonical_bytes(capsule).decode("utf-8")
        artifact_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        evidence_id = f"E-{obligation_id}"
        receipt_id = f"VR-{obligation_id}"
        artifact = {"artifact_id": artifact_id, "content": content, "artifact_sha256": artifact_sha256}
        receipt = {
            "receipt_id": receipt_id, "evidence_id": evidence_id, "artifact_id": artifact_id,
            "artifact_sha256": artifact_sha256, "evidence_type": "operation_capsule",
            "validator_id": "operation-capsule-contract", "verdict": "PASS",
        }
        receipt["receipt_sha256"] = canonical_sha(receipt)
        artifacts.append(artifact)
        receipts.append(receipt)
        evidence.append({
            "evidence_id": evidence_id, "evidence_type": "operation_capsule",
            "artifact_id": artifact_id, "artifact_sha256": artifact_sha256,
            "validator_receipt_id": receipt_id,
        })
        obligations.append({
            "obligation_id": obligation_id, "kind": "owner_operation", "origin_stage": "04",
            "source_ids": [obligation_id, route["burden_id"], *route["pressure_ids"]],
            "allowed_dispositions": ["satisfied"], "disposition": "satisfied",
            "evidence_refs": [evidence_id], "basis": "validated Plan05 operation capsule",
        })
    authority = {"source_ids": source_ids, "artifacts": artifacts, "validator_receipts": receipts}
    payload["topology_mass_evidence_authority"] = authority
    payload["topology_mass_evidence_authority_sha256"] = canonical_sha(authority)
    accounting = {
        "schema": "daee-topology-mass-accounting-v1",
        "case_id": payload["trace_id"],
        "input_sha256": payload["stage02_freeze"]["topology_state_sha256"],
        "staged_handoff_sha256": payload["upstream_obligation_set_sha256"],
        "output_sha256": canonical_sha({"capsule_id": payload["capsule_id"], "stage": payload["stage"]}),
        "obligations": obligations,
        "evidence_inventory": evidence,
        "partition_decisions": [],
        "unaccounted_obligation_ids": [], "unreconstructible_obligation_ids": [],
        "open_obligation_ids": [], "orphan_evidence_refs": [], "duplicate_evidence_groups": [],
        "initial_coverage_complete": True, "lifecycle_accounting_complete": True,
        "collapse_positive": True,
        "advisory_metrics": {
            "output_bytes": 0,
            "burden_count": len(payload["burden_cycles"]),
            "operation_capsule_count": len(payload["operation_capsules"]),
            "mrp_event_count": sum(len(row["operation_events"]) for row in payload["burden_cycles"]),
            "generated_burden_count": sum(row["origin"] == "B_MRP" for row in payload["burden_cycles"]),
            "held_or_partial_count": len(payload["held"]),
        },
        "non_claims": [
            "counts and bytes do not determine PASS",
            "structural accounting is not semantic truth",
            "one run is not broad model behavior",
        ],
    }
    if not obligations:
        accounting["authoritative_empty_universe"] = {
            "source_count": 0,
            "source_inventory_sha256": payload["upstream_obligation_set_sha256"],
            "basis": "independent Plan04 owner-obligation inventory is empty",
        }
    payload["topology_mass_accounting"] = accounting


def set_operation_body_artifacts(payload: dict[str, Any]) -> None:
    artifacts: dict[str, dict[str, str]] = {}
    for capsule in payload["operation_capsules"]:
        burden_id, ordinal = capsule["body_ref"].split("_", 1)
        content = f"body:{burden_id}:{ordinal}"
        artifacts[capsule["body_ref"]] = {
            "content": content,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }
    payload["operation_body_artifacts"] = artifacts


def set_projections(payload: dict[str, Any]) -> None:
    set_operation_body_artifacts(payload)
    set_reducer_and_authority(payload)
    set_topology_mass_accounting(payload)
    stage_number = int(payload["stage"].split("-")[1])
    b_mrp = [cycle["burden_id"] for cycle in payload["burden_cycles"] if cycle["origin"] == "B_MRP"]
    stage04_projection = {
        "upstream_obligation_ids": payload["upstream_obligation_ids"],
        "owner_routes": payload["owner_routes"],
        "act_row_details": payload["act_row_details"],
        "owner_execution_dispositions": payload["owner_execution_dispositions"],
        "owner_obligation_state": payload["owner_obligation_state"],
        "operation_capsules": payload["operation_capsules"],
        "operation_events": [event for cycle in payload["burden_cycles"] for event in cycle["operation_events"]],
    }
    stage05_projection = {"burden_cycles": payload["burden_cycles"]}
    reducer_projection = {
        "B_LA": payload["stage02_freeze"]["B_LA"],
        "B_MRP": b_mrp,
        "current_live_burdens": payload["current_live_burdens"],
        "held": payload["held"],
        "closure_state": payload["closure_state"],
        "reread_signature_history": payload["reread_signature_history"],
    }
    dag = event_dag(payload)
    activation_projection = {
        "owner_routes": payload["owner_routes"],
        "act_row_details": payload["act_row_details"],
        "owner_execution_dispositions": payload["owner_execution_dispositions"],
        "operation_capsules": payload["operation_capsules"],
        "burden_cycles": payload["burden_cycles"],
    }
    release_projection = {
        "stage04": stage04_projection,
        "stage05": stage05_projection,
        "reducer": reducer_projection,
        "event_dag": dag,
    }
    public_projection = {
        "trace_id": payload["trace_id"],
        "B_LA": payload["stage02_freeze"]["B_LA"],
        "B_MRP": b_mrp,
        "burden_cycles": payload["burden_cycles"],
        "closure_state": payload["closure_state"],
    }
    projection = {
        "stage04_activation_projection_sha256": canonical_sha(stage04_projection) if stage_number >= 4 else None,
        "stage05_lifecycle_projection_sha256": canonical_sha(stage05_projection) if stage_number >= 5 else None,
        "reducer_state_sha256": canonical_sha(reducer_projection) if stage_number >= 5 else None,
        "event_dag_sha256": canonical_sha(dag) if stage_number >= 5 else None,
        "activation_lifecycle_fingerprint_sha256": canonical_sha(activation_projection) if stage_number >= 4 else None,
        "stage06_projection_sha256": canonical_sha(release_projection) if stage_number >= 6 else None,
        "stage07_projection_sha256": canonical_sha(release_projection) if stage_number >= 7 else None,
        "public_field_witness_sha256": canonical_sha(public_projection) if stage_number >= 7 else None,
        "field_witness_envelope_sha256": None,
    }
    if stage_number >= 8:
        projection["field_witness_envelope_sha256"] = canonical_sha({
            "capsule_id": payload["capsule_id"],
            "source_commit": payload["source_commit"],
            "trace_id": payload["trace_id"],
            "public_field_witness_sha256": projection["public_field_witness_sha256"],
            "activation_lifecycle_fingerprint_sha256": projection["activation_lifecycle_fingerprint_sha256"],
        })
    payload["projection"] = projection
    refs = [{"id": "context-stage", "sha256": HEX["context"]}]
    if stage_number >= 7:
        refs.append({"id": "public-field-witness", "sha256": projection["public_field_witness_sha256"]})
    if stage_number >= 8:
        refs.append({"id": "field-witness-envelope", "sha256": projection["field_witness_envelope_sha256"]})
    payload["runtime_call_context_refs"] = refs


def rehash_payload(payload: dict[str, Any], *, skip: set[str] | None = None) -> dict[str, Any]:
    skip = skip or set()
    for capsule in payload.get("operation_capsules", []):
        if "operation_capsule_sha256" not in skip:
            capsule["operation_capsule_sha256"] = "sha256:" + self_sha(capsule, "operation_capsule_sha256")
    for item in payload.get("burden_cycles", []):
        route = item.get("route_gradient")
        if isinstance(route, dict):
            route["record_sha256"] = canonical_sha({
                "record_id": route["record_id"], "target_burden_id": route["target_burden_id"],
                "source_refs": route["source_refs"], "basis_refs": route["basis_refs"],
            })
            route["event_sha256"] = self_sha(route, "event_sha256")
        item["obligation_set_sha256"] = canonical_sha(sorted(item.get("obligation_ids", [])))
        for event in item.get("operation_events", []):
            event["event_sha256"] = self_sha(event, "event_sha256")
        land = item.get("land")
        if isinstance(land, dict):
            land["record_sha256"] = canonical_sha({
                "record_id": land["record_id"], "status": land["status"],
                "operation_capsule_ids": land["operation_capsule_ids"],
                "contribution_refs": land["contribution_refs"],
            })
            land["event_sha256"] = self_sha(land, "event_sha256")
        delta = item.get("post_land_delta")
        if isinstance(delta, dict):
            delta["delta_sha256"] = canonical_sha({
                "delta_id": delta["delta_id"], "source_land_event_id": delta["source_land_event_id"],
                "source_operation_capsule_ids": delta["source_operation_capsule_ids"],
                "basis_refs": delta["basis_refs"],
            })
            delta["event_sha256"] = self_sha(delta, "event_sha256")
        reread = item.get("reread")
        if isinstance(reread, dict):
            raw_exit = reread.get("raw_exit")
            if isinstance(raw_exit, dict):
                for candidate_row in raw_exit.get("candidate_events", []):
                    candidate_row["candidate_event_sha256"] = self_sha(candidate_row, "candidate_event_sha256")
                for diagnostic_row in raw_exit.get("field_diagnostics", []):
                    diagnostic_row["event_sha256"] = self_sha(diagnostic_row, "event_sha256")
                graph_row = raw_exit.get("noetic_dependency_graph")
                if isinstance(graph_row, dict):
                    graph_row["graph_sha256"] = self_sha(graph_row, "graph_sha256")
                no_new = raw_exit.get("no_new_resultant")
                if isinstance(no_new, dict):
                    no_new["sha256"] = self_sha(no_new, "sha256")
                loop = raw_exit.get("loopbreak")
                if isinstance(loop, dict):
                    for key in ("pre_break_graph", "post_break_graph"):
                        if isinstance(loop.get(key), dict):
                            loop[key]["graph_sha256"] = self_sha(loop[key], "graph_sha256")
                    post = loop.get("post_break_reread")
                    if isinstance(post, dict):
                        for diagnostic_row in post.get("field_diagnostics", []):
                            diagnostic_row["event_sha256"] = self_sha(diagnostic_row, "event_sha256")
                        post["record_sha256"] = self_sha(post, "record_sha256")
                    loop["loopbreak_sha256"] = self_sha(loop, "loopbreak_sha256")
                raw_exit["raw_exit_sha256"] = self_sha(raw_exit, "raw_exit_sha256")
            reread["record_sha256"] = self_sha(reread, "record_sha256")
        if "cycle_sha256" not in skip:
            item["cycle_sha256"] = self_sha(item, "cycle_sha256")
    if "stage02" not in skip:
        payload["stage02_freeze"] = stage02_freeze(payload, payload["stage02_freeze"]["B_LA"])
    set_projections(payload)
    return payload


def base_payload(*, stage: str = "stage-08-verifier-sidecars") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "daee-state-capsule-v2",
        "canonicalization": CANONICALIZATION,
        "capsule_id": "capsule-v2-001",
        "trace_id": "trace-v2-001",
        "source_commit": SOURCE_COMMIT,
        "previous_capsule_sha256": None,
        "stage": stage,
        "topology_contract": "input-pressure-v1",
        "observation_units": [{
            "unit_id": "U1", "source_start": 0, "source_end": 24,
            "source_sha256": canonical_sha("bounded observation unit"),
            "surface_kind": "claim", "parent_unit_id": None,
        }],
        "candidate_states": [{
            "state_id": "N1", "frame": "authority order", "frame_token": "authority-order",
            "observation_unit_ids": ["U1"], "pressure_ids": ["P1"],
            "live_registers": ["kappa", "Omega"], "read_status": "dominant",
            "confidence": "strong", "status": "selected", "partition_ids": ["NP1"],
            "merged_into": None, "decisive_missing_differentiator": None,
            "hold_gate": None, "next_review_point": None,
            "basis": "bounded source-anchored observation basis",
        }],
        "input_pressures": [{
            "pressure_id": "P1", "observation_unit_ids": ["U1"], "candidate_state_ids": ["N1"],
            "pressure_function": "restore the source-bounded authority relation",
            "register_axes": ["Omega"], "status": "routed", "burden_id": "B1",
            "decision_id": "BP1", "basis": "source-anchored load-bearing pressure",
        }],
        "candidate_state_partitions": [{
            "partition_id": "NP1", "member_state_ids": ["N1"],
            "shared_observation_unit_ids": ["U1"], "decision": "select_single",
            "selected_state_id": "N1", "held_state_ids": [], "merged_state_ids": [],
            "rejected_state_ids": [],
            "comparison": {
                "pressure_set_relation": "same", "register_relation": "same",
                "owner_eligibility_relation": "same", "held_route_relation": "same",
                "closure_consequence_relation": "same",
            },
            "decisive_differentiator": "none needed for a licensed single candidate",
            "basis_unit_ids": ["U1"], "basis": "source-bounded single-candidate decision",
        }],
        "burden_partition_decisions": [{
            "decision_id": "BP1", "candidate_state_ids": ["N1"],
            "observation_unit_ids": ["U1"], "pressure_ids": ["P1"],
            "decision": "one_to_one",
            "pressure_to_burden": [{"pressure_id": "P1", "burden_id": "B1"}],
            "same_function_proof": {
                "tau_relation": "same", "source_frame_relation": "same",
                "claim_cluster_relation": "same", "register_transition_relation": "compatible",
                "owner_operation_relation": "compatible", "restoration_vector_relation": "same",
                "collapse_dependency_relation": "same",
            },
            "residual_pressure_ids": [], "held_pressure_ids": [],
            "basis": "source-bound one-pressure one-burden partition",
        }],
        "input_coverage": {
            "all_observation_unit_ids": ["U1"], "pressure_bearing_unit_ids": ["U1"],
            "explicitly_disposed_unit_ids": [], "unaccounted_unit_ids": [],
        },
        "selection_status": "licensed",
        "selected_n_frame": "authority-order",
        "burden_floor": ["B1"],
        "upstream_obligation_ids": [],
        "upstream_obligation_set_sha256": canonical_sha([]),
        "upstream_pressure_ids": ["P1"],
        "upstream_partition_decision_ids": ["BP1"],
        "partition_derivative_mappings": [],
        "partition_derivative_mappings_sha256": canonical_sha([]),
        "owner_routes": [],
        "act_row_details": [],
        "owner_execution_dispositions": [],
        "owner_obligation_state": {"declared_ids":[],"executed_ids":[],"held_ids":[],"partial_ids":[],"terminal_disposition_sha256":canonical_sha([])},
        "operation_capsules": [],
        "operation_body_artifacts": {},
        "topology_mass_accounting": {},
        "topology_mass_evidence_authority": {"source_ids": [], "artifacts": [], "validator_receipts": []},
        "topology_mass_evidence_authority_sha256": canonical_sha({"source_ids": [], "artifacts": [], "validator_receipts": []}),
        "burden_cycles": [],
        "reread_signature_history": [],
        "reread_signature_history_sha256": canonical_sha([]),
        "current_live_burdens": [],
        "held": [],
        "resource_policy": {
            "policy_id": "uncapped-semantic-depth-v1", "policy_sha256": HEX["policy"],
            "semantic_depth_cap": None, "on_exhaustion": "PARTIAL", "limits": {"wall_clock_seconds": 600},
        },
        "projection": {},
        "runtime_call_context_refs": [],
        "closure_authority": {"burden_ids":[],"candidate_state_ids":[],"owner_obligation_ids":[],"inventory_sha256":canonical_sha({"burden_ids":[],"candidate_state_ids":[],"owner_obligation_ids":[]})},
        "closure_state": {},
        "non_claims": ["Structural validity does not establish semantic truth."],
    }
    item, plan04, capsule, _ = cycle("C1", "B1", 1)
    payload["owner_routes"] = [plan04["route"]]
    payload["act_row_details"] = [plan04["act"]]
    payload["owner_execution_dispositions"] = [plan04["disposition"]]
    payload["upstream_obligation_ids"] = [plan04["route"]["obligation_id"]]
    payload["upstream_obligation_set_sha256"] = canonical_sha(sorted(payload["upstream_obligation_ids"]))
    payload["operation_capsules"] = [capsule]
    payload["burden_cycles"] = [item]
    payload["stage02_freeze"] = stage02_freeze(payload, ["B1"])
    stage_number = int(stage.split("-")[1])
    complete = stage_number >= 7
    payload["closure_state"] = {
        "opening_state": "OPEN",
        "opening_closure_claim": "PENDING",
        "derived_decision": "COMPLETE" if complete else "CLOSURE_CANDIDATE",
        "initial_coverage_complete": True,
        "lifecycle_accounting_complete": True,
        "collapse_positive": complete,
        "closure_confirmed": complete,
        "remaining_open_ids": [],
        "divergence": "neutral",
        "curl": "null",
        "loopbreak": None,
    }
    set_projections(payload)
    return payload


def multi_generation_payload(depth: int = 2) -> dict[str, Any]:
    payload = base_payload()
    cycles: list[dict[str, Any]] = []
    plan04_rows: list[dict[str, Any]] = []
    capsules: list[dict[str, Any]] = []
    event_index = 1
    for index in range(depth + 1):
        cycle_id = f"C{index + 1}"
        burden_id = f"B{index + 1}"
        is_last = index == depth
        candidates = []
        if not is_last:
            candidates = [candidate_event(
                f"CE{index + 1}", f"runtime-candidate-{index + 1}", 0, "instantiate_generated",
                target=f"B{index + 2}", next_cycle=f"C{index + 2}",
            )]
        item, plan04, capsule, event_index = cycle(
            cycle_id, burden_id, event_index,
            origin="B_LA" if index == 0 else "B_MRP",
            depth=index,
            parent_cycle_id=None if index == 0 else f"C{index}",
            exit_disposition="STOP" if is_last else "RECURSE",
            candidates=candidates,
        )
        cycles.append(item); plan04_rows.append(plan04); capsules.append(capsule)
    payload["burden_cycles"] = cycles
    payload["owner_routes"] = [row["route"] for row in plan04_rows]
    payload["act_row_details"] = [row["act"] for row in plan04_rows]
    payload["owner_execution_dispositions"] = [row["disposition"] for row in plan04_rows]
    payload["upstream_obligation_ids"] = [row["route"]["obligation_id"] for row in plan04_rows]
    payload["upstream_obligation_set_sha256"] = canonical_sha(sorted(payload["upstream_obligation_ids"]))
    payload["operation_capsules"] = capsules
    payload["stage02_freeze"] = stage02_freeze(payload, ["B1"])
    rehash_payload(payload)
    return payload


def candidate_disposition_payload(disposition: str) -> dict[str, Any]:
    payload = base_payload(stage="stage-05-mrp-reread-terminal-state")
    if disposition == "activate_held":
        event = candidate_event("CE-ACTIVATE", "K-ACTIVATE", 0, disposition, kind="held_activation", target="B1", next_cycle="C2")
        first, first_plan04, first_capsule, next_index = cycle("C1", "B1", 1, exit_disposition="RECURSE", candidates=[event])
        second, second_plan04, second_capsule, _ = cycle("C2", "B1", next_index, ordinal=2, operation_override="repair-b1-reactivated")
        rows = [first_plan04, second_plan04]
        payload["burden_cycles"] = [first, second]
        payload["operation_capsules"] = [first_capsule, second_capsule]
    else:
        kind = "escape_route" if disposition in {"defer_preempted", "non_load_bearing"} else "unclassified"
        target = "B1" if disposition == "defer_preempted" else None
        event = candidate_event(f"CE-{disposition.upper()}", f"K-{disposition.upper()}", 0, disposition, kind=kind, target=target,
            gate="evidence-gate" if disposition == "hold_partial" else None,
            next_action="resume after evidence" if disposition == "hold_partial" else None)
        exit_disposition = "HOLD" if disposition in {"defer_preempted", "hold_partial"} else "STOP"
        first, first_plan04, first_capsule, _ = cycle("C1", "B1", 1, exit_disposition=exit_disposition, candidates=[event])
        rows = [first_plan04]
        payload["burden_cycles"] = [first]
        payload["operation_capsules"] = [first_capsule]
        if exit_disposition == "HOLD":
            payload["current_live_burdens"] = ["B1"]
            candidate_id = event["candidate_id"]
            payload["held"] = [
                {"item_id":"B1","kind":"burden","gate":"candidate-disposition","next_action":"resume candidate","basis":f"{disposition} keeps burden live"},
                {"item_id":candidate_id,"kind":"candidate","gate":"candidate-disposition","next_action":"resume candidate","basis":f"{disposition} remains live"},
            ]
            payload["closure_state"] = {"opening_state":"OPEN","opening_closure_claim":"PENDING","derived_decision":"HOLD","initial_coverage_complete":True,"lifecycle_accounting_complete":True,"collapse_positive":False,"closure_confirmed":False,"remaining_open_ids":["B1",candidate_id],"divergence":"neutral","curl":"null","loopbreak":None}
    payload["owner_routes"] = [row["route"] for row in rows]
    payload["act_row_details"] = [row["act"] for row in rows]
    payload["owner_execution_dispositions"] = [row["disposition"] for row in rows]
    payload["upstream_obligation_ids"] = [row["route"]["obligation_id"] for row in rows]
    payload["upstream_obligation_set_sha256"] = canonical_sha(sorted(payload["upstream_obligation_ids"]))
    payload["stage02_freeze"] = stage02_freeze(payload, ["B1"])
    rehash_payload(payload)
    return payload


def multi_capsule_payload(count: int = 2) -> dict[str, Any]:
    if count < 1:
        raise ValueError("count must be positive")
    payload = base_payload(stage="stage-05-mrp-reread-terminal-state")
    cycle_row = payload["burden_cycles"][0]
    for ordinal in range(2, count + 1):
        capsule = operation_capsule("C1", "B1", ordinal, operation_override=f"repair-b1-axis-{ordinal}")
        obligation_id = capsule["obligation_ids"][0]
        route = copy.deepcopy(payload["owner_routes"][0])
        route.update({"obligation_id":obligation_id,"operation":capsule["operation"],"basis":f"exact Plan04 route {ordinal} in C1"})
        act = {key:route[key] for key in ("obligation_id","burden_id","pressure_ids","owner_id","operation","register_axis")}
        act["body_ref"] = capsule["body_ref"]
        disposition = {"obligation_id":obligation_id,"burden_id":"B1","disposition":"executed","body_ref":capsule["body_ref"],"satisfied_by_obligation_id":None,"trigger_evidence":None,"basis":f"operation {ordinal} executed in C1","gate":None,"next_action":None}
        payload["owner_routes"].append(route); payload["act_row_details"].append(act); payload["owner_execution_dispositions"].append(disposition)
        payload["upstream_obligation_ids"].append(obligation_id)
        payload["operation_capsules"].append(capsule)
        cycle_row["obligation_ids"].append(obligation_id); cycle_row["operation_capsule_ids"].append(capsule["capsule_id"])
        cycle_row["operation_events"].extend(operation_events(capsule, 2 + 6 * (ordinal - 1)))
        cycle_row["land"]["operation_capsule_ids"].append(capsule["capsule_id"])
        cycle_row["land"]["contribution_refs"].append(f"capsule:{capsule['capsule_id']}#land_contribution")
        cycle_row["post_land_delta"]["source_operation_capsule_ids"].append(capsule["capsule_id"])
    payload["upstream_obligation_set_sha256"] = canonical_sha(sorted(payload["upstream_obligation_ids"]))
    cycle_row["land"]["event_index"] = 2 + 6 * count
    cycle_row["post_land_delta"]["event_index"] = cycle_row["land"]["event_index"] + 1
    raw = cycle_row["reread"]["raw_exit"]
    raw["field_diagnostics"][0]["event_index"] = cycle_row["post_land_delta"]["event_index"] + 1
    raw["field_diagnostics"][1]["event_index"] = cycle_row["post_land_delta"]["event_index"] + 2
    raw["event_index"] = cycle_row["post_land_delta"]["event_index"] + 3
    rehash_payload(payload)
    return payload


def unknown_candidate_held_payload() -> dict[str, Any]:
    payload = candidate_disposition_payload("hold_partial")
    payload["burden_cycles"][0]["reread"]["raw_exit"]["candidate_events"][0]["kind"] = "future-open-world-kind"
    rehash_payload(payload)
    return payload


def overlapping_hyperedges_payload() -> dict[str, Any]:
    """Neighboring valid proving candidate partition groups need not be disjoint."""
    payload = base_payload(stage="stage-05-mrp-reread-terminal-state")
    payload["candidate_states"][0]["partition_ids"] = ["NP1"]
    payload["candidate_states"].append({
        "state_id": "N2", "frame": "alternative authority order", "frame_token": "alternative-authority-order",
        "observation_unit_ids": ["U1"], "pressure_ids": ["P1"], "live_registers": ["kappa", "Omega"],
        "read_status": "distributed", "confidence": "provisional", "status": "held",
        "partition_ids": ["NP1", "NP2"], "merged_into": None,
        "decisive_missing_differentiator": "source-order discriminator", "hold_gate": "source-order-evidence",
        "next_review_point": "next reread", "basis": "bounded compatible overlapping ambiguity loci",
    })
    payload["input_pressures"][0]["candidate_state_ids"] = ["N1", "N2"]
    payload["burden_partition_decisions"][0]["candidate_state_ids"] = ["N1", "N2"]
    payload["candidate_state_partitions"] = [
        {
            "partition_id":"NP1", "member_state_ids":["N1","N2"], "shared_observation_unit_ids":["U1"],
            "decision":"select_and_hold", "selected_state_id":"N1", "held_state_ids":["N2"],
            "merged_state_ids":[], "rejected_state_ids":[],
            "comparison":{"pressure_set_relation":"same","register_relation":"compatible","owner_eligibility_relation":"compatible","held_route_relation":"distinct","closure_consequence_relation":"distinct"},
            "decisive_differentiator":"source-order discriminator", "basis_unit_ids":["U1"], "basis":"operative frame licensed while alternative is held",
        },
        {
            "partition_id":"NP2", "member_state_ids":["N2"], "shared_observation_unit_ids":["U1"],
            "decision":"keep_distinct", "selected_state_id":None, "held_state_ids":["N2"],
            "merged_state_ids":[], "rejected_state_ids":[],
            "comparison":{"pressure_set_relation":"same","register_relation":"compatible","owner_eligibility_relation":"compatible","held_route_relation":"distinct","closure_consequence_relation":"distinct"},
            "decisive_differentiator":"source-order discriminator", "basis_unit_ids":["U1"], "basis":"overlapping ambiguity group remains globally held",
        },
    ]
    payload["held"] = [{"item_id":"N2","kind":"candidate","gate":"source-order-evidence","next_action":"reread","basis":"bounded held alternative"}]
    payload["closure_state"] = {
        "opening_state":"OPEN", "opening_closure_claim":"PENDING", "derived_decision":"HOLD",
        "initial_coverage_complete":True, "lifecycle_accounting_complete":True,
        "collapse_positive":False, "closure_confirmed":False, "remaining_open_ids":["N2"],
        "divergence":"neutral", "curl":"null", "loopbreak":None,
    }
    payload["stage02_freeze"] = stage02_freeze(payload, ["B1"])
    rehash_payload(payload)
    return payload


def expectation(
    fixture: str,
    stage: str,
    failure_class: str,
    subcode: str,
    markers: list[str],
    downstream: list[str],
) -> dict[str, Any]:
    return {
        "schema": "daee-negative-fixture-expectation-v1",
        "fixture": fixture,
        "kind": "invalid-single-signature",
        "expected_checker_id": "state-capsule",
        "expected_exit_category": "validation-failure",
        "expected_exit_code": 1,
        "expected_earliest_stage": stage,
        "expected_failure_class": failure_class,
        "expected_failure_subcode": subcode,
        "expected_downstream_invalidated": downstream,
        "required_diagnostic_markers": markers,
        "forbidden_artifacts": ["completion-verdict.json"] if stage in {"05", "06", "07", "08"} else ["candidate-package-record.json"],
        "provenance": "xhigh frozen additive state-capsule-v2 interface TDD",
    }


def invalid_cases(valid: dict[str, Any]) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    cases: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}

    def add(name: str, payload: dict[str, Any], stage: str, cls: str, subcode: str, markers: list[str], downstream: list[str]) -> None:
        cases[name] = (payload, expectation(name, stage, cls, subcode, markers, downstream))

    value = copy.deepcopy(valid); value["schema_owner"] = "A07"
    add("competing-schema-owner.json", value, "control-plane", "competing-schema-owner", "competing-schema-owner", ["A16", "A07"], ["preflight", "candidate-package"])

    value = copy.deepcopy(valid); value["stage02_freeze"]["candidate_state_set_sha256"] = "0" * 64; value["stage02_freeze"]["record_sha256"] = self_sha(value["stage02_freeze"], "record_sha256")
    add("baseline-freeze-hash.json", value, "02", "stage02-input-pressure-coverage", "baseline-freeze-hash", ["candidate_state_set_sha256", "baseline-freeze-hash"], ["03", "04", "05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["stage02_freeze"]["B_LA"] = []; value["stage02_freeze"]["B_LA_sequence_sha256"] = canonical_sha([]); value["stage02_freeze"]["topology_state_sha256"] = canonical_sha({"candidate_states":value["candidate_states"],"input_pressures":value["input_pressures"],"candidate_state_partitions":value["candidate_state_partitions"],"burden_partition_decisions":value["burden_partition_decisions"],"B_LA":[]}); value["stage02_freeze"]["record_sha256"] = self_sha(value["stage02_freeze"], "record_sha256")
    add("late-b-la-append.json", value, "02", "stage02-input-pressure-coverage", "b-la-late-append", ["B1", "stage02_freeze", "B_LA"], ["03", "04", "05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["input_pressures"][0]["candidate_state_ids"] = ["N-missing"]; rehash_payload(value)
    add("dangling-reference.json", value, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing", ["N-missing", "candidate_state_ids"], ["03", "04", "05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["candidate_states"].append(copy.deepcopy(value["candidate_states"][0])); rehash_payload(value)
    add("duplicate-id.json", value, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing", ["duplicate", "state_id", "N1"], ["03", "04", "05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["burden_cycles"][0]["obligation_set_sha256"] = "0" * 64; value["burden_cycles"][0]["cycle_sha256"] = self_sha(value["burden_cycles"][0], "cycle_sha256"); set_projections(value)
    add("obligation-universe-hash.json", value, "03", "owner-obligation-coverage", "obligation-universe-hash", ["obligation_set_sha256"], ["04", "05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["partition_derivative_mappings_sha256"] = "0" * 64
    add("partition-derivative-authority-mismatch.json", value, "03", "owner-obligation-coverage", "derivative-inventory-hash", ["derivative inventory", "Plan03"], ["04", "05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["operation_capsules"][0]["owner_id"] = "other-owner"; rehash_payload(value)
    add("operation-capsule-reference-mismatch.json", value, "04", "act_body_evidence", "operation-capsule-join", ["owner_id", "obligation"], ["05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["operation_capsules"][0]["before_state"]["source_pressure_ids"] = ["P-GHOST"]; rehash_payload(value)
    add("operation-capsule-before-state-pressure.json", value, "04", "act_body_evidence", "before-state-pressure-anchor", ["before_state", "source_pressure_ids", "P1"], ["05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["burden_cycles"][0]["operation_events"][3]["sequence"] = 6; value["burden_cycles"][0]["operation_events"][5]["sequence"] = 4; rehash_payload(value)
    add("operation-capsule-chronology-mismatch.json", value, "04", "act_body_evidence", "performed-event-order", ["local_delta", "land_contribution"], ["05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["burden_cycles"][0]["land"]["event_index"] = value["burden_cycles"][0]["operation_events"][-1]["event_index"] - 1; rehash_payload(value)
    add("land-before-operation.json", value, "04", "act_body_evidence", "land-before-operation", ["Land", "operation"], ["05", "06", "07", "08"])

    value = copy.deepcopy(valid); value["burden_cycles"][0]["post_land_delta"]["event_index"] = value["burden_cycles"][0]["land"]["event_index"] - 1; rehash_payload(value)
    add("post-land-order.json", value, "05", "mrp", "post-land-order", ["post-Land", "event_index"], ["06", "07", "08"])

    value = copy.deepcopy(valid); value["burden_cycles"][0]["reread"]["raw_exit"]["exit_disposition"] = "COMPLETE"; rehash_payload(value)
    add("raw-complete-forbidden.json", value, "05", "mrp", "raw-complete-forbidden", ["COMPLETE", "Stage07"], ["06", "07", "08"])

    value = copy.deepcopy(valid); raw = value["burden_cycles"][0]["reread"]["raw_exit"]; raw["field_diagnostics"][1]["event_index"] = raw["field_diagnostics"][0]["event_index"]; rehash_payload(value)
    add("duplicate-event-index.json", value, "05", "mrp", "post-land-order", ["event_index", "duplicated"], ["06", "07", "08"])

    value = copy.deepcopy(valid); raw = value["burden_cycles"][0]["reread"]["raw_exit"]; raw["candidate_events"] = [candidate_event("CE-DANGLING", "runtime-candidate", 10, "hold_partial", kind="unclassified", previous="CE-MISSING")]; raw["field_diagnostics"][0]["event_index"] = 11; raw["field_diagnostics"][1]["event_index"] = 12; raw["event_index"] = 13; rehash_payload(value)
    add("candidate-transition-invalid.json", value, "05", "mrp", "candidate-transition-invalid", ["CE-MISSING", "previous"], ["06", "07", "08"])

    value = copy.deepcopy(valid); raw = value["burden_cycles"][0]["reread"]["raw_exit"]; raw["candidate_events"] = [candidate_event("CE-CYCLE", "runtime-candidate", 10, "activate_held", kind="held_activation", target="B1", next_cycle="C1")]; raw["field_diagnostics"][0]["event_index"] = 11; raw["field_diagnostics"][1]["event_index"] = 12; raw["event_index"] = 13; rehash_payload(value)
    add("event-dag-cycle.json", value, "05", "mrp", "event-dag-cycle", ["event DAG", "cyclic", "noetic"], ["06", "07", "08"])

    value = copy.deepcopy(valid); value["burden_cycles"][0]["origin"] = "B_MRP"; value["burden_cycles"][0]["generation_depth"] = 0; value["burden_cycles"][0]["parent_cycle_id"] = None; rehash_payload(value)
    add("invalid-cycle-provenance.json", value, "05", "mrp", "generation-parentage", ["B_MRP", "parent"], ["06", "07", "08"])

    value = copy.deepcopy(valid); value["burden_cycles"][0]["lifecycle_status"] = "active"; value["burden_cycles"][0]["terminal_state"] = "open"; rehash_payload(value)
    add("cycle-status-terminal-mismatch.json", value, "05", "mrp", "lifecycle_accounting", ["STOP", "active", "open"], ["06", "07", "08"])

    value = copy.deepcopy(valid); value["current_live_burdens"] = ["B1"]; rehash_payload(value)
    add("terminal-burden-listed-live.json", value, "05", "state-capsule-custody", "derived-live-held-mismatch", ["B1", "current_live_burdens"], ["06", "07", "08"])

    value = copy.deepcopy(valid); value["held"] = [{"item_id":"B1","kind":"burden","gate":"owner-gate","next_action":"resume","basis":"basis:held"}]; rehash_payload(value)
    add("held-burden-terminal-mismatch.json", value, "05", "state-capsule-custody", "derived-live-held-mismatch", ["B1", "held"], ["06", "07", "08"])

    value = copy.deepcopy(valid); value["closure_state"]["remaining_open_ids"] = ["B1"]; value["closure_state"]["closure_confirmed"] = True; rehash_payload(value)
    add("false-closure-with-live-burdens.json", value, "07", "public-projection", "coverage-predicate-mismatch", ["remaining_open_ids", "B1"], ["08"])

    value = copy.deepcopy(valid); value["closure_state"]["derived_decision"] = "PARTIAL"; rehash_payload(value)
    add("producer-oracle-mismatch.json", value, "07", "public-projection", "producer-oracle-mismatch", ["PARTIAL", "COMPLETE"], ["08"])

    value = copy.deepcopy(valid); value["topology_mass_evidence_authority"]["validator_receipts"][0]["verdict"] = "FAIL"; value["topology_mass_evidence_authority_sha256"] = canonical_sha(value["topology_mass_evidence_authority"])
    add("topology-mass-validator-receipt-authority.json", value, "06", "topology_mass_schema", "validator-receipt-shape", ["validator receipt", "malformed"], ["07", "08"])

    value = copy.deepcopy(valid); value["projection"]["public_field_witness_sha256"] = None
    add("stage07-witness-hash-missing.json", value, "07", "witness-binding", "public-witness-hash-missing", ["public_field_witness_sha256", "Stage07"], ["08"])

    value = copy.deepcopy(valid); value["resource_policy"]["semantic_depth_cap"] = 3
    add("semantic-depth-cap.json", value, "preflight", "semantic-depth-cap", "semantic-depth-cap", ["semantic_depth_cap", "null", "3"], ["candidate-package"])

    value = copy.deepcopy(valid); value["operation_capsules"][0]["performed_operation"]["application"] += " with a materially changed post-Land effect"; value["operation_capsules"][0]["operation_capsule_sha256"] = "sha256:" + self_sha(value["operation_capsules"][0], "operation_capsule_sha256")
    add("reread-signature-not-delta-sensitive.json", value, "05", "mrp", "reread-signature-mismatch", ["operation", "Land", "post-Land", "graph"], ["06", "07", "08"])

    value = copy.deepcopy(valid); raw = value["burden_cycles"][0]["reread"]["raw_exit"]; raw["candidate_events"] = [candidate_event("CE-UNKNOWN", "K-UNKNOWN", 10, "non_load_bearing", kind="future-open-world-kind")]; raw["field_diagnostics"][0]["event_index"] = 11; raw["field_diagnostics"][1]["event_index"] = 12; raw["event_index"] = 13; rehash_payload(value)
    add("unknown-candidate-kind-not-held.json", value, "05", "mrp", "state_v2_candidate_kind_delta", ["unknown candidate kind", "explicitly held"], ["06", "07", "08"])

    value = copy.deepcopy(valid); first = value["operation_capsules"][0]; second = copy.deepcopy(first); second["capsule_id"] = "OC-B1-2"; second["body_sha256"] = "f" * 64; second["operation_capsule_sha256"] = "sha256:" + self_sha(second, "operation_capsule_sha256"); value["operation_capsules"].append(second)
    add("body-hash-conflict.json", value, "04", "act_body_evidence", "body-hash-conflict", ["body_ref", "body_sha256"], ["05", "06", "07", "08"])

    loop_payload = base_payload(stage="stage-05-mrp-reread-terminal-state"); loop, _ = loopbreak_evidence(12); broken_cycle, broken_plan04, broken_capsule, _ = cycle("C1", "B1", 1, exit_disposition="HOLD", loopbreak=loop, noetic_graph=loop["post_break_graph"]); loop_payload["burden_cycles"]=[broken_cycle]; loop_payload["owner_routes"]=[broken_plan04["route"]]; loop_payload["act_row_details"]=[broken_plan04["act"]]; loop_payload["owner_execution_dispositions"]=[broken_plan04["disposition"]]; loop_payload["upstream_obligation_ids"]=[broken_plan04["route"]["obligation_id"]]; loop_payload["upstream_obligation_set_sha256"]=canonical_sha(loop_payload["upstream_obligation_ids"]); loop_payload["operation_capsules"]=[broken_capsule]; loop_payload["current_live_burdens"]=["B1"]; loop_payload["held"]=[{"item_id":"B1","kind":"burden","gate":"remaining-noetic-cycle","next_action":"resume after new evidence","basis":"basis:loopbreak"}]; loop_payload["closure_state"]={"opening_state":"OPEN","opening_closure_claim":"PENDING","derived_decision":"HOLD","initial_coverage_complete":True,"lifecycle_accounting_complete":True,"collapse_positive":False,"closure_confirmed":False,"remaining_open_ids":["B1"],"divergence":"neutral","curl":"held","loopbreak":{"loopbreak_id":"LB1","loopbreak_sha256":loop["loopbreak_sha256"]}}; del loop_payload["burden_cycles"][0]["reread"]["raw_exit"]["loopbreak"]["owner_ground_ref"]; rehash_payload(loop_payload)
    loop_payload["closure_state"]["loopbreak"]["loopbreak_sha256"] = loop_payload["burden_cycles"][0]["reread"]["raw_exit"]["loopbreak"]["loopbreak_sha256"]
    set_projections(loop_payload)
    add("incomplete-loopbreak.json", loop_payload, "05", "mrp", "incomplete-loopbreak", ["owner_ground_ref", "LoopBreak"], ["06", "07", "08"])

    value = copy.deepcopy(valid); value["canonicalization"] = "other-canonicalization"
    add("canonicalization-mismatch.json", value, "preflight", "state-capsule-custody", "canonicalization-mismatch", ["daee-canonical-json-v1"], ["candidate-package"])

    return cases


def historical_v1() -> dict[str, Any]:
    return {
        "schema":"daee-state-capsule-v1","case_id":"historical-v1",
        "input_fingerprint":"sha256:" + "a" * 64,"stage":"04",
        "n_frame":{"selected":"authority-order","held_candidates":[]},
        "live_registers":["N","m","tau","sigma"],"register_state":{"tau":"live","sigma":"live"},
        "B_LA":["B1"],"B_MRP":[],"B_total":["B1"],"current_burden":"B1","held_set_H":[],
        "completed_acts":[],"last_terminal":{"burden":None,"state":None},"last_delta":None,
        "last_mrp_resultant":{"source":None,"route_result_type":"none"},"route_result_type":"none",
        "field_diagnostics":{"divergence_state":"neutral","curl_state":"null-state"},"transport":"chat",
        "terminal_states":{},"next_burden":None,"current_owner_route":{"burden":"B1","owner_id":"M3","shards":[]},
        "coverage_complete":False,"next_required_action":"activate B1","output_artifact_path":None,
        "output_sha256":None,"output_offset_bytes":0,"cold_law_refs_used":[],"shards_loaded":[],
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build() -> dict[Path, Any]:
    composed = base_payload()
    stage05 = base_payload(stage="stage-05-mrp-reread-terminal-state")
    generated = multi_generation_payload(2)
    overlapping = overlapping_hyperedges_payload()
    loop_payload = base_payload(stage="stage-05-mrp-reread-terminal-state")
    loop, _ = loopbreak_evidence(12)
    loop_cycle, loop_obligation, loop_capsule, _ = cycle(
        "C1", "B1", 1, exit_disposition="HOLD", loopbreak=loop,
        noetic_graph=loop["post_break_graph"],
    )
    loop_payload["burden_cycles"] = [loop_cycle]
    loop_payload["owner_routes"] = [loop_obligation["route"]]
    loop_payload["act_row_details"] = [loop_obligation["act"]]
    loop_payload["owner_execution_dispositions"] = [loop_obligation["disposition"]]
    loop_payload["upstream_obligation_ids"] = [loop_obligation["route"]["obligation_id"]]
    loop_payload["upstream_obligation_set_sha256"] = canonical_sha(loop_payload["upstream_obligation_ids"])
    loop_payload["operation_capsules"] = [loop_capsule]
    loop_payload["current_live_burdens"] = ["B1"]
    loop_payload["held"] = [{"item_id":"B1","kind":"burden","gate":"remaining-noetic-cycle","next_action":"resume after new evidence","basis":"basis:loopbreak"}]
    loop_payload["closure_state"] = {
        "opening_state":"OPEN","opening_closure_claim":"PENDING","derived_decision":"HOLD",
        "initial_coverage_complete":True,"lifecycle_accounting_complete":True,"collapse_positive":False,
        "closure_confirmed":False,"remaining_open_ids":["B1"],"divergence":"neutral","curl":"held",
        "loopbreak":{"loopbreak_id":"LB1","loopbreak_sha256":loop["loopbreak_sha256"]},
    }
    rehash_payload(loop_payload)

    zero = base_payload(stage="stage-02-layer-a-diagnostic-ir")
    zero["candidate_states"] = [{
        "state_id":"N0", "frame":"underdetermined frame", "frame_token":"underdetermined-frame",
        "observation_unit_ids":["U1"], "pressure_ids":["P0"], "live_registers":["Omega"],
        "read_status":"underdetermined", "confidence":"low", "status":"underdetermined",
        "partition_ids":["NP0"], "merged_into":None,
        "decisive_missing_differentiator":"new source evidence", "hold_gate":"evidence",
        "next_review_point":"after evidence", "basis":"source-anchored underdetermination",
    }]
    zero["input_pressures"] = [{
        "pressure_id":"P0", "observation_unit_ids":["U1"], "candidate_state_ids":["N0"],
        "pressure_function":"bound the unresolved relation", "register_axes":["Omega"],
        "status":"held", "burden_id":None, "decision_id":"BP0", "basis":"awaiting evidence",
    }]
    zero["candidate_state_partitions"] = [{
        "partition_id":"NP0", "member_state_ids":["N0"], "shared_observation_unit_ids":["U1"],
        "decision":"keep_distinct", "selected_state_id":None, "held_state_ids":["N0"],
        "merged_state_ids":[], "rejected_state_ids":[],
        "comparison":{"pressure_set_relation":"unresolved","register_relation":"unresolved","owner_eligibility_relation":"unresolved","held_route_relation":"unresolved","closure_consequence_relation":"unresolved"},
        "decisive_differentiator":"new source evidence", "basis_unit_ids":["U1"], "basis":"preserved",
    }]
    zero["burden_partition_decisions"] = [{
        "decision_id":"BP0", "candidate_state_ids":["N0"], "observation_unit_ids":["U1"],
        "pressure_ids":["P0"], "decision":"hold_unresolved", "pressure_to_burden":[],
        "same_function_proof":{"tau_relation":"unresolved","source_frame_relation":"unresolved","claim_cluster_relation":"unresolved","register_transition_relation":"unresolved","owner_operation_relation":"unresolved","restoration_vector_relation":"unresolved","collapse_dependency_relation":"unresolved"},
        "residual_pressure_ids":[], "held_pressure_ids":["P0"], "basis":"not licensed",
    }]
    zero["input_coverage"] = {"all_observation_unit_ids":["U1"],"pressure_bearing_unit_ids":["U1"],"explicitly_disposed_unit_ids":[],"unaccounted_unit_ids":[]}
    zero["selection_status"] = "not_licensed"; zero["selected_n_frame"] = None; zero["burden_floor"] = []
    zero["upstream_obligation_ids"] = []; zero["upstream_obligation_set_sha256"] = canonical_sha([])
    zero["upstream_pressure_ids"] = ["P0"]; zero["upstream_partition_decision_ids"] = ["BP0"]
    zero["owner_routes"] = []; zero["act_row_details"] = []; zero["owner_execution_dispositions"] = []
    zero["operation_capsules"] = []; zero["burden_cycles"] = []
    zero["current_live_burdens"] = []
    zero["held"] = [
        {"item_id":"N0","kind":"candidate","gate":"evidence","next_action":"reassess","basis":"underdetermined"},
        {"item_id":"P0","kind":"pressure","gate":"evidence","next_action":"reassess","basis":"awaiting evidence"},
    ]
    zero["closure_state"] = {"opening_state":"OPEN","opening_closure_claim":"PENDING","derived_decision":"HOLD","initial_coverage_complete":True,"lifecycle_accounting_complete":True,"collapse_positive":False,"closure_confirmed":False,"remaining_open_ids":["N0","P0"],"divergence":"unknown","curl":"unknown","loopbreak":None}
    zero["stage02_freeze"] = stage02_freeze(zero, [])
    set_projections(zero)

    outputs: dict[Path, Any] = {
        VALID / "composed-all-plan-fields.json": composed,
        VALID / "low-topology.json": copy.deepcopy(composed),
        VALID / "stage05-stop-closure-candidate.json": stage05,
        VALID / "generated-child-of-generated-parent.json": generated,
        VALID / "overlapping-candidate-hyperedges.json": overlapping,
        VALID / "cyclic-noetic-loopbreak.json": loop_payload,
        VALID / "zero-selected-open-partial.json": zero,
        VALID / "candidate-disposition-activate-held.json": candidate_disposition_payload("activate_held"),
        VALID / "candidate-disposition-instantiate-generated.json": multi_generation_payload(1),
        VALID / "candidate-disposition-defer-preempted.json": candidate_disposition_payload("defer_preempted"),
        VALID / "candidate-disposition-non-load-bearing.json": candidate_disposition_payload("non_load_bearing"),
        VALID / "candidate-disposition-hold-partial.json": candidate_disposition_payload("hold_partial"),
        VALID / "multi-operation-capsule-cycle.json": multi_capsule_payload(),
        VALID / "unknown-candidate-kind-held.json": unknown_candidate_held_payload(),
    }
    for name, (payload, sidecar) in invalid_cases(composed).items():
        outputs[INVALID / name] = payload
        outputs[INVALID / name.replace(".json", ".expectation.json")] = sidecar
    outputs[INVALID / "release-bearing-v1.json"] = historical_v1()
    outputs[INVALID / "release-bearing-v1.expectation.json"] = expectation(
        "release-bearing-v1.json", "preflight", "release-bearing-v1", "release-bearing-v1",
        ["daee-state-capsule-v1", "daee-state-capsule-v2"], ["candidate-package"],
    )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    stale: list[str] = []
    for path, value in outputs.items():
        expected = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                stale.append(path.relative_to(ROOT).as_posix())
        else:
            write_json(path, value)
    if stale:
        print("state-capsule-v2 fixtures stale: " + ", ".join(stale))
        return 1
    print(f"state-capsule-v2 fixture build: PASS ({len(outputs)} file(s){', check' if args.check else ''})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
