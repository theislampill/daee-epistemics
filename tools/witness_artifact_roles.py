#!/usr/bin/env python3
"""Canonical witness artifact role and schema registry.

This stdlib-only module is the sole dispatcher for the current public graph,
Stage08 audit envelope, subordinate binding record, and state transport roles.
Historical objects are readable only through an explicitly selected adapter.
Structural acceptance does not establish semantic truth, provenance, uptake,
fresh generation, or release readiness.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CURRENT = "current"
HISTORICAL = "historical"


@dataclass(frozen=True)
class RoleSpec:
    role: str
    discriminator_field: str
    discriminator: str
    schema_path: str | None
    stage: str


@dataclass(frozen=True)
class Diagnostic:
    failure_class: str
    failure_subcode: str
    earliest_stage: str
    message: str
    path: str = "$"
    downstream_invalidated: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["downstream_invalidated"] = list(self.downstream_invalidated)
        return result


ROLE_SPECS: dict[str, RoleSpec] = {
    "public_graph": RoleSpec("public_graph", "schema_version", "public-field-witness-v1", "schema/field-witness.schema.json", "07"),
    "audit_envelope": RoleSpec("audit_envelope", "schema_version", "field-witness-envelope-v1", "schema/field-witness-envelope.schema.json", "08"),
    "artifact_binding": RoleSpec("artifact_binding", "schema_version", "field-witness-artifact-binding-v1", None, "08"),
    "state_transport_v2": RoleSpec("state_transport_v2", "schema", "daee-state-capsule-v2", "schema/state-capsule-v2.schema.json", "08"),
    "state_transport_v1": RoleSpec("state_transport_v1", "schema", "daee-state-capsule-v1", "schema/state-capsule.schema.json", "08"),
}

PUBLIC_EXCLUSIVE_KEYS = {"B_LA", "B_MRP", "B_total", "nodes", "edges", "generated_burdens", "mrp_resultants", "terminal_states", "owner_activations"}
ENVELOPE_EXCLUSIVE_KEYS = {"route_gradient", "burden_events", "reconstruction", "transfer_boundary", "register_deltas", "provenance", "artifact_binding"}
BINDING_REQUIRED = {
    "schema_version", "canonicalization", "source_commit", "output_sha256",
    "public_field_witness_sha256", "audit_envelope_projection_sha256",
    "activation_lifecycle_fingerprint_sha256", "stage04_projection_sha256",
    "stage06_projection_sha256", "stage07_projection_sha256", "act_rows_hash",
    "nar_hash", "owner_activation_ordering_hash", "proof_class",
    "binding_status", "non_claims",
}
SHA_FIELDS = {
    "output_sha256", "public_field_witness_sha256", "audit_envelope_projection_sha256",
    "activation_lifecycle_fingerprint_sha256", "stage04_projection_sha256",
    "stage06_projection_sha256", "stage07_projection_sha256", "act_rows_hash",
    "nar_hash", "owner_activation_ordering_hash",
}


def schema_path_for_role(role: str) -> Path | None:
    spec = ROLE_SPECS[role]
    return ROOT / spec.schema_path if spec.schema_path else None


def discriminator_for_role(role: str) -> str:
    return ROLE_SPECS[role].discriminator


def load_schema_for_role(role: str) -> dict[str, Any]:
    path = schema_path_for_role(role)
    if path is None:
        raise ValueError(f"role {role!r} has a subordinate custom contract, not an independent schema file")
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    import hashlib
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None
    value: Any = root_schema
    for part in ref[2:].split("/"):
        if not isinstance(value, dict):
            return None
        value = value.get(part.replace("~1", "/").replace("~0", "~"))
    return value if isinstance(value, dict) else None


def _type_ok(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def json_schema_errors(value: Any, root_schema: dict[str, Any], schema: dict[str, Any] | None = None, path: str = "$") -> list[str]:
    """Validate the repository's used JSON-Schema subset without dependencies."""
    schema = root_schema if schema is None else schema
    if "$ref" in schema:
        resolved = _resolve_ref(root_schema, str(schema["$ref"]))
        return [f"{path}: unresolved schema ref {schema['$ref']}"] if resolved is None else json_schema_errors(value, root_schema, resolved, path)
    if "anyOf" in schema:
        branches = schema.get("anyOf", [])
        if not any(not json_schema_errors(value, root_schema, branch, path) for branch in branches if isinstance(branch, dict)):
            return [f"{path}: value matches no anyOf branch"]
        return []
    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: must be one of {schema['enum']!r}")
    expected = schema.get("type")
    if isinstance(expected, list):
        if not any(_type_ok(value, item) for item in expected):
            return errors + [f"{path}: expected one of types {expected}, got {type(value).__name__}"]
    elif isinstance(expected, str) and not _type_ok(value, expected):
        return errors + [f"{path}: expected {expected}, got {type(value).__name__}"]
    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            errors.append(f"{path}: string shorter than minLength")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            errors.append(f"{path}: value does not match {pattern}")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path}: value is below minimum {schema['minimum']}")
    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            errors.append(f"{path}: array shorter than minItems")
        if schema.get("uniqueItems") is True:
            identities = [canonical_json_bytes(item) for item in value]
            if len(identities) != len(set(identities)):
                errors.append(f"{path}: array items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(json_schema_errors(item, root_schema, item_schema, f"{path}[{index}]"))
    if isinstance(value, dict):
        if len(value) < int(schema.get("minProperties", 0)):
            errors.append(f"{path}: object has fewer than minProperties")
        required = schema.get("required", [])
        for key in required if isinstance(required, list) else []:
            if key not in value:
                errors.append(f"{path}: missing required property {key}")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        additional = schema.get("additionalProperties", True)
        if additional is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unknown property {key}")
        for key, child in value.items():
            child_schema = properties.get(key)
            if child_schema is None and isinstance(additional, dict):
                child_schema = additional
            if isinstance(child_schema, dict):
                errors.extend(json_schema_errors(child, root_schema, child_schema, f"{path}.{key}"))
    return errors


def classify_role(payload: Any, compatibility: str = CURRENT) -> tuple[str | None, list[Diagnostic]]:
    if not isinstance(payload, dict):
        return None, [Diagnostic("witness-role", "witness-role-not-object", "07", "witness artifact must be a JSON object", downstream_invalidated=("08",))]
    version = payload.get("schema_version")
    schema = payload.get("schema")
    diagnostics: list[Diagnostic] = []
    for role, spec in ROLE_SPECS.items():
        if payload.get(spec.discriminator_field) == spec.discriminator:
            if role == "public_graph" and ENVELOPE_EXCLUSIVE_KEYS.intersection(payload):
                key = sorted(ENVELOPE_EXCLUSIVE_KEYS.intersection(payload))[0]
                diagnostics.append(Diagnostic("witness-role", "witness-role-competing-owner", "07", f"public_graph contains competing owner key {key}", f"$.{key}", ("08",)))
            if role == "audit_envelope" and PUBLIC_EXCLUSIVE_KEYS.intersection(payload):
                key = sorted(PUBLIC_EXCLUSIVE_KEYS.intersection(payload))[0]
                diagnostics.append(Diagnostic("witness-role", "witness-role-competing-owner", "08", f"audit_envelope contains competing public owner key {key}", f"$.{key}"))
            return role, diagnostics
    if compatibility == HISTORICAL:
        if PUBLIC_EXCLUSIVE_KEYS.intersection(payload):
            diagnostics.append(Diagnostic("witness-role", "witness-role-historical-public-adapter", "07", "deprecated historical public_graph adapter selected; current artifacts require public-field-witness-v1"))
            return "public_graph", diagnostics
        if {"route_gradient", "burden_events", "coverage_proof"}.issubset(payload):
            diagnostics.append(Diagnostic("witness-role", "witness-role-historical-envelope-adapter", "08", "deprecated historical audit_envelope adapter selected; current artifacts require field-witness-envelope-v1"))
            return "audit_envelope", diagnostics
    shown = version if version is not None else schema
    return None, [Diagnostic("witness-role", "witness-role-unknown-discriminator", "07", f"unknown or missing witness discriminator {shown!r}", downstream_invalidated=("08",))]


def _historical_public_shape(payload: dict[str, Any]) -> list[str]:
    # This adapter classifies retained public graphs; it is not a second schema
    # master. Historical convergence/graph owners validate the version-specific
    # payload, including pre-NAR and submove-node dialects. Current promotion
    # always dispatches to field-witness.schema.json instead.
    required = {"B_LA", "B_MRP", "B_total"}
    missing = sorted(required - set(payload))
    return [f"$: historical public graph missing {key}" for key in missing]


def _historical_envelope_shape(payload: dict[str, Any]) -> list[str]:
    required = {"route_gradient", "burden_events", "field_diagnostics", "loopbreak", "reconstruction", "closure", "transfer_boundary", "register_deltas", "non_claims", "provenance", "coverage_proof"}
    return [f"$: historical audit envelope missing {key}" for key in sorted(required - set(payload))]


def artifact_binding_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["$: artifact binding must be an object"]
    errors: list[str] = []
    missing = sorted(BINDING_REQUIRED - set(payload))
    unknown = sorted(set(payload) - BINDING_REQUIRED)
    errors.extend(f"$: missing required property {key}" for key in missing)
    errors.extend(f"$: unknown property {key}" for key in unknown)
    if payload.get("schema_version") != "field-witness-artifact-binding-v1":
        errors.append("$.schema_version: must equal field-witness-artifact-binding-v1")
    for key in SHA_FIELDS:
        if key in payload and not isinstance(payload[key], str) or key in payload and re.fullmatch(r"[0-9a-f]{64}", str(payload[key])) is None:
            errors.append(f"$.{key}: must be lowercase 64-hex")
    if re.fullmatch(r"[0-9a-f]{40}", str(payload.get("source_commit"))) is None:
        errors.append("binding-source-commit: $.source_commit must be lowercase 40-hex")
    if payload.get("canonicalization") != "daee-canonical-json-v1":
        errors.append("binding-canonicalization: $.canonicalization must equal daee-canonical-json-v1")
    if payload.get("proof_class") not in {"stage08-structural-audit", "historical-structural-binding", "historical-public-only-binding"}:
        errors.append("binding-proof-class: $.proof_class must be stage08-structural-audit or a labeled historical structural proof class")
    if payload.get("binding_status") not in {"current_bound", "legacy_unbound", "known_contract_drift"}:
        errors.append("$.binding_status: invalid binding status")
    non_claims = payload.get("non_claims")
    joined_non_claims = " ".join(str(item).lower() for item in non_claims) if isinstance(non_claims, list) else ""
    if not isinstance(non_claims, list) or not non_claims or not all(token in joined_non_claims for token in ("semantic truth", "fresh generation")):
        errors.append("binding-non-claims: $.non_claims must explicitly deny semantic truth and fresh generation")
    return errors


def validate_role(payload: Any, expected_role: str, compatibility: str = CURRENT) -> list[Diagnostic]:
    actual_role, diagnostics = classify_role(payload, compatibility)
    if actual_role != expected_role:
        if actual_role == "public_graph" and expected_role == "audit_envelope":
            subcode = "witness-role-public-as-envelope"
        elif actual_role == "audit_envelope" and expected_role == "public_graph":
            subcode = "witness-role-envelope-as-public"
        else:
            subcode = "witness-role-mismatch"
        stage = ROLE_SPECS.get(expected_role, ROLE_SPECS["public_graph"]).stage
        return [Diagnostic("witness-role", subcode, stage, f"artifact role {actual_role!r} cannot satisfy expected role {expected_role!r}", downstream_invalidated=("08",) if stage == "07" else ())]
    if diagnostics and diagnostics[0].failure_subcode == "witness-role-competing-owner":
        return diagnostics
    if expected_role == "artifact_binding":
        shape_errors = artifact_binding_errors(payload)
    elif compatibility == HISTORICAL and payload.get(ROLE_SPECS[expected_role].discriminator_field) != ROLE_SPECS[expected_role].discriminator:
        shape_errors = _historical_public_shape(payload) if expected_role == "public_graph" else _historical_envelope_shape(payload)
    else:
        shape_errors = json_schema_errors(payload, load_schema_for_role(expected_role))
    if shape_errors:
        stage = ROLE_SPECS[expected_role].stage
        return [Diagnostic("witness-schema", f"witness-schema-{expected_role.replace('_', '-')}", stage, error, downstream_invalidated=("08",) if stage == "07" else ()) for error in shape_errors]
    return diagnostics


def apply_json_pointer_mutation(payload: Any, mutation: dict[str, Any]) -> Any:
    result = copy.deepcopy(payload)
    parts = [part.replace("~1", "/").replace("~0", "~") for part in str(mutation.get("path", "")).strip("/").split("/") if part]
    if not parts:
        raise ValueError("mutation path must identify a child")
    parent = result
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    leaf = parts[-1]
    op = mutation.get("op")
    if op == "remove":
        parent.pop(int(leaf)) if isinstance(parent, list) else parent.pop(leaf)
    elif op == "append":
        target = parent[int(leaf)] if isinstance(parent, list) else parent[leaf]
        if not isinstance(target, list):
            raise ValueError("append target must be an array")
        target.append(copy.deepcopy(mutation.get("value")))
    elif op in {"add", "replace"}:
        if isinstance(parent, list):
            parent[int(leaf)] = copy.deepcopy(mutation.get("value"))
        else:
            parent[leaf] = copy.deepcopy(mutation.get("value"))
    else:
        raise ValueError(f"unsupported mutation op {op!r}")
    return result


def _result(payload: Any, expected_role: str, compatibility: str) -> dict[str, Any]:
    diagnostics = validate_role(payload, expected_role, compatibility)
    blocking = [d for d in diagnostics if not d.failure_subcode.startswith("witness-role-historical-")]
    return {
        "status": "pass" if not blocking else "fail",
        "checker_id": "witness-artifact-roles",
        "expected_role": expected_role,
        "compatibility": compatibility,
        "diagnostics": [d.to_dict() for d in diagnostics],
        "non_claims": ["structural role validation does not establish semantic truth or uptake"],
    }


def self_test() -> int:
    public = {"schema_version": "public-field-witness-v1", "route_gradient": {}}
    collision = validate_role(public, "public_graph")
    checks = [
        ("public schema owner path", schema_path_for_role("public_graph") == ROOT / "schema" / "field-witness.schema.json"),
        ("envelope schema owner path", schema_path_for_role("audit_envelope") == ROOT / "schema" / "field-witness-envelope.schema.json"),
        ("binding remains subordinate", schema_path_for_role("artifact_binding") is None),
        ("competing owner rejected", bool(collision and collision[0].failure_subcode == "witness-role-competing-owner")),
        ("canonical hash deterministic", canonical_json_sha256({"b": 2, "a": 1}) == canonical_json_sha256({"a": 1, "b": 2})),
    ]
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    ok = all(passed for _, passed in checks)
    print(f"witness-artifact-roles self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--expected-role", choices=sorted(ROLE_SPECS))
    parser.add_argument("--compatibility", choices=[CURRENT, HISTORICAL], default=CURRENT)
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.artifact is None or args.expected_role is None:
        parser.error("--artifact and --expected-role are required")
    payload = json.loads(args.artifact.read_text(encoding="utf-8"))
    result = _result(payload, args.expected_role, args.compatibility)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
