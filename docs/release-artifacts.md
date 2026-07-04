# Release Artifacts

This file records published package artifacts and local release-candidate
package evidence. Binary skill archives are not committed to the source
repository; GitHub Releases are the binary distribution surface for published
`.skill` assets.

Build the package locally from tracked atomics through generated `skill/`:

```powershell
python tools/build_framework_pipeline.py
python tools/build_compiled_runtime.py
python tools/package_skill.py build\daee-epistemics-v0.4.2.0.skill.zip
Copy-Item build\daee-epistemics-v0.4.2.0.skill.zip build\daee-epistemics-v0.4.2.0.skill
```

The package script archives the canonical packageable contents selected from
generated local/CI `skill/`, not raw atomics, not the repository root, and not
the top-level `skill/` directory. Generated `skill/` is not repository source:
`skill/SKILL.md` is force-tracked as the generated-runtime freshness-gate surface
(CI fails on a stale tracked copy via `git diff --exit-code -- skill/SKILL.md`
after rebuild), and all other `skill/**` paths remain ignored/generated. The build writes a local `.skill.zip` payload; the published GitHub
Release asset is the same checked payload renamed to `.skill`. Do not re-zip
the repository root. `package.ps1` calls the manifest-backed Python packager,
validates generated package shape, excludes repo/dev harness roots, and writes
slash-safe archive entries.

Tracking-status note for current claims: since the v0.4.3.0 source boundary
(`9a57961395643a1b56a1c39fcb8026d17d1ca6d7`), `git ls-files skill` returns
exactly `skill/SKILL.md`. Historical release-status rows below retain their
original wording as historical facts and are not retroactively rewritten; see
`docs/audits/v0.4.4.x-tracked-generated-skill-md-policy.md`.

## Artifact Evidence

## v0.4.5.0 Release Package / Provenance Status

