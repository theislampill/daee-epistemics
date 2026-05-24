NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1", "B2"],
  "generated_burdens": [
    {"id": "B2", "generated_by": "MRP(B1)", "reason": "generated pressure"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: landed",
      "reread": "R(H,Delta)",
      "route_gradient": "already-held B2 from B_LA",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "held_burden_activation",
      "mrp_resultant": "genuine-dependent -> release B2",
      "graph_delta": "B1 -> B2",
      "preemption_basis": "graph-bound",
      "route": "RECURSE",
      "next_burden": "B2",
      "owner_route": ["M9"]
    }
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed", "B2": "landed"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [["B1", "B2"]], "roots": ["B1"], "acyclic": true}
  }
}
