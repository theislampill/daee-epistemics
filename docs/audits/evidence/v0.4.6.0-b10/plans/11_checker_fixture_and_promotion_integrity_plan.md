# ANDON A11: Checker, Fixture, and Promotion Integrity

Priority: P0/P1 structural-integrity and evidence-promotion fix  
Implementation target: PR #9 branch at planned head `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Regression status: `unproven`  
Plan status: implementation-ready after owner authorization  
Scope: deterministic repo tooling only; no model invocation, issue filing, package publication, commit, push, tag, or release

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Plain-Language Summary

The repository has many useful checkers, fixtures, a first-failed-stage classifier, a candidate-output wrapper, and a scorecard. The abnormality is not that these controls are absent. It is that several control surfaces can say "rejected" or "PASS" without proving the precise thing their surrounding prose claims:

1. The mutation sweep currently counts any nonzero checker exit as a successful rejection. It records an expected stage and expected failure hint, but never compares them with the checker's structured first-failure result.
2. The stage workbench's `expected.*.json` files are documentary. The workbench README explicitly says the checker does not consume them.
3. At least one checked-in Stage07 invalid fixture is rejected first at Stage04. That is useful evidence that the record is invalid, but it is not evidence that the intended Stage07 defect was caught for the right reason.
4. Stage07, the post-hoc candidate verifier, and the scorecard each hard-code different checker lists. A green result therefore means "green under this list," not "green under the release list."
5. The candidate verifier is not hash-bound to the input, package, handoff record, sidecars, or checker registry. It cannot serve as a promotion verdict by itself.
6. The scorecard document describes its runner as future work even though the runner exists, and the documented `capture_meta` fields do not match the emitted fields.

The intended repair is to make every negative test prove the expected earliest stage, expected failure class, expected checker, expected diagnostic marker, and expected exit category. A single checker registry will then define Stage07, captured-output, and promotion profiles. Promotion will emit a hash-bound verdict that says exactly what ran, what did not run, and what its structural result means.

## Evidence Boundary

### Confirmed by direct GEMBA

- `tools/gen_fixture_mutations.py:594-598` invokes the handshake checker without `--explain-stage-failure` and sets `verdict = "rejected"` for every nonzero exit.
- `stage_record_self_test()` checks only `verdict == "rejected"` and nonzero exit. It does not compare `expected_stage`, `expected_class_hint`, or `expected_checker` with observed diagnostics.
- `tools/check_staged_runtime_handshake.py` already has a stable structured explanation surface. Its current fields are `stage`, `failure_class`, `earliest_stage`, `downstream_invalidated`, `requires_model_rerun`, and `repair_lane`.
- Current stable failure classes include `custody`, `burden-floor`, `owner-route`, `act_body_ref`, `mrp`, `field_witness`, `public-projection`, `sidecar`, `handoff`, `sequence`, `non-claim`, and `unclassified`.
- `tests/stage-contract-workbench/README.md:35-40` says `expected.*.json` files are documentation/anti-drift pins and are not consumed by the checker.
- The current sidecar for `stage-04-burden-execution-act/invalid/act-row-missing-land.json` claims Stage04 in a documentary schema. Direct `--explain-stage-failure` returned exit `1`, `earliest_stage: "04"`, and `failure_class: "act_body_ref"`.
- The current sidecar for `stage-07-release-output/invalid/slim-public-output-below-structural-minimum.json` claims Stage07 as the intended signature and admits that the fixture is `composite-historical`.
- Direct explanation of that Stage07 fixture returned exit `1`, but its actual earliest failure was `earliest_stage: "04"`, `failure_class: "act_body_ref"`. This is the exact wrong-reason false confidence this plan addresses.
- `tools/verify_candidate_output.py` runs six output-facing checkers and adds no detection logic.
- `run_release_validators()` in `tools/run_staged_current_skill_smoke.py` runs a different ten-checker Stage07 list, plus in-process visible-output validation and Stage05-to-public MRP parity.
- `tools/build_model_compliance_scorecard.py` has six runnable output detectors and two `NOT-RUN` record/manifest detectors. It does not consume the candidate verifier or Stage07 registry.
- The verifier and scorecard self-tests both currently pass. Those self-tests validate aggregation and mapping shape, not fixture-level right-reason rejection or battery parity.
- The retained `a9-science-source/output.md` currently passes the six-checker candidate verifier. That proves only acceptance by those six checkers.
- `verify_candidate_output.py` explicitly disclaims semantic truth, provenance, uptake, and live in-host enforcement.
- The current branch's no-model preflight is green. This plan preserves that control and extends its proof scope; it does not erase or relabel it.

### Planning-time command observations

The following commands were run read-only during planning:

```text
python tools\verify_candidate_output.py --self-test
  -> exit 0

python tools\build_model_compliance_scorecard.py --self-test
  -> exit 0

python tools\check_staged_runtime_handshake.py --explain-stage-failure --records tests\stage-contract-workbench\stage-04-burden-execution-act\invalid\act-row-missing-land.json
  -> exit 1; earliest_stage=04; failure_class=act_body_ref

python tools\check_staged_runtime_handshake.py --explain-stage-failure --records tests\stage-contract-workbench\stage-07-release-output\invalid\slim-public-output-below-structural-minimum.json
  -> exit 1; earliest_stage=04; failure_class=act_body_ref

python tools\verify_candidate_output.py tests\retained-proof-corpus\v0.4.3.0-schema-light\valid\sidecar-backed\cases\a9-science-source\output.md
  -> exit 0; PASS under six structural checkers
```

One bounded planning invocation of `python tools\gen_fixture_mutations.py --self-test` was terminated by the command host after approximately 124 seconds. It produced no terminal result and is non-evidence. The primary audit later ran `python tools\run_no_model_preflight.py` with a 900-second allowance; its mutation-sweep gate passed and the composed command exited `0` after 370.2 seconds. That later result is the controlling baseline, while the short-timeout invocation remains non-evidence.

### Inferred

- Independent hard-coded batteries are likely to continue drifting as new checkers land.
- A mutation can fail due to an unrelated upstream defect while the intended downstream checker remains ineffective.
- A green aggregate can conceal `NOT-RUN`, unavailable, usage-error, or infrastructure-error states if those states are represented only as a generic boolean.

### Unproven

- That any current verifier PASS establishes semantic completeness.
- That the current Grok specimen's failure was caused by PR #9.
- That every current checker belongs in every profile.
- That every output-capable checker is universally applicable to every governed output mode.
- That a fixed output size, burden count, or submove count would repair checker integrity.

## Exact Abnormality and False-Pass Model

### False-pass class 1: any nonzero counts as success

Current mutation logic reduces subprocess results to:

```text
return code == 0  -> survivor
return code != 0  -> rejected
```

This collapses at least five materially different outcomes:

| Outcome | Meaning | May count as right-reason rejection? |
| --- | --- | --- |
| Exit 0 | Mutant survived | No |
| Exit 1 plus expected diagnostic | Intended structural contract rejected the mutant | Yes |
| Exit 1 plus different earlier diagnostic | Artifact is invalid, but intended control is unproven | No |
| Exit 2 usage/path/argument error | Test harness did not exercise the checker | No |
| Process crash, timeout, import error, or signal | Infrastructure abnormality | No |

The target system must preserve all five states.

### False-pass class 2: documentary expectation is not an assertion

The workbench sidecar:

```json
{
  "stage": "stage-07-release-output",
  "failure_class_hint": "stage-07 output missing required structural sections",
  "checker": "check_staged_runtime_handshake"
}
```

does not constrain current execution. The checker reports Stage04 first for the named fixture. The sidecar and result can disagree indefinitely while both files remain green under their separate checks.

