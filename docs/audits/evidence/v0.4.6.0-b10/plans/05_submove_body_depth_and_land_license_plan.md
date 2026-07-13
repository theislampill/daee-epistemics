# ANDON A05: Submove Body Depth and Land License

Priority: P0/P1 structural-integrity repair  
Primary pipeline location: `ⁿB -> {ⁿBᵢ[OPᵢ]} -> Land(ⁿB) -> ΔⁿB/Δκ`  
Implementation target: PR #9 branch `codex/v0.4.6.0-runtime-footprint` at planned head `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Regression status: `unproven`  
Plan status: implementation-ready after owner authorization and after Plans 02 and 04 establish pressure and owner-obligation IDs

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Plain-Language Result

DAEE already knows, in prose and in several final-output checkers, that an ACT line is only a pointer. The current Stage04 record does not make that rule true at the stage named “Burden execution / ACT.” It can pass with a well-formed ACT line and a `body_ref` even though no operation body exists anywhere in the Stage04 record. The stronger body test runs later, after Stage07 has authored public prose.

The fix is to make Stage04 produce one canonical, input-bound operation capsule for every executed submove. The capsule records the pressure before the operation, the owner mechanism actually applied, the state afterward, the local delta, residual pressure, and why the delta contributes to `Land(B)`. Stage07 then renders that already-validated capsule; it does not invent, repair, or paraphrase the missing operation after the execution stage has passed.

This does not claim that a schema can prove theological truth. It makes a missing operation structurally visible, gives human reviewers a stable evidence object to challenge, and prevents a heading, ACT row, or `body_ref` from impersonating execution.

## Abnormality and Current False-Pass

The current checked-in minimal Stage04 fixture is:

```text
tests/stage-contract-workbench/stage-04-burden-execution-act/minimal-valid/single-act-row.json
```

Planning-baseline identity:

```text
bytes: 2709
sha256: 8CB0C1A0D15C0B76FBD79B41703E410573AAE6E9E713BB6871A597D042D0AB29
```

It contains:

- one routed owner;
- one canonical ACT row;
- one bare `body_ref`;
- no `act_row_details`;
- no operation body;
- no before-state;
- no performed-operation evidence;
- no after-state;
- no residual;
- no independently dereferenceable Land license.

The maximal Stage04 fixture is:

```text
tests/stage-contract-workbench/stage-04-burden-execution-act/maximal-valid/multi-act-row-details.json
```

Planning-baseline identity:

```text
bytes: 4188
sha256: B5D01394B8C3246813F74037BB749D6825D97381FA1D190AE498AA9C43FDEDEA
```

