#!/usr/bin/env python3
"""Deterministic Branch 10 protocol tests; no model runner is reachable here."""
from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_candidate_package_record as candidate  # noqa: E402
import campaign_usage_ledger as usage  # noqa: E402
import check_parallel_dispatch_manifest as barrier  # noqa: E402
import check_paired_cross_model_manifest as paired  # noqa: E402
import check_smoke_matrix_manifest as matrix  # noqa: E402
import check_case_registry_taint as registry_taint  # noqa: E402
import check_package_harness_parity as parity_contract  # noqa: E402
import build_smoke_matrix_verdict as verdict_builder  # noqa: E402
import run_five_smoke_matrix as five_runner  # noqa: E402
import run_paired_cross_model_matrix as paired_runner  # noqa: E402
import run_staged_current_skill_smoke as staged_harness  # noqa: E402
import smoke_matrix_registry as registry_contract  # noqa: E402
import validation_registry as validation_contract  # noqa: E402


FIXTURES = ROOT / "tests" / "smoke-matrix" / "fixtures"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


_FAKE_OPUS_UNSIGNED={"schema":"campaign-usage-fake-opus-child-authorization-v1","test_only":True,"parent_id":"paired-parent","parent_authorization_sha256":"1"*64,"candidate_id":"paired-parent-opus","cohort":"paired-producer","package_sha256":"d"*64,"archive_sha256":"a"*64,"extracted_tree_sha256":"b"*64,"registry_sha256":"e"*64,"model":"test-only-opus-exact","reasoning_effort":"high","protocol":"barrier-ten-submit-before-await-v1","settings":{"adapter":"never-reachable-fake"},"subject_ids":[f"subject-{index:02d}" for index in range(6,11)]}
FAKE_OPUS_CONTRACT={**_FAKE_OPUS_UNSIGNED,"authorization_sha256":canonical_sha256(_FAKE_OPUS_UNSIGNED)}


def fake_opus_contract(candidate_id: str) -> dict:
    unsigned={**_FAKE_OPUS_UNSIGNED,"parent_id":candidate_id,"candidate_id":f"{candidate_id}-opus"}
    return {**unsigned,"authorization_sha256":canonical_sha256(unsigned)}


def fake_paired_parent(candidate_id: str, subjects: list[str], cohort: str="paired-producer") -> dict:
    unsigned={"schema":"campaign-usage-fake-paired-parent-authorization-v1","test_only":True,"parent_id":candidate_id,"cohort":cohort,"gpt_candidate_id":f"{candidate_id}-gpt","opus_candidate_id":f"{candidate_id}-opus","package_sha256":"d"*64,"archive_sha256":"a"*64,"extracted_tree_sha256":"b"*64,"registry_sha256":"e"*64,"gpt_subject_ids":subjects[:5],"opus_subject_ids":subjects[5:]}
    return {**unsigned,"authorization_sha256":canonical_sha256(unsigned)}


def paired_authorization_kwargs(root: Path, parent_id: str, subjects: list[str], cohort: str="paired-producer", authorization_sha256: str|None=None) -> dict:
    root.mkdir(parents=True,exist_ok=True);auth=root/"fake-authorizations";auth.mkdir(exist_ok=True)
    shared={"source_commit":"6"*40,"package_sha256":"d"*64,"archive_sha256":"a"*64,"extracted_tree_sha256":"b"*64,"build_manifest_sha256":"7"*64,"registry_sha256":hashlib.sha256(registry_contract.DEFAULT_REGISTRY.read_bytes()).hexdigest()}
    common={"deterministic_fake_only":True,"live_execution_authorized":False,"parent_id":parent_id,**shared}
    outputs=[("c"*63+f"{index:x}") for index in range(1,11)] if cohort=="paired-review" else [None]*10;case_ids=[row["case_id"] for row in registry_contract.load_registry()["cases"]]
    gpt={"schema":"campaign-usage-fake-gpt-child-authorization-v1",**common,"child_cycle_id":f"{parent_id}-gpt-cycle","candidate_id":f"{parent_id}-gpt","candidate_record_sha256":"8"*64,"child_protocol_sha256":"9"*64,"subject_ids":subjects[:5],"case_ids":case_ids,"output_sha256s":outputs[:5]}
    opus={"schema":"campaign-usage-fake-opus-child-authorization-v1",**common,"child_cycle_id":f"{parent_id}-opus-cycle","candidate_id":f"{parent_id}-opus","candidate_record_sha256":"a"*64,"child_protocol_sha256":"b"*64,"subject_ids":subjects[5:],"case_ids":case_ids,"output_sha256s":outputs[5:],"model":"test-only-opus-exact","reasoning_effort":"high","protocol":"barrier-ten-submit-before-await-v1","settings":{"adapter":"never-reachable-fake"}}
    gpt_raw=canonical_bytes(gpt);opus_raw=canonical_bytes(opus);gpt_sha=hashlib.sha256(gpt_raw).hexdigest();opus_sha=hashlib.sha256(opus_raw).hexdigest()
    protocol_core={"schema":"campaign-usage-fake-paired-protocol-authorization-v1","deterministic_fake_only":True,"live_execution_authorized":False,"parent_id":parent_id,"cohort":cohort,**shared,"gpt_child_authorization_sha256":gpt_sha,"opus_child_authorization_sha256":opus_sha}
    outer={"schema":"campaign-usage-fake-outer-parent-authorization-v1","deterministic_fake_only":True,"live_execution_authorized":False,"parent_id":parent_id,"cohort":cohort,"paired_protocol_core_sha256":canonical_sha256(protocol_core),**shared,"gpt_child_authorization_sha256":gpt_sha,"opus_child_authorization_sha256":opus_sha,"gpt_candidate_id":gpt["candidate_id"],"opus_candidate_id":opus["candidate_id"],"gpt_candidate_record_sha256":gpt["candidate_record_sha256"],"opus_candidate_record_sha256":opus["candidate_record_sha256"],"gpt_child_cycle_id":gpt["child_cycle_id"],"opus_child_cycle_id":opus["child_cycle_id"],"gpt_child_protocol_sha256":gpt["child_protocol_sha256"],"opus_child_protocol_sha256":opus["child_protocol_sha256"],"gpt_subject_ids":gpt["subject_ids"],"opus_subject_ids":opus["subject_ids"],"gpt_case_ids":gpt["case_ids"],"opus_case_ids":opus["case_ids"],"gpt_output_sha256s":gpt["output_sha256s"],"opus_output_sha256s":opus["output_sha256s"]};outer_raw=canonical_bytes(outer);outer_sha=hashlib.sha256(outer_raw).hexdigest()
    protocol={**protocol_core,"outer_parent_authorization_sha256":outer_sha};protocol_raw=canonical_bytes(protocol);protocol_sha=hashlib.sha256(protocol_raw).hexdigest()
    paths=(auth/"outer.json",auth/"protocol.json",auth/"gpt.json",auth/"opus.json")
    for path,raw in zip(paths,(outer_raw,protocol_raw,gpt_raw,opus_raw)):path.write_bytes(raw)
    return {"authorization_sha256":outer_sha,"outer_parent_authorization_path":paths[0],"paired_protocol_authorization_path":paths[1],"paired_protocol_authorization_sha256":protocol_sha,"gpt_child_authorization_path":paths[2],"gpt_child_authorization_sha256":gpt_sha,"opus_child_authorization_path":paths[3],"opus_child_authorization_sha256":opus_sha}
REAL_USAGE_RESERVE=usage.reserve


def reserve_with_explicit_subjects(*args,**kwargs):
    if kwargs.get("call_subject_ids") is None:
        kwargs["call_subject_ids"]=[f"subject-{index:02d}" for index in range(1,kwargs["calls"]+1)]
    if kwargs.get("cohort") in {"paired-producer","paired-review"}:
        root=Path(args[0] if args else kwargs["root"]);kwargs.pop("paired_opus_contract",None);kwargs.pop("paired_parent_contract",None)
        kwargs.update(paired_authorization_kwargs(root,kwargs["candidate_id"],kwargs["call_subject_ids"],kwargs["cohort"]))
    return REAL_USAGE_RESERVE(*args,**kwargs)


usage.reserve=reserve_with_explicit_subjects


def provider_rows(candidate_id: str, batch_id: str, statuses: list[str], *, costs: list[str] | None=None, cohort: str="gpt-producer", subjects: list[str] | None=None, opus_model: str|None=None, opus_effort: str="high") -> list[dict]:
    costs=costs or [("0" if status=="NOT_DISPATCHED" else "unknown") for status in statuses]
    subjects=subjects or [f"subject-{index:02d}" for index in range(1,len(statuses)+1)]
    protocols={"gpt-producer":"barrier-five-submit-before-await-v1","paired-producer":"barrier-ten-submit-before-await-v1","gpt-review":"independent-cold-review-v1","paired-review":"paired-independent-cold-review-v1"}
    models=[];efforts=[];candidates=[]
    for index in range(1,len(statuses)+1):
        if cohort=="paired-producer" and index>len(statuses)//2:models.append(opus_model or "test-only-opus-exact");efforts.append(opus_effort)
        elif cohort in {"gpt-review","paired-review"}:models.append("gpt-5.6-sol");efforts.append("xhigh")
        else:models.append("gpt-5.5");efforts.append("high")
        candidates.append(f"{candidate_id}-gpt" if cohort in {"paired-producer","paired-review"} and index<=len(statuses)//2 else f"{candidate_id}-opus" if cohort in {"paired-producer","paired-review"} else candidate_id)
    case_ids=[row["case_id"] for row in registry_contract.load_registry()["cases"]]
    return [{"call_id":f"{batch_id}:call-{index:02d}","parent_id":candidate_id if cohort in {"paired-producer","paired-review"} else None,"child_cycle_id":f"{candidate_id}-gpt-cycle" if cohort in {"paired-producer","paired-review"} and index<=len(statuses)//2 else f"{candidate_id}-opus-cycle" if cohort in {"paired-producer","paired-review"} else None,"candidate_id":row_candidate,"child_protocol_sha256":"9"*64 if cohort in {"paired-producer","paired-review"} and index<=len(statuses)//2 else "b"*64 if cohort in {"paired-producer","paired-review"} else None,"cycle_or_review_batch_id":batch_id,"case_id":case_ids[(index-1)%5] if cohort in {"paired-producer","paired-review"} else None,"subject_id":subject,"subject_output_sha256":("c"*63+f"{index:x}") if cohort=="paired-review" else None,"model":model,"reasoning_effort":effort,"protocol":protocols[cohort],
             "started_at":"2026-07-10T12:00:00Z" if status in {"COMPLETED","FAILED","CANCELLED"} else None,
             "ended_at":"2026-07-10T12:00:01Z" if status in {"COMPLETED","FAILED","CANCELLED"} else None,
             "host_invocation_id":f"host-{batch_id}-{index:02d}" if status in {"COMPLETED","FAILED","CANCELLED"} else None,
             "accepted":True if status in {"COMPLETED","FAILED","CANCELLED"} else False if status=="NOT_DISPATCHED" else None,
             "in_flight":True if status in {"COMPLETED","FAILED","CANCELLED"} else False if status=="NOT_DISPATCHED" else None,
             "status":status,"unknown_kind":"DISPATCH_UNKNOWN" if status=="UNKNOWN" else None,"acknowledgment_origin":"BOTH" if status in {"COMPLETED","FAILED","CANCELLED"} else "NONE","terminal_transport_status":"COMPLETED" if status=="COMPLETED" else "FAILED" if status=="FAILED" else "CANCELLED" if status=="CANCELLED" else "NOT_STARTED" if status=="NOT_DISPATCHED" else "UNKNOWN",
             "provider_call_id":None if status in {"NOT_DISPATCHED","UNKNOWN"} else f"provider-{batch_id}-{index:02d}",
             "usage":{"status":"UNAVAILABLE"},"cost":{"unit":"usd","value":cost}}
            for index,(status,cost,subject,model,effort,row_candidate) in enumerate(zip(statuses,costs,subjects,models,efforts,candidates),1)]


def write_record(root: Path, relative: str, value: dict) -> dict[str, str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_bytes(value)
    path.write_bytes(raw)
    return {"path": relative.replace("\\", "/"), "sha256": __import__("hashlib").sha256(raw).hexdigest()}


def write_bytes_ref(root: Path, relative: str, raw: bytes) -> dict[str,str]:
    path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    return {"path":relative.replace("\\","/"),"sha256":hashlib.sha256(raw).hexdigest()}


def test_tree_sha256(root: Path) -> str:
    digest=hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()),key=lambda item:item.relative_to(root).as_posix()):
        relative=path.relative_to(root).as_posix().encode();digest.update(len(relative).to_bytes(4,"big"));digest.update(relative);digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def make_structural_near_positive(base: Path) -> tuple[Path,dict]:
    registry=registry_contract.load_registry();case_ids=[row["case_id"] for row in registry["cases"]]
    custody=base/"authorized-external-evidence";cycle=custody/"cycles"/"cycle-near";cycle.mkdir(parents=True)
    package_root=ROOT/"skill";parity=parity_contract.build_record(package_root,cycle,False);package_tree=parity["package_tree_sha256"]
    package_sha="d"*64;candidate_id="candidate-near";campaign_sha="c"*64
    candidate={"schema":"daee-smoke-matrix-v1","kind":"candidate-package-record","candidate_id":candidate_id,"status":"CONSUMED_OBSERVED","authorization_sha256":"b"*64,"claim_receipt_sha256":"e"*64,"archive_sha256":package_sha,"extracted_tree_sha256":package_tree,"predecessor_record_sha256":"1"*64,"root_creation":"CREATED","fallback_quarantine_path":None,"promotion_eligible":False}
    candidate["record_sha256"]=canonical_sha256(candidate);candidate_ref=write_record(cycle,"candidate-record.json",candidate)
    matrix_auth={"schema":"matrix-authorization-owner-boundary-v1","candidate_id":candidate_id,"candidate_package_record_sha256":candidate_ref["sha256"],"package_sha256":package_sha,"package_tree_sha256":package_tree}
    matrix_auth_ref=write_record(cycle,"matrix-authorization.json",matrix_auth);matrix_auth_sha=matrix_auth_ref["sha256"]
    ledger=cycle/"usage-ledger";reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256=campaign_sha,authorization_sha256=matrix_auth_sha,candidate_id=candidate_id,cycle_or_review_batch_id="cycle-near",call_subject_ids=case_ids)
    call_rows=provider_rows(candidate_id,"cycle-near",["COMPLETED"]*5,subjects=case_ids)
    settlement=usage.settle(ledger,reservation["transaction_sha256"],completed=5,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=call_rows,measured_cost={"unit":"usd","value":"unknown"},candidate_id=candidate_id,authorization_sha256=matrix_auth_sha)
    usage_ref={"path":f"usage-ledger/transactions/{settlement['transaction_sha256']}.json","sha256":settlement["transaction_sha256"]}
    dispatch_ref=write_record(cycle,"dispatch.json",five_runner.simulate_fake_cycle(["ok"]*5))
    claim={"schema":"cycle-claim-owner-boundary-v1","cycle_id":"cycle-near","matrix_authorization_sha256":matrix_auth_sha,"candidate_record_sha256":candidate_ref["sha256"]};claim_ref=write_record(cycle,"cycle-claim.json",claim)
    finalizer={"schema":"daee-smoke-matrix-v1","kind":"cycle-observation-finalizer","cycle_id":"cycle-near","cycle_claim_sha256":claim_ref["sha256"],"status":"FINALIZED","root_creation":"CREATED","dispatch_count":5,"usage_status":"SETTLED","candidate_status":"CONSUMED_OBSERVED","dispatch_manifest_sha256":dispatch_ref["sha256"],"usage_receipt_sha256":usage_ref["sha256"],"fallback_path":None}
    finalizer_ref=write_record(cycle,"observation-finalizer.json",finalizer)
    consumption={"schema":"candidate-consumption-owner-boundary-v1","cycle_id":"cycle-near","candidate_id":candidate_id,"candidate_status":"CONSUMED_OBSERVED","cycle_claim_sha256":claim_ref["sha256"],"candidate_record_sha256":candidate_ref["sha256"],"usage_receipt_sha256":usage_ref["sha256"],"dispatch_manifest_sha256":dispatch_ref["sha256"],"observation_finalizer_sha256":finalizer_ref["sha256"]};consumption_ref=write_record(cycle,"candidate-consumption.json",consumption)
    refs={"matrix_authorization":matrix_auth_ref,"ci_readback":write_record(cycle,"ci.json",{"schema":"ci-owner-boundary-v1","status":"PASS"}),"candidate_maturity":write_record(cycle,"maturity.json",{"schema":"maturity-owner-boundary-v1","status":"PASS"}),"dispatch_manifest":dispatch_ref,"candidate_record":candidate_ref,"cycle_claim":claim_ref,"candidate_consumption":consumption_ref,"usage_receipt":usage_ref,"observation_finalizer":finalizer_ref,"evidence_export":write_record(cycle,"evidence-export.json",{"schema":"evidence-export-owner-boundary-v1","status":"FINAL_PUBLISHED"}),"package_harness_parity":write_record(cycle,"package-parity.json",parity)}
    handoff_template=load(ROOT/"tests"/"staged-runtime-handshake"/"valid"/"source-order-basic.json")
    retained_output=(ROOT/"tests"/"retained-proof-corpus"/"v0.4.3.0-schema-light"/"valid"/"sidecar-backed"/"cases"/"a9-science-source"/"output.md").read_bytes()
    capsule_template=(ROOT/"tests"/"state-capsule-v2"/"valid"/"zero-selected-open-partial.json").read_bytes()
    cases=[]
    for row in registry["cases"]:
        case_id=row["case_id"];case_root=f"cases/{case_id}"
        output_ref=write_bytes_ref(cycle,f"{case_root}/output.md",retained_output)
        handoff=json.loads(json.dumps(handoff_template));handoff["case_id"]=case_id;handoff["stages"][6]["release_output"]={"path":"output.md","sha256":output_ref["sha256"]}
        handoff_ref=write_record(cycle,f"{case_root}/handoff.json",handoff)
        prompt={"schema":"daee-prompt-pack-manifest-v1","case_id":case_id,"stage":"stage-01-intake","call_index":1,"components":[{"name":"raw_input_text","bytes":4,"est_tok":1}],"total_bytes":4,"total_est_tok":1,"includes_full_runtime":False,"includes_prior_full_output":False}
        prompt_ref=write_bytes_ref(cycle,f"{case_root}/prompt.jsonl",canonical_bytes(prompt))
        capsule_dir=cycle/case_root/"state-capsules";capsule_dir.mkdir();(capsule_dir/"capsule-001.json").write_bytes(capsule_template)
        capsule_ref={"path":f"{case_root}/state-capsules","tree_sha256":test_tree_sha256(capsule_dir)}
        capture_ref=write_record(cycle,f"{case_root}/capture.json",{"schema":"a01-pre-review-capture-fixture-only-v1","status":"UNINTEGRATED_FIXTURE","case_id":case_id,"output_sha256":output_ref["sha256"]})
        promotion_ref=write_record(cycle,f"{case_root}/promotion.json",{"schema":"a11-promotion-fixture-only-v1","status":"UNINTEGRATED_FIXTURE","case_id":case_id,"output_sha256":output_ref["sha256"]})
        cases.append({"case_id":case_id,"input_sha256":row["raw_sha256"].lower(),"handoff_record":handoff_ref,"prompt_manifest":prompt_ref,"state_capsules":capsule_ref,"output":output_ref,"capture_manifest":capture_ref,"promotion_verdict":promotion_ref})
    manifest={"schema":"daee-structural-cycle-inventory-v1","cycle_id":"cycle-near","candidate_id":candidate_id,"source_commit":"a"*40,"package_sha256":package_sha,"package_tree_sha256":package_tree,"package_root":"skill","registry_sha256":hashlib.sha256(registry_contract.DEFAULT_REGISTRY.read_bytes()).hexdigest(),"campaign_authorization_sha256":campaign_sha,"matrix_authorization_sha256":matrix_auth_sha,"evidence_custody_root":str(custody.resolve()),"cycle_root":"cycles/cycle-near",**refs,"usage_ledger":{"path":"usage-ledger","tree_sha256":test_tree_sha256(ledger)},"cases":cases}
    (cycle/"cycle-manifest.json").write_bytes(canonical_bytes(manifest))
    return cycle,manifest


