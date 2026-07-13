# ANDON A07: MRP Recursion and Generated, Held, and Pre-empted Burden Lifecycle

**Plan class:** P0/P1 patch-execution-grade engineering plan  
**Scope:** Stage03 route, Stage04 ACT/Land, Stage05 MRP reread, and their projections into Stages06-08  
**Implementation target:** `C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`  
**Observed PR9 head:** `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
**Planning status:** ready for implementation sequencing; no implementation performed by this plan  
**Regression status:** `unproven` until same-fixture v0.4.5.0/v0.4.6.0 captured outputs exist  

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## 1. Plain-language result

PR9 already knows several important rules: a generated burden must not be smuggled into the input-derived burden floor, it must name its MRP parent, it must have a dependency edge, and it must receive a terminal accounting state. Those controls are real and should be retained.

The confirmed architectural defect is that the current staged runner can **declare** a generated burden at Stage05 but cannot **execute** that burden. The runner invokes Stages01 through 06 once each. Stage04 is restricted to the targets routed from the original Stage02 burden floor. A burden first instantiated by Stage05 therefore arrives after the only ACT pass in which it could have been worked. Stage07 correctly tends to carry such a burden as `RECURSE`, but there is no executable return edge from Stage05 to Stage03/04/05 inside the run.

This makes MRP recursion descriptive rather than operational. It also prevents the runtime from faithfully representing inputs whose field navigation genuinely requires:

- activation of an already-held input burden;
- a new MRP-generated burden;
- a generated burden that itself generates a later burden;
- an eligible burden that is pre-empted for ordering but remains live;
- a candidate route that is inspected and rejected as non-load-bearing;
- `no_new_resultant` only after all live routes and candidates have been accounted for.

The repair is not a fixed burden count, a fixed recursion depth, a text-length floor, or an argument bank. It is a governed, data-dependent burden-cycle executor with append-only provenance and a truthful open-state exit when its resource budget is exhausted.

## 2. Non-negotiable boundary

This plan does not authorize source edits, model calls, packaging, commits, pushes, issues, releases, or publication. It specifies how a later implementation lane should proceed.

The following remain prohibited as solutions:

1. A minimum or maximum number of burdens chosen as a proxy for adequacy.
2. A minimum number of submoves per burden chosen independently of derived obligations.
3. A byte, token, paragraph, or word floor used as a semantic-completeness gate.
4. Topic-specific branches for the Torah/Qur'an smoke or any other registered smoke.
5. Treating checker PASS as proof that a theological, historical, or philosophical claim is true.
6. Relabeling a generated burden as `B_LA` to make it executable in the existing single pass.
7. Treating a pre-empted candidate as discharged merely because it was not selected.
8. Claiming a v0.4.5.0-to-v0.4.6.0 regression without same-fixture captured artifacts.

## 3. ANDON statement and current false-pass surface

### 3.1 Abnormality

The specified pipeline contains a recursive burden cycle, but the current Stage01-Stage08 executable path is acyclic at the point where recursion is required. A Stage05-generated `B_MRP` burden can be structurally recorded and projected, yet cannot pass through a subsequent Stage03 route and Stage04 ACT/Land cycle in the same run.

### 3.2 Why this is a major ANDON

The framework's central engineering promise is runtime selection of arbitrary noetic topology. The input may yield one burden or many; any burden may yield one operation or several; rereading may expose a held burden or instantiate a genuinely new one. If the runtime can only execute the initial floor, then the topology is effectively frozen before the point at which MRP is designed to discover more topology.

This is not merely a rendering omission. It breaks the causal path from diagnosis to recursive execution and can cause one of two unsafe outcomes:

- truthful but permanently open output: the generated burden is carried as `RECURSE` with no mechanism to resume it; or
- false closure: downstream code or prose treats the first pass as complete despite an unexecuted generated or held burden.

### 3.3 Current false-pass

The current structural suite can pass a maximal Stage05 fixture that declares a generated burden, assigns provenance, and carries it in `RECURSE`. That is a legitimate test of declaration and accounting, but it can be mistaken for proof of executable recursion. It is not such proof.

The false-pass proposition is therefore:

> “A valid Stage05 generated-burden record proves the Stage01-Stage08 runtime can route, execute, reread, and close that generated burden.”

That proposition is false under the inspected runner. Existing tests prove record shape and open-state custody, not an executed recursive cycle.

## 4. Evidence status

### 4.1 Confirmed by direct PR9 GEMBA

| ID | Confirmed fact | Direct owner/evidence |
|---|---|---|
| C07-01 | The top-level smoke runner invokes Stages01-06 once, in order. | `tools/run_staged_current_skill_smoke.py`, the `stage_ids_to_run = STAGE_ORDER[:6]` execution loop near lines 19127-19203. |
| C07-02 | Stage03 route targets are constrained to the Stage02 burden floor. | `tools/check_staged_runtime_handshake.py`, Stage02/03 cross-stage checks near lines 2123-2126. |
| C07-03 | Stage04 ACT targets must come from Stage03 route targets. | `tools/check_staged_runtime_handshake.py`, Stage04 normalization/validation near lines 1816-1982 and cross-stage checks near lines 2137-2146. |
| C07-04 | Stage05 rejects a generated burden placed in the Stage02 floor and requires its parent to be pre-existing. | `tools/check_staged_runtime_handshake.py`, generated-provenance checks near lines 1520-1531. |
| C07-05 | A Stage05-generated burden therefore cannot have been a valid Stage04 ACT target in the same single pass. | Logical conjunction of C07-01 through C07-04; no model behavior assumption is needed. |
| C07-06 | Stage07 marks a generated burden without Stage04 execution as `carried-RECURSE`, `generated_unexecuted`, and unresolved. | `tools/run_staged_current_skill_smoke.py`, generated-burden projection near lines 3739-3799. |
| C07-07 | The conceptual pipeline includes a RECURSE return edge from the post-render gate to the diagnostic gate. | `atomics/skill/references/diagnostics/framework-pipeline.yaml`, recursive-gate description near lines 241-250 and edge near lines 424-427. |
| C07-08 | The executable runner does not implement the conceptual Stage05-to-route/ACT return edge. | Direct control-flow inspection of `tools/run_staged_current_skill_smoke.py`. |
| C07-09 | The maximal Stage05 workbench fixture leaves the generated burden open; it does not demonstrate a second ACT cycle. | `tests/stage-contract-workbench/stage-05-mrp-reread-terminal-state/maximal-valid/generated-burden-recurse-with-loopbreak.json`. |
| C07-10 | Current source and checkers already distinguish held activation, generated instantiation, no-new result, and LoopBreak-related states. | `atomics/skill/references/tactics/TTP-MRP-mid-reread-pressure.md`; `tools/check_mid_reread_pressure.py`; `tools/check_mrp_route_invariants.py`; `tools/check_mrp_generated_burden.py`. |
| C07-11 | The runner contains semantic normalization that can transform a raw Stage05 STOP/no-new response into a held activation and add graph/prose fields. | `tools/run_staged_current_skill_smoke.py`, `normalize_stage05_initial_burden_continuations` near lines 6646-6776 in the inspected file. |
| C07-12 | Generated depth and graph-completeness properties are partly defaulted or hard-coded in downstream projection. | `tools/run_staged_current_skill_smoke.py`, generated-depth projection near lines 3679-3718 and coverage/graph projection near lines 5390-5399. |

### 4.2 Inferred, not confirmed

| ID | Inference | Why it remains an inference |
|---|---|---|
| I07-01 | The missing executable loop likely contributes to thin or absent B_MRP bodies in observed v0.4.6.0 outputs. | The architecture prevents execution, but no controlled same-fixture model experiment has isolated its contribution to output thinness. |
| I07-02 | Stage05 semantic repair may mask model noncompliance and make runtime records look more governed than the raw response was. | The transformation is present; its actual frequency requires captured raw and normalized artifacts. |
| I07-03 | A model may learn from the compact runtime footprint to stop after the initial burden floor. | Plausible prompt/runtime effect, but causal attribution requires model artifacts and controlled comparison. |

### 4.3 Unproven and explicitly not claimed

- That v0.4.6.0 is worse than v0.4.5.0 on the same inputs.
- That any particular burden count is correct for any registered smoke.
- That recursive execution will make every output longer.
- That structurally closed output is semantically correct, historically accurate, persuasive, or taken up by a reader.
- That every generated candidate should become a burden.

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

One bounded reviewer invocation of `python tools\run_no_model_preflight.py` did not complete within 124 seconds; it was in `tools/gen_fixture_mutations.py --self-test` when that invocation timed out. That attempt is non-evidence, not a failed invariant. The primary audit subsequently reran the exact command with a 900-second allowance: it exited `0` after 370.2 seconds and all 16 gates passed. That later pass is the controlling planning baseline. It still does not test the new lifecycle contract proposed here and no model smoke was run.

## 5. Formal-chain location

The governed chain is:

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

As in Plan A05, the public chain is an aggregate projection. Within each executed ACT capsule the causal micro-order is `OPᵢ -> local_deltaᵢ -> contribution_to_Land`; `Land(ⁿB)` reduces those contributions and the following `ΔⁿB/Δκ` is the derived burden-level change used by diagnostics and reread. The recursion return edge begins only after that aggregate delta and its target-explicit diagnostics exist.

The defect is not at only one node. It is a missing executable return path across five adjacent transitions:

```text
Land(ⁿB)
→ ΔⁿB/Δκ
→ ∇·T/∇×T
→ R(H, ...)
→ [held activation or B_MRP instantiation]
→ ∇_route
→ {ⁿBᵢ[OPᵢ]}
→ Land(ⁿB)
```

In current PR9, the first path through `∇_route → ACT → Land → MRP` exists. The return from `R(...)` to `∇_route` exists in the conceptual YAML and prose, but not in the staged runner. Consequently:

- **burden number:** `B_LA` can be selected dynamically at Stage02, but executable `B_total` cannot grow after Stage04;
- **burden length:** a generated burden has no owner-backed ACT body in the same run, so its body cannot be reconstructed from execution provenance;
- **submove number:** owner-derived operations for a new burden cannot be routed and instantiated after generation;
- **recursion:** a generated burden cannot itself be reread after ACT and therefore cannot generate a deeper burden;
- **pre-emption:** a candidate can be named, but there is no durable scheduling lifecycle proving whether it was deferred, rejected, or later activated;
- **closure:** `no_new_resultant` cannot safely mean “no remaining live topology” unless all candidate and burden states across all cycles are closed.

## 6. Real 5 Whys

### Problem statement

Why can the current PR9 head record a generated burden but not execute it within the same Stage01-Stage08 run?

1. **Why is the generated burden unexecuted?**  
   Because it is first instantiated by Stage05, after the one Stage04 ACT call has completed.

2. **Why is there no later ACT call?**  
   Because `run_staged_current_skill_smoke.py` executes a fixed linear list of Stage01-06 calls once and then proceeds to projection and release.

3. **Why can the generated burden not be anticipated in the first Stage04 call?**  
   Because the checker correctly requires Stage03/04 targets to derive from the Stage02 `B_LA` floor, while a genuine `B_MRP` burden must be absent from that floor and have MRP provenance. Anticipating it there would falsify provenance.

4. **Why did record-level generated-burden controls not expose the missing executor?**  
   Because fixtures and checkers independently validate declaration, provenance, dependency edges, terminal labels, and open-state carrying. They do not require evidence of a second route/ACT/MRP cycle for a generated burden before treating the Stage05 record as valid.

5. **Why was conceptual recursion not translated into an executable contract?**  
   Because architecture prose/YAML and the single-pass runner/checker evolved under separate owners; no canonical owner was assigned to recursive cycle state, scheduling, provenance, and convergence. Direct Git-object inspection now confirms the linear `STAGE_ORDER[:6]`/single `for stage_id in stage_ids_to_run` path at current main `c86b3c6...`, PR9 base `56d023e...`, and PR9 head `6987c9e...`. The structural gap is therefore `code_lineage: main-inherited`; its original introduction commit is outside this plan's causal requirement.

### Actionable root cause

The root cause is a **contract/runner ownership gap**: there is no canonical recursive-cycle schema and no executor that owns the transition from a Stage05 route result back to Stage03/04/05. This is narrower and more actionable than blaming model brevity, token pressure, or checker weakness in the abstract.

`regression_status: unproven`. `code_lineage: main-inherited`. These fields must remain separate in issue/closure ledgers.

### Contributing causes

1. Stage05 route outcomes are represented largely as an end-of-stage summary rather than scheduler events.
2. Generated-burden parent validation assumes only pre-MRP parents, preventing B_MRP-to-B_MRP chains in one aggregate record.
3. Downstream projection defaults `generation_depth` rather than deriving it from a recursive event graph.
4. Some runner normalizers alter semantic route outcomes instead of rejecting nonconforming raw output.
5. Tests distinguish valid open records from invalid records, but there is no end-to-end positive fixture proving generated execution.
6. Conceptual and executable pipeline representations are checked for shape, but not for reachability equivalence at the recursion edge.

## 7. Hansei

1. **We tested nouns more strongly than transitions.** `B_MRP`, `generated_by`, and terminal-state fields were guarded, but the transition that makes the burden actionable was not.
2. **We allowed an open record to stand in for an executable capability.** Carrying a generated burden as `RECURSE` is truthful custody, but it is not proof that recursion can run.
3. **We split completeness logic across stages and helpers.** This made it possible to preserve local validity while missing global reachability.
4. **We let normalization cross from syntax repair into semantic authorship.** A runner may normalize Unicode or field spelling; it must not invent the model's MRP decision and then count that invention as evidence.
5. **We encoded a conceptual return edge without a promotion test for it.** Pipeline diagrams and prose need an executable path witness.
6. **We treated generation depth as presentation metadata.** It is a causal property of the burden graph and must be derived.
7. **We did not preserve candidate non-instantiation as first-class evidence.** That leaves “pre-empted,” “non-load-bearing,” and “forgotten” too easy to conflate.

## 8. Target architectural contract

### 8.1 Preserve the outer eight stages

Stage01 through Stage08 remain the public governance sequence. The repair is an internal governed cycle across Stages03-05, not a renumbering of the public pipeline:

```text
Stage01 intake
Stage02 input-pressure inventory and immutable B_LA
Stage03/04/05 burden cycle repeated as demanded by runtime state
Stage06 reconstruction
Stage07 governed projection and closure candidate
Stage08 verification and proof-sidecar publication
```

### 8.2 Introduce one canonical cycle owner

Add `tools/mrp_recursion_lib.py` as the canonical structural library for:

- burden-track membership;
- event ordering;
- candidate disposition;
- parent/depth derivation;
- next-target selection;
- repeated-state detection;
- cycle termination classification;
- exact graph projection consumed by Stage06/07 checkers.

The library must be pure with respect to model calls: it accepts parsed stage records and returns a derived lifecycle state plus structural errors. The runner owns model invocation; the library owns deterministic state transition validation.

### 8.3 Version the handshake additively

Retain legacy fixtures under `staged-runtime-handshake-v1`. Require new promotion runs to emit `staged-runtime-handshake-v2` with this top-level shape:

```yaml
recursion_contract: mrp-cycle-v1
B_LA: [B1, B2]
B_MRP: [B3, B4]
B_total: [B1, B2, B3, B4]
burden_cycles:
  - cycle_id: C1
    parent_cycle_id: null
    target_burden_id: B1
    target_track: B_LA
    generation_depth: 0
    route_record_ref: stage03-C1
    act_record_ref: stage04-C1
    reread_record_ref: stage05-C1
    exit_disposition: generated_burden_instantiation
  - cycle_id: C2
    parent_cycle_id: C1
    target_burden_id: B3
    target_track: B_MRP
    generation_depth: 1
    route_record_ref: stage03-C2
    act_record_ref: stage04-C2
    reread_record_ref: stage05-C2
    exit_disposition: no_new_resultant
