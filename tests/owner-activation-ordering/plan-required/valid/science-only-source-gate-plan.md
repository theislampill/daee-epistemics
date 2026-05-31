NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activation_ordering": {
    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
    "required_before": [
      {"target": "B1", "before_owner": "source-status-repair", "after_owner": "M1"}
    ],
    "parallel_groups": [],
    "contingent": [],
    "non_load_bearing": []
  },
  "owner_activations": [
    {
      "source": "B1",
      "target": "B1",
      "owner": "source-status-repair",
      "operation": "source-order",
      "pressure": "scientific-explanations-as-only-knowledge-source",
      "body_ref": "B1_1",
      "delta": "Delta B1:science-source-bounded",
      "land": "Land(B1)+",
      "ordering_role": "required"
    },
    {
      "source": "B1",
      "target": "B1",
      "owner": "M1",
      "operation": "self-grounding-test",
      "pressure": "only-science-counts-standard",
      "body_ref": "B1_2",
      "delta": "Delta B1:self-authorizing-standard-invalidated",
      "land": "Land(B1)+",
      "ordering_role": "required"
    }
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
