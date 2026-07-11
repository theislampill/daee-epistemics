# Validation registry and promotion boundary

Status: bounded A11 control-plane implementation. This document does not claim
consumer migration, candidate maturity, model behavior, WIP completion, or
release readiness.

## Canonical owners

`tools/validation-registry.json` is the single registry for checker identity,
source hashes, accepted exit categories, artifact applicability, requirement
status, and the six honest profiles. `schema/validation-registry.schema.json`
defines its public shape. `tools/validation_registry.py` owns pure parsing,
hashing, registry integrity, verdict integrity, and anti-bank helpers.
`tools/contract_validation.py` is the shared fail-closed JSON-Schema subset
validator and repository path-custody resolver. All external paths remain
repository-relative: absolute, drive-qualified, UNC, parent-traversal, and
resolved symlink/reparse escapes are rejected before a file is read.

The canonical artifact types are:

- `output-md`
- `input-output-pair`
- `staged-handoff-record`
- `state-capsule-sequence`
- `prompt-context-manifest`
- `proof-sidecar-set`
- `retained-case-manifest`
- `captured-output-custody-manifest`

The profiles are `stage07-release`, `captured-output-structural`,
`stage08-proof-surface`, `promotion`, `scorecard`, and `advisory`. Missing a
required row hard-fails or quarantines according to the profile; it never
becomes a neutral `NOT_RUN`. The scorecard profile is a projection of existing
verdicts and must not execute a second detector battery.

## Replay verdict

`schema/checker-replay-verdict.schema.json` separates launch/completion,
execution status, exit category/code, timeout, crash, usage error, malformed
diagnostic, exact diagnostic ID/stage/class/subcode, stdout/stderr hashes,
artifact/tool/registry hashes, downstream invalidation, forbidden-artifact
readback, and the accepted/rejected expectation status.

Only `completed + accepted` satisfies a required positive check. Only
`completed + structural-rejection` with exact expected stage, class, subcode,
downstream set, diagnostic markers, active fault, and absent forbidden
artifacts satisfies a negative right-reason check. Exit `1` alone is never
mutation success.

`tools/assert_expected_rejection.py` consumes an external expectation and
verdict. It does not invoke a model, network, or process tree. It rejects
unknown checkers, wrong-reason diagnostics, usage/infrastructure outcomes,
malformed JSON, hash drift, downstream mismatch, forbidden artifacts, and
active-fault mismatch.

Schema validation precedes semantic validation. Duplicate checker-result IDs,
artifact roles/paths, forbidden readbacks, registry IDs/aliases/profiles, and
consumer IDs are rejected before any index is built, so no dictionary
projection can silently collapse evidence. The registry bytes named by a
verdict must hash to and decode as the same registry object used to validate
that verdict.

## Model-smoke escapes

`schema/model-smoke-escape.schema.json` and
`tools/check_model_smoke_escape_registry.py` implement the Plan 21 D19-D20
boundary:

- Open `YES` and every `UNKNOWN` block maturity; a deterministically detectable
  escape can be closed only with red/green, neighboring-valid, exact
  right-reason, and registry evidence.
- `NO` is scoped to hashes, protocol, defect signature, and IR/artifact
  boundary; it records the missing neutral observable, anti-answer-bank basis,
  strongest compensating observability, and recheck predicates.
- `REASSESSMENT_DUE` is append-only and remains `NO -> NO`.
- `NO -> UNKNOWN` requires the accountable owner, a distinct independent
  reviewer, materially new evidence, a named current question, and a bounded
  resolution date.
- Renewed scoped `NO` requires updated evidence and compensating control.
- A paid successor after `NO` additionally requires five Whys, Hansei, a
  credible owner-source countermeasure, deterministic green, and independent
  concurrence, with usage and authorization drift explicitly resolved.
- Numeric calls avoided require a receipt for an actually blocked planned
  invocation. Otherwise the value is `unknown`.

No campaign cycle/call ceiling, case route, expected answer, expected topology,
fixed burden/submove count, or fixed byte rule belongs in these controls.

## Current integration boundary

The registry classifies every currently discovered `check_*.py` tool that
advertises `--outputs`. Three pre-existing consumers remain read-only in this
lane and still own private lists:

- `tools/run_staged_current_skill_smoke.py`
- `tools/verify_candidate_output.py`
- `tools/build_model_compliance_scorecard.py`

The live registry check intentionally fails closed while any of those lists
remain. `--registrations-only` verifies checker registration, source hashes,
profiles, and discovery without laundering consumer migration. A later
integration owner must replace those private lists with registry projections
and then change each consumer row from `legacy-private-list` to `registry`.

## Negative-expectation migration

`schema/negative-fixture-expectation.schema.json` now requires
`expected_failure_subcode`. Thirty-seven pre-existing sidecars lacked that
field. Each payload was executed through its owning checker first; because
those legacy checkers expose one stable machine diagnostic code as
`failure_class`, the matching emitted code was copied to the subcode field.
No generic placeholder was introduced. Every currently active sidecar has an
exact stage, class, subcode, downstream invalidation set, and forbidden
artifact set.

## Deterministic commands

```powershell
python tools/validation_registry.py --self-test
python tools/contract_validation.py --self-test
python tools/check_validation_registry.py --self-test
python tools/check_validation_registry.py --registrations-only
python tools/assert_expected_rejection.py --self-test
python tools/check_model_smoke_escape_registry.py --self-test
python tools/check_model_smoke_escape_registry.py
```

The full `python tools/check_validation_registry.py` command is expected to
remain nonzero until the read-only legacy consumer migration is integrated.
