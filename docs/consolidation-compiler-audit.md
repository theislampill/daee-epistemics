# daee-epistemics Consolidation Compiler Audit

> Phase 4 layout note: this Phase 1 audit used the earlier plan where `skill/` remained canonical source and `build/compiled-skill/` was the generated runtime. The implemented Phase 4 layout supersedes that path convention: canonical atomized source now lives under `atomics/skill/`, and `skill/` is the generated Claude package root. See `docs/source-vs-runtime-layout.md` for the current operating layout. Path references below that use `skill/` as source or `build/compiled-skill/` as final runtime are historical audit context, not current operating instructions.

## Executive Summary

The audit supports a compiler-style consolidation plan, not hand-authored flattening. The atomized source tree under `skill/` should remain the canonical development surface. Runtime packaging should eventually be generated into `build/compiled-skill/`, with bundled read views that preserve original module identity, source checksums, YAML contracts, diagnostic IR discipline, and `source_basis` traceability.

Sub-20 file calls are structurally achievable for ordinary runtime use if the generated runtime uses five always/near-always bundles plus selective omnibus bundles, and if a checker enforces that omnibus membership never becomes active dispatch. The result is conditional because no compiler, generated runtime, or call-budget checker exists yet.

No source files should be deleted, stubbed by hand, or moved in Phase 1. The safe first implementation is a report plus later deterministic tools under `tools/`.

## Core Finding

The atomized source architecture should remain canonical, but runtime execution should use generated compiled bundles.

The current source is already highly structured: all 103 Markdown files under `skill/references/` have YAML operative front matter, and `module-catalogue.json` maps registered module IDs to canonical source paths. That is enough to support a build pipeline, but not enough by itself to assign bundle boundaries, order, freshness, and call budgets. Those compiler decisions should be driven by source YAML plus a separate compiler manifest or equivalent deterministic compiler rules.

## Current Runtime Problem

The runtime problem is structural. `skill/SKILL.md` correctly requires an always-load foundation, a mandatory diagnostic core, V1 Phase 2 passes, a diagnostic IR dispatch gate, output-release governance, post-render state refresh, and confirmed-match module loads. In the atomized package, those are separate files. A normal substantive invocation can easily cross 20 file calls before the actual case family, tactics, techniques, and output governance are all loaded.

The issue is not a few pathological cases. The current architecture makes almost every serious case load too many small files because the governance surface is intentionally atomized.

## Canonical Source vs Compiled Runtime

- `skill/` = canonical atomized development source.
- `tools/` = compiler and checker scripts.
- `build/compiled-skill/` = generated runtime artifact.

The compiled runtime must be treated as a read-optimized build product, not a second source tree. If a generated bundle and the atomized source disagree, the atomized source wins. Generated files must be regenerated, not edited by hand.

## Audit Method

This audit used local inspection plus six read-only subagent audit passes:

- Runtime Pipeline Auditor
- YAML / Catalogue Compiler Auditor
- Bundle Boundary Auditor
- Call Budget Auditor
- Pipeline Repair Auditor
- Tooling / Compiler Auditor

Local inspection confirmed:

- No `docs/` directory existed before this report.
- No `build/` directory exists.
- No `skill/references/compiled/` directory exists.
- Existing `tools/` contains `check_frontmatter.py`, `check_coverage.py`, and `check_framework_pipeline.py`.
- `package.ps1` currently packages only from `skill/`.
- `rg` was unavailable in this environment because `rg.exe` returned access denied, so PowerShell and the bundled Python runtime were used for inspection.
- The repo copy is not a Git checkout, so no local git diff was available.

## Subagent Findings

### Runtime Pipeline Auditor Findings

Actual runtime order:

`SKILL.md` activation -> always-load foundation -> V1 diagnostic gate -> Phase 2 mandatory/triggered passes -> Diagnostic IR six-check dispatch gate -> selective matched module load floor -> output-release rubric -> diagnostic render contract -> bounded output -> post-render re-entry gate -> `STOP | HOLD | RECURSE | PARTIAL`.

