NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "mrp_resultants": [
    {"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: circularity diagnosed",
      "reread": "R(H,Delta)",
      "route_gradient": "LoopBreak after curl pressure; HOLD boundary",
      "divergence_state": "neutral",
      "curl_state": "LoopBreak",
      "route_result_type": "no_new_resultant",
      "mrp_resultant": "stable -> LoopBreak then STOP",
      "graph_delta": "none",
      "preemption_basis": "LoopBreak",
      "route": "STOP"
    }
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
