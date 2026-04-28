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

Recursive traversal governance is checked separately by `tools/check_recursive_traversal_governance.py`. It verifies that State Refresh, eligible-live-door handling, no-premature-STOP discipline, and STOP / HOLD / RECURSE / PARTIAL semantics are present in both atomized source and generated runtime.

Render-mode governance is checked separately by `tools/check_render_modes.py`. It verifies that the generated runtime documents clean default `/daee-epistemics` mode, compact `/daee-epistemics:dsl` lab-report mode, fuller `/daee-epistemics:audit` mode, grim-reaper prompt deprecation, and compiled path-resolution invariants.

The checkers verify generated freshness, section boundary metadata, original module ID preservation, source/YAML/catalogue integrity, modeled file-call budgets, runtime path resolution, and routing-parity fixtures.
