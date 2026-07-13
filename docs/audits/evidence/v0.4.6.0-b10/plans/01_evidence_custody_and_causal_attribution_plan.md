# ANDON A01: Evidence Custody and Causal Attribution

Priority: P0 containment  
Implementation target: PR #9 branch at planned head `6987c9eb...`  
Regression status: `unproven`  
Plan status: implementation-ready for repo-local custody tooling; model capture remains owner-gated

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Abnormality

A captured v46-shaped output is a strong invalid specimen: it uses completion, generated-burden, MRP, and `field_witness` language while current replay rejects it. However, the evidence chain does not bind the original prompt, exact runtime package, source commit, host/model, invocation, context state, output budget, or model response to one immutable capture record. The local `outputv45.md` and `outputv46.md` are not an admissible controlled pair.

This creates two different questions that must not be conflated:

1. Did a proof-looking structurally invalid output occur? Confirmed.
2. Did v0.4.6.0 runtime-footprint cause or amplify it relative to v0.4.5.0? Unproven.

## Current Evidence

### Confirmed

- `work/grok-v46-output.md` is retained and hashable.
- Current candidate-verifier replay recorded in the audit rejects it on three of six structural checkers.
- The artifact begins with premature completion, contradicts `B_LA/B_MRP` provenance, and contains non-parser-stable placeholder witness content.
- `verify_candidate_output.py` is explicitly post-hoc and structural only.
- PR #9 hot runtime is materially smaller than main, but total package/source mass is not smaller.
- The current branch no-model preflight passes all 16 gates.

### Missing

- Exact source prompt bound to the Grok specimen.
- Exact `.skill` package bytes and package hash used for the run.
- Model/host version, date, invocation surface, system/context state, output budget, and retry/continuation history.
- A v45 run and v46 run controlled on all feasible variables.
- A predeclared adjudication protocol for stochastic differences.

### Non-claims

- A verifier FAIL proves structural rejection under the wired battery, not theological falsehood.
- A verifier PASS proves structural acceptance under the wired battery, not semantic completeness.
- One pair cannot prove general model behavior.
- A different output length does not prove regression.

## Five Whys

1. Why can the ANDON not be causally assigned to v46?  
   Because the failing output is not bound to a complete run manifest and there is no controlled comparator.

2. Why is the run manifest incomplete?  
   The capture workflow retained answer text but did not make prompt/package/model/invocation/verdict custody a mandatory atomic artifact.

3. Why was answer text treated as enough?  
   Existing tools focus on post-hoc structural checking and retained proof fixtures, while live external-host capture remains explicitly owner-scoped.

4. Why does that matter for runtime-footprint diagnosis?  
   Model, host, context, package identity, output limit, and continuation policy can each change burden topology and body depth. Without controlling them, branch attribution is confounded.

5. Why did prior reporting still drift toward a branch-causal story?  
   The visible correlation between a smaller hot root and a thinner proof-looking output was narratively compelling, while the evidence ledger did not force every causal edge to retain `confirmed/inferred/unproven` status.

Root owner/source: external-output custody and promotion boundary, principally `tools/verify_candidate_output.py`, retained-corpus conventions, scorecard tooling, and the future authorized model-capture operator. Runtime source is not the first owner of this abnormality.

## Hansei

### What went well

- The invalid specimen was retained instead of summarized away.
- Later reports corrected the causal claim and preserved `regression_status: unproven`.
- Existing output replay gives a deterministic structural baseline.

### What failed

- Capturing an answer was not the same operation as capturing a reproducible run.
- Package claims inside model output were treated as evidence even though the output cannot attest to its own runtime provenance.
- Earlier plans used approximate paths, unsupported wildcard verifier commands, and underspecified “same model where possible” language.
- A handoff state and an audit-complete state appeared together in older material.

### Lesson

Causal attribution must be a data product, not a narrative conclusion. Every comparison row must be mechanically bound to the exact artifacts that license it, and missing controls must lower the status rather than be filled by inference.

## Target State

Create a custody subsystem that stores one immutable manifest per captured output and one comparison manifest per authorized comparison. Use the verified stacked geometry rather than collapsing several development layers into one comparison:

