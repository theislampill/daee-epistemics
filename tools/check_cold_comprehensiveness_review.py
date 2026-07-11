#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from check_captured_output_manifest import ROOT,ArtifactSnapshot,Finding,is_snapshot,read_json,schema_finding,snapshot_file,verify_artifact
from contract_validation import PathCustodyError,resolve_repo_path
CHECKER_ID="cold-comprehensiveness-review";SCHEMA=ROOT/"schema/cold-comprehensiveness-review.schema.json";DOWN=("human-adjudication","cycle-verdict")
ANSWER_MARKERS=("answer key","golden answer","golden conclusion","expected conclusion","expected answer","grading key","model answer")
def f(c,s,m,d=DOWN):return [Finding(c,s,m,"control-plane",d)]
def _structured(ref,root,label,schema_name,bindings):
 path,issues=verify_artifact(ref,root,label)
 if issues:return None,f("packet_proof",f"{label}-invalid",issues[0].message)
 value=read_json(path)
 if value.get("schema")!=schema_name:return None,f("packet_proof",f"{label}-shape",f"{label} has wrong schema")
 for key,expected in bindings.items():
  if value.get(key)!=expected:return None,f("packet_proof",f"{label}-binding",f"{label} {key} differs from packet")
 return value,[]
def validate_packet_manifest(path:Path|ArtifactSnapshot,root:Path,case_id:str,cycle_id:str,protocol_id:str,input_sha:str,output_sha:str,_seen:set[Path]|None=None)->list[Finding]:
 seen=set() if _seen is None else set(_seen);resolved=path.resolve()
 if resolved in seen:return f("packet_binding","packet-lineage-cycle","packet predecessor lineage contains a cycle")
 seen.add(resolved)
 packet=read_json(path);required={"schema","packet_id","protocol_id","case_id","cycle_id","retry_mode","input","output","payload","predecessor_packet","packet_delta","builder_red_green_proof","anti_answer_bank_proof","review_authorization","forbidden_content"}
 if set(packet)!=required or packet.get("schema")!="daee-cold-review-packet-v1":return f("packet_binding","packet-shape","packet manifest has missing or extra fields")
 if (packet.get("case_id"),packet.get("cycle_id"),packet.get("protocol_id"),packet.get("input",{}).get("sha256"),packet.get("output",{}).get("sha256"))!=(case_id,cycle_id,protocol_id,input_sha,output_sha):return f("packet_binding","packet-identity-mismatch","packet case/cycle/protocol/input/output binding differs")
 snapshots={}
 for label in ("input","output","payload"):
  snapshot,issues=verify_artifact(packet.get(label),root,label);snapshots[label]=snapshot
  if issues:return f("packet_binding",f"{label}-invalid",issues[0].message)
 bindings={"case_id":case_id,"cycle_id":cycle_id,"protocol_id":protocol_id,"input_sha256":input_sha,"output_sha256":output_sha}
 auth,issues=_structured(packet["review_authorization"],root,"authorization","daee-review-authorization-v1",bindings)
 if issues:return issues
 if not auth.get("one_use") or not auth.get("authorization_id"):return f("packet_proof","authorization-one-use","review authorization must be identified and one-use")
 anti,issues=_structured(packet["anti_answer_bank_proof"],root,"anti-bank","daee-anti-answer-bank-proof-v1",bindings)
 if issues:return issues
 if anti.get("status")!="PASS":return f("packet_proof","anti-bank-not-pass","anti-answer-bank proof must PASS")
 payload_path=snapshots["payload"];payload=read_json(payload_path)
 if payload.get("schema")!="daee-cold-review-packet-payload-v1" or payload.get("case_id")!=case_id or payload.get("cycle_id")!=cycle_id:return f("packet_binding","payload-identity-mismatch","payload case/cycle differs from packet")
 text=" ".join(str(payload.get(key,"")) for key in ("purpose","public_rubric")).lower()
 if any(marker in text for marker in ANSWER_MARKERS):return f("packet_content","answer-bank-marker","packet purpose/rubric contains an answer-key or expected-conclusion marker")
 if len(payload.get("stage_records",[]))!=8:return f("packet_binding","stage-record-count","packet payload requires Stage01-Stage08")
 if payload.get("input",{}).get("sha256")!=input_sha or payload.get("output",{}).get("sha256")!=output_sha:return f("packet_binding","payload-input-output","payload input/output differs from packet")
 if payload.get("input",{}).get("content_utf8","").encode("utf-8")!=snapshots["input"].read_bytes() or payload.get("output",{}).get("content_utf8","").encode("utf-8")!=snapshots["output"].read_bytes():return f("packet_binding","embedded-bytes-mismatch","payload does not embed exact input/output bytes")
 for group in ("stage_records","witness_refs","audit_refs","body_refs"):
  for ref in payload.get(group,[]):
   _,issues=verify_artifact(ref,root,f"payload-{group}")
   if issues:return f("packet_binding",f"payload-{group}-invalid",issues[0].message)
 if any(packet.get("forbidden_content",{}).values()):return f("packet_content","answer-bank-present","packet declares forbidden review content")
 if packet["retry_mode"]=="initial":
  if any(packet.get(key) is not None for key in ("predecessor_packet","packet_delta","builder_red_green_proof")):return f("packet_binding","initial-lineage-present","initial packet cannot declare rebuild lineage")
 elif packet["retry_mode"]=="rebuilt-packet":
  predecessor,issues_ref=verify_artifact(packet.get("predecessor_packet"),root,"predecessor-packet")
  if issues_ref:return f("packet_proof","predecessor-packet-invalid",issues_ref[0].message)
  pred_value=read_json(predecessor)
  if pred_value.get("input",{}).get("sha256")!=input_sha or pred_value.get("output",{}).get("sha256")!=output_sha or pred_value.get("protocol_id")!=protocol_id:return f("packet_proof","predecessor-binding","predecessor packet changed input/output/protocol")
  pred_issues=validate_packet_manifest(predecessor,root,case_id,cycle_id,protocol_id,input_sha,output_sha,seen)
  if pred_issues:return f("packet_proof","predecessor-semantic-invalid",f"predecessor packet invalid: {pred_issues[0].failure_class}/{pred_issues[0].failure_subcode}")
  delta,issues=_structured(packet.get("packet_delta"),root,"packet-delta","daee-packet-delta-v1",{**bindings,"predecessor_packet_sha256":packet["predecessor_packet"]["sha256"]})
  if issues:return issues
  if not delta.get("added_refs") and not delta.get("removed_refs"):return f("packet_proof","packet-delta-empty","rebuilt packet delta must record a nonempty predecessor-bound semantic change")
  if set(delta.get("added_refs",[]))==set(delta.get("removed_refs",[])):return f("packet_proof","packet-delta-tautology","rebuilt packet delta cannot add and remove the same reference set")
  proof,issues=_structured(packet.get("builder_red_green_proof"),root,"builder-proof","daee-packet-builder-proof-v1",bindings)
  if issues:return issues
  if not proof.get("red_rejected") or not proof.get("green_accepted"):return f("packet_proof","builder-proof-not-green","builder proof requires deterministic red and green")
 else:return f("packet_binding","retry-mode","unsupported packet retry mode")
 return []
