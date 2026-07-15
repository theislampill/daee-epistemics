#!/usr/bin/env python3
"""Validate Branch 10 registry, custody, usage, refusal, barrier, and verdict records."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from contract_validation import PathCustodyError, SchemaDefinitionError, resolve_repo_path, validate_schema_subset
from build_candidate_package_record import derive_transition
from check_parallel_dispatch_manifest import validate_dispatch_manifest
from check_paired_cross_model_manifest import validate_paired_manifest
from check_captured_output_manifest import validate_capture_manifest
from check_package_harness_parity import Failure as ParityFailure, validate as validate_package_parity
from check_prompt_pack_budget import BudgetViolation, DEFAULT_CEILING, validate_record as validate_prompt_record
from check_staged_runtime_handshake import record_errors as validate_handoff_record
from check_state_capsule import replay_errors_dispatch
import campaign_usage_ledger
from smoke_matrix_registry import ROOT, load_registry, validate_registry
from validation_registry import load_registry as load_validation_registry, validate_verdict as validate_registry_verdict
from artifact_tree import TREE_DIGEST_ALGORITHM, tree_sha256 as _shared_tree_digest
import execution_tooling_manifest as tooling_manifest

FIXTURES = ROOT / "tests" / "smoke-matrix" / "fixtures"
EXPECTATION_SCHEMA_PATH = ROOT / "schema" / "negative-fixture-expectation.schema.json"
SMOKE_SCHEMA_PATH = ROOT / "schema" / "smoke-matrix.schema.json"
PAIRED_SCHEMA_PATH = ROOT / "schema" / "cross-model-paired-cycle.schema.json"
KIND_DEFS = {
    "input-registry":"inputRegistry","candidate-transition":"candidateTransition","campaign-usage-reservation":"usageReservation",
    "campaign-usage-receipt":"usageReceipt","campaign-usage-recovery":"usageRecovery","candidate-package-record":"candidateRecord",
    "candidate-build-authorization":"candidateBuildAuthorization","candidate-build-claim":"candidateBuildClaim",
    "candidate-package-record-bound":"candidateRecordBound","candidate-readiness-marker":"candidateReadinessMarker","matrix-authorization":"matrixAuthorization",
    "matrix-authorization-claim":"matrixAuthorizationClaim","review-protocol":"reviewProtocol",
    "cycle-completion-attempt":"cycleAttempt","authorization-check":"authorizationCheck","usage-head-audit":"usageHeadAudit",
    "taint-audit":"taintAudit","review-gate":"reviewGate","structural-cycle":"structuralCycle","producer-outcome":"producerOutcome",
    "campaign-control":"campaignControl","dispatch-manifest":"dispatchManifest","cycle-observation":"cycleObservation",
    "cycle-observation-finalizer":"cycleObservationFinalizer","evidence-export":"evidenceExport",
    "structural-pre-review-verdict":"structuralVerdict","cycle-verdict":"reviewedVerdict",
}


def _err(cls: str, message: str) -> dict[str,str]: return {"failure_class":cls,"message":message}


def _has_reparse(path: Path) -> bool:
    try: stat_result=path.lstat()
    except OSError:return False
    return path.is_symlink() or bool(getattr(stat_result,"st_file_attributes",0)&getattr(stat_result,"FILE_ATTRIBUTE_REPARSE_POINT",0x400))


def _safe_path(base: Path, relative: str, *, directory: bool=False) -> Path:
    try:path=resolve_repo_path(base,relative,must_exist=True,expect_dir=directory,expect_file=not directory)
    except PathCustodyError as exc:raise ValueError(f"structural_path: {exc}") from exc
    lexical=base.resolve(strict=True)/Path(relative)
    current=base.resolve(strict=True)
    try:parts=lexical.relative_to(current).parts
    except ValueError as exc:raise ValueError("structural_path: artifact path escapes its custody root") from exc
    for part in parts:
        current=current/part
        if _has_reparse(current):raise ValueError(f"structural_path: symlink/reparse component is forbidden: {relative}")
    return path


def _read_ref(base: Path, reference: object) -> tuple[dict,bytes]:
    if not isinstance(reference,dict) or set(reference)!={"path","sha256"}:raise ValueError("structural_artifact_ref: exact path/hash reference required")
    path=_safe_path(base,reference["path"])
    try:raw=path.read_bytes()
    except OSError as exc:raise ValueError(f"structural_artifact_bytes: {exc}") from exc
    if hashlib.sha256(raw).hexdigest()!=reference["sha256"]:raise ValueError(f"structural_artifact_hash: hash drift at {reference['path']}")
    try:value=json.loads(raw)
    except json.JSONDecodeError as exc:raise ValueError(f"structural_artifact_bytes: {exc}") from exc
    if not isinstance(value,dict):raise ValueError("structural_artifact_bytes: referenced artifact must be a JSON object")
    return value,raw


def _external_custody_root(value: object, repo_root: Path) -> Path:
    if not isinstance(value,str) or not value:raise ValueError("structural_path: evidence custody root is required")
    path=Path(value)
    if not path.is_absolute():raise ValueError("structural_path: evidence custody root must be absolute")
    # Inspect the lexical chain before resolving it so a contained junction or symlink
    # cannot disappear into the normalized absolute path.
    current=Path(path.anchor)
    for part in path.parts[1:]:
        current=current/part
        if _has_reparse(current):raise ValueError("structural_path: evidence custody root contains a symlink/reparse component")
    try:resolved=path.resolve(strict=True)
    except OSError as exc:raise ValueError(f"structural_path: evidence custody root is unavailable: {exc}") from exc
    resolved_repo=repo_root.resolve(strict=True)
    for child,parent in ((resolved,resolved_repo),(resolved_repo,resolved)):
        try:child.relative_to(parent)
        except ValueError:continue
        raise ValueError("structural_path: evidence custody root must not overlap the mutable checkout")
    return resolved


def _read_bytes_ref(base: Path, reference: object) -> tuple[Path,bytes]:
    if not isinstance(reference,dict) or set(reference)!={"path","sha256"}:raise ValueError("structural_artifact_ref: exact path/hash reference required")
    path=_safe_path(base,reference["path"]);raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=reference["sha256"]:raise ValueError(f"structural_artifact_hash: hash drift at {reference['path']}")
    return path,raw


def _tree_digest(directory: Path) -> str:
    try:
        return _shared_tree_digest(directory)
    except ValueError as exc:
        raise ValueError(f"structural_path: {exc}") from exc


def _identity(data: dict) -> dict:
    return {field:data[field] for field in ("matrix_id","candidate_id","source_commit","package_sha256","package_tree_sha256","campaign_authorization_sha256","matrix_authorization_sha256")}


def _live_matrix_authority_errors(data: dict, root: Path) -> list[dict[str,str]]:
    try:
        parent,parent_raw=_read_ref(root,data["campaign_authorization"])
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        return [_err("campaign_authorization_binding",str(exc))]
    parent_sha=hashlib.sha256(parent_raw).hexdigest()
    if parent_sha!=data["campaign_authorization_sha256"]:
        return [_err("campaign_authorization_binding","parent campaign reference and full canonical artifact hash differ")]
    parent_keys={"schema","kind","authorization_id","status","revoked","valid_not_before","valid_not_after","branch","source_commit","source_preflight","candidate_id","candidate_state","candidate_claim_status","package_profile","package_sha256","package_tree_sha256","input_registry","review_protocol","action","lane","model_runner","producer_model","producer_reasoning_effort","authorized_calls","case_inputs","automatic_retry_authorized","optional_opus_authorized","authorization_sha256"}
    if set(parent)!=parent_keys or parent.get("schema")!="reviewed-campaign-owner-authorization-v1" or parent.get("kind")!="reviewed-five-smoke-campaign":
        return [_err("campaign_authorization_contract","parent campaign artifact has the wrong exact shape")]
    unsigned={key:value for key,value in parent.items() if key!="authorization_sha256"}
    if parent.get("authorization_sha256")!=hashlib.sha256((json.dumps(unsigned,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest():
        return [_err("campaign_authorization_contract","parent campaign unsigned self-hash is invalid")]
    exact={"status":"ACTIVE","revoked":False,"branch":data["branch"],"source_commit":data["source_commit"],"source_preflight":data["source_preflight"],"candidate_id":data["candidate_id"],"candidate_state":"READY_UNUSED","candidate_claim_status":"UNCLAIMED","package_profile":"execution-mini","package_sha256":data["package_sha256"],"package_tree_sha256":data["package_tree_sha256"],"input_registry":data["input_registry"],"review_protocol":data["review_protocol"],"action":"RUN_REVIEWED_FIVE_SMOKE","lane":"producer","model_runner":"codex","producer_model":"gpt-5.5","producer_reasoning_effort":"high","authorized_calls":5,"case_inputs":data["case_inputs"],"automatic_retry_authorized":False,"optional_opus_authorized":False}
    if any(parent.get(field)!=value for field,value in exact.items()):
        return [_err("campaign_authorization_contract","parent campaign scope differs from the child source/candidate/registry/model/case delegation")]
    try:
        execution_tooling,execution_tooling_raw=_read_ref(root,data["execution_tooling_manifest"])
        if execution_tooling_raw!=(json.dumps(execution_tooling,sort_keys=True,separators=(",",":"))+"\n").encode("utf-8"):
            raise ValueError("execution tooling manifest must be canonical JSON")
        tooling_manifest.validate_execution_tooling_manifest_identity(
            manifest=execution_tooling,
            expected_source_commit=data["source_commit"],
            schema_root=ROOT,
        )
    except (OSError,ValueError,tooling_manifest.ExecutionToolingManifestError) as exc:
        return [_err("execution_tooling_manifest_binding",str(exc))]
    if [row["case_id"] for row in data["case_inputs"]]!=data["case_ids"]:
        return [_err("campaign_authorization_cases","child case/input rows differ from the exact ordered case set")]
    try:
        parse=lambda value:datetime.strptime(value,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        parent_start,parent_end=parse(parent["valid_not_before"]),parse(parent["valid_not_after"])
        child_start,child_end=parse(data["launch_not_before"]),parse(data["launch_not_after"])
    except (TypeError,ValueError) as exc:
        return [_err("campaign_authorization_window",str(exc))]
    if not parent_start<=child_start<child_end<=parent_end:
        return [_err("campaign_authorization_window","child launch window is not contained in the active parent window")]
    return []


def _artifact_identity_errors(value: dict, identity: dict, *, cycle_field: str="cycle_id") -> bool:
    expected={**identity};expected[cycle_field]=expected.pop("matrix_id")
    return any(value.get(field)!=wanted for field,wanted in expected.items())


def _promotion_verdict_errors(value: dict, *, root: Path, expected_output_sha256: str) -> list[dict[str,str]]:
    if value.get("schema")!="daee-checker-replay-verdict-v1":return [_err("structural_promotion_binding","promotion reference is not an A11 checker-replay verdict")]
    try:registry=load_validation_registry(root=root)
    except (OSError,ValueError,json.JSONDecodeError) as exc:return [_err("structural_promotion_binding",f"validation registry unavailable/invalid: {exc}")]
    findings=validate_registry_verdict(value,registry,root=root,verify_files=True)
    if findings:return [_err("structural_promotion_binding",f"A11 replay verdict rejected: {findings[0].failure_class}/{findings[0].failure_subcode}: {findings[0].message}")]
    if value.get("selected_profile")!="promotion" or value.get("aggregate_status")!="PASS_STRUCTURAL":return [_err("structural_promotion_binding","A11 replay must be promotion-profile PASS_STRUCTURAL")]
    outputs=[row for row in value.get("artifacts",[]) if row.get("role")=="output"]
    if len(outputs)!=1 or outputs[0].get("sha256")!=expected_output_sha256:return [_err("structural_promotion_binding","A11 replay output artifact differs from structural case output")]
    return []


def _issuer_integration_boundary(field: str, value: dict) -> list[dict[str,str]]:
    """Fail closed until the named issuer's byte-level validator is integrated."""
    return [_err(f"structural_{field}_integration_boundary",f"{field} issuer/owner validator is not integrated; self-declared status or identity fields cannot authorize structural PASS")]


