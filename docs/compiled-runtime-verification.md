# Compiled Runtime Verification

## Summary

Phase 4 verification passed after migrating the editable atomized source to `atomics/skill/` and making `skill/` the generated low-call Claude package root.

Generated files under `skill/` were rebuilt only through `tools/build_compiled_runtime.py`; they were not hand-edited.

## Layout

```text
atomics/skill/ = canonical atomized source
skill/         = generated compiled Claude package root
tools/         = compiler/checker scripts
build/         = optional package/release outputs
```

Edit `atomics/skill/`. Do not edit `skill/` directly. Run `tools/build_compiled_runtime.py` to regenerate `skill/`. Package/deploy from `skill/`.

## Exact Tool Output

The commands below were run with Python 3.11.9 on Windows.

```text
COMMAND: python tools\build_compiled_runtime.py
compiled-runtime build: PASS
Output: skill
Bundles: 12
Compiled source sections: 100
EXIT: 0

COMMAND: python tools\check_compiled_runtime_freshness.py
compiled-runtime freshness: PASS
EXIT: 0

COMMAND: python tools\check_compiled_module_boundaries.py
compiled module boundaries: PASS
EXIT: 0

COMMAND: python tools\check_stub_integrity.py
stub/source integrity: PASS
EXIT: 0

COMMAND: python tools\check_consolidation_call_budget.py
Case class call budget
------------------------------------------------------------
PASS  2 calls (<= 5): Simple glossary / factual query
PASS  8 calls (<= 12): Ordinary theological or philosophical objection
PASS  9 calls (<= 12): Atheist / naturalist objection
PASS 10 calls (<= 12): Christian Trinity / incarnation / philosopher's-God case
PASS  9 calls (<= 12): Revelation / transmission / canon case
PASS  8 calls (<= 12): Hadith-authentication case
PASS 10 calls (<= 12): Kalamic / Maturidi evidentialist case
PASS  8 calls (<= 12): Grief-primary / identity-performance / thin-basis case
PASS 13 calls (<= 20): Complex mixed higher-order case
PASS 13 calls (non-normal): Maximal audit / regression case
------------------------------------------------------------
consolidation call budget: PASS
EXIT: 0

COMMAND: python tools\check_routing_parity.py
Routing parity summary
------------------------------------------------------------
Fixtures checked: 10
Required module assertions: 53
Optional module assertions: 28
Governance phrase assertions: 46
Strict mode: off
Path-resolution status
  exists-in-runtime: 4
  mapped-to-compiled-section: 434
  source-identity-only: 1
  unresolved-risk: 0
------------------------------------------------------------
routing parity: PASS
EXIT: 0

COMMAND: python tools\check_routing_parity.py --strict
Routing parity summary
------------------------------------------------------------
Fixtures checked: 10
Required module assertions: 53
Optional module assertions: 28
Governance phrase assertions: 46
Strict mode: on
Path-resolution status
  exists-in-runtime: 4
  mapped-to-compiled-section: 434
  source-identity-only: 1
  unresolved-risk: 0
------------------------------------------------------------
routing parity: PASS
EXIT: 0

COMMAND: python tools\check_recursive_traversal_governance.py
Recursive traversal governance summary
------------------------------------------------------------
Source files checked: 6
Runtime files checked: 3
Global invariants checked: 8
Decision invariants checked: 7
Pass-shape invariants checked: 6
Runtime no-premature-STOP surfaces: 3
Runtime eligible-live-door surfaces: 3
------------------------------------------------------------
recursive traversal governance: PASS
EXIT: 0

COMMAND: python tools\check_render_modes.py
Render mode governance summary
------------------------------------------------------------
Runtime files checked: 3
Required invariants checked: 13
Forbidden claims checked: 4
------------------------------------------------------------
render mode governance: PASS
EXIT: 0
```

## Generated Runtime Inventory

Expected generated runtime files are present under `skill/`:

```text
skill/SKILL.md
skill/build-manifest.json
skill/compiled-module-map.json
skill/references/diagnostics/module-catalogue.json
skill/references/diagnostics/diagnostic-ir.schema.json
skill/references/diagnostics/operative-contract.schema.json
skill/references/diagnostics/operative-contracts.md
skill/references/runtime-foundation.md
skill/references/runtime-diagnostic-core.md
skill/references/runtime-phase2-passes.md
skill/references/runtime-dispatch-gate.md
skill/references/runtime-output-governance.md
skill/references/omnibus/OMNIBUS-profiles.md
skill/references/omnibus/OMNIBUS-do-families.md
skill/references/omnibus/OMNIBUS-rt-transmission.md
skill/references/omnibus/OMNIBUS-tactics.md
skill/references/omnibus/OMNIBUS-techniques.md
skill/references/omnibus/OMNIBUS-procedures.md
skill/references/omnibus/OMNIBUS-specialty-diagnostics.md
```