It adds typed metadata (`owner_id`, `operation`, `register_axis`, `pressure`, and `delta_result`) but still contains no performed operation body. Both fixtures passed direct read-only replay at the planned head:

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
python tools\check_staged_runtime_handshake.py --explain-stage-failure --records tests\stage-contract-workbench\stage-04-burden-execution-act\minimal-valid\single-act-row.json
python tools\check_staged_runtime_handshake.py --explain-stage-failure --records tests\stage-contract-workbench\stage-04-burden-execution-act\maximal-valid\multi-act-row-details.json
```

Observed result for each command:

```json
{"status": "pass"}
```

This is a confirmed contract false-pass. The fixtures are valid under the current shape contract, but neither is sufficient release-bearing evidence for a stage that claims burden execution.

## Evidence Classification

### Confirmed

- `tools/check_staged_runtime_handshake.py::stage04_act_errors` requires `act_targets`, `act_burdens`, `act_body_refs`, and `act_rows`, validates canonical ACT grammar, checks body-ref membership/order, and rejects owners absent from Stage03.
- `act_row_details` is optional in the handshake checker. When present, most fields beyond burden and body ref are optional.
- The same Stage04 function shape is present in remote `main`, PR base, and PR head. PR9 added the explicit workbench fixtures; it did not introduce the underlying pointer-only acceptance rule.
- `tools/run_staged_current_skill_smoke.py` is stricter than the standalone checker: its producer instructions require `act_row_details`, and its normalizer requires typed owner/operation/register/delta metadata.
- Runner metadata is still not an operation body. Stage07 receives ACT rows and details, then authors the `TTP Operation Body:` prose later.
- `tools/check_manual_smoke_render_contract.py` already performs substantial final-output body checks. At the planned head, its fixture suite passed with 18 valid and 40 invalid fixtures.
- `tools/check_ttp_availability_canaries.py` already has a useful `body_ref_dereference` object and owner/delta joins. At the planned head, its fixture suite passed with 10 valid and 19 invalid fixtures.
- `schema/state-capsule.schema.json::completed_acts` currently carries body ref, owner, operation, register axis, delta result, and Land token, but not an operation-body object or hash.
- `tools/run_staged_current_skill_smoke.py::canonicalize_layer_b_owner_transition_facets` can rewrite selected Stage07 operation/result/contribution facets after model generation. That normalization must not be treated as proof that Stage04 performed the operation.

### Inferred

- Deferring body creation from Stage04 to Stage07 can encourage a proof-looking pipeline in which execution is declared first and prose is backfilled later.
- A canonical operation capsule should reduce thin-body and detached-witness failures because every downstream surface will join to the same evidence object.
- A deterministic Stage07 projection will reduce prompt/checker drift compared with asking Stage07 to regenerate the operation from compact metadata.

### Unproven

- This gap caused the captured Grok failure.
- v0.4.6.0 made body execution worse than v0.4.5.0.
- A structurally valid operation capsule is semantically correct, true, persuasive, or complete.
- Any fixed word count, paragraph count, or sentence count is sufficient for an operation.

## Existing Controls to Preserve

The patch must extend these controls, not replace or duplicate them:

| Existing control | What it already proves | Boundary to preserve |
| --- | --- | --- |
| Canonical ACT grammar in `check_staged_runtime_handshake.py` and `check_act_surface_syntax.py` | owner/operation/pressure/body-ref/delta/Land slots are parseable | Syntax is not execution |
| Stage03 owner eligibility join | Stage04 cannot invent an un-routed owner | Eligibility is not operation-body adequacy |
| Controlled owner-operation and delta vocabularies | owner, operation, and result tokens belong together | Vocabulary match is not case-specific performance |
| `check_manual_smoke_render_contract.py::is_operation_shaped_submove` | final public body has pressure, owner action, local state change, and Land contribution under existing heuristics | Structural/heuristic PASS is not semantic truth |
| `check_ttp_availability_canaries.py::row_is_complete` | canary rows cross-bind ACT, dereference object, owner activation, NAR, witness, and MRP | It is a canary contract, not the Stage04 source of truth |
| Stage06 body-ref parity | Stage06 refs mirror Stage04 refs | Matching identifiers can still point to missing bodies |
| State-capsule append-only `completed_acts` | operation metadata does not disappear across calls | Current v1 does not bind operation-body bytes |
| Manual render low-mass licensing | a genuinely compact body can be accepted when diagnostic state warrants it | Do not turn its local heuristics into universal length floors |

## Architectural Requirement

The governing chain is:

```text
𝓝 ⊢ D₀
  -> ⇝ Ψᴺ⟨N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩
  -> IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)
  -> ∇_route
  -> ⁿB
  -> {ⁿBᵢ[OPᵢ]}
  -> Land(ⁿB)
  -> ΔⁿB{♥,ξ,Ω,σ,μ}/Δκ
  -> ∇·T/∇×T
  -> LoopBreak(∇×T)
  -> R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)
  -> 𝒞(Ψᴺ)
  -> N_fiṭrī ∧ ʿaql ṣarīḥ
  -> T_lang: Ψᴺ ⇢ Ψᴵ
