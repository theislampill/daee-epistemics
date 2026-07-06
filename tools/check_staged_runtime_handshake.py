#!/usr/bin/env python3
"""Validate no-model staged runtime handshake fixture records.

This checker does not run daee-epistemics and does not prove model behavior.
It validates explicit harness/dev stage records so future staged execution work
has a stable contract before any model-stage harness is opened.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

from closure_witness_lib import extract_embedded_field_witness, extract_field_witness, parse_closure_witness, status_head
from delta_result_vocabulary import (
    DELTA_RESULT_VOCABULARY,
    delta_result_vocabulary_errors,
    family_alias_as_executable_owner_errors,
    owner_operation_delta_result_errors,
    owner_operation_vocabulary_errors,
    route_is_held_or_partial,
    route_owner_vocabulary_errors,
    source_formal_delta_operation_errors,
    split_owner_operation_token,
)
from register_axis_contract import register_axis_errors
from stage05_basis_contract import normalize_terminal_detail_basis
import check_nla_decode_semantic_faithfulness as nla_decode
import check_mrp_route_invariants as mrp_route_invariants
import check_retained_proof_corpus as retained
import build_staged_governed_output as staged_output


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "staged-runtime-handshake"
SCHEMA = "staged-runtime-handshake-v1"
B5_SIDECAR_SCHEMA = "b5-retained-proof-mode-full-ir-sidecar-v1"
B5_SIDECAR_BUILDER = "tools/build_b5_full_ir_projection_sidecar.py"
RETAINED_BINDING_SCHEMA = "staged-runtime-retained-artifact-bindings-v1"
B5_RETAINED_SIDECAR_FIELD = "b5_full_ir_projection_sidecar"
STAGE_ORDER = [
    "stage-01-intake",
    "stage-02-layer-a-diagnostic-ir",
    "stage-03-routing-owner-gate",
    "stage-04-burden-execution-act",
    "stage-05-mrp-reread-terminal-state",
    "stage-06-field-witness-nar",
    "stage-07-release-output",
    "stage-08-verifier-sidecars",
]
HANDOFF_CHECKS: dict[tuple[str, str], set[str]] = {
    ("stage-01-intake", "stage-02-layer-a-diagnostic-ir"): {
        "input_boundary_preserved",
    },
    ("stage-02-layer-a-diagnostic-ir", "stage-03-routing-owner-gate"): {
        "burden_floor_to_route_targets",
        "n_frame_present",
        "live_registers_present",
    },
    ("stage-03-routing-owner-gate", "stage-04-burden-execution-act"): {
        "route_targets_to_act_targets",
        "owner_eligibility_backed",
    },
    ("stage-04-burden-execution-act", "stage-05-mrp-reread-terminal-state"): {
        "act_rows_present",
        "act_body_refs_present",
    },
    ("stage-05-mrp-reread-terminal-state", "stage-06-field-witness-nar"): {
        "terminal_states_to_field_witness",
        "dependency_graph_explicit",
    },
    ("stage-06-field-witness-nar", "stage-07-release-output"): {
        "field_witness_nar_convergence",
    },
    ("stage-07-release-output", "stage-08-verifier-sidecars"): {
        "release_to_verifier_sidecars",
    },
}
NO_MODEL_MODES = {"no-model-fixture", "retained-artifact-replay", "self-test-no-model"}
MODEL_MODES = {"staged-current-skill-smoke", "staged-current-skill-stage-local-smoke"}
STAGE_LOCAL_MODEL_MODE = "staged-current-skill-stage-local-smoke"
NO_MODEL_REQUIRED_NON_CLAIMS = {
    "not_model_smoke",
    "not_runtime_default_emission_proof",
    "not_arbitrary_nl_ir_parser",
    "not_package_provenance",
    "not_guaranteed_t_lang_uptake",
}
MODEL_REQUIRED_NON_CLAIMS = {
    "not_broad_model_behavior",
    "not_broad_model_matrix",
    "not_runtime_default_emission_proof",
    "not_arbitrary_nl_ir_parser",
    "not_package_provenance",
    "not_guaranteed_t_lang_uptake",
    "not_graphify_or_activegraph_proof",
}
MODEL_SCOPE_TYPES = {"focused-current-skill-smoke", "focused-current-skill-stage-smoke"}
PASS_STATUS = {"pass", "held", "partial"}
HELD_TERMINAL_STATES = {
    "hold_partial",
    "held",
    "held-with-reason",
    "partial",
    "carried-PARTIAL",
    "carried-RECURSE",
}
TERMINAL_STATE_VALUES = HELD_TERMINAL_STATES | {"landed", "discharged-as-derivative"}
STAGE05_FORBIDDEN_FIELDS = {
    "closure_claim",
    "collapse_certificate",
    "field_witness",
    "final_output",
    "grapher_html",
    "output_is_full_governed_answer",
    "proof_sidecars",
    "release_output",
    "release_terminal_states",
    "verifier_sidecars",
}
STAGE06_FORBIDDEN_FIELDS = {
    "Closing Formulation",
    "Restorative Response",
    "closure_claim",
    "closing_formulation",
    "collapse_certificate",
    "final_output",
    "grapher_html",
    "output_is_full_governed_answer",
    "proof_sidecars",
    "release_output",
    "release_terminal_states",
    "restorative_response",
    "verifier_sidecars",
}
STAGE07_FORBIDDEN_FIELDS = {
    "b5_full_ir_projection_sidecar",
    "collapse_certificate",
    "grapher_html",
    "proof_sidecars",
    "retained_promotion",
    "verifier_sidecars",
}
STAGE07_CLOSURE_CLAIMS = {"complete", "hold", "partial", "recurse"}
STAGE07_RELEASE_VALIDATION_KEYS = {
    "visible_opening_header",
    "nla_semantic_faithfulness",
    "field_witness_convergence",
    "formal_reread_state_semantics",
    "mid_reread_pressure",
    "mrp_route_invariants",
    "mrp_record_surface_parity",
    "mrp_generated_burden",
    "graph_completeness_json",
    "manual_smoke_render_contract",
    "public_burden_grouping",
    "owner_activation_ordering",
}
STAGE07_OPTIONAL_VALIDATION_KEYS: set[str] = set()
RELEASE_DIVERGENCE_STATES = {"neutral", "non-neutral"}
RELEASE_CURL_STATES = {"null", "resolved", "non-null"}
REREAD_DIVERGENCE_STATES = {"neutral", "non-neutral", "settled", "residual", "positive", "held"}
REREAD_CURL_STATES = {"null", "resolved", "non-null", "held"}
REREAD_ROUTE_RESULT_TYPES = {
    "no_new_resultant",
    "generated_burden_instantiation",
    "hold_partial",
    "partial_real",
    "partial-real",
    "genuine_dependent",
    "genuine-dependent",
    "loopbreak",
}
REREAD_ROUTES = {"STOP", "HOLD", "PARTIAL", "RECURSE", "LoopBreak", "LOOPBREAK"}
STAGE05_FORBIDDEN_PER_BURDEN_TEXT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "guaranteed T_lang uptake claim",
        re.compile(
            r"T_lang\s+guarantees|guaranteed\s+T_lang\s+uptake|"
            r"guarantees\s+interlocutor\s+uptake|guarantees\s+uptake",
            re.IGNORECASE,
        ),
    ),
]
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ACT_BODY_REF_RE = re.compile(r"\bbody_ref=([^\s:⟧]+)")
ACT_OWNER_RE = re.compile(r"^⟦ACT\s+[^\[]+\[([^\.\]]+)\.[^\]]+\]")
LAND_TARGET_RE = re.compile(r"Land\((?P<target>[^)\n]+)\)")
SUP_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
BODY_REF_BURDEN_RE = re.compile(r"^(?P<burden>[⁰¹²³⁴⁵⁶⁷⁸⁹]+B|B[1-9][0-9]*)(?:[₀₁₂₃₄₅₆₇₈₉]+|[_\.][1-9][0-9]*)?$")
ASCII_BODY_REF_RE = re.compile(r"^(?P<burden>[1-9][0-9]*)B[1-9][0-9]*$")
ACT_OWNER_OPERATION_DELTA_RE = re.compile(
    r"^⟦ACT\s+[^\[]+\[(?P<owner>[^.\]]+)\.(?P<operation>[^\]]+)\]"
    r".*?\bΔ=[^:\s]+:(?P<delta_result>[^:\s⟧]+)"
)
CANONICAL_ACT_ROW_RE = re.compile(
    r"^\s*⟦ACT\s+[^\s\[]+\[[A-Za-z][A-Za-z0-9_/\-]*\.[A-Za-z][A-Za-z0-9_.\-/]*\]"
    r"\s*::\s*π=[^\n]+?"
    r"\s*::\s*body_ref=[^\s\[:⟧]+"
    r"\s*::\s*Δ=[^:\s]+:.+?"
    r"\s*::\s*Land\([^)\n]+\)\+?⟧\s*$"
)
CANONICAL_BURDEN_ID_RE = re.compile(r"(?<![A-Za-z0-9_])B([1-9][0-9]*)(?![A-Za-z0-9_])")
MRP_GENERATED_BY_RE = re.compile(r"^MRP\((B[1-9][0-9]*)\)$")
def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def expand_records(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        raw = str(path)
        if any(char in raw for char in "*?["):
            expanded.extend(Path(match) for match in glob.glob(raw))
        elif path.is_dir():
            expanded.extend(sorted(path.glob("*.json")))
        else:
            expanded.append(path)
    return sorted(expanded)


def read_json(path: Path) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)}: JSON parse error: {exc}"]


def as_string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    if not all(isinstance(item, str) and item for item in value):
        return None
    return list(value)


def bare_burden_id_errors(label: str, field: str, values: list[str]) -> list[str]:
    errors: list[str] = []
    for index, value in enumerate(values):
        if CANONICAL_BURDEN_ID_RE.fullmatch(value) is None:
            errors.append(
                f"{label}: {field}[{index}] must be a bare canonical burden id such as B1"
            )
    return errors


def ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def canonical_burden_id_from_text(value: str, allowed_ids: set[str] | None = None) -> str | None:
    text = value.strip()
    if (allowed_ids is None or text in allowed_ids) and CANONICAL_BURDEN_ID_RE.fullmatch(text):
        return text
    matches = ordered_unique([f"B{match.group(1)}" for match in CANONICAL_BURDEN_ID_RE.finditer(text)])
    if allowed_ids is not None:
        matches = [match for match in matches if match in allowed_ids]
    return matches[0] if len(matches) == 1 else None


def canonical_burden_id(value: str) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"B[1-9][0-9]*", text):
        return text
    match = re.fullmatch(r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B", text)
    if match:
        return f"B{match.group(1).translate(SUP_DIGITS)}"
    return text


def body_ref_burden_id(value: str) -> str:
    text = str(value or "").strip()
    match = BODY_REF_BURDEN_RE.fullmatch(text)
    if match:
        return canonical_burden_id(match.group("burden"))
    match = ASCII_BODY_REF_RE.fullmatch(text)
    if match:
        return f"B{match.group('burden')}"
    return ""


def canonical_burden_ids_from_strings(values: list[str], allowed_ids: set[str] | None = None) -> list[str] | None:
    result: list[str] = []
    for value in values:
        burden_id = canonical_burden_id_from_text(value, allowed_ids)
        if burden_id is None:
            return None
        result.append(burden_id)
    return ordered_unique(result)


def canonical_stage04_act_burdens(stage04: dict[str, Any] | None) -> set[str]:
    if not isinstance(stage04, dict):
        return set()
    act_targets = set(list_field(stage04, "act_targets"))
    raw = as_string_list(stage04.get("act_burdens"))
    if raw:
        canonical = canonical_burden_ids_from_strings(raw, act_targets or None)
        if canonical is not None:
            return set(canonical)
        return set(raw)
    return act_targets


def stage05_forbidden_per_burden_text_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    return [
        f"{label}: forbidden {name}"
        for name, pattern in STAGE05_FORBIDDEN_PER_BURDEN_TEXT_PATTERNS
        if pattern.search(value)
    ]


def stage05_route_types_by_burden(stage05: dict[str, Any] | None) -> dict[str, set[str]]:
    entries = stage05.get(PER_BURDEN_REREAD_FIELD) if isinstance(stage05, dict) else None
    if not isinstance(entries, list):
        return {}
    result: dict[str, set[str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        burden_id = entry.get("burden_id")
        route_type = entry.get("route_result_type")
        if isinstance(burden_id, str) and burden_id and isinstance(route_type, str) and route_type:
            result.setdefault(burden_id, set()).add(route_type)
    return result


def stage_map(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stages = record.get("stages")
    if not isinstance(stages, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        stage_id = stage.get("id")
        if isinstance(stage_id, str):
            result[stage_id] = stage
    return result


def failed_model_prefix_order(record: dict[str, Any]) -> list[str] | None:
    """Return completed stage prefix for explicit failed model records.

    This is for historical negative-evidence records only. It lets the checker
    verify the completed prefix without pretending downstream stages exist.
    """
    if record.get("mode") not in MODEL_MODES:
        return None
    failure = record.get("failure")
    if not isinstance(failure, str) or not failure.strip():
        return None
    if record.get("stage_scope") is not None:
        return None
    stage_items = record.get("stages")
    if not isinstance(stage_items, list) or not stage_items:
        return None
    stage_ids: list[str] = []
    for stage in stage_items:
        if not isinstance(stage, dict):
            return None
        stage_id = stage.get("id")
        if not isinstance(stage_id, str):
            return None
        stage_ids.append(stage_id)
    expected = STAGE_ORDER[: len(stage_ids)]
    if stage_ids != expected or len(stage_ids) >= len(STAGE_ORDER):
        return None
    return expected


def expected_stage_order(path: Path, record: dict[str, Any]) -> tuple[list[str], list[str]]:
    label = rel(path)
    mode = record.get("mode")
    stage_scope = record.get("stage_scope")
    if stage_scope is None:
        failed_prefix = failed_model_prefix_order(record)
        if failed_prefix is not None:
            return failed_prefix, []
        return list(STAGE_ORDER), []
    errors: list[str] = []
    if mode != STAGE_LOCAL_MODEL_MODE:
        errors.append(f"{label}: stage_scope is only valid for {STAGE_LOCAL_MODEL_MODE}")
        return list(STAGE_ORDER), errors
    if not isinstance(stage_scope, dict):
        return list(STAGE_ORDER), [f"{label}: stage_scope must be an object"]
    stop_after = stage_scope.get("stop_after_stage")
    if stop_after not in STAGE_ORDER:
        return list(STAGE_ORDER), [f"{label}: stage_scope.stop_after_stage must name a known stage"]
    expected = STAGE_ORDER[: STAGE_ORDER.index(stop_after) + 1]
    if stage_scope.get("stage_count") != len(expected):
        errors.append(f"{label}: stage_scope.stage_count must match stop_after_stage prefix length")
    stop_index = STAGE_ORDER.index(stop_after)
    release_index = STAGE_ORDER.index("stage-07-release-output")
    verifier_index = STAGE_ORDER.index("stage-08-verifier-sidecars")
    if stop_index < release_index:
        if stage_scope.get("not_release_output") is not True:
            errors.append(f"{label}: stage_scope.not_release_output must be true before stage-07")
    else:
        if stage_scope.get("release_output") is not True:
            errors.append(f"{label}: stage_scope.release_output must be true for stage-07 scoped records")
        if stage_scope.get("not_release_output") is True:
            errors.append(f"{label}: stage_scope.not_release_output must not be true for stage-07 scoped records")
    if stop_index < verifier_index and stage_scope.get("not_verifier_sidecars") is not True:
        errors.append(f"{label}: stage_scope.not_verifier_sidecars must be true")
    return expected, errors


def sequence_errors(path: Path, record: dict[str, Any], stages: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    label = rel(path)
    expected_order, found = expected_stage_order(path, record)
    errors.extend(found)
    failed_prefix = failed_model_prefix_order(record)
    stage_order = record.get("stage_order")
    if stage_order != expected_order:
        if not (failed_prefix is not None and stage_order == STAGE_ORDER):
            errors.append(f"{label}: stage_order must contain the required stages exactly once and in order")

    stage_items = record.get("stages")
    if not isinstance(stage_items, list):
        return errors + [f"{label}: stages must be a list"]
    stage_ids = [stage.get("id") if isinstance(stage, dict) else None for stage in stage_items]
    if stage_ids != expected_order:
        errors.append(f"{label}: stages must contain the required stage records exactly once and in order")
    if len(stages) != len(stage_items):
        errors.append(f"{label}: stages contain duplicate or malformed ids")

    for stage_id in expected_order:
        stage = stages.get(stage_id)
        if stage is None:
            continue
        status = stage.get("status")
        if status not in PASS_STATUS and status != "fail":
            errors.append(f"{label}: {stage_id}.status must be pass, held, partial, or fail")
        for key in ("produces", "requires"):
            if as_string_list(stage.get(key)) is None:
                errors.append(f"{label}: {stage_id}.{key} must be a string list")
    return errors


def handoff_errors(path: Path, record: dict[str, Any], stages: dict[str, dict[str, Any]]) -> list[str]:
    label = rel(path)
    handoffs = record.get("handoffs")
    if not isinstance(handoffs, list):
        return [f"{label}: handoffs must be a list"]
    errors: list[str] = []
    expected_order, found = expected_stage_order(path, record)
    errors.extend(found)
    failed_prefix = failed_model_prefix_order(record)
    expected_pairs = {
        pair
        for pair in HANDOFF_CHECKS
        if pair[0] in expected_order and pair[1] in expected_order
    }
    seen: set[tuple[str, str]] = set()
    for index, handoff in enumerate(handoffs):
        hlabel = f"{label}: handoffs[{index}]"
        if not isinstance(handoff, dict):
            errors.append(f"{hlabel}: must be an object")
            continue
        source = handoff.get("from")
        target = handoff.get("to")
        pair = (source, target)
        if not isinstance(source, str) or not isinstance(target, str):
            errors.append(f"{hlabel}: from/to must be strings")
            continue
        if failed_prefix is not None and (source not in expected_order or target not in expected_order):
            continue
        if source not in stages:
            errors.append(f"{hlabel}: from references unknown stage {source!r}")
        if target not in stages:
            errors.append(f"{hlabel}: to references unknown stage {target!r}")
        seen.add(pair)
        checks = as_string_list(handoff.get("checks"))
        if checks is None:
            errors.append(f"{hlabel}: checks must be a string list")
            continue
        expected = HANDOFF_CHECKS.get(pair)
        if expected is None:
            errors.append(f"{hlabel}: handoff pair is not part of the staged contract")
            continue
        if pair not in expected_pairs:
            errors.append(f"{hlabel}: handoff pair is outside the scoped staged contract")
            continue
        missing = sorted(expected - set(checks))
        if missing and handoff.get("status") == "pass":
            errors.append(f"{hlabel}: pass handoff missing required check(s): {missing}")
        if handoff.get("status") not in PASS_STATUS and handoff.get("status") != "fail":
            errors.append(f"{hlabel}: status must be pass, held, partial, or fail")
    for pair in expected_pairs:
        if pair not in seen:
            errors.append(f"{label}: missing required handoff {pair[0]} -> {pair[1]}")
    return errors


def model_scope_errors(path: Path, record: dict[str, Any]) -> list[str]:
    label = rel(path)
    scope = record.get("model_scope")
    if not isinstance(scope, dict):
        return [f"{label}: model_scope must be an object for model-mode staged records"]
    errors: list[str] = []
    scope_type = scope.get("type")
    if scope_type not in MODEL_SCOPE_TYPES:
        errors.append(f"{label}: model_scope.type must be one of {sorted(MODEL_SCOPE_TYPES)}")
    if record.get("mode") == STAGE_LOCAL_MODEL_MODE and scope_type != "focused-current-skill-stage-smoke":
        errors.append(f"{label}: stage-local model smoke requires model_scope.type='focused-current-skill-stage-smoke'")
    if scope.get("case_count") != 1:
        errors.append(f"{label}: model_scope.case_count must be 1")
    if not isinstance(scope.get("case_family"), str) or not scope["case_family"].strip():
        errors.append(f"{label}: model_scope.case_family must be a non-empty string")
    replay_target = scope.get("retained_replay_target")
    if not isinstance(replay_target, str):
        errors.append(f"{label}: model_scope.retained_replay_target must be a relative path string")
    else:
        errors.extend(relative_path_errors(path, replay_target, "model_scope.retained_replay_target"))
        resolved = (ROOT / replay_target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{label}: model_scope.retained_replay_target must resolve inside the repo")
        if not resolved.exists():
            errors.append(f"{label}: model_scope.retained_replay_target does not exist")
    return errors


def non_claim_errors(path: Path, record: dict[str, Any]) -> list[str]:
    non_claims = record.get("non_claims")
    label = f"{rel(path)}: non_claims"
    if not isinstance(non_claims, dict):
        return [f"{label}: must be an object"]
    errors: list[str] = []
    mode = record.get("mode")
    if mode in NO_MODEL_MODES:
        required = NO_MODEL_REQUIRED_NON_CLAIMS
    elif mode in MODEL_MODES:
        required = MODEL_REQUIRED_NON_CLAIMS
        errors.extend(model_scope_errors(path, record))
        if non_claims.get("not_model_smoke") is True:
            errors.append(f"{label}.not_model_smoke: must not be true for model-mode staged records")
    else:
        errors.append(f"{rel(path)}: mode is not a recognized staged-runtime handshake mode")
        required = NO_MODEL_REQUIRED_NON_CLAIMS
    missing = sorted(required - set(non_claims))
    if missing:
        errors.append(f"{label}: missing required non-claim(s): {missing}")
    for key in sorted(required):
        if non_claims.get(key) is not True:
            errors.append(f"{label}.{key}: must be true")
    return errors


def sha_errors(path: Path, value: Any, trail: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            next_trail = f"{trail}.{key}" if trail else str(key)
            if str(key).lower().endswith("sha256") or str(key).lower() == "input_digest":
                if not isinstance(nested, str) or not SHA256_RE.fullmatch(nested):
                    errors.append(f"{rel(path)}: {next_trail} must be a valid SHA256 hex digest")
            errors.extend(sha_errors(path, nested, next_trail))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(sha_errors(path, item, f"{trail}[{index}]"))
    return errors


def relative_path_errors(path: Path, value: str, label: str) -> list[str]:
    raw = value.strip()
    if not raw:
        return [f"{rel(path)}: {label} path must be non-empty"]
    if re.match(r"^[A-Za-z]:[\\/]", raw) or raw.startswith(("/", "\\")):
        return [f"{rel(path)}: {label} path must be relative and under the repo root"]
    normalized = raw.replace("\\", "/")
    if any(part == ".." for part in normalized.split("/")):
        return [f"{rel(path)}: {label} path must not escape the repo root"]
    return []


def resolve_record_relative_path(record_path: Path, value: Any, label: str) -> tuple[Path | None, list[str]]:
    if not isinstance(value, str):
        return None, [f"{rel(record_path)}: {label} path must be a string"]
    errors = relative_path_errors(record_path, value, label)
    if errors:
        return None, errors
    resolved = (ROOT / value.replace("\\", "/")).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        return None, [f"{rel(record_path)}: {label} path must resolve inside the repo root"]
    return resolved, []


def path_reference_errors(path: Path, value: Any, trail: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            next_trail = f"{trail}.{key}" if trail else str(key)
            if str(key).lower() in {"path", "output_path"} and isinstance(nested, str):
                errors.extend(relative_path_errors(path, nested, next_trail))
            errors.extend(path_reference_errors(path, nested, next_trail))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(path_reference_errors(path, item, f"{trail}[{index}]"))
    return errors


def list_field(stage: dict[str, Any], key: str) -> list[str]:
    value = stage.get(key)
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str)]
    return []


def owner_activation_body_refs(value: Any) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    if not isinstance(value, list) or not value:
        return [], [], ["stage-06 owner_activations must be a non-empty list"]
    if all(isinstance(item, str) and item for item in value):
        return list(value), [], []
    if all(isinstance(item, dict) for item in value):
        refs: list[str] = []
        details: list[dict[str, Any]] = []
        errors: list[str] = []
        for index, item in enumerate(value):
            body_ref = item.get("body_ref")
            if not isinstance(body_ref, str) or not body_ref:
                errors.append(f"stage-06 owner_activations[{index}].body_ref must be a non-empty string")
                continue
            refs.append(body_ref)
            details.append(item)
        return refs, details, errors
    return [], [], ["stage-06 owner_activations must be all body-ref strings or all objects with body_ref"]


def register_delta_errors(label: str, value: Any) -> list[str]:
    def delta_value_errors(value_label: str, delta: Any) -> list[str]:
        if isinstance(delta, str):
            if not delta:
                return [f"{value_label} must be non-empty when string-shaped"]
            return []
        if isinstance(delta, list):
            if not delta or not all(isinstance(item, str) and item for item in delta):
                return [f"{value_label} list values must be non-empty strings"]
            return []
        return [f"{value_label} must be a string or string list"]

    if isinstance(value, dict):
        errors: list[str] = []
        for register, delta in value.items():
            if not isinstance(register, str) or not register:
                errors.append(f"{label}: stage-06 register_deltas keys must be non-empty strings")
                continue
            errors.extend(delta_value_errors(f"{label}: stage-06 register_deltas[{register!r}]", delta))
        return errors
    if isinstance(value, list):
        errors = []
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"{label}: stage-06 register_deltas[{index}] must be an object")
                continue
            register = item.get("register")
            delta = item.get("delta")
            if not isinstance(register, str) or not register:
                errors.append(f"{label}: stage-06 register_deltas[{index}].register must be a non-empty string")
            errors.extend(delta_value_errors(f"{label}: stage-06 register_deltas[{index}].delta", delta))
        return errors
    return [f"{label}: stage-06 register_deltas must be an object or list"]


def nar_object_errors(
    label: str,
    nar: Any,
    *,
    burden_floor: set[str],
    nar_burdens: set[str],
    terminal_burdens: set[str],
    expected_route_types: dict[str, set[str]] | None = None,
) -> list[str]:
    if not isinstance(nar, dict):
        return [f"{label}: stage-06 normalized activation record details must be an object"]
    errors: list[str] = []
    n_frame = nar.get("n_frame")
    canonical_n_frame = ""
    if not isinstance(n_frame, str) or not n_frame.strip():
        errors.append(f"{label}: stage-06 NAR n_frame must be a non-empty string")
    else:
        canonical_n_frame = n_frame.strip()
    n_frame_details = nar.get("n_frame_details")
    if n_frame_details is not None:
        if not isinstance(n_frame_details, dict):
            errors.append(f"{label}: stage-06 NAR n_frame_details must be an object when present")
        else:
            detail_selected = n_frame_details.get("selected")
            if detail_selected is not None:
                if not isinstance(detail_selected, str) or not detail_selected.strip():
                    errors.append(f"{label}: stage-06 NAR n_frame_details.selected must be a non-empty string when present")
                elif canonical_n_frame and detail_selected.strip() != canonical_n_frame:
                    errors.append(f"{label}: stage-06 NAR n_frame_details.selected must match canonical n_frame")
            detail_held = n_frame_details.get("held")
            held_tokens: set[str] = set()
            if detail_held is not None:
                if not isinstance(detail_held, list) or not all(isinstance(item, str) and item for item in detail_held):
                    errors.append(f"{label}: stage-06 NAR n_frame_details.held must be a string list when present")
                else:
                    held_tokens = {item.strip() for item in detail_held}
            detail_held_details = n_frame_details.get("held_details")
            if detail_held_details is not None:
                if not isinstance(detail_held_details, list):
                    errors.append(f"{label}: stage-06 NAR n_frame_details.held_details must be an object list when present")
                else:
                    for index, item in enumerate(detail_held_details):
                        if not isinstance(item, dict):
                            errors.append(
                                f"{label}: stage-06 NAR n_frame_details.held_details[{index}] must be an object"
                            )
                            continue
                        detail_frame = item.get("n_frame")
                        if not isinstance(detail_frame, str) or not detail_frame.strip():
                            errors.append(
                                f"{label}: stage-06 NAR n_frame_details.held_details[{index}].n_frame must be a non-empty string"
                            )
                        elif held_tokens and detail_frame.strip() not in held_tokens:
                            errors.append(
                                f"{label}: stage-06 NAR n_frame_details.held_details[{index}].n_frame must appear in n_frame_details.held"
                            )
                        detail_reason = item.get("hold_reason")
                        if not isinstance(detail_reason, str) or not detail_reason.strip():
                            errors.append(
                                f"{label}: stage-06 NAR n_frame_details.held_details[{index}].hold_reason must be a non-empty string"
                            )
    normalization = nar.get("normalization")
    if normalization is not None and not isinstance(normalization, dict):
        errors.append(f"{label}: stage-06 NAR normalization must be an object when present")
    live_registers = as_string_list(nar.get("live_registers"))
    if live_registers is None:
        errors.append(f"{label}: stage-06 NAR live_registers must be a string list")
    nar_floor = as_string_list(nar.get("burden_floor"))
    if nar_floor is None:
        errors.append(f"{label}: stage-06 NAR burden_floor must be a string list")
        nar_floor_set: set[str] = set()
    else:
        nar_floor_set = set(nar_floor)
        if nar_floor_set != burden_floor:
            errors.append(f"{label}: stage-06 NAR burden_floor must match stage-02 burden_floor")
    rows = nar.get("per_burden")
    row_burdens: set[str] = set()
    if not isinstance(rows, list) or not rows:
        errors.append(f"{label}: stage-06 NAR per_burden must be a non-empty object list")
    else:
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{label}: stage-06 NAR per_burden[{index}] must be an object")
                continue
            burden_id = row.get("burden_id")
            if not isinstance(burden_id, str) or not burden_id:
                errors.append(f"{label}: stage-06 NAR per_burden[{index}].burden_id must be a non-empty string")
            else:
                row_burdens.add(burden_id)
                route_type = str(row.get("mrp_route_result_type") or row.get("route_result_type") or "").strip()
                expected = (expected_route_types or {}).get(burden_id)
                if route_type and expected and route_type not in expected:
                    errors.append(
                        f"{label}: stage-06 NAR per_burden[{index}].mrp_route_result_type must match stage-05 per_burden_reread route_result_type"
                    )
            for key in ("owner_id", "operation", "terminal_state"):
                value = row.get(key)
                if value is not None and (not isinstance(value, str) or not value):
                    errors.append(f"{label}: stage-06 NAR per_burden[{index}].{key} must be a non-empty string when present")
            errors.extend(object_source_formal_errors(f"{label}: stage-06 NAR per_burden[{index}]", row))
            if "generation_depth" in row and not isinstance(row.get("generation_depth"), int):
                errors.append(f"{label}: stage-06 NAR per_burden[{index}].generation_depth must be an integer when present")
    missing_nar = sorted(nar_burdens - row_burdens)
    if missing_nar:
        errors.append(f"{label}: stage-06 NAR per_burden missing nar_burdens: {missing_nar}")
    missing_terminal = sorted(terminal_burdens - row_burdens)
    if missing_terminal:
        errors.append(f"{label}: stage-06 NAR per_burden missing terminal burden(s): {missing_terminal}")
    extra = sorted(row_burdens - (nar_burdens | terminal_burdens | burden_floor))
    if extra:
        errors.append(f"{label}: stage-06 NAR per_burden names unknown burden(s): {extra}")
    return errors


def stage06_witness_nar_errors(
    label: str,
    record: dict[str, Any],
    stage02: dict[str, Any] | None,
    stage04: dict[str, Any] | None,
    stage05: dict[str, Any] | None,
    stage06: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    forbidden = sorted(STAGE06_FORBIDDEN_FIELDS & set(stage06))
    if forbidden:
        errors.append(f"{label}: stage-06 must not emit release/final/verifier field(s): {forbidden}")

    act_body_refs = list_field(stage04 or {}, "act_body_refs")
    act_burdens = canonical_stage04_act_burdens(stage04)
    burden_floor = set(list_field(stage02 or {}, "burden_floor"))
    terminal_states = stage05.get("terminal_states") if isinstance(stage05, dict) else {}
    terminal_burdens = set(terminal_states) if isinstance(terminal_states, dict) else set()
    expected_route_types = stage05_route_types_by_burden(stage05)

    field_refs = as_string_list(stage06.get("field_witness_body_refs"))
    if field_refs is None or not field_refs:
        errors.append(f"{label}: stage-06 field_witness_body_refs must be a non-empty string list")
        field_refs = []
    elif act_body_refs and field_refs != act_body_refs:
        errors.append(f"{label}: stage-06 field_witness_body_refs must exactly match stage-04 act_body_refs")

    nar_raw = as_string_list(stage06.get("nar_burdens"))
    if nar_raw is None or not nar_raw:
        errors.append(f"{label}: stage-06 nar_burdens must be a non-empty string list")
        nar_burdens: set[str] = set()
    else:
        nar_burdens = set(nar_raw)
    missing_act = sorted(act_burdens - nar_burdens)
    if missing_act:
        errors.append(f"{label}: stage-06 nar_burdens missing ACT burden(s): {missing_act}")
    missing_terminal = sorted(terminal_burdens - nar_burdens)
    if missing_terminal:
        errors.append(f"{label}: stage-06 nar_burdens missing terminal-state burden(s): {missing_terminal}")

    owner_refs, owner_details, found = owner_activation_body_refs(stage06.get("owner_activations"))
    errors.extend(f"{label}: {error}" for error in found)
    if owner_refs and field_refs and owner_refs != field_refs:
        errors.append(f"{label}: stage-06 owner_activations must exactly mirror field_witness_body_refs")
    explicit_details = stage06.get("owner_activation_details")
    if explicit_details is not None:
        if not isinstance(explicit_details, list) or not all(isinstance(item, dict) for item in explicit_details):
            errors.append(f"{label}: stage-06 owner_activation_details must be an object list when present")
        else:
            owner_details.extend(explicit_details)
    for index, detail in enumerate(owner_details):
        body_ref = detail.get("body_ref")
        if not isinstance(body_ref, str) or not body_ref:
            errors.append(f"{label}: stage-06 owner_activation_details[{index}].body_ref must be a non-empty string")
        elif field_refs and body_ref not in field_refs:
            errors.append(f"{label}: stage-06 owner_activation_details[{index}].body_ref must appear in field_witness_body_refs")
        burden_id = detail.get("burden_id") or detail.get("target") or detail.get("source")
        if burden_id is not None:
            burden_id = nla_decode.graph_burden_id(burden_id)
            if burden_id and burden_id not in nar_burdens:
                errors.append(f"{label}: stage-06 owner_activation_details[{index}].burden_id must appear in nar_burdens")
        for key in ("owner_id", "operation"):
            value = detail.get(key)
            if value is not None and (not isinstance(value, str) or not value):
                errors.append(f"{label}: stage-06 owner_activation_details[{index}].{key} must be a non-empty string when present")
        errors.extend(object_source_formal_errors(f"{label}: stage-06 owner_activation_details[{index}]", detail))
        terminal_state = detail.get("terminal_state")
        if terminal_state is not None and terminal_state not in TERMINAL_STATE_VALUES:
            errors.append(f"{label}: stage-06 owner_activation_details[{index}].terminal_state must use a controlled terminal state")

    nar_value = stage06.get("normalized_activation_record")
    nar_details = stage06.get("normalized_activation_record_details")
    mode = record.get("mode")
    if nar_value is None:
        errors.append(f"{label}: stage-06 normalized_activation_record is required")
    elif isinstance(nar_value, bool):
        if nar_value is not True:
            errors.append(f"{label}: stage-06 normalized_activation_record boolean must be true")
        if mode in MODEL_MODES and nar_details is None:
            errors.append(f"{label}: model-mode stage-06 requires structured normalized_activation_record or normalized_activation_record_details")
    elif isinstance(nar_value, dict):
        errors.extend(
            nar_object_errors(
                label,
                nar_value,
                burden_floor=burden_floor,
                nar_burdens=nar_burdens,
                terminal_burdens=terminal_burdens,
                expected_route_types=expected_route_types,
            )
        )
    else:
        errors.append(f"{label}: stage-06 normalized_activation_record must be true or an object")
    if nar_details is not None:
        errors.extend(
            nar_object_errors(
                label,
                nar_details,
                burden_floor=burden_floor,
                nar_burdens=nar_burdens,
                terminal_burdens=terminal_burdens,
                expected_route_types=expected_route_types,
            )
        )

    if "register_deltas" not in stage06:
        if isinstance(nar_value, dict) and "register_deltas" in nar_value:
            errors.append(
                f"{label}: stage-06 register_deltas is required at top level; "
                "normalized_activation_record.register_deltas is mirror evidence only"
            )
        else:
            errors.append(f"{label}: stage-06 register_deltas is required")
    else:
        errors.extend(register_delta_errors(label, stage06.get("register_deltas")))
    return errors


def visible_governed_output_errors(label: str, output_path: Path, text: str) -> list[str]:
    errors: list[str] = []
    checks = [
        ("visible noetic-field opening/header", r"NOETIC FIELD EXECUTION|noetic-field"),
        ("compact Layer A / Diagnostic IR header", r"Layer A\b.*(DSL/IR|Diagnostic IR|Header)"),
        ("governed Layer B / burden execution surface", r"Layer B\b|Bounded Governed Response|Burden\s+\d+"),
        ("canonical ACT-readable rows", r"⟦ACT\b"),
        ("ACT body_ref tokens", r"\bbody_ref="),
        ("Land surface", r"Land\("),
        ("MRP / reread / terminal state surface", r"MRP\(|R\(H,|Mid-Reread|Terminal states"),
        ("parser-stable field_witness", r"(?m)^\s*field_witness\b"),
        ("normalized_activation_record / NAR evidence", r"normalized_activation_record|\bNAR\b"),
        ("Restorative Response", r"(?im)^\s*(?:#+\s*)?Restorative Response\b"),
        ("Closing Formulation", r"(?im)^\s*(?:#+\s*)?Closing Formulation\b"),
    ]
    for check_label, pattern in checks:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE) is None:
            errors.append(f"{label}: stage-07 output {rel(output_path)} missing {check_label}")

    witness_payload = extract_embedded_field_witness(text)
    field_witness = extract_field_witness(witness_payload)
    if re.search(r"(?m)^\s*field_witness\b", text, re.IGNORECASE | re.MULTILINE) and field_witness is None:
        errors.append(f"{label}: stage-07 output {rel(output_path)} missing parser-stable field_witness object")
    if isinstance(field_witness, dict) and not isinstance(field_witness.get("normalized_activation_record"), dict):
        errors.append(f"{label}: stage-07 output {rel(output_path)} missing structured field_witness normalized_activation_record")

    forbidden_patterns = [
        ("harness commentary", r"You are executing stage-|Validated compact stage state|Return exactly one JSON object"),
        ("package/provenance claim", r"\bpackage/provenance\b|provenance asset|release package|\.skill\b|GitHub Release"),
        ("guaranteed T_lang uptake claim", r"T_lang guarantees|guaranteed T_lang uptake|guarantees interlocutor uptake"),
        ("Graphify/ActiveGraph proof claim", r"Graphify[^.\n]{0,80}\bproof\b|ActiveGraph[^.\n]{0,80}\bproof\b"),
    ]
    for claim_label, pattern in forbidden_patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if claim_label == "Graphify/ActiveGraph proof claim":
            matches = [
                match
                for match in matches
                if not (
                    staged_output.OPTIONAL_TOOLING_PROOF_NONCLAIM_RE.search(
                        staged_output.match_sentence(text, match.start(), match.end())
                    )
                    and not staged_output.OPTIONAL_TOOLING_POSITIVE_PROOF_RE.search(
                        staged_output.match_sentence(text, match.start(), match.end())
                    )
                )
            ]
        if matches:
            errors.append(f"{label}: stage-07 output {rel(output_path)} contains forbidden {claim_label}")
    return errors


def self_test_visible_optional_tooling_nonclaims() -> list[str]:
    base_output = """NOETIC FIELD EXECUTION

