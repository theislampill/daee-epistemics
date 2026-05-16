# Pre-v0.4.1 Miscellaneous Audit History

Consolidated history for older miscellaneous audits no longer active as current guidance.

This file consolidates historical evidence. Individual source files were removed from the active docs tree after their filename, purpose, verdict/status, risks, and provenance were summarized here.

Files consolidated: 8

### `codex-smoke-test-findings.md`

- Original filename: `docs/audits/archive/pre-v0.4.1/codex-smoke-test-findings.md`
- Preserved title/context: Codex Smoke-Test Findings
- Evidence kind: historical audit evidence
- Purpose: Host/testing caveat only. Not runtime doctrine.
- Result/verdict/status: - whether the failure was output-shape, routing, Phase 2, TTP execution, state re-read, or host Treat Codex smoke tests as host-aware behavioral probes. A failure is strong evidence only when it runtime invocations. Development-thread failures may still be useful, but they should be labeled Invocation: `codex exec --dangerously-bypass-approvals-and-sandbox --output-last-message` against
- Key risks/findings: Host/testing caveat only. smoke must follow `compiled-module-map.json` resolution and must not chase missing atomized paths - whether the failure was output-shape, routing, Phase 2, TTP execution, state re-read, or host Treat Codex smoke tests as host-aware behavioral probes. A failure is strong evidence only when it
- Release/artifact/provenance: partly host-shaped rather than purely daee-runtime-shaped. It is intended for maintainers designing daee output shape. Smoke tests should run in a clean thread without an active planning, - Codex shares a workspace with the repo. If the prompt asks for audit, comparison, patching, or - The compiled package contains runtime bundles, not every atomized source file. A valid Codex - whether the failure was output-shape, routing, Phase 2, TTP execution, state re-read, or host
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `compiled-runtime-verification.md`

- Original filename: `docs/audits/archive/pre-v0.4.1/compiled-runtime-verification.md`
- Preserved title/context: Compiled Runtime Verification
- Evidence kind: historical audit evidence
- Purpose: Phase 4 verification passed after migrating the editable atomized source to `atomics/skill/` and making `skill/` the generated low-call Claude package root. Generated files under `skill/` were rebuilt only through `tools/build_compiled_runtime.py`; they were not hand-edited.
- Result/verdict/status: Phase 4 verification passed after migrating the editable atomized source to `atomics/skill/` and making `skill/` the generated low-call Claude package root. compiled-runtime build: PASS compiled-runtime freshness: PASS compiled module boundaries: PASS
- Key risks/findings: unresolved-risk: 0 ## Remaining Risks
- Release/artifact/provenance: Phase 4 verification passed after migrating the editable atomized source to `atomics/skill/` and making `skill/` the generated low-call Claude package root. skill/ = generated compiled Claude package root build/ = optional package/release outputs Edit `atomics/skill/`. Do not edit `skill/` directly. Run `tools/build_compiled_runtime.py` to regenerate `skill/`. Package/deploy from `skill/`. Pass-shape invariants checked: 6
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `consolidation-compiler-audit.md`

- Original filename: `docs/audits/archive/pre-v0.4.1/consolidation-compiler-audit.md`
- Preserved title/context: daee-epistemics Consolidation Compiler Audit
- Evidence kind: historical audit evidence
- Purpose: Phase 4 layout note: this Phase 1 audit used the earlier plan where `skill/` remained canonical source and `build/compiled-skill/` was the generated runtime. The implemented Phase 4 layout supersedes that path convention: canonical atomized source now lives under `atomics/skill/`, and `skill/` is the generated Claude package root. See `docs/source-vs-runtime-layout.md` for the current operating layout. Path references below that use `skill/` as source or `build/compiled-skill/` as final runtime are historical audit context, not current operating instructions.
- Result/verdict/status: The current source is already highly structured: all 103 Markdown files under `skill/references/` have YAML operative front matter, and `module-catalogue.json` maps registered module IDs to canonical source paths. That is enough to support a build pipeline,... The runtime problem is structural. `skill/SKILL.md` correctly requires an always-load foundation, a mandatory diagnostic core, V1 Phase 2 passes, a diagnostic IR dispatch gate, output-release governance, post-render state refresh, and confirmed-match module... This audit used local inspection plus six read-only subagent audit passes: `SKILL.md` activation -> always-load foundation -> V1 diagnostic gate -> Phase 2 mandatory/triggered passes -> Diagnostic IR six-check dispatch gate -> selective matched module load floor -> output-release rubric -> diagnostic render contract -> bounded out...
- Key risks/findings: The issue is not a few pathological cases. The current architecture makes almost every serious case load too many small files because the governance surface is intentionally atomized. | Bundle | Included source files | Always or selective? | Why safe? | Routing risk | Required preservation rule | | `build/compiled-skill/references/omnibus/OMNIBUS-do-families.md` | `do-core.md`; `do-second-loop.md`; `do-christian-extensions.md`; `do-attribute-precision.md`; `philosophical-usurpation.md`; `sound-reason-epistemology.md`; `prophecy-wahy-supremacy.md` | ... | Tool | Inputs | Outputs | Checks | Failure conditions |
- Release/artifact/provenance: > Phase 4 layout note: this Phase 1 audit used the earlier plan where `skill/` remained canonical source and `build/compiled-skill/` was the generated runtime. The implemented Phase 4 layout supersedes that path convention: canonical atomized source now liv... The runtime problem is structural. `skill/SKILL.md` correctly requires an always-load foundation, a mandatory diagnostic core, V1 Phase 2 passes, a diagnostic IR dispatch gate, output-release governance, post-render state refresh, and confirmed-match module... - `build/compiled-skill/` = generated runtime artifact. - `package.ps1` currently packages only from `skill/`. | Pipeline stage | Current source files | Runtime role | Can compile? | Bundle target |
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `framework-pipeline-formalization.md`

