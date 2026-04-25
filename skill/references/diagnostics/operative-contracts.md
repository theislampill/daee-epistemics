---
id: operative-contracts
module_class: governance
canonical_path: skill/references/diagnostics/operative-contracts.md
contract_version: "0.2.0.0"
load_when:
  - adding or auditing YAML operative front matter on any skill file
  - migrating a module class to the contract layer
  - implementing a linter or checking catalogue/path alignment
catalogue_registered: false
---

> role: architecture spec for per-file machine-readable operative contracts — defines purpose, required/optional YAML front matter keys, allowed values, examples, failure modes, migration strategy, and linting plan
> use when: adding or auditing YAML operative front matter on any skill file; migrating a module class to the contract layer; implementing a linter; checking catalogue/path alignment
> do not use when: routing a live case — this file does not govern dispatch; it governs static file-level metadata

# Operative Contracts

## Function

An **operative contract** is a small YAML block at the top of an operative skill file that declares the file's machine-readable identity, class, path, and routing-relevant properties. It is a static per-file metadata layer — not a runtime control surface.

The contract layer coexists with, and does not replace:
- The **blockquote front matter** (`> role:`, `> use when:`) already present in most files — which remains the human-readable load declaration
- The **diagnostic IR** — which remains the canonical runtime dispatch gate
- The **module catalogue** — which remains the master registry for dispatched module ids, paths, and classes

The contract layer makes existing per-file knowledge machine-parseable and lintable. It is not an additional routing engine, and it does not add new governance logic.

The operative-contract layer is not a runtime dispatch substitute. Its operational value is **static discoverability and auditability**: it lets agents and future lint tools see which modules declare load conditions, companions, emitted fields, blocked moves, output constraints, and catalogue bindings before runtime routing decides which of them actually activate. This allows complex cases to expose a wider selectively routed field of candidate modules without making those modules ambient always-load.

A complex Trinitarian, kalāmic, atheist, secular, or mixed higher-order case may surface many candidate modules through contracts and companions. That does not mean all candidates are active. The diagnostic IR still decides current-pass activation. The contract layer makes the candidate field auditable; the IR makes dispatch lawful.

---

## Architecture Position

```
module-catalogue.json         operative-contract.schema.json
     |                                  |
     | id/path/class registry           | validates YAML front matter shape
     |                                  |
     +------ cross-check ---------------+
                    |
                    v
     [YAML operative front matter in each file]
           id, module_class, canonical_path,
           contract_version, load_when, emits, ...
                    |
                    | static declaration (not runtime)
                    v
     [human-readable blockquote front matter]
           > role: ..., > use when: ...
                    |
                    v
     [operative prose body]
           Rules, procedures, fixtures, case logic
                    |
                    v
     [diagnostic IR — runtime dispatch gate]
           case_family, matched_modules, routing_gate,
           output_shape, what_is_withheld_and_why, ...
```

The YAML operative front matter is read at audit/lint time. It is not read by the diagnostic IR at runtime. The IR governs what actually runs.

---

## Relation to Diagnostic IR

The diagnostic IR is the canonical audited control surface. It is formed at runtime after the dispatch gate opens. It is not derivable from operative contracts alone.

Operative contracts declare what a file *is* and *should do*. The IR records what *actually happened* in a pass.

**A contract field is not a guarantee of activation.** `load_when` describes the static trigger conditions; whether those conditions obtain in a given pass is determined by V1 and the diagnostic gate, not by reading the contract. Similarly, `emits` names the IR fields a module is capable of populating; whether they are populated in a given pass depends on the case-state.

**Operative contracts must not duplicate IR fields.** Do not add `case_family`, `deformation`, `pattern_profile`, `matched_modules`, or other IR runtime fields to operative front matter. Those belong to the IR, not to per-file static metadata.

---

## Relation to Module Catalogue

`module-catalogue.json` is the master registry: three fields per entry (`id`, `path`, `module_class`) for all dispatched modules. When a module has an operative contract, the contract's `id`, `canonical_path`, and `module_class` must match the catalogue entry exactly.

Governance files (framework-pipeline.md, routing-precedence.md, output-release.md, diagnostic-render-contract.md, operative-contracts.md, etc.) are not dispatched as modules and are not in the catalogue. They use `module_class: governance` and `catalogue_registered: false` in their contracts.