def validate_cold_review(path:Path|ArtifactSnapshot,custody_root:Path|None=None)->list[Finding]:
 root=(custody_root or path.parent).resolve();source=path if is_snapshot(path) else snapshot_file(path,root);v=read_json(source);issues=schema_finding(v,SCHEMA,stage="control-plane",downstream=DOWN)
 if issues:return issues
 r=v["reviewer"]
 if r.get("model_family")!="gpt-5.6-sol" or r.get("reasoning_effort")!="xhigh" or not r.get("exact_model_identifier"):return f("review_identity","reviewer-model","exact gpt-5.6-sol/xhigh identity is required")
 if not r.get("fresh_context") or any(r.get(k) for k in ("prior_conversation_supplied","cross_case_context_supplied","expected_topology_supplied","answer_bank_supplied")):return f("review_isolation","prior-context","cold review requires fresh context without prior conversation, cross-case context, topology, or answer bank")
 bindings={"case_id":v["case_id"],"cycle_id":v["cycle_id"],"protocol_id":v["review_protocol_id"],"input_sha256":v["input"]["sha256"],"output_sha256":v["output"]["sha256"]}
 auth,auth_issues=_structured(v["review_authorization"],root,"review-authorization","daee-review-authorization-v1",bindings)
 if auth_issues or not auth.get("one_use") or not auth.get("authorization_id"):return f("review_identity","review-authorization-binding","cold review authorization must be one-use and bind case/cycle/protocol/input/output")
 stage_hashes=[ref.get("sha256") for ref in v["stage_records"]]
 if len(stage_hashes)!=len(set(stage_hashes)):return f("stage_identity","duplicate-stage-evidence","Stage01-Stage08 must be eight distinct immutable artifacts")
 verified={}
 for label,ref in [("packet",v["packet"]),("input",v["input"]),("output",v["output"]),*[("stage",x) for x in v["stage_records"]],*[("witness",x) for x in v["witness_refs"]],*[("audit",x) for x in v["audit_refs"]],*[("body",x) for x in v["body_refs"]]]:
  snapshot,issues=verify_artifact(ref,root,label)
  if label in {"packet","input","output"}:verified[label]=snapshot
  if issues:return f(issues[0].failure_class,issues[0].failure_subcode,issues[0].message)
 stage_rows=[]
 for index,ref in enumerate(v["stage_records"],1):
  snapshot,ref_issues=verify_artifact(ref,root,"stage")
  if ref_issues:return f(ref_issues[0].failure_class,ref_issues[0].failure_subcode,ref_issues[0].message)
  row=read_json(snapshot);stage_rows.append(row)
  expected={"schema":"daee-stage-record-v1","stage_id":f"{index:02d}","case_id":v["case_id"],"cycle_id":v["cycle_id"],"input_sha256":v["input"]["sha256"],"output_sha256":v["output"]["sha256"]}
  if any(row.get(key)!=wanted for key,wanted in expected.items()):return f("stage_identity","stage-tuple-binding","stage identity/order/case/cycle/input/output tuple differs")
  if not all(str(row.get(key,"")).strip() for key in ("source_commit","package_sha256","checker_id","verdict")):return f("stage_identity","stage-tuple-incomplete","stage source/package/checker/verdict tuple is incomplete")
 checker_ids=[row["checker_id"] for row in stage_rows]
 if len(checker_ids)!=len(set(checker_ids)):return f("stage_identity","duplicate-stage-checker","stage checker identities must be unique")
 if len({(row["source_commit"],row["package_sha256"]) for row in stage_rows})!=1:return f("stage_identity","stage-runtime-drift","stage source/package identities drift within one review")
 comp=v["comprehension"];grading=v["grading"]
 if comp.get("status")=="PASS" and not comp.get("completed_before_grading"):return f("comprehension_gate","grades-before-comprehension","comprehension must complete before grading")
 if comp.get("status")=="REVIEW_INVALID":
  if any(value!="NOT_GRADED" for value in grading.values()):return f("review_laundering","invalid-review-graded","REVIEW_INVALID requires every grade to remain NOT_GRADED")
  if v["findings"]:return f("review_laundering","invalid-review-findings","REVIEW_INVALID cannot emit candidate findings")
 if comp.get("status")=="PASS" and not v["selection"].get("selected_for_final"):return f("review_shopping","latest-valid-not-selected","the latest valid attempt derived from complete lineage must be selected")
 if comp.get("status")=="REVIEW_INVALID" and v["selection"].get("selected_for_final"):return f("review_shopping","invalid-attempt-selected","REVIEW_INVALID attempt cannot be selected")
 cls=v.get("invalid_classification")
 finding_ids=[row.get("finding_id") for row in v["findings"]]
 if len(finding_ids)!=len(set(finding_ids)):return f("review_set","duplicate-cold-finding","cold finding IDs must be unique")
 if v["attempt_index"]>1 and (not v.get("predecessor_review_attempt") or not cls or not cls.get("owner_incident_report")):return f("retry_lineage","incident-missing","retry requires predecessor and owner incident before continuation",("review-retry","packet-repair","successor-cycle"))
 lineage=v["attempt_lineage"]
 if len(lineage)!=v["attempt_index"]-1:return f("retry_lineage","attempt-lineage-cardinality","attempt lineage must contain every predecessor exactly once",("review-retry","packet-repair","successor-cycle"))
 lineage_reviews=[]
 for index,ref in enumerate(lineage,1):
  lineage_path,issues=verify_artifact(ref,root,"attempt-lineage")
  if issues:return f("retry_lineage","attempt-lineage-invalid",issues[0].message,("review-retry","packet-repair","successor-cycle"))
  prior=read_json(lineage_path);lineage_reviews.append(prior)
  if prior.get("attempt_index")!=index or prior.get("case_id")!=v["case_id"] or prior.get("cycle_id")!=v["cycle_id"] or prior.get("review_protocol_id")!=v["review_protocol_id"]:return f("retry_lineage","attempt-lineage-order","attempt lineage indexes and identities must be contiguous",("review-retry","packet-repair","successor-cycle"))
  if prior.get("selection",{}).get("selected_for_final"):return f("review_shopping","prior-attempt-selected","a predecessor attempt cannot remain selected",("review-retry","packet-repair","successor-cycle"))
  prior_issues=validate_cold_review(lineage_path,root)
  if prior_issues:return f("retry_lineage","predecessor-semantic-invalid",f"predecessor attempt invalid: {prior_issues[0].failure_class}/{prior_issues[0].failure_subcode}",("review-retry","packet-repair","successor-cycle"))
 if v["attempt_index"]>1 and v["predecessor_review_attempt"].get("sha256")!=lineage[-1].get("sha256"):return f("retry_lineage","predecessor-not-latest","predecessor must be the latest complete lineage attempt",("review-retry","packet-repair","successor-cycle"))
 if v["attempt_index"]>1:
  pred_path,issues=verify_artifact(v["predecessor_review_attempt"],root,"predecessor-review")
  if issues:return f("retry_lineage","predecessor-invalid",issues[0].message,("review-retry","packet-repair","successor-cycle"))
  incident_path,issues=verify_artifact(cls["owner_incident_report"],root,"owner-incident")
  if issues:return f("retry_lineage","incident-invalid",issues[0].message,("review-retry","packet-repair","successor-cycle"))
  pred=read_json(pred_path)
  from check_review_incident_report import validate_incident_report
  incident_issues=validate_incident_report(incident_path,root)
  if incident_issues:return f("retry_lineage","incident-semantic-invalid",f"owner incident invalid: {incident_issues[0].failure_class}/{incident_issues[0].failure_subcode}",("review-retry","packet-repair","successor-cycle"))
  incident=read_json(incident_path)
  if incident.get("case_id")!=v["case_id"] or incident.get("cycle_id")!=v["cycle_id"] or incident.get("classified_attempt_id")!=pred.get("review_id") or incident.get("raw_output",{}).get("sha256")!=v["output"]["sha256"] or incident.get("packet",{}).get("sha256")!=pred.get("packet",{}).get("sha256") or incident.get("failure_class")!=cls.get("cause") or not incident.get("owner_notification",{}).get("notified_utc") or not incident.get("continuation_authority"):return f("retry_lineage","incident-binding","incident does not bind retry case/cycle/attempt/output/packet/cause/notification/authority",("review-retry","packet-repair","successor-cycle"))
  if pred.get("input",{}).get("sha256")!=v["input"]["sha256"] or pred.get("output",{}).get("sha256")!=v["output"]["sha256"]:return f("retry_lineage","input-output-changed","same-output retry changed input or output",("review-retry","packet-repair","successor-cycle"))
  cause=cls.get("cause")
  if cause in {"reviewer_transport","delivery_corruption","reviewer_policy_incompatibility"} and pred.get("packet",{}).get("sha256")!=v["packet"]["sha256"]:return f("retry_lineage","same-packet-changed","valid-packet transport retry must reuse the packet hash",("review-retry","packet-repair","successor-cycle"))
  if cause=="candidate_intelligibility":return f("review_classification","candidate-intelligibility-retried","candidate intelligibility requires a successor candidate",("review-retry","packet-repair","successor-cycle"))
 if cls and cls.get("candidate_intelligibility_observed") and (cls.get("cause")!="candidate_intelligibility" or not cls.get("product_andon")):return f("review_classification","candidate-intelligibility-mislabeled","candidate intelligibility is a product ANDON, not reviewer transport",("review-retry","packet-repair","successor-cycle"))
 replay=v["protocol_replay"]
 cohort_path,issues=verify_artifact(replay.get("cohort_manifest"),root,"cohort-manifest")
 if issues:return f("cohort_invalidation","cohort-manifest-invalid",issues[0].message)
 cohort=read_json(cohort_path);case_ids=cohort.get("case_ids",[])
 if cohort.get("schema")!="daee-cold-review-cohort-v1" or cohort.get("protocol_id")!=v["review_protocol_id"]:return f("cohort_invalidation","cohort-manifest-binding","cohort manifest must bind the review protocol")
 if not case_ids:return f("cohort_invalidation","empty-cohort","cohort case set cannot be empty")
 if len(case_ids)!=len(set(case_ids)):return f("cohort_invalidation","duplicate-cohort-case","cohort case IDs must be unique")
 if replay.get("change_scope")=="shared" and set(case_ids)!=set(replay.get("repeated_case_ids",[])):return f("cohort_invalidation","partial-cohort-retry","shared protocol change must repeat the independently bound entire cohort")
 if v["selection"].get("selection_basis")!="latest-valid-lineage":return f("review_shopping","favorable-selection","attempt selection must follow lineage, never favorability")
 packet_path=verified["packet"];packet=read_json(packet_path)
 packet_issues=validate_packet_manifest(packet_path,root,v["case_id"],v["cycle_id"],v["review_protocol_id"],v["input"]["sha256"],v["output"]["sha256"])
 if packet_issues:return packet_issues
 if packet.get("input",{}).get("sha256")!=v["input"]["sha256"] or packet.get("output",{}).get("sha256")!=v["output"]["sha256"]:return f("packet_binding","input-output-mismatch","review and packet input/output hashes differ")
 if v["attempt_index"]>1 and cls.get("cause")=="packet_insufficiency":
  pred=read_json(pred_path)
  if pred.get("packet",{}).get("sha256")==v["packet"]["sha256"]:return f("retry_lineage","rebuilt-packet-unchanged","packet repair requires a new packet hash",("review-retry","packet-repair","successor-cycle"))
  if packet.get("retry_mode")!="rebuilt-packet" or packet.get("predecessor_packet",{}).get("sha256")!=pred.get("packet",{}).get("sha256") or not all(packet.get(k) for k in ("packet_delta","builder_red_green_proof","anti_answer_bank_proof","review_authorization")):return f("retry_lineage","rebuilt-packet-proof-missing","rebuilt packet requires predecessor, delta, red/green, anti-bank, and authorization proof",("review-retry","packet-repair","successor-cycle"))
 return []
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--review",type=Path);p.add_argument("--custody-root",type=Path);p.add_argument("--explain",action="store_true");p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if a.self_test:return subprocess.run([sys.executable,str(ROOT/"tests/captured-output-custody/test_contract.py")],cwd=ROOT).returncode
 if not a.review:p.error("--review required")
 root=(a.custody_root or ROOT).resolve()
 try:path=resolve_repo_path(root,a.review,must_exist=True,expect_file=True)
 except PathCustodyError as exc:print(json.dumps({"checker_id":CHECKER_ID,"failure_class":"path_custody","failure_subcode":exc.subcode,"message":str(exc)},sort_keys=True));return 1
 fs=validate_cold_review(path,root)
 if fs:
  x=fs[0];print(json.dumps({"checker_id":CHECKER_ID,"manifest_path":str(path),"exit_category":"structural-rejection","exit_code":1,"earliest_stage":x.earliest_stage,"failure_class":x.failure_class,"failure_subcode":x.failure_subcode,"downstream_invalidated":list(x.downstream_invalidated),"message":x.message},sort_keys=True));return 1
 print(json.dumps({"checker_id":CHECKER_ID,"status":"PASS"},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
