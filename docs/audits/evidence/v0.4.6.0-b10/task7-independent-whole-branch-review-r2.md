# Task 7 independent whole-branch review - Revision 2

Date: 2026-07-12
Branch: `codex/v0.4.6.0-runtime-footprint-b10`
HEAD: `4bb7018f793166467a0215bbe614a9ae0b97f0ee`
Independent reviewer: `/root/task7_whole_branch_review`
Verdict: `REJECT`

- Critical findings: `0`
- Important findings: `3`
- Minor findings: `0`
- Canonical whole-branch review JSON created: `no`
- Source or staged bytes modified by this review: `no`

The zero-finding acceptance condition is not met. This is a durable rejection
record only. It does not authorize independent-review PASS publication or any
downstream progression.

## Exact reviewed identity

| Surface | Identity | Bytes / count | File SHA-256 |
|---|---|---:|---|
| Prospective Git tree | `a5a6f885f3e3a08a361c5e73f520a0d23c89ba39` | 238 staged paths | - |
| Source freeze | `ab1603a9d764b0ede3f1cc06c7a7e0991e5ae52a0de49fdb45a97d1acb73f970` | 812679 bytes; 3464 files | `02690b5918a4783e22f0e4d0d79a472aa15e3a7792bd888bc9a7be87448a75ad` |
| Reviewer authorization | `497ec356b8fe409e22d4a62285a1146dc60c23cefd2164f9f382dfd2f547cd36` | 717 bytes | `ba6949d2a863c73c8b3bb7226928d0f2b5e7a7c0a5b3847151d6f6801e32c9b6` |
| Generated-freshness/package PASS | `f7f22aaad3c73e4f22a02cccfbc4a05ff700f95e09124d04ac4fef68a718b573` | 2371 bytes | `87f8d56887c61e7e709ba8f2003cb8d303ed68aa0c95190ba3ae6afc053952c4` |
| No-model-preflight PASS | `2739fd75b10cc2b9cf99461e45390b7cdd242085458ed602faa73af24ab90e7c` | 2326 bytes; 25/25 gates; 62 commands | `0d26792de1682ac013ae2e57fc7c4b6ab3cdd665b20ae7c68d74cac9157dae32` |
| Full-local-CI PASS | `d8cf4a6d3fce68d34d90014d72f092210d0daf89d6b1f47319bfbc2463b86609` | 2304 bytes; 172/172 commands | `a65ef9603fc18a6cd514fda952bccb8aa00840a63dea1f850b7ab00c86579367` |

The corrected authorization names this reviewer, binds the exact prospective
tree and source freeze, was issued at `2026-07-13T01:12:33Z`, and passes the
staged producer's `validate_review_authorization` function. The earlier malformed
authorization was superseded before use and remains preserved only as the
failed-attempt artifact with SHA-256
`13f541f311970bd8ff6e757308b382a70994af2a90dd2f5de2af0e8fe81c4062`.

The freeze's 3464 file records total 42287406 bytes and have manifest digest
`49980730ea403beb95151ffc8685fd76e3d980d192294684ef7a78297e3ad698`.
Every freeze path, byte count, blob OID, and raw SHA-256 was compared with the
prospective tree. The index equals that tree. The deterministic verdicts above
bind the same freeze and tree, record `model_calls=0`, and remain bounded,
nonterminal PASS receipts. Their PASS status does not override the findings.

## Important findings

### I1 - Reviewed-campaign custody accepts Windows root-relative escapes

Evidence:

- `tools/reviewed_campaign_orchestrator.py:150-166` rejects `Path.is_absolute()`
  and `..`, then joins the remaining parts to the custody root without verifying
  the final path is still relative to that root.
- On Windows, `Path(r"\\Windows\\Temp\\daee-escape.json").is_absolute()` and
  `Path("/Windows/Temp/daee-escape.json").is_absolute()` are both false, while
  joining either path to a drive-qualified root discards the custody suffix and
  resolves on the root's drive.
- The affected helper is used for referenced reads and create-once/atomic
  publications, including `tools/reviewed_campaign_orchestrator.py:197-216`,
  and throughout both reviewed-campaign lanes.
- `docs/captured-output-custody.md:5-9` states that absolute paths and custody
  escapes are rejected. The reviewed-campaign contract suite has no root-relative
  Windows canary; all 41 current tests pass despite this escape.
- Reviewed source hashes are
  `tools/reviewed_campaign_orchestrator.py` =
  `d7c1bbcf655fede269a2b1fde4362774b26b8ad276ee9bf88c03f5b3ad06528e`
  and `tests/reviewed-campaign-orchestration/test_contract.py` =
  `607f39d2243c41f9192121569110e0aa1500cfa2241a40fd3cc6e3662e3fc674`.

