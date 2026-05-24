NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1", "B2"],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"}
  ],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M9", "operation": "repair", "pressure": "predicate-transfer", "body_ref": "B1_1", "delta": "Delta B1:predicate transfer blocked", "land": "Land(B1)+"},
    {"source": "MRP(B1)", "target": "B2", "owner": "P7", "operation": "bound", "pressure": "boundary-pressure", "body_ref": "B2_1", "delta": "Delta B2:boundary held", "land": "Land(B2)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed", "B2": "landed"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [["B1", "B2"]], "roots": ["B1"], "acyclic": true}
  }
}
