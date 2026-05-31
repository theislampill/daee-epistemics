# Session Orchestration

Created: 2026-05-31

Status: active orchestration policy and session map for post-v0.4.3.x
IMPLEMENTAUDIT work.

Canonical records remain:

- `docs/audits/v0.4.3.0-implementaudit-orchestrator.md`
- `docs/audits/v0.4.3.0-open-work-ledger.md`
- `docs/audits/v0.4.3.x-target-row-status.md`
- per-lane audit docs under `docs/audits/`
- git commits and CI/Pages runs

Codex chat/session UI state is not canonical. Graphify remains a read-only
navigation aid. ActiveGraph remains an ignored local experimental sidecar for
orchestration/custody metadata only, never proof.

## Tooling Boundary

The currently exposed Codex lifecycle tool surface is limited but usable for
fresh bounded scout sessions. Tool discovery has exposed `spawn_agent`,
`wait_agent`, `send_input`, `resume_agent`, and `close_agent`; it has not
exposed reliable session list, read, rename/title, hidden-sidebar inventory, or
archive/delete controls in this run.

Therefore:

- session names below are the required naming convention for any session that is
  created by the available tool surface or renamed by a future tool surface;
- this file is the tracked session map until stronger lifecycle tools are
  available;
- no hidden UI session rename is claimed;
- no session deletion is allowed;
- fresh scout/verification sessions may be closed after their reports are
  integrated; historical D.8 cleanup still requires exact ID approval where
  required;
- existing historical sessions from D.8 remain governed by D.8, not this file.

## Session Classes

### A. Managing Session

Name pattern: `MGMT-<goal-or-release-line>`.

Responsibilities:

- own the current goal and proof-ledger integrity;
- select exactly one implementation lane at a time;
- assign read-only scout sessions;
- integrate reports into the open ledger/orchestrator;
- own file-family locks, failure classification, commits, pushes, and CI
  monitoring under standing authorization;
- stop at protected boundaries.

Must read before acting:

- `AGENTS.md`
- `docs/audits/v0.4.3.x-target-row-status.md`
- `docs/audits/v0.4.3.0-open-work-ledger.md`
- `docs/audits/v0.4.3.0-implementaudit-orchestrator.md`
- this file

Close/archive rule: never archive while the active goal remains open.

### B. Scout Session

Name pattern: `SCOUT-<row-or-lane>`.

Responsibilities:

- read-only investigation of one ledger area;
- produce a short lane recommendation with files inspected, commands run,
  evidence, risks, and next action;
- classify whether work is docs-only, no-model checker/fixture, retained-corpus
  accounting, owner-decision prep, or protected-boundary work.

Forbidden:

- patch, stage, commit, push;
- package, tag, upload, release, or provenance;
- A.13 follow-on implementation;
- D.8 cleanup;
- model-smoke or broad smoke campaigns.

Close/archive rule: may be closed only after its report is summarized or
linked in the orchestrator/open ledger. Preserve if it contains unresolved
findings, failing checks, owner questions, or possible unmerged work.

### C. Implementation Session

Name pattern: `IMPL-<row>-<slice>`.

Responsibilities:

- work one named lane only;
- patch only the owner/source files named by the managing session;
- run IMPLEMENTAUDIT Smoke A before mutation and Smoke B after mutation;
- produce commit-ready evidence and stop at protected boundaries.

Forbidden:

- parallel mutation in the same dirty worktree;
- broad row rewrites outside the selected lane;
- model-smoke campaign unless explicitly authorized;
- package/tag/upload/release/provenance;
- A.13.2 or later implementation without explicit owner approval.

Close/archive rule: may be closed after the managing session verifies the diff,
checks, ledger update, and commit/push/CI status, or after it is explicitly
deferred/blocked.

### D. Verification Session

Name pattern: `VERIFY-<claim-or-boundary>`.

Responsibilities:

- read-only verification of changed files, check outputs, docs freshness, CI,
  Pages, retained corpus, manifests, or sidecars;
- run tests/checkers where authorized;
- report pass/fail and coverage limits.

Forbidden:

- patching unless promoted by the managing session into a named implementation
  lane;
- release/provenance/package actions;
- treating Graphify or ActiveGraph as proof.

Close/archive rule: may be closed after verification output is preserved in the
orchestrator/open ledger or final report.

### E. Archive / Cleanup Session

Name pattern: `ARCHIVE-D8-<exact-scope>`.

Responsibilities:

- D.8 or session-lifecycle cleanup only;
- verify exact IDs against the preserved inventory;
- report what is safe to close/archive and why.

Forbidden:

