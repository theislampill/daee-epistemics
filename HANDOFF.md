# HANDOFF

Repository path:

```text
C:\workspace\ai\daee-epistemics\expansion\repo
```

## Goal

Continue the docs/index SSOT hardening for `daee-epistemics` without widening scope.

The active workstream completed in this pass was the public docs/index generation system plus the
v0.4.2.0 current-release witness gate:

- `docs/index.html` and `docs/daee-epistemics-pipeline.html` are generated browser/navigation surfaces.
- Do not hand-edit generated HTML directly.
- Canonical runtime source remains `atomics/skill/**`.
- Generated runtime remains `skill/**`; do not edit generated runtime directly.
- The docs/index Architecture, Theory, Owner/TTP, and Reference Library surfaces should either be generated from source-owned files or explicitly marked and parity-checked.

Release guardrails still apply:

- Do not push, tag, create a GitHub Release, publish, or stage broadly unless explicitly instructed.
- Do not fabricate smoke outputs or treat local diagnostics as public release proof.
- The three-smoke gate is local package-bound evidence only; raw captures remain ignored
  diagnostics and are not committed.
- Keep release claims bounded: schema-light executable governance calculus; stronger than prompt engineering; not a full formal calculus; not a truth meter; not live-output proven beyond actual smoke evidence.

## Current Progress

The current docs/index audit verdict is:

```text
INDEX ACID/SSOT/GRASP HARDENED; TARGETED P2 GENERATION REMAINS OPTIONAL
```

The two P1 drift risks were:

1. Architecture interactive trace maps.
2. Owner/TTP operator/family maps.

Latest pass result:

```text
EXISTING v0.4.2.0 GITHUB RELEASE UPDATED; THREE-SMOKE GATE PASSED LOCALLY
```

What changed in this pass:

- `tools/check_smoke_artifacts.py --require-current-release-smokes` now invokes
  `tools/check_live_default_witness_contract.py` for manifest `witness_required=true` cases.
- The strict current-release smoke gate now requires `release-smoke witness capture mode` in the
  smoke input when witness capture is required.
- `tools/check_docs_index_interactions.py` now checks Architecture trace parity against `docs/index/runtime-architecture.json`.
- The checker verifies Architecture shared stage keys, stage numbers, stage titles, generated `data-stage-key`, generated `data-substage-key`, and trace-map substage keys/titles.
- `tools/check_docs_index_interactions.py` now checks Owner/TTP map parity against module-catalogue/source paths.
- The checker verifies operator source paths, catalogue-backed operator classes, family filter options, owner-family source tokens, generated module metadata, and guards against stale literal "69 modules" claims.
- `tools/check_docs_index_interactions.py` now verifies the three intended renderings of the shared
  runtime sequence remain separate and aligned:
  - Architecture plain row;
  - Architecture formal row;
  - Theory Deep Dive notation/mapping rendering.
- `tools/check_docs_index_interactions.py` now inventories large JavaScript constants with
  runtime/control claims and requires manifest `js_constants` coverage.
- `docs/index/templates/index.html.tpl` now has source/parity comments for the Architecture trace maps and Owner/TTP maps.
- `docs/index/manifest.json` now records `parity_checked_by`, `parity_scope`, and `js_constants`
  coverage for the runtime/control JavaScript blocks.
- `docs/index/manifest.json` reclassifies the standalone pipeline page as
  `CURATED_SUMMARY_WITH_OWNER_REFERENCES` rather than overstating structured-source derivation for
  its curated stage prose.
- `docs/index/README.md` documents the generation/parity boundary.
- `docs/audits/v0.4.2.0-docs-index-ssot-audit.md` was updated to say the P1 items are closed by parity checks, with optional full generation deferred as future hardening.
- `docs/index.html` and `docs/daee-epistemics-pipeline.html` were regenerated through `python tools/build_docs_index.py`.

Current changed source/docs files from this pass include:

