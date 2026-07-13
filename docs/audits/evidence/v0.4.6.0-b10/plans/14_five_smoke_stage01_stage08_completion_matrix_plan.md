# ANDON A14: Five-Smoke Stage01-Stage08 Completion Matrix

Priority: P0 release-line completion gate  
Planning baseline: PR #9 head `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
Regression status: `unproven`  
Plan status: implementation-ready for registry, fixture, checker, and runbook changes; no model call has run, and execution requires one owner-issued standing campaign, after which coordinator-minted one-use test-candidate, producer, and review children proceed without a per-cycle design pause

Packet identity: this concern is A14 and is implemented by file `14_...`. Producer/checker and harness/package parity remains A13 in file `13_...`.

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Intended Outcome

v0.4.6.0-wip is not complete until five exact inputs each traverse Stage01 through Stage08 under one frozen runtime and one predeclared protocol after the registered ANDON fixes. The required cases are:

1. `gate88-secularism`
2. `gate88-khaybar`
3. `gate88-trinitarian-j173`
4. `gate88-tst-lillard`
5. `gate88-torah-quran-source-authentication`

The matrix is an exact regression suite. It is not an argument bank. The registry stores input identity and custody metadata only. It must not store an expected noetic frame, burden count, burden IDs, submove count, owners, quotations, sources, response outline, answer length, or theological conclusion.

Five is the release test-suite cardinality. It is not a runtime burden or submove floor.

## Abnormality

The current no-model preflight can print `MATRIX_AUTHORIZED_AFTER_PREFLIGHT` after checking only four smoke input paths. Its Gate 14 iterates `FOUR_SMOKE_CASES` and assumes each input already lives under a retained-proof case directory. That design cannot safely add the new source-authentication input without either:

- creating a retained case before any current Stage08 pass exists; or
- pointing Gate 14 at a nonexistent retained input and failing preflight.

The historical four retained outputs also predate parts of the current contract and are explicitly schema-light row evidence. They are useful retained replay fixtures, but they are not fresh v0.4.6.0-wip model evidence. A four-case preflight or retained replay can therefore be green while the new five-case completion requirement is unmet.

## Current False-Pass

Current behavior:

```text
FOUR_SMOKE_CASES contains four IDs
Gate 14 validates four retained input paths
all 16 no-model gates can pass
terminal token says MATRIX_AUTHORIZED_AFTER_PREFLIGHT
fifth input is absent
```

Relative to the new release requirement, that is an authorization false-positive. The token remains truthful only for the old four-case launch contract.

The matrix has additional evidence gaps:

- no fifth canonical prompt fixture;
- no single machine registry binding all five exact inputs;
- no matrix checker that requires one unique Stage01-Stage08 record per case;
- no aggregate check for one runtime hash, input hashes, model/runner controls, no semantic repairs, and all five Stage08 records;
- no required independent topology review per case;
- no fresh model outputs in the planning workspace.

## Evidence Classification

### Confirmed

- The current canonical prompt directory contains the four existing smoke inputs.
- `run_no_model_preflight.py` hardcodes four IDs and derives input paths from retained case directories.
- The staged runner exposes exact CLI flags for case name, raw input path, run directory, model, model runner, output mode, output target, expansion rounds, transport retries, and stop stage.
- The runner stage order is exactly Stage01 intake, Stage02 diagnostic IR, Stage03 routing, Stage04 ACT, Stage05 MRP/reread, Stage06 witness/NAR, Stage07 release, Stage08 verifier sidecars.
- A successful full run writes `records/staged-handoff-record.json`, `output.md`, `prompt-pack-manifest.jsonl`, `state-capsules/`, `proof-sidecars/`, and `staged-smoke.hashes.json`.
- A failed run preserves `records/staged-handoff-failure.json` and a negative hash record.
- Historical Gate88 rows are classified `SIDECAR_BACKED_STRUCTURAL`, not semantic truth.
- No model smoke was run during this planning pass.

### Inferred

- The fifth input is a strong topology stress case because it combines a deconversion narrative, consistency claim, beneficiary challenge, corruption hypothesis, comparative revelation claim, and an epistemic invitation. This description does not prescribe how many burdens the runtime should select.
- A source-authentication case can expose early pressure loss, under-splitting, generated/baseline provenance drift, and witness reconstruction defects better than one-topic prompts.

### Unproven

- The exact noetic topology the fifth input should produce.
- Whether any of the five will pass after implementation.
- Whether a 5/5 structural pass is semantically adequate without human review.
- Whether v46 caused a regression relative to v45.
- Package-only parity until the separate parity lane in Plan 13 runs.

## Canonical Input Registry

Use canonical prompt files, not retained-proof directories, as the five-case launch source. Retained rows remain downstream promotion artifacts.

| Case ID | Canonical input path | Current/planned LF byte count | Current/planned raw SHA-256 | Status |
| --- | --- | ---: | --- | --- |
| `gate88-trinitarian-j173` | `tests/smokes/v0.4.3.0-release-regression/prompts/01-trinitarian-j173.md` | 1,095 | `DD7B21625FA55ECDC47110927C00EB66BC9919EF0576DB9076249A7FC197845C` | Confirmed current file |
| `gate88-tst-lillard` | `tests/smokes/v0.4.3.0-release-regression/prompts/02-tst-lillard.md` | 560 | `0A901886CEFADFCBA596D999A8716BDEA889AA729B71C960821CDAFD2DFDAC36` | Confirmed current file |
| `gate88-khaybar` | `tests/smokes/v0.4.3.0-release-regression/prompts/03-khaybar.md` | 4,896 | `76351ACEB44F9836F6AD7763D91A80D660BF2840FEE5C948FE6753D1774127A9` | Confirmed current file |
| `gate88-secularism` | `tests/smokes/v0.4.3.0-release-regression/prompts/06-secularism.md` | 35 | `F315B91F2B2BD3531FC1714F01A5682F0588180D71AEB6C7BE895122EE1D7E70` | Confirmed current file |
| `gate88-torah-quran-source-authentication` | `tests/smokes/v0.4.3.0-release-regression/prompts/07-torah-quran-source-authentication.md` | 1,396 | `ECE0E206447AE9EF9F2BC9987DA647BC220782E5B9C225EBC77DAAF97B465F57` | Planned exact LF fixture; unproven until added and rehashed |

The first four retained `input.txt` files are logically equivalent to their canonical prompt Git blobs, but some physical worktree copies use different line endings. `check_retained_proof_corpus.py` deliberately normalizes CRLF/CR to LF before hashing. The launch registry must avoid ambiguity by using the canonical `.md` prompt files, requiring LF, and recording both raw-run SHA and any repository-normalized hash explicitly. Do not silently compare a raw-byte digest with a normalized-text digest.

## Exact Fifth Input

The new fixture must contain exactly the following UTF-8 text with LF line endings and one final LF. The trailing space after `refute:` is part of the supplied line and must be retained unless the owner explicitly authorizes normalization. The expected raw byte count/hash above was calculated from this exact representation and must be independently recomputed after the file is created.

````text
[$daee-epistemics](C:\\Users\\theis\\.codex\\skills\\daee-epistemics\\SKILL.md) refute: 
```
When I was Muslim, I was told the Bible was full of contradictions.

So one day I picked up the Torah and read it for myself.

What I found wasn't contradiction. It was consistency.

Detailed timelines. Genealogies. Covenants. Laws. Sacrifices. Mercy. Prophecy. A unified story unfolding across generations with God's fingerprints all over it.

Then I went back and compared those same stories in the Quran.

Moses. Abraham. Noah. Joseph.
Same names. Different details. Different timelines. Different theology.

That forced me to ask a simple question:
If the Torah was corrupted, who corrupted it, and what did they gain?
Did it make Israel look better? No. The text constantly exposes their failures.

Did it make the prophets look perfect? No. David sins. Moses disobeys. The heroes are flawed and God alone gets the glory.

Did it make religion easier to follow? Definitely not. Read Leviticus.

So who exactly benefited from rewriting it?

The Quran affirms the Torah as revelation from God, yet often presents conflicting versions of key events. The more I studied, the more I felt like I wasn't looking at a correction of the story, but a revision of it.

Reading the Torah for myself started a journey that forced me to question everything I thought I knew.
Truth can handle investigation.

```
````

This fixture is input evidence only. No expected response accompanies it.

## Formal-Chain Acceptance

Every case must preserve the full governed chain:

```text
N |- D0
  -> PsiN<N in N,m,tau,sigma,heart,xi,Omega,mu,kappa,H>
  -> IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)
  -> route gradient
  -> Bn
  -> {Bni[OPi]}
  -> Land(Bn)
  -> Delta Bn{heart,xi,Omega,sigma,mu}/Delta kappa
  -> divergence/curl
  -> LoopBreak(curl)
  -> R(H,Delta,Delta-kappa)
  -> C(PsiN)
  -> N_fitri and sound reason
  -> T_lang: PsiN -> PsiI
```

The test does not require a fixed number of burdens or operations. It requires all runtime-selected obligations to remain reconstructible from exact input through final transfer.

## Stage01-Stage08 Completion Map

| Stage | Current owner and evidence | Required post-ANDON contract | Per-case pass condition | STOP/ANDON condition |
| --- | --- | --- | --- | --- |
| Stage01 intake | `run_staged_current_skill_smoke.py` Stage01 prompt; handshake Stage01 validator; raw input/hash record | Exact registry input, source observation anchors, no completion claim | input hash matches registry; Stage01 record validates; observation coverage is present under the migrated topology contract | input drift, missing span, early `COMPLETE`, or case/path metadata used as routing evidence |
| Stage02 Layer-A/IR | `diagnostic-ir.md`; Stage02 handshake/workbench | Candidate states and source pressures receive routed/merged/held/non-load-bearing/unresolved dispositions; `B_LA` contains only initial burdens | no unaccounted source unit; topology review finds no material omission; cardinality is runtime-derived | bare burden list on a release-bearing record, unresolved pressure hidden, topic-keyed expected burden count |
| Stage03 route/owner gate | routing atomics; Stage03 checker | Every pressure-to-burden split/merge is reconstructible; every route target has an owner/gate status | route targets equal the licensed Stage02 burden set; merges carry proof; held alternatives remain visible | unproved merge, disappearing candidate state, owner not licensed, generated burden predeclared |
| Stage04 burden execution/ACT | recursive-state/ACT law; Stage04 checker | Every distinct owner/register operation obligation receives an ACT body or explicit terminal disposition | operation manifest has complete target, owner, performed operation, delta, residual, Land contribution, and body reference | routed obligation absent, label-only/bodyless row, semantic repair by harness, fixed submove quota |
| Stage05 MRP/reread | `TTP-MRP-mid-reread-pressure.md`; Stage05 checker | One honest reread per terminal burden; generated/held/pre-empted/no-resultant states are mutually exclusive and sourced | raw producer record passes without STOP-to-RECURSE or graph mutation; all resultants are terminally accounted | generated burden in `B_LA`, held/pre-empted pressure disappears, semantic normalizer manufactures route/edge |
| Stage06 field witness/NAR | witness/recursive state source; Stage06 checker | Stage02-05 trajectory projects exactly into witness/NAR with owner/body/provenance parity | witness body refs, owners, operations, deltas, terminal states, generated burdens, and edges match upstream records | boolean/sparse witness substitutes for projection, body/owner cardinality mismatch, dialect ambiguity |
| Stage07 release output | `output-release.md`, render contract, assembler, 12-key release battery | Topology-derived segments; actual capsule/shard inputs; one final public tail; no fixed byte floor | release battery green; output reconstructs all obligations; no semantic repair events; independent topology/body review PASS | missing/duplicate/unassigned body refs, trajectory loss, padded byte target, contradictory tail, false completion |
| Stage08 verifier sidecars | sidecar builders, handshake Stage08, hash record | Sidecars bind exact Stage07 output/input/runtime; structural scope remains explicit | full handoff record has all eight ordered stages `status=pass`; sidecars/hashes validate; B5 eligibility satisfied | sidecar build/check failure, hash mismatch, Stage07 HOLD/PARTIAL promoted, structural PASS described as semantic truth |

