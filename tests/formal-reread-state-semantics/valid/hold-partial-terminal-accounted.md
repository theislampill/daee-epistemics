NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "mrp_resultants": [
    {"source": "B1", "type": "hold_partial", "finding": "partial-real", "graph": "none", "route": "HOLD"}
  ],
  "reread_records": [
    {"source": "B1", "reread": "R(H,Delta)", "release_next": "HOLD"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: bounded evidence gap remains",
      "reread": "R(H,Delta)",
      "route_gradient": "HOLD/PARTIAL: no generated burden; missing proof evidence remains held",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "hold_partial",
      "mrp_resultant": "partial-real -> no new graph edge; B1 held/PARTIAL pending named evidence",
      "graph_delta": "none",
      "preemption_basis": "graph-bound HOLD/PARTIAL",
      "route": "HOLD",
      "owner_route": ["P7"]
    }
  ],
  "field_diagnostics": {
    "divergence": "non-neutral / B1 carried-PARTIAL",
    "curl": "null",
    "route": "HOLD"
  },
  "terminal_states": {
    "B1": "carried-PARTIAL"
  },
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "coverage_complete": false,
    "terminal_states": {"B1": "carried-PARTIAL"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
