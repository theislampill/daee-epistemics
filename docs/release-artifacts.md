# Release Artifacts

This file records the current v0.3.2.0 GitHub Release package artifact. Binary skill archives
are not committed to the source repository; GitHub Releases are the binary distribution surface
for the published `.skill` asset.

Build the release candidate locally from the generated `skill/` package root:

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-v0.3.2.0.skill.zip
Copy-Item build\daee-epistemics-v0.3.2.0.skill.zip build\daee-epistemics-v0.3.2.0.skill
```

The package script archives the contents of `skill/`, not the repository root and not the
top-level `skill/` directory. It writes a local `.skill.zip` payload; the published GitHub Release
asset is the same checked payload renamed to `.skill`. Do not re-zip the repository root.

## Current Package / Release Asset Evidence

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.3.2.0.skill` |
| SHA256 | `06C3DACC5AAAD61E7B4FF6243E6F7EE57B3FFF40ED5345A950B763A94EE23A98` |
| Size | `524363` bytes |
| Entries | `45` |
| GitHub Release visibility | Published; asset replaced after post-release Level 3 polish |
| Release tag | `v0.3.2.0` |
| Release name | `v0.3.2.0 - Level 3 Route-First Runtime` |
| Release URL | `https://github.com/theislampill/daee-epistemics/releases/tag/v0.3.2.0` |
| Verification date | `2026-05-09` |
| Availability | Binary archive not committed; build locally with `package.ps1` from this source state or download the public GitHub Release asset. |

Local package build output: `daee-epistemics-v0.3.2.0.skill.zip`. It is byte-identical to the
public GitHub Release asset when copied/renamed from the same build output.
GitHub Release binary distribution asset: `daee-epistemics-v0.3.2.0.skill`. The source
repository does not commit the binary archive; the GitHub Release is the binary distribution surface.

Committed `runtime-grounding-v5` smoke artifacts are historical regression evidence for package
`daee-epistemics-RC00001-v0.3.1.0.skill.zip` / SHA256
`544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8`, not current-release
package evidence for the v0.3.2.0 SHA listed above. Their trace files explicitly mark
`release-artifact relation: historical-regression` and `current-release evidence: no`; any
`current source package` lines inside those historical traces record the release-candidate source
package known when the historical regression artifacts were written, not the current package
artifact in this file.

Current-release smoke suite: none.

`runtime-grounding-v7`, `runtime-grounding-v8`, and Hermes probe artifacts are development /
post-expansion regression evidence in this source state. They are not current-package smoke
evidence unless regenerated against the release package recorded in this file and marked with
current-release package provenance.

Current-package smoke replay artifacts for `daee-epistemics-v0.3.2.0.skill` / SHA256
`06C3DACC5AAAD61E7B4FF6243E6F7EE57B3FFF40ED5345A950B763A94EE23A98` are not present unless a smoke
suite is regenerated against that package and marked `release-artifact relation: current-release`
with `current-release evidence: yes`.

Current-package smoke evidence requires either regenerating those smoke artifacts against the
package SHA listed above or marking any older package SHA as historical regression evidence.
`tools/check_smoke_artifacts.py` compares committed smoke provenance against this file and fails
unmarked package-hash drift.

Binary skill archives are not committed. The source repository records local build evidence and
regression artifacts; it does not independently replay live host behavior unless a future live-runner
is added.

Evidence boundaries:

```text
source repo -> current atomics, tools, docs, generated skill/ runtime
local package build output -> ignored build/*.skill.zip archive built from skill/
historical smoke regression artifacts -> committed runtime-grounding-v5 Markdown/IR artifacts
current package evidence -> public GitHub Release .skill asset, local/internal RC .skill.zip filename, SHA256, size, entries, and archive-root checks above
current-package smoke evidence -> none in this source state
live-host behavior -> not independently replayed by this repo without a future live-runner
```

Expected archive root:

```text
SKILL.md
references/
data/
scripts/
tests/
compiled-module-map.json
build-manifest.json
```

Forbidden top-level archive entries:

```text
skill/
atomics/
tools/
docs/
build/
.git/
```
