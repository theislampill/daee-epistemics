# ANDON A13: Producer/Checker Contract and Harness/Package Parity

Priority: P0/P1 architectural integrity  
Planning baseline: PR #9 head `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR-attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Regression status: `unproven`  
Plan status: implementation-ready for deterministic repo changes; model parity runs remain owner-gated

Packet identity: this concern is A13 and is implemented by file `13_...`. Runtime-footprint salience/load-path fidelity remains A12 in file `12_...`.

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Intended Outcome

The ordinary packaged `/daee-epistemics` runtime and the repo/dev Stage01-Stage08 harness must be governed by the same canonical noetic laws. The harness may transport, validate, retain, and assemble evidence. It may not secretly teach semantic laws absent from the package, invent route topology, or repair a model-produced state transition before the authoritative checker sees the raw record.

This plan does not remove the staged harness. It makes the harness an honest observer and executor of canonical runtime law rather than an untracked second producer specification.

## Abnormality

PR #9's late matrix-repair loop improved staged outputs primarily by editing `tools/run_staged_current_skill_smoke.py`, related checkers, and fixtures. Those changes can make the harness-assisted lane greener without changing what a normal user receives in the default execution-mini package.

Four connected defects are confirmed at the current head:

1. **Harness-only countermeasures.** The commit range `a46e00f^..6987c9e` changes 35 files: 30 fixtures and five `tools/` files. It makes no change to `atomics/skill/**` or generated `skill/SKILL.md`. The execution-mini package excludes `tools/`.
2. **Semantic normalization before validation.** `normalize_stage05_initial_burden_continuations()` rewrites a producer-emitted `no_new_resultant + STOP + graph_delta:none` into `held_burden_activation + RECURSE`, adds a graph edge, rewrites the reread, and then validates the mutated record. That is route-topology construction, not spelling normalization.
3. **Capsules are not call inputs.** Canonical law says each recursive call receives kernel, current capsule, selected shards, and a bounded local excerpt. The harness explicitly documents `build_state_capsule()` as a parallel observability artifact that never feeds prompt composition. `stage_prompt()` and Stage07 section prompts receive `compact_state`, not the latest validated capsule.
4. **Stage07 continuity is fragmented.** Compiled Stage07 creates a number of ACT calls from `--target-output-kb`, partitions body refs among them, and gives each initial section call raw input plus the same compact Stage01-06 state. It does not give later sections the latest capsule or a bounded directly referenced predecessor excerpt. The final public tail is also split across independent MRP, restorative, closing, and witness calls even though canonical law says the final projection call writes the tail once.

The resulting false-pass class is:

```text
harness-assisted PASS
and/or checker-valid normalized record
without proof that the raw producer output or execution-mini package could produce the same topology
```

## Current False-Pass

The current repository can accept a harness-assisted result after the harness has supplied law and changed route state that the default package did not supply. Four read-only probes pin the condition:

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
git diff --quiet a46e00f^..HEAD -- atomics/skill skill/SKILL.md
if ($LASTEXITCODE -ne 0) { throw 'unexpected canonical/generated runtime change in late countermeasure range' }
rg -n 'never feeds into prompt composition|observability artifact only' tools\run_staged_current_skill_smoke.py
rg -n 'canonical_route_result_type.*held_burden_activation|entry\["route"\] = "RECURSE"|dependency_graph_edges' tools\run_staged_current_skill_smoke.py
rg -n 'def compiled_release_section_plan|target_output_kb|previous_stages_json' tools\run_staged_current_skill_smoke.py
```

Expected at the pinned head:

- `git diff --quiet` exits `0`: late fixes did not reach canonical/generated runtime;
- the first search finds the explicit capsule-not-prompt path;
- the second search locates semantic continuation/edge rewriting before validation;
- the third search locates target-size section planning and compact-state-only Stage07 prompt components.

None of these probes proves a historical model regression. Together they prove that a harness-assisted PASS is not sufficient package-parity evidence and that raw producer topology is not presently the sole input to the successful checker path.

## Evidence Classification

### Confirmed

- `atomics/skill/` is canonical editable source; `skill/` is generated.
- The default execution-mini package excludes repo-root `tools/`, `tests/`, and `docs/`.
- The ten late countermeasure commits do not modify canonical or generated runtime.
- Current Stage01-06 prompts are hardcoded in `tools/run_staged_current_skill_smoke.py` and present a runtime hash plus harness-authored contract text.
- Current Codex subprocesses run with the repo as working directory, but the prompt tells the model not to read files and does not embed the generated runtime or selected runtime shards.
- Current state capsules are written after validated stages, are not supplied to the next model call, and list Stage07 shards from stage identity rather than measured prompt inclusion.
- Current Stage05 normalization can construct a continuation edge and change STOP to RECURSE before incremental validation.
- Current prompt-pack checking proves component arithmetic, ceilings, and absence of full-runtime/full-prior-output replay. It does not prove that a listed shard or capsule was actually included unless the component is present and bound.
- Current Stage07 section count is derived from target output size, not from runtime noetic topology.

### Inferred

- Harness-only producer scaffolding can explain part of the gap between a staged matrix result and ordinary package behavior.
- Fragmented calls without capsule/local-predecessor continuity increase the risk of repeated, contradictory, or thinned submove bodies and a witness reconstructed from summaries rather than the performed trajectory.
- A smaller hot root may amplify the divergence when the harness supplies cold laws that an ordinary package invocation does not load at the same transition.

### Unproven

- These defects caused the Grok specimen or any named external model output.
- v0.4.6.0 is behaviorally worse than v0.4.5.0.
- Any particular model will pass after parity is repaired.
- Structural parity implies theological correctness, semantic truth, interlocutor uptake, or release readiness.

## Formal-Chain Location

The failure spans the whole transition chain, but its first actionable owner is the producer-to-checker boundary:

```text
N |- D0
  -> PsiN<...>
  -> IR(...)
  -> route gradient
  -> Bn
  -> {Bni[OPi]}
  -> Land(Bn)
  -> Delta/Delta-kappa
  -> divergence/curl
  -> LoopBreak
  -> R(H,Delta,Delta-kappa)
  -> C(PsiN)
  -> N_fitri and sound reason
  -> T_lang
