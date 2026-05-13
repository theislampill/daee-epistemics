# Codex Smoke-Test Findings

Host/testing caveat only.
Not runtime doctrine.
Does not create routes, module activation rules, IR fields, output modes, or source owners.

This note records why smoke tests run inside Codex can report compliance difficulties that are
partly host-shaped rather than purely daee-runtime-shaped. It is intended for maintainers designing
manual smoke tests or interpreting model-output regressions.

## Summary

Codex skill use is not the same thing as Claude skill runtime use. Codex can load and use skills,
but the surrounding host has its own agent instructions, tool channels, planning/review modes,
workspace behavior, and progressive-disclosure skill protocol. Those higher-priority or adjacent
behaviors can compete with the daee default response contract unless the smoke harness isolates the
final user-facing answer.

The practical consequence is simple: a Codex smoke result can be useful, but it is not a pure
model-compliance oracle. Grade what the installed skill emits as the final answer under a clean
daee invocation, and record any host confounders separately.

## Host Confounders

- Codex may emit commentary/tool narration while gathering context. Daee default mode forbids
  visible setup, loading, and composition narration, so smoke grading should inspect the final
  answer rather than intermediary tool chatter.
- Codex's skill protocol uses progressive disclosure. Daee substantive cases require specific
  runtime bundle loading and internal Phase 2 / output-governance execution. If a smoke prompt
  does not force installed-skill execution, Codex may under-load the runtime path while still
  producing plausible prose.
- Codex Plan Mode, code-review stance, repo-edit tasks, or coding-agent instructions can override
  daee output shape. Smoke tests should run in a clean thread without an active planning,
  implementation, review, or repository-maintenance task.
- Codex shares a workspace with the repo. If the prompt asks for audit, comparison, patching, or
  verification, Codex may answer as a coding agent rather than as the daee runtime.
- The compiled package contains runtime bundles, not every atomized source file. A valid Codex
  smoke must follow `compiled-module-map.json` resolution and must not chase missing atomized paths
  as literal runtime files.
- Codex may use local docs, repo files, and tool outputs as context. That is useful for
  development audits, but it is not identical to an installed `.skill.zip` runtime invocation.

## Recommended Codex Smoke Harness

Run Codex smoke tests in a clean thread/profile with the compiled daee skill installed. Do not run
them from an active repo-edit conversation. Frame prompts as user-facing daee invocations, for
example:

```text
/daee-epistemics There is no evidence for God, so belief is irrational.
```

For default-mode grading, inspect only the final answer. Do not count Codex commentary messages,
tool logs, file reads, or planning updates as daee runtime output.

For audit-mode grading, explicitly invoke the audit render:

```text
/daee-epistemics:audit The Father is God, the Son is God, and the Spirit is God. They are distinct persons. So by identity there are three Gods.
```

## What To Record

For each Codex smoke, record:

- host mode: default, Plan Mode, review posture, or repo-edit context;
- whether the compiled skill was installed or the repo files were merely available;
- whether the final answer, not commentary, was graded;
- whether the answer followed compiled runtime path resolution;
- whether the failure was output-shape, routing, Phase 2, TTP execution, state re-read, or host
  contamination.

## Interpretation Rule

Treat Codex smoke tests as host-aware behavioral probes. A failure is strong evidence only when it
survives a clean installed-skill thread, final-answer-only grading, and prompts framed as daee
runtime invocations. Development-thread failures may still be useful, but they should be labeled
as Codex-host confounded until reproduced in that cleaner harness.
