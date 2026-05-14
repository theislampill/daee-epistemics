---
id: ir-reconstruction-pass
module_class: governance
canonical_path: skill/references/diagnostics/ir-reconstruction-pass.md
contract_version: "0.4.0.0"
load_when:
  - after Diagnostic IR formation and before routing precedence is allowed to dispatch modules
routing_effects:
  - blocks ordinary module dispatch when the populated IR cannot reconstruct the live burden, selected operator, and governance verdict
emits:
  - reconstruction_fidelity
catalogue_registered: false
---

# IR Reconstruction Pass

This file owns the reconstruction check between Diagnostic IR formation and module dispatch.
It does not create routes, owners, PF codes, render modes, or a second DSL. It tests whether
the existing IR is faithful compression of the live noetic burden rather than plausible typed
commentary.

## Reconstructor

Self-reconstruction by the same runtime that formed the IR is not sufficient evidence. It may
inherit the same prose-shape prior that produced the IR. The default release-grade design is a
mechanical + LLM hybrid:

1. Mechanical check: parse the populated IR and verify schema shape, catalogue-valid
   `matched_modules`, `source_basis` coverage, post-render gate consistency, and any explicit
   input-anchored lexical or structural signals available without loading the skill.
2. Semantic check: use a separate no-skill reconstruction pass that receives only the original
   input, the populated IR or trace candidate, and the criteria below. It must not receive
   `SKILL.md`, `module-catalogue.json`, the routing catalogue, owner files, or compiled maps.

Cross-model reconstruction is allowed for release-grade audits when available: Hermes IRs may
be reconstructed by Sonnet and Sonnet IRs by Hermes. Cross-model agreement is stronger evidence,
but it is not required for the baseline repository check because it is operationally heavier and
runtime-dependent.

The reconstructor asks whether the populated IR alone recovers:

- case shape,
- live noetic burden,
- operative deformation or concealment,
- discourse orientation,
- selected operator/TTP,
- nearest plausible held, rejected, or deferred alternatives,
- expected Land(B),
- governance verdict.

## Inputs

The reconstruction pass uses existing IR fields only:

- `case_family`
- `claim_type`
- `claim_level`
- `matched_modules`
- `deformation`
- `concealment_mode`
- `do_orient`
- `restoration_target`
- `next_move`
- `post_render_gate`
- optional structural fields such as `load_bearing_node`, `collapse_radius`,
  `intervention_target`, `what_is_withheld_and_why`, and `what_remains_live`

No broad semantic field expansion is authorized here. The pass may add only:

```text
reconstruction_fidelity: pass | partial | fail
reconstructor_notes: brief note naming what could not be recovered when partial/fail
```

`reconstructor_notes` may also be present on a pass when it records a compact neighbor
contrast, but it must not become a hidden route ledger.

## Verdict Semantics

- `pass`: the original input plus populated IR can reconstruct the live burden, selected
  operator/TTP, nearest held or deferred alternatives, expected Land(B), and governance verdict.
- `partial`: some burden or neighbor contrast is recoverable but one required element is
  underdetermined. Ordinary content dispatch is not licensed; only bounded HOLD/PARTIAL output
  with explicit reason is licensed.
- `fail`: the IR cannot recover the live burden/operator/verdict relation. Ordinary dispatch is
  blocked. Re-run diagnostic reduction or emit Stop-4 / PARTIAL with the missing differentiator.

`fail` blocks ordinary module dispatch. `partial` permits only bounded PARTIAL/HOLD output. `pass`
permits normal routed execution, subject to routing precedence, owner-load, output-release, and
recursive-state rules.

## TTP Selection Reconstruction Check

For every selected operator/TTP, the trace or verdict evidence must preserve this compact chain:

```text
burden signal
-> IR field(s)
-> owner trigger
-> selected TTP/operator
-> nearest plausible alternatives
-> why selected TTP is first-live
-> why alternatives are held/rejected/deferred
-> expected Land(B)
-> governance verdict
```

The chain may live in trace/verdict artifacts or internal diagnostic evidence. It is not a
default public-output ledger. A selected TTP without a recoverable burden signal and owner-floor
operation is label-only routing and fails this pass.

## Ontological Accuracy Check

The reconstruction pass also flags invented noetic categories. `restoration_target`,
`deformation`, selected TTP, and governance verdict must correspond to licensed structures in the
existing architecture: case-state, diagnostic IR, metaphysical architecture, routing precedence,
recursive state transitions, and output governance. Do not add a new `ontological_audit` IR field;
record any flag or failure in `reconstructor_notes` and route to `partial` or `fail` when the
restoration target or operator cannot be licensed.

## Stability Thresholds

Routing determinism is tested as within-model repeatability, not full cross-model equivalence.
The architecture is deterministic once IR axes are set, but those axes still require interpretive
diagnosis.

For a stability fixture, run five repetitions with the same prompt, skill build, model, and
driver/mode.

- Stable: `case_family`, `claim_type`, and `claim_level` are identical across all five; the live
  burden is identical or semantically equivalent across all five.
- Near-stable: selected TTP differs by no more than one neighboring owner across the five runs,
  and the alternative is documented as a plausible neighbor while the live burden remains stable.
- Drift: more than one owner difference, burden differences, claim-type or claim-level
  differences, or governance verdict differences without input-sensitive reason.

A stability failure is a routing defect even when each individual run has
`reconstruction_fidelity: pass`.

## Reconstruction Faithfulness Through Render And Replay

The reconstruction bottleneck continues after initial IR formation:

```text
surface discourse
-> DSL/IR
-> reconstructed live noetic burden / selected operator / held-deferred alternatives / expected Land(B) / governance verdict
-> routed burden-cycle execution
```

Plausible typed commentary is not faithful compression unless the runtime can reconstruct the
burden-local control state it came from. Route labels, owner names, checker markers, or state
tokens appearing somewhere in a trace do not prove reconstruction faithfulness. The burden step
must remain locally replayable as `ⁿBᵢ -> owner-floor Target/Operation/Result -> Land(ⁿB) ->
R(H,Delta) -> next state decision`. A response that separates labels into global blobs has lost
the attachment needed to govern the next burden, even when the vocabulary looks correct.
For hard/compound/deformed Level 2 output, reconstruction faithfulness also asks whether the
owner's pressure dimensions can be recovered from the prose without printing a raw route field:
what premise, criterion, warrant, source-frame, predicate, testimony question, register, or
restoration vector was actually pressured, and what claim-state changed. If only owner labels,
generic Target/Operation/Result syntax, source citations, or closing restoration language can be
recovered, the render is plausible typed commentary rather than faithful compressed control state.
The same test applies to release sequencing: an auditor should be able to recover the nearest
held/deferred alternatives, any source-governed functions that were landed or held, and why the
next state is STOP, HOLD, PARTIAL, or RECURSE. If a compact render preserves only the first active
route and a final synthesis, it has not reconstructed the compound burden faithfully.

## Render Discipline

Default public output should not print the reconstruction ledger. The visible answer may show the
existing compact Layer A signal and case-specific `ⁿBᵢ -> Land(ⁿB) -> R(H,Delta)` work when needed.
The reconstruction witness belongs in trace/verdict evidence unless the user explicitly requests
diagnostic or audit render.
