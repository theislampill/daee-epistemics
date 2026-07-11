#!/usr/bin/env python3
"""Prove causal submit-before-observe barriers without timing thresholds."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _err(cls: str, message: str) -> dict[str, str]:
    return {"failure_class": cls, "message": message}


def _event_digest(event: dict) -> str:
    payload={key:value for key,value in event.items() if key!="event_sha256"}
    encoded=(json.dumps(payload,sort_keys=True,separators=(",",":"))+"\n").encode()
    return hashlib.sha256(encoded).hexdigest()


def chain_dispatch_events(events: list[dict]) -> list[dict]:
    """Add a monotonic sequence and predecessor/hash chain to fresh event rows."""
    chained=[]; predecessor=None
    for sequence,event in enumerate(events,start=1):
        row={**event,"sequence":sequence,"predecessor_event_sha256":predecessor}
        row["event_sha256"]=_event_digest(row); predecessor=row["event_sha256"]; chained.append(row)
    return chained


def validate_dispatch_manifest(data: object, expected_workers: int) -> list[dict[str, str]]:
    if not isinstance(data, dict): return [_err("dispatch_shape", "dispatch manifest must be an object")]
    events = data.get("events")
    if not isinstance(events, list): return [_err("dispatch_shape", "events must be an array")]
    expected_protocol = f"barrier-{'five' if expected_workers == 5 else 'ten'}-submit-before-await-v1"
    if data.get("protocol") != expected_protocol or data.get("expected_workers") != expected_workers:
        return [_err("dispatch_protocol", f"expected {expected_protocol} with {expected_workers} workers")]
    workers=data.get("workers")
    if not isinstance(workers,list) or len(workers)!=expected_workers:
        return [_err("dispatch_worker_binding",f"worker inventory must bind exactly {expected_workers} workers to cases")]
    bindings={};model_bindings={}
    for row in workers:
        if not isinstance(row,dict):return [_err("dispatch_worker_binding","worker inventory rows must be objects")]
        worker=row.get("worker");case_id=row.get("case_id")
        if not isinstance(worker,str) or not worker or worker in bindings or not isinstance(case_id,str) or not case_id:
            return [_err("dispatch_worker_binding","worker and case bindings must be nonempty and unique")]
        model_family=row.get("model_family")
        if expected_workers==10 and model_family not in {"GPT","OPUS"}:return [_err("dispatch_worker_binding","paired worker requires GPT or OPUS model_family")]
        bindings[worker]=case_id;model_bindings[worker]=model_family
    identities={(model_bindings[worker],case_id) for worker,case_id in bindings.items()}
    if len(identities)!=expected_workers:return [_err("dispatch_worker_binding","worker model/case bindings must be unique")]
    for field in ("home","cache","run_root"):
        values=[row.get(field) for row in workers]
        if any(not isinstance(value,str) or not value for value in values) or len(set(values))!=expected_workers:
            return [_err("shared_worker_state",f"workers must use isolated unique {field} values; shared {field} is forbidden")]
    predecessor=None
    for sequence,event in enumerate(events,start=1):
        if not isinstance(event,dict):return [_err("dispatch_event","event must be an object")]
        if event.get("sequence")!=sequence:return [_err("dispatch_event_sequence",f"event sequence must be monotonic at {sequence}")]
        if event.get("predecessor_event_sha256")!=predecessor:return [_err("dispatch_event_hash",f"event {sequence} predecessor hash mismatch")]
        if event.get("event_sha256")!=_event_digest(event):return [_err("dispatch_event_hash",f"event {sequence} hash mismatch")]
        predecessor=event["event_sha256"]
    ready:set[str]=set();submitted:set[str]=set();accepted:set[str]=set();released=False;aggregated=False
    provider_stopped = False
    for event in events:
        name = event.get("event"); worker = event.get("worker")
        if worker is not None and (worker not in bindings or event.get("case_id")!=bindings[worker] or event.get("model_family")!=model_bindings[worker]):
            return [_err("dispatch_worker_binding","event worker/case binding does not match inventory")]
        if name == "worker_ready":
            if released: return [_err("sequential_masquerade", f"worker became ready after release; require {expected_workers} ready workers")]
            if not isinstance(worker, str) or worker in ready: return [_err("dispatch_worker_identity", "worker_ready identities must be unique")]
            ready.add(worker)
        elif name == "barrier_release":
            if released or len(ready) != expected_workers:
                return [_err("sequential_masquerade", f"barrier release requires {expected_workers} ready workers")]
            released = True
        elif name == "request_submit_started":
            if not released or worker not in ready or worker in submitted:return [_err("submit_order","request submit requires one released ready worker")]
            submitted.add(worker)
        elif name in {"call_entered_in_flight", "request_accepted"}:
            if provider_stopped:
                return [_err("dispatch_after_provider_stop", "provider auth failure requires stop; later dispatch is forbidden")]
            if worker not in submitted:return [_err("missing_submit_event","acceptance requires that worker's request_submit_started event")]
            if worker in accepted:return [_err("dispatch_acceptance","each worker has exactly one acceptance")]
            accepted.add(worker)
        elif name == "provider_auth_failure":
            provider_stopped = True
        elif name in {"all_five_in_flight","all_ten_in_flight"}:
            expected_aggregate="all_five_in_flight" if expected_workers==5 else "all_ten_in_flight"
            if name!=expected_aggregate or aggregated or len(accepted)!=expected_workers:return [_err("aggregate_order",f"exact {expected_aggregate} requires all {expected_workers} acknowledgments")]
            aggregated=True
        elif name in {"terminal_result_observed", "first_result_awaited"}:
            if not aggregated:return [_err("early_result_observation",f"result observed before all {expected_workers} acceptance events and exact aggregate barrier")]
        else:
            return [_err("dispatch_event", f"unknown dispatch event {name!r}")]
    if len(ready) != expected_workers: return [_err("sequential_masquerade", f"manifest lacks {expected_workers} ready workers")]
    if not released: return [_err("sequential_masquerade", "barrier was not released")]
    if len(submitted)!=expected_workers:return [_err("missing_submit_event",f"manifest lacks {expected_workers} request_submit_started events")]
    if len(accepted) != expected_workers: return [_err("dispatch_acceptance", f"manifest lacks {expected_workers} in-flight acknowledgments")]
    if not aggregated:return [_err("missing_aggregate_barrier",f"manifest lacks exact all_{'five' if expected_workers==5 else 'ten'}_in_flight aggregate")]
    return []


def self_test() -> int:
    workers = [f"w{i}" for i in range(5)]
    inventory=[{"worker":w,"case_id":f"c{i}","home":f"h/{i}","cache":f"c/{i}","run_root":f"r/{i}"} for i,w in enumerate(workers)]
    raw=[*({"event":"worker_ready","worker":w,"case_id":f"c{i}"} for i,w in enumerate(workers)),{"event":"barrier_release"}]
    for i,w in enumerate(workers):raw.extend(({"event":"request_submit_started","worker":w,"case_id":f"c{i}"},{"event":"call_entered_in_flight","worker":w,"case_id":f"c{i}"}))
    raw.extend(({"event":"all_five_in_flight"},{"event":"terminal_result_observed","worker":"w0","case_id":"c0"}))
    good={"protocol":"barrier-five-submit-before-await-v1","expected_workers":5,"workers":inventory,"events":chain_dispatch_events(raw)}
    early_raw=[event for event in raw if event["event"]!="all_five_in_flight"]
    bad={**good,"events":chain_dispatch_events(early_raw)}
    checks = [("five-way barrier", not validate_dispatch_manifest(good, 5)), ("early observation", validate_dispatch_manifest(bad, 5)[0]["failure_class"] == "early_result_observation")]
    for name, ok in checks: print(f"  self-test {'PASS' if ok else 'FAIL'}: {name}")
    return 0 if all(x for _, x in checks) else 1


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--manifest",type=Path); p.add_argument("--expected-workers",type=int,choices=(5,10),default=5); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: return self_test()
    if not a.manifest: p.error("--manifest is required unless --self-test is used")
    errors=validate_dispatch_manifest(json.loads(a.manifest.read_text(encoding="utf-8")),a.expected_workers)
    print(json.dumps({"status":"FAIL" if errors else "PASS","errors":errors},sort_keys=True)); return 1 if errors else 0


if __name__ == "__main__": sys.exit(main())
