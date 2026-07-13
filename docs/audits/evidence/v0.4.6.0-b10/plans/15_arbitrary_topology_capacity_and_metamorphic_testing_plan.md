# ANDON A15: Arbitrary Topology Capacity and Metamorphic Testing

Priority: P1 structural-capacity proof after the P0 topology contracts land  
Implementation target: PR #9 branch `codex/v0.4.6.0-runtime-footprint`  
Planned-head evidence boundary: `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
Regression status: `unproven`  
Plan status: phased implementation-ready; generator/core properties begin after A02-A10 plus the A11 expectation scaffold, while full package-faithful Stage01-08 properties require A12-A13  
Packet identity: this concern is A15 and is implemented by plan file `15_...`; the five-smoke matrix is A14 in file `14_...`.

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## 1. Abnormality

DAEE is designed before the input and its noetic structure are known. The runtime must therefore be able to preserve a small field, a wide field, a deep field, or a recursively generated field without a topic-specific answer bank and without a fixed burden, submove, or output-size target.

The current repository proves several useful local shapes, but it does not yet prove this end to end:

- the Stage01-Stage08 workbench fixtures are mainly small, hand-authored examples;
- the richest checked-in Stage02 fixture has two declared burdens;
- the richest checked-in Stage04 fixture has one burden and two ACT rows;
- the richest checked-in Stage05 fixture has one baseline burden and one generated burden;
- `tools/check_staged_governed_output_high_mass.py` deliberately grows one operation body with repeated byte filler and checks size/hash stability; it is an assembly stress canary, not a topology-capacity test;
- the Stage03-to-Stage04 checker proves that emitted ACT owners are eligible, but does not prove the inverse: every eligible owner obligation was executed or explicitly disposed;
- no deterministic suite varies burden count, submove count, dependency shape, split/merge decisions, recursion depth, and generated/held/pre-empted lifecycle together while asserting conservation across all stages.

This is not evidence that the JSON parser has a low cardinality ceiling. Direct GEMBA demonstrated the opposite. It is evidence that the repository lacks a repeatable proof that topology survives the complete transition chain.

## 2. Direct GEMBA and Evidence Classification

### 2.1 Confirmed current behavior

The following were inspected directly at PR9 head `6987c9e`:

- canonical editable runtime source is `atomics/skill/**`; `skill/**` is generated and must not be hand-edited;
- `tests/stage-contract-workbench/` supplies per-stage minimal, maximal, and invalid records;
- `tools/check_staged_runtime_handshake.py` is the shared structural checker;
- `tools/gen_fixture_mutations.py` provides mutation operators, but its existing sweep primarily proves that some checker rejected a mutant, not every intended property at arbitrary topology size;
- `tools/daee_dry_run_emulator.py` supplies a no-model Stage01-Stage08 route;
- `tools/check_state_capsule.py` validates compact state and replay;
- `tools/build_staged_governed_output.py` owns deterministic assembly;
- `tools/run_no_model_preflight.py` composes the current no-model stop line;
- `tools/run_local_ci.py` owns the push/PR local sequence, and `tools/ci_registry.json` classifies checkers.

Fresh deterministic replay during this planning pass also confirmed:

- `python tools\check_staged_runtime_handshake.py --records tests\stage-contract-workbench\stage-04-burden-execution-act\maximal-valid\multi-act-row-details.json` exited `0`, reporting 25 valid fixtures, 119 invalid fixtures, and one hosted record checked;
- `python tools\check_staged_governed_output_high_mass.py --sizes 100 150 200` exited `0` for its three size/hash canaries.

Those green commands establish the current checker baseline and the existing byte-assembly canary. They do not close the capacity ANDON.

An in-memory probe added a second eligible Stage03 owner, `M7`, to the current valid Stage04 workbench record while leaving Stage04 unchanged. `record_errors(...)` returned zero errors. This confirms an owner-obligation disappearance false-pass under the current contract.

The same direct probe generated declared Stage02-Stage04 structures using controlled owner/delta vocabulary. Current `record_errors(...)` accepted:

| Declared baseline burdens | ACT rows per burden | Total ACT rows | Current result | What it proves |
| ---: | ---: | ---: | --- | --- |
| 1 | 1 | 1 | zero errors | minimal declared-shape capacity |
| 10 | 3 | 30 | zero errors | wider declared-shape capacity |
| 20 | 8 | 160 | zero errors | parser/checker container capacity at Stage04 |

The 160-row case reused one controlled owner/operation with distinct burden, pressure, body-ref, and delta references. It therefore does **not** prove 160 semantically warranted operations, input-pressure completeness, Stage05 recursion, Stage06 witness parity, Stage07 public reconstruction, or Stage08 proof custody. This distinction is the reason the new suite must be property-based rather than count-based.

### 2.2 Inferred

- High-cardinality joins are more likely to expose omission, ordering, aliasing, duplicate-reference, graph, capsule, and public-projection defects than the current small examples.
- Stage05-Stage07 may have scale-sensitive defects even though Stage04 accepts a large declared structure.
- The current numeric depth guidance can reward padding or reject a legitimately compact field; topology-derived properties are the safer control.

### 2.3 Unproven

- No evidence proves that twenty burdens or eight submoves is a maximum, a minimum, or the correct shape for any named smoke.
- No evidence proves v0.4.6 introduced a capacity regression.
- No finite property suite proves semantic correctness for arbitrary natural-language inputs.
- No structural PASS proves theological truth, source accuracy, persuasion, or interlocutor uptake.

## 3. Architectural Requirement and Formal-Chain Location

The controlling chain is:

```text
N |- D0
  -> PsiN<N in N,m,tau,sigma,heart,xi,Omega,mu,kappa,H>
  -> IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)
  -> route gradient
  -> Bn
  -> {Bni[OPi]}
  -> Land(Bn)
  -> Delta Bn{heart,xi,Omega,sigma,mu}/Delta kappa
  -> div T / curl T
  -> LoopBreak(curl T)
  -> R(H,Delta,Delta kappa)
  -> C(PsiN)
  -> N_fitri and sound reason
  -> T_lang: PsiN -> PsiI
```

Capacity is not one stage. It is preservation across every arrow:

| Transition | Capacity obligation |
| --- | --- |
| `D0 -> PsiN -> IR` | Source observations, candidate states, and live pressures remain accounted at any supported cardinality. |
| `IR -> route gradient -> Bn` | Split/merge and dependency decisions preserve distinct functions without topic-keyed quotas. |
| `Bn -> {Bni[OPi]}` | Every execution obligation has an ACT body or explicit terminal disposition; no eligible owner disappears. |
| `{OPi} -> Land -> Delta` | Each operation has a unique target and state transition; repeated headings or filler do not count. |
| `Delta -> div/curl -> LoopBreak -> R` | Every landed burden receives a local reread; generated, held, and pre-empted states remain distinguishable. |
| `R -> C(PsiN)` | Closure remains false when any pressure, obligation, dependency, residual, or generated node is unpaid. |
| `C -> T_lang` | Stage06 machine state, Stage07 public body, final witness, and Stage08 custody project the same topology. |

The North Star requirement is not “always emit many nodes.” It is “do not constrain or silently collapse the runtime-selected field because the designer guessed the future input.”

## 4. Five Whys

1. **Why is arbitrary topology not demonstrated?**  
   Because the checked-in examples exercise only a few hand-selected shapes, while the large-output canary increases bytes around one small topology.

2. **Why do those tests not expose topology loss?**  
   They validate each declared record locally. They do not systematically vary graph dimensions and then assert conservation of the same obligations across every downstream stage.

3. **Why is there no systematic variation?**  
   Fixture construction is primarily hand-authored and example-based. There is no canonical topic-neutral topology-spec generator or metamorphic oracle.

4. **Why is a generator alone insufficient?**  
   A generator can manufacture a large self-consistent record that merely repeats labels. Without invariants over source pressures, owner obligations, lifecycle classes, graph edges, body references, and public projection, it becomes another padding engine.

5. **Why did example-only coverage remain the release evidence?**  
   No owner or CI contract required a topic-neutral topology generator plus conservation oracle, so hand-authored smoke fixtures and byte-oriented canaries remained the cheapest available evidence and were never displaced by property-level coverage.

Severity: unknown-at-design-time topology is an architectural invariant. It must be enforced by reusable stage contracts and property tests, not by expected answers for secularism, Khaybar, J173, TST, or Torah/Qur'an source authentication.

Actionable root owner: the stage-contract test infrastructure and the canonical cross-stage validators. The first edit owners are `tools/check_staged_runtime_handshake.py`, a new topology-property library/checker, and generated topic-neutral fixtures. The root owner is not output byte limits and not a theological case library.

## 5. Hansei

### What the repository already does well

- It separates canonical source from generated runtime.
- It has explicit Stage01-Stage08 records, first-failure classification, positive/negative fixtures, state-capsule replay, and a no-model preflight.
- It already rejects many malformed ACT rows, generated-burden provenance errors, false complete states, path traversal, and witness inconsistencies.
- It explicitly labels the high-mass canary as byte filler and disclaims semantic/release proof.

### What planning and testing got wrong

- Prior proposals sometimes used 4+ burdens, 3-5 submoves, 30 KB, or 90-150 KB as if these could stand in for topology fidelity.
- A large file was treated as a possible proxy for a large governed field.
- “Can parse many rows” and “can preserve a warranted field through Stage08” were conflated.
- Small fixtures allowed omission defects to hide behind internal consistency.
- Mutation success was sometimes counted when any downstream checker failed, without proving the intended earliest stage and failure class.

### Corrective lesson

Use cardinalities as **capacity probes**, never as policy. The oracle is conservation of runtime-derived obligations and reconstructibility under transformations. A finite probe set is a canary for implementation boundaries, not a declaration that future inputs fit within those numbers.

## 6. Existing Controls to Reuse

The implementation must compose, not replace, these controls:

- `tools/check_staged_runtime_handshake.py`: canonical record and cross-stage structural validation;
- `tests/stage-contract-workbench/`: stage-local fixture taxonomy;
- `tools/gen_fixture_mutations.py`: mutation mechanism, after right-reason assertions are enforced;
- `tools/daee_dry_run_emulator.py`: no-model end-to-end execution;
- `tools/check_state_capsule.py`: compact state/replay validation;
- `tools/build_staged_governed_output.py`: deterministic release assembly;
- `tools/check_public_burden_grouping.py`, `check_owner_activation_ordering.py`, `check_mid_reread_pressure.py`, `check_mrp_generated_burden.py`, `check_field_witness_convergence.py`, `check_graph_completeness.py`, and `check_manual_smoke_render_contract.py`: output-facing checks where their CLI accepts generated artifacts;
- `tools/run_no_model_preflight.py`: pre-model stop line;
- `tools/run_local_ci.py` and `tools/ci_registry.json`: required local/CI wiring.

`tools/check_staged_governed_output_high_mass.py` remains useful for assembly size and hash stability. It must remain separately named and must never be cited as topology-capacity proof.

## 7. Target Property-Test Architecture

### 7.1 One declarative topology spec, ephemeral generated records

Add a topic-neutral spec format owned by `tests/topology-capacity/specs/`. A spec describes graph dimensions and lifecycle states, not a theological answer:

```json
{
  "schema": "daee-topology-capacity-spec-v1",
  "case_id": "capacity-chain-b10-s3",
  "seed": 104603,
  "dimensions": {
    "candidate_states": 2,
    "baseline_burdens": 10,
    "submoves_by_burden": {"default": 3},
    "held_baseline_burdens": 1,
    "generated_burdens": 2,
    "generation_depth": 2,
    "preempted_candidates": 1,
    "route_candidate_kinds": ["held_activation", "synthetic-unclassified-x"]
  },
  "dependency_shape": "chain",
  "terminal_policy": "partial-until-all-generated-land",
  "expected_relation": "valid"
}
```

The numbers above belong only to that probe. The schema permits any positive cardinality supported by available memory/time, and it does not define a maximum. `generation_depth` is a generated-case dimension, not a runtime recursion cap.

Generated Stage01-Stage08 records and output fragments must be written to a temporary directory by default. Do not commit hundreds of expanded JSON files. Commit only:

- compact specs;
- expected property manifests;
- a few minimized current false-pass fixtures;
- stable seeds;
- checker code and docs.

### 7.2 Stable dimension manifest

Each generated case emits `topology-dimensions.json` containing:

- source observation IDs;
- candidate state IDs and dispositions;
- baseline burden IDs;
- pressure-to-burden joins;
- split/merge decision IDs;
- owner-operation obligation IDs;
- ACT body refs;
- held ACT obligations;
- generated burden IDs with parent/depth;
- pre-empted candidate IDs and non-instantiation basis;
- event/provenance edges and normalized event order;
- pre-LoopBreak and post-LoopBreak noetic dependency edges, plus the evidenced interruption operation;
- route candidate kinds, including unknown/unclassified kinds and their open dispositions;
- per-burden reread IDs;
- Stage06 NAR rows;
- Stage07 visible operation/witness refs;
- Stage08 sidecar references;
- terminal state and closure claim.

Every later stage is compared to this manifest by set and relation, not by file size. The manifest itself is generated from the topology spec and independently re-derived from the produced records before comparison. The generator's expected object and the checker-extracted actual object must use separate functions so one shared bug cannot trivially self-certify.

### 7.3 Probe matrix

The mandatory baseline probe set is:

| Axis | Probe values | Meaning |
| --- | --- | --- |
| Baseline burdens | 1, 10, 20 | small, wide, wider capacity canaries |
| Submoves in a selected burden | 1, 3, 6, 8 | shallow to deeper owner-operation canaries |
| Candidate states | 1, 2, 4 | selected-only and selected/held/merged/rejected accounting |
| Generated depth | 0, 1, 3 | no generation, one post-Land resultant, deeper finite recursion |
| Held burdens | 0, 1, several | explicit hold and later activation behavior |
| Pre-empted candidates | 0, 1, several | visible non-instantiation without false graph nodes |
| Route-kind universe | known canaries; known plus synthetic unknown | prove open-world accounting and HOLD/PARTIAL for unclassified runtime states |

The suite need not execute the full Cartesian product on every CI run. Define:

- a **required pairwise set** under two minutes for local CI;
- a **full deterministic matrix** for no-model preflight or a scheduled/manual-slow lane;
- an **exact-dimension replay mode** that accepts a captured smoke's dimension manifest.

No checker may fail simply because a valid case has 21 burdens or 9 submoves. If a fresh run exceeds the standing probes, replay that exact shape and add a new capacity canary only when it exposes an implementation boundary. Do not convert the new observed value into a ceiling.

### 7.4 Dependency shapes

Generate at least these graph families:

1. independent roots;
2. a linear prerequisite chain;
3. fan-out from one upstream burden;
4. fan-in from several prerequisites;
5. a diamond with one shared downstream burden;
6. mixed independent and dependent components;
7. held baseline burden activated after an upstream Land/reread;
8. generated child chain with strictly increasing generation depth;
9. generated fan-out from one landed parent;
10. a cyclic noetic dependency relation preserved as diagnosed curl, followed by an explicit LoopBreak transition and a separately recorded post-break relation;
11. an invalid cycle in the ordered event/provenance DAG, which always fails because an event cannot depend on its own future occurrence.

Generated parent edges must increase generation depth. A pre-empted candidate remains in the decision ledger but does not become a graph node. A held baseline burden remains in `B_LA`; activation does not reclassify it as generated.

## 8. Required Properties

### P1. Source-pressure conservation

Every source observation has a pressure or explicit non-pressure disposition. Every pressure is routed, merged with proof, held, non-load-bearing, or unresolved. Adding cardinality must not create unaccounted input units.

### P2. Candidate-state terminal accounting

Every candidate noetic state is selected, held, merged with a named decision, or rejected with basis. No candidate vanishes when records are scaled or permuted.

### P3. Split/merge conservation

A merge preserves every incoming pressure ID and names the receiving burden. A split preserves the parent pressure and creates distinct owner/register obligations. The reverse transformation is valid only with the canonical same-function/source-frame/restoration-vector proof.

### P4. Owner-obligation conservation

For every Stage03 executable owner-operation obligation there is exactly one of:

- a Stage04 ACT body;
- an explicit duplicate-of obligation;
- a contingent or optional-non-load-bearing disposition;
- HOLD/PARTIAL with gate and next action.

The current one-way check, `emitted owner is eligible`, remains. Add the inverse coverage check. Removing one eligible owner from Stage04 must fail at Stage04 for the owner-coverage class, not later as witness noise.

### P5. Operation body identity without padding

Every generated ACT body has a unique obligation ID, target pressure ID, owner/operation, before-state, performed operation evidence, delta, residual, and contribution to `Land(B)`. Repeated prose, repeated headings, or repeated byte filler cannot create new obligations. Do not require a minimum character count.

### P6. Burden-local completeness

Each burden's submove set is derived from its obligation set. One burden may have one, three, six, eight, or another runtime-derived count. A same-owner operation on different pressures remains separately traceable; duplicate operations on the same target require an explicit duplicate/merge disposition.

### P7. Lifecycle partition

`B_LA` and `B_MRP` are disjoint. Their union equals the total instantiated burden set. Held baseline burdens remain baseline. Generated burdens have post-Land parent provenance. Pre-empted resultants remain visible as candidates but are absent from the instantiated union.

### P8. Recursion and terminal coverage

Every instantiated burden has terminal state, every landed burden has a local reread, and every generated child is executed, held, partial, or recursed with a next action. Closure is false while any generated or held executable obligation remains live.

### P9. Dependency integrity

All edge endpoints exist; generated-parent edges agree with provenance and depth; normalized event ordering respects prerequisites; independent-node permutation does not change graph meaning. The event/provenance DAG must be acyclic. A noetic dependency cycle must not be erased to satisfy that DAG; it remains in the pre-LoopBreak relation with target-explicit curl evidence until an explicit interruption produces the post-break relation.

### P9a. Open-world route accounting

The current named route/result classes are regression canaries, not an exhaustive enum. Adding a synthetic unknown candidate kind must preserve it and yield HOLD/PARTIAL with a differentiator/next action; it must not fail merely because it is a ninth class, disappear, or be coerced into a known class.

### P10. Stage06 exact parity

Stage06 field-witness refs, owner activation details, NAR rows, terminal burdens, register deltas, and generated/held states exactly cover Stage02-Stage05 obligations. Boolean NAR is not sufficient for release-bearing capacity fixtures.

### P11. Stage07 projection parity

The public ACT rows, operation bodies, Land/reread blocks, terminal states, closure claim, and final witness are re-derived and matched against Stage06. A large internal graph with a one-burden public projection fails.

### P12. Stage08 custody boundary

Sidecars bind to the exact output and stage record hashes. PASS means the structural suite accepted that generated artifact; it does not certify semantic truth or arbitrary-input behavior.

### P13. Bounded resource behavior

Record size, checker runtime, capsule size, and assembly memory are measured and reported, but no fixed output-byte floor is a correctness condition. Resource limits produce HOLD/PARTIAL or a clearly classified infrastructure/capacity ANDON; they do not silently prune nodes.

## 9. Metamorphic Relations

Each base spec must generate transformed siblings with expected invariants:

| Transformation | Expected invariant |
| --- | --- |
| Alpha-rename burden, pressure, state, and body-ref IDs consistently | Same validity, graph isomorphism, terminal distribution, and closure status. |
| Permute independent burdens | Same set-level topology and normalized topological order; public order may normalize but nothing disappears. |
| Add explicitly non-load-bearing context | Observation/disposition count changes; burden and ACT obligation sets do not. |
| Duplicate an observation with a proved duplicate/merge decision | Pressure lineage grows; instantiated burden count need not grow. |
| Split one pressure into two owner/register obligations | Submove set grows exactly by the new explicit obligation; all joins remain reconstructible. |
| Remove the split proof while keeping two obligations | Right-reason failure at Stage02/03. |
| Remove one Stage03 owner's Stage04 ACT/disposition | Right-reason failure at Stage04. |
| Convert an ACT obligation to HOLD with a valid gate | Structural validity may remain; closure becomes non-complete. |
| Instantiate a post-Land generated child | Child appears only in `B_MRP`, parent edge/depth/reread update, closure remains false until terminal. |
| Mark a candidate resultant pre-empted | Candidate remains in decision evidence, no instantiated graph node appears. |
| Delete one Stage05 reread | Failure at Stage05 before Stage06/07 noise. |
| Delete one Stage06 NAR row or owner activation | Failure at Stage06. |
| Project only a prefix of a valid large topology into Stage07 | Failure at Stage07 public-projection parity. |
| Append irrelevant filler bytes | No new obligation or topology credit; semantic/non-padding review unchanged. |
| Increase a probe from 20 to 21 burdens | No policy failure based on count; only real join/resource defects may fail. |

Every negative transformation records expected earliest stage, failure class, and invalidated downstream stages. A nonzero exit for an unrelated reason is not a passing mutation test.

## 10. Exact Edit Map

### Add

- `tools/topology_capacity_lib.py`  
  Pure spec parsing, deterministic ID generation, graph construction, and expected-dimension derivation.
- `tools/generate_topology_capacity_cases.py`  
  CLI that emits Stage01-Stage08 records/artifacts to a temporary or explicitly supplied directory.
- `tools/check_topology_capacity_properties.py`  
  Independent actual-record extraction, property checks, metamorphic runner, exact-dimension replay, and machine diagnostics.
- `schema/topology-capacity-spec.schema.json`  
  Spec shape only; it must not duplicate the Stage01-Stage08 runtime schema.
- `tests/topology-capacity/probe-set.json`  
  Required pairwise probe matrix and stable seeds.
- `tests/topology-capacity/specs/valid/`  
  Compact specs for independent, chain, fan-out, fan-in, diamond, mixed, held activation, generated recursion, and pre-emption.
- `tests/topology-capacity/specs/invalid/`  
  Specs or mutations with expected earliest-stage diagnostics.
- `tests/topology-capacity/current-false-pass/eligible-owner-unexecuted.json`  
  Minimized current Stage03-to-Stage04 omission specimen.
- `docs/topology-capacity-property-suite.md`  
  Evidence boundaries, probe meanings, exact commands, extension policy, and non-claims.

### Modify only as required by the canonical contracts

- `tools/check_staged_runtime_handshake.py`  
  Add missing cross-stage inverse/coverage properties; do not embed probe counts.
- `tools/gen_fixture_mutations.py`  
  Make expected earliest stage and failure class enforcing, then add topology-loss mutations.
- `tools/daee_dry_run_emulator.py`  
  Accept an optional generated topology case and preserve all dimensions through Stage08.
- `tools/run_no_model_preflight.py`  
  Add a named topology-property gate after the stage handshake and mutation gates; do not call it a new fixed “17-gate” contract in docs.
- `tools/run_local_ci.py`  
  Add the fast pairwise property command.
- `tools/ci_registry.json`  
  Register `check_topology_capacity_properties.py` as `required` only after runtime is acceptable on Windows/Linux; otherwise begin `manual-slow` with owner adjudication and promote later.
- `tests/stage-contract-workbench/README.md` and `docs/stage-contract-workbench.md`  
  Point to the property suite and distinguish example fixtures from arbitrary-topology evidence.
- `docs/non-claims.md`  
  State that finite capacity probes do not prove universal semantic behavior or an upper bound.

### Canonical runtime sources consumed, not independently redesigned here

- `atomics/skill/references/diagnostics/diagnostic-ir.md`
- `atomics/skill/references/diagnostics/recursive-state-transitions.md`
- `atomics/skill/references/tactics/TTP-MRP-mid-reread-pressure.md`
- `atomics/skill/references/rubrics/output-release.md`
- `atomics/skill/SKILL.md`

Those files are edited by Plans A02-A10 when the property suite exposes a missing runtime law. Plan A15 must not create a parallel topology contract inside test code.

### Generated files not to hand-edit

- `skill/SKILL.md`
- `skill/build-manifest.json`
- `skill/compiled-module-map.json`
- generated framework/docs surfaces

After any canonical atomics change, rebuild through the owner tools and verify freshness.

## 11. Test-Driven Implementation Sequence

All commands use PowerShell from the PR9 repository root.

### Phase 0: Reassert the planning baseline

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
git status --short --branch --untracked-files=all
git rev-parse HEAD
python tools\check_staged_runtime_handshake.py --records tests\stage-contract-workbench\stage-04-burden-execution-act\maximal-valid\multi-act-row-details.json
python tools\check_staged_governed_output_high_mass.py --sizes 100 150 200
```

Expected at the recorded baseline:

- clean branch at `6987c9e...`;
- Stage04 fixture exits `0`;
- high-mass assembly canary exits `0` and reports only size/hash canary success;
- neither command is described as arbitrary-topology proof.

STOP if the branch or fixture behavior has drifted. Refresh the plan before editing.

### Phase 1: Freeze the owner-disappearance false-pass

1. Add the minimized record under `current-false-pass/`.
2. Confirm the current checker exits `0` before the fix.
3. Add the expected Stage04 `owner-obligation-coverage` diagnostic.
4. Patch the shared owner-coverage validator.
5. Confirm the same record exits `1` for the right reason.

Target negative command after implementation:

```powershell
$p = 'tests\topology-capacity\current-false-pass\eligible-owner-unexecuted.json'
$raw = python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $p
$exit = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($exit -ne 1) { throw "expected exit 1, got $exit" }
if ($diag.earliest_stage -ne '04') { throw "wrong earliest stage: $($diag.earliest_stage)" }
if ($diag.failure_class -ne 'owner-obligation-coverage') { throw "wrong class: $($diag.failure_class)" }
```

The patch must add that exact class to the checker's controlled failure taxonomy and pin it in a Plan A11 `<fixture-stem>.expectation.json` sidecar.

```powershell
python tools\assert_expected_rejection.py --expectation tests\topology-capacity\current-false-pass\eligible-owner-unexecuted.expectation.json --artifact-root auto
```

Expected: exit `0`; the capacity canary fails for owner-obligation loss, not its large/small cardinality.

### Phase 2: Test-drive the spec and generator

Write schema and generator tests before generation logic:

- same seed/spec produces byte-identical records and dimension manifest;
- different stable seeds change IDs/order only where allowed;
- zero/negative cardinalities fail spec validation;
- an arbitrary positive cardinality is accepted when resources permit;
- generated records contain no topic labels, named smoke IDs, citations, conclusions, or stock answer prose;
- output directory must be absent or explicitly replaceable only in a temporary test lane;
- default self-test leaves no repository files.

Target commands:

```powershell
python tools\generate_topology_capacity_cases.py --self-test
python tools\generate_topology_capacity_cases.py --spec tests\topology-capacity\specs\valid\chain-b10-s3.json --check-only
```

Expected: exit `0`; no tracked or untracked file appears in the repository.

### Phase 3: Implement Stage01-Stage04 conservation properties

Add source-pressure, candidate-state, split/merge, burden, owner-obligation, body-ref, and operation-capsule checks. Run the pairwise suite:

```powershell
python tools\check_topology_capacity_properties.py --self-test
python tools\check_topology_capacity_properties.py --probe-set tests\topology-capacity\probe-set.json --through-stage stage-04-burden-execution-act
```

Expected: exit `0`; report includes probes with 1/10/20 burdens and 1/3/6/8 submoves, with no minimum/maximum language.

### Phase 4: Add Stage05 recursion and lifecycle properties

Generate baseline-held activation, generated chains, generated fan-out, pre-empted resultants, no-new-resultant, HOLD/PARTIAL, known and unknown route kinds, pre/post-LoopBreak noetic dependency relations, and invalid event-DAG cycles.

```powershell
python tools\check_topology_capacity_properties.py --probe-set tests\topology-capacity\probe-set.json --through-stage stage-05-mrp-reread-terminal-state
```

Expected: exit `0`; every instantiated burden has a terminal state and reread, generated depth is consistent, pre-empted candidates are not graph nodes, unknown route kinds remain open and visible, noetic cycles survive until LoopBreak, and event-DAG cycles fail for the right reason.

Right-reason deletion check:

```powershell
$raw = python tools\check_topology_capacity_properties.py --explain-case tests\topology-capacity\specs\invalid\generated-child-missing-reread.json
$exit = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($exit -ne 1) { throw "expected exit 1, got $exit" }
if ($diag.earliest_stage -ne '05') { throw "wrong earliest stage" }
if ($diag.failure_class -ne 'reread-terminal-coverage') { throw "wrong failure class" }
```

```powershell
python tools\assert_expected_rejection.py --expectation tests\topology-capacity\specs\invalid\generated-child-missing-reread.expectation.json --artifact-root auto
```

Expected: exit `0`; the generated-child deletion fails first at Stage05 and cannot emit Stage06-08 or promotion evidence.

### Phase 5: Add Stage06-Stage08 projection properties

Generate structured NAR, public operation bodies, final witness, and ephemeral sidecar-bound outputs. Do not use boolean NAR in release-bearing probes.

```powershell
python tools\check_topology_capacity_properties.py --probe-set tests\topology-capacity\probe-set.json --through-stage stage-08-verifier-sidecars
python tools\daee_dry_run_emulator.py --self-test
```

Expected: exit `0`; the checker reports exact Stage02-Stage08 parity by IDs/edges/states. It must not report semantic truth.

### Phase 6: Metamorphic and mutation sweep

```powershell
python tools\check_topology_capacity_properties.py --metamorphic --probe-set tests\topology-capacity\probe-set.json
python tools\gen_fixture_mutations.py --self-test
```

Expected: exit `0`; every negative mutation is rejected at its pinned earliest stage and class. A failure for an unrelated later checker fails the mutation suite.

### Phase 7: Resource and no-padding review

The property checker emits a JSON report with generation time, validation time, peak measured process memory where available, record bytes, and dimension counts. These are measurements, not correctness floors.

```powershell
python tools\check_topology_capacity_properties.py --full-matrix --json .daee\topology-capacity\full-matrix.json
python tools\check_staged_governed_output_high_mass.py --sizes 100 150 200
```

Expected: both exit `0`, but their verdicts remain separate:

- topology property PASS;
- byte/hash assembly canary PASS.

No combined “mass PASS” may be inferred.

### Phase 8: Full deterministic gates

```powershell
python tools\build_framework_pipeline.py
python tools\build_compiled_runtime.py
python tools\check_compiled_runtime_freshness.py
python tools\run_local_ci.py --strict-pwsh
python tools\run_no_model_preflight.py --self-test
python tools\run_no_model_preflight.py
git diff --check
```

Expected after the control-plane rename: all exit `0`; the preflight ends with `PREFLIGHT_GREEN_AWAITING_OWNER_AUTHORIZATION`. That token reports deterministic readiness for an owner decision. It is not authorization, a model-smoke result, or a release verdict.

## 12. Five-Smoke Implications

The five required cases are:

- `gate88-secularism`;
- `gate88-khaybar`;
- `gate88-trinitarian-j173`;
- `gate88-tst-lillard`;
- `gate88-torah-quran-source-authentication`.

This plan does not define their expected burdens, submoves, dependencies, citations, word count, or conclusions. For each fresh run:

1. extract its actual dimension manifest after Stage08;
2. run `check_topology_capacity_properties.py --replay-run` against the retained run directory so the checker independently locates its records, output, and `topology-dimensions.json`;
3. require every ID/relation to reconstruct across the eight stages;
4. perform the separate human topology review from Plan A02;
5. preserve structural and semantic-review verdicts separately.

If a smoke requires a shape outside the standing 1/10/20 or 1/3/6/8 probes, the smoke is not invalid for exceeding the canaries. Add an exact-dimension no-model reproduction and determine whether a real implementation/resource boundary exists. Never round the field down to the nearest fixture.

The fifth prompt is a test input only. The property suite must not contain “Torah,” “Qur'an,” expected corruption arguments, manuscript conclusions, or a preselected route. A topic-word scan over generator/spec files is a required anti-hardcoding test.

Exact per-run replay form after implementation:

```powershell
$run = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch\.daee\staged-row-family-smokes\authorized-cycle\gate88-secularism'
if (-not (Test-Path -LiteralPath $run -PathType Container)) { throw "run directory is absent: $run" }
python tools\check_topology_capacity_properties.py --replay-run $run
if ($LASTEXITCODE -ne 0) { throw "topology replay failed: $run" }
```

`authorized-cycle` is an illustrative custody directory name, not a claimed run. The final matrix procedure in Plan A14 supplies the actual cycle path programmatically.

### 12.1 No-model maturity and model-smoke escape role

This property suite is a P0 economic control as well as a topology control. The
owner reports that predecessor four-smoke campaigns sometimes consumed dozens of
full model invocations to expose small failures. A full five-case model cycle
must therefore be a behavioral integration observation after deterministic
maturity, not the routine way to discover cardinality, relation, lifecycle,
recursion, projection, or custody defects.

Plan A16 may issue `NO_MODEL_CANDIDATE_MATURE` only when the exact candidate's
A15 report proves all required probe families and every closed A11
`MODEL_SMOKE_ESCAPE` canary that belongs to topology. An open deterministically
detectable or unknown escape blocks another paid cycle. The maturity artifact
binds the topology-spec/generator/checker hashes, seeds, dimension manifests,
mutation reports, command exits, source commit, generated runtime, and package
record. It is not reusable after any bound byte changes.

An A11 row classified `deterministic_detectability=NO` does not compel A15 to
invent a universal topology oracle. The row records the missing observable and
the strongest valid structural pressure/owner/body/provenance signal. New A15
capability, recurrence, or pattern evidence may emit `REASSESSMENT_DUE`, but it
does not automatically change the classification. An accountable owner and an
independent reviewer must adjudicate whether materially new, topic-neutral
evidence justifies temporary `UNKNOWN`; the named question then resolves to a
CI-wired `YES` canary or renewed scoped `NO`. This preserves unknown-at-design-
time topology instead of converting a human semantic omission into a canned
burden expectation.

For a legitimate `NO`, A15 still supplies the strongest topic-neutral
observability canary available and joins it to the owner-source countermeasure,
Smoke A/B, integrated preflight, and independent concurrence required by Plans
A11/A21 before another paid cycle. Structural observability is compensating
evidence, not proof of the semantic proposition the model must still execute.

When a model smoke first reveals a topology defect, minimize its structural
shape without importing its theology or answer. The permanent canary must then:

1. reproduce the lost or false relation on the pre-fix boundary;
2. pass on the repaired candidate and preserve a neighboring valid control;
3. rename pressure/burden/submove IDs and still detect the relation;
4. permute declaration order where order is non-semantic;
5. replace prose with neutral payload text of different lengths;
6. add irrelevant source text without changing the expected topology result;
7. vary cardinality around the minimized shape rather than pinning the observed
   smoke's exact count as a universal rule;
8. fail if the repaired owner edge, lifecycle event, recursion return, projection
   join, or witness provenance is removed.

These transformations distinguish a real topology oracle from a memorized
fixture. Named smoke IDs and topic words are taint inputs: changing them must not
change the property verdict, and their presence in route logic or expected
topology blocks maturity.

Campaign telemetry records how many proposed model cycles were actually blocked
by A15 and which defect classes were found. It may report an invocation as
avoided only when a scheduled/authorized next call was prevented before dispatch
by this exact deterministic failure. Otherwise savings remain `unknown`. The
target is reduced repeat paid discovery, never reduced topology or review depth.

## 13. Rollback

- Revert the property checker, generator, specs, CI/preflight wiring, and docs as one coherent patch if the design is abandoned.
- If a canonical Stage contract change is reverted, rebuild `skill/**` from atomics and re-run freshness; never hand-edit generated files.
- Preserve minimized false-pass fixtures and property reports as historical evidence, clearly marked for the superseded contract.
- Do not remove an invalid fixture merely because it is expensive or exposes an unresolved defect; move the full matrix to `manual-slow` only with recorded owner approval and retain the fast minimized form in required CI.
- Never “fix” a resource failure by silently dropping burdens, submoves, edges, or generated states.

## 14. STOP / ANDON Conditions

Stop the implementation or promotion lane if:

- a checker introduces a universal burden, submove, recursion, or byte floor;
- the generator includes named-topic routes, expected answers, citations, or conclusions;
- a large case passes only because rows or prose are repeated without distinct obligations;
- Stage03 eligible owners can still disappear without ACT/disposition;
- a generated burden enters `B_LA` or a held baseline burden enters `B_MRP`;
- a pre-empted candidate becomes a graph node without instantiation;
- a property mutation is counted as rejected for the wrong stage/class;
- Stage06/07 cardinalities differ while Stage08 passes;
- a finite probe is described as proof of unbounded semantic correctness;
- the suite exceeds practical CI resources and the response is to prune topology rather than classify/move the full probe;
- a known topology `MODEL_SMOKE_ESCAPE` remains `YES` or `UNKNOWN` while another
  paid five-case cycle is authorized;
- an escape canary passes only with the original case name, topic words, IDs,
  row order, payload length, or exact observed cardinality;
- an invocation is counted as avoided without a documented pre-dispatch block;
- a model smoke, package, commit, issue, tag, release, or publication is attempted without separate authorization.

Required terminal record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED | DEFERRED
andon_id: A15
class: topology-loss | owner-obligation-loss | lifecycle-alias | projection-mismatch | resource-boundary | wrong-reason-rejection
probe_spec: tests/topology-capacity/specs/<exact-file>.json
seed: <integer from the spec>
dimensions: <exact topology-dimensions.json path and hash>
failing_command: <exact command>
exit_code: <integer>
earliest_stage: <stage-01 through stage-08 or infrastructure>
failure_class: <controlled diagnostic>
owner_source: <file/function/schema>
preserved_artifacts: <paths and hashes>
next_action: <one concrete patch, decision, or evidence request>
regression_status: unproven
```

The implementation must replace angle-bracket descriptions with actual values when it writes a record. They are field explanations here, not executable defaults.

## 15. Definition of Done

- A deterministic, topic-neutral generator and an independently implemented property checker exist.
- Required CI includes a fast pairwise suite; the full matrix has an explicit deterministic lane.
- The suite exercises 1/10/20 baseline burdens and 1/3/6/8 submoves as probes, not targets or limits.
- Dependency shapes include independent, chain, fan-out, fan-in, diamond, mixed, held activation, generated recursion, valid pre-LoopBreak noetic cycles with explicit interruption, and invalid event/provenance cycles.
- Route-kind probes vary the known universe and prove that unknown/unclassified candidates remain visible under HOLD/PARTIAL rather than being rejected by a closed enum.
- Candidate states, split/merge, owner obligations, body refs, generated/held/pre-empted lifecycle, rereads, NAR, public projection, and sidecar custody are conserved across stages.
- The current eligible-owner disappearance false-pass fails at Stage04 for the pinned right reason.
- Removing any required join produces the correct earliest-stage diagnostic.
- Repeated filler cannot add topology credit.
- A compact valid field can pass; a large padded unreconstructible field fails.
- Exact-dimension replay works for every fresh five-smoke record, regardless of whether its cardinalities match standing probes.
- Every deterministically reproducible topology defect first seen in a model
  smoke becomes a topic-neutral, metamorphically challenged, CI-wired permanent
  canary before the next candidate can become mature.
- The exact-SHA A15 report is a required input to
  `NO_MODEL_CANDIDATE_MATURE`; no stale or cross-candidate report is accepted.
- `run_local_ci.py --strict-pwsh` and the composed no-model preflight pass after wiring.
- No model smoke is claimed by this deterministic suite.
- Structural PASS remains explicitly non-semantic.
- `regression_status` remains `unproven` until the controlled evidence plan is executed.

## 16. Confidence

Current Stage04 parser/container capacity: **confirmed for the inspected declared 1x1, 10x3, and 20x8 probes only**.  
Current end-to-end arbitrary-topology fidelity: **unproven**.  
Property-suite architecture: **YES, implementation-ready after canonical P0 schemas are settled**.  
Semantic adequacy for arbitrary natural-language inputs: **NO, requires independent human adjudication and scoped model evidence**.  
v0.4.6 regression causality: **unproven**.