### False-pass class 3: battery-local PASS

The current lists are not interchangeable:

| Surface | Current scope |
| --- | --- |
| Stage07 runner | Ten subprocess validators, visible-output validation, and MRP record/surface parity |
| Candidate verifier | Six output-only validators |
| Scorecard | Six runnable output detectors plus two `NOT-RUN` rows |
| Stage08 | Selected reruns, sidecar builders, B5 eligibility, handoff validation, and capsule replay |

A candidate-verifier PASS cannot be promoted into a Stage07/Stage08 PASS because the required evidence sets differ.

### False-pass class 4: unbound promotion

The current candidate verifier records no:

- output SHA-256;
- input SHA-256;
- package SHA-256 or source commit;
- handoff-record SHA-256;
- state-capsule or prompt-context evidence;
- checker-registry hash;
- checker source hash;
- stdout/stderr hash;
- first failure class;
- unavailable/usage/infrastructure distinction;
- signed topology review.

It is therefore a useful local replay wrapper, not a promotion artifact.

## Architectural Requirement

DAEE's formal pipeline is:

```text
𝓝 ⊢ D₀
  → ⇝ Ψᴺ⟨N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩
  → IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)
  → ∇_route
  → ⁿB
  → {ⁿBᵢ[OPᵢ]}
  → Land(ⁿB)
  → ΔⁿB{♥,ξ,Ω,σ,μ}/Δκ
  → ∇·T/∇×T
  → LoopBreak(∇×T)
  → R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)
  → 𝒞(Ψᴺ)
  → N_fiṭrī ∧ ʿaql ṣarīḥ
  → T_lang: Ψᴺ ⇢ Ψᴵ
```

Checker integrity is the evidence-control plane around this whole chain. A negative fixture must identify the earliest transition it intentionally breaks. A promotion verdict must prove that every required structural control applicable to the captured artifact ran against hash-bound inputs. It may not claim the theological truth of the result, the correctness of an unobservable semantic judgment, or actual interlocutor uptake.

The OSM paper contributes only a bounded engineering caution: endpoint agreement does not establish trajectory agreement. Here, a final nonzero exit is an endpoint. Right-reason stage/class evidence is the trajectory needed to know which control actually acted.

## Five Whys

1. **Why can a mutation sweep report success while the intended checker remains unproven?**  
   Because `gen_fixture_mutations.py` treats every nonzero return code as `rejected` and does not compare the observed structured diagnostic with the expectation metadata.

2. **Why is expectation metadata not compared?**  
   The mutation sweep predates or was not integrated with the later `--explain-stage-failure` classifier. Its metadata remained descriptive while its executor retained boolean exit semantics.

3. **Why can an invalid fixture fail at the wrong stage without stopping CI?**  
   The workbench expectation sidecars are explicitly non-enforcing, and composite fixtures may carry unrelated upstream defects. The base invalid loop only asks whether some error exists.

4. **Why do Stage07, candidate verification, and scorecarding disagree about what must run?**  
   Each tool owns a separate hard-coded detector list. No source of truth classifies artifact requirements, invocation arguments, applicability, or promotion role.

5. **Why can a green aggregate be mistaken for release evidence?**  
   The aggregate is not hash-bound to custody artifacts or the registry version, and its boolean vocabulary does not distinguish accepted, rejected, not applicable, not run, usage error, and infrastructure error.

**Actionable root owner/source:** deterministic validation orchestration, principally `tools/gen_fixture_mutations.py`, `tools/check_staged_runtime_handshake.py`, the independent validator lists in `tools/run_staged_current_skill_smoke.py`, `tools/verify_candidate_output.py`, and `tools/build_model_compliance_scorecard.py`, plus their fixture and documentation contracts.

This root cause is not a claim about model behavior or PR #9 regression causality.

## Hansei

### What worked

- The repository already has many precise positive and negative fixtures.
- `--explain-stage-failure` already gives a structured earliest-stage result.
- The checker's expected-explain sidecars already enforce exact diagnostics for its canonical invalid fixture directory.
- The mutation sweep records operator identity, intended stage, intended checker, and known-gap state.
- The Stage07 runner already stops on validator failure.
- The candidate verifier explicitly states its narrow structural boundary.
- The scorecard already uses `NOT-RUN` instead of pretending record-only checks ran over Markdown.

### What failed

- Existing structured diagnostics were not joined to mutation expectations.
- Composite historical fixtures were allowed to stand in for single-signature right-reason fixtures.
- Checker lists became copied policy instead of profile projections from one registry.
- The candidate verifier's six-checker PASS was easy to read as broader than it is.
- The scorecard documentation and implementation drifted immediately after the runner landed.
- Prior plans named unsupported wildcard commands or flags instead of checking current CLIs.

### Lesson

The control must prove its own route. "Something rejected this" is not enough. The durable unit of evidence is:

```text
artifact hash
+ exact checker identity and source
+ expected applicability
+ observed exit category
+ observed earliest stage and failure class
+ diagnostic evidence
+ registry/profile identity
```

## Existing Controls to Reuse

This plan must extend, not replace, these controls:

- `check_staged_runtime_handshake.py --explain-stage-failure` and its stable class vocabulary.
- Existing `.expected-explain.json` fixtures under `tests/staged-runtime-handshake/`.
- Existing workbench minimal-valid, maximal-valid, and invalid organization.
- `KNOWN_CHECKER_GAPS` as a visible, owner-reviewed exception list, but only with expiry metadata and no promotion PASS.
- `run_release_validators()` Stage07 stop behavior.
- Candidate-verifier single-file CLI and structural-only non-claim.
- Scorecard offline/no-model behavior.
- `tools/ci_registry.json` and `tools/run_local_ci.py` required-check wiring.
- Plan 01's future captured-output custody manifest and comparison manifest.
- Raw fixture and captured-output immutability.

## Target Contract 1: Right-Reason Mutation Verdict

Every mutation operator must declare an executable expectation:

```json
{
  "operator": "corrupt-body_ref",
  "artifact_kind": "staged-handoff-record",
  "source_fixture": "tests/staged-runtime-handshake/valid/retained-a9-science-source.json",
  "target_stage": "04",
  "expected_checker_id": "staged-runtime-handshake",
  "expected_exit_category": "structural-rejection",
  "expected_exit_code": 1,
  "expected_earliest_stage": "04",
  "expected_failure_class": "act_body_ref",
  "required_diagnostic_markers": ["body_ref"],
  "rebinding_policy": "not-applicable"
}
```

Required rules:

1. Exit `1` counts only when the expected checker, earliest stage, failure class, and required marker all match.
2. Exit `0` is `survived`.
3. Exit `2` is `usage-error`, never rejection.
4. Timeout, signal, import failure, malformed JSON output, or missing executable is `infrastructure-error`.
5. A different exit-1 diagnostic is `rejected-wrong-reason`.
6. `rejected-wrong-reason` fails the mutation suite even though the artifact is invalid.
7. `known-gap` remains a failing promotion condition. It may make a diagnostic audit complete, but never make a release profile PASS.
8. The mutation must differ from its source and must not rewrite the source fixture.
9. Mutants are generated in a unique temporary directory and are hash-recorded.
10. Render mutations must mutate a real copied output and choose a rebinding policy explicitly.

### Rebinding policy

Rendered-artifact mutations need to prevent custody errors from masking the intended render error:

| Policy | Use |
| --- | --- |
| `preserve-binding-to-test-custody` | Deliberately mutate bytes without updating hash when the expected failure is custody/hash mismatch |
| `recompute-binding-to-test-content` | Update copied record path/hash so custody passes and the intended content checker sees the mutation |
| `not-applicable` | Record-only mutation with no external artifact binding |

