# Release Artifacts

This file records published package artifacts and local release-candidate
package evidence. Binary skill archives are not committed to the source
repository; GitHub Releases are the binary distribution surface for published
`.skill` assets.

Build the package locally from tracked atomics through generated `skill/`:

```powershell
python tools/build_framework_pipeline.py
python tools/build_compiled_runtime.py
python tools/package_skill.py build\daee-epistemics-v0.4.1.0.skill.zip
Copy-Item build\daee-epistemics-v0.4.1.0.skill.zip build\daee-epistemics-v0.4.1.0.skill
```

The package script archives the canonical packageable contents selected from
generated local/CI `skill/`, not raw atomics, not the repository root, and not
the top-level `skill/` directory. Generated `skill/` is ignored and not tracked
as source. The build writes a local `.skill.zip` payload; the published GitHub
Release asset is the same checked payload renamed to `.skill`. Do not re-zip
the repository root. `package.ps1` calls the manifest-backed Python packager,
validates generated package shape, excludes repo/dev harness roots, and writes
slash-safe archive entries.

## Artifact Evidence

## v0.4.1.0 Corrected Published Release Asset

This records the corrected v0.4.1.0 GitHub Release asset/provenance replaced
after the generated-runtime untracking, formalism/NLA, and release-claim
corrections. The public release asset is rebuilt from tracked atomics through
ignored generated `skill/`; raw atomics are not packaged. The public release
asset remains the checked `.skill` payload, not the `.skill.zip` build
intermediate.

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.4.1.0.skill` |
| Local zip build | `build/daee-epistemics-v0.4.1.0.skill.zip` |
| Local release asset copy | `build/daee-epistemics-v0.4.1.0.skill` |
| SHA256 | `532C47E100607627006C214FC2F43BD36F4C351A4803A489E023184601AEEE37` |
| Size | `584569` bytes |
| Entries | `20` |
| Notation-surface gate commit | `676396e0edc04103d603c9a68ecbc6f3d4e30356` |
| Source commit authority | Uploaded provenance JSON records the exact source commit used for the release asset. |
| Worktree state | Public v0.4.1.0 release asset/provenance refreshed after field-operator notation-surface correction |
| Branch | `main` |
| Contract version | `0.4.0.0` |
| Source/runtime tracking status | Corrected: `atomics/skill/**` tracked; `skill/**` ignored/generated |
| Generated runtime manifest SHA256 | `F6AA88138665781D5AEC9E429BFB84D7F6430B371F90481C370D2AF11F9A1381` |
| GitHub Release visibility | Public v0.4.1.0 release asset/provenance replaced; no `.skill.zip` asset uploaded |
| Provenance file | Published asset: `daee-epistemics-v0.4.1.0.provenance.json` |

Prior corrected asset evidence retained for provenance continuity:

| Field | Value |
| --- | --- |
| Prior package source commit | `517a9f133b6bc11f7f9b4dc1160f461c58b9e94e` |
| Prior SHA256 | `184D370534DE9E6FFC10C736CDD5C96C15D28761C5ED86156228930F95B4C59E` |
| Prior size | `557920` bytes |
| Status | Superseded by the notation-surface package artifact above; retained so release history remains auditable. |

Candidate package shape:

```text
SKILL.md
references/
compiled-module-map.json
build-manifest.json
README.md
```

Forbidden top-level archive entries checked absent:

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
```

## v0.4.0.0 Published Release Asset

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.4.0.0.skill` |
| SHA256 | `78C2BECE8818DEFF10C8CEF1A1578D9B54D0929950460681D04DC4F885576D0C` |
| Size | `554776` bytes |
| Entries | `20` |
| Source commit | `v0.4.0.0 release commit; see release tag` |
| GitHub Release visibility | Published historical release artifact for evidence-gated operator runtime and NS/register hardening |
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

## v0.4.0.0 Package-Bound Smoke Evidence

v0.4.0.0 package-bound smoke evidence is retained locally under ignored
`.daee/v0.4.0.0-current-release-smokes/` and validated with:

```powershell
python tools/check_smoke_artifacts.py --root .daee/v0.4.0.0-current-release-smokes --require-current-release-smokes
```

The retained suite is local, package-bound evidence for the v0.4.0.0 package
SHA. It is not committed, not packaged, not v0.4.1.0 replacement proof, and not
a universal semantic-grading claim.

Smoke families:

- hard moral-protest / source-worldview canary;
- predication / attribute canary;
- naturalist / transmission canary;
- child-mode local evidence boundary canary.

Evidence boundaries:

```text
source repo -> current tracked atomics, tools, tests, docs, and workflows
generated runtime -> ignored local/CI skill/ built from atomics
local package build output -> ignored build/*.skill.zip archive built from generated skill/
published release asset -> checked build/*.skill payload uploaded to GitHub Release
local smoke regression artifacts -> ignored smokes/ or .daee/ working directories
published package evidence -> public GitHub Release .skill asset, local/internal .skill.zip filename, SHA256, size, entries, and archive-root checks above
v0.4.0.0 package-smoke evidence -> ignored .daee/v0.4.0.0-current-release-smokes package-bound suite
local child-mode samples -> ignored .daee retained evidence, not release proof
dev-local checker PASS -> not universal semantic grading
live-host behavior -> not all-host parity or deterministic transformer execution
```
