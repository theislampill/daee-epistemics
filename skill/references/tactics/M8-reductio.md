---
id: M8-reductio
module_class: tactic
canonical_path: skill/references/tactics/M8-reductio.md
contract_version: "0.2.3.0"
load_when:
  - interlocutor's position, followed consistently, produces formally contradictory, obviously absurd, or manifestly rejected consequences
companions:
  - M1-self-refutation
  - M1P-performative-self-refutation
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

# M8 — Reductio ad Absurdum (Formal and Informal)

**Type:** Meta-tactic
**Deploy when:** Interlocutor's position, followed consistently, produces consequences that are formally contradictory, obviously absurd, or that the interlocutor manifestly rejects.

Distinct from M1 (premises undermine conclusion) and M1-P (speech act enacts what it denies): M8 assumes the position, traces its consequences, and shows the consequences are unacceptable.

## Formal Reductio

Assume P. Derive from P, by valid steps, both Q and not-Q. Conclude not-P.

**The guidance case:** Assume "there is no righteous guidance." Then: no reliable distinction between sound and unsound inquiry is possible; no advice about what to believe can be offered on grounds of being better-grounded than its denial. But the interlocutor is offering exactly such advice. Contradiction. Therefore "there is no righteous guidance" is false, or the interlocutor's assertion of it is incoherent.

## Informal Reductio

Assume P. Show that P, followed consistently, produces conclusions the interlocutor clearly does not accept — and that their rejection of those conclusions implies the rejection of P.

**Domain-specific examples:**
- The naturalist who grants reliability of inductive reasoning but denies non-physical reality: what grounds inductive reliability? The only satisfying answer requires something non-physical (rational structure, objective logical laws, mind-independent order). The naturalist is committed either to inductive skepticism or to something beyond the physical. Either conclusion is unacceptable; therefore naturalism as stated cannot be maintained.
- The moral skeptic who denies objective moral facts but makes moral criticisms: assume their position — then no moral criticism carries normative weight. The interlocutor must choose between moral skepticism and moral rhetoric; they cannot consistently hold both.
- The relativist who urges adoption of relativism: assume relativism — then "relativism is true" is only true relative to some framework, with no claim on anyone operating from a different one. The act of recommendation presupposes the non-relative truth of relativism.

**The fiṭrah reductio:** Assume the fiṭrah is a systematic cognitive error. Then: the faculties used to evaluate this claim are themselves products of the declared-unreliable system; virtually all humans throughout history have been systematically wrong about their most basic cognitive deliverances (which tawātur fiṭrī rules out); the interlocutor's own moral commitments, epistemic confidence, and conviction that truth-tracking is valuable are all products of this declared-unreliable system. The interlocutor has no vantage point from which to declare the fiṭrah faulty, because every vantage point they occupy is a delivery of it.

## Five-Step Sequencing

1. State clearly: "I am going to assume your position for the sake of argument and trace what follows."
2. Derive the consequences by valid steps — be explicit, not impressionistic.
3. Identify the absurdity or unacceptable commitment: "What follows is X. Do you accept X?"
4. If they accept X: stop there or leave one bounded question alive. Do not continue down the chain automatically in the same round; P7 Stop-2 governs. Any further extension requires a fresh reassessment of case-state, register, concealment/orientation, and release conditions.
5. If they reject X: "X follows necessarily from your position. You cannot reject X without rejecting the position that generated it."

M8 is not a one-shot contradiction move and not an autonomous chain-dump. It is a selective recursive tactic: land one consequence, reassess the live state, and extend only if the restoration target still requires further compounding. Same-round continuation is governed by P7 stops, register discipline, and current release conditions.