```text
HANDOFF.md
docs/audits/INDEX.md
docs/audits/v0.4.2.0-current-release-smoke-runbook.md
docs/audits/v0.4.2.0-docs-index-ssot-audit.md
docs/audits/v0.4.2.0-p0-remediation.md
docs/daee-epistemics-pipeline.html
docs/index.html
docs/index/README.md
docs/index/manifest.json
docs/index/runtime-architecture.json
docs/package-smoke-readiness.md
docs/release-artifacts.md
docs/v0.4.2.0-release-log.md
docs/v0.4.2.0-release-notes.md
tools/build_docs_index.py
tools/check_docs_index_interactions.py
tools/check_smoke_artifacts.py
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
python tools/check_smoke_artifacts.py --require-current-release-smokes
python tools/check_live_default_witness_contract.py tests\smokes\current-release\v0.4.2.0\CR-01\output.md
python tools/check_live_default_witness_contract.py tests\smokes\current-release\v0.4.2.0\CR-02\output.md
python tools/check_live_default_witness_contract.py tests\smokes\current-release\v0.4.2.0\CR-03\output.md
git diff --check
```

`git diff --check` returned success but printed line-ending normalization warnings for existing touched files.

## What Worked

- Treating `docs/index/runtime-architecture.json` as the shared source for Architecture cards, both Architecture rows, and Theory notation worked well.
- Rebuilding generated docs through `tools/build_docs_index.py` kept `docs/index.html` fresh without direct edits.
- Adding parity/inventory checks was the right scope for the remaining P1/P2 surfaces:
  - Architecture trace prose is still curated, but the trace keys/titles now fail if they drift from the shared architecture source.
  - Owner/TTP operator prose is still curated, but source paths, catalogue-backed classes, family filters, owner tokens, generated module metadata, and module-count claims now fail on drift.
- Keeping the Architecture plain row, Architecture formal row, and Theory rendering distinct matters; they are three related renderings of the same runtime sequence, not duplicates.
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

v0.4.2.0 is **released** through the existing GitHub Release:

```text
https://github.com/theislampill/daee-epistemics/releases/tag/v0.4.2.0
```

The existing `v0.4.2.0` release assets and body were updated after the final local gates passed.
The release tag was not force-moved.

The final local package/provenance pair still exists and verifies:

- package: `build\daee-epistemics-v0.4.2.0.skill`
- SHA256: `21B25FF08AD36E26A57BACEC785C635F49DEC06E84A6EE191F4F8A61870913A7`
- size: `594097`
- entries: `20`
- provenance: `build\daee-epistemics-v0.4.2.0.provenance.json`

Current local smoke result:

- `CR-01`: local package-bound capture passes `check_live_default_witness_contract.py`.
- `CR-02`: local package-bound capture passes `check_live_default_witness_contract.py`.
- `CR-03`: local package-bound capture passes `check_live_default_witness_contract.py`.
- `python tools\check_smoke_artifacts.py --require-current-release-smokes` passes and now invokes
  the witness checker for manifest `witness_required=true` cases.

Raw smoke captures are local/ignored diagnostics and should not be committed. Witness markers are
evidence surfaces, not competence proof. Docs/index parity/generation is not runtime proof.

Current release state:

```text
EXISTING RELEASE UPDATED; THREE-SMOKE GATE PASSED LOCALLY
```

Next release-line work, if any, is a future explicitly authorized correction or follow-up release.
Do not create a duplicate `v0.4.2.0` release, force-move the existing tag, or upload raw smoke
captures.

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
python tools/check_smoke_artifacts.py --require-current-release-smokes
```

3. If continuing docs/index SSOT hardening, likely next optional P2 items are:

- Fully generate Architecture interaction trace prose from `docs/index/runtime-architecture.json`, if the owner wants stronger SSOT than parity.
- Move Owner/TTP operator/family prose into a source-backed structured data file or generate it from catalogue/frontmatter where enough fields exist.
- Generate more standalone pipeline page prose from `framework-pipeline.yaml` / runtime architecture source if stronger derivation is desired.

4. If preparing a commit/PR later, do not stage with `git add .`. Stage explicit files only and review:

```powershell
git status --short
git diff --stat
git diff --check
```

5. Before pushing or claiming GitHub CI is clean, either push the generated docs/checker changes and inspect Actions, or state clearly that only local gates have passed. Earlier remote CI had failed because generated docs were stale; the local stale-docs issue has now been fixed but not pushed in this handoff.

6. Do not perform release work unless explicitly instructed. Release/smoke/package proof is a separate line from docs/index SSOT parity.
