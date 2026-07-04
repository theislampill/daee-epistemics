# 2026-07-03 Hardening/Fable Plan Closure Ledger

Scope: evaluated plans under `hardening/` and `fablehardening/` from baseline
`c86b3c6673147b8802fe222373a165a37d4d24a8`.

Execution surface: isolated worktree
`_worktrees/daee-epistemics-hardening-all`, branch
`codex/hardening-all-20260703`.

No commit, push, tag, release, branch-protection mutation, publication,
provenance upload, or destructive history/file-custody mutation was performed.

## Status Key

| Status | Meaning |
| --- | --- |
| DONE | Implemented locally and verified by named checks. |
| OWNER-GATED | Requires maintainer/external decision or GitHub mutation. |
| ARTIFACT-GATED | Requires missing or intentionally gitignored smoke artifacts. |
| PARTIAL | Safe local slice landed; remaining acceptance criteria are larger or intentionally deferred. |
| SUPERSEDED/RECORDED | Existing code already covers the plan or a dated retained-corpus note records why the row is not a current gate. |

## Hardening Folder

| Row | Status | Evidence / note |
| --- | --- | --- |
| P0-01 branch protection | OWNER-GATED | Read-only GitHub check found no protection/rulesets; no mutation was authorized. |
| P0-02 changelog/TODO cross-reference | DONE | `CHANGELOG.md`, `TODO.md`, and metacompliance canon updated; `python tools/check_metacompliance_current_canon.py` PASS. |
| P0-03 stale CHANGELOG/release default | DONE | `CHANGELOG.md` backfilled through v0.4.5.0; release workflow default updated to `v0.4.5.0`; metacompliance PASS. |
| P0-04 PyYAML unpinned | DONE | Added `requirements-ci.txt`; CI and release workflow install from it. |
| P0-05 dead 7.7MB JSON | OWNER-GATED | File remains tracked (`8036407` bytes). No tool/workflow consumer found, but docs reference it as historical archaeology. LFS vs release-asset custody is an explicit maintainer decision. |
| P0-06 local dependency manifest | DONE | Added `requirements-dev.txt`; README/AGENTS document local install and `tools/run_local_ci.py`. |
| P1-07 README stale version example | DONE | README/release references updated to current release-boundary wording. |
| P1-08 owner activation ordering schema drift | DONE | `tools/check_ir_instance_integrity.py` accepts and validates `owner_activation_ordering` shape. |
| P1-09 no single local CI command | DONE | Added `tools/run_local_ci.py`; CI calls it; release workflow now calls it before packaging. |
| P1-10 no inference-time verifier plan | DONE | Output preflight language now states prompt-level scope; `TODO.md` tracks a live output verifier. |
| P1-11 Codex subprocess env inherit | DONE | `run_staged_current_skill_smoke.py` and `run_current_skill_smoke.ps1` now use `shell_environment_policy.inherit=none`; self-test and PowerShell sidecar proof passed. |
| P1-12 negative examples unenforced | DONE | Added `tools/check_negative_example_mimicry.py`, 14 manifest rows, CI wrapper wiring; checker PASS. |
| P2-13 hard-smoke manifest trusted verdicts | PARTIAL | Stage07/staged runner validation is hardened elsewhere; hard-smoke manifest recomputation and live Grapher regeneration remain a follow-up lane. |
| P2-14 staged self-test runtime | PARTIAL | No correctness change made; large runtime/profiling optimization remains a performance lane. |
| P2-15 diagnostic IR field_witness schema disconnect | SUPERSEDED/RECORDED | Current schema already contains the real `owner_activations`/NAR/projection surfaces; broader schema coverage audit remains useful. |
| P2-16 retained-corpus coverage breadth | PARTIAL | Added wrapper coverage for fixture-level public grouping, ACT self-test, Shannon finite-fold retained outputs, and reproducibility fixtures. Corpus-wide public grouping/MRP scans still fail on historical retained outputs with dated contract notes. |
| P2-17 CI parallelization | PARTIAL | CI/release parity centralized through `tools/run_local_ci.py`; actual parallel job graph remains a performance lane after P2-14. |
| P2-18 semantic faithfulness naming/boundary | DONE/PARTIAL | Added `docs/proof-class-taxonomy.md`, bounded NLA wording, and docstring repair. A true semantic-replay grader remains a future plan. |

## Fable Hardening Folder

