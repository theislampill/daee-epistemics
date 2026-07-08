# Staged Smoke Maintenance

Measurement-only maintenance reference for `tools/run_staged_current_skill_smoke.py`
and its supporting instrumentation (prompt-pack manifest, capsule emission,
`--explain-stage-failure`, static call-site parity). Use this when adding a
new model call site or diagnosing a staged-smoke failure without weakening
the runtime it validates.

## Harness anatomy pointers

Each of the 7 model-producing stages (see
`docs/stage-contract-workbench.md` for the full stage map) is driven by a
per-stage prompt built by `run_staged_current_skill_smoke.py`. The prompt
carries:

- a **hash** of the relevant prior state (identity/continuity check), and
- **`compact_state`**, a small JSON projection of what the model needs to
  continue -- never the full artifact, never `SKILL.md`, never any
  `runtime-*.md` bundle.

This is the same discipline the state capsule formalizes for recursion (see
`docs/recursive-state-capsule.md`): a call receives compact structured state,
not a replay of everything that came before. If you are adding a new
call site and find yourself tempted to pass the growing artifact or a full
runtime bundle "just to be safe," that is the anti-pattern this
instrumentation exists to catch -- see "budget checker" below.

## Prompt-pack manifest + budget checker

Every model call site in the harness emits one JSON line to
`<run_dir>/prompt-pack-manifest.jsonl` (schema `daee-prompt-pack-manifest-v1`)
**before** invocation, via `emit_prompt_pack_manifest(...)`. The manifest
line records component byte accounting (measured from outside the
composition functions, so it cannot share a bug with what it measures),
`includes_full_runtime` (byte-threshold + verbatim-probe + whitespace-
normalized-probe detection), and `includes_prior_full_output`.

Validate a manifest:

```
python tools/check_prompt_pack_budget.py --manifest <run_dir>/prompt-pack-manifest.jsonl
python tools/check_prompt_pack_budget.py --self-test
```

The checker validates manifest schema, exact component-sum and est-tok
arithmetic, fails closed on `includes_full_runtime` /
`includes_prior_full_output`, enforces a per-call ceiling, and -- separately --
runs a **static call-site parity** self-test: it reads the harness source and
fails if any `invoke_model(` call site lacks a matching
`emit_prompt_pack_manifest(` call site. This is a static source-grep, not a
runtime check, so it catches a missing manifest call even if that code path
is never exercised by a fixture.

### Adding a model call site

If you add a new `invoke_model(` call anywhere in
`run_staged_current_skill_smoke.py`, you must add a matching
`emit_prompt_pack_manifest(` call at the same site, or the static parity
self-test fails. There is currently no way to opt a call site out of this
requirement -- that is deliberate.

## Capsule emission + validate-then-write + replay gate

After every validated stage, and again at Stage-07 completion, the harness
calls `build_state_capsule()` and validates the result in-process via
`check_state_capsule.py` before writing it. Two properties matter for
maintenance:

- **Validate-then-write**: an invalid capsule is quarantined as
  `capsule-NNN.invalid.json` and is never written at the canonical
  `capsule-NNN.json` name. A negative self-test in the harness asserts this
  directly -- do not "fix" a validation failure by relaxing this quarantine.
- **Hard replay gate at Stage-07 completion**: the harness runs a full-
  sequence replay over the real run directory and `output.md`; any replay
  failure raises `HarnessError` and aborts the run. This is a run-integrity
  gate, not observability -- a run that fails replay is not a successful run
  with a logged warning.

See `docs/recursive-state-capsule.md` for the capsule contract itself and
`docs/load-path-architecture.md` for why capsules exist instead of full
artifact replay.

## --explain-stage-failure output

On a stage failure, the harness prints:

```
EXPLAIN-STAGE-FAILURE: {"stage": ..., "failure_class": ..., "earliest_stage": ...,
  "downstream_invalidated": ..., "requires_model_rerun": ..., "repair_lane": ...}
```

before raising, by calling `check_staged_runtime_handshake.py`'s own
`--explain-stage-failure` classifier -- the mapping is not duplicated in the
harness. See `docs/stage-contract-workbench.md` for the full failure-class
taxonomy and the earliest-failure-locality rule this output follows.

Use this JSON, not raw exception text, as the first thing you read when a
staged smoke fails: it tells you the failure class, whether downstream
stages are invalidated by it, and whether the repair belongs in the checker,
the harness, or requires an actual model rerun.

## Keeping static call-site parity green

When adding, renaming, or refactoring a model call site:

1. Add the `invoke_model(...)` call and the `emit_prompt_pack_manifest(...)`
   call together, in the same commit.
2. Run `python tools/check_prompt_pack_budget.py --self-test` before
   considering the change done -- this is the only thing that actually
   exercises the static parity scan.
3. If the self-test's call-site count changes (currently 4 known sites:
   the stage 01-06 loop, Stage-07 compiled sections, the legacy Stage-07
   `release_prompt` fallback, and the Stage-07 section-expansion retry
   path), update any hardcoded expectation in the self-test deliberately --
   do not silence the check by loosening its source-grep pattern.
4. Re-run `python tools/run_staged_current_skill_smoke.py --self-test` to
   confirm harness wiring (this proves wiring only, not model behavior).

## Related no-model tooling

- `python tools/daee_dry_run_emulator.py --self-test` -- full Stage01-08
  dry run with no model call, reusing the harness's own
  `build_state_capsule()` and the handshake checker's error classifiers.
- `python tools/check_route_shard_selection.py --self-test` -- proves the
  dispatch index the harness's prompts route through is well-formed.
- `python tools/measure_load_path_budget.py --enforce-ratchet --enforce` --
  proves the budget ceilings a call site's manifest is measured against are
  themselves not regressing.

None of these replace an actual model smoke; they bound the architecture so
that a model smoke failure is never spent re-diagnosing a bug one of these
could have caught for free.
