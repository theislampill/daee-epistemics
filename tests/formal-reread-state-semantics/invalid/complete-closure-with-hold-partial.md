NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1", "B2"],
  "B_MRP": [],
  "B_total": ["B1", "B2"],
  "mrp_resultants": [
    {"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"},
    {"source": "B2", "type": "hold_partial", "finding": "partial-real", "graph": "none", "route": "HOLD"}
  ],
  "reread_records": [
    {"source": "B1", "reread": "R(H,Delta)", "release_next": "STOP"},
    {"source": "B2", "reread": "R(H,Delta)", "release_next": "HOLD"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: settled local burden",
      "reread": "R(H,Delta)",
      "route_gradient": "STOP; no new pressure remains for B1",
      "divergence_state": "neutral",
      "curl_state": "null",
      "route_result_type": "no_new_resultant",
      "mrp_resultant": "stable -> graph none; route STOP",
      "graph_delta": "none",
      "preemption_basis": "none",
      "route": "STOP",
      "no_new_resultant_proof": {
        "proved": true,
        "escape_routes_checked": [],
        "basis": "B1 has no live route."
      }
    },
    {
      "source_burden": "B2",
      "prior_land": "Land(B2)",
      "delta": "Delta B2: bounded evidence gap remains",
      "reread": "R(H,Delta)",
      "route_gradient": "HOLD/PARTIAL: no generated burden; missing proof evidence remains held",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "hold_partial",
      "mrp_resultant": "partial-real -> no new graph edge; B2 held/PARTIAL pending named evidence",
      "graph_delta": "none",
      "preemption_basis": "graph-bound HOLD/PARTIAL",
      "route": "HOLD",
      "owner_route": ["P7"]
    }
  ],
  "terminal_states": {
    "B1": "landed",
    "B2": "held-with-reason"
  },
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2"],
    "coverage_complete": true,
    "terminal_states": {"B1": "landed", "B2": "held-with-reason"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [], "roots": ["B1", "B2"], "acyclic": true}
  },
  "closure": {
    "status": "coverage_complete=true",
    "unresolved_burdens": []
  }
}
