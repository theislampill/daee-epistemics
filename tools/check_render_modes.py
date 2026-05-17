#!/usr/bin/env python3
"""Check render-mode governance in the generated runtime.

Invariants verified:
  - Public render modes and deprecated audit compatibility are named in the runtime.
  - Default mode has a mandatory noetic-field execution banner and compact DSL/IR header with no giant ledger by default.
  - [Diagnostic IR] code-fenced block is prohibited in default output.
  - Full [Case State] block is prohibited in default output.
  - Discipline-universal / printout-mode-specific invariant is present.
  - Full recursion in every mode; full ledger only in internal/development audit.
  - :dsl owns compact diagnostic / lab-report output (gating condition required).
  - :audit is deprecated as public output and retained for internal/development audit compatibility.
  - recursive-audit discipline applies universally; full audit printout belongs only to internal/development audit.
  - Recursive traversal governance is universal across modes.
  - Plain /daee-epistemics does NOT map to expanded diagnostic lab-report.
  - Noetic-field execution banner and compact Layer A DSL/IR header are required in default mode.
  - Layer A full audit machinery is prohibited in default mode.
  - Forbidden claims (behavioral parity, mandatory ledger, stale expanded-diagnostic mapping) are absent.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


RUNTIME_FILES = [
    "SKILL.md",
    "references/runtime-output-governance.md",
    "references/runtime-dispatch-gate.md",
]

CURRENT_GOVERNANCE_DOCS = [
    "README.md",
    "AGENTS.md",
    "docs/compiled-runtime-tools.md",
    "docs/recursive-traversal-governance.md",
]

STALE_CURRENT_DOC_TOKENS = [
    "state refresh",
    "eligible live door",
    "eligible-live-door",
    "live door:",
    "one door at a time",
    "compact diagnostic frame",
    "clean default `/daee-epistemics` mode",
    "clean default response with internal recursive governance",
    "fuller `/daee-epistemics:audit` mode",
    "fuller procedural audit closest to the old prompt's visible ledger",
    "recursive governance remains internal unless",
]

# Tokens that must appear somewhere in the combined runtime surfaces.
REQUIRED_TOKENS = [
    # Public render modes plus deprecated audit compatibility
    "/daee-epistemics",
    "/daee-epistemics:dsl",
    "/daee-epistemics:audit",
    # Default mode has a mandatory noetic-field execution banner plus compact DSL/IR header
    "Default Output Surface Invariant",
    "For plain `/daee-epistemics`, internal governance is mandatory and default visibly prints",
    "noetic-field execution banner",
    "NOETIC FIELD EXECUTION",
    "first visible content",
    "Markdown fences",
    "Clarifying or missing-input replies are still runtime outputs",
    "field: <LOCAL CLAIM | NAMED WORLDVIEW | SOURCE-AUTHENTICATION | MIXED NOETIC FIELD>",
    "user task: <RESPOND | REFUTE | DIAGNOSE | EXPLAIN | SOURCE-AUTHENTICATION | OTHER>",
    "external source request: <NONE EXPLICIT | IMPLICIT | EXPLICIT>",
    "authority frame: <NONE DETECTED | LIVE>",
    "state: <RECURSE | PARTIAL | COMPLETE>",
    "Print exactly one value for each field",
    "never print the choice list",
    "combine values with `|`",
    "`user task: REFUTE`",
    "`external source request: NONE EXPLICIT`",
    "do not mark it `IMPLICIT` merely because a",
    "worldview or authority frame is live",
    "supplies no actual text/reference",
    "relational field states",
    "scalar summaries",
    "Scalar collapse is an execution failure",
    "target-explicit",
    "not restricted to `κ`",
    "General noetic-selection / register-control reread gate",
    "do not assume the selected N frame is known at design time",
    "candidate/held N frames",
    "Delta-nB",
    "Delta-kappa",
    "It may not STOP or mark COMPLETE while downstream dependencies remain",
    "Prompt brevity does not imply simple execution",
    "Do not use SIMPLE, COMPACT",
    "banner categories or",
    "depth licenses",
    "Closure audit must match the",
    "banner state",
    "`matched_modules` and route plans remain internal",
    "literal `Recursion decision:`",
    "`next_eligible_pass`",
    "Full diagnostic blocks belong to `/daee-epistemics:dsl` or internal/development audit",
    "compact DSL/IR header",
    "- read status:",
    "- confidence:",
    "- claim_level:",
    "- pattern_profile:",
    "- reason-category:",
    "- concealment:",
    "- deformation:",
    "- DO-orient:",
    "- live noetic burden:",
    "- current bounded operator:",
    "- held:",
    "- source-status/noetic-frame:",
    "- decisive missing differentiator: [only when required]",
    "- gate/release decision:",
    "bounded governed response",
    "Hidden Premises",
    "Burden / Operation",
    "Restorative Response",
    "Core Formulation",
    "Bounded Response / operative submoves",
    "Closing Formulation",
    "TTP/operator trace",
    "one Restorative Response",
    "one final Closing Formulation",
    "not a general essay",
    "missing Core Formulation",
    "Closing Formulation is required once",
    "essay-only Layer B",
    "more-than-three major operative submoves trigger",
    "no invisible TTP execution",
    "source citation substituted for TTP invocation",
    "Source architecture collapsed into final restoration",
    "Family-local pressure flattened into generic worldview response",
    "source-thin surface compliance",
    "scholar/source/citation parade",
    "burden-complete",
    "submove saturation gate",
    "NewB license test",
    "owner-specific operation floor",
    "Family Execution Floor",
    "Family Release Floor",
    "Diagnostic Execution Floor",
    "public-render permission",
    "model/predication discipline runs first and V12 remains held",
    "cumulative-state delta",
    "rubric-schematic",
    "output.md != trace.md != verdict.md",
    "no headline-only answer",
    "not licensed until",
    "Pattern(deformation/concealment/unsoundness) > denomination/source-label",
    "Named denomination/source identity is never sufficient to route content",
    "Named frameworks/schools/authors/genealogies are not public-render material",
    "Only Qurʾān, Sunnah, and sound Salaf narrations may be cited by default",
    "how sound/innate reason has been deformed",
    "what criterion/source/warrant is returned to its proper place",
    "State/noetic re-read",
    "default compact DSL-governed surface",
    "giant load ledger by default",
    "prose-first",
    # Last-mile default output preflight
    "Default Final-Output Preflight Gate",
    "scan the proposed final response",
    "final-output gate, not a render preference",
    "not merely a visible-format sanitizer",
    "checks pipeline validity",
    "clean prose without pipeline validity",
    "response is invalid and must be rewritten before output",
    "Rewrite-before-output rule",
    "Output-release decides what may be released",
    "Diagnostic-render-contract decides how it appears",
    "the preflight gate enforces both",
    "V1 / diagnosis ran before answer",
    "Diagnostic IR formed internally before routing",
    "Routing came from validated IR",
    "Output-release rubric applied before visible render",
    "Render contract applied before final prose",
    "Post-render gate run before closure",
    "STOP / HOLD / RECURSE / PARTIAL decision made before ending",
    # Early internal-vs-visible scoping
    "Internal governance and visible render are distinct",
    "internal control surfaces where triggered",
    "The full IR is",
    "Default output is governed prose rendered from the internal state plus the mandatory compact",
    "not an optional internal gate or control surface",
    "Literal default governance fields",
    "`Governance:`",
    "literal governance fields such as `Recursion decision:`",
    "PARTIAL / RECURSE / COMPLETE decision needed to prevent false closure",
    "Render-mode scope: this template is an internal control shape",
    "Route Cosplay Failure",
    "visible recursion label != recursive traversal",
    "Bounded does not mean tiny",
    "clean prose does not mean shallow",
    "no ledger does not mean no recursion",
    "governed recursive sufficiency",
    "TTPs are surgical interventions, not essay sections",
    "Layer A contrast pairs",
    "Rule: prose diagnostic fact is allowed; field-style printout is not default output",
    "The objection imports a moral tribunal",
    "Visible block format is internal/development audit / diagnostic-trace only",
    "The imported criterion no longer governs as judge",
    "hujjah/accountability correction",
    "guidance-as-coercive-proof correction",
    "identity-frame may stabilize",
    "held downstream content",
    "PARTIAL requires concrete limit reason",
    "one live burden per burden-cycle",
    "PARTIAL requires concrete limit reason",
    "A TTP label is not execution",
    "Emission means internal case-state / IR update for routing",
    "Internal NS/PF emission for routing means case-state / IR update",
    "no named-example route",
    "no default raw IR/Case State/route ledger",
    "Clean Essay Cosplay",
    "Default multi-burden execution uses this repeated burden-cycle shape",
    "Layer A - compact DSL/IR header",
    "Layer B - bounded governed response",
    "State/noetic re-read - compact",
    "Current bounded operator",
    "Let me check",
    "I will produce governed prose",
    "file loading, searching, setup, readiness, or composition",
    "do not run repo checkers, route tools, smoke-artifact",
    "do not add harness verdicts",
    "Do not add source links, sanity scans",
    "keep explicit `Land(Bn)`",
    "The public identity-frame may stabilize the criterion or affect discourse orientation",
    "Identity is a modal/stabilizing node",
    "not the primary verdict-bearing load-bearer",
    "hidden premises listed without operator result",
    "Moving from the current live burden to downstream doctrine requires state re-read prose",
    "The imported criterion no longer governs as judge",
    # Discipline is universal; printout is mode-specific
    "discipline is universal",
    "printout is mode-specific",
    # Named invariant: full recursion in every mode; full ledger only in internal/development audit
    "full recursion in every mode",
    "full ledger only in internal/development audit",
    # recursive-audit discipline vs printout distinction
    "recursive-audit discipline applies",
    "full audit printout",
    # IR is internal, not a printout template
    "internal state object",
    "not a printout template",
    # Default mode prohibition: IR block must not appear in public response
    "must not appear in the public response",
    "Meta-composition prefixes",
    "Now I have enough",
    "Now I have enough to compose",
    "I now have enough",
    "I now have sufficient",
    "I now have sufficient grounding",
    "Let me compose",
    "Let me write",
    "Let me write it",
    "Let me craft",
    "Let me construct the diagnostic IR",
    "I'll now compose",
    "Diagnostic IR (Internal - Governing the Response)",
    # Default mode prohibition: full [Case State] must not appear
    "full `[Case State]`",
    "Case State:",
    "matched_modules",
    "source_basis",
    "route ledger",
    "planned route list",
    "Next: FPD",
    "Concealment:",
    "Deformation:",
    "NS-4/NS-5 compound",
    # Default mode prohibition: Load Ledger must not appear
    "Load Ledger",
    # Default mode prohibition: Render Permission Check must not appear
    "Render Permission Check",
    # Default source-list/bibliography suppression
    "bibliography",
    "Primary Sources Referenced",
    "source-basis ledger",
    # Compact Layer A DSL/IR header required in default mode
    "compact Layer A",
    "mandatory compact DSL/IR header",
    "default compact DSL/IR header",
    # DSL mode owns compact diagnostic (gating condition required)
    "compact diagnostic",
    "gating condition",
    # Audit mode is internal/development only
    "deprecated internal/development audit compatibility",
    # Recursion shape for default mode: visible through state-transition progression
    "bounded move",
    "state-transition progression",
    "prose state-change transition",
    "module stacking",
    "Layer A is the compact diagnostic/control surface",
    "governed operation/release surface",
    "Layer A overgrowth",
    "Layer B flattening",
    "Burden-cycle recursion follows live noetic order",
    "Burden recursion is licensed by live noetic order",
    "first-order",
    "second-order",
    "higher-order/meta-noetic",
    "truth-directed",
    "reliable warrant-process",
    "foundational order",
    "Move 1 / Move 2 / Move 3",
    "Step 1",
    "essay sequencing",
    "topical essay sequencing",
    "clean essay",
    "next live burden",
    "silent closure while an eligible",
    "render a partial release-status reason in prose",
    "silently stopping after criterion correction",
    # TTPs must execute, not merely be named in prose
    "TTP activation",
    "TTP execution",
    "validated case-state / IR",
    "the M1 move",
    "the M8 move",
    "bounded target",
    "operation performed",
    "result of the operation",
    "target -> operation -> result -> state re-read",
    # Identity diagnostic guardrail: relevant but not a shortcut verdict
    "identity may be part of the noetic equilibrium, but it cannot by itself carry the verdict",
    "modal/stabilizing node",
    "alone does not prove motive",
    "source-status",
    "creates no new route, PF code, IR field, or module owner",
    # Recursive governance is universal
    "Diagnostic IR",
    "state re-read",
    "live burden",
    "held routes",
    "STOP / HOLD / RECURSE / PARTIAL",
    # Path resolution invariants
    "bundle availability is not activation",
    "compiled-module-map.json",
    # Deprecated legacy recursive-audit prompt
    "former external recursive-audit prompt is deprecated",
    # execution mandate: minimum visible transition spine
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
    "layer a must not show",
    "Diagnostic-Reduction Bypass",
    "Route-Chain Collapse",
    "Route-Chain Recursion Cosplay",
    "Shallow Live-Burden Execution",
    "Current bounded operator is one live noetic burden/function",
    "current bounded operator is not a route chain",
    "Operative submoves are not burden-cycles",
    "hiddenness/punishment/source-status can be operative submoves under one burden",
    "multi-burden does not mean multi-recursion by default",
    "Same-burden collapse must preserve operator identity",
    "why it is live for that burden",
    "Anti-overcollapse guard",
    "Opposite guard: do not overcollapse distinct input-anchored burden families",
    "Practical handling becomes NewB only",
    "must not compress distinct source functions into one citation stack",
    "it cannot substitute for",
    "burden-local source operation",
    "imported tribunal / hiddenness / punishment / named source-worldview",
    "A burden-cycle begins only after the current burden lands",
    "burden landing -> state re-read",
    "Restoration synthesis",
    "runtime-verifiable diagnostic compiler",
    "not a deterministic argument bank",
    "TTP Entry / Exit Criteria",
    "TTP entry criteria",
    "TTP exit criteria",
    "Depth And Stop Guards",
    "No recursive depth increase without a burden landing and state re-read",
    "TTP entry before activation",
    "Layer A / Layer B release checks",
    "Layer A/B smuggling",
    "converge through controlled state transitions",
    # source-status and noetic-frame non-equivalence in render
    "Source-Status & Noetic-Frame Non-Equivalence Discipline",
    "Rule S-9",
    "Rule P-8",
    "N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡ N_Wahhābī",
    "family label != operative N",
    "shared vocabulary != shared warrant",
    "operative noetic frame",
    "noetic-equivalence prestige stack",
    "classical-theology umbrella",
    "contrast-as-operative-support",
    "intra-school flattening",
    "verbal-agreement smuggling",
    "operative support",
    "contrast",
    "opponent-position",
    "historical note",
    "genealogy",
    "held material",
    "bounded comparison",
    # rc14: grounded noetic re-read
    "Grounded Noetic Re-Read Shape",
    "Field-grounding rules",
    "ungrounded noetic re-read",
    "still live",
    "next licensed live burden",
    "burden landed",
    # positive default-mode worked-example anchors
    "Default-Mode Worked Example",
    "composition / dependence pressure",
    "TTP/operator trace",
    "source-status discipline",
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
    "Released: <item>",
    # positive submove-boundary worked-example anchors
    "Boundary Discipline",
    "imported compassion/autonomy tribunal",
    "¹B₁ [FPD]",
    "burden-complete",
    "no headline-only answer",
    "release the next burden-cycle",
]

# Tokens that must NOT appear in the generated runtime.
FORBIDDEN_TOKENS = [
    "legacy recursive-audit prompt required",
    "giant load ledger required",
    "omnibus names as matched_modules",
    "behavioral parity guaranteed",
    "full audit render is the default",
    # Stale expanded-diagnostic mapping: plain /daee-epistemics must NOT map to lab-report
    "plain /daee-epistemics = level 2",
    "plain /daee-epistemics = lab-report",
    "plain /daee-epistemics = full diagnostic ir",
    # Stale unscoped render-pressure language: these phrases made internal
    # governance feel like mandatory default visible output.
    "This is not an optional output",
    "| Pass | File | Emit |",
    "Surfaced `[Case State]`, `[Source Basis]`, and other governance blocks must be rendered from the validated IR",
    "This file governs how the skill surfaces its read of a case",
    "The case-state is the surfaced contract derived from the validated Diagnostic IR",
    "The `[Case State]` block is the surfaced form of the validated Diagnostic IR",
    "Use this block when diagnosis matters to the response",
    "In ordinary mode, surfaced output may omit inactive or routine fields",
    "The response should expose routing state, read strength, or module selection concisely",
    "compact governance sentence (e.g., \"Recursion decision: RECURSE",
    "may appear as a compact governance line at the close",
    "compact final-governance sentence naming the recursion decision is permitted",
    "at most three major operative submoves",
    "fourth-submove release is blocked",
    "must still name the recursion decision and next eligible pass",
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
    "no named-example route",
    "no default raw IR/Case State/route ledger",
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
    "Let me check",
    "I will produce governed prose",
    "The public identity-frame may stabilize the criterion or affect discourse orientation",
    "Identity is a modal/stabilizing node",
    "Moving from the current live burden to downstream doctrine requires state re-read prose",
    "hidden premises listed without operator result",
    # rc12: transition spine behavior shape
    "minimum visible transition spine",
    "no further same-input eligible burden remains",
    # input-anchored recursion discipline
    "component-tour cosplay",
    "input-anchored",
    # compact Layer A / Layer B / state re-read pass shape
    "single-pass layer a/b cosplay",
    "governing burden",
    "remaining input-anchored burdens",
    "compact state re-read",
    "route-chain collapse",
    "route-chain recursion cosplay",
    "shallow live-burden execution",
    "diagnostic-reduction bypass",
    "one live noetic burden/function selected",
    "operative submoves are not burden-cycles",
    "hiddenness/punishment/source-status can be operative submoves under one burden",
    "multi-burden does not mean multi-recursion by default",
    "runtime-verifiable diagnostic compiler",
    "TTP entry criteria",
    "TTP exit criteria",
    "Depth And Stop Guards",
    "Layer A / Layer B release checks",
    "deterministic argument bank",
    "Layer A/B smuggling",
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
    "Rule S-9",
    "Rule P-8",
]

DEFAULT_ALLOWED_FORMAL_STATE_MARKERS = [
    "∇ route-gradient",
    "ΔⁿB",
    "Δκ",
    "∇·",
    "∇×",
    "del-dot",
    "del-cross",
    "LoopBreak(∇×T)",
    "R(H,Δ)",
    "R(H,Delta)",
    "𝒞(Ψᴺ)",
    "T_lang",
    "PARTIAL",
    "RECURSE",
    "COMPLETE",
]

DEFAULT_REQUIRED_FORMAL_STATE_MARKER_TOKENS = [
    "burden-cycle",
    "operative submove",
    "∇ route-gradient",
    "Δκ",
    "∇·",
    "∇×",
    "LoopBreak(∇×T)",
    "R(H,Δ)",
    "𝒞(Ψᴺ)",
    "Ψᴵ",
    "PARTIAL",
    "RECURSE",
    "COMPLETE",
    "control-relevant",
]

DEFAULT_FIELD_DIAGNOSTIC_MARKERS = [
    "∇·",
    "∇×",
    "del-dot",
    "del-cross",
]

DEFAULT_FORMAL_MARKER_CONTROL_TERMS = [
    "state",
    "κ",
    "kappa",
    "r(h,δ)",
    "r(h,delta)",
    "δκ",
    "delta-kappa",
    "dependency",
    "pressure",
    "loop",
    "partial",
    "recurse",
    "complete",
    "closure",
    "held",
    "live",
    "checker",
    "control",
    "land(b)",
    "burden",
    "field target",
    "target-explicit",
    "register",
    "route",
    "relational field",
    "scalar",
    "governance",
    "route-gradient",
    "loopbreak",
    "loop-breaking",
    "closure-field",
    "coupling",
    "t_lang",
    "psii",
    "ψᴵ",
]

DEFAULT_FORBIDDEN_FORMALISM_EXPOSITION = [
    "nabla dot",
    "nabla cross",
    "antisymmetric jacobian",
    "exterior derivative",
]

DEFAULT_RUNTIME_FORMALISM_CLAIM_FORBIDDEN = [
    "Shannon entropy measures truth",
    "meaning entropy",
    "warrant entropy",
    "lower entropy proves",
    "entropy proves",
    "entropy measures warrant",
    "entropy measures meaning",
    "divergence measures truth",
    "divergence measures warrant",
    "curl measures truth",
    "curl measures warrant",
    "nabla measures truth",
    "nabla measures warrant",
    "nabla replaces delta",
    "divergence replaces delta",
    "curl replaces delta",
    "∇ replaces Δ",
    "∇ bypasses gates",
    "∇ bypasses catalogue",
    "route-gradient bypasses gates",
    "LoopBreak is arbitrary assertion",
    "𝒞(Ψᴺ) guarantees conversion",
    "Ψᴵ gives access to the soul",
    "agent controls guidance",
    "∇x symbol proves",
    "∇× symbol proves",
    "∇ applies to scalar",
    "∇· applies to scalar",
    "∇× applies to scalar",
]

DEFAULT_RUNTIME_NLA_FORBIDDEN = [
    "NLA",
    "Natural Language Autoencoder",
    "activation verbalizer",
    "activation reconstructor",
    "reconstruction loss",
    "FVE",
    "residual stream",
]

DEFAULT_RUNTIME_CONTEXTUAL_FORMALISM = [
    "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
    "IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)",
]

DEFAULT_RUNTIME_CONTEXT_REQUIRED = [
    "do not print",
    "not default",
    "audit/formalism",
    "forbidden default",
    "forbidden example",
    "formal/spec notation",
    "expanded formalism render boundary",
    "anti-symbol-theater",
    "long formalism exposition",
    "ascii alias",
    "ascii aliases",
    "not separate operators",
    "post-delta",
]

FORMAL_MARKER_POSITIVE_SAMPLES = {
    "closure_kappa_target": "State: Δκ live; ∇·κ positive; ∇×κ unresolved; R(H,Δ): RECURSE.",
    "burden_target": (
        "Burden field: ΔⁿB landed; ∇·B positive over B3/B4; "
        "∇×B unresolved around compact-neutrality dependency."
    ),
    "register_target": "Register field: ∇·♥ positive; ∇×ξ unresolved; R(H,Δ): HOLD.",
    "alias_target": "ASCII fallback: del-dot(kappa) positive; del-cross(xi) unresolved; R(H,Delta): RECURSE.",
    "route_gradient": "Route: ∇ pressure selects B2 after gates; Δ waits for burden landing.",
    "loop_break": "State: ∇×B nonzero; LoopBreak(∇×B) licensed; ΔⁿB lands; R(H,Δ): RECURSE.",
    "closure_field": "State: 𝒞(Ψᴺ) reached; ∇·κ negative; ∇×κ resolved; R(H,Δ): STOP.",
}

FORMAL_MARKER_BAD_SAMPLES = {
    "untargeted_marker": ("State: ∇× unresolved; COMPLETE.", "without explicit target"),
    "untargeted_alias": ("State: del-cross unresolved; COMPLETE.", "without explicit target"),
    "proof_by_symbol": ("The ∇× symbol proves the TTP executed.", "forbidden formalism claim"),
    "delta_replacement": ("Curl replaces Delta here; ∇ replaces Δ as the transition operator.", "forbidden formalism claim"),
    "gradient_bypass": ("Route-gradient bypasses gates and chooses any route.", "forbidden formalism claim"),
    "loopbreak_assertion": ("LoopBreak is arbitrary assertion over the field.", "forbidden formalism claim"),
    "closure_conversion": ("𝒞(Ψᴺ) guarantees conversion of the interlocutor.", "forbidden formalism claim"),
    "scalar_target": ("∇· applies to scalar master diagnosis; COMPLETE.", "forbidden formalism claim"),
    "long_exposition": ("The antisymmetric Jacobian of the noetic field shows a loop.", "formalism exposition"),
}

FIXTURE_FORBIDDEN_TOKENS = [
    "FPD/M1 landed",
    "the imported criterion has failed",
    "Recursion decision: RECURSE",
]

# Tokens that must appear in the dispatch-gate bundle specifically,
# confirming the IR render-mode policy was compiled in.
DISPATCH_GATE_REQUIRED = [
    "render-mode policy",
    "internal state object",
    "must not appear in the public response",
    "Default Final-Output Preflight Gate",
    "invalid and must be rewritten before output",
    "checks pipeline validity",
    "clean prose without pipeline validity",
    "discipline is universal",
    "printout is mode-specific",
    "full recursion in every mode",
    "compact Layer A",
    "compact DSL/IR header",
    "- read status:",
    "- confidence:",
    "- claim_level:",
    "- pattern_profile:",
    "- reason-category:",
    "- concealment:",
    "- deformation:",
    "- DO-orient:",
    "- live noetic burden:",
    "- current bounded operator:",
    "- held:",
    "- source-status/noetic-frame:",
    "- gate/release decision:",
    "bounded governed response",
    "Hidden Premises",
    "Bounded Response / operative submoves",
    "TTP/operator trace",
    "Restorative Response",
    "Core Formulation",
    "Closing Formulation",
    "State/noetic re-read",
    "Move 1 / Move 2 / Move 3",
    "Step 1",
    "silent closure while an eligible",
    "bibliography",
    "Let me construct the diagnostic IR",
    "Next: FPD",
    "Concealment:",
    "TTP activation",
    # rc12: transition spine in dispatch gate
    "minimum visible transition spine",
    "If no transition marker appears",
    # input-anchored recursion discipline
    "input-anchored",
    "component-tour cosplay",
    "topic transition",
    # compact Layer A / Layer B / state re-read pass shape
    "single-pass layer a/b cosplay",
    "remaining input-anchored burdens",
    "route-chain collapse",
    "one live noetic burden/function selected",
    "operative submoves are not burden-cycles",
    "hiddenness/punishment/source-status can be operative submoves under one burden",
    "runtime-verifiable diagnostic compiler",
    "TTP entry criteria",
    "TTP exit criteria",
    "Depth And Stop Guards",
    "Layer A / Layer B release checks",
    # source-status and noetic-frame non-equivalence in dispatch gate
    "Source-Status & Noetic-Frame Non-Equivalence Discipline",
    "operative noetic frame",
    "Rule S-9",
    "Rule P-8",
    "Grounded Noetic Re-Read Shape",
    "Field-grounding rules",
]


RENDER_SHAPE_BAD_OUTPUTS = {
    "literal_governance_label": (
        """### Layer A - Compact DSL/IR header
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
- The imported criterion is treated as judge.
#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector returns criterion to warrant.
##### Bounded Response / operative submoves
Target: imported criterion.
Operation: test whether it has authority.
Result: the criterion no longer governs.
##### TTP/operator trace
- tribunal-detection: Target: criterion. Operation: test its authority. Result: narrowed.
### State/noetic re-read
- What changed: the imported criterion no longer governs.
- Remaining input-anchored burdens: none
- Governance: STOP
### Restorative Response
The criterion returns to warrant.
### Closing Formulation
The case is closed.
""",
        "literal governance label in default output",
    ),
    "missing_core_formulation": (
        """### Layer A - Compact DSL/IR header
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
- held: full punishment doctrine
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### 1. Restorative Response
The tribunal is tested and loosened.
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
        """### Layer A - Compact DSL/IR header
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
- held: full punishment doctrine
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### 1. Restorative Response
The tribunal is tested and loosened.
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
    "source_function_first_appears_in_restoration": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: hard source-request
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: imported tribunal
- current bounded operator: imported tribunal test
- held: source architecture
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### Hidden Premises
- The objection imports a moral criterion.

#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector is to test the tribunal before downstream source work is released.

##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: imported tribunal. Operation: test whether the criterion has justified authority. Result: the tribunal cannot remain unexamined.

##### TTP/operator trace
Trace: tribunal-detection + FPD + M1.

### State/noetic re-read
- What changed: the imported criterion no longer governs.
- Remaining input-anchored burdens: none
- Held routes rechecked: none
- Release status: closed; no same-input eligible burden remains

### Restorative Response
The Qur'an 17:15 proves no punishment without a messenger; Qur'an 2:286 proves mercy and accountability; guidance, hujjah, and worship-worthiness are therefore restored.

### Closing Formulation
The answer is complete.
""",
        "source function first appears in final restoration",
    ),
    "meta_narration_opening": (
        """Now I will build the governed answer.

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
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### 1. Restorative Response
The tribunal is tested.
#### 2. Core Formulation
1. The criterion is imported.
#### 3. Closing Formulation
The frame lands.

### State/noetic re-read
- Cleared: imported tribunal
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "meta narration opening",
    ),
    "scaffold_language_in_default_output": (
        """### Layer A - Compact DSL/IR header
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
- source-status/noetic-frame: operative frame selected
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
Result: owner floor is applied and the operation is bounded to the target named above.

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
        """### Layer A - Compact DSL/IR header
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
    "excessive_submoves": (
        """### Layer A - Compact DSL/IR header
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
- source-status/noetic-frame: operative frame selected
- gate/release decision: over-release

### Layer B - bounded governed response
#### 1. Restorative Response
Operative submove target: tribunal.
Operative submove target: hiddenness.
Operative submove target: punishment.
Operative submove target: transmission.
#### 2. Core Formulation
1. Too much is released.
#### 3. Closing Formulation
The answer dumps arguments.

### State/noetic re-read
- Cleared: unclear
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "more-than-three submoves without cohesion gate",
    ),
    "missing_ttp_trace": (
        """### Layer A - Compact DSL/IR header
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
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### 1. Restorative Response
The tribunal is tested.
#### 2. Core Formulation
1. The criterion is imported.
#### 3. Closing Formulation
The frame lands.

### State/noetic re-read
- Cleared: imported tribunal
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
""",
        "missing TTP/operator trace",
    ),
    "unnamed_reductio_operation": (
        """### Layer A - Compact DSL/IR header
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
- source-status/noetic-frame: operative frame selected
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
        """### Layer A - Compact DSL/IR header
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
- source-status/noetic-frame: operative frame selected
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
    "default_source_parade": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: source-prestige support
- DO-orient: mixed
- live noetic burden: public source support
- current bounded operator: source-status check
- held: downstream doctrine
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### Hidden Premises
- The answer treats school context as public support.
#### Burden / Operation 1
##### Core Formulation
The deformation is source-prestige support; the restoration vector is source-status repair.
##### Bounded Response / operative submoves
Operator: source-status check.
Target: public support. Operation: cite named authorities, a named school, and external theorists as context that supports the answer. Result: the public frame relies on source prestige.
##### TTP/operator trace
Trace: source-status check.
### State/noetic re-read
- Cleared: claimed source context
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The source context is treated as support.
### Closing Formulation
The answer closes by association.
""",
        "default source/citation parade",
    ),
    "method_source_branding": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: method branding
- DO-orient: mixed
- live noetic burden: method identity
- current bounded operator: source-status check
- held: none
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### Hidden Premises
- Authority is borrowed through a named school.
#### Burden / Operation 1
##### Core Formulation
The deformation is method branding; the restoration vector is to reject authority-by-association.
##### Bounded Response / operative submoves
Operator: source-status check.
Target: method identity. Operation: describe daee-epistemics as an Ashari noetics founded under a named scholar. Result: method authority is branded by association.
##### TTP/operator trace
Trace: source-status check.
### State/noetic re-read
- Cleared: claimed brand identity
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The method is presented as a branded school.
### Closing Formulation
The answer closes by source-branding.
""",
        "method-source branding",
    ),
    "comparative_neutral_flattening": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: PF-comparative
