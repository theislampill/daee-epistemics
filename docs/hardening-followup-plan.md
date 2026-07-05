# Hardening Branch — Follow-Up Plan (remaining gated items)

> Companion to `docs/hardening-pr-handoff.md`. That ledger records the terminal
> state of every plan; this document turns each remaining **terminally-gated**
> item into an executable follow-up plan the next implementer can pick up. It is
> a planning artifact: the safe-local slices it scoped were subsequently
> **implemented or terminally gated** in the 2026-07-04 completion pass (see the
> status note below and `docs/hardening-pr-handoff.md`); the remaining lane recipes
> stay valid for the owner/external/spend/artifact-gated escalations. No external
> action (push, PR, tag, release, publication, spend) is authorized by this doc.
>
> Method: produced by a read-only, multi-agent audit pass (one reader per lane
> plus a completeness/owner-directive critic). Every cited path and function was
> read in the worktree; the critic confirmed all lanes are structurally complete,
> reopen no closed lane, change no runtime behavior, and reintroduce **no**
> dual-use / safety-policy / refusal-runtime infrastructure (the removal at
> commit `455a921` stays in force). Where this doc and the code disagree, the
> code wins. The North Star (skill-as-code, typed staged DSL/IR, public
> projection, sidecar eligibility, auditability) is architectural framing only;
> the current checkout and ledger override it.

## Completion-pass status (2026-07-04)

The safe-local completion pass implemented or terminally gated every lane here.
**Landed** — Plan 16 decisions (`2d5216c`), Plan 08 decision (`1d35a46`), Plan 17
D3 quarantine (`3db753a`), Plan 06 token contract (`2b323e4`), Plan 09 spike plan
(`fadb4a6`), Plan 15 record-only surfacing (`061ddbe`), Plan 03 envelope generator
(`76f4cd1`). **Terminally gated** — Plan 11 checker move (OWNER-GATED dedicated PR;
release/CI-facing blast radius). The per-lane recipes below remain the executable
reference for the still-gated escalations (Plan 03 Phase 4/5, Plan 06 generify/retire
code, Plan 08 adoption, Plan 11 move, Plan 15 verdict/schema/multi-site, Plan 16 root
slim, Plan 17 enforcing check). Final terminal state per plan: `docs/hardening-pr-handoff.md`.

## Gate classes

- **OWNER-GATED** — needs an owner decision (semantics, layout, or an evidentiary
  claim) before code follows.
- **EXTERNAL-GATED** — needs an authenticated external action (branch-protection,
  tag, publish, the PR itself). Never agent-executable.
- **ARTIFACT-GATED** — needs a new artifact materialized first.
- **A/B-GATED** — needs a measured before/after proof against the retained corpus.
- **SPEND-GATED** — needs a paid/hosted model or host run.
- **NOT-SAFE-TO-BUILD** — a naive discriminator overmatches; only a measured,
  non-overmatching variant may ship.

The consistent shape of every "smallest safe first slice" below: because each big
item is gated, the first slice is the **read-only / docs-only / additive
observability step that makes the gated decision executable** — never the gated
action itself. New measurement/generator tools are named `measure_` / `analyze_` /
`build_` / `spike_` so they stay **outside** the `check_*.py` wired-iff-required
invariant enforced by `tools/check_ci_registry_coverage.py` and cannot force a new
required CI gate.

## Master map

| Lane | Gate on the remaining item | Smallest safe first slice | Sequencing |
| --- | --- | --- | --- |
| 16 terminal-cover A/B | A/B (retained-corpus regression) + owner (root slimming) | `tools/measure_terminal_cover_ab.py` read-only 24-case delta harness + snapshot doc | Before merge — LANDED `0788b21` |
| 08 CI parallelization | owner (phase-staging + abort policy) | pure `benchmark_summary()` helper + self-test (doc-count fix already landed) | Before merge — LANDED `1cf82c6` |
| 15 normalizer-transparency | owner (verdict/schema) + spend (live capture) | additive `route_state_repairs` field in `write_hash_record` + classification table, byte-identity proof | After merge (own PR) |
| 03 field-witness envelope | artifact (envelope) + owner (`binding_status`, cert rev) | `tools/build_field_witness_envelope.py` generator (writes nothing by default) + decision packet | After merge (own PR) |
| 06 release de-stale | owner (release-body semantics) + external (branch-protection/tag/publish) | `docs/release-body-contract.md` inventory + token classification, awaiting sign-off | Later release |
| 17 owner/TTP contract | owner (operation-token canonicity) | `docs/audits/owner-contract-operation-token-drift-inventory.md` (D3 computed inventory) | Later release |
| 11 checker package extraction | owner (package layout) | `docs/audits/plan11-package-extraction-impact.md` impact analysis | Later release |
| 09 semantic-replay | not-safe (overmatch) + owner/spike + spend | `docs/semantic-replay-spike-plan.md` + advisory `spike_*` FP harness | Later release |

## Discovered during this planning pass

The deeper read surfaced work the earlier "folder exhausted" sweep missed:

1. **One real doc-drift defect — now fixed.** `docs/audits/ci-parallelizability.md`
   reported 88 commands / 82 read-only; the live battery was 89 / 83 at that commit
   (verified with `run_local_ci.py --list` and `analyze_ci_parallelizability.py`), and
   is now 91 / 85 after the Plan 16 and Plan 03 slices added read-only commands.
   Corrected in commit `22e5673` (`plan08: correct stale ci-parallelizability command
   counts`); classification and verdict unchanged.
2. **Two buildable before-merge slices — now landed strict-CI-green.** Plan 16
   terminal-cover A/B harness (`tools/measure_terminal_cover_ab.py`, `0788b21`) and
   Plan 08 pure `benchmark_summary()` helper (`1cf82c6`), both docs/measurement/
   pure-function only, no runtime change. A subsequent read-only exhaustion sweep
   (8 lanes + a strict adjudicator) then returned **all_safe_local_exhausted =
   true**: no further safe-local slice remains before the PR; every other lane is
   terminally gated (owner / external / spend / artifact / A-B / not-safe /
   deferred), with zero safety-reintroduction risk.

---

## Plan 16 — architecture-debt slimming + terminal-cover A/B

- **Terminal state.** DONE (dead-code sweep + `tools/measure_load_path_budget.py`).
  Terminal-cover strengthening is A/B-GATED; root-skill contract slimming is
  OWNER-GATED (`atomics/skill/SKILL.md` is at the 80 000-char guard,
  `check_metacompliance_current_canon.ROOT_MAX_CHARS`).
