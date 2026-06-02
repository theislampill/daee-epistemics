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

import check_nla_decode_semantic_faithfulness as nla_decode
import check_retained_proof_corpus as retained


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
HELD_TERMINAL_STATES = {"hold_partial", "held", "held-with-reason", "partial", "carried-PARTIAL"}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ACT_BODY_REF_RE = re.compile(r"\bbody_ref=([^\s:⟧]+)")
ACT_OWNER_RE = re.compile(r"^⟦ACT\s+[^\[]+\[([^\.\]]+)\.[^\]]+\]")


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


def expected_stage_order(path: Path, record: dict[str, Any]) -> tuple[list[str], list[str]]:
    label = rel(path)
    mode = record.get("mode")
    stage_scope = record.get("stage_scope")
    if stage_scope is None:
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
    if stage_scope.get("not_release_output") is not True:
        errors.append(f"{label}: stage_scope.not_release_output must be true")
    if stage_scope.get("not_verifier_sidecars") is not True:
        errors.append(f"{label}: stage_scope.not_verifier_sidecars must be true")
    return expected, errors


def sequence_errors(path: Path, record: dict[str, Any], stages: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    label = rel(path)
    expected_order, found = expected_stage_order(path, record)
    errors.extend(found)
    stage_order = record.get("stage_order")
    if stage_order != expected_order:
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
            result.setdefault(burden_id, set()).add(owner_id)
    return result


def act_body_ref(row: str) -> str | None:
    match = ACT_BODY_REF_RE.search(row)
    return match.group(1) if match else None


def act_owner(row: str) -> str | None:
    match = ACT_OWNER_RE.match(row.strip())
    return match.group(1) if match else None


def stage04_act_errors(
    label: str,
    stage03: dict[str, Any] | None,
    stage04: dict[str, Any],
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
    if act_body_refs is None or not act_body_refs:
        errors.append(f"{label}: stage-04 act_body_refs must be a non-empty string list")
        act_body_refs = []
    if act_rows is None or not act_rows:
        errors.append(f"{label}: stage-04 act_rows must be a non-empty string list")
        act_rows = []

    missing_burdens = sorted(set(act_targets) - set(act_burdens))
    if missing_burdens:
        errors.append(f"{label}: stage-04 act_burdens missing act target(s): {missing_burdens}")
    duplicate_refs = sorted({ref for ref in act_body_refs if act_body_refs.count(ref) > 1})
    if duplicate_refs:
        errors.append(f"{label}: stage-04 act_body_refs must not contain duplicates: {duplicate_refs}")

    row_refs: set[str] = set()
    row_owners: set[str] = set()
    for index, row in enumerate(act_rows):
        row_label = f"{label}: stage-04 act_rows[{index}]"
        stripped = row.strip()
        if not stripped.startswith("⟦ACT"):
            errors.append(f"{row_label} must start with canonical '⟦ACT'")
        if "body_ref=" not in stripped:
            errors.append(f"{row_label} must contain body_ref=")
        if "Δ=" not in stripped:
            errors.append(f"{row_label} must contain Δ=")
        if "Land(" not in stripped:
            errors.append(f"{row_label} must contain Land(")
        if not stripped.endswith("⟧"):
            errors.append(f"{row_label} must close with '⟧'")
        ref = act_body_ref(stripped)
        if ref is None:
            errors.append(f"{row_label} must expose a parseable body_ref token")
        else:
            row_refs.add(ref)
            if ref not in act_body_refs:
                errors.append(f"{row_label} body_ref {ref!r} must appear in stage-04 act_body_refs")
        owner = act_owner(stripped)
        if owner:
            row_owners.add(owner)

    missing_row_refs = sorted(set(act_body_refs) - row_refs)
    if act_body_refs and missing_row_refs:
        errors.append(f"{label}: stage-04 act_body_refs missing from ACT rows: {missing_row_refs}")

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
                act_row_value = detail.get("act_row")
                if act_row_value is not None:
                    if not isinstance(act_row_value, str) or not act_row_value:
                        errors.append(f"{detail_label}.act_row must be a string when present")
                    elif act_row_value not in act_rows:
                        errors.append(f"{detail_label}.act_row must appear in act_rows")
    return errors


def semantic_errors(path: Path, stages: dict[str, dict[str, Any]]) -> list[str]:
    label = rel(path)
    errors: list[str] = []
    stage02 = stages.get("stage-02-layer-a-diagnostic-ir")
    stage03 = stages.get("stage-03-routing-owner-gate")
    stage04 = stages.get("stage-04-burden-execution-act")
    stage05 = stages.get("stage-05-mrp-reread-terminal-state")
    stage06 = stages.get("stage-06-field-witness-nar")
    stage07 = stages.get("stage-07-release-output")
    stage08 = stages.get("stage-08-verifier-sidecars")

    burden_floor = set(list_field(stage02 or {}, "burden_floor"))
    route_targets = set(list_field(stage03 or {}, "route_targets"))
    act_targets = set(list_field(stage04 or {}, "act_targets"))
    act_body_refs = set(list_field(stage04 or {}, "act_body_refs"))
    field_witness_body_refs = set(list_field(stage06 or {}, "field_witness_body_refs"))
    act_burdens = set(list_field(stage04 or {}, "act_burdens") or list_field(stage04 or {}, "act_targets"))
    nar_burdens = set(list_field(stage06 or {}, "nar_burdens"))

    if stage02 is not None and not burden_floor:
        errors.append(f"{label}: stage-02 burden_floor is required")
    if stage03 is not None:
        raw_route_targets = stage03.get("route_targets")
        if as_string_list(raw_route_targets) is None:
            errors.append(f"{label}: stage-03 route_targets must be a string list")
        details = stage03.get("route_target_details")
        if details is not None:
            if not isinstance(details, list):
                errors.append(f"{label}: stage-03 route_target_details must be a list when present")
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
        errors.extend(stage04_act_errors(label, stage03, stage04))
    if stage03 is not None and stage04 is not None and act_targets != route_targets:
        errors.append(f"{label}: stage-04 act_targets must match stage-03 route_targets")
    if stage04 is not None and stage06 is not None and act_body_refs != field_witness_body_refs:
        errors.append(f"{label}: stage-06 field_witness_body_refs must match stage-04 act_body_refs")
    missing_nar = sorted(act_burdens - nar_burdens) if stage04 is not None and stage06 is not None else []
    if missing_nar:
        errors.append(f"{label}: stage-06 nar_burdens missing ACT burden(s): {missing_nar}")

    terminal_states = stage05.get("terminal_states") if stage05 is not None else None
    release_terminal_states = stage07.get("release_terminal_states") if stage07 is not None else None
    if stage05 is not None and (not isinstance(terminal_states, dict) or not terminal_states):
        errors.append(f"{label}: stage-05 terminal_states must be a non-empty object")
    elif stage05 is not None and stage07 is not None and terminal_states != release_terminal_states:
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
    if not errors:
        errors.extend(semantic_errors(path, stages))
    else:
        errors.extend(semantic_errors(path, stages))
    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.json")), sorted((root / "invalid").glob("*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--records", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    records_checked = 0

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
