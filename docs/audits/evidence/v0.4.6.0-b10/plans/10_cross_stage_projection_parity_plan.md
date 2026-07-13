# ANDON A10: Cross-Stage Projection Parity

Priority: P0 Stage06-to-Stage07 false-pass closure  
Implementation target: `C:/Users/theis/Documents/Codex/2026-07-08/dae/work/daee-v46-branch`  
Planned source head: `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Regression status: `unproven`  
Plan status: implementation-ready after coordination with Plans 02, 04, 05, 07, and 09

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Abnormality

The staged handshake can accept a Stage06 witness/NAR record that describes one activation while Stage07 publishes a governed output containing two activations. Both stages can be internally valid, yet the handoff between them is false.

This is not merely a theoretical omission. The checked-in file:

```text
tests/stage-contract-workbench/stage-07-release-output/minimal-valid/complete-closure-single-burden.json
```

has SHA-256:

```text
4F65C4978009D6E836C64F517727501ECB3B11752FFE9961B2D7FF390FA01261
```

It declares:

- one Stage04 ACT row;
- one Stage04 body reference;
- one Stage06 owner activation/body reference;
- `normalized_activation_record: true` rather than a structured Stage06 NAR.

Its Stage07 output points to:

```text
tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/a9-science-source/output.md
```

with SHA-256:

```text
4017E4AFDE38E747BE6BC6A42818DFD2E46138C1D2DB2310F233ABAC84412DD6
```

That output contains:

- two visible ACT rows;
- two public submove bodies;
- two `field_witness.owner_activations[]` objects;
- two `normalized_activation_record.per_burden[]` rows.

The current handshake exits `0` on this record.

## Direct GEMBA Reproduction

### Current checker pass

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
python -B tools\check_staged_runtime_handshake.py --records tests\stage-contract-workbench\stage-07-release-output\minimal-valid\complete-closure-single-burden.json
```

Observed at the planned head:

```text
staged runtime handshake check: PASS
Valid fixtures checked: 25
Invalid fixtures checked: 119
Hosted records checked: 1
```

### Current projection counts

```powershell
@'
import json
from pathlib import Path
import sys
sys.path.insert(0, "tools")
import check_nla_decode_semantic_faithfulness as nla

record_path = Path("tests/stage-contract-workbench/stage-07-release-output/minimal-valid/complete-closure-single-burden.json")
record = json.loads(record_path.read_text(encoding="utf-8"))
stages = {item["id"]: item for item in record["stages"]}
output_path = Path(stages["stage-07-release-output"]["release_output"]["path"])
text = output_path.read_text(encoding="utf-8")
acts, act_errors = nla.parse_act_records(nla.public_execution_text(text))
field_witness, witness_errors = nla.parse_field_witness(output_path, text)
print(json.dumps({
    "stage04_act_rows": len(stages["stage-04-burden-execution-act"]["act_rows"]),
    "stage04_body_refs": len(stages["stage-04-burden-execution-act"]["act_body_refs"]),
    "stage06_owner_activations": len(stages["stage-06-field-witness-nar"]["owner_activations"]),
    "stage06_nar_type": type(stages["stage-06-field-witness-nar"]["normalized_activation_record"]).__name__,
    "stage07_visible_act_rows": len(acts),
    "stage07_owner_activations": len(field_witness["owner_activations"]),
    "stage07_nar_rows": len(field_witness["normalized_activation_record"]["per_burden"]),
    "parse_errors": act_errors + witness_errors
}, indent=2))
'@ | python -B -
```

Observed:

```json
{
  "stage04_act_rows": 1,
  "stage04_body_refs": 1,
  "stage06_owner_activations": 1,
  "stage06_nar_type": "bool",
  "stage07_visible_act_rows": 2,
  "stage07_owner_activations": 2,
  "stage07_nar_rows": 2,
  "parse_errors": []
}
```

The repository remained clean after the read-only reproduction.

## Evidence Classification

### Confirmed

