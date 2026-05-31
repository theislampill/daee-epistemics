NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activation_ordering": {
    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
    "required_before": []
  },
  "owner_activations": [
    {
      "source": "B1",
      "target": "B1",
      "owner": "M1",
      "operation": "self-grounding-test",
      "pressure": "only-science-counts-standard",
      "body_ref": "B1_1",
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
