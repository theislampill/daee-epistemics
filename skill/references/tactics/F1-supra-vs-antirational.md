---
id: F1-supra-vs-antirational
module_class: tactic
canonical_path: skill/references/tactics/F1-supra-vs-antirational.md
contract_version: "0.2.2.0"
load_when:
  - interlocutor equates religious commitment with abandoning reason
companions:
  - R1-internalist-criterion
  - E3-cumulative-case
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

# F1 — Distinguishing Supra-rational from Anti-rational

**Register:** Fideist
**Deploy when:** Interlocutor equates religious commitment with abandoning reason.

Faith as going *beyond* what strict proof can establish is categorically different from faith as *contradicting* what reason establishes. Hard Fideism collapses them; Soft Fideism — which the tradition endorses — maintains the distinction.

Many things rightly committed to — love, trust, moral principle, the worth of a human life — exceed formal demonstration without being irrational. When an interlocutor equates religious commitment with abandoning reason, name and contest the conflation.

**The tradition's position:** Genuine reason (ʿaql ṣarīḥ) operating without distortion and genuine revelation properly understood are fully corroborative. Where they appear to conflict, either the reason is contaminated (bidʿī ʿaqlī) or the revelation is being misread (bidʿī naqlī). Never pure reason against true revelation.

**Connection:** Once the supra/anti distinction is established, move to the positive case: R1 (basic belief) or E3 (cumulative case).

## Failure Conditions

**Do not deploy when:**
- The objection is a specific substantive challenge framed in the rhetoric of reason vs. religion. If the interlocutor says "Islam abandons reason" but is actually pressing a specific claim (evolution conflicts with scriptural cosmology, penal rulings conflict with human rights norms, a specific hadith contradicts scientific consensus), F1 clears the rhetorical framing but cannot substitute for addressing the substantive content. F1 is needed, but the substantive objection must be routed to the appropriate DO/RT entry after. Deploying F1 and stopping there — as if clearing the framing resolves the substantive objection — is the primary anti-pattern.
- Hawā or gharaḍ is the primary deformation. When the "religion abandons reason" characterization is functioning as a rationalization for volitional resistance, F1's conceptual distinction will be acknowledged and set aside without movement. The distinction lands philosophically but generates no traction. F2 must surface the volitional dimension; clearing the characterization without addressing the resistance beneath it does nothing.
- V2 is needed first. If the interlocutor's conception of reason is contaminated (bidʿī ʿaqlī — reason implicitly restricted to empirically verifiable claims, or to a prior metaphysical picture presented as neutral), then establishing the supra/anti distinction within that contaminated framework achieves little — "supra-rational" will be heard as "beyond what reason can verify," which, under the contaminated conception, is the same as anti-rational. V2 must reconstitute the conception of reason first so that "supra-rational" can be properly understood as "exceeding formal proof" rather than "contradicting genuine reason."
- The interlocutor is defending Hard Fideism themselves. If the case involves someone from within a tradition who holds that faith operates independently of and against reason — that intellectual submission is the proper response to revelation regardless of what reason says — F1 is not the move. The structure of that conversation is different; the supra/anti distinction is not the operative question.

**F1 fails when:**
- The interlocutor accepts the supra/anti distinction in the abstract but insists that theism specifically falls on the anti-rational side: "going beyond proof is fine, but I have positive reasons to think theism is false, not just absence of proof." This is not a characterization problem — it is a substantive evidential or logical claim. F1 has done its clearing work; the case now routes to the evidential or meta-tactic register to address the positive reasons claimed.
- The interlocutor grants the supra/anti distinction but reasserts the contaminated reason-concept: "what I mean by reason is the scientific method, and faith goes beyond that." V2 must engage the conception of reason before F1's distinction can carry weight in this framework.

## IR-Visible Consequences

When F1 is live:
- **routing_gate**: characterization-correction active; positive-case content held while the supra/anti distinction is being established — do not deploy R1, E3, or V5 until the characterization is cleared
- **matched_modules**: R1 (basic belief) and E3 (cumulative case) become available as positive-case next moves once the distinction is established; V2 added to matched_modules if reason-concept contamination is identified during F1
- **held_material**: the positive case — evidential content, basic-belief account, cumulative case structure — is held pending characterization correction. Deploying positive-case content before the faith-vs-reason conflation is cleared allows the conflation to filter all content as anti-rational.
- **output_shape**: bounded-single-pass — F1 makes one characterization-correction move; reassessment governs what follows

If F1 lands (supra/anti distinction acknowledged):
- Characterization-correction complete; case-state updates to positive-case available; R1 or E3 released

If F1 does not land (conflation reasserted or reason-concept contamination active):
- If reason-concept contaminated: add V2 to matched_modules; route to V2 before returning to F1
- If specific substantive objection beneath the framing: route to appropriate DO/RT entry

## Minimal-Pair Discriminators

**F1 vs. V2 (reconstituting reason):**
V2 addresses the contaminated conception of reason itself — showing that "reason" restricted to empirically verifiable claims is a historically contingent philosophical stance, not reason as such. F1 addresses how faith is being characterized relative to reason — showing that "beyond proof" is not the same as "against reason." V2 when the interlocutor's conception of reason needs reconstitution before the faith-characterization can be properly assessed; F1 when the conception of reason is adequate but the faith-characterization is wrong. Often sequenced: V2 first (clear the reason-concept), then F1 (clarify the faith-characterization within the cleared concept).

**F1 vs. E2 (inferential criterion):**
E2 challenges the claim that inferential argument is necessary for warranted theistic belief — it targets the epistemological criterion. F1 challenges the characterization of faith as anti-rational — it targets the conceptual framing. E2 when the interlocutor holds that argument is necessary for warrant; F1 when the interlocutor characterizes faith itself as abandoning reason. These can co-occur; they address different levels of the same objection.

**F1 vs. M1 (internal consistency):**
M1 shows that an argument's premises undermine its conclusion or are self-refuting. F1 contests a conceptual conflation — Hard Fideism is not the tradition's position; the conflation of supra-rational with anti-rational is wrong. M1 when there is a specific argument to subject to internal-consistency analysis; F1 when the operative problem is a category mistake about faith's relationship to reason.

## Hold / Release Discipline

F1 holds all positive-case content (R1, E3, V5) pending the characterization correction. Deploying the positive case — the full account of how theism is rational — into an uncleared frame where "religious commitment = anti-rational" means that each element of the positive case is absorbed as evidence of the anti-rational framing. The positive case cannot land until the frame is cleared.

**Release signal:** The interlocutor has acknowledged the supra/anti distinction, or has shifted from a characterization objection to a substantive evidential or logical objection. Either signals F1's work is done; the positive case is now appropriate.

**Sequencing note:** F1 is a characterization-clearing move, not a positive case. It must be followed by substantive content once the frame is clear. F1 that clears the frame and stops, without directing to R1 or E3, leaves the conversation in mid-air.

## Anti-Pattern Guard

**Addressing the frame without the substance beneath it:** The most common misuse of F1. Clearing the "reason vs. faith" framing without identifying and routing to the substantive objection that was generating it. F1 that addresses only the rhetoric while the underlying intellectual challenge goes unaddressed leaves the interlocutor's real question unanswered. After F1 lands, read the case for the substantive objection that was being framed rhetorically, and route to it.

**Deploying F1 before V2 when reason-concept is contaminated:** If "reason" means "empirically verifiable claims" in the interlocutor's framework, then the supra/anti distinction lands within a framework where "supra-rational" is already interpreted as anti-rational. The distinction requires a sound conception of reason to operate. V2 first.
