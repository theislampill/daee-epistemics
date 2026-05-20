# TODO

This file tracks live work only. Completed v0.3.2.0 audit and hardening details
belong in the changelog and audit closure reports, not as active TODO prose.

Current layout:

```text
atomics/skill/          = canonical atomized editable source
skill/                  = ignored local/CI compiled Claude package root
tools/                  = compiler/checker scripts
tests/routing-fixtures/ = static routing parity fixtures
docs/                   = architecture, audit, and workflow notes
```

## Work Item Protocol

Use tagged context and structured TODO entries so active work does not drift into
mixed evidence, proposal, and release claims.

- RTFM: every TODO item must point to the repo manuals or canonical source surfaces
  needed to finish it. If the answer is in atomics, generated runtime, checkers, or
  package docs, read those before patching.
- Tagged context: prefer tags such as `[source]`, `[runtime]`, `[checker]`,
  `[fixture]`, `[smoke]`, `[docs]`, `[package]`, `[release]`, `[decision]`, and
  `[blocker]` in headings or status lines.
- Structured output: each active item should make the problem, source surfaces,
  checker/runtime surfaces, remaining verification, status, and decision boundary
  visible without requiring archaeology.
- OODA: Observe the evidence, Orient against source-of-truth boundaries, Decide the
  smallest honest patch/defer/reject path, then Act with source-first edits and
  verification.
- Default RACI: Responsible = patching agent; Accountable = user/maintainer for
  schema, package, release, and scope decisions; Consulted = atomics, generated
  runtime, checkers, fixtures, smoke artifacts, and release docs; Informed =
  `TODO.md`, audit docs, `README.md`, and navigation docs when claims change.
- MoSCoW: Must = release/truth-boundary blocker; Should = important hardening not
  required for the current gate; Could = optional coverage or ergonomics; Won't =
  intentionally out of scope for the current release line.
- RFC/ADR: any architecture, schema, package-boundary, release-line, or public runtime
  surface change needs a decision record here or in `docs/audits/` with status,
  evidence, consequences, and explicit defer/reject criteria.
- Interface contract discipline: if a contract changes, update producers, consumers,
  schemas, tests, examples, and docs together, or mark the incomplete edge explicitly.
  Keep parsing, validation, routing, execution, persistence, rendering, and documentation
  separate unless an owning module justifies combining them. Owner first: name the owning
  file/module/schema before patching symptoms.

## Active

### [MUST][release][checker] v0.4.3.0 Generated-Burden Hotfix Closeout

- Problem: v0.4.3.0 now needs a release hotfix that distinguishes ordinary
  held-burden activation from genuine MRP-generated burden instantiation and
  normalizes public burden notation without claiming unrun hosted Smoke 7 proof.
- Source surfaces: `atomics/skill/SKILL.md`,
  `atomics/skill/references/tactics/TTP-MRP-mid-reread-pressure.md`,
  `atomics/skill/references/diagnostics/recursive-state-transitions.md`,
  and `atomics/skill/references/rubrics/diagnostic-render-contract.md`.
- Checker/fixture surfaces: `tools/check_mrp_generated_burden.py`,
  `tools/check_mid_reread_pressure.py`, `tools/check_mrp_route_invariants.py`,
  `tests/mrp-generated-burden/`, and
  `tests/smokes/mrp-behavior/prompts/smoke7-mrp-generated-downstream-burden.md`.
- Release boundary: deterministic fixtures/checkers prove the generated-burden
  distinction for this package refresh. A fresh hosted Smoke 7 model-output proof
  was not run and must not be claimed in release notes/body.
- Status: release hotfix authorized for v0.4.3.0 same-version asset refresh after
  deterministic checks, package validation, provenance preflight, tag alignment,
  and GitHub Release asset/body replacement pass.

### [MUST][checker][source] Current Canon Checker Anchors

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
- OODA/RACI: observe checker drift, orient against render canon, patch source/checker
  anchors as Responsible, and leave public render changes Accountable to the maintainer.
- Status: active checker anchor only; not a completed-work catalogue.

### [MUST][smoke][runtime] Manual Scriptless Compact DSL Behavioral Rerun

- Problem: the scriptless compact DSL hard moral-protest / worship-worthiness output previously shrank against the
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
- Remaining verification: manually rerun Claude scriptless compact DSL output on the hard moral-protest canary
  and compare against the v0.3.1.0 golden for diagnostic depth, visible
  per-burden Layer A re-entry, distinct TTP submoves, operative Qur'an/hadith
  formatting, source-function coverage before final restoration, identity/worldview
  restoration, no premature Stop-2 closure, family-local pressure preservation,
  and rhetorical/restorative force.