1. v0.4.5.0 at `8c14e28...` is the public release-line behavior baseline.
2. Current `main` at `c86b3c6...` is PR #8's GitHub-declared base and the inherited-main layer.
3. PR #8 head `56d023e...`, branch `codex/hardening-all-20260703`, is 84 commits ahead of that main base and is also PR #9's declared base. It is the hardening layer.
4. PR #9 head at `6987c9e...` is the runtime-footprint implementation target.

The local PR checkout reports `--is-shallow-repository=true`; a failed local `git merge-base` query therefore cannot establish unrelated history. GitHub PR metadata and the GitHub compare API establish `c86b3c6... -> 56d023e... -> 6987c9e...`. Code introduced specifically by PR #9 is attributed with PR9-base to PR9-head. Release-line behavioral comparison may use v0.4.5.0 to PR9-head, but it must identify both the PR8-hardening and PR9-runtime-footprint layers as intervening variables unless the intermediate cells are run. The subsystem must support:

- exact input bytes and SHA-256;
- exact runtime archive bytes and SHA-256, plus source commit and build manifest;
- model runner, model identifier, host/application version where available;
- invocation command or exact operator procedure;
- context/session policy, tools enabled, output/token budget, retries, continuations, and truncation state;
- raw output bytes and SHA-256;
- per-checker command, version/commit, exit code, stdout/stderr hash, and first failure;
- human topology adjudication separated from structural verdict;
- a causal status that cannot advance when required controls are absent.

## Proposed Data Shapes

### `capture-manifest-v1`

Planned schema owner: `schema/captured-output-manifest.schema.json`.

Required fields:

```json
{
  "schema": "daee-captured-output-v1",
  "case_id": "gate88-torah-quran-source-authentication",
  "capture_id": "<stable operator-assigned id>",
  "input": {
    "path": "input.txt",
    "sha256": "<64 lowercase hex>",
    "byte_count": 0
  },
  "runtime": {
    "version_label": "v0.4.5.0 | v0.4.6.0-wip",
    "source_commit": "<40 hex>",
    "package_path": "<repo-relative or external-custody relative path>",
    "package_sha256": "<64 lowercase hex>",
    "build_manifest_sha256": "<64 lowercase hex>"
  },
  "execution": {
    "operator": "<accountable human or authorized runner>",
    "model_runner": "codex | claude | other",
    "model": "<exact reported identifier>",
    "host": "<reported host/application>",
    "started_utc": "<RFC3339>",
    "fresh_session": true,
    "tool_policy": "<label>",
    "output_budget": "<reported budget or unknown>",
    "retry_count": 0,
    "continuation_count": 0,
    "truncated": false
  },
  "output": {
    "path": "output.md",
    "sha256": "<64 lowercase hex>",
    "byte_count": 0
  },
  "structural_replay": {
    "verifier_commit": "<40 hex>",
    "aggregate_status": "PASS | FAIL | NOT_RUN",
    "first_failed_checker": "<tool or null>",
    "verdict_path": "verifier-verdict.json",
    "verdict_sha256": "<64 lowercase hex>"
  },
  "topology_review": {
    "schema": "daee-topology-review-v1",
    "review_id": "<immutable id or null>",
    "status": "PASS | FAIL | PARTIAL | NOT_REVIEWED",
    "review_path": "topology-review.json",
    "review_sha256": "<64 lowercase hex or null>"
  },
  "cold_comprehensiveness_review": {
    "schema": "daee-cold-comprehensiveness-review-v1",
    "review_id": "<immutable id or null>",
    "comprehension_status": "PASS | REVIEW_INVALID | NOT_REVIEWED",
    "coverage_verdict": "PASS | FAIL | PARTIAL | NOT_GRADED",
    "review_path": "cold-comprehensiveness-review.json",
    "review_sha256": "<64 lowercase hex or null>"
  },
  "non_claims": [
    "structural PASS is not semantic truth",
    "one capture is not a cross-host behavior claim"
  ]
}
```

Unknown values are represented as explicit `unknown`/`null` values only where the schema permits them. They are never guessed from prose inside the answer.

### `topology-review-v1`

Planned schema owner: `schema/topology-review.schema.json`. This is a custody record for accountable human adjudication, not a machine claim of semantic truth. Every review reference in capture and smoke manifests must be a hash-bound object with this shape:

```json
{
  "schema": "daee-topology-review-v1",
  "review_id": "<immutable id>",
  "case_id": "<registered case id>",
  "cycle_id": "<same cycle as reviewed output>",
  "input": {"path": "input.txt", "sha256": "<64 hex>"},
  "artifacts": {
    "stage02_sha256": "<64 hex>",
    "stage04_sha256": "<64 hex>",
    "stage05_sha256": "<64 hex>",
    "stage07_output_sha256": "<64 hex>",
    "field_witness_sha256": "<64 hex>"
  },
  "reviewer": {
    "identity_or_accountable_role": "<nonempty>",
    "relationship_to_producer": "independent | producer | owner-adjudicator",
    "independence_basis": "<required when independent>"
  },
  "reviewed_utc": "<RFC3339>",
  "independent_initial_assessment": {
    "path": "human-initial-assessment.json",
    "sha256": "<64 hex>",
    "recorded_utc": "<RFC3339 before cold-review disclosure>",
    "verdict": "PASS | FAIL | PARTIAL",
    "finding_ids": ["TR1"]
  },
  "cold_review_disclosure": {
    "cold_review_path": "cold-comprehensiveness-review.json",
    "cold_review_sha256": "<64 hex>",
    "disclosed_utc": "<RFC3339 not before initial assessment>",
    "initial_assessment_sha256_at_disclosure": "<same 64 hex>"
  },
  "cold_challenge_adjudications": [
    {
      "cold_finding_id": "CR1",
      "challenged_target_ids": ["P3", "B2", "OP-B2-3"],
      "disposition": "upheld | answered | unresolved",
      "evidence_refs": [
        {"path": "stage04.json", "sha256": "<64 hex>", "target_ids": ["OP-B2-3"]}
      ],
      "rationale": "<answer to the exact challenge>"
    }
  ],
  "review_invalid_classification": {
    "cause": "reviewer_transport | delivery_corruption | packet_insufficiency | reviewer_policy_incompatibility | candidate_intelligibility | origin_unproven | not_applicable",
    "classified_attempt_id": null,
    "classified_attempt_sha256": null,
    "predecessor_attempt_sha256s": [],
    "basis": null,
    "owner_incident_report_path": null,
    "owner_incident_report_sha256": null,
    "owner_notified_utc": null,
    "continuation_authorized_utc": null
  },
  "findings": [
    {"finding_id": "TR1", "target_ids": ["P3"], "severity": "material | nonmaterial", "basis": "<artifact-grounded review text>"}
  ],
  "verdict": "PASS | FAIL | PARTIAL",
  "owner_adjudication": {
    "required": false,
    "adjudicator": null,
    "decision": null,
    "evidence_refs": [],
    "basis": null,
    "decided_utc": null
  },
  "second_independent_review": {
    "required": false,
    "reason": "not-required | patch-owner-reversal | material-fail-overturn",
    "reviewer_identity_or_accountable_role": null,
    "relationship_to_patch_owner": null,
    "independence_basis": null,
    "review_path": null,
    "review_sha256": null,
    "verdict": null
  },
  "non_claims": ["review PASS is scoped human adjudication, not universal semantic truth"]
}
```

`human-initial-assessment.json` is a separately claimed immutable artifact. It
contains the question-level answers, initial findings, target IDs, and initial
verdict before the cold-review packet is disclosed. The disclosure receipt
binds that exact hash. This does not cryptographically prove a person's mental
independence, but it prevents the final record from silently rewriting the
initial view after seeing the model challenge.

`tools/check_topology_review.py` recomputes every referenced hash, verifies
cycle/case identity, validates disclosure/attempt lineage, and requires
exact-set equality between cold finding IDs and human challenge adjudications. `PASS` is
rejected when any material challenge is `upheld` or `unresolved`, when an
`answered` challenge lacks at least one hash-valid evidence reference bound to
the challenged target IDs, or when its rationale does not address that finding.
`REVIEW_INVALID` classification is explicit. A transport, delivery, reviewer
policy, packet, or unproven-origin failure first emits a hash-bound owner
incident report and pauses before retry or repair. Candidate intelligibility
cannot use a same-output review retry. A patch owner or owner-adjudicator who
reverses a material FAIL triggers `second_independent_review.required=true`,
and PASS is impossible until the second review is hash-valid, independent, and
affirming. The checker cannot author the review, decide theology, or infer
reviewer independence. A producer self-review remains evidence but cannot
satisfy the independent matrix requirement.

