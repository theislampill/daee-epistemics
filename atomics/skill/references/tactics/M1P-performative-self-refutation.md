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

- Activation: an asserted position, refusal, criterion, or speech act relies on the very norm, agency, truth-access, rational authority, or obligation it denies.
- Field target: the performed contradiction between the claim's content and the act needed to state, demand, deny, guide, or obligate by it.
- Burden/submove form: tactic `ⁿBᵢ[OPᵢ]`: quote or compactly name the performed act, identify what the act presupposes, then test whether the proposition denies that presupposition.
- Δ effect: `ΔⁿB` demotes the assertion from operative criterion to self-defeating performance when the enactment conflict lands; `Δκ` releases ordinary M1, M8, or STOP only after the performed contradiction is not merely verbal.
- Possible ∇ reread: after the exposure, check target-explicit `∇·B` for residual object-level pressure and `∇×ξ`/`∇×κ` if the interlocutor preserves the criterion by exempting their own act from it.
- R(H,Δ) obligation: reread held paraphrases, qualifications, and downstream objections to see whether the self-enactment remains, was only rhetorical, or has shifted into a different burden.
- Hold/release/closure effect: release only the specific performed contradiction; hold wider worldview consequences until the contradiction either lands or is qualified away.
- Output boundary: `layer-b-permitted` with output shapes `bounded-single-pass`. Default render may show compact state markers when control-bound; long formalism stays audit/formalism-expanded.
- Negative constraints: do not substitute premise-level M1 for performed self-refutation; do not infer contradiction from tone; do not close the whole case because one speech act fails; no scalar closure, no argument-bank drift, no proof-by-symbol, and no ∇ truth-or-warrant claim.
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
