# ANDON A08: Opening State, Monotonic Closure, and Recursion-State Integrity

**Plan class:** P0/P1 patch-execution-grade engineering plan  
**Scope:** opening formation, recursive state transitions, residual curl/LoopBreak, Restorative Response, Closing Formulation, Closure/Reconstruction Witness, final `field_witness`, and Stage07/08 release truth  
**Implementation target:** `C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`  
**Observed PR9 head:** `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
**Planning status:** implementation sequence specified; no implementation performed by this plan  
**Regression status:** `unproven` until same-fixture v0.4.5.0/v0.4.6.0 captured outputs exist  

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## 1. Plain-language result

The current PR9 contract permits the opening banner to say `COMPLETE`. That means the first public state declaration may announce the result that the remainder of the artifact is supposed to establish. The banner checker then asks mainly whether the final tail is compatible with that opening state; it does not prove that completion arose monotonically from the executed noetic trace.

This is not only awkward phrasing. It reverses the dependency:

```text
unsafe: opening COMPLETE → body rendered to match → final witness repeats COMPLETE
safe:   opening OPEN → execute/reread/recurse → derive closure → final witness may say COMPLETE
```

The same issue appears in downstream code. Different tools use different approximations for `coverage_complete`; the runner can hard-code a Stage07 `closure_claim: complete`; one state-capsule path ORs an asserted closure claim into derived coverage; missing terminal states can be defaulted to landed; and some graph properties are emitted as literal `true`. Stronger controls already exist elsewhere, especially in `check_state_capsule.py` and `check_graph_completeness.py`, but they are not yet one canonical closure predicate used by every producer and checker.

The repair is a versioned, monotonic state machine and one pure closure-state library. The opening may state only that the trace is open or resumed. `COMPLETE` becomes a terminal derived postcondition, available only after:

1. every input pressure and burden is accounted for;
2. every selected owner obligation has execution evidence;
3. every Land has an MRP reread;
4. generated, held, and pre-empted states are terminally accounted for;
5. residual divergence/curl is neutral, null, or validly resolved;
6. any LoopBreak has a diagnosed ground and a post-break reread;
7. Restorative Response is rendered;
8. Closing Formulation reports the derived disposition;
9. the final Closure/Reconstruction Witness reconstructs the trace and independently satisfies the same predicate.

## 2. Scope and prohibitions

This is planning only. It does not authorize source changes, model smokes, commits, pushes, packaging, issue filing, release work, or publication.

The implementation must not:

- solve closure with a byte, word, token, burden, or submove floor;
- encode a Torah/Qur'an answer or any other smoke-specific argument;
- treat a structural PASS as semantic truth, provenance truth, persuasion, conversion, or uptake;
- convert HOLD/PARTIAL/RECURSE into failure merely because they are not COMPLETE;
- allow a complete-looking banner or prose sentence to override derived state;
- infer closure from terminal-field presence alone;
- hard-code graph completeness or acyclicity;
- erase historical fixtures that truthfully represent a legacy contract;
- change `regression_status: unproven` without same-fixture captured evidence.

## 3. ANDON statement and current false-pass

### 3.1 Abnormality

The release contract allows a completion claim at the beginning of the public artifact and lacks a single monotonic, derived closure predicate shared by the runner, handshake checker, field witness, graph checker, state capsule, and collapse certificate.

### 3.2 Current false-pass proposition

The unsafe proposition is:

> “If the opening banner says `COMPLETE`, the final tail is compatible, and locally required fields are present, closure has been structurally established.”

That proposition is not guaranteed by current PR9 because:

- `COMPLETE` is a legal opening enum value;
- the opening checker validates compatibility more strongly than derivation order;
- some local completeness functions check state presence rather than closed-state truth;
- the runner manufactures a complete claim before all independent closure checks have run;
- downstream state derivation can consume that claim;
- output projection can default or hard-code supporting fields.

### 3.3 Why this is a major ANDON

`𝒞(Ψᴺ)` is the collapse/closure point of the architecture. If it can be asserted prospectively or assembled from weaker local predicates, then all earlier topology work can be bypassed at the final promotion boundary. A system may correctly detect a held burden, generated recoil, residual curl, or missing owner activation and still render a completion-shaped artifact.

The problem therefore affects:

- whether recursion continues;
- whether held burdens remain visible;
- whether LoopBreak is actually followed by reread;
- whether residual curl blocks closure;
- whether a partial run can resume;
- whether the final witness reconstructs body/provenance;
- whether Stage08 promotes an artifact for the right reason.

## 4. Evidence status

### 4.1 Confirmed by direct PR9 GEMBA

| ID | Confirmed fact | Direct owner/evidence |
|---|---|---|
| C08-01 | Canonical render source permits opening `state: RECURSE | PARTIAL | COMPLETE`. | `atomics/skill/references/rubrics/diagnostic-render-contract.md`, opening banner contract near lines 48-56. |
| C08-02 | The compact manual digest explicitly permits opening COMPLETE when the run is expected to discharge in one pass. | `atomics/skill/references/rubrics/manual-contract-digest.md`, near lines 217-221. |
| C08-03 | The banner checker accepts `COMPLETE` in `STATE_VALUES`. | `tools/check_noetic_field_banner_samples.py`, state enum near lines 12-28. |
| C08-04 | The banner checker checks final-tail compatibility but does not establish monotonic transition provenance. | `tools/check_noetic_field_banner_samples.py`, `_closure_errors` near lines 116-144. |
| C08-05 | The inspected Grok v0.4.6.0-WIP artifact begins with `state: COMPLETE` before the burden bodies and final witness. | Captured artifact registered in the established Sol evidence ledger. This proves observed behavior, not comparative regression. |
| C08-06 | `ClosureWitness.coverage_complete` checks that initial burdens have terminal-state entries, not that every B_total state is closed. | `tools/closure_witness_lib.py`, `coverage_complete` near lines 102-108; `collapse_positive` near lines 121-122. |
| C08-07 | `check_graph_completeness.py` has a local coverage expression based on initial burdens being present in terminal states, while stronger open-state checks exist elsewhere in the same checker. | `tools/check_graph_completeness.py`, condition rows near line 1622 and related stop/hold logic. |
| C08-08 | `check_state_capsule.py` already has a stronger rule: coverage requires an empty held set and every B_total burden in a closed state. | `tools/check_state_capsule.py`, coverage-complete checks near lines 664-690. |
| C08-09 | The runner computes state-capsule coverage and then ORs it with a Stage07 complete claim/full-answer condition. | `tools/run_staged_current_skill_smoke.py`, state-capsule projection near lines 1322-1330. |
| C08-10 | The runner emits Stage07 `closure_claim: complete` as a literal in the inspected main path. | `tools/run_staged_current_skill_smoke.py`, Stage07 record construction near lines 19573-19585. |
| C08-11 | Stage07 projection can default a missing terminal state to landed. | `tools/run_staged_current_skill_smoke.py`, field-witness state construction near lines 5059-5063. |
| C08-12 | Stage07 projection emits graph `acyclic: True` and diagnostic completeness `complete: True` as literals. | `tools/run_staged_current_skill_smoke.py`, field-witness projection near lines 5390 and 5395. |
| C08-13 | Stage07 COMPLETE rejection is substantially tied to Stage05 held status/terminal values, not one canonical whole-pipeline predicate. | `tools/check_staged_runtime_handshake.py`, Stage07 closure checks near lines 1197-1204 and cross-stage checks near lines 2169-2173. |
| C08-14 | `check_graph_completeness.py` already has a strong structured no-new proof covering live burdens, field state, residual κ, route checks, and terminal accounting. | `tools/check_graph_completeness.py`, no-new proof checks near lines 997-1118. |
| C08-15 | `check_graph_completeness.py` already guards residual curl and LoopBreak states. | `tools/check_graph_completeness.py`, residual-curl rules near lines 1504-1558. |
| C08-16 | The conceptual pipeline places the closure field condition after post-render checks and has a RECURSE return edge. | `atomics/skill/references/diagnostics/framework-pipeline.yaml`, near lines 409-427. |
| C08-17 | Recursive-state source already says STOP follows reread and distinguishes HOLD/PARTIAL/RECURSE. | `atomics/skill/references/diagnostics/recursive-state-transitions.md`; supporting MRP source/checkers. |

### 4.2 Inferred, not confirmed

| ID | Inference | Boundary |
|---|---|---|
| I08-01 | Prospective COMPLETE likely biases models toward writing a closure-shaped answer rather than allowing later recursion. | Plausible prompt-order effect; requires controlled model artifacts to establish causality. |
| I08-02 | Distributed closure predicates likely increase the chance that a future change creates a false positive despite individual checker coverage. | Architectural risk confirmed by drift, but no exhaustive historical false-positive corpus has been replayed under a unified oracle. |
| I08-03 | Literal Stage07 completion fields may have contributed to observed premature closure. | Code path is confirmed; attribution to a specific captured output needs raw Stage06/07 records. |

### 4.3 Unproven and not claimed

- A v0.4.5.0-to-v0.4.6.0 regression.
- That every current COMPLETE artifact is invalid.
- That changing the opening enum alone will alter model depth.
- That structural closure establishes the truth of any substantive answer.
- That HOLD/PARTIAL/RECURSE is a model failure; these may be the only truthful states.

### 4.4 Planning-time read-only verification

At plan finalization, both source worktrees were clean: PR9 at `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`, and the v0.4.5.0 reference at `8c14e28fbcf440275f4d143a9b7cadc6148aa5a9`. No source file was changed.

The following current PR9 checks exited `0` during this planning pass:

- `python tools\check_staged_runtime_handshake.py`;
- `python tools\check_mid_reread_pressure.py`;
- `python tools\check_mrp_route_invariants.py`;
- `python tools\check_mrp_generated_burden.py`;
- `python tools\check_formal_reread_state_semantics.py`;
- `python tools\check_graph_completeness.py`;
- `python tools\check_field_witness_convergence.py`;
- `python tools\check_state_capsule.py --self-test`;
- `python tools\check_collapse_certificate_schema.py`;
- `python tools\check_manual_smoke_render_contract.py`;
- `python tools\check_noetic_field_banner_samples.py tests\mrp-route-invariants\valid\synthetic-linear-chain.md`;
- `python tools\measure_load_path_budget.py --enforce-ratchet --enforce`;
- `python tools\run_no_model_preflight.py --self-test`.

One bounded reviewer invocation of `python tools\run_no_model_preflight.py` did not complete within 124 seconds; it was in `tools/gen_fixture_mutations.py --self-test` when that invocation timed out. That attempt is non-evidence, not a failed invariant. The primary audit subsequently reran the exact command with a 900-second allowance: it exited `0` after 370.2 seconds and all 16 gates passed. That later pass is the controlling planning baseline. It still does not test the new opening/closure contract proposed here and no model smoke was run.

## 5. Formal-chain location and ordering

The governing chain is:

```text
𝓝 ⊢ D₀
→ ⇝ Ψᴺ⟨N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩
→ IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)
→ ∇_route
→ ⁿB
→ {ⁿBᵢ[OPᵢ]}
→ Land(ⁿB)
→ ΔⁿB{♥,ξ,Ω,σ,μ}/Δκ
→ ∇·T/∇×T
→ LoopBreak(∇×T)
→ R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)
→ 𝒞(Ψᴺ)
→ N_fiṭrī ∧ ʿaql ṣarīḥ
→ T_lang: Ψᴺ ⇢ Ψᴵ
```

The opening `COMPLETE` defect moves `𝒞(Ψᴺ)` to the front as an assertion. The repair restores it as a derived gate after `R(...)` and before final public projection.

The mandatory public render order is:

```text
1. Opening Formation: trace is OPEN; no closure verdict
2. Layer A / diagnostic topology and burden map
3. Layer B / owner-backed ACT, Land, per-burden MRP, and recursive cycles
4. Restorative Response
5. Closing Formulation: human-facing derived disposition and bounded claim
6. Closure / Reconstruction Witness: final structural reconstruction and closure proof
```

The Closure/Reconstruction Witness comes **after** Closing Formulation, and Closing Formulation comes **after** Restorative Response. A final inline parser-stable `field_witness` follows the human witness, unless the predeclared transport uses a hash-bound external sidecar. Neither witness may repair or retroactively invent missing body/provenance.

Effects by topology dimension:

- **recursion:** RECURSE is emitted only after a real Land+reread reveals a live route; it returns to the cycle rather than coexisting with opening COMPLETE;
- **burden number:** closure uses exact `B_total`, including generated burdens from Plan 07, rather than initial-floor presence;
- **burden length:** each closed burden must reconstruct its owner obligations and ACT body references; headings or terminal labels do not suffice;
- **submove number:** all dynamically derived owner obligations must be executed/disposed before closure; no fixed count is assumed;
- **generated/pre-empted burdens:** every instantiated burden and live candidate must be terminally accounted for; an uninstantiated non-load-bearing candidate needs explicit basis;
- **residual curl:** any unresolved curl or missing post-LoopBreak reread blocks `𝒞(Ψᴺ)`;
- **held state:** any non-empty `H` blocks COMPLETE and yields HOLD/PARTIAL/RECURSE custody; non-load-bearing candidates are terminally disposed outside `H`.

## 6. Real 5 Whys

### Problem statement

Why can the public artifact announce COMPLETE before the pipeline has demonstrated closure?

1. **Why is opening COMPLETE accepted?**  
   Because the canonical render contract and banner checker include `COMPLETE` in the legal opening-state enum.

2. **Why was COMPLETE placed in an opening enum?**  
   Because the opening banner was designed partly as a summary of the intended whole artifact, including an estimate that the burden set was dischargeable in one pass.

3. **Why can an intended outcome stand in for a derived state?**  
   Because the contract does not distinguish entry state, continuation disposition, closure candidate, and closure confirmation as separate temporal fields.

4. **Why does downstream verification not fully recover the distinction?**  
   Because closure logic is distributed across the banner checker, runner, handshake checker, closure witness, graph checker, state capsule, and collapse certificate, with different definitions of coverage and some literal/defaulted positive fields.

5. **Why did those definitions diverge?**  
   Because there is no single canonical closure-state owner imported by both producers and validators, and promotion tests emphasized final shape/compatibility rather than monotonic provenance from open entry through recursive execution to confirmed closure.

### Actionable root cause

The actionable root cause is a **missing temporal state contract and canonical closure oracle**. The problem is not merely that the word COMPLETE appears early; it is that the same concept is used as prediction, local summary, producer assertion, and final postcondition without one monotonic derivation owner.

### Contributing causes

1. Local coverage checks use different burden universes (`B_LA` versus `B_total`).
2. Terminal-state presence is sometimes treated like terminal-state closure.
3. An asserted Stage07 claim can feed a derived state calculation.
4. Projection code supplies optimistic defaults for absent evidence.
5. Right-reason fixtures for premature COMPLETE are composite, so an earlier unrelated failure can hide the intended gate.
6. Historical fixtures with legal COMPLETE openings make an unversioned enum change risky, encouraging preservation of the old ambiguity.

## 7. Hansei

1. **We allowed a postcondition to become an opening promise.** A state machine cannot be monotonic if its final state is declared at entry.
2. **We confused compatibility with derivation.** A matching tail does not show that every required transition occurred.
3. **We implemented several partial oracles.** Strong controls exist, but a weak caller can still construct a positive claim before those controls agree.
4. **We trusted producer literals in consumer calculations.** A claim must be checked against evidence, never ORed into the evidence predicate.
5. **We defaulted absence toward success.** Missing state must remain unknown/open and fail closure, not become landed.
6. **We hard-coded graph properties that should be computed.** `acyclic: true` and `complete: true` are conclusions, not scaffold values.
7. **We under-specified render chronology.** Restorative Response, Closing Formulation, Closure/Reconstruction Witness, and final `field_witness` need one canonical order.
8. **We did not require minimal right-reason negatives.** Composite invalid fixtures can pass coverage while failing before the intended closure gate.
9. **We risked treating truthful open states as inferior outputs.** HOLD/PARTIAL/RECURSE protect epistemic custody and must remain valid outcomes.

## 8. Target state contract

### 8.1 Versioned opening formation

Introduce `opening-state-v2` for all new release-bearing artifacts:

```yaml
opening_state_contract: opening-state-v2
phase: ENTRY
state: OPEN
closure_claim: PENDING
trace_id: trace-001
resume_from_capsule: null
```

Rules:

1. `state` is exactly `OPEN` for a new trace.
2. A resumed trace remains `OPEN` and names its prior capsule; inherited HOLD/PARTIAL/RECURSE belongs in `resume_from_capsule`, not as a fresh closure prediction.
3. `closure_claim` is exactly `PENDING` in Opening Formation.
4. `COMPLETE`, `RECURSE`, `HOLD`, and `PARTIAL` are continuation/terminal dispositions derived after execution, not opening verdicts.
5. Historical retained fixtures may declare `opening_state_contract: legacy-v1`; they remain replayable but are not eligible to prove v2 promotion.
6. The public opening may name selected mode/topology, but cannot state that the noetic field has collapsed.

This avoids the misleading alternative of putting `RECURSE` at the opening before any reread has occurred. A multi-burden plan is still simply OPEN until the execution trace derives its next disposition.

### 8.2 Canonical monotonic state machine

Add a checked internal trace state:

```text
INTAKE
→ OPEN
→ ROUTED
→ EXECUTING
→ LOCAL_LANDED
→ REREAD_PENDING
→ REREAD_EVALUATED
→ {RECURSE | LOOPBREAK_PENDING | HOLD | PARTIAL | CLOSURE_CANDIDATE}

