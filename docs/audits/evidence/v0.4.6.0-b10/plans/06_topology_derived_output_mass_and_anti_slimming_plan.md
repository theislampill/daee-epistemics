# ANDON A06: Topology-Derived Output Mass and Anti-Slimming

Priority: P0 policy containment plus P1 structural replacement  
Primary pipeline location: `D₀ -> IR -> ∇_route -> ⁿB -> {ⁿBᵢ[OPᵢ]} -> Land -> R -> 𝒞 -> T_lang`  
Implementation target: PR #9 branch `codex/v0.4.6.0-runtime-footprint` at planned head `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Regression status: `unproven`  
Plan status: implementation-ready in phases; promotion wiring depends on Plans 02, 04, 05, 07, 09, and 10

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Plain-Language Result

The existing system learned an important lesson from earlier thin outputs: difficult inputs can require much more visible work than their surface length suggests. It encoded that lesson partly as fixed burden, submove, and byte thresholds. Those thresholds are understandable historical alarms, but they are the wrong release rule for DAEE.

A byte total cannot tell whether the answer paid its obligations. A long answer can repeat labels, citations, MRP blocks, or filler while omitting a live pressure. A compact answer can be complete when the diagnosed field is genuinely small. Likewise, “four burdens” or “three submoves per burden” can reward a fabricated topology and reject a valid one.

The replacement is an obligation ledger derived from the runtime topology. Every source pressure, selected or held candidate state, routed owner operation, burden landing, reread, generated/held/pre-empted state, witness edge, and closure consequence must either have reconstructible evidence or an explicit terminal disposition. Size remains recorded as telemetry and can trigger review. It can never produce PASS, erase an unpaid obligation, or force the model toward a prewritten topology.

## Abnormality

The current runtime and checker surfaces contain mutually inconsistent policies:

- canonical prose correctly says topology is the proof standard and word count is only an ANDON signal;
- the hot atomic root says hard cases with `4+ burdens` should resemble `40-80 KB` outputs with `3-5 submoves`;
- the manual digest names three submoves per major burden, fifteen total in a five-burden traversal, and a 30k-character floor as warning signs;
- the cold manual names fewer than three per burden and fewer than fifteen total as under-execution signals;
- `tools/check_hard_compound_mrp_smokes.py` turns four burdens, a calculated submove minimum, and calibrated byte floors into pass/fail conditions;
- `tools/check_hard_output_scope_fulfillment.py` defaults to three burdens, eight submoves, and three MRP occurrences, with an optional byte floor;
- a J173 family atomic precomputes six burden cells and fourteen owner submoves for one named smoke family;
- the large-output assembly checker intentionally uses byte filler and proves only assembly/hash capacity, not topology or semantic mass.

The result is a control-system contradiction: topology is declared primary, while numeric proxies can still decide release or shape runtime behavior.

## Direct GEMBA Evidence

### Branch and comparison geometry

- PR9 head inspected: `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`.
- PR base: `56d023e910810e94f36b1e5e2623d568852bf28b`.
- Inherited current-main layer: `c86b3c6673147b8802fe222373a165a37d4d24a8`.
- The local PR checkout is shallow, so its failed merge-base query is not ancestry evidence. GitHub establishes the stack `main c86b3c6... -> PR8 head/PR9 base 56d023e... -> PR9 head 6987c9e...`; PR9-specific attribution uses only the final edge.
- v0.4.5.0 tag checkout: `8c14e28...`.

### Confirmed inherited checker

`tools/check_hard_compound_mrp_smokes.py` has the same Git blob at all four checked references:

```text
v0.4.5.0: 8e47789b058e45bbf8bc3efead0b9acdcc191c6a
remote main: 8e47789b058e45bbf8bc3efead0b9acdcc191c6a
PR base:    8e47789b058e45bbf8bc3efead0b9acdcc191c6a
PR head:    8e47789b058e45bbf8bc3efead0b9acdcc191c6a
```

Therefore the fixed hard-compound checker is confirmed baseline policy debt. It is not introduced by PR9.

Current file identity at PR head:

```text
bytes: 16190
sha256: 9612FF2BFBFD48C826CB1F42175606A99AFB05C27FE44B2B6CC5500E779BFBFC
```

Confirmed pass/fail proxies in that checker:

- `BASE_KB = 8`;
- `FULL_BURDEN_KB = 10`;
- `PARTIAL_BURDEN_KB = 5`;
- `MRP_KB = 4`;
- `CLOSURE_KB = 8`;
- `RESTORATIVE_KB = 10`;
- `SMOKE6_SERIOUS_ANDON_KB = 60`;
- `SMOKE6_CALIBRATED_MIN_KB = 75`;
- hard-compound output must expose at least four burden nodes;
- required submoves are `15` for five or more burdens, otherwise `max(3, burdens * 3)`;
- a full traversal below the computed or calibrated floor exits nonzero.

### Confirmed inherited runtime language

The v45, remote-main, and PR-base `atomics/skill/SKILL.md` share blob `3b76ae3cd27b25d6726b9cc391e83ccc9000841a`. PR head changed the file elsewhere, but the current numeric depth lines remain inherited. Current PR-head lines 499-506 state that cases with `4+ burdens` should resemble `40-80 KB` smoke outputs and have `3-5 submoves`.

