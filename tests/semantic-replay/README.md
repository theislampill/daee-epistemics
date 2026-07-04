# Semantic-Replay Evaluation Fixtures

> Plan 09, Phase 0 deliverable. This directory pins the **scope and fixture
> schema** for bounded structural-equivalence evaluation. It is a correctness /
> faithfulness lane: the fixtures and any future harness check whether two
> governed outputs are **structurally** equivalent (or deliberately divergent)
> over enumerated invariants. Nothing here is a semantic grader, a safety or
> refusal mechanism, or a persuasion/uptake judgement.

## What "semantic replay" means here (and does not)

"Semantic replay" is a **bounded-slice, structural** notion in this repo, not a
universal semantic equivalence proof. A fixture pair asserts that two outputs
agree (or disagree) on specific, enumerable structural invariants — NAR
fingerprints, owner-set stability, delta-token vocabulary, HOLD/PARTIAL honesty,
and result polarity. Paraphrase or meaning shifts outside those enumerated
invariants are **expected misses**, documented as such, not failures of the tool.

This lane makes no claim of semantic truth, interlocutor uptake, cross-host
reproduction, or arbitrary-input correctness (see `docs/non-claims.md`), and it
carries no safety, refusal, or adversarial-content posture.

## Evaluation questions

1. Do two outputs derived from the same input carry the same NAR row fingerprints?
2. Is the set of activated owners stable across a structural-equivalent pair?
3. Do delta-result tokens stay within the declared vocabulary for both outputs?
4. Are HOLD / PARTIAL / RECURSE states reported honestly in both (no silent
   downgrade of a held route to a closed one)?
5. When an output is a deliberate meaning-inversion of its baseline, does the
   result **polarity** flip while the surface structure stays plausible?
6. Which invariants does the wired battery already enforce, and which are
   **known misses** (documented, not silently accepted)?
7. What is the smallest fixture pair that isolates each invariant (minimal pair)?

## Fixture schema

Each fixture record follows `semantic-replay-fixture-v1`:

```json
{
  "schema": "semantic-replay-fixture-v1",
  "kind": "equivalence-pair",
  "baseline": "cases/<id>/baseline.md",
  "counterpart": "cases/<id>/counterpart.md",
  "invariant": "nar-fingerprint",
  "expectation": "equivalent",
  "non_claims": [
    "structural equivalence over enumerated invariants only",
    "not a semantic-truth, uptake, or cross-host verdict"
  ]
}
```

- `kind`: `equivalence-pair` (should match), `polarity-pair` (result polarity
  should flip), or `known-miss` (documented accepted-bad: the pair differs in
  meaning but the wired battery cannot yet tell them apart).
- `expectation`: `equivalent`, `inverted`, or `divergent`.
- `non_claims`: mandatory; a fixture with no `non_claims` is malformed.

## Boundaries

- No universal semantic grader; every verdict is over an enumerated invariant.
- No safety, refusal, dual-use, or persuasion framing — this is a faithfulness /
  correctness lane only.
- Known misses are recorded, dated, and closed only when a wired invariant
  actually catches them; they are never silenced or deleted.
