# Hardening Branch — PR Handoff Ledger (final)

> Lane T deliverable. A local-only snapshot of the `codex/hardening-all-20260703`
> hardening branch for the eventual single PR. **This is a handoff record, not a
> PR:** no push, PR, tag, release, merge, publication, external action, or spend
> has occurred. Updated 2026-07-04.

## Branch state

- Branch: `codex/hardening-all-20260703` (local-only, not on any remote).
- Base: `main` at `c86b3c6` (MAIN untouched throughout).
- Commits: 53 on top of the base (a maximal safe-local completion pass landed seven slices — plans 16, 08, 17, 06, 09, 15, 03 — then a docs refresh + this stale-count reconcile, each strict-CI-green; Plan 11 was terminally gated after preflight, not attempted).
- Diffstat: ~139 files changed, ≈ +8850 / −2135 (content, `--ignore-cr-at-eol`; the raw diff is larger because the `plan15` commit incidentally normalized a pre-existing mixed-CRLF file to the repo-mandated LF).
- Latest strict CI: `run_local_ci: PASS (91 commands)`.
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

## Safe-local completion pass (2026-07-04)

A maximal safe-local completion pass worked every remaining lane as far as safely
possible. Seven slices landed, each strict-CI-green (one coherent commit per slice):

- **`plan16`** — recorded two owner decisions: terminal-cover strengthening
  DECLINED-AND-RECORDED (measured empty 24-case A/B delta; already enforced by
  `check_graph_completeness.py:1142` + `check_collapse_certificate_schema.py:212`),
  and root/runtime slimming HELD OUT (a full-load-path sweep found no mechanical
  behavior-preserving byte reduction; any cut is a semantic generator-first rewrite).
- **`plan08`** — recorded the parallelization decision (reject/defer; adoption
  owner-gated) alongside the `benchmark_summary()` Amdahl-ceiling helper.
- **`plan17`** — recorded the D3 operation-token QUARANTINE (cross-namespace) +
  advisory-only disposition (pure schema parity, no refusal layer).
- **`plan06`** — added the release-body token contract (invariant vs version-specific),
  awaiting owner sign-off for any generify/retire code.
- **`plan09`** — recorded the meaning-inversion spike plan; the standalone polarity
  guard is NOT SAFE TO BUILD (measured 47/66 valid-fixture overmatch).
- **`plan15`** — record-only `route_state_repairs` normalizer surfacing in the smoke
  harness (behavior-preserving; verdict/schema byte-identity proven by the harness
  `--self-test`).
- **`plan03`** — the field-witness envelope generator (`build_field_witness_envelope.py`,
  writes nothing by default, mutates zero retained bytes, wired `--self-test`).

**Plan 11 (checker package extraction) was terminally gated, not attempted.** A
read-only preflight found the blast radius far exceeds a clean atomic move: 42 files
need a `parents[1]→parents[2]` fix, 44 need import bootstrapping, 36 subprocess sites
in the smoke harness invoke checkers by literal path, plus hard-smoke fixture command
strings, and — decisively — `.github/workflows/release-skill.yml` + two `ci/level3-*.yml`
invoke moved checkers (a miss = green-local / red-release). It is OWNER-GATED as a
dedicated post-merge PR; the migration recipe lives in `docs/hardening-followup-plan.md`.

With this pass, every owner-approved safe-local slice is implemented or terminally
classified. The branch is a clean, strict-CI-green 53-commit series.

## Owner cleanup (standing directive)

This repository is a correctness / provenance / claim-boundary /
generated-runtime-integrity / retained-corpus-drift / ordinary-security tool. It
is **not** a dual-use, refusal, or safety-policy runtime. The AM-2 refusal gate,
profile-vocabulary hygiene gate, non-manipulation/adversarial-memetic directive,
and matching pins were removed by owner decision (`455a921 cleanup: remove
dual-use safety bloat`) and remain removed. Do not reintroduce that infrastructure.

## Commit series

The full, authoritative series is `git log c86b3c6..HEAD` — 53 commits (oldest →
newest) on top of the base. The 2026-07-04 completion-pass commits are `2d5216c`
plan16, `1d35a46` plan08, `3db753a` plan17, `2b323e4` plan06, `fadb4a6` plan09,
`061ddbe` plan15, `76f4cd1` plan03, followed by the docs refresh + reconcile. The two
reverted `plan07` safety commits remain in history; their effects were reversed by
`455a921` (no history rewrite, per owner instruction).

## Plan ledger — terminal state for every plan

