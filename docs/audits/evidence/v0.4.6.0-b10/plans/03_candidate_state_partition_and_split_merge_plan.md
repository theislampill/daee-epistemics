# ANDON A03: Candidate-State Partition and Split/Merge Proof

Priority: P0/P1 structural-integrity fix  
Implementation target: PR #9 branch `codex/v0.4.6.0-runtime-footprint`  
Planning baseline: `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Regression status: `unproven`  
Implementation status: not started  
Plan dependency: apply after, or in the same patch series as, `02_input_pressure_inventory_and_dynamic_burden_topology_plan.md`

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Purpose

This plan prevents two different structural losses:

1. several plausible noetic-state readings of the same source material being collapsed into one selected frame without a traceable decision; and
2. several materially distinct input pressures being collapsed into one broad burden without a same-function merge proof, or one coherent pressure cluster being split into separate burdens merely because several topics or owner labels are available.

The remedy is not a larger fixed burden count. It is a typed partition decision that remains reconstructible from source observation through candidate state, pressure, burden, route, reread, and closure.

## Abnormality

The current staged contract carries a singular `selected_n_frame` and a canonical `burden_floor`. Current Stage02 checking proves that `burden_floor` is a nonempty list of canonical burden IDs. Current Stage03 checking proves set equality between that list and `route_targets`. Neither stage requires:

- an inventory of alternative candidate noetic states;
- a terminal disposition for each candidate state;
- a decision showing why two candidate states are equivalent, distinct, held, or rejected;
- a source-bound proof for merging several pressures into one burden;
- a source-bound proof for keeping a pressure cluster split across distinct burdens; or
- a cross-stage digest proving that the selected/held partition survived into state carry and closure.

The downstream graph can therefore be internally complete over a field that was aliased before the graph existed. A complete witness over an incomplete partition remains incomplete relative to the source input.

## Direct GEMBA Result

### Confirmed current pass

The current full staged record:

```text
tests/staged-runtime-handshake/valid/retained-a9-science-source.json
```

passes the current checker with:

```json
{
  "burden_floor": ["B1"],
  "selected_n_frame": "science-only-source-order-warrant",
  "live_registers": ["xi", "kappa"]
}
```

and no typed candidate-state partition or split/merge decision. That record may be semantically adequate for its own case; the defect is that the checker has no way to distinguish an adequate single-state/single-burden decision from an aliased one.

Observed baseline command:

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
python tools\check_staged_runtime_handshake.py --records tests\staged-runtime-handshake\valid\retained-a9-science-source.json
```

Observed result at the planning baseline: exit `0`, terminal `staged runtime handshake check: PASS`.

### Confirmed migration false-pass

An in-memory probe added two candidate-state rows under `topology_contract: input-pressure-v1`, one selected and one held, but supplied no candidate partition decision. `record_errors(...)` still returned an empty list because the current checker does not own those fields.

Reproduction, which performs no filesystem write:

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
$env:PYTHONPATH='tools'
@'
import copy, json
from pathlib import Path
import check_staged_runtime_handshake as c

p = Path('tests/staged-runtime-handshake/valid/retained-a9-science-source.json')
record = json.loads(p.read_text(encoding='utf-8'))
mutant = copy.deepcopy(record)
stage02 = next(s for s in mutant['stages'] if s['id'] == 'stage-02-layer-a-diagnostic-ir')
stage02['topology_contract'] = 'input-pressure-v1'
stage02['candidate_states'] = [
    {'state_id': 'N1', 'status': 'selected', 'observation_unit_ids': ['U1'], 'pressure_ids': ['P1']},
    {'state_id': 'N2', 'status': 'held', 'observation_unit_ids': ['U1'], 'pressure_ids': ['P1']}
]
errors = c.record_errors(Path('in-memory-candidate-alias-without-partition.json'), mutant)
print(json.dumps({'error_count': len(errors), 'errors': errors}, ensure_ascii=False, indent=2))
raise SystemExit(0 if not errors else 1)
'@ | python -
```

Observed result: exit `0`, `error_count: 0`.

This probe is a TDD gap demonstration. It is not evidence that the retained science fixture itself needed two candidate states.

## Evidence Classification

### Confirmed

- `diagnostic-ir.md` requires alternative reads to remain uncertainty-bearing when discourse supports multiple candidate noetic structures.
- `recursive-state-transitions.md` says the runtime must scan the noetic-structure selection space, select or hold candidate frames, and preserve residual candidate routes until integrated, discharged, held, or carried forward.
- `framework-pipeline.yaml` identifies selected/held noetic frames as live control state before route selection.
- Current Stage02 and Stage03 records do not encode a typed candidate partition or split/merge proof.
- Current Stage02 `burden_floor_details` and Stage03 `route_target_details` are optional and are not joined to a partition decision.
- The current checker accepts the migration false-pass above.
- Existing `daee-state-capsule-v1` already carries `n_frame.selected` and `n_frame.held_candidates`; this is a useful carry surface, but it does not carry partition-decision identity or proof.
- Direct object inspection found no `candidate_states`, `candidate_state_partitions`, or `burden_partition_decisions` validation in either the inherited current-main layer `c86b3c6...` or PR #9's declared base `56d023e...`. At these owner surfaces, the gap is main-inherited structural debt rather than a PR9-introduced field regression.

### Inferred

- Missing typed partition decisions can allow latent-state aliasing, same-burden overcollapse, and topic-based oversplitting.
- The reported hard-input output likely exhibited at least some overcollapse, but no source-bound topology adjudication currently proves the exact missing partition.
- Hot/cold runtime placement may amplify the risk, but this plan does not assign causality to runtime-footprint compaction.

### Unproven

- The number of candidate states or burdens any of the five smokes should produce.
- That every ambiguous phrase requires a separate candidate state.
- That every distinct source proposition requires a separate burden.
- Any claim that PR #9 newly caused the observed behavioral thinness; the inspected contract gap predates the PR head, while behavioral amplification remains unproven.
- That a structurally valid split/merge record is semantically correct.
- That v0.4.6.0 regressed relative to v0.4.5.0.

## Architectural Requirement

The design-time framework cannot know which noetic structure an arbitrary future input will instantiate. It must therefore preserve a runtime-selected partition rather than hardcode a topic route or a canonical burden count.

The relevant chain is:

```text
𝓝 ⊢ D₀
  → ⇝ Ψᴺ⟨N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩
  → IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)
  → ∇_route
  → ⁿB
  → {ⁿBᵢ[OPᵢ]}
