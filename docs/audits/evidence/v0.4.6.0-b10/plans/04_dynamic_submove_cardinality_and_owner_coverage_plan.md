# ANDON A04: Dynamic Submove Cardinality and Owner-Obligation Coverage

Priority: P0 structural false-pass, then P1 runtime-policy migration  
Implementation target: PR #9 branch `codex/v0.4.6.0-runtime-footprint`  
Planning baseline: `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Regression status: `unproven`  
Implementation status: not started  
Prerequisites: Plan 02 source-pressure IDs and Plan 03 partition decisions

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Purpose

This plan closes the direct engineering form of the “too few submoves” ANDON.

The runtime must derive as many operative submoves as the selected burden topology requires. It may legitimately need one, three, six, eight, or another number. The count is not chosen from a quota. It is the number of distinct executable owner/register/pressure transitions that remain after valid integration, contingency, optionality, HOLD, and PARTIAL decisions.

The missing control is inverse owner coverage:

> Every executable owner obligation emitted by Stage03 must either execute as its own Stage04 ACT/submove or receive one permitted, evidence-bearing terminal disposition.

## Abnormality

Current Stage04 checking establishes burden-level coverage and forward owner validity:

- every Stage03 route target burden appears in Stage04 `act_targets` or `held_act_targets`;
- every ACT row owner must be backed by some Stage03 `owner_routes` entry;
- ACT rows must use canonical syntax and body references;
- owner/operation and delta-result vocabulary are validated; and
- the staged runner requires typed `act_row_details` for model-produced records.

Those are real safeguards and must be retained.

The surviving gap is the inverse relation. `stage04_act_errors(...)` computes:

```python
unsupported_owners = row_owners - eligible_owners
```

and rejects unsupported ACT owners. It does not compute or reject:

```python
eligible_executable_owner_obligations - executed_or_terminally_disposed_obligations
```

Burden-level coverage is too coarse. One ACT row can cover `B1` while a second or third executable owner route on `B1` disappears.

## Direct GEMBA Reproduction

The current maximal Stage04 fixture contains two Stage03 owner routes and two ACT rows:

```text
tests/stage-contract-workbench/stage-04-burden-execution-act/maximal-valid/multi-act-row-details.json
```

An in-memory probe appended a third executable route:

```json
{"burden_id": "B1", "owner_id": "M7", "eligibility": "catalogue-backed"}
```

without adding an M7 ACT row, body reference, or terminal disposition. The current checker returned no errors.

Exact read-only reproduction:

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
$env:PYTHONPATH='tools'
@'
import copy, json
from pathlib import Path
import check_staged_runtime_handshake as c

p = Path('tests/stage-contract-workbench/stage-04-burden-execution-act/maximal-valid/multi-act-row-details.json')
record = json.loads(p.read_text(encoding='utf-8'))
baseline = c.record_errors(p, record)
mutant = copy.deepcopy(record)
stage03 = next(s for s in mutant['stages'] if s['id'] == 'stage-03-routing-owner-gate')
stage03['owner_routes'].append({
    'burden_id': 'B1',
    'owner_id': 'M7',
    'eligibility': 'catalogue-backed'
})
errors = c.record_errors(Path('in-memory-stage03-owner-omission.json'), mutant)
print(json.dumps({
    'baseline_error_count': len(baseline),
    'mutant_error_count': len(errors),
    'mutant_errors': errors
}, ensure_ascii=False, indent=2))
raise SystemExit(0 if not baseline and not errors else 1)
'@ | python -
```

Observed planning-baseline result: exit `0`, `baseline_error_count: 0`, `mutant_error_count: 0`.

This is a confirmed structural false-pass. It does not prove that any particular live model output omitted M7, nor that M7 should be active for the fifth smoke.

Direct Git-object inspection also found the same forward-only `row_owners - eligible_owners` logic in the inherited current-main layer `c86b3c6...` and at PR #9's declared base `56d023e...`. The PR-base-to-head diff does not alter those lines. The inverse-coverage defect is therefore confirmed main-inherited contract debt at this owner surface, not code introduced by PR #9.

## Evidence Classification

### Confirmed