| Row | Status | Evidence / note |
| --- | --- | --- |
| P0-1 bold Land gate / MRP regex hardening | DONE | Bold `Land(...)` and superscript cases covered; MRP route/mid-reread checks PASS. |
| P0-2 retained corpus/current invariant reconciliation | PARTIAL | Manifest contract notes already mark unclaimed retained drift; corpus-wide advisory scans confirm old retained rows fail newer per-Land MRP/grouping contracts. No retained historical output was mutated. |
| P0-3 Smoke C promotion protection | ARTIFACT-GATED | Promotion helper self-test passes; actual fresh Smoke C promotion requires current smoke artifacts not committed in this worktree. |
| P0-4 manual contract relocation | DONE | Non-droppable manual contract moved to `atomics/skill/references/rubrics/non-droppable-manual-contract.md`; compiler binds it through `EXTRA_INPUTS`; runtime freshness PASS. |
| P1-1 live/verified marker and fabricated validation ban | DONE/PARTIAL | Manual contract requires `not_checker_verified: true` absent verifier evidence; render checker rejects fabricated validator/quality-gate verdicts with invalid fixture. Full live-output linter remains future tooling. |
| P1-2 Stage08 sidecar verification | SUPERSEDED/RECORDED | Existing handshake checker verifies B.5.4.1 sidecar schema/builder/role/hash bindings and artifact bindings; `check_staged_runtime_handshake.py` PASS. |
| P1-3 Stage07 release_validation attestation | PARTIAL | Runner re-runs release validators; handshake rejects missing/failed model-mode validation. Full recomputation of every attested key inside the replay checker remains a follow-up lane. |
| P1-4 normalizer transparency/strict mode | PARTIAL | Release notes/logs disclose compiled-output normalizers; no strict model-routes mode was added in this run. |
| P1-5 checker wiring | PARTIAL | Local/CI wrapper now centralizes the active checker set and includes added safe offline gates. Retained-corpus-wide public grouping/MRP gates remain blocked by documented historical drift. |
| P1-6 claim-boundary patch plan | DONE | Non-claims doc, safety boundary wording, release-note/README/VISION/docstring edits, metacompliance PASS. |
| P1-7 single-signature fixtures and Stage05 tooth | DONE/PARTIAL | Added Stage05 semicolon-curl diagnostic canary; handshake invalid count rose to 108. More minimal false-pass fixture splitting remains useful but is not required for current PASS. |
| P1-8 proof-class taxonomy | DONE | Added `docs/proof-class-taxonomy.md`; retained classification is `SIDECAR_BACKED_STRUCTURAL`; NLA references bounded. |
| P2-1 release workflow parity/readback/tag policy | PARTIAL/OWNER-GATED | Release workflow now calls `tools/run_local_ci.py`; post-release readback automation and tag immutability enforcement require owner/release decisions. |
| P2-2 safety/custody boundaries | DONE/PARTIAL | Added safety prohibitions, concealment basis requirements, uptake/interior/fabricated-validation fixtures. No claim of manipulation-proof semantic coverage. |
| P2-3 release-record consistency | DONE | Changelog backfill and release-status wording repaired; metacompliance PASS. |
| P2-4 artifact-binding upgrades | PARTIAL | Stage08 retained artifact bindings already hash-check; broader field_witness schema/certificate output-binding/origin-hash upgrades are future lanes. |
| P2-5 checker hygiene/residual guards | DONE/PARTIAL | Removed shadowed `check_mrp_block`; added Stage05 diagnostic canary; docs already prescribe four-checker visible-output battery. Replay refusal broadening and external sidecar loading remain follow-up. |

## Verification Snapshot

Representative checks run during closure:

```text
python tools/build_framework_pipeline.py -> PASS
python tools/build_compiled_runtime.py -> PASS
python tools/build_docs_index.py -> PASS
python tools/check_compiled_runtime_freshness.py -> PASS
python tools/check_metacompliance_current_canon.py -> PASS
python tools/check_manual_smoke_render_contract.py -> PASS
python tools/check_staged_runtime_handshake.py -> PASS
python tools/check_negative_example_mimicry.py -> PASS
python tools/check_ttp_operator_contracts.py --strict -> PASS
python tools/check_mid_reread_pressure.py -> PASS
python tools/check_mrp_route_invariants.py -> PASS
python tools/check_concealment_mode.py -> PASS
python tools/check_tlang_response_closure.py -> PASS
python tools/check_shannon_finite_fold.py --outputs retained outputs -> PASS
python tools/check_reproducibility.py -> PASS
python tools/run_staged_current_skill_smoke.py --self-test -> PASS
pwsh -NoProfile -ExecutionPolicy Bypass -File tools/run_current_skill_smoke.ps1 -Root . -ProofSidecarSelfTest -> PASS
```

Known non-green advisory probes, intentionally not wired as hard gates:

