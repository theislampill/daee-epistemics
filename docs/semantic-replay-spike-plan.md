# Semantic-Replay Spike Plan — Meaning-Inversion (NOT SAFE TO BUILD as a guard)

> Plan 09 deliverable, docs-only. Records the spike design for the meaning-inversion
> known-miss and the measured reason a standalone result-polarity guard is NOT SAFE
> TO BUILD. This is semantic-**correctness / faithfulness** only — a meaning-inverted
> output that flips result polarity while surface structure stays plausible. It is NOT
> a refusal, safety, persuasion, or adversarial-memetic detector; the dual-use/safety
> infrastructure removed at `455a921` stays removed. Dated 2026-07-04.

## The known-miss

`docs/fixture-taxonomy.md` section 4 records that a meaning-inverted output passes the
wired structural battery (the battery is structural: NAR fingerprints, owner-set,
delta vocabulary, HOLD/PARTIAL honesty). Closing it is Plan 09.

## Why a naive result-polarity guard is NOT SAFE TO BUILD

A lexical result-polarity discriminator (e.g. a `Land(...)` sign flip, a
`Route: RECURSE` <-> `STOP` inversion, antonym flips, negation counting) **overmatches
lawful output**. Measured, read-only: **47 of 66 valid fixtures** across the tlang /
mrp / mid-reread / concealment / retained corpora carry negation or boundary surfaces
(`does not`, `cannot`, `no active`, `not imply`, `Boundary:`) that a lexical polarity
detector would wrongly flag. Shipping such a guard would fail the valid-fixture loops
it is wired into — it would fabricate failures on conformant output, the exact inverse
of the "invent `validation: PASS`" anti-pattern. **Therefore the standalone polarity
guard is NOT SAFE TO BUILD.**

## The gate any future candidate must pass (spike design)

Before ANY discriminator is proposed as land-ready:

1. Enumerate candidate discriminators with their specific overmatch hazards (which
   named valid fixtures each would wrongly flag).
2. Run each candidate over the union valid corpus (the 66-fixture false-positive ground
   truth) and measure its false-positive count.
3. **A candidate may be proposed only if its measured false_positives == 0** against the
   union valid corpus. Given the 47/66 negation density, no naive lexical candidate is
   expected to reach FP == 0.

An advisory FP-measurement harness (a non-`check_*` `spike_` tool, never wired as a
gate) could produce these numbers, but building candidate discriminators to measure is
itself building the thing that overmatches; the honest current outcome is to keep
meaning-inversion a documented known-miss.

## Terminal disposition (owner-adjudicated 2026-07-04)

- Standalone lexical result-polarity guard: **NOT SAFE TO BUILD** (overmatch, measured).
- A model-lane judge that could discriminate meaning-inversion without lexical overmatch
  is **SPEND-GATED** and requires separate owner authorization; decide only after a
  measured FP report shows lexical candidates cannot reach FP == 0.
- Until then, meaning-inversion stays a **documented known-miss** in
  `docs/fixture-taxonomy.md` section 4; `docs/proof-class-taxonomy.md` continues to say
  `semantic-replay` is not implemented.

## Boundary

Any future Plan 09 work stays framed as meaning-inversion **correctness**. No refusal,
safety, persuasion, or adversarial-memetic framing is introduced or reintroduced.