- **Why not in the PR.** Strengthening a terminal-state coverage check (the
  `no_new_resultant_terminal_proof` condition in `tools/check_graph_completeness.py`;
  `terminal_stop_proof_count` at :1131) can flip pass/fail on the 24 retained
  outputs; landing it without measuring that effect risks a silent corpus
  regression.
- **Owner decision.** None for the measurement slice. Owner is needed only to (a)
  adopt a strengthened checker and (b) any root-skill slimming; any grandfathering
  of a retained case is a dated OWNER-DECISION.
- **Gate.** A/B-GATED — satisfiable locally with the committed corpus (no spend/
  external/artifact). The proof: run candidate vs current terminal-cover over the
  same 24 `output.md` files and show zero new failures on non-allowlisted cases.
- **Objective.** A read-only A/B measurement harness reporting, per retained case,
  `{current, candidate}` pass/fail and the delta set, so the strengthening decision
  is evidence-backed.
- **Why it matters.** Terminal-cover is the STOP/HOLD/RECURSE/PARTIAL ->
  preserve-for-audit -> sidecar-eligibility tail of the execution spine; a
  strengthening that silently invalidates retained proofs would corrupt the audit
  base it protects.
- **Source-of-truth.** `tools/check_graph_completeness.py` (`--outputs`, `--json`;
  `no_new_resultant_terminal_proof` at :1142/:1701), `tools/check_retained_corpus_advisory.py`
  (the per-output exit-code A/B pattern to clone: `probe_passes`, `scan_failing_pairs`,
  `evaluate`, `--self-test`), `tools/check_retained_row_claims.py`,
  `tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/*/output.md`
  (24), `tests/retained-proof-corpus/advisory-allowlist.json`, `tools/measure_load_path_budget.py`
  (the measurement-only precedent).
- **Likely files touched.** New `tools/measure_terminal_cover_ab.py` (+ `--self-test`);
  new `docs/terminal-cover-ab-snapshot.md`; one wiring line in `tools/run_local_ci.py`.
  No `check_*` checker, root skill, corpus, manifest, or allowlist.
- **Read-only preflight.** Enumerate the terminal-cover surface
  (`grep no_new_resultant_terminal_proof|terminal_stop_proof_count`), confirm 24
  cases, baseline each case through `check_graph_completeness.py --json`, confirm
  `measure_*` tools are absent from `ci_registry.json` (precedent), run the existing
  retained checkers green.
- **Implementation options.** (A) Two-checker A/B (`--current`/`--candidate` paths;
  cloneable, rule-agnostic). (B) Single-checker `--strict` flag — rejected for the
  first slice (edits a live checker). (C) JSON-condition A/B on the
  `no_new_resultant_terminal_proof` boolean — recommended measurement core, wrapped
  in A's two-input framing.
- **Smallest safe first slice.** `measure_terminal_cover_ab.py`: enumerate the 24
  outputs, extract the `no_new_resultant_terminal_proof` boolean per case (reuse the
  `check_retained_row_claims.py` JSON-parse idiom), classify BOUND vs ADVISORY like
  `check_retained_corpus_advisory.py`, accept optional `--candidate` (omitted =
  baseline snapshot, delta empty), ship a subprocess-free `--self-test`. Writes
  nothing; touches no `check_*`/corpus/root.
- **Validators.** `measure_terminal_cover_ab.py --self-test` (wire beside
  `measure_load_path_budget.py --self-test`); the existing retained checkers still
  PASS unchanged; `check_ci_registry_coverage.py` PASS (measure_ prefix stays out of
  the registry); full `run_local_ci --strict-pwsh` PASS. A/B proof = the printed
  delta empty on non-allowlisted cases.
- **Rollback.** Delete the two new files + revert the one wiring line; `git revert`
  the commit. Nothing else changes.
- **Stop / ANDON.** Baseline already failing on a BOUND case (pre-existing
  contradiction — surface, do not paper over); census != 24; the harness needing a
  live `check_*` edit; any impulse to add an allowlist entry / mutate a retained
  `output.md` to make a candidate pass (drift laundering); any safety-policy framing.
- **What not to do.** No root-skill edit; no `check_*` terminal-cover edit; no
  corpus/manifest/allowlist mutation; do not wire the harness as a hard gate (only
  its `--self-test`); do not raise `ROOT_MAX_CHARS`.
- **Done.** Harness exists, writes nothing, `--self-test` wired & green; dated
  24-row baseline snapshot in `docs/terminal-cover-ab-snapshot.md`; existing
  retained checkers unchanged; `--candidate` makes the strengthening decision a
  one-command query.
- **Commit slicing.** (1) add the harness; (2) wire its self-test into CI; (3)
  record the baseline snapshot. Independently green and revert-clean.
- **Sequencing: before merge — LANDED (`0788b21`).** Pure safe-local observability with a wired
  `--self-test`; it is the evidence instrument for the one A/B-gated sub-item and
  strengthens the PR's auditability story. The strengthening it measures stays
  after-merge/owner-gated; root slimming stays owner-gated.

## Plan 08 — CI coverage / parallelization adoption

- **Terminal state.** DONE (coverage checker + `--report` + static parallelizability
  proof). Adoption is OWNER-GATED: the proof shows no safe drop-in. Live verdict: 91
  commands -> 3 shared-writer, 3 git-gate, 85 read-only.
- **Why not in the PR.** Flipping CI to parallel has no safe drop-in: the 3
  shared-writers mutate shared generated files and the 3 git-gates read state those
  generators produce; a parallel read-only phase also discards the current
  first-failure-abort (`run_local_ci.py` `break` on first non-zero). Both are owner
  decisions.
- **Owner decision.** (a) accept a `serial generate -> serial git-gate -> parallel
  read-only` model; (b) choose fail-fast vs run-all-collect for the parallel tail.
- **Gate.** OWNER-GATED adoption plus an implicit measurement gap — the wall-clock
  win is currently unquantified; the owner cannot decide without a benchmark.
- **Objective.** Give the owner an evidence-backed basis: refresh the proof to live
  counts (**done** — `22e5673`) and add a read-only wall-clock benchmark that
  measures per-command/phase durations and the Amdahl ceiling, without changing CI
  execution.
- **Why it matters.** The CI battery is the enforcement surface for the
  generated-runtime-integrity invariants; a silent, unproven parallelization could
  reorder generate-then-verify and let a corrupted `skill/SKILL.md` pass. Keeping
  adoption behind a measured proof keeps the decision reconstructible from artifacts.
