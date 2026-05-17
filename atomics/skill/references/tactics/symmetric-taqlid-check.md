---
id: symmetric-taqlid-check
module_class: tactic
canonical_path: skill/references/tactics/symmetric-taqlid-check.md
contract_version: "0.4.0.0"
load_when:
  - before applying the outward taqlīd check (V7)
  - interlocutor asks whether the practitioner has examined their own position
companions:
  - V7-taqlid-check
  - V11-taqlid-transition
output_shapes:
  - pass-through
layer_constraint: layer-a-only
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

# Symmetric Taqlīd Check

## Runtime operator contract

- Activation: before applying the outward taqlīd check (V7).
- Field target: the live burden or submove pressure that made tactic `symmetric-taqlid-check` eligible; activation cue: before applying the outward taqlīd check (V7).
- Burden/submove form: tactic `ⁿBᵢ[OPᵢ]`: target -> operation -> result; the result contributes to `Land(ⁿB)` only when live for the current burden.
- Δ effect: `ΔⁿB` is the local target/operation/result transition; `Δκ` changes only if the operation affects closure, dependency radius, or held routes.
- Possible ∇ reread: after the tactic lands, check target-explicit `∇·B` for remaining burden pressure or `∇×ξ`/`∇×κ` for circular criterion/dependency pressure when relevant.
- R(H,Δ) obligation: after this owner acts, reread H, remaining burdens, alternate routes, register pressure, dependency loops, and closure state before STOP/RECURSE/PARTIAL.
- Hold/release/closure effect: release only the bounded result that has landed; hold, integrate, discharge as derivative, or carry forward unresolved pressure with reason.
- Output boundary: Layer A / diagnostic state only by default; release only the governed consequences permitted by render/output owners.
- Negative constraints: no argument-bank drift, no scalar closure, no deterministic route freezing, no indiscriminate TTP spraying, no ∇ as Δ replacement, no proof-by-symbol, and no Shannon/reconstruction-branding/∇ truth-or-warrant claim.
- Fixture/checker: Direct routing fixtures cover this owner (1); `tools/check_routing_parity.py`, `tools/check_ttp_operator_contracts.py`, and compiled-runtime freshness must remain green.


**Deploy when:** Before applying the outward taqlīd check; or when the interlocutor asks whether the practitioner has examined their own position.

The taqlīd check is typically directed outward — at the interlocutor's inherited skepticism. It has an equally important inward application.

**The symmetric principle:** An atheism absorbed from one's intellectual environment without genuine investigation is just as much taqlīd as a faith inherited from one's parents without genuine reflection. But so is a theism held by convention, community, or cultural inheritance without genuine examination. The practitioner who has not genuinely examined their own position has no standing to press the outward taqlīd check on anyone else.

**When the interlocutor asks:** "Have *you* actually investigated this?" The honest answer must be honest. If the practitioner holds their position by something closer to taqlīd than taḥqīq, the correct response is to acknowledge this and distinguish: "I hold this, and I am in the process of examining it more deeply" — not to deflect or project.

**This is not a concession:** A practitioner who acknowledges their own ongoing inquiry while maintaining their position models exactly what the engagement asks the interlocutor to do: hold the question open while examining it honestly. That modeling is itself epistemically operative.

**The epistemic integrity of the engagement:** If the practitioner holds their position by taqlīd, the entire engagement is compromised at the foundation. The tradition asks genuine investigation (taḥqīq) of everyone.