Stage01-Stage08 structural PASS is necessary but not sufficient. Each case also needs a signed topology/body adjudication because a machine can verify declared set relationships but cannot prove every source pressure was semantically classified correctly.

## Five Whys

1. **Why is the fifth smoke absent from completion evidence?**  
   The current launch source is a hardcoded tuple of four historical Gate88 IDs.

2. **Why is the launch source hardcoded to those four?**  
   Gate 14 derives case identity and input paths from already promoted retained-proof directories rather than from an independent input registry.

3. **Why are input registration and retained promotion coupled?**  
   The first four inputs already existed in the retained corpus, so the implementation reused that corpus as the launch registry and never created a schema separating “eligible exact input” from “passed output evidence.”

4. **Why was that lifecycle distinction never made machine-readable?**  
   The smoke control evolved from historical regression replay and deterministic preflight checks, with no canonical owner for current matrix membership, authorization binding, one-cycle execution, and post-pass promotion.

5. **Why could several separate controls remain the effective completion gate?**  
   No release-matrix contract required one versioned case registry, one non-authorizing readiness token, one immutable Stage01-Stage08 cycle record, and one promotion rule shared by preflight, launcher, verdict builder, and docs.

This is a major ANDON because the omitted case exercises unknown-at-design-time topology. The severity is the consequence of the causal chain, not a substitute for its fifth why.

**Actionable root owner/source:** input registry and Gate 14 in `tools/run_no_model_preflight.py`, canonical prompt fixtures under `tests/smokes/.../prompts`, full-run custody in `tools/run_staged_current_skill_smoke.py`, and a new matrix-completion checker. The Torah/Qur'an technique catalogue is not the root owner and must not be expanded into a golden answer.

## Hansei

### What worked

- The four existing inputs and retained outputs have durable identities.
- The staged runner already preserves failures, stage records, output, capsules, prompt manifests, and sidecars.
- The one-shot and first-failure disciplines are documented.
- The no-model preflight correctly refuses to authorize when any deterministic gate fails.

### What failed

- “Four-smoke” became both a historical label and a current completion assumption.
- Input custody was coupled to retained promotion.
- Earlier plans used placeholder commands and did not require exact input hashes or one record per case.
- Historical retained replay could be misread as fresh model proof.
- No single completion artifact distinguished structural, topology-review, package-faithful custody/paired-lane evidence, owner-gated, and regression-causality statuses.

### Lessons

- Register inputs before runs; promote outputs only after successful, authorized evidence review.
- A completion matrix is a conjunction of five independently valid case records. It is not an average.
- Every retry is a new attempt ID. A failed one-shot remains evidence and is never overwritten.
- Exact fixture identity is allowed. Expected topology or answer content is not.

## Target Registry Contract

Replace `FOUR_SMOKE_CASES` with one versioned JSON source of truth:

```text
tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json
```

```json
{
  "schema": "daee-smoke-matrix-v1",
  "kind": "input-registry",
  "matrix_id": "v0.4.6.0-wip-five-smoke",
  "cases": [
    {"case_id": "gate88-secularism", "input_path": "tests/smokes/v0.4.3.0-release-regression/prompts/06-secularism.md", "raw_bytes": 35, "raw_sha256": "F315B91F2B2BD3531FC1714F01A5682F0588180D71AEB6C7BE895122EE1D7E70"},
    {"case_id": "gate88-khaybar", "input_path": "tests/smokes/v0.4.3.0-release-regression/prompts/03-khaybar.md", "raw_bytes": 4896, "raw_sha256": "76351ACEB44F9836F6AD7763D91A80D660BF2840FEE5C948FE6753D1774127A9"},
    {"case_id": "gate88-trinitarian-j173", "input_path": "tests/smokes/v0.4.3.0-release-regression/prompts/01-trinitarian-j173.md", "raw_bytes": 1095, "raw_sha256": "DD7B21625FA55ECDC47110927C00EB66BC9919EF0576DB9076249A7FC197845C"},
    {"case_id": "gate88-tst-lillard", "input_path": "tests/smokes/v0.4.3.0-release-regression/prompts/02-tst-lillard.md", "raw_bytes": 560, "raw_sha256": "0A901886CEFADFCBA596D999A8716BDEA889AA729B71C960821CDAFD2DFDAC36"},
    {"case_id": "gate88-torah-quran-source-authentication", "input_path": "tests/smokes/v0.4.3.0-release-regression/prompts/07-torah-quran-source-authentication.md", "raw_bytes": 1396, "raw_sha256": "ECE0E206447AE9EF9F2BC9987DA647BC220782E5B9C225EBC77DAAF97B465F57"}
  ],
  "forbidden_case_fields": ["expected_burdens", "expected_submoves", "expected_route", "expected_citations", "expected_answer", "expected_output_bytes"]
}
```

`tools/run_no_model_preflight.py`, the authorized matrix launcher, verdict builder, and playbook all load this file through one shared registry library. No consumer maintains a second in-code case tuple.

Registry rules:

- case IDs and paths are unique;
- paths are repository-relative, resolve under the repo, and contain nonempty regular files;
- raw SHA is recomputed over bytes and must match;
- files use UTF-8 and LF;
- registry has no route or answer fields;
- the required v0.4.6.0-wip set is exactly these five IDs;
- adding a future case changes the release-matrix contract deliberately, not a burden-count rule;
- no retained manifest row is required for launch registration.

## Matrix Completion Artifact

Use the same `schema/smoke-matrix.schema.json` with discriminated verdict kinds. `kind: structural-pre-review-verdict` records deterministic post-run replay before cold/human review; `kind: cycle-verdict` is the final completion decision after required cold GPT-5.6 reviews, human topology/substantive reviews/adjudications, and A13 package-faithful lane-parity evidence exist. Both are validated by `tools/check_smoke_matrix_manifest.py` and built by `tools/build_smoke_matrix_verdict.py`; neither may silently upgrade itself. The final record contains:

```json
{
  "schema": "daee-smoke-matrix-v1",
  "kind": "cycle-verdict",
  "matrix_id": "<immutable run id>",
  "cycle_ordinal": "<positive integer within campaign>",
  "predecessor_cycle_verdict_sha256": "<64 hex or null for first cycle>",
  "runtime_commit": "<40 hex>",
  "runtime_sha256": "<skill/SKILL.md raw hash>",
  "campaign_authorization_sha256": "<64 hex>",
  "cycle_authorization_sha256": "<64 hex>",
  "protocol_id": "<immutable producer/reviewer protocol id>",
  "evidence_lane": "package-faithful",
  "package_profile": "execution-mini",
  "package_sha256": "<64 hex>",
  "package_tree_sha256": "<64 hex>",
  "candidate_package_record": {
    "path": "<cycle-relative or custody-root path>",
    "sha256": "<64 hex>",
    "build_authorization_sha256": "<64 hex>"
  },
  "pushed_ci_readback_sha256": "<64 hex>",
  "no_model_candidate_maturity_sha256": "<64 hex>",
  "model_smoke_escape_registry_sha256": "<64 hex>",
  "dispatch_event_manifest_sha256": "<64 hex>",
  "parallel_protocol": "barrier-five-submit-before-await-v1",
  "invocation_usage_receipt_sha256": "<64 hex>",
  "campaign_usage_resulting_head_sha256": "<64 hex>",
  "candidate_consumption_receipt_sha256": "<64 hex>",
  "cycle_observation_finalizer_sha256": "<64 hex>",
  "observation_finalizer_status": "FINALIZED",
  "producer_entrypoint": "tools/run_five_smoke_matrix.py",
  "model_runner": "codex",
  "runner_adapter_version": "<exact resolved version>",
  "model": "<exact identifier>",
  "reasoning_effort": "high",
  "host": "<exact host/application and version>",
  "model_parameters_sha256": "<64 hex>",
  "producer_prompt_contract_sha256": "<64 hex>",
  "cold_review_prompt_sha256": "<64 hex>",
  "release_output_mode": "compiled-output",
  "target_output_kb": 0,
  "section_expansion_rounds": 0,
  "transport_retry_rounds": 0,
  "cases": [
    {
      "case_id": "gate88-secularism",
      "input_sha256": "<registry hash>",
      "run_dir": "<repo-relative path>",
      "handoff_record_sha256": "<hash>",
      "output_sha256": "<hash>",
      "stage_status": "PASS | FAIL | NOT_RUN",
      "first_failed_stage": null,
      "first_failed_checker": null,
      "semantic_repair_events": [],
      "promotion_verdict": {
        "path": "<case-relative promotion-verdict.json>",
        "sha256": "<64 hex>",
        "validation_registry_sha256": "<64 hex>",
        "structural_status": "PASS_STRUCTURAL | FAIL_STRUCTURAL | QUARANTINED_INCOMPLETE_EVIDENCE | INFRASTRUCTURE_ERROR"
      },
      "cold_comprehensiveness_review": {
        "review_id": "<id or null>",
        "path": "<cycle-relative path or null>",
        "sha256": "<64 hex or null>",
        "comprehension_status": "PASS | REVIEW_INVALID | NOT_REVIEWED",
        "coverage_verdict": "PASS | FAIL | PARTIAL | NOT_GRADED"
      },
      "human_topology_review": {
        "review_id": "<id or null>",
        "path": "<cycle-relative path or null>",
        "sha256": "<64 hex or null>",
        "verdict": "PASS | FAIL | PARTIAL | NOT_REVIEWED"
      },
      "package_faithful_custody": "PASS | FAIL | NOT_RUN"
    }
  ],
  "paired_lane_fixture_verdict": {
    "path": "<cycle-relative or custody path>",
    "sha256": "<64 hex>",
    "status": "PASS | FAIL | NOT_RUN"
  },
  "structural_matrix_status": "PASS | FAIL | PARTIAL",
  "completion_status": "PASS | FAIL | PARTIAL",
  "regression_status": "unproven",
  "non_claims": [
    "structural PASS is not semantic truth",
    "five exact cases do not prove arbitrary paraphrases",
    "matrix PASS is not release or provenance proof"
  ]
}
```

`structural_matrix_status=PASS` only when all five exact case IDs appear once, all input hashes match, candidate-package authorization/record/archive/tree bindings agree, the pushed exact-SHA CI receipt and `NO_MODEL_CANDIDATE_MATURE` verdict verify, every record has exactly eight ordered passing stages, each A11 promotion verdict is hash-bound to the case output and canonical validation-registry hash with `structural_status=PASS_STRUCTURAL`, all replay checks pass, no semantic repair occurred, the invocation/consumption receipts reconcile, and the always-run observation finalizer reports `FINALIZED`. The observation finalizer records what was launched and retained; it cannot pre-judge structural replay, cold review, human review, or final completion.

`completion_status=PASS` additionally requires cold GPT-5.6 comprehension/comprehensiveness review plus human topology/body review and adjudication for each case, one package-faithful five-case cycle, Plan 13's deterministic paired lane-parity requirement, zero open `YES`/`UNKNOWN` escape rows, and an unbroken campaign cycle lineage. Otherwise it remains `PARTIAL` even when structural status is green. A paid harness-assisted five-case counterpart is not required.

No field may report a percentage or majority pass. One failure blocks completion.

### Authorization and candidate-custody discriminators

The same smoke-matrix schema owns four pre-run control objects so authorization cannot be inferred from a green checker or an environment-variable value.

Repair campaign authorization example:

