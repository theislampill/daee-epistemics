#!/usr/bin/env python3
"""Parent-owned deterministic fake canary for optional paired reconvergence."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from check_paired_cross_model_manifest import validate_paired_manifest
from check_parallel_dispatch_manifest import chain_dispatch_events
from smoke_matrix_registry import DEFAULT_REGISTRY, ROOT, load_registry


def simulate_fake_paired_cycle(gpt_results: list[str], opus_results: list[str], *, registry_path: Path | None = None, registry_root: Path | None = None) -> dict:
    if len(gpt_results)!=5 or len(opus_results)!=5: raise ValueError("paired parent requires exact five GPT and five Opus results")
    selected_registry=registry_path or DEFAULT_REGISTRY;cases=load_registry(selected_registry,registry_root or ROOT)["cases"]
    bindings=[*({"worker":f"g{i}","case_id":case["case_id"],"model_family":"GPT","home":f"homes/g{i}","cache":f"caches/g{i}","run_root":f"runs/g{i}"} for i,case in enumerate(cases)),*({"worker":f"o{i}","case_id":case["case_id"],"model_family":"OPUS","home":f"homes/o{i}","cache":f"caches/o{i}","run_root":f"runs/o{i}"} for i,case in enumerate(cases))]
    events=[*({"event":"worker_ready","worker":row["worker"],"case_id":row["case_id"],"model_family":row["model_family"]} for row in bindings),{"event":"barrier_release"}]
    for row in bindings:events.extend(({"event":"request_submit_started","worker":row["worker"],"case_id":row["case_id"],"model_family":row["model_family"]},{"event":"call_entered_in_flight","worker":row["worker"],"case_id":row["case_id"],"model_family":row["model_family"]}))
    events.append({"event":"all_ten_in_flight"})
    events.extend({"event":"terminal_result_observed","worker":row["worker"],"case_id":row["case_id"],"model_family":row["model_family"]} for row in bindings)
    registry_sha=hashlib.sha256(selected_registry.read_bytes()).hexdigest()
    provenance={"source_commit":"a"*40,"package_sha256":"b"*64,"archive_sha256":"c"*64,"extracted_tree_sha256":"d"*64,"build_manifest_sha256":"e"*64,"registry_sha256":registry_sha}
    gpt_candidate={"candidate_id":"fake-gpt-sibling",**provenance};opus_candidate={"candidate_id":"fake-opus-sibling",**provenance}
    gpt_rows=[{"row_id":f"g{i}","model_family":"GPT","case_id":case["case_id"],"worker":f"g{i}","candidate_id":gpt_candidate["candidate_id"]} for i,case in enumerate(cases)]
    opus_rows=[{"row_id":f"o{i}","model_family":"OPUS","case_id":case["case_id"],"worker":f"o{i}","candidate_id":opus_candidate["candidate_id"]} for i,case in enumerate(cases)]
    return {"schema":"daee-cross-model-paired-cycle-v1","kind":"paired-cycle-manifest","parent_cycle_id":"deterministic-fake-parent","post_completion_opus_authorization":"f"*64,"gpt_candidate":gpt_candidate,"opus_candidate":opus_candidate,"gpt_rows":gpt_rows,"opus_rows":opus_rows,"pass_carry_forward":False,"root_recurrences":[],"dispatch_manifest":{"protocol":"barrier-ten-submit-before-await-v1","expected_workers":10,"workers":bindings,"events":chain_dispatch_events(events)}}


def self_test() -> int:
    data=simulate_fake_paired_cycle(["ok"]*5,["ok"]*5); checks=[("fake ten barrier",not validate_paired_manifest(data)),("parent owns ten rows",len(data["gpt_rows"])+len(data["opus_rows"])==10), ("siblings package-identical",data["gpt_candidate"]["package_sha256"]==data["opus_candidate"]["package_sha256"])]
    for n,o in checks:print(f"  self-test {'PASS' if o else 'FAIL'}: {n}")
    return 0 if all(o for _,o in checks) else 1


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument("--test-only-fake-runner",action="store_true");p.add_argument("--post-completion-opus-authorization",type=Path);p.add_argument("--out",type=Path);p.add_argument("--self-test",action="store_true");a=p.parse_args()
    if a.self_test:return self_test()
    if not a.test_only_fake_runner:
        reason="SEPARATE_POST_COMPLETION_OPUS_AUTHORIZATION_REQUIRED" if not a.post_completion_opus_authorization else "LIVE_OPUS_EXECUTION_NOT_IMPLEMENTED_OR_AUTHORIZED_IN_BRANCH_10_DETERMINISTIC_LANE"
        print(json.dumps({"status":"BLOCKED","error":reason},sort_keys=True));return 2
    data=simulate_fake_paired_cycle(["ok"]*5,["ok"]*5);payload=json.dumps(data,indent=2,sort_keys=True)+"\n"
    if a.out:a.out.write_text(payload,encoding="utf-8",newline="\n")
    else:print(payload,end="")
    return 0


if __name__=="__main__":sys.exit(main())
