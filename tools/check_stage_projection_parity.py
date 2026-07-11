#!/usr/bin/env python3
"""Check lossless Stage04-Stage07 activation/lifecycle projection parity."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from stage_projection_contract import projection_diagnostics
from witness_artifact_roles import apply_json_pointer_mutation, json_schema_errors

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "stage-projection-parity"
EXPECTATION_SCHEMA = ROOT / "schema" / "negative-fixture-expectation.schema.json"


def load_fixture_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") == "daee-stage-projection-mutation-v1":
        base_path = ROOT / str(payload["base"])
        base = json.loads(base_path.read_text(encoding="utf-8"))
        return apply_json_pointer_mutation(base, payload["mutation"])
    return payload


def validate_fixture(path: Path) -> dict[str, Any]:
    path = path.resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    payload = load_fixture_payload(path)
    diagnostics = projection_diagnostics(payload)
    compatibility = raw.get("compatibility", "current") if isinstance(raw, dict) else "current"
    return {
        "status": "pass" if not diagnostics else "fail",
        "checker_id": "stage-projection-parity",
        "fixture": str(path.relative_to(ROOT)).replace("\\", "/"),
        "compatibility": compatibility,
        "diagnostics": diagnostics,
        "non_claims": ["structural parity does not establish semantic truth or T_lang uptake"],
    }


def _expectation_errors(fixture: Path, result: dict[str, Any]) -> list[str]:
    expectation_path = fixture.with_name(fixture.stem + ".expectation.json")
    if not expectation_path.is_file():
        return [f"{fixture}: missing same-stem expectation {expectation_path.name}"]
    expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
    expectation_schema = json.loads(EXPECTATION_SCHEMA.read_text(encoding="utf-8"))
    errors = [f"{expectation_path}: {error}" for error in json_schema_errors(expectation, expectation_schema)]
    if expectation.get("fixture") != fixture.name:
        errors.append(f"{expectation_path}: fixture must equal {fixture.name}")
    if expectation.get("expected_checker_id") != "stage-projection-parity":
        errors.append(f"{expectation_path}: expected_checker_id must equal stage-projection-parity")
    if expectation.get("expected_exit_category") != "structural-rejection" or expectation.get("expected_exit_code") != 1:
        errors.append(f"{expectation_path}: expected exit must be structural-rejection/1")
    diagnostics = result.get("diagnostics", [])
    if result.get("status") != "fail" or not diagnostics:
        errors.append(f"{fixture}: expected-invalid fixture unexpectedly passed")
        return errors
    diagnostic = diagnostics[0]
    expected_pairs = {
        "failure_class": expectation.get("expected_failure_class"),
        "failure_subcode": expectation.get("expected_failure_subcode"),
        "earliest_stage": expectation.get("expected_earliest_stage"),
        "downstream_invalidated": expectation.get("expected_downstream_invalidated"),
    }
    for key, expected in expected_pairs.items():
        if diagnostic.get(key) != expected:
            errors.append(f"{fixture}: expected {key}={expected!r}, got {diagnostic.get(key)!r}")
    rendered = json.dumps(diagnostic, sort_keys=True, ensure_ascii=False)
    for marker in expectation.get("required_diagnostic_markers", []):
        if str(marker).lower() not in rendered.lower():
            errors.append(f"{fixture}: required diagnostic marker {marker!r} missing")
    for artifact in expectation.get("forbidden_artifacts", []):
        if (fixture.parent / artifact).exists():
            errors.append(f"{fixture}: forbidden artifact exists: {artifact}")
    return errors


def run_fixture_suite(root: Path = FIXTURE_ROOT) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {"valid": 0, "historical": 0, "invalid": 0}
    for path in sorted((root / "valid").glob("*.json")):
        result = validate_fixture(path)
        if result["status"] != "pass":
            errors.append(f"{path}: expected valid: {json.dumps(result['diagnostics'], ensure_ascii=False)}")
        else:
            counts["valid"] += 1
            if result["compatibility"] != "current":
                counts["historical"] += 1
    for path in sorted((root / "invalid").glob("*.json")):
        if path.name.endswith(".expectation.json"):
            continue
        result = validate_fixture(path)
        errors.extend(_expectation_errors(path, result))
        if result["status"] == "fail":
            counts["invalid"] += 1
    orphan_expectations = []
    for path in (root / "invalid").glob("*.expectation.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not payload.get("fixture") or not (path.parent / payload["fixture"]).is_file():
            orphan_expectations.append(path)
    errors.extend(f"{path}: expectation has no same-stem fixture" for path in orphan_expectations)
    return errors, counts


def self_test() -> int:
    errors, counts = run_fixture_suite()
    if errors:
        print("stage-projection-parity self-test: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("stage-projection-parity self-test: PASS")
    print(json.dumps(counts, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--records", nargs="*", type=Path, default=[])
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.records:
        errors, counts = run_fixture_suite()
        if errors:
            print("stage projection parity: FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print("stage projection parity: PASS")
        print(json.dumps(counts, sort_keys=True))
        return 0
    failed = False
    for path in args.records:
        result = validate_fixture(path)
        failed = failed or result["status"] != "pass"
        if args.explain:
            print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        else:
            print(f"{path}: {result['status'].upper()}")
            for diagnostic in result["diagnostics"]:
                print(f"- {diagnostic['failure_subcode']}: {diagnostic['message']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
