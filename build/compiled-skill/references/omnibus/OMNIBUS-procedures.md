<!--
GENERATED FILE.
Do not edit directly.
Canonical source lives under skill/.
Regenerate with tools/build_compiled_runtime.py.
-->

# OMNIBUS-procedures

This generated bundle is a runtime read view. Section presence does not imply active dispatch.


## SOURCE MODULE: procedures-index

<!-- SOURCE: skill/references/procedures/INDEX.md -->
<!-- MODULE_ID: procedures-index -->
<!-- MODULE_CLASS: governance -->
<!-- CANONICAL_PATH: skill/references/procedures/INDEX.md -->
<!-- SOURCE_SHA256: cf5ffeae5a4333c1884d10c2efab92d0e4c413b905caacfdfce10eec9a5c40ba -->

---
id: procedures-index
module_class: governance
canonical_path: skill/references/procedures/INDEX.md
contract_version: "0.2.3.0"
load_when:
  - selecting a procedure after V1 case-classification
catalogue_registered: false
---

# Procedures — Index

Procedures are multi-stage engagement frameworks. Use them when the case cannot be handled
well by a single tactic or technique.

## Selection Rules

- Start with V1 before choosing a procedure, and use M5 inside V1's triage phase.
- Procedures govern sequencing. They do not cancel the need for tactic and technique discipline.
- If the case only needs one move, do not escalate it into a procedure.

## Procedures

| File | For | Use when | Do not use when | Typical pairings |
|------|-----|----------|-----------------|-----------------|
| `references/procedures/P1-fitrah-restoration.md` | Restoration-first cases | The fiṭrah is significantly suppressed and the main work is clearing conditions for recognition | The case is still a clean, truth-oriented intellectual exchange | V2, V5, F3 |
| `references/procedures/P2-objection-mapping.md` | Objection batteries | A cluster of objections must be separated and sequenced | The case is really one upstream criterion problem in disguise | V2, case-library DO files |
| `references/procedures/P3-reason-revelation-tension.md` | Framework conflict | Reason/science, or a prior theological-rational filter, is being posed as fundamentally opposed to revelation | The case is local rather than framework-level | V2, E4, `diagnostics/kalamic-interlocutor.md` |
| `references/procedures/P4-maieutic.md` | Inkār cases | Recognition seems present but suppressed | The case is still purely classificatory or grief-primary | V5 |
| `references/procedures/P5-already-believing.md` | Internal strengthening | A believer's conviction is shallow, inherited, or fragile | The case is not primarily internal to belief formation | E3, F3 |
| `references/procedures/P6-universal-aqidah-principle.md` | Neutrality challenge | The interlocutor claims to have no worldview or no righteous guidance | The case already acknowledges a substantive worldview | M7, M8 |
| `references/procedures/P7-restoration-stops.md` | Hard stop rails | Any case where premature argument, forced read, or relational-register bypass is a risk; mandatory when grief-primary, identity-performance, or hawā/gharaḍ are confirmed; mandatory when the case basis is insufficient for confident diagnosis | Only when a stop trigger has been identified; not a default opening procedure | heuristics.md (principles), mixed-case-handling.md (underdetermined), discourse-orientation.md (register) |

## Sequencing Notes

- P1 is usually upstream of other procedures because it restores conditions of apprehension.
- P2 often hands off to P4 when objection-generation accelerates rather than converges.
- P3 often precedes P2 because framework conflict can invalidate all first-order engagement.
- P6 is often an opening move establishing that a supposedly neutral stance is still an ʿaqīdah.
- P7 is not a sequenced procedure — it is a set of hard stop rails. When a stop trigger fires, P7 governs regardless of which other procedure is active. P7 constraints are not suspended by P2 or P3 engagement.

<!-- END_SOURCE: procedures-index -->


## SOURCE MODULE: P1-fitrah-restoration

<!-- SOURCE: skill/references/procedures/P1-fitrah-restoration.md -->
<!-- MODULE_ID: P1-fitrah-restoration -->
<!-- MODULE_CLASS: procedure -->
<!-- CANONICAL_PATH: skill/references/procedures/P1-fitrah-restoration.md -->
<!-- SOURCE_SHA256: 7fca134807b330417fd5ccbc54360263f43f39512275bb49c2e2abc7808df658 -->

---
id: P1-fitrah-restoration
module_class: procedure
canonical_path: skill/references/procedures/P1-fitrah-restoration.md
contract_version: "0.2.3.0"
load_when:
  - interlocutor's fiṭrah is significantly suppressed through prolonged iʿtiqādāt mawrūtha or ʿāda combined with volitional entrenchment
  - goal is to create conditions for fiṭrah recovery, not to win an argument
companions:
  - V2-reconstituting-reason
  - V4-contamination-identification
  - V5-directing-attention-signs
  - M4-grief-register
  - P7-restoration-stops
routing_effects:
  - establishes a staged restoration path before first-order content is released
  - holds argument deployment until trust, filter-clearing, and register conditions permit release
emits:
  - restoration_target
  - what_is_withheld_and_why
blocks:
  - proof-dumping before trust and filter conditions are established
  - treating filter-loosening as full alignment
output_shapes:
  - bounded-single-pass
  - held-pending-upstream
