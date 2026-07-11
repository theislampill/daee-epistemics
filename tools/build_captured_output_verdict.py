#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from check_captured_output_manifest import ROOT,PublicationError,atomic_publish_bytes,read_json,snapshot_file,validate_capture_manifest,validate_comparison_manifest
from contract_validation import PathCustodyError,resolve_repo_path

def build(source:Path,custody_root:Path,kind:str)->dict:
 snapshot=snapshot_file(source,custody_root)
 findings=validate_capture_manifest(snapshot,custody_root) if kind=="capture" else validate_comparison_manifest(snapshot,custody_root)
 if findings:raise ValueError(f"{findings[0].failure_class}/{findings[0].failure_subcode}: {findings[0].message}")
 value=read_json(snapshot)
 if kind=="capture":
  return {"schema":"daee-captured-output-verdict-v1","kind":"capture-structural-verdict","capture_id":value["capture_id"],"capture_manifest_sha256":snapshot.sha256,"structural_status":value["structural_replay"]["aggregate_status"],"promotion_eligible":False,"regression_status":"unproven","non_claims":["structural verdict is not semantic truth","capture verdict cannot establish regression causality"]}
 return {"schema":"daee-captured-output-verdict-v1","kind":"comparison-custody-verdict","comparison_id":value["comparison_id"],"comparison_manifest_sha256":snapshot.sha256,"regression_status":value["regression_status"],"promotion_eligible":False,"non_claims":["no automated tool emits proven","output length and one pair do not prove causality"]}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--capture",type=Path);p.add_argument("--comparison",type=Path);p.add_argument("--custody-root",type=Path);p.add_argument("--out",type=Path);p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if a.self_test:return subprocess.run([sys.executable,str(ROOT/"tests/captured-output-custody/test_contract.py")],cwd=ROOT).returncode
 source=a.capture or a.comparison
 if source is None or a.out is None:p.error("--capture or --comparison and --out required")
 root=(a.custody_root or ROOT).resolve()
 try:
  source=resolve_repo_path(root,source,must_exist=True,expect_file=True);out=resolve_repo_path(root,a.out,must_exist=False)
  if out.exists():raise ValueError("output path already exists")
  data=build(source,root,"capture" if a.capture else "comparison")
  encoded=(json.dumps(data,indent=2,sort_keys=True)+"\n").encode("utf-8")
  atomic_publish_bytes(out,encoded)
 except (ValueError,PublicationError,OSError,PathCustodyError) as exc:print(json.dumps({"status":"FAIL","message":str(exc)},sort_keys=True));return 1
 return 0
if __name__=="__main__":raise SystemExit(main())
