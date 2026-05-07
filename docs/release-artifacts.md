# Release Artifacts

Binary skill archives are not committed to this repository. Build the release candidate locally
from the generated `skill/` package root:

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-RC00005-v0.3.1.0.skill.zip
```

The package script archives the contents of `skill/`, not the repository root and not the
top-level `skill/` directory. If a host expects a `.skill` upload, rename the checked
`.skill.zip` payload to `daee-epistemics.skill`; do not re-zip the repository root.

## Current Local Build Evidence

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-RC00005-v0.3.1.0.skill.zip` |
| SHA256 | `08AD1BD7CEFC23EFF9C97BFED37986B9E4BAB634772F77BE8EEC48C38EC08E44` |
| Size | `474357` bytes |
| Entries | `19` |
| Availability | Not committed; build locally with `package.ps1` from this source state. |

Committed `runtime-grounding-v5` smoke artifacts are historical regression evidence for package
SHA256 `544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8`, not current-release
package evidence for the SHA listed above. Their trace files explicitly mark
`release-artifact relation: historical-regression` and `current-release evidence: no`.

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
current package evidence -> filename, SHA256, size, entries, and archive-root checks above
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
