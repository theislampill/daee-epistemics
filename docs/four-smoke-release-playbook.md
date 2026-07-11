# Four-Smoke Release Playbook

> Historical/current-boundary note: this file retains the four-smoke name and
> evidence lineage. The v0.4.6.0-wip prospective five-case convergence law is
> owned by
> `docs/audits/v0.4.6.0-wip-five-smoke-andon-convergence-north-star-addendum.md`.
> That addendum adds the Torah/Qur'an source-authentication input, cold GPT-5.6
> plus human review, and a full-five rerun after every audited countermeasure.
> It does not retroactively turn any four-smoke artifact into five-smoke proof.

Measurement-only reference for the four-smoke ("Gate88"-style) matrix
protocol and the no-model preflight gate that must pass before any of the
four smokes may run a model. This document describes mechanism and cost
shape; it makes no release, readiness, or provenance claim. Model smokes and
any packaging/release/provenance step remain **owner-gated** -- nothing here
authorizes running one.

## What the four smokes are and what each stresses

Historical four-smoke matrices (see `docs/audits/v0.4.4.0-current-boundary.md`
and the `v0.4.4.0-postgate*-four-smoke-matrix.md` series) run four
case-specific hosted smokes per matrix cycle, each stressing a different
noetic-structure family so that route/owner/closure coverage is not proven by
one case alone. A matrix cycle is only evidence of what it actually exercised
-- read the specific matrix doc's case list before assuming coverage of a
family not represented in it.

Direct validators run against the four smokes' retained outputs and staged
handoff records after the fact, for example:

```
python tools/check_staged_runtime_handshake.py --records <4 staged-handoff-record.json>
python tools/check_field_witness_convergence.py --outputs <4 output.md>
python tools/check_nla_decode_semantic_faithfulness.py --outputs <4 output.md>
python tools/check_mrp_generated_burden.py --outputs <4 output.md> --show-advisories
python tools/check_manual_smoke_render_contract.py --outputs <4 output.md>
python tools/check_graph_completeness.py --outputs <4 output.md>
```

These are diagnostic-matrix evidence only. They are not retained promotion,
package, tag, GitHub Release, release asset, public sample publication, or
provenance evidence by themselves.

## The no-model preflight gate

Before any model subprocess reaches Stage 01 in a four-smoke launch, a
no-model preflight must pass. The gate's two states are named in prior
matrix runbooks:

- `MATRIX_AUTHORIZED_AFTER_PREFLIGHT` -- the readiness audit for this launch
  is recorded, current, and the launch may proceed.
- `MATRIX_NOT_AUTHORIZED` -- remains in force until a fresh readiness record
  supersedes it; no further model matrix, Stage-08 sidecar, or release step
  may proceed while this state holds.

The composed preflight tool is `tools/run_no_model_preflight.py`. It never
runs a model; it composes 16 sequential no-model gates (generated-runtime
freshness, docs freshness, package shape, hot-context budget,
execution-kernel markers, route-shard manifest + selection, cold-law digest,
state capsule, Stage01-08 synthetic valid + invalid, mutation sweep, dry-run
emulator, retained-proof replay, large-output/file-retained, four-smoke
input-path preflight, prompt-pack manifest discipline, and first-failed-
checker reporting) and prints exactly one decision token as its last stdout
line: `MATRIX_AUTHORIZED_AFTER_PREFLIGHT` (every gate passed) or
`MATRIX_NOT_AUTHORIZED` (at least one gate failed). Every gate runs even if
an earlier one fails, so a single invocation reports every red gate at once
rather than stopping at the first. Its own input-path gate calls
`run_staged_current_skill_smoke.py --preflight-input-only`, which returns
before that harness's model-invoking code path is ever reached -- no `--model`
value is passed by the preflight tool under any gate. Run it directly:

```
python tools/run_no_model_preflight.py
python tools/run_no_model_preflight.py --json <report.json>
python tools/run_no_model_preflight.py --self-test
```

Re-verify this tool's gate list against its own `--help` output before
relying on this description -- gates may be added as new no-model checks are
built.

## One-runner-per-smoke, one-shot protocol

Each of the four smokes is launched by exactly one runner subagent/process
against `tools/run_staged_current_skill_smoke.py`, one shot:

- No patch, rerun, or release action may happen *during* a smoke's run. If a
  smoke's launch command is malformed (see the Gate53 Andon example in
  `docs/audits/v0.4.4.0-postgate52-four-smoke-matrix.md`, where a missing
  `--section-expansion-rounds` blocked all four launches before Stage 01),
  fix the command template and relaunch as a new one-shot attempt -- do not
  patch mid-flight.
- Preserve every artifact the run produces (run directory, `output.md`,
  `state-capsules/`, `prompt-pack-manifest.jsonl`, staged-handoff-record,
  Stage-08 sidecars) regardless of pass/fail. A failed run's artifacts are
  the evidence for the next Andon/Hansei cycle.
- Report the **first failed checker**, not a summary of all downstream
  noise. Downstream checks after an early pipeline failure are frequently
  invalidated by that failure (see `docs/stage-contract-workbench.md`'s
  earliest-failure-locality discussion) and reporting them as independent
  findings obscures the actual root cause.

## Expected cost shape

Per the load-path measurements in `docs/load-path-architecture.md`, a single
substantive case's eager-load floor dropped from the old unsatisfiable
"root + five bundles" pattern (~301k est-tok pre-program, exceeding any
practical context window on every single attempt) to root-plus-selected-shards
under the dispatch index. The `--enforce` aspirational default-exec ceiling
(105,000 est-tok worst case: root 34,021 + capsule allowance 4,000 + top-3
co-selectable `default_hot` shards 63,885) is the standing budget a single
model call in one of the four smokes should fit under. Per-smoke *total* cost
across a full multi-stage run (all 7 model-producing stages plus Stage-07
release) is on the order of ~140k est-tok, not the old >=301k-per-attempt
figure -- re-measure with `tools/check_prompt_pack_budget.py` against the
smoke's actual `prompt-pack-manifest.jsonl` rather than assuming this number
holds for a specific run; it is a shape claim, not a per-run guarantee.

## First-failure-as-evidence discipline

Treat the first failed checker in a smoke run as the Andon: stop, record
symptom, failed check, owner surface, and next concrete action (see
`AGENTS.md`'s ANDON/Hansei/5-Whys sections) before considering any retry.
Do not average across the four smokes' outcomes into a single pass/fail
verdict -- each case's Andon is independent evidence, and a matrix cycle with
three passes and one case-specific Andon blocks the next release-proof
boundary for the whole cycle (see the Gate62E example: Khaybar passed while
TST/Secularism/Trinitarian opened case-specific Andons, and no promotion
followed for any of the four).

## Retained replay as the no-model proxy

Once a smoke has actually run and its artifacts are retained, subsequent
regression checking should replay those retained artifacts through the
no-model validators listed above rather than re-running the model. This is
the "retained replay" pattern: it re-proves structural/replay/closure
invariants against real prior model output without spending a new model
call, and it is how `docs/stage-contract-workbench.md`'s mutation sweep and
`tools/daee_dry_run_emulator.py` get golden records to validate against in
the first place.

## Ownership boundary

Model smokes (any step that invokes a model subprocess), packaging, release,
tagging, GitHub Release publication, and provenance recording are all
**owner-gated**. Nothing in this document, the composed preflight, or a
`MATRIX_AUTHORIZED_AFTER_PREFLIGHT` state authorizes those steps by itself --
they require the owner's explicit release-gate decision, per `AGENTS.md`'s
Release Cycle Etiquette section.
