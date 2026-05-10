# Release Artifacts

This file records the current v0.3.2.0 package artifact used for the same-version
GitHub Release asset refresh. Binary skill archives are not committed to the source repository;
GitHub Releases are the binary distribution surface for the published `.skill` asset.

Build the package locally from the generated `skill/` package root:

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-v0.3.2.0.skill.zip
Copy-Item build\daee-epistemics-v0.3.2.0.skill.zip build\daee-epistemics-v0.3.2.0.skill
```

The package script archives the contents of `skill/`, not the repository root and not the
top-level `skill/` directory. It writes a local `.skill.zip` payload; the published GitHub Release
asset is the same checked payload renamed to `.skill`. Do not re-zip the repository root.
`package.ps1` calls the manifest-backed Python packager, validates generated package shape, and
writes slash-safe archive entries.

## Current Package / Release Asset Evidence

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.3.2.0.skill` |
| SHA256 | `1C1C3E59E72366689926922BE2117FF477B66E6A35B53004210E55A19559AA10` |
| Size | `572004` bytes |
| Entries | `45` |
| Source commit | `b0bad507d3e0115a6ae57fc5a2e0e45e3eee944c` |
| GitHub Release visibility | Published same-version asset refresh for golden-depth Level 3 hard-case governance, pressure-dimension execution, Level 1/2 scriptless governance lift, canary-name hygiene, and frontloaded Level 1/2 burden-depth governance |
| Release tag | `v0.3.2.0` |
| Release name | `v0.3.2.0 - Golden-depth Level 3 hard-case governance` |
| Release URL | `https://github.com/theislampill/daee-epistemics/releases/tag/v0.3.2.0` |
| Verification date | `2026-05-10` |
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

Current-release committed smoke suite: none.

Local retained real Codex CLI Level 3 hard moral-protest / worship-worthiness /
source-worldview canary evidence exists under ignored `.daee/` for this source/package rebake.
It proves the installed Level 3 path on that canary only;
raw smoke artifacts are not committed, not packaged, and do not prove Claude Level 1/2
scriptless behavioral recovery.

`runtime-grounding-v7`, `runtime-grounding-v8`, and Hermes probe artifacts are development /
post-expansion regression evidence in this source state. They are not current-package smoke
evidence unless regenerated against the release package recorded in this file and marked with
current-release package provenance.

Committed current-package smoke replay artifacts for `daee-epistemics-v0.3.2.0.skill` / SHA256
`1C1C3E59E72366689926922BE2117FF477B66E6A35B53004210E55A19559AA10` are not present unless a smoke
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
current package evidence -> public GitHub Release .skill asset, local/internal .skill.zip filename, SHA256, size, entries, and archive-root checks above
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
```
