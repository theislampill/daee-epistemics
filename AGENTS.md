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

## Operating Protocol

Use RTFM, tagged context, structured output, OODA, RACI, MoSCoW, and RFC/ADR as
lightweight governance, not extra ceremony.

- RTFM means read the repository manuals first: `AGENTS.md`, `TODO.md`, `README.md`,
  canonical atomics, generated runtime, checkers, and relevant docs before changing
  architecture-facing behavior. For source/runtime disagreements, canonical atomics
  plus passing generated-runtime freshness win over docs prose.
- Tagged context means substantial audits and implementation reports should label the
  working boundary: `[source]`, `[runtime]`, `[checker]`, `[fixture]`, `[smoke]`,
  `[docs]`, `[package]`, `[release]`, `[decision]`, or `[blocker]` as applicable.
- Structured output means reports should separate context, decision, changed files,
  verification, smoke evidence, risks, and remaining blockers. Do not bury readiness
  claims inside narrative prose.
- OODA loop: Observe repo state and evidence; Orient against canonical package/runtime
  boundaries; Decide the smallest honest patch or blocker classification; Act by
  editing source first, rebuilding when needed, and running the matching checks.
- RACI for nontrivial work: Responsible = the patching agent; Accountable = the user/
  maintainer approving release and schema decisions; Consulted = canonical atomics,
  generated runtime, checkers, fixtures, and smoke evidence; Informed = `TODO.md`,
  audit docs, and navigation docs updated after the decision.
- MoSCoW priority belongs in TODO/audit entries: Must = release or truth-boundary gate;
  Should = important hardening that can miss the current commit; Could = optional
  coverage or ergonomics; Won't = explicitly out of scope for the current release line.
- RFC/ADR discipline: architecture, schema, package-boundary, release-line, or public
  runtime-surface changes need a decision record in `TODO.md` or `docs/audits/` with
  status, evidence, consequences, and rollback/defer criteria. `docs/index.html` is
  never the sole RFC/ADR or source of truth.
- Interface contracts are preserved unless intentionally migrated. If a contract changes,
  update all producers, consumers, schemas, tests, examples, and docs together, or report
  the exact incomplete edge. Keep parsing, validation, routing, execution, persistence,
  rendering, and documentation separate unless a clear owning module has reason to combine
  them. Owner first: identify the owning file, module, or schema before editing; patch the
  owner rather than downstream symptoms.

## Normal Workflow

After editing source files under `atomics/skill/`, run:

```bash
python tools/build_framework_pipeline.py
python tools/build_compiled_runtime.py
python tools/check_framework_pipeline.py
python tools/check_compiled_runtime_freshness.py
python tools/check_package_shape.py
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
python tools/check_register_formalism_bridge.py
python tools/check_smoke_artifacts.py
python tools/check_ir_instance_integrity.py
python tools/check_diagnostic_ir_catalogue_integrity.py
python tools/check_encoding_hygiene.py
```

Before packaging or pushing, run the full applicable checker suite and confirm the generated
runtime is fresh. Smoke artifacts are local evidence unless a task explicitly authorizes a
tracked fixture suite. Do not commit `smokes/`, `.daee/`, `level3-runs/`, raw model outputs,
or local transcripts. `tools/check_smoke_artifacts.py` runs embedded regression samples by
default; pass `--root` for a local smoke suite, and use `--require-current-release-smokes`
only when package-bound current-release smokes have been truthfully regenerated. Package
only when explicitly requested.
`tools/check_noetic_field_banner_samples.py` is a tracked dev-local regression checker. When
noetic-field banner or algebraic-control retained smokes are part of a patch, run it against
those local artifacts. Its PASS is not package/release proof.

Current release-line contract: operative front matter must use `contract_version: "0.4.0.0"`
until the project intentionally moves to a later release line. Run:

```bash
python tools/check_frontmatter.py --contract-version 0.4.0.0
```

Historical release references may remain only when they are clearly historical. Current-release
claims, package metadata, generated runtime metadata, and checker samples must not silently retain
older version markers.

