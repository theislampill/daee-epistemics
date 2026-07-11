#!/usr/bin/env python3
"""Five-case causal barrier runner; only deterministic fake execution is implemented."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from check_parallel_dispatch_manifest import chain_dispatch_events, validate_dispatch_manifest
from smoke_matrix_registry import DEFAULT_REGISTRY, ROOT, load_registry

LIVE_CODEX_EXECUTION_IMPLEMENTED = False


class DeterministicFakeRunner:
    """Test-only submit/observe adapter that makes early observation impossible."""
    def __init__(self, results: list[str]):
        if len(results)!=5: raise ValueError("fake runner requires exactly five results")
        self.results=results; self.submitted=[]; self.observation_open=False

    def submit(self, worker: str) -> None:
        if self.observation_open: raise RuntimeError("submit after observation")
        self.submitted.append(worker)

    def open_observation(self) -> None:
        if len(self.submitted)!=5: raise RuntimeError("observation before five submissions")
        self.observation_open=True

    def observe(self, worker: str) -> str:
        if not self.observation_open: raise RuntimeError("early observation")
        return self.results[int(worker[1:])]


def simulate_fake_cycle(results: list[str], *, registry_path: Path | None = None, registry_root: Path | None = None) -> dict:
    runner=DeterministicFakeRunner(results); cases=load_registry(registry_path or DEFAULT_REGISTRY,registry_root or ROOT)["cases"]; workers=[f"w{i}" for i in range(5)]
    bindings=[{"worker":worker,"case_id":case["case_id"],"home":f"homes/{worker}","cache":f"caches/{worker}","run_root":f"runs/{worker}"} for worker,case in zip(workers,cases)]
    events=[*({"event":"worker_ready","worker":row["worker"],"case_id":row["case_id"]} for row in bindings),{"event":"barrier_release"}]
    for row in bindings:
        w=row["worker"];events.append({"event":"request_submit_started","worker":w,"case_id":row["case_id"]});runner.submit(w);events.append({"event":"call_entered_in_flight","worker":w,"case_id":row["case_id"]})
    events.append({"event":"all_five_in_flight"})
    runner.open_observation()
    rows=[]
    for row in bindings:
        w=row["worker"];result=runner.observe(w);rows.append({"worker":w,"case_id":row["case_id"],"result":result,"output_preserved":True});events.append({"event":"terminal_result_observed","worker":w,"case_id":row["case_id"]})
    return {"schema":"daee-smoke-matrix-v1","kind":"dispatch-manifest","protocol":"barrier-five-submit-before-await-v1","expected_workers":5,
            "workers":bindings,"events":chain_dispatch_events(events),"rows":rows,"cold_review_calls":0,
            "observation_finalizer":{"status":"FINALIZED","candidate_status":"CONSUMED_OBSERVED"}}


def _sha256_record(record: dict) -> str:
    return hashlib.sha256((json.dumps(record,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()


def authorize_model_runner(runner: str, *, authorization: dict|None, maturity: dict|None, claim: Path|None) -> None:
    if runner!="codex": return
    if not authorization or not maturity or claim is None: raise PermissionError("MODEL_AUTHORIZATION_REQUIRED: codex requires hash-bound authorization, maturity, and one-use claim")
    exact={"kind":"matrix-authorization","model_runner":"codex","one_use":True,
           "evidence_lane":"package-faithful","candidate_required_state":"READY_UNUSED",
           "reserved_invocations":5,"parallelism":5,
           "parallel_protocol":"barrier-five-submit-before-await-v1",
           "one_shot_policy":"complete-observation","reasoning_effort":"high"}
    if any(authorization.get(key)!=value for key,value in exact.items()):
        raise PermissionError("MODEL_AUTHORIZATION_REQUIRED: invalid or incomplete matrix authorization protocol")
    hashes=("candidate_maturity_sha256","campaign_authorization_sha256","registry_sha256","package_sha256","package_tree_sha256")
    if any(re.fullmatch(r"[a-f0-9]{64}",str(authorization.get(field,""))) is None for field in hashes):
        raise PermissionError("MODEL_AUTHORIZATION_REQUIRED: all external authorization and custody hashes are required")
    if re.fullmatch(r"[a-f0-9]{40}",str(authorization.get("source_commit",""))) is None:
        raise PermissionError("MODEL_AUTHORIZATION_REQUIRED: exact source commit is required")
    for field in ("model","runner_adapter_version","host_application_version","candidate_id","cycle_id"):
        if not isinstance(authorization.get(field),str) or not authorization[field]:
            raise PermissionError(f"MODEL_AUTHORIZATION_REQUIRED: {field} is required")
    if maturity.get("status")!="NO_MODEL_CANDIDATE_MATURE" or maturity.get("candidate_id")!=authorization.get("candidate_id") or authorization.get("candidate_maturity_sha256")!=_sha256_record(maturity):
        raise PermissionError("CANDIDATE_MATURITY_REQUIRED: maturity identity/hash mismatch")
    if authorization.get("cycle_claim_receipt_path")!=str(claim):
        raise PermissionError("MODEL_AUTHORIZATION_REQUIRED: one-use claim path is not authorization-bound")
    claim.parent.mkdir(parents=True,exist_ok=True)
    try: fd=os.open(claim,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError as exc: raise PermissionError("ONE_USE_AUTHORIZATION_CONSUMED: claim already exists") from exc
    with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as handle: json.dump({"authorization_sha256":_sha256_record(authorization)},handle,sort_keys=True);handle.write("\n")


def self_test() -> int:
    manifest=simulate_fake_cycle(["ok"]*5); checks=[("fake barrier",not validate_dispatch_manifest(manifest,5))]
    try: authorize_model_runner("codex",authorization=None,maturity=None,claim=None); checks.append(("codex boundary",False))
    except PermissionError as exc: checks.append(("codex boundary","MODEL_AUTHORIZATION_REQUIRED" in str(exc)))
    for n,o in checks: print(f"  self-test {'PASS' if o else 'FAIL'}: {n}")
    return 0 if all(o for _,o in checks) else 1


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument("--model-runner",choices=("fake","codex"));p.add_argument("--test-only-fake-runner",action="store_true");p.add_argument("--authorization",type=Path);p.add_argument("--candidate-maturity",type=Path);p.add_argument("--one-use-claim",type=Path);p.add_argument("--out",type=Path);p.add_argument("--self-test",action="store_true");a=p.parse_args()
    if a.self_test:return self_test()
    if a.model_runner=="fake":
        if not a.test_only_fake_runner: print(json.dumps({"status":"FAIL","error":"TEST_ONLY_FAKE_RUNNER_FLAG_REQUIRED"}));return 1
        result=simulate_fake_cycle(["ok"]*5)
    elif a.model_runner=="codex":
        if not LIVE_CODEX_EXECUTION_IMPLEMENTED:
            print(json.dumps({"status":"BLOCKED","error":"LIVE_MODEL_EXECUTION_NOT_IMPLEMENTED_OR_AUTHORIZED_IN_BRANCH_10_DETERMINISTIC_LANE"},sort_keys=True));return 2
        auth=json.loads(a.authorization.read_text(encoding="utf-8")) if a.authorization else None; maturity=json.loads(a.candidate_maturity.read_text(encoding="utf-8")) if a.candidate_maturity else None
        try: authorize_model_runner("codex",authorization=auth,maturity=maturity,claim=a.one_use_claim)
        except PermissionError as exc: print(json.dumps({"status":"FAIL","error":str(exc)},sort_keys=True));return 1
        raise AssertionError("live Codex execution implementation flag is inconsistent")
    else:p.error("--model-runner is required")
    payload=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.out:a.out.write_text(payload,encoding="utf-8",newline="\n")
    else:print(payload,end="")
    return 0


if __name__=="__main__":sys.exit(main())
