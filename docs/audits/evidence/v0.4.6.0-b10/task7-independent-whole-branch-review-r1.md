# Task 7 independent whole-branch review - Revision 1

Date: 2026-07-12
Branch: `codex/v0.4.6.0-runtime-footprint-b10`
HEAD: `4bb7018f793166467a0215bbe614a9ae0b97f0ee`
Independent reviewer: `/root/task7_whole_branch_review`
Verdict: `REJECT`

- Critical findings: `0`
- Important findings: `5`
- Minor findings: `3`
- Canonical whole-branch review JSON created: `no`
- Source or staged bytes modified by this review: `no`

The zero-finding acceptance condition is not met. This record is a durable rejection
report only. It does not authorize deterministic approval publication or downstream
progression.

## Exact reviewed identity

| Surface | Identity | Bytes / count | SHA-256 |
|---|---|---:|---|
| Prospective Git tree | `10810336aae80320695962be7cf95c7c70d65b07` | 230 staged paths | - |
| Source freeze | `a682b6ec3b90574e29fbc6aff6a4a2dbb0c029d77584a4a6ea8110c5eea1f65c` | 811729 bytes; 3460 files | `41cb920f19199523c240b2d79e8f243de9a4f8da38c8503489423f498ece8126` |
| Reviewer authorization | `9295cc0d4a928d07f9b60be62c96f9fd4bd53f9ee8131ad8462dd74b971fcb02` | 717 bytes | `4a06473b779f9100bd7daeee76db62d1913b4383956608f8cfedb06db72450f4` |
| Generated-freshness/package PASS | `4f86868308fbdbfe9760e535bf01661aa4d5160ccd7a321240bef606185a0ee9` | 2371 bytes | `675dc32a228563b8d142f28952e012a99c58324d8aa8acd7a314db32df9ae1e7` |
| No-model-preflight PASS | `243adfa24ad3df3b70549120ee29a4c41e5453d79a442a3beef0b0a9c4e403ee` | 2326 bytes; 25/25 gates; 62 commands | `9387e36a0758ddcbf16302e5e21cf7c07769c4c3eed3bc509426ad7acfef3b1e` |
| Full-local-CI PASS | `cace47d99384bfd03586549c599a7d72a1d367faca82b51e3341880cb589e567` | 2304 bytes; 172/172 commands | `591293f230d6906d553a390679cf20f73de1fbecb258f06b4f2ed4342dcad056` |

The authorization names `/root/task7_whole_branch_review`, binds the exact prospective
tree, and was issued at `2026-07-12T22:42:31Z`. The source freeze is complete, binds the
same tree, records `model_calls=0`, and its 3460 file records were compared with the
prospective tree. The index equals the prospective tree; there were 230 staged paths and
no unstaged source changes. The three deterministic verdict files above say `PASS`, bind
the same freeze and tree, record `terminal_claim=false`, and record zero model calls.

The existing broad PASS receipts were read and identity-checked; this independent review
did not rerun full preflight or full local CI. Focused contract checks and bounded probes
were used to test the newly identified failure modes.

## Important findings

### I1 - CI readback rejects Gate 16's canonical successful exit

Evidence:

- `tools/run_no_model_preflight.py:83-84` defines the shared narrow mapping
  `EXPECTED_GATE_RETURN_CODES = {16: 1}`.
- `tools/write_task7_deterministic_evidence.py:596-610` correctly validates Gate 16
  against that shared expected return code.
- `tools/check_ci_readback.py:783-804`, especially line 795, instead rejects every native
  gate step whose return code is not zero.
- `tests/ci-readback/build_task7_fixtures.py:59-81`, especially line 70, generates return
  code zero for every gate and therefore masks the production mismatch.
- `tests/ci-readback/test_contract.py:277-332` exercises the writer-side validator but
  does not prove the downstream readback checker accepts the canonical Gate 16 result.

Bounded probe:

The current no-model bundle was passed directly to the readback bundle validator with
the exact reviewed source tree and Gate 16's canonical exit `1`. It rejected the bundle
with `preflight-result: no-model preflight gate 16 is not proven PASS`.

Impact:

A legitimate exact-tree no-model-preflight PASS cannot be consumed by downstream CI
readback. The current fixture cohort gives false confidence because its Gate 16 value is
the value the production gate must reject.

Required repair:

1. Import and use the shared expected-return-code map in `tools/check_ci_readback.py`.
2. Apply the same mapping in `tests/ci-readback/build_task7_fixtures.py`.
3. Regenerate every dependent Task 7 support bundle and recorded digest.
4. Add downstream checker canaries proving Gate 16 exit `1` is accepted and exits `0`
   and `2` are rejected for the right reason.

### I2 - Preflight timeout handling does not contain descendant processes

Evidence:

- `tools/run_no_model_preflight.py:159-195` launches ordinary gate commands with
  `subprocess.run(..., timeout=...)`.
