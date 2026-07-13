#!/usr/bin/env python3
"""Run the repository's push/PR runtime check sequence locally.

This script is intentionally a thin command runner for the `runtime-checks`
job. Keep the command order in one place instead of copying long checker
lists into README, AGENTS.md, and workflow YAML.
"""

from __future__ import annotations

import argparse
import ctypes
import glob
import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


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
    "python tools/check_source_provenance.py --self-test",
    "python tools/check_source_provenance.py --tracked-only",
    "python -B tests/source-provenance/test_contract.py",
    "python tools/check_ci_readback.py --self-test",
    "python -B tests/ci-readback/test_contract.py",
    "python tools/check_evidence_retention_manifest.py --self-test",
    "python tools/export_cycle_evidence_bundle.py --self-test",
    "python tools/write_linux_a01_evidence.py --self-test",
    "python tools/write_task7_deterministic_evidence.py --self-test",
    "python tools/check_release_action_authorization.py --self-test",
    "python -B tests/release-action-authorization/test_contract.py",
    "python tools/check_vcs_action_authorization.py --self-test",
    "python -B tests/vcs-action-authorization/test_contract.py",
    "python tools/check_captured_output_manifest.py --self-test",
    "python tools/check_case_registry_taint.py --self-test",
    "python tools/check_cold_comprehensiveness_review.py --self-test",
    "python tools/check_input_pressure_coverage.py --self-test",
    "python tools/check_model_smoke_escape_registry.py --self-test",
    "python tools/check_mrp_recursion_lifecycle.py --self-test",
    "python tools/check_no_fixed_topology_floors.py --self-test",
    "python tools/check_no_model_candidate_maturity.py --self-test",
    "python tools/check_opening_closure_state.py --self-test",
    "python tools/check_package_harness_parity.py --self-test",
    "python tools/check_paired_cross_model_manifest.py --self-test",
    "python tools/check_parallel_dispatch_manifest.py --self-test",
    "python tools/check_producer_checker_parity.py --self-test",
    "python tools/check_review_incident_report.py --self-test",
    "python tools/check_runtime_context_delivery.py --self-test",
    "python tools/run_no_model_preflight.py --self-test",
    "python tools/check_smoke_matrix_manifest.py --self-test",
    "python tools/reviewed_campaign_orchestrator.py --self-test",
    "python tests/reviewed-campaign-orchestration/test_contract.py",
    "python tools/build_candidate_package_record.py --self-test",
    "python tests/artifact-tree/test_contract.py",
    "python tests/candidate-build/test_contract.py",
    "python tests/smoke-matrix/test_protocol.py",
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
    "python tests/evidence-retention/test_contract.py",
    "python tests/no-model-candidate-maturity/test_contract.py",
    "python tests/no-model-candidate-maturity/test_candidate_maturity.py",
    "python tools/check_smoke_matrix_manifest.py --manifest tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json --inputs-only",
    "python tools/check_stage_projection_parity.py",
    "python tools/check_topology_capacity_properties.py --probe-set tests/topology-capacity/probe-set.json --through-stage stage-04-burden-execution-act",
    "python tools/check_topology_capacity_properties.py --probe-set tests/topology-capacity/probe-set.json --through-stage stage-05-mrp-reread-terminal-state",
    "python tools/check_topology_capacity_properties.py --probe-set tests/topology-capacity/probe-set.json --through-stage stage-08-verifier-sidecars",
    "python tools/check_topology_capacity_properties.py --metamorphic --probe-set tests/topology-capacity/probe-set.json",
    "python tools/check_validation_registry.py --registrations-only",
    "python tools/check_validation_registry.py",
    "python tools/check_andon_closure_ledger.py",
    "python tools/render_andon_closure_ledger.py --check",
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

