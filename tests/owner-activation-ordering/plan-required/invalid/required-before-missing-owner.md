NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1", "B2"],
  "B_MRP": [],
  "B_total": ["B1", "B2"],
  "owner_activation_ordering": {
    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
    "required_before": [
      {"target": "B2", "before_owner": "source-status-repair", "after_owner": "P3-reason-revelation-tension"}
    ],
    "parallel_groups": []
  },
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "FPD", "operation": "foreign-premise-detection", "pressure": "academic-prestige-secular-ethics-hidden-tribunal", "body_ref": "B1_1", "delta": "Delta(B1):hidden-tribunal-blocked", "land": "Land(B1)+", "ordering_role": "required"},
    {"source": "MRP(B1)", "target": "B2", "owner": "source-status-repair", "operation": "source-order", "pressure": "hidden-authority-source-status-transfer", "body_ref": "B2_1", "delta": "Delta(B2):hidden-authority-source-status-bounded", "land": "Land(B2)+", "ordering_role": "required"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2"],
    "terminal_states": {"B1": "landed", "B2": "landed"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [["B1", "B2"]], "roots": ["B1"], "acyclic": true}
  }
}