- The separate Gate 16 execution at `tools/run_no_model_preflight.py:528-543` uses the
  same immediate-child-only timeout mechanism.
- `tools/run_no_model_preflight.py:209-217` continues remaining commands after a timed
  out or failed command.

Bounded probe:

A contained child/grandchild test returned timeout exit `124`, but the grandchild PID
remained alive for more than 24 seconds and blocked temporary-directory cleanup until
that exact process was terminated. Cleanup completed after termination.

Impact:

A timed-out command can leave an owned descendant running after its gate is RED. That
process can mutate files or race later gates and evidence publication while the runner
continues.

Required repair:

1. Route all preflight commands, including Gate 16, through the owned process-tree
   execution primitive used by local CI.
2. Complete descendant teardown before returning the timed-out result.
3. Stop the remaining commands in the affected gate after timeout.
4. Add child/grandchild cleanup and no-next-command canaries.

### I3 - Post-observation reviewed-campaign failures bypass terminal fallback

Evidence:

- The producer `try` block at `tools/reviewed_campaign_orchestrator.py:1057-1073`
  covers provider execution and observation publication only.
- Producer dispatch validation, settlement, completion, and success-finalizer work at
  lines 1074-1129 is outside the fallback boundary.
- The cold-review path has the same gap: its protected block ends at lines 1389-1405,
  while validation, settlement, completion, and finalization continue at lines
  1406-1448.

Bounded probe:

A fake-only, zero-provider-call producer probe forced dispatch-manifest validation to
fail after all five observations. It produced five result files, left one reservation
open, and published neither an incident nor an observation finalizer.

Impact:

Failures after observation can strand paid-usage custody and omit the terminal incident
and finalizer evidence required to distinguish incomplete, settled, and closed work.

Required repair:

1. Establish one phase-aware failure boundary from reservation through terminal
   publication for both producer and cold-review lanes.
2. On every post-observation, post-settlement, or post-completion exception, settle
   conservatively using known handles and receipts.
3. Always publish an incident plus terminal finalizer.
4. Add fault-injection canaries at each phase for both lanes.

### I4 - Sanitized bootstrap allows external package roots to shadow the stdlib

Evidence:

- `tools/sanitized_python_bootstrap.py:30-52` appends repository roots, system and user
  `purelib`/`platlib`, and only then the inherited `-I -S` interpreter paths containing
  the standard library.

Bounded probe:

The exact reviewed bootstrap produced user `purelib` at `sys.path` index `3` and the
standard-library directory at index `6`: `user_precedes_stdlib=True`.

Impact:

A same-named module in the admitted user package directory can replace a not-yet-loaded
standard-library module such as `subprocess`, `hashlib`, or `json` in a governed target.
The bootstrap therefore excludes startup customization but still admits ambient,
unbound code ahead of the stdlib.

Required repair:

1. Place `stdlib` and `platstdlib` roots before all system and user package roots.
2. Preserve only the intentional repository/tool/script-parent precedence.
3. Keep user dependency roots after the stdlib so the intended PyYAML dependency remains
   available without `.pth` processing.
4. Add a fake stdlib-name shadowing canary and retain the PyYAML-availability check.
5. Rebind the execution profile and governed fixtures, then regenerate deterministic
   evidence.

### I5 - Accepted architecture decision names a nonexistent owner path

Evidence:

- `docs/audits/v0.4.6.0-wip-architecture-decisions.json:575-592`, especially line 590,
  lists `tools/custody_fs.py` for accepted decision `ADR-046-017`.
- `tools/custody_fs.py` is absent from the exact prospective tree.
- The implemented shared custody-path owner is `tools/artifact_tree.py`, also recorded in
  the architecture ledger at line 962 and the contract registry at line 266.
- `tools/check_architecture_decision_ledger.py:63-103` checks schema, status, and narrow
  exclusive-owner rules but does not generally require every `owner_files` path to
  resolve. Of 92 ADR owner references, this was the sole unresolved path.

Impact:

An accepted, contract-bound architecture decision points executors and reviewers to a
nonexistent implementation owner while its structural checker reports PASS.

Required repair:

1. Reconcile `ADR-046-017` to the actual owner set, replacing the nonexistent path with
   the approved implemented owner.
2. Make the architecture-ledger checker reject every nonexistent repository owner path.
3. Add a missing-owner-path negative fixture.
4. Rerun the ADR, contract-registry, closure-ledger, and rendered-view checks.

## Minor findings

### M1 - Clean-filter fail-closed branches lack direct mutation canaries

Evidence:

- `tools/write_task7_deterministic_evidence.py:521-566` rejects CR/LF paths, missing
  paths, Git failure, unterminated or count-drifted output, non-ASCII OIDs, and malformed
  OIDs.
- Its direct self-test at `tools/write_task7_deterministic_evidence.py:713-790` covers
  portability, content drift, and index drift only.
