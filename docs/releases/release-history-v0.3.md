# v0.3 Release History

Consolidated history for v0.3.x release logs, notes, readiness, and final-verification surfaces.

This file consolidates historical evidence. Individual source files were removed from the active docs tree after their filename, purpose, verdict/status, risks, and provenance were summarized here.

Files consolidated: 9

### `v0.3.0.0-final-verification.md`

- Original filename: `docs/releases/archive/v0.3/v0.3.0.0-final-verification.md`
- Preserved title/context: v0.3.0.0 Final Verification
- Evidence kind: historical release evidence
- Purpose: **Superseded by current runtime canon.** After this verification was completed, a render-mode regression was identified and patched, and four missing runtime metadata files were added to the compiled
- Result/verdict/status: > **Superseded by current runtime canon.** After this verification was completed, a render-mode regression v0.3.0.0 converts daee-epistemics from an atomized runtime skill into a compiled low-call runtime while preserving the atomized source as canonical. It adds compiler/checker tooling, routing parity checks, recursive traversal governance, render modes, and r... | 1 | Consolidation compiler audit | PASS | `docs/consolidation-compiler-audit.md` (historical, marked) | | 2 | Compiler/checker tooling | PASS | All 8 tools in `tools/` PASS |
- Key risks/findings: > was identified and patched, and four missing runtime metadata files were added to the compiled - Anti-pattern §Module Proliferation and §Ghost-Load explicitly cover topic-then-dump failure. **Remaining caveats:** (1) Framework-pipeline is loaded on audit/diagnostic request, not every invocation — architecturally correct per `load_when` front matter. (2) State-carry partition is now canonical in `recursive-state-transitions.md`; cross-reference... ## Remaining Caveats
- Release/artifact/provenance: > package. Older render-mode terms below are historical; current compact DSL/IR default, **Phase:** Final (Phase 10 + stale-state audit + version sync + package + commit prep) | 10 | Final stale-state/version/package/push gate | PASS | This document | **Archive version verified:** `compiler_version: 0.3.0`, `contract_version: "0.3.0.0"` in final package `daee-epistemics-v0.3.0.0-final.skill.zip`. ## Stale Docs / TODO / Artifact Cleanup
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `v0.3.0.0-release-candidate.md`

- Original filename: `docs/releases/archive/v0.3/v0.3.0.0-release-candidate.md`
- Preserved title/context: v0.3.0.0 Release Candidate Gate
- Evidence kind: historical release evidence
- Purpose: **Superseded by current runtime canon.** This candidate gate is historical. Older render terms below such as clean default prose, live door, State Refresh, and fuller public audit
- Result/verdict/status: Release-candidate status: ready with caveats. The compiled runtime is current, all static verification tools pass, the package artifact is valid, Static routing parity and static governance checks pass. Exact prose parity and live model build_compiled_runtime.py: PASS
- Key risks/findings: Release-candidate status: ready with caveats. Path-resolution unresolved-risk: 0 The release notes include major changes, render modes, preserved invariants, non-claims, deprecated normal prompting pattern, verification results, package SHA256, and remaining risks. no missing atomized path chasing
- Release/artifact/provenance: The compiled runtime is current, all static verification tools pass, the package artifact is valid, ## Package Artifact Package command: powershell -NoProfile -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-runtime.skill.zip Package:
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `v0.3.0.0-release-log.md`

