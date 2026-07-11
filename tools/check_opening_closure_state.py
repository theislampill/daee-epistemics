#!/usr/bin/env python3
"""Check opening-state-v2 and monotonic closure traces."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from closure_state_lib import canonical_universe_sha256, validate_trace

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "opening-closure-state"
CHECKER_ID = "opening-closure-state"
EXPECTATION_FIELDS = {"schema","fixture","kind","expected_checker_id","expected_exit_category","expected_exit_code","expected_earliest_stage","expected_failure_class","expected_downstream_invalidated","required_diagnostic_markers","forbidden_artifacts","provenance"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fixture_upstream_universe(path: Path) -> dict:
    empty_names = {"vacuous-empty-complete.json", "opening-complete-before-execution.json"}
    name = "empty.json" if path.name in empty_names else "nonempty.json"
    return read_json(FIXTURE_ROOT / "upstream" / name)


def diagnostic(path: Path, finding: dict) -> dict:
    return {"artifact":path.as_posix(),"checker_id":CHECKER_ID,"exit_category":"validation-failure","exit_code":1,**finding}


def run_one(path: Path, explain: bool, upstream_universe: dict, upstream_inventory_sha256: str) -> int:
    findings = validate_trace(read_json(path), upstream_universe=upstream_universe, upstream_inventory_sha256=upstream_inventory_sha256)
    if findings:
        payload = diagnostic(path, findings[0])
        print(json.dumps(payload, sort_keys=True) if explain else f"opening/closure state: FAIL [{payload['failure_class']}/{payload['failure_subcode']}]: {payload['message']}")
        return 1
    print(json.dumps({"artifact":path.as_posix(),"checker_id":CHECKER_ID,"status":"PASS"}, sort_keys=True) if explain else f"opening/closure state: PASS ({path})")
    return 0


def self_test() -> int:
    problems: list[str] = []
    valid = sorted((FIXTURE_ROOT / "valid").glob("*.json"))
    invalid = sorted(path for path in (FIXTURE_ROOT / "invalid").glob("*.json") if not path.name.endswith(".expectation.json"))
    for path in valid:
        universe = fixture_upstream_universe(path)
        findings = validate_trace(read_json(path), upstream_universe=universe, upstream_inventory_sha256=canonical_universe_sha256(universe))
        if findings:
            problems.append(f"{path.name}: valid rejected {findings[0]}")
    for path in invalid:
        expectation = read_json(path.with_suffix(".expectation.json"))
        if not EXPECTATION_FIELDS <= set(expectation) or expectation.get("schema") != "daee-negative-fixture-expectation-v1" or expectation.get("kind") != "invalid-single-signature":
            problems.append(f"{path.name}: noncanonical expectation sidecar")
        universe = fixture_upstream_universe(path)
        findings = validate_trace(read_json(path), upstream_universe=universe, upstream_inventory_sha256=canonical_universe_sha256(universe))
        if not findings:
            problems.append(f"{path.name}: invalid survived")
            continue
        payload = diagnostic(path, findings[0])
        checks = {"expected_checker_id":CHECKER_ID,"expected_exit_category":payload["exit_category"],"expected_exit_code":payload["exit_code"],"expected_earliest_stage":payload["earliest_stage"],"expected_failure_class":payload["failure_class"],"expected_failure_subcode":payload["failure_subcode"],"expected_downstream_invalidated":payload["downstream_invalidated"]}
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
    print(f"opening/closure state self-test: PASS ({len(valid)} valid, {len(invalid)} invalid)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?")
    parser.add_argument("--fixture")
    parser.add_argument("--record")
    parser.add_argument("--upstream-inventory", help="independent burden/candidate/owner obligation universe JSON")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    selected = args.fixture or args.record or args.artifact
    if not selected:
        parser.error("fixture/record required unless --self-test")
    if not args.upstream_inventory:
        parser.error("--upstream-inventory is required for closure validation")
    path = Path(selected)
    if not path.is_absolute():
        path = ROOT / path
    upstream_path = Path(args.upstream_inventory)
    if not upstream_path.is_absolute():
        upstream_path = ROOT / upstream_path
    universe = read_json(upstream_path.resolve())
    if not isinstance(universe, dict):
        parser.error("--upstream-inventory must contain a JSON object")
    return run_one(path.resolve(), args.explain, universe, canonical_universe_sha256(universe))


if __name__ == "__main__":
    raise SystemExit(main())