- Current Stage03 may contain several owner routes for one burden.
- Current Stage04 can contain several owner-specific ACT rows for that burden.
- The checker rejects `row_owners - eligible_owners` but not the inverse omission set.
- The checker covers Stage03-to-Stage04 burdens, not every Stage03 executable owner transition.
- The staged runner prompt says every `route_targets` burden must be ACTed or held, but does not say every executable `owner_routes` row must terminate.
- Current source law already requires each materially active owner/TTP to remain a distinct target-operation-result submove.
- Existing source already classifies owner work as required/sequenced, parallel, contingent, optional non-load-bearing, or hold/partial.
- Existing output checkers already reject many label-only, ownerless, and body-thin submoves. This plan adds missing obligation coverage; it does not replace those checkers.
- Existing “more than three submoves” saturation language is inherited policy debt. It is not proof that three is a correct universal boundary.
- The inspected inverse-coverage implementation is present in both the inherited current-main layer and PR9's declared base, so it predates PR9 head.

### Inferred

- The inverse-coverage gap can produce too few submoves while all surviving ACT rows remain syntactically and locally valid.
- It plausibly contributes to proof-looking thin outputs when several owner operations are routed under one broad burden.
- Harness prompts may reduce the frequency of the gap without making the canonical checker complete.

### Unproven

- How many submoves any one smoke should produce.
- That every eligible catalogue owner should execute; only selected executable obligations are in scope.
- That runtime-footprint compaction behaviorally amplified this inherited gap in any particular model run.
- That adding owner-obligation records proves semantic sufficiency or owner-body depth.
- That v0.4.6.0 regressed relative to v0.4.5.0.

## Architectural Requirement and Formal Location

This ANDON sits at:

```text
IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)
  → ∇_route
  → ⁿB
  → {ⁿBᵢ[OPᵢ]}
  → Land(ⁿB)
  → ΔⁿB{♥,ξ,Ω,σ,μ}/Δκ
```

The owner plan is the bridge from selected burden to operative submoves. Each `ⁿBᵢ[OPᵢ]` is an executable transition, not a label:

```text
validated target + selected owner + callable operation + register axis
  → owner-local operation evidence
  → delta result
  → contribution to Land(ⁿB)
```

The cardinality follows the relation:

```text
submoves(ⁿB) = terminally executed distinct owner obligations required to Land(ⁿB)
```

This is not a numeric floor. An obligation that is genuinely duplicate, contingent and not triggered, optional and non-load-bearing, or held/partial does not become a fake ACT row. It must still remain visible as a terminal disposition.

## Real Five Whys

1. **Why can an executable owner disappear?**  
   Because Stage04 validates ACT owners against the Stage03 eligible set in the forward direction only.

2. **Why does burden coverage not catch it?**  
   `act_targets` is a burden-ID set. One ACT on a burden satisfies burden-level membership even when other executable owner transitions on that burden are absent.

3. **Why did `owner_routes` not function as a complete obligation ledger?**  
   Its rows identify eligibility and vocabulary, but they lack stable obligation IDs and no required Stage04 disposition joins back to every row.

4. **Why can later NAR or witness checks miss the omission?**  
   They reconstruct the ACT rows that survived. Without an expected owner-obligation set, an omitted owner leaves no orphan row or mismatched body reference to detect.

5. **Why are fixed submove minima or “more than three” triggers the wrong root fix?**  
   Counts cannot distinguish necessary transitions from padding. The actionable root is the missing Stage03-obligation-to-Stage04-disposition bijection, owned by the staged owner/ACT contract and its checker.

Root owner/source:

```text
tools/check_staged_runtime_handshake.py::stage04_act_errors
tools/run_staged_current_skill_smoke.py::STAGE_SPECS[stage-03/04]
atomics/skill/references/diagnostics/diagnostic-ir.md owner-plan law
```

## Hansei

### Existing strengths to preserve

- Stage03 has explicit owner routes rather than a prose route list.
- Owner aliases, callable operations, register axes, and delta-result vocabulary already have validators.
- Stage04 has canonical ACT rows, `body_ref` joins, and typed details in the model runner.
- Stage06/NAR and public field-witness surfaces already mirror owner activations.
- Existing ordering structures distinguish required-before, parallel, contingent, optional, and hold/partial owner work.
- Existing render checks test operation mass and body attachment.

### What failed

- Forward validity was mistaken for bidirectional coverage.
- Burden IDs were treated as the sufficient unit of Stage03-to-Stage04 accounting.
- Optional Stage04 detail behavior in the standalone checker drifted from the runner's stronger requirement.
- The saturation gate was triggered by a number instead of being applied as a relational cohesion test to each candidate transition.
- Historical hard-canary count and size examples risked becoming de facto universal policy.

### Learning

