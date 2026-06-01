NOETIC FIELD EXECUTION

## Layer A - Diagnostic IR

N-frame: generated-reserve-full-ir-decode
live registers: [xi, kappa]

## Layer B - Bounded Governed Response

## Burden 1 / B1 - local criterion repair
Matched owner/TTP route: [M7]
ACT records:
⟦ACT B1_1[M7.anchor] :: π=local criterion :: body_ref=B1_1 :: Δ=ΔB1:criterion anchored :: Land(B1)+⟧

#### Layer B - Governed Operation Body

### B1_1[M7] - anchor the criterion
Target: local criterion.
Operation: anchor the local criterion before it controls closure.
Result/state-change: criterion anchored
Contribution-to-Land(B1): the local criterion is anchored before reread.

TTP Operation Body:
The M7 operation anchors the local criterion and prevents it from controlling closure invisibly.

Land(B1): landed.

[Mid-Reread Pressure]
Target: B1 / local criterion repair
Reread: R(H,Delta)
Landed delta: Delta B1: criterion anchored, and reread detects generated reserve pressure.
Pressure activations:
- hidden-framework-recoil: FPD - reserve criterion is visible after Land(B1)
- entailment-pressure: P7 - stop and reopen condition must be bounded
divergence: non-neutral / generated reserve pressure remains
curl: null / directed dependency rather than loop
Finding: genuine-dependent
Route-gradient: gradient points to B2 [generated-by: MRP(B1)] because Delta B1 exposed reserve pressure absent from B_LA.
MRP route result type: generated_burden_instantiation
MRP resultant: genuine-dependent -> instantiate B2 [generated-by: MRP(B1)] and route RECURSE
Graph delta: B1 -> B2
Pre-emption basis: framework-bound
Route: RECURSE

## Burden 2 / B2 [generated-by: MRP(B1)] - generated reserve-immunity recoil
Matched owner/TTP route: [FPD, P7]
ACT records:
⟦ACT B2_1[FPD.expose] :: π=reserve criterion :: body_ref=B2_1 :: Δ=ΔB2:reserve criterion exposed :: Land(B2)+⟧
⟦ACT B2_2[P7.bound] :: π=proof-carousel pressure :: body_ref=B2_2 :: Δ=ΔB2:scoped stop condition licensed :: Land(B2)+⟧

#### Layer B - Governed Operation Body

### B2_1[FPD] - expose the reserve criterion
Target: reserve criterion.
Operation: expose the reserve criterion and require it to become a stated burden.
Result/state-change: reserve criterion exposed
Contribution-to-Land(B2): the generated node can no longer protect B1 invisibly.

TTP Operation Body:
The FPD operation exposes the reserve criterion as imported support and turns the hidden rule into a visible burden.

### B2_2[P7] - bind the stop and reopen condition
Target: proof-carousel pressure.
Operation: bound the proof-carousel pressure by defining STOP and reopen conditions.
Result/state-change: scoped stop condition licensed
Contribution-to-Land(B2): closure becomes available for the worked claim while future reserve routes remain possible as new burdens.

TTP Operation Body:
The P7 operation bounds the proof-carousel pressure and names the condition required to reopen the route.

Land(B2): landed.

[Mid-Reread Pressure]
Target: B2 / generated reserve-immunity recoil
Reread: R(H,Delta)
Landed delta: Delta B2: generated recoil landed and reopen conditions recorded.
Pressure activations:
- hidden-framework-recoil: pressure class cleared - reserve criterion exposed
- proof-carousel: pressure class cleared - stop condition licensed
divergence: neutral / no live generated burden remains
curl: null / no loop
Finding: stable
Route-gradient: gradient points to STOP because B_LA and B_MRP are landed for this scoped fixture.
MRP route result type: no_new_resultant
MRP resultant: stable -> no new graph edge
Graph delta: none
Pre-emption basis: none
Route: STOP

## Restorative Response
The generated reserve is exposed and bounded, so the response can release from fitrah and sound reason orientation without claiming guaranteed uptake.

