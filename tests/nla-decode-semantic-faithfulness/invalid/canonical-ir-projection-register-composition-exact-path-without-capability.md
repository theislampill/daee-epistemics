daee-epistemics - NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header
- Initial burden set: [¹B]

## Layer B - Bounded Governed Response

⟦ACT ¹B₁[P1.restore] :: π=fitrah-orientation :: body_ref=¹B₁ :: Δ=Δ¹B:fitrah-orientation-restored :: Land(¹B)+⟧

¹B₁[P1] - restore the orientation
- Target: fitrah-orientation pressure.
- Operation: restore the selected orientation.
- Result/state-change: fitrah-orientation-restored.
- Contribution-to-Land(¹B): Land(¹B) is licensed by the local operation.

Land(¹B): landed.

## field_witness

```json
{
  "n_frame": "neutral-register-composition",
  "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
  "burden_floor": ["B1"],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "P1", "operation": "restore", "pressure": "fitrah-orientation", "body_ref": "¹B₁", "delta": "Δ¹B:fitrah-orientation-restored", "land": "Land(¹B)+"}
  ],
  "normalized_activation_record": {
    "n_frame": "neutral-register-composition",
    "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "P1", "operation": "restore", "delta_result": "fitrah-orientation-restored", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0}
    ]
  },
  "canonical_ir_projection": {
    "schema": "b5-canonical-ir-projection-v1",
    "source_evidence": ["visible_act", "field_witness.owner_activations", "normalized_activation_record"],
    "n_frame": "neutral-register-composition",
    "live_registers": ["heart", "xi", "Omega", "mu", "kappa"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "P1", "operation": "restore", "delta_result": "fitrah-orientation-restored", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0}
    ],
    "diagnostic_completeness": {"live_registers": ["heart", "xi", "Omega", "mu", "kappa"], "coverage": {"heart": ["B1"], "xi": ["B1"], "Omega": ["B1"], "mu": ["B1"], "kappa": ["B1"]}, "complete": true},
    "register_composition": {
      "schema": "b5-register-composition-v1",
      "source_fixture": "tests/routing-fixtures/63-register-composition-owner-handoff.json",
      "component_registers": ["heart", "xi", "Omega", "mu", "kappa"],
      "sigma_boundary": {"present": true, "inside_hard_registers": false, "role": "sigma is the discourse-pattern surface outside the hard-register object"},
      "composition_rule": "register composition names owner eligibility, not automatic dispatch; owners remain locally selected after reread",
      "owner_handoff": {
        "selected": ["P1"],
        "held": [],
        "policy": "owner eligibility aids selection; it is not automatic dispatch"
      },
      "automatic_dispatch_chain": false,
      "evidence": [
        "old exact fixture path alone is not proof",
        "owner eligibility aids rather than automatic dispatch chains",
        "R(H,Delta)/kappa reread governs release after Land(B1)"
      ]
    }
  }
}
```
