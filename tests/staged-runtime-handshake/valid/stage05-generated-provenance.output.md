# NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header

- burden floor: B1
- generated burden: B2 [generated-by: MRP(B1)]

## Layer B - Bounded Governed Response

Burden B1

⟦ACT B1_1[source-status-repair.source-order] :: π=source-order :: body_ref=B1_1 :: Δ=ΔB1:source-order-landed :: Land(B1)+⟧

The visible owner body lands B1 while MRP keeps B2 as a generated carried burden.

## Mid-Reread Pressure

R(H,Delta): MRP(B1) generated B2.

Terminal states: B1 landed; B2 carried-RECURSE.

field_witness

```json
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "terminal_states": {
    "B1": {"state": "landed"},
    "B2": {"state": "carried-RECURSE"}
  },
  "normalized_activation_record": {"per_burden": [{"burden_id": "B1"}]}
}
```

## Restorative Response

B2 remains held for the next bounded pass.

## Closing Formulation

Closure is held, not complete.
