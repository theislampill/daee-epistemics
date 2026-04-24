# Changelog — daee-epistemics

## v0.2.0.0

### Added

- **Output-release rubric** (`skill/references/rubrics/output-release.md`): Runtime governance rubric with 9 pass/fail checks and 16 failure tests governing what may be released after the dispatch gate opens, in what order, and under what case-state constraints. Covers: governing burden identification, upstream blocker clearing, held-material reassessment, recursive traversal discipline, Layer B bounding, stop/hold/recurse decision, and diagnostic render eligibility.

- **Diagnostic render contract** (`skill/references/rubrics/diagnostic-render-contract.md`): 3-level render contract — Level 1 (ordinary bounded response), Level 2 (compact diagnostic / lab-report), Level 3 (full diagnostic / audit render). Governs visible render shape after the output-release rubric passes; does not determine routing.

- **Machine-readable operative contract architecture** (`skill/references/diagnostics/operative-contracts.md`): Architecture spec defining per-file YAML front matter contracts — purpose, required/optional keys, allowed values, examples by module class, failure modes, migration strategy, and linting plan. Operational value: static discoverability and auditability. Agents and lint tools can identify which modules declare load conditions, companions, emitted fields, blocked moves, and catalogue bindings before runtime routing activates them. Complex cases (Trinitarian, kalāmic, atheist, secular, attribute, proof-method, mixed higher-order) can expose a wider selectively routed candidate field without making modules ambient always-load.

- **Operative contract JSON schema** (`skill/references/diagnostics/operative-contract.schema.json`): JSON Schema (Draft 2020-12) for YAML front matter. Required: `id`, `module_class`, `canonical_path`, `contract_version`. Optional: `load_when`, `routing_effects`, `emits`, `blocks`, `companions`, `output_shapes`, `p7_stops_governed`, `layer_constraint`, `catalogue_registered`. `module_class` includes `governance` for non-catalogue framework/meta files. `additionalProperties: false`.

- **Pilot YAML operative contracts** on 4 representative files:
  - `skill/references/tactics/M9-predication-mode.md` — tactic; semantic-gate routing effects; companions: definition-discipline, do-attribute-precision
  - `skill/references/procedures/P7-restoration-stops.md` — procedure; all 5 stops declared; `layer_constraint: layer-b-governed`
  - `skill/references/diagnostics/routing-precedence.md` — governance; `catalogue_registered: false`; suppression rules S-1 through S-7 declared
  - `skill/references/case-library/do-attribute-precision.md` — case-library; 3 companions declared; DO-6/11/12/13 load conditions

- **PF atomization and routing-surface architecture**: DO family (do-core.md, do-second-loop.md, do-christian-extensions.md) converted to family routing surfaces with load floors, TTP fan-out tables, 9-subsection structural headers, and under-load guards. `do-attribute-precision.md`: Three-Layer Owner Distinction, Current-Pass/Held Distinction, Failure Tests. `philosophical-usurpation.md`: Peer-File Routing Integration. `case-library/INDEX.md`: DO-Family Routing Architecture section. `terminology.md §Route-Critical Worship Terms`: `ilāh` / `Allāh` / false-`ilāh` distinction expanded. `pattern-profiling.md`: PF-6 generalized to structural divine-plurality / worship-status coherence pressure pattern (cross-tradition); PF-7 renamed to Prophetic credential / authority-ordering challenge.

- **SKILL.md additions**: Rule 14 (ghost-load prohibition), Rule 15 (traversal-delayed; same-response recursion bounded by P7), Rule 8 in Named Routing Constraints (no held-as-never-answer), Output-Release Governance table, Per-File Operative Contracts table.

- **6 new anti-patterns** (total now 22): Held-but-Answered Contradiction, Held-as-Never-Answer, State-Refresh-as-User-Reply-Only, Recursive Dump, Fixed Full-Field Template Materialization, Template-Driven Routing.

### Clarified

- **Held downstream material is traversal-delayed, not response-delayed.** After a governing blocker is cleared, the system reassesses held downstream material and proceeds to the next bounded pass if the refreshed state permits — without requiring a new user reply. (`P7-restoration-stops.md` preamble rider; `SKILL.md` Rule 15; `routing-precedence.md` §VII; `framework-pipeline.md` forbidden shortcut paths)

- **State refresh is an internal operation.** It may occur inside the same response when the current pass has cleared the governing blocker and the next live burden is now eligible.

- **The diagnostic IR remains the canonical runtime dispatch gate.** Operative contracts declare static per-file metadata; they do not activate modules, substitute for the IR, or create a second catalogue.

- **Operative front matter is for machine parsing.** The YAML block is not runtime output and must not appear in Layer B responses. Human-readable prose below remains authoritative for judgment.

- **routing-precedence.md §VII** added: routing precedence (owner order) vs. output-release rubric (release amount/order) vs. diagnostic render contract (visible structure) are three distinct governance layers.

- **framework-pipeline.md** extended: OUTPUT-RELEASE RUBRIC and DIAGNOSTIC RENDER CONTRACT blocks added to ASCII pipeline chart; 4 new forbidden shortcut paths; compact pipeline expression added.

### Not Changed

- No module-catalogue.json shape migration (catalogue shape: `id`, `path`, `module_class` — unchanged).
- No replacement of diagnostic IR.
- No global always-load expansion.
- No new case families or ontology.
- No routing discipline weakened (output-release rubric and P7 stop discipline additive, not subtractive).
- Companion modules in operative contracts are not automatically active; diagnostic IR still decides current-pass activation.

---

## v0.1.4.1

Ghost-load prohibition: Rule 14 added to `SKILL.md`; ghost-load prohibition bullet added to `diagnostic-ir.md §Current-pass activation rule`; Ghost-Load anti-pattern added to `anti-patterns.md`.

---

## v0.1.4.0

Execution Discipline and Operator Parity: pipeline canonical ownership declared; IR-to-case-state derivation map; hold/withheld/continuation-eligibility cross-referenced; minimum load floor rule; module-codes.md added to always-load set.
