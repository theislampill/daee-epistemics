#!/usr/bin/env python3
"""Run a bounded staged current-skill smoke.

This is repo/dev harness tooling. It preserves the public `/daee-epistemics`
surface and writes staged scratch artifacts under `.daee/`. The no-model
self-test proves only harness wiring; it does not prove model behavior.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import build_staged_governed_output as staged_output
from closure_witness_lib import extract_embedded_field_witness, parse_closure_witness, status_head


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPLAY_RECORD = (
    ROOT / "tests" / "staged-runtime-handshake" / "valid" / "retained-a9-science-source.json"
)
DEFAULT_INPUT = (
    ROOT
    / "tests"
    / "retained-proof-corpus"
    / "v0.4.3.0-schema-light"
    / "valid"
    / "sidecar-backed"
    / "cases"
    / "a9-science-source"
    / "input.txt"
)

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

ACT_BODY_REF_RE = re.compile(r"\bbody_ref=([^\s:⟧]+)")
STAGE07_RELEASE_VALIDATION_KEYS = {
    "visible_opening_header",
    "nla_semantic_faithfulness",
    "field_witness_convergence",
    "formal_reread_state_semantics",
    "graph_completeness_json",
    "manual_smoke_render_contract",
    "owner_activation_ordering",
}
RELEASE_DIVERGENCE_STATES = {"neutral", "non-neutral"}
RELEASE_CURL_STATES = {"null", "resolved", "non-null"}
RELEASE_OUTPUT_MODE_ALIASES = {
    "single": "single-output",
    "single-output": "single-output",
    "compiled": "compiled-output",
    "compiled-output": "compiled-output",
}

STAGE_SPECS: dict[str, dict[str, Any]] = {
    "stage-01-intake": {
        "title": "Intake boundary",
        "produces": ["input_digest", "retained_input"],
        "requires": [],
        "instructions": (
            "Restate only the source boundary, case id, input digest, and retained input path. "
            "Do not answer the case yet."
        ),
    },
    "stage-02-layer-a-diagnostic-ir": {
        "title": "Layer A Diagnostic IR",
        "produces": ["burden_floor", "selected_n_frame", "live_registers"],
        "requires": ["input_digest"],
        "instructions": (
            "Identify the selected/held N-frame, the burden floor, and live registers. "
            "The canonical `selected_n_frame` field must be a string token. "
            "The canonical `burden_floor` and `live_registers` fields must be JSON "
            "arrays of strings. If richer diagnostic metadata is useful, put it in "
            "optional detail fields; do not replace the canonical string fields with "
            "objects. Do not release a final answer."
        ),
    },
    "stage-03-routing-owner-gate": {
        "title": "Routing / owner gate",
        "produces": ["route_targets", "owner_routes"],
        "requires": ["burden_floor"],
        "instructions": (
            "Route the burden floor to owner/TTP eligibility. Do not activate an owner "
            "unless the route is backed. The canonical `route_targets` field must be a "
            "JSON array of burden-id strings only, such as [\"B1\"]. If richer routing "
            "metadata is useful, put it in optional `route_target_details`; do not put "
            "objects in `route_targets`. The canonical `owner_routes` field must be a "
            "JSON array of objects with string `burden_id` and `owner_id` fields; richer "
            "owner-order evidence may be placed in optional detail fields."
        ),
    },
    "stage-04-burden-execution-act": {
        "title": "Burden execution / ACT",
        "produces": ["act_targets", "act_body_refs", "act_rows"],
        "requires": ["route_targets", "owner_routes"],
        "instructions": (
            "Produce canonical ACT handoff evidence for the routed burdens. "
            "`act_targets`, `act_burdens`, `act_body_refs`, and `act_rows` must be JSON "
            "arrays of strings. Every ACT row must be an exact canonical row beginning "
            "with `⟦ACT`, containing `body_ref=`, `Δ=`, and `Land(`, and closing with "
            "`⟧`. If richer per-row metadata is useful, put it in optional "
            "`act_row_details`; do not put objects in `act_rows` unless each object "
            "also carries an explicit string `act_row` for harness normalization."
        ),
    },
    "stage-05-mrp-reread-terminal-state": {
        "title": "MRP / reread / terminal state",
        "produces": ["terminal_states", "dependency_graph_edges", "no_new_resultant_proof"],
        "requires": ["act_rows"],
        "instructions": (
            "Produce Stage 05 JSON only. Do not write final answer prose, field_witness, "
            "Closing Formulation, release output, verifier sidecars, or proof artifacts. "
            "`terminal_states` must be a JSON object mapping every Stage 04 ACT burden id "
            "to a controlled terminal-state string. `dependency_graph_edges` must be a "
            "JSON array; use [] when no dependency edge remains. If no new resultant "
            "burden is live, set `no_new_resultant_proof` to true or to an object "
            "`{\"proved\": true, \"basis\": \"...\", \"unresolved_burdens\": []}`. "
            "If a generated/MRP burden exists, list it under `generated_burdens` and "
            "include it in `terminal_states`. If any burden remains unresolved, return "
            "`status` held or partial, not pass, and expose `unresolved_burdens`."
        ),
    },
    "stage-06-field-witness-nar": {
        "title": "field_witness / NAR",
        "produces": ["field_witness_body_refs", "nar_burdens", "normalized_activation_record"],
        "requires": ["terminal_states", "act_body_refs"],
        "instructions": (
            "Produce Stage 06 JSON only. Do not write a final answer, Restorative Response, "
            "Closing Formulation, sidecars, release output, Grapher output, or certificate "
            "evidence. `field_witness_body_refs` must be a JSON array of strings that exactly "
            "matches Stage 04 `act_body_refs`. `nar_burdens` must include Stage 04 ACT burdens "
            "and every Stage 05 terminal-state burden. `owner_activations` must be body-ref "
            "strings, or objects with explicit string `body_ref` so the harness can normalize "
            "them while preserving details under `owner_activation_details`. For model-mode "
            "Stage 06, do not use only `normalized_activation_record: true`; provide a "
            "structured `normalized_activation_record` object or `normalized_activation_record_details` "
            "with `n_frame`, `live_registers`, `burden_floor`, and `per_burden`. "
            "`per_burden` must be a JSON array/list of objects; each object must include "
            "a non-empty string `burden_id`. Do not emit `per_burden` as a burden-keyed object map. "
            "`register_deltas` must be parser-stable as an object or a list of objects with "
            "`register` and `delta`. If Stage 06 cannot honestly mirror ACT/terminal evidence, "
            "return status fail or partial; do not invent witness proof."
        ),
    },
}

HANDOFFS = [
    {
        "from": "stage-01-intake",
        "to": "stage-02-layer-a-diagnostic-ir",
        "checks": ["input_boundary_preserved"],
        "status": "pass",
    },
    {
        "from": "stage-02-layer-a-diagnostic-ir",
        "to": "stage-03-routing-owner-gate",
        "checks": ["burden_floor_to_route_targets", "live_registers_present", "n_frame_present"],
        "status": "pass",
    },
    {
        "from": "stage-03-routing-owner-gate",
        "to": "stage-04-burden-execution-act",
        "checks": ["owner_eligibility_backed", "route_targets_to_act_targets"],
        "status": "pass",
    },
    {
        "from": "stage-04-burden-execution-act",
        "to": "stage-05-mrp-reread-terminal-state",
        "checks": ["act_body_refs_present", "act_rows_present"],
        "status": "pass",
    },
    {
        "from": "stage-05-mrp-reread-terminal-state",
        "to": "stage-06-field-witness-nar",
        "checks": ["dependency_graph_explicit", "terminal_states_to_field_witness"],
        "status": "pass",
    },
    {
        "from": "stage-06-field-witness-nar",
        "to": "stage-07-release-output",
        "checks": ["field_witness_nar_convergence"],
        "status": "pass",
    },
    {
        "from": "stage-07-release-output",
        "to": "stage-08-verifier-sidecars",
        "checks": ["release_to_verifier_sidecars"],
        "status": "pass",
    },
]

NO_MODEL_NON_CLAIMS = {
    "not_model_smoke": True,
    "not_runtime_default_emission_proof": True,
    "not_arbitrary_nl_ir_parser": True,
    "not_package_provenance": True,
    "not_guaranteed_t_lang_uptake": True,
}
MODEL_NON_CLAIMS = {
    "not_model_smoke": False,
    "not_broad_model_behavior": True,
    "not_broad_model_matrix": True,
    "not_runtime_default_emission_proof": True,
    "not_arbitrary_nl_ir_parser": True,
    "not_package_provenance": True,
    "not_guaranteed_t_lang_uptake": True,
    "not_graphify_or_activegraph_proof": True,
}


class HarnessError(Exception):
    """User-facing harness failure."""


def rel(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_under_root(root: Path, value: str | Path, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise HarnessError(f"{label} must resolve inside repo root: {value}") from exc
    return resolved


def run_checked(command: list[str], *, cwd: Path, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def require_command_success(command: list[str], *, cwd: Path, input_text: str | None = None) -> str:
    result = run_checked(command, cwd=cwd, input_text=input_text)
    if result.returncode != 0:
        raise HarnessError(
            "Command failed: "
            + " ".join(command)
            + "\n"
            + result.stdout
        )
    return result.stdout


def validate_replay_record(root: Path, replay_record: Path) -> None:
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(replay_record),
        ],
        cwd=root,
    )


def validate_required_files(root: Path) -> dict[str, Path]:
    required = {
        "skill": root / "skill" / "SKILL.md",
        "handshake_checker": root / "tools" / "check_staged_runtime_handshake.py",
        "sidecar_builder": root / "tools" / "build_retained_proof_sidecars.py",
        "b5_sidecar_builder": root / "tools" / "build_b5_full_ir_projection_sidecar.py",
        "nla_checker": root / "tools" / "check_nla_decode_semantic_faithfulness.py",
        "field_witness_checker": root / "tools" / "check_field_witness_convergence.py",
        "formal_reread_checker": root / "tools" / "check_formal_reread_state_semantics.py",
        "graph_checker": root / "tools" / "check_graph_completeness.py",
        "manual_render_checker": root / "tools" / "check_manual_smoke_render_contract.py",
        "owner_ordering_checker": root / "tools" / "check_owner_activation_ordering.py",
    }
    missing = [f"{name}: {path}" for name, path in required.items() if not path.exists()]
    if missing:
        raise HarnessError("Required file(s) missing:\n- " + "\n- ".join(missing))
    return required


def compact_state(stages: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for stage in stages:
        stage_id = stage.get("id")
        if isinstance(stage_id, str):
            result[stage_id] = {
                key: value
                for key, value in stage.items()
                if key not in {"notes", "analysis", "rationale"}
            }
    return result


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1)
    else:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            stripped = stripped[start : end + 1]
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"Stage response was not a parseable JSON object: {exc}") from exc
    if not isinstance(parsed, dict):
        raise HarnessError("Stage response root must be a JSON object")
    return parsed


def normalized_stage(stage_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("id") != stage_id:
        raise HarnessError(f"{stage_id}: response id must be {stage_id!r}")
    status = payload.get("status")
    if status not in {"pass", "held", "partial", "fail"}:
        raise HarnessError(f"{stage_id}: status must be pass, held, partial, or fail")
    stage = dict(payload)
    spec = STAGE_SPECS.get(stage_id)
    if spec is not None:
        stage["produces"] = spec["produces"]
        stage["requires"] = spec["requires"]
    if stage_id == "stage-02-layer-a-diagnostic-ir":
        normalize_stage02_diagnostic_fields(stage)
    if stage_id == "stage-03-routing-owner-gate":
        normalize_stage03_route_targets(stage)
        normalize_stage03_owner_routes(stage)
    if stage_id == "stage-04-burden-execution-act":
        normalize_stage04_act_fields(stage)
    if stage_id == "stage-05-mrp-reread-terminal-state":
        normalize_stage05_mrp_fields(stage)
    if stage_id == "stage-06-field-witness-nar":
        normalize_stage06_witness_nar_fields(stage)
    return stage


def ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def normalization_object(stage: dict[str, Any]) -> dict[str, Any]:
    normalization = stage.get("normalization")
    if not isinstance(normalization, dict):
        normalization = {}
    return normalization


def non_empty_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def normalize_stage02_diagnostic_fields(stage: dict[str, Any]) -> None:
    normalization = normalization_object(stage)

    selected = stage.get("selected_n_frame")
    if isinstance(selected, dict):
        token = non_empty_string(selected.get("token") or selected.get("id") or selected.get("n_frame"))
        if token is None:
            raise HarnessError("stage-02 selected_n_frame object cannot be normalized without a string token")
        stage["selected_n_frame_details"] = selected
        stage["selected_n_frame"] = token
        normalization["selected_n_frame_from_details"] = True
    elif not isinstance(selected, str) or not selected.strip():
        raise HarnessError("stage-02 selected_n_frame must be a non-empty string token")

    floor = stage.get("burden_floor")
    if isinstance(floor, list) and floor and all(isinstance(item, str) and item for item in floor):
        stage["burden_floor"] = ordered_unique(list(floor))
    elif isinstance(floor, list) and floor and all(isinstance(item, dict) for item in floor):
        details = list(floor)
        burden_ids: list[str] = []
        for index, detail in enumerate(details):
            burden_id = non_empty_string(detail.get("burden_id") or detail.get("id"))
            if burden_id is None:
                raise HarnessError(
                    f"stage-02 burden_floor[{index}] object cannot be normalized without a string burden_id"
                )
            burden_ids.append(burden_id)
        stage["burden_floor_details"] = details
        stage["burden_floor"] = ordered_unique(burden_ids)
        normalization["burden_floor_from_details"] = True
        normalization["canonical_burden_floor"] = list(stage["burden_floor"])
    else:
        raise HarnessError("stage-02 burden_floor must be a non-empty list of burden-id strings")

    registers = stage.get("live_registers")
    if isinstance(registers, list) and registers and all(isinstance(item, str) and item for item in registers):
        stage["live_registers"] = ordered_unique(list(registers))
    elif isinstance(registers, list) and registers and all(isinstance(item, dict) for item in registers):
        details = list(registers)
        register_ids: list[str] = []
        for index, detail in enumerate(details):
            register_id = non_empty_string(detail.get("id") or detail.get("register"))
            if register_id is None:
                raise HarnessError(
                    f"stage-02 live_registers[{index}] object cannot be normalized without a string id"
                )
            register_ids.append(register_id)
        stage["live_register_details"] = details
        stage["live_registers"] = ordered_unique(register_ids)
        normalization["live_registers_from_details"] = True
        normalization["canonical_live_registers"] = list(stage["live_registers"])
    else:
        raise HarnessError("stage-02 live_registers must be a non-empty list of register strings")

    if normalization:
        stage["normalization"] = normalization


def normalize_stage03_route_targets(stage: dict[str, Any]) -> None:
    route_targets = stage.get("route_targets")
    if isinstance(route_targets, list) and all(isinstance(item, str) and item for item in route_targets):
        stage["route_targets"] = ordered_unique(list(route_targets))
        return
    if isinstance(route_targets, list) and route_targets and all(isinstance(item, dict) for item in route_targets):
        details = list(route_targets)
        burden_ids: list[str] = []
        for index, detail in enumerate(details):
            burden_id = detail.get("burden_id")
            if not isinstance(burden_id, str) or not burden_id.strip():
                raise HarnessError(
                    f"stage-03 route_targets[{index}] object cannot be normalized without a string burden_id"
                )
            burden_ids.append(burden_id)
        stage["route_target_details"] = details
        stage["route_targets"] = ordered_unique(burden_ids)
        normalization = normalization_object(stage)
        normalization["route_targets_from_details"] = True
        normalization["canonical_route_targets"] = list(stage["route_targets"])
        stage["normalization"] = normalization
        return
    raise HarnessError("stage-03 route_targets must be a non-empty list of burden-id strings")


def normalize_stage03_owner_routes(stage: dict[str, Any]) -> None:
    routes = stage.get("owner_routes")
    if isinstance(routes, list) and routes and all(isinstance(item, dict) for item in routes):
        canonical: list[dict[str, Any]] = []
        details: list[dict[str, Any]] = []
        for index, route in enumerate(routes):
            burden_id = non_empty_string(route.get("burden_id"))
            owner_id = non_empty_string(route.get("owner_id"))
            if burden_id is not None and owner_id is not None:
                canonical.append(dict(route))
                continue

            target = non_empty_string(route.get("target") or route.get("burden_id"))
            required = route.get("required")
            if target is None or not isinstance(required, list) or not required:
                raise HarnessError(
                    f"stage-03 owner_routes[{index}] must carry burden_id/owner_id or target plus required owner rows"
                )
            details.append(route)
            for required_index, required_row in enumerate(required):
                if not isinstance(required_row, dict):
                    raise HarnessError(
                        f"stage-03 owner_routes[{index}].required[{required_index}] must be an object"
                    )
                owner = non_empty_string(required_row.get("owner_id") or required_row.get("owner"))
                if owner is None:
                    raise HarnessError(
                        f"stage-03 owner_routes[{index}].required[{required_index}] cannot be normalized without owner"
                    )
                canonical_row: dict[str, Any] = {
                    "burden_id": target,
                    "owner_id": owner,
                }
                operation = non_empty_string(required_row.get("operation") or required_row.get("owner_operation"))
                if operation is not None:
                    canonical_row["operation"] = operation
                eligibility = non_empty_string(route.get("classification") or route.get("policy_id"))
                if eligibility is not None:
                    canonical_row["eligibility"] = eligibility
                canonical.append(canonical_row)

        if not canonical:
            raise HarnessError("stage-03 owner_routes must name at least one owner route")
        stage["owner_routes"] = canonical
        if details:
            stage["owner_route_details"] = details
            normalization = normalization_object(stage)
            normalization["owner_routes_from_required_details"] = True
            normalization["canonical_owner_routes"] = [
                {"burden_id": row.get("burden_id"), "owner_id": row.get("owner_id")} for row in canonical
            ]
            stage["normalization"] = normalization
        return
    raise HarnessError("stage-03 owner_routes must be a non-empty list of owner-route objects")


def extract_stage04_body_ref(act_row: str) -> str | None:
    match = ACT_BODY_REF_RE.search(act_row)
    return match.group(1) if match else None


def normalize_string_list(stage: dict[str, Any], key: str, *, required: bool) -> list[str]:
    value = stage.get(key)
    if value is None and not required:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise HarnessError(f"stage-04 {key} must be a string list")
    normalized = ordered_unique(list(value))
    stage[key] = normalized
    return normalized


def normalize_stage04_act_fields(stage: dict[str, Any]) -> None:
    normalize_string_list(stage, "act_targets", required=True)
    normalize_string_list(stage, "act_burdens", required=True)
    raw_rows = stage.get("act_rows")
    normalization = stage.get("normalization")
    if not isinstance(normalization, dict):
        normalization = {}

    if isinstance(raw_rows, list) and raw_rows and all(isinstance(item, str) and item for item in raw_rows):
        act_rows = ordered_unique(list(raw_rows))
        stage["act_rows"] = act_rows
    elif isinstance(raw_rows, list) and raw_rows and all(isinstance(item, dict) for item in raw_rows):
        details = list(raw_rows)
        act_rows = []
        for index, detail in enumerate(details):
            act_row = detail.get("act_row")
            if not isinstance(act_row, str) or not act_row.strip():
                raise HarnessError(
                    f"stage-04 act_rows[{index}] object cannot be normalized without a string act_row"
                )
            act_rows.append(act_row)
        stage["act_row_details"] = details
        stage["act_rows"] = ordered_unique(act_rows)
        normalization["act_rows_from_details"] = True
        normalization["canonical_act_rows"] = list(stage["act_rows"])
    else:
        raise HarnessError("stage-04 act_rows must be a non-empty list of ACT row strings")

    explicit_body_refs = stage.get("act_body_refs")
    if explicit_body_refs is None or explicit_body_refs == []:
        extracted = ordered_unique(
            [ref for ref in (extract_stage04_body_ref(row) for row in stage["act_rows"]) if ref]
        )
        if not extracted:
            raise HarnessError("stage-04 act_body_refs missing and no body_ref tokens were extractable from ACT rows")
        stage["act_body_refs"] = extracted
        normalization["act_body_refs_from_act_rows"] = True
    else:
        normalize_string_list(stage, "act_body_refs", required=True)

    if normalization:
        stage["normalization"] = normalization


def normalize_stage05_mrp_fields(stage: dict[str, Any]) -> None:
    terminal_states = stage.get("terminal_states")
    if not isinstance(terminal_states, dict) or not terminal_states:
        raise HarnessError("stage-05 terminal_states must be a non-empty object")
    if not all(isinstance(key, str) and key and isinstance(value, str) and value for key, value in terminal_states.items()):
        raise HarnessError("stage-05 terminal_states must map burden-id strings to terminal-state strings")

    edges = stage.get("dependency_graph_edges")
    if edges is None:
        graph = stage.get("dependency_graph")
        if isinstance(graph, dict) and isinstance(graph.get("edges"), list):
            stage["dependency_graph_edges"] = graph["edges"]
        else:
            raise HarnessError("stage-05 dependency_graph_edges must be a list")
    elif not isinstance(edges, list):
        raise HarnessError("stage-05 dependency_graph_edges must be a list")

    if "no_new_resultant_proof" not in stage:
        raise HarnessError("stage-05 no_new_resultant_proof is required")
    proof = stage.get("no_new_resultant_proof")
    if isinstance(proof, dict):
        if not isinstance(proof.get("proved"), bool):
            raise HarnessError("stage-05 no_new_resultant_proof.proved must be boolean")
        if proof.get("proved") is True and not str(proof.get("basis") or "").strip():
            raise HarnessError("stage-05 no_new_resultant_proof.basis is required when proved=true")
    elif not isinstance(proof, bool):
        raise HarnessError("stage-05 no_new_resultant_proof must be boolean or object")


def normalize_stage06_witness_nar_fields(stage: dict[str, Any]) -> None:
    field_refs = stage.get("field_witness_body_refs")
    if not isinstance(field_refs, list) or not field_refs or not all(isinstance(item, str) and item for item in field_refs):
        raise HarnessError("stage-06 field_witness_body_refs must be a non-empty string list")
    stage["field_witness_body_refs"] = ordered_unique(list(field_refs))

    nar_burdens = stage.get("nar_burdens")
    if not isinstance(nar_burdens, list) or not nar_burdens or not all(isinstance(item, str) and item for item in nar_burdens):
        raise HarnessError("stage-06 nar_burdens must be a non-empty string list")
    stage["nar_burdens"] = ordered_unique(list(nar_burdens))

    owner_activations = stage.get("owner_activations")
    if isinstance(owner_activations, list) and owner_activations and all(isinstance(item, str) and item for item in owner_activations):
        stage["owner_activations"] = ordered_unique(list(owner_activations))
    elif isinstance(owner_activations, list) and owner_activations and all(isinstance(item, dict) for item in owner_activations):
        details = list(owner_activations)
        refs: list[str] = []
        for index, detail in enumerate(details):
            body_ref = detail.get("body_ref")
            if not isinstance(body_ref, str) or not body_ref:
                raise HarnessError(f"stage-06 owner_activations[{index}] object cannot be normalized without body_ref")
            refs.append(body_ref)
        stage["owner_activation_details"] = details
        stage["owner_activations"] = ordered_unique(refs)
        normalization = stage.get("normalization")
        if not isinstance(normalization, dict):
            normalization = {}
        normalization["owner_activations_from_details"] = True
        normalization["canonical_owner_activations"] = list(stage["owner_activations"])
        stage["normalization"] = normalization
    else:
        raise HarnessError("stage-06 owner_activations must be body-ref strings or objects with body_ref")

    if "normalized_activation_record" not in stage:
        raise HarnessError("stage-06 normalized_activation_record is required")
    normalized = stage.get("normalized_activation_record")
    if isinstance(normalized, bool):
        if normalized is not True:
            raise HarnessError("stage-06 normalized_activation_record boolean must be true")
    elif isinstance(normalized, dict):
        normalize_stage06_nar_object(normalized, "stage-06 normalized_activation_record")
    else:
        raise HarnessError("stage-06 normalized_activation_record must be true or an object")
    details = stage.get("normalized_activation_record_details")
    if details is not None:
        normalize_stage06_nar_object(details, "stage-06 normalized_activation_record_details")

    if "register_deltas" not in stage:
        raise HarnessError("stage-06 register_deltas is required")
    register_deltas = stage.get("register_deltas")
    if isinstance(register_deltas, dict):
        for register, delta in register_deltas.items():
            if not isinstance(register, str) or not register:
                raise HarnessError("stage-06 register_deltas keys must be non-empty strings")
            if isinstance(delta, str):
                if not delta:
                    raise HarnessError("stage-06 register_deltas string values must be non-empty")
            elif isinstance(delta, list):
                if not all(isinstance(item, str) and item for item in delta):
                    raise HarnessError("stage-06 register_deltas list values must be non-empty strings")
            else:
                raise HarnessError("stage-06 register_deltas object values must be strings or string lists")
    elif isinstance(register_deltas, list):
        for index, item in enumerate(register_deltas):
            if not isinstance(item, dict):
                raise HarnessError(f"stage-06 register_deltas[{index}] must be an object")
            if not isinstance(item.get("register"), str) or not item["register"]:
                raise HarnessError(f"stage-06 register_deltas[{index}].register must be a non-empty string")
            if not isinstance(item.get("delta"), str) or not item["delta"]:
                raise HarnessError(f"stage-06 register_deltas[{index}].delta must be a non-empty string")
    else:
        raise HarnessError("stage-06 register_deltas must be an object or list")


def normalize_stage06_nar_object(value: dict[str, Any], label: str) -> None:
    if not isinstance(value.get("n_frame"), str) or not value["n_frame"].strip():
        raise HarnessError(f"{label}.n_frame must be a non-empty string")
    for key in ("live_registers", "burden_floor"):
        raw = value.get(key)
        if not isinstance(raw, list) or not all(isinstance(item, str) and item for item in raw):
            raise HarnessError(f"{label}.{key} must be a string list")
        value[key] = ordered_unique(list(raw))
    rows = value.get("per_burden")
    if isinstance(rows, dict) and rows:
        normalized_rows: list[dict[str, Any]] = []
        for raw_burden_id, payload in rows.items():
            if not isinstance(raw_burden_id, str) or not raw_burden_id:
                raise HarnessError(f"{label}.per_burden map keys must be non-empty burden ids")
            if not isinstance(payload, dict):
                raise HarnessError(f"{label}.per_burden[{raw_burden_id}] must be an object")
            row = dict(payload)
            row.setdefault("burden_id", raw_burden_id)
            normalized_rows.append(row)
        rows = normalized_rows
        value["per_burden"] = rows
    if not isinstance(rows, list) or not rows:
        raise HarnessError(f"{label}.per_burden must be a non-empty object list")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise HarnessError(f"{label}.per_burden[{index}] must be an object")
        if not isinstance(row.get("burden_id"), str) or not row["burden_id"]:
            raise HarnessError(f"{label}.per_burden[{index}].burden_id must be a non-empty string")


def list_field(stage: dict[str, Any] | None, key: str) -> list[str]:
    if not isinstance(stage, dict):
        return []
    value = stage.get(key)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def stage_by_id(stages: list[dict[str, Any]], stage_id: str) -> dict[str, Any] | None:
    for stage in stages:
        if stage.get("id") == stage_id:
            return stage
    return None


def validate_incremental_handoffs(stages: list[dict[str, Any]]) -> None:
    stage02 = stage_by_id(stages, "stage-02-layer-a-diagnostic-ir")
    stage03 = stage_by_id(stages, "stage-03-routing-owner-gate")
    stage04 = stage_by_id(stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(stages, "stage-05-mrp-reread-terminal-state")
    stage06 = stage_by_id(stages, "stage-06-field-witness-nar")
    if stage02 and stage03:
        if set(list_field(stage02, "burden_floor")) != set(list_field(stage03, "route_targets")):
            raise HarnessError("stage-03 route_targets must match stage-02 burden_floor")
    if stage03 and stage04:
        if set(list_field(stage03, "route_targets")) != set(list_field(stage04, "act_targets")):
            raise HarnessError("stage-04 act_targets must match stage-03 route_targets")
    if stage04 and stage06:
        if list_field(stage04, "act_body_refs") != list_field(stage06, "field_witness_body_refs"):
            raise HarnessError("stage-06 field_witness_body_refs must match stage-04 act_body_refs")
        act_burdens = set(list_field(stage04, "act_burdens") or list_field(stage04, "act_targets"))
        nar_burdens = set(list_field(stage06, "nar_burdens"))
        missing = sorted(act_burdens - nar_burdens)
        if missing:
            raise HarnessError(f"stage-06 nar_burdens missing ACT burden(s): {missing}")
        owner_activations = list_field(stage06, "owner_activations")
        if owner_activations != list_field(stage06, "field_witness_body_refs"):
            raise HarnessError("stage-06 owner_activations must mirror field_witness_body_refs")
    if stage05 and stage06:
        terminal_states = stage05.get("terminal_states")
        if isinstance(terminal_states, dict):
            missing = sorted(set(terminal_states) - set(list_field(stage06, "nar_burdens")))
            if missing:
                raise HarnessError(f"stage-06 nar_burdens missing terminal-state burden(s): {missing}")
    if stage05 and stage05.get("terminal_states") in ({}, None):
        raise HarnessError("stage-05 terminal_states must be non-empty")
    if stage04 and stage05:
        terminal_states = stage05.get("terminal_states")
        if not isinstance(terminal_states, dict):
            raise HarnessError("stage-05 terminal_states must be a non-empty object")
        act_burdens = set(list_field(stage04, "act_burdens") or list_field(stage04, "act_targets"))
        missing = sorted(act_burdens - set(terminal_states))
        if missing:
            raise HarnessError(f"stage-05 terminal_states missing ACT burden(s): {missing}")
        if not isinstance(stage05.get("dependency_graph_edges"), list):
            raise HarnessError("stage-05 dependency_graph_edges must be a list")
        proof = stage05.get("no_new_resultant_proof")
        unresolved = stage05.get("unresolved_burdens") or []
        if proof is True and unresolved:
            raise HarnessError("stage-05 no_new_resultant_proof true conflicts with unresolved_burdens")
        if isinstance(proof, dict) and proof.get("proved") is True and proof.get("unresolved_burdens"):
            raise HarnessError("stage-05 no_new_resultant_proof proved=true conflicts with unresolved_burdens")


def stage_prompt(
    *,
    root: Path,
    stage_id: str,
    case_name: str,
    raw_input_path: Path,
    input_text: str,
    input_digest: str,
    skill_hash: str,
    previous_stages: list[dict[str, Any]],
) -> str:
    spec = STAGE_SPECS[stage_id]
    previous = json.dumps(compact_state(previous_stages), ensure_ascii=False, indent=2)
    return f"""Runtime SHA256: {skill_hash}

