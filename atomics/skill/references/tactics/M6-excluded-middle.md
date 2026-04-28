---
id: M6-excluded-middle
module_class: tactic
canonical_path: skill/references/tactics/M6-excluded-middle.md
contract_version: "0.3.0.0"
load_when:
  - interlocutor retreats into indefiniteness, evasion, or refusal to commit
  - evasive stock phrases used as conversational exits
routing_effects:
  - pairs with M7-definition-anchor as sequential move — M7 anchors proposition first, M6 applies truth-value commitment
companions:
  - M7-definition-anchor
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

# M6 — The Excluded Middle as Immediate Conversational Instrument

**Type:** Meta-tactic
**Deploy when:** Interlocutor retreats into indefiniteness, evasion, or refusal to commit; "it's complicated," "you can't really say," "who's to know."

The Law of the Excluded Middle (a proposition is either true or false; there is no third option) is deployable as an immediate conversational move against evasion.

**Four-step deployment:**
1. State the proposition clearly and precisely. Precision matters — vague propositions are harder to apply the Excluded Middle to.
2. Apply the law: "This proposition is either true or false. There is no third option."
3. Address the evasion: "Declining to determine which it is does not change which it is. It only determines whether you are engaged in the question honestly."
4. Block the incredulity fallacy: inability to verify the truth of a proposition does not establish its falsity. "I cannot see how X could be true" is evidence about the limits of the speaker's current understanding, not evidence that X is false. The denial of a claim requires its own grounds, symmetric with those demanded for the affirmation.

**The incredulity fallacy:** A common move is to treat absence of evidence (from the interlocutor's perspective, given their evidential criteria) as evidence of absence. Name this: "you cannot see how X could be true — but that is a claim about your current understanding, not a claim about X."

**Connection:** M6 is often deployed alongside M7 (definition anchor) — first anchor the proposition precisely, then apply the Excluded Middle.

## Failure Conditions

**Do not deploy when:**
- The proposition is still poorly defined. Applying the Excluded Middle to a vague proposition ("God exists" without disambiguation of what "God" means) allows the interlocutor to escape by disputing the terms rather than the truth-value question. M7 (definition anchor) must establish a working definition first. Applying M6 before M7 generates a debate about which proposition is being evaluated.
- The evasion is grief-primary or pastoral in character. When the interlocutor retreats from the question because they are in distress, anger, or grief, the excluded-middle press reads as cold and confrontational — it demands epistemic performance at a moment when the operative barrier is affective. M4 (pastoral register) governs; attempting to force truth-value commitment at this moment damages rapport without advancing the question.
- Iʿrāḍ (deliberate turning away) is the concealment mode. A person who is actively avoiding the question as a volitional matter will not be moved by the observation that the proposition has a truth-value. The press becomes a show of force that the interlocutor absorbs without engaging. F2 (volitional deformation) must surface the turning-away first; M6 cannot clear what it cannot name.
- The vagueness is a deliberate theological position (apophatic theology, strong divine ineffability claims). In this case, the interlocutor is not evading — they hold that the proposition as stated cannot be evaluated as true or false given divine transcendence. M6 applied here reads as philosophically naive. Route to M7 for a qualified-proposition anchor, or to the substantive theological question about what claims can coherently be made about God.

**M6 fails when:**
- The interlocutor accepts that the proposition has a truth-value but continues to withhold commitment on grounds of insufficient evidence. This is not evasion — it is an epistemic position. The move has shifted from M6's excluded-middle territory to doubt-vs-skepticism (evidence-demand burden analysis) or M2 (prior probability).
- The interlocutor redefines the proposition to make it true by stipulation rather than engaging the truth-value question. This is a definitions dispute; return to M7 to anchor.

## IR-Visible Consequences

When M6 is live:
- **routing_gate**: truth-value-commitment active; evasion named as a conversational posture, not a substantive response
- **matched_modules**: typically follows M7; if M6 lands, case continues with the now-defined proposition as the active question
- **held_material**: M6 does not hold downstream content — it clears an evasion that was blocking continuation
- **output_shape**: bounded-single-pass — one application of excluded middle; reassessment governs whether the proposition is now engaged

If M6 lands (interlocutor acknowledges the proposition has a truth-value and must be engaged):
- Evasion cleared; case-state updates to proposition-under-direct-examination

If M6 does not land (evasion continues):
- Re-read concealment mode: if iʿrāḍ is now confirmed, update case-state and route to F2; do not iterate M6

## Minimal-Pair Discriminators

**M6 vs. M7 (definition anchor):**
M7 addresses definitional evasion — the interlocutor retreats into "it depends what you mean by X." M6 addresses truth-value evasion — the interlocutor retreats into "who can say whether X is true?" These can co-occur but require sequential ordering: M7 anchors the proposition first, then M6 presses the truth-value commitment. M7 when the primary evasion is definitional; M6 when the proposition is defined but the interlocutor refuses to evaluate it.

**M6 vs. M1-P (performative self-refutation):**
M1-P shows that the act of asserting a claim enacts what the claim denies. M6 shows that retreating from a truth-value claim does not alter the claim's truth-value. M1-P when the evasion-move is itself a performative assertion; M6 when the evasion is withdrawal from commitment rather than a counter-assertion.

**M6 vs. doubt-vs-skepticism:**
Doubt-vs-skepticism addresses the framework claim that evidence is required before any belief is rational. M6 addresses the specific conversational move of refusing to commit to a truth-value. M6 when the interlocutor is evading the question; doubt-vs-skepticism when the interlocutor is demanding evidence as a precondition for the question being engaged at all.

## Hold / Release Discipline

M6 holds no downstream content. It clears an evasion that was blocking the question from being engaged directly. Once the evasion is cleared, continuation is governed by whichever tactic or procedure is appropriate to the now-active proposition.

**Prerequisite:** A defined proposition (from M7) must be in place before M6 can operate. If M7 has not yet anchored the proposition, deploy M7 first.

**Do not loop M6:** If the evasion continues after one clear application of excluded middle, iterating with more force does not help. Diagnose the operative mode — grief, iʿrāḍ, or apophatic theology each require different responses. The signal to update rather than iterate is any continued evasion after one clear excluded-middle application.

## Anti-Pattern Guard

**Premature deployment before M7:** Applying excluded middle to an undefined proposition. The interlocutor correctly notes that they cannot evaluate the truth-value of an ambiguous claim. Confirm the proposition is anchored before pressing truth-value commitment.

**Force as iteration:** Repeating M6 with increasing rhetorical pressure when the first application did not move the interlocutor. This reads as a confrontational performance, not a philosophical move. One clean application is the unit; continued evasion is diagnostic data, not an invitation to escalate.
