# Compiled Runtime Tools

The compiler/checker suite treats `atomics/skill/` as canonical source and `skill/` as the generated Claude runtime package root.

Run from the repository root:

```bash
python tools/build_compiled_runtime.py
python tools/check_compiled_runtime_freshness.py
python tools/check_compiled_module_boundaries.py
python tools/check_stub_integrity.py
python tools/check_consolidation_call_budget.py
python tools/check_routing_parity.py
python tools/check_routing_parity.py --strict
python tools/check_recursive_traversal_governance.py
python tools/check_render_modes.py
python tools/check_framework_pipeline.py
python tools/check_frontmatter.py
python tools/check_coverage.py
python tools/check_recursion_collapse_noetic_frame.py
python tools/check_metacompliance_current_canon.py
python tools/check_smoke_artifacts.py
python tools/check_ir_instance_integrity.py
python tools/check_diagnostic_ir_catalogue_integrity.py
```

Operating rules:

- Edit `atomics/skill/`.
- Do not edit `skill/` directly.
- Run `tools/build_compiled_runtime.py` to regenerate `skill/`.
- Package/deploy from `skill/`.
- Package the contents of `skill/`, not the `skill/` directory itself.
- The archive root must contain `SKILL.md`, `references/`, `compiled-module-map.json`, and `build-manifest.json`.

Runtime path resolution:

- Inherited `references/...` paths inside generated `skill/SKILL.md` remain original atomized module references.
- Resolve missing atomized Markdown paths through `skill/compiled-module-map.json`: original path or module ID -> bundle path -> section with matching `MODULE_ID`.
- Runtime metadata still named literally by the source control plane is copied into `skill/references/diagnostics/`.
- Do not chase absent atomized paths inside the compiled package.

Routing parity fixtures live under `tests/routing-fixtures/`. Add or update those fixtures when a routing-owner expectation changes.

Recursive traversal governance is checked separately by `tools/check_recursive_traversal_governance.py`. It verifies that state/noetic re-read, eligible live noetic burden handling, no-premature-STOP discipline, and STOP / HOLD / RECURSE / PARTIAL semantics are present in both atomized source and generated runtime, with `recursive-state-transitions.md` as the abstract owner.

The recursive checker also treats the runtime as a diagnostic compiler: each substantive input
must reduce to validated IR, activate TTPs only through entry criteria, exit through a result and
state/noetic re-read, and obey depth/stop guards. This prevents deterministic argument-bank behavior,
unguarded TTP recursion, Layer A/B smuggling, and prose-momentum depth drift.

Render-mode governance is checked separately by `tools/check_render_modes.py`. It verifies that the generated runtime documents default compact DSL/IR visibility for `/daee-epistemics`, bounded governed Layer B with Hidden Premises, local Core Formulation, bounded operative submoves, compact TTP/operator trace when used, state/noetic re-read, one Restorative Response, one final Closing Formulation, concise `/daee-epistemics:dsl` DSL/IR printout mode, deprecated internal/development `/daee-epistemics:audit` compatibility, legacy recursive-audit prompt deprecation, and compiled path-resolution invariants.

Current-canon metacompliance is checked separately by `tools/check_metacompliance_current_canon.py`. It keeps root `SKILL.md` in control-plane shape, verifies that generated default output starts from compact DSL/IR plus bounded governed Layer B and state/noetic re-read, checks source-status/noetic-frame and held-release owner anchors, and rejects stale current guidance that revives public audit or prose-only default framing.

The checkers verify generated freshness, section boundary metadata, original module ID preservation, source/YAML/catalogue integrity, modeled file-call budgets, runtime path resolution, and routing-parity fixtures.
