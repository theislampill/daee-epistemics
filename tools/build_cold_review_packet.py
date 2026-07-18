#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from typing import Any
from check_captured_output_manifest import ROOT,PublicationError,atomic_publish_directory,read_json,snapshot_file,verify_artifact
from check_cold_comprehensiveness_review import ANSWER_MARKERS,_structured,validate_packet_manifest
from contract_validation import PathCustodyError,resolve_repo_path

FORBIDDEN_KEYS={"expected_answer","expected_answers","expected_topology","expected_burdens","expected_submoves","expected_counts","favorable_exemplar","favorable_exemplars","cross_case_output","cross_case_outputs","prior_conversation"}
def _keys(value:Any):
 if isinstance(value,dict):
  for key,child in value.items():yield str(key).lower().replace("-","_");yield from _keys(child)
 elif isinstance(value,list):
  for child in value:yield from _keys(child)
def _strings(value:Any):
 if isinstance(value,str):yield value
 elif isinstance(value,dict):
  for child in value.values():yield from _strings(child)
 elif isinstance(value,list):
  for child in value:yield from _strings(child)
def _embedded(root:Path,ref:dict[str,Any])->dict[str,Any]:
 snapshot,issues=verify_artifact(ref,root,"packet-artifact")
 if issues:raise ValueError(f"{issues[0].failure_class}/{issues[0].failure_subcode}: {issues[0].message}")
 assert snapshot
 try:content=snapshot.read_text(encoding="utf-8")
 except UnicodeDecodeError:raise ValueError("packet artifacts must be UTF-8 text")
 return {**ref,"content_utf8":content}