Current dirty work after the `v0.4.0.0` tag is `v0.4.1.0` candidate cleanup/hardening work.
That candidate label does not migrate operative `contract_version` by itself.

## Release Cycle Etiquette

Do not make release moves casually. A release pass must distinguish source readiness,
package artifact readiness, current-package smoke evidence, tag state, and GitHub Release
state.

- Do not tag, create a GitHub Release, upload/replace an asset, push, or publish unless the
  user explicitly approves that exact step.
- `.github/workflows/release-skill.yml` is a manual artifact-build workflow only: it builds and
  uploads workflow artifacts, but must not be treated as tag creation, GitHub Release publishing,
  or package-bound smoke proof.
- `.github/workflows/release-skill.yml` is a manual artifact-build workflow only: it builds and
  uploads workflow artifacts, but must not be treated as tag creation, GitHub Release publishing,
  or package-bound smoke proof.
- Do not use `git add .` for release work. Stage an explicit file list. Keep large smokes,
  raw model transcripts, local helper scripts, `.daee/`, `level3-runs/`, temporary owner
  lists, local machine paths, and scratch artifacts unstaged unless the user explicitly
  says otherwise.
- Do not stage canonical-package-excluded harness roots or run artifacts unless a task explicitly
  authorizes repo/dev harness work: `skill/data/`, `skill/scripts/`, `skill/tests/`,
  `atomics/skill/data/`, `atomics/skill/scripts/`, `atomics/skill/tests/`, `route_plan.json`,
  `features.json`, `validation.json`, `reconstruction.json`, `execution_verdict.json`,
  `execution_prompt.md`, `execution_blocked.md`, `partial_banner.md`, `retry_prompt.md`,
  `output.simulated.md`, or `output.model.md`.
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

- The optional script-capable route/check harness is deterministic routing given extracted
  features, not deterministic feature extraction or guaranteed transformer execution.
- Scriptless runtimes use the canonical compact DSL-governed surface; they are not prose-only
  fallback.
- Pure-Hermes parity, fixture-18 resolution, all-runtime script-harness claims, current-release smokes,
  broad codons, and owner packs are not claimed unless explicitly proven and documented.
- Any run using `--simulate-output` is only simulated structural route/check verification. It
  must not be reported as a behavioral smoke, model-execution smoke, or scriptless shrinkage
  recovery.
- Codex CLI final-answer output may compress hard script-harness executions. For golden-depth real
  model-execution smokes, retain the governed response in an ignored `output.model.md` file
  written by the runtime, then run `check_execution.py` against that file. This is real model
  output, not simulated evidence, but it is still local smoke evidence unless package/release
  provenance is explicitly recorded.
- For scriptless installed-skill hard canaries, `codex exec --output-last-message` writes only
  the final agent message and is not proof of full-depth canonical execution. Use ignored
  file-retained `output.md` artifacts for behavioral scoring, and treat terminal summaries as
  provenance/status only.
- Passing `check_execution.py` and any `quality_gate` is necessary but not sufficient for a
  golden-depth claim. Golden-depth claims require adversarial content review against the
  relevant anchor output across owner/TTP execution, operative sources, noetic diagnosis,
  restoration force, source-status discipline, and da'wah usefulness.

## Regression Audit Etiquette

When a model-output regression is reported, do not declare it fixed because the spec allows
the desired behavior. Compare the relevant outputs, classify likely causes, patch only
source-of-truth surfaces, rebuild, verify, and state whether a manual model rerun is still
required. For scriptless compact-DSL behavioral regressions, inspect the actual model output against the
golden or comparison anchor for burden count, per-burden Layer A re-entry, state/noetic
re-reads, source-operation burdening, owner/TTP pressure, and restoration force. Script-harness
checker success or spec permission does not prove scriptless compact-DSL recovery.

### Atomic Audit And Refactor Discipline

Atomics audits are power-first, not length-first. Do not mark a long, abstract, or repeated
file as fluff unless the audit shows that it weakens execution, conflicts with an owner,
buries the operative rule, causes topic-tour recursion, overcollapse, source-stack compression,
Layer A overgrowth, Layer B flattening, or less visible TTP/operator activation.

