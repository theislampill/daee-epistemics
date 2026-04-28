# Source vs Runtime Layout

The repository now separates editable atomized source from the Claude package runtime.

```text
atomics/skill/ = canonical atomized editable source
skill/         = generated compiled Claude package root
tools/         = compiler and checker scripts
tests/         = routing parity fixtures and static regression inputs
docs/          = reports and operating notes
build/         = optional temporary/release artifacts
```

Edit `atomics/skill/`. Do not edit `skill/` directly.

Regenerate the runtime package root with:

```bash
python tools/build_compiled_runtime.py
```

Before packaging or deployment, run:

```bash
python tools/check_compiled_runtime_freshness.py
python tools/check_compiled_module_boundaries.py
python tools/check_stub_integrity.py
python tools/check_consolidation_call_budget.py
python tools/check_routing_parity.py
python tools/check_routing_parity.py --strict
python tools/check_recursive_traversal_governance.py
python tools/check_render_modes.py
```

Package/deploy from `skill/`. A Claude-compatible `.skill` archive must contain `SKILL.md` at archive root, not a top-level `skill/` directory.

Generated `skill/SKILL.md` intentionally preserves inherited atomized load-table paths. At runtime those paths are not literal file loads: resolve them through `skill/compiled-module-map.json` to the compiled bundle section with the matching original `MODULE_ID`. Static metadata paths that remain literal, such as the module catalogue and schemas, are copied under `skill/references/diagnostics/`.

Routing parity fixtures live in `tests/routing-fixtures/` and are checked by `tools/check_routing_parity.py`.
