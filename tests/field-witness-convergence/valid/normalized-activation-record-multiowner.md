NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header
- live registers: xi and kappa are live.
- live noetic burden: B1 / authority tribunal.
- held: B2 / dependency chain.
- B_LA = {B1, B2}
- B_MRP = {}
- B_total = B_LA union B_MRP
- Initial burden set: [B1, B2]

## Layer B - Bounded Governed Response

## Burden 1 / B1 - authority tribunal
Matched owner/TTP route: [FPD, M1]
Land(B1): authority tribunal blocked and self-authorizing standard invalidated.

## Burden 2 / B2 - dependency chain
Matched owner/TTP route: [M8]
Land(B2): dependency chain exposed.

Restorative Response

The scoped pass accounts for the authority and dependency pressures.

Closing Formulation

Closure is local to the accounted register floor.

Closure/Reconstruction Witness
Initial burden set: [B1, B2]
B_LA = {B1, B2}
B_MRP = {}
B_total = B_LA union B_MRP
Burden dependency graph:
B1 (root) -> B2
Terminal states:
B1: landed / FPD-M1 / authority tribunal blocked and self-authorizing standard invalidated
B2: landed / M8 / dependency chain exposed
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
    {"id": "B1", "type": "burden", "title": "authority tribunal", "register_types": ["xi"], "state": "landed"},
    {"id": "B2", "type": "burden", "title": "dependency chain", "register_types": ["kappa"], "state": "landed"}
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
    {"source": "B1", "target": "B1", "owner": "FPD", "operation": "foreign-premise-detection", "pressure": "authority", "body_ref": "B1_1", "delta": "Delta B1:authority tribunal blocked", "land": "Land(B1)+"},
    {"source": "B1", "target": "B1", "owner": "M1", "operation": "self-grounding-test", "pressure": "authority", "body_ref": "B1_2", "delta": "Delta B1:self-authorizing standard invalidated", "land": "Land(B1)+"},
    {"source": "MRP(B1)", "target": "B2", "owner": "M8", "operation": "consequence-trace", "pressure": "dependency", "body_ref": "B2_1", "delta": "Delta B2:dependency exposed", "land": "Land(B2)+"}
  ],
  "normalized_activation_record": {
    "n_frame": "fixture-multiowner-nar",
    "live_registers": ["xi", "kappa"],
    "burden_floor": ["B1", "B2"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "FPD", "operation": "foreign-premise-detection", "delta_result": "authority tribunal blocked", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B1", "owner_id": "M1", "operation": "self-grounding-test", "delta_result": "self-authorizing standard invalidated", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B2", "owner_id": "M8", "operation": "consequence-trace", "delta_result": "dependency exposed", "mrp_route_result_type": "no_new_resultant", "terminal_state": "landed", "generation_depth": 0}
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
    "diagnostic_completeness": {
      "live_registers": ["xi", "kappa"],
      "coverage": {
        "xi": ["B1"],
        "kappa": ["B2"]
      },
      "complete": true
    },
    "divergence_check": "neutral",
    "curl_check": "null",
    "max_generation_depth": 0,
    "coverage_complete": true
  }
}