The `slim-public-while-sidecar-rich` operator must use `recompute-binding-to-test-content`, invoke the registered Stage07 render profile, and fail first as Stage07/public projection. A Stage04 failure is not acceptable evidence for that operator.

## Target Contract 2: Enforced Expectation Sidecars

Do not continue two incompatible expectation dialects.

The canonical negative expectation schema becomes `daee-negative-fixture-expectation-v1`:

```json
{
  "schema": "daee-negative-fixture-expectation-v1",
  "fixture": "slim-public-output-below-structural-minimum.json",
  "kind": "invalid-single-signature",
  "expected_checker_id": "staged-runtime-handshake",
  "expected_exit_category": "structural-rejection",
  "expected_exit_code": 1,
  "expected_earliest_stage": "07",
  "expected_failure_class": "public-projection",
  "expected_failure_subcode": "slim-public-while-sidecar-rich",
  "expected_downstream_invalidated": ["08"],
  "required_diagnostic_markers": ["stage-07", "release output"],
  "forbidden_artifacts": ["stage08-record.json", "promotion-verdict.json"],
  "provenance": "slim-public-while-sidecar-rich"
}
```

Migration rules:

- Existing `tests/staged-runtime-handshake/invalid/*.expected-explain.json` remain authoritative for the handshake suite and are accepted through an adapter.
- Every new active invalid fixture uses one companion `<fixture-stem>.expectation.json` encoded as `daee-negative-fixture-expectation-v1`.
- Workbench `expected.<name>.json` files migrate to `<fixture-stem>.expectation.json` and become executable.
- Composite historical fixtures remain retained but move to `tests/stage-contract-workbench/historical-composite/` and are excluded from right-reason coverage counts.
- Every active invalid fixture must have exactly one executable expectation.
- Every active valid fixture must produce `{"status":"pass"}` from the relevant profile.
- An expectation with `failure_class_hint` but no exact class is legacy and cannot satisfy promotion.
- Release-bearing expectations require exact `expected_downstream_invalidated` and `forbidden_artifacts`. Stage-local fixtures may use empty arrays, but may not omit the fields and thereby avoid a boundary assertion.
- `expected_earliest_stage` uses `01` through `08` for staged artifacts and the controlled values `preflight`, `control-plane`, `candidate-package`, or `release-action` for non-stage control artifacts. Non-stage expectations still require exact downstream/forbidden artifact arrays; an empty array must be deliberate, not omitted.

Add one canonical assertion wrapper, `tools/assert_expected_rejection.py`. Given an expectation sidecar and an isolated artifact root, it resolves the registered checker and validates all of the following as one atomic verdict: exact exit category/code, earliest stage, failure class and optional subcode, exact `downstream_invalidated`, required diagnostic markers, and absence of every `forbidden_artifacts` path. `--artifact-root auto` creates a unique helper-owned scratch/custody directory outside the checked-in fixture tree, records its path in the verdict, removes it on a clean pass only after the forbidden-artifact inventory is hashed, and preserves it on any wrong-reason/infrastructure failure. Before cleanup it resolves the absolute path, requires a helper-owned marker, rejects symlinks/junctions/reparse escapes, and proves the root remains under the designated temp/custody parent. It returns zero only when the fixture was rejected for the intended reason and no downstream or promotional artifact escaped the failed boundary. Individual plans may show direct assertions for clarity, but active CI/right-reason coverage calls this helper rather than copying weaker partial wrappers.

## Target Contract 3: One Validation Registry, Several Honest Profiles

Add `tools/validation_registry.py` as the canonical executable registry. It owns metadata and argument templates; it does not reimplement checker logic.

Each `CheckerSpec` records:

```text
checker_id
tool_path or in-process adapter
artifact_kinds
command arguments by artifact kind
earliest owning stage
failure-shape labels
applicability predicate
profiles
required inputs
structural-only non-claims
```

Required artifact kinds:

- `output-md`
- `input-output-pair`
- `staged-handoff-record`
- `state-capsule-sequence`
- `prompt-context-manifest`
- `proof-sidecar-set`
- `retained-case-manifest`
- `captured-output-custody-manifest`

Required profiles:

| Profile | Purpose | Missing prerequisite behavior |
| --- | --- | --- |
| `stage07-release` | Current release-output validation | Hard fail |
| `captured-output-structural` | Every applicable output-only checker over one captured Markdown file | Required checker cannot become `NOT-RUN`; hard fail |
| `stage08-proof-surface` | Record, output, capsule, and sidecar joins | Hard fail |
| `promotion` | Custody-bound superset of all required profiles | Quarantine, no PASS |
| `scorecard` | Reporting projection of an existing verdict | Never silently rerun a different battery |
| `advisory` | Non-promotion diagnostics | May warn; cannot satisfy a required row |

### Registry coverage law

`tools/check_validation_registry.py` must:

1. Discover current `check_*.py` tools that advertise `--outputs` and require each to be classified as required, advisory, mode-specific, or inapplicable with a basis.
2. Parse the Stage07 validator call sites and fail if an invoked checker is absent from the registry.
3. Fail if `verify_candidate_output.py` or `build_model_compliance_scorecard.py` declares a private detector list.
4. Fail if a profile references a missing tool or unsupported argument.
5. Fail if a required checker is registered as `NOT-RUN` for the artifact set needed by that profile.
6. Emit the registry SHA-256 used by every verdict.
7. Cross-check `tools/ci_registry.json`: registry and registry-coverage self-tests must be in required local CI.

Not every `--outputs` tool must become universally required. The mandatory engineering act is explicit classification, not blind inclusion.

## Target Contract 4: Structured Checker-Run Result

Every registry invocation emits or is adapted into:

```json
{
  "checker_id": "manual-smoke-render-contract",
  "tool_path": "tools/check_manual_smoke_render_contract.py",
  "tool_sha256": "64-lowercase-hex",
  "artifact_kind": "output-md",
  "artifact_sha256": "64-lowercase-hex",
  "execution_status": "completed",
  "structural_result": "accepted",
  "exit_code": 0,
  "failure_class": null,
  "earliest_stage": "07",
  "stdout_sha256": "64-lowercase-hex",
  "stderr_sha256": "64-lowercase-hex",
  "duration_ms": 1,
  "non_claims": ["structural acceptance only"]
}
```

Controlled vocabularies:

```text
execution_status:
  completed
  not-run
  usage-error
  timeout
  crashed
  unavailable

structural_result:
  accepted
  rejected
  not-applicable
  indeterminate
```

Only `completed + accepted` satisfies a required positive check. Only `completed + rejected` with the expected diagnostic satisfies a negative right-reason fixture. No other combination is silently coerced.

## Target Contract 5: Hash-Bound Promotion Verdict

Add `schema/checker-replay-verdict.schema.json`. The verdict binds:

- verdict schema version;
- validation registry SHA-256;
- source commit;
- custody manifest path and SHA-256;
- input path and SHA-256;
- output path and SHA-256;
- package/build-manifest identity when available;
- staged handoff path and SHA-256 when available;
- capsule/context/sidecar identities when available;
- selected profile;
- ordered checker results;
- first failed checker and first failed stage/class;
- aggregate status;
- explicit missing prerequisites;
- structural-only non-claims.

Aggregate status vocabulary:

```text
PASS_STRUCTURAL
FAIL_STRUCTURAL
QUARANTINED_INCOMPLETE_EVIDENCE
INFRASTRUCTURE_ERROR
NOT_RUN
```

Promotion rules:

- `PASS_STRUCTURAL` requires every required checker to be `completed + accepted` and every required artifact binding to verify.
- A required `not-run`, `not-applicable`, unavailable tool, hash mismatch, or missing sidecar yields `QUARANTINED_INCOMPLETE_EVIDENCE`, not PASS.
- A checker rejection yields `FAIL_STRUCTURAL`.
- A crash, timeout, or usage error yields `INFRASTRUCTURE_ERROR` unless an earlier genuine structural rejection is already hash-bound; both facts remain recorded.
- Changing any bound artifact invalidates the verdict.
- Structural PASS does not set semantic review to PASS and does not alter `regression_status`.

Plan 01's custody manifest is the provenance owner. This plan owns checker/profile integrity and the replay verdict. The two schemas join by hash and do not duplicate runtime/package fields.

## Target Contract 6: Scorecard v2 Without Semantic Ambiguity

Preserve `model-compliance-scorecard-v1` as a readable legacy format. Add `model-compliance-scorecard-v2` for promotion reporting.

V2 is a projection of hash-bound verdicts. It must not discover Markdown recursively and independently rerun a private list.

Per-case row:

```json
{
  "case_id": "gate88-secularism",
  "input_sha256": "64-lowercase-hex",
  "output_sha256": "64-lowercase-hex",
  "verdict_sha256": "64-lowercase-hex",
  "registry_sha256": "64-lowercase-hex",
  "structural_status": "PASS_STRUCTURAL",
  "required_checks": 0,
  "accepted_checks": 0,
  "rejected_checks": 0,
  "not_run_checks": 0,
  "topology_review_ref": null,
  "topology_review_status": "NOT_REVIEWED",
  "semantic_truth_status": "NOT_CLAIMED"
}
```

When reviewed, `topology_review_ref` is the path/hash/verdict projection of Plan A01's `daee-topology-review-v1`; the scorecard never accepts an unbound scalar as review evidence. Do not use one ambiguous `PASS/FAIL` field to mean both "defect detected" and "checker passed." Each detailed row carries `execution_status` and `structural_result`.

Documentation must be corrected in the same patch:

- remove the claim that the runner is future work;
- match actual emitted `capture_meta` fields;
- document v1 legacy behavior and v2 verdict projection;
- state that `NOT-RUN` cannot satisfy promotion;
- state that a scorecard cannot prove semantic truth, provenance beyond its bound manifest, uptake, cross-host behavior, or regression causality.

## Target Contract 7: Model-Smoke Escape Prevention

The owner reports that predecessor four-smoke repair campaigns sometimes spent
dozens of full model invocations locating small failures. A deterministic defect
first exposed by a paid smoke is therefore two abnormalities at once:

1. the product ANDON in the runtime trajectory; and
2. a `MODEL_SMOKE_ESCAPE` showing that the pre-model control system failed to
   detect or localize a reproducible defect cheaply.

Add an append-only `model-smoke-escape-v1` registry. Every row binds the failed
cycle/candidate/case, first observed gate, product ANDON IDs, raw evidence hashes,
deterministic-detectability decision, causal explanation, checker/fixture owner,
red-old and green-new evidence, right-reason/mutation evidence, recurrence link,
and model-call accounting. Allowed classifications are:

```text
YES
NO
UNKNOWN
```

`YES` and `UNKNOWN` block another paid five-case
cycle. `YES` closes only after the permanent canary is wired into the required
validation registry/profile and proves all of these:

- the minimized negative fails on the pre-fix boundary for the same earliest
  stage and stable failure class;
- the same fixture passes at the candidate boundary;
- a neighboring valid control remains valid;
- the checker rejects the semantic transition/relation/custody defect, not a
  copied phrase, case ID, topic word, output size, or fixed cardinality;
- identifier renaming, order permutation, neutral paraphrase, and irrelevant
  text insertion do not erase the intended detection;
- deleting or reversing the repaired relation makes the mutation suite fail;
- the canary is included in local CI and the composed no-model maturity gate.

`NO` is not a convenience waiver or permanent immunity. It is scoped to the
inspected source/schema/checker/model protocol and defect signature. The row
must identify the exact IR/artifact boundary, missing topic-neutral observable,
anti-answer-bank basis, strongest compensating observability/review control, and
exact recheck predicates. A recurrence, checker version change, or cross-cycle
similarity may append `REASSESSMENT_DUE`; it cannot mutate `NO` automatically.

`NO -> UNKNOWN` requires an append-only, hash-bound transition event approved
by the accountable escape owner and an independent reviewer, with appropriate
domain authority for a semantic case. The event must present materially new
evidence that a topic-neutral observable may exist without expected answers,
expected topology, topic/case tokens, fixed counts, or copied prose. Once
admitted, `UNKNOWN` blocks the next undispatched paid cycle until the named
current question resolves to `YES` with a CI-wired metamorphic canary or to a
renewed scoped `NO` with updated evidence and compensating review. Speculative
future detectability cannot keep `UNKNOWN` open indefinitely, and model reruns
cannot close it.

A paid cycle after `NO` also requires completed 5 Whys/Hansei, a credible
owner-source countermeasure, the strongest valid topic-neutral observability
canary, Smoke A/B and full deterministic preflight green, and accountable-owner
plus independent-reviewer concurrence. The `NO` label alone is never launch
permission; the successor complete model cycle is residual semantic
verification.

The registry also distinguishes honest savings from invented savings. Count an
invocation as avoided only when a previously intended model cycle was blocked by
a deterministic failure at an exact candidate boundary. Otherwise record
`estimated_model_invocations_avoided: unknown`. Report calls spent, maturity
blocks, escapes, recurrence, and closed permanent canaries. Do not reward a lower
call count obtained by thinning the output, review, or five-case matrix.

## Exact Owner and Edit Map

### Add

- `tools/validation_registry.py`
- `tools/check_validation_registry.py`
- `tools/assert_expected_rejection.py`
- `schema/negative-fixture-expectation.schema.json`
- `schema/checker-replay-verdict.schema.json`
- `schema/model-smoke-escape.schema.json`
- `tools/check_model_smoke_escape_registry.py`
- `tests/model-smoke-escape/registry.json`
- `tests/model-smoke-escape/valid/closed-deterministic-escape/`
- `tests/model-smoke-escape/valid/non-deterministic-with-observability/`
- `tests/model-smoke-escape/valid/scoped-no-with-recheck-predicates/`
- `tests/model-smoke-escape/valid/reassessment-due-without-state-mutation/`
- `tests/model-smoke-escape/valid/adjudicated-no-to-unknown-transition/`
- `tests/model-smoke-escape/valid/renewed-no-after-bounded-reassessment/`
- `tests/model-smoke-escape/invalid/open-yes-offered-as-mature/`
- `tests/model-smoke-escape/invalid/unknown-offered-as-mature/`
- `tests/model-smoke-escape/invalid/green-only-canary/`
- `tests/model-smoke-escape/invalid/topic-or-case-tainted-canary/`
- `tests/model-smoke-escape/invalid/wrong-reason-canary/`
- `tests/model-smoke-escape/invalid/recurring-escape-marked-closed/`
- `tests/model-smoke-escape/invalid/recurrence-automatically-mutates-no-to-unknown/`
- `tests/model-smoke-escape/invalid/unknown-left-open-on-speculative-future-capability/`
- `tests/model-smoke-escape/invalid/no-used-as-launch-waiver-without-countermeasure/`
- `tests/model-smoke-escape/invalid/speculative-calls-avoided/`
- `tests/validation-integrity/valid/right-reason-stage04/`
- `tests/validation-integrity/valid/right-reason-stage07-render/`
- `tests/validation-integrity/invalid/wrong-earliest-stage/`
- `tests/validation-integrity/invalid/wrong-failure-class/`
- `tests/validation-integrity/invalid/usage-error-counted-as-rejection/`
- `tests/validation-integrity/invalid/timeout-counted-as-rejection/`
- `tests/validation-integrity/invalid/unregistered-output-checker/`
- `tests/validation-integrity/invalid/profile-required-not-run/`
- `tests/validation-integrity/invalid/verdict-output-hash-drift/`
- `tests/validation-integrity/invalid/scorecard-private-battery/`
- `docs/validation-registry-and-promotion.md`

