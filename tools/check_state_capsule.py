#!/usr/bin/env python3
"""Validate the typed state capsule contract daee-state-capsule-v1 (Slice D wave 1, Plan 03).

A state capsule is the small, structured hand-off meant to let a single model
call receive kernel + capsule + selected shards instead of replaying a full
150-300KB output.md or a 300k-token runtime. This checker validates ONE
capsule's shape + semantic invariants (--capsule), an ORDERED capsule sequence
against an artifact.md for cross-capsule replay invariants (--replay), and
runs an embedded + fixture self-test (--self-test).

Scope discipline: this is a structural + semantic validation of the capsule
contract only. It does not certify interlocutor uptake, semantic faithfulness,
or release provenance, and it does not replace the harness emission wave that
will actually produce capsules at runtime (that is the next wave, not this one).

Stdlib-only; no jsonschema dependency, following the repo's existing custom
validation style (see tools/check_collapse_certificate_schema.py).

Usage:
  python tools/check_state_capsule.py --capsule <path.json>
  python tools/check_state_capsule.py --replay <dir>
  python tools/check_state_capsule.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "state-capsule.schema.json"
FIXTURE_ROOT = ROOT / "tests" / "state-capsule-fixtures"

SCHEMA_CONST = "daee-state-capsule-v1"

STAGE_ORDER = ["01", "02", "03", "04", "05", "06", "07", "08"]
STAGE_INDEX = {stage: index for index, stage in enumerate(STAGE_ORDER)}

LIVE_REGISTER_TOKENS = {
    "N", "m", "tau", "sigma", "heart", "xi", "Omega", "mu", "kappa", "H",
    "τ",  # tau
    "σ",  # sigma
    "♥",  # heart
    "ξ",  # xi
    "Ω",  # Omega
    "μ",  # mu
    "κ",  # kappa
}

ROUTE_RESULT_TYPES = {
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "loopbreak",
    "hold_partial",
    "none",
}

DIVERGENCE_STATES = {"neutral", "settled", "bounded", "non-neutral"}
CURL_STATES = {"null-state", "resolved", "held", "non-null"}
TRANSPORT_VALUES = {"chat", "file-retained"}

FINGERPRINT_RE = re.compile(r"^sha256:[A-Fa-f0-9]{64}$")
SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")
# Bare join-key body_ref: optional leading Unicode superscript digits, then
# B<digits>, optional _<digits> submove suffix. No '[' (owner/operation
# pollution) and no '.' beyond this pattern. Superscript digits 0-9 are NOT a
# contiguous Unicode range (0xB9/0xB2/0xB3 sit outside the 0x2070-0x2079
# block used for 0,4-9), so they are listed explicitly -- same set as SUP in
# tools/check_mrp_route_invariants.py.
SUPERSCRIPT_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
BODY_REF_RE = re.compile(rf"^[{SUPERSCRIPT_DIGITS}]*B[0-9]+(?:_[0-9]+)?$")

WARN_BYTES = 16_000
FAIL_BYTES = 40_000

CLOSED_TERMINAL_MARKERS = ("land", "rejected", "merged")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    if not path.exists():
        return None, [f"{rel(path)}: file not found"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)}: invalid JSON: {exc}"]


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Structural (schema) validation
# ---------------------------------------------------------------------------

def schema_required_optional(schema: dict[str, Any]) -> tuple[set[str], set[str]]:
    required = set(schema.get("required", []))
    optional = set(schema.get("properties", {})) - required
    return required, optional


def _type_ok(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_type_ok(value, item) for item in expected)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def structural_errors(label: str, payload: Any, schema: dict[str, Any]) -> list[str]:
    """Pure core: validate `payload` is a well-shaped capsule per the schema's
    top-level contract. Deliberately hand-rolled (no jsonschema dependency)
    mirroring tools/check_collapse_certificate_schema.py's local style."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{label}: capsule must be a JSON object"]

    required, optional = schema_required_optional(schema)
    allowed = required | optional
    keys = set(payload)

    missing = sorted(required - keys)
    if missing:
        errors.append(f"{label}: missing required field(s): {missing}")
    unknown = sorted(keys - allowed)
    if unknown:
        errors.append(f"{label}: unknown top-level field(s) (additionalProperties=false): {unknown}")

    if payload.get("schema") != SCHEMA_CONST:
        errors.append(f"{label}: schema must be {SCHEMA_CONST!r}, got {payload.get('schema')!r}")

    if "case_id" in payload and not (isinstance(payload["case_id"], str) and payload["case_id"]):
        errors.append(f"{label}: case_id must be a non-empty string")

    fp = payload.get("input_fingerprint")
    if "input_fingerprint" in payload and not (isinstance(fp, str) and FINGERPRINT_RE.match(fp)):
        errors.append(f"{label}: input_fingerprint must match sha256:<64 hex>")

    stage = payload.get("stage")
    if "stage" in payload and stage not in STAGE_INDEX:
        errors.append(f"{label}: stage must be one of {STAGE_ORDER}, got {stage!r}")

    errors.extend(_n_frame_errors(label, payload.get("n_frame")))
    errors.extend(_live_registers_errors(label, payload.get("live_registers")))

    if "register_state" in payload and not isinstance(payload["register_state"], dict):
        errors.append(f"{label}: register_state must be an object")

    for key in ("B_LA", "B_MRP", "B_total", "cold_law_refs_used", "shards_loaded"):
        if key in payload:
            errors.extend(_string_array_errors(label, key, payload[key]))

    errors.extend(_held_set_errors(label, payload.get("held_set_H")))
    errors.extend(_completed_acts_errors(label, payload.get("completed_acts")))
    errors.extend(_last_terminal_errors(label, payload.get("last_terminal")))

    if "last_delta" in payload and not (payload["last_delta"] is None or isinstance(payload["last_delta"], str)):
        errors.append(f"{label}: last_delta must be a string or null")

    errors.extend(_last_mrp_resultant_errors(label, payload.get("last_mrp_resultant")))

    rrt = payload.get("route_result_type")
    if "route_result_type" in payload and rrt not in ROUTE_RESULT_TYPES:
        errors.append(f"{label}: route_result_type must be one of {sorted(ROUTE_RESULT_TYPES)}, got {rrt!r}")

    errors.extend(_field_diagnostics_errors(label, payload.get("field_diagnostics")))

    transport = payload.get("transport")
    if "transport" in payload and transport not in TRANSPORT_VALUES:
        errors.append(f"{label}: transport must be one of {sorted(TRANSPORT_VALUES)}, got {transport!r}")

    if "terminal_states" in payload and not isinstance(payload["terminal_states"], dict):
        errors.append(f"{label}: terminal_states must be an object")

    if "next_burden" in payload and not (payload["next_burden"] is None or isinstance(payload["next_burden"], str)):
        errors.append(f"{label}: next_burden must be a string or null")

    errors.extend(_current_owner_route_errors(label, payload.get("current_owner_route")))

    if "coverage_complete" in payload and not isinstance(payload["coverage_complete"], bool):
        errors.append(f"{label}: coverage_complete must be a boolean")

    if "next_required_action" in payload and not isinstance(payload["next_required_action"], str):
        errors.append(f"{label}: next_required_action must be a string")

    oap = payload.get("output_artifact_path")
    if "output_artifact_path" in payload and not (oap is None or isinstance(oap, str)):
        errors.append(f"{label}: output_artifact_path must be a string or null")

    osha = payload.get("output_sha256")
    if "output_sha256" in payload and not (osha is None or (isinstance(osha, str) and (osha == "" or SHA256_RE.match(osha)))):
        errors.append(f"{label}: output_sha256 must be a 64-hex sha256 string, empty string, or null")

    oob = payload.get("output_offset_bytes")
    if "output_offset_bytes" in payload and not (isinstance(oob, int) and not isinstance(oob, bool) and oob >= 0):
        errors.append(f"{label}: output_offset_bytes must be an integer >= 0")

    if "notes" in payload and not isinstance(payload["notes"], str):
        errors.append(f"{label}: notes must be a string")

    return errors


