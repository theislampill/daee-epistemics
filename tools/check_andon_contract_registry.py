#!/usr/bin/env python3
"""Validate A01-A16 control-plane ownership, milestones, plans, ADRs, and cases."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from check_andon_closure_ledger import (
    FIXTURE_SCHEMA,
    Finding,
    ROOT,
    _cycle,
    _duplicates,
    apply_common_operation,
    expectation_problems,
    read_json,
    rel,
)
from source_provenance import validate_carrier_document


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


CHECKER = "tools/check_andon_contract_registry.py"
CHECKER_ID = "andon-contract-registry"
STAGE = "control-plane"
DOWNSTREAM_INVALIDATED = ["control-plane", "candidate-package", "release-action"]
LIVE_REGISTRY = ROOT / "docs" / "audits" / "v0.4.6.0-wip-andon-contract-registry.json"
LIVE_ADR = ROOT / "docs" / "audits" / "v0.4.6.0-wip-architecture-decisions.json"
LIVE_CLOSURE = ROOT / "docs" / "audits" / "v0.4.6.0-wip-andon-closure-ledger.json"
MIGRATION_LEDGER = ROOT / "docs" / "audits" / "v0.4.6.0-wip-state-capsule-v2-migration-ledger.json"
PLAN_ROOT = ROOT / "docs" / "audits" / "evidence" / "v0.4.6.0-b10" / "plans"
FIXTURE_ROOT = ROOT / "tests" / "andon-contract-registry"
_TRACKED_PLAN_CACHE: dict[str, bool] = {}
SOURCE_BINDING_OWNER_PATHS = {
    "owned_schema_paths": ("schema/source-binding.schema.json",),
    "owned_tool_paths": ("tools/source_provenance.py", "tools/check_source_provenance.py"),
    "owned_test_paths": (
        "tests/source-provenance/contract-cases.json",
        "tests/source-provenance/test_contract.py",
    ),
}
CI_READBACK_OWNER_PATHS = {
    "owned_schema_paths": ("schema/ci-readback.schema.json",),
    "owned_tool_paths": (
        "tools/check_ci_readback.py",
        "tools/write_linux_a01_evidence.py",
        "tools/write_task7_deterministic_evidence.py",
        "tools/sanitized_python_bootstrap.py",
        "tools/run_no_model_preflight.py",
        "tools/run_local_ci.py",
    ),
    "owned_test_paths": ("tests/ci-readback/test_contract.py",),
}
CANDIDATE_CUSTODY_OWNER_PATHS = {
    "owned_schema_paths": ("schema/smoke-matrix.schema.json",),
    "owned_tool_paths": (
        "tools/artifact_tree.py",
        "tools/build_candidate_package_record.py",
        "tools/check_smoke_matrix_manifest.py",
    ),
    "owned_test_paths": (
        "tests/artifact-tree/test_contract.py",
        "tests/candidate-build/test_contract.py",
        "tests/smoke-matrix/reviewed-five-smoke-protocol.json",
        "tests/smoke-matrix/test_protocol.py",
    ),
}
CANDIDATE_MATURITY_OWNER_PATHS = {
    "owned_schema_paths": (
        "schema/no-model-candidate-maturity.schema.json",
        "schema/evidence-retention-manifest.schema.json",
    ),
    "owned_tool_paths": (
        "tools/build_no_model_candidate_maturity_verdict.py",
        "tools/check_no_model_candidate_maturity.py",
        "tools/export_cycle_evidence_bundle.py",
        "tools/check_evidence_retention_manifest.py",
    ),
    "owned_test_paths": (
        "tests/no-model-candidate-maturity/test_contract.py",
        "tests/no-model-candidate-maturity/test_candidate_maturity.py",
        "tests/evidence-retention/test_contract.py",
    ),
}
REVIEWED_CAMPAIGN_OWNER_PATHS = {
    "owned_tool_paths": (
        "tools/reviewed_campaign_orchestrator.py",
        "tools/run_reviewed_producer_cohort.py",
        "tools/run_reviewed_cold_review_cohort.py",
    ),
    "owned_test_paths": ("tests/reviewed-campaign-orchestration/test_contract.py",),
}


def materialize(path: Path, decision_path: Path) -> tuple[Any, Any, dict[str, Any]]:
    raw = read_json(path)
    registry = copy.deepcopy(read_json(LIVE_REGISTRY))
    decisions = copy.deepcopy(read_json(decision_path))
    context: dict[str, Any] = {}
    if not isinstance(raw, dict) or raw.get("fixture_schema") != FIXTURE_SCHEMA:
        return raw, decisions, context
    if raw.get("base") != rel(LIVE_REGISTRY):
        raise ValueError(f"{rel(path)}: fixture base must be {rel(LIVE_REGISTRY)}")
    for operation in raw.get("operations", []):
        if apply_common_operation(registry, operation):
            continue
        op = operation.get("op")
        if op == "duplicate-contract":
            contract = next(c for c in registry["contracts"] if c.get("andon_id") == operation.get("id"))
            registry["contracts"].append(copy.deepcopy(contract))
        elif op == "set-decision-status":
            decision = next(d for d in decisions["decisions"] if d.get("decision_id") == operation.get("id"))
            decision["status"] = operation.get("value")
        elif op == "set-materialized-cases":
            context["materialized_cases"] = copy.deepcopy(operation.get("value"))
        elif op == "remove-owned-path":
            contract = next(c for c in registry["contracts"] if c.get("andon_id") == operation.get("id"))
            field = str(operation.get("field", ""))
            contract[field] = [value for value in contract.get(field, []) if value != operation.get("value")]
        else:
            raise ValueError(f"{rel(path)}: unsupported fixture operation: {operation!r}")
    return registry, decisions, context


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_plan_path(
    andon_id: str,
    filename: Any,
    *,
    plan_root: Path = PLAN_ROOT,
) -> tuple[Path | None, Finding | None]:
    if not isinstance(filename, str) or not filename.strip():
        return None, Finding(
            "plan_evidence_not_portable",
            f"{andon_id} plan_filename must name repository-relative tracked evidence",
        )
    relative = Path(filename)
    if relative.is_absolute() or len(relative.parts) != 1 or ".." in relative.parts:
        return None, Finding(
            "plan_evidence_not_portable",
            f"{andon_id} plan_filename {filename} is not repository-relative tracked evidence",
        )
    try:
        resolved_root = plan_root.resolve()
        resolved_root.relative_to(ROOT.resolve())
    except ValueError:
        return None, Finding(
            "plan_evidence_not_portable",
            f"{andon_id} plan root {plan_root} is outside repository-relative tracked evidence",
        )
    plan = (resolved_root / relative).resolve()
    try:
        repository_path = plan.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None, Finding(
            "plan_evidence_not_portable",
            f"{andon_id} plan_filename {filename} escapes repository-relative tracked evidence",
        )
    if not plan.is_file():
        return None, Finding("stale_plan_filename", f"{andon_id} plan {filename} not found")
    tracked = _TRACKED_PLAN_CACHE.get(repository_path)
    if tracked is None:
        check = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", repository_path],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        tracked = check.returncode == 0
        _TRACKED_PLAN_CACHE[repository_path] = tracked
    if not tracked:
        return None, Finding(
            "plan_evidence_not_portable",
            f"{andon_id} plan {repository_path} is local-only; plan_filename must resolve to repository-relative tracked evidence",
        )
    return plan, None


def _owned_duplicates(contracts: list[dict[str, Any]], field: str) -> tuple[str, list[str]] | None:
    owners: dict[str, list[str]] = {}
    for contract in contracts:
        for owned in contract.get(field, []):
            owners.setdefault(owned, []).append(contract.get("andon_id"))
    for owned in sorted(owners):
        if len(owners[owned]) > 1:
            return owned, sorted(owners[owned])
    return None


def _case_ids_from_file(path: Path) -> list[str] | None:
    if not path.exists():
        return None
    payload = read_json(path)
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list):
        return []
    return [case.get("case_id") for case in cases if isinstance(case, dict)]


def validate(registry: Any, decisions: Any, context: dict[str, Any]) -> list[Finding]:
    binding_findings = validate_carrier_document(registry, carrier_path=rel(LIVE_REGISTRY))
    if binding_findings:
        first = binding_findings[0]
        return [Finding(first.failure_class, first.message)]
    if not isinstance(registry, dict) or not isinstance(registry.get("contracts"), list):
        return [Finding("registry_contract", "contracts array is required")]
    contracts = [c for c in registry["contracts"] if isinstance(c, dict)]
    ids = [str(c.get("andon_id", "")) for c in contracts]
    duplicates = _duplicates(ids)
    if duplicates:
        return [Finding("duplicate_andon_id", f"duplicate ANDON ownership row {duplicates[0]}")]
    if set(ids) != set(registry.get("required_andon_ids", [])):
        return [Finding("andon_set_mismatch", "contract ANDON IDs do not equal required_andon_ids")]
    milestones: dict[str, list[str]] = {}
    all_milestone_ids: list[str] = []
    for contract in contracts:
        for milestone in contract.get("milestones", []):
            milestone_id = milestone.get("milestone_id")
            all_milestone_ids.append(milestone_id)
            milestones[milestone_id] = list(milestone.get("dependencies", []))
    duplicate_milestones = _duplicates(all_milestone_ids)
    if duplicate_milestones:
        return [Finding("duplicate_milestone_id", f"duplicate milestone ownership {duplicate_milestones[0]}")]

    for field, failure_class in (
        ("owned_schema_paths", "duplicate_schema_owner"),
        ("owned_tool_paths", "duplicate_tool_owner"),
        ("owned_test_paths", "duplicate_test_owner"),
    ):
        duplicate = _owned_duplicates(contracts, field)
        if duplicate:
            owned, owners = duplicate
            return [Finding(failure_class, f"{owned} has competing owners {', '.join(owners)}")]

    for milestone_id, dependencies in milestones.items():
        for dependency in dependencies:
            if dependency not in milestones:
                return [Finding("dangling_dependency", f"{milestone_id} depends on missing {dependency}")]
    cycle = _cycle(milestones)
    if cycle:
        return [Finding("milestone_cycle", f"milestone cycle {' -> '.join(cycle)}")]

    a16 = next((c for c in contracts if c.get("andon_id") == "A16"), None)
    if not a16:
        return [Finding("missing_a16_owner", "A16 contract is required")]
    a14 = next((c for c in contracts if c.get("andon_id") == "A14"), None)
    if not a14:
        return [Finding("missing_a14_owner", "A14 contract is required")]
    for field, required_paths in SOURCE_BINDING_OWNER_PATHS.items():
        registered = a16.get(field, [])
        for required_path in required_paths:
            if required_path not in registered:
                return [
                    Finding(
                        "source_binding_owner_registration",
                        f"A16 {field} must register tracked-binding owner {required_path}",
                    )
                ]
            if not (ROOT / required_path).is_file():
                return [
                    Finding(
                        "source_binding_owner_path_missing",
                        f"A16 registered tracked-binding owner path does not exist: {required_path}",
                    )
                ]
    for field, required_paths in CI_READBACK_OWNER_PATHS.items():
        registered = a16.get(field, [])
        for required_path in required_paths:
            if required_path not in registered:
                return [
                    Finding(
                        "ci_readback_owner_registration",
                        f"A16 {field} must register CI-readback owner {required_path}",
                    )
                ]
    for owner, family, failure_class, label in (
        (a14, CANDIDATE_CUSTODY_OWNER_PATHS, "candidate_custody_owner_registration", "candidate-custody"),
        (a16, CANDIDATE_MATURITY_OWNER_PATHS, "candidate_maturity_owner_registration", "candidate-maturity"),
        (a16, REVIEWED_CAMPAIGN_OWNER_PATHS, "reviewed_campaign_owner_registration", "reviewed-campaign"),
    ):
        for field, required_paths in family.items():
            registered = owner.get(field, [])
            for required_path in required_paths:
                if required_path not in registered:
                    return [Finding(failure_class, f"{owner['andon_id']} {field} must register {label} owner {required_path}")]
                if not (ROOT / required_path).is_file():
                    return [Finding(failure_class, f"{owner['andon_id']} registered {label} owner path does not exist: {required_path}")]
    rules = registry.get("rules", {})
    if rules.get("source_binding_owner_paths_must_exist") is not True:
        return [Finding("source_binding_owner_registration", "source-binding owner-path existence gate must be active")]
    if rules.get("ci_readback_owner_paths_must_exist") is not True:
        return [Finding("ci_readback_owner_registration", "CI-readback owner-path existence gate must be active")]
    if rules.get("candidate_custody_owner_paths_must_exist") is not True:
        return [Finding("candidate_custody_owner_registration", "candidate-custody owner-path existence gate must be active")]
    if rules.get("candidate_maturity_owner_paths_must_exist") is not True:
        return [Finding("candidate_maturity_owner_registration", "candidate-maturity owner-path existence gate must be active")]
    if rules.get("reviewed_campaign_owner_paths_must_exist") is not True:
        return [Finding("reviewed_campaign_owner_registration", "reviewed-campaign owner-path existence gate must be active")]
    if rules.get("global_missing_owner_path_rejection") is not True:
        return [
            Finding(
                "global_owner_path_gate_boundary",
                "global missing-owner-path rejection must be active after A16 Tasks 4-6 materialize",
            )
        ]
    for contract in contracts:
        for field in ("owned_schema_paths", "owned_tool_paths", "owned_test_paths"):
            for owned_path in contract.get(field, []):
                if not (ROOT / owned_path).is_file():
                    return [Finding("missing_owned_path", f"{contract.get('andon_id')} registered missing {field} path {owned_path}")]
    a16_milestones = {m.get("milestone_id"): m for m in a16.get("milestones", [])}
    if a16_milestones.get("A16.bootstrap", {}).get("dependencies") != []:
        return [Finding("a16_bootstrap_contract", "A16.bootstrap must have no dependencies")]
    expected_terminal = {f"A{i:02d}.terminal" for i in range(1, 16)}
    if set(a16_milestones.get("A16.terminal", {}).get("dependencies", [])) != expected_terminal:
        return [Finding("a16_terminal_contract", "A16.terminal must depend on A01-A15 terminal milestones")]

    for contract in contracts:
        plan, plan_finding = _tracked_plan_path(
            str(contract.get("andon_id", "")),
            contract.get("plan_filename"),
        )
        if plan_finding is not None or plan is None:
            return [plan_finding or Finding("plan_evidence_not_portable", "plan evidence unavailable")]
        actual_hash = _sha256(plan)
        if actual_hash != contract.get("plan_sha256"):
            return [Finding("stale_plan_hash", f"{contract.get('andon_id')} plan_sha256 does not match {actual_hash}")]

    decision_rows = decisions.get("decisions", []) if isinstance(decisions, dict) else []
    decision_status = {d.get("decision_id"): d.get("status") for d in decision_rows if isinstance(d, dict)}
    for contract in contracts:
        for decision_id in contract.get("binding_adr_ids", []):
            if decision_id not in decision_status:
                return [Finding("missing_binding_adr", f"binding ADR {decision_id} is missing for {contract.get('andon_id')}")]
            if decision_status[decision_id] != "ACCEPTED":
                return [Finding("rejected_binding_adr", f"binding ADR {decision_id} has status {decision_status[decision_id]}")]

    closure_rows = {row.get("andon_id"): row for row in read_json(LIVE_CLOSURE).get("rows", [])}
    for contract in contracts:
        closure_ids = closure_rows.get(contract.get("andon_id"), {}).get("binding_adr_ids", [])
        if closure_ids != contract.get("binding_adr_ids", []):
            return [Finding("cross_ledger_adr_mismatch", f"{contract.get('andon_id')} binding_adr_ids differ between contract registry and closure ledger")]
        registry_milestones = [
            {"milestone_id": milestone.get("milestone_id"), "dependencies": milestone.get("dependencies", [])}
            for milestone in contract.get("milestones", [])
        ]
        closure_milestones = [
            {"milestone_id": milestone.get("milestone_id"), "dependencies": milestone.get("depends_on", [])}
            for milestone in closure_rows.get(contract.get("andon_id"), {}).get("milestones", [])
        ]
        if closure_milestones != registry_milestones:
            return [Finding("cross_ledger_milestone_mismatch", f"{contract.get('andon_id')} milestone IDs or dependency arrays differ between contract registry and closure ledger")]

    state = registry.get("state_capsule_v2", {})
    if state.get("single_owner") != "A16":
        return [Finding("state_capsule_owner", "state-capsule v2 single_owner must be A16")]
    if "schema/state-capsule-v2.schema.json" not in a16.get("owned_schema_paths", []):
        return [Finding("state_capsule_owner", "A16 must own schema/state-capsule-v2.schema.json")]

    migration = read_json(MIGRATION_LEDGER)
    contributions = {
        item.get("andon_id"): set(item.get("fields", []))
        for item in migration.get("composed_v2_contributors", [])
        if isinstance(item, dict)
    }
    for contract in contracts:
        declared = {value for value in contract.get("state_capsule_contribution", []) if value in {
            "candidate_states", "input_pressures", "candidate_state_partitions", "burden_partition_decisions",
            "partition_derivative_mappings", "partition_derivative_mappings_sha256",
            "upstream_obligation_ids", "upstream_obligation_set_sha256", "upstream_pressure_ids",
            "upstream_partition_decision_ids", "owner_routes", "act_row_details",
            "owner_execution_dispositions", "owner_obligation_state", "operation_capsules", "operation_body_artifacts",
            "topology_mass_accounting", "topology_mass_evidence_authority", "topology_mass_evidence_authority_sha256",
            "burden_cycles", "reread_signature_history", "reread_signature_history_sha256",
            "current_live_burdens", "held", "resource_policy", "closure_authority", "closure_state",
            "projection", "runtime_call_context_refs",
        }}
        if declared != contributions.get(contract.get("andon_id"), set()):
            return [Finding("state_capsule_mapping", f"{contract.get('andon_id')} state-capsule contribution differs from migration ledger")]

    case_contract = registry.get("required_case_registry", {})
    planned_cases = case_contract.get("case_ids", [])
    materialized_cases = context.get("materialized_cases")
    if materialized_cases is None:
        case_path = ROOT / str(case_contract.get("path", ""))
        materialized_cases = _case_ids_from_file(case_path)
    if materialized_cases is not None and set(materialized_cases) != set(planned_cases):
        return [Finding("case_registry_mismatch", "materialized case set does not equal the A14 canonical case set")]
    if materialized_cases is not None and materialized_cases != planned_cases:
        return [Finding("case_registry_mismatch", "materialized case array does not exactly equal the A14 canonical case array")]
    bootstrap_state = case_contract.get("bootstrap_state")
    if bootstrap_state not in {"planned-unmaterialized", "materialized"}:
        return [Finding("case_registry_state", f"unsupported case-registry bootstrap state {bootstrap_state!r}")]
    if bootstrap_state == "materialized" and materialized_cases is None:
        return [Finding("case_registry_state", "materialized case registry is missing")]
    non_claims = " ".join(registry.get("non_claims", [])).lower()
    if "not authority" not in non_claims or "model call" not in non_claims:
        return [Finding("bootstrap_authority_overclaim", "case-registry state must explicitly deny model-call authority")]
    return []


def diag(path: Path, finding: Finding) -> dict[str, Any]:
    return {"artifact": rel(path), "checker": CHECKER, "checker_id": CHECKER_ID, "downstream_invalidated": DOWNSTREAM_INVALIDATED, "earliest_stage": STAGE, "exit_category": "structural-rejection", "exit_code": 1, "failure_class": finding.failure_class, "message": finding.message, "stage": STAGE}


def self_test() -> int:
    problems: list[str] = []
    _external_plan, external_finding = _tracked_plan_path(
        "A01",
        "01_evidence_custody_and_causal_attribution_plan.md",
        plan_root=ROOT.parents[1] / "outputs" / "Sol",
    )
    if external_finding is None or external_finding.failure_class != "plan_evidence_not_portable":
        problems.append("external plan root did not fail closed as plan_evidence_not_portable")
    valid = sorted((FIXTURE_ROOT / "valid").glob("*.json"))
    invalid = sorted(p for p in (FIXTURE_ROOT / "invalid").glob("*.json") if not p.name.endswith(".expectation.json"))
    for path in valid:
        findings = validate(*materialize(path, LIVE_ADR))
        if findings:
            problems.append(f"{rel(path)}: [{findings[0].failure_class}] {findings[0].message}")
    for path in invalid:
        findings = validate(*materialize(path, LIVE_ADR))
        if not findings:
            problems.append(f"{rel(path)}: invalid fixture survived")
        else:
            problems.extend(expectation_problems(path, findings[0], checker_id=CHECKER_ID, downstream_invalidated=DOWNSTREAM_INVALIDATED))
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        print(f"andon contract registry self-test: FAIL ({len(problems)} problem(s))")
        return 1
    print(f"andon contract registry self-test: PASS ({len(valid)} valid, {len(invalid)} invalid)")
    return 0


def run_one(path: Path, decision_path: Path, *, explain: bool) -> int:
    try:
        findings = validate(*materialize(path, decision_path))
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        findings = [Finding("fixture_or_json", str(exc))]
    if findings:
        first = findings[0]
        print(json.dumps(diag(path, first), sort_keys=True) if explain else f"andon contract registry: FAIL [{first.failure_class}]: {first.message}")
        return 1
    state = read_json(path).get("required_case_registry", {}).get("bootstrap_state") if path == LIVE_REGISTRY else "fixture"
    print(json.dumps({"artifact": rel(path), "checker": CHECKER, "status": "PASS"}, sort_keys=True) if explain else f"andon contract registry: PASS ({rel(path)}; case registry {state}; grants no execution authority)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?")
    parser.add_argument("--registry")
    parser.add_argument("--decision-ledger", default=rel(LIVE_ADR))
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    selected = args.registry or args.artifact or rel(LIVE_REGISTRY)
    path = Path(selected)
    decision_path = Path(args.decision_ledger)
    if not path.is_absolute():
        path = ROOT / path
    if not decision_path.is_absolute():
        decision_path = ROOT / decision_path
    return run_one(path.resolve(), decision_path.resolve(), explain=args.explain)


if __name__ == "__main__":
    raise SystemExit(main())