layer_constraint: layer-b-governed
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

# P1 - Fitrah Restoration

**For:** Interlocutors whose fitrah is significantly suppressed, typically through prolonged
`i'tiqadat mawrutha` or `ada` combined with volitional entrenchment (`hawa` or `gharad`).
The goal is not to win an argument but to create the conditions under which the fitrah can
resume its natural function. This procedure is not primarily argumentative; it is
spiritual-epistemic.

## Stages

**1. Establish genuine trust.**
Not a preliminary; foundational. An interlocutor who does not trust the da'i's sincerity
will not be honest, and honest inquiry is the only kind that leads anywhere. This stage may
require sustained engagement with no argumentative agenda at all. Argumentation presupposes
good faith; the da'i must build that first.

**2. Identify the primary deformation.**
Using `references/diagnostics/seven-deformations.md`, determine which mechanism is primarily
suppressing the fitrah. Name it, without accusation and without condescension, if the trust
established in Stage 1 has produced genuine candor from the interlocutor. If the barrier is
`gharad` or `hawa`, no intellectual content will help until this is acknowledged.

**3. Clear conceptual obstacles first.**
If `i'tiqadat mawrutha` or `ada` is functioning as a filter, deploy V2
(`references/techniques/V2-reconstituting-reason.md`) and V4
(`references/techniques/V4-contamination-identification.md`) before presenting any
first-order content. There is no point presenting evidence to a mind that has
pre-committed to not counting it. The filter must be loosened before ayat can land.

Filter-loosening is real progress, but it is not yet full alignment. Distinguish:
- tribunal loosened
- frame cleared enough for examination
- positive recognition plus willingness to inhabit the restored order

Do not treat the first as though it already guarantees the third.

**4. Direct attention to signs.**
Once the filter is loosened, use V5
(`references/techniques/V5-directing-attention-signs.md`), calibrated to this particular
person's sensibilities. Signs that may move a scientist are not the same as signs that may
move someone in grief or a morally serious person. Select with care. Frame non-coercively.
Be patient.

If another live burden is now governing, especially transmission, authority, or an explicitly
requested inferential question, clear that burden first. V5 is not an automatic post-V2 dump;
it is the next move only when refreshed case-state says it is the right restorative release.

**5. Introduce spiritual practice.**
Suggest, gently and without pressure, that the practices which open direct awareness of God
(attentive reflection, moral discipline, stillness, dhikr) are worth trying as inquiry rather
than as devotion. The tradition is explicit that the fitrah is kept intact through spiritual
practice. Since the qalb cannot grasp the evidence for God without spiritual attunement,
practical orientation toward God creates epistemic access. Introduce it as a recommendation
to investigate, not a demand to commit.

**6. Consolidate and protect.**
Once something opens in the interlocutor, it is fragile. Social pressure, intellectual
environment, and habitual patterns of thought can re-suppress what has become available.
Ongoing conversation, grounding in the tradition, and community all serve consolidation.
The opening is not the end; it is the beginning of a more vulnerable stage.

**Governed continuation note:** P1 is staged restoration, not indefinite momentum. After each
landed move, refresh the case-state. Continue only if the restoration target is still unmet
and no stop, register-hold, or semantic gate blocks the next step. A fresh differentiating
signal may arise in a later reply or within the same message through an accompanying
proposition or entailment; if not, stop with the live question left present.

---

**7. Suspend active engagement - reluctantly, conditionally, and without closing the door.**

This stage is invoked only after Stages 1-6 have been genuinely exhausted across sustained
engagement, and only when all three of the following conditions are confirmed:

*Condition 1:* Discourse orientation has been stably non-truth-seeking across multiple
exchanges, not mixed or fluctuating, but consistently identity-performance, autotelic
stimulation, or conjecture without anchor with no movement toward genuine inquiry.

*Condition 2:* No evidence of fitrah accessibility has appeared in any exchange: no
involuntary response to signs, no moments of recognition however faint, no existential
opening even in states of vulnerability.

*Condition 3:* Either (a) direct evidence of cognitive inaccessibility that places the
person outside normal discursive engagement, or (b) compound deformations so deeply
entrenched and mutually reinforcing that every matched instrument has been tried and none
has produced a new differentiator or any sign of live purchase.

**What this stage is not:** It is not a verdict on the interlocutor's state before God.
It is not a permanent conclusion about their fitrah's accessibility. It is not a withdrawal
of care. The da'i's obligation is bayan, clear conveyance, not the production of
recognition. Recognition belongs to God alone. The obligation is discharged when the means
have been genuinely exhausted and the question has been left clearly present.

**What this stage requires of the da'i:** Leave the door open explicitly. Do not end the
engagement with a verdict; end it with a question left alive. The fitrah continues to work
in the intervals. Many have been reached by what was planted long after the planting and in
the da'i's absence. The suspension is of *active instrumental engagement*, not of the
relationship or of hope.

**For direct cognitive inaccessibility specifically:** The correct posture is compassion
without argumentative pressure. The tradition is clear that accountability is calibrated to
what a person actually has access to (`hujjah`). Engage humanly; do not press epistemically,
and do not turn the suspension of pressure into a verdict on the person's standing before God.

