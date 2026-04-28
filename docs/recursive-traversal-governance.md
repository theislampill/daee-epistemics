# Recursive Traversal Governance

## Summary

Phase 6 internalizes the old external "grim reaper" prompt behavior into the skill's own routing and output governance.

The old prompt forced a large external sequence:

```text
load ledger
-> Diagnostic IR
-> routing gate
-> render permission
-> restorative pass 1
-> state refresh
-> recursive traversal
-> final governance
```

That prompt is obsolete because the compiled runtime no longer loads atomized files literally. The behavior it enforced is still required, so the rule now lives in the atomized source and compiled runtime governance.

The old grim-reaper prompt is deprecated as a normal invocation pattern. Use:

```text
/daee-epistemics       = clean default response with internal recursive governance
/daee-epistemics:dsl   = compact diagnostic / lab-report render
/daee-epistemics:audit = fuller procedural audit closest to the old prompt's visible ledger
```

Default mode still applies the traversal internally. It does not print the full load ledger, Diagnostic IR, or every door label unless the user asks for `:dsl` or `:audit`.

## Core Rule

After every bounded restorative move, run State Refresh.

STOP is valid only when:

- the current governing blocker has been addressed;
- no eligible live door already present in the original input remains live;
- no held route became releasable after the current move;
- continuing would be argument-stacking rather than governed traversal;
- P7 permits stopping.

If another eligible live door remains in the same input, choose RECURSE or PARTIAL, not STOP.

## Decision Semantics

STOP means the post-render gate has run, `next_eligible_pass` is `none`, no eligible live door remains, and no held route became newly releasable.

RECURSE is required when another already-present distortion becomes eligible after the current blocker clears. It releases one bounded next pass only.

HOLD is valid only when remaining material exists but release depends on an absent signal, active stop, register-hold, semantic gate, thin-basis rule, or other hard rail.

PARTIAL is required when recursion remains live and eligible, but token, tool, interaction, or response limits prevent completing the next pass. It must name the next eligible pass rather than pretending closure.

## Pass Shape

Diagnostic or audit render may expose recursive traversal as:

```text
Live door:
Why already present:
Released module(s):
Bounded move:
State refresh:
Governance: STOP / HOLD / RECURSE / PARTIAL
```

Ordinary answers may compress this shape. The internal governance still runs.

## Not An Argument Dump

Recursion means:

```text
one door at a time
upstream before downstream
state refresh after each move
release only the modules now permitted
stop only when governance licenses stop
```

It does not mean unloading every downstream argument after the first strong move. Held material is traversal-delayed, not permanently suppressed.

## Files Updated

Recursive traversal governance is carried by:

```text
atomics/skill/SKILL.md
atomics/skill/references/diagnostics/diagnostic-ir.md
atomics/skill/references/diagnostics/framework-pipeline.md
atomics/skill/references/rubrics/output-release.md
atomics/skill/references/rubrics/diagnostic-render-contract.md
atomics/skill/references/procedures/P7-restoration-stops.md
```

The generated runtime receives the same governance through `tools/build_compiled_runtime.py`.

## Checker

Run:

```bash
python tools/check_recursive_traversal_governance.py
```

The checker scans the focused atomized source files and generated runtime surfaces for:

```text
State Refresh
eligible live door
held routes rechecked
STOP / HOLD / RECURSE / PARTIAL
no premature STOP
recursion is not argument dump
one door at a time
traversal-delayed, not permanently suppressed
```

## Verification

After editing atomized source, regenerate and run:

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
