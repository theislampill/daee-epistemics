# Load-Path Architecture (v0.4.6.0 runtime-footprint)

Measurement-only reference for the kernel/digest/cold-law/shard/index
architecture landed in Slices A1/A2/B/C on `codex/v0.4.6.0-runtime-footprint`.
Describes mechanism and how to re-measure it; makes no release-readiness
claim. Run the commands below yourself before quoting any number.

## The core idea: non-droppable = enforced, not inlined

Before this program, the full manual contract and the "Load path for
substantive cases" five-bundle list were both instructed *hot* on every case
-- inlining was the only mechanism anyone trusted to guarantee an obligation
was not silently dropped. That produced an eager-load floor of ~301k est-tok
(pre-program) / ~279k (post Slice B) before any case-specific content.

The redesign keeps every obligation but changes *how* presence is proven:
load-bearing-on-every-call text stays hot (Always-Load kernel digests,
`SKILL.md` root); real law that does not need every context window goes cold,
proven present by a checker plus hash manifest instead of inlining (see
`docs/recursive-state-capsule.md` for the capsule side,
`check_cold_law_digest.py` for the manual-contract side); text only some
cases need is split into route shards, loaded only on dispatch-index
selection. One-line summary: a clause's importance is no longer measured by
whether it is always in context, but by whether a required, CI-wired checker
fails when it is missing, altered, or disconnected from its pointer.

## Layers, source files, and owning checkers

| Layer | Source of truth | Checker |
| --- | --- | --- |
| Kernel digest (Always-Load) | `atomics/skill/SKILL.md` `### Always-Load Digests (kernel)` | `check_metacompliance_current_canon.py`, `measure_load_path_budget.py` |
| Cold manual-contract law | `manual-contract-digest.md` (hot digest) + `non-droppable-manual-contract.md` (cold verbatim, COLD-LAW-CLAUSE anchors) | `check_cold_law_digest.py` |
| Cold-law manifest | generated `skill/cold-law-manifest.json` (`daee-cold-law-manifest-v1`, 13 clauses, gitignored) | `check_cold_law_digest.py` |
| Dispatch index + route shards | `SKILL.md` Dispatch Index table + `skill/references/runtime-*.md` (11 shards) | `check_route_shard_selection.py` |
| Budget/ratchet/aspirational gates | `tools/load-path-budget.config.json` | `measure_load_path_budget.py` |
| Shard classification | config `aspirational.shard_classes` | `measure_load_path_budget.py --enforce` |