- Original filename: `docs/audits/archive/pre-v0.4.1/framework-pipeline-formalization.md`
- Preserved title/context: Framework Pipeline Formalization
- Evidence kind: historical audit evidence
- Purpose: Explanatory / audit formalization only. Not live routing authority.
- Result/verdict/status: - `tools/check_framework_pipeline.py` verifies required nodes, mandatory-pass order, gate checks, - bypassing Diagnostic IR formation; dependencies will fail if a load-bearing premise, criterion, or authority node is cleared. already-named dynamics dock, persist, mutate, propagate, and instantiate in language, communities,
- Key risks/findings: architecture; `diagnostic-ir.md` makes it actionable through repo-owned fields, gates, and failure
- Release/artifact/provenance: - reasoning about why the generated pipeline has its current shape. - changing default output shape; or smoke report collapses those stages into linear argument delivery, it is no longer describing
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `hermes-hard-smoke-depth-diagnostic.md`

- Original filename: `docs/audits/archive/pre-v0.4.1/hermes-hard-smoke-depth-diagnostic.md`
- Preserved title/context: Hermes Hard-Smoke Depth Diagnostic
- Evidence kind: historical audit evidence
- Purpose: Created: 2026-05-08 Diagnostic artifact root:
- Result/verdict/status: This diagnostic did not create or promote theological smoke evidence. The fixture-11 runs below are diagnostic captures only and must not be treated as v7 PASS artifacts without the normal smoke artifact review. | `forced-depth-architecture-probe` | `38489` | Passed the 20 KB capacity test. Produced multi-burden architecture traversal with target -> operation -> result, state/noetic re-read, and held-route reassessment. | Boilerplate/padding scan over the diagnostic outputs found no matches for the known false-PASS filler phrases, including `Licensed traversal detail`, `apply the owner floor`, and `selected operator is not decorative`. The prior pilot likely failed because the smoke runner let Hermes satisfy the user-facing task compactly instead of requiring smoke-grade execution depth.
- Key risks/findings: High-risk source/scholar leakage scan over probe outputs found no matches for the known source-audit/scholar/platform leakage terms. - **F. missing continuation loop**: not the primary cause, but useful. Continuation works and should be available as a fallback when a live run explicitly ends PARTIAL or names a next live burden. Hermes is skill-grounded and capable of producing hard-depth output. The current failure is not a fixed output cap and not obvious skill-shallow loading. The smoke harness needs a stronger hard-smoke wrapper and, ideally, a continuation fallback for partial...
- Release/artifact/provenance: Diagnostic artifact root: This diagnostic did not create or promote theological smoke evidence. The fixture-11 runs below are diagnostic captures only and must not be treated as v7 PASS artifacts without the normal smoke artifact review. 4. Store multi-turn hard outputs as direct-capture turn artifacts and document concatenation/provenance in `trace.md` before considering any combined `output.md`. Hermes is skill-grounded and capable of producing hard-depth output. The current failure is not a fixed output cap and not obvious skill-shallow loading. The smoke harness needs a stronger hard-smoke wrapper and, ideally, a continuation fallback for partial...
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `hermes-render-through-opus-diagnostics.md`

- Original filename: `docs/audits/archive/pre-v0.4.1/hermes-render-through-opus-diagnostics.md`
- Preserved title/context: Hermes Render-Through / Opus Diagnostics
- Evidence kind: historical audit evidence
- Purpose: Purpose: incorporate Opus's recognition-vs-render-through diagnosis into the hard-output loop. The issue is not simply "Hermes bad" or "contract missing"; it is that Hermes/GPT-5.5 can
- Result/verdict/status: 1. Recognition PASS != render-through execution. 5. Hard smoke PASS needs owner-body / compiled-bundle access evidence, not just SKILL.md recognition. - Added **Burden-Cycle Compression Failure** as malformed: complex `B` rendered as one broad Target/Operation/Result block. - Rejects hard PASS without owner-body or compiled-bundle access evidence.
- Key risks/findings: The issue is not simply "Hermes bad" or "contract missing"; it is that Hermes/GPT-5.5 can - Added **Burden-Cycle Compression Failure** as malformed: complex `B` rendered as one broad Target/Operation/Result block. Rejected for ordinary default output. A visible submove-count sentinel risks making public `MIXED: RENDER-THROUGH PATCH SUCCESS + OWNER-BODY ACCESS GAP ADDRESSED + HOST/MODEL DEPTH REMAINS`.
- Release/artifact/provenance: - `tools/check_smoke_artifacts.py` - Current selected v8 PASS artifacts now state the owner-body evidence boundary truthfully: compiled bundles/source references were synced and available; direct Level 2 file-loads are not claimed. Artifacts: Judgment: the Opus patch improved visible render-through shape in pure mode, but the output
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `ns-ttp-meta-noetic-memetic-ontological-quantization-audit.md`