```

This ANDON sits at three joins:

1. `D₀ → Ψᴺ`: source observations may support several candidate state reads.
2. `Ψᴺ → IR`: candidate states must be selected, held, merged with proof, or rejected with basis.
3. `IR → ∇_route → ⁿB`: input pressures must be partitioned into burdens through explicit one-to-one, keep-distinct, or same-function-merge decisions.

The later `Land`, `Δ`, `R(H,Δ)`, and closure stages must retain enough identity to reconstruct those decisions. They must not invent the original partition retrospectively.

The OSM paper contributes only a bounded engineering analogy: matching a final endpoint is weaker than preserving the ordered latent-state trajectory that produced it. It does not prove DAEE semantics, a theological conclusion, or any numeric output requirement.

## Real Five Whys

1. **Why can distinct candidate states or pressures be aliased without detection?**  
   Because Stage02 accepts one selected frame and a declared burden list without a typed partition relation back to candidate states and source-bound pressures.

2. **Why does Stage03 not catch the loss?**  
   Stage03 enforces equality with the already-declared burden floor. It checks consistency after partitioning, not the adequacy or provenance of the partition itself.

3. **Why can closure and field-witness checks still look complete?**  
   They reconstruct the surviving burden graph. A source pressure or candidate state omitted before graph construction is outside the graph they compare.

4. **Why was prose law insufficient?**  
   The runtime source says to preserve selected/held frames and apply same-function/NewB discipline, but staged records do not give those rules stable IDs, joins, terminal states, or right-reason negative fixtures.

5. **Why is the actionable root not a byte floor, topic pack, or larger canary answer?**  
   Those measures operate after the lossy decision. The first repairable owner is the Diagnostic IR and Stage02/03 producer-checker contract that creates the candidate-state and pressure-to-burden partition.

Root owner/source:

```text
atomics/skill/references/diagnostics/diagnostic-ir.md
tools/run_staged_current_skill_smoke.py (Stage02/03 producer contract)
tools/check_staged_runtime_handshake.py (Stage02/03 semantic joins)
```

Supporting owners are `recursive-state-transitions.md`, `ir-reconstruction-pass.md`, state-capsule carry, and Stage06/07 topology projection.

## Hansei

### What existing work got right

- The source formalism already distinguishes selected execution order from the whole live field.
- The source already rejects both topical oversplitting and omnibus overcollapse.
- Stage02-to-Stage03 burden-set equality prevents silent downstream burden deletion.
- The state capsule already has selected and held N-frame fields.
- Current owner and witness controls provide downstream identities to which the partition can be joined.

### What failed

- A singular selected frame became the whole machine-readable state instead of a projection from a candidate-state ledger.
- Same-function and NewB rules remained prose assertions with no decision object.
- Optional detail fields carried descriptive labels but no required relational proof.
- Canary-specific examples accumulated while the general partition operation remained under-specified.
- Internal graph completeness was allowed to stand in for source-to-graph completeness.

### Learning

The correct anti-aliasing control is not “produce more burdens.” It is “preserve every materially live alternative and pressure until a named decision changes its status.” Merge and split are operations over a source-bound field, not stylistic choices about headings.

## Target Contract

### Contract boundary

Reuse the Plan 02 contract marker:

```json
{"topology_contract": "input-pressure-v1"}
```

Do not create a competing Stage02 version name. This plan extends that contract with two required collections:

```json
{
  "candidate_state_partitions": [],
  "burden_partition_decisions": []
}
```

Legacy retained artifacts remain legacy. New release-bearing runs, new retained cases, and all five fresh completion smokes must use the extended contract after migration.

### Candidate-state record

Plan 02 supplies source-anchored `observation_units`, `candidate_states`, and `input_pressures`. Under this plan, every candidate-state record is normalized to:

```json
{
  "state_id": "N1",
  "frame_token": "bounded-kebab-case-token",
  "observation_unit_ids": ["U1", "U2"],
  "pressure_ids": ["P1"],
  "live_registers": ["xi", "kappa"],
  "read_status": "dominant | distributed | underdetermined",
  "confidence": "strong | provisional | low",
  "status": "selected | held | underdetermined | merged | rejected",
  "partition_ids": ["NP1"],
  "merged_into": null,
  "decisive_missing_differentiator": null,
  "hold_gate": null,
  "next_review_point": null,
  "basis": "source-anchored reason"
}
```

Rules:

- One current operative frame is selected only when evidence licenses it. When the field remains underdetermined, `selected_n_frame` is null, `selection_status` is `not_licensed`, and every live alternative remains `held` or `underdetermined`; the route yields HOLD/PARTIAL rather than inventing a dominant frame.
- Every non-selected candidate is `held`, `underdetermined`, `merged`, or `rejected` with a partition decision.
- `held` requires a missing differentiator, nonempty `hold_gate`, and nonempty `next_review_point`.
- `merged` requires `merged_into` and an equivalence decision.
- `rejected` requires a bounded contradiction, non-fit, or non-load-bearing basis. “Rejected because not selected” is circular and invalid.
- Identical labels do not prove identical states. Different labels do not prove distinct states.
- Candidate count is runtime-derived. One candidate is valid when one is sufficient.

### Candidate-state partition object

Candidate states are grouped by ambiguity locus rather than requiring a quadratic pair table. These groups are relation hyperedges, not a forced disjoint partition: one candidate state may participate in several groups when several ambiguity dimensions overlap.

```json
{
  "partition_id": "NP1",
  "member_state_ids": ["N1", "N2"],
  "shared_observation_unit_ids": ["U2"],
  "decision": "select_single | select_and_hold | keep_distinct | merge_equivalent | reject_nonfit",
  "selected_state_id": "N1",
  "held_state_ids": ["N2"],
  "merged_state_ids": [],
  "rejected_state_ids": [],
  "comparison": {
    "pressure_set_relation": "same | overlapping | distinct | unresolved",
    "register_relation": "same | compatible | distinct | unresolved",
    "owner_eligibility_relation": "same | compatible | distinct | unresolved",
    "held_route_relation": "same | distinct | unresolved",
    "closure_consequence_relation": "same | distinct | unresolved"
  },
  "decisive_differentiator": "what evidence would change the selection",
  "basis_unit_ids": ["U2"],
  "basis": "bounded decision explanation"
}
```

Machine validation proves set accounting and compatible field values. It does not decide whether two noetic states are truly equivalent. That decision remains part of Plan A01's hash-bound `daee-topology-review-v1` artifact (`topology-review.json`) for the five-smoke promotion lane.

`select_single` is the valid low-ambiguity case: the partition has one member, that member is selected, and the held/merged/rejected sets are empty. It prevents the contract from manufacturing alternative states merely to satisfy a shape.

The union of all `member_state_ids` must cover the candidate-state set. A candidate may occur in more than one partition group, but every group must agree with its one global `status` and `merged_into` target. A state cannot be selected in one group and merged/rejected in another, and it cannot merge into different receiving states. This preserves overlapping candidate-state geometry without permitting contradictory terminal accounting.

`merge_equivalent` is allowed only when:

- all member IDs terminate as merged except the receiving state;
- the pressure sets are equal or explicitly mapped as derivative;
- live-register and owner-eligibility effects are equal or demonstrably equivalent;
- held-route and closure consequences do not diverge; and
- no unresolved differentiator remains.

If those conditions cannot be populated, use `select_and_hold`, `keep_distinct`, or `PARTIAL`; do not merge for compactness.

### Pressure/burden partition object

Input pressures remain atomic by noetic function. If one source unit carries several functions, Stage02 creates several pressure IDs before burden routing. A single pressure ID must not be copied into several burdens as a shortcut.

```json
{
  "decision_id": "BP1",
  "candidate_state_ids": ["N1"],
  "observation_unit_ids": ["U3", "U4"],
  "pressure_ids": ["P1", "P2"],
  "decision": "one_to_one | split_distinct_functions | keep_distinct | merge_same_function | hold_unresolved",
  "pressure_to_burden": [
    {"pressure_id": "P1", "burden_id": "B1"},
    {"pressure_id": "P2", "burden_id": "B2"}
  ],
  "same_function_proof": {
    "tau_relation": "same | distinct | unresolved",
    "source_frame_relation": "same | distinct | unresolved",
    "claim_cluster_relation": "same | distinct | unresolved",
    "register_transition_relation": "compatible | distinct | unresolved",
    "owner_operation_relation": "compatible | distinct | unresolved",
    "restoration_vector_relation": "same | distinct | unresolved",
    "collapse_dependency_relation": "same | distinct | unresolved"
  },
  "residual_pressure_ids": [],
  "held_pressure_ids": [],
  "basis": "source-bound partition explanation"
}
```

Relational rules:

- `one_to_one`: one atomic pressure maps to one burden.
- `split_distinct_functions`: one source cluster yielded several atomic pressures; distinct function evidence is named; each pressure has one route or hold disposition.
- `keep_distinct`: several pressure IDs remain separate because at least one function, frame, register transition, owner operation, restoration vector, or dependency relation is distinct.
- `merge_same_function`: several pressures map to one burden only when every same-function axis is `same` or `compatible`, one burden contains distinct owner-bearing submoves as needed, and all residuals are accounted.
- `hold_unresolved`: unresolved relation blocks an unqualified merge or split; the pressures remain visible and force HOLD/PARTIAL where material.
- A multi-pressure burden without `merge_same_function` is invalid.
- A topic label, owner count, desired response length, or formatter section count is never a split or merge basis.

### Cross-stage invariants

For `input-pressure-v1` release-bearing records:

1. When `selection_status: licensed`, `selected_n_frame` equals the selected candidate state's `frame_token`; when `selection_status: not_licensed`, it is null and no candidate has status `selected`.
2. Every candidate state appears in at least one applicable partition group, may appear in several compatible groups, and has one globally consistent terminal status.
3. Every pressure from Plan 02 appears in exactly one burden-partition decision.
4. Every routed pressure maps to one `B_LA` burden, directly or through `merge_same_function`.
5. Every Stage02 `burden_floor` ID is produced by at least one partition edge.
6. Every produced burden ID appears in `burden_floor`; no partition-only ghost burden exists.
7. Stage03 `route_targets` still equals `burden_floor`; this existing control is retained.
8. Held candidate states and held pressures cannot disappear from the state capsule.
9. An unresolved material candidate/partition prevents Stage07 `COMPLETE`.
10. Stage06 carries a hash-bound topology projection so later witnesses cannot silently describe a different partition.

### State-carry projection

Do not replace the existing `n_frame.selected` and `n_frame.held_candidates`. Extend state-capsule support through an explicit versioned topology object:

```json
{
  "topology_state": {
    "contract": "input-pressure-v1",
    "selected_state_id": "N1",
    "held_state_ids": ["N2"],
    "candidate_partition_ids": ["NP1"],
    "burden_partition_ids": ["BP1"],
    "unresolved_pressure_ids": [],
    "partition_sha256": "sha256:<64 hex>"
  }
}
```

Migration decision:

- retain `daee-state-capsule-v1` fixtures for historical replay;
- contribute candidate/partition fields and fixtures to Plan A16's one shared `daee-state-capsule-v2` migration for new topology-contract runs;
- do not rewrite v1 evidence into v2;
- require v2 only for fresh five-smoke completion runs after this contract is promoted.

The capsule is a carry and replay surface. It does not prove that the model consulted every field, and it does not replace the Stage02/03 record.

## Exact Owner and Edit Map

### Canonical editable runtime source

- `atomics/skill/references/diagnostics/diagnostic-ir.md`
  - own candidate-state and pressure/burden partition objects;
  - replace prose-only selected/held handling with the version-gated record law;
  - retain uncertainty and non-claim boundaries.
- `atomics/skill/references/diagnostics/recursive-state-transitions.md`
  - bind same-function collapse and NewB rules to `burden_partition_decisions`;
  - require residual candidate routes to remain carried through `R(H,Δ)`.
- `atomics/skill/references/diagnostics/ir-reconstruction-pass.md`
  - require reconstruction of selected state, nearest held alternatives, partition decisions, and unresolved differentiator.
- `atomics/skill/references/diagnostics/framework-pipeline.yaml`
  - index candidate-state partition before route-gradient and burden partition at `IR → ∇_route → B`.
- `atomics/skill/SKILL.md`
  - add only the compact hot invariant and shard pointer;
  - do not re-inline this full data contract or add topic-specific partitions.
- `atomics/skill/references/rubrics/output-release.md`
  - block `COMPLETE` when a material held/unresolved candidate or pressure lacks a terminal carry decision.
  - remove lexical topic/alias rules that directly select a frame, owner sequence, or exact pressure labels (including named science/source-order canaries) from normative runtime law; retain those named examples only as fixtures and express runtime selection through source-anchored structural differentiators.
- `atomics/skill/references/rubrics/manual-contract-digest.md` and `atomics/skill/references/rubrics/non-droppable-manual-contract.md`
  - replace the absolute slogan `same surface never means same hidden state` with the bounded rule: `surface identity alone does not determine hidden-state identity; preserve materially licensed alternatives and disambiguate when evidence warrants`;
  - remove `OSM discipline` branding from the normative rule. The OSM paper remains a bounded design analogy about endpoint/trajectory evidence, not the authority for DAEE state selection;
  - retain concrete aliases only as local canaries/minimal pairs, never as proof that every matching surface has distinct hidden states.

### Shared validation and staged pipeline

- Add `tools/topology_partition.py`
  - pure normalization and set/join validation;
  - no topic lexicon and no theological scoring.
- Modify `tools/check_staged_runtime_handshake.py`
  - import the shared validator;
  - require it for `topology_contract: input-pressure-v1`;
  - add exact classes `candidate-state-partition` and `split-merge-proof` to first-failed-stage classification.
- Modify `tools/run_staged_current_skill_smoke.py`
  - Stage02 prompt emits candidate partitions;
  - Stage03 prompt consumes burden decisions rather than inventing route topology;
  - normalizers may canonicalize spelling/shape but must not create, merge, split, reject, or select candidate states after model output.
- Modify `tools/daee_dry_run_emulator.py`
  - carry the new fields through deterministic no-model records.
- Modify `tools/build_staged_governed_output.py`
  - consume the selected/held topology projection; do not author partition evidence during assembly.

Add paired fixtures in which identical surface wording is licensed to one state in one source context and multiple held candidates in another. Add the converse pair in which different wording resolves to one materially equivalent state under a proved merge. The expected result is evidence-sensitive partitioning, not automatic splitting by surface identity.

### State carry

- Do not add an independently owned schema. Submit candidate/partition field changes to Plan A16's single `schema/state-capsule-v2.schema.json`; historical v1 semantics remain unchanged.
- Modify `tools/check_state_capsule.py` to dispatch by capsule schema and enforce append-only candidate/partition carry.
- Modify `docs/recursive-state-capsule.md` with v1/v2 compatibility and non-claims.
- Extend `tests/state-capsule-fixtures/` with v2 selected/held retention, decision-hash parity, and candidate-loss cases.

### Fixtures

- Add `tests/topology-partition/valid/` and `tests/topology-partition/invalid/` for pure validator tests.
- Extend `tests/stage-contract-workbench/stage-02-layer-a-diagnostic-ir/` for candidate-state partitions.
- Extend `tests/stage-contract-workbench/stage-03-routing-owner-gate/` for burden partition joins.
- Extend Stage06/07 fixtures only for projection parity and false-complete rejection; do not add expected theological content.
- Add `<fixture-stem>.expectation.json` sidecars under Plan A11's `daee-negative-fixture-expectation-v1` for every new active invalid staged fixture.

### Deterministic test/CI ownership

- `tools/run_local_ci.py`
- `tools/ci_registry.json`
- `tools/run_no_model_preflight.py`

Add only deterministic checks. No live model invocation belongs in CI.

### Generated files: never hand-edit

- `skill/**`
- the generated section of `atomics/skill/references/diagnostics/framework-pipeline.md`
- generated compiled-runtime maps/manifests under `skill/`

Regenerate from canonical atomics and YAML owners.

## Fixture Lattice

### Valid candidate-state cases

1. One observation cluster, one candidate state, one pressure, one burden.
2. Two plausible states over one observation cluster; one selected, one held with a decisive missing differentiator.
3. Two labels merged as equivalent because pressure, register, owner-eligibility, held-route, and closure effects are equal.
4. Composite selected state with one held alternative; selected projection remains singular for the current burden cycle.
5. Candidate rejected on a bounded source mismatch, not merely because another was selected.
6. Two unknown-pattern-typed candidates remain underdetermined with no selected state and an explicit differentiator gate.

### Valid pressure/burden cases

1. One atomic pressure to one burden.
2. One source cluster decomposed into several distinct pressure functions and separate burdens.
3. Several pressures merged into one burden under a complete same-function proof, while preserving separate owner obligations for Plan 04.
4. Several pressures kept distinct because register transition or restoration vector differs.
5. An unresolved relation held with a gate, forcing downstream HOLD/PARTIAL.

### Invalid cases

1. Held candidate disappears without a partition object.
2. Two candidate states merge with `closure_consequence_relation: distinct`.
3. Candidate rejection basis is circular.
4. `selected_n_frame` disagrees with the selected candidate, or is non-null while selection is not licensed.
5. Pressure disappears from every partition decision.
6. Two pressures map to one burden without `merge_same_function`.
7. Merge proof contains `unresolved` on a material axis but claims pass.
8. Split basis cites topic count, expected answer sections, byte target, or owner availability alone.
9. Named target or lexical alias forces `selected_n_frame` or owner order without a partition decision.
9. Burden appears in `burden_floor` without a partition edge.
10. Partition creates a burden absent from `burden_floor`.
11. State capsule v2 shrinks held candidates or drops a decision ID between calls.
12. Stage07 claims `COMPLETE` while a material partition remains unresolved.

### Topology-capacity properties

`tools/topology_partition.py --self-test` must generate topic-neutral candidate graphs and partition hyperedges rather than rely only on hand-authored small fixtures. Representative samples may include one, three, ten, and twenty candidate states, disjoint and overlapping ambiguity loci, zero-selected underdetermined states, and mixed selected/held/underdetermined/merged/rejected outcomes. Those sample sizes are capacity probes, not required counts.

For every generated graph within the test's resource-safe range:

```text
the union of ambiguity-locus memberships covers every candidate;
overlapping memberships are accepted when global terminal status agrees;
one contradictory terminal decision causes failure;
one missing candidate membership causes failure;
one missing pressure/burden decision causes failure;
permuting unordered candidate/group rows preserves the verdict;
changing a proved relation axis from compatible to distinct invalidates merge_same_function.
```

The checker must operate over supplied IDs and relations. It must not infer candidate topology from topic words or generate a cross-product of theological answers.

## Test-Driven Patch Sequence

### Phase 0: Reconfirm baseline and drift boundary

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
git -C $repo status --short --branch --untracked-files=all
git -C $repo rev-parse HEAD
git -C $repo rev-parse origin/codex/v0.4.6.0-runtime-footprint
```

Expected: clean worktree before implementation and all heads equal `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`.

STOP if another patch has changed any owner file. Re-read and rebase this plan; do not overwrite shared work.

### Phase 1: Freeze the candidate-partition false-pass

Add these first:

```text
tests/stage-contract-workbench/stage-02-layer-a-diagnostic-ir/invalid/candidate-state-alias-without-partition-decision.json
tests/stage-contract-workbench/stage-02-layer-a-diagnostic-ir/invalid/candidate-state-alias-without-partition-decision.expectation.json
tests/stage-contract-workbench/stage-02-layer-a-diagnostic-ir/invalid/multi-pressure-one-burden-without-merge-proof.json
tests/stage-contract-workbench/stage-02-layer-a-diagnostic-ir/invalid/multi-pressure-one-burden-without-merge-proof.expectation.json
```

Before checker implementation, each payload should pass record semantics, making the fixture-suite command fail because an expected-invalid fixture unexpectedly passed. That is the red TDD state.

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
python tools\check_staged_runtime_handshake.py
```

Expected before the fix: exit `1`; diagnostic includes `expected-invalid staged handshake fixture unexpectedly passed` for the new fixtures.

### Phase 2: Implement the pure partition validator

Create `tools/topology_partition.py` and its topic-neutral fixture root. It must expose one reusable function consumed by the handshake checker and runner. Do not copy validation logic into both.

```powershell
python tools\topology_partition.py --self-test
```

Expected after implementation: exit `0`; valid fixtures pass and invalid fixtures fail for registered reasons.

### Phase 3: Integrate Stage02/03 and exact diagnostics

Expected sidecars:

```json
{
  "stage": "02",
  "failure_class": "candidate-state-partition",
  "earliest_stage": "02",
  "downstream_invalidated": ["03", "04", "05", "06", "07", "08"],
  "requires_model_rerun": false,
  "repair_lane": "no-model fixture/checker/runtime-contract repair"
}
```

and:

```json
{
  "stage": "02",
  "failure_class": "split-merge-proof",
  "earliest_stage": "02",
  "downstream_invalidated": ["03", "04", "05", "06", "07", "08"],
  "requires_model_rerun": false,
  "repair_lane": "no-model fixture/checker/runtime-contract repair"
}
```

Right-reason assertion:

```powershell
$p = 'tests\stage-contract-workbench\stage-02-layer-a-diagnostic-ir\invalid\candidate-state-alias-without-partition-decision.json'
$raw = python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $p
$code = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($code -ne 1) { throw "expected exit 1, got $code" }
if ($diag.failure_class -ne 'candidate-state-partition') { throw "wrong class: $($diag.failure_class)" }
if ($diag.earliest_stage -ne '02') { throw "wrong earliest stage: $($diag.earliest_stage)" }
```

Repeat for `multi-pressure-one-burden-without-merge-proof.json`, asserting class `split-merge-proof` and stage `02`.

Canonical acceptance commands:

```powershell
python tools\assert_expected_rejection.py --expectation tests\stage-contract-workbench\stage-02-layer-a-diagnostic-ir\invalid\candidate-state-alias-without-partition-decision.expectation.json --artifact-root auto
if ($LASTEXITCODE -ne 0) { throw 'candidate-state partition expectation failed' }
python tools\assert_expected_rejection.py --expectation tests\stage-contract-workbench\stage-02-layer-a-diagnostic-ir\invalid\multi-pressure-one-burden-without-merge-proof.expectation.json --artifact-root auto
if ($LASTEXITCODE -ne 0) { throw 'split/merge expectation failed' }
```

These commands prove the exact downstream invalidation and forbidden-artifact sets in addition to the direct stage/class assertions.

Positive record assertion:

```powershell
$p = 'tests\stage-contract-workbench\stage-02-layer-a-diagnostic-ir\maximal-valid\ambiguous-held-alternative-with-partition.json'
$raw = python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $p
$code = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($code -ne 0) { throw "expected exit 0, got $code" }
if ($diag.status -ne 'pass') { throw "expected pass, got $($diag | ConvertTo-Json -Compress)" }
```

### Phase 4: Producer contract without post-hoc repair

Update Stage02/03 instructions and normalization. Normalization may:

- canonicalize IDs;
- order sets deterministically;
- normalize Unicode/ASCII register aliases; and
- attach derived hashes.

Normalization must not:

- create an omitted candidate state;
- select a state the producer held;
- merge or split pressures;
- fabricate a basis; or
- rewrite unresolved status to pass.

Commands:

```powershell
python tools\run_staged_current_skill_smoke.py --self-test
python tools\daee_dry_run_emulator.py --self-test
python tools\check_staged_runtime_handshake.py
```

Expected: all exit `0`; the new invalid fixtures fail for their pinned reasons.

### Phase 5: State-capsule carry

Add v2 schema and replay fixtures. Assert candidate and partition sets are append-only unless a decision event explicitly changes status.

```powershell
python tools\check_state_capsule.py --self-test
```

Expected: exit `0`. The candidate-loss and partition-hash-drift fixtures must be counted as expected invalid cases.

### Phase 6: Rebuild generated surfaces

Run only after canonical atomics/YAML edits:

```powershell
python tools\build_framework_pipeline.py
python tools\check_framework_pipeline.py
python tools\build_compiled_runtime.py
python tools\check_compiled_runtime_freshness.py
python tools\check_package_shape.py
python tools\build_package_shape_inventory.py --check
```

Expected: all exit `0`; generated runtime is fresh and the default/audit package profiles remain structurally valid. The new v2 schema belongs to the audit/development package surface unless a separate owner decision changes default package policy. Review `git diff` to confirm no unrelated generated churn.

### Phase 7: Broad deterministic regression

```powershell
python tools\run_no_model_preflight.py --self-test
python tools\run_no_model_preflight.py
python tools\run_local_ci.py
```

Expected: all exit `0`. These passes prove deterministic structural integration only.

## Stage01-Stage08 Effect

| Stage | Required effect of this plan | STOP condition |
| --- | --- | --- |
| Stage01 | Preserve exact source observation anchors from Plan 02; do not select a frame yet. | Source range or digest cannot be reconstructed. |
| Stage02 | Emit candidate states, ambiguity-locus decisions, and pressure/burden partition decisions. | Candidate, pressure, or partition has no terminal accounting. |
| Stage03 | Route exactly the burdens licensed by the Stage02 partition; retain held alternatives. | Route target lacks a partition edge or invents a new burden. |
| Stage04 | Execute only owner obligations licensed by the selected burden partition. | ACT changes the partition or silently uses a held frame as operative warrant. |
| Stage05 | Reread the whole selected/held field after `Land` and carry unresolved candidate pressure. | Held alternative or residual pressure disappears at reread. |
| Stage06 | Mirror selected/held state IDs, partition IDs, and partition hash in the topology projection. | Projection differs from Stage02/03 or reconstructs only the selected path. |
| Stage07 | Block unqualified completion when a material partition remains unresolved; keep bounded HOLD/PARTIAL visible. | Public release closes over a smaller field than the carried state. |
| Stage08 | Bind structural verdict to stage records and partition hash, with semantic non-claims. | Verdict upgrades set/join validity into semantic truth. |

## Five-Smoke Implications

The required fresh cases are:

- `gate88-secularism`
- `gate88-khaybar`
- `gate88-trinitarian-j173`
- `gate88-tst-lillard`
- `gate88-torah-quran-source-authentication`

For each fresh Stage01-Stage08 run:

1. Stage01 source anchors bind exact input bytes.
2. Stage02 records candidate states and a terminal candidate partition.
3. Stage02 records pressure/burden partition decisions.
4. Stage03 routes only burdens licensed by that partition.
5. State carry retains selected and held alternatives plus partition hash.
6. Stage06/07 topology projection matches Stage02/03.
7. Plan A01's hash-bound `daee-topology-review-v1` artifact adjudicates whether material alternative states and distinct pressures were represented.

The fifth smoke stores only the exact source-authentication input and source-neutral structural records. It must not contain an expected frame, burden list, owner route, argument outline, citation stack, submove count, output byte target, or expected conclusion.

A structural PASS means the declared partition is complete and internally joined. It does not prove that the selected theological interpretation is true or that every semantic nuance was correctly diagnosed.

## Rollback

- Revert the Stage02/03 contract, shared validator, v2 capsule schema, fixtures, and producer fields as one coherent patch series.
- Rebuild generated runtime and framework-pipeline outputs from reverted sources.
- Preserve the new invalid gap fixtures in a historical evidence directory if the design is abandoned; do not delete evidence that the prior checker ignored the fields.
- Do not rewrite old retained records or v1 capsules to simulate v2 evidence.
- If the data shape proves too large for hot context, keep the compact invariant hot and move the full schema to the routed diagnostic shard; do not drop the state or replace it with a count.

## STOP / ANDON Conditions

Stop implementation if any proposed change:

- requires more than one candidate state for every input;
- sets a minimum or maximum burden count;
- uses topic words to select a prewritten partition;
- treats one sentence as one pressure or one burden by default;
- merges states because their labels sound similar;
- splits burdens because several owners, headings, or arguments are available;
- lets a held candidate disappear from state carry;
- repairs omitted topology after the producer record instead of rejecting it;
- permits `COMPLETE` with a material unresolved partition;
- claims machine validation proves semantic equivalence;
- edits generated `skill/**` directly; or
- advances `regression_status` beyond `unproven` without the Plan 01 paired evidence gate.

Required ANDON record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED
class: candidate-state-loss | split-merge-proof | partition-join | state-carry-drift | semantic-adjudication
failing_check: "python tools/check_staged_runtime_handshake.py --explain-stage-failure --records tests/stage-contract-workbench/stage-02-layer-a-diagnostic-ir/invalid/candidate-state-alias-without-partition-decision.json"
first_failed_stage: "02"
owner_source: "tools/check_staged_runtime_handshake.py::semantic_errors"
candidate_state_ids: [N1, N2]
pressure_ids: [P1]
partition_ids: [NP1]
preserved_artifacts:
  - path: tests/stage-contract-workbench/stage-02-layer-a-diagnostic-ir/invalid/candidate-state-alias-without-partition-decision.json
    sha256_source: "computed by check_topology_partition fixture manifest after Phase 1 creates the file"
next_action: "implement candidate-state partition validation, then pin the expected diagnostic sidecar"
non_claim: "structural rejection does not prove semantic truth or v46 regression causality"
```

The fixture does not exist at planning time, so the example does not invent a hash. Phase 1 must create it, compute the SHA-256, and write that concrete value into the actual ANDON record/fixture manifest before handoff.

Handoff and completion are mutually exclusive. A blocked owner decision ends in `AUDIT_HANDOFF`, not `AUDIT_COMPLETE`.

## Definition of Done

- New release-bearing Stage02 records cannot pass with candidate states but no terminal partition.
- Every candidate state is selected, held, underdetermined, merged with proof, or rejected with basis; zero selected is valid when selection is not licensed and downstream status remains HOLD/PARTIAL.
- Every input pressure belongs to one explicit pressure/burden partition decision.
- Every multi-pressure burden has a same-function merge proof.
- Distinct-function splitting is source-anchored and not topic- or count-driven.
- `selection_status`/nullable `selected_n_frame`, Stage03 routes, state capsule, and Stage06/07 topology projection reconcile.
- Material unresolved candidate states or partition axes force HOLD/PARTIAL rather than false completion.
- Right-reason invalid fixtures emit exact `candidate-state-partition` or `split-merge-proof` diagnostics.
- Existing deterministic Stage01-Stage08, capsule, framework, runtime-freshness, preflight, and local-CI checks pass.
- All five fresh smokes carry the new contract and receive a separate topology review.
- No fixed byte, burden, candidate-state, or submove floor is introduced.
- No Torah/Qur'an argument bank is introduced.
- Structural PASS remains explicitly non-semantic.
- `regression_status` remains `unproven` until Plan 01 evidence permits a different status.

## Confidence

Repo-local structural contract: **YES, implementation-ready after Plan 02 field names are accepted.**  
State-capsule v2 migration: **PARTIAL, exact compatibility tests are planned but not implemented.**  
Automated semantic split/merge correctness: **NO; requires topology adjudication.**  
Five-smoke behavioral closure: **UNPROVEN until authorized fresh runs exist.**  
v46 regression causality: **UNPROVEN.**