- RFC/ADR status: behavioral proof gate remains open until a retained live smoke
  artifact, matrix, and audit note explicitly close it.
- Status: active. Do not claim the behavioral regression fixed until this manual
  rerun passes.

### [MUST][smoke][decision][release] Register-Formalism Live Smoke / Hard Schema / Release Migration Decision

- Problem: schema-light register bridge semantics are now canonical in atomics,
  generated runtime text, and `tests/register-formalism-bridge-fixtures/`, with
  `tools/check_register_formalism_bridge.py` proving the derived registers against existing control
  effects rather than token presence alone. Fresh installed-skill hard smokes are now
  recorded; the remaining schema decision is whether to promote `heart` / `xi` / `Omega` /
  `mu` / `kappa` from derived analytic lenses into hard Diagnostic IR schema fields.
  The v0.4.0.0 contract/package/release-line migration is release-gated and separately
  authorized only when package-bound current-release smokes pass.
- Baseline wording: this is schema-light register bridge baseline over existing IR/control
  surfaces. `Derived/conditional bridge` remains only the schema-light boundary term; it is not
  future parity, compact DSL/IR runtime spine, or optional theory annex.
- Source surfaces: `docs/algebraic-notation-and-noetic-formalism.md`,
  `docs/register-formalism-implementation-ledger.md`,
  `atomics/skill/references/diagnostics/nomenclature-normalization.md`,
  `atomics/skill/references/diagnostics/diagnostic-ir.md`,
  `atomics/skill/references/diagnostics/recursive-state-transitions.md`,
  `atomics/skill/references/diagnostics/noetic-reading-checklist.md`,
  `atomics/skill/references/diagnostics/framework-pipeline.yaml`,
  `atomics/skill/references/rubrics/output-release.md`, and
  `atomics/skill/references/rubrics/diagnostic-render-contract.md`.
- Required verification already present for bridge behavior: positive and negative static
  fixtures proving that `heart` / `xi` / `Omega` / `mu` / `kappa`, `Delta-kappa`, terminal
  collapse formalism, Shannon-boundary discipline, and anti-symbol-theater behavior alter owner
  choice, hold/release, burden selection, reread, PARTIAL, or restoration instead of only
  appearing in governance prose.
- Live smoke verification now recorded: fresh installed-skill hard smokes for moral-protest/
  source-worldview, predication/attribute, and naturalist/scientistic canaries are recorded in
  `docs/audits/audit-history-pre-v0.4.1.mdcodex-smoke-test-findings.md` with retained ignored artifacts
  under `.daee/`.
- Required verification for hard-schema promotion: schema/checker updates, positive and negative
  fixtures, contract/interface migration across producers and consumers, register stress smoke
  after schema migration, and explicit contract/version migration.
- OODA/RACI: observe fixture/static/live smoke evidence, orient against the current release-line
  contract and package boundary, decide hard-schema/release-line authorization with the
  maintainer Accountable, then act only after approval. Consult atomics, generated runtime,
  bridge fixtures, smoke artifacts, and release docs.
- RFC/ADR status: derived/conditional bridge accepted for source/fixture governance;
  hard mandatory schema fields remain a separate ADR decision after v0.4.0.0 release-line migration.
- Status: user decision. Source/fixture/installed-skill smoke evidence supports
  v0.4.0.0 release consideration; the current release gate is authorized, but package rebake,
  tag, and release remain blocked until all v0.4.0.0 release checks and package-bound smokes pass.

### [SHOULD][source][fixture][checker] Operator Extraction Stage 1 Backlog

- Problem: the 30-file operator extraction audit found real under-factorization, but the correct
  implementation path is parent-owner child modes plus checker/fixture proof, not new owner packs
  or corpus ingestion.
- Stage 1 source surfaces: `atomics/skill/references/tactics/M9-predication-mode.md`,
  `tests/routing-fixtures/`, and
  `docs/audits/ns-ttp-meta-noetic-memetic-ontological-quantization-audit.md`.
- Stage 1 decision: M9 is the first owner because it already owns semantic reception, ta'wil
  sense-splitting, literal/figurative label discipline, loaded negative terms, imagination as
  entailment, and category/domain failure.
