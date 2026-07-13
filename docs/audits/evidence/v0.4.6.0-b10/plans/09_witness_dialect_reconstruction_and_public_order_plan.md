# ANDON A09: Witness Dialect, Reconstruction, and Public Order

Priority: P0 contract-identity and release-integrity fix  
Implementation target: `C:/Users/theis/Documents/Codex/2026-07-08/dae/work/daee-v46-branch`  
Planned source head: `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Regression status: `unproven`  
Plan status: implementation-ready for an additive contract split; retained-artifact migration remains owner-gated

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Abnormality

The current tree uses the name `field_witness` for two incompatible machine objects:

1. The public graph/reconstruction witness required by the runtime and emitted after the human Closure/Reconstruction Witness. Its live keys include `B_LA`, `B_MRP`, `B_total`, `nodes`, `edges`, generated-burden provenance, MRP resultants, owner activations, NAR, and coverage proof.
2. The audit/reconstruction envelope defined by `schema/field-witness.schema.json` and `tools/check_ir_instance_integrity.py`. Its required top-level keys are `route_gradient`, `burden_events`, `field_diagnostics`, `loopbreak`, `reconstruction`, `closure`, `transfer_boundary`, `register_deltas`, `non_claims`, `provenance`, and `coverage_proof`.

Both are useful. Neither is a substitute for the other. The defect is the shared name and the absence of a typed bridge between them.

The tree also contains an incomplete public-order control. The intended order is now owner-set and must be canonical everywhere:

```text
Restorative Response
-> Closing Formulation
-> Closure/Reconstruction Witness
-> final parser-stable field_witness
```

The current checker already enforces most of that sequence. It rejects Closing Formulation before Restorative Response, rejects the Closure/Reconstruction Witness before Closing Formulation, and rejects an inline `field_witness` before Closing Formulation. It does not require the Closure/Reconstruction Witness to precede `field_witness`, and it does not prove that an inline `field_witness` is the final public artifact.

## Direct GEMBA Evidence

### Confirmed

- `atomics/skill/references/rubrics/output-release.md` states that the Closure/Reconstruction Witness is the human-readable proof ledger and `field_witness` is the machine-readable graph/reconstruction payload. It gives the intended final sequence at lines 846-857 and the public graph key family at lines 895-933.
- `atomics/skill/references/rubrics/manual-contract-digest.md` and `non-droppable-manual-contract.md` already carry `Restorative Response -> Closing Formulation -> Closure/Reconstruction Witness -> field_witness`.
- The worked example in `diagnostic-render-contract.md` renders the intended order.
- `diagnostic-render-contract.md` still says Closing Formulation is required "at the very end." `output-release.md` separately says Closing Formulation appears "at the end." Those phrases conflict with their own later proof-tail law.
- The North Star document lists Closure/Reconstruction Witness, then final Restorative Response, then Closing Formulation. The Rebake's NLA chain and current runtime digest use the owner-required order above. The architecture documents therefore disagree.
- `schema/field-witness.schema.json` is an audit-envelope key contract, while ordinary governed outputs such as the retained `a9-science-source/output.md` carry the public graph object.
- `tools/check_field_witness_binding.py` passes because it checks the audit-envelope schema against `FIELD_WITNESS_KEYS` and standalone audit-envelope fixtures. It does not validate the public graph dialect emitted by ordinary governed output.
- `tools/closure_witness_lib.py`, `tools/check_manual_smoke_render_contract.py`, and `tools/check_field_witness_convergence.py` already provide substantial public-graph and visible-witness validation. This plan preserves and composes those controls.
- `tools/build_field_witness_envelope.py` already creates `field-witness-artifact-binding-v1` hash projections. It is an implemented binding primitive, not evidence that the dialect collision is solved.
- `schema/state-capsule.schema.json` and `tools/check_state_capsule.py` already define a distinct `daee-state-capsule-v1` object for cross-call state. The capsule must remain distinct from both public witness and audit envelope.

### Confirmed order false-pass

At the planned head, this read-only in-memory mutation moved the complete public `field_witness` before the Closure/Reconstruction Witness while leaving it after Closing Formulation:

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
@'
from pathlib import Path
import sys
sys.path.insert(0, 'tools')
import check_manual_smoke_render_contract as c
p = Path('tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/a9-science-source/output.md')
t = p.read_text(encoding='utf-8')
closure_at = t.index('Closure/Reconstruction Witness')
field_at = t.index('field_witness', closure_at)
mutated = t[:closure_at] + t[field_at:] + '\n\n' + t[closure_at:field_at]
errors = c.check_text(p, mutated, True)
print('MUTATED_ORDER_ERROR_COUNT=' + str(len(errors)))
for error in errors:
    print(error)
'@ | python -B -
```