Bounded Windows probe, using a disposable temporary root and `must_exist=False`:

```text
root= C:\Users\theis\AppData\Local\Temp\tmp2fhhecbv
'\\Windows\\Temp\\daee-escape.json' absolute= False result= C:\Windows\Temp\daee-escape.json under_root= False
'/Windows/Temp/daee-escape.json' absolute= False result= C:\Windows\Temp\daee-escape.json under_root= False
'C:\\Windows\\Temp\\daee-escape.json' REJECT CampaignError PATH_CUSTODY_PROBE: path escapes custody root
'\\\\server\\share\\daee-escape.json' REJECT CampaignError PATH_CUSTODY_PROBE: path escapes custody root
```

The probe called the path resolver only; it did not create or modify the escaped
target.

Impact:

An otherwise schema-valid reviewed-campaign path controlled by an authorization,
reference, packet, claim, usage-ledger, incident, finalizer, or completion record
can escape the selected custody root on Windows. Read operations can consume
out-of-root bytes and publication operations can target out-of-root locations.
Hash checks do not restore the missing location boundary.

Required repair:

1. Apply one portable relative-path validator before joining, rejecting Windows
   rooted, drive-qualified, UNC, device, traversal, separator-alias, and ADS forms
   on every host.
2. After joining, prove the absolute lexical path is under the absolute custody
   root before any existence check, read, directory creation, or publication.
3. Preserve the existing symlink/reparse checks and fail closed on path-shape
   ambiguity.
4. Add direct Windows and cross-host canaries for `\\rooted`, `/rooted`, drive,
   UNC/device, ADS, traversal, and ordinary contained paths at every read/write
   owner boundary.

### I2 - A suffix-only local-CI run publishes a canonical complete PASS

Evidence:

- `tools/run_local_ci.py:337-341` documents `--start-at-command` as resuming at a
  1-based command index without replaying earlier green commands, but the command
  accepts no prior receipt and binds no evidence for those earlier commands.
- `tools/run_local_ci.py:446-472` always emits `status="PASS"` and
  `complete=true`; it sets `executed_count` to only the suffix length.
- `tools/run_local_ci.py:500-526` accepts that self-consistent completion as PASS
  without requiring `start_at_command=1`, `executed_count=command_count`, or
  `end_at_command=command_count`.
- `tools/run_local_ci.py:581-589` publishes the value through the CLI's
  `--json` surface, which is explicitly described at line 324 as the canonical
  completion report.
- The Task 7 writer and readback checker separately enforce a full 1-to-N run at
  `tools/write_task7_deterministic_evidence.py:339-349` and
  `tools/check_ci_readback.py:747-759`, so the current Task 7 full-CI receipt is
  not affected. The producer/parser and their public canonical JSON remain
  false-positive surfaces.
- Reviewed source hashes are `tools/run_local_ci.py` =
  `f948ad1e7c827fe799eada73ec354c3a8836f12be08546391af01882be4e9420`
  and `tests/ci-readback/test_contract.py` =
  `0598dd31f5231a5b2ffcb5063574c60d040c6a036e2c0f0ba87727557a9fe1a1`.

Bounded in-process probe over the exact 172-command list:

```text
build= {'status': 'PASS', 'complete': True, 'start_at_command': 172, 'executed_count': 1, 'command_count': 172}
parser_accepted= {'status': 'PASS', 'complete': True, 'start_at_command': 172, 'executed_count': 1, 'command_count': 172}
```

Impact:

Running only command 172 can produce an identity-valid canonical report that
claims complete PASS for a 172-command plan. A human or consumer using the
producer/parser directly can mistake an unbound suffix run for full-CI evidence.
The separate Task 7 checks reduce but do not remove this producer-level false
claim.

Required repair:

1. Either make suffix runs explicitly partial/non-PASS, or require a content-
   addressed prior completion receipt covering every skipped command and merge
   that evidence into the new report.
2. Make the completion schema and parser enforce the chosen full-versus-partial
   semantics rather than relying on selected downstream callers.
3. Add CLI-level canaries for `--start-at-command 2` and the final command,
   including `--json` readback and forged skipped-prefix evidence.

### I3 - Windows timeout teardown can silently abandon descendants or escape as an exception

Evidence:

- `tools/run_local_ci.py:249-266` invokes `taskkill /T /F` with a timeout. A
  nonzero `taskkill` result falls back to `process.kill()`, waits for and checks
  only the root process, then returns without any descendant verification.
