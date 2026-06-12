NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1", "B2"],
  "B_MRP": [],
  "B_total": ["B1", "B2"],
  "mrp_resultants": [
    {"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"},
    {"source": "B2", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "reread_records": [
    {"source": "B1", "reread": "R(H,Delta)", "release_next": "STOP"},
    {"source": "B2", "reread": "R(H,Delta)", "release_next": "STOP"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Δ¹B / Delta(B1): settled public display preserved.",
      "reread": "R(H,Delta)",
      "route_gradient": "STOP; no new pressure remains",
      "divergence_state": "settled",
      "curl_state": "null",
      "route_result_type": "no_new_resultant",
      "mrp_resultant": "stable -> STOP",
      "graph_delta": "none",
      "preemption_basis": "none",
      "route": "STOP"
    },
    {
      "source_burden": "B2",
      "prior_land": "Land(B2)",
      "delta": "Δ²B / Delta(B2): bounded public display preserved.",
      "reread": "R(H,Delta)",
      "route_gradient": "STOP; no new pressure remains",
      "divergence_state": "bounded",
      "curl_state": "null",
      "route_result_type": "no_new_resultant",
      "mrp_resultant": "stable -> STOP",
      "graph_delta": "none",
      "preemption_basis": "none",
      "route": "STOP"
    }
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2"],
    "terminal_states": {"B1": "landed", "B2": "landed"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [], "roots": ["B1", "B2"], "acyclic": true}
  }
}