### `cold-comprehensiveness-review-v1`

Planned schema owner: `schema/cold-comprehensiveness-review.schema.json`. This is a second review lane, not a replacement for the human `topology-review-v1` record. The owner-selected reviewer family is GPT-5.6. The exact resolved model identifier, host, review-prompt hash, and raw review response are recorded at execution time.

The reviewer is deliberately cold: it has no conversation history, branch familiarity, private expected topology, expected answer, or prior model-review conclusion. Cold does not mean context-starved. Its hash-bound packet contains the exact smoke input, unmodified candidate output, a concise DAEE purpose/rubric, Stage01-Stage08 records, public witness, audit envelope, and body references needed to understand what the output claims to have done.

Before grading, the reviewer must reconstruct the candidate in its own words:

1. central thesis and intended response;
2. material input pressures selected by the candidate;
3. burden/submove topology actually present;
4. performed operations and claimed local/aggregate resultants;
5. generated, held, pre-empted, and unresolved states;
6. restorative and closure trajectory.

The planned record is:

```json
{
  "schema": "daee-cold-comprehensiveness-review-v1",
  "review_id": "immutable-id",
  "attempt_index": 1,
  "predecessor_review_attempt_sha256": null,
  "review_authorization_sha256": "64-lowercase-hex",
  "case_id": "registered-case-id",
  "cycle_id": "same-cycle-as-output",
  "reviewer": {
    "model_family": "gpt-5.6-sol",
    "reasoning_effort": "xhigh",
    "exact_model_identifier": "reported-at-execution",
    "host": "reported-at-execution",
    "fresh_context": true,
    "prior_conversation_supplied": false
  },
  "packet": {
    "manifest_path": "cold-review-packet-manifest.json",
    "manifest_sha256": "64-lowercase-hex",
    "predecessor_manifest_sha256": null,
    "retry_mode": "initial | same-packet-transport | rebuilt-packet",
    "packet_delta_path": null,
    "packet_delta_sha256": null,
    "prompt_sha256": "64-lowercase-hex",
    "candidate_output_sha256": "64-lowercase-hex"
  },
  "comprehension": {
    "status": "PASS | REVIEW_INVALID",
    "candidate_thesis": "reviewer reconstruction",
    "pressure_ids": ["P1"],
    "burden_ids": ["B1"],
    "operation_ids": ["OP-B1-1"],
    "resultant_ids": ["R-B1"],
    "restoration_summary": "reviewer reconstruction"
  },
  "grading": {
    "material_pressure_coverage": "PASS | FAIL | PARTIAL | NOT_GRADED",
    "burden_partition_adequacy": "PASS | FAIL | PARTIAL | NOT_GRADED",
    "submove_and_body_depth": "PASS | FAIL | PARTIAL | NOT_GRADED",
    "resultant_and_recursion_honesty": "PASS | FAIL | PARTIAL | NOT_GRADED",
    "closure_reconstructibility": "PASS | FAIL | PARTIAL | NOT_GRADED",
    "overall": "PASS | FAIL | PARTIAL | NOT_GRADED"
  },
  "findings": [
    {
      "finding_id": "CR1",
      "target_ids": ["P1", "B1", "OP-B1-1"],
      "severity": "material | nonmaterial",
      "basis": "artifact-grounded review",
      "recommended_disposition": "uphold | answer | investigate"
    }
  ],
  "non_claims": [
    "formal notation presence is not execution",
    "length is not comprehensiveness",
    "cold review PASS is not universal semantic truth"
  ]
}
```

`REVIEW_INVALID` is not silently converted into candidate PASS or FAIL. The raw
attempt is retained and the human reviewer classifies reviewer transport,
delivery corruption, packet insufficiency, reviewer policy incompatibility,
candidate intelligibility, or unproven origin. Every failed or ambiguous review
emits an owner incident report before continuation. Candidate-intelligibility
failure registers an output ANDON and requires a repaired successor candidate.
For transport/reviewer/delivery failure with a valid canonical packet, a
same-output retry preserves both output and packet hashes. A packet-construction
repair preserves the input/output hashes but may use a new packet hash only with
predecessor hash, exact delta, red/green builder proof, anti-answer-bank scan,
new one-use authorization, and complete attempt lineage. A shared rubric,
schema, or packet-builder semantic change requires every cold review in the
five- or ten-output cohort to be repeated under one new review protocol. Only
the classified non-candidate cause may change. Selecting among reviewers or
attempts by favorability is forbidden.