### Modify

- `tools/gen_fixture_mutations.py`: invoke structured diagnostics, preserve exit categories, enforce expectations, and perform real artifact-bundle render mutations.
- `tools/assert_expected_rejection.py`: consume only Plan A11 expectation sidecars and the validation registry; reject unknown checker IDs, missing downstream assertions, missing forbidden-artifact declarations for release-bearing fixtures, and malformed diagnostic JSON.
- `tools/check_staged_runtime_handshake.py`: keep current classifier; add only any stable diagnostic IDs needed to avoid message-substring fragility. Do not duplicate mutation orchestration here.
- `tools/run_staged_current_skill_smoke.py`: obtain Stage07 commands/profile from the registry and emit registry/profile identity into Stage07/08 records.
- `tools/verify_candidate_output.py`: retain its single-file default CLI; use the `captured-output-structural` profile; add `--json-out`; bind output and registry hashes; preserve structural-only wording.
- `tools/build_model_compliance_scorecard.py`: preserve v1 read support; add v2 verdict-input mode; remove private detector policy.
- `tests/stage-contract-workbench/README.md`: remove stale operator count and stale fixed Stage01 gap; document enforced expectation semantics.
- `tests/stage-contract-workbench/stage-*/invalid/expected.*.json`: migrate active expectations to the canonical schema.
- `docs/model-compliance-scorecard.md`: align with existing runner and v2 contract.
- `docs/proof-class-taxonomy.md`: name checker profile and hash-bound replay evidence explicitly.
- `docs/non-claims.md`: state registry/profile PASS boundaries.
- `tools/run_local_ci.py`: add registry, expectation, verdict, scorecard, model-smoke
  escape registry, and permanent escape-canary self-tests as required checks.
- `tools/ci_registry.json`: classify the new checkers and permanent escape-canary
  runner as required, with explicit owner and expected diagnostic class.
- `tools/run_no_model_preflight.py`: add a composed validation-integrity gate after the underlying self-tests are stable.
- Plan A16's maturity builder: consume the escape-registry verdict by hash and
  refuse `NO_MODEL_CANDIDATE_MATURE` while a `YES` or `UNKNOWN` row is open.

### Generated or retained files not to hand-edit

- `skill/**`: no runtime-law change is required by this plan; generated files remain untouched.
- Raw retained outputs and captured specimens: never rewrite them to satisfy a checker.
- Existing historical composite fixtures: retain or relocate with history; do not silently normalize them into single-signature evidence.
- Generated docs/index surfaces: regenerate through their owner tool if the documentation build requires it.

### Files explicitly outside this plan

- No theological owner/argument module is added.
- No expected Torah/Qur'an burden topology is added.
- No output byte floor, burden floor, or submove floor is added.
- No live model runner is invoked.
- No issue, package, release, or Git state is published.

## Required Fixture Lattice

### Right-reason valid controls

1. One Stage01 custody mutation rejected at `01/custody`.
2. One Stage02 burden-floor mutation rejected at `02/burden-floor`.
3. One Stage03 route-owner mutation rejected at `03/owner-route`.
4. One Stage04 ACT/body-ref mutation rejected at `04/act_body_ref`.
5. One Stage05 MRP mutation rejected at `05/mrp`.
6. One Stage06 witness mutation rejected at `06/field_witness`.
7. One Stage07 output mutation with Stages01-06 otherwise valid, rejected at `07/public-projection`.
8. One Stage08 sidecar mutation with Stages01-07 otherwise valid, rejected at `08/sidecar`.
9. One cross-stage provenance mutation whose expected earliest contract is explicitly Stage02 even though the mutation also changes Stage05.
10. One custody-hash mutation whose hash is intentionally not rebound and is rejected by custody.
11. One content mutation whose path/hash is recomputed so custody passes and the intended content checker rejects it.
12. One fully valid artifact bundle accepted by every required profile applicable to it.

### Invalid integrity controls

1. Expected Stage07 but observed Stage04.
2. Expected `act_body_ref` but observed `owner-route`.
3. Exit 2 with usage text.
4. Timeout before diagnostic.
5. Checker executable missing.
6. Malformed JSON explanation.
7. Diagnostic class `unclassified`.
8. Required checker `NOT-RUN`.
9. Registry references unsupported CLI flag.
10. Stage07 invokes an unregistered checker.
11. Verifier declares a private `BATTERY` list.
12. Scorecard declares a private `DETECTORS` list.
13. Output changes after verdict creation.
14. Registry changes after verdict creation.
15. Composite fixture offered as single-signature coverage.
16. Known gap offered as promotion PASS.

## Test-Driven Implementation Sequence

### Phase 0: Freeze current evidence and drift boundary