LOOPBREAK_PENDING
→ LOOPBREAK_APPLIED
→ POST_BREAK_REREAD_PENDING
→ REREAD_EVALUATED

RECURSE
→ ROUTED

CLOSURE_CANDIDATE
→ CLOSURE_CONFIRMED
```

Only `CLOSURE_CONFIRMED` may project public `COMPLETE`.

Monotonicity rules:

- no transition leaves `CLOSURE_CONFIRMED` within the same trace;
- no transition goes from COMPLETE to RECURSE/HOLD/PARTIAL;
- new information after confirmed closure starts a new trace linked to the prior trace;
- LOCAL_LANDED is per burden and never equals global closure;
- RECURSE requires a completed reread and a live next target;
- HOLD requires an explicit blocking condition and custody owner;
- PARTIAL requires a continuation capsule and exact next action;
- LoopBreak cannot lead directly to closure without a post-break reread;
- resource exhaustion cannot produce CLOSURE_CANDIDATE.

### 8.3 One canonical closure owner

Add `tools/closure_state_lib.py` as a pure structural library. It should expose, at minimum:

```python
is_closed_terminal_state(value)
derive_burden_coverage(trace)
derive_candidate_coverage(trace)
derive_residual_field_state(trace)
derive_closure_decision(trace)
validate_monotonic_transitions(trace)
build_closure_witness_projection(trace)
```

The library must import or extract the strongest existing predicates rather than cloning weaker versions. All of these owners must call it:

- `tools/run_staged_current_skill_smoke.py`;
- `tools/check_staged_runtime_handshake.py`;
- `tools/closure_witness_lib.py`;
- `tools/check_graph_completeness.py`;
- `tools/check_state_capsule.py`;
- `tools/check_collapse_certificate_schema.py`;
- `tools/check_noetic_field_banner_samples.py`;
- `tools/build_staged_governed_output.py`.

Producers may propose a closure decision. Only the canonical derivation determines whether the proposal is structurally licensed.

### 8.4 Closure predicate v2

`derive_closure_decision(trace)` may return COMPLETE only when every condition below is true.

#### Input and topology coverage

- Stage01 input digest matches the governed trace.
- Stage02 pressure inventory has no unaccounted released-and-eligible candidate.
- Every candidate is terminally classified with evidence.
- `B_LA` is exact and immutable.
- `B_MRP` is append-only, disjoint, and provenance-backed.
- `B_total = B_LA ∪ B_MRP` exactly.

#### Execution coverage

- Every `B_total` burden has a terminal state in the canonical closed-state enum.
- No load-bearing burden is held, carried-RECURSE, unknown, or merely declared.
- Every derived owner obligation is executed or explicitly disposed under its owner contract.
- Every claimed ACT/Land has body references reconstructible in the artifact.
- Every generated burden claimed closed has its own route/ACT/Land cycle.

#### Reread and candidate coverage

- Every executed Land has a per-burden MRP/reread record.
- Every MRP candidate has one terminal disposition.
- No deferred pre-empted candidate remains live.
- Structured `no_new_resultant.stop_licensed` is true.
- The no-new proof is recomputed, not trusted from a Boolean.

#### Field convergence

- Diagnostics are target-explicit records, not route-derived scalar summaries: each divergence/curl row carries `operator`, `target`, `status`, `basis_refs`, and `delta_ref`; curl rows also carry dependency/cycle and LoopBreak references when applicable.
- Missing diagnostics remain `unknown/open`; they never default to neutral/null.
- Raw non-neutral divergence and raw non-null curl cannot be rewritten because a producer proposed STOP or `no_new_resultant`.
- For global COMPLETE, `∇·T` is neutral, `∇×T` is null or demonstrably resolved after a post-LoopBreak reread, residual `κ` is zero, and no load-bearing item remains live in `H`.
- Scoped closure may carry proof-bounded residual `κ` only as `{status: proof_bounded, scope, basis_refs, reopen_condition}` and must render a scoped/reopen boundary. Live or unknown residual pressure forces HOLD/PARTIAL/RECURSE.
- If LoopBreak occurred, diagnosed curl, interruption ground, action, and post-break reread all exist.
- Post-break field state, not pre-break intention, licenses closure.

Coverage and collapse are separate predicates:

- `initial_coverage_complete`: every initial `B_LA` burden has an explicit terminal accounting state, including honest HOLD/PARTIAL where applicable;
- `lifecycle_accounting_complete`: every `B_total` burden and every generated/held/pre-empted candidate has a provenance-backed disposition and next action where open;
- `collapse_positive`: load-bearing pressure is actually landed/closed, diagnostics converge, and the residual-pressure rule for the claimed scope is met;
- `closure_confirmed`: the public claim exactly matches global COMPLETE, scoped closure, HOLD, PARTIAL, or RECURSE derived from the preceding predicates.

Held accounting may satisfy initial/lifecycle coverage while correctly failing positive collapse. Do not turn `coverage_complete` into a synonym for global closure.

#### Reconstruction and render order

- Stage06 structured NAR/reconstruction covers exact `B_total`, owner activations, Land deltas, and provenance.
- Restorative Response is present before Closing Formulation.
- Closing Formulation contains the bounded human-facing disposition and does not overclaim semantic truth.
- Closure/Reconstruction Witness follows Closing Formulation.
- Final inline parser-stable `field_witness` follows the human witness, or a predeclared external sidecar transport binds it by hash.
- The witness reconstructs body/provenance and agrees exactly with canonical trace state.
- Stage07 and Stage08 do not manufacture missing evidence.

If any condition is false or unknown, COMPLETE is unavailable.

### 8.5 Decision precedence

The canonical oracle returns one of these ordered outcomes:

1. `RECURSE`: a live eligible burden/candidate has a routable next action and resources remain.
2. `LOOPBREAK_REQUIRED`: repeated state or diagnosed curl requires interruption.
3. `HOLD`: a load-bearing route is blocked by an explicit external or owner gate.
4. `PARTIAL`: work remains but the current execution budget is exhausted; capsule is complete.
5. `CLOSURE_CANDIDATE`: all local predicates appear satisfied; final reconstruction check pending.
6. `COMPLETE`: final reconstruction and every structural predicate pass.

The precedence prevents an apparent no-new claim from outranking a live burden, held route, residual curl, or missing reconstruction.

### 8.6 Truthful open outcomes

A structurally valid HOLD/PARTIAL/RECURSE artifact must:

- preserve `B_total` and all live candidate IDs;
- state which condition blocks closure;
- preserve raw evidence and next target/action;
- carry a valid state capsule when continuation is possible;
- omit collapse-positive/COMPLETE claims;
- remain eligible for checker PASS as a truthful open artifact;
- remain ineligible for a release gate that specifically requires closed five-smoke outputs.

This distinction prevents pressure to forge closure merely to satisfy a binary checker.

### 8.7 Final witness authority and limits

The final Closure/Reconstruction Witness is a verifier projection, not a second argument body. It must include references sufficient to reconstruct:

- exact input and trace identity;
- B_LA, B_MRP, and B_total;
- dependency graph and generated provenance;
- owner obligations and ACT body references;
- per-burden Land and reread states;
- candidate dispositions;
- residual divergence/curl and LoopBreak history;
- Restorative Response and Closing Formulation locations;
- derived closure decision and predicate rows.

It must not:

- invent missing body text;
- turn a held state into landed;
- claim acyclicity without graph derivation;
- use `coverage_complete: true` as its own evidence;
- claim substantive propositions are true because the structure is complete;
- appear before Restorative Response or Closing Formulation.

## 9. Existing controls to reuse

| Existing control | Current strength | Integration requirement |
|---|---|---|
| `check_state_capsule.py` closed-state and empty-held-set logic | Stronger than local witness presence checks | Extract/import as canonical burden-coverage behavior. |
| `check_graph_completeness.py` no-new proof | Checks live burdens, route checklist, field state, residual κ, and terminal accounting | Keep as the canonical stop-proof component or move its pure predicate into `closure_state_lib.py`. |
| `check_graph_completeness.py` residual curl rules | Blocks unsafe closure in covered cases | Reuse for LoopBreak/post-break state; do not write a weaker banner-only version. |
| `recursive-state-transitions.md` STOP-after-reread rules | Correct architectural intent | Make executable and fixture-backed. |
| Stage05 held-state rejection of COMPLETE | Useful local guard | Retain as an early error, then run the whole closure oracle. |
| `check_manual_smoke_render_contract.py` render-order/body checks | Existing public-artifact gate | Extend with v2 opening and final witness order. |
| Collapse certificate | Existing positive-closure artifact | Make it consume canonical decision; never let it create the decision. |
| State capsule | Existing continuation custody | Use for PARTIAL/HOLD resumes and monotonic trace linkage. |

## 10. Exact edit map

### 10.1 Canonical atomics source files

| File | Planned edit |
|---|---|
| `atomics/skill/SKILL.md` | Add non-droppable opening-PENDING and terminal-only COMPLETE invariant; specify final render order. |
| `atomics/skill/references/rubrics/diagnostic-render-contract.md` | Introduce `opening-state-v2`; remove prospective COMPLETE from new opening formations; specify the complete proof-tail order after Closing Formulation. |
| `atomics/skill/references/rubrics/manual-contract-digest.md` | Replace the one-pass opening COMPLETE permission with OPEN/PENDING semantics and derived terminal disposition. |
| `atomics/skill/references/rubrics/non-droppable-manual-contract.md` | Add monotonic state and no COMPLETE-before-witness rules. |
| `atomics/skill/references/rubrics/output-release.md` | Define closure predicate v2, truthful open release classification, and structural-not-semantic boundary. |
| `atomics/skill/references/diagnostics/recursive-state-transitions.md` | Define the canonical state graph, illegal regressions, post-LoopBreak reread, and new-trace reopening rule. |
| `atomics/skill/references/diagnostics/framework-pipeline.yaml` | Bind conceptual closure and RECURSE edges to executable state names and canonical predicate owner. |
| `atomics/skill/references/tactics/TTP-MRP-mid-reread-pressure.md` | Ensure route results map to RECURSE/HOLD/PARTIAL/no-new without prospective completion. |

### 10.2 Runtime/checker files

| File | Planned edit |
|---|---|
| `tools/closure_state_lib.py` | **Add.** Pure state transition and closure oracle shared by producers/checkers; own separate coverage/accounting/collapse predicates, target-explicit diagnostic records, scoped residual κ, and event-DAG versus noetic-dependency relations. |
| `tools/check_opening_closure_state.py` | **Add.** Self-test/fixture runner for opening-state monotonicity, diagnostic preservation, scoped/global closure, final render order, and canonical right-reason expectations. |
| `tools/run_staged_current_skill_smoke.py` | Emit OPEN/PENDING at entry; derive Stage07 closure claim; remove OR from asserted claim into coverage; remove landed/neutral/null defaults and hard-coded graph positives; forbid STOP/no-new from rewriting raw divergence/curl; preserve raw evidence. |
| `tools/check_noetic_field_banner_samples.py` | Add version-aware opening parser; reject COMPLETE/RECURSE/HOLD/PARTIAL in v2 opening; verify monotonic relation to final witness. |
| `tools/check_staged_runtime_handshake.py` | Validate trace transitions, full closure predicate, render ordering, and proposed-versus-derived claim equality. |
| `tools/closure_witness_lib.py` | Preserve separate initial coverage, lifecycle accounting, and positive-collapse predicates; carry pre/post noetic dependency edges separately from the acyclic event/provenance DAG; consume canonical oracle. |
| `tools/check_graph_completeness.py` | Call canonical burden/field predicates; retain detailed no-new and curl diagnostics; remove duplicated weaker coverage row. |
| `tools/check_state_capsule.py` | Export or call canonical state/coverage functions; validate target-explicit diagnostics, scoped residual κ, resumed trace links, and monotonicity through the one shared state-capsule-v2 migration. |
| `tools/check_collapse_certificate_schema.py` | Require `CLOSURE_CONFIRMED`; reject certificates built from producer assertions or open traces. |
| `tools/check_manual_smoke_render_contract.py` | Enforce Restorative Response → Closing Formulation → Closure/Reconstruction Witness → final inline `field_witness` ordering and body/provenance reconstruction. |
| `tools/check_formal_reread_state_semantics.py` | Reject RECURSE without prior Land/reread and COMPLETE with any live formal state. |
| `tools/check_field_witness_convergence.py` | Compare witness predicate rows with canonical oracle and exact body refs. |
| `tools/build_staged_governed_output.py` | Render opening OPEN/PENDING and final derived disposition; never synthesize missing state. |
| `tools/run_no_model_preflight.py` | Register opening/closure state suite and minimal right-reason negatives. |

### 10.3 Generated files not to hand-edit

Do not edit `skill/**` by hand. Change atomics, rebuild, and check freshness. Expected literal generated surfaces are `skill/SKILL.md`, `skill/compiled-module-map.json`, `skill/build-manifest.json`, `skill/cold-law-manifest.json`, and the mapped runtime bundles/shards. `diagnostic-render-contract`, `manual-contract-digest`, `non-droppable-manual-contract`, `output-release`, `recursive-state-transitions`, and `framework-pipeline` are canonical atomics module identities; they need not exist at same-path generated locations. Verify their module IDs, hashes, and destinations through `skill/compiled-module-map.json` and the repository freshness checks.

### 10.4 Fixture suite to add

Add `tests/opening-closure-state/valid/` and `tests/opening-closure-state/invalid/`. Each new invalid record needs a stable `<fixture-stem>.expectation.json` sidecar under Plan A11's `daee-negative-fixture-expectation-v1`, naming earliest stage, failure class, and diagnostic ID.

Valid fixtures:

1. `open-entry-complete-final.json`: starts OPEN/PENDING and reaches COMPLETE only in the final witness.
2. `open-entry-recurse-then-complete.json`: a real Land/reread derives RECURSE; second cycle closes.
3. `open-entry-hold-final.json`: truthful HOLD with load-bearing gate and no positive certificate.
4. `open-entry-partial-resumable.json`: PARTIAL with exact capsule/next action.
5. `loopbreak-post-reread-complete.json`: diagnosed curl, valid LoopBreak, post-break reread, neutral final field.
6. `non-load-bearing-candidate-licensed.json`: an inspected candidate is terminally classified outside `H`, with basis, while residual κ is zero.
7. `legacy-v1-opening-complete.json`: historical compatibility only, marked non-promotable for v2.
8. `generated-recursion-final-witness.json`: integrates Plan 07 and reconstructs generated ACT/reread provenance before COMPLETE.

Invalid fixtures:

1. `opening-complete-before-execution.json` → opening-state failure.
2. `opening-recurse-without-prior-reread.json` → temporal-state failure.
3. `opening-hold-used-as-final-prediction.json` → temporal-state failure.
4. `local-landed-upgraded-to-global-complete.json` → closure-coverage failure.
5. `complete-with-held-burden.json` → closure-coverage failure.
6. `complete-with-unaccounted-input-pressure.json` → input-coverage failure.
7. `complete-with-live-preempted-candidate.json` → candidate-coverage failure.
8. `boolean-no-new-v2.json` → stop-proof schema failure.
9. `no-new-object-with-live-route.json` → stop-proof semantic failure.
10. `loopbreak-without-post-break-reread.json` → LoopBreak state failure.
11. `complete-with-residual-curl.json` → field-convergence failure.
12. `stage07-asserts-complete-derived-partial.json` → producer/oracle mismatch.
13. `missing-terminal-defaulted-landed.json` → unsupported-default failure.
14. `hard-coded-acyclic-with-cycle.json` → graph-derivation failure.
15. `witness-before-restorative-response.json` → render-order failure.
16. `witness-before-closing-formulation.json` → render-order failure.
17. `closing-complete-witness-missing-body-provenance.json` → reconstruction failure.
18. `complete-to-recurse-same-trace.json` → monotonic-transition failure.
19. `field-witness-before-human-witness.json` → terminal-order failure.
20. `raw-non-neutral-divergence-stop-rewritten-neutral.json` → diagnostic-rewrite failure.
21. `raw-non-null-curl-stop-rewritten-null.json` → diagnostic-rewrite failure.
22. `missing-target-in-diagnostic-record.json` → diagnostic-target failure.
23. `missing-diagnostic-defaulted-converged.json` → unsupported-default failure.
24. `held-accounting-called-collapse-positive.json` → coverage/collapse predicate failure.
25. `proof-bounded-kappa-called-global-complete.json` → residual-scope failure.
26. `cyclic-noetic-dependency-erased-from-event-dag.json` → dependency/provenance graph conflation failure.
19. `partial-without-capsule.json` → continuation-custody failure.
20. `hold-without-blocking-condition.json` → hold-custody failure.

Existing fixtures to retain and compose:

- `tests/manual-smoke-render/invalid/stage07-hold-upgraded-in-closing.md`;
- `tests/formal-reread-state-semantics/invalid/complete-closure-with-hold-partial.md`;
- `tests/graph-completeness/invalid/loopbreak-residual-curl-claimed-resolved.md`;
- `tests/graph-completeness/invalid/no-new-resultant-live-route-unaccounted.md`;
- `tests/state-capsule-fixtures/invalid/false-coverage-complete/capsule-001.json`;
- `tests/state-capsule-fixtures/valid/partial-hold-resume/`;
- `tests/collapse-certificate/valid/collapse-positive-loopbreak-resolved.json`;
- `tests/collapse-certificate/invalid/positive-with-non-neutral-divergence.json`;
- live witness dependency-graph fixtures under `tests/live-witness-fixtures/`.

These existing controls remain valid evidence for their own predicates. New fixtures must isolate the prospective-opening and monotonic-closure requirements so an earlier Stage03 or owner-route error cannot hide the intended failure.

### 10.5 Documentation and scorecard changes

| Surface | Planned edit |
|---|---|
| Stage01-08 architecture docs | Show the recursive return edge and terminal closure oracle; preserve public stage numbering. |
| Runtime/operator guide | Explain OPEN, RECURSE, HOLD, PARTIAL, and COMPLETE in plain language; identify COMPLETE as structural only. |
| Fixture inventory | Classify legacy-v1 compatible, v2 promotable, truthful-open, and collapse-positive cases separately. |
| Model compliance scorecard | Score opening temporality, monotonic transitions, body/provenance reconstruction, and truthful open state separately; never score answer length as closure. |
| Release checklist | Require all five smoke traces and exact oracle/certificate parity; retain `regression_status: unproven` until comparison artifacts exist. |

## 11. TDD phases and exact commands

### Phase 0: Baseline and evidence custody

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
git status --short
git rev-parse HEAD
python tools\check_noetic_field_banner_samples.py tests\mrp-route-invariants\valid\synthetic-linear-chain.md
python tools\check_manual_smoke_render_contract.py
python tools\check_formal_reread_state_semantics.py
python tools\check_graph_completeness.py
python tools\check_field_witness_convergence.py
python tools\check_state_capsule.py --self-test
python tools\check_collapse_certificate_schema.py
python tools\check_staged_runtime_handshake.py
Pop-Location
```

Expected:

- clean or fully inventoried worktree;
- intended head, or refreshed evidence anchors before editing;
- all current baseline suites exit `0`;
- any pre-existing nonzero exit becomes a separate ANDON and is not hidden by the patch.

Before editing, capture the current source enum and a retained banner-checker artifact as legacy-v1 evidence. If a complete-opening artifact is added for migration replay, it must satisfy the full legacy checker for the right reason; the current route-invariant fixture containing COMPLETE is not automatically banner-valid. Legacy evidence proves backward behavior only and is not v2-promotable.

### Phase 1: Red tests for temporality

Add minimal v2 fixtures and a new closure-state checker harness before production changes:

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_opening_closure_state.py
Pop-Location
```

Expected before implementation: exit `1`. The first reported failures must include:

- opening COMPLETE prohibited under v2;
- opening RECURSE lacks prior reread;
- asserted Stage07 complete differs from derived partial;
- same-trace COMPLETE-to-RECURSE is illegal.

The test is not adequately red if it fails only because a new schema key is unknown.

### Phase 2: Pure closure oracle

Implement `tools/closure_state_lib.py` and unit-test every predicate row and state transition without invoking a model.

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_opening_closure_state.py --self-test
Pop-Location
```

Expected: exit `0`; all valid fixtures accepted; all invalid fixtures rejected by expected diagnostic ID. The new checker contract must implement and document `--self-test`; the command above is part of the acceptance surface.

Property tests must generate topic-neutral states over arbitrary B_total cardinality and cycle depth. Representative sizes may include 1, 10, and 20 burdens as capacity probes, never as expected topology or adequacy floors.

### Phase 3: Opening banner v2 migration

Update atomics and the banner checker with explicit legacy/v2 behavior.

Positive:

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_opening_closure_state.py --fixture tests\opening-closure-state\valid\open-entry-complete-final.json
Pop-Location
```

Expected: exit `0`; opening is OPEN/PENDING and COMPLETE occurs only in final witness.

Right-reason negative:

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
try {
  $raw = python tools\check_opening_closure_state.py --explain --fixture tests\opening-closure-state\invalid\opening-complete-before-execution.json
  $code = $LASTEXITCODE
  $diag = $raw | ConvertFrom-Json
  if ($code -ne 1) { throw "expected checker exit 1, got $code" }
  if ($diag.failure_class -ne 'opening_state.complete_is_terminal_only') { throw "wrong class: $($diag.failure_class)" }
  if ($diag.earliest_stage -ne '01') { throw "wrong earliest stage: $($diag.earliest_stage)" }
  if (($diag.downstream_invalidated -join ',') -ne '02,03,04,05,06,07,08') { throw 'wrong downstream invalidation set' }
} finally {
  Pop-Location
}
```

Expected: checker exit `1` is captured, the wrapper exits `0`, and the stable diagnostic identifies `opening_state.complete_is_terminal_only` at Stage01 with Stages02-08 invalidated. The new checker must implement and self-test the exact `--fixture` and `--explain` flags used above.

Canonical acceptance command:

```powershell
python tools\assert_expected_rejection.py --expectation tests\opening-closure-state\invalid\opening-complete-before-execution.expectation.json --artifact-root auto
```

Expected: exit `0`; the expectation pins the opening boundary and forbids all later stage/promotion artifacts.

### Phase 4: Runner and handshake integration

Remove producer authority over completion:

- Stage07 stores `proposed_closure_claim` from model output, if present;
- canonical oracle stores `derived_closure_decision`;
- mismatch is a failure or truthful downgrade, never an upgrade;
- state-capsule coverage is derived without OR from proposed claim;
- absent state remains unknown/open;
- graph completeness and acyclicity are computed.

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_staged_runtime_handshake.py --records tests\opening-closure-state\valid\open-entry-recurse-then-complete.json
python tools\check_staged_runtime_handshake.py --explain-stage-failure --records tests\opening-closure-state\invalid\stage07-asserts-complete-derived-partial.json
Pop-Location
```

Expected:

- first command exits `0`;
- second exits `1` with `earliest_stage: "07"`, `failure_class: "public-projection"`, and Stages08 downstream invalidated;
- if an earlier stage fails, simplify the fixture until it isolates Stage07.

The Stage07 invalid fixture also runs through:

```powershell
python tools\assert_expected_rejection.py --expectation tests\opening-closure-state\invalid\stage07-asserts-complete-derived-partial.expectation.json --artifact-root auto
```

### Phase 5: Render order and reconstruction witness

Extend the manual render and field-witness checks:

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_manual_smoke_render_contract.py
python tools\check_field_witness_convergence.py
python tools\check_graph_completeness.py
python tools\check_collapse_certificate_schema.py
Pop-Location
```

Expected: all exit `0`; invalid order fixtures fail in their own suite; final witness reconstruction uses exact body refs and cannot repair missing execution.

### Phase 6: Open-state continuation and LoopBreak

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_state_capsule.py --self-test
python tools\check_formal_reread_state_semantics.py
python tools\check_mid_reread_pressure.py
python tools\check_mrp_route_invariants.py
Pop-Location
```

Expected: all exit `0`. HOLD/PARTIAL resume fixtures preserve exact B_total and next action. LoopBreak without post-break reread fails. A valid open artifact may pass structurally while remaining collapse-negative.

### Phase 7: Rebuild and static promotion

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\build_compiled_runtime.py
python tools\check_compiled_runtime_freshness.py
python tools\check_route_shard_selection.py
python tools\measure_load_path_budget.py --enforce-ratchet --enforce
python tools\run_no_model_preflight.py --self-test
python tools\run_no_model_preflight.py
Pop-Location
```

Expected: every command exits `0`; opening/closure contracts are present in the selected runtime shard; configured load-path budget remains satisfied; no-model inventory names the new tests. PASS remains structural only.

### Phase 8: Five-smoke Stage01-Stage08 gate, separately authorized

After implementation authorization and no-model closure, run the exact registered inputs:

| Smoke ID | Required state evidence |
|---|---|
| `gate88-secularism` | Opening OPEN/PENDING; no COMPLETE until final oracle; every live burden/candidate accounted for. |
| `gate88-khaybar` | Same generic contract; source/provenance pressure may yield RECURSE/HOLD/PARTIAL without being forced closed. |
| `gate88-trinitarian-j173` | Dynamic topology and generated routes allowed; exact owner/body reconstruction before closure. |
| `gate88-tst-lillard` | Held/generated recoil retained; LoopBreak and residual curl handled monotonically. |
| `gate88-torah-quran-source-authentication` | Exact registered prompt; no hard-coded conclusion, burden number, submove number, or argument bank. Structural state only is asserted by the verifier. |

Every smoke must traverse Stage01 through Stage08 under the same code path. For v0.4.6.0-WIP completion, the agreed promotion packet requires five closed traces; a truthful HOLD/PARTIAL/RECURSE smoke is not checker corruption, but it leaves the release gate open and must be investigated or resumed rather than upgraded.

## 12. Exact right-reason matrix

| Fixture | Exit | Earliest stage | Failure class | Stable reason |
|---|---:|---|---|---|
| opening COMPLETE v2 | 1 | 01/public opening | `opening-state` | COMPLETE is terminal-only |
| opening RECURSE without reread | 1 | 01/public opening | `opening-state` | RECURSE requires prior Land/reread |
| local landed → global complete | 1 | 07 | `public-projection` | global closure predicates incomplete |
| complete with held B_total burden | 1 | 07 | `public-projection` | held load-bearing state blocks closure |
| complete with input pressure unaccounted | 1 | 07 | `public-projection` | Stage02 coverage incomplete |
| no-new Boolean under v2 | 1 | 05 | `mrp` | structured stop proof required |
| no-new with live candidate | 1 | 05 | `mrp` | stop not licensed |
| LoopBreak lacks post-reread | 1 | 05 | `mrp` | post-break reread missing |
| residual curl plus complete | 1 | 07 | `public-projection` | field not converged |
| producer complete, oracle partial | 1 | 07 | `public-projection` | proposed/derived mismatch |
| witness before Closing Formulation | 1 | 07 | `public-projection` | render-order violation |
| witness missing body provenance | 1 | 07 | `public-projection` | reconstruction incomplete |
| COMPLETE → RECURSE same trace | 1 | 07 | `public-projection` | non-monotonic transition |
| valid open HOLD | 0 | none | none | structurally valid, collapse-negative |
| valid partial resumable | 0 | none | none | structurally valid, collapse-negative |
| valid recursive complete | 0 | none | none | final witness equals canonical oracle |

Where current handshake classification cannot express `opening-state`, add that failure class explicitly or map it to the repository's canonical public-projection class. Do not misclassify it as an owner-route failure.

## 13. Five-smoke evidence and promotion record

Each smoke's artifact packet must contain:

- input fixture ID and SHA-256;
- repo commit and dirty-state evidence;
- compiled runtime SHA-256/freshness;
- opening state contract/version and parsed opening fields;
- ordered state-transition log;
- Plan 02 pressure-inventory coverage;
- Plan 07 B_LA/B_MRP/candidate lifecycle;
- owner obligations, body refs, Land, and reread records;
- residual divergence/curl and LoopBreak/post-break evidence;
- Restorative Response location;
- Closing Formulation location and bounded claim;
- final Closure/Reconstruction Witness location and predicate rows;
- proposed versus derived closure decision;
- Stage01-08 checker exits and diagnostics;
- collapse-certificate result;
- `semantic_truth_proven: false`;
- `regression_status: unproven` until comparison custody exists.

The fifth smoke's expected contract must not state how many burdens or submoves should be selected and must not prescribe a substantive answer. Its value is pressure across source authentication, tribunal selection, comparative narrative claims, corruption inference, and burden provenance while allowing the runtime to choose the actual topology.

## 14. Compatibility and rollback

### 14.1 Migration sequence

1. Add the pure closure oracle and fixtures without changing rendering.
2. Make existing checkers consume the oracle while preserving legacy-v1 parsing.
3. Add opening-state-v2 generation behind an explicit contract version.
4. Remove Stage07 hard-coded positives and unsupported defaults.
5. Make v2 the promotion default only after full no-model parity.
6. Retain legacy replay for historical artifacts, clearly marked non-promotable under v2.
7. Require v2 for the five-smoke release packet.

### 14.2 Rollback rules

If a phase fails:

- revert only the bounded phase patch;
- preserve failing artifact, raw record, command, exit, and diagnostic;
- keep legacy-v1 replay available;
- do not weaken an invalid fixture;
- do not make COMPLETE legal at opening to restore fixture count;
- do not downgrade held/curl/body-provenance checks;
- do not hand-edit generated runtime files;
- leave release promotion blocked.

Rollback to v1 restores old compatibility, not proof that v1 closure semantics are adequate.

## 15. STOP/ANDON conditions

Stop the implementation lane and record an ANDON when:

1. Baseline tree or commit custody is unclear.
2. A baseline checker fails before edits.
3. Any v2 opening contains COMPLETE, RECURSE, HOLD, or PARTIAL as a fresh prediction.
4. Proposed model closure is allowed to override derived closure.
5. Missing state defaults to landed/closed/complete.
6. Graph `acyclic` or diagnostic `complete` is emitted without derivation.
7. Any load-bearing live burden remains in `H` or any live candidate coexists with global COMPLETE; scoped/HOLD/PARTIAL release must name the held set and next action.
8. LoopBreak closes without post-break reread.
9. Residual curl is non-null/non-resolved while COMPLETE is claimed.
9a. Missing/non-neutral divergence or missing/non-null curl is defaulted or rewritten to neutral/null because STOP/no-new was proposed.
9b. Event/provenance DAG acyclicity is used to erase a cyclic noetic dependency relation rather than preserving pre/post LoopBreak edges.
10. Restorative Response, Closing Formulation, Closure/Reconstruction Witness, and final `field_witness` order is violated.
11. Final witness cannot reconstruct body/provenance but still passes.
12. A valid truthful open artifact is forced to COMPLETE to satisfy release scoring.
13. A fixed size/count floor or topic-specific answer branch is proposed.
14. Structural PASS is described as substantive truth.
15. Same-fixture comparative language appears without captured v45/v46 artifacts.

ANDON record:

```yaml
andon_id: DAEE-V46-MONOTONIC-CLOSURE
timestamp_utc: null
repo_head: null
phase: null
trace_id: null
command: null
exit_code: null
opening_state: null
proposed_closure: null
derived_closure: null
live_burdens: []
live_candidates: []
held_set: []
divergence_records: []
curl_records: []
kappa_residual: null
loopbreak_ref: null
post_break_reread_ref: null
render_order_refs: {}
earliest_stage: null
failure_class: null
containment: null
owner: null
next_evidence_needed: null
regression_status: unproven
semantic_truth_proven: false
```

## 16. Definition of Done

Plan 08 is implemented only when:

- [ ] Every new release-bearing artifact opens with `opening-state-v2`, OPEN, and PENDING.
- [ ] No v2 opening may declare COMPLETE or RECURSE prospectively.
- [ ] One canonical closure oracle is used by runner, handshake, witness, graph, capsule, and collapse-certificate surfaces.
- [ ] COMPLETE is emitted only from `CLOSURE_CONFIRMED` after final reconstruction.
- [ ] State transitions are monotonic and COMPLETE cannot return to RECURSE/HOLD/PARTIAL in the same trace.
- [ ] New evidence after closure starts a linked new trace.
- [ ] `initial_coverage_complete`, `lifecycle_accounting_complete`, `collapse_positive`, and `closure_confirmed` are distinct, exact predicates; held/PARTIAL accounting is never mislabeled positive collapse.
- [ ] Every selected owner obligation and generated burden has reconstructible execution/body provenance.
- [ ] Every Land has a per-burden reread.
- [ ] Every live candidate and pre-empted route is terminally accounted for.
- [ ] Structured no-new proof is independently recomputed.
- [ ] Any load-bearing live item in `H`, unresolved burden, unknown terminal state, or live candidate blocks global COMPLETE; honest held material remains representable for HOLD/PARTIAL/scoped release.
- [ ] Divergence/curl are target-explicit records; missing remains unknown/open; STOP/no-new cannot rewrite raw diagnostic state.
- [ ] Residual curl and LoopBreak/post-break reread rules are centrally enforced, with pre/post noetic dependency edges preserved separately from the acyclic event/provenance DAG.
- [ ] Global COMPLETE requires residual κ zero; scoped closure may carry proof-bounded κ only with scope, basis, and reopen condition.
- [ ] Resource exhaustion yields PARTIAL with a valid capsule.
- [ ] Restorative Response precedes Closing Formulation.
- [ ] Closing Formulation precedes the Closure/Reconstruction Witness.
- [ ] The final inline parser-stable `field_witness` follows the human witness, or the predeclared external-sidecar transport binds it by hash.
- [ ] The final witness reconstructs body/provenance and cannot manufacture it.
- [ ] Hard-coded `closure_claim: complete`, `acyclic: true`, `complete: true`, and missing-state-to-landed defaults are removed from promotion paths.
- [ ] Legacy-v1 artifacts remain replayable but cannot prove v2 promotion.
- [ ] Every new negative fails at the intended earliest stage for the intended reason.
- [ ] Existing banner, render, MRP, graph, witness, capsule, collapse, route, freshness, and no-model checks pass.
- [ ] All five registered smokes complete Stage01-08 with opening/closing/witness parity.
- [ ] The fifth smoke remains an input, not an argument bank.
- [ ] Structural PASS is explicitly bounded from semantic truth/provenance/uptake.
- [ ] `regression_status` remains `unproven` until same-fixture comparison evidence exists.

## 17. Confidence and owner decisions

**Implementation-readiness assessment: PARTIAL, high confidence in the confirmed abnormality and corrective architecture; a small number of schema decisions remain owner-gated.**

Confirmed enough to implement:

- current opening COMPLETE permission;
- non-monotonic/producer-authority risk;
- divergence among closure definitions;
- optimistic defaults and literal positive projection fields;
- render-order requirement;
- availability of stronger existing predicates to reuse;
- fixture and checker surfaces required for a safe migration.

Owner decisions before coding:

1. Approve `OPEN/PENDING` as the sole fresh opening-state-v2 pair. This plan recommends it because RECURSE cannot truthfully precede reread and COMPLETE cannot precede closure.
2. Decide whether legacy-v1 compatibility has a deprecation date or remains indefinitely replay-only.
3. Choose whether `closure_state_lib.py` absorbs the pure parts of graph/state-capsule checks or imports helpers extracted from those modules. There must still be one direction of authority and no circular imports.
4. Approve exact stable diagnostic IDs for opening-state and monotonicity failures.
5. Confirm that five-smoke promotion requires closed traces while truthful open traces remain valid diagnostic artifacts but block release.

Unproven until later authorized work:

- model behavior after the contract change;
- v45/v46 comparative regression;
- semantic adequacy or truth of any generated answer.

The implementation can begin after those ownership decisions. The core defect does not require further speculation: PR9 currently legalizes a terminal state at opening and does not derive closure through one canonical monotonic oracle.
