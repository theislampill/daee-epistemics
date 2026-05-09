# TODO

This file tracks unresolved future work after the compiled-runtime migration.

Current layout:

```text
atomics/skill/          = canonical atomized editable source
skill/                  = generated compiled Claude package root
tools/                  = compiler/checker scripts
tests/routing-fixtures/ = static routing parity fixtures
docs/                   = architecture, audit, and workflow notes
```

Completed historical gaps, coverage passes, routing parity work, and recursive traversal governance are summarized in `CHANGELOG.md`. They are not duplicated here as active TODOs.

## Active

No active unresolved release-blocking technical pass is currently assigned.

Before claiming behavioral recovery of the Level 1/2 TST-style regression, run a
manual Claude Level 1/2 rerun and compare it against the v0.3.1.0 golden for
diagnostic depth, recursive per-burden Layer A re-entry, distinct TTP submoves,
operative Qurʾān/ḥadīth deployment, and restorative force. The current repo
state only claims spec-side hardening.

## Completed Mainline Audit Patch Catalogue (post-v0.3.1.0)

- v0.3.2.0 Level 3 executable routing adds an additive route-first path for
  Codex-capable script runtimes: span-backed feature extraction, deterministic
  routing given features, reconstruction/validation checks, execution checking,
  continuation_queue traversal, and stable fixture tests. It does not claim
  deterministic feature extraction, pure-Hermes parity, codons, owner packs, or
  guaranteed transformer execution.
- v0.3.2.0 recursive render hardening clarifies that compact governance means
  concise richness rather than thinness, requires per-burden Layer A re-entry in
  hard/compound/deformed recursive cases, treats `R(H,Delta)` as a real
  state-transition judgment, and keeps Level 3 `continuation_queue` traversal
  conditional on state re-read.
- v0.3.2.0 final spec-side hardening prevents active TTP/operator submove
  consolidation, preserves distinct `Target -> Operation -> Result` execution,
  tightens Qurʾān/ḥadīth operative formatting, normalizes kalām and
  source-status terminology, and records durable release-cycle protocol in
  `AGENTS.md`.
- v0.3.2.0 package metadata hardening keeps the `SKILL.md` description within
  the 1024-character host limit and checks that limit in both frontmatter
  validation and package construction.
- v0.3.2.0 nomenclature normalization records canonical noetic-state, DSL/IR,
  Level 3, TTP/owner/operator, and transliteration names under
  `references/diagnostics/nomenclature-normalization.md`.
- v0.3.2.0 operator strengthening sharpened existing reason/revelation,
  attribute-predication, and noetic-restoration owners with compact floors,
  minimal-pair fixture expectations, source_basis discipline, and render
  restrictions while keeping runtime output source-neutral.
- Diagnostic IR ghost-load/source-basis enforcement is checker-backed by
  `tools/check_ir_instance_integrity.py` and
  `tools/check_diagnostic_ir_catalogue_integrity.py`.
- Runtime-grounding smoke artifacts are canonical at repo-local
  `smokes/runtime-grounding-v5/`; release traces/verdicts carry package/hash/run provenance, and
  `tools/check_smoke_artifacts.py` rejects unmarked drift from `docs/release-artifacts.md`.
- Package naming is split deliberately: `package.ps1` emits a checked local `.skill.zip` RC archive,
  while host uploads that require `.skill` may use the same payload renamed to `daee-epistemics.skill`.

## Completed Metaaudit Repair Catalogue (2026-05-02)

The repo-local metaaudit report found the skill partially compliant: the
diagnostic compiler existed, but default output risked hiding too much governance behind
`:audit` or a prose-only default. This pass catalogued and closed the reported risks as follows:

- Diagnostic reduction, IR formation, IR validation, and six-check gate visibility were
  too easy to assert invisibly in default mode. Closed by making the default compact
  DSL/IR header mandatory and checker-enforced while keeping raw Diagnostic IR,
  full Case State, `matched_modules`, and route ledger out of default output.
- The public `:audit` split risked making default too bare. Closed by deprecating
  `:audit` as public output and retaining it only as internal/development audit
  compatibility; `:dsl` remains the concise IR/lab-report mode.
- Routing precedence and TTP entry were only partially auditable. Closed by requiring
  the current bounded operator to be one burden-level function and by adding operation
  criteria that reject route chains, TTP labels, and generic `Operation:` prose.
- Operative submoves could be syntactic dressing. Closed by requiring `Operation:`
  lines to begin with the existing closed operative verbs and adding structural checker
  samples for non-operative operation verbs.
