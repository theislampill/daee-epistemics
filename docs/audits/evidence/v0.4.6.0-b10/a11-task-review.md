# A11 independent whole-scope review

Status: Needs fixes. This is the outstanding second independent A11 review on
the stable live bytes at checkpoint HEAD
`43d1d98bf52bd61367496f527047c3dc00f089ae`.

Reviewed aggregate: 160 files, SHA-256
`d8d1c79c372b4ba66b4295daa4203ac75777a97a47ca8382b5eac82179fee43e`.
The reviewed file set and Git-status fingerprint were stable before/after.

## Findings

### Critical — checker execution custody freezes entry files only

`tools/verify_candidate_output.py` copies and verifies each checker entry file,
but its bootstrap resolves imported helper modules and data files from the live
logical source tree. Stage07 likewise invokes the live checker path. A complete
checker result can therefore describe the entry hash without proving that the
same frozen helper/resource bytes executed.

Required correction: add RED controls that replace a helper module and resource
while the live entry path remains stable, plus a Stage07 live-path control;
execute the whole local checker tree from one contained, hash-attested snapshot
for both candidate replay and Stage07.

### Important — exact required consumer set is not enforced

The registry validates only consumer rows that remain present. Removing any of
the canonical Stage07 runner, candidate verifier, or scorecard rows yields no
finding in either scan mode. The projection check also recognizes a matching
call syntactically without binding the canonical consumer source bytes.

Required correction: add deletion/addition/swap negatives; require the exact
three canonical consumer tuples; bind each source SHA-256; retain focused tests
that prove each owner consumes its projected plan.

### Important — duplicate-key canary is absent from local CI

The raw-byte duplicate-key registry canary lives in
`tests/validation-integrity/test_hardening.py`, while `tools/run_local_ci.py`
registers only the candidate, consumer-migration, and scorecard hardening
suites. The current wiring assertion preserves that omission.

Required correction: add `test_hardening.py` to the canonical local-CI command
set and its wiring assertion.

## Completed deterministic checks

- validation-integrity discovery: `55` passed, one Windows
  symlink-capability skip;
- registry self-test/live: `2` valid / `13` invalid and `18` checkers / `6`
  profiles;
- CI coverage self/live: all self-tests and `106` registered / `87`
  required-wired / `19` non-required;
- candidate verifier and scorecard self-tests: `3/3` each;
- staged handshake: `25` valid / `119` invalid.

Stable primary identities:

- `tools/validation_registry.py`
  `a3f3bc56242ae8bb1eb1c3509549fe4aded1a879423931f41c0556ca244246ba`;
- `tools/verify_candidate_output.py`
  `9b5ef68c0b4cfeb512e9006320af73bf60e2d056ad3b4eb485a7be1c2db65914`;
- `tools/validation-registry.json`
  `a194d0de9dca7981e6bd08fee8ee290a3364a664679d77519e38826304055554`;
- `schema/checker-replay-verdict.schema.json`
  `ff663054ff7bd5a4400ea8611c26df38039d5ff31b39567321f8fa0344b43620`;
- `tests/validation-integrity/test_hardening.py`
  `2deb1bbab1e8f9131a5a9fdd2345decea1c5190692eae87bdd732a4e70282a29`.

## Prior-finding disposition and nonclaims

The review closes the documented bounds of ANDON 71/72/74, 76, 77/80/87/91,
and 90. ANDON 88 remains open through required-consumer completeness; ANDON 89
remains open through missing durable CI registration; ANDON 92 remains open
through incomplete execution-tree custody.

This review does not approve A11, Phase 4, Stage08 promotion integration, full
local CI, package or release state, candidate maturity, or model-backed
validation.

## Owner repair candidate for final independent disposition