---

## Required Front Matter Keys

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | Module id — must match module-catalogue.json entry when `catalogue_registered: true` |
| `module_class` | string (enum) | Module class — see allowed values below |
| `canonical_path` | string | Repo-root-relative path to this file |
| `contract_version` | string | Semver string of the repo version when this contract was written or last updated |

---

## Optional Front Matter Keys

| Key | Type | Description |
|-----|------|-------------|
| `load_when` | array of strings | Trigger conditions for loading this module; aligns with prose `> use when:` |
| `routing_effects` | array of strings | Effects on routing gate or dispatch order when this module runs |
| `emits` | array of strings | IR or output fields this module is capable of populating |
| `blocks` | array of strings | Moves or dispatch paths this module prohibits |
| `companions` | array of strings | Module ids that must or should be loaded alongside this one |
| `output_shapes` | array of strings (enum) | Output shape(s) this module can produce — see allowed values |
| `p7_stops_governed` | array of strings (enum) | P7 stops declared or governed by this file — only for procedure/governance files that own stop behavior |
| `layer_constraint` | string (enum) | Layer A / Layer B deployment constraint |
| `catalogue_registered` | boolean | Whether this file has a matching entry in module-catalogue.json (default: true for all non-governance classes) |

---

## Allowed Values

### `module_class`

| Value | Description |
|-------|-------------|
| `tactic` | Matched to M*, E*, F*, R* tactic files |
| `procedure` | Matched to P1–P7 procedure files |
| `technique` | Matched to V1–V12 technique files |
| `diagnostic` | Matched to diagnostic overlay files (causal-series-taxonomy, definition-discipline, etc.) |
| `case-library` | Matched to DO family, NS profiles, revelation-transmission, philosophical-usurpation, etc. |
| `governance` | Framework, pipeline, rubric, and meta files not dispatched as modules; not in catalogue |

### `output_shapes`

| Value | Description |
|-------|-------------|
| `bounded-single-pass` | Module produces a single bounded response and stops unless refreshed state permits continuation |
| `held-pending-upstream` | Module's output is held downstream of an upstream blocker; released only after that blocker clears |
| `recursive-traversal-permitted` | Module licenses or governs same-response recursion when case-state permits |
| `pass-through` | Module conditions other modules without itself producing a directly visible output |

### `layer_constraint`

| Value | Description |
|-------|-------------|
| `layer-a-only` | Module output stays in Layer A (full diagnostic); never deployed in Layer B visible response |
| `layer-b-permitted` | Module output may be deployed in Layer B when case-state and register permit |
| `layer-b-governed` | Module explicitly governs whether Layer B deployment is permitted or blocked in the current pass |

### `p7_stops_governed`

Values: `stop-1`, `stop-2`, `stop-3`, `stop-4`, `stop-5`

Only declare stops that this file owns or governs. P7-restoration-stops.md governs all five. Other files may govern one or two if they trigger or enforce a specific stop.

---

## Examples by Module Class

### Example: tactic — M9-predication-mode.md

```yaml
---
id: M9-predication-mode
module_class: tactic
canonical_path: skill/references/tactics/M9-predication-mode.md
contract_version: "0.2.0.0"
load_when:
  - equivocation across term occurrences
  - domain-boundary failure (empirical method on non-empirical subject)
  - univocal/equivocal/analogical predication question active
  - loaded negative-theological term operative
  - semantic-discipline-required gate active
routing_effects:
  - semantic-discipline-required
  - holds doctrinal-release pending predication clearance
emits:
  - ontological_disorder
  - what_is_withheld_and_why
blocks:
  - doctrinal-release before semantic clearing
  - yes/no answer on loaded term before sense-split
companions:
  - definition-discipline
  - do-attribute-precision
output_shapes:
  - bounded-single-pass
  - held-pending-upstream
catalogue_registered: true
---
```

### Example: procedure — P7-restoration-stops.md

