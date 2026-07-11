#!/usr/bin/env python3
"""Pure Plan06 topology-derived obligation accounting; counts remain telemetry."""
from __future__ import annotations

import re
import argparse
import hashlib
import json
from collections import defaultdict
from typing import Any

KINDS = {"source_pressure","candidate_state","burden_route","owner_operation","land_delta","mrp_reread","residual_pressure","generated_burden","field_projection","public_projection","restorative_consequence","closure_boundary"}
DISPOSITIONS = {"satisfied","discharged_duplicate","non_load_bearing","preempted_not_instantiated","held","carried_partial","carried_recurse"}
OPEN_DISPOSITIONS = {"held","carried_partial","carried_recurse"}
EVIDENCE_TYPES = {"operation_capsule","body","partition_decision","route","land","reread","projection","public_section","closure","basis"}
EVIDENCE_TYPES_BY_KIND = {
    "source_pressure": {"partition_decision", "route", "basis"},
    "candidate_state": {"partition_decision", "basis"},
    "burden_route": {"route", "partition_decision"},
    "owner_operation": {"operation_capsule", "body"},
    "land_delta": {"operation_capsule", "land"},
    "mrp_reread": {"reread"},
    "residual_pressure": {"land", "reread", "partition_decision", "basis"},
    "generated_burden": {"route", "operation_capsule", "reread"},
    "field_projection": {"projection"},
    "public_projection": {"public_section"},
    "restorative_consequence": {"projection", "public_section"},
    "closure_boundary": {"closure"},
}
DECISION_TYPES = {"split","merge","shared_operation"}
NON_CLAIMS = ["counts and bytes do not determine PASS","structural accounting is not semantic truth","one run is not broad model behavior"]
FORBIDDEN_POLICY_KEYS = {"coverage_complete","size_waiver","count_waiver","adjudicator_byte_waiver","minimum_bytes","minimum_burdens","minimum_submoves"}


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _finding(failure_class: str, subcode: str, message: str, *markers: str) -> dict[str, Any]:
    return {"failure_class":failure_class,"failure_subcode":subcode,"message":message,"markers":list(markers)}


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _evidence_id_set(evidence_inventory: list[dict[str, Any]]) -> set[str]:
    return {item["evidence_id"] for item in evidence_inventory if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)}