- Future stages: proof-method child modes under `proof-method-audit.md`; source-status child
  modes under existing source-status/inference/nomenclature owners; doubt/wiswas stop-hold modes
  under P7/doubt owners; divine action/speech/huduth modes under M9/V8/kalamic/do-attribute/
  sound-reason owners; MM/OQ register hardening only after owner-backed smokes prove a gap.
- Stage 3 adjacent source-status candidates intentionally remain TODO rather than runtime child
  modes until owner tracing proves they are needed: AS-1 source-prestige audit, AS-5
  scholar-error / position-error / public-use distinction, AS-6 testimony demotion / chain
  flattening audit, and AS-7 academic-method tribunal audit. Current AS work should stay under
  existing source-status / noetic-frame owners rather than becoming a broad AS pack.
- Stage 7 adjacent MM candidates intentionally remain TODO rather than runtime child modes until
  owner tracing proves they are needed: MM-1 slogan unpacking, MM-3 prestige-authority
  stabilization, MM-4 identity-cost / affiliation split, MM-6 semantic-default capture, MM-9
  reproduction-vector hold/release, and MM-10 public-obviousness / inherited-default audit.
  Current MM work should stay under `pattern-profiling.md` carrier/reproduction discipline
  rather than becoming a broad MM pack or argument bank.
- Stage 8 NS/register grammar follow-up remains TODO for checker design only: current static
  hardening documents unknown-pattern-typed fallback, compositional N/NS/PF/TTP/IR/register
  grammar, register-to-owner handoff, and child-family integration, but no checker yet enforces
  the whole compositional state across arbitrary outputs. Do not promote hard register schema
  fields or create release claims from this static grammar without explicit contract migration.
- Verification boundary: routing fixtures are static evidence only. They prove owner mapping and
  label-stripped generalization expectations; they are not live execution smokes.
- Stage-1.5/1.6 evidence boundary: retained local ignored M9 child-mode outputs under
  `.daee/stage1.5-m9-child-live-smokes-20260514/` are semantic local evidence, not
  package/release smoke proof. They are now machine-checkable by
  `tools/check_m9_child_mode_execution_samples.py`, which validates child-specific target,
  operation, result, Land(B), R(H,Delta), held/released routes, and anti-label-only safeguards.
  `tools/check_smoke_artifacts.py --root` remains intentionally package/provenance oriented and
  does not accept those local artifacts without release-style sidecars.
- Status: Stage 1 source/fixture patch staged with static verification; Stage-1.6 local checker
  added for M9 child-mode execution samples; package, tag, push, and release remain out of scope.

### [SHOULD][release][package][decision] Release Asset Rebake Decision

- Problem: current dirty work after the `v0.4.0.0` tag is `v0.4.1.0` candidate
  cleanup/hardening work. It changes governance, CI, audit, and generated-runtime
  surfaces, but does not authorize a new package, tag, release, or GitHub Release
  asset.
- Source surfaces: `atomics/skill/`, `tools/`, `tests`, `.github/workflows/`,
  release docs, and audit docs.
- Runtime surfaces: generated `skill/`.
- Remaining verification: if the user authorizes a release asset refresh, run the
  package workflow, update release-artifact docs and smoke/package SHA guards,
  replace the existing GitHub Release asset, download it back, and verify SHA.
- RFC/ADR status: pending maintainer release authorization; package rebake is not implied
  by source verification or git push.
- Status: active only if release rebake is authorized. Do not tag, push, package,
  or update GitHub Release from this TODO alone. Keep operative `contract_version`
  at `0.4.0.0` unless the maintainer explicitly requests a release-line migration.

### [COULD][package][decision] Optional Harness Dev Artifact Decision

- Problem: the canonical user-facing package shape now excludes the optional
  route/check harness roots (`data/`, `scripts/`, `tests/`), restoring the
  scriptless compact-DSL package boundary while keeping harness source in the repo
  for maintainer validation. Some harness files still carry historical `level3`
  / `daee_level3` names.
- Future patch surface: design a separate dev/script-harness artifact only if the
  user explicitly authorizes publishing Codex/CI harness machinery as a second
  artifact. Tracked repo-side harness roots that remain for now are
  `atomics/skill/data/`, `atomics/skill/scripts/`, `atomics/skill/tests/`,
  and their generated `skill/data/`, `skill/scripts/`, `skill/tests/` views.
  They are excluded from the canonical package selector; deletion or branch
  extraction is a separate repo-history/dev-artifact decision. A future rename to
  `runtime-harness`, `route-check-harness`, or similar should migrate atomics,
  generated runtime, docs, CI, and checker names together rather than piecemeal.
