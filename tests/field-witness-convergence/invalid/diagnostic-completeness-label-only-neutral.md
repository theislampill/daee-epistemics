NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header
- live noetic burden: xi is live.
- B_LA = {B1}
- B_MRP = {}
- B_total = B_LA union B_MRP
- Initial burden set: [B1]

## Layer B - Bounded Governed Response
Land(B1): authority tribunal landed.

Closure/Reconstruction Witness
Initial burden set: [B1]
B_LA = {B1}
B_MRP = {}
B_total = B_LA union B_MRP
Burden dependency graph:
B1 (root)
Terminal states:
B1: landed / FPD / authority tribunal landed
MRP resultants:
MRP(B1): type=no_new_resultant; finding=stable; graph=none; route=STOP
del-dot B: neutral
del-cross kappa: null
C(PsiN): coverage_complete=true

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "nodes": [
    {"id": "B1", "type": "burden", "title": "authority tribunal", "state": "landed"}
  ],
  "edges": [],
  "mrp_resultants": [
    {"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "null"},
  "terminal_states": {"B1": "landed"},
  "closure": {"status": "coverage_complete=true"},
  "owner_activations": [{"target": "B1"}],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": []},
    "diagnostic_completeness": {
      "complete": true,
      "live_registers": ["xi"],
      "coverage": {"xi": ["B1"]}
    },
    "divergence_check": "neutral",
    "curl_check": "null",
    "coverage_complete": true
  }
}