## Failure Conditions

Do not deploy P1 merely because the case is difficult, slow, or emotionally textured. If the
interlocutor is still in a stable truth-seeking intellectual exchange, use P2 or the matched
case-library owner rather than replacing the live objection with a broad restoration arc.

P1 fails when the practitioner treats trust-building as a preface to a hidden argument dump,
names a deformation before candor has been earned, or reads a loosened tribunal as full
alignment. A softened inherited filter permits the next bounded move; it does not prove that
recognition, willingness, or practice-readiness has arrived.

If grief-primary or relational injury is governing, P7 Stop 1 or Stop 3 fires before P1 can
advance beyond presence and repair. If the case is non-contractual, P7 Stop 5 limits P1 to a
single humane opening rather than a full staged procedure. If the interlocutor remains
truth-seeking and focused on a defined objection, P1 should yield to P2, P3, DO, RT, or a
matched tactic.

## IR-Visible Consequences

When P1 is active, the IR should mark the response as restoration-first and record the
current restoration stage: trust-building, deformation-identification, filter-clearing,
sign-attention, practice-invitation, consolidation, or conditional suspension. The matched
modules normally include P1 plus the relevant companion stage, not the whole companion set at
once.

First-order proofs, DO entries, RT entries, and V5 signs remain in `held_material` until the
stage that lawfully releases them. `what_is_withheld_and_why` should name the blocker in
stage language: trust not established, primary deformation not identified, filter not loosened,
register not clear, or suspension conditions not exhausted. The output shape is
`held-pending-upstream` while the stage blocker governs and `bounded-single-pass` once a
single stage move is ready.

## Minimal-Pair Discriminators

P1 vs. P2: choose P1 when apprehension itself is suppressed and staged restoration is needed;
choose P2 when the live burden is a cluster of objections that can still be mapped and
sequenced intellectually.

P1 vs. P4: choose P1 when access to recognition is broadly veiled and must be restored over
time; choose P4 when recognition appears near the surface and careful questioning can let the
interlocutor notice it.

P1 vs. P5: choose P1 for suppressed or blocked fitrah regardless of formal affiliation; choose
P5 when the person already believes but needs inherited belief strengthened into examined
conviction.

P1 vs. F3: choose P1 for the whole restoration procedure; choose F3 only for the specific
practice-as-epistemic-access tactic once openness and stage readiness are present.

## Hold/Release Discipline

Hold argumentative content until trust and the relevant filter-clearing condition have been
met. Hold V5 until the case-state shows that signs can land without being pre-filtered by the
old tribunal. Hold practice invitation until it can be framed as inquiry rather than pressure.

Release only the next stage-specific move, then refresh V1. Do not continue because the
procedure has more stages available. Stage 7 releases only when its three exhaustion
conditions are actually satisfied across sustained engagement; otherwise it remains held as a
serious last-resort posture, not a rhetorical exit.

## Anti-Pattern Guard

The main misuse is Restoration-First Default: diagnosing every hard case as suppressed fitrah
and bypassing the precise objection, source-pressure, grief-register, or criterion problem
actually present. The guardrail is stage evidence. If the IR cannot name which P1 stage is
active and what condition releases the next move, P1 is not yet lawfully deployed.

<!-- END_SOURCE: P1-fitrah-restoration -->


## SOURCE MODULE: P2-objection-mapping

<!-- SOURCE: skill/references/procedures/P2-objection-mapping.md -->
<!-- MODULE_ID: P2-objection-mapping -->
<!-- MODULE_CLASS: procedure -->
<!-- CANONICAL_PATH: skill/references/procedures/P2-objection-mapping.md -->
<!-- SOURCE_SHA256: 1456d708231aac700b35f1891ac1cedbe57c4e6cd3245114397915d57c19e28d -->

---
id: P2-objection-mapping
module_class: procedure
canonical_path: skill/references/procedures/P2-objection-mapping.md
contract_version: "0.2.3.0"
load_when:
  - interlocutor presenting a battery of intellectual objections
  - engagement is primarily critical rather than existential
companions:
  - V1-diagnostic
  - M5-deformation-triage
routing_effects:
  - separates objection batteries into second-order and first-order burdens
  - holds first-order answers until the governing framework burden is mapped
emits:
  - matched_modules
  - what_is_withheld_and_why
blocks:
  - answering objections in arrival order when framework-level objections are live
  - treating accelerating objection-generation as clean intellectual convergence
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

# P2 - Objection Mapping

**For:** Interlocutors presenting a battery of intellectual objections; engagement primarily critical rather than existential. Start with V1 and use M5 (`references/tactics/M5-deformation-triage.md`) inside its triage phase - apparent intellectual objections frequently conceal volitional barriers.

## Structure

**1. Complete taxonomy of objections.**
Before addressing any objection, map all of them. Distinguish rigorously:

- *Second-order objections* (against the epistemological framework - what counts as evidence,
  what counts as rational belief, what the conditions for knowledge are): address *first*.
  First-order content will not land until the framework that would pre-filter it is examined.
  Deploy V2 (`references/techniques/V2-reconstituting-reason.md`) for bidi 'aqli objections.
  A hostile historical-critical frame often lives here: not as neutral data, but as a narrowed
  theory of testimony, admissible causes, and public warrant.

