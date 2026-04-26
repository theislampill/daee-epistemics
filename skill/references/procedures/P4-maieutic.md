---
id: P4-maieutic
module_class: procedure
canonical_path: skill/references/procedures/P4-maieutic.md
contract_version: "0.2.2.0"
load_when:
  - interlocutor in inkār mode — qalb has already registered what the tongue denies
  - recognition is present but suppressed; not the case where genuine inquiry is absent
companions:
  - R2-the-reminder
  - V5-directing-attention-signs
routing_effects:
  - sustains recognition-eliciting questioning when inkar is the governing mode
  - holds argumentative assertion while recognition is being invited to surface
emits:
  - recognition_strength
  - what_is_withheld_and_why
blocks:
  - rhetorical trap-questioning presented as maieutic inquiry
  - pressing for conclusion after recognition surfaces
output_shapes:
  - bounded-single-pass
  - recursive-traversal-permitted
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

# P4 — The Socratic-Maieutic Procedure

**For:** Interlocutors in inkār mode — where the qalb has already registered what the
tongue denies. The most appropriate procedure when there is reason to believe the recognition
is present but suppressed.

**Logic:** The dāʿī's role is not to transmit knowledge but to help the interlocutor bring
to birth knowledge already present within them. This is the logic of the tradition itself:
the Messengers do not bring information from outside; they awaken what is already present in
the fiṭrah. The prophetic tradition is explicit: no Prophet ever opened by demanding that
his people first establish knowledge of their Creator through discursive argument. Everyone
is born with the fiṭrah intact; what happens afterward casts a veil over it. The maieutic
procedure works with this — clearing the veil, not constructing knowledge from outside.

## Execution

Careful questioning rather than assertion. Invite the interlocutor to attend to their own
experience, to name what they find there, to follow the logic of their own deepest
commitments. Questions are designed to allow what is already present to surface, not to
implant something new.

Questions must be:
- Genuinely exploratory, not rhetorical — to help the interlocutor examine their own
  experience, not to trap them
- Directed at experience, not at positions: "what arises, pre-argumentatively, when you
  face genuine mortality?" not "do you believe God exists?"
- Patient — allow the response to arise without rushing to capture it in a conclusion

Gentle questioning creates space in which the disjunction between inner recognition and
outer denial becomes visible — not because the dāʿī has argued the interlocutor into a
corner, but because the interlocutor's own inner life has been allowed to speak. When that
disjunction surfaces, do not press. Leave it present.

## Key Questions in the Maieutic Mode

- "When you face something you can only call beautiful — what are you responding to?"
- "When you feel genuine moral obligation — not social pressure, but the categorical 'I must
  not' — what do you take that to be?"
- "What do you make of the moments when recognition of something larger than yourself arises
  without your choosing it?"
- "What is the difference between the universe being indifferent and your experience feeling
  as though it is not?"

**Connection:** R2 (`references/tactics/R2-the-reminder.md`) is the tactic-level version of the same
move. P4 is the sustained procedure; R2 is the single-exchange deployment.

## Failure Conditions

Do not deploy P4 when there is no evidence that recognition is near the surface. If the
interlocutor is simply asking for information, presenting a clean objection, or operating
from an unexamined criterion, the right route is P2, P3, R1, E2, DO, RT, or another matched
owner.

P4 fails when questioning becomes a trap, a cross-examination, or a disguised argument. It
also fails when the practitioner presses the interlocutor to verbalize recognition after it
has surfaced. The procedure is meant to let the interlocutor notice what is already present;
turning that moment into a demand for concession corrupts the mode.

If grief-primary, identity-performance, or relational harm governs, P7 Stop 1 or Stop 3
precedes P4. If recognition is not available after bounded questioning, do not force the
read; mark the case underdetermined or route toward P1, F3, or the relevant intellectual
owner depending on the refreshed signal.

## IR-Visible Consequences

When P4 is active, the IR should mark recognition-elicitation as the current procedure and
track `recognition_strength` as weak, medium, strong, or not-yet-visible. Argumentative and
doctrinal content should be recorded in `held_material` while the question-space is open.

If recognition surfaces at medium or strong strength, P7 Stop 2 governs the current pass:
stop, leave at most one live question, and refresh before any further content. If no
recognition surfaces and the questioning basis remains thin, P7 Stop 4 may govern rather
than permitting more maieutic pressure.

## Minimal-Pair Discriminators

P4 vs. R2: R2 is a single reminder-tactic; P4 is the sustained procedure when multiple
careful questions are needed and the register permits them.

P4 vs. P1: choose P4 when recognition appears present but suppressed; choose P1 when the
conditions for recognition themselves must be restored over time.

P4 vs. P2: choose P4 when objection-language is secondary to suppressed recognition; choose
P2 when the objections remain honest critical burdens that should be mapped.

P4 vs. M3/V5: M3 probes an orphaned intuition; V5 directs attention to signs. P4 governs the
questioning posture that may use such material only if it serves recognition rather than
argument accumulation.

## Hold/Release Discipline

Hold assertions, doctrinal explanations, and cumulative proof while the maieutic space is
open. Release only one question or one brief reflection at a time. The release signal is not
that the practitioner sees the next clever question; it is that the interlocutor's answer
reveals a live path that V1 can refresh.

When recognition appears, stop pressing. If the recognition is weak, leave it present without
forcing a conclusion. If it is medium or strong, record the strength and let P7 Stop 2 govern
the boundary.

## Anti-Pattern Guard

The primary misuse is Socratic domination: using questions to corner rather than to midwife.
If the questions are designed to make the practitioner win, P4 has already failed. The guard
is whether the question creates space for the interlocutor's own recognition, not whether it
sets up the next answer.
