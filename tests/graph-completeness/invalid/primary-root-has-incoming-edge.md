NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1", "B2"],
  "nodes": [
    {"id": "B1", "type": "burden", "state": "landed"},
    {"id": "B2", "type": "generated_burden", "generated_by": "MRP(B1)", "generation_depth": 1, "state": "landed"}
  ],
  "edges": [{"from": "B2", "to": "B1"}],
  "generated_burdens": [{"id": "B2", "generated_by": "MRP(B1)", "generation_depth": 1}],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"},
    {"source": "B2", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "null"},
  "terminal_states": {"B1": "landed", "B2": "landed"},
  "closure": {"status": "coverage_complete=true"},
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M1", "operation": "repair", "pressure": "root pressure", "body_ref": "B1_1", "delta": "Delta B1:root repaired", "land": "Land(B1)+"},
    {"source": "MRP(B1)", "target": "B2", "owner": "FPD", "operation": "expose", "pressure": "dependent reserve", "body_ref": "B2_1", "delta": "Delta B2:reserve exposed", "land": "Land(B2)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed", "B2": "landed"},
    "dependency_graph": {
      "nodes": ["B1", "B2"],
      "edges": [["B2", "B1"]],
      "roots": ["B2"],
      "acyclic": true
    },
    "divergence_check": "neutral",
    "curl_check": "null",
    "max_generation_depth": 1,
    "coverage_complete": true
  }
}