The human `topology-review-v1` then independently evaluates topology/body comprehensiveness plus theological, factual, source, and argumentative adequacy. It consumes the cold review only after writing its own initial findings. Each cold challenge begins `open` and receives exactly one final human disposition:

- `upheld`: register the product ANDON and fail the cycle;
- `unresolved`: register/retain the ANDON and keep the cycle `PARTIAL` or `FAIL`;
- `answered`: remain PASS-eligible only when the adjudication binds new
  artifact-grounded evidence and rationale that answers the exact challenged
  IDs without editing the raw output.

The cold challenge, dissent, and answer evidence all remain immutable. Human adjudication cannot waive missing structural artifacts, alter raw output, or turn an unresolved material challenge into PASS. If the adjudicator owns the patch, authored the disputed answer, or overturns a material FAIL, a second independent accountable human review must affirm the evidence; an owner-only reversal remains `PARTIAL`.

### `comparison-manifest-v1`

Required controls for each pair or three-way cell:

- same exact input hash;
- separately hash-bound v45, inherited-main, PR8-head/PR9-base, and PR9-head packages for the full lineage experiment, or explicit `not_run` cells;
- same model runner and model identifier, unless the comparison status is downgraded to `confounded`;
- fresh session for each run;
- same tool policy, output budget, retry and continuation policy;
- capture order recorded and, for multiple replicates, alternated to reduce ordering bias;
- raw outputs retained without repair;
- structural replay and independent topology review for each output.

Allowed `regression_status` values:

```text
unproven
not-comparable
confounded
candidate-observed
replicated-candidate
not-observed
```

No automated tool may emit `proven`. A stronger causal claim requires owner-reviewed evidence outside this schema.

Transition rules:

- Missing package/input hash: `not-comparable`.
- Any changed model/host/tool/output-budget variable: `confounded` unless the owner explicitly defines that variable as the object of study.
- One admissible PR9-base/PR9-head pair where base passes the predeclared topology criteria and head fails: `candidate-observed` for a PR9-introduced regression.
- A v45/PR9-head difference without PR8-head/PR9-base and, where relevant, inherited-main cells: `confounded` for PR9 attribution, although it remains release-line comparison evidence.
- Predeclared repeated PR-base/PR-head pairs showing the same direction without a known confounder: `replicated-candidate`.
- Mixed results: remain `unproven` and report the distribution; do not average structural failures into a pass.
- Both fail: `not-observed` for a v46-only regression and a separate baseline defect remains open.

## Exact Owner and Edit Map

### Add