- close/delete/archive without exact owner-approved IDs;
- touching `PRESERVE`, `POSSIBLE_UNMERGED_WORK_DO_NOT_CLOSE`, or unknown rows;
- deleting evidence;
- source/runtime/checker/release edits.

Close/archive rule: exact-ID approval is required before any cleanup action.
Deletion is forbidden unless separately and explicitly approved by exact ID.

## Naming Convention

Use concise, row-first names:

- `MGMT-post-v043x-goal`
- `SCOUT-B-sidecar-residuals`
- `SCOUT-D3-mixed-concealment`
- `SCOUT-C5-C7-matrix`
- `SCOUT-A13-follow-on`
- `SCOUT-ledger-truthfulness`
- `IMPL-D3-MM2-loaded-label`
- `IMPL-D3-next-no-model`
- `VERIFY-ci-pages-boundary`
- `ARCHIVE-D8-approved-ids-only`

If the UI exposes a different display title than the tracked name, record both
in this file or the orchestrator. Duplicate display names must be distinguished
by exact ID/session.

## Active Session Map

| Session | Class | Ledger Area | Permission | Status | Close/Archive Rule |
|---|---|---|---|---|---|
| `MGMT-post-v043x-goal` | Managing | All open rows; final row selection | May mutate only the selected lane; may commit/push ordinary docs/source/checker work under standing authorization | Active current session | Never archive while goal remains open |
| `SCOUT-ledger-truthfulness` | Scout | target-row status, open ledger, orchestrator | Read-only; may run `rg`, `git status`, docs checks | Candidate session; local fallback in use when creation/list tools are unavailable | Close after stale findings are preserved or rejected |
| `SCOUT-D3-mixed-concealment` | Scout | D.3 residuals, concealment fixtures/checker | Read-only; no model smokes | Candidate session; recent MM-2 lane closed by managing session | Close only after recommendation/evidence is in orchestrator |
| `SCOUT-B-sidecar-residuals` | Scout | B.1/B.2/B.4/B.5 retained sidecars | Read-only; no sidecar mutation | Candidate future scout | Preserve if it identifies retained-corpus drift |
| `SCOUT-C5-C7-matrix` | Scout | restoration-recoil/two-track/divergence-curl breadth | Read-only; no new cases/model smokes | Candidate future scout | Preserve if it identifies missing case-family proof |
| `SCOUT-A13-follow-on` | Scout | A.13.2+ decision prep only | Read-only design; no implementation | Candidate future scout; owner approval required before any A.13.2 implementation | Preserve until owner decision is recorded |
| `VERIFY-ci-pages-boundary` | Verification | CI/Pages after commit/push | Read-only checks; no patch unless promoted | Used as a role by managing session after pushes | Close after run IDs and status are recorded |
| `ARCHIVE-D8-approved-ids-only` | Archive/Cleanup | D.8 exact-ID cleanup only | No action unless exact IDs approved | Not active; D.8 safe subset already closed at spawn-edge level | No close/archive/delete beyond exact owner-approved IDs |

## Current Exposed Agent Inventory

The current environment exposes the prior D.8 evidence agent plus the fresh
read-only scout agents from the 2026-05-31 post-v0.4.3.x scout refresh:

| Agent ID | Visible Name | Current Use | Rule |
|---|---|---|---|
| `019e7e9e-eed7-7712-8317-61ad892d2355` | Averroes | Prior D.8 read-only refresh evidence cited in target-row status | Preserve as evidence source; do not close/delete/archive without D.8 exact-ID approval |
| `019e8004-5c45-78f3-9cc1-47116247f54d` | Kuhn | `SCOUT-ledger-truthfulness`; found docs-only truthfulness drift | May be closed after integration; no source changes |
| `019e8004-7d1d-79a1-acd8-811c7b160628` | Ptolemy | `SCOUT-D3-mixed-concealment`; identified fixture 62 as D.3-adjacent owner-decision candidate and AS/MM static slices as already closed | May be closed after integration; no source changes |
| `019e8004-9f59-7f13-86c1-66859ed5f7c8` | Fermat | `SCOUT-B-sidecar-residuals`; identified canonical coverage-target pinning as the next no-model sidecar/accounting candidate; later implemented by commit `8a69d51511421ae57e473d2b3635dbb7a6c83930` | May be closed after integration; no source changes |
| `019e8004-c013-74b0-b0bb-3d3707b75b4c` | Peirce | `SCOUT-C5-C7-matrix`; confirmed current retained matrix closure for the named schema-light target set | May be closed after integration; no source changes |
| `019e8004-ed90-7993-801e-33c5017ebcaa` | Nietzsche | `SCOUT-A13-follow-on`; confirmed A.13 follow-on remains owner-gated | May be closed after integration; no source changes |