You are executing one bounded repo/dev staged current-skill smoke for daee-epistemics.
Use the generated runtime surface at `skill/SKILL.md` as the governing skill source.
This is stage only: {stage_id} — {spec['title']}.

Hard boundaries:
- Do not package, tag, upload, publish provenance, or create release assets.
- Do not claim broad model behavior, arbitrary NL-to-IR parsing, guaranteed T_lang uptake, or Graphify/ActiveGraph proof.
- Preserve the public `/daee-epistemics` interface; stage artifacts are repo/dev scratch only.

Case: {case_name}
Raw input path: {rel(raw_input_path, root)}
Input SHA256: {input_digest}

Raw input:
```text
{input_text}
```

Previous validated compact stage state:
```json
{previous}
```

Stage task:
{spec['instructions']}

Return exactly one JSON object and nothing else. Required shape:
{{
  "id": "{stage_id}",
  "status": "pass",
  "...": "stage-specific fields"
}}

Required stage-specific fields:
- produces: {spec['produces']}
- requires: {spec['requires']}

If this stage cannot be honestly completed, return the same JSON shape with
`"status": "fail"` and an `"error"` string. Do not invent downstream proof.
"""


def release_prompt(
    *,
    root: Path,
    case_name: str,
    raw_input_path: Path,
    input_text: str,
    input_digest: str,
    skill_hash: str,
    previous_stages: list[dict[str, Any]],
) -> str:
    previous = json.dumps(compact_state(previous_stages), ensure_ascii=False, indent=2)
    return f"""Runtime SHA256: {skill_hash}