| Pipeline stage | Current source files | Runtime role | Can compile? | Bundle target |
|---|---|---|---|---|
| Entrypoint | `skill/SKILL.md` | Governing control plane: activation, load rules, routing constraints, output contract | Yes, as generated entrypoint | `build/compiled-skill/SKILL.md` |
| Always-load foundation | `skill/references/terminology.md`; `skill/references/case-library/INDEX.md`; `skill/references/module-codes.md`; `skill/references/techniques/heuristics.md`; module catalogue summary | Vocabulary, first router, canonical module IDs, operator discipline | Yes | `build/compiled-skill/references/runtime-foundation.md` |
| Mandatory diagnostic core | `skill/references/techniques/V1-diagnostic.md`; `skill/references/diagnostics/noetic-reading-checklist.md`; `skill/references/diagnostics/seven-deformations.md`; `skill/references/diagnostics/modes-of-concealment.md`; `skill/references/diagnostics/discourse-orientation.md`; `skill/references/tactics/M5-deformation-triage.md` | Opening diagnostic pass before tactic or case dispatch | Yes | `build/compiled-skill/references/runtime-diagnostic-core.md` |
| Mandatory Phase 2 passes | `skill/references/diagnostics/reason-disambiguation.md`; `skill/references/diagnostics/foreign-premise-detection.md`; `skill/references/diagnostics/prophetic-discourse-neutralization.md`; `skill/references/diagnostics/arabic-backbone-predicates.md` | P-A through P-D pass stack; feeds IR | Yes | `build/compiled-skill/references/runtime-phase2-passes.md` |
| Dispatch gate files | `skill/references/diagnostics/diagnostic-ir.md`; `skill/references/diagnostics/diagnostic-ir.schema.json`; `skill/references/diagnostics/routing-precedence.md`; `skill/references/diagnostics/case-state-schema.md`; `skill/references/diagnostics/pattern-profiling.md`; `skill/references/diagnostics/inference-boundary.md`; `skill/references/diagnostics/mixed-case-handling.md`; `skill/references/diagnostics/anti-patterns.md`; `skill/references/diagnostics/framework-pipeline.md`; `skill/references/kernel-thesis.md`; `skill/references/metaphysical-architecture.md`; `skill/references/procedures/P7-restoration-stops.md` | IR formation, six gate checks, precedence, source-basis discipline, hard stops, architectural integrity | Yes | `build/compiled-skill/references/runtime-dispatch-gate.md` |
| Output release files | `skill/references/rubrics/output-release.md`; `skill/references/rubrics/diagnostic-render-contract.md`; response-format sections from `skill/SKILL.md` | Release amount, order, render level, Layer A / Layer B discipline | Yes | `build/compiled-skill/references/runtime-output-governance.md` |
| Post-render state refresh | `diagnostic-ir.md`; `framework-pipeline.md`; `output-release.md`; `diagnostic-render-contract.md`; `P7-restoration-stops.md` | Recheck held routes; decide `STOP`, `HOLD`, `RECURSE`, or `PARTIAL` | Yes | `runtime-dispatch-gate.md` plus `runtime-output-governance.md` |
| Selective content modules | Profiles, DO families, RT/transmission, tactics, techniques, procedures, specialty diagnostics | Loaded only when confirmed by IR and routing precedence | Yes, as selective sections | `build/compiled-skill/references/omnibus/*.md` |

Key finding: several mandatory runtime files lack `compiled_runtime_eligible: true`, so a compiler must not rely on that field alone in Phase 2. It must also use explicit runtime bundle rules.

### YAML / Catalogue Compiler Auditor Findings

All 103 Markdown files under `skill/references/` have YAML operative contracts. Local inspection found:

- `id`, `module_class`, `canonical_path`, `contract_version`, `load_when`, and `catalogue_registered` on all 103 reference files.
- 69 catalogue-registered modules.
- 34 governance or rubric files marked non-catalogue.
- 48 files with `compiled_runtime_eligible: true` and `operator_pack_eligible: true`.
- No current `compile_group`, `compile_order`, `compiled_selective_eligible`, `source_canonical`, `generated_bundle`, or `preserve_module_id_in_bundle` fields.

