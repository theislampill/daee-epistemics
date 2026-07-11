#!/usr/bin/env python3
"""Pure Stage04-Stage07 activation/lifecycle projection contract.

Stage04 execution and Stage05 lifecycle are the frozen source. Stage06 and
Stage07 are lossless projections; they may not add or repair owners,
operations, resultants, burdens, closure, or semantic body content.
"""
from __future__ import annotations

import hashlib
import json
import copy
from pathlib import Path
from typing import Any

from witness_artifact_roles import json_schema_errors

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "stage-projection.schema.json"


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def activation_lifecycle_projection(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "activations": payload.get("stage04", {}).get("activations", []),
        "burden_cycles": payload.get("stage05", {}).get("burden_cycles", []),
        "provenance_event_dag": payload.get("stage05", {}).get("provenance_event_dag"),
        "noetic_dependency_graph": payload.get("stage05", {}).get("noetic_dependency_graph"),
        "closure_projection": payload.get("stage05", {}).get("closure_projection"),
    }


def activation_lifecycle_fingerprint(payload: dict[str, Any]) -> str:
    return canonical_json_sha256(activation_lifecycle_projection(payload))


def stage04_projection_sha256(payload: dict[str, Any]) -> str:
    return canonical_json_sha256({"activations": payload.get("stage04", {}).get("activations", [])})


def normalized_release_projection(payload: dict[str, Any], stage_name: str) -> dict[str, Any]:
    stage = payload.get(stage_name, {})
    return {
        "activations": stage.get("activations", []),
        "burden_cycles": stage.get("burden_cycles", []),
        "closure_projection": stage.get("closure_projection"),
        "normalized_activation_record": stage.get("normalized_activation_record"),
    }


def release_projection_sha256(payload: dict[str, Any], stage_name: str) -> str:
    if stage_name not in {"stage06", "stage07"}:
        raise ValueError("release projection hash is defined only for stage06 and stage07")
    return canonical_json_sha256(normalized_release_projection(payload, stage_name))


def _diagnostic(subcode: str, stage: str, message: str, path: str) -> dict[str, Any]:
    return {
        "failure_class": "projection-parity",
        "failure_subcode": subcode,
        "earliest_stage": stage,
        "downstream_invalidated": ["07", "08"] if stage == "06" else ["08"],
        "message": message,
        "path": path,
    }


def _first_row_difference(expected: list[Any], actual: list[Any]) -> tuple[int, str, Any, Any] | None:
    for index, (left, right) in enumerate(zip(expected, actual)):
        if left == right:
            continue
        if isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(set(left) | set(right)):
                if left.get(key) != right.get(key):
                    return index, key, left.get(key), right.get(key)
        return index, "$row", left, right
    return None


def _nar_rows(activations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = ("ordinal", "obligation_id", "body_ref", "burden_id", "owner_id", "operation", "resultant_sha256")
    return [{key: row.get(key) for key in keys} for row in activations]


def _graph_cycle(graph: Any) -> bool:
    if not isinstance(graph, dict):
        return False
    nodes = {str(node) for node in graph.get("nodes", [])}
    adjacency = {node: [] for node in nodes}
    for edge in graph.get("edges", []):
        if isinstance(edge, dict):
            adjacency.setdefault(str(edge.get("from")), []).append(str(edge.get("to")))
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in adjacency.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in adjacency)


