# ANDON A02: Input-Pressure Inventory and Dynamic Burden Topology

Priority: P0/P1 structural-integrity fix  
Primary pipeline location: `D0 -> PsiN -> IR -> route gradient -> Bn`  
Plan status: implementation-ready after owner authorization  
Semantic completeness status: human-adjudicated; not fully machine-decidable
Regression status: `unproven`

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Abnormality

Stage02 currently proves that a declared `burden_floor` exists and uses canonical IDs. Stage03 proves that route targets mirror that floor. Neither proves that the floor faithfully represents the source input. A producer can collapse several live pressures into `B1`, omit the rest, and remain internally consistent through every later stage.

This is the earliest controllable location for the “too few burdens” ANDON. Later body, MRP, witness, and closure checks cannot recover a pressure that never entered the declared universe.

## Current False-Pass

The checked-in fixture:

```text
tests/stage-contract-workbench/stage-02-layer-a-diagnostic-ir/minimal-valid/single-burden-floor.json
```

passes with a single burden ID and no source-pressure anchors, candidate-state inventory, split/merge record, held pressure, or non-load-bearing disposition. This is a valid minimal syntax fixture under the current contract, but it is not sufficient evidence for a release-bearing Stage01-Stage08 model run.

Current checker behavior:

- `stage02.burden_floor` must be a nonempty canonical string list.
- `burden_floor_details` is optional.
- Stage03 route targets must equal the Stage02 floor.
- The original input is represented by an `input_digest`, but no join requires burdens to cover source-anchored observations.

## Architectural Requirement

The North Star and Rebake require the design to support noetic structures not known at design time. The implementation must therefore preserve:

- multiple candidate noetic frames when the input supports them;
- distinct live pressures until a merge is justified;
- candidate burdens, dependencies, held states, and non-load-bearing material;
- runtime-selected cardinality rather than topic-keyed or count-keyed routing;
- an honest `B_LA` consisting only of pressures recognized before post-Land MRP.

This plan does not tell the model how many burdens a Torah/Qur'an, secularism, Khaybar, trinitarian, or TST input “should” have. It makes omission observable.

## Five Whys

1. Why can too few burdens pass?  
   Because the checker validates the declared burden list but has no structural join back to the input pressures that licensed it.

2. Why is there no join?  
   Stage01 records only an input digest, and Stage02 pressure/burden details are optional. The contract begins after semantic partitioning has already occurred.

3. Why was a burden list considered sufficient?  
   Earlier hardening prioritized canonical IDs, cross-stage membership, and generated-burden provenance. Those controls prevent downstream contradiction but assume the initial universe is adequate.

4. Why cannot later witness completeness detect the omission?  
   A witness can be perfectly complete over an incomplete graph. Graph closure proves internal coverage of selected nodes, not that all materially live source pressures became nodes.

5. Why could this omission persist across later hardening?  
   Validation ownership began at the model-declared burden floor, while no source owner was assigned a machine-readable observation-to-pressure coverage proof before that floor. Later stages therefore had no upstream completeness object to join or challenge.

Severity: this is central to DAEE because unknown-at-design-time noetic topology is the thesis being implemented. If the runtime can silently choose a smaller universe before `IR`, every later formal operator can faithfully reconstruct the wrong field.

Root owner/source: Stage01-02 source-to-IR handoff and its producer/checker contract, not output byte limits or theological modules.

## Hansei

### Existing strengths

- The stage pipeline already has explicit Stage01 and Stage02 records.
- Input digest custody already exists.
- Canonical burden IDs and Stage02-to-Stage03 set equality are checked.
- The branch has a mutation framework, first-failed-stage classifier, and positive/negative fixture conventions.

### Failure in design

- “Input preserved by hash” was allowed to stand in for “input pressures considered.”
- `burden_floor_details` remained optional on release-bearing paths.
- Candidate noetic states were compressed into one selected state without a terminal candidate-state ledger.
- Earlier plans proposed fixed minimum burden counts, which would measure a symptom while violating the architecture.

### Learning

The pipeline needs a pre-burden accounting unit that is content-neutral but source-bound. It must be possible to say, “this source unit was considered and merged/held/non-load-bearing for this reason,” without pre-authoring its theological interpretation.

## Target Contract

### Contract versioning

Introduce `topology_contract: input-pressure-v1` on Stage01-02 records.

Migration rule:

- Legacy isolated fixtures may remain syntactically valid during Phase 1.
- Any Stage07/Stage08 release-bearing record, any five-smoke run, and any new retained case must use `input-pressure-v1` after Phase 2.
- Legacy release-bearing records cannot receive a current promotion verdict after the migration gate is enabled.

Do not silently reinterpret old retained sidecars as if they contained the new evidence.

