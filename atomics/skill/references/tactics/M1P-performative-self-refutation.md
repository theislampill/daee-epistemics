---
id: M1P-performative-self-refutation
module_class: tactic
canonical_path: skill/references/tactics/M1P-performative-self-refutation.md
contract_version: "0.4.0.0"
load_when:
  - act of asserting a position enacts what the position denies
companions:
  - M1-self-refutation
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
verification_status: L_check
direct_read_verified: true
failure_conditions_present: true
ir_consequences_present: true
minimal_pairs_present: true
hold_release_rules_present: true
compiled_runtime_eligible: true
operator_pack_eligible: true
---

# M1-P — Performative Self-Refutation

## Runtime operator contract

- Activation: act of asserting a position enacts what the position denies.
- Field target: the live burden or submove pressure that made tactic `M1P-performative-self-refutation` eligible; activation cue: act of asserting a position enacts what the position denies.
- Burden/submove form: tactic `ⁿBᵢ[OPᵢ]`: target -> operation -> result; the result contributes to `Land(ⁿB)` only when live for the current burden.
- Δ effect: `ΔⁿB` is the local target/operation/result transition; `Δκ` changes only if the operation affects closure, dependency radius, or held routes.
- Possible ∇ reread: after the tactic lands, check target-explicit `∇·B` for remaining burden pressure or `∇×ξ`/`∇×κ` for circular criterion/dependency pressure when relevant.
- R(H,Δ) obligation: after this owner acts, reread H, remaining burdens, alternate routes, register pressure, dependency loops, and closure state before STOP/RECURSE/PARTIAL.
- Hold/release/closure effect: release only the bounded result that has landed; hold, integrate, discharge as derivative, or carry forward unresolved pressure with reason.
- Output boundary: `layer-b-permitted` with output shapes `bounded-single-pass`. Default render may show compact state markers when control-bound; long formalism stays audit/formalism-expanded.
- Negative constraints: no argument-bank drift, no scalar closure, no deterministic route freezing, no indiscriminate TTP spraying, no ∇ as Δ replacement, no proof-by-symbol, and no Shannon/reconstruction-branding/∇ truth-or-warrant claim.
- Fixture/checker: Register-formalism fixtures reference this owner (1); add direct routing coverage when this owner becomes release-critical.


**Type:** Meta-tactic
**Deploy when:** The act of asserting a position enacts what the position denies.

Standard M1 examines whether an argument's *premises*, applied consistently, undermine its *conclusion*. Performative self-refutation is different: it identifies cases where the *act of asserting* the position enacts what the position denies. The interlocutor cannot escape it by adjusting premises — they would have to stop making the assertion.

**Examples:**
- "There is no righteous guidance" — offered as righteous guidance about what to believe. If no guidance is possible, this claim cannot recommend itself as worthy of acceptance; yet its assertion implicitly does exactly that. Full working: "To advise that there is no reliable guidance is itself an instance of offering advice about what to reliably believe. If no guidance is possible, neither is this claim — which guidance are you then offering against the possibility of guidance?"
- "You cannot know anything with certainty" — stated as a certain claim
- "Language cannot communicate truth" — communicated in language as if true
- "I have no ʿaqīdah / no comprehensive worldview" — a comprehensive claim about one's epistemic situation, made using a framework
- "No one should impose their values on others" — itself a value being imposed as binding
- "All truth is relative" — offered as an absolute truth

**Delivery:** Economy is essential. State the position. Name the self-enactment. Stop. The move is either seen immediately or it is not seen — elaboration only provides cover.

Hard-case scope note: this stop is local to the M1-P operation, not a license for whole-answer
closure in a compound same-input response. When M1-P is structurally live inside a burden,
Layer B must still show the quoted assertion or speech act, the denied condition it enacts,
the resulting self-undercut, and how that state change contributes to `Land(B)`. If the
refreshed state leaves another input-anchored burden live, continue or mark PARTIAL as
governed rather than treating M1-P's economy as final closure.

## The Staged-Visibility Protocol

M1-P is even more sensitive to economy than M1. Four stages:

**Stage 1 — State the position verbatim.** Use the interlocutor's own wording. If you
paraphrase, they can disown the paraphrase. Quote them.

**Stage 2 — Name the *act* of asserting it.** Not the content of the assertion, the act.
"When you say 'there is no reliable guidance,' that statement is itself offering guidance
about what to believe."

**Stage 3 — Leave the pairing visible.** Do not resolve it. Do not explain it. The
performative contradiction is visible in the pairing of the quoted assertion and the act
of asserting it. If the pair is on the table, the move is complete.

**Stage 4 — Stop.** M1-P is destroyed by elaboration more than any other move. A second
sentence almost always reduces the weight of the first. Trust that if the move has
landed, silence is the correct next move; if it has not landed, more words will not
produce landing.

If the interlocutor absorbs M1-P without movement — rephrases the position, adds a
qualifier that preserves the self-enactment, or pivots to a new assertion — the barrier
is not intellectual. Re-read the concealment mode (likely `istikbar` or `juhud` if the
move was engaged and deflected; `irad` if the subject never engaged the move at all and
simply turned the page) and the DO-orient (likely `identity-perf`), update the
case-state, and do not repeat the move with more force. The `irad` reading in
particular forbids a second pass: naming the turn-away converts a pre-press posture
into a named barrier and hardens it.

**Connection:** This pattern also governs claims about having no religion or no comprehensive worldview: the claim enacts what it denies by offering guidance about the absence of guidance.
