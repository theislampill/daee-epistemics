NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header
- live registers: xi and kappa are live.
- live noetic burden: B1 / opening pressure.
- held: B2 / mid-chain baseline burden; B3 / later baseline burden.
- B_LA = {B1, B2, B3}
- B_MRP = {B4}
- B_total = B_LA union B_MRP
- Initial burden set: [B1, B2, B3]

## Layer B - Bounded Governed Response

## Burden 1 / B1 - opening pressure
Matched owner/TTP route: [M8]
Land(B1): opening pressure landed.

## Burden 2 / B2 - mid-chain pressure
Matched owner/TTP route: [FPD]
Land(B2): mid-chain pressure landed and exposed a generated recoil.

## Burden 4 / B4 [generated-by: MRP(B2)] - generated source-worldview recoil
Matched owner/TTP route: [FPD, P7]
Land(B4): generated recoil executed and landed before returning to the later baseline burden.

Restorative Response

The generated burden is not treated as final merely because it came from the mid-chain parent; B3 remains a baseline Layer-A burden.

Closing Formulation

Closure remains HOLD/PARTIAL because B3 is still carried after the generated B4 execution.

Closure/Reconstruction Witness
B_total = {B1, B2, B3, B4}
Initial burden set: [B1, B2, B3]
B_LA = {B1, B2, B3}
B_MRP = {B4}
Burden dependency graph:
B1 (root)
B1 -> B2
B2 -> B4
B4 -> B3
Terminal states:
B1: landed / M8 / opening pressure landed
B2: landed / FPD / mid-chain pressure landed
B3: carried-RECURSE / later baseline burden remains held
B4: landed / FPD + P7 / generated source-worldview recoil executed
MRP resultants:
MRP(B1): type=held_burden_activation; finding=genuine-dependent; graph=B1 -> B2; route=RECURSE
MRP(B2): type=generated_burden_instantiation; finding=genuine-dependent; graph=B2 -> B4; route=RECURSE
MRP(B4): type=held_burden_activation; finding=genuine-dependent; graph=B4 -> B3; route=RECURSE
del-dot B: non-neutral / B3 remains baseline held after generated B4 lands
del-cross kappa: null
C(PsiN): coverage_complete=false; generated B4 is executed but not final
T_lang: PsiN -> PsiI: partial coupling boundary; no guaranteed uptake