def _usage_chain_errors(cycle_root: Path, ledger_ref: object, receipt_ref: object, identity: dict) -> list[dict[str,str]]:
    if not isinstance(ledger_ref,dict) or set(ledger_ref)!={"path","tree_sha256"}:return [_err("structural_usage_binding","exact usage ledger path/tree hash is required")]
    try:
        ledger_root=_safe_path(cycle_root,ledger_ref["path"],directory=True)
        before_tree=_tree_digest(ledger_root)
        if before_tree!=ledger_ref["tree_sha256"]:raise ValueError("structural_artifact_hash: usage ledger tree hash drift")
        receipt_path,receipt_raw=_read_bytes_ref(cycle_root,receipt_ref)
        expected_parent=(ledger_root/"transactions").resolve(strict=True)
        if receipt_path.parent.resolve(strict=True)!=expected_parent:raise ValueError("structural_usage_binding: settlement receipt is not in the bound ledger transaction directory")
        receipt_sha=hashlib.sha256(receipt_raw).hexdigest()
        if receipt_path.name!=f"{receipt_sha}.json":raise ValueError("structural_usage_binding: settlement filename is not its content address")
        head=campaign_usage_ledger.validate_head(ledger_root)
        transaction=campaign_usage_ledger._load_transaction(ledger_root,receipt_sha)
        if _tree_digest(ledger_root)!=before_tree:raise ValueError("structural_toctou: usage ledger changed during replay")
    except (OSError,ValueError,json.JSONDecodeError) as exc:return [_err(str(exc).split(":",1)[0] if str(exc).startswith(("structural_","usage_")) else "structural_usage_binding",str(exc))]
    expected_calls=transaction.get("reserved_calls")
    accounted=sum(transaction.get(field,-1) for field in ("completed","failed","cancelled","not_dispatched","unknown"))
    provider_rows=transaction.get("provider_usage_receipts",[])
    if transaction.get("kind") not in {"settlement","orphan-recovery"} or transaction.get("candidate_id")!=identity["candidate_id"] or transaction.get("cycle_or_review_batch_id")!=identity["matrix_id"] or transaction.get("campaign_authorization_sha256")!=identity["campaign_authorization_sha256"] or transaction.get("authorization_sha256")!=identity["matrix_authorization_sha256"] or transaction.get("cohort")!="gpt-producer" or transaction.get("lane")!="producer" or expected_calls!=5 or accounted!=5 or transaction.get("completed")!=5 or transaction.get("attempted")!=5 or transaction.get("unknown")!=0 or any(row.get("status")!="COMPLETED" or row.get("accepted") is not True or row.get("in_flight") is not True for row in provider_rows):return [_err("structural_usage_binding","settlement transaction does not bind five accepted/in-flight completed producer calls and cycle/candidate/authorization identity")]
    if head.get("last_transaction_sha256")!=receipt_sha or head.get("open_reservations") or head.get("unresolved_usage") is not False:return [_err("structural_usage_binding","canonical usage head does not terminate at a fully settled producer receipt")]
    return []


