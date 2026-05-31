NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "nodes": [{"id": "B1", "type": "burden", "state": "landed"}],
  "edges": [],
  "mrp_resultants": [
    {"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: landed while curl remains.",
      "reread": "R(H,Delta)",
      "route_gradient": "STOP despite curl.",
      "divergence_state": "neutral",
      "curl_state": "non-null",
      "route_result_type": "no_new_resultant",
      "mrp_resultant": "stable -> no new graph edge",
      "graph_delta": "none",
      "preemption_basis": "none",
      "route": "STOP"
    }
  ],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "non-null"},
  "terminal_states": {"B1": "landed"},
  "closure": {"status": "coverage_complete=true"},
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M1", "operation": "repair", "pressure": "root", "body_ref": "B1_1", "delta": "Delta B1:landed", "land": "Land(B1)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true},
    "divergence_check": "neutral",
    "curl_check": "non-null",
    "max_generation_depth": 0,
    "coverage_complete": true
  }
}
