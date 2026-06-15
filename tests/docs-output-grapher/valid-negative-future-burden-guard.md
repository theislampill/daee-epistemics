<!-- expect: pass -->
╔══════════════════════════════════════════════════════╗
║ daee-epistemics — NOETIC FIELD EXECUTION             ║
╚══════════════════════════════════════════════════════╝

Layer A — compact DSL/IR header
Initial burden set: [¹B, ²B, ³B]
𝔅_LA (B_LA) = {¹B, ²B, ³B}
𝔅_MRP (B_MRP) = {}
𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {¹B, ²B, ³B}

## Burden 1 / ¹B: definition claim
Layer B — Governed Operation Body
¹B₁[M7] — anchor the definition.
Land(¹B): landed.
R(H,Δ): reread shows ²B remains live.

MRP(¹B):
Result type: held_burden_activation
Finding: genuine-dependent
Graph delta: ¹B → ²B
Route: RECURSE

## Burden 2 / ²B: authority claim
Layer B — Governed Operation Body
²B₁[authority-order-repair] — expose the tribunal.
Land(²B): landed.
R(H,Δ): reread shows ³B remains live.

MRP(²B):
Result type: held_burden_activation
Finding: genuine-dependent
Graph delta: ²B → ³B
Route: RECURSE

## Burden 3 / ³B: dependency claim
Layer B — Governed Operation Body
³B₁[M8] — trace the dependency.
Land(³B): landed.
R(H,Δ): reread stable.

MRP(³B):
Result type: no_new_resultant
Finding: stable
Graph delta: none
Route: STOP

[Mid-Reread Pressure]
Target: ³B / dependency claim
R(H,Δ): held routes rechecked: no held routes; live remainder: no unresolved ³B remainder; release/next: STOP with ³B landed.
Pressure activations:
- dependency-tug: the dependency tug is satisfied by tracing borrowed reliance rather than opening ⁴B.

Closure witness
∇·B: neutral.
∇×κ: null.
𝒞(Ψᴺ): coverage_complete=true.
T_lang: Ψᴺ ⇢ Ψᴵ; uptake is not guaranteed.
Restoration aim: dependency pressure closed without a future burden.

field_witness
{
  "B_LA": ["B1", "B2", "B3"],
  "B_MRP": [],
  "B_total": ["B1", "B2", "B3"],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "M7", "operation": "definition-anchor", "pressure": "definition claim", "body_ref": "¹B₁", "delta": "Δ¹B:definition-anchored", "land": "Land(B1)+"},
    {"source": "MRP(B1)", "target": "B2", "owner": "authority-order-repair", "operation": "authority-order-repair", "pressure": "authority claim", "body_ref": "²B₁", "delta": "Δ²B:authority-order-repaired", "land": "Land(B2)+"},
    {"source": "MRP(B2)", "target": "B3", "owner": "M8", "operation": "dependency-trace", "pressure": "dependency claim", "body_ref": "³B₁", "delta": "Δκ:dependency-exposed", "land": "Land(B3)+"}
  ],
  "mrp_resultants": [
    {"source": "B1", "type": "held_burden_activation", "graph": {"from": "B1", "to": "B2"}, "route": "RECURSE"},
    {"source": "B2", "type": "held_burden_activation", "graph": {"from": "B2", "to": "B3"}, "route": "RECURSE"},
    {"source": "B3", "type": "no_new_resultant", "graph": "none", "route": "STOP"}
  ],
  "terminal_states": {"B1": "landed", "B2": "landed", "B3": "landed"},
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2", "B3"],
    "terminal_states": {"B1": "landed", "B2": "landed", "B3": "landed"},
    "dependency_graph": {
      "nodes": ["B1", "B2", "B3"],
      "edges": [{"from": "B1", "to": "B2"}, {"from": "B2", "to": "B3"}],
      "roots": ["B1"],
      "acyclic": true
    }
  }
}