Observed result: exit `0`, `MUTATED_ORDER_ERROR_COUNT=0`. This is a current structural false-pass. It proves an order-check gap; it does not prove that this gap caused the disputed model output.

### Inferred

- A shared label can cause a producer, checker, or reviewer to validate one dialect while believing it validated the other.
- Stale "very end" wording can pull a producer toward omitting or misordering the proof tail.
- The collision may amplify proof-looking but unreconstructible output when a model preserves labels while dropping object identity.

### Unproven

- The dialect collision caused the Grok specimen or any v45/v46 behavioral difference.
- Whether renaming artifacts, without the projection checks in Plan 10, would improve semantic adequacy.
- A structurally valid witness proves theological truth, interlocutor uptake, guidance, or release provenance.
- Whether PR9 introduced the underlying collision. Any PR9 attribution must use `56d023e... -> 6987c9e...`; the verified main -> PR8 -> PR9 stack must be inspected rather than inferred from the shallow clone.

## Architectural Requirement and Formal-Chain Location

The witness family serves three different points in the formal chain and must not collapse them:

```text
IR -> route-gradient -> Bn -> {Bn_i[OP_i]} -> Land(Bn) -> Delta
   -> div/curl -> LoopBreak -> R(H,Delta) -> C(PsiN) -> T_lang
```

| Artifact | Formal role | Stage owner | May claim | Must not claim |
| --- | --- | --- | --- | --- |
| `state_capsule` | Carries the currently accumulated internal execution state between bounded calls | Stages 01-07; capsule schema/checker | Structural continuity, append-only ledgers, current terminal/held state | Public reconstruction, semantic correctness, actual prompt uptake unless transport is separately proven |
| `field_witness` | Public machine graph of the executed trajectory from initial burdens through operations, rereads, graph deltas, and closure | Stage06 prepares; Stage07 publishes | Parser-stable public trajectory and parity with visible witness | Audit custody, package provenance, semantic truth |
| `field_witness_envelope` | Audit/replay record that binds route, events, diagnostics, reconstruction, provenance, coverage, and hashes to the public witness/output | Stage08/checker-owned | Structural audit and artifact binding under an explicit proof class | Replacement of the public graph, fresh generation, release, or uptake |

The OSM paper is relevant only by analogy: an endpoint can look correct while the state trajectory differs. It does not prove these contracts, prescribe output length, or validate DAEE semantics.

## Five Whys

1. Why can two incompatible objects both be called `field_witness`?  
   The public graph lane and the audit/IR-integrity lane evolved independently and retained the same historical label.

2. Why did existing checks not reject the collision?  
   Each checker is internally green over its own fixture family. `check_field_witness_binding.py` validates audit-envelope keys; manual/convergence checkers validate public graph content. No checker asserts that the names, schema IDs, parser entry points, and artifact roles are mutually exclusive.

3. Why is public order only partly enforced?  
   The proof tail was added after older prose had already called Closing Formulation "final" or "at the very end." The checker was hardened incrementally around known misorders but never acquired one canonical terminal-section state machine.

4. Why can a green output still place `field_witness` before the human witness?  
   `check_field_witness_contract()` compares `field_witness` only with Closing Formulation, while the separate closure-order check compares Closure/Reconstruction Witness only with Closing Formulation. The two comparisons are not joined.

5. Why could the namespace/order collision survive multiple checker additions?  
   Witness schemas and checkers evolved under separate artifact owners, with no canonical role registry or terminal-sequence state-machine owner required by promotion. Local pairwise validity therefore never had to prove global role exclusivity and order.

