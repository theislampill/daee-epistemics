# Changelog

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
- Bespoke Jewish, Sufism, Hindu Arya Samaj, Advaita, and Buddhist owner work remains scope-gated / needs-review unless separately authorized.
- Canonical source remains atomized files under `skill/references/`.
- No consolidation or bundle/read-view system is shipped in v0.2.2.0; future packaging bundles may be added separately without replacing canonical source ownership.