- `schema/captured-output-manifest.schema.json`
- `schema/captured-output-comparison.schema.json`
- `schema/topology-review.schema.json`
- `schema/topology-initial-assessment.schema.json`
- `schema/cold-comprehensiveness-review.schema.json`
- `schema/review-incident-report.schema.json`
- `tools/check_captured_output_manifest.py`
- `tools/build_captured_output_verdict.py`
- `tools/check_topology_review.py`
- `tools/check_cold_comprehensiveness_review.py`
- `tools/check_review_incident_report.py`
- `tests/captured-output-custody/valid/complete-single-capture/`
- `tests/captured-output-custody/valid/comparable-v45-v46-pair/`
- `tests/captured-output-custody/invalid/missing-input-hash/`
- `tests/captured-output-custody/invalid/self-attested-package-faithful/`
- `tests/captured-output-custody/invalid/comparison-changed-model-unmarked/`
- `tests/captured-output-custody/invalid/regression-status-overclaim/`
- `tests/captured-output-custody/valid/hash-bound-independent-topology-review/`
- `tests/captured-output-custody/invalid/topology-review-hash-drift/`
- `tests/captured-output-custody/invalid/topology-review-self-review-called-independent/`
- `tests/captured-output-custody/invalid/topology-review-open-challenge-called-pass/`
- `tests/captured-output-custody/valid/initial-human-assessment-before-cold-disclosure/`
- `tests/captured-output-custody/invalid/initial-human-assessment-missing/`
- `tests/captured-output-custody/invalid/initial-assessment-hash-changed-after-disclosure/`
- `tests/captured-output-custody/invalid/cold-finding-missing-human-adjudication/`
- `tests/captured-output-custody/invalid/cold-finding-duplicated-human-adjudication/`
- `tests/captured-output-custody/valid/cold-gpt56-comprehension-and-coverage-pass/`
- `tests/captured-output-custody/invalid/cold-review-prior-context-supplied/`
- `tests/captured-output-custody/invalid/cold-review-grades-before-comprehension/`
- `tests/captured-output-custody/invalid/cold-review-invalid-called-candidate-fail/`
- `tests/captured-output-custody/invalid/cold-human-disagreement-called-complete/`
- `tests/captured-output-custody/valid/cold-challenge-answered-with-hash-bound-evidence/`
- `tests/captured-output-custody/valid/reviewer-transport-invalid-retried-with-lineage/`
- `tests/captured-output-custody/valid/reviewer-transport-retry-same-packet-hash/`
- `tests/captured-output-custody/valid/packet-insufficiency-rebuilt-with-delta-lineage/`
- `tests/captured-output-custody/valid/shared-review-protocol-change-reviews-entire-cohort/`
- `tests/captured-output-custody/invalid/review-invalid-favorable-attempt-selected/`
- `tests/captured-output-custody/invalid/review-retry-before-owner-incident-notification/`
- `tests/captured-output-custody/invalid/rebuilt-packet-changes-candidate-output/`
- `tests/captured-output-custody/invalid/shared-review-protocol-change-retries-one-case/`
- `tests/captured-output-custody/invalid/cold-challenge-answered-with-rationale-only/`
- `tests/captured-output-custody/invalid/cold-challenge-answer-evidence-target-mismatch/`
- `tests/captured-output-custody/invalid/candidate-intelligibility-retried-as-reviewer-failure/`
- `tests/captured-output-custody/invalid/patch-owner-overturn-without-second-human-review/`
- `tests/captured-output-custody/invalid/second-reviewer-not-independent-of-patch-owner/`
- `tests/captured-output-custody/valid/reviewer-transport-invalid-with-predecessor-lineage/`
- `tests/captured-output-custody/invalid/review-invalid-cause-missing-attempt-lineage/`
- `tests/captured-output-custody/invalid/human-adjudication-waives-structural-failure/`
- `docs/captured-output-custody.md`

### Modify

- `tools/verify_candidate_output.py`: emit machine-readable per-checker details and accept an optional `--json-out`; retain single-output positional behavior and structural-only boundary.
- `tools/build_model_compliance_scorecard.py`: consume custody manifests or clearly remain an aggregate fixture runner; do not silently infer provenance.
- `docs/model-compliance-scorecard.md`: reconcile the stale “future runner” wording with the existing tool.
- `docs/non-claims.md`: add causal and custody non-claims.
- `tools/run_local_ci.py` and `tools/ci_registry.json`: add only deterministic schema/checker self-tests, never live model runs.

### Do not modify for this plan

- `atomics/skill/**`: no model-visible law is needed to establish evidence custody.
- `skill/**`: generated and out of scope.
- Existing retained outputs: never rewrite raw evidence to make it pass.

## Implementation Phases

### Phase 0: Preserve baseline

1. Assert branch and clean state.
2. Hash the existing captured specimen and prior local outputs.
3. Replay the existing verifier and store command output outside tracked source until the custody directory is approved.
4. Record that the current specimen has incomplete provenance instead of manufacturing missing fields.

Smoke A:

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
$root = 'C:\Users\theis\Documents\Codex\2026-07-08\dae'
git -C $repo status --short --branch --untracked-files=all
git -C $repo rev-parse HEAD
Get-FileHash -Algorithm SHA256 -LiteralPath "$root\work\grok-v46-output.md"
Set-Location $repo
python tools\verify_candidate_output.py "$root\work\grok-v46-output.md"
```

Expected: clean branch at planned head; existing output hash reproduced; verifier exits nonzero. The exact failing checker set is retained as baseline, not assumed forever.

STOP if the output hash has drifted or the raw artifact was rewritten.

### Phase 1: Test-drive custody schemas

1. Add valid and invalid fixture directories first.
2. Write expected diagnostics for missing hash, self-attested package, changed
   control, status overclaim, missing initial human assessment, cold-finding set
   mismatch, evidence-free answer, invalid-review lineage, and required second
   review.
3. Implement custody, topology-review, and cold-review checkers that recompute
   every local file hash and enforce enum/transition/set-equality rules.
4. Ensure paths are relative to the manifest directory and cannot escape it.

Smoke B:

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
python tools\check_captured_output_manifest.py --self-test
python tools\check_captured_output_manifest.py --root tests\captured-output-custody
python tools\check_topology_review.py --self-test
python tools\check_cold_comprehensiveness_review.py --self-test
```

