NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "nodes": [{"id": "B1", "type": "burden", "state": "landed"}],
  "edges": [],
  "mrp_resultants": [{"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "null"},
  "terminal_states": {"B1": "landed"},
  "closure": {"status": "coverage_complete=true"},
  "owner_activations": [],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true},
    "divergence_check": "neutral",
    "curl_check": "null",
    "max_generation_depth": 0,
    "coverage_complete": true
  }
}