Severity: Stage06, Stage07, Stage08, Output Grapher, NAR replay, and retained custody consume different witness roles. Without explicit types and order, a later proof surface can be accepted without reconstructing the same earlier trajectory.

Root owner/source: the witness artifact namespace and terminal render contract, principally `atomics/skill/references/rubrics/{output-release,diagnostic-render-contract,manual-contract-digest,non-droppable-manual-contract}.md`, `schema/field-witness.schema.json`, `tools/{closure_witness_lib,check_manual_smoke_render_contract,check_ir_instance_integrity,check_field_witness_binding,build_field_witness_envelope,check_field_witness_convergence}.py`, and their Stage06-08 consumers.

## Hansei

### What already works

- The public runtime distinguishes the human Closure/Reconstruction Witness from machine `field_witness` in prose.
- Public graph validation already covers burden ledgers, graph nodes/edges, generated provenance, terminal state, owner activation, NAR, and coverage convergence.
- The audit-envelope schema is closed at the top level and tied to Python key sets.
- The binding generator already computes stable hashes without mutating retained outputs.
- The capsule has its own schema, replay checker, and non-claim boundary.
- The checker already enforces three of the four terminal ordering relations.

### What failed

- A role distinction in prose was not carried into schema names and parser identities.
- The schema filename suggests it owns ordinary public `field_witness`, although its keys describe a different object.
- The binding generator's "envelope" name adds a second use of envelope terminology without a role registry.
- Stale finality language survived beside the newer proof-tail sequence.
- The order checker proved pairwise relations but not the complete terminal sequence or inline finality.
- Historical retained artifacts were treated as if a new name could be silently projected onto them.

### Learning

Artifact identity must be explicit and versioned. A public graph, an audit envelope, and a state capsule are not presentation variants of one object. Pairwise checks are not enough for an ordered terminal protocol; the complete sequence must be validated as one state machine.

## Target Contract

### 1. Canonical role vocabulary

Adopt these exact role names:

```text
public_graph: field_witness / public-field-witness-v1
audit_envelope: field_witness_envelope / field-witness-envelope-v1
state_transport: state_capsule / daee-state-capsule-v2 for new release-bearing runs; daee-state-capsule-v1 for legacy replay only
artifact_binding: field_witness_binding / field-witness-artifact-binding-v1
```

`field_witness_binding` is a subordinate hash record generated from the existing `build_field_witness_envelope.py` logic. It is not a fourth semantic witness. During migration, keep the current CLI as a compatibility wrapper or rename it only with a documented deprecation path; do not fork the canonicalization algorithm.

### 2. Public graph `field_witness`

The public graph remains the literal object under the final `field_witness` heading. It is not nested under a `field_witness` wrapper. Add an explicit discriminator such as:

```json
{
  "schema_version": "public-field-witness-v1",
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"]
}
```

The closed top-level contract must include the currently required public graph families, not the audit-envelope families:

- `schema_version`;
- `B_LA`, `B_MRP`, `B_total`;
- `nodes`, `edges`, `generated_burdens`;
- `mrp_resultants`, `reread_records`, `formal_reread_states`;
- `field_diagnostics`, `terminal_states`, `closure`, `T_lang`, `non_claims`;
- `owner_activations`, `owner_activation_ordering`;
- `normalized_activation_record`, `coverage_proof`.

Any optional public keys must be enumerated in the public schema. Unknown audit-envelope keys at public graph top level fail with `witness-dialect-mixed`.

### 3. Audit `field_witness_envelope`

Move the current audit object to an explicitly named schema, `schema/field-witness-envelope.schema.json`, with `schema_version: field-witness-envelope-v1`. Preserve its current event/reconstruction semantics:

- route gradient;
- burden events;
- field diagnostics and LoopBreak;
- reconstruction and closure;
- transfer boundary;
- register deltas;
- non-claims and provenance;
- coverage proof;
- optional reread/NAR/canonical projection/owner-ordering audit views.

Bind the envelope to the public graph and output through the existing `field-witness-artifact-binding-v1` canonical hashes. The envelope must carry or reference:

```text
output_sha256
public_field_witness_sha256
act_rows_hash
nar_hash
owner_activation_ordering_hash
source_commit
binding_status
proof_class
```