The current compiled-source digest and cold manual also contain numeric warning/floor language:

- `atomics/skill/references/rubrics/manual-contract-digest.md` lines 160-173 and 199-204;
- `atomics/skill/references/rubrics/non-droppable-manual-contract.md` lines 781-836 and 956-1009;
- `atomics/skill/references/rubrics/output-release.md` contains the better topology-first rule but still includes fixed generated-burden submove language and a five-burden size heuristic;
- `atomics/skill/references/case-library/do-christian-extensions.md` line 63 contains a six-cell/fourteen-submove J173 partition.

### Confirmed sibling checker policy

`tools/check_hard_output_scope_fulfillment.py` defaults to:

```text
--min-burdens 3
--min-submoves 8
--min-mrp 3
```

It also accepts `--min-bytes` as a failing floor. Its current fixture suite passed during planning. That green result proves fixture consistency under the current profile contract, not that its numeric defaults are architecture-correct.

### Existing nonnumeric controls are green

Direct planning-baseline runs:

```text
manual smoke render contract: PASS; 18 valid, 40 invalid
TTP availability canary check: PASS; 10 valid, 19 invalid
hard-output scope fulfillment check: PASS - fixtures
```

These controls are valuable. The replacement must preserve their owner-specific, prompt-anchor, state-change, provenance, and witness checks.

### The large-output checker is not semantic evidence

`tools/check_staged_governed_output_high_mass.py` explicitly repeats “Synthetic high-mass no-model body prose” around one burden and one ACT row. It checks byte targets, deterministic assembly hashes, non-claims, and forbidden release tokens. It is a legitimate transport/assembly capacity checker. It must remain one, and must never be cited as proof of high-topology capacity or output adequacy.

## Evidence Classification

### Confirmed

- Fixed count and byte gates exist in runtime source and checkers.
- The strict hard-compound checker is inherited unchanged across v45, main, PR base, and PR head.
- The current policy can reject an output solely for having fewer than four burdens, fewer than a computed number of submoves, or fewer than calibrated bytes.
- The current large-output checker can pass byte filler around a tiny topology and explicitly disclaims semantic proof.
- Existing manual render checks can reject many conclusion-shaped and owner-code-only bodies without relying solely on output size.
- The North Star and Rebake require topology to be selected at runtime from an input unknown at design time.

### Inferred

- Numeric floors can encourage models and maintainers to pad outputs or pre-partition cases to satisfy a visible quota.
- Topic-specific count rules can leak a smoke comparator into runtime routing and become an argument bank.
- The historical floors arose because earlier pipelines lacked a complete, machine-readable obligation ledger and therefore used observable proxies for missing work.

### Unproven

- The captured disputed output should have been 90-150 KB or any other exact range.
- Removing numeric floors alone will make outputs deeper.
- A particular number of burdens or submoves is correct for any of the five smokes.
- v0.4.6.0 caused the mass-underexpansion ANDON.
- A topology-ledger PASS proves semantic completeness or truth.

## Architectural Requirement

The design must preserve arbitrary runtime selection across the full chain:

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

The output may legitimately contain one burden or twenty. A burden may legitimately contain one operation or eight. Those examples demonstrate capacity, not targets. The required mass is the visible cost of the obligations actually instantiated by the selected topology.

The bounded OSM-paper lesson is applicable here only as an engineering analogy: endpoint agreement is weaker than trajectory agreement. A final `coverage_complete=true` or long output cannot substitute for preserving the state/operation route that produced it. The paper does not establish DAEE, theology, output length, or any numeric threshold.

## Five Whys

1. Why can a whole output be too thin or padded while still looking governed?  
   Because current controls partly measure bytes, burden labels, and submove labels instead of requiring every runtime obligation to have reconstructible evidence or a terminal disposition.

2. Why were numeric proxies used?  
   Earlier hard-smoke failures showed severe compression, while the stage records did not expose a complete source-pressure-to-operation-to-witness obligation graph. Counts and size were available, so they became alarms and later gates.

3. Why did the alarms become runtime policy?  
   Historical smoke calibration, manual depth guidance, and final-output checkers were copied into hot, digest, cold, and family-local surfaces without a single distinction between advisory telemetry and promotion evidence.

4. Why is the resulting policy unstable?  
   The number of burdens and submoves is itself an output of noetic diagnosis. A fixed threshold constrains the unknown topology it is supposed to observe, while byte floors can be satisfied by filler.

5. Why could the proxy policy persist across later hardening?  
   The promotion architecture had no canonical Stage02-Stage08 obligation-accounting owner, so numeric smoke heuristics could move from advisory telemetry into runtime and checker policy without a control that rejected topology-prescribing gates.

Severity: this control gap is thesis-level because meta-noetic memetic operation requires the pipeline to navigate whichever field the input generates. If design-time quotas choose or reward a topology in advance, the framework becomes a case-shaped argument bank rather than a runtime noetic compiler.

Root owner/source: the depth/mass policy split across canonical runtime atomics, hard-output checkers, smoke documentation, and promotion wiring. The first actionable sources are the numeric clauses in atomics, `tools/check_hard_compound_mrp_smokes.py`, `tools/check_hard_output_scope_fulfillment.py`, and the absence of a derived obligation ledger spanning Stage02-Stage08.

