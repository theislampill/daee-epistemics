NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1", "B2"],
  "B_MRP": [],
  "B_total": ["B1", "B2"],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M9", "operation": "repair", "pressure": "predicate-transfer", "body_ref": "B1_1", "delta": "Delta B1:predicate transfer blocked", "land": "Land(B1)+"}
  ],
  "field_diagnostics": {
    "divergence_check": "non-neutral / B2 remains live",
    "curl_check": "null"
  },
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2"],
    "coverage_complete": false,
    "terminal_states": {
      "B1": "landed",
      "B2": "carried-PARTIAL / source text needed before release"
    },
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [], "roots": ["B1", "B2"], "acyclic": true}
  }
}
