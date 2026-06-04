NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1", "B2", "B3"],
  "B_MRP": ["B4"],
  "B_total": ["B1", "B2", "B3", "B4"],
  "generated_burdens": [
    {"id": "B4", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "primary"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B4", "route": "HOLD"}
  ],
  "reread_records": [
    {"source": "B1", "reread": "R(H,Delta)", "release_next": "B4"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: moral tribunal filter exposed; generated TST recoil remains unexecuted.",
      "reread": "R(H,Delta)",
      "route_gradient": "generated B4 absent from B_LA while B2 and B3 remain baseline burdens",
      "divergence_state": "non-neutral",
      "curl_state": "held",
      "route_result_type": "generated_burden_instantiation",
      "mrp_resultant": "genuine-dependent -> instantiate B4 [generated-by: MRP(B1)] and HOLD",
      "graph_delta": "B1 -> B4",
      "preemption_basis": "framework-bound",
      "route": "HOLD",
      "next_burden": "B4",
      "owner_route": ["FPD", "M1-P", "P7"],
      "generated_by": "MRP(B1)",
      "hold_partial_detail": "B4 is generated-held, unexecuted, and carried-RECURSE; coverage_complete=false."
    }
  ],
  "terminal_states": {
    "B1": "landed",
    "B2": "carried-RECURSE / baseline held",
    "B3": "carried-RECURSE / baseline held",
    "B4": "carried-RECURSE / generated-held unexecuted"
  },
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2", "B3"],
    "terminal_states": {
      "B1": "landed",
      "B2": "carried-RECURSE / baseline held",
      "B3": "carried-RECURSE / baseline held",
      "B4": "carried-RECURSE / generated-held unexecuted"
    },
    "dependency_graph": {"nodes": ["B1", "B2", "B3", "B4"], "edges": [["B1", "B4"]], "roots": ["B1", "B2", "B3"], "acyclic": true},
    "coverage_complete": false
  }
}
