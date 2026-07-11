#!/usr/bin/env python3
"""Pure Plan05 operation-capsule-v1 structure, hashing, chronology, and joins."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from typing import Any, Iterable

REQUIRED_FIELDS = {"schema","canonicalization","capsule_id","cycle_id","body_ref","body_sha256","burden_id","obligation_ids","pressure_ids","owner_id","operation","register_axis","before_state","performed_operation","after_state","delta","residual","land_contribution","source_contract_refs","operation_capsule_sha256"}
CHRONOLOGY = ["before_state", "owner.operation", "performed_evidence", "local_delta", "residual", "land_contribution"]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def operation_capsule_sha256(capsule: dict[str, Any]) -> str:
    payload = {key: value for key, value in capsule.items() if key != "operation_capsule_sha256"}
    return f"sha256:{canonical_sha256(payload)}"


def _finding(subcode: str, message: str, *markers: str) -> dict[str, Any]:
    return {"failure_class": "act_body_evidence", "failure_subcode": subcode, "message": message, "markers": list(markers)}


def _ids(value: Any, field: str) -> tuple[list[str] | None, dict[str, Any] | None]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value) or len(value) != len(set(value)):
        return None, _finding("capsule-field-shape", f"{field} must be a nonempty unique string array", field)
    return value, None


def _normalized_state(value: Any) -> str:
    return "".join(char.casefold() for char in json.dumps(value, ensure_ascii=False, sort_keys=True) if char.isalnum())


def _resolve_path(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for token in path.split("."):
        if not isinstance(current, dict) or token not in current:
            raise KeyError(path)
        current = current[token]
    return current


def validate_operation_capsule(capsule: Any) -> list[dict[str, Any]]:
    if not isinstance(capsule, dict):
        return [_finding("capsule-shape", "capsule must be an object")]
    missing = sorted(REQUIRED_FIELDS - set(capsule))
    if missing:
        return [_finding("capsule-required-fields", f"operation capsule is incomplete; missing {', '.join(missing)}", *missing)]
    extras = sorted(set(capsule) - REQUIRED_FIELDS)
    if extras:
        return [_finding("capsule-extra-fields", f"operation capsule has unsupported fields {extras}", *extras)]
    if capsule["schema"] != "daee-operation-capsule-v1" or capsule["canonicalization"] != "daee-canonical-json-v1":
        return [_finding("capsule-version", "capsule must use operation-capsule-v1 and daee-canonical-json-v1")]
    for field in ("capsule_id", "cycle_id", "body_ref", "burden_id", "owner_id", "operation", "register_axis"):
        if not isinstance(capsule[field], str) or not capsule[field].strip():
            return [_finding("capsule-field-shape", f"{field} must be a nonempty string", field)]
    if not re.fullmatch(r"B[1-9][0-9]*", capsule["burden_id"]):
        return [_finding("burden-id", "burden_id must use B<number>", "burden_id")]
    for field in ("obligation_ids", "pressure_ids", "source_contract_refs"):
        _, finding = _ids(capsule[field], field)
        if finding:
            return [finding]
    if len(capsule["obligation_ids"]) != 1:
        return [_finding("obligation-capsule-cardinality", "operation-capsule-v1 binds exactly one executed obligation", *capsule["obligation_ids"])]
    if not isinstance(capsule["before_state"], dict) or not capsule["before_state"] or not isinstance(capsule["after_state"], dict) or not capsule["after_state"]:
        return [_finding("state-shape", "before_state and after_state must be nonempty objects", "before_state", "after_state")]
    if set(capsule["before_state"].get("source_pressure_ids", [])) != set(capsule["pressure_ids"]):
        return [_finding("before-state-pressure-anchor", "before_state must exactly anchor the capsule pressure inventory", "before_state", "source_pressure_ids", *capsule["pressure_ids"])]
    if _normalized_state(capsule["before_state"]) == _normalized_state(capsule["after_state"]):
        return [_finding("before-after-identical", "before_state and after_state do not differ after canonical punctuation/whitespace normalization", "before_state", "after_state")]
    performed = capsule["performed_operation"]
    if not isinstance(performed, dict) or set(performed) != {"mechanism", "application"} or not all(isinstance(performed[key], str) and performed[key].strip() for key in performed):
        return [_finding("performed-operation-shape", "performed_operation needs distinct mechanism and application strings", "mechanism", "application")]
    if not any(re.search(rf"(?<![A-Za-z0-9_-]){re.escape(pressure_id)}(?![A-Za-z0-9_-])", performed["application"]) for pressure_id in capsule["pressure_ids"]):
        return [_finding("performed-application-join", "performed application must name at least one exact capsule pressure ID", *capsule["pressure_ids"], "application")]
    delta = capsule["delta"]
    if not isinstance(delta, dict) or set(delta) != {"delta_id", "carrier", "result", "recoverability_evidence"} or not all(isinstance(delta.get(key), str) and delta[key].strip() for key in ("delta_id", "carrier", "result")):
        return [_finding("delta-shape", "delta needs delta_id, carrier, result, and recoverability_evidence", "delta")]
    evidence = delta["recoverability_evidence"]
    if not isinstance(evidence, list) or not evidence:
        return [_finding("delta-unrecoverable", "delta has no recoverability evidence", delta["delta_id"])]
    for row in evidence:
        if not isinstance(row, dict) or set(row) != {"after_state_path", "value"} or not isinstance(row["after_state_path"], str):
            return [_finding("delta-unrecoverable", "delta recoverability row has invalid shape", delta["delta_id"])]
        try:
            actual = _resolve_path(capsule["after_state"], row["after_state_path"])
        except KeyError:
            return [_finding("delta-unrecoverable", f"after_state path {row['after_state_path']} is absent", delta["delta_id"], row["after_state_path"])]
        if actual != row["value"]:
            return [_finding("delta-unrecoverable", f"after_state path {row['after_state_path']} does not equal recoverability value", delta["delta_id"], row["after_state_path"])]
    residual = capsule["residual"]
    if not isinstance(residual, dict) or set(residual) != {"status", "pressure_ids", "basis"} or residual.get("status") not in {"none", "live", "held"} or not str(residual.get("basis", "")).strip() or not isinstance(residual.get("pressure_ids"), list):
        return [_finding("residual-shape", "residual must contain status, pressure_ids, and basis", "residual")]
    if residual["status"] == "none" and residual["pressure_ids"]:
        return [_finding("residual-shape", "residual none cannot name pressure IDs", "residual")]
    if residual["status"] in {"live", "held"} and (not residual["pressure_ids"] or not set(residual["pressure_ids"]) <= set(capsule["pressure_ids"])):
        return [_finding("residual-pressure-join", "live/held residual must name capsule pressure IDs", "residual")]
    land = capsule["land_contribution"]
    if not isinstance(land, dict) or set(land) != {"decision", "delta_ref", "basis"} or land.get("decision") not in {"contributes", "does_not_contribute"} or land.get("delta_ref") != delta["delta_id"] or not str(land.get("basis", "")).strip():
        return [_finding("land-contribution-shape", "Land contribution must join delta and explain contribution without closure", "land_contribution", delta["delta_id"])]
    if not isinstance(capsule["body_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", capsule["body_sha256"]):
        return [_finding("body-hash-shape", "body_sha256 must be 64 lowercase hex", "body_sha256")]
    if capsule["operation_capsule_sha256"] != operation_capsule_sha256(capsule):
        return [_finding("operation-capsule-hash", "operation_capsule_sha256 is not the harness-recomputed canonical hash", "operation_capsule_sha256")]
    return []


def validate_operation_record(record: Any, *, upstream_inventory: dict[str, list[str]] | None = None, upstream_inventory_sha256: str | None = None) -> list[dict[str, Any]]:
    if not isinstance(record, dict):
        return [_finding("record-shape", "record must be an object")]
    if record.get("execution_contract") != "operation-capsule-v1":
        return [_finding("record-version", "execution_contract must be operation-capsule-v1")]
    if upstream_inventory is None or upstream_inventory_sha256 is None:
        return [_finding("upstream-boundary-required", "independent obligation, pressure, and cycle inventories are required", "external")]
    if not isinstance(upstream_inventory, dict) or set(upstream_inventory) != {"obligation_ids", "pressure_ids", "cycle_ids"} or upstream_inventory_sha256 != canonical_sha256(upstream_inventory):
        return [_finding("upstream-inventory-hash", "independent Plan03/04/cycle inventory hash mismatch", "external")]
    external: dict[str, set[str]] = {}
    for field, values in upstream_inventory.items():
        parsed, finding = _ids(values, field)
        if finding:
            return [finding]
        external[field] = set(parsed or [])
    if record.get("hydration_policy") != "projection-only" or "later_hydration" in record:
        return [_finding("later-semantic-hydration", "later stages may project but cannot hydrate Plan05 evidence", "later_hydration")]
    capsules = record.get("operation_capsules")
    if not isinstance(capsules, list) or not capsules:
        return [_finding("capsule-required-fields", "operation_capsules must be a nonempty Plan05 collection", "operation_capsules")]
    capsule_ids: set[str] = set()
    body_refs: set[str] = set()
    for capsule in capsules:
        findings = validate_operation_capsule(capsule)
        if findings:
            return findings
        assert isinstance(capsule, dict)
        if capsule["capsule_id"] in capsule_ids or capsule["body_ref"] in body_refs:
            return [_finding("capsule-identity-alias", "capsule_id and body_ref must each be globally unique", capsule["capsule_id"], capsule["body_ref"])]
        capsule_ids.add(capsule["capsule_id"])
        body_refs.add(capsule["body_ref"])
    events = record.get("events")
    if not isinstance(events, list) or not all(isinstance(event, dict) and set(event) == {"event_id", "capsule_id", "sequence", "kind", "ref"} for event in events):
        return [_finding("performed-event-record-missing", "each capsule needs six exact structured operation events", "events", *CHRONOLOGY)]
    if len({event["event_id"] for event in events}) != len(events):
        return [_finding("performed-event-record-missing", "operation event IDs must be unique", "events")]
    for capsule in capsules:
        capsule_events = [event for event in events if event["capsule_id"] == capsule["capsule_id"]]
        if len(capsule_events) != 6:
            return [_finding("performed-event-record-missing", f"{capsule['capsule_id']} needs six structured events", capsule["capsule_id"], *CHRONOLOGY)]
        if [event["sequence"] for event in capsule_events] != list(range(1, 7)) or [event["kind"] for event in capsule_events] != CHRONOLOGY:
            local = next((event for event in capsule_events if event.get("kind") == "local_delta"), {})
            land = next((event for event in capsule_events if event.get("kind") == "land_contribution"), {})
            return [_finding("performed-event-order", "events must prove before_state -> owner.operation -> performed_evidence -> local_delta -> residual -> land_contribution", str(local.get("event_id", "")), str(land.get("event_id", "")), "local_delta", "land_contribution")]
        route_ref = f"route:{capsule['obligation_ids'][0]}#owner.operation"
        expected_refs = [f"capsule:{capsule['capsule_id']}#before_state", route_ref, f"capsule:{capsule['capsule_id']}#performed_operation", f"capsule:{capsule['capsule_id']}#delta", f"capsule:{capsule['capsule_id']}#residual", f"capsule:{capsule['capsule_id']}#land_contribution"]
        for event, expected in zip(capsule_events, expected_refs):
            if event["ref"] != expected:
                return [_finding("performed-event-ref", f"{event['event_id']} ref must join distinct structured field {expected}", event["event_id"], expected)]
    unknown_event_capsules = sorted({event["capsule_id"] for event in events} - capsule_ids)
    if unknown_event_capsules:
        return [_finding("performed-event-ref", "events name unknown capsules", *unknown_event_capsules)]

    obligations = record.get("obligations")
    pressures = record.get("pressures")
    routes = record.get("owner_routes")
    acts = record.get("act_row_details")
    cycles = record.get("cycles")
    if not all(isinstance(value, list) for value in (obligations, pressures, routes, acts, cycles)):
        return [_finding("join-collection-shape", "obligations, pressures, owner_routes, ACT details, and cycles must be arrays")]
    identity_fields = ((obligations, "obligation_id", "obligation-row-duplicate"), (pressures, "pressure_id", "pressure-row-duplicate"), (routes, "obligation_id", "owner-route-row-duplicate"), (acts, "obligation_id", "act-row-duplicate"), (cycles, "cycle_id", "cycle-row-duplicate"))
    for rows, field, subcode in identity_fields:
        ids = [row.get(field) for row in rows if isinstance(row, dict)]
        if len(ids) != len(rows) or not all(isinstance(item, str) and item for item in ids):
            return [_finding("join-row-shape", f"every {field} row needs a string identity", field)]
        if len(ids) != len(set(ids)):
            duplicate = next(item for item in ids if ids.count(item) > 1)
            return [_finding(subcode, f"duplicate {field} row {duplicate}", duplicate, "duplicate")]
    actual_inventory = {"obligation_ids": {row["obligation_id"] for row in obligations}, "pressure_ids": {row["pressure_id"] for row in pressures}, "cycle_ids": {row["cycle_id"] for row in cycles}}
    for field in external:
        if actual_inventory[field] != external[field]:
            return [_finding("upstream-inventory-mismatch", f"record {field} differs from independent inventory", field, "external")]
    obligation_by_id = {item.get("obligation_id"): item for item in obligations if isinstance(item, dict) and isinstance(item.get("obligation_id"), str)}
    pressure_ids = {item.get("pressure_id") for item in pressures if isinstance(item, dict)}
    route_by_obligation = {item.get("obligation_id"): item for item in routes if isinstance(item, dict) and isinstance(item.get("obligation_id"), str)}
    artifacts = record.get("body_artifacts")
    if not isinstance(artifacts, dict):
        return [_finding("body-ref-dangling", "body_artifacts must be an object")]
    for capsule in capsules:
        if set(capsule["obligation_ids"]) - set(obligation_by_id):
            return [_finding("obligation-join", "capsule obligation_ids contain unresolved IDs", *capsule["obligation_ids"])]
        for obligation_id in capsule["obligation_ids"]:
            row = obligation_by_id[obligation_id]
            for field in ("burden_id", "owner_id", "operation", "register_axis"):
                if row.get(field) != capsule[field]:
                    return [_finding("obligation-join", f"{obligation_id} disagrees on {field}", obligation_id, field)]
            if set(row.get("pressure_ids", [])) != set(capsule["pressure_ids"]):
                return [_finding("obligation-join", f"{obligation_id} disagrees on pressure_ids", obligation_id, "pressure_ids")]
            route = route_by_obligation.get(obligation_id)
            if not isinstance(route, dict) or any(route.get(field) != capsule[field] for field in ("burden_id", "owner_id", "operation", "register_axis")) or set(route.get("pressure_ids", [])) != set(capsule["pressure_ids"]):
                return [_finding("owner-route-join", "capsule obligation does not join its exact Stage03 owner route", obligation_id)]
        if not set(capsule["pressure_ids"]) <= pressure_ids:
            return [_finding("pressure-join", "capsule pressure_ids contain unresolved IDs", *capsule["pressure_ids"])]
        act_matches = [row for row in acts if isinstance(row, dict) and row.get("body_ref") == capsule["body_ref"]]
        if len(act_matches) != 1:
            return [_finding("act-capsule-join", "body_ref must join exactly one ACT detail", capsule["body_ref"])]
        act = act_matches[0]
        for field in ("burden_id", "owner_id", "operation", "register_axis"):
            if act.get(field) != capsule[field]:
                return [_finding("act-capsule-join", f"ACT/capsule mismatch on {field}", capsule["body_ref"], field)]
        if act.get("obligation_id") not in capsule["obligation_ids"] or set(act.get("pressure_ids", [])) != set(capsule["pressure_ids"]):
            return [_finding("act-capsule-join", "ACT obligation/pressure set does not join capsule", capsule["body_ref"])]
        cycle_matches = [row for row in cycles if isinstance(row, dict) and row.get("cycle_id") == capsule["cycle_id"]]
        if len(cycle_matches) != 1 or cycle_matches[0].get("burden_id") != capsule["burden_id"] or capsule["capsule_id"] not in cycle_matches[0].get("operation_capsule_ids", []) or not set(capsule["obligation_ids"]) <= set(cycle_matches[0].get("obligation_ids", [])):
            return [_finding("cycle-join", "capsule does not join cycle burden/obligation/capsule inventory", capsule["cycle_id"])]
        if capsule["body_ref"] not in artifacts or not isinstance(artifacts[capsule["body_ref"]], dict) or not isinstance(artifacts[capsule["body_ref"]].get("content"), str):
            return [_finding("body-ref-dangling", "body_ref is not dereferenceable", capsule["body_ref"])]
        artifact = artifacts[capsule["body_ref"]]
        actual_body_hash = hashlib.sha256(artifact["content"].encode("utf-8")).hexdigest()
        if artifact.get("sha256") != actual_body_hash or capsule["body_sha256"] != actual_body_hash:
            return [_finding("body-hash-mismatch", "body content, artifact hash, and capsule body_sha256 disagree", capsule["body_ref"])]
        if capsule["residual"]["status"] in {"live", "held"} and record.get("release_state") == "COMPLETE":
            return [_finding("live-residual-complete", "live/held residual blocks unqualified COMPLETE", *capsule["residual"]["pressure_ids"])]
    if {item.get("body_ref") for item in acts if isinstance(item, dict)} != body_refs:
        return [_finding("act-capsule-cardinality", "every ACT body_ref must map exactly once to the capsule collection")]
    capsule_obligations = [obligation_id for capsule in capsules for obligation_id in capsule["obligation_ids"]]
    if len(capsule_obligations) != len(set(capsule_obligations)) or set(capsule_obligations) != external["obligation_ids"] or {item["obligation_id"] for item in acts} != external["obligation_ids"]:
        return [_finding("obligation-capsule-cardinality", "each authoritative executed obligation must bind exactly one capsule and one ACT", *sorted(external["obligation_ids"]))]
    hashes = record.get("operation_capsule_hashes")
    expected_hashes = {capsule["body_ref"]: capsule["operation_capsule_sha256"] for capsule in capsules}
    if not isinstance(hashes, dict) or hashes != expected_hashes:
        return [_finding("operation-capsule-hash-join", "operation_capsule_hashes must exactly bind every body_ref to its canonical capsule hash", *sorted(body_refs))]
    return []


def self_test() -> int:
    capsule = {"schema":"daee-operation-capsule-v1","canonicalization":"daee-canonical-json-v1","capsule_id":"OC1","cycle_id":"C1","body_ref":"B1_1","body_sha256":hashlib.sha256(b"alpha").hexdigest(),"burden_id":"B1","obligation_ids":["O1"],"pressure_ids":["P1"],"owner_id":"owner","operation":"operate","register_axis":"axis","before_state":{"state":"before","source_pressure_ids":["P1"]},"performed_operation":{"mechanism":"change the state","application":"apply the change to P1"},"after_state":{"state":"after"},"delta":{"delta_id":"D1","carrier":"Delta(B1)","result":"changed","recoverability_evidence":[{"after_state_path":"state","value":"after"}]},"residual":{"status":"none","pressure_ids":[],"basis":"none remains"},"land_contribution":{"decision":"contributes","delta_ref":"D1","basis":"the changed state contributes without deciding closure"},"source_contract_refs":["ref"],"operation_capsule_sha256":""}
    capsule["operation_capsule_sha256"] = operation_capsule_sha256(capsule)
    ok = not validate_operation_capsule(capsule)
    print(json.dumps({"checker_id":"operation-capsule-contract","status":"PASS" if ok else "FAIL","proof":"Plan05 shape and canonical hash"}, sort_keys=True))
    return 0 if ok else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    parser.error("operation_capsule_contract is a pure library; use --self-test or import it")


if __name__ == "__main__":
    raise SystemExit(main())