### Stage01 observation units

Stage01 gains a deterministic, interpretation-light observation manifest. It is not a burden list.

Each `observation_unit` contains:

```json
{
  "unit_id": "U1",
  "source_start": 0,
  "source_end": 42,
  "source_sha256": "<hash of exact UTF-8 slice>",
  "surface_kind": "claim | question | contrast | narrative-context | conclusion | instruction | quote",
  "parent_unit_id": null
}
```

Rules:

- Offsets are over exact UTF-8 bytes or exact Unicode code points; choose one and pin it in schema/tests. Do not mix them.
- Units may nest when one paragraph contains a quoted claim and an inference.
- Segmentation is a custody/coverage aid, not a semantic burden judgment.
- Empty, overlapping, or out-of-range anchors fail unless the overlap is an explicit parent-child relation.
- Every non-whitespace source range is covered by at least one top-level unit or an explicit formatting-only span.

Recommended implementation: use a deterministic paragraph/sentence/quoted-block splitter in a new `tools/input_observation_units.py`. Avoid a topic lexicon. The model may refine units in Stage02, but any refinement remains anchored to exact source spans.

### Stage02 candidate-state inventory

Stage02 must preserve the candidate noetic structures considered before selection:

```json
{
  "candidate_states": [
    {
      "state_id": "N1",
      "observation_unit_ids": ["U1", "U2"],
      "frame": "<bounded structural description>",
      "live_registers": ["kappa", "Omega"],
      "status": "selected | held | underdetermined | merged | rejected",
      "basis": "<required, source-anchored reason>",
      "merged_into": null
    }
  ]
}
```

The checker validates IDs, coverage, allowed statuses, and joins. It does not decide whether the frame is theologically correct.

Candidate-state rules:

- A selected state is required only when the evidence licenses selection. Zero selected candidates is valid with `selection_status: not_licensed` when one or more candidates remain `held` or `underdetermined`; the downstream artifact must remain HOLD/PARTIAL and may not claim collapse.
- Every candidate is selected, held, underdetermined, merged into another candidate with a decision record, or rejected with a bounded basis.
- “Rejected because not selected” is circular and invalid.
- A low-ambiguity input may have one candidate state. The contract never requires multiple candidates by count.

### Stage02 pressure inventory

```json
{
  "input_pressures": [
    {
      "pressure_id": "P1",
      "observation_unit_ids": ["U2"],
      "candidate_state_ids": ["N1"],
      "pressure_function": "<what must change or be bounded for the input to land>",
      "register_axes": ["Omega"],
      "status": "routed | merged | held | non_load_bearing | unresolved",
      "burden_id": "B1",
      "decision_id": null,
      "basis": "<source-anchored structural basis>"
    }
  ]
}
```

Rules:

- Every non-contextual observation unit maps to at least one pressure.
- Every observation unit not mapped to a pressure receives an explicit disposition: `narrative_context`, `duplicate`, `formatting`, `instruction_only`, or `non_load_bearing`, with basis.
- `routed` pressure names exactly one initial `B_LA` burden.
- `merged` pressure names a merge decision and the receiving burden.
- `held` remains visible and names a gate/next action; it does not disappear from coverage.
- `unresolved` forces Stage07 `PARTIAL` or `RECURSE`.
- Stage02 must not enumerate future MRP-generated burdens. Generated pressure remains Stage05-owned.

### Stage02 coverage proof

The machine proof is set accounting, not semantic certification:

```json
{
  "input_coverage": {
    "all_observation_unit_ids": ["U1", "U2"],
    "pressure_bearing_unit_ids": ["U2"],
    "explicitly_disposed_unit_ids": ["U1"],
    "unaccounted_unit_ids": []
  }
}
```

`unaccounted_unit_ids` must be empty for a release-bearing run. This proves every surface unit has a disposition. It does not prove the disposition is semantically correct; that remains a topology-review gate.

## Exact Owner and Edit Map

### Runtime source

- `atomics/skill/references/diagnostics/diagnostic-ir.md`: canonical candidate-state, observation, pressure, disposition, and burden-floor law.
- `atomics/skill/references/diagnostics/recursive-state-transitions.md`: ensure `B_LA` lifecycle begins from routed Stage02 pressures and generated burdens remain Stage05-owned.
- `atomics/skill/references/diagnostics/framework-pipeline.yaml`: add Stage01/02 input-pressure artifacts to the control-plane owner map if its schema permits.
- `atomics/skill/SKILL.md`: only a compact hot invariant and pointer; do not re-inline the full contract.

### Producer/harness

