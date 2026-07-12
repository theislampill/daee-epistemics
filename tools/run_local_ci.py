#!/usr/bin/env python3
"""Run the repository's push/PR runtime check sequence locally.

This script is intentionally a thin command runner for the `runtime-checks`
job. Keep the command order in one place instead of copying long checker
lists into README, AGENTS.md, and workflow YAML.
"""

from __future__ import annotations

import argparse
import glob
import shlex
import shutil
import subprocess
import sys


COMMANDS = [
    "python tools/check_stub_integrity.py --self-test",
    "python tools/check_stub_integrity.py",
    "python tools/build_framework_pipeline.py",
    "python tools/build_compiled_runtime.py",
    "python tools/build_docs_index.py --check",
    "python tools/check_compiled_runtime_freshness.py",
    "git diff --exit-code -- skill/SKILL.md",
    "python tools/check_compiled_skill_self_contained.py",
    "python tools/check_level3_data_shapes.py --include-generated",
    "python tools/check_package_shape.py",
    "python tools/check_compiled_module_boundaries.py",
    "python tools/check_consolidation_call_budget.py",
    "python tools/check_routing_parity.py",
    "python tools/check_routing_parity.py --strict",
    "python tools/check_recursive_traversal_governance.py",
    "python tools/check_render_modes.py",
    "python tools/check_frontmatter.py",
    "python tools/check_frontmatter.py --contract-version 0.4.0.0",
    "python tools/check_trigger_eval_manifest.py --self-test",
    "python tools/check_trigger_eval_manifest.py",
    "python tools/check_coverage.py",
    "python tools/check_framework_pipeline.py",
    "python tools/check_recursion_collapse_noetic_frame.py",
    "python tools/check_metacompliance_current_canon.py",
    "python tools/check_docs_claim_boundaries.py --self-test",
    "python tools/check_docs_claim_boundaries.py",
    "python tools/check_register_formalism_bridge.py",
    "python tools/check_field_witness_convergence.py",
    "python tools/check_owner_activation_ordering.py --require-plan --outputs tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/*/output.md",
    "python tools/check_reconstructibility_and_mrp.py",
    "python tools/check_nla_decode_semantic_faithfulness.py",
    "python tools/check_staged_runtime_handshake.py",
    "python tools/build_staged_runtime_replay_record.py --self-test",
    "python tools/build_staged_governed_output.py --self-test",
    "python tools/run_staged_current_skill_smoke.py --self-test",
    "python tools/compare_staged_runtime_replay.py --self-test",
    "python tools/check_tlang_response_closure.py --outputs tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/*/output.md",
    "python tools/check_nla_decode_semantic_faithfulness.py --outputs tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/*/output.md",
    "python tools/check_formal_reread_state_semantics.py --outputs tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/*/output.md",
    "python tools/check_public_burden_grouping.py",
    "python tools/check_act_surface_syntax.py --self-test",
    "python tools/check_shannon_finite_fold.py --outputs tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/*/output.md",
    "python tools/check_manual_smoke_render_contract.py",
    "python tools/check_collapse_certificate_schema.py",
    "python tools/check_graph_completeness.py",
    "python tools/check_output_grapher.py",
    "python tools/check_output_grapher_layout.py",
    "python tools/check_hard_smoke_manifest.py",
    "python tools/check_retained_proof_corpus.py",
    "python tools/check_retained_row_claims.py --self-test",
    "python tools/check_retained_row_claims.py",
    "python tools/check_retained_corpus_advisory.py --self-test",
    "python tools/check_retained_corpus_advisory.py",
    "python tools/build_retained_proof_sidecars.py --self-test",
    "python tools/build_field_witness_envelope.py --self-test",
    "python tools/promote_retained_proof_case.py --self-test",
    "pwsh -NoProfile -ExecutionPolicy Bypass -File tools/run_current_skill_smoke.ps1 -Root . -ProofSidecarSelfTest",
    "python tools/check_closure_witness_graph.py --input tests/live-witness-fixtures/valid/closure-witness-dependency-graph.md --field-witness tests/live-witness-fixtures/valid/closure-witness-dependency-graph.field_witness.json",
    "python tools/check_mid_reread_pressure.py",
    "python tools/check_mrp_generated_burden.py",
    "python tools/check_ttp_availability_canaries.py",
    "python tools/check_mrp_route_invariants.py",
    "python tools/check_concealment_mode.py",
    "python tools/check_trinitarian_mrp_hotfix.py",
    "python tools/check_ttp_operator_contracts.py --strict",
    "python tools/check_negative_example_mimicry.py",
    "python tools/verify_candidate_output.py --self-test",
    "python tools/check_andon_closure_ledger.py --self-test",
    "python tools/check_andon_contract_registry.py --self-test",
    "python tools/check_architecture_decision_ledger.py --self-test",
    "python tools/check_captured_output_manifest.py --self-test",
    "python tools/check_case_registry_taint.py --self-test",
    "python tools/check_cold_comprehensiveness_review.py --self-test",
    "python tools/check_input_pressure_coverage.py --self-test",
    "python tools/check_model_smoke_escape_registry.py --self-test",
    "python tools/check_mrp_recursion_lifecycle.py --self-test",
    "python tools/check_no_fixed_topology_floors.py --self-test",
    "python tools/check_opening_closure_state.py --self-test",
    "python tools/check_package_harness_parity.py --self-test",
    "python tools/check_paired_cross_model_manifest.py --self-test",
    "python tools/check_parallel_dispatch_manifest.py --self-test",
    "python tools/check_producer_checker_parity.py --self-test",
    "python tools/check_review_incident_report.py --self-test",
    "python tools/check_runtime_context_delivery.py --self-test",
    "python tools/run_no_model_preflight.py --self-test",
    "python tools/check_smoke_matrix_manifest.py --self-test",
    "python tools/check_stage_projection_parity.py --self-test",
    "python tools/check_topology_capacity_properties.py --self-test",
    "python tools/check_topology_mass_accounting.py --self-test",
    "python tools/check_topology_review.py --self-test",
    "python tools/check_validation_registry.py --self-test",
    "python tools/check_ci_registry_coverage.py --self-test",
    "python tools/check_ci_registry_coverage.py",
    "python tools/check_case_registry_taint.py",
    "python tools/check_model_smoke_escape_registry.py",
    "python tools/check_mrp_recursion_lifecycle.py",
    "python tools/check_no_fixed_topology_floors.py",
    "python tools/check_producer_checker_parity.py --registry tools/producer-contract-registry.json",
    "python tools/check_runtime_context_delivery.py --fixtures tests/runtime-context-delivery",
    "python tests/runtime-call-context-adapter/test_contract.py",
    "python tools/check_smoke_matrix_manifest.py --manifest tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json --inputs-only",
    "python tools/check_stage_projection_parity.py",
    "python tools/check_topology_capacity_properties.py --probe-set tests/topology-capacity/probe-set.json --through-stage stage-04-burden-execution-act",
    "python tools/check_topology_capacity_properties.py --probe-set tests/topology-capacity/probe-set.json --through-stage stage-05-mrp-reread-terminal-state",
    "python tools/check_topology_capacity_properties.py --probe-set tests/topology-capacity/probe-set.json --through-stage stage-08-verifier-sidecars",
    "python tools/check_topology_capacity_properties.py --metamorphic --probe-set tests/topology-capacity/probe-set.json",
    "python tools/check_validation_registry.py --registrations-only",
    "python tools/check_validation_registry.py",
    "python tools/check_andon_closure_ledger.py",
    "python tools/check_andon_contract_registry.py",
    "python tools/check_architecture_decision_ledger.py",
    "python tools/check_owner_contract_parity.py --self-test",
    "python tools/check_owner_contract_parity.py",
    "python tools/check_field_witness_binding.py --self-test",
    "python tools/check_field_witness_binding.py",
    "python tools/gen_fixture_mutations.py --self-test",
    "python tools/check_release_provenance.py --self-test",
    "python tools/analyze_ci_parallelizability.py --self-test",
    "python tools/measure_load_path_budget.py --self-test",
    "python tools/measure_load_path_budget.py --enforce-ratchet",
    "python tools/measure_load_path_budget.py --enforce",
    "python tools/build_package_shape_inventory.py --self-test",
    "python tools/build_package_shape_inventory.py --check",
    "python tools/check_prompt_pack_budget.py --self-test",
    "python tools/check_cold_law_digest.py --self-test",
    "python tools/check_cold_law_digest.py",
    "python tools/check_route_shard_selection.py --self-test",
    "python tools/check_route_shard_selection.py",
    "python tools/check_state_capsule.py --self-test",
    "python tools/measure_terminal_cover_ab.py --self-test",
    "python tools/build_model_compliance_scorecard.py --self-test",
    "python -B tests/validation-integrity/test_hardening.py",
    "python -B tests/validation-integrity/test_candidate_hardening.py",
    "python -B tests/validation-integrity/test_consumer_migration.py",
    "python -B tests/validation-integrity/test_scorecard_hardening.py",
    "python tools/check_spec_authoring_pack.py",
    "python tools/check_docs_index_interactions.py",
    "python tools/check_field_operator_architecture.py",
    "python tools/check_live_default_witness_contract.py tests/live-witness-fixtures/valid/current-public-graph.md",
    "python tools/check_reproducibility.py",
    "python tools/check_smoke_artifacts.py",
    "python tools/check_ir_instance_integrity.py",
    "python tools/check_diagnostic_ir_catalogue_integrity.py",
    "python tools/check_encoding_hygiene.py",
    "python tools/check_mojibake.py",
    "python -m py_compile tools/*.py",
    "git diff --exit-code -- atomics/skill/references/diagnostics/framework-pipeline.md",
    "git diff --check",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="print commands without running them")
    parser.add_argument(
        "--strict-pwsh",
        action="store_true",
        help="fail if pwsh is unavailable instead of skipping the PowerShell smoke step",
    )
    parser.add_argument(
        "--command-timeout-seconds",
        type=int,
        default=0,
        help="Bound each child command; zero preserves the historical unbounded default.",
    )
    parser.add_argument(
        "--start-at-command",
        type=int,
        default=1,
        help="Resume at this 1-based command index without replaying earlier green commands.",
    )
    return parser.parse_args()