def derive_accounting(obligations: list[dict[str, Any]], evidence_inventory: list[dict[str, Any]], partition_decisions: list[dict[str, Any]]) -> dict[str, Any]:
    ids = {item["obligation_id"] for item in obligations if isinstance(item, dict) and isinstance(item.get("obligation_id"), str)}
    evidence_ids = _evidence_id_set(evidence_inventory)
    decisions = {item["decision_id"]: item for item in partition_decisions if isinstance(item, dict) and isinstance(item.get("decision_id"), str)}
    unaccounted: set[str] = set(); unreconstructible: set[str] = set(); open_ids: set[str] = set(); users: dict[str,list[str]] = defaultdict(list)
    for obligation in obligations:
        if not isinstance(obligation, dict) or not isinstance(obligation.get("obligation_id"), str):
            continue
        oid=obligation["obligation_id"]; disposition=obligation.get("disposition"); allowed=obligation.get("allowed_dispositions")
        if disposition not in DISPOSITIONS or not isinstance(allowed,list) or disposition not in allowed:
            unaccounted.add(oid); continue
        refs=obligation.get("evidence_refs") if isinstance(obligation.get("evidence_refs"),list) else []
        for ref in refs:
            if isinstance(ref,str): users[ref].append(oid)
            if ref not in evidence_ids: unreconstructible.add(oid)
        if disposition=="satisfied" and not refs: unreconstructible.add(oid)
        if disposition=="discharged_duplicate":
            receiver=obligation.get("receiving_obligation_id"); decision=decisions.get(obligation.get("decision_id"))
            if receiver not in ids or receiver==oid or not isinstance(decision,dict) or decision.get("decision_type") not in DECISION_TYPES or oid not in decision.get("source_obligation_ids",[]) or decision.get("receiving_obligation_id")!=receiver:
                unreconstructible.add(oid)
        if disposition=="preempted_not_instantiated" and (obligation.get("kind")!="candidate_state" or any(re.fullmatch(r"B[1-9][0-9]*",str(source_id)) or str(source_id).startswith(("B_LA", "B_MRP")) for source_id in obligation.get("source_ids",[]))):
            unreconstructible.add(oid)
        if disposition in OPEN_DISPOSITIONS: open_ids.add(oid)
    orphan=sorted(evidence_ids-set(users))
    duplicate_groups=[]
    for ref, obligation_ids in users.items():
        if len(obligation_ids)>1:
            proved=any(item.get("decision_type") in {"merge","shared_operation"} and set(obligation_ids)<=set(item.get("source_obligation_ids",[])+[item.get("receiving_obligation_id")]) for item in partition_decisions if isinstance(item,dict))
            if not proved: duplicate_groups.append(sorted([ref,*obligation_ids]))
    initial={item["obligation_id"] for item in obligations if isinstance(item,dict) and item.get("origin_stage") in {"01","02"} and isinstance(item.get("obligation_id"),str)}
    initial_complete=not bool(initial&(unaccounted|unreconstructible)); lifecycle_complete=not unaccounted and not unreconstructible and not orphan and not duplicate_groups
    return {"unaccounted_obligation_ids":sorted(unaccounted),"unreconstructible_obligation_ids":sorted(unreconstructible),"open_obligation_ids":sorted(open_ids),"orphan_evidence_refs":orphan,"duplicate_evidence_groups":sorted(duplicate_groups),"initial_coverage_complete":initial_complete,"lifecycle_accounting_complete":lifecycle_complete,"collapse_positive":lifecycle_complete and not open_ids}


def build_accounting_record(*,case_id:str,input_sha256:str,staged_handoff_sha256:str,output_sha256:str,obligations:list[dict[str,Any]],evidence_inventory:list[dict[str,Any]],partition_decisions:list[dict[str,Any]]|None=None,advisory_metrics:dict[str,int]|None=None,authoritative_empty_universe:dict[str,Any]|None=None)->dict[str,Any]:
    decisions=partition_decisions or []; derived=derive_accounting(obligations,evidence_inventory,decisions); metrics={"output_bytes":0,"burden_count":0,"operation_capsule_count":0,"mrp_event_count":0,"generated_burden_count":0,"held_or_partial_count":0}; metrics.update(advisory_metrics or {})
    record={"schema":"daee-topology-mass-accounting-v1","case_id":case_id,"input_sha256":input_sha256,"staged_handoff_sha256":staged_handoff_sha256,"output_sha256":output_sha256,"obligations":obligations,"evidence_inventory":evidence_inventory,"partition_decisions":decisions,**derived,"advisory_metrics":metrics,"non_claims":NON_CLAIMS.copy()}
    if authoritative_empty_universe is not None: record["authoritative_empty_universe"]=authoritative_empty_universe
    return record


