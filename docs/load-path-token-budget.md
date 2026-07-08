# Load-Path Token Budget (measured snapshot)

> Plan 16, Phase 1 deliverable. A **measured** snapshot of the runtime load-path
> footprint. This is observability, not enforcement: nothing here slims a bundle
> or gates CI on a size threshold. `est_tokens` is a heuristic (`bytes // 4`), not
> a tokenizer count and not a claim about any specific model's context accounting.
>
> Regenerate with `python tools/measure_load_path_budget.py`. The tool's
> `--self-test` (arithmetic consistency) runs in the local CI lane; this table is
> a dated snapshot and is not byte-match-enforced (that would be brittle across
> routine bundle regeneration).
>
> Measured 2026-07-06 in worktree `codex/v0.4.6.0-runtime-footprint` after Slice C
> (route-shard split of `runtime-dispatch-gate.md` and `runtime-output-governance.md`
> into 11 route shards, plus the dispatch-index rewrite of SKILL.md's "Load path for
> substantive cases"); supersedes the prior five-bundle snapshot below.

## Measured table

| config | detail | bytes | lines | est_tokens (bytes/4) |
| --- | --- | ---: | ---: | ---: |
| skill-md-only | skill/SKILL.md | 130720 | 1752 | 32680 |
| per-bundle | skill/references/runtime-core-ir.md | 88604 | 1222 | 22151 |
| per-bundle | skill/references/runtime-core-pipeline.md | 47687 | 753 | 11921 |
| per-bundle | skill/references/runtime-core-recursion.md | 92946 | 1428 | 23236 |
| per-bundle | skill/references/runtime-core-routing.md | 21487 | 238 | 5371 |
| per-bundle | skill/references/runtime-diagnostic-core.md | 122746 | 1971 | 30686 |
| per-bundle | skill/references/runtime-foundation.md | 103208 | 1274 | 25802 |
| per-bundle | skill/references/runtime-phase2-passes.md | 48639 | 804 | 12159 |
| per-bundle | skill/references/runtime-shard-audit.md | 73995 | 594 | 18498 |
| per-bundle | skill/references/runtime-shard-diagnostic.md | 45049 | 605 | 11262 |
| per-bundle | skill/references/runtime-shard-ir-support.md | 36721 | 494 | 9180 |
| per-bundle | skill/references/runtime-shard-output-release.md | 117383 | 1567 | 29345 |
| per-bundle | skill/references/runtime-shard-render-contract.md | 149319 | 1949 | 37329 |
| per-bundle | skill/references/runtime-shard-restoration.md | 20654 | 208 | 5163 |
| per-bundle | skill/references/runtime-shard-thesis.md | 20697 | 224 | 5174 |
| five-bundle-substantive | SKILL.md + 14 bundles | 1119855 | 15083 | 279963 |
| always-load-bundles | SKILL.md + 0 always-load bundles | 130720 | 1752 | 32680 |
| structural-diagnosis-floor | SKILL.md + 1 always-load+diagnostic-core bundles | 253466 | 3723 | 63366 |
| largest-retained-output | tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/gate88-tst-lillard/output.md | 169456 | 1290 | 42364 |

constraint-census (skill/SKILL.md): must=79, never=44

## Findings (measured, not asserted)

- Slice C split the two mega-bundles into 11 route shards, RELOCATING modules only
  (anti-slimming law: nothing was removed). `runtime-dispatch-gate.md` (13 source
  modules, ~112k est-tok) is now `runtime-core-ir.md`, `runtime-core-pipeline.md`,
  `runtime-core-recursion.md`, `runtime-core-routing.md`,
  `runtime-shard-ir-support.md`, `runtime-shard-diagnostic.md`,
  `runtime-shard-audit.md`, `runtime-shard-thesis.md`, and
  `runtime-shard-restoration.md`. `runtime-output-governance.md` (2 source
  modules, ~67k est-tok) is now `runtime-shard-output-release.md` and
  `runtime-shard-render-contract.md`. The largest single shard,
  `runtime-shard-render-contract.md`, is ~37k est-tok — roughly a third of the
  size of the old dispatch-gate mega-bundle it partly succeeds.
- The `### Compiled Runtime Routing Addendum`'s "Load path for substantive cases"
  numbered list (in both `non-droppable-manual-contract.md` and
  `manual-contract-digest.md`) was rewritten from a five-line unconditional list
  to exactly **one** line, `references/runtime-core-routing.md`, followed by a
  Dispatch Index table describing when to load each of the 11 route shards
  (trigger signal, shard, load-when condition) and a selection law (one shard
  when unambiguous; body evidence disambiguates; ambiguous routes load all
  candidates capped at 3 or HOLD/PARTIAL `route-ambiguous`; live pressure with 0
  candidates HOLDs/PARTIALs `owner-not-available`; never fake Land). This is the
  mechanism that shrinks the eagerly-hot ("prompt-hot") surface: only
  `runtime-core-routing.md` (~5.4k est-tok) is now named in the unconditional
  list, versus five full bundles (~301k est-tok pre-Slice-B) previously.
- A consequence of the one-line rewrite: `runtime-foundation.md`,
  `runtime-diagnostic-core.md`, and `runtime-phase2-passes.md` are no longer
  named in the numbered list either, so `tools/build_package_shape_inventory.py`
  now classifies them (and all 11 new shards except `runtime-core-routing.md`)
  as `route-warm` rather than `prompt-hot`. They still ship in the package and
  remain reachable on demand (never `cold-law`-gated); they are simply no longer
  claimed hot by the load-path anchor text. See
  `docs/audits/package-shape-inventory.md` for the full per-file classification.
- `five-bundle-substantive` (SKILL.md + all runtime bundles, now 14 files: the 3
  untouched bundles plus the 11 shards) is ~280k est tokens — still exceeding a
  200k-token window if every bundle were loaded eagerly at once. The
  dispatch-index rewrite does not change this row's arithmetic (it sums
  everything regardless of hot/warm classification); it changes what the
  load-path *text* claims must be loaded unconditionally, which is now a small
  fraction of this total.
- `skill-md-only` grew slightly (127954 -> 130720 bytes, +2766 bytes / +692
  est-tok) because the Dispatch Index table and selection-law prose replacing
  the old five-line list are themselves larger than five bare file-path lines.
  This is licensed growth in the routing addendum text, not module content.
- The four `### Always Load` entries (terminology, case-library index, module
  codes, heuristics) still resolve to `runtime-foundation.md` via
  `compiled-module-map.json`, and the `### Mandatory Diagnostic Core` table's six
  files still resolve to `runtime-diagnostic-core.md` — this Always-Load /
  Mandatory-Diagnostic-Core resolution mechanism is independent of the "Load
  path for substantive cases" numbered list and is unaffected by the Slice C
  rewrite. The corrected always-load floor remains SKILL.md alone (0 bundles
  resolve; the four files' content lives as in-kernel digests) at **32,680
  est-tok**, and the structural-diagnosis floor (always-load + diagnostic-core)
  is **63,366 est-tok**.

## Boundaries

- Measurement only; no slimming, no threshold enforcement beyond the ratchet in
  `tools/load-path-budget.config.json`, no CI size gate here.
- `est_tokens` is a `bytes // 4` heuristic, not a model tokenizer.
- Any further slimming or re-architecture is owner-gated.
