---
id: M2-prior-probability
module_class: tactic
canonical_path: skill/references/tactics/M2-prior-probability.md
contract_version: "0.2.0.0"
load_when:
  - evidential arguments appear (problem of evil, divine hiddenness, religious diversity)
  - probabilistic argument assumes an implicit near-zero prior for God's existence
routing_effects:
  - prerequisite to engaging DO-1, DO-2, and DO-4 when their probabilistic force depends on an unexamined prior
companions:
  - do-core
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
load_class: routed
bundle: none
execution_phase: render
governs: []
must_precede: [render]
blocks_if_missing: false
trigger_conditions:
  - evidential arguments appear (problem of evil, divine hiddenness, religious diversity)
  - probabilistic argument assumes an implicit near-zero prior for God's existence
operator_pack: []
source_status: canonical
verification_status: L_check
direct_read_required: true
direct_read_verified: true
failure_conditions_present: true
ir_consequences_present: true
minimal_pairs_present: true
hold_release_rules_present: true
compiled_runtime_eligible: true
operator_pack_eligible: true
---

# M2 — Prior Probability Probe

**Type:** Meta-tactic
**Deploy when:** Evidential arguments appear — problem of evil, divine hiddenness, religious diversity. These arguments are probabilistic.

Surface the implicit prior probability being assigned to God's existence. These arguments only do their claimed work if the prior is near-zero. But the near-zero prior is precisely what is under dispute — it cannot be assumed.

**The prior grounded in what is native to human cognition:** The prior established by the fiṭrah's basic deliverances, the convergence of three knowledge sources, and the cross-cultural universality of theistic recognition (tawātur fiṭrī) is not near-zero. The evidential weight of suffering, hiddenness, or diversity must be assessed against this prior — not against a near-zero prior the interlocutor is assuming as neutral.

**The key move:** "This argument is probabilistic — it shows that the evidence lowers the probability of God's existence. But from what starting point? The prior probability you are assigning is not neutral — it is itself a position that requires grounds. What is it, and why?"

**Connection:** M2 is prerequisite to engaging DO-1 (divine hiddenness), DO-2 (problem of evil), and DO-4 (religious diversity) from `references/case-library/do-core.md`.

## Failure Conditions

**Do not deploy when:**
- The argument is deductive, not probabilistic. If the interlocutor is running a logical argument ("it is impossible for an omnipotent, omniscient, omnibenevolent God to coexist with any evil"), M2's prior-probability probe is off-register. A logical contradiction is not a probability update — it is a claim that the conjunction is impossible. Route to M1 (internal consistency check of the argument's premises) or M8 (formal reductio). Symptom: interlocutor says "even one instance of gratuitous evil disproves God," not "the amount of suffering makes God unlikely."
- Grief or suffering is the primary register, not argument. When the interlocutor is in acute emotional distress ("I cannot believe in God after what happened to X"), surfacing a prior-probability probe reads as cold rationalization of their pain. M4 (pastoral register) governs first. M2 becomes available only after the affective dimension has been acknowledged.
- The prior has already been surfaced and accepted. If the interlocutor has already conceded that the prior is not obviously near-zero, the work M2 does is complete. Proceeding to re-run the probe is redundant — move to DO-1/DO-2/DO-4 substantive content.

**M2 fails when:**
- The interlocutor concedes that the prior is not settled but insists their argument is deductive, not probabilistic. This is a form-of-argument challenge, not a prior question. M1 or M8 governs from here.
- The interlocutor accepts that the prior matters but asserts a specific alternative grounding for a low prior (e.g., "divine hiddenness itself justifies a low prior"). This shifts from the existence of a prior to the justification of a specific prior. Do not iterate M2; engage the substantive grounding claim directly.

## IR-Visible Consequences

When M2 is live:
- **routing_gate**: DO-1, DO-2, and DO-4 substantive content is held until prior is surfaced and acknowledged as not neutral
- **matched_modules**: expands to include DO-1/DO-2/DO-4 substantive responses once prior is acknowledged; M1 or M8 if argument turns out to be deductive
- **held_material**: DO-1/DO-2/DO-4 response content — held pending prior acknowledgment
- **output_shape**: bounded-single-pass — M2 makes one move (surface the prior); reassessment governs continuation

If M2 lands (prior acknowledged as non-neutral):
- prior-acknowledged flag set; DO-1/DO-2/DO-4 responses released

If M2 does not land (prior defended or argument framed as deductive):
- If argument is deductive: update case-state, clear M2, route to M1 or M8
- If prior justified on substantive grounds: engage those grounds directly; do not loop M2

## Minimal-Pair Discriminators

**M2 vs. direct DO-1/DO-2/DO-4 engagement:**
DO-1/DO-2/DO-4 assume the prior question has been settled or is not contested. M2 surfaces the prior as the prerequisite condition for those arguments to carry probabilistic weight. Run M2 first when the evidential argument is being deployed as if its force were self-evident; proceed directly to DO-entries when the interlocutor has already acknowledged that prior probability is relevant and contestable.

**M2 vs. M1 (internal consistency):**
M1 targets the logical structure of an argument — whether premises support conclusion, whether the argument is self-refuting. M2 targets the background assumption about prior probability that gives a formally valid probabilistic argument its claimed weight. M2 when the argument is probabilistic; M1 when the argument is deductive or structurally self-undermining.

**M2 vs. M8 (reductio):**
M8 shows that accepting an argument's premises leads to an absurd consequence that the interlocutor will not accept. M2 probes the hidden premise (near-zero prior) without yet showing where it leads. Run M2 to surface the hidden assumption; M8 to show the consequences of that assumption applied consistently.

## Hold / Release Discipline

M2 holds DO-1, DO-2, and DO-4 substantive response content. These arguments presuppose a resolved prior question; deploying them before the prior is surfaced allows the interlocutor's implicit near-zero prior to operate unexamined throughout.

**Release signal:** The interlocutor has stated their prior or acknowledged that the prior is not automatically near-zero. Even a partial acknowledgment ("I suppose the prior matters, but I still think the amount of suffering is significant") releases the hold — the prior is now in play, and the substantive DO-entry content can engage.

**Do not loop M2:** If the interlocutor refuses to acknowledge the prior question, do not re-state the probe with more force. Diagnose: is this a genuine philosophical commitment to the neutrality of evidence (shubhah requiring V2 to reconstitute the reason-concept), or is it a form-of-argument mismatch (deductive, not probabilistic)? Either route clears the impasse; looping M2 does not.

## Anti-Pattern Guard

**Form-of-argument mismatch:** Deploying M2 when the interlocutor's argument is structurally deductive. The probabilistic-prior probe is off-register for logical-impossibility arguments. Confirm the argument is probabilistic before deploying.

**Register mismatch:** Deploying M2 when grief or emotional distress is the actual operative state. The probe reads as cold rationalization of pain. This is the most common misuse in pastoral contexts — the intellectual framing of "problem of evil" can mask an affective crisis. Read the register before routing to M2.