mrp_candidate_events: []
terminal_states: {}
```

Field names may be adjusted once implementation inspects nearby serialization conventions, but the information content and invariants below are mandatory.

### 8.4 Burden-set invariants

1. `B_LA` is immutable after Stage02.
2. `B_MRP` is append-only.
3. `B_LA ∩ B_MRP = ∅`.
4. `B_total = ordered_unique(B_LA + B_MRP)`.
5. A burden ID is created once and never changes track.
6. Every `B_MRP` burden has one instantiation event.
7. Every instantiation event identifies a previously instantiated parent burden.
8. A parent may be in `B_LA` or an earlier `B_MRP`; this enables arbitrary finite depth.
9. `generation_depth(parent in B_LA) = 0`; `generation_depth(child) = generation_depth(parent) + 1`.
10. Depth is derived, never accepted as an unsupported model assertion.
11. The event/provenance graph is acyclic by checked event order, not by a hard-coded `acyclic: true` field. The noetic dependency relation is a separate graph and may be cyclic before LoopBreak; preserve pre-break and post-break edge sets and the operation that changed them.

### 8.5 Candidate lifecycle

MRP must record every route candidate that could affect closure in `mrp_candidate_events`. A candidate is not automatically a burden. It becomes a burden only through a valid instantiation event.

Each event must carry:

```yaml
candidate_id: E-C1-01
source_cycle_id: C1
source_burden_id: B1
source_reread_ref: stage05-C1
route_basis_refs: [field-ref-1]
candidate_kind: held_activation | generated_instantiation | escape_route | unclassified
target_burden_id: B2 | B3 | null
disposition: activate_held | instantiate_generated | defer_preempted | non_load_bearing | loopbreak | hold_partial | no_new_resultant
disposition_basis_refs: [field-ref-2]
next_cycle_id: C2 | null
```

Rules:

- `activate_held` targets an existing `B_LA` burden and schedules it.
- `instantiate_generated` appends exactly one new `B_MRP` burden and schedules it.
- `defer_preempted` keeps the candidate live; it cannot support STOP or COMPLETE.
- `non_load_bearing` requires an explicit basis showing why no burden obligation remains.
- `loopbreak` requires diagnosed curl and leads to a post-break reread before closure.
- `hold_partial` preserves an unresolved burden or candidate with an explicit gate/next action.
- `no_new_resultant` is a terminal proof object, not a bare Boolean or slogan.
- A candidate that is inspected and rejected is never inserted into `B_total`.
- A candidate that is instantiated is never left only in prose.
- The current eight named route/result classes are known canaries, not an exhaustive universe. Candidate types surfaced by runtime state derive the accounting set. An unknown/unclassified candidate is retained and routes HOLD/PARTIAL until classified; it is never rejected merely for being a ninth type and never silently omitted.

This distinguishes **pre-empted but live**, **considered but non-load-bearing**, and **instantiated burden**. They must never collapse into a single “not selected” state.

### 8.6 Executor algorithm

The runner must implement this data-dependent loop:

1. Run Stage01 once.
2. Run Stage02 once and freeze `B_LA` plus the input-pressure inventory.
3. Select the next eligible target from the lifecycle state.
4. Run Stage03 for that target and record `cycle_id`.
5. Run Stage04 ACT/Land for every owner obligation derived for that target.
6. Run one Stage05 per-burden reread for that target.
7. Validate the raw Stage05 event before any semantic normalization.
8. Apply exactly one governed exit disposition.
9. If held activation or generated instantiation schedules a target, return to step 4.
10. If LoopBreak is invoked, execute its interruption and a post-break reread before selecting a terminal disposition.
11. If HOLD/PARTIAL is reached, stop the recursive executor with open custody and do not claim closure.
12. If `no_new_resultant` is proposed, validate the full proof object against all burdens and candidate events.
13. Proceed to Stage06 only when the lifecycle state has a truthful terminal classification: closed, held, or partial.

The loop has no fixed burden-count or depth limit. Operational resource controls may cap time, model calls, or context use, but exhaustion must yield `PARTIAL` with resumable state, never synthetic `no_new_resultant` or COMPLETE.

### 8.7 Repeated-state and cycle guard

Compute a deterministic state signature after each reread from:

- ordered `B_LA` and `B_MRP`;
- terminal state of every `B_total` burden;
- live candidate IDs and dispositions;
- divergence/curl state;
- held set `H`;
- routed but unexecuted owner obligations.

If the same signature recurs without a new Land delta or candidate disposition, the runner must not continue silently. It must require one of:

- a valid `LoopBreak` followed by post-break reread;
- `HOLD` with the blocking condition;
- `PARTIAL` with the continuation capsule.

It must not infer `no_new_resultant` from repetition.

### 8.8 Raw-artifact custody and normalization boundary

Every cycle must preserve:

- raw Stage03 record and SHA-256;
- raw Stage04 record and SHA-256;
- raw Stage05 record and SHA-256;
- normalized structural projection;
- list of surface-only normalizations applied.

Permitted normalization includes Unicode canonicalization, line-ending normalization, and schema-compatible whitespace repair. Prohibited promotion-affecting normalization includes:

- changing STOP/no-new into held activation;
- inventing a dependency edge;
- inventing generated provenance;
- changing curl classification;
- changing divergence classification;
- deriving neutral/null diagnostics from STOP/no-new rather than the raw target-explicit records;
- inserting a terminal state not present in the raw record;
- adding an ACT body or owner activation;
- defaulting a missing state to `landed`.

`normalize_stage05_initial_burden_continuations` must be removed from the promotion path or reduced to surface-only repair. If retained for diagnostics, its output must be marked `semantic_repair_applied: true`, must preserve the raw record, and must be non-promotable.

### 8.9 `no_new_resultant` contract

New release-bearing runs require a structured object whose truth is independently derived:

```yaml
no_new_resultant:
  proposed: true
  stop_licensed: true
  checked_cycle_id: C4
  b_live: []
  unresolved_candidates: []
  deferred_preempted_candidates: []
  escape_route_checks: []
  field_state:
    divergence_records:
      - {operator: divergence, target: B_total, status: neutral, basis_refs: [field-ref-final], delta_ref: delta-final}
    curl_records:
      - {operator: curl, target: dependency-relation, status: null, basis_refs: [field-ref-final], delta_ref: delta-final}
    kappa_residual: {status: zero, scope: global, basis_refs: [field-ref-final], reopen_condition: null}
  terminal_accounting_ref: terminal-accounting-v2
  basis_refs: [field-ref-final]