## Hansei

### What worked

- Earlier maintainers correctly recognized that short surface inputs can carry dense noetic load.
- The code repeatedly states that topology outranks size and that padding is invalid.
- Manual render checks already look for target, owner operation, state change, Land contribution, and reconstructibility.
- Historical thresholds made severe compression visible when better evidence was unavailable.
- The large-output assembly checker honestly labels its filler and non-claims.

### What failed

- A warning signal became a deterministic pass/fail floor.
- Fixed burden/submove counts made design-time expectations compete with runtime topology.
- A named J173 canary acquired a precomputed burden partition inside runtime source.
- Profile-specific scope checking and general topology adequacy were not kept separate.
- Size telemetry, transport capacity, structural adequacy, semantic adequacy, and promotion status were allowed to share the word “mass.”
- Earlier plans sometimes treated a 90-150 KB expectation as if it were an acceptance criterion.

### Learning

Use size to ask a question, never to answer it. The release decision must be derived from obligations and evidence. If a small artifact claims a large topology, the correct diagnostic is not “add words”; it is “name the specific pressure, operation, reread, residual, or witness obligation that remains unpaid.” If none is unpaid, compactness is allowed.

## Target Contract: `topology-mass-accounting-v1`

### Source of truth

The ledger is checker-built from validated stage records and the captured output. The model does not author its own PASS verdict.

Inputs:

- Stage01 input hash and observation units;
- Stage02 candidate states, pressure inventory, burden mapping, and dispositions from Plan 02;
- Stage03 owner-operation obligations from Plan 04;
- Stage04 operation capsules from Plan 05;
- Stage05 terminal, MRP, generated/held/pre-empted, residual, divergence/curl, and route decisions from Plan 07;
- Stage06 witness/NAR projection from Plan 09;
- Stage07 public sections and assembly manifest;
- Stage06/07 projection parity from Plan A10 and Stage08 verifier/promotion custody from Plan A11.

### Machine artifact

Each release-bearing run produces:

```json
{
  "schema": "daee-topology-mass-accounting-v1",
  "case_id": "gate88-example",
  "input_sha256": "64-lowercase-hex",
  "staged_handoff_sha256": "64-lowercase-hex",
  "output_sha256": "64-lowercase-hex",
  "obligations": [
    {
      "obligation_id": "O-B1-source-status-repair-1",
      "kind": "owner_operation",
      "origin_stage": "03",
      "source_ids": ["P1", "B1"],
      "allowed_dispositions": ["satisfied", "held", "carried_partial", "carried_recurse"],
      "disposition": "satisfied",
      "evidence_refs": ["B1_1", "sha256:operation-capsule-hash"],
      "basis": "validated Stage04 capsule and matching public/witness projection"
    }
  ],
  "unaccounted_obligation_ids": [],
  "unreconstructible_obligation_ids": [],
  "open_obligation_ids": [],
  "orphan_evidence_refs": [],
  "duplicate_evidence_groups": [],
  "initial_coverage_complete": true,
  "lifecycle_accounting_complete": true,
  "collapse_positive": true,
  "advisory_metrics": {
    "output_bytes": 0,
    "burden_count": 0,
    "operation_capsule_count": 0,
    "mrp_event_count": 0,
    "generated_burden_count": 0,
    "held_or_partial_count": 0
  },
  "non_claims": [
    "counts and bytes do not determine PASS",
    "structural accounting is not semantic truth",
    "one run is not broad model behavior"
  ]
}
```

The zeros are schema examples, not floors. The builder fills them from the actual run.

### Obligation classes

| Obligation kind | Derived from | Required evidence or disposition |
| --- | --- | --- |
| `source_pressure` | Stage02 pressure inventory | burden mapping, proved merge, non-load-bearing basis, HOLD, or unresolved status |
| `candidate_state` | Stage02 candidate-state ledger | selected, held, merged, or rejected with non-circular basis |
| `burden_route` | Stage02/03 | route and owner plan, or explicit held/partial disposition |
| `owner_operation` | Stage03 obligation ledger | Stage04 operation capsule or explicit nonexecution disposition |
| `land_delta` | Stage04/05 | cumulative before/after delta and terminal state |
| `mrp_reread` | every landed burden | one matching post-Land reread and route consequence |
| `residual_pressure` | Stage04/05 | cleared, generated, held, pre-empted, carried partial, or carried recurse |
| `generated_burden` | Stage05 | parent MRP event, generation depth, route, later operation/terminal evidence |
| `field_projection` | Stage06 | exact burden/operation/delta/residual/witness projection |
| `public_projection` | Stage07 | visible section or sidecar reference tied to obligation IDs |
| `restorative_consequence` | final landed field | restored criterion/orientation and scoped/reopen boundary |
| `closure_boundary` | Stage06/07 | complete only when no unaccounted, unreconstructible, or open obligations remain |

### Disposition semantics

Allowed terminal accounting states:

```text
satisfied
discharged_duplicate
non_load_bearing
preempted_not_instantiated
held
carried_partial
carried_recurse
```

Rules:

- `discharged_duplicate` requires a split/merge decision and receiving obligation.
- `non_load_bearing` requires a source-anchored basis and remains reviewable.
- `preempted_not_instantiated` applies only to a candidate resultant that never became a burden; it cannot erase a real `B_LA` or `B_MRP` node.
- `held`, `carried_partial`, and `carried_recurse` are accounted but open. They can satisfy `lifecycle_accounting_complete=true`; they force `collapse_positive=false` and prevent a globally complete terminal claim.
- `initial_coverage_complete=true` means every initial source pressure and `B_LA` burden has an explicit, provenance-backed disposition. It may include honest open dispositions.
- `lifecycle_accounting_complete=true` means every initial, generated, held, pre-empted, partial, and recurse obligation has a disposition and evidence/basis.
- `collapse_positive=true` additionally requires the claimed scope's `open_obligation_ids=[]`, `unaccounted_obligation_ids=[]`, `unreconstructible_obligation_ids=[]`, satisfied diagnostic conditions, and the correct scoped/global residual rule. Do not use the ambiguous bare name `coverage_complete` in new release-bearing records.
- No state named `size_waiver`, `count_waiver`, or `adjudicator_byte_waiver` is allowed.

### Anti-padding contract

The structural anti-padding layer checks:

- every proof-bearing Stage07 section names at least one obligation ID or body ref in the assembly manifest;
- every referenced obligation exists;
- every operation body maps to exactly one operation capsule unless a proved merge explains shared evidence;
- repeated capsule/body hashes across distinct obligations require an explicit shared-operation/merge decision;
- ACT, MRP, witness, and terminal evidence that maps to no obligation is orphan evidence;
- duplicated recaps, citation dumps, and filler cannot satisfy an unpaid obligation because they carry no valid evidence reference.

The checker may flag `padding_review_required=true` when large unbound prose regions or repeated normalized blocks exist. It may not declare prose semantically useless solely from size or repetition. Human review decides whether connective/restorative prose is legitimate.

### Advisory metrics boundary

The system records bytes and counts because they are useful diagnostics. It enforces these invariants:

- changing only `output_bytes` cannot change structural verdict;
- adding filler cannot move an obligation from unpaid to paid;
- deleting evidence while keeping bytes constant must fail;
- a compact output with complete obligation evidence can pass structural accounting;
- a large output with an unpaid or unreconstructible obligation fails;
- dashboards label size as `telemetry`, never `proof`, `score`, or `minimum`;
- historical ranges remain historical observations, not current gates.

## Stage01-Stage08 Integration Map

| Stage | Obligation contribution | New control | STOP condition |
| --- | --- | --- | --- |
| Stage01 | exact input and observation custody | seed source-observation IDs; no mass estimate | input not hash-bound |
| Stage02 | candidate states, pressure IDs, burden/disposition map | create source-pressure obligations from the runtime inventory | source unit or pressure unaccounted |
| Stage03 | routes, owner eligibility, split/merge/order | create owner-operation obligations | routed pressure lacks operation/disposition |
| Stage04 | operation capsules and local deltas | pay owner-operation obligations with body evidence | pointer-only or unreconstructible capsule |
| Stage05 | terminal states, rereads, generated/held/pre-empted lifecycle | create/pay Land, MRP, residual, and recursion obligations | landed burden lacks reread or live residual is hidden |
| Stage06 | witness/NAR graph | pay field-projection obligations | graph complete only over a reduced/mismatched universe |
| Stage07 | public render and section manifest | bind every proof-bearing section to obligations; compute orphan evidence | padding or output length used as payment |
| Stage08 | verifier/custody sidecars | build and verify mass-accounting artifact; quarantine failure | any structural failure promoted as semantic PASS |

## Exact Owner and Edit Map

### Canonical runtime source to modify

- `atomics/skill/SKILL.md`: remove `4+ burdens`, `40-80 KB`, and `3-5 submoves` as runtime depth guidance; replace with unpaid-obligation language and HOLD/PARTIAL when required evidence cannot fit.
- `atomics/skill/references/rubrics/manual-contract-digest.md`: remove three/fifteen/30k and four-burden preclosure proxies; point to topology-mass accounting.
- `atomics/skill/references/rubrics/non-droppable-manual-contract.md`: rename `HARD-COMPOUND DEPTH FLOOR` to `TOPOLOGY-DERIVED EXECUTION DEPTH`; remove fixed submove totals and prose-movement counts; preserve owner-specific operation, state delta, residual, and Land requirements.
- `atomics/skill/references/rubrics/output-release.md`: preserve its topology-first language; remove remaining fixed generated-burden submove and five-burden size clauses; require the obligation ledger instead.
- `atomics/skill/references/diagnostics/recursive-state-transitions.md`: define obligation creation/payment across operation, Land, MRP, residual, and recurse transitions.
- `atomics/skill/references/diagnostics/diagnostic-ir.md`: connect Stage02 pressure inventory to obligation IDs.
- `atomics/skill/references/case-library/do-christian-extensions.md`: remove the six-burden/fourteen-submove J173 partition and any minimum-cell answer bank; retain source-owned owner eligibility and require every actual input pressure to be accounted dynamically.

### Schema and shared logic to add