| YAML field | Current status | Needed for compiler? | Recommendation |
|---|---|---|---|
| `id` | Present on all reference files | Yes | Preserve as original module or governance ID. |
| `module_class` | Present on all reference files | Yes | Preserve and emit in every compiled section header. |
| `canonical_path` | Present on all reference files | Yes | Treat as source identity. Do not rewrite to bundle paths. |
| `contract_version` | Present on all reference files | Yes | Keep as source contract version. |
| `catalogue_registered` | Present and aligned with catalogue/governance split | Yes | Keep source-controlled. |
| `load_when` | Present on all reference files | Yes, as audit metadata | Use for discoverability and checker hints, not as a deterministic dispatcher. |
| `companions` | Present on 66 files | Yes, if building co-load sets | Clarify whether companions may point to all contract IDs or only catalogue IDs. |
| `routing_effects` | Present on 47 files | Useful | Normalize vocabulary only if checkers depend on it. |
| `emits` | Present on 26 files | Useful | Tie to IR/schema vocabulary if validating outputs. |
| `blocks` | Present on 37 files | Useful | Keep as static audit metadata unless normalized. |
| `layer_constraint` | Present on 68 of 69 registered modules | Yes | Add to the redirect-like `noetic-profiles.md` or mark it non-runtime in a manifest. |
| `output_shapes` | Present on all 69 registered modules | Yes | Keep as compiler/audit signal. |
| `p7_stops_governed` | Present only where narrow | Yes | Keep narrow. |
| `compiled_runtime_eligible` | Present on 48 files, always true | Yes, but incomplete | Treat as an eligibility constraint, not a complete bundle assignment. |
| `operator_pack_eligible` | Present on same 48 files, always true | Yes, but incomplete | Same as above. |
| `compile_group` | Absent | Yes, if using source-only grouping | Prefer a separate manifest first; add only if source-owned grouping becomes necessary. |
| `compile_order` | Absent | Yes, if using source-only ordering | Prefer manifest/compiler rules first. |
| `compiled_selective_eligible` | Absent | Maybe | Add only if selective bundling cannot be expressed cleanly in a manifest. |
| `source_canonical` | Absent | Maybe | Better expressed globally: all `skill/` sources are canonical. |
| `generated_bundle` | Absent | No for source files | Generated artifacts should mark themselves in headers, not in source YAML. |
| `preserve_module_id_in_bundle` | Absent | Required behavior | Better enforced by boundary checker than per-file YAML. |

Recommendation: use a separate compiler manifest or deterministic compiler config to assign `compile_group`, bundle target, and order. Source YAML should remain identity, eligibility, contract, and routing-audit metadata.

### Bundle Boundary Auditor Findings

Bundle membership is availability only. A bundle read must not activate every section inside the bundle.

| Bundle | Included source files | Always or selective? | Why safe? | Routing risk | Required preservation rule |
|---|---|---|---|---|---|
| `build/compiled-skill/references/runtime-foundation.md` | `skill/references/terminology.md`; `skill/references/case-library/INDEX.md`; `skill/references/module-codes.md`; `skill/references/techniques/heuristics.md`; generated catalogue summary from `skill/references/diagnostics/module-catalogue.json` | Always | These are the vocabulary, first router, module ID reference, and operator discipline | Index/catalogue presence treated as routing | Catalogue constrains IDs; it does not dispatch modules |
| `build/compiled-skill/references/runtime-diagnostic-core.md` | `V1-diagnostic.md`; `noetic-reading-checklist.md`; `seven-deformations.md`; `modes-of-concealment.md`; `discourse-orientation.md`; `M5-deformation-triage.md` | Always for substantive cases | These define the opening diagnosis, not topic content | Skipping V1 or treating M5 as a rival entry | Preserve V1-first rule |
| `build/compiled-skill/references/runtime-phase2-passes.md` | `reason-disambiguation.md`; `foreign-premise-detection.md`; `prophetic-discourse-neutralization.md`; `arabic-backbone-predicates.md` | Mandatory inside V1 Phase 2, with triggers | Keeps reason, imported criterion, prophetic-discourse, and backbone predicate checks upstream | Emitting blocks from memory or treating skipped conditions as active | Preserve P-A to P-D order and file-backed emissions |
| `build/compiled-skill/references/runtime-dispatch-gate.md` | `diagnostic-ir.md`; `diagnostic-ir.schema.json`; `case-state-schema.md`; `pattern-profiling.md`; `inference-boundary.md`; `mixed-case-handling.md`; `anti-patterns.md`; `framework-pipeline.md`; `routing-precedence.md`; `kernel-thesis.md`; `metaphysical-architecture.md`; `P7-restoration-stops.md` | Always before dispatch | Bundles the gate, suppression rules, source-basis discipline, and hard rails | Ghost-loads and `matched_modules` as a warehouse | `matched_modules` stays current-pass only and source-basis-backed |
| `build/compiled-skill/references/runtime-output-governance.md` | `output-release.md`; `diagnostic-render-contract.md`; generated response-format excerpts from `skill/SKILL.md` | Always after gate-open | Separates release eligibility from visible render | Render level determining routing | Output shape follows IR; it never creates routing authority |
| `build/compiled-skill/references/omnibus/OMNIBUS-profiles.md` | `profiles/INDEX.md`; `noetic-profiles.md`; all `profiles/ns-*.md` | Selective | Profiles stay individually owned | Co-loading many NS profiles as active | Only confirmed NS sections activate |
| `build/compiled-skill/references/omnibus/OMNIBUS-do-families.md` | `do-core.md`; `do-second-loop.md`; `do-christian-extensions.md`; `do-attribute-precision.md`; `philosophical-usurpation.md`; `sound-reason-epistemology.md`; `prophecy-wahy-supremacy.md` | Selective | Consolidates confirmed DO and tribunal/theory owners | DO topic shortcut; sound-reason theory bleed | Confirm DO/upstream blocker first; record original IDs only |
| `build/compiled-skill/references/omnibus/OMNIBUS-rt-transmission.md` | `revelation-transmission.md`; `V10-transmission-content-vetting.md`; final-prophethood/source-use excerpts from `prophecy-wahy-supremacy.md` if not included in DO bundle | Selective | Keeps source-use, transmission, canon, and V10 together | Any scripture mention treated as RT | V10/source-use before RT content; no invented RT codes |
| `build/compiled-skill/references/omnibus/OMNIBUS-tactics.md` | `tactics/INDEX.md`; all tactic files including M/E/F/R, `doubt-vs-skepticism.md`, `husn-al-nazar-arguments.md`, `inductive-fitri-method.md`, `symmetric-taqlid-check.md` | Selective | Tactics remain immediate moves selected after diagnosis | Tactic stacking | Smallest case-state-justified tactic set only |
| `build/compiled-skill/references/omnibus/OMNIBUS-techniques.md` | `techniques/INDEX.md`; `V2` through `V12`; optionally generated cross-reference stubs for V1 and heuristics already present in runtime bundles | Selective | Techniques govern arcs, not automatic responses | Duplicate activation if V1/heuristics also appear in runtime bundles | Same source identity; no duplicate `matched_modules` |
| `build/compiled-skill/references/omnibus/OMNIBUS-procedures.md` | `procedures/INDEX.md`; `P1` through `P7`; optionally a cross-reference stub for P7 if full text is in the dispatch gate | Selective, with P7 gate-relevant | Procedures are workflows, not default answers | Escalating one-move cases into procedures | P7 rails outrank procedure momentum |
| `build/compiled-skill/references/omnibus/OMNIBUS-specialty-diagnostics.md` | `diagnostics/INDEX.md`; `kalamic-interlocutor.md`; `fitrah-perspectives.md`; `hadith-authentication-epistemology.md`; `causal-series-taxonomy.md`; `definition-discipline.md`; `proof-method-audit.md`; `perfection-criterion-usurpation.md` | Selective | Specialty files are discriminators for named structural burdens | Surface-label routing or proof dump | Load only on specialty markers; clear diagnostic burden before content |

