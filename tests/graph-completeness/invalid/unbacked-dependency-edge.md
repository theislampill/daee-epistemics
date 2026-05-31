NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1", "B2"],
  "B_MRP": [],
  "B_total": ["B1", "B2"],
  "nodes": [
    {"id": "B1", "type": "burden", "state": "landed"},
    {"id": "B2", "type": "burden", "state": "landed"}
  ],
  "edges": [
    {"from": "B1", "to": "B2", "type": "invented-edge"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"},
    {"source": "B2", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "formal_reread_states": [
    {"source_burden": "B1", "prior_land": "Land(B1)", "delta": "Delta B1: landed", "reread": "R(H,Delta)", "route_gradient": "STOP", "divergence_state": "neutral", "curl_state": "null", "route_result_type": "no_new_resultant", "mrp_resultant": "stable -> no new graph edge", "graph_delta": "none", "preemption_basis": "none", "route": "STOP"},
    {"source_burden": "B2", "prior_land": "Land(B2)", "delta": "Delta B2: landed", "reread": "R(H,Delta)", "route_gradient": "STOP", "divergence_state": "neutral", "curl_state": "null", "route_result_type": "no_new_resultant", "mrp_resultant": "stable -> no new graph edge", "graph_delta": "none", "preemption_basis": "none", "route": "STOP"}
  ],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "null"},
  "terminal_states": {"B1": "landed", "B2": "landed"},
  "closure": {"status": "coverage_complete=true"},
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M1", "operation": "repair", "pressure": "root", "body_ref": "B1_1", "delta": "Delta B1:landed", "land": "Land(B1)+"},
    {"source": "B2", "target": "B2", "owner": "M8", "operation": "trace", "pressure": "dependency", "body_ref": "B2_1", "delta": "Delta B2:landed", "land": "Land(B2)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2"],
    "terminal_states": {"B1": "landed", "B2": "landed"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [["B1", "B2"]], "roots": ["B1"], "acyclic": true},
    "divergence_check": "neutral",
    "curl_check": "null",
    "max_generation_depth": 0,
    "coverage_complete": true
  }
}