- `stage06_witness_nar_errors()` requires Stage06 `field_witness_body_refs` to equal Stage04 `act_body_refs` and Stage06 `owner_activations` to mirror those refs. That existing control is useful and must remain.
- The same function accepts `normalized_activation_record: true` for non-model modes. It requires a structured object/details only for modes in `MODEL_MODES`.
- The false-pass fixture is release-bearing because it contains Stage07 and Stage08, but its mode is `no-model-fixture`; the boolean therefore passes.
- `stage07_release_errors()` currently receives Stage05 and Stage07, not Stage04 or Stage06. It validates output presence/internal structure and Stage05 terminal-state equality, but it cannot compare Stage06 activations with Stage07 activations.
- `visible_governed_output_errors()` requires a structured NAR inside the Stage07 public `field_witness`; this proves the output has an internal NAR, not that it equals Stage06.
- `retained_parsed_evidence_errors()` performs some Stage04/output and Stage06/output comparisons only when retained `artifact_bindings` are present. The minimal workbench fixture has no such binding, and the comparisons are still count/set-level rather than complete row projection.
- `check_field_witness_convergence.py` and the NLA checker already enforce substantial parity within a single public output. This plan composes them with staged state; it does not replace them.
- Stage04 and Stage06 currently have rich maximal fixtures, including a two-owner structured NAR. The false-pass is therefore a missing release-handshake join, not a lack of all structured examples.

### Inferred

- Similar mismatches can hide missing owners, extra generated activations, changed operations/deltas, or NAR drift even when cardinalities happen to match.
- A boolean or heading-only Stage06 witness encourages endpoint validation rather than trajectory validation.
- A harness can appear green while Stage07 reconstructs a different execution than Stage04-06 actually declared.

### Unproven

- This false-pass caused any disputed external model output.
- v46 introduced the underlying weakness; branch attribution requires PR-base comparison.

### Rejected and non-claims

- Exact structural parity does not prove semantic sufficiency, theological truth, faithful source use, or uptake.
- No fixed number of ACTs, burdens, submoves, or bytes is accepted as correct for all inputs or as a smoke PASS condition.

## Architectural Requirement and Formal-Chain Location

The failure occurs across this portion of the required chain:

```text
Bn -> {Bn_i[OP_i]} -> Land(Bn) -> Delta/Delta-kappa
   -> div/curl -> LoopBreak -> R(H,Delta) -> C(PsiN)
   -> public reconstruction -> T_lang
```

Stage04 records the operation-bearing submoves. Stage05 records the post-Land reread, graph consequence, generated/held state, and terminal result. Stage06 must encode the same trajectory into owner activations and NAR. Stage07 must publish the same operations, bodies, graph, and terminal state. Stage08 may bind and replay that publication.

The implementation requirement is therefore:

> Every release-bearing Stage07 projection must be a count-exact, identity-exact, order-governed projection of the validated Stage02-06 state. No stage may gain, lose, relabel, merge, or repair an activation merely to make the public output look complete.

This does not require one ACT per burden. Several owner operations may land one burden; one operation may be sufficient for a genuinely atomic burden. Cardinality follows the runtime topology and owner obligations established by Plans 02-05.

## Five Whys

1. Why does the current mismatched fixture pass?  
   Stage04-to-Stage06 body references are compared, and Stage07 output is validated internally, but Stage06 activation rows are not compared with Stage07 visible/machine activation rows.

2. Why is the cross-stage comparison absent?  
   `stage07_release_errors()` is passed only Stage05 and Stage07. Its API cannot inspect Stage04 ACT identity or Stage06 owner/NAR identity.

3. Why did retained evidence not close the gap?  
   Richer parsed-evidence comparisons are conditional on retained `artifact_bindings`. Minimal/maximal workbench records can reach Stage07 without that path, and the retained checks do not compare every activation field.

4. Why can Stage06 use a boolean at all?  
   Boolean/string shorthands were retained for legacy and stage-local fixtures, while strictness was keyed to `mode` rather than to whether the record is release-bearing.

5. Why is this a systemic false-pass rather than one bad fixture?  
   There is no single canonical projection object or fingerprint joined across Stage04 ACT, Stage05 route/terminal state, Stage06 owner/NAR, and Stage07 visible/public-graph output. Each endpoint can be green over a different latent execution.

Root owner/source: the cross-stage composition layer in `tools/check_staged_runtime_handshake.py`, using existing parsers from `check_nla_decode_semantic_faithfulness.py`, current convergence logic, the staged producer/assembler, and Stage04-07 fixture families.

## Hansei

### What already works

