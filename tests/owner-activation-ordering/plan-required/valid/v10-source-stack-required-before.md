NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activation_ordering": {
    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
    "required_before": [
      {"target": "B1", "before_owner": "V10", "after_owner": "M8"},
      {"target": "B1", "before_owner": "V10", "after_owner": "P7"}
    ]
  },
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "V10", "operation": "provenance", "pressure": "hadith source chain", "body_ref": "B1_1", "delta": "Delta B1:source-function-bounded", "land": "Land(B1)+", "ordering_role": "required"},
    {"source": "B1", "target": "B1", "owner": "M8", "operation": "trace", "pressure": "fatal-harm inference", "body_ref": "B1_2", "delta": "Delta B1:consequence-traced", "land": "Land(B1)+", "ordering_role": "required"},
    {"source": "B1", "target": "B1", "owner": "P7", "operation": "bound", "pressure": "closure boundary", "body_ref": "B1_3", "delta": "Delta B1:scope-boundary-named", "land": "Land(B1)+", "ordering_role": "required"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
