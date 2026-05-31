NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header
- Initial burden set: [B1, B2]
- B_LA = {B1, B2}
- B_MRP = {}
- B_total = B_LA union B_MRP

Closure/Reconstruction Witness
Initial burden set: [B1, B2]
B_LA = {B1, B2}
B_MRP = {}
B_total = [B1, B2]
Terminal states:
B1: landed / M1 / root repaired
MRP resultants:
MRP(B1): type=no_new_resultant; finding=stable; graph=none; route=STOP
del-dot B: neutral
del-cross kappa: null
C(PsiN): coverage_complete=true
T_lang: PsiN -> PsiI: partial boundary

field_witness
{
  "B_LA": ["B1", "B2"],
  "B_MRP": [],
  "B_total": ["B1", "B2"],
  "nodes": [
    {"id": "B1", "type": "burden", "state": "landed"},
    {"id": "B2", "type": "burden", "state": "live"}
  ],
  "edges": [],
  "mrp_resultants": [
    {"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "null"},
  "terminal_states": {"B1": "landed"},
  "closure": {"status": "coverage_complete=true"},
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M1", "operation": "repair", "pressure": "root pressure", "body_ref": "B1_1", "delta": "Delta B1:root repaired", "land": "Land(B1)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1", "B2"], "edges": [], "roots": ["B1"], "acyclic": true},
    "divergence_check": "neutral",
    "curl_check": "null",
    "max_generation_depth": 0,
    "coverage_complete": true
  }
}