An owner route becomes runtime work only when it is either executed or terminally disposed. The checker must reason over obligation identities, not infer completeness from one ACT per burden or from aggregate output length.

## Target Contract

### Version gate

Reuse:

```json
{"topology_contract": "input-pressure-v1"}
```

For this contract, every Stage03 `owner_routes` row is an owner obligation. Legacy retained records remain valid under their historical contract, but no new five-smoke completion record may omit obligation identity.

### Stage03 owner-obligation row

Extend the existing `owner_routes` object rather than creating a second competing owner list:

```json
{
  "obligation_id": "O-B1-001",
  "burden_id": "B1",
  "pressure_ids": ["P1"],
  "partition_decision_id": "BP1",
  "owner_id": "M7",
  "operation": "definition-anchor",
  "register_axis": "Omega",
  "execution_class": "required | contingent | optional_non_load_bearing | hold_partial",
  "route_status": "executable | held | partial",
  "trigger": null,
  "owner_body_status": "loaded | not_loaded | vocabulary_gap",
  "same_burden_cohesion": {
    "target_family_relation": "same | distinct | unresolved",
    "tau_relation": "same | distinct | unresolved",
    "source_frame_relation": "same | distinct | unresolved",
    "claim_cluster_relation": "same | distinct | unresolved",
    "restoration_vector_relation": "same | distinct | unresolved",
    "already_handled": false
  },
  "basis": "why this owner transition is live or held"
}
```

Rules:

- `obligation_id` is unique within the case and stable through Stage03-Stage07.
- `pressure_ids` join to Plan 02; `partition_decision_id` joins to Plan 03.
- A route label, case family, noetic frame, or owner family mention is not an obligation unless it names a callable owner/operation or is explicitly held/partial.
- `required` and `contingent` executable rows require controlled owner, operation, register-axis, and owner-body status.
- `contingent` requires an explicit trigger that can be evaluated from prior obligation results.
- `optional_non_load_bearing` must name why it does not contribute a required state transition.
- `hold_partial` requires a blocker and next action; it cannot be upgraded to execution by normalizer inference.
- Two distinct operations by the same owner are two obligations.
- The same owner/operation acting on two distinct pressure transitions is two obligations unless Plan 03 proves the pressure is duplicate/derivative.
- Owner order continues to use the existing required-before/parallel structures. Obligation IDs are added as strong endpoints; existing owner/body-ref endpoints remain for public compatibility.

### Relational cohesion, not a numeric saturation trigger

Apply `same_burden_cohesion` to every candidate obligation after the first obligation selected for a burden, not only after a numerical threshold.

An obligation remains a submove inside the current burden only when:

- target family, `τ`, source/noetic frame, claim cluster, and restoration vector remain same/compatible;
- the operation is not already handled by a prior result; and
- Plan 03 has not classified the pressure as a distinct burden function.

If cohesion is distinct or unresolved, do not silently append or consolidate the submove. Return to the burden-partition decision, or carry the obligation as HOLD/PARTIAL. The number of existing submoves does not decide the result.

### Stage04 terminal disposition

Add a required list for `input-pressure-v1` records:

```json
{
  "owner_execution_dispositions": [
    {
      "obligation_id": "O-B1-001",
      "burden_id": "B1",
      "disposition": "executed | integrated_duplicate | contingent_not_triggered | optional_not_selected | held | partial",
      "body_ref": "B1_1",
      "satisfied_by_obligation_id": null,
      "trigger_evidence": null,
      "basis": "terminal reason",
      "gate": null,
      "next_action": null
    }
  ]
}
```

Disposition rules:

- `executed` requires exactly one matching Stage04 `act_row_details` row with the same `obligation_id`, burden, owner, operation, register axis, pressure, and body reference.
- `body_ref` is a nonempty join key only for `executed`; it is `null` for every non-executed disposition. A held, optional, contingent-not-triggered, partial, or integrated-duplicate row must not point at a body it did not execute.
- One ACT row satisfies one obligation. A multi-paragraph operation body remains one submove; a second distinct transition receives a second obligation and ACT row.
- `integrated_duplicate` requires `satisfied_by_obligation_id` naming an executed obligation. It is allowed only for the same owner/operation/register transition and the same pressure or a Plan 03 derivative mapping. It cannot consolidate distinct active TTPs.
- `contingent_not_triggered` is allowed only for a Stage03 `contingent` obligation and requires trigger evidence tied to preceding results.
- `optional_not_selected` is allowed only for `optional_non_load_bearing`; it cannot claim a delta or contribute to `Land(B)`.
- `held` and `partial` require a gate and `next_action`. They force the downstream release state away from unqualified completion. Preserve the current distinction between validation status and release status: Stage04 may remain structurally `pass` when Stage03 already supplied a valid hold/partial route, but a newly declined Stage03-executable obligation makes Stage04 held/partial, and neither case may become Stage07 `COMPLETE`.
- A `required` executable obligation can terminate only as `executed`, a narrowly proved `integrated_duplicate`, `held`, or `partial`.

