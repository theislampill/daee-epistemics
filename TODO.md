# TODO

This file tracks live work only. Completed v0.3.2.0 audit and hardening details
belong in the changelog and audit closure reports, not as active TODO prose.

Current layout:

```text
atomics/skill/          = canonical atomized editable source
skill/                  = generated compiled Claude package root
tools/                  = compiler/checker scripts
tests/routing-fixtures/ = static routing parity fixtures
docs/                   = architecture, audit, and workflow notes
```

## Active

### Current Canon Checker Anchors

- Problem: current-canon metacompliance intentionally verifies that TODO still
  remembers the live render surface instead of drifting into stale public-audit
  or prose-only framing.
- Required canon tokens: compact DSL/IR; bounded governed Layer B; Hidden Premises;
  Core Formulation; TTP/operator trace; state/noetic re-read;
  Restorative Response; Closing Formulation; deprecated `:audit` as public output.
- Source surfaces: `atomics/skill/SKILL.md`,
  `atomics/skill/references/rubrics/diagnostic-render-contract.md`, and
  generated `skill/SKILL.md`.
- Checker/runtime surfaces: `tools/check_metacompliance_current_canon.py`.
- Status: active checker anchor only; not a completed-work catalogue.

### Manual Level 1/2 Behavioral Rerun

- Problem: the Level 1/2 hard moral-protest / worship-worthiness output previously shrank against the
  v0.3.1.0 golden. Spec and checker hardening does not prove live model recovery.
- Source surfaces: `atomics/skill/SKILL.md`,
  `atomics/skill/references/rubrics/diagnostic-render-contract.md`,
  `atomics/skill/references/rubrics/output-release.md`,
  `atomics/skill/references/runtime-output-governance.md`,
  `atomics/skill/references/diagnostics/recursive-state-transitions.md`, and
  `atomics/skill/references/diagnostics/mixed-case-handling.md`.
- Checker/runtime surfaces: `tools/check_render_modes.py`,
  `tools/check_recursive_traversal_governance.py`,
  `skill/` generated runtime output.
- Evidence surfaces: repo-local smoke files under `../smokes/`.
- Remaining verification: manually rerun Claude Level 1/2 on the hard moral-protest canary
  and compare against the v0.3.1.0 golden for diagnostic depth, visible
  per-burden Layer A re-entry, distinct TTP submoves, operative Qur'an/hadith
  formatting, identity/worldview restoration, and rhetorical/restorative force.
- Status: active. Do not claim the behavioral regression fixed until this manual
  rerun passes.

### Release Asset Rebake Decision

- Problem: this hardening campaign changed source, tooling, tests, docs, and
  generated runtime output, but did not rebake or replace the v0.3.2.0 release
  asset by instruction.
- Source surfaces: `atomics/skill/`, `tools/`, `tests/`, release docs.
- Runtime surfaces: generated `skill/`.
- Remaining verification: if the user authorizes a release asset refresh, run the
  package workflow, update release-artifact docs and smoke/package SHA guards,
  replace the existing GitHub Release asset, download it back, and verify SHA.
- Status: active only if release rebake is authorized. Do not tag, push, package,
  or update GitHub Release from this TODO alone.

### Audit Report Tracking Decision

- Problem: `docs/audits/v0.3.2.0-*.md` is ignored by `.git/info/exclude`.
- Source surfaces: `docs/audits/v0.3.2.0-systemic-hardening-closure.md` and the
  prior systemic audit reports.
- Remaining verification: decide whether these reports should remain local-only
  or be force-added later with explicit staging.
- Status: requires user decision.

### Coverage Scope Owner Review Anchors

#### Bespoke religion-specific source-content owners

- Problem: coverage-scope claims for Buddhist, Hindu, Jewish, and similar
  source-content cases are intentionally marked needs-review/out-of-scope rather
  than packaged runtime owners.
- Source surfaces: `atomics/skill/references/diagnostics/coverage-scope.yaml`.
- Checker/runtime surfaces: `tools/check_coverage.py`, generated coverage report.
- Remaining verification: decide whether to add owner-file-faithful source-content
  owners in a later release line, keep them out of scope, or add narrower hold
  rules without pretending coverage exists.
- Status: active review anchor for coverage integrity.

#### Sufism-related source-content adjudication

- Problem: Sufism/tariqah authority and contested-practice cases require
  careful owner design before being treated as covered runtime source-content.
- Source surfaces: `atomics/skill/references/diagnostics/coverage-scope.yaml`.
- Checker/runtime surfaces: `tools/check_coverage.py`, generated coverage report.
- Remaining verification: decide whether to add specific adjudication owners,
  keep the cases out of scope, or document a narrower source-status hold rule.
- Status: active review anchor for coverage integrity.

## Closed In Current Working Tree

The v0.3.2.0 systemic hardening closure report catalogues every reported audit
item and maps each to patched, partial, deferred, rejected, or user-decision
status:

```text
docs/audits/v0.3.2.0-systemic-hardening-closure.md
```

Do not use this closed list as release proof. It records source/checker/runtime
hardening only; live Level 1/2 behavior remains gated by the manual rerun above.

### Structural Attachment / Reconstruction-Faithfulness Hardening

- Problem: route labels, owner markers, checker output, and state tokens can appear
  somewhere while losing the burden-local attachment that makes them executable.
- Source surfaces: `AGENTS.md`,
  `atomics/skill/references/diagnostics/recursive-state-transitions.md`,
  `atomics/skill/references/rubrics/diagnostic-render-contract.md`, and
  `atomics/skill/references/diagnostics/ir-reconstruction-pass.md`.
- Checker/runtime surfaces: `atomics/skill/scripts/route.py`,
  `atomics/skill/scripts/validate.py`, `atomics/skill/scripts/check_execution.py`,
  `atomics/skill/scripts/daee_level3.py`, and generated `skill/`.
- Status: patched in source with burden-local `state_envelope` replay and targeted
  structural-flattening checks. Follow-up notation normalization added `ⁿBᵢ` / `nBi`
  as the human/math and plain-text burden-submove notation while preserving `B1.s1`
  as a checker-compatible alias. Verification is recorded in the closure report after
  generated runtime rebuilds.
