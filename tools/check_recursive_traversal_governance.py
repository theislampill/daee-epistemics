#!/usr/bin/env python3
"""Check Phase 6 recursive traversal governance in source and runtime."""

from __future__ import annotations

import sys
import re
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


SOURCE_FILES = [
    "atomics/skill/SKILL.md",
    "atomics/skill/references/diagnostics/diagnostic-ir.md",
    "atomics/skill/references/diagnostics/framework-pipeline.md",
    "atomics/skill/references/diagnostics/recursive-state-transitions.md",
    "atomics/skill/references/diagnostics/anti-patterns.md",
    "atomics/skill/references/rubrics/output-release.md",
    "atomics/skill/references/rubrics/diagnostic-render-contract.md",
    "atomics/skill/references/procedures/P7-restoration-stops.md",
]

RUNTIME_FILES = [
    "SKILL.md",
    "references/runtime-dispatch-gate.md",
    "references/runtime-output-governance.md",
]

GLOBAL_INVARIANTS = [
    "state re-read",
    "eligible live burden",
    "held routes rechecked",
    "STOP / HOLD / RECURSE / PARTIAL",
    "no premature STOP",
    "recursion is not argument dump",
    "one live burden",
    "traversal-delayed, not permanently suppressed",
]

DECISION_INVARIANTS = [
    "STOP is valid only",
    "no eligible live burden",
    "post-render gate run before closure",
    "same-response RECURSE trigger checklist",
    "Current blocker cleared",
    "Another already-present burden remains live",
    "prose state-change transition",
    "module stacking",
    "Step 1",
    "Move 1 / Move 2 / Move 3",
    "essay sequencing",
    "first bounded move landed",
    "gate permits release",
    "next pass is bounded",
    "next live burden",
    "eligible same-input live burden remains",
    "silent closure while an eligible",
    "render a partial release-status reason in prose",
    "silently stopping after criterion correction",
    "clean prose without pipeline validity",
    "Clean Essay Failure",
    "topical essay sequencing",
    "TTP labels do not satisfy execution",
    "TTP label",
    "target -> operation -> result -> state re-read",
    "Route Cosplay Failure",
    "visible recursion label != recursive traversal",
    "Bounded does not mean tiny",
    "clean prose does not mean shallow",
    "no ledger does not mean no recursion",
    "governed recursive sufficiency",
    "The imported criterion no longer governs as judge",
    "one live burden per burden-cycle",
    "PARTIAL requires concrete limit reason",
    "A TTP label is not execution",
    "Clean Essay Cosplay",
    "Default multi-burden execution uses this repeated burden-cycle shape",
    "compact DSL/IR header",
    "Layer B - bounded governed response",
    "state re-read",
    "Current bounded operator",
    "hidden premises listed without operator result",
    "Moving from the current live burden to downstream doctrine requires state re-read prose",
    "RECURSE",
    "PARTIAL",
    "HOLD",
    "absent release signal",
    "limits prevent",
    # rc12: minimum visible transition spine
    "Default mode suppresses raw visible IR but does not suppress recursive execution",
    "If no transition marker appears",
    "essay organized by topic is not governed traversal",
    "minimum visible transition spine",
    "no further same-input eligible burden remains",
    # input-anchored recursion discipline
    "input-anchored",
    "component-tour cosplay",
    "topic transition",
    "enumerate remaining",
    "one bounded live burden per burden-cycle",
    # compact Layer A / Layer B / state re-read pass shape
    "single-pass layer a/b cosplay",
    "governing burden",
    "remaining input-anchored burdens",
    "compact state re-read",
    "Diagnostic-Reduction Bypass",
    "Route-Chain Collapse",
    "Route-Chain Recursion Cosplay",
    "Shallow Live-Burden Execution",
    "Current bounded operator is one live noetic burden/function",
    "current bounded operator is not a route chain",
    "Operative submoves are not burden-cycles",
    "A burden-cycle begins only after the current burden lands",
    "hiddenness/punishment/source-status can be operative submoves under one burden",
    "multi-burden does not mean multi-recursion by default",
    "imported tribunal / hiddenness / punishment / named source-worldview",
    "burden landing -> state re-read",
    "Restorative Response appears once after the final state/noetic re-read",
    "runtime-verifiable diagnostic compiler",
    "not a deterministic argument bank",
    "TTP Entry / Exit Criteria",
    "TTP entry criteria",
    "TTP exit criteria",
    "owner-specific operation floor",
    "Family Execution Floor",
    "Family Release Floor",
    "Diagnostic Execution Floor",
    "public-render permission",
    "model/predication discipline runs first and V12 remains held",
    "submove saturation gate",
    "NewB license test",
    "Land(B) requirements",
    "cumulative-state delta",
    "rubric-schematic",
    "output.md != trace.md != verdict.md",
    "Depth And Stop Guards",
    "No recursive depth increase without a burden landing and state re-read",
    "TTP entry before activation",
    "Layer A / Layer B release checks",
    "Layer A/B smuggling",
    "converge through controlled state transitions",
    "live noetic burden",
    "operative submove",
    "burden-cycle",
    "burden landed",
    "state re-read",
    "noetic re-read",
    "next live burden",
    "Operative-Submove Burden Split",
    "Operative-Submove Burden Split",
    # source-status and noetic-frame non-equivalence
    "Source-Status & Noetic-Frame Non-Equivalence Discipline",
    "N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡ N_Wahhābī",
    "family label != operative N",
    "shared vocabulary != shared warrant",
    "operative noetic frame",
    "noetic-equivalence prestige stack",
    "classical-theology umbrella",
    "contrast-as-operative-support",
    "intra-school flattening",
    "verbal-agreement smuggling",
    "Rule S-9",
    "Rule P-8",
    "thesis-protection",
    "operative support",
    "contrast",
    "opponent-position",
    "historical note",
    "genealogy",
    "held material",
    "bounded comparison",
    # grounded noetic re-read shape
    "Grounded Noetic Re-Read Shape",
    "Field-grounding rules",
    "ungrounded noetic re-read",
    "still live",
    "next licensed live burden",
    "burden landed",
    # positive default-mode worked-example anchors
    "Default-Mode Worked Example",
    "composition / dependence pressure",
    "Source-status: contrast only",
    # cosmetic IR, higher-order warrant, held-material, and operative-warrant guards
    "Decisive missing differentiator",
    "cosmetic-IR-formation guard",
    "higher-order vocabulary in the IR must be matched by a higher-order operator",
    "Held-routes carry rule (cross-cycle)",
    "held-material amnesia",
    "held-route semantic leakage",
    "Operative-warrant sentence convention",
    "Operative warrant:",
    "specific non-premise clause",
    "closed operative verbs",
    # rc16: positive RECURSE worked-example anchors
    "Submove Boundary",
    "materially necessary sub-burdens",
    "matched TTP/operator treatment",
    "burden-complete",
    "no headline-only answer",
    "not licensed until",
]

PASS_SHAPE_INVARIANTS = [
    "compact DSL/IR header",
    "read status:",
    "confidence:",
    "claim_level:",
    "pattern_profile:",
    "reason-category:",
    "concealment:",
    "deformation:",
    "DO-orient:",
    "live noetic burden:",
    "current bounded operator:",
    "held:",
    "source-status/noetic-frame:",
    "gate/release decision:",
    "bounded governed response",
    "Hidden Premises",
    "Burden / Operation",
    "Restorative Response",
    "Core Formulation",
    "Closing Formulation",
    "TTP/operator trace",
    "one Restorative Response",
    "one final Closing Formulation",
    "State/noetic re-read",
    "Live noetic burden:",
    "Why already present:",
    "Released module(s):",
    "Bounded move:",
    "state re-read:",
    "Release status: prose closure/hold/partial/continuation status",
]

FORBIDDEN_RECURSION_CLAIMS = [
    "compact governance sentence (e.g., \"Recursion decision: RECURSE",
    "may appear as a compact governance line at the close",
    "compact final-governance sentence naming the recursion decision is permitted",
    "must still name the recursion decision and next eligible pass",
    "Recursion decision: RECURSE → next pass",
    "Recursion decision: RECURSE may appear as a compact governance line at the close",
    "FPD/M1 landed",
    "the imported criterion has failed",
]

FIXTURE_REQUIRED_TOKENS = [
    "imported criterion is concretely identified",
    "criterion test is actually performed",
    "result changes case-state",
    "remaining same-input live burden is named or held with condition",
    "if recursion occurs, prose transition plus bounded next pass appears",
    "Clean Essay Cosplay",
    "compact DSL/IR header + Layer B + State/noetic re-read",
    "current bounded operator",
    "read status",
    "confidence",
    "claim_level",
    "pattern_profile",
    "reason-category",
    "concealment",
    "deformation",
    "DO-orient",
    "held",
    "source-status/noetic-frame",
    "gate/release decision",
    "decisive missing differentiator",
    "Moving from the current live burden to downstream doctrine requires state re-read prose",
    "hidden premises listed without operator result",
    # rc12: transition spine behavior shape
    "minimum visible transition spine",
    # input-anchored recursion discipline
    "component-tour cosplay",
    "input-anchored",
    # compact Layer A / Layer B / state re-read pass shape
    "single-pass layer a/b cosplay",
    "remaining input-anchored burdens",
    "route-chain bounded operator",
    "operative submoves",
    "diagnostic reduction",
    "route-chain collapse",
    "route-chain recursion cosplay",
    "shallow live-burden execution",
    "diagnostic-reduction bypass",
    "current bounded operator is one live noetic burden/function",
    "operative submoves are not burden-cycles",
    "runtime-verifiable diagnostic compiler",
    "TTP entry criteria",
    "TTP exit criteria",
    "Depth And Stop Guards",
    "Layer A / Layer B release checks",
    "deterministic argument bank",
    "Layer A/B smuggling",
    "live noetic burden",
    "operative submove",
    "burden-cycle",
    "burden landed",
    "state re-read",
    "noetic re-read",
    "Operative-Submove Burden Split",
    "hujjah/accountability can be operative submove only after same-function proof",
    "guidance-as-coercive-proof can be operative submove only after same-function proof",
    "hiddenness/punishment/source-status can be operative submoves under one burden",
    "multi-burden does not mean multi-recursion by default",
    "topical components split into burden-cycles",
    # source-status and grounded re-read fixture tokens
    "Source-Status & Noetic-Frame Non-Equivalence Discipline",
    "N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡ N_Wahhābī",
    "N_Ashʿarī[*]",
    "family label != operative N",
    "operative noetic frame",
    "Grounded Noetic Re-Read Shape",
    "ungrounded noetic re-read",
    "noetic-equivalence prestige stack",
    "classical-theology umbrella",
    "contrast-as-operative-support",
    "intra-school flattening",
    "Rule S-9",
    "Rule P-8",
    "still live",
    "next licensed live burden",
]

