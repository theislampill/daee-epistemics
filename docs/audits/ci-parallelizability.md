# CI Parallelizability Analysis (Plan 08, Lane K)

> A static A/B proof of what can and cannot safely parallelize in the local CI
> battery, produced by `tools/analyze_ci_parallelizability.py` (deterministic,
> read-only; wired `--self-test` in CI). No live parallel run was performed — a
> live parallel run would race the shared generated files by construction, which
> is exactly the hazard proven below. **CI execution is unchanged; parallelization
> is NOT adopted.** Measured 2026-07-04 over 91 commands.

## Classification

| Category | Count | Why it is a parallel hazard (or not) |
| --- | ---: | --- |
| shared-writer | 3 | `build_framework_pipeline`, `build_compiled_runtime`, and the pwsh smoke mutate shared generated artifacts (`atomics/.../framework-pipeline.md`, `skill/SKILL.md`, `.daee/`). Racing two of these corrupts the artifact. |
| git-gate | 3 | `git diff --exit-code -- skill/SKILL.md`, the framework-pipeline diff, and `git diff --check` READ tree state; they must run AFTER the generators that produce what they inspect. |
| read-only | 85 | `check_*`/`verify_*`/`gen_*`/`measure_*`/`*-self-test`/`py_compile` — side-effect-free over already-produced artifacts; independent of each other. |

## Verdict — PARTIAL / NOT SAFE as a drop-in

- The 3 shared-writers and 3 git-gates are **order-sensitive**: generators must
  run first, then the git-gates verify their output, then the read-only phase
  runs over that output. None of these six can run concurrently with each other
  or with the read-only phase.
- Only the 82 read-only commands could parallelize, and only **as a phase gated
  behind the serial generate-then-verify prefix**. Doing so would also trade away
  the current first-failure-abort semantics (a parallel phase runs all commands
  rather than stopping at the first failure), changing operator behavior.
- Net: there is no safe drop-in parallelization. Any parallelization must be
  phase-staged (serial generate → serial git-gate → parallel read-only) and is an
  explicit behavior change, so it is **not adopted here**. The proof harness and
  this report are the deliverable; actual parallelization remains owner-gated on
  the phase-staging + abort-semantics decision.

## What this does not claim

- It does not claim the 85 read-only commands are mutually independent at the
  data level beyond side-effect freedom (they all read the same artifacts, which
  is safe for concurrent reads).
- It does not measure wall-clock speedup; the point is safety, not speed. Since
  the serial prefix (generators) dominates, the achievable speedup from
  parallelizing only the read-only phase is bounded and unquantified here.

## Adoption decision (2026-07-04)

**Parallelization is REJECTED / DEFERRED for the hardening PR.** The static proof
above already shows no safe drop-in: the 3 shared-writers and 3 git-gates are
order-sensitive, and only the 85 read-only commands could parallelize — and only as
a phase gated behind the serial generate-then-verify prefix, which also trades away
the current first-failure-abort semantics. Adopting it is an owner decision, not a
safe-local slice, and the wall-clock win is unquantified.

What landed instead (measurement, no behavior change): a pure `benchmark_summary()`
helper in `tools/analyze_ci_parallelizability.py` (commit `1cf82c6`) that, from
measured per-command wall times, computes the phase-staged Amdahl ceiling —
`ceiling(N) = shared_writer_s + git_gate_s + read_only_s / N`, `speedup(N) =
serial_total / ceiling(N)` — an upper bound (perfect balance, zero overhead), not a
measured run and not authorization to adopt. It is exercised by the existing
`--self-test`; a live `--benchmark` runner that would time the real battery stays a
deferred, manual, non-lane-wired tool (it re-runs the shared-writers).

Owner decisions, recorded for a later dedicated pass:

- **OD-08a (adopt phase-staging):** accept a `serial generate -> serial git-gate ->
  parallel read-only` model, or reject/keep the serial thin runner. **Recommended:
  reject/defer** — zero correctness gain, real ordering-hazard regression surface (a
  reordered generate/verify could let a corrupted `skill/SKILL.md` pass), unquantified win.
- **OD-08b (abort policy, only if OD-08a accepts):** fail-fast (cancel in-flight on
  first failure; minimal delta from today's stop-at-first) vs run-all-collect (report
  every failure; larger behavioral departure). Recommended fail-fast if ever adopted.
- **OD-08c (measurement prerequisite):** authorize the manual live `--benchmark`
  runner before any adoption, so the win is measured rather than assumed.

Until an owner adopts OD-08a, CI execution stays exactly as-is: serial, first-failure-abort.
