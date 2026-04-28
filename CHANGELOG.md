# Changelog

## [v0.3.0.0] - 2026-04-28

v0.3.0.0 is the compiled runtime architecture release.

### Added

- Compiler/checker toolchain for generated runtime builds, freshness checks, module-boundary checks, source/stub integrity, call-budget modeling, routing parity, path resolution, and recursive traversal governance.
- Generated compiled Claude runtime package root under `skill/`.
- Static routing parity fixtures under `tests/routing-fixtures/`.
- Compiled runtime path-resolution checks for inherited atomized paths in generated `skill/SKILL.md`.
- Sub-20 normal case-class call-budget checker.
- Root `AGENTS.md` contributor guide for source/runtime workflow.
- Recursive traversal governance: State Refresh after bounded moves, no premature STOP while an eligible live door remains, HOLD/PARTIAL/RECURSE discipline, and recursion-as-one-door-at-a-time.
- Render-mode checker for clean default mode, compact DSL/lab-report mode, fuller audit mode, and grim-reaper prompt deprecation.

### Changed

- Canonical atomized source moved to `atomics/skill/`.
- `skill/` is now generated compiled Claude package root, not the canonical editable source tree.
- Claude packaging now packages the contents of `skill/`, so `SKILL.md` is at archive root.
- Runtime uses five core runtime bundles plus selective omnibus bundles and `compiled-module-map.json` for path/module resolution.
- README, TODO, and architecture docs now describe the source/runtime split.
- Render behavior is clarified: `/daee-epistemics` is clean prose-first, `/daee-epistemics:dsl` is compact diagnostic/lab-report mode, and `/daee-epistemics:audit` is fuller procedural audit mode.

### Preserved

- Original module IDs.
- YAML operative contracts in atomized source.
- Diagnostic IR discipline.
- Source-basis traceability.
- P7 STOP/HOLD/RECURSE/PARTIAL discipline.
- Atomized source authority under `atomics/skill/`.

### Not asserted

- Exact prose parity.
- Live model behavioral equivalence beyond static routing parity and static recursive-governance checks.

### Validation

- `python tools/build_compiled_runtime.py` - PASS
- `python tools/check_compiled_runtime_freshness.py` - PASS
- `python tools/check_compiled_module_boundaries.py` - PASS
- `python tools/check_stub_integrity.py` - PASS
- `python tools/check_consolidation_call_budget.py` - PASS
- `python tools/check_routing_parity.py` - PASS
- `python tools/check_routing_parity.py --strict` - PASS
- `python tools/check_recursive_traversal_governance.py` - PASS
- `python tools/check_render_modes.py` - PASS

## [v0.2.3.0] - 2026-04-26

v0.2.3.0 is the post-render recursion governance release after v0.2.2.0.

### Added

- Mandatory Diagnostic IR `post_render_gate` with `cleared_this_pass`, `remaining_live_distortions`, `held_routes_rechecked`, `newly_released_routes`, `next_eligible_pass`, and `recursion_decision`.
- Four-state post-render decision vocabulary: `STOP`, `HOLD`, `RECURSE`, and `PARTIAL`.
- Named anti-pattern `Premature Closure Without Re-Entry` for responses that land one strong move and stop without refreshing case-state or reassessing held material.
- Output-release failure test for false closure after an imported-tribunal move when a positive criterion-order pass remains eligible.
- Development validator `tools/check_framework_pipeline.py` to check the framework-pipeline ASCII audit chart against `SKILL.md`, YAML front matter, `module-catalogue.json`, `coverage-scope.yaml`, mandatory-pass order, forbidden shortcuts, and recursive state vocabulary.

### Changed

- `diagnostic-ir.schema.json` now makes `post_render_gate` schema-visible and required for a completed governed pass record.
- `diagnostic-ir.md`, `framework-pipeline.md`, `case-state-schema.md`, `diagnostic-render-contract.md`, `output-release.md`, `P7-restoration-stops.md`, and `heuristics.md` now require the post-render State Refresh / Re-Entry Gate before closure.
- Render governance now requires either a visible `[Post-Render Gate]` or compact `[Final Governance]` block naming the recursion decision and next eligible pass.
- P7 and output-release rules now distinguish blocked live material (`HOLD`), required same-input continuation (`RECURSE`), and limit-bounded incomplete traversal (`PARTIAL`).
- `contract_version` markers updated to `0.2.3.0` for the current packaged reference surface.

### Fixed