You are executing stage-07-release-output for one bounded staged current-skill smoke.
Use the generated runtime surface at `skill/SKILL.md` as the governing skill source.

Public interface boundary:
- Preserve `/daee-epistemics` governed output shape.
- Preserve the visible opening noetic-field read/header.
- Do not expose raw dev harness internals as a new public mode.

Case: {case_name}
Raw input path: {rel(raw_input_path, root)}
Input SHA256: {input_digest}

Raw input:
```text
{input_text}
```

Validated compact stage state:
```json
{previous}
```

Produce the final governed `output.md` only.

Required public output surface:
- Preserve the normal visible noetic-field opening/header.
- Include the compact Layer A / Diagnostic IR opening header.
- Include Layer B / ACT rows consistent with the validated Stage 04 state.
- Include MRP/reread/terminal-state surface consistent with Stage 05.
- Include parser-stable field_witness/NAR evidence consistent with Stage 06.
- Include visible Closure/Reconstruction Witness diagnostics for `∇·B` and
  `∇×κ`, and include matching machine values in
  `field_witness.coverage_proof.divergence_check` and
  `field_witness.coverage_proof.curl_check`.
- The visible `∇·B` status and coverage `divergence_check` status must be
  identical after status-head normalization.
- The visible `∇×κ` status and coverage `curl_check` status must be
  identical after status-head normalization.
- Include Restorative Response.
- Include Closing Formulation.