Debug in that order: kernel digest first (what's always true), then cold-law
manifest (proven present, not inlined), then the dispatch index (what loads
on selection), then the config (what the gates measure/enforce).

## The dispatch index replaces the 300k load path

`runtime-dispatch-gate.md` (13 modules) and `runtime-output-governance.md` (2
modules) were split into 11 flat `references/runtime-*.md` shards (relocation
only -- total shard bytes equal the old bundle bytes plus per-file header
overhead; see commit `b48b136`). The old "Load path for substantive cases"
numbered list is now exactly one line: `runtime-core-routing.md`. Everything
else loads through the 11-row Dispatch Index plus a selection law:

- unambiguous signal -> load exactly 1 shard;
- ambiguous signal -> load all candidates, capped at 3, OR route to
  `HOLD`/`PARTIAL` with reason `route-ambiguous`;
- zero candidates under live pressure -> `HOLD`/`PARTIAL` with reason
  `owner-not-available`;
- never fake `Land`; always record `shards_loaded`.

Stage-07 mandatory loads (`runtime-shard-output-release.md`,
`runtime-shard-render-contract.md`) are a fixed post-gate stage, **not**
selection-gated -- they are removed from the trigger table entirely (see
`a868bfa`). Do not add them back as a conditional dispatch-index row; "Release
waits for them" regardless of what the index selected.

`tools/check_route_shard_selection.py --self-test` proves: every dispatch-index
cell resolves to a real shard file; every shard except the numbered-list
entry, `runtime-foundation.md`, `runtime-diagnostic-core.md`, and
`runtime-phase2-passes.md` is index-reachable (a dead shard fails); every
module has exactly one shard home; the selection law and OSM alias block are
literally present; the addendum text is byte-identical (lockstep) across the
compiled root, the shipped cold copy, and both atomics rubric copies; and
`EXPECTED_EAGER_LIST == [runtime-core-routing.md]` -- the canary that would
catch a regression back toward the old eager five-bundle pattern.

## Floors table -- verify live before quoting

Run `python tools/measure_load_path_budget.py` yourself; do not copy these
numbers into a claim without re-measuring, because they change every time
atomics change. Measured at HEAD of this branch (`est_tok = bytes // 4`, an
overestimate vs. real `tiktoken o200k_base` tokens by ~11% per the
one-time calibration in `load-path-budget.config.json`):

| Row | est_tok | Meaning |
| --- | ---: | --- |
| `skill-md-only` (root) | 34,021 | Compiled `SKILL.md` alone |
| `always-load-bundles` | 34,021 | Root + 0 resolved always-load bundles -- **equals root**, because the four formerly-eager foundation files were replaced by in-kernel digests |
| `structural-diagnosis-floor` | 64,708 | Root + `runtime-diagnostic-core.md` (the Mandatory Diagnostic Core table) |
| `five-bundle-substantive` / `total-hot-surfaces` | 281,305 | Root + all 14 per-bundle files summed (retained naming from the pre-split "five bundle" row; now sums 14 files by design) |
| `largest-retained-output` | 42,364 | Size of the largest retained proof-corpus output; visibility only, never gated |

`always-load == root` is the headline structural fact: a case that never
needs structural diagnosis or a route shard pays only the root cost.

## Ratchet, anti-banking, and aspirational gates

Three independent gates read `tools/load-path-budget.config.json`:

1. **Ratchet** (`--enforce-ratchet`, always run in CI): fails if any row
   regresses more than `tolerance_pct` (2.0%) over its `baseline`, or more
   than `aggregate_tolerance_pct` (1.0%, stricter) for the
   `total-hot-surfaces` aggregate row -- the tighter aggregate bound is the
   countermeasure to a spreading attack where growth spread evenly across
   every per-row surface would otherwise stay inside 2% in aggregate too.
2. **Anti-banking**: a baseline above `measured * (1 + tolerance)` fails as
   "banked headroom" -- a baseline cannot be pre-raised today to hide growth
   tomorrow.
3. **Aspirational** (`--enforce`, independent of `--enforce-ratchet`):
   hot-root ceiling 35,000 est-tok (warn above 25,000); `default_hot`
   per-shard ceiling 25,000 est-tok (warn above 15,000); default-exec
   worst-case ceiling 105,000 est-tok = root (34,021) + capsule allowance
   (4,000) + top-3 co-selectable `default_hot` shards (`core-recursion`
   23,236 + `core-ir` 22,151 + `shard-audit` 18,498 = 63,885), printed as
   explicit arithmetic. Also enforces shard classification: every
   `runtime-*.md` on disk must appear in `shard_classes.default_hot` /
   `stage_warm` / `on_demand_cold`, or the check fails.

### Updating baselines deliberately

Baselines are data, not code, and anti-banking means they cannot be padded
speculatively. To update one: make the atomics change; run
`measure_load_path_budget.py` and read the new numbers; edit
`ratchet.baseline` to the newly measured values (not beforehand); add or
extend a `_comment_<slice>` note explaining *why* the number moved, citing
the commit/slice (every existing baseline change carries one); re-run
`--enforce-ratchet` and `--self-test` to confirm acceptance.

Same-commit ceiling raises (the ratchet baseline, or `ROOT_MAX_CHARS` in
`check_metacompliance_current_canon.py` / `check_recursion_collapse_noetic_frame.py`)
remain norm-mitigated, not tool-blocked: the tooling requires an explicit,
commented change but cannot judge whether the change is *warranted*.

## The never-re-inline rule

Do not restore the retired 5-line "Load path for substantive cases" eager
bundle list, and do not re-inline the full manual contract into the hot root.
Both regressions are caught mechanically:

- `check_route_shard_selection.py`'s `EXPECTED_EAGER_LIST` canary fails if the
  numbered list contains anything other than `runtime-core-routing.md`.
- `check_cold_law_digest.py`'s hash-parity and clause-ID-allowlist checks fail
  if the cold manual contract is inlined, altered, or its manifest entries
  drift from the anchored source spans.

If a future change seems to require re-inlining something, treat that as a
sign the checker/manifest layer needs a new clause or shard classification --
not a reason to bypass the split.

## Debugging without weakening the runtime

- **A row looks unexpectedly large**: run `measure_load_path_budget.py` (no
  flags) and compare against the config's `baseline` table before touching
  atomics. If real and licensed, follow "Updating baselines deliberately"
  above; do not silence the ratchet by disabling it.
- **`--enforce-ratchet` fails**: read which row regressed and by how much.
  Genuine reviewed growth gets a baseline update with a comment; accidental
  bloat gets reverted.
- **`--enforce` fails on shard classification**: a new `runtime-*.md` file
  has no entry in `shard_classes`. Add it to `default_hot`, `stage_warm`, or
  `on_demand_cold` -- do not delete the classification requirement.
- **`check_cold_law_digest.py` fails**: read its `--self-test` output; it
  names the failing clause ID and check (manifest schema, hash parity,
  checker mapping, digest reference parity, cold-copy verbatim, or
  advisory-budget).
- **`check_route_shard_selection.py` fails**: it prints which of its 7
  checks failed (index parse, shard existence, module homes, selection law
  text, OSM alias block, lockstep, or eager-list regression).

None of these repairs should route around the failing checker; the checker
failing loudly is the mechanism working as designed.