```

This plan owns the transition from `{ⁿBᵢ[OPᵢ]}` to `Land(ⁿB)` and the local delta that licenses the next reread.

The public chain above is an aggregate projection: the complete operation set is reduced into `Land(ⁿB)`, after which the burden-level `ΔⁿB/Δκ` is derived and diagnosed. Inside each operation capsule, the causal micro-order is more precise: `before_state -> performed OPᵢ -> local_deltaᵢ -> contribution_to_Land`. `Land(ⁿB)` reduces the validated contributions; the post-Land `ΔⁿB/Δκ` is the aggregate burden delta and must reconcile with, but is not identical to, any one local delta. This distinction prevents both impossible “Land before any change” semantics and a competing public pipeline order.

It depends on:

- Plan 02 for source-anchored `pressure_id` values;
- Plan 03 for valid split/merge decisions;
- Plan 04 for one execution obligation per distinct owner/register transition;
- Plan 07 for generated, held, and pre-empted burden lifecycle;
- Plan 09 for witness naming and public tail order;
- Plan 10 for cross-stage projection parity;
- Plan 11 for captured-output promotion and checker-profile custody;
- Plan 13 for prohibiting harness-only semantic repair.

An operation capsule is not a new argument bank. Its owner and operation come from the selected source-owned TTP contract; its pressure, before-state, performed application, after-state, and residual are generated from the runtime case state.

## Five Whys

1. Why can a syntactically present submove be too thin?  
   Because Stage04 accepts a canonical ACT row and `body_ref` without requiring a body object for the reference to resolve to.

2. Why is the dereferenced body absent at Stage04?  
   Because the Stage04 record was designed as compact ACT handoff metadata, while full operation prose was assigned to Stage07 output generation.

3. Why did downstream checking not close the stage boundary?  
   The final render checker can reject thin public bodies, but there is no shared canonical object that proves the body came from Stage04 execution rather than being newly generated or repaired at Stage07.

4. Why are existing body controls fragmented?  
   ACT syntax, owner vocabulary, TTP availability canaries, runner normalization, public-body heuristics, state capsules, NAR, and witness parity evolved as separate safeguards. They agree on identifiers but do not share one operation-body source of truth.

5. Why was no shared operation-body owner established?  
   Stage-contract and promotion hardening optimized identifier parity and final-render plausibility as separate surfaces; neither required Stage04 to emit the canonical performed-operation evidence object later renderers and witnesses must project.

Severity: the operation micro-order requires `OPᵢ` to produce `local_deltaᵢ` and a licensed contribution before `Land(B)` can reduce the operation set; the public aggregate delta is then derived after Land. Without the shared object, every later aggregate delta, reread, and closure witness can be internally consistent over an operation that never occurred.

Root owner/source: the Stage04 execution contract and its cross-stage projection, principally `tools/check_staged_runtime_handshake.py`, `tools/run_staged_current_skill_smoke.py`, the operation-body logic currently embedded in `tools/check_manual_smoke_render_contract.py` and `tools/check_ttp_availability_canaries.py`, and the Stage07 assembler/projection path.

## Hansei

### What worked

- The runtime law already says the ACT row is only a pointer.
- Final-output body checks already detect many generic, conclusion-shaped, owner-code-only, and missing-Land bodies.
- Owner operation and delta vocabularies make typed joins possible.
- Stage04, Stage06, state-capsule, NAR, and witness surfaces already share a stable `body_ref` key.
- Existing valid/invalid fixtures give a strong regression base.

### What failed

- The stage named execution records a declaration of execution, not its canonical evidence.
- The standalone handshake checker is weaker than the runner producer contract.
- Runner hydration can fill missing typed metadata from an ACT row, which is acceptable for syntax migration but cannot establish performed operation evidence.
- Stage07 can create or normalize the operation/result/contribution prose after Stage04 passed.
- The useful `body_ref_dereference` shape lives in a canary family instead of governing the real Stage04 handoff.
- A final-output checker failure arrives too late to identify whether the producer, stage handoff, renderer, or witness projection lost the body.

### Learning

Execution evidence must be born at the execution stage. Later stages may render and mirror it, but they may not manufacture the missing state transition. Structural tooling can prove joins and non-omission; a human reviewer still decides whether the owner mechanism genuinely addressed the pressure.

## Target Contract: `operation-capsule-v1`

### Stage04 record shape

Every release-bearing Stage04 record gains:

```json
{
  "execution_contract": "operation-capsule-v1",
  "operation_capsules": [
    {
      "body_ref": "B1_1",
      "burden_id": "B1",
      "obligation_ids": ["O-B1-source-status-repair-1"],
      "pressure_ids": ["P1"],
      "owner_id": "source-status-repair",
      "operation": "source-order-repair",
      "register_axis": "sigma",
      "before_state": {
        "claim_state": "the compared source is functioning as an unexamined final authority",
        "source_pressure_ids": ["P1"]
      },
      "performed_operation": {
        "mechanism": "separate source status, source function, and the conclusion licensed by that source",
        "application": "apply that separation to the source-comparison pressure carried by P1"
      },
      "after_state": {
        "claim_state": "the source comparison is bounded by an explicit authority and function distinction"
      },
      "delta": {
        "carrier": "Delta(B1)",
        "result": "source-order-repaired"
      },
      "residual": {
        "status": "none",
        "pressure_ids": [],
        "basis": "no unworked source-order residue remains in this operation"
      },
      "land_contribution": {
        "decision": "contributes",
        "basis": "the before-state no longer governs unchanged; Stage05 must still decide the burden terminal state"
      },
      "source_contract_refs": [
        "references/diagnostics/recursive-state-transitions.md",
        "references/rubrics/output-release.md"
      ]
    }
  ],
  "operation_capsule_hashes": {
    "B1_1": "sha256:64-lowercase-hex-computed-by-the-harness"
  }
}
```

The example demonstrates shape only. It is not a required answer, owner, burden count, or Torah/Qur'an route.

### Required capsule joins

For every executed Stage04 `body_ref`:

- exactly one operation capsule exists;
- the capsule `body_ref` equals the ACT row `body_ref` and `act_body_refs` entry;
- `burden_id` equals the ACT row Land target and the owning Stage04 burden;
- every `obligation_id` exists in the Plan 04 obligation ledger;
- every `pressure_id` exists in the Plan 02 pressure inventory or in a valid Stage05 generated-pressure record for generated burdens;
- owner and operation equal the Stage03 selected owner route and ACT bracket;
- register axis and delta result satisfy existing owner vocabularies;
- before-state is anchored to pressure IDs and cannot be an empty label;
- performed operation names a source-owned mechanism and its case application;
- after-state differs from before-state after canonical whitespace normalization;
- delta result is recoverable from the before/after transition;
- residual status is `none`, `live`, or `held`; live/held residuals name pressure IDs and prevent unqualified completion downstream;
- Land contribution explains contribution only; it does not self-attest the final Stage05 terminal state;
- the harness computes the canonical JSON hash after validation; model-supplied hashes are ignored and rejected if presented as authoritative.

### Structural versus semantic boundary

The machine validator may prove:

- required fields exist;
- identifiers and controlled vocabularies join;
- before and after are not byte-identical;
- pressure IDs, obligation IDs, owners, deltas, residuals, and Land references are not orphaned;
- Stage07 and Stage06 project the same capsule.

The machine validator may not prove:

- the before-state is a fair interpretation;
- the selected owner is the best owner;
- the mechanism is correctly applied;
- the after-state follows in truth;
- the burden has been semantically discharged;
- the interlocutor accepts or benefits from the response.

Those remain topology and semantic review questions. A reviewer can fail capsule `B3_2` by naming the exact pressure or inferential gap without prescribing a word count.

### Stage07 projection rule

ACT/body sections become deterministic projections of validated Stage04 capsules:

```text
ACT row copied from Stage04
Submove heading from body_ref + owner
Target from pressure IDs and before_state
Operation from owner.operation + performed_operation
Result/state-change from after_state + delta.result
Contribution-to-Land from land_contribution
TTP Operation Body from before_state -> performed_operation -> after_state -> residual
```

The renderer may perform Unicode/public-label conversion and sentence-safe escaping. It may not add owner mechanisms, state changes, or Land licenses that are absent from the capsule. Connective prose can be model-authored, but proof-bearing operation content is projected.

### Compatibility and migration

- Legacy retained artifacts remain classified under their historical contract. They are never rewritten to contain capsules they did not produce.
- Stage-local v1 syntax fixtures may remain in a `legacy-valid` directory during the first implementation phase.
- New release-bearing records, all five fresh smokes, and all newly promoted retained cases must use `operation-capsule-v1`.
- `act_row_details` remains a compatibility projection generated from validated capsules. It is not independently model-authored after migration.
- State-capsule v1 remains readable for historical replay. A v2 state-capsule schema carries `operation_capsule_sha256` in each `completed_acts` row; release-bearing new runs require v2 after the migration gate.
- No compatibility adapter may synthesize `before_state`, `performed_operation`, `after_state`, residual, or Land basis from an ACT row.

## Stage01-Stage08 Integration Map

| Stage | Current owner | Required change | Pass evidence | Failure effect |
| --- | --- | --- | --- | --- |
| Stage01 intake | runner intake and input digest | no body decision; preserve input hash used by pressure anchors | input hash remains stable | custody failure invalidates all capsules |
| Stage02 Diagnostic IR | Plan 02 pressure inventory | expose stable `pressure_id` values consumed by capsules | every capsule pressure resolves | unresolved pressure reference fails Stage04 |
| Stage03 routing/owner gate | owner routes and Plan 04 obligation ledger | assign stable `obligation_id`, owner, operation, and ordering disposition | every capsule resolves to an executable obligation | unsupported or omitted obligation fails Stage04 |
| Stage04 burden execution | runner producer, handshake checker | require full operation capsules; compute hashes; make metadata a projection | one capsule per executed body ref; no pointer-only pass | earliest stage `04`, class `act_body_evidence` |
| Stage05 MRP/reread | Stage05 terminal/reread checker | consume capsule deltas/residuals; forbid `landed` when required capsule is missing or says live residual | terminal and MRP decisions cite capsule hashes | downstream Stage05 invalidated by Stage04 failure |
| Stage06 witness/NAR | witness and NAR checker | mirror capsule hash, owner, operation, pressure, delta, Land contribution, and residual status | exact set and hash parity with Stage04 | witness cannot repair or replace missing capsule |
| Stage07 release | assembler, runner release prompt, manual render checker | deterministically project ACT bodies; compare parsed public blocks to capsules; remove semantic facet repair | public body and capsule reconstruct each other | projection mismatch fails without rewriting output |
| Stage08 verifier | staged handoff and captured-output verifier | include capsule parity verdict and evidence hashes in sidecars | structural replay can trace every ACT body to Stage04 | PASS remains structural only |

## Exact Owner and Edit Map

### Canonical runtime source to modify

- `atomics/skill/SKILL.md`: keep a compact hot invariant that Stage04 execution requires a capsule and ACT is only its pointer.
- `atomics/skill/references/diagnostics/recursive-state-transitions.md`: define the operation micro-order `ⁿBᵢ[OPᵢ] -> local_deltaᵢ -> Land contribution`, while preserving the public aggregate order `{OPᵢ} -> Land(ⁿB) -> ΔⁿB/Δκ`.
- `atomics/skill/references/diagnostics/diagnostic-ir.md`: connect operation capsule pressure IDs to the Plan 02 input-pressure contract.
- `atomics/skill/references/rubrics/output-release.md`: make Stage07 a projection of the capsule and preserve the existing owner-specific/low-mass boundary.
- `atomics/skill/references/rubrics/manual-contract-digest.md`: add the compact load-path rule and cold-law pointer; do not inline the schema.
- `atomics/skill/references/rubrics/non-droppable-manual-contract.md`: define the full capsule/dereference contract and prohibit post-Stage04 repair.

### Schemas to add or version

- Add `schema/operation-capsule.schema.json` for `operation-capsule-v1`.
- Preserve the current `schema/state-capsule.schema.json` and its v1 meaning in place for legacy replay.
- Contribute `operation_capsule_sha256` and operation-capsule join fields to the single shared `schema/state-capsule-v2.schema.json` migration owned by Plan A16 and composed from A03-A05, A07, A10, and A12 field requirements. Do not mint a second v2 shape or silently repoint the v1 filename.

### Shared checker/library to add

- Add `tools/operation_capsule_contract.py` as the single structural parser, canonicalizer, hasher, and join validator.
- The library exposes pure functions for schema validation, canonical JSON hashing, ACT/capsule parity, pressure/obligation joins, residual-state rules, and public-projection comparison.
- The library does not contain topic terms, expected conclusions, minimum words, minimum sentences, or minimum operation counts.

### Existing tools to modify

- `tools/check_staged_runtime_handshake.py`: require capsules for `execution_contract=operation-capsule-v1`; add right-reason failure class `act_body_evidence`; preserve legacy fixture handling explicitly.
- `tools/run_staged_current_skill_smoke.py`: request capsules in Stage04; validate before accepting Stage04; compute hashes; stop hydrating proof-bearing fields; pass only assigned capsules into each Stage07 ACT section.
- `tools/build_staged_governed_output.py`: render ACT/body sections from capsules and include capsule hashes in the assembly manifest.
- `tools/check_manual_smoke_render_contract.py`: parse public body blocks into a projection and delegate structural joins to the shared library; retain owner-specific semantic heuristics and anti-uptake checks.
- `tools/check_ttp_availability_canaries.py`: replace its private dereference-shape validation with the shared library while retaining catalogue-selection canary semantics.
- `tools/check_state_capsule.py`: support legacy v1 replay and require v2 capsule hashes for new release-bearing runs.
- `tools/check_field_witness_convergence.py`: compare witness owner activations to capsule hashes and projections, not only ACT refs.
- `tools/check_nla_decode_semantic_faithfulness.py`: require operation-capsule reconstruction in the decoded IR path.
- `tools/verify_candidate_output.py`: consume the Stage08 capsule-parity verdict when a custody manifest supplies stage records; do not fabricate it from output text alone.
- `tools/gen_fixture_mutations.py`: add capsule mutations only after expected earliest-stage/right-reason assertions are enforced.
- `tools/ci_registry.json`: register the new checker as required and keep live model execution excluded.

### Fixtures to add

- `tests/operation-capsule/valid/single-compact-executed.json`
- `tests/operation-capsule/valid/multi-owner-one-burden.json`
- `tests/operation-capsule/valid/same-owner-distinct-operations.json`
- `tests/operation-capsule/valid/unicode-public-ascii-join-key.json`
- `tests/operation-capsule/valid/live-residual-forces-recurse.json`
- `tests/operation-capsule/valid/generated-burden-pressure-provenance.json`
- `tests/operation-capsule/invalid/pointer-only-act-row.json`
- `tests/operation-capsule/invalid/typed-metadata-without-operation.json`
- `tests/operation-capsule/invalid/before-after-identical.json`
- `tests/operation-capsule/invalid/unresolved-pressure-id.json`
- `tests/operation-capsule/invalid/unresolved-obligation-id.json`
- `tests/operation-capsule/invalid/owner-operation-route-mismatch.json`
- `tests/operation-capsule/invalid/code-lookup-not-execution.json`
- `tests/operation-capsule/invalid/conclusion-shaped-application.json`
- `tests/operation-capsule/invalid/delta-not-recoverable.json`
- `tests/operation-capsule/invalid/generic-land-license.json`
- `tests/operation-capsule/invalid/live-residual-with-complete.json`
- `tests/operation-capsule/invalid/model-supplied-false-hash.json`
- `tests/operation-capsule/invalid/public-projection-mismatch.json`
- `tests/operation-capsule/invalid/witness-capsule-hash-mismatch.json`

### Workbench fixtures to migrate

- Move the current pointer-only Stage04 fixture to `tests/stage-contract-workbench/stage-04-burden-execution-act/invalid/operation-capsule-missing.json` once the new contract is active.
- Replace `minimal-valid/single-act-row.json` with `minimal-valid/single-operation-capsule.json`.
- Replace the current maximal fixture with `maximal-valid/multi-operation-capsules.json`.
- Add `<fixture-stem>.expectation.json` sidecars under Plan A11's canonical schema for every new invalid Stage04 fixture, with `expected_earliest_stage: "04"`, exact class/subcode/downstream set, and forbidden downstream artifacts.
- Extend Stage05, Stage06, Stage07, and Stage08 maximal fixtures with capsule hashes and parity evidence.

### Documentation to add or modify

- Add `docs/operation-capsule-and-land-license.md` as the maintainer contract and migration guide.
- Update `docs/stage-contract-workbench.md` with the Stage04 evidence boundary and failure class.
- Update `docs/recursive-state-capsule.md` for v1 legacy/v2 release-bearing behavior.
- Update `docs/execution-spine.md` to show Stage04 as the operation evidence owner.
- Update `docs/non-claims.md` so capsule PASS is never described as semantic truth.
- Update `docs/four-smoke-release-playbook.md` to five-smoke terminology only in coordination with Plan 13.

### Generated files not to hand-edit

- Never hand-edit `skill/SKILL.md` or any generated `skill/**` file.
- Rebuild the compiled runtime from atomics.
- Never rewrite retained historical outputs or sidecars to add capsules after the fact.

## Required Fixture Semantics

### Valid cases

1. A genuinely small operation has one capsule because one pressure, owner mechanism, state change, and residual account are sufficient. It passes without a length waiver.
2. Two distinct owner obligations in one burden produce two capsules and two body refs.
3. One owner performs two materially distinct operations only when Plan 04 produced two obligations; the capsules remain distinct and ordered.
4. A live residual is recorded and Stage05 routes RECURSE rather than COMPLETE.
5. An owner-body-not-loaded route is held without an ACT row or fabricated capsule.
6. A generated pressure uses Stage05 provenance and a later Stage04 execution pass before it can land.
7. Public Unicode notation and machine ASCII join keys canonicalize to one capsule identity.
8. A concise body passes when its structured transition is reconstructible and semantic review accepts it; no word floor is consulted.

### Invalid cases

1. ACT row plus `body_ref`, no capsule.
2. `act_row_details` metadata, no performed operation.
3. Capsule owner or operation differs from Stage03/ACT.
4. Capsule points to a missing source pressure or owner obligation.
5. Before and after states are identical or differ only in punctuation.
6. Application merely says the owner applies, quotes the catalogue, or repeats the desired conclusion.
7. Delta result is not represented in the after-state or conflicts with the ACT row.
8. Residual is live or held but Stage05 marks the burden landed and closes.
9. Land contribution says only “this licenses Land” without naming the changed state.
10. Public body omits, changes, or adds proof-bearing content relative to the capsule.
11. Witness/NAR mirrors the ACT row but not the capsule hash.
12. Harness normalization inserts a missing mechanism, state change, or Land basis.
13. A model-authored boolean such as `operation_complete=true` attempts to replace evidence.

## Test-Driven Implementation Sequence

### Phase 0: Freeze the false-pass and baseline controls

Run from the PR9 checkout:

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
git status --short --branch --untracked-files=all
git rev-parse HEAD
Get-FileHash -Algorithm SHA256 -LiteralPath tests\stage-contract-workbench\stage-04-burden-execution-act\minimal-valid\single-act-row.json
Get-FileHash -Algorithm SHA256 -LiteralPath tests\stage-contract-workbench\stage-04-burden-execution-act\maximal-valid\multi-act-row-details.json
python tools\check_staged_runtime_handshake.py --explain-stage-failure --records tests\stage-contract-workbench\stage-04-burden-execution-act\minimal-valid\single-act-row.json
python tools\check_staged_runtime_handshake.py --explain-stage-failure --records tests\stage-contract-workbench\stage-04-burden-execution-act\maximal-valid\multi-act-row-details.json
python tools\check_manual_smoke_render_contract.py
python tools\check_ttp_availability_canaries.py
```

Expected baseline:

- clean branch at `6987c9eb...`;
- fixture hashes match this plan;
- each Stage04 explain command exits `0` with `{"status":"pass"}`;
- manual render suite exits `0` with 18 valid/40 invalid;
- TTP availability suite exits `0` with 10 valid/19 invalid.

STOP if the head or fixture hashes drift. Rebase the plan before patching.

### Phase 1: Add the shared operation-capsule contract red tests

Add the schema, pure library skeleton, and valid/invalid fixtures before integration. The first test run must fail because validation is not implemented.

Planned command:

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
python tools\operation_capsule_contract.py --self-test
```

Expected red state: exit `1`, with named failures for pointer-only, missing operation application, invalid joins, generic Land license, residual/closure conflict, and public projection mismatch. An import error or missing-file error is not the intended red state.

Implement the pure contract until the same command exits `0`. The self-test must prove both valid acceptance and invalid right-reason rejection.

### Phase 2: Make Stage04 own execution evidence

Integrate the shared validator into the handshake checker and runner. Do not add a second validator inside the runner.

Post-integration suite:

```powershell
python tools\check_staged_runtime_handshake.py
python tools\run_staged_current_skill_smoke.py --self-test
```

Expected: both exit `0`; all migrated valid fixtures pass; all invalid fixtures fail with pinned expected diagnostics.

Right-reason negative smoke:

```powershell
$p = 'tests\stage-contract-workbench\stage-04-burden-execution-act\invalid\operation-capsule-missing.json'
$raw = & python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $p
$exitCode = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($exitCode -ne 1) { throw "expected exit 1, got $exitCode" }
if ($diag.earliest_stage -ne '04') { throw "expected earliest_stage 04, got $($diag.earliest_stage)" }
if ($diag.failure_class -ne 'act_body_evidence') { throw "expected act_body_evidence, got $($diag.failure_class)" }
if ($diag.requires_model_rerun -ne $false) { throw 'static Stage04 fixture must not require model rerun' }
```

Expected: PowerShell exits `0` because the checker exits `1` for the intended Stage04 class and the assertions pass.

Canonical acceptance command:

```powershell
python tools\assert_expected_rejection.py --expectation tests\stage-contract-workbench\stage-04-burden-execution-act\invalid\operation-capsule-missing.expectation.json --artifact-root auto
```

Expected: exit `0`; Stage04 is the earliest failure, Stages05-08 are invalidated, and no downstream or promotion artifact exists.

### Phase 3: Replace Stage07 body invention with projection

Write projection tests first. The valid fixture must render one public block per capsule. Invalid fixtures must detect altered owner, operation, before/after state, delta, Land contribution, missing capsule, and extra unbound ACT body.

Commands:

```powershell
python tools\build_staged_governed_output.py --self-test
python tools\check_manual_smoke_render_contract.py
python tools\check_nla_decode_semantic_faithfulness.py
```

Expected: all commands exit `0`. The manual checker still accepts its existing valid corpus and rejects its existing invalid corpus.

Remove or narrow `canonicalize_layer_b_owner_transition_facets` so it cannot add proof-bearing mechanism, result, or Land-license content. A permitted normalizer may repair typography or public notation only and must record every change. A proof-bearing mismatch must fail and preserve the raw artifact.

### Phase 4: Bind Stage06, state capsule, and Stage08

Implement capsule hashes and legacy/current schema dispatch.

Commands:

```powershell
python tools\check_state_capsule.py --self-test
python tools\check_field_witness_convergence.py
python tools\check_ttp_availability_canaries.py
python tools\check_staged_runtime_handshake.py
```

Expected: all commands exit `0`; legacy v1 fixtures remain explicitly legacy; new release-bearing v2 fixtures require capsule hashes; witness/NAR parity fails on any altered capsule hash or projection.

### Phase 5: Rebuild canonical runtime

Edit atomics, then regenerate:

```powershell
python tools\build_compiled_runtime.py
python tools\check_compiled_runtime_freshness.py
python tools\check_package_shape.py
python tools\check_prompt_pack_budget.py --self-test
```

Expected: all exit `0`; `skill/SKILL.md` changes only through the builder; hot-context budgets remain within the branch's ratchets; no full schema is re-inlined into the hot root.

### Phase 6: Full deterministic Stage01-Stage08 preflight

```powershell
python tools\run_no_model_preflight.py --self-test
python tools\run_no_model_preflight.py
```

Expected: all composed gates exit `0`. This proves deterministic contract migration only. It does not prove any model will produce an adequate capsule.

### Phase 7: Authorized five-smoke execution

No model command is authorized by this plan. After Plan A14 registers the fifth case and the owner authorizes the matrix, each smoke must produce Stage04 operation capsules and pass through Stage08. Preserve first failure; do not let Stage07 or the harness repair a failed capsule.

## Five-Smoke Implications

The required cases are:

- `gate88-secularism`
- `gate88-khaybar`
- `gate88-trinitarian-j173`
- `gate88-tst-lillard`
- `gate88-torah-quran-source-authentication`

For each case:

- every Stage04 ACT body ref resolves to one operation capsule;
- every capsule resolves to runtime-selected pressure and obligation IDs;
- public body, Stage06 witness/NAR, state capsule, and Stage08 sidecar agree with the Stage04 capsule;
- any capsule with live residual pressure prevents unqualified COMPLETE;
- semantic/topology review challenges capsules by ID and evidence, not by output length;
- a structural PASS does not certify the theological conclusion, source provenance, persuasion, or uptake.

The fifth smoke stores no expected owner, operation, body, burden count, submove count, citation list, answer outline, or conclusion. Its only fixed data is the exact user input and custody metadata. The operation capsule must be selected and populated from its runtime pressure topology.

## Adversarial Review Protocol

Before promotion, review at least these attacks:

1. Pointer theater: keep ACT and witness rows but delete the capsule.
2. Metadata theater: populate owner/operation/delta fields but make performed operation a conclusion label.
3. Catalogue theater: paste the owner definition without applying it to the pressure.
4. Delta theater: claim a controlled delta result while before and after states are equivalent.
5. Land theater: say “licenses Land” without naming what changed.
6. Residual laundering: mark residual `none` while Stage02/Stage05 still carries the pressure.
7. Projection drift: alter Stage07 prose while preserving the same body ref.
8. Witness laundering: mirror the ACT row while omitting or changing the capsule hash.
9. Repair laundering: allow harness normalization to insert the missing operation.
10. Padding: make the operation long but generic; it must still fail owner/pressure review.
11. Over-compression: make the operation short but complete; it must not fail solely for being short.
12. Topic banking: add a Torah, secularism, Khaybar, TST, or J173 expected operation to schema/checker code; this is an immediate STOP.

## Rollback

- Revert schema, shared library, checker integrations, fixtures, runtime atomics, and generated runtime as one coherent patch.
- Do not leave `execution_contract=operation-capsule-v1` in producer prompts if the checker is rolled back.
- Do not leave the checker requiring capsules if Stage07 cannot project them.
- Preserve invalid and adversarial fixtures even if the implementation is abandoned; move them to a documented historical-gap directory rather than deleting the evidence.
- Never rewrite captured outputs or retained historical cases.
- If the v2 state-capsule migration must be rolled back, keep v1 replay available and block new release-bearing runs. Do not silently drop capsule hashes while claiming current-contract PASS.
- A rollback returns the repository to a known pointer-only gap. The ANDON status becomes `BLOCKED`, not closed.

## STOP / ANDON Conditions

Stop implementation if any of the following occurs:

- a minimum word, sentence, paragraph, byte, burden, or submove count becomes the capsule pass rule;
- the schema contains topic-specific expected owners, arguments, sources, or conclusions;
- Stage04 accepts a body ref without a capsule on a release-bearing path;
- Stage07 creates proof-bearing operation content absent from Stage04;
- a normalizer repairs missing mechanism, state change, residual, or Land basis;
- generated and baseline pressure IDs are conflated;
- a live residual coexists with unqualified COMPLETE;
- state-capsule/witness parity is checked only by body-ref presence and not capsule hash;
- existing owner/delta registries are reimplemented inconsistently;
- a structural PASS is reported as semantic truth, provenance, uptake, or release readiness;
- raw failed model output is overwritten during repair;
- branch head or baseline fixture hashes drift without plan review.

Concrete STOP record for the present false-pass:

```yaml
status: UNVERIFIED
class: act_body_evidence
abnormality: Stage04 accepts an ACT pointer without a dereferenceable operation capsule
failing_check: python tools\check_staged_runtime_handshake.py --explain-stage-failure --records tests\stage-contract-workbench\stage-04-burden-execution-act\minimal-valid\single-act-row.json
observed_exit: 0
observed_diagnostic: '{"status":"pass"}'
owner_source: tools/check_staged_runtime_handshake.py::stage04_act_errors
evidence_sha256: 8CB0C1A0D15C0B76FBD79B41703E410573AAE6E9E713BB6871A597D042D0AB29
downstream_invalidated: ['05', '06', '07', '08']
next_action: add operation-capsule-v1 red fixtures and shared validator before changing producer behavior
regression_status: unproven
```

## Definition of Done

- A release-bearing Stage04 record cannot pass with only ACT rows, body refs, or typed metadata.
- Every executed owner obligation has exactly one canonical operation capsule.
- Every capsule joins to source pressure, routed obligation, owner operation, register axis, local delta, residual, and Land contribution.
- Stage07 operation bodies are deterministic projections of Stage04 capsules.
- Stage07 does not silently repair semantic facets.
- Stage05 terminal decisions and Stage06 witness/NAR rows are hash-bound to capsules.
- State-capsule v2 preserves operation-capsule hashes; legacy v1 remains honestly classified.
- Existing ACT syntax, owner vocabulary, manual render, TTP availability, witness, and NLA controls remain green.
- Right-reason invalid fixtures fail at earliest stage `04` with `act_body_evidence`.
- No fixed size or count floor is introduced.
- All five fresh smokes traverse Stage01-Stage08 with capsule parity and independent semantic/topology review.
- Structural PASS remains explicitly non-semantic.
- `regression_status` remains `unproven` until Plan 01's admissible comparison gate runs.

## Confidence

Current false-pass diagnosis: YES, confirmed by direct fixture replay.  
Repository owner map: YES, implementation-grade at the planned head.  
Structural operation-capsule countermeasure: YES, implementation-ready after Plans 02/04 IDs are fixed.  
Automated semantic sufficiency: NO, deliberately outside the machine claim.  
Five-smoke behavioral closure: UNPROVEN until authorized fresh runs exist.
