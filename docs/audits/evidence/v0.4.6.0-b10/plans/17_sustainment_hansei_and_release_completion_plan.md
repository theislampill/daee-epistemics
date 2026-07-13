# ANDON A16: Sustainment, Hansei, and Release Completion

Priority: P0 control plane, P1 completion gate, P2 release sustainment  
Implementation target: PR #9 branch `codex/v0.4.6.0-runtime-footprint`  
Planned-head evidence boundary: `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Inherited-main lineage base: `c86b3c6673147b8802fe222373a165a37d4d24a8`  
Regression status: `unproven`  
Plan status: implementation-ready for ledger, dependency, and five-smoke control-plane work; no external action has run; an active standing campaign may delegate test-candidate/model/review children, while issue, commit, push, release-package, tag, release, and publication actions retain their stated separate gates  
Packet identity: this concern is A16. File `16_...` is the corpus/GEMBA evidence ledger, so the sustainment plan is intentionally file `17_...`.

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## 1. Abnormality

The accumulated ANDON packet contains good evidence and many plausible countermeasures, but completion state has repeatedly been ambiguous:

- older reports mixed implemented, proposed, owner-gated, artifact-gated, and unverified work;
- one prior audit emitted both `AUDIT_HANDOFF` and `AUDIT_COMPLETE`;
- historical four-smoke records, current no-model checker health, model behavior, package readiness, and public release state were sometimes discussed too close together;
- the current PR branch has a green no-model preflight, but no fresh five-smoke Stage01-Stage08 completion matrix;
- the current preflight and playbook still register four cases, not the required fifth Torah/Qur'an source-authentication case;
- the existing release-gate ledger is a historical PR-base artifact and explicitly leaves build, package, tag, publication, provenance, readback, and branch-protection gates unverified or owner-gated;
- no single terminal ledger makes every reported ANDON carry cause, countermeasure, verification, Hansei, owner, artifact gates, and a mutually exclusive terminal state.
- the owner reports that predecessor four-smoke repair campaigns sometimes used
  dozens of full model invocations to discover and repair small errors that
  should increasingly be represented by deterministic canaries.

This creates a major control-system risk: a branch can look “done” because plans, checkers, or proof-like artifacts exist even though the actual abnormality, final five-smoke matrix, package identity, or owner decision remains open.

## 2. Current Evidence Boundary

### 2.1 Confirmed

- PR9 head was clean at `6987c9e` during planning.
- The local PR checkout is shallow, so its failed merge-base query is not ancestry evidence. GitHub establishes `main c86b3c6... -> PR8 head/PR9 base 56d023e... -> PR9 head 6987c9e...`. PR9-introduced claims compare only PR9 base to head; release-line comparisons retain the PR8 layer explicitly.
- The composed no-model preflight ran successfully at the inspected PR9 head: all sixteen current gates passed and the final token was `MATRIX_AUTHORIZED_AFTER_PREFLIGHT`.
- That preflight includes runtime freshness, docs freshness, package shape, load budgets, route shards, cold-law digest, state capsules, stage fixtures, mutation self-test, dry-run emulator, retained replay, large-file retention, four input-path checks, prompt-pack discipline, and first-failure reporting.
- `MATRIX_AUTHORIZED_AFTER_PREFLIGHT` does not run or prove a model smoke.
- Existing canonical smoke inputs are J173, TST/Lillard, Khaybar, and secularism.
- The fifth exact input has not yet been added to the repository.
- `docs/four-smoke-release-playbook.md` is explicitly measurement-only and owner-gates model, package, tag, release, and provenance actions.
- `docs/audits/release-gate-ledger.md` marks only local source/freshness evidence green at its historical snapshot and keeps downstream release gates open.
- `tools/run_local_ci.py --strict-pwsh` is the current push/PR local sequence.
- At the inspected branch, `.github/workflows/ci.yml` has workflow `CI`, job
  `runtime-checks`, and runs that strict local sequence on push and pull request.
  `.github/workflows/release-skill.yml` is manual-dispatch packaging, not a
  silently assumed required branch check.
- Read-only GitHub GEMBA on 2026-07-10 reported PR 9 open/draft at head
  `6987c9e...` over base `56d023e...`, with two successful `CI / runtime-checks`
  check runs for that head. The branch-protection endpoint returned `404 Branch
  not protected`. Therefore “required checks” cannot be inferred from protection;
  each push authorization must bind an owner-approved check-set snapshot and the
  current workflow/job evidence.
- Structural checker PASS is not semantic truth, arbitrary-input correctness, source provenance, interlocutor uptake, package proof, or release proof.

### 2.2 Inferred

- A machine-enforced terminal ledger will reduce status overclaim and stale-evidence reuse.
- A same-cycle five-smoke rule will make partial matrices and cross-cycle cherry-picking visible.
- Dependency-ordering countermeasures before the final model matrix will reduce expensive re-runs caused by deterministic contract defects.

### 2.3 Unproven

- v0.4.6 caused a behavioral regression relative to v0.4.5.0.
- All reported ANDON fixes have been implemented.
- Any of the five current-contract smokes passes Stage01-Stage08 at the final implementation commit.
- A package has been built from the final commit.
- Any tag, GitHub Release, asset, provenance record, Pages surface, or public readback exists for v0.4.6.0.

## 3. Architectural Requirement and Formal-Chain Location

The governed execution chain is:

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

Sustainment is not an extra decorative stage after `T_lang`. It is the engineering custody that proves each transition's obligations were preserved and that later evidence is not substituted for earlier missing work. The closure ledger must be able to point from an ANDON to:

- the affected formal transition;
- canonical owner source;
- failing fixture or retained specimen;
- implemented countermeasure;
- right-reason negative test;
- deterministic Smoke A and Smoke B;
- five-smoke impact;
- remaining owner/artifact gates;
- terminal status.

No top-level `COMPLETE` state is valid while any source pressure, owner obligation, generated/held/pre-empted state, witness projection, five-smoke case, or release gate required by the claimed state is unresolved.

## 4. Five Whys

1. **Why can the packet look complete while work remains open?**  
   Completion is expressed in prose across several reports rather than computed from one dependency-aware terminal ledger.

2. **Why do several reports use incompatible completion meanings?**  
   Audit finish, patch presence, deterministic green, scoped model evidence, WIP completion, and release are owned by separate tools/documents with no shared state vocabulary.

3. **Why is there no shared state vocabulary and join?**  
   No canonical control-plane schema composes each ANDON's dependencies, causal evidence, implementation proof, human review, owner/artifact gates, and release custody.

4. **Why was a canonical schema not created as hardening accumulated?**  
   Controls were added around individual checker failures and release steps, so each local control optimized its own endpoint instead of one terminal state machine.

5. **Why could local endpoints continue to stand in for closure?**  
   The promotion path did not require every ANDON row to carry a causal Five Whys chain, Hansei, countermeasure verification, follow-up control, and fresh same-cycle five-smoke evidence before WIP completion could be represented.

This is release-blocking because v0.4.6.0-wip's topology-fidelity claim cannot be supported while mandatory abnormality rows or any of the five Stage01-Stage08 canaries remain open. That is impact and severity, not a replacement for the causal root.

Actionable root owner: release/control-plane state and evidence composition. Canonical owners are a new structured ANDON ledger and checker, the smoke-matrix registry/verdict, `run_no_model_preflight.py`, local CI/CI registry, and release-facing docs. A theological module is not the owner of this abnormality.

### 4.1 Five Whys for the expensive model-debugger loop

1. **Why did small failures consume many full model invocations?**  
   The next full smoke was often the practical discovery surface after each
   repair, so deterministic defects could survive until an expensive end-to-end
   observation.
2. **Why could deterministic defects survive until the model observation?**  
   Existing checks were strong but incident-local: some validated declared
   structure, fixture markers, or one known shape without proving the missing
   relation across neutral mutations and the package-faithful path.
3. **Why did incident-local controls not accumulate into a prevention system?**  
   There was no append-only `MODEL_SMOKE_ESCAPE` registry requiring every
   reproducible paid discovery to become a permanent red-old/green-new,
   right-reason, CI-wired canary.
4. **Why could another model cycle begin while that prevention work was open?**  
   The preflight emitted readiness-like output but no exact-candidate maturity
   certificate joined open escapes, topology metamorphics, package/load-path
   parity, historical replay, and checker mutation evidence.
5. **Why was there no joined maturity and cost gate?**  
   Campaign authorization, deterministic evidence, single-use candidate
   custody, model usage, and Hansei metrics were not owned by one fail-closed
   control-plane transition.

Root owners: A11 validation/escape registry, A15 topology metamorphics, A14
candidate/matrix custody, and A16 maturity/authorization/usage composition. The
root is not “the model is expensive” and not “the smoke was difficult.”

## 5. Hansei

### What went well

- The later issue reports corrected causal overstatement and retained `regression_status: unproven`.
- Historical model outputs and checker failures were preserved rather than rewritten.
- The branch has explicit non-claims, strong deterministic checkers, a no-model preflight, package-shape checks, provenance tooling, and owner-gated release etiquette.
- The existing playbook already requires one-shot smokes, artifact preservation, first-failure reporting, and no averaging.

### What failed

- Document size and formal vocabulary sometimes substituted for execution readiness.
- “Audit completed” was confused with “ANDON closed.”
- Earlier plans included invalid or placeholder commands and did not pin owners, dependency order, or right-reason diagnostics.
- A four-case matrix was treated as the stable registry even after a fifth stress input became a release requirement.
- Historical retained rows and current model proof were not always kept far enough apart.
- Release ledgers were not versioned as snapshots strongly enough to prevent stale reuse.
- Model calls were allowed to carry too much discovery duty. The process did not
  force each deterministically reproducible paid escape into a permanent canary
  before the next cycle.

### Corrective lesson

Completion is a state transition with evidence predicates. It must fail closed when evidence is stale, scoped differently, contradictory, or owner-gated. A handoff and a completion marker are mutually exclusive. Hansei must produce a countermeasure owner and a follow-up control, not just retrospective explanation.

Model spend is also an evidence transition. The five-case matrix remains
mandatory, but it comes after cheap deterministic localization. Lower call count
is useful only when the same topology, body, review, and custody obligations are
preserved; otherwise it is merely a cheaper false green.

## 6. Target State Machine

Use one top-level branch state at a time:

| State | Required evidence | Forbidden inference |
| --- | --- | --- |
| `PLANNING_ONLY` | Plans and evidence ledger exist | No source fix, smoke, package, or release claim |
| `PATCH_IN_PROGRESS` | Authorized edits and red/green task evidence | No matrix or readiness claim |
| `LOCAL_STRUCTURAL_GREEN` | All required deterministic checks pass at one source state | No model-behavior claim |
| `NO_MODEL_SOURCE_PREFLIGHT_GREEN` | All source-owned deterministic gates pass at the exact pushed-green SHA and every known reproducible escape has a permanent canary | No package identity, model behavior, or launch authorization claim |
| `NO_MODEL_CANDIDATE_MATURE` | One immutable `READY_UNUSED` candidate is joined to source preflight, exact-SHA CI readback, package/load-path parity, escape closure, topology/metamorphic coverage, and one hash-bound maturity verdict | No model-behavior or launch authorization claim |
| `FINAL_MATRIX_AUTHORIZED` | Standing campaign plus one-use child authorization binds the exact model/runner/protocol/reservation after local green | Authorization is not a result |
| `FIVE_SMOKE_OBSERVED` | Five concurrently accepted/in-flight isolated workers have terminal rows and an always-run neutral cycle-observation finalizer for one candidate | Observation is not structural or reviewed green |
| `FIVE_SMOKE_STRUCTURAL_GREEN` | All five exact inputs pass Stage01-Stage08 and deterministic replay in one cycle | Human/cold review still open; no semantic or completion claim |
| `FIVE_SMOKE_GREEN` | Structural green plus cold GPT-5.6 review, human review/adjudication, package-faithful custody, and lane-parity gates all pass in the same cycle | No universal semantic or release claim |
| `WIP_COMPLETE` | Every P0/P1 ANDON row is terminally closed, owner decisions recorded, five-smoke green | Not packaged, tagged, or released |
| `POST_COMPLETION_OPUS_OBSERVED` | Separately authorized Opus five-case evidence exists against the completed package bytes | Not cross-model compatibility or authority to patch |
| `CROSS_MODEL_RECONVERGENCE_REQUIRED` | An accepted Opus countermeasure changed a candidate- or verdict-bearing boundary | Historical GPT completion is not current-head evidence |
| `CROSS_MODEL_PAIRED_GREEN` | One parent cycle has reviewed 5/5 GPT plus 5/5 Opus against sibling candidates with identical package hashes | Scoped two-model evidence only; not universal or release proof |
| `RC_READY` | WIP complete plus docs, scorecard, package plan, provenance plan, and clean diff review | Not owner-authorized for publication |
| `RELEASE_AUTHORIZED` | Explicit owner authorization for the exact commit/version/artifact actions | No claim actions succeeded |
| `RELEASED` | Tag, asset, provenance, release body, download/readback, and public docs are verified | No broader model/semantic claim |

`BLOCKED`, `DEFERRED`, and `HANDOFF` are terminal lane outcomes, not top-level success states. They cannot coexist with `WIP_COMPLETE` or `RELEASED`.

## 7. Per-ANDON Ledger Contract

### 7.1 Canonical source and generated view

Use a structured JSON source:

```text
docs/audits/v0.4.6.0-wip-andon-closure-ledger.json
```

Generate a human-readable view:

```text
docs/audits/v0.4.6.0-wip-andon-closure-ledger.md
```

The JSON is canonical. The Markdown is generated by `tools/render_andon_closure_ledger.py` and must not be hand-edited.

### 7.2 Allowed row statuses

```text
OPEN
IMPLEMENTED_UNVERIFIED
VERIFIED_STRUCTURAL
VERIFIED_SCOPED_MODEL
HANDOFF
BLOCKED
DEFERRED
CLOSED_OWNER_ACCEPTED
```

Rules:

- `IMPLEMENTED_UNVERIFIED` requires exact changed owner files but no pass claim.
- `VERIFIED_STRUCTURAL` requires deterministic Smoke A, Smoke B, and right-reason negative evidence at a named commit.
- `VERIFIED_SCOPED_MODEL` requires named case/cycle/package/model evidence and remains scoped to those artifacts.
- `HANDOFF` requires a named receiving owner, exact open dependencies/evidence, and one next command or decision. It is mutually exclusive with every verified/closed terminal status and cannot be used to imply completion.
- `CLOSED_OWNER_ACCEPTED` requires all mandatory dependencies, Hansei, countermeasures, follow-up control, and owner acceptance. It does not imply release.
- `BLOCKED` requires a concrete blocker, owner, preserved evidence, and next action.
- `DEFERRED` requires owner acceptance of the deferral and an explicit non-blocking reason.
- a row cannot use `CLOSED_OWNER_ACCEPTED` while any mandatory evidence reference is missing or stale.

### 7.3 Required row fields

Each A01-A16 row must contain:

```json
{
  "andon_id": "A01",
  "title": "evidence custody and causal attribution",
  "priority": "P0",
  "status": "OPEN",
  "evidence_class": "confirmed | inferred | unproven",
  "code_lineage": "main-inherited | pr8-hardening | pr9-introduced | cross-layer | external-observation | unproven",
  "regression_status": "unproven",
  "formal_chain_locations": ["D0->PsiN->IR"],
  "dependencies": [],
  "milestone_dependencies": ["A16.bootstrap"],
  "milestones": [],
  "owner_sources": ["tools/verify_candidate_output.py"],
  "abnormality_evidence": [],
  "five_whys": [],
  "root_owner": "external-output custody",
  "root_cause_id": "RC-immutable-id-or-null",
  "primary_andon_id": "A01-or-null",
  "affected_andon_ids": ["A01"],
  "shared_countermeasure_ref": null,
  "hansei": {
    "gap": "",
    "cause": "",
    "countermeasure": "",
    "follow_up_control": ""
  },
  "implementation": {
    "commit": null,
    "files": [],
    "generated_files": []
  },
  "verification": {
    "smoke_a": [],
    "smoke_b": [],
    "right_reason_negatives": [],
    "structural_only": true
  },
  "model_smoke_escape": {
    "escape_id": null,
    "deterministic_detectability": "YES | NO | UNKNOWN | NOT_APPLICABLE",
    "red_boundary_evidence": [],
    "green_boundary_evidence": [],
    "mutation_right_reason_evidence": [],
    "next_model_cycle_eligible": false,
    "recurrence_of_escape_id": null,
    "model_invocations_spent_before_detection": 0,
    "estimated_model_invocations_avoided_by_canary": "integer | unknown"
  },
  "five_smoke_impact": [],
  "owner_gates": [],
  "artifact_gates": [],
  "remaining_risk": [],
  "next_action": ""
}
```

The checker validates shape, dependency state, referenced local paths, commit/hash syntax, mutually exclusive states, and stale-head markers. It does not decide theological truth.

Two rows may share one `root_cause_id` and countermeasure only when one is named primary, every affected row is listed, and each symptom retains its own evidence, canary, and terminal disposition. Contradictory countermeasure references for one root fingerprint fail validation.

For A01-A15, `milestone_dependencies` may reference `A16.bootstrap` plus ordinary predecessor milestones. The A16 row has no plan-level dependency and declares at least `A16.bootstrap` and `A16.terminal`; `A16.terminal` depends on the required terminal milestones of A01-A15 and A14 completion. This phased representation prevents the integration plan's intentional bookends from becoming a false dependency cycle. The registry checker expands milestones and proves that expanded graph acyclic.

`regression_status` is the only regression field. Its schema vocabulary is `unproven`, `not-comparable`, `confounded`, `candidate-observed`, `replicated-candidate`, or `not-observed`; every row and smoke verdict starts `unproven`. Only A01's separately authorized, same-fixture comparison/adjudication can propose a transition, and no structural checker or five-smoke completion result changes it automatically. This packet requires it to remain `unproven` because that evidence does not yet exist.

## 7.4 Binding Architecture Decision Ledger

Before any child-plan patch, create and validate `docs/audits/v0.4.6.0-wip-architecture-decisions.json` under `schema/architecture-decision-ledger.schema.json`. The ledger is not an invitation to reopen settled design choices during implementation. It makes the following packet-level decisions executable and gives every affected schema/tool one stable reference:

| ADR | Binding decision | Consequence for implementation | Reopen condition |
| --- | --- | --- | --- |
| `DAEE-ADR-046-001` | `burden_cycles[]` is the canonical v2 recursive reducer input. Stage03/04/05 records remain separately retained and are referenced by `cycle_id`/hash from each cycle. | A07's reducer consumes one ordered cycle array; producers do not invent parallel canonical stage-array reducers. | Only a demonstrated non-lossless projection or schema impossibility, recorded as an ANDON with a replacement migration. |
| `DAEE-ADR-046-002` | `tools/run_staged_current_skill_smoke.py` owns scheduling and model invocation. `tools/mrp_recursion_lib.py` is pure transition/reduction logic with no process, network, prompt, or filesystem orchestration. | Deterministic tests call the pure reducer; the runner alone executes the Stage05 return edge. | Only if a dedicated scheduler is proposed with an explicit migration and no second invocation owner. |
| `DAEE-ADR-046-003` | Resource-policy values are supplied by hash-bound authorization/runtime configuration. There is no semantic recursion-depth cap. Resource exhaustion yields resumable `PARTIAL`/`HANDOFF` with live obligations preserved. | A07/A12 validate policy provenance and truthful exhaustion; capacity probe depths are never runtime ceilings. | Only an owner-approved resource-policy version change; never a smoke-specific count. |
| `DAEE-ADR-046-004` | Handshake/state-capsule v1 remains readable for historical replay until a separate deprecation ADR. Every new release-bearing execution uses composed v2. | Checkers dispatch by version; v1 cannot satisfy new recursion or completion evidence. | A separate deprecation decision with retained-artifact migration proof. |
| `DAEE-ADR-046-005` | `schema/field-witness.schema.json` owns the current public graph. `schema/field-witness-envelope.schema.json` owns the Stage08 audit envelope. Existing builder/parser names may remain compatibility wrappers with deprecation diagnostics, but cannot remain writable schema masters. | A09 has one public schema, one audit schema, one role registry, and no naming choice left to the patch executor. | Only a versioned public-schema migration with compatibility fixtures and owner approval. |
| `DAEE-ADR-046-006` | The five-smoke cycle is an indivisible concurrent observation over one single-use candidate. No prior-cycle row, queued/sequential substitute, raw-output repair, or consumed candidate may satisfy completion. Candidate custody records dispatch only; verdict artifacts record quality. | A14's canonical `tools/run_five_smoke_matrix.py --model-runner codex` lane uses five isolated workers under `barrier-five-submit-before-await-v1`, a neutral observation finalizer, pre-claim `READY_UNUSED` preservation, post-claim `CONSUMED_OBSERVED`/`CONSUMED_NO_DISPATCH`/`CONSUMED_DISPATCH_UNKNOWN`, and mixed-cycle/concurrency fixtures. | Only an owner-approved matrix-protocol version change backed by deterministic isolation and custody proof. |
| `DAEE-ADR-046-008` | The convergence objective has no fixed cycle or cumulative call ceiling; exact child reservations, factual usage/cost, open-ANDON stops, commit/push pauses, and provider circuit breakers govern execution. | A14/A19/A21 standing-campaign schema, one canonical usage head, five-call producer/review reservations, and recurrence stop rules. | Explicit owner revocation or a later protocol decision; never an arbitrary stop-after-N rule. |
| `DAEE-ADR-046-009` | An accepted Opus countermeasure that changes a candidate- or verdict-bearing boundary makes the new head unproven until a paired GPT/Opus parent cycle reconverges. | A14/A21 two sibling candidates with identical package hashes, ten-worker barrier, independent per-output stages/reviews, and no cross-model pass carry-forward. | Separate owner rejection of the Opus repair or a proven infrastructure-only boundary that changes no shared source/protocol. |
| `DAEE-ADR-046-007` | A paid/model smoke is the final behavioral integration gate, not the debugger. `NO_MODEL_CANDIDATE_MATURE` and terminal `MODEL_SMOKE_ESCAPE` accounting precede every cycle. | A11/A15/A14 preflight composes right-reason, mutation, topology/metamorphic, taint, load-path, package/harness, and historical-failure replay evidence. | Only a demonstrated behavior that cannot be deterministically approximated, classified `deterministic_detectability=NO` with owner review. |
| `DAEE-ADR-046-008` | Final scoped completion requires separate cold GPT-5.6 comprehension/comprehensiveness and human substantive review lanes. Cold challenges are preserved; upheld/unresolved material challenges fail the cycle; answered challenges require evidence. | A01 owns both review schemas/checkers; A14/A16 bind five of each and cannot call structural PASS semantic truth. | Only an owner-approved review protocol migration with retained old-review replay. |
| `DAEE-ADR-046-009` | Producer and cold-review model usage share one canonical content-addressed campaign head advanced through exclusive/CAS reservation and settlement transactions. | A14 owns usage-head tooling/fixtures; a predecessor conflict spends zero calls, and orphan recovery cannot mint capacity or reuse a candidate. | Only a replacement protocol proving equivalent cross-process linearizability and conservative crash recovery. |
| `DAEE-ADR-046-010` | Cycle identity is claimed outside the working root, candidate consumption is neutral, and external evidence moves through hash-verified staging to one atomic final publish/pointer. | Root creation failure still emits a fallback observation finalizer; partial staging never counts as final; structural and reviewed verdicts remain later artifacts. | Only a storage protocol with equivalent claim, no-overwrite, resume, and final-readback proof. |
| `DAEE-ADR-046-011` | Human review writes an immutable initial assessment before cold-review disclosure and dispositions every cold finding exactly once. | A01 checker rejects missing/changed initial hashes, finding-set mismatch, evidence-free answers, invalid retry lineage, and patch-owner reversal without second independent review. | Only an owner-approved review-schema migration preserving equivalent independence and dissent custody. |

Every ADR row binds decision status, rationale, affected plans, owner files, superseded alternatives, decision owner, accepted timestamp, and reopening evidence. `tools/check_architecture_decision_ledger.py` rejects a missing binding ADR, an undecided status, a duplicate owner, or implementation files that declare a conflicting canonical choice. The ADR checker proves decision custody only, not design correctness or model behavior.

## 8. Dependency-Ordered Execution Plan

### P0: Contain false evidence and close the earliest loss points

P0 completes before any final completion-matrix model run.

| Order | ANDON | Required result | Dependency |
| ---: | --- | --- | --- |
| 0 | A16 control-plane bootstrap | Canonical closure ledger, contract registry, architecture-decision ledger, v2 migration ledger, schemas, and self-tests exist before child patches; every A01-A16 row begins `OPEN` with exact dependencies and `regression_status: unproven` | none |
| 1 | A01 evidence custody/causality | Capture and comparison manifests; structural verdict bound to output; regression remains unproven | A16 control-plane bootstrap |
| 2 | A02 source-pressure inventory | Every source observation has pressure/disposition; candidate states terminate | A01 custody fields available |
| 3 | A03 partition and split/merge | Every merge/split has reconstructible basis; no latent-state aliasing | A02 |
| 4 | A04 dynamic submove/owner coverage | Every executable owner obligation has ACT or explicit disposition | A03 |
| 5 | A05 operation-body/Land license | ACT rows dereference canonical performed-operation bodies | A04 |
| 6 | A08 phase 1, opening/nonterminal-state contract | Opening state cannot claim completion; HOLD/PARTIAL/RECURSE remain honest while execution is incomplete | A02-A05 |
| 7 | A09 phase 1, witness dialect/order decision | Public graph, audit envelope, and state capsule have distinct names/bridges; final public order is fixed | A02-A05, A08 phase 1 |
| 8 | A11 phase 1, captured-output custody/promotion scaffold | Hash-bound verdict and quarantine path exist; the final battery remains dependent on P1 lifecycle/projection work | A01, A05, A09 phase 1 |

P0 exit criteria:

- every P0 row is at least `VERIFIED_STRUCTURAL`;
- Order 0 ledgers are valid, hash-bound, and updated after every patch group rather than reconstructed at the end;
- all binding ADR rows are accepted and no child plan declares a competing canonical owner;
- all current false-pass fixtures fail at their earliest intended stage/class;
- no source-anchored pressure can disappear before witness construction;
- witness owner decision is recorded;
- the invalid captured specimen remains invalid evidence, not rewritten;
- `regression_status` is still `unproven` unless an independently authorized comparison ran.

### P1: Prove depth, lifecycle, runtime delivery, capacity, and one package-faithful candidate

| Order | ANDON | Required result | Dependency |
| ---: | --- | --- | --- |
| 9 | A07 generated/held/pre-empted recursion | Stage05 activation/instantiation executes a later Stage03/04/05 cycle; a depth-two generated canary proves recursive return, lifecycle partition, provenance, terminal accounting, and reread | A02-A05, A08 phase 1 |
| 10 | A08 phase 2 | Final closure derives from completed lifecycle and preserves open/LoopBreak states truthfully | A07, A09 phase 1 |
| 11 | A10 projection parity | Stage06 witness/NAR and Stage07 public output are exact projections of the executed lifecycle | A07, A08 phase 2, A09 phase 1 |
| 12 | A06 topology-derived mass, final wiring | Unpaid obligations, not bytes/counts, govern adequacy; padding receives no credit across the completed lifecycle/projection | A02-A05, A07, A09, A10 |
| 13 | A12 runtime salience/load-path | Every live obligation receives a hash-bound canonical call context and prior capsule before use | P0 contracts, A07, A10 |
| 14 | A13 producer/checker/harness parity | Harness-only teaching/repair is classified; A12 call context owns the prompt projection; package behavior is not inferred from harness success | A10, A12 |
| 15 | A15 arbitrary topology/property suite | Topic-neutral 1/10/20 and 1/3/6/8 capacity canaries plus open-world route, dependency, recursion, and delivery metamorphics pass | A02-A10, A11 scaffold, A12-A13 |
| 16 | A11 final profile/registry freeze | Every checker added by A06-A15 is in one canonical promotion profile; right-reason expectations and hash-bound verdicts are complete | A01, A06-A15 |
| 17 | A14 five-smoke registry/control plane | Exact five inputs, canonical Codex producer lane, one campaign usage-head CAS, recoverable cycle claim, five-worker barrier proof, neutral observation finalizer, transactional evidence publish, candidate lifecycle, and no-answer-bank rules are current | A01, A10-A13, A15, A11 final |
| 18 | No-model source preflight | Every known model-smoke escape is classified; reproducible escapes have red-old/green-new canaries, neighboring valid controls, right-reason mutation coverage, topology/metamorphic and taint checks; one `NO_MODEL_SOURCE_PREFLIGHT_GREEN` verdict binds the exact pushed-green source | rows 1-17 green; A11/A15/A14 |
| 19 | Owner-authorized pre-matrix candidate package | Build and verify one single-use immutable execution-mini candidate solely for package-faithful matrix evidence; bind pushed-head/CI receipt and source/build/package hashes; do not tag, publish, install globally, or call it a release artifact | row 18; A12-A14; explicit package-build authorization |
| 20 | No-model candidate maturity | Join the `READY_UNUSED` candidate record to row-18 source preflight, exact-SHA CI readback, extracted package/load-path checks, escape registry, and deterministic reports; emit one `NO_MODEL_CANDIDATE_MATURE` verdict for that candidate | rows 18-19; A11-A15 |
| 21 | Final five-smoke matrix and reviews | Package-faithful `run_five_smoke_matrix.py --model-runner codex` proves five accepted/in-flight isolated workers before first-result consumption; all five pass Stage01-Stage08, A11 replay, cold GPT-5.6 review, human review/adjudication, package-faithful custody, and deterministic paired-lane fixtures in one cycle | rows 1-20 green; standing campaign, exact child cycle/model reservation, and evidence-retention authorization |

P1 exit criteria:

- `run_local_ci.py --strict-pwsh` passes at the final candidate commit;
- the composed no-model preflight passes and includes all five input paths and the topology-property gate;
- `NO_MODEL_CANDIDATE_MATURE` binds the exact candidate boundary and no `MODEL_SMOKE_ESCAPE` row is open or unknown;
- all five exact cases pass independently in one final authorized cycle;
- all five launch through the barrier protocol with isolated context/home/temp/cache/session/run roots, one canonical usage-head settlement, and an always-run neutral observation finalizer;
- all five have cold GPT-5.6 and human review evidence with no unresolved/upheld material defect under PASS;
- one failed, partial, truncated, repaired, or unreviewed case blocks aggregate green;
- no case is graded by an expected burden count, submove count, output byte range, or expected theological conclusion.

### P2: Sustainment and release custody

P2 begins after five-smoke green. The row-19 candidate package is a delegated,
one-use child of the standing campaign, an immutable test input, and not a
release package. P2 may prepare source/docs before owner release authorization,
but cannot build a release artifact or publish unless separately authorized.

| Order | Work | Required result |
| ---: | --- | --- |
| 22 | Freeze and render the terminal closure-ledger snapshot | The continuously maintained A01-A16 JSON ledger is revalidated and rendered; no contradictory completion/handoff state and no retroactive evidence reconstruction |
| 23 | Scorecard migration | Structural classes, custody identity, case/cycle, and non-claims; no ambiguous defect `pass/fail` fields |
| 24 | Docs and CI alignment | Five-smoke terminology, exact commands, property gate, generated-file rules, historical evidence labels |
| 25 | Issue packet | Fileable umbrella/children generated from the ledger; filing remains owner-gated |
| 26 | RC package plan | Exact profile/version/artifact/provenance/readback gates recorded; release build remains owner-gated and distinct from the row-19 candidate |
| 27 | Owner release decision | Exact commit, version, package profile, tag, publication, and readback actions explicitly authorized or deferred |
| 28 | Authorized release/readback | Only after separate authorization; verify tag/artifact/provenance/public state |

## 9. Exact Owner and Edit Map

### Shared schema integration rule

Plans A03, A04, A05, A07, A10, and A12 all add state that must survive multi-call execution. They must land through one composed `daee-state-capsule-v2` schema and one migration ledger, not several independently designed v2 objects. The composed schema includes candidate/partition carry, owner-obligation dispositions, operation-capsule hashes, generated/held/pre-empted lifecycle, projection fingerprints, and call-context delivery references. `schema/state-capsule.schema.json` retains its historical v1 meaning; Plan A16 is the single integration owner for the new `schema/state-capsule-v2.schema.json`. `tools/check_state_capsule.py` dispatches by schema version and tests v1 replay plus v2 release-bearing behavior. Any child patch that attempts to redefine or replace v2 independently is a STOP/ANDON.

### Add

- `schema/andon-closure-ledger.schema.json`
- `schema/state-capsule-v2.schema.json`
- `schema/architecture-decision-ledger.schema.json`
- `schema/release-action-authorization.schema.json`
- `schema/vcs-action-authorization.schema.json`
- `schema/ci-readback.schema.json`
- `schema/no-model-candidate-maturity.schema.json`
- `schema/evidence-retention-manifest.schema.json`
- `tools/check_andon_closure_ledger.py`
- `tools/render_andon_closure_ledger.py`
- `tools/check_andon_contract_registry.py`
- `tools/check_architecture_decision_ledger.py`
- `tools/check_release_action_authorization.py`
- `tools/check_vcs_action_authorization.py`
- `tools/check_ci_readback.py`
- `tools/build_no_model_candidate_maturity_verdict.py`
- `tools/check_no_model_candidate_maturity.py`
- `tools/export_cycle_evidence_bundle.py`
- `tools/check_evidence_retention_manifest.py`
- `docs/audits/v0.4.6.0-wip-andon-contract-registry.json`
- `docs/audits/v0.4.6.0-wip-architecture-decisions.json`
- `tests/andon-closure-ledger/valid/complete-structural-row.json`
- `tests/andon-closure-ledger/valid/blocked-with-next-action.json`
- `tests/andon-closure-ledger/invalid/complete-with-open-dependency.json`
- `tests/andon-closure-ledger/invalid/handoff-and-complete.json`
- `tests/andon-closure-ledger/invalid/structural-pass-claimed-semantic.json`
- `tests/andon-closure-ledger/invalid/stale-evidence-head.json`
- `tests/andon-closure-ledger/invalid/a16-plan-level-self-cycle.json`
- `tests/andon-closure-ledger/valid/a16-bootstrap-terminal-milestones.json`
- `tests/architecture-decision-ledger/valid/all-binding-decisions-accepted.json`
- `tests/architecture-decision-ledger/invalid/missing-recursion-owner-decision.json`
- `tests/architecture-decision-ledger/invalid/conflicting-field-witness-owner.json`
- `tests/release-action-authorization/valid/exact-release-package-build.json`
- `tests/release-action-authorization/invalid/reusable-boolean.json`
- `tests/release-action-authorization/invalid/source-head-drift.json`
- `tests/release-action-authorization/invalid/extra-release-actions.json`
- `tests/vcs-action-authorization/valid/exact-countermeasure-commit.json`
- `tests/vcs-action-authorization/valid/exact-nonforce-branch-push.json`
- `tests/vcs-action-authorization/invalid/matrix-authorization-used-for-push.json`
- `tests/vcs-action-authorization/invalid/remote-head-moved-after-approval.json`
- `tests/vcs-action-authorization/invalid/authorization-replayed.json`
- `tests/ci-readback/valid/required-checks-bound-to-pushed-sha.json`
- `tests/ci-readback/invalid/green-checks-for-another-sha.json`
- `tests/ci-readback/invalid/check-set-snapshot-drift.json`
- `tests/ci-readback/invalid/manual-release-workflow-counted-as-branch-green.json`
- `tests/no-model-candidate-maturity/valid/all-escape-and-canary-gates-green.json`
- `tests/no-model-candidate-maturity/valid/source-preflight-then-candidate-join.json`
- `tests/no-model-candidate-maturity/invalid/open-model-smoke-escape.json`
- `tests/no-model-candidate-maturity/invalid/unknown-deterministic-detectability.json`
- `tests/no-model-candidate-maturity/invalid/canary-green-without-red-boundary.json`
- `tests/no-model-candidate-maturity/invalid/case-registry-taint-reaches-routing.json`
- `tests/no-model-candidate-maturity/invalid/source-preflight-offered-as-candidate-mature.json`
- `tests/no-model-candidate-maturity/invalid/maturity-bound-to-other-candidate.json`
- `tests/evidence-retention/valid/staged-atomic-cycle-publish.json`
- `tests/evidence-retention/valid/partial-staging-resume-hash-equal.json`
- `tests/evidence-retention/invalid/repo-ignored-directory-only.json`
- `tests/evidence-retention/invalid/manifest-missing-failed-worker-artifact.json`
- `tests/evidence-retention/invalid/retention-readback-hash-drift.json`
- `tests/evidence-retention/invalid/partial-staging-resume-hash-mismatch.json`
- `tests/evidence-retention/invalid/staging-manifest-offered-as-final.json`
- `tests/evidence-retention/invalid/publish-pointer-cas-conflict.json`
- `tests/state-capsule-v2/valid/composed-all-plan-fields.json`
- `tests/state-capsule-v2/invalid/release-bearing-v1.json`
- `tests/state-capsule-v2/invalid/competing-schema-owner.json`
- `docs/audits/v0.4.6.0-wip-state-capsule-v2-migration-ledger.json`
- `docs/audits/v0.4.6.0-wip-andon-closure-ledger.json`
- generated `docs/audits/v0.4.6.0-wip-andon-closure-ledger.md`
- `docs/audits/v0.4.6.0-wip-five-smoke-completion-ledger.md` after an authorized final matrix
- `docs/audits/v0.4.6.0-wip-five-smoke-andon-convergence-north-star-addendum.md`

Every new active invalid fixture in these A16 families receives a same-stem `.expectation.json` under A11's canonical schema. Bootstrap self-tests may use direct assertions before A11 lands, but terminal structural verification requires the canonical helper verdict.

### Modify

- `tools/run_local_ci.py`  
  Add deterministic closure-ledger, contract-registry, maturity, escape-registry,
  and evidence-retention self-tests; consume A14's smoke-registry and A15's fast
  topology-property commands after their owners land.
- `tools/ci_registry.json`  
  Register new `check_*.py` tools with explicit required/manual-slow classification.
- `tools/build_model_compliance_scorecard.py`  
  Consume custody/matrix manifests; keep structural rows unambiguous and schema-versioned.
- `docs/four-smoke-release-playbook.md`  
  Retain the historical title/path for link stability; add a scoped pointer to the current five-smoke addendum and keep historical evidence explicitly historical.
- `docs/staged-smoke-maintenance.md`
- `docs/non-claims.md`
- `docs/model-compliance-scorecard.md`
- `docs/audits/release-gate-ledger.md` only to mark it historical or superseded; do not rewrite old results as current.
- `TODO.md` with explicit P0/P1/P2 status and owner gates after implementation is authorized.

### Consume without redefining

- Plan A14 alone owns `schema/smoke-matrix.schema.json`, `schema/cross-model-paired-cycle.schema.json`, `tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json`, `tools/smoke_matrix_registry.py`, `tools/check_smoke_matrix_manifest.py`, `tools/campaign_usage_ledger.py`, `tools/check_parallel_dispatch_manifest.py`, `tools/build_candidate_package_record.py`, `tools/build_smoke_matrix_verdict.py`, `tools/run_five_smoke_matrix.py`, `tools/run_paired_cross_model_matrix.py`, `tools/check_paired_cross_model_manifest.py`, the fifth exact prompt fixture, and smoke/preflight fixture families.
- Plan A01 alone owns `schema/topology-review.schema.json`, `schema/topology-initial-assessment.schema.json`, `schema/cold-comprehensiveness-review.schema.json`, `schema/review-incident-report.schema.json`, `tools/check_topology_review.py`, `tools/check_review_incident_report.py`, and their checker semantics.
- Plan A11 alone owns the canonical validation registry, promotion profile,
  verdict classes, negative-expectation schema, and append-only
  `MODEL_SMOKE_ESCAPE` registry/checker semantics.
- Plan A12 alone owns the runtime call-context schema/resolver/checker; A13 owns producer-clause and harness/package parity while consuming A12's prompt projection.

`docs/audits/v0.4.6.0-wip-andon-contract-registry.json` records one row per A01-A16 with canonical plan/file identity, exact milestone dependencies, schema/tool owners, required case-registry reference, state-capsule contribution, and binding ADR references. `tools/check_andon_contract_registry.py` rejects duplicate A IDs/milestone IDs, duplicate schema identities, dangling dependencies, cycles in the expanded milestone graph, competing owners, stale plan filenames, noncanonical smoke IDs, missing/rejected ADRs, and any case set differing from A14's registry. It is a control-plane consistency check, not a semantic proof.

### Canonical runtime/edit owners supplied by the child plans

- `atomics/skill/**` for runtime law;
- `tools/check_staged_runtime_handshake.py` for stage contracts;
- `tools/run_staged_current_skill_smoke.py` for the staged producer/harness;
- `tools/build_staged_governed_output.py` for deterministic assembly;
- output/witness checkers named by A05-A10;
- fixtures under `tests/stage-contract-workbench/` and the new topic-neutral property suite.

### Generated files not to hand-edit

- `skill/**`
- generated framework pipeline Markdown
- generated docs index/portal surfaces
- generated closure-ledger Markdown

### 9.1 Durable evidence custody outside the mutable checkout

The ignored `.daee/` tree is a working capture surface, not sufficient long-term
custody. The owner-selected external root is
`C:\Users\theis\Documents\Codex\2026-07-08\dae\evidence\v0.4.6.0-wip-five-smoke\`
with create-if-absent `.staging`, `claims`, `cycles`, and `pointers` children.
Before a cycle can be reviewed or used for completion, its always-run
observation finalizer or root-failure fallback is exported there. Cycle
authorization binds unique staging, final, and publish-pointer paths; none is
reused across cycles.

`evidence-retention-manifest-v1` binds:

- campaign, candidate, cycle, source commit, registry, package, model protocol,
  and authorization hashes;
- every worker's raw response, output, prompt/call context, Stage01-Stage08
  records, capsule, sidecars, logs, exit status, and first-failure evidence;
- cycle claim/fallback, observation finalizer, barrier dispatch events,
  invocation/usage-head transactions, candidate-consumption,
  structural, cold-review, human-review, ANDON, and escape-registry artifacts;
- repository-relative working paths plus external custody object paths;
- byte length and SHA-256 for every file, bundle/tree digest, export timestamp,
  storage class, accountable custodian, and indefinite-retention policy;
- copy/readback command results and a later integrity-check schedule;
- explicit missing-artifact rows. Missing evidence cannot disappear by omission
  from the manifest.

The exporter writes to an authorization-bound unique staging path, verifies all
object hashes and the manifest, then atomically publishes an unused final cycle
directory or CAS-advances an immutable object-store pointer. A hash-equal resume
under the same claim/export lineage is permitted; hash mismatch, overwrite, or
staging offered as final is rejected. A failed export leaves the working cycle
and partial staging frozen and completion
`PARTIAL`; it does not cause the raw `.daee` evidence to be deleted. There is no
automatic expiry. Any deletion, compaction, or pruning is a separately
authorized custody event that records exact removed hashes, reason, and
permanent manifest/provenance/removal-reason residue.

The checker proves byte/hash inventory and path containment only. It does not
claim that the storage service is infallible or that a copied model answer is
true. When no approved external root is available, model execution is blocked
before dispatch unless the authorization explicitly names an equally durable
alternative and its readback method.

## 10. Canonical Fifth Input Registration

Case ID:

```text
gate88-torah-quran-source-authentication
```

Canonical source path:

```text
tests/smokes/v0.4.3.0-release-regression/prompts/07-torah-quran-source-authentication.md
```

The canonical bytes are owned once by Plan A14's **Exact Fifth Input** block and, after implementation, by the fixture file itself. The active owner request contains doubled backslashes in the skill-link target. With UTF-8, LF line endings, and one final LF, the approved planning representation is 1,396 bytes with SHA-256 `ECE0E206447AE9EF9F2BC9987DA647BC220782E5B9C225EBC77DAAF97B465F57`. This plan does not duplicate the body because a second literal already drifted during review. During implementation, create the file from Plan A14, recompute its hash, and make the one JSON smoke registry the only downstream source. Do not add expected burdens, expected submoves, source lists, citations, answer outlines, or conclusions.

The other registry rows point to the existing canonical prompt files:

| Case ID | Input path |
| --- | --- |
| `gate88-trinitarian-j173` | `tests/smokes/v0.4.3.0-release-regression/prompts/01-trinitarian-j173.md` |
| `gate88-tst-lillard` | `tests/smokes/v0.4.3.0-release-regression/prompts/02-tst-lillard.md` |
| `gate88-khaybar` | `tests/smokes/v0.4.3.0-release-regression/prompts/03-khaybar.md` |
| `gate88-secularism` | `tests/smokes/v0.4.3.0-release-regression/prompts/06-secularism.md` |
| `gate88-torah-quran-source-authentication` | `tests/smokes/v0.4.3.0-release-regression/prompts/07-torah-quran-source-authentication.md` |

This table is explanatory only. The sole machine source is `tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json`, owned by Plan A14 and validated under `schema/smoke-matrix.schema.json`. Preflight, launcher, verdict builder, and sustainment consume that registry; none duplicates a case array.

## 11. Smoke-Matrix Manifest and Pass Rule

The canonical registry contains only identity and input custody. A completed cycle manifest adds evidence:

```json
{
  "schema": "daee-smoke-matrix-v1",
  "kind": "cycle-verdict",
  "matrix_id": "20260709T000000Z-final-candidate",
  "cycle_ordinal": 1,
  "predecessor_cycle_verdict_sha256": null,
  "triggering_andon_ids": [],
  "countermeasure_set_sha256": null,
  "campaign_authorization_sha256": "64-lowercase-hex",
  "cycle_authorization_sha256": "64-lowercase-hex",
  "protocol_id": "immutable-protocol-id",
  "runtime_commit": "40-lowercase-hex",
  "runtime_sha256": "64-lowercase-hex",
  "package_sha256": "64-lowercase-hex",
  "producer_entrypoint": "tools/run_five_smoke_matrix.py",
  "model_runner": "codex",
  "runner_adapter_version": "exact resolved version",
  "model": "exact owner-approved identifier",
  "reasoning_effort": "high",
  "host": "exact host/application version",
  "model_parameters_sha256": "64-lowercase-hex",
  "no_model_candidate_maturity_sha256": "64-lowercase-hex",
  "model_smoke_escape_registry_sha256": "64-lowercase-hex",
  "pushed_green_ci_readback_sha256": "64-lowercase-hex",
  "parallel_protocol": "barrier-five-submit-before-await-v1",
  "dispatch_event_manifest_sha256": "64-lowercase-hex",
  "invocation_usage_receipt_sha256": "64-lowercase-hex",
  "campaign_usage_resulting_head_sha256": "64-lowercase-hex",
  "candidate_consumption_receipt_sha256": "64-lowercase-hex",
  "cycle_observation_finalizer_sha256": "64-lowercase-hex",
  "evidence_retention_manifest_sha256": "64-lowercase-hex",
  "observation_finalizer_status": "FINALIZED",
  "cases": [],
  "structural_matrix_status": "PASS | FAIL | PARTIAL",
  "completion_status": "PASS | FAIL | PARTIAL",
  "regression_status": "unproven",
  "non_claims": [
    "structural PASS is not semantic truth",
    "five cases do not prove arbitrary-input behavior",
    "T_lang does not prove uptake"
  ]
}
```

This is a compact view of A14's discriminated `daee-smoke-matrix-v1`, not a second schema. A14 alone owns `schema/smoke-matrix.schema.json`; A16 consumes it. Each case row also carries the A11 promotion-verdict path/hash, canonical validation-registry hash, structural status, A01 cold-review path/hash/comprehension/coverage verdict, and A01 human topology-review path/hash/verdict/adjudication.

Each case row includes:

- exact input path/hash/bytes;
- run directory and hash record;
- Stage01-Stage08 statuses and record hashes;
- output hash/bytes and truncation state;
- prompt-pack and capsule replay verdicts;
- candidate-output verifier verdict;
- post-run checker results;
- Plan A01 `daee-topology-review-v1` path/hash/review ID/verdict, reviewer relationship, and adjudication status;
- Plan A01 `daee-cold-comprehensiveness-review-v1` packet/review path/hash, exact GPT-5.6 model/host/prompt identity, comprehension status, challenge set, and coverage verdict;
- first failed stage/class when not PASS;
- retry, continuation, and normalization/repair history;
- terminal case status.

Aggregate `PASS` requires all of the following in one cycle:

1. exactly the five registered case IDs, once each;
2. exact input hashes match the registry;
3. same source/checker/runtime package identity and approved model protocol;
4. Stage01 through Stage08 pass for every case;
5. no truncation, refusal, hidden continuation, or post-output repair;
6. every required post-run structural checker exits zero;
7. cold GPT-5.6 comprehension is PASS and every material challenge is answered with new hash-bound target evidence or fails/partials the cycle;
8. independent human topology/substantive review is PASS for every case; its initial assessment hash predates cold-review disclosure, its adjudication IDs exactly equal cold finding IDs, and a patch-owner material reversal has a second hash-bound independent review;
9. no live/held/unresolved obligation remains in a way that makes the case terminally PARTIAL;
10. custody artifacts and hashes exist;
11. A11 promotion and A13 paired-lane verdicts are bound to the same cycle;
12. cycle claim/fallback, barrier dispatch events, canonical usage-head
    reservation/settlement, neutral candidate consumption, observation
    finalizer, and final external publish/readback artifacts reconcile to the
    same single-use candidate/cycle;
13. no `YES` or `UNKNOWN` model-smoke escape is open, no adjudicated
    reassessment is unresolved, and the exact child reservations plus factual
    campaign usage head reconcile;
14. non-claims are present.

A truthful `PARTIAL` output may be structurally valid, but it does not count as a final completion-matrix PASS. One failed or partial case makes the cycle aggregate `FAIL` or `PARTIAL`. Results are not averaged. Passing rows from an earlier cycle cannot be combined with later rows to manufacture a green final cycle. Every successor cycle binds `predecessor_cycle_verdict_sha256`, triggering ANDON IDs, the countermeasure-set hash, pushed-green CI receipt, and a strictly increasing cycle ordinal.

## 12. Test-Driven Ledger and Registry Implementation

### Phase 0: Baseline and drift stop

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
$expected = '6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c'
$actual = (git rev-parse HEAD).Trim()
if ($actual -ne $expected) { throw "planning baseline drift: $actual" }
if ((git status --short --untracked-files=all | Measure-Object).Count -ne 0) { throw 'planning baseline is not clean' }
python tools\run_local_ci.py --list
python tools\run_no_model_preflight.py --self-test
```

Expected at the planning baseline: clean expected head; both Python commands exit `0`. If the head has legitimately advanced before implementation, do not force this assertion to pass. Refresh every owner/file/command claim and replace the planned baseline in the ledger.

### Phase 1: Red tests for terminal-state overclaim

Add invalid fixtures first:

- closed row with open dependency;
- `HANDOFF` and completion together;
- five-smoke PASS with four cases;
- matrix PASS containing one PARTIAL case;
- structural PASS labeled semantic truth;
- stale source commit;
- owner-gated action marked performed without authorization evidence.
- failed model cycle without an always-run observation finalizer or candidate consumption receipt;
- candidate consumption claims PASS/FAIL before review;
- producer and cold reviewer fork the campaign usage head;
- orphaned usage reservation is returned to capacity;
- `parallelism=5` trace awaits a result before the fifth request is accepted;
- cycle-root failure lacks an external claim/fallback record;
- partial/hash-drifted staging is called final evidence;
- successor cycle missing predecessor ANDON/countermeasure/pushed-green lineage;
- open or `UNKNOWN` `MODEL_SMOKE_ESCAPE` marked model-eligible;
- structural/human PASS with missing cold GPT-5.6 reconstruction;
- upheld material review finding under completion PASS;
- patch-owner adjudication overturning a material FAIL without second independent review;
- cold finding omitted/duplicated in human adjudication or initial human
  assessment changed after cold disclosure;
- two ANDON rows sharing a root fingerprint but naming contradictory countermeasures;
- mixed-cycle five-case splice or consumed candidate reuse.

Target commands:

```powershell
python tools\check_andon_closure_ledger.py --self-test
python tools\check_architecture_decision_ledger.py --self-test
python tools\check_andon_contract_registry.py --self-test
python tools\check_release_action_authorization.py --self-test
python tools\check_vcs_action_authorization.py --self-test
python tools\check_ci_readback.py --self-test
python tools\check_no_model_candidate_maturity.py --self-test
python tools\check_smoke_matrix_manifest.py --self-test
```

Expected before implementation: commands do not exist or red tests fail. Expected after implementation: exit `0`, meaning valid fixtures pass and every registered invalid fixture fails for its pinned class.

Right-reason check after implementation:

```powershell
$raw = python tools\check_andon_closure_ledger.py --explain tests\andon-closure-ledger\invalid\handoff-and-complete.json
$exit = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($exit -ne 1) { throw "expected exit 1, got $exit" }
if ($diag.failure_class -ne 'contradictory-terminal-state') { throw "wrong class: $($diag.failure_class)" }
```

```powershell
python tools\assert_expected_rejection.py --expectation tests\andon-closure-ledger\invalid\handoff-and-complete.expectation.json --artifact-root auto
```

This canonical wrapper is rerun at Order 8 after the A11 validation scaffold exists; it is not a prerequisite for creating the Order 0 ledger. Expected then: exit `0`; the control-plane expectation proves the exact contradiction class and forbids generated closure views, completion verdicts, package, or release artifacts.

### Phase 2: Implement canonical ledgers, binding decisions, and renderer

```powershell
python tools\check_architecture_decision_ledger.py --ledger docs\audits\v0.4.6.0-wip-architecture-decisions.json --require-status accepted
if ($LASTEXITCODE -ne 0) { throw 'binding architecture decisions are missing, stale, or contradictory' }
python tools\check_andon_contract_registry.py --registry docs\audits\v0.4.6.0-wip-andon-contract-registry.json --decision-ledger docs\audits\v0.4.6.0-wip-architecture-decisions.json
if ($LASTEXITCODE -ne 0) { throw 'ANDON contract/ADR ownership registry failed' }
python tools\check_andon_closure_ledger.py --ledger docs\audits\v0.4.6.0-wip-andon-closure-ledger.json
if ($LASTEXITCODE -ne 0) { throw 'canonical ANDON closure ledger failed' }
python tools\render_andon_closure_ledger.py --ledger docs\audits\v0.4.6.0-wip-andon-closure-ledger.json --out docs\audits\v0.4.6.0-wip-andon-closure-ledger.md
if ($LASTEXITCODE -ne 0) { throw 'closure-ledger render failed' }
python tools\render_andon_closure_ledger.py --ledger docs\audits\v0.4.6.0-wip-andon-closure-ledger.json --check docs\audits\v0.4.6.0-wip-andon-closure-ledger.md
if ($LASTEXITCODE -ne 0) { throw 'generated closure-ledger view is stale' }
```

Expected: all exit `0`; all binding ADRs are accepted, every child contract resolves to them without a second owner, renderer is deterministic, and manual edits to generated Markdown cause `--check` to fail. Update the canonical JSON closure ledger after every subsequent patch/checkpoint; Phase 2 creates the control surface and does not postpone ledger population until P2.

### Phase 3: Register five exact inputs

```powershell
python tools\check_smoke_matrix_manifest.py --manifest tests\smoke-matrix\v0.4.6.0-wip-five-smoke.json --inputs-only
if ($LASTEXITCODE -ne 0) { throw 'five-smoke input registry failed validation' }
$inputCheckRun = Join-Path '.daee\no-model-preflight' ('torah-quran-input-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $inputCheckRun) { throw "input-check run already exists: $inputCheckRun" }
python tools\run_staged_current_skill_smoke.py --preflight-input-only --case-name gate88-torah-quran-source-authentication --raw-input-path tests\smokes\v0.4.3.0-release-regression\prompts\07-torah-quran-source-authentication.md --run-dir $inputCheckRun
if ($LASTEXITCODE -ne 0) { throw 'fifth input preflight failed' }
```

Expected: both exit `0`; no model call, output, sidecar, retained promotion, or package action occurs. The run directory path must not already exist.

### Phase 4: Integrate deterministic control plane

Update the preflight registry, local CI, CI registry, docs, non-claims, and generated ledger checks.

```powershell
python tools\check_andon_closure_ledger.py --self-test
python tools\check_smoke_matrix_manifest.py --self-test
python tools\check_topology_capacity_properties.py --self-test
python tools\run_no_model_preflight.py --self-test
python tools\run_local_ci.py --strict-pwsh
$phase4Root = Join-Path '.daee\no-model-preflight' ('control-plane-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $phase4Root) { throw "preflight root already exists: $phase4Root" }
New-Item -ItemType Directory -Path $phase4Root | Out-Null
python tools\run_no_model_preflight.py --json (Join-Path $phase4Root 'preflight.json')
```

Expected: all exit `0`; final preflight line is `PREFLIGHT_GREEN_AWAITING_OWNER_AUTHORIZATION`; report lists all five input paths and the property gate and binds source head/dirty state, registry, checker profile, right-reason mutations, runtime/package, and freshness. This remains no-model evidence and grants no authorization.

### Phase 5: Prove no-model source preflight

The expensive model matrix is not the debugger. Before candidate build authorization, compose the source-owned deterministic evidence from A01-A15 and classify every prior paid-smoke escape:

```powershell
$maturityRoot = Join-Path '.daee\no-model-preflight' ('candidate-maturity-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $maturityRoot) { throw "maturity root already exists: $maturityRoot" }
New-Item -ItemType Directory -Path $maturityRoot | Out-Null
python tools\check_validation_registry.py --self-test
python tools\run_checker_mutation_sweep.py
python tools\check_topology_capacity_properties.py --self-test
python tools\check_cross_stage_projection.py --self-test
python tools\check_runtime_context_delivery.py --self-test
python tools\check_package_harness_parity.py --self-test
python tools\check_case_registry_taint.py --self-test
python tools\check_no_model_candidate_maturity.py --self-test
python tools\build_no_model_candidate_maturity_verdict.py --mode source-preflight --out (Join-Path $maturityRoot 'no-model-source-preflight.json')
if ($LASTEXITCODE -ne 0) { throw 'no-model source preflight verdict build failed' }
python tools\check_no_model_candidate_maturity.py --verdict (Join-Path $maturityRoot 'no-model-source-preflight.json') --require-status NO_MODEL_SOURCE_PREFLIGHT_GREEN
if ($LASTEXITCODE -ne 0) { throw 'source is not ready for candidate packaging' }
```

These are target commands after their owning plans land. The source-preflight verdict binds exact pushed source/clean-tree and CI readback, generated runtime, five-case registry, validation registry, historical failure replay, every `MODEL_SMOKE_ESCAPE`, red-old/green-new canary evidence, neighboring valid controls, right-reason mutation results, A15 metamorphic capacity, and A14 case-registry taint isolation. It deliberately does **not** claim package or candidate maturity. `YES` and `UNKNOWN` deterministic-detectability rows block packaging until the missing control is implemented or classification is resolved. `NO` requires an owner-reviewed explanation of why the behavior is genuinely model-semantic/probabilistic and what observability/review control remains.

This phase does not invoke a model or authorize the candidate build. It is the proof that branch-9 deterministic machinery has been used to discover small structural defects before packaging. Final `NO_MODEL_CANDIDATE_MATURE` is issued only after the immutable candidate exists and package-faithful checks join it below.

## 13. Owner-Gated Candidate Package and Final Five-Smoke Execution

### 13.1 Candidate execution-mini package gate

The package-faithful matrix cannot precede its package input. The following future procedure is forbidden in this planning task and requires an immutable A14 `candidate-package-build-authorization` manifest bound to the exact `NO_MODEL_SOURCE_PREFLIGHT_GREEN` verdict and pushed-SHA CI receipt. It creates an isolated test candidate only; it does not install, tag, publish, release, or mutate public state. The later matrix authorization is a second owner decision and must bind the resulting candidate-package-record and final `NO_MODEL_CANDIDATE_MATURE` hashes.

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
$buildAuthorization = [Environment]::GetEnvironmentVariable('DAEE_CANDIDATE_PACKAGE_BUILD_AUTHORIZATION')
if ([string]::IsNullOrWhiteSpace($buildAuthorization)) { throw 'DAEE_CANDIDATE_PACKAGE_BUILD_AUTHORIZATION is required' }
python tools\check_smoke_matrix_manifest.py --manifest $buildAuthorization --kind candidate-package-build-authorization --require-action build-candidate-package
if ($LASTEXITCODE -ne 0) { throw 'candidate package build authorization is invalid or stale' }
if ((git status --short --untracked-files=all | Measure-Object).Count -ne 0) { throw 'candidate package build requires a clean worktree' }
$buildAuth = Get-Content -Raw -LiteralPath $buildAuthorization | ConvertFrom-Json
$candidateBase = $buildAuth.custody_root
$packageProfile = $buildAuth.package_profile
$candidateId = $buildAuth.candidate_id
$claimReceipt = $buildAuth.claim_receipt_path
$failedRecordFallback = $buildAuth.failed_record_fallback_path
if ([string]::IsNullOrWhiteSpace($candidateBase)) { throw 'authorization custody_root is required' }
if ([string]::IsNullOrWhiteSpace($candidateId)) { throw 'authorization candidate_id is required' }
if ([string]::IsNullOrWhiteSpace($claimReceipt)) { throw 'authorization claim_receipt_path is required' }
if ([string]::IsNullOrWhiteSpace($failedRecordFallback)) { throw 'authorization failed_record_fallback_path is required' }
if ($packageProfile -ne 'execution-mini') { throw "candidate matrix requires execution-mini, got $packageProfile" }
$candidateRoot = Join-Path $candidateBase $candidateId
$artifact = Join-Path $candidateRoot 'daee-epistemics-v0.4.6.0-wip-execution-mini.skill.zip'
$extractRoot = Join-Path $candidateRoot 'extracted'
$record = Join-Path $candidateRoot 'candidate-package-record.json'
if (Test-Path -LiteralPath $candidateRoot) { throw "candidate root already exists: $candidateRoot" }
python tools\check_smoke_matrix_manifest.py --manifest $buildAuthorization --kind candidate-package-build-authorization --consume-once --candidate-id $candidateId --claim-receipt $claimReceipt
if ($LASTEXITCODE -ne 0) { throw 'candidate build authorization was already consumed or could not be atomically claimed' }
try {
  New-Item -ItemType Directory -Path $candidateRoot -ErrorAction Stop | Out-Null
  python tools\build_framework_pipeline.py
  if ($LASTEXITCODE -ne 0) { throw 'framework pipeline build failed' }
  python tools\build_compiled_runtime.py
  if ($LASTEXITCODE -ne 0) { throw 'compiled runtime build failed' }
  python tools\check_compiled_runtime_freshness.py
  if ($LASTEXITCODE -ne 0) { throw 'compiled runtime is stale' }
  git diff --quiet --
  if ($LASTEXITCODE -ne 0) { throw 'canonical rebuild changed tracked source/runtime; commit and re-authorize before candidate packaging' }
  git diff --cached --quiet --
  if ($LASTEXITCODE -ne 0) { throw 'candidate build may not use staged changes' }
  $unexpectedUntracked = @(git ls-files --others --exclude-standard | Where-Object { $_ -notlike '.daee/*' })
  if ($unexpectedUntracked.Count -ne 0) { throw "candidate build created untracked files outside custody root: $($unexpectedUntracked -join ', ')" }
  python tools\package_skill.py --profile $packageProfile $artifact
  if ($LASTEXITCODE -ne 0) { throw 'candidate execution-mini package build failed' }
  python tools\check_skill_package_artifact.py --profile $packageProfile $artifact
  if ($LASTEXITCODE -ne 0) { throw 'candidate package artifact validation failed' }
  Expand-Archive -LiteralPath $artifact -DestinationPath $extractRoot -ErrorAction Stop
  python tools\build_candidate_package_record.py --status READY_UNUSED --authorization $buildAuthorization --artifact $artifact --extract-root $extractRoot --out $record
  if ($LASTEXITCODE -ne 0) { throw 'candidate package custody record build failed' }
  python tools\check_smoke_matrix_manifest.py --manifest $record --kind candidate-package-record --require-status READY_UNUSED
  if ($LASTEXITCODE -ne 0) { throw 'candidate package custody record validation failed' }
} catch {
  $failureMessage = $_.Exception.Message
  $failedRecord = if (Test-Path -LiteralPath $candidateRoot -PathType Container) { $record } else { $failedRecordFallback }
  python tools\build_candidate_package_record.py --status QUARANTINED --authorization $buildAuthorization --claim-receipt $claimReceipt --candidate-root $candidateRoot --failure-message $failureMessage --out $failedRecord
  if ($LASTEXITCODE -ne 0) { throw "candidate failed and quarantine record could not be written: $failureMessage" }
  throw "candidate package quarantined in $failedRecord; never reuse or repair this candidate ID: $failureMessage"
}
```

Expected: every command exits `0`; `$record` has `status=READY_UNUSED` and binds the exact pushed source commit, CI-readback receipt, source-preflight verdict, generated runtime/build manifests, archive hash, extracted-tree hash, execution-mini profile, single-use authorization/claim-receipt hashes, candidate ID, and custody root. Any failed build leaves a `QUARANTINED` record in its immutable candidate directory or, when root creation fails, at the authorization-bound fallback path; it is never eligible for matrix authorization or in-place repair. The later matrix authorization binds `$record`, its hash, extracted-tree path, and final candidate-maturity verdict directly; no free-standing package-root environment value may override them.

### 13.1a Bind final no-model maturity to the immutable candidate

After the candidate exists, rerun the package/load-path projections and join the
source-preflight and candidate records. This is still a no-model operation:

```powershell
$sourcePreflight = Join-Path $maturityRoot 'no-model-source-preflight.json'
$candidateMaturity = Join-Path $candidateRoot 'no-model-candidate-maturity.json'
python tools\check_skill_package_artifact.py --profile execution-mini $artifact
if ($LASTEXITCODE -ne 0) { throw 'candidate package shape drifted before maturity join' }
python tools\check_runtime_context_delivery.py --package-root $extractRoot --package-only-self-test
if ($LASTEXITCODE -ne 0) { throw 'candidate package-only context delivery failed' }
python tools\check_route_shard_selection.py
if ($LASTEXITCODE -ne 0) { throw 'candidate source route-shard selection failed' }
python tools\measure_load_path_budget.py --enforce-ratchet --enforce
if ($LASTEXITCODE -ne 0) { throw 'candidate source load-path gates failed' }
python tools\build_no_model_candidate_maturity_verdict.py `
  --mode candidate `
  --source-preflight $sourcePreflight `
  --candidate-record $record `
  --package-root $extractRoot `
  --out $candidateMaturity
if ($LASTEXITCODE -ne 0) { throw 'candidate maturity join failed' }
python tools\check_no_model_candidate_maturity.py `
  --verdict $candidateMaturity `
  --require-status NO_MODEL_CANDIDATE_MATURE `
  --candidate-record $record
if ($LASTEXITCODE -ne 0) { throw 'candidate is not mature enough for model authorization' }
```

The exact package check command names are implementation targets and must be
reconciled with A12's existing package/load-path tools rather than creating
duplicate owners. The resulting verdict binds the `READY_UNUSED` record, source
preflight, exact-SHA CI receipt, archive/tree/build hashes, checker/escape
registries, generated runtime, route/load reports, and every deterministic
report used, including fake-Codex-adapter barrier ordering, campaign usage-head
conflict/orphan recovery, cycle-root fallback, and transactional-export
fixtures. Any change or terminal candidate transition invalidates it. The
later matrix authorization includes its path/hash; source-preflight alone cannot
authorize model spend.

### 13.2 Final five-smoke execution

The following is an exact future PowerShell procedure. It is **forbidden in this planning task** and may run only after the owner explicitly authorizes the exact model, spend, final source commit, cycle, and artifact-retention policy. The producer entrypoint and adapter are already settled as package-faithful `tools/run_five_smoke_matrix.py --model-runner codex`; execution records the exact resolved model, adapter, and host/application versions.

Required execution environment: `DAEE_SMOKE_AUTHORIZATION_MANIFEST` points to
an immutable one-use child authorization/protocol manifest minted by the named
coordinator under the active owner-issued standing campaign. The manifest itself
points to the hash-bound candidate record, composed preflight, final
candidate-maturity verdict, unused cycle/claim/fallback paths, canonical
campaign-usage head, and pre-approved external staging/final/pointer custody
paths. This plan never invents unbound values and never treats a reusable `YES`
flag or nonempty placeholder as approval. The child binds the parent hash,
delegated issuer, exact source commit, registry hash, runtime/package hash,
fixed `codex` runner adapter, exact model/resolved versions, exact five-call
reservation, factual usage/cost recording and anomaly policy, evidence lane,
retention paths/policy, barrier protocol, and launch window.

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
$registry = 'tests\smoke-matrix\v0.4.6.0-wip-five-smoke.json'
$authorization = [Environment]::GetEnvironmentVariable('DAEE_SMOKE_AUTHORIZATION_MANIFEST')
if ([string]::IsNullOrWhiteSpace($authorization)) { throw 'DAEE_SMOKE_AUTHORIZATION_MANIFEST is required' }
if ((git status --short --untracked-files=all | Measure-Object).Count -ne 0) { throw 'final candidate worktree must be clean' }
python tools\check_smoke_matrix_manifest.py --manifest $authorization --kind matrix-authorization --require-evidence-lane package-faithful
if ($LASTEXITCODE -ne 0) { throw 'matrix authorization is invalid, stale, overbroad, or bound to another candidate/source state' }
python tools\check_smoke_matrix_manifest.py --manifest $authorization --kind matrix-authorization --require-campaign-capacity --require-candidate-state READY_UNUSED --require-candidate-maturity NO_MODEL_CANDIDATE_MATURE
if ($LASTEXITCODE -ne 0) { throw 'campaign usage, candidate lifecycle, or no-model maturity blocks launch' }
$auth = Get-Content -Raw -LiteralPath $authorization | ConvertFrom-Json
$candidateRecord = Get-Content -Raw -LiteralPath $auth.candidate_package_record_path | ConvertFrom-Json
$cycle = $auth.cycle_id
$cycleRoot = $auth.matrix_root
$preflightReport = $auth.preflight_report_path
$candidateMaturity = $auth.no_model_candidate_maturity_path
$packageRoot = $candidateRecord.extracted_tree_path
$cycleClaim = $auth.cycle_claim_receipt_path
$failedFinalizerFallback = $auth.failed_observation_finalizer_fallback_path
$stagingRoot = $auth.external_evidence_staging_root
$finalRoot = $auth.external_evidence_final_root
$publishPointer = $auth.external_publish_pointer_path
$retentionManifest = $auth.evidence_retention_manifest_working_path
foreach ($required in @($cycle,$cycleRoot,$preflightReport,$candidateMaturity,$packageRoot,$cycleClaim,$failedFinalizerFallback,$stagingRoot,$finalRoot,$publishPointer,$retentionManifest)) {
  if ([string]::IsNullOrWhiteSpace($required)) { throw 'authorization/candidate record has an empty launch field' }
}
if (Test-Path -LiteralPath $cycleRoot) { throw "cycle already exists: $cycleRoot" }
if (Test-Path -LiteralPath $cycleClaim) { throw "cycle claim already exists: $cycleClaim" }
if (Test-Path -LiteralPath $finalRoot) { throw "external evidence final root already exists: $finalRoot" }
python tools\check_smoke_matrix_manifest.py --manifest $registry --inputs-only
if ($LASTEXITCODE -ne 0) { throw 'five-smoke input registry failed validation' }
python tools\check_no_model_candidate_maturity.py --verdict $candidateMaturity --require-status NO_MODEL_CANDIDATE_MATURE --candidate-record $auth.candidate_package_record_path
if ($LASTEXITCODE -ne 0) { throw 'bound no-model candidate maturity is invalid or stale' }
$runnerExit = 0
python tools\run_five_smoke_matrix.py `
  --registry $registry `
  --authorization-manifest $authorization `
  --preflight-report $preflightReport `
  --matrix-root $cycleRoot `
  --evidence-lane package-faithful `
  --package-root $packageRoot `
  --model-runner codex `
  --parallelism 5 `
  --parallel-protocol barrier-five-submit-before-await-v1 `
  --one-shot-policy complete-observation `
  --cycle-claim-receipt $cycleClaim `
  --failed-observation-finalizer-fallback $failedFinalizerFallback `
  --consume-authorization-once `
  --reserve-campaign-usage 5 `
  --campaign-usage-head $auth.campaign_usage_head_path `
  --expected-campaign-usage-head-sha256 $auth.expected_campaign_usage_head_sha256 `
  --expected-campaign-usage-sequence $auth.expected_campaign_usage_sequence
$runnerExit = $LASTEXITCODE
python tools\export_cycle_evidence_bundle.py `
  --cycle-root $cycleRoot `
  --fallback-finalizer $failedFinalizerFallback `
  --cycle-claim-receipt $cycleClaim `
  --staging-root $stagingRoot `
  --final-root $finalRoot `
  --publish-pointer $publishPointer `
  --authorization $authorization `
  --allow-failed-cycle `
  --resume-hash-equal-only `
  --out-manifest $retentionManifest
$exportExit = $LASTEXITCODE
if ($exportExit -eq 0) {
  python tools\check_evidence_retention_manifest.py --manifest $retentionManifest --readback
  $retentionExit = $LASTEXITCODE
} else {
  $retentionExit = $exportExit
}
if ($retentionExit -ne 0) { throw 'cycle evidence staging/publish/readback failed; freeze all evidence and block completion' }
if ($runnerExit -ne 0) { throw 'one or more one-shot cases failed/partial/not-run; complete cycle was finalized and retained; do not retry or promote' }
```

This is concurrent one-shot complete-observation execution: five isolated workers launch from one immutable authorization-bound snapshot with private context/home/temp/cache/session/run roots and read-only package views. The composed preflight and candidate-maturity reports are created before authorization and revalidated at launch; no unbound replacement is generated afterward. The coordinator runs capacity checks before claim where possible, then claims the cycle outside its working root, CAS-reserves five calls against the one campaign usage head, and proves the five-ready/five-in-flight-before-first-result barrier order. Each preauthorized registry case is attempted at most once; case-local product failure does not erase the other already-concurrent observations. The runner's `finally` path writes a neutral `cycle-observation-finalizer`, settled usage-head receipt or explicit orphan status, candidate-consumption receipt, artifact inventory, and a post-claim transition to `CONSUMED_OBSERVED`, `CONSUMED_NO_DISPATCH`, or `CONSUMED_DISPATCH_UNKNOWN`. Structural replay and reviewed `cycle-verdict` occur later. The wrapper stages, verifies, atomically publishes, and reads back the complete failed/partial/success cycle before returning. A proved provider/auth/capacity failure before claim leaves `READY_UNUSED`; systemic infrastructure failure trips the circuit breaker and records `NOT_RUN_INFRASTRUCTURE` for uncalled rows. Do not patch or retry in place. Product repair requires a new pushed-green source boundary and single-use candidate. Infrastructure-only repair may use the same pushed SHA with a fresh candidate/cycle after the external cause and no-model health are proven.

## 14. Exact Post-Run Verification

### 14.1 Structural replay before cold and human review

Run only after all five package-faithful calls in one cycle exit zero. Case paths come from A14's registry, never directory enumeration or a second ID list:

```powershell
$registry = 'tests\smoke-matrix\v0.4.6.0-wip-five-smoke.json'
$caseRowsRaw = @(python tools\smoke_matrix_registry.py --manifest $registry --emit-cases-json)
if ($LASTEXITCODE -ne 0) { throw 'canonical smoke registry read failed' }
$caseRows = @(($caseRowsRaw -join "`n") | ConvertFrom-Json)
if ($caseRows.Count -ne 5) { throw "registry emitted $($caseRows.Count) cases, expected 5" }
foreach ($caseRow in $caseRows) {
  $run = Get-Item -LiteralPath (Join-Path $cycleRoot $caseRow.case_id)
  $record = Join-Path $run.FullName 'records\staged-handoff-record.json'
  $output = Join-Path $run.FullName 'output.md'
  $capture = Join-Path $run.FullName 'capture-manifest.json'
  foreach ($path in @($record,$output,$capture)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "missing required artifact: $path" }
  }
  python tools\check_staged_runtime_handshake.py --records $record
  if ($LASTEXITCODE -ne 0) { throw "staged handshake replay failed: $($run.Name)" }
  $promotionVerdict = Join-Path $run.FullName 'promotion-verdict.json'
  python tools\verify_candidate_output.py --profile promotion --capture-manifest $capture --json-out $promotionVerdict
  if ($LASTEXITCODE -ne 0) { throw "promotion profile failed or quarantined: $($run.Name)" }
  python tools\check_validation_registry.py --verdict $promotionVerdict
  if ($LASTEXITCODE -ne 0) { throw "promotion verdict registry/hash validation failed: $($run.Name)" }
  python tools\check_topology_capacity_properties.py --replay-run $run.FullName
  if ($LASTEXITCODE -ne 0) { throw "topology replay failed: $($run.Name)" }
}
$preReviewVerdict = Join-Path $cycleRoot 'structural-pre-review-verdict.json'
python tools\build_smoke_matrix_verdict.py --mode structural-pre-review --registry $registry --cycle-root $cycleRoot --out $preReviewVerdict
if ($LASTEXITCODE -ne 0) { throw 'structural pre-review verdict build failed' }
python tools\check_smoke_matrix_manifest.py --kind structural-pre-review-verdict --manifest $preReviewVerdict
if ($LASTEXITCODE -ne 0) { throw 'structural pre-review verdict validation failed' }
```

Expected: structural replay and the pre-review verdict exit `0`. The artifact is required to report structural PASS and completion PARTIAL while cold GPT-5.6 and human reviews are absent.

### 14.2 Final completion after reviews and lane-parity evidence

After independent A01 cold GPT-5.6 and human reviews have been authored/adjudicated and A13's deterministic paired lane-parity verdict exists:

```powershell
foreach ($caseRow in $caseRows) {
  $run = Get-Item -LiteralPath (Join-Path $cycleRoot $caseRow.case_id)
  $coldReview = Join-Path $run.FullName 'cold-comprehensiveness-review.json'
  $topologyReview = Join-Path $run.FullName 'topology-review.json'
  if (-not (Test-Path -LiteralPath $coldReview -PathType Leaf)) { throw "missing cold review: $coldReview" }
  if (-not (Test-Path -LiteralPath $topologyReview -PathType Leaf)) { throw "missing topology review: $topologyReview" }
  python tools\check_cold_comprehensiveness_review.py --review $coldReview --require-comprehension-pass --require-final-disposition
  if ($LASTEXITCODE -ne 0) { throw "cold review custody/comprehension/disposition failed: $($run.Name)" }
  python tools\check_captured_output_manifest.py --topology-review $topologyReview
  if ($LASTEXITCODE -ne 0) { throw "topology review custody/adjudication failed: $($run.Name)" }
}
python tools\check_package_harness_parity.py --matrix-root $cycleRoot --require-evidence-lane package-faithful --require-paired-fixture-verdict
if ($LASTEXITCODE -ne 0) { throw 'package-faithful/lane-parity evidence failed' }
$finalVerdict = Join-Path $cycleRoot 'five-smoke-verdict.json'
python tools\build_smoke_matrix_verdict.py --mode completion --registry $registry --cycle-root $cycleRoot --out $finalVerdict
if ($LASTEXITCODE -ne 0) { throw 'five-smoke completion verdict build failed' }
python tools\check_smoke_matrix_manifest.py --kind cycle-verdict --manifest $finalVerdict
if ($LASTEXITCODE -ne 0) { throw 'five-smoke completion verdict validation failed' }
$final = Get-Content -Raw -LiteralPath $finalVerdict | ConvertFrom-Json
if ($final.completion_status -ne 'PASS') { throw "completion remains $($final.completion_status)" }
if ($final.regression_status -ne 'unproven') { throw 'completion verdict cannot advance regression causality' }
```

The proposed verdict commands are target CLI contracts to implement in Phase 1-5. They must bind hashes and reject mixed-cycle or partial rows. Plan A01's cold `daee-cold-comprehensiveness-review-v1` and independent human `daee-topology-review-v1` artifacts remain required for the final verdict; the builder must fail if either is absent, hash-drifted, self-reviewed under an independence claim, missing the cold comprehension reconstruction, missing an immutable initial-human-assessment hash claimed before cold disclosure, carrying a cold-finding/adjudication set mismatch, carrying an upheld/unresolved material challenge, calling a challenge `answered` without new hash-bound target evidence, or using patch-owner reversal without required second review. `REVIEW_INVALID` remains non-passing and emits an owner incident report before continuation. Transport/delivery retry preserves a valid packet hash; packet-construction repair preserves input/output but binds a new packet hash to predecessor/delta/red-green/anti-answer-bank evidence. A shared review-contract change repeats the whole cohort; candidate-intelligibility failure requires a successor candidate. The builder may never self-author either review. A second paid harness-assisted five-case run is not required.

## 15. P2 Package and Release Gates

### 15.1 WIP completion is not release

`FIVE_SMOKE_GREEN` plus closed P0/P1 rows permits `WIP_COMPLETE`. It does not authorize package creation, commit, push, issue filing, tag creation, GitHub Release mutation, asset upload, provenance publication, or public docs mutation.

### 15.2 Owner-gated package commands

The following commands are exact for a future `v0.4.6.0` `execution-mini` artifact, but are forbidden until the owner separately authorizes package creation through an immutable `release-action-authorization-v1` manifest. The manifest binds the exact source commit, clean-state digest, version, profile, output directory, allowed action `build-release-package`, validity window, and decision owner. It explicitly denies commit, push, tag, upload, publication, and release actions. A reusable boolean or a candidate-package authorization cannot satisfy this gate.

```json
{
  "schema": "release-action-authorization-v1",
  "kind": "release-action-authorization",
  "authorization_id": "owner-issued-immutable-id",
  "source_commit": "40-lowercase-hex",
  "clean_tree_sha256": "64-lowercase-hex",
  "version": "v0.4.6.0",
  "profile": "execution-mini",
  "output_directory": "build/authorized-unique-id",
  "allowed_actions": ["build-release-package"],
  "denied_actions": ["commit", "push", "tag", "upload", "publish", "release"],
  "valid_not_before": "RFC3339 timestamp",
  "valid_not_after": "RFC3339 timestamp",
  "decision_owner": "owner identity"
}
```

The checker requires exactly one allowed action, an unused output directory under the repository's permitted build root, current source/clean-state equality, and an unexpired window.

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
$authorizationPath = [Environment]::GetEnvironmentVariable('DAEE_RELEASE_PACKAGE_BUILD_AUTHORIZATION')
if ([string]::IsNullOrWhiteSpace($authorizationPath)) { throw 'DAEE_RELEASE_PACKAGE_BUILD_AUTHORIZATION is required' }
python tools\check_release_action_authorization.py --manifest $authorizationPath --require-action build-release-package
if ($LASTEXITCODE -ne 0) { throw 'release package authorization is invalid, stale, overbroad, or bound to another source state' }
if ((git status --short --untracked-files=all | Measure-Object).Count -ne 0) { throw 'release package build requires the authorization-bound clean worktree' }
$authorization = Get-Content -Raw -LiteralPath $authorizationPath | ConvertFrom-Json
$version = $authorization.version
$profile = $authorization.profile
$outputDir = $authorization.output_directory
if ($version -ne 'v0.4.6.0') { throw "unexpected authorized version: $version" }
if ($profile -ne 'execution-mini') { throw "unexpected authorized profile: $profile" }
$package = Join-Path $outputDir 'daee-epistemics-v0.4.6.0-execution-mini.skill.zip'
if (Test-Path -LiteralPath $package) { throw "refusing to overwrite existing release artifact: $package" }
python tools\package_skill.py --version $version --profile $profile --output-dir $outputDir
if ($LASTEXITCODE -ne 0) { throw 'package build failed' }
python tools\check_skill_package_artifact.py $package --expect-version $version --profile $profile
if ($LASTEXITCODE -ne 0) { throw 'package artifact validation failed' }
python tools\check_compiled_skill_self_contained.py --package $package
if ($LASTEXITCODE -ne 0) { throw 'package self-contained check failed' }
Get-FileHash -Algorithm SHA256 -LiteralPath $package
```

Package shape proves archive construction, not model behavior. The final matrix must separately bind the candidate package used for model runs if package-faithful evidence is claimed. A failed release-package build is quarantined under a fresh output path after its hash/state are recorded; it is never overwritten in place, and a replacement requires a new authorization manifest.

### 15.3 Provenance/readback verification

After an authorized provenance file exists:

```powershell
$package = 'build\daee-epistemics-v0.4.6.0-execution-mini.skill.zip'
$provenance = 'build\daee-epistemics-v0.4.6.0-execution-mini.provenance.json'
python tools\check_release_provenance.py --provenance $provenance --package $package --manifest skill\build-manifest.json --compiled-map skill\compiled-module-map.json --release-artifacts docs\release-artifacts.md --smoke-root $cycleRoot
```

Expected only after authorized artifacts exist: exit `0`. Missing provenance/package/smoke binding remains a blocker.

### 15.4 Commit, issue, push, tag, and release boundary

Repair-loop commit and push are pre-WIP actions but remain separate one-use owner gates. A campaign or matrix authorization cannot authorize VCS mutation. `schema/vcs-action-authorization.schema.json` owns two discriminated actions:

```json
{
  "schema": "vcs-action-authorization-v1",
  "kind": "commit-authorization",
  "authorization_id": "one-use-id",
  "action": "commit-countermeasure",
  "repository": "theislampill/daee-epistemics",
  "target_branch": "codex/v0.4.6.0-runtime-footprint",
  "parent_commit": "40-lowercase-hex",
  "exact_paths": ["owner/source/path"],
  "diff_sha256": "64-lowercase-hex",
  "commit_message_sha256": "64-lowercase-hex",
  "verification_verdict_sha256": "64-lowercase-hex",
  "allowed_actions": ["commit-countermeasure"],
  "denied_actions": ["push", "force-push", "tag", "release", "publish"],
  "valid_not_after": "RFC3339 timestamp",
  "nonce": "single-use nonce",
  "decision_owner": "owner identity"
}
```

```json
{
  "schema": "vcs-action-authorization-v1",
  "kind": "push-authorization",
  "authorization_id": "one-use-id",
  "action": "push-countermeasure",
  "repository": "theislampill/daee-epistemics",
  "target_ref": "refs/heads/codex/v0.4.6.0-runtime-footprint",
  "local_commit": "40-lowercase-hex",
  "expected_old_remote_oid": "40-lowercase-hex",
  "force": false,
  "required_checks": ["owner-designated workflow/check identifiers"],
  "allowed_actions": ["push-countermeasure"],
  "denied_actions": ["force-push", "tag", "release", "publish"],
  "valid_not_after": "RFC3339 timestamp",
  "nonce": "single-use nonce",
  "decision_owner": "owner identity"
}
```

`tools/check_vcs_action_authorization.py` validates exact action/path/diff/message/parent or ref/local/remote identities and atomically consumes the nonce. Immediately before push, the executor re-reads the remote ref and fails closed if it differs from `expected_old_remote_oid`. After push, `tools/check_ci_readback.py` builds `ci-readback-v1` for the exact pushed SHA and owner-designated required check set. The authorization records how that set was derived: workflow/job identity plus branch-protection or owner-decision readback at authorization time. At this baseline the repository workflow/job pair is `CI / runtime-checks`; the manual `Build Skill Artifact` workflow is not inferred to be required. If workflow or protection state changes, the old authorization is stale. Candidate build authorization must bind the resulting receipt; local green or CI for another SHA is insufficient.

No concrete mutation command is supplied here because the final explicit file list, commit SHA, authorization objects, issue destination/body, tag state, and artifact hash do not exist yet. Manufacturing those values would violate evidence custody. Before any such action, the executor must provide the owner with:

- clean/dirty state and complete diff;
- exact files to stage, never `git add .`;
- deterministic and five-smoke verdict hashes;
- proposed commit message and issue body;
- remote branch/tag/release readback;
- exact package/provenance hashes;
- rollback and replacement behavior.

The owner then authorizes each action separately. Issue authorization does not imply commit/push authorization; package authorization does not imply tag/release authorization.

Read-only prechecks that may be run before requesting authorization:

```powershell
git status --short --branch --untracked-files=all
git diff --check
git diff --stat
git ls-remote origin refs/heads/codex/v0.4.6.0-runtime-footprint refs/tags/v0.4.6.0
gh pr view 9 --repo theislampill/daee-epistemics --json state,isDraft,headRefOid,baseRefOid,url
gh release view v0.4.6.0 --repo theislampill/daee-epistemics --json tagName,assets,publishedAt,url
```

A “not found” release/tag readback may be expected before release, but it is not authorization to create either.

## 16. Rollback and Recovery

### Repo-local controls

- Revert ledger/schema/checker/fixture/docs wiring as one coherent patch if the contract is rejected.
- Regenerate compiled runtime and generated docs from canonical source after any rollback; never hand-edit generated artifacts.
- Preserve invalid fixtures and failed matrix directories. Mark them superseded; do not delete or repair raw evidence.
- If a child-plan patch causes deterministic failure, stop at the first failed check, revert only that coherent patch, and keep already-green independent controls.

### Matrix failure

- Do not resume a failed completion cycle as if it were the same one-shot run.
- The runner's neutral observation finalizer or root-failure fallback must preserve the claim, run directory when created, hash record, responses, capsules, prompt manifests, output, barrier dispatch events, usage-head reservation/settlement or orphan status, candidate `CONSUMED_OBSERVED`/`CONSUMED_NO_DISPATCH`/`CONSUMED_DISPATCH_UNKNOWN` receipt, and artifact inventory before returning nonzero. Structural and reviewed verdicts are derived later.
- Record first failed stage/class and affected ANDON row.
- Add a `MODEL_SMOKE_ESCAPE` process row for every defect first discovered by a paid/model smoke. `YES` or `UNKNOWN` deterministic detectability blocks another model cycle; `NO` requires owner-reviewed basis.
- Bind shared failures through `root_cause_id` while preserving each symptom row and canary.
- Patch only after owner authorization, prove red-old/green-new canaries, right-reason mutation coverage, Smoke A/B, and `NO_MODEL_CANDIDATE_MATURE`, then use one-use VCS authorizations, pushed-green CI readback, a new candidate, and a new cycle ID.
- The successor cycle binds predecessor cycle ID, triggering ANDON IDs, shared countermeasure-set hash, pushed-green CI receipt, and increasing ordinal.
- Do not combine old passing rows with new rows for aggregate completion.
- Do not reuse the consumed failed candidate or resample unchanged package/model settings as a repair claim.

### Package/release failure

- A matrix candidate and its `READY_UNUSED`/`CONSUMED_OBSERVED`/`CONSUMED_NO_DISPATCH`/`CONSUMED_DISPATCH_UNKNOWN`/`QUARANTINED` custody directory are immutable and are never removed, reset, or repaired in place.
- A separately authorized, unuploaded release-package attempt may be quarantined or removed from its unique `build/` attempt directory only after its hash/failure record is preserved; it is not a public rollback.
- A published artifact correction requires owner authorization, a new provenance/readback cycle, and truthful release-note treatment.
- Never force-move a tag or replace a public asset silently.

## 17. STOP / ANDON Conditions

Stop and emit a terminal record when:

- any mandatory P0/P1 dependency is open before the final matrix;
- `NO_MODEL_CANDIDATE_MATURE` is absent/hash-drifted or any model-smoke escape remains `YES`/`UNKNOWN` without required closure;
- an exact producer/review child reservation cannot be made safely, the shared
  CAS-governed usage head is conflicted or unresolved, a provider circuit
  breaker is open, or prior authorization/usage is rewritten;
- the final worktree or generated runtime is stale;
- the fifth input is missing, altered, empty, or accompanied by an answer bank;
- preflight ends `MATRIX_NOT_AUTHORIZED`;
- a smoke fails, truncates, refuses, enters PARTIAL, or needs a retry/continuation;
- five concurrent isolated workers cannot be established; the barrier lacks five
  accepted/in-flight acknowledgments before first-result observation; worker
  home/temp/cache/session roots overlap; or provider health/circuit-breaker
  contract fails;
- a failed/claimed cycle lacks its external claim, root-failure fallback,
  observation finalizer, usage-head settlement/recovery status, or neutral
  candidate-consumption transition;
- external evidence remains in staging, resumes over a hash mismatch, or lacks
  atomic final publish/readback;
- records, outputs, capsules, sidecars, or hashes are missing;
- a structural result is described as semantic truth or uptake;
- a passing row comes from another source commit, package, model protocol, or cycle;
- a cold review lacks comprehension reconstruction, receives prior context/expected topology, or has an upheld/unresolved material challenge under PASS;
- a patch-owner human overturns a material finding without new evidence and required second independent review;
- a consumed/quarantined candidate or consumed candidate authorization is reused;
- `regression_status` is advanced without the A01 comparison gate;
- a handoff and completion status coexist;
- an owner-gated action lacks explicit authorization;
- a package, issue, commit, push, tag, release, asset, or public docs mutation is attempted in this planning lane.

Required record:

```yaml
status: BLOCKED | DEFERRED | HANDOFF | PARTIAL | UNVERIFIED
andon_id: A01-A16
priority: P0 | P1 | P2
class: dependency-open | architecture-decision | deterministic-gate | model-smoke | model-smoke-escape | custody | cold-review | topology-review | infrastructure | package | provenance | authorization | claim-overreach
source_commit: <actual 40-hex value>
cycle_id: <actual cycle or null>
case_id: <actual case or null>
failing_command: <exact command or owner gate>
exit_code: <actual integer or null>
earliest_stage: <stage-01 through stage-08, infrastructure, or null>
failure_class: <controlled diagnostic or owner-gate class>
owner_source: <file/function/operator>
preserved_artifacts: <actual paths and hashes>
next_action: <one concrete patch, decision, or evidence request>
regression_status: unproven
```

The angle-bracket text documents required values. A real ledger row must replace it with evidence or explicit null where the schema allows null.

## 18. Definition of Done

### A16 sustainment control complete

- Canonical JSON ANDON ledger, schema, checker, renderer, valid/invalid fixtures, and generated Markdown view exist.
- The contract registry, binding ADRs, state-capsule-v2 migration ledger, and release-action authorization checker exist and pass their right-reason fixtures.
- The expanded binding ADR set, no-model maturity gate, one-use VCS authorization/CAS checks, CI-readback binding, single-use neutral candidate lifecycle, canonical campaign usage-head CAS, barrier concurrency proof, recoverable cycle claim, always-run observation finalizer, and transactional evidence publish pass right-reason fixtures.
- Handoff, blocked, deferred, structural green, scoped model green, WIP complete, RC ready, and released states are mutually coherent.
- Every A01-A16 row contains a real Five Whys chain to an owner/source, Hansei, countermeasure, follow-up control, Smoke A/B, right-reason negative, owner/artifact gates, and remaining risk.
- Stale commit/hash references fail closed.
- Structural PASS cannot be labeled semantic truth.

### v0.4.6.0-wip complete

- Every P0/P1 ANDON is implemented and at least structurally verified; owner-required closure decisions are recorded.
- Runtime source, generated runtime, docs, checkers, fixtures, and harness agree.
- `run_local_ci.py --strict-pwsh` passes at the final candidate commit.
- the composed no-model preflight passes at that same commit, includes all five input paths and topology-property tests, and ends with `PREFLIGHT_GREEN_AWAITING_OWNER_AUTHORIZATION`;
- `NO_MODEL_CANDIDATE_MATURE` binds that same pushed-green source/candidate boundary and no model-smoke escape remains open or unknown;
- one coordinator-minted, single-use execution-mini candidate child under the active standing campaign begins `READY_UNUSED` with source, pushed-green CI receipt, parent/delegation, archive, extracted-tree, build-manifest, and profile hashes bound, then ends `CONSUMED_OBSERVED` for the final cycle; PASS belongs only to the later reviewed verdict;
- secularism, Khaybar, J173, TST/Lillard, and Torah/Qur'an source authentication each pass Stage01-Stage08 in one final authorized package-faithful cycle using that candidate;
- package-faithful `tools/run_five_smoke_matrix.py --model-runner codex` uses
  `gpt-5.5` high with exact resolved versions retained; all five launch under
  isolated roots and the barrier proves five accepted/in-flight requests before
  any result is observed;
- the cycle has one CAS-settled campaign usage head, external claim/fallback,
  always-run neutral observation finalizer, and atomically published/read-back
  evidence bundle;
- the campaign used exact per-cycle reservations and factual cumulative
  accounting without a fixed cycle/cumulative-call give-up ceiling;
- every case has output, record, capsule, sidecar, hash, post-run checker, cold GPT-5.6 review, and independent human topology/substantive review evidence; the human's five initial assessments were hash-claimed before cold-review launch/disclosure;
- no cold challenge is upheld/unresolved under PASS; patch-owner material reversal has new evidence and second independent adjudication;
- the structural-pre-review verdict is PASS/PARTIAL at the correct boundary, the final cycle verdict is PASS/PASS only after all reviews, and both are immutable/hash-bound;
- A13's deterministic paired package-faithful/harness-assisted fixture verdict is PASS; no second paid harness-assisted five-case run is required;
- no case is partial, truncated, repaired, retried in place, or borrowed from another cycle;
- no fixed byte, burden, or submove floor decides PASS;
- no Torah/Qur'an answer bank exists;
- `regression_status` remains `unproven` unless A01's controlled evidence supports a stronger owner-reviewed status;
- terminal Hansei and the closure ledger are frozen/read back, then the owner
  explicitly accepts `WIP_COMPLETE`.

### Optional paired GPT/Opus compatibility complete

This later state is not required for initial WIP completion and is not
authorized by the initial campaign. After separately authorized Opus evaluation,
an accepted Opus product countermeasure that changes a candidate- or verdict-
bearing boundary requires:

- `CROSS_MODEL_RECONVERGENCE_REQUIRED` on the changed head while preserving the
  historical GPT verdict for its old SHA;
- two fresh sibling candidate identities with the same source/archive/tree/
  build-manifest hashes and separate GPT-5.5/high and exact Opus child protocols;
- one parent ten-worker barrier with all ten accepted/in flight before any
  result observation;
- five GPT and five Opus Stage01-Stage08 trajectories, followed by one human's
  ten hash-claimed pre-disclosure assessments, ten isolated cold reviews, and
  final human adjudication against the unchanged initial hashes;
- no material ANDON and no pass carry-forward from either child cohort;
- one immutable reviewed 10/10 parent verdict labeled only
  `POST_COMPLETION_CROSS_MODEL_COMPATIBILITY_PASS`.

An Opus accommodation that weakens notation, recursion, arbitrary topology,
anti-answer-bank discipline, body/witness fidelity, or GPT behavior is rejected
rather than promoted into DAEE.

### Release complete

Release completion is a later, separately authorized state requiring:

- exact package built from the final source commit;
- package shape/self-contained checks;
- package-bound five-smoke evidence if that claim is made;
- provenance pair and release-doc alignment;
- explicit commit/push/tag/release authorization;
- GitHub tag/release/asset readback and hash match;
- public docs/readback where applicable;
- no stale or contradictory release claim.

WIP completion does not satisfy this release definition.

## 19. Confidence

Ledger and state-machine plan: **YES, implementation-ready**.  
P0/P1 dependency order: **YES, sufficiently specified for patch sequencing, subject to child-plan schema integration**.  
Five-input registration and no-model preflight migration: **YES, implementation-ready**.  
No-model maturity/model-smoke escape control: **YES, implementation-ready as a target contract; unimplemented**.  
Final model matrix: **PARTIAL, owner/model/spend/artifact-gated and not run**.  
v0.4.6.0-wip completion: **NO, not yet proven**.  
Package/release readiness: **NO, owner-gated and unverified**.  
v0.4.6 regression causality: **unproven**.
