# Stage Contract Workbench

Measurement-only reference for the per-stage mutation sweep and fixture
workbench landed in Slice H (`f713acd`). This proves, without any model
spend, that each of the 8 staged-runtime-handshake stages fails for the
right reason when its contract is violated.

## Stage01-08 contract map

`tools/check_staged_runtime_handshake.py` validates the no-model staged
handoff record across 8 stages:

| Stage | Name | Produced by |
| --- | --- | --- |
| 01 | intake | model |
| 02 | Layer-A diagnostic IR | model |
| 03 | routing / owner gate | model |
| 04 | burden execution (ACT rows) | model |
| 05 | MRP reread / terminal state | model |
| 06 | field-witness NAR | model |
| 07 | release output | model |
| 08 | verifier sidecars | **no-model** |

Stages 01-07 are model-produced records validated by field-presence and
handoff-key checks; Stage 08 is deliberately no-model -- it is where sidecar
verifiers (checkers) run over the completed record, not another model call.
Keep this distinction when writing new fixtures: a Stage-08 fixture proves
sidecar/checker shape, not a model behavior.

## Workbench fixture layout

```
tests/stage-contract-workbench/
  stage-01-intake/
  stage-02-layer-a-diagnostic-ir/
  ...
  stage-08-verifier-sidecars/
```

Each stage directory has three subdirectories (see
`tests/stage-contract-workbench/README.md` for the authoritative version of
this description):

- `minimal-valid/` -- one record that stops at or passes through this stage
  with the smallest accepted shape.
- `maximal-valid/` -- one record exercising the stage's richer optional
  structure. Where the mission calls for a real structural difference (not
  minimal-valid with padding), it has one: stage-05's maximal-valid fixture
  adds a second MRP-generated burden with a distinct terminal state, a
  dependency edge, a `per_burden_reread` LoopBreak entry, and
  `terminal_state_details`.
- `invalid/` -- at least 3 variants that fail against
  `check_staged_runtime_handshake.py`, each with a companion
  `expected.<name>.json` sidecar recording `{stage, failure_class_hint,
  checker, provenance}`. These sidecars are documentation/anti-drift pins
  for this workbench; they are not consumed by the checker's own
  invalid-fixture loop the way `mrp-route-invariants` /
  `mid-reread-pressure` / `tlang-response-closure` family sidecars are (see
  `docs/fixture-taxonomy.md` section 5).

Verify any fixture directly:

```
python tools/check_staged_runtime_handshake.py --records <fixture.json>
```

Minimal/maximal-valid fixtures must exit 0; invalid fixtures must exit
nonzero with at least one error line naming the fixture.

## Mutation sweep operators + how to run

`tools/gen_fixture_mutations.py` implements `STAGE_RECORD_OPERATORS`: 14
mechanical mutation operators applied to a valid staged record (delete a
required field per stage x6, corrupt `body_ref`, swap owner/operation,
replace a controlled delta with prose, drop the MRP block, fake
`no_new_resultant`, move a burden from `B_MRP` to `B_LA`, omit
`generated-by`, remove the owner-activations mirror, slim the public output
while the sidecar stays rich, set `coverage_complete` despite an unresolved
burden, and use an absolute sidecar path).

```
python tools/gen_fixture_mutations.py --sweep \
  tests/staged-runtime-handshake/valid/retained-a9-science-source.json \
  --out-dir <scratch-dir-outside-tests/>
python tools/gen_fixture_mutations.py --self-test
```

`--sweep` writes one mutated JSON per applicable operator plus a
`sweep-manifest.json` recording, per operator: `expected_stage`,
`expected_class_hint`, `expected_checker`, and `verdict` (`rejected` /
`survivor` / `skipped-not-applicable` / `no-op-identical-to-source` /
`manifest-only-not-checker-verified`). `--self-test` asserts genuine
subprocess rejection, not a hand-wave.

Three operators need a different source record because the plain golden
record has no `generated_burdens`:
`tests/staged-runtime-handshake/valid/stage05-generated-provenance.json`
exercises `move-burden-bmrp-to-bla` and `omit-generated-by`; the workbench's
own stage-05 `maximal-valid/generated-burden-recurse-with-loopbreak.json`
is needed for `drop-mrp-block` (requires a multi-entry `per_burden_reread`
block neither official golden record carries).

## Failure-class taxonomy and --explain-stage-failure

