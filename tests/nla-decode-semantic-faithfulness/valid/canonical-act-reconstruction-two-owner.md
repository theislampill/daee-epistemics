NOETIC FIELD EXECUTION

## Layer A - Diagnostic IR

N-frame: science-only-source-order-warrant
live registers: [xi, kappa]

## Layer B - Bounded Governed Response

## Burden 1 / B1 - source-order warrant
Matched owner/TTP route: [source-status-repair, M1]
ACT records:
⟦ACT B1_1[source-status-repair.source-order] :: π=scientific-explanations-only-knowledge-source :: body_ref=B1_1 :: Δ=ΔB1:science-source-bounded :: Land(B1)+⟧
⟦ACT B1_2[M1.self-grounding-test] :: π=only-science-counts-standard :: body_ref=B1_2 :: Δ=ΔB1:self-authorizing-standard-invalidated :: Land(B1)+⟧

#### Layer B - Governed Operation Body

### B1_1[source-status-repair] - sort the source-order claim
Target: scientific-explanations-only-knowledge-source in the demand that only scientific explanation can authorize knowledge.
Operation: source-order bounds the scientific-explanations-only-knowledge-source pressure by assigning science to its proper source lane rather than letting it rule every warrant type.
Result/state-change: science-source-bounded; the scientific source-order pressure is no longer allowed to veto non-scientific warrant.
Contribution-to-Land(B1): This science-source-bounded state change contributes to Land(B1) by sorting the source-order pressure.

TTP Operation Body:
The operation source-order bounds the source claim by naming the category of scientific explanation and preventing it from becoming the whole tribunal for knowledge.

### B1_2[M1] - test the self-authorizing standard
Target: only-science-counts-standard in the claim that only scientific explanations count as knowledge.
Operation: self-grounding-test tests the only-science-counts-standard by asking whether that standard can authorize itself without borrowing a non-scientific warrant.
Result/state-change: self-authorizing-standard-invalidated; the only-science-counts-standard fails its own rule.
Contribution-to-Land(B1): This self-authorizing-standard-invalidated state change contributes to Land(B1) by exposing the standard's self-grounding failure.

TTP Operation Body:
The M1 operation performs the self-grounding-test on the only-science-counts-standard and makes the state change visible: the standard cannot authorize its own authority.

Land(B1): the source-order warrant burden is landed.

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "source-status-repair", "operation": "source-order", "pressure": "scientific-explanations-only-knowledge-source", "body_ref": "B1_1", "delta": "ΔB1:science-source-bounded", "land": "Land(B1)+"},
    {"source": "B1", "target": "B1", "owner": "M1", "operation": "self-grounding-test", "pressure": "only-science-counts-standard", "body_ref": "B1_2", "delta": "ΔB1:self-authorizing-standard-invalidated", "land": "Land(B1)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1"],
    "terminal_states": {"B1": "landed"},
    "dependency_graph": {"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}
  }
}
