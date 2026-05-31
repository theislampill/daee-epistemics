# ActiveGraph Event Model Sketch

Status: `READY_FOR_EXPERIMENTAL_SIDECAR_USE`

This document defines the initial event model for bounded local ActiveGraph
sidecar use. It is not canonical and not a migration plan. The canonical proof
ledger remains `docs/audits/v0.4.3.0-implementaudit-orchestrator.md`.

## Candidate Entities

| Entity | Purpose |
|---|---|
| `ledger_row` | A row from the open-work ledger or orchestrator |
| `proposal` | A candidate patch lane, docs lane, or owner decision |
| `proof_item` | A file, hash, sidecar, certificate, smoke output, or command result |
| `smoke_run` | A governed model/harness run and its input/output/provenance |
| `checker_result` | A checker command, exit code, output summary, and target artifact |
| `subagent_history_item` | A read-only or patching subagent/session report |
| `d8_classification` | D.8 sidebar/history cleanup classification by exact ID |
| `commit` | A source-boundary commit and its proof/CI relationship |
| `release_checkpoint` | Tag/release/package/provenance boundary event |
| `blocker` | A named unmet prerequisite or owner decision |
| `dependency_edge` | A relationship between rows, artifacts, checks, or blockers |

## v0.4.3.x Ledger-Closure Vocabulary

For bounded ledger-closure waves, use these names as the sidecar orchestration
vocabulary. The Markdown ledgers remain canonical; these are ActiveGraph
node/edge/event labels only.

Node types:

- `LedgerRow`
- `SubagentRun`
- `EvidenceFile`
- `Commit`
- `Smoke`
- `Blocker`
- `OwnerDecision`
- `D8HistoryItem`
- `GraphifyArtifact`
- `ActiveGraphScratchRun`

Edge types:

- `audits`
- `blocks`
- `closes`
- `supersedes`
- `needs_owner_decision`
- `produced_evidence`
- `verified_by`
- `references`
- `forked_from`

Required event types:

- `subagent.spawn_requested`
- `subagent.spawn_failed`
- `subagent.reported`
- `ledger.row_classified`
- `ledger.row_closed`
- `ledger.row_blocked`
- `evidence.attached`
- `owner.decision_required`
- `d8.history_classified`
- `graphify.report_consulted`

## Candidate Event Types

```json
{
  "event_id": "uuid",
  "event_type": "ledger.row.classified",
  "timestamp": "iso-8601",
  "actor": "codex|user|subagent:<id>|ci",
  "row_id": "A.1",
  "status_before": "PARTIAL",
  "status_after": "CLOSED_DOCS_ONLY",
  "evidence": [
    {
      "path": "docs/algebraic-notation-and-noetic-formalism.md",
      "sha256": "...",
      "evidence_type": "source|checker|fixture|smoke|audit-doc|ci"
    }
  ],
  "commands": [
    {
      "command": "python tools/build_docs_index.py --check",
      "exit_code": 0,
      "summary": "PASS"
    }
  ],
  "boundaries": [
    "no package",
    "no tag",
    "no release",
    "no A.13",
    "no D.8 cleanup"
  ],
  "notes": "human-readable summary"
}
```

Potential event names:

- `ledger.row.classified`
- `proposal.created`
- `proposal.accepted`
- `proposal.rejected`
- `proof.artifact.recorded`
- `checker.result.recorded`
- `smoke.run.recorded`
- `subagent.report.recorded`
- `d8.item.classified`
- `blocker.opened`
- `blocker.closed`
- `commit.boundary.recorded`
- `release.checkpoint.recorded`

## Candidate Relationships

| Edge | Meaning |
|---|---|
| `row_depends_on_row` | Row B cannot close before row A |
| `row_proven_by_checker` | A checker is required evidence for the row |
| `checker_exercises_fixture` | Fixture coverage for a checker rule |
| `smoke_produces_artifact` | Smoke output/certificate/Grapher artifact |
| `artifact_hash_recorded_in` | Manifest or orchestrator stores the hash |
| `subagent_finding_preserved_in` | Subagent finding was folded into a ledger/orchestrator row |
| `commit_contains_artifact` | Commit captured source/proof files |
| `release_targets_commit` | Release checkpoint points to a commit |
| `blocker_blocks_row` | A blocker prevents row closure |

## Scratch Smoke Mapping

The initial scratch smoke used:

- `ledger_row` object with `row_id = D.7`;
- `proof_item` object pointing to `docs/audits/ACTIVEGRAPH_PREFLIGHT.md`;
- `has_preflight_evidence` relation from the row to the proof item;
- `runtime.idle` event as the terminal event.

This proves only that ActiveGraph can record and replay a tiny local sidecar
event graph in ignored scratch storage.

The 2026-05-31 gate refresh added a second tiny run,
`activegraph_scratch_v043x_gate_20260531_r2`, using the v0.4.3.x names
`LedgerRow`, `EvidenceFile`, and `produced_evidence`. It also verified
`inspect`, `replay`, `fork`, and `diff` on ignored SQLite scratch storage. The
fork command generated run id `01KSZT05B7KRRCVKKYQP694KTV`; the human label was
not a usable run id for diff.

## Later Spike Requirements

Before ActiveGraph can be promoted beyond an ignored experimental sidecar,
define:

- storage path and ignored/tracked policy;
- event schema versioning;
- exact D.8 subagent ID retention model;
- fork/diff semantics for parallel agents;
- redaction rules for paths, prompts, logs, secrets, and private data;
- cleanup/retention rules;
- import/export from the Markdown orchestrator;
- failure recovery and replay checks;
- explicit owner decision that ActiveGraph is allowed for a bounded spike.

## Non-Claims

ActiveGraph would be custody/orchestration metadata only. It would not prove
runtime behavior, checker correctness, Output Grapher correctness, prose-scope
adequacy, package provenance, release readiness, or public docs truthfulness.
