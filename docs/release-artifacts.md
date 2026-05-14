# Release Artifacts

This file records the current v0.4.0.0 package artifact for the GitHub Release
asset. Binary skill archives are not committed to the source repository; GitHub
Releases are the binary distribution surface for the published `.skill` asset.

Build the package locally from the generated `skill/` package root:

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-v0.4.0.0.skill.zip
Copy-Item build\daee-epistemics-v0.4.0.0.skill.zip build\daee-epistemics-v0.4.0.0.skill
```

The package script archives the canonical packageable contents selected from
`skill/`, not the repository root and not the top-level `skill/` directory. It
writes a local `.skill.zip` payload; the published GitHub Release asset is the
same checked payload renamed to `.skill`. Do not re-zip the repository root.
`package.ps1` calls the manifest-backed Python packager, validates generated
package shape, excludes repo/dev harness roots, and writes slash-safe archive
entries.

## Current Package / Release Asset Evidence

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.4.0.0.skill` |
| SHA256 | `78C2BECE8818DEFF10C8CEF1A1578D9B54D0929950460681D04DC4F885576D0C` |
| Size | `554776` bytes |
| Entries | `20` |
| Source commit | `v0.4.0.0 release commit; see release tag` |
| GitHub Release visibility | Current release artifact for evidence-gated operator runtime and NS/register hardening |
| Release tag | `v0.4.0.0` |
| Release name | `v0.4.0.0 - Register Grammar, Release-Boundary and Meta-Noetic Operator Hardening, Evidence-Gated Operator Runtime` |
| Release URL | `https://github.com/theislampill/daee-epistemics/releases/tag/v0.4.0.0` |
| Verification date | `2026-05-14` |
| Availability | Binary archive not committed; build locally with `package.ps1` from this source state or download the public GitHub Release asset. |

Local package build output: `daee-epistemics-v0.4.0.0.skill.zip`. It is
byte-identical to the public GitHub Release asset when copied/renamed from the
same build output. GitHub Release binary distribution asset:
`daee-epistemics-v0.4.0.0.skill`. The source repository does not commit the
binary archive; the GitHub Release is the binary distribution surface.

Package shape:

```text
SKILL.md
references/
compiled-module-map.json
build-manifest.json
README.md
```

Forbidden top-level archive entries remain excluded:

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

## Current-Release Smoke Evidence

Current-release package-bound smoke evidence is retained locally under ignored
`.daee/v0.4.0.0-current-release-smokes/` and validated with:

```powershell
python tools/check_smoke_artifacts.py --root .daee/v0.4.0.0-current-release-smokes --require-current-release-smokes
```

The retained suite is local, package-bound evidence for this package SHA. It is
not committed, not packaged, and not a universal semantic-grading claim.

Smoke families:

- hard moral-protest / source-worldview canary;
- predication / attribute canary;
- naturalist / transmission canary;
- child-mode local evidence boundary canary.

Evidence boundaries:

```text
source repo -> current atomics, tools, docs, generated skill/ runtime
local package build output -> ignored build/*.skill.zip archive built from skill/
release asset -> checked build/*.skill payload uploaded to GitHub Release
local smoke regression artifacts -> ignored smokes/ or .daee/ working directories
current package evidence -> public GitHub Release .skill asset, local/internal .skill.zip filename, SHA256, size, entries, and archive-root checks above
current-package smoke evidence -> ignored .daee/v0.4.0.0-current-release-smokes package-bound suite
local child-mode samples -> ignored .daee retained evidence, not release proof
dev-local checker PASS -> not universal semantic grading
live-host behavior -> not all-host parity or deterministic transformer execution
```