Before slimming or merging atomics, classify the file's operative role and power contribution:
diagnostic/control surface, Layer B operation, `Land(B)` / `R(H,Delta)` governance,
source-status/noetic-frame discipline, first-/second-/higher-order noetic ordering,
TTP/operator owner floor, restoration, package metadata, or repo/dev harness. Classify overlap
as load-bearing reinforcement, harmless duplication, confusing duplication, contradictory
duplication, stale duplication, verbose-but-necessary, or removable fluff. Some reinforcement is
intentional for weaker/scriptless runtimes and must not be removed unless the surviving owner is
clear, earlier-loaded, and smoke-proven.

Every dispatchable owner/TTP must have source-level trigger, target, operation, result, and
exit/land clarity, or be explicitly marked pass-through, diagnostic-only, marker-only, or
repo/dev-harness-only. Distinguish the broad compiled registry from the optional script-harness
covered-scope catalogue. When the user forbids edits during an audit, record TODO-intended
findings in the audit report instead of modifying `TODO.md`.

### Operator Child-Mode Hardening Protocol

When a broad parent owner is correct but under-factorized, use the evidence-gated path before
creating any new owner pack:

1. Trace owner first.
2. Patch the existing parent owner before creating a new owner.
3. Add compact child-mode rows only when they sharpen entry criteria, false trigger, target,
   operation, result, `Land(B)`, `R(H,Delta)`, collapse radius, held routes, and guardrail
   consequences.
4. Add label-stripped static routing fixtures.
5. Rebuild generated runtime when atomics change.
6. Run the applicable routing/checker suite.
7. Add retained ignored local live samples only after static patch review.
8. Add a dev-local checker only after live samples are semantically accepted.
9. Require positive controls and negative controls before accepting the checker.
10. Preserve the evidence boundary: local ignored samples are not package/release smoke proof.
11. Do not proceed to the next owner family until the current family has an accepted static-only
    boundary, accepted local execution evidence, or accepted dev-local checker evidence.

TTP label presence is not execution. Child-mode row presence is not execution. Static fixture
success is not live behavior proof. Local live smoke evidence is not package/release proof.
Dev-local checker PASS is not universal semantic grading. Package/release smoke proof requires
package-bound provenance and explicit release authorization. `.daee/` remains ignored local
evidence unless explicitly authorized otherwise. Never use `git add .` for this work.

SOLID / GRASP may be used as lightweight repo/dev design heuristics for owner placement,
checker cohesion, and evidence boundaries. They are not runtime doctrine, public skill grammar,
or substitutes for SSOT, owner-first tracing, ACID, and smoke-before-claim.

SOLID mapping: Single Responsibility means each owner/checker has one evidence role; Open/Closed
means extend parent owners through child modes before new owner packs; Liskov means child modes
must satisfy the parent owner-floor; Interface Segregation means static fixtures, local live
samples, dev-local checkers, and package smokes are separate evidence interfaces; Dependency
Inversion means checkers depend on repo contracts and repo-relative paths, not local machine paths
or summaries.

GRASP mapping: Information Expert means patch the file that owns the operation; Controller means
checkers/scripts validate evidence while owners do not become scripts; Low Coupling / High
Cohesion means avoid broad packs when existing owners can carry child modes; Indirection means
compiled-module-map, schema-light registers, and local checkers separate source/runtime/evidence;
Protected Variations means do not hard-migrate schemas or release claims without explicit contract
migration; Pure Fabrication means dev-local checkers are allowed repo tools but not package
identity.

### Scriptless Compact DSL Behavioral Coercion Memory

v0.3.2.0 restored v0.3.1.0-style top-level behavioral coercion for scriptless compact DSL
governance. Default `/daee-epistemics` is the canonical compact DSL-governed surface, not
prose-only mode. DSL/IR is integral to the skill's anti-hallucination, routing,
burden-accounting, and restoration discipline. `/daee-epistemics:dsl` is expanded
diagnostic/IR visibility; it is not the first place DSL appears. The optional script-capable
route/check harness can help Codex/dev/CI, but it is not the public identity of the skill and
is not required for ordinary portability. If a model cannot produce the compact DSL-governed
surface from the package alone, that is a runtime/model compliance limitation, not a reason
to redefine the skill as prose-only.