Historical 475-row D.8 inventory remains governed by
`.daee/thread-audit/20260530-131739/subagent-sidebar-inventory.{json,md}` and
the D.8 row. This map does not reclassify or supersede those rows.

## Output Integration

Every scout, implementation, verification, or archive session must return a
bounded report that can be folded into the canonical ledgers:

- verdict;
- files inspected;
- commands run;
- findings table;
- required patches;
- required fixtures/canaries;
- what closes;
- what remains;
- next smallest safe action.

The managing session integrates accepted findings into:

- `docs/audits/v0.4.3.0-implementaudit-orchestrator.md`;
- `docs/audits/v0.4.3.0-open-work-ledger.md`;
- `docs/audits/v0.4.3.x-target-row-status.md` when row status changes.

Graphify links remain candidate navigation until verified with live files,
checkers, fixtures, smoke artifacts, hashes, command output, or orchestrator
evidence.

## ActiveGraph Event Policy

ActiveGraph may record local ignored sidecar events for:

- `session.created`;
- `session.renamed`;
- `session.assigned_ledger_row`;
- `session.reported`;
- `session.integrated`;
- `session.closed`;
- `session.archived`;
- `session.preserved`;
- `commit.recorded`;
- `push.recorded`;
- `ci.recorded`;
- `pages.recorded`;
- `andon.recorded`;
- `owner_decision.recorded`.

ActiveGraph remains:

- ignored local sidecar under `.daee/activegraph/<timestamp>/`;
- non-proof;
- non-canonical;
- not a runtime dependency;
- not a CI dependency;
- not a release/provenance/package dependency;
- not a replacement for the open ledger or orchestrator.

## D.8 Safety Rules

D.8 governs historical subagent/sidebar cleanup:

- the preserved inventory records 475 recovered rows;
- 16 exact `SAFE_TO_CLOSE_LATER` IDs were owner-approved and already closed at
  spawn-edge level;
- 318 `PRESERVE` rows must not be deleted;
- 141 `POSSIBLE_UNMERGED_WORK_DO_NOT_CLOSE` rows must not be deleted;
- unknown sessions must be preserved until classified;
- cleanup beyond the approved 16 IDs requires a future promoted D.8
  archaeology lane and exact owner approval;
- deletion is forbidden unless separately approved by exact ID.

This session policy does not authorize D.8 cleanup. It only prevents future
agents from confusing lifecycle management with deletion permission.

## Current Next-Lane Priority

The managing session chooses exactly one lane using this priority:

1. docs/ledger truthfulness if stale;
2. no-model checker/fixture hardening;
3. retained-corpus/accounting hardening;
4. A.13.2 decision packet, not implementation;
5. broader model-smoke work only with explicit authorization.

Current lane state after the later 2026-05-31 follow-up: docs-only ledger and
session truthfulness was committed/pushed, and the B-sidecar canonical
coverage-target pinning candidate was implemented for all 11 current target
IDs. AS-8/MM-2/MM-5/MM-7/MM-8 static D.3 slices remain source-boundary covered;
fixture 62 remains a D.3-adjacent owner-decision candidate; and A.13 follow-on
implementation remains owner-gated. No new implementation session is opened by
this policy document itself.

Post-sidecar checkpoint after commit
`e651756bc210e764b1c8a112eac6c216f20d642d`: read-only scouts Galileo
(`019e8032-437a-7320-8e5c-7172e7010d2a`) and Aquinas
(`019e8032-71a9-7240-8e62-465a3c4d0ed5`) reported no actionable stale wording
and no owner-free no-model residual lane. The managing session should not open
a new implementation session until the owner accepts fixture 62 as
D.3-adjacent, opens later A.13/full-IR work, promotes D.8 archaeology, approves
broad governed/model matrix work, or names another concrete residual with owner
files.

Fixture 62 decision prep now exists at
`docs/audits/v0.4.3.x-fixture62-d3-adjacent-decision-packet.md`. It is a
docs-only owner-decision packet, not an implementation session and not approval
to patch D.3.

## Boundaries

This policy does not authorize:

- package build;
- tag creation or movement;
- upload;
- GitHub release creation/update;
- release/provenance;
- release-asset edits;
- A.13.2 or later implementation;
- full IR decode;
- D.8 cleanup beyond exact approved IDs;
- model-smoke campaigns;
- parallel file mutation;
- session deletion/archive without exact approval.
