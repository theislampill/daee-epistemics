# Owner/TTP Operation-Token Drift — D3 Inventory & Quarantine

> Plan 17 deliverable, read-only / computed. Records the one measured D3
> operation-token drift row and its owner-adjudicated disposition. This is
> correctness / operation-token **schema parity** only — NOT a refusal, safety, or
> policy layer (the dual-use/safety infrastructure removed at `455a921` stays
> removed). Dated 2026-07-04.

## Background

Plan 17 already ships (green): the R2 family-parity check
(`tools/check_owner_contract_parity.py`, registered `required`) enforces that every
owner-family key in the source-owned ACT-operation set is declared in
`delta-result-vocabulary.json` `owner_families`; the drift inventory
(`docs/audits/owner-contract-drift-inventory.md`) observes D1-D5. The remaining open
drift is **D3 on the operation-token axis**: a formal owner contract's
`operation_token` can name an operation the vocabulary never declared in
`owner_operations`, and `check_ttp_availability_canaries.source_owned_operations_for_owner`
trusts that token verbatim without cross-checking it against R1.

## The single measured D3 row

| Contract | Owner family | Tokens with no R1 `owner_operations` home |
| --- | --- | --- |
| `TTP-MRP-mid-reread-pressure` | MRP | the 5 MRP reread route-result tokens |

Verified read-only: `delta-result-vocabulary.json` `owner_operations` has **zero** MRP
entries. Crucially, MRP's tokens are **reread route-result-type names on a different
axis** than `owner_operations` (which names Layer-B owner operations). MRP is never a
Layer-B owner code (`TTP-MRP-mid-reread-pressure.md`), so declaring its tokens in
`owner_operations` would be a **category error**, not a parity fix. The gap is
**latent**: `source_owned_operations_for_owner('MRP')` is never exercised by any live
fixture (no fixture selects an MRP owner).

## Disposition (owner-adjudicated 2026-07-04)

- **OD-17a — QUARANTINE (cross-namespace).** Record the MRP D3 row here as an
  intentional cross-namespace case. Do **not** declare the MRP tokens in
  `owner_operations` (wrong axis) and do **not** rewrite the contract's
  `operation_token` (a semantics edit). MRP reread tokens and owner-operation tokens
  are distinct axes; forcing them together is incorrect.
- **OD-17b — ADVISORY, not a failing gate.** If a D3 operation-token cross-check is
  ever added, it is **advisory info-only**, never a CI-failing gate — a failing gate
  would add red-CI risk on future contract authoring without closing any live hole
  (the gap is latent).

## What this does not do

- It authors no new owner/TTP semantics and adds no failing checker.
- It is not a refusal/safety/adversarial-memetic layer; it is operation-token schema
  parity accounting only.
- It closes no gate on its own; it records the quarantine so a future advisory
  cross-check (if ever built) has a dated baseline.
