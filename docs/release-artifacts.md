# Release Artifacts

This file records the last published v0.3.2.0 package artifact used for the same-version
GitHub Release asset refresh. Binary skill archives are not committed to the source repository;
GitHub Releases are the binary distribution surface for the published `.skill` asset.

Build the package locally from the generated `skill/` package root:

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-v0.3.2.0.skill.zip
Copy-Item build\daee-epistemics-v0.3.2.0.skill.zip build\daee-epistemics-v0.3.2.0.skill
```

The package script archives the canonical packageable contents selected from `skill/`, not the
repository root and not the top-level `skill/` directory. It writes a local `.skill.zip` payload;
the published GitHub Release asset is the same checked payload renamed to `.skill`. Do not re-zip
the repository root. `package.ps1` calls the manifest-backed Python packager, validates generated
package shape, excludes repo/dev harness roots, and writes slash-safe archive entries.

## Current Package / Release Asset Evidence

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.3.2.0.skill` |
| SHA256 | `1C47CE08C19D4A6A3972FFFF4CBD78BE16BD72B773C0BDBD490399A1D6745071` |
| Size | `536216` bytes |
| Entries | `20` |
| Source commit | `36a98c3811280feb0ae2e5c6b55070d828ff2162` |
| GitHub Release visibility | Current same-version asset refresh after canonical compact-DSL hard-canary recovery |
| Release tag | `v0.3.2.0` |
| Release name | `v0.3.2.0 - Canonical compact DSL runtime recovery` |
| Release URL | `https://github.com/theislampill/daee-epistemics/releases/tag/v0.3.2.0` |
| Verification date | `2026-05-14` |
| Availability | Binary archive not committed; build locally with `package.ps1` from this source state or download the public GitHub Release asset. |

Local package build output: `daee-epistemics-v0.3.2.0.skill.zip`. It is byte-identical to the
public GitHub Release asset when copied/renamed from the same build output.
GitHub Release binary distribution asset: `daee-epistemics-v0.3.2.0.skill`. The source
repository does not commit the binary archive; the GitHub Release is the binary distribution surface.

Committed smoke suite: none. Historical `runtime-grounding-v5` artifacts were removed from the
source repository; local retained smoke evidence may exist only in ignored working directories.

Current-release committed smoke suite: none.

Local retained installed-skill smoke evidence exists under ignored `.daee/` for this
source/package rebake:

- hard moral-protest / worship-worthiness / source-worldview canary: `45.6k` characters,
  owner/TTP visible, source-operative, closure audit visible, P1/P7 present, no route-check
  harness refs;
- predication/attribute support smoke: `35.0k` characters, M9/V8 predication recursion visible,
  no generic attribute essay, no route-check harness refs;
- naturalist/transmission support smoke: `17.0k` characters, FPD/V2/V10/M1 plus
  testimony/tawatur work visible, clean rerun after a prior harness-contaminated attempt.

These smokes prove current installed-skill file-retained behavior only. They do not prove Claude,
nested `codex exec`, or all-host parity. `codex exec --output-last-message` was confirmed to write
only the final agent message/status, not a full-depth canonical smoke artifact. Raw smoke artifacts
are not committed and not packaged.

`runtime-grounding-v7`, `runtime-grounding-v8`, and Hermes probe artifacts are development /
post-expansion regression evidence in this source state. They are not current-package smoke
evidence unless regenerated against the release package recorded in this file and marked with
current-release package provenance.

Current-package smoke evidence requires regenerating local smoke artifacts against the package SHA
listed above and validating them with `tools/check_smoke_artifacts.py --root <local-smoke-root>`.
`--require-current-release-smokes` remains a release-promotion gate when such a suite exists.

Binary skill archives are not committed. The source repository records local build evidence and
regression artifacts; it does not independently replay live host behavior unless a future live-runner
is added.

Evidence boundaries:

```text
source repo -> current atomics, tools, docs, generated skill/ runtime
local package build output -> ignored build/*.skill.zip archive built from skill/
local smoke regression artifacts -> ignored smokes/ or .daee/ working directories
current package evidence -> public GitHub Release .skill asset, local/internal .skill.zip filename, SHA256, size, entries, and archive-root checks above
current-package smoke evidence -> none in this source state
live-host behavior -> not independently replayed by this repo without a future live-runner
```

Expected canonical archive root:

```text
SKILL.md
references/
compiled-module-map.json
build-manifest.json
README.md
```

Forbidden top-level archive entries:

```text
skill/
atomics/
tools/
docs/
build/
.git/
data/
scripts/
tests/
smokes/
.daee/
level3-runs/
__pycache__/
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