- *First-order objections* (against theistic content - God's existence, divine attributes,
  revelation, scripture, prophecy, the problem of evil): address second. Many dissolve once the
  epistemological framework is clarified. For named objections, load
  `references/case-library/INDEX.md`.

  In Christian doctrinal cases, separate divine-perfection arguments, formal Trinity-coherence
  arguments, and mystery appeals before loading the relevant DO entry.

  In revelation / scripture / final-prophethood cases, separate:
  - revelation as such
  - testimony / transmission
  - textual integrity
  - canon formation
  - specific prophetic credibility
  - moral authority

  Revelation routing is fixed:
  - testimony / manuscript / source claims -> V10 first, then RT-1
  - canon formation / "who chose scripture?" -> V10 first, then RT-2
- Qur'anic preservation / qirāʾāt / manuscript confusion -> V10 first, then RT-3
  - Muslim-internal textual-historical destabilization -> V10 first, then RT-4 and often P5
  - specific prophetic-claim objections -> separate the transmission issue from the prophetic
    claim itself before broader doctrinal rebuttal

**2. Address second-order first, first-order second.**
The sequence is non-negotiable. Attempting to resolve first-order objections before the
second-order framework is cleared is attempting to fill a sieve.

For revelation and transmission cases, "second-order first" often means exposing a hidden theory
of testimony, historical authority, or public warrant before debating any one text. Do not let a
historical-critical frame pose as neutral data if it is really a narrowed epistemology.

**3. What positive engagement looks like after clearing.**
The objection-mapping process, if conducted with genuine attention, reveals something about
the interlocutor: which signs move them, what their existing sensibilities are, what they
have cared about throughout the exchange. Use this. The cleared path is an opening, not a
destination.

What fills it should be calibrated to *this particular person*:
- The scientist who raised fine-tuning objections already cares about cosmological order -
  direct toward that sign (V5 track: cosmological / fine-tuning)
- The moral philosopher who raised the problem of evil already cares about objective value -
  M3 (orphaned intuition probe) and the moral ground of the tradition
- The person whose objections were mostly about suffering - M4 (grief register), which was
  never appropriate while intellectual defenses were up, may now be exactly right
- The believer destabilized by viral manuscript content may now need P5 strengthening more than a
  debate-performance answer

The positive engagement is not a new argument. It is the occasion for the fiṭrah to encounter
what it was always disposed to recognize.

**Caution:** If the pattern of objection generation is accelerating rather than converging,
the barrier is not primarily intellectual. Shift to P1 or P4 (maieutic).

## Failure Conditions

Do not deploy P2 for a single well-formed objection with an obvious owner. A local DO, RT,
V-series, or tactic route should not be inflated into a mapping procedure just because the
practitioner wants a comprehensive answer.

P2 fails when objections are answered in arrival order, when first-order content is released
before the second-order criterion is identified, or when a hidden historical-critical,
scientistic, or moral-tribunal frame is allowed to pose as neutral data. It also fails when
objection multiplication is mistaken for sincere convergence. If the map grows after each
answer rather than narrowing, the case has likely shifted toward P1, P4, F2, or P7 rather
than deeper P2.

If grief-primary, identity-performance, relational harm, or non-contractual inquiry is
governing, P7 constrains the procedure before any taxonomy is surfaced externally. If the
case is fundamentally reason-revelation conflict rather than a mixed objection battery, P3
governs first.

## IR-Visible Consequences

When P2 is active, the IR should record an objection map with at least these buckets:
second-order framework objections, first-order content objections, source/transmission
objections, and affective or volitional signals that are not objections in the strict sense.
`matched_modules` should reflect the ordered sequence, not the whole list as immediately
deployable.

First-order DO and RT material should appear in `held_material` whenever a second-order
burden is upstream. `what_is_withheld_and_why` should name the withheld item and the
framework condition that must clear first, such as testimony theory, evidence criterion,
moral tribunal, source authority, or discourse orientation. The visible output should be one
bounded mapping move or the first lawful upstream engagement, not a full answer to the
entire battery.

## Minimal-Pair Discriminators

P2 vs. V1: V1 classifies the case-state; P2 sequences a confirmed objection battery after
V1 has already opened the routing gate.

P2 vs. P3: choose P2 when multiple objections need taxonomy; choose P3 when the governing
burden is the alleged conflict between reason/science and revelation as such.

P2 vs. direct DO/RT routing: choose direct routing when the objection has one clear owner;
choose P2 when several owners are present and answering one would distort the order.

P2 vs. P1/P4: choose P2 when objections are converging under honest critical engagement;
choose P1 or P4 when the pattern shows suppressed recognition, objection-generation as
avoidance, or a need for staged restoration rather than taxonomy.

## Hold/Release Discipline

Hold all first-order answers until the map is complete enough to identify the upstream
burden. Hold downstream DO/RT modules when a criterion, source-authority, or testimony
standard is controlling their admissibility. Release only the first upstream item in the
sequence, then refresh the case-state.

If one objection is answered and the interlocutor shifts to a new objection from a different
bucket, do not automatically release the next answer. Re-map the shift. If the shift reveals
acceleration rather than convergence, stop P2 and route to the register, volitional, or
restoration owner.