### Set invariants

Let:

```text
E = all Stage03 obligation IDs
A = obligation IDs named by Stage04 ACT details
D = obligation IDs named by Stage04 terminal dispositions
X = disposition IDs marked executed
```

For every new release-bearing record:

```text
E = D
A = X
A ⊆ E
```

Additional invariants:

- no duplicate obligation ID in Stage03, ACT details, or dispositions;
- no ACT detail without a routed obligation;
- no routed obligation without a disposition;
- no executed disposition without an ACT row;
- no ACT row whose disposition is non-executed;
- Stage04 structural `pass` with held/partial is allowed only when the same Stage03 obligation was already classified `hold_partial`; a newly declined executable obligation cannot remain Stage04 pass;
- no unqualified Stage07 `COMPLETE` while an obligation remains held/partial;
- current burden-level `act_targets` coverage remains enforced and is not removed.

### Dynamic cardinality result

The Stage04 submove count is derived after the set proof:

```text
submove_count(Bn) = |{o in E(Bn) : disposition(o) = executed}|
```

The count is reported for audit only. It never becomes a minimum, maximum, output-length multiplier, or topic-specific expectation.

### State-carry projection

Build on Plan A16's one shared `daee-state-capsule-v2` object, after Plan A03 contributes its topology fields:

```json
{
  "owner_obligation_state": {
    "declared_ids": ["O-B1-001", "O-B1-002"],
    "executed_ids": ["O-B1-001"],
    "held_ids": ["O-B1-002"],
    "partial_ids": [],
    "disposition_sha256": "sha256:<64 hex>"
  }
}
```

This is append-only across multi-call execution except for explicit terminal transitions. A pending obligation may become executed, held, partial, or validly integrated; it may not disappear.

## Exact Owner and Edit Map

### Canonical editable runtime source

- `atomics/skill/references/diagnostics/diagnostic-ir.md`
  - own the Stage03 obligation record and execution classes;
  - preserve existing required-before, parallel, contingent, optional, and hold/partial semantics.
- `atomics/skill/references/diagnostics/recursive-state-transitions.md`
  - replace the numeric “more than three” trigger with per-obligation relational cohesion;
  - keep distinct active owner operations distinct.
- `atomics/skill/references/diagnostics/routing-precedence.md`
  - replace Rule P-6 numeric trigger with the same relational gate;
  - retain refresh-before-NewB and owner-specific exit.
- `atomics/skill/references/rubrics/diagnostic-render-contract.md`
  - bind visible ACT/submoves and owner activation ordering to obligation IDs;
  - do not duplicate body-depth semantics owned by Plan 05.
- `atomics/skill/references/rubrics/output-release.md`
  - block closure on unresolved owner obligations.
- `atomics/skill/SKILL.md`
  - add the compact bidirectional coverage invariant;
  - remove universal submove-count suggestions from normative language;
  - coordinate byte/whole-output language with Plan 06.

### Reuse without redefining

- `tools/delta_result_vocabulary.py`
  - keep as owner/operation/delta vocabulary owner;
  - do not copy its vocabulary into a new checker.
- Existing ACT parsing and body-ref helpers in `tools/check_staged_runtime_handshake.py` and staged-output utilities.
- Existing `owner_activation_ordering` and NAR projection structures.
- Existing manual render/body-depth checkers. A coverage PASS does not replace them.

### Add

- `tools/owner_obligation_coverage.py`
  - pure set/join/disposition validator;
  - accepts abstract IDs for property tests and typed staged rows for integration.
- `tests/owner-obligation-coverage/valid/`
- `tests/owner-obligation-coverage/invalid/`

### Modify staged producer/checker

- `tools/check_staged_runtime_handshake.py`
  - derive obligation set from Stage03 rows;
  - require `act_row_details` for `input-pressure-v1` release-bearing records;
  - enforce inverse coverage and terminal dispositions;
  - add first-failure class `owner-obligation-coverage` with earliest stage `04`: Stage03 creates the eligible-owner obligation; the omission becomes invalid when Stage04 fails to execute or explicitly dispose it.
