NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activation_ordering": {
    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
    "required_before": [
      {
        "target": "B1",
        "before_owner": "source-status-repair",
        "before_operation": "source-order",
        "after_owner": "source-status-repair",
        "after_operation": "source-order"
      }
    ],
    "parallel_groups": []
  },
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "source-status-repair", "operation": "source-order", "pressure": "source-order-first-pass", "body_ref": "B1_1", "delta": "Delta B1:source-function-bounded", "land": "Land(B1)+", "ordering_role": "required"},
    {"source": "B1", "target": "B1", "owner": "source-status-repair", "operation": "source-order", "pressure": "source-order-second-pass", "body_ref": "B1_2", "delta": "Delta B1:science-source-bounded", "land": "Land(B1)+", "ordering_role": "required"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
