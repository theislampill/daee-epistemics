# Hardening Branch — PR Handoff Ledger (final)

> Lane T deliverable. A local-only snapshot of the `codex/hardening-all-20260703`
> hardening branch for the eventual single PR. **This is a handoff record, not a
> PR:** no push, PR, tag, release, merge, publication, external action, or spend
> has occurred. Finalized 2026-07-04.

## Branch state

- Branch: `codex/hardening-all-20260703` (local-only, not on any remote).
- Base: `main` at `c86b3c6` (MAIN untouched throughout).
- Commits: 39 on top of the base.
- Diffstat: ~132 files changed, ≈ +7200 / −2135.
- Latest strict CI: `run_local_ci: PASS (89 commands)`.
- Working tree: clean.

## North-Star alignment (execution-spine map)

`docs/execution-spine.md` is a docs-only **pointer map** indexing how the repo
already implements the North-Star skill-as-code pipeline (`surface observation →
hidden noetic state → owner/TTP operation → register-axis transition → controlled
delta → MRP/NAR/field_witness mirror → public proof scaffold → sidecar
eligibility`), with the Tier 0 / Tier 1 / Tier 2 split and a skill↔harness
vocabulary table. The Tier-0 execution spine (`## EXECUTION SPINE`) already ships
in `skill/SKILL.md`, so no runtime reference was added and the size-guarded root is
untouched — the map is a review/audit index, not a runtime change.

## Folder exhausted

Every clean, low-risk, safe-local slice in the packet is **done** — including the
final polish: the execution-spine map (`docs: add execution spine map`) and the
stale v0.4.3.0 release-body guard (`plan06: guard stale release-body template`).
All remaining work is terminally classified as owner / spend / external / artifact
/ A-B gated, NOT-SAFE, DEFERRED (no repo surface), or one buildable-but-large
refactor flagged for its own focused pass (Plan 15 normalizer-transparency). There
is no further low-risk local slice to land; the branch is a clean, strict-CI-green
39-commit series ready to become the single PR once the gated items are
owner-adjudicated.

## Owner cleanup (standing directive)

This repository is a correctness / provenance / claim-boundary /
generated-runtime-integrity / retained-corpus-drift / ordinary-security tool. It
is **not** a dual-use, refusal, or safety-policy runtime. The AM-2 refusal gate,
profile-vocabulary hygiene gate, non-manipulation/adversarial-memetic directive,
and matching pins were removed by owner decision (`455a921 cleanup: remove
dual-use safety bloat`) and remain removed. Do not reintroduce that infrastructure.

## Commit series (oldest → newest)

`62acd08` plan18 · `ba10168` plan05 · `f2e6c25` plan05 · `75dea01` plan07 *(reverted)* ·
`c140e82` plan07 *(reverted)* · `052fd0c` plan13 · `6b29127` plan02 · `0bdeb0c` plan04 ·
`fa41cc7` plan01 · `284bcac` plan03 · `3043304` plan08 · `ff4943b` plan12 · `dc6e015` plan06 ·
`455a921` cleanup · `9a39618` plan11 · `9848cc3` plan16 · `06b6d66` plan17 · `951c49d` plan09 ·
`7665365` plan15 · `74c80e0` plan16 · `70488dd` plan17 · `4fe6040` plan15 · `e7aec63` plan03 ·
`15fac09` plan03 · `1b7dce9` plan12 · `5123d7c` plan08 · `009125f` plan12 · `f74451f` docs ·
`56c8daa` plan06 · `b6a95ae` plan12 · `91ef69f` plan08 · `2138f1b` docs · `0f5a93d` plan12 ·
`8c07cda` plan12 · `38a40de` plan03 · *(this)* docs: finalize hardening pr handoff

The two `plan07` safety commits remain in history; their effects were reversed by
`455a921` (no history rewrite, per owner instruction).

## Plan ledger — terminal state for every plan