```

| Boundary | Current parity risk | Required control |
| --- | --- | --- |
| `D0 -> PsiN -> IR` | Stage prompts can carry harness-only diagnostic law | Every semantic prompt clause resolves to a canonical atomics clause and packaged runtime location |
| `IR -> route gradient -> Bn` | Normalizers can canonicalize or add route targets | Raw record is checked first; only lossless representation adapters may run before canonical validation |
| `Bn -> {Bni[OPi]}` | Stage04 scaffolding can be richer than package-visible law | Owner/operation law is source-owned and loaded through the same dispatch contract |
| `Land -> Delta -> reread` | Stage05 semantic rewrite can manufacture held activation and graph delta | Producer must emit the transition; a mismatch fails at Stage05 with raw evidence preserved |
| `R -> closure -> T_lang` | Independent Stage07 calls can lose trajectory continuity | Latest capsule, selected shards, segment ledger, and bounded predecessor excerpt govern each call; one final tail projection |
| package/harness evidence | Harness PASS can be mistaken for package recovery | Separate lane labels and paired custody manifests; neither lane substitutes for the other |

## Existing Controls to Preserve

This plan must reuse and strengthen the controls already present:

- generated-runtime freshness and package-shape checks;
- execution-mini versus audit-full package profiles;
- route-shard selection and load-path budget checks;
- prompt-pack manifest arithmetic and invocation/manifest call-site parity;
- state-capsule schema, validate-then-write behavior, and final replay gate;
- Stage01-Stage08 handshake fixtures and first-failed-stage classifier;
- Stage07 release validator battery;
- raw run-directory retention and hash record;
- structural-only and no-guaranteed-uptake non-claims.

The defect is not that these controls are absent. The defect is that they do not yet bind canonical source law, actual per-call inputs, raw producer output, and final package behavior into one trace.

## Five Whys

The abnormality has three coupled causal branches. Treating them as one linear chain hid distinct repair owners, so each branch receives its own Five Whys.

### Chain A: harness/package authority divergence

1. **Why can harness-assisted PASS diverge from package behavior?** Late fixes changed harness prompts and adapters without necessarily changing canonical runtime source or generated package content.
2. **Why were semantic fixes able to land only in harness prompts?** The nearest repair surface to each observed stage failure was the runner prompt/normalizer, and no gate rejected unowned semantic clauses there.
3. **Why was there no rejection gate?** Prompt-pack checks measured bytes, replay flags, and call-site parity, but did not trace each model-visible semantic clause to canonical atomics and a packaged runtime component.
4. **Why was source tracing absent?** Package-shape, compiled-map, prompt-pack, and checker registries evolved as separate controls without one producer-clause authority relation.
5. **Why did those controls remain separate?** The release protocol never required a package-faithful producer trace as the promotion object; harness success was allowed to stand as the practical feedback endpoint.

Root owner: producer-clause registry, compiled-module mapping, A12 canonical call-context/prompt renderer, and package-faithful promotion profile.

### Chain B: semantic normalization before validation

1. **Why can route meaning change before a checker reports the producer's failure?** Broad `normalize_*` functions can add or rewrite topology-bearing fields before canonical validation.
2. **Why can a normalizer make semantic changes?** Representation canonicalization, compatibility hydration, semantic completion, and topology repair share one undifferentiated adapter surface.
3. **Why are adapter classes not enforced?** Raw producer responses are retained, but promotion validation begins after normalization and no allowlist proves a field-level transformation lossless.
4. **Why was raw-first validation not the boundary?** The runner was optimized to continue staged execution and obtain checker-shaped records, while repair-event observability was added later.
5. **Why could continuation outrank evidentiary fidelity?** No release gate required the raw response itself to satisfy the semantic contract or forced repaired records into a non-promotable evidence class.

Root owner: raw-first runner validation, adapter taxonomy, field-diff proof, and promotion eligibility.

### Chain C: capsule delivery and multi-call continuity

1. **Why can multi-call continuity disagree with the documented capsule architecture?** Capsule files are emitted, but later prompts can still use the older `compact_state()` path instead of the exact capsule/components.
2. **Why did emission not imply consumption?** The capsule wave was implemented as observability alongside the existing prompt path, without replacing or binding that path.
3. **Why was consumption not mechanically checked?** Capsule fields and loaded shards are validated as declared arrays, not joined to exact rendered-prompt bytes and package component hashes.
4. **Why is that join absent?** Runtime context resolution, prompt construction, package identity, and capsule replay have separate owners and no common call-context manifest.
5. **Why could documentation describe the target before the join existed?** Promotion checked static/runtime shape and replay separately, but did not require one content-addressed delivery trace from package component through call input to next-state capsule.

Root owner: A12 call-context manifest/resolver, deterministic prompt projection, state-capsule migration, and package-faithful delivery tests.

**Actionable root owner/source:** canonical clause ownership in `atomics/skill/**`, A12-owned call-context/prompt construction and normalizer policy in `tools/run_staged_current_skill_smoke.py`, package exclusion policy in `tools/package_shape.py`, and new parity fixtures/checkers that bind these surfaces. Model behavior is not the first repair owner.

## Hansei

### What worked

- The staged loop retained failures and turned recurring failure shapes into fixtures.
- The harness records normalizer events rather than silently deleting all traces.
- The package boundary clearly says repo/dev tooling is not the public runtime.
- Prompt budget and capsule replay tooling make a source-owned repair feasible without returning to full-runtime or full-output replay.

### What failed

- A green matrix cycle could reward harness sophistication rather than package capability.
- “Normalization” became too broad a permission. Some functions derive equivalent representations; at least one creates a new route consequence.
- The intended capsule I/O contract and implemented prompt I/O contract diverged.
- Stage07 partitioning was coupled to a byte target. This can reward padding and can split one burden because of a requested output size rather than because topology or context requires a boundary.
- Docs sometimes described the target architecture as if it were operative.

### Lessons

- Every semantic instruction needs a canonical owner and a proof that the ordinary package can expose it at the transition where it is needed.
- A raw producer record is evidence. It must be retained and judged before any semantic rewrite.
- Multi-call compression is valid only when typed state and bounded local continuity actually enter the next call.
- Harness assistance and package behavior are different evidence lanes. Honest labels are a control, not cosmetic wording.

## Target Contract

### 1. Canonical producer-clause registry

Add `tools/producer-contract-registry.json` with one record per model-visible semantic clause used by the staged harness:

```json
{
  "schema": "daee-producer-contract-registry-v1",
  "clauses": [
    {
      "clause_id": "stage05.held-initial-continuation",
      "stage": "05",
      "class": "canonical_semantic_law",
      "source_path": "atomics/skill/references/tactics/TTP-MRP-mid-reread-pressure.md",
      "source_anchor": "held-initial-continuation",
      "runtime_path": "references/runtime-core-recursion.md",
      "load_trigger": "stage05-reread",
      "prompt_component": "selected_runtime_clause",
      "checker_owner": "tools/check_staged_runtime_handshake.py"
    }
  ]
}
```

Allowed classes:

- `canonical_semantic_law`: must resolve to atomics and generated runtime, and must be loaded in the prompt envelope when active.
- `transport_adapter`: may describe JSON-only output, retry transport, or artifact location; may not change route, burden, owner, Land, delta, terminal state, or closure.
- `checker_grammar_adapter`: may explain exact parser syntax already owned by a checker and source contract; must cite both owners.
- `instrumentation_only`: never model-visible and never influences a verdict.

Unknown or unregistered model-visible clauses fail parity. A registry row cannot make a harness-only rule canonical; canonical status requires a real atomics anchor and generated-runtime mapping.

### 2. Raw-first producer record

For every Stage01-06 model response retain:

```text
responses/<stage>.raw-response.txt
records/<stage>.raw.json
records/<stage>.adapter.json
records/<stage>.stage.json
records/<stage>.normalization-events.json
```

Validation order:

1. Parse raw JSON without semantic mutation.
2. Run raw producer-contract validation.
3. If raw validation fails, emit earliest failure and stop. Do not repair.
4. Apply only allowlisted lossless adapters.
5. Prove adapter equivalence and retain a field-level diff.
6. Run canonical stage validation on the adapted record.

Lossless adapters may trim surrounding whitespace, map a documented alias to one canonical spelling, or derive a redundant mirror from an identical source value. They may not:

- add/remove burdens or owners;
- change STOP/HOLD/PARTIAL/RECURSE;
- instantiate/pre-empt a burden;
- add/remove a graph edge;
- alter terminal state, Land, delta, or closure;
- fill a missing operation body or reread basis.

`normalize_stage05_initial_burden_continuations()` must be removed from pre-validation mutation. Its semantic rule belongs in canonical producer law and the producer must emit the held activation itself. The old rewrite remains only as a negative fixture demonstrating the retired false-pass.

### 3. Prompt projection from the canonical call-context manifest

Replace ad hoc string composition with a deterministic prompt projection owned by Plan A12's `daee-runtime-call-context-v1`. Do not create a second authoritative prompt-envelope schema or checker. The exact prompt is rendered from the canonical manifest's ordered components; the projection below is a nested/derived view whose parent manifest hash is always present:

```json
{
  "schema": "daee-runtime-call-context-v1",
  "case_id": "<custody only>",
  "stage": "04",
  "call_index": 4,
  "runtime": {"package_sha256": "<hash>", "skill_root_sha256": "<hash>"},
  "input": {"sha256": "<hash>"},
  "state_capsule": {"path": "state-capsules/capsule-003.json", "sha256": "<hash>", "included": true},
  "components": [{"component_id": "...", "source_path": "...", "sha256": "<hash>", "byte_count": 1, "prompt_start_byte": 0, "prompt_end_byte": 1}],
  "producer_contract_clause_ids": ["stage04.operation-body"],
  "transport_adapter_clause_ids": ["transport.json-only"],
  "prompt": {"path": "prompts/stage-04.prompt.md", "sha256": "<hash>", "byte_count": 1, "effective_context_est_tok": 1},
  "prompt_projection": {"includes_full_runtime": false, "includes_prior_full_output": false}
}
```

The prompt string is rendered from this manifest. A12's `check_runtime_context_delivery.py` recomputes that each declared component appears exactly once or by an explicitly hashed excerpt; `check_prompt_pack_budget.py` consumes its prompt projection rather than minting a competing hash authority. `shards_loaded` and `cold_law_refs_used` are copied from measured delivered components, not inferred from stage number.

The call gets selected shards, not full bundles. This preserves the runtime-footprint objective.

### 4. Actual capsule transport

- Stage01 receives a bootstrap capsule containing exact input identity and intake state.
- After Stage01-06, validate and write the updated capsule before composing the next call.
- The next prompt envelope must include the exact latest capsule path/hash.
- Stage07 section calls update the capsule after each accepted segment, preserving append hash/offset and completed operation state.
- A capsule write failure before a dependent call is a hard Stage boundary failure, not a warning.
- The final replay gate remains and checks the same capsules used as inputs.

Do not pass the whole prior output. The bounded local excerpt is selected by direct dependency: the current burden's preceding submove, an explicitly referenced Land/reread line, or the immediately preceding public tail segment.

### 5. Topology-derived Stage07 partition

Retire output-byte target as the source of ACT section count. Preserve `--target-output-kb` temporarily as a non-gating measurement label for historical runs, but completion-matrix commands set it to `0`.

Partition rules:

1. Start from Stage04 body refs grouped by burden and dependency order.
2. Never split a body ref.
3. Keep one burden together when its prompt envelope fits the configured call budget.
4. Split a burden only at a submove boundary and include the directly referenced predecessor excerpt in the next call.
5. Merge small adjacent burden groups only when the dependency/order contract permits it.
6. Derive the number of sections from obligation topology and measured prompt budget, not output bytes.
7. Require every section to discharge its assigned obligation manifest. No minimum byte count licenses a pass.

Use three projection phases:

- initial projection: visible opening and Layer A/IR from the selected state;
- execution projection: one or more topology-derived ACT segments;
- final projection: MRP/reread, Restorative Response, Closing Formulation, Closure/Reconstruction Witness, and final parser-stable `field_witness` in the required order, written once from the final capsule and segment ledger.

### 6. Harness/package evidence lanes

Every model-bearing run declares exactly one evidence lane:

- `package-faithful`: staged execution in which the hash-bound extracted execution-mini candidate is the only model-visible source of DAEE runtime law. Generic transport, immutable raw records, deterministic capsule/context delivery, and structural checkers remain available, but the harness may not add semantic instructions, repair topology, or substitute repo/dev prose for package law.
- `harness-assisted`: a development-only staged lane that may expose additional hash-recorded harness semantic guidance for diagnosis. It is non-promotional and cannot substitute for package-faithful completion evidence.

`package-only deterministic isolation` may be used as the name of a no-model test family that loads only package files. It is not a third model-evidence lane and must not appear in a matrix authorization or cycle verdict.

Never label harness-assisted output package-bound merely because its hash record names `skill/SKILL.md`.

A parity manifest binds same input, model/host controls, generated runtime hash, package hash, outputs, and structural/human reviews. Allowed status:

```text
not-run
not-comparable
structural-divergence
topology-divergence
candidate-parity
replicated-candidate-parity
```

No automated status says semantic equivalence or truth. `candidate-parity` requires both outputs to pass their applicable structural gates and an independent topology review to find no lost pressure/operation/trajectory. Branch regression status remains `unproven`.

## Exact Owner and Edit Map

### Canonical source edits

- `atomics/skill/references/rubrics/manual-contract-digest.md`
  - make actual call-context-bound capsule/shard prompt transport a non-droppable execution requirement;
  - forbid semantic state repair under normalization;
  - preserve HOLD/PARTIAL when required state or shard cannot be loaded.
- `atomics/skill/references/diagnostics/recursive-state-transitions.md`
  - define raw producer state versus lossless canonical representation;
  - make route/graph/terminal changes producer-owned operations.
- `atomics/skill/references/tactics/TTP-MRP-mid-reread-pressure.md`
  - source-own held-initial-burden continuation and generated/no-resultant distinctions now taught by the harness.
- `atomics/skill/references/rubrics/output-release.md`
  - source-own topology-derived Stage07 partition and one-call final-tail projection.
- `atomics/skill/references/rubrics/diagnostic-render-contract.md`
  - define segment obligation manifests and bounded predecessor excerpts.
- `atomics/skill/references/diagnostics/framework-pipeline.yaml`
  - add canonical call-context/prompt-projection, raw-record, adapter-event, capsule-input, segment-ledger, and parity-manifest owners.
- `atomics/skill/SKILL.md`
  - add only compact hot pointers needed to make the boundaries discoverable; do not re-inline the full manual contract.

### Generated surfaces

- `skill/SKILL.md`
- `skill/references/**`
- `skill/compiled-module-map.json`
- `skill/build-manifest.json`
- `skill/cold-law-manifest.json`

Never hand-edit these. Regenerate from atomics.

### Tool edits

- `tools/run_staged_current_skill_smoke.py`
  - retain raw records;
  - enforce raw-first validation;
  - remove semantic route repair;
  - call A12's context resolver and render prompts from the resulting canonical manifest components;
  - derive Stage07 sections from topology and prompt budget;
  - emit one final tail projection;
  - record evidence lane and model runner in hash records.
  - add target CLI `--evidence-lane {package-faithful,harness-assisted}` and `--package-root PATH`;
  - in `package-faithful`, resolve every model-visible runtime clause from the hash-bound extracted execution-mini root and reject harness-only semantic teaching/repair;
  - record package-root tree hash, generated root hash, registry hash, and evidence lane in every call/capture manifest.
- `tools/check_staged_runtime_handshake.py`
  - expose a pure raw-stage validator and diagnostics for forbidden semantic repair;
  - keep canonical stage validation authoritative.
- `tools/check_prompt_pack_budget.py`
  - consume A12's canonical call-context prompt projection; validate component hashes and actual inclusion, not only names/size;
  - preserve no-full-runtime/no-full-prior-output and ceiling checks.
- `tools/check_state_capsule.py`
  - verify each dependent call consumed the prior capsule hash;
  - permit repeated Stage07 capsule updates while preserving monotonic sequence.
- `tools/build_staged_governed_output.py`
  - consume obligation-based segment manifests and final-tail segment;
  - preserve existing duplicate/missing body-ref and Land-gate checks.
- `tools/daee_dry_run_emulator.py`
  - exercise canonical call contexts, deterministic prompt projections, capsule consumption, and raw/adapter records without a model.
- `tools/run_no_model_preflight.py`
  - compose producer/checker parity into the existing route/runtime gate family;
  - compose capsule-consumption checks into Gate 8 and canonical call-context prompt-projection checks into Gate 15;
  - preserve the existing 16-gate table instead of adding ceremonial gate numbers.
- `tools/run_local_ci.py` and `tools/ci_registry.json`
  - add deterministic checker self-tests only.

### New tool/schema surfaces

- `tools/producer-contract-registry.json`
- `tools/check_producer_checker_parity.py`
- `tools/check_package_harness_parity.py`
- `schema/package-harness-parity.schema.json`

Plan A12 alone adds `schema/runtime-call-context.schema.json` and `tools/check_runtime_context_delivery.py`. This plan extends their coordinated field/test contract through one patch series; it does not fork them.

### Fixtures

- `tests/producer-checker-parity/`
- `tests/runtime-context-delivery/prompt-projection/` under A12's fixture family
- `tests/package-harness-parity/`
- new raw-versus-adapted fixtures under each Stage01-06 workbench directory;
- Stage05 invalid fixture for semantic STOP-to-RECURSE repair;
- Stage07 valid multi-segment same-burden continuity fixture;
- Stage07 invalid missing predecessor excerpt fixture;
- Stage07 invalid split-by-byte-target-only fixture;
- Stage07 invalid tail-written-by-separate-contradictory-calls fixture.

### Docs

- `docs/staged-smoke-maintenance.md`
- `docs/recursive-state-capsule.md`
- `docs/load-path-architecture.md`
- `docs/runtime-harness-onboarding.md`
- `docs/stage-contract-workbench.md`
- `docs/non-claims.md`

## Required Fixture Lattice

### Valid

1. Lossless whitespace/alias adapter with raw and canonical hashes retained.
2. Stage02 keyed detail map projected to the same burden IDs without adding a burden.
3. Stage04 redundant mirror hydration from an identical ACT row.
4. Stage05 producer-emitted held initial continuation with explicit edge and RECURSE.
5. Stage05 genuine `no_new_resultant + STOP` with no later initial burden.
6. Stage07 one-burden/one-submove compact call.
7. Stage07 one burden split at a real submove boundary because the prompt envelope would exceed call budget; next call receives capsule and direct predecessor excerpt.
8. Stage07 many burdens partitioned by topology with no count or byte minimum.
9. Final projection writes the complete public tail once from final capsule and segment ledger.
10. Package-faithful and harness-assisted manifests with identical input/runtime identities and distinct lane labels.

### Invalid

1. Harness clause marked canonical but absent from atomics.
2. Atomics clause present but not reachable in generated execution-mini runtime.
3. Prompt manifest claims a shard that is absent from prompt bytes.
4. Capsule lists Stage07 shards solely because stage ID is 07.
5. Next call uses a stale capsule hash.
6. Adapter changes STOP to RECURSE.
7. Adapter adds a dependency edge, burden, owner, operation, or terminal state.
8. Raw record fails but normalized record passes.
9. Stage07 section count changes only because target KB changes while topology and call budget remain fixed.
10. Same-burden continuation omits predecessor excerpt.
11. Final witness reconstructs an operation absent from segment ledger.
12. Harness-assisted output is labeled package-faithful.
13. Parity manifest upgrades structural agreement to semantic truth.

## TDD Execution Phases

### Phase 0: Freeze the current false-pass and baseline

Run before any implementation:

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
git status --short --branch --untracked-files=all
git rev-parse HEAD
git diff --name-only a46e00f^..HEAD
git diff --quiet a46e00f^..HEAD -- atomics/skill skill/SKILL.md
if ($LASTEXITCODE -ne 0) { throw 'late countermeasure range unexpectedly changes runtime source' }
python tools\check_prompt_pack_budget.py --self-test
python tools\check_state_capsule.py --self-test
python tools\run_staged_current_skill_smoke.py --self-test
python tools\check_package_shape.py
```

Expected baseline:

- head is `6987c9e...` and worktree is clean;
- runtime diff command exits `0` because no runtime source changed in the late range;
- existing deterministic checks exit `0`;
- this is current-control evidence only, not parity proof.

STOP if the branch head or worktree differs. Mark this plan stale before patching.

### Phase 1: Producer-clause provenance

1. Add invalid registry fixtures first.
2. Implement exact atomics-anchor and generated-runtime reachability checks.
3. Inventory every model-visible instruction emitted by `stage_prompt()`, `release_prompt()`, `release_section_prompt()`, and expansion prompts.
4. Classify each instruction. Move semantic law to atomics where absent; do not merely point a registry row at harness text.
5. Rebuild generated runtime and recheck hashes.

Commands:

```powershell
python tools\check_producer_checker_parity.py --self-test
python tools\build_compiled_runtime.py
python tools\check_compiled_runtime_freshness.py
python tools\check_producer_checker_parity.py --registry tools\producer-contract-registry.json
python tools\check_route_shard_selection.py --self-test
python tools\check_cold_law_digest.py --self-test
```

Expected: every command exits `0`; an unregistered or unreachable semantic clause produces a nonzero exit naming its clause ID and source/runtime boundary.

### Phase 2: Raw-first validation and adapter allowlist

1. Add the semantic STOP-to-RECURSE fixture as a current false-pass canary.
2. Split parsing, raw validation, lossless adaptation, equivalence checking, and canonical validation into explicit functions.
3. Remove `normalize_stage05_initial_burden_continuations()` from the successful pre-validation path.
4. Preserve legacy raw records as invalid evidence.
5. Pin earliest-stage and failure-class diagnostics.

Right-reason negative smoke:

```powershell
$fixture = 'tests\stage-contract-workbench\stage-05-mrp-reread-terminal-state\invalid\semantic-stop-to-recurse-repair.json'
$json = python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $fixture
$exit = $LASTEXITCODE
$diag = $json | ConvertFrom-Json
if ($exit -ne 1) { throw "expected exit 1; got $exit" }
if ($diag.earliest_stage -ne '05') { throw "wrong stage: $($diag.earliest_stage)" }
if ($diag.failure_class -ne 'stage05-semantic-repair-required') { throw "wrong class: $($diag.failure_class)" }
```

The patch must establish and pin that exact class in a Plan A11 `<fixture-stem>.expectation.json` sidecar.

```powershell
python tools\assert_expected_rejection.py --expectation tests\stage-contract-workbench\stage-05-mrp-reread-terminal-state\invalid\semantic-stop-to-recurse-repair.expectation.json --artifact-root auto
```

Expected: exit `0`; the raw-invalid record is rejected at Stage05, Stages06-08 are invalidated, and no adapted/promotional artifact is accepted.

Positive suite:

```powershell
python tools\check_staged_runtime_handshake.py
python tools\run_staged_current_skill_smoke.py --self-test
```

Expected: exit `0`; lossless adapters pass, semantic mutations fail on the raw record.

### Phase 3: Actual capsule/shard prompt transport

1. Add prompt-projection fixtures under A12's canonical runtime-context schema.
2. Compose a bootstrap capsule for Stage01.
3. Feed each subsequent call the latest validated capsule.
4. Load only selected runtime excerpts/shards owned by the registry.
5. Populate `shards_loaded` and `cold_law_refs_used` from envelope evidence.
6. Make missing/invalid capsule input a hard failure before invocation.

Commands:

```powershell
python tools\check_runtime_context_delivery.py --self-test
python tools\check_prompt_pack_budget.py --self-test
python tools\check_state_capsule.py --self-test
python tools\daee_dry_run_emulator.py --self-test
python tools\run_staged_current_skill_smoke.py --self-test
```

Expected: exit `0`; the invalid “claimed shard not included” and “stale capsule input” fixtures fail for their pinned reasons.

### Phase 4: Stage07 continuity and final projection

1. Add obligation-based partition fixtures before changing section planning.
2. Replace target-KB-derived ACT chunk count with topology and the measured canonical call-context prompt budget.
3. Emit a capsule after each accepted segment.
4. Supply bounded predecessor excerpts only when dependency requires them.
5. Generate the public tail in one final call and retain current public order.
6. Keep existing assembly checks for missing/duplicate body refs and Land gates.

Commands:

```powershell
python tools\build_staged_governed_output.py --self-test
python tools\check_runtime_context_delivery.py --self-test
python tools\check_state_capsule.py --self-test
python tools\run_staged_current_skill_smoke.py --self-test
python tools\check_staged_runtime_handshake.py
```

Expected: exit `0`. Re-running the no-model partition fixture with different advisory target values must produce the same obligation partition when topology and call budget are unchanged.

### Phase 5: Package/harness parity custody

1. Add schema/checker fixtures for lane identity and control equality.
2. Extend hash records with `evidence_lane`, `model_runner`, canonical call-context/prompt-projection hashes, package/runtime identities, and semantic-repair count.
3. Reject harness-assisted records labeled package-faithful.
4. Prepare, but do not automatically launch, paired model runs.

The deterministic implementation phase uses synthetic hash-bound package fixtures only:

```powershell
python tools\check_package_harness_parity.py --self-test
python tools\check_package_shape.py
```

Expected: exit `0`; synthetic fixtures prove the parity checker's transition rules only. The actual immutable execution-mini candidate is built once under the separately owner-authorized pre-matrix gate in Plan A16 row 18/A14 custody, then replayed through this checker. Package-faithful evidence requires that candidate-package-record and proves that each model-visible DAEE clause came from that extracted tree; harness-assisted evidence requires Stage01-08 and canonical call-context/prompt-projection custody but remains non-promotional.

### Phase 6: Composed preflight and CI

```powershell
python tools\run_no_model_preflight.py --self-test
python tools\run_no_model_preflight.py
python tools\run_local_ci.py
git diff --check
```

Expected after the control-plane rename: all deterministic gates exit `0`; no-model preflight ends `PREFLIGHT_GREEN_AWAITING_OWNER_AUTHORIZATION`. This explicitly reports readiness for an owner decision and proves no model behavior.

The preflight must still report 16 gates. The new controls extend the existing ownership-aligned gates (route/runtime, state capsule, Stage01-08 handshake, and prompt-pack discipline) rather than inflating the gate table.

## Five-Smoke Implications

For each of the five registered inputs, the later owner-gated matrix must retain:

- raw Stage01-06 producer responses;
- raw and adapted stage records plus explicit adapter diffs;
- A12 call-context manifests and prompt projections proving actual capsule and shard inputs;
- topology-derived Stage07 segment manifests;
- final capsule and segment ledger;
- no semantic-repair events;
- Stage01-08 record, output, sidecars, and hash record;
- independent topology review;
- package-faithful candidate-package/call-context custody and deterministic paired lane-parity fixtures.

The five cases are exact regression fixtures, not templates for expected topology. The Torah/Qur'an case must not contain expected burden IDs, burden count, submove count, owner route, quotations, answer outline, or theological conclusion in any registry or prompt adapter.

A harness-assisted 5/5 pass cannot close this ANDON if package-faithful behavior is not exercised or if semantic repair events occurred. The final owner-gated five-smoke completion cycle in Plan A14 must run the `package-faithful` lane and retain full Stage01-08 trajectory records. A second paid harness-assisted 5/5 cycle is not required for WIP completion; deterministic paired prompt/record fixtures must prove which clauses and adapters differ between lanes. Harness-assisted model cycles remain development evidence and can never substitute for the package-faithful final matrix.

## Rollback

- Keep raw failing fixtures and manifests. Never rewrite them into passing artifacts.
- Revert canonical source, registry, runner, checker, schema, and fixture changes as one coherent unit if the new contract cannot be made green.
- Regenerate `skill/**` after rollback; never restore generated files by hand.
- If actual capsule transport exceeds the prompt budget, route HOLD/PARTIAL with `state-capsule-budget` or split at a genuine dependency boundary. Do not re-enable full-output replay.
- If topology partitioning is unstable, fall back to one ACT segment where it fits and one final tail call. Do not fall back to target-byte chunking.
- Preserve old CLI flags for one compatibility cycle, but mark output-size targets non-promotional and unused by the five-smoke completion protocol.

## STOP / ANDON Conditions

Stop the patch or matrix when:

- a semantic prompt clause has no canonical atomics owner;
- a registry row claims runtime reachability that the generated package lacks;
- a raw-invalid record becomes valid only after route/graph/terminal mutation;
- a normalizer changes burden, owner, route, Land, delta, graph, terminal, or closure state;
- a call claims a capsule or shard absent from its canonical call-context prompt projection;
- a dependent call uses a stale capsule;
- a Stage07 split is caused only by requested output bytes;
- a required predecessor excerpt is missing or the whole prior output is replayed;
- the public tail is assembled from contradictory independent projections;
- a harness-assisted result is called package-bound;
- structural PASS is promoted to semantic truth or uptake;
- `regression_status` is advanced from `unproven` without the evidence plan's controlled comparison.

Required record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED
class: canonical-owner-gap | semantic-repair | capsule-transport | shard-claim | segment-continuity | lane-mislabel | parity-divergence
case_id: <fixture or smoke id>
earliest_stage: <01-08 or preflight>
failing_check: <exact command or review gate>
raw_artifact: <path and sha256>
adapted_artifact: <path and sha256 or null>
owner_source: <canonical file/function>
downstream_invalidated: [<stages>]
next_action: <one concrete source/checker/fixture action>
regression_status: unproven
```

## Definition of Done

- Every model-visible semantic harness clause is source-traced to canonical atomics and generated runtime.
- Raw model records are retained and validated before adaptation.
- Only lossless adapters are allowed before canonical validation.
- The Stage05 STOP-to-RECURSE semantic rewrite false-pass is impossible.
- Every dependent call consumes the latest validated capsule and measured selected shards.
- `shards_loaded` describes actual prompt inputs.
- Stage07 partitions by obligations and call budget, never by desired output bytes.
- Same-burden split calls receive bounded predecessor continuity.
- The final public tail is projected once and reconstructs the segment ledger.
- Existing package, prompt-budget, capsule, handshake, release, and no-model controls remain green.
- One owner-authorized five-case `package-faithful` matrix passes Stage01-Stage08 with no semantic repair events and with candidate-package/call-context custody intact.
- Deterministic paired package-faithful versus harness-assisted prompt/record fixtures prove lane classification, clause provenance, and adapter differences. A second paid five-case harness-assisted cycle is not required for WIP completion.
- Any harness-assisted model run is retained only as development evidence and cannot satisfy the completion matrix.
- No structural result is described as semantic truth, provenance, uptake, or release readiness.
- `regression_status` remains `unproven` until controlled evidence says otherwise.

## Confidence

Deterministic source/registry/raw-record/capsule/partition changes: **YES, implementation-ready after owner authorization.**  
Five-case package-faithful evidence: **PARTIAL, candidate-package/owner/model-spend gated.**  
Deterministic paired lane-parity evidence: **YES, implementation-ready; no second paid five-case harness-assisted cycle required.**  
Harness-assisted model evidence: **OPTIONAL development evidence, never promotional.**  
Claim that v46 caused the historical output defect: **NO, unproven.**
