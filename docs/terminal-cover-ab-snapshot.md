# Terminal-Cover A/B Baseline Snapshot

> Plan 16 deliverable, **measurement only**. A dated snapshot of the current
> terminal-cover state of the 24 retained proof outputs, produced by
> `tools/measure_terminal_cover_ab.py` (read-only; wired `--self-test` in CI). It
> does NOT strengthen any checker, gate CI, mutate any retained output, or change
> terminal-cover semantics — it is the evidence instrument for the A/B-gated Plan
> 16 terminal-cover strengthening decision, which stays OWNER-GATED. Measured
> 2026-07-04.

## What is measured

"Terminal cover" is the `no_new_resultant_terminal_proof` graph condition in
`tools/check_graph_completeness.py`: a claimed terminal STOP must be backed by an
actual terminal-stop proof count, not an empty terminal claim. Per case,
terminal-cover PASSES iff that condition is absent from the case's `--json`
`failures` list (the same per-condition surface `tools/check_retained_row_claims.py`
consumes). The underlying checker's overall exit code is ignored — it reflects
unrelated conditions over the retained outputs — so the measurement reads only the
terminal-cover boolean.

Each case is classified:

- **BOUND** — its terminal-cover claim is enforced by a manifest `graph-keys`
  coverage target (keys `ALL` or `no_new_resultant_terminal_proof`). A candidate
  strengthening that newly fails a BOUND case is a hard regression: it would break
  `check_retained_row_claims`, and is never allowlistable.
- **ADVISORY** — not bound by such a target; a newly-failing ADVISORY case is
  allowlist-eligible, not a hard regression.

## Baseline (current checker, no candidate)

| case | class | current terminal-cover |
| --- | --- | --- |
| a9-science-source | BOUND | PASS |
| academic-prestige-authority | BOUND | PASS |
| authority-return-recoil | BOUND | PASS |
| c7-loopbreak | BOUND | PASS |
| cd9a-mixed-concealment | ADVISORY | PASS |
| dad8-science-only-c8 | BOUND | PASS |
| dad8-testimony-c8 | BOUND | PASS |
| exact-secularism | BOUND | PASS |
| exact-trinitarian-j173 | BOUND | PASS |
| exact-tst-lillard | BOUND | PASS |
| fitrah-restoration-recoil | BOUND | PASS |
| gate88-khaybar | BOUND | PASS |
| gate88-secularism | BOUND | PASS |
| gate88-trinitarian-j173 | BOUND | PASS |
| gate88-tst-lillard | BOUND | PASS |
| mixed-family-authority | BOUND | PASS |
| restoration-track | BOUND | PASS |
| source-order-tlang | BOUND | PASS |
| staged-a9-science-source-proofbundle | BOUND | PASS |
| staged-secularism-proofbundle-pilot-v17 | BOUND | PASS |
| therapy-moral-tribunal | BOUND | PASS |
| trinitarian-j173-repair-v6 | BOUND | PASS |
| uptake-guarantee-recoil | BOUND | PASS |
| worship-frame-recoil | BOUND | PASS |

**Baseline: 24/24 cases pass terminal-cover; 23 BOUND, 1 ADVISORY.** No candidate
was supplied, so the delta is empty by construction — this row set is the frozen
reference every future candidate is diffed against.

## Running the A/B when a candidate exists

```
python tools/measure_terminal_cover_ab.py                    # baseline snapshot above
python tools/measure_terminal_cover_ab.py --candidate tools/<candidate>.py
```

With a `--candidate`, the tool prints the newly-failing cases (current PASS,
candidate FAIL) split into BOUND regressions and ADVISORY deltas. The A/B decision
rule: **a terminal-cover strengthening may be adopted only if its measured delta
introduces zero BOUND regressions** (an ADVISORY delta is an owner-adjudicated,
dated-allowlist decision, not an automatic block). The tool never enforces this —
it reports; adoption stays OWNER-GATED on the phase decision.

## What this does not claim

- It does not strengthen terminal cover, nor assert any candidate exists.
- A `PASS` here is terminal-cover-condition state only — not release/provenance
  proof, not model-behavior proof, not proof for other graph conditions.
- The measurement runs the current checker over already-committed retained outputs;
  it mutates nothing and depends on no external service.
