#!/usr/bin/env python3
"""Check input-pressure-v1 observation and pressure coverage."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from input_observation_units import validate_input_pressure_record

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "input-pressure-coverage"
CHECKER_ID = "input-pressure-coverage"
EARLIEST_STAGE = "02"
DOWNSTREAM = ["03", "04", "05", "06", "07", "08"]
EXPECTATION_FIELDS = {"schema","fixture","kind","expected_checker_id","expected_exit_category","expected_exit_code","expected_earliest_stage","expected_failure_class","expected_downstream_invalidated","required_diagnostic_markers","forbidden_artifacts","provenance"}


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fixture_upstream_source(path: Path) -> str:
    name = "empty.json" if path.name == "empty-input.json" else "alpha-beta.json" if path.name == "source-observation-disappears.json" else "unicode.json" if path.name == "utf8-crlf-quote-nesting.json" else "alpha.json"
    return _read(FIXTURE_ROOT / "upstream" / name)["source_text"]


def diagnostic(path: Path, finding: dict) -> dict:
    return {
        "artifact": path.as_posix(),
        "checker_id": CHECKER_ID,
        "downstream_invalidated": DOWNSTREAM,
        "earliest_stage": EARLIEST_STAGE,
        "exit_category": "validation-failure",
        "exit_code": 1,
        **finding,
    }


def run_one(path: Path, explain: bool, upstream_source_text: str) -> int:
    findings = validate_input_pressure_record(_read(path), upstream_source_text=upstream_source_text)
    if findings:
        payload = diagnostic(path, findings[0])
        print(json.dumps(payload, sort_keys=True) if explain else f"input-pressure coverage: FAIL [{payload['failure_class']}/{payload['failure_subcode']}]: {payload['message']}")
        return 1
    print(json.dumps({"artifact": path.as_posix(), "checker_id": CHECKER_ID, "status": "PASS"}, sort_keys=True) if explain else f"input-pressure coverage: PASS ({path})")
    return 0


def self_test() -> int:
    problems: list[str] = []
    valid = sorted((FIXTURE_ROOT / "valid").glob("*.json"))
    invalid = sorted(path for path in (FIXTURE_ROOT / "invalid").glob("*.json") if not path.name.endswith(".expectation.json"))
    for path in valid:
        findings = validate_input_pressure_record(_read(path), upstream_source_text=fixture_upstream_source(path))
        if findings:
            problems.append(f"{path.name}: valid fixture rejected: {findings[0]}")
    for path in invalid:
        expectation = _read(path.with_suffix(".expectation.json"))
        if not EXPECTATION_FIELDS <= set(expectation) or expectation.get("schema") != "daee-negative-fixture-expectation-v1" or expectation.get("kind") != "invalid-single-signature":
            problems.append(f"{path.name}: noncanonical expectation sidecar")
        findings = validate_input_pressure_record(_read(path), upstream_source_text=fixture_upstream_source(path))
        if not findings:
            problems.append(f"{path.name}: invalid fixture survived")
            continue
        first = findings[0]
        if first["failure_class"] != expectation["expected_failure_class"] or first.get("failure_subcode") != expectation.get("expected_failure_subcode"):
            problems.append(f"{path.name}: wrong reason {first}")
        if expectation["expected_checker_id"] != CHECKER_ID or expectation["expected_earliest_stage"] != EARLIEST_STAGE or expectation["expected_downstream_invalidated"] != DOWNSTREAM:
            problems.append(f"{path.name}: expectation contract mismatch")
        if expectation.get("expected_exit_category") != "validation-failure" or expectation.get("expected_exit_code") != 1:
            problems.append(f"{path.name}: wrong expected exit contract")
        diagnostic_text = json.dumps(diagnostic(path, first), sort_keys=True)
        for marker in expectation["required_diagnostic_markers"]:
            if marker.lower() not in diagnostic_text.lower():
                problems.append(f"{path.name}: missing marker {marker}")
        for forbidden in expectation["forbidden_artifacts"]:
            if any(candidate.name == Path(forbidden).name for candidate in FIXTURE_ROOT.rglob("*")):
                problems.append(f"{path.name}: forbidden artifact exists: {forbidden}")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print(f"input-pressure coverage self-test: PASS ({len(valid)} valid, {len(invalid)} invalid)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?")
    parser.add_argument("--record")
    parser.add_argument("--upstream-source", help="independent JSON object containing source_text")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    selected = args.record or args.artifact
    if not selected:
        parser.error("an artifact/--record is required unless --self-test is used")
    if not args.upstream_source:
        parser.error("--upstream-source is required for record validation")
    path = Path(selected)
    if not path.is_absolute():
        path = ROOT / path
    upstream_path = Path(args.upstream_source)
    if not upstream_path.is_absolute():
        upstream_path = ROOT / upstream_path
    upstream = _read(upstream_path.resolve())
    if not isinstance(upstream, dict) or not isinstance(upstream.get("source_text"), str):
        parser.error("--upstream-source must be a JSON object containing source_text")
    return run_one(path.resolve(), args.explain, upstream["source_text"])


if __name__ == "__main__":
    raise SystemExit(main())
