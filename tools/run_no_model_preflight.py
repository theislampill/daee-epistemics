#!/usr/bin/env python3
"""No-model composed preflight gate (Plan 12 Section 3).
================================================================

THIS TOOL NEVER RUNS A MODEL SMOKE. It composes only existing no-model
checkers/builders (plus one static self-test unit) and prints exactly one
final decision token as its last stdout line:

    MATRIX_AUTHORIZED_AFTER_PREFLIGHT   -- every gate passed
    MATRIX_NOT_AUTHORIZED               -- at least one gate failed

It is the stop-line gate that must pass before any five-smoke model matrix
is launched. The matrix itself remains owner-gated: this tool does not
launch it, does not decide to launch it, and does not contain any code path
that invokes a model. Gate 14 (five-smoke input-path preflight) calls
`tools/run_staged_current_skill_smoke.py --preflight-input-only`, which is
input-shape validation only -- it returns before reaching that harness's
`run_model_smoke()` function (see that file's `main()`: the
`--preflight-input-only` branch returns from `preflight_smoke_inputs()`
directly and the model-smoke code path is never imported into this
process). No `--model` value is ever passed by this tool.

Each gate is: a name, one or more shell-style commands (run via subprocess,
argv-split, no shell=True), a pass/fail rule (exit code 0 == pass unless
noted), and a minimal no-model repair lane string shown only when the gate
fails. Gates run sequentially; a failing gate does not stop the sweep --
every gate is attempted so the ledger reports ALL red gates at once. Only
the final decision line depends on the aggregate.

Per-gate stdout/stderr is captured and suppressed unless the gate fails, to
keep the ledger readable; on failure the captured output is included in the
JSON report (if --json is given) and a short tail is printed to the console.

Usage:
    python tools/run_no_model_preflight.py               run the full sweep
    python tools/run_no_model_preflight.py --json out.json   also write a report
    python tools/run_no_model_preflight.py --self-test    validate gate-table,
                                                           decision aggregation,
                                                           and Gate 14 registry
                                                           custody (no subprocesses)
"""

from __future__ import annotations

import argparse
import glob
import json
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import smoke_matrix_registry

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]

AUTHORIZED_TOKEN = "MATRIX_AUTHORIZED_AFTER_PREFLIGHT"
NOT_AUTHORIZED_TOKEN = "MATRIX_NOT_AUTHORIZED"

DEFAULT_TIMEOUT_SEC = 300
LONG_TIMEOUT_SEC = 900

RETAINED_CASES_ROOT = (
    "tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases"
)
RETAINED_OUTPUTS_GLOB = f"{RETAINED_CASES_ROOT}/*/output.md"

STABLE_EXPLAIN_FIXTURE = "tests/staged-runtime-handshake/invalid/absolute-output-path.json"


def argv_for(command: str) -> list[str]:
    """Split a command string into argv, substituting the current interpreter
    for a bare "python" token and expanding shell-style globs the way the
    caller's own shell would. Mirrors tools/run_local_ci.py's argv_for so the
    two runners resolve identical command strings identically (in particular
    on Windows, where the shell does not expand globs itself)."""
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


@dataclass
class StepResult:
    command: str
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_sec: float
    timed_out: bool = False


@dataclass
class GateResult:
    name: str
    passed: bool
    repair_lane: str
    steps: list[StepResult] = field(default_factory=list)
    note: str = ""


