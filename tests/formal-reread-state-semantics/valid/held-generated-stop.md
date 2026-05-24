NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1", "B2"],
  "B_MRP": ["B3"],
  "B_total": ["B1", "B2", "B3"],
  "generated_burdens": [
    {"id": "B3", "generated_by": "MRP(B2)", "reason": "new boundary pressure"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"},
    {"source": "B2", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B2 -> B3", "route": "RECURSE"},
    {"source": "B3", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "reread_records": [
    {"source": "B1", "reread": "R(H,Delta)", "release_next": "B2"},
    {"source": "B2", "reread": "R(H,Delta)", "release_next": "B3"},
    {"source": "B3", "reread": "R(H,Delta)", "release_next": "STOP"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: first pressure landed",
      "reread": "R(H,Delta)",
      "route_gradient": "already-held B2 from B_LA; release B2",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "held_burden_activation",
      "mrp_resultant": "genuine-dependent -> release B2",
      "graph_delta": "B1 -> B2",
      "preemption_basis": "graph-bound",
      "route": "RECURSE",
      "next_burden": "B2",
      "owner_route": ["M9"]
    },
    {
      "source_burden": "B2",
      "prior_land": "Land(B2)",
      "delta": "Delta B2: second pressure landed",
      "reread": "R(H,Delta)",
      "route_gradient": "newly generated B3 absent from B_LA by MRP(B2)",
      "divergence_state": "non-neutral",
      "curl_state": "held",
      "route_result_type": "generated_burden_instantiation",
      "mrp_resultant": "genuine-dependent -> instantiate B3 [generated-by: MRP(B2)]",
      "graph_delta": "B2 -> B3",
      "preemption_basis": "framework-bound",
      "route": "RECURSE",
      "next_burden": "B3",
      "generated_by": "MRP(B2)",
      "owner_route": ["P7"]
    },
    {
      "source_burden": "B3",
      "prior_land": "Land(B3)",
      "delta": "Delta B3: generated pressure landed",
      "reread": "R(H,Delta)",
      "route_gradient": "STOP; no new load-bearing pressure remains",
      "divergence_state": "neutral",
      "curl_state": "resolved",
      "route_result_type": "no_new_resultant",
      "mrp_resultant": "stable -> no new graph edge; STOP",
      "graph_delta": "none",
      "preemption_basis": "none",
      "route": "STOP"
    }
  ],
  "field_diagnostics": {
    "divergence_check": "neutral",
    "curl_check": "resolved"
  },
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2"],
    "coverage_complete": true,
    "terminal_states": {"B1": "landed", "B2": "landed", "B3": "landed"},
    "dependency_graph": {
      "nodes": ["B1", "B2", "B3"],
      "edges": [["B1", "B2"], ["B2", "B3"]],
      "roots": ["B1"],
      "acyclic": true
    }
  }
}
