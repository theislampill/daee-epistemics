NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header
- live noetic burden: B1 / root pressure.
- held: B2 / unresolved dependent pressure.
- B_LA = {B1, B2}
- B_MRP = {}
- B_total = B_LA union B_MRP
- Initial burden set: [B1, B2]

## Layer B - Bounded Governed Response

Closure/Reconstruction Witness
Initial burden set: [B1, B2]
B_LA = {B1, B2}
B_MRP = {}
B_total = B_LA union B_MRP
Burden dependency graph: B1 (root) -> B2
Terminal states:
B1: landed / M1 / root pressure repaired
B2: carried-RECURSE / M8 / still live for next pass
del-dot B: non-neutral / B2 remains live
del-cross kappa: null
C(PsiN): coverage_complete=true; runtime execution field closed
T_lang: PsiN -> PsiI: partial coupling boundary

field_witness
{
  "B_LA": ["B1", "B2"],
  "B_MRP": [],
  "B_total": ["B1", "B2"],
  "nodes": [
    {"id": "B1", "type": "burden", "state": "landed"},
    {"id": "B2", "type": "burden", "state": "carried-RECURSE"}
  ],
  "edges": [{"from": "B1", "to": "B2"}],
  "field_diagnostics": {"divergence_check": "non-neutral / B2 remains live", "curl_check": "null"},
  "terminal_states": {"B1": "landed", "B2": "carried-RECURSE / still live"},
  "closure": {"status": "coverage_complete=true"},
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M1", "operation": "repair", "body_ref": "B1_1", "delta": "Delta B1:root repaired", "land": "Land(B1)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2"],
    "terminal_states": {"B1": "landed", "B2": "carried-RECURSE / still live"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [["B1", "B2"]], "roots": ["B1"], "acyclic": true},
    "divergence_check": "non-neutral / B2 remains live",
    "curl_check": "null",
    "coverage_complete": true
  }
}
