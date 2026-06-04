<!-- expect: fail -->
daee-epistemics — NOETIC FIELD EXECUTION

Layer A — compact DSL/IR header
B_LA = [B1, B2, B3]
B_MRP = [B4]
B_total = [B1, B2, B3, B4]

## Burden 1 / ¹B: moral tribunal filter
Layer B — Governed Operation Body
¹B₁[FPD] — expose tribunal filter.
Land(¹B): filter exposed.
R(H,Δ): generated ⁴B remains held, but this invalid fixture falsely claims complete closure.

Closure/Reconstruction Witness
B_LA = [B1, B2, B3]
B_MRP = [B4]
B_total = [B1, B2, B3, B4]
Terminal states:
B1: landed
B2: carried-RECURSE
B3: carried-RECURSE
B4: carried-RECURSE / generated-held unexecuted
MRP resultants:
  MRP(¹B): type=generated_burden_instantiation; finding=genuine-dependent; graph=¹B -> ⁴B; route=HOLD
C(PsiN): coverage_complete=true

field_witness
{
  "B_LA": ["B1", "B2", "B3"],
  "B_MRP": ["B4"],
  "B_total": ["B1", "B2", "B3", "B4"],
  "terminal_states": {
    "B1": "landed",
    "B2": "carried-RECURSE",
    "B3": "carried-RECURSE",
    "B4": "carried-RECURSE / generated-held unexecuted"
  },
  "mrp_resultants": [
    {"source": "B1", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B1 -> B4", "route": "HOLD"}
  ],
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "FPD", "operation": "expose", "pressure": "moral tribunal filter", "body_ref": "¹B₁", "delta": "Δ¹B:imported-criterion-blocked", "land": "Land(B1)+"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2", "B3"],
    "terminal_states": {
      "B1": "landed",
      "B2": "carried-RECURSE",
      "B3": "carried-RECURSE",
      "B4": "carried-RECURSE / generated-held unexecuted"
    },
    "dependency_graph": {"nodes": ["B1", "B2", "B3", "B4"], "edges": [["B1", "B4"]], "roots": ["B1"], "acyclic": true},
    "coverage_complete": true
  }
}