FIXTURE_FORBIDDEN_TOKENS = [
    "FPD/M1 landed",
    "the imported criterion has failed",
    "Recursion decision: RECURSE",
]

STRUCTURAL_BAD_OUTPUTS = {
    "literal_governance_label": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: PF-10
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: imported criterion
- current bounded operator: tribunal-detection
- held: none
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### Hidden Premises
- The objection imports a criterion.
#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector returns criterion to warrant.
##### Bounded Response / operative submoves
Target: imported criterion. Operation: test whether it can judge. Result: criterion no longer governs.
##### TTP/operator trace
- tribunal-detection: Target: criterion. Operation: test authority. Result: narrowed.
### state re-read
- What changed: the imported criterion no longer governs.
- Remaining input-anchored burdens: none
- Governance: STOP
### Restorative Response
The proper order is returned to warrant.
### Closing Formulation
The objection cannot close by printing a governance label.
""",
        "literal governance label in default output",
    ),
    "missing_default_compact_frame": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: hiddenness objection
- Current bounded operator: hiddenness rebuttal
### Layer B
The answer is readable but lacks the required compiler trace.
### state re-read
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "missing compact DSL/IR header",
    ),
    "recurse_without_next_pass": (
        """## Pass 1
### Layer A
- Governing burden: hiddenness objection
### Layer B
The current bounded pass clears the first burden.
### state re-read
- Remaining input-anchored burdens: punishment
- Release status: next bounded pass licensed because another input-anchored burden remains
""",
        "RECURSE without a later pass",
    ),
    "single_pass_stop_with_remaining_doors": (
        """## Pass 1
### Layer A
- Governing burden: imported criterion
### Layer B
This essay answers hiddenness and punishment together as one section.
### state re-read
- Remaining input-anchored burdens: hiddenness, punishment
- Release status: closed; no same-input eligible burden remains
""",
        "STOP with remaining input-anchored burdens",
    ),
    "route_list_cosplay": (
        """## Pass 1
### Layer A
Route: FPD -> M1 -> V2 -> DO-2 -> DO-15 -> DO-8 -> M8
### Layer B
The labels show the route.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "raw route chain",
    ),
    "route_chain_current_operator": (
        """## Pass 1
### Layer A
- Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration
### Layer B
The labels show the route.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "route chain as current bounded operator",
    ),
    "route_chain_recursion_cosplay": (
        """## Pass 1
FPD lists the hidden premises.
## Pass 2
M1 names the criterion problem.
## Pass 3
DO-8 discusses accountability.
## Pass 4
M8 traces consequences.
## Pass 5
Restoration closes the answer.
""",
        "route legs treated as burden-cycles",
    ),
    "door_without_state_refresh": (
        """## Pass 1
### Layer A
- Current bounded operator: worship-worthiness criterion test
### Layer B
The criterion is challenged and the answer moves on.
""",
        "live burden without state re-read",
    ),
    "restoration_before_refresh": (
        """## Pass 1
### Layer A
- Current bounded operator: imported-criterion tribunal test
### Layer B
Restoration: the coherent picture is now clear.
Pastoral note: be gentle.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "restoration before state re-read",
    ),
    "shallow_ttp_execution": (
        """## Pass 1
### Layer A
- Current bounded operator: M1
### Layer B
M1 and M8 are relevant here, so the worldview fails.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "shallow TTP execution",
    ),
    "missing_core_formulation": (
        """## Pass 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: imported tribunal
- current bounded operator: imported tribunal test
- held: none
- source-status/noetic-frame: selected operative frame
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### 1. Restorative Response
The selected operator tests the imported tribunal.
#### 3. Closing Formulation
The restored frame lands.
### State/noetic re-read
- Cleared: imported tribunal
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "missing Core Formulation",
    ),
    "missing_closing_formulation": (
        """## Pass 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: imported tribunal
- current bounded operator: imported tribunal test
- held: none
- source-status/noetic-frame: selected operative frame
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### 1. Restorative Response
The selected operator tests the imported tribunal.
#### 2. Core Formulation
1. The objection imports a criterion.
2. The criterion has not justified itself.
### State/noetic re-read
- Cleared: imported tribunal
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "missing Closing Formulation",
    ),
    "essay_only_output": (
        """The objection assumes that divine action must answer to a modern moral tribunal.
That tribunal is not neutral. Islam has a different account of mercy, guidance, accountability,
and worship-worthiness. Therefore the objection fails once the imported standard is exposed.""",
        "essay-only output",
    ),
    "meta_narration_opening": (
        """Now I will produce the governed response.
## Pass 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: imported tribunal
- current bounded operator: imported tribunal test
- held: none
- source-status/noetic-frame: selected operative frame
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### 1. Restorative Response
The selected operator tests the imported tribunal.
#### 2. Core Formulation
1. The objection imports a criterion.
#### 3. Closing Formulation
The restored frame lands.
### State/noetic re-read
- Cleared: imported tribunal
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "meta narration opening",
    ),
    "scaffold_language_in_default_output": (
        """## Pass 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: tribunal import
- reason-category: 3
- concealment: criterion import
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: imported tribunal
- current bounded operator: tribunal-detection
- held: downstream doctrine
- source-status/noetic-frame: selected operative frame
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### Hidden Premises
- The stated moral criterion is treated as judge without first being warranted.
#### Burden / Operation 1
##### Core Formulation
The deformation is imported criterion; the noetic pattern operates by replacing warrant with a tribunal; the restoration vector returns the criterion to proper order.
##### Bounded Response / operative submoves
Target: the imported moral criterion.
Operation: expose its borrowed authority.
Result: owner-floor pressure appears and the TTP has to change something.
##### TTP/operator trace
- tribunal-detection: Target: imported criterion. Operation: expose the borrowed judge. Result: the criterion is narrowed.
### State/noetic re-read
- Cleared: the criterion is no longer treated as self-authorizing.
- Cumulative-state delta: what changed is that the moral tribunal is narrowed from judge to claim requiring warrant.
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The proper order is returned to warrant before accusation.
### Closing Formulation
The objection cannot govern by an ungrounded judge.
""",
        "scaffold/test-harness language in default output",
    ),
    "formula_hinge_language_in_default_output": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: tribunal import
- reason-category: 3
- concealment: criterion import
- deformation: moral tribunal
- DO-orient: truth-seeking
- live noetic burden: imported criterion
- current bounded operator: tribunal-detection
- held: downstream doctrine
- source-status/noetic-frame: selected operative frame
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### Hidden Premises
- The objection imports a criterion.
#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector is to test the criterion.
##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: criterion. Operation: test whether it has authority. Result: the criterion cannot govern.
The load-bearing point is criterion authority. If that point is left vague, the reply can sound forceful while the actual claim remains untouched.
##### TTP/operator trace
Trace: tribunal-detection.
### State/noetic re-read
- What changed: the criterion is narrowed.
- Cleared: criterion
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The criterion is returned to warrant.
### Closing Formulation
The objection cannot govern by an ungrounded judge.
""",
        "scaffold/test-harness language in default output",
    ),
    "excessive_submoves_released": (
        """## Pass 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: imported tribunal