- **Source-of-truth.** `tools/run_local_ci.py` (`COMMANDS`, `--list`,
  `--strict-pwsh`, first-failure `break`), `tools/analyze_ci_parallelizability.py`
  (`classify`, `analyze`, `--self-test`; no timing path yet),
  `docs/audits/ci-parallelizability.md` (now 91/85, corrected).
- **Likely files touched.** `tools/analyze_ci_parallelizability.py` (add a pure
  `benchmark_summary()` helper + self-test; the live-timing `--benchmark` runner is a
  deferred, manual, non-lane-wired second slice); a doc section. No runtime, no
  `ci_registry.json` (the analyze tool is not a `check_*`).
- **Read-only preflight.** `run_local_ci.py --list | wc -l` (91),
  `analyze_ci_parallelizability.py` (3/3/85), confirm no `perf_counter`/`--benchmark`
  exists yet.
- **Implementation options.** (A) static-only refresh — insufficient alone (win
  stays unquantified). (B) read-only serial benchmark with a pure `benchmark_summary`
  helper unit-tested via `--self-test`; the live runner stays manual (it re-runs
  generators) — recommended. (C) checked-in timing snapshot — goes stale.
- **Smallest safe first slice.** The pure `benchmark_summary(timings) -> dict`
  helper (buckets by `classify()`, computes the ceiling) + synthetic-timing
  self-test cases. Zero runtime change; adds no parallelism; the live `--benchmark`
  runner is deferred and must never enter `COMMANDS`. (The doc-count refresh that
  originally rode with this slice already landed as `22e5673`.)
- **Validators.** `analyze_ci_parallelizability.py --self-test` (new cases PASS);
  verdict still 3/3/85; `py_compile`; full `run_local_ci --strict-pwsh` PASS.
- **Rollback.** Single-file additive; `git checkout` the `.py`. The helper is pure
  and unreferenced by the lane except its idempotent `--self-test` line.
- **Stop / ANDON.** Any need to add the live `--benchmark` to `COMMANDS` (races
  shared files); any move to parallel or to remove the `break`; any re-classification
  of `classify()` categories (that is a proof change, not a benchmark); any
  safety-policy framing.
- **What not to do.** No `concurrent.futures` in `run_local_ci.py`; do not weaken
  first-failure-abort; do not reorder `COMMANDS`; do not register the analyze tool in
  `ci_registry.json`; do not treat the benchmark as adoption authorization.
- **Done.** `benchmark_summary()` pure and self-tested; `run_local_ci --strict-pwsh`
  still PASS (91); the owner-facing measurement is runnable so decisions (a)/(b) are
  executable.
- **Commit slicing.** (already landed) doc-count fix `22e5673`; (next) add the
  benchmark helper + self-test; (optional) add the manual `--benchmark` runner,
  never lane-wired.
- **Sequencing: before merge — LANDED (`1cf82c6`).** Safe-local, additive, docs+pure-function; it already
  corrected a self-contradicting artifact in the PR. Adoption stays later/owner.

## Plan 15 — normalizer-transparency / live capture

- **Terminal state.** DONE (scorecard format + offline runner
  `tools/build_model_compliance_scorecard.py`). The normalizer-transparency refactor
  is BUILDABLE but flagged for its own focused pass (the ~15.9k-line harness
  `tools/run_staged_current_skill_smoke.py`); live model/host capture is SPEND-GATED
  and out of scope here.
- **Why not in the PR.** The harness writes `stage["normalization"]` at ~13 sites; a
  clean transparency refactor is multi-site and the owner flagged it for a dedicated
  pass. Making repairs appear in the verdict risks reading as a runtime change unless
  proven record-only.
- **Owner decision.** None to begin (record-only is neutral). Owner is needed before
  escalations: (A) whether a fired repair should annotate/downgrade the `verdict`
  string; (B) whether adding the field bumps the `staged-current-skill-smoke-hashes-v1`
  schema (prefer additive, no bump).
- **Gate.** SPEND-GATED only for the live-capture sub-lane (out of scope). The
  record-only slice is ungated and, being strictly additive, carries no A/B corpus
  risk.
- **Objective.** Make route-state-repair normalizer firings visible in the
  verdict/hash record so a repair cannot silently upgrade a weaker model's raw
  output: (a) a machine-readable classification (lossless-parse / cli-alias-helper /
  route-state-repair) matching `docs/execution-spine.md`; (b) an additive top-level
  `route_state_repairs` summary in `write_hash_record`.
- **Why it matters.** A route-state repair sits at the owner-op / controlled-delta
  hinge of the execution spine. If a repair turns a non-conformant route/terminal
  state into a passing one and the record does not name it, the audit trail
  overstates conformance — exactly what the scorecard lane exists to prevent.
- **Source-of-truth.** `tools/run_staged_current_skill_smoke.py` (`write_hash_record`
  at :7382, its payload at :7399-7427; the route-state-repair normalizers
  `normalize_stage03_route_targets` :1197, `normalize_stage05_mrp_fields` :1857,
  `normalize_stage05_held_route_gradient_identity` :2173; the stage-05 continuation
  repair chain `matched_route_hydrations`; the self-test with per-normalizer
  assertions), `docs/execution-spine.md` (Normalizer classification),
  `docs/model-compliance-scorecard.md`.
- **Likely files touched.** `tools/run_staged_current_skill_smoke.py` (classification
  constant + a `route_state_repairs` collector threaded into `write_hash_record`;
  extended self-test); `docs/execution-spine.md` (point the classification subsection
  at the code table). A standalone `check_normalizer_transparency.py` is an optional
  second slice, not the first.
- **Read-only preflight.** Baseline `--self-test` and `run_local_ci --strict-pwsh`
  green; enumerate every `normalization[...]` key; confirm no existing machine
  classification; read the exact `write_hash_record` payload keys so the new field is
  additive.
- **Implementation options.** (A) classification table + additive hash-record field,
  in-harness — recommended, minimal blast radius, provably behavior-preserving. (B)
  standalone `check_normalizer_transparency.py` — natural second slice, only after A
  surfaces the field. (C) full multi-site `record_normalization(...)` refactor — the
  owner-deferred focused pass; not first.
- **Smallest safe first slice.** Option A, record-only, additive: a
  `NORMALIZATION_KEY_CLASS` constant; a pure `collect_route_state_repairs()`; one
  additive `payload["route_state_repairs"] = ...` line (do not touch `schema` or
  `verdict`); self-test asserting repair-present -> surfaced, lossless-only -> empty,
  and `verdict`/`schema` byte-identical.