- Source-status labels could be emitted while contrast material silently became a
  premise. Closed by strengthening the operative-warrant sentence with a specific
  non-premise clause and adding checker coverage.
- Held routes could leak semantically into Layer B. Closed by requiring explicit
  `Released: <item>` / equivalent release markers before held material can be answered,
  plus structural checker coverage for held-route semantic leakage.
- Topic-to-IR fingerprinting remained possible with the two-fixture hiddenness pair.
  Closed by adding a third same-vocabulary Muslim-internal authority-fatigue fixture and
  extending routing parity checks so the minimal-pair triangle diverges on existing
  discriminators: concealment mode, DO-orient, restoration target, or routing gate.
- Grounded state/noetic re-read, STOP/HOLD/PARTIAL/RECURSE, and Layer A/B release
  discipline were preserved and tied to the new false-compliance guards.

No new IR fields, route IDs, PF codes, owners, or architecture were introduced.

## Post-v0.3.2.0 Candidates

### Live model regression testing
- Manually rerun the Level 1/2 TST-style case in Claude before claiming behavioral
  recovery from the v0.3.2.0 thinning regression.
- Build a small live-run suite that compares actual Claude outputs against the static routing fixtures.
- Track whether outputs preserve Diagnostic IR, matched original module IDs, post-render gate discipline, and recursive traversal decisions.
- Track default-vs-DSL-vs-audit render behavior: default should expose the compact DSL/IR header plus bounded governed Layer B (Hidden Premises, local Core Formulation, bounded operative submoves, compact TTP/operator trace when used), then state/noetic re-read, one Restorative Response, and one final Closing Formulation without becoming a giant ledger or essay-only output; `:dsl` should expose concise DSL/IR or lab-report state; `:audit` should remain internal/development-only compatibility rather than public governance visibility.
- Do not treat static routing parity as live behavioral equivalence.

### Broader routing fixture coverage
- Add fixtures for more mixed higher-order cases, comparative-religion structural transfers, grief-primary cases, ḥadīth cases, and thin-basis ambiguity.
- Keep fixture expectations structural: module IDs, governance phrases, path resolution, and call budgets, not exact prose.

### Recursive traversal fixtures
- Add focused fixtures for same-input multi-burden traversal, newly eligible held routes, HOLD because release signal is absent, and PARTIAL because limits block the next eligible burden-cycle.
- Preserve the rule that recursion is one governed burden-cycle at a time, not argument dumping.

### File-call telemetry
- Consider optional telemetry or manual audit notes for actual runtime file-call counts in live hosts.
- Keep modeled call-budget checks as the deterministic baseline.

### Packaging automation
- Polish release packaging into one command that rebuilds, runs all checkers, packages `skill/` contents, verifies archive root, and prints checksum.
- Keep the current rule: package the contents of `skill/`, not the `skill/` directory.

### CI integration
- Add a CI job for the compiler/checker suite if repository automation is desired.
- Include `tools/check_routing_parity.py --strict`, `tools/check_recursive_traversal_governance.py`,
  `tools/check_recursion_collapse_noetic_frame.py`, and
  `tools/check_metacompliance_current_canon.py`.

### Release artifact checksum policy
- Decide whether release artifacts should publish SHA256 checksums, signatures, both, or neither.
- Keep `build/` as an optional local output directory unless the project decides to commit release artifacts.

## Closed Scope Decisions

### Bespoke religion-specific source-content owners
- Status: closed / out of scope for v0.3.1.0.
- Decision: do not add bespoke Jewish, Hindu Arya Samaj, Advaita, Buddhist, Sufi, tariqah-specific, or other tradition-specific source-content owners without a later authorized coverage task.
- Existing coverage is structural. The skill may route authority-order, criterion, semantic, category-set, transmission, and register cases through existing owners, but it must not claim bespoke source-content adjudication.

### Sufism-related source-content adjudication
- Status: closed / out of scope. No bespoke Sufism, tariqah-authority, or contested-practices source-content owner is authorized.
- Cases involving Sufism-contested-practices or Sufism-tariqah-authority-claims may route through existing family-transfer and structural pattern owners only.
- Do not add bespoke Sufism owners without an authorized coverage task.

### Generated runtime as source
- Status: closed / prohibited.
- Decision: `skill/` is generated runtime output. Edit `atomics/skill/`, rebuild, and run the checker suite.
- Do not hand-edit generated runtime files, do not treat omnibus bundles as canonical source, and do not use omnibus filenames as `matched_modules`.