- current bounded operator: imported tribunal test
- held: downstream doctrine
- source-status/noetic-frame: selected operative frame
- gate/release decision: over-release
### Layer B - bounded governed response
#### 1. Restorative Response
Operative submove target: tribunal.
Operative submove target: hiddenness.
Operative submove target: punishment.
Operative submove target: transmission.
#### 2. Core Formulation
1. Four major moves were released in one Layer B.
#### 3. Closing Formulation
This is an argument dump.
### State/noetic re-read
- Cleared: unclear
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "excessive submoves released",
    ),
    "missing_ttp_operator_trace": (
        """## Pass 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: imported tribunal
- current bounded operator: imported criterion / moral tribunal test
- held: downstream doctrine
- source-status/noetic-frame: selected operative frame
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### 1. Restorative Response
The selected operator tests the imported tribunal.
#### 2. Core Formulation
1. The objection imports a criterion.
#### 3. Closing Formulation
The restored frame lands.
### State/noetic re-read
- Cleared: imported tribunal
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "missing TTP/operator trace",
    ),
    "unnamed_ttp_operation": (
        """## Pass 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: self-defeating criterion
- DO-orient: truth-seek
- live noetic burden: criterion reversal
- current bounded operator: self-defeating criterion test
- held: downstream doctrine
- source-status/noetic-frame: selected operative frame
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### Hidden Premises
- The criterion defeats itself.
#### Burden / Operation 1
##### Core Formulation
The deformation is self-defeating criterion import; the restoration vector is to test the criterion by its own demand.
##### Bounded Response / operative submoves
Target: the criterion. Operation: derive contradiction from its own demand. Result: the criterion cannot govern.
##### TTP/operator trace
Trace: FPD.
### State/noetic re-read
- Cleared: self-defeating criterion
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The criterion no longer governs.
### Closing Formulation
The bounded takeaway is criterion reversal.
""",
        "missing TTP/operator invocation",
    ),
    "headline_only_burden": (
        """## Pass 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: hiddenness / punishment composite
- current bounded operator: tribunal-detection
- held: downstream doctrine
- source-status/noetic-frame: selected operative frame
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### Hidden Premises
- The headline objection is treated as if it were already the whole burden.
#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector is to reject the headline objection.
##### Bounded Response / operative submoves
Operator: tribunal-detection.
The headline objection is wrong, so the whole objection collapses.
##### TTP/operator trace
Trace: tribunal-detection.
### State/noetic re-read
- Cleared: whole burden
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The burden is treated as cleared.
### Closing Formulation
The bounded takeaway is a broad conclusion.
""",
        "burden sub-burdens skipped",
    ),
    "raw_layer_a_leakage": (
        """## Pass 1
### Layer A
matched_modules: [FPD, M1, M8]
source_basis: inference
Diagnostic IR: visible
Case State: full
Concealment: irad
Deformation: hawa primary
Recursion decision: RECURSE
### Layer B
Public response.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "raw default machinery",
    ),
    "identity_source_status_overcertification": (
        """## Pass 1
### Layer A
The identity-performance layer is governing.
### Layer B
This is haw? primary, i?r?? primary, and possible juh?d.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "source-status over-certification",
    ),
    "ttp_label_without_operation": (
        """## Pass 1
### Layer A
- Current bounded operator: M1
### Layer B
This is the M1 move and then the M8 move.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "TTP labels without target-operation-result-refresh",
    ),
    "deterministic_argument_bank": (
        """## Pass 1
### Layer A
- Governing burden: evidence objection
### Layer B
Known rebuttal from the deterministic argument bank: here is the standard proof sequence.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "deterministic argument bank",
    ),
    "unguarded_ttp_recursion": (
        """## Pass 1
### Layer A
- Current bounded operator: imported-criterion tribunal test
### Layer B
The TTP route itinerary now proceeds through M1, M8, DO-8, and restoration from the initial read.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "TTP recursion without entry/exit criteria",
    ),
    "layer_ab_smuggling": (
        """## Pass 1
### Layer A
- Held routes: hiddenness and punishment held until criterion clears
### Layer B
Hiddenness is answered here, and punishment is answered here too.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "Layer A/B smuggling",
    ),
    "depth_drift": (
        """## Pass 1
### Layer A
- Current bounded operator: criterion test
### Layer B
The first point lands, then another section continues by prose momentum without state re-read.
""",
        "depth drift",
    ),
    "door_internal_operator_split": (
        """## Pass 1
### Layer A
- Current bounded operator: imported-criterion tribunal test
### Layer B
The secular criterion is challenged.
### state re-read
- Cleared: criterion exposed
- Remaining input-anchored burdens: accountability, hiddenness
- Next bounded pass: hujjah/accountability correction

## Pass 2
### Layer A
- Current bounded operator: hujjah/accountability correction
### Layer B
Accountability is corrected as a separate pass.
### state re-read
- Cleared: accountability narrowed
- Remaining input-anchored burdens: hiddenness
- Next bounded pass: guidance-as-coercive-proof correction

## Pass 3
### Layer A
- Current bounded operator: guidance-as-coercive-proof correction
### Layer B
Hiddenness is corrected as a third pass.
### state re-read
- Cleared: hiddenness narrowed
- Remaining input-anchored burdens: none
""",
        "Operative-Submove Burden Split",
    ),
    "topical_component_recursion_split": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: PF-10 moral protest / PF-2 evidentialist demand
- reason-category: 3
- concealment: clear
- deformation: imported moral criterion as tribunal
- DO-orient: mixed moral protest / evidential demand
- live noetic burden: imported tribunal
- current bounded operator: imported criterion / moral tribunal
- held: hiddenness; punishment; named source-worldview
- source-status/noetic-frame: named source-worldview tenets held as opponent-position
- gate/release decision: release tribunal test
### Layer B - bounded response
Operative submove. Target: tribunal authority. Operation: test against own grounds whether the imported criterion can judge divine action. Result: tribunal loosened.
Burden landed: imported tribunal no longer governs.
### State/noetic re-read
- Cleared: imported tribunal.
- Remaining input-anchored burdens: hiddenness, punishment, named source-worldview.
- Held routes rechecked: hiddenness, punishment, and named source-worldview are all promoted as separate next burdens without showing they survived as new burdens rather than submoves.
- Next bounded pass: hiddenness.

## Burden-Cycle 2
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: first-order
- pattern_profile: PF-2 evidentialist demand
- reason-category: 3
- concealment: clear
- deformation: evidence-demand pressure
- DO-orient: mixed moral protest / evidential demand
- live noetic burden: hiddenness
- current bounded operator: hiddenness-as-coercive-proof correction
- held: punishment; named source-worldview
- source-status/noetic-frame: no source-status discipline yet
- gate/release decision: release hiddenness
### Layer B - bounded response
Operative submove. Target: hiddenness. Operation: distinguish guidance from coercive proof. Result: hiddenness narrowed.
Burden landed: hiddenness handled.
### State/noetic re-read
- Cleared: hiddenness.
- Remaining input-anchored burdens: punishment, named source-worldview.
- Held routes rechecked: punishment is next.
- Next bounded pass: punishment.

## Burden-Cycle 3
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: first-order
- pattern_profile: PF-10 moral protest
- reason-category: 3
- concealment: clear
- deformation: moral indictment
- DO-orient: mixed moral protest / evidential demand
- live noetic burden: punishment
- current bounded operator: punishment/accountability correction
- held: named source-worldview
- source-status/noetic-frame: no source-status discipline yet
- gate/release decision: release punishment
### Layer B - bounded response
Operative submove. Target: punishment. Operation: narrow through hujjah/accountability. Result: punishment narrowed.
Burden landed: punishment handled.
### State/noetic re-read
- Cleared: punishment.
- Remaining input-anchored burdens: named source-worldview.
- Held routes rechecked: named source-worldview is next.
- Next bounded pass: named source-worldview.

## Burden-Cycle 4
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-noetic
- pattern_profile: none
- reason-category: 4
- concealment: clear
- deformation: source-status confusion
- DO-orient: mixed
- live noetic burden: named source-worldview
- current bounded operator: source-status discipline
- held: none
- source-status/noetic-frame: named source-worldview opponent-position
- gate/release decision: release source-status note
### Layer B - bounded response
Operative submove. Target: named source-worldview. Operation: classify it as opponent-position. Result: source-status marked.
Operative warrant: selected source-status discipline; the opponent-position source above does not contribute to this warrant; specifically, the named source-worldview is not used as a premise here.
Burden landed: named source-worldview classified.
### State/noetic re-read
- Cleared: named source-worldview.
- Remaining input-anchored burdens: none.
- Held routes rechecked: none.
- Next bounded pass: none.
""",
        "topical components split into burden-cycles",
    ),
    "ungrounded_noetic_re_read": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: imported moral tribunal
### Layer B
The tribunal has been addressed.

Noetic re-read:
- burden landed: yes
- still live: hiddenness, punishment
- held: none
- recursion decision: continue
- next licensed live burden: hiddenness
""",
        "ungrounded noetic re-read",
    ),
    "classical_theology_umbrella": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: attribute predication
### Layer B
The whole classical tradition agrees that this conclusion is correct.
### state re-read
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "classical-theology umbrella",
    ),
    "noetic_frame_equivalence_stack": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: imported moral criterion
### Layer B
Ash?ar?, M?tur?d?, and Taymiyyan approaches are all classically acceptable theological routes here.
### state re-read
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "noetic-equivalence prestige stack",
    ),
    "contrast_as_operative_support": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: attribute predication
### Layer B
Source-status: contrast only. A rival formulation is mentioned only as contrast.

Therefore, the operative answer is established by a contrast source together with the selected operative frame.
### state re-read
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "contrast-as-operative-support",
    ),
    "cosmetic_ir_no_differentiator": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: imported moral criterion
- Confidence: provisional
- Read status: underdetermined
### Layer B
The criterion has been engaged.
### state re-read
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "cosmetic IR without differentiator",
    ),
    "higher_order_vocabulary_theater": (
        """## Burden-Cycle 1
### Layer A
- Claim-level: meta-epistemic
- Pattern-profile: PF-2
- Governing burden: hiddenness
- Current bounded operator: hiddenness rebuttal from divine wisdom
### Layer B
The rebuttal is delivered.
### state re-read
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "higher-order claim_level with first-order bounded operator",
    ),
    "non_operative_operation_verb": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: imported criterion
### Layer B
Operative submove. Target: imported criterion. Operation: address the objection broadly. Result: the answer sounds complete.
Burden landed: imported criterion handled.
### state re-read
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "non-operative operation verb",
    ),
    "operative_warrant_missing_specific_clause": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: attribute predication
### Layer B
Source-status: contrast only. A later kalamic formulation is named as contrast.
Operative warrant: selected Athari frame; the contrast source above does not contribute to this warrant.
Burden landed: attribute predication is narrowed.
### state re-read
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "operative warrant missing specific non-premise clause",
    ),
    "held_route_semantic_leakage": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: imported criterion
- held: full punishment doctrine; hiddenness answer
### Layer B
The full punishment doctrine is answered here before the criterion has landed.
Burden landed: criterion handled.
### state re-read
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "held-route semantic leakage",
    ),
    "held_material_amnesia": (
        """## Burden-Cycle 1
### Layer A
- Governing burden: imported moral tribunal
- Held routes: hiddenness, punishment, foundational epistemology
### Layer B
The tribunal is tested.
Operative submove. Target: tribunal authority. Operation: test independence. Result: tribunal cannot stand unexamined.
Burden landed: tribunal no longer governs as judge.
### state re-read
- Cleared: imported moral tribunal exposed.
- Remaining input-anchored burdens: hiddenness, punishment.
- Held routes rechecked: foundational epistemology remains held.
- Next bounded pass: hiddenness.

## Burden-Cycle 2
### Layer A
- Governing burden: hiddenness
- Held routes:
### Layer B
Hiddenness is engaged.
Operative submove. Target: hiddenness-as-coercive-proof. Operation: distinguish guidance from coercive proof. Result: hiddenness loosens.
Burden landed: hiddenness no longer governs.
### state re-read
- Cleared: hiddenness loosened.
- Remaining input-anchored burdens: none.
- Release status: closed; no same-input eligible burden remains
""",
        "held-material amnesia",
    ),
    "audit_proof_in_default_output": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: truth-seek
