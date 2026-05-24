NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activation_ordering": {
    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
    "parallel_groups": [
      {"target": "B1", "group": "predicate-source-pair", "owners": ["M9", "SOURCE"]}
    ],
    "required_before": []
  },
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M9", "operation": "repair", "pressure": "root-predicate-pressure", "body_ref": "B1_1", "delta": "Delta B1:predicate repaired", "land": "Land(B1)+", "ordering_role": "parallel", "ordering_group": "predicate-source-pair"},
    {"source": "B1", "target": "B1", "owner": "source-status-repair", "operation": "sort", "pressure": "source-function", "body_ref": "B1_2", "delta": "Delta B1:source sorted", "land": "Land(B1)+", "ordering_role": "parallel", "ordering_group": "predicate-source-pair"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