- Stage04 body refs are ordered and tied to canonical ACT rows in the runner.
- Stage06 refs already mirror Stage04 refs.
- Model-mode Stage06 already requires structured NAR or details.
- Stage07 already requires a structured NAR in the public graph.
- The NLA checker already parses ACT rows and compares public ACT fields to `field_witness.owner_activations[]`.
- The convergence checker already requires NAR rows to match owner activations, MRP resultants, terminal states, and generated depth inside the output.
- Retained artifact binding already compares some staged and public projections.
- The checker has a first-failed-stage diagnostic mechanism and stable failure classes.

### What failed

- Existing checks were composed as parallel endpoint checks rather than one end-to-end projection contract.
- `mode=no-model-fixture` was treated as a reason to allow a boolean NAR even after the record crossed into release.
- Set comparisons erased multiplicity and order, which matter when several owners act on one burden.
- A fixture named `minimal-valid` was accepted because each local field was legal, despite referencing a richer output.
- Expected-invalid metadata often proved only that some checker failed, not that the intended handoff failed for the intended reason.

### Learning

The public output must be derived evidence over staged state, not a separately plausible answer. Structural parity must compare ordered activation identities and lifecycle transitions, not merely headings, burden sets, or nonempty lists. Right-reason failure classification is part of the contract.

## Target Contract

### 1. Release-bearing predicate

Define one shared function:

```text
release_bearing(record) = Stage07 is present OR Stage08 is present
```

For a release-bearing record:

- `normalized_activation_record` at Stage06 must be an object, not `true`;
- `normalized_activation_record_details` may be accepted only as a legacy alias and must be exactly equal to the canonical object; new producers emit only the canonical object;
- `owner_activations` must be an object list carrying full projection fields, not body-ref strings;
- `owner_activation_details` must not become an independent second master. If retained during migration, it must be exactly equal by normalized row identity;
- Stage06 `field_witness_body_refs` remains an ordered list exactly matching Stage04 refs;
- any shorthand is allowed only for an explicitly Stage06-local record whose `stage_scope.stop_after_stage` is Stage06 and whose `stage_scope.not_release_output` is `true`. It can never be promoted.

### 2. Canonical activation projection

Add a pure shared projection module, recommended path:

```text
tools/stage_projection_contract.py
```

It must reuse existing parsers and normalizers rather than introducing new regex grammars:

- `check_nla_decode_semantic_faithfulness.parse_act_records`;
- `parse_field_witness`;
- `canonical_activation_from_record`;
- `graph_burden_id` and `graph_submove_id`;
- current body-ref normalization from the capsule checker/runner, refactored into one shared helper if necessary;
- current owner-family and controlled delta-result rules;
- current field-witness convergence functions for internal public-output checks.

Each normalized activation row contains:

```json
{
  "ordinal": 0,
  "body_ref": "B1_1",
  "burden_id": "B1",
  "source_event": "B1 | MRP(B1)",
  "target_burden": "B1",
  "owner_id": "source-status-repair",
  "operation": "source-order",
  "pressure": "scientific-explanations-only-knowledge-source",
  "register_axis": "xi",
  "delta_result": "science-source-bounded",
  "land": "Land(B1)+",
  "mrp_route_result_type": "no_new_resultant",
  "terminal_state": "landed",
  "generation_depth": 0,
  "ordering_role": "required",
  "ordering_group": null
}
```

Fields not present at one stage are joined from the stage that owns them; they are never guessed from prose. Missing owner-required data yields an error, not an empty string that happens to hash.

### 3. Activation parity invariants

For every release-bearing record:

| Source | Required parity |
| --- | --- |
| Stage04 `act_rows` | Parse to exactly one canonical row per visible operation obligation worked at Stage04 |
| Stage04 `act_body_refs` | Equal the canonical ACT body refs in order; no duplicates |
| Stage06 `field_witness_body_refs` | Equal Stage04 refs in order |
| Stage06 `owner_activations` | Equal Stage04 activation identities, count-exact and field-exact |
| Stage06 NAR `per_burden[]` | ACT-level rows; equal Stage06 activations for owner, operation, delta, burden, route type, terminal state, depth |
| Stage07 visible ACT rows | Equal the Stage04/06 canonical rows; no added or dropped operation |
| Stage07 `field_witness.owner_activations[]` | Equal visible ACT rows and Stage06 rows |
| Stage07 public NAR | Equal Stage06 NAR and public owner activations |

Do not compare these as sets. Two activations on one burden are distinct. Duplicate rows remain observable.

### 4. Ordering parity

Use the existing `owner_activation_ordering` contract:

