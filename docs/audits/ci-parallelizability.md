# CI Parallelizability Analysis (Plan 08, Lane K)

> A static A/B proof of what can and cannot safely parallelize in the local CI
> battery, produced by `tools/analyze_ci_parallelizability.py` (deterministic,
> read-only; wired `--self-test` in CI). No live parallel run was performed — a
> live parallel run would race the shared generated files by construction, which
> is exactly the hazard proven below. **CI execution is unchanged; parallelization
> is NOT adopted.** Measured 2026-07-04 over 90 commands.

## Classification

| Category | Count | Why it is a parallel hazard (or not) |
| --- | ---: | --- |
| shared-writer | 3 | `build_framework_pipeline`, `build_compiled_runtime`, and the pwsh smoke mutate shared generated artifacts (`atomics/.../framework-pipeline.md`, `skill/SKILL.md`, `.daee/`). Racing two of these corrupts the artifact. |
| git-gate | 3 | `git diff --exit-code -- skill/SKILL.md`, the framework-pipeline diff, and `git diff --check` READ tree state; they must run AFTER the generators that produce what they inspect. |
| read-only | 84 | `check_*`/`verify_*`/`gen_*`/`measure_*`/`*-self-test`/`py_compile` — side-effect-free over already-produced artifacts; independent of each other. |

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

- It does not claim the 82 read-only commands are mutually independent at the
  data level beyond side-effect freedom (they all read the same artifacts, which
  is safe for concurrent reads).
- It does not measure wall-clock speedup; the point is safety, not speed. Since
  the serial prefix (generators) dominates, the achievable speedup from
  parallelizing only the read-only phase is bounded and unquantified here.
