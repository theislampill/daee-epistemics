#!/usr/bin/env python3
"""Validate content-addressed DAEE call-context delivery without invoking models."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from runtime_context_resolver import ResolutionError, resolve_context, sha256_bytes  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "runtime-call-context.schema.json"
FIXTURES = ROOT / "tests" / "runtime-context-delivery"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TAINT_KEYS = {"case-id", "case_id", "topic", "case-name", "smoke-id", "prompt-topic"}

SUPPORTED_SCENARIO_FAILURES = {
    "prior-capsule-not-delivered", "selected-component-not-delivered", "stage-derived-delivery-claim",
    "component-hash-mismatch", "declared-use-not-delivered", "package-path-escape",
    "tainted-selection-basis", "unresolved-context-without-hold", "ambiguity-cap-without-hold",
    "prompt-hash-mismatch", "full-runtime-reinline", "context-budget-without-hold",
    "package-hash-mismatch", "unverifiable-host-receipt", "membership-is-not-delivery",
    "mandatory-stage-component-missing", "raw-input-not-delivered", "raw-input-hash-mismatch",
    "undeclared-prompt-envelope", "capsule-binding-mismatch", "cold-law-delivery-list-mismatch",
    "usage-evidence-mismatch", "schema-invalid",
}


class Failure(Exception):
    def __init__(self, failure_class: str, stage: str, subcode: str, detail: str):
        super().__init__(detail)
        self.failure_class, self.stage, self.subcode, self.detail = failure_class, stage, subcode, detail

    def diagnostic(self) -> dict[str, Any]:
        downstream = [f"{x:02d}" for x in range(int(self.stage) + 1, 9)] if self.stage.isdigit() else ["model-call", "promotion"]
        return {"checker_id": "runtime-context-delivery", "status": "fail", "exit_category": "structural-rejection", "exit_code": 1,
                "failure_class": self.failure_class, "failure_subcode": self.subcode, "earliest_stage": self.stage,
                "downstream_invalidated": downstream, "detail": self.detail, "message": self.detail}


A11_EXPECTATION_FIELDS = {
    "schema", "fixture", "kind", "expected_checker_id", "expected_exit_category", "expected_exit_code",
    "expected_earliest_stage", "expected_failure_class", "expected_failure_subcode",
    "expected_downstream_invalidated", "required_diagnostic_markers", "forbidden_artifacts", "provenance",
}


def validate_expectation_contract(expectation: dict[str, Any], checker_id: str, exit_code: int,
                                  diagnostic: dict[str, Any], artifact_root: Path, fixture_name: str | None = None) -> list[str]:
    """Mirror the canonical A11 right-reason assertion dialect for local fixtures."""
    errors: list[str] = []
    missing = sorted(A11_EXPECTATION_FIELDS - set(expectation))
    if missing: errors.append(f"missing expectation fields: {missing}")
    unknown = sorted(set(expectation) - A11_EXPECTATION_FIELDS)
    if unknown: errors.append(f"unknown expectation fields: {unknown}")
    if expectation.get("schema") != "daee-negative-fixture-expectation-v1": errors.append("wrong expectation schema")
    if expectation.get("kind") != "invalid-single-signature": errors.append("expectation is not active single-signature")
    if fixture_name is not None and expectation.get("fixture") != fixture_name: errors.append("expectation fixture does not match scenario")
    if not isinstance(expectation.get("provenance"), str) or not expectation.get("provenance", "").strip(): errors.append("expectation provenance is empty")
    comparisons = (
        (expectation.get("expected_checker_id"), checker_id, "checker ID"),
        (expectation.get("expected_exit_category"), diagnostic.get("exit_category"), "exit category"),
        (expectation.get("expected_exit_code"), exit_code, "exit code"),
        (str(expectation.get("expected_earliest_stage")), str(diagnostic.get("earliest_stage")), "earliest stage"),
        (expectation.get("expected_failure_class"), diagnostic.get("failure_class"), "failure class"),
        (expectation.get("expected_failure_subcode"), diagnostic.get("failure_subcode"), "failure subcode"),
    )
    for expected, actual, label in comparisons:
        if expected != actual: errors.append(f"{label}: expected {expected!r}, got {actual!r}")
    if set(expectation.get("expected_downstream_invalidated", [])) != set(diagnostic.get("downstream_invalidated", [])):
        errors.append("downstream invalidation set differs")
    text = " ".join(str(diagnostic.get(key, "")) for key in ("failure_class", "failure_subcode", "detail", "message"))
    for marker in expectation.get("required_diagnostic_markers", []):
        if marker not in text: errors.append(f"required diagnostic marker missing: {marker}")
    base = artifact_root.resolve(strict=True)
    forbidden = expectation.get("forbidden_artifacts", [])
    if len(forbidden) != len(set(forbidden)): errors.append("duplicate forbidden artifact path")
    for relative in forbidden:
        try:
            candidate = (base / relative).resolve(strict=False); candidate.relative_to(base)
        except (OSError, ValueError):
            errors.append(f"forbidden artifact path escapes isolated root: {relative}"); continue
        if candidate.exists(): errors.append(f"forbidden artifact exists: {relative}")
    return errors


def sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_sha(root: Path) -> str:
    base = root.resolve(strict=True)
    digest = hashlib.sha256()
    for path in sorted((p for p in base.rglob("*") if p.is_file()), key=lambda p: p.relative_to(base).as_posix()):
        rel = path.relative_to(base).as_posix().encode()
        digest.update(len(rel).to_bytes(4, "big")); digest.update(rel); digest.update(bytes.fromhex(sha(path)))
    return digest.hexdigest()


def contained(root: Path, relative: str, stage: str) -> Path:
    if Path(relative).is_absolute() or not relative:
        raise Failure("package-path-escape", stage, "absolute-or-empty", f"non-relative path: {relative!r}")
    base = root.resolve(strict=True)
    try:
        lexical = base / relative
        was_symlink = lexical.is_symlink()
        target = lexical.resolve(strict=True)
        target.relative_to(base)
    except (OSError, ValueError) as exc:
        subcode = "package-symlink-escape" if 'was_symlink' in locals() and was_symlink else "package-path-escape"
        raise Failure("package-path-escape", stage, subcode, f"path escapes package root: {relative}") from exc
    if not target.is_file():
        raise Failure("package-path-escape", stage, "not-a-file", f"component is not a package file: {relative}")
    return target


def _schema_errors(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> list[str]:
    if "$ref" in schema:
        target: Any = root
        for part in schema["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        return _schema_errors(value, target, root, path)
    if "anyOf" in schema:
        if any(not _schema_errors(value, option, root, path) for option in schema["anyOf"]):
            return []
        return [f"{path}: does not match anyOf"]
    if "const" in schema and value != schema["const"]:
        return [f"{path}: expected constant {schema['const']!r}"]
    if "enum" in schema and value not in schema["enum"]:
        return [f"{path}: not in enum"]
    kind = schema.get("type")
    kinds = kind if isinstance(kind, list) else [kind] if kind else []
    pytypes = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
    if kinds and not any(isinstance(value, pytypes[x]) and not (x == "integer" and isinstance(value, bool)) for x in kinds):
        return [f"{path}: expected type {kind}"]
    errors: list[str] = []
    if isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{path}: missing required {name}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            errors.extend(f"{path}: unexpected property {name}" for name in value if name not in props)
        for name, child in value.items():
            if name in props:
                errors.extend(_schema_errors(child, props[name], root, f"{path}.{name}"))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0): errors.append(f"{path}: too few items")
        if schema.get("uniqueItems") is True:
            encoded = [json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for item in value]
            if len(encoded) != len(set(encoded)): errors.append(f"{path}: duplicate items")
        if "items" in schema:
            for i, item in enumerate(value): errors.extend(_schema_errors(item, schema["items"], root, f"{path}[{i}]"))
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value): errors.append(f"{path}: pattern mismatch")
    if isinstance(value, int) and not isinstance(value, bool) and value < schema.get("minimum", value): errors.append(f"{path}: below minimum")
    return errors


def source_bytes(component: dict[str, Any], package_root: Path, run_root: Path, stage: str) -> bytes:
    rel = component["source_path"]
    if rel.startswith("run://"):
        path = contained(run_root, rel.removeprefix("run://"), stage)
    else:
        path = contained(package_root, rel, stage)
    data = path.read_bytes()
    spec = component["source_slice"]
    if spec["kind"] == "whole-file": return data
    if spec["kind"] == "bytes": return data[spec["start"]:spec["end"]]
    lines = data.splitlines()
    return b"\n".join(lines[spec["start"] - 1:spec["end"]])


def validate(manifest: dict[str, Any], package_root: Path, run_root: Path) -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    stage = str(manifest.get("stage", "preflight"))
    schema_errors = _schema_errors(manifest, schema, schema)
    if schema_errors:
        joined = "; ".join(schema_errors[:5])
        subcode = "runtime-call-context-schema"
        for prefix, name in (("$.input", "unknown-input-field"), ("$.validated_state", "unknown-validated-state-field"),
                             (".source_slice", "unknown-source-slice-field"), ("$.budget_telemetry", "unknown-budget-field")):
            if prefix in joined and "unexpected property" in joined:
                subcode = name; break
        raise Failure("schema-invalid", stage, subcode, joined)

    runtime, selection = manifest["runtime"], manifest["selection"]
    package_root = package_root.resolve(strict=True); run_root = run_root.resolve(strict=True)
    if tree_sha(package_root) != runtime["package_sha256"]:
        raise Failure("package-hash-mismatch", "01", "package-hash-drift", "package tree hash differs")
    if sha(contained(package_root, "build-manifest.json", stage)) != runtime["build_manifest_sha256"]:
        raise Failure("package-hash-mismatch", "01", "build-manifest-drift", "build manifest hash differs")
    if sha(contained(package_root, "SKILL.md", stage)) != runtime["skill_root_sha256"]:
        raise Failure("package-hash-mismatch", "01", "skill-root-drift", "skill root hash differs")

    basis_blob = " ".join([selection["basis_kind"], *selection["basis_ids"]]).lower()
    if any(token in basis_blob for token in TAINT_KEYS):
        raise Failure("tainted-selection-basis", stage, "case-id-routes-shard", "case/topic custody was used as selection basis")
    if manifest["validated_state"]["live_pressure"] and not selection["candidate_components"] and selection["status"] == "selected":
        raise Failure("unresolved-context-without-hold", stage, "live-pressure-zero-candidate-without-hold", "live pressure has no candidate and no HOLD/PARTIAL")
    if manifest["validated_state"]["ambiguous"] and len(selection["candidate_components"]) > selection["candidate_cap"] and selection["status"] == "selected":
        raise Failure("ambiguity-cap-without-hold", stage, "ambiguous-over-cap-without-hold", "over-cap ambiguity did not HOLD/PARTIAL")

    input_row = manifest["input"]
    input_path = contained(run_root, input_row["path"], stage)
    raw_input = input_path.read_bytes()
    if sha256_bytes(raw_input) != input_row["sha256"] or len(raw_input) != input_row["byte_count"]:
        raise Failure("raw-input-hash-mismatch", stage, "raw-input-hash-drift", "raw input path/hash/byte count differ")
    capsule = manifest["state_capsule"]
    previous_capsule: bytes | None = None
    if stage == "01":
        if not capsule["bootstrap"] or capsule["included"] or capsule["path"] is not None or capsule["sha256"] is not None:
            raise Failure("prior-capsule-not-delivered", stage, "bootstrap-contract", "Stage01 must be explicit capsule bootstrap")
        if input_row["included"] is not True:
            raise Failure("raw-input-not-delivered", stage, "raw-input-included-false", "Stage01 must transport exact raw input bytes")
    else:
        if not capsule["included"] or not capsule["validated"] or not isinstance(capsule["path"], str):
            raise Failure("prior-capsule-not-delivered", stage, "previous-capsule-omitted", "dependent call lacks previous validated capsule")
        capsule_path = contained(run_root, capsule["path"], stage)
        previous_capsule = capsule_path.read_bytes()
        if sha256_bytes(previous_capsule) != capsule["sha256"]:
            raise Failure("capsule-binding-mismatch", stage, "capsule-field-component-mismatch", "capsule path/hash binding differs")

    try:
        resolved = resolve_context(package_root, stage, manifest["validated_state"], previous_capsule,
                                   selection["candidate_cap"], raw_input if stage == "01" else None)
    except ResolutionError as exc:
        raise Failure("selected-component-not-delivered", stage, "resolver-failed", str(exc)) from exc
    if (resolved.get("status") == "HOLD" and resolved.get("hold_reason") == "live-pressure-without-semantic-context"
            and selection["status"] == "selected"):
        raise Failure("unresolved-context-without-hold", stage, "live-pressure-semantic-context-without-hold",
                      "live pressure has only transport custody and no owner/operation/route/cold semantic context")
    if selection["candidate_components"] != resolved["candidate_components"]:
        raise Failure("stage-derived-delivery-claim", stage, "candidate-set-not-resolver-derived", "declared candidates differ from pure resolver output")
    if selection["selected_components"] != resolved["selected_components"]:
        subcode = "stage07-shards-stage-derived-only" if stage == "07" else "selected-set-not-resolver-derived"
        raise Failure("stage-derived-delivery-claim", stage, subcode, "declared selection differs from pure resolver output")
    if selection["status"] != resolved["status"] or selection["hold_reason"] != resolved["hold_reason"]:
        raise Failure("status-join-mismatch", stage, "resolver-status-mismatch", "selection status/reason differs from resolver")

    selection_status = selection["status"]
    expected_status_join = {"HOLD": ("HOLD", "HOLD"), "PARTIAL": ("PARTIAL", "PARTIAL")}
    if selection_status in expected_status_join:
        if (manifest["delivery_status"], manifest["usage_status"]) != expected_status_join[selection_status] or not selection["hold_reason"]:
            raise Failure("status-join-mismatch", stage, "hold-partial-status-join", "HOLD/PARTIAL selection must carry matching delivery, usage, and reason")
    elif selection["hold_reason"] is not None or manifest["delivery_status"] in {"HOLD", "PARTIAL"} or manifest["usage_status"] in {"HOLD", "PARTIAL"}:
        raise Failure("status-join-mismatch", stage, "selected-status-join", "selected context cannot carry HOLD/PARTIAL status")

    components = manifest["components"]
    ids = [x["component_id"] for x in components]
    if len(ids) != len(set(ids)):
        raise Failure("undeclared-prompt-envelope", stage, "duplicate-component-id", "component IDs must be unique")
    by_id = {x["component_id"]: x for x in components}
    expected_by_id = {x["component_id"]: x for x in resolved["components"]}
    missing = [component_id for component_id in resolved["selected_components"] if component_id not in by_id]
    if missing:
        if stage == "07" and any(x in missing for x in ("package:references/runtime-shard-output-release.md", "package:references/runtime-shard-render-contract.md")):
            raise Failure("mandatory-stage-component-missing", stage, "missing-both-stage07-shards", f"mandatory Stage07 component missing: {missing}")
        if "raw-input" in missing:
            raise Failure("raw-input-not-delivered", stage, "raw-input-omitted", "Stage01 raw input component is absent")
        if "state-capsule" in missing:
            raise Failure("prior-capsule-not-delivered", stage, "capsule-not-in-prompt", "previous capsule component is absent")
        raise Failure("selected-component-not-delivered", stage, "selected-shard-envelope-absent", f"selected-shard delivery component missing: {missing}")
    for component_id, expected in expected_by_id.items():
        actual = by_id.get(component_id)
        if actual is None:
            continue
        if actual["kind"] != expected["kind"] or actual["sha256"] != expected["sha256"] or actual["byte_count"] != expected["byte_count"] or actual["source_slice"] != expected["source_slice"]:
            cls = "capsule-binding-mismatch" if component_id == "state-capsule" else "raw-input-hash-mismatch" if component_id == "raw-input" else "component-hash-mismatch"
            subcode = "cold-clause-hash-mismatch" if actual["kind"] == "cold-law-clause" else "component-hash-drift" if cls == "component-hash-mismatch" else f"{component_id}-resolver-byte-mismatch"
            raise Failure(cls, stage, subcode, "component bytes/slice differ from resolver output")
        if component_id == "state-capsule" and (actual["source_path"] != f"run://{capsule['path']}" or actual["sha256"] != capsule["sha256"]):
            raise Failure("capsule-binding-mismatch", stage, "capsule-field-component-mismatch", "capsule fields and component do not bind the same path/hash")
        if component_id == "raw-input" and (actual["source_path"] != f"run://{input_row['path']}" or actual["sha256"] != input_row["sha256"]):
            raise Failure("raw-input-hash-mismatch", stage, "raw-input-field-component-mismatch", "input fields and raw-input component differ")
    undeclared_components = [x for x in components if x["component_id"] not in expected_by_id and x["kind"] != "harness-supplement"]
    if undeclared_components:
        raise Failure("undeclared-prompt-envelope", stage, "undeclared-runtime-component", "manifest contains runtime components not selected by resolver")

    selected = set(selection["selected_components"])
    delivered_ids = {x["component_id"] for x in components if x["delivery"] != "not-delivered"}
    if not selected.issubset(delivered_ids):
        raise Failure("selected-component-not-delivered", stage, "selected-shard-envelope-absent", "selected component is not delivered")
    delivered_cold = sorted(x["component_id"] for x in components if x["kind"] == "cold-law-clause" and x["delivery"] != "not-delivered")
    if manifest["cold_law_clauses_delivered"] != delivered_cold:
        raise Failure("cold-law-delivery-list-mismatch", stage, "cold-law-derived-list-mismatch", "cold-law delivery list is not derived from delivered clause components")
    declared = set(manifest["producer_declared_used"]); operation_bound = set(manifest["operation_bound_components"])
    if not declared.issubset(delivered_ids):
        raise Failure("declared-use-not-delivered", stage, "declared-used-not-delivered", "producer declared use of undelivered component")
    if not operation_bound.issubset(declared) or not operation_bound.issubset(delivered_ids):
        raise Failure("usage-evidence-mismatch", stage, "operation-bound-not-delivered-declared", "operation-bound components must be delivered and producer-declared")
    usage = manifest["usage_status"]
    usage_ok = ((usage == "NOT_DECLARED" and not declared and not operation_bound) or
                (usage == "PRODUCER_DECLARED" and bool(declared) and not operation_bound) or
                (usage == "OPERATION_BOUND" and bool(operation_bound) and bool(declared)) or
                usage in {"HOLD", "PARTIAL"})
    if not usage_ok:
        raise Failure("usage-evidence-mismatch", stage, "usage-status-declaration-mismatch", "usage_status disagrees with declared/operation-bound evidence")
    if manifest["prompt"]["includes_full_runtime"] or any(x["source_path"] == "SKILL.md" and x["kind"] != "kernel" for x in components):
        raise Failure("full-runtime-reinline", stage, "full-runtime-reinline", "full runtime was eagerly re-inlined")

    prompt_path = contained(run_root, manifest["prompt"]["path"], stage); prompt = prompt_path.read_bytes()
    if sha256_bytes(prompt) != manifest["prompt"]["sha256"] or len(prompt) != manifest["prompt"]["byte_count"]:
        raise Failure("prompt-hash-mismatch", stage, "prompt-hash-drift", "prompt bytes changed after manifest binding")
    mode = runtime["delivery_mode"]; receipt = manifest.get("host_receipt")
    if mode == "unverified-host-ambient":
        raise Failure("membership-is-not-delivery", stage, "package-membership-only-claim", "package membership does not prove delivery")
    if mode == "host-skill-context-receipt":
        if not isinstance(receipt, dict) or receipt.get("opaque") is not False or receipt.get("self_attested") is not False:
            raise Failure("unverifiable-host-receipt", stage, "opaque-host-receipt", "host receipt lacks independent exact hashes")
        if receipt.get("package_sha256") != runtime["package_sha256"]:
            raise Failure("unverifiable-host-receipt", stage, "receipt-package-mismatch", "host receipt package hash differs")

    prompt_bound: list[tuple[str, str]] = []
    for component in components:
        data = source_bytes(component, package_root, run_root, stage)
        if sha256_bytes(data) != component["sha256"] or len(data) != component["byte_count"]:
            raise Failure("component-hash-mismatch", stage, "source-slice-drift", f"component hash/bytes differ: {component['component_id']}")
        if component["delivery"] == "prompt-bound":
            prompt_bound.append((component["component_id"], component["sha256"]))
            header = f"----- BEGIN DAEE COMPONENT: {component['component_id']}; sha256={component['sha256']} -----\n".encode()
            footer = f"\n----- END DAEE COMPONENT: {component['component_id']} -----".encode(); envelope = header + data + footer
            if prompt.count(envelope) != 1:
                raise Failure("selected-component-not-delivered", stage, "component-envelope-count", f"component envelope not exactly once: {component['component_id']}")
            start = prompt.index(envelope) + len(header); end = start + len(data)
            if component["prompt_start_byte"] != start or component["prompt_end_byte"] != end:
                raise Failure("selected-component-not-delivered", stage, "component-offset-mismatch", f"component offsets differ: {component['component_id']}")
        elif component["delivery"] == "host-receipt-bound":
            rows = receipt.get("components", []) if isinstance(receipt, dict) else []
            if not any(x.get("component_id") == component["component_id"] and x.get("sha256") == component["sha256"] for x in rows if isinstance(x, dict)):
                raise Failure("unverifiable-host-receipt", stage, "receipt-component-missing", f"receipt lacks component: {component['component_id']}")
    observed_envelopes = [(m.group(1).decode(), m.group(2).decode()) for m in re.finditer(rb"----- BEGIN DAEE COMPONENT: ([^;\r\n]+); sha256=([0-9a-f]{64}) -----\r?\n", prompt)]
    if sorted(observed_envelopes) != sorted(prompt_bound):
        raise Failure("undeclared-prompt-envelope", stage, "undeclared-prompt-envelope", "prompt envelope inventory differs from declared prompt-bound components")

    telemetry = manifest["budget_telemetry"]
    if telemetry["selected_component_count"] != len(selected):
        raise Failure("schema-invalid", stage, "telemetry-selection-count", "selected component telemetry differs")
    if telemetry["effective_context_bytes"] > telemetry["effective_context_limit"] and selection["status"] == "selected":
        raise Failure("context-budget-without-hold", stage, "over-budget-without-hold", "over-budget call did not HOLD/PARTIAL")
    expected_proof = "harness-assisted" if any(x["kind"] == "harness-supplement" for x in components) else "package-faithful"
    if manifest["proof_mode"] != expected_proof:
        raise Failure("stage-derived-delivery-claim", stage, "proof-mode-misclassified", "proof mode does not match component sources")
    return {"status": selection_status.lower() if selection_status != "selected" else "pass", "failure_class": None, "earliest_stage": None,
            "proof_mode": manifest["proof_mode"], "selected_component_count": len(selected), "effective_context_bytes": telemetry["effective_context_bytes"],
            "component_ids": sorted(delivered_ids), "cold_law_clause_ids": delivered_cold}


def _actual_scenario_manifest(path: Path, package: Path, run: Path) -> dict[str, Any]:
    row = json.loads(path.read_text(encoding="utf-8"))
    name, kind = row.get("scenario"), row.get("kind")
    stage = str(row.get("stage", "03"))
    state = {"route_shards": [], "owner_module_ids": [], "cold_clause_ids": [], "live_pressure": False, "ambiguous": False}
    if kind == "bootstrap": stage = "01"
    elif kind == "prior-capsule": stage = "02"
    elif kind == "owner-module": stage = "04"; state["owner_module_ids"] = ["M1-self-refutation"]
    elif kind == "cold-clause": stage = "04"; state["cold_clause_ids"] = ["clause.execution-mandate-detail"]
    elif kind == "stage07-release": stage = "07"
    elif kind == "wide-capacity": state["route_shards"] = ["references/runtime-core-ir.md", "references/runtime-core-pipeline.md"]
    elif kind == "ambiguous-hold":
        state["ambiguous"] = True
        state["route_shards"] = [f"references/over-cap-{index}.md" for index in range(5)]
    elif kind == "live-pressure-owner-resolved":
        stage = "04"; state["live_pressure"] = True; state["owner_module_ids"] = ["M1-self-refutation"]
    mutation = row.get("mutation")
    if name == "stage04-live-pressure-capsule-only":
        stage = "04"; state["live_pressure"] = True
    if mutation in {"cold-law-delivery-list-mismatch", "usage-evidence-mismatch"} or name == "cold-clause-hash-mismatch":
        stage = "04"; state["cold_clause_ids"] = ["clause.execution-mandate-detail"]
    manifest = compose_actual_fixture(package, run, stage=stage, state=state)
    if name == "stage04-live-pressure-capsule-only":
        manifest["selection"].update(status="selected", hold_reason=None,
                                     selected_components=["state-capsule"], candidate_components=["state-capsule"])
        manifest["delivery_status"] = "DELIVERED"; manifest["usage_status"] = "NOT_DECLARED"
        manifest["budget_telemetry"]["selected_component_count"] = 1
    if kind == "host-receipt":
        manifest["runtime"]["delivery_mode"] = "host-skill-context-receipt"
        receipt_rows = []
        for component in manifest["components"]:
            component["delivery"] = "host-receipt-bound"; component["prompt_start_byte"] = None; component["prompt_end_byte"] = None
            receipt_rows.append({"component_id": component["component_id"], "sha256": component["sha256"]})
        manifest["host_receipt"] = {"opaque": False, "self_attested": False, "package_sha256": manifest["runtime"]["package_sha256"], "components": receipt_rows}
        prompt = b"DAEE host-receipt transport frame\n"; (run / manifest["prompt"]["path"]).write_bytes(prompt)
        manifest["prompt"]["sha256"] = sha256_bytes(prompt); manifest["prompt"]["byte_count"] = len(prompt); manifest["budget_telemetry"]["effective_context_bytes"] = len(prompt)
    if mutation == "prior-capsule-not-delivered": manifest["components"] = [x for x in manifest["components"] if x["component_id"] != "state-capsule"]
    elif mutation == "selected-component-not-delivered": manifest["components"] = [x for x in manifest["components"] if x["component_id"] == "state-capsule"]
    elif mutation == "stage-derived-delivery-claim": manifest["selection"]["selected_components"].append("package:stage-derived-only.md")
    elif mutation == "component-hash-mismatch": manifest["components"][-1]["sha256"] = "f" * 64
    elif mutation == "declared-use-not-delivered": manifest["producer_declared_used"] = ["absent-clause"]
    elif mutation == "package-path-escape": manifest["components"][-1]["source_path"] = "escape-link.md" if name == "package-symlink-escape" else "../outside-package.md"
    elif mutation == "tainted-selection-basis": manifest["selection"]["basis_ids"] = ["case_id:fixture-taint"]
    elif mutation == "unresolved-context-without-hold" and name != "stage04-live-pressure-capsule-only":
        manifest["validated_state"]["live_pressure"] = True; manifest["selection"].update(candidate_components=[], selected_components=[]); manifest["budget_telemetry"]["selected_component_count"] = 0
    elif mutation == "ambiguity-cap-without-hold":
        manifest["validated_state"]["ambiguous"] = True; manifest["selection"].update(candidate_components=[f"candidate:{x}" for x in range(5)], selected_components=[]); manifest["budget_telemetry"]["selected_component_count"] = 0
    elif mutation == "prompt-hash-mismatch": manifest["prompt"]["sha256"] = "f" * 64
    elif mutation == "full-runtime-reinline": manifest["prompt"]["includes_full_runtime"] = True
    elif mutation == "context-budget-without-hold": manifest["budget_telemetry"]["effective_context_limit"] = 1
    elif mutation == "package-hash-mismatch": manifest["runtime"]["package_sha256"] = "f" * 64
    elif mutation == "unverifiable-host-receipt":
        manifest["runtime"]["delivery_mode"] = "host-skill-context-receipt"
        manifest["host_receipt"] = {"opaque": True, "self_attested": True, "package_sha256": manifest["runtime"]["package_sha256"], "components": []}
    elif mutation == "membership-is-not-delivery":
        manifest["runtime"]["delivery_mode"] = "unverified-host-ambient"; manifest["runtime"]["evidence_lane"] = "unverified-host-ambient"
    elif mutation == "mandatory-stage-component-missing":
        manifest["components"] = [x for x in manifest["components"] if x["component_id"] not in {"package:references/runtime-shard-output-release.md", "package:references/runtime-shard-render-contract.md"}]
    elif mutation == "raw-input-not-delivered": manifest["components"] = [x for x in manifest["components"] if x["component_id"] != "raw-input"]
    elif mutation == "raw-input-hash-mismatch": manifest["input"]["sha256"] = "f" * 64
    elif mutation == "undeclared-prompt-envelope":
        prompt_path = run / manifest["prompt"]["path"]
        prompt = prompt_path.read_bytes() + b"----- BEGIN DAEE COMPONENT: undeclared; sha256=" + (b"f" * 64) + b" -----\nundeclared\n----- END DAEE COMPONENT: undeclared -----\n"
        prompt_path.write_bytes(prompt); manifest["prompt"]["sha256"] = sha256_bytes(prompt); manifest["prompt"]["byte_count"] = len(prompt); manifest["budget_telemetry"]["effective_context_bytes"] = len(prompt)
    elif mutation == "capsule-binding-mismatch": manifest["state_capsule"]["sha256"] = "f" * 64
    elif mutation == "cold-law-delivery-list-mismatch": manifest["cold_law_clauses_delivered"] = []
    elif mutation == "usage-evidence-mismatch":
        manifest["producer_declared_used"] = ["clause.execution-mandate-detail"]
        manifest["usage_status"] = "NOT_DECLARED"
    elif mutation == "schema-invalid":
        if name == "unknown-input-field": manifest["input"]["review_unknown"] = True
        elif name == "unknown-validated-state-field": manifest["validated_state"]["review_unknown"] = True
        elif name == "unknown-source-slice-field": manifest["components"][0]["source_slice"]["review_unknown"] = True
        elif name == "unknown-budget-field": manifest["budget_telemetry"]["review_unknown"] = True
    return manifest


def scenario_result(path: Path, package: Path | None = None) -> tuple[int, dict[str, Any]]:
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("schema") != "daee-runtime-context-scenario-v1":
        return 1, Failure("schema-invalid", "preflight", "scenario-schema", "wrong scenario schema").diagnostic()
    cls, stage = row.get("mutation"), str(row.get("stage", "preflight"))
    if cls not in SUPPORTED_SCENARIO_FAILURES:
        if row.get("expected_valid") is not True:
            return 1, Failure("schema-invalid", stage, "unknown-mutation", f"unsupported mutation: {cls}").diagnostic()
    exp_path = path.with_suffix(".expectation.json")
    if row.get("expected_valid") is not True:
        if not exp_path.is_file(): return 1, Failure("schema-invalid", stage, "expectation-missing", "invalid fixture lacks same-stem expectation").diagnostic()
        exp = json.loads(exp_path.read_text(encoding="utf-8"))
        if exp.get("expected_failure_class") != cls or str(exp.get("expected_earliest_stage")) != stage:
            return 1, Failure("schema-invalid", stage, "expectation-mismatch", "scenario and expectation disagree").diagnostic()
    with tempfile.TemporaryDirectory(prefix="daee-context-scenario-") as tmp:
        run = Path(tmp); package_root = (package or (ROOT / "skill")).resolve()
        if path.stem == "package-symlink-escape":
            copied = run / "package"; shutil.copytree(package_root, copied); outside = run / "outside-package.md"; outside.write_text("outside package\n", encoding="utf-8")
            try:
                os.symlink(outside, copied / "escape-link.md")
            except OSError as exc:
                return 0, {"checker_id": "runtime-context-delivery", "status": "skip", "skip_reason": "host-symlink-capability-unavailable", "os_error": f"{type(exc).__name__}: {exc}"}
            package_root = copied
        try:
            result = validate(_actual_scenario_manifest(path, package_root, run), package_root, run)
            return 0, result | {"scenario": row.get("scenario")}
        except Failure as exc:
            diagnostic = exc.diagnostic()
            if row.get("expected_valid") is not True:
                contract_errors = validate_expectation_contract(exp, "runtime-context-delivery", 1, diagnostic, run, path.name)
                if contract_errors:
                    return 1, Failure("expectation-contract-failure", stage, "a11-expectation-mismatch", "; ".join(contract_errors)).diagnostic()
            return 1, diagnostic


def fixture_sweep(root: Path) -> tuple[bool, int, int, int]:
    valid = sorted((root / "valid").glob("*.json")); invalid = sorted((root / "invalid").glob("*.json"))
    invalid = [p for p in invalid if not p.name.endswith(".expectation.json")]
    ok = True; skipped = 0
    for path in valid:
        code, _ = scenario_result(path); ok &= code == 0
    for path in invalid:
        code, diag = scenario_result(path)
        exp = json.loads(path.with_suffix(".expectation.json").read_text(encoding="utf-8"))
        if path.stem == "package-symlink-escape" and code == 0 and diag.get("status") == "skip":
            skipped += 1; continue
        ok &= code == 1 and diag["failure_class"] == exp["expected_failure_class"] and diag["earliest_stage"] == str(exp["expected_earliest_stage"])
    return ok, len(valid), len(invalid), skipped


def compose_actual_fixture(package_root: Path, run_root: Path, stage: str = "03", state: dict[str, Any] | None = None) -> dict[str, Any]:
    raw_input = b"neutral raw input bytes"
    (run_root / "raw-input.bin").write_bytes(raw_input)
    capsule = None if stage == "01" else b'{"schema":"daee-state-capsule-v2","sequence":2}'
    if capsule is not None: (run_root / "previous-capsule.json").write_bytes(capsule)
    state = state or {"route_shards": [], "owner_module_ids": [], "cold_clause_ids": [], "live_pressure": False, "ambiguous": False}
    resolution = resolve_context(package_root, stage, state, capsule, 4, raw_input if stage == "01" else None)
    parts = [b"DAEE transport frame\n"]
    components = []
    for raw in resolution["components"]:
        data = raw["bytes"]
        header = f"----- BEGIN DAEE COMPONENT: {raw['component_id']}; sha256={raw['sha256']} -----\n".encode()
        footer = f"\n----- END DAEE COMPONENT: {raw['component_id']} -----".encode()
        start = sum(map(len, parts)) + len(header); end = start + len(data)
        parts.extend([header, data, footer, b"\n"])
        source_path = {"transport://raw-input": "run://raw-input.bin", "transport://previous-capsule": "run://previous-capsule.json"}.get(raw["source_path"], raw["source_path"])
        components.append({k: v for k, v in raw.items() if k != "bytes"} | {"source_path": source_path, "delivery": "prompt-bound", "prompt_start_byte": start, "prompt_end_byte": end})
    prompt = b"".join(parts); (run_root / "prompt.md").write_bytes(prompt)
    runtime_bytes = sum(x["byte_count"] for x in components if x["kind"] not in {"state-capsule", "raw-input"})
    hold = resolution["status"] in {"HOLD", "PARTIAL"}
    cold_delivered = sorted(x["component_id"] for x in components if x["kind"] == "cold-law-clause")
    return {
        "schema": "daee-runtime-call-context-v1", "case_id": "custody-only", "stage": stage, "call_index": int(stage),
        "runtime": {"delivery_mode": "explicit-prompt-components", "evidence_lane": "package-faithful", "package_profile": "execution-mini",
                    "package_sha256": tree_sha(package_root), "build_manifest_sha256": sha(package_root / "build-manifest.json"),
                    "skill_root_sha256": sha(package_root / "SKILL.md"), "source_commit": "0" * 40},
        "input": {"path": "raw-input.bin", "sha256": sha256_bytes(raw_input), "byte_count": len(raw_input), "included": stage == "01"},
        "state_capsule": {"bootstrap": stage == "01", "path": None if capsule is None else "previous-capsule.json", "sha256": None if capsule is None else sha256_bytes(capsule), "included": capsule is not None, "validated": capsule is not None},
        "validated_state": state,
        "selection": {"basis_kind": "structural-trigger", "basis_ids": ["validated-stage-02-route-state"],
                      "candidate_components": list(resolution["candidate_components"]), "selected_components": list(resolution["selected_components"]),
                      "status": resolution["status"], "hold_reason": resolution["hold_reason"], "candidate_cap": 4},
        "components": components, "cold_law_clauses_delivered": cold_delivered, "producer_declared_used": [], "operation_bound_components": [],
        "prompt": {"path": "prompt.md", "sha256": sha256_bytes(prompt), "byte_count": len(prompt), "includes_full_runtime": False, "includes_prior_full_output": False},
        "delivery_status": resolution["status"] if hold else "DELIVERED", "usage_status": resolution["status"] if hold else "NOT_DECLARED", "proof_mode": "package-faithful", "host_receipt": None,
        "budget_telemetry": {"transport_frame_bytes": len(parts[0]), "runtime_component_bytes": runtime_bytes, "capsule_bytes": 0 if capsule is None else len(capsule),
                             "local_excerpt_bytes": 0, "effective_context_bytes": len(prompt), "effective_context_limit": len(prompt) + 1000,
                             "selected_component_count": len(resolution["selected_components"])},
        "non_claims": ["delivery does not prove internal model attention", "structural context fidelity is not semantic truth"]}


def self_test(package_root: Path | None = None) -> int:
    package = (package_root or (ROOT / "skill")).resolve()
    checks: list[tuple[str, bool]] = []
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    checks.append(("schema identity", schema.get("title") == "DAEE runtime call context v1"))
    with tempfile.TemporaryDirectory(prefix="daee-context-") as tmp:
        run = Path(tmp)
        manifest = compose_actual_fixture(package, run)
        checks.append(("actual package/component/prompt hashes validate", validate(manifest, package, run)["status"] == "pass"))
        drift = json.loads(json.dumps(manifest)); drift["components"][1]["sha256"] = "f" * 64
        try: validate(drift, package, run); caught = False
        except Failure as exc: caught = exc.failure_class == "component-hash-mismatch"
        checks.append(("component hash mutation rejected for right reason", caught))
        omitted = json.loads(json.dumps(manifest)); omitted["components"] = [x for x in omitted["components"] if x["component_id"] != "state-capsule"]
        try: validate(omitted, package, run); caught = False
        except Failure as exc: caught = exc.failure_class == "prior-capsule-not-delivered"
        checks.append(("previous capsule omission rejected before downstream", caught))
        used = json.loads(json.dumps(manifest)); used["producer_declared_used"] = ["absent-clause"]
        try: validate(used, package, run); caught = False
        except Failure as exc: caught = exc.failure_class == "declared-use-not-delivered"
        checks.append(("used-not-delivered mutation rejected", caught))
        over = json.loads(json.dumps(manifest)); over["budget_telemetry"]["effective_context_limit"] = 1
        try: validate(over, package, run); caught = False
        except Failure as exc: caught = exc.failure_class == "context-budget-without-hold"
        checks.append(("over-budget without HOLD rejected", caught))
        state = {"route_shards": [], "owner_module_ids": [], "cold_clause_ids": ["clause.execution-mandate-detail"], "live_pressure": False, "ambiguous": False}
        cold_resolution = resolve_context(package, "04", state, b"{}")
        cold_component = next(x for x in cold_resolution["components"] if x["kind"] == "cold-law-clause")
        cold_record = {k: v for k, v in cold_component.items() if k != "bytes"} | {"delivery": "prompt-bound", "prompt_start_byte": 0, "prompt_end_byte": cold_component["byte_count"]}
        checks.append(("checker reproduces resolver cold-clause bytes", sha256_bytes(source_bytes(cold_record, package, run, "04")) == cold_component["sha256"]))
        hold_state = {"route_shards": [f"references/over-cap-{index}.md" for index in range(5)], "owner_module_ids": [], "cold_clause_ids": [], "live_pressure": False, "ambiguous": True}
        mislabeled_hold = compose_actual_fixture(package, run, stage="03", state=hold_state)
        mislabeled_hold["delivery_status"] = "DELIVERED"; mislabeled_hold["usage_status"] = "NOT_DECLARED"
        try: validate(mislabeled_hold, package, run); caught = False
        except Failure as exc: caught = exc.failure_class == "status-join-mismatch"
        checks.append(("HOLD cannot claim DELIVERED/ordinary usage", caught))
        expectation = json.loads((FIXTURES / "invalid" / "shard-selected-not-delivered.expectation.json").read_text(encoding="utf-8"))
        diagnostic = Failure("selected-component-not-delivered", "03", "selected-shard-envelope-absent", "selected-shard delivery missing").diagnostic()
        expectation_root = run / "expectation-artifacts"; expectation_root.mkdir()
        checks.append(("A11 expectation baseline accepted", not validate_expectation_contract(expectation, "runtime-context-delivery", 1, diagnostic, expectation_root, "shard-selected-not-delivered.json")))
        sabotages: list[tuple[str, Any]] = [
            ("schema", "wrong"), ("kind", "composite-historical"), ("fixture", "other.json"),
            ("expected_checker_id", "wrong-checker"), ("expected_exit_category", "usage-error"),
            ("expected_exit_code", 2), ("expected_earliest_stage", "02"),
            ("expected_failure_class", "wrong-class"), ("expected_failure_subcode", "wrong-subcode"),
            ("expected_downstream_invalidated", ["04"]), ("required_diagnostic_markers", ["absent-marker"]),
            ("provenance", ""),
        ]
        sabotage_results = []
        for field, value in sabotages:
            candidate = json.loads(json.dumps(expectation)); candidate[field] = value
            sabotage_results.append(bool(validate_expectation_contract(candidate, "runtime-context-delivery", 1, diagnostic, expectation_root, "shard-selected-not-delivered.json")))
        missing_field = json.loads(json.dumps(expectation)); missing_field.pop("expected_failure_subcode")
        sabotage_results.append(bool(validate_expectation_contract(missing_field, "runtime-context-delivery", 1, diagnostic, expectation_root, "shard-selected-not-delivered.json")))
        unknown_field = json.loads(json.dumps(expectation)); unknown_field["review_unknown"] = True
        sabotage_results.append(bool(validate_expectation_contract(unknown_field, "runtime-context-delivery", 1, diagnostic, expectation_root, "shard-selected-not-delivered.json")))
        forbidden_path = expectation_root / expectation["forbidden_artifacts"][0]; forbidden_path.write_text("sabotage", encoding="utf-8")
        sabotage_results.append(bool(validate_expectation_contract(expectation, "runtime-context-delivery", 1, diagnostic, expectation_root, "shard-selected-not-delivered.json")))
        forbidden_path.unlink()
        checks.append((f"A11 expectation field sabotage rejected ({len(sabotage_results)} variants)", all(sabotage_results)))
    fixture_ok, valid_count, invalid_count, skipped_count = fixture_sweep(FIXTURES)
    checks.append((f"fixture lattice ({valid_count} valid/{invalid_count} invalid/{skipped_count} capability skip)", fixture_ok))
    checks.append(("no process/network/model orchestration imports", all(name not in globals() for name in ("subprocess", "socket", "requests"))))
    ok = all(v for _, v in checks)
    for name, passed in checks: print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"runtime context delivery self-test: {'PASS' if ok else 'FAIL'} ({sum(v for _, v in checks)}/{len(checks)})")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--package-only-self-test", action="store_true")
    parser.add_argument("--package-root", type=Path)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--scenario", type=Path)
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test or args.package_only_self_test:
        return self_test(args.package_root)
    if args.fixtures:
        ok, valid, invalid, skipped = fixture_sweep(args.fixtures)
        print(json.dumps({"status": "pass" if ok else "fail", "valid": valid, "invalid": invalid, "skipped": skipped}, sort_keys=True)); return 0 if ok else 1
    if args.scenario:
        code, diag = scenario_result(args.scenario); print(json.dumps(diag, sort_keys=True)); return code
    if args.manifest:
        if not args.package_root or not args.run_root: parser.error("--manifest requires --package-root and --run-root")
        try:
            result = validate(json.loads(args.manifest.read_text(encoding="utf-8")), args.package_root, args.run_root)
            print(json.dumps(result, sort_keys=True)); return 0
        except Failure as exc:
            print(json.dumps(exc.diagnostic(), sort_keys=True)); return 1
    parser.error("choose --self-test, --fixtures, --scenario, or --manifest")


if __name__ == "__main__":
    sys.exit(main())