## Layer A / Diagnostic IR Header
- Initial burden set: [B1]

## Layer B / Burden 1
ACT records:
⟦ACT B1_1[M7.definition-anchor] :: π=definition-pressure :: body_ref=B1_1 :: Δ=ΔB1:definition-anchored :: Land(B1)+⟧

Land(B1): definition anchored.
MRP(B1): type=no_new_resultant; graph=none; route=STOP

## Restorative Response
The response is governed and visible.

## Closing Formulation
The closure is bounded to the visible state.

field_witness
{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "normalized_activation_record": {},
  "terminal_states": {"B1": "landed"}
}
"""
    output_path = ROOT / "tests" / "staged-runtime-handshake" / "self-test-output.md"
    errors: list[str] = []
    accepted_nonclaims = {
        "stage07-optional-tooling-proof-nonclaim-does-not-claim": (
            "Boundary: T_lang does not imply guaranteed uptake; this reread records only "
            "the runtime field transition and does not claim interlocutor acceptance, "
            "package proof, Graphify proof, or ActiveGraph proof."
        ),
        "stage07-optional-tooling-proof-nonclaim-without-claiming": (
            "coverage gap: public rendering must reorient from formal explosion rhetoric "
            "to the landed burden order B1-B5 without claiming release proof, packaging, "
            "Graphify proof, or guaranteed interlocutor uptake."
        ),
    }
    for case_id, line in accepted_nonclaims.items():
        found = visible_governed_output_errors(case_id, output_path, f"{base_output}\n{line}\n")
        if found:
            errors.append(f"{case_id}: rejected optional-tooling proof nonclaim: {found}")
    positive = visible_governed_output_errors(
        "stage07-optional-tooling-positive-proof-claim",
        output_path,
        f"{base_output}\nGraphify proof confirms retained closure.\n",
    )
    if not any("Graphify/ActiveGraph proof claim" in error for error in positive):
        errors.append("stage07-optional-tooling-positive-proof-claim: accepted forbidden proof claim")
    return errors


def release_output_path_and_text(
    record_path: Path,
    stage07: dict[str, Any],
) -> tuple[Path | None, str | None, list[str]]:
    label = "stage-07 release_output"
    release_output = stage07.get("release_output")
    if not isinstance(release_output, dict):
        return None, None, [f"{rel(record_path)}: {label} must be an object"]
    errors: list[str] = []
    missing = sorted({"path", "sha256"} - set(release_output))
    if missing:
        errors.append(f"{rel(record_path)}: {label} missing field(s): {missing}")
    output_path, found = resolve_record_relative_path(record_path, release_output.get("path"), label)
    errors.extend(found)
    if output_path is None:
        return None, None, errors
    if not output_path.exists():
        errors.append(f"{rel(record_path)}: {label}.path {rel(output_path)} missing")
        return output_path, None, errors
    expected_hash = release_output.get("sha256")
    if isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash):
        actual_hash = retained.sha256_file(output_path)
        if expected_hash.upper() != actual_hash:
            errors.append(f"{rel(record_path)}: {label}.sha256 expected {expected_hash.upper()} but found {actual_hash}")
    text = output_path.read_text(encoding="utf-8", errors="replace")
    return output_path, text, errors


def field_witness_coverage_status(field_witness: dict[str, Any] | None, key: str) -> str:
    if not isinstance(field_witness, dict):
        return ""
    coverage = field_witness.get("coverage_proof")
    if not isinstance(coverage, dict):
        return ""
    value = coverage.get(key)
    if not isinstance(value, str):
        return ""
    return status_head(value)


def release_field_diagnostics_from_text(output_text: str) -> dict[str, Any]:
    witness = parse_closure_witness(output_text)
    field_witness = extract_embedded_field_witness(output_text)
    visible = {
        "divergence_check": status_head(witness.divergence) if witness is not None else "",
        "curl_check": status_head(witness.curl) if witness is not None else "",
    }
    field_witness_coverage = {
        "divergence_check": field_witness_coverage_status(field_witness, "divergence_check"),
        "curl_check": field_witness_coverage_status(field_witness, "curl_check"),
    }
    matches = (
        visible["divergence_check"] in RELEASE_DIVERGENCE_STATES
        and visible["curl_check"] in RELEASE_CURL_STATES
        and visible == field_witness_coverage
    )
    return {
        "visible": visible,
        "field_witness_coverage": field_witness_coverage,
        "matches": matches,
    }


def release_field_diagnostics_errors(label: str, diagnostics: Any, output_text: str | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(diagnostics, dict):
        return [f"{label}: stage-07 release_field_diagnostics must be an object"]
    visible = diagnostics.get("visible")
    field_witness_coverage = diagnostics.get("field_witness_coverage")
    if not isinstance(visible, dict):
        errors.append(f"{label}: stage-07 release_field_diagnostics.visible must be an object")
        visible = {}
    if not isinstance(field_witness_coverage, dict):
        errors.append(f"{label}: stage-07 release_field_diagnostics.field_witness_coverage must be an object")
        field_witness_coverage = {}
    visible_divergence = visible.get("divergence_check")
    visible_curl = visible.get("curl_check")
    coverage_divergence = field_witness_coverage.get("divergence_check")
    coverage_curl = field_witness_coverage.get("curl_check")
    if visible_divergence not in RELEASE_DIVERGENCE_STATES:
        errors.append(
            f"{label}: stage-07 release_field_diagnostics.visible.divergence_check must be one of "
            f"{sorted(RELEASE_DIVERGENCE_STATES)}"
        )
    if coverage_divergence not in RELEASE_DIVERGENCE_STATES:
        errors.append(
            f"{label}: stage-07 release_field_diagnostics.field_witness_coverage.divergence_check must be one of "
            f"{sorted(RELEASE_DIVERGENCE_STATES)}"
        )
    if visible_curl not in RELEASE_CURL_STATES:
        errors.append(
            f"{label}: stage-07 release_field_diagnostics.visible.curl_check must be one of "
            f"{sorted(RELEASE_CURL_STATES)}"
        )
    if coverage_curl not in RELEASE_CURL_STATES:
        errors.append(
            f"{label}: stage-07 release_field_diagnostics.field_witness_coverage.curl_check must be one of "
            f"{sorted(RELEASE_CURL_STATES)}"
        )
    computed_matches = visible == field_witness_coverage and not errors
    if diagnostics.get("matches") is not computed_matches:
        errors.append(f"{label}: stage-07 release_field_diagnostics.matches must equal checker-computed agreement")
    if not computed_matches:
        errors.append(f"{label}: stage-07 release_field_diagnostics visible and field_witness_coverage must agree")
    if output_text is not None:
        actual = release_field_diagnostics_from_text(output_text)
        if diagnostics != actual:
            errors.append(
                f"{label}: stage-07 release_field_diagnostics must match checker extraction from release_output"
            )
    return errors


def stage07_release_errors(
    label: str,
    record_path: Path,
    record: dict[str, Any],
    stage05: dict[str, Any] | None,
    stage07: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    forbidden = sorted(STAGE07_FORBIDDEN_FIELDS & set(stage07))
    if forbidden:
        errors.append(f"{label}: stage-07 must not emit verifier/sidecar/provenance field(s): {forbidden}")

    output_path, output_text, found = release_output_path_and_text(record_path, stage07)
    errors.extend(found)
    visible_errors: list[str] = []
    if output_path is not None and output_text is not None:
        visible_errors = visible_governed_output_errors(label, output_path, output_text)
        visible_errors.extend(
            f"{label}: stage-07 public projection integrity: {error}"
            for error in mrp_route_invariants.check_text(output_path, output_text)
        )

    release_terminal_states = stage07.get("release_terminal_states")
    if not isinstance(release_terminal_states, dict) or not release_terminal_states:
        errors.append(f"{label}: stage-07 release_terminal_states must be a non-empty object")
    terminal_states = stage05.get("terminal_states") if isinstance(stage05, dict) else None
    if isinstance(terminal_states, dict) and terminal_states != release_terminal_states:
        errors.append(f"{label}: stage-07 release_terminal_states must match stage-05 terminal_states")

    closure_claim = stage07.get("closure_claim")
    if closure_claim not in STAGE07_CLOSURE_CLAIMS:
        errors.append(f"{label}: stage-07 closure_claim must be one of {sorted(STAGE07_CLOSURE_CLAIMS)}")
    held_or_partial = False
    if isinstance(terminal_states, dict):
        held_or_partial = any(str(value) in HELD_TERMINAL_STATES for value in terminal_states.values())
    if held_or_partial and closure_claim == "complete":
        errors.append(f"{label}: stage-07 closure_claim must not be complete when Stage 05 held/partial states exist")

    full_answer = stage07.get("output_is_full_governed_answer")
    if full_answer is not True:
        errors.append(f"{label}: stage-07 output_is_full_governed_answer must be true for a passing Stage 07 release-output record")
    elif visible_errors:
        errors.extend(visible_errors)

    validation = stage07.get("release_validation")
    mode = record.get("mode")
    if mode in MODEL_MODES and not isinstance(validation, dict):
        errors.append(f"{label}: model-mode stage-07 requires release_validation object")
    if validation is not None:
        if not isinstance(validation, dict):
            errors.append(f"{label}: stage-07 release_validation must be an object when present")
        else:
            required = STAGE07_RELEASE_VALIDATION_KEYS
            missing = sorted(required - set(validation))
            if missing:
                errors.append(f"{label}: stage-07 release_validation missing required key(s): {missing}")
            allowed = required | STAGE07_OPTIONAL_VALIDATION_KEYS
            unknown = sorted(set(validation) - allowed)
            if unknown:
                errors.append(f"{label}: stage-07 release_validation contains unknown key(s): {unknown}")
            for key, value in validation.items():
                if value != "pass":
                    errors.append(f"{label}: stage-07 release_validation.{key} must be 'pass'")
    release_field_diagnostics = stage07.get("release_field_diagnostics")
    if mode in MODEL_MODES and release_field_diagnostics is None:
        errors.append(f"{label}: model-mode stage-07 requires release_field_diagnostics object")
    if release_field_diagnostics is not None:
        errors.extend(release_field_diagnostics_errors(label, release_field_diagnostics, output_text))
    return errors


def generated_burden_ids(stage05: dict[str, Any]) -> tuple[set[str], list[str]]:
    raw = stage05.get("generated_burdens", [])
    if raw in (None, []):
        return set(), []
    errors: list[str] = []
    if not isinstance(raw, list):
        return set(), ["stage-05 generated_burdens must be a list when present"]
    result: set[str] = set()
    for index, item in enumerate(raw):
        if isinstance(item, str) and item:
            result.add(item)
            errors.append(
                f"stage-05 generated_burdens[{index}] must be an object with generated_by provenance"
            )
            continue
        if isinstance(item, dict):
            burden_id = item.get("id") or item.get("burden_id")
            if isinstance(burden_id, str) and burden_id:
                result.add(burden_id)
                continue
        errors.append(f"stage-05 generated_burdens[{index}] must be an object with id/burden_id and generated_by")
    return result, errors


def generated_burden_parent_map(stage05: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    raw = stage05.get("generated_burdens", [])
    if raw in (None, []):
        return {}, []
    if not isinstance(raw, list):
        return {}, []
    parents: dict[str, str] = {}
    errors: list[str] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        burden_id = item.get("id") or item.get("burden_id")
        if not isinstance(burden_id, str) or not burden_id:
            continue
        generated_by = item.get("generated_by")
        if not isinstance(generated_by, str) or not generated_by.strip():
            errors.append(f"stage-05 generated_burdens[{index}].generated_by is required")
            continue
        match = MRP_GENERATED_BY_RE.fullmatch(generated_by.strip())
        if not match:
            errors.append(
                f"stage-05 generated_burdens[{index}].generated_by must use MRP(Bn) provenance"
            )
            continue
        parents[burden_id] = match.group(1)
    return parents, errors


def unresolved_burden_ids(stage05: dict[str, Any], proof: Any) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    raw = stage05.get("unresolved_burdens", [])
    if raw in (None, []):
        result: set[str] = set()
    elif isinstance(raw, list) and all(isinstance(item, str) and item for item in raw):
        result = set(raw)
    else:
        result = set()
        errors.append("stage-05 unresolved_burdens must be a string list when present")
    if isinstance(proof, dict):
        proof_raw = proof.get("unresolved_burdens", [])
        if proof_raw in (None, []):
            pass
        elif isinstance(proof_raw, list) and all(isinstance(item, str) and item for item in proof_raw):
            result.update(proof_raw)
        else:
            errors.append("stage-05 no_new_resultant_proof.unresolved_burdens must be a string list when present")
    return result, errors


def dependency_graph_edge_endpoints(edge: Any) -> tuple[str | None, str | None, str | None]:
    if isinstance(edge, str):
        if "->" in edge:
            source, target = edge.split("->", 1)
            return source.strip(), target.strip(), None
        return None, None, "string edge must use 'from->to' form"
    if isinstance(edge, dict):
        source = edge.get("from") or edge.get("source")
        target = edge.get("to") or edge.get("target")
        if isinstance(source, str) and isinstance(target, str) and source and target:
            return source, target, None
        return None, None, "object edge must expose string from/to or source/target"
    return None, None, "edge must be a string or object"


PER_BURDEN_REREAD_FIELD = "per_burden_reread"
PER_BURDEN_PRESSURE_KEYS = {
    "freeze-landed-move",
    "dependency-tug",
    "hidden-framework-recoil",
    "entailment-pressure",
    "doubt-churn-guard",
    "reorientation-reminder",
}
PER_BURDEN_FINDINGS = {
    "stable",
    "genuine-dependent",
    "partial-real",
    "hidden-framework-recoil",
    "doubt-churn",
    "reorientation",
}
PER_BURDEN_ROUTE_RESULT_TYPES = {
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "loopbreak",
    "hold_partial",
}
PER_BURDEN_ROUTES = {"STOP", "HOLD", "RECURSE", "LoopBreak(∇×T)"}
PER_BURDEN_PREEMPTION_BASES = {"none", "graph-bound", "commitment-bound", "framework-bound"}
PER_BURDEN_BOUNDARY_PREFIX = "T_lang does not imply guaranteed uptake"
PER_BURDEN_REQUIRED_STRING_FIELDS = (
    "burden_id",
    "target",
    "reread",
    "landed_delta",
    "route_gradient",
    "finding",
    "route_result_type",
    "mrp_resultant",
    "graph_delta",
    "preemption_basis",
    "route",
    "boundary",
)


def per_burden_reread_errors(label: str, stage05: dict[str, Any]) -> list[str]:
    """Validate optional stage-05 per_burden_reread entries when present.

    Each entry mirrors one visible per-burden [Mid-Reread Pressure] block so
    the public projection can be checked against producer state instead of
    letting per-burden reread structure live only in machine sidecars. This is
    shape/vocabulary validation; producer adoption in the staged runner is the
    follow-up no-model slice.
    """
    if PER_BURDEN_REREAD_FIELD not in stage05:
        return []
    entries = stage05.get(PER_BURDEN_REREAD_FIELD)
    prefix = f"{label}: stage-05 {PER_BURDEN_REREAD_FIELD}"
    if not isinstance(entries, list) or not entries:
        return [f"{prefix} must be a non-empty list when present"]
    terminal_states = stage05.get("terminal_states")
    terminal_ids = set(terminal_states) if isinstance(terminal_states, dict) else set()
    errors: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        entry_label = f"{prefix}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{entry_label} must be an object")
            continue
        for field in PER_BURDEN_REQUIRED_STRING_FIELDS:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{entry_label}.{field} must be a non-empty string")
            else:
                errors.extend(stage05_forbidden_per_burden_text_errors(f"{entry_label}.{field}", value))
        burden_id = entry.get("burden_id")
        if isinstance(burden_id, str) and burden_id:
            if burden_id in seen:
                errors.append(f"{entry_label}.burden_id duplicates {burden_id}")
            seen.add(burden_id)
            if terminal_ids and burden_id not in terminal_ids:
                errors.append(f"{entry_label}.burden_id {burden_id} must appear in terminal_states")
        reread = entry.get("reread")
        if isinstance(reread, str) and "R(H," not in reread:
            errors.append(f"{entry_label}.reread must invoke R(H,Δ)")
        landed_delta = entry.get("landed_delta")
        if isinstance(landed_delta, str) and "Δ" not in landed_delta and "Delta" not in landed_delta:
            errors.append(f"{entry_label}.landed_delta must name Δ/Delta")
        if entry.get("finding") not in PER_BURDEN_FINDINGS:
            errors.append(f"{entry_label}.finding must be a controlled finding token")
        if entry.get("route_result_type") not in PER_BURDEN_ROUTE_RESULT_TYPES:
            errors.append(f"{entry_label}.route_result_type must be a controlled MRP route result type")
        if entry.get("route") not in PER_BURDEN_ROUTES:
            errors.append(f"{entry_label}.route must be STOP, HOLD, RECURSE, or LoopBreak(∇×T)")
        if entry.get("preemption_basis") not in PER_BURDEN_PREEMPTION_BASES:
            errors.append(
                f"{entry_label}.preemption_basis must be none, graph-bound, commitment-bound, or framework-bound"
            )
        boundary = entry.get("boundary")
        if isinstance(boundary, str) and boundary and not boundary.startswith(PER_BURDEN_BOUNDARY_PREFIX):
            errors.append(f"{entry_label}.boundary must begin with the T_lang non-uptake boundary")
        divergence = entry.get("divergence")
        if isinstance(divergence, str) and divergence.strip():
            errors.extend(
                staged_output.per_burden_diag_errors(
                    f"{entry_label}.divergence",
                    divergence,
                    staged_output.PER_BURDEN_DIVERGENCE_PREFIX_RE,
                    staged_output.PER_BURDEN_DIVERGENCE_HEADS,
                )
            )
        curl = entry.get("curl")
        if isinstance(curl, str) and curl.strip():
            errors.extend(
                staged_output.per_burden_diag_errors(
                    f"{entry_label}.curl",
                    curl,
                    staged_output.PER_BURDEN_CURL_PREFIX_RE,
                    staged_output.PER_BURDEN_CURL_HEADS,
                )
            )
        activations = entry.get("pressure_activations")
        if not isinstance(activations, dict):
            errors.append(f"{entry_label}.pressure_activations must be an object carrying the six fixed slots")
            continue
        missing = sorted(PER_BURDEN_PRESSURE_KEYS - set(activations))
        extra = sorted(set(activations) - PER_BURDEN_PRESSURE_KEYS)
        if missing:
            errors.append(f"{entry_label}.pressure_activations missing slot(s): {missing}")
        if extra:
            errors.append(f"{entry_label}.pressure_activations unknown slot(s): {extra}")
        for key, value in activations.items():
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{entry_label}.pressure_activations.{key} must be a non-empty string")
            else:
                errors.extend(
                    stage05_forbidden_per_burden_text_errors(
                        f"{entry_label}.pressure_activations.{key}", value
                    )
                )
    return errors


def per_burden_reread_coverage_errors(
    label: str, stage05: dict[str, Any], required_burdens: set[str]
) -> list[str]:
    if stage05.get("status") not in PASS_STATUS or len(required_burdens) <= 1:
        return []
    if PER_BURDEN_REREAD_FIELD not in stage05:
        return []
    entries = stage05.get(PER_BURDEN_REREAD_FIELD)
    prefix = f"{label}: stage-05 {PER_BURDEN_REREAD_FIELD}"
    if not isinstance(entries, list) or not entries:
        return [
            f"{prefix} must cover every landed ACT burden before multi-burden no_new_resultant closure"
        ]
    seen = {
        entry.get("burden_id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("burden_id"), str)
    }
    missing = sorted(required_burdens - seen)
    if missing:
        return [
            f"{prefix} missing landed ACT burden(s) {missing}; one terminal MRP/no_new_resultant "
            "cannot cover multiple prior burden landings"
        ]
    return []


def stage05_mrp_errors(
    label: str,
    stage02: dict[str, Any] | None,
    stage03: dict[str, Any] | None,
    stage04: dict[str, Any] | None,
    stage05: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    forbidden = sorted(STAGE05_FORBIDDEN_FIELDS & set(stage05))
    if forbidden:
        errors.append(f"{label}: stage-05 must not emit release/final/verifier field(s): {forbidden}")
    errors.extend(per_burden_reread_errors(label, stage05))

    act_burdens = canonical_stage04_act_burdens(stage04)
    known_burdens = (
        set(list_field(stage02 or {}, "burden_floor"))
        | set(list_field(stage03 or {}, "route_targets"))
        | set(list_field(stage04 or {}, "act_targets"))
        | act_burdens
    )
    floor_burdens = set(list_field(stage02 or {}, "burden_floor"))
    pre_generated_known_burdens = set(known_burdens)
    generated, found = generated_burden_ids(stage05)
    errors.extend(f"{label}: {error}" for error in found)
    generated_parents, found = generated_burden_parent_map(stage05)
    errors.extend(f"{label}: {error}" for error in found)
    known_burdens |= generated
    for burden_id, parent_id in sorted(generated_parents.items()):
        if burden_id in floor_burdens:
            errors.append(f"{label}: generated burden {burden_id} must not be in stage-02 burden_floor")
        if parent_id not in pre_generated_known_burdens:
            errors.append(f"{label}: generated burden {burden_id} parent {parent_id} must be an existing pre-MRP burden")

    terminal_states = stage05.get("terminal_states")
    terminal_burdens: set[str] = set()
    if not isinstance(terminal_states, dict) or not terminal_states:
        errors.append(f"{label}: stage-05 terminal_states must be a non-empty object")
    else:
        for burden_id, state in terminal_states.items():
            if not isinstance(burden_id, str) or not burden_id:
                errors.append(f"{label}: stage-05 terminal_states keys must be non-empty burden ids")
                continue
            terminal_burdens.add(burden_id)
            if not isinstance(state, str):
                errors.append(f"{label}: stage-05 terminal_states[{burden_id!r}] must be a string")
            elif state not in TERMINAL_STATE_VALUES:
                errors.append(
                    f"{label}: stage-05 terminal_states[{burden_id!r}] must use a controlled terminal state"
                )
        missing_act = sorted(act_burdens - terminal_burdens)
        if missing_act:
            errors.append(f"{label}: stage-05 terminal_states missing ACT burden(s): {missing_act}")
        missing_generated = sorted(generated - terminal_burdens)
        if missing_generated:
            errors.append(f"{label}: stage-05 terminal_states missing generated burden(s): {missing_generated}")
        unknown_terminal = sorted(terminal_burdens - known_burdens)
        if unknown_terminal:
            errors.append(f"{label}: stage-05 terminal_states names unknown burden(s): {unknown_terminal}")
    required_reread_burdens = act_burdens | (terminal_burdens & known_burdens)
    errors.extend(per_burden_reread_coverage_errors(label, stage05, required_reread_burdens))

    edge_pairs: set[tuple[str, str]] = set()
    edges = stage05.get("dependency_graph_edges")
    if not isinstance(edges, list):
        errors.append(f"{label}: stage-05 dependency_graph_edges must be a list")
        edges = []
    for index, edge in enumerate(edges):
        source, target, error = dependency_graph_edge_endpoints(edge)
        edge_label = f"{label}: stage-05 dependency_graph_edges[{index}]"
        if error:
            errors.append(f"{edge_label}: {error}")
            continue
        assert source is not None and target is not None
        edge_pairs.add((source, target))
        unknown = sorted({source, target} - known_burdens)
        if unknown:
            errors.append(f"{edge_label}: endpoint(s) must appear in known/generated burden set: {unknown}")

    graph = stage05.get("dependency_graph")
    if graph is not None:
        if not isinstance(graph, dict):
            errors.append(f"{label}: stage-05 dependency_graph must be an object when present")
        else:
            nodes = graph.get("nodes", [])
            if not isinstance(nodes, list) or not all(isinstance(item, str) and item for item in nodes):
                errors.append(f"{label}: stage-05 dependency_graph.nodes must be a string list when present")
            else:
                unknown_nodes = sorted(set(nodes) - known_burdens)
                if unknown_nodes:
                    errors.append(f"{label}: stage-05 dependency_graph.nodes names unknown burden(s): {unknown_nodes}")
            graph_edges = graph.get("edges", [])
            if not isinstance(graph_edges, list):
                errors.append(f"{label}: stage-05 dependency_graph.edges must be a list when present")
            else:
                for index, edge in enumerate(graph_edges):
                    source, target, error = dependency_graph_edge_endpoints(edge)
                    graph_edge_label = f"{label}: stage-05 dependency_graph.edges[{index}]"
                    if error:
                        errors.append(f"{graph_edge_label}: {error}")
                        continue
                    assert source is not None and target is not None
                    edge_pairs.add((source, target))
                    unknown = sorted({source, target} - known_burdens)
                    if unknown:
                        errors.append(f"{graph_edge_label}: endpoint(s) must appear in known/generated burden set: {unknown}")
    for burden_id, parent_id in sorted(generated_parents.items()):
        if (parent_id, burden_id) not in edge_pairs:
            errors.append(
                f"{label}: generated burden {burden_id} must have dependency edge {parent_id}->{burden_id}"
            )

    proof = stage05.get("no_new_resultant_proof")
    if proof is None:
        errors.append(f"{label}: stage-05 no_new_resultant_proof is required")
    unresolved, found = unresolved_burden_ids(stage05, proof)
    errors.extend(f"{label}: {error}" for error in found)
    if isinstance(proof, bool):
        if proof is False and stage05.get("status") == "pass":
            errors.append(f"{label}: stage-05 pass requires a positive no_new_resultant_proof")
        if proof is True and unresolved:
            errors.append(f"{label}: stage-05 no_new_resultant_proof true conflicts with unresolved burden(s): {sorted(unresolved)}")
    elif isinstance(proof, dict):
        proved = proof.get("proved")
        if not isinstance(proved, bool):
            errors.append(f"{label}: stage-05 no_new_resultant_proof.proved must be boolean")
        if proved is True:
            basis = proof.get("basis")
            if not isinstance(basis, str) or not basis.strip():
                errors.append(f"{label}: stage-05 no_new_resultant_proof.basis must be non-empty when proved=true")
            if unresolved:
                errors.append(f"{label}: stage-05 no_new_resultant_proof proved=true conflicts with unresolved burden(s): {sorted(unresolved)}")
        if proved is False and stage05.get("status") == "pass":
            errors.append(f"{label}: stage-05 pass requires no_new_resultant_proof.proved=true")
    elif proof is not None:
        errors.append(f"{label}: stage-05 no_new_resultant_proof must be boolean or object")

    if unresolved and stage05.get("status") == "pass":
        errors.append(f"{label}: stage-05 status must be held/partial/fail when unresolved_burdens are present")

    reread_state = stage05.get("reread_state")
    if reread_state is not None:
        if not isinstance(reread_state, dict):
            errors.append(f"{label}: stage-05 reread_state must be an object when present")
        else:
            divergence = reread_state.get("divergence_state")
            curl = reread_state.get("curl_state")
            route_result = reread_state.get("route_result_type")
            route = reread_state.get("route")
            if divergence is not None and divergence not in REREAD_DIVERGENCE_STATES:
                errors.append(f"{label}: stage-05 reread_state.divergence_state is not controlled")
            if curl is not None and curl not in REREAD_CURL_STATES:
                errors.append(f"{label}: stage-05 reread_state.curl_state is not controlled")
            if route_result is not None and route_result not in REREAD_ROUTE_RESULT_TYPES:
                errors.append(f"{label}: stage-05 reread_state.route_result_type is not controlled")
            if route is not None and route not in REREAD_ROUTES:
                errors.append(f"{label}: stage-05 reread_state.route is not controlled")
            if route == "STOP" and unresolved:
                errors.append(f"{label}: stage-05 reread_state.route STOP conflicts with unresolved burden(s): {sorted(unresolved)}")

    details = stage05.get("terminal_state_details")
    if details is not None:
        if not isinstance(details, list):
            errors.append(f"{label}: stage-05 terminal_state_details must be a list when present")
        else:
            for index, detail in enumerate(details):
                if not isinstance(detail, dict):
                    errors.append(f"{label}: stage-05 terminal_state_details[{index}] must be an object")
                    continue
                burden_id = detail.get("burden_id")
                state = detail.get("state")
                terminal_state = detail.get("terminal_state")
                if state is None:
                    state = terminal_state
                elif terminal_state is not None and terminal_state != state:
                    errors.append(
                        f"{label}: stage-05 terminal_state_details[{index}].state and .terminal_state must match"
                    )
                if not isinstance(burden_id, str) or burden_id not in terminal_burdens:
                    errors.append(f"{label}: stage-05 terminal_state_details[{index}].burden_id must name a terminal burden")
                if not isinstance(state, str) or state not in TERMINAL_STATE_VALUES:
                    errors.append(f"{label}: stage-05 terminal_state_details[{index}].state must use a controlled terminal state")
                elif isinstance(terminal_states, dict) and terminal_states.get(burden_id) != state:
                    errors.append(f"{label}: stage-05 terminal_state_details[{index}].state must match terminal_states")
                basis = detail.get("basis")
                _normalized_basis, basis_error = normalize_terminal_detail_basis(basis)
                if basis_error:
                    errors.append(f"{label}: stage-05 terminal_state_details[{index}].basis {basis_error}")
    return errors


def owner_routes_by_burden(stage03: dict[str, Any] | None) -> dict[str, set[str]]:
    if not isinstance(stage03, dict):
        return {}
    routes = stage03.get("owner_routes")
    if not isinstance(routes, list):
        return {}
    result: dict[str, set[str]] = {}
    for route in routes:
        if not isinstance(route, dict):
            continue
        burden_id = route.get("burden_id")
        owner_id = route.get("owner_id")
        if isinstance(burden_id, str) and burden_id and isinstance(owner_id, str) and owner_id:
            owner, _operation = split_owner_operation_token(owner_id, route.get("operation") or route.get("owner_operation"))
            owners = result.setdefault(burden_id, set())
            owners.add(owner_id)
            if owner:
                owners.add(owner)
    return result


def act_body_ref(row: str) -> str | None:
    match = ACT_BODY_REF_RE.search(row)
    return match.group(1) if match else None


def act_land_burden(row: str) -> str:
    match = LAND_TARGET_RE.search(row)
    if not match:
        return ""
    return canonical_burden_id(match.group("target"))


def act_owner(row: str) -> str | None:
    match = ACT_OWNER_RE.match(row.strip())
    return match.group(1) if match else None


def act_row_owner_transition_errors(label: str, row: str) -> list[str]:
    match = ACT_OWNER_OPERATION_DELTA_RE.match(row.strip())
    if not match:
        return []
    owner = match.group("owner")
    operation = match.group("operation")
    delta_result = match.group("delta_result")
    errors: list[str] = []
    errors.extend(family_alias_as_executable_owner_errors(label, owner, operation))
    errors.extend(owner_operation_vocabulary_errors(label, owner, operation))
    errors.extend(delta_result_vocabulary_errors(label, owner, delta_result))
    errors.extend(owner_operation_delta_result_errors(label, owner, operation, delta_result))
    errors.extend(
        source_formal_delta_operation_errors(
            label,
            owner,
            operation,
            delta_result,
        )
    )
    return errors


def object_source_formal_errors(label: str, item: dict[str, Any]) -> list[str]:
    owner = item.get("owner_id") or item.get("owner")
    operation = item.get("operation")
    delta_result = item.get("delta_result")
    if owner is None or operation is None or delta_result is None:
        return []
    errors: list[str] = []
    errors.extend(family_alias_as_executable_owner_errors(label, str(owner), str(operation)))
    errors.extend(owner_operation_vocabulary_errors(label, str(owner), str(operation)))
    errors.extend(delta_result_vocabulary_errors(label, str(owner), str(delta_result)))
    errors.extend(owner_operation_delta_result_errors(label, str(owner), str(operation), str(delta_result)))
    errors.extend(source_formal_delta_operation_errors(label, str(owner), str(operation), str(delta_result)))
    return errors


def stage04_hold_partial_burdens(stage04: dict[str, Any]) -> set[str]:
    held: set[str] = set()
    for key in ("hold_partial", "hold_partial_routes", "held_or_partial_routes"):
        value = stage04.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str):
                burden_id = canonical_burden_id_from_text(item)
                if burden_id:
                    held.add(burden_id)
                continue
            if not isinstance(item, dict):
                continue
            burden_id = item.get("burden_id") or item.get("target")
            if not isinstance(burden_id, str):
                continue
            if route_is_held_or_partial(item) or key in {"hold_partial", "hold_partial_routes", "held_or_partial_routes"}:
                canonical = canonical_burden_id_from_text(burden_id)
                if canonical:
                    held.add(canonical)
    return held


def stage04_held_target_burdens(stage04: dict[str, Any] | None) -> set[str]:
    if not isinstance(stage04, dict):
        return set()
    held: set[str] = set(stage04_hold_partial_burdens(stage04))
    for value in as_string_list(stage04.get("held_act_targets")) or []:
        canonical = canonical_burden_id_from_text(value)
        if canonical:
            held.add(canonical)
    details = stage04.get("held_act_details")
    if isinstance(details, list):
        for item in details:
            if isinstance(item, str):
                canonical = canonical_burden_id_from_text(item)
                if canonical:
                    held.add(canonical)
                continue
            if not isinstance(item, dict):
                continue
            burden_id = item.get("burden_id") or item.get("target") or item.get("land_target")
            if isinstance(burden_id, str):
                canonical = canonical_burden_id_from_text(burden_id)
                if canonical:
                    held.add(canonical)
    return held


def stage04_act_errors(
    label: str,
    stage03: dict[str, Any] | None,
    stage04: dict[str, Any],
    *,
    allow_descriptive_burdens: bool = False,
) -> list[str]:
    errors: list[str] = []
    raw_targets = stage04.get("act_targets")
    raw_burdens = stage04.get("act_burdens")
    raw_body_refs = stage04.get("act_body_refs")
    raw_rows = stage04.get("act_rows")

    act_targets = as_string_list(raw_targets)
    act_burdens = as_string_list(raw_burdens)
    act_body_refs = as_string_list(raw_body_refs)
    act_rows = as_string_list(raw_rows)
    if act_targets is None or not act_targets:
        errors.append(f"{label}: stage-04 act_targets must be a non-empty string list")
        act_targets = []
    if act_burdens is None or not act_burdens:
        errors.append(f"{label}: stage-04 act_burdens must be a non-empty string list")
        act_burdens = []
    else:
        allowed_ids = set(act_targets) if act_targets else None
        noncanonical_burdens: list[str] = []
        unparseable_burdens: list[str] = []
        for value in act_burdens:
            canonical = canonical_burden_id_from_text(value, allowed_ids)
            if canonical is None:
                unparseable_burdens.append(value)
            elif value != canonical:
                noncanonical_burdens.append(value)
        if unparseable_burdens:
            errors.append(f"{label}: stage-04 act_burdens must name routed canonical burden ids: {unparseable_burdens}")
        if noncanonical_burdens and not allow_descriptive_burdens:
            errors.append(
                f"{label}: stage-04 act_burdens must use canonical ids, not descriptive labels: {noncanonical_burdens}"
            )
    if act_body_refs is None or not act_body_refs:
        errors.append(f"{label}: stage-04 act_body_refs must be a non-empty string list")
        act_body_refs = []
    if act_rows is None or not act_rows:
        errors.append(f"{label}: stage-04 act_rows must be a non-empty string list")
        act_rows = []

    semantic_act_burdens = canonical_stage04_act_burdens(stage04)
    hold_partial_burdens = stage04_hold_partial_burdens(stage04)
    held_target_burdens = stage04_held_target_burdens(stage04)
    if hold_partial_burdens and stage04.get("status") == "pass":
        errors.append(f"{label}: stage-04 status must be held/partial/fail when hold_partial route evidence is present")
    missing_burdens = sorted(set(act_targets) - semantic_act_burdens - held_target_burdens)
    if missing_burdens:
        errors.append(f"{label}: stage-04 act_burdens missing act target(s): {missing_burdens}")
    duplicate_refs = sorted({ref for ref in act_body_refs if act_body_refs.count(ref) > 1})
    if duplicate_refs:
        errors.append(f"{label}: stage-04 act_body_refs must not contain duplicates: {duplicate_refs}")
    errors.extend(staged_output.body_ref_grouping_errors(act_body_refs, f"{label}: stage-04 act_body_refs"))

    row_refs: set[str] = set()
    row_ref_sequence: list[str] = []
    row_owners: set[str] = set()
    for index, row in enumerate(act_rows):
        row_label = f"{label}: stage-04 act_rows[{index}]"
        stripped = row.strip()
        if not stripped.startswith("⟦ACT"):
            errors.append(f"{row_label} must start with canonical '⟦ACT'")
        if not CANONICAL_ACT_ROW_RE.match(stripped):
            errors.append(
                f"{row_label} must match canonical slot order "
                "'⟦ACT <ref>[owner.operation] :: π=... :: body_ref=... :: Δ=... :: Land(Bn)+⟧'"
            )
        if "body_ref=" not in stripped:
            errors.append(f"{row_label} must contain body_ref=")
        if "Δ=" not in stripped:
            errors.append(f"{row_label} must contain Δ=")
        errors.extend(act_row_owner_transition_errors(row_label, stripped))
        if "Land(" not in stripped:
            errors.append(f"{row_label} must contain Land(")
        if not stripped.endswith("⟧"):
            errors.append(f"{row_label} must close with '⟧'")
        ref = act_body_ref(stripped)
        if ref is None:
            errors.append(f"{row_label} must expose a parseable body_ref token")
        else:
            row_refs.add(ref)
            row_ref_sequence.append(ref)
            if ref not in act_body_refs:
                errors.append(f"{row_label} body_ref {ref!r} must appear in stage-04 act_body_refs")
            encoded_burden = body_ref_burden_id(ref)
            land_burden = act_land_burden(stripped)
            if encoded_burden and land_burden and encoded_burden != land_burden:
                errors.append(
                    f"{row_label} body_ref {ref!r} encodes {encoded_burden} but Land() targets {land_burden}"
                )
        owner = act_owner(stripped)
        if owner:
            row_owners.add(owner)

    missing_row_refs = sorted(set(act_body_refs) - row_refs)
    if act_body_refs and missing_row_refs:
        errors.append(f"{label}: stage-04 act_body_refs missing from ACT rows: {missing_row_refs}")
    errors.extend(
        staged_output.body_ref_grouping_errors(row_ref_sequence, f"{label}: stage-04 ACT row body_ref order")
    )

    owners_by_burden = owner_routes_by_burden(stage03)
    eligible_owners = {owner for owners in owners_by_burden.values() for owner in owners}
    unsupported_owners = sorted(row_owners - eligible_owners) if eligible_owners else []
    if unsupported_owners:
        errors.append(f"{label}: stage-04 ACT row owner(s) not backed by stage-03 owner_routes: {unsupported_owners}")

    details = stage04.get("act_row_details")
    if details is not None:
        if not isinstance(details, list):
            errors.append(f"{label}: stage-04 act_row_details must be a list when present")
        else:
            for index, detail in enumerate(details):
                detail_label = f"{label}: stage-04 act_row_details[{index}]"
                if not isinstance(detail, dict):
                    errors.append(f"{detail_label} must be an object")
                    continue
                burden_id = detail.get("burden_id")
                if not isinstance(burden_id, str) or not burden_id:
                    errors.append(f"{detail_label}.burden_id must be a string")
                elif burden_id not in set(act_targets) | set(act_burdens):
                    errors.append(f"{detail_label}.burden_id must appear in act_targets or act_burdens")
                body_ref = detail.get("body_ref")
                if not isinstance(body_ref, str) or not body_ref:
                    errors.append(f"{detail_label}.body_ref must be a string")
                elif body_ref not in act_body_refs:
                    errors.append(f"{detail_label}.body_ref must appear in act_body_refs")
                elif isinstance(burden_id, str) and body_ref_burden_id(body_ref) and body_ref_burden_id(body_ref) != burden_id:
                    errors.append(
                        f"{detail_label}.body_ref {body_ref!r} encodes {body_ref_burden_id(body_ref)} "
                        f"but burden_id is {burden_id}"
                    )
                owner_id = detail.get("owner_id")
                if owner_id is not None:
                    if not isinstance(owner_id, str) or not owner_id:
                        errors.append(f"{detail_label}.owner_id must be a string when present")
                    elif (
                        isinstance(burden_id, str)
                        and owners_by_burden.get(burden_id)
                        and owner_id not in owners_by_burden[burden_id]
                    ):
                        errors.append(f"{detail_label}.owner_id must be backed by stage-03 owner_routes for {burden_id}")
                for key in ("operation", "delta_result"):
                    value = detail.get(key)
                    if value is not None and (not isinstance(value, str) or not value):
                        errors.append(f"{detail_label}.{key} must be a string when present")
                errors.extend(
                    register_axis_errors(
                        detail_label,
                        detail.get("owner_id") or detail.get("owner"),
                        detail.get("operation"),
                        detail.get("register_axis", detail.get("axis")),
                    )
                )
                errors.extend(object_source_formal_errors(detail_label, detail))
                act_row_value = detail.get("act_row")
                if act_row_value is not None:
                    if not isinstance(act_row_value, str) or not act_row_value:
                        errors.append(f"{detail_label}.act_row must be a string when present")
                    elif act_row_value not in act_rows:
                        errors.append(f"{detail_label}.act_row must appear in act_rows")
    return errors


STAGE01_REQUIRED_FIELDS = (
    # input_digest: the only field every stage-01 payload across all harness
    # paths (retained-artifact-replay, no-model-fixture, staged-current-
    # skill-stage-local-smoke) actually emits. It is the custody anchor
    # stage-02 depends on (stage-02.requires == ["input_digest"]); deleting it
    # breaks the input-boundary chain silently, which is the gap this
    # validator closes.
    "input_digest",
)


def stage01_intake_errors(label: str, stage01: dict[str, Any]) -> list[str]:
    """Field-presence validator for stage-01-intake.

    Mirrors the stageNN_*_errors() pattern used for stages 02-06: each of
    those stages re-derives its own required-field presence from
    field-specific validation (e.g. stage-05 requires terminal_states
    directly). Stage-01 had no such check -- only the generic stage-shape
    checks in sequence_errors() -- so deleting stage-01's input_digest was not
    rejected. See tools/gen_fixture_mutations.py KNOWN_CHECKER_GAPS history.

    Only input_digest is required here. retained_input and
    source_boundary_preserved are real fields the retained-artifact-replay
    harness path emits, but they are legitimately absent from
    staged-current-skill-stage-local-smoke stage-01 payloads (confirmed
    against all 25 valid fixtures), so requiring them would break otherwise-
    valid model-mode fixtures. case_id (case identity) is already enforced at
    the record level in record_errors(), not per-stage, so it is not
    duplicated here.
    """
    errors: list[str] = []
    for field in STAGE01_REQUIRED_FIELDS:
        value = stage01.get(field)
        if not isinstance(value, str) or not value:
            errors.append(f"{label}: stage-01 {field} is required and must be a non-empty string")
    return errors


def semantic_errors(path: Path, record: dict[str, Any], stages: dict[str, dict[str, Any]]) -> list[str]:
    label = rel(path)
    errors: list[str] = []
    stage01 = stages.get("stage-01-intake")
    stage02 = stages.get("stage-02-layer-a-diagnostic-ir")
    stage03 = stages.get("stage-03-routing-owner-gate")
    stage04 = stages.get("stage-04-burden-execution-act")
    stage05 = stages.get("stage-05-mrp-reread-terminal-state")
    stage06 = stages.get("stage-06-field-witness-nar")
    stage07 = stages.get("stage-07-release-output")
    stage08 = stages.get("stage-08-verifier-sidecars")

    if stage01 is not None:
        errors.extend(stage01_intake_errors(label, stage01))

    raw_burden_floor = stage02.get("burden_floor") if stage02 is not None else None
    burden_floor_values = as_string_list(raw_burden_floor)
    burden_floor = {
        value
        for value in (burden_floor_values or [])
        if CANONICAL_BURDEN_ID_RE.fullmatch(value) is not None
    }
    route_targets = set(list_field(stage03 or {}, "route_targets"))
    act_targets = set(list_field(stage04 or {}, "act_targets"))
    act_body_refs = set(list_field(stage04 or {}, "act_body_refs"))
    field_witness_body_refs = set(list_field(stage06 or {}, "field_witness_body_refs"))
    act_burdens = canonical_stage04_act_burdens(stage04)
    nar_burdens = set(list_field(stage06 or {}, "nar_burdens"))

    if stage02 is not None:
        if burden_floor_values is None or not burden_floor_values:
            errors.append(f"{label}: stage-02 burden_floor must be a non-empty string list")
        else:
            errors.extend(bare_burden_id_errors(label, "stage-02 burden_floor", burden_floor_values))
        floor_details = stage02.get("burden_floor_details")
        if floor_details is not None:
            if not isinstance(floor_details, list):
                errors.append(f"{label}: stage-02 burden_floor_details must be a list when present")
            else:
                for index, detail in enumerate(floor_details):
                    if not isinstance(detail, dict):
                        errors.append(f"{label}: stage-02 burden_floor_details[{index}] must be an object")
                        continue
                    burden_id = detail.get("burden_id") or detail.get("id")
                    if not isinstance(burden_id, str) or not burden_id:
                        errors.append(
                            f"{label}: stage-02 burden_floor_details[{index}].burden_id must be a string"
                        )
                    elif CANONICAL_BURDEN_ID_RE.fullmatch(burden_id) is None:
                        errors.append(
                            f"{label}: stage-02 burden_floor_details[{index}].burden_id must be a canonical burden id"
                        )
                    elif burden_id not in burden_floor:
                        errors.append(
                            f"{label}: stage-02 burden_floor_details[{index}].burden_id must appear in burden_floor"
                        )
    if stage03 is not None:
        raw_route_targets = stage03.get("route_targets")
        if as_string_list(raw_route_targets) is None:
            errors.append(f"{label}: stage-03 route_targets must be a string list")
        owner_routes = stage03.get("owner_routes")
        if not isinstance(owner_routes, list) or not owner_routes:
            errors.append(f"{label}: stage-03 owner_routes must be a non-empty object list")
        else:
            for index, route in enumerate(owner_routes):
                route_label = f"{label}: stage-03 owner_routes[{index}]"
                if not isinstance(route, dict):
                    errors.append(f"{route_label} must be an object")
                    continue
                errors.extend(route_owner_vocabulary_errors(route_label, route))
        details = stage03.get("route_target_details")
        if details is not None:
            if isinstance(details, dict):
                for burden_id, detail in details.items():
                    if not isinstance(burden_id, str) or not burden_id:
                        errors.append(f"{label}: stage-03 route_target_details keys must be burden ids")
                    elif burden_id not in route_targets:
                        errors.append(
                            f"{label}: stage-03 route_target_details[{burden_id!r}] must appear in route_targets"
                        )
                    if not isinstance(detail, dict):
                        errors.append(f"{label}: stage-03 route_target_details[{burden_id!r}] must be an object")
            elif not isinstance(details, list):
                errors.append(f"{label}: stage-03 route_target_details must be a list or burden-id map when present")
            else:
                for index, detail in enumerate(details):
                    if not isinstance(detail, dict):
                        errors.append(f"{label}: stage-03 route_target_details[{index}] must be an object")
                        continue
                    burden_id = detail.get("burden_id")
                    if not isinstance(burden_id, str) or not burden_id:
                        errors.append(f"{label}: stage-03 route_target_details[{index}].burden_id must be a string")
                    elif burden_id not in route_targets:
                        errors.append(
                            f"{label}: stage-03 route_target_details[{index}].burden_id must appear in route_targets"
                        )
    if stage03 is not None and not route_targets:
        errors.append(f"{label}: stage-03 route_targets is required")
    if stage02 is not None and stage03 is not None and route_targets != burden_floor:
        errors.append(f"{label}: stage-03 route_targets must match stage-02 burden_floor")
    if stage04 is not None:
        errors.extend(
            stage04_act_errors(
                label,
                stage03,
                stage04,
                allow_descriptive_burdens=failed_model_prefix_order(record) is not None,
            )
        )
    if stage03 is not None and stage04 is not None:
        held_targets = stage04_held_target_burdens(stage04)
        extra_act_targets = sorted(act_targets - route_targets)
        missing_route_targets = sorted(route_targets - act_targets - held_targets)
        if extra_act_targets:
            errors.append(f"{label}: stage-04 act_targets not routed by stage-03: {extra_act_targets}")
        if missing_route_targets:
            errors.append(
                f"{label}: stage-04 route_targets must be covered by act_targets or held_act_targets: "
                f"{missing_route_targets}"
            )

    terminal_states = stage05.get("terminal_states") if stage05 is not None else None
    release_terminal_states = stage07.get("release_terminal_states") if stage07 is not None else None
    if stage05 is not None:
        errors.extend(stage05_mrp_errors(label, stage02, stage03, stage04, stage05))
        if (
            record.get("mode") in MODEL_MODES
            and stage05.get("status") in PASS_STATUS
            and PER_BURDEN_REREAD_FIELD not in stage05
            and record.get("legacy_contract") != "pre-per-burden-reread"
        ):
            errors.append(
                f"{label}: stage-05 model-mode records require {PER_BURDEN_REREAD_FIELD}; "
                "only pre-slice-B retained records may carry legacy_contract 'pre-per-burden-reread'"
            )
    if stage06 is not None:
        errors.extend(stage06_witness_nar_errors(label, record, stage02, stage04, stage05, stage06))
    if stage07 is not None:
        errors.extend(stage07_release_errors(label, path, record, stage05, stage07))
    if stage05 is not None and isinstance(terminal_states, dict) and stage07 is not None and terminal_states != release_terminal_states:
        errors.append(f"{label}: stage-07 release_terminal_states must match stage-05 terminal_states")

    held_or_partial = any(stage.get("status") in {"held", "partial"} for stage in stages.values())
    if isinstance(terminal_states, dict):
        held_or_partial = held_or_partial or any(str(value) in HELD_TERMINAL_STATES for value in terminal_states.values())
    if held_or_partial and stage07 is not None and stage07.get("closure_claim") == "complete":
        errors.append(f"{label}: release must not claim complete closure after held/partial stage state")

    verifier_sidecars = stage08.get("verifier_sidecars") if stage08 is not None else None
    if isinstance(verifier_sidecars, dict):
        b5 = verifier_sidecars.get("b5_4_1")
        if isinstance(b5, dict) and b5.get("claimed") is True:
            if not isinstance(stage07.get("release_output"), dict):
                errors.append(f"{label}: B.5.4.1 sidecar claim requires stage-07 release_output")
            if not isinstance(terminal_states, dict) or not terminal_states:
                errors.append(f"{label}: B.5.4.1 sidecar claim requires terminal-state evidence")
            if not nar_burdens:
                errors.append(f"{label}: B.5.4.1 sidecar claim requires NAR burden evidence")
            if b5.get("builder") != B5_SIDECAR_BUILDER:
                errors.append(f"{label}: B.5.4.1 sidecar claim must reference {B5_SIDECAR_BUILDER}")
            if b5.get("schema") != B5_SIDECAR_SCHEMA:
                errors.append(f"{label}: B.5.4.1 sidecar claim must use schema {B5_SIDECAR_SCHEMA}")
            if b5.get("role") != "checker-owned-final-verifier":
                errors.append(f"{label}: B.5.4.1 sidecar role must be checker-owned-final-verifier")
            non_claims = b5.get("non_claims")
            if not isinstance(non_claims, dict) or non_claims.get("not_fresh_runtime_default_emission") is not True:
                errors.append(f"{label}: B.5.4.1 sidecar must preserve not_fresh_runtime_default_emission")
        # Plan 04: proof_sidecars path integrity. When a stage-08 proof_sidecars set is
        # claimed, its paths must be a non-empty list of repo-relative strings with no
        # absolute prefix and no '..' traversal. This closes the escape where a claimed
        # sidecar set listed an absolute or '../' path unchecked. Existence/hash binding
        # is deliberately NOT asserted here: the sidecars live in gitignored .daee run
        # dirs, so existence is run-context-dependent and remains owner-gated.
        proof_sidecars = verifier_sidecars.get("proof_sidecars")
        if isinstance(proof_sidecars, dict) and proof_sidecars.get("claimed") is True:
            sidecar_paths = proof_sidecars.get("paths")
            if not isinstance(sidecar_paths, list) or not sidecar_paths:
                errors.append(f"{label}: proof_sidecars claim requires a non-empty 'paths' list")
            else:
                for raw in sidecar_paths:
                    if not isinstance(raw, str) or not raw.strip():
                        errors.append(f"{label}: proof_sidecars path must be a non-empty string, got {raw!r}")
                        continue
                    norm = raw.replace("\\", "/")
                    is_absolute = norm.startswith("/") or (len(norm) >= 2 and norm[1] == ":")
                    if is_absolute or ".." in norm.split("/"):
                        errors.append(
                            f"{label}: proof_sidecars path must be repo-relative without '..' or an absolute prefix: {raw!r}"
                        )
    return errors


def b5_claim(stage08: dict[str, Any]) -> dict[str, Any] | None:
    verifier_sidecars = stage08.get("verifier_sidecars")
    if not isinstance(verifier_sidecars, dict):
        return None
    b5 = verifier_sidecars.get("b5_4_1")
    return b5 if isinstance(b5, dict) and b5.get("claimed") is True else None


def manifest_case_by_id(manifest: dict[str, Any], case_id: str) -> dict[str, Any] | None:
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        return None
    for case in cases:
        if isinstance(case, dict) and case.get("id") == case_id:
            return case
    return None


def expected_manifest_artifact_path(
    manifest_path: Path,
    case: dict[str, Any],
    field: str,
) -> tuple[Path | None, list[str]]:
    value: Any
    if field == B5_RETAINED_SIDECAR_FIELD:
        sidecar = case.get(B5_RETAINED_SIDECAR_FIELD)
        if not isinstance(sidecar, dict):
            return None, [f"{field}: retained case lacks B.5 full-IR sidecar metadata"]
        value = sidecar.get("path")
    else:
        value = case.get(field)
    resolved, error = retained.resolve_manifest_path(manifest_path, value)
    if error:
        return None, [f"{field}: {error}"]
    assert resolved is not None
    return resolved, []


def binding_artifact_errors(
    record_path: Path,
    bindings: dict[str, Any],
    manifest_path: Path,
    case: dict[str, Any],
    field: str,
    *,
    required: bool = True,
) -> tuple[Path | None, list[str]]:
    label = f"artifact_bindings.artifacts.{field}"
    artifacts = bindings.get("artifacts")
    if not isinstance(artifacts, dict):
        return None, [f"{rel(record_path)}: artifact_bindings.artifacts must be an object"]
    entry = artifacts.get(field)
    if entry is None and not required:
        return None, []
    if not isinstance(entry, dict):
        return None, [f"{rel(record_path)}: {label} must be an object"]
    errors: list[str] = []
    missing = sorted({"path", "sha256"} - set(entry))
    if missing:
        errors.append(f"{rel(record_path)}: {label} missing field(s): {missing}")
    if "schema" in entry and field != B5_RETAINED_SIDECAR_FIELD:
        errors.append(f"{rel(record_path)}: {label}.schema is only valid for retained sidecar artifacts")
    if "builder" in entry and field != B5_RETAINED_SIDECAR_FIELD:
        errors.append(f"{rel(record_path)}: {label}.builder is only valid for retained sidecar artifacts")

    actual_path, found = resolve_record_relative_path(record_path, entry.get("path"), label)
    errors.extend(found)
    expected_path, expected_found = expected_manifest_artifact_path(manifest_path, case, field)
    errors.extend(f"{rel(record_path)}: retained manifest case {error}" for error in expected_found)
    if actual_path is not None and expected_path is not None and actual_path.resolve() != expected_path.resolve():
        errors.append(
            f"{rel(record_path)}: {label}.path must match retained manifest path {rel(expected_path)!r}"
        )
    if actual_path is not None and not actual_path.exists():
        errors.append(f"{rel(record_path)}: {label}.path {rel(actual_path)} missing")

    expected_hash = entry.get("sha256")
    if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
        errors.append(f"{rel(record_path)}: {label}.sha256 must be a SHA256 hex digest")
    elif actual_path is not None and actual_path.exists():
        actual_hash = retained.sha256_file(actual_path)
        if expected_hash.upper() != actual_hash:
            errors.append(f"{rel(record_path)}: {label}.sha256 expected {expected_hash.upper()} but found {actual_hash}")

    if field == B5_RETAINED_SIDECAR_FIELD:
        sidecar = case.get(B5_RETAINED_SIDECAR_FIELD)
        if not isinstance(sidecar, dict):
            errors.append(f"{rel(record_path)}: {label} cannot be bound because retained case has no sidecar")
        else:
            if entry.get("schema") != B5_SIDECAR_SCHEMA:
                errors.append(f"{rel(record_path)}: {label}.schema must be {B5_SIDECAR_SCHEMA!r}")
            if entry.get("builder") != B5_SIDECAR_BUILDER:
                errors.append(f"{rel(record_path)}: {label}.builder must be {B5_SIDECAR_BUILDER!r}")
            manifest_hash = sidecar.get("sha256")
            if isinstance(manifest_hash, str) and isinstance(expected_hash, str) and manifest_hash.upper() != expected_hash.upper():
                errors.append(f"{rel(record_path)}: {label}.sha256 must match retained sidecar manifest hash")
    else:
        manifest_hashes = case.get("hashes")
        manifest_hash = manifest_hashes.get(field) if isinstance(manifest_hashes, dict) else None
        if isinstance(manifest_hash, str) and isinstance(expected_hash, str) and manifest_hash.upper() != expected_hash.upper():
            errors.append(f"{rel(record_path)}: {label}.sha256 must match retained manifest hash")

    return actual_path, errors


def parsed_evidence_errors(
    record_path: Path,
    bindings: dict[str, Any],
    output_path: Path,
    stages: dict[str, dict[str, Any]],
    *,
    sidecar_required: bool,
) -> list[str]:
    label = f"{rel(record_path)}: artifact_bindings.parsed_evidence"
    errors: list[str] = []
    text = output_path.read_text(encoding="utf-8", errors="replace")
    field_witness, found = nla_decode.parse_field_witness(output_path, text)
    errors.extend(f"{rel(record_path)}: retained output: {error}" for error in found)
    records, parse_errors = nla_decode.parse_act_records(nla_decode.public_execution_text(text))
    errors.extend(f"{rel(record_path)}: retained output {rel(output_path)}: {error}" for error in parse_errors)
    if not records:
        errors.append(f"{rel(record_path)}: retained output must expose at least one parseable ACT row")

    parsed = bindings.get("parsed_evidence")
    if parsed is not None and not isinstance(parsed, dict):
        errors.append(f"{label} must be an object when present")
        parsed = {}
    if isinstance(parsed, dict):
        if parsed.get("field_witness") is not True:
            errors.append(f"{label}.field_witness must be true")
        visible_count = parsed.get("visible_act_records")
        if not isinstance(visible_count, int) or visible_count != len(records):
            errors.append(f"{label}.visible_act_records must equal parsed ACT count {len(records)}")
        if parsed.get("normalized_activation_record") is not True:
            errors.append(f"{label}.normalized_activation_record must be true")
        if sidecar_required and parsed.get("b5_full_ir_projection_sidecar") is not True:
            errors.append(f"{label}.b5_full_ir_projection_sidecar must be true for B.5.4.1 retained binding")

    stage04 = stages.get("stage-04-burden-execution-act", {})
    stage06 = stages.get("stage-06-field-witness-nar", {})
    stage04_refs = set(list_field(stage04, "act_body_refs"))
    parsed_refs = {record.body_ref for record in records if record.body_ref}
    if stage04_refs and stage04_refs != parsed_refs:
        errors.append(
            f"{rel(record_path)}: stage-04 act_body_refs must match retained output ACT body_refs {sorted(parsed_refs)}"
        )

    if field_witness is None:
        return errors
    normalized = field_witness.get("normalized_activation_record")
    if not isinstance(normalized, dict):
        errors.append(f"{rel(record_path)}: retained output field_witness.normalized_activation_record is required")
        return errors
    nar_rows = normalized.get("per_burden")
    if not isinstance(nar_rows, list) or not nar_rows:
        errors.append(f"{rel(record_path)}: retained output NAR per_burden rows are required")
    else:
        nar_burdens = {
            nla_decode.graph_burden_id(row.get("burden_id"))
            for row in nar_rows
            if isinstance(row, dict)
        }
        stage06_burdens = set(list_field(stage06, "nar_burdens"))
        if stage06_burdens and stage06_burdens != nar_burdens:
            errors.append(
                f"{rel(record_path)}: stage-06 nar_burdens must match retained output NAR burdens {sorted(nar_burdens)}"
            )
    return errors


def artifact_binding_errors(path: Path, record: dict[str, Any], stages: dict[str, dict[str, Any]]) -> list[str]:
    stage08 = stages.get("stage-08-verifier-sidecars", {})
    claimed_b5 = b5_claim(stage08)
    bindings = record.get("artifact_bindings")
    if bindings is None:
        if claimed_b5 is not None:
            return [f"{rel(path)}: B.5.4.1 sidecar claim requires retained artifact_bindings"]
        return []
    if not isinstance(bindings, dict):
        return [f"{rel(path)}: artifact_bindings must be an object"]

    errors: list[str] = []
    if bindings.get("schema") != RETAINED_BINDING_SCHEMA:
        errors.append(f"{rel(path)}: artifact_bindings.schema must be {RETAINED_BINDING_SCHEMA!r}")
    manifest_path, found = resolve_record_relative_path(path, bindings.get("retained_manifest"), "artifact_bindings.retained_manifest")
    errors.extend(found)
    case_id = bindings.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        errors.append(f"{rel(path)}: artifact_bindings.case_id must be a non-empty string")
    elif record.get("case_id") != case_id:
        errors.append(f"{rel(path)}: artifact_bindings.case_id must match record case_id")

    manifest: Any | None = None
    case: dict[str, Any] | None = None
    if manifest_path is not None:
        if not manifest_path.exists():
            errors.append(f"{rel(path)}: artifact_bindings.retained_manifest {rel(manifest_path)} missing")
        else:
            manifest, found = retained.load_json(manifest_path)
            errors.extend(f"{rel(path)}: retained manifest: {error}" for error in found)
            if isinstance(manifest, dict):
                retained_found = retained.manifest_errors(manifest_path)
                errors.extend(f"{rel(path)}: retained manifest: {error}" for error in retained_found)
                if isinstance(case_id, str):
                    case = manifest_case_by_id(manifest, case_id)
                    if case is None:
                        errors.append(f"{rel(path)}: artifact_bindings.case_id {case_id!r} not found in retained manifest")
            else:
                errors.append(f"{rel(path)}: artifact_bindings.retained_manifest must be a manifest object")

    if case is None or manifest_path is None:
        return errors

    artifact_paths: dict[str, Path] = {}
    for field in retained.ARTIFACT_FIELDS:
        artifact_path, found = binding_artifact_errors(path, bindings, manifest_path, case, field)
        errors.extend(found)
        if artifact_path is not None:
            artifact_paths[field] = artifact_path

    sidecar_required = claimed_b5 is not None
    sidecar_path, found = binding_artifact_errors(
        path,
        bindings,
        manifest_path,
        case,
        B5_RETAINED_SIDECAR_FIELD,
        required=sidecar_required,
    )
    errors.extend(found)
    if claimed_b5 is not None and sidecar_path is None:
        errors.append(f"{rel(path)}: B.5.4.1 sidecar claim requires retained B.5 full-IR projection sidecar binding")

    output_path = artifact_paths.get("output")
    if output_path is not None and output_path.exists():
        errors.extend(
            parsed_evidence_errors(
                path,
                bindings,
                output_path,
                stages,
                sidecar_required=sidecar_required,
            )
        )
    return errors


def record_errors(path: Path, record: Any) -> list[str]:
    if not isinstance(record, dict):
        return [f"{rel(path)}: record root must be a JSON object"]
    errors: list[str] = []
    if record.get("schema") != SCHEMA:
        errors.append(f"{rel(path)}: schema must be {SCHEMA!r}")
    if record.get("user_interface_preserved") is not True:
        errors.append(f"{rel(path)}: user_interface_preserved must be true")
    if not isinstance(record.get("case_id"), str) or not record["case_id"].strip():
        errors.append(f"{rel(path)}: case_id is required")
    stages = stage_map(record)
    errors.extend(sequence_errors(path, record, stages))
    errors.extend(handoff_errors(path, record, stages))
    errors.extend(non_claim_errors(path, record))
    errors.extend(sha_errors(path, record))
    errors.extend(path_reference_errors(path, record))
    errors.extend(artifact_binding_errors(path, record, stages))
    errors.extend(semantic_errors(path, record, stages))
    return errors


EXPECTED_EXPLAIN_SUFFIX = ".expected-explain.json"


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    def fixtures_only(paths: Any) -> list[Path]:
        return sorted(p for p in paths if not p.name.endswith(EXPECTED_EXPLAIN_SUFFIX))

    return (
        fixtures_only((root / "valid").glob("*.json")),
        fixtures_only((root / "invalid").glob("*.json")),
    )


# ---------------------------------------------------------------------------
# Plan 13 Slice F / --explain-stage-failure: first-failed-stage classification
# ---------------------------------------------------------------------------
#
# This maps every error family this checker can emit onto a stable
# failure_class token and the earliest stage whose contract was violated
# (not necessarily the stage where the checker happened to notice it -- e.g. a
# stage-06 record that is missing a stage-04 act_body_ref is an act_body_ref
# violation, not a field_witness violation, even though it surfaces while
# validating stage-06 fields).
#
# Boundary (read before adding a "model-observed" class here): every failure
# class this checker can produce is decided by static, deterministic
# comparison of JSON/text fixtures already on disk -- there is no live model
# call in this checker's path. The pragmatic/uptake family (does the model's
# free-text response actually secure interlocutor uptake, do per-burden
# rereads plausibly reflect genuine reconsideration, etc.) is judged by the
# *render* checkers (check_tlang_response_closure.py and friends) against
# live model output, not by this handshake/record-shape checker. So no class
# below is "model-observed"; requires_model_rerun is always False here. If a
# future no-model-catchable class is added, keep it False; only add
# "model-observed" if a genuinely new class requires live model judgment,
# and call that out explicitly at the call site (this module never emits it).
FAILURE_CLASS_CUSTODY = "custody"
FAILURE_CLASS_BURDEN_FLOOR = "burden-floor"
FAILURE_CLASS_OWNER_ROUTE = "owner-route"
FAILURE_CLASS_ACT_BODY_REF = "act_body_ref"
FAILURE_CLASS_MRP = "mrp"
FAILURE_CLASS_FIELD_WITNESS = "field_witness"
FAILURE_CLASS_PUBLIC_PROJECTION = "public-projection"
FAILURE_CLASS_SIDECAR = "sidecar"
FAILURE_CLASS_HANDOFF = "handoff"
FAILURE_CLASS_SEQUENCE = "sequence"
FAILURE_CLASS_NON_CLAIM = "non-claim"
FAILURE_CLASS_UNCLASSIFIED = "unclassified"

ALL_FAILURE_CLASSES = {
    FAILURE_CLASS_CUSTODY,
    FAILURE_CLASS_BURDEN_FLOOR,
    FAILURE_CLASS_OWNER_ROUTE,
    FAILURE_CLASS_ACT_BODY_REF,
    FAILURE_CLASS_MRP,
    FAILURE_CLASS_FIELD_WITNESS,
    FAILURE_CLASS_PUBLIC_PROJECTION,
    FAILURE_CLASS_SIDECAR,
    FAILURE_CLASS_HANDOFF,
    FAILURE_CLASS_SEQUENCE,
    FAILURE_CLASS_NON_CLAIM,
    FAILURE_CLASS_UNCLASSIFIED,
}

# Classes that this checker can, in principle, ever emit as requiring a model
# rerun. Kept empty deliberately -- see boundary comment above.
MODEL_RERUN_FAILURE_CLASSES: set[str] = set()

STAGE_NUMBER_TOKEN_RE = re.compile(r"stage-(0[1-8])\b")
STAGES_INDEX_TOKEN_RE = re.compile(r"\bstages\[(\d+)\]")
HANDOFF_INDEX_TOKEN_RE = re.compile(r"\bhandoffs\[(\d+)\]")

# Stage-id substring -> failure_class, most-specific-first. A message is
# classified by the *earliest* (lowest stage number) contract it names; when
# a message names no stage at all it falls through to the record-level rules
# below (non_claims/model_scope -> non-claim; schema/case_id/JSON shape ->
# custody; artifact_bindings/proof_sidecars -> sidecar).
STAGE_ID_FAILURE_CLASS = {
    "stage-01-intake": FAILURE_CLASS_CUSTODY,
    "stage-02-layer-a-diagnostic-ir": FAILURE_CLASS_BURDEN_FLOOR,
    "stage-03-routing-owner-gate": FAILURE_CLASS_OWNER_ROUTE,
    "stage-04-burden-execution-act": FAILURE_CLASS_ACT_BODY_REF,
    "stage-05-mrp-reread-terminal-state": FAILURE_CLASS_MRP,
    "stage-06-field-witness-nar": FAILURE_CLASS_FIELD_WITNESS,
    "stage-07-release-output": FAILURE_CLASS_PUBLIC_PROJECTION,
    "stage-08-verifier-sidecars": FAILURE_CLASS_SIDECAR,
}
STAGE_NUMBER_FAILURE_CLASS = {
    "01": FAILURE_CLASS_CUSTODY,
    "02": FAILURE_CLASS_BURDEN_FLOOR,
    "03": FAILURE_CLASS_OWNER_ROUTE,
    "04": FAILURE_CLASS_ACT_BODY_REF,
    "05": FAILURE_CLASS_MRP,
    "06": FAILURE_CLASS_FIELD_WITNESS,
    "07": FAILURE_CLASS_PUBLIC_PROJECTION,
    "08": FAILURE_CLASS_SIDECAR,
}
# Non-claim / model-scope governance fields are record-level (validated
# against the whole record, not one stage payload) but their contract is
# owned by intake: a record is not admissible before its non-claims are
# declared. Substrings are matched case-sensitively against the raw message.
NON_CLAIM_MESSAGE_MARKERS = (
    "non_claims",
    "model_scope",
)
# artifact_bindings / retained-manifest / proof_sidecars errors are all
# stage-08 (verifier sidecars / retained-proof custody) territory even when
# the message does not literally say "stage-08".
SIDECAR_MESSAGE_MARKERS = (
    "artifact_bindings",
    "retained manifest",
    "retained_manifest",
    "proof_sidecars",
    "B.5.4.1",
)
CUSTODY_MESSAGE_MARKERS = (
    "record root must be a JSON object",
    "schema must be",
    "user_interface_preserved",
    "case_id is required",
    "JSON parse error",
)


def _stage_token(stage_id: str) -> str:
    return stage_id.split("-")[1]


def classify_failure_message(message: str) -> tuple[str, str]:
    """Return (failure_class, earliest_stage) for one checker error message.

    earliest_stage is a two-digit stage token ("01".."08") or "" when the
    violated contract is record-level rather than stage-scoped (custody /
    non-claim messages before any stage payload is even reachable).

    A message can name more than one stage (e.g. a handoff error names both
    sides of the pair, or an unrelated downstream check happens to mention an
    upstream stage id in passing); when that happens we take the lowest stage
    index, since that is the earliest contract actually violated.
    """
    candidate_indexes: list[int] = []

    for stage_id in STAGE_ID_FAILURE_CLASS:
        if stage_id in message:
            candidate_indexes.append(STAGE_ORDER.index(stage_id))

    for number in STAGE_NUMBER_TOKEN_RE.findall(message):
        candidate_indexes.append(int(number) - 1)

    for raw_index in STAGES_INDEX_TOKEN_RE.findall(message):
        idx = int(raw_index)
        if 0 <= idx < len(STAGE_ORDER):
            candidate_indexes.append(idx)

    if candidate_indexes:
        earliest_index = min(candidate_indexes)
        stage_id = STAGE_ORDER[earliest_index]
        stage_token = _stage_token(stage_id)
        if HANDOFF_INDEX_TOKEN_RE.search(message) and "handoff" in message.lower():
            return FAILURE_CLASS_HANDOFF, stage_token
        return STAGE_ID_FAILURE_CLASS[stage_id], stage_token

    if HANDOFF_INDEX_TOKEN_RE.search(message) and "handoff" in message.lower():
        return FAILURE_CLASS_HANDOFF, ""
    if "stage_order" in message or "stages must" in message or "stages contain" in message:
        return FAILURE_CLASS_SEQUENCE, "01"
    if any(marker in message for marker in SIDECAR_MESSAGE_MARKERS):
        return FAILURE_CLASS_SIDECAR, "08"
    if any(marker in message for marker in NON_CLAIM_MESSAGE_MARKERS):
        return FAILURE_CLASS_NON_CLAIM, "01"
    if any(marker in message for marker in CUSTODY_MESSAGE_MARKERS):
        return FAILURE_CLASS_CUSTODY, "01"
    return FAILURE_CLASS_UNCLASSIFIED, ""


def classify_record_errors(errors: list[str]) -> dict[str, Any]:
    """Classify a full record_errors() list into one explain-stage-failure diagnostic.

    Picks the single earliest-stage violation across all reported errors (not
    just the first error string), since error discovery order follows the
    checker's internal pipeline order, not stage order.
    """
    if not errors:
        return {"status": "pass"}
    best_class = FAILURE_CLASS_UNCLASSIFIED
    best_stage = ""
    best_index = len(STAGE_ORDER) + 1
    for message in errors:
        failure_class, stage_token = classify_failure_message(message)
        index = int(stage_token) - 1 if stage_token else len(STAGE_ORDER)
        if index < best_index:
            best_index = index
            best_class = failure_class
            best_stage = stage_token
    if not best_stage:
        best_stage = "01"
    downstream = [token for token in ("02", "03", "04", "05", "06", "07", "08") if token > best_stage]
    requires_model_rerun = best_class in MODEL_RERUN_FAILURE_CLASSES
    if requires_model_rerun:
        repair_lane = "model-observed"
    else:
        repair_lane = "no-model fixture/checker/runtime-contract repair"
    return {
        "stage": best_stage,
        "failure_class": best_class,
        "earliest_stage": best_stage,
        "downstream_invalidated": downstream,
        "requires_model_rerun": requires_model_rerun,
        "repair_lane": repair_lane,
    }


def explain_stage_failure_self_test(root: Path) -> list[str]:
    """Verify every invalid fixture classifies to its expected diagnostic.

    Expected diagnostics live in <fixture>.expected-explain.json sidecars next
    to the fixture (additive; created for fixtures that lacked one). Every
    valid fixture must classify to {"status": "pass"}. Any fixture that
    classifies to failure_class "unclassified" fails the self-test outright
    -- this keeps the message->class mapping total instead of letting new
    checker error strings silently fall through uncategorized.
    """
    errors: list[str] = []
    valid, invalid = iter_fixtures(root)
    for path in valid:
        payload, json_errors = read_json(path)
        all_errors = json_errors + (record_errors(path, payload) if payload is not None else ["unreadable"])
        if all_errors:
            # Not actually a valid fixture per the base checker; the main
            # fixture-suite pass already reports this, skip double-reporting.
            continue
        diagnostic = classify_record_errors(all_errors)
        if diagnostic != {"status": "pass"}:
            errors.append(f"{rel(path)}: expected status pass diagnostic, got {diagnostic}")
    for path in invalid:
        payload, json_errors = read_json(path)
        all_errors = json_errors + (record_errors(path, payload) if payload is not None else [])
        if not all_errors:
            # Not actually an invalid fixture per the base checker; the main
            # fixture-suite pass already reports this, skip double-reporting.
            continue
        diagnostic = classify_record_errors(all_errors)
        if diagnostic.get("failure_class") == FAILURE_CLASS_UNCLASSIFIED:
            errors.append(
                f"{rel(path)}: classify_record_errors produced unclassified failure_class for errors {all_errors[:3]}"
            )
        expected_path = path.parent / f"{path.stem}.expected-explain.json"
        if expected_path.exists():
            expected_payload, expected_read_errors = read_json(expected_path)
            if expected_read_errors:
                errors.extend(f"{rel(expected_path)}: {error}" for error in expected_read_errors)
                continue
            if expected_payload != diagnostic:
                errors.append(
                    f"{rel(path)}: explain diagnostic {diagnostic} does not match expected sidecar {expected_payload}"
                )
    return errors


def run_explain_stage_failure(root: Path, records: list[Path]) -> int:
    exit_code = 0
    paths = expand_records(records) if records else []
    if not paths:
        # No explicit records given: explain every invalid fixture, printing
        # one JSON line per fixture. This lets `--explain-stage-failure` be
        # demonstrated without requiring a caller to pick specific fixture
        # paths; the full pass/fail self-test lives in the bare (no-flag)
        # checker run via explain_stage_failure_self_test.
        _valid, invalid = iter_fixtures(root)
        paths = invalid
    for path in paths:
        if not path.exists():
            print(json.dumps({"status": "fail", "error": f"record path not found: {path}"}))
            exit_code = 1
            continue
        payload, found = read_json(path)
        found = list(found)
        found.extend(record_errors(path, payload) if payload is not None else [])
        diagnostic = classify_record_errors(found)
        print(json.dumps(diagnostic, sort_keys=True))
        if diagnostic.get("status") != "pass":
            exit_code = 1
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--records", nargs="*", type=Path, default=[])
    parser.add_argument(
        "--explain-stage-failure",
        action="store_true",
        help=(
            "Classify staged-runtime handshake failures into a first-failed-stage "
            "diagnostic (failure_class/earliest_stage/downstream_invalidated) instead "
            "of running the full fixture-suite check. Emits one JSON line per record."
        ),
    )
    args = parser.parse_args()

    if args.explain_stage_failure:
        return run_explain_stage_failure(args.root, args.records)

    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    records_checked = 0

    errors.extend(self_test_visible_optional_tooling_nonclaims())
    errors.extend(explain_stage_failure_self_test(args.root))

    valid, invalid = iter_fixtures(args.root)
    for path in valid:
        payload, found = read_json(path)
        found.extend(record_errors(path, payload) if payload is not None else [])
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        payload, found = read_json(path)
        found.extend(record_errors(path, payload) if payload is not None else [])
        if not found:
            errors.append(f"{rel(path)}: expected-invalid staged handshake fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in expand_records(args.records):
        if not path.exists():
            errors.append(f"{path}: record path not found")
            continue
        payload, found = read_json(path)
        found.extend(record_errors(path, payload) if payload is not None else [])
        if found:
            errors.extend(found)
        else:
            records_checked += 1

    if errors:
        print("staged runtime handshake check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("staged runtime handshake check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.records:
        print(f"Hosted records checked: {records_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
