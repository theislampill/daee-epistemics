#!/usr/bin/env python3
"""Validate the separately authorized parent-owned paired GPT/Opus protocol."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from check_parallel_dispatch_manifest import validate_dispatch_manifest
from contract_validation import SchemaDefinitionError, validate_schema_subset
from smoke_matrix_registry import load_registry

SCHEMA_PATH=Path(__file__).resolve().parents[1]/"schema"/"cross-model-paired-cycle.schema.json"


def _err(cls: str, message: str) -> dict[str,str]: return {"failure_class":cls,"message":message}


def validate_paired_manifest(data: object) -> list[dict[str,str]]:
    try:issues=validate_schema_subset(data,json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    except SchemaDefinitionError as exc:return [_err("schema_definition",str(exc))]
    if issues:return [_err("schema_contract",f"{issue.path} {issue.keyword}: {issue.message}") for issue in issues]
    if not isinstance(data,dict): return [_err("paired_shape","paired manifest must be an object")]
    if data.get("schema")!="daee-cross-model-paired-cycle-v1" or data.get("kind")!="paired-cycle-manifest": return [_err("paired_discriminator","paired discriminator mismatch")]
    if not data.get("post_completion_opus_authorization"): return [_err("opus_authorization","separate post-completion Opus authorization is required")]
    g=data.get("gpt_candidate",{}); o=data.get("opus_candidate",{})
    if g.get("candidate_id")==o.get("candidate_id"): return [_err("sibling_candidate_identity","paired siblings require distinct candidate identities")]
    provenance=("source_commit","package_sha256","archive_sha256","extracted_tree_sha256","build_manifest_sha256","registry_sha256")
    if any(not g.get(field) or g.get(field)!=o.get(field) for field in provenance):return [_err("sibling_provenance_mismatch","sibling source, package, archive, tree, build-manifest, and registry provenance must be identical")]
    if data.get("pass_carry_forward") is not False: return [_err("pass_carry_forward","paired cycle forbids one-model pass carry-forward")]
    for row in data.get("root_recurrences",[]):
        if row.get("circuit_breaker")!="OPEN":
            family=str(row.get("model_family","unknown")).upper(); cls="gpt_root_recurrence" if family=="GPT" else "opus_root_recurrence" if family=="OPUS" else "root_cause_circuit_breaker"
            return [_err(cls,f"{family} root recurrence requires an open circuit breaker")]
    expected_cases=[row["case_id"] for row in load_registry()["cases"]]
    all_workers=[]
    for field,family,candidate in (("gpt_rows","GPT",g),("opus_rows","OPUS",o)):
        rows=data.get(field)
        if not isinstance(rows,list) or len(rows)!=5 or any(not isinstance(row,dict) for row in rows):return [_err("paired_cohort_shape",f"parent must own exactly five structured {family} rows")]
        if [row.get("case_id") for row in rows]!=expected_cases:return [_err("paired_cohort_shape",f"{family} cohort must cover the exact ordered canonical five registry cases")]
        if any(row.get("model_family")!=family or row.get("candidate_id")!=candidate.get("candidate_id") for row in rows):return [_err("paired_candidate_binding",f"every {family} row must bind its sibling candidate")]
        workers=[row.get("worker") for row in rows]
        if any(not isinstance(worker,str) or not worker for worker in workers) or len(set(workers))!=5:return [_err("paired_cohort_shape",f"{family} row workers must be distinct")]
        all_workers.extend(workers)
    if len(set(all_workers))!=10:return [_err("paired_cohort_overlap","GPT and OPUS cohorts cannot overlap workers")]
    inventory=data.get("dispatch_manifest",{}).get("workers")
    if not isinstance(inventory,list) or {row.get("worker") for row in inventory if isinstance(row,dict)}!=set(all_workers):return [_err("paired_worker_binding","dispatch workers must equal the ten cohort row workers")]
    row_by_worker={row["worker"]:row for row in data["gpt_rows"]+data["opus_rows"]}
    if any(row_by_worker.get(item.get("worker"),{}).get("case_id")!=item.get("case_id") or row_by_worker.get(item.get("worker"),{}).get("model_family")!=item.get("model_family") for item in inventory):return [_err("paired_worker_binding","dispatch worker model/case binding must match its cohort row")]
    errors=validate_dispatch_manifest(data.get("dispatch_manifest"),10)
    return errors


def self_test() -> int:
    fixture=Path(__file__).resolve().parents[1]/"tests"/"smoke-matrix"/"fixtures"/"valid"/"paired-matching.json"
    base=json.loads(fixture.read_text(encoding="utf-8"))
    checks=[("matching siblings and barrier",not validate_paired_manifest(base)),("mismatch rejected",validate_paired_manifest({**base,"opus_candidate":{**base["opus_candidate"],"package_sha256":"0"*64}})[0]["failure_class"]=="sibling_provenance_mismatch"),("carry-forward rejected",validate_paired_manifest({**base,"pass_carry_forward":True})[0]["failure_class"]=="pass_carry_forward")]
    for n,o in checks: print(f"  self-test {'PASS' if o else 'FAIL'}: {n}")
    return 0 if all(o for _,o in checks) else 1


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument("--manifest",type=Path);p.add_argument("--self-test",action="store_true");a=p.parse_args()
    if a.self_test:return self_test()
    if not a.manifest:p.error("--manifest required unless --self-test")
    errors=validate_paired_manifest(json.loads(a.manifest.read_text(encoding="utf-8")));print(json.dumps({"status":"FAIL" if errors else "PASS","errors":errors},sort_keys=True));return 1 if errors else 0


if __name__=="__main__":sys.exit(main())
