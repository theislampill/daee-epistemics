#!/usr/bin/env python3
"""Validate Diagnostic IR instance integrity.

This checker is intentionally schema-adjacent/custom rather than a jsonschema
runtime. It covers the schema enums, required fields, conditional
decisive_missing_differentiator rule, and repo-specific executable constraints
that JSON Schema alone cannot prove: catalogue membership, compiled-module-map
resolution, source_basis coverage, ghost-load rejection, and post-render
decision consistency. It validates any IR fixture/artifact passed by --file or
discovered under --root, and treats files under tests/ir-fixtures/invalid/ as
expected-invalid regression fixtures. Smoke sidecars named
smokes/runtime-grounding-v*/<fixture>/ir.json are expected-valid by default.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root
from delta_result_vocabulary import delta_result_vocabulary_errors


OMNIBUS_RE = re.compile(r"(?i)(?:^OMNIBUS-|/omnibus/|\\omnibus\\|\.md$|\.json$|\.ya?ml$|/|\\)")
NONE_VALUES = {"", "none", "none.", "n/a", "no", "null"}
DECISIONS = {"STOP", "HOLD", "RECURSE", "PARTIAL"}
REASON_CATEGORY_VALUES = {1, 2, 3, 4, "1", "2", "3", "4"}
MATCHED_MODULE_KEYS = {"id", "module_class"}
SOURCE_BASIS_KEYS = {"entries"}
SOURCE_BASIS_ENTRY_KEYS = {"basis_type", "claim", "source_kind", "module_id", "source_ref", "section", "notes"}
SOURCE_BASIS_TYPES = {"anchored", "inference", "speculative", "synthesis"}
SOURCE_KINDS = {"input", "module", "schema", "catalogue", "operator"}
POST_RENDER_GATE_KEYS = {
    "cleared_this_pass",
    "remaining_live_distortions",
    "held_routes_rechecked",
    "newly_released_routes",
    "next_eligible_pass",
    "recursion_decision",
}
FIELD_WITNESS_KEYS = {
    "route_gradient",
    "burden_events",
    "field_diagnostics",
    "loopbreak",
    "reconstruction",
    "closure",
    "transfer_boundary",
    "register_deltas",
    "non_claims",
    "provenance",
    "coverage_proof",
}
FIELD_WITNESS_OPTIONAL_KEYS = {
    "reread_pressure",
    "normalized_activation_record",
    "canonical_ir_projection",
}
FIELD_WITNESS_ROUTE_KEYS = {"eligible_routes", "selected", "reason"}
FIELD_WITNESS_BURDEN_EVENT_KEYS = {"owner", "delta_nB", "delta_kappa", "result"}
FIELD_WITNESS_NAR_KEYS = {"n_frame", "live_registers", "burden_floor", "per_burden"}
FIELD_WITNESS_NAR_ROW_KEYS = {
    "burden_id",
    "owner_id",
    "operation",
    "delta_result",
    "mrp_route_result_type",
    "terminal_state",
    "generation_depth",
}
FIELD_WITNESS_DIAGNOSTIC_KEYS = {"divergence", "curl"}
FIELD_WITNESS_TARGET_STATUS_KEYS = {"target", "status"}
FIELD_WITNESS_LOOPBREAK_KEYS = {"licensed", "target", "ground", "delta_effect", "post_break_reread"}
FIELD_WITNESS_RECONSTRUCTION_KEYS = {"held_set", "live_remainder", "reread_scope"}
FIELD_WITNESS_CLOSURE_KEYS = {"operator", "decision", "agent_field_status"}
FIELD_WITNESS_TRANSFER_KEYS = {"operator", "from", "to", "mode"}
FIELD_WITNESS_REGISTER_DELTA_ENTRY_KEYS = {"register", "delta"}
FIELD_WITNESS_PROVENANCE_KEYS = {"evidence_type", "source", "captured_by"}
FIELD_WITNESS_COVERAGE_KEYS = {
    "initial_burden_set",
    "terminal_states",
    "dependency_graph",
    "divergence_check",
    "curl_check",
    "coverage_complete",
}
FIELD_WITNESS_COVERAGE_OPTIONAL_KEYS = {"diagnostic_completeness"}
FIELD_WITNESS_DIAGNOSTIC_COMPLETENESS_KEYS = {"live_registers", "coverage", "complete"}
FIELD_WITNESS_CANONICAL_IR_PROJECTION_KEYS = {
    "schema",
    "diagnostic_ir_schema_version",
    "hard_registers",
    "n_frame",
    "live_registers",
    "burden_floor",
    "per_burden",
    "diagnostic_completeness",
}
FIELD_WITNESS_CANONICAL_IR_PROJECTION_OPTIONAL_KEYS = {
    "register_composition",
    "decoded_ir",
    "full_ir_decode",
    "proof_mode",
    "emission_policy",
}
FIELD_WITNESS_CANONICAL_IR_DECODE_KEYS = {
    "schema",
    "source_evidence",
    "n_frame",
    "live_registers",
    "burden_floor",
    "per_burden",
    "diagnostic_completeness",
}
FIELD_WITNESS_CANONICAL_IR_DECODE_OPTIONAL_KEYS = {"hard_registers", "register_composition"}
FIELD_WITNESS_CANONICAL_IR_DECODE_ROW_KEYS = FIELD_WITNESS_NAR_ROW_KEYS | {"pressure", "body_ref"}
FIELD_WITNESS_CANONICAL_IR_DECODE_SOURCE_EVIDENCE = {
    "visible_act",
    "field_witness.owner_activations",
    "normalized_activation_record",
    "canonical_ir_projection",
}
FIELD_WITNESS_FULL_IR_DECODE_KEYS = {
    "schema",
    "source_evidence",
    "n_frame",
    "live_registers",
    "burden_floor",
    "B_LA",
    "B_MRP",
    "B_total",
    "dependency_graph",
    "terminal_states",
    "diagnostic_completeness",
    "per_burden",
    "generated_burdens",
    "formal_reread",
    "source_basis",
}
FIELD_WITNESS_FULL_IR_DECODE_OPTIONAL_KEYS = {"hard_registers", "register_composition"}
FIELD_WITNESS_FULL_IR_DECODE_SOURCE_EVIDENCE = {
    "visible_act",
    "field_witness.owner_activations",
    "normalized_activation_record",
    "canonical_ir_projection",
    "canonical_ir_projection.decoded_ir",
    "field_witness.coverage_proof",
    "field_witness.coverage_proof.dependency_graph",
    "field_witness.generated_burdens",
    "field_witness.formal_reread_states",
    "field_witness.source_basis",
}
FIELD_WITNESS_FULL_IR_DECODE_REQUIRED_SOURCE_EVIDENCE = {
    "visible_act",
    "field_witness.owner_activations",
    "normalized_activation_record",
    "canonical_ir_projection",
    "canonical_ir_projection.decoded_ir",
    "field_witness.coverage_proof",
    "field_witness.coverage_proof.dependency_graph",
}
FIELD_WITNESS_FULL_IR_DECODE_ROW_KEYS = FIELD_WITNESS_CANONICAL_IR_DECODE_ROW_KEYS | {
    "graph_role",
    "generated_by",
    "track",
}
FULL_IR_DECODE_FORMAL_REREAD_KEYS = {
    "states_present",
    "divergence_state",
    "curl_state",
    "escape_routes_checked",
    "no_new_resultant_proof",
}
FULL_IR_DECODE_SOURCE_BASIS_KEYS = {
    "source_basis_available",
    "sigma_inside_hard_registers",
    "basis",
}
FIELD_WITNESS_FULL_IR_PROOF_MODE_KEYS = {
    "schema",
    "mode",
    "source_evidence",
    "machine_facing",
    "schema_light_absent_valid",
    "requires_decoded_ir",
    "visible_opening_header_preserved",
    "arbitrary_nl_ir_parser_claim",
    "default_runtime_emission_claim",
    "t_lang_uptake_claim",
}
FIELD_WITNESS_FULL_IR_PROOF_MODE_SOURCE_EVIDENCE = {
    "visible_noetic_field_opening",
    "visible_layer_a_diagnostic_ir_header",
    "field_witness.canonical_ir_projection",
    "field_witness.canonical_ir_projection.decoded_ir",
    "field_witness.canonical_ir_projection.full_ir_decode",
}
FIELD_WITNESS_FULL_IR_PROOF_MODE_MODES = {
    "selected-surface",
    "checker-owned-sidecar",
    "retained-proof-corpus-sidecar",
}
FIELD_WITNESS_RUNTIME_EMISSION_POLICY_KEYS = {
    "schema",
    "mode",
    "source_evidence",
    "machine_facing",
    "default_runtime",
    "proof_class_closure_only",
    "requires_projection",
    "requires_decoded_ir",
    "requires_full_ir_decode",
    "visible_opening_header_required",
    "legacy_schema_light_absent_valid",
    "public_prose_replacement",
    "arbitrary_nl_ir_parser_claim",
    "t_lang_uptake_claim",
}
FIELD_WITNESS_RUNTIME_EMISSION_POLICY_SOURCE_EVIDENCE = {
    "visible_noetic_field_opening",
    "visible_layer_a_diagnostic_ir_header",
    "field_witness.canonical_ir_projection",
    "field_witness.canonical_ir_projection.proof_mode",
    "field_witness.canonical_ir_projection.decoded_ir",
    "field_witness.canonical_ir_projection.full_ir_decode",
}
FIELD_WITNESS_RUNTIME_EMISSION_POLICY_MODES = {
    "default-runtime-when-proof-class-closure-claimed",
}
FIELD_WITNESS_DEPENDENCY_GRAPH_KEYS = {"nodes", "edges", "roots", "parallel_groups", "acyclic"}
FIELD_WITNESS_DEPENDENCY_EDGE_KEYS = {"from", "to"}
FIELD_WITNESS_REREAD_PRESSURE_KEYS = {
    "target_burden_id",
    "reread_delta",
    "pressure_activations",
    "route_gradient",
    "divergence_state",
    "curl_state",
    "finding",
    "route_result_type",
    "graph_delta",
    "preemption_basis",
    "route",
    "non_claims",
}
FIELD_WITNESS_REREAD_PRESSURE_ACTIVATION_KEYS = {
    "freeze_landed_move",
    "dependency_tug",
    "hidden_framework_recoil",
    "entailment_pressure",
    "doubt_churn_guard",
    "reorientation_reminder",
}
FIELD_WITNESS_REREAD_PRESSURE_GRAPH_DELTA_KEYS = {"nodes_added", "edges_added", "note"}
FIELD_WITNESS_REREAD_PRESSURE_DIVERGENCE = {"neutral", "settled", "bounded", "non-neutral"}
FIELD_WITNESS_REREAD_PRESSURE_CURL = {"null", "resolved", "held", "non-null"}
FIELD_WITNESS_REREAD_PRESSURE_FINDINGS = {
    "stable",
    "genuine-dependent",
    "partial-real",
    "hidden-framework-recoil",
    "doubt-churn",
    "reorientation",
}
FIELD_WITNESS_REREAD_PRESSURE_ROUTE_TYPES = {
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "loopbreak",
    "hold_partial",
}
FIELD_WITNESS_REREAD_PRESSURE_ROUTES = {"STOP", "HOLD", "RECURSE", "LoopBreak(∇×T)"}
FIELD_WITNESS_REREAD_PRESSURE_PREEMPTION = {"none", "graph-bound", "commitment-bound", "framework-bound"}
FIELD_WITNESS_CLOSURE_OPERATORS = {"𝒞(Ψᴺ)"}
FIELD_WITNESS_TRANSFER_FROM_VALUES = {"Ψᴺ"}
FIELD_WITNESS_TRANSFER_TO_VALUES = {"Ψᴵ"}
FIELD_WITNESS_TERMINAL_STATES = {
    "landed",
    "discharged-as-derivative",
    "held-with-reason",
    "carried-PARTIAL",
    "carried-RECURSE",
    "cleared",
}
FIELD_WITNESS_CLOSURE_DECISIONS = {"COMPLETE", "STOP", "HOLD", "RECURSE", "PARTIAL"}
HARD_REGISTER_SCHEMA_VERSION = "0.4.3-hard-registers-v1"
CANONICAL_IR_PROJECTION_SCHEMA = "b5-canonical-ir-projection-v1"
CANONICAL_IR_DECODE_SCHEMA = "b5-canonical-ir-decode-v1"
FULL_IR_DECODE_SCHEMA = "b5-full-ir-decode-v1"
FULL_IR_PROOF_MODE_SCHEMA = "b5-full-ir-proof-mode-v1"
RUNTIME_EMISSION_POLICY_SCHEMA = "b5-full-ir-runtime-emission-v1"
HARD_REGISTER_KEYS = ("heart", "xi", "Omega", "mu", "kappa")
HARD_REGISTER_KEY_SET = set(HARD_REGISTER_KEYS)
NONCANONICAL_HARD_REGISTER_KEYS = {"omega", "Ω", "♥", "ξ", "μ", "κ"}
HARD_REGISTER_STATES = {"live", "held", "non_live"}
HARD_REGISTER_OPTIONAL_KEYS = {"state", "functions", "basis", "non_live_reason"}
HARD_REGISTER_FUNCTIONS = {
    "heart": {"affective-posture", "security-posture", "moral-recoil", "restoration-recoil"},
    "xi": {"warrant-authority", "source-order", "proof-tribunal", "testimony-status"},
    "Omega": {"ontology-predication", "category-transfer", "referent-confusion", "creator-creation"},
    "mu": {"memetic-carrier", "compression-carrier", "defensive-stabilizer", "mutation-reproduction"},
    "kappa": {"dependency-collapse", "entailment-chain", "closure-boundary", "cycle-curl"},
}


POSITIVE_SAMPLE: dict[str, Any] = {
    "case_family": "criterion-import",
    "claim_type": "moral",
    "claim_level": "meta-epistemic",
    "pattern_profile": "PF-10",
    "deformation": "imported moral tribunal",
    "concealment_mode": "clear",
    "do_orient": "mixed",
    "read_status": "dominant",
    "confidence": "strong",
    "alignment_state": "tribunal-loosened",
    "recognition_strength": "medium",
    "continuation_eligibility": "blocked",
    "p7_stops_active": ["none"],
    "reason_category": 3,
    "routing_gate": "open",
    "matched_modules": [
        {"id": "M1-self-refutation", "module_class": "tactic"},
        {"id": "M8-reductio", "module_class": "tactic"},
    ],
    "source_basis": {
        "entries": [
            {
                "basis_type": "anchored",
                "claim": "routing fork: imported criterion requires self-refutation pressure",
                "source_kind": "module",
                "module_id": "M1-self-refutation",
                "source_ref": "atomics/skill/references/tactics/M1-self-refutation.md",
            },
            {
                "basis_type": "anchored",
                "claim": "claim: reductio traces the criterion's consequence",
                "source_kind": "module",
                "module_id": "M8-reductio",
                "source_ref": "atomics/skill/references/tactics/M8-reductio.md",
            },
        ]
    },
    "restoration_target": "return moral criterion to warranted order",
    "reconstruction_fidelity": "pass",
    "reconstructor_notes": "burden, owner contrast, Land(B), and STOP verdict recover from input plus IR",
    "next_move": "test imported criterion before downstream content",
    "output_shape": "single-response",
    "post_render_gate": {
        "cleared_this_pass": "imported tribunal no longer governs as neutral judge",
        "remaining_live_distortions": "none",
        "held_routes_rechecked": [],
        "newly_released_routes": [],
        "next_eligible_pass": "none",
        "recursion_decision": "STOP",
    },
    "field_witness": {
        "route_gradient": {
            "eligible_routes": ["M1-self-refutation", "M8-reductio"],
            "selected": "M1-self-refutation",
            "reason": "imported tribunal pressure governs before reductio consequence trace",
        },
        "burden_events": [
            {
                "owner": "M1-self-refutation",
                "delta_nB": "imported criterion no longer stands as neutral judge",
                "delta_kappa": "downstream moral-content route remains held behind criterion repair",
                "result": "criterion pressure landed",
            }
        ],
        "field_diagnostics": {
            "divergence": {"target": "B", "status": "bounded"},
            "curl": {"target": "kappa", "status": "null"},
        },
        "loopbreak": {
            "licensed": False,
            "target": "",
            "ground": "",
            "delta_effect": "",
            "post_break_reread": "",
        },
        "reconstruction": {
            "held_set": [],
            "live_remainder": [],
            "reread_scope": "held routes and remaining live distortions rechecked before STOP",
        },
        "closure": {
            "operator": "𝒞(Ψᴺ)",
            "decision": "STOP",
            "agent_field_status": "agent execution field closed with no remaining live distortion",
        },
        "transfer_boundary": {
            "operator": "T_lang",
            "from": "Ψᴺ",
            "to": "Ψᴵ",
            "mode": "coupling-attempt",
        },
        "register_deltas": [
            {"register": "heart", "delta": "grief-coded register held with reason"},
            {"register": "xi", "delta": "criterion warrant pressure landed"},
            {"register": "Omega", "delta": "no live ontological delta in this sample"},
            {"register": "sigma", "delta": "source-status unchanged"},
            {"register": "mu", "delta": "no carrier/reproduction vector live"},
            {"register": "kappa", "delta": "B2 dependency radius discharged after B1 landed"},
            {"register": "H", "delta": "held set empty after reread"},
        ],
        "non_claims": [
            "not truth or warrant proof",
            "not interlocutor uptake",
            "not soul access",
            "not package-bound release proof",
        ],
        "provenance": {
            "evidence_type": "static-checker-positive-sample",
            "source": "tools/check_ir_instance_integrity.py",
            "captured_by": "embedded fixture",
        },
        "normalized_activation_record": {
            "n_frame": "fixture-imported-criterion",
            "live_registers": ["xi", "kappa"],
            "burden_floor": ["B1", "B2"],
            "per_burden": [
                {
                    "burden_id": "B1",
                    "owner_id": "M1",
                    "operation": "self-refutation",
                    "delta_result": "criterion-self-failed",
                    "mrp_route_result_type": "no_new_resultant",
                    "terminal_state": "landed",
                    "generation_depth": 0,
                },
                {
                    "burden_id": "B2",
                    "owner_id": "M8",
                    "operation": "dependency-discharge",
                    "delta_result": "dependency-exposed",
                    "mrp_route_result_type": "no_new_resultant",
                    "terminal_state": "discharged-as-derivative",
                    "generation_depth": 0,
                },
            ],
        },
        "coverage_proof": {
            "initial_burden_set": ["B1", "B2"],
            "terminal_states": {
                "B1": {
                    "state": "landed",
                    "operator": "M1-self-refutation",
                    "delta_nB": "criterion pressure landed",
                },
                "B2": {
                    "state": "discharged-as-derivative",
                    "reason": "dissolved when B1 landed",
                },
            },
            "dependency_graph": {
                "nodes": ["B1", "B2"],
                "edges": [{"from": "B1", "to": "B2"}],
                "roots": ["B1"],
                "parallel_groups": [],
                "acyclic": True,
            },
            "divergence_check": "neutral",
            "curl_check": "null",
            "coverage_complete": True,
        },
    },
}


BAD_SAMPLES: dict[str, tuple[dict[str, Any], str]] = {}


def _sample_with(mutator) -> dict[str, Any]:  # noqa: ANN001
    sample = deepcopy(POSITIVE_SAMPLE)
    mutator(sample)
    return sample


def _hard_register_sample(live_registers: tuple[str, ...] = ("xi", "kappa")) -> dict[str, Any]:
    sample = deepcopy(POSITIVE_SAMPLE)
    live = set(live_registers)
    sample["diagnostic_ir_schema_version"] = HARD_REGISTER_SCHEMA_VERSION
    sample["registers"] = {}
    for key in HARD_REGISTER_KEYS:
        if key in live:
            function = sorted(HARD_REGISTER_FUNCTIONS[key])[0]
            sample["registers"][key] = {
                "state": "live",
                "functions": [function],
                "basis": [f"{key} pressure is live in the fixture diagnosis"],
            }
        else:
            sample["registers"][key] = {
                "state": "non_live",
                "functions": [],
                "basis": [],
                "non_live_reason": "not diagnosed as live in this fixture",
            }
    sample["field_witness"]["normalized_activation_record"]["live_registers"] = [
        key for key in HARD_REGISTER_KEYS if key in live
    ]
    sample["field_witness"]["coverage_proof"]["diagnostic_completeness"] = {
        "live_registers": [key for key in HARD_REGISTER_KEYS if key in live],
        "coverage": {
            key: ["B1" if key != "kappa" else "B2"]
            for key in HARD_REGISTER_KEYS
            if key in live
        },
        "complete": True,
    }
    return sample


def _hard_register_sample_with(mutator) -> dict[str, Any]:  # noqa: ANN001
    sample = _hard_register_sample()
    mutator(sample)
    return sample


def _attach_canonical_ir_projection(sample: dict[str, Any]) -> None:
    field_witness = sample["field_witness"]
    normalized = field_witness["normalized_activation_record"]
    diagnostic = field_witness["coverage_proof"]["diagnostic_completeness"]
    field_witness["canonical_ir_projection"] = {
        "schema": CANONICAL_IR_PROJECTION_SCHEMA,
        "diagnostic_ir_schema_version": HARD_REGISTER_SCHEMA_VERSION,
        "hard_registers": deepcopy(sample["registers"]),
        "n_frame": normalized["n_frame"],
        "live_registers": deepcopy(normalized["live_registers"]),
        "burden_floor": deepcopy(normalized["burden_floor"]),
        "per_burden": deepcopy(normalized["per_burden"]),
        "diagnostic_completeness": deepcopy(diagnostic),
    }


def _attach_canonical_ir_decode(sample: dict[str, Any]) -> None:
    field_witness = sample["field_witness"]
    if "canonical_ir_projection" not in field_witness:
        _attach_canonical_ir_projection(sample)
    projection = field_witness["canonical_ir_projection"]
    decoded_rows = []
    for index, row in enumerate(projection["per_burden"], start=1):
        decoded = deepcopy(row)
        decoded["pressure"] = f"{row['burden_id'].lower()}-{row['operation']}-pressure"
        decoded["body_ref"] = f"{row['burden_id']}_{index}"
        decoded_rows.append(decoded)
    projection["decoded_ir"] = {
        "schema": CANONICAL_IR_DECODE_SCHEMA,
        "source_evidence": [
            "visible_act",
            "field_witness.owner_activations",
            "normalized_activation_record",
            "canonical_ir_projection",
        ],
        "n_frame": projection["n_frame"],
        "live_registers": deepcopy(projection["live_registers"]),
        "burden_floor": deepcopy(projection["burden_floor"]),
        "per_burden": decoded_rows,
        "diagnostic_completeness": deepcopy(projection["diagnostic_completeness"]),
        "hard_registers": deepcopy(projection["hard_registers"]),
    }


def _hard_register_projection_sample_with(mutator) -> dict[str, Any]:  # noqa: ANN001
    sample = _hard_register_sample()
    _attach_canonical_ir_projection(sample)
    mutator(sample)
    return sample


HARD_REGISTER_POSITIVE_SAMPLE = _hard_register_sample()
HARD_REGISTER_PROJECTION_POSITIVE_SAMPLE = _hard_register_sample_with(_attach_canonical_ir_projection)
HARD_REGISTER_DECODE_POSITIVE_SAMPLE = _hard_register_sample_with(_attach_canonical_ir_decode)


BAD_SAMPLES["invented_module_id"] = (
    _sample_with(lambda s: s["matched_modules"].append({"id": "invented-owner", "module_class": "tactic"})),
    "module id not found in catalogue",
)
BAD_SAMPLES["module_class_mismatch"] = (
    _sample_with(lambda s: s["matched_modules"][0].update({"module_class": "technique"})),
    "module_class mismatch",
)
BAD_SAMPLES["omnibus_active_module"] = (
    _sample_with(lambda s: s["matched_modules"].append({"id": "OMNIBUS-tactics", "module_class": "tactic"})),
    "omnibus/path used as matched module id",
)
BAD_SAMPLES["missing_source_basis"] = (
    _sample_with(lambda s: s.pop("source_basis")),
    "source_basis missing while matched_modules present",
)
BAD_SAMPLES["ghost_load"] = (
    _sample_with(lambda s: s["source_basis"]["entries"].pop()),
    "ghost-load",
)
BAD_SAMPLES["source_basis_module_mismatch"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"module_id": "M8-reductio"})),
    "ghost-load",
)
BAD_SAMPLES["source_basis_invalid_module"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"module_id": "invented-owner"})),
    "source_basis module_id not found",
)
BAD_SAMPLES["source_basis_without_claim"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"claim": ""})),
    "module source_basis entry lacks claim",
)
BAD_SAMPLES["source_basis_vague_claim"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"claim": "module used"})),
    "module source_basis entry uses vague claim",
)
BAD_SAMPLES["stop_with_next_pass"] = (
    _sample_with(lambda s: s["post_render_gate"].update({"next_eligible_pass": "model/predication"})),
    "STOP requires next_eligible_pass none",
)
BAD_SAMPLES["weak_confidence_without_differentiator"] = (
    _sample_with(lambda s: s.update({"confidence": "provisional"})),
    "missing required field: decisive_missing_differentiator",
)
BAD_SAMPLES["distributed_read_without_differentiator"] = (
    _sample_with(lambda s: s.update({"read_status": "distributed"})),
    "missing required field: decisive_missing_differentiator",
)
BAD_SAMPLES["reconstruction_partial_without_notes"] = (
    _sample_with(lambda s: (s.update({"reconstruction_fidelity": "partial"}), s.pop("reconstructor_notes", None))),
    "missing required field: reconstructor_notes",
)
BAD_SAMPLES["p7_none_combined_with_stop"] = (
    _sample_with(lambda s: s.update({"p7_stops_active": ["none", "Stop-1"]})),
    "p7_stops_active cannot combine none with active stops",
)
BAD_SAMPLES["invalid_reason_category"] = (
    _sample_with(lambda s: s.update({"reason_category": "unknown"})),
    "reason_category invalid oneOf value",
)
BAD_SAMPLES["matched_module_extra_key"] = (
    _sample_with(lambda s: s["matched_modules"][0].update({"extra": "leak"})),
    "matched_modules[0] additional property not allowed",
)
BAD_SAMPLES["source_basis_extra_key"] = (
    _sample_with(lambda s: s["source_basis"].update({"extra": "leak"})),
    "source_basis additional property not allowed",
)
BAD_SAMPLES["source_basis_entry_extra_key"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"extra": "leak"})),
    "source_basis.entries[0] additional property not allowed",
)
BAD_SAMPLES["post_render_gate_extra_key"] = (
    _sample_with(lambda s: s["post_render_gate"].update({"extra": "leak"})),
    "post_render_gate additional property not allowed",
)
BAD_SAMPLES["field_witness_extra_key"] = (
    _sample_with(lambda s: s["field_witness"].update({"extra": "leak"})),
    "field_witness additional property not allowed",
)
BAD_SAMPLES["field_witness_empty_burden_events"] = (
    _sample_with(lambda s: s["field_witness"].update({"burden_events": []})),
    "field_witness.burden_events must be a non-empty array",
)
BAD_SAMPLES["field_witness_nar_missing_per_burden"] = (
    _sample_with(lambda s: s["field_witness"]["normalized_activation_record"].pop("per_burden")),
    "field_witness.normalized_activation_record missing required field: per_burden",
)
BAD_SAMPLES["field_witness_nar_delta_result_out_of_vocabulary"] = (
    _sample_with(
        lambda s: s["field_witness"]["normalized_activation_record"]["per_burden"][0].update(
            {"delta_result": "generic-criterion-repaired"}
        )
    ),
    "delta_result token 'generic-criterion-repaired' is outside controlled vocabulary",
)
BAD_SAMPLES["field_witness_loopbreak_licensed_without_target"] = (
    _sample_with(lambda s: s["field_witness"]["loopbreak"].update({"licensed": True, "target": ""})),
    "field_witness.loopbreak.target required when licensed",
)
BAD_SAMPLES["field_witness_transfer_uptake_mode"] = (
    _sample_with(lambda s: s["field_witness"]["transfer_boundary"].update({"mode": "uptake-guarantee"})),
    "field_witness.transfer_boundary.mode must be coupling-attempt",
)
BAD_SAMPLES["field_witness_coverage_missing_terminal"] = (
    _sample_with(lambda s: s["field_witness"]["coverage_proof"]["terminal_states"].pop("B2")),
    "field_witness.coverage_proof missing terminal state for B2",
)
BAD_SAMPLES["field_witness_dependency_unknown_node"] = (
    _sample_with(lambda s: s["field_witness"]["coverage_proof"]["dependency_graph"]["edges"].append({"from": "B1", "to": "B9"})),
    "field_witness.coverage_proof.dependency_graph edge endpoint not in nodes",
)
BAD_SAMPLES["field_witness_dependency_cycle"] = (
    _sample_with(lambda s: s["field_witness"]["coverage_proof"]["dependency_graph"]["edges"].append({"from": "B2", "to": "B1"})),
    "field_witness.coverage_proof.dependency_graph contains a cycle",
)
BAD_SAMPLES["field_witness_empty_non_claims"] = (
    _sample_with(lambda s: s["field_witness"].update({"non_claims": []})),
    "field_witness.non_claims must be non-empty array",
)
BAD_SAMPLES["hard_registers_without_version"] = (
    _hard_register_sample_with(lambda s: s.pop("diagnostic_ir_schema_version")),
    "registers require diagnostic_ir_schema_version",
)
BAD_SAMPLES["hard_register_version_without_registers"] = (
    _hard_register_sample_with(lambda s: s.pop("registers")),
    "registers required for hard-register schema version",
)
BAD_SAMPLES["hard_register_missing_field"] = (
    _hard_register_sample_with(lambda s: s["registers"].pop("mu")),
    "registers missing required field: mu",
)
BAD_SAMPLES["hard_register_unknown_key"] = (
    _hard_register_sample_with(lambda s: s["registers"].update({"zeta": {"state": "live", "functions": [], "basis": []}})),
    "registers additional property not allowed: zeta",
)
BAD_SAMPLES["hard_register_invalid_vocabulary_token"] = (
    _hard_register_sample_with(lambda s: s["registers"]["xi"].update({"functions": ["generic-warrant"]})),
    "registers.xi.functions invalid token",
)
BAD_SAMPLES["hard_register_nar_mismatch"] = (
    _hard_register_sample_with(
        lambda s: s["field_witness"]["normalized_activation_record"].update({"live_registers": ["xi"]})
    ),
    "hard-register live set mismatch",
)
BAD_SAMPLES["hard_register_register_delta_missing_live"] = (
    _hard_register_sample_with(
        lambda s: s["field_witness"].update(
            {
                "register_deltas": [
                    item
                    for item in s["field_witness"]["register_deltas"]
                    if item.get("register") != "kappa"
                ]
            }
        )
    ),
    "field_witness.register_deltas missing live hard register kappa",
)
BAD_SAMPLES["hard_register_noncanonical_delta_key"] = (
    _hard_register_sample_with(
        lambda s: s["field_witness"]["register_deltas"][0].update({"register": "Ω"})
    ),
    "field_witness.register_deltas uses noncanonical hard-register key",
)
BAD_SAMPLES["hard_register_diagnostic_completeness_missing"] = (
    _hard_register_sample_with(
        lambda s: s["field_witness"]["coverage_proof"].pop("diagnostic_completeness")
    ),
    "field_witness.coverage_proof.diagnostic_completeness required for hard-register reconciliation",
)
BAD_SAMPLES["hard_register_diagnostic_completeness_live_mismatch"] = (
    _hard_register_sample_with(
        lambda s: s["field_witness"]["coverage_proof"]["diagnostic_completeness"].update(
            {"live_registers": ["xi"]}
        )
    ),
    "diagnostic_completeness.live_registers must reconcile with hard registers",
)
BAD_SAMPLES["hard_register_diagnostic_completeness_coverage_missing"] = (
    _hard_register_sample_with(
        lambda s: s["field_witness"]["coverage_proof"]["diagnostic_completeness"]["coverage"].pop("kappa")
    ),
    "diagnostic_completeness omits live register kappa coverage",
)
BAD_SAMPLES["canonical_ir_projection_without_version"] = (
    _hard_register_projection_sample_with(lambda s: s.pop("diagnostic_ir_schema_version")),
    "field_witness.canonical_ir_projection requires diagnostic_ir_schema_version",
)
BAD_SAMPLES["canonical_ir_projection_schema_marker_mismatch"] = (
    _hard_register_projection_sample_with(
        lambda s: s["field_witness"]["canonical_ir_projection"].update({"schema": "invented-projection-v1"})
    ),
    "field_witness.canonical_ir_projection.schema must be",
)
BAD_SAMPLES["canonical_ir_projection_hard_registers_mismatch"] = (
    _hard_register_projection_sample_with(
        lambda s: s["field_witness"]["canonical_ir_projection"]["hard_registers"]["mu"].update(
            {"state": "live", "functions": ["memetic-carrier"], "basis": ["invented live carrier"]}
        )
    ),
    "canonical_ir_projection.hard_registers must match root registers",
)
BAD_SAMPLES["canonical_ir_projection_live_registers_mismatch"] = (
    _hard_register_projection_sample_with(
        lambda s: s["field_witness"]["canonical_ir_projection"].update({"live_registers": ["xi"]})
    ),
    "field_witness.canonical_ir_projection hard-register live set mismatch",
)
BAD_SAMPLES["canonical_ir_projection_nar_mismatch"] = (
    _hard_register_projection_sample_with(
        lambda s: s["field_witness"]["canonical_ir_projection"].update({"n_frame": "invented-frame"})
    ),
    "field_witness.canonical_ir_projection.n_frame must match",
)
BAD_SAMPLES["canonical_ir_projection_diagnostic_completeness_mismatch"] = (
    _hard_register_projection_sample_with(
        lambda s: s["field_witness"]["canonical_ir_projection"]["diagnostic_completeness"].update(
            {"live_registers": ["xi"]}
        )
    ),
    "canonical_ir_projection.diagnostic_completeness must match",
)
BAD_SAMPLES["canonical_ir_projection_missing_register_delta"] = (
    _hard_register_projection_sample_with(
        lambda s: s["field_witness"].update(
            {
                "register_deltas": [
                    item
                    for item in s["field_witness"]["register_deltas"]
                    if item.get("register") != "kappa"
                ]
            }
        )
    ),
    "field_witness.canonical_ir_projection missing live hard register delta kappa",
)
BAD_SAMPLES["canonical_ir_decode_missing_required_field"] = (
    _hard_register_projection_sample_with(
        lambda s: (
            _attach_canonical_ir_decode(s),
            s["field_witness"]["canonical_ir_projection"]["decoded_ir"].pop("burden_floor"),
        )
    ),
    "field_witness.canonical_ir_projection.decoded_ir missing required field: burden_floor",
)
BAD_SAMPLES["canonical_ir_decode_nar_mismatch"] = (
    _hard_register_projection_sample_with(
        lambda s: (
            _attach_canonical_ir_decode(s),
            s["field_witness"]["canonical_ir_projection"]["decoded_ir"].update({"n_frame": "invented-frame"}),
        )
    ),
    "field_witness.canonical_ir_projection.decoded_ir.n_frame must match",
)
BAD_SAMPLES["canonical_ir_decode_hard_register_mismatch"] = (
    _hard_register_projection_sample_with(
        lambda s: (
            _attach_canonical_ir_decode(s),
            s["field_witness"]["canonical_ir_projection"]["decoded_ir"]["hard_registers"]["xi"].update(
                {"state": "held"}
            ),
        )
    ),
    "decoded_ir.hard_registers must match",
)
BAD_SAMPLES["canonical_ir_decode_generation_depth_mismatch"] = (
    _hard_register_projection_sample_with(
        lambda s: (
            _attach_canonical_ir_decode(s),
            s["field_witness"]["canonical_ir_projection"]["decoded_ir"]["per_burden"][0].update(
                {"generation_depth": 7}
            ),
        )
    ),
    "decoded_ir.per_burden[0] core fields must match",
)
BAD_SAMPLES["canonical_ir_decode_owner_delta_route_mismatch"] = (
    _hard_register_projection_sample_with(
        lambda s: (
            _attach_canonical_ir_decode(s),
            s["field_witness"]["canonical_ir_projection"]["decoded_ir"]["per_burden"][0].update(
                {
                    "owner_id": "invented-owner",
                    "delta_result": "invented-delta",
                    "mrp_route_result_type": "advice_only",
                }
            ),
        )
    ),
    "decoded_ir.per_burden[0] core fields must match",
)
BAD_SAMPLES["canonical_ir_projection_proof_mode_without_full_decode"] = (
    _hard_register_projection_sample_with(
        lambda s: (
            _attach_canonical_ir_decode(s),
            s["field_witness"]["canonical_ir_projection"].update(
                {
                    "proof_mode": {
                        "schema": FULL_IR_PROOF_MODE_SCHEMA,
                        "mode": "selected-surface",
                        "source_evidence": [
                            "visible_noetic_field_opening",
                            "visible_layer_a_diagnostic_ir_header",
                            "field_witness.canonical_ir_projection",
                            "field_witness.canonical_ir_projection.decoded_ir",
                            "field_witness.canonical_ir_projection.full_ir_decode",
                        ],
                        "machine_facing": True,
                        "schema_light_absent_valid": True,
                        "requires_decoded_ir": True,
                        "visible_opening_header_preserved": True,
                        "arbitrary_nl_ir_parser_claim": False,
                        "default_runtime_emission_claim": False,
                        "t_lang_uptake_claim": False,
                    }
                }
            ),
        )
    ),
    "proof_mode requires field_witness.canonical_ir_projection.full_ir_decode",
)

COMPILED_MAP_BAD_SAMPLES = {
    "matched_module_absent_from_compiled_map": (
        _sample_with(lambda s: None),
        "matched module does not resolve in compiled-module-map.json",
        "M1-self-refutation",
    )
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_ir_like(payload: Any) -> bool:
    return isinstance(payload, dict) and (
        "matched_modules" in payload
        or "post_render_gate" in payload
        or "case_family" in payload
    )


def as_instances(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if is_ir_like(item)]
    return [payload] if is_ir_like(payload) else []


def is_noneish(value: Any) -> bool:
    if isinstance(value, str):
        stripped = value.strip().lower()
        return stripped in NONE_VALUES or stripped.startswith("none ")
    if isinstance(value, list):
        return len(value) == 0 or all(is_noneish(item) for item in value)
    return value is None


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def canonical_live_registers(registers: dict[str, Any]) -> list[str]:
    live: list[str] = []
    for key in HARD_REGISTER_KEYS:
        value = registers.get(key)
        if isinstance(value, dict) and value.get("state") in {"live", "held"}:
            live.append(key)
    return live


def hard_register_object_errors(registers: Any, label: str) -> list[str]:
    if not isinstance(registers, dict):
        return [f"schema: {label} must be object"]

    errors: list[str] = []
    extra = sorted(set(registers) - HARD_REGISTER_KEY_SET)
    missing = sorted(HARD_REGISTER_KEY_SET - set(registers), key=HARD_REGISTER_KEYS.index)
    if extra:
        errors.append(f"schema: {label} additional property not allowed: " + ", ".join(extra))
    if missing:
        errors.append(f"schema: {label} missing required field: " + ", ".join(missing))

    for key in HARD_REGISTER_KEYS:
        if key not in registers:
            continue
        value = registers.get(key)
        row_label = f"{label}.{key}"
        if not isinstance(value, dict):
            errors.append(f"schema: {row_label} must be object")
            continue
        row_extra = sorted(set(value) - HARD_REGISTER_OPTIONAL_KEYS)
        if row_extra:
            errors.append(f"schema: {row_label} additional property not allowed: {', '.join(row_extra)}")
        for required_field in ("state", "functions", "basis"):
            if required_field not in value:
                errors.append(f"schema: {row_label} missing required field: {required_field}")
        state = value.get("state")
        functions = value.get("functions")
        basis = value.get("basis")
        if state not in HARD_REGISTER_STATES:
            errors.append(f"schema: {row_label}.state invalid enum value: {state!r}")
        if not isinstance(functions, list) or not all(non_empty_string(item) for item in functions):
            errors.append(f"schema: {row_label}.functions must be array of non-empty strings")
            functions = []
        if not isinstance(basis, list) or not all(non_empty_string(item) for item in basis):
            errors.append(f"schema: {row_label}.basis must be array of non-empty strings")
            basis = []
        if state in {"live", "held"}:
            if not functions:
                errors.append(f"schema: {row_label}.functions required when state is {state}")
            if not basis:
                errors.append(f"schema: {row_label}.basis required when state is {state}")
            invalid_functions = sorted(set(functions) - HARD_REGISTER_FUNCTIONS[key])
            if invalid_functions:
                errors.append(
                    f"schema: {row_label}.functions invalid token(s): {', '.join(invalid_functions)}"
                )
        elif state == "non_live":
            if functions:
                errors.append(f"schema: {row_label}.functions must be empty when state is non_live")
            if basis:
                errors.append(f"schema: {row_label}.basis must be empty when state is non_live")
            if not non_empty_string(value.get("non_live_reason")):
                errors.append(f"schema: {row_label}.non_live_reason required when state is non_live")
    return errors


def diagnostic_completeness_reconciliation_errors(
    diagnostic: Any,
    expected_live: list[str],
    initial_burden_set: Any,
    label: str,
) -> list[str]:
    errors = require_exact_keys(
        diagnostic,
        FIELD_WITNESS_DIAGNOSTIC_COMPLETENESS_KEYS,
        label,
    )
    if errors:
        return errors

    claimed_live = diagnostic.get("live_registers")
    if not isinstance(claimed_live, list) or not all(non_empty_string(item) for item in claimed_live):
        errors.append(f"schema: {label}.live_registers must be array of non-empty strings")
    elif claimed_live != expected_live:
        errors.append(
            f"schema: {label}.live_registers must reconcile with hard registers: "
            f"registers={expected_live!r} {label}.live_registers={claimed_live!r}"
        )
    coverage_map = diagnostic.get("coverage")
    floor = set(initial_burden_set) if isinstance(initial_burden_set, list) else set()
    if not isinstance(coverage_map, dict):
        errors.append(f"schema: {label}.coverage must be object")
    else:
        extra = sorted(set(coverage_map) - set(expected_live))
        if extra:
            errors.append(f"schema: {label}.coverage contains non-live register(s): " + ", ".join(extra))
        for register in expected_live:
            burdens = coverage_map.get(register)
            if not isinstance(burdens, list) or not burdens:
                errors.append(f"schema: {label} omits live register {register} coverage")
                continue
            for burden in burdens:
                if not isinstance(burden, str) or not re.fullmatch(r"B\d+", burden):
                    errors.append(
                        f"schema: {label} maps live register {register} to invalid burden {burden!r}"
                    )
                elif floor and burden not in floor:
                    errors.append(
                        f"schema: {label} maps live register {register} to non-floor burden {burden}"
                    )
    if diagnostic.get("complete") is not True:
        errors.append(f"schema: {label}.complete=false cannot support hard-register reconciliation")
    return errors


def canonical_ir_decode_errors(
    projection: dict[str, Any],
    field_witness: dict[str, Any],
) -> list[str]:
    decoded = projection.get("decoded_ir")
    if decoded is None:
        return []

    label = "field_witness.canonical_ir_projection.decoded_ir"
    errors = require_keys_with_optional(
        decoded,
        FIELD_WITNESS_CANONICAL_IR_DECODE_KEYS,
        FIELD_WITNESS_CANONICAL_IR_DECODE_OPTIONAL_KEYS,
        label,
    )
    if errors:
        return errors

    if decoded.get("schema") != CANONICAL_IR_DECODE_SCHEMA:
        errors.append(f"schema: {label}.schema must be {CANONICAL_IR_DECODE_SCHEMA!r}")

    source_evidence = decoded.get("source_evidence")
    if not isinstance(source_evidence, list) or not all(non_empty_string(item) for item in source_evidence):
        errors.append(f"schema: {label}.source_evidence must be array of non-empty strings")
    else:
        missing = sorted(FIELD_WITNESS_CANONICAL_IR_DECODE_SOURCE_EVIDENCE - set(source_evidence))
        extra = sorted(set(source_evidence) - FIELD_WITNESS_CANONICAL_IR_DECODE_SOURCE_EVIDENCE)
        if missing:
            errors.append(f"schema: {label}.source_evidence missing required source(s): {', '.join(missing)}")
        if extra:
            errors.append(f"schema: {label}.source_evidence unknown source(s): {', '.join(extra)}")

    for key in ("n_frame", "live_registers", "burden_floor", "diagnostic_completeness"):
        if decoded.get(key) != projection.get(key):
            errors.append(f"schema: {label}.{key} must match field_witness.canonical_ir_projection.{key}")

    if decoded.get("hard_registers") != projection.get("hard_registers"):
        errors.append(
            "schema: field_witness.canonical_ir_projection.decoded_ir.hard_registers "
            "must match field_witness.canonical_ir_projection.hard_registers"
        )

    if projection.get("register_composition") is not None:
        if decoded.get("register_composition") != projection.get("register_composition"):
            errors.append(
                "schema: field_witness.canonical_ir_projection.decoded_ir.register_composition "
                "must match field_witness.canonical_ir_projection.register_composition"
            )
    elif "register_composition" in decoded:
        errors.append(
            "schema: field_witness.canonical_ir_projection.decoded_ir.register_composition "
            "requires field_witness.canonical_ir_projection.register_composition"
        )

    projection_rows = projection.get("per_burden")
    decoded_rows = decoded.get("per_burden")
    normalized = field_witness.get("normalized_activation_record")
    nar_rows = normalized.get("per_burden") if isinstance(normalized, dict) else None
    if not isinstance(decoded_rows, list) or not decoded_rows:
        errors.append(f"schema: {label}.per_burden must be non-empty array")
        return errors
    if isinstance(projection_rows, list) and len(decoded_rows) != len(projection_rows):
        errors.append(f"schema: {label}.per_burden row count must match canonical_ir_projection.per_burden")
    if isinstance(nar_rows, list) and len(decoded_rows) != len(nar_rows):
        errors.append(f"schema: {label}.per_burden row count must match normalized_activation_record.per_burden")

    for index, row in enumerate(decoded_rows):
        row_label = f"{label}.per_burden[{index}]"
        row_errors = require_exact_keys(row, FIELD_WITNESS_CANONICAL_IR_DECODE_ROW_KEYS, row_label)
        errors.extend(row_errors)
        if row_errors:
            continue
        core = {key: row.get(key) for key in FIELD_WITNESS_NAR_ROW_KEYS}
        if isinstance(projection_rows, list) and index < len(projection_rows):
            projection_row = projection_rows[index]
            if isinstance(projection_row, dict) and core != {
                key: projection_row.get(key) for key in FIELD_WITNESS_NAR_ROW_KEYS
            }:
                errors.append(f"schema: {row_label} core fields must match canonical_ir_projection.per_burden")
        if isinstance(nar_rows, list) and index < len(nar_rows):
            nar_row = nar_rows[index]
            if isinstance(nar_row, dict) and core != {key: nar_row.get(key) for key in FIELD_WITNESS_NAR_ROW_KEYS}:
                errors.append(f"schema: {row_label} core fields must match normalized_activation_record.per_burden")
        if not non_empty_string(row.get("pressure")):
            errors.append(f"schema: {row_label}.pressure must be non-empty string")
        body_ref = row.get("body_ref")
        if not isinstance(body_ref, str) or not re.fullmatch(r"B\d+_\d+", body_ref):
            errors.append(f"schema: {row_label}.body_ref must be submove ref")
    return errors


def full_ir_decode_errors(
    projection: dict[str, Any],
    field_witness: dict[str, Any],
) -> list[str]:
    full = projection.get("full_ir_decode")
    if full is None:
        return []

    label = "field_witness.canonical_ir_projection.full_ir_decode"
    errors = require_keys_with_optional(
        full,
        FIELD_WITNESS_FULL_IR_DECODE_KEYS,
        FIELD_WITNESS_FULL_IR_DECODE_OPTIONAL_KEYS,
        label,
    )
    if errors:
        return errors

    decoded = projection.get("decoded_ir")
    if not isinstance(decoded, dict):
        errors.append(f"schema: {label} requires field_witness.canonical_ir_projection.decoded_ir")
        decoded = {}

    if full.get("schema") != FULL_IR_DECODE_SCHEMA:
        errors.append(f"schema: {label}.schema must be {FULL_IR_DECODE_SCHEMA!r}")

    source_evidence = full.get("source_evidence")
    if not isinstance(source_evidence, list) or not all(non_empty_string(item) for item in source_evidence):
        errors.append(f"schema: {label}.source_evidence must be array of non-empty strings")
    else:
        source_set = set(source_evidence)
        missing = sorted(FIELD_WITNESS_FULL_IR_DECODE_REQUIRED_SOURCE_EVIDENCE - source_set)
        extra = sorted(source_set - FIELD_WITNESS_FULL_IR_DECODE_SOURCE_EVIDENCE)
        if missing:
            errors.append(f"schema: {label}.source_evidence missing required source(s): {', '.join(missing)}")
        if extra:
            errors.append(f"schema: {label}.source_evidence unknown source(s): {', '.join(extra)}")

    for key in ("n_frame", "live_registers", "burden_floor", "diagnostic_completeness"):
        if full.get(key) != decoded.get(key):
            errors.append(f"schema: {label}.{key} must match decoded_ir.{key}")

    for key in ("B_LA", "B_MRP", "B_total"):
        expected = string_list(field_witness.get(key))
        if full.get(key) != expected:
            errors.append(f"schema: {label}.{key} must match field_witness.{key}")

    coverage = field_witness.get("coverage_proof")
    if not isinstance(coverage, dict):
        errors.append(f"schema: {label} requires field_witness.coverage_proof")
        coverage = {}
    if full.get("dependency_graph") != coverage.get("dependency_graph"):
        errors.append(f"schema: {label}.dependency_graph must match coverage_proof.dependency_graph")
    if full.get("terminal_states") != coverage.get("terminal_states"):
        errors.append(f"schema: {label}.terminal_states must match coverage_proof.terminal_states")

    expected_generated = field_witness.get("generated_burdens")
    if expected_generated is None:
        expected_generated = []
    if full.get("generated_burdens") != expected_generated:
        errors.append(f"schema: {label}.generated_burdens must match field_witness.generated_burdens")

    if "hard_registers" in projection and full.get("hard_registers") != projection.get("hard_registers"):
        errors.append(f"schema: {label}.hard_registers must match canonical_ir_projection.hard_registers")
    if "hard_registers" not in projection and "hard_registers" in full:
        errors.append(f"schema: {label}.hard_registers requires canonical_ir_projection.hard_registers")
    if projection.get("register_composition") is not None:
        if full.get("register_composition") != projection.get("register_composition"):
            errors.append(f"schema: {label}.register_composition must match canonical_ir_projection.register_composition")
    elif "register_composition" in full:
        errors.append(f"schema: {label}.register_composition requires canonical_ir_projection.register_composition")

    source_basis = full.get("source_basis")
    source_errors = require_exact_keys(source_basis, FULL_IR_DECODE_SOURCE_BASIS_KEYS, f"{label}.source_basis")
    errors.extend(source_errors)
    if not source_errors:
        if not isinstance(source_basis.get("source_basis_available"), bool):
            errors.append(f"schema: {label}.source_basis.source_basis_available must be boolean")
        if source_basis.get("sigma_inside_hard_registers") is not False:
            errors.append(f"schema: {label}.source_basis.sigma_inside_hard_registers must be false")
        basis = source_basis.get("basis")
        if not isinstance(basis, list) or not all(non_empty_string(item) for item in basis):
            errors.append(f"schema: {label}.source_basis.basis must be array of non-empty strings")

    formal = full.get("formal_reread")
    formal_errors = require_exact_keys(formal, FULL_IR_DECODE_FORMAL_REREAD_KEYS, f"{label}.formal_reread")
    errors.extend(formal_errors)
    if not formal_errors:
        if not isinstance(formal.get("states_present"), bool):
            errors.append(f"schema: {label}.formal_reread.states_present must be boolean")
        if not non_empty_string(formal.get("divergence_state")):
            errors.append(f"schema: {label}.formal_reread.divergence_state must be non-empty string")
        if not non_empty_string(formal.get("curl_state")):
            errors.append(f"schema: {label}.formal_reread.curl_state must be non-empty string")
        if not isinstance(formal.get("escape_routes_checked"), list):
            errors.append(f"schema: {label}.formal_reread.escape_routes_checked must be array")
        if "no_new_resultant_proof" not in formal:
            errors.append(f"schema: {label}.formal_reread.no_new_resultant_proof is required")

    decoded_rows = decoded.get("per_burden")
    full_rows = full.get("per_burden")
    if not isinstance(full_rows, list) or not full_rows:
        errors.append(f"schema: {label}.per_burden must be non-empty array")
        return errors
    if isinstance(decoded_rows, list) and len(full_rows) != len(decoded_rows):
        errors.append(f"schema: {label}.per_burden row count must match decoded_ir.per_burden")

    for index, row in enumerate(full_rows):
        row_label = f"{label}.per_burden[{index}]"
        row_errors = require_exact_keys(row, FIELD_WITNESS_FULL_IR_DECODE_ROW_KEYS, row_label)
        errors.extend(row_errors)
        if row_errors:
            continue
        if isinstance(decoded_rows, list) and index < len(decoded_rows):
            decoded_row = decoded_rows[index]
            if isinstance(decoded_row, dict):
                decoded_core = {key: decoded_row.get(key) for key in FIELD_WITNESS_CANONICAL_IR_DECODE_ROW_KEYS}
                full_core = {key: row.get(key) for key in FIELD_WITNESS_CANONICAL_IR_DECODE_ROW_KEYS}
                if full_core != decoded_core:
                    errors.append(f"schema: {row_label} core fields must match decoded_ir.per_burden")
        if row.get("graph_role") not in {"root", "dependent", "isolated"}:
            errors.append(f"schema: {row_label}.graph_role invalid")
        if row.get("track") not in {"baseline", "primary", "restoration"}:
            errors.append(f"schema: {row_label}.track invalid")
        if row.get("generated_by") is not None and not non_empty_string(row.get("generated_by")):
            errors.append(f"schema: {row_label}.generated_by must be null or non-empty string")
    return errors


def full_ir_proof_mode_errors(projection: dict[str, Any]) -> list[str]:
    label = "field_witness.canonical_ir_projection.proof_mode"
    proof_mode = projection.get("proof_mode")
    full_decode = projection.get("full_ir_decode")
    decoded = projection.get("decoded_ir")
    errors: list[str] = []

    if full_decode is not None and proof_mode is None:
        errors.append(
            "schema: field_witness.canonical_ir_projection.full_ir_decode "
            "requires proof_mode adoption marker"
        )
    if proof_mode is None:
        return errors

    errors.extend(require_exact_keys(proof_mode, FIELD_WITNESS_FULL_IR_PROOF_MODE_KEYS, label))
    if full_decode is None:
        errors.append(f"schema: {label} requires field_witness.canonical_ir_projection.full_ir_decode")
    if not isinstance(decoded, dict):
        errors.append(f"schema: {label} requires field_witness.canonical_ir_projection.decoded_ir")
    if errors:
        return errors

    if proof_mode.get("schema") != FULL_IR_PROOF_MODE_SCHEMA:
        errors.append(f"schema: {label}.schema must be {FULL_IR_PROOF_MODE_SCHEMA!r}")
    if proof_mode.get("mode") not in FIELD_WITNESS_FULL_IR_PROOF_MODE_MODES:
        errors.append(f"schema: {label}.mode invalid")

    source_evidence = proof_mode.get("source_evidence")
    if not isinstance(source_evidence, list) or not all(non_empty_string(item) for item in source_evidence):
        errors.append(f"schema: {label}.source_evidence must be array of non-empty strings")
    else:
        source_set = set(source_evidence)
        missing = sorted(FIELD_WITNESS_FULL_IR_PROOF_MODE_SOURCE_EVIDENCE - source_set)
        extra = sorted(source_set - FIELD_WITNESS_FULL_IR_PROOF_MODE_SOURCE_EVIDENCE)
        if missing:
            errors.append(f"schema: {label}.source_evidence missing required source(s): {', '.join(missing)}")
        if extra:
            errors.append(f"schema: {label}.source_evidence unknown source(s): {', '.join(extra)}")

    for key in (
        "machine_facing",
        "schema_light_absent_valid",
        "requires_decoded_ir",
        "visible_opening_header_preserved",
    ):
        if proof_mode.get(key) is not True:
            errors.append(f"schema: {label}.{key} must be true")

    for key in (
        "arbitrary_nl_ir_parser_claim",
        "default_runtime_emission_claim",
        "t_lang_uptake_claim",
    ):
        if proof_mode.get(key) is not False:
            errors.append(f"schema: {label}.{key} must be false")

    return errors


def runtime_emission_policy_errors(projection: dict[str, Any]) -> list[str]:
    label = "field_witness.canonical_ir_projection.emission_policy"
    policy = projection.get("emission_policy")
    if policy is None:
        return []
    errors: list[str] = []
    errors.extend(require_exact_keys(policy, FIELD_WITNESS_RUNTIME_EMISSION_POLICY_KEYS, label))
    if not isinstance(projection.get("proof_mode"), dict):
        errors.append(f"schema: {label} requires field_witness.canonical_ir_projection.proof_mode")
    if not isinstance(projection.get("decoded_ir"), dict):
        errors.append(f"schema: {label} requires field_witness.canonical_ir_projection.decoded_ir")
    if not isinstance(projection.get("full_ir_decode"), dict):
        errors.append(f"schema: {label} requires field_witness.canonical_ir_projection.full_ir_decode")
    if errors:
        return errors

    if policy.get("schema") != RUNTIME_EMISSION_POLICY_SCHEMA:
        errors.append(f"schema: {label}.schema must be {RUNTIME_EMISSION_POLICY_SCHEMA!r}")
    if policy.get("mode") not in FIELD_WITNESS_RUNTIME_EMISSION_POLICY_MODES:
        errors.append(f"schema: {label}.mode invalid")

    source_evidence = policy.get("source_evidence")
    if not isinstance(source_evidence, list) or not all(non_empty_string(item) for item in source_evidence):
        errors.append(f"schema: {label}.source_evidence must be array of non-empty strings")
    else:
        source_set = set(source_evidence)
        missing = sorted(FIELD_WITNESS_RUNTIME_EMISSION_POLICY_SOURCE_EVIDENCE - source_set)
        extra = sorted(source_set - FIELD_WITNESS_RUNTIME_EMISSION_POLICY_SOURCE_EVIDENCE)
        if missing:
            errors.append(f"schema: {label}.source_evidence missing required source(s): {', '.join(missing)}")
        if extra:
            errors.append(f"schema: {label}.source_evidence unknown source(s): {', '.join(extra)}")

    for key in (
        "machine_facing",
        "default_runtime",
        "proof_class_closure_only",
        "requires_projection",
        "requires_decoded_ir",
        "requires_full_ir_decode",
        "visible_opening_header_required",
        "legacy_schema_light_absent_valid",
    ):
        if policy.get(key) is not True:
            errors.append(f"schema: {label}.{key} must be true")

    for key in (
        "public_prose_replacement",
        "arbitrary_nl_ir_parser_claim",
        "t_lang_uptake_claim",
    ):
        if policy.get(key) is not False:
            errors.append(f"schema: {label}.{key} must be false")

    proof_mode = projection["proof_mode"]
    if proof_mode.get("schema") != FULL_IR_PROOF_MODE_SCHEMA:
        errors.append(f"schema: {label}.proof_mode schema must be {FULL_IR_PROOF_MODE_SCHEMA!r}")
    if proof_mode.get("default_runtime_emission_claim") is not False:
        errors.append(
            f"schema: {label} keeps B.5.3 proof_mode v1 default_runtime_emission_claim false"
        )
    return errors


def canonical_ir_projection_errors(field_witness: dict[str, Any]) -> list[str]:
    projection = field_witness.get("canonical_ir_projection")
    if projection is None:
        return []

    errors = require_keys_with_optional(
        projection,
        FIELD_WITNESS_CANONICAL_IR_PROJECTION_KEYS,
        FIELD_WITNESS_CANONICAL_IR_PROJECTION_OPTIONAL_KEYS,
        "field_witness.canonical_ir_projection",
    )
    if errors:
        return errors

    label = "field_witness.canonical_ir_projection"
    if projection.get("schema") != CANONICAL_IR_PROJECTION_SCHEMA:
        errors.append(f"schema: {label}.schema must be {CANONICAL_IR_PROJECTION_SCHEMA!r}")
    if projection.get("diagnostic_ir_schema_version") != HARD_REGISTER_SCHEMA_VERSION:
        errors.append(
            f"schema: {label}.diagnostic_ir_schema_version must be {HARD_REGISTER_SCHEMA_VERSION!r}"
        )

    projected_registers = projection.get("hard_registers")
    errors.extend(hard_register_object_errors(projected_registers, f"{label}.hard_registers"))
    expected_live = (
        canonical_live_registers(projected_registers)
        if isinstance(projected_registers, dict)
        else []
    )
    claimed_live = projection.get("live_registers")
    if not isinstance(claimed_live, list) or not all(non_empty_string(item) for item in claimed_live):
        errors.append(f"schema: {label}.live_registers must be array of non-empty strings")
    elif claimed_live != expected_live:
        errors.append(
            f"schema: {label} hard-register live set mismatch: "
            f"hard_registers={expected_live!r} live_registers={claimed_live!r}"
        )

    normalized = field_witness.get("normalized_activation_record")
    if not isinstance(normalized, dict):
        errors.append(f"schema: {label} requires field_witness.normalized_activation_record")
    else:
        for key in ("n_frame", "live_registers", "burden_floor", "per_burden"):
            if projection.get(key) != normalized.get(key):
                errors.append(
                    f"schema: {label}.{key} must match "
                    f"field_witness.normalized_activation_record.{key}"
                )

    coverage = field_witness.get("coverage_proof")
    witness_diagnostic = coverage.get("diagnostic_completeness") if isinstance(coverage, dict) else None
    projection_diagnostic = projection.get("diagnostic_completeness")
    if projection_diagnostic != witness_diagnostic:
        errors.append(
            f"schema: {label}.diagnostic_completeness must match "
            "field_witness.coverage_proof.diagnostic_completeness"
        )
    if isinstance(projection_diagnostic, dict):
        initial = coverage.get("initial_burden_set") if isinstance(coverage, dict) else None
        errors.extend(
            diagnostic_completeness_reconciliation_errors(
                projection_diagnostic,
                expected_live,
                initial,
                f"{label}.diagnostic_completeness",
            )
        )

    register_deltas = field_witness.get("register_deltas")
    if isinstance(register_deltas, list):
        seen = {
            item.get("register")
            for item in register_deltas
            if isinstance(item, dict) and isinstance(item.get("register"), str)
        }
        missing = [register for register in expected_live if register not in seen]
        for register in missing:
            errors.append(f"schema: {label} missing live hard register delta {register}")
    errors.extend(canonical_ir_decode_errors(projection, field_witness))
    errors.extend(full_ir_decode_errors(projection, field_witness))
    errors.extend(full_ir_proof_mode_errors(projection))
    errors.extend(runtime_emission_policy_errors(projection))
    return errors


def hard_register_field_witness_errors(
    registers: dict[str, Any],
    field_witness: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected = canonical_live_registers(registers)

    normalized = field_witness.get("normalized_activation_record")
    if not isinstance(normalized, dict):
        errors.append(
            "schema: field_witness.normalized_activation_record required for hard-register reconciliation"
        )
    else:
        claimed_live = normalized.get("live_registers")
        if not isinstance(claimed_live, list) or not all(non_empty_string(item) for item in claimed_live):
            errors.append(
                "schema: field_witness.normalized_activation_record.live_registers "
                "must reconcile with hard registers"
            )
        elif claimed_live != expected:
            errors.append(
                "schema: hard-register live set mismatch: "
                f"registers={expected!r} normalized_activation_record.live_registers={claimed_live!r}"
            )

    register_deltas = field_witness.get("register_deltas")
    if isinstance(register_deltas, list):
        seen: set[str] = set()
        for item in register_deltas:
            if not isinstance(item, dict):
                continue
            register = item.get("register")
            if isinstance(register, str):
                if register in NONCANONICAL_HARD_REGISTER_KEYS:
                    errors.append(
                        "schema: field_witness.register_deltas uses noncanonical hard-register key: "
                        f"{register!r}"
                    )
                seen.add(register)
        missing = [register for register in expected if register not in seen]
        for register in missing:
            errors.append(
                f"schema: field_witness.register_deltas missing live hard register {register}"
            )

    coverage = field_witness.get("coverage_proof")
    if isinstance(coverage, dict):
        diagnostic = coverage.get("diagnostic_completeness")
        if not isinstance(diagnostic, dict):
            errors.append(
                "schema: field_witness.coverage_proof.diagnostic_completeness "
                "required for hard-register reconciliation"
            )
        else:
            errors.extend(
                diagnostic_completeness_reconciliation_errors(
                    diagnostic,
                    expected,
                    coverage.get("initial_burden_set"),
                    "field_witness.coverage_proof.diagnostic_completeness",
                )
            )

    projection = field_witness.get("canonical_ir_projection")
    if isinstance(projection, dict):
        projected_registers = projection.get("hard_registers")
        if projected_registers != registers:
            errors.append(
                "schema: field_witness.canonical_ir_projection.hard_registers "
                "must match root registers"
            )

    return errors


def hard_register_errors(instance: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    version = instance.get("diagnostic_ir_schema_version")
    registers = instance.get("registers")
    field_witness = instance.get("field_witness")
    has_projection = (
        isinstance(field_witness, dict)
        and "canonical_ir_projection" in field_witness
    )

    if version is None:
        if registers is not None:
            errors.append(
                f"schema: registers require diagnostic_ir_schema_version {HARD_REGISTER_SCHEMA_VERSION!r}"
            )
        if has_projection:
            errors.append(
                "schema: field_witness.canonical_ir_projection requires "
                f"diagnostic_ir_schema_version {HARD_REGISTER_SCHEMA_VERSION!r}"
            )
        return errors

    if version != HARD_REGISTER_SCHEMA_VERSION:
        errors.append(f"schema: diagnostic_ir_schema_version invalid enum value: {version!r}")
        return errors
    if not isinstance(registers, dict):
        errors.append("schema: registers required for hard-register schema version")
        return errors

    errors.extend(hard_register_object_errors(registers, "registers"))
    if isinstance(field_witness, dict):
        errors.extend(hard_register_field_witness_errors(registers, field_witness))
    return errors


def schema_errors(instance: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = schema.get("required") or []
    for field in required:
        if field not in instance:
            errors.append(f"schema: missing required field: {field}")

    allowed = set(schema.get("properties") or {})
    for field in instance:
        if field not in allowed:
            errors.append(f"schema: additional property not allowed: {field}")

    properties = schema.get("properties") or {}
    for field, spec in properties.items():
        if field not in instance:
            continue
        value = instance[field]
        enum = spec.get("enum")
        if enum is not None and value not in enum:
            errors.append(f"schema: {field} invalid enum value: {value!r}")
        if spec.get("type") == "string":
            if not isinstance(value, str):
                errors.append(f"schema: {field} must be string")
            elif spec.get("minLength", 0) and len(value) < spec["minLength"]:
                errors.append(f"schema: {field} must be non-empty")
        if spec.get("type") == "array" and not isinstance(value, list):
            errors.append(f"schema: {field} must be array")
        if spec.get("type") == "object" and not isinstance(value, dict):
            errors.append(f"schema: {field} must be object")

    if "reason_category" in instance and instance.get("reason_category") not in REASON_CATEGORY_VALUES:
        errors.append(f"schema: reason_category invalid oneOf value: {instance.get('reason_category')!r}")
    errors.extend(hard_register_errors(instance))
    p7_stops = instance.get("p7_stops_active")
    if isinstance(p7_stops, list):
        if "none" in p7_stops and len(p7_stops) > 1:
            errors.append("schema: p7_stops_active cannot combine none with active stops")
        if len(set(p7_stops)) != len(p7_stops):
            errors.append("schema: p7_stops_active must have unique items")

    if instance.get("confidence") != "strong" and "decisive_missing_differentiator" not in instance:
        errors.append("schema: missing required field: decisive_missing_differentiator")
    if instance.get("read_status") != "dominant" and "decisive_missing_differentiator" not in instance:
        errors.append("schema: missing required field: decisive_missing_differentiator")
    if instance.get("read_status") == "underdetermined" and instance.get("confidence") == "strong":
        errors.append("schema: read_status underdetermined cannot pair with strong confidence")
    if instance.get("reconstruction_fidelity") in {"partial", "fail"} and "reconstructor_notes" not in instance:
        errors.append("schema: missing required field: reconstructor_notes")

    matched = instance.get("matched_modules")
    if matched is not None:
        if not isinstance(matched, list) or not matched:
            errors.append("schema: matched_modules must be a non-empty array")
        else:
            for index, item in enumerate(matched):
                if not isinstance(item, dict):
                    errors.append(f"schema: matched_modules[{index}] must be object")
                    continue
                extra = sorted(set(item) - MATCHED_MODULE_KEYS)
                if extra:
                    errors.append(f"schema: matched_modules[{index}] additional property not allowed: {', '.join(extra)}")
                for field in ("id", "module_class"):
                    if not isinstance(item.get(field), str) or not item[field].strip():
                        errors.append(f"schema: matched_modules[{index}].{field} must be non-empty string")
            if "source_basis" not in instance:
                errors.append("schema: source_basis required when matched_modules present")

    source_basis = instance.get("source_basis")
    if source_basis is not None:
        entries = source_basis.get("entries") if isinstance(source_basis, dict) else None
        if isinstance(source_basis, dict):
            extra = sorted(set(source_basis) - SOURCE_BASIS_KEYS)
            if extra:
                errors.append("schema: source_basis additional property not allowed: " + ", ".join(extra))
        if not isinstance(entries, list) or not entries:
            errors.append("schema: source_basis.entries must be a non-empty array")
        else:
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    errors.append(f"schema: source_basis.entries[{index}] must be object")
                    continue
                extra = sorted(set(entry) - SOURCE_BASIS_ENTRY_KEYS)
                if extra:
                    errors.append(f"schema: source_basis.entries[{index}] additional property not allowed: {', '.join(extra)}")
                for field in ("basis_type", "claim", "source_kind"):
                    if not isinstance(entry.get(field), str) or not entry[field].strip():
                        errors.append(f"schema: source_basis.entries[{index}].{field} must be non-empty string")
                if entry.get("basis_type") not in SOURCE_BASIS_TYPES:
                    errors.append(f"schema: source_basis.entries[{index}].basis_type invalid enum value: {entry.get('basis_type')!r}")
                if entry.get("source_kind") not in SOURCE_KINDS:
                    errors.append(f"schema: source_basis.entries[{index}].source_kind invalid enum value: {entry.get('source_kind')!r}")
                if entry.get("source_kind") == "module" and not isinstance(entry.get("module_id"), str):
                    errors.append(f"schema: source_basis.entries[{index}].module_id required for module source")
                if entry.get("basis_type") in {"anchored", "inference", "speculative"} and not isinstance(entry.get("source_ref"), str):
                    errors.append(f"schema: source_basis.entries[{index}].source_ref required for anchored/inference/speculative basis")

    post_gate = instance.get("post_render_gate")
    if isinstance(post_gate, dict):
        extra = sorted(set(post_gate) - POST_RENDER_GATE_KEYS)
        if extra:
            errors.append("schema: post_render_gate additional property not allowed: " + ", ".join(extra))
        required_gate = (properties.get("post_render_gate", {}).get("required") or [])
        for field in required_gate:
            if field not in post_gate:
                errors.append(f"schema: post_render_gate missing required field: {field}")
        for field in ("cleared_this_pass", "remaining_live_distortions", "next_eligible_pass"):
            if field in post_gate and (not isinstance(post_gate.get(field), str) or not post_gate[field].strip()):
                errors.append(f"schema: post_render_gate.{field} must be non-empty string")
        for field in ("held_routes_rechecked", "newly_released_routes"):
            if field in post_gate:
                values = post_gate.get(field)
                if not isinstance(values, list):
                    errors.append(f"schema: post_render_gate.{field} must be array")
                elif len(set(values)) != len(values):
                    errors.append(f"schema: post_render_gate.{field} must have unique items")
        decision = post_gate.get("recursion_decision")
        if decision not in DECISIONS:
            errors.append(f"schema: post_render_gate.recursion_decision invalid: {decision!r}")
    elif post_gate is not None:
        errors.append("schema: post_render_gate must be object")

    field_witness = instance.get("field_witness")
    if field_witness is not None:
        errors.extend(field_witness_errors(field_witness))

    return errors


def require_exact_keys(value: Any, keys: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"schema: {label} must be object"]
    extra = sorted(set(value) - keys)
    missing = sorted(keys - set(value))
    errors: list[str] = []
    if extra:
        errors.append(f"schema: {label} additional property not allowed: {', '.join(extra)}")
    if missing:
        errors.append(f"schema: {label} missing required field: {', '.join(missing)}")
    return errors


def require_keys_with_optional(value: Any, required: set[str], optional: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"schema: {label} must be object"]
    allowed = required | optional
    extra = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    errors: list[str] = []
    if extra:
        errors.append(f"schema: {label} additional property not allowed: {', '.join(extra)}")
    if missing:
        errors.append(f"schema: {label} missing required field: {', '.join(missing)}")
    return errors


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def graph_has_cycle(nodes: list[str], edges: list[tuple[str, str]]) -> bool:
    graph = {node: [] for node in nodes}
    for source, target in edges:
        graph.setdefault(source, []).append(target)
        graph.setdefault(target, [])
    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(node: str) -> bool:
        if node in permanent:
            return False
        if node in temporary:
            return True
        temporary.add(node)
        for target in graph.get(node, []):
            if visit(target):
                return True
        temporary.remove(node)
        permanent.add(node)
        return False

    return any(visit(node) for node in list(graph))


def normalized_activation_record_errors(value: Any) -> list[str]:
    label = "field_witness.normalized_activation_record"
    errors = require_exact_keys(value, FIELD_WITNESS_NAR_KEYS, label)
    if errors:
        return errors
    if not non_empty_string(value.get("n_frame")):
        errors.append(f"schema: {label}.n_frame must be non-empty string")
    for key in ("live_registers", "burden_floor"):
        values = value.get(key)
        if not isinstance(values, list) or not all(non_empty_string(item) for item in values):
            errors.append(f"schema: {label}.{key} must be array of non-empty strings")
    floor = value.get("burden_floor")
    if isinstance(floor, list):
        for item in floor:
            if non_empty_string(item) and not re.fullmatch(r"B[0-9]+", item):
                errors.append(f"schema: {label}.burden_floor item must be graph burden id: {item!r}")

    per_burden = value.get("per_burden")
    if not isinstance(per_burden, list) or not per_burden:
        errors.append(f"schema: {label}.per_burden must be a non-empty array")
        return errors
    for index, item in enumerate(per_burden):
        row_label = f"{label}.per_burden[{index}]"
        row_errors = require_exact_keys(item, FIELD_WITNESS_NAR_ROW_KEYS, row_label)
        errors.extend(row_errors)
        if row_errors:
            continue
        if not re.fullmatch(r"B[0-9]+", str(item.get("burden_id") or "")):
            errors.append(f"schema: {row_label}.burden_id must be graph burden id")
        for key in FIELD_WITNESS_NAR_ROW_KEYS - {"generation_depth"}:
            if not non_empty_string(item.get(key)):
                errors.append(f"schema: {row_label}.{key} must be non-empty string")
        depth = item.get("generation_depth")
        if not isinstance(depth, int) or isinstance(depth, bool) or depth < 0:
            errors.append(f"schema: {row_label}.generation_depth must be non-negative integer")
        errors.extend(
            "schema: " + error
            for error in delta_result_vocabulary_errors(
                row_label,
                str(item.get("owner_id") or ""),
                str(item.get("delta_result") or ""),
            )
        )
    return errors


def field_witness_errors(field_witness: Any) -> list[str]:
    errors = require_keys_with_optional(
        field_witness,
        FIELD_WITNESS_KEYS,
        FIELD_WITNESS_OPTIONAL_KEYS,
        "field_witness",
    )
    if errors:
        return errors

    route = field_witness["route_gradient"]
    errors.extend(require_exact_keys(route, FIELD_WITNESS_ROUTE_KEYS, "field_witness.route_gradient"))
    if isinstance(route, dict):
        eligible = route.get("eligible_routes")
        if not isinstance(eligible, list) or not all(non_empty_string(item) for item in eligible):
            errors.append("schema: field_witness.route_gradient.eligible_routes must be array of non-empty strings")
        if not non_empty_string(route.get("selected")):
            errors.append("schema: field_witness.route_gradient.selected must be non-empty string")
        if not non_empty_string(route.get("reason")):
            errors.append("schema: field_witness.route_gradient.reason must be non-empty string")

    burden_events = field_witness["burden_events"]
    if not isinstance(burden_events, list) or not burden_events:
        errors.append("schema: field_witness.burden_events must be a non-empty array")
    elif not all(isinstance(event, dict) for event in burden_events):
        errors.append("schema: field_witness.burden_events entries must be objects")
    else:
        for index, event in enumerate(burden_events):
            label = f"field_witness.burden_events[{index}]"
            errors.extend(require_exact_keys(event, FIELD_WITNESS_BURDEN_EVENT_KEYS, label))
            for key in FIELD_WITNESS_BURDEN_EVENT_KEYS:
                if not non_empty_string(event.get(key)):
                    errors.append(f"schema: {label}.{key} must be non-empty string")

    if "normalized_activation_record" in field_witness:
        errors.extend(normalized_activation_record_errors(field_witness.get("normalized_activation_record")))

    if "canonical_ir_projection" in field_witness:
        errors.extend(canonical_ir_projection_errors(field_witness))

    diagnostics = field_witness["field_diagnostics"]
    errors.extend(require_exact_keys(diagnostics, FIELD_WITNESS_DIAGNOSTIC_KEYS, "field_witness.field_diagnostics"))
    if isinstance(diagnostics, dict):
        for key in ("divergence", "curl"):
            value = diagnostics.get(key)
            label = f"field_witness.field_diagnostics.{key}"
            errors.extend(require_exact_keys(value, FIELD_WITNESS_TARGET_STATUS_KEYS, label))
            if isinstance(value, dict):
                for subkey in FIELD_WITNESS_TARGET_STATUS_KEYS:
                    if not non_empty_string(value.get(subkey)):
                        errors.append(f"schema: {label}.{subkey} must be non-empty string")

    loopbreak = field_witness["loopbreak"]
    errors.extend(require_exact_keys(loopbreak, FIELD_WITNESS_LOOPBREAK_KEYS, "field_witness.loopbreak"))
    if isinstance(loopbreak, dict):
        if not isinstance(loopbreak.get("licensed"), bool):
            errors.append("schema: field_witness.loopbreak.licensed must be boolean")
        if loopbreak.get("licensed") is True:
            for key in ("target", "ground", "delta_effect", "post_break_reread"):
                if not non_empty_string(loopbreak.get(key)):
                    errors.append(f"schema: field_witness.loopbreak.{key} required when licensed")
        else:
            for key in ("target", "ground", "delta_effect", "post_break_reread"):
                if not isinstance(loopbreak.get(key), str):
                    errors.append(f"schema: field_witness.loopbreak.{key} must be string")

    reconstruction = field_witness["reconstruction"]
    errors.extend(require_exact_keys(reconstruction, FIELD_WITNESS_RECONSTRUCTION_KEYS, "field_witness.reconstruction"))
    if isinstance(reconstruction, dict):
        for key in ("held_set", "live_remainder"):
            values = reconstruction.get(key)
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                errors.append(f"schema: field_witness.reconstruction.{key} must be array of strings")
        if not non_empty_string(reconstruction.get("reread_scope")):
            errors.append("schema: field_witness.reconstruction.reread_scope must be non-empty string")

    closure = field_witness["closure"]
    errors.extend(require_exact_keys(closure, FIELD_WITNESS_CLOSURE_KEYS, "field_witness.closure"))
    if isinstance(closure, dict):
        if closure.get("operator") not in FIELD_WITNESS_CLOSURE_OPERATORS:
            errors.append("schema: field_witness.closure.operator must be 𝒞(Ψᴺ)")
        if closure.get("decision") not in FIELD_WITNESS_CLOSURE_DECISIONS:
            errors.append(f"schema: field_witness.closure.decision invalid: {closure.get('decision')!r}")
        if not non_empty_string(closure.get("agent_field_status")):
            errors.append("schema: field_witness.closure.agent_field_status must be non-empty string")

    transfer = field_witness["transfer_boundary"]
    errors.extend(require_exact_keys(transfer, FIELD_WITNESS_TRANSFER_KEYS, "field_witness.transfer_boundary"))
    if isinstance(transfer, dict):
        if transfer.get("operator") != "T_lang":
            errors.append("schema: field_witness.transfer_boundary.operator must be T_lang")
        if transfer.get("from") not in FIELD_WITNESS_TRANSFER_FROM_VALUES:
            errors.append("schema: field_witness.transfer_boundary.from must be Ψᴺ")
        if transfer.get("to") not in FIELD_WITNESS_TRANSFER_TO_VALUES:
            errors.append("schema: field_witness.transfer_boundary.to must be Ψᴵ")
        if transfer.get("mode") != "coupling-attempt":
            errors.append("schema: field_witness.transfer_boundary.mode must be coupling-attempt")

    register_deltas = field_witness["register_deltas"]
    if (
        not isinstance(register_deltas, list)
        or not register_deltas
        or not all(isinstance(item, dict) for item in register_deltas)
    ):
        errors.append("schema: field_witness.register_deltas must be a non-empty array of register/delta objects")
    else:
        seen_registers: set[str] = set()
        for index, item in enumerate(register_deltas):
            label = f"field_witness.register_deltas[{index}]"
            errors.extend(require_exact_keys(item, FIELD_WITNESS_REGISTER_DELTA_ENTRY_KEYS, label))
            register = item.get("register")
            delta = item.get("delta")
            if not non_empty_string(register):
                errors.append(f"schema: {label}.register must be non-empty string")
            elif register in seen_registers:
                errors.append(f"schema: {label}.register duplicates {register!r}")
            else:
                seen_registers.add(register)
            if not non_empty_string(delta):
                errors.append(f"schema: {label}.delta must be non-empty string")

    non_claims = field_witness["non_claims"]
    if not isinstance(non_claims, list) or not non_claims or not all(non_empty_string(item) for item in non_claims):
        errors.append("schema: field_witness.non_claims must be non-empty array of strings")
    elif not any(re.search(r"(?i)\b(?:uptake|acceptance|soul|truth|warrant|release proof)\b", item) for item in non_claims):
        errors.append("schema: field_witness.non_claims must include proof/uptake/soul/release boundary")

    provenance = field_witness["provenance"]
    errors.extend(require_exact_keys(provenance, FIELD_WITNESS_PROVENANCE_KEYS, "field_witness.provenance"))
    if isinstance(provenance, dict):
        for key in FIELD_WITNESS_PROVENANCE_KEYS:
            if not non_empty_string(provenance.get(key)):
                errors.append(f"schema: field_witness.provenance.{key} must be non-empty string")

    reread_pressure = field_witness.get("reread_pressure")
    if reread_pressure is not None:
        errors.extend(
            require_exact_keys(
                reread_pressure,
                FIELD_WITNESS_REREAD_PRESSURE_KEYS,
                "field_witness.reread_pressure",
            )
        )
        if isinstance(reread_pressure, dict):
            target = reread_pressure.get("target_burden_id")
            if not isinstance(target, str) or not re.fullmatch(r"B\d+", target):
                errors.append("schema: field_witness.reread_pressure.target_burden_id must be burden ID")
            if not non_empty_string(reread_pressure.get("reread_delta")):
                errors.append("schema: field_witness.reread_pressure.reread_delta must be non-empty string")
            if not non_empty_string(reread_pressure.get("route_gradient")):
                errors.append("schema: field_witness.reread_pressure.route_gradient must be non-empty string")
            activations = reread_pressure.get("pressure_activations")
            errors.extend(
                require_exact_keys(
                    activations,
                    FIELD_WITNESS_REREAD_PRESSURE_ACTIVATION_KEYS,
                    "field_witness.reread_pressure.pressure_activations",
                )
            )
            if isinstance(activations, dict):
                for key in FIELD_WITNESS_REREAD_PRESSURE_ACTIVATION_KEYS:
                    if not non_empty_string(activations.get(key)):
                        errors.append(f"schema: field_witness.reread_pressure.pressure_activations.{key} must be non-empty string")
            if reread_pressure.get("finding") not in FIELD_WITNESS_REREAD_PRESSURE_FINDINGS:
                errors.append(f"schema: field_witness.reread_pressure.finding invalid: {reread_pressure.get('finding')!r}")
            if reread_pressure.get("route_result_type") not in FIELD_WITNESS_REREAD_PRESSURE_ROUTE_TYPES:
                errors.append(
                    f"schema: field_witness.reread_pressure.route_result_type invalid: {reread_pressure.get('route_result_type')!r}"
                )
            if reread_pressure.get("divergence_state") not in FIELD_WITNESS_REREAD_PRESSURE_DIVERGENCE:
                errors.append(
                    f"schema: field_witness.reread_pressure.divergence_state invalid: {reread_pressure.get('divergence_state')!r}"
                )
            if reread_pressure.get("curl_state") not in FIELD_WITNESS_REREAD_PRESSURE_CURL:
                errors.append(
                    f"schema: field_witness.reread_pressure.curl_state invalid: {reread_pressure.get('curl_state')!r}"
                )
            if reread_pressure.get("route") not in FIELD_WITNESS_REREAD_PRESSURE_ROUTES:
                errors.append(f"schema: field_witness.reread_pressure.route invalid: {reread_pressure.get('route')!r}")
            if reread_pressure.get("preemption_basis") not in FIELD_WITNESS_REREAD_PRESSURE_PREEMPTION:
                errors.append(
                    f"schema: field_witness.reread_pressure.preemption_basis invalid: {reread_pressure.get('preemption_basis')!r}"
                )
            graph_delta = reread_pressure.get("graph_delta")
            errors.extend(
                require_exact_keys(
                    graph_delta,
                    FIELD_WITNESS_REREAD_PRESSURE_GRAPH_DELTA_KEYS,
                    "field_witness.reread_pressure.graph_delta",
                )
            )
            if isinstance(graph_delta, dict):
                for key in ("nodes_added", "edges_added"):
                    if not isinstance(graph_delta.get(key), list):
                        errors.append(f"schema: field_witness.reread_pressure.graph_delta.{key} must be array")
                for index, node in enumerate(graph_delta.get("nodes_added", [])):
                    if not isinstance(node, str) or not re.fullmatch(r"B\d+", node):
                        errors.append(f"schema: field_witness.reread_pressure.graph_delta.nodes_added[{index}] must be burden ID")
                for index, edge in enumerate(graph_delta.get("edges_added", [])):
                    label = f"field_witness.reread_pressure.graph_delta.edges_added[{index}]"
                    errors.extend(require_exact_keys(edge, FIELD_WITNESS_DEPENDENCY_EDGE_KEYS, label))
                    if isinstance(edge, dict):
                        if not isinstance(edge.get("from"), str) or not re.fullmatch(r"B\d+", edge.get("from", "")):
                            errors.append(f"schema: {label}.from must be burden ID")
                        if not isinstance(edge.get("to"), str) or not re.fullmatch(r"B\d+", edge.get("to", "")):
                            errors.append(f"schema: {label}.to must be burden ID")
                if not non_empty_string(graph_delta.get("note")):
                    errors.append("schema: field_witness.reread_pressure.graph_delta.note must be non-empty string")
            local_non_claims = reread_pressure.get("non_claims")
            if not isinstance(local_non_claims, list) or not local_non_claims or not all(non_empty_string(item) for item in local_non_claims):
                errors.append("schema: field_witness.reread_pressure.non_claims must be non-empty array of strings")
            elif not any(re.search(r"(?i)\b(?:uptake|acceptance|conversion|guidance|soul)\b", item) for item in local_non_claims):
                errors.append("schema: field_witness.reread_pressure.non_claims must include uptake/guidance boundary")

    coverage = field_witness.get("coverage_proof")
    if coverage is not None:
        errors.extend(
            require_keys_with_optional(
                coverage,
                FIELD_WITNESS_COVERAGE_KEYS,
                FIELD_WITNESS_COVERAGE_OPTIONAL_KEYS,
                "field_witness.coverage_proof",
            )
        )
        if isinstance(coverage, dict):
            initial = coverage.get("initial_burden_set")
            terminals = coverage.get("terminal_states")
            if not isinstance(initial, list) or not initial or not all(isinstance(item, str) and re.fullmatch(r"B\d+", item) for item in initial):
                errors.append("schema: field_witness.coverage_proof.initial_burden_set must be non-empty B-id array")
                initial = []
            if len(set(initial)) != len(initial):
                errors.append("schema: field_witness.coverage_proof.initial_burden_set must be unique")
            if not isinstance(terminals, dict):
                errors.append("schema: field_witness.coverage_proof.terminal_states must be object")
                terminals = {}
            for burden in initial:
                if burden not in terminals:
                    errors.append(f"schema: field_witness.coverage_proof missing terminal state for {burden}")
            expected_complete = bool(initial) and all(burden in terminals for burden in initial)
            if coverage.get("coverage_complete") != expected_complete:
                errors.append("schema: field_witness.coverage_proof.coverage_complete does not match terminal-state coverage")
            for burden, terminal in terminals.items():
                if not re.fullmatch(r"B\d+", str(burden)):
                    errors.append(f"schema: field_witness.coverage_proof terminal key must be burden ID: {burden!r}")
                if not isinstance(terminal, dict):
                    errors.append(f"schema: field_witness.coverage_proof.{burden} must be object")
                    continue
                if terminal.get("state") not in FIELD_WITNESS_TERMINAL_STATES:
                    errors.append(
                        f"schema: field_witness.coverage_proof.{burden}.state invalid: {terminal.get('state')!r}"
                    )
                for key in set(terminal) - {"state", "operator", "delta_nB", "reason"}:
                    errors.append(f"schema: field_witness.coverage_proof.{burden} additional property not allowed: {key}")
            diagnostic = coverage.get("diagnostic_completeness")
            if diagnostic is not None:
                errors.extend(
                    require_exact_keys(
                        diagnostic,
                        FIELD_WITNESS_DIAGNOSTIC_COMPLETENESS_KEYS,
                        "field_witness.coverage_proof.diagnostic_completeness",
                    )
                )
                if isinstance(diagnostic, dict):
                    live_registers = diagnostic.get("live_registers")
                    if (
                        not isinstance(live_registers, list)
                        or not all(non_empty_string(item) for item in live_registers)
                    ):
                        errors.append(
                            "schema: field_witness.coverage_proof.diagnostic_completeness.live_registers "
                            "must be array of non-empty strings"
                        )
                    elif len(set(live_registers)) != len(live_registers):
                        errors.append(
                            "schema: field_witness.coverage_proof.diagnostic_completeness.live_registers "
                            "must be unique"
                        )
                    diagnostic_coverage = diagnostic.get("coverage")
                    if not isinstance(diagnostic_coverage, dict):
                        errors.append(
                            "schema: field_witness.coverage_proof.diagnostic_completeness.coverage "
                            "must be object"
                        )
                    else:
                        for register, burdens in diagnostic_coverage.items():
                            if not non_empty_string(register):
                                errors.append(
                                    "schema: field_witness.coverage_proof.diagnostic_completeness.coverage "
                                    "keys must be non-empty strings"
                                )
                                continue
                            if not isinstance(burdens, list) or not burdens:
                                errors.append(
                                    "schema: field_witness.coverage_proof.diagnostic_completeness.coverage."
                                    f"{register} must be non-empty B-id array"
                                )
                                continue
                            for burden in burdens:
                                if not isinstance(burden, str) or not re.fullmatch(r"B\d+", burden):
                                    errors.append(
                                        "schema: field_witness.coverage_proof.diagnostic_completeness.coverage."
                                        f"{register} item must be burden ID"
                                    )
                                elif initial and burden not in initial:
                                    errors.append(
                                        "schema: field_witness.coverage_proof.diagnostic_completeness.coverage."
                                        f"{register} maps to non-floor burden {burden}"
                                    )
                    if not isinstance(diagnostic.get("complete"), bool):
                        errors.append(
                            "schema: field_witness.coverage_proof.diagnostic_completeness.complete "
                            "must be boolean"
                        )
            dependency_graph = coverage.get("dependency_graph")
            errors.extend(
                require_exact_keys(
                    dependency_graph,
                    FIELD_WITNESS_DEPENDENCY_GRAPH_KEYS,
                    "field_witness.coverage_proof.dependency_graph",
                )
            )
            if isinstance(dependency_graph, dict):
                nodes = dependency_graph.get("nodes")
                roots = dependency_graph.get("roots")
                raw_edges = dependency_graph.get("edges")
                raw_parallel = dependency_graph.get("parallel_groups")
                if not isinstance(nodes, list) or not nodes or not all(isinstance(node, str) and re.fullmatch(r"B\d+", node) for node in nodes):
                    errors.append("schema: field_witness.coverage_proof.dependency_graph.nodes must be non-empty B-id array")
                    nodes = []
                if len(set(nodes)) != len(nodes):
                    errors.append("schema: field_witness.coverage_proof.dependency_graph.nodes must be unique")
                if set(nodes) != set(initial) | set(terminals):
                    errors.append("schema: field_witness.coverage_proof.dependency_graph.nodes must match initial burdens and terminal states")
                if not isinstance(roots, list) or not all(isinstance(node, str) and re.fullmatch(r"B\d+", node) for node in roots):
                    errors.append("schema: field_witness.coverage_proof.dependency_graph.roots must be B-id array")
                    roots = []
                edges: list[tuple[str, str]] = []
                if not isinstance(raw_edges, list):
                    errors.append("schema: field_witness.coverage_proof.dependency_graph.edges must be array")
                    raw_edges = []
                for index, edge in enumerate(raw_edges):
                    label = f"field_witness.coverage_proof.dependency_graph.edges[{index}]"
                    errors.extend(require_exact_keys(edge, FIELD_WITNESS_DEPENDENCY_EDGE_KEYS, label))
                    if not isinstance(edge, dict):
                        continue
                    source = edge.get("from")
                    target = edge.get("to")
                    if not isinstance(source, str) or not re.fullmatch(r"B\d+", source):
                        errors.append(f"schema: {label}.from must be B-id")
                        continue
                    if not isinstance(target, str) or not re.fullmatch(r"B\d+", target):
                        errors.append(f"schema: {label}.to must be B-id")
                        continue
                    if source not in nodes or target not in nodes:
                        errors.append("schema: field_witness.coverage_proof.dependency_graph edge endpoint not in nodes")
                    edges.append((source, target))
                if not isinstance(raw_parallel, list):
                    errors.append("schema: field_witness.coverage_proof.dependency_graph.parallel_groups must be array")
                    raw_parallel = []
                for index, group in enumerate(raw_parallel):
                    if not isinstance(group, list) or len(group) < 2 or not all(isinstance(node, str) and re.fullmatch(r"B\d+", node) for node in group):
                        errors.append(f"schema: field_witness.coverage_proof.dependency_graph.parallel_groups[{index}] must contain at least two B-ids")
                    elif any(node not in nodes for node in group):
                        errors.append(f"schema: field_witness.coverage_proof.dependency_graph.parallel_groups[{index}] node not in nodes")
                indegree = {node: 0 for node in nodes}
                for _source, target in edges:
                    indegree[target] = indegree.get(target, 0) + 1
                for root in roots:
                    if root not in nodes:
                        errors.append(f"schema: field_witness.coverage_proof.dependency_graph root not in nodes: {root}")
                    elif indegree.get(root, 0) != 0:
                        errors.append(f"schema: field_witness.coverage_proof.dependency_graph root has upstream dependency: {root}")
                for node, degree in indegree.items():
                    if degree == 0 and node not in roots:
                        errors.append(f"schema: field_witness.coverage_proof.dependency_graph node missing root marker: {node}")
                actual_acyclic = not graph_has_cycle(nodes, edges)
                if not actual_acyclic:
                    errors.append("schema: field_witness.coverage_proof.dependency_graph contains a cycle")
                if not isinstance(dependency_graph.get("acyclic"), bool):
                    errors.append("schema: field_witness.coverage_proof.dependency_graph.acyclic must be boolean")
                elif dependency_graph.get("acyclic") != actual_acyclic:
                    errors.append("schema: field_witness.coverage_proof.dependency_graph.acyclic does not match graph")
            if not isinstance(coverage.get("divergence_check"), str):
                errors.append("schema: field_witness.coverage_proof.divergence_check must be string")
            if not isinstance(coverage.get("curl_check"), str):
                errors.append("schema: field_witness.coverage_proof.curl_check must be string")
            if not isinstance(coverage.get("coverage_complete"), bool):
                errors.append("schema: field_witness.coverage_proof.coverage_complete must be boolean")

    return errors


def integrity_errors(
    instance: dict[str, Any],
    catalogue: dict[str, dict[str, Any]],
    compiled_modules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    matched = instance.get("matched_modules") or []
    if not isinstance(matched, list):
        return errors

    matched_ids: list[str] = []
    for item in matched:
        if not isinstance(item, dict):
            continue
        module_id = item.get("id")
        module_class = item.get("module_class")
        if not isinstance(module_id, str):
            continue
        matched_ids.append(module_id)
        if OMNIBUS_RE.search(module_id):
            errors.append(f"omnibus/path used as matched module id: {module_id}")
        catalogue_entry = catalogue.get(module_id)
        if catalogue_entry is None:
            errors.append(f"module id not found in catalogue: {module_id}")
        elif catalogue_entry.get("module_class") != module_class:
            errors.append(
                f"module_class mismatch for {module_id}: "
                f"{module_class!r} != {catalogue_entry.get('module_class')!r}"
            )
        compiled_entry = compiled_modules.get(module_id)
        if compiled_entry is None:
            errors.append(f"matched module does not resolve in compiled-module-map.json: {module_id}")
        elif not compiled_entry.get("bundle_path"):
            errors.append(f"matched module lacks compiled bundle_path: {module_id}")

    if matched_ids and "source_basis" not in instance:
        errors.append("source_basis missing while matched_modules present")
        return errors

    source_basis = instance.get("source_basis") or {}
    entries = source_basis.get("entries") if isinstance(source_basis, dict) else []
    module_entries = [entry for entry in entries if isinstance(entry, dict) and entry.get("source_kind") == "module"]
    for entry in module_entries:
        module_id = entry.get("module_id")
        if not isinstance(module_id, str) or not module_id.strip():
            errors.append("module source_basis entry lacks module_id")
            continue
        if module_id not in catalogue:
            errors.append(f"source_basis module_id not found in catalogue: {module_id}")
        claim = entry.get("claim")
        if not isinstance(claim, str) or not claim.strip():
            errors.append(f"module source_basis entry lacks claim/routing fork: {module_id}")
        elif re.fullmatch(r"(?i)\s*(?:module used|supporting source|source|module|support)\s*\.?", claim):
            errors.append(f"module source_basis entry uses vague claim/routing fork: {module_id}")

    for module_id in matched_ids:
        if not any(entry.get("module_id") == module_id for entry in module_entries):
            errors.append(f"ghost-load: {module_id} lacks matching module source_basis entry")

    gate = instance.get("post_render_gate")
    if not isinstance(gate, dict):
        errors.append("post_render_gate missing or not object")
        return errors

    decision = gate.get("recursion_decision")
    remaining = gate.get("remaining_live_distortions")
    newly_released = gate.get("newly_released_routes")
    next_pass = gate.get("next_eligible_pass")
    held = gate.get("held_routes_rechecked")

    if decision == "STOP":
        if not is_noneish(remaining):
            errors.append("STOP requires remaining_live_distortions none")
        if not is_noneish(newly_released):
            errors.append("STOP requires newly_released_routes empty")
        if not is_noneish(next_pass):
            errors.append("STOP requires next_eligible_pass none")
    elif decision == "HOLD":
        if not is_noneish(newly_released):
            errors.append("HOLD invalid while newly_released_routes is non-empty")
        if not is_noneish(next_pass):
            errors.append("HOLD invalid while next_eligible_pass is live")
        if is_noneish(remaining) and is_noneish(held):
            errors.append("HOLD requires remaining or held material")
    elif decision == "RECURSE":
        if is_noneish(next_pass):
            errors.append("RECURSE requires next_eligible_pass")
        if is_noneish(remaining) and is_noneish(newly_released):
            errors.append("RECURSE requires remaining_live_distortions or newly_released_routes")
    elif decision == "PARTIAL":
        if is_noneish(next_pass) and is_noneish(remaining):
            errors.append("PARTIAL requires remaining_live_distortions or next_eligible_pass")

    # Defensive type check for fields the consistency rules depend on.
    if not isinstance(newly_released, list):
        errors.append("post_render_gate.newly_released_routes must be array")
    if not isinstance(held, list):
        errors.append("post_render_gate.held_routes_rechecked must be array")
    for value in string_list(newly_released) + string_list(held):
        if not value.strip():
            errors.append("post_render_gate route arrays must not contain blank entries")

    return errors


def load_catalogue(root: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(root / "atomics/skill/references/diagnostics/module-catalogue.json")
    return {entry["id"]: entry for entry in payload.get("modules", [])}


def load_compiled_modules(root: Path) -> dict[str, Any]:
    payload = load_json(out_dir(root) / "compiled-module-map.json")
    modules = payload.get("modules")
    return modules if isinstance(modules, dict) else {}


def iter_json_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.json") if ".git" not in path.parts)


def validate_instance(
    label: str,
    instance: dict[str, Any],
    schema: dict[str, Any],
    catalogue: dict[str, dict[str, Any]],
    compiled_modules: dict[str, Any],
) -> list[str]:
    errors = schema_errors(instance, schema)
    # The catalogue/source-basis checks still run after schema checks so one
    # bad fixture can expose every relevant failure in one pass.
    errors.extend(integrity_errors(instance, catalogue, compiled_modules))
    return [f"{label}: {error}" for error in errors]


def check_bad_samples(
    schema: dict[str, Any],
    catalogue: dict[str, dict[str, Any]],
    compiled_modules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    positive_errors = validate_instance("positive sample", POSITIVE_SAMPLE, schema, catalogue, compiled_modules)
    if positive_errors:
        errors.extend(positive_errors)
    hard_positive_errors = validate_instance(
        "hard-register positive sample",
        HARD_REGISTER_POSITIVE_SAMPLE,
        schema,
        catalogue,
        compiled_modules,
    )
    if hard_positive_errors:
        errors.extend(hard_positive_errors)
    hard_projection_positive_errors = validate_instance(
        "hard-register projection positive sample",
        HARD_REGISTER_PROJECTION_POSITIVE_SAMPLE,
        schema,
        catalogue,
        compiled_modules,
    )
    if hard_projection_positive_errors:
        errors.extend(hard_projection_positive_errors)
    hard_decode_positive_errors = validate_instance(
        "hard-register decode positive sample",
        HARD_REGISTER_DECODE_POSITIVE_SAMPLE,
        schema,
        catalogue,
        compiled_modules,
    )
    if hard_decode_positive_errors:
        errors.extend(hard_decode_positive_errors)
    for name, (sample, expected) in BAD_SAMPLES.items():
        found = validate_instance(name, sample, schema, catalogue, compiled_modules)
        if not any(expected in error for error in found):
            errors.append(f"bad sample {name!r} was not rejected with {expected!r}; got {found!r}")
    for name, (sample, expected, missing_module_id) in COMPILED_MAP_BAD_SAMPLES.items():
        compiled_without_module = dict(compiled_modules)
        compiled_without_module.pop(missing_module_id, None)
        found = validate_instance(name, sample, schema, catalogue, compiled_without_module)
        if not any(expected in error for error in found):
            errors.append(f"bad sample {name!r} was not rejected with {expected!r}; got {found!r}")
    return errors


def expected_invalid_fixture(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to((root / "tests/ir-fixtures/invalid").resolve())
    except ValueError:
        return False
    return relative.parts != ()


def smoke_sidecar(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to((root / "smokes").resolve())
    except ValueError:
        return False
    return (
        len(relative.parts) == 3
        and re.fullmatch(r"runtime-grounding-v\d+", relative.parts[0]) is not None
        and relative.name == "ir.json"
    )


def valid_fixture(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to((root / "tests/ir-fixtures/valid").resolve())
    except ValueError:
        return False
    return relative.parts != ()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", action="append", default=[], help="IR JSON artifact to validate.")
    parser.add_argument("--root", action="append", default=[], help="Directory tree containing IR JSON artifacts.")
    parser.add_argument("--samples-only", action="store_true", help="Only run embedded sample checks.")
    parser.add_argument(
        "--include-smoke-sidecars",
        dest="include_smoke_sidecars",
        action="store_true",
        default=True,
        help="Include smokes/runtime-grounding-v*/<fixture>/ir.json sidecars when scanning defaults.",
    )
    parser.add_argument(
        "--no-include-smoke-sidecars",
        dest="include_smoke_sidecars",
        action="store_false",
        help="Do not include smoke ir.json sidecars in the default scan.",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    schema = load_json(root / "atomics/skill/references/diagnostics/diagnostic-ir.schema.json")
    catalogue = load_catalogue(root)
    compiled_modules = load_compiled_modules(root)

    errors = check_bad_samples(schema, catalogue, compiled_modules)
    files_checked = 0
    instances_checked = 0
    valid_fixtures_checked = 0
    expected_invalid_checked = 0
    smoke_sidecars_checked = 0
    smoke_sidecar_paths_checked: set[Path] = set()
    ignored = 0

    paths: list[Path] = []
    explicit_paths = [Path(item) for item in args.file] + [Path(item) for item in args.root]
    if explicit_paths:
        for path in explicit_paths:
            resolved = path if path.is_absolute() else root / path
            if not resolved.exists():
                errors.append(f"IR artifact path does not exist: {resolved}")
                continue
            paths.extend(iter_json_files(resolved))
    elif not args.samples_only:
        default_root = root / "tests/ir-fixtures"
        paths.extend(iter_json_files(default_root))
        if args.include_smoke_sidecars:
            smoke_root = root / "smokes"
            if smoke_root.exists():
                paths.extend(sorted(smoke_root.glob("runtime-grounding-v*/*/ir.json")))

    if not args.samples_only:
        for path in paths:
            try:
                payload = load_json(path)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}: JSON parse error: {exc}")
                continue
            files_checked += 1
            instances = as_instances(payload)
            if not instances:
                if expected_invalid_fixture(path, root):
                    errors.append(f"{path.relative_to(root).as_posix()}: expected-invalid fixture is not IR-like")
                ignored += 1
                continue
            for index, instance in enumerate(instances):
                label = f"{path.relative_to(root).as_posix()}[{index}]"
                found = validate_instance(label, instance, schema, catalogue, compiled_modules)
                if expected_invalid_fixture(path, root):
                    expected_invalid_checked += 1
                    if not found:
                        errors.append(f"{label}: expected-invalid fixture unexpectedly passed")
                else:
                    errors.extend(found)
                    instances_checked += 1
                    if valid_fixture(path, root):
                        valid_fixtures_checked += 1
                    elif smoke_sidecar(path, root):
                        smoke_sidecar_paths_checked.add(path)
                        smoke_sidecars_checked += 1

    if not errors:
        print("Diagnostic IR instance integrity summary")
        print("------------------------------------------------------------")
        print(f"Embedded bad samples checked: {len(BAD_SAMPLES) + len(COMPILED_MAP_BAD_SAMPLES)}")
        print(f"tests/ir-fixtures valid checked: {valid_fixtures_checked}")
        print(f"tests/ir-fixtures invalid checked: {expected_invalid_checked}")
        print(f"smoke sidecars checked: {len(smoke_sidecar_paths_checked)}")
        print(f"smoke sidecar IR instances checked: {smoke_sidecars_checked}")
        print(f"Non-IR JSON files ignored: {ignored}")
        print(f"Total JSON files scanned: {files_checked}")
        print(f"Total expected-valid IR instances checked: {instances_checked}")
        print("------------------------------------------------------------")
    return fail_with_errors("diagnostic IR instance integrity", errors)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