`binding_status=current_bound` remains an owner/evidence claim and must never be auto-stamped. Legacy outputs remain `legacy_unbound` or `known_contract_drift` until requalified.

### 4. `state_capsule`

Keep `schema/state-capsule.schema.json` and `daee-state-capsule-v1` as the legacy internal-state replay contract. Plan A16's one shared `schema/state-capsule-v2.schema.json` is the mandatory state transport for every new release-bearing run. The role contract must say explicitly:

- it may carry `B_LA`, `B_MRP`, `B_total`, completed ACT projections, terminal states, held set, and output hashes;
- it is not emitted as the public `field_witness`;
- it is not validated by the public witness schema;
- it is not the Stage08 audit envelope;
- current PR9 v1 capsules are observability artifacts and are not prompt transport proof;
- v2 gains release-bearing transport status only when A12/A13 bind its exact hash into the canonical call-context manifest and prompt projection.

### 5. Terminal public order

For normal inline graphable output, require exactly:

```text
Restorative Response
Closing Formulation
Closure/Reconstruction Witness
field_witness
EOF
```

Rules:

- Each heading occurs once.
- Restorative Response follows the final state/noetic reread.
- Closing Formulation follows Restorative Response.
- Closure/Reconstruction Witness follows Closing Formulation.
- Inline `field_witness` follows Closure/Reconstruction Witness.
- After the complete JSON object, only a closing code fence and trailing whitespace are allowed.
- For a transport that legitimately uses an adjacent `.field_witness.json`, the public text ends with Closure/Reconstruction Witness and the Stage07 record names and hashes the sidecar. Five-smoke completion must select one transport protocol in advance; for the current completion matrix, require the inline final object so all five exercise the same order checker.
- Neither finality rule permits Closing Formulation to replace the human or machine witness.

### 6. Migration and compatibility

Use a two-step migration:

1. Add the public schema and explicitly named envelope schema while accepting legacy audit-envelope references under `schema/field-witness.schema.json` only in a compatibility fixture lane. Emit deprecation diagnostics, not silent reinterpretation.
2. Switch current release-bearing producers/checkers to explicit dialects. Historical retained artifacts keep their original bytes and get manifest-level dialect/binding status. Never rewrite retained output merely to add a discriminator.

`DAEE-ADR-046-005` makes the choice binding: `schema/field-witness.schema.json` owns the public graph, and `schema/field-witness-envelope.schema.json` owns the Stage08 audit object. Existing builder/parser names may remain deprecation-marked compatibility wrappers, but there may be no second writable schema master. The patch executor validates the ADR before migration and stops rather than reopening this naming decision ad hoc.

## Exact Owner and Edit Map

### Canonical runtime source to edit

- `atomics/skill/SKILL.md`: replace finality shorthand with the complete terminal sequence and role split.
- `atomics/skill/references/rubrics/manual-contract-digest.md`: retain its correct order; add explicit public/envelope/capsule names.
- `atomics/skill/references/rubrics/non-droppable-manual-contract.md`: retain the full public graph contract; add discriminator and role boundary.
- `atomics/skill/references/rubrics/output-release.md`: remove contradictory "Closing Formulation at the end" wording and make inline finality/sidecar transport exact.
- `atomics/skill/references/rubrics/diagnostic-render-contract.md`: replace "at the very end" with "final public formulation before the proof tail" and update examples.
- `atomics/skill/README.md`: name the three artifact roles without presenting the audit envelope as user-facing prose.
- `AGENTS.md`: replace any durable "final Closing Formulation" shorthand that conflicts with the actual proof-tail order.

### Schema and checker source to edit