- Prevented false STOP after one strong bounded move when same-input distortions or newly eligible held routes remain live.
- Prevented token/tool/interaction limits from being represented as completion; such cases now require `PARTIAL`.
- Updated public orientation text so the README reflects the current STOP / HOLD / RECURSE / PARTIAL pass model.

### Removed

- No files were consolidated, no runtime/omnibus files were generated, and no canonical atomic source files were replaced.

### Validation

- `python tools/check_frontmatter.py` - PASS
- `python tools/check_coverage.py` - PASS
- `python tools/check_framework_pipeline.py` - PASS
- `python -m json.tool skill/references/diagnostics/diagnostic-ir.schema.json` - PASS
- `python -m json.tool skill/references/diagnostics/operative-contract.schema.json` - PASS
- `python -m json.tool skill/references/diagnostics/module-catalogue.json` - PASS

### Scope Boundaries

- No new bespoke religion-specific owner files were created.
- No new public coverage claims were added.
- Diagnostic IR remains the runtime dispatch authority; YAML/front matter and development validators remain validation surfaces, not live routing engines.
- Canonical source remains atomized under `skill/references/`; future bundles may be added separately without replacing canonical source ownership.

## [v0.2.2.0] - 2026-04-26

v0.2.2.0 is the stabilization, packaging, and validation release after v0.2.1.0.

### Added

- Optional Diagnostic IR fields for structural pattern print, load-bearing node, collapse radius, intervention target, and framing notes.
- Source-audit-derived structural framing support for DO-15 moral objections, Sufi kashf/tariqah authority, Jewish Torah-completeness, Arya Samaj critique, Advaita pressure, and Buddhist anatta/impermanence pressure.
- Pattern-first validation notes that route source-audit-derived topics through existing Diagnostic IR owners instead of treating them as new coverage sources.
- Anti-pattern coverage for argument-bank/citation-dump substitution, tradition-label routing, abuse-doctrine collapse, and pattern theater.

### Changed

- YAML front matter normalized as the single packaged metadata regime for reference files.
- Desired verification metadata preserved in headers: `verification_status`, `direct_read_verified`, `failure_conditions_present`, `ir_consequences_present`, `minimal_pairs_present`, `hold_release_rules_present`, `compiled_runtime_eligible`, and `operator_pack_eligible`.
- Runtime metadata expressed through `load_when`, `routing_effects`, `emits`, `blocks`, `companions`, `output_shapes`, `p7_stops_governed`, `layer_constraint`, and `catalogue_registered`.
- `framework-pipeline.md` normalized under the current metadata regime.
- Validators aligned with the current operative-contract model, including verification-aware front matter and legacy-blockquote rejection.
- `contract_version` markers updated to `0.2.2.0` for the current normalized packaged reference surface.

### Fixed

- Stale version prose that treated the completed v0.2.2.0 release set as `v0.2.1.0` or earlier pre-release work.
- Stale local/scratch path references and repo-facing task-log wording from earlier hygiene passes.
- Duplicate metadata systems in Markdown reference files.
- Source-audit framing paths that could otherwise invite prooftext dumping, citation-bank behavior, or tradition-label routing.

### Removed

- Manual coverage-ledger behavior as current authority; the old ledger is retained only as a retired tombstone.
- Legacy post-frontmatter blockquote metadata blocks such as `> role:`, `> use when:`, `> do not use when:`, and `> output:`.
- Repo-facing progress/changelog/task prose outside the canonical audit/future-work surfaces.

### Validation

- `python tools/check_frontmatter.py` - PASS
- `python tools/check_coverage.py` - PASS
- `python -m json.tool skill/references/diagnostics/diagnostic-ir.schema.json` - PASS
- `python -m json.tool skill/references/diagnostics/operative-contract.schema.json` - PASS
- Bundle compiler smoke tests - not applicable; no bundle compiler or packaged context-bundle support exists in this release.

### Scope Boundaries

- No new bespoke religion-specific owner files were created.
- No new public coverage claims were added from source-audit material.
- Bespoke religion-specific source-content owners are out of scope for v0.2.2.0 because no authorized primary/source-audit basis is available.
- Existing family-transfer and Diagnostic IR architecture remains sufficient for structural response handling when the live burden instantiates a governed route.
- Jewish, Sufism, Hindu Arya Samaj, Advaita, and Buddhist cases may be handled only at the governed structural level unless a dedicated source-content owner is later authorized and added.
- Canonical source remains atomized files under `skill/references/`.
- No consolidation or bundle/read-view system is shipped in v0.2.2.0; future packaging bundles may be added separately without replacing canonical source ownership.
