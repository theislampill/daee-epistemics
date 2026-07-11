from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


HEX_A = "a" * 64
HEX_B = "b" * 64
COMMIT_A = "1" * 40
COMMIT_B = "2" * 40
NONCLAIMS_CAPTURE = [
    "structural PASS is not semantic truth",
    "one capture is not a cross-host behavior claim",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(root: Path, relative: str, value: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def write_json(root: Path, relative: str, value: Any) -> None:
    write_text(root, relative, json.dumps(value, indent=2, sort_keys=True) + "\n")


def artifact(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    return {"path": relative, "sha256": sha256(path), "byte_count": path.stat().st_size}


def _base_files(root: Path) -> None:
    write_text(root, "input.txt", "neutral input\n")
    write_text(root, "output.md", "neutral governed output\n")
    write_text(root, "package.skill", "immutable package bytes\n")
    write_text(root, "package-base.skill", "immutable base package bytes\n")
    write_json(root, "build-manifest.json", {"schema":"daee-package-build-manifest-v1","build_id": "build-alpha", "source_commit": COMMIT_A,"package_sha256":sha256(root/"package.skill")})
    write_json(root, "build-manifest-base.json", {"schema":"daee-package-build-manifest-v1","build_id": "build-base", "source_commit": COMMIT_B,"package_sha256":sha256(root/"package-base.skill")})
    write_text(root, "invocation.txt", "synthetic invocation\n")
    write_text(root, "checker.stdout", "PASS\n")
    write_text(root, "checker.stderr", "")
    write_text(root,"checker.py","# neutral checker source\n")
    checker_tuple={"checker_id":"neutral-checker","command":"neutral-checker --artifact output.md","checker_source_sha256":sha256(root/"checker.py"),"exit_code":0,"stdout_sha256":sha256(root/"checker.stdout"),"stderr_sha256":sha256(root/"checker.stderr"),"first_failure":False}
    write_json(root, "verifier-verdict.json", {"schema":"daee-checker-replay-verdict-v1","verifier_commit":COMMIT_A,"aggregate_status": "PASS", "first_failed_checker":None,"output_sha256": sha256(root / "output.md"),"checker_results":[checker_tuple]})
    write_json(root, "verifier-verdict-base.json", {"schema":"daee-checker-replay-verdict-v1","verifier_commit":COMMIT_B,"aggregate_status": "PASS", "first_failed_checker":None,"output_sha256": sha256(root / "output.md"),"checker_results":[checker_tuple]})
    for stage in range(1, 9):
        write_json(root, f"stages/stage-{stage:02d}.json", {"schema":"daee-stage-record-v1","stage_id":f"{stage:02d}","case_id":"case-alpha","cycle_id":"cycle-alpha","input_sha256":sha256(root/"input.txt"),"output_sha256":sha256(root/"output.md"),"source_commit":COMMIT_A,"package_sha256":sha256(root/"package.skill"),"checker_id":f"stage-checker-{stage:02d}","verdict":"PASS"})
        write_json(root, f"stages-base/stage-{stage:02d}.json", {"schema":"daee-stage-record-v1","stage_id":f"{stage:02d}","case_id":"case-alpha","cycle_id":"cycle-alpha","input_sha256":sha256(root/"input.txt"),"output_sha256":sha256(root/"output.md"),"source_commit":COMMIT_B,"package_sha256":sha256(root/"package-base.skill"),"checker_id":f"stage-checker-{stage:02d}","verdict":"PASS"})
    write_json(root, "witness.json", {"status": "PASS", "target_ids": ["target-1"]})
    write_json(root, "audit.json", {"status": "PASS"})
    write_json(root, "body.json", {"target_ids": ["target-1"], "body": "neutral evidence"})
    write_text(root, "rubric.txt", "Reconstruct before grading. Judge only the supplied artifacts.\n")
    binding={"case_id":"case-alpha","cycle_id":"cycle-alpha","protocol_id":"protocol-alpha","input_sha256":sha256(root/"input.txt"),"output_sha256":sha256(root/"output.md")}
    write_json(root, "review-authorization-1.json", {"schema":"daee-review-authorization-v1","authorization_id": "auth-1", "one_use": True,**binding})
    write_json(root, "review-authorization-2.json", {"schema":"daee-review-authorization-v1","authorization_id": "auth-2", "one_use": True,**binding})
    write_json(root, "packet-delta.json", {"schema":"daee-packet-delta-v1","added_refs": ["body.json"], "removed_refs": [],"predecessor_packet_sha256":None,**binding})
    write_json(root, "builder-red-green.json", {"schema":"daee-packet-builder-proof-v1","red_rejected":True,"green_accepted":True,**binding})
    write_json(root, "anti-bank.json", {"schema":"daee-anti-answer-bank-proof-v1","status": "PASS", "forbidden_markers": [],**binding})
    write_json(root,"cohort-manifest.json",{"schema":"daee-cold-review-cohort-v1","protocol_id":"protocol-alpha","case_ids":["case-alpha","case-beta"]})
    write_json(root, "second-review.json", {
        "schema": "daee-second-independent-review-v1",
        "case_id": "case-alpha",
        "cycle_id": "cycle-alpha",
        "reviewer_identity_or_accountable_role": "independent-reviewer-2",
        "relationship_to_patch_owner": "independent",
        "independence_basis": "did not author the patch, output, or first adjudication",
        "verdict": "PASS",
        "output": artifact(root,"output.md"),
        "patch_owner_identity_or_role":"independent-reviewer-1",
    })


def _packet_payload(root: Path, *, include_body: bool = True) -> dict[str, Any]:
    refs = [artifact(root, f"stages/stage-{stage:02d}.json") for stage in range(1, 9)]
    body_refs = [artifact(root, "body.json")] if include_body else []
    return {
        "schema": "daee-cold-review-packet-payload-v1",
        "case_id": "case-alpha",
        "cycle_id": "cycle-alpha",
        "purpose": "Cold reconstruction and artifact-bound comprehensiveness review.",
        "public_rubric": (root / "rubric.txt").read_text(encoding="utf-8"),
        "input": {**artifact(root, "input.txt"), "content_utf8": (root / "input.txt").read_text(encoding="utf-8")},
        "output": {**artifact(root, "output.md"), "content_utf8": (root / "output.md").read_text(encoding="utf-8")},
        "stage_records": refs,
        "witness_refs": [artifact(root, "witness.json")],
        "audit_refs": [artifact(root, "audit.json")],
        "body_refs": body_refs,
    }


def _write_packet(root: Path, *, prefix: str = "packet", include_body: bool = True, predecessor: dict[str, Any] | None = None) -> dict[str, Any]:
    payload_path = f"{prefix}/payload.json"
    manifest_path = f"{prefix}/manifest.json"
    write_json(root, payload_path, _packet_payload(root, include_body=include_body))
    if predecessor is not None:
        delta=load_json(root/"packet-delta.json");delta["predecessor_packet_sha256"]=predecessor["sha256"];write_json(root,"packet-delta.json",delta)
    manifest = {
        "schema": "daee-cold-review-packet-v1",
        "packet_id": prefix,
        "protocol_id": "protocol-alpha",
        "case_id": "case-alpha",
        "cycle_id": "cycle-alpha",
        "retry_mode": "initial" if predecessor is None else "rebuilt-packet",
        "input": artifact(root, "input.txt"),
        "output": artifact(root, "output.md"),
        "payload": artifact(root, payload_path),
        "predecessor_packet": predecessor,
        "packet_delta": None if predecessor is None else artifact(root, "packet-delta.json"),
        "builder_red_green_proof": None if predecessor is None else artifact(root, "builder-red-green.json"),
        "anti_answer_bank_proof": artifact(root, "anti-bank.json"),
        "review_authorization": artifact(root, "review-authorization-1.json" if predecessor is None else "review-authorization-2.json"),
        "forbidden_content": {
            "expected_answers": False,
            "expected_topology_or_counts": False,
            "favorable_exemplars": False,
            "cross_case_outputs": False,
            "prior_conversation": False,
        },
    }
    write_json(root, manifest_path, manifest)
    return artifact(root, manifest_path)


def _cold_review(root: Path, packet_ref: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "daee-cold-comprehensiveness-review-v1",
        "review_id": "cold-review-1",
        "review_protocol_id":"protocol-alpha",
        "attempt_index": 1,
        "predecessor_review_attempt": None,
        "attempt_lineage":[],
        "review_authorization": artifact(root, "review-authorization-1.json"),
        "case_id": "case-alpha",
        "cycle_id": "cycle-alpha",
        "reviewer": {
            "model_family": "gpt-5.6-sol",
            "reasoning_effort": "xhigh",
            "exact_model_identifier": "gpt-5.6-sol-resolved",
            "host": "synthetic-host",
            "fresh_context": True,
            "prior_conversation_supplied": False,
            "cross_case_context_supplied": False,
            "expected_topology_supplied": False,
            "answer_bank_supplied": False,
        },
        "packet": packet_ref,
        "input": artifact(root, "input.txt"),
        "output": artifact(root, "output.md"),
        "stage_records": [artifact(root, f"stages/stage-{stage:02d}.json") for stage in range(1, 9)],
        "witness_refs": [artifact(root, "witness.json")],
        "audit_refs": [artifact(root, "audit.json")],
        "body_refs": [artifact(root, "body.json")],
        "comprehension": {
            "status": "PASS",
            "completed_before_grading": True,
            "candidate_thesis": "neutral thesis",
            "pressure_ids": ["pressure-1"],
            "burden_ids": ["burden-1"],
            "operation_ids": ["operation-1"],
            "resultant_ids": ["resultant-1"],
            "lifecycle_summary": "no unresolved lifecycle state",
            "restoration_summary": "neutral restoration trajectory",
        },
        "grading": {
            "material_pressure_coverage": "PASS",
            "burden_partition_adequacy": "PASS",
            "submove_and_body_depth": "PASS",
            "resultant_and_recursion_honesty": "PASS",
            "closure_reconstructibility": "PASS",
            "overall": "PASS",
        },
        "findings": [{
            "finding_id": "cold-finding-1",
            "target_ids": ["target-1"],
            "severity": "material",
            "basis": "the bound body reference requires adjudication",
            "recommended_disposition": "answer",
        }],
        "invalid_classification": None,
        "selection": {"selected_for_final": True, "selection_basis": "latest-valid-lineage"},
        "protocol_replay": {
            "change_scope": "none",
            "cohort_manifest": artifact(root,"cohort-manifest.json"),
            "repeated_case_ids": [],
        },
        "non_claims": [
            "formal notation presence is not execution",
            "length is not comprehensiveness",
            "cold review PASS is not universal semantic truth",
        ],
    }


def _initial_assessment(root: Path) -> dict[str, Any]:
    return {
        "schema": "daee-topology-initial-assessment-v1",
        "assessment_id": "assessment-1",
        "case_id": "case-alpha",
        "cycle_id": "cycle-alpha",
        "input": artifact(root, "input.txt"),
        "output": artifact(root, "output.md"),
        "reviewer_identity_or_accountable_role": "independent-reviewer-1",
        "recorded_utc": "2026-07-10T12:00:00Z",
        "question_answers": [{
            "question_id": "coverage",
            "answer": "all material targets are explicitly adjudicated",
            "target_ids": ["target-1"],
            "basis": "bound output and stage evidence",
        }],
        "findings": [{"finding_id": "human-finding-1", "target_ids": ["target-1"], "severity": "nonmaterial", "basis": "neutral initial finding"}],
        "verdict": "PASS",
        "non_claims": ["initial assessment precedes cold disclosure and is not rewritten by final adjudication"],
    }


def _topology_review(root: Path, initial_ref: dict[str, Any], cold_ref: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "daee-topology-review-v1",
        "review_id": "topology-review-1",
        "case_id": "case-alpha",
        "cycle_id": "cycle-alpha",
        "input": artifact(root, "input.txt"),
        "artifacts": {
            "stage02": artifact(root, "stages/stage-02.json"),
            "stage04": artifact(root, "stages/stage-04.json"),
            "stage05": artifact(root, "stages/stage-05.json"),
            "stage07_output": artifact(root, "output.md"),
            "field_witness": artifact(root, "witness.json"),
        },
        "reviewer": {
            "identity_or_accountable_role": "independent-reviewer-1",
            "relationship_to_producer": "independent",
            "independence_basis": "did not produce the output or patch",
        },
        "reviewed_utc": "2026-07-10T14:00:00Z",
        "structural_status": "PASS",
        "initial_assessment": initial_ref,
        "cold_review_disclosure": {
            "cold_review": cold_ref,
            "disclosed_utc": "2026-07-10T13:00:00Z",
            "initial_assessment_sha256_at_disclosure": initial_ref["sha256"],
        },
        "cold_challenge_adjudications": [{
            "cold_finding_id": "cold-finding-1",
            "challenged_target_ids": ["target-1"],
            "disposition": "answered",
            "evidence_refs": [{**artifact(root, "body.json"), "target_ids": ["target-1"]}],
            "rationale_finding_id": "cold-finding-1",
            "rationale": "The bound body artifact directly records the challenged target.",
        }],
        "findings": [{"finding_id": "human-finding-1", "target_ids": ["target-1"], "severity": "nonmaterial", "basis": "neutral final finding"}],
        "verdict": "PASS",
        "owner_adjudication": {"material_reversal": False, "patch_owner_involved": False, "basis": None},
        "second_independent_review": {"required": False, "reason": "not-required", "review": None},
        "non_claims": ["review PASS is scoped human adjudication, not universal semantic truth"],
    }


def _capture(root: Path, topology_ref: dict[str, Any], cold_ref: dict[str, Any], *, capture_id: str = "capture-head", source_commit: str = COMMIT_A, package_path: str = "package.skill", build_manifest_path: str = "build-manifest.json",verdict_path: str = "verifier-verdict.json") -> dict[str, Any]:
    return {
        "schema": "daee-captured-output-v1",
        "case_id": "case-alpha",
        "cycle_id":"cycle-alpha",
        "capture_id": capture_id,
        "input": artifact(root, "input.txt"),
        "runtime": {
            "version_label": "v0.4.6.0-wip",
            "source_commit": source_commit,
            "package": artifact(root, package_path),
            "build_manifest": artifact(root, build_manifest_path),
            "identity_source": "external-custodian",
        },
        "execution": {
            "operator": "operator-alpha",
            "model_runner": "synthetic-runner",
            "model": "synthetic-model-resolved",
            "host": "synthetic-host",
            "session_id": "session-alpha",
            "started_utc": "2026-07-10T11:00:00Z",
            "fresh_session": True,
            "tool_policy": "tools-disabled",
            "output_budget": "fixed-budget-alpha",
            "retry_policy": "zero-retry",
            "continuation_policy": "zero-continuation",
            "retry_count": 0,
            "continuation_count": 0,
            "truncated": False,
            "invocation": artifact(root, "invocation.txt"),
        },
        "output": artifact(root, "output.md"),
        "structural_replay": {
            "verifier_commit": source_commit,
            "aggregate_status": "PASS",
            "first_failed_checker": None,
            "checker_results": [{
                "checker_id": "neutral-checker",
                "command": "neutral-checker --artifact output.md",
                "checker_source":artifact(root,"checker.py"),
                "checker_source_sha256": sha256(root/"checker.py"),
                "exit_code": 0,
                "stdout": artifact(root, "checker.stdout"),
                "stderr": artifact(root, "checker.stderr"),
                "first_failure": False,
            }],
            "verdict": artifact(root, verdict_path),
        },
        "topology_review": topology_ref,
        "cold_comprehensiveness_review": cold_ref,
        "historical_provenance": {"status": "complete", "missing_fields": [], "promotable": True},
        "non_claims": NONCLAIMS_CAPTURE,
    }


def build_base_bundle(root: Path) -> dict[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    _base_files(root)
    packet_ref = _write_packet(root)
    cold = _cold_review(root, packet_ref)
    write_json(root, "cold-review.json", cold)
    cold_ref = artifact(root, "cold-review.json")
    initial = _initial_assessment(root)
    write_json(root, "initial-assessment.json", initial)
    initial_ref = artifact(root, "initial-assessment.json")
    topology = _topology_review(root, initial_ref, cold_ref)
    write_json(root, "topology-review.json", topology)
    topology_ref = artifact(root, "topology-review.json")
    capture = _capture(root, topology_ref, cold_ref)
    write_json(root, "capture-manifest.json", capture)
    base_payload=load_json(root/"packet/payload.json");base_payload["stage_records"]=[artifact(root,f"stages-base/stage-{stage:02d}.json") for stage in range(1,9)];write_json(root,"packet-base/payload.json",base_payload)
    base_packet=load_json(root/"packet/manifest.json");base_packet["packet_id"]="packet-base";base_packet["payload"]=artifact(root,"packet-base/payload.json");write_json(root,"packet-base/manifest.json",base_packet)
    base_cold=copy.deepcopy(cold);base_cold["review_id"]="cold-review-base";base_cold["packet"]=artifact(root,"packet-base/manifest.json");base_cold["stage_records"]=[artifact(root,f"stages-base/stage-{stage:02d}.json") for stage in range(1,9)];write_json(root,"cold-review-base.json",base_cold);base_cold_ref=artifact(root,"cold-review-base.json")
    base_topology=copy.deepcopy(topology);base_topology["review_id"]="topology-review-base";base_topology["artifacts"].update({"stage02":artifact(root,"stages-base/stage-02.json"),"stage04":artifact(root,"stages-base/stage-04.json"),"stage05":artifact(root,"stages-base/stage-05.json")});base_topology["cold_review_disclosure"]["cold_review"]=base_cold_ref;write_json(root,"topology-review-base.json",base_topology);base_topology_ref=artifact(root,"topology-review-base.json")
    base_capture = _capture(root, base_topology_ref, base_cold_ref, capture_id="capture-base", source_commit=COMMIT_B, package_path="package-base.skill",build_manifest_path="build-manifest-base.json",verdict_path="verifier-verdict-base.json")
    write_json(root, "capture-base.json", base_capture)
    comparison = {
        "schema": "daee-captured-output-comparison-v1",
        "comparison_id": "comparison-alpha",
        "attribution_target": "pr9",
        "cells": [
            {"cell_id": "v45", "status": "not-run", "source_layer":"v45","expected_source_commit":"3"*40,"expected_package_sha256":None,"captures": []},
            {"cell_id": "inherited-main", "status": "not-run", "source_layer":"inherited-main","expected_source_commit":"4"*40,"expected_package_sha256":None,"captures": []},
            {"cell_id": "pr9-base", "status": "run", "source_layer":"pr9-base","expected_source_commit":COMMIT_B,"expected_package_sha256":sha256(root/"package-base.skill"),"captures": [artifact(root, "capture-base.json")]},
            {"cell_id": "pr9-head", "status": "run", "source_layer":"pr9-head","expected_source_commit":COMMIT_A,"expected_package_sha256":sha256(root/"package.skill"),"captures": [artifact(root, "capture-manifest.json")]},
        ],
        "pairings": [{"pair_id": "pair-1", "base_capture_id": "capture-base", "head_capture_id": "capture-head", "capture_order": ["capture-base", "capture-head"]}],
        "regression_status": "unproven",
        "basis": "No causal status is advanced by this neutral fixture.",
        "non_claims": ["output length and one pair do not prove causality", "no automated tool emits proven"],
    }
    write_json(root, "comparison.json", comparison)
    incident_attempt=copy.deepcopy(cold);incident_attempt["review_id"]="cold-review-incident";incident_attempt["comprehension"]["status"]="REVIEW_INVALID";incident_attempt["findings"]=[];incident_attempt["selection"]["selected_for_final"]=False
    for key in incident_attempt["grading"]:incident_attempt["grading"][key]="NOT_GRADED"
    write_json(root,"incident-attempt.json",incident_attempt);incident_attempt_ref=artifact(root,"incident-attempt.json")
    incident = {
        "schema": "daee-review-incident-report-v1",
        "incident_id": "incident-1",
        "case_id": "case-alpha",
        "cycle_id": "cycle-alpha",
        "classified_attempt_id": "cold-review-incident",
        "raw_attempt": incident_attempt_ref,
        "raw_output": artifact(root, "output.md"),
        "packet": packet_ref,
        "failure_class": "reviewer_transport",
        "substantive_grading_occurred": False,
        "attempt_lineage": [incident_attempt_ref],
        "owner_notification": {"owner_identity_or_role": "accountable-owner", "notified_utc": "2026-07-10T15:00:00Z"},
        "proposed_action": "same-packet-retry",
        "continuation_authority": artifact(root, "review-authorization-2.json"),
        "basis": "synthetic transport classification",
    }
    write_json(root, "incident.json", incident)
    return {
        "capture": root / "capture-manifest.json",
        "comparison": root / "comparison.json",
        "cold": root / "cold-review.json",
        "topology": root / "topology-review.json",
        "incident": root / "incident.json",
    }

def make_valid_retry(root: Path, cause: str) -> Path:
    predecessor = load_json(root / "cold-review.json")
    predecessor["review_id"] = "cold-review-0"
    predecessor["comprehension"]["status"] = "REVIEW_INVALID"
    for key in predecessor["grading"]: predecessor["grading"][key] = "NOT_GRADED"
    predecessor["findings"] = []
    predecessor["selection"] = {"selected_for_final": False, "selection_basis": "latest-valid-lineage"}
    write_json(root, "cold-review-predecessor.json", predecessor)
    pred_ref = artifact(root, "cold-review-predecessor.json")
    incident = load_json(root / "incident.json")
    incident.update({"classified_attempt_id":"cold-review-0","raw_attempt":pred_ref,"attempt_lineage":[pred_ref],"failure_class":cause,"proposed_action":"same-packet-retry" if cause=="reviewer_transport" else "rebuild-packet"})
    incident["packet"] = predecessor["packet"]
    write_json(root, "incident-retry.json", incident)
    current = load_json(root / "cold-review.json")
    current.update({"attempt_index":2,"predecessor_review_attempt":pred_ref,"review_authorization":artifact(root,"review-authorization-2.json")})
    current["attempt_lineage"]=[pred_ref]
    current["invalid_classification"]={"cause":cause,"candidate_intelligibility_observed":False,"product_andon":False,"owner_incident_report":artifact(root,"incident-retry.json")}
    if cause=="packet_insufficiency":
        current["packet"]=_write_packet(root,prefix="packet-rebuilt",predecessor=predecessor["packet"])
    write_json(root, "cold-review-retry.json", current)
    return root / "cold-review-retry.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def mutate_json(path: Path, callback) -> None:
    value = load_json(path)
    callback(value)
    write_json(path.parent, path.name, value)


def apply_fault(root: Path, fault: str) -> str:
    paths = {key: root / name for key, name in {
        "capture": "capture-manifest.json", "comparison": "comparison.json", "cold": "cold-review.json",
        "topology": "topology-review.json", "incident": "incident.json",
    }.items()}
    target = "capture"
    if fault == "missing-input-hash":
        mutate_json(paths["capture"], lambda value: value["input"].pop("sha256"))
    elif fault == "self-attested-package":
        mutate_json(paths["capture"], lambda value: value["runtime"].update({"identity_source": "captured-output"}))
    elif fault == "comparison-confound-unmarked":
        def mutate(value):
            capture = load_json(root / "capture-manifest.json"); capture["execution"]["model"] = "changed-model"; write_json(root, "capture-manifest.json", capture)
            value["cells"][3]["captures"][0] = artifact(root, "capture-manifest.json")
            value["regression_status"] = "candidate-observed"
        mutate_json(paths["comparison"], mutate); target = "comparison"
    elif fault == "comparison-overclaim":
        mutate_json(paths["comparison"], lambda value: value.update({"regression_status": "replicated-candidate"})); target = "comparison"
    elif fault == "initial-assessment-missing":
        mutate_json(paths["topology"], lambda value: value.update({"initial_assessment": None})); target = "topology"
    elif fault == "initial-assessment-hash-drift":
        mutate_json(paths["topology"], lambda value: value["cold_review_disclosure"].update({"initial_assessment_sha256_at_disclosure": HEX_B})); target = "topology"
    elif fault == "cold-adjudication-missing":
        mutate_json(paths["topology"], lambda value: value.update({"cold_challenge_adjudications": []})); target = "topology"
    elif fault == "cold-adjudication-duplicate":
        mutate_json(paths["topology"], lambda value: value["cold_challenge_adjudications"].append(copy.deepcopy(value["cold_challenge_adjudications"][0]))); target = "topology"
    elif fault == "challenge-answer-evidence-missing":
        mutate_json(paths["topology"], lambda value: value["cold_challenge_adjudications"][0].update({"evidence_refs": []})); target = "topology"
    elif fault == "challenge-answer-target-mismatch":
        mutate_json(paths["topology"], lambda value: value["cold_challenge_adjudications"][0]["evidence_refs"][0].update({"target_ids": ["different-target"]})); target = "topology"
    elif fault == "patch-owner-without-second-review":
        def mutate(value):
            value["reviewer"]["relationship_to_producer"] = "patch-owner"; value["owner_adjudication"]["patch_owner_involved"] = True
        mutate_json(paths["topology"], mutate); target = "topology"
    elif fault == "producer-self-review-pass":
        mutate_json(paths["topology"], lambda value: value["reviewer"].update({"relationship_to_producer": "producer", "independence_basis": "self review"})); target = "topology"
    elif fault == "unresolved-material-pass":
        mutate_json(paths["topology"], lambda value: value["cold_challenge_adjudications"][0].update({"disposition": "unresolved"})); target = "topology"
    elif fault == "structural-waiver":
        mutate_json(paths["topology"], lambda value: value.update({"structural_status": "FAIL", "verdict": "PASS"})); target = "topology"
    elif fault == "grades-before-comprehension":
        mutate_json(paths["cold"], lambda value: value["comprehension"].update({"completed_before_grading": False})); target = "cold"
    elif fault == "prior-context":
        mutate_json(paths["cold"], lambda value: value["reviewer"].update({"prior_conversation_supplied": True})); target = "cold"
    elif fault == "review-invalid-laundered":
        def mutate(value):
            value["comprehension"]["status"] = "REVIEW_INVALID"; value["grading"]["overall"] = "FAIL"
        mutate_json(paths["cold"], mutate); target = "cold"
    elif fault == "retry-before-incident":
        def mutate(value):
            value["attempt_index"] = 2; value["predecessor_review_attempt"] = artifact(root, "cold-review.json"); value["invalid_classification"] = None
        mutate_json(paths["cold"], mutate); target = "cold"
    elif fault == "candidate-intelligibility-mislabeled":
        def mutate(value):
            value["comprehension"]["status"] = "REVIEW_INVALID"
            for key in value["grading"]: value["grading"][key] = "NOT_GRADED"
            value["findings"] = []
            value["selection"]["selected_for_final"] = False
            value["invalid_classification"] = {"cause": "reviewer_transport", "candidate_intelligibility_observed": True, "product_andon": False, "owner_incident_report": artifact(root, "incident.json")}
        mutate_json(paths["cold"], mutate); target = "cold"
    elif fault == "shared-protocol-one-case":
        def mutate(value):
            value["protocol_replay"] = {"change_scope": "shared", "cohort_manifest": artifact(root,"cohort-manifest.json"), "repeated_case_ids": ["case-alpha"]}
        mutate_json(paths["cold"], mutate); target = "cold"
    elif fault == "favorable-selection":
        mutate_json(paths["cold"], lambda value: value["selection"].update({"selection_basis": "favorable-outcome"})); target = "cold"
    elif fault == "incident-lineage-missing":
        mutate_json(paths["incident"], lambda value: value.update({"attempt_lineage": []})); target = "incident"
    else:
        raise ValueError(f"unknown synthetic fault: {fault}")
    return target