- Original filename: `docs/releases/archive/v0.3/v0.3.0.0-release-log.md`
- Preserved title/context: v0.3.0.0 — Compiled Runtime With Governed Recursion
- Evidence kind: historical release evidence
- Purpose: **Superseded by current runtime canon.** This log describes the v0.3.0.0 build. That package was incomplete (missing four runtime metadata files declared in `RUNTIME_METADATA_COPIES`) and had a
- Result/verdict/status: > **Superseded by current runtime canon.** This log describes the v0.3.0.0 build. That package was incomplete v0.3.0.0 converts daee-epistemics from an atomized runtime skill into a compiled low-call runtime while preserving the atomized source as canonical. It adds compiler/checker tooling, routing parity checks, recursive traversal governance, render modes, and r... - Five always/near-always runtime bundles: `runtime-foundation`, `runtime-diagnostic-core`, `runtime-phase2-passes`, `runtime-dispatch-gate`, `runtime-output-governance`. Eight verification tools, all PASS:
- Key risks/findings: > (missing four runtime metadata files declared in `RUNTIME_METADATA_COPIES`) and had a - `check_routing_parity.py --strict` passes: 434 module-to-compiled-section mappings, 1 source-identity-only, 0 unresolved risk. ## Remaining Caveats
- Release/artifact/provenance: > **Superseded by current runtime canon.** This log describes the v0.3.0.0 build. That package was incomplete **Package:** `daee-epistemics-v0.3.0.0-final.skill.zip` **SHA256:** `08902b415b47fd01a364fd1daa70359acccee6d6c49ecb82bb356c6b2c7674f4` - `skill/` is now the generated compiled Claude package root. Do not hand-edit. - `tools/compiled_runtime_lib.py` provides shared compiler utilities.
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `v0.3.0.0-release-notes.md`