Default scriptless compact DSL output is burden-governed, not concise-answer-governed.
Compact means after burden accounting; it never licenses fewer live burdens, fewer necessary
TTP submoves, thinner source operation, or final-restoration source dumping.

For every released burden-cycle, compact Layer A -> governed Layer B -> state/noetic reread
must remain locally attached. If reread leaves another input-anchored burden live and no
HOLD/PARTIAL/limit/register gate blocks it, continue in the same response. Same-burden
collapse does not collapse active submoves. Imported tribunal pressure, hujjah/accountability,
coercive-guidance pressure, source-worldview consequence, mercy/justice, fitrah/ayat,
Creator-right, repentance/return, testimony, and predicate-source work must either land
burden-locally or be explicitly held/PARTIAL.

Final restoration cannot be the first place live source architecture appears. Named hard-case
smokes are canaries, not architecture. Do not add named-person, movement-specific, or
one-golden-output-specific runtime logic unless explicitly instructed.

- For scriptless compact-DSL render regressions, preserve both governance and depth: compact does not mean
  thin; Layer A must stay compact but load-bearing; Layer B must stay burden-complete,
  case-specific, owner-floor faithful, and restoration-directed.
- Compactness removes padding, source parade, and framework dumping. It does not reduce live
  burden count, distinct TTP submoves, source-operation density, per-burden Layer A re-entry,
  or state/noetic re-reads.
- Hard noetic cases may require long outputs. Length is not the target; burden-complete
  restoration is. A 20-25kb answer that closes with live burdens still unlanded is a failure,
  while a 30-80kb answer can be correct when it is source-operative, TTP-complete, and not
  padded. If response/runtime limits prevent full traversal, mark PARTIAL and name the next
  live burden or blocked submove rather than closing thinly.
- Output depth is determined by live noetic burden, not prompt length, apparent simplicity, or
  surface size. Short slogans and small questions may contain dense inherited assumptions,
  proof-order inversions, source-status confusion, predication pressure, deformation, grief/register
  signals, or concealed worldview criteria. Brevity is licensed only after diagnostic burden
  accounting; compact output is compression after burden accounting, not shortcut before diagnosis.
- Active TTP/operator submoves must not be consolidated. Same burden-cycle does not mean a
  merged operation: each active TTP receives its own target -> operation -> result, or the
  output is PARTIAL if limits prevent distinct execution.
- Active TTP/owner invocation is not satisfied by naming the owner, tactic, specialty marker,
  or operation family. The operation must produce a local Target -> Operation -> Result, change
  claim-state, and then pass through `Land(B)` / `R(H,Delta)` before it can be counted as
  executed.
- Final-synthesis loophole: hard-case source architecture, mercy/worship-worthiness,
  testimony/transmission, predication/category, source-worldview consequence, and other
  source-governed material cannot first appear as final restoration. If that material is live,
  it must land as a burden-local submove or licensed next burden, or be explicitly held/PARTIAL
  before closure.
- `R(H,Delta)` is a real state-transition judgment, not a formatting marker. It decides
  whether to continue, hold/defer, skip, reroute boundedly, or close.
- New burden-cycle ordering: a new burden requires a distinct input-anchored noetic function
  licensed by `Land(B) -> R(H,Delta)`. Practical application, source maps, concise wording,
  warnings, do/don't guardrails, and recaps of already-landed material usually belong in the
  current Layer B or final Restorative/Application Response unless the state re-read proves a
  genuinely new unresolved noetic pressure. Source-worldview may become its own burden when
  the worldview/source-frame itself is criterion-bearing or explicitly requested; practical
  response guidance is not automatically a burden.
- Anti-overcollapse guard: same-burden collapse is licensed only when same function/source-frame/
  claim-cluster/noetic target really holds. Do not absorb distinct accountability, hiddenness/
  coercive-guidance, punishment/mercy, source-worldview, predication, transmission/testimony,
  grief/register, or family-local proof-method burdens into one omnibus tribunal. Release the
  next burden after `Land(B) -> R(H,Delta)`, or explicitly HOLD/PARTIAL it.
