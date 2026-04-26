---
id: R1-internalist-criterion
module_class: tactic
canonical_path: skill/references/tactics/R1-internalist-criterion.md
contract_version: "0.2.3.0"
load_when:
  - interlocutor holds that knowledge of God requires inferential argument
companions:
  - R2-the-reminder
  - R3-warranted-basic-belief
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

# R1 — Challenging the Internalist Criterion

**Register:** Reformed Epistemology / Basic Belief
**Deploy when:** Interlocutor holds that knowledge of God requires inferential argument.

Reject the premise. Draw the analogy with other domains of basic belief — other minds, the past, the reliability of memory — none of which rest on argument, yet all considered rational and warranted. The criterion that disqualifies theistic belief equally disqualifies these. It proves too much.

**Formally:** A belief has warrant when produced by cognitive faculties functioning properly, successfully aimed at truth, in environments to which those faculties have been designed to apply. The fiṭrah is precisely such a faculty. When functioning without corruption, it produces warranted belief in God directly — properly basic, without inference. See `references/sound-reason-epistemology.md` §2–3 for the full proper-function account.

**Connection:** R1 clears the criterion; R2 directs attention to the basic belief already present; R3 applies the proper-function framework to the interlocutor's own experience.

## Failure Conditions

**Do not deploy when:**
- The interlocutor is not actually running an internalist criterion. If they have not demanded argument as a precondition for theistic belief, pressing R1 introduces a criterion-debate they were not having. Confirm that the demand for inferential argument is operative before deploying.
- The interlocutor already accepts basic belief in principle and has not restricted it specifically to theism. If they accept that other minds, memory, and the past are warranted non-inferentially and have not explicitly excluded theism, R1 presses a door that is already open. Proceed directly to R2 (eliciting the basic belief) or R3 (proper-function application).
- Juḥūd or istikbār is the concealment mode. When the criterion demand is a face-saving structure rather than a genuine epistemological commitment, clearing the criterion philosophically does nothing — the barrier is not epistemic. The interlocutor will acknowledge the analogy and continue withholding. Read concealment mode before routing to R1.
- Hawā or gharaḍ is the primary deformation. The criterion demand is serving as a rationalization for a volitional resistance. F2 must surface the volitional dimension; removing the philosophical cover without addressing the resistance beneath it does not clear the barrier.

**R1 fails when:**
- The interlocutor accepts the analogy for other domains but carves out theism as a special case requiring inference: "basic belief is fine for other minds, but theistic belief involves a higher-stakes metaphysical claim that requires argument." This is no longer a universal criterion objection — it is a specifically theistic restriction. E2 presses at the meta-level (the universal criterion proves too much); R1 is now at the object-level (the theism-specific restriction). Both may be in play; R1's work here is to push back on the claimed asymmetry: what makes theistic belief specifically subject to a stricter standard?
- The interlocutor defends global internalism — denying that other minds, memory, or the past are warranted non-inferentially. The analogy is absorbed. M1 (self-refutation: a global internalist cannot hold the internalist position by its own standard) is required before R1's analogy can gain purchase.

## IR-Visible Consequences

When R1 is live:
- **routing_gate**: marks criterion-challenge active for the Reformed route; opens the R2 → R3 chain as a permissible continuation
- **matched_modules**: expands to include R2 and R3 once the criterion is challenged; E2 if the interlocutor shifts to a universal internalist defense
- **held_material**: R2 (reminder) and R3 (proper-function application) are held pending R1 — deploying them before the criterion is challenged allows the criterion to filter the recognition they elicit
- **output_shape**: bounded-single-pass — R1 makes one criterion-challenge move; reassessment governs continuation

If R1 lands (criterion acknowledged as proving too much, or theism-specific restriction remains):
- If criterion loosened: R2 and R3 released; Reformed route fully open
- If theism-specific restriction remains: R1's work is to push back on the asymmetry; the case continues at object-level

If R1 does not land (global internalism defended):
- Route to M1 (self-refutation of global internalism) before returning to R1's analogy

## Minimal-Pair Discriminators

**R1 vs. E2 (inferential criterion):**
E2 presses at the meta-level: the universal inferential criterion proves too much — it disqualifies other minds, memory, the past. R1 presses at the object-level: even if some basic belief is acceptable, theistic basic belief specifically is not disqualified by a proper-function account. E2 first when the criterion is stated universally; R1 when the specifically theistic restriction remains after E2 has softened universal internalism — or when E2 was bypassed and the interlocutor is operating with an implicit theism-specific restriction from the outset.

**R1 vs. R3 (warranted basic belief):**
R1 challenges the criterion that bars the door to basic theistic belief. R3 applies the proper-function framework to the interlocutor's own involuntary recognition. Sequencing: R1 clears the criterion, R2 elicits the recognition, R3 engages what that recognition is philosophically. Do not deploy R3 before the criterion is at least challenged by R1 — the interlocutor's criterion will filter the recognition R3 engages.

**R1 vs. doubt-vs-skepticism:**
Doubt-vs-skepticism challenges the framework claim that evidence is the default requirement for all belief. R1 challenges the specific claim that theistic belief requires inferential argument — within a framework that already accepts some basic belief. Doubt-vs-skepticism when the interlocutor treats evidence as the neutral universal default; R1 when the interlocutor accepts basic belief for other domains but restricts theism to the inferential requirement.

## Hold / Release Discipline

R2 and R3 are held pending R1. R2 (the reminder — eliciting basic theistic belief) and R3 (proper-function analysis of the interlocutor's own recognition) both presuppose that the criterion blocking basic belief has at least been challenged. Deploying R2 before R1 allows the criterion to dismiss the recognition as anecdotal feeling, not warrant. Deploying R3 before R1 allows the criterion to dismiss the proper-function account as begging the question.

**Release signal:** The interlocutor has acknowledged that the analogy creates pressure for the criterion, or has shifted from a universal to a theism-specific restriction. Either signals R1 has done its work; R2 and R3 are now available.

**Do not loop R1:** If the criterion is defended by global internalism, R1 cannot proceed until M1 (self-refutation) has been applied. If concealment is operative, philosophical criterion-clearing will not move the interlocutor regardless of the argument's quality. Diagnose before iterating.

## Anti-Pattern Guard

**Over-deployment when criterion not operative:** Running R1 when the interlocutor has not demanded argument as a precondition for belief. This introduces a criterion-debate the interlocutor was not having and reads as a non-sequitur. Confirm the internalist criterion is actually operative before deploying.

**Skipping to R3 without R1:** Applying the proper-function framework to the interlocutor's own recognition (R3) when the internalist criterion has not been challenged. The criterion will be used to classify the recognition as a psychological curiosity rather than a cognitive deliverable, and R3 will not gain purchase.
