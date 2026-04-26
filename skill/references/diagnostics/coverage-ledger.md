---
id: coverage-ledger
module_class: governance
canonical_path: skill/references/diagnostics/coverage-ledger.md
contract_version: "0.2.2.0"
load_when:
  - historical coverage-ledger references need redirecting
catalogue_registered: false
---

# Coverage Ledger — Retired

This manual parity ledger has been retired.

Do not use this file as the source of truth for current coverage.

Runtime coverage and scope in the packaged skill are now represented by:

- `skill/SKILL.md`
- module front matter
- `skill/references/diagnostics/module-catalogue.json`
- relevant `INDEX.md` routing files
- explicit scope notes in the relevant owner/router files
- `TODO.md` for unresolved human scope/source decisions

Repository validators in `/tools/` may check these files during development, but `/tools/`
is not packaged into the skill and is not runtime authority.

Historical ledger details are available in git history.
