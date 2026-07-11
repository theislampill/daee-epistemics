#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from check_captured_output_manifest import ROOT,ArtifactSnapshot,Finding,is_snapshot,read_json,schema_finding,snapshot_file,verify_artifact
from contract_validation import PathCustodyError,resolve_repo_path
CHECKER_ID="review-incident-report";SCHEMA=ROOT/"schema/review-incident-report.schema.json";DOWN=("review-retry","packet-repair","successor-cycle")
def validate_incident_report(path:Path|ArtifactSnapshot,custody_root:Path|None=None)->list[Finding]:
 root=(custody_root or path.parent).resolve();source=path if is_snapshot(path) else snapshot_file(path,root);v=read_json(source)
 issues=schema_finding(v,SCHEMA,stage="control-plane",downstream=DOWN)
 if isinstance(v.get("attempt_lineage"),list) and not v["attempt_lineage"]:return [Finding("incident_lineage","lineage-missing","incident requires complete attempt lineage","control-plane",DOWN)]
 if issues:return issues
 held={}
 for index,(label,ref) in enumerate([("raw-attempt",v["raw_attempt"]),("raw-output",v["raw_output"]),("packet",v["packet"]),*[("lineage",x) for x in v["attempt_lineage"]]]):
  snapshot,issues=verify_artifact(ref,root,label);held[(ref.get("path"),ref.get("sha256"),ref.get("byte_count"))]=snapshot
  if issues:return [Finding(issues[0].failure_class,issues[0].failure_subcode,issues[0].message,"control-plane",DOWN)]
 attempt_path=held[(v["raw_attempt"]["path"],v["raw_attempt"]["sha256"],v["raw_attempt"]["byte_count"])];attempt=read_json(attempt_path)
 if attempt.get("review_id")!=v["classified_attempt_id"]:return [Finding("incident_binding","attempt-id-mismatch","incident classified_attempt_id differs from raw attempt","control-plane",DOWN)]
 if attempt.get("output",{}).get("sha256")!=v["raw_output"]["sha256"] or attempt.get("packet",{}).get("sha256")!=v["packet"]["sha256"]:return [Finding("incident_binding","attempt-artifact-mismatch","incident output or packet differs from raw attempt","control-plane",DOWN)]
 if attempt.get("case_id")!=v["case_id"] or attempt.get("cycle_id")!=v["cycle_id"] or attempt.get("comprehension",{}).get("status")!="REVIEW_INVALID":return [Finding("incident_binding","attempt-semantic-mismatch","incident must bind the same case/cycle and a REVIEW_INVALID attempt","control-plane",DOWN)]
 lineage_ids=[]
 for index,ref in enumerate(v["attempt_lineage"],1):
  lineage_path=held[(ref["path"],ref["sha256"],ref["byte_count"])];row=read_json(lineage_path);lineage_ids.append(row.get("review_id"))
  if row.get("attempt_index")!=index or row.get("case_id")!=v["case_id"] or row.get("cycle_id")!=v["cycle_id"]:return [Finding("incident_lineage","lineage-order","incident attempt lineage must be contiguous and identity-bound","control-plane",DOWN)]
 if len(lineage_ids)!=len(set(lineage_ids)) or v["attempt_lineage"][-1].get("sha256")!=v["raw_attempt"]["sha256"]:return [Finding("incident_lineage","lineage-terminal","classified raw attempt must be the unique terminal lineage entry","control-plane",DOWN)]
 grading_values=list(attempt.get("grading",{}).values());graded=any(value!="NOT_GRADED" for value in grading_values)
 if graded!=v["substantive_grading_occurred"]:return [Finding("incident_binding","grading-flag-mismatch","substantive grading flag differs from raw attempt","control-plane",DOWN)]
 if v["proposed_action"]!="stop":
  authority_path,issues=verify_artifact(v.get("continuation_authority"),root,"continuation-authority")
  if issues:return [Finding("continuation_authority","authority-missing",issues[0].message,"control-plane",DOWN)]
  authority=read_json(authority_path)
  if authority.get("schema")!="daee-review-authorization-v1" or not authority.get("one_use") or authority.get("case_id")!=v["case_id"] or authority.get("cycle_id")!=v["cycle_id"] or authority.get("input_sha256")!=attempt.get("input",{}).get("sha256") or authority.get("output_sha256")!=v["raw_output"]["sha256"]:return [Finding("continuation_authority","authority-binding","continuation authority must be one-use and bind case/cycle/input/output","control-plane",DOWN)]
 if not v["owner_notification"].get("notified_utc"):return [Finding("owner_notification","notification-missing","owner notification timestamp is required","control-plane",DOWN)]
 return []
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--report",type=Path);p.add_argument("--custody-root",type=Path);p.add_argument("--explain",action="store_true");p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if a.self_test:return subprocess.run([sys.executable,str(ROOT/"tests/captured-output-custody/test_contract.py")],cwd=ROOT).returncode
 if not a.report:p.error("--report required")
 root=(a.custody_root or ROOT).resolve()
 try:path=resolve_repo_path(root,a.report,must_exist=True,expect_file=True)
 except PathCustodyError as exc:print(json.dumps({"checker_id":CHECKER_ID,"failure_class":"path_custody","failure_subcode":exc.subcode,"message":str(exc)},sort_keys=True));return 1
 fs=validate_incident_report(path,root)
 if fs:
  x=fs[0];print(json.dumps({"checker_id":CHECKER_ID,"manifest_path":str(path),"exit_category":"structural-rejection","exit_code":1,"earliest_stage":x.earliest_stage,"failure_class":x.failure_class,"failure_subcode":x.failure_subcode,"downstream_invalidated":list(x.downstream_invalidated),"message":x.message},sort_keys=True));return 1
 print(json.dumps({"checker_id":CHECKER_ID,"status":"PASS"},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