Static validation and historical-audit files such as `coverage-ledger.md`, `coverage-scope.yaml`, `operative-contracts.md`, `operative-contract.schema.json`, and `pattern-family-audit.md` should not become active runtime dispatch bundles. They may be copied into an audit/debug package or embedded into checker inputs.

### Call Budget Auditor Findings

The current atomized estimates are based on `skill/SKILL.md` load floors, required governance files, and confirmed-match file counts. They are estimates, not measured telemetry, because no compiled runtime checker exists yet.

Success thresholds:

- Simple cases: at most 5 file calls.
- Ordinary substantive cases: at most 12 file calls.
- Complex governed cases: at most 20 file calls.
- Maximal audit/regression cases are non-normal and may exceed 20.

The proposed checker `tools/check_consolidation_call_budget.py` must encode these case classes and fail normal cases above threshold.

### Pipeline Repair Auditor Findings

| Current instruction | Problem | Proposed compiled-runtime instruction |
|---|---|---|
| Source `skill/SKILL.md` routes to atomized `references/...` paths | Generated runtime would still load source paths first | Source `SKILL.md` should state that `skill/` is canonical source and generated bundles are runtime read views |
| No `build/compiled-skill/SKILL.md` exists | No compiled runtime entrypoint | Generate `build/compiled-skill/SKILL.md` from source `skill/SKILL.md` plus compiled routing instructions |
| Always-load table names source files | A compiled artifact should load bundled runtime files | Generated `SKILL.md` loads `runtime-foundation.md`, then diagnostic/runtime bundles |
| `matched_modules` assumes loaded source file | In compiled runtime, the loaded object is a bundle section | Every `matched_modules` entry must map to an original `module_id`, `module_class`, and `canonical_path` section in a loaded bundle |
| `module-catalogue.json` maps IDs to source paths | Rewriting catalogue paths would break source authority | Keep source catalogue canonical; generate a bundle map/resolver from source ID to bundle section |
| Source indexes route to source paths | Rewriting them would corrupt development source | Keep source indexes source-only; generated runtime may include a generated resolver/index |
| Omnibus bundle exposes many sibling sections | Sibling modules could become ambiently active | Bundle read does not equal activation; only IR-confirmed sections recorded in `source_basis` are active |
| Packaging builds only from `skill/` | No low-call runtime package | Add future source/debug and compiled/runtime package modes |

### Tooling / Compiler Auditor Findings

Current `tools/` contains only:

- `tools/check_frontmatter.py`
- `tools/check_coverage.py`
- `tools/check_framework_pipeline.py`

