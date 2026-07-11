#!/usr/bin/env python3
"""Plan04 Stage03 owner routes, Stage04 ACT rows, and terminal dispositions."""
from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any, Iterable

EXECUTION_CLASSES = {"required", "contingent", "optional_non_load_bearing", "hold_partial"}
ROUTE_STATUSES = {"executable", "held", "partial"}
BODY_STATUSES = {"loaded", "not_loaded", "vocabulary_gap"}
DISPOSITIONS = {"executed", "integrated_duplicate", "contingent_not_triggered", "optional_not_selected", "held", "partial"}
COHESION_AXES = {"target_family_relation", "tau_relation", "source_frame_relation", "claim_cluster_relation", "restoration_vector_relation", "already_handled"}


def stable_obligation_id(burden_id: str, pressure_ids: list[str], owner_id: str, operation: str) -> str:
    payload = {"burden_id": burden_id, "operation": operation, "owner_id": owner_id, "pressure_ids": sorted(set(pressure_ids))}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return f"O-{digest[:24]}"


def obligation_set_sha256(obligation_ids: list[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(obligation_ids), separators=(",", ":")).encode("utf-8")).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _finding(subcode: str, message: str, *markers: str) -> dict[str, Any]:
    return {"failure_class": "owner-obligation-coverage", "failure_subcode": subcode, "message": message, "markers": list(markers)}


def _ids(value: Any, field: str, *, allow_empty: bool = False) -> tuple[list[str] | None, dict[str, Any] | None]:
    if not isinstance(value, list) or (not allow_empty and not value) or not all(isinstance(item, str) and item for item in value) or len(value) != len(set(value)):
        return None, _finding("collection-shape", f"{field} must be a {'possibly empty ' if allow_empty else 'nonempty '}unique string array", field)
    return value, None


