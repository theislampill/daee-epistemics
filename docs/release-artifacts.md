# Release Artifacts

Binary skill archives are not committed to this repository. Build the release candidate locally
from the generated `skill/` package root:

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-v0.3.1.0.skill.zip
```

The package script archives the contents of `skill/`, not the repository root and not the
top-level `skill/` directory. If a host expects a `.skill` upload, rename the checked
`.skill.zip` payload to `daee-epistemics.skill`; do not re-zip the repository root.

## Current Package / Release Asset Evidence

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.3.1.0.skill.zip` |
| SHA256 | `08AD1BD7CEFC23EFF9C97BFED37986B9E4BAB634772F77BE8EEC48C38EC08E44` |
| Size | `474357` bytes |
| Entries | `19` |
| GitHub Release visibility | Public verified |
| Release tag | `v0.3.1.0` |
| Release name | `v0.3.1.0 - Render Governance and Evidence-Chain Readiness` |
| Release URL | `https://github.com/theislampill/daee-epistemics/releases/tag/v0.3.1.0` |
| Verification date | `2026-05-07` |
| Availability | Not committed; build locally with `package.ps1` from this source state or download the public GitHub Release asset. |

Internal/local RC evidence package: `daee-epistemics-RC00005-v0.3.1.0.skill.zip`. It is
byte-identical to the public GitHub Release asset when copied from the same build output.
Public GitHub Release binary distribution asset: `daee-epistemics-v0.3.1.0.skill.zip`.
A byte-identical versioned alias asset, `daee-epistemics-v0.3.1.0.skill`, is also present for
hosts that expect `.skill`. The source repository does not commit either binary archive; the
GitHub Release is the binary distribution surface.

Committed `runtime-grounding-v5` smoke artifacts are historical regression evidence for package
`daee-epistemics-RC00001-v0.3.1.0.skill.zip` / SHA256
`544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8`, not current-release
package evidence for the RC00005 SHA listed above. Their trace files explicitly mark
`release-artifact relation: historical-regression`, `current-release evidence: no`, and the
current RC00005 source package filename/SHA.

Current-release smoke suite: none.

Current-package smoke replay artifacts for `daee-epistemics-v0.3.1.0.skill.zip` / SHA256
`08AD1BD7CEFC23EFF9C97BFED37986B9E4BAB634772F77BE8EEC48C38EC08E44` is not present unless a smoke
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
current package evidence -> public GitHub Release asset, local/internal RC filename, SHA256, size, entries, and archive-root checks above
current-package smoke evidence -> none in this source state
live-host behavior -> not independently replayed by this repo without a future live-runner
```

Expected archive root:

```text
SKILL.md
references/
compiled-module-map.json
build-manifest.json
```

Forbidden top-level archive entries:

```text
skill/
atomics/
tools/
docs/
tests/
build/
.git/
```
