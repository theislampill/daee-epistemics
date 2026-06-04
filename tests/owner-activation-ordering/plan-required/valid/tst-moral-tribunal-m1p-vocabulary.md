NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activation_ordering": {
    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
    "required_before": [
      {"target": "B1", "before_owner": "FPD", "after_owner": "M1-P"},
      {"target": "B1", "before_owner": "M1-P", "after_owner": "P7"}
    ]
  },
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "FPD", "operation": "expose", "pressure": "moral tribunal filter", "body_ref": "B1_1", "delta": "Delta B1:imported-criterion-blocked", "land": "Land(B1)+", "ordering_role": "required"},
    {"source": "B1", "target": "B1", "owner": "M1-P", "operation": "test", "pressure": "public moral self-exemption", "body_ref": "B1_2", "delta": "Delta B1:performative-contradiction-exposed", "land": "Land(B1)+", "ordering_role": "required"},
    {"source": "B1", "target": "B1", "owner": "P7", "operation": "bound", "pressure": "reopen boundary", "body_ref": "B1_3", "delta": "Delta B1:scope-boundary-named", "land": "Land(B1)+", "ordering_role": "required"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