- reason-category: 3
- concealment: clear
- deformation: abstract universalism
- DO-orient: mixed
- live noetic burden: comparative pattern
- current bounded operator: pattern-first routing
- held: revelation-order repair
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### Hidden Premises
- All traditions are treated as interchangeable cases of one neutral comparative system.
#### Burden / Operation 1
##### Core Formulation
The deformation is comparative-neutral flattening; the restoration vector is pattern-first routing.
##### Bounded Response / operative submoves
Operator: pattern-first routing.
Target: tradition difference. Operation: treat all religions as the same abstract noetic pattern. Result: source, function, warrant, and authority-order differences disappear.
##### TTP/operator trace
Trace: pattern-first routing.
### State/noetic re-read
- Cleared: tradition difference
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
All systems are treated as interchangeable.
### Closing Formulation
The answer closes as neutral comparison.
""",
        "comparative-neutral flattening",
    ),
    "revealed_text_without_source": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: textual
- pattern_profile: none
- reason-category: 2
- concealment: clear
- deformation: unsupported textual citation
- DO-orient: truth-seek
- live noetic burden: textual support
- current bounded operator: source-status check
- held: none
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### Hidden Premises
- Textual support is invoked without a direct source.
#### Burden / Operation 1
##### Core Formulation
The deformation is unsupported textual citation; the restoration vector is direct source discipline.
##### Bounded Response / operative submoves
Operator: source-status check.
Target: textual support. Operation: invoke the Qurʾān and Sunnah as direct support without any external reference. Result: source discipline is missing.
##### TTP/operator trace
Trace: source-status check.
### State/noetic re-read
- Cleared: textual support
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The answer relies on an unreferenced textual support.
### Closing Formulation
The answer closes without direct source.
""",
        "revealed source without direct reference",
    ),
    "denomination_first_routing": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: first-order