```text
python tools/check_act_surface_syntax.py --outputs retained outputs -> FAIL on pilot-v17 target= dialect, already contract-noted.
python tools/check_public_burden_grouping.py --outputs retained outputs -> FAIL on historical pilot-v17 grouping drift.
python tools/check_mid_reread_pressure.py --outputs retained outputs -> FAIL on historical Gate88/pilot per-Land MRP visibility under newer contract.
```

## Handoff Boundary

Local safe implementation is closed as far as this run can truthfully take it
without owner release/security decisions or fresh smoke artifacts. Remaining
work should be picked up as explicit lanes in `gpthardeningfinal/`, not hidden
behind a global "all complete" claim.

## 2026-07-04 Green-State Repair (Plan 18) — closure-ledger correction

The 2026-07-03 snapshot above under-reports the worktree's real CI state. Verified
2026-07-04 (smoke-proven): the WT would fail its own `tools/run_local_ci.py`
wrapper with **8 hard-gate failures**, and this section corrects the three gaps
named in `gpthardeningfinal/20-verified-state-annex-2026-07-04.md` §4:

1. The earlier "Promotion helper self-test passes" is FALSE — `promote_retained_proof_case.py --self-test` FAILED (root cause E) until this run's repair.
2. Six hard-gate failures (root causes A×4, B, C) were omitted entirely.
3. The advisory-probe count was three; six advisory probe classes actually fail.

### OWNER-DECISION rows (recorded before executing B and D)

```
OWNER-DECISION | OD-02 | 2026-07-04 | Root cause B: atomics/skill/SKILL.md (80,418 chars) exceeds the 80,000-char control-plane guard (check_recursion_collapse_noetic_frame) after the WT safety paragraph was added |
  CHOICE: B1 trim — relocate the safety paragraph into the canonical referenced rubric references/rubrics/output-release.md; DO NOT raise the guard. Additionally restore check_metacompliance ROOT_MAX_CHARS 81_000 -> 80_000 (the WT had raised it) to honor "do not raise the threshold." |
  AUTH-CLASS: rule-scoping (strengthening) |
  EVIDENCE-SEEN: char count 80,418; the +7-line diff; sibling rubric load_when |
  UNBLOCKS: Plan 18 Phase 4, Plan 10, Plan 16 |
  READBACK: pending (SKILL.md char count < 80,000; recursion_collapse green; metacompliance green)
OWNER-DECISION | OD-03 | 2026-07-04 | Root cause D: the new concealment basis-qualifier safety rule breaks bound row d3-mixed-concealment-retained-breadth on 3 historical retained outputs |
  CHOICE: D1 narrow dated grandfathering — exempt ONLY the 3 named legacy retained-corpus outputs (mixed-family-authority, academic-prestige-authority, therapy-moral-tribunal) via a dated exemption in check_concealment_mode.py; keep the rule live on all fixtures, live output, and non-legacy surfaces. No historical output is mutated. |
  AUTH-CLASS: rule-scoping (narrow, dated) |
  EVIDENCE-SEEN: the 3 failing outputs; the d3 validator_binding (outputs-checker over check_concealment_mode); the rule at check_concealment_mode.py:506-513 |
  UNBLOCKS: Plan 18 Phase 4, Plan 05, Plan 10 |
  READBACK: pending (check_retained_row_claims green; rule still enforced on non-grandfathered surfaces)
```

Note: `trinitarian-j173-repair-v6` also fails the concealment rule as an ADVISORY
corpus probe (not a bound row, not a hard gate). Per OD-03's "only ... the bound-row
break" scope it is NOT grandfathered here; it is recorded as advisory drift for
Plan 05's requalification allowlist.

### Root-cause repair rows (this run, no commit/push/tag/release performed)

| Root cause | Repair | Status | Smoke B (2026-07-04) |
| --- | --- | --- | --- |
| A (×4 checkers) | Added YAML front matter to `atomics/skill/references/rubrics/non-droppable-manual-contract.md`; rebuilt (it is a hash-bound EXTRA_INPUT) | DONE | `check_stub_integrity`, `check_frontmatter` (both), `check_coverage`, `check_framework_pipeline`, `check_compiled_runtime_freshness` all GREEN |
| C | Restored the required token `python tools/check_register_formalism_bridge.py` to `AGENTS.md` (kept the wrapper-centralization edit) | DONE | `check_register_formalism_bridge` GREEN |
| E | `build_entry` classification literal `SIDECAR_BACKED_PROOF` -> `SIDECAR_BACKED_STRUCTURAL` (`promote_retained_proof_case.py:310`); the `b5_full_ir_projection_sidecar` field was already built conditionally, so no second edit needed | DONE | `promote_retained_proof_case.py --self-test` GREEN (false-pass canary still rejected) |
| D (partial) | Added dated `LEGACY_BASIS_QUALIFIER_EXEMPT` for the 3 OD-03-named legacy outputs in `check_concealment_mode.py`; rule stays live on fixtures + all non-legacy surfaces | PARTIAL — see correction below | 3 named outputs now pass; `check_retained_row_claims` still RED on a 4th output |
| B | HELD — safety-pin collision (see OD-02 amendment) | OWNER-GATED | `check_recursion_collapse_noetic_frame` RED by design |

