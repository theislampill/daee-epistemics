# Task 7 Whole-Branch R2 Repair Owner Report

Date: 2026-07-12

Scope: the three Important findings in
`task7-independent-whole-branch-review-r2.md` only.

## Disposition

The complete deterministic PASS cohort for rejected prospective tree
`a5a6f885f3e3a08a361c5e73f520a0d23c89ba39` remains historical and
non-promotable under `evidence/deterministic-verdicts/failed-attempts/`.
No canonical review ACCEPT JSON was created.

| Finding | Test-first repair | Focused evidence |
|---|---|---|
| I1 Windows root-relative campaign custody escape | one portable string-level relative-path validator rejects rooted/drive/UNC/device/backslash/traversal/ADS/alias/reserved/control forms before joining; absolute lexical containment is proven before filesystem access; symlink/reparse checks remain | 18 hostile forms across producer/cold read/write, `72` combinations; ordinary contained paths pass; campaign focused suite `43/43`; zero residue |
| I2 suffix-only local CI terminal PASS | suffixes without prefix evidence are `PARTIAL`, `complete=false`; schema, producer, parser, CLI JSON, and Task-7 consumer bind exact full-versus-suffix semantics and plan identities | focused CI-readback suite `51/51`; self-test `1` valid / `63` invalid; exact start-2/final and drift canaries PASS |
| I3 Windows timeout teardown uncertainty | descendant ownership is snapshotted and verified; taskkill nonzero/spawn/timeout, root-wait, PID-query, or survivor uncertainty returns structured `PROCESS_TREE_TEARDOWN` exit `125`; proven teardown retains ordinary timeout `124` | failure-injection cohort plus real child/grandchild teardown PASS; no raw exception or scoped residue |

## Final focused identities

- `tools/reviewed_campaign_orchestrator.py` SHA-256
  `1a4b9a526395fd64d84244def8d24f6691ac452d6718176c2106a23b2e8288b5`
- `tests/reviewed-campaign-orchestration/test_contract.py` SHA-256
  `540d0a77accbbc3b6c47ca374b35bd2cd12110a190b5121e21f18256a5a0fe2d`
- `schema/ci-readback.schema.json` SHA-256
  `ac451b8a40727fcf534a47f427e43c9774f393ab569a0ec8ce313d5222fe80e0`
- `tools/run_local_ci.py` SHA-256
  `a9616098e9c38d07b9dbec97cfc8754dcbc6c8db08e7e3288099c04492c97192`
- `tests/ci-readback/test_contract.py` SHA-256
  `d634c8e2544a0854099011bdf2f6e19b8b3ecc9f76af41dc9545130188928422`

## Boundary

This report does not claim a new exact tree, deterministic closure, whole-branch
acceptance, commit, push, exact-SHA CI, candidate maturity, model execution, or terminal
A01-A16 closure. The complete accepted repair set must be restaged, frozen, rerun, and
reviewed as one new exact tree.

