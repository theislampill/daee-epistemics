# Stage Contract Workbench

Plan 13, Slice H (`Sec 3` + `Sec 7`): a per-stage mutation sweep proving each
stage of `tools/check_staged_runtime_handshake.py` FAILS FOR THE RIGHT REASON
before any model spend.

## Layout

One directory per staged-runtime-handshake stage:

```
stage-01-intake/
stage-02-layer-a-diagnostic-ir/
stage-03-routing-owner-gate/
stage-04-burden-execution-act/
stage-05-mrp-reread-terminal-state/
stage-06-field-witness-nar/
stage-07-release-output/
stage-08-verifier-sidecars/
```

Each stage directory has three subdirectories:

- `minimal-valid/` — one record that stops at (or passes through) this stage
  with the smallest shape the checker accepts.
- `maximal-valid/` — one record exercising this stage's richer optional
  structure (multi-burden detail objects, generated-burden RECURSE/LoopBreak
  chains, structured NAR, release_validation, sidecar claims, etc). Where the
  mission calls for a REAL structural difference (stage-05 in particular),
  maximal-valid is not minimal-valid with padding: it adds a second,
  MRP-generated burden with a distinct terminal state, dependency edge,
  `per_burden_reread` LoopBreak entry, and `terminal_state_details`.
- `invalid/` — at least 3 variants that fail against
  `check_staged_runtime_handshake.py`, each with a companion
  `expected.<name>.json` diagnostic sidecar recording `{stage,
  failure_class_hint, checker, provenance}`. This checker family does not
  itself consume `expected.*` sidecars the way the mrp-route-invariants /
  mid-reread-pressure / tlang-response-closure families do (see
  `docs/fixture-taxonomy.md` section 5) — they are documentation/anti-drift
  pins for this workbench, not enforced by the checker's own invalid-loop.

All fixtures are individually verified against
`python tools/check_staged_runtime_handshake.py --records <file>`:
minimal/maximal-valid fixtures must exit 0 (PASS); invalid fixtures must
exit nonzero (FAIL) with at least one error line naming the fixture.

## How the invalid variants relate to the sweep tool

`tools/gen_fixture_mutations.py` implements a STAGE-RECORD mutation family
(`STAGE_RECORD_OPERATORS`) that takes a valid staged record and mechanically
applies one of 14 operators (delete-required-field x6, corrupt-body_ref,
swap-owner-operation, replace-controlled-delta-with-prose, drop-mrp-block,
fake-no-new-resultant, move-burden-bmrp-to-bla, omit-generated-by,
remove-owner-activations-mirror, slim-public-while-sidecar-rich,
set-coverage-complete-despite-unresolved, absolute-sidecar-path), each
carrying `{stage, failure_class_hint, checker}` metadata.

Most `invalid/` fixtures in this directory are the on-disk, hand-finished
form of one of those operators applied to a golden record (either
`tests/staged-runtime-handshake/valid/retained-a9-science-source.json` or
`tests/staged-runtime-handshake/valid/stage05-generated-provenance.json` for
the generated-burden-specific operators). Their `expected.*.json` sidecar
names the operator in its `provenance` field. A few invalid variants are
instead minimal-pairs of existing fixtures under
`tests/staged-runtime-handshake/invalid/` (named in `provenance`) chosen to
cover a stage-03/stage-04 signature the operator set does not target
directly (e.g. `route_target_details` naming an unknown burden, an ACT row
missing `Land(...)`).

### Regenerating the sweep

To regenerate the mechanical (record-only) mutants and see which stages'
operators reach full checker-rejection verification vs manifest-only:

```
python tools/gen_fixture_mutations.py --sweep \
  tests/staged-runtime-handshake/valid/retained-a9-science-source.json \
  --out-dir <scratch-dir-outside-tests/>
```

This writes one mutated JSON per applicable operator plus a
`sweep-manifest.json` recording, per operator: `expected_stage`,
`expected_class_hint`, `expected_checker`, and `verdict`
(`rejected` / `survivor` / `skipped-not-applicable` /
`no-op-identical-to-source` / `manifest-only-not-checker-verified`).

Three operators (`drop-mrp-block`, `move-burden-bmrp-to-bla`,
`omit-generated-by`) are not applicable to the plain `retained-a9-science-source`
record (it has no `generated_burdens`); run the sweep against
`tests/staged-runtime-handshake/valid/stage05-generated-provenance.json`
instead to exercise `move-burden-bmrp-to-bla` and `omit-generated-by` (both
reach `rejected`/full there). `drop-mrp-block` additionally requires an
existing multi-entry `per_burden_reread` block, which neither official golden
record carries; run the sweep against
`tests/stage-contract-workbench/stage-05-mrp-reread-terminal-state/maximal-valid/generated-burden-recurse-with-loopbreak.json`
(this workbench's own maximal-valid fixture) to see it reach full
checker-rejection verification.

### Verification depth: full vs manifest-only vs known-gap

- **full** — the sweep writes the mutated record to disk and invokes
  `tools/check_staged_runtime_handshake.py --records <mutant>` via
  subprocess, asserting nonzero exit. This is real, executed rejection
  evidence, not a hand-wave.
- **manifest-only** (`slim-public-while-sidecar-rich`) — this operator's
  target is the *rendered* `release_output` Markdown artifact, which the
  record-only sweep does not generate. The manifest honestly marks this
  `expected_checker: "render-family"` and does NOT claim checker rejection
  for the bare record. This workbench's own
  `stage-07-release-output/invalid/slim-public-output-below-structural-minimum.json`
  supplies a real, hand-authored slimmed `.output.md` artifact instead, so
  IT is fully checker-verified even though the generic sweep operator is not.
- **known-gap** (`delete-required-field-stage-01-intake`) — confirmed
  reproducible non-rejection: `check_staged_runtime_handshake.py` has a
  dedicated field-presence validator for stages 02-06 but not for stage-01,
  so deleting stage-01's `input_digest` is NOT rejected (verified against
  both golden records, 2026-07-06). This is a real checker gap, out of scope
  to fix here (this task may only touch `tools/gen_fixture_mutations.py` and
  NEW fixtures, not the checker). The sweep records this honestly in
  `tools/gen_fixture_mutations.py`'s `KNOWN_CHECKER_GAPS` dict and reports it
  as a FINDING rather than silently passing or hiding it.
  `stage-01-intake/invalid/` therefore does NOT include a
  delete-required-field variant; it instead uses a malformed-hash variant
  (which the generic `sha_errors()` format check DOES catch), a
  missing-handoff variant, and a stage_order variant.

## Fixture kinds used here

Per `docs/fixture-taxonomy.md` section 1: most `invalid/` fixtures here are
`invalid-single-signature` (one pinned reason). A few are `composite-historical`
(carry multiple cascading signatures because a minimal no-model-fixture stub
in an unrelated stage also trips independent checks) — these are marked
`"kind": "composite-historical"` in their `expected.*.json` sidecar and note
which signature is primary.
