daee-epistemics — NOETIC FIELD EXECUTION

## Layer A — Compact DSL/IR Header

Initial burden set: [¹B]
𝔅_MRP (B_MRP) = [²B]

## Layer B — Bounded Governed Response

## Burden 1 / ¹B — baseline

⟦ACT ¹B₁[M7.anchor] :: π=baseline-pressure :: body_ref=¹B₁ :: Δ=Δ¹B:baseline-anchored :: Land(¹B)+⟧
Land(¹B): baseline anchored.

[Mid-Reread Pressure]
Target: ¹B
R(H,Δ): generated recoil remains.
MRP route result type: generated_burden_instantiation
MRP resultant: genuine-dependent -> instantiate ²B [generated-by: MRP(¹B)]
Route: RECURSE

## Burden 2 / ²B — generated recoil without marker

⟦ACT ²B₁[P7.bound] :: π=generated-recoil :: body_ref=²B₁ :: Δ=Δ²B:recoil-bounded :: Land(²B)+⟧
Land(²B): generated recoil bounded.

[Mid-Reread Pressure]
Target: ²B
R(H,Δ): no live generated burden remains.
MRP route result type: no_new_resultant
MRP resultant: stable -> ²B
Route: STOP

Closure/Reconstruction Witness

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1", "B2"],
  "generated_burdens": [{"id": "B2", "generated_by": "MRP(B1)"}],
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"},
    {"source": "B2", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}
  ],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M7", "operation": "anchor", "pressure": "baseline-pressure", "body_ref": "¹B₁", "delta": "Δ¹B:baseline-anchored", "land": "Land(B1)+"},
    {"source": "MRP(B1)", "target": "B2", "owner": "P7", "operation": "bound", "pressure": "generated-recoil", "body_ref": "²B₁", "delta": "Δ²B:recoil-bounded", "land": "Land(B2)+"}
  ]
}