def _structural_dispatch_errors(dispatch: dict, expected_cases: list[str]) -> list[dict[str,str]]:
    errors=validate_dispatch_manifest(dispatch,5)
    if errors:return [_err("structural_dispatch_binding",errors[0]["message"])]
    workers=dispatch.get("workers",[]);rows=dispatch.get("rows",[]);events=dispatch.get("events",[])
    bindings=[(row.get("worker"),row.get("case_id")) for row in workers]
    row_bindings=[(row.get("worker"),row.get("case_id")) for row in rows]
    if len(bindings)!=5 or [case for _,case in bindings]!=expected_cases or len(set(bindings))!=5:return [_err("structural_dispatch_binding","dispatch workers do not bind the exact ordered canonical five cases")]
    if row_bindings!=bindings or any(row.get("result")!="ok" or row.get("output_preserved") is not True for row in rows):return [_err("structural_dispatch_binding","dispatch terminal rows do not preserve five completed canonical outputs")]
    terminal_bindings=[(event.get("worker"),event.get("case_id")) for event in events if event.get("event")=="terminal_result_observed"]
    if sum(event.get("event")=="call_entered_in_flight" for event in events)!=5 or len(terminal_bindings)!=5:return [_err("structural_dispatch_binding","dispatch does not prove exactly five in-flight and terminal observations")]
    if set(terminal_bindings)!=set(bindings) or len(set(terminal_bindings))!=5:return [_err("structural_dispatch_binding","terminal observations do not bind every canonical worker/case exactly once")]
    return []


def _structural_finalizer_errors(finalizer: dict, data: dict, refs: dict[str,dict]) -> list[dict[str,str]]:
    errors=validate_manifest(finalizer,root=ROOT) if finalizer.get("kind")=="cycle-observation-finalizer" else [_err("schema_contract","not a finalizer")]
    if errors:return [_err("structural_finalizer_binding",errors[0]["message"])]
    exact={"cycle_id":data["matrix_id"],"cycle_claim_sha256":refs["cycle_claim"]["sha256"],"status":"FINALIZED","root_creation":"CREATED","dispatch_count":5,"usage_status":"SETTLED","candidate_status":"CONSUMED_OBSERVED","dispatch_manifest_sha256":refs["dispatch_manifest"]["sha256"],"usage_receipt_sha256":refs["usage_receipt"]["sha256"]}
    if any(finalizer.get(field)!=value for field,value in exact.items()):return [_err("structural_finalizer_binding","finalizer does not join exact cycle/dispatch/usage/consumption custody")]
    return []


def _prompt_manifest_errors(raw: bytes, case_id: str) -> list[dict[str,str]]:
    try:lines=[line for line in raw.decode("utf-8").splitlines() if line.strip()]
    except UnicodeDecodeError as exc:return [_err("structural_prompt_binding",f"prompt manifest is not UTF-8: {exc}")]
    if not lines:return [_err("structural_prompt_binding","prompt manifest is empty")]
    for line in lines:
        try:record=json.loads(line);validate_prompt_record(record,DEFAULT_CEILING)
        except (json.JSONDecodeError,BudgetViolation,KeyError,TypeError) as exc:return [_err("structural_prompt_binding",f"prompt manifest owner validation failed: {exc}")]
        if record.get("case_id")!=case_id:return [_err("structural_prompt_binding",f"prompt manifest case_id differs from canonical case {case_id}")]
    return []


