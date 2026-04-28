---
id: P2-objection-mapping
module_class: procedure
canonical_path: skill/references/procedures/P2-objection-mapping.md
contract_version: "0.3.0.0"
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