The required proposed tools do not exist yet. They should be added in Phase 2, not in this audit-only pass.

| Tool | Inputs | Outputs | Checks | Failure conditions |
|---|---|---|---|---|
| `tools/build_compiled_runtime.py` | `skill/SKILL.md`; `skill/references/**/*.md`; `skill/references/diagnostics/module-catalogue.json`; compiler manifest/rules | `build/compiled-skill/SKILL.md`; runtime bundles; omnibus bundles; generated bundle map; build manifest | Parse front matter; group by bundle; preserve headers; emit checksums; generate entrypoint; never mutate source | Missing source; duplicate ID; catalogue drift; required bundle member absent; nondeterministic output |
| `tools/check_compiled_runtime_freshness.py` | Current source tree; generated bundles; build manifest; compiler rules | PASS/FAIL freshness report | Recompute source hashes; compare compiler version/rules; ensure catalogue modules appear in required bundle map | Source changed; stale hash; compiler/rule drift; generated `SKILL.md` stale |
| `tools/check_consolidation_call_budget.py` | Case-class config; generated `SKILL.md`; bundle map | PASS/FAIL call-budget report | Model load paths; count calls; enforce simple/ordinary/complex thresholds | Normal case exceeds threshold; maximal case not marked non-normal; path points outside `build/compiled-skill/` |
| `tools/check_compiled_module_boundaries.py` | Generated bundles; module catalogue; source front matter | PASS/FAIL boundary report | Verify source markers, IDs, classes, canonical paths, checksums, one source per section | Missing `SOURCE_SHA256`; lost ID; section collapse; duplicate module; omnibus name used as module ID |
| `tools/check_stub_integrity.py` | Source tree; catalogue; generated stubs/maps | PASS/FAIL stub report | Ensure source files remain, YAML remains, paths resolve, stubs point to valid sections | Source deleted; YAML removed; canonical path drift; stub points nowhere; registered file lacks body or pointer |

Recommended CI order after Phase 2:

1. `tools/check_frontmatter.py`
2. `tools/check_coverage.py`
3. `tools/check_framework_pipeline.py`
4. JSON schema sanity checks
5. `tools/build_compiled_runtime.py`
6. `tools/check_compiled_runtime_freshness.py`
7. `tools/check_compiled_module_boundaries.py`
8. `tools/check_stub_integrity.py`
9. `tools/check_consolidation_call_budget.py`

## Proposed Compiled Runtime Architecture

```text
skill/ canonical atomized source
  -> source YAML/front matter
  -> module-catalogue.json
  -> compiler manifest/rules under tools/
  -> tools/build_compiled_runtime.py
  -> build/compiled-skill/
  -> generated runtime package
```

Generated `build/compiled-skill/SKILL.md` should:

1. Declare itself generated.
2. Declare `skill/` as canonical source.
3. Load `references/runtime-foundation.md` first.
4. Load diagnostic core, Phase 2, dispatch gate, and output governance for substantive cases.
5. Route selective modules through `references/omnibus/*.md`.
6. Forbid omnibus names in `matched_modules`.
7. Require `source_basis` entries to name original module IDs and compiled bundle sections.

Every generated file must begin with:

```md
<!--
GENERATED FILE.
Do not edit directly.
Canonical source lives under skill/.
Regenerate with tools/build_compiled_runtime.py.
-->
```

Every compiled section must preserve source identity:

```md
<!-- SOURCE: skill/references/tactics/M9-predication-mode.md -->
<!-- MODULE_ID: M9-predication-mode -->
<!-- MODULE_CLASS: tactic -->
<!-- CANONICAL_PATH: skill/references/tactics/M9-predication-mode.md -->
<!-- SOURCE_SHA256: ... -->
```

## Proposed Runtime Bundles

- `build/compiled-skill/references/runtime-foundation.md`
- `build/compiled-skill/references/runtime-diagnostic-core.md`
- `build/compiled-skill/references/runtime-phase2-passes.md`
- `build/compiled-skill/references/runtime-dispatch-gate.md`
- `build/compiled-skill/references/runtime-output-governance.md`

These bundles are safe because they compile governance that is already mandatory or near-mandatory in ordinary substantive cases. They do not turn selective content into always-load runtime content.

## Proposed Selective Omnibus Bundles

- `build/compiled-skill/references/omnibus/OMNIBUS-profiles.md`
- `build/compiled-skill/references/omnibus/OMNIBUS-do-families.md`
- `build/compiled-skill/references/omnibus/OMNIBUS-rt-transmission.md`
- `build/compiled-skill/references/omnibus/OMNIBUS-tactics.md`
- `build/compiled-skill/references/omnibus/OMNIBUS-techniques.md`
- `build/compiled-skill/references/omnibus/OMNIBUS-procedures.md`
- `build/compiled-skill/references/omnibus/OMNIBUS-specialty-diagnostics.md`

