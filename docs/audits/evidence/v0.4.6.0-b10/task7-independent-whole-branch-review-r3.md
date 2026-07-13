# Task 7 independent whole-branch review - Revision 3

Date: 2026-07-12
Branch: `codex/v0.4.6.0-runtime-footprint-b10`
HEAD: `4bb7018f793166467a0215bbe614a9ae0b97f0ee`
Independent reviewer: `/root/task7_whole_branch_review`
Verdict: `REJECT`

- Critical findings: `0`
- Important findings: `0`
- Minor findings: `2`
- Canonical whole-branch review JSON created: `no`
- Source or staged bytes modified by this review: `no`

The zero-finding acceptance condition is not met. This is a durable rejection
record only. It does not authorize independent-review ACCEPT publication or any
downstream progression.

## Exact reviewed identity

| Surface | Identity | Bytes / count | File SHA-256 |
|---|---|---:|---|
| Prospective Git tree | `a683ab24a52cdc9af2ad7f6fb92b6ef470e8d88e` | 238 staged paths | - |
| Source freeze | `40dbcd03eb9e61b7b5dd579aab419f367548f9c98f8e6927b6a73925927083d9` | 812679 bytes; 3464 files | `7ff24f167fead7a5c4abc75c753718ecd2291aa21736793574de47444f0c394f` |
| Reviewer authorization | `3d2e4b0d32d382ad55274090447dd4793cf8743a92d750a91730e09b3c5f5188` | 717 bytes | `d81744f5975e1b2b8b18fa60427ff92faee67b869d2969c04cc1cfea3643b1d0` |
| Generated-freshness/package PASS | current exact-tree bundle | 2371 bytes; 7/7 checks | `15347337fb5fc1ea10103367100dff1650110c7b5871442cd8f1d9a227e5ef25` |
| No-model-preflight PASS | current exact-tree bundle | 2326 bytes; 25/25 gates; 62 commands | `0a06338fb75e986ef266ee1d99d362fcf5f992d9e5fc81d2e9dedda353887a5f` |
| Full-local-CI PASS | current exact-tree bundle | 2304 bytes; 172/172 commands | `91a98ca86e57feaa0085c5476a9cf98f974da61f595b99f64070691bfcfada78` |

The authorization names this reviewer, binds the exact prospective tree and source
freeze, was issued at `2026-07-13T02:44:13Z`, and passes the staged producer's
`validate_review_authorization` function.

The complete freeze manifest has 3464 unique sorted paths, 42341880 source bytes,
and review-manifest aggregate
`e4cdd8f36be640931c6bff0839cb0404e475a18b769b9e7ef016578aa8b619a4`.
Every path, byte count, blob OID, and raw SHA-256 was replayed from the exact Git
tree and matched. The clean-filter worktree verifier also passed. The three
deterministic bundles above independently pass the contentful downstream bundle
validator, bind the same tree/freeze, record zero model calls, and remain bounded,
nonterminal observations. Their PASS status does not override the findings.

## R1 and R2 reconciliation

All concrete R1 and R2 repair families were reopened against current staged bytes.
The earlier defects remain closed:

- Gate 16's shared expected exit is consumed consistently by preflight, Task 7
  production, and CI readback.
- Preflight timeout handling uses owned process-tree custody and stops the gate.
- Reviewed-campaign post-observation cleanup, incident/finalizer reconstruction,
  and create-once custody remain present.
- The isolated Python bootstrap orders repository/tool roots, stdlib/platstdlib,
  then system/user package roots and removes inherited Python startup variables.
- ADR-046-017 names the existing `tools/artifact_tree.py`; all ADR owner paths are
  checked for portable containment and regular-file existence.
- Source-freeze clean-filter parser failure canaries, audit-index owners, and OPEN
  dimensional closure contracts remain present.
- R2 path-custody reads/publications reject rooted, drive, UNC/device, traversal,
  backslash, colon/ADS, trailing-alias, reserved-device, and control forms before
  filesystem access.
- Suffix-only local CI is `PARTIAL` / `complete=false`; its producer, schema,
  parser, CLI JSON, counts, and plan digests agree, while Task 7 remains full-only.
- Windows timeout teardown uncertainty produces structured
  `PROCESS_TREE_TEARDOWN` exit 125; ordinary timeout 124 remains reserved for a
  tree proven dead.

The findings below are residual supported-contract gaps outside those already
closed defect statements.

## Minor findings

### M1 - Isolated worker-root metadata bypasses the portable path validator

Evidence:

- `tools/reviewed_campaign_orchestrator.py:155-173` defines the new portable
  string-level path validator used for campaign filesystem custody.
- `tools/reviewed_campaign_orchestrator.py:1447-1458` separately validates
  authorization field `isolated_root_prefix` with host-dependent
  `Path.is_absolute()` and `..` checks instead of that portable validator.
- The resulting `home`, `cache`, and `run_root` strings are bound into the
  execution-custody envelope at line 1500, submitted to the supported adapter at
  lines 1508-1521, and mirrored into producer/cold dispatch manifests.
- Existing contracts use only ordinary prefixes
  `producer/isolated` and `cold-review/isolated`; no hostile prefix canary exists.
- Reviewed source SHA-256 is
  `tools/reviewed_campaign_orchestrator.py` =
  `1a4b9a526395fd64d84244def8d24f6691ac452d6718176c2106a23b2e8288b5`.