- Original filename: `docs/releases/archive/v0.3/v0.3.0.0-release-notes.md`
- Preserved title/context: v0.3.0.0 Release Notes
- Evidence kind: historical release evidence
- Purpose: **Superseded by current runtime canon.** The v0.3.0.0 package was missing four runtime metadata files (`module-catalogue.json`, `diagnostic-ir.schema.json`, `operative-contract.schema.json`,
- Result/verdict/status: build_compiled_runtime.py: PASS check_compiled_runtime_freshness.py: PASS check_compiled_module_boundaries.py: PASS check_stub_integrity.py: PASS
- Key risks/findings: > **Superseded by current runtime canon.** The v0.3.0.0 package was missing four runtime metadata files ## Remaining Risks
- Release/artifact/provenance: > **Superseded by current runtime canon.** The v0.3.0.0 package was missing four runtime metadata files `atomics/skill/`, while `skill/` is the generated compiled Claude package root. ## Package Package command: powershell -NoProfile -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-runtime.skill.zip
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `v0.3.0.0-release-readiness.md`

- Original filename: `docs/releases/archive/v0.3/v0.3.0.0-release-readiness.md`
- Preserved title/context: v0.3.0.0 Release Readiness
- Evidence kind: historical release evidence
- Purpose: **Superseded by current runtime canon.** This readiness report is historical. Older terminology below, including post-render state refresh, is superseded by `R` / state/noetic re-read and the
- Result/verdict/status: Release posture: ready with caveats. The repo is consistent for `v0.3.0.0` static release readiness: `skill/`. Static routing parity and recursive traversal governance pass. Live model behavioral Result: pass after updates. -> Phase 2 passes
- Key risks/findings: Release posture: ready with caveats. The repo is consistent for `v0.3.0.0` static release readiness: | Pipeline section | Current issue | Proposed update | Risk if not fixed | | `atomics/skill/SKILL.md` minimum execution load floor | Matched modules were described as standalone files in the skill package, which could be misread in the compiled runtime. | Updated wording so matched modules are original module IDs/source identities... Result: pass with historical caveat.
- Release/artifact/provenance: edit `atomics/skill/`, compile into `skill/`, run the checker suite, and package the contents of skill/ = generated compiled Claude package root build/ = optional local release/package outputs | `atomics/skill/SKILL.md` minimum execution load floor | Matched modules were described as standalone files in the skill package, which could be misread in the compiled runtime. | Updated wording so matched modules are original module IDs/source identities... - generated compiled runtime package root;
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `v0.3.1.0-release-log.md`

- Original filename: `docs/releases/archive/v0.3/v0.3.1.0-release-log.md`
- Preserved title/context: v0.3.1.0 - Render Governance Cleanup Release
- Evidence kind: historical release evidence
- Purpose: **Date:** 2026-05-01 **Release:** daee-epistemics v0.3.1.0
- Result/verdict/status: v0.3.1.0 is the push-ready patch release over v0.3.0.0. It preserves the compiled runtime - The `runtime-grounding-v5` smoke artifacts passed the burden-completeness gate: hard fixtures remain hard, bounded fixtures are marked bounded-complete with explicit first-/second-/ higher-order burden audits, and the smoke artifact checker rejects quiet hard-to-bounded
- Key risks/findings: architecture while correcting the default render-mode regression, restoring missing runtime
- Release/artifact/provenance: > Superseded render-mode note: this file records the v0.3.1.0 packaged release state. Current > public output, IR source-basis integrity is checker-backed, and repo-local smoke artifacts carry aligning package metadata with the v0.3.1.0 release line. Package: `daee-epistemics-RC00001-v0.3.1.0.skill.zip` SHA256: `544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8`
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `v0.3.1.0-release-notes.md`

- Original filename: `docs/releases/archive/v0.3/v0.3.1.0-release-notes.md`
- Preserved title/context: v0.3.1.0 - Render-Mode Governance Patch
- Evidence kind: historical release evidence
- Purpose: **Date:** 2026-05-01 **Release:** daee-epistemics v0.3.1.0 - Render-Mode Governance Patch
- Result/verdict/status: completes the compiled package with four runtime metadata files that were declared in 2. **Incomplete package artifact.** The v0.3.0.0 `.skill.zip` was missing four files explicitly All 12 checks pass: | `python tools/build_compiled_runtime.py` | PASS |
- Key risks/findings: 2. **Incomplete package artifact.** The v0.3.0.0 `.skill.zip` was missing four files explicitly - decisive missing differentiator when required ## Remaining Caveats
- Release/artifact/provenance: > Superseded render-mode note: this file records the v0.3.1.0 packaged release state. Current > public output, IR source-basis integrity is checker-backed, and repo-local smoke artifacts carry completes the compiled package with four runtime metadata files that were declared in `RUNTIME_METADATA_COPIES` but absent from the v0.3.0.0 artifact, and repairs release-patch 2. **Incomplete package artifact.** The v0.3.0.0 `.skill.zip` was missing four files explicitly
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `v0.3.2.0-release-log.md`

- Original filename: `docs/releases/archive/v0.3/v0.3.2.0-release-log.md`
- Preserved title/context: v0.3.2.0 - Level 3 Route-First Readiness Log
- Evidence kind: historical release evidence
- Purpose: **Date:** 2026-05-10 **Release state:** published GitHub Release with same-version asset refresh for golden-depth
- Result/verdict/status: - Added `ir-reconstruction-pass.md`. - `atomics/skill/references/diagnostics/ir-reconstruction-pass.md` - Added route plans that distinguish first-live, held, deferred, rejected, and - Model execution can still fail to honor a valid plan on highest-complexity
- Key risks/findings: - Summarized the v15 owner-gap adjudication and codon-pilot decision in the - Bounded remaining owner gaps as non-blocking.
- Release/artifact/provenance: **Release state:** published GitHub Release with same-version asset refresh for golden-depth **Baseline reviewed:** tag `v0.3.1.0` at `934a824ff7900ca245bb98bdd134dddf7255bf03`. v0.3.2.0 readiness line and the post-release Level 3 polish package rebuild. It also records the later same-version package rebake for Level 1/2 recursive asset refresh from commit `a62bbdc534a7de958882d6cfd864db5831fe0f3f`. The
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.

### `v0.3.2.0-release-notes.md`

- Original filename: `docs/releases/archive/v0.3/v0.3.2.0-release-notes.md`
- Preserved title/context: v0.3.2.0 Release Notes
- Evidence kind: historical release evidence
- Purpose: **Date:** 2026-05-10 **State:** published GitHub Release with same-version asset refresh for golden-depth Level 3
- Result/verdict/status: burden-complete Layer B execution, and real `R(H,Delta)` state-transition - The codon pilot was rejected/not needed; no owner packs or broad codon DSL
- Key risks/findings: are not counted as operative owner gaps, and no release-blocking routing or loadform gap remained.
- Release/artifact/provenance: **State:** published GitHub Release with same-version asset refresh for golden-depth Level 3 - Same-version asset refresh: the v0.3.2.0 `.skill` asset was rebuilt from v0.3.2.0 package hash while preserving the `v0.3.2.0` tag. than checker-shaped Target / Operation / Result labels. adversarially against the v0.3.1.0/Sonnet golden as installed-package Level 3
- Release relevance: Historical evidence only unless referenced by current v0.4.1.0 candidate docs.
- Superseded status: Superseded as active guidance; preserved by this consolidated history entry.