```yaml
---
id: P7-restoration-stops
module_class: procedure
canonical_path: skill/references/procedures/P7-restoration-stops.md
contract_version: "0.2.0.0"
load_when:
  - any response sequence at risk of premature argument deployment
  - grief-primary or identity-performance orientation confirmed
  - recognition or contact has surfaced (stop-2 trigger)
  - thin basis underdetermination active (stop-4 trigger)
routing_effects:
  - may halt content dispatch (stops 1-5)
  - requires boundary-reset after landed move
  - permits recursion only from refreshed case-state
p7_stops_governed:
  - stop-1
  - stop-2
  - stop-3
  - stop-4
  - stop-5
emits:
  - p7_stops_active
blocks:
  - debate-autonomous chaining after landed move
  - premature content deployment before register established
layer_constraint: layer-b-governed
output_shapes:
  - bounded-single-pass
  - held-pending-upstream
catalogue_registered: true
---
```

### Example: governance — routing-precedence.md

```yaml
---
id: routing-precedence
module_class: governance
canonical_path: skill/references/diagnostics/routing-precedence.md
contract_version: "0.2.0.0"
load_when:
  - multiple diagnostic axes produce competing signals
  - suppression rules needed to prevent invalid routing combinations
  - tie-break required between equally-weighted routes
routing_effects:
  - establishes deterministic owner order
  - applies suppression rules S-1 through S-7
  - applies route-priority rules P-1 through P-4
emits:
  - routing_gate
blocks:
  - simultaneous dispatch of competing routes without precedence resolution
catalogue_registered: false
---
```

### Example: case-library — do-attribute-precision.md

```yaml
---
id: do-attribute-precision
module_class: case-library
canonical_path: skill/references/case-library/do-attribute-precision.md
contract_version: "0.2.0.0"
load_when:
  - live pressure involves how divine attributes are predicated
  - DO-6, DO-11, DO-12, or DO-13 confirmed in case-state
  - NS-6 or NS-10 case carries ontological burden
  - composition/dependence or person-multiplicity pressure active
routing_effects:
  - runs downstream of DO family routing-surface confirmation
  - companion to M9 when loaded negative-theological terms present
emits:
  - what_is_withheld_and_why
blocks:
  - attribute-doctrine release before semantic/predication discipline clears
companions:
  - M9-predication-mode
  - definition-discipline
  - V8-bila-kayf-anchor
output_shapes:
  - bounded-single-pass
  - held-pending-upstream
layer_constraint: layer-b-governed
catalogue_registered: true
---
```

---

## What Front Matter Governs

- **Identity:** `id`, `module_class`, `canonical_path` — binds file to catalogue entry; enables path/class drift detection
- **Static load contract:** `load_when` — machine-readable version of the blockquote `> use when:` field; lintable for drift from prose
- **Routing declaration:** `routing_effects`, `emits`, `blocks` — what this module claims to affect; lintable against known IR fields and suppression rules
- **Companion requirements:** `companions` — which other modules should be co-loaded; lintable for catalogue membership
- **Output contract:** `output_shapes`, `layer_constraint` — what shape of output this module may produce; lintable against IR `output_shape` field constraints
- **Stop governance:** `p7_stops_governed` — which P7 stops this file owns or enforces; lintable for consistency with P7-restoration-stops.md

## What Front Matter Does NOT Govern

- **Routing decisions** — the IR owns those at runtime; the contract cannot force dispatch
- **Case-specific activation** — whether `load_when` conditions are met in a given pass is determined by V1 and the diagnostic gate, not by the contract
- **Judgment calls** — prose remains authoritative for application, edge cases, and interpretation
- **Proof of load** — the IR `source_basis` record (with `source_kind: module`) is the proof that loading actually constrained output; the contract is not a substitute for that
- **Precedence order** — routing-precedence.md owns precedence; a contract cannot override it

---

## Prose vs. Front Matter Authority

| Domain | Authoritative source |
|--------|---------------------|
| Machine-readable id, class, path | Front matter (normative for automation) |
| Static trigger conditions | Front matter (lintable) — prose explains judgment |
| Routing effects and emits | Front matter (lintable) — prose explains how |
| Application, edge cases, distinctions | Prose body |
| Pass-specific routing decisions | Diagnostic IR |
| Proof of load in a given pass | IR `source_basis` |

**When prose and front matter conflict:** the prose is authoritative for judgment; the conflict is a lint error to be resolved by updating the front matter (preferred) or flagging the prose for revision.

---

## Failure Modes

**1. Front-matter-as-second-IR**
Populating operative front matter with runtime IR fields (`case_family`, `deformation`, `pattern_profile`, `matched_modules`). These belong to the runtime IR, not to static per-file metadata. The contract layer declares what a file *is*; the IR records what *happened*.