Expected: all four commands exit 0 because valid fixtures pass and registered invalid fixtures fail with their expected class.

The topology-review self-test specifically proves that PASS is rejected for a
missing/pre-disclosure initial assessment, a cold-finding/adjudication set
mismatch, an `answered` challenge without hash-bound target evidence, a
candidate-intelligibility retry mislabeled as transport failure, and a
patch-owner material reversal without an affirming second independent review.

Right-reason negative after implementation:

```powershell
$manifest = 'tests\captured-output-custody\invalid\missing-input-hash\capture-manifest.json'
$raw = python tools\check_captured_output_manifest.py --explain --manifest $manifest
$exit = $LASTEXITCODE
$diag = $raw | ConvertFrom-Json
if ($exit -ne 1) { throw "expected structural rejection exit 1, got $exit" }
if ($diag.failure_class -ne 'evidence-custody-missing-input-hash') { throw "wrong failure class: $($diag.failure_class)" }
if ($diag.manifest_path -ne $manifest) { throw 'diagnostic is not bound to the tested manifest' }
```

The exact class is pinned in the fixture's A11-compatible canonical expectation once the validation registry lands. A missing-hash fixture rejected for some later output/checker defect does not satisfy Smoke A.

Canonical Smoke A acceptance command:

```powershell
python tools\assert_expected_rejection.py --expectation tests\captured-output-custody\invalid\missing-input-hash\capture-manifest.expectation.json --artifact-root auto
```

Expected: exit `0`; the helper additionally pins the `preflight` custody boundary, exact downstream invalidation, and absence of verifier/promotion artifacts.

Rollback: remove the new schema/checker/fixtures together. Never leave a schema without a validating consumer.

### Phase 2: Machine-readable verifier verdict

1. Extend `verify_candidate_output.py` without changing its default human-readable exit behavior.
2. Record checker command, exit code, stdout/stderr SHA-256, and ordered first failure.
3. Bind verdict to output SHA-256 and verifier source commit.
4. Test that changing the output after verdict creation invalidates custody.

Smoke B:

```powershell
python tools\verify_candidate_output.py --self-test
python tools\build_captured_output_verdict.py --self-test
python tools\check_captured_output_manifest.py --root tests\captured-output-custody
```

Expected: exit 0; mutation of fixture output without manifest/verdict update is rejected.

### Phase 3: Controlled three-way protocol

This phase prepares files and instructions only. It does not run a model without explicit authorization.

1. Store exact smoke input once and hash it.
2. Produce v45, inherited-main, PR8-head/PR9-base, and PR9-head packages from pinned sources or use owner-supplied immutable archives; record all hashes. If the PR9-base package cannot be built, record that artifact gate and do not attribute a v45/head difference specifically to PR9.
3. Pre-register model/host/settings and run order.
4. Run at least one fresh-session lineage set only when authorized. A minimum PR9-causal set is PR9-base plus PR9-head; a full decomposition adds v45 and inherited-main. Alternate order across replicates; do not always run the same variant last.
5. Preserve every result, including failure, refusal, truncation, or infrastructure error.
6. Do not retry a failed response under a different policy and call it the same replicate.
7. Apply the same structural battery and independent topology rubric to both.

Owner gate required for: model spend, host use, package installation, and retention of third-party output.

### Phase 4: Causal decision

Use the comparison schema mechanically, then perform an owner review.

Decision questions:

1. Were input bytes identical in all cells?
2. Were package bytes and source commits independently verified?
3. Were all feasible execution controls equal?
4. Did the same predeclared checker/rubric judge all outputs?
5. Does PR9-base to PR9-head isolate the same direction seen in the release-line comparison, and does the inherited-main to PR8-head cell distinguish hardening-layer behavior?
6. Is the difference topology/depth related rather than merely wording or length?
7. Does repetition preserve the direction?

If any answer is unknown, do not advance beyond `unproven` or `confounded`.

## Five-Smoke Integration

