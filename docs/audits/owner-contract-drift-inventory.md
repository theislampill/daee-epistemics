# Owner / TTP Contract Drift Inventory

> Plan 17, Phase 1 deliverable. A **read-only, computed** inventory of drift
> across the owner/TTP contract representations. It **observes** divergence; it
> does **not** resolve it. Choosing a canonical side, admitting or removing any
> operation, or authoring owner/TTP contract content are owner decisions
> (Plan 17 Phases 3-5, routed via Plan 19) and are out of scope here. This
> document changes no runtime, checker, or owner semantics.
>
> All sets below were computed on 2026-07-04 in the `codex/hardening-all-20260703`
> worktree by loading each representation and taking set differences; they are
> measured, not asserted.

## Representations compared

| # | Representation | Source | Shape |
| --- | --- | --- | --- |
| R1 | Machine vocabulary | `atomics/skill/references/diagnostics/delta-result-vocabulary.json` (`contract_version` 0.4.3.0) | `owner_operations` (29 keys), `owner_families` (30 keys), `owner_operation_delta_results`, `owner_aliases` |
| R2 | Source-owned ACT operation table | `tools/check_mrp_generated_burden.py` `SOURCE_OWNED_ACT_OPERATIONS` (line 129) | dict: 11 families → 22 operation tokens (each with a hand-written regex body) |
| R3 | Formal owner contracts | `tools/check_ttp_operator_contracts.py` `FORMAL_OWNER_CONTRACT_REQUIRED` (line 26) | 3 contract IDs |
| R4 | Prose contracts | `atomics/skill/references/tactics|techniques|procedures/*.md` | free-form (not machine-diffed here) |

## Measured drift

**D1 — R2 families are a clean subset of R1 (no orphans).** Every family in
`SOURCE_OWNED_ACT_OPERATIONS` exists in `delta-result-vocabulary.json`
`owner_families` (set difference R2−R1 = ∅). This is the healthy direction: the
checker table does not admit a family the vocabulary has never heard of.

**D2 — R2 covers 11 of 30 vocabulary families (coverage extent, not a bug by
itself).** Families present in R1 but with no `SOURCE_OWNED_ACT_OPERATIONS`
entry (19):
`DO_SECOND_LOOP, FPD, HUSN_AL_NAZAR, INDUCTIVE_FITRI, LOOPBREAK, M1-P, P1, P2,
P3, P4, P5, P6, PATTERN_PROFILE, PROOF_METHOD, SYMMETRIC_TAQLID, V10, V12, V3, V6`.
These families are not enforced through the source-owned ACT operation table;
whether any of them *should* be is an owner call (do not add keys to make a
parity check pass — that silently admits new operations).

**D3 — R3 keys are in a different namespace than R1 families.** The 3
`FORMAL_OWNER_CONTRACT_REQUIRED` keys — `M8-reductio`, `M9-predication-mode`,
`TTP-MRP-mid-reread-pressure` — are contract identifiers, not `owner_families`
names, so they do not set-compare against R1. This is the "formal-contract
operation tokens unvalidated" gap: a formal contract can name an operation the
vocabulary never declared, and nothing cross-checks the contract's
`operation_token` against R1's `owner_operations` for its family.

**D4 — R3 is sparse.** 30 vocabulary families exist; only 3 formal contracts are
required today. Expanding formal contracts to more families is Plan 17 Phase 5,
which is owner-gated (executors must not author owner/TTP contract content).

**D5 — LOOPBREAK is a family with no operation.** `owner_families` has 30
entries; `owner_operations` has 29. The extra family is `LOOPBREAK` (a family
that carries no owner_operation token). This is an internal R1 shape fact, noted
for completeness.

## Expressibility verdict (for the Phase 2 parity decision)

- The **key sets** — R1 `owner_families`/`owner_operations` and R2
  `SOURCE_OWNED_ACT_OPERATIONS` family/token keys — are schema-expressible and
  set-comparable; a parity checker could enforce R2-keys ⊆ R1 and flag D2/D3 as
  a dated allowlist without any regex or semantic judgement (Track B: parity-only).
- The **regex bodies** in R2 and the free-form R3/R4 prose are **not**
  schema-expressible and cannot be single-sourced by codegen without an owner
  decision on canonical wording (Track A would require that decision).
- Recommendation for the owner: Track B (import the key tables into a parity
  checker, quarantine D2/D3 in a dated allowlist) is achievable as neutral
  correctness work; Track A (single-sourcing the regex bodies / contract prose)
  is owner-gated. The parity checker itself is Plan 17 Phase 2.

## What this inventory does not do

- It does not decide which representation is canonical for any drift row.
- It does not add, remove, or reword any owner operation, family, contract, or
  regex — doing so would change diagnostic semantics and is owner-gated.
- It does not diff R4 prose mechanically; prose reconciliation is a manual owner
  task.
