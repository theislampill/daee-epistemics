# Release Gate Ledger

> Plan 06, Phase 1 deliverable. Twelve release-custody gates, each with an
> authorization state, a performed state, an evidence command, a result, and
> remaining risk. This ledger is a custody record, not a release: a green source
> lane does NOT certify semantic correctness, interlocutor uptake, arbitrary-input
> behavior, or cross-host reproduction, and nothing here authorizes a build, tag,
> publication, provenance claim, or branch-protection change.
>
> **Authorization:** `authorized?` is set only by the owner. Gates 6, 7, and 12
> are never executable by an agent. Owner decisions for gates 6, 7, 11, and 12
> are queued and adjudicated via Plan 19 (owner decision queue). No row inherits
> status from the closure ledger, which under-reports (Annex 20 §4).
>
> **Deviation from the Plan 06 Phase 1 initializer (recorded):** the plan
> pre-dates the Plan 18 worktree green-state repair and instructed gate 1 to read
> `BLOCKED-ON-PLAN-18`. Plan 18 has since landed as a committed local series on
> `codex/hardening-all-20260703`, and `python tools/run_local_ci.py --strict-pwsh`
> exits 0 this session — so gate 1 (and the locally-verifiable gate 2) are
> recorded as PASS with an embedded transcript rather than as a stale blocker.
> Gates 3-12 remain `no` / `UNVERIFIED` / owner-gated.

## Gates

| # | Gate | authorized? | performed? | Evidence command | Result | Remaining risk |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Source validation | n/a (local check) | yes | `python tools/run_local_ci.py --strict-pwsh` | PASS — `run_local_ci: PASS (84 commands)`, exit 0, 2026-07-04, HEAD on `codex/hardening-all-20260703` (Plan 18 closed) | Structural/checker-replay only; not semantic correctness |
| 2 | Generated runtime freshness | n/a (local check) | yes | `python tools/check_compiled_runtime_freshness.py` + `git diff --exit-code -- skill/SKILL.md` | PASS — both in the gate-1 battery, exit 0, 2026-07-04 | Freshness is byte-identity of the compiled runtime, nothing more |
| 3 | Package build | no | no | `python tools/package_skill.py build/daee-epistemics-<v>.skill.zip` | UNVERIFIED — build not run in this local pass | Build is execution-time; no package produced |
| 4 | Package checksum | no | no | `Get-FileHash -Algorithm SHA256 <pkg>` vs `docs/release-artifacts.md` row | UNVERIFIED — depends on gate 3 | No package to hash |
| 5 | Local package install smoke | no | no | `python tools/check_skill_package_artifact.py <pkg> --expect-version <v>` + `python tools/check_compiled_skill_self_contained.py --package <pkg>` | UNVERIFIED — depends on gate 3 | Install path unexercised |
| 6 | Tag creation | OWNER | no | `git ls-remote origin "refs/tags/<v>^{}"` | OWNER-DECISION PENDING (Plan 19) | Never agent-executable; not authorized this pass |
| 7 | Release publication | OWNER | no | `gh release view <v> --repo theislampill/daee-epistemics --json tagName,assets,publishedAt` | OWNER-DECISION PENDING (Plan 19) | Never agent-executable; not authorized this pass |
| 8 | Release asset readback | no | no | `gh release download <v>` + hash compare | UNVERIFIED — no network this session (Annex 20 §6) | No published asset to read back |
| 9 | Provenance pair verification | no | no | `python tools/check_release_provenance.py --provenance <dl>.provenance.json --package <dl>.skill --manifest skill/build-manifest.json --compiled-map skill/compiled-module-map.json` | UNVERIFIED — depends on gates 3/8 | Output-side provenance binding unexercised |
| 10 | Pages / docs readback | no | no | `gh api repos/theislampill/daee-epistemics/pages` + live URL fetch | UNVERIFIED — no network this session | Pages state unknown |
| 11 | Branch-protection / ruleset readback | OWNER | no | `gh api repos/theislampill/daee-epistemics/branches/main/protection`; `.../rulesets`; `.../rules/branches/main` | OWNER-DECISION PENDING (Plan 19) — no authenticated `gh` session this pass; do NOT infer "unprotected" from a 403 | Live protection state unverified (Annex 20 §6) |
| 12 | Large-artifact custody decision | OWNER | no | Plan 06 Phase 3 decision packet | OWNER-DECISION PENDING (Plan 19) | 8 MB tracked `docs/audits/v0.4.1.0-history-regression-scan.json` custody unresolved |

## Notes

- Gates 1-2 are the only gates verifiable in a local, no-network, no-spend pass;
  their PASS is the source-validation precondition for a future release, not the
  release itself.
- Gates 3-5 and 8-10 are UNVERIFIED because they require an execution-time build
  or network access, neither performed here.
- Gates 6, 7, 11, 12 are owner decisions; they are recorded PENDING and routed to
  Plan 19. No mutation, tag, publication, or protection change was performed.