```

The existing graph-completeness escape-route and field-state checks should be reused after removing their closed-world route enum, scalar diagnostic defaults, and zero-only scoped-closure assumption. A bare `true`, a prose claim, or a proof object with any live/unknown candidate must fail at Stage05 with `failure_class: mrp`. Global COMPLETE requires zero residual κ; proof-bounded residual κ may support only a scoped closure with explicit scope, basis, and reopen condition.

## 9. Existing controls to preserve and compose

Implementation must not replace working controls with a parallel system. It should extract or call them from the new lifecycle owner.

| Existing control | Preserve as | Required composition |
|---|---|---|
| Generated burden absent from Stage02 floor | B_LA/B_MRP disjointness | Apply on every append event, not only one Stage05 summary. |
| `generated_by: MRP(Bn)` | Human-readable provenance projection | Derive from `source_burden_id`; reject mismatch. |
| Dependency edge required | Burden-graph edge | Tie edge to an instantiation event and event order. |
| Terminal state required | Per-burden custody | Distinguish open `carried-RECURSE` from executed/closed. |
| Per-burden reread | Cycle exit gate | Exactly one current reread per completed ACT cycle; later cycles may reread again with distinct IDs. |
| MRP route result types | Event dispositions | Centralize spelling and transition legality in `mrp_recursion_lib.py`. |
| Graph-completeness `no_new_resultant` proof | Stop proof | Call the same predicate; do not duplicate weaker logic. |
| LoopBreak and residual-curl checks | Cycle interruption | Require post-break reread and preserve open state if residual curl remains. |
| Stage07 generated-unexecuted projection | Legacy/open custody | Continue for legacy v1; v2 promotion requires a scheduled/executed cycle or truthful open status. |

## 10. Exact edit map

### 10.1 Canonical atomics source files to edit

| File | Planned change |
|---|---|
| `atomics/skill/SKILL.md` | Add a compact non-droppable invariant: Stage05 resultant activation/instantiation returns to the burden cycle; `B_LA` stays immutable; `B_MRP` is append-only; resource exhaustion is PARTIAL. |
| `atomics/skill/references/tactics/TTP-MRP-mid-reread-pressure.md` | Define the event lifecycle, B_MRP-to-B_MRP provenance, candidate dispositions, structured no-new proof, and mandatory post-result scheduling. Remove any implication that declaration alone executes a generated burden. |
| `atomics/skill/references/diagnostics/recursive-state-transitions.md` | Define the recursive cycle state machine, repeated-state guard, resumable PARTIAL capsule, and generated-depth derivation. Remove fixed-count reasoning from saturation policy. |
| `atomics/skill/references/diagnostics/framework-pipeline.yaml` | Make the existing RECURSE edge executable-contract-bearing: name the cycle schema, scheduler owner, entry/exit conditions, and Stage06 handoff states. |
| `atomics/skill/references/rubrics/output-release.md` | Require executed provenance for any generated burden claimed landed/closed; replace the current generated-burden numeric submove minimum with complete owner-derived obligation coverage. |
| `atomics/skill/references/rubrics/non-droppable-manual-contract.md` | Add the concise B_LA/B_MRP/candidate/recursion invariants to the manual contract. |
| `atomics/skill/references/rubrics/manual-contract-digest.md` | Project the same invariants without introducing a weaker shorthand. |

### 10.2 Runtime and structural tools to edit

| File | Planned change |
|---|---|
| `tools/mrp_recursion_lib.py` | **Add.** Canonical pure lifecycle reducer, parent/depth derivation, state signature, next-target decision, event validation, and graph projection. |
| `tools/check_mrp_recursion_lifecycle.py` | **Add.** Self-test/fixture runner for the lifecycle reducer, canonical negative expectations, right-reason diagnostics, and exact positive/negative inventory. |
| `tools/run_staged_current_skill_smoke.py` | Replace the single-pass Stage03/04/05 path with the governed burden-cycle executor; preserve raw records; eliminate promotion-affecting semantic repair; derive depth and acyclicity; emit resumable open state. |
| `tools/check_staged_runtime_handshake.py` | Add v2 cycle-schema validation, cross-cycle reachability, raw/normalized custody checks, parent ordering, candidate terminality, and right-reason diagnostics. Retain v1 fixture compatibility. |
| `tools/check_mid_reread_pressure.py` | Consume canonical dispositions and validate one reread per executed cycle, including post-LoopBreak reread. |
| `tools/check_mrp_route_invariants.py` | Validate event-to-route consistency, deferred candidate liveness, and no-new terminal conditions across cycles. |
| `tools/check_mrp_generated_burden.py` | Validate append-only B_MRP, parent event, derived depth, executed ACT provenance, and B_MRP-to-B_MRP chains. |
| `tools/check_formal_reread_state_semantics.py` | Validate that formal reread state mirrors the lifecycle rather than a single summary row. |
| `tools/check_graph_completeness.py` | Import canonical burden/event graph projection; keep its stronger escape-route and no-new proof checks; remove closed-world route/result enums; derive the candidate accounting set from runtime records; retain unknown/unclassified candidates as HOLD/PARTIAL; distinguish the acyclic event/provenance DAG from the possibly cyclic pre-LoopBreak noetic dependency graph. |
| `tools/closure_witness_lib.py` | Consume complete B_total/candidate lifecycle when judging coverage; do not treat declaration or terminal-field presence as execution. |
| `tools/check_field_witness_convergence.py` | Require generated-burden body/provenance reconstruction from its actual cycle when closure is claimed. |
| `tools/check_state_capsule.py` | Include cycle cursor, live candidates, generation graph, and raw record hashes in resumable state validation; remove the fallback that treats a matching ACT/body ref as generation provenance. Only an ordered MRP instantiation event may append `B_MRP`; ACT proves later execution. |
| `tools/build_staged_governed_output.py` | Project the ordered cycle history and open/closed state without collapsing pre-empted candidates into burdens. |
| `tools/run_no_model_preflight.py` | Register the new lifecycle/checker self-tests and promotion fixtures. |

### 10.3 Generated files not to hand-edit

Do not hand-edit any path under `skill/`. The atomics tree is the owner. After source and checker tests pass, regenerate through the repository's normal build command and verify freshness.

Expected literal generated surfaces are `skill/SKILL.md`, `skill/compiled-module-map.json`, `skill/build-manifest.json`, `skill/cold-law-manifest.json`, and the runtime bundle/shard destinations named by the compiled map. The atomics modules `TTP-MRP-mid-reread-pressure`, `recursive-state-transitions`, `framework-pipeline`, and `output-release` are canonical module identities; they need not appear as same-path generated files. Verify their module IDs, source hashes, and bundle destinations through `skill/compiled-module-map.json` and freshness checkers rather than asserting nonexistent literal paths.

### 10.4 Fixtures to add

Add a focused suite under `tests/mrp-recursion-lifecycle/` with `valid/` and `invalid/` directories. Each new invalid fixture needs a `<fixture-stem>.expectation.json` sidecar using Plan A11's `daee-negative-fixture-expectation-v1`; do not invent a lifecycle-specific expectation dialect.

Valid fixtures:

1. `single-baseline-no-new.json`: one B_LA burden executes and closes; no generated candidate.
2. `held-baseline-activation.json`: B1 reread activates held B2; B2 receives its own route/ACT/MRP cycle.
3. `generated-depth-one-executed.json`: B1 instantiates B3; B3 is routed, acted, reread, and closed.
4. `generated-depth-two-executed.json`: B1 → B3 → B4 with derived depths 1 and 2.
5. `generated-held-open.json`: generated B3 is scheduled but reaches a truthful HOLD/PARTIAL terminal handoff.
6. `preempted-then-activated.json`: an eligible candidate is deferred, remains live, and later receives a cycle.
7. `candidate-non-load-bearing.json`: inspected candidate is not instantiated and has a basis-backed terminal disposition.
8. `loopbreak-post-reread-no-new.json`: repeated state triggers LoopBreak, then a post-break reread licenses no-new.
9. `capacity-topic-neutral.json`: generated fixture builder exercises parameterized breadth/depth, including representative 1, 10, and 20-burden graphs, solely as capacity samples and never as adequacy floors.
10. `legacy-v1-generated-carried-recurse.json`: retained compatibility proof for truthful open legacy records.

Invalid fixtures:

1. `generated-in-baseline-floor.json` → Stage05/MRP provenance failure.
2. `generated-parent-is-future-event.json` → parent ordering failure.
3. `generated-depth-assertion-mismatch.json` → derived-depth failure.
4. `generated-claims-landed-without-act-cycle.json` → execution-provenance failure.
5. `generated-child-without-parent-reread.json` → instantiation provenance failure.
6. `preempted-candidate-dropped.json` → live-candidate custody failure.
7. `non-load-bearing-without-basis.json` → candidate-disposition failure.
8. `no-new-with-live-candidate.json` → stop-proof failure.
9. `no-new-with-deferred-preempted.json` → stop-proof failure.
10. `loopbreak-without-post-reread.json` → recursion-state failure.
11. `repeated-signature-silently-retries.json` → cycle-guard failure.
12. `resource-budget-yields-complete.json` → open-state/closure failure.
13. `semantic-normalizer-invents-held-activation.json` → raw-custody failure.
14. `missing-terminal-defaults-to-landed.json` → unsupported-default failure.
15. `hard-coded-acyclic-true-with-cycle.json` → graph derivation failure.
16. `b-mrp-act-row-without-instantiation-event.json` → generation-provenance failure; ACT proves execution only, never generation.
17. `stop-rewrites-non-neutral-divergence.json` → diagnostic-custody failure.
18. `stop-rewrites-non-null-curl.json` → diagnostic-custody failure.
19. `unclassified-route-rejected-by-closed-enum.json` → open-world route-accounting failure.
20. `noetic-cycle-erased-to-satisfy-event-dag.json` → graph-role-conflation failure.
21. `proof-bounded-kappa-called-global-complete.json` → residual-scope failure.

Existing fixtures to retain and reclassify, not erase:

- `tests/stage-contract-workbench/stage-05-mrp-reread-terminal-state/maximal-valid/generated-burden-recurse-with-loopbreak.json` remains a valid **open v1 declaration/custody** fixture.
- `tests/stage-contract-workbench/stage-05-mrp-reread-terminal-state/minimal-valid/plain-single-burden-landed.json` remains a minimal v1 baseline.
- Existing `tests/graph-completeness/valid/generated-burden-collapse-positive.md` continues to test final graph shape, but is not an executor proof.
- Existing invalid generated-provenance and no-new fixtures remain in their current suites and should be reused by the v2 checker.

### 10.5 Documentation and scorecard surfaces

| File/surface | Planned change |
|---|---|
| `README.md` if it describes Stage01-08 | State that Stages03-05 are a data-dependent cycle and distinguish structural validation from semantic truth. |
| Existing runtime-footprint architecture/release docs discovered during implementation | Replace linear-only diagrams with the governed return edge; preserve public eight-stage naming. |
| Scorecard configuration consumed by `tools/build_model_compliance_scorecard.py` | Add separate measures for declaration custody, executable generated cycle, recursive depth projection, candidate accounting, and truthful open exits. Do not convert them into a content-length score. |
| Stage contract workbench inventory | Label fixtures by capability proved so open custody cannot be counted as executed recursion. |

## 11. TDD implementation phases

### Phase 0: Baseline custody and STOP gate

**Purpose:** prevent implementation on an unknown tree and capture current checker behavior.

Run:

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
git status --short
git rev-parse HEAD
python tools\check_staged_runtime_handshake.py
python tools\check_mid_reread_pressure.py
python tools\check_mrp_route_invariants.py
python tools\check_mrp_generated_burden.py
python tools\check_formal_reread_state_semantics.py
python tools\check_graph_completeness.py
python tools\check_field_witness_convergence.py
python tools\check_state_capsule.py --self-test
Pop-Location
```