- `tools/run_staged_current_skill_smoke.py`
  - Stage03 emits obligation IDs and classes;
  - Stage04 receives all obligations and emits all dispositions;
  - normalizers may canonicalize but never fabricate a missing disposition or ACT;
  - no route-topology manufacture after model output.
- `tools/daee_dry_run_emulator.py`
  - carry and check obligation/disposition sets.
- `tools/build_staged_governed_output.py`
  - derive public owner activation mirrors only from executed dispositions and ACT rows.

### State and witness parity

- `schema/state-capsule-v2.schema.json` owned by Plan A16, with Plan A03 topology fields already integrated
- `tools/check_state_capsule.py`
- `docs/recursive-state-capsule.md`
- `tools/check_field_witness_convergence.py`
- Stage06/07 workbench fixtures

The public witness migration must preserve the Plan 09 dialect decision. This plan adds obligation IDs and parity, not a second `field_witness` shape.

### Fixtures

- Extend `tests/stage-contract-workbench/stage-03-routing-owner-gate/` with obligation rows and ordering roles.
- Extend `tests/stage-contract-workbench/stage-04-burden-execution-act/` with terminal disposition fixtures.
- Add Stage06/07 projection fixtures for omitted owner activation and unresolved obligation closure.
- Add `<fixture-stem>.expectation.json` sidecars under Plan A11's `daee-negative-fixture-expectation-v1` for every new active staged invalid fixture. Existing historical `.expected-explain.json` files are consumed only through A11's adapter.

### Deterministic CI

- `tools/run_local_ci.py`
- `tools/ci_registry.json`
- `tools/run_no_model_preflight.py`
- `tools/gen_fixture_mutations.py`, but only after mutation verdicts assert expected earliest stage and class.

### Generated: never hand-edit

- `skill/**`
- compiled runtime maps and manifests
- generated framework-pipeline sections

## Fixture and Property-Test Lattice

### Valid integration fixtures

1. One required obligation, one ACT row, one executed disposition.
2. Several required owners on one burden, each with a distinct obligation and ACT row.
3. Same owner with two distinct operations, two obligations, two ordered ACT rows.
4. Same owner/operation on distinct non-derivative pressures, preserved as separate obligations.
5. Contingent owner whose trigger is false after a preceding result.
6. Optional non-load-bearing owner explicitly not selected.
7. Held owner body with gate and next action; Stage04/07 remains held or partial.
8. Valid derivative integration naming the executed obligation that satisfies it.
9. Required-before and parallel groups whose obligation endpoints match ACT order.

### Invalid integration fixtures

1. `eligible-owner-omitted-no-disposition.json`: the confirmed M7 false-pass.
2. Disposition says executed but no ACT row exists.
3. ACT row exists but no Stage03 obligation exists; preserve the existing forward check.
4. Required obligation is marked `optional_not_selected`.
5. Contingent obligation lacks trigger evidence.
6. Integrated duplicate names a different owner/operation or a distinct pressure.
7. A newly declined Stage03-executable obligation coexists with Stage04 pass, or any held/partial obligation coexists with Stage07 complete.
8. Duplicate obligation ID.
9. ACT detail and disposition disagree on body reference.
10. Same-burden cohesion is distinct/unresolved but operation executes without repartition or hold.
11. State capsule drops a pending owner obligation between calls.
12. NAR/field witness omits an executed obligation or invents one not executed.

### Cardinality property tests

The pure checker generates neutral obligation sets parameterized by `n`; it must not contain hardcoded theological owners or expected response text.

Representative regression samples include `n = 1, 3, 6, 8, 20`, because the owner explicitly identified those as plausible shapes. They are capacity samples, not floors or caps. The property under test is:

```text
for any generated n within resource-safe test bounds:
  complete one-to-one obligation/disposition joins pass;
  deleting any one required disposition fails;
  adding any unsupported ACT fails;
  permuting valid parallel obligations preserves validity;
  violating required order fails;
```

Do not use repeated filler prose or bytes to simulate topology capacity.

## Test-Driven Patch Sequence