## Anti-Pattern Guard

The principal misuse is whack-a-mole apologetics: treating a battery as a queue of content
requests. P2 exists to prevent that. If the output does not show which objection is upstream
and which material is held, the procedure has collapsed into answer-stacking.

<!-- END_SOURCE: P2-objection-mapping -->


## SOURCE MODULE: P3-reason-revelation-tension

<!-- SOURCE: skill/references/procedures/P3-reason-revelation-tension.md -->
<!-- MODULE_ID: P3-reason-revelation-tension -->
<!-- MODULE_CLASS: procedure -->
<!-- CANONICAL_PATH: skill/references/procedures/P3-reason-revelation-tension.md -->
<!-- SOURCE_SHA256: bbfcb2107fb7268daf23e8bb83a88c2ed8c2dcf65896789f3312cffee40d9f5f -->

---
id: P3-reason-revelation-tension
module_class: procedure
canonical_path: skill/references/procedures/P3-reason-revelation-tension.md
contract_version: "0.2.3.0"
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

## Hold/Release Discipline

Hold revelation reinterpretation, apologetic proof-stacking, and positive-sign deployment
until the alleged conflict has been specified. Release only the audit of the reason-concept
first. If the standard proves self-undermining or historically contingent, release a bounded
frame-clearing move and refresh before moving to E4, V5, or case-library content.

Do not loop the same reason-audit if the interlocutor acknowledges the standard was not
neutral. That acknowledgment is a release signal for the next matched burden, not permission
to keep pressing the same point.

## Anti-Pattern Guard

The central anti-pattern is accommodation-as-cure: altering revelation to satisfy an
unexamined tribunal while calling the result rational engagement. The paired danger is
fideist retreat. P3 must neither surrender revelation to corrupted reason nor abandon reason;
it restores the order between sound reason and revelation.

<!-- END_SOURCE: P3-reason-revelation-tension -->


## SOURCE MODULE: P4-maieutic

<!-- SOURCE: skill/references/procedures/P4-maieutic.md -->
<!-- MODULE_ID: P4-maieutic -->
<!-- MODULE_CLASS: procedure -->
<!-- CANONICAL_PATH: skill/references/procedures/P4-maieutic.md -->
<!-- SOURCE_SHA256: 0bcd20269f80e0a10cfa828fabea98cff77ae7c9e587e56b87998e9a3d3f1280 -->

---
id: P4-maieutic
module_class: procedure
canonical_path: skill/references/procedures/P4-maieutic.md
contract_version: "0.2.3.0"
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

<!-- END_SOURCE: P4-maieutic -->


## SOURCE MODULE: P5-already-believing

<!-- SOURCE: skill/references/procedures/P5-already-believing.md -->
<!-- MODULE_ID: P5-already-believing -->
<!-- MODULE_CLASS: procedure -->
<!-- CANONICAL_PATH: skill/references/procedures/P5-already-believing.md -->
<!-- SOURCE_SHA256: f8d7a73f3bcc71ad522ebe9d271445339ae1be4b954d6f9016a34ff26bf02a42 -->

---
id: P5-already-believing
module_class: procedure
canonical_path: skill/references/procedures/P5-already-believing.md
contract_version: "0.2.3.0"
load_when:
  - believer whose belief is shallow, untested, or held by taqlīd
  - belief fragile under pressure; moving from inherited assumption to examined conviction
companions:
  - V11-taqlid-transition
  - F3-practice-epistemic-access
  - P7-restoration-stops
routing_effects:
  - moves inherited or fragile belief toward examined conviction without debate habituation
  - holds reassurance or rebuttal until the article of faith and source of pressure are specified
emits:
  - restoration_target
  - matched_modules
  - what_is_withheld_and_why
blocks:
  - generic encouragement when a specific article of faith is under pressure
  - panic-answering viral source claims before V10 source vetting
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

# P5 - Working with the Already-Believing

**For:** Believers whose belief is shallow, untested, or held by taqlīd - inherited without
genuine examination and therefore fragile under pressure. The procedure moves belief from
inherited assumption to genuine, examined conviction without turning the person into a permanent
debater.

Epistemic importance: belief held by taqlīd is not epistemically stable - it is arrived at by
chance and will not survive serious intellectual pressure. The same tradition that asks genuine
investigation of skeptics asks it of believers.

## Stages

**1. Honest assessment of foundations.**
What is their belief actually based on - evidence and experience, or habit and social belonging?
Neither is shameful, but only the former is epistemically stable. The goal is to distinguish
taqlīd from taḥqīq (genuine investigation). This requires gentleness: the person has been
faithful; the issue is not fidelity but epistemic grounding.

**2. Name the article of faith and source of pressure precisely.**
Do not strengthen "belief in general." Ask which article is actually thin, inherited, or under
pressure: God's existence, revelation, the Qur'an, final prophethood, divine attributes,
afterlife, or trust in the tradition's transmitters and teachers. Then classify the pressure:
text-history, moral recoil, philosophical objection, authority fatigue, betrayal, or panic after
viral material. Examined conviction grows by specificity, not by vague encouragement.

