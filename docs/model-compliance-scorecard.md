# Model-Compliance Scorecard (format + detector coverage map)

> Plan 15, Phase 3 (format/mapping only). This document defines the
> `model-compliance-scorecard-v1` shape and maps eight structural-conformance
> failure shapes to the **existing** deterministic detectors that already catch
> them. It is **structural-conformance only**: it measures whether a captured
> output satisfies the wired structural checkers, not whether it is semantically
> true, persuasive, or accepted. **No model run, network call, or spend is
> involved in this document**, and it carries no safety, refusal, or dual-use
> posture — it is a correctness/observability spec.
>
> Populating a scorecard with fresh outputs from a specific host/model is a
> capture step that requires owner authorization and spend (a model run); that
> step is out of scope here. This spec only fixes the format and the
> failure-shape → detector mapping so a future **offline** runner (over already
> captured outputs) has a stable contract.

## Scorecard schema `model-compliance-scorecard-v1`

```json
{
  "schema": "model-compliance-scorecard-v1",
  "capture_meta": {
    "host": "<label, e.g. reference | other>",
    "captured_from": "<how the outputs were obtained; 'fixtures' for offline>",
    "date": "<YYYY-MM-DD>"
  },
  "rows": [
    {
      "failure_shape": "burden-loss",
      "detector": "check_mrp_generated_burden.py",
      "mode": "structural",
      "verdict": "PASS | FAIL | NOT-RUN"
    }
  ],
  "non_claims": [
    "structural-conformance only; not a semantic-truth, uptake, or cross-host verdict",
    "a PASS row means the wired detector accepted the captured output, nothing more"
  ]
}
```

A scorecard missing `non_claims` is malformed. `verdict` is `NOT-RUN` until an
output has actually been passed through the detector; scores are never inferred.

## Failure-shape → detector coverage map

| Failure shape | What it is | Existing structural detector |
| --- | --- | --- |
| `burden-loss` | a generated MRP burden is dropped / not owner-activated | `tools/check_mrp_generated_burden.py` |
| `mrp-skip` | a public `Land(Bn)` gate lacks its per-burden MRP traversal | `tools/check_mrp_route_invariants.py` |
| `premature-closure` | STOP/closure declared while a downstream burden is live | `tools/check_mid_reread_pressure.py` |
| `symbol-theater` | ACT/ledger surface syntax present but malformed | `tools/check_act_surface_syntax.py` |
| `fabricated-verdict` | a compliance/validation "pass" asserted without the required structure | `tools/check_manual_smoke_render_contract.py` |
| `uptake-claim` | the public `T_lang` surface claims guaranteed uptake | `tools/check_tlang_response_closure.py` |
| `parser-unstable-stage05` | stage-05 continuation/punctuation shape a normalizer had to repair | `tools/check_staged_runtime_handshake.py` |
| `sidecar-reliance` | a claim rests on a proof sidecar whose path integrity is unverified | `tools/check_retained_proof_corpus.py` (+ stage08 `proof_sidecars` path checks in `check_staged_runtime_handshake.py`) |

Every detector above is deterministic and already wired into the local CI lane;
the scorecard reuses them, it does not add new detection logic.

## Offline runner contract (queued, not built here)

A future `tools/build_model_compliance_scorecard.py` would, given a directory of
**already captured** outputs, shell each output through the eight detectors and
emit the schema above. It must:
- run **offline** — no model invocation, no network (a self-test should assert
  no such call on the default path);
- refuse to emit a scorecard lacking `non_claims`;
- reference seed outputs by path, never by copy.

## Boundaries

- No model/host run, no spend, no network in this document.
- No safety, refusal, dual-use, or persuasion framing; structural-conformance
  correctness only (`docs/non-claims.md`).
- A green scorecard certifies structural conformance of the captured outputs,
  not semantic correctness, uptake, or behavior on other inputs/hosts.
