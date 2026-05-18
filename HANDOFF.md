# HANDOFF

Repository path:

```text
C:\workspace\ai\daee-epistemics\expansion\repo
```

## Goal

Continue the docs/index SSOT hardening for `daee-epistemics` without widening scope.

The active workstream is the public docs/index generation system:

- `docs/index.html` and `docs/daee-epistemics-pipeline.html` are generated browser/navigation surfaces.
- Do not hand-edit generated HTML directly.
- Canonical runtime source remains `atomics/skill/**`.
- Generated runtime remains `skill/**`; do not edit generated runtime directly.
- The docs/index Architecture, Theory, Owner/TTP, and Reference Library surfaces should either be generated from source-owned files or explicitly marked and parity-checked.

Release guardrails still apply:

- Do not push, tag, create a GitHub Release, publish, or stage broadly unless explicitly instructed.
- Do not fabricate smoke outputs or treat local diagnostics as public release proof.
- Keep release claims bounded: schema-light executable governance calculus; stronger than prompt engineering; not a full formal calculus; not a truth meter; not live-output proven beyond actual smoke evidence.

## Current Progress

The previous docs/index audit verdict was:

```text
INDEX MOSTLY CLEAN; TARGETED GENERATION PATCHES NEEDED
```

The two P1 drift risks were:

1. Architecture interactive trace maps.
2. Owner/TTP operator/family maps.

Latest pass result:

```text
P1 MOSTLY CLOSED; PARITY CHECKS ADDED
```

What changed in this pass:

- `tools/check_docs_index_interactions.py` now checks Architecture trace parity against `docs/index/runtime-architecture.json`.
- The checker verifies Architecture shared stage keys, stage numbers, stage titles, generated `data-stage-key`, generated `data-substage-key`, and trace-map substage keys/titles.
- `tools/check_docs_index_interactions.py` now checks Owner/TTP map parity against module-catalogue/source paths.
- The checker verifies operator source paths, catalogue-backed operator classes, family filter options, owner-family source tokens, generated module metadata, and guards against stale literal "69 modules" claims.
- `docs/index/templates/index.html.tpl` now has source/parity comments for the Architecture trace maps and Owner/TTP maps.
- `docs/index/manifest.json` now records `parity_checked_by` and `parity_scope` for the two P1 surfaces.
- `docs/index/README.md` documents the generation/parity boundary.
- `docs/audits/v0.4.2.0-docs-index-ssot-audit.md` was updated to say the P1 items are closed by parity checks, with optional full generation deferred as future hardening.
- `docs/index.html` and `docs/daee-epistemics-pipeline.html` were regenerated through `python tools/build_docs_index.py`.

Current dirty files include prior docs/index SSOT work as well as this pass:

```text
docs/audits/INDEX.md
docs/audits/v0.4.2.0-deep-research-next-handoff.md
docs/audits/v0.4.2.0-release-candidate-audit.md
docs/audits/v0.4.2.0-docs-index-ssot-audit.md
docs/daee-epistemics-pipeline.html
docs/index.html
docs/index/README.md
docs/index/manifest.json
docs/index/runtime-architecture.json
docs/index/sections/architecture.html
docs/index/sections/theory.html
docs/index/templates/index.html.tpl
tools/build_docs_index.py
tools/check_docs_index_interactions.py
tools/check_field_operator_architecture.py
```

Latest commands run and passing:

```powershell
python tools/build_docs_index.py
python tools/build_docs_index.py --check
python tools/check_docs_index_interactions.py
python tools/build_framework_pipeline.py
python tools/build_compiled_runtime.py
python tools/check_compiled_runtime_freshness.py
python tools/check_compiled_module_boundaries.py
python tools/check_ttp_operator_contracts.py --strict
python tools/check_field_operator_architecture.py
git diff --check
```

`git diff --check` returned success but printed line-ending normalization warnings for existing touched files.

## What Worked

- Treating `docs/index/runtime-architecture.json` as the shared source for Architecture cards, Architecture rows, and Theory notation worked well.
- Rebuilding generated docs through `tools/build_docs_index.py` kept `docs/index.html` fresh without direct edits.
- Adding parity checks was the right scope for the remaining P1 surfaces:
  - Architecture trace prose is still curated, but the trace keys/titles now fail if they drift from the shared architecture source.
  - Owner/TTP operator prose is still curated, but source paths, catalogue-backed classes, family filters, owner tokens, generated module metadata, and module-count claims now fail on drift.