Selective omnibus loading means the relevant sections are available in one file call. It does not mean every module inside the file is active. Active modules are still only those confirmed by V1, routing precedence, the diagnostic IR, and output governance.

## YAML Requirements

Current YAML is sufficient for identity, catalogue integrity, eligibility hints, and static audit. It is not sufficient by itself for deterministic bundle construction because bundle membership and order are absent.

Recommended Phase 2 policy:

- Use existing YAML fields for identity and constraints.
- Add a compiler manifest/rule table for bundle membership and order.
- Do not add `compile_group` and `compile_order` to source YAML until the first compiler proves they are needed.
- Treat absent `compiled_runtime_eligible` as "not yet asserted", not as a reason to omit mandatory runtime files.
- Keep `module-catalogue.json` source-canonical.

If source YAML later owns bundle grouping, evaluate these keys:

```yaml
compile_group: runtime-foundation
compile_order: 10
compiled_selective_eligible: true
source_canonical: true
preserve_module_id_in_bundle: true
```

Do not add `generated_bundle` to source files. Generated artifacts should self-identify with generated headers.

## Compiler Tooling Requirements

`tools/build_compiled_runtime.py` should:

1. Read YAML/front matter from `skill/`.
2. Read `module-catalogue.json`.
3. Group source files by manifest/rules or future `compile_group`.
4. Preserve source headers.
5. Emit generated bundles under `build/compiled-skill/`.
6. Include generated-file warnings.
7. Include source path, module ID, module class, checksum, and canonical path for each section.
8. Generate `build/compiled-skill/SKILL.md` from `skill/SKILL.md` plus compiled-runtime routing modifications.
9. Never mutate canonical source files unless explicitly configured in a later task.

`tools/check_compiled_runtime_freshness.py` should fail if:

1. A source file changed but the compiled bundle was not rebuilt.
2. A YAML compile group or manifest mapping changed but the bundle is stale.
3. A source checksum in a bundle does not match the current file.
4. A catalogue module is absent from its required bundle or bundle map.
5. Generated `build/compiled-skill/SKILL.md` is stale relative to source `skill/SKILL.md` and compiler template/rules.

`tools/check_consolidation_call_budget.py` should:

1. Model case-class load paths.
2. Count file calls.
3. Assert sub-20 thresholds.
4. Fail if normal case classes exceed threshold.
5. Explicitly distinguish maximal audit/regression from normal execution.

`tools/check_compiled_module_boundaries.py` should fail if:

1. Original module ID is lost.
2. A section header lacks canonical path.
3. An omnibus section lacks module class.
4. Multiple source files collapse without boundary markers.
5. A generated bundle contains source content without `SOURCE_SHA256`.

`tools/check_stub_integrity.py` should fail if:

1. Original source file was deleted.
2. YAML front matter was removed.
3. Canonical path changed without catalogue migration.
4. A stub points to a non-existent compiled section.
5. A catalogue-registered file no longer has an identifiable source body or source pointer.

## SKILL.md Pipeline Repair Requirements

Source `skill/SKILL.md` should add a short development-source note:

```text
Canonical source is the atomized source tree under skill/references/.
Generated compiled bundles are runtime read views only.
Do not edit compiled artifacts directly; regenerate them from source.
On conflict, atomized source governs.
```

Generated `build/compiled-skill/SKILL.md` should add compiled-runtime routing rules:

```text
Load runtime bundles from references/runtime-*.md.
Use references/omnibus/*.md only after V1, Phase 2, and the Diagnostic IR authorize the original module owner.
Bundle names never appear in matched_modules.
Every matched module must cite the original module_id and a compiled bundle section in source_basis.
Bundle co-location does not activate sibling sections.
```

Indexes should remain source-only in `skill/`. A generated bundle resolver may be created in `build/compiled-skill/`, but source indexes should not be rewritten.

## Package Strategy

The final low-call distributable should eventually be built from `build/compiled-skill/`, not directly from `skill/`.

Recommended package modes:

- Source/debug package from `skill/`.
- Compiled/runtime package from `build/compiled-skill/`.

Current command:

```powershell
.\package.ps1 daee-epistemics-source.skill.zip
```

Future compiled command shape:

```powershell
python tools/build_compiled_runtime.py
python tools/check_compiled_runtime_freshness.py
python tools/check_compiled_module_boundaries.py
python tools/check_stub_integrity.py
python tools/check_consolidation_call_budget.py
.\package.ps1 -SkillRoot build\compiled-skill daee-epistemics-runtime.skill.zip
```

