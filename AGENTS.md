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
After source changes, confirm the generated runtime is fresh; do not report success from
atomics alone.

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
python tools/check_ir_instance_integrity.py
python tools/check_diagnostic_ir_catalogue_integrity.py
python tools/check_encoding_hygiene.py
```

Before packaging or pushing, run the full applicable checker suite and confirm the generated
runtime is fresh. The canonical smoke artifact gate is repo-local
`smokes/runtime-grounding-v5/`; it is committed regression evidence with trace/verdict
provenance, and `tools/check_smoke_artifacts.py` defaults to that root and compares package
filename/SHA evidence against `docs/release-artifacts.md`.
Package only when explicitly requested.

Current release-line contract: operative front matter must use `contract_version: "0.3.2.0"`
until the project intentionally moves to a later release line. Run:

```bash
python tools/check_frontmatter.py --contract-version 0.3.2.0
```

Historical release references may remain only when they are clearly historical. Current-release
claims, package metadata, generated runtime metadata, and checker samples must not silently retain
older version markers.

## Release Cycle Etiquette

Do not make release moves casually. A release pass must distinguish source readiness,
package artifact readiness, current-package smoke evidence, tag state, and GitHub Release
state.

- Do not tag, create a GitHub Release, upload/replace an asset, push, or publish unless the
  user explicitly approves that exact step.
- Do not use `git add .` for release work. Stage an explicit file list. Keep large smokes,
  raw model transcripts, local helper scripts, `.daee/`, `level3-runs/`, temporary owner
  lists, local machine paths, and scratch artifacts unstaged unless the user explicitly
  says otherwise.
- Historical smokes are historical regression evidence. Do not claim current-release
  package-bound smokes unless they were regenerated against the current package filename and
  SHA and are marked current-release.
- If atomics change, rebuild `skill/` and run freshness checks before reporting success.
- If package contents or release-artifact docs change, rebuild the `.skill` package, compute
  SHA256, size, entry count, and top-level entries, then update `docs/release-artifacts.md`
  before any release asset update.
- Git pushes do not update GitHub Release assets. If `skill/` or package-facing docs change after
  a release, rebuild the package and explicitly replace the release asset before claiming the
  release page reflects the patched state.
- Before any tag/release, run a hard-gate check: local/remote HEAD coherence, tag absence or
  intended tag state, GitHub Release absence or intended update state, version-marker search,
  frontmatter contract check, generated-from-atomics freshness, package-shape validation,
  release-artifact hash coherence, smoke/evidence boundary check, public docs coherence, CI
  status, source-neutrality/local-path sweep, and `git diff --check`.
- If replacing an existing GitHub Release asset on the same tag, say plainly that the asset
  hash changed, update the release notes/artifact docs, and verify the release page afterward.
- Do not create a patch tag such as `v0.3.2.1` unless explicitly instructed. If a same-version
  release asset is being corrected, keep it on the existing release line and document the
  rebake.
- Before committing release work, show `git status --short`, `git diff --cached --stat`,
  `git diff --cached --name-only`, and `git diff --cached --check`.

Release claims must stay narrow and honest:

- Level 3 is deterministic routing given extracted features, not deterministic feature
  extraction or guaranteed transformer execution.
- Scriptless runtimes visibly fall back to Level 1/2.
- Pure-Hermes parity, fixture-18 resolution, all-runtime Level 3, current-release smokes,
  broad codons, and owner packs are not claimed unless explicitly proven and documented.
- Any run using `--simulate-output` is only simulated structural route/check verification. It
  must not be reported as a behavioral smoke, model-execution smoke, or Level 1/2 shrinkage
  recovery.
- Codex CLI final-answer output may compress hard Level 3 executions. For golden-depth real
  model-execution smokes, retain the governed response in an ignored `output.model.md` file
  written by the runtime, then run `check_execution.py` against that file. This is real model
  output, not simulated evidence, but it is still local smoke evidence unless package/release
  provenance is explicitly recorded.
- Passing `check_execution.py` and any `quality_gate` is necessary but not sufficient for a
  golden-depth claim. Golden-depth claims require adversarial content review against the
  relevant anchor output across owner/TTP execution, operative sources, noetic diagnosis,
  restoration force, source-status discipline, and da'wah usefulness.

## Regression Audit Etiquette

When a model-output regression is reported, do not declare it fixed because the spec allows
the desired behavior. Compare the relevant outputs, classify likely causes, patch only
source-of-truth surfaces, rebuild, verify, and state whether a manual model rerun is still
required.

- For Level 1/2 render regressions, preserve both governance and depth: compact does not mean
  thin; Layer A must stay compact but load-bearing; Layer B must stay burden-complete,
  case-specific, owner-floor faithful, and restoration-directed.
- Active TTP/operator submoves must not be consolidated. Same burden-cycle does not mean a
  merged operation: each active TTP receives its own target -> operation -> result, or the
  output is PARTIAL if limits prevent distinct execution.
- `R(H,Delta)` is a real state-transition judgment, not a formatting marker. It decides
  whether to continue, hold/defer, skip, reroute boundedly, or close.
- Structural attachment fidelity is required. Marker presence is not execution, and the same
  tokens in a different order do not preserve the same state. Keep each burden submove
  (`ⁿBᵢ` / `nBi`, with `B1.s1` as checker-compatible alias) -> owner-floor `Target` /
  `Operation` / `Result` -> `Land(B)` -> `R(H,Delta)` -> next decision locally attached;
  grouped reasoning, grouped owner markers, or checker-shaped blobs are structural-flattening
  failures even if every label appears somewhere.
- Hard-case pressure execution is required. Labels, owner IDs, Target/Operation/Result syntax,
  and route markers count only when the prose pressures the actual premise, criterion, warrant,
  source-frame, theological predicate, testimony question, register-hold, or restoration vector.
  Level 3 may expose this as `pressure_dimensions`; Level 1/2 must obey the same internal
  governance principle without printing raw `pressure_dimensions` in public/default output.
- For hard Level 3 cases, the execution must reconstruct the noetic frame before argument:
  claim level, pattern/deformation, reason category, concealment, DO-orient, live burden,
  source-status/noetic-frame, held/released state, and gate/release decision. A checker-shaped
  route answer without that frame is PARTIAL even if it names the right owners.
- TST-style hard smokes are canaries, not the architecture. Do not add TST, Richard-Lael,
  Satanism, or one-golden-output-specific routing unless a future task explicitly authorizes a
  bespoke owner. Fixes should generalize across hard/compound/deformed noetic structures and
  preserve family-local pressure rather than flattening kalam, falsafah, predication,
  transmission, grief/register, naturalist, or source-worldview cases into one blob.
- These checks are not generic answer-polish. They actualize the skill thesis:
  surface discourse -> typed noetic state -> pressure-dimensioned owner execution -> `Land(B)`
  -> `R(H,Delta)` -> STOP/HOLD/PARTIAL/RECURSE. The aim is to prevent collapse into
  argument-bank prose, detached route labels, checker-shaped scaffolding, source lists without
  operation, or restoration summaries without noetic state change.
- Qurʾān/ḥadīth evidence, when operative, should be visually clean and immediately explained
  as diagnostic/restorative work; do not collapse central revealed text into prose or pad with
  citations.
- Use normalized transliteration in prose where the file supports Unicode: fiṭrah, ʿaqīdah,
  ḍarūrī, naẓarī, waḥy, kalām, Ashʿarī, Māturīdī, Muʿtazilī, Qurʾān, ḥadīth, ḥudūth,
  bilā kayf, hawā, and iʿrāḍ. Preserve ASCII keys, filenames, schema fields, YAML/JSON keys,
  and code identifiers unless a migration is explicitly requested.
- Run `python tools/check_encoding_hygiene.py` after transliteration or diacritic edits. Mojibake,
  UTF-8 BOM residue, malformed YAML front matter, and non-ASCII YAML/JSON keys in code/data are
  release blockers unless intentionally and safely migrated.
- Controlled terminology: `kalām` is Speculative Theology in this repo, not "Rational Theology".
  Ashʿarī and Māturīdī labels are varied speculative-theological families, not monoliths. In
  operative repo terminology, reserve "Islamic scholar" / "Islamic scholarship" for
  Salafī/Atharī-aligned scholarship; use labels such as kalām theologian, speculative theologian,
  school theologian, mutakallim, philosopher, school authority, or later theological figure for
  non-Atharī kalām/falsafah figures. Keep this as source-status discipline, not polemical clutter.

## Level 3 Protocol

Level 3 is additive route-first execution for Codex/script-capable runtimes.

- `/daee-epistemics [input]` should use Level 3 by default in Codex when bundled scripts are
  available.
- Scriptless runtimes must visibly fall back to Level 1/2 behavior.
- `route.py` is deterministic given extracted features; feature extraction includes span-backed
  interpretive components, and transformer execution remains probabilistic.
- Level 3 does not solve fixture-18 capability ceilings and does not justify pure-Hermes parity
  claims.
- `continuation_queue` is a planned route, not an unconditional checklist. After each `Land(B)`,
  `R(H,Delta)` must decide whether to continue, hold/defer, skip, bounded-reroute, or close.

## Skill Architecture

Current runtime notation is owned by
`atomics/skill/references/diagnostics/recursive-state-transitions.md`.

```text
Input -> IR(N,m,τ,σ) -> B -> {s1...sn} -> Land(B) -> R(H,Δ) -> STOP/HOLD/PARTIAL/RECURSE
```

Burden/submove notation uses `ⁿBᵢ` for the i-th operative submove inside the n-th burden-cycle,
with `nBi` as the plain-text mirror. Example: `¹B₁` / `1B1` is burden 1, submove 1;
`¹B₂` / `1B2` is burden 1, submove 2; `²B₁` / `2B1` begins only after `Land(¹B) ->
R(H,Δ)` licenses burden 2. Existing `B1.s1` / `B1.s2` notation remains an accepted
legacy/checker alias.

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
- Release smoke artifacts must carry provenance in `trace.md` or `verdict.md`: package filename,
  SHA256, model/host, invocation mode, prompt pointer, timestamp, and live-run versus
  handcrafted-regression classification. SHA mismatches must be explicitly marked as historical
  regression evidence.
- `Operation:` lines must begin with the closed operative verbs named in
  `recursive-state-transitions.md`.
- Non-operative source-status use requires the operative-warrant sentence with the
  specific non-premise clause.
- Held material must remain semantically held until an explicit release marker appears
  in a preceding state/noetic re-read.

When addressing a repo audit, catalogue each reported problem in `TODO.md`, map it to
source/checker/fixture/runtime surfaces, then close or leave it active with a concrete
remaining verification task.

If background agents or subagents are unavailable, reuse or close existing agents, or run
independent local audit lenses and label that honestly. Specialist/architecture audits do not
replace mechanical release-manager checks. Classify every finding as release-blocking,
patch-before-commit, non-blocking, deferred, or historical/acceptable.

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

## Package Shape Rule

For the v0.3.2.0 package shape, the `.skill` archive root may contain:

```text
SKILL.md
references/
data/
scripts/
tests/
compiled-module-map.json
build-manifest.json
README.md
```

The archive must not contain:

```text
skill/SKILL.md
atomics/
tools/
docs/
build/
.git/
smokes/
level3-runs/
.daee/
__pycache__/
```

Package the contents of `skill/`, not the `skill/` directory itself.
Local Hermes helpers, temporary owner lists, raw campaign artifacts, local absolute paths, and
machine-specific files are not package content.
The `SKILL.md` frontmatter `description` must be 1024 characters or fewer; keep metadata concise
and put richer terminology in the body/reference surfaces. `tools/check_frontmatter.py` and
`package.ps1` must catch this before release.

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