def argv_for(command: str) -> list[str]:
    parts = shlex.split(command)
    if parts and parts[0] == "python":
        parts[0] = sys.executable

    expanded: list[str] = []
    for part in parts:
        if any(marker in part for marker in "*?["):
            matches = sorted(glob.glob(part))
            expanded.extend(matches if matches else [part])
        else:
            expanded.append(part)
    return expanded


def main() -> int:
    args = parse_args()
    if args.command_timeout_seconds < 0:
        print("--command-timeout-seconds must be zero or a positive integer", file=sys.stderr)
        return 2
    if not 1 <= args.start_at_command <= len(COMMANDS):
        print(f"--start-at-command must be between 1 and {len(COMMANDS)}", file=sys.stderr)
        return 2
    failures: list[tuple[str, int]] = []

    for index, command in enumerate(COMMANDS, start=1):
        if index < args.start_at_command:
            continue
        if args.list:
            print(command)
            continue

        if command.startswith("pwsh ") and shutil.which("pwsh") is None:
            message = f"[{index}/{len(COMMANDS)}] SKIP pwsh unavailable: {command}"
            if args.strict_pwsh:
                print(message, file=sys.stderr)
                return 127
            print(message)
            continue

        print(f"[{index}/{len(COMMANDS)}] {command}", flush=True)
        try:
            result = subprocess.run(
                argv_for(command),
                timeout=args.command_timeout_seconds or None,
            )
        except subprocess.TimeoutExpired:
            print(
                f"TIMEOUT ({args.command_timeout_seconds}s): {command}",
                file=sys.stderr,
            )
            failures.append((command, 124))
            break
        if result.returncode != 0:
            failures.append((command, result.returncode))
            break

    if args.list:
        return 0

    if failures:
        for command, code in failures:
            print(f"FAILED ({code}): {command}", file=sys.stderr)
        return failures[0][1]

    executed = len(COMMANDS) - args.start_at_command + 1
    print(f"run_local_ci: PASS ({executed} command(s), indices {args.start_at_command}-{len(COMMANDS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
