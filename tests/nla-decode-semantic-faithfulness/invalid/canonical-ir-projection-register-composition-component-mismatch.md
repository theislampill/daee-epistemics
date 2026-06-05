NOETIC FIELD EXECUTION

## Layer A - Diagnostic IR

N-frame: register-composition-component-mismatch-canary
live registers: [heart, xi, Omega, mu, kappa]

## Layer B - Bounded Governed Response

## Burden 1 / B1 - register composition
Matched owner/TTP route: [M8]
ACT records:
⟦ACT B1_1[M8.consequence-trace] :: π=register-composition :: body_ref=B1_1 :: Δ=ΔB1:dependency-exposed :: Land(B1)+⟧

#### Layer B - Governed Operation Body

### B1_1[M8] - expose register composition
Target: register-composition in the short claim.
Operation: consequence-trace traces the register-composition and exposes the owner handoff dependency.
Result/state-change: dependency-exposed; the register-composition is no longer hidden.
Contribution-to-Land(B1): This dependency-exposed state change contributes to Land(B1) by exposing the register-composition dependency.

TTP Operation Body:
The M8 operation performs consequence-trace over register-composition and exposes the dependency before any owner handoff is released.

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M8", "operation": "consequence-trace", "pressure": "register-composition", "body_ref": "B1_1", "delta": "ΔB1:dependency-exposed", "land": "Land(B1)+"}
  ],
  "register_deltas": [
    {"register": "heart", "delta": "heart is live"},
    {"register": "xi", "delta": "xi is live"},
    {"register": "Omega", "delta": "Omega is live"},
    {"register": "mu", "delta": "mu is live"},
    {"register": "kappa", "delta": "kappa is live"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true},
    "diagnostic_completeness": {
      "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
      "coverage": {"heart": ["B1"], "xi": ["B1"], "Omega": ["B1"], "mu": ["B1"], "kappa": ["B1"]},
      "complete": true
    }
  },
  "normalized_activation_record": {
    "n_frame": "register-composition-component-mismatch-canary",
    "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "M8", "operation": "consequence-trace", "delta_result": "dependency-exposed", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0}
    ]
  },
  "canonical_ir_projection": {
    "schema": "b5-canonical-ir-projection-v1",
    "diagnostic_ir_schema_version": "0.4.3-hard-registers-v1",
    "hard_registers": {
      "heart": {"state": "live", "functions": ["affective-posture"], "basis": ["heart pressure"]},
      "xi": {"state": "live", "functions": ["proof-tribunal"], "basis": ["xi pressure"]},
      "Omega": {"state": "live", "functions": ["category-transfer"], "basis": ["Omega pressure"]},
      "mu": {"state": "live", "functions": ["compression-carrier"], "basis": ["mu pressure"]},
      "kappa": {"state": "live", "functions": ["closure-boundary"], "basis": ["kappa pressure"]}
    },
    "n_frame": "register-composition-component-mismatch-canary",
    "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "M8", "operation": "consequence-trace", "delta_result": "dependency-exposed", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0}
    ],
    "diagnostic_completeness": {
      "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
      "coverage": {"heart": ["B1"], "xi": ["B1"], "Omega": ["B1"], "mu": ["B1"], "kappa": ["B1"]},
      "complete": true
    },
    "register_composition": {
      "schema": "b5-register-composition-v1",
      "source_fixture": "tests/routing-fixtures/63-register-composition-owner-handoff.json",
      "source_fixture_capability": "register-composition-owner-handoff-v1",
      "component_registers": ["heart", "xi", "Omega", "mu", "sigma"],
      "sigma_boundary": {"present": true, "inside_hard_registers": true, "role": "sigma is inside the hard-register object"},
      "composition_rule": "register composition names owner eligibility, not automatic dispatch",
      "owner_handoff": {"selected": ["M8"], "held": [], "policy": "owner eligibility, not automatic dispatch"},
      "automatic_dispatch_chain": false,
      "evidence": ["register-composition-owner-handoff-v1", "owner eligibility", "R(H,Delta)"]
    }
  }
}