```json
{
  "schema": "daee-smoke-matrix-v1",
  "kind": "repair-campaign-authorization",
  "authorization_id": "owner-issued-immutable-campaign-id",
  "target_branch": "codex/v0.4.6.0-runtime-footprint",
  "registry_sha256": "64-lowercase-hex",
  "package_profile": "execution-mini",
  "producer_model_family": "gpt-5.5",
  "producer_reasoning_effort": "high",
  "producer_entrypoint": "tools/run_five_smoke_matrix.py",
  "producer_runner_adapter": "codex",
  "cold_reviewer_model_family": "gpt-5.6-sol",
  "cold_reviewer_reasoning_effort": "xhigh",
  "protocol_id": "owner-issued-immutable-protocol-id",
  "campaign_usage_head_path": "owner-custody/campaign-usage/head.json",
  "campaign_usage_control_root": "owner-custody/campaign-usage/claims",
  "campaign_usage_writer_protocol": "exclusive-cas-v1",
  "allowed_actions": [
    "build-candidate-package",
    "run-five-smoke-cycle",
    "run-cold-review"
  ],
  "denied_actions": ["commit", "push", "force-push", "tag", "upload", "publish", "release", "mutate-provenance"],
  "convergence_policy": "no-fixed-cycle-or-cumulative-call-ceiling",
  "child_reservation_policy": "exact-declared-calls-v1",
  "usage_cost_accounting": "append-only-factual",
  "provider_anomaly_policy": "stop-and-classify-infrastructure-andon",
  "revocation_state": "ACTIVE | REVOKED | COMPLETE",
  "valid_not_before": "RFC3339 timestamp",
  "valid_not_after": "RFC3339 timestamp",
  "decision_owner": "owner identity"
}
```

This object provides standing model/build campaign scope only. The convergence
objective has no fixed cycle or cumulative call ceiling and ends only at owner-
accepted WIP completion, explicit revocation, or a genuine blocked handoff. Each
candidate build, five-call producer cycle, and five-call review cohort still
receives its own immutable child authorization bound to current
commit/package/preflight hashes and an exact reservation. Commit and push use
Plan A16's separate one-use VCS action authorizations. Producer and reviewer
reservations share one canonical append-only campaign-usage head; neither lane
may maintain a private cumulative total. An unresolved head conflict, unknown
usage, provider anomaly, open ANDON, or protocol drift blocks before the next
call. Any branch, registry, model family/reasoning, package profile, action,
time-window, entrypoint, or runner-adapter drift stops the campaign. This
planning amendment does not instantiate the authorization or perform its
actions.

The active owner-issued campaign delegates child-manifest minting to the named
coordinator. Once the separately approved push is exact-SHA CI green, the
coordinator may mint the candidate-build child, build and mature the execution
candidate, mint the producer child, and later mint the review child after the
human initial-assessment claim, without another owner/design pause. Every child
still fails closed on parent revocation, hash drift, unmet predicates, usage-head
conflict, or an open ANDON. This delegation covers test evidence only; it does
not authorize a release package or any VCS/public action.

Candidate build authorization example:

```json
{
  "schema": "daee-smoke-matrix-v1",
  "kind": "candidate-package-build-authorization",
  "authorization_id": "coordinator-minted-immutable-id",
  "candidate_id": "coordinator-minted-unused-candidate-id",
  "campaign_authorization_path": "owner-custody/campaign-authorization.json",
  "campaign_authorization_sha256": "64-lowercase-hex",
  "source_commit": "40-lowercase-hex",
  "pushed_head_sha": "same-40-lowercase-hex",
  "ci_readback_path": "owner-custody/ci-readback.json",
  "ci_readback_sha256": "64-lowercase-hex",
  "no_model_source_preflight_path": "owner-custody/no-model-source-preflight.json",
  "no_model_source_preflight_sha256": "64-lowercase-hex",
  "clean_tree_sha256": "64-lowercase-hex",
  "registry_sha256": "64-lowercase-hex",
  "package_profile": "execution-mini",
  "custody_root": ".daee/candidate-packages",
  "claim_receipt_path": "owner-custody/candidate-claims/unused-id.json",
  "failed_record_fallback_path": "owner-custody/candidate-failures/unused-id.json",
  "allowed_actions": ["build-candidate-package"],
  "denied_actions": ["install", "commit", "push", "tag", "upload", "publish", "release"],
  "valid_not_before": "RFC3339 timestamp",
  "valid_not_after": "RFC3339 timestamp",
  "issued_by": "campaign coordinator identity",
  "delegation_source_sha256": "campaign authorization sha256",
  "decision_owner": "owner identity"
}
```

Ready candidate record example:

```json
{
  "schema": "daee-smoke-matrix-v1",
  "kind": "candidate-package-record",
  "candidate_id": "fresh immutable id",
  "status": "READY_UNUSED",
  "authorization_sha256": "64-lowercase-hex",
  "claim_receipt_sha256": "64-lowercase-hex",
  "source_commit": "40-lowercase-hex",
  "ci_readback_sha256": "64-lowercase-hex",
  "no_model_source_preflight_sha256": "64-lowercase-hex",
  "package_profile": "execution-mini",
  "archive_path": ".daee/candidate-packages/id/package.skill.zip",
  "archive_sha256": "64-lowercase-hex",
  "extracted_tree_path": ".daee/candidate-packages/id/extracted",
  "extracted_tree_sha256": "64-lowercase-hex",
  "build_manifest_sha256": "64-lowercase-hex",
  "created_at": "RFC3339 timestamp"
}
```

A proved provider/capacity failure before the atomic cycle claim leaves the
candidate `READY_UNUSED`. Once the cycle claim is consumed, the matrix moves the
candidate to exactly one neutral terminal state: `CONSUMED_OBSERVED` when one or
more producer calls are proved dispatched, `CONSUMED_NO_DISPATCH` when zero
dispatch is proved, or `CONSUMED_DISPATCH_UNKNOWN` when dispatch cannot be
resolved. The unknown state carries unresolved usage and blocks more paid calls
until reconciliation. Candidate state never says PASS or FAIL; structural and
reviewed outcomes belong to later immutable verdict artifacts. The consumption
receipt binds the observation-finalizer and usage-receipt hashes, dispatch
status/count, cycle ID, and terminal reason. `QUARANTINED` uses the same
candidate ID/authorization/source identity for build/root failure, omits
unavailable success hashes, records the exact failed command/category and any
partial-artifact hashes, and sets `promotion_eligible: false`. Candidate-build
authorization is atomically consumed before filesystem mutation. The checker
forbids authorization replay and any transition from a post-claim
`CONSUMED_*` state or `QUARANTINED` to `READY_UNUSED`.

Atomic consumption writes the authorization-bound claim receipt outside the new
candidate directory before attempting to create that directory. If root creation
itself fails, the quarantine record is written to the authorization-bound
fallback path and references the claim receipt; a failed build may never vanish
because its intended output directory was unavailable.

Matrix authorization example:

```json
{
  "schema": "daee-smoke-matrix-v1",
  "kind": "matrix-authorization",
  "authorization_id": "coordinator-minted-matrix-id",
  "cycle_id": "coordinator-minted-unused-cycle-id",
  "cycle_ordinal": "positive-integer-within-campaign",
  "matrix_root": ".daee/v0.4.6.0-wip-five-smoke/unused-cycle-id",
  "cycle_claim_receipt_path": "owner-custody/cycle-claims/unused-cycle-id.json",
  "failed_observation_finalizer_fallback_path": "owner-custody/cycle-failures/unused-cycle-id.json",
  "external_evidence_staging_root": "C:\\Users\\theis\\Documents\\Codex\\2026-07-08\\dae\\evidence\\v0.4.6.0-wip-five-smoke\\.staging\\unused-cycle-id\\unused-export-attempt-id",
  "external_evidence_final_root": "C:\\Users\\theis\\Documents\\Codex\\2026-07-08\\dae\\evidence\\v0.4.6.0-wip-five-smoke\\cycles\\unused-cycle-id",
  "external_publish_pointer_path": "C:\\Users\\theis\\Documents\\Codex\\2026-07-08\\dae\\evidence\\v0.4.6.0-wip-five-smoke\\pointers\\unused-cycle-id.json",
  "evidence_retention_manifest_working_path": "owner-custody/retention-manifests/unused-cycle-id.json",
  "campaign_authorization_path": "owner-custody/campaign-authorization.json",
  "campaign_authorization_sha256": "64-lowercase-hex",
  "source_commit": "40-lowercase-hex",
  "clean_tree_sha256": "64-lowercase-hex",
  "registry_sha256": "64-lowercase-hex",
  "preflight_report_sha256": "64-lowercase-hex",
  "preflight_report_path": "owner-custody/exact-candidate-preflight.json",
  "no_model_candidate_maturity_path": ".daee/maturity/id/no-model-candidate-maturity.json",
  "no_model_candidate_maturity_sha256": "64-lowercase-hex",
  "model_smoke_escape_registry_sha256": "64-lowercase-hex",
  "candidate_package_record_path": ".daee/candidate-packages/id/candidate-package-record.json",
  "candidate_package_record_sha256": "64-lowercase-hex",
  "package_sha256": "64-lowercase-hex",
  "package_tree_sha256": "64-lowercase-hex",
  "evidence_lane": "package-faithful",
  "producer_entrypoint": "tools/run_five_smoke_matrix.py",
  "model_runner": "codex",
  "runner_adapter_version": "exact resolved version at execution",
  "host_application_version": "exact resolved version at execution",
  "model": "gpt-5.5 exact resolved identifier",
  "reasoning_effort": "high",
  "model_parameters_sha256": "64-lowercase-hex",
  "reserved_invocations": 5,
  "usage_cost_recording": "required-factual-or-explicitly-unknown",
  "one_shot_policy": "complete-observation",
  "parallelism": 5,
  "parallel_protocol": "barrier-five-submit-before-await-v1",
  "dispatch_event_manifest_path": ".daee/v0.4.6.0-wip-five-smoke/unused-cycle-id/dispatch-events.json",
  "campaign_usage_head_path": "owner-custody/campaign-usage/head.json",
  "expected_campaign_usage_head_sha256": "64-lowercase-hex",
  "expected_campaign_usage_sequence": "nonnegative-integer",
  "candidate_required_state": "READY_UNUSED",
  "predecessor_cycle_verdict_sha256": "64-lowercase-hex-or-null",
  "retention_policy": "immutable-full-cycle-indefinite-owner-pruning-only",
  "valid_not_before": "RFC3339 timestamp",
  "valid_not_after": "RFC3339 timestamp",
  "issued_by": "campaign coordinator identity",
  "delegation_source_sha256": "campaign authorization sha256",
  "decision_owner": "owner identity"
}
```

Cold-review child authorization example:

```json
{
  "schema": "daee-smoke-matrix-v1",
  "kind": "cold-review-authorization",
  "authorization_id": "coordinator-minted-cold-review-id",
  "campaign_authorization_path": "owner-custody/campaign-authorization.json",
  "campaign_authorization_sha256": "64-lowercase-hex",
  "cycle_id": "exact completed structural cycle",
  "cold_review_packet_sha256s": ["five exact packet hashes"],
  "reviewer_model_family": "gpt-5.6-sol",
  "reviewer_reasoning_effort": "xhigh",
  "exact_model_identifier": "resolved before launch",
  "host": "exact host/application version",
  "review_prompt_sha256": "64-lowercase-hex",
  "campaign_usage_head_path": "owner-custody/campaign-usage/head.json",
  "expected_campaign_usage_head_sha256": "64-lowercase-hex",
  "expected_campaign_usage_sequence": "nonnegative-integer",
  "reserved_invocations": 5,
  "usage_cost_recording": "required-factual-or-explicitly-unknown",
  "retention_policy": "immutable-full-review",
  "valid_not_before": "RFC3339 timestamp",
  "valid_not_after": "RFC3339 timestamp",
  "issued_by": "campaign coordinator identity",
  "delegation_source_sha256": "campaign authorization sha256",
  "decision_owner": "owner identity"
}
```

Every coordinator-minted child authorization and evidence record binds the
campaign path/hash and delegated issuer. The authorization checker recomputes
every referenced hash, factual cumulative
usage, source/clean-state, pushed-head/CI receipt, and packet identity
immediately before use. `reserved_invocations: 5` belongs to one exact
five-input producer or reviewer cohort; it is not a campaign give-up ceiling or
a topology, burden, submove, or retry quota inside any case.

### Campaign usage reservation, canonical head, and receipt

