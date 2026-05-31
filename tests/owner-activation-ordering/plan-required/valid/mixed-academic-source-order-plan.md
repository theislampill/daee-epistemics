NOETIC FIELD EXECUTION

field_witness
{
  "B_LA": ["B1", "B2", "B3", "B4"],
  "B_MRP": ["B5"],
  "B_total": ["B1", "B2", "B3", "B4", "B5"],
  "owner_activation_ordering": {
    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
    "required_before": [
      {"target": "B4", "before_owner": "doubt-vs-skepticism", "after_owner": "P1"},
      {"target": "B5", "before_owner": "source-status-repair", "after_owner": "P7"}
    ],
    "parallel_groups": []
  },
  "owner_activations": [
    {"source": "B1", "target": "B1", "owner": "FPD", "operation": "foreign-premise-detection", "pressure": "academic-prestige-secular-ethics-hidden-tribunal", "body_ref": "B1_1", "delta": "Delta(B1):hidden-tribunal-blocked", "land": "Land(B1)+", "ordering_role": "required"},
    {"source": "MRP(B1)", "target": "B2", "owner": "source-status-repair", "operation": "source-order", "pressure": "hidden-authority-source-status-transfer", "body_ref": "B2_1", "delta": "Delta(B2):hidden-authority-source-status-bounded", "land": "Land(B2)+", "ordering_role": "required"},
    {"source": "MRP(B2)", "target": "B3", "owner": "P3-reason-revelation-tension", "operation": "reason-revelation-tension", "pressure": "reason-as-sovereign-veto-over-revelation", "body_ref": "B3_1", "delta": "Delta(B3):reason-revelation-order-stabilized", "land": "Land(B3)+", "ordering_role": "required"},
    {"source": "MRP(B3)", "target": "B4", "owner": "doubt-vs-skepticism", "operation": "method-distinction", "pressure": "academic-respectability-doubt-boundary", "body_ref": "B4_1", "delta": "Delta(B4):doubt-method-separated-from-sincere-question", "land": "Land(B4)+", "ordering_role": "required"},
    {"source": "MRP(B3)", "target": "B4", "owner": "P1", "operation": "restoration", "pressure": "salah-tawhid-attraction-restoration", "body_ref": "B4_2", "delta": "Delta(B4):tawhid-orientation-restored", "land": "Land(B4)+", "ordering_role": "required"},
    {"source": "MRP(B4)", "target": "B5", "owner": "source-status-repair", "operation": "source-order", "pressure": "source-order-recoil-hidden-support", "body_ref": "B5_1", "delta": "Delta(B5):hidden-support-blocked", "land": "Land(B5)+", "ordering_role": "required"},
    {"source": "MRP(B4)", "target": "B5", "owner": "P7", "operation": "scope-boundary", "pressure": "bounded-answer-reopen-boundary", "body_ref": "B5_2", "delta": "Delta(B5):reopen-boundary-licensed", "land": "Land(B5)+", "ordering_role": "required"}
  ],
  "coverage_proof": {
    "initial_burden_set": ["B1", "B2", "B3", "B4"],
    "terminal_states": {"B1": "landed", "B2": "landed", "B3": "landed", "B4": "landed", "B5": "landed"},
    "dependency_graph": {"nodes": ["B1", "B2", "B3", "B4", "B5"], "edges": [["B1", "B2"], ["B2", "B3"], ["B3", "B4"], ["B4", "B5"]], "roots": ["B1"], "acyclic": true}
  }
}