TIMEOUT_EXIT_CODE = 124
TEARDOWN_EXIT_CODE = 125
TEARDOWN_FAILURE_KIND = "PROCESS_TREE_TEARDOWN"
PROCESS_TREE_TERMINATION_GRACE_SECONDS = 5.0
PYTHON_STARTUP_FLAGS = ("-I", "-S", "-B")
PYTHON_BOOTSTRAP_PATH = Path(__file__).resolve().with_name("sanitized_python_bootstrap.py")
PYTHON_LOGICAL_STARTUP_FLAGS = {"-B", "-E", "-I", "-S", "-s"}
PYTHON_ALLOWED_MODULES = {"py_compile"}
PYTHON_EXECUTION_PROFILE_ID = "python-isolated-bootstrap-v2"
REMOVED_ENVIRONMENT_NAMES_ATTRIBUTE = "_daee_sanitized_python_removed_environment_names"
PYTHON_EXECUTION_PROFILE = {
    "profile_id": PYTHON_EXECUTION_PROFILE_ID,
    "launcher": "running-interpreter",
    "python_flags": list(PYTHON_STARTUP_FLAGS),
    "bootstrap_path": "tools/sanitized_python_bootstrap.py",
    "environment_policy": "isolated-startup-then-delete-python-prefixed-and-pyvenv-launcher-v2",
    "import_roots_policy": "stdlib-plus-repo-tools-script-parent-direct-sysconfig-system-user-no-pth-v2",
}
NATIVE_EXECUTION_PROFILE = {
    "profile_id": "native-inherited-environment-v1",
    "launcher": "path",
    "python_flags": [],
    "bootstrap_path": "",
    "environment_policy": "inherit-v1",
    "import_roots_policy": "native-v1",
}
COMPLETION_PREFIX = "RUN_LOCAL_CI_COMPLETION "
COMPLETION_KEYS = frozenset(
    {
        "schema",
        "completion_id",
        "status",
        "complete",
        "command_count",
        "executed_count",
        "start_at_command",
        "end_at_command",
        "command_list_sha256",
        "execution_plan_sha256",
        "strict_pwsh",
        "command_timeout_seconds",
        "timeout_count",
        "skip_count",
    }
)


class OwnedProcessTeardownError(RuntimeError):
    """The runner could not prove that every owned process was terminated."""


@dataclass(frozen=True)
class OwnedCommandResult:
    args: list[str]
    returncode: int
    stdout: bytes | None
    stderr: bytes | None
    timed_out: bool
    teardown_failed: bool = False
    failure_kind: str | None = None


def _posix_group_running(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _windows_process_parent_map() -> dict[int, int]:
    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("cntUsage", ctypes.c_ulong),
            ("th32ProcessID", ctypes.c_ulong),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", ctypes.c_ulong),
            ("cntThreads", ctypes.c_ulong),
            ("th32ParentProcessID", ctypes.c_ulong),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.c_ulong),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel32.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32FirstW.restype = ctypes.c_int
    kernel32.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32NextW.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    invalid_handle = ctypes.c_void_p(-1).value
    if not handle or handle == invalid_handle:
        error = ctypes.get_last_error()
        raise OSError(error, "CreateToolhelp32Snapshot failed")
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        if not kernel32.Process32FirstW(handle, ctypes.byref(entry)):
            error = ctypes.get_last_error()
            if error == 18:  # ERROR_NO_MORE_FILES
                return {}
            raise OSError(error, "Process32FirstW failed")
        parents: dict[int, int] = {}
        while True:
            parents[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
            if not kernel32.Process32NextW(handle, ctypes.byref(entry)):
                error = ctypes.get_last_error()
                if error != 18:  # ERROR_NO_MORE_FILES
                    raise OSError(error, "Process32NextW failed")
                break
        return parents
    finally:
        kernel32.CloseHandle(handle)


def _windows_pid_is_running(pid: int) -> bool:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel32.GetExitCodeProcess.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER: PID no longer exists.
            return False
        raise OSError(error, f"OpenProcess failed for PID {pid}")
    try:
        exit_code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            error = ctypes.get_last_error()
            raise OSError(error, f"GetExitCodeProcess failed for PID {pid}")
        return exit_code.value == 259  # STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def _windows_owned_pids(
    root_pid: int, parent_map: Mapping[int, int], *, seeds: Sequence[int] = ()
) -> set[int]:
    owned = {root_pid, *seeds}
    changed = True
    while changed:
        changed = False
        for pid, parent_pid in parent_map.items():
            if pid not in owned and parent_pid in owned:
                owned.add(pid)
                changed = True
    return owned