def validate_accounting(record:Any,*,upstream_obligation_ids:list[str]|None=None,upstream_inventory_sha256:str|None=None,evidence_authority:dict[str,Any]|None=None,evidence_authority_sha256:str|None=None)->list[dict[str,Any]]:
    if not isinstance(record,dict): return [_finding("topology_mass_schema","record-shape","record must be an object")]
    forbidden=sorted(set(_walk_keys(record))&FORBIDDEN_POLICY_KEYS)
    if forbidden:return [_finding("topology_mass_policy","forbidden-quota-or-closure-field",f"forbidden policy field {forbidden[0]}",forbidden[0])]
    if record.get("schema")!="daee-topology-mass-accounting-v1":return [_finding("topology_mass_schema","schema-version","schema must be daee-topology-mass-accounting-v1")]
    for field in ("case_id","input_sha256","staged_handoff_sha256","output_sha256"):
        if not isinstance(record.get(field),str) or not record[field]:return [_finding("topology_mass_schema","identity-field",f"{field} must be a nonempty string",field)]
    for field in ("input_sha256","staged_handoff_sha256","output_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}",record[field]):return [_finding("topology_mass_schema","hash-shape",f"{field} must be 64 lowercase hex",field)]
    obligations=record.get("obligations")
    if not isinstance(obligations,list):return [_finding("topology_mass_schema","collection-shape","obligations must be an array")]
    if upstream_obligation_ids is None or not isinstance(upstream_obligation_ids,list) or not all(isinstance(item,str) and item for item in upstream_obligation_ids) or len(upstream_obligation_ids)!=len(set(upstream_obligation_ids)):
        return [_finding("topology_mass_schema","upstream-boundary-shape","independent unique upstream obligation IDs are required","external")]
    if not isinstance(upstream_inventory_sha256,str) or not re.fullmatch(r"[0-9a-f]{64}",upstream_inventory_sha256):return [_finding("topology_mass_schema","upstream-boundary-shape","independent upstream source hash is required","external")]
    if record["staged_handoff_sha256"]!=upstream_inventory_sha256:return [_finding("topology_mass_unpaid_obligation","upstream-source-hash-mismatch","staged handoff hash differs from external source hash","external")]
    if not isinstance(evidence_authority,dict) or set(evidence_authority)!={"source_ids","artifacts","validator_receipts"} or evidence_authority_sha256!=canonical_sha256(evidence_authority):
        return [_finding("topology_mass_schema","evidence-authority-boundary","independent hash-bound source, artifact, and validator receipt authority is required","external")]
    source_ids=evidence_authority["source_ids"]
    if not isinstance(source_ids,list) or not all(isinstance(item,str) and item for item in source_ids) or len(source_ids)!=len(set(source_ids)):
        return [_finding("topology_mass_schema","source-inventory-shape","independent source IDs must be unique strings","source_ids","external")]
    artifacts=evidence_authority["artifacts"]
    artifact_by_id={}
    if not isinstance(artifacts,list):return [_finding("topology_mass_schema","artifact-inventory-shape","artifact inventory must be an array","artifacts")]
    for artifact in artifacts:
        if not isinstance(artifact,dict) or set(artifact)!={"artifact_id","content","artifact_sha256"} or not isinstance(artifact.get("artifact_id"),str) or not artifact["artifact_id"] or artifact["artifact_id"] in artifact_by_id or not isinstance(artifact.get("content"),str) or artifact.get("artifact_sha256")!=hashlib.sha256(artifact["content"].encode("utf-8")).hexdigest():
            return [_finding("topology_mass_schema","artifact-inventory-shape","artifact bytes must recompute to one unique typed artifact hash","artifacts")]
        artifact_by_id[artifact["artifact_id"]]=artifact
    receipts=evidence_authority["validator_receipts"]
    receipt_by_evidence={}
    receipt_fields={"receipt_id","evidence_id","artifact_id","artifact_sha256","evidence_type","validator_id","verdict","receipt_sha256"}
    if not isinstance(receipts,list):return [_finding("topology_mass_schema","validator-receipt-shape","validator receipts must be an array","validator_receipts")]
    for receipt in receipts:
        payload={key:value for key,value in receipt.items() if key!="receipt_sha256"} if isinstance(receipt,dict) else {}
        if not isinstance(receipt,dict) or set(receipt)!=receipt_fields or not isinstance(receipt.get("evidence_id"),str) or receipt["evidence_id"] in receipt_by_evidence or receipt.get("verdict")!="PASS" or receipt.get("evidence_type") not in EVIDENCE_TYPES or not isinstance(receipt.get("validator_id"),str) or not receipt["validator_id"] or receipt.get("receipt_sha256")!=canonical_sha256(payload):
            return [_finding("topology_mass_schema","validator-receipt-shape","canonical validator receipt is malformed or self-inconsistent","validator_receipts")]
        artifact=artifact_by_id.get(receipt.get("artifact_id"))
        if not artifact or receipt.get("artifact_sha256")!=artifact["artifact_sha256"]:
            return [_finding("topology_mass_unreconstructible","validator-receipt-artifact-join","validator receipt does not join recomputed artifact bytes",str(receipt.get("evidence_id")))]
        receipt_by_evidence[receipt["evidence_id"]]=receipt
    declared_ids=[item.get("obligation_id") for item in obligations if isinstance(item,dict) and isinstance(item.get("obligation_id"),str)]
    if set(declared_ids)!=set(upstream_obligation_ids):
        missing=sorted(set(upstream_obligation_ids)-set(declared_ids));extra=sorted(set(declared_ids)-set(upstream_obligation_ids));return [_finding("topology_mass_unpaid_obligation","upstream-boundary-mismatch",f"accounted obligations differ from external inventory; missing={missing}, extra={extra}",*missing,*extra,"external")]
    evidence=record.get("evidence_inventory")
    if not isinstance(evidence,list) or not all(isinstance(item,dict) for item in evidence):return [_finding("topology_mass_schema","evidence-inventory-shape","evidence_inventory must contain typed objects","evidence_inventory","typed")]
    evidence_by_id={}
    for item in evidence:
        if set(item)!={"evidence_id","evidence_type","artifact_id","artifact_sha256","validator_receipt_id"} or not isinstance(item.get("evidence_id"),str) or not item["evidence_id"] or item["evidence_id"] in evidence_by_id or item.get("evidence_type") not in EVIDENCE_TYPES or not isinstance(item.get("artifact_id"),str) or not re.fullmatch(r"[0-9a-f]{64}",str(item.get("artifact_sha256",""))) or not isinstance(item.get("validator_receipt_id"),str):
            return [_finding("topology_mass_schema","evidence-inventory-shape","evidence row must be unique, typed, hash-bound, and validated","evidence_inventory")]
        evidence_by_id[item["evidence_id"]]=item
        receipt=receipt_by_evidence.get(item["evidence_id"])
        artifact=artifact_by_id.get(item["artifact_id"])
        if not receipt or not artifact or receipt["receipt_id"]!=item["validator_receipt_id"] or any(receipt[field]!=item[field] for field in ("evidence_id","evidence_type","artifact_id","artifact_sha256")) or item["artifact_sha256"]!=artifact["artifact_sha256"]:
            return [_finding("topology_mass_unreconstructible","evidence-authority-join",f"evidence {item['evidence_id']} lacks an exact canonical validator receipt and artifact join",item["evidence_id"],"external")]
    if not obligations:
        proof=record.get("authoritative_empty_universe")
        if not isinstance(proof,dict) or proof.get("source_count")!=0 or not str(proof.get("basis","")).strip():return [_finding("topology_mass_unpaid_obligation","vacuous-empty-collapse","empty obligations require authoritative empty proof","authoritative_empty_universe")]
        if proof.get("source_inventory_sha256")!=upstream_inventory_sha256:return [_finding("topology_mass_unpaid_obligation","empty-universe-source-mismatch","empty proof does not join external source hash","source_inventory_sha256","external")]
    decisions=record.get("partition_decisions",[])
    if not isinstance(decisions,list):return [_finding("topology_mass_schema","partition-decision-shape","partition_decisions must be an array")]
    decision_ids=set()
    for decision in decisions:
        if not isinstance(decision,dict) or not {"decision_id","decision_type","source_obligation_ids","receiving_obligation_id","basis"}<=set(decision) or not isinstance(decision.get("decision_id"),str) or not decision["decision_id"] or decision.get("decision_type") not in DECISION_TYPES or decision.get("decision_id") in decision_ids or not isinstance(decision.get("source_obligation_ids"),list) or not decision["source_obligation_ids"] or not all(isinstance(item,str) and item for item in decision["source_obligation_ids"]) or len(decision["source_obligation_ids"])!=len(set(decision["source_obligation_ids"])) or not isinstance(decision.get("receiving_obligation_id"),str) or not decision["receiving_obligation_id"] or not str(decision.get("basis","")).strip():
            return [_finding("topology_mass_schema","partition-decision-shape","invalid split/merge/shared-operation decision","partition_decisions")]
        decision_ids.add(decision["decision_id"])
    ids=set();
    for obligation in obligations:
        if not isinstance(obligation,dict):return [_finding("topology_mass_schema","obligation-shape","obligation must be an object")]
        oid=obligation.get("obligation_id")
        if not isinstance(oid,str) or not oid or oid in ids:return [_finding("topology_mass_schema","obligation-id",f"invalid or duplicate obligation ID {oid!r}")]
        ids.add(oid)
        if obligation.get("kind") not in KINDS:return [_finding("topology_mass_schema","obligation-kind",f"{oid} has unsupported obligation kind",oid)]
        if obligation.get("origin_stage") not in {f"{n:02d}" for n in range(1,9)}:return [_finding("topology_mass_schema","origin-stage",f"{oid} has invalid origin_stage",oid)]
        if not isinstance(obligation.get("source_ids"),list) or not obligation["source_ids"] or not all(isinstance(item,str) and item for item in obligation["source_ids"]):return [_finding("topology_mass_schema","source-ids",f"{oid} has invalid source_ids",oid)]
        ghosts=sorted(set(obligation["source_ids"])-set(source_ids))
        if ghosts:return [_finding("topology_mass_unreconstructible","source-inventory-join",f"{oid} names source IDs absent from independent inventory",oid,*ghosts,"external")]
        allowed=obligation.get("allowed_dispositions")
        if not isinstance(allowed,list) or not allowed or not set(allowed)<=DISPOSITIONS or len(allowed)!=len(set(allowed)):return [_finding("topology_mass_schema","allowed-disposition-shape",f"{oid} has invalid allowed_dispositions",oid)]
        refs=obligation.get("evidence_refs")
        if not isinstance(refs,list) or not all(isinstance(item,str) and item for item in refs) or len(refs)!=len(set(refs)):return [_finding("topology_mass_schema","evidence-ref-shape",f"{oid} evidence_refs must be unique strings",oid,"evidence_refs")]
        missing=sorted(set(refs)-set(evidence_by_id))
        if missing:return [_finding("topology_mass_unreconstructible","evidence-ref-missing-from-inventory",f"{oid} evidence {missing[0]} is absent from inventory",oid,missing[0])]
        if obligation.get("disposition")=="satisfied":
            allowed_evidence_types=EVIDENCE_TYPES_BY_KIND[obligation["kind"]]
            actual_types={evidence_by_id[ref]["evidence_type"] for ref in refs}
            if refs and not actual_types.intersection(allowed_evidence_types):
                return [_finding("topology_mass_unreconstructible","evidence-kind-mismatch",f"{oid} satisfied {obligation['kind']} lacks a validated source artifact of type {sorted(allowed_evidence_types)}",oid,*sorted(actual_types))]
        if not str(obligation.get("basis","")).strip():return [_finding("topology_mass_schema","basis",f"{oid} lacks basis",oid)]
    non_claims=record.get("non_claims")
    if not isinstance(non_claims,list) or len(non_claims)!=len(NON_CLAIMS) or set(non_claims)!=set(NON_CLAIMS):
        missing=sorted(set(NON_CLAIMS)-set(non_claims if isinstance(non_claims,list) else []));return [_finding("topology_mass_policy","structural-non-claims-missing",f"missing or altered structural non-claim {missing[0] if missing else 'exact-set-required'}","non_claims",*(missing[:1]))]
    derived=derive_accounting(obligations,evidence,decisions)
    if derived["unreconstructible_obligation_ids"]:
        oid=derived["unreconstructible_obligation_ids"][0];obligation=next(item for item in obligations if item["obligation_id"]==oid)
        if obligation.get("kind")=="owner_operation" and obligation.get("disposition")=="satisfied" and not obligation.get("evidence_refs"):return [_finding("topology_mass_unpaid_obligation","owner-operation-unpaid",f"owner operation {oid} lacks typed evidence",oid)]
        if obligation.get("disposition")=="discharged_duplicate":return [_finding("topology_mass_unreconstructible","duplicate-decision-missing",f"duplicate {oid} lacks receiver plus split/merge/shared-operation decision",oid,str(obligation.get("receiving_obligation_id")),str(obligation.get("decision_id")))]
        if obligation.get("disposition")=="preempted_not_instantiated":return [_finding("topology_mass_unreconstructible","preempted-real-burden",f"{oid} attempts to preempt an instantiated burden",oid)]
        return [_finding("topology_mass_unreconstructible","obligation-unreconstructible",f"obligation {oid} is unreconstructible",oid)]
    if derived["unaccounted_obligation_ids"]:return [_finding("topology_mass_unpaid_obligation","obligation-unaccounted",f"obligation {derived['unaccounted_obligation_ids'][0]} has no legal disposition",derived["unaccounted_obligation_ids"][0])]
    if derived["orphan_evidence_refs"]:return [_finding("topology_mass_orphan_evidence","orphan-evidence",f"evidence {derived['orphan_evidence_refs'][0]} maps to no obligation",derived["orphan_evidence_refs"][0])]
    if derived["duplicate_evidence_groups"]:return [_finding("topology_mass_duplicate_evidence","unproved-shared-evidence","shared evidence lacks valid merge/shared-operation decision",*derived["duplicate_evidence_groups"][0])]
    for key,value in derived.items():
        if record.get(key)!=value:return [_finding("topology_mass_derived_mismatch","derived-accounting-mismatch",f"declared {key} does not equal checker derivation",key)]
    metrics=record.get("advisory_metrics")
    if not isinstance(metrics,dict) or "output_bytes" not in metrics or not all(isinstance(value,int) and not isinstance(value,bool) and value>=0 for value in metrics.values()):return [_finding("topology_mass_schema","advisory-metrics","advisory metrics must be nonnegative integers")]
    return []