- A `subprocess.TimeoutExpired` raised by the `taskkill` invocation itself is not
  caught. It bypasses the root fallback and propagates through
  `run_owned_command` at `tools/run_local_ci.py:313-317` instead of returning the
  tool's owned timeout result.
- `tests/ci-readback/test_contract.py:1028-1088` verifies successful real process-
  tree teardown, but there is no failure-path canary for nonzero or timed-out
  `taskkill`.

Bounded mock probe; no real process was signalled:

```text
taskkill_rc1_returned= True root_kill_calls= 1 wait_calls= 1
taskkill_timeout_exception= TimeoutExpired root_kill_calls= 0 wait_calls= 0
```

Impact:

If `taskkill` fails while the root is alive, descendants may remain able to
mutate the checkout while the runner reports ordinary timeout completion. If
`taskkill` itself times out, the runner crashes out of its structured timeout
path and does not even attempt the root fallback. Both outcomes violate the
owned-process-tree containment guarantee relied on by full local CI and the
no-model preflight runner.

Required repair:

1. Prefer an OS-owned Windows Job Object with kill-on-close semantics for every
   child process, or another primitive that provides verifiable descendant
   ownership and teardown.
2. Catch `taskkill` spawn/timeout/nonzero outcomes, attempt bounded cleanup, and
   fail closed with a distinct infrastructure/teardown result when descendant
   death cannot be proven; never return ordinary timeout success after root-only
   cleanup.
3. Add Windows failure-injection tests for `taskkill` nonzero, spawn failure,
   timeout, root wait timeout, and surviving descendant state, while retaining
   the current happy-path child/grandchild test.

## Verification performed

- Exact branch, HEAD, and index tree were checked before and after review.
- The complete 3464-file source-freeze manifest was replayed against the staged
  prospective tree; every path, blob, byte count, and raw SHA-256 matched.
- The corrected one-use authorization passed the staged producer's validator.
- All three existing deterministic verdict bundles were read back and remained
  exact-tree, exact-freeze, nonterminal, zero-model-call PASS receipts.
- `python -B tools/write_task7_deterministic_evidence.py --self-test`: PASS.
- `python -B tests/ci-readback/test_contract.py`: PASS, 45 tests.
- `python -B tests/no-model-preflight/test_contract.py`: PASS, 21 tests.
- `python -B tests/reviewed-campaign-orchestration/test_contract.py`: PASS, 41 tests.
- `python -B tests/candidate-build/test_contract.py`: PASS, 11 tests.
- No-model candidate-maturity suites: PASS, 21 and 15 tests.
- Evidence-retention suite: PASS, 27 tests with 6 Windows capability-dependent
  symlink tests skipped.
- Architecture-decision ledger: PASS, 1 valid / 5 invalid plus live check.
- Contract registry: PASS, 1 valid / 18 invalid plus live check.
- Closure ledger: PASS, 5 valid / 17 invalid plus live check.
- Generated docs freshness, staged docs projection, and generated source hashes:
  PASS.
- Strict parsing of all 188 staged JSON files: PASS with duplicate-key rejection.
- AST parsing of all 36 staged Python files: PASS.
- `git diff --cached --check`: PASS.
- The bounded probes above were diagnostic only, created no source artifacts,
  made no provider/model calls, and did not signal a real process.

The broad passing checks do not supersede the findings. I1 is a platform-specific
path interpretation gap absent from the campaign fixtures; I2 is accepted by the
producer/parser even though selected Task 7 consumers add a stricter check; and I3
is outside the existing successful-`taskkill` process-tree test.

## Explicit downstream nonclaims

This `REJECT` record is not evidence of and does not claim or authorize:

- a canonical Task 7 independent whole-branch review PASS verdict or JSON record;
- repair acceptance or review of a post-repair source identity;
- a successor commit, commit authorization use, push, or remote readback;
- external source receipt, external preflight, exact-SHA GitHub CI, or branch-
  protection satisfaction;
- immutable candidate construction, retention, maturity, readiness, or promotion;
- provider/model execution, reviewed five-smoke execution, cold review, or
  campaign success;
- tag, release package, release, publication, deployment, owner acceptance, or
  terminal closure of any A01-A16 row.

## Decision and required next gate

`REJECT` exact tree `a5a6f885f3e3a08a361c5e73f520a0d23c89ba39` for Task 7
whole-branch-review promotion.

Close all three Important findings with narrow, reviewed repairs. Because those
repairs change governed source and tests, create a fresh exact source freeze,
regenerate affected deterministic receipts, and obtain a fresh one-use review
authorization. A new independent whole-branch review of the repaired exact tree
is mandatory. Only a zero-Critical, zero-Important, zero-Minor result may create
the canonical review JSON and proceed to later gates.
