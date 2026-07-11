# Model-compliance scorecard

Status: bounded A11 record-projection contract. This surface makes no model,
network, candidate-maturity, five-smoke, provenance, or release-readiness
claim.

## Current writer: `model-compliance-scorecard-v2`

`tools/build_model_compliance_scorecard.py` emits v2 only from existing
`daee-checker-replay-verdict-v1` records named by one exact
`daee-scorecard-case-manifest-v1`. That manifest names verdict paths and binds a
cohort label, source commit/profile, and canonical validation-registry path/SHA;
it does not authorize its own completeness. The builder independently loads the
sole canonical five-case input registry through `smoke_matrix_registry`, checks
its immutable digest and input custody, and requires the manifest's ordered case
IDs to equal those five IDs exactly before reading any verdict. Before
projection, every replay is read once; its raw hash, parsed object, and canonical
hash all derive from those same bytes. Schema/semantic validation then checks
the registry, checker-source hashes, and artifact hashes. The scorecard profile
has zero invocations. The builder does not import, launch, or replay a detector.

The v2 shape is:

```json
{
  "schema": "model-compliance-scorecard-v2",
  "selected_profile": "scorecard",
  "registry_path": "tools/validation-registry.json",
  "registry_sha256": "<sha256>",
  "case_registry_path": "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json",
  "case_registry_sha256": "<sha256>",
  "cohort_manifest_path": "<repository-relative manifest>",
  "cohort_manifest_sha256": "<sha256>",
  "cohort_id": "<cohort-id>",
  "source_commit": "<40-hex commit>",
  "source_profile": "<replay profile>",
  "completeness_status": "COMPLETE_EXACT_CANONICAL_FIVE_CASE_AUTHORITY",
  "capture_meta": {
    "host": "<label>",
    "captured_from": "checker-replay-verdicts",
    "verdict_count": 5
  },
  "rows": [
    {
      "case_id": "<source verdict_id>",
      "cohort_id": "<cohort-id>",
      "source_commit": "<40-hex commit>",
      "source_profile": "<replay profile>",
      "source_verdict_path": "<repository-relative replay verdict>",
      "input_path": "<canonical case input path>",
      "input_sha256": "<sha256>",
      "output_sha256": "<sha256>",
      "verdict_sha256": "<raw replay-file sha256>",
      "canonical_verdict_sha256": "<canonical replay-object sha256>",
      "registry_sha256": "<sha256>",
      "structural_status": "PASS_STRUCTURAL | FAIL_STRUCTURAL | QUARANTINED_INCOMPLETE_EVIDENCE | INFRASTRUCTURE_ERROR | NOT_RUN",
      "required_checker_ids": ["<ordered checker id>"],
      "required_checks": 1,
      "missing_required_checker_ids": [],
      "accepted_checks": 1,
      "rejected_checks": 0,
      "not_run_checks": 0,
      "indeterminate_checks": 0,
      "topology_review_ref": null,
      "topology_review_status": "NOT_REVIEWED",
      "semantic_truth_status": "NOT_CLAIMED",
      "checker_results": [
        {
          "checker_id": "<registry checker id>",
          "tool_path": "<registry source path>",
          "tool_sha256": "<sha256>",
          "artifact_type": "<type>",
          "artifact_sha256": "<sha256>",
          "execution_status": "<recorded status>",
          "structural_result": "accepted | structural-rejection | not-run | indeterminate",
          "exit_code": 0,
          "expectation_status": "<recorded expectation>",
          "diagnostic": null,
          "stdout_sha256": "<sha256>",
          "stderr_sha256": "<sha256>"
        }
      ]
    }
  ],
  "non_claims": ["record projection only; no detector or model execution"]
}
```

Rows preserve manifest order and each verdict's checker-result order.
Each case row binds input, output, raw verdict, canonical verdict object, and
registry hashes. Its input path/hash must equal the same case ID's canonical
input-custody tuple; a relabeled verdict cannot satisfy completeness. Each row
reports the replay aggregate plus required, accepted,
rejected, not-run, and indeterminate counts. Missing required result rows are
named and counted as not run. Detailed results keep `execution_status` separate
from `structural_result`: accepted and structural rejection remain distinct,
while infrastructure or malformed outcomes project as indeterminate. The exact
recorded fields remain present; no ambiguous `PASS/FAIL` scalar replaces them.

The current A11 replay verdict has no bound topology-review artifact. Therefore
the v2 builder writes `topology_review_ref: null`, `NOT_REVIEWED`, and
`semantic_truth_status: NOT_CLAIMED`; an unbound scalar cannot become review
evidence.

Readback resolves the bound manifest and every replay under repository custody,
independently reloads the canonical five-case authority, revalidates
registry/tool/artifact identities, and recomputes the entire row.
Forged aggregate status, counts, paths, hashes, omitted results/cases, duplicate
cases, mixed commits/profiles, or a subset of the expected manifest are rejected.
Completeness is exact only relative to the canonical five-case input authority;
the cohort label and caller-authored manifest cannot shrink or reorder it.
Publication removes private staging only before the no-replace transaction.
After the final directory becomes visible, any later evidence ambiguity is
reported while the final path is preserved; the writer never path-deletes a
possibly swapped competitor.

## Historical reader: `model-compliance-scorecard-v1`

The validator and Markdown renderer continue to read the historical v1 shape:

```json
{
  "schema": "model-compliance-scorecard-v1",
  "capture_meta": {"host": "legacy", "captured_from": "fixtures", "output_count": 1},
  "rows": [
    {
      "failure_shape": "<legacy label>",
      "detector": "<legacy checker filename>",
      "mode": "structural",
      "verdict": "PASS | FAIL | NOT-RUN"
    }
  ],
  "non_claims": ["<non-claim>"]
}
```

Compatibility is read-only: the current builder does not accept captured
Markdown as a reason to rerun v1's detector map, and it never emits new v1
records.

## Commands

```powershell
python -B tools/build_model_compliance_scorecard.py --self-test
python -B tools/build_model_compliance_scorecard.py --case-manifest <case-manifest.json> --case-registry tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json --out-dir <fresh-scorecard-directory>
python -B tools/build_model_compliance_scorecard.py --read-scorecard <v1-or-v2.json>
```

## Boundaries

- Projection is offline and record-only. It does not execute a detector or a
  model and does not make a network request.
- `NOT_RUN` and missing required checker rows cannot satisfy promotion; v2
  preserves and counts them instead of converting them to a pass.
- A projected pass is structural replay evidence only, not semantic truth,
  persuasion, interlocutor uptake, cross-host behavior, or provenance.
- A scorecard is not a candidate-maturity, five-smoke, promotion, package,
  publication, or release authorization surface.
- Consumption of the five-case input registry proves only cohort completeness;
  it does not prove that the authoritative five-smoke campaign ran or passed.
