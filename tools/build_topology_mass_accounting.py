#!/usr/bin/env python3
"""Build a checker-derived topology mass accounting record."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

from topology_mass_accounting import build_accounting_record, canonical_sha256, validate_accounting

ROOT = Path(__file__).resolve().parents[1]


def build(source: dict) -> dict:
    return build_accounting_record(case_id=source["case_id"], input_sha256=source["input_sha256"], staged_handoff_sha256=source["staged_handoff_sha256"], output_sha256=source["output_sha256"], obligations=source.get("obligations", []), evidence_inventory=source.get("evidence_inventory", []), partition_decisions=source.get("partition_decisions", []), advisory_metrics=source.get("advisory_metrics", {}), authoritative_empty_universe=source.get("authoritative_empty_universe"))


def self_test() -> int:
    content="validated capsule";artifact_hash=hashlib.sha256(content.encode("utf-8")).hexdigest()
    source = {"case_id":"self-test","input_sha256":"1"*64,"staged_handoff_sha256":"2"*64,"output_sha256":"3"*64,"obligations":[{"obligation_id":"O1","kind":"owner_operation","origin_stage":"03","source_ids":["P1","B1"],"allowed_dispositions":["satisfied"],"disposition":"satisfied","evidence_refs":["R1"],"basis":"self-test evidence"}],"evidence_inventory":[{"evidence_id":"R1","evidence_type":"operation_capsule","artifact_id":"OC1","artifact_sha256":artifact_hash,"validator_receipt_id":"VR1"}],"partition_decisions":[],"advisory_metrics":{"output_bytes":0}}
    record = build(source)
    receipt={"receipt_id":"VR1","evidence_id":"R1","artifact_id":"OC1","artifact_sha256":artifact_hash,"evidence_type":"operation_capsule","validator_id":"operation-capsule-contract","verdict":"PASS"};receipt["receipt_sha256"]=canonical_sha256(receipt)
    authority={"source_ids":["P1","B1"],"artifacts":[{"artifact_id":"OC1","content":content,"artifact_sha256":artifact_hash}],"validator_receipts":[receipt]}
    if validate_accounting(record, upstream_obligation_ids=[item["obligation_id"] for item in source["obligations"]], upstream_inventory_sha256=source["staged_handoff_sha256"],evidence_authority=authority,evidence_authority_sha256=canonical_sha256(authority)):
        print(json.dumps({"checker_id":"build-topology-mass-accounting","status":"FAIL"}, sort_keys=True))
        return 1
    print(json.dumps({"checker_id":"build-topology-mass-accounting","status":"PASS"}, sort_keys=True))
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record")
    parser.add_argument("--upstream-inventory", help="independent JSON array or object with obligation_ids")
    parser.add_argument("--evidence-authority", help="independent source/artifact/validator-receipt inventory")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.record:
        parser.error("--record is required")
    if not args.upstream_inventory:
        parser.error("--upstream-inventory is required")
    if not args.evidence_authority:
        parser.error("--evidence-authority is required")
    source_path = Path(args.record)
    if not source_path.is_absolute():
        source_path = ROOT / source_path
    source = json.loads(source_path.read_text(encoding="utf-8"))
    record = build(source)
    upstream_path = Path(args.upstream_inventory)
    if not upstream_path.is_absolute():
        upstream_path = ROOT / upstream_path
    upstream = json.loads(upstream_path.read_text(encoding="utf-8"))
    upstream_ids = upstream if isinstance(upstream, list) else upstream.get("obligation_ids") if isinstance(upstream, dict) else None
    if not isinstance(upstream_ids, list):
        parser.error("--upstream-inventory must contain a JSON array or an obligation_ids array")
    upstream_hash = hashlib.sha256(upstream_path.read_bytes()).hexdigest()
    authority_path=Path(args.evidence_authority)
    if not authority_path.is_absolute(): authority_path=ROOT/authority_path
    authority=json.loads(authority_path.read_text(encoding="utf-8"))
    findings = validate_accounting(record, upstream_obligation_ids=upstream_ids, upstream_inventory_sha256=upstream_hash,evidence_authority=authority,evidence_authority_sha256=canonical_sha256(authority))
    if findings:
        print(json.dumps({"checker_id":"build-topology-mass-accounting","status":"FAIL",**findings[0]}, sort_keys=True))
        return 1
    rendered = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = ROOT / output
        if output.exists():
            print(json.dumps({"checker_id":"build-topology-mass-accounting","status":"FAIL","failure_class":"output-exists","artifact":str(output)}, sort_keys=True))
            return 1
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