**3. Vet sources before answering them.**
If the believer is being shaken by clips, manuscripts, screenshots, or textual-history claims,
run V10 (`references/techniques/V10-transmission-content-vetting.md`) before content rebuttal.
Move from "this scared me" to "what kind of source is this, what does it actually show, and what
authority does it really carry?" Use RT-1 through RT-4 when the pressure is revelation,
transmission, canon, or preservation related. This is often the point where taqlīd begins to
become taḥqīq.

**4. Engage objections by taxonomy, not by panic.**
Once the source-pressure is classified, engage the strongest objections directly and honestly.
Use `references/case-library/INDEX.md` DO-1 through DO-14 for doctrinal cases and RT-1 through
RT-4 for revelation / transmission cases. Keep the classes separate. A believer whose manuscript
fear is answered with a Trinity speech, or whose moral recoil is answered with a canon defense,
is not being strengthened but overwhelmed.

**5. Broaden the evidential base into examined convergence.**
The grounds for belief are wider than inherited assumption: cross-cultural convergence
(tawātur fiṭrī), cosmological and fine-tuning signs, moral experience and orphaned intuitions,
scriptural testimony and disciplined transmission, and direct experience of God in sincere
practice all contribute. Move the believer from a single inherited channel to multi-channel,
examined warrant. Deploy E3 (`references/tactics/E3-cumulative-case.md`) where needed.

**6. Connect examined conviction to practice.**
F3 (`references/tactics/F3-practice-epistemic-access.md`) remains a consolidation stage, not a
substitute for source-vetting or objection work. Once the article of faith has been clarified and
the strongest pressures have been answered proportionally, help the believer inhabit the truth in
practice. Deeper examined conviction produces more sincere practice, and sincere practice keeps
the channels of the fiṭrah clear.

## Failure Conditions

Do not deploy P5 merely because the interlocutor is Muslim or religiously affiliated. P5 is
for fragile, inherited, shallow, or pressure-tested belief that needs strengthening into
examined conviction. If the person is presenting as a non-believer, skeptic, or external
critic, route through the relevant NS, DO, RT, or procedure owner first.

P5 fails when the practitioner strengthens "belief in general" without identifying the
specific article under pressure. It also fails when reassurance replaces source-vetting, when
viral textual-history material is answered before V10 classifies it, or when the believer is
trained into permanent debate-consumption rather than stable conviction and practice.

If the believer's distress is grief-primary, betrayal-based, or authority-wound driven, P7
Stop 1 or Stop 3 governs before strengthening content. If the live burden is transmission,
V10 and RT govern before broad encouragement. If the issue is taqlid as such, V11 is the
companion transition and should not be skipped.

## IR-Visible Consequences

When P5 is active, the IR should mark an internal-strengthening route and identify the
article of faith under pressure: God's existence, revelation, Qur'an, final prophethood,
attributes, afterlife, transmission, or trust in tradition. It should also record the pressure
type: text-history, moral recoil, philosophical objection, authority fatigue, betrayal, or
panic after viral material.

Generic reassurance, apologetic breadth, and practice-consolidation remain in `held_material`
until the article and pressure type are specified. `matched_modules` may include V11, V10,
RT, DO, E3, or F3, but only the next lawful owner is released. Output may be
`recursive-traversal-permitted` only through refreshed case-state and P7 stop discipline, not
through anxiety momentum.

## Minimal-Pair Discriminators

P5 vs. P1: choose P5 when belief is present but shallow or destabilized; choose P1 when the
conditions of fitrah-recognition are broadly suppressed and must be restored.

P5 vs. P2: choose P5 when objections arise inside fragile belief and the goal is examined
conviction; choose P2 when the exchange is primarily critical objection-mapping.

P5 vs. V11: V11 governs the taqlid-to-tahqiq transition as a technique; P5 governs the
whole internal-strengthening procedure around a believer's concrete pressure.

P5 vs. RT-4: RT-4 owns Muslim-internal textual-historical destabilization; P5 owns the wider
pastoral and epistemic strengthening path after that pressure has been typed.

## Hold/Release Discipline

Hold reassurance until the specific article of faith is named. Hold rebuttal until the source
and pressure type are vetted. Hold F3 practice-consolidation until the strongest live pressure
has been addressed proportionally; otherwise practice is misused as avoidance.

Release one strengthening move at a time: source-vetting, objection classification, strongest
answer, evidential broadening, or practice consolidation. After each landed move, refresh V1
and check P7 before continuing. Do not make the believer dependent on endless new answers.

## Anti-Pattern Guard

The main misuse is panic-apologetics: feeding the believer a stream of answers that treats
anxiety as a content deficit. P5 should produce examined stability, not a permanent need for
the next rebuttal. The guardrail is specificity plus consolidation: named article, named
pressure, lawful next owner, then practice and steadiness.

<!-- END_SOURCE: P5-already-believing -->


## SOURCE MODULE: P6-universal-aqidah-principle

<!-- SOURCE: skill/references/procedures/P6-universal-aqidah-principle.md -->
<!-- MODULE_ID: P6-universal-aqidah-principle -->
<!-- MODULE_CLASS: procedure -->
<!-- CANONICAL_PATH: skill/references/procedures/P6-universal-aqidah-principle.md -->
<!-- SOURCE_SHA256: 50e9a1bd3d9bf3dc0644698ab17a3c6c039e501ba79a4ded4ae36be9003682c8 -->

