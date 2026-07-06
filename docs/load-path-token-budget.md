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
> Measured 2026-07-06 in worktree `codex/v0.4.6.0-runtime-footprint` (post
> always-load resolver fix; supersedes the 2026-07-04 snapshot below).

## Measured table

| config | detail | bytes | lines | est_tokens (bytes/4) |
| --- | --- | ---: | ---: | ---: |
| skill-md-only | skill/SKILL.md | 216112 | 2852 | 54028 |
| per-bundle | skill/references/runtime-diagnostic-core.md | 122746 | 1971 | 30686 |
| per-bundle | skill/references/runtime-dispatch-gate.md | 446879 | 5742 | 111719 |
| per-bundle | skill/references/runtime-foundation.md | 103208 | 1274 | 25802 |
| per-bundle | skill/references/runtime-output-governance.md | 266571 | 3513 | 66642 |
| per-bundle | skill/references/runtime-phase2-passes.md | 48639 | 804 | 12159 |
| five-bundle-substantive | SKILL.md + 5 bundles | 1204155 | 16156 | 301038 |
| always-load-bundles | SKILL.md + 1 always-load bundles | 319320 | 4126 | 79830 |
| structural-diagnosis-floor | SKILL.md + 2 always-load+diagnostic-core bundles | 442066 | 6097 | 110516 |
| largest-retained-output | tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/gate88-tst-lillard/output.md | 169456 | 1290 | 42364 |

constraint-census (skill/SKILL.md): must=175, never=51

## Findings (measured, not asserted)

- `runtime-dispatch-gate.md` is the single largest bundle at ~112k est tokens —
  by itself over half of a 200k-token window.
- `five-bundle-substantive` (SKILL.md + all five runtime bundles) is ~301k est
  tokens, exceeding a 200k-token window: loading every substantive bundle at once
  does not fit.
- The four `### Always Load` entries (terminology, case-library index, module
  codes, heuristics) **do** have `compiled-module-map.json` module entries; all
  four resolve to the same bundle, `references/runtime-foundation.md`. The
  earlier snapshot's claim that they had "no module entry" was wrong — the
  original tool under-reported because of a path-prefix mismatch: the map's
  `canonical_path` values are repo-root-relative (`skill/references/...`)
  while the Always Load table lists paths relative to `skill/`
  (`references/...`), so an exact-match lookup between the two never hit, and
  a second bug joined the resolved `bundle_path` against the repo root instead
  of `skill/`, so even a successful lookup would have pointed at a
  nonexistent file. Both are fixed: the resolver now normalizes the `skill/`
  prefix before comparing, and joins `bundle_path` against `ROOT / "skill"`.
  The corrected always-load floor is SKILL.md + `runtime-foundation.md` ~=
  **79,830 est-tok**.
- The `### Mandatory Diagnostic Core` table's six files all resolve, via the
  same map, to `references/runtime-diagnostic-core.md`. Combined with the
  always-load floor, the structural-diagnosis floor is SKILL.md +
  `runtime-foundation.md` + `runtime-diagnostic-core.md` ~= **110,516 est-tok**.

## Boundaries

- Measurement only; no slimming, no threshold enforcement, no CI size gate here.
- `est_tokens` is a `bytes // 4` heuristic, not a model tokenizer.
- Any slimming that would change the runtime is owner-gated (Plan 16 Phases 2-4).
