# Hardening Branch — PR Handoff Ledger

> Lane M / M2 deliverable. A local-only snapshot of the `codex/hardening-all-20260703`
> hardening branch for the eventual single PR. **This is a handoff record, not a
> PR:** no push, PR, tag, release, merge, publication, external action, or spend
> has occurred, and the branch is not yet exhausted — buildable lanes remain
> (see "Remaining work"). Refreshed 2026-07-04.

## Branch state

- Branch: `codex/hardening-all-20260703` (local-only, not on any remote).
- Base: `main` at `c86b3c6` (MAIN untouched throughout).
- Commits: 32 on top of the base.
- Diffstat: ~128 files changed, ≈ +6900 / −2135.
- Latest strict CI: `run_local_ci: PASS (89 commands)`.
- Working tree: clean.

## Owner cleanup (standing directive)

This repository is a correctness / provenance / claim-boundary /
generated-runtime-integrity / retained-corpus-drift / ordinary-security tool. It
is **not** a dual-use, refusal, or safety-policy runtime. The AM-2 refusal gate,
profile-vocabulary hygiene gate, non-manipulation/adversarial-memetic directive,
and matching pins were removed by owner decision (`cleanup: remove dual-use safety
bloat`). Do not reintroduce that infrastructure.

## Commit series (oldest → newest)

| SHA | Subject |
|---|---|
| `62acd08` | plan18: close hardening keystone gates |
| `ba10168` | plan05: add retained corpus requalification ledger |
| `f2e6c25` | plan05: add retained corpus advisory-drift gate |
| `75dea01` | plan07: pin profile-catalogue vocabulary hygiene *(reverted by cleanup)* |
| `c140e82` | plan07: add safety refusal gates *(reverted by cleanup)* |
| `052fd0c` | plan13: add docs claim-boundary checks |
| `6b29127` | plan02: tighten claim-boundary documentation |
| `0bdeb0c` | plan04: refresh stage validation harness |
| `fa41cc7` | plan01: add local hardening scaffold |
| `284bcac` | plan03: add field-witness binding map |
| `3043304` | plan08: add ci registry coverage checker |
| `ff4943b` | plan12: add fixture taxonomy and census |
| `dc6e015` | plan06: add release gate ledger |
| `455a921` | cleanup: remove dual-use safety bloat |
| `9a39618` | plan11: single-source the land-gate regex |
| `9848cc3` | plan16: remove dead identical if/else in record_errors |
| `06b6d66` | plan17: add owner/TTP contract drift inventory |
| `951c49d` | plan09: add semantic-replay fixture scope and schema |
| `7665365` | plan15: add model-compliance scorecard format and detector map |
| `74c80e0` | plan16: add load-path budget tool |
| `70488dd` | plan17: add owner-contract parity checker |
| `4fe6040` | plan15: add offline compliance scorecard runner |
| `e7aec63` | plan03: add field-witness binding schema |
| `15fac09` | plan03: add field-witness binding checker |
| `1b7dce9` | plan12: add fixture integrity checks |
| `5123d7c` | plan08: improve ci registry reporting |
| `009125f` | plan12: add fixture sidecar checks |
| `f74451f` | docs: add hardening pr handoff |
| `56c8daa` | plan06: add release provenance fixtures |
| `b6a95ae` | plan12: extend expected-diagnostic sidecars |
| `91ef69f` | plan08: add ci parallelization proof harness |
| *(this)* | docs: refresh hardening pr handoff |

Note: the two `plan07` safety commits remain in history but their effects were
reversed by `455a921` (no history rewrite, per owner instruction).

## Plan ledger (P0/P1/P2/P3)

| Prio | Plan | State |
|---|---|---|
| P0 | 18 / 19 / 10 | DONE (10 = local commits; PR owner-gated) |
| P1 | 05 | SUBSTANTIALLY DONE (Smoke-C promotion owner/artifact-gated) |
| P1 | 07 | OWNER-DECLINED / REPLACED (safety layer removed; neutral parts retained) |
| P1 | 13 / 02 | DONE |
| P1 | 04 | SUBSTANTIALLY DONE (existence/hash + re-exec owner/spend-gated) |
| P1 | 01 | SCAFFOLD DONE (custody subsystem owner-scoped) |
| P1 | 03 | PARTIAL — map + schema + binding checker done; canon-spec/hash-envelope artifact-gated |
| P2 | 08 | PARTIAL — coverage checker + report mode + **parallelization proof** done; parallelization NOT adopted (PARTIAL/phase-staging owner-gated) |
| P2 | 06 | PARTIAL — gate ledger + **provenance `--self-test`** done; de-stale HELD (self-test covers `--provenance/--package` only, not the release-body path); branch-protection EXTERNAL-gated, tag/publish/custody OWNER-gated |
| P2 | 12 | PARTIAL — taxonomy + mutation sweep + **sidecars on 2 checkers** done; `check_mid_reread_pressure` sidecar + minimal pairs queued |
| P2 | 11 | PARTIAL — land-gate single-sourced; package extraction OWNER-GATED |
| P2 | 16 | PARTIAL — dead-code + budget tool done; terminal-cover strengthening OWNER-GATED (semantics-changing, retained-A/B risk); slimming OWNER-GATED |
| P2 | 17 | PARTIAL — drift inventory + parity checker done; contract resolution OWNER-GATED (safety-sensitive) |
| P2 | 14 | DEFERRED (no repo surface — planning-lane only) |
| P3 | 15 | PARTIAL — scorecard format + offline runner done; normalizer-transparency refactor queued; live capture SPEND-GATED |
| P3 | 09 | PARTIAL — README/schema done; polarity guard NOT SAFE TO BUILD standalone (overmatch); deeper phases OWNER/SPIKE-gated |

## Remaining work

**Buildable (not gated), queued:**
- Plan 12: extend the expected-diagnostic sidecar to `check_mid_reread_pressure`
  (the pattern is proven on two checkers); minimal pairs where mechanical.
- Plan 03: canon-spec + hash-envelope binding (artifact-gated — needs the envelope).

**Gated (require owner / spend / external / careful A/B):**
- Plan 06 de-stale: needs a self-test covering the release-body/preflight path
  before it is provably behavior-preserving; branch-protection / tag / publish /
  custody are external/owner.
- Plan 08 parallelization: phase-staging + first-failure-abort change is a CI
  behavior decision (proof shows no safe drop-in).
- Plan 16 terminal-cover strengthening: semantics-changing; needs retained-corpus
  A/B proving no new bound-case failures. Plan 16 slimming: owner adoption.
- Plan 17 contract resolution / negative-contract authoring (safety-sensitive);
  Plan 11 package-layout API; Plan 15 live model/host capture; Plan 09 deeper
  semantic-replay phases; and the single PR itself.

## Readiness

The folder is **not yet exhausted** — the buildable lanes above remain (notably
the `check_mid_reread_pressure` sidecar). This branch is a clean,
strict-CI-green 32-commit series suitable for a single PR once those lanes are
done or terminally gated. No PR has been opened.