---
id: P6-universal-aqidah-principle
module_class: procedure
canonical_path: skill/references/procedures/P6-universal-aqidah-principle.md
contract_version: "0.2.3.0"
load_when:
  - interlocutor claims no religion, no worldview, no ʿaqīdah
  - the claim that there is no righteous guidance asserted as a position
  - skepticism presented as a neutral non-position
  - pseudo-neutral slogan ("I just follow the evidence") functioning as worldview-deflection
routing_effects:
  - establishes the interlocutor has a position before proceeding to its content
companions:
  - M1P-performative-self-refutation
  - V2-reconstituting-reason
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
---

# P6 - The Universal ʿAqīdah Principle

**For:** Interlocutors who claim to have no religion, no worldview, no ʿaqīdah; or who
assert "there is no righteous guidance"; or who present their skepticism as a neutral
non-position. This procedure establishes that the interlocutor has a position before
examining it.

---

## The Logical and Epistemological Claim

"I have no religion" is itself a religious claim. More precisely: every human being
necessarily possesses an ʿaqīdah - a comprehensive method of understanding the world,
a set of foundational commitments that bind together their interpretation of reality,
their values, and their judgements about what matters.

---

## The Etymological Convergence

The Arabic word ʿaqīdah derives from the root ʿaqada - to knot, to tie, to bind fast.
It names what holds a person's understanding together: the binding commitments that
prevent a worldview from being a mere collection of disconnected opinions.

The English word "religion" derives from the Latin *religare* - to bind fast, to reconnect,
to anchor.

These two roots, arising from entirely different linguistic and cultural traditions, converge
on the same structural claim about what a worldview fundamentally is: a binding. That two
independent traditions arrived at this same metaphor is itself a datum - a cross-cultural
attestation that this is the correct way to understand what every person's worldview is doing.

**The practical consequence:** When an interlocutor says "religion is too wide a concept" or
"I don't have beliefs, I just follow the evidence," do not defend the word "religion." Point
to the structure both roots are pointing at: *you have bindings*. You have things you are
tied to - epistemically, morally, interpretively. The question is whether you know what they
are and whether you have examined them.

---

## Why This Is a Logical Necessity

Every person who forms any belief about the world, makes any value judgement, acts on any
conception of what constitutes benefit or harm, or operates with any framework for
interpreting experience - is operating with an ʿaqīdah. These are not optional. Forming
beliefs, making judgements, and acting are not activities that can be performed without some
framework. The question is never *whether* a person has an ʿaqīdah. It is only *which* one
they have, *how coherently* it is held, and *how honestly* they have examined it.

---

## The Diagnostic Implication

When an interlocutor claims "I have no religion," "I'm not religious," or "I don't have
beliefs - I just follow the evidence," the correct response is not to argue about whether
they have a religion. It is to identify and name the ʿaqīdah they are actually operating
with - the implicit bindings that structure their epistemic practice, their values, and
their judgements - and to examine it with the same rigor they would apply to any other
position.

This is V7 (`references/techniques/V7-taqlid-check.md`) at its deepest level: distinguishing
between a position arrived at through genuine investigation and a position absorbed from one's
milieu without examination. The modern ʿaqīdah of secular non-religion - however unnamed - is no
less a comprehensive worldview for being unnamed. Its bindings are simply invisible to its
holder.

**Common forms of unnamed ʿaqīdah and their bindings:**

- *Empiricism as the only valid path to knowledge* - a philosophical commitment not itself
  established by empirical method; self-undermining as stated
- *Moral commitments held as objective* (torture is wrong, dignity matters) - a substantive
  metaphysical position whose grounding the holder has typically never examined (see M3 in
  `references/tactics/M3-orphaned-intuition.md`)
- *Personal autonomy as the foundational value* - a normative claim about the purpose and
  proper authority-structure of a human life
- *Naturalism as the default* - the view that the physical is all there is, treated as
  common sense rather than as the contested philosophical thesis it in fact is
- *Objects of practical dependence* - whatever is treated as bearing unseen authority over
  benefit or harm may occupy a worship-function even when not named "religion." Ask whether it is
  treated as independently effective or as an intermediary to a higher power.

Each of these is a binding. Each has load-bearing anchors, implicit doxastic rules, and
consequences that can be traced and examined using the noetic reading checklist
(`references/diagnostics/noetic-reading-checklist.md`).

---

## The Self-Refutation of "I Have No Religion"

The claim "I have no comprehensive framework for understanding the world" is itself a
comprehensive claim about the world - specifically, about one's own epistemic situation
within it. It requires a framework to state and a framework to evaluate. The person making
it is using an ʿaqīdah to deny having one.

This is performative self-refutation: the act of assertion enacts what the assertion denies.
Deploy M1-P (`references/tactics/M1P-performative-self-refutation.md`) cleanly and early.

## Worldview-Deflection and Pseudo-Neutrality

