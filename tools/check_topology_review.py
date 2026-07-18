#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from datetime import datetime
from pathlib import Path
from typing import Any
from check_captured_output_manifest import ROOT, ArtifactSnapshot, Finding, is_snapshot, read_json, schema_finding, snapshot_file, verify_artifact
from contract_validation import PathCustodyError,resolve_repo_path

CHECKER_ID="topology-review"
SCHEMA=ROOT/"schema/topology-review.schema.json"
INITIAL_SCHEMA=ROOT/"schema/topology-initial-assessment.schema.json"
DOWN=("human-adjudication","cycle-verdict")
def f(cls,sub,msg): return [Finding(cls,sub,msg,"control-plane",DOWN)]
def validate_topology_review(path:Path|ArtifactSnapshot,custody_root:Path|None=None)->list[Finding]:
 root=(custody_root or path.parent).resolve();source=path if is_snapshot(path) else snapshot_file(path,root);v=read_json(source)
 issues=schema_finding(v,SCHEMA,stage="control-plane",downstream=DOWN)
 if issues:return issues
 stage_refs=[v.get("artifacts",{}).get(key) for key in ("stage02","stage04","stage05")]
 if all(isinstance(ref,dict) for ref in stage_refs) and len({ref.get("sha256") for ref in stage_refs})!=3:return f("review_binding","topology-stage-alias","topology stages 02, 04, and 05 must be distinct immutable artifacts")
 if v.get("initial_assessment") is None:return f("review_custody","initial-assessment-missing","initial assessment is required before cold disclosure")
 held={}
 for label,ref in [("input",v["input"]),*v["artifacts"].items(),("initial-assessment",v["initial_assessment"]),("cold-review",v["cold_review_disclosure"].get("cold_review"))]:
  snapshot,issues=verify_artifact(ref,root,label);held[label]=snapshot
  if issues:return [Finding(issues[0].failure_class,issues[0].failure_subcode,issues[0].message,"control-plane",DOWN)]
 stage_rows=[]
 for label,stage_id in (("stage02","02"),("stage04","04"),("stage05","05")):
  try:row=read_json(held[label])
  except (UnicodeDecodeError,json.JSONDecodeError):return f("review_binding","topology-stage-shape",f"{label} must be a canonical stage JSON artifact")
  stage_rows.append(row)
  if row.get("schema")!="daee-stage-record-v1" or row.get("stage_id")!=stage_id or row.get("case_id")!=v["case_id"] or row.get("cycle_id")!=v["cycle_id"] or row.get("input_sha256")!=v["input"]["sha256"] or row.get("output_sha256")!=v["artifacts"]["stage07_output"]["sha256"]:return f("review_binding","topology-stage-binding",f"{label} identity tuple differs from topology review")
 if len({(row.get("source_commit"),row.get("package_sha256")) for row in stage_rows})!=1:return f("review_binding","topology-runtime-drift","topology stage source/package identities differ")
 initial_path=held["initial-assessment"];initial=read_json(initial_path)
 issues=schema_finding(initial,INITIAL_SCHEMA,stage="control-plane",downstream=DOWN)
 if issues:return issues
 for label,rows,key in (("assessment-question",initial.get("question_answers",[]),"question_id"),("assessment-finding",initial.get("findings",[]),"finding_id")):
  identities=[row.get(key) for row in rows]
  if any(not str(identity or "").strip() for identity in identities) or len(identities)!=len(set(identities)):return f("review_set",f"duplicate-{label}",f"{label} identities must be nonempty and unique")
 for label,ref in (("initial-input",initial.get("input")),("initial-output",initial.get("output"))):
  _,issues=verify_artifact(ref,root,label)
  if issues:return f("review_custody","initial-artifact-invalid",issues[0].message)
 if initial.get("case_id")!=v["case_id"] or initial.get("cycle_id")!=v["cycle_id"] or initial.get("input",{}).get("sha256")!=v["input"]["sha256"] or initial.get("output",{}).get("sha256")!=v["artifacts"]["stage07_output"]["sha256"]:return f("review_binding","initial-identity-mismatch","initial assessment case/cycle/input/output differs from topology review")
 reviewer=v["reviewer"]
 if initial.get("reviewer_identity_or_accountable_role")!=reviewer.get("identity_or_accountable_role"):return f("review_binding","reviewer-identity-drift","final topology reviewer identity differs from the immutable pre-disclosure assessment reviewer")
 if not str(reviewer.get("identity_or_accountable_role","")).strip() or not str(reviewer.get("independence_basis","")).strip():return f("independence","reviewer-basis-missing","reviewer identity and independence basis are required")
 disclosure=v["cold_review_disclosure"]
 if disclosure.get("initial_assessment_sha256_at_disclosure")!=v["initial_assessment"]["sha256"]:return f("review_custody","initial-assessment-hash-drift","disclosure initial assessment hash differs from immutable assessment")
 try:
  if datetime.fromisoformat(initial["recorded_utc"].replace("Z","+00:00"))>=datetime.fromisoformat(disclosure["disclosed_utc"].replace("Z","+00:00")):return f("review_custody","assessment-not-before-disclosure","initial assessment timestamp must precede disclosure")
 except ValueError:return f("review_custody","timestamp-shape","review timestamps must be RFC3339-compatible")
 cold_path=held["cold-review"];cold=read_json(cold_path)
 cold_ids=[row.get("finding_id") for row in cold.get("findings",[]) if isinstance(row,dict)]
 if len(cold_ids)!=len(set(cold_ids)):return f("review_set","duplicate-cold-finding","cold finding IDs must be unique before adjudication set equality")
 from check_cold_comprehensiveness_review import validate_cold_review
 cold_issues=validate_cold_review(cold_path,root)
 if cold_issues:return f("cross_object","cold-review-invalid",f"cold review invalid: {cold_issues[0].failure_class}/{cold_issues[0].failure_subcode}")
 if cold.get("case_id")!=v["case_id"] or cold.get("cycle_id")!=v["cycle_id"] or cold.get("input",{}).get("sha256")!=v["input"]["sha256"] or cold.get("output",{}).get("sha256")!=v["artifacts"]["stage07_output"]["sha256"]:return f("review_binding","cold-identity-mismatch","cold review case/cycle/input/output differs from topology review")
 adj_ids=[row.get("cold_finding_id") for row in v["cold_challenge_adjudications"]]
 if len(adj_ids)!=len(set(adj_ids)):return f("review_set","duplicate-adjudication","duplicate cold finding adjudication")
 if set(cold_ids)-set(adj_ids):return f("review_set","missing-adjudication","cold finding lacks human adjudication")
 if set(adj_ids)-set(cold_ids):return f("review_set","unknown-adjudication","human adjudication names no cold finding")
 severity={row.get("finding_id"):row.get("severity") for row in cold.get("findings",[])}
 for row in v["cold_challenge_adjudications"]:
  if row.get("disposition")=="answered":
   if not row.get("evidence_refs"):return f("challenge_answer","evidence-missing","answered challenge requires hash-valid evidence")
   covered=set()
   for ref in row["evidence_refs"]:
    _,issues=verify_artifact(ref,root,"challenge-evidence")
    if issues:return f("challenge_answer","evidence-hash-drift",issues[0].message)
    covered.update(ref.get("target_ids",[]))
   if covered!=set(row.get("challenged_target_ids",[])):return f("challenge_answer","target-mismatch","challenge evidence target set differs from challenged targets")
   if row.get("rationale_finding_id")!=row.get("cold_finding_id") or not str(row.get("rationale","")).strip():return f("challenge_answer","rationale-mismatch","finding-specific rationale is required")
  if severity.get(row.get("cold_finding_id"))=="material" and row.get("disposition") in {"upheld","unresolved"} and v["verdict"]=="PASS":return f("claim_overreach","material-challenge-open","material upheld or unresolved challenge prevents PASS")
 if v["structural_status"]!="PASS" and v["verdict"]=="PASS":return f("claim_overreach","structural-failure-waiver","human review cannot waive structural failure")
 owner=v["owner_adjudication"];rel=v["reviewer"].get("relationship_to_producer");required=bool(owner.get("material_reversal") or owner.get("patch_owner_involved") or rel=="patch-owner")
 second=v["second_independent_review"]
 if v["verdict"]=="PASS" and rel in {"producer","owner-adjudicator"} and not second.get("required"):return f("independence","independent-review-required","producer self-review cannot satisfy independent review PASS")
 if required and not second.get("required"):return f("independence","second-review-required","patch-owner or material reversal requires a second independent review")
 if required:
  review_ref=second.get("review");second_path,issues=verify_artifact(review_ref,root,"second-review")
  if issues:return f("independence","second-review-invalid",issues[0].message)
  proof=read_json(second_path)
  if proof.get("schema")!="daee-second-independent-review-v1" or proof.get("case_id")!=v["case_id"] or proof.get("cycle_id")!=v["cycle_id"] or proof.get("output",{}).get("sha256")!=v["artifacts"]["stage07_output"]["sha256"] or proof.get("patch_owner_identity_or_role")!=v["reviewer"]["identity_or_accountable_role"]:return f("independence","second-review-binding","second review must bind the same case/cycle/output and patch owner")
  identities={proof.get("reviewer_identity_or_accountable_role"),v["reviewer"].get("identity_or_accountable_role")}
  if None in identities or "" in identities or len(identities)!=2:return f("independence","second-reviewer-not-distinct","second reviewer must be a distinct accountable human independent of the first reviewer and patch owner")
  _,issues=verify_artifact(proof.get("output"),root,"second-review-output")
  if issues:return f("independence","second-review-output-invalid",issues[0].message)
  if proof.get("relationship_to_patch_owner")!="independent" or not proof.get("independence_basis") or proof.get("verdict")!="PASS":return f("independence","second-review-not-affirming","second review must be independent and affirming")
 human_ids=[row.get("finding_id") for row in v["findings"]]
 if any(not str(identity or "").strip() for identity in human_ids) or len(human_ids)!=len(set(human_ids)):return f("review_set","duplicate-human-finding","human finding IDs must be nonempty and unique")
 return []
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--review",type=Path);p.add_argument("--custody-root",type=Path);p.add_argument("--explain",action="store_true");p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if a.self_test:return subprocess.run([sys.executable,"-B",str(ROOT/"tests/captured-output-custody/test_contract.py")],cwd=ROOT).returncode
 if not a.review:p.error("--review required")
 root=(a.custody_root or ROOT).resolve()
 try:path=resolve_repo_path(root,a.review,must_exist=True,expect_file=True)
 except PathCustodyError as exc:print(json.dumps({"checker_id":CHECKER_ID,"failure_class":"path_custody","failure_subcode":exc.subcode,"message":str(exc)},sort_keys=True));return 1
 fs=validate_topology_review(path,root)
 if fs:
  x=fs[0];d={"checker_id":CHECKER_ID,"manifest_path":str(path),"exit_category":"structural-rejection","exit_code":1,"earliest_stage":x.earliest_stage,"failure_class":x.failure_class,"failure_subcode":x.failure_subcode,"downstream_invalidated":list(x.downstream_invalidated),"message":x.message};print(json.dumps(d,sort_keys=True) if a.explain else d);return 1
 print(json.dumps({"checker_id":CHECKER_ID,"status":"PASS"},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