- Keeping Owner/TTP operator graph and full module catalogue separate was important. The graph is not one-to-one with all 69 catalogue entries because case-library/noetic-profile modules are not operator chips.
- Extending `tools/check_docs_index_interactions.py` was a good fit; it already owns docs/index structure, source-data, freshness, JS syntax, and interaction checks.
- Local checks passed after regenerating docs.

## What Didn't Work

- Fully generating the Architecture trace prose and Owner/TTP operator prose would be a larger migration than this P1 pass needed. It risks rewriting public-site explanatory language and should be treated as optional future hardening.
- Assuming `OPERATORS` should exactly match all entries in `module-catalogue.json` is wrong. The operator graph excludes case-library/noetic-profile modules and includes source-backed diagnostic passes that are not catalogue entries.
- Hand-editing `docs/index.html` is still forbidden and unnecessary. Always patch `docs/index/**` or tools, then rebuild.
- Broad visual redesign was out of scope. The current work is source ownership and parity checking, not public-site polish.
- Do not treat docs/index parity as runtime proof, package proof, or smoke proof. It only prevents docs/index source drift.

## Release / Smoke Status

v0.4.2.0 is **not released**.

Source/runtime/docs/provenance gates passed in the last reported pass, and the final local package/provenance pair exists and verifies, but the current-release smoke gate is still blocked.

Three local package-bound smokes were captured for the final package, but all three failed the live witness checker. Do not claim the smokes passed.

Latest known smoke result:

- `CR-01`: captured locally, but FAILED `check_live_default_witness_contract.py`
  - missing valid `T_lang` boundary and Restorative Response
  - `R(H,Delta)` / closure witness surfaces did not satisfy checker
- `CR-02`: captured locally, but FAILED `check_live_default_witness_contract.py`
  - missing route-gradient witness
  - incomplete repeated diagnostics
  - missing `T_lang` boundary and Restorative Response
- `CR-03`: captured locally, but FAILED `check_live_default_witness_contract.py`
  - missing route-gradient witness
  - incomplete diagnostics
  - closure witness defect
  - missing Restorative Response

`python tools\check_smoke_artifacts.py --require-current-release-smokes` therefore remains failing.

Raw smoke captures are local/ignored diagnostics and should not be committed.

Current release state:

```text
RELEASE-BLOCKED
```

Next release-line work is witness-gate remediation / release-smoke capture mode, followed by fresh package-bound smoke capture. Do not tag, publish, or create a GitHub Release until the required smoke/witness gates pass honestly.

## Next Steps

Recommended next actions for a fresh agent:

1. Start by reading:

```text
AGENTS.md
HANDOFF.md
docs/audits/v0.4.2.0-docs-index-ssot-audit.md
docs/index/README.md
docs/index/manifest.json
tools/build_docs_index.py
tools/check_docs_index_interactions.py
docs/index/runtime-architecture.json
```

2. Confirm current local status:

```powershell
git status --short
python tools/build_docs_index.py --check
python tools/check_docs_index_interactions.py
```

3. If continuing docs/index SSOT hardening, likely next optional P2 items are:

- Fully generate Architecture interaction trace prose from `docs/index/runtime-architecture.json`, if the owner wants stronger SSOT than parity.
- Move Owner/TTP operator/family prose into a source-backed structured data file or generate it from catalogue/frontmatter where enough fields exist.
- Add a small inventory check that flags new large JS constants with runtime/control claims unless they have manifest entries and checker coverage.
- Consider reclassifying or generating more of the standalone pipeline page prose if its current manifest classification overstates structured-source derivation.

4. If preparing a commit/PR later, do not stage with `git add .`. Stage explicit files only and review:

```powershell
git status --short
git diff --stat
git diff --check
```

5. Before pushing or claiming GitHub CI is clean, either push the generated docs/checker changes and inspect Actions, or state clearly that only local gates have passed. Earlier remote CI had failed because generated docs were stale; the local stale-docs issue has now been fixed but not pushed in this handoff.

6. Do not perform release work unless explicitly instructed. Release/smoke/package proof is a separate line from docs/index SSOT parity.
