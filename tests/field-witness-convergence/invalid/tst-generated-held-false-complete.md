NOETIC FIELD EXECUTION

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
    {"id": "B4", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "primary"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B4", "route": "HOLD"}
  ],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "resolved"},
  "terminal_states": {
    "B1": "landed",
    "B2": "carried-RECURSE / baseline held",
    "B3": "carried-RECURSE / baseline held",
    "B4": "carried-RECURSE / generated-held unexecuted"
  },
  "closure": {"status": "coverage_complete=true"},
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "FPD", "operation": "expose", "pressure": "moral tribunal filter", "body_ref": "B1_1", "delta": "Delta B1:imported-criterion-blocked", "land": "Land(B1)+"}
  ],
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
