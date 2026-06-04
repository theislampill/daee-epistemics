NOETIC FIELD EXECUTION

Closure/Reconstruction Witness
B_LA = {B1, B2, B3}
B_MRP = {B4}
B_total = B_LA union B_MRP
Terminal states:
B1: landed
B2: carried-RECURSE
B3: carried-RECURSE
B4: carried-RECURSE / generated-held unexecuted
C(PsiN): coverage_complete=true

field_witness
{
  "B_LA": ["B1", "B2", "B3"],
  "B_MRP": ["B4"],
  "B_total": ["B1", "B2", "B3", "B4"],
  "nodes": [
    {"id": "B1", "type": "burden", "state": "landed"},
    {"id": "B2", "type": "burden", "state": "carried-RECURSE"},
    {"id": "B3", "type": "burden", "state": "carried-RECURSE"},
    {"id": "B4", "type": "generated_burden", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "primary", "state": "carried-RECURSE"}
  ],
  "edges": [{"from": "B1", "to": "B4", "type": "generated_burden_instantiation"}],
  "generated_burdens": [
    {"id": "B4", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "primary", "reason": "TST proof-carousel recoil remains unexecuted"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B4", "route": "HOLD"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: generated recoil remains live.",
      "reread": "R(H,Delta)",
      "route_gradient": "generated B4 remains live",
      "divergence_state": "non-neutral",
      "curl_state": "held",
      "route_result_type": "generated_burden_instantiation",
      "mrp_resultant": "genuine-dependent -> instantiate B4 and HOLD",
      "graph_delta": "B1 -> B4",
      "preemption_basis": "framework-bound",
      "route": "HOLD",
      "next_burden": "B4",
      "owner_route": ["FPD", "M1-P", "P7"],
      "generated_by": "MRP(B1)",
      "hold_partial_detail": "B4 remains live and unexecuted."
    }
  ],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "resolved"},
  "terminal_states": {
    "B1": "landed",
    "B2": "carried-RECURSE / baseline held",
    "B3": "carried-RECURSE / baseline held",
    "B4": "carried-RECURSE / generated-held unexecuted"
  },
  "closure": {"status": "coverage_complete=true"},
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2", "B3"],
    "terminal_states": {
      "B1": "landed",
      "B2": "carried-RECURSE / baseline held",
      "B3": "carried-RECURSE / baseline held",
      "B4": "carried-RECURSE / generated-held unexecuted"
    },
    "dependency_graph": {"nodes": ["B1", "B2", "B3", "B4"], "edges": [["B1", "B4"]], "roots": ["B1"], "acyclic": true},
    "divergence_check": "neutral",
    "curl_check": "resolved",
    "max_generation_depth": 1,
    "coverage_complete": true
  }
}
