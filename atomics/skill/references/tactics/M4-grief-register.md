---
id: M4-grief-register
module_class: tactic
canonical_path: skill/references/tactics/M4-grief-register.md
contract_version: "0.4.0.0"
load_when:
  - problem of evil is a personal moral protest arising from genuine suffering (not a philosophical argument)
  - grief or betrayal is primary
blocks:
  - intellectual content, theodicy, or doctrinal content while grief is primary
routing_effects:
  - triggers P7 Stop-1 (Content-Withholding Stop) automatically
p7_stops_governed:
  - stop-1
companions:
  - P7-restoration-stops
output_shapes:
  - bounded-single-pass
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

# M4 — Grief Register

## Runtime operator contract

- Activation: problem of evil is a personal moral protest arising from genuine suffering (not a philosophical argument).
- Field target: the live burden or submove pressure that made tactic `M4-grief-register` eligible; activation cue: problem of evil is a personal moral protest arising from genuine suffering (not a philosophical argument).
- Burden/submove form: tactic `ⁿBᵢ[OPᵢ]`: target -> operation -> result; the result contributes to `Land(ⁿB)` only when live for the current burden.
- Δ effect: `ΔⁿB` is the local target/operation/result transition; `Δκ` changes only if the operation affects closure, dependency radius, or held routes.
- Possible ∇ reread: after the tactic lands, check target-explicit `∇·B` for remaining burden pressure or `∇×ξ`/`∇×κ` for circular criterion/dependency pressure when relevant.
- R(H,Δ) obligation: after this owner acts, reread H, remaining burdens, alternate routes, register pressure, dependency loops, and closure state before STOP/RECURSE/PARTIAL.
- Hold/release/closure effect: release only the bounded result that has landed; hold, integrate, discharge as derivative, or carry forward unresolved pressure with reason.
- Output boundary: `layer-b-governed` with output shapes `bounded-single-pass`. Default render may show compact state markers when control-bound; long formalism stays audit/formalism-expanded.
- Negative constraints: no argument-bank drift, no scalar closure, no deterministic route freezing, no indiscriminate TTP spraying, no ∇ as Δ replacement, no proof-by-symbol, and no Shannon/reconstruction-branding/∇ truth-or-warrant claim.
- Fixture/checker: Direct routing fixtures cover this owner (5); `tools/check_routing_parity.py`, `tools/check_ttp_operator_contracts.py`, and compiled-runtime freshness must remain green.


**Type:** Meta-tactic
**Deploy when:** Problem of evil is not a philosophical argument but a personal moral protest arising from genuine suffering.

When this is operative, the argumentative register must be entirely suspended. Enter a different mode: attentive, non-argumentative, genuinely present to the weight of what the person carries.

**The diagnostic:** Distinguish philosophical argument from personal protest. The philosophical argument asks: given the distribution of suffering in the world, what is the probability of God's existence? The personal protest says: I have suffered, or someone I love has suffered, and this is not acceptable. The two require categorically different responses.

**What works:** Genuine presence. Attentiveness to what is actually being carried. No argument, no theodicy, no "but consider that..." The fiṭrah of a person in genuine grief is often very close to the surface — it will not be reached through argument. Theological content, if it comes at all, comes later and gently, at the invitation of the person.

**What does not work:** Any intellectual content while the grief is present and primary. Theodicy offered too soon is experienced as dismissal.

**P7 stop:** When M4 is active, P7 Stop 1 (Content-Withholding Stop) in `references/procedures/P7-restoration-stops.md` is automatically triggered. Grief-primary is a named trigger for that stop. The mandatory action (establish relational register before any intellectual content) and the prohibited action (deploying doctrinal content into a grief-primary space) are specified there. M4 names the register; P7 Stop 1 enforces the mandatory and prohibited actions as hard rails.

**Connection:** M4 does not route to any subsequent tactic directly — it suspends the tactic-selection process. The subsequent engagement is governed by what the person needs and what opens, not by the skill's diagnostic.
