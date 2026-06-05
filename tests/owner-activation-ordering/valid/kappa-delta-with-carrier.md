NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activations": [
    {
      "source": "B1",
      "target": "B1",
      "owner": "source-status-repair",
      "operation": "source-order",
      "pressure": "source-order pressure",
      "body_ref": "B1_1",
      "delta": "Delta-kappa:source-order-repaired",
      "kappa_carrier": "kappa carrier over B1 dependency radius",
      "reread_state_effect": "R(H,Delta) reread binds kappa carrier back to B1 before release",
      "land": "Land(B1)+"
    }
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
