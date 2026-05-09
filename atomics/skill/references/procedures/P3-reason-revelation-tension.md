---
id: P3-reason-revelation-tension
module_class: procedure
canonical_path: skill/references/procedures/P3-reason-revelation-tension.md
contract_version: "0.3.1.0"
load_when:
  - intellectually serious interlocutor stuck on perceived fundamental conflict between rational/scientific standards and religious belief
  - often combined with kalāmic interlocutor profile (NS-6, NS-10)
companions:
  - V2-reconstituting-reason
  - F1-supra-vs-antirational
routing_effects:
  - audits the operative conception of reason before revelation is reinterpreted or defended
  - holds first-order doctrinal content until the alleged conflict is precisely typed
emits:
  - reason_category
  - upstream_findings
  - what_is_withheld_and_why
blocks:
  - conceding a contaminated conception of reason as neutral reason
  - fideistic retreat from reason/revelation coherence
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

# P3 — Resolving the Reason-Revelation Tension

**For:** Intellectually serious interlocutors stuck on a perceived fundamental conflict
between rational/scientific standards and religious belief. The most common form of serious
contemporary skepticism among educated people. Often combined with the kalāmic interlocutor
type.

**Key insight:** The perceived conflict is almost always bidʿī ʿaqlī operating at the
foundational level — a historically conditioned conception of reason mistaken for reason as
such. The procedure dissolves the conflict at the epistemological level rather than surviving
it by reinterpreting revelation to accommodate an unexamined "reason."

## Steps

**1. Articulate the conflict precisely.**
What specifically does the interlocutor's conception of "reason" say that theistic belief
conflicts with? Many apparent conflicts evaporate under examination. Do not grant the conflict
until its specific form is established.

**Operator floor: proof-status triage.**
The phrase "reason contradicts revelation" is not typed enough to route. Classify the two
alleged proofs before any doctrinal content lands:

| Claimed proof-status cell | P3 operation | Release result |
|---|---|---|
| `qati/qati` | Refuse real contradiction; locate misclassification, invalid inference, or semantic error. | No global tribunal; next move is the local error. |
| `qati/zanni` | The decisive proof governs regardless of whether it is rational or transmitted. | Hold the speculative side for audit. |
| `zanni/zanni` | Require tarjih between speculative proofs. | No universal reason/revelation hierarchy is licensed. |

P3 has not landed if it merely says "sound reason and revelation agree" while leaving the
alleged proof status untyped.

**Operator floor: verification-consistency.**
If the interlocutor says reason validates the Messenger or revelation in general, but then
reserves an indefinite veto over every transmitted content item, expose the witness-reversal:
the validating reason cannot both certify the source and keep every report hostage to an
unbounded future "rational" objection. The exit options are bounded: deny prophetic authority
openly, name a local authenticity/semantic/proof-strength issue, or hold a speculative premise
for audit. Do not let a general verifier become an unlimited veto.

**Operator floor: local issue decomposition.**
A reason/revelation slogan may hide four different local burdens:

- transmission or authenticity;
- semantic indication;
- proof strength;
- speculative philosophical premise.

Route to the local owner when the burden is local: V10/RT for transmission, M9/definition
discipline for semantic claims, proof-method-audit for proof grammar, and
perfection-criterion-usurpation when a perfection premise governs.

**2. Examine the conception of reason (V2).**
Where did the operative conception come from? Is it itself self-evident? Was it always
dominant? Can it establish itself by its own standards? Scientism cannot validate itself
scientifically. The contamination may also arrive in theological form: a narrow necessary-
knowledge criterion, a demand that all belief about God begin with discursive proof, or a prior
metaphysical model of perfection presented as "reason itself." Deploy
`references/techniques/V2-reconstituting-reason.md`.

**3. Apply the cross-cultural check (E4 with tawātur grounding).**
Does the interlocutor's conception of reason require that virtually all human beings in all
cultures and times have been fundamentally wrong about the most basic features of their
experience? If so, the cost of that conception is very high — and the tawātur fiṭrī argument
shows why that cost is not payable. Deploy `references/tactics/E4-cross-cultural-check.md`.

**4. Show the tradition does not ask reason to be abandoned.**
"You are using a historically contingent and self-undermining conception of reason. ʿAql
ṣarīḥ — genuine reason, operating without distortion — and genuine revelation, properly
understood, are fully corroborative. Never 'believe despite what reason says' — always 'you
are using a deficient conception of reason.'"

Sound reason is not exhausted by one modern method or one narrowed scholastic criterion.
Fiṭrī recognition, sound testimony, tawātur, and valid naẓar each have their proper place.
The conflict dissolves when historically conditioned filters stop posing as reason itself.

**5. Return to the positive.**
Once the conceptual obstacles are cleared, return to the direct case: the convergence of the
three knowledge sources, the āyāt, and the invitation to attend to what the fiṭrah itself
says. Deploy V5 (`references/techniques/V5-directing-attention-signs.md`) calibrated to this person.