Every fresh smoke capture must produce:

```text
input.txt
capture-manifest.json
output.md
verifier-verdict.json
topology-review.json
cold-review-packet-manifest.json
cold-comprehensiveness-review.json
stage-records/
package-build-manifest.json or immutable external package reference
```

The five required case IDs are:

- `gate88-secularism`
- `gate88-khaybar`
- `gate88-trinitarian-j173`
- `gate88-tst-lillard`
- `gate88-torah-quran-source-authentication`

The fifth case must use the exact owner-supplied prompt. Its custody manifest must not contain expected burdens, expected submove counts, expected output bytes, or expected theological conclusions.

All five final completion rows require both review lanes. GPT-5.6 performs the cold comprehension/comprehensiveness review from a fresh context. A human performs the independent substantive review and issue-level adjudication. Either lane may register an ANDON. Any such ANDON fails the whole candidate cycle and enters the A14/A16 convergence loop; no earlier passing case is carried forward.

## Rollback and Evidence Preservation

- Checker/schema changes may be reverted normally.
- Raw captures, manifests, and verdicts are append-only evidence. If a fixture is invalid, mark it superseded with a new manifest; do not rewrite it.
- A privacy or licensing concern moves a capture to owner-controlled external custody and leaves a hash/reference record. It does not justify a fabricated minimized equivalent.
- If a minimized synthetic fixture is created, label it synthetic and do not claim it is equivalent to the original without a documented preservation test.

## STOP / ANDON Conditions

Stop and record a terminal handoff if:

- exact package bytes cannot be obtained;
- an output self-attests to package identity but no external binding exists;
- v45 and v46 runs use different models or hidden session state;
- output truncation differs between variants;
- an operator retries only one variant;
- a raw output is normalized or repaired before capture;
- a structural verdict is described as semantic truth;
- a cold reviewer receives prior conversation, an expected topology, or an answer bank;
- a cold review grades without first passing the comprehension gate;
- `REVIEW_INVALID` is used to shop for a favorable verdict or is relabeled candidate PASS/FAIL without human classification;
- the independent human initial-assessment hash was not claimed before cold
  review disclosure, or it changes afterward;
- cold finding IDs and final human challenge adjudications are not exact-set
  equal;
- a non-`not_applicable` invalid-review classification omits cause, attempt hash,
  or predecessor lineage;
- a human adjudication waives a structural failure or leaves a material challenge unresolved under PASS;
- an `answered` material challenge lacks new hash-bound evidence for the exact
  challenged IDs;
- a patch owner overturns a material finding without the required second
  independent human review;
- any tool promotes `regression_status` beyond the allowed evidence transition;
- issue filing, package release, or external publication is attempted without authorization.

ANDON record fields:

```yaml
status: BLOCKED | DEFERRED | UNVERIFIED
class: evidence-custody | comparison-confounder | artifact-drift | claim-overreach
failing_check: <exact command or human gate>
owner_source: <file/tool/operator>
next_action: <one concrete action>
preserved_artifacts: [<paths and hashes>]
```

## Definition of Done

- Custody schema and checker have valid/invalid fixture coverage.
- Machine verdict binds output, checker results, and source commit.
- Cold GPT-5.6 review and human review are separate hash-bound evidence lanes with right-reason fixtures.
- The human initial assessment is immutable and hash-bound before cold-review
  disclosure; the checker validates disclosure and attempt lineage.
- The cold-review comprehension gate distinguishes invalid review from candidate intelligibility failure without reviewer shopping.
- Cold challenges have an executable `upheld | answered | unresolved` state
  machine; only evidence-backed `answered` is PASS-eligible, and patch-owner
  reversals require a hash-bound affirming second independent human review.
- Reviewer or human ANDONs re-enter the full five-smoke candidate-repair loop.
- Existing invalid specimen is represented truthfully as incomplete-provenance evidence.
- No current report or scorecard promotes it to v46 regression proof.
- An authorized same-fixture three-way set can be captured without procedural ambiguity.
- `regression_status` remains `unproven` until the comparison gate actually runs.
- All deterministic tests pass and raw evidence remains unchanged.

## Confidence

Repo-local custody implementation: YES, implementation-ready after owner authorization.  
Controlled model comparison: PARTIAL, owner/artifact/spend gated.  
v46 regression conclusion: NO, still unproven.
