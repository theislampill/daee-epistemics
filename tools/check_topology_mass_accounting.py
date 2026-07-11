#!/usr/bin/env python3
"""Validate topology-derived mass accounting fixtures and records."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

from topology_mass_accounting import canonical_sha256, validate_accounting

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "topology-mass-accounting"
CHECKER_ID = "topology-mass-accounting"
EXPECTATION_FIELDS = {"schema","fixture","kind","expected_checker_id","expected_exit_category","expected_exit_code","expected_earliest_stage","expected_failure_class","expected_downstream_invalidated","required_diagnostic_markers","forbidden_artifacts","provenance"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fixture_upstream_ids(path: Path) -> list[str]:
    if path.parent.name == "valid":
        upstream_name = "duplicate.json" if path.name == "proved-duplicate-discharge.json" else "nonempty.json" if path.name == "compact-fully-paid.json" else "empty.json"
        return read_json(FIXTURE_ROOT / "upstream" / upstream_name)["obligation_ids"]
    if path.name == "self-rehashed-obligation-omission.json":
        return ["O1", "O2"]
    record = read_json(path)
    return [item["obligation_id"] for item in record.get("obligations", []) if isinstance(item, dict) and isinstance(item.get("obligation_id"), str)]


def fixture_upstream_hash(path: Path) -> str:
    if path.name in {"self-attested-arbitrary-evidence.json","ghost-pressure-burden-source.json"}:
        return read_json(path)["staged_handoff_sha256"]
    if path.parent.name != "valid":
        return "2" * 64
    upstream_name = "duplicate.json" if path.name == "proved-duplicate-discharge.json" else "nonempty.json" if path.name == "compact-fully-paid.json" else "empty.json"
    upstream = FIXTURE_ROOT / "upstream" / upstream_name
    return hashlib.sha256(upstream.read_bytes()).hexdigest()


def fixture_evidence_authority(path: Path):
    record=read_json(path)
    if not record.get("obligations"):
        name="evidence-empty.json"
    elif path.name in {"proved-duplicate-discharge.json","duplicate-without-decision.json"}:
        name="evidence-duplicate.json"
    else:
        name="evidence-compact.json"
    value=read_json(FIXTURE_ROOT/"upstream"/name)
    return value,canonical_sha256(value)


def diagnostic(path: Path, finding: dict) -> dict:
    stage_map = {
        "evidence-inventory-shape": ("08", []),
        "structural-non-claims-missing": ("08", []),
        "vacuous-empty-collapse": ("02", ["03","04","05","06","07","08"]),
    }
    earliest_stage, downstream = stage_map.get(finding.get("failure_subcode"), ("04", ["05","06","07","08"]))
    return {"artifact":path.as_posix(),"checker_id":CHECKER_ID,"exit_category":"validation-failure","exit_code":1,"earliest_stage":earliest_stage,"downstream_invalidated":downstream,**finding}


def run_one(path: Path, explain: bool, upstream_obligation_ids: list[str], upstream_inventory_sha256: str, evidence_authority: dict, evidence_authority_sha256: str) -> int:
    findings = validate_accounting(read_json(path), upstream_obligation_ids=upstream_obligation_ids, upstream_inventory_sha256=upstream_inventory_sha256,evidence_authority=evidence_authority,evidence_authority_sha256=evidence_authority_sha256)
    if findings:
        payload = diagnostic(path, findings[0])
        print(json.dumps(payload, sort_keys=True) if explain else f"topology mass accounting: FAIL [{payload['failure_class']}/{payload['failure_subcode']}]: {payload['message']}")
        return 1
    print(json.dumps({"artifact":path.as_posix(),"checker_id":CHECKER_ID,"status":"PASS"}, sort_keys=True) if explain else f"topology mass accounting: PASS ({path})")
    return 0


def self_test() -> int:
    problems: list[str] = []
    valid = sorted((FIXTURE_ROOT / "valid").glob("*.json"))
    invalid = sorted(path for path in (FIXTURE_ROOT / "invalid").glob("*.json") if not path.name.endswith(".expectation.json"))
    for path in valid:
        authority,digest=fixture_evidence_authority(path)
        findings = validate_accounting(read_json(path), upstream_obligation_ids=fixture_upstream_ids(path), upstream_inventory_sha256=fixture_upstream_hash(path),evidence_authority=authority,evidence_authority_sha256=digest)
        if findings:
            problems.append(f"{path.name}: valid rejected {findings[0]}")
    for path in invalid:
        expectation_path = path.with_suffix(".expectation.json")
        expectation = read_json(expectation_path)
        if not EXPECTATION_FIELDS <= set(expectation) or expectation.get("schema") != "daee-negative-fixture-expectation-v1" or expectation.get("kind") != "invalid-single-signature":
            problems.append(f"{path.name}: noncanonical expectation sidecar")
        authority,digest=fixture_evidence_authority(path)
        findings = validate_accounting(read_json(path), upstream_obligation_ids=fixture_upstream_ids(path), upstream_inventory_sha256=fixture_upstream_hash(path),evidence_authority=authority,evidence_authority_sha256=digest)
        if not findings:
            problems.append(f"{path.name}: invalid survived")
            continue
        payload = diagnostic(path, findings[0])
        checks = {
            "expected_checker_id": CHECKER_ID,
            "expected_exit_category": payload["exit_category"],
            "expected_exit_code": payload["exit_code"],
            "expected_earliest_stage": payload["earliest_stage"],
            "expected_failure_class": payload["failure_class"],
            "expected_failure_subcode": payload["failure_subcode"],
            "expected_downstream_invalidated": payload["downstream_invalidated"],
        }
        for key, actual in checks.items():
            if expectation.get(key) != actual:
                problems.append(f"{path.name}: {key} expected {expectation.get(key)!r}, actual {actual!r}")
        rendered = json.dumps(payload, sort_keys=True).lower()
        for marker in expectation["required_diagnostic_markers"]:
            if marker.lower() not in rendered:
                problems.append(f"{path.name}: missing marker {marker}")
        for forbidden in expectation["forbidden_artifacts"]:
            if any(candidate.name == Path(forbidden).name for candidate in FIXTURE_ROOT.rglob("*")):
                problems.append(f"{path.name}: forbidden artifact exists: {forbidden}")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print(f"topology mass accounting self-test: PASS ({len(valid)} valid, {len(invalid)} invalid)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?")
    parser.add_argument("--record")
    parser.add_argument("--upstream-inventory", help="independent JSON array or object with obligation_ids")
    parser.add_argument("--evidence-authority", help="independent source/artifact/validator-receipt inventory")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    selected = args.record or args.artifact
    if not selected:
        parser.error("record required unless --self-test")
    if not args.upstream_inventory:
        parser.error("--upstream-inventory is required for record validation")
    if not args.evidence_authority:
        parser.error("--evidence-authority is required for record validation")
    path = Path(selected)
    if not path.is_absolute():
        path = ROOT / path
    upstream_path = Path(args.upstream_inventory)
    if not upstream_path.is_absolute():
        upstream_path = ROOT / upstream_path
    upstream = read_json(upstream_path.resolve())
    upstream_ids = upstream if isinstance(upstream, list) else upstream.get("obligation_ids") if isinstance(upstream, dict) else None
    if not isinstance(upstream_ids, list):
        parser.error("--upstream-inventory must contain a JSON array or an obligation_ids array")
    upstream_hash = hashlib.sha256(upstream_path.resolve().read_bytes()).hexdigest()
    authority_path=Path(args.evidence_authority)
    if not authority_path.is_absolute(): authority_path=ROOT/authority_path
    authority=read_json(authority_path.resolve())
    return run_one(path.resolve(), args.explain, upstream_ids, upstream_hash,authority,canonical_sha256(authority))


if __name__ == "__main__":
    raise SystemExit(main())