def validate_owner_obligation_coverage(record: Any, *, upstream_obligation_ids: list[str] | None = None, upstream_pressure_ids: list[str] | None = None, upstream_partition_decision_ids: list[str] | None = None, upstream_derivative_inventory: list[dict[str, Any]] | None = None, upstream_derivative_inventory_sha256: str | None = None) -> list[dict[str, Any]]:
    if not isinstance(record, dict):
        return [_finding("record-shape", "record must be an object")]
    if record.get("topology_contract") != "input-pressure-v1":
        return [_finding("contract-version", "topology_contract must be input-pressure-v1")]
    if upstream_obligation_ids is None or upstream_pressure_ids is None or upstream_partition_decision_ids is None or upstream_derivative_inventory is None or upstream_derivative_inventory_sha256 is None:
        return [_finding("upstream-boundary-required", "independent obligation, pressure, partition-decision, and derivative inventories are required", "external")]
    if not isinstance(upstream_derivative_inventory, list) or upstream_derivative_inventory_sha256 != _canonical_sha256(upstream_derivative_inventory):
        return [_finding("derivative-inventory-hash", "independent Plan03 derivative inventory hash mismatch", "derivative", "external")]
    embedded_derivatives = record.get("partition_derivative_mappings", [])
    if embedded_derivatives != upstream_derivative_inventory:
        return [_finding("derivative-inventory-mismatch", "record derivative projection differs from independent Plan03 inventory", "derivative", "external")]
    derivative_by_id: dict[str, dict[str, Any]] = {}
    derivative_fields = {"decision_id", "decision", "source_obligation_ids", "receiving_obligation_id", "source_pressure_ids", "receiving_pressure_ids", "same_function_proof"}
    for derivative in upstream_derivative_inventory:
        if not isinstance(derivative, dict) or set(derivative) != derivative_fields:
            return [_finding("derivative-inventory-shape", "Plan03 derivative row lacks exact fields", "derivative")]
        decision_id = derivative.get("decision_id")
        if not isinstance(decision_id, str) or not decision_id or decision_id in derivative_by_id:
            return [_finding("derivative-decision-duplicate", f"duplicate derivative decision {decision_id}", str(decision_id), "duplicate")]
        if derivative.get("decision") not in {"merge_equivalent", "merge_same_function", "shared_operation"}:
            return [_finding("derivative-inventory-shape", f"{decision_id} has unsupported derivative decision", decision_id)]
        proof = derivative.get("same_function_proof")
        if not isinstance(proof, dict) or set(proof) != {"register_transition_relation", "owner_operation_relation", "restoration_vector_relation"} or any(value != "same" for value in proof.values()):
            return [_finding("derivative-proof-shape", f"{decision_id} lacks exact same-function proof", decision_id)]
        for field in ("source_obligation_ids", "source_pressure_ids", "receiving_pressure_ids"):
            _, finding = _ids(derivative.get(field), field)
            if finding:
                return [finding]
        derivative_by_id[decision_id] = derivative
    external_ids, finding = _ids(upstream_obligation_ids, "upstream_obligation_ids")
    if finding:
        return [finding]
    external_pressure_ids, finding = _ids(upstream_pressure_ids, "upstream_pressure_ids")
    if finding:
        return [finding]
    external_partition_ids, finding = _ids(upstream_partition_decision_ids, "upstream_partition_decision_ids")
    if finding:
        return [finding]
    embedded_ids, finding = _ids(record.get("upstream_obligation_ids"), "upstream_obligation_ids")
    if finding:
        return [finding]
    if record.get("upstream_obligation_set_sha256") != obligation_set_sha256(record["upstream_obligation_ids"]):
        return [_finding("obligation-universe-hash", "embedded obligation inventory hash mismatch", "upstream_obligation_set_sha256")]
    if set(embedded_ids or []) != set(external_ids or []):
        missing = sorted(set(external_ids or []) - set(embedded_ids or []))
        return [_finding("upstream-boundary-mismatch", f"embedded obligation inventory omits external IDs {missing}", *missing, "external")]

    routes = record.get("owner_routes")
    acts = record.get("act_row_details")
    dispositions = record.get("owner_execution_dispositions")
    if not all(isinstance(value, list) for value in (routes, acts, dispositions)):
        return [_finding("collection-shape", "owner_routes, act_row_details, and owner_execution_dispositions must be arrays")]
    route_by_id: dict[str, dict[str, Any]] = {}
    for route in routes:
        if not isinstance(route, dict):
            return [_finding("route-shape", "owner route must be an object")]
        required = {"obligation_id", "burden_id", "pressure_ids", "partition_decision_id", "owner_id", "operation", "register_axis", "execution_class", "route_status", "trigger", "owner_body_status", "same_burden_cohesion", "basis"}
        missing = sorted(required - set(route))
        if missing:
            return [_finding("route-shape", f"owner route lacks {missing}", *missing)]
        obligation_id = route["obligation_id"]
        if not isinstance(obligation_id, str) or not obligation_id or obligation_id in route_by_id:
            return [_finding("obligation-id", f"invalid or duplicate obligation_id {obligation_id!r}")]
        pressure_ids, finding = _ids(route["pressure_ids"], "pressure_ids")
        if finding:
            return [finding]
        if not set(pressure_ids or []) <= set(external_pressure_ids or []):
            return [_finding("route-pressure-join", f"{obligation_id} references pressure outside the independent Plan02 inventory", obligation_id, *sorted(set(pressure_ids or []) - set(external_pressure_ids or [])), "external")]
        if route["partition_decision_id"] not in set(external_partition_ids or []):
            return [_finding("route-partition-join", f"{obligation_id} references a partition decision outside the independent Plan03 inventory", obligation_id, str(route["partition_decision_id"]), "external")]
        for field in ("burden_id", "partition_decision_id", "owner_id", "operation", "register_axis", "basis"):
            if not isinstance(route[field], str) or not route[field].strip():
                return [_finding("route-shape", f"{obligation_id} omits {field}", obligation_id, field)]
        derived = stable_obligation_id(route["burden_id"], pressure_ids or [], route["owner_id"], route["operation"])
        if obligation_id != derived:
            return [_finding("unstable-obligation-id", f"declared {obligation_id} does not equal derived {derived}", obligation_id, derived)]
        if route["execution_class"] not in EXECUTION_CLASSES or route["route_status"] not in ROUTE_STATUSES or route["owner_body_status"] not in BODY_STATUSES:
            return [_finding("route-vocabulary", f"{obligation_id} has unsupported execution/route/body status", obligation_id)]
        cohesion = route["same_burden_cohesion"]
        if not isinstance(cohesion, dict) or set(cohesion) != COHESION_AXES or not isinstance(cohesion["already_handled"], bool) or any(cohesion[axis] not in {"same", "distinct", "unresolved"} for axis in COHESION_AXES - {"already_handled"}):
            return [_finding("cohesion-shape", f"{obligation_id} lacks exact relational cohesion", obligation_id)]
        if route["execution_class"] in {"required", "contingent"} and route["route_status"] == "executable" and route["owner_body_status"] != "loaded":
            return [_finding("executable-body-state", f"{obligation_id} executable route has no loaded owner body", obligation_id)]
        if route["execution_class"] == "contingent" and (not isinstance(route["trigger"], str) or not route["trigger"].strip()):
            return [_finding("contingent-trigger", f"{obligation_id} contingent route needs an explicit trigger", obligation_id)]
        if route["execution_class"] != "contingent" and route["trigger"] is not None:
            return [_finding("contingent-trigger", f"{obligation_id} non-contingent route cannot carry trigger", obligation_id)]
        if route["execution_class"] == "optional_non_load_bearing" and not str(route.get("non_load_bearing_basis", "")).strip():
            return [_finding("optional-basis", f"{obligation_id} optional route lacks non-load-bearing basis", obligation_id)]
        if route["execution_class"] == "hold_partial" and (route["route_status"] not in {"held", "partial"} or not str(route.get("blocker", "")).strip() or not str(route.get("next_action", "")).strip()):
            return [_finding("open-route-custody", f"{obligation_id} hold_partial route needs held/partial status, blocker, and next_action", obligation_id)]
        if route["route_status"] == "executable" and (cohesion["already_handled"] or any(cohesion[axis] in {"distinct", "unresolved"} for axis in COHESION_AXES - {"already_handled"})):
            return [_finding("cohesion-repartition-required", f"{obligation_id} has distinct, unresolved, or already-handled cohesion and must repartition or hold before execution", obligation_id, "same_burden_cohesion")]
        route_by_id[obligation_id] = route
    if set(route_by_id) != set(external_ids or []):
        missing = sorted(set(external_ids or []) - set(route_by_id))
        extra = sorted(set(route_by_id) - set(external_ids or []))
        return [_finding("obligation-universe-mismatch", f"owner routes differ from external inventory; missing={missing}, extra={extra}", *missing, *extra, "upstream")]

    act_by_id: dict[str, dict[str, Any]] = {}
    for act in acts:
        if not isinstance(act, dict):
            return [_finding("act-shape", "ACT detail must be an object")]
        required = {"obligation_id", "burden_id", "pressure_ids", "owner_id", "operation", "register_axis", "body_ref"}
        missing = sorted(required - set(act))
        if missing:
            return [_finding("act-shape", f"ACT detail lacks {missing}", *missing)]
        obligation_id = act["obligation_id"]
        if obligation_id in act_by_id:
            return [_finding("act-duplicate", f"duplicate ACT for {obligation_id}", str(obligation_id))]
        route = route_by_id.get(obligation_id)
        if route is None:
            return [_finding("orphan-act", f"ACT names unrouted obligation {obligation_id}", str(obligation_id))]
        for field in ("burden_id", "pressure_ids", "owner_id", "operation", "register_axis"):
            if act[field] != route[field]:
                return [_finding("act-route-mismatch", f"ACT {obligation_id} disagrees on {field}", obligation_id, field)]
        if not isinstance(act["body_ref"], str) or not act["body_ref"]:
            return [_finding("act-shape", f"ACT {obligation_id} needs body_ref", obligation_id)]
        act_by_id[obligation_id] = act

    disposition_by_id: dict[str, dict[str, Any]] = {}
    for disposition in dispositions:
        if not isinstance(disposition, dict):
            return [_finding("disposition-shape", "terminal disposition must be an object")]
        required = {"obligation_id", "burden_id", "disposition", "body_ref", "satisfied_by_obligation_id", "trigger_evidence", "basis", "gate", "next_action"}
        missing = sorted(required - set(disposition))
        if missing:
            return [_finding("disposition-shape", f"disposition lacks {missing}", *missing)]
        obligation_id = disposition["obligation_id"]
        if obligation_id in disposition_by_id or obligation_id not in route_by_id:
            return [_finding("disposition-id", f"duplicate or unrouted disposition {obligation_id}", str(obligation_id))]
        route = route_by_id[obligation_id]
        if disposition["burden_id"] != route["burden_id"] or disposition["disposition"] not in DISPOSITIONS or not str(disposition["basis"]).strip():
            return [_finding("disposition-shape", f"{obligation_id} disposition is unsupported or mismatched", obligation_id)]
        disposition_by_id[obligation_id] = disposition
    if set(disposition_by_id) != set(route_by_id):
        missing = sorted(set(route_by_id) - set(disposition_by_id))
        return [_finding("eligible-obligation-unpaid", f"Stage03 obligations have no Stage04 terminal disposition: {missing}", *missing, "eligible-obligation-unpaid")]

    executed_ids = {obligation_id for obligation_id, item in disposition_by_id.items() if item["disposition"] == "executed"}
    if set(act_by_id) != executed_ids:
        missing_acts = sorted(executed_ids - set(act_by_id))
        unsupported_acts = sorted(set(act_by_id) - executed_ids)
        return [_finding("act-execution-set-mismatch", f"A=X violated; missing ACT={missing_acts}, nonexecuted ACT={unsupported_acts}", *missing_acts, *unsupported_acts, "A=X")]
    for decision_id, mapping in derivative_by_id.items():
        source_ids = set(mapping["source_obligation_ids"])
        receiver = mapping.get("receiving_obligation_id")
        if not source_ids <= set(route_by_id) or receiver not in route_by_id or receiver in source_ids:
            return [_finding("derivative-obligation-join", f"{decision_id} does not join routed source and receiver obligations", decision_id)]
        source_pressures = {pressure_id for obligation_id in source_ids for pressure_id in route_by_id[obligation_id]["pressure_ids"]}
        receiver_pressures = set(route_by_id[receiver]["pressure_ids"])
        if set(mapping["source_pressure_ids"]) != source_pressures or set(mapping["receiving_pressure_ids"]) != receiver_pressures:
            return [_finding("derivative-pressure-join", f"{decision_id} pressure projection does not match its routed obligations", decision_id)]
    for obligation_id, disposition in disposition_by_id.items():
        route = route_by_id[obligation_id]
        kind = disposition["disposition"]
        if kind == "executed":
            act = act_by_id[obligation_id]
            if route["route_status"] != "executable" or disposition["body_ref"] != act["body_ref"] or any(disposition[field] is not None for field in ("satisfied_by_obligation_id", "trigger_evidence", "gate", "next_action")):
                return [_finding("executed-disposition-join", f"{obligation_id} executed disposition does not exactly join its ACT", obligation_id)]
        else:
            if disposition["body_ref"] is not None:
                return [_finding("nonexecuted-body-ref", f"{obligation_id} nonexecuted disposition cannot name body_ref", obligation_id)]
        if kind == "integrated_duplicate":
            if route["route_status"] != "executable" or any(disposition[field] is not None for field in ("trigger_evidence", "gate", "next_action")):
                return [_finding("duplicate-receiver", f"{obligation_id} integrated duplicate has incompatible route or fields", obligation_id)]
            receiver = disposition["satisfied_by_obligation_id"]
            if receiver not in executed_ids or receiver == obligation_id:
                return [_finding("duplicate-receiver", f"{obligation_id} lacks a distinct executed receiver", obligation_id, str(receiver))]
            receiver_route = route_by_id[receiver]
            same_transition = all(route[field] == receiver_route[field] for field in ("owner_id", "operation", "register_axis", "pressure_ids"))
            mapping = derivative_by_id.get(disposition.get("derivative_decision_id"))
            mapped = isinstance(mapping, dict) and mapping.get("decision") in {"merge_equivalent", "merge_same_function", "shared_operation"} and obligation_id in mapping.get("source_obligation_ids", []) and mapping.get("receiving_obligation_id") == receiver
            if not same_transition and not mapped:
                return [_finding("duplicate-derivative-proof", f"{obligation_id} has no same transition or Plan03 derivative mapping", obligation_id, str(receiver))]
        elif kind == "contingent_not_triggered":
            if route["execution_class"] != "contingent" or route["route_status"] != "executable" or not str(disposition["trigger_evidence"] or "").strip() or any(disposition[field] is not None for field in ("satisfied_by_obligation_id", "gate", "next_action")):
                return [_finding("contingent-trigger", f"{obligation_id} contingent_not_triggered lacks typed route/evidence", obligation_id)]
        elif kind == "optional_not_selected":
            if route["execution_class"] != "optional_non_load_bearing" or any(disposition[field] is not None for field in ("satisfied_by_obligation_id", "trigger_evidence", "gate", "next_action")):
                return [_finding("optional-class-mismatch", f"{obligation_id} optional_not_selected is not an exact optional non-load-bearing disposition", obligation_id)]
        elif kind in {"held", "partial"}:
            if not str(disposition["gate"] or "").strip() or not str(disposition["next_action"] or "").strip() or any(disposition[field] is not None for field in ("satisfied_by_obligation_id", "trigger_evidence")):
                return [_finding("open-disposition-custody", f"{obligation_id} {kind} needs gate and next_action", obligation_id)]
            if route["execution_class"] != "hold_partial" and record.get("stage04_status") == "pass":
                return [_finding("newly-declined-executable-pass", f"newly declined executable {obligation_id} cannot keep Stage04 pass", obligation_id)]
        if route["execution_class"] == "required" and kind not in {"executed", "integrated_duplicate", "held", "partial"}:
            return [_finding("required-disposition-law", f"required obligation {obligation_id} has illegal disposition {kind}", obligation_id)]
        if route["execution_class"] == "hold_partial" and kind not in {"held", "partial"}:
            return [_finding("open-route-disposition-law", f"hold_partial obligation {obligation_id} must remain held or partial", obligation_id)]
    if any(item["disposition"] in {"held", "partial"} for item in dispositions) and record.get("downstream_release_state") == "COMPLETE":
        return [_finding("open-obligation-complete", "held/partial obligation cannot coexist with downstream COMPLETE", "COMPLETE")]
    return []


def self_test() -> int:
    oid = stable_obligation_id("B1", ["P2", "P1"], "owner", "operate")
    ok = oid == stable_obligation_id("B1", ["P1", "P2"], "owner", "operate")
    print(json.dumps({"checker_id": "owner-obligation-coverage", "status": "PASS" if ok else "FAIL", "proof": "order-independent stable obligation IDs"}, sort_keys=True))
    return 0 if ok else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    parser.error("owner_obligation_coverage is a pure library; use --self-test or import it")


if __name__ == "__main__":
    raise SystemExit(main())