| Plan | Terminal state |
|---|---|
| 01 live-output verifier | SCAFFOLD DONE; full custody subsystem OWNER-GATED |
| 02 proof-class / taxonomy | DONE |
| 03 field-witness binding | DONE (map + schema + binding checker + canon-spec); envelope generation ARTIFACT-GATED; `binding_status` + certificate `output_fingerprint` OWNER-GATED |
| 04 stage07/08 | SUBSTANTIALLY DONE; existence/hash ARTIFACT-GATED, live re-exec SPEND-GATED |
| 05 retained-corpus requal | SUBSTANTIALLY DONE; Smoke-C promotion OWNER/ARTIFACT-GATED |
| 06 release provenance | DONE (gate ledger + provenance `--self-test` + **stale release-body guard**: the v0.4.3.0-specific template now fails-safe for any other version, so it cannot emit misleading future text); full de-stale (redefining what a release body contains) remains OWNER-GATED (semantics decision); branch-protection EXTERNAL-GATED; tag/publish/custody OWNER-GATED |
| 07 safety boundary | OWNER-DECLINED / REPLACED (dual-use/safety layer removed; neutral parts retained) |
| 08 CI coverage / perf | DONE (coverage checker + `--report` + parallelization proof); parallelization adoption OWNER-GATED (phase-staging + first-failure-abort decision; proof shows no safe drop-in) |
| 09 semantic-replay | DONE (README + schema); polarity guard NOT SAFE TO BUILD (overmatch); deeper phases OWNER/SPIKE-GATED |
| 10 worktree custody | DONE (local commits); PR OWNER-GATED |
| 11 checker consolidation | DONE (land-gate single-sourced); package extraction OWNER-GATED |
| 12 fixture taxonomy/integrity | DONE (taxonomy + census + mutation sweep + expected-diagnostic sidecars on all 3 route checkers + minimal pair); further sidecars/pairs are optional incremental coverage |
| 13 docs claim-boundary | DONE; lexical claim-verb rules OWNER-GATED (overmatch) |
| 14 executor playbook | DEFERRED (no repo surface — planning-lane only) |
| 15 smaller-model compliance | DONE (scorecard format + offline runner); normalizer-transparency refactor BUILDABLE but flagged for a focused pass (large multi-site CI-wired harness); live capture SPEND-GATED |
| 16 architecture-debt slimming | DONE (dead-code + budget tool); terminal-cover strengthening A/B-GATED; contract slimming OWNER-GATED |
| 17 owner/TTP schema | DONE (drift inventory + parity checker); contract resolution / negative-contract authoring OWNER-GATED (safety-sensitive) |
| 18 worktree green-state | DONE |
| 19 owner-decision queue | DONE |

## Remaining gates (by class)

- **OWNER-GATED:** 03 `binding_status` + cert `output_fingerprint`; 06 de-stale + custody; 08 parallelization adoption; 11 package layout; 16 slimming; 17 contract resolution; 01 custody subsystem; 05 Smoke-C; 13 lexical rules.
- **EXTERNAL-GATED:** 06 branch-protection / rulesets; tag / publish / release; the PR itself.
- **ARTIFACT-GATED:** 03 envelope generation; 04 existence/hash; 05 Smoke-C artifact.
- **A/B-GATED:** 16 terminal-cover strengthening (retained-corpus regression risk).
- **SPEND-GATED:** 15 live model/host capture; 04 live re-execution; 09 model-lane spike.
- **NOT SAFE TO BUILD:** 09 standalone polarity guard (overmatch).
- **DEFERRED (no repo surface):** 14.
- **BUILDABLE (own focused pass):** 15 normalizer-transparency (large multi-site harness).

## Confirmations

- Dual-use / safety-policy / refusal infrastructure remains **removed**; none was
  reintroduced — every slice is neutral correctness / provenance / observability.
- No push, PR, draft PR, tag, release, merge, publication, external action, spend,
  issue, branch-protection change, dependency upgrade, or history rewrite occurred.
  MAIN is unchanged at `c86b3c6`; HEAD is on no remote; tree is clean.
