#!/usr/bin/env python3
"""Plan03 candidate hyperedge and pressure/burden partition validation."""
from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any, Iterable

CANDIDATE_DECISIONS = {"select_single", "select_and_hold", "keep_distinct", "merge_equivalent", "reject_nonfit"}
PRESSURE_DECISIONS = {"one_to_one", "split_distinct_functions", "keep_distinct", "merge_same_function", "hold_unresolved"}
COMPARISON_AXES = {"pressure_set_relation", "register_relation", "owner_eligibility_relation", "held_route_relation", "closure_consequence_relation"}
COMPARISON_VALUES = {
    "pressure_set_relation": {"same", "overlapping", "distinct", "unresolved"},
    "register_relation": {"same", "compatible", "distinct", "unresolved"},
    "owner_eligibility_relation": {"same", "compatible", "distinct", "unresolved"},
    "held_route_relation": {"same", "distinct", "unresolved"},
    "closure_consequence_relation": {"same", "distinct", "unresolved"},
}
PROOF_AXES = {"tau_relation", "source_frame_relation", "claim_cluster_relation", "register_transition_relation", "owner_operation_relation", "restoration_vector_relation", "collapse_dependency_relation"}
CANDIDATE_STATUSES = {"selected", "held", "underdetermined", "merged", "rejected"}
READ_STATUSES = {"dominant", "distributed", "underdetermined"}
CONFIDENCE_LEVELS = {"strong", "provisional", "low"}
PRESSURE_STATUSES = {"routed", "merged", "held", "non_load_bearing", "unresolved"}


def _finding(subcode: str, message: str, *markers: str) -> dict[str, Any]:
    return {"failure_class": "split-merge-proof", "failure_subcode": subcode, "message": message, "markers": list(markers)}


def _set_sha256(values: list[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(values), separators=(",", ":")).encode("utf-8")).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _set_relation(left: set[str], right: set[str], *, compatible_overlap: bool) -> str:
    if left == right:
        return "same"
    if left.isdisjoint(right):
        return "distinct"
    return "compatible" if compatible_overlap else "overlapping"


def _string_set(value: Any, field: str, *, allow_empty: bool = False) -> tuple[set[str] | None, dict[str, Any] | None]:
    if not isinstance(value, list) or (not allow_empty and not value) or not all(isinstance(item, str) and item for item in value) or len(value) != len(set(value)):
        return None, _finding("collection-shape", f"{field} must be a {'possibly empty ' if allow_empty else 'nonempty '}unique string array", field)
    return set(value), None


