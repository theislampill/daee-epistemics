#!/usr/bin/env python3
"""Validate witness roles, current graph/envelope/binding triplets, and fixtures."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from closure_witness_lib import public_graph_integrity_diagnostics, terminal_public_order_diagnostics
from witness_artifact_roles import (
    CURRENT,
    HISTORICAL,
    apply_json_pointer_mutation,
    artifact_binding_errors,
    canonical_json_sha256,
    classify_role,
    json_schema_errors,
    validate_role,
)
from stage_projection_contract import (
    activation_lifecycle_fingerprint,
    projection_diagnostics,
    release_projection_sha256,
    stage04_projection_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "witness-artifact-roles"
EXPECTATION_SCHEMA = ROOT / "schema" / "negative-fixture-expectation.schema.json"


def _diagnostic(failure_class: str, subcode: str, stage: str, message: str, downstream: list[str] | None = None) -> dict[str, Any]:
    return {"failure_class": failure_class, "failure_subcode": subcode, "earliest_stage": stage, "downstream_invalidated": downstream or [], "message": message}


def _role_dicts(payload: Any, expected_role: str, compatibility: str = CURRENT) -> list[dict[str, Any]]:
    return [item.to_dict() for item in validate_role(payload, expected_role, compatibility)]


def triplet_diagnostics(graph: Any, envelope: Any, binding: Any, projection: Any | None = None) -> list[dict[str, Any]]:
    diagnostics = _role_dicts(graph, "public_graph", CURRENT)
    if diagnostics:
        return diagnostics
    diagnostics = public_graph_integrity_diagnostics(graph, compatibility=CURRENT)
    if diagnostics:
        return diagnostics
    diagnostics = _role_dicts(envelope, "audit_envelope", CURRENT)
    if diagnostics:
        return diagnostics
    binding_role, binding_role_diagnostics = classify_role(binding, CURRENT)
    if binding_role != "artifact_binding":
        return [item.to_dict() for item in binding_role_diagnostics]
    binding_errors = artifact_binding_errors(binding)
    if binding_errors:
        error = binding_errors[0]
        if "binding-source-commit" in error:
            subcode = "witness-binding-source-commit"
        elif "binding-canonicalization" in error:
            subcode = "witness-binding-canonicalization"
        elif "binding-proof-class" in error:
            subcode = "witness-binding-proof-class"
        elif "binding-non-claims" in error:
            subcode = "witness-binding-non-claims"
        else:
            subcode = "witness-binding-shape"
        return [_diagnostic("witness-binding", subcode, "08", error)]
    if binding.get("binding_status") != "current_bound":
        return [_diagnostic("witness-binding", "witness-binding-status", "08", "current triplet binding_status must equal current_bound")]
    if binding.get("proof_class") != "stage08-structural-audit":
        return [_diagnostic("witness-binding", "witness-binding-proof-class", "08", "current triplet proof_class must equal stage08-structural-audit")]
    embedded = envelope.get("artifact_binding") if isinstance(envelope, dict) else None
    if embedded != binding:
        return [_diagnostic("witness-binding", "witness-binding-embedded-record", "08", "audit envelope embedded binding does not equal the subordinate binding record")]
    graph_hash = canonical_json_sha256(graph)
    if binding.get("public_field_witness_sha256") != graph_hash:
        return [_diagnostic("witness-binding", "witness-binding-public-hash", "08", f"public graph hash {graph_hash} does not match binding {binding.get('public_field_witness_sha256')}")]
    envelope_projection = copy.deepcopy(envelope)
    envelope_projection.pop("artifact_binding", None)
    envelope_hash = canonical_json_sha256(envelope_projection)
    if binding.get("audit_envelope_projection_sha256") != envelope_hash:
        return [_diagnostic("witness-binding", "witness-binding-envelope-hash", "08", f"audit envelope projection hash {envelope_hash} does not match binding")]
    fingerprint = graph.get("activation_lifecycle_fingerprint_sha256")
    if binding.get("activation_lifecycle_fingerprint_sha256") != fingerprint:
        return [_diagnostic("witness-binding", "witness-binding-lifecycle-fingerprint", "08", "graph and binding activation/lifecycle fingerprints differ")]
    if binding.get("stage06_projection_sha256") != binding.get("stage07_projection_sha256"):
        return [_diagnostic("witness-binding", "witness-binding-stage-projection", "08", "binding Stage06 and Stage07 projection hashes differ")]
    if projection is None:
        return [_diagnostic("witness-binding", "witness-binding-projection-missing", "08", "current triplet must join the actual Stage04/06/07 projection artifact")]
    projection_errors = projection_diagnostics(projection)
    if projection_errors:
        return [_diagnostic("witness-binding", "witness-binding-projection-invalid", "08", f"actual projection artifact is invalid: {projection_errors[0]['message']}")]
    actual_fingerprint = activation_lifecycle_fingerprint(projection)
    if binding.get("activation_lifecycle_fingerprint_sha256") != actual_fingerprint or graph.get("activation_lifecycle_fingerprint_sha256") != actual_fingerprint:
        return [_diagnostic("witness-binding", "witness-binding-lifecycle-fingerprint", "08", "graph and binding fingerprint must join the actual projection artifact")]
    actual_stage04 = stage04_projection_sha256(projection)
    if binding.get("stage04_projection_sha256") != actual_stage04:
        return [_diagnostic("witness-binding", "witness-binding-stage04-projection", "08", f"Stage04 projection hash {binding.get('stage04_projection_sha256')} does not match actual projection artifact {actual_stage04}")]
    actual_stage06 = release_projection_sha256(projection, "stage06")
    if binding.get("stage06_projection_sha256") != actual_stage06:
        return [_diagnostic("witness-binding", "witness-binding-stage06-projection", "08", f"Stage06 projection hash {binding.get('stage06_projection_sha256')} does not match actual projection artifact {actual_stage06}")]
    actual_stage07 = release_projection_sha256(projection, "stage07")
    if binding.get("stage07_projection_sha256") != actual_stage07:
        return [_diagnostic("witness-binding", "witness-binding-stage07-projection", "08", f"Stage07 projection hash {binding.get('stage07_projection_sha256')} does not match actual projection artifact {actual_stage07}")]
    return []


def _load_triplet(directory: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return tuple(json.loads((directory / name).read_text(encoding="utf-8")) for name in ("public-graph.json", "audit-envelope.json", "artifact-binding.json"))  # type: ignore[return-value]


def _load_projection_ref(directory: Path) -> dict[str, Any]:
    ref = json.loads((directory / "projection-ref.json").read_text(encoding="utf-8"))
    return json.loads((ROOT / ref["path"]).read_text(encoding="utf-8"))


def validate_fixture(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if path.suffix.lower() == ".md":
        diagnostics = terminal_public_order_diagnostics(path.read_text(encoding="utf-8"))
        return {"status": "pass" if not diagnostics else "fail", "checker_id": "witness-artifact-roles", "fixture": str(path.relative_to(ROOT)).replace("\\", "/"), "compatibility": CURRENT, "diagnostics": diagnostics}
    raw = json.loads(path.read_text(encoding="utf-8"))
    schema = raw.get("schema") if isinstance(raw, dict) else None
    compatibility = str(raw.get("compatibility", CURRENT)) if isinstance(raw, dict) else CURRENT
    if schema == "daee-witness-artifact-role-case-v1":
        payload = json.loads((ROOT / raw["base"]).read_text(encoding="utf-8"))
        diagnostics = _role_dicts(payload, raw["expected_role"], compatibility)
    elif schema == "daee-witness-artifact-mutation-v1":
        base = json.loads((ROOT / raw["base"]).read_text(encoding="utf-8"))
        payload = apply_json_pointer_mutation(base, raw["mutation"])
        diagnostics = _role_dicts(payload, raw["expected_role"], compatibility)
        if not diagnostics and raw["expected_role"] == "public_graph":
            diagnostics = public_graph_integrity_diagnostics(payload, compatibility=compatibility)
    elif schema in {"daee-witness-artifact-triplet-mutation-v1", "daee-witness-artifact-triplet-mutations-v1"}:
        directory = ROOT / raw["base"]
        graph, envelope, binding = _load_triplet(directory)
        targets = {"public-graph.json": graph, "audit-envelope.json": envelope, "artifact-binding.json": binding}
        mutated = targets[raw["target"]]
        for mutation in raw.get("mutations", [raw.get("mutation")]):
            mutated = apply_json_pointer_mutation(mutated, mutation)
        targets[raw["target"]] = mutated
        if raw["target"] == "artifact-binding.json":
            targets["audit-envelope.json"]["artifact_binding"] = copy.deepcopy(mutated)
        diagnostics = triplet_diagnostics(targets["public-graph.json"], targets["audit-envelope.json"], targets["artifact-binding.json"], _load_projection_ref(directory))
    else:
        expected_role = "public_graph"
        diagnostics = _role_dicts(raw, expected_role, compatibility)
        blocking = [item for item in diagnostics if not item.get("failure_subcode", "").startswith("witness-role-historical-")]
        if not blocking:
            diagnostics = public_graph_integrity_diagnostics(raw, compatibility=compatibility)
        else:
            diagnostics = blocking
    return {"status": "pass" if not diagnostics else "fail", "checker_id": "witness-artifact-roles", "fixture": str(path.relative_to(ROOT)).replace("\\", "/"), "compatibility": compatibility, "diagnostics": diagnostics}


def _expectation_errors(fixture: Path, result: dict[str, Any]) -> list[str]:
    expectation_path = fixture.with_name(fixture.stem + ".expectation.json")
    if not expectation_path.is_file():
        return [f"{fixture}: missing same-stem expectation {expectation_path.name}"]
    expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
    expectation_schema = json.loads(EXPECTATION_SCHEMA.read_text(encoding="utf-8"))
    errors = [f"{expectation_path}: {error}" for error in json_schema_errors(expectation, expectation_schema)]
    if expectation.get("fixture") != fixture.name:
        errors.append(f"{expectation_path}: fixture must equal {fixture.name}")
    if expectation.get("expected_checker_id") != "witness-artifact-roles":
        errors.append(f"{expectation_path}: expected_checker_id must equal witness-artifact-roles")
    if expectation.get("expected_exit_category") != "structural-rejection" or expectation.get("expected_exit_code") != 1:
        errors.append(f"{expectation_path}: expected exit must be structural-rejection/1")
    diagnostics = result.get("diagnostics", [])
    if result.get("status") != "fail" or not diagnostics:
        return errors + [f"{fixture}: expected-invalid fixture unexpectedly passed"]
    diagnostic = diagnostics[0]
    for key, expected in {
        "failure_class": expectation.get("expected_failure_class"),
        "failure_subcode": expectation.get("expected_failure_subcode"),
        "earliest_stage": expectation.get("expected_earliest_stage"),
        "downstream_invalidated": expectation.get("expected_downstream_invalidated"),
    }.items():
        if diagnostic.get(key) != expected:
            errors.append(f"{fixture}: expected {key}={expected!r}, got {diagnostic.get(key)!r}")
    rendered = json.dumps(diagnostic, sort_keys=True, ensure_ascii=False)
    for marker in expectation.get("required_diagnostic_markers", []):
        if str(marker).lower() not in rendered.lower():
            errors.append(f"{fixture}: required diagnostic marker {marker!r} missing")
    for artifact in expectation.get("forbidden_artifacts", []):
        if (fixture.parent / artifact).exists():
            errors.append(f"{fixture}: forbidden artifact exists: {artifact}")
    return errors


def run_fixture_suite(root: Path = FIXTURE_ROOT) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {"current_triplets": 0, "valid": 0, "historical": 0, "historical_envelopes": 0, "invalid": 0}
    triplet_dir = root / "valid" / "current-triplet"
    graph, envelope, binding = _load_triplet(triplet_dir)
    found = triplet_diagnostics(graph, envelope, binding, _load_projection_ref(triplet_dir))
    if found:
        errors.append(f"{triplet_dir}: current triplet invalid: {json.dumps(found, ensure_ascii=False)}")
    else:
        counts["current_triplets"] += 1
    for path in sorted((root / "valid").glob("*.md")):
        result = validate_fixture(path)
        if result["status"] != "pass":
            errors.append(f"{path}: expected valid: {json.dumps(result['diagnostics'], ensure_ascii=False)}")
        else:
            counts["valid"] += 1
    for path in sorted((root / "valid" / "historical-compatibility").glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        diagnostics = _role_dicts(raw, "public_graph", HISTORICAL)
        blocking = [item for item in diagnostics if not item.get("failure_subcode", "").startswith("witness-role-historical-")]
        blocking.extend(public_graph_integrity_diagnostics(raw, compatibility=HISTORICAL))
        if blocking:
            errors.append(f"{path}: historical compatibility fixture invalid: {json.dumps(blocking, ensure_ascii=False)}")
        else:
            counts["historical"] += 1
    for path in sorted((ROOT / "tests" / "live-witness-fixtures" / "valid").glob("*.field_witness.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        diagnostics = _role_dicts(raw, "audit_envelope", HISTORICAL)
        blocking = [item for item in diagnostics if not item.get("failure_subcode", "").startswith("witness-role-historical-")]
        if blocking:
            errors.append(f"{path}: historical audit-envelope compatibility fixture invalid: {json.dumps(blocking, ensure_ascii=False)}")
        else:
            counts["historical_envelopes"] += 1
    for path in sorted((root / "invalid").iterdir()):
        if not path.is_file() or path.name.endswith(".expectation.json") or path.suffix.lower() not in {".json", ".md"}:
            continue
        result = validate_fixture(path)
        errors.extend(_expectation_errors(path, result))
        if result["status"] == "fail":
            counts["invalid"] += 1
    for expectation in (root / "invalid").glob("*.expectation.json"):
        payload = json.loads(expectation.read_text(encoding="utf-8"))
        fixture_name = payload.get("fixture", "")
        if not fixture_name or not (expectation.parent / fixture_name).is_file():
            errors.append(f"{expectation}: expectation has no same-stem fixture")
    return errors, counts


def self_test() -> int:
    errors, counts = run_fixture_suite()
    if errors:
        print("field-witness binding self-test: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("field-witness binding self-test: PASS")
    print(json.dumps(counts, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--graph", type=Path)
    parser.add_argument("--envelope", type=Path)
    parser.add_argument("--binding", type=Path)
    parser.add_argument("--projection", type=Path)
    parser.add_argument("--fixture-root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if any((args.graph, args.envelope, args.binding)):
        if not all((args.graph, args.envelope, args.binding)):
            parser.error("--graph, --envelope, and --binding must be supplied together")
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
        binding = json.loads(args.binding.read_text(encoding="utf-8"))
        projection = json.loads(args.projection.read_text(encoding="utf-8")) if args.projection else None
        diagnostics = triplet_diagnostics(graph, envelope, binding, projection)
        result = {"status": "pass" if not diagnostics else "fail", "checker_id": "witness-artifact-roles", "role": "current-triplet", "diagnostics": diagnostics, "non_claims": ["structural binding does not establish semantic truth or uptake"]}
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return 0 if not diagnostics else 1
    errors, counts = run_fixture_suite(args.fixture_root)
    if args.explain:
        print(json.dumps({"status": "pass" if not errors else "fail", "checker_id": "witness-artifact-roles", "counts": counts, "errors": errors}, sort_keys=True, ensure_ascii=False))
    elif errors:
        print("field-witness binding: FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print("field-witness binding: PASS")
        print(json.dumps(counts, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