- Original filename: `docs/audits/archive/pre-v0.4.1/ns-ttp-meta-noetic-memetic-ontological-quantization-audit.md`
- Preserved title/context: NS/TTP Meta-Noetic Memetic and Ontological Quantization Audit
- Evidence kind: historical audit evidence
- Purpose: Status: Stage-0 architecture audit accepted; Stage-1 evidence-closure and M9 child-mode patch. The current Pipeline #2 baseline DSL/IR-governed architecture thesis is sound, but the repo is
- Result/verdict/status: Status: Stage-0 architecture audit accepted; Stage-1 evidence-closure and M9 child-mode patch. ## Executive Verdict - Verification status: Stage-1 checker run recorded below; static checks passed. | DA/DS/HK | remaining DA/DS/HK-* | merge/defer | no free-floating owner without failed owner trace |
- Key risks/findings: | OQ | OQ-2, OQ-8, OQ-9, OQ-10, OQ-6 | diagnostic/audit vocabulary first | promote only after parent owner smokes prove gap | | M9-SR | child mode under M9 | later technical interpretation overrides received meaning | tafsir/bayan clarification only | first-audience received meaning | audit speaker intent, usage, context, and direct-audience availability before semantic override |... label-only compliance, generic operation verbs, route/check harness leakage, missing case-specific targets, missing child-specific operations, missing burden-state change, missing Land(B), and
- Release/artifact/provenance: Status: Stage-0 architecture audit accepted; Stage-1 evidence-closure and M9 child-mode patch. material. Stage 1 implements evidence closure plus a narrow M9-first slice rather than a new owner - Corpus manifest: present below with filename, stable corpus-relative path, size, SHA256, read - Repo paths in this artifact: repo-relative. - Patch scope: one persisted audit artifact, one M9 child-mode table, three label-stripped routing
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `pattern-family-audit.md`

- Original filename: `docs/audits/archive/pre-v0.4.1/pattern-family-audit.md`
- Preserved title/context: Pattern-Family Robustness and Multi-Module Routing Discipline Audit
- Evidence kind: historical audit evidence
- Purpose: Historical audit / regression-probe material. Not live routing authority.
- Result/verdict/status: **Abstract pattern:** The interlocutor requests justification but has not yet formed a genuine inquiry. The "no reason" claim is a pre-inquiry position, not an examined conclusion. Frequently, an implicit criterion functions as the tribunal; the demand to "... **Surface realizations:** "I don't have any reason to be Muslim", "give me evidence", "what's the proof?", "it needs to pass scientific scrutiny." **Noetic pressures:** NS-2 (agnostic evidentialist) or NS-12 (blank slate). The phrasing is ambiguous between (a) genuine truth-seeking inquiry and (b) criterion-enforcement demanding religion pass a foreign bar. The discourse orientation (truth-seek vs. au... **Noetic pressures:** NS-7 (theistic evidentialist seeking philosophical coherence); NS-3 (deconverted — Christian crisis may have already occurred); NS-11 (fideist — holding Trinity on faith, resistant to rational examination).
- Key risks/findings: **Co-dispatch conditions:** V2 must land before any evidential content (E1/E3). V7 can co-dispatch with V2 once initial triage confirms the criterion is the live issue. P1 can co-dispatch in positive-register cases where no hostile criterion is operating. **Secondary modules:** M2 (prior probability — surface the prior when it's set so low evidence cannot land), E3 (cumulative-case — only when no single upstream blocker and register is open) - **PF-3A — Christian canon selection** (which Bible version — Protestant / Catholic / Orthodox): The live question is about a tradition the interlocutor comes from; the challenge is identifying why any version is authoritative. **Currently ungoverned as a ... **Canonical routing surfaces (PF-3A):** MISSING — see GAP-A. After Patch A, routes to `do-christian-extensions.md DO-14`.
- Release/artifact/provenance: **Canonical routing surfaces (PF-3B):** `revelation-transmission.md RT-2`, `V10` (separate artifact from transmission), `ns-9` profile if skepticism is methodologically formed **Primary module cluster:** V2 (loosen historical-critical framework), V10, RT-1 (artifact vs. authenticated transmission), RT-3 (qirāʾāt vs. manuscript variants) Expected: PF-4 now active alongside PF-1. "How do I know who's right?" indicates genuine inquiry. DO-orient: truth-seek likely. Deformation: thin — ẓann candidate ("I've heard Muslims say" is second-hand exposure). Route: FPD pass (no explicit criterion; tr...
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.