field_witness
{
  "B_LA": ["B1", "B2", "B3"],
  "B_MRP": ["B4"],
  "B_total": ["B1", "B2", "B3", "B4"],
  "nodes": [
    {"id": "B1", "type": "burden", "title": "opening pressure", "register_types": ["xi"], "state": "landed"},
    {"id": "B2", "type": "burden", "title": "mid-chain pressure", "register_types": ["xi"], "state": "landed"},
    {"id": "B3", "type": "burden", "title": "later baseline burden", "register_types": ["kappa"], "state": "carried-RECURSE"},
    {"id": "B4", "type": "generated_burden", "title": "generated source-worldview recoil", "register_types": ["xi"], "generated_by": "MRP(B2)", "generation_depth": 1, "track": "primary", "state": "landed"}
  ],
  "edges": [
    {"from": "B1", "to": "B2", "type": "held_burden_activation"},
    {"from": "B2", "to": "B4", "type": "generated_burden_instantiation"},
    {"from": "B4", "to": "B3", "type": "held_burden_activation"}
  ],
  "generated_burdens": [
    {"id": "B4", "generated_by": "MRP(B2)", "generation_depth": 1, "track": "primary", "reason": "mid-chain source-worldview recoil after B2 landed"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"},
    {"source": "B2", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B2 -> B4", "route": "RECURSE"},
    {"source": "B4", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B4 -> B3", "route": "RECURSE"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: opening pressure landed",
      "reread": "R(H,Delta)",
      "route_gradient": "already-held B2 from B_LA; release B2",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "held_burden_activation",
      "mrp_resultant": "genuine-dependent -> release B2",
      "graph_delta": "B1 -> B2",
      "preemption_basis": "graph-bound",
      "route": "RECURSE",
      "next_burden": "B2",
      "owner_route": ["M8"]
    },
    {
      "source_burden": "B2",
      "prior_land": "Land(B2)",
      "delta": "Delta B2: mid-chain pressure landed and exposed source-worldview recoil",
      "reread": "R(H,Delta)",
      "route_gradient": "newly generated B4 absent from B_LA by MRP(B2) while later baseline B3 remains initial-held",
      "divergence_state": "non-neutral",
      "curl_state": "held",
      "route_result_type": "generated_burden_instantiation",
      "mrp_resultant": "genuine-dependent -> instantiate B4 [generated-by: MRP(B2)] and route RECURSE",
      "graph_delta": "B2 -> B4",
      "preemption_basis": "framework-bound",
      "route": "RECURSE",
      "next_burden": "B4",
      "generated_by": "MRP(B2)",
      "owner_route": ["FPD", "P7"]
    },
    {
      "source_burden": "B4",
      "prior_land": "Land(B4)",
      "delta": "Delta B4: generated source-worldview recoil executed and landed",
      "reread": "R(H,Delta)",
      "route_gradient": "already-held B3 from B_LA remains after generated B4 lands; release B3 instead of treating B4 as final",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "held_burden_activation",
      "mrp_resultant": "genuine-dependent -> release B3 from B_LA after generated B4 lands",
      "graph_delta": "B4 -> B3",
      "preemption_basis": "graph-bound",
      "route": "RECURSE",
      "next_burden": "B3",
      "owner_route": ["held-route-B3"]
    }
  ],
  "field_diagnostics": {
    "divergence_check": "non-neutral / B3 remains baseline held after generated B4 lands",
    "curl_check": "null"
  },
  "terminal_states": {
    "B1": "landed",
    "B2": "landed",
    "B3": "carried-RECURSE / baseline held",
    "B4": "landed"
  },
  "closure": {"status": "coverage_complete=false"},
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M8", "operation": "trace", "pressure": "opening pressure", "body_ref": "B1_1", "delta": "Delta B1:opening pressure landed", "land": "Land(B1)+"},
    {"source": "B2", "target": "B2", "owner": "FPD", "operation": "expose", "pressure": "mid-chain pressure", "body_ref": "B2_1", "delta": "Delta B2:mid-chain pressure exposed", "land": "Land(B2)+"},
    {"source": "MRP(B2)", "target": "B4", "owner": "FPD", "operation": "expose", "pressure": "generated recoil", "body_ref": "B4_1", "delta": "Delta B4:generated recoil exposed", "land": "Land(B4)+"},
    {"source": "MRP(B2)", "target": "B4", "owner": "P7", "operation": "bound", "pressure": "generated recoil", "body_ref": "B4_2", "delta": "Delta B4:generated recoil bounded", "land": "Land(B4)+"}
  ],
  "normalized_activation_record": {
    "n_frame": "fixture-mid-generated-executed",
    "live_registers": ["xi", "kappa"],
    "burden_floor": ["B1", "B2", "B3"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "M8", "operation": "trace", "delta_result": "opening pressure landed", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B2", "owner_id": "FPD", "operation": "expose", "delta_result": "mid-chain pressure exposed", "mrp_route_result_type": "generated_burden_instantiation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B3", "owner_id": "P7", "operation": "hold", "delta_result": "held-route-bounded", "mrp_route_result_type": "held_burden_activation", "terminal_state": "carried-RECURSE", "generation_depth": 0},
      {"burden_id": "B4", "owner_id": "FPD", "operation": "expose", "delta_result": "generated recoil exposed", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 1},
      {"burden_id": "B4", "owner_id": "P7", "operation": "bound", "delta_result": "generated recoil bounded", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 1}
    ]
  },
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2", "B3"],
    "terminal_states": {
      "B1": "landed",
      "B2": "landed",
      "B3": "carried-RECURSE / baseline held",
      "B4": "landed"
    },
    "dependency_graph": {"nodes": ["B1", "B2", "B3", "B4"], "edges": [["B1", "B2"], ["B2", "B4"], ["B4", "B3"]], "roots": ["B1"], "acyclic": true},
    "diagnostic_completeness": {
      "live_registers": ["xi", "kappa"],
      "coverage": {"xi": ["B1", "B2"], "kappa": ["B3"]},
      "complete": true
    },
    "divergence_check": "non-neutral / B3 remains baseline held after generated B4 lands",
    "curl_check": "null",
    "max_generation_depth": 1,
    "coverage_complete": false
  }
}