This task should not change packaging. A later task should add `-SkillRoot` or equivalent packaging support.

Freshness checks before packaging from `build/compiled-skill/`:

- Rebuild deterministically or compare against a temp rebuild.
- Verify all source checksums.
- Verify generated `SKILL.md` is current.
- Verify module boundaries and source markers.
- Verify normal call-budget case classes.

Generated `build/` artifacts should usually be ignored unless the project wants reviewable generated artifacts in PRs. If ignored, `.gitignore` should add:

```gitignore
/build/
```

An alternate review policy is to commit `build/compiled-skill/` only for release branches, after freshness checks pass.

## Success Condition: Sub-20 File Calls

Sub-20 is structurally achievable if and only if:

1. The generated runtime uses the five runtime bundles.
2. Ordinary cases use at most a few selective omnibus bundles.
3. Bundle loading remains section-scoped, not ambient activation.
4. `tools/check_consolidation_call_budget.py` enforces case-class budgets.
5. Maximal audit/regression runs are explicitly marked non-normal.

## Case-Class Call Budget Table

| Case class | Current atomized calls | Post-compiled calls | Load path | Under 20? | Notes |
|---|---:|---:|---|---|---|
| Simple glossary / factual query | 2-4 | 2 | `build/compiled-skill/SKILL.md` -> `build/compiled-skill/references/runtime-foundation.md` | Yes | Meets simple threshold `<= 5`. No diagnostic core unless structural diagnosis is needed. |
| Ordinary theological or philosophical objection | 18-22 | 8 | `SKILL.md` -> `runtime-foundation.md` -> `runtime-diagnostic-core.md` -> `runtime-phase2-passes.md` -> `runtime-dispatch-gate.md` -> `runtime-output-governance.md` -> `omnibus/OMNIBUS-do-families.md` -> `omnibus/OMNIBUS-tactics.md` | Yes | Meets ordinary threshold `<= 12`. |
| Atheist / naturalist objection | 21-26 | 9 | `SKILL.md` -> `runtime-foundation.md` -> `runtime-diagnostic-core.md` -> `runtime-phase2-passes.md` -> `runtime-dispatch-gate.md` -> `runtime-output-governance.md` -> `omnibus/OMNIBUS-profiles.md` -> `omnibus/OMNIBUS-tactics.md` -> `omnibus/OMNIBUS-techniques.md` | Yes | Matched modules remain original IDs such as `ns-1-naturalist`, `V2-reconstituting-reason`, `M1-self-refutation`, or `doubt-vs-skepticism`. |
| Christian Trinity / incarnation / philosopher's-God case | 28-35 | 10 | `SKILL.md` -> `runtime-foundation.md` -> `runtime-diagnostic-core.md` -> `runtime-phase2-passes.md` -> `runtime-dispatch-gate.md` -> `runtime-output-governance.md` -> `omnibus/OMNIBUS-do-families.md` -> `omnibus/OMNIBUS-tactics.md` -> `omnibus/OMNIBUS-techniques.md` -> `omnibus/OMNIBUS-specialty-diagnostics.md` | Yes | Original IDs remain, for example `do-christian-extensions`, `do-attribute-precision`, `M9-predication-mode`, `V8-bila-kayf-anchor`, `V12-tamanuc-exhaustion`. |
| Revelation / transmission / canon case | 24-30 | 9 | `SKILL.md` -> `runtime-foundation.md` -> `runtime-diagnostic-core.md` -> `runtime-phase2-passes.md` -> `runtime-dispatch-gate.md` -> `runtime-output-governance.md` -> `omnibus/OMNIBUS-rt-transmission.md` -> `omnibus/OMNIBUS-techniques.md` -> `omnibus/OMNIBUS-tactics.md` | Yes | RT and V10 remain section-scoped. |
| Hadith-authentication case | 22-27 | 8 | `SKILL.md` -> `runtime-foundation.md` -> `runtime-diagnostic-core.md` -> `runtime-phase2-passes.md` -> `runtime-dispatch-gate.md` -> `runtime-output-governance.md` -> `omnibus/OMNIBUS-specialty-diagnostics.md` -> `omnibus/OMNIBUS-rt-transmission.md` if RT pressure is also live | Yes | Hadith owner can be loaded without treating all scripture questions as RT. |
| Kalamic / Maturidi evidentialist case | 25-32 | 10 | `SKILL.md` -> `runtime-foundation.md` -> `runtime-diagnostic-core.md` -> `runtime-phase2-passes.md` -> `runtime-dispatch-gate.md` -> `runtime-output-governance.md` -> `omnibus/OMNIBUS-profiles.md` -> `omnibus/OMNIBUS-specialty-diagnostics.md` -> `omnibus/OMNIBUS-techniques.md` -> `omnibus/OMNIBUS-tactics.md` | Yes | Keeps proof-method and sound-reason routing under IR control. |
| Grief-primary / identity-performance / thin-basis case | 18-23 | 8 | `SKILL.md` -> `runtime-foundation.md` -> `runtime-diagnostic-core.md` -> `runtime-phase2-passes.md` -> `runtime-dispatch-gate.md` -> `runtime-output-governance.md` -> `omnibus/OMNIBUS-procedures.md` -> `omnibus/OMNIBUS-tactics.md` | Yes | P7, M4, and register holds can be section-loaded without doctrinal release. |
| Complex mixed higher-order case | 35-45 | 13 | `SKILL.md` -> all five runtime bundles -> `OMNIBUS-profiles.md` -> `OMNIBUS-do-families.md` -> `OMNIBUS-rt-transmission.md` -> `OMNIBUS-tactics.md` -> `OMNIBUS-techniques.md` -> `OMNIBUS-procedures.md` -> `OMNIBUS-specialty-diagnostics.md` | Yes | Meets complex threshold `<= 20`; active modules must remain current-pass only. |
| Maximal audit / regression case | 80-110+ | 21+ or audit-configured | `SKILL.md` -> all runtime bundles -> all omnibus bundles -> schemas/manifests/checker inputs as needed | Non-normal | May exceed 20. Must be explicitly marked as audit/regression, not ordinary runtime execution. |

