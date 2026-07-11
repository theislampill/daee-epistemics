#!/usr/bin/env python3
"""Pure opening, lifecycle, LoopBreak, and monotonic closure derivation."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from typing import Any

CLOSED_TERMINAL_STATES = {"complete", "landed", "discharged", "cleared", "rejected", "merged", "non_load_bearing", "preempted_not_instantiated"}
OPEN_TERMINAL_STATES = {"open", "live", "held", "partial", "recurse", "unknown", "underdetermined"}
FINAL_RENDER_ORDER = ["restorative_response", "closing_formulation", "closure_reconstruction_witness", "field_witness"]
LOOPBREAK_FIELDS = {"loopbreak_id", "observed_loop_ref", "owner_ground_ref", "performed_operation_ref", "delta_ref", "post_break_graph_ref", "full_reread_ref"}
OWNER_DISPOSITIONS = {"executed", "integrated_duplicate", "contingent_not_triggered", "optional_not_selected", "held", "partial", "recurse", "executable"}


class ClosureUniverseAuthorityError(ValueError):
    """Public closure oracle was called without a valid independent universe."""

    def __init__(self, finding: dict[str, Any]) -> None:
        super().__init__(f"{finding['failure_subcode']}: {finding['message']}")
        self.finding = finding
        self.failure_subcode = finding["failure_subcode"]


def _finding(failure_class: str, subcode: str, stage: str, downstream: list[str], message: str, *markers: str) -> dict[str, Any]:
    return {"failure_class": failure_class, "failure_subcode": subcode, "earliest_stage": stage, "downstream_invalidated": downstream, "message": message, "markers": list(markers)}


def is_closed_terminal_state(value: Any) -> bool:
    return isinstance(value, str) and value.lower() in CLOSED_TERMINAL_STATES


def derive_burden_coverage(trace: dict[str, Any]) -> dict[str, Any]:
    burdens = trace.get("burdens") if isinstance(trace.get("burdens"), list) else []
    initial = [item for item in burdens if isinstance(item, dict) and item.get("origin") == "B_LA"]
    accounted_ids = [item.get("burden_id") for item in burdens if isinstance(item, dict) and isinstance(item.get("terminal_state"), str)]
    open_ids = [
        item.get("burden_id") for item in burdens
        if isinstance(item, dict) and item.get("load_bearing", True) and not is_closed_terminal_state(item.get("terminal_state"))
    ]
    return {
        "initial_coverage_complete": all(item.get("burden_id") in accounted_ids for item in initial),
        "lifecycle_accounting_complete": len(accounted_ids) == len(burdens),
        "open_burden_ids": sorted(str(item) for item in open_ids if item is not None),
    }


def derive_candidate_coverage(trace: dict[str, Any]) -> dict[str, Any]:
    candidates = trace.get("candidate_states") if isinstance(trace.get("candidate_states"), list) else []
    terminal = {"selected", "merged", "rejected", "non_load_bearing", "preempted_not_instantiated", "cleared"}
    open_ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict) and item.get("status") not in terminal]
    accounted = all(isinstance(item, dict) and isinstance(item.get("status"), str) and str(item.get("basis", "")).strip() for item in candidates)
    return {"candidate_accounting_complete": accounted, "open_candidate_ids": sorted(str(item) for item in open_ids if item is not None)}


def _loopbreak_complete(trace: dict[str, Any]) -> bool:
    loopbreak = trace.get("loopbreak")
    return isinstance(loopbreak, dict) and LOOPBREAK_FIELDS <= set(loopbreak) and all(str(loopbreak[field]).strip() for field in LOOPBREAK_FIELDS)


def derive_residual_field_state(trace: dict[str, Any]) -> dict[str, Any]:
    diagnostics = trace.get("diagnostics") if isinstance(trace.get("diagnostics"), list) else []
    divergence_values = [item.get("status") for item in diagnostics if isinstance(item, dict) and item.get("operator") == "divergence"]
    curl_values = [item.get("status") for item in diagnostics if isinstance(item, dict) and item.get("operator") == "curl"]
    divergence = "unknown" if not divergence_values or "unknown" in divergence_values else "non-neutral" if "non-neutral" in divergence_values else "neutral"
    curl = "unknown" if not curl_values or "unknown" in curl_values else "held" if "held" in curl_values else "non-null" if "non-null" in curl_values else "resolved" if "resolved" in curl_values else "null"
    return {
        "divergence": divergence,
        "curl": curl,
        "loopbreak_complete": _loopbreak_complete(trace),
    }


def validate_monotonic_transitions(trace: dict[str, Any]) -> list[dict[str, Any]]:
    transitions = trace.get("transitions")
    if not isinstance(transitions, list) or transitions[:2] != ["INTAKE", "OPEN"]:
        return [_finding("temporal-state", "trace-must-open", "01", ["02", "03", "04", "05", "06", "07", "08"], "trace must begin INTAKE -> OPEN", "INTAKE", "OPEN")]
    if "CLOSURE_CONFIRMED" in transitions:
        index = transitions.index("CLOSURE_CONFIRMED")
        if index != len(transitions) - 1 or "CLOSURE_CANDIDATE" not in transitions[:index]:
            return [_finding("public-projection", "non-monotonic-closure", "07", ["08"], "CLOSURE_CONFIRMED is terminal and requires a prior CLOSURE_CANDIDATE", "CLOSURE_CONFIRMED")]
    if "RECURSE" in transitions and "REREAD_EVALUATED" not in transitions[:transitions.index("RECURSE")]:
        return [_finding("temporal-state", "recurse-before-reread", "05", ["06", "07", "08"], "RECURSE requires a completed reread", "RECURSE", "REREAD_EVALUATED")]
    if "LOOPBREAK_APPLIED" in transitions:
        applied = transitions.index("LOOPBREAK_APPLIED")
        if "LOOPBREAK_PENDING" not in transitions[:applied] or "POST_BREAK_REREAD_PENDING" not in transitions[applied + 1:] or "REREAD_EVALUATED" not in transitions[applied + 1:]:
            return [_finding("mrp", "loopbreak-transition-order", "05", ["06", "07", "08"], "LoopBreak requires pending, applied, post-break reread pending, and evaluated states", "LOOPBREAK_APPLIED")]
    return []


def _derive_closure_decision_unchecked(trace: dict[str, Any]) -> str:
    burden = derive_burden_coverage(trace)
    candidate = derive_candidate_coverage(trace)
    field = derive_residual_field_state(trace)
    burdens = trace.get("burdens") if isinstance(trace.get("burdens"), list) else []
    obligations = trace.get("owner_obligations") if isinstance(trace.get("owner_obligations"), list) else []

    if any(isinstance(item, dict) and item.get("disposition") == "recurse" for item in obligations):
        return "RECURSE"
    if any(isinstance(item, dict) and item.get("terminal_state") in {"live", "recurse"} and item.get("next_action") for item in burdens):
        return "RECURSE"
    if field["curl"] in {"non-null", "held", "unknown"} and not field["loopbreak_complete"]:
        return "LOOPBREAK_REQUIRED"
    if any(isinstance(item, dict) and item.get("terminal_state") == "held" for item in burdens) or any(isinstance(item, dict) and item.get("disposition") == "held" for item in obligations) or candidate["open_candidate_ids"]:
        return "HOLD"
    if any(isinstance(item, dict) and item.get("terminal_state") in {"partial", "open", "unknown", "underdetermined"} for item in burdens) or any(isinstance(item, dict) and item.get("disposition") in {"partial", "executable"} for item in obligations):
        return "PARTIAL"
    lands = trace.get("lands") if isinstance(trace.get("lands"), list) else []
    rereads = trace.get("rereads") if isinstance(trace.get("rereads"), list) else []
    reread_ids = {item.get("reread_id") for item in rereads if isinstance(item, dict) and item.get("status") == "evaluated"}
    lands_reconstructed = all(isinstance(item, dict) and item.get("reread_id") in reread_ids and item.get("body_refs") and item.get("delta_ref") for item in lands)
    no_new = trace.get("no_new_resultant")
    stop_licensed = isinstance(no_new, dict) and no_new.get("stop_licensed") is True and no_new.get("candidate_ids") == []
    converged = field["divergence"] == "neutral" and (field["curl"] == "null" or (field["curl"] == "resolved" and field["loopbreak_complete"]))
    coverage = burden["initial_coverage_complete"] and burden["lifecycle_accounting_complete"] and candidate["candidate_accounting_complete"]
    if coverage and not burden["open_burden_ids"] and not candidate["open_candidate_ids"] and lands_reconstructed and stop_licensed and converged:
        witness = trace.get("witness")
        all_body_refs = {ref for land in lands if isinstance(land, dict) for ref in land.get("body_refs", [])}
        witness_refs = set(witness.get("body_refs", [])) if isinstance(witness, dict) else set()
        if trace.get("render_order") == FINAL_RENDER_ORDER and all_body_refs <= witness_refs:
            return "COMPLETE"
        return "CLOSURE_CANDIDATE"
    return "PARTIAL"


def _build_closure_witness_projection_unchecked(trace: dict[str, Any]) -> dict[str, Any]:
    burden = derive_burden_coverage(trace)
    candidate = derive_candidate_coverage(trace)
    field = derive_residual_field_state(trace)
    return {
        "trace_id": trace.get("opening", {}).get("trace_id") if isinstance(trace.get("opening"), dict) else None,
        "burden_ids": [item.get("burden_id") for item in trace.get("burdens", []) if isinstance(item, dict)],
        "open_burden_ids": burden["open_burden_ids"],
        "open_candidate_ids": candidate["open_candidate_ids"],
        "divergence": field["divergence"],
        "curl": field["curl"],
        "derived_closure_decision": _derive_closure_decision_unchecked(trace),
    }


def canonical_universe_sha256(universe: dict[str, Any]) -> str:
    payload = json.dumps(universe, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _external_authority_finding(trace: Any, upstream_universe: dict[str, Any] | None, upstream_inventory_sha256: str | None) -> dict[str, Any] | None:
    if not isinstance(trace, dict):
        return _finding("topology-accounting", "closure-universe-shape", "02", ["03", "04", "05", "06", "07", "08"], "closure trace must be an object before universe comparison")
    burdens = trace.get("burdens"); candidates = trace.get("candidate_states"); obligations = trace.get("owner_obligations")
    if not isinstance(burdens, list) or not isinstance(candidates, list) or not isinstance(obligations, list):
        return _finding("topology-accounting", "closure-universe-shape", "02", ["03", "04", "05", "06", "07", "08"], "burdens, candidate_states, and owner_obligations must be arrays")
    universe_fields = {"burden_ids", "candidate_state_ids", "owner_obligation_ids"}
    if not isinstance(upstream_universe, dict) or set(upstream_universe) != universe_fields or not isinstance(upstream_inventory_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", upstream_inventory_sha256) is None:
        return _finding("topology-accounting", "closure-universe-boundary-required", "02", ["03", "04", "05", "06", "07", "08"], "closure oracle requires an independently supplied hash-bound burden/candidate/obligation universe", "external", "upstream_universe", "upstream_inventory_sha256")
    for field in sorted(universe_fields):
        values = upstream_universe[field]
        if not isinstance(values, list) or not all(isinstance(item, str) and item for item in values) or len(values) != len(set(values)):
            return _finding("topology-accounting", "closure-universe-boundary-required", "02", ["03", "04", "05", "06", "07", "08"], f"external {field} must be a unique string array", "external", field)
    canonical_hash = canonical_universe_sha256(upstream_universe)
    if upstream_inventory_sha256 != canonical_hash:
        return _finding("topology-accounting", "closure-universe-source-mismatch", "02", ["03", "04", "05", "06", "07", "08"], "external inventory hash does not bind the supplied upstream universe", "external", "upstream_inventory_sha256", canonical_hash)
    trace_id_fields = ((burdens, "burden_id", "burden_ids"), (candidates, "candidate_id", "candidate_state_ids"), (obligations, "obligation_id", "owner_obligation_ids"))
    for rows, row_field, universe_field in trace_id_fields:
        trace_ids = [item.get(row_field) for item in rows if isinstance(item, dict) and isinstance(item.get(row_field), str) and item.get(row_field)]
        if len(trace_ids) != len(rows) or len(trace_ids) != len(set(trace_ids)):
            return _finding("topology-accounting", "closure-universe-shape", "02", ["03", "04", "05", "06", "07", "08"], f"trace {row_field} rows must have unique nonempty IDs", row_field)
        external_ids = set(upstream_universe[universe_field])
        if set(trace_ids) != external_ids:
            missing = sorted(external_ids - set(trace_ids)); ghost = sorted(set(trace_ids) - external_ids)
            return _finding("topology-accounting", "closure-universe-mismatch", "02", ["03", "04", "05", "06", "07", "08"], f"trace {row_field} universe differs from external authority; missing={missing}, ghost={ghost}", *missing, *ghost, "external", universe_field)
    return None


def derive_closure_decision(trace: dict[str, Any], *, upstream_universe: dict[str, Any] | None = None, upstream_inventory_sha256: str | None = None) -> str:
    finding = _external_authority_finding(trace, upstream_universe, upstream_inventory_sha256)
    if finding is not None:
        raise ClosureUniverseAuthorityError(finding)
    return _derive_closure_decision_unchecked(trace)


def build_closure_witness_projection(trace: dict[str, Any], *, upstream_universe: dict[str, Any] | None = None, upstream_inventory_sha256: str | None = None) -> dict[str, Any]:
    finding = _external_authority_finding(trace, upstream_universe, upstream_inventory_sha256)
    if finding is not None:
        raise ClosureUniverseAuthorityError(finding)
    return _build_closure_witness_projection_unchecked(trace)


def validate_trace(trace: Any, *, upstream_universe: dict[str, Any] | None = None, upstream_inventory_sha256: str | None = None) -> list[dict[str, Any]]:
    if not isinstance(trace, dict):
        return [_finding("opening-state", "trace-shape", "01", ["02", "03", "04", "05", "06", "07", "08"], "trace must be an object")]
    opening = trace.get("opening")
    if not isinstance(opening, dict) or opening.get("opening_state_contract") != "opening-state-v2" or opening.get("phase") != "ENTRY":
        return [_finding("opening-state", "opening-contract", "01", ["02", "03", "04", "05", "06", "07", "08"], "opening-state-v2 ENTRY record is required", "opening-state-v2")]
    if opening.get("state") != "OPEN" or opening.get("closure_claim") != "PENDING":
        return [_finding("opening-state", "complete_is_terminal_only", "01", ["02", "03", "04", "05", "06", "07", "08"], "new traces must open as OPEN with closure_claim PENDING; COMPLETE is terminal only", "OPEN", "PENDING", "complete_is_terminal_only")]
    transition_findings = validate_monotonic_transitions(trace)
    if transition_findings:
        return transition_findings

    authority_finding = _external_authority_finding(trace, upstream_universe, upstream_inventory_sha256)
    if authority_finding is not None:
        return [authority_finding]
    burdens = trace["burdens"]; candidates = trace["candidate_states"]; obligations = trace["owner_obligations"]
    if trace.get("raw_exit_disposition") == "COMPLETE":
        return [_finding("mrp", "raw-complete-forbidden", "05", ["06", "07", "08"], "Stage05 raw exit cannot be COMPLETE; STOP may yield CLOSURE_CANDIDATE and only Stage07 confirms COMPLETE", "COMPLETE", "STOP", "Stage07")]
    if trace.get("proposed_closure_claim") == "COMPLETE" and not burdens and not candidates and not obligations:
        proof = trace.get("authoritative_empty_universe")
        valid_proof = isinstance(proof, dict) and proof.get("source_count") == 0 and isinstance(proof.get("source_inventory_sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", proof["source_inventory_sha256"]) and str(proof.get("basis", "")).strip()
        if not valid_proof:
            return [_finding("topology-accounting", "vacuous-closure-universe", "02", ["03", "04", "05", "06", "07", "08"], "empty closure universe requires authoritative hash-bound proof", "empty", "authoritative")]
        if proof["source_inventory_sha256"] != upstream_inventory_sha256:
            return [_finding("topology-accounting", "closure-universe-source-mismatch", "02", ["03", "04", "05", "06", "07", "08"], "empty closure proof does not join independently supplied upstream hash", "external", "source_inventory_sha256")]

    loopbreak = trace.get("loopbreak")
    if loopbreak is not None:
        if not isinstance(loopbreak, dict):
            return [_finding("mrp", "incomplete-loopbreak", "05", ["06", "07", "08"], "loopbreak must be an evidence object", "incomplete-loopbreak")]
        missing = sorted(LOOPBREAK_FIELDS - set(loopbreak) | {field for field in LOOPBREAK_FIELDS if field in loopbreak and not str(loopbreak[field]).strip()})
        if missing:
            return [_finding("mrp", "incomplete-loopbreak", "05", ["06", "07", "08"], f"LoopBreak {loopbreak.get('loopbreak_id', '<unknown>')} lacks {', '.join(missing)}", str(loopbreak.get("loopbreak_id", "")), *missing, "incomplete-loopbreak")]

        dependency_refs = {ref for item in trace.get("diagnostics", []) if isinstance(item, dict) for ref in item.get("dependency_refs", []) if isinstance(ref, str)}
        owner_refs = {item.get("obligation_id") for item in obligations if isinstance(item, dict)}
        lands_for_refs = trace.get("lands") if isinstance(trace.get("lands"), list) else []
        operation_refs = {ref for item in lands_for_refs if isinstance(item, dict) for ref in item.get("body_refs", []) if isinstance(ref, str)}
        delta_refs = {item.get("delta_ref") for item in lands_for_refs if isinstance(item, dict)}
        graph_refs = {item.get("graph_id") for item in trace.get("post_break_graphs", []) if isinstance(item, dict)} if isinstance(trace.get("post_break_graphs", []), list) else set()
        reread_refs = {item.get("reread_id") for item in trace.get("rereads", []) if isinstance(item, dict) and item.get("status") == "evaluated" and item.get("post_break") is True}
        joins = {
            "observed_loop_ref": dependency_refs,
            "owner_ground_ref": owner_refs,
            "performed_operation_ref": operation_refs,
            "delta_ref": delta_refs,
            "post_break_graph_ref": graph_refs,
            "full_reread_ref": reread_refs,
        }
        unresolved = [str(loopbreak[field]) for field, universe in joins.items() if loopbreak[field] not in universe]
        if unresolved:
            return [_finding("mrp", "loopbreak-reference-unresolved", "05", ["06", "07", "08"], f"LoopBreak references are not joined: {unresolved}", *unresolved, "loopbreak")]

    diagnostics = trace.get("diagnostics")
    if not isinstance(diagnostics, list):
        return [_finding("mrp", "diagnostic-shape", "05", ["06", "07", "08"], "diagnostics must be an array")]
    diagnostic_states: dict[tuple[str, str, str], str] = {}
    burden_targets = {item.get("burden_id") for item in burdens if isinstance(item, dict)}
    delta_targets = {item.get("delta_ref") for item in trace.get("lands", []) if isinstance(item, dict)}
    trace_target = trace.get("opening", {}).get("trace_id") if isinstance(trace.get("opening"), dict) else None
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict):
            return [_finding("mrp", "diagnostic-shape", "05", ["06", "07", "08"], "diagnostic must be an object")]
        missing = [field for field in ("operator", "target", "status", "basis_refs", "delta_ref") if field not in diagnostic or diagnostic[field] in (None, "", [])]
        if missing:
            return [_finding("mrp", "diagnostic-target", "05", ["06", "07", "08"], f"diagnostic lacks {', '.join(missing)}", *missing)]
        operator=diagnostic["operator"]
        allowed_statuses={"divergence":{"neutral","non-neutral","unknown"},"curl":{"null","non-null","resolved","held","unknown"}}
        if operator not in allowed_statuses or diagnostic["status"] not in allowed_statuses[operator]:
            return [_finding("mrp", "diagnostic-shape", "05", ["06", "07", "08"], "diagnostic operator/status vocabulary is unsupported", str(operator), str(diagnostic["status"]))]
        trace_level_empty = not burden_targets and diagnostic["target"] == trace_target
        if (diagnostic["target"] not in burden_targets and not trace_level_empty) or (not trace_level_empty and diagnostic["delta_ref"] not in delta_targets):
            return [_finding("mrp", "diagnostic-target-unresolved", "05", ["06", "07", "08"], "diagnostic target or delta does not join the burden/Land inventory", str(diagnostic["target"]), str(diagnostic["delta_ref"]))]
        key=(operator,diagnostic["target"],diagnostic["delta_ref"])
        if key in diagnostic_states and diagnostic_states[key]!=diagnostic["status"]:
            return [_finding("mrp", "diagnostic-conflict", "05", ["06", "07", "08"], "conflicting diagnostic statuses share one operator/target/delta identity", operator,diagnostic["target"],diagnostic["delta_ref"])]
        diagnostic_states[key]=diagnostic["status"]

    for obligation in obligations:
        if not isinstance(obligation,dict) or not isinstance(obligation.get("disposition"),str):
            return [_finding("owner-obligation-coverage", "obligation-disposition-missing", "04", ["05","06","07","08"], "every owner obligation requires a canonical terminal/open disposition", str(obligation.get("obligation_id") if isinstance(obligation,dict) else ""))]
        if obligation["disposition"] not in OWNER_DISPOSITIONS:
            return [_finding("owner-obligation-coverage", "obligation-disposition-invalid", "04", ["05","06","07","08"], "owner obligation disposition is outside the controlled vocabulary", str(obligation.get("obligation_id")),str(obligation["disposition"]))]

    burden = derive_burden_coverage(trace)
    candidate = derive_candidate_coverage(trace)
    proposed = trace.get("proposed_closure_claim")
    if proposed == "COMPLETE" and trace.get("transitions", [])[-2:] != ["CLOSURE_CANDIDATE", "CLOSURE_CONFIRMED"]:
        return [_finding("public-projection", "complete-without-terminal-transition", "07", ["08"], "COMPLETE requires terminal CLOSURE_CANDIDATE -> CLOSURE_CONFIRMED transitions", "CLOSURE_CANDIDATE", "CLOSURE_CONFIRMED")]
    if proposed == "COMPLETE" and (burden["open_burden_ids"] or candidate["open_candidate_ids"]):
        markers = burden["open_burden_ids"] + candidate["open_candidate_ids"]
        states = [item.get("terminal_state") for item in trace.get("burdens", []) if isinstance(item, dict) and item.get("burden_id") in burden["open_burden_ids"]]
        return [_finding("public-projection", "complete-with-open-state", "07", ["08"], f"COMPLETE coexists with open/held state {markers}", *markers, *[str(item) for item in states], "complete-with-open-state")]
    if proposed == "COMPLETE":
        open_obligations = [str(item.get("obligation_id")) for item in obligations if isinstance(item, dict) and item.get("disposition") in {"executable", "held", "partial", "recurse"}]
        if open_obligations:
            dispositions = [str(item.get("disposition")) for item in obligations if isinstance(item, dict) and str(item.get("obligation_id")) in open_obligations]
            return [_finding("public-projection", "complete-with-open-obligation", "07", ["08"], f"COMPLETE coexists with open owner obligation {open_obligations}", *open_obligations, *dispositions)]

    lands = trace.get("lands") if isinstance(trace.get("lands"), list) else []
    burden_ids = {item.get("burden_id") for item in burdens if isinstance(item, dict)}
    land_ids = [item.get("burden_id") for item in lands if isinstance(item, dict)]
    unknown_land_ids = sorted(str(item) for item in set(land_ids) - burden_ids)
    if unknown_land_ids:
        return [_finding("topology-accounting", "land-burden-join", "06", ["07", "08"], f"land targets are absent from burden universe: {unknown_land_ids}; known={sorted(str(item) for item in burden_ids)}", *unknown_land_ids, *[str(item) for item in burden_ids], "land")]
    if proposed == "COMPLETE":
        closed_load_bearing_ids = {item.get("burden_id") for item in burdens if isinstance(item, dict) and item.get("load_bearing", True) and is_closed_terminal_state(item.get("terminal_state"))}
        if set(land_ids) != closed_load_bearing_ids or len(land_ids) != len(set(land_ids)):
            return [_finding("topology-accounting", "land-burden-join", "06", ["07", "08"], "COMPLETE requires exactly one land for every closed load-bearing burden", *[str(item) for item in sorted(closed_load_bearing_ids)], "land")]

    derived = _derive_closure_decision_unchecked(trace)
    expected_coverage = {
        "initial_coverage_complete": burden["initial_coverage_complete"],
        "lifecycle_accounting_complete": burden["lifecycle_accounting_complete"] and candidate["candidate_accounting_complete"],
        "collapse_positive": derived == "COMPLETE",
        "closure_confirmed": proposed == derived,
    }
    coverage = trace.get("coverage")
    if not isinstance(coverage, dict):
        return [_finding("public-projection", "coverage-shape", "07", ["08"], "coverage predicate object is required")]
    for key, value in expected_coverage.items():
        if coverage.get(key) != value:
            return [_finding("public-projection", "coverage-predicate-mismatch", "07", ["08"], f"{key}={coverage.get(key)!r} but canonical derivation is {value!r}", key)]
    if proposed != derived:
        return [_finding("public-projection", "producer-oracle-mismatch", "07", ["08"], f"producer proposed {proposed!r}; canonical oracle derived {derived!r}", str(proposed), derived)]
    if derived == "COMPLETE" and trace.get("render_order") != FINAL_RENDER_ORDER:
        return [_finding("public-projection", "terminal-order", "07", ["08"], "complete render order must be Restorative -> Closing -> Witness -> field_witness", *FINAL_RENDER_ORDER)]
    return []


def self_test() -> int:
    trace = {"opening":{"opening_state_contract":"opening-state-v2","phase":"ENTRY","state":"OPEN","closure_claim":"PENDING"},"transitions":["INTAKE","OPEN"],"burdens":[{"burden_id":"B1"}],"candidate_states":[{"candidate_id":"N1"}],"owner_obligations":[{"obligation_id":"O1"}],"raw_exit_disposition":"COMPLETE"}
    universe = {"burden_ids":["B1"],"candidate_state_ids":["N1"],"owner_obligation_ids":["O1"]}
    findings = validate_trace(trace, upstream_universe=universe, upstream_inventory_sha256=canonical_universe_sha256(universe))
    ok = bool(findings) and findings[0].get("failure_subcode") == "raw-complete-forbidden"
    print(json.dumps({"checker_id":"opening-closure-state-lib","status":"PASS" if ok else "FAIL","proof":"Stage05 raw COMPLETE cannot bypass Stage07"}, sort_keys=True))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    parser.error("closure_state_lib is a pure library; use --self-test or import it")


if __name__ == "__main__":
    raise SystemExit(main())