Bounded Windows probe, with no filesystem access or provider call:

```text
'/escape' ACCEPT home=/escape/producer-01/home dispatch_issues=[]
'\\escape' ACCEPT home=\escape/producer-01/home dispatch_issues=[]
'C:escape' ACCEPT home=C:escape/producer-01/home dispatch_issues=[]
'isolated:stream' ACCEPT home=isolated:stream/producer-01/home dispatch_issues=[]
'NUL/workers' ACCEPT home=NUL/workers/producer-01/home dispatch_issues=[]
'producer/isolated' ACCEPT home=producer/isolated/producer-01/home dispatch_issues=[]
```

Impact:

An otherwise accepted producer or cold-review authorization can emit structurally
green execution-custody and dispatch metadata whose worker roots are rooted,
drive-relative, ADS-like, or reserved on Windows. The currently supported adapter
is deterministic fake/no-dispatch, and this probe made no out-of-root write, so
this is a metadata/isolation-contract gap rather than a demonstrated filesystem
escape.

Required repair:

1. Validate `isolated_root_prefix` with the same portable string-level owner before
   any claim, reservation, or adapter boundary, and construct worker paths only
   from its canonical slash-separated parts.
2. Add producer and cold-review negatives for rooted slash/backslash, drive,
   UNC/device, traversal, ADS/colon, aliases, reserved devices, and controls.
3. Prove hostile prefixes fail before claims/reservations/adapter calls and that
   ordinary worker inventories and dispatch manifests remain exact.

### M2 - Durable STATE routing predates the current completed deterministic cohort

Evidence:

- `.IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5/STATE.md:15-16`
  says no new freeze has occurred and routes next to staging, freezing, and
  rebuilding deterministic evidence.
- The final Task 7 continuity section at `STATE.md:342-344` repeats that source
  freeze, generated/package, preflight, and full local CI remain to be run.
- The current retained cohort already binds exact tree
  `a683ab24a52cdc9af2ad7f6fb92b6ef470e8d88e`, source freeze
  `40dbcd03eb9e61b7b5dd579aab419f367548f9c98f8e6927b6a73925927083d9`,
  and the three contentful PASS bundle hashes recorded above.
- Current `STATE.md` SHA-256 is
  `12284496ad083205beb0c4879e523a11dc4b4529a290eb0a553d47c8aa1d8cce`.

Impact:

The sole durable numbered-ANDON owner routes a successor into already completed
evidence work and omits the current review boundary. It makes no terminal claim,
but it is no longer a truthful current-state handoff.

Required repair:

1. Preserve this exact R3-reviewed cohort as historical/non-promotable evidence
   after the M1 finding.
2. Record the R3 rejection and remaining M1 repair in `STATE.md`, which remains the
   sole numbered ANDON owner; do not create a competing `ANDON.md`.
3. Route next to the narrow M1 repair, then a fresh exact tree, source freeze,
   deterministic cohort, one-use authorization, and zero-finding whole-branch
   review.

## Verification performed

- Exact branch, HEAD, 238-path index tree, zero unstaged paths, and zero untracked
  paths were checked.
- The complete 3464-file source freeze was replayed from Git and through the
  clean-filter worktree verifier.
- The one-use reviewer authorization passed the repository validator.
- Generated/package, complete preflight, and full local-CI bundles passed the
  contentful downstream bundle validator and matched their supplied hashes.
- Native preflight is complete at 25 gates / 62 commands / zero timeouts.
- Native local CI is complete at 172/172, start 1, end 172, strict PowerShell,
  timeout bound 900, zero timeout, and zero skip.
- All 36 staged Python files parsed as AST; all 188 staged JSON files passed strict
  duplicate-key parsing; no conflict markers were found.
- All seven paths changed since the rejected R2 tree were reopened; the remaining
  231 staged paths are blob-identical to the already inspected tree.
- Closure-ledger live validation, generated Markdown parity, sole-ANDON-owner
  inventory, and staged `git diff --check` passed on unchanged governing bytes.
- No model/provider call, broad-suite replay, package/candidate action, source edit,
  or staging action was performed by this review.

## Explicit downstream nonclaims

This `REJECT` record is not evidence of and does not claim or authorize:

- a canonical Task 7 independent whole-branch review ACCEPT verdict or JSON record;
- repair acceptance or review of a post-repair source identity;
- a successor commit, commit-authorization use, push, or remote readback;
- external source receipt, exact-SHA GitHub CI, or branch-protection satisfaction;
- immutable candidate construction, retention, maturity, readiness, or promotion;
- provider/model execution, reviewed five-smoke execution, cold review, or campaign
  success;
- tag, release package, release, publication, deployment, owner acceptance, or
  terminal closure of any A01-A16 row.

## Decision and required next gate

`REJECT` exact tree `a683ab24a52cdc9af2ad7f6fb92b6ef470e8d88e` for Task 7
whole-branch-review promotion.

Close both Minor findings with a narrow reviewed repair/continuity update. Because
the M1 repair changes governed source and tests, create a fresh exact source freeze,
regenerate the affected deterministic receipts, obtain a fresh one-use review
authorization, and perform a new independent whole-branch review. Only a
zero-Critical, zero-Important, zero-Minor result may create the canonical review
JSON and proceed to later gates.
