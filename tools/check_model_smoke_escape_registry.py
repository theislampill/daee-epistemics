#!/usr/bin/env python3
"""Validate append-only D19-D20 model-smoke escape state and canary evidence."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Iterable

from contract_validation import PathCustodyError
from validation_registry import ROOT, Finding, canonical_sha256, read_json, scan_anti_bank, schema_findings

CHECKER_ID = "model-smoke-escape-registry"
FIXTURE_ROOT = ROOT / "tests" / "model-smoke-escape"
LIVE_REGISTRY = FIXTURE_ROOT / "registry.json"
SCHEMA_REL = Path("schema/model-smoke-escape.schema.json")
DOWNSTREAM = ["candidate-maturity", "paid-dispatch"]


def _event_hash(event: dict[str, Any]) -> str:
    value = {key: val for key, val in event.items() if key != "event_hash"}
    return canonical_sha256(value)


def _controls() -> dict[str, Any]:
    return {
        "five_whys": ["symptom", "escape", "observable", "owner", "countermeasure"],
        "hansei": {"gap":"residual semantic behavior escaped", "cause":"no valid binary observable", "lesson":"retain review evidence"},
        "owner_source_countermeasure": {"owner":"control-owner", "source":"schema/model-smoke-escape.schema.json", "countermeasure":"strongest neutral observability"},
        "deterministic_green": ["smoke-a", "smoke-b", "full-preflight"],
        "independent_concurrence": {"accountable_owner":"control-owner", "independent_reviewer":"independent-reviewer", "basis":"reviewed scoped residual"},
        "usage_drift_resolved": True,
        "authorization_drift_resolved": True,
    }


def _scope() -> dict[str, Any]:
    return {
        "source_sha256":"1" * 64, "schema_sha256":"2" * 64, "checker_sha256":"3" * 64,
        "model_protocol_sha256":"4" * 64, "defect_signature":"neutral-transition-signature",
        "ir_artifact_boundary":"selected operation to public projection",
    }


def _no_row() -> dict[str, Any]:
    return {
        "escape_id":"escape-neutral-001", "deterministic_detectability":"NO", "status":"SCOPED_NO", "scope":_scope(),
        "detectability_basis": {
            "missing_topic_neutral_observable":"residual semantic adequacy is not fully machine observable",
            "anti_answer_bank_basis":"binary enforcement would prescribe an answer or topology",
            "strongest_topic_neutral_observability":["projection relation present", "review packet reconstructible"],
            "recheck_predicates":["checker identity changes", "new neutral relation becomes observable"],
        },
        "canary": {"topic_neutral":True, "taint_tokens":[], "red_boundary":[], "green_boundary":["observability-green"], "neighboring_valid":["neighbor-green"], "mutation_right_reason":[]},
        "causal_control":_controls(), "paid_cycle_eligible":True, "estimated_model_invocations_avoided":"unknown", "recurrence_of_escape_id":None,
    }


def _yes_row() -> dict[str, Any]:
    row = _no_row()
    row.update({"escape_id":"escape-neutral-yes", "deterministic_detectability":"YES", "status":"CLOSED", "paid_cycle_eligible":False})
    row["canary"] = {
        "topic_neutral":True, "taint_tokens":[], "red_boundary":["red-old-stage"], "green_boundary":["green-new-stage"],
        "neighboring_valid":["neighbor-valid"],
        "mutation_right_reason":[{"expected_stage":"07","observed_stage":"07","expected_class":"projection","observed_class":"projection","expected_subcode":"missing-relation","observed_subcode":"missing-relation"}],
        "ci_registry_evidence":["required-profile", "composed-preflight"],
    }
    return row


def _base_registry(row: dict[str, Any], *, maturity: str) -> dict[str, Any]:
    return {
        "schema":"daee-model-smoke-escape-v1", "registry_id":"escape-fixture-registry", "append_only":True,
        "candidate_maturity_status":maturity, "escapes":[row], "events":[],
        "structural_non_claims":["detectability status is scoped", "maturity is not model authorization", "structural controls are not semantic truth"],
    }


def _append_event(registry: dict[str, Any], event: dict[str, Any]) -> None:
    event = dict(event)
    event["sequence"] = len(registry["events"]) + 1
    event["event_id"] = f"event-{event['sequence']:04d}-{str(event['event_type']).lower().replace('_', '-')}"
    event["previous_event_hash"] = registry["events"][-1]["event_hash"] if registry["events"] else None
    event["event_hash"] = _event_hash(event)
    registry["events"].append(event)


def build_case(case_id: str) -> dict[str, Any]:
    if case_id == "closed-deterministic-escape": return _base_registry(_yes_row(), maturity="MATURE")
    if case_id == "scoped-no": return _base_registry(_no_row(), maturity="MATURE")
    if case_id == "reassessment-due-without-mutation":
        reg = _base_registry(_no_row(), maturity="MATURE")
        _append_event(reg, {"event_type":"REASSESSMENT_DUE","escape_id":"escape-neutral-001","from_state":"NO","to_state":"NO","trigger":"checker-change","state_mutated":False})
        return reg
    if case_id == "adjudicated-no-to-unknown":
        row = _no_row(); row.update({"deterministic_detectability":"UNKNOWN","status":"OPEN","paid_cycle_eligible":False})
        reg = _base_registry(row, maturity="BLOCKED")
        _append_event(reg, {"event_type":"NO_TO_UNKNOWN","escape_id":row["escape_id"],"from_state":"NO","to_state":"UNKNOWN","state_mutated":True,"automatic":False,"accountable_owner":"control-owner","independent_reviewer":"independent-reviewer","materially_new_evidence":"a neutral relation may now be observable","named_question":"can the new relation be checked without prescribed content","resolution_deadline":"2026-08-01","speculative":False})
        return reg
    if case_id == "renewed-no":
        reg = build_case("adjudicated-no-to-unknown")
        _append_event(reg, {"event_type":"UNKNOWN_TO_NO_RENEWED","escape_id":"escape-neutral-001","from_state":"UNKNOWN","to_state":"NO","state_mutated":True,"accountable_owner":"control-owner","independent_reviewer":"independent-reviewer","updated_evidence":"bounded reassessment found no valid binary observable","updated_compensating_control":"stronger independent review packet"})
        reg["escapes"][0] = _no_row(); reg["candidate_maturity_status"] = "MATURE"
        return reg
    if case_id == "open-yes-offered-mature":
        row=_yes_row(); row["status"]="OPEN"; row["paid_cycle_eligible"]=False; return _base_registry(row,maturity="MATURE")
    if case_id == "open-unknown-offered-mature":
        reg=build_case("adjudicated-no-to-unknown"); reg["candidate_maturity_status"]="MATURE"; return reg
    if case_id == "green-only-no-red-boundary":
        reg=_base_registry(_yes_row(),maturity="MATURE"); reg["escapes"][0]["canary"]["red_boundary"]=[]; return reg
    if case_id == "case-topic-tainted-canary":
        reg=_base_registry(_yes_row(),maturity="MATURE"); reg["escapes"][0]["canary"]["taint_tokens"]=["fixture-route-token"]; return reg
    if case_id == "wrong-reason-canary":
        reg=_base_registry(_yes_row(),maturity="MATURE"); reg["escapes"][0]["canary"]["mutation_right_reason"][0]["observed_subcode"]="other-relation"; return reg
    if case_id == "recurring-escape-called-closed":
        reg=_base_registry(_yes_row(),maturity="MATURE"); reg["escapes"][0]["recurrence_of_escape_id"]="escape-prior"; return reg
    if case_id == "automatic-no-to-unknown":
        reg=build_case("adjudicated-no-to-unknown"); event=reg["events"][0]; event.update({"automatic":True,"accountable_owner":None,"independent_reviewer":None}); event["event_hash"]=_event_hash(event); return reg
    if case_id == "speculative-unknown":
        reg=build_case("adjudicated-no-to-unknown"); event=reg["events"][0]; event.update({"speculative":True,"named_question":"future capability may help","resolution_deadline":None}); event["event_hash"]=_event_hash(event); return reg
    if case_id == "no-launch-waiver-lacking-controls":
        reg=_base_registry(_no_row(),maturity="MATURE"); reg["escapes"][0]["causal_control"]["deterministic_green"]=[]; return reg
    if case_id == "speculative-calls-avoided":
        reg=_base_registry(_no_row(),maturity="MATURE"); reg["escapes"][0]["estimated_model_invocations_avoided"]=5; return reg
    raise KeyError(case_id)


def validate_registry(document: Any) -> list[Finding]:
    schema_errors = schema_findings(document, SCHEMA_REL)
    if schema_errors:
        return schema_errors
    assert isinstance(document, dict)
    if document.get("append_only") is not True:
        return [Finding("append_only_contract", "append_only must be true", "append-only")]
    events = document.get("events", [])
    event_ids = [str(event["event_id"]) for event in events]
    if len(event_ids) != len(set(event_ids)):
        return [Finding("duplicate_event_id", "event IDs must be unique", "event-id")]
    event_hashes = [str(event["event_hash"]) for event in events]
    if len(event_hashes) != len(set(event_hashes)):
        return [Finding("duplicate_event_hash", "event hashes must be unique", "event-hash")]
    previous = None
    event_states: dict[str, str] = {}
    for index, event in enumerate(events, 1):
        if event.get("sequence") != index or event.get("previous_event_hash") != previous or event.get("event_hash") != _event_hash(event):
            return [Finding("event_chain_invalid", f"event {index} breaks append-only hash chain", "event-chain")]
        previous = event["event_hash"]
        kind = event.get("event_type")
        escape_id = str(event.get("escape_id", ""))
        if escape_id in event_states and event.get("from_state") != event_states[escape_id]:
            return [Finding("event_state_discontinuity", f"{escape_id} event state is discontinuous", "event-state")]
        event_states[escape_id] = str(event.get("to_state", ""))
        if kind == "REASSESSMENT_DUE" and (event.get("from_state") != "NO" or event.get("to_state") != "NO" or event.get("state_mutated") is not False):
            return [Finding("reassessment_mutated_state", "REASSESSMENT_DUE must be trigger-only NO to NO", "reassessment-event")]
        if kind == "NO_TO_UNKNOWN":
            if event.get("from_state") != "NO" or event.get("to_state") != "UNKNOWN" or event.get("state_mutated") is not True:
                return [Finding("event_transition_invalid", "NO_TO_UNKNOWN must be a mutating NO to UNKNOWN transition", "event-transition")]
            if event.get("automatic") is not False or not event.get("accountable_owner") or not event.get("independent_reviewer") or event.get("accountable_owner") == event.get("independent_reviewer"):
                return [Finding("automatic_no_to_unknown", "NO to UNKNOWN requires owner plus distinct independent reviewer", "no-to-unknown")]
            if not event.get("materially_new_evidence"):
                return [Finding("missing_new_evidence", "NO to UNKNOWN lacks materially new evidence", "new-evidence")]
            if event.get("speculative") or not event.get("named_question") or not event.get("resolution_deadline"):
                return [Finding("speculative_unknown", "UNKNOWN must be bounded by a named current question and deadline", "speculative-unknown")]
        if kind == "UNKNOWN_TO_NO_RENEWED":
            if event.get("from_state") != "UNKNOWN" or event.get("to_state") != "NO" or event.get("state_mutated") is not True:
                return [Finding("event_transition_invalid", "UNKNOWN_TO_NO_RENEWED must be a mutating UNKNOWN to NO transition", "event-transition")]
            if not all(event.get(k) for k in ("accountable_owner","independent_reviewer","updated_evidence","updated_compensating_control")) or event.get("accountable_owner") == event.get("independent_reviewer"):
                return [Finding("renewed_no_incomplete", "renewed NO lacks distinct adjudication or updated control", "renewed-no")]
    rows = document.get("escapes", [])
    ids = [row.get("escape_id") for row in rows]
    if len(ids) != len(set(ids)):
        return [Finding("duplicate_escape_id", "escape IDs must be unique", "duplicate-escape")]
    for event_id, state in event_states.items():
        if event_id not in ids:
            return [Finding("unknown_escape_event", f"event references unknown escape {event_id}", "unknown-escape")]
        row = next(item for item in rows if item.get("escape_id") == event_id)
        if row.get("deterministic_detectability") != state:
            return [Finding("event_state_mismatch", f"{event_id} row state does not match append-only event head", "event-state")]
    for row in rows:
        detect = row.get("deterministic_detectability"); status = row.get("status"); canary = row.get("canary", {})
        if detect == "NO" and status != "SCOPED_NO":
            return [Finding("detectability_status_mismatch", "NO must remain explicitly SCOPED_NO", "detectability-status")]
        if detect == "UNKNOWN" and (status != "OPEN" or row.get("paid_cycle_eligible")):
            return [Finding("detectability_status_mismatch", "UNKNOWN must be OPEN and paid-cycle ineligible", "detectability-status")]
        if detect == "YES" and row.get("paid_cycle_eligible"):
            return [Finding("detectability_status_mismatch", "YES cannot waive paid-cycle controls", "detectability-status")]
        if canary.get("topic_neutral") is not True or canary.get("taint_tokens"):
            return [Finding("case_topic_tainted_canary", "canary contains routing/topic taint", "tainted-canary")]
        if detect == "YES" and status == "CLOSED":
            required = (canary.get("red_boundary"), canary.get("green_boundary"), canary.get("neighboring_valid"), canary.get("mutation_right_reason"), canary.get("ci_registry_evidence"))
            if not all(required): return [Finding("green_only_canary", "closed YES requires red, green, neighbor, right-reason, and CI evidence", "red-boundary-missing")]
            for proof in canary.get("mutation_right_reason", []):
                for suffix in ("stage","class","subcode"):
                    if proof.get(f"expected_{suffix}") != proof.get(f"observed_{suffix}"):
                        return [Finding("wrong_reason_canary", f"mutation {suffix} differs from expected", "wrong-reason")]
        if row.get("recurrence_of_escape_id") and status == "CLOSED" and not row.get("deep_recurrence_analysis"):
            return [Finding("recurring_escape_called_closed", "recurrence requires deep root analysis before closure", "recurrence-open")]
        if detect == "NO":
            basis = row.get("detectability_basis", {})
            if not all(basis.get(k) for k in ("missing_topic_neutral_observable","anti_answer_bank_basis","strongest_topic_neutral_observability","recheck_predicates")):
                return [Finding("scoped_no_incomplete", "NO lacks scoped basis or recheck predicates", "scoped-no")]
        if detect == "NO" and row.get("paid_cycle_eligible"):
            control = row.get("causal_control", {})
            if len(control.get("five_whys", [])) != 5 or not control.get("hansei") or not control.get("owner_source_countermeasure") or not control.get("deterministic_green") or not control.get("independent_concurrence") or control.get("usage_drift_resolved") is not True or control.get("authorization_drift_resolved") is not True:
                return [Finding("no_launch_waiver_lacking_controls", "NO launch path lacks D20 causal and concurrence controls", "no-launch-controls")]
        avoided = row.get("estimated_model_invocations_avoided")
        if isinstance(avoided, int) and not row.get("blocked_invocation_receipt"):
            return [Finding("speculative_calls_avoided", "numeric calls avoided require an actual blocked planned invocation receipt", "calls-avoided")]
    if document.get("candidate_maturity_status") == "MATURE":
        for row in document.get("escapes", []):
            if (row.get("deterministic_detectability") == "YES" and row.get("status") != "CLOSED") or row.get("deterministic_detectability") == "UNKNOWN":
                return [Finding("open_detectability_offered_mature", "YES or UNKNOWN blocks candidate maturity", "maturity-block")]
    return []


EXPECTED = {
    "open-yes-offered-mature":"open_detectability_offered_mature", "open-unknown-offered-mature":"open_detectability_offered_mature",
    "green-only-no-red-boundary":"green_only_canary", "case-topic-tainted-canary":"case_topic_tainted_canary",
    "wrong-reason-canary":"wrong_reason_canary", "recurring-escape-called-closed":"recurring_escape_called_closed",
    "automatic-no-to-unknown":"automatic_no_to_unknown", "speculative-unknown":"speculative_unknown",
    "no-launch-waiver-lacking-controls":"no_launch_waiver_lacking_controls", "speculative-calls-avoided":"speculative_calls_avoided",
}


def run_fixture_inventory(root: Path, inventory: dict[str, Any]) -> tuple[list[str], tuple[int, int]]:
    problems: list[str] = []; valid=list(inventory.get("valid",[])); invalid=list(inventory.get("invalid",[]))
    for case_id in valid:
        path=root/"valid"/f"{case_id}.json"
        if not path.is_file(): problems.append(f"missing valid fixture {path}"); continue
        findings=validate_registry(build_case(case_id))
        if findings: problems.append(f"{case_id}: [{findings[0].failure_class}] {findings[0].message}")
    for case_id in invalid:
        path=root/"invalid"/f"{case_id}.json"; exp=path.with_suffix(".expectation.json")
        if not path.is_file(): problems.append(f"missing invalid fixture {path}"); continue
        if not exp.is_file(): problems.append(f"missing expectation {exp}"); continue
        expectation=read_json(exp.relative_to(ROOT))
        if "expected_failure_subcode" not in expectation: problems.append(f"{case_id}: expectation lacks expected_failure_subcode")
        findings=validate_registry(build_case(case_id)); expected=EXPECTED[case_id]
        if not findings: problems.append(f"{case_id}: invalid fixture survived")
        elif findings[0].failure_class != expected: problems.append(f"{case_id}: expected {expected}, got {findings[0].failure_class}")
    scan_paths=[path.relative_to(ROOT) for path in root.rglob("*.json")]
    scan_paths.extend((Path("tools/check_model_smoke_escape_registry.py"), SCHEMA_REL))
    problems.extend(scan_anti_bank(scan_paths))
    return problems,(len(valid),len(invalid))


def self_test() -> int:
    inventory=read_json((FIXTURE_ROOT/"inventory.json").relative_to(ROOT)); problems,counts=run_fixture_inventory(FIXTURE_ROOT,inventory)
    live_findings=validate_registry(read_json(LIVE_REGISTRY.relative_to(ROOT)))
    problems.extend(f"live: [{f.failure_class}] {f.message}" for f in live_findings)
    if problems:
        for problem in problems: print(f"FAIL: {problem}")
        print(f"model-smoke escape self-test: FAIL ({len(problems)} problem(s))"); return 1
    print(f"model-smoke escape self-test: PASS ({counts[0]} valid, {counts[1]} invalid)"); return 0


def main(argv: Iterable[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("artifact",nargs="?"); parser.add_argument("--registry"); parser.add_argument("--self-test",action="store_true"); parser.add_argument("--explain",action="store_true"); args=parser.parse_args(argv)
    if args.self_test: return self_test()
    path=args.registry or args.artifact or LIVE_REGISTRY.relative_to(ROOT)
    try: findings=validate_registry(read_json(path))
    except PathCustodyError as exc: findings=[Finding("path_custody",str(exc),exc.subcode)]
    except (OSError,ValueError,json.JSONDecodeError) as exc: findings=[Finding("malformed_json_or_path",str(exc),"malformed-json")]
    if findings:
        f=findings[0]; payload={"checker_id":CHECKER_ID,"earliest_stage":"control-plane","exit_category":"structural-rejection","exit_code":1,"failure_class":f.failure_class,"failure_subcode":f.failure_subcode,"downstream_invalidated":DOWNSTREAM,"message":f.message}
        print(json.dumps(payload,sort_keys=True) if args.explain else f"model-smoke escape registry: FAIL [{f.failure_class}/{f.failure_subcode}]: {f.message}"); return 1
    print(json.dumps({"checker_id":CHECKER_ID,"status":"PASS"},sort_keys=True) if args.explain else "model-smoke escape registry: PASS"); return 0


if __name__=="__main__": raise SystemExit(main())