- **Validators.** Extended `--self-test` PASS; `run_local_ci --strict-pwsh` PASS
  (count unchanged for slice 1). A/B behavior-preserving proof (in the commit body):
  `verdict`/`schema` unchanged; existing normalization assertions untouched; the
  diff adds exactly one additive key.
- **Rollback.** Single-file additive; `git revert`. The field is never consulted by
  a gate in slice 1, so removal restores byte-identical shape minus the key.
- **Stop / ANDON.** Any change to an existing `--self-test` assertion or to
  `verdict`/`schema`; ambiguous key classification (leave unclassified, flag owner —
  mis-tagging creates false audit alarms); drift toward the multi-site refactor
  (Option C); any live capture; any "policy violation" framing of a repair.
- **What not to do.** No schema bump (owner); no verdict downgrade (owner); no
  multi-site centralization; no model/network call; no `check_*` detector accept/
  reject change; no safety framing; treat the code table as authoritative over the
  doc.
- **Done.** Machine classification covers the route-state-repair keys; additive
  `route_state_repairs` list emitted (empty when none); self-test proves surfacing +
  byte-identity; `run_local_ci --strict-pwsh` PASS; execution-spine subsection points
  at the code table.
- **Commit slicing.** (1) classify + surface (code + self-test, A/B proof in body);
  (2) point execution-spine at the code table (docs); (3, later PR) optional
  `check_normalizer_transparency` detector.
- **Sequencing: after merge (own PR).** The handoff flags this as a focused pass to
  keep the harness change out of the omnibus PR; even the small record-only slice
  touches the hash-record contract and deserves a dedicated review where the
  behavior-preserving proof is the focus.

## Plan 03 — field-witness envelope / binding_status / certificate

- **Terminal state.** DONE for the built portion (binding map + `field-witness.schema.json`
  key contract + `check_field_witness_binding.py` + `daee-canon-eol-v1` byte canon +
  `docs/field-witness-canonicalization-spec.md`, added `38a40de`). Three pieces
  remain: envelope generation (ARTIFACT-GATED), retained `binding_status` (OWNER-GATED),
  certificate `output_fingerprint` rev (OWNER-GATED). Verified: `output_fingerprint`
  and `binding_status` appear only in docs; zero occurrences in `schema/` or `tools/`.
- **Why not in the PR.** Each remaining piece crosses a gate the PR could not open:
  the envelope needs a new per-case artifact; `binding_status` is an owner evidentiary
  claim over 24 legacy cases; `output_fingerprint` revs a tracked schema interacting
  with 24 retained certs.
- **Owner decision.** OD-1 (`binding_status` policy — honest default `legacy_unbound`
  for all 24 per F2, `known_contract_drift` for the two F1 shared-cert pairs). OD-2
  (add `output_fingerprint` to `schema/collapse-certificate.schema.json` — only an
  optional additive field is in-bounds; required would force mutating historical
  outputs).
- **Gate.** ARTIFACT-GATED (the envelope discharged by generating into a **new**
  sidecar path, not overwriting any of the 4 hashed fields). No external/spend; no
  A/B for the generator slice.
- **Objective.** Make OD-1/OD-2 executable: a deterministic envelope generator (emits
  `field-witness-artifact-binding-v1` from already-hashed artifacts + public
  projections, to a new path, mutating no retained byte) + a decision packet
  presenting OD-1/OD-2 as concrete owner-ratifiable diffs.
- **Why it matters.** F1 is a real hole: two byte-identical certificate pairs each
  bind two different outputs because binding is input-side only. The envelope is the
  output-side binding that closes F1 without a schema rev, recomputing `act_rows_hash`/
  `nar_hash` from the public ACT/NAR projections and pinning `output_sha256` — a typed
  sidecar over already-owned surfaces, adding zero new claims.
- **Source-of-truth.** `docs/field-witness-canonicalization-spec.md` (envelope shape;
  canonical-JSON projection hashing), `schema/field-witness.schema.json`,
  `schema/collapse-certificate.schema.json` (22 required keys, no `output_fingerprint`),
  `tools/check_field_witness_binding.py`, `tools/check_retained_proof_corpus.py`
  (`sha256_artifact_bytes`, `ARTIFACT_FIELDS`, the B5 sidecar precedent),
  `docs/audits/field-witness-binding-map.md` (F1/F2/F3), the 24-case manifest,
  `tools/check_ci_registry_coverage.py` (the required<->wired invariant that makes a
  wired checker unsafe for the first slice).
- **Likely files touched.** New `tools/build_field_witness_envelope.py` (+ `--self-test`);
  new `docs/audits/v0.4.3.x-field-witness-envelope-decision-packet.md`; one
  `--self-test` line in `run_local_ci.py`. Not touched: the certificate schema, the
  manifest, any retained bytes.
- **Read-only preflight.** `check_ci_registry_coverage.py`, `check_field_witness_binding.py`,
  `check_retained_proof_corpus.py` green; `grep output_fingerprint|binding_status|artifact-binding-v1`
  in `schema/ tools/` = zero; copy the `build_*.py --self-test` wiring idiom; inspect
  the B5 additive-optional sidecar pattern.
- **Implementation options.** (A) standalone generator, output to a new sidecar,
  no manifest change, no checker wired — recommended. (B) A plus a wired recompute
  checker — rejected for the first slice (the required<->wired invariant forces it to
  be `required`, which pre-commits OD-1 across 24 cases). (C) docs/spec-only — weaker;
  leaves the artifact gate un-discharged.
- **Smallest safe first slice.** Generator that prints the envelope by default and
  only writes with `--out` to a path outside the four hashed fields; default
  `binding_status=legacy_unbound`; carries the spec `non_claims` verbatim; `--self-test`
  proves projection hashes are order-insensitive and the byte hash matches
  `sha256_artifact_bytes`. Plus the OD-1/OD-2 decision packet.
- **Validators.** `build_field_witness_envelope.py --self-test` (wire it);
  `check_ci_registry_coverage.py` PASS (a `build_*.py` needs no registry entry);
  `check_field_witness_binding.py` + `check_retained_proof_corpus.py` unchanged;
  manifest still 24; `run_local_ci --strict-pwsh` PASS. Determinism: same inputs ->
  byte-identical; permuted row order -> unchanged hashes.
- **Rollback.** Purely additive (two new files + append-only lines); `git revert`.
  No retained artifact/manifest/schema touched.
