NOETIC FIELD EXECUTION

## Layer A - Diagnostic IR

N-frame: predication-repair-schema-light
live registers: [Omega]

## Layer B - Bounded Governed Response

## Burden 1 / B1 - predicate transfer
Matched owner/TTP route: [M9]
ACT records:
⟦ACT B1_1[M9.repair] :: π=predicate-transfer :: body_ref=B1_1 :: Δ=ΔB1:predicate transfer blocked :: Land(B1)+⟧

#### Layer B - Governed Operation Body

### B1_1[M9] - repair predicate transfer
Target: predicate-transfer in the claim that one exclusive predicate can be moved to a second referent.
Operation: repair the predicate-transfer by separating the exclusive predicate from the later category move.
Result/state-change: predicate transfer blocked; the predicate no longer moves from the first referent to the second.
Contribution-to-Land(B1): This blocks the predicate-transfer pressure and contributes to Land(B1).

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M9", "operation": "repair", "pressure": "predicate-transfer", "body_ref": "B1_1", "delta": "ΔB1:predicate transfer blocked", "land": "Land(B1)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true},
    "diagnostic_completeness": {"live_registers": ["Omega"], "coverage": {"Omega": ["B1"]}, "complete": true}
  },
  "normalized_activation_record": {
    "n_frame": "predication-repair-schema-light",
    "live_registers": ["Omega"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "M9", "operation": "repair", "delta_result": "predicate transfer blocked", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0}
    ]
  },
  "canonical_ir_projection": {
    "schema": "b5-canonical-ir-projection-v1",
    "n_frame": "predication-repair-schema-light",
    "live_registers": ["Omega"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "M9", "operation": "repair", "delta_result": "predicate transfer blocked", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B2", "owner_id": "M9", "operation": "repair", "delta_result": "predicate transfer blocked", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0}
    ],
    "diagnostic_completeness": {"live_registers": ["Omega"], "coverage": {"Omega": ["B1"]}, "complete": true}
  }
}
