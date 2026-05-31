NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1", "B2"],
  "owner_activations": [
    {"source": "MRP(B1)", "target": "B2", "owner": "authority-order-repair", "operation": "sort", "pressure": "proof-text-hidden-support", "body_ref": "B2_1", "delta": "Delta(B2):hidden-support-blocked", "land": "Land(B2)+", "ordering_role": "required"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed", "B2": "landed"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [["B1", "B2"]], "roots": ["B1"], "acyclic": true}
  }
}