Parallel launch must not fork the canonical usage head, and producer and cold-
review coordinators must not each believe they own the same predecessor state.
Immediately before producer dispatch, the coordinator reserves exactly five
producer invocations against the immutable campaign and cycle authorization. It
does the same for a five-review cold batch under its review authorization. Both
lanes use the one campaign-owned head named by
`campaign_usage_head_path`; a per-run cumulative counter is not authoritative.

The head is a content-addressed record with `sequence`,
`latest_transaction_sha256`, cumulative call/spend values, and the campaign
authorization hash. A reservation transaction MUST:

1. read and hash the canonical head;
2. match the child authorization's expected head hash and sequence;
3. acquire the campaign's exclusive writer claim or perform an equivalent
   compare-and-swap;
4. write an immutable reservation claim/record bound to that predecessor;
5. atomically advance the head to the reservation transaction before any model
   dispatch; and
6. release the writer claim only after head readback proves the new hash.

If two coordinators name the same predecessor, exactly one can advance the
head. The loser emits `USAGE_HEAD_CONFLICT`, performs zero model calls, and must
obtain a fresh child authorization against the new head. Settlement is a second
append-only transaction and CAS advance. It never edits the reservation.

The smoke-matrix schema adds discriminated `campaign-usage-reservation` and
`campaign-usage-receipt` records. They bind:

```json
{
  "schema": "daee-smoke-matrix-v1",
  "kind": "campaign-usage-receipt",
  "campaign_authorization_sha256": "64-lowercase-hex",
  "authorization_sha256": "64-lowercase-hex",
  "cycle_or_review_batch_id": "immutable-id",
  "predecessor_usage_head_sha256": "64-lowercase-hex",
  "predecessor_usage_sequence": 0,
  "reservation_claim_sha256": "64-lowercase-hex",
  "reservation_transaction_sha256": "64-lowercase-hex",
  "settlement_transaction_sha256": "64-lowercase-hex",
  "resulting_usage_head_sha256": "64-lowercase-hex",
  "resulting_usage_sequence": 2,
  "lane": "producer | cold-review",
  "reserved_invocations": 5,
  "attempted": 0,
  "completed": 0,
  "cancelled_after_dispatch": 0,
  "failed_after_dispatch": 0,
  "not_dispatched": 5,
  "provider_usage_receipts": [],
  "measured_cost": {"unit": "authorization-unit", "value": "number-or-unknown"},
  "cumulative_producer_invocations": 0,
  "cumulative_cold_review_invocations": 0,
  "cumulative_total_invocations": 0,
  "cumulative_spend": {"unit": "authorization-unit", "value": "number-or-unknown"},
  "reservation_status": "SETTLED"
}
```

Counts satisfy `reserved = attempted + not_dispatched` and
`attempted = completed + cancelled_after_dispatch + failed_after_dispatch`.
Every call row binds case/review ID,
exact model/protocol, start/end, host invocation identifier where available,
terminal transport status, and provider usage/cost receipt or explicit
`unavailable`. Cost is never guessed from prose length.

Pre-dispatch enforcement cannot depend on a cost value learned only afterward.
The coordinator records provider pricing/usage metadata when available and
stops on unexpected price, quota, authorization, or capacity drift. This is an
infrastructure circuit breaker, not a fixed campaign cycle/call give-up rule.
Unknown cost remains `unknown`; it cannot be represented as a known spend value.

The reservation is settled by the always-run observation finalizer even on
nonzero exit. Unused reserved slots become `not_dispatched`; they do not become
retry credits for the same candidate. A successor cycle gets a new reservation
and a new causal basis. The canonical usage head continues to record cumulative
fact without imposing an arbitrary terminal cycle/call count.

If the coordinator dies after the reservation-head advance but before ordinary
settlement, the reservation is orphaned, not erased. A recovery process uses a
separate one-use recovery authorization, the same reservation/cycle identity,
provider receipts and dispatch events, and another head CAS to write the most
conservative truthful settlement. Unknown dispatch/usage remains `unknown` and
blocks further campaign calls until reconciled; it is never converted to unused
capacity. A claimed candidate becomes `CONSUMED_NO_DISPATCH` when zero dispatch
is proved, `CONSUMED_OBSERVED` when one-or-more dispatches are proved, or
`CONSUMED_DISPATCH_UNKNOWN` when evidence cannot distinguish them. Recovery
cannot return it to `READY_UNUSED`.

The campaign summary separately records deterministic maturity blocks,
`MODEL_SMOKE_ESCAPE` classes, recurrences, and permanent canaries. It reports
model invocations avoided only when a planned invocation was actually prevented
before dispatch by a hash-bound deterministic gate; otherwise the value is
`unknown`. The metric cannot be improved by dropping a smoke, weakening review,
or reducing topology/body obligations.

Candidate custody roots are repository-relative and must resolve beneath the designated ignored `.daee/candidate-packages/` parent after normalization. The checker rejects absolute paths, `..`, symlink/junction/reparse escapes, an existing candidate ID, or any attempt to overwrite a `READY_UNUSED`, `CONSUMED_OBSERVED`, `CONSUMED_NO_DISPATCH`, `CONSUMED_DISPATCH_UNKNOWN`, or `QUARANTINED` record. Matrix `package_root` must equal the `READY_UNUSED` record's extracted-tree path and hash; a merely existing directory is insufficient.

The external evidence destination is a different path class. It is explicitly
supplied by owner authorization and must resolve outside the mutable checkout,
or to an approved content-addressed object-store namespace. The schema/checker
validates provider/path kind, normalized staging and final destinations, unused
cycle child, retention policy, and readback method. Candidate-root relative-path
rules must not accidentally coerce durable evidence back under `.daee`.

Export is a recoverable publish transaction, not a direct copy into the final
cycle directory. The exporter writes to the authorization-bound unique
`.staging/<cycle-id>/<export-attempt-id>` location, copies the complete local or
fallback inventory, writes the retention manifest last, and reads every staged
hash back. It then atomically renames/publishes the staging directory to the
unused final cycle path where the filesystem supports that operation. For an
object store, it writes immutable objects first and advances an immutable
manifest pointer with compare-and-swap. Only the verified final directory or
pointer is completion evidence.

A partial staging tree is retained as failure evidence but is never offered as
final. Resume is idempotent only when every pre-existing staged object has the
same path, byte count, SHA-256, cycle-claim hash, and export-attempt lineage.
Hash mismatch emits `EVIDENCE_STAGING_CONFLICT`, forbids overwrite, and blocks
completion. The final path/pointer can be published once only.

### Cycle claim and root-failure recovery

Cycle authorization is consumed before the working root is created. The
coordinator first performs create-if-absent on the authorization-bound
`cycle_claim_receipt_path`, recording authorization/campaign/candidate hashes,
cycle ID/ordinal, expected usage head, matrix root, external staging/final
destinations, and claim time. Only that receipt licenses creation of the matrix
root. A pre-existing claim, cycle root, final destination, or incompatible
staging lineage blocks launch.

If matrix-root creation fails, the coordinator still writes an immutable
`kind: cycle-observation-finalizer` to
`failed_observation_finalizer_fallback_path`, binds the cycle-claim receipt and
failure diagnostic, settles the reservation as zero-dispatch when provable,
and writes candidate state `CONSUMED_NO_DISPATCH`; if dispatch cannot be proved,
it writes `CONSUMED_DISPATCH_UNKNOWN` and leaves usage unresolved. The fallback
plus claim and usage records become the export source; absence of a matrix root
cannot erase a claimed cycle. Unknown dispatch blocks future model calls pending
authorized recovery.

### Machine-verifiable five-worker concurrency

`parallelism: 5` is descriptive only. The required proof is the event protocol
`barrier-five-submit-before-await-v1`. The runner writes a monotonic,
hash-chained dispatch-event manifest containing exactly one worker identity per
registered case and this partial order:

1. all five workers emit `worker_ready` after private
   context/home/temp/cache/session/run-root and read-only package verification;
2. one coordinator emits `barrier_released` only after all five ready events;
3. each worker emits `request_submit_started` after that release;
4. each worker emits provider `request_accepted` or a Codex-adapter
   `call_entered_in_flight` acknowledgment that proves the call has crossed the
   nonblocking/concurrent boundary and has not returned;
5. the fifth acceptance/in-flight acknowledgment occurs before any
   `terminal_result_observed`, `first_result_awaited`, response parse, checker
   invocation, or product decision; and
6. result collection may begin only after the coordinator emits
   `all_five_in_flight` bound to the five acknowledgments.

This is a causal-order proof, not a millisecond overlap threshold. Provider
request receipts are retained when available. If the Codex adapter/host cannot
produce five acceptance or in-flight acknowledgments under that barrier, the
claimed cycle ends as a finalized `PARALLEL_CAPACITY_BLOCKED` zero-dispatch
record, not as `FIVE_SMOKE_OBSERVED`. Queued/sequential submission, awaiting the
first result before the fifth submission, or constructing workers lazily after
seeing an earlier result is invalid even when a command-line flag says
`--parallelism 5`.

## Exact Owner and Edit Map

### Add

- `tests/smokes/v0.4.3.0-release-regression/prompts/07-torah-quran-source-authentication.md`
- `schema/smoke-matrix.schema.json` with registry, standing repair-campaign
  authorization, candidate-package-build authorization/record, matrix and
  cold-review authorization, campaign-usage head/reservation/settlement/recovery,
  cycle-claim, barrier dispatch-event manifest, candidate-consumption receipt,
  cycle-observation-finalizer, structural-pre-review-verdict, and cycle-verdict
  definitions
- consume Plan A01's `schema/topology-review.schema.json` and `schema/cold-comprehensiveness-review.schema.json` by reference; do not define competing review schemas
- `tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json`
- `tools/smoke_matrix_registry.py`
- `tools/check_smoke_matrix_manifest.py`
- `tools/campaign_usage_ledger.py`
  - own the single campaign usage head, exclusive/CAS reservation, settlement,
    orphan recovery, and producer/cold-review serialization protocol;
- `tools/check_parallel_dispatch_manifest.py`
  - verify the barrier/event partial order without elapsed-time heuristics;
- `tools/build_smoke_matrix_verdict.py`
- `tools/build_candidate_package_record.py`
  - emit either immutable `status: READY_UNUSED` with archive/tree/build-manifest hashes or `status: QUARANTINED` with failure custody;
  - preserve `READY_UNUSED` only when a pre-claim failure is proved; after claim,
    transition one use to neutral `CONSUMED_OBSERVED`,
    `CONSUMED_NO_DISPATCH`, or `CONSUMED_DISPATCH_UNKNOWN`;
  - forbid changing a consumed/quarantined record to ready or reusing its candidate ID;
- `tools/run_five_smoke_matrix.py`
- `schema/cross-model-paired-cycle.schema.json`
- `tools/run_paired_cross_model_matrix.py`
- `tools/check_paired_cross_model_manifest.py`
- `tools/build_cold_review_packet.py`
- `tools/check_case_registry_taint.py`
  - prove case ID, path, hash, and distinctive prompt text cannot reach runtime route/owner/output selection;
  - include renamed-ID/path and blinded topic-neutral metamorphic fixtures after candidate freeze;
  - remain no-model and never contain expected answers.