Status: stable, root-verified candidate; final independent A11 disposition
pending. Branch, HEAD, upstream, and remote-tracking checkpoint remain
`codex/v0.4.6.0-runtime-footprint-b10` at
`43d1d98bf52bd61367496f527047c3dc00f089ae`. The index is empty. The complete
working tree has 64 paths (33 modified, 31 untracked); the bounded A11 set below
has 23 files. No reset, discard, commit, push, model call, candidate launch, or
release action occurred.

The second-review findings have the following owner disposition:

1. Complete execution custody: candidate replay and Stage07 now execute checker
   entry bytes, local imports, schemas, and declared runtime resources from one
   contained, hash-attested execution tree. Both launch through the same
   isolated `-I -B` child bootstrap, which verifies the private entry hash
   before execution. Candidate output bytes are copied into the same private
   custody. All-entry replace/execute/restore, helper/resource replacement,
   child-entry swap, Stage07 private source/output, manifest mutation,
   destination escape, and supported symlink controls are permanent tests.
2. Exact consumer custody: the registry schema and semantic validator require
   exactly the canonical Stage07, candidate, and scorecard tuples and bind each
   source SHA-256. Deletion, addition, source swap, profile-projection, and
   source-drift controls are permanent tests.
3. Full canary registration: canonical local CI contains all four
   validation-integrity suites, including the strict duplicate-key suite.
   Registration readback reports 4/4 and the suites were executed sequentially.

The Python invocation scanner remains bounded to the explicit launcher,
interpreter-option, script/module, collection, alias, comprehension, and
process-sink forms encoded in the permanent consumer and CI-coverage matrices.
This disposition makes no general Python program-construction completeness
claim. Unknown pre-script interpreter forms fail closed under the registered
contract; broader language-completeness research is not an A11 acceptance
condition.

Sequential decisive evidence on these exact bytes:

- validation-integrity hardening: 12 passed, one Windows symlink-capability
  skip;
- candidate custody: 15 passed, one Windows symlink-capability skip;
- consumer migration/attestation: 22 passed;
- scorecard custody: 10 passed;
- validation registry self/live: 2 valid / 13 invalid and 18 checkers / 6
  profiles;
- CI coverage self/live: all 16 controls and 106 registered / 87
  required-wired / 19 non-required;
- candidate verifier and scorecard self-tests: 3/3 each;
- staged runtime handshake: 25 valid / 119 invalid;
- A11 Python compile, Git diff whitespace check, and 4/4 local-CI command
  readback: pass.

Every command used an explicit bound. Earlier tool-wrapper timeouts left seven
confirmed descendant test processes, one candidate-replay directory, and one
empty validation scratch directory. Only those attributed descendants and
paths were terminated/removed after absolute-path containment checks. Final
readback is zero active A11 test processes, zero candidate/Stage07 execution
directories, zero validation scratch directories, and zero owned bytecode
files.

Stable A11 identities (path, SHA-256):

