NOETIC FIELD EXECUTION

## Layer A - Diagnostic IR

N-frame: register-composition-owner-handoff
live registers: [heart, xi, Omega, mu, kappa]

## Layer B - Bounded Governed Response

## Burden 1 / B1 - register composition owner handoff
Matched owner/TTP route: [P1, source-status-repair, M9, M8, P7]
ACT records:
⟦ACT B1_1[P1.fitrah-reorientation] :: π=anxiety-pressure :: body_ref=B1_1 :: Δ=ΔB1:fitrah-reorientation-restored :: Land(B1)+⟧
⟦ACT B1_2[source-status-repair.source-order] :: π=proof-denominator-demand :: body_ref=B1_2 :: Δ=ΔB1:source-order-repaired :: Land(B1)+⟧
⟦ACT B1_3[M9.predication-repair] :: π=loaded-semantic-label :: body_ref=B1_3 :: Δ=ΔB1:predicate-separated :: Land(B1)+⟧
⟦ACT B1_4[M8.consequence-trace] :: π=compressed-owner-carrier :: body_ref=B1_4 :: Δ=ΔB1:dependency-exposed :: Land(B1)+⟧
⟦ACT B1_5[P7.stop-condition] :: π=automatic-dispatch-chain :: body_ref=B1_5 :: Δ=ΔB1:scope-boundary-named :: Land(B1)+⟧

#### Layer B - Governed Operation Body

### B1_1[P1] - restore posture before owner handoff
Target: anxiety-pressure in the same short claim.
Operation: fitrah-reorientation steadies the anxiety-pressure before content owners are stacked.
Result/state-change: fitrah-reorientation-restored; the anxiety-pressure is no longer allowed to govern the owner handoff.
Contribution-to-Land(B1): This fitrah-reorientation-restored state change contributes to Land(B1) by keeping the heart register inside the composed burden without letting it become the whole answer.

TTP Operation Body:
The P1 operation performs fitrah-reorientation over anxiety-pressure and makes a local state change before the other live registers are considered.

### B1_2[source-status-repair] - repair the proof denominator
Target: proof-denominator-demand in the same short claim.
Operation: source-order repairs the proof-denominator-demand by naming which proof source is being asked to control admissibility.
Result/state-change: source-order-repaired; the proof-denominator-demand is bounded instead of becoming the only proof tribunal.
Contribution-to-Land(B1): This source-order-repaired state change contributes to Land(B1) by keeping the xi register explicit in the owner handoff.

TTP Operation Body:
The source-status-repair operation performs source-order over the proof-denominator-demand and prevents a single proof denominator from silently controlling the composed route.

### B1_3[M9] - separate the loaded label
Target: loaded-semantic-label in the same short claim.
Operation: predication-repair separates the loaded-semantic-label from the referent it was trying to control.
Result/state-change: predicate-separated; the loaded-semantic-label no longer transfers its category to the whole field.
Contribution-to-Land(B1): This predicate-separated state change contributes to Land(B1) by keeping the Omega register locally repaired before reread.

TTP Operation Body:
The M9 operation performs predication-repair over the loaded-semantic-label and separates label, referent, and category so the composition remains typed.

### B1_4[M8] - expose the compressed carrier
Target: compressed-owner-carrier in the same short claim.
Operation: consequence-trace traces the compressed-owner-carrier and shows which owner pressures it is carrying together.
Result/state-change: dependency-exposed; the compressed-owner-carrier no longer hides the proof, semantic, and posture dependencies.
Contribution-to-Land(B1): This dependency-exposed state change contributes to Land(B1) by making the mu register's carrier function visible without turning it into a generic mixed case.

TTP Operation Body:
The M8 operation performs consequence-trace over the compressed-owner-carrier and exposes the dependency that made the short claim carry multiple registers at once.

### B1_5[P7] - prevent automatic route stacking
Target: automatic-dispatch-chain in the same short claim.
Operation: stop-condition names the automatic-dispatch-chain risk and requires R(H,Delta) reread before another owner is released.
Result/state-change: scope-boundary-named; the automatic-dispatch-chain is blocked and the composed register handoff remains bounded.
Contribution-to-Land(B1): This scope-boundary-named state change contributes to Land(B1) by forcing owner eligibility to remain an aid, not an automatic dispatch chain.

TTP Operation Body:
The P7 operation performs stop-condition over the automatic-dispatch-chain and names the scope boundary before R(H,Delta) can release or hold the next route.