v0.4.5.0 public artifact status: replaced on 2026-06-18 after the ACT/MRP
round-robin false-pass hardening and fresh 4/4 Smoke C matrix. The original
2026-06-15 publication from source boundary
`4a85628a5be8194611ec2b303bc491e6281d75ed` is superseded. The current package
is built from hardening source boundary
`8c14e28fbcf440275f4d143a9b7cadc6148aa5a9`. The `.skill.zip` file is a local
build intermediate only and was not uploaded.

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.4.5.0.skill` |
| Local zip build | `build/daee-epistemics-v0.4.5.0.skill.zip` |
| Local package copy | `build/daee-epistemics-v0.4.5.0.skill` |
| SHA256 | `67FF081EF34B9CBE3BF03309F03DFAEF1C8D471640CED715D299A90344DFAB6F` |
| Size | `711841` bytes |
| Entries | `21` |
| Source commit recorded in provenance | `8c14e28fbcf440275f4d143a9b7cadc6148aa5a9` |
| Source state | ACT/MRP false-pass hardening with retained invalid secularism fixture, intermediate continuation normalization, Stage05 diagnostic punctuation normalization, no-model canaries PASS, Smoke C 4/4 matrix PASS, release replacement readback PASS |
| Branch | `main` |
| Contract version | `0.4.0.0` |
| Source/runtime tracking status | `atomics/skill/**` tracked; `skill/**` ignored/generated except force-tracked `skill/SKILL.md` freshness-gate surface |
| Generated runtime manifest SHA256 | `28F55E498E698F2E185EF0EFD64A633571C24ACC05A9DA14B5BFAE97D6C4A02D` |
| Compiled module map SHA256 | `6B31DF9899A64B837D96D8EF9AD786F066ABE2C5395FB76147BE7C1F58540C56` |
| GitHub Release visibility | Published at `https://github.com/theislampill/daee-epistemics/releases/tag/v0.4.5.0`; annotated tag peels to `8c14e28fbcf440275f4d143a9b7cadc6148aa5a9` |
| Provenance file | Release asset: `daee-epistemics-v0.4.5.0.provenance.json` generated from `build/daee-epistemics-v0.4.5.0.provenance.json` |
| Provenance SHA256 | `E0BE60F71D78184206846918AE9329B5CF28378F297338E74A6B181381324239` |
| Source-boundary proof + package validation | The historical false-pass output is rejected by `tools/check_mrp_route_invariants.py`; no-model canaries passed; Smoke C 4/4 one-shot matrix ran from the worktree at package source commit `8c14e28` through the staged harness and passed Stage07, MRP parity, Stage08, and direct validators before release replacement; package artifact validation PASS; self-contained package PASS; local and downloaded provenance checks PASS. Cross-host/paraphrase proof, arbitrary-input correctness, single-output model-emitted proof, and guaranteed `T_lang` uptake are not claimed. |

The v0.4.5.0 release assets include the canonical `.skill` payload and package
provenance JSON only:

- `daee-epistemics-v0.4.5.0.skill`
- `daee-epistemics-v0.4.5.0.provenance.json`

No `.skill.zip` asset was uploaded. Raw Smoke C artifacts remain local
custody/proof evidence and are not release assets. OSM/CSCG was an aliasing and
hidden-state audit lens only, not release proof. No cross-host/paraphrase proof,
guaranteed `T_lang` uptake, or universal semantic grading is claimed.

The downloaded package/provenance pair is checked with:

```powershell
python tools/check_release_provenance.py --provenance .daee\release-readback\v0.4.5.0-repair-20260618-0755\daee-epistemics-v0.4.5.0.provenance.json --package .daee\release-readback\v0.4.5.0-repair-20260618-0755\daee-epistemics-v0.4.5.0.skill --manifest skill\build-manifest.json --compiled-map skill\compiled-module-map.json
```

## v0.4.4.0 Release Package / Provenance Status

v0.4.4.0 public artifact status: published after Gate88 four-smoke closure and
retained proof-corpus promotion. The package is built from the retained-proof
source boundary `651b5b98dd7bf81be258ebe29fe43bab3a073eb2`. The `.skill.zip`
file is a local build intermediate only and was not uploaded.

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.4.4.0.skill` |
| Local zip build | `build/daee-epistemics-v0.4.4.0.skill.zip` |
| Local package copy | `build/daee-epistemics-v0.4.4.0.skill` |
| SHA256 | `011E5EAA603747E126A0E403B9F22174043936E827235F423314D312ECE43CE0` |
| Size | `711590` bytes |
| Entries | `21` |
| Source commit recorded in provenance | `651b5b98dd7bf81be258ebe29fe43bab3a073eb2` |
| Source state | Gate88 4/4 Stage08 matrix pass, direct validator replay, retained proof promotion, and CI/Pages PASS before package build |
| Branch | `main` |
| Contract version | `0.4.0.0` |
| Source/runtime tracking status | `atomics/skill/**` tracked; `skill/**` ignored/generated |
| Generated runtime manifest SHA256 | `CFC21BDFCF7725EF451FD1CD6DD87DB59EE066B971CF8BE1DBB146A518C7F6E7` |
| Compiled module map SHA256 | `D00D8A752B766978D5A949CF5304489AD9E78EF7EF0D14610E7877E256837800` |
| GitHub Release visibility | Published at `https://github.com/theislampill/daee-epistemics/releases/tag/v0.4.4.0`; annotated tag peels to `651b5b98dd7bf81be258ebe29fe43bab3a073eb2` |
| Provenance file | Release asset: `daee-epistemics-v0.4.4.0.provenance.json` generated from `build/daee-epistemics-v0.4.4.0.provenance.json` |
| Provenance SHA256 | `899BDAD2860153ADFE6D75C3D0296BC6BABE39D45727373CD1424F22DFF57E0A` |
| Package-bound proof | Gate88 4/4 one-shot matrix passed through Stage08 before package publication; direct replay validators passed across all four Gate88 outputs; retained proof corpus promotion passed for row scope `B.1 B.2 B.3 B.4 B.5 T_lang`; package artifact validation PASS; self-contained package PASS; local and downloaded provenance checks PASS. Cross-host/paraphrase proof is not claimed. |

The v0.4.4.0 release assets include the canonical `.skill` payload and package
provenance JSON only:

- `daee-epistemics-v0.4.4.0.skill`
- `daee-epistemics-v0.4.4.0.provenance.json`

No `.skill.zip` asset was uploaded. Raw Gate88 smoke artifacts remain local
custody/proof evidence and are not release assets. No cross-host/paraphrase
proof, guaranteed `T_lang` uptake, or universal semantic grading is claimed.

The downloaded package/provenance pair is checked with:

```powershell
python tools/check_release_provenance.py --provenance build\download-verify-v0.4.4.0-20260607\daee-epistemics-v0.4.4.0.provenance.json --package build\download-verify-v0.4.4.0-20260607\daee-epistemics-v0.4.4.0.skill --manifest skill\build-manifest.json --compiled-map skill\compiled-module-map.json
```

## v0.4.3.5 Release Package / Provenance Status

v0.4.3.5 public artifact status: published on the existing GitHub Release for
tag `v0.4.3.5` after the docs-truthfulness/source-boundary checkpoint. The
package is built from the tagged source boundary
`da68ae87ef74424a081a3bf96f673106d9ebd60e`. The `.skill.zip` file is a local
build intermediate only and was not uploaded.

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.4.3.5.skill` |
| Local zip build | `build/daee-epistemics-v0.4.3.5.skill.zip` |
| Local package copy | `build/daee-epistemics-v0.4.3.5.skill` |
| SHA256 | `7B1050DF02077198E3F1B6FA7C56C5DDCE6B6BB8444E543FA5350238D33ED24C` |
| Size | `702030` bytes |
| Entries | `21` |
| Source commit recorded in provenance | `da68ae87ef74424a081a3bf96f673106d9ebd60e` |
| Source state | Docs-truthfulness source boundary tag with live CI and Pages PASS before package build |
| Branch | `main` |
| Contract version | `0.4.0.0` |
| Source/runtime tracking status | `atomics/skill/**` tracked; `skill/**` ignored/generated |
| Generated `SKILL.md` SHA256 | `FEEA5664B5010C606545395D7F9913C6B94832634986CD408344C9D19336775A` |
| Generated runtime manifest SHA256 | `1AA08F70352D62BED557DFE0DC17117B7A8FEED07337DC64B38F889B19291F61` |
| Compiled module map SHA256 | `A7872365723E8DA9130A840C4FE729360BE3650F80FBA0926075138D9A045FCE` |
| GitHub Release visibility | Published at `https://github.com/theislampill/daee-epistemics/releases/tag/v0.4.3.5`; remote tag peels to `da68ae87ef74424a081a3bf96f673106d9ebd60e` |
| Provenance file | Release asset: `daee-epistemics-v0.4.3.5.provenance.json` generated from `build/daee-epistemics-v0.4.3.5.provenance.json` |
| Provenance SHA256 | `AEEC6318DBBA484ECD1E1F0637378038F255B9FF905EBDBE5D56E663D0AFA607` |
| Package-bound proof | Full release preflight PASS from a clean detached `v0.4.3.5` tag worktree; package artifact validation PASS; self-contained package PASS; local provenance check PASS; uploaded assets were downloaded back from GitHub and hash/provenance verified. Cross-host/paraphrase proof is not claimed. |

The v0.4.3.5 release assets include the canonical `.skill` payload and package
provenance JSON only:

- `daee-epistemics-v0.4.3.5.skill`
- `daee-epistemics-v0.4.3.5.provenance.json`

No `.skill.zip` asset was uploaded. No A.13 hard-register schema acceptance,
D.8 cleanup completion, full IR decode, guaranteed `T_lang` uptake,
cross-host/paraphrase proof, or new model-smoke proof is claimed.

The downloaded package/provenance pair is checked with:

```powershell
python tools/check_release_provenance.py --provenance build\download-verify-v0.4.3.5-20260531\daee-epistemics-v0.4.3.5.provenance.json --package build\download-verify-v0.4.3.5-20260531\daee-epistemics-v0.4.3.5.skill --manifest skill\build-manifest.json --compiled-map skill\compiled-module-map.json
```

## v0.4.3.0 Release Package / Provenance Status

v0.4.3.0 public artifact status: published after corrected-goal closure. The stale
same-version assets were replaced only after source CI, package rebuild, package-bound
Boltzmann repeated-run proof, downloaded asset hash verification, and release provenance
verification. The public release name and tag are `v0.4.3.0`, not an RC label. Raw smoke
and visualizer outputs remain local diagnostic artifacts and are not committed or uploaded
as release assets.

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.4.3.0.skill` |
| Local zip build | `build/daee-epistemics-v0.4.3.0.skill.zip` |
| Local package copy | `build/daee-epistemics-v0.4.3.0.skill` |
| SHA256 | `6C096A0DF199D44BBFD26F8F73BC836C53AA76BBA7B63B5E80B0FAE390C6CF5E` |
| Size | `680020` bytes |
| Entries | `20` |
| Source commit recorded in provenance | `9a57961395643a1b56a1c39fcb8026d17d1ca6d7` |
| Source state | Corrected-goal source/checker/package gates passed locally before tag/release replacement |
| Branch | `main` |
| Contract version | `0.4.0.0` |
| Source/runtime tracking status | `atomics/skill/**` tracked; `skill/**` ignored/generated |
| Generated `SKILL.md` SHA256 | `C29609AC6C5546E00B1D44784F801E2675BF5073EF264FA891D8188D070A3696` |
| Generated runtime manifest SHA256 | `DE068C48E6447C00BFAD25BECEE5244B3F90B5DAA53143C11D41808234604B0D` |
| Compiled module map SHA256 | `2D9C455F2A0CE356AC3454BAD23B3A8654FA7BD2F4D80EA422DF9E04213DD1A0` |
| GitHub Release visibility | Published at `https://github.com/theislampill/daee-epistemics/releases/tag/v0.4.3.0`; remote tag peels to `9a57961395643a1b56a1c39fcb8026d17d1ca6d7` |
| Provenance file | Release asset: `daee-epistemics-v0.4.3.0.provenance.json` generated from `build/daee-epistemics-v0.4.3.0.provenance.json` |
| Package-bound proof | Local package artifact validation passed for the `.skill` release payload and its local `.skill.zip` build intermediate; package-bound Boltzmann run1/run2 passed syntax, strict MRP, manual, witness, mid-reread, formal reread, convergence, NLA, owner-plan, Grapher, and compare-runs; repeated-run fingerprints matched (`9376BCAE93F4`, `AB43E82A5170`, `D4BC08CD21C6`). Cross-host/paraphrase proof is not claimed. |

The v0.4.3.0 release assets include the canonical `.skill` payload and package provenance. The
`.skill.zip` file is a local build intermediate only and must not be uploaded as a GitHub Release
asset. The corrected-goal package includes register-derived burden floors, formal reread-state
semantics, field-witness convergence, bounded NLA structural faithfulness, LoopBreak enforcement,
legacy alias cleanup, and false-pass canaries. The literal Shannon/integral theorem and full
`T_lang` response-closure checker are outside v0.4.3.0 release claims.

The local package/provenance pair is checked with:

```powershell
python tools/check_release_provenance.py --provenance build\download-verify-v0.4.3.0-20260524-232840\daee-epistemics-v0.4.3.0.provenance.json --package build\download-verify-v0.4.3.0-20260524-232840\daee-epistemics-v0.4.3.0.skill --manifest skill\build-manifest.json --compiled-map skill\compiled-module-map.json
```

## v0.4.2.0 Release Package / Provenance Status

v0.4.2.0 public artifact status: published on the existing GitHub Release for tag
`v0.4.2.0`. The package/provenance pair below is the checked release payload. Raw
current-release smoke captures are local diagnostic artifacts and are not committed or uploaded as
release assets.

| Field | Value |
| --- | --- |
| Package filename | `daee-epistemics-v0.4.2.0.skill` |
| Local zip build | `build/daee-epistemics-v0.4.2.0.skill.zip` |
| Local package copy | `build/daee-epistemics-v0.4.2.0.skill` |
| SHA256 | `21B25FF08AD36E26A57BACEC785C635F49DEC06E84A6EE191F4F8A61870913A7` |
| Size | `594097` bytes |
| Entries | `20` |
| Source commit recorded in provenance | Generated at release time from the release source commit |
| Source state | Release-gate source/checker/smoke gates passed locally before tag/release |
| Branch | `main` |
| Contract version | `0.4.0.0` |
| Source/runtime tracking status | `atomics/skill/**` tracked; `skill/**` ignored/generated |
| Generated runtime manifest SHA256 | `240BCCCBEA373CD049585CCC885ED4FB44B9B86FB01BC3A414B537FED2AEA504` |
| Compiled module map SHA256 | `031C7522FD21F1F8DECF200BB2785D50976FB7FB7D99EF865B4BDDF6877AB608` |
| GitHub Release visibility | Existing GitHub Release updated: `https://github.com/theislampill/daee-epistemics/releases/tag/v0.4.2.0` |
| Provenance file | Release asset: `daee-epistemics-v0.4.2.0.provenance.json` generated from `build/daee-epistemics-v0.4.2.0.provenance.json` |
| Current-release smoke proof | Local 3-case package-bound smoke passed against this SHA (`CR-01` hard, `CR-02` misuse boundary, `CR-03` bounded answer), including witness-required live contract checks; raw captures are local diagnostic artifacts and are not committed |

Docs/index visual/SSOT/design consolidation is complete in tracked docs/generator/checker sources
and does not change the package payload or SHA above. The generated docs/index surfaces are
navigation evidence only, not runtime or smoke proof.

The local package/provenance pair passed:

```powershell
python tools/check_release_provenance.py --provenance build\daee-epistemics-v0.4.2.0.provenance.json --package build\daee-epistemics-v0.4.2.0.skill --manifest skill\build-manifest.json --compiled-map skill\compiled-module-map.json --release-artifacts docs\release-artifacts.md
```

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
SHA. It is not committed, not packaged, not later v0.4.x replacement proof, and not
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