- `tools/run_staged_current_skill_smoke.py`: Stage01 and Stage02 prompts, record normalization, state-capsule handoff, and required `topology_contract` on new runs.
  Remove any named-target-to-`PRESUPPOSED` frame default and any topic/lexical mapping that fixes owner order, pressure labels, or burden floor. A named target is an observation anchor, not permission to select a noetic frame.
- `tools/daee_dry_run_emulator.py`: carry the new fields in no-model runs.
- `tools/build_staged_governed_output.py`: consume Stage02 IDs only if release assembly needs them; do not duplicate validation.

### Checkers

- `tools/check_staged_runtime_handshake.py`: validate observation anchors, candidate-state terminal accounting, pressure dispositions, and joins to `B_LA`.
- New `tools/input_observation_units.py`: deterministic source segmentation and anchor verification.
- New `tools/check_input_pressure_coverage.py`: pure reusable validator imported by handshake and runner, avoiding duplicate Stage02 implementations.
- `tools/gen_fixture_mutations.py`: add targeted mutations only after right-reason classification is fixed by Plan 11.

### Fixtures

- Extend `tests/stage-contract-workbench/stage-01-intake/` with observation-manifest valid/invalid fixtures.
- Extend `stage-02-layer-a-diagnostic-ir/` with topology-contract fixtures.
- Add topic-neutral unit tests under `tests/input-pressure-coverage/`.
- Do not encode the fifth smoke's expected burdens.

### Generated files

Never hand-edit `skill/**`. After atomics changes:

```powershell
python tools\build_compiled_runtime.py
python tools\check_compiled_runtime_freshness.py
```

## Required Fixture Lattice

### Valid

1. One observation, one pressure, one burden, one candidate state.
2. Several observation units merge into one burden with a valid merge decision.
3. One observation creates two distinct pressures and two burdens.
4. Context-only unit is explicitly disposed without becoming a burden.
5. Ambiguous input preserves two candidate states, selects one, and holds one with a gate.
6. A routed pressure plus a held pressure yields a non-complete downstream status.
7. Large neutral input with twenty routed burdens, generated mechanically, to prove schema capacity only.
8. Two plausible unknown-pattern-typed candidates, zero selected, truthful HOLD/PARTIAL with a differentiator gate.

### Invalid

1. Source text span omitted from all observation units.
2. Observation anchor hash does not match the source slice.
3. Observation unit has neither pressure nor explicit disposition.
4. Candidate state disappears without selected/held/merged/rejected status.
5. Two pressures map to one burden without a merge decision.
6. `unresolved` pressure coexists with Stage07 `COMPLETE`.
7. Stage02 declares a future MRP-generated burden in `B_LA`.
8. Basis is circular (`merged because same`, `rejected because rejected`).
9. Topic label appears as a required routing key or expected burden count.
10. Named target or lexical token forces a selected frame/owner order without a source-anchored differentiator.

## Test-Driven Implementation Sequence

### Step 1: Freeze current false-pass

Add a copy of the current minimal Stage02 record under a new invalid-v2 fixture with `topology_contract: input-pressure-v1` but no inventory. It must initially pass or fail for the wrong reason, proving the gap.