Expected:

- `git status --short` is empty or every pre-existing change is separately inventoried and owner-approved.
- `git rev-parse HEAD` prints the intended implementation commit; if it differs from `6987c9e...`, refresh all source anchors before editing.
- Every baseline checker exits `0`. A nonzero baseline is an ANDON; preserve the output and do not attribute it to the patch.

### Phase 1: Red tests for the missing executable edge

Add the minimal valid and invalid lifecycle fixtures plus a new checker test harness. Before production changes:

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_mrp_recursion_lifecycle.py
Pop-Location
```

Expected before implementation: exit `1`, with diagnostics proving at least these failures:

- no cycle after generated instantiation;
- generated burden lacks ACT execution provenance;
- B_MRP-to-B_MRP parent rejected or unsupported;
- pre-empted candidate has no durable terminal state.

The red test is invalid if it fails only because the new schema is unknown. The diagnostic must identify the missing transition or invariant.

### Phase 2: Pure lifecycle reducer

Implement `tools/mrp_recursion_lib.py` without model invocation. Unit tests must cover event application, append-only sets, depth derivation, next-target selection, and repeated-state signatures.

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_mrp_recursion_lifecycle.py --self-test
Pop-Location
```

Expected: exit `0`, summary reports all valid fixtures accepted and all invalid fixtures rejected for their expected reason. The new checker contract must implement and document `--self-test`; the command above is part of the acceptance surface, not a placeholder.