Land(B1): the composed register handoff is landed without pretending the owners form an automatic chain.

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "P1", "operation": "fitrah-reorientation", "pressure": "anxiety-pressure", "body_ref": "B1_1", "delta": "ΔB1:fitrah-reorientation-restored", "land": "Land(B1)+"},
    {"source": "B1", "target": "B1", "owner": "source-status-repair", "operation": "source-order", "pressure": "proof-denominator-demand", "body_ref": "B1_2", "delta": "ΔB1:source-order-repaired", "land": "Land(B1)+"},
    {"source": "B1", "target": "B1", "owner": "M9", "operation": "predication-repair", "pressure": "loaded-semantic-label", "body_ref": "B1_3", "delta": "ΔB1:predicate-separated", "land": "Land(B1)+"},
    {"source": "B1", "target": "B1", "owner": "M8", "operation": "consequence-trace", "pressure": "compressed-owner-carrier", "body_ref": "B1_4", "delta": "ΔB1:dependency-exposed", "land": "Land(B1)+"},
    {"source": "B1", "target": "B1", "owner": "P7", "operation": "stop-condition", "pressure": "automatic-dispatch-chain", "body_ref": "B1_5", "delta": "ΔB1:scope-boundary-named", "land": "Land(B1)+"}
  ],
  "register_deltas": [
    {"register": "heart", "delta": "affective posture pressure remains live and locally restored inside the composition"},
    {"register": "xi", "delta": "proof tribunal pressure remains live and source-order repaired inside the composition"},
    {"register": "Omega", "delta": "category transfer pressure remains live and predication-repaired inside the composition"},
    {"register": "mu", "delta": "compression carrier pressure remains live and dependency-exposed inside the composition"},
    {"register": "kappa", "delta": "closure-boundary pressure remains live and scope-boundary named before reread"}
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
    "n_frame": "register-composition-owner-handoff",
    "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "P1", "operation": "fitrah-reorientation", "delta_result": "fitrah-reorientation-restored", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B1", "owner_id": "source-status-repair", "operation": "source-order", "delta_result": "source-order-repaired", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B1", "owner_id": "M9", "operation": "predication-repair", "delta_result": "predicate-separated", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B1", "owner_id": "M8", "operation": "consequence-trace", "delta_result": "dependency-exposed", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B1", "owner_id": "P7", "operation": "stop-condition", "delta_result": "scope-boundary-named", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0}
    ]
  },
  "canonical_ir_projection": {
    "schema": "b5-canonical-ir-projection-v1",
    "diagnostic_ir_schema_version": "0.4.3-hard-registers-v1",
    "hard_registers": {
      "heart": {"state": "live", "functions": ["affective-posture"], "basis": ["anxiety pressure is live in the short claim"]},
      "xi": {"state": "live", "functions": ["proof-tribunal"], "basis": ["proof denominator demand is live in the short claim"]},
      "Omega": {"state": "live", "functions": ["category-transfer"], "basis": ["loaded semantic label is live in the short claim"]},
      "mu": {"state": "live", "functions": ["compression-carrier"], "basis": ["the claim compresses multiple owner pressures"]},
      "kappa": {"state": "live", "functions": ["closure-boundary"], "basis": ["owner handoff requires reread before another route is released"]}
    },
    "n_frame": "register-composition-owner-handoff",
    "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "P1", "operation": "fitrah-reorientation", "delta_result": "fitrah-reorientation-restored", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B1", "owner_id": "source-status-repair", "operation": "source-order", "delta_result": "source-order-repaired", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B1", "owner_id": "M9", "operation": "predication-repair", "delta_result": "predicate-separated", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B1", "owner_id": "M8", "operation": "consequence-trace", "delta_result": "dependency-exposed", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B1", "owner_id": "P7", "operation": "stop-condition", "delta_result": "scope-boundary-named", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0}
    ],
    "diagnostic_completeness": {
      "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
      "coverage": {"heart": ["B1"], "xi": ["B1"], "Omega": ["B1"], "mu": ["B1"], "kappa": ["B1"]},
      "complete": true
    },
    "register_composition": {
      "schema": "b5-register-composition-v1",
      "source_fixture": "tests/routing-fixtures/63-register-composition-owner-handoff.json",
      "component_registers": ["heart", "xi", "Omega", "mu", "kappa"],
      "sigma_boundary": {"present": true, "inside_hard_registers": false, "role": "sigma is the discourse-pattern surface outside the hard-register object"},
      "composition_rule": "register composition names owner eligibility, not automatic dispatch; owners remain locally selected after reread",
      "owner_handoff": {
        "selected": ["P1", "source-status-repair", "M9", "M8", "P7"],
        "held": ["proof-method-audit", "doubt-vs-skepticism"],
        "policy": "owner eligibility aids selection; it is not automatic dispatch"
      },
      "automatic_dispatch_chain": false,
      "evidence": [
        "fixture 63 register-composition owner handoff",
        "owner eligibility aids rather than automatic dispatch chains",
        "R(H,Delta)/kappa reread governs release after Land(B1)"
      ]
    }
  }
}