def run_step(command: str, *, timeout: int = DEFAULT_TIMEOUT_SEC, cwd: Path = ROOT) -> StepResult:
    argv = argv_for(command)
    start = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        duration = time.monotonic() - start
        return StepResult(
            command=command,
            argv=argv,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_sec=duration,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        return StepResult(
            command=command,
            argv=argv,
            returncode=124,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else f"TIMEOUT after {timeout}s",
            duration_sec=duration,
            timed_out=True,
        )
    except FileNotFoundError as exc:
        duration = time.monotonic() - start
        return StepResult(
            command=command,
            argv=argv,
            returncode=127,
            stdout="",
            stderr=str(exc),
            duration_sec=duration,
        )


def steps_all_pass(commands: list[str], *, timeout: int = DEFAULT_TIMEOUT_SEC) -> tuple[bool, list[StepResult]]:
    steps: list[StepResult] = []
    ok = True
    for command in commands:
        result = run_step(command, timeout=timeout)
        steps.append(result)
        if result.returncode != 0:
            ok = False
    return ok, steps


# ---------------------------------------------------------------------------
# Gate implementations
#
# Each gate function returns (passed: bool, steps: list[StepResult], note: str)
# ---------------------------------------------------------------------------


def gate_generated_runtime_freshness() -> tuple[bool, list[StepResult], str]:
    commands = [
        "python tools/build_framework_pipeline.py",
        "python tools/build_compiled_runtime.py",
        "python tools/check_compiled_runtime_freshness.py",
        "git diff --exit-code -- skill/SKILL.md",
    ]
    ok, steps = steps_all_pass(commands)
    return ok, steps, "regenerate the compiled runtime/framework pipeline and commit the result"


def gate_docs_freshness() -> tuple[bool, list[StepResult], str]:
    ok, steps = steps_all_pass(["python tools/build_docs_index.py --check"])
    return ok, steps, "run `python tools/build_docs_index.py` (without --check) and commit docs/index.html"


def gate_package_shape() -> tuple[bool, list[StepResult], str]:
    ok, steps = steps_all_pass(["python tools/check_package_shape.py"])
    return ok, steps, "reconcile skill/ tree against build-manifest.json (rerun the compiled-runtime build)"


def gate_hot_context_budget() -> tuple[bool, list[StepResult], str]:
    commands = [
        "python tools/measure_load_path_budget.py --self-test",
        "python tools/measure_load_path_budget.py --enforce-ratchet",
        "python tools/measure_load_path_budget.py --enforce",
    ]
    ok, steps = steps_all_pass(commands)
    return ok, steps, "trim the regressed shard/root back under its load-path budget ceiling; do not raise the ceiling"


EXECUTION_KERNEL_MARKERS = (
    "EXECUTION MANDATE - DEFAULT MODE",
    "NON-DROPPABLE DEFAULT MANUAL CONTRACT",
    "MULTI-CALL STATE CAPSULE LAW",
    "Always-Load Digests",
    "Stage-07 mandatory loads",
    "Dispatch Index",
)


def gate_execution_kernel_markers() -> tuple[bool, list[StepResult], str]:
    compiled_root = ROOT / "skill" / "SKILL.md"
    start = time.monotonic()
    command = f"read-markers {compiled_root.as_posix()}"
    if not compiled_root.exists():
        step = StepResult(
            command=command,
            argv=[],
            returncode=1,
            stdout="",
            stderr=f"compiled root missing: {compiled_root}",
            duration_sec=time.monotonic() - start,
        )
        return False, [step], "regenerate skill/SKILL.md via tools/build_compiled_runtime.py"

    text = compiled_root.read_text(encoding="utf-8", errors="replace")
    missing = [marker for marker in EXECUTION_KERNEL_MARKERS if marker not in text]
    duration = time.monotonic() - start
    if missing:
        step = StepResult(
            command=command,
            argv=[],
            returncode=1,
            stdout="",
            stderr=f"missing literal kernel markers in skill/SKILL.md: {missing}",
            duration_sec=duration,
        )
        return False, [step], "restore the load-bearing kernel markers in atomics/skill source, then rebuild"

    step = StepResult(
        command=command,
        argv=[],
        returncode=0,
        stdout=f"all {len(EXECUTION_KERNEL_MARKERS)} execution-kernel markers present in skill/SKILL.md",
        stderr="",
        duration_sec=duration,
    )
    return True, [step], ""


def gate_route_shard_selection() -> tuple[bool, list[StepResult], str]:
    commands = [
        "python tools/check_route_shard_selection.py --self-test",
        "python tools/check_route_shard_selection.py",
    ]
    ok, steps = steps_all_pass(commands)
    return ok, steps, "repair the Dispatch Index / route-shard addendum lockstep, then rerun the checker"


def gate_cold_law_digest() -> tuple[bool, list[StepResult], str]:
    commands = [
        "python tools/check_cold_law_digest.py --self-test",
        "python tools/check_cold_law_digest.py",
    ]
    ok, steps = steps_all_pass(commands)
    return ok, steps, "restore the cold-law digest anti-theater contract in the compiled root, then rerun"


def gate_state_capsule() -> tuple[bool, list[StepResult], str]:
    commands = [
        "python tools/check_state_capsule.py --self-test",
        "python tools/check_state_capsule.py --replay tests/state-capsule-fixtures/valid/multi-call-append",
    ]
    ok, steps = steps_all_pass(commands)
    return ok, steps, "fix the state-capsule shape/replay-invariant violation using the fixture diagnostics"


def gate_staged_runtime_handshake() -> tuple[bool, list[StepResult], str]:
    ok, steps = steps_all_pass(["python tools/check_staged_runtime_handshake.py"])
    return ok, steps, (
        "inspect the failing fixture with --explain-stage-failure and fix the fixture or the checker "
        "(never loosen a floor/canary to pass)"
    )


def gate_mutation_sweep() -> tuple[bool, list[StepResult], str]:
    ok, steps = steps_all_pass(["python tools/gen_fixture_mutations.py --self-test"])
    return ok, steps, "restore the mutation-sweep anti-evasion coverage flagged by the self-test"


def gate_dry_run_emulator() -> tuple[bool, list[StepResult], str]:
    commands = [
        "python tools/daee_dry_run_emulator.py --self-test",
        "python tools/daee_dry_run_emulator.py",
    ]
    ok, steps = steps_all_pass(commands)
    return ok, steps, "fix the stage handoff / capsule-build regression the emulator identified (no model needed)"


def gate_retained_proof_replay() -> tuple[bool, list[StepResult], str]:
    commands = [
        "python tools/check_retained_proof_corpus.py",
        f"python tools/check_owner_activation_ordering.py --require-plan --outputs {RETAINED_OUTPUTS_GLOB}",
        f"python tools/check_tlang_response_closure.py --outputs {RETAINED_OUTPUTS_GLOB}",
        "python tools/check_field_witness_convergence.py",
        "python tools/check_graph_completeness.py",
        "python tools/check_manual_smoke_render_contract.py",
    ]
    ok, steps = steps_all_pass(commands, timeout=LONG_TIMEOUT_SEC)
    return ok, steps, "diagnose via the failing checker's own diagnostics against the retained corpus; do not thin outputs"


def gate_large_output_retained() -> tuple[bool, list[StepResult], str]:
    """This gate does not run a new check of its own. It documents and
    verifies two facts already proven elsewhere so the ledger has an
    explicit line item for the large-output/file-retained property instead
    of leaving it implicit inside gate 11's self-test:

    1. tools/daee_dry_run_emulator.py --self-test (gate 11) includes
       `self_test_large_output_preservation`, which builds a synthetic
       150KB+ artifact and proves the final state capsule stays <16KB and
       replay-consistent. This gate does not re-run that self-test (gate 11
       already did); it only asserts gate 11 passed by re-reading this
       process's own gate table below is out of scope here -- this function
       instead performs the second, independent half: proving a REAL
       retained output (not synthetic) that large exists on disk and is
       exactly the file gate 12 (check_manual_smoke_render_contract etc.)
       already rendered/validated against.
    2. The largest retained proof-corpus output.md is >130KB on disk, i.e.
       the large-output regime is not just a synthetic fixture -- it is the
       real shape of a retained proof case that gate 12 already put through
       render/graph/closure checks.

    What this gate actually proves: a real retained output file over 130KB
    exists at the expected path. It relies on gate 11 (self-test) for the
    synthetic capsule-size proof and on gate 12 for that same file's
    render/graph/closure validity. It does NOT re-validate capsule size or
    render contract itself -- doing so here would be theater (duplicate,
    not independent, coverage). If gate 11 or gate 12 is not also green,
    this gate's pass is necessary but not sufficient.
    """
    start = time.monotonic()
    threshold_bytes = 130_000
    pattern = str(ROOT / RETAINED_OUTPUTS_GLOB)
    matches = sorted(glob.glob(pattern))
    command = f"stat-largest {RETAINED_OUTPUTS_GLOB} (threshold {threshold_bytes} bytes)"
    if not matches:
        step = StepResult(
            command=command,
            argv=[],
            returncode=1,
            stdout="",
            stderr=f"no retained outputs matched {RETAINED_OUTPUTS_GLOB}",
            duration_sec=time.monotonic() - start,
        )
        return False, [step], "restore the retained-proof-corpus case directories"

    sized = [(Path(m), Path(m).stat().st_size) for m in matches]
    largest_path, largest_size = max(sized, key=lambda pair: pair[1])
    duration = time.monotonic() - start
    if largest_size < threshold_bytes:
        step = StepResult(
            command=command,
            argv=[],
            returncode=1,
            stdout="",
            stderr=(
                f"largest retained output is only {largest_size} bytes "
                f"({largest_path}); expected at least {threshold_bytes} bytes"
            ),
            duration_sec=duration,
        )
        return False, [step], "confirm no retained case has been truncated/re-thinned; restore the full-size output"

    step = StepResult(
        command=command,
        argv=[],
        returncode=0,
        stdout=(
            f"largest retained output is {largest_size} bytes ({largest_path.relative_to(ROOT)}); "
            f">= {threshold_bytes} byte large-output/file-retained threshold. "
            "Synthetic capsule-size proof is gate 11's self-test; render/graph/closure proof for this "
            "same file is gate 12. This gate only proves the real large file exists on disk."
        ),
        stderr="",
        duration_sec=duration,
    )
    return True, [step], ""


def load_five_smoke_preflight_rows(
    registry_path: Path = smoke_matrix_registry.DEFAULT_REGISTRY,
    registry_root: Path = ROOT,
) -> tuple[tuple[str, str], ...]:
    """Return Gate 14 rows in canonical registry order after owner validation."""
    registry = smoke_matrix_registry.load_registry(registry_path, registry_root)
    return tuple((row["case_id"], row["input_path"]) for row in registry["cases"])


def gate_five_smoke_input_preflight(
    *,
    registry_path: Path = smoke_matrix_registry.DEFAULT_REGISTRY,
    registry_root: Path = ROOT,
    step_runner: Callable[[str], StepResult] = run_step,
    timestamp: str | None = None,
) -> tuple[bool, list[StepResult], str]:
    registry_command = "in-process: smoke_matrix_registry.load_registry(canonical registry)"
    try:
        rows = load_five_smoke_preflight_rows(registry_path, registry_root)
    except (OSError, ValueError) as exc:
        return False, [
            StepResult(
                command=registry_command,
                argv=[],
                returncode=1,
                stdout="",
                stderr=f"Gate 14 canonical registry validation failed: {exc}",
                duration_sec=0.0,
            )
        ], (
            "restore the immutable five-smoke registry and its exact input byte/hash custody through "
            "tools/smoke_matrix_registry.py before retrying Gate 14"
        )

    steps: list[StepResult] = [
        StepResult(
            command=registry_command,
            argv=[],
            returncode=0,
            stdout=f"validated {len(rows)} canonical rows in registry order",
            stderr="",
            duration_sec=0.0,
        )
    ]
    ok = True
    timestamp = timestamp or time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    for case_id, input_path in rows:
        run_dir = f".daee/no-model-preflight/{timestamp}-{case_id}-input-preflight"
        command = (
            "python tools/run_staged_current_skill_smoke.py --preflight-input-only "
            f"--case-name {case_id} --raw-input-path {input_path} --run-dir {run_dir}"
        )
        result = step_runner(command)
        steps.append(result)
        if result.returncode != 0:
            ok = False
    return ok, steps, (
        "confirm each registry-owned input exists with its canonical bytes/hash and that the run-dir did not already exist; "
        "this mode never invokes a model (verified by reading run_staged_current_skill_smoke.py: "
        "--preflight-input-only returns from preflight_smoke_inputs() before run_model_smoke() is reachable)"
    )


def gate_prompt_pack_manifest_discipline() -> tuple[bool, list[StepResult], str]:
    commands = [
        "python tools/check_prompt_pack_budget.py --self-test",
        "python tools/measure_load_path_budget.py --enforce",
    ]
    ok, steps = steps_all_pass(commands)
    note = (
        "Static preconditions only: no real per-run prompt-pack-manifest.jsonl exists until a model run. "
        "check_prompt_pack_budget.py --self-test proves fixture validation + the static call-site parity "
        "(4/4) the plan requires; measure_load_path_budget.py --enforce proves the eager-list/300k pattern "
        "is absent. Per-run manifests get validated post-run during the matrix via "
        "`check_prompt_pack_budget.py --manifest <run_dir>/prompt-pack-manifest.jsonl` -- that invocation "
        "does not exist yet and is intentionally out of scope for a no-model preflight."
    )
    return ok, steps, "fix the prompt-pack fixture/static parity failure reported by --self-test, or the load-path budget violation"


def gate_first_failed_checker_reporting() -> tuple[bool, list[StepResult], str]:
    start = time.monotonic()
    fixture_path = ROOT / STABLE_EXPLAIN_FIXTURE
    sidecar_path = fixture_path.parent / f"{fixture_path.stem}.expected-explain.json"
    command = f"python tools/check_staged_runtime_handshake.py --explain-stage-failure --records {STABLE_EXPLAIN_FIXTURE}"
    argv = argv_for(command)
    proc = subprocess.run(
        argv,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=DEFAULT_TIMEOUT_SEC,
    )
    duration = time.monotonic() - start
    step = StepResult(
        command=command,
        argv=argv,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        duration_sec=duration,
    )

    if not sidecar_path.exists():
        step.stderr += f"\nmissing expected sidecar: {sidecar_path}"
        return False, [step], "restore the .expected-explain.json sidecar for the stable fixture"

    try:
        expected = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        step.stderr += f"\nsidecar is not valid JSON: {exc}"
        return False, [step], "repair the malformed .expected-explain.json sidecar"

    stdout_lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if len(stdout_lines) != 1:
        step.stderr += f"\nexpected exactly one JSON line on stdout, got {len(stdout_lines)}"
        return False, [step], "the checker's --explain-stage-failure output shape regressed for a single-record call"

    try:
        actual = json.loads(stdout_lines[0])
    except json.JSONDecodeError as exc:
        step.stderr += f"\n--explain-stage-failure did not emit valid JSON: {exc}"
        return False, [step], "the checker's --explain-stage-failure JSON emission regressed"

    expected_class = expected.get("failure_class")
    actual_class = actual.get("failure_class")
    if expected_class is None or actual_class != expected_class:
        step.stderr += (
            f"\nfailure_class mismatch: expected {expected_class!r} (from sidecar), got {actual_class!r}"
        )
        return False, [step], "first-failed-checker classification drifted from the stable fixture's recorded class"

    step.stdout += f"\nfailure_class matches stable fixture sidecar: {actual_class!r}"
    return True, [step], ""


def gate_runtime_context_and_producer_parity() -> tuple[bool, list[StepResult], str]:
    commands = [
        "python tools/check_runtime_context_delivery.py --self-test",
        "python tools/check_runtime_context_delivery.py --fixtures tests/runtime-context-delivery",
        "python tools/check_producer_checker_parity.py --self-test",
        "python tools/check_producer_checker_parity.py --registry tools/producer-contract-registry.json",
        "python tools/check_package_harness_parity.py --self-test",
        "python tests/runtime-call-context-adapter/test_contract.py",
    ]
    ok, steps = steps_all_pass(commands)
    return ok, steps, (
        "reconcile exact runtime-context delivery, immediate prior-capsule lineage, "
        "execution-mini package shape, producer/checker custody, and package parity hashes; "
        "do not relabel harness assistance as package-faithful execution"
    )


@dataclass
class Gate:
    number: int
    name: str
    run: Callable[[], tuple[bool, list[StepResult], str]]


GATES: list[Gate] = [
    Gate(1, "generated-runtime freshness", gate_generated_runtime_freshness),
    Gate(2, "docs freshness", gate_docs_freshness),
    Gate(3, "package shape", gate_package_shape),
    Gate(4, "hot-context budget", gate_hot_context_budget),
    Gate(5, "execution-kernel markers", gate_execution_kernel_markers),
    Gate(6, "route-shard manifest + selection", gate_route_shard_selection),
    Gate(7, "cold-law digest", gate_cold_law_digest),
    Gate(8, "state capsule", gate_state_capsule),
    Gate(9, "Stage01-08 synthetic valid + invalid", gate_staged_runtime_handshake),
    Gate(10, "mutation sweep", gate_mutation_sweep),
    Gate(11, "dry-run emulator", gate_dry_run_emulator),
    Gate(12, "retained-proof replay", gate_retained_proof_replay),
    Gate(13, "large-output/file-retained", gate_large_output_retained),
    Gate(14, "five-smoke input-path preflight", gate_five_smoke_input_preflight),
    Gate(15, "prompt-pack manifest discipline", gate_prompt_pack_manifest_discipline),
    Gate(16, "first-failed-checker reporting", gate_first_failed_checker_reporting),
    Gate(17, "runtime-context + producer/package parity", gate_runtime_context_and_producer_parity),
]


def gate_table_is_well_formed(gates: list[Gate]) -> list[str]:
    errors: list[str] = []
    seen_numbers: set[int] = set()
    for gate in gates:
        if not gate.name or not gate.name.strip():
            errors.append(f"gate {gate.number}: empty name")
        if gate.number in seen_numbers:
            errors.append(f"gate {gate.number}: duplicate gate number")
        seen_numbers.add(gate.number)
        if not callable(gate.run):
            errors.append(f"gate {gate.number} ({gate.name}): run is not callable")
    if [g.number for g in gates] != sorted(g.number for g in gates):
        errors.append("gate numbers are not in ascending order")
    return errors


def aggregate_decision(gate_results: list[GateResult]) -> str:
    """Pure aggregation: AUTHORIZED iff every gate passed and there is at
    least one gate (an empty gate list must never authorize)."""
    if not gate_results:
        return NOT_AUTHORIZED_TOKEN
    if all(result.passed for result in gate_results):
        return AUTHORIZED_TOKEN
    return NOT_AUTHORIZED_TOKEN


def run_self_test() -> int:
    failures: list[str] = []

    table_errors = gate_table_is_well_formed(GATES)
    if table_errors:
        failures.extend(table_errors)

    if len(GATES) != 17:
        failures.append(f"expected exactly 17 gates, found {len(GATES)}")
    parity_gate_present = any(
        gate.number == 17
        and gate.name == "runtime-context + producer/package parity"
        for gate in GATES
    )
    if not parity_gate_present:
        failures.append("Gate 17 runtime-context + producer/package parity is missing")

    for gate in GATES:
        if not gate.name.strip():
            failures.append(f"gate {gate.number}: name required")

    # Most real gates would run subprocesses, so aggregation uses synthetic
    # results. Gate 14 is exercised below with an injected in-memory step
    # runner so its registry binding is also covered without a subprocess.
    all_pass = [
        GateResult(name=g.name, passed=True, repair_lane="") for g in GATES
    ]
    one_fail = [
        GateResult(name=g.name, passed=(i != 0), repair_lane="fix it")
        for i, g in enumerate(GATES)
    ]
    empty: list[GateResult] = []

    if aggregate_decision(all_pass) != AUTHORIZED_TOKEN:
        failures.append("aggregate_decision did not authorize when all gates passed")
    if aggregate_decision(one_fail) != NOT_AUTHORIZED_TOKEN:
        failures.append("aggregate_decision authorized despite one failing gate")
    if aggregate_decision(empty) != NOT_AUTHORIZED_TOKEN:
        failures.append("aggregate_decision authorized with an empty gate list")

    # Exhaustively: for every single-gate-failing configuration, decision
    # must be NOT_AUTHORIZED (not just the i=0 case above).
    for i in range(len(GATES)):
        configuration = [
            GateResult(name=g.name, passed=(j != i), repair_lane="x")
            for j, g in enumerate(GATES)
        ]
        if aggregate_decision(configuration) != NOT_AUTHORIZED_TOKEN:
            failures.append(f"aggregate_decision authorized despite gate index {i} failing")

    if AUTHORIZED_TOKEN != "MATRIX_AUTHORIZED_AFTER_PREFLIGHT":
        failures.append("AUTHORIZED_TOKEN literal drifted")
    if NOT_AUTHORIZED_TOKEN != "MATRIX_NOT_AUTHORIZED":
        failures.append("NOT_AUTHORIZED_TOKEN literal drifted")
    if AUTHORIZED_TOKEN == NOT_AUTHORIZED_TOKEN:
        failures.append("tokens must be distinct")

    gate14_rows_ok = False
    gate14_registry_drift_ok = False
    gate14_input_hash_drift_ok = False
    try:
        registry = smoke_matrix_registry.load_registry()
        expected_rows = tuple(
            (row["case_id"], row["input_path"])
            for row in registry["cases"]
        )
        recorded_commands: list[str] = []

        def record_gate14_step(command: str) -> StepResult:
            recorded_commands.append(command)
            return StepResult(
                command=command,
                argv=[],
                returncode=0,
                stdout="",
                stderr="",
                duration_sec=0.0,
            )

        gate14_passed, gate14_steps, _ = gate_five_smoke_input_preflight(
            step_runner=record_gate14_step,
            timestamp="20000101-000000",
        )
        expected_commands = [
            "python tools/run_staged_current_skill_smoke.py --preflight-input-only "
            f"--case-name {case_id} --raw-input-path {input_path} "
            f"--run-dir .daee/no-model-preflight/20000101-000000-{case_id}-input-preflight"
            for case_id, input_path in expected_rows
        ]
        gate14_rows_ok = (
            len(expected_rows) == 5
            and load_five_smoke_preflight_rows() == expected_rows
            and gate14_passed
            and len(gate14_steps) == 6
            and recorded_commands == expected_commands
        )

        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            drifted_registry = json.loads(json.dumps(registry))
            drifted_registry["cases"][0]["case_id"] += "-drift"
            drifted_registry_path = temporary_root / "registry.json"
            drifted_registry_path.write_text(
                json.dumps(drifted_registry),
                encoding="utf-8",
            )
            unexpected_steps: list[str] = []

            def record_unexpected_step(command: str) -> StepResult:
                unexpected_steps.append(command)
                return record_gate14_step(command)

            drift_passed, drift_steps, _ = gate_five_smoke_input_preflight(
                registry_path=drifted_registry_path,
                registry_root=ROOT,
                step_runner=record_unexpected_step,
            )
            gate14_registry_drift_ok = (
                not drift_passed
                and len(drift_steps) == 1
                and "registry_identity" in drift_steps[0].stderr
                and not unexpected_steps
            )

        with tempfile.TemporaryDirectory() as directory:
            mirror = Path(directory)
            for row in registry["cases"]:
                source = ROOT / row["input_path"]
                target = mirror / row["input_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            first = mirror / registry["cases"][0]["input_path"]
            raw = first.read_bytes()
            replacement = b"X" if raw[:1] != b"X" else b"Y"
            first.write_bytes(replacement + raw[1:])
            unexpected_steps = []
            hash_passed, hash_steps, _ = gate_five_smoke_input_preflight(
                registry_path=smoke_matrix_registry.DEFAULT_REGISTRY,
                registry_root=mirror,
                step_runner=record_unexpected_step,
            )
            gate14_input_hash_drift_ok = (
                not hash_passed
                and len(hash_steps) == 1
                and "registry_input_hash" in hash_steps[0].stderr
                and not unexpected_steps
            )
    except (OSError, ValueError) as exc:
        failures.append(f"Gate 14 registry canary could not run: {exc}")

    if not gate14_rows_ok:
        failures.append("Gate 14 did not derive exactly five ordered canonical registry rows")
    if not gate14_registry_drift_ok:
        failures.append("Gate 14 did not reject registry tuple drift as registry_identity")
    if not gate14_input_hash_drift_ok:
        failures.append("Gate 14 did not reject same-length input drift as registry_input_hash")

    for name, ok in (
        ("gate table well-formed", not table_errors),
        ("17 gates present", len(GATES) == 17),
        ("Gate 17 runtime-context + producer/package parity present", parity_gate_present),
        ("aggregate authorizes only when all pass", aggregate_decision(all_pass) == AUTHORIZED_TOKEN),
        ("aggregate rejects on any single failure", all(
            aggregate_decision(
                [GateResult(name=g.name, passed=(j != i), repair_lane="x") for j, g in enumerate(GATES)]
            ) == NOT_AUTHORIZED_TOKEN
            for i in range(len(GATES))
        )),
        ("aggregate rejects empty gate list", aggregate_decision(empty) == NOT_AUTHORIZED_TOKEN),
        ("decision tokens exact + distinct", AUTHORIZED_TOKEN == "MATRIX_AUTHORIZED_AFTER_PREFLIGHT"
            and NOT_AUTHORIZED_TOKEN == "MATRIX_NOT_AUTHORIZED"),
        ("Gate 14 derives exactly five ordered registry rows", gate14_rows_ok),
        ("Gate 14 rejects registry identity drift", gate14_registry_drift_ok),
        ("Gate 14 rejects input hash drift", gate14_input_hash_drift_ok),
    ):
        print(f"  self-test {'PASS' if ok else 'FAIL'}: {name}")

    ok = not failures
    print(f"run_no_model_preflight self-test: {'PASS' if ok else 'FAIL'}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


def step_tail(step: StepResult, limit: int = 2000) -> str:
    combined = (step.stdout or "") + (("\n" + step.stderr) if step.stderr else "")
    combined = combined.strip()
    if len(combined) > limit:
        combined = combined[-limit:]
    return combined


def print_banner() -> None:
    print("=" * 78)
    print("run_no_model_preflight: composed no-model stop-line gate (Plan 12 Section 3)")
    print("This tool NEVER runs a model smoke. The five-smoke matrix remains owner-gated.")
    print("=" * 78)


def run_full_sweep(json_path: Path | None) -> int:
    print_banner()
    gate_results: list[GateResult] = []

    for gate in GATES:
        print(f"[gate {gate.number}/{len(GATES)}] {gate.name} ...", flush=True)
        try:
            passed, steps, repair_lane = gate.run()
            note = ""
        except Exception as exc:  # defensive: a crashing gate must still be reported, not abort the sweep
            passed = False
            steps = [
                StepResult(
                    command=f"<gate {gate.number} raised>",
                    argv=[],
                    returncode=1,
                    stdout="",
                    stderr=f"{type(exc).__name__}: {exc}",
                    duration_sec=0.0,
                )
            ]
            repair_lane = "gate implementation raised an exception; fix run_no_model_preflight.py's gate function"
            note = "internal error"

        result = GateResult(name=gate.name, passed=passed, repair_lane=repair_lane, steps=steps, note=note)
        gate_results.append(result)

        status = "PASS" if passed else "FAIL"
        print(f"[gate {gate.number}/{len(GATES)}] {gate.name}: {status}")
        if not passed:
            for step in steps:
                if step.returncode != 0:
                    print(f"    command: {step.command}")
                    print(f"    exit code: {step.returncode}")
                    tail = step_tail(step)
                    if tail:
                        for line in tail.splitlines()[-40:]:
                            print(f"    | {line}")

    decision = aggregate_decision(gate_results)

    if decision == NOT_AUTHORIZED_TOKEN:
        print("")
        print("repair lanes:")
        for result in gate_results:
            if not result.passed:
                print(f"- [{result.name}] {result.repair_lane}")

    print("")
    print("gate ledger:")
    for result in gate_results:
        print(f"  {'PASS' if result.passed else 'FAIL'}  {result.name}")

    if json_path is not None:
        report = {
            "schema": "daee-no-model-preflight-report-v1",
            "decision": decision,
            "gates": [
                {
                    "number": gate.number,
                    "name": result.name,
                    "passed": result.passed,
                    "repair_lane": result.repair_lane,
                    "steps": [
                        {
                            "command": step.command,
                            "returncode": step.returncode,
                            "duration_sec": round(step.duration_sec, 3),
                            "timed_out": step.timed_out,
                            "stdout_tail": step_tail(step) if not result.passed else "",
                        }
                        for step in result.steps
                    ],
                }
                for gate, result in zip(GATES, gate_results)
            ],
        }
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"json report written: {json_path}")

    print("")
    print(decision)
    return 0 if decision == AUTHORIZED_TOKEN else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true", help="validate gate-table shape and decision aggregation only; no subprocesses")
    parser.add_argument("--json", type=Path, default=None, help="path to write a machine-readable JSON report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()
    return run_full_sweep(args.json)


if __name__ == "__main__":
    sys.exit(main())