- `docs/model-compliance-scorecard.md` `356eb647c72603aa52eefc1009fd88e8d441a5238e0d36516768bd4759f5518a`
- `docs/validation-registry-and-promotion.md` `d93cfadede6689a4760bf76d9cf15666f61cdf03afb99a0dad3606d1e31a942b`
- `schema/checker-replay-verdict.schema.json` `7d39ddfafb3e8128a04f77fd6e2887e4cdd51820fb81296fec9aef9c3d53e711`
- `schema/validation-registry.schema.json` `7fd93688a4bcc2cc4f74458ae2cdbdac3524296ba78ccc5e8c69c4d7367ac91c`
- `tests/validation-integrity/helpers/private_scorecard_consumer.py` `4bf0584f0fa706054b8bb040321334bbe0d6f416bbdfeac971a653138cb09f83`
- `tests/validation-integrity/test_hardening.py` `f4edbf7196e3888f77299969740eab7f96c4ed0da489dbff527b1da28dfa5148`
- `tests/validation-integrity/test_candidate_hardening.py` `79ce96969f18d66b7d66dc6c66c5a98759596fc17bd5955a24e1ae3b4199ad89`
- `tests/validation-integrity/test_consumer_migration.py` `c4f2c9bd39b5903e0975369766f0e467e503832abb217742c87ab7b88001a0e6`
- `tests/validation-integrity/test_scorecard_hardening.py` `ef1d8b50fa844d2b7c90e76d174827478264c36c0a5844527840751025ebcb61`
- `tests/validation-integrity/fixtures/candidate-source-custody/candidate_source_helper.py` `382ffdfcba6d73e044baeb25a6ac7843db2124ca21090af1e4972aec58c89f96`
- `tests/validation-integrity/fixtures/candidate-source-custody/competitor_checker.py` `96f8ce62d33afdefade99352f18f6a0e355e58dc39e41e1a1244e475e1fdaf93`
- `tests/validation-integrity/fixtures/candidate-source-custody/probe_checker.py` `7037a84ae1ed44a83e499ba5bdadbfbfd05cd959f01baf10ceebaa2de4d240f5`
- `tests/validation-integrity/fixtures/candidate-source-custody/probe_resource.txt` `3658a4189f0d5c038f20d4c92e82dd1266fc5a0e802a52c08ed1811388ca7b4f`
- `tools/build_model_compliance_scorecard.py` `97e228f8da55e3a14cad4228c105212a82932973332ca29a7fcb21954fd9216c`
- `tools/check_ci_registry_coverage.py` `3369685a714254dd7bd09d4e73ac247825722b7cc51a29db484cd512b8170c65`
- `tools/check_validation_registry.py` `af85031af425fc7248e354ee1962f7c266c53fd5b220221fb1536fbdedabbbbc`
- `tools/ci_registry.json` `67ab6eef7db07fcf70b14d68bdd7deb6550360ba1d4866e5f9ab5fa71d32af05`
- `tools/checker_execution_snapshot.py` `93695b0c88a69f20f297a62a0245d70983d699efe3bd7e9d4b91747893509813`
- `tools/run_local_ci.py` `3cb2d9e806b6f3a3a7baac0eedf8bade87f50b8ed614fe679265a51aa8fc1d47`
- `tools/run_staged_current_skill_smoke.py` `bc13e36d67dc2dfcbaea41d1dd1be854e7190e2bf6ffae7721a7dd476e0aa325`
- `tools/validation-registry.json` `6d5cf4cdc632d5251bf326fac90fca30949ab92f67bd614f93f53fbbd3240668`
- `tools/validation_registry.py` `de8540d757cbf74338d57e2afd407963919076adfc12e5d4c5d435b3863d37d0`
- `tools/verify_candidate_output.py` `0e5cf920a05c0e09cb8746cfc04872357cfe08741bd7b87199e4111d3a92264f`

Ordered 23-file aggregate SHA-256 (each row is path, one ASCII tab,
lowercase hash; rows are joined by LF with a final LF; UTF-8, no BOM):
`d0d87140aeec48b458ed3a0c17b82014a8f4a4cafe9fc8a23292cbb705733b0c`.
Complete 64-path Git-status fingerprint SHA-256:
`269000be420704a55cf6308d2bc28a3d4d109cbad63a92913e1eb1277ac73268`.

Nonclaims: final independent A11 approval, shared witness-role integration,
A12/A13 joins, full local CI, package/preflight closure, A16, candidate
maturity, release readiness, and terminal A01-A16/campaign success remain open.

## First final-review return and bounded repair

The final reviewer matched the prior 23/23 identities and aggregate, then
returned one Critical finding and no Important/Minor findings: canonical
checker imports read runtime resources under `atomics/skill`, but the private
tree copied only `tools`, `schema`, and declared resources while canonical
checker rows declared none. A real canonical replay therefore produced eight
infrastructure-class results even though the probe-substitution custody test
passed.

