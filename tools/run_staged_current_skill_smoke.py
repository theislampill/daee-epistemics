#!/usr/bin/env python3
"""Run a bounded staged current-skill smoke.

This is repo/dev harness tooling. It preserves the public `/daee-epistemics`
surface and writes staged scratch artifacts under `.daee/`. The no-model
self-test proves only harness wiring; it does not prove model behavior.
"""

from __future__ import annotations

import argparse
import copy
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
from delta_result_vocabulary import DELTA_RESULT_VOCABULARY, canonical_delta_owner


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
SUP_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
ASCII_TO_SUP_DIGITS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
ACT_ROW_DETAIL_RE = re.compile(
    r"^\s*⟦ACT\s+(?P<body_ref>[^\s\[]+)"
    r"\[(?P<owner>[A-Za-z][A-Za-z0-9_/\-]*)\.(?P<operation>[A-Za-z][A-Za-z0-9_.\-/]*)\]"
    r"\s*::\s*π=(?P<pressure>[^\n]+?)"
    r"\s*::\s*body_ref=(?P<body_ref_field>[^\s:⟧]+)"
    r"\s*::\s*Δ=(?P<delta>[^:\s]+):(?P<delta_result>.+?)"
    r"\s*::\s*(?P<land>Land\([^)\n]+\)\+?)⟧\s*$"
)
LAND_TARGET_RE = re.compile(r"Land\((?P<target>[^)\n]+)\)")
CANONICAL_BURDEN_ID_RE = re.compile(r"(?<![A-Za-z0-9_])B([1-9][0-9]*)(?![A-Za-z0-9_])")
BODY_REF_BURDEN_RE = re.compile(r"^(?P<burden>[⁰¹²³⁴⁵⁶⁷⁸⁹]+B|B[1-9][0-9]*)(?:[₀₁₂₃₄₅₆₇₈₉]+|[_\.][1-9][0-9]*)?$")
ASCII_BODY_REF_RE = re.compile(r"^(?P<burden>[1-9][0-9]*)B[1-9][0-9]*$")
STAGE07_RELEASE_VALIDATION_KEYS = {
    "visible_opening_header",
    "nla_semantic_faithfulness",
    "field_witness_convergence",
    "formal_reread_state_semantics",
    "graph_completeness_json",
    "manual_smoke_render_contract",
    "public_burden_grouping",
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
TRANSPORT_ATTEMPTS_SCHEMA = "staged-model-subprocess-attempts-v1"
TRANSPORT_RESUME_SCHEMA = "staged-transport-resume-v1"
SEMANTIC_FAILURE_RE = re.compile(
    r"(?i)\b("
    r"assembly error|validator|validation failed|missing required surface|semantic|"
    r"forbidden claim|hash mismatch|section budget|public output"
    r")\b"
)
TRANSPORT_TIMEOUT_RE = re.compile(
    r"(?i)\b("
    r"timed out|timeout|connection reset|connection aborted|stream disconnected|"
    r"network error|temporarily unavailable|service unavailable|gateway timeout"
    r")\b"
)

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
            "arrays of strings. `act_targets` and `act_burdens` must use canonical "
            "burden-id strings only, such as [\"B1\"], not descriptive burden labels. "
            "Every ACT row must be an exact canonical row beginning "
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
            "`normalized_activation_record.n_frame` must be one non-empty string token. "
            "Do not put `selected`/`held` objects in canonical `n_frame`; if those details "
            "are useful, put them in `n_frame_details` or "
            "`normalized_activation_record_details.n_frame_details`. "
            "When a structured `normalized_activation_record` is present, "
            "`normalized_activation_record_details` is supplemental metadata only; any "
            "`n_frame_details.selected` value there must match the canonical string "
            "`normalized_activation_record.n_frame`. "
            "`per_burden` must be a JSON array/list of objects; each object must include "
            "a non-empty string `burden_id`. Do not emit `per_burden` as a burden-keyed object map. "
            "`register_deltas` must be parser-stable as an object mapping register names to "
            "a non-empty string or non-empty string array, or as a list of objects with "
            "`register` plus `delta` as a non-empty string or non-empty string array. "
            "If Stage 06 cannot honestly mirror ACT/terminal evidence, "
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
        "public_burden_grouping_checker": root / "tools" / "check_public_burden_grouping.py",
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


def delta_token_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def canonical_delta_result_for_owner(
    owner: Any,
    operation: Any,
    pressure: Any,
    raw_delta_result: Any,
) -> str:
    raw = str(raw_delta_result or "").strip()
    if not raw:
        return raw
    family = canonical_delta_owner(str(owner or "")) or str(owner or "").strip().upper()
    vocabulary = DELTA_RESULT_VOCABULARY.get(family)
    if not vocabulary or raw in vocabulary:
        return raw

    combined = delta_token_key(f"{operation} {pressure} {raw}")
    candidates: list[str] = []
    if family == "DO_CHRISTIAN":
        if any(token in combined for token in ("trinitarian", "person-nature", "model-transfer", "model-identification")):
            candidates.append("trinitarian-model-identified")
        if "fan-out" in combined:
            candidates.append("fan-out-route-named")
    elif family == "M7":
        if any(token in combined for token in ("only-scope", "definition", "scope-defined")):
            candidates.append("definition-anchored")
        if "semantic" in combined or "meaning" in combined:
            candidates.append("semantic-anchor-stabilized")
        if "term" in combined:
            candidates.append("term-meaning-bounded")
        if "falsifiability" in combined:
            candidates.append("falsifiability-standard-defined")
    elif family == "M8":
        if "entailment" in combined:
            candidates.append("entailment-blocked")
        if "consequence" in combined:
            candidates.append("consequence-traced")
        if "dependency" in combined:
            candidates.append("dependency-exposed")
        if "implication" in combined:
            candidates.append("implication-demoted")
    elif family == "M9":
        if "person-nature" in combined:
            candidates.append("person-nature-transfer-blocked")
        if "category" in combined:
            candidates.append("category-separated")
        if "referent" in combined or "sender-sent" in combined:
            candidates.append("referent-separated")
        if "predicate" in combined or "predication" in combined:
            candidates.append("predicate-separated")
        if "sense" in combined:
            candidates.append("sense-separated")
    elif family == "SOURCE":
        if "proof-text-hidden-support" in combined:
            candidates.append("proof-text-hidden-support-blocked")
        if "proof-text" in combined or "proof-stack" in combined:
            candidates.append("proof-text-sorted")
        if "source-order" in combined or "proof-stack-routed" in combined:
            candidates.append("source-order-repaired")
        if "hidden-support" in combined:
            candidates.append("hidden-support-blocked")
        if "authority-order" in combined:
            candidates.append("authority-order-repaired")
    elif family == "P7":
        if "hold" in combined or "held" in combined:
            candidates.append("held-route-bounded")
        if "scope" in combined:
            candidates.append("scope-boundary-named")
        if "reopen" in combined:
            candidates.append("reopen-condition-stated")

    for candidate in ordered_unique(candidates):
        if candidate in vocabulary:
            return candidate
    return raw


def canonicalize_delta_fields(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str] | None]:
    owner = item.get("owner") or item.get("owner_id")
    operation = item.get("operation")
    pressure = item.get("pressure")
    raw_result = item.get("delta_result")
    delta_value = str(item.get("delta") or "")
    if not raw_result and ":" in delta_value:
        raw_result = delta_value.split(":", 1)[1]
    canonical = canonical_delta_result_for_owner(owner, operation, pressure, raw_result)
    if not raw_result or canonical == str(raw_result).strip():
        return item, None
    updated = dict(item)
    updated["delta_result"] = canonical
    if delta_value and ":" in delta_value:
        updated["delta"] = delta_value.split(":", 1)[0] + ":" + canonical
    return updated, {
        "owner": str(owner or ""),
        "operation": str(operation or ""),
        "pressure": str(pressure or ""),
        "raw_delta_result": str(raw_result).strip(),
        "canonical_delta_result": canonical,
    }


def canonicalize_stage04_act_row(row: str) -> tuple[str, dict[str, str] | None]:
    match = ACT_ROW_DETAIL_RE.match(row)
    if not match:
        return row, None
    raw_result = match.group("delta_result").strip()
    canonical = canonical_delta_result_for_owner(
        match.group("owner"),
        match.group("operation"),
        match.group("pressure"),
        raw_result,
    )
    if canonical == raw_result:
        return row, None
    start, end = match.span("delta_result")
    return (
        row[:start] + canonical + row[end:],
        {
            "body_ref": match.group("body_ref"),
            "owner": match.group("owner"),
            "operation": match.group("operation"),
            "pressure": match.group("pressure").strip(),
            "raw_delta_result": raw_result,
            "canonical_delta_result": canonical,
        },
    )