- `tests/smoke-matrix/fixtures/valid/complete-five-case-structural.json`
- `tests/smoke-matrix/fixtures/invalid/missing-fifth-case.json`
- `tests/smoke-matrix/fixtures/invalid/duplicate-case.json`
- `tests/smoke-matrix/fixtures/invalid/input-hash-drift.json`
- `tests/smoke-matrix/fixtures/invalid/stage07-only.json`
- `tests/smoke-matrix/fixtures/invalid/stage08-missing.json`
- `tests/smoke-matrix/fixtures/invalid/semantic-repair-present.json`
- `tests/smoke-matrix/fixtures/invalid/structural-pass-called-semantic.json`
- `tests/smoke-matrix/fixtures/invalid/topology-review-partial-called-complete.json`
- `tests/smoke-matrix/fixtures/invalid/candidate-package-built-without-bound-authorization.json`
- `tests/smoke-matrix/fixtures/invalid/candidate-package-record-missing-tree-hash.json`
- `tests/smoke-matrix/fixtures/invalid/quarantined-candidate-reused.json`
- `tests/smoke-matrix/fixtures/invalid/matrix-authorization-package-hash-mismatch.json`
- `tests/smoke-matrix/fixtures/invalid/campaign-authorization-branch-drift.json`
- `tests/smoke-matrix/fixtures/invalid/campaign-authorization-model-settings-drift.json`
- `tests/smoke-matrix/fixtures/invalid/campaign-provider-price-or-quota-drift.json`
- `tests/smoke-matrix/fixtures/invalid/selective-prior-cycle-pass-carried-forward.json`
- `tests/smoke-matrix/fixtures/invalid/reviewer-andon-not-reentered.json`
- `tests/smoke-matrix/fixtures/valid/campaign-has-no-fixed-cycle-or-cumulative-call-ceiling.json`
- `tests/smoke-matrix/fixtures/invalid/campaign-usage-head-factual-count-rewritten.json`
- `tests/smoke-matrix/fixtures/invalid/candidate-build-authorization-replayed.json`
- `tests/smoke-matrix/fixtures/invalid/candidate-root-create-failure-without-fallback-quarantine.json`
- `tests/smoke-matrix/fixtures/invalid/candidate-claim-receipt-reused.json`
- `tests/smoke-matrix/fixtures/invalid/consumed-observed-candidate-reused.json`
- `tests/smoke-matrix/fixtures/invalid/consumed-no-dispatch-candidate-reused.json`
- `tests/smoke-matrix/fixtures/invalid/consumed-dispatch-unknown-candidate-reused.json`
- `tests/smoke-matrix/fixtures/valid/preclaim-capacity-failure-preserves-ready-unused.json`
- `tests/smoke-matrix/fixtures/valid/claimed-dispatch-unknown-is-terminal.json`
- `tests/smoke-matrix/fixtures/invalid/failed-cycle-missing-observation-finalizer.json`
- `tests/smoke-matrix/fixtures/valid/cycle-root-create-failure-with-fallback-finalizer.json`
- `tests/smoke-matrix/fixtures/invalid/cycle-root-create-failure-without-fallback-finalizer.json`
- `tests/smoke-matrix/fixtures/valid/producer-green-review-fail-candidate-consumed-observed.json`
- `tests/smoke-matrix/fixtures/invalid/observation-finalizer-emits-reviewed-cycle-verdict.json`
- `tests/smoke-matrix/fixtures/invalid/candidate-consumption-state-claims-pass-before-review.json`
- `tests/smoke-matrix/fixtures/invalid/parallel-worker-shared-home-cache.json`
- `tests/smoke-matrix/fixtures/invalid/provider-auth-failure-dispatches-later-calls.json`
- `tests/smoke-matrix/fixtures/invalid/human-patch-owner-overturns-fail-without-second-review.json`
- `tests/smoke-matrix/fixtures/invalid/case-id-hash-taint-reaches-routing.json`
- `tests/smoke-matrix/fixtures/valid/parallel-five-call-usage-reservation-settled.json`
- `tests/smoke-matrix/fixtures/invalid/parallel-workers-fork-canonical-usage-head.json`
- `tests/smoke-matrix/fixtures/invalid/conflicting-predecessor-usage-reservations.json`
- `tests/smoke-matrix/fixtures/invalid/concurrent-producer-review-reservation-conflict.json`
- `tests/smoke-matrix/fixtures/valid/orphaned-reservation-recovery-without-reuse.json`
- `tests/smoke-matrix/fixtures/invalid/usage-head-nonmonotonic.json`
- `tests/smoke-matrix/fixtures/invalid/usage-receipt-arithmetic-mismatch.json`
- `tests/smoke-matrix/fixtures/invalid/failed-cycle-usage-reservation-unsettled.json`
- `tests/smoke-matrix/fixtures/invalid/reviewer-usage-counted-as-producer.json`
- `tests/smoke-matrix/fixtures/invalid/speculative-model-calls-avoided.json`
- `tests/smoke-matrix/fixtures/invalid/source-preflight-used-as-candidate-maturity.json`
- `tests/smoke-matrix/fixtures/valid/barrier-five-submit-before-await.json`
- `tests/smoke-matrix/fixtures/invalid/sequential-masquerading-as-parallel.json`
- `tests/smoke-matrix/fixtures/invalid/await-first-result-before-fifth-submit.json`
- `tests/smoke-matrix/fixtures/invalid/shared-barrier-missing-worker.json`
- `tests/smoke-matrix/fixtures/valid/partial-export-resume-hash-equal.json`
- `tests/smoke-matrix/fixtures/invalid/partial-export-resume-hash-mismatch.json`
- `tests/smoke-matrix/fixtures/invalid/staging-manifest-offered-as-final.json`
- `tests/smoke-matrix/fixtures/valid/product-refusal-substitutes-prose-for-required-execution.json`
- `tests/smoke-matrix/fixtures/valid/prestage-policy-incompatibility-with-typed-host-evidence.json`
- `tests/smoke-matrix/fixtures/valid/refusal-origin-unproven-fails-without-causal-attribution.json`
- `tests/smoke-matrix/fixtures/invalid/policy-label-manufactures-zero-dispatch.json`
- `tests/smoke-matrix/fixtures/valid/paired-gpt-opus-sibling-candidates-same-package.json`
- `tests/smoke-matrix/fixtures/invalid/paired-sibling-package-hash-mismatch.json`
- `tests/smoke-matrix/fixtures/invalid/paired-result-observed-before-tenth-acceptance.json`
- `tests/smoke-matrix/fixtures/invalid/paired-one-model-pass-carried-forward.json`
- `tests/smoke-matrix/fixtures/invalid/opus-countermeasure-regresses-gpt.json`

Every invalid fixture above has a same-stem `.expectation.json` under Plan A11's canonical schema; no smoke-matrix-private expectation dialect is permitted.

### Modify

- `tools/run_no_model_preflight.py`
  - replace four-ID retained-path coupling with the shared five-case JSON registry loader;
  - rename Gate 14 and user-facing banner to smoke-matrix/five-case language;
  - self-test exact required IDs, unique paths, and hashes;
  - keep model invocation unreachable.
- `tools/run_staged_current_skill_smoke.py`
  - preserve exact model runner and all launch controls in the hash record;
  - emit raw/adapter/semantic-repair evidence required by Plan 13;
  - after Plan A13, accept `--evidence-lane package-faithful` and `--package-root <hash-bound extracted execution-mini root>`; reject a package-faithful run that obtains runtime law from harness-only prose;
  - keep each run directory immutable and fail if reused.
- `tools/run_five_smoke_matrix.py`
  - validate a `kind: matrix-authorization` object under `schema/smoke-matrix.schema.json`;
  - require its candidate-package-record path/hash and reject package, source, registry, or profile drift;
  - bind authorization, registry, preflight, source commit, runtime/package, and launch controls before the first paid call;
  - call `campaign_usage_ledger.py` to CAS-advance the one canonical campaign
    head for reservation and settlement; a head conflict performs zero calls;
  - launch all five registry rows through the fixed `codex` adapter concurrently
    under isolated workers and the canonical `complete-observation` policy;
  - emit `barrier-five-submit-before-await-v1` events and refuse result
    consumption until all five workers have proved request acceptance/in-flight
    state;
  - create fresh per-case context and run directories; reject shared mutable state, duplicate run roots, or observation-dependent launch mutation;
  - allocate private temp/home/cache/session roots per worker and read-only candidate views; run a no-output provider/auth health probe before concurrent dispatch;
  - always write a neutral `cycle-observation-finalizer`, settled invocation
    usage receipt, candidate-consumption receipt, and neutral candidate
    `CONSUMED_*` state before returning;
  - classify typed pre-Stage01 policy blocks, model-authored product refusal,
    and refusal of unproven origin without allowing the class to determine
    candidate consumption;
  - preserve every result and return nonzero after all five observations when any row is not PASS.
- `tools/build_smoke_matrix_verdict.py`
  - require explicit `--mode structural-pre-review|completion`;
  - emit `kind: structural-pre-review-verdict` only from deterministic run/replay artifacts;
  - emit `kind: cycle-verdict` only when every A01 review and A13 parity artifact is present and hash-valid;
  - never turn a missing review/parity artifact into a generic successful structural verdict.
- `docs/four-smoke-release-playbook.md`
  - retain the path for stable references;
  - distinguish historical four-smoke evidence from current five-smoke completion;
  - replace current `<4 ...>` examples with exact five-case registry/replay commands;
  - keep all owner gates and non-claims.
- `docs/staged-smoke-maintenance.md`
  - document five-case completion record and no-retry attempt identity.
- `docs/non-claims.md`
  - add five-case scope and structural/topology/package boundaries.
- `tools/run_local_ci.py` and `tools/ci_registry.json`
  - add registry/completion checker self-tests, never live model calls.

### Do not add or modify before a pass

- no `tests/retained-proof-corpus/.../cases/gate88-torah-quran-source-authentication/` directory;
- no retained manifest row for the fifth case;
- no golden output;
- no expected route, burden, submove, citation, or answer file;
- no case-specific runtime code or owner allowlist.

### Generated/package boundary

The input registry and completion checker do not require a canonical runtime edit by themselves. Runtime fixes required by the other ANDON plans are made in atomics and regenerated. Never hand-edit `skill/**`. The final package-faithful matrix requires an immutable extracted execution-mini candidate. Building that test candidate is a delegated one-use child operation under the active owner-issued `repair-campaign-authorization`, not a new owner pause and not a release-package build. `candidate-package-build-authorization` is coordinator-minted, single-use, and binds candidate ID, pushed source commit, clean-state digest, exact-SHA CI-readback receipt, `NO_MODEL_SOURCE_PREFLIGHT_GREEN` path/hash, profile, custody root, and allowed build window before the build; `candidate-package-record` binds the resulting archive/extracted-tree/build-manifest hashes and single-use lifecycle; later `matrix-authorization` binds that record, the package-bound `NO_MODEL_CANDIDATE_MATURE` verdict, exact five-call reservation, model/settings/protocol/retention controls, and launch window. A failed candidate build is hash-recorded as `QUARANTINED`; a proved pre-claim stop may preserve `READY_UNUSED`; a claimed matrix moves the candidate neutrally to `CONSUMED_OBSERVED`, `CONSUMED_NO_DISPATCH`, or `CONSUMED_DISPATCH_UNKNOWN`, while structural/review PASS/FAIL remains in later verdicts. No terminal directory is repaired or reused. Product repair requires a fresh pushed-green source boundary and candidate; infrastructure-only repair may use the same SHA with a fresh candidate after the external cause and no-model health are proven. None of these objects authorizes install, commit, push, tag, publish, or release.

## TDD Execution Phases

