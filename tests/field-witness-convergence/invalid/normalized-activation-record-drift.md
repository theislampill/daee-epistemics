NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header
- live noetic burden: B1 / root pressure.
- held: B2 / dependent pressure.
- B_LA = {B1, B2}
- B_MRP = {}
- B_total = B_LA union B_MRP
- Initial burden set: [B1, B2]

## Layer B - Bounded Governed Response

## Burden 1 / B1 - root pressure
Matched owner/TTP route: [M1]
Land(B1): root pressure repaired.

## Burden 2 / B2 - released dependent pressure
Matched owner/TTP route: [M8]
Land(B2): dependent pressure landed.

Closure/Reconstruction Witness
Initial burden set: [B1, B2]
B_LA = {B1, B2}
B_MRP = {}
B_total = B_LA union B_MRP
Burden dependency graph:
B1 (root) -> B2
Terminal states:
B1: landed / M1 / root pressure repaired
B2: landed / M8 / dependent pressure landed
MRP resultants:
MRP(B1): type=held_burden_activation; finding=genuine-dependent; graph=B1 -> B2; route=RECURSE
MRP(B2): type=no_new_resultant; finding=stable; graph=none; route=STOP
del-dot B: neutral
del-cross kappa: null
C(PsiN): coverage_complete=true; runtime execution field closed for this bounded reply
T_lang: PsiN -> PsiI: partial coupling boundary; no guaranteed uptake

field_witness
{
  "B_LA": ["B1", "B2"],
  "B_MRP": [],
  "B_total": ["B1", "B2"],
  "nodes": [
    {"id": "B1", "type": "burden", "owners": ["M1"], "state": "landed"},
    {"id": "B2", "type": "burden", "owners": ["M8"], "state": "landed"}
  ],
  "edges": [
    {"from": "B1", "to": "B2", "type": "held_burden_activation"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"},
    {"source": "B2", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "field_diagnostics": {
    "divergence_check": "neutral",
    "curl_check": "null"
  },
  "terminal_states": {
    "B1": "landed",
    "B2": "landed"
  },
  "closure": {
    "status": "coverage_complete=true"
  },
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M1", "operation": "repair", "pressure": "root-pressure", "body_ref": "B1_1", "delta": "Delta B1:root repaired", "land": "Land(B1)+"},
    {"source": "MRP(B1)", "target": "B2", "owner": "M8", "operation": "trace", "pressure": "dependent-pressure", "body_ref": "B2_1", "delta": "Delta B2:dependent landed", "land": "Land(B2)+"}
  ],
  "normalized_activation_record": {
    "n_frame": "fixture-drift-canary",
    "live_registers": [],
    "burden_floor": ["B1", "B2"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "M1", "operation": "repair", "delta_result": "root repaired", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B2", "owner_id": "M1", "operation": "repair", "delta_result": "invented drift", "mrp_route_result_type": "no_new_resultant", "terminal_state": "held-with-reason", "generation_depth": 9}
    ]
  },
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2"],
    "terminal_states": {
      "B1": "landed",
      "B2": "landed"
    },
    "dependency_graph": {
      "nodes": ["B1", "B2"],
      "edges": [["B1", "B2"]],
      "roots": ["B1"],
      "acyclic": true
    },
    "divergence_check": "neutral",
    "curl_check": "null",
    "max_generation_depth": 0,
    "coverage_complete": true
  }
}