- Burden recursion follows live noetic order, not topic count. First-order surface claims,
  second-order criteria/warrants/proof-methods/source-authority/testimony standards/moral
  tribunals, and higher-order source-worldview/register/source-status/noetic-frame pressures
  may each require release when they remain live after `Land(B) -> R(H,Delta)`. Do not recurse
  because more content is available; do not collapse distinct orders into one omnibus burden.
  This protects noetic function, reliable warrant-process, and foundational ordering: what is
  treated as basic, what is inferred, which hidden premise/source-rule/tribunal is acting as a
  foundation, and whether the operation is truth-directed or deformed by hawā, inherited
  assumptions, identity pressure, grief, source inversion, desire, imported criteria, selective
  testimony rules, scientistic filters, or anti-revelation priors.
- Practitioner framing is not automatically NewB. Requests to respond, deal with a claim,
  bring sources, or dismantle a belief system require source-operation inside the relevant
  burdens and a usable Restorative/Application Response; they do not by themselves license a
  late practical-handling burden unless an unresolved practitioner constraint remains live.
- Hard source-request cases must not compress distinct source functions into one citation stack.
  Each materially distinct source function must operate locally on the burden before `Land(B)`;
  source maps summarize after landing and do not replace source operation.
- Hard canary recovery is a behavioral gate, not a static/package-shape gate. A complete-looking
  hard compound/source-request smoke below 30k characters fails unless it visibly says `PARTIAL`
  and names the missing live burden/TTP/source function. 30k-35k remains suspect and must pass
  the owner/source/closure matrix. Above 35k is eligible for review, not automatic pass.
- The v0.3.2.0 moral-protest/source-worldview canary showed two distinct regression modes:
  smooth short closure and owner-label compliance without enough local Layer B depth. Keep the
  depth floor early in the execution mandate: compact means no padding or route dump, not fewer
  source-operative burden bodies. A recovered normal file-retained smoke must show real owner
  execution, source-local work, P1/P7 closure discipline, M1/M1-P where worship-veto/self-grounding
  is live, M9 where divine-predicate/category transfer is live, and a visible hard-case
  `closure audit:` before final restoration.
- Same-burden collapse must preserve operator identity. Inside a valid burden-cycle, every
  materially active TTP/operator still executes visibly as a local submove: why this operator
  is live for the current burden, its target, its operation, its result/state change, and how
  that result contributes to `Land(B)`. Use the actual matched owner/TTP where structurally
  warranted; do not replace FPD, M1/M1P, M8, M9, V2, P1/P7, transmission, predication,
  register-hold, or family-local operators with generic verbs such as expose, correct, warn,
  or clarify.
- Structural attachment fidelity is required. Marker presence is not execution, and the same
  tokens in a different order do not preserve the same state. Keep each burden submove
  (`¹B₁` preferred, `1B1` fallback, `B1.s1` checker-compatible alias) -> owner-floor `Target` / `Operation` /
  `Result` -> `Land(B)` -> `R(H,Delta)` -> next decision locally attached; grouped reasoning,
  grouped owner markers, or checker-shaped blobs are structural-flattening failures even if
  every label appears somewhere.
- Hard-case pressure execution is required. Labels, owner IDs, Target/Operation/Result syntax,
  and route markers count only when the prose pressures the actual premise, criterion, warrant,
  source-frame, theological predicate, testimony question, register-hold, or restoration vector.
  The optional script harness may expose this as `pressure_dimensions`; scriptless compact DSL
  output must obey the same internal governance principle without printing raw
  `pressure_dimensions` in public/default output.
- For hard script-harness cases, the execution must reconstruct the noetic frame before argument:
  claim level, pattern/deformation, reason category, concealment, DO-orient, live burden,
  source-status/noetic-frame, held/released state, and gate/release decision. A checker-shaped
  route answer without that frame is PARTIAL even if it names the right owners.