- Add `schema/topology-mass-accounting.schema.json`.
- Add `tools/topology_mass_accounting.py` as pure obligation derivation and comparison logic.
- Add `tools/build_topology_mass_accounting.py` to produce the Stage08 sidecar from validated records and output.
- Add `tools/check_topology_mass_accounting.py` to validate fixture and captured sidecars.

### Existing tools to modify

- `tools/check_hard_compound_mrp_smokes.py`: remove fixed burden, submove, and byte pass/fail logic; retain hard-compound MRP/route/reconstructibility checks; consume staged records and topology accounting; add a real fixture `--self-test` mode.
- `tools/check_hard_output_scope_fulfillment.py`: remove `--min-bytes`, `--min-burdens`, `--min-submoves`, and `--min-mrp` from release judgment; keep canary-specific visible scope groups clearly classified as smoke-only semantic probes, not topology oracles.
- `tools/check_manual_smoke_render_contract.py`: consume operation capsules and topology ledger for body/obligation parity; preserve current owner-specific checks.
- `tools/check_staged_runtime_handshake.py`: require accounting-sidecar eligibility at Stage08 and ensure coverage status agrees with open obligations.
- `tools/run_staged_current_skill_smoke.py`: carry obligation IDs through prompts/records; never tell the model target bytes or target counts as proof requirements; preserve transport budgets as transport controls only.
- `tools/build_staged_governed_output.py`: add `obligation_refs` to section manifest entries and fail unbound proof-bearing sections.
- `tools/verify_candidate_output.py`: include topology-mass accounting only when stage/custody artifacts are available; output-only replay must say `NOT_EVALUABLE`, not PASS by absence.
- `tools/build_model_compliance_scorecard.py`: report unaccounted, unreconstructible, open, and orphan evidence separately; report bytes under telemetry.
- `tools/check_staged_governed_output_high_mass.py`: retain as transport/assembly capacity; rename user-facing labels from semantic “high-mass” to “large-output transport” where compatibility permits; never wire it as an adequacy verdict.
- `tools/ci_registry.json`: register the topology accounting self-test as required; keep live/captured output review separate and owner-gated.

### Fixtures to add

- `tests/topology-mass-accounting/valid/compact-single-obligation-complete/`
- `tests/topology-mass-accounting/valid/multi-burden-mixed-operation-counts/`
- `tests/topology-mass-accounting/valid/twenty-burden-capacity/`
- `tests/topology-mass-accounting/valid/open-held-obligation-accounted-not-closed/`
- `tests/topology-mass-accounting/valid/proved-merge-reduces-cardinality/`
- `tests/topology-mass-accounting/valid/preempted-candidate-not-instantiated/`
- `tests/topology-mass-accounting/invalid/compact-missing-source-pressure/`
- `tests/topology-mass-accounting/invalid/large-padded-unpaid-owner-operation/`
- `tests/topology-mass-accounting/invalid/old-count-floor-pass-duplicate-bodies/`
- `tests/topology-mass-accounting/invalid/bytes-only-verdict/`
- `tests/topology-mass-accounting/invalid/open-obligation-with-complete/`
- `tests/topology-mass-accounting/invalid/orphan-act-and-witness-evidence/`
- `tests/topology-mass-accounting/invalid/unproved-shared-body/`
- `tests/topology-mass-accounting/invalid/generated-burden-without-full-cycle/`
- `tests/topology-mass-accounting/invalid/model-authored-accounting-pass/`

### Existing fixtures/docs to modify

- `tests/smokes/mrp-behavior/hard-compound-smokes.md`: remove the at-least-four burden gold shape and 60/75-100 KB gate; replace it with source-pressure and obligation accounting.
- `tests/hard-output-scope-fulfillment/`: remove reliance on numeric fixture args; add obligation-bound positive/negative cases.
- `docs/algebraic-notation-and-noetic-formalism.md`: document obligation accounting as trajectory preservation without claiming the OSM paper proves DAEE.
- `docs/stage-contract-workbench.md`: add mass-accounting failure classes and right-reason fixture rules.
- `docs/model-compliance-scorecard.md`: separate structural accounting, semantic review, and size telemetry.
- `docs/four-smoke-release-playbook.md`: update to five-smoke terminology with Plan 13 and require one accounting sidecar per run.
- Historical audit reports remain historical evidence. Do not rewrite old byte-floor observations; label them superseded when cited by current docs.

### Generated surfaces

- Never hand-edit `skill/**`.
- Rebuild `skill/SKILL.md` from atomics.
- Rebuild any generated docs through their owners.
- Package shape and hot-context budgets remain required but prove packaging/transport only.

## Fixture and Property-Test Matrix

### Core valid behavior

1. One pressure, one burden, one operation, one reread, and one complete witness passes without a minimum size.
2. One burden with several distinct owner obligations passes when each has an operation capsule.
3. Several burdens with uneven submove counts pass when their actual obligations are paid.
4. A proved merge reduces burden/operation cardinality and remains reconstructible.
5. A held obligation is fully accounted, so lifecycle accounting can pass, but `collapse_positive=false` and global completion is forbidden.
6. A pre-empted candidate resultant remains visible without becoming `B_LA` or `B_MRP`.
7. Ten- and twenty-burden generated neutral fixtures pass capacity and set-join checks when complete.
8. One burden with three, six, or eight generated operation obligations passes because the obligation set demands them, not because those counts are preferred.