def _string_array_errors(label: str, key: str, value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return [f"{label}: {key} must be an array of non-empty strings"]
    return []


def _n_frame_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: n_frame must be an object"]
    errors: list[str] = []
    required = {"selected", "held_candidates"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: n_frame missing field(s): {missing}")
    unknown = sorted(set(value) - required)
    if unknown:
        errors.append(f"{label}: n_frame has unknown field(s): {unknown}")
    if "selected" in value and not (isinstance(value["selected"], str) and value["selected"]):
        errors.append(f"{label}: n_frame.selected must be a non-empty string")
    if "held_candidates" in value:
        errors.extend(_string_array_errors(label, "n_frame.held_candidates", value["held_candidates"]))
    return errors


def _live_registers_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        return [f"{label}: live_registers must be an array"]
    errors: list[str] = []
    if len(value) != len(set(value)):
        errors.append(f"{label}: live_registers must have unique entries")
    unknown = [item for item in value if item not in LIVE_REGISTER_TOKENS]
    if unknown:
        errors.append(f"{label}: live_registers has unrecognized register token(s): {unknown}")
    return errors


def _held_set_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        return [f"{label}: held_set_H must be an array"]
    errors: list[str] = []
    for index, entry in enumerate(value):
        item_label = f"{label}: held_set_H[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{item_label}: must be an object")
            continue
        required = {"burden", "reason"}
        missing = sorted(required - set(entry))
        if missing:
            errors.append(f"{item_label}: missing field(s): {missing}")
        unknown = sorted(set(entry) - required)
        if unknown:
            errors.append(f"{item_label}: unknown field(s): {unknown}")
        if "burden" in entry and not (isinstance(entry["burden"], str) and entry["burden"]):
            errors.append(f"{item_label}: burden must be a non-empty string")
        if "reason" in entry and not (isinstance(entry["reason"], str) and entry["reason"]):
            errors.append(f"{item_label}: reason must be a non-empty string")
    return errors


def _completed_acts_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        return [f"{label}: completed_acts must be an array"]
    errors: list[str] = []
    required = {"body_ref", "owner_id", "operation", "register_axis", "delta_result", "land"}
    for index, entry in enumerate(value):
        item_label = f"{label}: completed_acts[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{item_label}: must be an object")
            continue
        missing = sorted(required - set(entry))
        if missing:
            errors.append(f"{item_label}: missing field(s): {missing}")
        unknown = sorted(set(entry) - required)
        if unknown:
            errors.append(f"{item_label}: unknown field(s): {unknown}")
        for key in required:
            if key in entry and not (isinstance(entry[key], str) and entry[key]):
                errors.append(f"{item_label}.{key} must be a non-empty string")
        errors.extend(body_ref_pollution_errors(item_label, entry.get("body_ref")))
    return errors


def body_ref_pollution_errors(label: str, body_ref: Any) -> list[str]:
    """Pure core: body_ref must be a bare join key (no owner/operation
    pollution). Reject '[' anywhere, and reject '.' entirely since the bare
    burden/submove shape (B1, B1_1, superscript-prefixed forms) never uses '.'.
    """
    if not isinstance(body_ref, str) or not body_ref:
        return [f"{label}.body_ref must be a non-empty string"]
    if "[" in body_ref or "." in body_ref:
        return [f"{label}.body_ref {body_ref!r} is polluted with owner/operation syntax ('[' or '.')"]
    if not BODY_REF_RE.match(body_ref):
        return [f"{label}.body_ref {body_ref!r} is not a bare join key (expected form like 'B1_1')"]
    return []


