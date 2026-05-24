NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: landed",
      "reread": "R(H,Delta)",
      "route_gradient": "newly generated B2 absent from B_LA by MRP(B1)",
      "divergence_state": "non-neutral",
      "curl_state": "held",
      "route_result_type": "generated_burden_instantiation",
      "mrp_resultant": "genuine-dependent -> instantiate B2",
      "graph_delta": "B1 -> B2",
      "preemption_basis": "framework-bound",
      "route": "RECURSE",
      "next_burden": "B2",
      "generated_by": "MRP(B1)",
      "owner_route": ["P7"]
    }
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