- **Stop / ANDON.** Any need to write into a hashed field, add a manifest entry, or
  change a recorded hash; any retained checker changing verdict; any `binding_status`
  other than `legacy_unbound` forced on a retained case (that is OD-1); any impulse
  to rev the certificate schema (OD-2); a projection hash that needs non-public
  (`.daee`/origin) content (F3).
- **What not to do.** No `binding_status` written onto retained cases; no
  `output_fingerprint` in `schema/`/`tools/`; no retained-byte or manifest-hash
  mutation; no wired envelope checker in this slice; no new canonicalization
  (`daee-canon-v2`/NFC); no safety framing.
- **Done.** Generator deterministic, defaults `legacy_unbound`, writes nothing by
  default, self-test wired & green; retained checkers unchanged; manifest still 24;
  `git diff --stat` shows only the new tool + packet + wiring; decision packet states
  OD-1 (24-case table) and OD-2 (optional-additive diff).
- **Commit slicing.** (1) `plan03: field-witness envelope generator (spec-only
  emission)`; (2) `plan03: envelope + certificate-rev decision packet`. Keep separate;
  bundle no Phase-4 (checker-wiring) or Phase-5 (schema-rev) work.
- **Sequencing: after merge (own PR), before any release.** Additive/safe-local, so
  it need not precede merge; it must land before OD-1/OD-2 and the Phase-4/5 work
  that depend on it, giving the owner a runnable artifact to adjudicate against.

## Plan 06 — release provenance / de-stale / custody

- **Terminal state.** DONE (gate ledger + provenance `--self-test` + stale
  release-body guard: the v0.4.3.0-specific template now fails-safe for any other
  version). Full de-stale is OWNER-GATED (semantics); branch-protection is
  EXTERNAL-GATED; tag/publish/custody are OWNER-GATED.
- **Why not in the PR.** `write_release_body`/`check_release_body` hardcode v0.4.3.0
  release claims (Repair14, route/curl, Smoke 7, the Closure-Reconstructibility
  title). Generifying them requires first deciding what a release body must assert and
  must not assert going forward — an owner-authored contract. The guard already
  removes the only live risk (stale text emitting for a future version).
- **Owner decision.** Sign off on a release-body contract: which current required
  tokens are version-specific (remove from a generic checker) vs invariant caveats
  (retain); whether `write_release_body` is deleted, reduced to a skeleton, or kept
  legacy-only behind the guard; whether the manual `--version/--artifact` preflight
  path stays sanctioned or is retired.
- **Gate.** OWNER-GATED de-stale semantics; EXTERNAL-GATED branch-protection/tag/
  publish; no artifact/spend gate for the docs slice.
- **Objective.** Make the semantics decision executable: a read-only owner-signable
  release-body contract spec + a verified inventory of every v0.4.3.0 hardcode, so a
  later slice can generify or retire the template without changing active verification.
- **Why it matters.** The release body is the public projection of a release's
  evidence boundary; a stale template silently reasserting another version's proof
  claims is a provenance-integrity defect. The guard blocks it today; a contract turns
  the block into a durable, owner-owned contract.
- **Source-of-truth.** `tools/check_release_provenance.py` (guard
  `stale_release_body_guard_error`, `LEGACY_RELEASE_BODY_VERSION="v0.4.3.0"`,
  `write_release_body`, `check_release_body`, `verify_provenance_package`,
  `check_release_preflight`, `self_test`; v0.4.3.0 hardcodes at lines 115-116, 417,
  427, 435-508, 516-525, 758-759), `.github/workflows/release-skill.yml` (uses only
  `--provenance/--package`, no release-body step), `docs/audits/release-gate-ledger.md`,
  `docs/release-artifacts.md`, `CHANGELOG.md`, `AGENTS.md` (manual preflight lines).
- **Likely files touched (later slice; none now for code).** New
  `docs/release-body-contract.md`. Later (post sign-off): `check_release_provenance.py`
  and `AGENTS.md`.
- **Read-only preflight.** Full v0.4.3.0 hardcode inventory; confirm CI never calls
  the release-body path; confirm the guard + self-test are shipped; enumerate the
  `check_release_body` required tokens; confirm no consumer of `write_release_body`
  outside the tool.
- **Implementation options.** (A) docs-only contract spec + hardcode inventory —
  recommended first slice. (B) generify `write_release_body` into a skeleton + external
  prose — changes active behavior, needs A first. (C) retire the release-body path
  entirely — a deletion decision, owner-gated.
- **Smallest safe first slice.** `docs/release-body-contract.md`: inventory every
  hardcode with file:line; classify each required token invariant vs version-specific;
  propose the generic mandatory skeleton; list the owner decisions as checkboxes.
  Changes no runtime, no guard, no active `--provenance/--package` path; marked
  AWAITING OWNER SIGN-OFF.
- **Validators.** `check_release_provenance.py --self-test` and `run_local_ci
  --strict-pwsh` PASS with zero diff under `tools/`; docs-honesty checkers
  (claim-boundaries, mojibake, metacompliance) PASS.
- **Rollback.** Docs-only; `git rm docs/release-body-contract.md`. No behavioral state
  to unwind.
- **Stop / ANDON.** The spec cannot be written without asserting a new required token
  or touching the guard; a consumer of `write_release_body` outside the tool; any `gh`
  call for branch-protection/tag/release; CI regressing from a docs file.
- **What not to do.** No change to `LEGACY_RELEASE_BODY_VERSION`, the guard,
  `write_release_body`, or `check_release_body`; no touch to `verify_provenance_package`
  or the workflow; no tag/publish/branch-protection; no safety framing (caveats are
  evidence-boundary only); do not implement the generic template in this slice.
- **Done.** `docs/release-body-contract.md` inventories all hardcodes with file:line,
  classifies every token, proposes the skeleton, enumerates owner decisions; `git diff`
  shows only the doc; provenance self-test + strict CI unchanged; spec marked awaiting
  sign-off.
- **Commit slicing.** (1) `plan06: add release-body contract spec for owner sign-off`
  (docs only). Deferred (post sign-off): generify/retire the template; update AGENTS.md.
- **Sequencing: later release / after merge.** The shipped scope (guard + self-test +
  ledger) is DONE in the PR; the contract spec is a net-new owner-decision artifact
  needing sign-off before code, and bundling a semantics debate into a green PR delays
  merge for no correctness gain. Open it as its own small follow-up.

## Plan 17 — owner/TTP schema / contract resolution

