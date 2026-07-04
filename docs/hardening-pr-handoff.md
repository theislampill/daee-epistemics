# Hardening Branch — PR Handoff Ledger

> Lane M deliverable. A local-only snapshot of the `codex/hardening-all-20260703`
> hardening branch for the eventual single PR. **This is a handoff record, not a
> PR:** no push, PR, tag, release, merge, publication, external action, or spend
> has occurred, and the branch is not yet exhausted — buildable lanes remain
> (see "Remaining work"). Prepared 2026-07-04.

## Branch state

- Branch: `codex/hardening-all-20260703` (local-only, not on any remote).
- Base: `main` at `c86b3c6` (MAIN untouched throughout).
- Commits: 27 on top of the base.
- Diffstat: 123 files changed, +6517 / −2083.
- Latest strict CI: `run_local_ci: PASS (87 commands)`.
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

Note: the two `plan07` safety commits remain in history but their effects were
reversed by `455a921` (no history rewrite, per owner instruction).

## Plan ledger (P0/P1/P2/P3)

| Prio | Plan | State |
|---|---|---|
| P0 | 18 worktree green-state | DONE |
| P0 | 19 owner-decision queue | DONE |
| P0 | 10 worktree custody/commits | DONE (local commits; PR owner-gated) |
| P1 | 05 retained-corpus requalification | SUBSTANTIALLY DONE (Smoke-C promotion owner/artifact-gated) |
| P1 | 07 safety boundary | OWNER-DECLINED / REPLACED (safety layer removed; neutral parts retained) |
| P1 | 13 docs claim-boundary | DONE (lexical rules owner-scoped) |
| P1 | 02 proof-class/taxonomy | DONE |
| P1 | 04 stage07/08 | SUBSTANTIALLY DONE (existence/hash + re-exec owner/spend-gated) |
| P1 | 01 live-output verifier | SCAFFOLD DONE (custody subsystem owner-scoped) |
| P1 | 03 field-witness binding | PARTIAL — map + schema + binding checker done; canon-spec/hash-envelope artifact-gated |
| P2 | 08 CI coverage/perf | PARTIAL — coverage checker + report mode done; parallelization needs A/B proof |
| P2 | 06 release provenance | PARTIAL — gate ledger done; de-stale needs provenance fixtures; branch-protection EXTERNAL-gated, tag/publish/custody OWNER-gated |
| P2 | 12 fixture taxonomy/integrity | PARTIAL — taxonomy + mutation sweep + sidecar (1 checker) done; more sidecars + minimal pairs queued |
| P2 | 11 checker consolidation | PARTIAL — land-gate single-sourced; package extraction OWNER-GATED |
| P2 | 16 architecture-debt slimming | PARTIAL — dead-code + budget tool done; terminal-cover strengthening A/B-gated; slimming OWNER-GATED |
| P2 | 17 owner/TTP schema | PARTIAL — drift inventory + parity checker done; contract resolution OWNER-GATED (safety-sensitive) |
| P2 | 14 executor playbook | DEFERRED (no repo surface — planning-lane only) |
| P3 | 15 smaller-model compliance | PARTIAL — scorecard format + offline runner done; normalizer-transparency refactor queued; live capture SPEND-GATED |
| P3 | 09 semantic-replay | PARTIAL — README/schema done; polarity guard NOT SAFE TO BUILD standalone (overmatch); deeper phases OWNER/SPIKE-gated |

## Remaining work

**Buildable (not gated), queued for a continuation pass:**
- Plan 06: minimal self-consistent provenance/package fixtures for
  `check_release_provenance` → then the de-stale refactor (behavior-preservation
  provable only once fixtures exist; the checker is unwired so CI won't validate it).
- Plan 08: an A/B serial-vs-parallel proof harness. Note: the ~9 build /
  generated-file commands write shared artifacts, so safe parallelization is
  limited to the pure checkers and is likely PARTIAL with findings.
- Plan 12: extend the expected-diagnostic sidecar to the other two route checkers;
  minimal pairs where the distinction is mechanical.
- Plan 16: terminal-cover strengthening — requires retained-corpus A/B proving no
  new bound-case failures; owner-gated if it changes semantics.
- Plan 03: canon-spec + hash-envelope binding (artifact-gated — needs the envelope).

**Owner / spend / external gates (out of local scope):**
- Branch protection / ruleset changes; tag / publish / release; large-asset custody.
- Contract resolution / negative-contract authoring (Plan 17); runtime slimming
  adoption (Plan 16); package-layout API (Plan 11).
- Live model/host capture (Plan 15); deeper semantic-replay phases (Plan 09).
- The single PR itself.

## Readiness

The folder is **not yet exhausted** — the buildable lanes above remain. This
branch is a clean, strict-CI-green, reviewable 27-commit series suitable for a
single PR once those lanes are done or terminally gated. No PR has been opened.