`check_staged_runtime_handshake.py --explain-stage-failure` classifies a
failing record into
`{stage, failure_class, earliest_stage, downstream_invalidated,
requires_model_rerun, repair_lane}` JSON, one line per record. The taxonomy
covers every existing error family: custody, sequence, non-claim,
burden-floor, owner-route, `act_body_ref`, MRP, field-witness,
public-projection, sidecar, and handoff. `unclassified` is a real fallback
bucket, but the self-test fails if any real fixture ever lands in it -- the
mapping is total by construction, not by omission.

`requires_model_rerun` is `false` for every class this checker emits: it
judges static records only. The genuinely model-observed
pragmatic/uptake family (e.g. concession/uptake laundering) lives in the
render checkers, not here -- do not conflate a static-record classification
with a claim about live model behavior.

## Earliest-failure locality

Classification scans the *full* error list for a record and reports the
lowest-stage violation, because the first error in pipeline order is often
an unrelated upstream gap rather than the actual defect under test. When
debugging a fixture that fails "for the wrong stage," check whether an
earlier, unrelated field is also malformed before assuming the classifier is
wrong.

`tools/daee_dry_run_emulator.py` uses the same discipline end-to-end: it
walks stages 01-08 in order over a full record with **no model call**,
reusing `record_errors()`/`classify_record_errors()`, `build_state_capsule()`,
and `check_route_shard_selection.py`'s live dispatch-index preflight (all
imported, not reimplemented), and stops at the first failed stage, printing
the same explain-stage-failure JSON shape. Run it directly:

```
python tools/daee_dry_run_emulator.py --record <staged-record.json>
python tools/daee_dry_run_emulator.py --self-test
```

## When to add a canary vs. when not to

Add a canary (new named invalid fixture + sidecar) when it targets a
**basis family** -- a mutation class that could recur across many records
(a new field-deletion operator, laundering channel, or handoff-key
omission). Basis-family canaries generalize: one canary in
`gen_fixture_mutations.py`'s operator set covers every record that shape of
mutation could apply to.

Do **not** add a one-off canary for a single record's quirk that does not
generalize (mirrors `AGENTS.md`'s "Operator Child-Mode Hardening Protocol"):
patch the owning operator/checker family first; only add a fixture when it
sharpens a real, reusable entry/target/operation/result boundary. Prefer
extending an existing family fixture over a near-duplicate invalid variant
that differs only cosmetically from one already covered.

## Andon thresholds

- **2-3 same-stage failures**: if the mutation sweep or a live smoke
  produces 2-3 failures classified to the same stage in a short window,
  treat that as an Andon -- stop and root-cause the stage's contract or
  checker rather than patching each failure as an independent incident.
- **More than 10 canaries in one lane**: if a single stage/lane accumulates
  more than 10 invalid canaries, that is itself a signal of either (a) a
  genuinely under-specified contract that needs a structural fix, not more
  fixtures, or (b) one-off accretion that should be consolidated into fewer,
  more general family fixtures. Either way, stop adding canaries and escalate
  to a design review of that stage's contract.

## The stage-01 gap the sweep found (closed)

The sweep found a real, reproducible checker gap, confirmed against both
golden records: `check_staged_runtime_handshake.py` had a dedicated
field-presence validator for stages 02-06, but **not for stage-01**. Deleting
stage-01's `input_digest` field was not rejected by the checker.

This was recorded honestly in `tools/gen_fixture_mutations.py`'s
`KNOWN_CHECKER_GAPS` dict at discovery time rather than silently passed or
hidden. The gap has since been closed: `check_staged_runtime_handshake.py`
now has a `stage01_intake_errors()` validator (mirroring the
`stageNN_*_errors()` pattern used for stages 02-06) that requires
`input_digest` to be a non-empty string, because it is the one field every
stage-01 payload across all harness paths (retained-artifact-replay,
no-model-fixture, staged-current-skill-stage-local-smoke) actually emits and
is the custody anchor stage-02 depends on. `KNOWN_CHECKER_GAPS` is now empty,
and `tests/staged-runtime-handshake/invalid/stage01-missing-input-digest.json`
is a real, currently-enforced rejection fixture for this class:

```
python tools/check_staged_runtime_handshake.py \
  --records tests/staged-runtime-handshake/invalid/stage01-missing-input-digest.json
```

Deliberately not required at stage-01: `retained_input` and
`source_boundary_preserved` are real fields the retained-artifact-replay
harness path emits, but they are legitimately absent from
staged-current-skill-stage-local-smoke stage-01 payloads, so requiring them
would break otherwise-valid model-mode fixtures; `case_id` is already
enforced at the record level, not per-stage, so it is not duplicated here.

Re-verify `tools/gen_fixture_mutations.py`'s `KNOWN_CHECKER_GAPS` dict
directly before assuming any gap's status if time has passed -- this section
describes a point-in-time verification, not a standing guarantee.