- **Terminal state.** DONE (drift inventory `docs/audits/owner-contract-drift-inventory.md`
  + parity checker `tools/check_owner_contract_parity.py`, wired, `required`; the R2
  family subset invariant is enforced and green, allowlist empty). Contract resolution
  is OWNER-GATED. The ledger labels this "safety-sensitive"; this slice narrows its own
  scope to pure **operation-token schema parity**, not any refusal/policy layer.
- **Why not in the PR.** The remaining measured drift is D3: a formal owner contract's
  `operation_token` can name an operation the vocabulary never declared, and nothing
  cross-checks it against R1 `owner_operations`. `check_ttp_availability_canaries.source_owned_operations_for_owner`
  trusts the token verbatim. Closing D3 by editing contracts or the vocabulary is an
  owner decision (which representation is canonical).
- **Owner decision.** OD-17a (canonicity): for each contract `operation_token` absent
  from `owner_operations[family]`, declare it, correct the contract, or quarantine it
  in a dated allowlist. OD-17b (enforcement direction): make the D3 cross-check a
  failing gate vs advisory (a failing check can turn CI red on a live contract).
- **Gate.** OWNER-GATED for the enforcing step. The inventory/spec slice is ungated.
- **Objective.** A read-only computed D3 drift-closure inventory (which formal-contract
  operation tokens lack a parity-checked home in `owner_operations`, and which declared
  tokens have no contract consumer) + a docs-only OD-17a/OD-17b decision table.
- **Why it matters.** Three representations of the owner contract (R1 machine
  vocabulary, R3 formal contracts, R2/canary consumers) can silently disagree on the
  operation-token axis. Closing D3 makes the declared contract and its verifier agree —
  the same correctness/parity class as the shipped R2 family check. Not a safety layer.
- **Source-of-truth.** `tools/check_owner_contract_parity.py` (`evaluate` at :44),
  `docs/audits/owner-contract-drift-inventory.md` (D3 at :39-45),
  `atomics/skill/references/diagnostics/delta-result-vocabulary.json` (`owner_operations`,
  `owner_families`), `tools/check_ttp_operator_contracts.py`
  (`FORMAL_OWNER_CONTRACT_REQUIRED`; `check_formal_owner_contract` validates
  `delta_result` vs families but not `operation_token`), `tools/check_ttp_availability_canaries.py`
  (`source_owned_operations_for_owner` returns the token unvalidated),
  `tools/delta_result_vocabulary.py` (`OWNER_OPERATION_VOCABULARY`).
- **Likely files touched.** New `docs/audits/owner-contract-operation-token-drift-inventory.md`.
  Numbers computed via a throwaway scratchpad script (not committed); only the doc lands.
  No checker/vocabulary/contract/`ci_registry.json` edits.
- **Read-only preflight.** `check_owner_contract_parity.py` (+ `--self-test`) and
  `check_ttp_operator_contracts.py --strict` green; enumerate the D3 set by loading R1
  `owner_operations` and every formal contract's `(family, operation_token)` (reuse
  `extract_formal_owner_contract` and `OWNER_OPERATION_VOCABULARY` — do not
  re-implement parsing).
- **Implementation options.** (A) docs-only D3 inventory + decision table — recommended.
  (B) advisory (info-only) D3 cross-check printed by the parity checker — larger, edits
  a shipped checker, defer to after OD-17b. (C) failing D3 check with dated allowlist —
  the actual resolution, OWNER-GATED.
- **Smallest safe first slice.** Option A: the new audit doc with the two computed
  tables, a reproducible command, an OD-17a/OD-17b decision table with the three
  canonical options per row, and an explicit "not a safety layer" note. If the D3 set
  is currently empty, record that and recommend enforcement be deferred as precautionary.
- **Validators.** `run_local_ci` stays PASS (91); `check_owner_contract_parity.py`,
  `check_ttp_operator_contracts.py --strict`, `check_ci_registry_coverage.py` unchanged;
  the doc's numbers reproducible from the recorded command.
- **Rollback.** Docs-only; `git rm` the doc. Nothing else to unwind.
- **Stop / ANDON.** Any need to edit a contract `operation_token`, the vocabulary, or
  prose (OD-17a); any need to choose a canonical side (record, do not decide); any
  refusal/safety/adversarial-memetic framing (out of scope per `455a921`); CI going
  non-green from a docs change.
- **What not to do.** Do not add a token to make a check pass; do not make the D3 check
  fail CI in this slice; do not edit any checker/vocabulary/contract/allowlist/registry;
  do not mechanically diff R4 prose; do not frame any part as a refusal/safety gate.
- **Done.** The inventory doc exists, is read-only/computed/dated, states its
  out-of-scope boundary, carries the two D3 tables + reproducible command + OD-17a/OD-17b
  decision table; `run_local_ci` PASS; no owner semantics changed.
- **Commit slicing.** (1) `plan17: add owner-contract operation-token (D3) drift
  inventory` (docs). (2, after OD-17b=advisory) info-line + extended self-test. (3,
  after OD-17a/OD-17b=enforce) failing invariant + dated allowlist + self-test.
- **Sequencing: later release.** The safe-local half (inventory + R2 parity) merges
  as-is; the D3 slice is preparatory for an unmade owner decision. Produce it as the
  first post-merge Plan-17 follow-up so the owner can adjudicate canonicity before any
  enforcing check is written.

## Plan 11 — checker consolidation / package extraction

- **Terminal state.** DONE (land-gate single-sourced: `run_local_ci.COMMANDS` is the
  single source, `check_ci_registry_coverage.py` enforces required<->wired against
  `ci_registry.json`). Package extraction (moving `tools/check_*.py` into a package
  layout) is OWNER-GATED. Verified: no `__init__.py` exists anywhere; checkers are flat
  in `tools/`.
- **Why not in the PR.** A file move changes runtime discovery and the import graph at
  once: the coverage checker globs `tools/check_*.py` and derives `wired` by substring
  match against `COMMANDS`; ~40 cross-checker sibling imports + ~48 non-checker sibling
  imports resolve only because `tools/` is on `sys.path` (see the load-bearing comment
  `# heavy import; resolves with tools/ on path` in `check_owner_contract_parity.py`);
  `COMMANDS` hardcodes ~70 `tools/check_*.py` paths. Not a smallest-safe slice.
- **Owner decision.** The layout + migration contract: (a) target shape (`tools/checks/`
  vs top-level package vs namespace-only), (b) import style (keep bare + `sys.path` shim
  vs package-relative), (c) registry key convention (bare basename vs package-qualified),
  (d) whether shared libs move too.