- `required` rows preserve exact order;
- `parallel` rows may vary only inside an explicitly declared, identical ordering group;
- a canonical fingerprint sorts rows inside a verified parallel group by normalized row identity before hashing;
- `contingent`, `optional_non_load_bearing`, and `hold_partial` rows retain their controlled disposition and trigger/gate;
- an undeclared reorder is a parity failure, not harmless prose variation.

### 5. Lifecycle and graph parity

Activation parity alone is insufficient. Join Stage05-07 for:

- `B_LA`, `B_MRP`, and ordered `B_total`;
- generated burden ID, parent/source MRP event, generation depth, route result, owner execution or HOLD/PARTIAL state;
- held burden activation versus newly generated burden instantiation;
- explicit pre-empted candidate and non-instantiation basis when that contract is added by Plan 07;
- per-burden reread route result;
- dependency graph edges and roots;
- terminal states;
- divergence/curl/LoopBreak state;
- closure claim and held/live remainder.

An unexecuted held burden does not need a fabricated ACT row. It needs a lifecycle projection with gate and next action. A generated burden that executes does need activation rows. This avoids using activation count as a universal burden count.

### 6. Projection fingerprints and audit binding

Compute canonical JSON hashes over normalized projections:

```text
stage04_activation_projection_sha256
stage06_activation_projection_sha256
stage07_activation_projection_sha256
stage05_lifecycle_projection_sha256
stage07_lifecycle_projection_sha256
```

Stage07 cannot pass unless the corresponding hashes agree. Stage08's `field_witness_envelope`/binding record from Plan 09 records the final hashes. Hash equality proves normalized structural equality only; it does not prove body sufficiency or semantic truth.

### 7. Stable diagnostic class

Use one failure class with stage-accurate subcodes. A release-bearing boolean Stage06 NAR is rejected at Stage06 before Stage07 is evaluated. A fully structured Stage06 record that first diverges from Stage07 is rejected at Stage07. Do not assign the composite specimen's earliest defect to every projection failure.

| Single-signature defect | `failure_class` | `failure_subcode` | `earliest_stage` | `downstream_invalidated` |
| --- | --- | --- | --- | --- |
| release-bearing Stage06 boolean/string shorthand | `projection-parity` | `projection-parity-boolean-nar-release` | `06` | `['07','08']` |
| Stage04 and Stage06 each contain two matching structured activations, while Stage07 publishes one | `projection-parity` | `projection-parity-activation-count` | `07` | `['08']` |

Diagnostics must include the first normalized row difference and only the stages downstream of the earliest failed boundary. Required subcodes:

```text
projection-parity-boolean-nar-release
projection-parity-activation-count
projection-parity-body-ref
projection-parity-owner-operation
projection-parity-pressure-delta
projection-parity-route-terminal-depth
projection-parity-ordering
projection-parity-lifecycle
projection-parity-graph
```

The classifier must special-case this handoff before generic stage substring classification so it does not report a misleading Stage01/03/05 error from unrelated fixture defects.

## Exact Owner and Edit Map

### Add

- `tools/stage_projection_contract.py`: pure normalization, projection, fingerprint, and difference functions.
- `tools/check_stage_projection_parity.py`: CLI/self-test wrapper over the pure module; no independent parser.
- `schema/stage-projection.schema.json`: closed normalized projection shape and versioned source of truth for projection sidecars.
- `tests/stage-projection-parity/valid/compact-single-activation/`.
- `tests/stage-projection-parity/valid/multi-owner-single-burden/`.
- `tests/stage-projection-parity/valid/generated-and-held-mixed-lifecycle/`.
- Invalid fixtures for every diagnostic subcode.
- `docs/stage06-stage07-projection-parity.md`.

### Modify

- `tools/check_staged_runtime_handshake.py`:
  - pass Stage02, Stage04, Stage05, and Stage06 into Stage07 parity validation;
  - add the release-bearing predicate;
  - require structured Stage06 rows for release;
  - invoke the shared projection module;
  - add `projection-parity` classification and right-reason explanation.
- `tools/run_staged_current_skill_smoke.py`:
  - emit canonical structured Stage06 activation/NAR data;
  - derive projection fingerprints after validation;
  - fail on mismatch before Stage07/08;
  - never normalize a mismatch into agreement after model output.
- `tools/build_staged_governed_output.py`:
  - consume the validated projection when assembling public sections;
  - do not reparse or repair owner identity independently.
