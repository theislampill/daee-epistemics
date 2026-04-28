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

## Post-v0.3.0.0 Candidates

### Live model regression testing
- Build a small live-run suite that compares actual Claude outputs against the static routing fixtures.
- Track whether outputs preserve Diagnostic IR, matched original module IDs, post-render gate discipline, and recursive traversal decisions.
- Track default-vs-DSL-vs-audit render behavior: default should not become a giant ledger; `:dsl` should expose compact diagnostic state; `:audit` should expose fuller procedure only when invoked.
- Do not treat static routing parity as live behavioral equivalence.

### Broader routing fixture coverage
- Add fixtures for more mixed higher-order cases, comparative-religion structural transfers, grief-primary cases, hadith cases, and thin-basis ambiguity.
- Keep fixture expectations structural: module IDs, governance phrases, path resolution, and call budgets, not exact prose.

### Recursive traversal fixtures
- Add focused fixtures for same-input multi-door traversal, newly eligible held routes, HOLD because release signal is absent, and PARTIAL because limits block the next eligible pass.
- Preserve the rule that recursion is one governed door at a time, not argument dumping.

### File-call telemetry
- Consider optional telemetry or manual audit notes for actual runtime file-call counts in live hosts.
- Keep modeled call-budget checks as the deterministic baseline.

### Packaging automation
- Polish release packaging into one command that rebuilds, runs all checkers, packages `skill/` contents, verifies archive root, and prints checksum.
- Keep the current rule: package the contents of `skill/`, not the `skill/` directory.

### CI integration
- Add a CI job for the compiler/checker suite if repository automation is desired.
- Include `tools/check_routing_parity.py --strict` and `tools/check_recursive_traversal_governance.py`.

### Release artifact checksum policy
- Decide whether release artifacts should publish SHA256 checksums, signatures, both, or neither.
- Keep `build/` as an optional local output directory unless the project decides to commit release artifacts.

## Closed Scope Decisions

### Bespoke religion-specific source-content owners
- Status: closed / out of scope for v0.3.0.0.
- Decision: do not add bespoke Jewish, Hindu Arya Samaj, Advaita, Buddhist, Sufi, tariqah-specific, or other tradition-specific source-content owners without a later authorized source-audit task.
- Existing coverage is structural. The skill may route authority-order, criterion, semantic, category-set, transmission, and register cases through existing owners, but it must not claim bespoke source-content adjudication.

### Generated runtime as source
- Status: closed / prohibited.
- Decision: `skill/` is generated runtime output. Edit `atomics/skill/`, rebuild, and run the checker suite.
- Do not hand-edit generated runtime files, do not treat omnibus bundles as canonical source, and do not use omnibus filenames as `matched_modules`.