- **Gate.** OWNER-GATED (layout). No spend/external/artifact/A-B. The preparatory slice
  is read-only/docs-only.
- **Objective.** Make the layout decision executable: a read-only extraction proposal +
  mechanical impact analysis enumerating every invariant/discovery site that breaks under
  each candidate layout, the full import-edge inventory, and a per-option migration
  recipe — without moving a file.
- **Why it matters.** The `ci_registry.json` <-> `run_local_ci.COMMANDS` <-> on-disk-files
  triangle is the auditability spine (a checker cannot silently join/leave the required
  lane). A package move threatens that spine; a documented impact analysis converts an
  unbounded "should we packageify?" into a bounded, reviewable decision with a known blast
  radius.
- **Source-of-truth.** `tools/check_ci_registry_coverage.py` (discovery glob :95,
  wired-derivation :97, `evaluate` :53-84), `tools/ci_registry.json` (basename-keyed),
  `tools/run_local_ci.py` (`COMMANDS`), `tools/analyze_ci_parallelizability.py`,
  `tools/build_model_compliance_scorecard.py`, `tools/check_field_operator_architecture.py`
  (literal-path read of a checker), the full cross-checker import-edge list, and the
  `sys.path`-insert idiom in `check_owner_contract_parity.py`.
- **Likely files touched.** New `docs/audits/plan11-package-extraction-impact.md`.
  Optional advisory `tools/analyze_checker_import_graph.py` (name starts `analyze_`, so
  invisible to the `check_*.py` glob; if added, register `advisory`, do not wire beyond
  `--self-test`). No file moves.
- **Read-only preflight.** Confirm no `__init__.py`; inventory all sibling imports +
  `sys.path` shims; enumerate every discovery/COMMANDS site; confirm registry keys are
  bare basenames; baseline `run_local_ci --list | wc -l`, `check_ci_registry_coverage.py`,
  and its `--report` green.
- **Implementation options.** (A) `tools/checks/` sub-package, imports kept bare via a
  `sys.path` bootstrap — smallest import churn, keeps the fragile trick. (B) full package
  with relative imports — cleanest end-state, rewrites all ~88 edges, forces `-m` module
  invocation. (C) namespace-only (`__init__.py` + one bootstrap, files stay flat) —
  near-zero breakage, delivers little of the move.
- **Smallest safe first slice.** `docs/audits/plan11-package-extraction-impact.md`: the
  verified import-edge inventory; a discovery-site table (per site, what breaks + the exact
  edit under A/B/C); the invariant-breakage list (required<->wired, coverage, py_compile
  glob); per-option migration recipe + a recommended option. No files move.
- **Validators.** `check_ci_registry_coverage.py` (+ `--self-test`) and its `--report`
  output **byte-identical** before/after; `py_compile` unaffected; `git diff --check`
  clean; `run_local_ci --strict-pwsh` PASS with zero discovery delta. If the analyzer is
  added, `--report` shows it advisory-and-unwired.
- **Rollback.** Docs-only; `git restore` the doc (and remove the analyzer + its registry
  entry if added). For the later migration, the coverage checker catches a broken move
  before merge.
- **Stop / ANDON.** Any need to move a `check_*.py`; `--report` output changing during the
  docs slice; a need to change `evaluate()` semantics; any safety framing; strict-pwsh
  count changing from 89 for a docs-only slice.
- **What not to do.** Do not move/rename/`git mv` any checker or lib; do not edit
  `COMMANDS`/registry keys/the glob or wired logic; do not add `__init__.py`; do not pick
  the layout for the owner; do not convert bare imports to relative "to be tidy"; no
  safety surface.
- **Done.** The impact doc enumerates the complete import-edge inventory, every
  discovery/invariant site with per-option breakage and exact edit, and a recommended
  layout + step-ordered recipe; `check_ci_registry_coverage.py --report` byte-identical
  before/after; `run_local_ci --strict-pwsh` PASS at the same count; the owner can answer
  (a)-(d) without further archaeology.
- **Commit slicing.** (1) `docs(plan11): package-extraction impact analysis + owner
  decision matrix`. (2, optional) the advisory `analyze_*` import-graph tool + registry
  advisory entry + `--self-test`.
- **Sequencing: later release (post-merge, gated).** The land-gate consolidation is
  shipped; the move is a one-way architectural commit blocked on an owner layout decision.
  The docs-only impact analysis can be authored now but is a preparatory artifact for a
  later, separately-approved migration.

## Plan 09 — semantic-replay deeper phases (meaning-inversion)

- **Terminal state.** DONE at README + schema (`tests/semantic-replay/README.md` holds
  the `semantic-replay-fixture-v1` schema; no `cases/`, no harness). The standalone
  polarity guard is NOT-SAFE-TO-BUILD (overmatch); deeper phases are OWNER/SPIKE-GATED;
  the model-lane spike is SPEND-GATED. This is a semantic-**correctness/faithfulness**
  lane (does a meaning-inverted output flip result polarity while surface structure stays
  plausible?), not a safety/refusal/persuasion lane.
- **Why not in the PR.** Two terminal gates. (a) A lexical polarity discriminator
  overmatches lawful negation-bearing surfaces (the entire `concealment-mode/valid/`
  family, `Boundary:` lines, "does not imply guaranteed uptake" disclaimers) and would
  fail the valid-fixture loops. (b) A reliable discriminator plausibly needs a model-lane
  judge (SPEND-gated). So no guard can land until a spike measures its false-positive rate
  against the valid corpus.
- **Owner decision.** After reading the spike's measured FP report, exactly one of: (i)
  approve a specific bounded discriminator with measured FP == 0 and wire it `required`;
  (ii) approve a SPEND-gated model-lane spike; (iii) confirm meaning-inversion stays a
  documented known-miss.
- **Gate.** SPEND-GATED (model-lane); a self-imposed A/B gate (no guard proposed until the
  FP harness reports its count); no external/branch gate for the spike.
- **Objective.** The read-only preparatory artifact: (a) a spike design doc enumerating
  candidate result-polarity discriminators and their overmatch hazards; (b) an FP
  measurement harness (a non-`check_*` `spike_` tool) that runs each candidate over the
  valid corpus and reports how many valid fixtures it would wrongly flag — a disqualifier,
  not a policing detector.
- **Why it matters.** Meaning-inversion is the one documented hole where the structural
  battery certifies a Landed, polarity-flipped output as equivalent. Closing it correctly
  requires proving the discriminator does not itself become a false authority (overmatch =
  fabricated failures on lawful output). The FP harness turns "we think a guard is unsafe"
  into a measured, replayable number for the owner.
