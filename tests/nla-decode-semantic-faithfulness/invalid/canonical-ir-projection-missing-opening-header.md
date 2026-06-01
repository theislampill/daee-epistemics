N-frame: source-order-with-machine-projection
live registers: [xi]

## Layer B - Bounded Governed Response

## Burden 1 / B1 - source-order warrant
Matched owner/TTP route: [source-status-repair]
ACT records:
⟦ACT B1_1[source-status-repair.source-order] :: π=science-only-warrant :: body_ref=B1_1 :: Δ=ΔB1:science-source-bounded :: Land(B1)+⟧

#### Layer B - Governed Operation Body

### B1_1[source-status-repair] - sort the source-order claim
Target: science-only-warrant in the demand that only scientific explanation can authorize knowledge.
Operation: source-order bounds the science-only-warrant pressure by assigning science to its proper source lane rather than letting it rule every warrant type.
Result/state-change: science-source-bounded; the scientific source-order pressure is no longer allowed to veto non-scientific warrant.
Contribution-to-Land(B1): This science-source-bounded state change contributes to Land(B1) by sorting the source-order pressure.

TTP Operation Body:
The operation source-order bounds the source claim by naming the category of scientific explanation and preventing it from becoming the whole tribunal for knowledge.

Land(B1): the source-order warrant burden is landed.

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "source-status-repair", "operation": "source-order", "pressure": "science-only-warrant", "body_ref": "B1_1", "delta": "ΔB1:science-source-bounded", "land": "Land(B1)+"}
  ],
  "register_deltas": [
    {"register": "xi", "delta": "warrant authority typed as live source-order pressure"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true},
    "diagnostic_completeness": {
      "live_registers": ["xi"],
      "coverage": {"xi": ["B1"]},
      "complete": true
    }
  },
  "normalized_activation_record": {
    "n_frame": "source-order-with-machine-projection",
    "live_registers": ["xi"],
    "burden_floor": ["B1"],
    "per_burden": [
      {
        "burden_id": "B1",
        "owner_id": "source-status-repair",
        "operation": "source-order",
        "delta_result": "science-source-bounded",
        "mrp_route_result_type": "held_burden_activation",
        "terminal_state": "landed",
        "generation_depth": 0
      }
    ]
  },
  "canonical_ir_projection": {
    "schema": "b5-canonical-ir-projection-v1",
    "diagnostic_ir_schema_version": "0.4.3-hard-registers-v1",
    "hard_registers": {
      "heart": {"state": "non_live", "functions": [], "basis": [], "non_live_reason": "no affective posture pressure is live in this bounded fixture"},
      "xi": {"state": "live", "functions": ["warrant-authority", "source-order"], "basis": ["the source-order pressure controls admissible warrant"]},
      "Omega": {"state": "non_live", "functions": [], "basis": [], "non_live_reason": "no ontology or predication transfer pressure is live in this bounded fixture"},
      "mu": {"state": "non_live", "functions": [], "basis": [], "non_live_reason": "no memetic carrier pressure is live in this bounded fixture"},
      "kappa": {"state": "non_live", "functions": [], "basis": [], "non_live_reason": "no closure-boundary pressure is live in this bounded fixture"}
    },
    "n_frame": "source-order-with-machine-projection",
    "live_registers": ["xi"],
    "burden_floor": ["B1"],
    "per_burden": [
      {
        "burden_id": "B1",
        "owner_id": "source-status-repair",
        "operation": "source-order",
        "delta_result": "science-source-bounded",
        "mrp_route_result_type": "held_burden_activation",
        "terminal_state": "landed",
        "generation_depth": 0
      }
    ],
    "diagnostic_completeness": {
      "live_registers": ["xi"],
      "coverage": {"xi": ["B1"]},
      "complete": true
    }
  }
}