- MoSCoW/RACI: Could; Responsible patching agent drafts only if requested, and
  Accountable maintainer decides whether a second dev artifact exists.
- Status: future artifact-profile decision. Do not create a dev artifact, tag,
  package, or release from this TODO alone.

### [CLOSED][docs][decision] Audit Report Tracking Decision

- Resolution: v0.4.1.0 docs consolidation archives historical audit surfaces under
  `docs/audits/audit-history-*.md` and indexes them through `docs/audits/INDEX.md`.
- Source surfaces: `docs/audits/audit-history-v0.3.md`,
  `docs/audits/audit-history-v0.4.0.0.md`, and `docs/audits/audit-history-pre-v0.4.1.md`.
- Status: closed for current cleanup. Future retention deletion still requires explicit
  maintainer approval.

### [SHOULD][coverage][decision] Coverage Scope Owner Review Anchors

#### [SHOULD][checker][fixture] Optional script-harness family/transmission coverage expansion

- Problem: RC4 regression findings for testimony/transmission/tawatur and
  Ash'ari/Maturidi family-variant kalam pressure have optional script-harness
  analogues, but the current covered-scope script-harness catalogue does not include dedicated
  testimony/transmission or family-variant owners. This pass added generic
  source-function leakage checks and non-TST pressure fixtures, but it did not
  add broad new owners outside the covered scope.
- Source surfaces: `atomics/skill/data/module-catalogue.json`,
  `atomics/skill/data/trigger-matrix.json`,
  `atomics/skill/references/diagnostics/coverage-scope.yaml`, and the relevant
  transmission/family owner source files if later authorized. Current script-harness
  checker coverage now rejects generic pressure-token lists for covered owners,
  but that does not create missing family/transmission owner coverage.
- Checker/runtime surfaces: `atomics/skill/scripts/route.py`,
  `atomics/skill/scripts/check_execution.py`,
  `atomics/skill/tests/fixtures/`, generated `skill/`, and routing parity
  fixtures under `tests/routing-fixtures/`.
- Remaining verification: decide whether to expand script-harness covered scope with
  owner-file-faithful transmission/testimony/tawatur and family-variant kalam
  owners, or keep those as scriptless governance plus routing-parity coverage.
- MoSCoW/RACI: Should if optional harness parity is claimed; Could otherwise.
  Accountable maintainer decides covered-scope expansion before implementation.
- Status: future coverage / user decision. Do not imply the optional script harness fully covers
  these families until dedicated owners and fixtures exist.

#### [COULD][checker][fixture] Optional script-harness catalogue-wide non-covered owner expansion

- Problem: the full runtime catalogue contains many scriptless-governed owners,
  profiles, diagnostics, and auxiliary TTPs that are not executable optional script-harness
  route/check owners in v0.3.2.0. Current script-harness coverage is intentionally
  limited to the fixture-backed covered-scope owners in
  `atomics/skill/data/module-catalogue.json`.
- Scriptless status: covered by compact DSL governance, routing parity,
  render/recursive checks, and owner source files. Active owners still must
  execute Target/Operation/Result, pressure the case-specific burden, land,
  and pass state/noetic re-read.