Do not include JSON-only stage scratch as the public answer.
Do not include commentary about this harness.
Do not build or claim verifier sidecars, collapse certificates, Grapher output,
B.5 projection sidecars, retained promotion, package/provenance, guaranteed
uptake, broad model behavior, broad A/B/C/D closure, Graphify proof, or
ActiveGraph proof.
"""


def normalize_release_output_mode(value: str) -> str:
    try:
        return RELEASE_OUTPUT_MODE_ALIASES[value]
    except KeyError as exc:
        allowed = ", ".join(sorted(RELEASE_OUTPUT_MODE_ALIASES))
        raise HarnessError(f"Unknown release output mode {value!r}; expected one of {allowed}") from exc


def compiled_release_section_plan(target_output_kb: int | None) -> list[tuple[str, str]]:
    target = max(0, int(target_output_kb or 0))
    act_chunks = 1 if target <= 0 else max(1, min(8, (target + 24) // 25))
    return [
        ("opening", "visible_opening"),
        ("layer-a-diagnostic-ir", "layer_a_diagnostic_ir"),
        *[(f"act-body-{index}", "layer_b_act") for index in range(1, act_chunks + 1)],
        ("mrp-reread-terminal", "mrp_reread_terminal"),
        ("field-witness-nar", "field_witness_nar"),
        ("restorative-response", "restorative_response"),
        ("closing-formulation", "closing_formulation"),
    ]


def release_section_prompt(
    *,
    root: Path,
    case_name: str,
    raw_input_path: Path,
    input_text: str,
    input_digest: str,
    skill_hash: str,
    previous_stages: list[dict[str, Any]],
    section_id: str,
    section_role: str,
    section_number: int,
    section_count: int,
    target_output_kb: int | None,
) -> str:
    previous = json.dumps(compact_state(previous_stages), ensure_ascii=False, indent=2)
    target = max(0, int(target_output_kb or 0))
    section_floor = max(0, (target * 1024 + section_count - 1) // section_count) if target else 0
    role_guidance = {
        "visible_opening": (
            "Write only the visible opening for the governed answer. It must contain the exact banner "
            "`NOETIC FIELD EXECUTION` or the token `noetic-field`, plus the field/read/state surface a "
            "normal `/daee-epistemics` answer exposes. Do not include Layer B, field_witness, "
            "Restorative Response, or Closing Formulation."
        ),
        "layer_a_diagnostic_ir": (
            "Write only the compact Layer A / Diagnostic IR public surface. It must include a Layer A "
            "Compact DSL/IR or Diagnostic IR header, B_LA, B_MRP, B_total, and Initial burden set "
            "ledger lines. Do not include raw dev harness internals or downstream proof claims."
        ),
        "layer_b_act": (
            "Write only this bounded Layer B / ACT section. Include a governed Layer B header, "
            "ACT-readable rows, body_ref tokens, local operation/result prose, and Land(...) surfaces "
            "consistent with Stage 04. Expand the operation bodies instead of summarizing them. "
            "Do not include MRP, field_witness, Restorative Response, or Closing Formulation."
        ),
        "mrp_reread_terminal": (
            "Write only the MRP/reread/terminal-state section consistent with Stage 05. It must include "
            "`[Mid-Reread Pressure]`, `R(H,Delta)` or `R(H,Δ)`, terminal states, `MRP route result type`, "
            "`Graph delta`, `Field diagnostics`, and the STOP/HOLD/PARTIAL/RECURSE route consequence. "
            "Do not include final verifier sidecars or retained proof claims."
        ),
        "field_witness_nar": (
            "Write only the Closure/Reconstruction Witness plus parser-stable `field_witness` JSON. "
            "The section must contain a line that begins exactly `field_witness`, then a JSON object "
            "with `B_LA`, `B_MRP`, `B_total`, `coverage_proof`, `owner_activations`, "
            "`normalized_activation_record`, and any generated-burden/formal-reread mirrors required "
            "by Stage 06. The visible divergence/curl statuses must match "
            "`field_witness.coverage_proof.divergence_check` and `.curl_check`. Do not use prose-only "
            "`Field Witness` or prose-only `Normalized Activation Record` labels."
        ),
        "restorative_response": (
            "Write only the Restorative Response section. Do not include Closing Formulation here. "
            "Do not claim guaranteed uptake, package/provenance, sidecar proof, retained promotion, "
            "broad model behavior, or broad A/B/C/D closure."
        ),
        "closing_formulation": (
            "Write only the Closing Formulation section. It must include explicit high-mass slots for "
            "Established failure, Restored criterion/orientation, and Scoped boundary or Reopen boundary. "
            "Do not claim guaranteed uptake, package/provenance, sidecar proof, retained promotion, "
            "broad model behavior, or broad A/B/C/D closure."
        ),
    }
    target_line = ""
    if target:
        target_line = (
            f"\nOverall compiled output floor: at least {target}KB across {section_count} sections. "
            f"This section's rough share is {section_floor} bytes; expand governed content enough to "
            "help the assembled output meet the floor. The harness will fail the assembly if the "
            "compiled output is under target.\n"
        )
    return f"""Runtime SHA256: {skill_hash}

You are executing one bounded section of stage-07-release-output for a staged
current-skill smoke. The final public `output.md` will be assembled by repo
tooling from hash-checked section files; do not try to write the whole answer
in this one message.

Public interface boundary:
- Preserve `/daee-epistemics` governed output shape across the assembled file.
- Do not expose raw dev harness internals as a new public mode.
- Do not include commentary about this harness, section manifest, or compiler.
- Do not build or claim verifier sidecars, collapse certificates, Grapher output,
  B.5 projection sidecars, retained promotion, package/provenance, guaranteed
  uptake, broad model behavior, broad A/B/C/D closure, Graphify proof, or
  ActiveGraph proof.

Case: {case_name}
Raw input path: {rel(raw_input_path, root)}
Input SHA256: {input_digest}
Section: {section_number} of {section_count}
Section id: {section_id}
Section role: {section_role}
{target_line}
Raw input:
```text
{input_text}
```

Validated compact stage state:
```json
{previous}
```

Section task:
{role_guidance[section_role]}

