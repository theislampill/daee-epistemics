daee-epistemics — NOETIC FIELD EXECUTION

## Layer A — Compact DSL/IR Header
- Initial burden set: [¹B]
- B_LA = [B1]
- B_MRP = []

## Burden 1 / ¹B: Entailment pressure

Matched owner/TTP route: [M8]
- ACT records:
  ⟦ACT ¹B₁[M8.dependency-exposure] :: π=entailment-pressure :: body_ref=¹B₁ :: Δ=Δ¹B:dependency-exposed :: Land(¹B)+⟧

Layer B — Governed Operation Body

¹B₁[M8] — expose dependency
- Target: entailment-pressure.
- Operation: dependency-exposure.
- Result/state-change: dependency-exposed / the hidden dependency is named.
- Contribution-to-Land(¹B): the consequence is claimed as landed.

TTP Operation Body:
The body names a dependency and says it is exposed. It intentionally uses a
result/pressure label as the operation token instead of the registered
M8-reductio operation `consequence-trace`.

Land(¹B): dependency exposed.

[Mid-Reread Pressure]
Target: ¹B / entailment pressure
R(H,Δ): held routes rechecked: none; live remainder: none in current scope; release/next: STOP.
Landed delta: Δ¹B / dependency-exposed.
Pressure activations:
- freeze-landed-move: terminal-state accounting — freeze ¹B.
- entailment-pressure: M8 — dependency exposure is mislabeled as the operation.
Field diagnostics: ∇·B: neutral / no remaining burden; ∇×κ: null / no loop.
Route-gradient: ∇ points to STOP because the row claims the dependency landed.
Finding: stable
MRP route result type: no_new_resultant
MRP resultant: stable -> no new resultant remains; route STOP.
Graph delta: none
Pre-emption basis: none
Route: STOP

### Closure/Reconstruction Witness
- Initial burden set: [¹B]
- MRP resultants:
  MRP(¹B): type=no_new_resultant; finding=stable; graph=none; route=STOP
- Owner activations:
  ⟦ACT ¹B₁[M8.dependency-exposure] :: π=entailment-pressure :: body_ref=¹B₁ :: Δ=Δ¹B:dependency-exposed :: Land(¹B)+⟧

## field_witness
```json
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activations": [
    {
      "source": "B1",
      "target": "B1",
      "owner": "M8",
      "owner_id": "M8",
      "operation": "dependency-exposure",
      "pressure": "entailment-pressure",
      "body_ref": "¹B₁",
      "delta": "Δ¹B:dependency-exposed",
      "delta_result": "dependency-exposed",
      "land": "Land(¹B)+",
      "land_target": "B1"
    }
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "formal_reread_states": [
    {
      "source_burden": "B1",
      "prior_land": "Land(B1)",
      "delta": "Δ¹B / dependency-exposed.",
      "reread": "R(H,Δ): held routes rechecked: none; live remainder: none in current scope; release/next: STOP.",
      "route_gradient": "∇ points to STOP because the row claims the dependency landed.",
      "divergence_state": "neutral",
      "curl_state": "null",
      "route_result_type": "no_new_resultant",
      "mrp_resultant": "stable -> no new resultant remains; route STOP.",
      "graph_delta": "none",
      "preemption_basis": "none",
      "route": "STOP"
    }
  ]
}
```
