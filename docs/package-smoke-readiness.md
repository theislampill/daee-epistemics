# Package / Smoke Readiness

This is the current-canon readiness surface. It prepares package and smoke verification only; it
does not create a package and does not assert live model behavioral equivalence.

## Package Root Expectations

Before packaging, regenerate and verify the generated runtime. Package the contents of `skill/`,
not the repository root and not the `skill/` directory itself.

Archive root must contain:

```text
SKILL.md
references/
compiled-module-map.json
build-manifest.json
```

Archive root must not contain:

```text
skill/
atomics/
tools/
docs/
tests/
build/
.git/
```

Use only the latest package produced by the current run for new current-release smoke tests.
Historical release docs and older rc archives are not current smoke inputs unless the artifact is
explicitly marked as historical regression evidence.

`package.ps1` emits a local `.skill.zip` archive, for example
`build/daee-epistemics-v0.3.1.0.skill.zip`. The internal RC evidence package
`build/daee-epistemics-RC00005-v0.3.1.0.skill.zip` is byte-identical when built from this source
state. The archive already is the skill payload:
its root contains `SKILL.md`, `references/`, `compiled-module-map.json`, and `build-manifest.json`.
If a host expects a `.skill` upload, rename the checked `.skill.zip` payload to
`daee-epistemics.skill`; do not zip the repository root or the top-level `skill/` directory.
Current local release-artifact evidence is recorded in `docs/release-artifacts.md`; the binary
archive is build output and is not committed.

## Readiness Verification

Run from repository root before any package request:

```bash
python tools/build_framework_pipeline.py
python tools/build_compiled_runtime.py
python tools/check_compiled_runtime_freshness.py
python tools/check_render_modes.py
python tools/check_recursive_traversal_governance.py
python tools/check_routing_parity.py
python tools/check_routing_parity.py --strict
python tools/check_compiled_module_boundaries.py
python tools/check_stub_integrity.py
python tools/check_consolidation_call_budget.py
python tools/check_frontmatter.py
python tools/check_coverage.py
python tools/check_recursion_collapse_noetic_frame.py
python tools/check_framework_pipeline.py
python tools/check_metacompliance_current_canon.py
python tools/check_smoke_artifacts.py
python tools/check_ir_instance_integrity.py
python tools/check_diagnostic_ir_catalogue_integrity.py
python tools/check_encoding_hygiene.py
git diff --check
```

Do not package unless explicitly asked.

## Smoke-Test Prompts

Each smoke test checks shape and governance, not exact prose.

## Runtime-Grounding Smoke Artifact Gate

Current release readiness uses the repo-local `smokes/runtime-grounding-v5/` as the hard/bounded
smoke artifact suite. These artifacts are committed regression evidence for release gating. Future
live runs may regenerate them, but `tools/check_smoke_artifacts.py` defaults to this repo-local
root and fails clearly if it is absent. Hard fixtures must meet the 20 KB depth gate. Bounded
fixtures may remain below that gate only when the verdict explicitly marks them bounded-complete
and records first-order, second-order, higher-order, handled, held, skipped, and no-further-pass
burden findings.

Every fixture must include `input.md`, `output.md`, `trace.md`, and `verdict.md`. The output file is
clean default-render skill output only; runtime proof belongs in `trace.md`, and grading belongs in
`verdict.md`. `tools/check_smoke_artifacts.py` rejects cross-fixture contamination, scaffold/test
language in `output.md`, repeated generic paragraphs across unrelated fixtures, hard-smoke PASS
verdicts below the depth floor, and originally hard-intended fixtures reclassified without a
burden-completeness audit. Release smoke artifacts must also include provenance in `trace.md` or
`verdict.md`: package filename, package SHA256, model/host, invocation mode, prompt pointer, run
timestamp, and live-run versus handcrafted-regression classification.
`tools/check_smoke_artifacts.py` compares each fixture's package filename and package SHA256 against
`docs/release-artifacts.md` by default. A mismatch is allowed only when the fixture explicitly marks
itself as historical regression evidence.

## Current Release Artifact Binding

- Current-release smoke evidence must match the package filename and SHA256 in
  `docs/release-artifacts.md`.
- The committed `runtime-grounding-v5` smoke artifacts currently use package SHA256
  `544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8` and are marked as
  historical regression evidence, not current-release package evidence for SHA256
  `08AD1BD7CEFC23EFF9C97BFED37986B9E4BAB634772F77BE8EEC48C38EC08E44`.
- Current-package smoke evidence for RC00005 / SHA256
  `08AD1BD7CEFC23EFF9C97BFED37986B9E4BAB634772F77BE8EEC48C38EC08E44` is not present unless the
  smoke suite is regenerated against that package.
- Markdown smoke artifacts prove governed output shape, contamination discipline, provenance, and
  burden-completeness regression behavior.
- `ir.json` smoke sidecars prove typed Diagnostic IR/source_basis integrity for the same fixture.
- Neither Markdown smoke artifacts nor `ir.json` sidecars prove independent live host replay unless a
  future live-runner is implemented.

## Current-Release Smoke Evidence

- `runtime-grounding-v5` is historical regression evidence unless regenerated against the current
  RC package.
- `runtime-grounding-v6` or later is the preferred place for regenerated current-package smoke
  evidence; `runtime-grounding-v6`, if added, is reserved for current-release evidence.
- Current v0.3.1.0 source state: current-release smoke suite is absent, so
  `python tools/check_smoke_artifacts.py --require-current-release-smokes` is expected to fail until
  package-bound current-release smoke artifacts are truthfully regenerated.