- `tools/check_nla_decode_semantic_faithfulness.py`: expose stable pure parse/projection helpers if needed; preserve its bounded semantic-facet scope.
- `tools/check_field_witness_convergence.py`: expose or reuse normalized public-row projection; do not duplicate cross-stage logic.
- `tools/check_state_capsule.py` and capsule emission only if body-ref normalization is extracted to a shared primitive. Preserve capsule-specific replay semantics.
- `tools/gen_fixture_mutations.py`: after the right-reason mutation framework is fixed, add targeted cardinality/identity mutations with expected class, not any-nonzero success.
- `tools/run_local_ci.py` and `tools/ci_registry.json`: add deterministic projection self-tests and handshake fixtures.
- `atomics/skill/references/rubrics/manual-contract-digest.md`, `non-droppable-manual-contract.md`, and `output-release.md`: compactly state that release-bearing Stage06 NAR is structured and Stage07 is an exact projection. Do not re-inline checker internals.
- `docs/execution-spine.md`, `docs/stage-contract-workbench.md`, `docs/recursive-state-capsule.md`, and `docs/non-claims.md`.

### Repair or reclassify current fixtures

- Preserve the current `1/1/bool -> 2/2/2` false-pass as `tests/stage-contract-workbench/historical-composite/stage06-boolean-plus-stage07-cardinality-false-pass.json` with a hash/census metadata sidecar. It is not an active right-reason fixture because the Stage06 shorthand defect masks the Stage07 cardinality defect.
- Add two minimal active invalid fixtures:

```text
tests/stage-contract-workbench/stage-06-field-witness-nar/invalid/release-bearing-boolean-nar.json
tests/stage-contract-workbench/stage-06-field-witness-nar/invalid/release-bearing-boolean-nar.expectation.json
tests/stage-contract-workbench/stage-07-release-output/invalid/stage06-stage07-activation-cardinality-mismatch.json
tests/stage-contract-workbench/stage-07-release-output/invalid/stage06-stage07-activation-cardinality-mismatch.expectation.json
```

  The cardinality fixture must be clean through Stage06: Stage04 has two ACT rows, Stage06 has two matching structured owner-activation/NAR rows, and Stage07 publishes exactly one. Its only intentional defect is the Stage06-to-Stage07 row loss.

- Repair `minimal-valid/complete-closure-single-burden.json` so its Stage03 owner routes, Stage04 two ACT rows, Stage06 two structured owner activations, and Stage06 two NAR rows match the referenced `a9-science-source` output. Alternatively point it to a new genuinely one-activation output; do not call a two-activation artifact "minimal" while declaring one activation.
- Reclassify `stage-06-field-witness-nar/minimal-valid/boolean-nar-single-owner.json` as Stage06-local only by removing Stage07/08 and adding explicit `stage_scope.stop_after_stage=stage-06-field-witness-nar` plus `not_release_output=true`; or convert it to structured NAR. It may not remain release-bearing with a boolean.
- Keep `maximal-valid/structured-nar-multi-owner-nframe-details.json` as a positive seed, but remove duplicate canonical/details masters after migration.
- Migrate current Stage07/08 valid fixtures to structured release projections.

### Generated files not to hand-edit

- `skill/**`.
- Generated docs portal/index artifacts.
- Package archives, package inventories, and ignored `.daee` run artifacts.

## Required Fixture Lattice

### Valid

1. One burden, one owner activation, one structured NAR row, one public ACT.
2. One burden, two distinct owner operations, two ordered ACT/NAR/public rows.
3. Several burdens with different activation counts derived from owner obligations.
4. Explicit parallel owner group with stable group-normalized fingerprint.
5. Generated burden with MRP source, operation rows, generation depth, and terminal state.
6. Held burden with no fabricated ACT and an explicit gate/next action.
7. Pre-empted candidate with no fabricated node/ACT and a non-instantiation basis.
8. Compact complete output whose small topology is fully reconstructible.
9. Large arbitrary-topology fixture generated by Plan A15/file 15, with parity at every join. Its size/count is capacity evidence only.

### Invalid