### Phase 0: Baseline and ownership drift

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
git -C $repo status --short --branch --untracked-files=all
git -C $repo rev-parse HEAD
git -C $repo rev-parse origin/codex/v0.4.6.0-runtime-footprint
```

Expected before implementation: clean and pinned at `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`.

STOP if Plan 02/03 or another worker has already changed the same staged contract. Re-read the effective data shape and revise this plan before editing.

### Phase 1: Freeze the inverse-coverage false-pass

Add:

```text
tests/stage-contract-workbench/stage-04-burden-execution-act/invalid/eligible-owner-omitted-no-disposition.json
tests/stage-contract-workbench/stage-04-burden-execution-act/invalid/eligible-owner-omitted-no-disposition.expectation.json
```

The fixture is the current maximal-valid Stage04 record plus a third M7 Stage03 obligation, with no M7 ACT or disposition. Before the fix, the full fixture suite must go red because the expected-invalid fixture passes.

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
python tools\check_staged_runtime_handshake.py
```

Expected before checker implementation: exit `1`, with `expected-invalid staged handshake fixture unexpectedly passed` naming the new fixture.

### Phase 2: Implement pure set/join validation

Add `tools/owner_obligation_coverage.py` and topic-neutral fixture tests before changing the handshake checker.

```powershell
python tools\owner_obligation_coverage.py --self-test
```

Expected after implementation: exit `0`; valid fixtures pass and all invalid relation mutations fail for their registered reason.

The helper must accept already-normalized rows. It must not reimplement owner vocabulary, ACT grammar, body depth, or semantic truth checks.

### Phase 3: Integrate the staged handshake

Add exact first-failure classification:

```json
{
  "origin_stage": "03",
  "failure_class": "owner-obligation-coverage",
  "earliest_stage": "04",
  "downstream_invalidated": ["05", "06", "07", "08"],
  "requires_model_rerun": false,
  "repair_lane": "no-model fixture/checker/runtime-contract repair"
}
```

Right-reason negative assertion:

```powershell
$p = 'tests\stage-contract-workbench\stage-04-burden-execution-act\invalid\eligible-owner-omitted-no-disposition.json'
$raw = python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $p
$code = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($code -ne 1) { throw "expected exit 1, got $code" }
if ($diag.failure_class -ne 'owner-obligation-coverage') { throw "wrong class: $($diag.failure_class)" }
if ($diag.earliest_stage -ne '04') { throw "wrong earliest stage: $($diag.earliest_stage)" }
if (($diag.downstream_invalidated -join ',') -ne '05,06,07,08') { throw "wrong downstream invalidation set: $($diag.downstream_invalidated -join ',')" }
```

Canonical CI assertion after Plan A11's helper lands:

```powershell
python tools\assert_expected_rejection.py --expectation tests\stage-contract-workbench\stage-04-burden-execution-act\invalid\eligible-owner-omitted-no-disposition.expectation.json --artifact-root auto
```

Expected: exit `0`; the helper also proves the fixture produced no Stage05-08 or promotion artifacts.

Positive assertion:

```powershell
$p = 'tests\stage-contract-workbench\stage-04-burden-execution-act\maximal-valid\multi-owner-obligations-complete.json'
$raw = python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $p
$code = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($code -ne 0) { throw "expected exit 0, got $code" }
if ($diag.status -ne 'pass') { throw "expected pass, got $($diag | ConvertTo-Json -Compress)" }
```

Full staged suite:

```powershell
python tools\check_staged_runtime_handshake.py
```

Expected: exit `0`; every invalid fixture has a matching expected diagnostic.

### Phase 4: Strengthen producer records without repair

Update Stage03 and Stage04 prompts. The Stage04 call receives the complete Stage03 obligation list and must answer for each ID.

Allowed normalization:

- canonical ID formatting;
- deterministic list ordering;
- owner alias normalization already supported by the repository;
- hash calculation; and
- derivation of executed-set parity from ACT details.

Forbidden normalization:

- deleting an owner route to make sets match;
- fabricating an ACT or disposition;
- changing required to optional;
- changing held/partial to executed;
- merging two obligations because they share a burden or owner; or
- manufacturing route topology before validation.

Commands:

```powershell
python tools\run_staged_current_skill_smoke.py --self-test
python tools\daee_dry_run_emulator.py --self-test
python tools\check_staged_runtime_handshake.py
```

Expected: all exit `0`.

### Phase 5: Migrate the cardinality law

Edit the canonical source so cohesion is checked for every candidate obligation. Remove normative dependence on:

- “more than three” as the point where cohesion suddenly matters;
- “3-5 submoves” as a hard-case target; and
- any implication that count or byte range can license completeness.

Keep examples only when explicitly labeled non-normative. Plan 06 owns whole-output mass and byte-warning policy; this plan owns submove cardinality.

