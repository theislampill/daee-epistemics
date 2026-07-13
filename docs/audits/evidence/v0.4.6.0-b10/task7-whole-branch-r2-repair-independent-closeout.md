# Task 7 Whole-Branch R2 Repair Independent Closeout

Date: 2026-07-12

Reviewer: `/root/task7_whole_branch_review`, read-only and independent of
implementation.

## Final bounded dispositions

| R2 finding | Final disposition | Findings |
|---|---|---|
| I1 portable campaign path custody | ACCEPT | 0 Critical / 0 Important / 0 Minor |
| I2 full-versus-suffix local-CI producer/schema/parser contract | ACCEPT | 0 Critical / 0 Important / 0 Minor |
| I3 Windows process-tree teardown failure custody | ACCEPT | 0 Critical / 0 Important / 0 Minor |

I1 final review verified 18 hostile portable path forms across producer/cold
read/write boundaries (`72` combinations), direct C0 coverage, absolute lexical
containment before filesystem access, retained symlink/reparse checks, and ordinary
contained-path behavior. Final focused suite: `43/43` PASS with zero residue.

I2 final review verified one exact full schema branch and exactly `171` suffix branches
for starts `2..172`, exact counts and plan identities, truthful `PARTIAL/false` suffix
reports, `PASS/true` full reports, parser/CLI parity, Task-7 full-only consumption, and
all required drift canaries. Final focused suite: `51/51` PASS.

I3 final review verified structured exit `125` for nonzero/spawn/timeout/root-wait,
PID-query, and survivor uncertainty, plus ordinary timeout `124` only after a real
child/grandchild tree is proven dead.

Accepted exact hashes:

- campaign orchestrator `1a4b9a526395fd64d84244def8d24f6691ac452d6718176c2106a23b2e8288b5`
- campaign contract `540d0a77accbbc3b6c47ca374b35bd2cd12110a190b5121e21f18256a5a0fe2d`
- CI-readback schema `ac451b8a40727fcf534a47f427e43c9774f393ab569a0ec8ce313d5222fe80e0`
- local-CI runner `a9616098e9c38d07b9dbec97cfc8754dcbc6c8db08e7e3288099c04492c97192`
- CI-readback contract `d634c8e2544a0854099011bdf2f6e19b8b3ecc9f76af41dc9545130188928422`

## Boundary

This closeout accepts only the three R2 repairs. It is not a whole-branch review of the
later restaged tree and does not promote R2's deterministic cohort. Fresh source freeze,
generated/package verification, complete preflight, full local CI, new one-use review
authorization, and zero-finding whole-branch review remain mandatory before commit/push.
Exact-SHA GitHub CI, external source receipt, candidate maturity, paid reviewed five-smoke
execution, and final owner acceptance remain open.