- **Source-of-truth.** `tests/semantic-replay/README.md` (schema + kinds),
  `docs/fixture-taxonomy.md` section 4 (meaning-inversion known-miss),
  `docs/proof-class-taxonomy.md` (`semantic-replay` = "Not currently implemented"),
  `docs/non-claims.md` ("No universal semantic grader"), `tools/check_tlang_response_closure.py`
  (the overmatch-prone lexical logic + valid/invalid loop pattern),
  `tools/check_ci_registry_coverage.py` + `ci_registry.json` (the wired-iff-required
  invariant), `tools/run_local_ci.py`. Valid-corpus FP ground truth: tlang 2, mrp 6,
  mid-reread 13, concealment 21, retained 24.
- **Likely files touched.** New `docs/plans/plan09-semantic-replay-spike.md` (verify
  `docs/plans/` exists at preflight; else `docs/`); new
  `tools/spike_semantic_replay_polarity.py` (advisory, `--self-test`-only, non-gating,
  deliberately not `check_*`). Optional later: one `polarity-pair` + one `known-miss`
  fixture under `tests/semantic-replay/cases/`. Not touched in the spike: `run_local_ci.py`,
  `ci_registry.json`, any `check_*.py`.
- **Read-only preflight.** Confirm no `cases/` and no `tools/*polarity*`/`*semantic_replay*`;
  enumerate the valid corpus (the FP ground truth); `grep` negation/boundary surfaces in
  `valid/` (its hit count is the lower bound of what a discriminator must not flag); confirm
  the coverage glob is `check_*.py` only.
- **Implementation options.** (A) read-only spike doc + local FP-measurement harness —
  recommended; produces the exact number the owner needs, closes nothing by design. (B)
  fixtures only — safe-local but no FP measurement; weaker. (C) model-lane spike —
  SPEND-gated, out of scope now; name it as the future path.
- **Smallest safe first slice.** `docs/plans/plan09-semantic-replay-spike.md`: the
  meaning-inversion problem statement; an enumerated table of 2-4 candidate polarity
  discriminators, each with the specific valid fixtures it would wrongly flag; the FP-report
  format; a non-claim block ("No universal semantic grader; structural/enumerated invariants
  only; no safety/refusal/persuasion posture"). Ships no tool and no runtime change. The
  harness is a second commit only if the candidate list is concrete, and stays advisory/
  non-`check_`.
- **Validators.** Docs slice: `check_docs_claim_boundaries.py`, `check_encoding_hygiene.py`,
  `check_mojibake.py`, `git diff --check`, `py_compile` all in `COMMANDS`. Harness slice —
  the A/B proof: `spike_semantic_replay_polarity.py --self-test` PASS (pure-core self-test);
  a plain run prints per-candidate `false_positives=<n>` over the real valid corpus and exits
  0; because it is not `check_*`, `check_ci_registry_coverage.py` does not require it wired.
  No `COMMANDS` addition in the spike. **Lane A/B rule: no candidate is proposed to the owner
  unless its measured false_positives == 0 against the union valid corpus.**
- **Rollback.** Purely additive; `git rm` the doc + tool (+ fixtures if added). No checker/
  `COMMANDS`/registry/fixture-loop edit was made.
- **Stop / ANDON.** Any candidate with FP > 0 on the valid corpus (disqualified — record the
  FP fixtures, escalate to owner for the model-lane decision; this is the expected outcome
  for naive lexical candidates); any need to re-add refusal/safety/persuasion logic; any need
  for a model/host call (SPEND); any need to edit a `check_*` valid/invalid loop.
- **What not to do.** Do not ship/wire/propose-as-land-ready the standalone polarity guard;
  do not name the harness `check_*.py`; do not add to `COMMANDS`/`ci_registry.json` in the
  spike; do not frame this as safety/refusal/dual-use/persuasion; do not delete or silence
  the `fixture-taxonomy.md` section-4 known-miss; do not claim `semantic-replay` is
  implemented.
- **Done.** The spike doc enumerates >=2 candidates each with a named overmatch hazard tied
  to specific valid fixtures, defines the FP-report format, carries the non-claim block, and
  passes `check_docs_claim_boundaries.py`; (if built) the harness `--self-test` PASSes, a
  plain run prints per-candidate FP over the real corpus, and the tool is absent from
  `ci_registry.json`/`COMMANDS`; `run_local_ci --strict-pwsh` green with no new required
  check; the owner-decision item is executable (a measured FP number exists per candidate).
- **Commit slicing.** (1) `plan09: add semantic-replay spike design + FP hazard enumeration`
  (docs). (2) `plan09: add advisory false-positive measurement harness (no wiring)`. (3,
  optional) polarity-pair + known-miss fixtures.
- **Sequencing: later release (post-merge), owner/spend-gated.** The shippable action (a
  guard) is behind two terminal gates only an owner can lift after seeing the FP measurement.
  The spike is safe-local but closes no gate, so folding it into the PR only enlarges the
  diff. Merge -> run the spike as a follow-up -> present the FP report -> owner picks
  (i)/(ii)/(iii) -> later release wires an approved discriminator or model-lane.

---

## PR / release / external gate sequence (terminal, not agent-executable)

These remain external/owner actions, in order, none performed by this pass:

1. Open the single PR from `codex/hardening-all-20260703` (EXTERNAL).
2. Branch-protection / ruleset readback and changes (EXTERNAL, authenticated `gh`).
3. Tag creation, release publication, large-artifact custody (OWNER + EXTERNAL).
4. Post-merge follow-ups in the sequence above: before-merge slices (16, 08, now landed `0788b21`/`1cf82c6`) if
   authorized; then the after-merge own-PR slices (15, 03); then the later-release
   docs/spec slices (06, 17, 11, 09) that unblock their owner decisions.

## Confirmations

- No dual-use / safety-policy / refusal-runtime infrastructure is proposed anywhere
  in this plan; every lane is neutral correctness / provenance / observability, and
  the two lanes nearest the removed surface (09 semantic-replay, 17 owner/TTP) are
  explicitly scoped to meaning-inversion correctness and operation-token parity. The
  `455a921` removal stays in force.
- This planning pass performed exactly one repo change beyond authoring this document:
  the `22e5673` ci-parallelizability doc-count fix. No push, PR, tag, release,
  publication, external action, spend, model smoke, branch-protection change,
  dependency upgrade, or history rewrite occurred.
