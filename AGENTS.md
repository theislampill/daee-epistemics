# AGENTS.md

## Repository Rule

This repository has a canonical atomized source tree and a generated runtime tree.

- `atomics/skill/` is the canonical editable source.
- `skill/` is generated compiled runtime output.
- `tools/` contains compiler/checker scripts.
- `tests/routing-fixtures/` contains static routing parity fixtures.
- `docs/` contains architecture, audit, and workflow notes.

Do not hand-edit generated files under `skill/`.
Edit `atomics/skill/`, then regenerate `skill/`.

## Normal Workflow

After editing source files under `atomics/skill/`, run:

```bash
python tools/build_framework_pipeline.py
python tools/build_compiled_runtime.py
python tools/check_framework_pipeline.py
python tools/check_compiled_runtime_freshness.py
python tools/check_compiled_module_boundaries.py
python tools/check_stub_integrity.py
python tools/check_consolidation_call_budget.py
python tools/check_routing_parity.py
python tools/check_routing_parity.py --strict
python tools/check_recursive_traversal_governance.py
python tools/check_render_modes.py
python tools/check_frontmatter.py
python tools/check_coverage.py
python tools/check_recursion_collapse_noetic_frame.py
python tools/check_metacompliance_current_canon.py
python tools/check_smoke_artifacts.py
```

Before packaging or pushing, run the full applicable checker suite and confirm the generated
runtime is fresh. When `smokes/runtime-grounding-v5/` exists, include the smoke artifact gate.
Package only when explicitly requested.

## Skill Architecture

Current runtime notation is owned by
`atomics/skill/references/diagnostics/recursive-state-transitions.md`.

```text
Input -> IR(N,m,τ,σ) -> B -> {s1...sn} -> Land(B) -> R(H,Δ) -> STOP/HOLD/PARTIAL/RECURSE
```

The compiled runtime must preserve this route:

```text
SKILL.md
-> runtime-foundation
-> runtime-diagnostic-core
-> runtime-phase2-passes
-> runtime-dispatch-gate
-> runtime-output-governance
-> selective omnibus sections
-> post-render gate
-> STOP / HOLD / RECURSE / PARTIAL
```

Do not bypass:

- V1 diagnosis
- Phase 2 passes
- Diagnostic IR
- routing precedence
- P7 stop discipline
- output-release governance
- post-render state/noetic re-read

## Render And Metacompliance Rules

The skill thesis is diagnostic compiler first, not argument bank. Do not let default
mode become clean essay cosplay.

- Default `/daee-epistemics` must render the compact DSL/IR header, bounded governed
  Layer B, State/noetic re-read, one Restorative Response, and one final Closing Formulation.
- Default Layer B includes Hidden Premises, Core Formulation local to each released operation,
  bounded operative submoves, and TTP/operator trace when a named operator performs work.
- `/daee-epistemics:dsl` is the concise DSL / IR printout mode.
- `/daee-epistemics:audit` is deprecated as public output and retained only for
  internal/development audit compatibility.
- Default output must not expose raw Diagnostic IR, full Case State, `matched_modules`,
  route ledger, load ledger, route IDs, PF codes, or owner dumps.

False-compliance guards are executable, not merely prose:

- Minimal-pair fixtures must prevent topic-to-IR fingerprinting.
- Runtime-grounding smoke artifacts must be cleanly separated: `output.md` is user-facing default
  render only, while runtime proof and verdict language stay in `trace.md` and `verdict.md`.
- Hard smoke PASS verdicts below the depth floor, cross-fixture contamination, and repeated generic
  paragraphs across unrelated outputs must fail the smoke artifact checker.
- `Operation:` lines must begin with the closed operative verbs named in
  `recursive-state-transitions.md`.
- Non-operative source-status use requires the operative-warrant sentence with the
  specific non-premise clause.
- Held material must remain semantically held until an explicit release marker appears
  in a preceding state/noetic re-read.

When addressing a repo audit, catalogue each reported problem in `TODO.md`, map it to
source/checker/fixture/runtime surfaces, then close or leave it active with a concrete
remaining verification task.

## Generated Runtime Rules

The compiled runtime under `skill/` may contain old atomized paths such as:

```text
references/tactics/M9-predication-mode.md
```

In the compiled runtime these are canonical source identities, not literal file paths unless the file exists.

Resolve them through:

```text
skill/compiled-module-map.json
```

Then load the containing runtime bundle or omnibus section.

Do not use omnibus filenames as `matched_modules`.

Correct:

```text
matched_modules: M9-predication-mode
```

Incorrect:

```text
matched_modules: OMNIBUS-tactics
```

## Module Identity Rules

Always preserve:

- original module IDs
- `module_class`
- `canonical_path`
- YAML front matter in atomized source
- source-basis traceability
- `SOURCE_SHA256` in compiled sections

Never change module IDs casually.

## Claude Packaging Rule

Claude expects a `.skill` archive whose root contains:

```text
SKILL.md
references/
compiled-module-map.json
build-manifest.json
```

The archive must not contain:

```text
skill/SKILL.md
atomics/
tools/
docs/
tests/
build/
.git/
```

Package the contents of `skill/`, not the `skill/` directory itself.

## Common Failure Modes

Avoid:

- editing generated `skill/` files directly
- forgetting to rebuild after editing `atomics/skill/`
- treating omnibus membership as active dispatch
- using omnibus filenames in `matched_modules`
- deleting atomized source files
- weakening Diagnostic IR discipline
- weakening P7 STOP / HOLD / RECURSE / PARTIAL discipline
- turning recursive traversal into argument dumping
- declaring STOP while an eligible live noetic burden remains
- changing packaging so `SKILL.md` is not at archive root

## Where To Start

For source architecture:

```text
atomics/skill/SKILL.md
atomics/skill/references/diagnostics/diagnostic-ir.md
atomics/skill/references/diagnostics/framework-pipeline.md
atomics/skill/references/diagnostics/routing-precedence.md
atomics/skill/references/procedures/P7-restoration-stops.md
```

For compiled-runtime tooling:

```text
tools/build_compiled_runtime.py
tools/check_routing_parity.py
tools/check_metacompliance_current_canon.py
tools/compiled_runtime_lib.py
```

For docs:

```text
docs/source-vs-runtime-layout.md
docs/compiled-runtime-tools.md
docs/routing-parity-fixtures.md
docs/compiled-runtime-verification.md
```
