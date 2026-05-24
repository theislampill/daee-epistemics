NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1"],
  "generated_burdens": [
    {"id": "B2", "generated_by": "MRP(B1)", "reason": "post-land pressure"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"}
  ],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M9", "operation": "repair", "pressure": "predicate-transfer", "body_ref": "B1_1", "delta": "Delta B1:predicate transfer blocked", "land": "Land(B1)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