### Phase 0: Pin the four current inputs and baseline

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
git status --short --branch --untracked-files=all
git rev-parse HEAD
$inputs = @(
  'tests\smokes\v0.4.3.0-release-regression\prompts\01-trinitarian-j173.md',
  'tests\smokes\v0.4.3.0-release-regression\prompts\02-tst-lillard.md',
  'tests\smokes\v0.4.3.0-release-regression\prompts\03-khaybar.md',
  'tests\smokes\v0.4.3.0-release-regression\prompts\06-secularism.md'
)
$inputs | ForEach-Object { Get-FileHash -Algorithm SHA256 -LiteralPath $_ }
python tools\run_staged_current_skill_smoke.py --help
python tools\run_no_model_preflight.py --self-test
```

Expected at the planning baseline:

- clean head `6987c9e...`;
- hashes equal the four table values;
- runner help lists current flags;
- old preflight self-test exits `0` but still describes four cases. This last result confirms current wiring, not the new requirement.

STOP on any hash or head drift.

### Phase 1: Test-drive the five-case registry

1. Add failing self-tests for missing fifth case, duplicate ID/path, wrong hash, empty file, path escape, and route/answer metadata.
2. Add the exact fifth input fixture.
3. Replace the tuple and Gate 14 path logic.
4. Recompute all five raw hashes in the checker.
5. Ensure preflight mode returns before `run_model_smoke()`.

Commands:

```powershell
python tools\run_no_model_preflight.py --self-test
$inputCheckRun = '.daee\no-model-preflight\torah-quran-input-' + (Get-Date -AsUTC -Format 'yyyyMMddTHHmmssfffffffZ')
python tools\run_staged_current_skill_smoke.py --preflight-input-only --case-name gate88-torah-quran-source-authentication --raw-input-path tests\smokes\v0.4.3.0-release-regression\prompts\07-torah-quran-source-authentication.md --run-dir $inputCheckRun
```

Expected: both exit `0`; the second command prints input bytes/hash and the no-model/non-promotion non-claims. The timestamp includes fractional seconds so the command creates a fresh evidence path; never delete an evidence directory merely to reuse its name.

Fifth fixture hash assertion:

```powershell
$path = 'tests\smokes\v0.4.3.0-release-regression\prompts\07-torah-quran-source-authentication.md'
$item = Get-Item -LiteralPath $path
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
if ($item.Length -ne 1396) { throw "unexpected fifth input bytes: $($item.Length)" }
if ($hash -ne 'ECE0E206447AE9EF9F2BC9987DA647BC220782E5B9C225EBC77DAAF97B465F57') { throw "unexpected fifth input hash: $hash" }
```

Expected: no output on success.

### Phase 2: Completion checker fixtures

1. Add the schema and invalid fixtures first.
2. Implement exact five-ID set equality, unique run dirs, input/runtime/control parity, exact Stage01-08 order, stage status, hash bindings, no semantic repair, and review status logic.
3. Keep structural and completion statuses separate.
4. Make `regression_status` accept `unproven` only in this release completion artifact.

Commands:

```powershell
python tools\check_smoke_matrix_manifest.py --self-test
python tools\check_smoke_matrix_manifest.py --manifest tests\smoke-matrix\v0.4.6.0-wip-five-smoke.json --inputs-only
```

Expected: exit `0` because valid fixtures pass and every registered invalid fixture fails for its pinned reason.

Canonical right-reason canary:

```powershell
python tools\assert_expected_rejection.py --expectation tests\smoke-matrix\fixtures\invalid\missing-fifth-case.expectation.json --artifact-root auto
```

Expected: exit `0`; the manifest is rejected specifically for five-case set inequality and cannot emit authorization, cycle, promotion, package, or completion artifacts.

### Phase 3: Integrate source-only deterministic preflight

```powershell
python tools\run_no_model_preflight.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'no-model preflight self-test failed' }
$preflightRoot = Join-Path '.daee\no-model-preflight' ('five-smoke-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $preflightRoot) { throw "preflight root already exists: $preflightRoot" }
New-Item -ItemType Directory -Path $preflightRoot | Out-Null
$rawPreflight = Join-Path $preflightRoot 'preflight.json'
$sourcePreflight = Join-Path $preflightRoot 'no-model-source-preflight.json'
python tools\run_no_model_preflight.py --json $rawPreflight
if ($LASTEXITCODE -ne 0) { throw 'no-model preflight failed' }
python tools\build_no_model_candidate_maturity_verdict.py --mode source-preflight --preflight-report $rawPreflight --out $sourcePreflight
if ($LASTEXITCODE -ne 0) { throw 'source-preflight verdict build failed' }
python tools\check_no_model_candidate_maturity.py --verdict $sourcePreflight --require-status NO_MODEL_SOURCE_PREFLIGHT_GREEN
if ($LASTEXITCODE -ne 0) { throw 'source-only deterministic maturity failed' }
```

Expected: all source-owned deterministic gates pass and the runner's final line is `PREFLIGHT_GREEN_AWAITING_OWNER_AUTHORIZATION`. The source-preflight artifact records the five input checks, source head/dirty state, pushed-SHA CI receipt, registry hash, checker profile, right-reason mutation results, prior model-smoke escape closure, topology/metamorphic capacity, case-registry taint isolation, and generated freshness identities. Its only maturity status is `NO_MODEL_SOURCE_PREFLIGHT_GREEN`. It has no candidate/package identity and cannot authorize a model.

STOP if Gate 14 still says four-smoke, checks a retained fifth path, accepts fewer than five IDs, has an open/unknown deterministically detectable `MODEL_SMOKE_ESCAPE`, lacks right-reason/mutation evidence for a prior escape canary, or allows case identity/hash/text to influence routing.

### Phase 3a: Build one authorized immutable candidate

Execute A16 Section 13.1 only after a one-use candidate-build authorization
binds `$sourcePreflight`, exact pushed SHA/CI, candidate ID, claim/fallback paths,
and execution-mini profile. The only successful state is `READY_UNUSED`; build or
root-claim failure is `QUARANTINED`. This phase does not invoke a model.

### Phase 3b: Join package-bound candidate maturity

Execute A16 Section 13.1a against the actual candidate record and extracted
package. Package-only delivery, route/load, package/harness parity, escape,
topology/metamorphic, fake-Codex-adapter five-way barrier, campaign usage-head
CAS/conflict/orphan-recovery, cycle-claim/fallback, transactional-export, and
source-preflight hashes must join into
`NO_MODEL_CANDIDATE_MATURE`. Matrix authorization binds that artifact. Neither
Phase 3 nor 3a can substitute for it.

### Phase 4: Owner-gated parallel one-shot matrix

This phase is not run during implementation planning. The owner must supply one valid standing campaign authorization for the model protocol, evidence destination, delegation, and revocation boundary. After exact-SHA CI and candidate predicates are green, the named coordinator mints the one-use child cycle authorization for model, usage reservation, package/runtime identity, evidence paths, and launch window without another design pause. The canonical producer lane is the package-faithful `tools/run_five_smoke_matrix.py` entrypoint using its `codex` runner adapter with `gpt-5.5` and reasoning effort `high`. The child authorization and launch record capture the exact resolved model identifier, Codex adapter version, and host/application version. A normal Codex Desktop conversation or direct staged-runner invocation is observational evidence only and cannot satisfy this completion lane.

The following is the target canonical launcher protocol after Plans A01, A11-A13, and this plan are implemented. It deliberately uses no target output floor, no expansion retry, and no transport retry. A reusable `YES` environment variable is not authorization. The standing campaign plus one-use child manifest binds approved source commit, registry hash, generated runtime/package hash, model runner, model identifier, evidence lane, exact five-call reservation, factual usage/cost policy, retention policy, and launch window.

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
Set-Location $repo
$registry = 'tests\smoke-matrix\v0.4.6.0-wip-five-smoke.json'
$authorization = [Environment]::GetEnvironmentVariable('DAEE_SMOKE_AUTHORIZATION_MANIFEST')
if ([string]::IsNullOrWhiteSpace($authorization)) { throw 'DAEE_SMOKE_AUTHORIZATION_MANIFEST is required' }
python tools\check_smoke_matrix_manifest.py --manifest $authorization --kind matrix-authorization --require-evidence-lane package-faithful
if ($LASTEXITCODE -ne 0) { throw 'matrix authorization is invalid, stale, overbroad, or bound to another candidate/source state' }
$auth = Get-Content -Raw -LiteralPath $authorization | ConvertFrom-Json
$candidateRecord = Get-Content -Raw -LiteralPath $auth.candidate_package_record_path | ConvertFrom-Json
$matrixId = $auth.cycle_id
$matrixRoot = $auth.matrix_root
$preflightReport = $auth.preflight_report_path
$candidateMaturity = $auth.no_model_candidate_maturity_path
$cycleClaim = $auth.cycle_claim_receipt_path
$failedFinalizerFallback = $auth.failed_observation_finalizer_fallback_path
$stagingRoot = $auth.external_evidence_staging_root
$finalRoot = $auth.external_evidence_final_root
$publishPointer = $auth.external_publish_pointer_path
$retentionManifest = $auth.evidence_retention_manifest_working_path
$packageRoot = $candidateRecord.extracted_tree_path
foreach ($required in @($matrixId,$matrixRoot,$preflightReport,$candidateMaturity,$cycleClaim,$failedFinalizerFallback,$stagingRoot,$finalRoot,$publishPointer,$retentionManifest,$packageRoot)) {
  if ([string]::IsNullOrWhiteSpace($required)) { throw 'authorization/candidate record has an empty launch field' }
}
if (Test-Path -LiteralPath $matrixRoot) { throw "matrix root already exists: $matrixRoot" }
if (Test-Path -LiteralPath $cycleClaim) { throw "cycle claim already exists: $cycleClaim" }
if (Test-Path -LiteralPath $finalRoot) { throw "external evidence final root already exists: $finalRoot" }
python tools\check_smoke_matrix_manifest.py --manifest $registry --inputs-only
if ($LASTEXITCODE -ne 0) { throw 'five-smoke input registry failed validation' }
python tools\check_no_model_candidate_maturity.py --verdict $candidateMaturity --require-status NO_MODEL_CANDIDATE_MATURE --candidate-record $auth.candidate_package_record_path
if ($LASTEXITCODE -ne 0) { throw 'bound no-model candidate maturity report is invalid or stale' }
$runnerExit = 0
python tools\run_five_smoke_matrix.py `
  --registry $registry `
  --authorization-manifest $authorization `
  --preflight-report $preflightReport `
  --matrix-root $matrixRoot `
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
  --cycle-root $matrixRoot `
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
  $exportExit = $LASTEXITCODE
}
if ($exportExit -ne 0) { throw 'cycle evidence staging/publish/readback failed; freeze all evidence and block completion' }
if ($runnerExit -ne 0) { throw 'five-smoke matrix failed/partial/not-run; the finalized cycle is retained; do not retry or promote' }
```

Protocol rules:

- Run the composed no-model preflight and candidate-maturity join immediately
  before minting the one-use matrix authorization. The coordinator-minted child object
  binds their paths/hashes, cycle ID/root, candidate, and launch window; the
  launcher revalidates them rather than generating an unbound replacement.
- The launcher verifies that the canonical usage head can safely accept the
  exact five-call reservation and that authorization, registry, preflight,
  candidate maturity, repo head, generated runtime/package, model, runner,
  host, evidence lane, external custody root, and command flags bind to the
  same cycle before the first invocation.
- Before every case and after the fifth, the launcher rechecks source HEAD/dirty state plus candidate archive/extracted-tree/build-manifest hashes. Drift stops further calls, preserves the partial observation, and invalidates the cycle; it is never repaired in place.
- One invocation per case per matrix ID. A failed case is not retried under the same matrix ID.
- Do not patch between case launches.
- Before claim, the launcher revalidates the maturity-bound fake-runner barrier,
  usage-CAS, root-fallback, and export-transaction reports and performs a
  no-output provider/auth/rate-limit/live-capacity probe. It then atomically
  consumes the one-use authorization by writing the cycle-claim receipt outside
  the unused working root, CAS-reserves five calls against the one canonical
  campaign usage head, and creates the root. A conflicting usage predecessor,
  unresolved prior settlement, root failure, or failed post-claim
  health/capacity condition stops before any model call; the
  observation finalizer settles all five as not dispatched when provable and
  consumes the claimed candidate/cycle rather than leaving ambiguous reusable
  state. Root failure uses the authorization-bound fallback finalizer path.
- Parallel `complete-observation` launches five isolated workers from one immutable launch snapshot through `barrier-five-submit-before-await-v1`. All five `worker_ready` events precede release; all five request acceptance/in-flight acknowledgments precede the first terminal-result observation or await. A case-local product failure is retained, and the remaining already-concurrent workers finish once so the ANDON cycle has a complete five-case observation set. No result is inspected for repair and no result is promoted while another worker remains active. Queued/sequential starts, a missing worker, or awaiting one response before the fifth submit do not satisfy this contract; inability to prove the partial order is `PARALLEL_CAPACITY_BLOCKED` before paid launch.
- A shared provider/auth/rate-limit failure trips a circuit breaker and cancels calls not yet dispatched where possible. Remaining rows become `NOT_RUN_INFRASTRUCTURE`, not independent model failures.
- The runner's observation finalizer executes on success, product failure, infrastructure failure, cancellation, missing row, or cycle-root creation failure. Before returning zero/nonzero it writes `kind: cycle-observation-finalizer`, CAS-settled usage receipt or explicit unresolved orphan status, candidate-consumption receipt, dispatch/artifact inventory, and a post-claim transition from `READY_UNUSED` to `CONSUMED_OBSERVED`, `CONSUMED_NO_DISPATCH`, or `CONSUMED_DISPATCH_UNKNOWN`. It does not emit `kind: cycle-verdict`. Structural pre-review and final reviewed verdicts are built only in later phases. The wrapper then stages, hash-readbacks, and atomically publishes the complete cycle/fallback bundle to A16's authorized external custody root. Missing observation finalization, final publish/readback, or usage-head reconciliation is itself a P0 custody ANDON.
- Every new attempt after Hansei receives a new matrix ID and preserves the old directory.

### Phase 5: Independent structural replay and pre-review verdict

For a matrix where all runner invocations returned zero, derive case identity only from the canonical registry. This phase must succeed without pretending that not-yet-authored cold or human reviews exist:

```powershell
$matrixRoot = [Environment]::GetEnvironmentVariable('DAEE_FIVE_SMOKE_MATRIX_ROOT')
if ([string]::IsNullOrWhiteSpace($matrixRoot)) { throw 'DAEE_FIVE_SMOKE_MATRIX_ROOT is required' }
if (-not (Test-Path -LiteralPath $matrixRoot -PathType Container)) { throw "matrix root does not exist: $matrixRoot" }
$registry = 'tests\smoke-matrix\v0.4.6.0-wip-five-smoke.json'
$caseRowsRaw = @(python tools\smoke_matrix_registry.py --manifest $registry --emit-cases-json)
if ($LASTEXITCODE -ne 0) { throw 'canonical smoke registry read failed' }
$caseRows = @(($caseRowsRaw -join "`n") | ConvertFrom-Json)
if ($caseRows.Count -ne 5) { throw "registry emitted $($caseRows.Count) cases, expected 5" }
$caseDirs = foreach ($caseRow in $caseRows) {
  $casePath = Join-Path $matrixRoot $caseRow.case_id
  if (-not (Test-Path -LiteralPath $casePath -PathType Container)) { throw "missing case run directory: $casePath" }
  Get-Item -LiteralPath $casePath
}
foreach ($caseDir in $caseDirs) {
  $record = Join-Path $caseDir.FullName 'records\staged-handoff-record.json'
  $manifest = Join-Path $caseDir.FullName 'prompt-pack-manifest.jsonl'
  $capsules = Join-Path $caseDir.FullName 'state-capsules'
  $output = Join-Path $caseDir.FullName 'output.md'
  $capture = Join-Path $caseDir.FullName 'capture-manifest.json'
  $promotionVerdict = Join-Path $caseDir.FullName 'promotion-verdict.json'
  python tools\check_staged_runtime_handshake.py --records $record
  if ($LASTEXITCODE -ne 0) { throw "handshake replay failed: $($caseDir.Name)" }
  python tools\check_prompt_pack_budget.py --manifest $manifest
  if ($LASTEXITCODE -ne 0) { throw "prompt-pack replay failed: $($caseDir.Name)" }
  python tools\check_state_capsule.py --replay $capsules --artifact $output
  if ($LASTEXITCODE -ne 0) { throw "capsule replay failed: $($caseDir.Name)" }
  python tools\check_tlang_response_closure.py --outputs $output
  if ($LASTEXITCODE -ne 0) { throw "T_lang closure failed: $($caseDir.Name)" }
  python tools\verify_candidate_output.py --profile promotion --capture-manifest $capture --json-out $promotionVerdict
  if ($LASTEXITCODE -ne 0) { throw "promotion replay failed or quarantined: $($caseDir.Name)" }
  python tools\check_validation_registry.py --verdict $promotionVerdict
  if ($LASTEXITCODE -ne 0) { throw "promotion verdict registry/hash check failed: $($caseDir.Name)" }
}
$preReviewVerdict = Join-Path $matrixRoot 'structural-pre-review-verdict.json'
python tools\build_smoke_matrix_verdict.py --mode structural-pre-review --registry $registry --cycle-root $matrixRoot --out $preReviewVerdict
if ($LASTEXITCODE -ne 0) { throw 'structural pre-review verdict build failed' }
python tools\check_smoke_matrix_manifest.py --kind structural-pre-review-verdict --manifest $preReviewVerdict
if ($LASTEXITCODE -ne 0) { throw 'structural pre-review verdict validation failed' }
$preReview = Get-Content -Raw -LiteralPath $preReviewVerdict | ConvertFrom-Json
if ($preReview.structural_matrix_status -ne 'PASS') { throw "structural matrix is not PASS: $($preReview.structural_matrix_status)" }
if ($preReview.completion_status -ne 'PARTIAL') { throw 'pre-review verdict must remain PARTIAL until human review and parity evidence are bound' }
```

Expected: every command exits `0`; the hash-bound pre-review artifact reports structural PASS and completion PARTIAL. Missing topology review is an expected open gate here, not a reason to make the structural build command fail and not permission to emit final completion.

### Phase 6: Cold GPT-5.6 comprehension/comprehensiveness review

Before any cold-review packet is disclosed or cold review is launched, one
independent human writes and hash-claims the five
`daee-topology-initial-assessment-v1` artifacts against the structurally green
outputs. This creates the accepted pre-disclosure boundary and avoids accidental
anchoring. The later human adjudication binds those unchanged hashes.

For each structurally replayed case, `tools/build_cold_review_packet.py` emits one hash-bound self-contained packet using Plan A01's contract. The packet contains the exact input, unmodified candidate output, concise DAEE purpose/rubric, Stage01-Stage08 records, witness/envelope, and body references. It contains no prior conversation, expected answer, expected burden/submove topology, or case-specific argument bank.

GPT-5.6 first reconstructs the candidate's thesis, selected pressures,
burdens/submoves, performed operations, resultants, lifecycle states, and
restorative/closure arc. It grades only after `comprehension_status=PASS`.
`REVIEW_INVALID` is preserved and human-classified as reviewer transport,
delivery corruption, packet insufficiency, reviewer policy incompatibility,
candidate intelligibility, or unproven origin. Every failed/ambiguous review
emits a hash-bound owner incident report and pauses before retry or repair. A
same-output transport retry preserves the valid packet hash; packet-construction
repair preserves input/output hashes but uses a new packet hash with predecessor,
delta, red/green builder, anti-answer-bank, and authorization evidence. A shared
rubric/schema/builder semantic change repeats the complete five-review cohort,
or ten-review cohort under paired reconvergence. Candidate-intelligibility
failure requires a repaired successor candidate. No attempt is selected by
favorability. Cold findings begin as immutable challenges. A challenge becomes
a product ANDON when the independent human review upholds it or cannot resolve
it; an answered challenge retains the cold dissent and new hash-bound
evidence/rationale.

### Phase 6a: Human topology/body adjudication

Each case receives Plan A01's `daee-topology-review-v1` artifact, bound by hash to the input, Stage02/04/05 records, Stage07 output, and `field_witness`. The reviewer answers:

- Are all materially live input pressures represented or explicitly disposed?
- Are split/merge decisions justified without a topic quota?
- Does every routed owner/register obligation have a substantive body or honest hold?
- Are generated, held, pre-empted, and no-new-resultant states correctly distinguished?
- Does the final witness reconstruct the performed trajectory and public body?
- Is output mass adequate because all obligations are paid, rather than because a byte target was met?

Allowed verdicts: `PASS`, `FAIL`, `PARTIAL`. The human first writes a separate hash-claimed `daee-topology-initial-assessment-v1` before cold-review disclosure; the final `daee-topology-review-v1` binds its unchanged hash and disclosure receipt. It requires exact-set equality between cold finding IDs and human adjudications, with every finding dispositioned exactly once as `upheld`, `answered`, or `unresolved`. `answered` requires rationale plus hash-valid evidence bound to the challenged target IDs. Disagreement or uncertainty is `PARTIAL`, not an average. `REVIEW_INVALID` carries an explicit cause and predecessor-attempt lineage. The human cannot waive a structural failure, edit raw output, omit/duplicate a cold finding, or call an unresolved material challenge PASS. When the adjudicator also owns the patch or overturns a material FAIL, a hash-bound affirming second independent human/accountable review is required; owner-only reversal without new evidence remains PARTIAL. `tools/check_topology_review.py` verifies this custody and cannot self-author the review.

### Phase 6b: Final completion verdict after review and lane-parity custody

Only after all five A01 cold GPT-5.6 reviews, all five human topology/substantive reviews/adjudications, and A13 deterministic paired lane-parity fixtures are green may the final verdict be built:

```powershell
$registry = 'tests\smoke-matrix\v0.4.6.0-wip-five-smoke.json'
$matrixRoot = [Environment]::GetEnvironmentVariable('DAEE_FIVE_SMOKE_MATRIX_ROOT')
if ([string]::IsNullOrWhiteSpace($matrixRoot)) { throw 'DAEE_FIVE_SMOKE_MATRIX_ROOT is required' }
python tools\check_package_harness_parity.py --matrix-root $matrixRoot --require-evidence-lane package-faithful --require-paired-fixture-verdict
if ($LASTEXITCODE -ne 0) { throw 'package-faithful/lane-parity evidence is incomplete or invalid' }
$finalVerdict = Join-Path $matrixRoot 'five-smoke-verdict.json'
python tools\build_smoke_matrix_verdict.py --mode completion --registry $registry --cycle-root $matrixRoot --out $finalVerdict
if ($LASTEXITCODE -ne 0) { throw 'final completion verdict build failed' }
python tools\check_smoke_matrix_manifest.py --kind cycle-verdict --manifest $finalVerdict
if ($LASTEXITCODE -ne 0) { throw 'final completion verdict validation failed' }
$final = Get-Content -Raw -LiteralPath $finalVerdict | ConvertFrom-Json
if ($final.structural_matrix_status -ne 'PASS') { throw "final structural status is $($final.structural_matrix_status)" }
if ($final.completion_status -ne 'PASS') { throw "final completion status is $($final.completion_status)" }
if ($final.regression_status -ne 'unproven') { throw 'matrix must not advance regression causality' }
```

Expected: exit `0` only when the one package-faithful five-case cycle, five cold GPT-5.6 reviews, five human reviews/adjudications, A11 verdicts, candidate-package custody, and deterministic A13 paired-lane evidence all bind to the same cycle. No second paid harness-assisted five-case run is required.

### Phase 7: Retained-source validation and optional promotion

Only after one case has Stage01-Stage08 structural PASS, topology/body PASS, package-faithful custody, the matrix's deterministic paired-lane fixture verdict, exact custody, and owner approval may its source artifacts be checked for possible retained promotion:

```powershell
$run = [Environment]::GetEnvironmentVariable('DAEE_PROMOTION_SOURCE_RUN')
if ([string]::IsNullOrWhiteSpace($run)) { throw 'DAEE_PROMOTION_SOURCE_RUN is required' }
if (-not (Test-Path -LiteralPath $run -PathType Container)) { throw "source run directory does not exist: $run" }
python tools\promote_retained_proof_case.py --source-only --hash-record "$run\staged-smoke.hashes.json"
```

The environment variable is intentionally an owner decision, not an executable preauthorization. Source-only mode writes no retained case. Actual promotion requires separate explicit authorization and the current `--rows` argument. Never use the stale `--row-scope` spelling.

The fifth retained directory and manifest row do not exist before this phase. A five-smoke completion pass does not automatically authorize promotion, packaging, issue filing, commit, push, tag, release, or publication.

### Phase 8: Optional post-completion GPT/Opus paired reconvergence

This phase is not authorized by the initial WIP campaign. If the owner later
authorizes an exact Opus protocol, the first Opus five-case run remains a
separate post-completion observation against the completed package bytes. An
Opus failure is preserved and classified before any patch. A countermeasure that
would weaken notation, recursion, arbitrary topology, anti-answer-bank
discipline, body/witness fidelity, or GPT behavior is rejected as an invalid
framework accommodation.

Once an accepted Opus product countermeasure changes runtime, package, shared
checker, runner/adapter, or review-contract identity, the new head becomes
`CROSS_MODEL_RECONVERGENCE_REQUIRED`. Build two fresh sibling candidate IDs
with identical source/archive/tree/build-manifest hashes, one for GPT-5.5/high
and one for the separately frozen Opus protocol. A parent
`barrier-ten-submit-before-await-v1` proves all ten child calls accepted/in
flight before any result is observed. Each child retains the ordinary five-case
registry and isolated state; the parent joins identities and verdicts without
forcing identical output or topology.

All ten outputs independently pass Stage01-Stage08. One human then hash-claims
ten pre-disclosure initial assessments, ten isolated cold reviews run, and the
same human performs final adjudication against the unchanged initial hashes.
Any material GPT or Opus ANDON fails the parent cycle. After countermeasure,
commit/push/CI, and two fresh sibling candidates, rerun all ten with no pass
carry-forward. The only positive claim is scoped
`POST_COMPLETION_CROSS_MODEL_COMPATIBILITY_PASS` for one reviewed 10/10 parent
cycle; it is not universal cross-model proof or release authority.

## Attempt and Failure Semantics

For each case:

- exit `0` plus eight passing stages means structural runner PASS only;
- nonzero before Stage01 is a launch/preflight ANDON;
- a typed host/provider control-layer block proved before model-authored output
  entered Stage01 is `NOT_RUN_POLICY_INCOMPATIBILITY`;
- a model-authored response that understands but refuses, disputes, summarizes,
  or substitutes for mandatory execution is `PRODUCT_REFUSAL` at Stage01;
- an unlocatable refusal layer is `REFUSAL_ORIGIN_UNPROVEN`; it fails without
  unsupported model/platform attribution;
- nonzero during Stage01-06 is a producer/handshake ANDON at the earliest failed stage;
- nonzero during Stage07 is release/assembly/output-checker ANDON;
- nonzero during Stage08 is sidecar/B5/hash ANDON;
- topology review FAIL/PARTIAL blocks completion even if runner exit is `0`;
- cold-review material FAIL/PARTIAL or unresolved `REVIEW_INVALID` blocks completion even if runner exit is `0`;
- package-faithful custody or paired-lane fixture status `NOT_RUN` blocks completion but does not relabel the structural result;
- one case failure makes matrix completion FAIL/PARTIAL; four passes do not compensate.

Do not retry transport or expand a section within the same completion attempt. The zero retry/expansion flags make the one-shot evidence interpretable. If later engineering requires an approved retry policy, it must be predeclared for all five cases and receives a new matrix protocol version.

### Matrix-level ANDON convergence

Any Stage01-Stage08, cold-review, human-review, custody, or infrastructure ANDON fails the entire cycle. Preserve all five rows and their raw/derived artifacts. Passing rows from that cycle remain evidence but are not reusable completion credits.

For every distinct ANDON, and for every case affected by a shared root:

1. register the exact failure, first rightful stage/review gate, artifacts, and hashes;
2. Gemba the live producer/checker/runtime/package/review owner;
3. perform a real 5 Whys chain to owner/source and Hansei;
4. implement the smallest general countermeasure at that owner;
5. add neutral valid/invalid red-green canaries that detect the transition, not a copied case string;
6. run owner-level Smoke A, integrated Smoke B, deterministic CI/freshness/package checks, and right-reason mutation checks;
7. under separate one-use A16 commit and push authorizations, create a verbose ANDON-bound commit, push non-force to `codex/v0.4.6.0-runtime-footprint` with compare-and-swap remote-head protection, and require exact-SHA owner-designated CI checks plus any configured/named Pages check to read back green;
8. build a new immutable candidate and child authorization;
9. rerun all five from scratch in parallel under a new cycle ID.

Commit and push in step 7 require Plan A16's separate one-use action authorizations; the campaign/matrix manifest cannot be presented as VCS authority. Do not rerun only the failed cases, patch between workers, reuse any consumed candidate, import a prior passing row, coach the model with the failed answer, or change model/settings without creating a new campaign protocol whose results are marked non-comparable to the old protocol. Same-class recurrence stops another paid cycle until the deeper architecture/root-owner analysis and a recurrence canary are green. This is audited convergence, not stochastic retry-until-pass.

## Five-Smoke Coverage Without Argument Banking

The five cases are selected because they expose different failure surfaces, but the runner must not use these descriptions for routing:

| Case | What maintainers inspect after the run | Forbidden precomputation |
| --- | --- | --- |
| secularism | short hard-input handling, worldview-frame adequacy, no length-based under-routing | expected burden count or secularism answer |
| Khaybar | long source bundle, formal-logic framing, source/status/semantic distinctions | expected Arabic/source route or proof outline |
| trinitarian J173 | textual claim, grammatical argument, person/nature/identity distinctions | expected owner chain or doctrinal script |
| TST/Lillard | moral protest, suffering/punishment, source request, register sensitivity | motive diagnosis or fixed pastoral/doctrinal sequence |
| Torah/Qur'an source authentication | deconversion narrative, text-consistency/corruption/beneficiary/comparative-revelation pressures | expected burdens, Torah/Qur'an conclusion, quotations, manuscript argument, or citation bank |

These descriptions belong in reviewer guidance only. They do not enter model prompts, route fixtures, owner allowlists, or expected output files.

## Rollback

- Revert registry/checker/playbook changes together if the five-case gate cannot be made deterministic.
- Never delete the fifth input fixture merely because a model run fails; input registration is independent of output success.
- Never create or preserve a retained fifth case directory from a failed run.
- Keep all failed matrix directories immutable and ignored under `.daee/`.
- If a hash mismatch is caused by line endings, restore LF and rehash the canonical prompt. Do not weaken raw hash checks or silently switch to normalized hashing.
- If a run requires HOLD/PARTIAL under the topology contract, retain it as valid negative evidence; do not coerce Stage07/08 completion.
- If Plan 13 parity work is not complete, matrix structural runs may be performed only as diagnostic evidence and `completion_status` remains `PARTIAL`.

## STOP / ANDON Conditions

Stop and record an ANDON when:

- any canonical input hash drifts;
- the fifth input is changed, summarized, or stripped without owner approval;
- registry metadata includes expected topology or answer content;
- Gate 14 still depends on a retained fifth case;
- preflight does not check all five unique inputs;
- a run directory is reused or overwritten;
- a cycle is claimed without an external claim receipt, or root-creation failure
  lacks its fallback observation finalizer;
- producer/reviewer reservation does not CAS the same canonical campaign usage
  head, the predecessor conflicts, or an orphaned reservation is treated as
  unused capacity;
- the `codex` adapter or `tools/run_five_smoke_matrix.py` entrypoint differs from
  authorization, or exact resolved runner/model/app versions are absent;
- five ready/acceptance events and the
  `barrier-five-submit-before-await-v1` partial order cannot be proved;
- result collection, parse, or checking begins before the fifth request is
  accepted/in flight;
- an external staging tree or unverified manifest is offered as final evidence,
  a resume overwrites a hash mismatch, or final publish/readback is absent;
- model/runner/runtime/settings change between cases;
- a case is retried inside the same matrix ID;
- a semantic normalizer repairs route topology;
- fewer than eight ordered passing stages are called PASS;
- any Stage08 sidecar or hash binding fails;
- topology review is skipped or averaged;
- one case failure is averaged into a matrix pass;
- historical retained output is described as fresh v0.4.6 behavior;
- structural PASS is described as semantic truth, provenance, uptake, or release readiness;
- `regression_status` is changed from `unproven` without controlled comparison evidence.

Required record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED
matrix_id: <immutable id>
case_id: <one of five or matrix-wide>
class: input-drift | preflight | launch | producer | stage-contract | release-output | sidecar | topology-review | package-faithful-custody | lane-parity | claim-overreach
earliest_stage: <01-08 or preflight>
first_failed_checker: <exact checker or null>
failing_command: <exact command>
runtime_commit: <40 hex>
runtime_sha256: <hash>
input_sha256: <hash>
preserved_run_dir: <path>
downstream_invalidated: [<stages/cases>]
next_action: <one concrete source/checker/fixture action>
regression_status: unproven
```

## Definition of Done

- The exact fifth prompt exists at the registered path with the pinned bytes/hash.
- The registry contains exactly the five required IDs and no answer/topology metadata.
- No-model preflight checks five canonical prompt files and uses five-case wording.
- The fifth case has no retained row before a current successful run and separate owner approval.
- Completion checker has positive and right-reason negative fixture coverage.
- One atomically consumed candidate-package build authorization yields one `READY_UNUSED` execution-mini record with source/CI/archive/tree/build-manifest hashes; a proved pre-claim stop may preserve it, while a claimed matrix consumes it neutrally to `CONSUMED_OBSERVED`, `CONSUMED_NO_DISPATCH`, or `CONSUMED_DISPATCH_UNKNOWN`; failed builds remain `QUARANTINED` and no terminal candidate is reused.
- One authorized matrix freezes the package-faithful
  `tools/run_five_smoke_matrix.py --model-runner codex` lane, exact resolved
  model/runner/app versions, runtime, settings, and one attempt per case.
- Producer and cold-review reservations advance one canonical campaign usage
  head through exclusive/CAS transactions; conflicts spend zero calls, and
  orphan recovery cannot mint capacity or reuse a candidate.
- The cycle claim exists outside the working root; root failure yields a neutral
  fallback observation finalizer and truthful `CONSUMED_NO_DISPATCH` only when
  zero dispatch is proved.
- The dispatch manifest proves all five workers ready and all five requests
  accepted/in flight before any result is observed, without a timing threshold.
- Evidence is staged, hash-read back, and atomically published to an unused
  final path/pointer; partial staging never satisfies retention.
- Every case preserves raw/adapted stage evidence, prompt envelopes, capsules, output, sidecars, and hashes.
- Every case has exactly eight ordered `status=pass` stage records.
- No case contains semantic route repair events.
- Every case independently passes topology/body adjudication.
- Every case has cold GPT-5.6 comprehension PASS plus a final cold-review disposition, and a human review/adjudication with no unresolved material challenge.
- Structural replay first emits `structural-pre-review-verdict` with structural PASS/completion PARTIAL; only the later review/parity join may emit final `cycle-verdict` PASS/PASS.
- The matrix itself is package-faithful, and deterministic package-faithful/harness-assisted lane-parity fixtures are satisfied per Plan 13; otherwise completion remains `PARTIAL`.
- All five cases pass; no averaging or majority rule exists.
- Any failed cycle has a complete IMPLEMENTAUDIT record, verified countermeasure/canaries, pushed-green repair boundary, fresh candidate, and complete five-case rerun; no selective pass carry-forward exists.
- Structural scope and non-claims remain explicit.
- Historical four-case evidence remains historical and is not overwritten.
- `regression_status` remains `unproven` unless a separate controlled comparison advances it.
- No commit, push, package, promotion, issue, release, or publication is implied by matrix completion.

## Confidence

Five-input registry and deterministic completion checker: **YES, implementation-ready after owner authorization.**  
Stage01-Stage08 model matrix: **PARTIAL, implementation/campaign/spend/evidence-root authorization gated; the canonical Codex producer lane is settled.**  
Topology/body adequacy: **PARTIAL until independent review of fresh outputs.**  
Package-faithful custody and deterministic lane parity: **PARTIAL until the candidate and Plan 13 paired-fixture evidence exist.**  
v0.4.6.0-wip completion today: **NO. The fifth case is unregistered and no fresh five-case matrix exists.**