- pattern_profile: none
- reason-category: 2
- concealment: clear
- deformation: untyped
- DO-orient: truth-seek
- live noetic burden: Christian objection
- current bounded operator: standard Christian rebuttal
- held: none
- source-status/noetic-frame: denomination treated as route
- gate/release decision: release denomination-specific content

### Layer B - bounded governed response
#### Hidden Premises
- Because this is a Christian objection, the standard apologetic bank should be used.
#### Burden / Operation 1
##### Core Formulation
The objection is Christian, so use the standard response.
##### Bounded Response / operative submoves
Operator: denomination lookup.
Target: Christian label. Operation: paste the standard apologetic bank for that denomination. Result: content is routed from label rather than diagnosed pattern.
##### TTP/operator trace
Trace: denomination lookup.
### State/noetic re-read
- Cleared: topic label
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The label is treated as restored order.
### Closing Formulation
The answer closes from denomination.
""",
        "denomination-first routing",
    ),
    "topic_argument_bank": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: first-order
- pattern_profile: none
- reason-category: 2
- concealment: clear
- deformation: untyped
- DO-orient: truth-seek
- live noetic burden: hiddenness topic
- current bounded operator: hiddenness answer bank
- held: none
- source-status/noetic-frame: operative frame selected
- gate/release decision: release topic bank

### Layer B - bounded governed response
#### Hidden Premises
- The topic was detected.
#### Burden / Operation 1
##### Core Formulation
This is a hiddenness question, so list the standard arguments.
##### Bounded Response / operative submoves
Operator: topic bank.
Target: hiddenness topic. Operation: paste the known rebuttal and standard proof sequence. Result: the answer bypasses diagnostic IR.
##### TTP/operator trace
Trace: topic bank.
### State/noetic re-read
- Cleared: topic
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The topic receives stock content.
### Closing Formulation
The answer closes from a bank.
""",
        "topic-to-argument-bank",
    ),
    "summary_only_core": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: criterion import
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
The objection assumes a criterion and needs an answer.
##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: criterion. Operation: test whether it has authority. Result: the criterion cannot govern.
##### TTP/operator trace
Trace: tribunal-detection.
### State/noetic re-read
- Cleared: criterion
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The proper warrant order is restored; the criterion is returned to its proper place; the imported deformation is relieved; downstream doctrine remains held.
### Closing Formulation
The answer closes from the landed operation.
""",
        "Core Formulation lacks deformation + modality + restoration vector",
    ),
    "repeated_closing_formulation": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: criterion import
- DO-orient: truth-seek
- live noetic burden: criterion
- current bounded operator: tribunal-detection
- held: none
- source-status/noetic-frame: operative frame selected
- gate/release decision: release two operations

### Layer B - bounded governed response
#### Hidden Premises
- A criterion is imported.
#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector is to test the tribunal.
##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: criterion. Operation: test whether it has authority. Result: the criterion cannot govern.
##### Closing Formulation
This burden closes rhetorically.
#### Burden / Operation 2
##### Core Formulation
The deformation is authority disorder; the noetic pattern is warrant inversion; the restoration vector is to return warrant order.
##### Bounded Response / operative submoves
Operator: authority-order repair.
Target: warrant order. Operation: restore order. Result: warrant is returned.
##### TTP/operator trace
Trace: tribunal-detection + authority-order repair.
### State/noetic re-read
- Cleared: criterion and warrant order
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The proper warrant order is restored; the imported criterion is returned to its proper place; the deformation is relieved; nothing remains held.
### Closing Formulation
The answer closes once at the end.
""",
        "multiple Closing Formulations",
    ),
    "decorative_ttp_name": (
        """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: none
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: truth-seek
- live noetic burden: tribunal test
- current bounded operator: reductio / tribunal-detection
- held: downstream doctrine
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### Hidden Premises
- A criterion is imported.
#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the restoration vector is to test it.
##### Bounded Response / operative submoves
This is a reductio. The objection is wrong.
##### TTP/operator trace
Trace: reductio.
### State/noetic re-read
- Cleared: unclear
- Remaining input-anchored burdens: none
- Release status: closed; no same-input eligible burden remains
### Restorative Response
The criterion no longer governs.
### Closing Formulation
The bounded takeaway is unclear.
""",
        "TTP named without bounded operation",
    ),
    "audit_proof_in_default": (
        """### Layer A - Compact DSL/IR header
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

Smoke runtime note: SKILL.md loaded before output; proof of loaded files is below.

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
- What changed: the criterion no longer governs.
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
    "rubric_schematic_landing": (
        """### Layer A - Compact DSL/IR header
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
Target: criterion. Operation: address the criterion. Result: this burden lands.
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
        """### Layer A - Compact DSL/IR header
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
    "weak_state_reread_no_delta": (
        """### Layer A - Compact DSL/IR header
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
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector is to test the criterion.
##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: criterion. Operation: test whether it has authority. Result: the criterion cannot govern.
##### TTP/operator trace
Trace: tribunal-detection.
### State/noetic re-read
- Cleared: criterion
- Remaining input-anchored burdens: downstream doctrine
- Release status: next bounded pass licensed because another input-anchored burden remains
### Restorative Response
The criterion is returned to its proper place.
### Closing Formulation
The answer closes from the landed operation.
""",
        "weak state/noetic re-read",
    ),
    "shallow_v12_execution": (
        """### Layer A - Compact DSL/IR header
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
        """### Layer A - Compact DSL/IR header
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
        """### Layer A - Compact DSL/IR header
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

RENDER_SHAPE_POSITIVE_OUTPUTS = {
    "governed_default_shape": """### Layer A - Compact DSL/IR header
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
- source-status/noetic-frame: operative frame selected
- gate/release decision: release one bounded operator

### Layer B - bounded governed response
#### Hidden Premises
- The objection imports a moral criterion as tribunal.

#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement; the restoration vector is to test the tribunal before downstream doctrine is released.

##### Bounded Response / operative submoves
Operator: tribunal-detection.
Target: imported tribunal. Operation: test whether the criterion has justified authority over revelation. Result: the tribunal cannot remain unexamined.

##### TTP/operator trace
Trace: tribunal-detection + FPD + M1 + diagnostic-render-contract.

### State/noetic re-read
- What changed: the imported criterion no longer governs as the judge of the answer.
- Cleared: imported tribunal
- Remaining input-anchored burdens: none
- Held routes rechecked: downstream doctrine remains held
- Release status: closed; no same-input eligible burden remains

### Restorative Response
The restored order is that the tribunal must be judged before it judges.

### Closing Formulation
What cleared is the imported criterion's authority; what remains held is downstream doctrine; the governed takeaway is bounded restoration rather than argument dump.
""",
    "governed_more_than_three_submoves": """### Layer A - Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-epistemic
- pattern_profile: compound moral protest
- reason-category: 3
- concealment: clear
- deformation: imported criterion
- DO-orient: mixed
- live noetic burden: imported tribunal
- current bounded operator: imported tribunal test
- held: broad doctrine; interior motive certification
- source-status/noetic-frame: operative criterion frame selected
- gate/release decision: release one burden with distinct subordinate submoves

### Layer B - bounded governed response
#### Hidden Premises
- The objection imports a moral criterion as tribunal.

#### Burden / Operation 1
##### Core Formulation
The deformation is criterion import; the noetic pattern is tribunal displacement through several active supports; the restoration vector is to keep each support distinct while landing the governing imported-criterion burden.

##### Bounded Response / operative submoves
Operator: tribunal-detection.
Operative submove target: tribunal. Operation: test whether the criterion has justified authority over revelation. Result: the tribunal cannot remain unexamined.
Operative submove target: hiddenness. Operation: test whether guidance is being redefined as coercive proof. Result: hiddenness cannot by itself judge worship-worthiness.
Operative submove target: accountability. Operation: test whether accountability is being treated as cruelty before justice is defined. Result: the objection has not established its standard.
Operative submove target: source-worldview. Operation: test whether the public worldview supplies a binding moral criterion. Result: the source-worldview consequence trace remains live for the state re-read.
Submove saturation cohesion audit: the fourth submove shares the same target-family, source/noetic frame, claim cluster, and restoration vector, so it remains distinct inside this burden instead of being consolidated or falsely capped.

##### TTP/operator trace
Trace: tribunal-detection + FPD + M1 + M8 + diagnostic-render-contract.

### State/noetic re-read
- What changed: the imported criterion no longer governs as the judge of the answer.
- Cleared: imported tribunal as governing burden
- Remaining input-anchored burdens: source-worldview consequence trace remains live if not landed in this pass.
- Held routes rechecked: downstream doctrine and interior motive certification remain held.
- Release status: continue or mark partial if the remaining burden cannot be landed.

### Restorative Response
The restored order is that the tribunal must be judged before it judges, and every active support must be named without turning into an argument dump.

### Closing Formulation
The governed result is not a three-submove cap; it is enough distinct operation for the live burden to land.
""",
}

META_NARRATION_OPENING_RE = re.compile(
    r"(?is)^\s*(?:now i|i now|let me|i will now|i'll now)\b"
)
RESTORATIVE_RE = re.compile(r"(?im)^\s*#{3,5}\s*(?:1\.\s*)?Restorative Response\b")
HIDDEN_PREMISES_RE = re.compile(r"(?im)^\s*#{3,5}\s*Hidden Premises\b")
CORE_RE = re.compile(r"(?im)^\s*#{3,6}\s*(?:\d+\.\s*)?Core Formulation\b")
CLOSING_RE = re.compile(r"(?im)^\s*#{3,5}\s*(?:\d+\.\s*)?Closing Formulation\b")
STATE_RE = re.compile(r"(?im)^\s*#{3,5}\s*State/noetic re-read\b")
LAYER_A_RE = re.compile(r"(?im)^\s*#{3,5}\s*Layer A\s*(?:\u2014|-)\s*Compact DSL/IR header\b")
LAYER_B_RE = re.compile(r"(?im)^\s*#{3,5}\s*Layer B\s*(?:\u2014|-)\s*bounded governed response\b")
NON_TRIVIAL_OPERATOR_RE = re.compile(
    r"(?im)^\s*-?\s*current bounded operator\s*:\s*.*"
    r"(?:criterion|tribunal|composition|predication|source-status|warrant|worship-worthiness)"
)
TRACE_RE = re.compile(
    r"(?im)^\s*(?:#{3,6}\s*)?(?:TTP/operator trace|TTP/module trace|Owner trace|Trace)\b"
)
MAJOR_SUBMOVE_RE = re.compile(
    r"(?im)^\s*(?:Operative submove target:|(?:Move|Step)\s+\d+\s*:|#{3,6}\s*(?:Move|Submove)\s+\d+\b)"
)
SUBMOVE_COHESION_GATE_RE = re.compile(
    r"(?i)\b(?:submove saturation(?: cohesion audit| gate)?|cohesion audit|"
    r"cohesion gate|more-than-three)\b"
)
NAMED_OPERATOR_RE = re.compile(
    r"(?i)\b(?:reductio|tamanu|tamÃƒâ€žÃ‚ÂnuÃƒÅ Ã‚Â¿|criterion-reversal|tribunal-detection|"
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
DENOMINATION_FIRST_RE = re.compile(
    r"(?i)\b(?:because|since|as)\s+(?:this is|they are|the interlocutor is|it is)\s+"
    r"(?:an?\s+)?(?:ash'?ari|maturidi|christian|naturalist|muslim|hindu|buddhist|"
    r"sufi|kalamic|denomination|school)\b.{0,180}\b(?:standard|argument bank|"
    r"apologetic|rebuttal|proof sequence)\b"
)
TOPIC_ARGUMENT_BANK_RE = re.compile(
    r"(?i)\b(?:topic|objection|source|denomination|label)\b.{0,100}"
    r"\b(?:argument bank|standard proof sequence|known rebuttal|apologetic bank|"
    r"standard arguments|stock content|pasted arguments)\b"
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
FINAL_SOURCE_FUNCTION_RE = re.compile(
    r"(?i)\b(?:mercy|guidance|hujjah|accountability|worship-worthiness|"
    r"worthy of worship|testimony|tawatur|transmission|predication|predicate|"
    r"source architecture|qur'?an\s+\d+:\d+|hadith|sunnah)\b"
)
CORE_BLOCK_RE = re.compile(
    r"(?ims)^\s*#{3,6}\s*(?:\d+\.\s*)?Core Formulation\b(?P<body>.*?)"
    r"(?=^\s*#{3,6}\s*(?:Bounded Response|TTP/operator trace|State/noetic re-read|"
    r"Restorative Response|Closing Formulation|Burden / Operation|\d+\.|Hidden Premises)\b|\Z)"
)
CORE_DEFORMATION_RE = re.compile(r"(?i)\b(?:deformation|concealment|deviation|deformed|concealed|deviated|unsound)\b")
CORE_MODALITY_RE = re.compile(r"(?i)\b(?:modality|pattern|noetic pattern|modal|operates|functions|tribunal|authority displacement|warrant inversion)\b")
CORE_RESTORATION_RE = re.compile(r"(?i)\b(?:restoration vector|restore|restored|returned|return|sound order|proper order)\b")
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
    r"restored order is restored|address the criterion|predication is mentioned)\b"
)
STATE_BLOCK_RE = re.compile(
    r"(?ims)^\s*#{3,5}\s*State/noetic re-read\b(?P<body>.*?)"
    r"(?=^\s*#{3,5}\s*(?:Restorative Response|Closing Formulation|Burden / Operation|Layer B)\b|\Z)"
)
STATE_DELTA_RE = re.compile(
    r"(?i)\b(?:what changed|cumulative-state delta|state-change|state delta|"
    r"narrowed|no longer governs|now exposed|now licensed|now blocked|"
    r"returned as not-yet-target)\b"
)
LITERAL_DEFAULT_GOVERNANCE_RE = re.compile(
    r"(?im)^\s*-?\s*(?:Governance|Release status|Closure|recursion decision)\s*:\s*"
    r"(?:STOP|HOLD|RECURSE|PARTIAL)\b"
)
V12_OPERATOR_RE = re.compile(r"(?i)\b(?:V12|tamanu|tamÃƒÆ’Ã¢â‚¬Å¾Ãƒâ€šÃ‚ÂnuÃƒÆ’Ã…Â Ãƒâ€šÃ‚Â¿|multiple independent lords?)\b")
V12_PREMATURE_TRINITY_RE = re.compile(
    r"(?is)\b(?:Trinity|Trinitarian)\b(?:(?!independent lordship|worship-status plurality).){0,1200}"
    r"\b(?:V12|tamanu|tamÃƒÆ’Ã¢â‚¬Å¾Ãƒâ€šÃ‚ÂnuÃƒÆ’Ã…Â Ãƒâ€šÃ‚Â¿)\b"
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


def first_pos(pattern: re.Pattern[str], text: str) -> int:
    match = pattern.search(text)
    return match.start() if match else -1


def final_source_function_first_appears(text: str) -> bool:
    restorative = RESTORATIVE_RE.search(text)
    if restorative is None:
        return False
    prior = text[: restorative.start()]
    final = text[restorative.start() :]
    direct_source_first = bool(DIRECT_SOURCE_RE.search(final)) and not bool(DIRECT_SOURCE_RE.search(prior))
    function_first = bool(FINAL_SOURCE_FUNCTION_RE.search(final)) and not bool(FINAL_SOURCE_FUNCTION_RE.search(prior))
    return direct_source_first or function_first


def render_shape_violations(text: str) -> list[str]:
    violations: list[str] = []
    lower = text.lower()
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
    if not LAYER_A_RE.search(text):
        violations.append("missing DSL/IR header")
    if LAYER_A_RE.search(text) and not LAYER_B_RE.search(text):
        violations.append("missing bounded governed Layer B")
    if LAYER_B_RE.search(text) and not HIDDEN_PREMISES_RE.search(text):
        violations.append("missing Hidden Premises")
    if not RESTORATIVE_RE.search(text):
        violations.append("missing Restorative Response")
    if not CORE_RE.search(text):
        violations.append("missing Core Formulation")
    if not CLOSING_RE.search(text):
        violations.append("missing Closing Formulation")
    if not STATE_RE.search(text):
        violations.append("missing state/noetic re-read")
    if "layer a" not in lower and "restorative response" not in lower and len(text) > 80:
        violations.append("essay-only output")
    if len(MAJOR_SUBMOVE_RE.findall(text)) > 3 and not SUBMOVE_COHESION_GATE_RE.search(text):
        violations.append("more-than-three submoves without cohesion gate")
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
    if DENOMINATION_FIRST_RE.search(layer_b_text):
        violations.append("denomination-first routing")
    if TOPIC_ARGUMENT_BANK_RE.search(layer_b_text):
        violations.append("topic-to-argument-bank")
    if DEFAULT_SOURCE_PARADE_RE.search(layer_b_text):
        violations.append("default source/citation parade")
    if METHOD_SOURCE_BRANDING_RE.search(layer_b_text):
        violations.append("method-source branding")
    if COMPARATIVE_NEUTRAL_RE.search(layer_b_text):
        violations.append("comparative-neutral flattening")
    if REVEALED_TEXT_RE.search(layer_b_text) and not DIRECT_SOURCE_RE.search(layer_b_text):
        violations.append("revealed source without direct reference")
    if final_source_function_first_appears(text):
        violations.append("source function first appears in final restoration")
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
    for core in CORE_BLOCK_RE.finditer(text):
        body = core.group("body")
        if not (
            CORE_DEFORMATION_RE.search(body)
            and CORE_MODALITY_RE.search(body)
            and CORE_RESTORATION_RE.search(body)
        ):
            violations.append("Core Formulation lacks deformation + modality + restoration vector")
            break

    state_pos = first_pos(STATE_RE, text)
    restorative_positions = [match.start() for match in RESTORATIVE_RE.finditer(text)]
    closing_positions = [match.start() for match in CLOSING_RE.finditer(text)]
    if len(restorative_positions) > 1:
        violations.append("multiple Restorative Responses")
    if len(closing_positions) > 1:
        violations.append("multiple Closing Formulations")
    if state_pos != -1 and restorative_positions and restorative_positions[0] < state_pos:
        violations.append("Restorative Response before state/noetic re-read")
    if state_pos != -1 and closing_positions and closing_positions[0] < state_pos:
        violations.append("Closing Formulation before state/noetic re-read")
    if restorative_positions and closing_positions and closing_positions[0] < restorative_positions[0]:
        violations.append("Closing Formulation before Restorative Response")
    return violations


def check_render_shape_samples(errors: list[str]) -> None:
    for name, (sample, expected_violation) in RENDER_SHAPE_BAD_OUTPUTS.items():
        violations = render_shape_violations(sample)
        if expected_violation not in violations:
            errors.append(
                "render-shape bad sample was not rejected: "
                f"{name} expected {expected_violation!r}, got {violations!r}"
            )
    for name, sample in RENDER_SHAPE_POSITIVE_OUTPUTS.items():
        violations = render_shape_violations(sample)
        if violations:
            errors.append(
                "render-shape positive sample was rejected: "
                f"{name} got {violations!r}"
            )


def read_runtime(root: Path, errors: list) -> str:
    runtime_root = out_dir(root)
    if not runtime_root.is_dir():
        errors.append("skill runtime root is absent")
        return ""
    parts = []
    for rel_path in RUNTIME_FILES:
        path = runtime_root / rel_path
        if not path.is_file():
            errors.append(f"missing runtime render-mode surface: skill/{rel_path}")
            continue
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def read_dispatch_gate(root: Path, errors: list) -> str:
    path = out_dir(root) / "references/runtime-dispatch-gate.md"
    if not path.is_file():
        errors.append("dispatch-gate bundle missing for render-mode policy check")
        return ""
    return path.read_text(encoding="utf-8")


def check_current_doc_staleness(root: Path, errors: list) -> None:
    for rel_path in CURRENT_GOVERNANCE_DOCS:
        path = root / rel_path
        if not path.is_file():
            errors.append(f"missing current governance doc for staleness check: {rel_path}")
            continue
        lower_text = path.read_text(encoding="utf-8").lower()
        for token in STALE_CURRENT_DOC_TOKENS:
            if token.lower() in lower_text:
                errors.append(
                    f"stale render-governance terminology in {rel_path}: {token!r}"
                )


def _has_any_context(text: str, contexts: list[str]) -> bool:
    lower = text.lower()
    return any(context.lower() in lower for context in contexts)


TARGET_EXPLICIT_FIELD_DIAGNOSTIC_RE = re.compile(
    r"(?:"
    r"(?:∇[·×]|del-(?:dot|cross)\s*\(?)(?:κ|kappa|B|burden|H|heart|♥|xi|ξ|Omega|Ω|sigma|σ|mu|μ|N|T|route|register)"
    r"|∇·`?\s+(?:pressure|diagnostic|field)"
    r"|∇×`?\s+(?:loops?|diagnostic|field)"
    r")",
    re.I,
)


def check_default_formal_marker_policy(corpus: str, errors: list[str], label: str = "default runtime surface") -> None:
    """Allow compact control-bound state markers; reject exposition-as-governance."""
    lines = corpus.splitlines()
    for index, line in enumerate(lines):
        window = "\n".join(lines[max(0, index - 2) : min(len(lines), index + 3)])
        boundary_context = _has_any_context(window, DEFAULT_RUNTIME_CONTEXT_REQUIRED) or _has_any_context(
            window,
            [
                "target-explicit",
                "explicit field target",
                "explicit target field",
                "operator distinction",
                "not restricted",
                "not replacements",
                "read the `δ`-produced field state",
                "read the `Δ`-produced field state",
                "diagnostic marker",
                "field diagnostics",
                "diagnostic",
                "post-delta",
                "loop-breaking",
                "loopbreak",
                "closure-field",
                "not a replacement",
                "not replace",
                "ascii aliases",
                "operator family",
                "forbidden default",
                "forbidden default exposition",
                "forbidden example",
                "anti-symbol-theater",
            ],
        )
        for marker in DEFAULT_FIELD_DIAGNOSTIC_MARKERS:
            has_control_context = _has_any_context(window, DEFAULT_FORMAL_MARKER_CONTROL_TERMS)
            if marker in line and not TARGET_EXPLICIT_FIELD_DIAGNOSTIC_RE.search(line) and not boundary_context:
                errors.append(
                    f"{label} contains field diagnostic marker without explicit target: "
                    f"{marker!r} on line {index + 1}"
                )
            if marker in line and not has_control_context and not boundary_context:
                errors.append(
                    f"{label} contains field diagnostic marker without compact control context: "
                    f"{marker!r} on line {index + 1}"
                )
        lower_line = line.lower()
        for term in DEFAULT_FORBIDDEN_FORMALISM_EXPOSITION:
            if term in lower_line and not _has_any_context(window, DEFAULT_RUNTIME_CONTEXT_REQUIRED):
                errors.append(
                    f"{label} contains default-forbidden formalism exposition without "
                    f"an explicit boundary/example context: {term!r} on line {index + 1}"
                )
        for term in DEFAULT_RUNTIME_FORMALISM_CLAIM_FORBIDDEN:
            if term.lower() in lower_line and (
                "does not" in window.lower()
                or "not " in window.lower()
                or "cannot " in window.lower()
            ):
                continue
            if term.lower() in lower_line and not _has_any_context(window, DEFAULT_RUNTIME_CONTEXT_REQUIRED):
                errors.append(
                    f"{label} contains forbidden formalism claim without explicit boundary/example context: "
                    f"{term!r} on line {index + 1}"
                )


def check_formal_marker_policy_samples(errors: list[str]) -> None:
    for name, sample in FORMAL_MARKER_POSITIVE_SAMPLES.items():
        sample_errors: list[str] = []
        check_default_formal_marker_policy(sample, sample_errors, f"formal-marker positive sample {name}")
        if sample_errors:
            errors.append(f"formal-marker positive sample rejected: {name}: {sample_errors!r}")
    for name, (sample, expected_fragment) in FORMAL_MARKER_BAD_SAMPLES.items():
        sample_errors = []
        check_default_formal_marker_policy(sample, sample_errors, f"formal-marker bad sample {name}")
        if not any(expected_fragment.lower() in error.lower() for error in sample_errors):
            errors.append(
                "formal-marker bad sample was not rejected: "
                f"{name} expected {expected_fragment!r}, got {sample_errors!r}"
            )


SUBMOVE_BOUNDARY_EXAMPLE_RE = re.compile(
    r"(?ims)^## Default-Mode Worked Example\s+.*?Boundary Discipline\b(?P<body>.*?)(?=^---\s*$|^##\s|\Z)"
)
OLD_HARD_SMOKE_EXAMPLE_RE = re.compile(
    r"(?i)\bThe Satanic Temple'?s tenets are more humane\b"
)


def check_submove_boundary_worked_example(corpus: str, errors: list) -> None:
    match = SUBMOVE_BOUNDARY_EXAMPLE_RE.search(corpus)
    if not match:
        errors.append("missing submove-boundary worked example")
        return

    body = match.group("body")
    normalized_body = " ".join(body.split())
    layer_a_count = len(re.findall(r"(?im)^#{3,5}\s*Layer A\b", body))
    if layer_a_count < 1:
        errors.append("submove-boundary worked example does not show Layer A")
    if OLD_HARD_SMOKE_EXAMPLE_RE.search(body):
        errors.append("submove-boundary worked example uses named hard-smoke wording")
    if "source-worldview consequence" not in body:
        errors.append(
            "submove-boundary worked example does not keep source-worldview burden live"
        )
    if "release the next burden-cycle" not in body:
        errors.append(
            "submove-boundary worked example does not license the next bounded pass"
        )
    r_idx = body.find("`R(H,Delta)`")
    premature_close_idx = body.find("Remaining input-anchored burdens: none")
    if premature_close_idx != -1 and (r_idx == -1 or premature_close_idx < r_idx):
        errors.append(
            "submove-boundary worked example closes before state re-read"
        )
    if (
        "Hard compound source-request cases often require several burden-cycles"
        not in normalized_body
    ):
        errors.append(
            "submove-boundary worked example lacks source-worldview load-bearing rule"
        )


def main() -> int:
    root = repo_root()
    errors = []

    check_current_doc_staleness(root, errors)
    check_render_shape_samples(errors)
    check_formal_marker_policy_samples(errors)

    corpus = read_runtime(root, errors)
    lower = corpus.lower()
    check_submove_boundary_worked_example(corpus, errors)

    for token in REQUIRED_TOKENS:
        if token.lower() not in lower:
            errors.append(f"missing render-mode invariant in generated runtime: {token!r}")

    for token in DEFAULT_REQUIRED_FORMAL_STATE_MARKER_TOKENS:
        haystack = corpus if any(ord(ch) > 127 for ch in token) else lower
        needle = token if any(ord(ch) > 127 for ch in token) else token.lower()
        if needle not in haystack:
            errors.append(f"missing default formal state-marker policy token in generated runtime: {token!r}")

    for token in FORBIDDEN_TOKENS:
        if token.lower() in lower:
            errors.append(f"forbidden render-mode claim in generated runtime: {token!r}")

    check_default_formal_marker_policy(corpus, errors)

    lines = corpus.splitlines()
    for index, line in enumerate(lines):
        window = "\n".join(lines[max(0, index - 1) : min(len(lines), index + 2)])
        for token in DEFAULT_RUNTIME_FORMALISM_CLAIM_FORBIDDEN:
            if token.lower() in line.lower() and (
                "does not" in window.lower()
                or "not " in window.lower()
                or "cannot " in window.lower()
            ):
                continue
            if token.lower() in line.lower() and not _has_any_context(
                window,
                DEFAULT_RUNTIME_CONTEXT_REQUIRED
                + [
                    "forbidden default",
                    "forbidden default exposition",
                    "forbidden example",
                    "anti-symbol-theater",
                    "not truth",
                    "not warrant",
                ],
            ):
                errors.append(
                    "default runtime surface contains forbidden NLA/Shannon/formalism claim "
                    f"without boundary context: {token!r} on line {index + 1}"
                )

    for token in DEFAULT_RUNTIME_NLA_FORBIDDEN:
        haystack = corpus if token in {"NLA", "FVE"} else lower
        needle = token if token in {"NLA", "FVE"} else token.lower()
        if needle in haystack:
            errors.append(f"default runtime surface contains forbidden NLA jargon: {token!r}")

    if "symbol theater" in lower and "control effect" not in lower:
        errors.append("default runtime surface contains symbol-theater language without control-effect boundary")

    for token in DEFAULT_RUNTIME_CONTEXTUAL_FORMALISM:
        if token in corpus and not any(context in lower for context in DEFAULT_RUNTIME_CONTEXT_REQUIRED):
            errors.append(
                "default runtime surface contains raw expanded formalism without "
                f"a bounded audit/formalism context: {token!r}"
            )

    generated_skill = out_dir(root) / "SKILL.md"
    if generated_skill.is_file():
        skill_text = generated_skill.read_text(encoding="utf-8")
        invariant_idx = skill_text.find("# Default Output Surface Invariant")
        addendum_idx = skill_text.find("# Compiled Runtime Routing Addendum")
        mandate_idx = skill_text.find("# EXECUTION MANDATE")
        if invariant_idx == -1:
            errors.append("generated skill root missing top Default Output Surface Invariant")
        elif addendum_idx != -1 and addendum_idx < invariant_idx:
            errors.append(
                "generated skill root places compiled routing vocabulary before "
                "Default Output Surface Invariant"
            )
        if mandate_idx == -1:
            errors.append("generated skill root missing EXECUTION MANDATE section")
        elif invariant_idx != -1 and mandate_idx > invariant_idx:
            errors.append(
                "generated skill root places EXECUTION MANDATE after "
                "Default Output Surface Invariant (must come before)"
            )
        if invariant_idx > 0:
            pre_invariant = skill_text[:invariant_idx].lower()
            for artifact in [
                "matched_modules",
                "source_basis",
                "diagnostic ir",
                "case state",
                "recursion decision",
                "next_eligible_pass",
            ]:
                if artifact in pre_invariant:
                    errors.append(
                        "generated skill root exposes internal artifact vocabulary "
                        f"before the default-output invariant: {artifact!r}"
                    )

    gate_text = read_dispatch_gate(root, errors)
    gate_lower = gate_text.lower()
    for token in DISPATCH_GATE_REQUIRED:
        if token.lower() not in gate_lower:
            errors.append(
                f"dispatch-gate bundle missing render-mode policy token: {token!r}"
            )
    scope_count = gate_lower.count(
        "render-mode scope: this template is an internal control shape"
    )
    if scope_count < 2:
        errors.append(
            "dispatch-gate bundle does not mark both IR and Case State templates "
            "as not default-facing"
        )

    fixture_path = (
        root
        / "tests/routing-fixtures/11-secular-moral-protest-hiddenness-imported-criterion.json"
    )
    if fixture_path.is_file():
        fixture_text = fixture_path.read_text(encoding="utf-8")
        fixture_lower = fixture_text.lower()
        for token in FIXTURE_REQUIRED_TOKENS:
            if token.lower() not in fixture_lower:
                errors.append(f"fixture 11 missing behavior-shape token: {token!r}")
        for token in FIXTURE_FORBIDDEN_TOKENS:
            if token.lower() in fixture_lower:
                errors.append(f"fixture 11 still rewards label cosplay: {token!r}")
    else:
        errors.append("fixture 11 missing for render-mode drift guard")

    if not errors:
        print("Render mode governance summary")
        print("-" * 60)
        print(f"Runtime files checked: {len(RUNTIME_FILES)}")
        print(f"Required invariants checked: {len(REQUIRED_TOKENS)}")
        print(f"Forbidden claims checked: {len(FORBIDDEN_TOKENS)}")
        print(f"Dispatch-gate policy tokens checked: {len(DISPATCH_GATE_REQUIRED)}")
        print(f"Dispatch-gate template scope markers: {scope_count}")
        print(f"Fixture 11 behavior tokens checked: {len(FIXTURE_REQUIRED_TOKENS)}")
        print(f"Render-shape bad samples checked: {len(RENDER_SHAPE_BAD_OUTPUTS)}")
        print(f"Render-shape positive samples checked: {len(RENDER_SHAPE_POSITIVE_OUTPUTS)}")
        print(f"Current governance docs checked: {len(CURRENT_GOVERNANCE_DOCS)}")
        print(f"Current-doc stale tokens checked: {len(STALE_CURRENT_DOC_TOKENS)}")
        print("-" * 60)

    return fail_with_errors("render mode governance", errors)


if __name__ == "__main__":
    sys.exit(main())