Gate tally after this run: **6 of 8 hard gates GREEN** (A×4, C, E). Two remain
owner-gated: **B** (recursion_collapse) and **D** (retained_row_claims, on the
uncovered 4th output). `run_local_ci.py --strict-pwsh` was NOT run to a full
success line because it stops at the first remaining red gate; no commit, push,
tag, release, provenance, or branch-protection action was performed.

### OD-02 amendment (root cause B — HELD on safety-pin collision)

During execution the B1 "move the safety paragraph to a rubric" step collided
with a deliberate safety canon: `check_metacompliance_current_canon.py` REQUIRES
the safety sentence tokens `"Safety boundary: diagnosed deformations"` and
`"never constructs or optimizes one"` in BOTH `ROOT_REQUIRED` (checked against
`atomics/skill/SKILL.md`, checker line 287) AND `GENERATED_REQUIRED` (checked
against `skill/SKILL.md`, line 303). Arithmetic: `atomics/skill/SKILL.md` is
80,418 chars (418 over the 80,000 guard); the safety paragraph is ~439 chars;
removing it to get under strips the safety boundary from the two places it is
pinned, and a compact anchor that keeps both tokens is still ~250 chars (only
~185 saved -> 80,233, still over). So B1-as-literally-specified is
self-contradictory given the safety pins: you cannot get the root under 80,000
by trimming only safety text while keeping the safety pin satisfied in the root.

The metacompliance cap was therefore NOT restored to 80,000 this run — with the
paragraph still in place (80,418) that would have created a NEW red gate.

Owner refinement needed (recommended options):
- **B1a (recommended): relocate the safety canon.** Move the full text to
  `references/rubrics/output-release.md` (source) AND move both metacompliance
  pins (ROOT + GENERATED) to that rubric's source and compiled locations, so the
  safety boundary stays present-required and canonical but is anchored in the
  release-governance rubric (loaded whenever output is shaped/released — an apt
  home) instead of the root control plane. Then restore the cap to 80,000. This
  re-anchors WHERE the safety boundary lives, which is why it is an owner call.
- **B1b: keep the safety anchor in root, trim ~200 chars of genuinely-redundant
  NON-safety root content** to get under (needs owner OK to trim non-safety
  text — outside the safety-text-only scope OD-02 authorized).
- **B2 (declined by owner): raise the guard.** Not pursued.

### OD-03 correction (root cause D — failing set is 4, not 3)