- Repository-wide test search found no direct mutation coverage for the remaining
  rejection branches. The same gap was carried at
  `.IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5/reviews/task7-clean-filter-portability-independent-review.md:40-48`.

Required repair:

Extract or directly drive the batch-output parser and add exact-reason canaries for
missing paths, CR/LF paths, subprocess failure, unterminated output, count drift,
non-ASCII OIDs, and malformed OIDs.

### M2 - Current Branch 10 audit owners are absent from the active audit index

Evidence:

- `docs/audits/README.md:20-26`, especially line 22, requires current audit documents to
  appear in the active index.
- `docs/audits/INDEX.md:12-23` omits the current Branch 10 closure ledger, contract
  registry, and architecture-decision ledger. Exact-path search found no entry for any
  of the three.

Required repair:

Add the three current audit owners under `Current Implementation Targets` with explicit
`OPEN`, structural-only, and non-terminal qualifiers. Do not describe checker PASS as
terminal closure.

### M3 - Mutable run-root continuity surfaces contradict the current Task 7 state

Evidence:

- `.IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5/STATE.md:15-16`
  accurately records Revision 4 acceptance, the exact tree, `25/25` no-model-preflight,
  `172/172` full local CI, and whole-branch review as the next open gate.
- The same file's `Current Hansei / 5 Whys / Kaizen` section at lines 194-202 still says
  Revision 3 needs review before preflight/local CI.
- `.IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5/ROADMAP.md:85-96`
  repeats the Revision 3/preflight/local-CI pending sequence.
- `.IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5/phases/phase-3.md:118-130`
  makes the same stale statement.

Impact:

The authoritative top state is current, but nearby surfaces labeled as the current
roadmap, phase, and Hansei can route a successor into already completed work. This review
does not separately classify the source-frozen closure ledger's pre-receipt wording as a
defect; that tracked ledger is bound to the pre-receipt source snapshot.

Required repair:

Update only the mutable run-root continuity surfaces to agree with `STATE.md:15-16`,
preserve every still-open downstream boundary, and re-read them together before handoff.

## Verification performed

- `git diff --cached --name-status 10810336aae80320695962be7cf95c7c70d65b07`
  returned empty: the index exactly equals the authorized prospective tree.
- `git diff --name-status` returned empty: there were no unstaged source changes.
- `git diff --cached --check` passed.
- Source-freeze schema, tree identity, and all 3460 blob records matched the prospective
  tree.
- Closure-ledger self-test/live check passed at `5` valid / `17` invalid.
- Contract-registry self-test/live check passed at `1` valid / `18` invalid.
- Architecture-ledger self-test/live check passed at `1` valid / `3` invalid.
- Closure renderer and CI-registry self/live checks passed.
- Task 7 fixture freshness passed for 40 governed files.
- CI-readback contracts passed `43/43`; no-model-preflight contracts passed `15/15`;
  reviewed-campaign contracts passed `30/30`.
- All referenced ledger evidence and owner paths, except the ADR owner path identified in
  I5, resolved; failed-attempt lineage remained preserved.
- The bounded probes described in I1-I4 were diagnostic only. The campaign probe used
  fakes and made zero model/provider calls. The descendant process created by the timeout
  probe was explicitly terminated and cleaned up.

The focused suites passing does not supersede the findings: I1, I5, M1, and M2 identify
coverage or structural gaps that the current passing fixtures mask, while I2-I4 are
bounded failure-mode reproductions outside the existing happy-path contracts.

## Explicit downstream nonclaims

This `REJECT` record is not evidence of and does not claim or authorize:

- a canonical Task 7 independent whole-branch review PASS verdict or its JSON record;
- repair acceptance or a reviewed post-repair source identity;
- a successor source commit, commit authorization use, push, or exact remote readback;
- external current-commit source receipt or external preflight;
- exact-SHA GitHub CI or branch-protection satisfaction;
- immutable candidate construction, retention, maturity, readiness, or package promotion;
- provider/model execution, reviewed five-smoke or cold-review execution, or campaign
  success;
- tag, release package, release, publication, or deployment;
- owner acceptance, audit-object closure, or terminal closure of any A01-A16 row.

The existing generated-freshness/package, no-model-preflight, and full-local-CI PASS
receipts remain bounded observations of the rejected exact tree. They do not override
the findings, authorize a canonical review PASS, or satisfy later gates.

## Decision and required next gate

`REJECT` exact tree `10810336aae80320695962be7cf95c7c70d65b07` for Task 7
whole-branch-review promotion.

Close all five Important and three Minor findings with narrow, reviewed repairs. Because
the repairs change governed source and/or continuity identities, create a fresh exact
source freeze, regenerate all affected fixtures and deterministic receipts, and obtain a
fresh one-use independent-review authorization naming a reviewer who did not author the
repairs. A fresh independent whole-branch review of the repaired exact tree is mandatory.
Only a zero-Critical, zero-Important, zero-Minor result may create the canonical review
JSON and proceed to the ordinary downstream authorization gates.