| Plan | Terminal state |
|---|---|
| 01 live-output verifier | SCAFFOLD DONE; full custody subsystem OWNER-GATED |
| 02 proof-class / taxonomy | DONE |
| 03 field-witness binding | DONE (map + schema + binding checker + canon-spec + **envelope generator** `build_field_witness_envelope.py`: writes nothing by default, mutates zero retained bytes, `--self-test` wired); Phase-4 wired recompute checker ARTIFACT-GATED (needs materialized envelopes); retained `binding_status` assignment + Phase-5 certificate `output_fingerprint` rev OWNER-GATED |
| 04 stage07/08 | SUBSTANTIALLY DONE; existence/hash ARTIFACT-GATED, live re-exec SPEND-GATED |
| 05 retained-corpus requal | SUBSTANTIALLY DONE; Smoke-C promotion OWNER/ARTIFACT-GATED |
| 06 release provenance | DONE (gate ledger + provenance `--self-test` + **stale release-body guard**: the v0.4.3.0-specific template now fails-safe for any other version, so it cannot emit misleading future text); full de-stale (redefining what a release body contains) remains OWNER-GATED (semantics; the token contract is now documented in `docs/release-body-contract.md`, OD-06a/b/c); branch-protection EXTERNAL-GATED; tag/publish/custody OWNER-GATED |
| 07 safety boundary | OWNER-DECLINED / REPLACED (dual-use/safety layer removed; neutral parts retained) |
| 08 CI coverage / perf | DONE (coverage checker + `--report` + parallelization proof + pure `benchmark_summary()` helper `1cf82c6`); `docs/audits/ci-parallelizability.md` counts corrected then kept live (now 91/85; `22e5673`) with the adoption decision (reject/defer; OD-08a/b/c) recorded there; parallelization adoption OWNER-GATED (phase-staging + first-failure-abort decision; proof shows no safe drop-in) |
| 09 semantic-replay | DONE (README + schema + **spike plan** `docs/semantic-replay-spike-plan.md`); standalone polarity guard NOT SAFE TO BUILD (measured 47/66 valid-fixture overmatch); model-lane judge SPEND-GATED; meaning-inversion stays a documented known-miss |
| 10 worktree custody | DONE (local commits); PR OWNER-GATED |
| 11 checker consolidation | DONE (land-gate single-sourced); package extraction OWNER-GATED / dedicated post-merge PR (preflight found a release/CI-facing blast radius: 42 `parents[1]` fixes, 44 import bootstraps, 36 harness subprocess sites, hard-smoke fixtures, `release-skill.yml` + `ci/level3-*.yml`; a miss = green-local/red-release; recipe in the follow-up plan) |
| 12 fixture taxonomy/integrity | DONE (taxonomy + census + mutation sweep + expected-diagnostic sidecars on all 3 route checkers + minimal pair); further sidecars/pairs are optional incremental coverage |
| 13 docs claim-boundary | DONE; lexical claim-verb rules OWNER-GATED (overmatch) |
| 14 executor playbook | DEFERRED (no repo surface — planning-lane only) |
| 15 smaller-model compliance | DONE (scorecard format + offline runner + **record-only `route_state_repairs` normalizer surfacing** in the smoke harness, verdict/schema byte-identity self-tested); verdict-downgrade (OD-15A), schema-bump (OD-15B), and the multi-site `record_normalization()` centralization (OD-15C) OWNER-GATED/deferred; live capture SPEND-GATED |
| 16 architecture-debt slimming | DONE (dead-code + budget tool + terminal-cover A/B harness `0788b21`); terminal-cover strengthening **DECLINED-AND-RECORDED** (empty A/B delta, already enforced elsewhere); root/runtime slimming HELD OUT (no mechanical behavior-preserving slim exists; semantic rewrite OWNER-GATED) — both recorded in `docs/terminal-cover-ab-snapshot.md` |
| 17 owner/TTP schema | DONE (drift inventory + parity checker + **D3 quarantine record** `docs/audits/owner-contract-operation-token-drift-inventory.md`); the single D3 operation-token row is QUARANTINE (cross-namespace) + advisory-only (OD-17a/b); pure operation-token schema parity, no refusal layer |
| 18 worktree green-state | DONE |
| 19 owner-decision queue | DONE |

## Follow-up plan

Every remaining gated item now has a detailed, executable follow-up plan —
smallest safe first slice, validators, rollback, stop conditions, and
before/after-merge sequencing per lane — in
[`docs/hardening-followup-plan.md`](hardening-followup-plan.md).

The before-merge slices and the subsequent completion pass (see above) are now all
landed strict-CI-green. Every owner-approved safe-local slice is implemented or
terminally classified; what remains is genuinely owner / external / spend / artifact
/ A-B gated, NOT-SAFE, or the Plan 11 dedicated-PR refactor — with zero
safety-reintroduction risk.

## Remaining gates (by class)

- **OWNER-GATED:** 03 `binding_status` + cert `output_fingerprint`; 06 de-stale + custody; 08 parallelization adoption; 11 package layout; 16 slimming; 17 contract resolution; 01 custody subsystem; 05 Smoke-C; 13 lexical rules.
- **EXTERNAL-GATED:** 06 branch-protection / rulesets; tag / publish / release; the PR itself.
- **ARTIFACT-GATED:** 03 Phase-4 recompute checker (needs materialized envelopes; the generator now exists); 04 existence/hash; 05 Smoke-C artifact.
- **A/B-GATED:** 16 terminal-cover strengthening (retained-corpus regression risk).
- **SPEND-GATED:** 15 live model/host capture; 04 live re-execution; 09 model-lane spike.
- **NOT SAFE TO BUILD:** 09 standalone polarity guard (overmatch).
- **DEFERRED (no repo surface):** 14.
- **BUILDABLE (own focused pass):** 15 multi-site `record_normalization()` centralization (the record-only surfacing slice landed); 11 checker package move (release/CI-facing atomic PR).

## Confirmations

- Dual-use / safety-policy / refusal infrastructure remains **removed**; none was
  reintroduced — every slice is neutral correctness / provenance / observability.
- No push, PR, draft PR, tag, release, merge, publication, external action, spend,
  model smoke, issue, branch-protection change, dependency upgrade, or history
  rewrite occurred. MAIN is unchanged at `c86b3c6`; HEAD is on no remote; tree is clean.
- The `plan15` commit incidentally normalized a pre-existing mixed-CRLF file
  (`tools/run_staged_current_skill_smoke.py`) to the repo-mandated LF
  (`.gitattributes: * text=auto`); its real content change is +88 lines
  (`git diff --ignore-cr-at-eol`). No history was rewritten to reshape that commit.
