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
> Measured 2026-07-04 in worktree `codex/hardening-all-20260703`.

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
| always-load-bundles | SKILL.md + 0 always-load bundles (unresolved: references/terminology.md, references/case-library/INDEX.md, references/module-codes.md, references/techniques/heuristics.md) | 216112 | 2852 | 54028 |
| largest-retained-output | tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/gate88-tst-lillard/output.md | 169456 | 1290 | 42364 |

constraint-census (skill/SKILL.md): must=175, never=51

## Findings (measured, not asserted)

- `runtime-dispatch-gate.md` is the single largest bundle at ~112k est tokens —
  by itself over half of a 200k-token window.
- `five-bundle-substantive` (SKILL.md + all five runtime bundles) is ~301k est
  tokens, exceeding a 200k-token window: loading every substantive bundle at once
  does not fit.
- The four `### Always Load` entries are **reference** files (terminology,
  case-library index, module codes, heuristics), not diagnostic modules, so they
  have no `compiled-module-map.json` module entry and their bundle footprint is
  not resolvable via that map — the tool reports them as unresolved rather than
  guessing.

## Boundaries

- Measurement only; no slimming, no threshold enforcement, no CI size gate here.
- `est_tokens` is a `bytes // 4` heuristic, not a model tokenizer.
- Any slimming that would change the runtime is owner-gated (Plan 16 Phases 2-4).