def _validate_structural_verdict(data: dict, root: Path) -> list[dict[str,str]]:
    # 1 schema already ran. 2 canonical registry bytes/identity.
    try:
        registry_path,registry_raw=_read_bytes_ref(root,data["registry"]);registry=json.loads(registry_raw)
        input_before={row["case_id"]:hashlib.sha256(_safe_path(root,row["input_path"]).read_bytes()).hexdigest() for row in registry.get("cases",[])}
        registry_errors=validate_registry(registry,root)
        input_after={row["case_id"]:hashlib.sha256(_safe_path(root,row["input_path"]).read_bytes()).hexdigest() for row in registry.get("cases",[])}
        if registry_errors:raise ValueError(registry_errors[0]["message"])
        if input_before!=input_after:raise ValueError("structural_toctou: canonical registry inputs changed during validation")
    except (OSError,ValueError,json.JSONDecodeError,KeyError,TypeError) as exc:return [_err("structural_registry_binding",str(exc))]
    # 3 safe root/matrix binding; 4 hash-read every root artifact before trusting fields.
    try:
        evidence_custody_root=_external_custody_root(data["evidence_custody_root"],root)
        cycle_root=_safe_path(evidence_custody_root,data["cycle_root"],directory=True)
        try:cycle_root.relative_to(root.resolve(strict=True))
        except ValueError:pass
        else:raise ValueError("structural_path: resolved cycle root must be external to the mutable checkout")
        cycle_manifest,_=_read_ref(cycle_root,data["cycle_manifest"])
    except ValueError as exc:return [_err(str(exc).split(":",1)[0],str(exc))]
    identity=_identity(data)
    if cycle_manifest.get("schema")!="daee-structural-cycle-inventory-v1" or cycle_manifest.get("cycle_id")!=data["matrix_id"] or cycle_manifest.get("package_root")!=data["package_root"] or cycle_manifest.get("registry_sha256")!=hashlib.sha256(registry_raw).hexdigest() or cycle_manifest.get("evidence_custody_root")!=str(evidence_custody_root) or cycle_manifest.get("cycle_root")!=data["cycle_root"]:return [_err("structural_identity_mismatch","cycle inventory does not bind matrix/package/registry/custody identity")]
    if any(cycle_manifest.get(field)!=value for field,value in identity.items() if field!="matrix_id"):return [_err("structural_identity_mismatch","cycle inventory root identity differs from verdict")]
    root_fields=("matrix_authorization","ci_readback","candidate_maturity","dispatch_manifest","candidate_record","cycle_claim","candidate_consumption","usage_receipt","observation_finalizer","evidence_export","package_harness_parity")
    artifacts={};artifact_raws={}
    for field in root_fields:
        if cycle_manifest.get(field)!=data[field]:return [_err("structural_root_binding",f"{field} reference differs from cycle inventory")]
        try:artifacts[field],artifact_raws[field]=_read_ref(cycle_root,data[field])
        except ValueError as exc:return [_err(str(exc).split(":",1)[0],str(exc))]
    cycle_replay_digest=_tree_digest(cycle_root)
    # These issuer/A16 surfaces have no integrated byte-level owner validator in
    # this bounded A14 surface. Their scalar PASS/status fields are never oracles.
    integration_boundaries=[]
    for field in ("matrix_authorization","ci_readback","candidate_maturity","cycle_claim","candidate_consumption"):
        integration_boundaries.extend(_issuer_integration_boundary(field,artifacts[field]))
    expected_case_ids=[row["case_id"] for row in registry["cases"]]
    dispatch_errors=_structural_dispatch_errors(artifacts["dispatch_manifest"],expected_case_ids)
    if dispatch_errors:return dispatch_errors
    candidate=artifacts["candidate_record"]
    candidate_errors=validate_manifest(candidate,root=root) if candidate.get("kind")=="candidate-package-record" else [_err("schema_contract","not a candidate record")]
    if candidate_errors or candidate.get("candidate_id")!=data["candidate_id"] or candidate.get("status")!="CONSUMED_OBSERVED" or candidate.get("archive_sha256")!=data["package_sha256"] or candidate.get("extracted_tree_sha256")!=data["package_tree_sha256"] or not candidate.get("authorization_sha256") or not candidate.get("claim_receipt_sha256"):return [_err("structural_candidate_binding","candidate record failed its A14 contract or archive/extracted-tree/custody binding")]

    # 5 exact canonical cases/input hashes; every case row is inventory-bound.
    rows=data["cases"];expected=registry["cases"]
    if [row["case_id"] for row in rows]!=[row["case_id"] for row in expected]:return [_err("five_case_set","structural verdict must contain the exact ordered canonical five cases once")]
    if cycle_manifest.get("cases")!=rows:return [_err("structural_row_binding","case rows differ from cycle inventory")]
    auth=artifacts["matrix_authorization"];claim=artifacts["cycle_claim"];consumption=artifacts["candidate_consumption"]
    if data.get("matrix_authorization_sha256")!=data["matrix_authorization"]["sha256"] or cycle_manifest.get("matrix_authorization_sha256")!=data["matrix_authorization"]["sha256"]:return [_err("structural_authorization_binding","matrix authorization content address differs across verdict and cycle inventory")]
    if auth.get("candidate_package_record_sha256")!=data["candidate_record"]["sha256"] or auth.get("candidate_id")!=data["candidate_id"] or auth.get("package_sha256")!=data["package_sha256"] or auth.get("package_tree_sha256")!=data["package_tree_sha256"]:return [_err("structural_authorization_binding","matrix authorization does not reference the exact candidate/package record")]
    if claim.get("matrix_authorization_sha256")!=data["matrix_authorization"]["sha256"] or claim.get("candidate_record_sha256")!=data["candidate_record"]["sha256"] or claim.get("cycle_id")!=data["matrix_id"]:return [_err("structural_claim_binding","cycle claim does not reference the exact matrix authorization/candidate")]
    consumption_exact={"cycle_id":data["matrix_id"],"candidate_id":data["candidate_id"],"candidate_status":"CONSUMED_OBSERVED","cycle_claim_sha256":data["cycle_claim"]["sha256"],"candidate_record_sha256":data["candidate_record"]["sha256"],"usage_receipt_sha256":data["usage_receipt"]["sha256"],"dispatch_manifest_sha256":data["dispatch_manifest"]["sha256"],"observation_finalizer_sha256":data["observation_finalizer"]["sha256"]}
    if any(consumption.get(field)!=value for field,value in consumption_exact.items()):return [_err("structural_consumption_binding","candidate consumption does not join exact claim/candidate/dispatch/usage/finalizer custody")]
    if cycle_manifest.get("usage_ledger")!=data["usage_ledger"]:return [_err("structural_root_binding","usage_ledger reference differs from cycle inventory")]
    usage_errors=_usage_chain_errors(cycle_root,data["usage_ledger"],data["usage_receipt"],identity)
    if usage_errors:return usage_errors
    usage_tx=json.loads(artifact_raws["usage_receipt"])
    if [row.get("subject_id") for row in usage_tx.get("provider_usage_receipts",[])]!=expected_case_ids:return [_err("structural_usage_binding","producer call subjects do not equal the exact canonical five cases")]
    finalizer_errors=_structural_finalizer_errors(artifacts["observation_finalizer"],data,data)
    if finalizer_errors:return finalizer_errors
    package_root=None
    try:
        package_root=_safe_path(root,data["package_root"],directory=True);package_before=_tree_digest(package_root);run_before=_tree_digest(cycle_root)
        parity_result=validate_package_parity(artifacts["package_harness_parity"],package_root,cycle_root,root)
        if _tree_digest(package_root)!=package_before or _tree_digest(cycle_root)!=run_before:raise ValueError("structural_toctou: package or cycle evidence tree changed during parity replay")
    except (ValueError,ParityFailure) as exc:return [_err("structural_parity_binding",str(exc))]
    if parity_result.get("classification")!="package-faithful" or artifacts["package_harness_parity"].get("package_tree_sha256")!=data["package_tree_sha256"]:return [_err("structural_parity_binding","package parity is not package-faithful or differs from candidate extracted tree")]
    # A16 owns durable export authorization/publication. Record the boundary,
    # but do not let it mask locally replayable case evidence.
    integration_boundaries[:0]=_issuer_integration_boundary("evidence_export",artifacts["evidence_export"])
    for registry_row,row in zip(expected,rows):
        case_id=row["case_id"]
        if row["input_sha256"]!=registry_row["raw_sha256"].lower():return [_err("structural_row_binding",f"input hash mismatch for {case_id}")]
        try:
            handoff_path,handoff_raw=_read_bytes_ref(cycle_root,row["handoff_record"]);handoff=json.loads(handoff_raw)
            prompt_path,prompt_raw=_read_bytes_ref(cycle_root,row["prompt_manifest"])
            output_path,output_raw=_read_bytes_ref(cycle_root,row["output"])
            capture_path,capture_raw=_read_bytes_ref(cycle_root,row["capture_manifest"]);capture=json.loads(capture_raw)
            promotion_path,promotion_raw=_read_bytes_ref(cycle_root,row["promotion_verdict"]);promotion=json.loads(promotion_raw)
            capsule_dir=_safe_path(cycle_root,row["state_capsules"]["path"],directory=True)
        except (ValueError,OSError,json.JSONDecodeError) as exc:return [_err(str(exc).split(":",1)[0] if str(exc).startswith("structural_") else "structural_artifact_bytes",str(exc))]
        capsule_before=_tree_digest(capsule_dir)
        if capsule_before!=row["state_capsules"]["tree_sha256"]:return [_err("structural_artifact_hash",f"state capsule tree hash drift for {case_id}")]
        # 6 actual Stage01-08 owner replay, prompt-pack and capsule replay; no repair.
        handoff_failures=validate_handoff_record(handoff_path,handoff)
        external_output_failures=[failure for failure in handoff_failures if "stage-07 release_output.path" in failure and " missing" in failure]
        local_handoff_failures=[failure for failure in handoff_failures if failure not in external_output_failures]
        if local_handoff_failures:return [_err("structural_stage_binding",local_handoff_failures[0])]
        if external_output_failures:integration_boundaries.extend([_err("structural_staged_handoff_external_custody_integration_boundary","staged handoff owner validator resolves release output beneath the repo and cannot authorize the external custody join")])
        stages=handoff.get("stages",[])
        if handoff.get("case_id")!=case_id or [stage.get("id") for stage in stages]!=["stage-01-intake","stage-02-layer-a-diagnostic-ir","stage-03-routing-owner-gate","stage-04-burden-execution-act","stage-05-mrp-reread-terminal-state","stage-06-field-witness-nar","stage-07-release-output","stage-08-verifier-sidecars"] or any(stage.get("status")!="pass" for stage in stages):return [_err("structural_stage_binding",f"handoff is not exact eight-stage PASS for {case_id}")]
        if any(isinstance(node,dict) and node.get("semantic_repair_events") not in (None,[]) for node in [handoff,*stages]):return [_err("semantic_repair",f"semantic repair is present for {case_id}")]
        prompt_errors=_prompt_manifest_errors(prompt_raw,case_id)
        if prompt_errors:return prompt_errors
        capsule_errors=replay_errors_dispatch(capsule_dir,artifact_path=output_path,release_bearing=True)
        if capsule_errors:return [_err("structural_capsule_binding",capsule_errors[0])]
        if _tree_digest(capsule_dir)!=capsule_before:return [_err("structural_toctou",f"state capsule tree changed during replay for {case_id}")]
        # 7 actual A01 capture and A11 promotion replay, bound to exact output.
        # A01's current capture validator requires cold-review/topology artifacts,
        # and A11 currently resolves output paths only beneath the repo. Neither is
        # a valid external-custody Phase-5 oracle until those owner joins land.
        integration_boundaries.extend(_issuer_integration_boundary("a01_pre_review_capture",capture))
        integration_boundaries.extend(_issuer_integration_boundary("a11_external_promotion",promotion))
        stage07=next(stage for stage in stages if stage.get("id")=="stage-07-release-output")
        if str(stage07.get("release_output",{}).get("sha256","")).lower()!=hashlib.sha256(output_raw).hexdigest():return [_err("structural_promotion_binding",f"handoff Stage07 output hash differs for {case_id}")]

    # 9 exact PARTIAL layering and nonclaims.
    if data.get("completion_status")!="PARTIAL" or data.get("semantic_truth") is True:return [_err("structural_semantic_overclaim","structural PASS must remain completion PARTIAL and non-semantic")]
    required_nonclaims={"structural PASS is not semantic truth","structural pre-review PASS cannot authorize cold review or final completion by itself"}
    if not required_nonclaims.issubset(data.get("non_claims",[])):return [_err("structural_semantic_overclaim","structural verdict nonclaims are incomplete")]
    if _tree_digest(cycle_root)!=cycle_replay_digest:return [_err("structural_toctou","cycle evidence tree changed during complete five-case replay")]
    if integration_boundaries:return integration_boundaries
    return []


