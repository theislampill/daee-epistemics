#!/usr/bin/env python3
"""Validate registry coverage, hash-bound verdicts, and A11 fixture inventories."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from assert_expected_rejection import assert_rejection
from contract_validation import PathCustodyError
from validation_registry import (
    ROOT, Finding, hydrate_fixture, load_registry, materialize_fixture,
    profile_map, read_json, scan_anti_bank, validate_registry, validate_verdict,
)

CHECKER_ID = "validation-registry"
DOWNSTREAM = ["candidate-package", "paid-dispatch", "promotion"]


def _base_verdict(stage: str, failure_class: str, subcode: str) -> dict[str, Any]:
    return {
        "schema": "daee-checker-replay-verdict-v1", "verdict_id": f"fixture-{subcode}",
        "source_commit": "6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c", "selected_profile": "advisory",
        "registry_path": "tools/validation-registry.json", "registry_sha256": "AUTO",
        "launch": {"started_at": "2026-07-10T00:00:00Z", "argv_sha256": "1" * 64, "record_sha256": "4" * 64},
        "completion": {"finished_at": "2026-07-10T00:00:01Z", "duration_ms": 1, "record_sha256": "5" * 64},
        "artifacts": [
            {"role": "input", "artifact_type": "input-output-pair", "path": "tests/validation-integrity/artifacts/input.txt", "sha256": "AUTO"},
            {"role": "output", "artifact_type": "output-md", "path": "tests/validation-integrity/artifacts/output.md", "sha256": "AUTO"},
        ],
        "checker_results": [{
            "checker_id": "manual-smoke-render-contract", "tool_path": "tools/check_manual_smoke_render_contract.py", "tool_sha256": "AUTO",
            "artifact_type": "output-md", "artifact_sha256": "AUTO", "execution_status": "completed",
            "exit_category": "structural-rejection", "exit_code": 1, "timeout": False, "crash": False, "usage_error": False, "malformed_diagnostic": False,
            "diagnostic": {"diagnostic_id": f"fixture-{subcode}", "earliest_stage": stage, "failure_class": failure_class, "failure_subcode": subcode, "message": f"{stage} {failure_class} {subcode}"},
            "stdout_sha256": "2" * 64, "stderr_sha256": "3" * 64,
            "downstream_invalidated": [str(i).zfill(2) for i in range(int(stage) + 1, 9)] if stage.isdigit() else DOWNSTREAM,
            "forbidden_artifact_readback": [{"path": "tests/validation-integrity/artifacts/forbidden-promotion.json", "exists": False}],
            "expectation_status": "REJECTED_EXPECTED",
        }],
        "aggregate_status": "FAIL_STRUCTURAL", "mutation_fault_id": subcode,
        "structural_non_claims": ["structural rejection only", "not semantic truth", "not model behavior"],
    }


def _expectation_for(verdict: dict[str, Any]) -> dict[str, Any]:
    row = verdict["checker_results"][0]
    diag = row["diagnostic"]
    return {
        "schema": "daee-negative-fixture-expectation-v1", "fixture": "synthetic-verdict.json", "kind": "invalid-single-signature",
        "expected_checker_id": row["checker_id"], "expected_exit_category": "structural-rejection", "expected_exit_code": 1,
        "expected_earliest_stage": diag["earliest_stage"], "expected_failure_class": diag["failure_class"], "expected_failure_subcode": diag["failure_subcode"],
        "expected_downstream_invalidated": row["downstream_invalidated"], "required_diagnostic_markers": [diag["failure_subcode"]],
        "forbidden_artifacts": ["tests/validation-integrity/artifacts/forbidden-promotion.json"], "provenance": "A11 topic-neutral self-test",
    }


def _case_findings(case_id: str, registry: dict[str, Any]) -> list[Finding]:
    if case_id == "right-reason-stage04":
        verdict = hydrate_fixture(_base_verdict("04", "act_body_ref", "body-ref-missing"), root=ROOT)
        return assert_rejection(_expectation_for(verdict), verdict, registry, root=ROOT)
    if case_id == "right-reason-stage07":
        verdict = hydrate_fixture(_base_verdict("07", "public-projection", "projection-body-missing"), root=ROOT)
        return assert_rejection(_expectation_for(verdict), verdict, registry, root=ROOT)
    verdict = _base_verdict("04", "act_body_ref", "body-ref-missing")
    expected_rejection = _expectation_for(verdict)
    if case_id == "wrong-earliest-stage": verdict["checker_results"][0]["diagnostic"]["earliest_stage"] = "03"
    elif case_id == "wrong-failure-class": verdict["checker_results"][0]["diagnostic"]["failure_class"] = "owner-route"
    elif case_id == "wrong-failure-subcode":
        verdict["checker_results"][0]["diagnostic"]["failure_subcode"] = "different-fault"
        verdict["mutation_fault_id"] = "different-fault"
    elif case_id == "exit-1-usage-error": verdict["checker_results"][0].update({"exit_category":"usage-error", "usage_error":True, "diagnostic":None})
    elif case_id == "exit-1-crash": verdict["checker_results"][0].update({"execution_status":"crashed", "exit_category":"crash", "crash":True, "diagnostic":None})
    elif case_id == "timeout": verdict["checker_results"][0].update({"execution_status":"timeout", "exit_category":"timeout", "exit_code":None, "timeout":True, "diagnostic":None})
    elif case_id == "malformed-diagnostic": verdict["checker_results"][0].update({"malformed_diagnostic":True, "diagnostic":None})
    elif case_id == "unregistered-checker":
        mutated = copy.deepcopy(registry)
        mutated["checkers"] = [row for row in mutated["checkers"] if row.get("checker_id") != "act-surface-syntax"]
        return [f for f in validate_registry(mutated, root=ROOT, scan_repo=True) if f.failure_class == "unregistered_output_checker"]
    elif case_id == "required-not-run": verdict.update({"selected_profile":"captured-output-structural", "checker_results":[]})
    elif case_id == "verdict-output-hash-drift": verdict["artifacts"][1]["sha256"] = "0" * 64
    elif case_id == "checker-source-hash-drift": verdict["checker_results"][0]["tool_sha256"] = "0" * 64
    elif case_id == "forbidden-artifact-exists":
        verdict["checker_results"][0]["forbidden_artifact_readback"] = [{"path":"tests/validation-integrity/artifacts/input.txt", "exists":True}]
    elif case_id == "private-scorecard-list":
        mutated = copy.deepcopy(registry)
        mutated["consumers"] = [{"consumer_id":"fixture-scorecard","source_path":"tests/validation-integrity/helpers/private_scorecard_consumer.py","profile_id":"scorecard","policy_source":"legacy-private-list"}]
        return [f for f in validate_registry(mutated, root=ROOT, scan_repo=True) if f.failure_class == "private_consumer_battery"]
    else: return [Finding("unknown_fixture", f"unknown validation-integrity case {case_id}", "unknown-fixture")]
    verdict = hydrate_fixture(verdict, root=ROOT)
    if case_id in {"wrong-earliest-stage", "wrong-failure-class", "wrong-failure-subcode"}:
        return assert_rejection(expected_rejection, verdict, registry, root=ROOT)
    return validate_verdict(verdict, registry, root=ROOT, verify_files=True)


EXPECTED_INVALID_CLASSES = {
    "wrong-earliest-stage": "wrong_earliest_stage", "wrong-failure-class": "wrong_failure_class", "wrong-failure-subcode": "wrong_failure_subcode",
    "exit-1-usage-error": "usage_error_not_rejection", "exit-1-crash": "infrastructure_not_rejection", "timeout": "infrastructure_not_rejection",
    "malformed-diagnostic": "malformed_diagnostic", "unregistered-checker": "unregistered_output_checker", "required-not-run": "profile_required_not_run",
    "verdict-output-hash-drift": "verdict_output_hash_drift", "checker-source-hash-drift": "checker_source_hash_drift",
    "forbidden-artifact-exists": "forbidden_artifact_exists", "private-scorecard-list": "private_consumer_battery",
}


def run_fixture_inventory(root: Path, inventory: dict[str, Any]) -> tuple[list[str], tuple[int, int]]:
    problems: list[str] = []
    registry = load_registry()
    valid = list(inventory.get("valid", [])); invalid = list(inventory.get("invalid", []))
    for case_id in valid:
        path = root / "valid" / f"{case_id}.json"
        if not path.is_file(): problems.append(f"missing valid fixture {path}"); continue
        findings = _case_findings(case_id, registry)
        if findings: problems.append(f"{case_id}: [{findings[0].failure_class}] {findings[0].message}")
    for case_id in invalid:
        path = root / "invalid" / f"{case_id}.json"; exp = path.with_suffix(".expectation.json")
        if not path.is_file(): problems.append(f"missing invalid fixture {path}"); continue
        if not exp.is_file(): problems.append(f"missing expectation {exp}"); continue
        expectation = read_json(exp.relative_to(ROOT))
        if "expected_failure_subcode" not in expectation: problems.append(f"{case_id}: expectation lacks expected_failure_subcode")
        findings = _case_findings(case_id, registry)
        expected = EXPECTED_INVALID_CLASSES[case_id]
        if not findings: problems.append(f"{case_id}: invalid fixture survived")
        elif findings[0].failure_class != expected: problems.append(f"{case_id}: expected {expected}, got {findings[0].failure_class}")
    scan_paths = [path.relative_to(ROOT) for path in root.rglob("*.json")]
    scan_paths.extend((Path("tools/validation_registry.py"), Path("tools/check_validation_registry.py")))
    problems.extend(scan_anti_bank(scan_paths))
    return problems, (len(valid), len(invalid))


def self_test() -> int:
    inventory_root = ROOT / "tests" / "validation-integrity"
    inventory = read_json((inventory_root / "inventory.json").relative_to(ROOT))
    problems, counts = run_fixture_inventory(inventory_root, inventory)
    registry = load_registry()
    structural_findings = validate_registry(registry, root=ROOT, scan_repo=False)
    problems.extend(f"registry: [{f.failure_class}] {f.message}" for f in structural_findings)
    live = validate_registry(registry, root=ROOT, scan_repo=True)
    unexpected_live = [f for f in live if f.failure_class != "private_consumer_battery"]
    problems.extend(f"live: [{f.failure_class}] {f.message}" for f in unexpected_live)
    if not any(f.failure_class == "private_consumer_battery" for f in live):
        problems.append("live scan failed to detect read-only legacy private consumers")
    mutations = []
    duplicate = copy.deepcopy(registry); duplicate["checkers"].append(copy.deepcopy(duplicate["checkers"][0])); mutations.append(("duplicate_checker_id", duplicate, False))
    missing_tool = copy.deepcopy(registry); missing_tool["checkers"][0]["source_path"] = "tools/missing_validation_tool.py"; mutations.append(("nonexistent_checker_tool", missing_tool, False))
    deprecated = copy.deepcopy(registry); deprecated["checkers"][0]["deprecated_aliases"] = ["old-checker-name"]; deprecated["profiles"][0]["requirements"][0]["checker_id"] = "old-checker-name"; mutations.append(("deprecated_checker_alias", deprecated, False))
    missing_consumer = copy.deepcopy(registry); missing_consumer["consumers"] = [{"consumer_id":"missing","source_path":"tools/missing_consumer.py","profile_id":"scorecard","policy_source":"registry"}]; mutations.append(("unregistered_consumer", missing_consumer, True))
    for expected_class, document, scan_repo in mutations:
        found = validate_registry(document, root=ROOT, scan_repo=scan_repo)
        if not any(f.failure_class == expected_class for f in found):
            problems.append(f"registry mutation failed to detect {expected_class}")
    if problems:
        for problem in problems: print(f"FAIL: {problem}")
        print(f"validation registry self-test: FAIL ({len(problems)} problem(s))")
        return 1
    print(f"validation registry self-test: PASS ({counts[0]} valid, {counts[1]} invalid; legacy consumers detected and blocked)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="tools/validation-registry.json")
    parser.add_argument("--verdict")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--registrations-only", action="store_true")
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test: return self_test()
    try:
        registry = load_registry(args.registry)
        if args.verdict:
            verdict = hydrate_fixture(materialize_fixture(args.verdict), root=ROOT)
            findings = validate_verdict(verdict, registry, root=ROOT, verify_files=True)
        else:
            findings = validate_registry(registry, root=ROOT, scan_repo=True)
            if args.registrations_only:
                findings = [finding for finding in findings if finding.failure_class != "private_consumer_battery"]
    except PathCustodyError as exc:
        findings = [Finding("path_custody", str(exc), exc.subcode)]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings = [Finding("malformed_json_or_path", str(exc), "malformed-json")]
    if findings:
        first = findings[0]
        payload = {"checker_id":CHECKER_ID,"earliest_stage":"control-plane","exit_category":"structural-rejection","exit_code":1,"failure_class":first.failure_class,"failure_subcode":first.failure_subcode,"message":first.message,"finding_count":len(findings)}
        print(json.dumps(payload, sort_keys=True) if args.explain else f"validation registry: FAIL [{first.failure_class}/{first.failure_subcode}] ({len(findings)} finding(s)): {first.message}")
        return 1
    payload = {"checker_id":CHECKER_ID,"status":"PASS","profiles":sorted(profile_map(registry)),"registered_checkers":len(registry.get("checkers", []))}
    print(json.dumps(payload, sort_keys=True) if args.explain else f"validation registry: PASS ({payload['registered_checkers']} registered checkers, {len(payload['profiles'])} profiles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
