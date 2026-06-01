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
HARD_REGISTER_SCHEMA_VERSION = "0.4.3-hard-registers-v1"
CANONICAL_IR_PROJECTION_SCHEMA = "b5-canonical-ir-projection-v1"
REGISTER_COMPOSITION_SCHEMA = "b5-register-composition-v1"
REGISTER_COMPOSITION_SOURCE_FIXTURE = "tests/routing-fixtures/63-register-composition-owner-handoff.json"
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
    "component_registers",
    "sigma_boundary",
    "composition_rule",
    "owner_handoff",
    "automatic_dispatch_chain",
    "evidence",
}
REGISTER_COMPOSITION_SIGMA_KEYS = {"present", "inside_hard_registers", "role"}
REGISTER_COMPOSITION_OWNER_HANDOFF_KEYS = {"selected", "held", "policy"}


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


def string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return None
    return value


def diagnostic_completeness(field_witness: dict[str, Any]) -> dict[str, Any] | None:
    coverage = field_witness.get("coverage_proof")
    if not isinstance(coverage, dict):
        return None
    diagnostic = coverage.get("diagnostic_completeness")
    return diagnostic if isinstance(diagnostic, dict) else None


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
    if source_fixture != REGISTER_COMPOSITION_SOURCE_FIXTURE:
        errors.append(f"{label}: source_fixture must be {REGISTER_COMPOSITION_SOURCE_FIXTURE!r}")
    elif not (ROOT / source_fixture).is_file():
        errors.append(f"{label}: source_fixture path does not exist")

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
            errors.append(f"{label}.sigma_boundary: present must be true for fixture 63 composition")
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
    for term in ("fixture 63", "r(h,delta)", "owner eligibility"):
        if term not in evidence_text:
            errors.append(f"{label}: evidence must include {term!r}")

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
    return (
        canonical_ir_projection_common_errors(path, field_witness, projection, records)
        + hard_register_projection_errors(path, field_witness, projection)
        + register_composition_projection_errors(path, projection)
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

    land_target_tokens = [graph_burden_id(item) for item in land_targets(record.land)]
    target = land_target_tokens[0] if land_target_tokens else ""
    if not target:
        errors.append(f"{label}: Land clause must name a burden target")
    body_ref_target = graph_submove_id(record.body_ref).split("_", 1)[0]
    if target and body_ref_target and body_ref_target != target:
        errors.append(f"{label}: body_ref {graph_submove_id(record.body_ref)!r} does not belong to Land({target})")

    section = public_execution_text(text)
    raw_target = target_token_from_submove_ref(record.body_ref)
    blocks = submove_block_index(section, raw_target).get(record.body_ref, []) if raw_target else []
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
    blocks = submove_block_index(reconstructed, target).get(record.body_ref, []) if target else []
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
