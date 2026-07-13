# Task 3b command-timeout and stale-log repair independent rereview

Date: 2026-07-12
Reviewer: `/root/task5_retention`
Implementation owner: `/root/task3b_ci_receipt`
Verdict: `ACCEPT`
Findings: `0 Critical / 0 Important / 0 Minor`

## Independence and exact reviewed identity

The reviewer did not author the reviewed Task 3b workflow, writer, checker, local-CI
runner, fixture-builder, support-log, receipt, registry, or ledger bytes. This review is
limited to the final timeout/stale-log repair identified by:

- complete `tests/ci-readback/**` cohort: `153` files / `180997` bytes /
  `e79347282fde0397e3caa6db7ad49d327d78cb89664150c7abe91564c80a1366`;
- de-duplicated Task 3b integration scope: `163` paths / `510184` bytes /
  `aba89e4abdbff59db6c7f6052a7009f6d7c64a5b953feaf9d7f2c9c15c3f17fc`;
- owner report: `7962` bytes /
  `a163d50341004c3fdf69178e6a65baa2827ad3e1a6212995a34c04729b34eb1c`.

Both aggregates were independently recomputed from the live checkout with sorted UTF-8
rows `path NUL byte_count NUL sha256 LF` before inspection and again after all focused
commands. All three supplied identities matched exactly both times.

## Reviewed joins

- `.github/workflows/ci.yml`, `write_task7_deterministic_evidence.py`, and
  `check_ci_readback.py` bind the identical full-local-CI command:
  `python tools/run_local_ci.py --strict-pwsh --command-timeout-seconds 900`.
- `run_local_ci.py` executes each command in a Windows process group or POSIX session.
  Timeout cleanup terminates the owned Windows tree with `taskkill /T /F` or the POSIX
  process group with TERM followed by KILL, reaps the root, returns `124`, breaks the
  command loop, and therefore cannot start the next command.
- The Task 7 writer applies a distinct `7200`-second outer role timeout through the same
  owned-command runner. A timed-out role raises typed `Task7RoleTimeout` with return code
  `124` before command-log, report, or deterministic-verdict publication.
- The governed raw Linux support log retains the exact bounded full-local-CI marker once.
  Direct replay through production `_a01_log()` returned a `434`-byte segment with SHA-256
  `42e8e6980e8c609e4aa039403a120ca34314e7cc71421fee171173a127fda86b`,
  `(test_count, status, skipped) == (23, "OK", 0)`, and raw-log identity `705` bytes /
  `b9cdbd0358fa511cbfe07c5323b70d93e9db77e82c40e610a0a5db7238d87e8a`.
  The valid receipt binds the same raw-log and parsed-segment hashes.
- The canonical fixture builder derives that marker from the writer role command, parses
  the generated raw log through production code, and owns the refreshed receipt/support
  hashes. Its timeout-drift cohort removes only `--command-timeout-seconds 900` from an
  otherwise internally consistent full-local-CI evidence bundle; production validation
  rejects it at `deterministic_verdicts/role-command`.

## Focused verification

- `python -B -m unittest tests/ci-readback/test_contract.py -v` — `35/35 PASS`.
  The Windows timeout regression observed exit `124`, no next-command marker, and both
  owned child/grandchild PIDs exited. The separate Task 7 outer-timeout regression also
  observed typed exit `124` and both owned PIDs exited.
- `python -B tools/check_ci_readback.py --self-test` — `PASS`, `1` valid / `60`
  right-reason invalid, with no external evidence written.
- `python -B tests/ci-readback/build_task7_fixtures.py --check` — `PASS`, exact
  `27`-file cohort.
- `python -B tools/write_task7_deterministic_evidence.py --self-test` — `PASS`, including
  schema, freeze identity, create-once publication, and replay rejection.
- Pre-test and post-test Windows process readback found zero matching Task 7/local-CI
  timeout children or grandchildren. `%TEMP%` contained zero owned
  `daee-local-ci-timeout-*` or `daee-task7-timeout-*` directories after the suite.
- The only `tests/ci-readback` directory residue was an empty pre-existing
  `__pycache__` directory timestamped before this rereview; `-B` prevented this review's
  commands from creating bytecode residue. It was not modified or deleted.

## Disposition and nonclaims

The exact reviewed Task 3b timeout/stale-log repair is bounded-approved. No source edit,
fixture regeneration, full local CI, no-model preflight, live GitHub query, external
Task 7 role, candidate action, provider/model call, commit, push, tag, release, or
publication was performed by this review.

This ACCEPT is not POSIX runtime proof, exact-SHA GitHub CI, source-receipt issuance,
deterministic whole-branch closure, candidate maturity, model authorization, reviewed
smoke success, release readiness, owner acceptance, or terminal A16 closure. The POSIX
session/process-group branch remains subject to its normal Linux CI execution before any
POSIX runtime-proof claim.
