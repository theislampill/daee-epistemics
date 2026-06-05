#!/usr/bin/env python3
"""Check bounded NLA decode / semantic faithfulness for ACT records.

This is not a universal semantic grader. It treats the checker-derived
CanonicalActivation as the encoded activation, dereferences body_ref, and
checks whether owner, operation, pressure, delta/result, and Land facets can be
recovered from the exact Layer B body and field_witness mirror. It also builds a
bounded reconstructed Layer B submove from the CanonicalActivation and verifies
that the reconstructed submove passes the same semantic-facet contract.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from closure_witness_lib import extract_embedded_field_witness, extract_field_witness
from check_mrp_generated_burden import (
    SUB,
    UNTRUSTED_ACTIVATION_SELF_CLAIMS,
    ActRecord,
    canonical_activation_from_record,
    contribution_body,
    contribution_names_land,
    field_body,
    field_body_any,
    graph_burden_id,
    graph_normalized_text,
    graph_submove_id,
    land_targets,
    parse_act_records,
    render_act,
    strict_owner_family,
    submove_block_index,
    submove_block_ref_owner,
    submove_operation_body,
    transition_values_agree,
    visible_keywords,
    GENERIC_ACT_VALUE_RE,
    STATE_CHANGE_RE,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "nla-decode-semantic-faithfulness"
FORMAL_CONTRACT_HEADING = "## Formal owner contract"
HARD_REGISTER_SCHEMA_VERSION = "0.4.3-hard-registers-v1"
CANONICAL_IR_PROJECTION_SCHEMA = "b5-canonical-ir-projection-v1"
CANONICAL_IR_DECODE_SCHEMA = "b5-canonical-ir-decode-v1"
FULL_IR_DECODE_SCHEMA = "b5-full-ir-decode-v1"
FULL_IR_PROOF_MODE_SCHEMA = "b5-full-ir-proof-mode-v1"
RUNTIME_EMISSION_POLICY_SCHEMA = "b5-full-ir-runtime-emission-v1"
REGISTER_COMPOSITION_SCHEMA = "b5-register-composition-v1"
REGISTER_COMPOSITION_SOURCE_CAPABILITY = "register-composition-owner-handoff-v1"
HARD_REGISTER_KEYS = ("heart", "xi", "Omega", "mu", "kappa")
HARD_REGISTER_KEY_SET = set(HARD_REGISTER_KEYS)
HARD_REGISTER_STATES = {"live", "held", "non_live"}
HARD_REGISTER_FUNCTIONS = {
    "heart": {"affective-posture", "security-posture", "moral-recoil", "restoration-recoil"},
    "xi": {"warrant-authority", "source-order", "proof-tribunal", "testimony-status"},
    "Omega": {"ontology-predication", "category-transfer", "referent-confusion", "creator-creation"},
    "mu": {"memetic-carrier", "compression-carrier", "defensive-stabilizer", "mutation-reproduction"},
    "kappa": {"dependency-collapse", "entailment-chain", "closure-boundary", "cycle-curl"},
}
PROJECTION_ROUTE_RESULT_TYPES = {
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "loopbreak",
}
PROJECTION_TERMINAL_STATES = {"landed", "hold_partial"}
PROJECTION_PER_BURDEN_KEYS = (
    "burden_id",
    "owner_id",
    "operation",
    "delta_result",
    "mrp_route_result_type",
    "terminal_state",
    "generation_depth",
)
REGISTER_COMPOSITION_KEYS = {
    "schema",
    "source_fixture",
    "source_fixture_capability",
    "component_registers",
    "sigma_boundary",
    "composition_rule",
    "owner_handoff",
    "automatic_dispatch_chain",
    "evidence",
}
REGISTER_COMPOSITION_SIGMA_KEYS = {"present", "inside_hard_registers", "role"}
REGISTER_COMPOSITION_OWNER_HANDOFF_KEYS = {"selected", "held", "policy"}
CANONICAL_IR_DECODE_KEYS = {
    "schema",
    "source_evidence",
    "n_frame",
    "live_registers",
    "burden_floor",
    "per_burden",
    "diagnostic_completeness",
}
CANONICAL_IR_DECODE_OPTIONAL_KEYS = {"hard_registers", "register_composition"}
CANONICAL_IR_DECODE_SOURCE_EVIDENCE = {
    "visible_act",
    "field_witness.owner_activations",
    "normalized_activation_record",
    "canonical_ir_projection",
}
CANONICAL_IR_DECODE_ROW_KEYS = {
    "burden_id",
    "owner_id",
    "operation",
    "pressure",
    "body_ref",
    "delta_result",
    "mrp_route_result_type",
    "terminal_state",
    "generation_depth",
}
FULL_IR_DECODE_KEYS = {
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
FULL_IR_DECODE_OPTIONAL_KEYS = {"hard_registers", "register_composition"}
FULL_IR_DECODE_REQUIRED_SOURCE_EVIDENCE = {
    "visible_act",
    "field_witness.owner_activations",
    "normalized_activation_record",
    "canonical_ir_projection",
    "canonical_ir_projection.decoded_ir",
    "field_witness.coverage_proof",
    "field_witness.coverage_proof.dependency_graph",
}
FULL_IR_DECODE_OPTIONAL_SOURCE_EVIDENCE = {
    "field_witness.generated_burdens",
    "field_witness.formal_reread_states",
    "field_witness.source_basis",
}
FULL_IR_DECODE_SOURCE_EVIDENCE = (
    FULL_IR_DECODE_REQUIRED_SOURCE_EVIDENCE | FULL_IR_DECODE_OPTIONAL_SOURCE_EVIDENCE
)
FULL_IR_DECODE_ROW_KEYS = CANONICAL_IR_DECODE_ROW_KEYS | {
    "graph_role",
    "generated_by",
    "track",
}
FULL_IR_GRAPH_ROLES = {"root", "dependent", "isolated"}
FULL_IR_TRACKS = {"baseline", "primary", "restoration"}
FULL_IR_FORMAL_REREAD_KEYS = {
    "states_present",
    "divergence_state",
    "curl_state",
    "escape_routes_checked",
    "no_new_resultant_proof",
}
FULL_IR_SOURCE_BASIS_KEYS = {
    "source_basis_available",
    "sigma_inside_hard_registers",
    "basis",
}
FULL_IR_PROOF_MODE_KEYS = {
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
FULL_IR_PROOF_MODE_MODES = {
    "selected-surface",
    "checker-owned-sidecar",
    "retained-proof-corpus-sidecar",
}
FULL_IR_PROOF_MODE_SOURCE_EVIDENCE = {
    "visible_noetic_field_opening",
    "visible_layer_a_diagnostic_ir_header",
    "field_witness.canonical_ir_projection",
    "field_witness.canonical_ir_projection.decoded_ir",
    "field_witness.canonical_ir_projection.full_ir_decode",
}
RUNTIME_EMISSION_POLICY_KEYS = {
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


def owner_contract_key(value: str) -> str:
    return re.sub(r"[\s_]+", "-", value.strip().strip("[]")).upper()


def formal_owner_contract_operations() -> dict[str, set[str]]:
    operations: dict[str, set[str]] = {}
    catalogue = ROOT / "atomics/skill/references/diagnostics/module-catalogue.json"
    if not catalogue.is_file():
        return operations
    try:
        payload = json.loads(catalogue.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return operations
    for entry in payload.get("modules") or []:
        if not isinstance(entry, dict):
            continue
        path_value = str(entry.get("path") or "")
        if not path_value.startswith("skill/"):
            continue
        source = ROOT / "atomics/skill" / path_value[len("skill/") :]
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        start = text.find(FORMAL_CONTRACT_HEADING)
        if start == -1:
            continue
        section = text[start:]
        next_heading = re.search(r"(?m)^##\s+", section[len(FORMAL_CONTRACT_HEADING) :])
        if next_heading:
            section = section[: len(FORMAL_CONTRACT_HEADING) + next_heading.start()]
        match = re.search(r"```json\s*(\{.*?\})\s*```", section, re.S)
        if not match:
            continue
        try:
            contract = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if not isinstance(contract, dict):
            continue
        raw_ops = contract.get("operation_token")
        if isinstance(raw_ops, str):
            op_set = {raw_ops.strip()} if raw_ops.strip() else set()
        elif isinstance(raw_ops, list):
            op_set = {str(item).strip() for item in raw_ops if str(item).strip()}
        else:
            op_set = set()
        if not op_set:
            continue
        for key in (contract.get("owner_id"), contract.get("owner_family"), entry.get("id")):
            token = str(key or "").strip()
            if token:
                operations[owner_contract_key(token)] = op_set
    return operations


FORMAL_OWNER_CONTRACT_OPERATIONS = formal_owner_contract_operations()
RUNTIME_EMISSION_POLICY_MODES = {
    "default-runtime-when-proof-class-closure-claimed",
}
RUNTIME_EMISSION_POLICY_SOURCE_EVIDENCE = {
    "visible_noetic_field_opening",
    "visible_layer_a_diagnostic_ir_header",
    "field_witness.canonical_ir_projection",
    "field_witness.canonical_ir_projection.proof_mode",
    "field_witness.canonical_ir_projection.decoded_ir",
    "field_witness.canonical_ir_projection.full_ir_decode",
}


@dataclass(frozen=True)
class DecodedFacets:
    body_ref: str
    owner_family: str
    operation: str
    pressure: str
    delta_result: str
    land_target: str
    body_target: str
    body_owner_family: str
    body_operation: str
    body_result: str
    body_contribution: str
    body_prose: str


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def expand_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        raw = str(path)
        if any(char in raw for char in "*?["):
            matches = sorted(Path(match) for match in glob.glob(raw))
            expanded.extend(matches or [path])
        else:
            expanded.append(path)
    return expanded


def public_execution_text(text: str) -> str:
    match = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:Restorative Response|Closing Formulation|"
        r"Closure/Reconstruction Witness|Held-node Accounting|field_witness)\b",
        text,
    )
    return text[: match.start()] if match else text


def parse_field_witness(path: Path, text: str) -> tuple[dict[str, Any] | None, list[str]]:
    payload = extract_embedded_field_witness(text)
    if payload is None:
        return None, [f"{rel(path)}: field_witness parser-stable JSON payload missing"]
    field_witness = extract_field_witness(payload)
    if field_witness is None:
        return None, [f"{rel(path)}: field_witness object missing"]
    return field_witness, []


def projection_opening_surface_errors(path: Path, text: str, field_witness: dict[str, Any]) -> list[str]:
    projection = field_witness.get("canonical_ir_projection")
    if not isinstance(projection, dict):
        return []

    errors: list[str] = []
    label = f"{rel(path)}: field_witness.canonical_ir_projection"
    lines = text.splitlines()
    first_nonblank = next((line.strip() for line in lines if line.strip()), "")
    head = "\n".join(lines[:10])
    layer_a = re.search(r"(?im)^\s*(?:#{1,6}\s*)?Layer A\b.*(?:Compact DSL|DSL/IR|Diagnostic)", text)
    field_heading = re.search(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\b", text)

    if "NOETIC FIELD EXECUTION" not in head:
        errors.append(f"{label}: opt-in projection requires visible noetic-field opening banner")
    if layer_a is None:
        errors.append(f"{label}: opt-in projection requires visible Layer A / Diagnostic IR opening header")
    elif field_heading is not None and field_heading.start() < layer_a.start():
        errors.append(f"{label}: machine projection appears before visible Layer A opening header")
    if first_nonblank in {"field_witness", "{", "```json"} or first_nonblank.startswith("{"):
        errors.append(f"{label}: machine projection must not replace the human-facing opening field read")
    return errors


def target_token_from_submove_ref(ref: str) -> str:
    text = str(ref or "").strip()
    match = re.fullmatch(r"(B\d+)(?:[_\.]\d+)", text)
    if match:
        return match.group(1)
    match = re.fullmatch(rf"(?P<target>.+?)(?:[{SUB}]+|[_\.]\d+)", text)
    return match.group("target") if match else ""


def normalized_words(value: str) -> set[str]:
    normalized = re.sub(r"[-_/]", " ", graph_normalized_text(value).lower())
    return set(re.findall(r"[a-z0-9][a-z0-9']{3,}", normalized))


def keywords_recoverable(label: str, body: str, *, minimum: int = 2) -> bool:
    keywords = visible_keywords(label)
    if not keywords:
        return False
    words = normalized_words(body)
    hits = sum(1 for keyword in keywords if keyword in words)
    return hits >= min(len(keywords), minimum)


def operation_recoverable(operation: str, body_operation: str, body_prose: str) -> bool:
    if GENERIC_ACT_VALUE_RE.fullmatch(operation):
        return False
    operation_norm = graph_normalized_text(operation).lower()
    scope = f"{body_operation}\n{body_prose}"
    if operation_norm and operation_norm in graph_normalized_text(scope).lower():
        return True
    return keywords_recoverable(operation, scope, minimum=2)


def field_witness_activation_by_body_ref(field_witness: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw = field_witness.get("owner_activations")
    if not isinstance(raw, list):
        return {}
    result: dict[str, list[dict[str, Any]]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        body_ref = graph_submove_id(item.get("body_ref"))
        if body_ref:
            result.setdefault(body_ref, []).append(item)
    return result


def visible_activation_triplets(records: list[ActRecord]) -> set[tuple[str, str, str]]:
    triplets: set[tuple[str, str, str]] = set()
    for record in records:
        land_target_tokens = [graph_burden_id(item) for item in land_targets(record.land)]
        target = land_target_tokens[0] if land_target_tokens else ""
        owner = strict_owner_family(record.owner)
        if target and owner and record.operation:
            triplets.add((target, owner, record.operation))
    return triplets


def activation_surface_coverage_errors(
    path: Path,
    field_witness: dict[str, Any],
    records: list[ActRecord],
) -> list[str]:
    """Reject proof mirrors for owners not backed by visible ACT rows."""

    label = rel(path)
    errors: list[str] = []
    visible_body_refs = {graph_submove_id(record.body_ref) for record in records}
    for index, item in enumerate(field_witness.get("owner_activations") or [], start=1):
        if not isinstance(item, dict):
            continue
        body_ref = graph_submove_id(item.get("body_ref"))
        if body_ref and body_ref not in visible_body_refs:
            errors.append(
                f"{label}: field_witness.owner_activations[{index}] body_ref {body_ref} has no visible ACT row"
            )

    normalized = field_witness.get("normalized_activation_record")
    if not isinstance(normalized, dict):
        return errors
    raw_rows = normalized.get("per_burden")
    if not isinstance(raw_rows, list):
        return errors
    visible_triplets = visible_activation_triplets(records)
    for index, row in enumerate(raw_rows, start=1):
        if not isinstance(row, dict):
            continue
        burden = graph_burden_id(row.get("burden_id"))
        owner = strict_owner_family(str(row.get("owner_id") or ""))
        operation = str(row.get("operation") or "").strip()
        if burden and owner and operation and (burden, owner, operation) not in visible_triplets:
            errors.append(
                f"{label}: normalized_activation_record.per_burden[{index}] "
                f"{burden}/{owner}/{operation} has no visible ACT row"
            )
    return errors


def string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return None
    return value


def key_shape_errors(
    value: Any,
    required: set[str],
    optional: set[str],
    label: str,
) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: must be an object"]
    keys = set(value)
    missing = sorted(required - keys)
    extra = sorted(keys - (required | optional))
    errors: list[str] = []
    if missing:
        errors.append(f"{label}: missing required key(s): {missing}")
    if extra:
        errors.append(f"{label}: additional key(s) not allowed: {extra}")
    return errors


def diagnostic_completeness(field_witness: dict[str, Any]) -> dict[str, Any] | None:
    coverage = field_witness.get("coverage_proof")
    if not isinstance(coverage, dict):
        return None
    diagnostic = coverage.get("diagnostic_completeness")
    return diagnostic if isinstance(diagnostic, dict) else None


def burden_list(field_witness: dict[str, Any], key: str) -> list[str]:
    value = field_witness.get(key)
    if isinstance(value, list) and all(isinstance(item, str) and graph_burden_id(item) for item in value):
        return [graph_burden_id(item) for item in value]
    return []


def coverage_proof(field_witness: dict[str, Any]) -> dict[str, Any]:
    value = field_witness.get("coverage_proof")
    return value if isinstance(value, dict) else {}


def dependency_edges(graph: dict[str, Any]) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    raw_edges = graph.get("edges")
    if not isinstance(raw_edges, list):
        return edges
    for raw in raw_edges:
        if isinstance(raw, dict):
            source = graph_burden_id(raw.get("from"))
            target = graph_burden_id(raw.get("to"))
        elif isinstance(raw, list) and len(raw) == 2:
            source = graph_burden_id(raw[0])
            target = graph_burden_id(raw[1])
        else:
            continue
        if source and target:
            edges.append((source, target))
    return edges


def graph_role_for_burden(burden_id: str, dependency_graph: dict[str, Any]) -> str:
    roots = {graph_burden_id(item) for item in dependency_graph.get("roots", []) if graph_burden_id(item)}
    incoming = {target for _, target in dependency_edges(dependency_graph)}
    outgoing = {source for source, _ in dependency_edges(dependency_graph)}
    if burden_id in roots:
        return "root"
    if burden_id in incoming:
        return "dependent"
    if burden_id in outgoing:
        return "root"
    return "isolated"


def field_witness_generated_burdens(field_witness: dict[str, Any]) -> list[dict[str, Any]]:
    generated = field_witness.get("generated_burdens")
    if not isinstance(generated, list):
        return []
    return [item for item in generated if isinstance(item, dict)]


def generated_burden_map(field_witness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in field_witness_generated_burdens(field_witness):
        burden_id = graph_burden_id(item.get("id"))
        if burden_id:
            result[burden_id] = item
    return result


def formal_reread_states(field_witness: dict[str, Any]) -> list[dict[str, Any]]:
    states = field_witness.get("formal_reread_states")
    if not isinstance(states, list):
        return []
    return [item for item in states if isinstance(item, dict)]


def flattened_escape_routes(states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for state in states:
        checked = state.get("escape_routes_checked")
        if isinstance(checked, list):
            routes.extend(item for item in checked if isinstance(item, dict))
    return routes


def terminal_no_new_resultant_proof(states: list[dict[str, Any]]) -> Any:
    for state in reversed(states):
        if "no_new_resultant_proof" in state:
            return state.get("no_new_resultant_proof")
    return None


def canonical_hard_register_live_registers(registers: dict[str, Any]) -> list[str]:
    live: list[str] = []
    for key in HARD_REGISTER_KEYS:
        value = registers.get(key)
        if isinstance(value, dict) and value.get("state") in {"live", "held"}:
            live.append(key)
    return live


def canonical_projection_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row.get(key) for key in PROJECTION_PER_BURDEN_KEYS}


def projection_row_set(records: list[ActRecord]) -> set[tuple[str, str, str, str]]:
    rows: set[tuple[str, str, str, str]] = set()
    for record in records:
        land_target_tokens = [graph_burden_id(item) for item in land_targets(record.land)]
        target = land_target_tokens[0] if land_target_tokens else ""
        rows.add((target, strict_owner_family(record.owner), record.operation, record.delta_result))
    return rows


def act_record_by_body_ref(records: list[ActRecord]) -> dict[str, ActRecord]:
    return {graph_submove_id(record.body_ref): record for record in records}


def canonical_ir_projection_common_errors(
    path: Path,
    field_witness: dict[str, Any],
    projection: dict[str, Any],
    records: list[ActRecord],
) -> list[str]:
    label = f"{rel(path)}: field_witness.canonical_ir_projection"
    errors: list[str] = []
    if projection.get("schema") != CANONICAL_IR_PROJECTION_SCHEMA:
        errors.append(f"{label}: schema must be {CANONICAL_IR_PROJECTION_SCHEMA!r}")

    normalized = field_witness.get("normalized_activation_record")
    if not isinstance(normalized, dict):
        return errors + [f"{label}: normalized_activation_record mirror is required"]

    for key in ("n_frame", "live_registers", "burden_floor"):
        if projection.get(key) != normalized.get(key):
            errors.append(f"{label}: {key} does not match normalized_activation_record")

    projection_diag = projection.get("diagnostic_completeness")
    witness_diag = diagnostic_completeness(field_witness)
    if not isinstance(projection_diag, dict):
        errors.append(f"{label}: diagnostic_completeness object is required")
    elif witness_diag is None:
        errors.append(f"{label}: field_witness.coverage_proof.diagnostic_completeness is required")
    elif projection_diag != witness_diag:
        errors.append(f"{label}: diagnostic_completeness does not match field_witness coverage_proof")

    live_registers = string_list(projection.get("live_registers"))
    if live_registers is None:
        errors.append(f"{label}: live_registers must be a string list")
    burden_floor = string_list(projection.get("burden_floor"))
    if burden_floor is None:
        errors.append(f"{label}: burden_floor must be a string list")
    n_frame = projection.get("n_frame")
    if not isinstance(n_frame, str) or not n_frame.strip():
        errors.append(f"{label}: n_frame must be a non-empty string")

    nar_rows = normalized.get("per_burden")
    projection_rows = projection.get("per_burden")
    if not isinstance(nar_rows, list) or not isinstance(projection_rows, list):
        errors.append(f"{label}: per_burden must mirror normalized_activation_record.per_burden")
        return errors
    if len(projection_rows) != len(nar_rows):
        errors.append(f"{label}: per_burden row count does not match normalized_activation_record")

    record_rows = projection_row_set(records)
    for index, row in enumerate(projection_rows):
        row_label = f"{label}.per_burden[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{row_label}: row must be an object")
            continue
        missing = [key for key in PROJECTION_PER_BURDEN_KEYS if key not in row]
        if missing:
            errors.append(f"{row_label}: missing required key(s): {missing}")
        if index < len(nar_rows):
            nar_row = nar_rows[index]
            if not isinstance(nar_row, dict):
                errors.append(f"{row_label}: normalized_activation_record row is not an object")
            elif canonical_projection_row(row) != canonical_projection_row(nar_row):
                errors.append(f"{row_label}: row does not match normalized_activation_record")
        owner_family = strict_owner_family(str(row.get("owner_id") or ""))
        if not owner_family:
            errors.append(f"{row_label}: owner_id is not catalogue-backed")
        route_type = row.get("mrp_route_result_type")
        if route_type not in PROJECTION_ROUTE_RESULT_TYPES:
            errors.append(f"{row_label}: mrp_route_result_type is not controlled")
        terminal = row.get("terminal_state")
        if terminal not in PROJECTION_TERMINAL_STATES:
            errors.append(f"{row_label}: terminal_state is not controlled")
        generation_depth = row.get("generation_depth")
        if type(generation_depth) is not int or generation_depth < 0:
            errors.append(f"{row_label}: generation_depth must be a non-negative integer")
        record_key = (
            graph_burden_id(row.get("burden_id")),
            owner_family,
            str(row.get("operation") or ""),
            str(row.get("delta_result") or ""),
        )
        if record_key not in record_rows:
            errors.append(f"{row_label}: no visible ACT row decodes to this projection row")
    return errors


def hard_register_projection_errors(
    path: Path,
    field_witness: dict[str, Any],
    projection: dict[str, Any],
) -> list[str]:
    label = f"{rel(path)}: field_witness.canonical_ir_projection"
    errors: list[str] = []
    version = projection.get("diagnostic_ir_schema_version")
    if version is None:
        if "hard_registers" in projection:
            errors.append(f"{label}: hard_registers requires {HARD_REGISTER_SCHEMA_VERSION}")
        return errors
    if version != HARD_REGISTER_SCHEMA_VERSION:
        return [f"{label}: diagnostic_ir_schema_version invalid: {version!r}"]

    registers = projection.get("hard_registers")
    if not isinstance(registers, dict):
        return [f"{label}: hard-register projection requires hard_registers object"]
    register_keys = set(registers)
    missing = sorted(HARD_REGISTER_KEY_SET - register_keys)
    extra = sorted(register_keys - HARD_REGISTER_KEY_SET)
    if missing:
        errors.append(f"{label}: hard_registers missing register key(s): {missing}")
    if extra:
        errors.append(f"{label}: hard_registers has unknown register key(s): {extra}")

    for key in HARD_REGISTER_KEYS:
        item = registers.get(key)
        if not isinstance(item, dict):
            errors.append(f"{label}.hard_registers.{key}: must be object")
            continue
        state = item.get("state")
        functions = item.get("functions")
        basis = item.get("basis")
        if state not in HARD_REGISTER_STATES:
            errors.append(f"{label}.hard_registers.{key}: state invalid")
        if not isinstance(functions, list) or not all(isinstance(value, str) and value for value in functions):
            errors.append(f"{label}.hard_registers.{key}: functions must be strings")
            functions = []
        if not isinstance(basis, list) or not all(isinstance(value, str) and value for value in basis):
            errors.append(f"{label}.hard_registers.{key}: basis must be strings")
            basis = []
        if state in {"live", "held"}:
            if not functions:
                errors.append(f"{label}.hard_registers.{key}: functions required for live/held")
            if not basis:
                errors.append(f"{label}.hard_registers.{key}: basis required for live/held")
            invalid_functions = sorted(set(functions) - HARD_REGISTER_FUNCTIONS[key])
            if invalid_functions:
                errors.append(f"{label}.hard_registers.{key}: invalid function(s): {invalid_functions}")
        elif state == "non_live":
            if functions or basis:
                errors.append(f"{label}.hard_registers.{key}: non_live must have empty functions and basis")
            if not isinstance(item.get("non_live_reason"), str) or not item["non_live_reason"].strip():
                errors.append(f"{label}.hard_registers.{key}: non_live_reason required")

    expected_live = canonical_hard_register_live_registers(registers)
    if projection.get("live_registers") != expected_live:
        errors.append(
            f"{label}: hard-register live set mismatch: "
            f"hard_registers={expected_live!r} live_registers={projection.get('live_registers')!r}"
        )

    normalized = field_witness.get("normalized_activation_record")
    if isinstance(normalized, dict) and normalized.get("live_registers") != expected_live:
        errors.append(
            f"{label}: hard-register live set mismatch: "
            f"hard_registers={expected_live!r} normalized_activation_record.live_registers="
            f"{normalized.get('live_registers')!r}"
        )

    register_deltas = field_witness.get("register_deltas")
    if not isinstance(register_deltas, list):
        errors.append(f"{label}: field_witness.register_deltas required for hard-register projection")
    else:
        seen_hard = {
            item.get("register")
            for item in register_deltas
            if isinstance(item, dict) and item.get("register") in HARD_REGISTER_KEY_SET
        }
        missing_live = [register for register in expected_live if register not in seen_hard]
        extra_live = sorted(seen_hard - set(expected_live))
        for register in missing_live:
            errors.append(f"{label}: field_witness.register_deltas missing live register {register}")
        if extra_live:
            errors.append(f"{label}: field_witness.register_deltas contains non-live hard register(s): {extra_live}")

    witness_diag = diagnostic_completeness(field_witness)
    if not isinstance(witness_diag, dict):
        errors.append(f"{label}: field_witness.coverage_proof.diagnostic_completeness required")
    else:
        if witness_diag.get("live_registers") != expected_live:
            errors.append(
                f"{label}: diagnostic_completeness.live_registers mismatch: "
                f"hard_registers={expected_live!r} diagnostic_completeness.live_registers="
                f"{witness_diag.get('live_registers')!r}"
            )
        coverage = witness_diag.get("coverage")
        if not isinstance(coverage, dict):
            errors.append(f"{label}: diagnostic_completeness.coverage must be object")
        else:
            extra_coverage = sorted(set(coverage) - set(expected_live))
            if extra_coverage:
                errors.append(
                    f"{label}: diagnostic_completeness.coverage contains non-live register(s): {extra_coverage}"
                )
            for register in expected_live:
                burdens = coverage.get(register)
                if not isinstance(burdens, list) or not burdens:
                    errors.append(f"{label}: diagnostic_completeness omits live register {register} coverage")
        if witness_diag.get("complete") is not True:
            errors.append(f"{label}: diagnostic_completeness.complete must be true")
    return errors


def register_composition_projection_errors(path: Path, projection: dict[str, Any]) -> list[str]:
    composition = projection.get("register_composition")
    if composition is None:
        return []

    label = f"{rel(path)}: field_witness.canonical_ir_projection.register_composition"
    errors: list[str] = []
    if not isinstance(composition, dict):
        return [f"{label}: must be an object"]

    keys = set(composition)
    missing = sorted(REGISTER_COMPOSITION_KEYS - keys)
    extra = sorted(keys - REGISTER_COMPOSITION_KEYS)
    if missing:
        errors.append(f"{label}: missing required key(s): {missing}")
    if extra:
        errors.append(f"{label}: additional key(s) not allowed: {extra}")

    if composition.get("schema") != REGISTER_COMPOSITION_SCHEMA:
        errors.append(f"{label}: schema must be {REGISTER_COMPOSITION_SCHEMA!r}")

    source_fixture = composition.get("source_fixture")
    if not isinstance(source_fixture, str) or not source_fixture.strip():
        errors.append(f"{label}: source_fixture must be a non-empty relative custody path")
    else:
        source_path = ROOT / source_fixture
        try:
            source_path.resolve().relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{label}: source_fixture must resolve inside the repo")
        if not source_path.is_file():
            errors.append(f"{label}: source_fixture path does not exist")

    capability = composition.get("source_fixture_capability")
    if capability != REGISTER_COMPOSITION_SOURCE_CAPABILITY:
        errors.append(
            f"{label}: source_fixture_capability must be {REGISTER_COMPOSITION_SOURCE_CAPABILITY!r}"
        )

    component_registers = string_list(composition.get("component_registers"))
    if component_registers is None:
        errors.append(f"{label}: component_registers must be a string list")
        component_registers = []
    else:
        component_set = set(component_registers)
        missing_hard = sorted(HARD_REGISTER_KEY_SET - component_set)
        unknown = sorted(component_set - HARD_REGISTER_KEY_SET)
        if missing_hard:
            errors.append(f"{label}: component_registers missing hard register(s): {missing_hard}")
        if unknown:
            errors.append(f"{label}: component_registers contains non-hard register(s): {unknown}")

    projection_live = string_list(projection.get("live_registers")) or []
    if component_registers and projection_live and component_registers != projection_live:
        errors.append(f"{label}: component_registers must match projection live_registers")

    sigma_boundary = composition.get("sigma_boundary")
    if not isinstance(sigma_boundary, dict):
        errors.append(f"{label}: sigma_boundary must be an object")
    else:
        sigma_keys = set(sigma_boundary)
        missing_sigma = sorted(REGISTER_COMPOSITION_SIGMA_KEYS - sigma_keys)
        extra_sigma = sorted(sigma_keys - REGISTER_COMPOSITION_SIGMA_KEYS)
        if missing_sigma:
            errors.append(f"{label}.sigma_boundary: missing required key(s): {missing_sigma}")
        if extra_sigma:
            errors.append(f"{label}.sigma_boundary: additional key(s) not allowed: {extra_sigma}")
        if sigma_boundary.get("present") is not True:
            errors.append(f"{label}.sigma_boundary: present must be true for register-composition handoff")
        if sigma_boundary.get("inside_hard_registers") is not False:
            errors.append(f"{label}.sigma_boundary: sigma must remain outside hard_registers")
        role = sigma_boundary.get("role")
        if not isinstance(role, str) or "outside" not in role.lower():
            errors.append(f"{label}.sigma_boundary: role must name sigma as outside the hard-register object")

    composition_rule = composition.get("composition_rule")
    if not isinstance(composition_rule, str) or not composition_rule.strip():
        errors.append(f"{label}: composition_rule must be a non-empty string")
    else:
        rule = composition_rule.lower()
        for term in ("composition", "not automatic", "owner"):
            if term not in rule:
                errors.append(f"{label}: composition_rule must include {term!r}")

    owner_handoff = composition.get("owner_handoff")
    if not isinstance(owner_handoff, dict):
        errors.append(f"{label}: owner_handoff must be an object")
    else:
        handoff_keys = set(owner_handoff)
        missing_handoff = sorted(REGISTER_COMPOSITION_OWNER_HANDOFF_KEYS - handoff_keys)
        extra_handoff = sorted(handoff_keys - REGISTER_COMPOSITION_OWNER_HANDOFF_KEYS)
        if missing_handoff:
            errors.append(f"{label}.owner_handoff: missing required key(s): {missing_handoff}")
        if extra_handoff:
            errors.append(f"{label}.owner_handoff: additional key(s) not allowed: {extra_handoff}")
        selected = string_list(owner_handoff.get("selected"))
        held = string_list(owner_handoff.get("held"))
        if not selected:
            errors.append(f"{label}.owner_handoff.selected must be a non-empty string list")
            selected = []
        if held is None:
            errors.append(f"{label}.owner_handoff.held must be a string list")
            held = []
        projection_owners = {
            strict_owner_family(str(row.get("owner_id") or ""))
            for row in projection.get("per_burden", [])
            if isinstance(row, dict)
        }
        selected_families = {strict_owner_family(owner) for owner in selected}
        missing_selected = sorted(owner for owner in selected_families if owner and owner not in projection_owners)
        if missing_selected:
            errors.append(f"{label}.owner_handoff.selected not backed by projection rows: {missing_selected}")
        policy = owner_handoff.get("policy")
        if not isinstance(policy, str) or not policy.strip():
            errors.append(f"{label}.owner_handoff.policy must be a non-empty string")
        else:
            policy_text = policy.lower()
            for term in ("owner eligibility", "not automatic", "dispatch"):
                if term not in policy_text:
                    errors.append(f"{label}.owner_handoff.policy must include {term!r}")

    if composition.get("automatic_dispatch_chain") is not False:
        errors.append(f"{label}: automatic_dispatch_chain must be false")

    evidence = string_list(composition.get("evidence"))
    if not evidence:
        errors.append(f"{label}: evidence must be a non-empty string list")
        evidence = []
    evidence_text = " ".join(evidence).lower()
    for term in (REGISTER_COMPOSITION_SOURCE_CAPABILITY, "r(h,delta)", "owner eligibility"):
        if term not in evidence_text:
            errors.append(f"{label}: evidence must include {term!r}")

    return errors


def canonical_ir_decode_errors(
    path: Path,
    field_witness: dict[str, Any],
    projection: dict[str, Any],
    records: list[ActRecord],
) -> list[str]:
    decoded = projection.get("decoded_ir")
    if decoded is None:
        return []

    label = f"{rel(path)}: field_witness.canonical_ir_projection.decoded_ir"
    errors = key_shape_errors(
        decoded,
        CANONICAL_IR_DECODE_KEYS,
        CANONICAL_IR_DECODE_OPTIONAL_KEYS,
        label,
    )
    if errors:
        return errors

    if decoded.get("schema") != CANONICAL_IR_DECODE_SCHEMA:
        errors.append(f"{label}: schema must be {CANONICAL_IR_DECODE_SCHEMA!r}")

    source_evidence = string_list(decoded.get("source_evidence"))
    if source_evidence is None:
        errors.append(f"{label}: source_evidence must be a string list")
    else:
        missing_sources = sorted(CANONICAL_IR_DECODE_SOURCE_EVIDENCE - set(source_evidence))
        extra_sources = sorted(set(source_evidence) - CANONICAL_IR_DECODE_SOURCE_EVIDENCE)
        if missing_sources:
            errors.append(f"{label}: source_evidence missing required source(s): {missing_sources}")
        if extra_sources:
            errors.append(f"{label}: source_evidence has unknown source(s): {extra_sources}")

    for key in ("n_frame", "live_registers", "burden_floor", "diagnostic_completeness"):
        if decoded.get(key) != projection.get(key):
            errors.append(f"{label}: {key} does not match canonical_ir_projection")

    projection_has_hard_registers = "hard_registers" in projection
    decoded_has_hard_registers = "hard_registers" in decoded
    if projection_has_hard_registers and not decoded_has_hard_registers:
        errors.append(f"{label}: hard_registers required when projection has hard_registers")
    elif decoded_has_hard_registers and decoded.get("hard_registers") != projection.get("hard_registers"):
        errors.append(f"{label}: hard_registers does not match canonical_ir_projection")

    projection_composition = projection.get("register_composition")
    decoded_composition = decoded.get("register_composition")
    if projection_composition is not None and decoded_composition != projection_composition:
        errors.append(f"{label}: register_composition does not match canonical_ir_projection")
    elif projection_composition is None and decoded_composition is not None:
        errors.append(f"{label}: register_composition requires canonical_ir_projection.register_composition")

    projection_rows = projection.get("per_burden")
    decoded_rows = decoded.get("per_burden")
    normalized = field_witness.get("normalized_activation_record")
    nar_rows = normalized.get("per_burden") if isinstance(normalized, dict) else None
    if not isinstance(projection_rows, list) or not isinstance(decoded_rows, list):
        errors.append(f"{label}: per_burden must mirror canonical_ir_projection.per_burden")
        return errors
    if len(decoded_rows) != len(projection_rows):
        errors.append(f"{label}: per_burden row count does not match canonical_ir_projection")
    if isinstance(nar_rows, list) and len(decoded_rows) != len(nar_rows):
        errors.append(f"{label}: per_burden row count does not match normalized_activation_record")

    record_by_ref = act_record_by_body_ref(records)
    mirrors = field_witness_activation_by_body_ref(field_witness)
    for index, row in enumerate(decoded_rows):
        row_label = f"{label}.per_burden[{index}]"
        row_errors = key_shape_errors(row, CANONICAL_IR_DECODE_ROW_KEYS, set(), row_label)
        errors.extend(row_errors)
        if row_errors:
            continue

        core = canonical_projection_row(row)
        if index < len(projection_rows):
            projection_row = projection_rows[index]
            if not isinstance(projection_row, dict):
                errors.append(f"{row_label}: canonical_ir_projection row is not an object")
            elif core != canonical_projection_row(projection_row):
                errors.append(f"{row_label}: core row does not match canonical_ir_projection")
        if isinstance(nar_rows, list) and index < len(nar_rows):
            nar_row = nar_rows[index]
            if not isinstance(nar_row, dict):
                errors.append(f"{row_label}: normalized_activation_record row is not an object")
            elif core != canonical_projection_row(nar_row):
                errors.append(f"{row_label}: core row does not match normalized_activation_record")

        pressure = row.get("pressure")
        body_ref = graph_submove_id(row.get("body_ref"))
        if not isinstance(pressure, str) or not pressure.strip():
            errors.append(f"{row_label}: pressure must be a non-empty string")
        if not body_ref:
            errors.append(f"{row_label}: body_ref must be a non-empty submove ref")

        record = record_by_ref.get(body_ref)
        if record is None:
            errors.append(f"{row_label}: no visible ACT row has body_ref {body_ref!r}")
        else:
            owner_family = strict_owner_family(str(row.get("owner_id") or ""))
            land_target_tokens = [graph_burden_id(item) for item in land_targets(record.land)]
            land_target = land_target_tokens[0] if land_target_tokens else ""
            if graph_burden_id(row.get("burden_id")) != land_target:
                errors.append(f"{row_label}: burden_id does not match ACT Land target")
            if owner_family != strict_owner_family(record.owner):
                errors.append(f"{row_label}: owner_id does not match visible ACT owner")
            if row.get("operation") != record.operation:
                errors.append(f"{row_label}: operation does not match visible ACT operation")
            if row.get("pressure") != record.pi:
                errors.append(f"{row_label}: pressure does not match visible ACT pressure")
            if row.get("delta_result") != record.delta_result:
                errors.append(f"{row_label}: delta_result does not match visible ACT delta")

        mirror_items = mirrors.get(body_ref, [])
        if len(mirror_items) != 1:
            errors.append(f"{row_label}: field_witness.owner_activations must have exactly one mirror")
        else:
            mirror = mirror_items[0]
            if strict_owner_family(str(row.get("owner_id") or "")) != strict_owner_family(str(mirror.get("owner") or "")):
                errors.append(f"{row_label}: owner_id does not match field_witness mirror")
            if row.get("operation") != mirror.get("operation"):
                errors.append(f"{row_label}: operation does not match field_witness mirror")
            if row.get("pressure") != mirror.get("pressure"):
                errors.append(f"{row_label}: pressure does not match field_witness mirror")
            mirror_delta = str(mirror.get("delta") or "").split(":", 1)[-1]
            if row.get("delta_result") != mirror_delta:
                errors.append(f"{row_label}: delta_result does not match field_witness mirror")
            if body_ref != graph_submove_id(mirror.get("body_ref")):
                errors.append(f"{row_label}: body_ref does not match field_witness mirror")
    return errors


def full_ir_decode_errors(
    path: Path,
    field_witness: dict[str, Any],
    projection: dict[str, Any],
) -> list[str]:
    full = projection.get("full_ir_decode")
    if full is None:
        return []

    label = f"{rel(path)}: field_witness.canonical_ir_projection.full_ir_decode"
    errors = key_shape_errors(full, FULL_IR_DECODE_KEYS, FULL_IR_DECODE_OPTIONAL_KEYS, label)
    if errors:
        return errors

    decoded = projection.get("decoded_ir")
    if not isinstance(decoded, dict):
        errors.append(f"{label}: decoded_ir is required before full_ir_decode")
        decoded = {}

    if full.get("schema") != FULL_IR_DECODE_SCHEMA:
        errors.append(f"{label}: schema must be {FULL_IR_DECODE_SCHEMA!r}")

    source_evidence = string_list(full.get("source_evidence"))
    if source_evidence is None:
        errors.append(f"{label}: source_evidence must be a string list")
    else:
        source_set = set(source_evidence)
        missing_sources = sorted(FULL_IR_DECODE_REQUIRED_SOURCE_EVIDENCE - source_set)
        extra_sources = sorted(source_set - FULL_IR_DECODE_SOURCE_EVIDENCE)
        if missing_sources:
            errors.append(f"{label}: source_evidence missing required source(s): {missing_sources}")
        if extra_sources:
            errors.append(f"{label}: source_evidence has unknown source(s): {extra_sources}")
        if field_witness_generated_burdens(field_witness) and "field_witness.generated_burdens" not in source_set:
            errors.append(f"{label}: source_evidence must include field_witness.generated_burdens")
        if formal_reread_states(field_witness) and "field_witness.formal_reread_states" not in source_set:
            errors.append(f"{label}: source_evidence must include field_witness.formal_reread_states")

    for key in ("n_frame", "live_registers", "burden_floor", "diagnostic_completeness"):
        if full.get(key) != decoded.get(key):
            errors.append(f"{label}: {key} does not match decoded_ir")

    for key in ("B_LA", "B_MRP", "B_total"):
        if full.get(key) != burden_list(field_witness, key):
            errors.append(f"{label}: {key} does not match field_witness")

    coverage = coverage_proof(field_witness)
    dependency_graph = coverage.get("dependency_graph")
    if not isinstance(dependency_graph, dict):
        errors.append(f"{label}: field_witness.coverage_proof.dependency_graph is required")
        dependency_graph = {}
    if full.get("dependency_graph") != dependency_graph:
        errors.append(f"{label}: dependency_graph does not match field_witness coverage_proof")
    if full.get("terminal_states") != coverage.get("terminal_states"):
        errors.append(f"{label}: terminal_states does not match field_witness coverage_proof")

    expected_generated = field_witness_generated_burdens(field_witness)
    if full.get("generated_burdens") != expected_generated:
        errors.append(f"{label}: generated_burdens does not match field_witness")

    if "hard_registers" in projection:
        if full.get("hard_registers") != projection.get("hard_registers"):
            errors.append(f"{label}: hard_registers does not match canonical_ir_projection")
    elif "hard_registers" in full:
        errors.append(f"{label}: hard_registers requires canonical_ir_projection.hard_registers")

    if projection.get("register_composition") is not None:
        if full.get("register_composition") != projection.get("register_composition"):
            errors.append(f"{label}: register_composition does not match canonical_ir_projection")
    elif "register_composition" in full:
        errors.append(f"{label}: register_composition requires canonical_ir_projection.register_composition")

    source_basis = full.get("source_basis")
    source_label = f"{label}.source_basis"
    source_errors = key_shape_errors(source_basis, FULL_IR_SOURCE_BASIS_KEYS, set(), source_label)
    errors.extend(source_errors)
    if not source_errors:
        if not isinstance(source_basis.get("source_basis_available"), bool):
            errors.append(f"{source_label}: source_basis_available must be boolean")
        if source_basis.get("sigma_inside_hard_registers") is not False:
            errors.append(f"{source_label}: sigma_inside_hard_registers must be false")
        basis = string_list(source_basis.get("basis"))
        if basis is None:
            errors.append(f"{source_label}: basis must be a string list")

    states = formal_reread_states(field_witness)
    formal = full.get("formal_reread")
    formal_label = f"{label}.formal_reread"
    formal_errors = key_shape_errors(formal, FULL_IR_FORMAL_REREAD_KEYS, set(), formal_label)
    errors.extend(formal_errors)
    if not formal_errors:
        states_present = bool(states)
        if formal.get("states_present") is not states_present:
            errors.append(f"{formal_label}: states_present does not match field_witness.formal_reread_states")
        final_state = states[-1] if states else {}
        expected_divergence = final_state.get("divergence_state", coverage.get("divergence_check"))
        expected_curl = final_state.get("curl_state", coverage.get("curl_check"))
        if formal.get("divergence_state") != expected_divergence:
            errors.append(f"{formal_label}: divergence_state does not match terminal formal reread/coverage")
        if formal.get("curl_state") != expected_curl:
            errors.append(f"{formal_label}: curl_state does not match terminal formal reread/coverage")
        if formal.get("escape_routes_checked") != flattened_escape_routes(states):
            errors.append(f"{formal_label}: escape_routes_checked does not match field_witness.formal_reread_states")
        if formal.get("no_new_resultant_proof") != terminal_no_new_resultant_proof(states):
            errors.append(f"{formal_label}: no_new_resultant_proof does not match terminal formal reread state")

    decoded_rows = decoded.get("per_burden")
    full_rows = full.get("per_burden")
    if not isinstance(decoded_rows, list) or not isinstance(full_rows, list):
        errors.append(f"{label}: per_burden must mirror decoded_ir.per_burden")
        return errors
    if len(full_rows) != len(decoded_rows):
        errors.append(f"{label}: per_burden row count does not match decoded_ir")

    generated_map = generated_burden_map(field_witness)
    b_la = set(burden_list(field_witness, "B_LA"))
    for index, row in enumerate(full_rows):
        row_label = f"{label}.per_burden[{index}]"
        row_errors = key_shape_errors(row, FULL_IR_DECODE_ROW_KEYS, set(), row_label)
        errors.extend(row_errors)
        if row_errors:
            continue
        if index < len(decoded_rows):
            decoded_row = decoded_rows[index]
            if isinstance(decoded_row, dict):
                decoded_core = {key: decoded_row.get(key) for key in CANONICAL_IR_DECODE_ROW_KEYS}
                row_core = {key: row.get(key) for key in CANONICAL_IR_DECODE_ROW_KEYS}
                if row_core != decoded_core:
                    errors.append(f"{row_label}: core fields do not match decoded_ir")
        burden_id = graph_burden_id(row.get("burden_id"))
        expected_role = graph_role_for_burden(burden_id, dependency_graph)
        if row.get("graph_role") not in FULL_IR_GRAPH_ROLES:
            errors.append(f"{row_label}: graph_role is not controlled")
        elif row.get("graph_role") != expected_role:
            errors.append(f"{row_label}: graph_role does not match dependency_graph")
        if row.get("track") not in FULL_IR_TRACKS:
            errors.append(f"{row_label}: track is not controlled")
        generated = generated_map.get(burden_id)
        if generated:
            if row.get("generated_by") != generated.get("generated_by"):
                errors.append(f"{row_label}: generated_by does not match field_witness.generated_burdens")
            if row.get("track") != generated.get("track"):
                errors.append(f"{row_label}: track does not match field_witness.generated_burdens")
        elif burden_id in b_la:
            if row.get("generated_by") is not None:
                errors.append(f"{row_label}: baseline burden generated_by must be null")
            if row.get("track") != "baseline":
                errors.append(f"{row_label}: baseline burden track must be 'baseline'")
        else:
            errors.append(f"{row_label}: burden_id is neither B_LA nor generated burden")
    return errors


def full_ir_proof_mode_errors(path: Path, projection: dict[str, Any]) -> list[str]:
    label = f"{rel(path)}: field_witness.canonical_ir_projection.proof_mode"
    proof_mode = projection.get("proof_mode")
    full_decode = projection.get("full_ir_decode")
    decoded = projection.get("decoded_ir")
    errors: list[str] = []

    if full_decode is not None and proof_mode is None:
        errors.append(
            f"{rel(path)}: field_witness.canonical_ir_projection.full_ir_decode "
            "requires proof_mode adoption marker"
        )
    if proof_mode is None:
        return errors

    errors.extend(key_shape_errors(proof_mode, FULL_IR_PROOF_MODE_KEYS, set(), label))
    if full_decode is None:
        errors.append(f"{label}: proof_mode requires full_ir_decode")
    if not isinstance(decoded, dict):
        errors.append(f"{label}: proof_mode requires decoded_ir")
    if errors:
        return errors

    if proof_mode.get("schema") != FULL_IR_PROOF_MODE_SCHEMA:
        errors.append(f"{label}: schema must be {FULL_IR_PROOF_MODE_SCHEMA!r}")
    if proof_mode.get("mode") not in FULL_IR_PROOF_MODE_MODES:
        errors.append(f"{label}: mode is not controlled")

    source_evidence = string_list(proof_mode.get("source_evidence"))
    if source_evidence is None:
        errors.append(f"{label}: source_evidence must be a string list")
    else:
        source_set = set(source_evidence)
        missing = sorted(FULL_IR_PROOF_MODE_SOURCE_EVIDENCE - source_set)
        extra = sorted(source_set - FULL_IR_PROOF_MODE_SOURCE_EVIDENCE)
        if missing:
            errors.append(f"{label}: source_evidence missing required source(s): {missing}")
        if extra:
            errors.append(f"{label}: source_evidence has unknown source(s): {extra}")

    for key in (
        "machine_facing",
        "schema_light_absent_valid",
        "requires_decoded_ir",
        "visible_opening_header_preserved",
    ):
        if proof_mode.get(key) is not True:
            errors.append(f"{label}: {key} must be true")

    for key in (
        "arbitrary_nl_ir_parser_claim",
        "default_runtime_emission_claim",
        "t_lang_uptake_claim",
    ):
        if proof_mode.get(key) is not False:
            errors.append(f"{label}: {key} must be false")

    return errors


def runtime_emission_policy_errors(path: Path, projection: dict[str, Any]) -> list[str]:
    label = f"{rel(path)}: field_witness.canonical_ir_projection.emission_policy"
    policy = projection.get("emission_policy")
    if policy is None:
        return []
    errors: list[str] = []
    errors.extend(key_shape_errors(policy, RUNTIME_EMISSION_POLICY_KEYS, set(), label))
    if not isinstance(projection.get("proof_mode"), dict):
        errors.append(f"{label}: runtime emission policy requires proof_mode")
    if not isinstance(projection.get("decoded_ir"), dict):
        errors.append(f"{label}: runtime emission policy requires decoded_ir")
    if not isinstance(projection.get("full_ir_decode"), dict):
        errors.append(f"{label}: runtime emission policy requires full_ir_decode")
    if errors:
        return errors

    if policy.get("schema") != RUNTIME_EMISSION_POLICY_SCHEMA:
        errors.append(f"{label}: schema must be {RUNTIME_EMISSION_POLICY_SCHEMA!r}")
    if policy.get("mode") not in RUNTIME_EMISSION_POLICY_MODES:
        errors.append(f"{label}: mode is not controlled")

    source_evidence = string_list(policy.get("source_evidence"))
    if source_evidence is None:
        errors.append(f"{label}: source_evidence must be a string list")
    else:
        source_set = set(source_evidence)
        missing = sorted(RUNTIME_EMISSION_POLICY_SOURCE_EVIDENCE - source_set)
        extra = sorted(source_set - RUNTIME_EMISSION_POLICY_SOURCE_EVIDENCE)
        if missing:
            errors.append(f"{label}: source_evidence missing required source(s): {missing}")
        if extra:
            errors.append(f"{label}: source_evidence has unknown source(s): {extra}")

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
            errors.append(f"{label}: {key} must be true")

    for key in (
        "public_prose_replacement",
        "arbitrary_nl_ir_parser_claim",
        "t_lang_uptake_claim",
    ):
        if policy.get(key) is not False:
            errors.append(f"{label}: {key} must be false")

    proof_mode = projection["proof_mode"]
    if proof_mode.get("schema") != FULL_IR_PROOF_MODE_SCHEMA:
        errors.append(f"{label}: proof_mode schema must be {FULL_IR_PROOF_MODE_SCHEMA!r}")
    if proof_mode.get("default_runtime_emission_claim") is not False:
        errors.append(f"{label}: B.5.3 proof_mode v1 default_runtime_emission_claim remains false")
    return errors


def canonical_ir_projection_errors(
    path: Path,
    field_witness: dict[str, Any],
    records: list[ActRecord],
) -> list[str]:
    projection = field_witness.get("canonical_ir_projection")
    if projection is None:
        return []
    if not isinstance(projection, dict):
        return [f"{rel(path)}: field_witness.canonical_ir_projection must be an object"]
    return canonical_ir_projection_object_errors(path, "", field_witness, records, projection)


def canonical_ir_projection_object_errors(
    path: Path,
    text: str,
    field_witness: dict[str, Any],
    records: list[ActRecord],
    projection: dict[str, Any],
) -> list[str]:
    """Validate an explicit projection object against already-emitted evidence.

    Retained proof-corpus sidecars use this path. It does not parse prose into
    IR; it checks a caller-supplied projection against visible ACT rows,
    field_witness, NAR, and coverage evidence.
    """

    if not isinstance(projection, dict):
        return [f"{rel(path)}: field_witness.canonical_ir_projection must be an object"]
    projected_witness = dict(field_witness)
    projected_witness["canonical_ir_projection"] = projection
    opening_errors = projection_opening_surface_errors(path, text, projected_witness) if text else []
    return (
        opening_errors
        + canonical_ir_projection_common_errors(path, field_witness, projection, records)
        + hard_register_projection_errors(path, field_witness, projection)
        + register_composition_projection_errors(path, projection)
        + canonical_ir_decode_errors(path, field_witness, projection, records)
        + full_ir_decode_errors(path, field_witness, projection)
        + full_ir_proof_mode_errors(path, projection)
        + runtime_emission_policy_errors(path, projection)
    )


def activation_mirror_errors(
    path: Path,
    record: ActRecord,
    target: str,
    mirror: dict[str, Any] | None,
) -> list[str]:
    label = f"{rel(path)}: ACT {record.submove_ref}"
    if mirror is None:
        return [f"{label}: field_witness.owner_activations missing mirror for body_ref {record.body_ref}"]

    errors: list[str] = []
    self_claims = sorted(UNTRUSTED_ACTIVATION_SELF_CLAIMS.intersection(mirror))
    if self_claims:
        errors.append(
            f"{label}: model-authored activation verification fields are not proof: "
            + ", ".join(self_claims)
        )

    record_family = strict_owner_family(record.owner)
    mirror_family = strict_owner_family(str(mirror.get("owner") or ""))
    if record_family != mirror_family:
        errors.append(f"{label}: field_witness owner does not decode to ACT owner family")
    if str(mirror.get("operation") or "").strip() != record.operation:
        errors.append(f"{label}: field_witness operation does not match ACT operation")
    if str(mirror.get("pressure") or "").strip() != record.pi:
        errors.append(f"{label}: field_witness pressure does not match ACT pressure")
    if not transition_values_agree(mirror.get("delta"), f"{record.delta}:{record.delta_result}"):
        errors.append(f"{label}: field_witness delta does not match ACT delta/result")
    mirror_land_targets = [graph_burden_id(item) for item in land_targets(str(mirror.get("land") or ""))]
    if target not in mirror_land_targets:
        errors.append(f"{label}: field_witness land does not target Land({target})")
    mirror_target = graph_burden_id(mirror.get("target"))
    if mirror_target and mirror_target != target:
        errors.append(f"{label}: field_witness target {mirror_target} disagrees with ACT Land({target})")
    mirror_ref = graph_submove_id(mirror.get("body_ref"))
    if mirror_ref != graph_submove_id(record.body_ref):
        errors.append(f"{label}: field_witness body_ref does not match ACT body_ref")
    return errors


def decode_facets(path: Path, text: str, record: ActRecord) -> tuple[DecodedFacets | None, list[str]]:
    label = f"{rel(path)}: ACT {record.submove_ref}"
    errors: list[str] = []
    canonical = canonical_activation_from_record(record)
    rendered = render_act(canonical)
    if record.record != rendered:
        errors.append(f"{label}: ACT row does not match checker-rendered CanonicalActivation")
    if record.submove_ref != record.body_ref:
        errors.append(f"{label}: body_ref must equal the encoded submove ref")

    owner_family = strict_owner_family(record.owner)
    if not owner_family:
        errors.append(f"{label}: owner {record.owner!r} is not catalogue-backed")
    if GENERIC_ACT_VALUE_RE.fullmatch(record.operation):
        errors.append(f"{label}: operation is generic and cannot be decoded faithfully")
    formal_allowed = (
        FORMAL_OWNER_CONTRACT_OPERATIONS.get(owner_contract_key(record.owner))
        or FORMAL_OWNER_CONTRACT_OPERATIONS.get(owner_contract_key(owner_family))
    )
    if formal_allowed and record.operation not in formal_allowed:
        expected = ", ".join(sorted(formal_allowed))
        errors.append(
            f"{label}: operation {record.operation!r} is not declared by formal owner contract; "
            f"expected one of: {expected}"
        )

    land_target_tokens = [graph_burden_id(item) for item in land_targets(record.land)]
    target = land_target_tokens[0] if land_target_tokens else ""
    if not target:
        errors.append(f"{label}: Land clause must name a burden target")
    body_ref_target = graph_submove_id(record.body_ref).split("_", 1)[0]
    if target and body_ref_target and body_ref_target != target:
        errors.append(f"{label}: body_ref {graph_submove_id(record.body_ref)!r} does not belong to Land({target})")

    section = public_execution_text(text)
    raw_target = target_token_from_submove_ref(record.body_ref)
    blocks = (
        submove_block_index(section, raw_target).get(graph_submove_id(record.body_ref), [])
        if raw_target
        else []
    )
    if len(blocks) != 1:
        errors.append(f"{label}: body_ref must dereference to exactly one Layer B submove body")
        return None, errors
    block = blocks[0]
    _block_ref, block_owner = submove_block_ref_owner(block)
    body_owner_family = strict_owner_family(block_owner)
    if owner_family and body_owner_family != owner_family:
        errors.append(f"{label}: body owner {block_owner!r} does not decode to ACT owner family {owner_family}")

    facets = DecodedFacets(
        body_ref=graph_submove_id(record.body_ref),
        owner_family=owner_family,
        operation=record.operation,
        pressure=record.pi,
        delta_result=record.delta_result,
        land_target=target,
        body_target=field_body(block, "Target"),
        body_owner_family=body_owner_family,
        body_operation=field_body_any(block, ("Operation", "What it does")),
        body_result=field_body_any(block, ("Result", "Result/state-change")),
        body_contribution=contribution_body(block),
        body_prose=submove_operation_body(block),
    )
    return facets, errors


def semantic_faithfulness_errors(path: Path, record: ActRecord, facets: DecodedFacets) -> list[str]:
    label = f"{rel(path)}: ACT {record.submove_ref}"
    errors: list[str] = []
    body_scope = "\n".join(
        (
            facets.body_target,
            facets.body_operation,
            facets.body_result,
            facets.body_contribution,
            facets.body_prose,
        )
    )
    result_scope = "\n".join((facets.body_result, facets.body_contribution, facets.body_prose))
    operation_scope = "\n".join((facets.body_operation, facets.body_result, facets.body_contribution, facets.body_prose))

    if not facets.body_target:
        errors.append(f"{label}: dereferenced body missing Target facet")
    if not facets.body_operation:
        errors.append(f"{label}: dereferenced body missing Operation facet")
    if not facets.body_result:
        errors.append(f"{label}: dereferenced body missing Result/state-change facet")
    if not facets.body_contribution:
        errors.append(f"{label}: dereferenced body missing Contribution-to-Land facet")
    if errors:
        return errors

    if not keywords_recoverable(facets.pressure, body_scope):
        errors.append(f"{label}: pressure label is not recoverable from dereferenced body")
    if not operation_recoverable(facets.operation, facets.body_operation, operation_scope):
        errors.append(f"{label}: operation label is not recoverable from dereferenced body")
    if not keywords_recoverable(facets.delta_result, result_scope):
        errors.append(f"{label}: delta/result label is not recoverable from body result or contribution")
    if not STATE_CHANGE_RE.search(result_scope):
        errors.append(f"{label}: body result/contribution lacks a concrete state-change verb")
    if facets.land_target and not contribution_names_land(
        "\n".join((f"Contribution-to-Land({facets.land_target}): {facets.body_contribution}", facets.body_prose)),
        facets.land_target,
    ):
        errors.append(f"{label}: body contribution does not decode to Land({facets.land_target})")
    return errors


def reconstruct_layer_b_submove(path: Path, record: ActRecord) -> tuple[str | None, list[str]]:
    """Build the bounded B.5 reconstruction surrogate for one canonical ACT.

    This is intentionally modest: it proves that the checker-owned activation
    slots can regenerate a verifier-passable Layer B body. Full IR-state
    reconstruction remains dependent on the hard register schema migration.
    """

    label = f"{rel(path)}: ACT {record.submove_ref}"
    errors: list[str] = []
    canonical = canonical_activation_from_record(record)
    owner_family = strict_owner_family(canonical.owner)
    if not owner_family:
        errors.append(f"{label}: cannot reconstruct from non-catalogue owner {canonical.owner!r}")
    if GENERIC_ACT_VALUE_RE.fullmatch(canonical.operation):
        errors.append(f"{label}: cannot reconstruct from generic operation {canonical.operation!r}")
    if GENERIC_ACT_VALUE_RE.fullmatch(canonical.pressure):
        errors.append(f"{label}: cannot reconstruct from generic pressure {canonical.pressure!r}")
    if GENERIC_ACT_VALUE_RE.fullmatch(record.delta_result):
        errors.append(f"{label}: cannot reconstruct from generic delta/result {record.delta_result!r}")

    land_target_tokens = [graph_burden_id(item) for item in land_targets(canonical.land)]
    target = land_target_tokens[0] if land_target_tokens else ""
    if not target:
        errors.append(f"{label}: cannot reconstruct without Land target")
    raw_body_ref = canonical.body_ref
    body_ref = graph_submove_id(raw_body_ref)
    body_ref_target = body_ref.split("_", 1)[0]
    if target and body_ref_target and body_ref_target != target:
        errors.append(f"{label}: cannot reconstruct body_ref {body_ref!r} into Land({target})")
    if errors:
        return None, errors

    pressure = canonical.pressure
    operation = canonical.operation
    delta_result = record.delta_result
    reconstructed = "\n".join(
        (
            f"### {raw_body_ref}[{canonical.owner}] - reconstructed {operation} over {pressure}",
            f"Target: {pressure}.",
            (
                f"Operation: {operation} acts on {pressure}; owner family {owner_family} "
                "performs the named operation rather than merely echoing the label."
            ),
            (
                f"Result/state-change: {delta_result}; state-change: {pressure} is no "
                f"longer load-bearing after {operation}."
            ),
            (
                f"Contribution-to-Land({target}): This {delta_result} state change "
                f"contributes to Land({target}) by making {pressure} no longer "
                "load-bearing."
            ),
            "",
            "TTP Operation Body:",
            (
                f"The reconstructed {owner_family} operation recovers {operation}, "
                f"targets {pressure}, makes {delta_result} visible, and explains the "
                f"local state change that licenses Land({target})."
            ),
        )
    )
    return reconstructed, []


def reconstructed_submove_errors(
    path: Path,
    record: ActRecord,
    reconstructed_submoves: list[str] | None = None,
) -> list[str]:
    label = f"{rel(path)}: ACT {record.submove_ref}"
    reconstructed, errors = reconstruct_layer_b_submove(path, record)
    if reconstructed is None:
        return errors
    target = target_token_from_submove_ref(record.body_ref)
    blocks = (
        submove_block_index(reconstructed, target).get(graph_submove_id(record.body_ref), [])
        if target
        else []
    )
    if len(blocks) != 1:
        return errors + [f"{label}: reconstructed Layer B submove is not parser-stable"]
    block = blocks[0]
    _block_ref, block_owner = submove_block_ref_owner(block)
    land_target_tokens = [graph_burden_id(item) for item in land_targets(record.land)]
    land_target = land_target_tokens[0] if land_target_tokens else ""
    facets = DecodedFacets(
        body_ref=graph_submove_id(record.body_ref),
        owner_family=strict_owner_family(record.owner),
        operation=record.operation,
        pressure=record.pi,
        delta_result=record.delta_result,
        land_target=land_target,
        body_target=field_body(block, "Target"),
        body_owner_family=strict_owner_family(block_owner),
        body_operation=field_body_any(block, ("Operation", "What it does")),
        body_result=field_body_any(block, ("Result", "Result/state-change")),
        body_contribution=contribution_body(block),
        body_prose=submove_operation_body(block),
    )
    errors.extend(semantic_faithfulness_errors(path, record, facets))
    if facets.body_owner_family != facets.owner_family:
        errors.append(f"{label}: reconstructed body owner does not match ACT owner family")
    if not errors and reconstructed_submoves is not None:
        reconstructed_submoves.append(reconstructed)
    return errors


def nla_decode_errors(
    path: Path,
    text: str,
    reconstructed_submoves: list[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    field_witness, found = parse_field_witness(path, text)
    errors.extend(found)
    if field_witness is None:
        return errors
    errors.extend(projection_opening_surface_errors(path, text, field_witness))
    mirrors = field_witness_activation_by_body_ref(field_witness)
    raw_activations = field_witness.get("owner_activations")
    if not isinstance(raw_activations, list):
        errors.append(f"{rel(path)}: field_witness.owner_activations must be a list")

    records, parse_errors = parse_act_records(public_execution_text(text))
    errors.extend(f"{rel(path)}: {message}" for message in parse_errors)
    if not records:
        return errors + [f"{rel(path)}: no visible ACT records to decode"]

    errors.extend(activation_surface_coverage_errors(path, field_witness, records))
    errors.extend(canonical_ir_projection_errors(path, field_witness, records))

    seen_body_refs: set[str] = set()
    for record in records:
        body_ref = graph_submove_id(record.body_ref)
        if body_ref in seen_body_refs:
            errors.append(f"{rel(path)}: duplicate ACT body_ref {body_ref}")
        seen_body_refs.add(body_ref)

        facets, decode_found = decode_facets(path, text, record)
        errors.extend(decode_found)
        target = facets.land_target if facets else ""
        mirror_items = mirrors.get(body_ref, [])
        if len(mirror_items) > 1:
            errors.append(f"{rel(path)}: field_witness.owner_activations has duplicate mirror for {body_ref}")
            mirror = mirror_items[0]
        else:
            mirror = mirror_items[0] if mirror_items else None
        errors.extend(activation_mirror_errors(path, record, target, mirror))
        if facets is not None:
            errors.extend(semantic_faithfulness_errors(path, record, facets))
        errors.extend(reconstructed_submove_errors(path, record, reconstructed_submoves))
    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0
    reconstructed_submoves: list[str] = []

    for path in valid:
        found = nla_decode_errors(path, read_text(path), reconstructed_submoves)
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = nla_decode_errors(path, read_text(path))
        if not found:
            errors.append(f"{rel(path)}: expected-invalid NLA decode fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in expand_paths(args.outputs):
        if not path.exists():
            errors.append(f"{path}: output path not found")
            continue
        found = nla_decode_errors(path, read_text(path), reconstructed_submoves)
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("NLA decode semantic-faithfulness check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("NLA decode semantic-faithfulness check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    print(f"Reconstructed submoves checked: {len(reconstructed_submoves)}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