def self_test() -> int:
    content="validated capsule";artifact_hash=hashlib.sha256(content.encode("utf-8")).hexdigest()
    evidence=[{"evidence_id":"E1","evidence_type":"operation_capsule","artifact_id":"OC1","artifact_sha256":artifact_hash,"validator_receipt_id":"VR1"}]
    obligations=[{"obligation_id":"O1","kind":"owner_operation","origin_stage":"03","source_ids":["P1","B1"],"allowed_dispositions":["satisfied"],"disposition":"satisfied","evidence_refs":["E1"],"basis":"paid"}]
    record=build_accounting_record(case_id="self-test",input_sha256="1"*64,staged_handoff_sha256="2"*64,output_sha256="3"*64,obligations=obligations,evidence_inventory=evidence,partition_decisions=[],advisory_metrics={"output_bytes":0})
    receipt={"receipt_id":"VR1","evidence_id":"E1","artifact_id":"OC1","artifact_sha256":artifact_hash,"evidence_type":"operation_capsule","validator_id":"operation-capsule-contract","verdict":"PASS"};receipt["receipt_sha256"]=canonical_sha256(receipt)
    authority={"source_ids":["P1","B1"],"artifacts":[{"artifact_id":"OC1","content":content,"artifact_sha256":artifact_hash}],"validator_receipts":[receipt]}
    ok=not validate_accounting(record,upstream_obligation_ids=["O1"],upstream_inventory_sha256="2"*64,evidence_authority=authority,evidence_authority_sha256=canonical_sha256(authority))
    print(json.dumps({"checker_id":"topology-mass-accounting-lib","status":"PASS" if ok else "FAIL"},sort_keys=True))
    return 0 if ok else 1


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--self-test",action="store_true");args=parser.parse_args()
    if args.self_test:return self_test()
    parser.error("topology_mass_accounting is a pure library; use --self-test or import it")


if __name__=="__main__":
    raise SystemExit(main())