- Replace the current contents/role of `schema/field-witness.schema.json` with the canonical public-graph contract under an explicit version/discriminator, preserving the old audit shape in compatibility fixtures rather than as a second master.
- Add `schema/field-witness-envelope.schema.json` from the current audit-envelope contract, with explicit version/name.
- Add a read-only compatibility alias/adapter only if historical fixtures require it; the adapter resolves to one of the two canonical schemas and cannot be edited as an independent contract.
- Add `tools/witness_artifact_roles.py` as a small role/schema registry used by checkers.
- Modify `tools/closure_witness_lib.py` to expose the public graph required/optional keys and a final JSON extent.
- Modify `tools/check_manual_smoke_render_contract.py` to validate the complete four-section order and terminal inline JSON extent.
- Modify `tools/check_field_witness_binding.py` to validate public graph and audit envelope against their own owners; keep its current pure self-test.
- Modify `tools/check_ir_instance_integrity.py` to rename audit-envelope key constants and preserve compatibility aliases only during migration.
- Modify `tools/check_field_witness_convergence.py` to require the public discriminator for current release-bearing outputs while retaining a labeled legacy lane.
- Modify `tools/build_field_witness_envelope.py` to state whether it builds the audit envelope or subordinate binding record. Reuse its canonical hashes; do not create a second implementation.
- Modify `tools/check_docs_output_grapher_smoke.py` and `docs/index/output-grapher.js` so the browser-facing parser asserts the same terminal order and inline finality. Keep the JavaScript visualizer a consumer, never proof authority.
- Modify `tools/check_staged_runtime_handshake.py` and `tools/run_staged_current_skill_smoke.py` only to carry explicit dialect/version fields and Stage07/08 artifact paths. Cross-stage row parity belongs to Plan 10.
- Modify `tools/build_staged_governed_output.py` only if it is the owner of final section assembly; do not duplicate order checks there.

### Documentation to edit

- `docs/field-witness-canonicalization-spec.md`.
- `docs/audits/field-witness-binding-map.md`.
- `docs/execution-spine.md`.
- `docs/recursive-state-capsule.md`.
- `docs/non-claims.md`.
- `docs/stage-contract-workbench.md`.
- The owner-maintained North Star source: reconcile its old witness/restoration/closing list with the owner-required order. If that file remains external to the repo, record the change as a separately reviewed architecture-artifact update rather than silently editing a download.
- The Rebake already contains the desired NLA sequence; update only any contradictory passages found during implementation.

### Fixtures to add or revise

- Add `tests/witness-artifact-roles/valid/public-graph.json`.
- Add `tests/witness-artifact-roles/valid/audit-envelope.json`.
- Add `tests/witness-artifact-roles/valid/state-capsule.json` by referencing, not copying, the canonical capsule fixture shape.
- Add invalid mixed-dialect, wrong-discriminator, audit-as-public, public-as-envelope, and unbound-current-status fixtures.
- Add `tests/manual-smoke-render/invalid/field-witness-before-closure-witness.md` from the confirmed in-memory mutation.
- Add `tests/manual-smoke-render/invalid/content-after-inline-field-witness.md`.
- Add a valid exact-order inline fixture and a valid explicitly external-sidecar fixture.
- Add Stage07/08 workbench fixtures that bind public graph, audit envelope, and capsule without treating them as interchangeable.

### Generated files not to hand-edit

- `skill/**`, including `skill/SKILL.md`, compiled module maps, build manifests, and cold-law manifests.
- Generated `docs/index.html` or other generated portal artifacts.
- Package archives and extracted package inventories.

Regenerate only from canonical source with the repository builders.

## Test-Driven Implementation Sequence

### Phase 0: Freeze the two current boundaries