The exact RED was added before repair and reproduced all eight unsupported
results. The canonical twelve captured-output checker rows now declare
`atomics/skill` as their runtime resource; snapshot creation copies and attests
that complete 145-file, 2,593,209-byte runtime tree once. Permanent positives
execute the real canonical candidate plan and a real canonical Stage07 checker
from custody, reject traceback/missing-resource diagnostics, and prove the
delta-result vocabulary resource is present. Scratch-root construction now
copies the same declared resources instead of weakening the production
contract.

Post-repair sequential evidence is the updated 12/15/22/10 suite set above;
registry self/live, candidate/scorecard self-tests, and handshake 25/119 are
green. The final readback remains 64 working-tree paths, 33 modified, 31
untracked, empty index, zero A11 descendants, and zero candidate/Stage07/scratch
temporary directories. Final independent re-review of the updated aggregate is
pending; all earlier nonclaims remain in force.

## Final independent disposition

Verdict: Approved. The final independent reviewer reported zero Critical, zero
Important, and zero Minor findings for the bounded A11 contract.

The reviewer independently matched 23/23 file hashes and the explicit
tab/LF aggregate
`d0d87140aeec48b458ed3a0c17b82014a8f4a4cafe9fc8a23292cbb705733b0c`.
It verified that all 12 captured-output and all 11 Stage07 checker rows declare
the private `atomics/skill` runtime tree; exact three-consumer source/profile
attestation remains enforced; and all four validation-integrity suites remain
registered in canonical local CI. Its bounded rerun passed the real canonical
candidate resource test, the real canonical Stage07 resource test, and live
registry validation at 18 checkers / 6 profiles.

A11 is therefore bounded-approved on these exact bytes. Shared runtime/witness,
A12/A13, package/preflight, full local CI, A16, exact-SHA CI, candidate maturity,
five-smoke, release, and every terminal A01-A16 status remain open. The tracked
dimensional closure ledger must not fabricate a pre-commit blob identity for
these dirty bytes; its A11 source-blob refresh remains a successor-checkpoint
join while all terminal dimensions stay OPEN.

## Canonical staged-byte follow-up and successor checkpoint

The commit gate found that Git's configured text normalization changed only
the line endings of `tools/check_ci_registry_coverage.py` and
`tools/run_staged_current_skill_smoke.py` between the reviewed worktree and the
canonical index. The final reviewer independently matched every staged blob,
read the index twice without drift, and proved the normalized byte streams,
Python tokens, and ASTs (including constant values) were identical. It
Approved the exact staged 23-path aggregate
`07bed966e252df64c3b84040dd13b903dfe3797dc0feef7ca2c54b9c4aebc851`
with zero findings. This replaces the raw-worktree aggregate only for canonical
repository-byte identity; it does not widen the bounded A11 contract.

The 70-path checkpoint boundary had tree
`f9f9e4806832fa9bab13ff255d37eee554d032e8`, binary staged-patch SHA-256
`675e78c4494d6c2ba0cd199ec51129fa095770ff34d191e6d5b85ef5fe19202c`,
and passed source-clean, staged-diff, high-signal secret, suspicious-filename,
conflict-marker, and review gates. Separate exact one-use commit and push
artifacts were consumed. The ordinary non-terminal commit
`484e61c9c2af30ed3f9e3c5c98551a7973a9417f` was pushed without force to the
matching Branch 10 ref, and exact remote readback matched that SHA. Durable
artifacts are `vcs-commit-authorization-a11-successor.json`,
`vcs-commit-receipt-a11-successor.json`,
`vcs-push-authorization-a11-successor.json`, and
`vcs-push-receipt-a11-successor.json` in the run root.

This is a WIP durability checkpoint, not terminal A11/A01-A16 closure,
Phase 7 exact-SHA CI, candidate maturity, campaign success, or release
readiness. The next active lane is the already-scoped current-versus-historical
witness-role integration.