Run from PowerShell:

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
$expectedHead = '6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c'
$status = git -C $repo status --short --branch --untracked-files=all
$head = git -C $repo rev-parse HEAD
if ($head -ne $expectedHead) { throw "STALE PLAN: expected $expectedHead, got $head" }
if (($status | Select-Object -Skip 1).Count -ne 0) { throw "STOP: source worktree is dirty" }
Set-Location $repo
python tools\verify_candidate_output.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'baseline candidate-verifier self-test failed' }
python tools\build_model_compliance_scorecard.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'baseline scorecard self-test failed' }
```

Expected: both existing self-tests exit `0`. This is baseline capability evidence only.

Right-reason baseline:

```powershell
$fixture = 'tests\stage-contract-workbench\stage-07-release-output\invalid\slim-public-output-below-structural-minimum.json'
$raw = & python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $fixture 2>&1
$code = $LASTEXITCODE
$diag = ($raw | Select-Object -Last 1) | ConvertFrom-Json
if ($code -ne 1) { throw "expected structural rejection exit 1, got $code" }
if ($diag.earliest_stage -ne '04') { throw "baseline drift: expected current wrong-reason stage 04, got $($diag.earliest_stage)" }
if ($diag.failure_class -ne 'act_body_ref') { throw "baseline drift: expected current class act_body_ref, got $($diag.failure_class)" }
```

Expected before the fix: exit `1`, earliest stage `04`, class `act_body_ref`. This proves the current Stage07 fixture is not right-reason Stage07 evidence.

STOP if the fixture or diagnostic has changed; update the plan against the new head instead of forcing this baseline.

### Phase 1: Add the validation registry in red/green order

1. Add registry fixture data and a failing coverage test first.
2. Add `validation_registry.py` with current checker metadata and explicit profile membership.
3. Classify every discovered output-capable checker; do not auto-promote by naming convention.
4. Add command-shape validation by invoking each registered tool's supported test path in fixture mode.
5. Wire registry self-tests into local CI only after direct self-test passes.

Commands after the phase:

```powershell
python tools\check_validation_registry.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'validation registry self-test failed' }
python tools\check_validation_registry.py
if ($LASTEXITCODE -ne 0) { throw 'live validation registry coverage failed' }
```

Expected: both exit `0`; output reports no private Stage07/verifier/scorecard detector list and no unclassified `--outputs` checker.

Rollback: revert the registry and coverage checker together. Do not leave consumers partly migrated to a registry that CI does not validate.

### Phase 2: Make expectation sidecars executable

1. Add the negative-expectation schema.
2. Write an adapter for existing handshake `.expected-explain.json` files.
3. Migrate active workbench sidecars.
4. Move composite historical cases out of active single-signature coverage.
5. Require exact exit category, stage, class, checker ID, and marker.

Commands:

```powershell
python tools\check_validation_registry.py --expectations tests\stage-contract-workbench
if ($LASTEXITCODE -ne 0) { throw 'workbench expectation enforcement failed' }
python tools\check_staged_runtime_handshake.py
if ($LASTEXITCODE -ne 0) { throw 'staged handshake suite failed' }
```

Expected: exit `0`; every active invalid fixture matches its expectation and every active valid fixture passes.

Right-reason Stage04 assertion:

```powershell
$p = 'tests\stage-contract-workbench\stage-04-burden-execution-act\invalid\act-row-missing-land.json'
$raw = & python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $p 2>&1
$code = $LASTEXITCODE
$diag = ($raw | Select-Object -Last 1) | ConvertFrom-Json
if ($code -ne 1) { throw "expected exit 1, got $code" }
if ($diag.earliest_stage -ne '04') { throw "expected stage 04, got $($diag.earliest_stage)" }
if ($diag.failure_class -ne 'act_body_ref') { throw "expected act_body_ref, got $($diag.failure_class)" }
```

Expected: the wrapper exits `0` because the underlying checker exits exactly `1` with the pinned diagnostic.

### Phase 3: Repair the mutation sweep

1. Replace `_run_handshake_checker()` with a structured runner using `--explain-stage-failure`.
2. Preserve raw exit code, stdout, stderr, timeout, and parse state.
3. Replace `rejected` with controlled verdicts:

```text
rejected-right-reason
rejected-wrong-reason
survivor
usage-error
infrastructure-error
skipped-not-applicable
manifest-only-not-checker-verified
```

4. Make `rejected-wrong-reason`, usage error, infrastructure error, unexpected survivor, and unapproved manifest-only cases fail `--self-test`.
5. Keep known gaps visible but non-passing.
6. Add explicit per-operator source fixtures so generated-burden operators are exercised rather than skipped by one universal golden file.

Commands:

```powershell
$scratch = Join-Path ([System.IO.Path]::GetTempPath()) ("daee-right-reason-sweep-" + [guid]::NewGuid().ToString('N'))
python tools\gen_fixture_mutations.py --sweep tests\staged-runtime-handshake\valid\retained-a9-science-source.json --out-dir $scratch
if ($LASTEXITCODE -ne 0) { throw 'base mutation sweep failed' }
$manifest = Get-Content -Raw -LiteralPath (Join-Path $scratch 'sweep-manifest.json') | ConvertFrom-Json
$bad = @($manifest | Where-Object {
  $_.applicable -and $_.verification_depth -eq 'full' -and $_.verdict -ne 'rejected-right-reason'
})
if ($bad.Count -ne 0) { throw "right-reason failures: $($bad.operator -join ', ')" }
```

Generated-burden sweep:

```powershell
$scratch = Join-Path ([System.IO.Path]::GetTempPath()) ("daee-generated-right-reason-" + [guid]::NewGuid().ToString('N'))
python tools\gen_fixture_mutations.py --sweep tests\staged-runtime-handshake\valid\stage05-generated-provenance.json --out-dir $scratch
if ($LASTEXITCODE -ne 0) { throw 'generated-burden mutation sweep failed' }
```

Maximal MRP sweep:

```powershell
$scratch = Join-Path ([System.IO.Path]::GetTempPath()) ("daee-mrp-right-reason-" + [guid]::NewGuid().ToString('N'))
python tools\gen_fixture_mutations.py --sweep tests\stage-contract-workbench\stage-05-mrp-reread-terminal-state\maximal-valid\generated-burden-recurse-with-loopbreak.json --out-dir $scratch
if ($LASTEXITCODE -ne 0) { throw 'maximal MRP mutation sweep failed' }
```

Expected: all commands exit `0`; every applicable full-depth mutant is `rejected-right-reason`.

### Phase 4: Build a true Stage07 single-signature fixture

1. Start from a record that is valid through Stage06.
2. Copy its bound output into the fixture directory.
3. Apply only the Stage07 slim-public mutation.
4. Recompute the copied output hash in the copied record so custody remains valid.
5. Ensure no Stage01-06 field is invalid.
6. Assert the first failure is `07/public-projection`.

Command:

```powershell
$p = 'tests\validation-integrity\valid\right-reason-stage07-render\slim-public-output.json'
$raw = & python tools\check_staged_runtime_handshake.py --explain-stage-failure --records $p 2>&1
$code = $LASTEXITCODE
$diag = ($raw | Select-Object -Last 1) | ConvertFrom-Json
if ($code -ne 1) { throw "expected exit 1, got $code" }
if ($diag.earliest_stage -ne '07') { throw "expected earliest stage 07, got $($diag.earliest_stage)" }
if ($diag.failure_class -ne 'public-projection') { throw "expected public-projection, got $($diag.failure_class)" }
```

Expected: wrapper exits `0`. The old composite fixture remains historical evidence but no longer satisfies Stage07 right-reason coverage.

### Phase 5: Migrate Stage07 to registry profiles

1. Replace the local validator list with `stage07-release` profile resolution.
2. Keep `visible_governed_output_errors` and MRP record/surface parity as registered in-process adapters.
3. Preserve validator ordering and first failure.
4. Store registry hash and profile name in Stage07's release-validation record.
5. Assert compiled-output and single-output modes resolve the same required profile.

Commands:

```powershell
python tools\run_staged_current_skill_smoke.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'staged harness self-test failed after registry migration' }
python tools\check_validation_registry.py
if ($LASTEXITCODE -ne 0) { throw 'registry/runner parity failed' }
python tools\check_staged_runtime_handshake.py
if ($LASTEXITCODE -ne 0) { throw 'stage records failed after profile identity fields were added' }
```

Expected: all exit `0`; Stage07 records carry profile and registry identity.

### Phase 6: Upgrade candidate verification and verdict custody

1. Preserve `python tools\verify_candidate_output.py output.md` behavior.
2. Add `--profile captured-output-structural` and `--json-out`.
3. Run every required output-only checker in the profile.
4. Record all structured results, not only failed names.
5. Bind output and registry hashes.
6. Add a verdict-schema validator.

Positive command:

```powershell
$out = 'tests\retained-proof-corpus\v0.4.3.0-schema-light\valid\sidecar-backed\cases\a9-science-source\output.md'
$verdict = Join-Path ([System.IO.Path]::GetTempPath()) ("daee-verdict-" + [guid]::NewGuid().ToString('N') + '.json')
python tools\verify_candidate_output.py --profile captured-output-structural --json-out $verdict $out
if ($LASTEXITCODE -ne 0) { throw 'known structural seed failed captured-output profile' }
python tools\check_validation_registry.py --verdict $verdict
if ($LASTEXITCODE -ne 0) { throw 'verdict schema/hash validation failed' }
```

Negative command:

```powershell
$out = 'tests\stage-contract-workbench\stage-07-release-output\invalid\slim-public-output-below-structural-minimum.output.md'
$verdict = Join-Path ([System.IO.Path]::GetTempPath()) ("daee-negative-verdict-" + [guid]::NewGuid().ToString('N') + '.json')
python tools\verify_candidate_output.py --profile captured-output-structural --json-out $verdict $out
$code = $LASTEXITCODE
if ($code -ne 1) { throw "expected structural FAIL exit 1, got $code" }
python tools\check_validation_registry.py --verdict $verdict
if ($LASTEXITCODE -ne 0) { throw 'negative verdict artifact itself is malformed' }
```

Expected: positive exits `0`; negative verifier exits `1`; both verdict artifacts validate structurally.

Hash-drift test:

```powershell
python tools\check_validation_registry.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'hash-drift negative fixture was not rejected' }
```

The self-test must mutate a copied output after verdict creation and prove the verdict is invalid.

### Phase 7: Make Stage08 promotion profile compulsory

1. Join Plan 01 custody manifest, staged handoff, state capsules, prompt context, output, and sidecars.
2. Run the `promotion` profile.
3. Quarantine incomplete evidence.
4. Preserve raw outputs and failed verdicts.
5. Do not let a candidate-output-only PASS satisfy promotion.

Commands over a deterministic fixture bundle:

```powershell
$case = 'tests\validation-integrity\valid\promotion-complete-case\capture-manifest.json'
$verdict = Join-Path ([System.IO.Path]::GetTempPath()) ("daee-promotion-verdict-" + [guid]::NewGuid().ToString('N') + '.json')
python tools\verify_candidate_output.py --profile promotion --capture-manifest $case --json-out $verdict
if ($LASTEXITCODE -ne 0) { throw 'complete promotion fixture failed' }
python tools\check_validation_registry.py --verdict $verdict
if ($LASTEXITCODE -ne 0) { throw 'promotion verdict validation failed' }
```

Incomplete-evidence fixture:

```powershell
$case = 'tests\validation-integrity\invalid\profile-required-not-run\capture-manifest.json'
$verdict = Join-Path ([System.IO.Path]::GetTempPath()) ("daee-quarantine-verdict-" + [guid]::NewGuid().ToString('N') + '.json')
python tools\verify_candidate_output.py --profile promotion --capture-manifest $case --json-out $verdict
$code = $LASTEXITCODE
if ($code -ne 1) { throw "expected quarantined/non-pass exit 1, got $code" }
$payload = Get-Content -Raw -LiteralPath $verdict | ConvertFrom-Json
if ($payload.aggregate_status -ne 'QUARANTINED_INCOMPLETE_EVIDENCE') {
  throw "expected quarantine, got $($payload.aggregate_status)"
}
```

Expected: complete fixture exits `0`; incomplete fixture exits `1` with exact quarantine status.

### Phase 8: Align scorecard implementation and documentation

1. Keep v1 reader compatibility.
2. Add `--verdicts-dir` and `--schema-version v2`.
3. Remove detector execution policy from the scorecard.
4. Project per-case structural results and missing evidence from verdicts.
5. Validate docs examples against the emitted schema.

Commands:

```powershell
python tools\build_model_compliance_scorecard.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'scorecard self-test failed' }
python tools\check_docs_claim_boundaries.py
if ($LASTEXITCODE -ne 0) { throw 'scorecard documentation claim boundary failed' }
```

Fixture projection:

```powershell
$out = Join-Path ([System.IO.Path]::GetTempPath()) ("daee-scorecard-v2-" + [guid]::NewGuid().ToString('N') + '.json')
python tools\build_model_compliance_scorecard.py --schema-version v2 --verdicts-dir tests\validation-integrity\valid\scorecard-verdict-set --out $out
if ($LASTEXITCODE -ne 0) { throw 'scorecard v2 projection failed' }
$scorecard = Get-Content -Raw -LiteralPath $out | ConvertFrom-Json
if ($scorecard.schema -ne 'model-compliance-scorecard-v2') { throw 'wrong scorecard schema' }
if (@($scorecard.cases | Where-Object { $_.semantic_truth_status -ne 'NOT_CLAIMED' }).Count -ne 0) {
  throw 'scorecard made a semantic truth claim'
}
```

Expected: exit `0`; v2 schema matches docs; no private battery exists.

### Phase 9: Full deterministic closure

```powershell
python tools\check_validation_registry.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'validation registry self-test failed' }
python tools\check_validation_registry.py
if ($LASTEXITCODE -ne 0) { throw 'validation registry live check failed' }
python tools\gen_fixture_mutations.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'right-reason mutation suite failed' }
python tools\verify_candidate_output.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'candidate verifier self-test failed' }
python tools\build_model_compliance_scorecard.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'scorecard self-test failed' }
python tools\check_staged_runtime_handshake.py
if ($LASTEXITCODE -ne 0) { throw 'staged handshake suite failed' }
python tools\run_staged_current_skill_smoke.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'staged harness self-test failed' }
python tools\run_no_model_preflight.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'no-model preflight self-test failed' }
python tools\run_no_model_preflight.py
if ($LASTEXITCODE -ne 0) { throw 'no-model preflight failed' }
```

Expected: every command exits `0`. These are deterministic structural controls only.

## Stage01-Stage08 Control Map

| Stage | Integrity obligation | Required right-reason evidence | Promotion effect |
| --- | --- | --- | --- |
| 01 | Input/custody record is present and bound | `01/custody` negative plus valid intake | Failure invalidates all later stages |
| 02 | Declared topology contract is structurally valid | `02/burden-floor` or Plan 02's refined class | Failure invalidates 03-08 |
| 03 | Route and owner joins are valid | `03/owner-route` | Failure invalidates 04-08 |
| 04 | ACT/body refs and owner operations are structurally joined | `04/act_body_ref` | Failure invalidates 05-08 |
| 05 | MRP, provenance, and terminal state are valid | `05/mrp` | Failure invalidates 06-08 |
| 06 | Witness/NAR mirrors the surviving trajectory | `06/field_witness` | Failure invalidates 07-08 |
| 07 | Public projection passes the registered release profile and record/surface joins | `07/public-projection` single-signature fixture | Output is quarantined on failure |
| 08 | Sidecars, capsule/context, custody, hashes, and verifier profile are complete | `08/sidecar` plus promotion verdict | Only `PASS_STRUCTURAL` permits owner review |

The stage map does not claim that machine checks prove the correct theological analysis. It proves structural execution and evidence custody over the topology the system declared. Plans 02-10 address whether that declared topology and public witness are adequate.

## Five-Smoke Implications

The required cases are:

- `gate88-secularism`
- `gate88-khaybar`
- `gate88-trinitarian-j173`
- `gate88-tst-lillard`
- `gate88-torah-quran-source-authentication`

For each fresh authorized Stage01-Stage08 run:

1. The exact input, package, output, handoff, capsule/context, and sidecar hashes are bound by Plan 01 custody.
2. Stage07 uses the same registry hash and `stage07-release` profile.
3. Stage08 uses the same registry hash and `promotion` profile.
4. A required checker `NOT-RUN` quarantines that case.
5. A structural failure in one case is not averaged against four passes.
6. A retry is a new capture with a new manifest; it does not overwrite the failed run.
7. The fifth fixture stores the exact prompt only. It contains no expected burden count, submove count, output byte count, citation list, response outline, or theological conclusion.
8. Structural PASS is followed by topology and semantic review; it does not replace them.
9. Before owner authorization can permit the five paid producer calls, the exact
   candidate must hold `NO_MODEL_CANDIDATE_MATURE`, including zero open
   `YES` or `UNKNOWN` escape rows.
10. Any small structural/lifecycle/projection/custody defect first found here is
    converted into a permanent topic-neutral canary before a successor candidate
    is eligible. The complete failed five-case cycle remains preserved.

Completion evidence for this plan is five hash-bound promotion verdicts from the same registry/profile version. Historical retained outputs do not count as fresh model evidence.

## Rollback

- Registry migration must be atomic across runner, verifier, and scorecard. If one consumer cannot migrate, keep the old consumer explicitly labeled legacy and block promotion; do not maintain two silent policy sources.
- Revert schema, registry, adapters, fixtures, and consumers as one reviewed unit.
- Preserve every failed mutation manifest and promotion verdict generated during testing outside canonical fixtures until triage is complete.
- Never rewrite a raw captured output to make a verdict green.
- If a checker proves inapplicable, change registry classification with owner-reviewed basis and a fixture; do not simply delete it from a private list.
- If a right-reason fixture cannot be made single-signature, retain it as historical composite and add a new single-signature fixture.
- Rollback does not authorize returning to broad promotion claims. The honest rollback state is `promotion-integrity: unverified`.

## STOP / ANDON Conditions

Stop and write a terminal record if:

- a mutation is counted as rejected on any nonzero exit;
- a negative fixture fails at a different earliest stage or class;
- a required diagnostic is `unclassified`;
- a usage error, timeout, crash, or unavailable checker is coerced into structural rejection;
- a composite fixture is counted as single-signature proof;
- Stage07, verifier, or scorecard retains a private detector policy after migration;
- a required promotion checker is `NOT-RUN` or missing;
- output, registry, or checker hashes drift after verdict creation;
- a scorecard upgrades structural acceptance into semantic truth, uptake, provenance, or regression proof;
- a known gap is represented as PASS;
- a paid/model smoke is used to recheck a known deterministic escape before its
  permanent canary is red/green/right-reason proven and CI-wired;
- an escape is classified `NO` without an accountable basis and
  compensating observability/review control;
- model calls allegedly avoided are counted without an actually blocked planned
  invocation or cycle;
- raw evidence is edited;
- a model run, issue, package, release, commit, push, tag, or publication is attempted without separate authorization.

Terminal record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED
andon_class: wrong-reason-rejection | battery-drift | fixture-composite | promotion-custody | infrastructure | claim-overreach
case_or_fixture: repo-relative-path
expected_checker_id: stable-registry-id
expected_earliest_stage: "01" | "02" | "03" | "04" | "05" | "06" | "07" | "08"
expected_failure_class: stable-class
observed_execution_status: completed | not-run | usage-error | timeout | crashed | unavailable
observed_structural_result: accepted | rejected | not-applicable | indeterminate
observed_earliest_stage: stage-or-null
observed_failure_class: class-or-null
registry_sha256: hash-or-null
artifact_sha256: hash
failing_command: exact-command
owner_source: file-and-function
next_action: one-concrete-action
preserved_artifacts: paths-and-hashes
regression_status: unproven
```

