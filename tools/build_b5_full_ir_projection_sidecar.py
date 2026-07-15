#!/usr/bin/env python3
"""Build a checker-owned B.5.4 full-IR projection sidecar.

This builder does not parse arbitrary natural language into IR. It derives a
machine-facing projection only from an already governed output's visible ACT
records, parser-stable field_witness, normalized_activation_record, coverage
proof, and retained sidecar evidence.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import check_nla_decode_semantic_faithfulness as nla_decode
from check_collapse_certificate_schema import certificate_errors
from check_graph_completeness import input_fingerprint_for_path
from check_mrp_generated_burden import graph_burden_id, graph_submove_id, strict_owner_family


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = "tools/build_b5_full_ir_projection_sidecar.py"
SIDECAR_SCHEMA = "b5-retained-proof-mode-full-ir-sidecar-v1"
PROOF_MODE = "retained-proof-corpus-sidecar"
CURRENT_PUBLIC_WITNESS_SCHEMA = "public-field-witness-v1"
CURRENT_ADAPTER_SCHEMA = "b5-current-public-field-witness-adapter-v1"
CURRENT_DIAGNOSTIC_SCHEMA = "b5-current-checker-diagnostic-evidence-v1"
CURRENT_STAGE_IDS = (
    "stage-02-layer-a-diagnostic-ir",
    "stage-04-burden-execution-act",
    "stage-05-mrp-reread-terminal-state",
    "stage-06-field-witness-nar",
)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    if not path.exists():
        return None, [f"{rel(path)}: file not found"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)}: invalid JSON: {exc}"]


def require_existing(path: Path, label: str) -> list[str]:
    if not path.exists():
        return [f"{label}: {rel(path)} missing"]
    if not path.is_file():
        return [f"{label}: {rel(path)} is not a file"]
    return []


def mirror_key(item: dict[str, Any]) -> tuple[str, str, str, str]:
    delta_result = str(item.get("delta") or "").split(":", 1)[-1]
    return (
        graph_burden_id(item.get("target") or item.get("source")),
        strict_owner_family(str(item.get("owner") or "")),
        str(item.get("operation") or ""),
        delta_result,
    )


def projection_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        graph_burden_id(row.get("burden_id")),
        strict_owner_family(str(row.get("owner_id") or "")),
        str(row.get("operation") or ""),
        str(row.get("delta_result") or ""),
    )


def mirror_for_projection_row(
    row: dict[str, Any],
    mirrors: list[dict[str, Any]],
    used: set[int],
    errors: list[str],
    index: int,
) -> dict[str, Any] | None:
    wanted = projection_key(row)
    matches = [
        (mirror_index, mirror)
        for mirror_index, mirror in enumerate(mirrors)
        if mirror_index not in used and mirror_key(mirror) == wanted
    ]
    if len(matches) != 1:
        errors.append(
            "normalized_activation_record.per_burden"
            f"[{index}]: expected exactly one owner_activation mirror for {wanted!r}, found {len(matches)}"
        )
        return None
    mirror_index, mirror = matches[0]
    used.add(mirror_index)
    return mirror


def source_basis_object(field_witness: dict[str, Any]) -> dict[str, Any]:
    raw = field_witness.get("source_basis")
    if isinstance(raw, dict):
        basis = raw.get("basis")
        if not isinstance(basis, list) or not all(isinstance(item, str) for item in basis):
            basis = []
        return {
            "source_basis_available": True,
            "sigma_inside_hard_registers": False,
            "basis": basis,
        }
    return {
        "source_basis_available": False,
        "sigma_inside_hard_registers": False,
        "basis": [],
    }


def formal_reread_object(field_witness: dict[str, Any]) -> dict[str, Any]:
    coverage = nla_decode.coverage_proof(field_witness)
    states = nla_decode.formal_reread_states(field_witness)
    final_state = states[-1] if states else {}
    return {
        "states_present": bool(states),
        "divergence_state": final_state.get("divergence_state", coverage.get("divergence_check")),
        "curl_state": final_state.get("curl_state", coverage.get("curl_check")),
        "escape_routes_checked": nla_decode.flattened_escape_routes(states),
        "no_new_resultant_proof": nla_decode.terminal_no_new_resultant_proof(states),
    }


def _string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return None
    return list(value)


def _current_stage_map(
    stage_carriers: Any,
) -> tuple[dict[str, dict[str, Any]] | None, list[str]]:
    if not isinstance(stage_carriers, list):
        return None, ["current B.5 adapter requires a Stage02/04/05/06 carrier list"]
    errors: list[str] = []
    stage_map: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(stage_carriers):
        if not isinstance(raw, dict):
            errors.append(f"current B.5 adapter carrier[{index}] must be an object")
            continue
        stage_id = raw.get("id")
        if stage_id not in CURRENT_STAGE_IDS:
            errors.append(
                "mixed Stage02/04/05/06 carrier set contains unsupported stage "
                f"{stage_id!r}"
            )
            continue
        if stage_id in stage_map:
            errors.append(f"duplicate Stage02/04/05/06 carrier: {stage_id}")
            continue
        if raw.get("status") != "pass":
            errors.append(f"current B.5 adapter carrier {stage_id} must already be status=pass")
        stage_map[stage_id] = raw
    missing = [stage_id for stage_id in CURRENT_STAGE_IDS if stage_id not in stage_map]
    if missing:
        errors.append(f"missing required Stage02/04/05/06 carrier: {missing}")
    if len(stage_carriers) != len(CURRENT_STAGE_IDS) and not missing and not any(
        "duplicate Stage02/04/05/06 carrier" in error for error in errors
    ):
        errors.append("mixed Stage02/04/05/06 carrier set must contain exactly four records")
    return (None if errors else stage_map), errors


def _current_terminal_states(field_witness: dict[str, Any]) -> dict[str, str] | None:
    coverage = nla_decode.coverage_proof(field_witness)
    raw = coverage.get("terminal_states")
    if not isinstance(raw, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in raw.items()):
        return None
    return dict(raw)


def _current_dependency_edges(value: Any) -> list[tuple[str, str]] | None:
    if not isinstance(value, list):
        return None
    edges: list[tuple[str, str]] = []
    for row in value:
        if not isinstance(row, dict):
            return None
        source = graph_burden_id(row.get("from") or row.get("source"))
        target = graph_burden_id(row.get("to") or row.get("target"))
        if not source or not target:
            return None
        edges.append((source, target))
    return edges


def _current_diagnostic_evidence(
    *,
    stage_map: dict[str, dict[str, Any]],
    field_witness: dict[str, Any],
    records: list[Any],
    certificate: dict[str, Any],
) -> dict[str, Any]:
    stage02 = stage_map[CURRENT_STAGE_IDS[0]]
    carrier_hashes = {
        stage_id: nla_decode.canonical_json_sha256(stage_map[stage_id])
        for stage_id in CURRENT_STAGE_IDS
    }
    return {
        "schema": CURRENT_DIAGNOSTIC_SCHEMA,
        "selected_n_frame": stage02.get("selected_n_frame"),
        "live_registers": copy.deepcopy(stage02.get("live_registers")),
        "burden_floor": copy.deepcopy(stage02.get("burden_floor")),
        "collapse_certificate": {
            key: certificate.get(key)
            for key in ("collapse_positive", "coverage_complete", "diagnostic_completeness")
        },
        "stage_carrier_sha256": carrier_hashes,
        "public_field_witness_sha256": nla_decode.canonical_json_sha256(field_witness),
        "visible_act_sha256": nla_decode.canonical_json_sha256(
            [str(record.record) for record in records]
        ),
    }


def build_current_projection(
    field_witness: dict[str, Any],
    records: list[Any],
    stage_carriers: Any,
    certificate: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str]]:
    """Adapt validated current carriers without changing the public witness schema."""

    errors: list[str] = []
    if field_witness.get("schema_version") != CURRENT_PUBLIC_WITNESS_SCHEMA:
        return None, [
            "mixed witness contract: current B.5 adapter requires public-field-witness-v1"
        ]
    stage_map, found = _current_stage_map(stage_carriers)
    errors.extend(found)
    if stage_map is None:
        return None, errors
    if any(certificate.get(key) is not True for key in ("collapse_positive", "coverage_complete", "diagnostic_completeness")):
        errors.append("current B.5 adapter requires a positive checker-owned collapse certificate")

    stage02 = stage_map[CURRENT_STAGE_IDS[0]]
    stage04 = stage_map[CURRENT_STAGE_IDS[1]]
    stage05 = stage_map[CURRENT_STAGE_IDS[2]]
    stage06 = stage_map[CURRENT_STAGE_IDS[3]]

    selected_n_frame = stage02.get("selected_n_frame")
    live_registers = _string_list(stage02.get("live_registers"))
    burden_floor = _string_list(stage02.get("burden_floor"))
    if not isinstance(selected_n_frame, str) or not selected_n_frame:
        errors.append("Stage02 selected_n_frame must be a non-empty string")
    if live_registers is None or len(live_registers) != len(set(live_registers)):
        errors.append("Stage02 live_registers must be a unique string list")
        live_registers = []
    if burden_floor is None or len(burden_floor) != len(set(burden_floor)):
        errors.append("Stage02 burden_floor must be a unique string list")
        burden_floor = []

    b_la = nla_decode.burden_list(field_witness, "B_LA")
    b_mrp = nla_decode.burden_list(field_witness, "B_MRP")
    b_total = nla_decode.burden_list(field_witness, "B_total")
    if b_total != [*b_la, *b_mrp] or len(b_total) != len(set(b_total)):
        errors.append("current public witness B_total must equal unique ordered B_LA plus B_MRP")
    coverage = nla_decode.coverage_proof(field_witness)
    if burden_floor != b_la or burden_floor != coverage.get("initial_burden_set"):
        errors.append("Stage02 burden_floor must equal current B_LA and coverage initial_burden_set")

    terminal_states = _current_terminal_states(field_witness)
    if terminal_states is None or list(terminal_states) != b_total:
        errors.append("current public witness terminal_states must cover ordered B_total")
        terminal_states = {}
    stage05_terminals = stage05.get("terminal_states")
    if stage05_terminals != terminal_states:
        errors.append("Stage05 terminal_state mapping differs from current public witness")
    public_terminal_states = field_witness.get("terminal_states")
    if not isinstance(public_terminal_states, dict):
        errors.append("current public witness typed terminal_states are required")
        public_terminal_states = {}
    for burden in b_total:
        payload = public_terminal_states.get(burden)
        if not isinstance(payload, dict) or payload.get("state") != terminal_states.get(burden):
            errors.append(f"current public witness terminal_state drift for {burden}")

    nodes = field_witness.get("nodes")
    node_by_burden: dict[str, dict[str, Any]] = {}
    if not isinstance(nodes, list):
        errors.append("current public witness nodes must be a list")
    else:
        for row in nodes:
            if not isinstance(row, dict):
                errors.append("current public witness node must be an object")
                continue
            burden = graph_burden_id(row.get("id"))
            if not burden or burden in node_by_burden:
                errors.append("current public witness nodes contain a missing or duplicate burden id")
                continue
            depth = row.get("generation_depth")
            if type(depth) is not int or depth < 0:
                errors.append(f"current public witness generation_depth invalid for {burden}")
            node_by_burden[burden] = row
        if list(node_by_burden) != b_total:
            errors.append("current public witness node order must equal B_total")

    public_activations = field_witness.get("owner_activations")
    if not isinstance(public_activations, list) or not public_activations or not all(
        isinstance(row, dict) for row in public_activations
    ):
        errors.append("current public witness owner_activations must be a non-empty object list")
        public_activations = []
    ordinals = [row.get("ordinal") for row in public_activations]
    if ordinals != list(range(len(public_activations))):
        errors.append("current public witness owner activation ordinals must be contiguous and ordered")
    public_refs = [graph_submove_id(row.get("body_ref")) for row in public_activations]
    if not all(public_refs) or len(public_refs) != len(set(public_refs)):
        errors.append("current public witness owner activation body_ref values must be unique")

    public_nar = field_witness.get("normalized_activation_record")
    nar_rows = public_nar.get("per_burden") if isinstance(public_nar, dict) else None
    if not isinstance(public_nar, dict) or public_nar.get("schema_version") != "daee-nar-v2" or not isinstance(nar_rows, list):
        errors.append("current public witness daee-nar-v2 per_burden rows are required")
        nar_rows = []
    partition: list[int] = []
    if [graph_burden_id(row.get("burden_id")) for row in nar_rows if isinstance(row, dict)] != b_total:
        errors.append("current public witness NAR burden order must equal B_total")
    for row in nar_rows:
        if not isinstance(row, dict):
            errors.append("current public witness NAR row must be an object")
            continue
        burden = graph_burden_id(row.get("burden_id"))
        activation_ordinals = row.get("activation_ordinals")
        if not isinstance(activation_ordinals, list) or not all(type(item) is int for item in activation_ordinals):
            errors.append(f"current public witness {burden} activation_ordinals must be an integer list")
            continue
        partition.extend(activation_ordinals)
        for ordinal in activation_ordinals:
            if ordinal < 0 or ordinal >= len(public_activations):
                errors.append(f"current public witness {burden} activation ordinal is out of range")
            elif graph_burden_id(public_activations[ordinal].get("burden_id")) != burden:
                errors.append(f"current public witness {burden} activation ordinal names another burden")
    if sorted(partition) != list(range(len(public_activations))) or len(partition) != len(set(partition)):
        errors.append("current public witness activation ordinals must partition all activations exactly once")

    act_details = stage04.get("act_row_details")
    if not isinstance(act_details, list) or not all(isinstance(row, dict) for row in act_details):
        errors.append("Stage04 act_row_details must be an object list")
        act_details = []
    if len(act_details) != len(records) or len(act_details) != len(public_activations):
        errors.append("Stage04 act_row_details count must equal visible ACT and current activation counts")
    act_refs = [graph_submove_id(row.get("body_ref")) for row in act_details]
    if not all(act_refs) or len(act_refs) != len(set(act_refs)):
        errors.append("Stage04 body_ref values must be non-empty and unique")
    decoded_rows: list[dict[str, Any]] = []
    for index, detail in enumerate(act_details):
        if index >= len(records) or index >= len(public_activations):
            continue
        record = records[index]
        mirror = public_activations[index]
        record_targets = [
            graph_burden_id(item) for item in nla_decode.land_targets(record.land)
            if graph_burden_id(item)
        ]
        record_burden = record_targets[0] if len(record_targets) == 1 else ""
        checks = (
            ("body_ref", graph_submove_id(detail.get("body_ref")), graph_submove_id(record.body_ref)),
            ("burden_id", graph_burden_id(detail.get("burden_id")), record_burden),
            ("owner_id", str(detail.get("owner_id") or ""), str(record.owner)),
            ("operation", str(detail.get("operation") or ""), str(record.operation)),
            ("pressure", str(detail.get("pressure") or ""), str(record.pi)),
            ("delta", str(detail.get("delta") or ""), str(record.delta)),
            ("delta_result", str(detail.get("delta_result") or ""), str(record.delta_result)),
            ("land", str(detail.get("land") or ""), str(record.land)),
            ("act_row", str(detail.get("act_row") or ""), str(record.record)),
        )
        for key, actual, expected in checks:
            if actual != expected:
                errors.append(f"Stage04 act_row_details[{index}] {key} differs from visible ACT")
        for key, actual, expected in (
            ("body_ref", graph_submove_id(mirror.get("body_ref")), graph_submove_id(detail.get("body_ref"))),
            ("burden_id", graph_burden_id(mirror.get("burden_id")), graph_burden_id(detail.get("burden_id"))),
            ("owner_id", str(mirror.get("owner_id") or ""), str(detail.get("owner_id") or "")),
            ("operation", str(mirror.get("operation") or ""), str(detail.get("operation") or "")),
        ):
            if actual != expected:
                errors.append(f"current activation[{index}] {key} differs from Stage04")

    owner_details = stage06.get("owner_activation_details")
    if not isinstance(owner_details, list) or not all(isinstance(row, dict) for row in owner_details):
        errors.append("Stage06 owner_activation_details must be an object list")
        owner_details = []
    owner_refs = [graph_submove_id(row.get("body_ref")) for row in owner_details]
    if owner_refs != act_refs or len(owner_refs) != len(set(owner_refs)):
        errors.append("Stage06 owner_activation_details body_ref order must uniquely equal Stage04")
    for index, owner_detail in enumerate(owner_details):
        if index >= len(act_details):
            continue
        detail = act_details[index]
        for key, actual, expected in (
            ("burden_id", graph_burden_id(owner_detail.get("burden_id")), graph_burden_id(detail.get("burden_id"))),
            ("owner_id", str(owner_detail.get("owner_id") or ""), str(detail.get("owner_id") or "")),
            ("operation", str(owner_detail.get("operation") or ""), str(detail.get("operation") or "")),
            ("terminal_state", str(owner_detail.get("terminal_state") or ""), str(terminal_states.get(graph_burden_id(detail.get("burden_id"))) or "")),
        ):
            if actual != expected:
                errors.append(f"Stage06 owner_activation_details[{index}] {key} differs from current carriers")

    rich_nar = stage06.get("normalized_activation_record_details")
    if not isinstance(rich_nar, dict):
        errors.append("Stage06 normalized_activation_record_details rich carrier is required")
        rich_nar = {}
    rich_rows = rich_nar.get("per_burden")
    if (
        rich_nar.get("schema_version") == "daee-nar-v2"
        or not isinstance(rich_rows, list)
        or any(isinstance(row, dict) and ("activation_ordinals" in row or "cycle_id" in row) for row in (rich_rows or []))
    ):
        errors.append("mixed current-public NAR used as rich Stage06 carrier")
        rich_rows = []
    for key, expected in (
        ("n_frame", selected_n_frame),
        ("live_registers", live_registers),
        ("burden_floor", burden_floor),
    ):
        if rich_nar.get(key) != expected:
            errors.append(f"Stage06 normalized_activation_record_details {key} differs from Stage02")
    if len(rich_rows) != len(act_details):
        errors.append("Stage06 rich per_burden row count must equal Stage04 activation count")

    rereads = stage05.get("per_burden_reread")
    reread_by_burden: dict[str, dict[str, Any]] = {}
    if not isinstance(rereads, list):
        errors.append("Stage05 per_burden_reread must be a list")
        rereads = []
    for row in rereads:
        if not isinstance(row, dict):
            errors.append("Stage05 per_burden_reread row must be an object")
            continue
        burden = graph_burden_id(row.get("burden_id"))
        if not burden or burden in reread_by_burden:
            errors.append("Stage05 per_burden_reread burden identities must be unique")
            continue
        reread_by_burden[burden] = row
    if list(reread_by_burden) != b_total:
        errors.append("Stage05 per_burden_reread order must cover B_total")

    for index, row in enumerate(rich_rows):
        if not isinstance(row, dict):
            errors.append(f"Stage06 rich per_burden[{index}] must be an object")
            continue
        if index >= len(act_details):
            continue
        detail = act_details[index]
        burden = graph_burden_id(detail.get("burden_id"))
        expected_values = {
            "burden_id": burden,
            "owner_id": str(detail.get("owner_id") or ""),
            "operation": str(detail.get("operation") or ""),
            "delta_result": str(detail.get("delta_result") or ""),
            "mrp_route_result_type": str(reread_by_burden.get(burden, {}).get("route_result_type") or ""),
            "terminal_state": str(terminal_states.get(burden) or ""),
            "generation_depth": node_by_burden.get(burden, {}).get("generation_depth"),
        }
        for key, expected in expected_values.items():
            if row.get(key) != expected:
                errors.append(f"Stage06 rich per_burden[{index}] {key} differs from validated current carriers")
        decoded_rows.append(
            {
                **nla_decode.canonical_projection_row(row),
                "pressure": str(detail.get("pressure") or ""),
                "body_ref": graph_submove_id(detail.get("body_ref")),
            }
        )

    graph = coverage.get("dependency_graph")
    expected_edges = nla_decode.dependency_edges(graph) if isinstance(graph, dict) else []
    stage05_edges = _current_dependency_edges(stage05.get("dependency_graph_edges"))
    if stage05_edges is None or stage05_edges != expected_edges:
        errors.append("Stage05 dependency_graph_edges differ from current public witness")

    if errors:
        return None, errors

    diagnostic = _current_diagnostic_evidence(
        stage_map=stage_map,
        field_witness=field_witness,
        records=records,
        certificate=certificate,
    )
    projection: dict[str, Any] = {
        "schema": nla_decode.CANONICAL_IR_PROJECTION_SCHEMA,
        "n_frame": selected_n_frame,
        "live_registers": live_registers,
        "burden_floor": burden_floor,
        "per_burden": [nla_decode.canonical_projection_row(row) for row in rich_rows],
        "diagnostic_completeness": diagnostic,
    }
    projection["decoded_ir"] = {
        "schema": nla_decode.CANONICAL_IR_DECODE_SCHEMA,
        "source_evidence": [
            "visible_act",
            "field_witness.owner_activations",
            "normalized_activation_record",
            "canonical_ir_projection",
        ],
        "n_frame": selected_n_frame,
        "live_registers": live_registers,
        "burden_floor": burden_floor,
        "per_burden": decoded_rows,
        "diagnostic_completeness": diagnostic,
    }

    generated_map = {
        graph_burden_id(row.get("id")): row
        for row in nla_decode.field_witness_generated_burdens(field_witness)
        if graph_burden_id(row.get("id"))
    }
    full_rows: list[dict[str, Any]] = []
    for row in decoded_rows:
        burden = graph_burden_id(row.get("burden_id"))
        generated = generated_map.get(burden)
        full_rows.append(
            {
                **row,
                "graph_role": nla_decode.graph_role_for_burden(burden, graph),
                "generated_by": f"MRP({generated.get('source')})" if generated else None,
                "track": "restoration" if generated else "baseline",
            }
        )
    projection["full_ir_decode"] = {
        "schema": nla_decode.FULL_IR_DECODE_SCHEMA,
        "source_evidence": [
            "visible_act",
            "field_witness.owner_activations",
            "normalized_activation_record",
            "canonical_ir_projection",
            "canonical_ir_projection.decoded_ir",
            "field_witness.coverage_proof",
            "field_witness.coverage_proof.dependency_graph",
            *(["field_witness.generated_burdens"] if generated_map else []),
            *(["field_witness.formal_reread_states"] if nla_decode.formal_reread_states(field_witness) else []),
        ],
        "n_frame": selected_n_frame,
        "live_registers": live_registers,
        "burden_floor": burden_floor,
        "B_LA": b_la,
        "B_MRP": b_mrp,
        "B_total": b_total,
        "dependency_graph": graph,
        "terminal_states": terminal_states,
        "diagnostic_completeness": diagnostic,
        "per_burden": full_rows,
        "generated_burdens": nla_decode.field_witness_generated_burdens(field_witness),
        "formal_reread": formal_reread_object(field_witness),
        "source_basis": source_basis_object(field_witness),
    }
    projection["proof_mode"] = {
        "schema": nla_decode.FULL_IR_PROOF_MODE_SCHEMA,
        "mode": "checker-owned-sidecar",
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
    projection["current_adapter"] = {
        "schema": CURRENT_ADAPTER_SCHEMA,
        "public_witness_schema": CURRENT_PUBLIC_WITNESS_SCHEMA,
        "stage_carrier_sha256": copy.deepcopy(diagnostic["stage_carrier_sha256"]),
        "public_field_witness_sha256": diagnostic["public_field_witness_sha256"],
        "visible_act_sha256": diagnostic["visible_act_sha256"],
        "diagnostic_evidence_sha256": nla_decode.canonical_json_sha256(diagnostic),
        "historical_diagnostic_member_added": False,
    }
    return projection, []


def build_projection(field_witness: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    normalized = field_witness.get("normalized_activation_record")
    if not isinstance(normalized, dict):
        return None, ["field_witness.normalized_activation_record is required"]
    nar_rows = normalized.get("per_burden")
    if not isinstance(nar_rows, list) or not nar_rows:
        return None, ["field_witness.normalized_activation_record.per_burden is required"]

    diagnostic = nla_decode.diagnostic_completeness(field_witness)
    if not isinstance(diagnostic, dict):
        errors.append("field_witness.coverage_proof.diagnostic_completeness is required")
        diagnostic = {}

    mirrors = field_witness.get("owner_activations")
    if not isinstance(mirrors, list) or not mirrors:
        return None, ["field_witness.owner_activations is required"]
    mirror_dicts = [item for item in mirrors if isinstance(item, dict)]
    if len(mirror_dicts) != len(mirrors):
        errors.append("field_witness.owner_activations must contain only objects")

    per_burden: list[dict[str, Any]] = []
    decoded_rows: list[dict[str, Any]] = []
    used_mirrors: set[int] = set()
    for index, raw_row in enumerate(nar_rows):
        if not isinstance(raw_row, dict):
            errors.append(f"normalized_activation_record.per_burden[{index}]: row must be an object")
            continue
        row = nla_decode.canonical_projection_row(raw_row)
        per_burden.append(row)
        mirror = mirror_for_projection_row(row, mirror_dicts, used_mirrors, errors, index)
        if mirror is None:
            continue
        decoded_rows.append(
            {
                **row,
                "pressure": str(mirror.get("pressure") or ""),
                "body_ref": graph_submove_id(mirror.get("body_ref")),
            }
        )

    if len(decoded_rows) != len(per_burden):
        errors.append("decoded_ir.per_burden could not be derived for every projection row")

    projection: dict[str, Any] = {
        "schema": nla_decode.CANONICAL_IR_PROJECTION_SCHEMA,
        "n_frame": normalized.get("n_frame"),
        "live_registers": normalized.get("live_registers"),
        "burden_floor": normalized.get("burden_floor"),
        "per_burden": per_burden,
        "diagnostic_completeness": diagnostic,
    }

    hard_registers = field_witness.get("hard_registers")
    if isinstance(hard_registers, dict):
        projection["diagnostic_ir_schema_version"] = nla_decode.HARD_REGISTER_SCHEMA_VERSION
        projection["hard_registers"] = hard_registers
    register_composition = field_witness.get("register_composition")
    if isinstance(register_composition, dict):
        projection["register_composition"] = register_composition

    decoded_ir: dict[str, Any] = {
        "schema": nla_decode.CANONICAL_IR_DECODE_SCHEMA,
        "source_evidence": [
            "visible_act",
            "field_witness.owner_activations",
            "normalized_activation_record",
            "canonical_ir_projection",
        ],
        "n_frame": projection.get("n_frame"),
        "live_registers": projection.get("live_registers"),
        "burden_floor": projection.get("burden_floor"),
        "per_burden": decoded_rows,
        "diagnostic_completeness": diagnostic,
    }
    if "hard_registers" in projection:
        decoded_ir["hard_registers"] = projection["hard_registers"]
    if "register_composition" in projection:
        decoded_ir["register_composition"] = projection["register_composition"]
    projection["decoded_ir"] = decoded_ir

    coverage = nla_decode.coverage_proof(field_witness)
    dependency_graph = coverage.get("dependency_graph")
    if not isinstance(dependency_graph, dict):
        errors.append("field_witness.coverage_proof.dependency_graph is required")
        dependency_graph = {}

    b_la = set(nla_decode.burden_list(field_witness, "B_LA"))
    generated_map = nla_decode.generated_burden_map(field_witness)
    full_rows: list[dict[str, Any]] = []
    for index, row in enumerate(decoded_rows):
        burden_id = graph_burden_id(row.get("burden_id"))
        generated = generated_map.get(burden_id)
        if generated:
            generated_by = generated.get("generated_by")
            track = generated.get("track")
        elif burden_id in b_la:
            generated_by = None
            track = "baseline"
        else:
            errors.append(f"decoded_ir.per_burden[{index}]: burden is neither B_LA nor generated burden")
            generated_by = None
            track = "baseline"
        full_rows.append(
            {
                **row,
                "graph_role": nla_decode.graph_role_for_burden(burden_id, dependency_graph),
                "generated_by": generated_by,
                "track": track,
            }
        )

    source_evidence = [
        "visible_act",
        "field_witness.owner_activations",
        "normalized_activation_record",
        "canonical_ir_projection",
        "canonical_ir_projection.decoded_ir",
        "field_witness.coverage_proof",
        "field_witness.coverage_proof.dependency_graph",
    ]
    if nla_decode.field_witness_generated_burdens(field_witness):
        source_evidence.append("field_witness.generated_burdens")
    if nla_decode.formal_reread_states(field_witness):
        source_evidence.append("field_witness.formal_reread_states")
    if isinstance(field_witness.get("source_basis"), dict):
        source_evidence.append("field_witness.source_basis")

    full_ir_decode: dict[str, Any] = {
        "schema": nla_decode.FULL_IR_DECODE_SCHEMA,
        "source_evidence": source_evidence,
        "n_frame": projection.get("n_frame"),
        "live_registers": projection.get("live_registers"),
        "burden_floor": projection.get("burden_floor"),
        "B_LA": nla_decode.burden_list(field_witness, "B_LA"),
        "B_MRP": nla_decode.burden_list(field_witness, "B_MRP"),
        "B_total": nla_decode.burden_list(field_witness, "B_total"),
        "dependency_graph": dependency_graph,
        "terminal_states": coverage.get("terminal_states"),
        "diagnostic_completeness": diagnostic,
        "per_burden": full_rows,
        "generated_burdens": nla_decode.field_witness_generated_burdens(field_witness),
        "formal_reread": formal_reread_object(field_witness),
        "source_basis": source_basis_object(field_witness),
    }
    if "hard_registers" in projection:
        full_ir_decode["hard_registers"] = projection["hard_registers"]
    if "register_composition" in projection:
        full_ir_decode["register_composition"] = projection["register_composition"]
    projection["full_ir_decode"] = full_ir_decode

    projection["proof_mode"] = {
        "schema": nla_decode.FULL_IR_PROOF_MODE_SCHEMA,
        "mode": PROOF_MODE,
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

    return (None if errors else projection), errors


def validate_inputs(
    input_path: Path,
    output_path: Path,
    certificate_path: Path,
    grapher_html_path: Path | None,
) -> tuple[dict[str, Any] | None, list[Any] | None, dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    for label, path in (
        ("input", input_path),
        ("output", output_path),
        ("collapse_certificate", certificate_path),
    ):
        errors.extend(require_existing(path, label))
    if grapher_html_path is not None:
        errors.extend(require_existing(grapher_html_path, "grapher_html"))
    if errors:
        return None, None, None, errors

    output_text = read_text(output_path)
    field_witness, found = nla_decode.parse_field_witness(output_path, output_text)
    errors.extend(found)

    records, parse_errors = nla_decode.parse_act_records(nla_decode.public_execution_text(output_text))
    errors.extend(f"{rel(output_path)}: {message}" for message in parse_errors)
    if not records:
        errors.append(f"{rel(output_path)}: no visible ACT records available for sidecar projection")

    nla_errors = nla_decode.nla_decode_errors(output_path, output_text)
    if nla_errors:
        errors.append(f"{rel(output_path)}: schema-light NLA semantic faithfulness must pass before sidecar build")
        errors.extend(nla_errors)

    certificate, cert_load_errors = load_json(certificate_path)
    errors.extend(cert_load_errors)
    if isinstance(certificate, dict):
        errors.extend(f"{rel(certificate_path)}: {error}" for error in certificate_errors(certificate))
        expected_fingerprint = input_fingerprint_for_path(input_path)
        if certificate.get("input_fingerprint") != expected_fingerprint:
            errors.append(
                f"{rel(certificate_path)}: input_fingerprint does not match {rel(input_path)}"
            )
        for key in ("collapse_positive", "coverage_complete", "diagnostic_completeness"):
            if certificate.get(key) is not True:
                errors.append(f"{rel(certificate_path)}: {key} must be true")
    else:
        errors.append(f"{rel(certificate_path)}: collapse certificate must be a JSON object")

    if grapher_html_path is not None:
        grapher_text = read_text(grapher_html_path)
        if "Verdict: reconstructible" not in grapher_text:
            errors.append(f"{rel(grapher_html_path)}: missing reconstructible verdict")
        if "No warnings." not in grapher_text:
            errors.append(f"{rel(grapher_html_path)}: missing warning-clean marker")

    return field_witness, records, certificate if isinstance(certificate, dict) else None, errors


def build_sidecar(
    input_path: Path,
    output_path: Path,
    certificate_path: Path,
    grapher_html_path: Path | None,
    stage_carriers: Any = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    field_witness, records, certificate, errors = validate_inputs(
        input_path,
        output_path,
        certificate_path,
        grapher_html_path,
    )
    if errors:
        return None, errors
    assert field_witness is not None
    assert records is not None
    assert certificate is not None

    if field_witness.get("schema_version") == CURRENT_PUBLIC_WITNESS_SCHEMA:
        projection, found = build_current_projection(
            field_witness,
            records,
            stage_carriers,
            certificate,
        )
    elif stage_carriers is not None:
        projection, found = None, [
            "historical B.5 projection must not consume current Stage02/04/05/06 carriers"
        ]
    else:
        projection, found = build_projection(field_witness)
    errors.extend(found)
    if projection is None:
        return None, errors

    output_text = read_text(output_path)
    if field_witness.get("schema_version") == CURRENT_PUBLIC_WITNESS_SCHEMA:
        reprojected, projection_errors = build_current_projection(
            field_witness,
            records,
            stage_carriers,
            certificate,
        )
        if reprojected != projection:
            projection_errors.append("current adapter deterministic re-projection differs")
    else:
        projection_errors = nla_decode.canonical_ir_projection_object_errors(
            output_path,
            output_text,
            field_witness,
            records,
            projection,
        )
    if projection_errors:
        errors.append(f"{rel(output_path)}: generated sidecar projection failed semantic validation")
        errors.extend(projection_errors)
        return None, errors

    source = {
        "raw_input": rel(input_path),
        "governed_output": rel(output_path),
        "collapse_certificate": rel(certificate_path),
        "builder": BUILDER_PATH,
    }
    if grapher_html_path is not None:
        source["grapher_html"] = rel(grapher_html_path)

    return {
        "schema": SIDECAR_SCHEMA,
        "source": source,
        "projection": projection,
    }, []


def write_sidecar(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_self_test() -> int:
    case = ROOT / "tests" / "retained-proof-corpus" / "v0.4.3.0-schema-light" / "valid" / "sidecar-backed" / "cases" / "a9-science-source"
    with tempfile.TemporaryDirectory(prefix="b5-full-ir-sidecar-") as tmp:
        sidecar_path = Path(tmp) / "b5-full-ir-projection-sidecar.json"
        payload, errors = build_sidecar(
            case / "input.txt",
            case / "output.md",
            case / "collapse-certificate.json",
            case / "grapher.html",
        )
        if payload is None:
            print("B.5 full-IR sidecar builder self-test: FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        write_sidecar(sidecar_path, payload)
        reread, reread_errors = load_json(sidecar_path)
        if reread_errors or reread != payload:
            print("B.5 full-IR sidecar builder self-test: FAIL")
            for error in reread_errors:
                print(f"- {error}")
            if reread != payload:
                print("- generated sidecar did not round-trip")
            return 1
    print("B.5 full-IR sidecar builder self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--collapse-certificate", type=Path)
    parser.add_argument("--grapher-html", type=Path)
    parser.add_argument("--stage-carriers", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    missing = [
        name
        for name, value in (
            ("--input", args.input),
            ("--output", args.output),
            ("--collapse-certificate", args.collapse_certificate),
            ("--out", args.out),
        )
        if value is None
    ]
    if missing:
        parser.error("missing required argument(s): " + ", ".join(missing))

    assert args.input is not None
    assert args.output is not None
    assert args.collapse_certificate is not None
    assert args.out is not None
    stage_carriers: Any = None
    if args.stage_carriers is not None:
        stage_carriers, carrier_errors = load_json(args.stage_carriers)
        if carrier_errors:
            print("B.5 full-IR sidecar build: FAIL")
            for error in carrier_errors:
                print(f"- {error}")
            return 1
    payload, errors = build_sidecar(
        args.input,
        args.output,
        args.collapse_certificate,
        args.grapher_html,
        stage_carriers,
    )
    if payload is None:
        print("B.5 full-IR sidecar build: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    write_sidecar(args.out, payload)
    print("B.5 full-IR sidecar build: PASS")
    print(f"Sidecar: {rel(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
