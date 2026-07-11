#!/usr/bin/env python3
"""Assert one external negative expectation against one hash-bound checker verdict."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from contract_validation import PathCustodyError, resolve_repo_path
from validation_registry import (
    EXPECTATION_SCHEMA_REL,
    ROOT,
    Finding,
    hydrate_fixture,
    load_registry,
    materialize_fixture,
    read_json,
    schema_findings,
    validate_verdict,
)

CHECKER_ID = "expected-rejection-assertion"
REQUIRED_EXPECTATION_FIELDS = (
    "schema", "fixture", "kind", "expected_checker_id", "expected_exit_category",
    "expected_exit_code", "expected_earliest_stage", "expected_failure_class",
    "expected_failure_subcode", "expected_downstream_invalidated",
    "required_diagnostic_markers", "forbidden_artifacts", "provenance",
)


def expectation_findings(value: Any) -> list[Finding]:
    findings = schema_findings(value, EXPECTATION_SCHEMA_REL)
    if findings:
        return findings
    assert isinstance(value, dict)
    if value.get("kind") != "invalid-single-signature":
        return [Finding("composite_not_active", "active expectation must be invalid-single-signature", "single-signature")]
    return []


def assert_rejection(expectation: dict[str, Any], verdict: dict[str, Any], registry: dict[str, Any], *, root: Path = ROOT, artifact_root: str | Path | None = None) -> list[Finding]:
    findings = expectation_findings(expectation)
    if findings:
        return findings
    verdict_findings = validate_verdict(verdict, registry, root=root, verify_files=True)
    if verdict_findings:
        return verdict_findings
    checker_id = str(expectation["expected_checker_id"])
    known = {row.get("checker_id") for row in registry.get("checkers", [])}
    if checker_id not in known:
        return [Finding("unknown_checker_id", f"expectation references unknown checker {checker_id}", "unknown-checker")]
    rows = [row for row in verdict.get("checker_results", []) if row.get("checker_id") == checker_id]
    if len(rows) != 1:
        return [Finding("checker_result_cardinality", f"expected exactly one result for {checker_id}, found {len(rows)}", "checker-result-cardinality")]
    row = rows[0]
    if row.get("execution_status") != "completed":
        return [Finding("execution_not_completed", f"checker execution status is {row.get('execution_status')}", "execution-status")]
    if row.get("exit_category") != expectation["expected_exit_category"]:
        return [Finding("wrong_exit_category", f"expected {expectation['expected_exit_category']}, got {row.get('exit_category')}", "exit-category")]
    if row.get("exit_code") != expectation["expected_exit_code"]:
        return [Finding("wrong_exit_code", f"expected {expectation['expected_exit_code']}, got {row.get('exit_code')}", "exit-code")]
    diag = row.get("diagnostic")
    if not isinstance(diag, dict):
        return [Finding("malformed_diagnostic", "checker diagnostic is not an object", "malformed-diagnostic")]
    comparisons = (
        ("earliest_stage", "expected_earliest_stage", "wrong_earliest_stage"),
        ("failure_class", "expected_failure_class", "wrong_failure_class"),
        ("failure_subcode", "expected_failure_subcode", "wrong_failure_subcode"),
    )
    for actual_key, expected_key, failure_class in comparisons:
        if diag.get(actual_key) != expectation[expected_key]:
            return [Finding(failure_class, f"expected {expected_key}={expectation[expected_key]}, got {diag.get(actual_key)}", failure_class.replace("_", "-"))]
    if verdict.get("mutation_fault_id") != expectation["expected_failure_subcode"]:
        return [Finding("different_active_fault", "mutation fault identity does not match expected subcode", "active-fault-mismatch")]
    if set(row.get("downstream_invalidated", [])) != set(expectation["expected_downstream_invalidated"]):
        return [Finding("wrong_downstream_set", "observed downstream invalidation set differs from expectation", "downstream-set")]
    diagnostic_text = " ".join(str(diag.get(key, "")) for key in ("diagnostic_id", "message", "failure_subcode"))
    for marker in expectation["required_diagnostic_markers"]:
        if marker not in diagnostic_text:
            return [Finding("missing_diagnostic_marker", f"missing diagnostic marker {marker!r}", "diagnostic-marker")]
    readback_rows = [item for item in row.get("forbidden_artifact_readback", []) if isinstance(item, dict)]
    readback_paths = [str(item.get("path")) for item in readback_rows]
    if len(readback_paths) != len(set(readback_paths)):
        return [Finding("duplicate_forbidden_readback_path", "forbidden-artifact readback paths must be unique", "forbidden-readback-path")]
    readback = {str(item["path"]): item.get("exists") for item in readback_rows}
    if set(readback) != set(expectation["forbidden_artifacts"]):
        return [Finding("forbidden_artifact_readback_mismatch", "forbidden-artifact readback set differs from expectation", "forbidden-readback")]
    for path, exists in readback.items():
        try:
            base = root if artifact_root is None else resolve_repo_path(root, artifact_root, must_exist=True, expect_dir=True)
            relative = Path(path) if base == root else base.relative_to(root.resolve()) / Path(path)
            resolved = resolve_repo_path(root, relative, must_exist=False)
        except PathCustodyError as exc:
            return [Finding("path_custody", f"forbidden artifact {path}: {exc}", exc.subcode)]
        actual_exists = resolved.exists()
        if bool(exists) or actual_exists:
            return [Finding("forbidden_artifact_exists", f"forbidden artifact exists: {path}", "forbidden-artifact")]
    return []


def _load_verdict(path: str | Path) -> dict[str, Any]:
    return hydrate_fixture(materialize_fixture(path), root=ROOT)


def self_test() -> int:
    from check_validation_registry import _base_verdict, _expectation_for
    registry = load_registry()
    verdict = hydrate_fixture(_base_verdict("04", "act_body_ref", "body-ref-missing"), root=ROOT)
    expectation = _expectation_for(verdict)
    checks = [
        ("right-reason rejection accepted", not assert_rejection(expectation, verdict, registry, root=ROOT)),
        ("required subcode enforced", expectation_findings({k:v for k,v in expectation.items() if k != "expected_failure_subcode"})[0].failure_subcode == "required-field"),
    ]
    copy_verdict = json.loads(json.dumps(verdict))
    copy_verdict["checker_results"][0]["diagnostic"]["earliest_stage"] = "03"
    checks.append(("wrong earliest stage rejected", assert_rejection(expectation, copy_verdict, registry, root=ROOT)[0].failure_class == "wrong_earliest_stage"))
    unknown = json.loads(json.dumps(expectation)); unknown["expected_checker_id"] = "unregistered-fixture-checker"
    checks.append(("unknown checker rejected", assert_rejection(unknown, verdict, registry, root=ROOT)[0].failure_class == "unknown_checker_id"))
    wrong_fault = json.loads(json.dumps(verdict)); wrong_fault["mutation_fault_id"] = "different-fault"
    checks.append(("different active fault rejected", assert_rejection(expectation, wrong_fault, registry, root=ROOT)[0].failure_class == "different_active_fault"))
    wrong_downstream = json.loads(json.dumps(verdict)); wrong_downstream["checker_results"][0]["downstream_invalidated"] = ["05"]
    checks.append(("wrong downstream set rejected", assert_rejection(expectation, wrong_downstream, registry, root=ROOT)[0].failure_class == "wrong_downstream_set"))
    registry_drift = json.loads(json.dumps(verdict)); registry_drift["registry_sha256"] = "0" * 64
    checks.append(("registry hash drift rejected", assert_rejection(expectation, registry_drift, registry, root=ROOT)[0].failure_class == "registry_hash_drift"))
    ok = all(result for _, result in checks)
    for name, result in checks:
        print(f"  self-test {'PASS' if result else 'FAIL'}: {name}")
    print(f"expected rejection self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expectation")
    parser.add_argument("--verdict")
    parser.add_argument("--registry", default="tools/validation-registry.json")
    parser.add_argument("--artifact-root")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.expectation or not args.verdict:
        parser.error("--expectation and --verdict are required unless --self-test is used")
    try:
        expectation_path = resolve_repo_path(ROOT, args.expectation, must_exist=True, expect_file=True)
        verdict_path = resolve_repo_path(ROOT, args.verdict, must_exist=True, expect_file=True)
        expectation = read_json(expectation_path.relative_to(ROOT))
        fixture_path = resolve_repo_path(
            ROOT,
            expectation_path.relative_to(ROOT).parent / str(expectation.get("fixture", "")),
            must_exist=True,
            expect_file=True,
        )
        if fixture_path != verdict_path:
            findings = [Finding("expectation_verdict_mismatch", "expectation fixture is not the supplied verdict", "expectation-verdict")]
        else:
            findings = []
        verdict = _load_verdict(verdict_path.relative_to(ROOT))
        registry = load_registry(args.registry)
        artifact_root = args.artifact_root
        if not findings:
            findings = assert_rejection(expectation, verdict, registry, root=ROOT, artifact_root=artifact_root)
    except PathCustodyError as exc:
        findings = [Finding("path_custody", str(exc), exc.subcode)]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings = [Finding("malformed_json_or_path", str(exc), "malformed-json")]
    if findings:
        finding = findings[0]
        if args.explain:
            print(json.dumps({"checker_id": CHECKER_ID, "earliest_stage": "control-plane", "exit_category": "structural-rejection", "exit_code": 1, "failure_class": finding.failure_class, "failure_subcode": finding.failure_subcode, "message": finding.message}, sort_keys=True))
        else:
            print(f"expected rejection: FAIL [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
        return 1
    print(json.dumps({"checker_id": CHECKER_ID, "status": "PASS"}, sort_keys=True) if args.explain else "expected rejection: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
