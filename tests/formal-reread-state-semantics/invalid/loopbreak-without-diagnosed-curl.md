NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "mrp_resultants": [
    {"source": "B1", "type": "loopbreak", "finding": "doubt-churn", "graph": "none", "route": "LoopBreak(∇×T)"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: loopbreak asserted",
      "reread": "R(H,Delta)",
      "route_gradient": "LoopBreak/HOLD asserted without diagnosed curl",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "loopbreak",
      "mrp_resultant": "doubt-churn -> LoopBreak licensed; graph none; HOLD/PARTIAL",
      "graph_delta": "none",
      "preemption_basis": "commitment-bound",
      "route": "LoopBreak(∇×T)",
      "loopbreak_target": "B1",
      "loopbreak_ground": "generic worry",
      "loopbreak_delta": "Delta B1: loopbreak asserted",
      "post_break_reread": "R(H,Delta)"
    }
  ],
  "field_diagnostics": {
    "divergence_check": "non-neutral / pressure remains held",
    "curl_check": "null / no curl diagnosed"
  },
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "coverage_complete": false,
    "terminal_states": {"B1": "held-with-reason"},
    "dependency_graph": {
      "nodes": ["B1"],
      "edges": [],
      "roots": ["B1"],
      "acyclic": true
    }
  }
}
