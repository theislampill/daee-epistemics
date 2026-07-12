#!/usr/bin/env python3
"""Validate versioned DAEE prompt-pack JSONL lines against bounded budgets.

This is a cheap, stdlib-only budget gate over additive prompt-pack manifests.
Version 1 preserves its original whole-prompt accounting. Version 2 applies
the same token ceiling only to the harness frame, separately measures the
resolver-selected runtime components, and binds them to the A12 sidecar and
final prompt bytes. Neither version runs a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
SMOKE_HARNESS_PATH = ROOT / "tools" / "run_staged_current_skill_smoke.py"


SCHEMA_V1 = "daee-prompt-pack-manifest-v1"
SCHEMA_V2 = "daee-prompt-pack-manifest-v2"
# Backward-compatible public name used by existing v1 fixtures and consumers.
SCHEMA = SCHEMA_V1
REQUIRED_KEYS = (
    "schema",
    "case_id",
    "stage",
    "call_index",
    "components",
    "total_bytes",
    "total_est_tok",
    "includes_full_runtime",
    "includes_prior_full_output",
)
DEFAULT_CEILING = 20_000
V2_REQUIRED_KEYS = frozenset(
    {
        "schema",
        "case_id",
        "stage",
        "call_index",
        "harness_frame",
        "runtime_context",
        "includes_full_runtime",
        "includes_prior_full_output",
    }
)
V2_HARNESS_FRAME_KEYS = frozenset({"components", "total_bytes", "total_est_tok"})
V2_RUNTIME_CONTEXT_KEYS = frozenset(
    {
        "component_scope",
        "manifest_path",
        "manifest_sha256",
        "prompt_path",
        "prompt_sha256",
        "prompt_byte_count",
        "selected_components",
        "selected_component_bytes",
        "effective_context_bytes",
        "effective_context_limit",
    }
)
V2_COMPONENT_KEYS = frozenset({"component_id", "sha256", "byte_count"})


class BudgetViolation(Exception):
    """A single manifest line failed validation."""


def _case_label(record: dict[str, Any]) -> str:
    case_id = record.get("case_id", "<missing case_id>")
    stage = record.get("stage", "<missing stage>")
    call_index = record.get("call_index", "<missing call_index>")
    return f"case_id={case_id!r} stage={stage!r} call_index={call_index!r}"


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _closed_keys(value: Any, expected: frozenset[str], label: str, record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BudgetViolation(f"{_case_label(record)}: {label} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        detail = []
        if missing:
            detail.append(f"missing={missing}")
        if extra:
            detail.append(f"unknown={extra}")
        raise BudgetViolation(f"{_case_label(record)}: {label} fields are not closed ({', '.join(detail)})")
    return value


def _validate_sha256(value: Any, label: str, record: dict[str, Any]) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise BudgetViolation(f"{_case_label(record)}: {label} is not a lowercase SHA-256")


def _resolve_record_path(artifact_root: Path, value: Any, label: str, record: dict[str, Any]) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise BudgetViolation(f"{_case_label(record)}: {label} must be a non-empty relative path")
    root = artifact_root.resolve()
    resolved = (root / value).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise BudgetViolation(f"{_case_label(record)}: {label} escapes the artifact root") from exc
    return resolved


def _path_under_root(artifact_root: Path, path: Path, label: str) -> Path:
    root = artifact_root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise BudgetViolation(f"{label} escapes the artifact root") from exc
    return resolved


def _selected_component_rows(context: dict[str, Any], record: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        selection = context["selection"]
        selected_ids = selection["selected_components"]
        components = context["components"]
    except (KeyError, TypeError) as exc:
        raise BudgetViolation(f"{_case_label(record)}: runtime context lacks selection/components") from exc
    if not isinstance(selection, dict) or selection.get("status") != "selected":
        raise BudgetViolation(f"{_case_label(record)}: runtime context selection is not dispatchable 'selected' state")
    if not isinstance(selected_ids, list) or not selected_ids or not all(isinstance(value, str) and value for value in selected_ids):
        raise BudgetViolation(f"{_case_label(record)}: runtime context selected_components must be a non-empty string list")
    if len(selected_ids) != len(set(selected_ids)):
        raise BudgetViolation(f"{_case_label(record)}: runtime context selected component IDs are not unique")
    if not isinstance(components, list):
        raise BudgetViolation(f"{_case_label(record)}: runtime context components must be a list")
    by_id: dict[str, dict[str, Any]] = {}
    for component in components:
        if not isinstance(component, dict) or not isinstance(component.get("component_id"), str):
            raise BudgetViolation(f"{_case_label(record)}: malformed runtime context component")
        component_id = component["component_id"]
        if component_id in by_id:
            raise BudgetViolation(f"{_case_label(record)}: duplicate runtime context component ID {component_id!r}")
        by_id[component_id] = component
    missing = [component_id for component_id in selected_ids if component_id not in by_id]
    if missing:
        raise BudgetViolation(f"{_case_label(record)}: selected runtime component(s) absent from context: {missing}")
    rows: list[dict[str, Any]] = []
    for component_id in selected_ids:
        component = by_id[component_id]
        _validate_sha256(component.get("sha256"), f"runtime context component {component_id!r} SHA-256", record)
        byte_count = component.get("byte_count")
        if not _is_int(byte_count) or byte_count <= 0:
            raise BudgetViolation(f"{_case_label(record)}: runtime context component {component_id!r} has invalid byte_count")
        rows.append({"component_id": component_id, "sha256": component["sha256"], "byte_count": byte_count})
    return rows


def _validate_v2_artifact_bindings(record: dict[str, Any], runtime: dict[str, Any], artifact_root: Path) -> None:
    context_path = _resolve_record_path(artifact_root, runtime["manifest_path"], "runtime_context.manifest_path", record)
    prompt_path = _resolve_record_path(artifact_root, runtime["prompt_path"], "runtime_context.prompt_path", record)
    try:
        context_bytes = context_path.read_bytes()
    except OSError as exc:
        raise BudgetViolation(f"{_case_label(record)}: cannot read runtime context manifest: {exc}") from exc
    if _sha256_bytes(context_bytes) != runtime["manifest_sha256"]:
        raise BudgetViolation(f"{_case_label(record)}: runtime context manifest SHA-256 mismatch")
    try:
        context = json.loads(context_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BudgetViolation(f"{_case_label(record)}: runtime context manifest is not valid UTF-8 JSON") from exc
    if not isinstance(context, dict) or context.get("schema") != "daee-runtime-call-context-v1":
        raise BudgetViolation(f"{_case_label(record)}: runtime context manifest schema mismatch")
    context_supplements = sorted(
        (
            {
                "name": component.get("component_id"),
                "sha256": component.get("sha256"),
                "bytes": component.get("byte_count"),
                "est_tok": component.get("byte_count", 0) // 4,
            }
            for component in context.get("components", [])
            if isinstance(component, dict) and component.get("kind") == "harness-supplement"
        ),
        key=lambda item: str(item["name"]),
    )
    if record["harness_frame"]["components"] != context_supplements:
        raise BudgetViolation(
            f"{_case_label(record)}: harness frame identity/hash/byte binding differs from runtime context supplements"
        )
    if (context.get("case_id"), context.get("stage"), context.get("call_index")) != (
        record["case_id"],
        record["stage"],
        record["call_index"],
    ):
        raise BudgetViolation(f"{_case_label(record)}: runtime context identity differs from prompt-pack identity")

    try:
        context_prompt = context["prompt"]
        telemetry = context["budget_telemetry"]
    except (KeyError, TypeError) as exc:
        raise BudgetViolation(f"{_case_label(record)}: runtime context lacks prompt/budget telemetry") from exc
    if not isinstance(context_prompt, dict) or not isinstance(telemetry, dict):
        raise BudgetViolation(f"{_case_label(record)}: runtime context prompt/budget telemetry is malformed")
    expected_prompt_path = _resolve_record_path(
        context_path.parent,
        context_prompt.get("path"),
        "runtime context prompt.path",
        record,
    )
    if expected_prompt_path != prompt_path:
        raise BudgetViolation(f"{_case_label(record)}: prompt-pack prompt path differs from runtime context prompt path")
    try:
        prompt_bytes = prompt_path.read_bytes()
    except OSError as exc:
        raise BudgetViolation(f"{_case_label(record)}: cannot read final prompt: {exc}") from exc
    prompt_sha256 = _sha256_bytes(prompt_bytes)
    if prompt_sha256 != runtime["prompt_sha256"]:
        raise BudgetViolation(f"{_case_label(record)}: final prompt SHA-256 mismatch")
    if len(prompt_bytes) != runtime["prompt_byte_count"]:
        raise BudgetViolation(f"{_case_label(record)}: final prompt byte count mismatch")
    if context_prompt.get("sha256") != prompt_sha256 or context_prompt.get("byte_count") != len(prompt_bytes):
        raise BudgetViolation(f"{_case_label(record)}: runtime context prompt binding differs from final prompt bytes")
    if context_prompt.get("includes_full_runtime") is not record["includes_full_runtime"]:
        raise BudgetViolation(f"{_case_label(record)}: whole-runtime semantic flag differs from runtime context")
    if context_prompt.get("includes_prior_full_output") is not record["includes_prior_full_output"]:
        raise BudgetViolation(f"{_case_label(record)}: prior-output semantic flag differs from runtime context")

    derived_rows = _selected_component_rows(context, record)
    if runtime["selected_components"] != derived_rows:
        raise BudgetViolation(f"{_case_label(record)}: selected component identity/hash/byte binding differs from runtime context")
    if runtime["selected_component_bytes"] != sum(row["byte_count"] for row in derived_rows):
        raise BudgetViolation(f"{_case_label(record)}: selected component byte total differs from runtime context")
    if telemetry.get("selected_component_count") != len(derived_rows):
        raise BudgetViolation(f"{_case_label(record)}: selected component count differs from runtime context telemetry")
    if telemetry.get("effective_context_bytes") != runtime["effective_context_bytes"]:
        raise BudgetViolation(f"{_case_label(record)}: effective context bytes differ from runtime context telemetry")
    if telemetry.get("effective_context_limit") != runtime["effective_context_limit"]:
        raise BudgetViolation(f"{_case_label(record)}: effective context limit differs from runtime context telemetry")


def _validate_v2_record(record: dict[str, Any], ceiling: int, artifact_root: Path | None) -> None:
    _closed_keys(record, V2_REQUIRED_KEYS, "prompt-pack-v2", record)
    if not isinstance(record["case_id"], str) or not record["case_id"]:
        raise BudgetViolation(f"{_case_label(record)}: case_id must be a non-empty string")
    if not isinstance(record["stage"], str) or re.fullmatch(r"0[1-7]", record["stage"]) is None:
        raise BudgetViolation(f"{_case_label(record)}: stage must be an exact 01-07 identity")
    if not _is_int(record["call_index"]) or record["call_index"] < 1:
        raise BudgetViolation(f"{_case_label(record)}: call_index must be a positive integer")
    if record["includes_full_runtime"] is not False:
        raise BudgetViolation(f"{_case_label(record)}: explicit includes_full_runtime semantic flag is not false")
    if record["includes_prior_full_output"] is not False:
        raise BudgetViolation(f"{_case_label(record)}: includes_prior_full_output is not false")

    frame = _closed_keys(record["harness_frame"], V2_HARNESS_FRAME_KEYS, "harness_frame", record)
    components = frame["components"]
    if not isinstance(components, list) or not components:
        raise BudgetViolation(f"{_case_label(record)}: harness_frame.components must be a non-empty list")
    component_names: list[str] = []
    component_bytes = 0
    for component in components:
        component = _closed_keys(component, frozenset({"name", "sha256", "bytes", "est_tok"}), "harness_frame component", record)
        name = component["name"]
        if not isinstance(name, str) or not name:
            raise BudgetViolation(f"{_case_label(record)}: harness frame component name must be non-empty")
        byte_count = component["bytes"]
        if not _is_int(byte_count) or byte_count < 0:
            raise BudgetViolation(f"{_case_label(record)}: harness frame component {name!r} has invalid bytes")
        if component["est_tok"] != byte_count // 4:
            raise BudgetViolation(f"{_case_label(record)}: harness frame component {name!r} token arithmetic mismatch")
        _validate_sha256(component["sha256"], f"harness frame component {name!r} SHA-256", record)
        component_names.append(name)
        component_bytes += byte_count
    if len(component_names) != len(set(component_names)):
        raise BudgetViolation(f"{_case_label(record)}: harness frame component names are not unique")
    if frame["total_bytes"] != component_bytes:
        raise BudgetViolation(f"{_case_label(record)}: harness frame component sum differs from total_bytes")
    if frame["total_est_tok"] != component_bytes // 4:
        raise BudgetViolation(f"{_case_label(record)}: harness frame total_est_tok arithmetic mismatch")
    if frame["total_est_tok"] > ceiling:
        raise BudgetViolation(
            f"{_case_label(record)}: harness frame total_est_tok {frame['total_est_tok']} exceeds ceiling {ceiling}"
        )

    runtime = _closed_keys(record["runtime_context"], V2_RUNTIME_CONTEXT_KEYS, "runtime_context", record)
    if runtime["component_scope"] != "resolver-selected-components":
        raise BudgetViolation(f"{_case_label(record)}: runtime context component_scope is not resolver-selected-components")
    for key in ("manifest_path", "prompt_path"):
        if not isinstance(runtime[key], str) or not runtime[key] or Path(runtime[key]).is_absolute():
            raise BudgetViolation(f"{_case_label(record)}: runtime_context.{key} must be a non-empty relative path")
    _validate_sha256(runtime["manifest_sha256"], "runtime_context.manifest_sha256", record)
    _validate_sha256(runtime["prompt_sha256"], "runtime_context.prompt_sha256", record)
    for key in ("prompt_byte_count", "selected_component_bytes", "effective_context_bytes", "effective_context_limit"):
        if not _is_int(runtime[key]) or runtime[key] < 1:
            raise BudgetViolation(f"{_case_label(record)}: runtime_context.{key} must be a positive integer")
    selected_rows = runtime["selected_components"]
    if not isinstance(selected_rows, list) or not selected_rows:
        raise BudgetViolation(f"{_case_label(record)}: runtime_context.selected_components must be non-empty")
    selected_ids: list[str] = []
    selected_bytes = 0
    for component in selected_rows:
        component = _closed_keys(component, V2_COMPONENT_KEYS, "selected component", record)
        component_id = component["component_id"]
        if not isinstance(component_id, str) or not component_id:
            raise BudgetViolation(f"{_case_label(record)}: selected component ID must be non-empty")
        _validate_sha256(component["sha256"], f"selected component {component_id!r} SHA-256", record)
        if not _is_int(component["byte_count"]) or component["byte_count"] < 1:
            raise BudgetViolation(f"{_case_label(record)}: selected component {component_id!r} byte_count is invalid")
        selected_ids.append(component_id)
        selected_bytes += component["byte_count"]
    if len(selected_ids) != len(set(selected_ids)):
        raise BudgetViolation(f"{_case_label(record)}: selected component IDs are not unique")
    if runtime["selected_component_bytes"] != selected_bytes:
        raise BudgetViolation(f"{_case_label(record)}: selected component byte sum differs from selected_component_bytes")
    if runtime["prompt_byte_count"] != runtime["effective_context_bytes"]:
        raise BudgetViolation(f"{_case_label(record)}: final prompt bytes differ from effective_context_bytes")
    if runtime["effective_context_bytes"] > runtime["effective_context_limit"]:
        raise BudgetViolation(f"{_case_label(record)}: effective context bytes exceed explicit byte limit")
    if artifact_root is None:
        raise BudgetViolation(f"{_case_label(record)}: prompt-pack-v2 validation requires an artifact root")
    _validate_v2_artifact_bindings(record, runtime, artifact_root)


def validate_record(record: dict[str, Any], ceiling: int, *, artifact_root: Path | None = None) -> None:
    if not isinstance(record, dict):
        raise BudgetViolation("manifest line is not a JSON object")

    if record.get("schema") == SCHEMA_V2:
        _validate_v2_record(record, ceiling, artifact_root)
        return

    if record.get("schema") != SCHEMA:
        raise BudgetViolation(
            f"{_case_label(record)}: schema mismatch (expected {SCHEMA!r}, got {record.get('schema')!r})"
        )

    missing = [key for key in REQUIRED_KEYS if key not in record]
    if missing:
        raise BudgetViolation(f"{_case_label(record)}: missing required key(s): {', '.join(missing)}")

    components = record["components"]
    if not isinstance(components, list) or not components:
        raise BudgetViolation(f"{_case_label(record)}: components must be a non-empty list")

    components_bytes_sum = 0
    for component in components:
        if not isinstance(component, dict) or "name" not in component or "bytes" not in component or "est_tok" not in component:
            raise BudgetViolation(f"{_case_label(record)}: malformed component entry: {component!r}")
        comp_bytes = component["bytes"]
        comp_tok = component["est_tok"]
        if not isinstance(comp_bytes, int) or comp_bytes < 0:
            raise BudgetViolation(f"{_case_label(record)}: component {component.get('name')!r} has invalid bytes {comp_bytes!r}")
        if comp_tok != comp_bytes // 4:
            raise BudgetViolation(
                f"{_case_label(record)}: component {component.get('name')!r} est_tok {comp_tok} != bytes//4 ({comp_bytes // 4})"
            )
        components_bytes_sum += comp_bytes

    total_bytes = record["total_bytes"]
    if not isinstance(total_bytes, int) or total_bytes < 0:
        raise BudgetViolation(f"{_case_label(record)}: total_bytes is not a non-negative int: {total_bytes!r}")
    if components_bytes_sum != total_bytes:
        raise BudgetViolation(
            f"{_case_label(record)}: components sum {components_bytes_sum} != total_bytes {total_bytes}"
        )

    total_est_tok = record["total_est_tok"]
    if total_est_tok != total_bytes // 4:
        raise BudgetViolation(
            f"{_case_label(record)}: total_est_tok {total_est_tok} != total_bytes//4 ({total_bytes // 4})"
        )

    if record["includes_full_runtime"] is not False:
        raise BudgetViolation(f"{_case_label(record)}: includes_full_runtime is not false")

    if record["includes_prior_full_output"] is not False:
        raise BudgetViolation(f"{_case_label(record)}: includes_prior_full_output is not false")

    if total_est_tok > ceiling:
        raise BudgetViolation(
            f"{_case_label(record)}: total_est_tok {total_est_tok} exceeds ceiling {ceiling}"
        )


def check_manifest_file(path: Path, ceiling: int) -> int:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        print(f"ERROR: cannot read {path}: {exc}")
        return 1

    checked = 0
    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"prompt pack budget check: FAIL ({path}:{lineno}: invalid JSON: {exc})")
            return 1
        try:
            validate_record(record, ceiling, artifact_root=path.parent)
        except BudgetViolation as exc:
            print(f"prompt pack budget check: FAIL ({path}:{lineno}: {exc})")
            return 1
        checked += 1

    print(f"prompt pack budget check: PASS ({checked} manifest line(s) checked, ceiling={ceiling})")
    return 0


def build_prompt_pack_manifest_v2(
    *,
    artifact_root: Path,
    runtime_context_manifest_path: Path,
    prompt_path: Path,
    harness_frame_parts: dict[str, str | bytes],
    includes_full_runtime: bool,
    includes_prior_full_output: bool,
) -> dict[str, Any]:
    """Build a fail-closed v2 record from already-written A12 call artifacts.

    The 20k token ceiling applies only to ``harness_frame_parts``. Resolver-
    selected component bytes remain separately visible and are bound to the
    final prompt and runtime-context sidecar; their size never implies the
    semantic ``includes_full_runtime`` flag.
    """
    root = artifact_root.resolve()
    context_path = _path_under_root(root, runtime_context_manifest_path, "runtime context manifest path")
    final_prompt_path = _path_under_root(root, prompt_path, "final prompt path")
    try:
        context_bytes = context_path.read_bytes()
        final_prompt_bytes = final_prompt_path.read_bytes()
    except OSError as exc:
        raise BudgetViolation(f"cannot read v2 prompt-pack artifact: {exc}") from exc
    try:
        context = json.loads(context_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BudgetViolation("runtime context manifest is not valid UTF-8 JSON") from exc
    if not isinstance(context, dict) or context.get("schema") != "daee-runtime-call-context-v1":
        raise BudgetViolation("runtime context manifest schema mismatch")
    record_label = {
        "case_id": context.get("case_id"),
        "stage": context.get("stage"),
        "call_index": context.get("call_index"),
    }
    selected_rows = _selected_component_rows(context, record_label)
    try:
        telemetry = context["budget_telemetry"]
    except (KeyError, TypeError) as exc:
        raise BudgetViolation(f"{_case_label(record_label)}: runtime context lacks budget telemetry") from exc
    if not isinstance(telemetry, dict):
        raise BudgetViolation(f"{_case_label(record_label)}: runtime context budget telemetry is malformed")
    frame_components: list[dict[str, Any]] = []
    frame_total = 0
    if not isinstance(harness_frame_parts, dict) or not harness_frame_parts:
        raise BudgetViolation(f"{_case_label(record_label)}: harness_frame_parts must be a non-empty mapping")
    for name, value in sorted(harness_frame_parts.items()):
        if not isinstance(name, str) or not name:
            raise BudgetViolation(f"{_case_label(record_label)}: harness frame part name must be non-empty")
        if isinstance(value, str):
            data = value.encode("utf-8")
        elif isinstance(value, bytes):
            data = value
        else:
            raise BudgetViolation(f"{_case_label(record_label)}: harness frame part {name!r} is not str/bytes")
        byte_count = len(data)
        frame_components.append(
            {
                "name": name,
                "sha256": _sha256_bytes(data),
                "bytes": byte_count,
                "est_tok": byte_count // 4,
            }
        )
        frame_total += byte_count
    try:
        relative_context = context_path.relative_to(root).as_posix()
        relative_prompt = final_prompt_path.relative_to(root).as_posix()
    except ValueError as exc:  # Defensive: _path_under_root already proves this.
        raise BudgetViolation("v2 prompt-pack artifact escapes artifact root") from exc
    record: dict[str, Any] = {
        "schema": SCHEMA_V2,
        "case_id": context.get("case_id"),
        "stage": context.get("stage"),
        "call_index": context.get("call_index"),
        "harness_frame": {
            "components": frame_components,
            "total_bytes": frame_total,
            "total_est_tok": frame_total // 4,
        },
        "runtime_context": {
            "component_scope": "resolver-selected-components",
            "manifest_path": relative_context,
            "manifest_sha256": _sha256_bytes(context_bytes),
            "prompt_path": relative_prompt,
            "prompt_sha256": _sha256_bytes(final_prompt_bytes),
            "prompt_byte_count": len(final_prompt_bytes),
            "selected_components": selected_rows,
            "selected_component_bytes": sum(row["byte_count"] for row in selected_rows),
            "effective_context_bytes": telemetry.get("effective_context_bytes"),
            "effective_context_limit": telemetry.get("effective_context_limit"),
        },
        "includes_full_runtime": includes_full_runtime,
        "includes_prior_full_output": includes_prior_full_output,
    }
    validate_record(record, DEFAULT_CEILING, artifact_root=root)
    return record


def emit_prompt_pack_manifest_v2(
    *,
    manifest_path: Path,
    artifact_root: Path,
    runtime_context_manifest_path: Path,
    prompt_path: Path,
    harness_frame_parts: dict[str, str | bytes],
    includes_full_runtime: bool,
    includes_prior_full_output: bool,
) -> dict[str, Any]:
    """Append one validated v2 record; any binding/budget failure aborts emission."""
    root = artifact_root.resolve()
    output_path = _path_under_root(root, manifest_path, "prompt-pack manifest path")
    record = build_prompt_pack_manifest_v2(
        artifact_root=root,
        runtime_context_manifest_path=runtime_context_manifest_path,
        prompt_path=prompt_path,
        harness_frame_parts=harness_frame_parts,
        includes_full_runtime=includes_full_runtime,
        includes_prior_full_output=includes_prior_full_output,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


# --- self-test fixtures (no filesystem dependency) --------------------------


def _fixture_record(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema": SCHEMA,
        "case_id": "self-test-case",
        "stage": "stage-01",
        "call_index": 1,
        "components": [
            {"name": "raw_input_text", "bytes": 40, "est_tok": 10},
            {"name": "previous_stages_json", "bytes": 20, "est_tok": 5},
            {"name": "frame_and_residual", "bytes": 140, "est_tok": 35},
        ],
        "total_bytes": 200,
        "total_est_tok": 50,
        "includes_full_runtime": False,
        "includes_prior_full_output": False,
    }
    base.update(overrides)
    return base


def _run_self_test_case(
    label: str,
    record: dict[str, Any],
    ceiling: int,
    expect_pass: bool,
    *,
    artifact_root: Path | None = None,
) -> bool:
    try:
        validate_record(record, ceiling, artifact_root=artifact_root)
        passed = True
        reason = ""
    except BudgetViolation as exc:
        passed = False
        reason = str(exc)
    ok = passed == expect_pass
    status = "PASS" if ok else "FAIL"
    detail = "" if not reason else f" ({reason})"
    print(f"[{status}] {label}: expected {'pass' if expect_pass else 'fail'}, got {'pass' if passed else 'fail'}{detail}")
    return ok


def _write_v2_fixture(root: Path, *, runtime_bytes: int = 160_001, effective_limit_delta: int = 1_000) -> tuple[Path, Path]:
    component_bytes = b"R" * runtime_bytes
    component_sha256 = hashlib.sha256(component_bytes).hexdigest()
    harness_bytes = b"bounded harness frame"
    harness_sha256 = hashlib.sha256(harness_bytes).hexdigest()
    header = f"----- BEGIN DAEE COMPONENT: package:SKILL.md; sha256={component_sha256} -----\n".encode()
    footer = b"\n----- END DAEE COMPONENT: package:SKILL.md -----\n"
    harness_header = f"----- BEGIN DAEE COMPONENT: harness:stage-prompt; sha256={harness_sha256} -----\n".encode()
    harness_footer = b"\n----- END DAEE COMPONENT: harness:stage-prompt -----\n"
    prompt = b"DAEE transport frame\n" + header + component_bytes + footer + harness_header + harness_bytes + harness_footer
    prompt_path = root / "call-001-stage-01" / "prompt.md"
    prompt_path.parent.mkdir(parents=True)
    prompt_path.write_bytes(prompt)
    context = {
        "schema": "daee-runtime-call-context-v1",
        "case_id": "self-test-case",
        "stage": "01",
        "call_index": 1,
        "selection": {"status": "selected", "selected_components": ["package:SKILL.md"]},
        "components": [
            {
                "component_id": "package:SKILL.md",
                "kind": "kernel",
                "source_path": "SKILL.md",
                "sha256": component_sha256,
                "byte_count": len(component_bytes),
            },
            {
                "component_id": "harness:stage-prompt",
                "kind": "harness-supplement",
                "source_path": "run://harness-stage-prompt.md",
                "sha256": harness_sha256,
                "byte_count": len(harness_bytes),
            },
        ],
        "prompt": {
            "path": "prompt.md",
            "sha256": hashlib.sha256(prompt).hexdigest(),
            "byte_count": len(prompt),
            "includes_full_runtime": False,
            "includes_prior_full_output": False,
        },
        "budget_telemetry": {
            "effective_context_bytes": len(prompt),
            "effective_context_limit": len(prompt) + effective_limit_delta,
            "selected_component_count": 1,
        },
    }
    context_path = prompt_path.parent / "context.json"
    context_path.write_text(json.dumps(context, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return context_path, prompt_path


def _run_v2_self_tests() -> list[bool]:
    results: list[bool] = []
    with tempfile.TemporaryDirectory(prefix="daee-prompt-pack-v2-") as tmp:
        root = Path(tmp)
        context_path, prompt_path = _write_v2_fixture(root)
        build_args = {
            "artifact_root": root,
            "runtime_context_manifest_path": context_path,
            "prompt_path": prompt_path,
            "harness_frame_parts": {"harness:stage-prompt": b"bounded harness frame"},
            "includes_full_runtime": False,
            "includes_prior_full_output": False,
        }
        record = build_prompt_pack_manifest_v2(**build_args)
        results.append(
            _run_self_test_case(
                "v2 large selected kernel is separately measured without whole-runtime inference",
                record,
                DEFAULT_CEILING,
                expect_pass=True,
                artifact_root=root,
            )
        )
        results.append(record["harness_frame"]["total_bytes"] == len(b"bounded harness frame"))
        results.append(record["runtime_context"]["selected_component_bytes"] == 160_001)
        try:
            build_prompt_pack_manifest_v2(
                **(build_args | {"harness_frame_parts": {"harness:stage-prompt": b"underreported"}})
            )
            caught_harness_drift = False
        except BudgetViolation as exc:
            caught_harness_drift = "harness frame identity/hash/byte binding" in str(exc)
        results.append(caught_harness_drift)
        try:
            validate_record(record, DEFAULT_CEILING)
            caught_missing_artifact_root = False
        except BudgetViolation as exc:
            caught_missing_artifact_root = "requires an artifact root" in str(exc)
        results.append(caught_missing_artifact_root)

        selected_drift = json.loads(json.dumps(record))
        selected_drift["runtime_context"]["selected_components"][0]["sha256"] = "f" * 64
        results.append(
            _run_self_test_case(
                "v2 selected component hash drift fails",
                selected_drift,
                DEFAULT_CEILING,
                expect_pass=False,
                artifact_root=root,
            )
        )

        over_harness = json.loads(json.dumps(record))
        over_harness["harness_frame"] = {
            "components": [{"name": "harness:stage-prompt", "sha256": "f" * 64, "bytes": 80_004, "est_tok": 20_001}],
            "total_bytes": 80_004,
            "total_est_tok": 20_001,
        }
        results.append(
            _run_self_test_case(
                "v2 harness frame remains subject to unchanged token ceiling",
                over_harness,
                DEFAULT_CEILING,
                expect_pass=False,
                artifact_root=root,
            )
        )

        whole_runtime = json.loads(json.dumps(record))
        whole_runtime["includes_full_runtime"] = True
        results.append(
            _run_self_test_case(
                "v2 explicit whole-runtime replay fails",
                whole_runtime,
                DEFAULT_CEILING,
                expect_pass=False,
                artifact_root=root,
            )
        )

        prior_output = json.loads(json.dumps(record))
        prior_output["includes_prior_full_output"] = True
        results.append(
            _run_self_test_case(
                "v2 prior full output replay fails",
                prior_output,
                DEFAULT_CEILING,
                expect_pass=False,
                artifact_root=root,
            )
        )

        over_effective = json.loads(json.dumps(record))
        over_effective["runtime_context"]["effective_context_limit"] = 1
        results.append(
            _run_self_test_case(
                "v2 effective context over explicit byte limit fails",
                over_effective,
                DEFAULT_CEILING,
                expect_pass=False,
                artifact_root=root,
            )
        )

        manifest_path = root / "prompt-pack-manifest.jsonl"
        emitted = emit_prompt_pack_manifest_v2(manifest_path=manifest_path, **build_args)
        results.append(emitted == record and check_manifest_file(manifest_path, DEFAULT_CEILING) == 0)

        context_path.write_text(context_path.read_text(encoding="utf-8") + " ", encoding="utf-8", newline="\n")
        try:
            validate_record(record, DEFAULT_CEILING, artifact_root=root)
            caught_context_drift = False
        except BudgetViolation as exc:
            caught_context_drift = "runtime context manifest SHA-256 mismatch" in str(exc)
        results.append(caught_context_drift)

        context_path.write_bytes(context_path.read_bytes()[:-1])
        prompt_path.write_bytes(prompt_path.read_bytes() + b"tamper")
        try:
            validate_record(record, DEFAULT_CEILING, artifact_root=root)
            caught_prompt_drift = False
        except BudgetViolation as exc:
            caught_prompt_drift = "final prompt SHA-256 mismatch" in str(exc)
        results.append(caught_prompt_drift)

    for index, passed in enumerate(results, start=1):
        if index in {2, 3, 4, 10, 11, 12}:
            print(f"[{'PASS' if passed else 'FAIL'}] v2 direct expectation {index}")
    return results


# --- FIX 6: static call-site parity (structural instrumentation coverage) --
#
# The manifest checker above only ever sees synthetic fixtures or whatever
# manifest lines a real run happened to produce; it has no way to notice a
# NEW invoke_model() call site in tools/run_staged_current_skill_smoke.py
# that was never wired up to emit_prompt_pack_manifest(). This performs a
# cheap, purely textual structural check on that file's source instead, as a
# floor guarantee that every model-invocation call site has a paired
# manifest-emission call site.
#
# Method (documented per FIX 6's requirement): count line-start-anchored
# occurrences of "invoke_model(" and "emit_prompt_pack_manifest(" via a
# regex that requires the match to begin a logical call expression -- i.e.
# preceded only by leading whitespace, an assignment target, "return ", or
# the start of an expression statement, NEVER preceded by "def " (which
# would match the function's own definition line) and never occurring
# inside a quoted string literal starting at that same position (approximated
# by requiring the token NOT be immediately preceded by a quote character,
# which is sufficient to exclude the common "quoted example" case without a
# full tokenizer; this is a deliberately cheap heuristic, not a parser).
_CALL_SITE_RE_TEMPLATE = r"(?<!def )(?<!['\"])\b{name}\("


def _count_call_sites(source: str, function_name: str) -> int:
    pattern = re.compile(_CALL_SITE_RE_TEMPLATE.format(name=re.escape(function_name)))
    return len(pattern.findall(source))


def check_call_site_parity(smoke_harness_path: Path) -> tuple[bool, str]:
    """Return (ok, message) for the invoke_model / emit_prompt_pack_manifest parity check.

    Every model invocation (invoke_model call site) must have a paired
    manifest emission (emit_prompt_pack_manifest call site): the count of
    emit_prompt_pack_manifest call sites must be >= the count of invoke_model
    call sites. A mismatch means a new (or newly discovered) invoke_model
    call site was added without instrumenting it -- the fix is to add the
    missing emit_prompt_pack_manifest() call at that site, not to loosen this
    check.
    """
    try:
        source = smoke_harness_path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"cannot read {smoke_harness_path}: {exc}"

    invoke_model_count = _count_call_sites(source, "invoke_model")
    emit_manifest_count = _count_call_sites(source, "emit_prompt_pack_manifest")

    if emit_manifest_count < invoke_model_count:
        return False, (
            f"call-site parity FAIL: {invoke_model_count} invoke_model( call site(s) but only "
            f"{emit_manifest_count} emit_prompt_pack_manifest( call site(s)) in {smoke_harness_path}. "
            "Every model invocation must be paired with a manifest emission -- instrument the new "
            "invoke_model( call site with an emit_prompt_pack_manifest(...) call immediately before it."
        )

    return True, (
        f"call-site parity OK: {emit_manifest_count} emit_prompt_pack_manifest( call site(s) >= "
        f"{invoke_model_count} invoke_model( call site(s)) in {smoke_harness_path}"
    )


def run_self_test() -> int:
    results = []

    valid = _fixture_record()
    results.append(_run_self_test_case("valid manifest line passes", valid, DEFAULT_CEILING, expect_pass=True))

    full_runtime = _fixture_record(includes_full_runtime=True)
    results.append(
        _run_self_test_case("includes_full_runtime=true fails", full_runtime, DEFAULT_CEILING, expect_pass=False)
    )

    prior_output = _fixture_record(includes_prior_full_output=True)
    results.append(
        _run_self_test_case(
            "includes_prior_full_output=true fails", prior_output, DEFAULT_CEILING, expect_pass=False
        )
    )

    sum_mismatch = _fixture_record(total_bytes=999)
    results.append(_run_self_test_case("component sum mismatch fails", sum_mismatch, DEFAULT_CEILING, expect_pass=False))

    over_ceiling = _fixture_record(
        components=[
            {"name": "raw_input_text", "bytes": 400_000, "est_tok": 100_000},
            {"name": "frame_and_residual", "bytes": 0, "est_tok": 0},
        ],
        total_bytes=400_000,
        total_est_tok=100_000,
    )
    results.append(_run_self_test_case("over-ceiling total_est_tok fails", over_ceiling, DEFAULT_CEILING, expect_pass=False))

    parity_ok, parity_message = check_call_site_parity(SMOKE_HARNESS_PATH)
    status = "PASS" if parity_ok else "FAIL"
    print(f"[{status}] invoke_model / emit_prompt_pack_manifest call-site parity: {parity_message}")
    results.append(parity_ok)

    results.extend(_run_v2_self_tests())

    if all(results):
        print(f"check_prompt_pack_budget self-test: PASS ({len(results)}/{len(results)} expectations met)")
        return 0
    print(f"check_prompt_pack_budget self-test: FAIL ({sum(results)}/{len(results)} expectations met)")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="Path to a prompt-pack-manifest.jsonl file to validate.")
    parser.add_argument(
        "--ceiling",
        type=int,
        default=DEFAULT_CEILING,
        help="Max v1 total_est_tok or v2 harness_frame.total_est_tok per line.",
    )
    parser.add_argument("--self-test", action="store_true", help="Run built-in fixture-based expectations.")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    if args.manifest is None:
        parser.error("--manifest is required unless --self-test is used")

    if not args.manifest.exists():
        print(f"ERROR: manifest not found: {args.manifest}")
        return 1

    return check_manifest_file(args.manifest, args.ceiling)


if __name__ == "__main__":
    raise SystemExit(main())
