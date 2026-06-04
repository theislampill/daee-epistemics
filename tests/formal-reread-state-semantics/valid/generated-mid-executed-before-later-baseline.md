NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1", "B2", "B3"],
  "B_MRP": ["B4"],
  "B_total": ["B1", "B2", "B3", "B4"],
  "generated_burdens": [
    {"id": "B4", "generated_by": "MRP(B2)", "generation_depth": 1, "reason": "mid-chain source-worldview recoil after B2 landed"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"},
    {"source": "B2", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B2 -> B4", "route": "RECURSE"},
    {"source": "B4", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B4 -> B3", "route": "RECURSE"}
  ],
  "reread_records": [
    {"source": "B1", "reread": "R(H,Delta)", "release_next": "B2"},
    {"source": "B2", "reread": "R(H,Delta)", "release_next": "B4"},
    {"source": "B4", "reread": "R(H,Delta)", "release_next": "B3"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: opening pressure landed",
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
      "owner_route": ["M8"]
    },
    {
      "source_burden": "B2",
      "prior_land": "Land(B2)",
      "delta": "Delta B2: mid-chain pressure landed and exposed source-worldview recoil",
      "reread": "R(H,Delta)",
      "route_gradient": "newly generated B4 absent from B_LA by MRP(B2) while later baseline B3 remains initial-held",
      "divergence_state": "non-neutral",
      "curl_state": "held",
      "route_result_type": "generated_burden_instantiation",
      "mrp_resultant": "genuine-dependent -> instantiate B4 [generated-by: MRP(B2)] and route RECURSE",
      "graph_delta": "B2 -> B4",
      "preemption_basis": "framework-bound",
      "route": "RECURSE",
      "next_burden": "B4",
      "generated_by": "MRP(B2)",
      "owner_route": ["FPD", "P7"]
    },
    {
      "source_burden": "B4",
      "prior_land": "Land(B4)",
      "delta": "Delta B4: generated source-worldview recoil executed and landed",
      "reread": "R(H,Delta)",
      "route_gradient": "already-held B3 from B_LA remains after generated B4 lands; release B3 instead of treating B4 as final",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "held_burden_activation",
      "mrp_resultant": "genuine-dependent -> release B3 from B_LA after generated B4 lands",
      "graph_delta": "B4 -> B3",
      "preemption_basis": "graph-bound",
      "route": "RECURSE",
      "next_burden": "B3",
      "owner_route": ["held-route-B3"]
    }
  ],
  "field_diagnostics": {
    "divergence_check": "non-neutral / B3 remains baseline held after generated B4 lands",
    "curl_check": "null"
  },
  "terminal_states": {
    "B1": "landed",
    "B2": "landed",
    "B3": "carried-RECURSE / baseline held",
    "B4": "landed"
  },
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2", "B3"],
    "coverage_complete": false,
    "terminal_states": {"B1": "landed", "B2": "landed", "B3": "carried-RECURSE / baseline held", "B4": "landed"},
    "dependency_graph": {
      "nodes": ["B1", "B2", "B3", "B4"],
      "edges": [["B1", "B2"], ["B2", "B4"], ["B4", "B3"]],
      "roots": ["B1"],
      "acyclic": true
    }
  }
}