1. Release-bearing Stage06 boolean NAR.
2. Stage04 has two ACT rows; Stage06 has one.
3. Stage06 has two rows; Stage07 visible output has one.
4. Counts match but one body ref differs.
5. Counts/body refs match but owner or operation differs.
6. Pressure or delta changes between Stage04, Stage06, and Stage07.
7. Stage05 route/terminal/depth differs from NAR.
8. Generated burden exists in Stage05 but is absent from Stage07 graph.
9. Held burden is converted into a generated burden or silently closed.
10. Required rows reorder without declared parallel grouping.
11. Public ACT and public `owner_activations` agree with each other but both disagree with Stage06.
12. Projection hashes are copied/model-authored rather than recomputed.

## Test-Driven Implementation Sequence

### Phase 0: Preserve the current false-pass

Run the two Direct GEMBA commands above and record:

- planned head;
- both fixture hashes;
- checker exit `0`;
- the `1/1/bool -> 2/2/2` count mismatch.

Also record clean state:

```powershell
git status --short --branch --untracked-files=all
```

STOP if any source or fixture has drifted. Do not reconstruct the old result from memory.

### Phase 1: Add the red fixture and expected reason

1. Preserve the original composite specimen and its hashes outside active right-reason coverage.
2. Derive the Stage06 boolean fixture by repairing every other defect and retaining only release-bearing shorthand.
3. Derive the Stage07 cardinality fixture by making Stage04 and Stage06 structured and equal at cardinality two, then deleting exactly one Stage07 projected activation.
4. Add canonical Plan A11 expectation sidecars. The Stage07 fixture expectation is:

```json
{
  "schema": "daee-negative-fixture-expectation-v1",
  "fixture": "stage06-stage07-activation-cardinality-mismatch.json",
  "kind": "invalid-single-signature",
  "expected_checker_id": "staged-runtime-handshake",
  "expected_exit_category": "structural-rejection",
  "expected_exit_code": 1,
  "expected_earliest_stage": "07",
  "expected_failure_class": "projection-parity",
  "expected_failure_subcode": "projection-parity-activation-count",
  "expected_downstream_invalidated": ["08"],
  "forbidden_artifacts": ["stage08-record.json", "promotion-verdict.json"]
}
```

5. The Stage06 shorthand expectation pins `expected_earliest_stage: '06'`, subcode `projection-parity-boolean-nar-release`, downstream `['07','08']`, and the same forbidden artifacts.
6. Before implementing, verify each minimal fixture unexpectedly passes or fails for the wrong reason. Record each independently as RED. A rejection of the composite specimen alone is not sufficient.

### Phase 2: Build the pure projection core

Implement projection from in-memory Stage04/05/06 objects and from Stage07 output using existing parsers.

```powershell
python -B tools\check_stage_projection_parity.py --self-test
```

Expected after implementation: exit `0`; pure tests cover Unicode/ASCII body-ref equivalence, duplicate rows, required order, parallel grouping, generated/held lifecycle, and fingerprint determinism.

The self-test must not write fixtures, repair outputs, or invoke a model.

### Phase 3: Wire the handshake and right-reason classifier

```powershell
$fixture = 'tests\stage-contract-workbench\stage-07-release-output\invalid\stage06-stage07-activation-cardinality-mismatch.json'
$raw = python -B tools\check_staged_runtime_handshake.py --explain-stage-failure --records $fixture
$exit = $LASTEXITCODE
$diagnostic = $raw | ConvertFrom-Json
if ($exit -ne 1) { throw "expected checker exit 1, got $exit" }
if ($diagnostic.earliest_stage -ne '07') { throw "expected earliest_stage 07, got $($diagnostic.earliest_stage)" }
if ($diagnostic.failure_class -ne 'projection-parity') { throw "expected projection-parity, got $($diagnostic.failure_class)" }
if ($diagnostic.failure_subcode -ne 'projection-parity-activation-count') { throw "wrong subcode: $($diagnostic.failure_subcode)" }
if (($diagnostic.downstream_invalidated -join ',') -ne '08') { throw 'wrong downstream invalidation set' }
if (Test-Path -LiteralPath 'tests\stage-contract-workbench\stage-07-release-output\invalid\promotion-verdict.json') { throw 'invalid fixture produced a promotion artifact' }
```

Run both canonical expectations:

```powershell
python tools\assert_expected_rejection.py --expectation tests\stage-contract-workbench\stage-06-field-witness-nar\invalid\release-bearing-boolean-nar.expectation.json --artifact-root auto
if ($LASTEXITCODE -ne 0) { throw 'Stage06 shorthand expectation failed' }
python tools\assert_expected_rejection.py --expectation tests\stage-contract-workbench\stage-07-release-output\invalid\stage06-stage07-activation-cardinality-mismatch.expectation.json --artifact-root auto
if ($LASTEXITCODE -ne 0) { throw 'Stage07 cardinality expectation failed' }
```