## Failure Conditions

Do not deploy P3 for every scientific, philosophical, or evidential objection. P3 is for a
framework-level conflict claim: reason, science, or a prior theological rationalism being
treated as a tribunal over revelation. If the live issue is one local proof, one textual
claim, or one moral objection, route to P2, DO, RT, V10, or the matched tactic instead.

P3 fails when the practitioner concedes the interlocutor's conception of reason and then
tries to save revelation by accommodation. It also fails in the opposite direction: retreating
into "faith despite reason" when the procedure's point is that sound reason and genuine
revelation are corroborative once corrupted reason is disambiguated.

If the conflict is really a school-specific kalamic burden, load the kalamic interlocutor
diagnostic and the relevant sound-reason material rather than treating all rational tension
as modern scientism. If grief, identity-performance, or relational harm is primary, P7 fires
before P3 content can be released.

P3 fails when it treats a local semantic, transmission, proof-strength, or perfection-premise
issue as a global reason/revelation conflict. It also fails when it lets "reason validates
revelation" become an unbounded veto over any revealed content the interlocutor dislikes.

## IR-Visible Consequences

When P3 is active, the IR should mark a framework-level reason/revelation tension and record
the operative `reason_category`: sound reason, corrupted reason, pseudo-neutral reason, or
inherited reason-filter. `upstream_findings` should name the tribunal if one is present:
scientism, historicist public-warrant restriction, narrow kalamic proof condition,
perfection-criterion import, or another identified standard.

First-order doctrinal defense, revelation reinterpretation, and proof accumulation remain
in `held_material` until the conception of reason is articulated and audited. `matched_modules`
normally includes P3 with V2 and, where the issue is faith-as-irrational rhetoric, F1. E4 and
V5 are downstream releases only after the reason-filter is no longer controlling admissibility.

When proof-status triage governs, `upstream_findings` should name the governing cell
(`qati/qati`, `qati/zanni`, or `zanni/zanni`) or state that the conflict is untyped and
therefore held. When verification-consistency governs, `upstream_findings` should name
`tribunal-installation` or `verifier-veto`, and `what_is_withheld_and_why` should identify
the held doctrinal content.

## Minimal-Pair Discriminators

P3 vs. V2: V2 is the technique for reconstituting a corrupted reason-concept; P3 is the
larger procedure when that corruption is specifically framed as reason versus revelation.

P3 vs. F1: F1 corrects the claim that faith is anti-rational or supra-rational; P3 governs
the broader conflict structure where a whole standard of reason is being placed over
revelation.

P3 vs. P2: choose P3 when all objections depend on one alleged rational tribunal; choose P2
when several objection families must be mapped before their order is known.

P3 vs. NS-6/NS-10 handling: choose the NS route when the decisive issue is school-specific
burden, necessary-knowledge priority, or attribute ontology; choose P3 when the pressure is
the general reason/revelation conflict.

Global tribunal vs. local issue: choose P3 when "reason" is claiming jurisdiction over
revelation as such; choose M9/definition discipline for local semantic indication, V10/RT for
transmission/authenticity, and proof-method-audit for a local proof-strength challenge.

Proof-status minimal pair: same phrase, "reason contradicts revelation"; if the conflict is
untyped, P3 must classify before content. If the user names a local report, word, or premise,
P3 either remains secondary or holds while the local owner leads.

## Hold/Release Discipline

Hold revelation reinterpretation, apologetic proof-stacking, and positive-sign deployment
until the alleged conflict has been specified. Release only the audit of the reason-concept
first. If the standard proves self-undermining or historically contingent, release a bounded
frame-clearing move and refresh before moving to E4, V5, or case-library content.

Do not loop the same reason-audit if the interlocutor acknowledges the standard was not
neutral. That acknowledgment is a release signal for the next matched burden, not permission
to keep pressing the same point.

Hold first-order content when the alleged conflict is unclassified by proof status. Release
only the operator trace until the cell is named or the issue decomposes into a local owner.
If the interlocutor supplies a local authenticity, semantic, or speculative-premise claim,
release that owner instead of continuing a global P3 frame.

## Anti-Pattern Guard

The central anti-pattern is accommodation-as-cure: altering revelation to satisfy an
unexamined tribunal while calling the result rational engagement. The paired danger is
fideist retreat. P3 must neither surrender revelation to corrupted reason nor abandon reason;
it restores the order between sound reason and revelation.

Additional v0.3.2.0 anti-patterns:

- Reason/revelation slogan: declaring harmony without classifying the alleged proofs.
- Verifier-veto collapse: reason validates revelation, then becomes an unlimited veto over it.
- Certainty cosplay: a contested school premise is treated as reason itself.
- Theodicy dump: a logical problem-of-evil claim receives wisdom lists before hidden premises
  and necessity status are exposed.