def _terminate_windows_owned_process_tree(process: subprocess.Popen[bytes]) -> None:
    issues: list[str] = []
    try:
        before = _windows_process_parent_map()
    except OSError as exc:
        before = {}
        issues.append(f"snapshot-before:{type(exc).__name__}")
    owned_pids = _windows_owned_pids(process.pid, before)

    taskkill_succeeded = False
    try:
        taskkill = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
            timeout=PROCESS_TREE_TERMINATION_GRACE_SECONDS,
        )
    except subprocess.TimeoutExpired:
        issues.append("taskkill-timeout")
    except OSError as exc:
        issues.append(f"taskkill-spawn:{type(exc).__name__}")
    else:
        if taskkill.returncode == 0:
            taskkill_succeeded = True
        else:
            issues.append(f"taskkill-returncode:{taskkill.returncode}")

    if not taskkill_succeeded and process.poll() is None:
        try:
            process.kill()
        except OSError as exc:
            issues.append(f"root-kill:{type(exc).__name__}")

    try:
        process.wait(timeout=PROCESS_TREE_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        issues.append("root-wait-timeout")
        try:
            process.kill()
        except OSError as exc:
            issues.append(f"root-kill-after-wait:{type(exc).__name__}")
        try:
            process.wait(timeout=PROCESS_TREE_TERMINATION_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            issues.append("root-wait-timeout-after-kill")

    try:
        after = _windows_process_parent_map()
    except OSError as exc:
        after = {}
        issues.append(f"snapshot-after:{type(exc).__name__}")
    owned_pids = _windows_owned_pids(process.pid, after, seeds=tuple(owned_pids))

    deadline = time.monotonic() + PROCESS_TREE_TERMINATION_GRACE_SECONDS
    survivors: set[int] = set()
    while True:
        survivors = set()
        query_failed = False
        for pid in sorted(owned_pids):
            try:
                if _windows_pid_is_running(pid):
                    survivors.add(pid)
            except OSError as exc:
                issues.append(f"pid-query:{pid}:{type(exc).__name__}")
                query_failed = True
        if not survivors or query_failed or time.monotonic() >= deadline:
            break
        time.sleep(0.05)
    if survivors:
        issues.append("surviving-pids:" + ",".join(str(pid) for pid in sorted(survivors)))
    if issues:
        raise OwnedProcessTeardownError(";".join(issues))


def _terminate_owned_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        _terminate_windows_owned_process_tree(process)
        return

    process_group_id = process.pid
    try:
        os.killpg(process_group_id, signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + 1.0
    while _posix_group_running(process_group_id) and time.monotonic() < deadline:
        time.sleep(0.05)
    if _posix_group_running(process_group_id):
        try:
            os.killpg(process_group_id, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=PROCESS_TREE_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=PROCESS_TREE_TERMINATION_GRACE_SECONDS)
    deadline = time.monotonic() + PROCESS_TREE_TERMINATION_GRACE_SECONDS
    while _posix_group_running(process_group_id) and time.monotonic() < deadline:
        time.sleep(0.05)
    if _posix_group_running(process_group_id):
        raise RuntimeError(f"timed-out owned process group {process_group_id} is still running")


def run_owned_command(
    argv: Sequence[str],
    *,
    cwd: Path | str | None = None,
    capture_output: bool = False,
    timeout_seconds: int | float | None = None,
    env: Mapping[str, str] | None = None,
) -> OwnedCommandResult:
    popen_kwargs: dict[str, object] = {
        "cwd": cwd,
        "stdout": subprocess.PIPE if capture_output else None,
        "stderr": subprocess.PIPE if capture_output else None,
        "env": dict(env) if env is not None else None,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    process = subprocess.Popen(list(argv), **popen_kwargs)
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds or None)
    except subprocess.TimeoutExpired as timeout:
        try:
            _terminate_owned_process_tree(process)
        except OwnedProcessTeardownError as exc:
            stderr = timeout.stderr
            if stderr and not stderr.endswith(b"\n"):
                stderr += b"\n"
            stderr = (stderr or b"") + f"{TEARDOWN_FAILURE_KIND} {exc}\n".encode("utf-8")
            return OwnedCommandResult(
                list(argv),
                TEARDOWN_EXIT_CODE,
                timeout.output,
                stderr,
                True,
                True,
                TEARDOWN_FAILURE_KIND,
            )
        stdout, stderr = process.communicate()
        return OwnedCommandResult(list(argv), TIMEOUT_EXIT_CODE, stdout, stderr, True)
    return OwnedCommandResult(list(argv), process.returncode, stdout, stderr, False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="print commands without running them")
    parser.add_argument("--json", type=Path, default=None, help="atomically write the canonical completion report")
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


def _logical_parts(command: str | Sequence[str]) -> list[str]:
    return shlex.split(command) if isinstance(command, str) else list(command)


def execution_profile_for(command: str | Sequence[str]) -> dict[str, object]:
    parts = _logical_parts(command)
    if not parts or parts[0] != "python":
        return {**NATIVE_EXECUTION_PROFILE, "removed_environment_names": []}
    removed = getattr(sys, REMOVED_ENVIRONMENT_NAMES_ATTRIBUTE, ())
    if not isinstance(removed, (list, tuple)) or any(not isinstance(name, str) for name in removed):
        raise RuntimeError("sanitized Python bootstrap removed-name custody is malformed")
    names = sorted(set(removed), key=lambda name: (name.upper(), name))
    if any(
        not (name.upper().startswith("PYTHON") or name.upper() == "__PYVENV_LAUNCHER__")
        for name in names
    ):
        raise RuntimeError("sanitized Python bootstrap recorded a non-Python environment name")
    return {**PYTHON_EXECUTION_PROFILE, "removed_environment_names": names}


def execution_environment_for(
    command: str | Sequence[str], *, inherited: Mapping[str, str] | None = None
) -> dict[str, str] | None:
    parts = _logical_parts(command)
    if not parts or parts[0] != "python":
        return None
    source = os.environ if inherited is None else inherited
    return {
        key: value
        for key, value in source.items()
        if not key.upper().startswith("PYTHON") and key.upper() != "__PYVENV_LAUNCHER__"
    }


def execution_argv_for(command: str | Sequence[str], *, expand_globs: bool = False) -> list[str]:
    parts = _logical_parts(command)
    if parts and parts[0] == "python":
        tail = parts[1:]
        while tail and tail[0] in PYTHON_LOGICAL_STARTUP_FLAGS:
            tail.pop(0)
        if not tail or tail[0] in {"-c", "-"}:
            raise ValueError("sanitized Python execution requires a static script or allowed module")
        if tail[0] == "-m":
            if len(tail) < 2 or tail[1] not in PYTHON_ALLOWED_MODULES:
                raise ValueError("sanitized Python execution rejects unsupported module mode")
            parts = [
                sys.executable,
                *PYTHON_STARTUP_FLAGS,
                str(PYTHON_BOOTSTRAP_PATH),
                "--module",
                tail[1],
                *tail[2:],
            ]
        else:
            if tail[0].startswith("-") or not tail[0].endswith(".py"):
                raise ValueError("sanitized Python execution rejects dynamic or indeterminate forms")
            parts = [
                sys.executable,
                *PYTHON_STARTUP_FLAGS,
                str(PYTHON_BOOTSTRAP_PATH),
                "--script",
                *tail,
            ]

    expanded: list[str] = []
    for part in parts:
        if expand_globs and any(marker in part for marker in "*?["):
            matches = sorted(glob.glob(part))
            expanded.extend(matches if matches else [part])
        else:
            expanded.append(part)
    return expanded


def argv_for(command: str) -> list[str]:
    return execution_argv_for(command, expand_globs=True)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def command_list_sha256(commands: Sequence[str] | None = None) -> str:
    selected = list(COMMANDS if commands is None else commands)
    return hashlib.sha256(_canonical_json_bytes(selected)).hexdigest()


def execution_plan_sha256(commands: Sequence[str] | None = None) -> str:
    selected = list(COMMANDS if commands is None else commands)
    plan = [
        {"sequence": index, "command": command, "execution_profile": execution_profile_for(command)}
        for index, command in enumerate(selected, 1)
    ]
    return hashlib.sha256(_canonical_json_bytes(plan)).hexdigest()


def _completion_id(value: Mapping[str, object]) -> str:
    body = {key: value[key] for key in value if key != "completion_id"}
    return hashlib.sha256(b"daee-run-local-ci-completion-v1\0" + _canonical_json_bytes(body)).hexdigest()


def build_completion(
    *,
    start_at_command: int,
    strict_pwsh: bool,
    command_timeout_seconds: int,
    skip_count: int | None = None,
    commands: Sequence[str] | None = None,
) -> dict[str, object]:
    selected = list(COMMANDS if commands is None else commands)
    if not selected:
        raise ValueError("local-CI completion requires at least one command")
    if type(start_at_command) is not int or not 1 <= start_at_command <= len(selected):
        raise ValueError("local-CI completion start index is out of range")
    expected_skip_count = start_at_command - 1
    if skip_count is None:
        skip_count = expected_skip_count
    if type(skip_count) is not int or skip_count != expected_skip_count:
        raise ValueError("local-CI completion skip count must equal the unexecuted prefix length")
    if type(strict_pwsh) is not bool:
        raise ValueError("local-CI completion strict-pwsh value is malformed")
    if type(command_timeout_seconds) is not int or command_timeout_seconds < 0:
        raise ValueError("local-CI completion timeout is malformed")
    executed_count = len(selected) - start_at_command + 1
    complete = start_at_command == 1
    value: dict[str, object] = {
        "schema": "daee-run-local-ci-completion-v1",
        "completion_id": "0" * 64,
        "status": "PASS" if complete else "PARTIAL",
        "complete": complete,
        "command_count": len(selected),
        "executed_count": executed_count,
        "start_at_command": start_at_command,
        "end_at_command": len(selected),
        "command_list_sha256": command_list_sha256(selected),
        "execution_plan_sha256": execution_plan_sha256(selected),
        "strict_pwsh": strict_pwsh,
        "command_timeout_seconds": command_timeout_seconds,
        "timeout_count": 0,
        "skip_count": skip_count,
    }
    value["completion_id"] = _completion_id(value)
    return value


def completion_stdout(value: Mapping[str, object]) -> bytes:
    return (COMPLETION_PREFIX + _canonical_json_bytes(dict(value)).decode("utf-8") + "\n").encode("utf-8")


def publish_completion_report(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(dict(value), indent=2, sort_keys=True).encode("utf-8") + b"\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    if path.read_bytes() != raw:
        raise OSError(f"local-CI completion report readback drifted: {path}")


def parse_completion_stdout(raw: bytes) -> dict[str, object]:
    try:
        lines = raw.decode("utf-8", "strict").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError(f"local-CI completion stdout is not UTF-8: {exc}") from exc
    completion_lines = [line for line in lines if line.startswith(COMPLETION_PREFIX)]
    if len(completion_lines) != 1 or not lines or lines[-1] != completion_lines[0]:
        raise ValueError("local-CI stdout must end with exactly one structured completion line")
    try:
        value = json.loads(completion_lines[0][len(COMPLETION_PREFIX) :])
    except json.JSONDecodeError as exc:
        raise ValueError(f"local-CI completion JSON is invalid: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != "daee-run-local-ci-completion-v1":
        raise ValueError("local-CI completion schema drifted")
    if set(value) != COMPLETION_KEYS:
        raise ValueError("local-CI completion fields drifted")
    if value.get("completion_id") != _completion_id(value):
        raise ValueError("local-CI completion identity drifted")
    integer_fields = (
        "command_count",
        "executed_count",
        "start_at_command",
        "end_at_command",
        "command_timeout_seconds",
        "timeout_count",
        "skip_count",
    )
    if any(type(value.get(field)) is not int for field in integer_fields):
        raise ValueError("local-CI completion integer fields are malformed")
    if type(value.get("complete")) is not bool or type(value.get("strict_pwsh")) is not bool:
        raise ValueError("local-CI completion boolean fields are malformed")
    command_count = value["command_count"]
    start_at_command = value["start_at_command"]
    skip_count = value["skip_count"]
    if command_count != len(COMMANDS):
        raise ValueError("local-CI completion command count drifted")
    if not 1 <= start_at_command <= command_count:
        raise ValueError("local-CI completion start index drifted")
    if skip_count != start_at_command - 1:
        raise ValueError("local-CI completion skipped-prefix count drifted")
    if value["end_at_command"] != command_count:
        raise ValueError("local-CI completion end index drifted")
    if value["executed_count"] != command_count - start_at_command + 1:
        raise ValueError("local-CI completion executed count drifted")
    complete = start_at_command == 1
    expected_status = "PASS" if complete else "PARTIAL"
    if value.get("status") != expected_status or value.get("complete") is not complete:
        raise ValueError("local-CI completion full-versus-partial semantics drifted")
    if value["command_timeout_seconds"] < 0:
        raise ValueError("local-CI completion timeout drifted")
    if value.get("command_list_sha256") != command_list_sha256():
        raise ValueError("local-CI completion command-list digest drifted")
    if value.get("execution_plan_sha256") != execution_plan_sha256():
        raise ValueError("local-CI completion execution-plan digest drifted")
    if value.get("timeout_count") != 0:
        raise ValueError("local-CI completion timeout count is nonzero")
    return value


def main() -> int:
    args = parse_args()
    if args.command_timeout_seconds < 0:
        print("--command-timeout-seconds must be zero or a positive integer", file=sys.stderr)
        return 2
    if not 1 <= args.start_at_command <= len(COMMANDS):
        print(f"--start-at-command must be between 1 and {len(COMMANDS)}", file=sys.stderr)
        return 2
    failures: list[tuple[str, int]] = []
    skip_count = args.start_at_command - 1

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
            skip_count += 1
            continue

        print(f"[{index}/{len(COMMANDS)}] {command}", flush=True)
        result = run_owned_command(
            argv_for(command),
            timeout_seconds=args.command_timeout_seconds or None,
            env=execution_environment_for(command),
        )
        if result.teardown_failed:
            detail = (result.stderr or b"").decode("utf-8", "replace").strip()
            print(f"{TEARDOWN_FAILURE_KIND}: {command}: {detail}", file=sys.stderr)
            failures.append((command, TEARDOWN_EXIT_CODE))
            break
        if result.timed_out:
            print(
                f"TIMEOUT ({args.command_timeout_seconds}s): {command}",
                file=sys.stderr,
            )
            failures.append((command, TIMEOUT_EXIT_CODE))
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

    if skip_count != args.start_at_command - 1:
        print("local-CI completion withheld because an in-range command was skipped", file=sys.stderr)
        return 127

    completion = build_completion(
        start_at_command=args.start_at_command,
        strict_pwsh=args.strict_pwsh,
        command_timeout_seconds=args.command_timeout_seconds,
        skip_count=skip_count,
    )
    if args.json is not None:
        publish_completion_report(args.json, completion)
    print(completion_stdout(completion).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