Generated bundle Markdown files include the generated-file warning header naming `atomics/skill/` as canonical source. Runtime metadata copies are source-faithful copies and are listed separately in `skill/build-manifest.json` under `runtime_metadata_copies`.

Every compiled section checked by `tools/check_compiled_module_boundaries.py` preserves:

- `SOURCE`
- `MODULE_ID`
- `MODULE_CLASS`
- `CANONICAL_PATH`
- `SOURCE_SHA256`

Section markers now use physical canonical source paths such as `atomics/skill/references/tactics/M9-predication-mode.md`.

## Runtime Semantics Verification

Original module IDs remain intact. Omnibus bundle names are not used as `matched_modules`; the generated `SKILL.md` instructs runtime use to keep original module IDs from `module-catalogue.json`.

Source-basis semantics remain possible because `skill/compiled-module-map.json` maps each original module ID to its compiled bundle path, source path, canonical path, module class, and checksum.

Phase 5 adds an explicit runtime path-resolution rule: inherited atomized paths in generated `skill/SKILL.md` resolve through `compiled-module-map.json` to a bundle section with the matching original `MODULE_ID`. Static metadata paths still named by the control plane are copied under `skill/references/diagnostics/`.

Runtime bundles do not automatically activate selective modules. The generated `SKILL.md` and bundle headers state that bundle co-location is availability, not dispatch. Activation remains governed by V1, Phase 2 passes, Diagnostic IR, routing precedence, and output governance.

The generated `SKILL.md` preserves post-render gate discipline with the `STOP`, `HOLD`, `RECURSE`, and `PARTIAL` decision model.

## Packaging Verification

The package script was run with PowerShell execution-policy bypass because direct script execution is disabled on this machine:

```text
COMMAND: powershell -NoProfile -ExecutionPolicy Bypass -File .\package.ps1 build\daee-epistemics-runtime.skill.zip
Archive: /mnt/c/workspace/ai/daee-epistemics/daee-epistemics/build/daee-epistemics-runtime.skill.zip
Entries: 19
Root check: PASS
Separator check: PASS
Compiled metadata check: PASS

Packaged skill archive:
  Path:   C:\workspace\ai\daee-epistemics\daee-epistemics\build\daee-epistemics-runtime.skill.zip
  Size:   429966 bytes
  SHA256: 10A227E99310423E27282E9E6BD27EFB7CAA410687493AAF5A3699D560851E17

Archive root contains SKILL.md, references/, compiled-module-map.json, and build-manifest.json.
EXIT: 0
```

Archive contents were inspected directly:

```text
SKILL.md
build-manifest.json
compiled-module-map.json
references/diagnostics/diagnostic-ir.schema.json
references/diagnostics/module-catalogue.json
references/diagnostics/operative-contract.schema.json
references/diagnostics/operative-contracts.md
references/omnibus/OMNIBUS-do-families.md
references/omnibus/OMNIBUS-procedures.md
references/omnibus/OMNIBUS-profiles.md
references/omnibus/OMNIBUS-rt-transmission.md
references/omnibus/OMNIBUS-specialty-diagnostics.md
references/omnibus/OMNIBUS-tactics.md
references/omnibus/OMNIBUS-techniques.md
references/runtime-diagnostic-core.md
references/runtime-dispatch-gate.md
references/runtime-foundation.md
references/runtime-output-governance.md
references/runtime-phase2-passes.md
```

Confirmed:

- `SKILL.md` is at archive root.
- There is no top-level `skill/` folder.
- `atomics/`, `tools/`, `docs/`, `build/`, and `.git/` are excluded from the archive.
- `tests/` is excluded from the archive.
- `compiled-module-map.json` and `build-manifest.json` are at archive root.

## Packaging Readiness

`skill/` is ready to be the packaging root for the compiled low-call Claude runtime.

`package.ps1` now packages the contents of `skill/`, including root generated metadata, and validates that the archive root contains `SKILL.md`, `references/`, `compiled-module-map.json`, and `build-manifest.json`.

Source/debug and compiled/runtime package modes can still be added later if needed, but the current repository layout makes `skill/` the compiled runtime package root and `atomics/skill/` the source/debug root.

Before packaging compiled runtime, run:

```text
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

`build/` should remain an optional temporary/release-output location unless the project explicitly decides to commit generated package artifacts.

## Remaining Risks

- Source front matter still contains legacy `canonical_path: skill/...` values in many atomized files; the tools tolerate these during the migration and emit generated section markers with `atomics/skill/...`.
- Generated `skill/` can drift if edited by hand or packaged without freshness checks.
- Runtime readers can misuse omnibus availability unless they follow the generated `SKILL.md` dispatch rules; Phase 5 fixtures now check representative cases against omnibus-as-active-dispatch regression.
- Recursive traversal is statically checked, but live model behavior still depends on following the generated governance at inference time.
- `build/` commit policy remains a repository-management decision.