### Core invalid behavior

1. A 150 KB output omits one source pressure.
2. A 200 KB output repeats one operation body across many ACT labels without merge/shared-operation proof.
3. A compact output has a complete-looking witness over an incomplete Stage02 universe.
4. An output satisfies the old burden/submove counts but leaves an owner obligation unpaid.
5. An output contains every ACT row but omits one operation capsule.
6. A landed burden has no post-Land MRP record.
7. A generated burden appears in the witness but lacks parent, route, operation, terminal, or reread evidence.
8. A held/partial/recurse obligation coexists with `collapse_positive=true` or a globally complete terminal claim.
9. A model-authored ledger declares itself complete but disagrees with checker-derived obligations.
10. Output bytes are used as the only reason for PASS or FAIL.

### Metamorphic properties

- Appending filler changes bytes but not obligation verdict.
- Deleting evidence for one paid obligation changes PASS to FAIL even if bytes are restored with filler.
- Reordering parallel obligations preserves verdict; violating `required_before` ordering fails.
- Splitting an operation with a valid split decision creates the corresponding additional obligations.
- Merging operations with a valid merge/shared-evidence decision removes only the obligations licensed by that decision.
- Repeating an identical body under a new body ref without a decision creates orphan/duplicate evidence.
- Changing only the topic words while preserving the same synthetic topology does not change structural behavior.
- Changing topology while preserving byte count changes the derived obligation set and verdict appropriately.

## Test-Driven Implementation Sequence

