# Captured-output evidence custody

This subsystem records deterministic custody and review boundaries. It does not run a model, mutate an external evidence root, rewrite a raw output, build a package, promote a candidate, or prove theological or causal claims.

## Custody roots and references

Every manifest is interpreted against one explicitly supplied custody root. Every referenced input, package, build manifest, invocation record, output, replay stream, review artifact, incident, authorization, stage record, witness, audit envelope, body record, packet, and packet proof is one relative `path` / lowercase SHA-256 / byte-count object. Validators resolve and hash-read back the object before applying semantics. Absolute paths, drive-qualified paths, UNC paths, parent traversal, missing files, and resolved symlink or reparse-point escapes are rejected.

Validation produces an immutable in-memory artifact snapshot: canonical contained path, exact bytes, digest, byte count, and decoded JSON or text derived from those bytes. Downstream joins and builders consume that snapshot rather than reopening the pathname. Verdict and packet publication stage complete bytes under the destination parent, verify the staged bytes, publish without replacing an existing target, and perform a final byte-for-byte readback. A race winner remains untouched; injected failures remove both any visible A01 output and its staging residue.

Atomic directory no-replace publication uses Windows rename semantics or Linux `renameat2(RENAME_NOREPLACE)`; platforms or filesystems without an atomic no-replace primitive fail closed without a check-then-rename fallback.

Hash validity is only the first boundary. Every load-bearing referenced JSON object is then checked by its canonical pure validator and joined back to the parent's case, cycle, input, output, protocol, source commit, package, verdict, attempt, and authorization identities. Hash-valid arbitrary JSON is rejected. These joins are lazy in-process function calls; they do not use subprocess exit codes as semantic evidence and do not permit circular validator ownership.

The root may be a synthetic fixture root, a repo-local capture root, or an owner-approved durable external root. The tools never create or alter the owner-selected external evidence root unless an explicit builder command names an unused output directory under that root.

## Contracts

- `daee-captured-output-v1` binds exact input and output bytes; package, build-manifest, and source-commit identity; operator, resolved model/runner/host/session, tool/output-budget/retry/continuation/truncation controls; invocation; per-checker replay streams and first failure; both review references; provenance state; and structural-only nonclaims.
- `daee-captured-output-comparison-v1` preserves the `v45 -> inherited-main -> pr9-base -> pr9-head` stack, including explicit `not-run` cells. It permits only `unproven`, `not-comparable`, `confounded`, `candidate-observed`, `replicated-candidate`, and `not-observed`. No tool emits `proven`; output length and one pair do not prove causality.
- `daee-topology-initial-assessment-v1` is a separate immutable human artifact claimed before cold disclosure.
- `daee-topology-review-v1` binds the unchanged initial hash and disclosure time, requires exact cold-finding/adjudication set equality, requires target-bound evidence and finding-specific rationale for every `answered` challenge, blocks material `upheld` or `unresolved` findings under PASS, forbids structural waiver, and requires an affirming independent second review for patch-owner or material reversal.
- `daee-cold-comprehensiveness-review-v1` binds exact `gpt-5.6-sol` / `xhigh` resolved identity, fresh isolated context, input/output, Stage01-Stage08, witness/audit/body records, packet, authorization, reconstruction-before-grading, attempt selection, retry lineage, and cohort replay.
- `daee-review-incident-report-v1` is required before retry, packet repair, or a successor cycle after an invalid or ambiguous attempt. It binds the attempt, output, packet, failure class, substantive-grading flag, complete lineage, owner notification, proposed action, and continuation authority.

## Packet builder

`build_cold_review_packet.py` reads a relative-reference specification, hash-validates every source artifact, and writes only a new `payload.json` and `manifest.json` under an unused custody-root-relative directory. The payload embeds the exact UTF-8 input and unmodified output plus the supplied public rubric, eight stage records, witnesses, audits, and body references. Forbidden expectation, topology/count, favorable exemplar, cross-case-output, and prior-conversation keys stop the build. A same-packet transport retry reuses existing bytes; a rebuilt packet requires predecessor, exact delta, deterministic red/green builder proof, anti-answer-bank proof, unchanged input/output, and new authorization.

The builder and cold checker validate structured predecessor, delta, red/green, anti-bank, and one-use authorization objects before accepting them. Purpose, rubric, and all supplied metadata strings are scanned for topic-neutral answer-key, golden-answer/conclusion, expected-conclusion, and grading-key instructions; self-declared `forbidden_content` booleans are not treated as proof. Packet or attempt selection is derived from complete contiguous lineage: predecessors must be unselected and the latest valid attempt must be selected.

Shared-protocol replay consumes an independently hash-bound `daee-cold-review-cohort-v1` manifest. Empty or duplicate case sets, protocol drift, and any repeated-case set smaller than that independently supplied cohort are rejected. A01 validates this object but does not own the A14 cohort producer or the A14/A16 authorization issuer.

## Commands

Use a custody-root-relative manifest path in operational use:

```powershell
python tools/check_captured_output_manifest.py --manifest capture-manifest.json --custody-root <root> --explain
python tools/check_captured_output_manifest.py --comparison comparison.json --custody-root <root> --explain
python tools/check_topology_review.py --review topology-review.json --custody-root <root> --explain
python tools/check_cold_comprehensiveness_review.py --review cold-review.json --custody-root <root> --explain
python tools/check_review_incident_report.py --report incident.json --custody-root <root> --explain
python tools/build_captured_output_verdict.py --capture capture-manifest.json --custody-root <root> --out <unused-output>
python tools/build_cold_review_packet.py --spec packet-spec.json --custody-root <root> --out-dir <unused-relative-directory>
```

`tests/captured-output-custody/run_scenarios.py` is the direct same-stem expectation assertion surface. It validates each sidecar with A11's canonical schema and pins the exact checker, exit, earliest boundary, class, subcode, downstream invalidation, diagnostic markers, and forbidden-artifact absence. A11's shared `contract_validation.py` is reused directly. The current `assert_expected_rejection.py` cannot directly consume A01 scenario manifests because it requires a validation-registry checker-replay verdict and registry wiring is outside A01 write ownership; this is an integration delta, not a reason to weaken custody.

## Retained incomplete-provenance specimen

`work/grok-v46-output.md` remains read-only external evidence with owner-reproduced SHA-256 `8987D4E0EEC63DCBE5E0D58536B776B25700AECA24AF6426C803C9B31CCE3F40`. Its historical input, package, host/model/session, and execution controls are incomplete, so it is nonpromotable and is not normalized into a valid capture manifest. The replayed structural failures remain structural evidence only. `regression_status` remains `unproven`.
