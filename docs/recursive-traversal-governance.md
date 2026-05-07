# Recursive Traversal Governance

## Summary

Phase 6 internalizes the former external recursive-audit prompt behavior into the skill's own routing and output governance.

The old prompt forced a large external sequence:

```text
load ledger
-> Diagnostic IR
-> routing gate
-> render permission
-> burden-cycle 1
-> state/noetic re-read
-> governed traversal
-> final governance
```

That prompt is obsolete because the compiled runtime no longer loads atomized files literally. The behavior it enforced is still required, so the rule now lives in the atomized source and compiled runtime governance.

The former external recursive-audit prompt is deprecated as a normal invocation pattern. Use:

```text
/daee-epistemics       = compact DSL/IR header + bounded governed response + state/noetic re-read
/daee-epistemics:dsl   = concise DSL/IR printout
/daee-epistemics:audit = deprecated internal/development compatibility surface
```

Default mode visibly instantiates the compiler with compact DSL/IR fields, then keeps the response bounded and readable through governed Layer B: Hidden Premises, Core Formulation local to each released operation, bounded operative submoves, and compact TTP/operator trace when used. State/noetic re-read follows Layer B, then one Restorative Response and one final Closing Formulation. It does not print the full load ledger, raw Diagnostic IR, full Case State, `matched_modules`, route ledger, or load ledger. `:dsl` is the concise DSL/IR printout mode. `:audit` is retained only for internal/development compatibility, not as the public place where governance becomes real.

## Core Rule

After every bounded restorative move lands, run state/noetic re-read.

STOP is valid only when:

- the current live noetic burden has been addressed;
- no eligible live noetic burden already present in the original input remains live outside the submoves already handled;
- no held route became releasable after the current move;
- continuing would be argument-stacking rather than governed traversal;
- P7 permits stopping.

If another eligible live noetic burden remains in the same input after state/noetic re-read, and it was not already handled as an operative submove under the current governing burden, choose RECURSE or PARTIAL, not STOP.

## Decision Semantics

STOP means the post-render gate has run, `next_eligible_pass` is `none`, no eligible live noetic burden remains, and no held route became newly releasable.

RECURSE is required when another already-present live noetic burden becomes eligible after the current burden lands and the state/noetic re-read licenses a new burden-cycle. It releases one bounded next burden-cycle only.

HOLD is valid only when remaining material exists but release depends on an absent signal, active stop, register-hold, semantic gate, thin-basis rule, or other hard rail.

PARTIAL is required when recursion remains live and eligible, but token, tool, interaction, or response limits prevent completing the next pass. It must name the next eligible pass rather than pretending closure.

## Pass Shape

Diagnostic render may expose recursive traversal as:

```text
Live noetic burden:
Why already present:
Released module(s):
Bounded operation:
State/noetic re-read:
Governance: STOP / HOLD / RECURSE / PARTIAL
```

Ordinary answers may compress this shape. The internal governance still runs.

## Not An Argument Dump

Recursion means:

```text
one live noetic burden per burden-cycle
operative submoves stay inside that burden when subordinate
upstream before downstream
state/noetic re-read after each burden lands
release only the modules now permitted
stop only when governance licenses stop
```

It does not mean unloading every downstream argument after the first strong move, and it does not mean splitting every topical facet into its own burden-cycle. Hiddenness, punishment/accountability, source-status, source-worldview, and identity-stabilization may be operative submoves inside one governing burden. Held material is traversal-delayed, not permanently suppressed.

## Files Updated

Recursive traversal governance is carried by:

```text
atomics/skill/SKILL.md
atomics/skill/references/diagnostics/diagnostic-ir.md
atomics/skill/references/diagnostics/framework-pipeline.md
atomics/skill/references/diagnostics/recursive-state-transitions.md
atomics/skill/references/rubrics/output-release.md
atomics/skill/references/rubrics/diagnostic-render-contract.md
atomics/skill/references/procedures/P7-restoration-stops.md
```

`recursive-state-transitions.md` is the canonical abstract owner for STOP / HOLD / RECURSE /
PARTIAL and state carry/reset/re-evaluation. `framework-pipeline.md` remains the compiled pipeline
audit surface and forbidden-shortcut index.

The generated runtime receives the same governance through `tools/build_compiled_runtime.py`.

## Checker

Run:

```bash
python tools/check_recursive_traversal_governance.py
```

The checker scans the focused atomized source files and generated runtime surfaces for:

```text
state/noetic re-read
eligible live noetic burden
held routes rechecked
STOP / HOLD / RECURSE / PARTIAL
no premature STOP
recursion is not argument dump
one live noetic burden per burden-cycle
operative submoves are not burden-cycles
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
python tools/check_recursion_collapse_noetic_frame.py
python tools/check_metacompliance_current_canon.py
```