## Preservation Rules

- Atomized files remain canonical.
- Generated bundles are build artifacts.
- Generated bundles live under `build/compiled-skill/`.
- Compiler/checker scripts live under `tools/`.
- Original module IDs remain authoritative.
- `matched_modules` never uses omnibus names unless an omnibus is itself a governance artifact.
- `source_basis` names the original source module or section.
- YAML front matter is preserved.
- `module-catalogue.json` remains authoritative for source identity.
- No source file deletion in the first implementation phase.
- Bundle membership is not active dispatch.
- A loaded bundle section must include original source path, module ID, module class, canonical path, and source checksum.
- Generated files must not be edited by hand.

## Risks and Failure Modes

- Omnibus-as-active-dispatch: a bundle is loaded and every sibling module is treated as active.
- Stale generated bundle: source changed but bundle checksum did not.
- Lost module identity: original `id` or `module_class` disappears inside a bundle.
- Ghost-loads: `matched_modules` includes a module without a corresponding `source_basis` entry.
- Catalogue drift: `module-catalogue.json` no longer matches source or generated map.
- YAML drift: source front matter and body/routing prose diverge.
- Runtime/source divergence: compiled artifact evolves as if canonical.
- Over-broad always-load: selective modules get pulled into runtime bundles.
- Weakened P7 stop/recurse discipline: compiled runtime shortcuts `STOP`, `HOLD`, `RECURSE`, or `PARTIAL`.
- Diagnostic IR bypass: bundle routing substitutes for IR.
- Generated build artifact accidentally edited by hand.
- Source package and compiled package drifting apart.
- Companion expansion becoming unbounded.
- Duplicate source bodies creating inconsistent module sections.
- Source-basis entries citing omnibus filenames without original module IDs.

## Recommended Implementation Phases

### Phase 1 - Audit and compiler spec only

Create this report. Do not generate compiled bundles. Do not delete source files.

### Phase 2 - Add compiler/checker tools

Add:

```text
tools/build_compiled_runtime.py
tools/check_compiled_runtime_freshness.py
tools/check_consolidation_call_budget.py
tools/check_compiled_module_boundaries.py
tools/check_stub_integrity.py
```

### Phase 3 - Generate compiled runtime into build

Generate:

```text
build/compiled-skill/
```

Do not write generated bundles into `skill/`.

### Phase 4 - Build/package from compiled runtime

Add a packaging command that can build the `.skill` from:

```text
build/compiled-skill/
```

### Phase 5 - Optional dual package mode

Support:

```text
source/debug package from skill/
compiled/runtime package from build/compiled-skill/
```

### Phase 6 - CI enforcement

CI should fail if:

```text
build/compiled-skill/ is stale
normal case-class call budget exceeds 20
compiled section identity markers are missing
source checksums do not match
module IDs are lost
```

## Final Recommendation

Proceed with compiler/checker implementation before generating any runtime bundles. The safest architecture is a deterministic compiler that consumes the atomized `skill/` source, preserves original IDs and source checksums in generated bundle sections, and packages the low-call runtime from `build/compiled-skill/` only after freshness, boundary, stub, and call-budget checks pass.

The source tree should remain the development and debug artifact. The compiled tree should become the low-call runtime artifact once the Phase 2 tools exist.
