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
  `atomics/skill/references/diagnostics/mixed-case-handling.md`, plus the
  owner/TTP surfaces that govern imported-criterion, self-refutation,
  hujjah/coercive-guidance, reason-role repair, source-worldview consequence,
  restoration, predication, transmission, and register-held cases.
- Checker/runtime surfaces: `tools/check_render_modes.py`,
  `tools/check_recursive_traversal_governance.py`,
  `skill/` generated runtime output.
- Evidence surfaces: repo-local smoke files under `../smokes/`.
- Remaining verification: manually rerun Claude Level 1/2 on the hard moral-protest canary
  and compare against the v0.3.1.0 golden for diagnostic depth, visible
  per-burden Layer A re-entry, distinct TTP submoves, operative Qur'an/hadith
  formatting, source-function coverage before final restoration, identity/worldview
  restoration, no premature Stop-2 closure, family-local pressure preservation,
  and rhetorical/restorative force.
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

#### Level 3 family/transmission coverage expansion

- Problem: RC4 regression findings for testimony/transmission/tawatur and
  Ash'ari/Maturidi family-variant kalam pressure have Level 3 analogues, but the
  current covered-scope Level 3 catalogue does not include dedicated
  testimony/transmission or family-variant owners. This pass added generic
  source-function leakage checks and non-TST pressure fixtures, but it did not
  add broad new owners outside the covered scope.
- Source surfaces: `atomics/skill/data/module-catalogue.json`,
  `atomics/skill/data/trigger-matrix.json`,
  `atomics/skill/references/diagnostics/coverage-scope.yaml`, and the relevant
  transmission/family owner source files if later authorized. Current Level 3
  checker coverage now rejects generic pressure-token lists for covered owners,
  but that does not create missing family/transmission owner coverage.
- Checker/runtime surfaces: `atomics/skill/scripts/route.py`,
  `atomics/skill/scripts/check_execution.py`,
  `atomics/skill/tests/fixtures/`, generated `skill/`, and routing parity
  fixtures under `tests/routing-fixtures/`.
- Remaining verification: decide whether to expand Level 3 covered scope with
  owner-file-faithful transmission/testimony/tawatur and family-variant kalam
  owners, or keep those as Level 1/2 governance plus routing-parity coverage.
- Status: future coverage / user decision. Do not imply Level 3 fully covers
  these families until dedicated owners and fixtures exist.

#### Level 3 catalogue-wide non-covered owner expansion

- Problem: the full runtime catalogue contains many Level 1/2-governed owners,
  profiles, diagnostics, and auxiliary TTPs that are not executable Level 3
  route/check owners in v0.3.2.0. Current Level 3 coverage is intentionally
  limited to the fixture-backed covered-scope owners in
  `atomics/skill/data/module-catalogue.json`.
- Level 1/2 status: covered by scriptless governance, routing parity,
  render/recursive checks, and owner source files. Active owners still must
  execute Target/Operation/Result, pressure the case-specific burden, land,
  and pass state/noetic re-read.
- Level 3 status by family:
  - Evidence/fitrah/attention owners not executable in Level 3 yet:
    `E1-broadening-evidence`, `E2-inferential-criterion`,
    `E3-cumulative-case`, `E4-cross-cultural-check`, `M2-prior-probability`,
    `M3-orphaned-intuition`, `R1-internalist-criterion`,
    `R2-the-reminder`, `R3-warranted-basic-belief`,
    `V5-directing-attention-signs`, `V6-convergence`,
    `husn-al-nazar-arguments`, and `inductive-fitri-method`.
  - Definition, logic, doubt, taqlid, contamination, and maieutic owners not
    executable in Level 3 yet: `M1P-performative-self-refutation`,
    `M6-excluded-middle`, `M7-definition-anchor`,
    `doubt-vs-skepticism`, `symmetric-taqlid-check`,
    `F1-supra-vs-antirational`, `F2-volitional-dimensions`,
    `F3-practice-epistemic-access`, `V3-regress-dissolution`,
    `V4-contamination-identification`, `V7-taqlid-check`,
    `V11-taqlid-transition`, `V12-tamanuc-exhaustion`,
    `P2-objection-mapping`, `P4-maieutic`, and
    `P5-already-believing`.
  - Transmission/authentication owners not executable in Level 3 yet:
    `revelation-transmission`, `V10-transmission-content-vetting`, and
    `hadith-authentication-epistemology`.
  - Kalam/family/proof-method and philosophical-frame owners not executable
    in Level 3 yet: `kalamic-interlocutor`, `proof-method-audit`,
    `philosophical-usurpation`, `P3-reason-revelation-tension`,
    `P6-universal-aqidah-principle`, `ns-6-kalamic-evidentialist`,
    and `ns-10-maturidi-evidentialist`.
  - Noetic-profile and broad case-library modules not executable as Level 3
    owners yet: `do-core`, `noetic-profiles`, `ns-1-naturalist`,
    `ns-2-agnostic-evidentialist`, `ns-3-deconverted`,
    `ns-4-secular-moral-realist`, `ns-5-habituated-atheist`,
    `ns-7-theistic-evidentialist`, `ns-8-muslim-internal-crisis`,
    `ns-9-historical-critical-skeptic`, `ns-11-fideist-reformed`,
    and `ns-12-blank-slate-dual-fitrah`.
  - Diagnostic/governance surfaces such as `definition-discipline`,
    `causal-series-taxonomy`, `perfection-criterion-usurpation`,
    `prophetic-discourse-neutralization`, `reason-disambiguation`,
    `pattern-profiling`, and `mixed-case-handling` govern Level 1/2 and
    routing parity but are not direct Level 3 owner routes unless promoted
    by an explicit covered-scope design.
- Exact blocker: each family needs owner-file-faithful Level 3 extractor
  features, trigger-matrix rules, pressure dimensions, expected fixtures,
  negative compression fixtures, and check-execution gates. Adding these
  casually would broaden the executable Level 3 claim beyond the covered scope.
- Future file/data/check needed: extend `atomics/skill/data/module-catalogue.json`,
  `atomics/skill/data/trigger-matrix.json`, `atomics/skill/scripts/diagnose.py`,
  `atomics/skill/tests/fixtures/`, `atomics/skill/tests/expected/`,
  `atomics/skill/scripts/check_execution.py`, and generated `skill/` for each
  authorized owner family.
- Status: future coverage / user decision. This is not a release blocker as
  long as docs and release claims say these owners are Level 1/2-governed or
  routing-parity covered, not executable Level 3 covered-scope owners.

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
