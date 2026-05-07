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
python tools/check_frontmatter.py
python tools/check_coverage.py
python tools/check_framework_pipeline.py
python tools/check_recursion_collapse_noetic_frame.py
python tools/check_metacompliance_current_canon.py
```

Package/deploy from `skill/`. A Claude-compatible `.skill` archive must contain `SKILL.md` at archive root, not a top-level `skill/` directory.
Current readiness checks and smoke prompts are documented in `docs/package-smoke-readiness.md`.

Generated `skill/SKILL.md` intentionally preserves inherited atomized load-table paths. At runtime those paths are not literal file loads: resolve them through `skill/compiled-module-map.json` to the compiled bundle section with the matching original `MODULE_ID`. Static metadata paths that remain literal, such as the module catalogue and schemas, are copied under `skill/references/diagnostics/`.

## Runtime Metadata Copies

The compiled runtime package intentionally includes four metadata files under `references/diagnostics/`. These are declared in `RUNTIME_METADATA_COPIES` in `tools/compiled_runtime_lib.py` and are recorded in `build-manifest.json` under `runtime_metadata_copies`. They are not source leakage.

| File | Purpose |
|------|---------|
| `module-catalogue.json` | Authoritative registry of all module `id`/`module_class` pairs. Every `matched_modules` IR entry must match this catalogue exactly. Required by `check_compiled_module_boundaries.py`. |
| `diagnostic-ir.schema.json` | JSON schema the Diagnostic IR must validate against before dispatch. Compliance is a conceptual check; presence enables practitioner and checker discipline. |
| `operative-contract.schema.json` | JSON schema governing operative front-matter fields (`id`, `module_class`, `canonical_path`, `contract_version`, optional fields). |
| `operative-contracts.md` | Architecture specification for operative contracts — purpose, required/optional keys, allowed values, failure modes, migration strategy. |

A `.skill` archive missing these four files has a stale or incomplete staging directory. Rebuild from `skill/` after running `python tools/build_compiled_runtime.py` to ensure all `RUNTIME_METADATA_COPIES` are present.

Routing parity fixtures live in `tests/routing-fixtures/` and are checked by `tools/check_routing_parity.py`.
