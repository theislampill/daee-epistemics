# Task 7 Whole-Branch R4 Repair Owner Report

Date: 2026-07-14

Scope: the five Important findings in the rejected R4 whole-branch review only.

## Disposition

Rejected prospective tree `3b022b9507a303def93c24ff8d06d44575de5c70` and its
deterministic/review-authorization cohort remain historical and non-promotable. No
governed ACCEPT artifact was created from it.

| Finding | Bounded repair | Focused evidence |
|---|---|---|
| Windows descendant custody | launch-time Job Object custody for probes and producer processes, with suspended assign/verify/resume and fail-closed cleanup | process canaries, live producer `31/31`, full reviewed campaign `76/76` GREEN |
| Stage07 tooling identity | create-once exact-source tooling manifest, production rechecks, strict finalizer/promotion binding, dirty/deletion and paid-fixture canaries | manifest `6/6`, full campaign `76/76`, registered producer structural `17/17` GREEN |
| absent-ref upstream equality | null-predecessor exact CAS create followed by explicit upstream establishment and four-way equality readback | VCS `13/13`, CI-readback `57/57`, fixture `41/41`, both checker self-tests GREEN |
| first-host liveness | bounded post-start liveness before in-flight attestation and fan-out | already-exited-process canary GREEN |
| launch-relative deadlines | one monotonic deadline per launch and remaining-budget observation | elapsed-before-observation canary GREEN |

Independent bounded reviews accepted all five repairs on exact hashes. The complete hash
inventory and detailed evidence are preserved in the durable Task 11an–11aq records.

This repair-level closeout does not promote R4 evidence and does not claim a new source
freeze, deterministic closure, whole-branch acceptance, commit, push, exact-SHA CI,
candidate maturity, model execution, owner acceptance, release readiness, or terminal
A01–A16 closure. Paid execution remains `0/5`.