## Closing Formulation
Established failure: the reserve criterion can no longer govern closure invisibly.
Restored criterion/orientation: fitrah and sound reason remain the release orientation.
Scoped boundary: future reserve material would need a new routed burden.

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1", "B2"],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M7", "operation": "anchor", "pressure": "local criterion", "body_ref": "B1_1", "delta": "ΔB1:criterion anchored", "land": "Land(B1)+"},
    {"source": "MRP(B1)", "target": "B2", "owner": "FPD", "operation": "expose", "pressure": "reserve criterion", "body_ref": "B2_1", "delta": "ΔB2:reserve criterion exposed", "land": "Land(B2)+"},
    {"source": "MRP(B1)", "target": "B2", "owner": "P7", "operation": "bound", "pressure": "proof-carousel pressure", "body_ref": "B2_2", "delta": "ΔB2:scoped stop condition licensed", "land": "Land(B2)+"}
  ],
  "generated_burdens": [
    {"id": "B2", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "primary", "reason": "reserve pressure remained after B1 landed"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed", "B2": "landed"},
    "dependency_graph": {
      "nodes": ["B1", "B2"],
      "edges": [{"from": "B1", "to": "B2"}],
      "roots": ["B1"],
      "acyclic": true
    },
    "diagnostic_completeness": {
      "live_registers": ["xi", "kappa"],
      "coverage": {"xi": ["B1"], "kappa": ["B1"]},
      "complete": true
    },
    "divergence_check": "neutral",
    "curl_check": "null",
    "coverage_complete": true
  },
  "normalized_activation_record": {
    "n_frame": "generated-reserve-full-ir-decode",
    "live_registers": ["xi", "kappa"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "M7", "operation": "anchor", "delta_result": "criterion anchored", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B2", "owner_id": "FPD", "operation": "expose", "delta_result": "reserve criterion exposed", "mrp_route_result_type": "generated_burden_instantiation", "terminal_state": "landed", "generation_depth": 1},
      {"burden_id": "B2", "owner_id": "P7", "operation": "bound", "delta_result": "scoped stop condition licensed", "mrp_route_result_type": "generated_burden_instantiation", "terminal_state": "landed", "generation_depth": 1}
    ]
  },
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: criterion anchored, and reread detects generated reserve pressure.",
      "reread": "R(H,Delta)",
      "route_gradient": "gradient points to B2 [generated-by: MRP(B1)] because Delta B1 exposed reserve pressure absent from B_LA.",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "generated_burden_instantiation",
      "mrp_resultant": "genuine-dependent -> instantiate B2 [generated-by: MRP(B1)] and route RECURSE",
      "graph_delta": "B1 -> B2",
      "preemption_basis": "framework-bound",
      "route": "RECURSE",
      "next_burden": "B2",
      "owner_route": ["FPD", "P7"],
      "generated_by": "MRP(B1)",
      "escape_routes_checked": [
        {"type": "hidden-framework-recoil", "live": true, "disposition": "generated_burden_instantiation", "target_burden": "B2", "basis": "After Land(B1), R(H,Delta) exposes framework-bound reserve pressure."}
      ]
    },
    {
      "source_burden": "B2",
      "prior_land": "Land(B2)",
      "delta": "Delta B2: generated recoil landed and reopen conditions recorded.",
      "reread": "R(H,Delta)",
      "route_gradient": "gradient points to STOP because B_LA and B_MRP are landed for this scoped fixture.",
      "divergence_state": "neutral",
      "curl_state": "null",
      "route_result_type": "no_new_resultant",
      "mrp_resultant": "stable -> no new graph edge",
      "graph_delta": "none",
      "preemption_basis": "none",
      "route": "STOP",
      "escape_routes_checked": [
        {"type": "closure-boundary-immunity", "live": false, "basis": "B2 bounded the generated reserve-immunity recoil."},
        {"type": "proof-carousel", "live": false, "basis": "P7 recorded scoped stop and reopen conditions."},
        {"type": "hidden-framework-recoil", "live": false, "basis": "FPD exposed the reserve criterion carried by B2."}
      ],
      "no_new_resultant_proof": {
        "escape_routes_checked": [
          {"type": "closure-boundary-immunity", "live": false, "basis": "B2 bounded the generated reserve-immunity recoil."},
          {"type": "proof-carousel", "live": false, "basis": "P7 recorded scoped stop and reopen conditions."},
          {"type": "hidden-framework-recoil", "live": false, "basis": "FPD exposed the reserve criterion carried by B2."}
        ],
        "field_state_at_stop": {"divergence": "neutral", "curl": "null", "b_live": "empty", "kappa_residual": 0},
        "stop_licensed": true
      }
    }
  ],
  "canonical_ir_projection": {
    "schema": "b5-canonical-ir-projection-v1",
    "n_frame": "generated-reserve-full-ir-decode",
    "live_registers": ["xi", "kappa"],
    "burden_floor": ["B1"],
    "per_burden": [
      {"burden_id": "B1", "owner_id": "M7", "operation": "anchor", "delta_result": "criterion anchored", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
      {"burden_id": "B2", "owner_id": "FPD", "operation": "expose", "delta_result": "reserve criterion exposed", "mrp_route_result_type": "generated_burden_instantiation", "terminal_state": "landed", "generation_depth": 1},
      {"burden_id": "B2", "owner_id": "P7", "operation": "bound", "delta_result": "scoped stop condition licensed", "mrp_route_result_type": "generated_burden_instantiation", "terminal_state": "landed", "generation_depth": 1}
    ],
    "diagnostic_completeness": {
      "live_registers": ["xi", "kappa"],
      "coverage": {"xi": ["B1"], "kappa": ["B1"]},
      "complete": true
    },
    "decoded_ir": {
      "schema": "b5-canonical-ir-decode-v1",
      "source_evidence": ["visible_act", "field_witness.owner_activations", "normalized_activation_record", "canonical_ir_projection"],
      "n_frame": "generated-reserve-full-ir-decode",
      "live_registers": ["xi", "kappa"],
      "burden_floor": ["B1"],
      "per_burden": [
        {"burden_id": "B1", "owner_id": "M7", "operation": "anchor", "pressure": "local criterion", "body_ref": "B1_1", "delta_result": "criterion anchored", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0},
        {"burden_id": "B2", "owner_id": "FPD", "operation": "expose", "pressure": "reserve criterion", "body_ref": "B2_1", "delta_result": "reserve criterion exposed", "mrp_route_result_type": "generated_burden_instantiation", "terminal_state": "landed", "generation_depth": 1},
        {"burden_id": "B2", "owner_id": "P7", "operation": "bound", "pressure": "proof-carousel pressure", "body_ref": "B2_2", "delta_result": "scoped stop condition licensed", "mrp_route_result_type": "generated_burden_instantiation", "terminal_state": "landed", "generation_depth": 1}
      ],
      "diagnostic_completeness": {
        "live_registers": ["xi", "kappa"],
        "coverage": {"xi": ["B1"], "kappa": ["B1"]},
        "complete": true
      }
    },
    "full_ir_decode": {
      "schema": "b5-full-ir-decode-v1",
      "source_evidence": ["visible_act", "field_witness.owner_activations", "normalized_activation_record", "canonical_ir_projection", "canonical_ir_projection.decoded_ir", "field_witness.coverage_proof", "field_witness.coverage_proof.dependency_graph", "field_witness.generated_burdens", "field_witness.formal_reread_states"],
      "n_frame": "generated-reserve-full-ir-decode",
      "live_registers": ["xi", "kappa"],
      "burden_floor": ["B1"],
      "B_LA": ["B1"],
      "B_MRP": ["B2"],
      "B_total": ["B1", "B2"],
      "dependency_graph": {"nodes": ["B1", "B2"], "edges": [{"from": "B1", "to": "B2"}], "roots": ["B1"], "acyclic": true},
      "terminal_states": {"B1": "landed", "B2": "landed"},
      "diagnostic_completeness": {"live_registers": ["xi", "kappa"], "coverage": {"xi": ["B1"], "kappa": ["B1"]}, "complete": true},
      "per_burden": [
        {"burden_id": "B1", "owner_id": "M7", "operation": "anchor", "pressure": "local criterion", "body_ref": "B1_1", "delta_result": "criterion anchored", "mrp_route_result_type": "held_burden_activation", "terminal_state": "landed", "generation_depth": 0, "graph_role": "root", "generated_by": null, "track": "baseline"},
        {"burden_id": "B2", "owner_id": "FPD", "operation": "expose", "pressure": "reserve criterion", "body_ref": "B2_1", "delta_result": "reserve criterion exposed", "mrp_route_result_type": "generated_burden_instantiation", "terminal_state": "landed", "generation_depth": 1, "graph_role": "dependent", "generated_by": "MRP(B1)", "track": "primary"},
        {"burden_id": "B2", "owner_id": "P7", "operation": "bound", "pressure": "proof-carousel pressure", "body_ref": "B2_2", "delta_result": "scoped stop condition licensed", "mrp_route_result_type": "generated_burden_instantiation", "terminal_state": "landed", "generation_depth": 1, "graph_role": "dependent", "generated_by": "MRP(B1)", "track": "primary"}
      ],
      "generated_burdens": [{"id": "B2", "generated_by": "MRP(B1)", "generation_depth": 1, "track": "primary", "reason": "reserve pressure remained after B1 landed"}],
      "formal_reread": {
        "states_present": true,
        "divergence_state": "neutral",
        "curl_state": "null",
        "escape_routes_checked": [
          {"type": "hidden-framework-recoil", "live": true, "disposition": "generated_burden_instantiation", "target_burden": "B2", "basis": "After Land(B1), R(H,Delta) exposes framework-bound reserve pressure."},
          {"type": "closure-boundary-immunity", "live": false, "basis": "B2 bounded the generated reserve-immunity recoil."},
          {"type": "proof-carousel", "live": false, "basis": "P7 recorded scoped stop and reopen conditions."},
          {"type": "hidden-framework-recoil", "live": false, "basis": "FPD exposed the reserve criterion carried by B2."}
        ],
        "no_new_resultant_proof": {
          "escape_routes_checked": [
            {"type": "closure-boundary-immunity", "live": false, "basis": "B2 bounded the generated reserve-immunity recoil."},
            {"type": "proof-carousel", "live": false, "basis": "P7 recorded scoped stop and reopen conditions."},
            {"type": "hidden-framework-recoil", "live": false, "basis": "FPD exposed the reserve criterion carried by B2."}
          ],
          "field_state_at_stop": {"divergence": "neutral", "curl": "null", "b_live": "empty", "kappa_residual": 0},
          "stop_licensed": true
        }
      },
      "source_basis": {
        "source_basis_available": false,
        "sigma_inside_hard_registers": false,
        "basis": ["no explicit source_basis object is emitted in this schema-light fixture"]
      }
    }
  }
}