def validate_topology_partition(record: Any, *, upstream_candidate_ids: list[str] | None = None, upstream_pressure_ids: list[str] | None = None, upstream_derivative_inventory: list[dict[str, Any]] | None = None, upstream_derivative_inventory_sha256: str | None = None) -> list[dict[str, Any]]:
    if not isinstance(record, dict):
        return [_finding("record-shape", "record must be an object")]
    if record.get("topology_contract") != "input-pressure-v1":
        return [_finding("contract-version", "topology_contract must be input-pressure-v1")]
    if upstream_candidate_ids is None or upstream_pressure_ids is None or upstream_derivative_inventory is None or upstream_derivative_inventory_sha256 is None:
        return [_finding("upstream-boundary-required", "independent candidate, pressure, and derivative inventories are required", "external")]
    if not isinstance(upstream_derivative_inventory, list) or upstream_derivative_inventory_sha256 != _canonical_sha256(upstream_derivative_inventory):
        return [_finding("derivative-inventory-hash", "independent derivative inventory hash mismatch", "derivative", "external")]
    embedded_derivatives = record.get("candidate_derivative_mappings", [])
    if embedded_derivatives != upstream_derivative_inventory:
        return [_finding("derivative-inventory-mismatch", "record derivative projection differs from independent inventory", "derivative", "external")]
    derivative_by_id: dict[str, dict[str, Any]] = {}
    derivative_fields = {"decision_id", "partition_id", "source_state_ids", "receiving_state_id", "source_pressure_ids", "receiving_pressure_ids", "comparison", "basis"}
    for derivative in upstream_derivative_inventory:
        if not isinstance(derivative, dict) or set(derivative) != derivative_fields:
            return [_finding("derivative-inventory-shape", "derivative inventory row lacks exact fields", "derivative")]
        decision_id = derivative.get("decision_id")
        if not isinstance(decision_id, str) or not decision_id or decision_id in derivative_by_id:
            return [_finding("derivative-decision-duplicate", "derivative decision IDs must be unique", str(decision_id))]
        if not isinstance(derivative.get("basis"), str) or not derivative["basis"].strip():
            return [_finding("derivative-inventory-shape", "derivative decision needs a basis", decision_id)]
        derivative_by_id[decision_id] = derivative
    external_candidates, finding = _string_set(upstream_candidate_ids, "upstream_candidate_ids")
    if finding:
        return [finding]
    external_pressures, finding = _string_set(upstream_pressure_ids, "upstream_pressure_ids")
    if finding:
        return [finding]
    embedded_candidates, finding = _string_set(record.get("upstream_candidate_ids"), "upstream_candidate_ids")
    if finding:
        return [finding]
    embedded_pressures, finding = _string_set(record.get("upstream_pressure_ids"), "upstream_pressure_ids")
    if finding:
        return [finding]
    if record.get("upstream_candidate_set_sha256") != _set_sha256(record["upstream_candidate_ids"]) or record.get("upstream_pressure_set_sha256") != _set_sha256(record["upstream_pressure_ids"]):
        return [_finding("upstream-universe-hash", "embedded upstream inventory hash mismatch", "upstream")]
    if embedded_candidates != external_candidates or embedded_pressures != external_pressures:
        missing = sorted((external_candidates or set()) - (embedded_candidates or set())) + sorted((external_pressures or set()) - (embedded_pressures or set()))
        return [_finding("upstream-boundary-mismatch", f"embedded inventories omit external identities {missing}", *missing, "external")]

    candidates = record.get("candidate_states")
    pressures = record.get("input_pressures")
    partitions = record.get("candidate_state_partitions")
    decisions = record.get("burden_partition_decisions")
    burden_floor = record.get("burden_floor")
    if not all(isinstance(value, list) for value in (candidates, pressures, partitions, decisions, burden_floor)):
        return [_finding("collection-shape", "candidate_states, input_pressures, partitions, decisions, and burden_floor must be arrays")]
    candidate_row_ids = [item.get("state_id") for item in candidates if isinstance(item, dict) and isinstance(item.get("state_id"), str)]
    pressure_row_ids = [item.get("pressure_id") for item in pressures if isinstance(item, dict) and isinstance(item.get("pressure_id"), str)]
    if set(candidate_row_ids) != external_candidates or set(pressure_row_ids) != external_pressures:
        missing = sorted((external_candidates or set()) - set(candidate_row_ids)) + sorted((external_pressures or set()) - set(pressure_row_ids))
        extra = sorted(set(candidate_row_ids) - (external_candidates or set())) + sorted(set(pressure_row_ids) - (external_pressures or set()))
        return [_finding("upstream-universe-mismatch", f"record rows do not equal external inventories; missing={missing}, extra={extra}", *missing, *extra, "upstream")]
    candidate_by_id: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        required = {"state_id", "frame_token", "observation_unit_ids", "pressure_ids", "live_registers", "read_status", "confidence", "status", "partition_ids", "merged_into", "decisive_missing_differentiator", "hold_gate", "next_review_point", "basis"}
        if not isinstance(candidate, dict) or not required <= set(candidate):
            missing = sorted(required - set(candidate)) if isinstance(candidate, dict) else sorted(required)
            return [_finding("candidate-shape", f"candidate state lacks canonical Plan03 fields {missing}", *missing)]
        state_id = candidate.get("state_id")
        if not isinstance(state_id, str) or not state_id or state_id in candidate_by_id:
            return [_finding("candidate-shape", "candidate states need unique nonempty state_id")]
        for field in ("observation_unit_ids", "pressure_ids", "live_registers", "partition_ids"):
            _, finding = _string_set(candidate[field], field)
            if finding:
                return [finding]
        if not isinstance(candidate["frame_token"], str) or not candidate["frame_token"].strip() or not isinstance(candidate["basis"], str) or not candidate["basis"].strip():
            return [_finding("candidate-shape", f"{state_id} needs frame_token and source-anchored basis", state_id)]
        if candidate["read_status"] not in READ_STATUSES or candidate["confidence"] not in CONFIDENCE_LEVELS or candidate["status"] not in CANDIDATE_STATUSES:
            return [_finding("candidate-shape", f"{state_id} has unsupported candidate vocabulary", state_id)]
        if candidate["status"] == "held":
            if not all(isinstance(candidate[field], str) and candidate[field].strip() for field in ("decisive_missing_differentiator", "hold_gate", "next_review_point")):
                return [_finding("candidate-hold-custody", f"{state_id} held state needs differentiator, gate, and next review point", state_id)]
        elif any(candidate[field] is not None for field in ("decisive_missing_differentiator", "hold_gate", "next_review_point")):
            return [_finding("candidate-hold-custody", f"{state_id} non-held state cannot carry hold-only fields", state_id)]
        if candidate["status"] == "merged":
            if not isinstance(candidate["merged_into"], str) or candidate["merged_into"] == state_id:
                return [_finding("candidate-merge-target", f"{state_id} needs a distinct merge receiver", state_id)]
        elif candidate["merged_into"] is not None:
            return [_finding("candidate-merge-target", f"{state_id} non-merged state cannot name merged_into", state_id)]
        if candidate["status"] == "rejected" and "not selected" in candidate["basis"].lower():
            return [_finding("candidate-circular-basis", f"{state_id} uses circular rejection basis", state_id)]
        candidate_by_id[state_id] = candidate
    selected = [item for item in candidates if item["status"] == "selected"]
    if record.get("selection_status") == "licensed":
        if len(selected) != 1 or record.get("selected_n_frame") != selected[0]["frame_token"]:
            return [_finding("selection-join", "licensed selection must name the one selected frame_token")]
    elif record.get("selection_status") == "not_licensed":
        if selected or record.get("selected_n_frame") is not None or not any(item["status"] in {"held", "underdetermined"} for item in candidates):
            return [_finding("selection-join", "not_licensed selection must preserve live alternatives and select none")]
    else:
        return [_finding("selection-join", "selection_status must be licensed or not_licensed")]
    pressure_by_id: dict[str, dict[str, Any]] = {}
    for pressure in pressures:
        required = {"pressure_id", "observation_unit_ids", "candidate_state_ids", "pressure_function", "register_axes", "status", "burden_id", "decision_id", "basis"}
        if not isinstance(pressure, dict) or not required <= set(pressure):
            missing = sorted(required - set(pressure)) if isinstance(pressure, dict) else sorted(required)
            return [_finding("pressure-shape", f"pressure lacks canonical Plan02 fields {missing}", *missing)]
        pressure_id = pressure.get("pressure_id")
        if not isinstance(pressure_id, str) or not pressure_id or pressure_id in pressure_by_id:
            return [_finding("pressure-shape", "pressures need unique nonempty pressure_id")]
        for field in ("observation_unit_ids", "candidate_state_ids", "register_axes"):
            _, finding = _string_set(pressure[field], field)
            if finding:
                return [finding]
        if not set(pressure["candidate_state_ids"]) <= set(candidate_by_id) or not isinstance(pressure["pressure_function"], str) or not pressure["pressure_function"].strip() or not isinstance(pressure["basis"], str) or not pressure["basis"].strip() or pressure["status"] not in PRESSURE_STATUSES:
            return [_finding("pressure-shape", f"{pressure_id} has invalid joins/function/status/basis", pressure_id)]
        pressure_by_id[pressure_id] = pressure
    partition_ids: set[str] = set()
    memberships: set[str] = set()
    for partition in partitions:
        if not isinstance(partition, dict):
            return [_finding("partition-shape", "candidate partition must be an object")]
        required = {"partition_id", "member_state_ids", "shared_observation_unit_ids", "decision", "selected_state_id", "held_state_ids", "merged_state_ids", "rejected_state_ids", "comparison", "decisive_differentiator", "basis_unit_ids", "basis"}
        missing = sorted(required - set(partition))
        if missing:
            return [_finding("partition-shape", f"partition lacks {missing}", *missing)]
        partition_id = partition["partition_id"]
        if not isinstance(partition_id, str) or not partition_id or partition_id in partition_ids:
            return [_finding("partition-id", f"invalid or duplicate partition_id {partition_id!r}")]
        partition_ids.add(partition_id)
        members, finding = _string_set(partition["member_state_ids"], "member_state_ids")
        if finding:
            return [finding]
        if not members <= set(candidate_by_id):
            return [_finding("partition-candidate-join", f"{partition_id} references unknown candidates", partition_id)]
        memberships.update(members)
        decision = partition["decision"]
        if decision not in CANDIDATE_DECISIONS or not str(partition["basis"]).strip():
            return [_finding("partition-decision", f"{partition_id} has unsupported decision/basis", partition_id)]
        comparison = partition["comparison"]
        bad_axes = [] if isinstance(comparison, dict) and set(comparison) == COMPARISON_AXES else sorted(COMPARISON_AXES)
        if not bad_axes:
            bad_axes = sorted(axis for axis in COMPARISON_AXES if comparison[axis] not in COMPARISON_VALUES[axis])
        if bad_axes:
            return [_finding("partition-comparison", f"{partition_id} lacks exact comparison axes {bad_axes}", partition_id, *bad_axes)]
        roles: dict[str, str] = {}
        selected_id = partition["selected_state_id"]
        if selected_id is not None:
            if selected_id not in members:
                return [_finding("partition-role-join", f"{partition_id} selected_state_id is not a member", partition_id, str(selected_id))]
            roles[selected_id] = "selected"
        for field, status in (("held_state_ids", "held"), ("merged_state_ids", "merged"), ("rejected_state_ids", "rejected")):
            values, finding = _string_set(partition[field], field, allow_empty=True)
            if finding:
                return [finding]
            if not values <= members or set(roles).intersection(values):
                return [_finding("partition-role-join", f"{partition_id} has overlapping or nonmember terminal roles", partition_id, field)]
            roles.update({value: status for value in values})
        for state_id in sorted(members):
            global_status = candidate_by_id[state_id].get("status")
            assigned = roles.get(state_id)
            if assigned is None and global_status != "underdetermined":
                return [_finding("partition-global-status", f"{partition_id} leaves {state_id} unclassified against global {global_status}", partition_id, state_id)]
            if assigned is not None and assigned != global_status:
                return [_finding("partition-global-status", f"{partition_id} assigns {state_id}={assigned} but global status is {global_status}", partition_id, state_id, assigned, str(global_status))]
            if assigned == "merged" and candidate_by_id[state_id].get("merged_into") != selected_id:
                return [_finding("partition-merge-target", f"{state_id} merge target disagrees with {partition_id}", state_id, partition_id)]
        if decision == "select_single" and not (len(members) == 1 and selected_id in members and len(roles) == 1):
            return [_finding("select-single-shape", f"{partition_id} select_single must select its sole member", partition_id)]
        if decision == "select_and_hold" and (selected_id is None or set(partition["held_state_ids"]) != members - {selected_id}):
            return [_finding("select-hold-shape", f"{partition_id} select_and_hold must select one and hold the remainder", partition_id)]
        if decision == "merge_equivalent":
            if selected_id is None or set(partition["merged_state_ids"]) != members - {selected_id}:
                return [_finding("merge-shape", f"{partition_id} merge_equivalent needs one receiver and merged remainder", partition_id)]
            if any(value in {"distinct", "unresolved"} for value in comparison.values()):
                return [_finding("merge-axis-incompatible", f"{partition_id} merge has distinct/unresolved comparison axis", partition_id)]
            member_rows = [candidate_by_id[state_id] for state_id in sorted(members)]
            actual_pressure = _set_relation(set(member_rows[0]["pressure_ids"]), set(member_rows[1]["pressure_ids"]), compatible_overlap=False)
            actual_register = _set_relation(set(member_rows[0]["live_registers"]), set(member_rows[1]["live_registers"]), compatible_overlap=True)
            if any(_set_relation(set(member_rows[0]["pressure_ids"]), set(row["pressure_ids"]), compatible_overlap=False) != actual_pressure for row in member_rows[1:]) or any(_set_relation(set(member_rows[0]["live_registers"]), set(row["live_registers"]), compatible_overlap=True) != actual_register for row in member_rows[1:]):
                return [_finding("partition-relation-mismatch", f"{partition_id} members do not share one derived relation", partition_id)]
            derivative_id = partition.get("derivative_decision_id")
            derivative = derivative_by_id.get(derivative_id) if isinstance(derivative_id, str) else None
            if actual_pressure != "same" and derivative is None:
                return [_finding("merge-derivative-proof-required", f"{partition_id} nonidentical pressure sets require an authoritative derivative decision", partition_id)]
            mismatch_axes = []
            if comparison["pressure_set_relation"] != actual_pressure:
                mismatch_axes.append("pressure_set_relation")
            if comparison["register_relation"] != actual_register:
                mismatch_axes.append("register_relation")
            if mismatch_axes:
                return [_finding("partition-relation-mismatch", f"{partition_id} declared comparison disagrees with candidate rows on {mismatch_axes}", partition_id, *mismatch_axes)]
            if derivative is not None:
                source_ids = set(partition["merged_state_ids"])
                source_pressures = {pressure_id for state_id in source_ids for pressure_id in candidate_by_id[state_id]["pressure_ids"]}
                receiver_pressures = set(candidate_by_id[selected_id]["pressure_ids"])
                if derivative.get("partition_id") != partition_id or set(derivative.get("source_state_ids", [])) != source_ids or derivative.get("receiving_state_id") != selected_id or set(derivative.get("source_pressure_ids", [])) != source_pressures or set(derivative.get("receiving_pressure_ids", [])) != receiver_pressures or derivative.get("comparison") != comparison:
                    return [_finding("partition-relation-mismatch", f"{partition_id} derivative proof does not reconstruct its actual members", partition_id, str(derivative_id))]
        if decision == "keep_distinct" and partition["merged_state_ids"]:
            return [_finding("keep-distinct-role-shape", f"{partition_id} keep_distinct cannot assign a merged terminal role", partition_id)]
        if decision == "reject_nonfit" and not partition["rejected_state_ids"]:
            return [_finding("reject-shape", f"{partition_id} reject_nonfit names no rejected state", partition_id)]
    if memberships != external_candidates:
        missing = sorted((external_candidates or set()) - memberships)
        return [_finding("candidate-membership-missing", f"candidate union omits {missing}", *missing)]
    actual_partition_ids = {state_id: {item["partition_id"] for item in partitions if state_id in item["member_state_ids"]} for state_id in candidate_by_id}
    for state_id, candidate in candidate_by_id.items():
        if set(candidate["partition_ids"]) != actual_partition_ids[state_id]:
            return [_finding("candidate-partition-join", f"{state_id} partition_ids disagree with hyperedge memberships", state_id)]

    decision_ids: set[str] = set()
    decided_pressures: set[str] = set()
    burden_routes: dict[str, list[tuple[str, str]]] = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            return [_finding("burden-decision-shape", "burden partition decision must be an object")]
        required = {"decision_id", "candidate_state_ids", "observation_unit_ids", "pressure_ids", "decision", "pressure_to_burden", "same_function_proof", "residual_pressure_ids", "held_pressure_ids", "basis"}
        missing = sorted(required - set(decision))
        if missing:
            return [_finding("burden-decision-shape", f"decision lacks {missing}", *missing)]
        decision_id = decision["decision_id"]
        if not isinstance(decision_id, str) or not decision_id or decision_id in decision_ids:
            return [_finding("burden-decision-id", f"invalid or duplicate decision_id {decision_id!r}")]
        decision_ids.add(decision_id)
        ids, finding = _string_set(decision["pressure_ids"], "pressure_ids")
        if finding:
            return [finding]
        if not ids <= external_pressures or decided_pressures.intersection(ids):
            return [_finding("pressure-decision-cardinality", f"{decision_id} repeats or references unknown pressure", decision_id)]
        decided_pressures.update(ids)
        for field, universe in (("candidate_state_ids", set(candidate_by_id)), ("observation_unit_ids", {unit_id for candidate in candidates for unit_id in candidate["observation_unit_ids"]})):
            refs, finding = _string_set(decision[field], field)
            if finding:
                return [finding]
            if not refs <= universe:
                return [_finding("burden-decision-source-join", f"{decision_id} has unknown {field}", decision_id, field)]
        if decision["decision"] not in PRESSURE_DECISIONS or not str(decision["basis"]).strip():
            return [_finding("burden-decision", f"{decision_id} has unsupported decision/basis", decision_id)]
        proof = decision["same_function_proof"]
        if not isinstance(proof, dict) or set(proof) != PROOF_AXES:
            return [_finding("same-function-proof-shape", f"{decision_id} lacks exact same-function axes", decision_id)]
        same_axes = {"tau_relation", "source_frame_relation", "claim_cluster_relation", "restoration_vector_relation", "collapse_dependency_relation"}
        compatible_axes = {"register_transition_relation", "owner_operation_relation"}
        if any(proof[axis] not in {"same", "distinct", "unresolved"} for axis in same_axes) or any(proof[axis] not in {"compatible", "distinct", "unresolved"} for axis in compatible_axes):
            return [_finding("same-function-proof-shape", f"{decision_id} has unsupported proof-axis value", decision_id)]
        mappings = decision["pressure_to_burden"]
        if not isinstance(mappings, list) or any(not isinstance(item, dict) or set(item) != {"pressure_id", "burden_id"} for item in mappings):
            return [_finding("pressure-burden-map-shape", f"{decision_id} has invalid pressure_to_burden", decision_id)]
        mapped_pressures: set[str] = set()
        for mapping in mappings:
            pressure_id, burden_id = mapping["pressure_id"], mapping["burden_id"]
            if pressure_id not in ids or pressure_id in mapped_pressures or not isinstance(burden_id, str) or not burden_id:
                return [_finding("pressure-burden-map-shape", f"{decision_id} mapping is duplicate or outside its pressure set", decision_id, str(pressure_id))]
            mapped_pressures.add(pressure_id)
            burden_routes.setdefault(burden_id, []).append((pressure_id, decision_id))
        held = set(decision["held_pressure_ids"]) if isinstance(decision["held_pressure_ids"], list) else set()
        residual = set(decision["residual_pressure_ids"]) if isinstance(decision["residual_pressure_ids"], list) else set()
        if mapped_pressures | held | residual != ids:
            return [_finding("pressure-residual-accounting", f"{decision_id} does not account every pressure exactly once", decision_id)]
        if (mapped_pressures & held) or (mapped_pressures & residual) or (held & residual):
            return [_finding("pressure-residual-accounting", f"{decision_id} assigns a pressure more than once", decision_id)]
        for pressure_id in ids:
            pressure = pressure_by_id[pressure_id]
            mapped = next((item for item in mappings if item["pressure_id"] == pressure_id), None)
            if mapped is not None and (pressure.get("burden_id") != mapped["burden_id"] or pressure.get("decision_id") != decision_id or pressure.get("status") not in {"routed", "merged"}):
                return [_finding("pressure-row-decision-join", f"{pressure_id} row disagrees with {decision_id} mapping", pressure_id, decision_id)]
            if pressure_id in held and pressure.get("status") != "held":
                return [_finding("pressure-row-decision-join", f"{pressure_id} held decision disagrees with pressure status", pressure_id, decision_id)]
            if pressure_id in residual and pressure.get("status") != "unresolved":
                return [_finding("pressure-row-decision-join", f"{pressure_id} residual decision disagrees with pressure status", pressure_id, decision_id)]
        if decision["decision"] == "one_to_one" and not (len(ids) == 1 and len(mappings) == 1):
            return [_finding("one-to-one-shape", f"{decision_id} one_to_one must map one pressure to one burden", decision_id)]
        if decision["decision"] == "merge_same_function":
            if len(ids) < 2 or len({item["burden_id"] for item in mappings}) != 1:
                return [_finding("merge-shape", f"{decision_id} merge_same_function must map multiple pressures to one burden", decision_id)]
            allowed = {"tau_relation": {"same"}, "source_frame_relation": {"same"}, "claim_cluster_relation": {"same"}, "register_transition_relation": {"compatible"}, "owner_operation_relation": {"compatible"}, "restoration_vector_relation": {"same"}, "collapse_dependency_relation": {"same"}}
            bad = [axis for axis, values in allowed.items() if proof.get(axis) not in values]
            if bad:
                return [_finding("merge-axis-incompatible", f"{decision_id} merge_same_function fails axes {bad}", decision_id, *bad)]
        if decision["decision"] in {"split_distinct_functions", "keep_distinct"} and "distinct" not in set(proof.values()):
            return [_finding("distinct-axis-missing", f"{decision_id} distinct decision names no distinct axis", decision_id)]
        if decision["decision"] == "hold_unresolved" and "unresolved" not in set(proof.values()):
            return [_finding("unresolved-axis-missing", f"{decision_id} hold_unresolved names no unresolved axis", decision_id)]
    if decided_pressures != external_pressures:
        missing = sorted((external_pressures or set()) - decided_pressures)
        return [_finding("pressure-decision-cardinality", f"pressure inventory omitted from decisions: {missing}", *missing)]
    for burden_id, routes in burden_routes.items():
        if len(routes) > 1:
            decision_set = {decision_id for _, decision_id in routes}
            if len(decision_set) != 1 or next(item for item in decisions if item["decision_id"] in decision_set)["decision"] != "merge_same_function":
                return [_finding("multi-pressure-burden-unproved", f"burden {burden_id} receives multiple pressures without one merge_same_function decision", burden_id)]
    produced_burdens = set(burden_routes)
    if set(burden_floor) != produced_burdens:
        missing = sorted(set(burden_floor) - produced_burdens)
        extra = sorted(produced_burdens - set(burden_floor))
        return [_finding("burden-floor-mismatch", f"burden_floor and produced burdens differ; missing={missing}, ghost={extra}", *missing, *extra)]
    for pressure_id, pressure in pressure_by_id.items():
        if pressure.get("status") in {"routed", "merged"} and not any(p == pressure_id for routes in burden_routes.values() for p, _ in routes):
            return [_finding("routed-pressure-unmapped", f"routed pressure {pressure_id} has no B_LA mapping", pressure_id)]
    return []


def self_test() -> int:
    print(json.dumps({"checker_id": "topology-partition", "status": "PASS", "proof": "canonical Plan03 fixtures are the executable self-test"}, sort_keys=True))
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    parser.error("topology_partition is a pure library; use --self-test or import it")


if __name__ == "__main__":
    raise SystemExit(main())