Return only the public governed-output text for this section. Do not wrap it in
JSON or code fences. Do not mention that this is a section unless the normal
public governed answer itself needs a section heading.
"""


def write_compiled_release_manifest(
    *,
    root: Path,
    manifest_path: Path,
    case_name: str,
    raw_input_path: Path,
    section_entries: list[dict[str, str]],
    output_path: Path,
    target_output_kb: int = 0,
) -> None:
    manifest_dir = manifest_path.parent
    write_json(
        manifest_path,
        {
            "schema": staged_output.ASSEMBLY_SCHEMA,
            "case_id": case_name,
            "source_input": rel(raw_input_path, root),
            "sections": [
                {
                    "id": entry["id"],
                    "path": rel(Path(entry["path"]), manifest_dir),
                    "sha256": entry["sha256"],
                    "role": entry["role"],
                }
                for entry in section_entries
            ],
            "output": {"path": rel(output_path, manifest_dir), "target_output_kb": int(target_output_kb or 0)},
            "non_claims": {
                "not_release_provenance": True,
                "not_model_behavior_by_itself": True,
                "not_sidecar_proof": True,
            },
        },
    )


def split_text_for_compiled_self_test(text: str) -> list[tuple[str, str, str]]:
    plan = [
        ("opening", "visible_opening"),
        ("layer-a-diagnostic-ir", "layer_a_diagnostic_ir"),
        ("act-body", "layer_b_act"),
        ("mrp-reread-terminal", "mrp_reread_terminal"),
        ("field-witness-nar", "field_witness_nar"),
        ("restorative-response", "restorative_response"),
        ("closing-formulation", "closing_formulation"),
    ]
    lines = text.splitlines(keepends=True)
    if len(lines) < len(plan):
        raise HarnessError("Compiled-mode self-test source output is too small to split into required sections")
    chunk_size = max(1, (len(lines) + len(plan) - 1) // len(plan))
    sections: list[tuple[str, str, str]] = []
    cursor = 0
    for index, (section_id, role) in enumerate(plan):
        remaining_sections = len(plan) - index
        remaining_lines = len(lines) - cursor
        take = max(1, remaining_lines - (remaining_sections - 1)) if remaining_sections == 1 else chunk_size
        chunk = "".join(lines[cursor : cursor + take])
        cursor += take
        sections.append((section_id, role, chunk))
    if cursor < len(lines):
        section_id, role, chunk = sections[-1]
        sections[-1] = (section_id, role, chunk + "".join(lines[cursor:]))
    return sections


def run_compiled_release_self_test(
    *,
    root: Path,
    run_dir: Path,
    replay_output_path: Path,
    replay_record: Path,
    replay: dict[str, Any],
    stage07_validation: dict[str, str],
) -> None:
    compiled_dir = run_dir / "compiled-release-self-test"
    source_text = replay_output_path.read_text(encoding="utf-8", errors="replace")
    manifest_path = staged_output.manifest_for_sections(
        compiled_dir,
        case_id="self-test-a9-science-source-stage07-compiled",
        source_input=rel(replay_output_path, root),
        section_specs=split_text_for_compiled_self_test(source_text),
    )
    assembly_record = staged_output.assemble_manifest(manifest_path, root=root)
    compiled_output_path = root / assembly_record["output"]["path"]
    compiled_validation = run_release_validators(root, compiled_output_path)
    compiled_diagnostics = build_release_field_diagnostics(compiled_output_path)
    if compiled_diagnostics.get("matches") is not True:
        raise HarnessError("Compiled-mode self-test output did not produce matching release_field_diagnostics")

    stage07_local_record = base_record(
        "self-test-a9-science-source-stage07-compiled",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-07-release-output",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage07-compiled",
            replay_record,
            stop_after_stage="stage-07-release-output",
        ),
    )
    stage07_stage = dict(replay["stages"][6])
    stage07_stage["release_output"] = {
        "path": assembly_record["output"]["path"],
        "sha256": assembly_record["output"]["sha256"],
    }
    stage07_stage["release_validation"] = dict(compiled_validation)
    stage07_stage["release_field_diagnostics"] = dict(compiled_diagnostics)
    stage07_stage["release_output_mode"] = "compiled-output"
    stage07_stage["assembly_manifest"] = dict(assembly_record["assembly_manifest"])
    stage07_stage["assembly_hashes"] = dict(assembly_record["hash_record"])
    stage07_local_record["stages"] = [*replay["stages"][:6], stage07_stage]
    compiled_record_path = compiled_dir / "staged-handoff-stage07-compiled-record.json"
    write_json(compiled_record_path, stage07_local_record)
    validate_replay_record(root, compiled_record_path)
    if set(compiled_validation) != set(stage07_validation):
        raise HarnessError("Compiled-mode self-test validator keys drifted from single-output Stage 07 keys")


def invoke_codex(root: Path, model: str, prompt: str, output_path: Path, log_path: Path) -> int:
    codex = shutil.which("codex")
    if codex is None:
        raise HarnessError("codex CLI not found on PATH; model smoke is blocked by harness/credential environment")
    command = [
        codex,
        "exec",
        "-C",
        str(root),
        "-s",
        "read-only",
        "-m",
        model,
        "-c",
        'approval_policy="never"',
        "-c",
        'shell_environment_policy.inherit="all"',
        "--output-last-message",
        str(output_path),
        "-",
    ]
    result = run_checked(command, cwd=root, input_text=prompt)
    write_text(log_path, result.stdout)
    return result.returncode


def stage_order_for_stop(stop_after_stage: str | None) -> list[str]:
    if stop_after_stage is None:
        return list(STAGE_ORDER)
    if stop_after_stage not in STAGE_ORDER:
        raise HarnessError(f"Unknown stop-after-stage value: {stop_after_stage}")
    return STAGE_ORDER[: STAGE_ORDER.index(stop_after_stage) + 1]


def handoffs_for_stage_order(stage_order: list[str]) -> list[dict[str, Any]]:
    included = set(stage_order)
    return [dict(handoff) for handoff in HANDOFFS if handoff["from"] in included and handoff["to"] in included]


def model_scope(case_name: str, replay_record: Path, *, stop_after_stage: str | None) -> dict[str, Any]:
    return {
        "type": "focused-current-skill-stage-smoke" if stop_after_stage else "focused-current-skill-smoke",
        "case_count": 1,
        "case_family": "a9-science-source" if "a9-science-source" in case_name else case_name,
        "retained_replay_target": rel(replay_record),
    }


def base_record(
    case_name: str,
    mode: str,
    *,
    not_model_smoke: bool,
    stop_after_stage: str | None = None,
    model_scope_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stage_order = stage_order_for_stop(stop_after_stage)
    non_claims = dict(NO_MODEL_NON_CLAIMS if not_model_smoke else MODEL_NON_CLAIMS)
    non_claims["not_model_smoke"] = not_model_smoke
    record: dict[str, Any] = {
        "schema": "staged-runtime-handshake-v1",
        "case_id": case_name,
        "mode": mode,
        "user_interface_preserved": True,
        "stage_order": stage_order,
        "stages": [],
        "handoffs": handoffs_for_stage_order(stage_order),
        "non_claims": non_claims,
    }
    if stop_after_stage is not None:
        stop_index = STAGE_ORDER.index(stop_after_stage)
        release_index = STAGE_ORDER.index("stage-07-release-output")
        verifier_index = STAGE_ORDER.index("stage-08-verifier-sidecars")
        record["stage_scope"] = {
            "stop_after_stage": stop_after_stage,
            "stage_count": len(stage_order),
            "not_verifier_sidecars": stop_index < verifier_index,
        }
        if stop_index < release_index:
            record["stage_scope"]["not_release_output"] = True
        else:
            record["stage_scope"]["release_output"] = True
    if model_scope_payload is not None:
        record["model_scope"] = model_scope_payload
    return record


def write_hash_record(
    path: Path,
    *,
    root: Path,
    case_name: str,
    mode: str,
    model: str | None,
    skill_path: Path,
    replay_record: Path,
    raw_input_path: Path,
    run_dir: Path,
    stage_files: list[Path],
    handoff_record: Path | None,
    output_path: Path | None,
    sidecar_paths: list[Path],
    verdict: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "staged-current-skill-smoke-hashes-v1",
        "case_name": case_name,
        "mode": mode,
        "model": model,
        "verdict": verdict,
        "run_dir": rel(run_dir, root),
        "skill": {"path": rel(skill_path, root), "sha256": sha256_file(skill_path)},
        "replay_record": {"path": rel(replay_record, root), "sha256": sha256_file(replay_record)},
        "raw_input": {"path": rel(raw_input_path, root), "sha256": sha256_file(raw_input_path)},
        "stage_artifacts": [
            {"path": rel(path_item, root), "sha256": sha256_file(path_item)}
            for path_item in stage_files
            if path_item.exists()
        ],
        "handoff_record": None,
        "output": None,
        "sidecars": [
            {"path": rel(path_item, root), "sha256": sha256_file(path_item)}
            for path_item in sidecar_paths
            if path_item.exists()
        ],
        "non_claims": {
            "not_package_provenance": True,
            "not_retained_promotion": True,
            "not_broad_model_matrix": True,
            "not_graphify_or_activegraph_proof": True,
        },
    }
    if handoff_record is not None and handoff_record.exists():
        payload["handoff_record"] = {"path": rel(handoff_record, root), "sha256": sha256_file(handoff_record)}
    if output_path is not None and output_path.exists():
        payload["output"] = {"path": rel(output_path, root), "sha256": sha256_file(output_path)}
    write_json(path, payload)
    return payload


def run_self_test(root: Path) -> int:
    files = validate_required_files(root)
    replay_record = DEFAULT_REPLAY_RECORD
    raw_input = DEFAULT_INPUT
    validate_replay_record(root, replay_record)
    replay = load_json(replay_record)
    run_dir = root / ".daee" / "validation" / f"staged-current-skill-harness-self-test-{uuid.uuid4().hex}"
    stages_dir = run_dir / "stages"
    stages_dir.mkdir(parents=True, exist_ok=True)
    stage_files: list[Path] = []
    for stage in replay["stages"]:
        stage_path = stages_dir / f"{stage['id']}.response.json"
        write_json(stage_path, stage)
        stage_files.append(stage_path)
    record_path = run_dir / "staged-handoff-record.json"
    write_json(record_path, replay)
    validate_replay_record(root, record_path)
    hash_path = run_dir / "staged-smoke.hashes.json"
    write_hash_record(
        hash_path,
        root=root,
        case_name="self-test-a9-science-source",
        mode="self-test-no-model",
        model=None,
        skill_path=files["skill"],
        replay_record=replay_record,
        raw_input_path=raw_input,
        run_dir=run_dir,
        stage_files=stage_files,
        handoff_record=record_path,
        output_path=None,
        sidecar_paths=[],
        verdict="SELF_TEST_NO_MODEL_PASS",
    )
    loaded_hashes = load_json(hash_path)
    if loaded_hashes.get("mode") != "self-test-no-model":
        raise HarnessError("Self-test hash record did not preserve self-test mode")
    if loaded_hashes.get("model") is not None:
        raise HarnessError("Self-test hash record must not claim a model invocation")
    normalized_stage02 = normalized_stage(
        "stage-02-layer-a-diagnostic-ir",
        {
            "id": "stage-02-layer-a-diagnostic-ir",
            "status": "pass",
            "selected_n_frame": {
                "token": "science-only-source-order-warrant",
                "basis": [
                    "scientific explanations treated as the only knowledge source",
                    "science-measurability treated as the criterion for whether an answer counts",
                ],
            },
            "live_registers": [
                {
                    "id": "xi",
                    "functions": ["warrant-authority", "source-order", "proof-tribunal"],
                    "basis": "science is installed as the only admissible knowledge source and criterion",
                },
                {
                    "id": "kappa",
                    "functions": ["dependency-collapse"],
                    "basis": "the only-science standard requires a self-grounding/dependency check before closure",
                },
            ],
            "burden_floor": [
                {
                    "burden_id": "B1",
                    "label": "science-only source-order/warrant standard",
                    "register_types": ["xi", "kappa"],
                }
            ],
        },
    )
    if normalized_stage02.get("selected_n_frame") != "science-only-source-order-warrant":
        raise HarnessError("Self-test failed to normalize rich Stage 02 selected_n_frame into token")
    if normalized_stage02.get("live_registers") != ["xi", "kappa"]:
        raise HarnessError("Self-test failed to normalize rich Stage 02 live_registers into register ids")
    if normalized_stage02.get("burden_floor") != ["B1"]:
        raise HarnessError("Self-test failed to normalize rich Stage 02 burden_floor into burden-id list")
    if not isinstance(normalized_stage02.get("selected_n_frame_details"), dict):
        raise HarnessError("Self-test failed to preserve rich Stage 02 selected_n_frame details")
    if not isinstance(normalized_stage02.get("live_register_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 02 live register details")
    if not isinstance(normalized_stage02.get("burden_floor_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 02 burden-floor details")
    try:
        normalized_stage(
            "stage-02-layer-a-diagnostic-ir",
            {
                "id": "stage-02-layer-a-diagnostic-ir",
                "status": "pass",
                "selected_n_frame": {"basis": ["missing token"]},
                "live_registers": [{"id": "xi"}],
                "burden_floor": [{"burden_id": "B1"}],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject rich Stage 02 selected_n_frame without token")

    normalized = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": [
                {
                    "burden_id": "B1",
                    "route_target": "science-only-source-order-warrant",
                    "register_types": ["xi", "kappa"],
                }
            ],
            "owner_routes": [{"burden_id": "B1", "owner_id": "source-status-repair"}],
        },
    )
    if normalized.get("route_targets") != ["B1"]:
        raise HarnessError("Self-test failed to normalize rich Stage 03 route_targets into burden-id list")
    if not isinstance(normalized.get("route_target_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 03 route metadata")
    normalized_owner_routes = normalized_stage(
        "stage-03-routing-owner-gate",
        {
            "id": "stage-03-routing-owner-gate",
            "status": "pass",
            "route_targets": ["B1"],
            "owner_routes": [
                {
                    "target": "B1",
                    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",
                    "classification": "required_owner_sequence",
                    "required": [
                        {
                            "owner": "source-status-repair",
                            "operation": "source-order",
                            "pressure_label": "scientific-explanations-only-knowledge-source",
                        },
                        {
                            "owner": "M1",
                            "operation": "self-grounding-test",
                            "pressure_label": "only-science-counts-standard",
                        },
                    ],
                }
            ],
        },
    )
    if normalized_owner_routes.get("owner_routes") != [
        {
            "burden_id": "B1",
            "owner_id": "source-status-repair",
            "operation": "source-order",
            "eligibility": "required_owner_sequence",
        },
        {
            "burden_id": "B1",
            "owner_id": "M1",
            "operation": "self-grounding-test",
            "eligibility": "required_owner_sequence",
        },
    ]:
        raise HarnessError("Self-test failed to normalize rich Stage 03 owner_routes into owner identities")
    if not isinstance(normalized_owner_routes.get("owner_route_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 03 owner-route details")
    try:
        normalized_stage(
            "stage-03-routing-owner-gate",
            {
                "id": "stage-03-routing-owner-gate",
                "status": "pass",
                "route_targets": ["B1"],
                "owner_routes": [{"target": "B1", "required": [{}]}],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject rich Stage 03 owner route without owner id")

    canonical_act_row = (
        "⟦ACT ¹B₁[source-status-repair.source-order] :: "
        "π=scientific-explanations-only-knowledge-source :: "
        "body_ref=¹B₁ :: Δ=Δ¹B:science-source-bounded :: Land(¹B)+⟧"
    )
    normalized_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["B1"],
            "act_rows": [
                {
                    "burden_id": "B1",
                    "body_ref": "¹B₁",
                    "owner_id": "source-status-repair",
                    "operation": "source-order",
                    "act_row": canonical_act_row,
                }
            ],
        },
    )
    if normalized_stage04.get("act_rows") != [canonical_act_row]:
        raise HarnessError("Self-test failed to normalize Stage 04 object-shaped act_rows into strings")
    if normalized_stage04.get("act_body_refs") != ["¹B₁"]:
        raise HarnessError("Self-test failed to derive Stage 04 act_body_refs from canonical ACT rows")
    if not isinstance(normalized_stage04.get("act_row_details"), list):
        raise HarnessError("Self-test failed to preserve Stage 04 act_row_details")
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["B1"],
                "act_rows": [{"burden_id": "B1", "body_ref": "¹B₁"}],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 04 object-shaped act_rows without act_row")
    stage_local_record = base_record(
        "self-test-a9-science-source-stage03",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-03-routing-owner-gate",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage03",
            replay_record,
            stop_after_stage="stage-03-routing-owner-gate",
        ),
    )
    stage_local_record["stages"] = [*replay["stages"][:2], normalized]
    stage_local_path = run_dir / "staged-handoff-stage03-model-scope-record.json"
    write_json(stage_local_path, stage_local_record)
    validate_replay_record(root, stage_local_path)

    stage04_local_record = base_record(
        "self-test-a9-science-source-stage04",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-04-burden-execution-act",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage04",
            replay_record,
            stop_after_stage="stage-04-burden-execution-act",
        ),
    )
    stage04_local_record["stages"] = [*replay["stages"][:3], normalized_stage04]
    stage04_local_path = run_dir / "staged-handoff-stage04-model-scope-record.json"
    write_json(stage04_local_path, stage04_local_record)
    validate_replay_record(root, stage04_local_path)

    normalized_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass",
            "terminal_states": {"B1": "landed"},
            "dependency_graph_edges": [],
            "no_new_resultant_proof": {
                "proved": True,
                "basis": "Stage 04 ACT burden B1 landed; reread produced no generated burden.",
                "unresolved_burdens": [],
            },
        },
    )
    stage05_local_record = base_record(
        "self-test-a9-science-source-stage05",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage05",
            replay_record,
            stop_after_stage="stage-05-mrp-reread-terminal-state",
        ),
    )
    stage05_local_record["stages"] = [*replay["stages"][:4], normalized_stage05]
    stage05_local_path = run_dir / "staged-handoff-stage05-model-scope-record.json"
    write_json(stage05_local_path, stage05_local_record)
    validate_replay_record(root, stage05_local_path)

    generated_missing_terminal = dict(stage05_local_record)
    generated_missing_terminal["case_id"] = "self-test-stage05-generated-missing-terminal"
    generated_missing_terminal["model_scope"] = model_scope(
        "self-test-stage05-generated-missing-terminal",
        replay_record,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
    )
    generated_missing_terminal["stages"] = [dict(stage) for stage in stage05_local_record["stages"]]
    generated_missing_terminal["stages"][-1] = dict(generated_missing_terminal["stages"][-1])
    generated_missing_terminal["stages"][-1]["generated_burdens"] = ["B2"]
    generated_missing_terminal_path = run_dir / "stage05-generated-missing-terminal.invalid.json"
    write_json(generated_missing_terminal_path, generated_missing_terminal)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(generated_missing_terminal_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 05 generated burden missing terminal state")

    no_new_with_unresolved = dict(stage05_local_record)
    no_new_with_unresolved["case_id"] = "self-test-stage05-no-new-unresolved"
    no_new_with_unresolved["model_scope"] = model_scope(
        "self-test-stage05-no-new-unresolved",
        replay_record,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
    )
    no_new_with_unresolved["stages"] = [dict(stage) for stage in stage05_local_record["stages"]]
    no_new_with_unresolved["stages"][-1] = dict(no_new_with_unresolved["stages"][-1])
    no_new_with_unresolved["stages"][-1]["unresolved_burdens"] = ["B2"]
    no_new_with_unresolved["stages"][-1]["no_new_resultant_proof"] = True
    no_new_with_unresolved_path = run_dir / "stage05-no-new-unresolved.invalid.json"
    write_json(no_new_with_unresolved_path, no_new_with_unresolved)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(no_new_with_unresolved_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 05 no-new-resultant proof with unresolved burden")

    structured_nar = {
        "n_frame": "science-only-source-order-warrant",
        "live_registers": ["xi", "kappa"],
        "burden_floor": ["B1"],
        "per_burden": [
            {
                "burden_id": "B1",
                "owner_id": "source-status-repair",
                "operation": "source-order",
                "terminal_state": "landed",
                "generation_depth": 0,
            }
        ],
    }
    normalized_stage06 = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁", "¹B₂"],
            "nar_burdens": ["B1"],
            "owner_activations": [
                {
                    "body_ref": "¹B₁",
                    "burden_id": "B1",
                    "owner_id": "source-status-repair",
                    "operation": "source-order",
                    "terminal_state": "landed",
                },
                {
                    "body_ref": "¹B₂",
                    "burden_id": "B1",
                    "owner_id": "M1",
                    "operation": "self-grounding-test",
                    "terminal_state": "landed",
                }
            ],
            "normalized_activation_record": structured_nar,
            "register_deltas": {"xi": "source-order-landed"},
        },
    )
    if normalized_stage06.get("owner_activations") != ["¹B₁", "¹B₂"]:
        raise HarnessError("Self-test failed to normalize Stage 06 owner_activations into body-ref strings")
    if not isinstance(normalized_stage06.get("owner_activation_details"), list):
        raise HarnessError("Self-test failed to preserve Stage 06 owner_activation_details")
    mapped_nar_stage06 = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁", "¹B₂"],
            "nar_burdens": ["B1"],
            "owner_activations": ["¹B₁", "¹B₂"],
            "normalized_activation_record": {
                "n_frame": "science-only-source-order-warrant",
                "live_registers": ["xi", "kappa"],
                "burden_floor": ["B1"],
                "per_burden": {
                    "B1": {
                        "owner_id": "source-status-repair",
                        "operation": "source-order",
                        "terminal_state": "landed",
                        "generation_depth": 0,
                    }
                },
            },
            "register_deltas": {"xi": "source-order-landed"},
        },
    )
    mapped_rows = mapped_nar_stage06["normalized_activation_record"].get("per_burden")
    if not isinstance(mapped_rows, list) or mapped_rows[0].get("burden_id") != "B1":
        raise HarnessError("Self-test failed to normalize Stage 06 NAR per_burden map into object list")
    stage06_local_record = base_record(
        "self-test-a9-science-source-stage06",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-06-field-witness-nar",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage06",
            replay_record,
            stop_after_stage="stage-06-field-witness-nar",
        ),
    )
    stage06_local_record["stages"] = [*replay["stages"][:5], normalized_stage06]
    stage06_local_path = run_dir / "staged-handoff-stage06-model-scope-record.json"
    write_json(stage06_local_path, stage06_local_record)
    validate_replay_record(root, stage06_local_path)

    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": [{"burden_id": "B1"}],
                "normalized_activation_record": structured_nar,
                "register_deltas": {},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 06 owner_activation object without body_ref")

    stage06_boolean_nar = dict(stage06_local_record)
    stage06_boolean_nar["case_id"] = "self-test-stage06-boolean-nar-no-details"
    stage06_boolean_nar["model_scope"] = model_scope(
        "self-test-stage06-boolean-nar-no-details",
        replay_record,
        stop_after_stage="stage-06-field-witness-nar",
    )
    stage06_boolean_nar["stages"] = [dict(stage) for stage in stage06_local_record["stages"]]
    stage06_boolean_nar["stages"][-1] = dict(stage06_boolean_nar["stages"][-1])
    stage06_boolean_nar["stages"][-1].pop("normalized_activation_record_details", None)
    stage06_boolean_nar["stages"][-1]["normalized_activation_record"] = True
    stage06_boolean_nar_path = run_dir / "stage06-boolean-nar-no-details.invalid.json"
    write_json(stage06_boolean_nar_path, stage06_boolean_nar)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage06_boolean_nar_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject model-mode Stage 06 boolean NAR without details")

    stage06_floor_mismatch = dict(stage06_local_record)
    stage06_floor_mismatch["case_id"] = "self-test-stage06-nar-floor-mismatch"
    stage06_floor_mismatch["model_scope"] = model_scope(
        "self-test-stage06-nar-floor-mismatch",
        replay_record,
        stop_after_stage="stage-06-field-witness-nar",
    )
    stage06_floor_mismatch["stages"] = [dict(stage) for stage in stage06_local_record["stages"]]
    stage06_floor_mismatch["stages"][-1] = dict(stage06_floor_mismatch["stages"][-1])
    stage06_floor_mismatch["stages"][-1]["normalized_activation_record"] = dict(structured_nar)
    stage06_floor_mismatch["stages"][-1]["normalized_activation_record"]["burden_floor"] = ["B999"]
    stage06_floor_mismatch_path = run_dir / "stage06-nar-floor-mismatch.invalid.json"
    write_json(stage06_floor_mismatch_path, stage06_floor_mismatch)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage06_floor_mismatch_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 06 NAR burden_floor mismatch")

    stage06_release_output = dict(stage06_local_record)
    stage06_release_output["case_id"] = "self-test-stage06-release-output"
    stage06_release_output["model_scope"] = model_scope(
        "self-test-stage06-release-output",
        replay_record,
        stop_after_stage="stage-06-field-witness-nar",
    )
    stage06_release_output["stages"] = [dict(stage) for stage in stage06_local_record["stages"]]
    stage06_release_output["stages"][-1] = dict(stage06_release_output["stages"][-1])
    stage06_release_output["stages"][-1]["release_output"] = {"path": "output.md"}
    stage06_release_output_path = run_dir / "stage06-release-output.invalid.json"
    write_json(stage06_release_output_path, stage06_release_output)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage06_release_output_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 06 release_output")

    stage07_validation = {
        "visible_opening_header": "pass",
        "nla_semantic_faithfulness": "pass",
        "field_witness_convergence": "pass",
        "formal_reread_state_semantics": "pass",
        "graph_completeness_json": "pass",
        "manual_smoke_render_contract": "pass",
        "owner_activation_ordering": "pass",
    }
    replay_stage07 = stage_by_id(replay.get("stages", []), "stage-07-release-output") or {}
    replay_release_output = replay_stage07.get("release_output") if isinstance(replay_stage07, dict) else {}
    if not isinstance(replay_release_output, dict) or not isinstance(replay_release_output.get("path"), str):
        raise HarnessError("Self-test replay record missing Stage 07 release_output.path")
    replay_output_path = resolve_under_root(root, replay_release_output["path"], "self-test Stage 07 release output")
    stage07_diagnostics = build_release_field_diagnostics(replay_output_path)
    if stage07_diagnostics.get("matches") is not True:
        raise HarnessError("Self-test replay output did not produce matching release_field_diagnostics")
    stage07_local_record = base_record(
        "self-test-a9-science-source-stage07",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-07-release-output",
        model_scope_payload=model_scope(
            "self-test-a9-science-source-stage07",
            replay_record,
            stop_after_stage="stage-07-release-output",
        ),
    )
    stage07_stage = dict(replay["stages"][6])
    stage07_stage["release_validation"] = dict(stage07_validation)
    stage07_stage["release_field_diagnostics"] = dict(stage07_diagnostics)
    stage07_local_record["stages"] = [*replay["stages"][:6], stage07_stage]
    if stage07_local_record.get("stage_scope", {}).get("release_output") is not True:
        raise HarnessError("Self-test failed to mark Stage 07 scope as release-output producing")
    if stage07_local_record.get("stage_scope", {}).get("not_release_output") is True:
        raise HarnessError("Self-test Stage 07 scope must not carry not_release_output=true")
    stage07_local_path = run_dir / "staged-handoff-stage07-model-scope-record.json"
    write_json(stage07_local_path, stage07_local_record)
    validate_replay_record(root, stage07_local_path)
    run_compiled_release_self_test(
        root=root,
        run_dir=run_dir,
        replay_output_path=replay_output_path,
        replay_record=replay_record,
        replay=replay,
        stage07_validation=stage07_validation,
    )

    stage07_missing_validation = dict(stage07_local_record)
    stage07_missing_validation["case_id"] = "self-test-stage07-missing-validation"
    stage07_missing_validation["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_missing_validation["stages"][-1] = dict(stage07_missing_validation["stages"][-1])
    stage07_missing_validation["stages"][-1].pop("release_validation", None)
    stage07_missing_validation_path = run_dir / "stage07-missing-release-validation.invalid.json"
    write_json(stage07_missing_validation_path, stage07_missing_validation)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_missing_validation_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject model-mode Stage 07 missing release_validation")

    stage07_missing_diagnostics = dict(stage07_local_record)
    stage07_missing_diagnostics["case_id"] = "self-test-stage07-missing-release-field-diagnostics"
    stage07_missing_diagnostics["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_missing_diagnostics["stages"][-1] = dict(stage07_missing_diagnostics["stages"][-1])
    stage07_missing_diagnostics["stages"][-1].pop("release_field_diagnostics", None)
    stage07_missing_diagnostics_path = run_dir / "stage07-missing-release-field-diagnostics.invalid.json"
    write_json(stage07_missing_diagnostics_path, stage07_missing_diagnostics)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_missing_diagnostics_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject model-mode Stage 07 missing release_field_diagnostics")

    stage07_mismatched_diagnostics = dict(stage07_local_record)
    stage07_mismatched_diagnostics["case_id"] = "self-test-stage07-mismatched-release-field-diagnostics"
    stage07_mismatched_diagnostics["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_mismatched_diagnostics["stages"][-1] = dict(stage07_mismatched_diagnostics["stages"][-1])
    mismatched_diagnostics = json.loads(json.dumps(stage07_diagnostics))
    mismatched_diagnostics["field_witness_coverage"]["divergence_check"] = "non-neutral"
    mismatched_diagnostics["matches"] = True
    stage07_mismatched_diagnostics["stages"][-1]["release_field_diagnostics"] = mismatched_diagnostics
    stage07_mismatched_diagnostics_path = run_dir / "stage07-mismatched-release-field-diagnostics.invalid.json"
    write_json(stage07_mismatched_diagnostics_path, stage07_mismatched_diagnostics)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_mismatched_diagnostics_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 07 mismatched release_field_diagnostics")

    stage07_failed_validation = dict(stage07_local_record)
    stage07_failed_validation["case_id"] = "self-test-stage07-failed-validation"
    stage07_failed_validation["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_failed_validation["stages"][-1] = dict(stage07_failed_validation["stages"][-1])
    stage07_failed_validation["stages"][-1]["release_validation"] = dict(stage07_validation)
    stage07_failed_validation["stages"][-1]["release_validation"]["nla_semantic_faithfulness"] = "fail"
    stage07_failed_validation_path = run_dir / "stage07-failed-release-validation.invalid.json"
    write_json(stage07_failed_validation_path, stage07_failed_validation)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_failed_validation_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 07 failed release_validation")

    stage07_with_sidecars = dict(stage07_local_record)
    stage07_with_sidecars["case_id"] = "self-test-stage07-with-sidecars"
    stage07_with_sidecars["stages"] = [dict(stage) for stage in stage07_local_record["stages"]]
    stage07_with_sidecars["stages"][-1] = dict(stage07_with_sidecars["stages"][-1])
    stage07_with_sidecars["stages"][-1]["verifier_sidecars"] = {"claimed": True}
    stage07_with_sidecars_path = run_dir / "stage07-with-sidecars.invalid.json"
    write_json(stage07_with_sidecars_path, stage07_with_sidecars)
    invalid_result = run_checked(
        [
            sys.executable,
            str(root / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(stage07_with_sidecars_path),
        ],
        cwd=root,
    )
    if invalid_result.returncode == 0:
        raise HarnessError("Self-test failed to reject Stage 07 verifier_sidecars")
    print("staged current-skill harness self-test: PASS")
    print(f"self-test run dir: {rel(run_dir, root)}")
    print(f"handoff record: {rel(record_path, root)}")
    print(f"hashes: {rel(hash_path, root)}")
    return 0


def visible_governed_output_errors(output_path: Path) -> list[str]:
    text = output_path.read_text(encoding="utf-8", errors="replace")
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
    errors = [label for label, pattern in checks if re.search(pattern, text, re.IGNORECASE | re.MULTILINE) is None]
    forbidden = [
        ("harness commentary", r"You are executing stage-|Validated compact stage state|Return exactly one JSON object"),
        ("package/provenance claim", r"\bpackage/provenance\b|provenance asset|release package|\.skill\b|GitHub Release"),
        ("guaranteed T_lang uptake claim", r"T_lang guarantees|guaranteed T_lang uptake|guarantees interlocutor uptake"),
        ("Graphify/ActiveGraph proof claim", r"Graphify[^.\n]{0,80}\bproof\b|ActiveGraph[^.\n]{0,80}\bproof\b"),
    ]
    errors.extend(label for label, pattern in forbidden if re.search(pattern, text, re.IGNORECASE))
    return errors


def coverage_status(field_witness: dict[str, Any] | None, key: str) -> str:
    if not isinstance(field_witness, dict):
        return ""
    coverage = field_witness.get("coverage_proof")
    if not isinstance(coverage, dict):
        return ""
    value = coverage.get(key)
    if not isinstance(value, str):
        return ""
    return status_head(value)


def build_release_field_diagnostics(output_path: Path) -> dict[str, Any]:
    text = output_path.read_text(encoding="utf-8", errors="replace")
    witness = parse_closure_witness(text)
    field_witness = extract_embedded_field_witness(text)
    visible = {
        "divergence_check": status_head(witness.divergence) if witness is not None else "",
        "curl_check": status_head(witness.curl) if witness is not None else "",
    }
    field_witness_coverage = {
        "divergence_check": coverage_status(field_witness, "divergence_check"),
        "curl_check": coverage_status(field_witness, "curl_check"),
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


def run_release_validators(root: Path, output_path: Path) -> dict[str, str]:
    visible_errors = visible_governed_output_errors(output_path)
    if visible_errors:
        raise HarnessError(
            "stage-07-release-output: visible governed output validation failed:\n- "
            + "\n- ".join(visible_errors)
        )
    validators = [
        (
            "nla_semantic_faithfulness",
            [sys.executable, str(root / "tools" / "check_nla_decode_semantic_faithfulness.py"), "--outputs", str(output_path)],
        ),
        (
            "field_witness_convergence",
            [sys.executable, str(root / "tools" / "check_field_witness_convergence.py"), "--outputs", str(output_path)],
        ),
        (
            "formal_reread_state_semantics",
            [sys.executable, str(root / "tools" / "check_formal_reread_state_semantics.py"), "--outputs", str(output_path)],
        ),
        (
            "graph_completeness_json",
            [sys.executable, str(root / "tools" / "check_graph_completeness.py"), "--outputs", str(output_path), "--json"],
        ),
        (
            "manual_smoke_render_contract",
            [sys.executable, str(root / "tools" / "check_manual_smoke_render_contract.py"), "--outputs", str(output_path)],
        ),
        (
            "owner_activation_ordering",
            [sys.executable, str(root / "tools" / "check_owner_activation_ordering.py"), "--outputs", str(output_path)],
        ),
    ]
    results = {"visible_opening_header": "pass"}
    for key, command in validators:
        require_command_success(command, cwd=root)
        results[key] = "pass"
    missing = STAGE07_RELEASE_VALIDATION_KEYS - set(results)
    if missing:
        raise HarnessError(f"stage-07-release-output: internal validator set missing {sorted(missing)}")
    return results


def build_sidecars(
    *,
    root: Path,
    raw_input: Path,
    output_path: Path,
    out_dir: Path,
    prefix: str,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_nla_decode_semantic_faithfulness.py"),
            "--outputs",
            str(output_path),
        ],
        cwd=root,
    )
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_field_witness_convergence.py"),
            "--outputs",
            str(output_path),
        ],
        cwd=root,
    )
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_formal_reread_state_semantics.py"),
            "--outputs",
            str(output_path),
        ],
        cwd=root,
    )
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "check_graph_completeness.py"),
            "--outputs",
            str(output_path),
            "--json",
        ],
        cwd=root,
    )
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "build_retained_proof_sidecars.py"),
            "--input",
            str(raw_input),
            "--output",
            str(output_path),
            "--out-dir",
            str(out_dir),
            "--prefix",
            prefix,
            "--force",
        ],
        cwd=root,
    )
    certificate = out_dir / f"{prefix}.collapse-certificate.json"
    grapher = out_dir / f"{prefix}.grapher.html"
    b5_sidecar = out_dir / f"{prefix}.b5-full-ir-projection-sidecar.json"
    require_command_success(
        [
            sys.executable,
            str(root / "tools" / "build_b5_full_ir_projection_sidecar.py"),
            "--input",
            str(raw_input),
            "--output",
            str(output_path),
            "--collapse-certificate",
            str(certificate),
            "--grapher-html",
            str(grapher),
            "--out",
            str(b5_sidecar),
        ],
        cwd=root,
    )
    return [certificate, grapher, out_dir / f"{prefix}.hashes.json", b5_sidecar]


def run_model_smoke(args: argparse.Namespace, root: Path) -> int:
    files = validate_required_files(root)
    replay_record = resolve_under_root(root, args.replay_record, "Replay record")
    raw_input = resolve_under_root(root, args.raw_input_path, "Raw input")
    validate_replay_record(root, replay_record)
    run_dir = resolve_under_root(root, args.run_dir, "Run directory")
    run_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = run_dir / "prompts"
    responses_dir = run_dir / "responses"
    records_dir = run_dir / "records"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    responses_dir.mkdir(parents=True, exist_ok=True)
    records_dir.mkdir(parents=True, exist_ok=True)

    input_text = raw_input.read_text(encoding="utf-8", errors="replace")
    input_digest = sha256_file(raw_input)
    skill_hash = sha256_file(files["skill"])
    stages: list[dict[str, Any]] = []
    stage_files: list[Path] = []
    mode = "staged-current-skill-stage-local-smoke" if args.stop_after_stage else "staged-current-skill-smoke"
    release_output_mode = normalize_release_output_mode(args.release_output_mode)
    record = base_record(
        args.case_name,
        mode,
        not_model_smoke=False,
        stop_after_stage=args.stop_after_stage,
        model_scope_payload=model_scope(args.case_name, replay_record, stop_after_stage=args.stop_after_stage),
    )

    try:
        stage_ids_to_run = stage_order_for_stop(args.stop_after_stage)
        if args.stop_after_stage is None or args.stop_after_stage == "stage-07-release-output":
            stage_ids_to_run = STAGE_ORDER[:6]
        for stage_id in stage_ids_to_run:
            prompt = stage_prompt(
                root=root,
                stage_id=stage_id,
                case_name=args.case_name,
                raw_input_path=raw_input,
                input_text=input_text,
                input_digest=input_digest,
                skill_hash=skill_hash,
                previous_stages=stages,
            )
            prompt_path = prompts_dir / f"{stage_id}.prompt.md"
            response_path = responses_dir / f"{stage_id}.response.txt"
            log_path = responses_dir / f"{stage_id}.codex-log.txt"
            write_text(prompt_path, prompt)
            exit_code = invoke_codex(root, args.model, prompt, response_path, log_path)
            stage_files.extend([prompt_path, response_path, log_path])
            if exit_code != 0:
                raise HarnessError(f"{stage_id}: codex exec failed with exit code {exit_code}; see {rel(log_path, root)}")
            payload = extract_json_object(response_path.read_text(encoding="utf-8", errors="replace"))
            stage = normalized_stage(stage_id, payload)
            if stage.get("status") == "fail":
                raise HarnessError(f"{stage_id}: model returned fail: {stage.get('error')}")
            stages.append(stage)
            validate_incremental_handoffs(stages)
            write_json(records_dir / f"{stage_id}.stage.json", stage)
            if args.stop_after_stage == stage_id:
                record["stages"] = stages
                handoff_record = records_dir / "staged-handoff-stage-local-record.json"
                write_json(handoff_record, record)
                validate_replay_record(root, handoff_record)
                hash_path = run_dir / "staged-smoke.hashes.json"
                write_hash_record(
                    hash_path,
                    root=root,
                    case_name=args.case_name,
                    mode=mode,
                    model=args.model,
                    skill_path=files["skill"],
                    replay_record=replay_record,
                    raw_input_path=raw_input,
                    run_dir=run_dir,
                    stage_files=stage_files + [handoff_record],
                    handoff_record=handoff_record,
                    output_path=None,
                    sidecar_paths=[],
                    verdict=f"STAGED_CURRENT_SKILL_STAGE_LOCAL_PASS: stopped after {stage_id}",
                )
                print("staged current-skill stage-local smoke: PASS")
                print(f"run dir: {rel(run_dir, root)}")
                print(f"stop-after-stage: {stage_id}")
                print(f"handoff record: {rel(handoff_record, root)}")
                print(f"hashes: {rel(hash_path, root)}")
                return 0

        output_path = run_dir / "output.md"
        assembly_record: dict[str, Any] | None = None
        if release_output_mode == "compiled-output":
            section_plan = compiled_release_section_plan(args.target_output_kb)
            sections_dir = run_dir / "release-sections"
            sections_dir.mkdir(parents=True, exist_ok=True)
            section_entries: list[dict[str, str]] = []
            for index, (section_id, section_role) in enumerate(section_plan, start=1):
                section_prompt = release_section_prompt(
                    root=root,
                    case_name=args.case_name,
                    raw_input_path=raw_input,
                    input_text=input_text,
                    input_digest=input_digest,
                    skill_hash=skill_hash,
                    previous_stages=stages,
                    section_id=section_id,
                    section_role=section_role,
                    section_number=index,
                    section_count=len(section_plan),
                    target_output_kb=args.target_output_kb,
                )
                safe_section_id = section_id.replace("_", "-")
                section_prompt_path = prompts_dir / f"stage-07-release-output-{index:02d}-{safe_section_id}.prompt.md"
                section_output_path = sections_dir / f"{index:02d}-{safe_section_id}.md"
                section_log_path = responses_dir / f"stage-07-release-output-{index:02d}-{safe_section_id}.codex-log.txt"
                write_text(section_prompt_path, section_prompt)
                exit_code = invoke_codex(root, args.model, section_prompt, section_output_path, section_log_path)
                stage_files.extend([section_prompt_path, section_output_path, section_log_path])
                if exit_code != 0:
                    raise HarnessError(
                        f"stage-07-release-output {section_id}: codex exec failed with exit code {exit_code}; "
                        f"see {rel(section_log_path, root)}"
                    )
                if not section_output_path.exists() or section_output_path.stat().st_size == 0:
                    raise HarnessError(f"stage-07-release-output {section_id}: section output was not produced")
                section_entries.append(
                    {
                        "id": section_id,
                        "role": section_role,
                        "path": str(section_output_path),
                        "sha256": sha256_file(section_output_path),
                    }
                )
            assembly_manifest_path = run_dir / "stage-07-output-assembly.manifest.json"
            write_compiled_release_manifest(
                root=root,
                manifest_path=assembly_manifest_path,
                case_name=args.case_name,
                raw_input_path=raw_input,
                section_entries=section_entries,
                output_path=output_path,
                target_output_kb=args.target_output_kb,
            )
            stage_files.append(assembly_manifest_path)
            assembly_record = staged_output.assemble_manifest(assembly_manifest_path, root=root)
            assembly_hash_path = output_path.with_suffix(output_path.suffix + ".assembly.hashes.json")
            if assembly_hash_path.exists():
                stage_files.append(assembly_hash_path)
        else:
            release = release_prompt(
                root=root,
                case_name=args.case_name,
                raw_input_path=raw_input,
                input_text=input_text,
                input_digest=input_digest,
                skill_hash=skill_hash,
                previous_stages=stages,
            )
            release_prompt_path = prompts_dir / "stage-07-release-output.prompt.md"
            release_log_path = responses_dir / "stage-07-release-output.codex-log.txt"
            write_text(release_prompt_path, release)
            exit_code = invoke_codex(root, args.model, release, output_path, release_log_path)
            stage_files.extend([release_prompt_path, output_path, release_log_path])
            if exit_code != 0:
                raise HarnessError(
                    f"stage-07-release-output: codex exec failed with exit code {exit_code}; "
                    f"see {rel(release_log_path, root)}"
                )
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise HarnessError("stage-07-release-output: output.md was not produced")
        release_validation = run_release_validators(root, output_path)
        release_field_diagnostics = build_release_field_diagnostics(output_path)
        stage05 = stage_by_id(stages, "stage-05-mrp-reread-terminal-state") or {}
        stage07 = {
            "id": "stage-07-release-output",
            "status": "pass",
            "produces": ["release_output", "release_terminal_states"],
            "requires": ["field_witness_body_refs", "nar_burdens"],
            "release_output": {"path": rel(output_path, root), "sha256": sha256_file(output_path)},
            "release_terminal_states": stage05.get("terminal_states", {}),
            "closure_claim": "complete",
            "output_is_full_governed_answer": True,
            "release_validation": release_validation,
            "release_field_diagnostics": release_field_diagnostics,
            "release_output_mode": release_output_mode,
        }
        if assembly_record is not None:
            stage07["assembly_manifest"] = dict(assembly_record["assembly_manifest"])
            stage07["assembly_hashes"] = dict(assembly_record["hash_record"])
            stage07["target_output_kb"] = int(args.target_output_kb or 0)
        stages.append(stage07)
        if args.stop_after_stage == "stage-07-release-output":
            record["stages"] = stages
            handoff_record = records_dir / "staged-handoff-stage-local-record.json"
            write_json(handoff_record, record)
            validate_replay_record(root, handoff_record)
            hash_path = run_dir / "staged-smoke.hashes.json"
            write_hash_record(
                hash_path,
                root=root,
                case_name=args.case_name,
                mode=mode,
                model=args.model,
                skill_path=files["skill"],
                replay_record=replay_record,
                raw_input_path=raw_input,
                run_dir=run_dir,
                stage_files=stage_files + [handoff_record],
                handoff_record=handoff_record,
                output_path=output_path,
                sidecar_paths=[],
                verdict="STAGED_CURRENT_SKILL_STAGE_LOCAL_PASS: stopped after stage-07-release-output",
            )
            print("staged current-skill stage-local smoke: PASS")
            print(f"run dir: {rel(run_dir, root)}")
            print("stop-after-stage: stage-07-release-output")
            print(f"output: {rel(output_path, root)}")
            print(f"handoff record: {rel(handoff_record, root)}")
            print(f"hashes: {rel(hash_path, root)}")
            return 0

        sidecar_dir = run_dir / "proof-sidecars"
        sidecars = build_sidecars(root=root, raw_input=raw_input, output_path=output_path, out_dir=sidecar_dir, prefix=args.case_name)
        stage08 = {
            "id": "stage-08-verifier-sidecars",
            "status": "pass",
            "produces": ["verifier_sidecars"],
            "requires": ["release_output"],
            "verifier_sidecars": {
                "proof_sidecars": {
                    "claimed": True,
                    "paths": [rel(path_item, root) for path_item in sidecars],
                },
                "b5_4_1": {
                    "claimed": False,
                    "path": rel(sidecars[-1], root),
                    "role": "checker-owned-final-verifier-built-but-not-retained",
                    "non_claims": {"not_fresh_runtime_default_emission": True},
                },
            },
        }
        stages.append(stage08)
        record["stages"] = stages
        handoff_record = records_dir / "staged-handoff-record.json"
        write_json(handoff_record, record)
        validate_replay_record(root, handoff_record)
        hash_path = run_dir / "staged-smoke.hashes.json"
        write_hash_record(
            hash_path,
            root=root,
            case_name=args.case_name,
            mode=mode,
            model=args.model,
            skill_path=files["skill"],
            replay_record=replay_record,
            raw_input_path=raw_input,
            run_dir=run_dir,
            stage_files=stage_files,
            handoff_record=handoff_record,
            output_path=output_path,
            sidecar_paths=sidecars,
            verdict="STAGED_CURRENT_SKILL_ONE_CASE_PROOF_SURFACE_PASS",
        )
        print("staged current-skill smoke: PASS")
        print(f"run dir: {rel(run_dir, root)}")
        print(f"output: {rel(output_path, root)}")
        print(f"handoff record: {rel(handoff_record, root)}")
        print(f"hashes: {rel(hash_path, root)}")
        return 0
    except HarnessError as exc:
        failed_record = dict(record)
        failed_record["stages"] = stages
        failed_record["failure"] = str(exc)
        partial_output_path = run_dir / "output.md"
        if partial_output_path.exists() and partial_output_path.stat().st_size > 0:
            failed_record["stage07_release_field_diagnostics"] = build_release_field_diagnostics(partial_output_path)
        failure_record_path = records_dir / "staged-handoff-failure.json"
        write_json(failure_record_path, failed_record)
        hash_path = run_dir / "staged-smoke.hashes.json"
        write_hash_record(
            hash_path,
            root=root,
            case_name=args.case_name,
            mode="staged-current-skill-smoke",
            model=args.model,
            skill_path=files["skill"],
            replay_record=replay_record,
            raw_input_path=raw_input,
            run_dir=run_dir,
            stage_files=stage_files + [failure_record_path],
            handoff_record=failure_record_path,
            output_path=run_dir / "output.md",
            sidecar_paths=[],
            verdict=f"STAGED_MODEL_HARNESS_NEGATIVE_EVIDENCE: {exc}",
        )
        print("staged current-skill smoke: FAIL")
        print(f"run dir: {rel(run_dir, root)}")
        print(f"failure: {exc}")
        print(f"failure record: {rel(failure_record_path, root)}")
        print(f"hashes: {rel(hash_path, root)}")
        return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--case-name", default="staged-a9-science-source")
    parser.add_argument("--raw-input-path", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--replay-record", type=Path, default=DEFAULT_REPLAY_RECORD)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--stop-after-stage", choices=STAGE_ORDER[:7], default=None)
    parser.add_argument("--release-output-mode", choices=sorted(RELEASE_OUTPUT_MODE_ALIASES), default="single-output")
    parser.add_argument("--target-output-kb", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if Path.cwd().resolve() != root:
        raise HarnessError(
            f"Wrong current directory. Current={Path.cwd().resolve()}; expected root={root}. "
            "Run from the repo root so artifacts cannot bind another workspace."
        )
    if args.self_test:
        return run_self_test(root)
    if args.run_dir is None:
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        args.run_dir = root / ".daee" / "staged-current-skill-smokes" / f"{timestamp}-{args.case_name}"
    return run_model_smoke(args, root)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HarnessError as exc:
        print(f"staged current-skill harness: BLOCKED: {exc}")
        raise SystemExit(2)