### Phase 3: Handshake v2 validation

Teach `check_staged_runtime_handshake.py` to validate cycle arrays and preserve v1 behavior.

Positive command:

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_staged_runtime_handshake.py --records tests\mrp-recursion-lifecycle\valid\generated-depth-two-executed.json
Pop-Location
```

Expected: exit `0`; hosted-record count includes the fixture; no compatibility fixture regresses.

Right-reason negative command:

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
try {
  $raw = python tools\check_staged_runtime_handshake.py --explain-stage-failure --records tests\mrp-recursion-lifecycle\invalid\generated-claims-landed-without-act-cycle.json
  $code = $LASTEXITCODE
  $diag = $raw | ConvertFrom-Json
  if ($code -ne 1) { throw "expected exit 1, got $code" }
  if ($diag.earliest_stage -ne '05') { throw "expected earliest stage 05, got $($diag.earliest_stage)" }
  if ($diag.failure_class -ne 'mrp') { throw "expected failure class mrp, got $($diag.failure_class)" }
  if (@($diag.downstream_invalidated) -join ',' -ne '06,07,08') { throw "unexpected downstream invalidation: $(@($diag.downstream_invalidated) -join ',')" }
} finally {
  Pop-Location
}
```

Expected: the checker exit captured in `$code` is `1`, all assertions pass, and the PowerShell wrapper exits `0`; JSON diagnostic reports `earliest_stage: "05"`, `failure_class: "mrp"`, and downstream invalidation of Stages06-08. Any earlier unrelated error means the fixture is not minimal and must be repaired.

