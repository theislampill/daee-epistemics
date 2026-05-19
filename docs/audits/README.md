# Audit Retention Policy

This directory keeps audit evidence usable without making every historical
snapshot look like current release truth.

## Status Classes

Use these classes when updating `docs/audits/INDEX.md`:

| Status | Meaning | Default action |
|---|---|---|
| ACTIVE CURRENT TRUTH | Current source of readiness, release, runtime, docs/index, or governance truth. | Keep in the active index. |
| ACTIVE IMPLEMENTATION EVIDENCE | Current proof that a named implementation loop closed. | Keep in the active index until superseded by a later implementation record. |
| FUTURE-WORK SOURCE | Contains deferred or tabled work that still needs a clean owner and next action. | Move the deferred item into `v0.4.3.0-future-work-ledger.md`; keep the source audit linked. |
| SUPERSEDED BUT KEEP | Historical snapshot superseded by a named newer audit, but still useful for provenance. | Keep linked under Historical / archived audits and name the superseding file. |
| HISTORICAL SNAPSHOT | Prior release-line evidence or background no longer carrying current blockers. | Keep under Historical / archived audits. |
| OWNER DECISION REQUIRED | A finding cannot be closed safely without maintainer direction. | Keep visible until an owner decides. |
| DELETE CANDIDATE | Duplicate, unreferenced, recoverable from Git history, and not release/provenance evidence. | Delete only after reference search and owner approval. |

## Retention Rules

- Current audit docs appear in the active index.
- `Current implementation targets` is the work queue. A finding is eligible for
  implementation only when it is explicitly promoted there.
- Historical snapshots are classified under Historical / archived audits or moved to
  `docs/audits/archive/` only after references are updated.
- Superseded docs must name what superseded them.
- Deferred and future-work items belong in `v0.4.3.0-future-work-ledger.md`, not
  repeated as live blockers across old audits. The future-work ledger is backlog,
  not an implementation input.
- Do not implement items listed only under Future work, Deferred, Owner decision
  required, Historical, or Out of scope. Preserve/classify them with owner/source,
  reason deferred, next smallest action, verification, and closure status.
- Deleted docs must be duplicate, unreferenced, not release/provenance evidence,
  and recoverable from Git history.
- Do not delete current release evidence, package/smoke evidence, audit-of-audits
  records, or owner-facing handoff mirrors without an explicit owner decision.

## Current Archive Mode

The v0.4.3.0 pruning pass uses index classification rather than physical moves.
Reference search found active inbound links for the audit corpus, so moving files
would create link churn without reducing source overload.