Expected: both single-signature wrappers exit `0`; each uses a helper-owned unique scratch root and neither creates Stage07/08 or promotion evidence beyond its earliest rejected boundary.

Then run:

```powershell
python -B tools\check_staged_runtime_handshake.py
```

Expected: exit `0`; all valid fixtures pass, all invalid fixtures fail, and no registered invalid is `unclassified`.

### Phase 4: Repair valid fixtures and shorthand scope

1. Repair the current Stage07 minimal fixture to match its referenced output.
2. Make every release-bearing Stage06 fixture structured.
3. Restrict any retained boolean shorthand to explicit Stage06-local/no-release scope.
4. Add near-miss fixtures where row counts match but identity differs.

```powershell
python -B tools\check_stage_projection_parity.py --records tests\stage-contract-workbench\stage-07-release-output\minimal-valid\complete-closure-single-burden.json
python -B tools\check_staged_runtime_handshake.py --records tests\stage-contract-workbench\stage-07-release-output\minimal-valid\complete-closure-single-burden.json
```

Expected: both exit `0` and report two matched activation rows for the retained A9 output.

### Phase 5: Producer and assembler adoption

1. Stage06 prompt requests the canonical structured object.
2. Runner validates it before Stage07.
3. Stage07 assembler receives the validated projection and emits matching public rows.
4. A mismatch stops with preserved raw response/record; no normalizer adds, drops, or rewrites owner rows to force agreement.
5. Projection hashes are checker-authored after validation.

```powershell
python -B tools\run_staged_current_skill_smoke.py --self-test
python -B tools\daee_dry_run_emulator.py --self-test
python -B tools\build_staged_governed_output.py --self-test
```

Expected: every command exits `0`; `build_staged_governed_output.py --self-test` is present at the inspected PR9 head.

### Phase 6: Public-output validators and witness binding

```powershell
python -B tools\check_manual_smoke_render_contract.py
python -B tools\check_field_witness_convergence.py
python -B tools\check_nla_decode_semantic_faithfulness.py
python -B tools\check_owner_activation_ordering.py
python -B tools\check_state_capsule.py --self-test
python -B tools\check_field_witness_binding.py
```

Expected: exit `0`. These checks retain their bounded claims. The projection checker adds cross-stage equality; it does not turn NLA or convergence into a universal semantic grader.

### Phase 7: Full deterministic preflight

```powershell
python -B tools\build_compiled_runtime.py
python -B tools\check_compiled_runtime_freshness.py
python -B tools\run_no_model_preflight.py --self-test
python -B tools\run_no_model_preflight.py
```

Expected: all deterministic gates exit `0`. A green no-model preflight is not a five-smoke model result.

## Stage01-Stage08 Effects

| Stage | Projection obligation introduced or consumed |
| --- | --- |
| 01 | Input hash/case identity only; no operation rows invented |
| 02 | Candidate frame, live registers, input pressures, and burden floor from Plan 02 become projection roots |
| 03 | Owner routes and split/merge decisions define eligible operation obligations |
| 04 | Canonical ACT rows/body refs become the activation source of truth |
| 05 | MRP route, generated/held/pre-empted lifecycle, graph delta, and terminal state are joined to activation rows |
| 06 | Structured owner activations and NAR must exactly encode Stage04/05 state |
| 07 | Visible ACT/body/witness/public graph must exactly project Stage06 and preserve Plan 09 terminal order |
| 08 | Checker-owned envelope/binding records projection hashes and may promote only structurally green artifacts |

No later stage is permitted to repair an earlier omission. If Plan 02 finds that the burden universe was under-inventoried, projection parity over the smaller universe is still insufficient and the run remains invalid.

## Five-Smoke Acceptance

The five required cases are:

```text
gate88-secularism
gate88-khaybar
gate88-trinitarian-j173
gate88-tst-lillard
gate88-torah-quran-source-authentication
```

For every fresh case:

