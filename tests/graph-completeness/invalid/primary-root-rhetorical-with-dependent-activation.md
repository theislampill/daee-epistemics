NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header
- Initial burden set: [B1]
- B_LA = {B1}
- B_MRP = {B2}
- B_total = B_LA union B_MRP

## Burden 1 / ¹B - primary claim
Land(B1): landed by assertion only.

[Mid-Reread Pressure]
Target: ¹B / primary claim
Reread: R(H,Delta)
Landed delta: Delta B1: asserted.
∇·T: non-neutral / generated reserve remains
∇×T: null / no loop
Finding: genuine-dependent
Route-gradient: B2 generated after asserted root landing.
MRP route result type: generated_burden_instantiation
MRP resultant: genuine-dependent -> instantiate B2 [generated-by: MRP(B1)]
Graph delta: B1 -> B2
Route: RECURSE

## Burden 2 / B2 [generated-by: MRP(B1)] - dependent burden

### B2_1[FPD] - expose dependent reserve
- Target: dependent reserve.
- Operation: expose the reserve criterion.
- Result/state-change: reserve exposed.
- Contribution-to-Land(B2): the dependent burden lands.

The dependent operation is real, but the primary root never received a source-owned owner
activation. The graph must not accept the dependent node as proof that the root landed.

Land(B2): landed / FPD / dependent reserve exposed.

[Mid-Reread Pressure]
Target: B2 / dependent burden
Reread: R(H,Delta)
Landed delta: Delta B2: reserve exposed.
∇·T: neutral / no live generated burden remains
∇×T: null / no loop
Finding: stable
Route-gradient: STOP
MRP route result type: no_new_resultant
MRP resultant: stable -> no new graph edge
Graph delta: none
Route: STOP

## Restorative Response
The dependent reserve is named, but the primary root was never verified.

## Closing Formulation
This fixture must fail because root Land(B1) is rhetorical.

## field_witness
```json
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1", "B2"],
  "nodes": [
    {"id": "B1", "type": "burden", "state": "landed"},
    {"id": "B2", "type": "generated_burden", "generated_by": "MRP(B1)", "generation_depth": 1, "state": "landed"}
  ],
  "edges": [{"from": "B1", "to": "B2"}],
  "generated_burdens": [
    {"id": "B2", "generated_by": "MRP(B1)", "generation_depth": 1}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"},
    {"source": "B2", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Delta B1: asserted.",
      "reread": "R(H,Delta)",
      "route_gradient": "B2 generated after asserted root landing.",
      "divergence_state": "non-neutral",
      "curl_state": "null",
      "route_result_type": "generated_burden_instantiation",
      "mrp_resultant": "genuine-dependent -> instantiate B2 [generated-by: MRP(B1)]",
      "graph_delta": "B1 -> B2",
      "preemption_basis": "framework-bound",
      "route": "RECURSE",
      "next_burden": "B2",
      "owner_route": ["FPD"],
      "generated_by": "MRP(B1)"
    },
    {
      "source_burden": "B2",
      "prior_land": "Land(B2)",
      "delta": "Delta B2: reserve exposed.",
      "reread": "R(H,Delta)",
      "route_gradient": "STOP",
      "divergence_state": "neutral",
      "curl_state": "null",
      "route_result_type": "no_new_resultant",
      "mrp_resultant": "stable -> no new graph edge",
      "graph_delta": "none",
      "preemption_basis": "none",
      "route": "STOP"
    }
  ],
  "field_diagnostics": {"divergence_check": "neutral", "curl_check": "null"},
  "terminal_states": {"B1": "landed", "B2": "landed"},
  "closure": {"status": "coverage_complete=true"},
  "owner_activations": [
    {"source": "MRP(B1)", "target": "B2", "owner": "FPD", "operation": "expose", "pressure": "dependent reserve", "body_ref": "B2_1", "delta": "Delta B2:reserve exposed", "land": "Land(B2)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed", "B2": "landed"},
    "dependency_graph": {
      "nodes": ["B1", "B2"],
      "edges": [["B1", "B2"]],
      "roots": ["B1"],
      "acyclic": true
    },
    "divergence_check": "neutral",
    "curl_check": "null",
    "max_generation_depth": 1,
    "coverage_complete": true
  }
}
```