def canonicalize_stage04_act_rows(rows: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    canonical_rows: list[str] = []
    rewrites: list[dict[str, str]] = []
    for row in rows:
        canonical_row, rewrite = canonicalize_stage04_act_row(row)
        canonical_rows.append(canonical_row)
        if rewrite:
            rewrites.append(rewrite)
    return ordered_unique(canonical_rows), rewrites


def canonical_burden_id_from_text(value: str, allowed_ids: set[str] | None = None) -> str | None:
    text = value.strip()
    if allowed_ids is None or text in allowed_ids:
        if CANONICAL_BURDEN_ID_RE.fullmatch(text):
            return text
    matches = ordered_unique([f"B{match.group(1)}" for match in CANONICAL_BURDEN_ID_RE.finditer(text)])
    if allowed_ids is not None:
        matches = [match for match in matches if match in allowed_ids]
    return matches[0] if len(matches) == 1 else None


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


def normalize_stage04_burden_ids(
    stage: dict[str, Any],
    key: str,
    *,
    allowed_ids: set[str],
    normalization: dict[str, Any],
) -> list[str]:
    value = stage.get(key)
    if not isinstance(value, list) or not value:
        raise HarnessError(f"stage-04 {key} must be a non-empty burden-id list")

    canonical: list[str] = []
    details: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if isinstance(item, str) and item.strip():
            burden_id = canonical_burden_id_from_text(item, allowed_ids)
            if burden_id is None:
                raise HarnessError(f"stage-04 {key}[{index}] cannot be normalized to a routed burden id")
            canonical.append(burden_id)
            if item.strip() != burden_id:
                details.append({"raw": item, "burden_id": burden_id})
        elif isinstance(item, dict):
            burden_id = non_empty_string(item.get("burden_id") or item.get("id"))
            if burden_id is None:
                raise HarnessError(f"stage-04 {key}[{index}] object cannot be normalized without a string burden_id")
            burden_id = burden_id.strip()
            if burden_id not in allowed_ids:
                raise HarnessError(f"stage-04 {key}[{index}] burden_id is not routed: {burden_id}")
            canonical.append(burden_id)
            details.append(dict(item))
        else:
            raise HarnessError(f"stage-04 {key} must contain burden-id strings or burden objects")

    stage[key] = ordered_unique(canonical)
    if details:
        stage[f"{key}_details"] = details
        normalization[f"{key}_normalized_to_canonical_ids"] = True
        normalization[f"canonical_{key}"] = list(stage[key])
    return stage[key]


def normalize_stage04_act_fields(stage: dict[str, Any]) -> None:
    act_targets = normalize_string_list(stage, "act_targets", required=True)
    normalization = normalization_object(stage)
    normalize_stage04_burden_ids(
        stage,
        "act_burdens",
        allowed_ids=set(act_targets),
        normalization=normalization,
    )
    raw_rows = stage.get("act_rows")

    if isinstance(raw_rows, list) and raw_rows and all(isinstance(item, str) and item for item in raw_rows):
        act_rows, delta_rewrites = canonicalize_stage04_act_rows(ordered_unique(list(raw_rows)))
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
        act_rows, delta_rewrites = canonicalize_stage04_act_rows(ordered_unique(act_rows))
        stage["act_rows"] = act_rows
        normalization["act_rows_from_details"] = True
        normalization["canonical_act_rows"] = list(stage["act_rows"])
    else:
        raise HarnessError("stage-04 act_rows must be a non-empty list of ACT row strings")
    if delta_rewrites:
        normalization["delta_result_canonicalizations"] = delta_rewrites

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


def normalize_stage06_register_delta_value(
    value: Any,
    *,
    empty_string_message: str,
    list_message: str,
    type_message: str,
) -> str | list[str]:
    if isinstance(value, str):
        if not value:
            raise HarnessError(empty_string_message)
        return value
    if isinstance(value, list):
        if not value or not all(isinstance(item, str) and item for item in value):
            raise HarnessError(list_message)
        return ordered_unique(list(value))
    raise HarnessError(type_message)


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
        details = []
        delta_rewrites: list[dict[str, str]] = []
        for raw_detail in owner_activations:
            detail, rewrite = canonicalize_delta_fields(dict(raw_detail))
            details.append(detail)
            if rewrite:
                delta_rewrites.append(rewrite)
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
        if delta_rewrites:
            normalization["owner_activation_delta_result_canonicalizations"] = delta_rewrites
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
        hydrate_stage06_nar_details(details, normalized)
        normalize_stage06_nar_object(details, "stage-06 normalized_activation_record_details")

    if "register_deltas" not in stage:
        raise HarnessError("stage-06 register_deltas is required")
    register_deltas = stage.get("register_deltas")
    if isinstance(register_deltas, dict):
        for register, delta in register_deltas.items():
            if not isinstance(register, str) or not register:
                raise HarnessError("stage-06 register_deltas keys must be non-empty strings")
            register_deltas[register] = normalize_stage06_register_delta_value(
                delta,
                empty_string_message="stage-06 register_deltas string values must be non-empty",
                list_message="stage-06 register_deltas list values must be non-empty strings",
                type_message="stage-06 register_deltas object values must be strings or string lists",
            )
    elif isinstance(register_deltas, list):
        for index, item in enumerate(register_deltas):
            if not isinstance(item, dict):
                raise HarnessError(f"stage-06 register_deltas[{index}] must be an object")
            if not isinstance(item.get("register"), str) or not item["register"]:
                raise HarnessError(f"stage-06 register_deltas[{index}].register must be a non-empty string")
            item["delta"] = normalize_stage06_register_delta_value(
                item.get("delta"),
                empty_string_message=f"stage-06 register_deltas[{index}].delta must be a non-empty string",
                list_message=f"stage-06 register_deltas[{index}].delta list values must be non-empty strings",
                type_message=(
                    f"stage-06 register_deltas[{index}].delta must be a non-empty string "
                    "or non-empty string list"
                ),
            )
    else:
        raise HarnessError("stage-06 register_deltas must be an object or list")


def normalize_stage06_nar_object(value: dict[str, Any], label: str) -> None:
    raw_n_frame = value.get("n_frame")
    if isinstance(raw_n_frame, dict):
        selected = raw_n_frame.get("selected")
        if not isinstance(selected, str) or not selected.strip():
            raise HarnessError(f"{label}.n_frame object cannot be normalized without a non-empty string selected token")
        if "n_frame_details" not in value:
            value["n_frame_details"] = dict(raw_n_frame)
        value["n_frame"] = selected.strip()
        normalization = value.get("normalization")
        if normalization is None:
            normalization = {}
        if not isinstance(normalization, dict):
            raise HarnessError(f"{label}.normalization must be an object when present")
        normalization["n_frame_from_selected_detail"] = True
        normalization["canonical_n_frame"] = value["n_frame"]
        value["normalization"] = normalization
    elif isinstance(raw_n_frame, str) and raw_n_frame.strip():
        value["n_frame"] = raw_n_frame.strip()
    else:
        raise HarnessError(f"{label}.n_frame must be a non-empty string")
    n_frame = value["n_frame"]
    n_frame_details = value.get("n_frame_details")
    if n_frame_details is not None:
        if not isinstance(n_frame_details, dict):
            raise HarnessError(f"{label}.n_frame_details must be an object when present")
        detail_selected = n_frame_details.get("selected")
        if detail_selected is not None:
            if not isinstance(detail_selected, str) or not detail_selected.strip():
                raise HarnessError(f"{label}.n_frame_details.selected must be a non-empty string when present")
            if detail_selected.strip() != n_frame:
                raise HarnessError(f"{label}.n_frame_details.selected must match canonical n_frame")
        detail_held = n_frame_details.get("held")
        if detail_held is not None and (
            not isinstance(detail_held, list) or not all(isinstance(item, str) and item for item in detail_held)
        ):
            raise HarnessError(f"{label}.n_frame_details.held must be a string list when present")
    normalization = value.get("normalization")
    if normalization is not None and not isinstance(normalization, dict):
        raise HarnessError(f"{label}.normalization must be an object when present")
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
    delta_rewrites: list[dict[str, str]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise HarnessError(f"{label}.per_burden[{index}] must be an object")
        if not isinstance(row.get("burden_id"), str) or not row["burden_id"]:
            raise HarnessError(f"{label}.per_burden[{index}].burden_id must be a non-empty string")
        updated, rewrite = canonicalize_delta_fields(row)
        if rewrite:
            rows[index] = updated
            delta_rewrites.append(rewrite)
    if delta_rewrites:
        normalization = value.get("normalization")
        if normalization is None:
            normalization = {}
        if not isinstance(normalization, dict):
            raise HarnessError(f"{label}.normalization must be an object when present")
        normalization["per_burden_delta_result_canonicalizations"] = delta_rewrites
        value["normalization"] = normalization


def hydrate_stage06_nar_details(details: Any, canonical_nar: Any) -> None:
    if not isinstance(details, dict):
        raise HarnessError("stage-06 normalized_activation_record_details must be an object when present")
    required = ("n_frame", "live_registers", "burden_floor", "per_burden")
    missing = [key for key in required if key not in details]
    if not missing:
        return
    if not isinstance(canonical_nar, dict):
        raise HarnessError(
            "stage-06 normalized_activation_record_details must include full NAR fields "
            "when normalized_activation_record is not a structured object"
        )
    detail_frame = details.get("n_frame_details")
    if detail_frame is not None:
        if not isinstance(detail_frame, dict):
            raise HarnessError("stage-06 normalized_activation_record_details.n_frame_details must be an object")
        selected = non_empty_string(detail_frame.get("selected"))
        if selected is not None and selected != canonical_nar.get("n_frame"):
            raise HarnessError(
                "stage-06 normalized_activation_record_details.n_frame_details.selected "
                "must match canonical normalized_activation_record.n_frame"
            )
    for key in missing:
        if key not in canonical_nar:
            raise HarnessError(f"stage-06 canonical normalized_activation_record missing {key} for details hydration")
        details[key] = copy.deepcopy(canonical_nar[key])
    normalization = details.get("normalization")
    if normalization is None:
        normalization = {}
    if not isinstance(normalization, dict):
        raise HarnessError("stage-06 normalized_activation_record_details.normalization must be an object when present")
    normalization["hydrated_from_normalized_activation_record"] = missing
    normalization["canonical_n_frame"] = canonical_nar.get("n_frame")
    details["normalization"] = normalization


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


def canonical_burden_id(value: str) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"B[1-9][0-9]*", text):
        return text
    match = re.fullmatch(r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B", text)
    if match:
        return f"B{match.group(1).translate(SUP_DIGITS)}"
    return text


def public_burden_id(value: str) -> str:
    burden = canonical_burden_id(str(value or "").strip())
    if re.fullmatch(r"B[1-9][0-9]*", burden):
        return f"{burden[1:].translate(ASCII_TO_SUP_DIGITS)}B"
    return str(value or "").strip()


def public_burden_list(values: list[str]) -> str:
    return ", ".join(public_burden_id(value) for value in values)


def body_ref_burden_id(value: str) -> str:
    text = str(value or "").strip()
    match = BODY_REF_BURDEN_RE.fullmatch(text)
    if match:
        return canonical_burden_id(match.group("burden"))
    match = ASCII_BODY_REF_RE.fullmatch(text)
    if match:
        return f"B{match.group('burden')}"
    return ""


def body_ref_completion_flags(all_body_refs: list[str], assigned_body_refs: list[str]) -> dict[str, dict[str, bool]]:
    by_burden: dict[str, list[str]] = {}
    for ref in all_body_refs:
        burden_id = body_ref_burden_id(ref)
        if burden_id:
            by_burden.setdefault(burden_id, []).append(ref)
    assigned = set(assigned_body_refs)
    result: dict[str, dict[str, bool]] = {}
    for burden_refs in by_burden.values():
        for index, ref in enumerate(burden_refs):
            if ref not in assigned:
                continue
            result[ref] = {
                "first_for_burden": index == 0,
                "last_for_burden": index == len(burden_refs) - 1,
            }
    return result


def public_burden_set(values: list[str]) -> str:
    return "{" + public_burden_list(values) + "}" if values else "{}"


def public_graph_value(value: Any) -> str:
    rendered = str(value or "")
    rendered = re.sub(r"\bB[1-9][0-9]*\b", lambda match: public_burden_id(match.group(0)), rendered)
    return rendered.replace("->", "→")


def public_graph_line(b_total: list[str], edges: list[dict[str, str]]) -> str:
    graph_line, _roots, _parallel_groups = stage07_dependency_graph_scaffold(b_total, edges)
    return public_graph_value(graph_line)


def burden_id_from_land(land: str) -> str:
    match = LAND_TARGET_RE.search(land)
    return canonical_burden_id(match.group("target")) if match else ""


def stage04_act_details_by_ref(stage04: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    details: dict[str, dict[str, str]] = {}
    for row in list_field(stage04, "act_rows"):
        match = ACT_ROW_DETAIL_RE.match(row)
        if not match:
            continue
        body_ref = match.group("body_ref")
        if body_ref != match.group("body_ref_field"):
            continue
        details[body_ref] = {
            "row": row,
            "body_ref": body_ref,
            "owner": match.group("owner"),
            "operation": match.group("operation"),
            "pressure": match.group("pressure").strip(),
            "delta": match.group("delta").strip(),
            "delta_result": match.group("delta_result").strip(),
            "land": match.group("land").strip(),
            "burden_id": burden_id_from_land(match.group("land")),
        }
    return details


def stage04_owner_routes_by_burden(stage04: dict[str, Any] | None) -> dict[str, list[str]]:
    routes: dict[str, list[str]] = {}
    for detail in stage04_act_details_by_ref(stage04).values():
        burden = detail.get("burden_id") or ""
        owner = detail.get("owner") or ""
        operation = detail.get("operation") or ""
        if not burden or not owner:
            continue
        token = f"{owner}.{operation}" if operation else owner
        routes.setdefault(burden, []).append(token)
    return {burden: ordered_unique(tokens) for burden, tokens in routes.items()}


def stage06_owner_activation_details_by_ref(stage06: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(stage06, dict):
        return {}
    raw = stage06.get("owner_activation_details")
    if not isinstance(raw, list):
        return {}
    details: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        body_ref = item.get("body_ref")
        if isinstance(body_ref, str) and body_ref:
            details[body_ref] = item
    return details


def b_id(value: Any) -> str:
    burden = canonical_burden_id(str(value or "").strip())
    return burden if re.fullmatch(r"B[1-9][0-9]*", burden) else ""


def burden_endpoint_id(value: Any) -> str:
    direct = b_id(value)
    if direct:
        return direct
    text = str(value or "").strip()
    match = re.search(r"(?i)\bMRP\((?P<burden>[^)]+)\)", text)
    return b_id(match.group("burden")) if match else ""


def stage05_generated_burdens(stage05: dict[str, Any] | None) -> list[str]:
    if not isinstance(stage05, dict):
        return []
    raw = stage05.get("generated_burdens")
    generated: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                burden = b_id(item)
            elif isinstance(item, dict):
                burden = b_id(item.get("id") or item.get("burden_id") or item.get("burden") or item.get("target"))
            else:
                burden = ""
            if burden:
                generated.append(burden)
    elif isinstance(raw, dict):
        generated.extend(burden for burden in (b_id(key) for key in raw) if burden)
    return ordered_unique(generated)


def stage05_generated_burden_records(stage05: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(stage05, dict):
        return []
    raw = stage05.get("generated_burdens")
    if not isinstance(raw, (list, dict)):
        return []
    terminal_states = stage05.get("terminal_states") if isinstance(stage05.get("terminal_states"), dict) else {}
    records: list[dict[str, Any]] = []
    items: list[Any]
    if isinstance(raw, dict):
        items = [{"id": key, **value} if isinstance(value, dict) else {"id": key} for key, value in raw.items()]
    else:
        items = list(raw)
    for item in items:
        if isinstance(item, str):
            burden = b_id(item)
            record: dict[str, Any] = {"id": burden} if burden else {}
        elif isinstance(item, dict):
            burden = b_id(item.get("id") or item.get("burden_id") or item.get("burden") or item.get("target"))
            record = dict(item)
            if burden:
                record["id"] = burden
        else:
            continue
        burden = b_id(record.get("id"))
        if not burden:
            continue
        record["id"] = burden
        record.setdefault("type", "generated_burden")
        record.setdefault("terminal_state", str(terminal_states.get(burden) or "held-with-reason"))
        record.setdefault("activation_state", "generated_unexecuted")
        depth = record.get("generation_depth")
        if isinstance(depth, str) and depth.isdigit():
            record["generation_depth"] = int(depth)
        elif not isinstance(depth, int):
            record["generation_depth"] = 1
        records.append(record)
    seen: set[str] = set()
    unique_records: list[dict[str, Any]] = []
    for record in records:
        burden = str(record.get("id") or "")
        if burden in seen:
            continue
        seen.add(burden)
        unique_records.append(record)
    return unique_records


def stage05_unresolved_burdens(stage05: dict[str, Any] | None) -> list[str]:
    if not isinstance(stage05, dict):
        return []
    unresolved = [burden for burden in (b_id(item) for item in list_field(stage05, "unresolved_burdens")) if burden]
    proof = stage05.get("no_new_resultant_proof")
    if isinstance(proof, dict):
        unresolved.extend(burden for burden in (b_id(item) for item in list_field(proof, "unresolved_burdens")) if burden)
    return ordered_unique(unresolved)


def stage05_dependency_edges(stage05: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(stage05, dict):
        return []
    raw = stage05.get("dependency_graph_edges")
    if raw is None:
        graph = stage05.get("dependency_graph")
        raw = graph.get("edges") if isinstance(graph, dict) else None
    if not isinstance(raw, list):
        return []
    edges: list[dict[str, str]] = []
    for item in raw:
        edge_type = "held_burden_activation"
        if isinstance(item, dict):
            source = burden_endpoint_id(item.get("from") or item.get("source"))
            target = burden_endpoint_id(item.get("to") or item.get("target"))
            if isinstance(item.get("type"), str) and item["type"].strip():
                edge_type = item["type"].strip()
        elif isinstance(item, list) and len(item) == 2:
            source = burden_endpoint_id(item[0])
            target = burden_endpoint_id(item[1])
        else:
            continue
        if source and target:
            edges.append({"from": source, "to": target, "type": edge_type})
    return edges


def stage02_register_coverage(stage02: dict[str, Any] | None, burdens: list[str]) -> dict[str, list[str]]:
    coverage: dict[str, list[str]] = {}
    if isinstance(stage02, dict):
        details = stage02.get("burden_floor_details")
        if isinstance(details, list):
            for item in details:
                if not isinstance(item, dict):
                    continue
                burden = b_id(item.get("burden_id"))
                registers = item.get("register_types")
                if not burden or not isinstance(registers, list):
                    continue
                for register in registers:
                    if isinstance(register, str) and register.strip():
                        coverage.setdefault(register.strip(), []).append(burden)
    if coverage:
        return {register: ordered_unique(ids) for register, ids in coverage.items()}
    return {register: [burden] for register, burden in zip(list_field(stage02, "live_registers"), burdens)}


def stage02_burden_register_types(stage02: dict[str, Any] | None, burdens: list[str]) -> dict[str, list[str]]:
    burden_registers: dict[str, list[str]] = {}
    if isinstance(stage02, dict):
        details = stage02.get("burden_floor_details")
        if isinstance(details, list):
            for item in details:
                if not isinstance(item, dict):
                    continue
                burden = b_id(item.get("burden_id"))
                registers = item.get("register_types")
                if not burden or not isinstance(registers, list):
                    continue
                values = [str(register).strip() for register in registers if str(register).strip()]
                if values:
                    burden_registers[burden] = ordered_unique(values)
    if burden_registers:
        return burden_registers
    return {
        burden: [register]
        for burden, register in zip(burdens, list_field(stage02, "live_registers"))
        if register
    }


def stage07_route_type_for_burden(
    burden: str,
    edges: list[dict[str, str]],
    final_source: str,
    final_type: str,
) -> str:
    if burden == final_source and final_type:
        return final_type
    for edge in edges:
        if burden in {edge["from"], edge["to"]}:
            return edge.get("type") or "held_burden_activation"
    return "no_new_resultant"


def stage07_dependency_graph_scaffold(
    b_total: list[str],
    edges: list[dict[str, str]],
) -> tuple[str, list[str], list[list[str]]]:
    if not b_total:
        return "none", [], []
    if edges:
        incoming = {edge["to"] for edge in edges}
        roots = [burden for burden in b_total if burden not in incoming]
        graph_segments = [f"{root} (root)" for root in roots]
        graph_segments.extend(f"{edge['from']} -> {edge['to']}" for edge in edges)
        return "; ".join(graph_segments), roots, []
    roots = list(b_total)
    parallel_groups = [list(b_total)] if len(b_total) > 1 else []
    return " || ".join(f"{burden} (root)" for burden in b_total), roots, parallel_groups


def stage07_route_target_from_graph(value: Any) -> str:
    match = re.search(r"\bB[1-9][0-9]*\s*(?:->|→)\s*(B[1-9][0-9]*)\b", str(value or ""))
    return match.group(1) if match else ""


def stage07_stop_proof(source: str) -> dict[str, Any]:
    return {
        "escape_routes_checked": [
            {
                "type": "closure-boundary-immunity",
                "live": False,
                "basis": f"MRP({source}) reported no new closure-boundary-immunity route after R(H,Delta).",
            },
            {
                "type": "proof-carousel",
                "live": False,
                "basis": f"MRP({source}) reported no proof-carousel route after the terminal reread.",
            },
            {
                "type": "total-system-exhaustion",
                "live": False,
                "basis": "The bounded Stage 07 reply licenses only this scoped terminal state, not a global total-system proof.",
            },
            {
                "type": "doubt-churn",
                "live": False,
                "basis": f"MRP({source}) reports neutral divergence and null curl at STOP.",
            },
            {
                "type": "moral-tribunal",
                "live": False,
                "basis": f"MRP({source}) did not expose a live moral-tribunal route.",
            },
            {
                "type": "authority-order-recoil",
                "live": False,
                "basis": f"MRP({source}) did not expose a live authority-order recoil route.",
            },
            {
                "type": "hidden-framework-recoil",
                "live": False,
                "basis": f"MRP({source}) did not expose a live hidden-framework recoil route.",
            },
            {
                "type": "restoration-recoil",
                "subtype": "scope-protest",
                "live": False,
                "basis": f"MRP({source}) did not expose a live restoration-recoil route.",
            },
        ],
        "field_state_at_stop": {
            "divergence": "neutral",
            "curl": "null",
            "b_live": "empty",
            "kappa_residual": 0,
        },
        "stop_licensed": True,
    }


def stage07_formal_reread_states(
    mrp_resultants: list[dict[str, str]],
    terminal_states: dict[str, str],
    unresolved_burdens: list[str] | None = None,
    owner_routes_by_burden: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    unresolved = set(unresolved_burdens or [])
    owner_routes = owner_routes_by_burden or {}
    for row in mrp_resultants:
        source = row.get("source") or ""
        if not source:
            continue
        route_type = row.get("type") or "no_new_resultant"
        route = row.get("route") or "STOP"
        graph = row.get("graph") or "none"
        terminal_state = terminal_states.get(source, "landed")
        held_or_partial = source in unresolved or re.search(
            r"(?i)\b(?:hold|held|partial|carried[-_ ]?recurse)\b",
            terminal_state,
        ) is not None
        target = stage07_route_target_from_graph(graph)
        public_graph = public_graph_value(graph)
        public_source = public_burden_id(source)
        public_target = public_graph_value(target or source)
        state: dict[str, Any] = {
            "source_burden": source,
            "prior_land": f"Land({source}): terminal state {terminal_state}.",
            "delta": stage07_mrp_landed_delta(source, terminal_state, route_type),
            "reread": "R(H,Delta)",
            "divergence_state": "neutral",
            "curl_state": "null",
            "route_result_type": route_type,
            "mrp_resultant": f"{row.get('finding') or 'stable'} -> graph {graph}; route {route}",
            "graph_delta": graph,
            "preemption_basis": (
                f"bounded MRP row only; {public_source} remains {terminal_state} with HOLD/PARTIAL accounting"
                if held_or_partial and str(graph).strip().lower() == "none"
                else
                "terminal states landed; B_MRP empty; no generated burden remains"
                if str(graph).strip().lower() == "none"
                else "graph-bound MRP route recorded"
            ),
            "route": route,
        }
        if route_type == "held_burden_activation":
            state["route_gradient"] = (
                f"already-held/initial burden gradient points to {route} through {public_graph} after R(H,Δ)."
                if target
                else f"held/B_LA route after {source}."
            )
            if target:
                state["next_burden"] = target
            state["owner_route"] = owner_routes.get(target) or ["held"]
        elif route_type == "generated_burden_instantiation":
            state["route_gradient"] = (
                f"generated-gradient points to {route} through {public_graph} after Delta {public_source}; "
                f"newly generated {public_target} [generated-by: MRP({public_source})] is absent from 𝔅_LA "
                "and comes from post-Land field-pressure."
                if target
                else f"generated/new MRP route absent from B_LA after Delta {source}."
            )
            if target:
                state["next_burden"] = target
            state["owner_route"] = owner_routes.get(target) or ["generated"]
            state["generated_by"] = f"MRP({source})"
        else:
            state["route_gradient"] = (
                f"plain-gradient holds {public_source} as HOLD/PARTIAL after R(H,Δ); no new graph edge is licensed."
                if held_or_partial
                else f"plain-gradient points to {route} after {public_source}; no live pressure remains."
            )
            if route_type in {"no_new_resultant", "none", "stable"} or str(route).upper() == "STOP":
                state["no_new_resultant_proof"] = (
                    {
                        "escape_routes_checked": [],
                        "proved": False,
                        "basis": (
                            f"{source} remains {terminal_state}; no-new-resultant STOP is not licensed "
                            "for coverage completion while the burden is unresolved."
                        ),
                    }
                    if held_or_partial
                    else stage07_stop_proof(source)
                )
        states.append(state)
    return states


def stage07_mrp_landed_delta(source: str, terminal_state: str, route_type: str) -> str:
    return f"Delta {source}: terminal state {terminal_state}; MRP route result type {route_type}."


def stage07_mrp_reread_contract_guidance(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    if not isinstance(stage05, dict) or not stage05:
        return ""
    burden_floor = list_field(stage02, "burden_floor") or list_field(stage04, "act_burdens") or list_field(stage04, "act_targets")
    generated_records = stage05_generated_burden_records(stage05)
    generated_burdens = ordered_unique(
        [*stage05_generated_burdens(stage05), *[str(record.get("id") or "") for record in generated_records if record.get("id")]]
    )
    generated_record_by_id = {str(record.get("id")): dict(record) for record in generated_records if record.get("id")}
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    act_owner_routes_by_burden = stage04_owner_routes_by_burden(stage04)
    executed_act_burdens = set(act_owner_routes_by_burden)
    owner_routes_by_burden = dict(act_owner_routes_by_burden)
    terminal_states_raw = stage05.get("terminal_states")
    terminal_states = terminal_states_raw if isinstance(terminal_states_raw, dict) else {}
    terminal_states = {
        burden: str(terminal_states.get(burden) or "landed")
        for burden in b_total
    }
    edges = stage05_dependency_edges(stage05)
    reread_state = stage05.get("reread_state")
    if not isinstance(reread_state, dict):
        reread_state = {}
    final_source = burden_endpoint_id(reread_state.get("source_burden") or reread_state.get("source")) or (b_total[-1] if b_total else "")
    final_type = str(reread_state.get("route_result_type") or "no_new_resultant").strip().rstrip(".;:,")
    final_route = str(reread_state.get("route") or "STOP").strip().rstrip(".;:,")
    if final_type in {"none", "stable", ""}:
        final_type = "no_new_resultant"
    if not final_route:
        final_route = "STOP"
    unresolved_burdens = stage05_unresolved_burdens(stage05)
    def unresolved_terminal(burden: str) -> bool:
        return burden in unresolved_burdens or re.search(
            r"(?i)\b(?:hold|held|partial|carried[-_ ]?recurse)\b",
            terminal_states.get(burden, ""),
        ) is not None

    if (
        final_source
        and unresolved_terminal(final_source)
        and final_type in {"no_new_resultant", "none", "stable"}
        and final_route.upper() == "STOP"
    ):
        final_type = "hold_partial"
        final_route = "HOLD"
    if edges and final_type == "no_new_resultant" and final_route.upper() == "STOP":
        final_type = str(edges[0].get("type") or "generated_burden_instantiation")
        final_route = "RECURSE"
        final_source = edges[0]["from"]
    mrp_resultants = [
        {
            "source": edge["from"],
            "type": edge["type"],
            "finding": "genuine-dependent",
            "graph": f"{edge['from']} -> {edge['to']}",
            "route": "RECURSE",
        }
        for edge in edges
    ]
    has_matching_final_resultant = any(
        row["source"] == final_source and row["type"] == final_type for row in mrp_resultants
    )
    if final_source and not has_matching_final_resultant:
        mrp_resultants.append(
            {
                "source": final_source,
                "type": final_type,
                "finding": "partial-real" if final_type == "hold_partial" else "stable",
                "graph": "none",
                "route": final_route,
            }
        )

    for edge in edges:
        target = edge["to"]
        if target not in generated_burdens:
            continue
        record = generated_record_by_id.setdefault(
            target,
            {
                "id": target,
                "type": "generated_burden",
                "generation_depth": 1,
                "terminal_state": terminal_states.get(target, "held-with-reason"),
            },
        )
        record.setdefault("generated_by", f"MRP({edge['from']})")

    def route_tokens_for_burden(target: str) -> list[str]:
        tokens = list(owner_routes_by_burden.get(target) or [])
        record = generated_record_by_id.get(target, {})
        raw_route = record.get("required_owner_route")
        if isinstance(raw_route, list):
            tokens.extend(str(item).strip() for item in raw_route if str(item).strip())
        elif isinstance(raw_route, str) and raw_route.strip():
            tokens.append(raw_route.strip())
        return ordered_unique(tokens)

    def matched_route_line(target: str) -> str:
        tokens = route_tokens_for_burden(target)
        if not tokens:
            return "Matched owner/TTP route: [held] source-owned route pending explicit ACT execution"
        return "Matched owner/TTP route: " + ", ".join(f"[{token}]" for token in tokens)

    def generated_heading_lines() -> list[str]:
        lines: list[str] = []
        for burden in generated_burdens:
            record = generated_record_by_id.get(burden, {})
            generated_by = str(record.get("generated_by") or "")
            source = b_id(generated_by.replace("MRP(", "").replace(")", ""))
            if not source:
                for edge in edges:
                    if edge["to"] == burden:
                        source = edge["from"]
                        generated_by = f"MRP({source})"
                        break
            if not source:
                continue
            state = terminal_states.get(burden, "held-with-reason")
            title = str(record.get("title") or record.get("reason") or "generated MRP burden").strip()
            public_burden = public_burden_id(burden)
            public_source = public_burden_id(source)
            lines.extend(
                [
                    f"## Burden {burden[1:]} / {public_burden} [generated-by: MRP({public_source})] — {title}",
                    "### Layer A — Generated Burden Accounting",
                    f"- live noetic burden: {public_burden} [generated-by: MRP({public_source})]",
                    f"- generated status: not in 𝔅_LA; present in 𝔅_MRP; terminal_state={state}",
                    f"- {matched_route_line(burden)}",
                ]
            )
            if burden in executed_act_burdens:
                lines.append(
                    f"Land({public_burden}): generated MRP burden has visible Stage 04 ACT execution; "
                    "its landed/terminal status must match owner activations, MRP, and field_witness."
                )
            else:
                lines.append(
                    f"HOLD({public_burden}): generated MRP burden remains unresolved/unexecuted unless Stage 04 ACT rows actually execute it; "
                    "coverage_complete=false; route remains HOLD/PARTIAL/RECURSE."
                )
        return lines

    def mrp_block_lines(row: dict[str, str]) -> list[str]:
        source = row["source"]
        graph = row["graph"]
        route = row["route"]
        route_type = row["type"]
        finding = row["finding"]
        public_graph = public_graph_value(graph)
        public_source = public_burden_id(source)
        target = stage07_route_target_from_graph(graph)
        public_target = public_graph_value(target or source)
        held_or_partial = route_type == "hold_partial" or unresolved_terminal(source)
        landed_state = terminal_states.get(source, "landed")
        if route_type == "generated_burden_instantiation" and graph != "none":
            route_gradient = (
                f"generated-gradient points to {route} through {public_graph} after Delta {public_source}; "
                f"newly generated {public_target} [generated-by: MRP({public_source})] is absent from 𝔅_LA "
                "and comes from post-Land field-pressure."
            )
        elif route_type == "held_burden_activation" and graph != "none":
            route_gradient = (
                f"already-held/initial burden gradient points to {route} through {public_graph} after R(H,Δ)."
            )
        else:
            route_gradient = (
                f"plain-gradient points to {route} through {public_graph} after R(H,Δ)."
                if graph != "none"
                else (
                    f"plain-gradient holds {public_source} as HOLD/PARTIAL after R(H,Δ); no new graph edge is licensed."
                    if held_or_partial
                    else f"plain-gradient points to {route} after {public_source}; no live pressure remains."
                )
            )
        reread_line = (
            f"R(H,Δ): held routes rechecked: {public_graph}; "
            f"live remainder: {public_graph_value(target or source)}; release/next: {route}."
            if graph != "none"
            else (
                f"R(H,Δ): held routes rechecked: none; live remainder: {public_source}; release/next: HOLD."
                if held_or_partial
                else f"R(H,Δ): held routes rechecked: none; live remainder: no remaining burden; "
                f"release/next: {route} after {public_source}."
            )
        )
        preemption_basis = (
            f"bounded MRP row only; {public_source} remains {landed_state} with HOLD/PARTIAL accounting"
            if held_or_partial and graph == "none"
            else "terminal states landed; B_MRP empty; no generated burden remains"
            if graph == "none"
            else "graph-bound MRP route recorded"
        )
        landed_delta = stage07_mrp_landed_delta(source, landed_state, route_type)
        return [
            "[Mid-Reread Pressure]",
            f"Target: MRP({public_source}) / Stage 05 terminal MRP source",
            reread_line,
            f"Landed delta: {landed_delta}",
            "Field diagnostics: del-dot B: neutral / no remaining burden; del-cross kappa: null / no circular dependency.",
            f"Route-gradient: {route_gradient}",
            matched_route_line(target or source),
            f"Finding: {finding}",
            f"MRP route result type: {route_type}",
            f"MRP resultant: {finding} -> graph {public_graph}; route {route}",
            f"Graph delta: {public_graph}",
            f"Pre-emption basis: {preemption_basis}",
            "LoopBreak: not needed",
            f"Route: {route}",
            "Boundary: T_lang does not imply guaranteed uptake.",
        ]

    terminal_lines = [
        f"{public_burden_id(burden)}: {terminal_states.get(burden, 'landed')}"
        for burden in b_total
    ]
    visible_lines: list[str] = []
    for row in mrp_resultants:
        visible_lines.extend(mrp_block_lines(row))
    visible_lines.extend(generated_heading_lines())
    visible_lines.extend(["Terminal states:", *terminal_lines])
    lines = [
        "",
        "Stage 07 public MRP block contract:",
        "- Print these checker-complete public MRP blocks in the MRP/reread/terminal section before prose expansion:",
        *[f"  {line}" for line in visible_lines],
        "- Emit one `[Mid-Reread Pressure]` block for every Stage 05 / field_witness `mrp_resultants[]` source; do not summarize a B1-B6 chain as one MRP block.",
        "- `Target:` is required and must name the Stage 05 MRP source burden in public notation, for example `MRP(⁴B)`; do not leave the target implicit in prose.",
        "- `Landed delta:` must use the exact same canonical delta string as `field_witness.formal_reread_states[].delta`.",
        "- `MRP route result type:` must be one canonical token with no trailing punctuation: `held_burden_activation`, `generated_burden_instantiation`, `no_new_resultant`, `loopbreak`, or `hold_partial`.",
        "- `MRP resultant:`, `Graph delta:`, `Pre-emption basis:`, and `Route:` are required public fields; field_witness and Closure/Reconstruction Witness mirrors do not replace them.",
        "- For terminal STOP/no-new-resultant, use `Graph delta: none`, `Route: STOP`, and do not invent a graph edge.",
        "- For generated or held routes, use the exact Stage 05 graph edge in `Graph delta:` and `MRP resultant:`.",
        "- Do not rely on a later `MRP(ⁿB): ...` closure-ledger row as the only public MRP evidence; the `[Mid-Reread Pressure]` block itself must be parseable.",
    ]
    return "\n".join(lines)


def stage07_layer_a_contract_guidance(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    burden_floor = list_field(stage02, "burden_floor") or list_field(stage04, "act_burdens") or list_field(stage04, "act_targets")
    if not burden_floor:
        return ""
    generated_burdens = stage05_generated_burdens(stage05)
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    live_registers = list_field(stage02, "live_registers")
    burden_registers = stage02_burden_register_types(stage02, burden_floor)
    burden_rows = []
    for burden in burden_floor:
        registers = burden_registers.get(burden, [])
        register_text = ", ".join(registers) if registers else "register-types-from-Stage-02"
        burden_rows.append(f"{public_burden_id(burden)} [{register_text}] status=initial-live")

    visible_lines = [
        f"Live registers: {', '.join(live_registers)}" if live_registers else "Live registers: none",
        f"Initial burden set: [{public_burden_list(burden_floor)}]",
        f"𝔅_LA (B_LA) = {public_burden_set(burden_floor)}",
        f"𝔅_MRP (B_MRP) = {public_burden_set(generated_burdens)}",
        f"𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {public_burden_set(b_total)}",
        "Layer A burden/register rows:",
        *burden_rows,
    ]
    lines = [
        "",
        "Stage 07 Layer A parser-stable contract:",
        "- Print these checker-owned Layer A lines near the top of the Layer A section before prose expansion:",
        *[f"  {line}" for line in visible_lines],
        "- Do not replace `Initial burden set: [...]` with `Initial burden set ledger:`; prose ledgers may follow only after the exact line exists.",
        "- `𝔅_LA (B_LA)` must equal the initial burden set; `𝔅_MRP (B_MRP)` must contain only Stage 05 generated burdens and must be `{}` when there are none.",
        "- `𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP` is required exactly as the public total-ledger relation, followed by the concrete public burden set.",
        "- Each Layer A burden/register row must expose the burden ID and its Stage 02 register type(s) so the field witness can prove live-register floor coverage.",
    ]
    return "\n".join(lines)


def stage07_act_contract_guidance(
    previous_stages: list[dict[str, Any]],
    assigned_body_refs: list[str],
) -> str:
    if not assigned_body_refs:
        return ""
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage06 = stage_by_id(previous_stages, "stage-06-field-witness-nar")
    act_details = stage04_act_details_by_ref(stage04)
    owner_details = stage06_owner_activation_details_by_ref(stage06)
    all_body_refs = list_field(stage04, "act_body_refs")
    completion_flags = body_ref_completion_flags(all_body_refs, assigned_body_refs)
    missing = [ref for ref in assigned_body_refs if ref not in act_details]
    if missing:
        raise HarnessError(f"compiled Stage 07 ACT prompt missing canonical Stage 04 row(s): {missing}")

    lines = [
        "",
        "Stage 07 NLA semantic-faithfulness contract for this ACT slice:",
        "- Copy these canonical Stage 04 ACT rows exactly; do not rewrite their owner, operation, pressure, delta, body_ref, or Land slots:",
    ]
    lines.extend(f"  {act_details[ref]['row']}" for ref in assigned_body_refs)
    lines.extend(
        [
            "- Do not write malformed rows such as `⟦ACT [owner.operation] ...⟧`; the body_ref must appear immediately after `ACT`.",
            "- After each copied ACT row, emit exactly one dereferenceable public submove block for the same body_ref.",
            "- Emit a `## Burden N / ⁿB` heading only when this section contains the first Stage 04 body_ref for that burden.",
            "- If this section continues a burden started in the prior ACT slice, continue with the next submove only; do not repeat the burden heading.",
            "- Each submove block heading must begin `{body_ref}[{owner}] - ...` with the owner token only; put the operation in the `Operation:` facet.",
            "- Each submove block must contain `Target:`, `Operation:`, `Result/state-change:`, and `Contribution-to-Land(Bn):` facets.",
            "- The block prose must make the ACT pressure, operation, delta/result, and Land(Bn) contribution recoverable without relying on the ACT row alone.",
            "- Emit standalone public landing lines such as `Land(Bn): ...` or `HOLD(Bn): ...` only after the final Stage 04 body_ref for that burden; `Contribution-to-Land(Bn):` alone is not a landing line.",
            "- Never print `Land(Bn):` for a burden while another assigned or later Stage 04 body_ref for the same burden remains unrendered.",
            "Required submove block skeletons:",
        ]
    )
    landing_lines: list[str] = []
    seen_landing_targets: set[str] = set()
    for ref in assigned_body_refs:
        detail = dict(act_details[ref])
        mirror = owner_details.get(ref, {})
        if isinstance(mirror.get("burden_id"), str) and mirror["burden_id"]:
            detail["burden_id"] = str(mirror["burden_id"])
        burden_id = detail["burden_id"] or canonical_burden_id(ref.split("B", 1)[0] + "B")
        flags = completion_flags.get(ref, {})
        public_burden = public_burden_id(burden_id)
        if flags.get("first_for_burden"):
            lines.append(f"- Start burden block: `## Burden {burden_id[1:]} / {public_burden} — <burden-local title>` before {ref}.")
        else:
            lines.append(f"- Continue the existing {public_burden} burden block for {ref}; do not emit a new burden heading.")
        if burden_id and flags.get("last_for_burden") and burden_id not in seen_landing_targets:
            seen_landing_targets.add(burden_id)
            landing_lines.append(
                f"  Land({public_burden}): summarize the cumulative state delta from the visible submove block(s); "
                f"use `HOLD({public_burden}):` instead if the burden is not landed."
            )
        lines.extend(
            [
                f"- {ref}[{detail['owner']}] - {detail['operation']} over {detail['pressure']}",
                f"  Target: {detail['pressure']}.",
                f"  Operation: {detail['operation']} must act on {detail['pressure']} with owner family {detail['owner']}.",
                f"  Result/state-change: {detail['delta_result']}; state-change must be visible in local prose.",
                f"  Contribution-to-Land({public_burden}): explain how {detail['delta_result']} contributes to Land({public_burden}).",
                "  TTP Operation Body: expand the local governed operation in ordinary public prose.",
            ]
        )
    if landing_lines:
        lines.extend(["Required standalone landing lines for this ACT slice:", *landing_lines])
    return "\n".join(lines)


def stage07_field_witness_contract_guidance(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    stage06 = stage_by_id(previous_stages, "stage-06-field-witness-nar")
    act_details = stage04_act_details_by_ref(stage04)
    if not act_details:
        return ""
    burden_floor = list_field(stage02, "burden_floor") or list_field(stage04, "act_burdens") or list_field(stage04, "act_targets")
    generated_records = stage05_generated_burden_records(stage05)
    generated_burdens = ordered_unique(
        [*stage05_generated_burdens(stage05), *[str(record.get("id") or "") for record in generated_records if record.get("id")]]
    )
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    act_owner_routes_by_burden = stage04_owner_routes_by_burden(stage04)
    executed_act_burdens = set(act_owner_routes_by_burden)
    owner_routes_by_burden = dict(act_owner_routes_by_burden)
    terminal_states = stage05.get("terminal_states") if isinstance(stage05, dict) else {}
    if not isinstance(terminal_states, dict):
        terminal_states = {}
    terminal_states = {burden: str(terminal_states.get(burden) or "landed") for burden in b_total}
    edges = stage05_dependency_edges(stage05)
    reread_state = stage05.get("reread_state") if isinstance(stage05, dict) else {}
    if not isinstance(reread_state, dict):
        reread_state = {}
    final_source = burden_endpoint_id(reread_state.get("source_burden") or reread_state.get("source")) or (b_total[-1] if b_total else "")
    final_type = str(reread_state.get("route_result_type") or "no_new_resultant").strip().rstrip(".;:,")
    final_route = str(reread_state.get("route") or "STOP").strip().rstrip(".;:,")
    unresolved_burdens = stage05_unresolved_burdens(stage05)
    def unresolved_terminal(burden: str) -> bool:
        return burden in unresolved_burdens or re.search(
            r"(?i)\b(?:hold|held|partial|carried[-_ ]?recurse)\b",
            terminal_states.get(burden, ""),
        ) is not None

    if (
        final_source
        and unresolved_terminal(final_source)
        and final_type in {"no_new_resultant", "none", "stable", ""}
        and final_route.upper() == "STOP"
    ):
        final_type = "hold_partial"
        final_route = "HOLD"
    live_registers = list_field(stage02, "live_registers")
    diagnostic_coverage = stage02_register_coverage(stage02, burden_floor)
    burden_registers = stage02_burden_register_types(stage02, burden_floor)
    generated_record_by_id = {str(record.get("id")): dict(record) for record in generated_records if record.get("id")}
    for edge in edges:
        target = edge["to"]
        if target not in generated_burdens:
            continue
        record = generated_record_by_id.setdefault(
            target,
            {
                "id": target,
                "type": "generated_burden",
                "generation_depth": 1,
                "terminal_state": terminal_states.get(target, "held-with-reason"),
                "activation_state": "generated_unexecuted",
            },
        )
        record.setdefault("generated_by", f"MRP({edge['from']})")
        record.setdefault("reason", f"generated by {edge['from']} -> {target}")
        raw_route = record.get("required_owner_route")
        tokens: list[str] = []
        if isinstance(raw_route, list):
            tokens.extend(str(item).strip() for item in raw_route if str(item).strip())
        elif isinstance(raw_route, str) and raw_route.strip():
            tokens.append(raw_route.strip())
        if tokens:
            owner_routes_by_burden[target] = ordered_unique([*(owner_routes_by_burden.get(target) or []), *tokens])
    graph_line, roots, parallel_groups = stage07_dependency_graph_scaffold(b_total, edges)
    closed_terminal_states = {"landed", "cleared", "discharged-as-derivative", "held-with-reason"}
    coverage_complete = not unresolved_burdens and all(
        str(state).strip() in closed_terminal_states for state in terminal_states.values()
    )
    unresolved_text = ", ".join(unresolved_burdens)
    closure_status = (
        "coverage_complete=true"
        if coverage_complete
        else f"coverage_complete=false; unresolved_burdens=[{unresolved_text}]"
    )
    divergence_status = "neutral" if coverage_complete else f"non-neutral / unresolved_burdens=[{unresolved_text}]"
    curl_status = "null" if coverage_complete else f"unresolved / generated_burden_hold=[{unresolved_text}]"
    incoming_source_by_target = {edge["to"]: edge["from"] for edge in edges}
    owner_activation_rows: list[dict[str, Any]] = []
    nar_rows: list[dict[str, Any]] = []
    for ref, detail in act_details.items():
        target = detail["burden_id"]
        route_type = stage07_route_type_for_burden(target, edges, final_source, final_type)
        incoming_source = incoming_source_by_target.get(target)
        source = target if target in roots or not incoming_source else f"MRP({incoming_source})"
        if target in generated_burdens:
            generated_source = str(generated_record_by_id.get(target, {}).get("generated_by") or "")
            if generated_source:
                source = generated_source
        owner_activation_rows.append(
            {
                "body_ref": ref,
                "source": source,
                "target": target,
                "owner": detail["owner"],
                "owner_id": detail["owner"],
                "operation": detail["operation"],
                "pressure": detail["pressure"],
                "delta": f"{detail['delta']}:{detail['delta_result']}",
                "delta_result": detail["delta_result"],
                "land": detail["land"],
                "land_target": target,
                "terminal_state": terminal_states.get(target, "landed"),
                "mrp_route_result_type": route_type,
            }
        )
        nar_rows.append(
            {
                "burden_id": target,
                "owner_id": detail["owner"],
                "operation": detail["operation"],
                "delta_result": detail["delta_result"],
                "mrp_route_result_type": route_type,
                "terminal_state": terminal_states.get(target, "landed"),
                "generation_depth": 0 if target in burden_floor else 1,
            }
        )
    for burden in generated_burdens:
        if any(row.get("burden_id") == burden for row in nar_rows):
            continue
        record = generated_record_by_id.get(burden, {})
        route_type = stage07_route_type_for_burden(burden, edges, final_source, final_type)
        nar_rows.append(
            {
                "burden_id": burden,
                "owner_id": "MRP",
                "operation": route_type or "generated-burden-instantiation",
                "delta_result": str(record.get("reason") or terminal_states.get(burden) or "generated burden held"),
                "mrp_route_result_type": route_type,
                "terminal_state": terminal_states.get(burden, "held-with-reason"),
                "generation_depth": int(record.get("generation_depth") or 1),
            }
        )
    mrp_resultants = [
        {
            "source": edge["from"],
            "type": edge["type"],
            "finding": "genuine-dependent",
            "graph": f"{edge['from']} -> {edge['to']}",
            "route": "RECURSE",
        }
        for edge in edges
    ]
    has_matching_final_resultant = any(
        row["source"] == final_source and row["type"] == final_type for row in mrp_resultants
    )
    if final_source and not has_matching_final_resultant and (
        final_type in {"no_new_resultant", "none", "stable", "hold_partial"} or final_route.upper() in {"STOP", "HOLD"}
    ):
        mrp_resultants.append(
            {
                "source": final_source,
                "type": final_type,
                "finding": "partial-real" if final_type == "hold_partial" else "stable",
                "graph": "none",
                "route": final_route,
            }
        )
    formal_reread_states = stage07_formal_reread_states(
        mrp_resultants,
        terminal_states,
        unresolved_burdens=unresolved_burdens,
        owner_routes_by_burden=owner_routes_by_burden,
    )

    def terminal_state_line(burden: str) -> str:
        state = terminal_states.get(burden, "landed")
        if burden in generated_burdens:
            record = generated_record_by_id.get(burden, {})
            source = str(record.get("generated_by") or "MRP(source)")
            reason = str(record.get("reason") or "generated burden is held at this Stage 07 boundary")
            if burden in executed_act_burdens:
                return (
                    f"{public_burden_id(burden)}: {state} / {public_graph_value(source)} / "
                    f"visible Stage 04 ACT rows / {reason}"
                )
            return f"{public_burden_id(burden)}: {state} / {public_graph_value(source)} / no Stage 04 ACT rows / {reason}"
        return f"{public_burden_id(burden)}: {state} / ACT owners / landed by visible owner activations"

    visible_lines = [
        f"Initial burden set: [{public_burden_list(burden_floor)}]",
        f"𝔅_LA (B_LA) = {public_burden_set(burden_floor)}",
        f"𝔅_MRP (B_MRP) = {public_burden_set(generated_burdens)}",
        f"𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {public_burden_set(b_total)}",
        "Burden dependency graph:",
        public_graph_line(b_total, edges),
        "Terminal states:",
        *[terminal_state_line(burden) for burden in b_total],
        "Owner activations:",
        *[detail["row"] for detail in act_details.values()],
        "MRP resultants:",
        *[
            f"MRP({public_burden_id(row['source'])}): type={row['type']}; finding={row['finding']}; graph={public_graph_value(row['graph'])}; route={row['route']}"
            for row in mrp_resultants
        ],
        "Formal reread states:",
        *[
            f"formal_reread_state({row['source_burden']}): reread={row['reread']}; type={row['route_result_type']}; graph={row['graph_delta']}; route={row['route']}"
            for row in formal_reread_states
        ],
        f"∇·B: {divergence_status} / runtime execution field remains bounded to the displayed handoff",
        f"∇×κ: {curl_status} / runtime execution field remains bounded to the displayed handoff",
        f"𝒞(Ψᴺ): {'COMPLETE' if coverage_complete else 'HOLD'} / {closure_status}; runtime execution field remains bounded to the displayed handoff",
        "T_lang: PsiN -> PsiI: partial coupling boundary; no guaranteed uptake",
    ]
    nodes_payload: list[dict[str, Any]] = []
    for burden in b_total:
        node: dict[str, Any] = {
            "id": burden,
            "type": "generated_burden" if burden in generated_burdens else "burden",
            "register_types": burden_registers.get(burden, []),
            "state": terminal_states.get(burden, "landed"),
            "generation_depth": 1 if burden in generated_burdens else 0,
        }
        if burden in generated_burdens:
            record = generated_record_by_id.get(burden, {})
            if record.get("generated_by"):
                node["generated_by"] = record["generated_by"]
        nodes_payload.append(node)
    generated_payload = [generated_record_by_id[burden] for burden in generated_burdens if burden in generated_record_by_id]
    scaffold = {
        "B_LA": burden_floor,
        "B_MRP": generated_burdens,
        "B_total": b_total,
        "nodes": nodes_payload,
        "edges": edges,
        "generated_burdens": generated_payload,
        "mrp_resultants": mrp_resultants,
        "formal_reread_states": formal_reread_states,
        "field_diagnostics": {"divergence_check": divergence_status, "curl_check": curl_status},
        "terminal_states": terminal_states,
        "closure": {"status": closure_status, "unresolved_burdens": unresolved_burdens},
        "T_lang": "T_lang: PsiN -> PsiI: partial coupling boundary; no guaranteed uptake",
        "owner_activations": owner_activation_rows,
        "normalized_activation_record": {
            "n_frame": str((stage02 or {}).get("selected_n_frame") or (stage06 or {}).get("selected_n_frame") or "selected-n-frame"),
            "live_registers": live_registers,
            "burden_floor": burden_floor,
            "per_burden": nar_rows,
        },
        "coverage_proof": {
            "initial_burden_set": burden_floor,
            "terminal_states": terminal_states,
            "dependency_graph": {
                "nodes": b_total,
                "edges": [{"from": edge["from"], "to": edge["to"]} for edge in edges],
                "roots": roots,
                "parallel_groups": parallel_groups,
                "acyclic": True,
            },
            "diagnostic_completeness": {
                "live_registers": live_registers,
                "coverage": diagnostic_coverage,
                "complete": True,
            },
            "divergence_check": divergence_status,
            "curl_check": curl_status,
            "max_generation_depth": 1 if generated_burdens else 0,
            "coverage_complete": coverage_complete,
        },
    }
    lines = [
        "",
        "Stage 07 field_witness mirror contract:",
        "- After Closing Formulation, print the visible Closure/Reconstruction Witness ledger, then emit the `field_witness` JSON as the final machine payload using these exact line shapes:",
        *[f"  {line}" for line in visible_lines],
        "- If Stage 05 `generated_burdens` is empty, `𝔅_MRP (B_MRP)` is empty: visible `𝔅_MRP (B_MRP) = {}` and JSON `\"B_MRP\": []`; never place baseline Layer-A burdens in `B_MRP`.",
        "- Visible public burden IDs must use superscript notation such as `¹B`; JSON machine IDs remain canonical ASCII such as `B1`.",
        "- `𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP` is required in the visible ledger; JSON `B_total` must equal JSON `B_LA` plus `B_MRP` in order.",
        "- `coverage_proof.dependency_graph` is required with `nodes`, `edges`, `roots`, and boolean `acyclic`.",
        "- If the dependency edge list is empty and `B_total` has multiple nodes, the visible graph line must declare every node as a parallel root, for example `¹B (root) || ²B (root)`, and JSON `parallel_groups` must mirror the full node group.",
        "- If the dependency edge list is non-empty, the visible graph must declare every root node plus every actual edge, for example `¹B (root); ²B (root); ⁴B → ⁵B`; never convert an edgeful graph into `¹B (root) → ⁵B` unless Stage 05 actually records that edge.",
        "- A generated `B_MRP` burden must appear in `generated_burdens[]`, `nodes[]`, `B_total`, `terminal_states`, `coverage_proof.dependency_graph.nodes`, and `normalized_activation_record.per_burden[]` with `generation_depth` and `generated_by` provenance.",
        "- If Stage 05 leaves `unresolved_burdens` or `no_new_resultant_proof.proved=false`, do not claim `coverage_complete=true`; set `coverage_complete` false and keep the generated burden held/unresolved instead of synthesizing terminal STOP proof.",
        "- Do not synthesize a generated-burden `MRP(Bn)` row with `graph=none`; visible generated/held MRP resultants must expose the concrete Stage 05 graph edge such as `⁴B → ⁵B`, while JSON mirrors keep ASCII machine IDs.",
        "- Each `nodes[]` burden payload must include `register_types` copied from Stage 02 `burden_floor_details` when live registers are present.",
        "- Every `owner_activations[]` object must include both `target` and `land_target`; the checker reads `target` for terminal-state evidence.",
        "- Emit one `normalized_activation_record.per_burden[]` row per `owner_activations[]` mirror, plus one MRP-owned row for each generated `B_MRP` burden that has no Stage 04 ACT rows; do not collapse these into one summary row per burden.",
        "- Each NAR row must include `burden_id`, `owner_id`, `operation`, `delta_result`, `mrp_route_result_type`, `terminal_state`, and integer `generation_depth`.",
        "- `formal_reread_states[]` is required; emit exactly one row for every `mrp_resultants[]` source and keep `source_burden`, `route_result_type`, `graph_delta`, and `route` aligned with that MRP row.",
        "- `curl_state` values must be parser-stable JSON strings. When curl is absent/resolved, emit JSON string `\"null\"`, never bare JSON null.",
        "- Terminal `STOP` / `no_new_resultant` rows must set `reread` to `R(H,Delta)`, `divergence_state` to `neutral`, `curl_state` to JSON string `\"null\"`, `graph_delta` to `none`, omit `next_burden`, and include `no_new_resultant_proof.escape_routes_checked` as a JSON list.",
        "- If a terminal `STOP` / `no_new_resultant` row is only a bounded MRP row for a generated or unresolved burden, keep `coverage_complete=false`, set `no_new_resultant_proof.proved=false`, and keep explicit HOLD/PARTIAL accounting instead of claiming clean closure.",
        "- For every `owner_activations[]` mirror, `owner` must contain only the ACT owner token or owner family, not `owner.operation`.",
        "- Put the operation in the separate `operation` field, and keep `owner_id` aligned with the owner token.",
        "- Do not set `owner` to `owner.operation`; for example use `\"owner\": \"FPD\"` and `\"operation\": \"foreign-premise-detection\"`.",
        "- Required field_witness scaffold and checker-owned keys (copy field names exactly; adapt prose details but keep the structure):",
        json.dumps(scaffold, ensure_ascii=False, indent=2),
        "- Mirror these exact ACT-visible values by body_ref; include `target` exactly as shown:",
    ]
    for ref, detail in act_details.items():
        lines.append(
            "  "
            + json.dumps(
                {
                    "body_ref": ref,
                    "owner": detail["owner"],
                    "owner_id": detail["owner"],
                    "operation": detail["operation"],
                    "pressure": detail["pressure"],
                    "delta": f"{detail['delta']}:{detail['delta_result']}",
                    "delta_result": detail["delta_result"],
                    "land": detail["land"],
                    "target": detail["burden_id"],
                    "land_target": detail["burden_id"],
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(lines)


def first_json_object_from_text(text: str) -> dict[str, Any] | None:
    cursor = 0
    decoder = json.JSONDecoder()
    while True:
        start = text.find("{", cursor)
        if start < 0:
            return None
        try:
            decoded, _end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            cursor = start + 1
            continue
        return decoded if isinstance(decoded, dict) else None


def contract_scaffold_lines(contract: str, marker: str) -> list[str]:
    lines = contract.splitlines()
    collecting = False
    collected: list[str] = []
    for line in lines:
        if not collecting:
            if marker in line:
                collecting = True
            continue
        if line.startswith("  "):
            collected.append(line[2:])
            continue
        if collected and line.startswith("- "):
            break
    return collected


def stage07_mrp_reread_section_scaffold(previous_stages: list[dict[str, Any]]) -> str:
    contract = stage07_mrp_reread_contract_guidance(previous_stages)
    lines = contract_scaffold_lines(contract, "Print these checker-complete public MRP blocks")
    if not lines:
        return ""
    return "\n".join(lines).rstrip() + "\n"


def stage07_field_witness_section_scaffold(previous_stages: list[dict[str, Any]]) -> str:
    contract = stage07_field_witness_contract_guidance(previous_stages)
    visible_lines = contract_scaffold_lines(
        contract,
        "print the visible Closure/Reconstruction Witness ledger",
    )
    if not visible_lines:
        return ""
    scaffold_tail = contract.split("Required field_witness scaffold", 1)[-1]
    payload = first_json_object_from_text(scaffold_tail)
    if payload is None:
        return ""
    return (
        "Closure/Reconstruction Witness\n"
        + "\n".join(visible_lines).rstrip()
        + "\n\nfield_witness\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n"
    )


RESTORATIVE_SLOT_PATTERNS = (
    re.compile(r"(?im)^\s*(?:[-*]\s*)?Restored criterion/(?:order|orientation)\s*:\s*\S"),
    re.compile(r"(?im)^\s*(?:[-*]\s*)?Relieved pressure\s*:\s*\S"),
    re.compile(r"(?im)^\s*(?:[-*]\s*)?Held/scoped/reopenable remainder\s*:\s*\S"),
)


def restorative_response_slots_present(text: str) -> bool:
    return all(pattern.search(text) for pattern in RESTORATIVE_SLOT_PATTERNS)


def stage07_restorative_response_section_scaffold(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    burden_floor = list_field(stage02, "burden_floor") or list_field(stage05, "B_LA")
    generated_burdens = stage05_generated_burdens(stage05)
    unresolved_burdens = list_field(stage05, "unresolved_burdens")
    if not unresolved_burdens and isinstance(stage05, dict):
        proof = stage05.get("no_new_resultant_proof")
        if isinstance(proof, dict):
            unresolved_burdens = [
                b_id(item) for item in proof.get("unresolved_burdens", []) if b_id(item)
            ]
    held = ordered_unique([*generated_burdens, *unresolved_burdens])
    floor_text = public_burden_list(burden_floor) if burden_floor else "the displayed baseline burden floor"
    held_text = public_burden_list(held) if held else "future concrete burdens only"
    if held:
        remainder = (
            f"Generated or unresolved burden(s) {held_text} remain held/scoped/reopenable "
            "unless a later bounded pass actually executes matching ACT rows; "
            "coverage_complete=false stays honest for this closure boundary."
        )
    else:
        remainder = (
            "Specific future objections remain reopenable only as concrete named burdens; "
            "no hidden proof-carousel or total-system demand is allowed to repair the landed reply."
        )
    return (
        "Restorative Response\n\n"
        f"Restored criterion/order: Preserve the landed source-owned burden order {floor_text} "
        "and return the field to tawhid, fitrah, and sound reason without letting a later model "
        "override the local proof state.\n\n"
        "Relieved pressure: The visible ACT and MRP rows block the reply's predicate-transfer, "
        "source-order, proof-stack, analogy, and worship-orientation pressure from governing "
        "the text before the text's own sender-sent order is heard.\n\n"
        f"Held/scoped/reopenable remainder: {remainder}\n"
    )


def stage07_closing_formulation_budget_supplement(previous_stages: list[dict[str, Any]]) -> str:
    stage02 = stage_by_id(previous_stages, "stage-02-layer-a-diagnostic-ir")
    stage05 = stage_by_id(previous_stages, "stage-05-mrp-reread-terminal-state")
    stage06 = stage_by_id(previous_stages, "stage-06-field-witness-nar")
    burden_floor = (
        list_field(stage02, "burden_floor")
        or list_field(stage06, "B_LA")
        or list_field(stage05, "B_LA")
    )
    generated_burdens = ordered_unique(
        [
            *stage05_generated_burdens(stage05),
            *list_field(stage06, "B_MRP"),
        ]
    )
    b_total = ordered_unique([*burden_floor, *generated_burdens])
    unresolved_burdens = ordered_unique(
        [
            *stage05_unresolved_burdens(stage05),
            *list_field(stage06, "unresolved_burdens"),
        ]
    )
    terminal_states = stage05.get("terminal_states") if isinstance(stage05, dict) else {}
    if not isinstance(terminal_states, dict):
        terminal_states = {}
    burden_registers = stage02_burden_register_types(stage02, burden_floor)
    generated_records = {
        str(record.get("id")): dict(record)
        for record in stage05_generated_burden_records(stage05)
        if record.get("id")
    }
    n_frame = ""
    if isinstance(stage02, dict):
        n_frame = str(stage02.get("selected_n_frame") or "")
    if not n_frame and isinstance(stage06, dict):
        n_frame = str(stage06.get("selected_n_frame") or "")
    if not n_frame:
        n_frame = "the selected noetic frame"

    lines = [
        "### Closure boundary confirmation",
        "",
        f"The final close remains tied to {n_frame}. It does not ask the reader to accept a total-system verdict before the displayed burdens have done their work. It keeps the reply's pressure ordered by the visible burden floor, the landed ACT rows, the MRP reread, and the held remainder.",
        "",
        "The closing therefore has three controlled claims. First, the stated reply fails where it tries to move the verse's predicate away from the addressed Father. Second, the repair is local to the argument actually made: word-placement, analogy, proof-text backread, co-knowledge inference, and worship-orientation pressure. Third, anything not executed as an ACT row remains reopenable as a named burden rather than being smuggled into a clean global close.",
        "",
        "### Burden-state recap",
        "",
    ]
    if not b_total:
        lines.append("The displayed burden ledger remains the governing scope of this close.")
    for burden in b_total:
        public_burden = public_burden_id(burden)
        state = str(terminal_states.get(burden) or ("generated-held" if burden in generated_burdens else "landed"))
        registers = ", ".join(burden_registers.get(burden, [])) or "local registers"
        if burden in generated_burdens:
            record = generated_records.get(burden, {})
            generated_by = str(record.get("generated_by") or f"MRP({burden})")
            lines.append(
                f"- {public_burden}: generated by {public_graph_value(generated_by)}; state={state}; registers={registers}. "
                "It is not counted as a baseline floor burden unless a later pass actually executes matching ACT rows."
            )
        else:
            lines.append(
                f"- {public_burden}: baseline burden; state={state}; registers={registers}. "
                "Its local close is limited to the visible owner operation and its public Land(...) consequence."
            )
    held_text = public_burden_list(unresolved_burdens) if unresolved_burdens else "none"
    lines.extend(
        [
            "",
            "### Reopenable remainder",
            "",
            f"The remaining live or generated burden set is {held_text}. When that set is non-empty, the close is intentionally a HOLD/PARTIAL close for that remainder. When it is empty, the close still remains bounded to concrete future burdens rather than to an unlimited proof-carousel.",
            "",
            "This matters for the reader because the answer should not win by compression. The reply is answered where its stated moves actually operate: the exclusivity of the addressed Father, the sender/sent relation, the category mistake in the analogy, the secondary status of proof-text backreads, and the difference between salvific knowledge of the sent Messiah and identity with the God who sent him.",
            "",
            "The final formulation is therefore deliberately disciplined. It restores the order of the verse, names the burden that remains open if a further answer wants to continue, and refuses to convert a bounded refutation into an unbounded claim that every possible downstream doctrine has been exhausted.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def compiled_section_budget_guardrail(
    section_role: str,
    text: str,
    previous_stages: list[dict[str, Any]],
    section_min_bytes: int,
) -> tuple[str, dict[str, Any] | None]:
    if section_min_bytes <= 0 or len(text.encode("utf-8")) >= section_min_bytes:
        return text, None
    if section_role != "closing_formulation" or "### Closure boundary confirmation" in text:
        return text, None
    supplement = stage07_closing_formulation_budget_supplement(previous_stages)
    if not supplement:
        return text, None
    supplemented = text.rstrip() + "\n\n" + supplement
    return supplemented, {
        "role": section_role,
        "compiled_section_budget_guardrail": True,
        "original_bytes": len(text.encode("utf-8")),
        "canonical_bytes": len(supplemented.encode("utf-8")),
        "section_min_bytes": section_min_bytes,
    }


def canonical_compiled_structural_section(
    section_role: str,
    text: str,
    previous_stages: list[dict[str, Any]],
) -> tuple[str, dict[str, Any] | None]:
    if section_role == "mrp_reread_terminal":
        scaffold = stage07_mrp_reread_section_scaffold(previous_stages)
    elif section_role == "field_witness_nar":
        scaffold = stage07_field_witness_section_scaffold(previous_stages)
    elif section_role == "restorative_response":
        if restorative_response_slots_present(text):
            return text, None
        scaffold = stage07_restorative_response_section_scaffold(previous_stages)
        body = re.sub(
            r"(?is)^\s*(?:#{1,6}\s*)?Restorative Response\s*",
            "",
            text,
            count=1,
        ).lstrip()
        if body:
            scaffold = scaffold.rstrip() + "\n\n" + body.rstrip() + "\n"
    else:
        return text, None
    if not scaffold:
        return text, None
    if text.strip() == scaffold.strip():
        return text, None
    return scaffold, {
        "role": section_role,
        "canonicalized_structural_stage07_section": True,
        "original_bytes": len(text.encode("utf-8")),
        "canonical_bytes": len(scaffold.encode("utf-8")),
    }


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


def stage04_delta_vocabulary_guidance(previous_stages: list[dict[str, Any]]) -> str:
    stage03 = stage_by_id(previous_stages, "stage-03-routing-owner-gate")
    if not isinstance(stage03, dict):
        return ""
    owners: list[str] = []
    for route in stage03.get("owner_routes") or []:
        if isinstance(route, dict):
            owner = non_empty_string(route.get("owner_id") or route.get("owner"))
            if owner:
                owners.append(owner)
        elif isinstance(route, str) and route.strip():
            owners.append(route.strip())
    for detail in stage03.get("owner_route_details") or []:
        if not isinstance(detail, dict):
            continue
        owner = non_empty_string(detail.get("owner_id") or detail.get("owner"))
        if owner:
            owners.append(owner)
    families = ordered_unique(
        [
            family
            for owner in owners
            for family in [canonical_delta_owner(owner)]
            if family and family in DELTA_RESULT_VOCABULARY
        ]
    )
    if not families:
        return ""
    lines = [
        "",
        "Stage 04 controlled delta_result vocabulary:",
        "- The token after the colon in each `Δ=...:<delta_result>` slot must be one of the source-owned owner-local tokens below.",
        "- Do not invent near-synonyms such as `predicate-transfer-blocked`, `only-scope-defined`, `proof-stack-routed`, or `entailment-bounded`.",
    ]
    for family in families:
        tokens = ", ".join(sorted(DELTA_RESULT_VOCABULARY[family]))
        lines.append(f"- {family}: {tokens}")
    return "\n".join(lines)


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
    extra_guidance = ""
    if stage_id == "stage-04-burden-execution-act":
        extra_guidance = stage04_delta_vocabulary_guidance(previous_stages)
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
{extra_guidance}

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
        ("restorative-response", "restorative_response"),
        ("closing-formulation", "closing_formulation"),
        ("field-witness-nar", "field_witness_nar"),
    ]


SECTION_BUDGET_ROLE_WEIGHTS = {
    "visible_opening": 5,
    "layer_a_diagnostic_ir": 10,
    "layer_b_act": 55,
    "mrp_reread_terminal": 1,
    "field_witness_nar": 1,
    "restorative_response": 18,
    "closing_formulation": 10,
}


def compiled_section_budgets(
    section_plan: list[tuple[str, str]],
    target_output_kb: int | None,
) -> dict[str, Any] | None:
    target_bytes = max(0, int(target_output_kb or 0)) * 1024
    if target_bytes <= 0:
        return None

    role_counts: dict[str, int] = {}
    for _section_id, role in section_plan:
        role_counts[role] = role_counts.get(role, 0) + 1

    role_min_bytes: dict[str, int] = {}
    role_remainders: list[tuple[int, str]] = []
    for role, weight in SECTION_BUDGET_ROLE_WEIGHTS.items():
        numerator = target_bytes * weight
        role_min_bytes[role] = numerator // 100
        role_remainders.append((numerator % 100, role))
    residual = target_bytes - sum(role_min_bytes.values())
    for _remainder, role in sorted(role_remainders, reverse=True)[:residual]:
        role_min_bytes[role] += 1
    min_section_bytes: dict[str, int] = {}
    role_seen: dict[str, int] = {}
    for section_id, role in section_plan:
        role_budget = role_min_bytes.get(role, 0)
        count = max(1, role_counts.get(role, 1))
        seen = role_seen.get(role, 0)
        base = role_budget // count
        remainder = role_budget % count
        min_section_bytes[section_id] = base + (1 if seen < remainder else 0)
        role_seen[role] = seen + 1

    return {
        "schema": staged_output.SECTION_BUDGET_SCHEMA,
        "target_output_bytes": target_bytes,
        "role_min_bytes": role_min_bytes,
        "min_section_bytes": min_section_bytes,
    }


def partition_body_refs(body_refs: list[str], section_ids: list[str]) -> list[dict[str, Any]]:
    if not section_ids:
        return []
    assignments = [{"section_id": section_id, "body_refs": []} for section_id in section_ids]
    if not body_refs:
        return assignments

    groups: list[list[str]] = []
    for body_ref in body_refs:
        burden_id = body_ref_burden_id(body_ref)
        if groups and burden_id and body_ref_burden_id(groups[-1][-1]) == burden_id:
            groups[-1].append(body_ref)
        else:
            groups.append([body_ref])

    if len(groups) >= len(assignments):
        group_index = 0
        for section_index, assignment in enumerate(assignments):
            remaining_sections = len(assignments) - section_index
            remaining_groups = len(groups) - group_index
            remaining_refs = sum(len(group) for group in groups[group_index:])
            target_refs = max(1, (remaining_refs + remaining_sections - 1) // remaining_sections)
            while group_index < len(groups):
                group = groups[group_index]
                if assignment["body_refs"] and remaining_groups <= remaining_sections:
                    break
                if assignment["body_refs"] and len(assignment["body_refs"]) + len(group) > target_refs:
                    break
                assignment["body_refs"].extend(group)
                group_index += 1
                remaining_groups = len(groups) - group_index
            if section_index == len(assignments) - 1 and group_index < len(groups):
                for group in groups[group_index:]:
                    assignment["body_refs"].extend(group)
                break
        return assignments

    cursor = 0
    total = len(body_refs)
    for section_index, assignment in enumerate(assignments):
        remaining_sections = len(assignments) - section_index
        remaining_refs = total - cursor
        if remaining_refs <= 0:
            break
        take = max(1, (remaining_refs + remaining_sections - 1) // remaining_sections)
        assignment["body_refs"].extend(body_refs[cursor : cursor + take])
        cursor += take
    return assignments


def compiled_act_partition(
    previous_stages: list[dict[str, Any]],
    section_plan: list[tuple[str, str]],
) -> dict[str, Any]:
    stage04 = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    body_refs = list_field(stage04, "act_body_refs")
    act_section_ids = [section_id for section_id, role in section_plan if role == "layer_b_act"]
    if not body_refs:
        raise HarnessError("compiled Stage 07 ACT partition requires Stage 04 act_body_refs")
    return {
        "schema": staged_output.ACT_PARTITION_SCHEMA,
        "assignments": partition_body_refs(body_refs, act_section_ids),
        "no_duplicate_body_refs": True,
        "all_assigned_refs_present": True,
        "contiguous_public_burden_groups": True,
    }


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
    section_min_bytes: int = 0,
    assigned_body_refs: list[str] | None = None,
) -> str:
    previous = json.dumps(compact_state(previous_stages), ensure_ascii=False, indent=2)
    target = max(0, int(target_output_kb or 0))
    section_floor = max(0, (target * 1024 + section_count - 1) // section_count) if target else 0
    stage04_for_prompt = stage_by_id(previous_stages, "stage-04-burden-execution-act")
    all_act_body_refs = list_field(stage04_for_prompt, "act_body_refs")
    assigned_for_prompt = assigned_body_refs or []
    first_act_body_ref = all_act_body_refs[0] if all_act_body_refs else ""
    is_first_act_slice = bool(assigned_for_prompt and assigned_for_prompt[0] == first_act_body_ref)
    layer_b_header_instruction = (
        "Include the exact governed header `## Layer B — Bounded Governed Response` because this is the first ACT slice. "
        if is_first_act_slice
        else "Do not emit `## Layer B — Bounded Governed Response`; the first ACT slice owns that single public Layer B header. "
    )
    role_guidance = {
        "visible_opening": (
            "Write only the visible opening for the governed answer. It must contain the exact banner "
            "`daee-epistemics — NOETIC FIELD EXECUTION`, plus the field/read/state surface a "
            "normal `/daee-epistemics` answer exposes. Do not include Layer B, field_witness, "
            "Restorative Response, or Closing Formulation."
        ),
        "layer_a_diagnostic_ir": (
            "Write only the compact Layer A / Diagnostic IR public surface. It must include a Layer A "
            "Compact DSL/IR or Diagnostic IR header, B_LA, B_MRP, B_total, and Initial burden set "
            "ledger lines. Do not include raw dev harness internals or downstream proof claims."
        ),
        "layer_b_act": (
            "Write only this bounded Layer B / ACT section. "
            + layer_b_header_instruction
            + "ACT-readable rows, body_ref tokens, local operation/result prose, and Land(...) surfaces "
            "consistent with Stage 04. Expand the operation bodies instead of summarizing them. "
            "Do not include MRP, field_witness, Restorative Response, or Closing Formulation. "
            "This section is an ACT partition slice inside one coherent public Layer B body."
        ),
        "mrp_reread_terminal": (
            "Write only the MRP/reread/terminal-state section consistent with Stage 05. It must include "
            "`[Mid-Reread Pressure]`, `R(H,Delta)` or `R(H,Δ)`, terminal states, `MRP route result type`, "
            "`Graph delta`, `Field diagnostics`, and the STOP/HOLD/PARTIAL/RECURSE route consequence. "
            "Do not include final verifier sidecars or retained proof claims."
        ),
        "field_witness_nar": (
            "Write only the Closure/Reconstruction Witness plus parser-stable `field_witness` JSON as the final compiled section after Closing Formulation. "
            "The section must contain a line that begins exactly `field_witness`, then a JSON object "
            "with `B_LA`, `B_MRP`, `B_total`, `coverage_proof`, `owner_activations`, "
            "`normalized_activation_record`, and any generated-burden/formal-reread mirrors required "
            "by Stage 06. The visible divergence/curl statuses must match "
            "`field_witness.coverage_proof.divergence_check` and `.curl_check`. Every visible ACT row "
            "must have exactly one `field_witness.owner_activations[]` mirror with `body_ref`, `owner`, "
            "`owner_id`, `operation`, `pressure`, `delta`, `delta_result`, `land`, `land_target`, "
            "`terminal_state`, `mrp_route_result_type`, and explicit `ordering_role` when those values are visible or validated "
            "upstream. Copy exact ACT-visible owner/operation/pressure/delta/Land values; do not invent "
            "missing proof values and do not add model-authored verification/self-claim fields. Sparse "
            "`owner_activations` are invalid for compiled Stage 07 proof output. Do not use prose-only "
            "`Field Witness` or prose-only `Normalized Activation Record` labels. Do not include Restorative Response or Closing Formulation here."
        ),
        "restorative_response": (
            "Write only the Restorative Response section. Begin with the exact public role heading `Restorative Response`. "
            "Carry explicit fitrah/tawhid and sound reason/ʿaql orientation in the endpoint. "
            "It must include these exact parser-stable lines before any extended prose: "
            "`Restored criterion/order: ...`, `Relieved pressure: ...`, and "
            "`Held/scoped/reopenable remainder: ...`. "
            "The remainder line must name any generated or unresolved B_MRP pressure that remains held/scoped/reopenable. "
            "Do not include Closing Formulation here. "
            "Do not claim guaranteed uptake, package/provenance, sidecar proof, retained promotion, "
            "broad model behavior, or broad A/B/C/D closure."
        ),
        "closing_formulation": (
            "Write only the Closing Formulation section. Begin with the exact public role heading `Closing Formulation`. "
            "Carry explicit fitrah/tawhid and sound reason/ʿaql orientation in the endpoint. "
            "It must include explicit high-mass slots for "
            "Established failure, Restored criterion/orientation, and Scoped boundary or Reopen boundary. "
            "Use these exact subsection labels: `### Established failure`, `### Restored criterion/orientation`, and either `### Scoped boundary` or `### Reopen boundary`. "
            "Do not claim guaranteed uptake, package/provenance, sidecar proof, retained promotion, "
            "broad model behavior, or broad A/B/C/D closure."
        ),
    }
    target_line = ""
    if target:
        section_budget_text = (
            f"This section's validator-owned minimum is {section_min_bytes} UTF-8 bytes. "
            if section_min_bytes
            else f"This section's rough share is {section_floor} bytes. "
        )
        target_line = (
            f"\nOverall compiled output floor: at least {target}KB across {section_count} sections. "
            f"{section_budget_text}Expand governed content enough to "
            "help the assembled output meet the floor. The harness will fail the assembly if the "
            "compiled output is under target.\n"
        )
    partition_line = ""
    if section_role == "layer_b_act":
        assigned = assigned_body_refs or []
        assigned_json = json.dumps(assigned, ensure_ascii=False)
        completion_flags_json = json.dumps(body_ref_completion_flags(all_act_body_refs, assigned), ensure_ascii=False)
        partition_line = f"""
ACT partition contract for this section:
- Assigned Stage 04 ACT body_refs: {assigned_json}
- First Stage 04 ACT body_ref for the compiled answer: {json.dumps(first_act_body_ref, ensure_ascii=False)}
- Per-body_ref completion flags for this section: {completion_flags_json}
- Emit ACT rows only for those exact `body_ref=` tokens.
- Do not emit ACT rows for unassigned body_refs, even if they appear in the validated compact stage state.
- Every assigned body_ref must appear exactly once in this section.
- Preserve public burden grouping: body_refs for the same burden must stay contiguous in the final assembled body.
- Emit a burden heading only for a body_ref marked `first_for_burden`; emit a standalone Land/HOLD line only for a body_ref marked `last_for_burden`.
- Do not repeat `## Layer B — Bounded Governed Response` unless this section owns the first Stage 04 ACT body_ref.
- The assembler will fail duplicate, missing, or unassigned ACT body_refs before Stage 07 validators run.
"""
    semantic_contract = ""
    if section_role == "layer_a_diagnostic_ir":
        semantic_contract = stage07_layer_a_contract_guidance(previous_stages)
    elif section_role == "layer_b_act":
        semantic_contract = stage07_act_contract_guidance(previous_stages, assigned_body_refs or [])
    elif section_role == "mrp_reread_terminal":
        semantic_contract = stage07_mrp_reread_contract_guidance(previous_stages)
    elif section_role == "field_witness_nar":
        semantic_contract = stage07_field_witness_contract_guidance(previous_stages)
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
{partition_line}
{semantic_contract}

Return only the public governed-output text for this section. Do not wrap it in
JSON or code fences. Do not mention that this is a section unless the normal
public governed answer itself needs a section heading.
"""


def release_section_expansion_prompt(
    *,
    root: Path,
    case_name: str,
    raw_input_path: Path,
    input_digest: str,
    skill_hash: str,
    section_id: str,
    section_role: str,
    section_min_bytes: int,
    current_bytes: int,
    expansion_round: int,
    max_rounds: int,
    assigned_body_refs: list[str] | None,
    existing_text: str,
) -> str:
    remaining = max(0, section_min_bytes - current_bytes)
    assigned = json.dumps(assigned_body_refs or [], ensure_ascii=False)
    role_notes = {
        "layer_b_act": (
            "Use only the assigned ACT body_refs. Do not add ACT rows for unassigned body_refs. "
            "Expand owner operation bodies, local result prose, and Land(...) consequences. "
            "Do not repeat the main Layer B bounded heading or print Land(...) before all submoves "
            "for that burden have rendered."
        ),
        "field_witness_nar": (
            "Add human-readable Closure/Reconstruction Witness detail without emitting a second "
            "`field_witness` JSON object and without changing existing JSON proof values."
        ),
        "mrp_reread_terminal": (
            "Expand MRP reread, terminal-state, graph-delta, and field-diagnostic detail without "
            "changing the route result."
        ),
        "restorative_response": (
            "Preserve the exact Restorative Response heading and keep the parser-stable lines "
            "`Restored criterion/order:`, `Relieved pressure:`, and "
            "`Held/scoped/reopenable remainder:` visible before any added prose."
        ),
    }
    return f"""Runtime SHA256: {skill_hash}

You are expanding one already-generated stage-07 compiled output section inside
the same bounded pilot run. This is not a second pilot. The harness will append
your text to the same section file, hash it, and validate the assembled output.

Case: {case_name}
Raw input path: {rel(raw_input_path, root)}
Input SHA256: {input_digest}
Section id: {section_id}
Section role: {section_role}
Expansion round: {expansion_round} of {max_rounds}
Current section bytes: {current_bytes}
Required section minimum bytes: {section_min_bytes}
Approximate remaining bytes needed: {remaining}
Assigned ACT body_refs for this section: {assigned}

Expansion contract:
- Return only additional public governed-output text for this same section.
- Do not repeat the whole section.
- Do not contradict or replace existing text.
- Do not include JSON or code fences unless the section role itself requires JSON and the added text is valid for that role.
- Do not claim verifier sidecars, retained promotion, package/provenance, guaranteed uptake, broad model behavior, broad A/B/C/D closure, Graphify proof, or ActiveGraph proof.
- Do not mention this harness, expansion loop, byte budget, manifest, or compiler.
- {role_notes.get(section_role, "Add role-local governed detail that stays inside the current section boundary.")}

Existing section text:
```text
{existing_text}
```

Return only the additional text to append.
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
    act_partition: dict[str, Any] | None = None,
    section_budgets: dict[str, Any] | None = None,
    section_expansions: dict[str, Any] | None = None,
    transport_resume: dict[str, Any] | None = None,
) -> None:
    manifest_dir = manifest_path.parent
    payload: dict[str, Any] = {
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
    }
    if act_partition is not None:
        payload["act_partition"] = act_partition
    if section_budgets is not None:
        payload["section_budgets"] = section_budgets
    if section_expansions is not None:
        payload["section_expansions"] = section_expansions
    if transport_resume is not None:
        payload["transport_resume"] = transport_resume
    write_json(manifest_path, payload)


def split_text_for_compiled_self_test(text: str) -> list[tuple[str, str, str]]:
    plan = [
        ("opening", "visible_opening"),
        ("layer-a-diagnostic-ir", "layer_a_diagnostic_ir"),
        ("act-body", "layer_b_act"),
        ("mrp-reread-terminal", "mrp_reread_terminal"),
        ("restorative-response", "restorative_response"),
        ("closing-formulation", "closing_formulation"),
        ("field-witness-nar", "field_witness_nar"),
    ]
    layer_b = re.search(r"(?im)^\s*##\s+Layer B\b", text)
    mrp = re.search(r"(?im)^\s*\[Mid-Reread Pressure\]\s*$", text)
    restorative = re.search(r"(?im)^\s*(?:#{1,6}\s*)?Restorative Response\s*$", text)
    closing = re.search(r"(?im)^\s*(?:#{1,6}\s*)?Closing Formulation\s*$", text)
    witness = re.search(r"(?im)^\s*Closure/Reconstruction Witness\s*$", text)
    first_line_end = text.find("\n")
    marker_positions = [
        first_line_end + 1 if first_line_end >= 0 else -1,
        layer_b.start() if layer_b else -1,
        mrp.start() if mrp else -1,
        restorative.start() if restorative else -1,
        closing.start() if closing else -1,
        witness.start() if witness else -1,
    ]
    if all(position >= 0 for position in marker_positions) and marker_positions == sorted(marker_positions):
        layer_a_start, layer_b_start, mrp_start, restorative_start, closing_start, witness_start = marker_positions
        return [
            ("opening", "visible_opening", text[:layer_a_start]),
            ("layer-a-diagnostic-ir", "layer_a_diagnostic_ir", text[layer_a_start:layer_b_start]),
            ("act-body", "layer_b_act", text[layer_b_start:mrp_start]),
            ("mrp-reread-terminal", "mrp_reread_terminal", text[mrp_start:restorative_start]),
            ("restorative-response", "restorative_response", text[restorative_start:closing_start]),
            ("closing-formulation", "closing_formulation", text[closing_start:witness_start]),
            ("field-witness-nar", "field_witness_nar", text[witness_start:]),
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


def read_text_if_exists(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def classify_transport_failure(exit_code: int, log_text: str) -> dict[str, Any]:
    websocket_403_matches = re.findall(
        r"(?is)(?:websocket|wss|ws)[^\n]{0,240}403\s+Forbidden|"
        r"403\s+Forbidden[^\n]{0,240}(?:websocket|wss|ws)",
        log_text,
    )
    http_fallback = re.search(r"(?i)(falling back to HTTP|HTTP fallback|fallback[^\n]{0,120}HTTP)", log_text) is not None
    http_429 = re.search(r"(?i)(429\s+Too Many Requests|Too Many Requests|rate limit)", log_text) is not None
    timeout = TRANSPORT_TIMEOUT_RE.search(log_text) is not None
    semantic_failure = SEMANTIC_FAILURE_RE.search(log_text) is not None
    transport_markers = bool(websocket_403_matches or http_fallback or http_429 or timeout)
    return {
        "websocket_403_count": len(websocket_403_matches),
        "http_fallback": http_fallback,
        "http_429": http_429,
        "timeout_or_network": timeout,
        "semantic_failure_marker": semantic_failure,
        "retryable": exit_code != 0 and transport_markers,
    }


def expansion_subprocess_id(section_id: str, expansion_round: int) -> str:
    safe_section_id = section_id.replace("_", "-")
    return f"stage-07-release-output-{safe_section_id}-expansion-{expansion_round}"


def attempt_path(path: Path, attempt: int) -> Path:
    if attempt <= 1:
        return path
    name = path.name
    for suffix in (".prompt.md", ".codex-log.txt"):
        if name.endswith(suffix):
            return path.with_name(f"{name[:-len(suffix)]}-attempt-{attempt}{suffix}")
    return path.with_name(f"{path.stem}-attempt-{attempt}{path.suffix}")


def path_hash_payload(root: Path, path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {"path": rel(path, root), "exists": path.exists()}
    if path.exists() and path.is_file():
        payload["sha256"] = sha256_file(path)
        payload["bytes"] = path.stat().st_size
    return payload


def transport_attempt_record(
    *,
    root: Path,
    subprocess_id: str,
    stage: str,
    role: str,
    section_id: str,
    expansion_round: int,
    attempt: int,
    prompt_path: Path,
    response_path: Path,
    log_path: Path,
    exit_code: int,
    status: str,
    transport: dict[str, Any],
) -> dict[str, Any]:
    return {
        "subprocess_id": subprocess_id,
        "stage": stage,
        "role": role,
        "section_id": section_id,
        "round": expansion_round,
        "attempt": attempt,
        "prompt": path_hash_payload(root, prompt_path),
        "response": path_hash_payload(root, response_path),
        "log": path_hash_payload(root, log_path),
        "exit_code": exit_code,
        "status": status,
        "transport": transport,
    }


def write_transport_attempts_record(path: Path, *, root: Path, attempts: list[dict[str, Any]]) -> None:
    write_json(
        path,
        {
            "schema": TRANSPORT_ATTEMPTS_SCHEMA,
            "attempt_count": len(attempts),
            "attempts": attempts,
        },
    )


def resolve_hash_payload_path(root: Path, payload: dict[str, Any], key: str) -> Path:
    value = payload.get(key)
    if not isinstance(value, dict) or not isinstance(value.get("path"), str):
        raise HarnessError(f"Resume hash record missing {key}.path")
    return resolve_under_root(root, Path(value["path"]), f"Resume {key}")


def validate_hash_payload_file(root: Path, item: dict[str, Any], label: str) -> Path:
    if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
        raise HarnessError(f"{label}: missing path or sha256")
    path = resolve_under_root(root, Path(item["path"]), label)
    if not path.exists() or not path.is_file():
        raise HarnessError(f"{label}: hashed artifact is missing: {rel(path, root)}")
    actual = sha256_file(path)
    expected = item["sha256"].upper()
    if actual != expected:
        raise HarnessError(f"{label}: hash mismatch for {rel(path, root)}; expected {expected} but found {actual}")
    return path


def hash_artifact_map(root: Path, hash_payload: dict[str, Any]) -> tuple[dict[str, str], list[Path]]:
    artifacts = hash_payload.get("stage_artifacts")
    if not isinstance(artifacts, list):
        raise HarnessError("Resume hash record stage_artifacts must be a list")
    artifact_hashes: dict[str, str] = {}
    artifact_paths: list[Path] = []
    for index, item in enumerate(artifacts):
        path = validate_hash_payload_file(root, item, f"stage_artifacts[{index}]")
        artifact_hashes[rel(path, root)] = item["sha256"].upper()
        artifact_paths.append(path)
    for key in ("skill", "replay_record", "raw_input"):
        validate_hash_payload_file(root, hash_payload.get(key, {}), key)
    return artifact_hashes, artifact_paths


def require_hash_matched(path: Path, *, root: Path, artifact_hashes: dict[str, str], label: str) -> None:
    key = rel(path, root)
    expected = artifact_hashes.get(key)
    if expected is None:
        raise HarnessError(f"{label}: missing from prior hash record: {key}")
    if not path.exists() or not path.is_file():
        raise HarnessError(f"{label}: missing prior artifact: {key}")
    actual = sha256_file(path)
    if actual != expected:
        raise HarnessError(f"{label}: hash mismatch for {key}; expected {expected} but found {actual}")


def parse_stage07_expansion_failure(message: str) -> dict[str, Any]:
    match = re.search(
        r"stage-07-release-output\s+([A-Za-z0-9_-]+)\s+expansion\s+([0-9]+):"
        r".*?see\s+([^\r\n]+?\.codex-log\.txt)",
        message,
        re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        raise HarnessError("Resume failure record does not identify a Stage 07 expansion subprocess")
    return {
        "section_id": match.group(1),
        "round": int(match.group(2)),
        "log_path": Path(match.group(3).strip()),
    }


def load_stage07_resume_context(root: Path, run_dir: Path) -> dict[str, Any]:
    hash_path = run_dir / "staged-smoke.hashes.json"
    failure_record_path = run_dir / "records" / "staged-handoff-failure.json"
    if not hash_path.exists():
        raise HarnessError(f"Resume run missing hash record: {rel(hash_path, root)}")
    if not failure_record_path.exists():
        raise HarnessError(f"Resume run missing failure record: {rel(failure_record_path, root)}")
    for forbidden in (
        run_dir / "output.md",
        run_dir / "stage-07-output-assembly.manifest.json",
        run_dir / "output.md.assembly.hashes.json",
    ):
        if forbidden.exists():
            raise HarnessError(f"Resume refuses run with existing final/assembly artifact: {rel(forbidden, root)}")
    for forbidden_dir in (run_dir / "proof-sidecars", run_dir / "retained-promotion"):
        if forbidden_dir.exists() and any(forbidden_dir.iterdir()):
            raise HarnessError(f"Resume refuses run with downstream sidecars/promotion: {rel(forbidden_dir, root)}")

    hash_payload = load_json(hash_path)
    failure_payload = load_json(failure_record_path)
    if not isinstance(hash_payload, dict) or not isinstance(failure_payload, dict):
        raise HarnessError("Resume records must be JSON objects")
    artifact_hashes, artifact_paths = hash_artifact_map(root, hash_payload)
    stages = failure_payload.get("stages")
    if not isinstance(stages, list) or len(stages) != 6:
        raise HarnessError("Resume requires exactly completed Stage 01-06 records")
    expected_stage_ids = STAGE_ORDER[:6]
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict) or stage.get("id") != expected_stage_ids[index] or stage.get("status") != "pass":
            raise HarnessError("Resume requires Stage 01-06 to be present and pass")
    failure = failure_payload.get("failure")
    if not isinstance(failure, str) or not failure.strip():
        raise HarnessError("Resume failure record must include a failure string")
    failed = parse_stage07_expansion_failure(failure)
    log_path = resolve_under_root(root, failed["log_path"], "failed expansion log")
    require_hash_matched(log_path, root=root, artifact_hashes=artifact_hashes, label="failed expansion log")
    transport = classify_transport_failure(1, read_text_if_exists(log_path))
    if transport.get("retryable") is not True:
        raise HarnessError("Resume failure is not classified as retryable transport")

    log_name_match = re.search(
        r"stage-07-release-output-([0-9]+)-(.+)-expansion-([0-9]+)\.codex-log\.txt$",
        log_path.name,
    )
    if log_name_match is None:
        raise HarnessError("Resume failed expansion log name is not parseable")
    section_index = int(log_name_match.group(1))
    safe_section_id = log_name_match.group(2)
    expansion_round = int(log_name_match.group(3))
    prompt_path = run_dir / "prompts" / f"stage-07-release-output-{section_index:02d}-{safe_section_id}-expansion-{expansion_round}.prompt.md"
    response_path = run_dir / "release-section-expansions" / f"{section_index:02d}-{safe_section_id}-expansion-{expansion_round}.md"
    require_hash_matched(prompt_path, root=root, artifact_hashes=artifact_hashes, label="failed expansion prompt")
    prior_attempt = transport_attempt_record(
        root=root,
        subprocess_id=expansion_subprocess_id(failed["section_id"], failed["round"]),
        stage="stage-07-release-output",
        role=failed["section_id"].replace("-", "_"),
        section_id=failed["section_id"],
        expansion_round=failed["round"],
        attempt=1,
        prompt_path=prompt_path,
        response_path=response_path,
        log_path=log_path,
        exit_code=1,
        status="failed_transport",
        transport=transport,
    )
    return {
        "schema": TRANSPORT_RESUME_SCHEMA,
        "run_dir": rel(run_dir, root),
        "hash_record": rel(hash_path, root),
        "failure_record": rel(failure_record_path, root),
        "raw_input_path": resolve_hash_payload_path(root, hash_payload, "raw_input"),
        "replay_record_path": resolve_hash_payload_path(root, hash_payload, "replay_record"),
        "stages": [dict(stage) for stage in stages],
        "artifact_hashes": artifact_hashes,
        "artifact_paths": artifact_paths,
        "failed_expansion": {
            "section_id": failed["section_id"],
            "section_index": section_index,
            "safe_section_id": safe_section_id,
            "round": failed["round"],
            "log_path": rel(log_path, root),
        },
        "prior_attempts": [prior_attempt],
    }


def existing_expansion_records_for_resume(
    *,
    root: Path,
    run_dir: Path,
    section_plan: list[tuple[str, str]],
    max_rounds: int,
    artifact_hashes: dict[str, str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    expansions_dir = run_dir / "release-section-expansions"
    for index, (section_id, section_role) in enumerate(section_plan, start=1):
        safe_section_id = section_id.replace("_", "-")
        for expansion_round in range(1, max_rounds + 1):
            expansion_path = expansions_dir / f"{index:02d}-{safe_section_id}-expansion-{expansion_round}.md"
            if not expansion_path.exists():
                continue
            require_hash_matched(
                expansion_path,
                root=root,
                artifact_hashes=artifact_hashes,
                label="prior successful expansion",
            )
            records.append(
                {
                    "section_id": section_id,
                    "role": section_role,
                    "round": expansion_round,
                    "path": str(expansion_path),
                    "sha256": sha256_file(expansion_path),
                }
            )
    return records


def invoke_expansion_with_transport_policy(
    *,
    root: Path,
    model: str,
    prompt: str,
    base_prompt_path: Path,
    base_output_path: Path,
    base_log_path: Path,
    section_id: str,
    section_role: str,
    expansion_round: int,
    first_attempt: int,
    retry_rounds: int,
    attempts: list[dict[str, Any]],
    attempts_record_path: Path,
    stage_files: list[Path],
) -> Path:
    if retry_rounds < 0:
        raise HarnessError("--transport-retry-rounds must be a non-negative integer")
    subprocess_id = expansion_subprocess_id(section_id, expansion_round)
    last_attempt = first_attempt + retry_rounds
    for attempt in range(first_attempt, last_attempt + 1):
        prompt_path = attempt_path(base_prompt_path, attempt)
        output_path = attempt_path(base_output_path, attempt)
        log_path = attempt_path(base_log_path, attempt)
        write_text(prompt_path, prompt)
        exit_code = invoke_codex(root, model, prompt, output_path, log_path)
        stage_files.extend([prompt_path, output_path, log_path])
        log_text = read_text_if_exists(log_path)
        transport = classify_transport_failure(exit_code, log_text)
        if exit_code == 0:
            if not output_path.exists() or output_path.stat().st_size == 0:
                attempts.append(
                    transport_attempt_record(
                        root=root,
                        subprocess_id=subprocess_id,
                        stage="stage-07-release-output",
                        role=section_role,
                        section_id=section_id,
                        expansion_round=expansion_round,
                        attempt=attempt,
                        prompt_path=prompt_path,
                        response_path=output_path,
                        log_path=log_path,
                        exit_code=exit_code,
                        status="failed_semantic",
                        transport=transport,
                    )
                )
                write_transport_attempts_record(attempts_record_path, root=root, attempts=attempts)
                raise HarnessError(
                    f"stage-07-release-output {section_id} expansion {expansion_round}: "
                    "expansion output was not produced"
                )
            attempts.append(
                transport_attempt_record(
                    root=root,
                    subprocess_id=subprocess_id,
                    stage="stage-07-release-output",
                    role=section_role,
                    section_id=section_id,
                    expansion_round=expansion_round,
                    attempt=attempt,
                    prompt_path=prompt_path,
                    response_path=output_path,
                    log_path=log_path,
                    exit_code=exit_code,
                    status="pass",
                    transport=transport,
                )
            )
            write_transport_attempts_record(attempts_record_path, root=root, attempts=attempts)
            return output_path
        status = "failed_transport" if transport.get("retryable") is True else "failed_non_transport"
        attempts.append(
            transport_attempt_record(
                root=root,
                subprocess_id=subprocess_id,
                stage="stage-07-release-output",
                role=section_role,
                section_id=section_id,
                expansion_round=expansion_round,
                attempt=attempt,
                prompt_path=prompt_path,
                response_path=output_path,
                log_path=log_path,
                exit_code=exit_code,
                status=status,
                transport=transport,
            )
        )
        write_transport_attempts_record(attempts_record_path, root=root, attempts=attempts)
        if transport.get("retryable") is not True:
            raise HarnessError(
                f"stage-07-release-output {section_id} expansion {expansion_round}: "
                f"codex exec failed with exit code {exit_code}; see {rel(log_path, root)}"
            )
        if attempt == last_attempt:
            raise HarnessError(
                f"stage-07-release-output {section_id} expansion {expansion_round}: "
                f"transport retry budget exhausted after {attempt - first_attempt + 1} attempt(s); "
                f"see {rel(log_path, root)}"
            )
    raise HarnessError("transport retry loop exited unexpectedly")


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
    global invoke_codex
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
    transport_log = (
        "websocket attempt failed: 403 Forbidden\n"
        "falling back to HTTP transport\n"
        "HTTP status: 429 Too Many Requests\n"
    )
    transport_classification = classify_transport_failure(1, transport_log)
    if transport_classification.get("retryable") is not True:
        raise HarnessError("Self-test failed to classify websocket 403/HTTP 429 as retryable transport")
    if transport_classification.get("websocket_403_count") != 1 or transport_classification.get("http_429") is not True:
        raise HarnessError("Self-test transport classification missed 403 or 429 markers")
    semantic_classification = classify_transport_failure(
        1,
        "AssemblyError: validation failed; missing required surface in public output",
    )
    if semantic_classification.get("retryable") is True:
        raise HarnessError("Self-test classified semantic validator failure as retryable transport")
    if attempt_path(Path("response.md"), 2).name != "response-attempt-2.md":
        raise HarnessError("Self-test attempt path did not suffix markdown response")
    if attempt_path(Path("call.codex-log.txt"), 2).name != "call-attempt-2.codex-log.txt":
        raise HarnessError("Self-test attempt path did not suffix codex log")

    def artifact(path: Path) -> dict[str, str]:
        return {"path": rel(path, root), "sha256": sha256_file(path)}

    def write_resume_fixture(name: str) -> Path:
        fixture_dir = run_dir / name
        fixture_prompts = fixture_dir / "prompts"
        fixture_responses = fixture_dir / "responses"
        fixture_sections = fixture_dir / "release-sections"
        fixture_records = fixture_dir / "records"
        for directory in (fixture_prompts, fixture_responses, fixture_sections, fixture_records):
            directory.mkdir(parents=True, exist_ok=True)
        fixture_raw_input = fixture_dir / "raw-input.md"
        failed_prompt = fixture_prompts / "stage-07-release-output-08-restorative-response-expansion-1.prompt.md"
        failed_log = fixture_responses / "stage-07-release-output-08-restorative-response-expansion-1.codex-log.txt"
        section_output = fixture_sections / "08-restorative-response.md"
        write_text(fixture_raw_input, "Secularism test fixture input.\n")
        write_text(failed_prompt, "Expand restorative response.\n")
        write_text(failed_log, transport_log)
        write_text(section_output, "## Restorative Response\n\nBase section text.\n")
        failure_record = fixture_records / "staged-handoff-failure.json"
        write_json(
            failure_record,
            {
                "schema": "staged-runtime-handshake-v1",
                "case_id": "self-test-transport-resume",
                "mode": "staged-current-skill-smoke",
                "stage_order": STAGE_ORDER,
                "stages": [dict(stage) for stage in replay["stages"][:6]],
                "handoffs": handoffs_for_stage_order(STAGE_ORDER),
                "non_claims": MODEL_NON_CLAIMS,
                "failure": (
                    "stage-07-release-output restorative-response expansion 1: "
                    f"codex exec failed with exit code 1; see {rel(failed_log, root)}"
                ),
            },
        )
        write_json(
            fixture_dir / "staged-smoke.hashes.json",
            {
                "schema": "staged-current-skill-smoke-hashes-v1",
                "case_name": "self-test-transport-resume",
                "mode": "staged-current-skill-smoke",
                "model": "fake-model",
                "verdict": "STAGED_MODEL_HARNESS_NEGATIVE_EVIDENCE: transport fixture",
                "run_dir": rel(fixture_dir, root),
                "skill": artifact(files["skill"]),
                "replay_record": artifact(replay_record),
                "raw_input": artifact(fixture_raw_input),
                "stage_artifacts": [
                    artifact(failed_prompt),
                    artifact(section_output),
                    artifact(failed_log),
                    artifact(failure_record),
                ],
                "handoff_record": artifact(failure_record),
                "output": None,
                "sidecars": [],
                "non_claims": {
                    "not_package_provenance": True,
                    "not_retained_promotion": True,
                    "not_broad_model_matrix": True,
                    "not_graphify_or_activegraph_proof": True,
                },
            },
        )
        return fixture_dir

    resume_fixture = write_resume_fixture("transport-resume-valid")
    resume_context = load_stage07_resume_context(root, resume_fixture)
    if resume_context["failed_expansion"].get("section_id") != "restorative-response":
        raise HarnessError("Self-test resume preflight did not identify the failed expansion section")
    if resume_context["prior_attempts"][0].get("status") != "failed_transport":
        raise HarnessError("Self-test resume preflight did not record the failed transport attempt")

    hash_mismatch_fixture = write_resume_fixture("transport-resume-hash-mismatch")
    write_text(hash_mismatch_fixture / "release-sections" / "08-restorative-response.md", "mutated\n")
    try:
        load_stage07_resume_context(root, hash_mismatch_fixture)
    except HarnessError as exc:
        if "hash mismatch" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test resume preflight accepted a hash-mismatched artifact")

    final_output_fixture = write_resume_fixture("transport-resume-final-output")
    write_text(final_output_fixture / "output.md", "already final\n")
    try:
        load_stage07_resume_context(root, final_output_fixture)
    except HarnessError as exc:
        if "existing final/assembly artifact" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test resume preflight accepted an existing final output")

    sidecar_fixture = write_resume_fixture("transport-resume-sidecar")
    sidecar_path = sidecar_fixture / "proof-sidecars" / "sidecar.json"
    write_json(sidecar_path, {"unexpected": True})
    try:
        load_stage07_resume_context(root, sidecar_fixture)
    except HarnessError as exc:
        if "downstream sidecars/promotion" not in str(exc):
            raise
    else:
        raise HarnessError("Self-test resume preflight accepted existing sidecars")

    manifest_fixture = write_resume_fixture("transport-resume-manifest")
    manifest_context = load_stage07_resume_context(root, manifest_fixture)
    manifest_attempt_output = (
        manifest_fixture / "release-section-expansions" / "08-restorative-response-expansion-1-attempt-2.md"
    )
    write_text(manifest_attempt_output, "Successful resumed expansion.\n")
    manifest_attempt_log = (
        manifest_fixture / "responses" / "stage-07-release-output-08-restorative-response-expansion-1-attempt-2.codex-log.txt"
    )
    write_text(manifest_attempt_log, "ok\n")
    manifest_attempt_prompt = (
        manifest_fixture / "prompts" / "stage-07-release-output-08-restorative-response-expansion-1-attempt-2.prompt.md"
    )
    write_text(manifest_attempt_prompt, "Expand restorative response.\n")
    manifest_attempts = list(manifest_context["prior_attempts"])
    manifest_attempts.append(
        transport_attempt_record(
            root=root,
            subprocess_id=expansion_subprocess_id("restorative-response", 1),
            stage="stage-07-release-output",
            role="restorative_response",
            section_id="restorative-response",
            expansion_round=1,
            attempt=2,
            prompt_path=manifest_attempt_prompt,
            response_path=manifest_attempt_output,
            log_path=manifest_attempt_log,
            exit_code=0,
            status="pass",
            transport=classify_transport_failure(0, "ok\n"),
        )
    )
    manifest_attempts_record = manifest_fixture / "records" / "stage-07-transport-attempts.json"
    write_transport_attempts_record(manifest_attempts_record, root=root, attempts=manifest_attempts)
    manifest_path = manifest_fixture / "stage-07-output-assembly.manifest.json"
    write_compiled_release_manifest(
        root=root,
        manifest_path=manifest_path,
        case_name="self-test-transport-resume",
        raw_input_path=manifest_context["raw_input_path"],
        section_entries=[
            {
                "id": "restorative-response",
                "role": "restorative_response",
                "path": str(manifest_fixture / "release-sections" / "08-restorative-response.md"),
                "sha256": sha256_file(manifest_fixture / "release-sections" / "08-restorative-response.md"),
            }
        ],
        output_path=manifest_fixture / "output.md",
        transport_resume={
            "schema": TRANSPORT_RESUME_SCHEMA,
            "resumed": True,
            "source_run_dir": manifest_context["run_dir"],
            "failed_expansion": manifest_context["failed_expansion"],
            "attempts_record": rel(manifest_attempts_record, manifest_path.parent),
            "attempts": manifest_attempts,
        },
    )
    manifest_payload = load_json(manifest_path)
    if len(manifest_payload.get("transport_resume", {}).get("attempts", [])) != 2:
        raise HarnessError("Self-test resume manifest did not record failed and successful attempts")

    retry_fixture = run_dir / "transport-retry-budget"
    retry_fixture.mkdir(parents=True, exist_ok=True)
    retry_attempts: list[dict[str, Any]] = []
    retry_stage_files: list[Path] = []
    real_invoke_codex = invoke_codex

    def fake_transport_failure(
        _root: Path,
        _model: str,
        _prompt: str,
        _output_path: Path,
        log_path: Path,
    ) -> int:
        write_text(log_path, transport_log)
        return 1

    try:
        invoke_codex = fake_transport_failure
        try:
            invoke_expansion_with_transport_policy(
                root=root,
                model="fake-model",
                prompt="expand\n",
                base_prompt_path=retry_fixture / "call.prompt.md",
                base_output_path=retry_fixture / "call.md",
                base_log_path=retry_fixture / "call.codex-log.txt",
                section_id="restorative-response",
                section_role="restorative_response",
                expansion_round=1,
                first_attempt=1,
                retry_rounds=1,
                attempts=retry_attempts,
                attempts_record_path=retry_fixture / "stage-07-transport-attempts.json",
                stage_files=retry_stage_files,
            )
        except HarnessError as exc:
            if "transport retry budget exhausted after 2 attempt(s)" not in str(exc):
                raise
        else:
            raise HarnessError("Self-test retry budget did not stop after the bounded attempts")
    finally:
        invoke_codex = real_invoke_codex
    if len(retry_attempts) != 2:
        raise HarnessError("Self-test retry budget did not record exactly two attempts")
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
    trinitarian_delta_guidance = stage04_delta_vocabulary_guidance(
        [
            {
                "id": "stage-03-routing-owner-gate",
                "owner_routes": [
                    {"burden_id": "B1", "owner_id": "do-christian-extensions"},
                    {"burden_id": "B1", "owner_id": "M9"},
                    {"burden_id": "B2", "owner_id": "M7"},
                    {"burden_id": "B2", "owner_id": "M9"},
                    {"burden_id": "B3", "owner_id": "source-status-repair"},
                    {"burden_id": "B3", "owner_id": "authority-order-repair"},
                    {"burden_id": "B4", "owner_id": "M8"},
                    {"burden_id": "B4", "owner_id": "M9"},
                ],
            }
        ]
    )
    for required in (
        "DO_CHRISTIAN: fan-out-route-named, trinitarian-model-identified",
        "M7: definition-anchored",
        "M8: coercive-clarity-entailment-demoted",
        "M9: category-separated",
        "SOURCE: authority-order-repaired",
        "Do not invent near-synonyms such as `predicate-transfer-blocked`",
    ):
        if required not in trinitarian_delta_guidance:
            raise HarnessError(f"Self-test Stage 04 delta vocabulary guidance omitted {required}")
    trinitarian_drift_rows = [
        "⟦ACT ¹B₁[do-christian-extensions.model-identification] :: π=trinitarian-person-nature-model-transfer :: body_ref=¹B₁ :: Δ=Δ¹B:trinitarian-model-transfer-bounded :: Land(¹B)+⟧",
        "⟦ACT ¹B₂[M9.predication-repair] :: π=father-only-true-god-predicate-transfer :: body_ref=¹B₂ :: Δ=Δ¹B:predicate-transfer-blocked :: Land(¹B)+⟧",
        "⟦ACT ²B₁[M7.definition-anchor] :: π=only-placement-analogy :: body_ref=²B₁ :: Δ=Δ²B:only-scope-defined :: Land(²B)+⟧",
        "⟦ACT ²B₂[M9.predication-repair] :: π=2-plus-2-predicate-category :: body_ref=²B₂ :: Δ=Δ²B:predicate-category-separated :: Land(²B)+⟧",
        "⟦ACT ³B₁[source-status-repair.source-order] :: π=john-1-1-and-1-john-5-20-proof-stack :: body_ref=³B₁ :: Δ=Δ³B:proof-stack-routed :: Land(³B)+⟧",
        "⟦ACT ³B₂[authority-order-repair.sort] :: π=proof-text-hidden-support :: body_ref=³B₂ :: Δ=Δ³B:hidden-support-demoted :: Land(³B)+⟧",
        "⟦ACT ⁴B₁[M8.consequence-trace] :: π=eternal-life-knowing-jesus-entailment :: body_ref=⁴B₁ :: Δ=Δ⁴B:entailment-bounded :: Land(⁴B)+⟧",
        "⟦ACT ⁴B₂[M9.predication-repair] :: π=sender-sent-relation-category :: body_ref=⁴B₂ :: Δ=Δ⁴B:sender-sent-predication-separated :: Land(⁴B)+⟧",
    ]
    normalized_trinitarian_stage04 = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1", "B2", "B3", "B4"],
            "act_burdens": ["B1", "B2", "B3", "B4"],
            "act_rows": trinitarian_drift_rows,
        },
    )
    trinitarian_delta_results = [
        stage04_act_details_by_ref(normalized_trinitarian_stage04)[ref]["delta_result"]
        for ref in ["¹B₁", "¹B₂", "²B₁", "²B₂", "³B₁", "³B₂", "⁴B₁", "⁴B₂"]
    ]
    if trinitarian_delta_results != [
        "trinitarian-model-identified",
        "predicate-separated",
        "definition-anchored",
        "category-separated",
        "proof-text-sorted",
        "proof-text-hidden-support-blocked",
        "entailment-blocked",
        "category-separated",
    ]:
        raise HarnessError("Self-test failed to canonicalize Trinitarian Stage 04 delta_result drift")
    rewrites = normalized_trinitarian_stage04.get("normalization", {}).get("delta_result_canonicalizations")
    if not isinstance(rewrites, list) or len(rewrites) != 8:
        raise HarnessError("Self-test failed to record Trinitarian Stage 04 delta_result canonicalizations")
    partition_stage04 = dict(normalized_stage04)
    partition_stage04["act_body_refs"] = ["¹B₁", "¹B₂", "²B₁", "²B₂", "³B₁", "³B₂", "⁴B₁", "⁴B₂", "⁵B₁", "⁵B₂"]
    partition_plan = compiled_release_section_plan(70)
    plan_roles = [role for _section_id, role in partition_plan]
    if plan_roles.index("field_witness_nar") <= plan_roles.index("closing_formulation"):
        raise HarnessError("Self-test compiled section plan must place field_witness after Closing Formulation")
    partition = compiled_act_partition([partition_stage04], partition_plan)
    budgets = compiled_section_budgets(partition_plan, 70)
    if not isinstance(budgets, dict) or budgets.get("schema") != staged_output.SECTION_BUDGET_SCHEMA:
        raise HarnessError("Self-test failed to derive compiled section budgets")
    if budgets.get("target_output_bytes") != 70 * 1024:
        raise HarnessError("Self-test compiled section budgets used the wrong target byte floor")
    min_section_bytes = budgets.get("min_section_bytes")
    if not isinstance(min_section_bytes, dict):
        raise HarnessError("Self-test compiled section budgets did not produce per-section floors")
    planned_section_ids = {section_id for section_id, _role in partition_plan}
    if set(min_section_bytes) != planned_section_ids:
        raise HarnessError("Self-test compiled section budgets did not cover every section exactly once")
    if any(not isinstance(value, int) or value <= 0 for value in min_section_bytes.values()):
        raise HarnessError("Self-test compiled section budgets produced a non-positive section floor")
    if sum(min_section_bytes.values()) != 70 * 1024:
        raise HarnessError("Self-test compiled section budgets did not distribute the full target floor")
    graph_line, graph_roots, graph_parallel = stage07_dependency_graph_scaffold(["B1", "B2", "B3"], [])
    if graph_line != "B1 (root) || B2 (root) || B3 (root)":
        raise HarnessError("Self-test Stage 07 graph scaffold omitted edge-empty parallel roots")
    if graph_roots != ["B1", "B2", "B3"] or graph_parallel != [["B1", "B2", "B3"]]:
        raise HarnessError("Self-test Stage 07 graph scaffold did not mirror edge-empty roots/parallel group")
    edgeful_graph_line, edgeful_roots, edgeful_parallel = stage07_dependency_graph_scaffold(
        ["B1", "B2", "B3", "B4", "B5"],
        [{"from": "B4", "to": "B5", "type": "generated_burden_instantiation"}],
    )
    for required_graph_token in ("B1 (root)", "B2 (root)", "B3 (root)", "B4 (root)", "B4 -> B5"):
        if required_graph_token not in edgeful_graph_line:
            raise HarnessError(f"Self-test Stage 07 edgeful graph scaffold omitted {required_graph_token}")
    if edgeful_roots != ["B1", "B2", "B3", "B4"] or edgeful_parallel:
        raise HarnessError("Self-test Stage 07 edgeful graph scaffold did not derive roots from incoming edges")
    assigned_once = [
        ref
        for assignment in partition["assignments"]
        for ref in assignment["body_refs"]
    ]
    if sorted(assigned_once) != sorted(partition_stage04["act_body_refs"]):
        raise HarnessError("Self-test failed to assign every Stage 04 ACT body_ref exactly once")
    if len(assigned_once) != len(set(assigned_once)):
        raise HarnessError("Self-test produced duplicate compiled ACT partition assignments")
    if any(not assignment["body_refs"] for assignment in partition["assignments"]):
        raise HarnessError("Self-test compiled ACT partition left an ACT section empty for this fixture")
    expected_partition = [
        ["¹B₁", "¹B₂", "²B₁", "²B₂"],
        ["³B₁", "³B₂"],
        ["⁴B₁", "⁴B₂", "⁵B₁", "⁵B₂"],
    ]
    actual_partition = [assignment["body_refs"] for assignment in partition["assignments"]]
    if actual_partition != expected_partition:
        raise HarnessError(f"Self-test compiled ACT partition did not preserve whole burden groups: {actual_partition}")
    small_partition = partition_body_refs(["¹B₁", "¹B₂", "²B₁", "²B₂"], [assignment["section_id"] for assignment in partition["assignments"]])
    if [ref for assignment in small_partition for ref in assignment["body_refs"]] != ["¹B₁", "¹B₂", "²B₁", "²B₂"]:
        raise HarnessError("Self-test small ACT partition did not preserve input body_ref order")
    normalized_stage04_rich_burdens = normalized_stage(
        "stage-04-burden-execution-act",
        {
            "id": "stage-04-burden-execution-act",
            "status": "pass",
            "act_targets": ["B1"],
            "act_burdens": ["¹B / B1 source-order diagnostic burden"],
            "act_rows": [canonical_act_row],
        },
    )
    if normalized_stage04_rich_burdens.get("act_burdens") != ["B1"]:
        raise HarnessError("Self-test failed to normalize rich Stage 04 act_burdens into burden ids")
    if not isinstance(normalized_stage04_rich_burdens.get("act_burdens_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 04 act_burdens details")
    try:
        normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": ["B1"],
                "act_burdens": ["source-order diagnostic burden without canonical id"],
                "act_rows": [canonical_act_row],
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject Stage 04 act_burdens without canonical id")
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

    generated_carried_recurse_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "partial",
            "terminal_states": {"B1": "landed", "B2": "carried-RECURSE"},
            "dependency_graph_edges": [{"from": "B1", "to": "B2"}],
            "generated_burdens": [
                {
                    "burden_id": "B2",
                    "generated_by": "MRP(B1)",
                    "terminal_state": "carried-RECURSE",
                }
            ],
            "unresolved_burdens": ["B2"],
            "no_new_resultant_proof": {
                "proved": False,
                "basis": "B2 was generated by MRP(B1) and remains unexecuted.",
                "unresolved_burdens": ["B2"],
            },
        },
    )
    generated_carried_recurse_record = base_record(
        "self-test-stage05-generated-carried-recurse",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
        model_scope_payload=model_scope(
            "self-test-stage05-generated-carried-recurse",
            replay_record,
            stop_after_stage="stage-05-mrp-reread-terminal-state",
        ),
    )
    generated_carried_recurse_record["stages"] = [*replay["stages"][:4], generated_carried_recurse_stage05]
    generated_carried_recurse_path = run_dir / "stage05-generated-carried-recurse.valid.json"
    write_json(generated_carried_recurse_path, generated_carried_recurse_record)
    validate_replay_record(root, generated_carried_recurse_path)

    rich_stage04_handoff_record = base_record(
        "self-test-stage04-rich-burdens-to-stage05",
        "staged-current-skill-stage-local-smoke",
        not_model_smoke=False,
        stop_after_stage="stage-05-mrp-reread-terminal-state",
        model_scope_payload=model_scope(
            "self-test-stage04-rich-burdens-to-stage05",
            replay_record,
            stop_after_stage="stage-05-mrp-reread-terminal-state",
        ),
    )
    rich_stage03_detail_map = dict(replay["stages"][2])
    rich_stage03_detail_map["route_target_details"] = {
        "B1": {
            "route_pressure": "source-order diagnostic burden",
            "backing": "self-test detail map keyed by canonical burden id",
        }
    }
    rich_stage04_handoff_record["stages"] = [
        *replay["stages"][:2],
        rich_stage03_detail_map,
        normalized_stage04_rich_burdens,
        normalized_stage05,
    ]
    rich_stage04_handoff_path = run_dir / "stage04-rich-burdens-stage05-handoff.valid.json"
    write_json(rich_stage04_handoff_path, rich_stage04_handoff_record)
    validate_replay_record(root, rich_stage04_handoff_path)

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
    normalized_stage06_list_delta = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁"],
            "nar_burdens": ["B1"],
            "owner_activations": ["¹B₁"],
            "normalized_activation_record": structured_nar,
            "register_deltas": [
                {"register": "Omega", "delta": ["B1:model-family-bounded", "B1:predicate-separated"]},
                {"register": "xi", "delta": "B1:source-order-landed"},
            ],
        },
    )
    if normalized_stage06_list_delta["register_deltas"][0]["delta"] != [
        "B1:model-family-bounded",
        "B1:predicate-separated",
    ]:
        raise HarnessError("Self-test failed to preserve Stage 06 list-object register_deltas string lists")
    for invalid_delta, message in [
        ([], "empty string-list"),
        (["B1:source-order-landed", 1], "non-string list member"),
    ]:
        try:
            normalized_stage(
                "stage-06-field-witness-nar",
                {
                    "id": "stage-06-field-witness-nar",
                    "status": "pass",
                    "field_witness_body_refs": ["¹B₁"],
                    "nar_burdens": ["B1"],
                    "owner_activations": ["¹B₁"],
                    "normalized_activation_record": structured_nar,
                    "register_deltas": [{"register": "xi", "delta": invalid_delta}],
                },
            )
        except HarnessError:
            pass
        else:
            raise HarnessError(f"Self-test failed to reject Stage 06 list-object register_deltas {message}")
    normalized_stage06_delta_drift = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₂", "³B₂"],
            "nar_burdens": ["B1", "B3"],
            "owner_activations": [
                {
                    "body_ref": "¹B₂",
                    "burden_id": "B1",
                    "owner": "M9",
                    "owner_id": "M9",
                    "operation": "predication-repair",
                    "pressure": "father-only-true-god-predicate-transfer",
                    "delta": "Δ¹B:predicate-transfer-blocked",
                    "delta_result": "predicate-transfer-blocked",
                    "land": "Land(¹B)+",
                    "terminal_state": "landed",
                },
                {
                    "body_ref": "³B₂",
                    "burden_id": "B3",
                    "owner": "authority-order-repair",
                    "owner_id": "authority-order-repair",
                    "operation": "sort",
                    "pressure": "proof-text-hidden-support",
                    "delta": "Δ³B:hidden-support-demoted",
                    "delta_result": "hidden-support-demoted",
                    "land": "Land(³B)+",
                    "terminal_state": "landed",
                },
            ],
            "normalized_activation_record": {
                "n_frame": "trinitarian-john-17-3-source-order-repair",
                "live_registers": ["Omega", "xi"],
                "burden_floor": ["B1", "B3"],
                "per_burden": [
                    {
                        "burden_id": "B1",
                        "owner_id": "M9",
                        "operation": "predication-repair",
                        "pressure": "father-only-true-god-predicate-transfer",
                        "delta_result": "predicate-transfer-blocked",
                        "terminal_state": "landed",
                        "generation_depth": 0,
                    },
                    {
                        "burden_id": "B3",
                        "owner_id": "authority-order-repair",
                        "operation": "sort",
                        "pressure": "proof-text-hidden-support",
                        "delta_result": "hidden-support-demoted",
                        "terminal_state": "landed",
                        "generation_depth": 0,
                    },
                ],
            },
            "register_deltas": {"Omega": "predicate-transfer-blocked", "xi": "hidden-support-demoted"},
        },
    )
    delta_details = normalized_stage06_delta_drift.get("owner_activation_details") or []
    if [item.get("delta_result") for item in delta_details] != [
        "predicate-separated",
        "proof-text-hidden-support-blocked",
    ]:
        raise HarnessError("Self-test failed to canonicalize Stage 06 owner_activation delta_result drift")
    nar_delta_results = [
        row.get("delta_result")
        for row in normalized_stage06_delta_drift["normalized_activation_record"]["per_burden"]
    ]
    if nar_delta_results != ["predicate-separated", "proof-text-hidden-support-blocked"]:
        raise HarnessError("Self-test failed to canonicalize Stage 06 NAR delta_result drift")
    stage07_layer_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="layer-a-diagnostic-ir",
        section_role="layer_a_diagnostic_ir",
        section_number=2,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Initial burden set: [¹B]",
        "𝔅_LA (B_LA) = {¹B}",
        "𝔅_MRP (B_MRP) = {}",
        "𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {¹B}",
        "¹B [xi, kappa] status=initial-live",
        "Do not replace `Initial burden set: [...]` with `Initial burden set ledger:`",
    ):
        if required not in stage07_layer_prompt:
            raise HarnessError(f"Self-test Stage 07 Layer A prompt omitted parser-stable scaffold: {required}")
    stage07_mrp_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="mrp-reread-terminal",
        section_role="mrp_reread_terminal",
        section_number=6,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Stage 07 public MRP block contract:",
        "[Mid-Reread Pressure]",
        "Target: MRP(¹B) / Stage 05 terminal MRP source",
        "R(H,Δ): held routes rechecked: none; live remainder: no remaining burden; release/next: STOP after ¹B.",
        "Landed delta: Delta B1: terminal state landed; MRP route result type no_new_resultant.",
        "Route-gradient: plain-gradient points to STOP after ¹B; no live pressure remains.",
        "Finding: stable",
        "MRP route result type: no_new_resultant",
        "MRP resultant: stable -> graph none; route STOP",
        "Graph delta: none",
        "Pre-emption basis: terminal states landed; B_MRP empty; no generated burden remains",
        "Route: STOP",
        "`Landed delta:` must use the exact same canonical delta string as `field_witness.formal_reread_states[].delta`.",
        "`MRP route result type:` must be one canonical token with no trailing punctuation",
        "field_witness and Closure/Reconstruction Witness mirrors do not replace them",
    ):
        if required not in stage07_mrp_prompt:
            raise HarnessError(f"Self-test Stage 07 MRP prompt omitted public-block scaffold: {required}")
    if "MRP route result type: no_new_resultant." in stage07_mrp_prompt:
        raise HarnessError("Self-test Stage 07 MRP prompt allowed trailing punctuation on no_new_resultant")
    stage07_act_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="act-body-1",
        section_role="layer_b_act",
        section_number=3,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=["¹B₁"],
    )
    if canonical_act_row not in stage07_act_prompt:
        raise HarnessError("Self-test Stage 07 ACT prompt omitted exact canonical Stage 04 ACT row")
    for required in (
        "Do not write malformed rows such as `⟦ACT [owner.operation] ...⟧`",
        "¹B₁[source-status-repair] - source-order over scientific-explanations-only-knowledge-source",
        "Contribution-to-Land(¹B)",
        "Land(¹B): summarize the cumulative state delta from the visible submove block(s)",
    ):
        if required not in stage07_act_prompt:
            raise HarnessError(f"Self-test Stage 07 ACT prompt omitted semantic scaffold: {required}")
    stage07_restorative_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="restorative-response",
        section_role="restorative_response",
        section_number=7,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Begin with the exact public role heading `Restorative Response`",
        "Carry explicit fitrah/tawhid and sound reason/ʿaql orientation in the endpoint",
        "`Restored criterion/order: ...`",
        "`Relieved pressure: ...`",
        "`Held/scoped/reopenable remainder: ...`",
        "Do not include Closing Formulation here",
    ):
        if required not in stage07_restorative_prompt:
            raise HarnessError(f"Self-test Stage 07 Restorative prompt omitted role-heading scaffold: {required}")
    drifted_restorative_text = (
        "Restorative Response\n\n"
        "The answer restores tawhid and sound reason, but this model-authored prose does not "
        "emit the required held remainder slot.\n"
    )
    canonical_restorative_text, canonical_restorative_event = canonical_compiled_structural_section(
        "restorative_response",
        drifted_restorative_text,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    if not canonical_restorative_event:
        raise HarnessError("Self-test Stage 07 Restorative canonicalization did not record an event")
    for required in (
        "Restored criterion/order:",
        "Relieved pressure:",
        "Held/scoped/reopenable remainder:",
    ):
        if required not in canonical_restorative_text:
            raise HarnessError(f"Self-test Stage 07 Restorative canonicalization omitted slot: {required}")
    if canonical_restorative_text.count("Restorative Response") != 1:
        raise HarnessError("Self-test Stage 07 Restorative canonicalization duplicated the heading")
    already_slot_shaped_restorative = (
        "Restorative Response\n\n"
        "Restored criterion/order: keep the source-owned order.\n"
        "Relieved pressure: block the proof-stack pressure.\n"
        "Held/scoped/reopenable remainder: future concrete burdens remain reopenable.\n"
    )
    unchanged_restorative, unchanged_event = canonical_compiled_structural_section(
        "restorative_response",
        already_slot_shaped_restorative,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
    )
    if unchanged_event or unchanged_restorative != already_slot_shaped_restorative:
        raise HarnessError("Self-test Stage 07 Restorative canonicalization mutated an already slot-shaped section")
    stage07_closing_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="closing-formulation",
        section_role="closing_formulation",
        section_number=8,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Begin with the exact public role heading `Closing Formulation`",
        "Carry explicit fitrah/tawhid and sound reason/ʿaql orientation in the endpoint",
        "`### Established failure`",
        "`### Restored criterion/orientation`",
        "`### Scoped boundary`",
    ):
        if required not in stage07_closing_prompt:
            raise HarnessError(f"Self-test Stage 07 Closing prompt omitted role-heading scaffold: {required}")
    short_closing = "Closing Formulation\n\nShort governed close.\n"
    supplemented_closing, supplement_event = compiled_section_budget_guardrail(
        "closing_formulation",
        short_closing,
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        1800,
    )
    if not supplement_event:
        raise HarnessError("Self-test Closing Formulation budget guardrail did not record an event")
    if len(supplemented_closing.encode("utf-8")) < 1800:
        raise HarnessError("Self-test Closing Formulation budget guardrail remained under the byte floor")
    for required in ("### Closure boundary confirmation", "### Burden-state recap", "### Reopenable remainder"):
        if required not in supplemented_closing:
            raise HarnessError(f"Self-test Closing Formulation budget guardrail omitted {required}")
    for forbidden in ("harness", "byte budget", "manifest", "compiler"):
        if forbidden in supplemented_closing:
            raise HarnessError(f"Self-test Closing Formulation budget guardrail leaked harness term {forbidden}")
    unchanged_closing, unchanged_closing_event = compiled_section_budget_guardrail(
        "closing_formulation",
        short_closing + ("Already long enough. " * 120),
        [normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        1000,
    )
    if unchanged_closing_event or "### Closure boundary confirmation" in unchanged_closing:
        raise HarnessError("Self-test Closing Formulation budget guardrail mutated an over-floor section")
    stage07_witness_prompt = release_section_prompt(
        root=root,
        case_name="self-test-a9-science-source",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, normalized_stage05, normalized_stage06],
        section_id="field-witness-nar",
        section_role="field_witness_nar",
        section_number=7,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Do not set `owner` to `owner.operation`",
        "After Closing Formulation, print the visible Closure/Reconstruction Witness ledger",
        "visible `𝔅_MRP (B_MRP) = {}` and JSON `\"B_MRP\": []`",
        "JSON machine IDs remain canonical ASCII such as `B1`",
        "`𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP` is required",
        "`coverage_proof.dependency_graph` is required",
        "If the dependency edge list is non-empty",
        "Do not synthesize a generated-burden `MRP(Bn)` row with `graph=none`",
        "Each `nodes[]` burden payload must include `register_types`",
        "one `normalized_activation_record.per_burden[]` row per `owner_activations[]` mirror",
        "plus one MRP-owned row for each generated `B_MRP` burden",
        "`formal_reread_states[]` is required",
        "`curl_state` values must be parser-stable JSON strings",
        'emit JSON string `"null"`, never bare JSON null',
        "Terminal `STOP` / `no_new_resultant` rows must set",
        '"curl_state": "null"',
        '"B_MRP": []',
        '"dependency_graph"',
        '"formal_reread_states"',
        '"source_burden": "B1"',
        '"route_result_type": "no_new_resultant"',
        '"graph_delta": "none"',
        '"route": "STOP"',
        '"no_new_resultant_proof"',
        '"register_types": [\n        "xi",\n        "kappa"\n      ]',
        '"target": "B1"',
        '"generation_depth": 0',
        '"owner": "source-status-repair"',
        '"operation": "source-order"',
    ):
        if required not in stage07_witness_prompt:
            raise HarnessError(f"Self-test Stage 07 field_witness prompt omitted mirror scaffold: {required}")
    generated_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "held",
            "terminal_states": {"B1": "landed", "B2": "held-with-reason"},
            "dependency_graph_edges": [
                {"source": "B1", "target": "B2", "type": "generated_burden_instantiation", "via": "MRP(B1)"}
            ],
            "generated_burdens": [
                {
                    "burden_id": "B2",
                    "generated_by": "MRP(B1)",
                    "generation_depth": 1,
                    "required_owner_route": ["source-status-repair.source-order", "P7.scope-boundary"],
                    "reason": "self-test generated boundary remains live",
                }
            ],
            "reread_state": {
                "source_burden": "B1",
                "route_result_type": "generated_burden_instantiation",
                "route": "RECURSE",
            },
            "no_new_resultant_proof": {
                "proved": False,
                "basis": "self-test generated B2 remains unresolved",
                "unresolved_burdens": ["B2"],
            },
            "unresolved_burdens": ["B2"],
        },
    )
    generated_stage07_witness_prompt = release_section_prompt(
        root=root,
        case_name="self-test-generated-burden",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, generated_stage05, normalized_stage06],
        section_id="field-witness-nar",
        section_role="field_witness_nar",
        section_number=7,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "¹B (root); ¹B → ²B",
        "²B: held-with-reason / MRP(¹B) / no Stage 04 ACT rows",
        "MRP(¹B): type=generated_burden_instantiation; finding=genuine-dependent; graph=¹B → ²B; route=RECURSE",
        "𝒞(Ψᴺ): HOLD / coverage_complete=false; unresolved_burdens=[B2]",
        '"B_MRP": [\n    "B2"\n  ]',
        '"generated_burdens"',
        '"id": "B2"',
        '"generated_by": "MRP(B1)"',
        '"burden_id": "B2"',
        '"owner_id": "MRP"',
        '"operation": "generated_burden_instantiation"',
        '"coverage_complete": false',
        '"proved": false',
        "explicit HOLD/PARTIAL accounting",
    ):
        if required not in generated_stage07_witness_prompt:
            raise HarnessError(f"Self-test Stage 07 generated-burden prompt omitted scaffold: {required}")
    if "MRP(B2): type=generated_burden_instantiation" in generated_stage07_witness_prompt:
        raise HarnessError("Self-test Stage 07 generated-burden prompt synthesized an MRP(B2) graph=none row")
    wide_mrp_resultants = [
        {"source": "B1", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B1 -> B2", "route": "RECURSE"},
        {"source": "B2", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B2 -> B3", "route": "RECURSE"},
        {"source": "B3", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B3 -> B4", "route": "RECURSE"},
        {"source": "B4", "type": "held_burden_activation", "finding": "genuine-dependent", "graph": "B4 -> B5", "route": "RECURSE"},
        {"source": "B5", "type": "generated_burden_instantiation", "finding": "genuine-dependent", "graph": "B5 -> B6", "route": "RECURSE"},
        {"source": "B6", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"},
    ]
    wide_states = stage07_formal_reread_states(
        wide_mrp_resultants,
        {"B1": "landed", "B2": "landed", "B3": "landed", "B4": "landed", "B5": "landed", "B6": "carried-RECURSE"},
        unresolved_burdens=["B6"],
    )
    if [row.get("source_burden") for row in wide_states] != ["B1", "B2", "B3", "B4", "B5", "B6"]:
        raise HarnessError("Self-test Stage 07 wide MRP formal reread states did not preserve B1-B6 source registration")
    if any(row.get("curl_state") != "null" for row in wide_states):
        raise HarnessError("Self-test Stage 07 wide MRP formal reread states emitted non-string/null curl_state")
    b6_state = wide_states[-1]
    if b6_state.get("route_result_type") != "no_new_resultant" or b6_state.get("route") != "STOP":
        raise HarnessError("Self-test Stage 07 B6 terminal row did not preserve STOP/no_new_resultant accounting")
    proof = b6_state.get("no_new_resultant_proof")
    if not isinstance(proof, dict) or proof.get("proved") is not False:
        raise HarnessError("Self-test Stage 07 B6 unresolved row claimed clean no-new-resultant proof")
    if "plain-gradient holds ⁶B as HOLD/PARTIAL" not in str(b6_state.get("route_gradient")):
        raise HarnessError("Self-test Stage 07 B6 unresolved row omitted public-token HOLD/PARTIAL route-gradient")
    if "⁶B remains carried-RECURSE" not in str(b6_state.get("preemption_basis")):
        raise HarnessError("Self-test Stage 07 B6 unresolved row omitted generated-burden HOLD/PARTIAL accounting")
    wide_stage02 = dict(normalized_stage02)
    wide_stage02["burden_floor"] = ["B1", "B2", "B3", "B4", "B5"]
    wide_stage05 = normalized_stage(
        "stage-05-mrp-reread-terminal-state",
        {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "partial",
            "terminal_states": {
                "B1": "landed",
                "B2": "landed",
                "B3": "landed",
                "B4": "landed",
                "B5": "landed",
                "B6": "carried-RECURSE",
            },
            "dependency_graph_edges": [
                {"source": "B1", "target": "B2", "type": "held_burden_activation"},
                {"source": "B2", "target": "B3", "type": "held_burden_activation"},
                {"source": "B3", "target": "B4", "type": "held_burden_activation"},
                {"source": "B4", "target": "B5", "type": "held_burden_activation"},
                {"source": "B5", "target": "B6", "type": "generated_burden_instantiation"},
            ],
            "generated_burdens": [
                {
                    "burden_id": "B6",
                    "generated_by": "MRP(B5)",
                    "generation_depth": 1,
                    "required_owner_route": ["source-status-repair.source-order", "P7.scope-boundary"],
                    "reason": "self-test generated burden remains live",
                }
            ],
            "no_new_resultant_proof": {
                "proved": False,
                "basis": "self-test generated B6 remains unresolved",
                "unresolved_burdens": ["B6"],
            },
            "unresolved_burdens": ["B6"],
        },
    )
    wide_stage07_mrp_prompt = release_section_prompt(
        root=root,
        case_name="self-test-wide-generated-chain",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[wide_stage02, normalized_stage04, wide_stage05, normalized_stage06],
        section_id="mrp-reread-terminal",
        section_role="mrp_reread_terminal",
        section_number=6,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Emit one `[Mid-Reread Pressure]` block for every Stage 05 / field_witness `mrp_resultants[]` source",
        "Target: MRP(¹B) / Stage 05 terminal MRP source",
        "Target: MRP(²B) / Stage 05 terminal MRP source",
        "Target: MRP(³B) / Stage 05 terminal MRP source",
        "Target: MRP(⁴B) / Stage 05 terminal MRP source",
        "Target: MRP(⁵B) / Stage 05 terminal MRP source",
        "Target: MRP(⁶B) / Stage 05 terminal MRP source",
        "MRP route result type: generated_burden_instantiation",
        "MRP route result type: hold_partial",
        "Route: HOLD",
        "do not summarize a B1-B6 chain as one MRP block",
    ):
        if required not in wide_stage07_mrp_prompt:
            raise HarnessError(f"Self-test Stage 07 wide MRP prompt omitted scaffold: {required}")
    wide_stage07_witness_prompt = release_section_prompt(
        root=root,
        case_name="self-test-wide-generated-chain",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[wide_stage02, normalized_stage04, wide_stage05, normalized_stage06],
        section_id="field-witness-nar",
        section_role="field_witness_nar",
        section_number=7,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        '"source_burden": "B6"',
        '"route_result_type": "hold_partial"',
        '"route": "HOLD"',
        '"curl_state": "null"',
        '"coverage_complete": false',
        '"id": "B6"',
        '"generated_by": "MRP(B5)"',
    ):
        if required not in wide_stage07_witness_prompt:
            raise HarnessError(f"Self-test Stage 07 wide field_witness prompt omitted scaffold: {required}")

    def synthetic_act_row(burden: str) -> str:
        number = burden[1:]
        public = public_burden_id(burden)
        body_ref = f"{public}₁"
        return (
            f"⟦ACT {body_ref}[M8.trace] :: π=pressure-{number} :: "
            f"body_ref={body_ref} :: Δ=Δ{public}:landed-{number} :: Land({public})+⟧"
        )

    def synthetic_stage04(burdens: list[str]) -> dict[str, Any]:
        rows = [synthetic_act_row(burden) for burden in burdens]
        return normalized_stage(
            "stage-04-burden-execution-act",
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "act_targets": burdens,
                "act_burdens": burdens,
                "act_rows": rows,
            },
        )

    generated_topology_stage02 = {
        "id": "stage-02-layer-a-diagnostic-ir",
        "status": "pass",
        "selected_n_frame": "self-test-generated-topology",
        "live_registers": ["xi", "kappa"],
        "burden_floor": ["B1", "B2", "B3", "B4", "B5"],
        "burden_floor_details": [
            {"burden_id": "B1", "register_types": ["xi"]},
            {"burden_id": "B2", "register_types": ["kappa"]},
            {"burden_id": "B3", "register_types": ["xi"]},
            {"burden_id": "B4", "register_types": ["kappa"]},
            {"burden_id": "B5", "register_types": ["xi", "kappa"]},
        ],
    }

    def synthetic_generated_stage05(parent: str, generated: str, *, executed: bool) -> dict[str, Any]:
        terminal_states = {burden: "landed" for burden in generated_topology_stage02["burden_floor"]}
        terminal_states[generated] = "landed" if executed else "carried-RECURSE"
        payload: dict[str, Any] = {
            "id": "stage-05-mrp-reread-terminal-state",
            "status": "pass" if executed else "partial",
            "terminal_states": terminal_states,
            "dependency_graph_edges": [
                {
                    "from": parent,
                    "to": generated,
                    "source": f"MRP({parent})",
                    "type": "generated_burden_instantiation",
                }
            ],
            "generated_burdens": [
                {
                    "burden_id": generated,
                    "generated_by": f"MRP({parent})",
                    "generation_depth": 1,
                    "required_owner_route": ["source-status-repair.source-order", "P7.scope-boundary"],
                    "reason": f"self-test {parent} generated {generated}",
                }
            ],
            "reread_state": {
                "source_burden": generated if executed else parent,
                "route_result_type": "no_new_resultant" if executed else "generated_burden_instantiation",
                "route": "STOP" if executed else "RECURSE",
            },
        }
        if executed:
            payload["no_new_resultant_proof"] = {
                "proved": True,
                "basis": "generated burden was actually executed and landed in Stage 04",
                "unresolved_burdens": [],
            }
            payload["unresolved_burdens"] = []
        else:
            payload["no_new_resultant_proof"] = {
                "proved": False,
                "basis": "generated burden remains unresolved and carried",
                "unresolved_burdens": [generated],
            }
            payload["unresolved_burdens"] = [generated]
        return normalized_stage("stage-05-mrp-reread-terminal-state", payload)

    def assert_generated_topology(parent: str, generated: str, *, executed: bool, label: str) -> None:
        stage04 = synthetic_stage04([*generated_topology_stage02["burden_floor"], *([generated] if executed else [])])
        stage05 = synthetic_generated_stage05(parent, generated, executed=executed)
        stages_for_case = [generated_topology_stage02, stage04, stage05, normalized_stage06]
        mrp_text = stage07_mrp_reread_section_scaffold(stages_for_case)
        witness_text = stage07_field_witness_section_scaffold(stages_for_case)
        payload = first_json_object_from_text(witness_text)
        if payload is None:
            raise HarnessError(f"Self-test {label} generated topology did not emit field_witness JSON")
        if generated not in payload.get("B_MRP", []):
            raise HarnessError(f"Self-test {label} generated burden {generated} missing from B_MRP")
        if generated in payload.get("B_LA", []):
            raise HarnessError(f"Self-test {label} generated burden {generated} was misclassified as B_LA")
        if parent not in payload.get("B_LA", []):
            raise HarnessError(f"Self-test {label} parent {parent} must remain a baseline B_LA burden")
        generated_records = {
            str(item.get("id") or item.get("burden_id")): item
            for item in payload.get("generated_burdens", [])
            if isinstance(item, dict)
        }
        record = generated_records.get(generated)
        if not isinstance(record, dict) or record.get("generated_by") != f"MRP({parent})":
            raise HarnessError(f"Self-test {label} generated_burdens provenance missing MRP({parent})")
        edge = {"from": parent, "to": generated}
        coverage_edges = payload.get("coverage_proof", {}).get("dependency_graph", {}).get("edges", [])
        if edge not in coverage_edges:
            raise HarnessError(f"Self-test {label} dependency graph missing {parent}->{generated}")
        if not any(item.get("source") == parent and item.get("type") == "generated_burden_instantiation" for item in payload.get("mrp_resultants", [])):
            raise HarnessError(f"Self-test {label} MRP resultants missing generated source {parent}")
        public_marker = f"## Burden {generated[1:]} / {public_burden_id(generated)} [generated-by: MRP({public_burden_id(parent)})]"
        if public_marker not in mrp_text:
            raise HarnessError(f"Self-test {label} public generated marker missing")
        later_baselines = [
            burden
            for burden in generated_topology_stage02["burden_floor"]
            if int(burden[1:]) > int(parent[1:])
        ]
        for later in later_baselines:
            if later not in payload.get("B_LA", []):
                raise HarnessError(f"Self-test {label} later baseline {later} fell out of B_LA")
        coverage_complete = payload.get("coverage_proof", {}).get("coverage_complete")
        if executed:
            if coverage_complete is not True:
                raise HarnessError(f"Self-test {label} executed generated branch did not complete coverage")
            if f"Land({public_burden_id(generated)})" not in mrp_text:
                raise HarnessError(f"Self-test {label} executed generated branch did not render Land({generated})")
            activations = [
                item for item in payload.get("owner_activations", [])
                if isinstance(item, dict) and item.get("target") == generated
            ]
            if not activations or activations[0].get("source") != f"MRP({parent})":
                raise HarnessError(f"Self-test {label} executed generated branch lacked MRP(parent) owner activation")
        else:
            if coverage_complete is not False:
                raise HarnessError(f"Self-test {label} held generated branch falsely completed coverage")
            if f"HOLD({public_burden_id(generated)})" not in mrp_text:
                raise HarnessError(f"Self-test {label} held generated branch did not render HOLD({generated})")
            activations = [
                item for item in payload.get("owner_activations", [])
                if isinstance(item, dict) and item.get("target") == generated
            ]
            if activations:
                raise HarnessError(f"Self-test {label} held generated branch invented owner activations")

    assert_generated_topology("B1", "B6", executed=False, label="early-held")
    assert_generated_topology("B3", "B6", executed=False, label="mid-held")
    assert_generated_topology("B5", "B6", executed=False, label="terminal-held")
    assert_generated_topology("B3", "B6", executed=True, label="mid-executed")
    drifted_mrp_text = (
        "[Mid-Reread Pressure]\n"
        "Target: MRP(¹B)\n"
        "R(H,Δ): old model prose only.\n"
        "MRP route result type: generated_burden_instantiation\n"
        "MRP resultant: model drift without generated heading\n"
        "Route: RECURSE\n"
    )
    canonical_mrp_text, canonical_mrp_event = canonical_compiled_structural_section(
        "mrp_reread_terminal",
        drifted_mrp_text,
        [wide_stage02, normalized_stage04, wide_stage05, normalized_stage06],
    )
    if not canonical_mrp_event:
        raise HarnessError("Self-test Stage 07 structural MRP canonicalization did not record an event")
    for required in (
        "Target: MRP(⁵B) / Stage 05 terminal MRP source",
        "Route-gradient: generated-gradient points to RECURSE through ⁵B → ⁶B after Delta ⁵B",
        "## Burden 6 / ⁶B [generated-by: MRP(⁵B)]",
        "HOLD(⁶B): generated MRP burden remains unresolved/unexecuted",
        "Target: MRP(⁶B) / Stage 05 terminal MRP source",
        "MRP route result type: hold_partial",
        "Route: HOLD",
    ):
        if required not in canonical_mrp_text:
            raise HarnessError(f"Self-test Stage 07 structural MRP canonicalization omitted scaffold: {required}")
    if "old model prose only" in canonical_mrp_text:
        raise HarnessError("Self-test Stage 07 structural MRP canonicalization retained drifted model MRP prose")

    drifted_field_witness = (
        "Closure/Reconstruction Witness\n"
        "field_witness\n"
        "{\n"
        '  "B_LA": ["B1", "B2", "B3", "B4", "B5"],\n'
        '  "B_MRP": ["B6"],\n'
        '  "B_total": ["B1", "B2", "B3", "B4", "B5", "B6"],\n'
        '  "generated_burdens": [{"id": "B6", "generated_by": "MRP(B5)"}],\n'
        '  "mrp_resultants": [{"source": "B5", "type": "generated_burden_instantiation", "graph": "B5 -> B6", "route": "RECURSE"}],\n'
        '  "formal_reread_states": [{"source_burden": "B5", "curl_state": null}],\n'
        '  "coverage_proof": {"coverage_complete": true, "diagnostic_completeness": {"coverage": {"xi": ["B6"]}}}\n'
        "}\n"
    )
    canonical_witness_text, canonical_witness_event = canonical_compiled_structural_section(
        "field_witness_nar",
        drifted_field_witness,
        [wide_stage02, normalized_stage04, wide_stage05, normalized_stage06],
    )
    if not canonical_witness_event:
        raise HarnessError("Self-test Stage 07 structural field_witness canonicalization did not record an event")
    for required in (
        '"B_MRP": [\n    "B6"\n  ]',
        '"generated_by": "MRP(B5)"',
        '"source_burden": "B6"',
        '"route_result_type": "hold_partial"',
        '"coverage_complete": false',
        '"owner_route": [\n        "source-status-repair.source-order",\n        "P7.scope-boundary"\n      ]',
    ):
        if required not in canonical_witness_text:
            raise HarnessError(f"Self-test Stage 07 structural field_witness canonicalization omitted scaffold: {required}")
    if '"coverage_complete": true' in canonical_witness_text or '"curl_state": null' in canonical_witness_text:
        raise HarnessError("Self-test Stage 07 structural field_witness canonicalization retained drifted proof values")
    generated_stage07_mrp_prompt = release_section_prompt(
        root=root,
        case_name="self-test-generated-burden",
        raw_input_path=raw_input,
        input_text=raw_input.read_text(encoding="utf-8", errors="replace"),
        input_digest=sha256_file(raw_input),
        skill_hash="SELFTEST",
        previous_stages=[normalized_stage02, normalized_stage04, generated_stage05, normalized_stage06],
        section_id="mrp-reread-terminal",
        section_role="mrp_reread_terminal",
        section_number=6,
        section_count=9,
        target_output_kb=70,
        section_min_bytes=1024,
        assigned_body_refs=None,
    )
    for required in (
        "Target: MRP(¹B) / Stage 05 terminal MRP source",
        "R(H,Δ): held routes rechecked: ¹B → ²B; live remainder: ²B; release/next: RECURSE.",
        "Landed delta: Delta B1: terminal state landed; MRP route result type generated_burden_instantiation.",
        "Route-gradient: generated-gradient points to RECURSE through ¹B → ²B after Delta ¹B; newly generated ²B [generated-by: MRP(¹B)] is absent from 𝔅_LA and comes from post-Land field-pressure.",
        "Matched owner/TTP route: [source-status-repair.source-order], [P7.scope-boundary]",
        "Finding: genuine-dependent",
        "MRP route result type: generated_burden_instantiation",
        "MRP resultant: genuine-dependent -> graph ¹B → ²B; route RECURSE",
        "Graph delta: ¹B → ²B",
        "Pre-emption basis: graph-bound MRP route recorded",
        "Route: RECURSE",
        "For generated or held routes, use the exact Stage 05 graph edge in `Graph delta:`",
    ):
        if required not in generated_stage07_mrp_prompt:
            raise HarnessError(f"Self-test Stage 07 generated MRP prompt omitted scaffold: {required}")
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
    selected_detail_stage06 = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁", "¹B₂"],
            "nar_burdens": ["B1"],
            "owner_activations": ["¹B₁", "¹B₂"],
            "normalized_activation_record": {
                "n_frame": {
                    "selected": "science-only-source-order-warrant",
                    "held": ["revelation-private-preference-frame"],
                },
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
            },
            "register_deltas": {"xi": "source-order-landed"},
        },
    )
    selected_detail_nar = selected_detail_stage06["normalized_activation_record"]
    if selected_detail_nar.get("n_frame") != "science-only-source-order-warrant":
        raise HarnessError("Self-test failed to normalize object-shaped Stage 06 n_frame to selected scalar")
    selected_detail = selected_detail_nar.get("n_frame_details")
    if not isinstance(selected_detail, dict) or selected_detail.get("selected") != "science-only-source-order-warrant":
        raise HarnessError("Self-test failed to preserve object-shaped Stage 06 n_frame under n_frame_details")
    selected_detail_normalization = selected_detail_nar.get("normalization")
    if not isinstance(selected_detail_normalization, dict) or selected_detail_normalization.get("n_frame_from_selected_detail") is not True:
        raise HarnessError("Self-test failed to record Stage 06 n_frame selected/detail normalization")
    supplemental_details_stage06 = normalized_stage(
        "stage-06-field-witness-nar",
        {
            "id": "stage-06-field-witness-nar",
            "status": "pass",
            "field_witness_body_refs": ["¹B₁", "¹B₂"],
            "nar_burdens": ["B1"],
            "owner_activations": ["¹B₁", "¹B₂"],
            "normalized_activation_record": copy.deepcopy(structured_nar),
            "normalized_activation_record_details": {
                "n_frame_details": {
                    "selected": "science-only-source-order-warrant",
                    "held_frame_pressures": ["revelation-private-preference-frame"],
                },
                "per_burden_count": 1,
                "generated_terminal_burdens_without_act": [],
            },
            "register_deltas": {"xi": "source-order-landed"},
        },
    )
    supplemental_details = supplemental_details_stage06["normalized_activation_record_details"]
    if supplemental_details.get("n_frame") != "science-only-source-order-warrant":
        raise HarnessError("Self-test failed to hydrate supplemental Stage 06 NAR details from canonical NAR")
    supplemental_normalization = supplemental_details.get("normalization")
    if not isinstance(supplemental_normalization, dict) or "per_burden" not in supplemental_normalization.get(
        "hydrated_from_normalized_activation_record", []
    ):
        raise HarnessError("Self-test failed to record supplemental Stage 06 NAR details hydration")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₁"],
                "normalized_activation_record": copy.deepcopy(structured_nar),
                "normalized_activation_record_details": {
                    "n_frame_details": {"selected": "mismatched-frame"},
                    "per_burden_count": 1,
                },
                "register_deltas": {"xi": "source-order-landed"},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject supplemental Stage 06 NAR details with mismatched n_frame")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₁"],
                "normalized_activation_record": True,
                "normalized_activation_record_details": {
                    "n_frame_details": {"selected": "science-only-source-order-warrant"},
                    "per_burden_count": 1,
                },
                "register_deltas": {"xi": "source-order-landed"},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject supplemental Stage 06 NAR details without structured canonical NAR")
    try:
        normalized_stage(
            "stage-06-field-witness-nar",
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "field_witness_body_refs": ["¹B₁"],
                "nar_burdens": ["B1"],
                "owner_activations": ["¹B₁"],
                "normalized_activation_record": {
                    "n_frame": {"held": ["revelation-private-preference-frame"]},
                    "live_registers": ["xi", "kappa"],
                    "burden_floor": ["B1"],
                    "per_burden": [{"burden_id": "B1"}],
                },
                "register_deltas": {"xi": "source-order-landed"},
            },
        )
    except HarnessError:
        pass
    else:
        raise HarnessError("Self-test failed to reject object-shaped Stage 06 n_frame without selected scalar")
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

    stage06_register_delta_list_record = dict(stage06_local_record)
    stage06_register_delta_list_record["case_id"] = "self-test-stage06-register-delta-list-values"
    stage06_register_delta_list_record["model_scope"] = model_scope(
        "self-test-stage06-register-delta-list-values",
        replay_record,
        stop_after_stage="stage-06-field-witness-nar",
    )
    stage06_register_delta_list_record["stages"] = [dict(stage) for stage in stage06_local_record["stages"]]
    stage06_register_delta_list_record["stages"][-1] = dict(stage06_register_delta_list_record["stages"][-1])
    stage06_register_delta_list_record["stages"][-1]["register_deltas"] = [
        {"register": "Omega", "delta": ["B1:model-family-bounded", "B1:predicate-separated"]},
        {"register": "xi", "delta": "B1:source-order-landed"},
    ]
    stage06_register_delta_list_path = run_dir / "stage06-register-delta-list-values.valid.json"
    write_json(stage06_register_delta_list_path, stage06_register_delta_list_record)
    validate_replay_record(root, stage06_register_delta_list_path)

    for invalid_delta, suffix in [
        ([], "empty"),
        (["B1:source-order-landed", 1], "non-string-member"),
    ]:
        invalid_register_delta_record = dict(stage06_register_delta_list_record)
        invalid_register_delta_record["case_id"] = f"self-test-stage06-register-delta-list-{suffix}"
        invalid_register_delta_record["model_scope"] = model_scope(
            f"self-test-stage06-register-delta-list-{suffix}",
            replay_record,
            stop_after_stage="stage-06-field-witness-nar",
        )
        invalid_register_delta_record["stages"] = [
            dict(stage) for stage in stage06_register_delta_list_record["stages"]
        ]
        invalid_register_delta_record["stages"][-1] = dict(invalid_register_delta_record["stages"][-1])
        invalid_register_delta_record["stages"][-1]["register_deltas"] = [
            {"register": "xi", "delta": invalid_delta}
        ]
        invalid_register_delta_path = run_dir / f"stage06-register-delta-list-{suffix}.invalid.json"
        write_json(invalid_register_delta_path, invalid_register_delta_record)
        invalid_result = run_checked(
            [
                sys.executable,
                str(root / "tools" / "check_staged_runtime_handshake.py"),
                "--records",
                str(invalid_register_delta_path),
            ],
            cwd=root,
        )
        if invalid_result.returncode == 0:
            raise HarnessError(
                f"Self-test failed to reject Stage 06 register_deltas list-object {suffix} delta"
            )

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
        "public_burden_grouping": "pass",
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
            "public_burden_grouping",
            [sys.executable, str(root / "tools" / "check_public_burden_grouping.py"), "--outputs", str(output_path)],
        ),
        (
            "owner_activation_ordering",
            [sys.executable, str(root / "tools" / "check_owner_activation_ordering.py"), "--require-plan", "--outputs", str(output_path)],
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
    run_dir = resolve_under_root(root, args.run_dir, "Run directory")
    resume_context: dict[str, Any] | None = None
    if args.resume_run_dir is not None:
        resume_run_dir = resolve_under_root(root, args.resume_run_dir, "Resume run directory")
        if resume_run_dir != run_dir:
            raise HarnessError("--resume-run-dir and --run-dir must identify the same directory")
        resume_context = load_stage07_resume_context(root, resume_run_dir)
        replay_record = resume_context["replay_record_path"]
        raw_input = resume_context["raw_input_path"]
    else:
        replay_record = resolve_under_root(root, args.replay_record, "Replay record")
        raw_input = resolve_under_root(root, args.raw_input_path, "Raw input")
    validate_replay_record(root, replay_record)
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
    stages: list[dict[str, Any]] = list(resume_context["stages"]) if resume_context else []
    stage_files: list[Path] = list(resume_context["artifact_paths"]) if resume_context else []
    transport_attempts: list[dict[str, Any]] = list(resume_context["prior_attempts"]) if resume_context else []
    transport_attempts_record_path = records_dir / "stage-07-transport-attempts.json"
    if transport_attempts:
        write_transport_attempts_record(transport_attempts_record_path, root=root, attempts=transport_attempts)
        stage_files.append(transport_attempts_record_path)
    mode = "staged-current-skill-stage-local-smoke" if args.stop_after_stage else "staged-current-skill-smoke"
    release_output_mode = normalize_release_output_mode(args.release_output_mode)
    if resume_context is not None and release_output_mode != "compiled-output":
        raise HarnessError("--resume-run-dir requires --release-output-mode compiled")
    if resume_context is not None and args.stop_after_stage not in (None, "stage-07-release-output"):
        raise HarnessError("--resume-run-dir may only resume through stage-07-release-output or the full smoke")
    record = base_record(
        args.case_name,
        mode,
        not_model_smoke=False,
        stop_after_stage=args.stop_after_stage,
        model_scope_payload=model_scope(args.case_name, replay_record, stop_after_stage=args.stop_after_stage),
    )

    try:
        if resume_context is None:
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
            section_budgets = compiled_section_budgets(section_plan, args.target_output_kb)
            min_section_bytes = (
                dict(section_budgets.get("min_section_bytes", {}))
                if isinstance(section_budgets, dict)
                else {}
            )
            act_partition = compiled_act_partition(stages, section_plan)
            assigned_refs_by_section = {
                str(item["section_id"]): list(item["body_refs"])
                for item in act_partition["assignments"]
                if isinstance(item, dict)
            }
            sections_dir = run_dir / "release-sections"
            sections_dir.mkdir(parents=True, exist_ok=True)
            expansions_dir = run_dir / "release-section-expansions"
            if args.section_expansion_rounds:
                expansions_dir.mkdir(parents=True, exist_ok=True)
            section_entries: list[dict[str, str]] = []
            expansion_records: list[dict[str, Any]] = (
                existing_expansion_records_for_resume(
                    root=root,
                    run_dir=run_dir,
                    section_plan=section_plan,
                    max_rounds=args.section_expansion_rounds,
                    artifact_hashes=resume_context["artifact_hashes"],
                )
                if resume_context is not None
                else []
            )
            expansion_record_paths = {str(Path(record["path"]).resolve()) for record in expansion_records}
            if args.section_expansion_rounds:
                stage_files.append(transport_attempts_record_path)
            for index, (section_id, section_role) in enumerate(section_plan, start=1):
                section_min_bytes = int(min_section_bytes.get(section_id, 0) or 0)
                assigned_refs = assigned_refs_by_section.get(section_id)
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
                    section_min_bytes=section_min_bytes,
                    assigned_body_refs=assigned_refs,
                )
                safe_section_id = section_id.replace("_", "-")
                section_prompt_path = prompts_dir / f"stage-07-release-output-{index:02d}-{safe_section_id}.prompt.md"
                section_output_path = sections_dir / f"{index:02d}-{safe_section_id}.md"
                section_log_path = responses_dir / f"stage-07-release-output-{index:02d}-{safe_section_id}.codex-log.txt"
                if resume_context is not None and section_output_path.exists():
                    require_hash_matched(
                        section_output_path,
                        root=root,
                        artifact_hashes=resume_context["artifact_hashes"],
                        label="resumed section output",
                    )
                else:
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
                for expansion_round in range(1, args.section_expansion_rounds + 1):
                    current_text = section_output_path.read_text(encoding="utf-8", errors="replace")
                    current_bytes = len(current_text.encode("utf-8"))
                    if not section_min_bytes or current_bytes >= section_min_bytes:
                        break
                    expansion_prompt = release_section_expansion_prompt(
                        root=root,
                        case_name=args.case_name,
                        raw_input_path=raw_input,
                        input_digest=input_digest,
                        skill_hash=skill_hash,
                        section_id=section_id,
                        section_role=section_role,
                        section_min_bytes=section_min_bytes,
                        current_bytes=current_bytes,
                        expansion_round=expansion_round,
                        max_rounds=args.section_expansion_rounds,
                        assigned_body_refs=assigned_refs,
                        existing_text=current_text,
                    )
                    expansion_prompt_path = (
                        prompts_dir
                        / f"stage-07-release-output-{index:02d}-{safe_section_id}-expansion-{expansion_round}.prompt.md"
                    )
                    expansion_output_path = (
                        expansions_dir / f"{index:02d}-{safe_section_id}-expansion-{expansion_round}.md"
                    )
                    expansion_log_path = (
                        responses_dir
                        / f"stage-07-release-output-{index:02d}-{safe_section_id}-expansion-{expansion_round}.codex-log.txt"
                    )
                    if resume_context is not None and expansion_output_path.exists():
                        require_hash_matched(
                            expansion_output_path,
                            root=root,
                            artifact_hashes=resume_context["artifact_hashes"],
                            label="resumed expansion output",
                        )
                    else:
                        failed_expansion = resume_context.get("failed_expansion") if resume_context else None
                        is_resumed_failed_expansion = (
                            isinstance(failed_expansion, dict)
                            and failed_expansion.get("section_id") == section_id
                            and failed_expansion.get("round") == expansion_round
                        )
                        first_attempt = 2 if is_resumed_failed_expansion else 1
                        expansion_output_path = invoke_expansion_with_transport_policy(
                            root=root,
                            model=args.model,
                            prompt=expansion_prompt,
                            base_prompt_path=expansion_prompt_path,
                            base_output_path=expansion_output_path,
                            base_log_path=expansion_log_path,
                            section_id=section_id,
                            section_role=section_role,
                            expansion_round=expansion_round,
                            first_attempt=first_attempt,
                            retry_rounds=args.transport_retry_rounds,
                            attempts=transport_attempts,
                            attempts_record_path=transport_attempts_record_path,
                            stage_files=stage_files,
                        )
                    if not expansion_output_path.exists() or expansion_output_path.stat().st_size == 0:
                        raise HarnessError(
                            f"stage-07-release-output {section_id} expansion {expansion_round}: "
                            "expansion output was not produced"
                        )
                    expansion_text = expansion_output_path.read_text(encoding="utf-8", errors="replace").strip()
                    if not expansion_text:
                        raise HarnessError(
                            f"stage-07-release-output {section_id} expansion {expansion_round}: "
                            "expansion output was empty"
                        )
                    if str(expansion_output_path.resolve()) not in expansion_record_paths:
                        separator = "\n" if current_text.endswith("\n") else "\n\n"
                        write_text(section_output_path, current_text + separator + expansion_text + "\n")
                        expansion_records.append(
                            {
                                "section_id": section_id,
                                "role": section_role,
                                "round": expansion_round,
                                "path": str(expansion_output_path),
                                "sha256": sha256_file(expansion_output_path),
                            }
                        )
                        expansion_record_paths.add(str(expansion_output_path.resolve()))
                current_text = section_output_path.read_text(encoding="utf-8", errors="replace")
                canonical_text, canonical_event = canonical_compiled_structural_section(
                    section_role,
                    current_text,
                    stages,
                )
                if canonical_event is not None:
                    write_text(section_output_path, canonical_text)
                    current_text = canonical_text
                budget_text, budget_event = compiled_section_budget_guardrail(
                    section_role,
                    current_text,
                    stages,
                    section_min_bytes,
                )
                if budget_event is not None:
                    write_text(section_output_path, budget_text)
                section_entries.append(
                    {
                        "id": section_id,
                        "role": section_role,
                        "path": str(section_output_path),
                        "sha256": sha256_file(section_output_path),
                    }
                )
            assembly_manifest_path = run_dir / "stage-07-output-assembly.manifest.json"
            transport_resume_payload = None
            if resume_context is not None:
                transport_resume_payload = {
                    "schema": TRANSPORT_RESUME_SCHEMA,
                    "resumed": True,
                    "source_run_dir": resume_context["run_dir"],
                    "hash_record": resume_context["hash_record"],
                    "failure_record": resume_context["failure_record"],
                    "failed_expansion": resume_context["failed_expansion"],
                    "attempts_record": rel(transport_attempts_record_path, assembly_manifest_path.parent),
                    "attempts": transport_attempts,
                }
            write_compiled_release_manifest(
                root=root,
                manifest_path=assembly_manifest_path,
                case_name=args.case_name,
                raw_input_path=raw_input,
                section_entries=section_entries,
                output_path=output_path,
                target_output_kb=args.target_output_kb,
                act_partition=act_partition,
                section_budgets=section_budgets,
                section_expansions={
                    "schema": staged_output.SECTION_EXPANSIONS_SCHEMA,
                    "rounds_allowed": int(args.section_expansion_rounds or 0),
                    "records": [
                        {
                            "section_id": record["section_id"],
                            "role": record["role"],
                            "round": record["round"],
                            "path": rel(Path(record["path"]), assembly_manifest_path.parent),
                            "sha256": record["sha256"],
                        }
                        for record in expansion_records
                    ],
                }
                if args.section_expansion_rounds or expansion_records
                else None,
                transport_resume=transport_resume_payload,
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
    parser.add_argument("--section-expansion-rounds", type=int, default=0)
    parser.add_argument("--transport-retry-rounds", type=int, default=0)
    parser.add_argument("--resume-run-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if Path.cwd().resolve() != root:
        raise HarnessError(
            f"Wrong current directory. Current={Path.cwd().resolve()}; expected root={root}. "
            "Run from the repo root so artifacts cannot bind another workspace."
        )
    if args.section_expansion_rounds < 0:
        raise HarnessError("--section-expansion-rounds must be a non-negative integer")
    if args.transport_retry_rounds < 0:
        raise HarnessError("--transport-retry-rounds must be a non-negative integer")
    if args.self_test:
        return run_self_test(root)
    if args.resume_run_dir is not None:
        resume_run_dir = resolve_under_root(root, args.resume_run_dir, "Resume run directory")
        if args.run_dir is None:
            args.run_dir = resume_run_dir
        else:
            run_dir = resolve_under_root(root, args.run_dir, "Run directory")
            if run_dir != resume_run_dir:
                raise HarnessError("--resume-run-dir and --run-dir must identify the same directory")
            args.run_dir = run_dir
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