Annex 20 §3.1 #7 recorded the d3 basis-qualifier failing set as 3 outputs; that
was a documentation undercount caused by a truncated verification transcript.
The actual set of `d3-mixed-concealment-retained-breadth` members that fail the
basis-qualifier rule is FOUR: `cd9a-mixed-concealment`, `mixed-family-authority`,
`academic-prestige-authority`, `therapy-moral-tribunal` (smoke-proven 2026-07-04;
`dad8-science-only-c8` passes). OD-03 named only the 3 I had documented, so the
exemption landed for 3; `check_retained_row_claims` stays RED on
`cd9a-mixed-concealment`. Because this is a SAFETY-rule exemption and my code
carries the guard "do NOT extend without a dated OWNER-DECISION row," the 4th
output is HELD for owner confirmation rather than added unilaterally.
Recommended: extend OD-03 to include `cd9a-mixed-concealment` (identical legacy
class, needed to achieve OD-03's own goal of fixing the bound-row break) — a
one-line dated amendment closes D. `trinitarian-j173-repair-v6` remains
advisory-only (not a bound row) and is not part of this decision.

### 2026-07-04 Owner approvals (executed)

```
OWNER-DECISION | OD-02a | 2026-07-04 | Approve B1a: re-anchor the safety canon into the release-governance rubric |
  CHOICE: Move the safety paragraph out of atomics/skill/SKILL.md into atomics/skill/references/rubrics/output-release.md, which compiles into the runtime bundle skill/references/runtime-output-governance.md (VERIFIED in generated/runtime loading path via compiled-module-map.json bundle_path). Move the metacompliance pins: remove the 2 safety tokens from ROOT_REQUIRED (atomics/skill/SKILL.md) and GENERATED_REQUIRED (skill/SKILL.md); add them to OWNER_REQUIRED[output-release.md] (source) and a new generated-bundle check against skill/references/runtime-output-governance.md (runtime). Restore ROOT_MAX_CHARS 81_000 -> 80_000. Do NOT raise, weaken, or bypass. |
  AUTH-CLASS: rule-scoping (relocation + strengthening cap) |
  UNBLOCKS: Plan 18 recursion_collapse; Plan 10 |
  READBACK: pending
OWNER-DECISION | OD-03a | 2026-07-04 | Approve extending the dated legacy exemption from 3 to exactly 4 |
  CHOICE: Add cd9a-mixed-concealment to LEGACY_BASIS_QUALIFIER_EXEMPT (now 4: cd9a-mixed-concealment, mixed-family-authority, academic-prestige-authority, therapy-moral-tribunal). Do NOT include trinitarian-j173-repair-v6. Rule stays live on fixtures, new/live outputs, and all non-grandfathered surfaces; invalid fixture must still fail. |
  AUTH-CLASS: rule-scoping (narrow, dated) |
  UNBLOCKS: Plan 18 retained_row_claims; Plan 05 |
  READBACK: DONE 2026-07-04 — LEGACY_BASIS_QUALIFIER_EXEMPT now holds exactly the 4 named outputs (trinitarian-j173-repair-v6 excluded); check_retained_row_claims GREEN (d3 target PASS, cases=5); check_concealment_mode fixtures GREEN with invalid fixture source-mode-without-basis STILL REJECTED (rule live).
```

### Readback (both decisions executed, Plan 18 to 8/8 green)

OD-02a (B1a) READBACK — DONE 2026-07-04:
- Safety text relocated to `atomics/skill/references/rubrics/output-release.md`; compiles into runtime bundle `skill/references/runtime-output-governance.md` (safety sentence present there, count 1) and REMOVED from `skill/SKILL.md` (count 0).
- `atomics/skill/SKILL.md` = 79,979 chars (< 80,000); `check_recursion_collapse_noetic_frame` GREEN; `ROOT_MAX_CHARS` restored 81_000 -> 80_000; guard NOT raised.
- Metacompliance pins moved: removed from `ROOT_REQUIRED` and `GENERATED_REQUIRED`; added to `OWNER_REQUIRED[output-release.md]` (source) and new `GENERATED_BUNDLE_REQUIRED[references/runtime-output-governance.md]` (runtime); `check_metacompliance_current_canon` GREEN.
- Safety sentence not weakened/deleted/bypassed; still present-required in source rubric + compiled runtime bundle.

Regression found and fixed during B1a: stripping was needed because root-cause-A
front matter had been inlined verbatim into `skill/SKILL.md`, shifting
`Matched owner/TTP route` to line 121 and breaking the manual-render 120-line
check (`d2-closing-formulation-retained-breadth`). Fixed correctly in
`tools/build_compiled_runtime.py` (strip manual-contract front matter before
inlining; source front matter retained for the A-checkers). Token now at line
109; `check_manual_smoke_render_contract` GREEN.

Plan 18 gate tally: 8 of 8 hard gates GREEN (A×4, B, C, D, E), plus metacompliance,
freshness, and manual-render GREEN. No commit, push, tag, release, provenance, or
branch-protection action performed.

### run_local_ci success line is commit-gated (honest boundary)

`python tools/run_local_ci.py --strict-pwsh` cannot print its `PASS (N commands)`
success line in the uncommitted worktree: its COMMANDS list includes
`git diff --exit-code -- skill/SKILL.md` (and the same for
`atomics/skill/references/diagnostics/framework-pipeline.md`), which compare the
regenerated generated files against the git index/HEAD. Because the entire WT
delta is uncommitted (branch tip = main@c86b3c6), the freshly-rebuilt
`skill/SKILL.md` legitimately differs from HEAD's older committed copy, so those
two steps exit 1 and the runner stops. This is NOT a code failure — it is a
freshness-vs-committed gate that only passes once the generated files are
committed (OD-05, owner-gated, not authorized this run). The actual freshness
property is independently proven GREEN by `check_compiled_runtime_freshness.py`.
Every other COMMANDS entry (all builders + all checkers + staged/pwsh self-tests)
passes; see the run report for the full pass list with only the two commit-gated
`git diff` steps skipped. To obtain the literal success line, an owner commits the
regenerated tree (OD-05) and re-runs; nothing else is red.
