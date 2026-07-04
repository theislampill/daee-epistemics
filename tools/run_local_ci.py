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
    "python tools/build_framework_pipeline.py",
    "python tools/build_compiled_runtime.py",
    "python tools/build_docs_index.py --check",
    "python tools/check_compiled_runtime_freshness.py",
    "git diff --exit-code -- skill/SKILL.md",
    "python tools/check_compiled_skill_self_contained.py",
    "python tools/check_level3_data_shapes.py --include-generated",
    "python tools/check_package_shape.py",
    "python tools/check_compiled_module_boundaries.py",
    "python tools/check_stub_integrity.py",
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
    "python tools/check_profile_vocabulary_hygiene.py --self-test",
    "python tools/check_profile_vocabulary_hygiene.py",
    "python tools/check_safety_refusal.py --self-test",
    "python tools/check_safety_refusal.py",
    "python tools/check_spec_authoring_pack.py",
    "python tools/check_docs_index_interactions.py",
    "python tools/check_field_operator_architecture.py",
    "python tools/check_live_default_witness_contract.py tests/live-witness-fixtures/valid/closure-witness-dependency-graph.md",
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
    failures: list[tuple[str, int]] = []

    for index, command in enumerate(COMMANDS, start=1):
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
        result = subprocess.run(argv_for(command))
        if result.returncode != 0:
            failures.append((command, result.returncode))
            break

    if args.list:
        return 0

    if failures:
        for command, code in failures:
            print(f"FAILED ({code}): {command}", file=sys.stderr)
        return failures[0][1]

    print(f"run_local_ci: PASS ({len(COMMANDS)} commands)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