def build(spec_path:Path,custody_root:Path,out_dir_relative:str,*,fault_at:str|None=None)->tuple[Path,Path]:
 spec_snapshot=snapshot_file(spec_path,custody_root);spec=read_json(spec_snapshot);bad=sorted(set(_keys(spec))&FORBIDDEN_KEYS)
 if bad:raise ValueError(f"anti-answer-bank forbidden key: {bad[0]}")
 text=" ".join(_strings(spec)).lower()
 if any(marker in text for marker in ANSWER_MARKERS):raise ValueError("anti-answer-bank instruction marker in packet purpose or rubric")
 if spec.get("retry_mode")=="same-packet-transport":raise ValueError("same-packet transport retry must reuse the existing packet bytes and hash")
 required=("packet_id","protocol_id","case_id","cycle_id","retry_mode","input","output","purpose","public_rubric","stage_records","witness_refs","audit_refs","body_refs","review_authorization","anti_answer_bank_proof")
 missing=[key for key in required if key not in spec]
 if missing:raise ValueError(f"packet spec missing {missing[0]}")
 allowed=set(required)|{"predecessor_packet","packet_delta","builder_red_green_proof"}
 extra=sorted(set(spec)-allowed)
 if extra:raise ValueError(f"packet spec has unsupported metadata key: {extra[0]}")
 if len(spec["stage_records"])!=8:raise ValueError("packet requires exactly Stage01-Stage08 records")
 bindings={"case_id":spec["case_id"],"cycle_id":spec["cycle_id"],"protocol_id":spec["protocol_id"],"input_sha256":spec["input"]["sha256"],"output_sha256":spec["output"]["sha256"]}
 auth,issues=_structured(spec["review_authorization"],custody_root,"authorization","daee-review-authorization-v1",bindings)
 if issues or not auth.get("one_use"):raise ValueError("review authorization proof is invalid or not one-use")
 anti,issues=_structured(spec["anti_answer_bank_proof"],custody_root,"anti-bank","daee-anti-answer-bank-proof-v1",bindings)
 if issues or anti.get("status")!="PASS":raise ValueError("anti-answer-bank proof is invalid")
 if spec["retry_mode"]=="rebuilt-packet":
  for key in ("predecessor_packet","packet_delta","builder_red_green_proof","anti_answer_bank_proof"):
   if not spec.get(key):raise ValueError(f"rebuilt packet missing {key}")
  predecessor_path,ref_issues=verify_artifact(spec["predecessor_packet"],custody_root,"predecessor-packet")
  if ref_issues:raise ValueError(ref_issues[0].message)
  predecessor=read_json(predecessor_path)
  if predecessor.get("input",{}).get("sha256")!=bindings["input_sha256"] or predecessor.get("output",{}).get("sha256")!=bindings["output_sha256"] or predecessor.get("protocol_id")!=bindings["protocol_id"]:raise ValueError("rebuilt predecessor changed input/output/protocol")
  predecessor_issues=validate_packet_manifest(predecessor_path,custody_root,spec["case_id"],spec["cycle_id"],spec["protocol_id"],bindings["input_sha256"],bindings["output_sha256"])
  if predecessor_issues:raise ValueError(f"predecessor packet is semantically invalid: {predecessor_issues[0].failure_subcode}")
  delta,issues=_structured(spec["packet_delta"],custody_root,"packet-delta","daee-packet-delta-v1",{**bindings,"predecessor_packet_sha256":spec["predecessor_packet"]["sha256"]})
  if issues:raise ValueError(issues[0].message)
  if not delta.get("added_refs") and not delta.get("removed_refs"):raise ValueError("packet-delta-empty: rebuilt packet requires a nonempty semantic delta")
  if set(delta.get("added_refs",[]))==set(delta.get("removed_refs",[])):raise ValueError("packet-delta-tautology: added and removed reference sets cannot be equal")
  proof,issues=_structured(spec["builder_red_green_proof"],custody_root,"builder-proof","daee-packet-builder-proof-v1",bindings)
  if issues or not proof.get("red_rejected") or not proof.get("green_accepted"):raise ValueError("rebuilt packet red/green proof is invalid")
 payload={"schema":"daee-cold-review-packet-payload-v1","case_id":spec["case_id"],"cycle_id":spec["cycle_id"],"purpose":spec["purpose"],"public_rubric":spec["public_rubric"],"input":_embedded(custody_root,spec["input"]),"output":_embedded(custody_root,spec["output"]),"stage_records":[_embedded(custody_root,x) for x in spec["stage_records"]],"witness_refs":[_embedded(custody_root,x) for x in spec["witness_refs"]],"audit_refs":[_embedded(custody_root,x) for x in spec["audit_refs"]],"body_refs":[_embedded(custody_root,x) for x in spec["body_refs"]]}
 try:out_dir=resolve_repo_path(custody_root,out_dir_relative,must_exist=False)
 except PathCustodyError as exc:raise ValueError(f"{exc.subcode}: {exc}")
 payload_path=out_dir/"payload.json";payload_bytes=(json.dumps(payload,indent=2,sort_keys=True)+"\n").encode("utf-8")
 rel_payload=payload_path.relative_to(custody_root.resolve()).as_posix();payload_ref={"path":rel_payload,"sha256":hashlib.sha256(payload_bytes).hexdigest(),"byte_count":len(payload_bytes)}
 manifest={"schema":"daee-cold-review-packet-v1","packet_id":spec["packet_id"],"protocol_id":spec["protocol_id"],"case_id":spec["case_id"],"cycle_id":spec["cycle_id"],"retry_mode":spec["retry_mode"],"input":spec["input"],"output":spec["output"],"payload":payload_ref,"predecessor_packet":spec.get("predecessor_packet"),"packet_delta":spec.get("packet_delta"),"builder_red_green_proof":spec.get("builder_red_green_proof"),"anti_answer_bank_proof":spec["anti_answer_bank_proof"],"review_authorization":spec["review_authorization"],"forbidden_content":{"expected_answers":False,"expected_topology_or_counts":False,"favorable_exemplars":False,"cross_case_outputs":False,"prior_conversation":False}}
 manifest_path=out_dir/"manifest.json";manifest_bytes=(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode("utf-8")
 atomic_publish_directory(out_dir,{"payload.json":payload_bytes,"manifest.json":manifest_bytes},fault_at=fault_at)
 return manifest_path,payload_path
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--spec",type=Path);p.add_argument("--custody-root",type=Path);p.add_argument("--out-dir");p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if a.self_test:return subprocess.run([sys.executable,"-B",str(ROOT/"tests/captured-output-custody/test_contract.py")],cwd=ROOT).returncode
 if not a.spec or not a.custody_root or not a.out_dir:p.error("--spec --custody-root --out-dir required")
 try:
  root=a.custody_root.resolve();spec=resolve_repo_path(root,a.spec,must_exist=True,expect_file=True);m,payload=build(spec,root,a.out_dir)
 except (ValueError,PublicationError,OSError,json.JSONDecodeError,PathCustodyError) as exc:print(json.dumps({"status":"FAIL","message":str(exc)},sort_keys=True));return 1
 print(json.dumps({"status":"PASS","manifest":str(m),"payload":str(payload)},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