- Stage04, Stage06, and Stage07 activation projection hashes agree.
- Stage05 and Stage07 lifecycle/graph projection hashes agree.
- Every distinct runtime-derived owner obligation is executed or explicitly disposed under the relevant plan.
- Generated, held, and pre-empted states remain distinguishable.
- Stage07 follows the terminal order in Plan 09.
- Stage08 stores the parity verdict and artifact hashes.
- Any mismatch is a one-shot STOP for that case; no averaging across cases and no automatic repair/retry.
- A structural PASS does not certify the theological answer, factual sources, semantic completeness, or uptake. Independent topology/body/semantic review remains required.

The Torah/Qur'an fixture contains only the exact user-supplied input and custody metadata. It must not contain expected burden IDs, owner routes, submove counts, quotations, citations, response text, or a golden conclusion.

## Rollback

- Add the pure projection checker and fixtures before changing producer behavior, so rollback can return to observation without losing the false-pass canary.
- Revert handshake integration, runner adoption, and atomics as one coherent compatibility unit.
- Rebuild generated runtime after reverting atomics; never hand-edit `skill/**`.
- Preserve the invalid cardinality fixture and its hash even if the implementation approach changes.
- Do not rewrite retained public outputs. If a retained case cannot satisfy the new release-bearing contract, mark it legacy/known-contract-drift and remove current-promotion eligibility.
- If shared normalizer extraction destabilizes capsule replay, revert the extraction but keep equivalent behavior covered by cross-module tests; do not weaken parity to make the refactor pass.
- Projection verdicts and captured run artifacts are append-only evidence.

## STOP / ANDON Conditions

Stop and record an ANDON if implementation:

- compares activation rows as sets and loses duplicates/order;
- adds a universal ACT/submove/burden/byte minimum;
- allows release-bearing boolean NAR;
- trusts a model-authored projection hash or `validated=true` field;
- repairs Stage06/07 mismatch after the response rather than rejecting it;
- requires an ACT for a legitimately held/unexecuted burden instead of lifecycle accounting;
- collapses held and generated burdens;
- lets a public output agree internally while disagreeing with Stage06;
- introduces a second ACT/field-witness parser rather than reusing current parsers;
- reports any-nonzero fixture rejection as right-reason success;
- upgrades structural equality to semantic truth, source provenance, or uptake;
- advances `regression_status` beyond `unproven`;
- runs model smokes or performs package/issue/commit/push/tag/release/publication actions without authorization.

ANDON record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED
class: projection-parity | boolean-nar-release | activation-identity | lifecycle-parity | graph-parity | checker-classification
failing_check: exact command and exit
earliest_stage: '06 | 07'
failure_subcode: exact stable token
first_difference: normalized path/value pair
owner_source: exact file/function/fixture
affected_case_ids: []
preserved_hashes: []
next_action: one concrete patch or owner decision
regression_status: unproven
```

## Definition of Done

- The confirmed `1/1/bool -> 2/2/2` record is preserved as a historical composite specimen and is never counted as single-signature right-reason coverage.
- The isolated release-bearing boolean NAR fixture fails at Stage06 with subcode `projection-parity-boolean-nar-release` and invalidates only Stages07-08.
- The isolated structured cardinality fixture is valid through Stage06, fails first at Stage07 with subcode `projection-parity-activation-count`, and invalidates only Stage08.
- No release-bearing record accepts boolean NAR or string-only owner activations.
- Stage04, Stage06, and Stage07 activation rows are count-exact, identity-exact, and order-governed.
- Stage05 and Stage07 generated/held/pre-empted lifecycle, graph, route, and terminal state are parity-checked.
- Public ACT, public graph owner activations, public NAR, and staged NAR share one canonical projection/fingerprint.
- Existing NLA, convergence, owner-ordering, capsule, and retained-binding controls are reused and remain green.
- Every negative fixture fails for its registered class and earliest stage.
- No checker uses output length or fixed cardinality as a pass condition.
- Deterministic Stage01-Stage08 workbench, generated-runtime freshness, and no-model preflight pass.
- After all related ANDON plans are implemented, all five fresh smokes traverse Stage01-Stage08 with parity verdicts and independent human review.
- Structural PASS remains structural; regression causality remains unproven.

## Confidence

Confirmed false-pass reproduction: HIGH.  
Checker/fixture implementation plan: YES, implementation-ready.  
Producer migration: PARTIAL until coordinated with Stage02-05 contract patches.  
Semantic adequacy and model behavior: owner/reviewer-gated and unproven.  
v46 regression causality: NO, unproven.