def projection_diagnostics(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return [_diagnostic("projection-parity-schema", "06", "projection artifact must be an object", "$")]
    if payload.get("schema") == "daee-stage-projection-compatibility-case-v1":
        if payload.get("compatibility") == "historical-stage06-local" and payload.get("not_release_output") is True and str(payload.get("stop_after_stage")) == "06":
            return []
        return [_diagnostic("projection-parity-legacy-scope", "06", "historical shorthand must be Stage06-local and explicitly non-release", "$")]
    stage06 = payload.get("stage06", {})
    stage07 = payload.get("stage07", {})
    if isinstance(stage06, dict) and not isinstance(stage06.get("normalized_activation_record"), dict):
        return [_diagnostic("projection-parity-boolean-nar-release", "06", "release-bearing Stage06 requires a structured NAR object", "$.stage06.normalized_activation_record")]
    if isinstance(stage07, dict) and "semantic_body_text" in stage07:
        return [_diagnostic("projection-parity-body-text", "07", "Stage07 cannot add semantic body text absent from Stage04", "$.stage07.semantic_body_text")]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_errors = json_schema_errors(payload, schema)
    if schema_errors:
        return [_diagnostic("projection-parity-schema", "06", schema_errors[0], "$")]

    stage04 = payload["stage04"]
    stage05 = payload["stage05"]
    expected_activations = stage04["activations"]
    expected_cycles = stage05["burden_cycles"]
    expected_closure = stage05["closure_projection"]
    fingerprint = activation_lifecycle_fingerprint(payload)

    for name, stage in (("stage04", "06"), ("stage05", "06"), ("stage06", "06"), ("stage07", "07")):
        actual = payload[name]["activation_lifecycle_fingerprint_sha256"]
        if actual != fingerprint:
            return [_diagnostic("projection-parity-lifecycle-fingerprint", stage, f"{name.title()} fingerprint {actual} does not match canonical activation/lifecycle fingerprint {fingerprint}", f"$.{name}.activation_lifecycle_fingerprint_sha256")]

    stage06_activations = stage06["activations"]
    if len(stage06_activations) != len(expected_activations):
        return [_diagnostic("projection-parity-activation-count", "06", "Stage06 activation count differs from executed Stage04 obligations", "$.stage06.activations")]
    diff = _first_row_difference(expected_activations, stage06_activations)
    if diff:
        index, key, expected, actual = diff
        return [_diagnostic("projection-parity-owner-operation" if key in {"owner_id", "operation"} else "projection-parity-activation-identity", "06", f"Stage06 activation {index} field {key} differs: {expected!r} != {actual!r}", f"$.stage06.activations[{index}].{key}")]
    if stage06["burden_cycles"] != expected_cycles:
        return [_diagnostic("projection-parity-lifecycle", "06", "Stage06 lifecycle differs from frozen Stage05 burden cycles", "$.stage06.burden_cycles")]
    if stage06["closure_projection"] != expected_closure:
        return [_diagnostic("projection-parity-closure", "06", "Stage06 closure projection differs from frozen lifecycle state", "$.stage06.closure_projection")]
    expected_nar = _nar_rows(expected_activations)
    nar06 = stage06["normalized_activation_record"]["per_activation"]
    if len(nar06) != len(expected_nar) or nar06 != expected_nar:
        return [_diagnostic("projection-parity-structured-cardinality-loss", "06", "Stage06 structured NAR cardinality or identity differs from executed activations", "$.stage06.normalized_activation_record.per_activation")]

    stage07_activations = stage07["activations"]
    if len(stage07_activations) != len(expected_activations):
        return [_diagnostic("projection-parity-activation-count", "07", "Stage07 activation count adds or drops an executed activation", "$.stage07.activations")]
    diff = _first_row_difference(expected_activations, stage07_activations)
    if diff:
        index, key, expected, actual = diff
        if key in {"owner_id", "operation"}:
            subcode = "projection-parity-owner-operation"
        elif key == "resultant_sha256":
            subcode = "projection-parity-resultant"
        elif key == "burden_id":
            subcode = "projection-parity-burden"
        elif key == "semantic_body_sha256":
            subcode = "projection-parity-body-text"
        else:
            subcode = "projection-parity-activation-identity"
        return [_diagnostic(subcode, "07", f"Stage07 activation {index} field {key} differs: {expected!r} != {actual!r}", f"$.stage07.activations[{index}].{key}")]
    if len(stage07["burden_cycles"]) != len(expected_cycles):
        return [_diagnostic("projection-parity-burden-count", "07", "Stage07 burden count adds or drops a frozen lifecycle cycle", "$.stage07.burden_cycles")]
    if stage07["burden_cycles"] != expected_cycles:
        diff = _first_row_difference(expected_cycles, stage07["burden_cycles"])
        detail = f" at row {diff[0]} field {diff[1]}" if diff else ""
        return [_diagnostic("projection-parity-lifecycle", "07", f"Stage07 lifecycle{detail} differs from frozen Stage05/Stage06 lifecycle", "$.stage07.burden_cycles")]
    if stage07["closure_projection"] != expected_closure:
        return [_diagnostic("projection-parity-closure", "07", "Stage07 closure projection differs from frozen lifecycle state", "$.stage07.closure_projection")]
    nar07 = stage07["normalized_activation_record"]["per_activation"]
    if len(nar07) != len(expected_nar) or nar07 != expected_nar:
        return [_diagnostic("projection-parity-structured-cardinality-loss", "07", "Stage07 structured NAR cardinality or identity differs from Stage06 activations", "$.stage07.normalized_activation_record.per_activation")]
    body_hashes = stage07["semantic_body_hashes"]
    expected_hashes = {row["body_ref"]: row["semantic_body_sha256"] for row in expected_activations}
    if body_hashes != expected_hashes:
        return [_diagnostic("projection-parity-body-text", "07", "Stage07 semantic body hashes differ from Stage04 proof-bearing body hashes", "$.stage07.semantic_body_hashes")]
    if stage07["T_lang"].get("projection") != "partial_coupling" or stage07["T_lang"].get("uptake_guaranteed") is not False:
        return [_diagnostic("projection-parity-t-lang-overclaim", "07", "T_lang must remain partial coupling with non-guaranteed uptake", "$.stage07.T_lang")]
    if _graph_cycle(stage05.get("provenance_event_dag")):
        return [_diagnostic("projection-parity-event-dag-cycle", "06", "provenance event DAG must be acyclic; the noetic dependency graph is distinct", "$.stage05.provenance_event_dag")]
    return []


def self_test_payload() -> dict[str, Any]:
    return json.loads((ROOT / "tests" / "stage-projection-parity" / "valid" / "lossless-stage06-stage07.json").read_text(encoding="utf-8"))


def self_test() -> int:
    payload = self_test_payload()
    noetic_cycle = copy.deepcopy(payload)
    noetic_cycle["stage05"]["noetic_dependency_graph"]["edges"] = [{"from": "B1", "to": "B1"}]
    noetic_fingerprint = activation_lifecycle_fingerprint(noetic_cycle)
    for stage_name in ("stage04", "stage05", "stage06", "stage07"):
        noetic_cycle[stage_name]["activation_lifecycle_fingerprint_sha256"] = noetic_fingerprint
    checks = [
        ("canonical fingerprint is lowercase 64-hex", len(activation_lifecycle_fingerprint(payload)) == 64),
        ("lossless fixture passes", projection_diagnostics(payload) == []),
        ("noetic dependency cycle is not conflated with event DAG", projection_diagnostics(noetic_cycle) == []),
    ]
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    ok = all(passed for _, passed in checks)
    print(f"stage-projection-contract self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(self_test())
