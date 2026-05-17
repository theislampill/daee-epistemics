---
id: M8-reductio
module_class: tactic
canonical_path: skill/references/tactics/M8-reductio.md
contract_version: "0.4.0.0"
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

## Runtime operator contract

- Activation: interlocutor's position, followed consistently, produces formally contradictory, obviously absurd, or manifestly rejected consequences.
- Field target: the live burden or submove pressure that made tactic `M8-reductio` eligible; activation cue: interlocutor's position, followed consistently, produces formally contradictory, obviously absurd, or manifestly rejected consequences.
- Burden/submove form: tactic `ⁿBᵢ[OPᵢ]`: target -> operation -> result; the result contributes to `Land(ⁿB)` only when live for the current burden.
- Δ effect: `ΔⁿB` is the local target/operation/result transition; `Δκ` changes only if the operation affects closure, dependency radius, or held routes.
- Possible ∇ reread: after the tactic lands, check target-explicit `∇·B` for remaining burden pressure or `∇×ξ`/`∇×κ` for circular criterion/dependency pressure when relevant.
- R(H,Δ) obligation: after this owner acts, reread H, remaining burdens, alternate routes, register pressure, dependency loops, and closure state before STOP/RECURSE/PARTIAL.
- Hold/release/closure effect: release only the bounded result that has landed; hold, integrate, discharge as derivative, or carry forward unresolved pressure with reason.
- Output boundary: `layer-b-permitted` with output shapes `bounded-single-pass`. Default render may show compact state markers when control-bound; long formalism stays audit/formalism-expanded.
- Negative constraints: no argument-bank drift, no scalar closure, no deterministic route freezing, no indiscriminate TTP spraying, no ∇ as Δ replacement, no proof-by-symbol, and no Shannon/reconstruction-branding/∇ truth-or-warrant claim.
- Fixture/checker: Direct routing fixtures cover this owner (3); `tools/check_routing_parity.py`, `tools/check_ttp_operator_contracts.py`, and compiled-runtime freshness must remain green.


**Type:** Meta-tactic
**Deploy when:** Interlocutor's position, followed consistently, produces consequences that are formally contradictory, obviously absurd, or that the interlocutor manifestly rejects.

Distinct from M1 (premises undermine conclusion) and M1-P (speech act enacts what it denies): M8 assumes the position, traces its consequences, and shows the consequences are unacceptable.

## Layer B Activation Floor

M8 is not executed by writing a generic consequence paragraph. When M8 is structurally live,
Layer B must show:

1. why the reductio is live for the present burden;
2. the target criterion, premise, source-frame, or proof-rule being assumed for the trace;
3. the operation: follow that commitment by valid or locally accepted steps;
4. the result/state change: the consequence contradicts the claim, defeats the criterion on
   its own grounds, or forces an unacceptable commitment;
5. how the consequence contributes to `Land(B)` without turning every further implication
   into a new burden-cycle.

If the consequence trace belongs to predication, transmission, proof-method, grief/register,
or another family-local owner, M8 must stay inside that owner's live burden rather than
relabeling the case as generic worldview critique.

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

M8 uses `B -> {s1...sn} -> Land(B) -> R` from `recursive-state-transitions.md`. Gloss: land one consequence, reassess live state, and extend only if the restoration target still requires further compounding under P7, register discipline, and current release conditions.

Source-worldview consequence traces must be concrete, not labels. When a public worldview,
school frame, ideology, or noetic-family frame supplies the criterion, M8 must assume the
actual operative commitment, trace what that commitment can and cannot warrant, name the
unacceptable or self-defeating consequence, and keep source-status discipline intact. A
generic "worldview consequence" paragraph fails M8 if it does not identify the criterion
being assumed and the burden-state changed by the consequence trace. If the live pressure is
predication, transmission, kalamic proof-order, grief/register, or another family-local frame,
do not relabel it as source-worldview; trace the consequence in that family's own terms.