`BLOCKED` and `AUDIT_COMPLETE` are mutually exclusive for the same active abnormality.

## Adversarial Review Applied

The plan was attacked against the current implementation before finalization. The following objections are incorporated as requirements rather than left as review notes.

| Adversarial attack | Why it would defeat a weaker plan | Adopted countermeasure | Proof fixture/gate |
| --- | --- | --- | --- |
| A central registry can become one more stale list | Merely moving copied names into a new file does not prevent omissions | Discover `--outputs` tools, parse consumer call sites, and require explicit classification | `unregistered-output-checker` and private-battery fixtures |
| Exact message substrings can make fixtures brittle | Harmless wording changes could look like checker failure | Prefer stable failure class/diagnostic ID; keep message markers narrow and secondary | Wrong-class and required-marker fixtures |
| An exit-1 crash can masquerade as rejection | Some scripts use exit 1 for environment or internal faults | Capture execution status, JSON parse state, stdout/stderr, and expected diagnostic | Usage, timeout, crash, malformed-diagnostic fixtures |
| A composite fixture can still satisfy its target marker | The intended marker may be present after an earlier unrelated failure | Require earliest-stage equality and single-signature active fixtures | Current Stage07-to-Stage04 reproducer plus repaired Stage07 fixture |
| Running every checker over every file can create false failures | Checkers have different artifact and mode prerequisites | Registry declares artifact kinds, applicability, and required inputs | Profile-required-not-run and mode-specific fixtures |
| A registry hash can be correct while checker code changes | Registry identity alone does not bind tool behavior | Record each checker source hash in every verdict | Tool-hash drift fixture |
| A verdict can be replayed against a changed output | Path identity is insufficient | Bind output SHA-256 and revalidate before consumption | Verdict-output-hash-drift fixture |
| A scorecard can independently rerun a smaller battery | Reporting then becomes a second policy owner | V2 consumes verdicts; registry checker rejects a private scorecard list | `scorecard-private-battery` fixture |
| `NOT-RUN` can be made to look neutral in aggregate | Missing proof disappears into summary counts | Required `NOT-RUN` quarantines promotion | `profile-required-not-run` fixture |
| Known gaps can normalize permanent weakness | A visible exception may still be read as green | Known gaps are findings, require owner/expiry metadata, and cannot promote | Known-gap-offered-as-PASS fixture |
| More checkers can be mistaken for semantic rigor | Structural breadth still cannot prove truth or uptake | Non-claims are schema-required and topology review remains separate | Verdict/scorecard schema negative fixtures |
| Five passing cases can hide one failed case through averaging | Aggregate success can erase a stopped lane | One-shot per-case verdicts; any failed case stops matrix promotion | Five-smoke scorecard projection test |