- Named hard-case smokes are canaries, not the architecture. Fixes should state the general
  noetic/family class they strengthen, generalize across hard/compound/deformed noetic
  structures, and preserve family-local pressure rather than flattening kalam, falsafah,
  predication, transmission, grief/register, naturalist, or source-worldview cases into one blob.
- These checks are not generic answer-polish. They actualize the skill thesis:
  surface discourse -> typed noetic state -> pressure-dimensioned owner execution -> `Land(B)`
  -> `R(H,Delta)` -> STOP/HOLD/PARTIAL/RECURSE. The aim is to prevent collapse into
  argument-bank prose, detached route labels, checker-shaped scaffolding, source lists without
  operation, or restoration summaries without noetic state change.
- DSL/IR is a reconstruction-faithful control bottleneck. If the rendered prose or trace cannot
  recover the live burden, selected operator, nearest held/deferred alternatives, expected
  `Land(B)`, and governance verdict, the output is plausible commentary rather than governed
  execution.
- Natural-language diagnostic explanations must be reconstruction-faithful: state ->
  explanation -> reconstructed state. A rendered diagnostic explanation, compact Layer A,
  trace, audit panel, or local smoke output must be able to recover the relevant surface signal
  (`D0`), selected or held `N`/`N_space`, live burden, claim level / pattern profile, live
  registers (`heart`, `xi`, `Omega`, `mu`, `kappa`, `sigma`), selected owner/child mode,
  target, operation, result, held routes, collapse radius / Delta-kappa, `Land(B)`,
  `R(H,Delta)`, and STOP/HOLD/PARTIAL/RECURSE decision when those fields are live; otherwise it
  is decorative prose, not governed diagnostic explanation.
- Scriptless compact-DSL regression findings should be mapped to optional script-harness
  route/check/fixture coverage wherever
  the failure can be expressed as route state, owner pressure, source function, held-route behavior,
  or negative output checking. "Manual rerun required" does not defer machine-testable analogues.
- Terminology boundary: specialist audit passes may use SPECOP-style lenses, but SPECOP is not a
  runtime owner, TTP family, route class, module class, or user-visible skill grammar. Keep audit-side
  specialist operation language separate from daee TTP/owner execution.
- Qur'an/hadith evidence, when operative, should be visually clean and immediately explained
  as diagnostic/restorative work; do not collapse central revealed text into prose or pad with
  citations.
- Preserve ASCII keys, filenames, schema fields, YAML/JSON keys, and code identifiers unless a
  migration is explicitly requested. Run `python tools/check_encoding_hygiene.py` after
  transliteration or diacritic edits. Mojibake, UTF-8 BOM residue, malformed YAML front matter,
  and non-ASCII YAML/JSON keys in code/data are release blockers unless intentionally and safely
  migrated.
- Controlled terminology: `kalam` is Speculative Theology in this repo, not "Rational Theology".
  Ash'ari and Maturidi labels are varied speculative-theological families, not monoliths. In
  operative repo terminology, reserve "Islamic scholar" / "Islamic scholarship" for
  Salafi/Athari-aligned scholarship; use labels such as kalam theologian, speculative theologian,
  school theologian, mutakallim, philosopher, school authority, or later theological figure for
  non-Athari kalam/falsafah figures. Keep this as source-status discipline, not polemical clutter.
## Optional Script-Capable Route/Check Harness

The optional script-capable route/check harness (formerly called "Level 3") is additive
route-first validation machinery for maintainers. The legacy filenames remain for compatibility,
but active push/PR CI should prefer invariant checks and must not treat the legacy harness as the
canonical execution surface.

- Default `/daee-epistemics [input]` remains the canonical compact DSL-governed surface.
  Codex/script-capable runtimes may use repo-local `skill/scripts/daee_level3.py` as a harness
  around that surface when explicitly requested by a maintainer, but the harness is not the
  public identity of the skill and is not part of the canonical user-facing package.
- `tools/check_level3_data_shapes.py` remains an active, legacy-named data-shape checker until a
  deliberate harness rename migrates producers, generated runtime, docs, and CI together.