Baseline command:

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
python tools\check_staged_runtime_handshake.py --records tests\stage-contract-workbench\stage-02-layer-a-diagnostic-ir\minimal-valid\single-burden-floor.json
```

Expected before change: exit 0.

### Step 2: Implement anchor library

Write tests for UTF-8 boundaries, line endings, quotations, nested units, and empty input. Implement deterministic segmentation and anchor validation.

Planned commands:

```powershell
python tools\input_observation_units.py --self-test
python tools\check_input_pressure_coverage.py --self-test
```

Expected after implementation: exit 0.

### Step 3: Integrate Stage02 validator

Import the shared validator into `check_staged_runtime_handshake.py`. Do not fork a second version into the runner.

Full fixture smoke:

```powershell
python tools\check_staged_runtime_handshake.py
```

Expected: exit 0, with all valid and invalid fixtures classified correctly.

Right-reason negative smoke:

```powershell
$p = 'tests\stage-contract-workbench\stage-02-layer-a-diagnostic-ir\invalid\input-pressure-unit-unaccounted.json'
$raw = python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $p
$exit = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($exit -ne 1) { throw "expected checker exit 1, got $exit" }
if ($diag.earliest_stage -ne '02') { throw "wrong earliest stage: $($diag.earliest_stage)" }
if ($diag.failure_class -ne 'stage02-input-pressure-coverage') { throw "wrong class: $($diag.failure_class)" }
```

The exact class string is established in the patch and then pinned by `<fixture-stem>.expectation.json` under Plan A11's `daee-negative-fixture-expectation-v1`; it must not remain a prose placeholder.

```powershell
python tools\assert_expected_rejection.py --expectation tests\stage-contract-workbench\stage-02-layer-a-diagnostic-ir\invalid\input-pressure-unit-unaccounted.expectation.json --artifact-root auto
```

Expected: exit `0`; this helper invocation, not the shorter diagnostic wrapper alone, is the right-reason acceptance gate.

### Step 4: Integrate producer

Modify Stage01/02 prompts to request the new fields and forbid topic-keyed expected topology. The producer must receive the exact raw input and observation manifest.

Self-test:

```powershell
python tools\run_staged_current_skill_smoke.py --self-test
python tools\daee_dry_run_emulator.py --self-test
```

Expected: both exit 0; producer fixtures contain source anchors and terminal pressure dispositions.

### Step 5: Migrate release-bearing fixtures

Migrate Stage07/08 workbench fixtures and five-smoke no-model preflight to require `input-pressure-v1`. Keep historical retained artifacts explicitly legacy.

No-model release gate:

```powershell
python tools\run_no_model_preflight.py --self-test
python tools\run_no_model_preflight.py
```

Expected: all gates pass. This proves structural migration only.

## Semantic Adjudication Gate

A structural coverage proof can still misclassify a material claim as context. Each five-smoke run therefore requires the exact hash-bound `daee-topology-review-v1` artifact defined and owned by Plan A01 at `schema/topology-review.schema.json`. The review binds the case/cycle, exact input, Stage02/04/05 records, Stage07 output, and public witness; identifies the accountable reviewer and relationship to the producer; records challenged unit/pressure/burden/operation IDs and question-level answers; and carries a `PASS`, `FAIL`, or `PARTIAL` verdict plus any owner adjudication. The machine checker validates custody and completeness of this review record. It does not write the review or turn it into semantic truth.

The reviewer may say “U7 contains a distinct source-authentication pressure not carried by B2.” The reviewer may not say “this topic always requires seven burdens.”

Two reviewers may disagree. Disagreement yields `PARTIAL` and an explicit owner-adjudication record; it does not get averaged into PASS. A producer self-review cannot satisfy the independent-review field.

## Five-Smoke Acceptance

For each of the five registered inputs:

- Stage01 observation anchors cover exact input bytes.
- Stage02 accounts for every observation unit.
- Candidate states have terminal statuses.
- Every routed pressure joins `B_LA` exactly once or through a proved merge.
- Held/unresolved pressure prevents false completion.
- Independent topology review passes.

The Torah/Qur'an fifth fixture stores only the exact prompt and neutral observation spans. It stores no expected burden list, submove list, citation list, or response outline.

## Rollback

- Revert the shared validator, schema/fixtures, and producer fields as one coherent change.
- Rebuild generated runtime from reverted atomics.
- Do not delete captured v2-invalid fixtures; move them to a historical gap directory if the contract is abandoned.
- If deterministic segmentation proves unstable across platforms, retain exact input bytes and switch to code-point anchors with a schema version bump; do not silently change offset semantics.

## STOP / ANDON Conditions

Stop if implementation:

- introduces a minimum number of burdens;
- uses topic words to select expected burden IDs;
- treats each sentence as necessarily one burden;
- forces multiple candidate states when one is adequate;
- forces any candidate to `selected` merely because a named target/topic token is present;
- allows an observation unit to disappear without disposition;
- lets unresolved/held pressure coexist with unqualified `COMPLETE`;
- puts generated MRP burdens in Stage02 `B_LA`;
- makes a machine coverage proof claim semantic truth;
- duplicates Stage02 semantic logic in both runner and checker;
- repairs missing pressure inventory after model output instead of failing the producer record.

ANDON record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED
class: source-anchor | candidate-state-loss | pressure-omission | unproved-merge | semantic-adjudication
failing_check: <exact command/review>
owner_source: <file/function/record>
affected_units: [U...]
affected_pressures: [P...]
next_action: <concrete patch or owner decision>
```

## Definition of Done

- Release-bearing Stage02 cannot pass with only a bare burden list.
- Every source observation has a pressure or explicit non-pressure disposition.
- Candidate states terminate visibly, including a valid zero-selected `underdetermined/held` state that forces HOLD/PARTIAL.
- Pressure-to-burden mapping supports arbitrary cardinality without quotas.
- Generated burdens remain Stage05-owned.
- Right-reason fixtures fail at Stage02 with pinned diagnostics.
- Existing Stage01-Stage08 no-model gates pass after migration.
- All five fresh smokes carry the new topology contract and pass independent topology review.
- Verifier/scorecard language remains structural only.

## Confidence

Structural contract and fixtures: YES, implementation-ready.  
Automated semantic completeness: NO, impossible to certify solely from shape.  
Five-smoke topology adequacy: owner/adjudicator-gated until fresh runs exist.
