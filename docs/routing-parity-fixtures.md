# Routing Parity Fixtures

## What Routing Parity Means

Routing parity means the compiled low-call runtime under `skill/` preserves the routing skeleton, module ownership, and gate discipline of the canonical atomized source under `atomics/skill/`.

The checker verifies that expected routes still point to original module IDs, that those IDs resolve through `skill/compiled-module-map.json`, and that compiled bundle sections preserve source identity markers.

## What It Does Not Mean

Routing parity does not mean exact prose equivalence. The compiled runtime may rearrange source text into runtime bundles, and model outputs may vary in wording. The invariant is the control surface:

```text
V1 diagnosis
Phase 2 pass activation
claim_level
pattern_profile
reason-category
foreign-premise status
routing_gate
matched_modules
withheld routes
output_shape
post_render_gate decision
STOP / HOLD / RECURSE / PARTIAL
```

## Path Resolution

Generated `skill/SKILL.md` intentionally keeps atomized paths in inherited routing tables. In the compiled package those paths are source identities, not literal file-load targets unless the file actually exists in `skill/`.

Resolve an atomized path or original module ID as:

```text
original atomized module path / module ID
-> skill/compiled-module-map.json
-> bundle file
-> section with MODULE_ID
```

Example:

```text
references/tactics/M9-predication-mode.md
-> compiled-module-map.json
-> references/omnibus/OMNIBUS-tactics.md
-> section MODULE_ID: M9-predication-mode
```

The checker classifies runtime path references as:

```text
exists-in-runtime
mapped-to-compiled-section
source-identity-only
unresolved-risk
```

It fails on `unresolved-risk`.

## Fixture Location

Fixtures live under:

```text
tests/routing-fixtures/
```

Each fixture is JSON and uses original module IDs, not omnibus filenames.

## Fixture Shape

```json
{
  "id": "trinity-person-multiplicity",
  "prompt": "The Father is God...",
  "case_class": "complex",
  "expected": {
    "required_modules": [
      "do-christian-extensions",
      "do-attribute-precision",
      "M9-predication-mode"
    ],
    "optional_modules": [],
    "forbidden_matched_modules": [
      "OMNIBUS-do-families"
    ],
    "required_governance": [
      "semantic discipline before doctrinal release",
      "post-render gate"
    ],
    "allowed_post_render_decisions": [
      "STOP",
      "HOLD",
      "RECURSE",
      "PARTIAL"
    ],
    "expected_bundles": [
      "references/runtime-foundation.md",
      "references/runtime-diagnostic-core.md"
    ],
    "owner_clusters": [
      "do-families"
    ],
    "max_calls": 20
  }
}
```

`required_modules` and `optional_modules` must be original module IDs that exist in `compiled-module-map.json`. `forbidden_matched_modules` may name omnibus files or ordinary IDs that must not appear in that fixture's active module set.

## Omnibus Bundles

Omnibus bundle filenames are runtime containers only. They are never valid `matched_modules`.

The checker verifies that fixture modules map into existing omnibus or runtime bundles while keeping the active module identity at the original `MODULE_ID` section.

## Running

Standard compiled-runtime verification:

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

Strict mode also verifies declared owner clusters:

```bash
python tools/check_routing_parity.py --strict
```

The checker does not call a live LLM.

Recursive traversal expectations may appear in `required_governance` when a fixture needs to guard against premature STOP. The dedicated recursive checker owns the invariant vocabulary; routing fixtures use those phrases to keep representative cases tied to the same discipline.
