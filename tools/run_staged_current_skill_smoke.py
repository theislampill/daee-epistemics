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
            "Do not release a final answer."
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
            "objects in `route_targets`."
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
            "Produce dependency graph evidence, terminal states, and no-new-resultant or "
            "HOLD/PARTIAL accounting."
        ),
    },
    "stage-06-field-witness-nar": {
        "title": "field_witness / NAR",
        "produces": ["field_witness_body_refs", "nar_burdens", "normalized_activation_record"],
        "requires": ["terminal_states", "act_body_refs"],
        "instructions": (
            "Produce parser-stable field_witness/NAR summary fields that mirror ACT rows and "
            "terminal states."
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
    if stage_id == "stage-03-routing-owner-gate":
        normalize_stage03_route_targets(stage)
    if stage_id == "stage-04-burden-execution-act":
        normalize_stage04_act_fields(stage)
    return stage


def ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


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
        normalization = stage.get("normalization")
        if not isinstance(normalization, dict):
            normalization = {}
        normalization["route_targets_from_details"] = True
        normalization["canonical_route_targets"] = list(stage["route_targets"])
        stage["normalization"] = normalization
        return
    raise HarnessError("stage-03 route_targets must be a non-empty list of burden-id strings")


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
        if set(list_field(stage04, "act_body_refs")) != set(list_field(stage06, "field_witness_body_refs")):
            raise HarnessError("stage-06 field_witness_body_refs must match stage-04 act_body_refs")
        act_burdens = set(list_field(stage04, "act_burdens") or list_field(stage04, "act_targets"))
        nar_burdens = set(list_field(stage06, "nar_burdens"))
        missing = sorted(act_burdens - nar_burdens)
        if missing:
            raise HarnessError(f"stage-06 nar_burdens missing ACT burden(s): {missing}")
    if stage05 and stage05.get("terminal_states") in ({}, None):
        raise HarnessError("stage-05 terminal_states must be non-empty")


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

Produce the final governed `output.md` only. It must contain the normal visible
noetic-field opening, compact Layer A, Layer B governed operations with ACT rows,
state reread/MRP accounting when live, parser-stable field_witness/NAR evidence,
Restorative Response, and Closing Formulation. Do not include commentary about
this harness. Do not claim package/provenance, guaranteed uptake, or broad A/B/C/D
closure.
"""


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
        record["stage_scope"] = {
            "stop_after_stage": stop_after_stage,
            "stage_count": len(stage_order),
            "not_release_output": True,
            "not_verifier_sidecars": True,
        }
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
            "owner_routes": [],
        },
    )
    if normalized.get("route_targets") != ["B1"]:
        raise HarnessError("Self-test failed to normalize rich Stage 03 route_targets into burden-id list")
    if not isinstance(normalized.get("route_target_details"), list):
        raise HarnessError("Self-test failed to preserve rich Stage 03 route metadata")

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
    print("staged current-skill harness self-test: PASS")
    print(f"self-test run dir: {rel(run_dir, root)}")
    print(f"handoff record: {rel(record_path, root)}")
    print(f"hashes: {rel(hash_path, root)}")
    return 0


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
    record = base_record(
        args.case_name,
        mode,
        not_model_smoke=False,
        stop_after_stage=args.stop_after_stage,
        model_scope_payload=model_scope(args.case_name, replay_record, stop_after_stage=args.stop_after_stage),
    )

    try:
        stage_ids_to_run = stage_order_for_stop(args.stop_after_stage)
        if args.stop_after_stage is None:
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
        output_path = run_dir / "output.md"
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
        }
        stages.append(stage07)

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
    parser.add_argument("--stop-after-stage", choices=STAGE_ORDER[:6], default=None)
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