- Canonical behavioral smokes must not use `daee_level3.py`, `route.py`, `check_execution.py`,
  generated `route_plan.json`, `features.json`, or `execution_verdict.json` as proof of default
  scriptless execution. If a noninteractive Codex run creates or mentions harness artifacts while
  testing an installed skill, mark that evidence advisory/contaminated for canonical-smoke
  purposes and score the retained `output.md` itself against the owner/source/depth matrix.
- Scriptless runtimes must produce the canonical compact DSL-governed surface; do not invent
  script results if scripts are unavailable.
- `route.py` is deterministic given extracted features; feature extraction includes span-backed
  interpretive components, and transformer execution remains probabilistic.
- The optional script harness does not solve fixture-18 capability ceilings and does not justify pure-Hermes parity
  claims.
- `continuation_queue` is a planned route, not an unconditional checklist. After each `Land(B)`,
  `R(H,Delta)` must decide whether to continue, hold/defer, skip, bounded-reroute, or close.

## Skill Architecture

Current runtime notation is owned by
`atomics/skill/references/diagnostics/recursive-state-transitions.md`.

```text
Input -> IR(N,m,tau,sigma) -> B -> {s1...sn} -> Land(B) -> R(H,Delta) -> STOP/HOLD/PARTIAL/RECURSE
```

Visual architecture reference:
`docs/daee-epistemics-pipeline.html`. Treat it as a repo-navigation aid, not a
new source of truth. Keep it in parity with the canonical compact DSL-governed
runtime, the canonical package boundary, and the repo/dev-only route/check harness
boundary. It must describe the design-space requirement: the framework is engineered
to operate across every possible live noetic-structure selection before the chosen
runtime route is known; meta-noetic memetics becomes executable only through DSL/IR
state, owner/TTP activation, burden landing, state re-read, and restoration.

Expanded visual/diagnostic wiki reference:
`docs/index.html`. Treat the published GitHub Pages page as a navigation and diagnostic aid
only. Durable formalism lives in `docs/algebraic-notation-and-noetic-formalism.md` and canonical
runtime rules still live in atomics. schema-light register bridge semantics are
current where atomics, generated runtime text, and `tests/register-formalism-bridge-fixtures/` make
`heart`/`xi`/`Omega`/`mu`/`kappa` govern existing IR, owner/TTP selection, hold/release,
collapse radius, burden landing, state re-read, PARTIAL, anti-symbol-theater, or restoration.
Bridge live-smoke proof must point to retained audit evidence, not the index page. Do not call
a later release/package readiness until the release-line, contract markers, package artifact,
release docs, and current-release smoke requirements are migrated together. Do not make those
registers mandatory runtime fields without a deliberate schema/checker/fixture/smoke migration,
and do not claim a release-line migration from the index page alone.

Burden/submove notation in public canonical output prefers the compact human/math form:
`¹B₁`, `¹B₂`, `²B₁` = burden 1 submoves 1/2, then burden 2 submove 1. Plain `1B1`,
`1B2`, `2B1` is the ASCII fallback. Existing `B1.s1` / `B1.s2` notation remains an
accepted legacy/checker alias, but public canonical output should not primarily use the
`B<N>.s<M>` style unless a checker/dev harness context requires it. In default compact DSL
hard-case output, absence of the superscript/subscript form is not by itself a failure when
the ASCII fallback or readable "Burden N / operative submove" language preserves
submove-vs-burden grammar and local attachment.

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
- `/daee-epistemics:dsl` is the expanded diagnostic/IR visibility mode, not the first place
  DSL governance appears.
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

For the current canonical user-facing package shape, the `.skill` archive root may contain:

```text
SKILL.md
references/
compiled-module-map.json
build-manifest.json
README.md
```

This mirrors the pre-harness scriptless package boundary, with `README.md` retained as current
package metadata. The canonical package must not contain repo/dev harness roots:

```text
data/
scripts/
tests/
route_plan.json
features.json
validation.json
reconstruction.json
execution_verdict.json
execution_prompt.md
execution_blocked.md
partial_banner.md
retry_prompt.md
output.simulated.md
output.model.md
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
docs/runtime-harness-onboarding.md
docs/audits/INDEX.md
```