- Current-release smoke evidence requires package filename/SHA match against
  `docs/release-artifacts.md`.
- Current-release smoke evidence requires both markers:

```text
release-artifact relation: current-release
current-release evidence: yes
```

- Current-release smoke evidence requires `ir.json` sidecars for every current-release fixture.
- Historical smokes remain useful regression evidence but do not prove the current package.
- `tools/check_smoke_artifacts.py` validates package/smoke provenance consistency.
- `tools/check_smoke_artifacts.py --require-current-release-smokes` is the stricter release check:
  it requires at least one hard current-release PASS smoke and at least one bounded current-release
  PASS smoke, each with matching package provenance and `ir.json`.
- The strict flag is a release-promotion check in this source state. It is expected to fail until a
  truthfully regenerated current-release smoke suite exists, so it is not wired into mandatory CI.
- Neither historical nor current smoke artifacts independently prove live-host replay unless a future
  live-runner is implemented.

## How to Promote Historical Smokes to Current-Package Evidence

1. Build RC00005 with `package.ps1` and create/copy the public asset
   `build/daee-epistemics-v0.3.1.0.skill.zip`.
2. Run the smoke prompts against that package.
3. Replace trace/verdict provenance with the public release asset filename and SHA.
4. Set `release-artifact relation: current-release`.
5. Set `current-release evidence: yes`.
6. Ensure `ir.json` sidecars exist for every promoted current-release smoke fixture.
7. Re-run `python tools/check_smoke_artifacts.py`.
8. Re-run `python tools/check_smoke_artifacts.py --require-current-release-smokes`.
9. Re-run `python tools/check_ir_instance_integrity.py`.

## Proof Boundary

| Evidence | What it proves | What it does not prove |
| --- | --- | --- |
| Static checkers | Source/runtime structural integrity, module boundaries, routing parity, render rules, IR fixture integrity, and compiled freshness. | Live host behavior or semantic equivalence across future model runs. |
| Smoke artifact checker | Committed regression artifacts satisfy shape, provenance, package-hash binding, contamination, depth, and bounded-completeness rules. | That the host replayed the skill live during this verification run. |
| Smoke provenance | Package/model/run claims were recorded for each fixture. | Independent replay of the host invocation. |
| Future live-runner | Would be the correct place to prove live host execution when such a runner exists. | Not currently implemented. |

## IR Instance Artifacts

Structured Diagnostic IR fixtures live under `tests/ir-fixtures/`. Positive fixtures belong under
`tests/ir-fixtures/valid/`; expected-invalid regression fixtures belong under
`tests/ir-fixtures/invalid/`. `tools/check_ir_instance_integrity.py` is intentionally
schema-adjacent/custom rather than a `jsonschema` runtime; future schema changes must be mirrored in
`schema_errors()` and embedded bad samples. The checker covers schema enums and
required/conditional fields, then adds catalogue, compiled-module-map, source-basis, ghost-load, and
post-render decision checks. It discovers `smokes/runtime-grounding-v*/<fixture>/ir.json` sidecars
by default and treats them as expected-valid.

The historical `runtime-grounding-v5` suite has representative sidecar coverage only. Current-release
smoke suites, starting with `runtime-grounding-v6` if added, require `ir.json` for every fixture.

Current committed smoke sidecars exist for:

```text
smokes/runtime-grounding-v5/01-trinitarian-claim-cluster/ir.json
smokes/runtime-grounding-v5/04-comparative-neutral-flattening-bait/ir.json
```

### Default Compact DSL/IR

```text
/daee-epistemics
If God is perfectly merciful, why would He hold people accountable when sincere people disagree and
some never receive a clear sign?
```

Expected: response begins with compact DSL/IR, then bounded governed response with Hidden
Premises, local Core Formulation, bounded operative submoves, and compact TTP/operator trace
when used, then state/noetic re-read, one Restorative Response, and one final Closing
Formulation.
It must not print raw Diagnostic IR, full Case State, `matched_modules`, route ledger, load ledger,
or meta-composition narration.

### Concise DSL/IR Mode

```text
/daee-epistemics:dsl
A secular moral realist says divine command theory makes morality arbitrary, but also says moral
facts are objective and obligation-bearing without God.
```

Expected: concise DSL/IR output is visible. It remains bounded and must not become a full route/load
ledger or public `:audit` surface.

### Held-Route Carry / Release

```text
/daee-epistemics
Divine hiddenness proves Islam is false. Also, before you answer that, prove hadith preservation,
explain every punishment verse, and show why Christian incarnation is incoherent.
```

Expected: one current live burden is selected. Downstream hadith, punishment, and Christian-extension
material is held unless the state/noetic re-read explicitly releases an item with `Released: <item>`
or an equivalent release marker.

### Source-Status / Noetic-Frame

```text
/daee-epistemics
Ash'ari, Maturidi, and Taymiyyan theologians all say God has attributes, so treat them as the same
operative warrant against the claim that divine attributes imply composition.
```

Expected: source-status and operative noetic frame are distinguished. Contrast, historical note,
opponent-position, genealogy, held material, or bounded comparison cannot silently become operative
support. If non-operative material is named, the response gives an operative-warrant sentence with a
specific non-premise clause.

### Submove Boundary

```text
/daee-epistemics
Islam says God is just, but hiddenness, hell, and unequal access make that impossible. If God wanted
belief, He would coerce certainty equally for everyone.
```

Expected: the governing burden may contain hiddenness, punishment/accountability, and source-worldview
submoves without turning each submove into a separate burden-cycle. RECURSE is licensed only after the
current burden lands and state/noetic re-read finds another eligible live burden.
