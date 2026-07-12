#!/usr/bin/env python3
"""Validate the binding DAEE v0.4.6 architecture-decision ledger."""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from check_andon_closure_ledger import (
    CHECKER as _CLOSURE_CHECKER,
    FIXTURE_SCHEMA,
    Finding,
    ROOT,
    apply_common_operation,
    expectation_problems,
    read_json,
    rel,
    schema_findings,
)
from source_provenance import validate_carrier_document


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


del _CLOSURE_CHECKER
CHECKER = "tools/check_architecture_decision_ledger.py"
CHECKER_ID = "architecture-decision-ledger"
STAGE = "control-plane"
DOWNSTREAM_INVALIDATED = ["control-plane", "candidate-package", "release-action"]
SCHEMA_PATH = ROOT / "schema" / "architecture-decision-ledger.schema.json"
LIVE_LEDGER = ROOT / "docs" / "audits" / "v0.4.6.0-wip-architecture-decisions.json"
CONTRACT_REGISTRY = ROOT / "docs" / "audits" / "v0.4.6.0-wip-andon-contract-registry.json"
FIXTURE_ROOT = ROOT / "tests" / "architecture-decision-ledger"


def materialize(path: Path) -> Any:
    raw = read_json(path)
    if not isinstance(raw, dict) or raw.get("fixture_schema") != FIXTURE_SCHEMA:
        return raw
    if raw.get("base") != rel(LIVE_LEDGER):
        raise ValueError(f"{rel(path)}: fixture base must be {rel(LIVE_LEDGER)}")
    document = copy.deepcopy(read_json(LIVE_LEDGER))
    for operation in raw.get("operations", []):
        if apply_common_operation(document, operation):
            continue
        op = operation.get("op")
        if op == "remove-decision":
            document["decisions"] = [d for d in document["decisions"] if d.get("decision_id") != operation.get("id")]
        elif op == "append-owner":
            decision = next(d for d in document["decisions"] if d.get("decision_id") == operation.get("id"))
            decision["owner_files"].append(operation.get("value"))
        else:
            raise ValueError(f"{rel(path)}: unsupported fixture operation: {operation!r}")
    return document


def validate(document: Any, *, require_status: str | None) -> list[Finding]:
    binding_findings = validate_carrier_document(document, carrier_path=rel(LIVE_LEDGER))
    if binding_findings:
        first = binding_findings[0]
        return [Finding(first.failure_class, first.message)]
    schema = read_json(SCHEMA_PATH)
    errors = schema_findings(document, schema, schema)
    if errors:
        return [Finding("schema_contract", message) for message in errors]
    decisions = [d for d in document["decisions"] if isinstance(d, dict)]
    ids = [str(d.get("decision_id", "")) for d in decisions]
    if len(ids) != len(set(ids)):
        duplicate = next(value for value in ids if ids.count(value) > 1)
        return [Finding("duplicate_decision_id", f"duplicate architecture decision {duplicate}")]
    required_ids = {
        decision_id
        for contract in read_json(CONTRACT_REGISTRY).get("contracts", [])
        for decision_id in contract.get("binding_adr_ids", [])
    }
    missing = sorted(required_ids - set(ids))
    if missing:
        return [Finding("missing_binding_adr", f"binding architecture decision {missing[0]} is missing")]
    required = require_status.upper() if require_status else "ACCEPTED"
    for decision in decisions:
        if decision.get("status") != required:
            return [Finding("rejected_binding_adr", f"{decision.get('decision_id')} has status {decision.get('status')}; required {required}")]

    exclusive = {
        "schema/field-witness.schema.json": "DAEE-ADR-046-005",
        "schema/field-witness-envelope.schema.json": "DAEE-ADR-046-005",
    }
    by_id = {d.get("decision_id"): d for d in decisions}
    for owner_file, owner_id in exclusive.items():
        claimants = sorted(d.get("decision_id") for d in decisions if owner_file in d.get("owner_files", []))
        conflicts = [claimant for claimant in claimants if claimant != owner_id]
        if conflicts:
            return [Finding("conflicting_owner", f"{owner_file} is canonically owned by {owner_id} but also claimed by {conflicts[0]}")]
        if owner_file not in by_id.get(owner_id, {}).get("owner_files", []):
            return [Finding("missing_owner", f"{owner_file} is missing canonical owner {owner_id}")]

    return []


def diag(path: Path, finding: Finding) -> dict[str, Any]:
    return {"artifact": rel(path), "checker": CHECKER, "checker_id": CHECKER_ID, "downstream_invalidated": DOWNSTREAM_INVALIDATED, "earliest_stage": STAGE, "exit_category": "structural-rejection", "exit_code": 1, "failure_class": finding.failure_class, "message": finding.message, "stage": STAGE}


def run_one(path: Path, *, explain: bool, require_status: str | None = None) -> int:
    try:
        findings = validate(materialize(path), require_status=require_status)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        findings = [Finding("fixture_or_json", str(exc))]
    if findings:
        first = findings[0]
        print(json.dumps(diag(path, first), sort_keys=True) if explain else f"architecture decision ledger: FAIL [{first.failure_class}]: {first.message}")
        return 1
    print(json.dumps({"artifact": rel(path), "checker": CHECKER, "status": "PASS"}, sort_keys=True) if explain else f"architecture decision ledger: PASS ({rel(path)})")
    return 0


def self_test() -> int:
    problems: list[str] = []
    valid = sorted((FIXTURE_ROOT / "valid").glob("*.json"))
    invalid = sorted(p for p in (FIXTURE_ROOT / "invalid").glob("*.json") if not p.name.endswith(".expectation.json"))
    for path in valid:
        findings = validate(materialize(path), require_status="ACCEPTED")
        if findings:
            problems.append(f"{rel(path)}: [{findings[0].failure_class}] {findings[0].message}")
    for path in invalid:
        findings = validate(materialize(path), require_status="ACCEPTED")
        if not findings:
            problems.append(f"{rel(path)}: invalid fixture survived")
        else:
            problems.extend(expectation_problems(path, findings[0], checker_id=CHECKER_ID, downstream_invalidated=DOWNSTREAM_INVALIDATED))
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        print(f"architecture decision ledger self-test: FAIL ({len(problems)} problem(s))")
        return 1
    print(f"architecture decision ledger self-test: PASS ({len(valid)} valid, {len(invalid)} invalid)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?")
    parser.add_argument("--ledger")
    parser.add_argument("--require-status")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    selected = args.ledger or args.artifact or rel(LIVE_LEDGER)
    path = Path(selected)
    if not path.is_absolute():
        path = ROOT / path
    return run_one(path.resolve(), explain=args.explain, require_status=args.require_status)


if __name__ == "__main__":
    raise SystemExit(main())
