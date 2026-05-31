# IMPLEMENTAUDIT Execution Templates

Status: process guidance.

These templates standardize IMPLEMENTAUDIT execution state for ledger rows,
failure compaction, subagent tasks, and pause/resume checkpoints. They do not
replace the active proof ledger:
`docs/audits/v0.4.3.0-implementaudit-orchestrator.md`.

## Ledger Row Execution Object

```yaml
row_id:
status:
dependencies:
allowed_files:
forbidden_files:
required_checkers:
required_fixtures:
required_smokes:
proof_artifacts:
blocking_failures:
next_smallest_action:
release_gate_impact:
```

## Failure Compaction Object

```yaml
failure:
  command:
  exit_code:
  exact_text:
  classification:
  affected_rows:
  minimal_patch_scope:
  forbidden_scope:
  rerun_commands:
```

## Subagent Task Object

```yaml
agent:
  lane:
  read_only: true/false
  allowed_files:
  forbidden_actions:
  required_commands:
  stop_condition:
  return_shape:
```

## Pause/Resume Checkpoint Object

```yaml
checkpoint:
  current_goal:
  current_sha:
  dirty_status:
  active_row:
  active_artifacts:
  last_passing_commands:
  last_failing_commands:
  next_action:
```