Static scan after the edit:

```powershell
$hits = @(rg -n "more than three|3-5 submoves|3–5 submoves|minimum submove|submove floor" atomics\skill 2>&1)
$rgCode = $LASTEXITCODE
if ($rgCode -gt 1) { throw "rg failed with exit $rgCode" }
$hits
exit 0
```

Expected: the PowerShell block exits `0`. An empty result means no matching phrase remains; a nonempty result is a mandatory manual review list. Every surviving match must be explicitly historical or non-normative before this phase can close.

### Phase 6: State, NAR, and witness parity

Add obligation/disposition carry to capsule v2 and require executed IDs to equal NAR/owner-activation IDs.

```powershell
python tools\check_state_capsule.py --self-test
python tools\check_field_witness_convergence.py
```

Expected: both exit `0`; omission/invention fixtures fail internally and are counted as expected invalid.

These are structural parity checks. Plan 05 still decides whether a body executes enough owner-specific operation mass to license its delta.

### Phase 7: Capacity/property probes

```powershell
python tools\owner_obligation_coverage.py --self-test
```

Expected: exit `0`; generated 1/3/6/8/20 samples pass when complete, and one-deletion mutations fail. The tool reports sample sizes as test coverage only.

### Phase 8: Rebuild generated runtime

```powershell
python tools\build_framework_pipeline.py
python tools\check_framework_pipeline.py
python tools\build_compiled_runtime.py
python tools\check_compiled_runtime_freshness.py
python tools\check_package_shape.py
python tools\build_package_shape_inventory.py --check
```

Expected: all exit `0`. The default package remains free of development-only schema/tools, while the audit profile includes the planned validation surfaces according to existing package-shape policy. Review the generated diff and reject unrelated churn.

### Phase 9: Broad deterministic gates

```powershell
python tools\run_no_model_preflight.py --self-test
python tools\run_no_model_preflight.py
python tools\run_local_ci.py
```

Expected: all exit `0`. No model smoke runs in this phase.

## Stage01-Stage08 Effect

| Stage | Required effect of this plan | Failure if absent |
| --- | --- | --- |
| Stage01 | No direct owner decision; preserve exact source anchors from Plan 02. | Owner obligation cannot be traced to input. |
| Stage02 | Pressures and burden partitions supply obligation provenance. | Owner list can become a topic itinerary. |
| Stage03 | Every selected owner transition receives a stable obligation ID and class. | Eligible owner universe remains uncounted. |
| Stage04 | Every obligation receives one terminal disposition; executed obligations receive ACT rows. | Confirmed inverse-coverage false-pass survives. |
| Stage05 | Held/partial and contingent results remain visible during reread. | Missing owner pressure can be hidden by STOP. |
| Stage06 | NAR and witness owner activations equal the executed obligation set. | Proof object reconstructs only a subset. |
| Stage07 | Public submoves/body refs dereference every executed obligation; unresolved obligations block complete. | Labels or final synthesis can hide omitted work. |
| Stage08 | Verifier sidecars retain obligation/disposition hashes and first-failure class. | Promotion cannot distinguish omission from valid compactness. |

## Five-Smoke Implications

Required fresh cases:

- `gate88-secularism`
- `gate88-khaybar`
- `gate88-trinitarian-j173`
- `gate88-tst-lillard`
- `gate88-torah-quran-source-authentication`

For each case:

1. Stage03 records every selected executable owner transition as an obligation.
2. Stage04 accounts for every obligation without count targets.
3. Each executed obligation has one local ACT/submove and a Plan 05 body.
4. Held, partial, optional, and contingent obligations remain explicit.
5. Stage06/07 mirrors the executed and unresolved sets exactly.
6. Stage08 records structural verdicts without claiming semantic truth.

The fifth smoke must not predeclare M7, V10, transmission, source-status, a burden count, a submove count, citations, or an expected answer. Its owner obligation set is produced only after its actual Stage02/03 diagnosis and partition.

Passing all five cases under this checker proves that those five runs did not omit a declared Stage03 owner obligation. It does not prove that Stage03 selected every semantically necessary owner. Plan 02/03 topology review and Plan 05 body review remain separate gates.

## Rollback

