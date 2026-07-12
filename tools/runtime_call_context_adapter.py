#!/usr/bin/env python3
"""Fail-closed Stage01/02 adapter for validated DAEE runtime call context.

The adapter prepares exact model-visible prompt bytes, validates the A12
runtime-context record, then validates the A13 package/harness parity record.
It performs no model invocation and returns only after both checks pass.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from check_package_harness_parity import (
    Failure as PackageParityFailure,
    tree_sha,
    validate as validate_package_parity,
)
from check_producer_checker_parity import DEFAULT_REGISTRY, validate_registry
from check_runtime_context_delivery import (
    Failure as RuntimeContextFailure,
    validate as validate_runtime_context,
)
from check_state_capsule import capsule_size_errors, validate_capsule_payload_dispatch
from package_shape import (
    CANONICAL_REQUIRED_ROOT_ENTRIES,
    expected_package_files,
    package_file_paths,
)
from runtime_context_resolver import ResolutionError, resolve_context, sha256_bytes


SUPPORTED_STAGES = {"01", "02"}
HARNESSED_COMPONENT_ID = "harness:stage-prompt"
EMPTY_VALIDATED_STATE = {
    "route_shards": [],
    "owner_module_ids": [],
    "cold_clause_ids": [],
    "live_pressure": False,
    "ambiguous": False,
}
_HEX40 = re.compile(r"^[0-9a-f]{40}$")


class RuntimeCallPreparationError(ValueError):
    """A deterministic pre-dispatch preparation or validation failure."""

    def __init__(self, phase: str, detail: str):
        super().__init__(f"{phase}: {detail}")
        self.phase = phase
        self.detail = detail


@dataclass(frozen=True)
class PreparedRuntimeCall:
    prompt: str
    call_root: Path
    prompt_path: Path
    context_path: Path
    parity_path: Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def validate_execution_mini_package(package_root: Path) -> None:
    """Reject a mislabeled dev tree or any non-manifest execution-mini byte."""
    try:
        root = package_root.resolve(strict=True)
        manifest = json.loads((root / "build-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeCallPreparationError("package", f"execution-mini manifest is unavailable or invalid: {exc}") from exc
    expected, errors = expected_package_files(root, manifest)
    if errors:
        raise RuntimeCallPreparationError("package", f"execution-mini manifest is invalid: {errors[0]}")
    actual_roots = {path.name for path in root.iterdir()}
    if actual_roots != CANONICAL_REQUIRED_ROOT_ENTRIES:
        raise RuntimeCallPreparationError(
            "package",
            "execution-mini root entries differ: "
            f"missing={sorted(CANONICAL_REQUIRED_ROOT_ENTRIES - actual_roots)} "
            f"extra={sorted(actual_roots - CANONICAL_REQUIRED_ROOT_ENTRIES)}",
        )
    if any(path.is_symlink() for path in root.rglob("*")):
        raise RuntimeCallPreparationError("package", "execution-mini contains a symbolic link")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise RuntimeCallPreparationError(
            "package",
            "execution-mini file inventory differs: "
            f"missing={sorted(expected - actual)[:5]} extra={sorted(actual - expected)[:5]}",
        )


def materialize_execution_mini_package(repo_root: Path, destination: Path) -> Path:
    """Copy the manifest-owned execution-mini files into one fresh tree."""
    repo_root = repo_root.resolve(strict=True)
    if destination.exists():
        raise RuntimeCallPreparationError("package", f"execution-mini destination already exists: {destination}")
    paths, errors = package_file_paths(repo_root)
    if errors:
        raise RuntimeCallPreparationError("package", f"cannot materialize execution-mini: {errors[0]}")
    source_root = repo_root / "skill"
    destination.mkdir(parents=True)
    for source in paths:
        relative = source.relative_to(source_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    validate_execution_mini_package(destination)
    return destination.resolve(strict=True)


def _artifact(kind: str, scope: str, path: str, root: Path) -> dict[str, Any]:
    artifact_path = root / path
    return {
        "kind": kind,
        "scope": scope,
        "path": path,
        "sha256": _sha(artifact_path),
        "byte_count": artifact_path.stat().st_size,
    }


def _validated_capsule_bytes(
    path: Path,
    *,
    run_dir: Path,
    case_id: str,
    input_digest: str,
) -> tuple[bytes, str]:
    try:
        resolved = path.resolve(strict=True)
        capsule_root = (run_dir / "state-capsules").resolve(strict=True)
        resolved.relative_to(capsule_root)
        raw = resolved.read_bytes()
    except ValueError as exc:
        raise RuntimeCallPreparationError("state-capsule", "previous capsule is outside this run") from exc
    except OSError as exc:
        raise RuntimeCallPreparationError("state-capsule", f"previous capsule is unavailable: {path}: {exc}") from exc
    if resolved.parent != capsule_root or resolved.name != "capsule-001.json":
        raise RuntimeCallPreparationError("state-capsule", "previous capsule is not the immediate Stage01 capsule")
    canonical_capsules = sorted(
        candidate.resolve()
        for candidate in capsule_root.glob("capsule-*.json")
        if not candidate.name.endswith(".invalid.json")
    )
    if canonical_capsules != [resolved]:
        raise RuntimeCallPreparationError("state-capsule", "same-run capsule sequence is not the exact immediate predecessor")
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeCallPreparationError("state-capsule", f"previous capsule is not valid UTF-8 JSON: {exc}") from exc
    identity = str(payload.get("schema")) if isinstance(payload, dict) else "unknown"
    if identity == "daee-state-capsule-v2":
        raise RuntimeCallPreparationError(
            "state-capsule",
            "state-capsule-v2 transport is unsupported until the A16 owner integration",
        )
    if identity != "daee-state-capsule-v1":
        raise RuntimeCallPreparationError("state-capsule", f"unsupported previous capsule schema: {identity}")
    expected_fingerprint = f"sha256:{input_digest}"
    if payload.get("stage") != "01":
        raise RuntimeCallPreparationError("state-capsule", "previous capsule does not record Stage01")
    if payload.get("case_id") != case_id:
        raise RuntimeCallPreparationError("state-capsule", "previous capsule case_id differs from this call")
    if payload.get("input_fingerprint") != expected_fingerprint:
        raise RuntimeCallPreparationError("state-capsule", "previous capsule input fingerprint differs from this call")
    errors = validate_capsule_payload_dispatch(str(path), payload, release_bearing=False)
    _warnings, size_failures = capsule_size_errors(str(path), raw)
    errors.extend(size_failures)
    if errors:
        raise RuntimeCallPreparationError("state-capsule", f"previous capsule failed validation: {errors[0]}")
    return raw, identity


def _render_prompt(
    resolution: dict[str, Any],
    harness_prompt: bytes,
) -> tuple[bytes, list[dict[str, Any]], int]:
    parts: list[bytes] = [b"DAEE validated runtime call context\n"]
    components: list[dict[str, Any]] = []
    framing_bytes = len(parts[0])

    raw_components = list(resolution["components"])
    raw_components.append(
        {
            "component_id": HARNESSED_COMPONENT_ID,
            "kind": "harness-supplement",
            "source_path": "run://harness-stage-prompt.md",
            "source_slice": {"kind": "whole-file", "start": 0, "end": 0},
            "sha256": sha256_bytes(harness_prompt),
            "byte_count": len(harness_prompt),
            "bytes": harness_prompt,
        }
    )
    for raw in raw_components:
        data = raw["bytes"]
        header = (
            f"----- BEGIN DAEE COMPONENT: {raw['component_id']}; "
            f"sha256={raw['sha256']} -----\n"
        ).encode("utf-8")
        footer = f"\n----- END DAEE COMPONENT: {raw['component_id']} -----".encode("utf-8")
        start = sum(len(part) for part in parts) + len(header)
        end = start + len(data)
        parts.extend([header, data, footer, b"\n"])
        framing_bytes += len(header) + len(footer) + 1
        source_path = {
            "transport://raw-input": "run://raw-input.bin",
            "transport://previous-capsule": "run://previous-capsule.json",
        }.get(raw["source_path"], raw["source_path"])
        components.append(
            {key: value for key, value in raw.items() if key != "bytes"}
            | {
                "source_path": source_path,
                "delivery": "prompt-bound",
                "prompt_start_byte": start,
                "prompt_end_byte": end,
            }
        )
    return b"".join(parts), components, framing_bytes


def _model_visible_clause_ids(context_components: list[dict[str, Any]]) -> list[str]:
    registry = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    validate_registry(registry)
    visible_components = {row["component_id"] for row in context_components}
    return [
        row["clause_id"]
        for row in registry["clauses"]
        if row.get("class") == "canonical_semantic_law"
        and any(
            projection.get("component_id") in visible_components
            for projection in [row.get("delivery_projection", {}), *row.get("alternate_delivery_projections", [])]
        )
    ]


def prepare_runtime_call(
    *,
    package_root: Path,
    repo_root: Path,
    run_dir: Path,
    call_index: int,
    case_id: str,
    stage: str,
    raw_input_path: Path,
    previous_capsule_path: Path | None,
    harness_prompt: str,
    validated_state: dict[str, Any] | None,
    source_commit: str,
    effective_context_limit: int,
    candidate_cap: int = 4,
) -> PreparedRuntimeCall:
    """Prepare and validate one supported call before any model dispatch.

    Stage02 accepts a structurally/semantically validated v1 capsule only as
    historical transport compatibility.  This does not promote it to v2 or
    release-bearing evidence.
    """
    if stage not in SUPPORTED_STAGES:
        raise RuntimeCallPreparationError("stage", f"unsupported adapter stage: {stage}")
    if not isinstance(call_index, int) or call_index < 1:
        raise RuntimeCallPreparationError("call", "call_index must be a positive integer")
    if not _HEX40.fullmatch(source_commit):
        raise RuntimeCallPreparationError("runtime", "source_commit must be exact lowercase 40-hex")
    if not isinstance(effective_context_limit, int) or effective_context_limit < 1:
        raise RuntimeCallPreparationError("budget", "effective_context_limit must be a positive integer")
    if not harness_prompt:
        raise RuntimeCallPreparationError("prompt", "harness prompt must not be empty")
    if validated_state is None:
        validated_state = dict(EMPTY_VALIDATED_STATE)

    package_root = package_root.resolve(strict=True)
    validate_execution_mini_package(package_root)
    repo_root = repo_root.resolve(strict=True)
    run_dir = run_dir.resolve(strict=True)
    raw_input = raw_input_path.resolve(strict=True).read_bytes()
    if not raw_input:
        raise RuntimeCallPreparationError("input", "raw input must not be empty")

    capsule_bytes: bytes | None = None
    capsule_identity: str | None = None
    if stage == "01":
        if previous_capsule_path is not None:
            raise RuntimeCallPreparationError("state-capsule", "Stage01 must not receive a previous capsule")
    else:
        if previous_capsule_path is None:
            raise RuntimeCallPreparationError("state-capsule", "Stage02 requires the previous capsule")
        capsule_bytes, capsule_identity = _validated_capsule_bytes(
            previous_capsule_path,
            run_dir=run_dir,
            case_id=case_id,
            input_digest=sha256_bytes(raw_input),
        )

    call_root = run_dir / "runtime-calls" / f"call-{call_index:03d}-stage-{stage}"
    if call_root.exists():
        raise RuntimeCallPreparationError("call", f"runtime call root already exists: {call_root}")
    call_root.mkdir(parents=True)
    (call_root / "raw-input.bin").write_bytes(raw_input)
    harness_bytes = harness_prompt.encode("utf-8")
    (call_root / "harness-stage-prompt.md").write_bytes(harness_bytes)
    if capsule_bytes is not None:
        (call_root / "previous-capsule.json").write_bytes(capsule_bytes)

    try:
        resolution = resolve_context(
            package_root,
            stage,
            validated_state,
            capsule_bytes,
            candidate_cap,
            raw_input if stage == "01" else None,
        )
    except ResolutionError as exc:
        raise RuntimeCallPreparationError("resolver", str(exc)) from exc
    if resolution["status"] != "selected":
        raise RuntimeCallPreparationError(
            "resolver",
            f"runtime context did not select: {resolution['status']}/{resolution['hold_reason']}",
        )

    prompt_bytes, components, framing_bytes = _render_prompt(resolution, harness_bytes)
    prompt_path = call_root / "prompt.md"
    prompt_path.write_bytes(prompt_bytes)
    context_path = call_root / "context.json"
    parity_path = call_root / "package-harness-parity.json"

    runtime_component_bytes = sum(
        row["byte_count"]
        for row in components
        if row["kind"] not in {"raw-input", "state-capsule", "harness-supplement", "local-excerpt"}
    )
    non_claims = [
        "delivery does not prove internal model attention or semantic truth",
        "development package custody is not candidate maturity or release readiness",
    ]
    if capsule_identity == "daee-state-capsule-v1":
        non_claims.append("historical-v1 capsule compatibility is A12 transport only and is not v2 promotion")

    context: dict[str, Any] = {
        "schema": "daee-runtime-call-context-v1",
        "case_id": case_id,
        "stage": stage,
        "call_index": call_index,
        "runtime": {
            "delivery_mode": "explicit-prompt-components",
            "evidence_lane": "harness-assisted",
            "package_profile": "execution-mini",
            "package_sha256": tree_sha(package_root),
            "build_manifest_sha256": _sha(package_root / "build-manifest.json"),
            "skill_root_sha256": _sha(package_root / "SKILL.md"),
            "source_commit": source_commit,
        },
        "input": {
            "path": "raw-input.bin",
            "sha256": sha256_bytes(raw_input),
            "byte_count": len(raw_input),
            "included": stage == "01" or raw_input in harness_bytes,
        },
        "state_capsule": {
            "bootstrap": stage == "01",
            "path": None if capsule_bytes is None else "previous-capsule.json",
            "sha256": None if capsule_bytes is None else sha256_bytes(capsule_bytes),
            "included": capsule_bytes is not None,
            "validated": capsule_bytes is not None,
        },
        "validated_state": validated_state,
        "selection": {
            "basis_kind": "stage-policy",
            "basis_ids": [f"runtime-stage-{stage}"],
            "candidate_components": list(resolution["candidate_components"]),
            "selected_components": list(resolution["selected_components"]),
            "status": resolution["status"],
            "hold_reason": resolution["hold_reason"],
            "candidate_cap": candidate_cap,
        },
        "components": components,
        "cold_law_clauses_delivered": sorted(
            row["component_id"] for row in components if row["kind"] == "cold-law-clause"
        ),
        "producer_declared_used": [],
        "operation_bound_components": [],
        "prompt": {
            "path": "prompt.md",
            "sha256": sha256_bytes(prompt_bytes),
            "byte_count": len(prompt_bytes),
            "includes_full_runtime": False,
            "includes_prior_full_output": False,
        },
        "delivery_status": "DELIVERED",
        "usage_status": "NOT_DECLARED",
        "proof_mode": "harness-assisted",
        "host_receipt": None,
        "budget_telemetry": {
            "transport_frame_bytes": framing_bytes,
            "runtime_component_bytes": runtime_component_bytes,
            "capsule_bytes": 0 if capsule_bytes is None else len(capsule_bytes),
            "local_excerpt_bytes": 0,
            "effective_context_bytes": len(prompt_bytes),
            "effective_context_limit": effective_context_limit,
            "selected_component_count": len(resolution["selected_components"]),
        },
        "non_claims": non_claims,
    }
    _write_json(context_path, context)
    try:
        validate_runtime_context(context, package_root, call_root)
    except RuntimeContextFailure as exc:
        raise RuntimeCallPreparationError(
            "A12",
            f"{exc.failure_class}/{exc.subcode}: {exc.detail}",
        ) from exc

    supplement = {
        "supplement_id": HARNESSED_COMPONENT_ID,
        "path": "harness-stage-prompt.md",
        "sha256": sha256_bytes(harness_bytes),
        "byte_count": len(harness_bytes),
        "semantic": True,
        "claimed_package_bound": False,
    }
    parity: dict[str, Any] = {
        "schema": "daee-package-harness-parity-v1",
        "classification": "harness-assisted",
        "package_profile": "execution-mini",
        "package_tree_sha256": context["runtime"]["package_sha256"],
        "producer_registry_sha256": _sha(DEFAULT_REGISTRY),
        "model_visible_clause_ids": _model_visible_clause_ids(components),
        "artifacts": [
            _artifact("skill-root", "package", "SKILL.md", package_root),
            _artifact("build-manifest", "package", "build-manifest.json", package_root),
            _artifact("cold-law-manifest", "package", "cold-law-manifest.json", package_root),
            _artifact("module-map", "package", "compiled-module-map.json", package_root),
            _artifact("call-context", "run", "context.json", call_root),
            _artifact("prompt", "run", "prompt.md", call_root),
            _artifact("checker", "repo", "tools/check_runtime_context_delivery.py", repo_root),
            _artifact("normalizer", "repo", "tools/runtime_context_resolver.py", repo_root),
        ],
        "harness_supplements": [supplement],
        "delivery_proof": "exact-component-binding",
        "semantic_repair_count": 0,
        "non_claims": [
            "harness assistance is enumerated and is not relabeled package law",
            "parity of exact bytes does not prove semantic correctness or release readiness",
        ],
    }
    _write_json(parity_path, parity)
    try:
        validate_package_parity(parity, package_root, call_root, repo_root)
    except PackageParityFailure as exc:
        raise RuntimeCallPreparationError("A13", f"{exc.cls}/{exc.subcode}: {exc.detail}") from exc

    try:
        prompt = prompt_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeCallPreparationError("prompt", f"selected context is not strict UTF-8: {exc}") from exc
    return PreparedRuntimeCall(
        prompt=prompt,
        call_root=call_root,
        prompt_path=prompt_path,
        context_path=context_path,
        parity_path=parity_path,
    )