Rejected countermeasures:

- Treat every nonzero exit as success.
- Add a universal answer-length threshold.
- Add universal burden or submove counts.
- Hard-code the fifth smoke's expected topology or answer.
- Delete difficult checkers from the candidate profile without an applicability decision.
- Rewrite invalid outputs until the current battery accepts them.
- Treat registry/verifier PASS as semantic truth.

## Definition of Done

- Every active mutation operator has an executable exact expectation.
- Every active invalid fixture either rejects for the expected earliest stage/class/checker or fails the suite.
- The Stage07 slim-output test is single-signature and rejects at `07/public-projection`, not Stage04.
- Exit 2, timeout, crash, unavailable checker, malformed diagnostic, and wrong-reason exit 1 are all non-passing states.
- One registry owns checker classification, arguments, applicability, and profiles.
- Stage07, candidate verification, Stage08 promotion, and scorecarding consume registry projections rather than private lists.
- Every output-capable checker is classified with a reason.
- Promotion verdicts are hash-bound to output, registry, checker results, and Plan 01 custody.
- Required `NOT-RUN` or missing evidence quarantines; it never passes.
- Scorecard documentation matches implementation and v2 rows are semantically unambiguous.
- Existing no-model preflight remains green after the added gate.
- Every paid-smoke-discovered deterministic defect has a closed append-only
  escape row and a permanent CI-wired canary; `UNKNOWN` blocks maturity.
- Escape canaries survive topic-neutral identifier/order/paraphrase/noise
  transformations and fail when the repaired relation is removed.
- Campaign reporting separates calls attempted/completed/cancelled/not
  dispatched, actual maturity blocks, escapes, recurrences, and honest unknowns.
- All five fresh smokes eventually carry verdicts from one registry/profile version.
- Structural PASS remains explicitly non-semantic.
- `regression_status` remains `unproven` until Plan 01's controlled comparison gate produces admissible evidence.

## Confidence

Right-reason mutation and fixture enforcement: **YES, implementation-ready.**  
Unified registry and hash-bound structural verdict: **YES, implementation-ready with Plan 01 schema coordination.**  
Scorecard v2 migration: **YES, implementation-ready with v1 read compatibility.**  
Semantic completeness or theological correctness from these controls: **NO, not claimed and not machine-proven.**  
PR #9 regression causality: **NO, unproven.**