- Optional script-harness status by family:
  - Evidence/fitrah/attention owners not executable in the script harness yet:
    `E1-broadening-evidence`, `E2-inferential-criterion`,
    `E3-cumulative-case`, `E4-cross-cultural-check`, `M2-prior-probability`,
    `M3-orphaned-intuition`, `R1-internalist-criterion`,
    `R2-the-reminder`, `R3-warranted-basic-belief`,
    `V5-directing-attention-signs`, `V6-convergence`,
    `husn-al-nazar-arguments`, and `inductive-fitri-method`.
  - Definition, logic, doubt, taqlid, contamination, and maieutic owners not
    executable in the script harness yet: `M1P-performative-self-refutation`,
    `M6-excluded-middle`, `M7-definition-anchor`,
    `doubt-vs-skepticism`, `symmetric-taqlid-check`,
    `F1-supra-vs-antirational`, `F2-volitional-dimensions`,
    `F3-practice-epistemic-access`, `V3-regress-dissolution`,
    `V4-contamination-identification`, `V7-taqlid-check`,
    `V11-taqlid-transition`, `V12-tamanuc-exhaustion`,
    `P2-objection-mapping`, `P4-maieutic`, and
    `P5-already-believing`.
  - Transmission/authentication owners not executable in the script harness yet:
    `revelation-transmission`, `V10-transmission-content-vetting`, and
    `hadith-authentication-epistemology`.
  - Kalam/family/proof-method and philosophical-frame owners not executable
    in the script harness yet: `kalamic-interlocutor`, `proof-method-audit`,
    `philosophical-usurpation`, `P3-reason-revelation-tension`,
    `P6-universal-aqidah-principle`, `ns-6-kalamic-evidentialist`,
    and `ns-10-maturidi-evidentialist`.
  - Noetic-profile and broad case-library modules not executable as script-harness
    owners yet: `do-core`, `noetic-profiles`, `ns-1-naturalist`,
    `ns-2-agnostic-evidentialist`, `ns-3-deconverted`,
    `ns-4-secular-moral-realist`, `ns-5-habituated-atheist`,
    `ns-7-theistic-evidentialist`, `ns-8-muslim-internal-crisis`,
    `ns-9-historical-critical-skeptic`, `ns-11-fideist-reformed`,
    and `ns-12-blank-slate-dual-fitrah`.
  - Diagnostic/governance surfaces such as `definition-discipline`,
    `causal-series-taxonomy`, `perfection-criterion-usurpation`,
    `prophetic-discourse-neutralization`, `reason-disambiguation`,
    `pattern-profiling`, and `mixed-case-handling` govern scriptless compact DSL output and
    routing parity but are not direct script-harness owner routes unless promoted
    by an explicit covered-scope design.
- Exact blocker: each family needs owner-file-faithful script-harness extractor
  features, trigger-matrix rules, pressure dimensions, expected fixtures,
  negative compression fixtures, and check-execution gates. Adding these
  casually would broaden the executable script-harness claim beyond the covered scope.
- Future file/data/check needed: extend `atomics/skill/data/module-catalogue.json`,
  `atomics/skill/data/trigger-matrix.json`, `atomics/skill/scripts/diagnose.py`,
  `atomics/skill/tests/fixtures/`, `atomics/skill/tests/expected/`,
  `atomics/skill/scripts/check_execution.py`, and generated `skill/` for each
  authorized owner family.
- RFC/ADR status: deferred covered-scope expansion; each family needs its own accepted
  mini-ADR before executable script-harness claims broaden.
- Status: future coverage / user decision. This is not a release blocker as
  long as docs and release claims say these owners are scriptless-governed or
  routing-parity covered, not executable script-harness covered-scope owners.

#### [COULD][coverage][decision] Bespoke religion-specific source-content owners

- Problem: coverage-scope claims for Buddhist, Hindu, Jewish, and similar
  source-content cases are intentionally marked needs-review/out-of-scope rather
  than packaged runtime owners.
- Source surfaces: `atomics/skill/references/diagnostics/coverage-scope.yaml`.
- Checker/runtime surfaces: `tools/check_coverage.py`, generated coverage report.
- Remaining verification: decide whether to add owner-file-faithful source-content
  owners in a later release line, keep them out of scope, or add narrower hold
  rules without pretending coverage exists.
- MoSCoW: Could for a later release line; Won't for current release claims unless
  explicitly authorized.
- Status: active review anchor for coverage integrity.

#### [COULD][coverage][decision] Sufism-related source-content adjudication

- Problem: Sufism/tariqah authority and contested-practice cases require
  careful owner design before being treated as covered runtime source-content.
- Source surfaces: `atomics/skill/references/diagnostics/coverage-scope.yaml`.
- Checker/runtime surfaces: `tools/check_coverage.py`, generated coverage report.
- Remaining verification: decide whether to add specific adjudication owners,
  keep the cases out of scope, or document a narrower source-status hold rule.
- MoSCoW: Could for a later release line; Won't for current release claims unless
  explicitly authorized.
- Status: active review anchor for coverage integrity.

## Closed In Current Working Tree

The v0.3.2.0 systemic hardening closure report catalogues every reported audit
item and maps each to patched, partial, deferred, rejected, or user-decision
status:

```text
docs/audits/audit-history-v0.3.mdv0.3.2.0-systemic-hardening-closure.md
```

Do not use this closed list as release proof. It records source/checker/runtime
hardening only; live scriptless compact DSL behavior remains gated by the manual rerun above.

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
