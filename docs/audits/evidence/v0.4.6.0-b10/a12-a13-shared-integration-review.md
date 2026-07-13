# A12/A13 and shared-integration final review

Scope: the complete post-checkpoint source byte set for the A12 runtime-call-context adapter and staged-runner joins, A13 package/harness parity joins, current-versus-historical witness-role integration, bounded local-CI repairs, and no-model preflight integration. This review does not cover A16 implementation, model execution, candidate maturity, terminal A01-A16 closure, tagging, merging, or release publication.

## Freeze revision 1 — REJECTED

Independent reviewer `/root/a12_a13_final_review` matched all 28 source hashes, all seven evidence hashes, and aggregate `3459a0feeff2a59ce7448311129b0880c08a719560ddcde692874d4abf1b46d3` before testing. The reviewer returned `REJECT` with one Important finding: command 68 was RED because `tests/andon-closure-ledger/invalid/stale-evidence-head.expectation.json` still required the pre-repair boundary after command 109 changed the canonical ledger `source_head`.

Every other bounded reviewer check passed, the reviewer reconfirmed the aggregate after testing, and no scoped child process or owned temporary residue remained. Freeze revision 1 must not be used for a checkpoint or approval claim.

## Exact root repair

Only the stale-evidence expectation was changed. Its current SHA-256 is `bf229b25f9a3f360200602523e0b1b69de82bb50d29ae2fee0f55aaa06b8ee81` over 870 bytes. The expected diagnostic marker now matches the canonical ledger's declared Branch 10 boundary `484e61c9c2af30ed3f9e3c5c98551a7973a9417f` while retaining the intentionally wrong all-zero fixture value.

Sequential post-repair evidence:

- command 68, `check_andon_closure_ledger.py --self-test`: PASS, 5 valid and 17 invalid;
- command 109, `check_andon_closure_ledger.py`: PASS on the canonical ledger.

No broader parser, ledger, runner, or registry redesign was performed.

## Freeze revision 2 — APPROVED

The replacement machine-readable manifest is `reviews/a12-a13-shared-integration-freeze.json`. It contains 29 exact source paths and seven evidence hashes. Ordered aggregate SHA-256, using the canonical path/TAB/hash/LF recipe recorded in the manifest:

`4e16e6ee2184d4ce0a50cdacaf7007a400f0a0336a0a2fafde89281f99b0b8b6`

All A01-A16 terminal states remain OPEN. Stage02 support remains v1 same-run immediate transport only; v2 and A16 remain unstarted. No model, candidate, release, merge, or tag claim is made.

Fresh independent reviewer `/root/a12_a13_rereview` matched all 29 source hashes, all seven evidence hashes, byte counts, the empty index, the unchanged dirty-path set, and aggregate `4e16e6ee2184d4ce0a50cdacaf7007a400f0a0336a0a2fafde89281f99b0b8b6` before review and again after testing.

Verdict: **APPROVE**. Findings: Critical `0`, Important `0`, Minor `0`.

Independent decisive evidence included:

- commands 68 and 109 PASS, plus an independent all-zero-head rejection at exact class `stale_evidence_head` and exit `1`;
- commands 69 and 70 self-tests and live ledgers PASS;
- replacement command 139 PASS on the static current public-graph fixture, with exact 7,503-byte equality to the runner-generated fixture;
- runtime-call adapter `11/11`, runtime-context delivery `12/12` plus `10` valid / `29` invalid / `1` Windows capability skip, producer parity `12/12` plus live registry, package parity `10/10`, prompt-pack budget `19/19`, and current witness-role `36/36` PASS;
- historical closure-witness contract PASS; validation registry self/live PASS at `18` checkers / `6` profiles; CI registry self/live PASS at `106` registered / `87` required-wired / `19` non-required; no-model preflight contract `7/7`; and `git diff --check` PASS;
- no scoped process, owned `.daee` residue, or review-created temporary fixture remained.

The reviewer confirmed that Stage01/02 A12 and A13 checks occur before dispatch; Stage02 accepts only same-run immediate `capsule-001.json` v1 lineage; v2 remains rejected pending A16; harness-assisted evidence remains non-promotional; and current and historical witness roles retain separate contracts. Twelve of the nineteen earlier approved witness paths retained their exact hashes; all seven intentionally evolved paths were reviewed at their revision-2 hashes.

The reviewer did not replay all 148 local-CI commands, the long staged-runner self-test, or the complete 17-gate preflight. Their recorded evidence hashes remained exact, and all governing bounded checks were rerun. This approval closes only the bounded shared-integration review gate; every A01-A16 terminal row remains OPEN and later exact-SHA CI, A16, model, candidate, and release gates remain outside this verdict.

## Canonical index review — APPROVED

After exact staging, 29/29 paths reproduced staged aggregate `cbf529dbe405793636856f7c418c75ccfc1b4d9defe3e5ac199cb74715acb1be`, index tree `7238bb567209003adb9b07cb0ec2d1629780cc2e`, and full-index patch SHA-256 `58e7dcd6c2b11ea477e1036d4b15d48dde4d07c1f3e1b0960f486604445de7b3`. Seventeen paths matched reviewed worktree bytes exactly; twelve Python paths were canonicalized from CRLF to LF with exact normalized bytes, token streams, and ASTs.

Independent reviewer `/root/staged_byte_review` reproduced every staged blob/hash/byte count and the worktree aggregate before and after review, found no unstaged or untracked source, conflict marker, credential signature, suspicious path, boundary drift, or unintended file, and returned APPROVE with zero Critical, Important, or Minor findings. These exact index bytes—not the raw worktree encodings—are the commit boundary.

## Successor checkpoint receipt

The separately authorized ordinary commit and non-force push completed at exact SHA `bcccb4e34c75e1f8e363ef020e2deeaabae60435`, parent `484e61c9c2af30ed3f9e3c5c98551a7973a9417f`, and tree `7238bb567209003adb9b07cb0ec2d1629780cc2e`. Local HEAD, upstream, and live remote Branch 10 ref matched exactly; ahead/behind was `0/0` and the nonignored source checkout was clean. Receipts are `vcs-commit-receipt-a12-a13-shared-integration.json` and `vcs-push-receipt-a12-a13-shared-integration.json`.

This is a non-terminal WIP durability checkpoint. It does not start A16, prove pushed exact-SHA CI, authorize model execution, mature a candidate, or permit merge, tag, release, or publication.