Run from the PR9 checkout:

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
git status --short --branch --untracked-files=all
git rev-parse HEAD
python -B tools\check_field_witness_binding.py --self-test
python -B tools\check_field_witness_binding.py
python -B tools\check_manual_smoke_render_contract.py --outputs tests\retained-proof-corpus\v0.4.3.0-schema-light\valid\sidecar-backed\cases\a9-science-source\output.md
```

Expected before patch: clean planned head; all commands exit `0`.

Run the in-memory mutation from the Direct GEMBA section. Expected before patch: exit `0`, `MUTATED_ORDER_ERROR_COUNT=0`. Preserve that transcript as the red test specification.

STOP if the fixture hash or planned head drifts. Mark this plan stale and re-GEMBA instead of adjusting expected results by intuition.

### Phase 1: Add failing role and order fixtures

1. Add the role registry tests before implementation.
2. Add the field-before-closure and content-after-field invalid fixtures.
3. Add Plan A11 `<fixture-stem>.expectation.json` records for exact failure class/subcode, earliest stage, downstream invalidation, and forbidden artifacts; do not introduce an equivalent private dialect.
4. Confirm the new invalid fixture is a false-pass under the old checker before adding the fix.

Direct red-test command:

```powershell
$output = python -B tools\check_manual_smoke_render_contract.py --outputs tests\manual-smoke-render\invalid\field-witness-before-closure-witness.md 2>&1
$exit = $LASTEXITCODE
if ($exit -ne 1) { throw "expected direct invalid-output exit 1 after the fix, got $exit" }
if (($output -join "`n") -notmatch 'field_witness must follow Closure/Reconstruction Witness') {
  throw 'missing right-reason terminal-order diagnostic'
}
```

Expected after the fix: command-level exit `0` from the PowerShell assertion wrapper, while the checker itself exits `1` for the directly supplied invalid output.

Canonical acceptance command:

```powershell
python tools\assert_expected_rejection.py --expectation tests\manual-smoke-render\invalid\field-witness-before-closure-witness.expectation.json --artifact-root auto
```

Expected: exit `0`; the helper proves the exact Stage07 terminal-order subcode, Stage08 invalidation, and absence of binding/promotion artifacts.

### Phase 2: Introduce explicit artifact roles additively

1. Add the public and envelope schemas.
2. Add the shared role registry and schema-dispatch checker.
3. Keep the current binding checker green while changing its report to identify which dialect it checked.
4. Pin mixed-dialect rejection.

Planned commands:

```powershell
python -B tools\witness_artifact_roles.py --self-test
python -B tools\check_field_witness_binding.py --self-test
python -B tools\check_field_witness_binding.py
python -B tools\build_field_witness_envelope.py --self-test
python -B tools\check_state_capsule.py --self-test
```

Expected: every command exits `0`; reports name public graph, audit envelope, state capsule, and binding record separately.

### Phase 3: Enforce complete terminal order

Refactor the current pairwise heading checks into one pure terminal-section validator. It receives heading extents and selected transport mode and returns stable diagnostics. It must not parse theological prose.

Required negative diagnostics:

```text
terminal-order-restorative-after-closing
terminal-order-closure-before-closing
terminal-order-field-before-closure
terminal-order-content-after-inline-field
terminal-order-duplicate-section
terminal-order-invalid-field-json
```

Required commands:

```powershell
python -B tools\check_manual_smoke_render_contract.py
python -B tools\check_field_witness_convergence.py
python -B tools\check_docs_output_grapher_smoke.py
```

Expected: exit `0`; all registered valid fixtures pass and all invalid fixtures fail for their intended reason. The ordinary checker suites have no unsupported `--self-test` flag.

### Phase 4: Migrate source prose and generated runtime

1. Update every canonical source location in the edit map.
2. Run a repository search for contradictory finality phrases.
3. Rebuild, then check freshness; never hand-edit generated runtime.

```powershell
$matches = rg -n "Closing Formulation.*(?:very end|at the end)|final Closing Formulation|Closure/Reconstruction Witness.*Restorative Response" atomics AGENTS.md docs
$searchExit = $LASTEXITCODE
if ($searchExit -gt 1) { throw "contract search failed with exit $searchExit" }
$matches
python -B tools\build_compiled_runtime.py
python -B tools\check_compiled_runtime_freshness.py
python -B tools\check_cold_law_digest.py --self-test
python -B tools\check_cold_law_digest.py
python -B tools\check_prompt_pack_budget.py --self-test
```

Expected: the search returns only historical/quoted migration notes or no live contradiction; `rg` exit `0` (matches) or `1` (none) is handled explicitly, and all Python checks exit `0` using their currently verified command-line interfaces.

### Phase 5: Stage06-08 and package-bound integration

After Plan 10's projection parity is implemented:

```powershell
python -B tools\check_staged_runtime_handshake.py
python -B tools\run_staged_current_skill_smoke.py --self-test
python -B tools\daee_dry_run_emulator.py --self-test
python -B tools\run_no_model_preflight.py --self-test
python -B tools\run_no_model_preflight.py
```

Expected: all deterministic gates exit `0`. This proves structural migration only. It does not prove model behavior, semantic correctness, or release readiness.

## Five-Smoke Implications

For each of the five registered cases:

- Stage06 must produce a structured public graph projection, not a heading or boolean.
- Stage07 must render exactly Restorative Response, Closing Formulation, Closure/Reconstruction Witness, final inline parser-stable `field_witness`.
- Stage07 public graph must use the public schema and discriminator.
- Stage08 must emit or reference the separately typed audit envelope and binding record.
- State capsules remain separately hashed continuity artifacts; their PASS is not substituted for public witness or envelope PASS.
- The visible human witness, public graph, NAR, and audit envelope must reconstruct the same burden/operation/reread trajectory.
- A structural PASS remains a structural claim. Human topology and semantic review remain separate.

The required IDs are:

```text
gate88-secularism
gate88-khaybar
gate88-trinitarian-j173
gate88-tst-lillard
gate88-torah-quran-source-authentication
```

The fifth fixture stores only the exact source-authentication input. This plan adds no expected burdens, owners, citations, submoves, response outline, or conclusion.

## Rollback

- Keep the first migration additive. If cutover fails, revert consumer routing to the explicit legacy schema while retaining the new fixtures and migration ledger.
- Revert canonical atomics and rebuild generated runtime. Never edit generated `skill/**` to simulate rollback.
- Do not delete or rewrite historical retained outputs. Revert their manifest classification/reference only if the corresponding schema consumer is reverted.
- Preserve the confirmed order false-pass fixture even if the chosen parser implementation changes.
- If implementation conflicts with `DAEE-ADR-046-005`, STOP and record an architecture-decision ANDON; do not leave two writable masters or silently choose another owner.
- Binding hashes and raw evidence are append-only. A superseding envelope is a new artifact, not an overwrite.

## STOP / ANDON Conditions

Stop and record an ANDON if any patch:

- deletes either useful dialect instead of separating it;
- calls the state capsule a public witness or semantic proof;
- creates a second artifact-canonicalization algorithm instead of reusing the existing one;
- auto-stamps `binding_status=current_bound`;
- rewrites retained outputs to make them conform;
- allows audit-envelope keys to satisfy the public graph schema or vice versa;
- leaves inline content after the final parser-stable object;
- restores "Closing Formulation at the very end" wording without qualifying "before the proof tail";
- omits the human Closure/Reconstruction Witness because machine JSON exists;
- infers semantic truth, provenance, uptake, or guidance from structural PASS;
- asserts v46 regression causality;
- starts a model smoke, package, issue, commit, push, tag, release, or publication without separate authorization.

ANDON record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED
class: witness-dialect | terminal-order | schema-migration | binding-status | retained-artifact-drift
failing_check: exact command and exit
owner_source: exact file/function/schema
artifact_role: public_graph | audit_envelope | state_transport | artifact_binding
affected_case_ids: []
preserved_hashes: []
next_action: one concrete owner decision or patch
regression_status: unproven
```

## Definition of Done

- Public graph, audit envelope, state capsule, and binding record have explicit, non-overlapping names and versions.
- The current public graph key family has a schema/checker owner independent from the audit envelope.
- Existing audit-envelope and binding controls remain operational and are not reimplemented in parallel.
- Normal inline output cannot pass unless its terminal order is Restorative Response -> Closing Formulation -> Closure/Reconstruction Witness -> final `field_witness`.
- The confirmed field-before-closure mutation fails for the right reason.
- No live canonical source calls Closing Formulation the absolute end of the artifact.
- Sidecar transport has an explicit, hashed Stage07/08 path and cannot silently replace the public human witness.
- Legacy retained artifacts are classified, not rewritten.
- Stage06-08 workbench, convergence, manual render, capsule, binding, docs-grapher, generated-runtime freshness, and no-model preflight gates pass.
- All five fresh smokes exercise the same selected terminal transport and pass Stage01-Stage08 only after the broader ANDON packet is implemented.
- Structural PASS is reported only as structural; `regression_status` remains `unproven`.

## Confidence

Dialect separation and terminal-order checker: YES, implementation-ready.  
Retained audit-envelope migration: PARTIAL, artifact-requalification gated; naming ownership is settled by `DAEE-ADR-046-005`.  
Semantic reconstruction adequacy: human-reviewed; not proven by schema shape.  
Behavioral regression attribution: NO, unproven.