- live noetic burden: criterion
- current bounded operator: tribunal-detection
- held: none
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
Skill invocation proof: SKILL.md loaded; proof of loaded files follows in output.md.
#### Hidden Premises
- A criterion is imported.
#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector is to test the criterion.
##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: criterion. Operation: test whether it has authority. Result: the criterion no longer governs.
##### TTP/operator trace
Trace: tribunal-detection.
### State/noetic re-read
- What changed: criterion authority is removed.
- Cleared: criterion
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The criterion is returned to its proper place.
### Closing Formulation
The answer closes from the landed operation.
""",
        "audit/proof boilerplate in default output",
    ),
    "rubric_schematic_output": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: truth-seek
- live noetic burden: criterion
- current bounded operator: tribunal-detection
- held: downstream doctrine
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### Hidden Premises
- A criterion is imported.
#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector is restoration.
##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: criterion. Operation: address the objection broadly. Result: this burden lands.
##### TTP/operator trace
Trace: tribunal-detection.
### State/noetic re-read
- Cleared: criterion
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The restored order is restored.
### Closing Formulation
The burden lands.
""",
        "rubric-schematic output",
    ),
    "pressure_dimension_label_only": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: first-order
- pattern_profile: predication/category pressure
- reason-category: 3
- concealment: clear
- deformation: category pressure
- DO-orient: truth-seek
- live noetic burden: attribute predication
- current bounded operator: predication-mode repair
- held: broad attribute exposition
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### Hidden Premises
- Predication is being treated as if every real attribute becomes a separable part.
#### Burden / Operation 1
##### Core Formulation
The deformation is predication confusion; the noetic pattern is category pressure; the restoration vector is to clear terms.
##### Bounded Response / operative submoves
Operator: M9-predication-mode.
Target: attribute terms. Operation: pressure dimensions are satisfied. Result: owner pressure dimensions applied.
##### TTP/operator trace
Trace: M9-predication-mode.
### State/noetic re-read
- Cleared: predication
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The terms are now in order.
### Closing Formulation
The burden closes.
""",
        "scaffold/test-harness language in default output",
    ),
    "fake_recursion_without_delta": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: truth-seek
- live noetic burden: criterion
- current bounded operator: tribunal-detection
- held: model/predication
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator
### Layer B - bounded governed response
#### Hidden Premises
- A criterion is imported.
#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector is to test the criterion.
##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: criterion. Operation: test whether it has authority. Result: the criterion cannot govern.
##### TTP/operator trace
Trace: tribunal-detection.
### State/noetic re-read
- Cleared: criterion
- Remaining input-anchored burdens: model/predication
- Release status: next bounded pass licensed because another input-anchored burden remains

## Burden-Cycle 2
### Layer A - Compact DSL/IR header
- current bounded operator: model/predication
### Layer B
The next topic is discussed.
### state re-read
- Release status: closed; no same-input eligible burden remains
""",
        "fake recursion without cumulative-state delta",
    ),
    "shallow_v12_execution": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: first-order
- pattern_profile: divine plurality pressure
- reason-category: 2
- concealment: clear
- deformation: plurality disorder
- DO-orient: truth-seek
- live noetic burden: multiple lords
- current bounded operator: V12 / tamanu
- held: model details
- source-status/noetic-frame: operative frame selected
- gate/release decision: release V12
### Layer B - bounded governed response
#### Hidden Premises
- Multiple gods are treated as coherent.
#### Burden / Operation 1
##### Core Formulation
The deformation is plurality disorder; the noetic pattern is independent-lordship confusion; the restoration vector is to restore unity of lordship.
##### Bounded Response / operative submoves
Operator: tamanu.
Target: multiple gods. Operation: say independent lords conflict. Result: divine plurality is incoherent.
##### TTP/operator trace
Trace: V12-tamanuc-exhaustion.
### State/noetic re-read
- What changed: the plurality claim is said to fail.
- Cleared: multiple lords
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
Unity of lordship is restored.
### Closing Formulation
The plurality claim fails.
""",
        "shallow V12 execution",
    ),
    "shallow_m9_execution": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: first-order
- pattern_profile: predication disorder
- reason-category: 2
- concealment: clear
- deformation: one-three confusion
- DO-orient: truth-seek
- live noetic burden: Trinity predication
- current bounded operator: M9 predication-mode
- held: V12
- source-status/noetic-frame: operative frame selected
- gate/release decision: release M9
### Layer B - bounded governed response
#### Hidden Premises
- Predication is unstable.
#### Burden / Operation 1
##### Core Formulation
The deformation is predication disorder; the noetic pattern is identity/counting instability; the restoration vector is predication repair.
##### Bounded Response / operative submoves
Operator: M9 predication-mode.
Target: Trinity. Operation: mention person and nature. Result: the objection is unclear.
##### TTP/operator trace
Trace: M9-predication-mode.
### State/noetic re-read
- What changed: predication is mentioned.
- Cleared: Trinity predication
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
Predication is restored.
### Closing Formulation
The one-three issue is unclear.
""",
        "shallow M9 execution",
    ),
    "v12_before_independence_gate": (
        """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: first-order
- pattern_profile: Trinitarian model pressure
- reason-category: 2
- concealment: clear
- deformation: one-three predication
- DO-orient: truth-seek
- live noetic burden: Trinity model/predication
- current bounded operator: V12 / tamanu
- held: M9 model identification
- source-status/noetic-frame: operative frame selected
- gate/release decision: release V12 first
### Layer B - bounded governed response
#### Hidden Premises
- Trinity is treated as independent-lordship pressure before person/nature is split.
#### Burden / Operation 1
##### Core Formulation
The deformation is predication disorder; the noetic pattern is one-three instability; the restoration vector is to test multiple independent lords.
##### Bounded Response / operative submoves
Operator: tamanu.
Target: Trinity. Operation: run V12 before deciding whether independent lordship is actually live. Result: the model/predication gate is bypassed.
##### TTP/operator trace
Trace: V12-tamanuc-exhaustion.
### State/noetic re-read
- What changed: V12 was run from the Trinity label.
- Cleared: Trinity
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
Plurality is rejected.
### Closing Formulation
The Trinity is answered by V12 first.
""",
        "V12 before independence gate",
    ),
}

STRUCTURAL_POSITIVE_OUTPUTS = {
    "single_burden_multiple_submoves": """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: PF-10 moral protest / PF-2 evidentialist demand
- reason-category: 3
- concealment: clear; identity-performance not certified
- deformation: imported moral criterion as tribunal
- DO-orient: mixed moral protest / evidential demand
- live noetic burden: imported criterion / moral tribunal
- current bounded operator: tribunal-detection / worship-worthiness criterion burden
- held: broad punishment doctrine; full synthesis
- source-status/noetic-frame: operative frame selected; external context held
- gate/release decision: release tribunal test with subordinate hiddenness/accountability/source-status submoves

### Layer B - bounded governed response
#### Hidden Premises
- The objection imports a moral criterion as tribunal.
- Hiddenness and accountability are supports inside that same released burden.

#### Burden / Operation 1
##### Core Formulation
The deformation is tribunal import; the noetic pattern is authority displacement through worship-worthiness pressure; the restoration vector is to test the tribunal and its necessary supports before downstream doctrine is released.

##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: tribunal authority. Operation: test whether the imported criterion has justified authority over divine action. Result: the tribunal cannot remain unexamined.

Operator: reason-disambiguation.
Target: hiddenness-as-coercive-proof. Operation: disambiguate hiddenness as a support for the tribunal rather than a separate released burden. Result: hiddenness no longer props up the same indictment as an untested proof demand.

Operator: authority-order repair.
Target: punishment/accountability support. Operation: narrow the claim through accountability while holding broad doctrine. Result: the accusation is no longer treated as punishment for mere non-belief inside this burden.

##### TTP/operator trace
Trace: tribunal-detection + reason-disambiguation + authority-order repair + FPD + M1 + output-release.

### State/noetic re-read
- What changed: the imported tribunal no longer governs as judge; subordinate supports have been narrowed inside the same burden.
- Cleared: imported moral tribunal; hiddenness, accountability, and source-status treated as subordinate supports for that tribunal.
- Remaining input-anchored burdens: none newly licensed in this prompt.
- Held routes rechecked: broad punishment doctrine and full synthesis remain held.
- Next live burden: none unless a later prompt supplies a burden not already handled as a submove.

### Restorative Response
The restored order is that the imported tribunal and its supports no longer judge worship-worthiness without first bearing warrant.

### Closing Formulation
What cleared is the borrowed tribunal's authority; what remains held is broader punishment doctrine and full synthesis; the governed takeaway is bounded restoration rather than an argument dump.
""",
    "grounded_noetic_re_read_with_contrast": """## Burden-Cycle 1
### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-ontological
- pattern_profile: none
- reason-category: 2
- concealment: clear
- deformation: category pressure / none primary certified
- DO-orient: truth-seek
- live noetic burden: attribute predication and composition pressure
- current bounded operator: predication-mode repair for composition and dependence pressure
- held: broader attribute exposition
- source-status/noetic-frame: operative frame selected; school/source contrast not rendered
- gate/release decision: release lexical/category correction; hold contrast formulation

### Layer B - bounded governed response
#### Hidden Premises
- The objection treats conceptual distinction as separable part-composition.

#### Burden / Operation 1
##### Core Formulation
The deformation is category pressure on predication; the noetic pattern is equivocation between distinction and separable composition; the restoration vector is to repair predication before wider exposition is released.

##### Bounded Response / operative submoves
Operator: predication-mode repair.
Target: the loaded term "composition". Operation: split ordinary conceptual distinction from separable part-composition. Result: the objection's move from real attributes to composite parts no longer follows.

##### TTP/operator trace
Trace: predication-mode repair + M9-predication-mode + diagnostic-render-contract.

### State/noetic re-read
- What changed: the composition-dependence inference no longer follows from the predication shift.
- Cleared: composition pressure dissolved through lexical/category split.
- Remaining input-anchored burdens: none
- Held routes rechecked: broader attribute exposition remains held.
- Release status: closed; no same-input eligible burden remains

### Restorative Response
The restored order is that predication is not collapsed into dependence merely because the mind can distinguish meanings.

### Closing Formulation
What cleared is the composition-dependence inference; what remains held is broader attribute exposition; the governed takeaway is that the objection no longer follows from its operative category shift.
""",
}