- Revert obligation IDs, dispositions, checker integration, source-law migration, capsule fields, fixtures, and generated runtime as one coherent patch series.
- Rebuild generated files from reverted atomics; never hand-edit `skill/**`.
- Preserve the confirmed M7 omission fixture as historical negative evidence even if the chosen data shape changes.
- If full terminal dispositions prove too verbose in model prompts, keep stable obligation IDs and require non-executed dispositions plus checker-derived executed rows. Do not fall back to one-ACT-per-burden coverage.
- If state-capsule v2 is deferred, Stage03/04 records and Stage06 projection must still retain obligation identity; mark multi-call carry `PARTIAL` rather than claiming completion.

## STOP / ANDON Conditions

Stop if implementation:

- adds a universal minimum or maximum submove count;
- uses 3, 6, 8, or 20 as a policy rather than a capacity sample;
- creates ACT filler to satisfy counts;
- treats every catalogue-eligible owner as executable without route selection;
- lets one ACT satisfy several distinct owner/operation/register transitions without derivative proof;
- changes a required obligation to optional after Stage03;
- permits an unresolved obligation to vanish from capsule, NAR, witness, or public body;
- upgrades a held/partial release disposition to `COMPLETE`, or treats Stage04 structural pass as proof that no owner remains held;
- duplicates owner-vocabulary or body-depth logic in the new set checker;
- lets normalizers repair missing owner execution;
- claims obligation coverage proves semantic truth or adequate body depth;
- introduces Torah/Qur'an-specific owner routes or response content; or
- advances `regression_status` beyond `unproven` without Plan 01 evidence.

Required ANDON record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED
class: owner-obligation-coverage | obligation-disposition-drift | cardinality-policy | state-carry-loss | projection-parity
failing_check: "python tools/check_staged_runtime_handshake.py --explain-stage-failure --records tests/stage-contract-workbench/stage-04-burden-execution-act/invalid/eligible-owner-omitted-no-disposition.json"
first_failed_stage: "04"
owner_source: "tools/check_staged_runtime_handshake.py::stage04_act_errors"
burden_ids: [B1]
obligation_ids: [O-B1-001, O-B1-002, O-B1-003]
missing_or_conflicting_dispositions: ["O-B1-003:missing"]
preserved_artifacts:
  - path: tests/stage-contract-workbench/stage-04-burden-execution-act/invalid/eligible-owner-omitted-no-disposition.json
    sha256_source: "computed by owner-obligation fixture manifest after Phase 1 creates the file"
next_action: "enforce inverse owner-obligation coverage and pin the expected diagnostic sidecar"
non_claim: "this structural omission does not prove semantic owner selection, body sufficiency, or v46 regression causality"
```

The fixture does not exist at planning time, so the example does not invent a hash. Phase 1 must create it, compute the SHA-256, and write that concrete value into the actual ANDON record/fixture manifest before handoff.

Do not emit both handoff and completion for the same audit state.

## Definition of Done

- The exact M7 omission fixture fails with `owner-obligation-coverage`, earliest stage `04`.
- Existing unsupported-owner forward rejection remains intact.
- Every new-contract Stage03 owner route has a unique obligation ID and execution class.
- Every Stage03 obligation has exactly one Stage04 terminal disposition.
- Executed dispositions and ACT details are a bijection.
- Required, contingent, optional, held, partial, and valid duplicate states have right-reason fixtures.
- Same-burden cohesion is relational for every candidate obligation; no numeric trigger governs it.
- The checker processes arbitrary obligation-list lengths without hardcoded topology caps.
- Representative 1/3/6/8/20 property probes pass complete cases and reject deletion mutations.
- State capsule, NAR, field-witness projection, and public ACT/body references agree on obligation identity.
- Plan 05 body-depth checks remain mandatory; this plan does not substitute structural presence for operation mass.
- Deterministic Stage01-Stage08, capsule, witness, framework, runtime-freshness, no-model preflight, and local-CI gates pass.
- All five fresh smokes pass obligation coverage through Stage08 after the complete ANDON patch set.
- No fixed byte, burden, or submove floor and no fifth-smoke argument bank is introduced.
- Structural PASS remains explicitly non-semantic.
- `regression_status` remains `unproven` until admissible paired evidence exists.

## Confidence

Confirmed false-pass and checker owner: **HIGH.**  
Repo-local inverse-coverage implementation: **YES, implementation-ready after Plan 02/03 field names are fixed.**  
Cardinality-policy migration: **YES in design; requires coordinated source and fixture review.**  
Semantic owner selection completeness: **NO; topology review remains required.**  
Five-smoke behavioral closure: **UNPROVEN until authorized fresh Stage01-Stage08 runs exist.**  
v46 regression causality: **UNPROVEN.**
