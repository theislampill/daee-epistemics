# Task 7 Whole-Branch R1 Repair Owner Report

Date: 2026-07-12

Scope: exact concrete findings from `task7-independent-whole-branch-review-r1.md` only.

## Disposition

The rejected prospective tree `10810336aae80320695962be7cf95c7c70d65b07`
and its deterministic PASS cohort remain historical, preserved, and non-promotable.
Every R1 finding was repaired test-first on later working bytes without claiming a new
source freeze, deterministic closure, commit, push, exact-SHA CI, candidate maturity,
model execution, or terminal A01-A16 closure.

| Finding | Owner disposition | Focused result |
|---|---|---|
| I1 downstream Gate 16 return-code drift | shared expected-return-code map consumed by CI readback; Gate 16 requires exit 1 and every other gate exit 0 | CI-readback contract and writer/fixture checks PASS |
| I2 preflight timeout descendant leakage/continuation | all preflight children use owned command custody; timeout terminates descendants, halts the gate sequence, and produces an incomplete unauthorized report | timeout contract and preflight self-test PASS; zero owned residue |
| I3 campaign post-observation and resume custody | phase-aware cleanup and terminalization; incident and standalone success-finalizer adoption reconstruct exact retained claims, results, transactions, state, completion, dispatch, and live usage | reviewed-campaign contract `41/41` PASS; self-test PASS; zero residue |
| I4 bootstrap import precedence | repository/tool roots, then stdlib/platstdlib, then system/user packages, then inherited safe roots; deterministic dedupe and fail-closed sysconfig roots | CI-readback contract `45/45` PASS |
| I5 ADR owner custody | ADR-046-017 names `tools/artifact_tree.py`; every owner path must be safe, portable, non-ADS, repository-contained, and an existing regular file | ADR self-test `1` valid / `5` invalid and live ledger PASS |
| M1 source-freeze writer mutation depth | malformed/count/missing/non-ASCII/CR-LF/Git-failure canaries retained | writer self-test PASS |
| M2 audit index omissions | closure ledger, contract registry, and ADR carrier listed as explicit OPEN/STRUCTURAL/NON-TERMINAL controls | independent rereview ACCEPT |
| M3 durable continuity staleness | STATE/ROADMAP/phase/Hansei/closure ledger identify Revision 4, R1 rejection, historical evidence, repair wave, and downstream nonclaims | closure `5/17`, live checker, renderer, diff hygiene PASS |

## Stable focused identities

- `tools/reviewed_campaign_orchestrator.py` SHA-256
  `d7c1bbcf655fede269a2b1fde4362774b26b8ad276ee9bf88c03f5b3ad06528e`
- `tests/reviewed-campaign-orchestration/test_contract.py` SHA-256
  `607f39d2243c41f9192121569110e0aa1500cfa2241a40fd3cc6e3662e3fc674`
- `tools/check_architecture_decision_ledger.py` SHA-256
  `3b70be4398930edac8910badc0724494350b4f50a2930e3d0c03a6e8c8608820`
- `docs/audits/v0.4.6.0-wip-architecture-decisions.json` SHA-256
  `d36f25a3955b29c04de5cb9225ebec13a441926e36c849bb42eb1f611b0f6085`

## Next exact boundary

Stop all writers, reconcile and stage the complete reviewed source set, compute the new
prospective tree, then rebuild source-freeze, generated/package, complete no-model
preflight, and full local-CI evidence. A new independently authorized whole-branch review
must accept that exact tree before any successor commit or push.