SMOKE_VERDICT_BAD_SAMPLES = {
    "pass_with_unresolved_checker_gap": (
        """# verdict

status: PASS

## Failure cause
none

## Checker gap
No checker currently enforces the owner-specific V12 operation floor.
""",
        "PASS verdict with unresolved checker gaps",
    ),
}

PASS_HEADER_RE = re.compile(r"(?im)^##\s*(?:Pass|Burden-Cycle)\s+(\d+)\b")
GOVERNANCE_RECURSE_RE = re.compile(
    r"(?im)^\s*-?\s*(?:Governance:\s*RECURSE|Release status:\s*"
    r"(?:next bounded pass licensed|continue|continuation))\b"
)
GOVERNANCE_STOP_RE = re.compile(
    r"(?im)^\s*-?\s*(?:Governance:\s*STOP|Release status:\s*closed)\b"
)
LITERAL_DEFAULT_GOVERNANCE_RE = re.compile(
    r"(?im)^\s*-?\s*(?:Governance|Release status|Closure|recursion decision)\s*:\s*"
    r"(?:STOP|HOLD|RECURSE|PARTIAL)\b"
)
REMAINING_DOORS_RE = re.compile(
    r"(?ims)^\s*-?\s*Remaining input-anchored (?:doors|burdens):\s*(.+?)"
    r"(?=^\s*(?:-?\s*)?(?:Held routes rechecked|Next bounded pass|Release status|Governance|###|##)\b|\Z)"
)
ROUTE_CHAIN_RE = re.compile(
    r"\bFPD\s*(?:->|->|->)\s*M1\s*(?:"
    r"(?:->|->|->)\s*(?:V2|DO-2|DO-15|DO-8|M8|restoration)\s*){2,}",
    re.IGNORECASE,
)
CURRENT_OPERATOR_RE = re.compile(r"(?im)current bounded operator:\s*(?P<value>.+)$")
ROUTE_LABEL_LIST_RE = re.compile(r"\b(?:FPD|M1|M8|DO-\d+|restoration)\b", re.IGNORECASE)
INTERNAL_PASS_COSPLAY_RE = re.compile(
    r"(?is)##\s*Pass\s+1\b.*?\bFPD\b.*?##\s*Pass\s+2\b.*?\bM1\b"
    r".*?##\s*Pass\s+3\b.*?\bDO-8\b",
)
TTP_LABEL_RE = re.compile(r"\b(?:the\s+)?(?:M1P|M1-P|M1|M8|M9)\s+move\b", re.IGNORECASE)
DOOR_INTERNAL_OPERATOR_SPLIT_RE = re.compile(
    r"(?is)##\s*(?:Pass|Burden-Cycle)\s+1\b"
    r"(?:(?!##\s*(?:Pass|Burden-Cycle)\s+2\b).)*current bounded operator:\s*.*(?:imported|tribunal|worship)"
    r".*?##\s*(?:Pass|Burden-Cycle)\s+2\b"
    r"(?:(?!##\s*(?:Pass|Burden-Cycle)\s+3\b).)*current bounded operator:\s*.*(?:hujjah|accountability)"
    r".*?##\s*(?:Pass|Burden-Cycle)\s+3\b"
    r"(?:(?!##\s*(?:Pass|Burden-Cycle)\s+4\b).)*current bounded operator:\s*.*(?:hiddenness|guidance-as-coercive-proof)"
)
TOPICAL_COMPONENT_RECURSION_SPLIT_RE = re.compile(
    r"(?is)##\s*(?:Pass|Burden-Cycle)\s+1\b"
    r"(?:(?!##\s*(?:Pass|Burden-Cycle)\s+2\b).)*(?:imported|tribunal|moral tribunal)"
    r".*?##\s*(?:Pass|Burden-Cycle)\s+2\b"
    r"(?:(?!##\s*(?:Pass|Burden-Cycle)\s+3\b).)*hiddenness"
    r".*?##\s*(?:Pass|Burden-Cycle)\s+3\b"
    r"(?:(?!##\s*(?:Pass|Burden-Cycle)\s+4\b).)*(?:punishment|accountability|hell)"
    r".*?##\s*(?:Pass|Burden-Cycle)\s+4\b"
    r"(?:(?!##\s*(?:Pass|Burden-Cycle)\s+5\b).)*(?:source-worldview|source-status|tenets)"
)

NOETIC_RE_READ_BLOCK_RE = re.compile(
    r"(?im)^\s*Noetic re-read\s*:\s*$",
)
CLASSICAL_UMBRELLA_RE = re.compile(
    r"(?i)\b("
    r"classical (?:islamic )?theological tradition"
    r"|classical (?:islamic )?theologies"
    r"|whole classical tradition"
    r"|the classical tradition"
    r"|mainstream kalam"
    r"|ashari/maturidi tradition"
    r")\b"
)
NOETIC_EQUIVALENCE_STACK_RE = re.compile(
    r"(?is)(?:Ash[?']?ar[?i].{0,40}M[?a]tur[?i]d[?i].{0,40}"
    r"(?:Taymiyy|Athar[?i]|athar[?i]|kal[?a]mic).{0,80}"
    r"(?:classically acceptable|all (?:classically )?acceptable|peer[- ]valid|equally acceptable|all provide acceptable|one unified)"
    r"|classically acceptable theological routes)"
)
CONTRAST_THEN_OPERATIVE_RE = re.compile(
    r"(?is)source-status\s*:\s*contrast[^\n]{0,200}\n(?:[^\n]*\n){0,6}\s*"
    r"(?:therefore|thus|hence|so)\b[^\n]{0,200}\b(?:operative answer|operative conclusion|operative warrant|established by)\b"
)
NON_OPERATIVE_SOURCE_STATUS_RE = re.compile(
    r"(?i)source-status\s*:\s*(?:contrast|opponent-position|historical note|genealogy|held material|bounded comparison)"
)
OPERATIVE_WARRANT_LINE_RE = re.compile(r"(?im)^\s*Operative warrant:\s*(?P<value>.+)$")
OPERATIVE_WARRANT_SPECIFIC_RE = re.compile(
    r"(?i)does not contribute to this warrant;\s*specifically,\s+.+?\s+is not used as a premise here\.?"
)
OPERATION_LINE_RE = re.compile(r"(?i)\bOperation:\s*(?P<value>[^\n]+)")
ALLOWED_OPERATION_START_RE = re.compile(
    r"(?i)^(?:split\b|split ordinary\b|distinguish\b|test\b|test against own grounds\b|test whether\b|"
    r"derive contradiction\b|derive consequence\b|disambiguate\b|classify\b|audit\b|reclassify\b|narrow\b|"
    r"narrow the claim\b|expose\b|re-read\b|sequence\b|refuse jurisdiction\b|refuse jurisdiction of\b|"
    r"clear\b|run\b|route\b|hold\b|cite\b)"
)
WEAK_CONFIDENCE_RE = re.compile(
    r"(?im)^\s*-?\s*Confidence\s*:\s*(provisional|low)\b"
)
WEAK_READ_STATUS_RE = re.compile(
    r"(?im)^\s*-?\s*Read status\s*:\s*(underdetermined|distributed)\b"
)
DECISIVE_DIFFERENTIATOR_RE = re.compile(
    r"(?i)decisive missing differentiator"
)
HIGHER_ORDER_CLAIM_LEVEL_RE = re.compile(
    r"(?im)^\s*-?\s*Claim-level\s*:\s*(meta-epistemic|meta-ontological|meta-noetic|cross-level)\b"
)
HIGHER_ORDER_OPERATOR_KEYWORDS = [
    "criterion", "tribunal", "authority order", "authority-order",
    "semantic", "predication", "category", "category-set",
    "source-status", "identity stabilization", "identity-stabilization",
    "foundational", "warrant", "validation order", "validation-order",
    "imported", "usurpation",
]
PASS_BOUNDED_OPERATOR_RE = re.compile(
    r"(?im)^\s*-?\s*Current bounded operator\s*:\s*(?P<value>.+)$"
)
DEFAULT_FRAME_HEADING_RE = re.compile(
    r"(?im)^\s*#{3,4}\s*Layer A\s*(?:\u2014|-)\s*Compact (?:DSL/IR header|diagnostic frame)\b"
)
DEFAULT_FRAME_REQUIRED_RE = [
    re.compile(r"(?im)^\s*-?\s*read status\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*confidence\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*claim_level\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*pattern_profile\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*reason-category\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*concealment\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*deformation\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*DO-orient\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*live noetic burden\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*current bounded operator\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*held\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*source-status/noetic-frame\s*:\s*.+$"),
    re.compile(r"(?im)^\s*-?\s*gate/release decision\s*:\s*.+$"),
]
RESTORATIVE_RESPONSE_RE = re.compile(
    r"(?im)^\s*#{3,5}\s*(?:\d+\.\s*)?Restorative Response\b"
)
HIDDEN_PREMISES_RE = re.compile(r"(?im)^\s*#{3,5}\s*Hidden Premises\b")
CORE_FORMULATION_RE = re.compile(
    r"(?im)^\s*#{3,6}\s*(?:\d+\.\s*)?Core Formulation\b"
)
CLOSING_FORMULATION_RE = re.compile(
    r"(?im)^\s*#{3,5}\s*(?:\d+\.\s*)?Closing Formulation\b"
)
LAYER_B_GOVERNED_RE = re.compile(
    r"(?im)^\s*#{3,5}\s*Layer B\s*(?:\u2014|-)\s*bounded governed response\b"
)
META_NARRATION_OPENING_RE = re.compile(
    r"(?is)^\s*(?:now i|i now|let me|i will now|i'll now)\b"
)
MAJOR_SUBMOVE_RE = re.compile(
    r"(?im)^\s*(?:Operative submove target:|(?:Move|Step)\s+\d+\s*:|#{3,6}\s*(?:Move|Submove)\s+\d+\b)"
)
NON_TRIVIAL_OPERATOR_RE = re.compile(
    r"(?im)^\s*-?\s*current bounded operator\s*:\s*.*"
    r"(?:criterion|tribunal|composition|predication|source-status|warrant|worship-worthiness)"
)
TRACE_RE = re.compile(
    r"(?im)^\s*(?:#{3,6}\s*)?(?:TTP/operator trace|TTP/module trace|Owner trace|Trace)\b"
)
NAMED_OPERATOR_RE = re.compile(
    r"(?i)\b(?:reductio|tamanu|tam[?a]nu[?']?|criterion-reversal|tribunal-detection|"
    r"predication repair|authority-order repair|predication-mode|self-refutation|"
    r"source-status check|pattern-first routing|reason-disambiguation|foreign-premise detection|"
    r"perfection-criterion-usurpation|model-identification gate|V10|transmission-content vetting|"
    r"V2|reconstituting reason|accountability correction|hiddenness criterion correction|"
    r"direct-source accountability anchor|kernel-thesis guard|definition discipline|"
    r"ordered-world pressure|DO-\d+ discriminator)\b"
)
OPERATIONAL_LANGUAGE_RE = re.compile(
    r"(?i)\b(?:derive contradiction|contradiction from|cannot satisfy its own|"
    r"test whether|test the criterion|authority over|predicate|predication|"
    r"criterion cannot|tribunal cannot|target:|operation:|result:)\b"
)
BOUNDED_OPERATION_RE = re.compile(r"(?is)target:.*?operation:.*?result:")
HEADLINE_ONLY_BYPASS_RE = re.compile(
    r"(?i)\b(?:headline objection|whole objection collapses|broad conclusion|"
    r"jump directly|skip(?:s|ped)? internal sub-burdens|generic prose)\b"
)
AUDIT_PROOF_BOILERPLATE_RE = re.compile(
    r"(?i)\b(?:smoke runtime note|runtime grounding detail|skill invocation proof|"
    r"loaded before output|proof of loaded files|output\.md\s*!=\s*trace\.md|"
    r"trace\.md|verdict\.md|checker proof)\b"
)
SCAFFOLD_LANGUAGE_RE = re.compile(
    r"(?i)\b(?:this smoke artifact|runtime constraint being tested|owner floor is applied|"
    r"owner-floor pressure|the TTP has to change something|burden-completeness check|"
    r"the operation is bounded to the target named above|target named above|test harness|"
    r"smoke scaffold|runtime artifact|generic owner-floor|"
    r"generic target/operation/result boilerplate|repeated generic paragraphs|"
    r"that test changes the force of the case|the result is a real state change|"
    r"what remains after that change is not forgotten|filled compliance frame|"
    r"pressure dimensions are satisfied|pressure dimension is satisfied|"
    r"pressure dimensions applied|owner pressure dimensions|"
    r"load-bearing point|if that point is left vague|this exact pressure can stand|"
    r"surrounding topic is held back|the live hinge can be tested|live hinge can be tested|"
    r"case-state after this pressure|the move forces the inference to carry its own burden)\b"
)
RUBRIC_SCHEMATIC_RE = re.compile(
    r"(?i)\b(?:this burden lands|the burden lands|burden lands|"
    r"restored order is restored|address the objection broadly|predication is mentioned)\b"
)
STATE_BLOCK_RE = re.compile(
    r"(?ims)^\s*#{3,5}\s*(?:State/noetic re-read|state re-read)\b(?P<body>.*?)"
    r"(?=^\s*#{3,5}\s*(?:Restorative Response|Closing Formulation|Burden / Operation|Layer B)\b|"
    r"^\s*##\s*(?:Pass|Burden-Cycle)\s+\d+\b|\Z)"
)
STATE_DELTA_RE = re.compile(
    r"(?i)\b(?:what changed|cumulative-state delta|state-change|state delta|"
    r"narrowed|no longer governs|now exposed|now licensed|now blocked|"
    r"returned as not-yet-target)\b"
)
V12_OPERATOR_RE = re.compile(r"(?i)\b(?:V12|tamanu|tam[?a]nu[?']?|multiple independent lords?)\b")
V12_PREMATURE_TRINITY_RE = re.compile(
    r"(?is)\b(?:Trinity|Trinitarian)\b(?:(?!independent lordship|worship-status plurality).){0,1200}"
    r"\b(?:V12|tamanu|tam[?a]nu[?']?)\b"
)
V12_DIMENSION_TERMS = [
    "dependency",
    "derivation",
    "equality",
    "unequal",
    "joint causation",
    "influence",
    "creation",
    "independent lordship",
]


