# Release Artifacts

Binary skill archives are not committed to this repository. Build the release candidate locally
from the generated `skill/` package root:

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-RC00001-v0.3.1.0.skill.zip
```

The package script archives the contents of `skill/`, not the repository root and not the
top-level `skill/` directory. If a host expects a `.skill` upload, rename the checked
`.skill.zip` payload to `daee-epistemics.skill`; do not re-zip the repository root.

## Current Local Build Evidence

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-RC00001-v0.3.1.0.skill.zip` |
| SHA256 | `08AD1BD7CEFC23EFF9C97BFED37986B9E4BAB634772F77BE8EEC48C38EC08E44` |
| Size | `474357` bytes |
| Entries | `19` |
| Availability | Not committed; build locally with `package.ps1` from this source state. |

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