class FixtureProtocolTests(unittest.TestCase):
    def test_schema_first_rejects_unknown_missing_and_wrong_type_for_every_smoke_kind(self) -> None:
        representatives = {}
        for path in sorted((FIXTURES / "valid").glob("*.json")):
            data = load(path)
            if data.get("schema") == "daee-smoke-matrix-v1":
                representatives.setdefault(data["kind"], data)
        self.assertGreaterEqual(len(representatives), 10)
        for kind, data in representatives.items():
            with self.subTest(kind=kind, mutation="unknown"):
                errors = matrix.validate_manifest({**data, "__unknown__": True}, root=ROOT)
                self.assertTrue(errors)
                self.assertEqual("schema_contract", errors[0]["failure_class"])
            with self.subTest(kind=kind, mutation="missing"):
                malformed = dict(data); malformed.pop("schema")
                errors = matrix.validate_manifest(malformed, root=ROOT)
                self.assertTrue(errors)
                self.assertEqual("schema_contract", errors[0]["failure_class"])
            with self.subTest(kind=kind, mutation="type"):
                errors = matrix.validate_manifest({**data, "kind": 7}, root=ROOT)
                self.assertTrue(errors)
                self.assertEqual("schema_contract", errors[0]["failure_class"])

    def test_schema_first_rejects_malformed_paired_record_before_semantics(self) -> None:
        data = load(FIXTURES / "valid" / "paired-matching.json")
        malformed = {**data, "gpt_candidate": {**data["gpt_candidate"], "package_sha256": "not-a-hash"}}
        errors = matrix.validate_manifest(malformed, root=ROOT)
        self.assertTrue(errors)
        self.assertEqual("schema_contract", errors[0]["failure_class"])
        direct = paired.validate_paired_manifest(malformed)
        self.assertTrue(direct)
        self.assertEqual("schema_contract", direct[0]["failure_class"])

    def test_schema_first_has_one_strict_representative_for_every_smoke_kind(self) -> None:
        representatives = {}
        for path in sorted(FIXTURES.rglob("*.json")):
            if path.name.endswith(".expectation.json"):
                continue
            data = load(path)
            if data.get("schema") == "daee-smoke-matrix-v1" and not matrix._schema_errors(data):
                representatives.setdefault(data["kind"], data)
        registry=registry_contract.load_registry()
        ref={"path":"artifact.json","sha256":"a"*64};directory={"path":"state-capsules","tree_sha256":"b"*64}
        representatives["structural-pre-review-verdict"]={
            "schema":"daee-smoke-matrix-v1","kind":"structural-pre-review-verdict","matrix_id":"m",
            "structural_matrix_status":"PASS","completion_status":"PARTIAL","source_commit":"c"*40,
            "candidate_id":"candidate","package_sha256":"d"*64,"package_tree_sha256":"e"*64,
            "package_root":".daee/candidate-packages/candidate/extracted","campaign_authorization_sha256":"f"*64,
            "matrix_authorization_sha256":"a"*64,"registry":ref,"evidence_custody_root":"external-evidence",
            "cycle_root":"cycles/m","cycle_manifest":ref,"matrix_authorization":ref,"ci_readback":ref,
            "candidate_maturity":ref,"dispatch_manifest":ref,"candidate_record":ref,"cycle_claim":ref,
            "candidate_consumption":ref,"usage_ledger":directory,"usage_receipt":ref,"observation_finalizer":ref,"evidence_export":ref,
            "package_harness_parity":ref,
            "cases":[{"case_id":row["case_id"],"input_sha256":row["raw_sha256"].lower(),"handoff_record":ref,
                      "prompt_manifest":ref,"state_capsules":directory,"output":ref,"capture_manifest":ref,
                      "promotion_verdict":ref} for row in registry["cases"]],
            "non_claims":["structural PASS is not semantic truth","structural pre-review PASS cannot authorize cold review or final completion by itself"],
        }
        representatives["cycle-verdict"] = {"schema":"daee-smoke-matrix-v1","kind":"cycle-verdict","matrix_id":"m","structural_matrix_status":"PARTIAL","completion_status":"PARTIAL","reviews":[{} for _ in range(5)],"non_claims":["matrix PASS is not release or provenance proof"]}
        self.assertEqual(set(matrix.KIND_DEFS), set(representatives))
        for kind, data in representatives.items():
            with self.subTest(kind=kind):
                self.assertEqual([], matrix._schema_errors(data))
                self.assertEqual("schema_contract", matrix.validate_manifest({**data, "unknown_field": True}, root=ROOT)[0]["failure_class"])
                missing=dict(data);missing.pop("schema")
                self.assertEqual("schema_contract",matrix.validate_manifest(missing,root=ROOT)[0]["failure_class"])
                self.assertEqual("schema_contract",matrix.validate_manifest({**data,"kind":7},root=ROOT)[0]["failure_class"])

    def test_schema_hash_patterns_precede_semantics_where_hashes_exist(self) -> None:
        samples = [load(FIXTURES / "valid" / "parallel-five-call-usage-reservation-settled.json"),
                   load(FIXTURES / "valid" / "cycle-root-create-failure-with-fallback-finalizer.json"),
                   paired_runner.simulate_fake_paired_cycle(["ok"] * 5, ["ok"] * 5)]
        for data in samples:
            mutated = json.loads(json.dumps(data))
            if data.get("schema") == "daee-cross-model-paired-cycle-v1":
                mutated["gpt_candidate"]["archive_sha256"] = "bad"
            elif data["kind"] == "campaign-usage-receipt":
                mutated["predecessor_usage_head_sha256"] = "bad"
            else:
                mutated["cycle_claim_sha256"] = "bad"
            self.assertEqual("schema_contract", matrix.validate_manifest(mutated, root=ROOT)[0]["failure_class"])
    def test_plan14_named_fixture_families_are_present(self) -> None:
        required_valid = {
            "campaign-has-no-fixed-cycle-or-cumulative-call-ceiling.json",
            "cycle-root-create-failure-with-fallback-finalizer.json",
            "orphaned-reservation-recovery-without-reuse.json",
            "parallel-five-call-usage-reservation-settled.json",
            "partial-export-resume-hash-equal.json",
            "producer-green-review-fail-candidate-consumed-observed.json",
        }
        required_invalid = {
            "candidate-root-create-failure-without-fallback-quarantine.json",
            "failed-cycle-missing-observation-finalizer.json",
            "failed-cycle-usage-reservation-unsettled.json",
            "observation-finalizer-emits-reviewed-cycle-verdict.json",
            "parallel-worker-shared-home-cache.json",
            "partial-export-resume-hash-mismatch.json",
            "policy-label-manufactures-zero-dispatch.json",
            "provider-auth-failure-dispatches-later-calls.json",
            "reviewer-usage-counted-as-producer.json",
            "speculative-model-calls-avoided.json",
            "staging-manifest-offered-as-final.json",
            "usage-receipt-arithmetic-mismatch.json",
        }
        self.assertTrue(required_valid <= {p.name for p in (FIXTURES / "valid").glob("*.json")})
        self.assertTrue(required_invalid <= {p.name for p in (FIXTURES / "invalid").glob("*.json")})

    def test_every_invalid_fixture_has_canonical_plan11_expectation(self) -> None:
        for fixture in sorted((FIXTURES / "invalid").glob("*.json")):
            if fixture.name.endswith(".expectation.json"):
                continue
            with self.subTest(fixture=fixture.name):
                expectation = fixture.with_suffix(".expectation.json")
                self.assertTrue(expectation.is_file(), f"missing expectation for {fixture.name}")
                self.assertEqual([], matrix._expectation_shape_errors(load(expectation)))

    def test_diagnostic_pins_stable_failure_subcode(self) -> None:
        data = load(FIXTURES / "invalid" / "usage-receipt-arithmetic-mismatch.json")
        error = matrix.validate_manifest(data, root=ROOT)[0]
        diagnostic = matrix._diagnostic_record(data, error)
        self.assertEqual("usage_arithmetic", diagnostic["failure_subcode"])

    def test_registry_cli_matches_plan_14_manifest_and_emit_contract(self) -> None:
        registry = ROOT / "tests" / "smoke-matrix" / "v0.4.6.0-wip-five-smoke.json"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "smoke_matrix_registry.py"),
                "--manifest",
                str(registry),
                "--emit-cases-json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        rows = json.loads(result.stdout)
        self.assertEqual(5, len(rows))
        self.assertEqual(load(registry)["cases"], rows)

    def test_registry_identity_rejects_id_path_and_hash_metamorphs(self) -> None:
        canonical = load(registry_contract.DEFAULT_REGISTRY)
        mutations = []
        changed_id = json.loads(json.dumps(canonical)); changed_id["cases"][0]["case_id"] += "-changed"; mutations.append(changed_id)
        changed_path = json.loads(json.dumps(canonical)); changed_path["cases"][0]["input_path"] = changed_path["cases"][1]["input_path"]; mutations.append(changed_path)
        changed_hash = json.loads(json.dumps(canonical)); changed_hash["cases"][0]["raw_sha256"] = "0" * 64; mutations.append(changed_hash)
        for mutation in mutations:
            errors = registry_contract.validate_registry(mutation, ROOT)
            self.assertTrue(errors)
            self.assertEqual("registry_identity", errors[0]["failure_class"])

    def test_a14_consumers_reject_registry_and_prompt_text_metamorphs(self) -> None:
        canonical = load(registry_contract.DEFAULT_REGISTRY)
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            changed = json.loads(json.dumps(canonical)); changed["cases"][0]["case_id"] += "-changed"
            changed_path = temp / "changed-registry.json"; changed_path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "registry_identity"):
                five_runner.simulate_fake_cycle(["ok"] * 5, registry_path=changed_path)
            with self.assertRaisesRegex(ValueError, "registry_identity"):
                paired_runner.simulate_fake_paired_cycle(["ok"] * 5, ["ok"] * 5, registry_path=changed_path)
            mirror = temp / "mirror"
            for row in canonical["cases"]:
                source = ROOT / row["input_path"]
                target = mirror / row["input_path"]
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
            first = mirror / canonical["cases"][0]["input_path"]
            first.write_bytes(first.read_bytes() + b"metamorphic-change\n")
            with self.assertRaisesRegex(ValueError, "registry_input_(bytes|hash)"):
                five_runner.simulate_fake_cycle(["ok"] * 5, registry_root=mirror)

        report = registry_taint.run_taint_check(ROOT)
        self.assertEqual(0, report["exit_code"], report)
        self.assertEqual(
            ["registry_id", "input_path", "raw_sha256", "prompt_text"],
            report["a14_dimensions"],
        )
        self.assertEqual(
            ["route selection", "owner binding", "output selection"],
            report["a14_surfaces"],
        )
        self.assertEqual(["fake-five", "fake-paired"], report["a14_consumers"])
        self.assertEqual(8, report["a14_checks"])
        self.assertEqual(8, report["a14_rejections_before_manifest"])
        self.assertTrue(report["same_length_prompt_proven"])
        for result in report["a14_results"]:
            if result["dimension"] == "prompt_text":
                self.assertEqual(result["mutation_bytes_before"], result["mutation_bytes_after"])
        self.assertEqual(
            {
                "fake_consumers_only": True,
                "live_runtime_invoked": False,
                "manifest_returned_on_taint": False,
                "paired_output_interpreted": False,
            },
            report["execution_boundary"],
        )
        source = (ROOT / "tools" / "check_case_registry_taint.py").read_text(encoding="utf-8")
        canonical_ids = [row["case_id"] for row in registry_contract.load_registry()["cases"]]
        self.assertTrue(all(case_id not in source for case_id in canonical_ids))

    def test_valid_fixtures_pass(self) -> None:
        for path in sorted((FIXTURES / "valid").glob("*.json")):
            with self.subTest(path=path.name):
                self.assertEqual([], matrix.validate_manifest(load(path), root=ROOT))

    def test_invalid_fixtures_fail_for_expected_reason(self) -> None:
        for path in sorted((FIXTURES / "invalid").glob("*.json")):
            if path.name.endswith(".expectation.json"):
                continue
            expectation = load(path.with_suffix(".expectation.json"))
            with self.subTest(path=path.name):
                errors = matrix.validate_manifest(load(path), root=ROOT)
                self.assertTrue(errors, path.name)
                self.assertEqual(expectation["expected_failure_class"], errors[0]["failure_class"])

    def test_candidate_claim_dispatch_transitions_and_no_reuse(self) -> None:
        ready = {"kind": "candidate-package-record", "candidate_id": "c1", "status": "READY_UNUSED"}
        self.assertEqual("READY_UNUSED", candidate.derive_transition(ready, claimed=False, dispatch_count=None))
        self.assertEqual("CONSUMED_NO_DISPATCH", candidate.derive_transition(ready, claimed=True, dispatch_count=0))
        self.assertEqual("CONSUMED_OBSERVED", candidate.derive_transition(ready, claimed=True, dispatch_count=1))
        self.assertEqual("CONSUMED_DISPATCH_UNKNOWN", candidate.derive_transition(ready, claimed=True, dispatch_count=None))
        with self.assertRaisesRegex(ValueError, "terminal_candidate_reuse"):
            candidate.derive_transition({**ready, "status": "CONSUMED_OBSERVED"}, claimed=True, dispatch_count=0)

    def test_usage_exact_reservations_and_unknown_block(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td)
            campaign = "c" * 64
            initial = usage.head_snapshot(ledger)
            first = usage.reserve(ledger, cohort="gpt-producer", calls=5, expected_sequence=0, expected_head_sha256=initial["head_sha256"], campaign_authorization_sha256=campaign, authorization_sha256="a"*64, candidate_id="c1", cycle_or_review_batch_id="cycle1")
            usage.settle(ledger, first["transaction_sha256"], completed=5, failed=0, cancelled=0, not_dispatched=0, unknown=0, provider_usage_receipts=provider_rows("c1","cycle1",["COMPLETED"]*5), measured_cost={"unit":"usd","value":"unknown"}, candidate_id="c1", authorization_sha256="a"*64)
            after_first = usage.head_snapshot(ledger)
            with self.assertRaisesRegex(ValueError, "usage_head_conflict"):
                usage.reserve(ledger, cohort="gpt-review", calls=5, expected_sequence=2, expected_head_sha256="0" * 64, campaign_authorization_sha256=campaign, authorization_sha256="b"*64, candidate_id="c2", cycle_or_review_batch_id="review1")
            second = usage.reserve(ledger, cohort="paired-producer", calls=10, expected_sequence=2, expected_head_sha256=after_first["head_sha256"], campaign_authorization_sha256=campaign, authorization_sha256="b"*64, candidate_id="c2", cycle_or_review_batch_id="cycle2",paired_opus_contract=fake_opus_contract("c2"))
            usage.settle(ledger, second["transaction_sha256"], completed=9, failed=0, cancelled=0, not_dispatched=0, unknown=1, provider_usage_receipts=provider_rows("c2","cycle2",["COMPLETED"]*9+["UNKNOWN"],cohort="paired-producer"), measured_cost={"unit":"usd","value":"unknown"}, candidate_id="c2", authorization_sha256=second["authorization_sha256"])
            with self.assertRaisesRegex(ValueError, "unresolved_usage"):
                usage.reserve(ledger, cohort="gpt-review", calls=5, expected_sequence=4, expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"], campaign_authorization_sha256=campaign, authorization_sha256="d"*64, candidate_id="c3", cycle_or_review_batch_id="review2")

    def test_usage_rejects_reservation_mutated_from_five_calls_to_one(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td)
            initial = usage.head_snapshot(ledger)
            reservation = usage.reserve(
                ledger,
                cohort="gpt-producer",
                calls=5,
                expected_sequence=0,
                expected_head_sha256=initial["head_sha256"],
                campaign_authorization_sha256="c" * 64,
                authorization_sha256="a" * 64,
                candidate_id="candidate-mutated",
                cycle_or_review_batch_id="cycle-mutated",
            )
            transaction_path = ledger / "transactions" / f"{reservation['transaction_sha256']}.json"
            mutated = json.loads(transaction_path.read_text(encoding="utf-8"))
            mutated["reserved_calls"] = 1
            transaction_path.write_bytes(canonical_bytes(mutated))
            with self.assertRaisesRegex(ValueError, "usage_transaction_content_address"):
                usage.settle(
                    ledger,
                    reservation["transaction_sha256"],
                    completed=1,
                    failed=0,
                    cancelled=0,
                    not_dispatched=0,
                    unknown=0,
                    candidate_id="candidate-mutated",
                    authorization_sha256="a" * 64,
                )

    def test_usage_requires_campaign_and_child_identity_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td)
            initial = usage.head_snapshot(ledger)
            with self.assertRaisesRegex(ValueError, "campaign_authorization_required"):
                usage.reserve(
                    ledger, cohort="gpt-producer", calls=5, expected_sequence=0,
                    expected_head_sha256=initial["head_sha256"],
                )

    def test_usage_chain_rejects_head_mutation_fork_gap_reorder_and_cross_binding(self) -> None:
        bindings = {
            "campaign_authorization_sha256": "c" * 64,
            "authorization_sha256": "a" * 64,
            "candidate_id": "candidate-usage-1",
            "cycle_or_review_batch_id": "cycle-usage-1",
        }
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td)
            first = usage.reserve(
                ledger, cohort="gpt-producer", calls=5, expected_sequence=0,
                expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"], **bindings,
            )
            head_path = ledger / "head.json"
            original_head = head_path.read_bytes()
            head = json.loads(original_head)
            head["totals"]["producer_invocations"] = 99
            head_path.write_bytes(canonical_bytes(head))
            with self.assertRaisesRegex(ValueError, "usage_head_chain"):
                usage.head_snapshot(ledger)
            head_path.write_bytes(original_head)

            reservation_path = ledger / "transactions" / f"{first['transaction_sha256']}.json"
            reservation = json.loads(reservation_path.read_text(encoding="utf-8"))
            fork = {**reservation, "authorization_sha256": "b" * 64}
            fork_sha = canonical_sha256(fork)
            (ledger / "transactions" / f"{fork_sha}.json").write_bytes(canonical_bytes(fork))
            self.assertEqual(first["transaction_sha256"],usage.head_snapshot(ledger)["last_transaction_sha256"])
            (ledger / "transactions" / f"{fork_sha}.json").unlink()

            reordered = {**reservation, "sequence": 2}
            reordered_sha = canonical_sha256(reordered)
            reordered_path = ledger / "transactions" / f"{reordered_sha}.json"
            reordered_path.write_bytes(canonical_bytes(reordered))
            head = json.loads(original_head)
            head["last_transaction_sha256"] = reordered_sha
            head["open_reservations"] = [reordered_sha]
            head_path.write_bytes(canonical_bytes(head))
            reservation_path.unlink()
            with self.assertRaisesRegex(ValueError, "usage_chain_(gap|sequence)"):
                usage.head_snapshot(ledger)

    def test_usage_post_write_head_readback_fault_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "head.json"
            with mock.patch.object(Path, "read_bytes", return_value=b"faulted-readback"):
                with self.assertRaisesRegex(ValueError, "usage_head_readback"):
                    usage._atomic_write(path, usage._initial())

    def test_usage_append_before_head_residue_is_retained_and_retry_can_advance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);initial=usage.head_snapshot(ledger);real_write=usage._atomic_write
            with mock.patch.object(usage,"_atomic_write",side_effect=ValueError("usage_head_readback: injected replace failure")):
                with self.assertRaisesRegex(ValueError,"usage_head_readback"):
                    usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=initial["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="residue-a",cycle_or_review_batch_id="cycle-a")
            residues=list((ledger/"transactions").glob("*.json"));self.assertEqual(1,len(residues))
            with mock.patch.object(usage,"_atomic_write",side_effect=real_write):
                retried=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=initial["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="b"*64,candidate_id="residue-b",cycle_or_review_batch_id="cycle-b")
            self.assertEqual(retried["transaction_sha256"],usage.validate_head(ledger)["last_transaction_sha256"])
            self.assertEqual(2,len(list((ledger/"transactions").glob("*.json"))),"valid unreachable residue must be preserved")

    def test_usage_terminal_transactions_are_content_address_checked(self) -> None:
        for terminal in ("settlement","orphan-recovery"):
            with self.subTest(terminal=terminal),tempfile.TemporaryDirectory() as td:
                ledger=Path(td);campaign="c"*64;candidate=f"candidate-{terminal}"
                reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256=campaign,authorization_sha256="a"*64,candidate_id=candidate,cycle_or_review_batch_id=f"cycle-{terminal}")
                if terminal=="settlement":
                    result=usage.settle(ledger,reservation["transaction_sha256"],completed=5,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=provider_rows(candidate,f"cycle-{terminal}",["COMPLETED"]*5),measured_cost={"unit":"usd","value":"unknown"},candidate_id=candidate,authorization_sha256="a"*64)
                else:
                    authorization={"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":"terminal-tamper","campaign_authorization_sha256":campaign,"authorization_sha256":"a"*64,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"orphan","candidate_id":candidate,"expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":"claims/terminal-tamper.json","dispatch_provider_evidence_path":None,"dispatch_provider_evidence_sha256":None}
                    auth=ledger/"auth.json";auth.write_text(json.dumps(authorization),encoding="utf-8")
                    result=usage.recover_orphan(ledger,reservation["transaction_sha256"],recovery_authorization=auth,orphan_id="orphan",candidate_id=candidate,completed=0,failed=0,cancelled=0,not_dispatched=5,unknown=0)
                path=ledger/"transactions"/f"{result['transaction_sha256']}.json";mutated=load(path);mutated["candidate_id"]="retained-status-wrong-binding";path.write_bytes(canonical_bytes(mutated))
                with self.assertRaisesRegex(ValueError,"usage_transaction_content_address"):usage.validate_head(ledger)

    def test_usage_correctly_readdressed_terminal_binding_fault_rejects_before_replay(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="binding-candidate",cycle_or_review_batch_id="binding-cycle")
            settlement=usage.settle(ledger,reservation["transaction_sha256"],completed=5,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=provider_rows("binding-candidate","binding-cycle",["COMPLETED"]*5),measured_cost={"unit":"usd","value":"unknown"},candidate_id="binding-candidate",authorization_sha256="a"*64)
            original=load(ledger/"transactions"/f"{settlement['transaction_sha256']}.json")
            malformed={**original,"reservation_transaction_sha256":[]}
            malformed_sha=canonical_sha256(malformed)
            (ledger/"transactions"/f"{malformed_sha}.json").write_bytes(canonical_bytes(malformed))
            with self.assertRaisesRegex(ValueError,"usage_binding"):
                usage.validate_head(ledger)

    def test_usage_head_rejects_boolean_and_malformed_scalar_shapes(self) -> None:
        mutations={"sequence":False,"campaign_authorization_sha256":7,"last_transaction_sha256":[],"open_reservations":"not-a-list","unresolved_usage":0}
        for field,value in mutations.items():
            with self.subTest(field=field),tempfile.TemporaryDirectory() as td:
                ledger=Path(td);path=ledger/"head.json";head={"schema":"campaign-usage-head-v1","sequence":0,"campaign_authorization_sha256":None,"last_transaction_sha256":None,"unresolved_usage":False,"open_reservations":[],"totals":{"attempted":0,"completed":0,"failed":0,"cancelled":0,"not_dispatched":0,"unknown":0,"producer_invocations":0,"cold_review_invocations":0},"measured_cost":{"unit":"usd","value":"0"}};head[field]=value;path.write_bytes(canonical_bytes(head))
                with self.assertRaisesRegex(ValueError,"usage_head_shape|usage_binding"):usage.validate_head(ledger)
        for primitive in ([],7):
            with self.subTest(primitive=primitive),tempfile.TemporaryDirectory() as td:
                ledger=Path(td);(ledger/"head.json").write_bytes(canonical_bytes(primitive))
                with self.assertRaisesRegex(ValueError,"usage_head_shape"):usage.validate_head(ledger)

    def test_usage_rejects_boolean_counts_and_totals(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td)
            bindings = {"campaign_authorization_sha256":"c"*64,"authorization_sha256":"a"*64,"candidate_id":"bool-candidate","cycle_or_review_batch_id":"bool-cycle"}
            reservation = usage.reserve(ledger, cohort="gpt-producer", calls=5, expected_sequence=0, expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"], **bindings)
            with self.assertRaisesRegex(ValueError, "usage_arithmetic"):
                usage.settle(ledger, reservation["transaction_sha256"], completed=True, failed=0, cancelled=0, not_dispatched=4, unknown=0, candidate_id="bool-candidate", authorization_sha256="a"*64)
            head_path=ledger/"head.json";head=load(head_path);head["totals"]["attempted"]=False;head_path.write_bytes(canonical_bytes(head))
            with self.assertRaisesRegex(ValueError, "usage_head_shape"):
                usage.head_snapshot(ledger)

    def test_usage_settlement_replay_and_cross_candidate_binding_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td)
            bindings = {
                "campaign_authorization_sha256": "c" * 64,
                "authorization_sha256": "a" * 64,
                "candidate_id": "candidate-usage-2",
                "cycle_or_review_batch_id": "cycle-usage-2",
            }
            reservation = usage.reserve(
                ledger, cohort="gpt-producer", calls=5, expected_sequence=0,
                expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"], **bindings,
            )
            with self.assertRaisesRegex(ValueError, "usage_binding"):
                usage.settle(
                    ledger, reservation["transaction_sha256"], completed=5, failed=0,
                    cancelled=0, not_dispatched=0, unknown=0,
                    candidate_id="different-candidate",
                    authorization_sha256=bindings["authorization_sha256"],
                )
            usage.settle(
                ledger, reservation["transaction_sha256"], completed=5, failed=0,
                cancelled=0, not_dispatched=0, unknown=0,
                provider_usage_receipts=provider_rows(bindings["candidate_id"],bindings["cycle_or_review_batch_id"],["COMPLETED"]*5),
                measured_cost={"unit":"usd","value":"unknown"},
                candidate_id=bindings["candidate_id"],
                authorization_sha256=bindings["authorization_sha256"],
            )
            with self.assertRaisesRegex(ValueError, "usage_(head_conflict|reservation_replay)"):
                usage.settle(
                    ledger, reservation["transaction_sha256"], completed=5, failed=0,
                    cancelled=0, not_dispatched=0, unknown=0,
                    candidate_id=bindings["candidate_id"],
                    authorization_sha256=bindings["authorization_sha256"],
                )

    def test_orphan_recovery_requires_bound_artifact_and_consumes_it_once(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td); campaign = "c" * 64; candidate_id = "candidate-1"; orphan_id = "orphan-1"
            initial = usage.head_snapshot(ledger)
            reservation = usage.reserve(ledger, cohort="gpt-producer", calls=5, expected_sequence=0, expected_head_sha256=initial["head_sha256"], campaign_authorization_sha256=campaign, authorization_sha256="a"*64, candidate_id=candidate_id, cycle_or_review_batch_id="cycle-1")
            authorization = {
                "schema": "campaign-usage-recovery-authorization-v1", "kind": "orphan-recovery-authorization",
                "authorization_id": "recovery-1", "campaign_authorization_sha256": campaign,
                "authorization_sha256": "a" * 64,
                "reservation_sha256": reservation["transaction_sha256"], "orphan_id": orphan_id,
                "candidate_id": candidate_id, "expected_usage_head_sha256": usage.head_snapshot(ledger)["head_sha256"],
                "claim_path": "claims/recovery-1.json", "dispatch_provider_evidence_path":None, "dispatch_provider_evidence_sha256":None,
            }
            auth_path = ledger / "recovery-authorization.json"; auth_path.write_text(json.dumps(authorization), encoding="utf-8")
            recovered = usage.recover_orphan(ledger, reservation["transaction_sha256"], recovery_authorization=auth_path,
                                             orphan_id=orphan_id, candidate_id=candidate_id,
                                             completed=0, failed=0, cancelled=0, not_dispatched=0, unknown=5)
            self.assertEqual("orphan-recovery", recovered["kind"])
            self.assertEqual(64, len(recovered["recovery_authorization_sha256"]))
            with self.assertRaisesRegex(ValueError, "recovery_authorization_replay"):
                usage.recover_orphan(ledger, reservation["transaction_sha256"], recovery_authorization=auth_path,
                                     orphan_id=orphan_id, candidate_id=candidate_id,
                                     completed=0, failed=0, cancelled=0, not_dispatched=5, unknown=0)

    def test_orphan_recovery_rejects_binding_mismatch_before_claim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td); campaign = "c" * 64
            initial = usage.head_snapshot(ledger)
            reservation = usage.reserve(ledger, cohort="gpt-producer", calls=5, expected_sequence=0, expected_head_sha256=initial["head_sha256"], campaign_authorization_sha256=campaign, authorization_sha256="a"*64, candidate_id="c1", cycle_or_review_batch_id="cycle-2")
            authorization = {"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":"recovery-2","campaign_authorization_sha256":campaign,"authorization_sha256":"a"*64,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"o1","candidate_id":"c1","expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":"claims/recovery-2.json","dispatch_provider_evidence_path":None,"dispatch_provider_evidence_sha256":None}
            auth_path=ledger/"auth.json";auth_path.write_text(json.dumps(authorization),encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "recovery_authorization_binding"):
                usage.recover_orphan(ledger,reservation["transaction_sha256"],recovery_authorization=auth_path,orphan_id="different",candidate_id="c1",completed=0,failed=0,cancelled=0,not_dispatched=5,unknown=0)
            self.assertFalse((ledger/"claims/recovery-2.json").exists())

    def test_orphan_recovery_corrupt_reservation_does_not_consume_claim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);campaign="c"*64;authorization_sha="a"*64;candidate="corrupt-candidate"
            reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256=campaign,authorization_sha256=authorization_sha,candidate_id=candidate,cycle_or_review_batch_id="corrupt-cycle")
            auth_data={"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":"corrupt-recovery","campaign_authorization_sha256":campaign,"authorization_sha256":authorization_sha,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"orphan","candidate_id":candidate,"expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":"claims/corrupt-recovery.json","dispatch_provider_evidence_path":None,"dispatch_provider_evidence_sha256":None}
            auth=ledger/"auth.json";auth.write_text(json.dumps(auth_data),encoding="utf-8")
            transaction=ledger/"transactions"/f"{reservation['transaction_sha256']}.json";mutated=load(transaction);mutated["reserved_calls"]=1;transaction.write_bytes(canonical_bytes(mutated))
            with self.assertRaisesRegex(ValueError,"usage_transaction_content_address"):
                usage.recover_orphan(ledger,reservation["transaction_sha256"],recovery_authorization=auth,orphan_id="orphan",candidate_id=candidate,completed=0,failed=0,cancelled=0,not_dispatched=5,unknown=0)
            self.assertFalse((ledger/"claims/corrupt-recovery.json").exists())

    def test_orphan_recovery_claim_race_has_one_winner(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);campaign="c"*64;head=usage.head_snapshot(ledger)
            reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=head["head_sha256"],campaign_authorization_sha256=campaign,authorization_sha256="a"*64,candidate_id="c",cycle_or_review_batch_id="cycle-race")
            authorization={"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":"race","campaign_authorization_sha256":campaign,"authorization_sha256":"a"*64,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"o","candidate_id":"c","expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":"claims/race.json","dispatch_provider_evidence_path":None,"dispatch_provider_evidence_sha256":None}
            auth=ledger/"auth.json";auth.write_text(json.dumps(authorization),encoding="utf-8")
            def attempt():
                try:
                    usage.recover_orphan(ledger,reservation["transaction_sha256"],recovery_authorization=auth,orphan_id="o",candidate_id="c",completed=0,failed=0,cancelled=0,not_dispatched=5,unknown=0)
                    return "won"
                except ValueError as exc:
                    return str(exc).split(":",1)[0]
            with ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(lambda _:attempt(),range(2)))
            self.assertEqual(1,outcomes.count("won"))
            self.assertEqual(1,outcomes.count("usage_head_conflict"), outcomes)

    def test_orphan_recovery_without_dispatch_evidence_forces_unknown_and_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);campaign="c"*64;candidate="no-evidence-candidate"
            reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256=campaign,authorization_sha256="a"*64,candidate_id=candidate,cycle_or_review_batch_id="no-evidence-cycle")
            authorization={"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":"no-evidence","campaign_authorization_sha256":campaign,"authorization_sha256":"a"*64,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"orphan","candidate_id":candidate,"expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":"claims/no-evidence.json","dispatch_provider_evidence_path":None,"dispatch_provider_evidence_sha256":None}
            auth=ledger/"authorization.json";auth.write_text(json.dumps(authorization),encoding="utf-8")
            recovered=usage.recover_orphan(ledger,reservation["transaction_sha256"],recovery_authorization=auth,orphan_id="orphan",candidate_id=candidate,completed=0,failed=0,cancelled=0,not_dispatched=5,unknown=0)
            self.assertEqual(5,recovered["unknown"],"caller counts cannot manufacture proved-zero dispatch")
            self.assertEqual(0,recovered["not_dispatched"])
            self.assertTrue(usage.head_snapshot(ledger)["unresolved_usage"])
            with self.assertRaisesRegex(ValueError,"unresolved_usage"):
                usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=2,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256=campaign,authorization_sha256="b"*64,candidate_id="next",cycle_or_review_batch_id="next-cycle")

    def test_orphan_recovery_derives_proved_zero_or_unknown_from_bound_evidence(self) -> None:
        for classification,statuses,expected_unknown in (("proved-zero",["NOT_DISPATCHED"]*5,False),("unknown",["UNKNOWN"]*5,True)):
            with self.subTest(classification=classification),tempfile.TemporaryDirectory() as td:
                ledger=Path(td);campaign="c"*64;candidate=f"{classification}-candidate";batch=f"{classification}-cycle"
                reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256=campaign,authorization_sha256="a"*64,candidate_id=candidate,cycle_or_review_batch_id=batch)
                evidence={"schema":"campaign-usage-dispatch-provider-evidence-v1","reservation_sha256":reservation["transaction_sha256"],"campaign_authorization_sha256":campaign,"authorization_sha256":"a"*64,"candidate_id":candidate,"cycle_or_review_batch_id":batch,"rows":provider_rows(candidate,batch,statuses)}
                evidence_path=ledger/"evidence.json";evidence_path.write_bytes(canonical_bytes(evidence));evidence_sha=hashlib.sha256(evidence_path.read_bytes()).hexdigest()
                authorization={"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":classification,"campaign_authorization_sha256":campaign,"authorization_sha256":"a"*64,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"orphan","candidate_id":candidate,"expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":f"claims/{classification}.json","dispatch_provider_evidence_path":"evidence.json","dispatch_provider_evidence_sha256":evidence_sha}
                auth=ledger/"authorization.json";auth.write_text(json.dumps(authorization),encoding="utf-8")
                caller={"completed":0,"failed":0,"cancelled":0,"not_dispatched":5 if classification=="proved-zero" else 0,"unknown":5 if classification=="unknown" else 0}
                recovered=usage.recover_orphan(ledger,reservation["transaction_sha256"],recovery_authorization=auth,orphan_id="orphan",candidate_id=candidate,**caller)
                self.assertEqual(5,recovered["not_dispatched"] if classification=="proved-zero" else recovered["unknown"])
                self.assertEqual(evidence_sha,recovered["dispatch_provider_evidence_sha256"])
                self.assertEqual(expected_unknown,usage.head_snapshot(ledger)["unresolved_usage"])

    def test_usage_invalid_unreachable_terminal_residue_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="dag-candidate",cycle_or_review_batch_id="dag-cycle")
            valid=load(ledger/"transactions"/f"{reservation['transaction_sha256']}.json")
            invalid={"schema":"campaign-usage-transaction-v1","kind":"settlement","sequence":2,"predecessor_usage_head_sha256":"0"*64,"predecessor_transaction_sha256":reservation["transaction_sha256"],"campaign_authorization_sha256":"c"*64,"authorization_sha256":"a"*64,"candidate_id":"dag-candidate","cycle_or_review_batch_id":"dag-cycle","cohort":"gpt-producer","lane":"producer","call_contract":valid["call_contract"],"paired_opus_contract":None,"paired_parent_contract":None,"authorization_custody":[],"reservation_transaction_sha256":reservation["transaction_sha256"],"reserved_calls":5,"attempted":5,"accepted":5,"in_flight":5,"completed":5,"failed":0,"cancelled":0,"not_dispatched":0,"unknown":0,"provider_usage_receipts":provider_rows("dag-candidate","dag-cycle",["COMPLETED"]*5),"measured_cost":{"unit":"usd","value":"unknown"}}
            invalid_sha=canonical_sha256(invalid);(ledger/"transactions"/f"{invalid_sha}.json").write_bytes(canonical_bytes(invalid))
            self.assertEqual(valid["sequence"],1)
            with self.assertRaisesRegex(ValueError,"usage_chain_predecessor"):usage.validate_head(ledger)

    def test_usage_invalid_metadata_is_rejected_before_append_or_head_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="metadata-candidate",cycle_or_review_batch_id="metadata-cycle")
            before_head=(ledger/"head.json").read_bytes();before_inventory=sorted(path.name for path in (ledger/"transactions").glob("*.json"))
            with self.assertRaisesRegex(ValueError,"usage_transaction_shape|usage_provider_metadata"):
                usage.settle(ledger,reservation["transaction_sha256"],completed=5,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=provider_rows("metadata-candidate","metadata-cycle",["COMPLETED"]*5),measured_cost={"unit":"usd","value":"0","extra":"forbidden"},candidate_id="metadata-candidate",authorization_sha256="a"*64)
            self.assertEqual(before_head,(ledger/"head.json").read_bytes())
            self.assertEqual(before_inventory,sorted(path.name for path in (ledger/"transactions").glob("*.json")))

    def test_usage_completed_calls_require_factual_per_call_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="provider-candidate",cycle_or_review_batch_id="provider-cycle")
            before=usage.head_snapshot(ledger)
            with self.assertRaisesRegex(ValueError,"usage_provider_metadata"):
                usage.settle(ledger,reservation["transaction_sha256"],completed=5,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=[],measured_cost={"unit":"usd","value":"unknown"},candidate_id="provider-candidate",authorization_sha256="a"*64)
            self.assertEqual(before,usage.head_snapshot(ledger))

    def test_orphan_recovery_non_text_claim_path_is_stable_invalid_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="claim-candidate",cycle_or_review_batch_id="claim-cycle")
            authorization={"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":"bad-claim","campaign_authorization_sha256":"c"*64,"authorization_sha256":"a"*64,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"orphan","candidate_id":"claim-candidate","expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":[],"dispatch_provider_evidence_path":None,"dispatch_provider_evidence_sha256":None}
            auth=ledger/"authorization.json";auth.write_text(json.dumps(authorization),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"recovery_authorization_invalid"):
                usage.recover_orphan(ledger,reservation["transaction_sha256"],recovery_authorization=auth,orphan_id="orphan",candidate_id="claim-candidate",completed=0,failed=0,cancelled=0,not_dispatched=0,unknown=5)

    def test_usage_settlement_keeps_lane_and_provider_metadata_factual(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td)
            initial = usage.head_snapshot(ledger)
            reservation = usage.reserve(ledger, cohort="gpt-review", calls=5, expected_sequence=0, expected_head_sha256=initial["head_sha256"], campaign_authorization_sha256="c"*64, authorization_sha256="a"*64, candidate_id="candidate-review", cycle_or_review_batch_id="review-batch")
            rows=provider_rows("candidate-review","review-batch",["COMPLETED"]*5,costs=["0.10"]*5,cohort="gpt-review")
            receipt = usage.settle(ledger, reservation["transaction_sha256"], completed=5, failed=0, cancelled=0, not_dispatched=0, unknown=0,
                                   provider_usage_receipts=rows, measured_cost={"unit": "usd", "value": "0.5"}, candidate_id="candidate-review", authorization_sha256="a"*64)
            self.assertEqual("gpt-review", receipt["cohort"])
            self.assertEqual("provider-review-batch-01", receipt["provider_usage_receipts"][0]["provider_call_id"])
            head=usage.head_snapshot(ledger);totals=head["totals"]
            self.assertEqual(0, totals["producer_invocations"])
            self.assertEqual(5, totals["cold_review_invocations"])
            self.assertEqual({"unit":"usd","value":"0.5"},head["measured_cost"])

    def test_usage_paired_contract_accepts_exact_five_plus_five_and_rejects_model_effort_subject_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);reservation=usage.reserve(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="paired-candidate",cycle_or_review_batch_id="paired-batch",paired_opus_contract=FAKE_OPUS_CONTRACT)
            rows=provider_rows("paired-candidate","paired-batch",["COMPLETED"]*10,cohort="paired-producer")
            self.assertEqual(["gpt-5.5"]*5+["test-only-opus-exact"]*5,[row["model"] for row in rows])
            canonical_cases=[row["case_id"] for row in registry_contract.load_registry()["cases"]]
            self.assertEqual(canonical_cases*2,[row["case_id"] for row in reservation["call_contract"]]);self.assertEqual(["paired-candidate-gpt"]*5+["paired-candidate-opus"]*5,[row["candidate_id"] for row in reservation["call_contract"]])
            self.assertEqual({"paired-candidate"},{row["parent_id"] for row in reservation["call_contract"]});self.assertEqual(2,len({row["child_cycle_id"] for row in reservation["call_contract"]}))
            for field,value in (("model","arbitrary-model"),("reasoning_effort","low"),("subject_id","substituted-subject"),("protocol","wrong-protocol"),("started_at","not-a-time"),("accepted",False)):
                with self.subTest(field=field):
                    mutated=json.loads(json.dumps(rows));mutated[0][field]=value
                    with self.assertRaisesRegex(ValueError,"usage_provider_metadata"):
                        usage.settle(ledger,reservation["transaction_sha256"],completed=10,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=mutated,measured_cost={"unit":"usd","value":"unknown"},candidate_id="paired-candidate",authorization_sha256=reservation["authorization_sha256"])
            receipt=usage.settle(ledger,reservation["transaction_sha256"],completed=10,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=rows,measured_cost={"unit":"usd","value":"unknown"},candidate_id="paired-candidate",authorization_sha256=reservation["authorization_sha256"])
            self.assertEqual(10,receipt["attempted"])

    def test_usage_paired_review_contract_is_ten_isolated_gpt56_xhigh_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"gpt-output-{index}" for index in range(5)]+[f"opus-output-{index}" for index in range(5)]
            reservation=usage.reserve(ledger,cohort="paired-review",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="paired-review-candidate",cycle_or_review_batch_id="paired-review-batch",call_subject_ids=subjects)
            rows=provider_rows("paired-review-candidate","paired-review-batch",["COMPLETED"]*10,cohort="paired-review",subjects=subjects)
            self.assertEqual({"gpt-5.6-sol"},{row["model"] for row in rows});self.assertEqual({"xhigh"},{row["reasoning_effort"] for row in rows})
            self.assertEqual(["paired-review-candidate-gpt"]*5+["paired-review-candidate-opus"]*5,[row["candidate_id"] for row in rows])
            self.assertEqual(subjects,[row["subject_id"] for row in rows]);self.assertEqual(10,len({row["subject_output_sha256"] for row in rows}))
            receipt=usage.settle(ledger,reservation["transaction_sha256"],completed=10,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=rows,measured_cost={"unit":"usd","value":"unknown"},candidate_id="paired-review-candidate",authorization_sha256=reservation["authorization_sha256"])
            self.assertEqual("paired-review",receipt["cohort"])

    def test_usage_unknown_without_dispatch_evidence_does_not_manufacture_attempts(self) -> None:
        rows=provider_rows("c","b",["UNKNOWN"]*5)
        counts,_=usage._provider_facts(rows,candidate_id="c",batch_id="b",cohort="gpt-producer",reserved_calls=5,call_contract=usage._make_call_contract("gpt-producer",5,[f"subject-{i:02d}" for i in range(1,6)],candidate_id="c"),paired_opus_contract=None)
        self.assertEqual(0,counts["attempted"])
        self.assertEqual(0,counts["accepted"])
        self.assertEqual(0,counts["in_flight"])

    def test_usage_outcome_unknown_counts_one_proved_attempt_from_dispatch_evidence(self) -> None:
        rows=provider_rows("c","b",["UNKNOWN"]+["NOT_DISPATCHED"]*4);rows[0].update({"unknown_kind":"OUTCOME_UNKNOWN","acknowledgment_origin":"BOTH","accepted":True,"in_flight":True,"started_at":"2026-07-10T12:00:00Z","host_invocation_id":"observed-host-1","terminal_transport_status":"IN_FLIGHT"})
        contract=usage._make_call_contract("gpt-producer",5,[f"subject-{i:02d}" for i in range(1,6)],candidate_id="c")
        counts,_=usage._provider_facts(rows,candidate_id="c",batch_id="b",cohort="gpt-producer",reserved_calls=5,call_contract=contract,paired_opus_contract=None)
        self.assertEqual((1,1,1,1),(counts["attempted"],counts["accepted"],counts["in_flight"],counts["unknown"]))

    def test_usage_provider_transport_facts_are_coherent_and_unique(self) -> None:
        contract=usage._make_call_contract("gpt-producer",5,[f"subject-{i:02d}" for i in range(1,6)],candidate_id="c")
        good=provider_rows("c","b",["COMPLETED"]*5)
        mutations=[]
        duplicate=json.loads(json.dumps(good));duplicate[1]["provider_call_id"]=duplicate[0]["provider_call_id"];mutations.append(duplicate)
        duplicate_host=json.loads(json.dumps(good));duplicate_host[1]["host_invocation_id"]=duplicate_host[0]["host_invocation_id"];mutations.append(duplicate_host)
        incoherent=provider_rows("c","b",["UNKNOWN"]*5);incoherent[0].update({"accepted":False,"in_flight":True,"ended_at":"2026-07-10T12:00:01Z","provider_call_id":[]});mutations.append(incoherent)
        for rows in mutations:
            with self.assertRaisesRegex(ValueError,"usage_provider_metadata"):
                usage._provider_facts(rows,candidate_id="c",batch_id="b",cohort="gpt-producer",reserved_calls=5,call_contract=contract,paired_opus_contract=None)

    def test_usage_acknowledgment_origins_accept_provider_adapter_or_both_independently(self) -> None:
        contract=usage._make_call_contract("gpt-producer",5,[f"subject-{i:02d}" for i in range(1,6)],candidate_id="c")
        variants=(("PROVIDER_ACCEPTED",True,None),("ADAPTER_IN_FLIGHT",None,True),("BOTH",True,True))
        for origin,accepted,in_flight in variants:
            with self.subTest(origin=origin):
                rows=provider_rows("c","b",["UNKNOWN"]+["NOT_DISPATCHED"]*4);rows[0].update({"unknown_kind":"OUTCOME_UNKNOWN","acknowledgment_origin":origin,"accepted":accepted,"in_flight":in_flight,"started_at":"2026-07-10T12:00:00Z","host_invocation_id":"host-observed","terminal_transport_status":"TIMEOUT"})
                counts,_=usage._provider_facts(rows,candidate_id="c",batch_id="b",cohort="gpt-producer",reserved_calls=5,call_contract=contract,paired_opus_contract=None)
                self.assertEqual(1,counts["attempted"]);self.assertEqual(int(accepted is True),counts["accepted"]);self.assertEqual(int(in_flight is True),counts["in_flight"])
        for origin,accepted,in_flight in (("NONE",True,None),("PROVIDER_ACCEPTED",None,None),("ADAPTER_IN_FLIGHT",True,True),("BOTH",True,None)):
            rows=provider_rows("c","b",["UNKNOWN"]+["NOT_DISPATCHED"]*4);rows[0].update({"unknown_kind":"OUTCOME_UNKNOWN","acknowledgment_origin":origin,"accepted":accepted,"in_flight":in_flight,"started_at":"2026-07-10T12:00:00Z","terminal_transport_status":"UNKNOWN"})
            with self.subTest(contradiction=origin),self.assertRaisesRegex(ValueError,"acknowledgment"):
                usage._provider_facts(rows,candidate_id="c",batch_id="b",cohort="gpt-producer",reserved_calls=5,call_contract=contract,paired_opus_contract=None)

    def test_usage_transport_outcome_matrix_rejects_one_variable_contradictions(self) -> None:
        contract=usage._make_call_contract("gpt-producer",5,[f"subject-{i:02d}" for i in range(1,6)],candidate_id="c")
        base=provider_rows("c","b",["UNKNOWN"]+["NOT_DISPATCHED"]*4);base[0].update({"unknown_kind":"OUTCOME_UNKNOWN","acknowledgment_origin":"ADAPTER_IN_FLIGHT","accepted":None,"in_flight":True,"started_at":"2026-07-10T12:00:00Z","host_invocation_id":"host-observed","terminal_transport_status":"TIMEOUT"})
        usage._provider_facts(base,candidate_id="c",batch_id="b",cohort="gpt-producer",reserved_calls=5,call_contract=contract,paired_opus_contract=None)
        dispatch_unknown=provider_rows("c","b",["UNKNOWN"]*5);dispatch_unknown[0]["terminal_transport_status"]="TIMEOUT"
        counts,_=usage._provider_facts(dispatch_unknown,candidate_id="c",batch_id="b",cohort="gpt-producer",reserved_calls=5,call_contract=contract,paired_opus_contract=None)
        self.assertEqual(0,counts["attempted"])
        for field,value in (("acknowledgment_origin","NONE"),("terminal_transport_status","NOT_STARTED"),("unknown_kind","DISPATCH_UNKNOWN")):
            mutated=json.loads(json.dumps(base));mutated[0][field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"usage_provider_metadata"):
                usage._provider_facts(mutated,candidate_id="c",batch_id="b",cohort="gpt-producer",reserved_calls=5,call_contract=contract,paired_opus_contract=None)

    def test_usage_subject_manifest_shape_is_stable_usage_binding(self) -> None:
        for subjects in ("abcde",["a","b","c","d",[]],["a","b","c","d",{}],["a","b","c","d",True],["a","b","c","d",None],["a","a","b","c","d"]):
            with self.subTest(subjects=repr(subjects)),self.assertRaisesRegex(ValueError,"usage_binding"):
                usage._make_call_contract("gpt-producer",5,subjects,candidate_id="c")

    def test_usage_paired_parent_binds_two_siblings_and_shared_custody(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects)
            reservation=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertEqual(["parent-gpt"]*5+["parent-opus"]*5,[row["candidate_id"] for row in reservation["call_contract"]])
            protocol_path=anchors["paired_protocol_authorization_path"];protocol=load(protocol_path);protocol["package_sha256"]="f"*64;protocol_path.write_bytes(canonical_bytes(protocol))
            with self.assertRaisesRegex(ValueError,"external content address mismatch"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=1,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired-2",call_subject_ids=subjects,**anchors)

    def test_usage_each_external_paired_anchor_rejects_substitution(self) -> None:
        fields=("outer_parent_authorization_path","paired_protocol_authorization_path","gpt_child_authorization_path","opus_child_authorization_path")
        for field in fields:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as td:
                ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);path=anchors[field];record=load(path);record["parent_id"]="substituted";path.write_bytes(canonical_bytes(record))
                with self.assertRaisesRegex(ValueError,"external content address mismatch"):
                    REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)

    def test_usage_recomputed_four_record_custody_cannot_reuse_parent_authority(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects)
            outer=load(anchors["outer_parent_authorization_path"]);gpt=load(anchors["gpt_child_authorization_path"]);opus=load(anchors["opus_child_authorization_path"]);protocol=load(anchors["paired_protocol_authorization_path"])
            for record in (outer,gpt,opus,protocol):
                record.update({"package_sha256":"1"*64,"archive_sha256":"2"*64,"extracted_tree_sha256":"3"*64,"build_manifest_sha256":"4"*64})
            for key,record,prefix in (("gpt",gpt,"gpt_child"),("opus",opus,"opus_child")):
                path=anchors[f"{prefix}_authorization_path"];raw=canonical_bytes(record);path.write_bytes(raw);anchors[f"{prefix}_authorization_sha256"]=hashlib.sha256(raw).hexdigest()
            protocol["gpt_child_authorization_sha256"]=anchors["gpt_child_authorization_sha256"];protocol["opus_child_authorization_sha256"]=anchors["opus_child_authorization_sha256"]
            raw=canonical_bytes(protocol);anchors["paired_protocol_authorization_path"].write_bytes(raw);anchors["paired_protocol_authorization_sha256"]=hashlib.sha256(raw).hexdigest()
            outer["gpt_child_authorization_sha256"]=anchors["gpt_child_authorization_sha256"];outer["opus_child_authorization_sha256"]=anchors["opus_child_authorization_sha256"];outer["paired_protocol_core_sha256"]=canonical_sha256({key:value for key,value in protocol.items() if key!="outer_parent_authorization_sha256"});anchors["outer_parent_authorization_path"].write_bytes(canonical_bytes(outer))
            with self.assertRaisesRegex(ValueError,"outer_parent_authorization"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertFalse((ledger/"head.json").exists());self.assertFalse((ledger/"transactions").exists())

    def test_usage_authorization_drift_after_read_is_rejected_before_publication(self) -> None:
        for field in ("outer_parent_authorization_path","paired_protocol_authorization_path","gpt_child_authorization_path","opus_child_authorization_path"):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as td:
                ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);target=anchors[field].resolve();real=Path.read_bytes;drifted=False
                def drifting_read(path):
                    nonlocal drifted
                    raw=real(path)
                    if path.resolve()==target and not drifted:
                        drifted=True;record=json.loads(raw);record["package_sha256"]="f"*64;path.write_bytes(canonical_bytes(record))
                    return raw
                with mock.patch.object(Path,"read_bytes",drifting_read),self.assertRaisesRegex(ValueError,"authorization_toctou"):
                    REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
                self.assertFalse((ledger/"head.json").exists());self.assertFalse((ledger/"transactions").exists())

    def _assert_authorization_mutation_after_final_verify_cannot_publish(self,field: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);target=anchors[field];real_verify=usage._verify_authorization_snapshots
            def verify_then_mutate(root,snapshots):
                real_verify(root,snapshots);record=load(target);record["package_sha256"]="f"*64;target.write_bytes(canonical_bytes(record))
            with mock.patch.object(usage,"_verify_authorization_snapshots",side_effect=verify_then_mutate),self.assertRaisesRegex(ValueError,"authorization_toctou"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertFalse((ledger/"head.json").exists());self.assertFalse((ledger/"transactions").exists())

    def test_usage_outer_authorization_mutation_after_final_verify_cannot_publish(self) -> None:
        self._assert_authorization_mutation_after_final_verify_cannot_publish("outer_parent_authorization_path")

    def test_usage_protocol_authorization_mutation_after_final_verify_cannot_publish(self) -> None:
        self._assert_authorization_mutation_after_final_verify_cannot_publish("paired_protocol_authorization_path")

    def test_usage_gpt_child_authorization_mutation_after_final_verify_cannot_publish(self) -> None:
        self._assert_authorization_mutation_after_final_verify_cannot_publish("gpt_child_authorization_path")

    def test_usage_opus_child_authorization_mutation_after_final_verify_cannot_publish(self) -> None:
        self._assert_authorization_mutation_after_final_verify_cannot_publish("opus_child_authorization_path")

    def test_usage_authorization_custody_is_replayed_and_content_addressed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects)
            reservation=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertEqual(4,len(reservation["authorization_custody"]))
            custody=ledger/reservation["authorization_custody"][0]["path"]
            record=load(custody);record["package_sha256"]="f"*64;custody.write_bytes(canonical_bytes(record))
            self.assertEqual(1,usage.validate_head(ledger)["sequence"],"transaction-embedded custody remains authoritative after staging drift")
            transaction=load(ledger/"transactions"/f"{reservation['transaction_sha256']}.json");transaction["authorization_custody"][0]["record"]["package_sha256"]="e"*64
            tampered_sha=canonical_sha256(transaction);(ledger/"transactions"/f"{tampered_sha}.json").write_bytes(canonical_bytes(transaction))
            with self.assertRaisesRegex(ValueError,"usage_authorization_custody_content_address"):
                usage.validate_head(ledger)

    def test_usage_authorization_custody_publication_is_no_replace(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects)
            custody=ledger/"authorization-custody"/f"{anchors['authorization_sha256']}.json";custody.parent.mkdir();collision=b"{}\n";custody.write_bytes(collision)
            reservation=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertEqual(1,reservation["sequence"]);self.assertEqual(anchors["outer_parent_authorization_path"].read_bytes(),custody.read_bytes())
            quarantined=list((ledger/"quarantine"/"authorization-custody").glob(f"{anchors['authorization_sha256']}.*.json"));self.assertEqual(1,len(quarantined));self.assertEqual(collision,quarantined[0].read_bytes())

    def test_usage_post_transfer_custody_mutation_does_not_publish_and_retries(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);real_transfer=usage._transfer_authorization_custody
            def transfer_then_mutate(root,snapshots):
                refs=real_transfer(root,snapshots);path=root/refs[0]["path"];record=load(path);record["package_sha256"]="f"*64;path.write_bytes(canonical_bytes(record));return refs
            with mock.patch.object(usage,"_transfer_authorization_custody",side_effect=transfer_then_mutate),self.assertRaisesRegex(ValueError,"usage_authorization_custody_content_address"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertFalse((ledger/"head.json").exists());self.assertEqual([],list((ledger/"transactions").glob("*.json")) if (ledger/"transactions").exists() else [])
            self.assertEqual(0,usage.validate_head(ledger)["sequence"])
            retry=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertEqual(1,retry["sequence"]);self.assertEqual([retry["transaction_sha256"]],usage.validate_head(ledger)["open_reservations"])

    def test_usage_post_append_pre_head_custody_mutation_retains_valid_transaction_and_retries(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);real_append=usage._append
            def append_then_mutate(root,tx):
                digest=real_append(root,tx);path=root/tx["authorization_custody"][0]["path"];record=load(path);record["package_sha256"]="f"*64;path.write_bytes(canonical_bytes(record));return digest
            with mock.patch.object(usage,"_append",side_effect=append_then_mutate),mock.patch.object(usage,"_quarantine_drifted_custody",side_effect=RuntimeError("injected crash before cleanup")),self.assertRaisesRegex(RuntimeError,"crash before cleanup"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertFalse((ledger/"head.json").exists());self.assertEqual(1,len(list((ledger/"transactions").glob("*.json"))))
            self.assertEqual(0,usage.validate_head(ledger)["sequence"],"unreachable append residue must remain a valid DAG node")
            retry=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertEqual(1,retry["sequence"]);self.assertEqual(1,len(list((ledger/"transactions").glob("*.json"))));self.assertEqual(1,len(list((ledger/"quarantine"/"authorization-custody").glob("*.json"))))

    def test_usage_partial_custody_publication_is_adopted_on_retry(self) -> None:
        for crash_at in (2,3,4):
            with self.subTest(published_before_crash=crash_at-1),tempfile.TemporaryDirectory() as td:
                ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);real_publish=usage.atomic_publish_bytes;published=0
                def publish_partial_then_crash(path,raw):
                    nonlocal published
                    if "authorization-custody" in path.parts:
                        published+=1
                        if published==crash_at:raise RuntimeError("injected partial custody crash")
                    return real_publish(path,raw)
                with mock.patch.object(usage,"atomic_publish_bytes",side_effect=publish_partial_then_crash),self.assertRaisesRegex(RuntimeError,"partial custody crash"):
                    REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
                self.assertFalse((ledger/"head.json").exists());self.assertEqual(crash_at-1,len(list((ledger/"authorization-custody").glob("*.json"))));self.assertEqual(0,usage.validate_head(ledger)["sequence"])
                retry=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
                self.assertEqual(1,retry["sequence"]);self.assertEqual(4,len(list((ledger/"authorization-custody").glob("*.json"))))

    def test_usage_append_linearization_allows_only_byte_identical_retry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects)
            with mock.patch.object(usage,"_atomic_write",side_effect=RuntimeError("injected pre-head crash")),self.assertRaisesRegex(RuntimeError,"pre-head crash"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertFalse((ledger/"head.json").exists());self.assertEqual(1,len(list((ledger/"transactions").glob("*.json"))));self.assertEqual(0,usage.validate_head(ledger)["sequence"])
            with self.assertRaisesRegex(ValueError,"usage_authorization_replay"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="substituted-batch",call_subject_ids=subjects,**anchors)
            self.assertFalse((ledger/"head.json").exists());self.assertEqual(1,len(list((ledger/"transactions").glob("*.json"))))
            retry=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertEqual(1,retry["sequence"]);self.assertEqual(1,len(list((ledger/"transactions").glob("*.json"))))

    def test_usage_transaction_mid_write_is_private_and_exact_retryable_for_every_kind(self) -> None:
        real_fdopen=os.fdopen
        def crash_fdopen_at(target_call):
            calls=0
            def crash(fd,*args,**kwargs):
                nonlocal calls
                calls+=1;handle=real_fdopen(fd,*args,**kwargs)
                if calls!=target_call:return handle
                class ShortWriter:
                    def __enter__(self):return self
                    def __exit__(self,*_):handle.close()
                    def write(self,data):
                        handle.write(data[:max(1,len(data)//2)]);handle.flush();os.fsync(handle.fileno());raise RuntimeError("injected mid-transaction write crash")
                return ShortWriter()
            return crash
        subjects=[f"subject-{index:02d}" for index in range(1,6)]
        with self.subTest(kind="reservation"),tempfile.TemporaryDirectory() as td:
            ledger=Path(td);kwargs=dict(cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="mid-reserve",cycle_or_review_batch_id="mid-reserve-cycle",call_subject_ids=subjects)
            with mock.patch.object(usage.os,"fdopen",side_effect=crash_fdopen_at(1)),self.assertRaisesRegex(RuntimeError,"mid-transaction write crash"):usage.reserve(ledger,**kwargs)
            self.assertEqual([],list((ledger/"transactions").glob("*.json")));self.assertEqual(0,usage.validate_head(ledger)["sequence"])
            self.assertEqual(1,usage.reserve(ledger,**kwargs)["sequence"])
        with self.subTest(kind="settlement"),tempfile.TemporaryDirectory() as td:
            ledger=Path(td);reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="mid-settle",cycle_or_review_batch_id="mid-settle-cycle",call_subject_ids=subjects);rows=provider_rows("mid-settle","mid-settle-cycle",["COMPLETED"]*5)
            kwargs=dict(completed=5,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=rows,measured_cost={"unit":"usd","value":"unknown"},candidate_id="mid-settle",authorization_sha256="a"*64)
            with mock.patch.object(usage.os,"fdopen",side_effect=crash_fdopen_at(1)),self.assertRaisesRegex(RuntimeError,"mid-transaction write crash"):usage.settle(ledger,reservation["transaction_sha256"],**kwargs)
            self.assertEqual(1,len(list((ledger/"transactions").glob("*.json"))));self.assertEqual([reservation["transaction_sha256"]],usage.validate_head(ledger)["open_reservations"])
            self.assertEqual("settlement",usage.settle(ledger,reservation["transaction_sha256"],**kwargs)["kind"])
        with self.subTest(kind="orphan-recovery"),tempfile.TemporaryDirectory() as td:
            ledger=Path(td);reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="mid-orphan",cycle_or_review_batch_id="mid-orphan-cycle",call_subject_ids=subjects)
            authorization={"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":"mid-orphan","campaign_authorization_sha256":"c"*64,"authorization_sha256":"a"*64,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"orphan","candidate_id":"mid-orphan","expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":"claims/mid-orphan.json","dispatch_provider_evidence_path":None,"dispatch_provider_evidence_sha256":None};auth=ledger/"auth.json";auth.write_text(json.dumps(authorization),encoding="utf-8")
            kwargs=dict(recovery_authorization=auth,orphan_id="orphan",candidate_id="mid-orphan",completed=0,failed=0,cancelled=0,not_dispatched=0,unknown=5)
            with mock.patch.object(usage.os,"fdopen",side_effect=crash_fdopen_at(2)),self.assertRaisesRegex(RuntimeError,"mid-transaction write crash"):usage.recover_orphan(ledger,reservation["transaction_sha256"],**kwargs)
            self.assertEqual(1,len(list((ledger/"transactions").glob("*.json"))));self.assertEqual([reservation["transaction_sha256"]],usage.validate_head(ledger)["open_reservations"])
            self.assertEqual("orphan-recovery",usage.recover_orphan(ledger,reservation["transaction_sha256"],**kwargs)["kind"])

    def test_usage_settlement_residue_rejects_contradiction_and_adopts_exact_retry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{index:02d}" for index in range(1,6)];reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="terminal-settle",cycle_or_review_batch_id="terminal-settle-cycle",call_subject_ids=subjects)
            completed=dict(completed=5,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=provider_rows("terminal-settle","terminal-settle-cycle",["COMPLETED"]*5),measured_cost={"unit":"usd","value":"unknown"},candidate_id="terminal-settle",authorization_sha256="a"*64)
            with mock.patch.object(usage,"_atomic_write",side_effect=RuntimeError("injected settlement head crash")),self.assertRaisesRegex(RuntimeError,"settlement head crash"):usage.settle(ledger,reservation["transaction_sha256"],**completed)
            residue=sorted(path.name for path in (ledger/"transactions").glob("*.json"));self.assertEqual(2,len(residue));self.assertEqual([reservation["transaction_sha256"]],usage.validate_head(ledger)["open_reservations"])
            contradictory=dict(completed=0,failed=0,cancelled=0,not_dispatched=5,unknown=0,provider_usage_receipts=provider_rows("terminal-settle","terminal-settle-cycle",["NOT_DISPATCHED"]*5),measured_cost={"unit":"usd","value":"0"},candidate_id="terminal-settle",authorization_sha256="a"*64)
            with self.assertRaisesRegex(ValueError,"usage_terminal_replay"):usage.settle(ledger,reservation["transaction_sha256"],**contradictory)
            self.assertEqual(residue,sorted(path.name for path in (ledger/"transactions").glob("*.json")));self.assertEqual(5,usage.settle(ledger,reservation["transaction_sha256"],**completed)["completed"])

    def test_usage_recovery_claim_and_terminal_residues_are_exactly_adoptable(self) -> None:
        subjects=[f"subject-{index:02d}" for index in range(1,6)]
        for fault in ("after-claim","after-terminal"):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                ledger=Path(td);reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id=f"recovery-{fault}",cycle_or_review_batch_id=f"recovery-{fault}-cycle",call_subject_ids=subjects)
                authorization={"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":fault,"campaign_authorization_sha256":"c"*64,"authorization_sha256":"a"*64,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"orphan","candidate_id":f"recovery-{fault}","expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":f"claims/{fault}.json","dispatch_provider_evidence_path":None,"dispatch_provider_evidence_sha256":None};auth=ledger/"auth.json";auth.write_text(json.dumps(authorization),encoding="utf-8");kwargs=dict(recovery_authorization=auth,orphan_id="orphan",candidate_id=f"recovery-{fault}",completed=0,failed=0,cancelled=0,not_dispatched=0,unknown=5)
                target=usage._append if fault=="after-claim" else usage._atomic_write
                with mock.patch.object(usage,"_append" if fault=="after-claim" else "_atomic_write",side_effect=RuntimeError(f"injected {fault} crash")),self.assertRaisesRegex(RuntimeError,fault):usage.recover_orphan(ledger,reservation["transaction_sha256"],**kwargs)
                self.assertTrue((ledger/"claims"/f"{fault}.json").exists());self.assertEqual([reservation["transaction_sha256"]],usage.validate_head(ledger)["open_reservations"])
                recovered=usage.recover_orphan(ledger,reservation["transaction_sha256"],**kwargs);self.assertEqual("orphan-recovery",recovered["kind"]);self.assertEqual(5,recovered["unknown"])

    def test_usage_competing_terminal_kind_rejects_without_damaging_residue(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{index:02d}" for index in range(1,6)];reservation=usage.reserve(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="terminal-kind",cycle_or_review_batch_id="terminal-kind-cycle",call_subject_ids=subjects);settlement=dict(completed=5,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=provider_rows("terminal-kind","terminal-kind-cycle",["COMPLETED"]*5),measured_cost={"unit":"usd","value":"unknown"},candidate_id="terminal-kind",authorization_sha256="a"*64)
            with mock.patch.object(usage,"_atomic_write",side_effect=RuntimeError("injected terminal head crash")),self.assertRaisesRegex(RuntimeError,"terminal head crash"):usage.settle(ledger,reservation["transaction_sha256"],**settlement)
            authorization={"schema":"campaign-usage-recovery-authorization-v1","kind":"orphan-recovery-authorization","authorization_id":"competing-kind","campaign_authorization_sha256":"c"*64,"authorization_sha256":"a"*64,"reservation_sha256":reservation["transaction_sha256"],"orphan_id":"orphan","candidate_id":"terminal-kind","expected_usage_head_sha256":usage.head_snapshot(ledger)["head_sha256"],"claim_path":"claims/competing-kind.json","dispatch_provider_evidence_path":None,"dispatch_provider_evidence_sha256":None};auth=ledger/"auth.json";auth.write_text(json.dumps(authorization),encoding="utf-8");before=sorted(path.name for path in (ledger/"transactions").glob("*.json"))
            with self.assertRaisesRegex(ValueError,"usage_terminal_replay"):usage.recover_orphan(ledger,reservation["transaction_sha256"],recovery_authorization=auth,orphan_id="orphan",candidate_id="terminal-kind",completed=0,failed=0,cancelled=0,not_dispatched=0,unknown=5)
            self.assertEqual(before,sorted(path.name for path in (ledger/"transactions").glob("*.json")));self.assertFalse((ledger/"claims/competing-kind.json").exists())

    def test_usage_collision_is_atomically_moved_before_mutation_classification(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{index:02d}" for index in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);custody=ledger/"authorization-custody"/f"{anchors['authorization_sha256']}.json";custody.parent.mkdir();first=b"first-collision\n";second=b"second-collision\n";custody.write_bytes(first);real_replace=usage.os.replace;moved=False
            def replace_then_compete(source,destination):
                nonlocal moved
                result=real_replace(source,destination)
                if Path(source)==custody:moved=True;custody.write_bytes(second)
                return result
            with mock.patch.object(usage.os,"replace",side_effect=replace_then_compete),self.assertRaisesRegex(ValueError,"usage_authorization_custody_exists"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertTrue(moved);self.assertEqual(second,custody.read_bytes());self.assertFalse((ledger/"head.json").exists());self.assertFalse((ledger/"transactions").exists())
            retry=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors);self.assertEqual(1,retry["sequence"])
            preserved={path.read_bytes() for path in (ledger/"quarantine"/"authorization-custody").glob("*.json")};self.assertEqual({first,second},preserved)

    def test_usage_quarantine_move_crash_is_content_addressed_on_retry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{index:02d}" for index in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);custody=ledger/"authorization-custody"/f"{anchors['authorization_sha256']}.json";custody.parent.mkdir();collision=b"move-crash-collision\n";custody.write_bytes(collision);real_replace=usage.os.replace;moved=False
            def replace_then_crash(source,destination):
                nonlocal moved
                result=real_replace(source,destination)
                if Path(source)==custody:moved=True;raise RuntimeError("injected quarantine post-move crash")
                return result
            with mock.patch.object(usage.os,"replace",side_effect=replace_then_crash),self.assertRaisesRegex(RuntimeError,"quarantine post-move crash"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertTrue(moved);self.assertFalse(custody.exists());intakes=list((ledger/"quarantine"/"authorization-custody").glob(f".{anchors['authorization_sha256']}.intake-*/collision.bin"));self.assertEqual(1,len(intakes));self.assertEqual(collision,intakes[0].read_bytes())
            retry=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors);self.assertEqual(1,retry["sequence"])
            self.assertEqual([],list((ledger/"quarantine"/"authorization-custody").glob(".*.intake-*")));self.assertIn(collision,{path.read_bytes() for path in (ledger/"quarantine"/"authorization-custody").glob("*.json")})

    def test_usage_quarantine_payload_unlink_crash_leaves_empty_intake_retryable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{index:02d}" for index in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);expected=anchors["authorization_sha256"];custody=ledger/"authorization-custody"/f"{expected}.json";custody.parent.mkdir();collision=b"post-unlink-crash-collision\n";custody.write_bytes(collision);real_rmdir=Path.rmdir;crashed=False
            def crash_empty_intake(path):
                nonlocal crashed
                if not crashed and path.name.startswith(f".{expected}.intake-"):
                    self.assertEqual([],list(path.iterdir()));crashed=True;raise RuntimeError("injected quarantine empty-intake cleanup crash")
                return real_rmdir(path)
            with mock.patch.object(Path,"rmdir",autospec=True,side_effect=crash_empty_intake),self.assertRaisesRegex(RuntimeError,"empty-intake cleanup crash"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            intakes=list((ledger/"quarantine"/"authorization-custody").glob(f".{expected}.intake-*"));self.assertTrue(crashed);self.assertEqual(1,len(intakes));self.assertEqual([],list(intakes[0].iterdir()));self.assertIn(collision,{path.read_bytes() for path in (ledger/"quarantine"/"authorization-custody").glob("*.json")})
            retry=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors);self.assertEqual(1,retry["sequence"]);self.assertFalse(intakes[0].exists())

    def test_usage_empty_well_formed_quarantine_intake_before_move_is_cleanup_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{index:02d}" for index in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);expected=anchors["authorization_sha256"];intake=ledger/"quarantine"/"authorization-custody"/f".{expected}.intake-before-move";intake.mkdir(parents=True)
            reservation=REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
            self.assertEqual(1,reservation["sequence"]);self.assertFalse(intake.exists());self.assertEqual([],list((ledger/"quarantine"/"authorization-custody").glob("*.json")))

    def test_usage_nonempty_malformed_quarantine_intake_remains_fail_closed(self) -> None:
        for shape in ("extra","misnamed","non-file"):
            with self.subTest(shape=shape),tempfile.TemporaryDirectory() as td:
                ledger=Path(td);subjects=[f"subject-{index:02d}" for index in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);expected=anchors["authorization_sha256"];intake=ledger/"quarantine"/"authorization-custody"/f".{expected}.intake-malformed-{shape}";intake.mkdir(parents=True)
                if shape=="extra":(intake/"collision.bin").write_bytes(b"collision\n");(intake/"extra.bin").write_bytes(b"extra\n")
                elif shape=="misnamed":(intake/"wrong.bin").write_bytes(b"collision\n")
                else:(intake/"collision.bin").mkdir()
                with self.assertRaisesRegex(ValueError,"usage_authorization_custody_quarantine_intake: .* intake shape differs"):
                    REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
                self.assertTrue(intake.exists());self.assertFalse((ledger/"head.json").exists());self.assertFalse((ledger/"transactions").exists())

    def test_staged_harness_compiles_with_deprecation_warnings_as_errors(self) -> None:
        source=(ROOT/"tools"/"run_staged_current_skill_smoke.py").read_text(encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("error",DeprecationWarning)
            compile(source,"tools/run_staged_current_skill_smoke.py","exec")
        prompt=staged_harness.release_section_prompt(root=ROOT,case_name="fixture",raw_input_path=Path("input.txt"),input_text="fixture",input_digest="a"*64,skill_hash="b"*64,previous_stages=[],section_id="fixture",section_role="closing_formulation",section_number=1,section_count=1,target_output_kb=None)
        self.assertIn(r"`(?m)^Land\((?P<burden>[¹²³⁴⁵⁶⁷⁸⁹]B)\):`",prompt)
        self.assertIn(r"`^\s*#{0,6}\s*Layer A\b`",prompt)

    @unittest.skipUnless(os.name=="nt","Windows junction canary")
    def test_usage_authorization_junction_ancestor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);real_dir=ledger/"fake-authorizations";junction=ledger/"authorization-junction"
            made=subprocess.run(["cmd","/c","mklink","/J",str(junction),str(real_dir)],text=True,capture_output=True,check=False)
            self.assertEqual(0,made.returncode,made.stdout+made.stderr)
            for field in ("outer_parent_authorization_path","paired_protocol_authorization_path","gpt_child_authorization_path","opus_child_authorization_path"):anchors[field]=junction/anchors[field].name
            with self.assertRaisesRegex(ValueError,"reparse"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)

    def test_usage_authorization_path_escape_and_symlink_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td,tempfile.TemporaryDirectory() as outside_td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);outside=Path(outside_td)/"protocol.json";outside.write_bytes(anchors["paired_protocol_authorization_path"].read_bytes());anchors["paired_protocol_authorization_path"]=outside
            with self.assertRaisesRegex(ValueError,"lexically contained"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td);subjects=[f"subject-{i:02d}" for i in range(1,11)];anchors=paired_authorization_kwargs(ledger,"parent",subjects);link=ledger/"protocol-link.json"
            try:link.symlink_to(anchors["paired_protocol_authorization_path"])
            except OSError:return
            anchors["paired_protocol_authorization_path"]=link
            with self.assertRaisesRegex(ValueError,"symlink/reparse"):
                REAL_USAGE_RESERVE(ledger,cohort="paired-producer",calls=10,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,candidate_id="parent",cycle_or_review_batch_id="paired",call_subject_ids=subjects,**anchors)

    def test_usage_reservation_requires_explicit_subjects(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger=Path(td)
            with self.assertRaisesRegex(ValueError,"usage_binding"):
                REAL_USAGE_RESERVE(ledger,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=usage.head_snapshot(ledger)["head_sha256"],campaign_authorization_sha256="c"*64,authorization_sha256="a"*64,candidate_id="c",cycle_or_review_batch_id="b")

    def test_fake_five_barrier_has_five_acknowledgments_before_observation(self) -> None:
        manifest = five_runner.simulate_fake_cycle(["ok"] * 5)
        self.assertEqual([], barrier.validate_dispatch_manifest(manifest, expected_workers=5))

    def test_structural_dispatch_requires_exact_terminal_worker_case_set(self) -> None:
        dispatch=five_runner.simulate_fake_cycle(["ok"]*5);first=dispatch["workers"][0]
        raw=[]
        for event in dispatch["events"]:
            event={key:value for key,value in event.items() if key not in {"sequence","predecessor_event_sha256","event_sha256"}}
            if event["event"]=="terminal_result_observed":event={**event,"worker":first["worker"],"case_id":first["case_id"]}
            raw.append(event)
        dispatch["events"]=barrier.chain_dispatch_events(raw)
        self.assertEqual("structural_dispatch_binding",matrix._structural_dispatch_errors(dispatch,[row["case_id"] for row in dispatch["workers"]])[0]["failure_class"])

    def test_fake_five_emits_submit_aggregate_and_hash_chained_protocol(self) -> None:
        manifest = five_runner.simulate_fake_cycle(["ok"] * 5)
        names = [event["event"] for event in manifest["events"]]
        self.assertEqual(5, names.count("request_submit_started"))
        self.assertEqual(1, names.count("all_five_in_flight"))
        self.assertEqual(list(range(1, len(manifest["events"]) + 1)), [event["sequence"] for event in manifest["events"]])
        self.assertTrue(all(len(event["event_sha256"]) == 64 for event in manifest["events"]))

    def test_dispatch_sabotage_fails_for_exact_protocol_reason(self) -> None:
        good = five_runner.simulate_fake_cycle(["ok"] * 5)
        raw = [{key: value for key, value in event.items() if key not in {"sequence", "predecessor_event_sha256", "event_sha256"}} for event in good["events"]]
        cases = {
            "missing-submit": ([event for event in raw if not (event["event"] == "request_submit_started" and event.get("worker") == "w0")], "missing_submit_event"),
            "missing-aggregate": ([event for event in raw if event["event"] != "all_five_in_flight"], "early_result_observation"),
            "case-drift": ([{**event, "case_id": "wrong"} if event.get("worker") == "w0" and event["event"] == "worker_ready" else event for event in raw], "dispatch_worker_binding"),
        }
        for name, (events, expected) in cases.items():
            with self.subTest(name=name):
                mutated = {**good, "events": barrier.chain_dispatch_events(events)}
                self.assertEqual(expected, barrier.validate_dispatch_manifest(mutated, 5)[0]["failure_class"])
        broken = json.loads(json.dumps(good)); broken["events"][3]["event_sha256"] = "0" * 64
        self.assertEqual("dispatch_event_hash", barrier.validate_dispatch_manifest(broken, 5)[0]["failure_class"])

    def test_fake_five_failure_preserves_all_rows_finalizes_and_spends_no_cold_calls(self) -> None:
        manifest = five_runner.simulate_fake_cycle(["ok", "structural-fail", "ok", "ok", "ok"])
        self.assertEqual(5, len(manifest["rows"]))
        self.assertEqual("structural-fail", manifest["rows"][1]["result"])
        self.assertEqual("FINALIZED", manifest["observation_finalizer"]["status"])
        self.assertEqual(0, manifest["cold_review_calls"])

    def test_fake_paired_barrier_has_ten_acknowledgments_before_observation(self) -> None:
        manifest = paired_runner.simulate_fake_paired_cycle(["ok"] * 5, ["ok"] * 5)
        self.assertEqual([], paired.validate_paired_manifest(manifest))

    def test_fake_paired_emits_submit_aggregate_and_hash_chained_protocol(self) -> None:
        manifest = paired_runner.simulate_fake_paired_cycle(["ok"] * 5, ["ok"] * 5)
        events = manifest["dispatch_manifest"]["events"]
        names = [event["event"] for event in events]
        self.assertEqual(10, names.count("request_submit_started"))
        self.assertEqual(1, names.count("all_ten_in_flight"))
        self.assertEqual(list(range(1, len(events) + 1)), [event["sequence"] for event in events])

    def test_paired_siblings_bind_full_provenance_and_exact_rows(self) -> None:
        manifest = paired_runner.simulate_fake_paired_cycle(["ok"] * 5, ["ok"] * 5)
        fields = {"source_commit", "package_sha256", "archive_sha256", "extracted_tree_sha256", "build_manifest_sha256", "registry_sha256"}
        self.assertTrue(fields <= set(manifest["gpt_candidate"]))
        self.assertTrue(fields <= set(manifest["opus_candidate"]))
        self.assertTrue(all(isinstance(row, dict) for row in manifest["gpt_rows"] + manifest["opus_rows"]))
        self.assertEqual([], paired.validate_paired_manifest(manifest))

    def test_paired_provenance_and_worker_sabotage_rejects_right_reason(self) -> None:
        base = paired_runner.simulate_fake_paired_cycle(["ok"] * 5, ["ok"] * 5)
        for field in ("source_commit", "package_sha256", "archive_sha256", "extracted_tree_sha256", "build_manifest_sha256", "registry_sha256"):
            with self.subTest(field=field):
                mutated = json.loads(json.dumps(base)); mutated["opus_candidate"][field] = "0" * (40 if field == "source_commit" else 64)
                self.assertEqual("sibling_provenance_mismatch", paired.validate_paired_manifest(mutated)[0]["failure_class"])
        overlap = json.loads(json.dumps(base)); overlap["opus_rows"][0]["worker"] = overlap["gpt_rows"][0]["worker"]
        self.assertEqual("paired_cohort_overlap", paired.validate_paired_manifest(overlap)[0]["failure_class"])
        unrelated = json.loads(json.dumps(base)); unrelated["dispatch_manifest"]["workers"][0]["worker"] = "unrelated"
        self.assertEqual("paired_worker_binding", paired.validate_paired_manifest(unrelated)[0]["failure_class"])

    def test_codex_runner_requires_hash_bound_one_use_boundary(self) -> None:
        with self.assertRaisesRegex(PermissionError, "MODEL_AUTHORIZATION_REQUIRED"):
            five_runner.authorize_model_runner("codex", authorization=None, maturity=None, claim=None)

    def test_codex_runner_rejects_partial_external_predicates_before_claim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            claim = Path(td) / "claim.json"
            maturity = {"status": "NO_MODEL_CANDIDATE_MATURE", "candidate_id": "c1"}
            partial = {"kind": "matrix-authorization", "model_runner": "codex", "one_use": True,
                       "candidate_maturity_sha256": five_runner._sha256_record(maturity)}
            with self.assertRaisesRegex(PermissionError, "MODEL_AUTHORIZATION_REQUIRED"):
                five_runner.authorize_model_runner("codex", authorization=partial, maturity=maturity, claim=claim)
            self.assertFalse(claim.exists())

    def test_unimplemented_codex_runner_blocks_before_consuming_claim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            maturity = {"status": "NO_MODEL_CANDIDATE_MATURE", "candidate_id": "c1"}
            authorization = {
                "kind": "matrix-authorization",
                "model_runner": "codex",
                "one_use": True,
                "candidate_maturity_sha256": five_runner._sha256_record(maturity),
            }
            authorization_path = temp / "authorization.json"
            maturity_path = temp / "maturity.json"
            claim_path = temp / "claim.json"
            authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
            maturity_path.write_text(json.dumps(maturity), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "run_five_smoke_matrix.py"),
                    "--model-runner",
                    "codex",
                    "--authorization",
                    str(authorization_path),
                    "--candidate-maturity",
                    str(maturity_path),
                    "--one-use-claim",
                    str(claim_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, result.returncode, result.stderr or result.stdout)
            self.assertIn("LIVE_MODEL_EXECUTION_NOT_IMPLEMENTED", result.stdout)
            self.assertFalse(claim_path.exists(), "a pre-dispatch capability failure consumed the claim")

    def test_final_verdict_fails_closed_until_review_join_is_implemented(self) -> None:
        forged = {
            "schema": "daee-smoke-matrix-v1",
            "kind": "cycle-verdict",
            "matrix_id": "forged-final",
            "structural_matrix_status": "PASS",
            "completion_status": "PASS",
            "reviews": [{"status": "PASS"} for _ in range(5)],
            "non_claims": ["matrix PASS is not release or provenance proof"],
        }
        errors = matrix.validate_manifest(forged, root=ROOT)
        self.assertTrue(errors)
        self.assertEqual("review_contract_unavailable", errors[0]["failure_class"])

    def test_forged_unbound_structural_pass_is_rejected(self) -> None:
        forged = {"schema":"daee-smoke-matrix-v1","kind":"structural-pre-review-verdict","matrix_id":"arbitrary-unbound-matrix","structural_matrix_status":"PASS","completion_status":"PARTIAL","non_claims":["structural PASS is not semantic truth","structural pre-review PASS cannot authorize cold review or final completion by itself"]}
        errors = matrix.validate_manifest(forged, root=ROOT)
        self.assertTrue(errors, "an arbitrary matrix ID cannot self-authorize structural PASS")
        self.assertEqual("schema_contract", errors[0]["failure_class"])

    def test_structural_promotion_uses_actual_validation_registry_oracle(self) -> None:
        path = ROOT / "tests" / "validation-integrity" / "valid" / "right-reason-stage04.verdict.json"
        value = validation_contract.hydrate_fixture(validation_contract.materialize_fixture(path.relative_to(ROOT)), root=ROOT)
        value["aggregate_status"] = "PASS_STRUCTURAL"
        findings = validation_contract.validate_verdict(value, validation_contract.load_registry(), root=ROOT, verify_files=True)
        self.assertTrue(findings)
        self.assertEqual("aggregate_status_mismatch", findings[0].failure_class)
        errors = matrix._promotion_verdict_errors(value, root=ROOT, expected_output_sha256=value["artifacts"][1]["sha256"])
        self.assertTrue(errors)
        self.assertEqual("structural_promotion_binding", errors[0]["failure_class"])

    def test_structural_replay_rejects_synthetic_owner_status_surrogates(self) -> None:
        synthetic = {"schema":"structural-promotion-verdict-v1","structural_status":"PASS_STRUCTURAL","validation_registry_sha256":"2"*64}
        errors = matrix._promotion_verdict_errors(synthetic, root=ROOT, expected_output_sha256="1"*64)
        self.assertTrue(errors)
        self.assertEqual("structural_promotion_binding", errors[0]["failure_class"])

    def test_structural_unintegrated_owner_statuses_fail_closed_after_binding_mutation(self) -> None:
        for field in ("matrix_authorization","ci_readback","candidate_maturity","cycle_claim","candidate_consumption","a01_pre_review_capture","a11_external_promotion"):
            with self.subTest(field=field):
                retained_pass={"status":"PASS","candidate_id":"wrong-but-status-retained"}
                errors=matrix._issuer_integration_boundary(field,retained_pass)
                self.assertEqual(f"structural_{field}_integration_boundary",errors[0]["failure_class"])
                self.assertIn("cannot authorize structural PASS",errors[0]["message"])

    def test_structural_prompt_manifest_rejects_valid_other_case_substitution(self) -> None:
        record={"schema":"daee-prompt-pack-manifest-v1","case_id":"other-case","stage":"stage-01","call_index":1,
                "components":[{"name":"raw_input_text","bytes":40,"est_tok":10}],"total_bytes":40,"total_est_tok":10,
                "includes_full_runtime":False,"includes_prior_full_output":False}
        raw=(json.dumps(record)+"\n").encode()
        errors=matrix._prompt_manifest_errors(raw,"canonical-case")
        self.assertEqual("structural_prompt_binding",errors[0]["failure_class"])
        self.assertIn("case_id",errors[0]["message"])

    def test_structural_reference_rejects_hash_drift_escape_and_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests" / "smoke-matrix") as td:
            base=Path(td);reference=write_record(base,"record.json",{"schema":"probe-v1"})
            with self.assertRaisesRegex(ValueError,"structural_artifact_hash"):
                matrix._read_ref(base,{**reference,"sha256":"0"*64})
            with self.assertRaisesRegex(ValueError,"structural_path"):
                matrix._read_ref(base,{"path":"../escape.json","sha256":"0"*64})
            link=base/"link.json"
            try:link.symlink_to(base/"record.json")
            except OSError:self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(ValueError,"structural_path"):
                matrix._read_ref(base,{"path":"link.json","sha256":reference["sha256"]})

    def test_structural_external_custody_accepts_bound_cycle_and_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            custody=Path(td)/"authorized-evidence";cycle=custody/"cycles"/"cycle-1";cycle.mkdir(parents=True)
            manifest={"schema":"daee-structural-cycle-inventory-v1","evidence_custody_root":str(custody.resolve()),"cycle_root":"cycles/cycle-1"}
            (cycle/"cycle-manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
            resolved=matrix._external_custody_root(str(custody),ROOT)
            self.assertEqual(cycle.resolve(),matrix._safe_path(resolved,"cycles/cycle-1",directory=True))
            with self.assertRaisesRegex(ValueError,"structural_path"):
                matrix._safe_path(resolved,"../escape",directory=True)
            try:
                verdict_builder.build_structural_verdict(registry_contract.DEFAULT_REGISTRY,cycle)
            except ValueError as exc:
                self.assertNotIn("structural_path",str(exc),"authorized external custody must pass before artifact-contract replay")
                self.assertIn("structural_cycle_manifest",str(exc))
            else:self.fail("an incomplete external cycle inventory unexpectedly authorized structural PASS")

    def test_structural_external_custody_rejects_reparse_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);real=base/"real";real.mkdir();link=base/"linked"
            try:link.symlink_to(real,target_is_directory=True)
            except OSError:self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(ValueError,"structural_path"):
                matrix._external_custody_root(str(link),ROOT)
            with self.assertRaisesRegex(ValueError,"structural_path"):
                verdict_builder._contained_relative(link,link,"cycle root")

    def test_structural_external_custody_rejects_repo_parent_and_cycle_back_into_repo(self) -> None:
        repo_parent=ROOT.parent
        with self.assertRaisesRegex(ValueError,"structural_path"):
            matrix._external_custody_root(str(repo_parent),ROOT)
        manifest={"evidence_custody_root":str(repo_parent.resolve()),"cycle_root":ROOT.relative_to(repo_parent).as_posix()}
        with self.assertRaisesRegex(ValueError,"structural_path"):
            verdict_builder._external_cycle_binding(ROOT,manifest,ROOT)

    def test_structural_builder_requires_registry_and_cycle_root_and_emits_no_review_artifact_on_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "structural-pre-review-verdict.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "build_smoke_matrix_verdict.py"),
                 "--mode", "structural-pre-review", "--out", str(out)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertFalse(out.exists())
            self.assertFalse((out.parent / "cold-review-packet.json").exists())

    def test_structural_verdict_publication_is_fresh_no_replace_with_hash_readback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"structural-pre-review-verdict.json";sentinel=b"existing-verdict\n";out.write_bytes(sentinel)
            with self.assertRaisesRegex(ValueError,"structural_verdict_exists"):
                verdict_builder.publish_verdict(out,{"schema":"probe"})
            self.assertEqual(sentinel,out.read_bytes())

    def test_structural_output_destination_is_exact_fresh_cycle_child(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);cycle=base/"cycle";cycle.mkdir();exact=cycle/"structural-pre-review-verdict.json"
            verdict_builder.validate_output_destination(exact,cycle)
            for invalid in (base/"outside.json",cycle/"other.json",base/"structural-pre-review-verdict.json"):
                with self.subTest(invalid=invalid),self.assertRaisesRegex(ValueError,"structural_output_path"):verdict_builder.validate_output_destination(invalid,cycle)
            exact.write_text("occupied",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"structural_verdict_exists"):verdict_builder.validate_output_destination(exact,cycle)

    def test_structural_cli_rejects_outside_output_before_replay_or_publication(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);cycle,_=make_structural_near_positive(base);outside=base/"structural-pre-review-verdict.json"
            result=subprocess.run([sys.executable,"-B",str(ROOT/"tools"/"build_smoke_matrix_verdict.py"),"--mode","structural-pre-review","--registry",str(registry_contract.DEFAULT_REGISTRY),"--cycle-root",str(cycle),"--out",str(outside)],cwd=ROOT,text=True,capture_output=True,check=False)
            self.assertEqual(1,result.returncode);self.assertIn("structural_output_path",result.stdout);self.assertFalse(outside.exists())

    def test_structural_output_destination_rejects_reparse_cycle_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);real=base/"real";real.mkdir();link=base/"linked"
            try:link.symlink_to(real,target_is_directory=True)
            except OSError:self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(ValueError,"structural_output_path"):
                verdict_builder.validate_output_destination(link/"structural-pre-review-verdict.json",link)

    def test_structural_external_cycle_near_positive_reaches_explicit_a16_export_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cycle,_=make_structural_near_positive(Path(td))
            with self.assertRaisesRegex(ValueError,"structural_evidence_export_integration_boundary"):
                verdict_builder.build_structural_verdict(registry_contract.DEFAULT_REGISTRY,cycle)

    def test_structural_local_case_replay_precedes_a16_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cycle,manifest=make_structural_near_positive(Path(td));manifest["cases"][0]["handoff_record"]={"path":"missing.json","sha256":"0"*64};(cycle/"cycle-manifest.json").write_bytes(canonical_bytes(manifest))
            with self.assertRaisesRegex(ValueError,"structural_path"):
                verdict_builder.build_structural_verdict(registry_contract.DEFAULT_REGISTRY,cycle)

    def test_structural_external_cycle_mutations_fail_at_exact_first_join(self) -> None:
        expected={"registry":"structural_registry_binding","cycle":"structural_path","package":"structural_parity_binding","dispatch":"structural_dispatch_binding","authorization":"structural_authorization_binding","usage":"usage_head_chain","finalizer":"structural_finalizer_binding","export":"structural_evidence_export_integration_boundary"}
        for mutation,failure_class in expected.items():
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as td:
                cycle,manifest=make_structural_near_positive(Path(td))
                if mutation=="registry":manifest["registry_sha256"]="0"*64
                elif mutation=="cycle":manifest["cycle_root"]="cycles/substituted"
                elif mutation=="package":
                    parity=load(cycle/manifest["package_harness_parity"]["path"]);parity["classification"]="harness-assisted"
                    manifest["package_harness_parity"]=write_record(cycle,"package-parity.json",parity)
                elif mutation=="dispatch":
                    dispatch=load(cycle/manifest["dispatch_manifest"]["path"]);dispatch["rows"][0]["case_id"]="substituted-case"
                    manifest["dispatch_manifest"]=write_record(cycle,"dispatch.json",dispatch)
                elif mutation=="authorization":manifest["matrix_authorization_sha256"]="0"*64
                elif mutation=="usage":
                    head_path=cycle/manifest["usage_ledger"]["path"]/"head.json";head=load(head_path);head["totals"]["completed"]+=1;head_path.write_bytes(canonical_bytes(head));manifest["usage_ledger"]["tree_sha256"]=test_tree_sha256(head_path.parent)
                elif mutation=="finalizer":
                    finalizer=load(cycle/manifest["observation_finalizer"]["path"]);finalizer["dispatch_count"]=4
                    finalizer_ref=write_record(cycle,"observation-finalizer.json",finalizer);manifest["observation_finalizer"]=finalizer_ref
                    consumption=load(cycle/manifest["candidate_consumption"]["path"]);consumption["observation_finalizer_sha256"]=finalizer_ref["sha256"]
                    manifest["candidate_consumption"]=write_record(cycle,"candidate-consumption.json",consumption)
                elif mutation=="export":
                    manifest["evidence_export"]=write_record(cycle,"evidence-export.json",{"schema":"evidence-export-owner-boundary-v1","status":"PASS_BUT_UNVALIDATED"})
                (cycle/"cycle-manifest.json").write_bytes(canonical_bytes(manifest))
                with self.assertRaisesRegex(ValueError,failure_class):verdict_builder.build_structural_verdict(registry_contract.DEFAULT_REGISTRY,cycle)

    def test_structural_every_local_case_surface_replays_before_owner_boundary(self) -> None:
        for surface in ("handoff_record","prompt_manifest","state_capsules","output","capture_manifest","promotion_verdict"):
            with self.subTest(surface=surface),tempfile.TemporaryDirectory() as td:
                cycle,manifest=make_structural_near_positive(Path(td));row=manifest["cases"][0]
                if surface=="handoff_record":
                    record=load(cycle/row[surface]["path"]);record["case_id"]="substituted";row[surface]=write_record(cycle,row[surface]["path"],record)
                elif surface=="prompt_manifest":
                    record=json.loads((cycle/row[surface]["path"]).read_text());record["case_id"]="substituted";row[surface]=write_bytes_ref(cycle,row[surface]["path"],canonical_bytes(record))
                elif surface=="state_capsules":
                    (cycle/row[surface]["path"]/"capsule-001.json").write_bytes(b"{}\n")
                else:(cycle/row[surface]["path"]).write_bytes(b"mutated\n")
                (cycle/"cycle-manifest.json").write_bytes(canonical_bytes(manifest))
                with self.assertRaisesRegex(ValueError,"structural_(?:stage|prompt|artifact)"):
                    verdict_builder.build_structural_verdict(registry_contract.DEFAULT_REGISTRY,cycle)

    def test_structural_directory_replay_detects_ledger_and_parity_toctou(self) -> None:
        for surface in ("ledger","parity"):
            with self.subTest(surface=surface),tempfile.TemporaryDirectory() as td:
                cycle,_=make_structural_near_positive(Path(td))
                if surface=="ledger":
                    real=usage.validate_head
                    def drifting_head(root):
                        result=real(root);(root/"toctou-drift.bin").write_bytes(b"drift");return result
                    patcher=mock.patch.object(usage,"validate_head",side_effect=drifting_head)
                else:
                    real=matrix.validate_package_parity
                    def drifting_parity(record,package_root,run_root,repo_root):
                        result=real(record,package_root,run_root,repo_root);(run_root/"toctou-drift.bin").write_bytes(b"drift");return result
                    patcher=mock.patch.object(matrix,"validate_package_parity",side_effect=drifting_parity)
                with patcher,self.assertRaisesRegex(ValueError,"structural_toctou"):
                    verdict_builder.build_structural_verdict(registry_contract.DEFAULT_REGISTRY,cycle)

    def test_structural_cycle_wide_digest_detects_case_replay_drift_before_owner_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cycle,_=make_structural_near_positive(Path(td));real=matrix.validate_handoff_record;calls=0
            def drifting_handoff(path,record):
                nonlocal calls
                result=real(path,record);calls+=1
                if calls==1:(cycle/"cycle-wide-drift.bin").write_bytes(b"drift")
                return result
            with mock.patch.object(matrix,"validate_handoff_record",side_effect=drifting_handoff),self.assertRaisesRegex(ValueError,"structural_toctou"):
                verdict_builder.build_structural_verdict(registry_contract.DEFAULT_REGISTRY,cycle)

    def test_candidate_archive_safe_extract_and_hash_readback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            archive = temp / "safe.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("skill/SKILL.md", "safe\n")
                zf.writestr("skill/references/x.md", "x\n")
            receipt = candidate.safe_extract_zip(archive, temp / "fresh-destination", declared_total_bytes=7, max_total_bytes=1024)
            self.assertEqual(2, receipt["file_count"])
            self.assertEqual(7, receipt["actual_total_bytes"])
            self.assertEqual(64, len(receipt["tree_sha256"]))

    def test_candidate_archive_rejects_named_security_canaries(self) -> None:
        specs = load(ROOT / "tests" / "smoke-matrix" / "archive-canaries" / "invalid-entries.json")
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            for index, spec in enumerate(specs):
                with self.subTest(failure_class=spec["failure_class"]):
                    archive = temp / f"bad-{index}.zip"
                    with zipfile.ZipFile(archive, "w") as zf:
                        first = zipfile.ZipInfo(spec["name"])
                        if spec.get("symlink"):
                            first.create_system = 3
                            first.external_attr = 0o120777 << 16
                        if spec.get("unix_mode") is not None:
                            first.create_system = 3
                            first.external_attr = int(spec["unix_mode"], 8) << 16
                        if spec.get("reparse"):
                            first.external_attr |= 0x400
                        zf.writestr(first, "x")
                        if spec.get("second_name") is not None:
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore", UserWarning)
                                zf.writestr(spec["second_name"], "y")
                    with self.assertRaisesRegex(ValueError, spec["failure_class"]):
                        candidate.safe_extract_zip(archive, temp / f"dest-{index}", declared_total_bytes=2 if spec.get("second_name") else 1, max_total_bytes=1024)

    def test_candidate_archive_rejects_size_bomb_and_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td); archive = temp / "sized.zip"
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("large.txt", "x" * 2048)
            with self.assertRaisesRegex(ValueError, "archive_size_bomb"):
                candidate.safe_extract_zip(archive, temp / "size-dest", declared_total_bytes=2048, max_total_bytes=1024)
            with self.assertRaisesRegex(ValueError, "archive_declared_size_mismatch"):
                candidate.safe_extract_zip(archive, temp / "declared-dest", declared_total_bytes=1, max_total_bytes=4096)
            existing = temp / "existing"; existing.mkdir()
            with self.assertRaisesRegex(FileExistsError, "destination_exists"):
                candidate.safe_extract_zip(archive, existing, declared_total_bytes=2048, max_total_bytes=4096)

    def test_candidate_destination_is_fresh_contained_and_not_symlinked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "candidates"
            root.mkdir()
            candidate.assert_fresh_contained_path(root, root / "c1" / "extracted")
            with self.assertRaisesRegex(ValueError, "candidate_path_escape"):
                candidate.assert_fresh_contained_path(root, root.parent / "outside")
            link = root / "linked"
            try:
                link.symlink_to(root.parent, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(ValueError, "candidate_symlink_escape"):
                candidate.assert_fresh_contained_path(root, link / "c2")

    def test_candidate_transition_publication_is_no_replace_and_hash_bound(self) -> None:
        ready = {"schema": "daee-smoke-matrix-v1", "kind": "candidate-package-record", "candidate_id": "c1",
                 "status": "READY_UNUSED", "authorization_sha256": "a" * 64, "claim_receipt_sha256": "b" * 64}
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "transition.json"
            built = candidate.publish_transition_record(ready, out, claimed=True, dispatch_count=1)
            self.assertEqual("CONSUMED_OBSERVED", built["status"])
            self.assertEqual("c1", built["candidate_id"])
            self.assertEqual("a" * 64, built["authorization_sha256"])
            self.assertEqual("b" * 64, built["claim_receipt_sha256"])
            self.assertEqual(64, len(built["predecessor_record_sha256"]))
            original = out.read_bytes()
            with self.assertRaisesRegex(ValueError, "target already exists"):
                candidate.publish_transition_record(ready, out, claimed=True, dispatch_count=0)
            self.assertEqual(original, out.read_bytes())

    def test_candidate_terminal_record_hash_tamper_is_rejected(self) -> None:
        ready={"schema":"daee-smoke-matrix-v1","kind":"candidate-package-record","candidate_id":"c1","status":"READY_UNUSED","authorization_sha256":"a"*64,"claim_receipt_sha256":"b"*64}
        terminal=candidate.build_transition_record(ready,claimed=True,dispatch_count=1)
        self.assertEqual([],matrix.validate_manifest(terminal,root=ROOT))
        tampered={**terminal,"candidate_id":"different"}
        self.assertEqual("candidate_record_hash",matrix.validate_manifest(tampered,root=ROOT)[0]["failure_class"])

    def test_candidate_extraction_receipt_publication_is_no_replace(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "receipt.json"
            receipt = {"schema": "candidate-extraction-receipt-v1", "archive_sha256": "a" * 64, "tree_sha256": "b" * 64}
            candidate.publish_extraction_receipt(receipt, out)
            original = out.read_bytes()
            with self.assertRaisesRegex(ValueError, "target already exists"):
                candidate.publish_extraction_receipt(receipt, out)
            self.assertEqual(original, out.read_bytes())

    def test_candidate_directory_publish_race_and_unsupported_platform_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            temp=Path(td);archive=temp/"safe.zip"
            with zipfile.ZipFile(archive,"w") as zf:zf.writestr("skill/SKILL.md","safe\n")
            destination=temp/"race-destination"
            def competitor(source, target):
                target.mkdir();(target/"competitor.txt").write_text("competitor",encoding="utf-8")
                raise candidate.PublicationError("publication target already exists")
            with mock.patch.object(candidate,"_rename_directory_noreplace",side_effect=competitor):
                with self.assertRaisesRegex(ValueError,"target already exists"):
                    candidate.safe_extract_zip(archive,destination,declared_total_bytes=5,max_total_bytes=32)
            self.assertEqual("competitor",(destination/"competitor.txt").read_text(encoding="utf-8"))
            unsupported=temp/"unsupported"
            with mock.patch.object(candidate,"_rename_directory_noreplace",side_effect=candidate.PublicationError("unsupported platform")):
                with self.assertRaisesRegex(ValueError,"unsupported platform"):
                    candidate.safe_extract_zip(archive,unsupported,declared_total_bytes=5,max_total_bytes=32)
            self.assertFalse(unsupported.exists())


if __name__ == "__main__":
    unittest.main()