def _last_terminal_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: last_terminal must be an object"]
    errors: list[str] = []
    required = {"burden", "state"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: last_terminal missing field(s): {missing}")
    unknown = sorted(set(value) - required)
    if unknown:
        errors.append(f"{label}: last_terminal has unknown field(s): {unknown}")
    for key in ("burden", "state"):
        if key in value and not (value[key] is None or isinstance(value[key], str)):
            errors.append(f"{label}: last_terminal.{key} must be a string or null")
    return errors


def _last_mrp_resultant_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: last_mrp_resultant must be an object"]
    errors: list[str] = []
    required = {"source", "route_result_type"}
    optional = {"generated_by", "next_burden"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: last_mrp_resultant missing field(s): {missing}")
    unknown = sorted(set(value) - required - optional)
    if unknown:
        errors.append(f"{label}: last_mrp_resultant has unknown field(s): {unknown}")
    if "source" in value and not (value["source"] is None or isinstance(value["source"], str)):
        errors.append(f"{label}: last_mrp_resultant.source must be a string or null")
    rrt = value.get("route_result_type")
    if "route_result_type" in value and rrt not in ROUTE_RESULT_TYPES:
        errors.append(f"{label}: last_mrp_resultant.route_result_type must be one of {sorted(ROUTE_RESULT_TYPES)}")
    if "generated_by" in value and not (isinstance(value["generated_by"], str) and value["generated_by"]):
        errors.append(f"{label}: last_mrp_resultant.generated_by must be a non-empty string")
    if "next_burden" in value and not (value["next_burden"] is None or isinstance(value["next_burden"], str)):
        errors.append(f"{label}: last_mrp_resultant.next_burden must be a string or null")
    return errors


def _field_diagnostics_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: field_diagnostics must be an object"]
    errors: list[str] = []
    required = {"divergence_state", "curl_state"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: field_diagnostics missing field(s): {missing}")
    unknown = sorted(set(value) - required)
    if unknown:
        errors.append(f"{label}: field_diagnostics has unknown field(s): {unknown}")
    if "divergence_state" in value and value["divergence_state"] not in DIVERGENCE_STATES:
        errors.append(f"{label}: field_diagnostics.divergence_state must be one of {sorted(DIVERGENCE_STATES)}")
    if "curl_state" in value and value["curl_state"] not in CURL_STATES:
        errors.append(f"{label}: field_diagnostics.curl_state must be one of {sorted(CURL_STATES)}")
    return errors


def _current_owner_route_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: current_owner_route must be an object"]
    errors: list[str] = []
    required = {"burden", "owner_id", "shards"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: current_owner_route missing field(s): {missing}")
    unknown = sorted(set(value) - required)
    if unknown:
        errors.append(f"{label}: current_owner_route has unknown field(s): {unknown}")
    for key in ("burden", "owner_id"):
        if key in value and not (value[key] is None or isinstance(value[key], str)):
            errors.append(f"{label}: current_owner_route.{key} must be a string or null")
    if "shards" in value:
        errors.extend(_string_array_errors(label, "current_owner_route.shards", value["shards"]))
    return errors


# ---------------------------------------------------------------------------
# Semantic invariants (single capsule)
# ---------------------------------------------------------------------------

def semantic_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: cross-field invariants a schema alone can't express."""
    errors: list[str] = []

    b_la = payload.get("B_LA")
    b_mrp = payload.get("B_MRP")
    b_total = payload.get("B_total")
    if isinstance(b_la, list) and isinstance(b_mrp, list) and isinstance(b_total, list):
        errors.extend(union_errors(label, b_la, b_mrp, b_total))

    current_burden = payload.get("current_burden")
    if isinstance(b_total, list) and isinstance(current_burden, str) and current_burden:
        if current_burden not in b_total:
            last_terminal = payload.get("last_terminal") or {}
            is_terminal = isinstance(last_terminal, dict) and last_terminal.get("burden") == current_burden
            if not is_terminal:
                errors.append(
                    f"{label}: current_burden {current_burden!r} is not in B_total and is not "
                    "the explicit last_terminal burden"
                )

    next_burden = payload.get("next_burden")
    if isinstance(b_total, list) and isinstance(next_burden, str) and next_burden:
        if next_burden not in b_total:
            terminal_states = payload.get("terminal_states") or {}
            explicitly_terminal = isinstance(terminal_states, dict) and next_burden in terminal_states
            if not explicitly_terminal:
                errors.append(f"{label}: next_burden {next_burden!r} is not in B_total or explicitly terminal")

    errors.extend(mrp_provenance_errors(label, payload))
    errors.extend(coverage_complete_errors(label, payload))
    errors.extend(partial_hold_errors(label, payload))
    errors.extend(output_artifact_errors(label, payload))

    return errors


def union_errors(label: str, b_la: list[Any], b_mrp: list[Any], b_total: list[Any]) -> list[str]:
    """Pure core: B_total must equal the order-preserving union of B_LA and
    B_MRP with no duplicates (B_LA entries first in their order, then any
    B_MRP entries not already present, in their order)."""
    errors: list[str] = []
    if len(set(b_la)) != len(b_la):
        errors.append(f"{label}: B_LA contains duplicate entries")
    if len(set(b_mrp)) != len(b_mrp):
        errors.append(f"{label}: B_MRP contains duplicate entries")
    if len(set(b_total)) != len(b_total):
        errors.append(f"{label}: B_total contains duplicate entries")

    expected: list[Any] = []
    seen: set[Any] = set()
    for burden in list(b_la) + list(b_mrp):
        if burden not in seen:
            expected.append(burden)
            seen.add(burden)
    if b_total != expected:
        errors.append(
            f"{label}: B_total {b_total!r} is not the order-preserving union of B_LA and B_MRP "
            f"(expected {expected!r})"
        )
    return errors


def mrp_provenance_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: every B_MRP entry must have MRP provenance -- either a
    matching completed_acts entry (via body_ref burden prefix) whose act
    chain is backed by a generated_burden_instantiation resultant, or the
    capsule's own last_mrp_resultant naming it via generated_by/next_burden
    with route_result_type generated_burden_instantiation. Generated burdens
    are created ONLY by MRP, never predeclared."""
    b_mrp = payload.get("B_MRP")
    if not isinstance(b_mrp, list):
        return []

    errors: list[str] = []
    last_mrp = payload.get("last_mrp_resultant") or {}
    provenanced: set[str] = set()
    if isinstance(last_mrp, dict) and last_mrp.get("route_result_type") == "generated_burden_instantiation":
        for key in ("generated_by", "next_burden"):
            value = last_mrp.get(key)
            if isinstance(value, str) and value:
                provenanced.add(value)
        source = last_mrp.get("source")
        if isinstance(source, str) and source:
            provenanced.add(source)

    completed_acts = payload.get("completed_acts")
    if isinstance(completed_acts, list):
        for entry in completed_acts:
            if not isinstance(entry, dict):
                continue
            body_ref = entry.get("body_ref")
            if not isinstance(body_ref, str):
                continue
            burden_id = burden_id_from_body_ref(body_ref)
            if burden_id:
                provenanced.add(burden_id)
                provenanced.add(body_ref)

    for burden in b_mrp:
        if burden in provenanced:
            continue
        errors.append(
            f"{label}: generated burden {burden!r} in B_MRP has no MRP provenance "
            "(no matching completed_acts entry and no generated_burden_instantiation "
            "last_mrp_resultant naming it); generated burdens must be created only by MRP"
        )
    return errors


def burden_id_from_body_ref(body_ref: str) -> str:
    match = re.match(rf"^[{SUPERSCRIPT_DIGITS}]*(B[0-9]+)", body_ref)
    return match.group(1) if match else ""


def coverage_complete_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: coverage_complete=true requires held_set_H empty AND all
    B_total burdens present in terminal_states with a closed state. False
    coverage claims are a fail, not a warning."""
    if payload.get("coverage_complete") is not True:
        return []
    errors: list[str] = []
    held = payload.get("held_set_H")
    if isinstance(held, list) and held:
        errors.append(f"{label}: coverage_complete=true but held_set_H is non-empty (false coverage)")

    b_total = payload.get("B_total")
    terminal_states = payload.get("terminal_states")
    if isinstance(b_total, list) and isinstance(terminal_states, dict):
        for burden in b_total:
            state = terminal_states.get(burden)
            if state is None:
                errors.append(
                    f"{label}: coverage_complete=true but burden {burden!r} has no terminal_states entry "
                    "(false coverage)"
                )
            elif not is_closed_state(state):
                errors.append(
                    f"{label}: coverage_complete=true but burden {burden!r} terminal state {state!r} "
                    "is not closed (false coverage)"
                )
    return errors


def is_closed_state(state: Any) -> bool:
    if not isinstance(state, str):
        return False
    lowered = state.lower()
    return any(marker in lowered for marker in CLOSED_TERMINAL_MARKERS)


def partial_hold_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: hold_partial/PARTIAL states require next_required_action
    non-empty."""
    errors: list[str] = []
    is_partial = payload.get("route_result_type") == "hold_partial" or payload.get("coverage_complete") is False
    if not is_partial:
        return errors
    action = payload.get("next_required_action")
    if not (isinstance(action, str) and action.strip()):
        errors.append(
            f"{label}: coverage_complete=false/hold_partial requires a non-empty next_required_action"
        )
    return errors


def output_artifact_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: when output_artifact_path is set, output_sha256 must be
    present (non-null, non-empty) and output_offset_bytes >= 0 (schema already
    enforces >=0 when present as int; here we enforce the presence coupling)."""
    errors: list[str] = []
    path = payload.get("output_artifact_path")
    if path:
        sha = payload.get("output_sha256")
        if not (isinstance(sha, str) and sha):
            errors.append(f"{label}: output_artifact_path is set but output_sha256 is missing/empty")
        offset = payload.get("output_offset_bytes")
        if not (isinstance(offset, int) and not isinstance(offset, bool) and offset >= 0):
            errors.append(f"{label}: output_artifact_path is set but output_offset_bytes is missing/invalid")
    return errors


def capsule_size_errors(label: str, raw_bytes: bytes) -> tuple[list[str], list[str]]:
    """Return (warnings, failures) for capsule byte-size discipline."""
    size = len(raw_bytes)
    warnings: list[str] = []
    failures: list[str] = []
    if size > FAIL_BYTES:
        failures.append(f"{label}: capsule is {size} bytes, exceeds hard cap {FAIL_BYTES} bytes")
    elif size > WARN_BYTES:
        warnings.append(f"{label}: capsule is {size} bytes, exceeds warning threshold {WARN_BYTES} bytes")
    return warnings, failures


def validate_capsule_payload(label: str, payload: Any, schema: dict[str, Any]) -> list[str]:
    errors = structural_errors(label, payload, schema)
    if isinstance(payload, dict) and not errors:
        errors.extend(semantic_errors(label, payload))
    elif isinstance(payload, dict):
        # Still run semantic checks even with minor structural issues elsewhere,
        # as long as the core ledger fields are usable, to surface as many
        # independent problems as possible in one pass.
        core_present = all(key in payload for key in ("B_LA", "B_MRP", "B_total"))
        if core_present:
            errors.extend(semantic_errors(label, payload))
    return errors


def validate_capsule_file(path: Path, schema: dict[str, Any]) -> list[str]:
    payload, errors = load_json(path)
    if errors:
        return errors
    label = rel(path)
    errors = validate_capsule_payload(label, payload, schema)
    raw_bytes = path.read_bytes()
    warnings, failures = capsule_size_errors(label, raw_bytes)
    for warning in warnings:
        print(f"  WARNING: {warning}")
    errors.extend(failures)
    return errors


# ---------------------------------------------------------------------------
# Replay (ordered capsule sequence + artifact.md)
# ---------------------------------------------------------------------------

CAPSULE_NAME_RE = re.compile(r"^capsule-(\d+)\.json$")


def discover_capsule_sequence(directory: Path) -> list[Path]:
    entries = []
    for path in sorted(directory.glob("capsule-*.json")):
        match = CAPSULE_NAME_RE.match(path.name)
        if match:
            entries.append((int(match.group(1)), path))
    entries.sort(key=lambda item: item[0])
    return [path for _, path in entries]


def replay_errors(directory: Path, schema: dict[str, Any]) -> list[str]:
    artifact_path = directory / "artifact.md"
    capsule_paths = discover_capsule_sequence(directory)

    if not capsule_paths:
        return [f"{rel(directory)}: no capsule-NNN.json files found"]
    if not artifact_path.is_file():
        return [f"{rel(directory)}: missing artifact.md"]

    artifact_bytes = artifact_path.read_bytes()
    artifact_text = artifact_bytes.decode("utf-8", errors="replace")

    capsules: list[dict[str, Any]] = []
    for index, path in enumerate(capsule_paths, start=1):
        payload, load_errs = load_json(path)
        if load_errs:
            return [f"{rel(directory)}: capsule index {index} ({rel(path)}): " + "; ".join(load_errs)]
        errs = validate_capsule_file(path, schema)
        if errs:
            return [f"{rel(directory)}: capsule index {index} ({rel(path)}): " + "; ".join(errs)]
        capsules.append(payload)

    errors = replay_sequence_errors(rel(directory), capsules, artifact_text, artifact_bytes)
    return errors


def replay_sequence_errors(
    label: str,
    capsules: list[dict[str, Any]],
    artifact_text: str,
    artifact_bytes: bytes,
) -> list[str]:
    """Pure core: cross-capsule replay invariants over an already-validated
    ordered capsule sequence. Fails with the earliest offending capsule index
    (1-based) + reason, per the mission's fail-fast contract."""
    if not capsules:
        return [f"{label}: empty capsule sequence"]

    case_id = capsules[0].get("case_id")
    fingerprint = capsules[0].get("input_fingerprint")

    prev_offset = -1
    prev_stage_index = -1
    prev_b_la: list[Any] = []
    prev_b_mrp: list[Any] = []
    prev_acts: list[Any] = []

    for index, capsule in enumerate(capsules, start=1):
        if capsule.get("case_id") != case_id:
            return [f"{label}: capsule index {index}: case_id drift ({capsule.get('case_id')!r} != {case_id!r})"]
        if capsule.get("input_fingerprint") != fingerprint:
            return [
                f"{label}: capsule index {index}: input_fingerprint drift "
                f"({capsule.get('input_fingerprint')!r} != {fingerprint!r})"
            ]

        stage = capsule.get("stage")
        stage_index = STAGE_INDEX.get(stage, -1)
        if stage_index < prev_stage_index:
            return [
                f"{label}: capsule index {index}: stage {stage!r} moves backward "
                f"(previous stage index {prev_stage_index})"
            ]
        prev_stage_index = stage_index

        offset = capsule.get("output_offset_bytes")
        if not isinstance(offset, int) or offset < prev_offset:
            return [
                f"{label}: capsule index {index}: output_offset_bytes {offset!r} is not "
                f"monotonic non-decreasing (previous {prev_offset})"
            ]
        prev_offset = offset

        b_la = capsule.get("B_LA") or []
        missing_la = [b for b in prev_b_la if b not in b_la]
        if missing_la:
            return [
                f"{label}: capsule index {index}: B_LA shrank; missing burden(s) {missing_la} "
                "present in a prior capsule (anti-slimming violation)"
            ]
        prev_b_la = list(b_la)

        b_mrp = capsule.get("B_MRP") or []
        if len(b_mrp) < len(prev_b_mrp) or b_mrp[: len(prev_b_mrp)] != prev_b_mrp:
            return [
                f"{label}: capsule index {index}: B_MRP is not append-only "
                f"(previous {prev_b_mrp!r}, current {b_mrp!r})"
            ]
        prev_b_mrp = list(b_mrp)

        acts = capsule.get("completed_acts") or []
        if len(acts) < len(prev_acts) or acts[: len(prev_acts)] != prev_acts:
            return [
                f"{label}: capsule index {index}: completed_acts is not append-only "
                "(earlier entries must be preserved verbatim)"
            ]
        prev_acts = list(acts)

        for entry in acts:
            body_ref = entry.get("body_ref") if isinstance(entry, dict) else None
            if isinstance(body_ref, str) and body_ref not in artifact_text:
                return [
                    f"{label}: capsule index {index}: completed_acts body_ref {body_ref!r} "
                    "does not appear in artifact.md (capsule-artifact parity violation)"
                ]

        terminal_states = capsule.get("terminal_states") or {}
        if isinstance(terminal_states, dict):
            for burden, state in terminal_states.items():
                if isinstance(state, str) and "land" in state.lower():
                    land_token = f"Land({burden})"
                    if land_token not in artifact_text:
                        return [
                            f"{label}: capsule index {index}: terminal_states burden {burden!r} "
                            f"marked Land but {land_token!r} does not appear in artifact.md"
                        ]

    final = capsules[-1]
    final_offset = final.get("output_offset_bytes")
    if final_offset != len(artifact_bytes):
        return [
            f"{label}: capsule index {len(capsules)}: final output_offset_bytes {final_offset} "
            f"!= len(artifact.md bytes) {len(artifact_bytes)}"
        ]
    actual_sha = hashlib.sha256(artifact_bytes).hexdigest()
    final_sha = final.get("output_sha256")
    if final_sha != actual_sha:
        return [
            f"{label}: capsule index {len(capsules)}: final output_sha256 {final_sha!r} "
            f"!= sha256(artifact.md) {actual_sha!r}"
        ]

    return []


# ---------------------------------------------------------------------------
# CLI entrypoints
# ---------------------------------------------------------------------------

def run_capsule(path: Path) -> int:
    schema = load_schema()
    errors = validate_capsule_file(path, schema)
    if errors:
        print(f"state-capsule --capsule {rel(path)}: FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"state-capsule --capsule {rel(path)}: PASS")
    return 0


def run_replay(directory: Path) -> int:
    schema = load_schema()
    errors = replay_errors(directory, schema)
    if errors:
        print(f"state-capsule --replay {rel(directory)}: FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"state-capsule --replay {rel(directory)}: PASS")
    return 0


# ---------------------------------------------------------------------------
# Self-test: embedded pure-core cases + fixture directory cases
# ---------------------------------------------------------------------------

def _base_capsule(**overrides: Any) -> dict[str, Any]:
    capsule: dict[str, Any] = {
        "schema": SCHEMA_CONST,
        "case_id": "case-001",
        "input_fingerprint": "sha256:" + ("a" * 64),
        "stage": "04",
        "n_frame": {"selected": "authority-order", "held_candidates": []},
        "live_registers": ["N", "m", "tau", "sigma"],
        "register_state": {},
        "B_LA": ["B1", "B2"],
        "B_MRP": [],
        "B_total": ["B1", "B2"],
        "current_burden": "B1",
        "held_set_H": [],
        "completed_acts": [],
        "last_terminal": {"burden": None, "state": None},
        "last_delta": None,
        "last_mrp_resultant": {"source": None, "route_result_type": "none"},
        "route_result_type": "none",
        "field_diagnostics": {"divergence_state": "neutral", "curl_state": "null-state"},
        "transport": "chat",
        "terminal_states": {},
        "next_burden": "B2",
        "current_owner_route": {"burden": "B1", "owner_id": "M3", "shards": []},
        "coverage_complete": False,
        "next_required_action": "activate B1",
        "output_artifact_path": None,
        "output_sha256": None,
        "output_offset_bytes": 0,
        "cold_law_refs_used": [],
        "shards_loaded": [],
    }
    capsule.update(overrides)
    return capsule


def embedded_self_test_cases() -> list[tuple[str, bool]]:
    schema = load_schema()
    cases: list[tuple[str, bool]] = []

    good = _base_capsule()
    cases.append(("valid minimal capsule passes", validate_capsule_payload("t", good, schema) == []))

    missing_field = dict(good)
    del missing_field["stage"]
    cases.append((
        "missing required field fails",
        any("missing required" in e for e in structural_errors("t", missing_field, schema)),
    ))

    extra_field = dict(good)
    extra_field["bogus_extra_field"] = 1
    cases.append((
        "unknown top-level field fails",
        any("unknown top-level" in e for e in structural_errors("t", extra_field, schema)),
    ))

    bad_schema_const = dict(good)
    bad_schema_const["schema"] = "wrong-v1"
    cases.append((
        "wrong schema const fails",
        any("schema must be" in e for e in structural_errors("t", bad_schema_const, schema)),
    ))

    bad_fp = dict(good)
    bad_fp["input_fingerprint"] = "not-a-fingerprint"
    cases.append((
        "malformed input_fingerprint fails",
        any("input_fingerprint" in e for e in structural_errors("t", bad_fp, schema)),
    ))

    # B_total union invariant
    cases.append((
        "B_total union ok",
        union_errors("t", ["B1", "B2"], ["B3"], ["B1", "B2", "B3"]) == [],
    ))
    cases.append((
        "B_total union mismatch fails",
        any("not the order-preserving union" in e for e in union_errors("t", ["B1", "B2"], ["B3"], ["B1", "B3", "B2"])),
    ))
    cases.append((
        "B_total duplicate fails",
        any("duplicate" in e for e in union_errors("t", ["B1"], [], ["B1", "B1"])),
    ))

    # current_burden / next_burden membership
    bad_current = _base_capsule(current_burden="B9")
    cases.append((
        "current_burden outside B_total fails",
        any("current_burden" in e for e in semantic_errors("t", bad_current)),
    ))
    ok_terminal_current = _base_capsule(
        current_burden="B9", last_terminal={"burden": "B9", "state": "Land(B9)"}
    )
    cases.append((
        "current_burden matching explicit last_terminal passes",
        not any("current_burden" in e for e in semantic_errors("t", ok_terminal_current)),
    ))

    # MRP provenance
    no_provenance = _base_capsule(B_MRP=["B7"], B_total=["B1", "B2", "B7"])
    cases.append((
        "generated burden without MRP provenance fails",
        any("no MRP provenance" in e for e in mrp_provenance_errors("t", no_provenance)),
    ))
    with_provenance = _base_capsule(
        B_MRP=["B7"],
        B_total=["B1", "B2", "B7"],
        last_mrp_resultant={
            "source": "B2",
            "route_result_type": "generated_burden_instantiation",
            "generated_by": "B2",
            "next_burden": "B7",
        },
    )
    cases.append((
        "generated burden with last_mrp_resultant provenance passes",
        mrp_provenance_errors("t", with_provenance) == [],
    ))
    with_act_provenance = _base_capsule(
        B_MRP=["B7"],
        B_total=["B1", "B2", "B7"],
        completed_acts=[
            {
                "body_ref": "B7_1",
                "owner_id": "M3",
                "operation": "op",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B7)",
            }
        ],
    )
    cases.append((
        "generated burden with completed_acts provenance passes",
        mrp_provenance_errors("t", with_act_provenance) == [],
    ))

    # coverage_complete
    false_coverage_held = _base_capsule(coverage_complete=True, held_set_H=[{"burden": "B2", "reason": "r"}])
    cases.append((
        "coverage_complete=true with non-empty held_set_H fails",
        any("held_set_H" in e for e in coverage_complete_errors("t", false_coverage_held)),
    ))
    false_coverage_open = _base_capsule(
        coverage_complete=True,
        terminal_states={"B1": "Land(B1)"},
    )
    cases.append((
        "coverage_complete=true with unclosed/missing terminal burden fails",
        any("false coverage" in e for e in coverage_complete_errors("t", false_coverage_open)),
    ))
    true_coverage_ok = _base_capsule(
        coverage_complete=True,
        held_set_H=[],
        terminal_states={"B1": "Land(B1)", "B2": "Land(B2)"},
        next_required_action="",
    )
    cases.append((
        "coverage_complete=true with all closed passes",
        coverage_complete_errors("t", true_coverage_ok) == [],
    ))

    # partial hold / next_required_action
    partial_missing_action = _base_capsule(coverage_complete=False, next_required_action="")
    cases.append((
        "coverage_complete=false with empty next_required_action fails",
        any("next_required_action" in e for e in partial_hold_errors("t", partial_missing_action)),
    ))
    partial_with_action = _base_capsule(coverage_complete=False, next_required_action="resume B2")
    cases.append((
        "coverage_complete=false with non-empty next_required_action passes",
        partial_hold_errors("t", partial_with_action) == [],
    ))

    # body_ref pollution
    cases.append((
        "clean body_ref passes",
        body_ref_pollution_errors("t", "B1_1") == [],
    ))
    cases.append((
        "body_ref with bracket fails",
        any("polluted" in e for e in body_ref_pollution_errors("t", "B1[M3.op]")),
    ))
    cases.append((
        "body_ref with dot fails",
        any("polluted" in e for e in body_ref_pollution_errors("t", "B1.op")),
    ))
    cases.append((
        "unicode superscript body_ref passes",
        body_ref_pollution_errors("t", "¹B") == [] or body_ref_pollution_errors("t", "¹B1") == [],
    ))

    # output artifact coupling
    missing_sha = _base_capsule(output_artifact_path="out/artifact.md", output_sha256=None, output_offset_bytes=10)
    cases.append((
        "output_artifact_path without sha256 fails",
        any("output_sha256" in e for e in output_artifact_errors("t", missing_sha)),
    ))

    # size discipline
    warn_bytes = b"x" * (WARN_BYTES + 1)
    warnings, failures = capsule_size_errors("t", warn_bytes)
    cases.append(("capsule over warn threshold warns not fails", bool(warnings) and not failures))
    fail_bytes = b"x" * (FAIL_BYTES + 1)
    warnings2, failures2 = capsule_size_errors("t", fail_bytes)
    cases.append(("capsule over hard cap fails", bool(failures2)))

    # replay sequence invariants (pure core, synthetic)
    artifact_text = "ACT B1_1 ... Land(B1)\nACT B2_1 ... Land(B2)\n"
    artifact_bytes = artifact_text.encode("utf-8")
    cap1 = _base_capsule(
        stage="04",
        output_offset_bytes=0,
        output_artifact_path=None,
        output_sha256=None,
        completed_acts=[],
        terminal_states={},
    )
    cap2 = _base_capsule(
        stage="04",
        current_burden="B2",
        next_burden=None,
        output_offset_bytes=len(artifact_bytes),
        output_artifact_path="artifact.md",
        output_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
        completed_acts=[
            {
                "body_ref": "B1_1",
                "owner_id": "M3",
                "operation": "op",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B1)",
            },
            {
                "body_ref": "B2_1",
                "owner_id": "M3",
                "operation": "op",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B2)",
            },
        ],
        terminal_states={"B1": "Land(B1)", "B2": "Land(B2)"},
        coverage_complete=True,
        next_required_action="",
        held_set_H=[],
    )
    cases.append((
        "replay sequence: valid two-capsule sequence passes",
        replay_sequence_errors("t", [cap1, cap2], artifact_text, artifact_bytes) == [],
    ))

    cap2_bad_offset = dict(cap2)
    cap2_bad_offset["output_offset_bytes"] = 0
    cap1_high_offset = dict(cap1)
    cap1_high_offset["output_offset_bytes"] = 999
    cases.append((
        "replay sequence: non-monotonic offset fails",
        any(
            "not monotonic" in e
            for e in replay_sequence_errors("t", [cap1_high_offset, cap2_bad_offset], artifact_text, artifact_bytes)
        ),
    ))

    cap1_extra_la = dict(cap1)
    cap1_extra_la["B_LA"] = ["B1", "B2", "B3"]
    cap1_extra_la["B_total"] = ["B1", "B2", "B3"]
    cases.append((
        "replay sequence: B_LA shrink fails",
        any(
            "B_LA shrank" in e
            for e in replay_sequence_errors("t", [cap1_extra_la, cap2], artifact_text, artifact_bytes)
        ),
    ))

    return cases


def _write_fixture_capsule(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fixture_self_test(root: Path) -> tuple[list[str], int, int]:
    schema = load_schema()
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0

    valid_root = root / "valid"
    invalid_root = root / "invalid"

    # valid/multi-call-append and valid/partial-hold-resume: --replay style
    # directories (each contains capsule-NNN.json + artifact.md).
    for name in ("multi-call-append", "partial-hold-resume"):
        directory = valid_root / name
        if not directory.is_dir():
            errors.append(f"{rel(directory)}: expected valid replay fixture directory missing")
            continue
        found = replay_errors(directory, schema)
        if found:
            errors.extend(f"valid fixture {name} unexpectedly failed replay: {e}" for e in found)
        else:
            valid_checked += 1

    # valid/large-artifact-small-capsule: single-capsule fixture exercising a
    # large (>150KB) artifact with a small capsule; artifact generated inline
    # here rather than committed, per the mission's size-discipline judgment
    # call (committing 150KB is unreasonable for a fixture).
    large_dir = valid_root / "large-artifact-small-capsule"
    if not large_dir.is_dir():
        errors.append(f"{rel(large_dir)}: expected valid fixture directory missing")
    else:
        found = large_artifact_fixture_errors(large_dir, schema)
        if found:
            errors.extend(f"valid fixture large-artifact-small-capsule unexpectedly failed: {e}" for e in found)
        else:
            valid_checked += 1

    # invalid/*: each single-capsule fixture must fail for its own named reason.
    invalid_specs = {
        "offset-nonmonotonic": "not monotonic",
        "act-not-in-artifact": "does not appear in artifact.md",
        "false-coverage-complete": "false coverage",
        "generated-burden-without-mrp-provenance": "no MRP provenance",
        "partial-without-next-action": "next_required_action",
        "bla-shrinks": "B_LA shrank",
        "body-ref-polluted": "polluted",
        "artifact-hash-mismatch": "output_sha256",
    }
    for name, expected_substring in invalid_specs.items():
        directory = invalid_root / name
        if not directory.is_dir():
            errors.append(f"{rel(directory)}: expected invalid fixture directory missing")
            continue
        found = replay_errors(directory, schema) if (directory / "artifact.md").is_file() else None
        if found is None:
            capsule_path = directory / "capsule-001.json"
            if not capsule_path.is_file():
                errors.append(f"{rel(directory)}: no capsule-001.json or artifact.md found")
                continue
            found = validate_capsule_file(capsule_path, schema)
        if not found:
            errors.append(f"invalid fixture {name} unexpectedly passed")
            continue
        blob = "\n".join(found)
        if expected_substring not in blob:
            errors.append(
                f"invalid fixture {name} failed for the wrong reason; expected substring "
                f"{expected_substring!r} not found in: {blob}"
            )
        else:
            invalid_checked += 1

    return errors, valid_checked, invalid_checked


def large_artifact_fixture_errors(directory: Path, schema: dict[str, Any]) -> list[str]:
    """valid/large-artifact-small-capsule ships a small capsule.json + a
    generator note; the >150KB artifact.md is synthesized here in a temp
    location rather than committed to the repo."""
    capsule_path = directory / "capsule-001.json"
    payload, errs = load_json(capsule_path)
    if errs:
        return errs
    label = rel(capsule_path)
    errors = validate_capsule_file(capsule_path, schema)
    if errors:
        return errors

    # Synthesize a >150KB artifact body containing the recorded ACT/Land
    # tokens so capsule-artifact parity can be exercised without committing
    # a large fixture file.
    filler = ("x" * 200 + "\n") * 800  # ~160KB of filler
    acts = payload.get("completed_acts") or []
    act_lines = "\n".join(
        f"ACT {entry.get('body_ref')} :: {entry.get('land')}" for entry in acts if isinstance(entry, dict)
    )
    artifact_text = filler + act_lines + "\n"
    artifact_bytes = artifact_text.encode("utf-8")
    if len(artifact_bytes) <= 150_000:
        return [f"{label}: generated inline artifact is not >150KB ({len(artifact_bytes)} bytes)"]

    expected_offset = payload.get("output_offset_bytes")
    expected_sha = payload.get("output_sha256")
    actual_sha = hashlib.sha256(artifact_bytes).hexdigest()

    # The fixture capsule's output_offset_bytes/output_sha256 are pinned to
    # match this generator's deterministic output; if the generator ever
    # changes, the fixture capsule must be regenerated to match.
    local_errors: list[str] = []
    if expected_offset != len(artifact_bytes):
        local_errors.append(
            f"{label}: fixture output_offset_bytes {expected_offset} != generated artifact length "
            f"{len(artifact_bytes)}"
        )
    if expected_sha != actual_sha:
        local_errors.append(f"{label}: fixture output_sha256 {expected_sha!r} != generated sha256 {actual_sha!r}")
    return local_errors


def self_test() -> int:
    cases = embedded_self_test_cases()
    ok = True
    for name, passed in cases:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
        ok = ok and passed

    fixture_errors, valid_checked, invalid_checked = fixture_self_test(FIXTURE_ROOT)
    for error in fixture_errors:
        print(f"  self-test FAIL: {error}")
    ok = ok and not fixture_errors

    print(
        f"state-capsule self-test: {'PASS' if ok else 'FAIL'} "
        f"({len(cases)} embedded case(s), {valid_checked} valid fixture(s), {invalid_checked} invalid fixture(s))"
    )
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--capsule", type=Path, help="Validate a single capsule JSON file")
    group.add_argument("--replay", type=Path, help="Validate an ordered capsule sequence directory + artifact.md")
    group.add_argument("--self-test", action="store_true", help="Run embedded + fixture self-tests")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.capsule is not None:
        return run_capsule(args.capsule)
    return run_replay(args.replay)


if __name__ == "__main__":
    sys.exit(main())
