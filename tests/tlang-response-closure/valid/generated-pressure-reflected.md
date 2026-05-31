daee-epistemics — T_lang fixture

## Layer A
- B_LA = {B1}
- B_MRP = {B2}
- B_total = B_LA union B_MRP

## Burden 1 / B1
Land(B1): landed.

[Mid-Reread Pressure]
Target: B1 / baseline criterion
MRP route result type: generated_burden_instantiation
MRP resultant: genuine-dependent -> instantiate B2 [generated-by: MRP(B1)] and route RECURSE
Graph delta: B1 -> B2
Route: RECURSE
Boundary: T_lang does not imply guaranteed uptake.

## Burden 2 / B2 [generated-by: MRP(B1)] — reserve criterion
Matched owner/TTP route: [FPD, P7]
- ACT records:
  ⟦ACT B2_1[FPD.expose] :: π=reserve criterion :: body_ref=B2_1 :: Δ=DeltaB2:reserve criterion exposed :: Land(B2)+⟧
  ⟦ACT B2_2[P7.bound] :: π=proof-carousel pressure :: body_ref=B2_2 :: Δ=DeltaB2:stop condition licensed :: Land(B2)+⟧

### B2_1[FPD] — expose reserve criterion
- Target: reserve criterion.
- Operation: expose the imported reserve criterion.
- Result/state-change: reserve criterion exposed.
- Contribution-to-Land(B2): the generated pressure is visible.

### B2_2[P7] — bound proof carousel
- Target: proof-carousel pressure.
- Operation: define the stop condition.
- Result/state-change: stop condition licensed.
- Contribution-to-Land(B2): the generated route is scoped.

Land(B2): landed.

## Restorative Response
The reserve criterion is exposed instead of allowed to govern the answer silently, and the
proof-carousel pressure is bounded by a stated reopen condition.

## Closing Formulation
The public response is a T_lang coupling attempt, not guaranteed uptake.

## field_witness
```json
{
  "B_LA": ["B1"],
  "B_MRP": ["B2"],
  "B_total": ["B1", "B2"],
  "generated_burdens": [
    {"id": "B2", "generated_by": "MRP(B1)", "generation_depth": 1, "reason": "reserve criterion pressure remained after B1 landed"}
  ],
  "owner_activations": [
    {"source": "MRP(B1)", "target": "B2", "owner": "FPD", "operation": "expose", "pressure": "reserve criterion", "body_ref": "B2_1", "delta": "DeltaB2:reserve criterion exposed", "land": "Land(B2)+"},
    {"source": "MRP(B1)", "target": "B2", "owner": "P7", "operation": "bound", "pressure": "proof-carousel pressure", "body_ref": "B2_2", "delta": "DeltaB2:stop condition licensed", "land": "Land(B2)+"}
  ],
  "coverage_proof": {
    "terminal_states": {
      "B1": "landed",
      "B2": "landed"
    }
  }
}
```