Canonical acceptance command:

```powershell
python tools\assert_expected_rejection.py --expectation tests\mrp-recursion-lifecycle\invalid\generated-claims-landed-without-act-cycle.expectation.json --artifact-root auto
```

Expected: exit `0`; the helper also proves no Stage06-08, final witness, or promotion artifact escaped the failed lifecycle boundary.

### Phase 4: Runner cycle execution

Refactor the runner so Stage03/04/05 calls are emitted per `cycle_id`. Test with a deterministic stub provider or captured stage records; do not begin with live model smokes.

Required deterministic cases:

1. no-new after one cycle;
2. held activation and second cycle;
3. one generated cycle;
4. generated child cycle;
5. resource exhaustion to PARTIAL;
6. repeated signature to LoopBreak requirement;
7. malformed raw STOP that semantic normalization previously repaired.

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_staged_runtime_handshake.py
python tools\check_mrp_recursion_lifecycle.py
Pop-Location
```

Expected: exit `0` for both. Captured runner records show an actual Stage03/04/05 sequence for each generated burden claimed executed.

### Phase 5: Projection and closure integration

Replace defaulted depth, hard-coded acyclicity, and declaration-as-execution behavior. Compose existing graph, field-witness, and capsule checks.

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\check_mid_reread_pressure.py
python tools\check_mrp_route_invariants.py
python tools\check_mrp_generated_burden.py
python tools\check_formal_reread_state_semantics.py
python tools\check_graph_completeness.py
python tools\check_field_witness_convergence.py
python tools\check_state_capsule.py --self-test
Pop-Location
```

