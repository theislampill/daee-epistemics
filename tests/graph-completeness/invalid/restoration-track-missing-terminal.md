NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1", "B2"],
  "nodes": [
    {"id": "B1", "type": "burden", "state": "landed"},
    {"id": "B2", "type": "generated_burden", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "restoration", "state": "live"}
  ],
  "edges": [{"from": "B1", "to": "B2", "type": "generated_burden_instantiation"}],
  "generated_burdens": [{"id": "B2", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "restoration"}],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: restoration recoil appears.",
      "reread": "R(H,Delta)",
      "route_gradient": "B2",
      "route_result_type": "generated_burden_instantiation",
      "mrp_resultant": "instantiate B2",
      "route": "RECURSE",
      "escape_routes_checked": [
        {"type": "restoration-recoil", "subtype": "scope-protest", "live": true, "disposition": "generated_burden_instantiation", "target_burden": "B2", "owner_family": "P7", "basis": "After Land(B1), Delta B1 and R(H,Delta) show restoration recoil generating B2."}
      ]
    }
  ],
  "field_diagnostics": {"divergence_check": "non-neutral", "curl_check": "null"},
  "terminal_states": {"B1": "landed"},
  "closure": {"status": "coverage_complete=false"},
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M1", "operation": "repair", "pressure": "root", "body_ref": "B1_1", "delta": "Delta B1:landed", "land": "Land(B1)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [["B1", "B2"]], "roots": ["B1"], "acyclic": true},
    "divergence_check": "non-neutral",
    "curl_check": "null",
    "max_generation_depth": 1,
    "coverage_complete": false
  }
}
