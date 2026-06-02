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


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "staged-runtime-handshake"
SCHEMA = "staged-runtime-handshake-v1"
B5_SIDECAR_SCHEMA = "b5-retained-proof-mode-full-ir-sidecar-v1"
B5_SIDECAR_BUILDER = "tools/build_b5_full_ir_projection_sidecar.py"
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
REQUIRED_NON_CLAIMS = {
    "not_model_smoke",
    "not_runtime_default_emission_proof",
    "not_arbitrary_nl_ir_parser",
    "not_package_provenance",
    "not_guaranteed_t_lang_uptake",
}
PASS_STATUS = {"pass", "held", "partial"}
HELD_TERMINAL_STATES = {"hold_partial", "held", "held-with-reason", "partial", "carried-PARTIAL"}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


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


def sequence_errors(path: Path, record: dict[str, Any], stages: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    label = rel(path)
    stage_order = record.get("stage_order")
    if stage_order != STAGE_ORDER:
        errors.append(f"{label}: stage_order must contain the required stages exactly once and in order")

    stage_items = record.get("stages")
    if not isinstance(stage_items, list):
        return errors + [f"{label}: stages must be a list"]
    stage_ids = [stage.get("id") if isinstance(stage, dict) else None for stage in stage_items]
    if stage_ids != STAGE_ORDER:
        errors.append(f"{label}: stages must contain the required stage records exactly once and in order")
    if len(stages) != len(stage_items):
        errors.append(f"{label}: stages contain duplicate or malformed ids")

    for stage_id in STAGE_ORDER:
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
        missing = sorted(expected - set(checks))
        if missing and handoff.get("status") == "pass":
            errors.append(f"{hlabel}: pass handoff missing required check(s): {missing}")
        if handoff.get("status") not in PASS_STATUS and handoff.get("status") != "fail":
            errors.append(f"{hlabel}: status must be pass, held, partial, or fail")
    for pair in HANDOFF_CHECKS:
        if pair not in seen:
            errors.append(f"{label}: missing required handoff {pair[0]} -> {pair[1]}")
    return errors


def non_claim_errors(path: Path, record: dict[str, Any]) -> list[str]:
    non_claims = record.get("non_claims")
    label = f"{rel(path)}: non_claims"
    if not isinstance(non_claims, dict):
        return [f"{label}: must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_NON_CLAIMS - set(non_claims))
    if missing:
        errors.append(f"{label}: missing required non-claim(s): {missing}")
    for key in sorted(REQUIRED_NON_CLAIMS):
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


def semantic_errors(path: Path, stages: dict[str, dict[str, Any]]) -> list[str]:
    label = rel(path)
    errors: list[str] = []
    stage02 = stages.get("stage-02-layer-a-diagnostic-ir", {})
    stage03 = stages.get("stage-03-routing-owner-gate", {})
    stage04 = stages.get("stage-04-burden-execution-act", {})
    stage05 = stages.get("stage-05-mrp-reread-terminal-state", {})
    stage06 = stages.get("stage-06-field-witness-nar", {})
    stage07 = stages.get("stage-07-release-output", {})
    stage08 = stages.get("stage-08-verifier-sidecars", {})

    burden_floor = set(list_field(stage02, "burden_floor"))
    route_targets = set(list_field(stage03, "route_targets"))
    act_targets = set(list_field(stage04, "act_targets"))
    act_body_refs = set(list_field(stage04, "act_body_refs"))
    field_witness_body_refs = set(list_field(stage06, "field_witness_body_refs"))
    act_burdens = set(list_field(stage04, "act_burdens") or list_field(stage04, "act_targets"))
    nar_burdens = set(list_field(stage06, "nar_burdens"))

    if not burden_floor:
        errors.append(f"{label}: stage-02 burden_floor is required")
    if not route_targets:
        errors.append(f"{label}: stage-03 route_targets is required")
    if route_targets != burden_floor:
        errors.append(f"{label}: stage-03 route_targets must match stage-02 burden_floor")
    if act_targets != route_targets:
        errors.append(f"{label}: stage-04 act_targets must match stage-03 route_targets")
    if act_body_refs != field_witness_body_refs:
        errors.append(f"{label}: stage-06 field_witness_body_refs must match stage-04 act_body_refs")
    missing_nar = sorted(act_burdens - nar_burdens)
    if missing_nar:
        errors.append(f"{label}: stage-06 nar_burdens missing ACT burden(s): {missing_nar}")

    terminal_states = stage05.get("terminal_states")
    release_terminal_states = stage07.get("release_terminal_states")
    if not isinstance(terminal_states, dict) or not terminal_states:
        errors.append(f"{label}: stage-05 terminal_states must be a non-empty object")
    elif terminal_states != release_terminal_states:
        errors.append(f"{label}: stage-07 release_terminal_states must match stage-05 terminal_states")

    held_or_partial = any(stage.get("status") in {"held", "partial"} for stage in stages.values())
    if isinstance(terminal_states, dict):
        held_or_partial = held_or_partial or any(str(value) in HELD_TERMINAL_STATES for value in terminal_states.values())
    if held_or_partial and stage07.get("closure_claim") == "complete":
        errors.append(f"{label}: release must not claim complete closure after held/partial stage state")

    verifier_sidecars = stage08.get("verifier_sidecars")
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