### Phase 0: Freeze inherited policy and current safeguards

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
$v45 = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v45-tag'
Set-Location $repo
git status --short --branch --untracked-files=all
git rev-parse HEAD
git rev-parse 56d023e910810e94f36b1e5e2623d568852bf28b:tools/check_hard_compound_mrp_smokes.py
git rev-parse HEAD:tools/check_hard_compound_mrp_smokes.py
git rev-parse origin/main:tools/check_hard_compound_mrp_smokes.py
git -C $v45 rev-parse HEAD:tools/check_hard_compound_mrp_smokes.py
rg -n 'SMOKE6_SERIOUS_ANDON_KB|SMOKE6_CALIBRATED_MIN_KB|required_submoves|at least four burden' tools\check_hard_compound_mrp_smokes.py
rg -n '4\+ burdens|40-80 KB|3-5 submoves|thirty|fifteen|at least three|30k' atomics\skill\SKILL.md atomics\skill\references\rubrics\manual-contract-digest.md atomics\skill\references\rubrics\non-droppable-manual-contract.md
python tools\check_manual_smoke_render_contract.py
python tools\check_ttp_availability_canaries.py
python tools\check_hard_output_scope_fulfillment.py
```

Expected:

- PR head is the planned head and clean;
- all four hard-compound checker blob IDs equal `8e47789b058e45bbf8bc3efead0b9acdcc191c6a`;
- `rg` prints the current numeric proxy sites;
- all three deterministic fixture suites exit `0`.

The historical hard-compound live output named in old docs is not tracked in this workspace, so the old checker is not rerun as current behavioral evidence. Do not synthesize a model output to make the command runnable.

### Phase 1: Add topology-accounting red fixtures

Add the schema, pure derivation skeleton, and fixture lattice. The first intended red run is:

```powershell
python tools\check_topology_mass_accounting.py --self-test
```

Expected red state: exit `1` with named failures for unaccounted source pressure, unpaid owner operation, open obligation with complete closure, orphan evidence, unproved shared body, and bytes-only verdict. Import errors and missing fixture roots are not acceptable red evidence.

Implement the shared derivation/checker until the same command exits `0`.

### Phase 2: Prove right-reason unpaid-obligation failure

```powershell
$record = 'tests\topology-mass-accounting\invalid\large-padded-unpaid-owner-operation\staged-handoff-record.json'
$raw = & python tools\check_topology_mass_accounting.py --explain --record $record
$exitCode = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($exitCode -ne 1) { throw "expected exit 1, got $exitCode" }
if ($diag.failure_class -ne 'topology_mass_unpaid_obligation') { throw "wrong class: $($diag.failure_class)" }
if ($diag.failure_subcode -ne 'owner-operation-unpaid') { throw "wrong subcode: $($diag.failure_subcode)" }
if ($diag.earliest_stage -ne '04') { throw "wrong earliest stage: $($diag.earliest_stage)" }
if (($diag.downstream_invalidated -join ',') -ne '05,06,07,08') { throw "wrong downstream invalidation set: $($diag.downstream_invalidated -join ',')" }
if ($diag.unaccounted_obligation_ids.Count -ne 1) { throw 'expected exactly the fixture-declared unpaid obligation' }
if ($diag.advisory_metrics.output_bytes -lt 100000) { throw 'fixture must remain large enough to prove bytes cannot buy PASS' }
if ($diag.promotion_eligible -ne $false) { throw 'invalid accounting record was marked promotion eligible' }
$artifactRoot = Split-Path -Parent $record
foreach ($forbidden in @('stage08-record.json','promotion-verdict.json')) {
  if (Test-Path -LiteralPath (Join-Path $artifactRoot $forbidden)) { throw "invalid fixture produced forbidden artifact: $forbidden" }
}
```

Expected: PowerShell exits `0` after the checker rejects the large padded fixture for the one intended unpaid obligation.

Canonical CI/right-reason command after Plan A11 lands:

```powershell
python tools\assert_expected_rejection.py --expectation tests\topology-mass-accounting\invalid\large-padded-unpaid-owner-operation\staged-handoff-record.expectation.json --artifact-root auto
```

Expected: exit `0`; the A11 helper proves the same class/subcode/stage/downstream set and forbidden-artifact absence from the canonical expectation sidecar.

Compact positive smoke:

```powershell
python tools\check_topology_mass_accounting.py --record tests\topology-mass-accounting\valid\compact-single-obligation-complete\staged-handoff-record.json
```

Expected: exit `0`. No size waiver field exists.

### Phase 3: Replace hard-compound numeric verdicts

Refactor the hard-compound and scope checkers after topology-accounting tests are green.

```powershell
python tools\check_hard_compound_mrp_smokes.py --self-test
python tools\check_hard_output_scope_fulfillment.py
python tools\check_manual_smoke_render_contract.py
```

Expected: all exit `0`.

The hard-compound self-test must include:

- compact but obligation-complete PASS;
- large padded but unpaid FAIL;
- mixed held/PARTIAL lifecycle-accounting PASS with `collapse_positive=false`;
- missing inter-burden MRP FAIL;
- witness/route mismatch FAIL;
- mutation of bytes alone with unchanged structural verdict.

The scope checker may still fail a named smoke when explicit input scope is omitted, but it cannot create burden or submove counts for the output.

### Phase 4: Remove quota language from canonical source

Edit all owner files in one patch. Add a static anti-quota checker rather than relying on review memory:

- new `tools/check_no_fixed_topology_floors.py` scans model-visible canonical source and promotion checkers;
- allowlisted numeric examples must be marked `capacity-example` or historical/non-operative;
- the checker rejects runtime phrases that make bytes, burden counts, or submove counts a universal or topic-keyed PASS condition;
- it also rejects named-smoke minimum burden partitions in packaged runtime source.

Commands:

```powershell
python tools\check_no_fixed_topology_floors.py --self-test
python tools\check_no_fixed_topology_floors.py
python tools\build_compiled_runtime.py
python tools\check_compiled_runtime_freshness.py
python tools\check_package_shape.py
```

Expected: all exit `0`; generated runtime is fresh; package shape and hot-context budgets remain green.

### Phase 5: Preserve transport capacity without semantic overclaim

```powershell
python tools\check_staged_governed_output_high_mass.py
python tools\build_staged_governed_output.py --self-test
```

Expected: both exit `0`. The report must call the first check large-output transport/assembly evidence and explicitly say it does not prove topology, body adequacy, model behavior, or release readiness.

### Phase 6: Wire Stage08 and promotion

```powershell
python tools\check_staged_runtime_handshake.py
python tools\verify_candidate_output.py --self-test
python tools\build_model_compliance_scorecard.py --self-test
```

Expected: all exit `0`. Output-only verification reports topology mass as `NOT_EVALUABLE` unless custody supplies staged records and the accounting sidecar. It must never infer obligation completeness from bytes or visible counts.

### Phase 7: Full deterministic preflight

```powershell
python tools\run_no_model_preflight.py --self-test
python tools\run_no_model_preflight.py
```

Expected: all composed no-model gates exit `0`. This proves the fixture/checker/runtime migration only.

### Phase 8: Authorized five-smoke matrix

Model runs remain owner-gated. After Plan A14 registers the fifth exact input, each run must produce a topology-mass sidecar and pass Stage01-Stage08. Preserve every first failure. Do not rerun one failed case with changed settings and average the results.

## Five-Smoke Completion Contract

Required cases:

| Case ID | Topology rule | Prohibited shortcut |
| --- | --- | --- |
| `gate88-secularism` | derive pressures, burdens, and owner obligations from the exact input | reuse historical burden/count shape as an oracle |
| `gate88-khaybar` | preserve source/transmission pressure and every routed owner dynamically | satisfy a citation or byte quota |
| `gate88-trinitarian-j173` | account for every input-anchored pressure and selected owner operation | enforce the current six-burden/fourteen-submove partition |
| `gate88-tst-lillard` | preserve tribunal/source-worldview/held routes selected at runtime | use a fixed minimum operation count |
| `gate88-torah-quran-source-authentication` | derive source-authentication topology from the exact new input | store expected arguments, burdens, submoves, citations, or conclusion |

Each case must have:

- exact input/package/output custody;
- Stage02 pressure and candidate-state accounting;
- Stage03 obligation ledger;
- Stage04 operation capsules;
- Stage05 per-burden reread and lifecycle accounting;
- Stage06 witness parity;
- Stage07 obligation-bound public sections;
- Stage08 topology-mass sidecar and structural verdict;
- independent topology/body review;
- bytes and counts reported only as telemetry.

One case with an unaccounted, unreconstructible, or falsely closed obligation stops completion. Results are not averaged. A structural five-case PASS is still not theological truth, broad model generalization, cross-host proof, or guaranteed uptake.

## Adversarial Review Protocol

Challenge the implementation with these attacks:

1. Inflate a failing output past every historical byte floor without adding evidence.
2. Duplicate one valid submove until the old count floor is met.
3. Split one pressure into many cosmetic burdens to satisfy a burden floor.
4. Merge several live pressures into one burden while preserving a long output.
5. Delete one obligation's public body, then replace its bytes with citations.
6. Claim `non_load_bearing` without a source-anchored basis.
7. Mark a live pressure `preempted_not_instantiated` after it already became a burden.
8. Keep witness and output internally consistent while omitting a Stage02 source pressure.
9. Add a topic-specific expected topology to the fifth smoke.
10. Restore the J173 six/fourteen count through a checker fixture or hidden prompt.
11. Use the large-output assembly checker as release evidence.
12. Let output-only verifier absence silently count as topology PASS.
13. Treat a human semantic review disagreement as a score to average.
14. Change only output size and verify the structural verdict remains unchanged.

## Rollback

- The safest rollback for a failed implementation is to disable the new promotion gate, preserve all generated evidence, and mark release `BLOCKED` while repairing the ledger.
- Do not re-enable fixed byte/count thresholds as release gates to get a green build.
- If the new schema must be reverted, retain invalid fixtures and the static anti-quota test in an audit branch or historical-gap directory.
- Revert atomics and rebuild generated runtime together; never hand-edit `skill/SKILL.md`.
- Preserve historical audit reports and old live-output observations; do not rewrite history to make them topology-derived.
- If backward compatibility requires the old hard-compound checker temporarily, run it under an explicit `legacy_advisory_only` mode whose exit code cannot authorize promotion.
- Rolling back to the current baseline reopens a confirmed policy ANDON. It is not closure.

## STOP / ANDON Conditions

Stop if implementation:

- introduces any universal or topic-keyed byte, word, burden, submove, or MRP count floor;
- uses an output-size waiver as evidence of semantic sufficiency;
- lets filler, duplicate ACT rows, or citation volume pay an obligation;
- creates obligation IDs from topic names instead of Stage02/03 runtime records;
- accepts a model-authored accounting verdict without recomputation;
- treats held/PARTIAL/RECURSE obligations as closed;
- drops generated, held, or pre-empted provenance;
- allows public/witness parity over an incomplete source-pressure universe;
- puts the Torah/Qur'an or any other smoke's expected answer topology in runtime/checker code;
- uses `check_staged_governed_output_high_mass.py` as semantic or topology evidence;
- reports structural accounting PASS as truth, provenance, guidance, uptake, or release readiness;
- changes the PR head without plan drift review;
- calls the inherited hard-compound checker a PR9 regression.

Concrete STOP record for the inherited floor policy:

```yaml
status: BLOCKED
class: fixed_topology_proxy
abnormality: hard-compound release can be decided by inherited burden, submove, and byte thresholds
owner_source:
  - atomics/skill/SKILL.md
  - atomics/skill/references/rubrics/manual-contract-digest.md
  - atomics/skill/references/rubrics/non-droppable-manual-contract.md
  - tools/check_hard_compound_mrp_smokes.py
  - tools/check_hard_output_scope_fulfillment.py
