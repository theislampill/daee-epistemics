NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "nodes": [{"id": "B1", "type": "burden", "state": "landed"}],
  "edges": [],
  "mrp_resultants": [
    {"source": "B1", "type": "loopbreak", "finding": "doubt-churn", "graph": "none", "route": "LoopBreak(∇×T)"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: loopbreak asserted.",
      "reread": "R(H,Delta)",
      "route_gradient": "LoopBreak asserted as resolved.",
      "divergence_state": "neutral",
      "curl_state": "non-null",
      "route_result_type": "loopbreak",
      "mrp_resultant": "doubt-churn -> LoopBreak with no graph edge",
      "graph_delta": "none",
      "preemption_basis": "commitment-bound",
      "route": "LoopBreak(∇×T)",
      "loopbreak_target": "B1",
      "loopbreak_ground": "doubt_churn_boundary",
      "loopbreak_delta": "Delta B1: loopbreak asserted",
      "post_break_reread": "R(H,Delta): curl remains non-null but closure claims resolved"
    }
  ],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "resolved"},
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
    "curl_check": "resolved",
    "max_generation_depth": 0,
    "coverage_complete": true
  }
}