Expected: all exit `0`. The depth-two fixture reports max generation depth `2`; a cyclic graph with hard-coded `acyclic: true` exits `1`; an unexecuted generated burden cannot project as landed or closed.

### Phase 6: Atomics, generated runtime, and freshness

Edit atomics only, then rebuild:

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\build_compiled_runtime.py
python tools\check_compiled_runtime_freshness.py
python tools\check_route_shard_selection.py
python tools\measure_load_path_budget.py --enforce-ratchet --enforce
Pop-Location
```

Expected: each exits `0`. The load-path budget must remain within its configured budget; the repair may route a recursion shard on demand but must not load the whole argument surface by default.

### Phase 7: No-model promotion suite

```powershell
$Repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Push-Location $Repo
python tools\run_no_model_preflight.py --self-test
python tools\run_no_model_preflight.py
Pop-Location
```

Expected: both exit `0`. The preflight inventory must explicitly list the recursion lifecycle checker and its positive/negative fixture counts. A pass is structural only.

### Phase 8: Five-smoke Stage01-Stage08 promotion, separately authorized

This phase is planned but not authorized by this document. Once implementation and no-model gates pass, run all five registered prompts through the same Stage01-Stage08 command surface, preserving raw and normalized artifacts:

| Smoke ID | Required recursion observation |
|---|---|
| `gate88-secularism` | No expected burden count. Record whether MRP activates held or generated routes and prove every selected route receives a cycle. |
| `gate88-khaybar` | Preserve source/provenance and chronology-related candidate custody without hard-coded topical operations. |
| `gate88-trinitarian-j173` | Permit arbitrary generated depth and owner families selected by runtime topology. |
| `gate88-tst-lillard` | Preserve earlier generated/held recoil behavior while proving actual execution or truthful open state. |
| `gate88-torah-quran-source-authentication` | Use the exact registered prompt; do not prescribe a Torah/Qur'an answer, burden count, submove count, or conclusion. Prove only topology/provenance/closure structure. |

For every smoke, Stage01 through Stage08 must pass as a single governed trace. A smoke may truthfully terminate HOLD/PARTIAL/RECURSE; that is structurally valid but does not satisfy a release criterion requiring full closure. The promotion scorecard must distinguish these outcomes.

## 12. Exact right-reason test matrix

| Case | Expected exit | Earliest stage | Failure class | Required diagnostic fragment |
|---|---:|---|---|---|
| generated burden in B_LA | 1 | 05 | `mrp` | generated target overlaps immutable baseline floor |
| generated claims landed without ACT | 1 | 05 | `mrp` | no executed cycle for generated target |
| future parent | 1 | 05 | `mrp` | parent was not instantiated before child event |
| depth mismatch | 1 | 05 | `mrp` | generation depth differs from derived parent depth |
| pre-empted candidate dropped | 1 | 05 | `mrp` | live candidate missing terminal disposition |
| no-new with live candidate | 1 | 05 | `mrp` | stop not licensed while candidate remains live |
| LoopBreak without post-reread | 1 | 05 | `mrp` | post-break reread missing |
| resource exhaustion reported COMPLETE | 1 | 07 | `public-projection` | exhausted cycle must project PARTIAL |
| hard-coded acyclic on cyclic graph | 1 | 07 | `public-projection` | derived graph contains a cycle |
| valid generated depth-two execution | 0 | none | none | two generated ACT/reread cycles and derived depth 2 |
| valid non-load-bearing candidate | 0 | none | none | candidate basis and terminal non-instantiation retained |

Expected stage/class/diagnostic IDs are encoded in `<fixture-stem>.expectation.json` under A11's canonical schema, not as brittle full-message matching.

## 13. Five-smoke evidence packet

Each smoke run must produce a manifest containing:

- exact input SHA-256;
- repo commit and dirty-state record;
- runtime artifact SHA-256 and freshness result;
- route shard selection;
- `B_LA`, `B_MRP`, and exact `B_total`;
- ordered burden cycles;
- candidate event ledger including non-instantiated candidates;
- raw and normalized Stage03/04/05 hashes per cycle;
- owner obligations and ACT body references per burden;
- per-cycle reread and terminal disposition;
- LoopBreak/post-break reread evidence if used;
- final open/closed state;
- checker command, exit code, and version;
- explicit `semantic_truth_proven: false` or equivalent boundary statement.

The fifth smoke is registered as an input fixture, not as an argument template. Its expected file may specify shape and custody requirements only.

## 14. Rollback and compatibility

### 14.1 Reversible patch sequence

1. Land the pure lifecycle library and fixtures without changing the default runner.
2. Add handshake-v2 parsing behind an explicit version field.
3. Add deterministic runner-cycle support behind a local feature flag.
4. Make v2 the promotion default only after old and new no-model suites pass.
5. Retain v1 parsing for historical artifacts and fixture replay.
6. Remove the feature flag only after five-smoke evidence and scorecard review.

### 14.2 Rollback behavior

If any phase fails:

- revert only the phase's patch, not unrelated workspace changes;
- preserve the failed fixtures and command transcript in the ANDON record;
- return the promotion path to legacy v1;
- do not relabel v1 as proving recursion;
- do not delete generated-burden evidence to make tests green;
- do not hand-edit generated runtime artifacts.

Legacy v1 remains structurally readable. It is not eligible to prove the new executable-recursion capability.

## 15. STOP/ANDON conditions and record

Stop implementation immediately when any of the following occurs:

1. The target commit or dirty state differs from the recorded baseline and ownership is unclear.
2. A baseline checker fails before edits.
3. A proposed fix requires placing a generated burden in `B_LA`.
4. A resource guard produces COMPLETE rather than PARTIAL.
5. A normalizer changes an MRP semantic outcome and the raw artifact is not preserved.
6. A generated burden is marked landed/closed without an ACT cycle.
7. A pre-empted candidate disappears without terminal disposition.
8. `no_new_resultant` passes with a live burden, held load-bearing route, or unresolved candidate.
9. A fixed burden/submove/text-size threshold is proposed as the adequacy mechanism.
10. A checker change weakens an existing invalid fixture to pass.
11. Any five-smoke test is made topic-specific in runtime code.
12. Any structural PASS is reported as semantic truth or reader uptake.

Record template:

```yaml
andon_id: DAEE-V46-MRP-RECURSION
timestamp_utc: null
repo_head: null
dirty_state_sha256: null
phase: null
command: null
exit_code: null
expected: null
observed: null
earliest_stage: null
failure_class: null
raw_artifact_refs: []
normalized_artifact_refs: []
invariant_breached: null
containment: null
owner: null
next_evidence_needed: null
regression_status: unproven
semantic_truth_proven: false
```

## 16. Definition of Done

Plan 07 is implemented only when all of the following are evidenced:

- [ ] `B_LA` remains immutable after Stage02 and `B_MRP` is append-only/disjoint.
- [ ] A Stage05-generated burden can enter a later Stage03 route and Stage04 ACT/Land cycle in the same governed Stage01-08 run.
- [ ] A B_MRP burden can generate a later B_MRP burden with derived parent/depth provenance.
- [ ] Every executed cycle has raw Stage03/04/05 custody and one current per-burden reread.
- [ ] Held activation, generated instantiation, deferred pre-emption, non-load-bearing rejection, LoopBreak, HOLD/PARTIAL, and no-new are distinct checked dispositions.
- [ ] No live pre-empted candidate can disappear or support STOP.
- [ ] Resource exhaustion yields a resumable PARTIAL capsule.
- [ ] Repeated state cannot silently loop or be called no-new.
- [ ] Missing terminal state cannot default to landed.
- [ ] Event/provenance DAG acyclicity and generation depth are derived from ordered events; pre-LoopBreak noetic dependency cycles remain represented until an evidenced LoopBreak produces the post-break relation.
- [ ] Only an ordered MRP instantiation event can append `B_MRP`; an ACT row proves execution after instantiation and can never forge generation provenance.
- [ ] The current named route/result classes remain canaries, not a closed enum; unknown/unclassified runtime candidates are retained under HOLD/PARTIAL rather than rejected or dropped.
- [ ] Semantic normalization cannot manufacture promotion evidence.
- [ ] Existing v1 fixtures remain classified truthfully and are not advertised as executor proofs.
- [ ] Every new invalid fixture fails at the intended earliest stage and stable failure class.
- [ ] Existing MRP, graph, witness, capsule, route-shard, freshness, and no-model suites pass.
- [ ] All five registered smokes traverse Stage01-08 under the same generic runtime mechanism.
- [ ] Smoke artifacts prove topology and provenance only; no structural checker claims semantic truth.
- [ ] Same-fixture v0.4.5.0/v0.4.6.0 evidence is captured before changing `regression_status` from `unproven`.

## 17. Confidence and binding decisions

**Implementation-readiness assessment: YES for authorized repo-local patch execution after A16 control-plane bootstrap; model evidence and WIP completion remain artifact/owner-gated.**

Confirmed enough to implement:

- the single-pass/generated-execution contradiction;
- the need for a canonical lifecycle reducer and executable return edge;
- the required burden/candidate provenance invariants;
- the prohibition on semantic repair as proof;
- the right-reason fixture families.

Binding implementation decisions, recorded by A16's architecture-decision ledger:

1. `DAEE-ADR-046-001`: v2 uses `burden_cycles[]` as the canonical reducer input; separately retained Stage03/04/05 records are referenced by `cycle_id` and hash.
2. `DAEE-ADR-046-002`: `tools/run_staged_current_skill_smoke.py` owns scheduling/model invocation; `tools/mrp_recursion_lib.py` is a pure transition/reducer library. A test stub may call the pure library but may not become a second scheduler.
3. `DAEE-ADR-046-003`: exact resource-policy fields/values come from hash-bound authorization/runtime configuration. No recursion-depth value is a semantic cap; exhaustion produces resumable PARTIAL/HANDOFF with live state preserved.
4. `DAEE-ADR-046-004`: handshake/capsule v1 remains legacy replay only until a separate deprecation ADR; every new release-bearing run uses composed v2.

The patch executor must validate these ADRs before editing and stop on a conflicting owner or schema. It does not reopen them by default.

Unproven until later artifacts exist:

- model compliance on all five smokes;
- comparative v0.4.5.0/v0.4.6.0 quality;
- semantic adequacy of any smoke answer.

No further conceptual research is required to prove that the current executable return edge is missing. Implementation still cannot claim model compliance, comparative quality, or semantic adequacy until the later evidence artifacts exist.