confirmed_checker_blob: 8e47789b058e45bbf8bc3efead0b9acdcc191c6a
introduced_by_pr9: false
replacement_gate: topology-mass-accounting-v1
next_action: add compact-complete and large-padded-unpaid red/green fixtures before removing numeric verdicts
regression_status: unproven
```

## Definition of Done

- No packaged runtime law or promotion checker uses fixed bytes, burden counts, submove counts, MRP counts, or topic-specific partitions as PASS/FAIL criteria.
- The J173 six-burden/fourteen-submove argument-bank floor is removed from runtime source.
- Every release-bearing run has a checker-derived topology-mass accounting artifact.
- Every source pressure, candidate state, routed operation, Land/reread event, residual, generated/held/pre-empted state, witness edge, and closure consequence has evidence or an explicit disposition.
- `initial_coverage_complete`, `lifecycle_accounting_complete`, and `collapse_positive` remain distinct; the ambiguous bare `coverage_complete` field is migrated out of new release-bearing records.
- Large padded outputs with unpaid obligations fail.
- Compact complete outputs pass without a waiver.
- Counts and bytes remain telemetry and cannot change structural verdict alone.
- Large-output assembly/hash checks remain green and are labeled transport capacity only.
- Existing manual render, TTP availability, MRP, witness, NLA, and custody controls remain green.
- Right-reason fixtures and metamorphic tests prove anti-padding and anti-slimming behavior.
- All five fresh smokes pass Stage01-Stage08 with topology/body review and no expected answer bank.
- Structural PASS remains explicitly non-semantic.
- `regression_status` remains `unproven` until Plan 01's controlled comparison evidence exists.

## Confidence

Numeric-floor diagnosis: YES, confirmed directly in source and checker code.  
PR9 attribution: YES, the strict hard-compound checker is confirmed inherited, not PR9-introduced.  
Topology-derived structural replacement: YES, implementation-ready after prerequisite stage IDs/contracts land.  
Automatic semantic completeness: NO, deliberately not claimed.  
Expected output byte range for any smoke: NO, not a valid acceptance claim.  
Five-smoke completion: UNPROVEN until owner-authorized fresh Stage01-Stage08 runs exist.
