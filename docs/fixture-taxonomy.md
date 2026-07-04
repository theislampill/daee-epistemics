# Fixture Taxonomy and Census

> Plan 12, Phase 0 deliverable. Defines the fixture kinds the test estate uses,
> a verified census of the fixture families, and a per-fixture kind assignment
> for the three families this plan hardens. Structural/census evidence only; no
> claim that any fixture proves semantic correctness or interlocutor uptake.
> Counts verified against a fresh `ls` in the `codex/hardening-all-20260703`
> worktree on 2026-07-04.

## 1. Fixture kinds

| Kind | Definition | Rule |
| --- | --- | --- |
| `valid-control` | Passes its owning checker; documents the lawful shape. | Lives in `valid/`. |
| `invalid-single-signature` | Fails for exactly one pinned reason. | Preferred negative; one signature per fixture. |
| `composite-historical` | A preserved real-world failure carrying several signatures at once; quarantined. | MUST never be the *only* invalid fixture guarding a signature — a minimal-pair single-signature twin must also exist. |
| `mutation-canary` | A scripted mutation of a committed fixture (e.g. the bold-Land-gate class) that must stay rejected. | Pins a specific hardening; if it starts passing, the hardening regressed. |
| `overreach-canary` | A *valid* fixture pinned against checker over-tightening (the TST / Khaybar class). | Lives in `valid/`; if it starts failing, a checker overreached. |
| `known-miss` | A documented accepted-bad: content that *should* be rejected but passes the wired battery today. | Recorded here and in a known-miss registry, never silently "fixed" or deleted; closed only when the owning plan lands. |

## 2. Census

All family counts are on-disk fixture files (`.md`, plus `.json` for the JSON
families). "checked" counts reported by a checker may differ from file counts
where a family carries companion sidecars (e.g. a `.field_witness.json` next to
a `.md`).

| Family root | valid / invalid (files) | checker "checked" counts | Notes |
| --- | --- | --- | --- |
| `tests/mrp-route-invariants` | 6 / 7 | Valid 6 / Invalid 7 | invalid includes the ~102 KB composite; WT adds the bold-gate mutant |
| `tests/mid-reread-pressure` | 14 / 26 | Valid 13 / Invalid 26 | valid file count includes one `.field_witness.json` companion (13 `.md` + 1 json) |
| `tests/tlang-response-closure` | 1 / 2 | Valid 1 / Invalid 2 | thinnest family; WT adds the uptake-assertion invalid |
| `tests/public-burden-grouping` | 2 / 5 | — | |
| `tests/manual-smoke-render` | 18 / 39 | — | WT adds compliance-side-success, fabricated-validation-pass |
| `tests/concealment-mode` | 21 / 25 | — | WT adds 2 invalids |
| `tests/staged-runtime-handshake` | 26 / 111 | — | JSON fixtures; 111 = plan-recorded 110 + the Plan 04 `stage08-proof-sidecars-absolute-path.json` path-integrity fixture |
| `tests/routing-fixtures` | 92 flat | — | no valid/invalid split; zero rejection negatives; consumer `check_routing_parity.py` is a static parity contract |
| `tests/negative-example-mimicry` | manifest only | 14 rows | rows synthesized from the manifest; no on-disk fixture files |

## 3. Kind assignment — the three hardened families

### `tests/mrp-route-invariants/invalid`

| Fixture | Kind |
| --- | --- |
| `bold-land-gate-single-terminal-mrp.md` | mutation-canary |
| `generic-graph-edge-missing-mrp.md` | invalid-single-signature |
| `generic-held-beyond-prompt-complete.md` | invalid-single-signature |
| `generic-linear-curl-misuse.md` | invalid-single-signature |
| `generic-mixed-field-local-claim.md` | invalid-single-signature |
| `generic-stop-before-continuation.md` | invalid-single-signature |
| `secularism-round-robin-act-terminal-mrp-false-pass.md` | composite-historical |

### `tests/tlang-response-closure/invalid`

| Fixture | Kind |
| --- | --- |
| `generated-pressure-absent-from-response.md` | invalid-single-signature |
| `uptake-assertion.md` | invalid-single-signature |

### `tests/mid-reread-pressure/invalid`

`mutation-canary`: `bold-land-gate-single-terminal-mrp.md`,
`ascii-multi-land-single-terminal-mrp.md` (bold/ascii variants of the multi-land
signature; both must stay rejected).

`invalid-single-signature` (all remaining 24): `always-expands-speculative-edge.md`,
`bare-rh-delta-heading.md`, `boltzmann-proof-stack-after-self-reference-loopbreak.md`,
`false-closure-with-downstream-burden.md`, `finding-without-pressure-owner.md`,
`graph-edge-missing-terminal.md`, `guaranteed-uptake-claim.md`,
`held-activation-edge-none-preemption.md`, `loopbreak-without-diagnosed-curl.md`,
`mrp-refutation-content-in-block.md`, `multi-land-single-terminal-mrp.md`,
`nonzero-curl-stop-without-loopbreak.md`, `partial-owner-closure-leak.md`,
`proof-stack-after-loopbreak.md`, `public-field-diagnostics-loose-prose.md`,
`public-invalid-route-value.md`, `public-missing-pressure-activations.md`,
`public-preemption-loose-prose.md`, `recurse-without-graph-delta.md`,
`stop-held-beyond-prompt-complete.md`, `stop-with-unreleased-escape-route.md`,
`unqualified-framework-recoil.md`, `visible-chain-missing-mrp-resultant.md`,
`visible-chain-missing-route-result-type.md`.

## 4. Known-miss registry (documented accepted-bad)

These are not on-disk invalid fixtures; they are content classes that pass the
wired battery today and are closed only when their owning plan lands:

- **Meaning-inversion** — a meaning-inverted output passes the wired structural
  battery (closed by Plan 09 semantic-replay).
- **Stage-07 literal pass-strings** — literal pass tokens are not re-executed
  (closed by Plan 04 Stage07/08 re-execution).
- **Generic Stage-08 `proof_sidecars` non-verification** — claimed sidecars are
  path-integrity-checked (Plan 04) but existence/hash binding is owner/spend-gated.

## 5. Expected-diagnostic sidecar (`expected-diagnostic-v1`)

An invalid fixture may carry an opt-in `<fixture-stem>.expected.json` sidecar that
pins the fixture to fail for the RIGHT reason (anti-masking). The owning checker's
invalid loop, when a sidecar is present, additionally requires every
`expected_error_substrings` entry to be a substring of at least one emitted error.

```json
{
  "schema": "expected-diagnostic-v1",
  "fixture": "<name>.md",
  "kind": "<taxonomy kind>",
  "expected_error_substrings": ["a distinctive, stable diagnostic phrase"],
  "provenance": "<origin note>"
}
```

Rules: each substring is `>= 12` chars and must not equal the fixture name/path
(rejects trivial pins). Sidecars are opt-in — a fixture without one is unaffected,
so existing checker behavior is preserved. Consumed today by
`check_tlang_response_closure`; extending the other route checkers is a
follow-up slice.

## 6. What this does not establish

- It does not prove any invalid fixture is the *only* way its signature can
  fail, nor that the single-signature label is exhaustive.
- Minimal-pair coverage and the wider sidecar rollout are Plan 12 Phases 1-2;
  the mutation sweep (Phase 3) is already wired (`gen_fixture_mutations.py`).