def v12_before_independence_gate(text: str) -> bool:
    """Reject V12 only when the released operation lacks the owner gate."""
    for match in V12_OPERATOR_RE.finditer(text):
        start = max(
            text.rfind("## Burden-Cycle", 0, match.start()),
            text.rfind("#### Burden / Operation", 0, match.start()),
        )
        block = text[start if start != -1 else 0 : match.end() + 240].lower()
        if (
            "independent lordship" not in block
            and "worship-status plurality" not in block
            and "multiple independent" not in block
        ):
            return True
    return False


M9_OPERATOR_RE = re.compile(r"(?i)\b(?:M9|predication-mode|predication repair|person/nature|one-three)\b")
M9_TRINITY_TRIGGER_RE = re.compile(r"(?i)\b(?:Trinity|Trinitarian|person|nature|one-three)\b")
PASS_VERDICT_RE = re.compile(r"(?im)^\s*(?:status\s*:\s*)?PASS\b")
UNRESOLVED_CHECKER_GAP_RE = re.compile(
    r"(?is)(?:checker gap|unresolved checker|remaining checker|not currently enforced)"
    r".{0,240}(?:no checker|not currently enforced|missing checker|gap|unresolved)"
)
DEFAULT_SOURCE_PARADE_RE = re.compile(
    r"(?i)\b(?:named authorities?|named scholars?|contradictory authorities?|"
    r"school-label|classical tradition|whole classical tradition)\b"
)
METHOD_SOURCE_BRANDING_RE = re.compile(
    r"(?i)\bdaee-epistemics\b.{0,120}\b(?:named scholar|named school|ash'?ari|"
    r"maturidi|new creed|new aqidah|new noetics|methodology|founded)\b"
)
COMPARATIVE_NEUTRAL_RE = re.compile(
    r"(?i)\b(?:all traditions|all systems|all religions|religions)\b.{0,140}"
    r"\b(?:interchangeable|one neutral comparative system|same abstract noetic pattern|"
    r"same neutral pattern)\b"
)
REVEALED_TEXT_RE = re.compile(r"(?i)\b(?:qur'?an|sunnah|salaf)\b")
DIRECT_SOURCE_RE = re.compile(
    r"(?i)\b(?:https?://|quran\.com|sunnah\.com|sahih|surah|qur'?an\s+\d+:\d+|"
    r"bukhari|muslim|tirmidhi|abu dawud|nasai|ibn majah)\b"
)
RESTORATION_BEFORE_REREAD_RE = re.compile(
    r"(?im)^\s*(?:#{3,5}\s*)?(?:Restoration|Pastoral note|Restorative Response)\s*:?"
)
HELD_ROUTES_RE = re.compile(
    r"(?im)^\s*-?\s*(?:Held routes|held)\s*:\s*(?P<value>.*)$"
)
CLEARED_LINE_RE = re.compile(
    r"(?im)^\s*-?\s*Cleared\s*:\s*(?P<value>.+)$"
)
RELEASED_LINE_RE = re.compile(
    r"(?im)^\s*-?\s*(?:Newly released routes|Released routes|Released)\s*:\s*(?P<value>.+)$"
)

EMPTY_DOOR_MARKERS = {
    "none",
    "none.",
    "no eligible live burden remains",
    "no input-anchored eligible burden remains",
    "no further same-input eligible burden remains",
}
STOP_PROOF_MARKERS = [
    "no eligible",
    "no further same-input eligible burden remains",
    "no input-anchored eligible burden remains",
    "hold because",
    "held because",
    "partial because",
    "blocked by",
    "release condition absent",
]
RAW_DEFAULT_MARKERS = [
    "matched_modules",
    "source_basis",
    "Diagnostic IR",
    "Case State",
    "Concealment: irad",
    "Deformation: hawa primary",
    "Recursion decision: RECURSE",
    "Governance: STOP",
    "Governance: HOLD",
    "Governance: RECURSE",
    "Governance: PARTIAL",
]
OVER_CERTIFICATION_MARKERS = [
    "haw? primary",
    "hawa primary",
    "i?r?? primary",
    "irad primary",
    "possible juh?d",
    "possible juhud",
    "identity-performance layer is governing",
]
SOURCE_STATUS_QUALIFIERS = [
    "source-status",
    "differentiating signal",
    "thin input",
    "provisional",
    "underdetermined",
    "not certified",
    "cannot certify",
    "public statement alone",
]