**2. Invented IDs not matching catalogue**
Using an `id` in front matter that does not match the corresponding entry in `module-catalogue.json` (when `catalogue_registered: true`). This defeats the purpose of the contract layer — the file becomes unlinkable by a linter.

**3. Stale `canonical_path` after file rename**
Renaming a file without updating its `canonical_path`. The linter check `canonical_path == actual path` catches this. Always update `canonical_path` when renaming.

**4. Companions listed that do not exist in catalogue**
Listing a companion `id` that has no entry in `module-catalogue.json`. Companions must be valid registered module ids, not prose descriptions or file path fragments.

**5. Using front matter to suppress routing that prose permits**
Adding a `blocks` entry that contradicts the file's own prose routing rules. Front matter must not be used to tighten or loosen routing discipline beyond what the prose defines. If the prose says a route is permitted, `blocks` must not contradict it.

**6. Governance files misclassified as dispatched modules**
Assigning `module_class: diagnostic` (or any non-governance class) to a file like `framework-pipeline.md` or `routing-precedence.md` and setting `catalogue_registered: true`. These files are not dispatched as modules. Use `module_class: governance` and `catalogue_registered: false`.

---

## Migration Strategy

Migration should proceed one module class per session, smallest class first, to keep diffs reviewable:

| Priority | Class | Files | Notes |
|----------|-------|-------|-------|
| 1 | Pilot (done) | M9, P7, routing-precedence, do-attribute-precision | 4 representative files |
| 2 | `technique` | V1–V12, heuristics | 13 files; compact; highest reuse |
| 3 | `tactic` | M1–M9+variants, E1–E4, F1–F3, R1–R3, + unlisted | ~25 files |
| 4 | `procedure` | P1–P6 | 6 files (P7 done in pilot) |
| 5 | `diagnostic` | causal-series-taxonomy, definition-discipline, perfection-criterion-usurpation, proof-method-audit, etc. | ~10 files |
| 6 | `case-library` | do-core, do-second-loop, do-christian-extensions, ns-* profiles, philosophical-usurpation, etc. | ~20+ files |
| 7 | `governance` | framework-pipeline, SKILL.md, diagnostic-ir, output-release, diagnostic-render-contract, etc. | After all dispatched classes done |

Do not migrate an entire class in a single pass unless the class is small and the diffs are brief.

---

## Linting Plan

No toolchain exists yet. The following checks are ready for implementation as a future `scripts/lint-contracts.js` or equivalent:

1. **Required fields:** Every file with a YAML front matter block (`---`) must have `id`, `module_class`, `canonical_path`, and `contract_version`.
2. **Catalogue alignment:** For every file where `catalogue_registered: true` (or `module_class` is not `governance`), `id` + `module_class` must match a `module-catalogue.json` entry exactly.
3. **Path accuracy:** `canonical_path` must equal the actual file path relative to repo root.
4. **Companion validity:** Every string in `companions` must be a valid `id` in `module-catalogue.json`.
5. **No duplicate ids:** Across all operative-contract-bearing files, no two files may declare the same `id`.
6. **Governance class discipline:** `module_class: governance` files must have `catalogue_registered: false` (or `catalogue_registered` absent, which defaults to `false` for governance class).
7. **Schema validation:** Each front matter block must validate against `operative-contract.schema.json`.

---

## Related Files

| File | Relation |
|------|----------|
| `references/diagnostics/module-catalogue.json` | Master id/path/class registry; contracts must align to it |
| `references/diagnostics/operative-contract.schema.json` | JSON schema for YAML front matter; validates all operative contract blocks |
| `references/diagnostics/diagnostic-ir.md` | Canonical runtime dispatch gate; operative contracts do not replace it |
| `references/diagnostics/diagnostic-ir.schema.json` | Runtime IR schema; `matched_modules`, `routing_gate`, `output_shape` are IR fields — not contract fields |
| `references/module-codes.md` | Canonical code reference for all code systems the skill emits; contract `id` values derive from these codes |
| `skill/SKILL.md` | Reference Architecture; operative contracts table added |
| `references/diagnostics/framework-pipeline.md` | Canonical pipeline; the contract layer sits upstream of runtime dispatch, not inside the pipeline execution path |