def _schema_errors(data: object) -> list[dict[str,str]]:
    paired=isinstance(data,dict) and (data.get("schema")=="daee-cross-model-paired-cycle-v1" or data.get("kind")=="paired-cycle-manifest" or "gpt_candidate" in data)
    path=PAIRED_SCHEMA_PATH if paired else SMOKE_SCHEMA_PATH
    root_schema=json.loads(path.read_text(encoding="utf-8"))
    selected=root_schema
    if not paired and isinstance(data,dict) and data.get("kind") in KIND_DEFS:
        selected={"$ref":f"#/$defs/{KIND_DEFS[data['kind']]}","$defs":root_schema["$defs"]}
    try:issues=validate_schema_subset(data,selected)
    except SchemaDefinitionError as exc:return [_err("schema_definition",str(exc))]
    return [_err("schema_contract",f"{issue.path} {issue.keyword}: {issue.message}") for issue in issues]


def validate_manifest(data: object, *, root: Path = ROOT) -> list[dict[str,str]]:
    schema_errors=_schema_errors(data)
    if schema_errors:return schema_errors
    if not isinstance(data,dict): return [_err("manifest_shape","manifest must be an object")]
    if data.get("schema")=="daee-cross-model-paired-cycle-v1": return validate_paired_manifest(data)
    if data.get("schema")!="daee-smoke-matrix-v1": return [_err("manifest_schema","unknown smoke-matrix schema")]
    kind=data.get("kind")
    if kind=="input-registry": return validate_registry(data,root)
    if kind=="review-protocol":
        registry_path=root/data["input_registry"]["path"]
        if registry_path.resolve()!= (root/"tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json").resolve():
            return [_err("review_protocol_registry","review protocol must bind the canonical five-case registry path")]
        try: raw=registry_path.read_bytes();registry=load_registry(registry_path,root)
        except (OSError,ValueError,json.JSONDecodeError) as exc:return [_err("review_protocol_registry",str(exc))]
        if hashlib.sha256(raw).hexdigest()!=data["input_registry"]["sha256"]:
            return [_err("review_protocol_registry","review protocol registry raw hash drift")]
        if data["case_ids"]!=[row["case_id"] for row in registry["cases"]]:
            return [_err("review_protocol_cases","review protocol must bind the exact ordered canonical five cases")]
        return []
    if kind in {"candidate-build-authorization","matrix-authorization"}:
        expected=hashlib.sha256((json.dumps({key:value for key,value in data.items() if key!="authorization_sha256"},sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
        if data["authorization_sha256"]!=expected:return [_err("authorization_content_hash","authorization content hash mismatch")]
        if data.get("ref") is not None and data.get("ref")!=f"refs/heads/{data.get('branch')}":return [_err("authorization_branch_ref","authorization branch/ref mismatch")]
        if kind=="candidate-build-authorization":
            custody=Path(data["custody_root"]);candidate=Path(data["candidate_root"]);claim=Path(data["claim_path"])
            try:candidate.relative_to(custody);claim.relative_to(custody/"claims")
            except ValueError:return [_err("candidate_custody_path","candidate root must be beneath its authorized custody root")]
            if claim.name!=f"{data['authorization_id']}.claim.json":return [_err("candidate_claim_path","candidate claim path must be derived from the authorization ID")]
        if kind=="matrix-authorization":
            return _live_matrix_authority_errors(data,root)
        return []
    if kind in {"candidate-build-claim","matrix-authorization-claim"}:
        expected=hashlib.sha256((json.dumps({key:value for key,value in data.items() if key!="claim_sha256"},sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
        if data["claim_sha256"]!=expected:return [_err("authorization_claim_hash","authorization claim content hash mismatch")]
        return []
    if kind=="candidate-package-record-bound":
        expected=hashlib.sha256((json.dumps({key:value for key,value in data.items() if key!="record_sha256"},sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
        if data["record_sha256"]!=expected:return [_err("candidate_record_hash","bound candidate record content hash mismatch")]
        if data["status"]=="READY_UNUSED" and data["claim_status"]!="UNCLAIMED":return [_err("candidate_claim_state","READY_UNUSED candidate must be unclaimed")]
        if data["tree_digest_algorithm"]!=TREE_DIGEST_ALGORITHM:return [_err("candidate_tree_algorithm","candidate uses an unsupported tree digest algorithm")]
        return []
    if kind=="candidate-readiness-marker":
        expected=hashlib.sha256((json.dumps({key:value for key,value in data.items() if key!="marker_sha256"},sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
        if data["marker_sha256"]!=expected:return [_err("candidate_readiness_hash","candidate readiness marker content hash mismatch")]
        return []
    if kind=="candidate-transition":
        try: expected=derive_transition({"status":data.get("from_status")},claimed=data.get("claimed") is True,dispatch_count=data.get("dispatch_count"))
        except ValueError as exc:
            cls=str(exc).split(":",1)[0]; return [_err(cls,str(exc))]
        if data.get("to_status")!=expected:return [_err("candidate_transition",f"claim/dispatch evidence requires {expected}")]
        if expected=="CONSUMED_DISPATCH_UNKNOWN" and data.get("unresolved_usage") is not True:return [_err("unresolved_usage","unknown dispatch requires unresolved usage")]
        return []
    if kind=="campaign-usage-reservation":
        if data.get("unresolved_usage") is True:return [_err("unresolved_usage","unresolved usage blocks a new paid-call reservation")]
        cohort=data.get("cohort"); required=10 if cohort in {"paired-producer","paired-review"} else 5 if cohort in {"gpt-producer","gpt-review"} else None
        if required is None:return [_err("reservation_cohort","unknown reservation cohort")]
        if data.get("reserved_calls")!=required:return [_err("reservation_count",f"{cohort} must reserve exactly {required} calls")]
        return []
    if kind=="campaign-control":
        prohibited=[name for name in ("maximum_cycles","maximum_invocations","cumulative_call_ceiling") if name in data]
        if prohibited:return [_err("fixed_campaign_ceiling",f"fixed campaign ceiling is prohibited: {prohibited[0]}")]
        if data.get("unresolved_usage") is True:return [_err("unresolved_usage","unresolved usage blocks more paid calls")]
        if data.get("root_cause_recurrence") is True and data.get("circuit_breaker")!="OPEN":return [_err("root_cause_circuit_breaker","same-root recurrence requires an open circuit breaker")]
        if "calls_avoided" in data and not data.get("calls_avoided_evidence_sha256"):
            return [_err("speculative_calls_avoided","calls avoided requires hash-bound deterministic gate evidence")]
        return []
    if kind=="campaign-usage-receipt":
        reserved=data.get("reserved_invocations")
        parts=[data.get(name) for name in ("completed","failed_after_dispatch","cancelled_after_dispatch","not_dispatched","unknown")]
        if not isinstance(reserved,int) or any(not isinstance(value,int) or value<0 for value in parts) or sum(parts)!=reserved:
            return [_err("usage_arithmetic","reserved invocation arithmetic must equal completed, failed, cancelled, not dispatched, and unknown")]
        if data.get("reservation_status")!="SETTLED":
            return [_err("usage_reservation_unsettled","failed cycle reservation must be settled before finalization")]
        if data.get("resulting_usage_sequence") != data.get("predecessor_usage_sequence",-1)+2:
            return [_err("usage_head_nonmonotonic","reservation and settlement must advance the canonical head by two")]
        if data.get("lane")=="cold-review" and (data.get("producer_invocations_delta",0)!=0 or data.get("cold_review_invocations_delta",5)!=5):
            return [_err("usage_lane_misattribution","cold review usage cannot be counted as producer usage")]
        if data.get("provider_metadata_status") not in {"RECORDED","UNAVAILABLE"}:
            return [_err("usage_provider_metadata","provider usage and cost metadata must be recorded or explicitly unavailable")]
        return []
    if kind=="campaign-usage-recovery":
        if data.get("reservation_reused") is True:
            return [_err("reservation_reuse","orphan recovery cannot reuse or erase the reservation")]
        if data.get("claimed_candidate_status") not in {"CONSUMED_NO_DISPATCH","CONSUMED_OBSERVED","CONSUMED_DISPATCH_UNKNOWN"}:
            return [_err("candidate_transition","orphan recovery must preserve a terminal consumed candidate")]
        return []
    if kind=="candidate-package-record":
        if data.get("status")=="QUARANTINED" and data.get("root_creation")=="FAILED" and not data.get("fallback_quarantine_path"):
            return [_err("candidate_fallback_missing","candidate root failure requires a claim-bound fallback quarantine record")]
        if data.get("status")=="READY_UNUSED" and not data.get("authorization_sha256"):
            return [_err("candidate_authorization_missing","ready candidate requires hash-bound authorization")]
        if data.get("status")=="READY_UNUSED" and not data.get("extracted_tree_sha256"):
            return [_err("candidate_tree_hash_missing","ready candidate requires extracted tree hash")]
        if data.get("status") in {"CONSUMED_NO_DISPATCH","CONSUMED_OBSERVED","CONSUMED_DISPATCH_UNKNOWN"}:
            if any(not data.get(field) for field in ("authorization_sha256","claim_receipt_sha256","predecessor_record_sha256","record_sha256")):
                return [_err("candidate_transition_binding","terminal candidate record requires predecessor, candidate, authorization, and claim bindings")]
            unsigned={key:value for key,value in data.items() if key!="record_sha256"}
            digest=hashlib.sha256((json.dumps(unsigned,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
            if data["record_sha256"]!=digest:return [_err("candidate_record_hash","terminal candidate record content hash mismatch")]
        return []
    if kind=="authorization-check":
        if data.get("authorization_replayed") is True or data.get("claim_receipt_reused") is True:
            return [_err("authorization_replay","authorization or claim replay is forbidden")]
        drift=[field for field in ("branch_match","model_settings_match","provider_contract_match","package_hash_match") if data.get(field) is False]
        if drift:return [_err("authorization_drift",f"authorization drift detected at {drift[0]}")]
        return []
    if kind=="usage-head-audit":
        if data.get("canonical_rewritten") is True:return [_err("usage_head_rewritten","canonical usage head factual count rewrite is forbidden")]
        if data.get("forked") is True:return [_err("usage_head_fork","worker fork of canonical usage head is forbidden")]
        if data.get("conflicting_predecessor") is True:return [_err("usage_head_conflict","predecessor usage head conflict must spend zero calls")]
        if data.get("producer_review_conflict") is True:return [_err("usage_head_conflict","producer review reservation conflict must spend zero calls")]
        return []
    if kind=="taint-audit":
        if data.get("case_identity_reaches_routing") is True:return [_err("case_registry_taint","case identity or hash cannot reach runtime routing")]
        return []
    if kind=="review-gate":
        if data.get("patch_owner_overturn") is True and data.get("second_independent_review") is not True:return [_err("second_review_required","patch-owner material reversal requires second independent review")]
        if data.get("reviewer_andon") is True and data.get("reviewer_andon_reentered") is not True:return [_err("reviewer_andon_bypass","reviewer ANDON must pause and re-enter the repair loop")]
        return []
    if kind=="structural-cycle":
        registry=load_registry(); expected=[row["case_id"] for row in registry["cases"]]
        if data.get("case_ids")!=expected:return [_err("five_case_set","structural cycle must contain the exact ordered five registry cases")]
        counts=data.get("stage_counts")
        if not isinstance(counts,list) or len(counts)!=5 or any(count!=8 for count in counts):return [_err("stage_sequence","every case requires exactly eight ordered stage records")]
        if data.get("semantic_repair_events"):
            return [_err("semantic_repair","semantic repair events invalidate structural replay")]
        if data.get("source_maturity_used_as_candidate") is True:return [_err("candidate_maturity_substitution","source preflight cannot substitute for candidate maturity")]
        if data.get("candidate_custody_claim") in {"PASS","FAIL"}:return [_err("candidate_custody_overclaim",f"candidate custody cannot claim {data['candidate_custody_claim']} before review")]
        if data.get("pass_carry_forward") is True:return [_err("pass_carry_forward","selective prior-cycle pass carry forward is forbidden")]
        reviews=data.get("topology_review_statuses")
        if reviews is not None and any(status!="PASS" for status in reviews):return [_err("review_incomplete",f"review status {next(status for status in reviews if status!='PASS')} blocks completion")]
        return []
    if kind=="cycle-completion-attempt":
        if data.get("claimed") is True and data.get("failed") is True and not data.get("observation_finalizer_sha256"):
            return [_err("observation_finalizer_missing","failed claimed cycle requires an observation finalizer")]
        return []
    if kind=="producer-outcome":
        outcome=data.get("outcome")
        if outcome=="NOT_RUN_POLICY_INCOMPATIBILITY" and not (data.get("control_layer_proof") is True and data.get("model_authored") is False and data.get("stage01_entered") is False):return [_err("refusal_origin_evidence","policy incompatibility requires typed control-layer proof before model-authored Stage01 output")]
        if outcome=="PRODUCT_REFUSAL" and not (data.get("model_authored") is True and data.get("stage01_entered") is True):return [_err("refusal_origin_evidence","product refusal requires model-authored Stage01 evidence")]
        if outcome=="REFUSAL_ORIGIN_UNPROVEN" and (data.get("control_layer_proof") is True or data.get("model_authored") is not None):return [_err("refusal_origin_evidence","unproven refusal origin cannot assert control-layer or model authorship")]
        if outcome not in {"NOT_RUN_POLICY_INCOMPATIBILITY","PRODUCT_REFUSAL","REFUSAL_ORIGIN_UNPROVEN"}:return [_err("refusal_outcome","unknown refusal outcome")]
        if data.get("candidate_status")=="CONSUMED_NO_DISPATCH" and data.get("dispatch_evidence")!="PROVED_ZERO":
            return [_err("candidate_consumption_evidence","zero dispatch candidate consumption requires proved dispatch evidence independent of refusal label")]
        return []
    if kind=="dispatch-manifest": return validate_dispatch_manifest(data,5)
    if kind=="cycle-observation-finalizer":
        if "completion_status" in data or "structural_matrix_status" in data:
            return [_err("observation_verdict_overclaim","observation finalizer cannot emit a reviewed cycle verdict")]
        if data.get("root_creation")=="FAILED" and not data.get("fallback_path"):
            return [_err("observation_finalizer_missing","root creation failure requires a claim-bound fallback finalizer")]
        if data.get("usage_status")!="SETTLED":
            return [_err("usage_reservation_unsettled","observation finalizer cannot leave a reservation unsettled")]
        if data.get("candidate_status") not in {"CONSUMED_NO_DISPATCH","CONSUMED_OBSERVED","CONSUMED_DISPATCH_UNKNOWN"}:
            return [_err("candidate_transition","finalizer must bind a neutral consumed candidate state")]
        return []
    if kind=="evidence-export":
        if data.get("resume_mode")=="HASH_EQUAL_ONLY" and data.get("resume_hash_equal") is False:
            return [_err("evidence_staging_conflict","staging resume hash mismatch forbids overwrite or final publication")]
        if data.get("completion_evidence") is True and data.get("phase")!="FINAL_PUBLISHED":
            return [_err("staging_not_final","staging manifest is not final completion evidence")]
        if data.get("phase")=="FINAL_PUBLISHED" and not (data.get("staging_verified") is True and data.get("final_readback") is True and data.get("final_path_unused_before_publish") is True):
            return [_err("evidence_publish_unverified","final publication requires verified staging, exclusive unused destination, and readback")]
        return []
    if kind=="cycle-observation":
        if "completion_status" in data or "structural_matrix_status" in data:return [_err("observation_verdict_overclaim","cycle observation cannot emit a structural or reviewed verdict")]
        if data.get("candidate_status") not in {"CONSUMED_NO_DISPATCH","CONSUMED_OBSERVED","CONSUMED_DISPATCH_UNKNOWN"}:return [_err("candidate_transition","observation must bind one neutral consumed state")]
        return []
    if kind=="structural-pre-review-verdict":
        return _validate_structural_verdict(data,root)
    if kind=="cycle-verdict":
        return [_err("review_contract_unavailable","final cycle verdict is blocked until the A01 human/cold review join and custody checker are implemented")]
    return [_err("manifest_kind",f"unsupported manifest kind {kind!r}")]


def _expectation_shape_errors(data: object) -> list[str]:
    """Validate the frozen Plan 11 expectation dialect without dependencies."""
    schema=json.loads(EXPECTATION_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(data,dict): return ["expectation must be an object"]
    required=set(schema["required"]); allowed=set(schema["properties"]); errors=[]
    if missing:=sorted(required-set(data)): errors.append(f"missing fields: {missing}")
    if extra:=sorted(set(data)-allowed): errors.append(f"extra fields: {extra}")
    props=schema["properties"]
    if data.get("schema")!=props["schema"]["const"]: errors.append("schema discriminator mismatch")
    if data.get("kind") not in props["kind"]["enum"]: errors.append("kind mismatch")
    for field in ("expected_checker_id","expected_exit_category","expected_failure_class"):
        value=data.get(field); pattern=props[field]["pattern"]
        if not isinstance(value,str) or re.fullmatch(pattern,value) is None: errors.append(f"{field} pattern mismatch")
    subcode=data.get("expected_failure_subcode")
    if subcode is not None and (not isinstance(subcode,str) or re.fullmatch(props["expected_failure_subcode"]["pattern"],subcode) is None): errors.append("expected_failure_subcode pattern mismatch")
    code=data.get("expected_exit_code")
    if not isinstance(code,int) or not 1<=code<=255: errors.append("expected_exit_code range mismatch")
    if data.get("expected_earliest_stage") not in props["expected_earliest_stage"]["enum"]: errors.append("expected_earliest_stage mismatch")
    for field in ("expected_downstream_invalidated","required_diagnostic_markers","forbidden_artifacts"):
        value=data.get(field)
        if not isinstance(value,list) or len(value)!=len(set(value)) or any(not isinstance(item,str) or not item for item in value): errors.append(f"{field} array mismatch")
    if not data.get("required_diagnostic_markers"): errors.append("required_diagnostic_markers must be nonempty")
    if not isinstance(data.get("fixture"),str) or not data.get("fixture"): errors.append("fixture missing")
    if not isinstance(data.get("provenance"),str) or not data.get("provenance"): errors.append("provenance missing")
    return errors


def _checker_id_for(data: dict) -> str:
    if data.get("schema")=="daee-cross-model-paired-cycle-v1": return "paired-cross-model-manifest"
    if data.get("kind")=="dispatch-manifest": return "parallel-dispatch-manifest"
    return "smoke-matrix-manifest"


def _diagnostic_record(data: dict, error: dict[str,str]) -> dict:
    cls=error["failure_class"]
    candidate_classes={"terminal_candidate_reuse","sibling_package_mismatch","sibling_provenance_mismatch","candidate_fallback_missing","authorization_replay","candidate_authorization_missing","candidate_tree_hash_missing"}
    if cls in candidate_classes: stage="candidate-package"
    elif cls=="candidate_maturity_substitution": stage="preflight"
    elif cls=="semantic_repair": stage="05"
    elif cls=="stage_sequence": stage="07" if data.get("stage_counts")==[1,1,1,1,1] else "08"
    elif data.get("outcome")=="PRODUCT_REFUSAL" or cls=="candidate_consumption_evidence": stage="01"
    else: stage="control-plane"
    downstream={
        "early_result_observation": ["paired-cycle-verdict"] if data.get("schema")=="daee-cross-model-paired-cycle-v1" else ["cycle-observation-finalizer"],
        "fixed_campaign_ceiling": ["matrix-authorization"], "unresolved_usage": ["paid-dispatch"],
        "terminal_candidate_reuse": ["cycle-verdict"], "gpt_root_recurrence": ["paired-paid-dispatch"],
        "opus_root_recurrence": ["paired-paid-dispatch"], "sibling_package_mismatch": ["paired-cycle-verdict"],
        "pass_carry_forward": ["paired-cycle-verdict"], "sequential_masquerade": ["paired-cycle-verdict"] if data.get("schema")=="daee-cross-model-paired-cycle-v1" else ["cycle-observation-finalizer"],
        "refusal_origin_evidence": ["cycle-verdict"] if data.get("outcome")=="PRODUCT_REFUSAL" else ["structural-pre-review-verdict"],
        "reservation_count": ["paired-paid-dispatch"] if data.get("cohort") in {"paired-producer","paired-review"} else ["paid-dispatch"],
        "root_cause_circuit_breaker": ["campaign-usage-reservation"], "structural_semantic_overclaim": ["cycle-verdict"],
        "candidate_fallback_missing": ["candidate-package-record.json"],
        "observation_finalizer_missing": ["cycle-verdict.json"],
        "usage_reservation_unsettled": ["cycle-verdict.json"],
        "observation_verdict_overclaim": ["cycle-verdict.json"],
        "shared_worker_state": ["dispatch-manifest.accepted.json"],
        "evidence_staging_conflict": ["final-retention-manifest.json"],
        "candidate_consumption_evidence": ["candidate-consumption-receipt.json"],
        "dispatch_after_provider_stop": ["all-five-in-flight.json"],
        "usage_lane_misattribution": ["campaign-usage-head.json"],
        "speculative_calls_avoided": ["campaign-summary.json"],
        "staging_not_final": ["cycle-verdict.json"],
        "usage_arithmetic": ["campaign-usage-head.json"],
        "authorization_drift": ["dispatch-manifest.json"],
        "authorization_replay": ["candidate-package-record.json"],
        "usage_head_rewritten": ["campaign-usage-head.json"],
        "usage_head_fork": ["paid-dispatch"], "usage_head_conflict": ["paid-dispatch"],
        "candidate_custody_overclaim": ["cycle-verdict.json"],
        "candidate_authorization_missing": ["candidate-package-record.json"],
        "candidate_tree_hash_missing": ["matrix-authorization.json"],
        "case_registry_taint": ["matrix-authorization.json"],
        "second_review_required": ["cycle-verdict.json"],
        "reviewer_andon_bypass": ["successor-cycle.json"],
        "pass_carry_forward": ["cycle-verdict.json"] if data.get("schema")=="daee-smoke-matrix-v1" else ["paired-cycle-verdict"],
        "semantic_repair": ["structural-pre-review-verdict.json"],
        "candidate_maturity_substitution": ["matrix-authorization.json"],
        "stage_sequence": ["structural-pre-review-verdict.json"],
        "review_incomplete": ["cycle-verdict.json"],
        "usage_head_nonmonotonic": ["campaign-usage-head.json"],
        "registry_duplicate_id": ["matrix-authorization.json"],
        "registry_input_hash": ["matrix-authorization.json"],
        "registry_case_count": ["matrix-authorization.json"],
        "registry_identity": ["matrix-authorization.json"],
        "schema_contract": ["paired-cycle-verdict"] if data.get("schema")=="daee-cross-model-paired-cycle-v1" else ["matrix-authorization.json"] if data.get("kind")=="input-registry" else [],
        "sibling_provenance_mismatch": ["paired-cycle-verdict"],
        "paired_cohort_overlap": ["paired-cycle-verdict"], "paired_worker_binding": ["paired-cycle-verdict"],
        "missing_submit_event": ["cycle-observation-finalizer"], "missing_aggregate_barrier": ["cycle-observation-finalizer"],
        "dispatch_event_hash": ["cycle-observation-finalizer"], "dispatch_event_sequence": ["cycle-observation-finalizer"],
        "dispatch_worker_binding": ["cycle-observation-finalizer"],
    }.get(cls,[])
    return {**error,"failure_subcode":cls,"checker_id":_checker_id_for(data),"exit_category":"validation-failure","exit_code":1,"earliest_stage":stage,"downstream_invalidated":downstream}


def _check_expectation(path: Path, data: dict, errors: list[dict[str,str]]) -> bool:
    expectation=json.loads(path.with_suffix(".expectation.json").read_text(encoding="utf-8"))
    if _expectation_shape_errors(expectation) or expectation.get("fixture")!=path.name or not errors:return False
    diagnostic=_diagnostic_record(data,errors[0])
    if expectation["expected_checker_id"]!=diagnostic["checker_id"] or expectation["expected_exit_category"]!=diagnostic["exit_category"] or expectation["expected_exit_code"]!=diagnostic["exit_code"]:return False
    if expectation["expected_earliest_stage"]!=diagnostic["earliest_stage"] or expectation["expected_downstream_invalidated"]!=diagnostic["downstream_invalidated"]:return False
    if diagnostic["failure_class"]!=expectation["expected_failure_class"] or diagnostic["failure_subcode"]!=expectation["expected_failure_subcode"]:return False
    if any((path.parent/artifact).exists() for artifact in expectation["forbidden_artifacts"]):return False
    message=diagnostic["message"].lower()
    return all(marker.lower() in message for marker in expectation["required_diagnostic_markers"])


def self_test() -> int:
    checks=[]
    for schema in (ROOT/"schema"/"smoke-matrix.schema.json",ROOT/"schema"/"cross-model-paired-cycle.schema.json"):
        try: json.loads(schema.read_text(encoding="utf-8")); checks.append((f"schema parses {schema.name}",True))
        except Exception: checks.append((f"schema parses {schema.name}",False))
    for path in sorted((FIXTURES/"valid").glob("*.json")):
        checks.append((f"valid {path.name}",not validate_manifest(json.loads(path.read_text(encoding="utf-8")),root=ROOT)))
    for path in sorted((FIXTURES/"invalid").glob("*.json")):
        if path.name.endswith(".expectation.json"):continue
        data=json.loads(path.read_text(encoding="utf-8"));errors=validate_manifest(data,root=ROOT); checks.append((f"invalid right-reason {path.name}",_check_expectation(path,data,errors)))
    for name,ok in checks: print(f"  self-test {'PASS' if ok else 'FAIL'}: {name}")
    ok=all(v for _,v in checks); print(f"smoke-matrix-manifest self-test: {'PASS' if ok else 'FAIL'} ({sum(v for _,v in checks)}/{len(checks)})"); return 0 if ok else 1


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument("--manifest",type=Path);p.add_argument("--inputs-only",action="store_true");p.add_argument("--kind");p.add_argument("--self-test",action="store_true");a=p.parse_args()
    if a.self_test:return self_test()
    if not a.manifest:p.error("--manifest required unless --self-test")
    try:data=json.loads(a.manifest.read_text(encoding="utf-8"));errors=validate_manifest(data,root=ROOT)
    except (OSError,json.JSONDecodeError) as exc:errors=[_err("manifest_io",str(exc))];data={}
    if a.inputs_only and data.get("kind")!="input-registry":errors=[_err("manifest_kind","--inputs-only requires input-registry")]
    if a.kind and data.get("kind")!=a.kind:errors=[_err("manifest_kind",f"expected kind {a.kind}")]
    diagnostics=[_diagnostic_record(data,error) for error in errors] if isinstance(data,dict) else errors
    print(json.dumps({"status":"FAIL" if errors else "PASS","diagnostics":diagnostics},sort_keys=True));return 1 if errors else 0


if __name__=="__main__":sys.exit(main())