def read_file(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing file: {path.as_posix()}")
        return ""
    return path.read_text(encoding="utf-8")


def contains(corpus: str, token: str) -> bool:
    return token.lower() in corpus.lower()


def held_items(raw: str) -> set[str]:
    value = raw.lower().strip()
    if not value or value in EMPTY_DOOR_MARKERS:
        return set()
    value = re.sub(r"\b(held|withheld|remains held|not yet released|until|because)\b.*", "", value)
    parts = re.split(r"[;,]|\s+and\s+", value)
    items = set()
    for part in parts:
        item = re.sub(r"[^a-z0-9 /-]+", "", part).strip()
        if len(item) > 3 and item not in EMPTY_DOOR_MARKERS:
            items.add(item)
    return items


def layer_b_before_refresh(block: str) -> str:
    match = re.search(
        r"(?is)###?\s*Layer B[^\n]*\n(?P<body>.*?)(?=###?\s*(?:State/noetic re-read|state re-read)|##\s*(?:Pass|Burden-Cycle)|\Z)",
        block,
    )
    return match.group("body") if match else ""


def phrase_is_topical_commitment(body: str, phrase: str) -> bool:
    lowered = body.lower()
    start = lowered.find(phrase)
    while start != -1:
        window = lowered[max(0, start - 80) : start + len(phrase) + 80]
        if not any(marker in window for marker in ("held", "withheld", "not released", "remains held", "contrast only")):
            return True
        start = lowered.find(phrase, start + 1)
    return False


def check_tokens(label: str, corpus: str, tokens: list[str], errors: list[str]) -> None:
    for token in tokens:
        if not contains(corpus, token):
            errors.append(f"{label}: missing invariant token: {token!r}")


def has_state_reread(lower_text: str) -> bool:
    return (
        "state re-read" in lower_text
        or "state/noetic re-read" in lower_text
        or "state refresh" in lower_text
    )


def first_state_reread_pos(lower_text: str) -> int:
    positions = [
        pos
        for marker in ("state re-read", "state/noetic re-read", "state refresh")
        if (pos := lower_text.find(marker)) != -1
    ]
    return min(positions) if positions else -1


def structural_default_output_violations(text: str) -> list[str]:
    lower = text.lower()
    violations: list[str] = []
    pass_headers = list(PASS_HEADER_RE.finditer(text))
    layer_b_match = re.search(r"(?is)###\s*Layer B[^\n]*\n(?P<body>.*)", text)
    layer_b_text = layer_b_match.group("body") if layer_b_match else text

    if META_NARRATION_OPENING_RE.search(text):
        violations.append("meta narration opening")

    if LITERAL_DEFAULT_GOVERNANCE_RE.search(text):
        violations.append("literal governance label in default output")

    if AUDIT_PROOF_BOILERPLATE_RE.search(text):
        violations.append("audit/proof boilerplate in default output")

    if SCAFFOLD_LANGUAGE_RE.search(text):
        violations.append("scaffold/test-harness language in default output")

    if "layer a" not in lower and "restorative response" not in lower and len(text) > 80:
        violations.append("essay-only output")

    if pass_headers:
        if not DEFAULT_FRAME_HEADING_RE.search(text):
            violations.append("missing compact DSL/IR header")
        elif not all(pattern.search(text) for pattern in DEFAULT_FRAME_REQUIRED_RE):
            violations.append("missing compact DSL/IR header anchors")
        if not LAYER_B_GOVERNED_RE.search(text):
            violations.append("missing bounded governed Layer B")
        if LAYER_B_GOVERNED_RE.search(text) and not HIDDEN_PREMISES_RE.search(text):
            violations.append("missing Hidden Premises")
        if not RESTORATIVE_RESPONSE_RE.search(text):
            violations.append("missing Restorative Response")
        if not CORE_FORMULATION_RE.search(text):
            violations.append("missing Core Formulation")
        if not CLOSING_FORMULATION_RE.search(text):
            violations.append("missing Closing Formulation")

    if len(MAJOR_SUBMOVE_RE.findall(text)) > 3:
        violations.append("excessive submoves released")

    if RUBRIC_SCHEMATIC_RE.search(layer_b_text):
        violations.append("rubric-schematic output")

    if NON_TRIVIAL_OPERATOR_RE.search(text) and not TRACE_RE.search(text):
        violations.append("missing TTP/operator trace")

    if OPERATIONAL_LANGUAGE_RE.search(layer_b_text) and not NAMED_OPERATOR_RE.search(layer_b_text):
        violations.append("missing TTP/operator invocation")

    if NAMED_OPERATOR_RE.search(layer_b_text) and not BOUNDED_OPERATION_RE.search(layer_b_text):
        violations.append("TTP named without bounded operation")

    if HEADLINE_ONLY_BYPASS_RE.search(layer_b_text):
        violations.append("burden sub-burdens skipped")

    if DEFAULT_SOURCE_PARADE_RE.search(layer_b_text):
        violations.append("default source/citation parade")

    if METHOD_SOURCE_BRANDING_RE.search(layer_b_text):
        violations.append("method-source branding")

    if COMPARATIVE_NEUTRAL_RE.search(layer_b_text):
        violations.append("comparative-neutral flattening")

    if REVEALED_TEXT_RE.search(layer_b_text) and not DIRECT_SOURCE_RE.search(layer_b_text):
        violations.append("revealed source without direct reference")

    for state in STATE_BLOCK_RE.finditer(text):
        if not STATE_DELTA_RE.search(state.group("body")):
            violations.append("weak state/noetic re-read")
            break

    if V12_OPERATOR_RE.search(layer_b_text):
        if v12_before_independence_gate(text):
            violations.append("V12 before independence gate")
        v12_lower = layer_b_text.lower()
        dimension_hits = sum(1 for term in V12_DIMENSION_TERMS if term in v12_lower)
        if dimension_hits < 3:
            violations.append("shallow V12 execution")

    if M9_OPERATOR_RE.search(layer_b_text) and M9_TRINITY_TRIGGER_RE.search(layer_b_text):
        m9_lower = layer_b_text.lower()
        required_terms = ["person", "nature", "is god", "one", "three"]
        if not all(term in m9_lower for term in required_terms):
            violations.append("shallow M9 execution")

    state_pos = first_state_reread_pos(lower)
    restorative_positions = [match.start() for match in RESTORATIVE_RESPONSE_RE.finditer(text)]
    closing_positions = [match.start() for match in CLOSING_FORMULATION_RE.finditer(text)]
    if len(restorative_positions) > 1:
        violations.append("multiple Restorative Responses")
    if len(closing_positions) > 1:
        violations.append("multiple Closing Formulations")
    if state_pos != -1 and restorative_positions and restorative_positions[0] < state_pos:
        violations.append("restoration before state re-read")
    if state_pos != -1 and closing_positions and closing_positions[0] < state_pos:
        violations.append("Closing Formulation before state/noetic re-read")
    if restorative_positions and closing_positions and closing_positions[0] < restorative_positions[0]:
        violations.append("Closing Formulation before Restorative Response")

    for recurse in GOVERNANCE_RECURSE_RE.finditer(text):
        state_window = text[max(0, recurse.start() - 700) : recurse.end() + 200]
        if not STATE_DELTA_RE.search(state_window):
            violations.append("fake recursion without cumulative-state delta")
        if not any(
            header.start() > recurse.end() and int(header.group(1)) > 1
            for header in pass_headers
        ):
            violations.append("RECURSE without a later pass")

    for remaining in REMAINING_DOORS_RE.finditer(text):
        door_text = remaining.group(1).strip().lower()
        if door_text and door_text not in EMPTY_DOOR_MARKERS:
            window = text[remaining.end() : remaining.end() + 400].lower()
            if GOVERNANCE_STOP_RE.search(window):
                if "held" not in window or "absent release" not in window:
                    violations.append("STOP with remaining input-anchored burdens")

    if ROUTE_CHAIN_RE.search(text):
        violations.append("raw route chain")

    for operator in CURRENT_OPERATOR_RE.finditer(text):
        value = operator.group("value")
        label_hits = ROUTE_LABEL_LIST_RE.findall(value)
        if "->" in value or "->" in value or len(set(label.upper() for label in label_hits)) >= 3:
            violations.append("route chain as current bounded operator")
        if re.fullmatch(r"\s*(?:M1|M8|M9|DO-\d+)\s*", value, flags=re.IGNORECASE):
            if not all(marker in lower for marker in ["target", "operation", "result"]) or not has_state_reread(lower):
                violations.append("shallow TTP execution")

    if INTERNAL_PASS_COSPLAY_RE.search(text):
        violations.append("route legs treated as burden-cycles")

    if DOOR_INTERNAL_OPERATOR_SPLIT_RE.search(text):
        violations.append("Operative-Submove Burden Split")

    if TOPICAL_COMPONENT_RECURSION_SPLIT_RE.search(text):
        violations.append("topical components split into burden-cycles")

    if pass_headers and not has_state_reread(lower):
        violations.append("live burden without state re-read")

    layer_b_pos = lower.find("### layer b")
    search_start = layer_b_pos if layer_b_pos != -1 else 0
    first_refresh = first_state_reread_pos(lower[search_start:])
    if first_refresh != -1:
        first_refresh += search_start
    pre_refresh_text = text[search_start:first_refresh] if first_refresh != -1 else text[search_start:]
    if RESTORATION_BEFORE_REREAD_RE.search(pre_refresh_text):
        violations.append("restoration before state re-read")

    if any(marker.lower() in lower for marker in RAW_DEFAULT_MARKERS):
        violations.append("raw default machinery")

    has_ttp_label = bool(TTP_LABEL_RE.search(text))
    has_operation_spine = all(
        marker in lower for marker in ["target", "operation", "result"]
    ) and has_state_reread(lower)
    if has_ttp_label and not has_operation_spine:
        violations.append("TTP labels without target-operation-result-refresh")

    for operation in OPERATION_LINE_RE.finditer(text):
        value = operation.group("value").strip()
        if value and not ALLOWED_OPERATION_START_RE.match(value):
            violations.append("non-operative operation verb")
            break

    if "deterministic argument bank" in lower or "known rebuttal" in lower:
        if "validated ir" not in lower or not has_state_reread(lower):
            violations.append("deterministic argument bank")

    if "ttp route itinerary" in lower or "initial read" in lower:
        if "entry criteria" not in lower or "exit criteria" not in lower:
            violations.append("TTP recursion without entry/exit criteria")

    if "held routes:" in lower and "### layer b" in lower:
        layer_b = lower.split("### layer b", 1)[1]
        refresh_pos = first_state_reread_pos(layer_b)
        before_refresh = layer_b if refresh_pos == -1 else layer_b[:refresh_pos]
        if any(term in before_refresh for term in ["hiddenness is answered", "punishment is answered"]):
            violations.append("Layer A/B smuggling")

    if "prose momentum" in lower and (
        "without state refresh" in lower or "without state re-read" in lower or not has_state_reread(lower)
    ):
        violations.append("depth drift")

    has_over_certification = any(marker.lower() in lower for marker in OVER_CERTIFICATION_MARKERS)
    has_source_status_qualification = any(
        marker in lower for marker in SOURCE_STATUS_QUALIFIERS
    )
    if has_over_certification and not has_source_status_qualification:
        violations.append("source-status over-certification")

    if NOETIC_RE_READ_BLOCK_RE.search(text):
        layer_b_text = ""
        layer_b_match = re.search(r"(?is)###?\s*Layer B[^\n]*\n(.*?)(?=Noetic re-read:|###\s*(?:state/noetic re-read|state re-read)|##\s*(?:Pass|Burden-Cycle))", text)
        if layer_b_match:
            layer_b_text = layer_b_match.group(1).lower()
        landed_yes = re.search(
            r"(?im)^\s*-?\s*burden\s+landed\s*:\s*(yes|true|landed)\b",
            text,
        )
        has_operative_spine = (
            "target:" in layer_b_text
            or "operation:" in layer_b_text
            or ("target" in layer_b_text and "operation" in layer_b_text and "result" in layer_b_text)
        )
        if landed_yes and not has_operative_spine:
            violations.append("ungrounded noetic re-read")

    if CLASSICAL_UMBRELLA_RE.search(text):
        violations.append("classical-theology umbrella")

    if NOETIC_EQUIVALENCE_STACK_RE.search(text):
        violations.append("noetic-equivalence prestige stack")

    if CONTRAST_THEN_OPERATIVE_RE.search(text):
        violations.append("contrast-as-operative-support")

    if NON_OPERATIVE_SOURCE_STATUS_RE.search(text):
        warrant = OPERATIVE_WARRANT_LINE_RE.search(text)
        if not warrant or not OPERATIVE_WARRANT_SPECIFIC_RE.search(warrant.group("value")):
            violations.append("operative warrant missing specific non-premise clause")

    weak_confidence = WEAK_CONFIDENCE_RE.search(text)
    weak_read_status = WEAK_READ_STATUS_RE.search(text)
    if (weak_confidence or weak_read_status) and not DECISIVE_DIFFERENTIATOR_RE.search(text):
        violations.append("cosmetic IR without differentiator")

    higher_order = HIGHER_ORDER_CLAIM_LEVEL_RE.search(text)
    if higher_order:
        operator_match = PASS_BOUNDED_OPERATOR_RE.search(text)
        if operator_match:
            operator_value = operator_match.group("value").lower()
            if not any(keyword in operator_value for keyword in HIGHER_ORDER_OPERATOR_KEYWORDS):
                violations.append("higher-order claim_level with first-order bounded operator")

    pass_blocks = list(PASS_HEADER_RE.finditer(text))
    if pass_blocks:
        released_so_far: set[str] = set()
        for index, header in enumerate(pass_blocks):
            start = header.end()
            end = pass_blocks[index + 1].start() if index + 1 < len(pass_blocks) else len(text)
            block = text[start:end]
            held_match = HELD_ROUTES_RE.search(block)
            if held_match:
                layer_b_text = layer_b_before_refresh(block)
                for item in held_items(held_match.group("value")):
                    if item not in released_so_far and phrase_is_topical_commitment(layer_b_text, item):
                        violations.append("held-route semantic leakage")
                        break
            released_match = RELEASED_LINE_RE.search(block)
            if released_match:
                released_so_far.update(held_items(released_match.group("value")))

    if len(pass_blocks) >= 2:
        held_entries: list[set[str]] = []
        cleared_entries: list[set[str]] = []
        released_entries: list[set[str]] = []
        for index, header in enumerate(pass_blocks):
            start = header.end()
            end = pass_blocks[index + 1].start() if index + 1 < len(pass_blocks) else len(text)
            block = text[start:end]
            held_match = HELD_ROUTES_RE.search(block)
            held_set: set[str] = set()
            if held_match:
                held_set = held_items(held_match.group("value"))
            held_entries.append(held_set)
            cleared_match = CLEARED_LINE_RE.search(block)
            cleared_set: set[str] = set()
            if cleared_match:
                cleared_set = set(cleared_match.group("value").strip().lower().split())
            cleared_entries.append(cleared_set)
            released_match = RELEASED_LINE_RE.search(block)
            released_set: set[str] = set()
            if released_match:
                released_set = held_items(released_match.group("value"))
            released_entries.append(released_set)

        for index in range(1, len(pass_blocks)):
            prior_held = held_entries[index - 1]
            current_held = held_entries[index]
            cleared_text = " ".join(cleared_entries[index - 1])
            released = released_entries[index - 1]
            if not prior_held:
                continue
            for item in prior_held:
                if item in current_held:
                    continue
                if any(token in item for token in released):
                    continue
                if any(token for token in cleared_text.split() if token and token in item):
                    continue
                if not current_held:
                    violations.append("held-material amnesia")
                    break
                violations.append("held-material amnesia")
                break

    return violations


def check_structural_bad_output_samples(errors: list[str]) -> None:
    for name, (sample, expected_violation) in STRUCTURAL_BAD_OUTPUTS.items():
        violations = structural_default_output_violations(sample)
        if expected_violation not in violations:
            errors.append(
                "structural bad-output sample was not rejected: "
                f"{name} expected {expected_violation!r}, got {violations!r}"
            )


def check_structural_positive_output_samples(errors: list[str]) -> None:
    for name, sample in STRUCTURAL_POSITIVE_OUTPUTS.items():
        violations = structural_default_output_violations(sample)
        if violations:
            errors.append(
                "structural positive-output sample was rejected: "
                f"{name} got {violations!r}"
            )


def smoke_verdict_violations(text: str) -> list[str]:
    if PASS_VERDICT_RE.search(text) and UNRESOLVED_CHECKER_GAP_RE.search(text):
        return ["PASS verdict with unresolved checker gaps"]
    return []


def check_smoke_verdict_bad_samples(errors: list[str]) -> None:
    for name, (sample, expected_violation) in SMOKE_VERDICT_BAD_SAMPLES.items():
        violations = smoke_verdict_violations(sample)
        if expected_violation not in violations:
            errors.append(
                "smoke verdict bad sample was not rejected: "
                f"{name} expected {expected_violation!r}, got {violations!r}"
            )


def main() -> int:
    root = repo_root()
    compiled_root = out_dir(root)
    errors: list[str] = []

    source_texts = [read_file(root / rel, errors) for rel in SOURCE_FILES]
    source_corpus = "\n".join(source_texts)

    if not compiled_root.is_dir():
        return fail_with_errors("recursive traversal governance", ["skill runtime root is absent"])

    runtime_texts = [read_file(compiled_root / rel, errors) for rel in RUNTIME_FILES]
    runtime_corpus = "\n".join(runtime_texts)

    check_tokens("atomized source", source_corpus, GLOBAL_INVARIANTS, errors)
    check_tokens("generated runtime", runtime_corpus, GLOBAL_INVARIANTS, errors)
    check_tokens("generated runtime decision semantics", runtime_corpus, DECISION_INVARIANTS, errors)
    check_tokens("generated runtime recursive pass shape", runtime_corpus, PASS_SHAPE_INVARIANTS, errors)

    for token in FORBIDDEN_RECURSION_CLAIMS:
        if contains(source_corpus, token) or contains(runtime_corpus, token):
            errors.append(f"stale recursion-label permission remains: {token!r}")

    if not contains(
        source_corpus,
        "Default mode must not print literal state fields",
    ):
        errors.append(
            "atomized source: recursive owner does not ban literal default state fields"
        )
    if not contains(
        runtime_corpus,
        "Default mode must not print literal state fields",
    ):
        errors.append(
            "generated runtime: recursive owner does not ban literal default state fields"
        )

    fixture_path = (
        root
        / "tests/routing-fixtures/11-secular-moral-protest-hiddenness-imported-criterion.json"
    )
    if fixture_path.is_file():
        fixture_text = fixture_path.read_text(encoding="utf-8")
        for token in FIXTURE_REQUIRED_TOKENS:
            if not contains(fixture_text, token):
                errors.append(f"fixture 11 missing recursive behavior token: {token!r}")
        for token in FIXTURE_FORBIDDEN_TOKENS:
            if contains(fixture_text, token):
                errors.append(f"fixture 11 still rewards recursion label cosplay: {token!r}")
    else:
        errors.append("fixture 11 missing for recursive traversal drift guard")

    check_structural_bad_output_samples(errors)
    check_structural_positive_output_samples(errors)
    check_smoke_verdict_bad_samples(errors)

    # Make sure the critical STOP/RECURSE distinction is represented in more
    # than one generated surface, so it is not lost if one section is skipped.
    stop_surfaces = sum(1 for text in runtime_texts if contains(text, "no premature STOP"))
    door_surfaces = sum(1 for text in runtime_texts if contains(text, "eligible live burden"))
    if stop_surfaces < 2:
        errors.append("generated runtime: no premature STOP invariant appears in fewer than two runtime surfaces")
    if door_surfaces < 2:
        errors.append("generated runtime: eligible live burden invariant appears in fewer than two runtime surfaces")

    print("Recursive traversal governance summary")
    print("------------------------------------------------------------")
    print(f"Source files checked: {len(SOURCE_FILES)}")
    print(f"Runtime files checked: {len(RUNTIME_FILES)}")
    print(f"Global invariants checked: {len(GLOBAL_INVARIANTS)}")
    print(f"Decision invariants checked: {len(DECISION_INVARIANTS)}")
    print(f"Pass-shape invariants checked: {len(PASS_SHAPE_INVARIANTS)}")
    print(f"Forbidden recursion-label permissions checked: {len(FORBIDDEN_RECURSION_CLAIMS)}")
    print(f"Fixture 11 recursive behavior tokens checked: {len(FIXTURE_REQUIRED_TOKENS)}")
    print(f"Structural bad-output samples checked: {len(STRUCTURAL_BAD_OUTPUTS)}")
    print(f"Structural positive-output samples checked: {len(STRUCTURAL_POSITIVE_OUTPUTS)}")
    print(f"Smoke verdict bad samples checked: {len(SMOKE_VERDICT_BAD_SAMPLES)}")
    print(f"Runtime no-premature-STOP surfaces: {stop_surfaces}")
    print(f"Runtime eligible-live-burden surfaces: {door_surfaces}")
    print("------------------------------------------------------------")
    return fail_with_errors("recursive traversal governance", errors)


if __name__ == "__main__":
    sys.exit(main())