Slogans such as "I have no religion, I just follow the evidence wherever it leads,"
"I'm just following reason," "I'm neutral; I only accept evidence," or
"I looked and just wasn't convinced" are often not neutral descriptions of inquiry.
They are frequently meta-epistemic posture claims: they pre-classify what may count as
evidence, install a tribunal before the matter is examined, and deny carrying a worldview
while still operating from an unnamed ʿaqīdah.

This family must therefore be treated as a live selective branch inside P6, not as a
generic objection that simply wants sharper rebuttal. Internally, keep the full diagnosis
alive: reason-category 3 as the default pseudo-neutral read, with reason-category 4 if an
inherited criterion later becomes explicit; foreign-premise detection active; tribunal-
smuggling named; worldview denial / unnamed ʿaqīdah logged; concealment possibility left
live; deployment discipline governed by the active register. The case is memetic before it
is merely propositional.

Not every use of this language is an act of conscious deflection. Some cases are sincere but
inherited pseudo-neutrality; others are active worldview-deflection. The distinction changes
direct external deployment, not the existence of the diagnosis.

**Selective state update for this family:**

- **Retain internally:** tribunal-smuggling, reason-category, foreign premise, worldview denial,
  concealment suspicion, and whether the routing gate is still constraining release
- **Suppress externally:** premature full doctrinal discharge, over-answering, and first-order
  pile-on while the interlocutor is still installing a pseudo-neutral tribunal
- **Emit next:** one bounded diagnostic question or a tightly calibrated tribunal-clearing move,
  depending on whether the register is still deflective or has opened into genuine inquiry
- **Escalate later only if warranted:** when the interlocutor lets the question press, re-enter
  through the live case-state rather than treating the original slogan as a settled inquiry

These slogans may instantiate imported criterion-smuggling. They may function as worldview-
deflection rather than inquiry. They may also carry concealment, especially `irad`, when
deployed pre-inquiry or as register-control to stop the matter from pressing. In such cases,
internal diagnosis remains full while external deployment remains bounded.

The correct first external move is often a single honest diagnostic question rather than a
full argument dump. Canonical bounded questions for this family include:

- "When you say you just follow the evidence, what tells you in advance what is allowed to count as evidence?"
- "What made your criterion look neutral to you rather than inherited?"
- "Are you examining Islam, or only examining whether Islam fits a criterion you did not examine?"

If the interlocutor actually moves from deflection into sincere inquiry, the route can widen
into calibrated tribunal-clearing and only then into fuller first-order engagement. Until that
shift appears, bounded externalization is part of the procedure itself, not a soft stylistic choice.

---

## The Epistemic Weight of Denying Guidance

The denial "there is no righteous guidance" is frequently presented as a passive shrug -
a simple withholding of assent, epistemically modest and uncommitted. It is none of these
things. It is a substantive positive claim with specific epistemic consequences:

**1. It has its own burden of proof.**
"There is no righteous guidance" is not the null position. The null position is "I do not
know whether there is guidance." The denial is a positive assertion requiring grounds.
Deploy M6 (`references/tactics/M6-excluded-middle.md`): the proposition is either true or false; the
denial requires symmetric grounds to those demanded for the affirmation.

**2. It is subject to the Excluded Middle symmetrically.**
"You cannot prove there is guidance" must be met with: "Can you prove there is not?" If
the evidential bar is too high for the positive claim, it is equally too high for the
negative. Agnosticism - genuine suspension of judgment - is the only position consistent
with maintaining that bar for both.

**3. Pressed to its consequences, the denial generates absurdity.**
If there is no reliable guidance, then: no distinction between sound and unsound inquiry is
possible; no advice about how to live can be given; no critique of any position can be
offered on grounds of being better-grounded than another. The interlocutor who denies
guidance while offering critiques of the claim that guidance exists wields what they have
denied. Deploy M8 (`references/tactics/M8-reductio.md`) - formal reductio.

**4. The denial typically conceals an unnamed ʿaqīdah.**
When pressed - "on what basis do you determine that guidance does not exist?" - the
interlocutor will typically produce an implicit criterion: empirical verifiability, historical
conditionality, or divine hiddenness. Each of these is itself a position within a
comprehensive framework - i.e., an ʿaqīdah. The denial is never groundless; its grounds are
always examinable.

---

## Practical Deployment

**Step 1:** Do not argue about the word "religion." Agree it is contested and wide. Deploy
M7 (`references/tactics/M7-definition-anchor.md`) to anchor a functional definition: "every person
operates with a comprehensive framework - a set of bindings - whether or not they call it
religion."

**Step 2:** Ask: "What do you take to be the reliable way of knowing what is true? What do
you take to be the basis of your moral commitments? What is your account of why human life
has the significance it appears to have? What do you treat as the source of benefit and harm?"
The answers reveal the bindings, including any worship-function embedded in the person's
practical ʿaqīdah.

**Step 3:** Once bindings are identified, run the noetic reading checklist
(`references/diagnostics/noetic-reading-checklist.md`) on the unnamed ʿaqīdah just revealed. The
examination proceeds from there.

**Step 4:** If the interlocutor pushes back on "there is righteous guidance," deploy the
four-point argument above in sequence: burden of proof -> Excluded Middle -> reductio ->
unnamed ʿaqīdah revealed.

<!-- END_SOURCE: P6-universal-aqidah-principle -->
