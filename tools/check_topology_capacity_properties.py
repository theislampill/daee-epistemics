#!/usr/bin/env python3
"""Independently extract and verify A15 topology conservation properties."""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import re
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any, Iterable

from generate_topology_capacity_cases import (
    MANIFEST_FILE,
    PROJECTION_FILE,
    PUBLIC_OUTPUT_FILE,
    SPEC_FILE,
    STAGE_FILES,
    STATE_FILE,
    WITNESS_FILE,
    directory_digest,
    generate_case,
    refresh_case_bindings,
)
from topology_capacity_lib import canonical_bytes, canonical_sha256, validate_spec


STAGES = tuple(f"{number:02d}" for number in range(1, 9))
KNOWN_ROUTE_KINDS = {"direct", "held-activation", "generated", "preempted", "loopbreak"}
IDENTITY_TOKEN_RE = re.compile(
    r"\b(?:obs|pressure|candidate|hyperedge|burden|generated|preempted|obligation|owner|register|body|route|cycle|event|reread)-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
FILLER_RE = re.compile(r"\b(?:neutral\s+)?filler\b", re.IGNORECASE)
POSITIVE_RELATIONS = (
    "alpha-rename",
    "permutation",
    "split-conservation",
    "merge-with-proof",
    "irrelevant-filler",
    "payload-length",
    "valid-hold",
    "generated-child",
    "preempt-resultant",
)
CHECKER_SAME_FUNCTION_PROOF = {
    "tau_relation": "same",
    "source_frame_relation": "same",
    "claim_cluster_relation": "same",
    "register_transition_relation": "compatible",
    "owner_operation_relation": "compatible",
    "restoration_vector_relation": "same",
    "collapse_dependency_relation": "same",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _checker_stable_id(seed: int, namespace: str, ordinal: int) -> str:
    digest = hashlib.sha256(f"{seed}:{namespace}:{ordinal}".encode("ascii")).hexdigest()[:12]
    return f"{namespace}-{digest}"


def _checker_ids(seed: int, namespace: str, count: int) -> list[str]:
    return [_checker_stable_id(seed, namespace, ordinal) for ordinal in range(1, count + 1)]


def _checker_canonical_sha256(value: Any) -> str:
    payload = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _checker_partition_decisions(
    spec: dict[str, Any], pressures: list[str], canonical_baseline: list[str]
) -> list[dict[str, Any]]:
    rows = []
    source_fields = (
        "authorization_key",
        "relation_type",
        "pressure_ordinals",
        "receiving_burden_ordinals",
        "owner_ordinal",
        "operation",
        "register_ordinal",
        "evidence_identity",
        "same_function_proof",
    )
    coverage = []
    for index, source in enumerate(spec.get("partition_authorizations", []), 1):
        source_payload = {field: copy.deepcopy(source[field]) for field in source_fields}
        if source.get("authorization_sha256") != _checker_canonical_sha256(source_payload):
            raise ValueError("checker-derived partition source hash mismatch")
        coverage.extend(source["pressure_ordinals"])
        pressure_ids = [pressures[item - 1] for item in source["pressure_ordinals"]]
        burden_ids = [
            canonical_baseline[item - 1]
            for item in source["receiving_burden_ordinals"]
        ]
        payload = {
            "decision_id": _checker_stable_id(spec["seed"], "partition", index),
            "source_authorization_key": source["authorization_key"],
            "source_authorization_sha256": source["authorization_sha256"],
            "relation_type": source["relation_type"],
            "pressure_ids": pressure_ids,
            "receiving_burden_ids": burden_ids,
            "owner_id": _checker_stable_id(spec["seed"], "owner", source["owner_ordinal"]),
            "operation": source["operation"],
            "register_id": _checker_stable_id(spec["seed"], "register", source["register_ordinal"]),
            "evidence_identity": source["evidence_identity"],
            "same_function_proof": copy.deepcopy(source["same_function_proof"]),
            "pressure_to_burden": [
                {
                    "pressure_id": pressure_id,
                    "burden_id": burden_ids[0] if len(burden_ids) == 1 else burden_ids[position],
                }
                for position, pressure_id in enumerate(pressure_ids)
            ],
        }
        payload["authorization_sha256"] = _checker_canonical_sha256(payload)
        rows.append(payload)
    if sorted(coverage) != list(range(1, len(pressures) + 1)):
        raise ValueError("checker-derived pressure partition coverage mismatch")
    return rows


def _checker_shared_authorizations(
    spec: dict[str, Any],
    pressures: list[str],
    canonical_baseline: list[str],
    partition_decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    partition_by_key = {
        row["source_authorization_key"]: row for row in partition_decisions
    }
    source_fields = (
        "authorization_key",
        "upstream_partition_keys",
        "pressure_ordinals",
        "receiving_burden_ordinals",
        "owner_ordinal",
        "operation",
        "register_ordinal",
        "evidence_identity",
        "same_function_proof",
    )
    rows = []
    for index, source in enumerate(spec.get("shared_operation_authorizations", []), 1):
        source_payload = {field: copy.deepcopy(source[field]) for field in source_fields}
        if source.get("authorization_sha256") != _checker_canonical_sha256(source_payload):
            raise ValueError("checker-derived shared source hash mismatch")
        upstream = [partition_by_key[key] for key in source["upstream_partition_keys"]]
        payload = {
            "shared_authorization_id": _checker_stable_id(spec["seed"], "sharedauth", index),
            "source_authorization_key": source["authorization_key"],
            "source_authorization_sha256": source["authorization_sha256"],
            "upstream_partition_decision_ids": [row["decision_id"] for row in upstream],
            "upstream_partition_authorization_sha256": [row["authorization_sha256"] for row in upstream],
            "pressure_ids": [pressures[item - 1] for item in source["pressure_ordinals"]],
            "receiving_burden_ids": [canonical_baseline[item - 1] for item in source["receiving_burden_ordinals"]],
            "owner_id": _checker_stable_id(spec["seed"], "owner", source["owner_ordinal"]),
            "operation": source["operation"],
            "register_id": _checker_stable_id(spec["seed"], "register", source["register_ordinal"]),
            "evidence_identity": source["evidence_identity"],
            "same_function_proof": copy.deepcopy(source["same_function_proof"]),
        }
        payload["authorization_sha256"] = _checker_canonical_sha256(payload)
        rows.append(payload)
    return rows


def _checker_dependency_edges(shape: str, burdens: list[str]) -> list[list[str]]:
    if shape == "noetic-cycle-loopbreak" and burdens:
        return [[burdens[index], burdens[(index + 1) % len(burdens)]] for index in range(len(burdens))]
    if len(burdens) < 2 or shape in {"independent", "pre-emption"}:  # topology-constructor-arity
        return []
    if shape in {"chain", "generated-chain", "held-activation"}:
        return [[burdens[index], burdens[index + 1]] for index in range(len(burdens) - 1)]
    if shape in {"fan-out", "generated-fan-out"}:
        return [[burdens[0], item] for item in burdens[1:]]
    if shape == "fan-in":
        return [[item, burdens[-1]] for item in burdens[:-1]]
    if shape == "diamond" and len(burdens) >= 4:  # topology-constructor-arity
        return [[burdens[0], burdens[1]], [burdens[0], burdens[2]], [burdens[1], burdens[3]], [burdens[2], burdens[3]]]
    midpoint = max(1, len(burdens) // 2)
    return [[burdens[index], burdens[index + 1]] for index in range(midpoint - 1)] + [[burdens[0], item] for item in burdens[midpoint:]]


def _checker_expected_from_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Checker-owned derivation; it does not consume producer manifest logic."""
    spec = validate_spec(spec)
    seed = spec["seed"]
    dims = spec["dimensions"]
    observations = _checker_ids(seed, "obs", dims["input_observations"])
    pressures = _checker_ids(seed, "pressure", dims["input_pressures"])
    candidates = _checker_ids(seed, "candidate", dims["candidate_states"])
    hyperedges = _checker_ids(seed, "hyperedge", dims["candidate_hyperedges"])
    canonical_baseline = _checker_ids(seed, "burden", dims["baseline_burdens"])
    declaration_order = spec.get(
        "baseline_declaration_order",
        list(range(1, dims["baseline_burdens"] + 1)),
    )
    baseline = [canonical_baseline[index - 1] for index in declaration_order]
    generated = _checker_ids(seed, "generated", dims["generated_burdens"])
    preempted = _checker_ids(seed, "preempted", dims["preempted_candidates"])
    all_burdens = baseline + generated
    canonical_all_burdens = canonical_baseline + generated
    canonical_cycle_ids = _checker_ids(seed, "cycle", len(canonical_all_burdens))
    cycle_by_burden = dict(zip(canonical_all_burdens, canonical_cycle_ids))
    cycle_ids = [cycle_by_burden[burden] for burden in all_burdens]
    held = canonical_baseline[-dims["held_baseline_burdens"] :] if dims["held_baseline_burdens"] else []
    generation = []
    for index, child in enumerate(generated):
        if index < dims["generation_depth"]:
            parent = canonical_baseline[0] if index == 0 else generated[index - 1]
        elif dims["generation_depth"] <= 1:
            parent = canonical_baseline[0]
        else:
            parent = generated[dims["generation_depth"] - 2]
        parent_depth = next((row["depth"] for row in generation if row["burden_id"] == parent), 0)
        generation.append({"burden_id": child, "parent_id": parent, "parent_cycle_id": cycle_by_burden[parent], "cycle_id": cycle_by_burden[child], "depth": parent_depth + 1})
    generation_by_burden = {row["burden_id"]: row for row in generation}
    cycles = []
    event_ordinal = 0
    event_ids = []
    cycle_events = []
    for index, burden in enumerate(all_burdens):
        generated_row = generation_by_burden.get(burden)
        origin = "B_MRP" if generated_row else "B_LA"
        activated = burden in held
        kinds = (
            ("instantiate", "stage03-reentry", "execute", "land", "reread")
            if origin == "B_MRP"
            else ("hold", "hold-disposition", "activate", "stage03-reentry", "execute", "land", "reread")
            if activated
            else ("route", "execute", "land", "reread")
        )
        ids = []
        for kind in kinds:
            event_ordinal += 1
            event_id = _checker_stable_id(seed, "event", event_ordinal)
            ids.append(event_id)
            event_ids.append(event_id)
            cycle_events.append({"event_id": event_id, "cycle_id": cycle_ids[index], "kind": kind, "ordinal": event_ordinal})
        cycles.append(
            {
                "cycle_id": cycle_ids[index],
                "burden_id": burden,
                "origin": origin,
                "parent_cycle_id": generated_row["parent_cycle_id"] if generated_row else None,
                "generation_depth": generated_row["depth"] if generated_row else 0,
                "activated_from_hold": activated,
                "event_ids": ids,
                "event_kinds": list(kinds),
            }
        )
    obligations_by_burden: dict[str, list[dict[str, Any]]] = {}
    for burden_index, burden in enumerate(canonical_all_burdens):
        rows = []
        for ordinal in range(1, dims["submoves_per_burden"] + 1):
            flat = burden_index * dims["submoves_per_burden"] + ordinal
            rows.append(
                {
                    "obligation_id": _checker_stable_id(seed, "obligation", flat),
                    "burden_id": burden,
                    "pressure_id": pressures[burden_index % len(pressures)],
                    "owner_id": _checker_stable_id(seed, "owner", ordinal),
                    "register_id": _checker_stable_id(seed, "register", ordinal),
                    "operation": f"neutral-operation-{ordinal}",
                    "body_ref": _checker_stable_id(seed, "body", flat),
                    "cycle_id": cycle_by_burden[burden],
                }
            )
        obligations_by_burden[burden] = rows
    obligations = [
        row for burden in all_burdens for row in obligations_by_burden[burden]
    ]
    pre_edges = _checker_dependency_edges(spec["dependency_shape"], canonical_baseline)
    post_edges = pre_edges[:-1] if spec["dependency_shape"] == "noetic-cycle-loopbreak" else list(pre_edges)
    partition_decisions = _checker_partition_decisions(
        spec, pressures, canonical_baseline
    )
    shared_authorizations = _checker_shared_authorizations(
        spec, pressures, canonical_baseline, partition_decisions
    )
    return {
        "seed": seed,
        "source_spec_sha256": canonical_sha256(spec),
        "dependency_shape": spec["dependency_shape"],
        "baseline_declaration_order": declaration_order,
        "source_observation_ids": observations,
        "pressure_ids": pressures,
        "candidate_state_ids": candidates,
        "candidate_hyperedge_ids": hyperedges,
        "baseline_burden_ids": baseline,
        "generated_burden_ids": generated,
        "held_baseline_burden_ids": held,
        "preempted_candidate_ids": preempted,
        "obligation_ids": [row["obligation_id"] for row in obligations],
        "obligations": obligations,
        "pressure_partition_decisions": partition_decisions,
        "shared_operation_authorizations": shared_authorizations,
        "generation": generation,
        "burden_cycles": cycles,
        "cycle_events": cycle_events,
        "route_candidate_kinds": list(dims["route_candidate_kinds"]),
        "noetic_edges_pre_loopbreak": pre_edges,
        "noetic_edges_post_loopbreak": post_edges,
        "event_ids": event_ids,
        "event_edges": [[event_ids[index], event_ids[index + 1]] for index in range(len(event_ids) - 1)],
        "closure_policy": spec["closure_policy"],
    }


def _normalize_evidence(value: str) -> str:
    text = IDENTITY_TOKEN_RE.sub("<identity>", value.lower())
    text = FILLER_RE.sub(" ", text)
    return " ".join(text.split())


def _event_for_kind(cycle: dict[str, Any], kind: str) -> str | None:
    return next(
        (
            event_id
            for event_id, event_kind in zip(cycle["event_ids"], cycle["event_kinds"])
            if event_kind == kind
        ),
        None,
    )


def _expected_cycle_stage_rows(
    expected: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    seed = expected["seed"]
    stage03_rows: list[dict[str, Any]] = []
    stage04_rows: list[dict[str, Any]] = []
    stage05_rows: list[dict[str, Any]] = []
    for index, cycle in enumerate(expected["burden_cycles"], 1):
        stage03_ref = _checker_stable_id(seed, "stage03cycle", index)
        stage04_ref = _checker_stable_id(seed, "stage04cycle", index)
        stage03_rows.append(
            {
                "stage03_cycle_ref": stage03_ref,
                "cycle_id": cycle["cycle_id"],
                "burden_id": cycle["burden_id"],
                "origin": cycle["origin"],
                "parent_cycle_id": cycle["parent_cycle_id"],
                "generation_depth": cycle["generation_depth"],
                "route_event_id": cycle["event_ids"][0],
                "reentry_event_id": _event_for_kind(cycle, "stage03-reentry"),
            }
        )
        stage04_rows.append(
            {
                "stage04_cycle_ref": stage04_ref,
                "stage03_cycle_ref": stage03_ref,
                "cycle_id": cycle["cycle_id"],
                "burden_id": cycle["burden_id"],
                "execution_event_id": _event_for_kind(cycle, "execute"),
                "hold_disposition_event_id": _event_for_kind(cycle, "hold-disposition"),
            }
        )
        stage05_rows.append(
            {
                **copy.deepcopy(cycle),
                "stage03_cycle_ref": stage03_ref,
                "stage04_cycle_ref": stage04_ref,
                "land_event_id": _event_for_kind(cycle, "land"),
                "reread_id": _checker_stable_id(seed, "reread", index),
                "terminal_state": "LANDED",
            }
        )
    return stage03_rows, stage04_rows, stage05_rows


def _public_segments(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "ordinal": index,
            "obligation_id": row["obligation_id"],
            "body_ref": row["body_ref"],
            "semantic_payload": row["semantic_payload"],
        }
        for index, row in enumerate(operations, 1)
    ]


def _expected_public_output_bytes(stage07: dict[str, Any]) -> bytes:
    return canonical_bytes(
        {
            "schema": "daee-topology-public-output-v1",
            "segments": stage07["segments"],
            "operations": stage07["operations"],
            "projection": stage07["projection"],
            "T_lang": stage07["T_lang"],
            "non_claim": "structural projection is not semantic truth or guaranteed uptake",
        }
    )


SHARED_RELATION_FIELDS = (
    "relation_schema",
    "source_relation",
    "decision_id",
    "upstream_shared_authorization_id",
    "upstream_shared_authorization_sha256",
    "upstream_partition_decision_ids",
    "upstream_partition_authorization_sha256",
    "obligation_ids",
    "pressure_ids",
    "owner_id",
    "operation",
    "register_id",
    "target_burden_ids",
    "normalized_evidence_sha256",
)


def _shared_relation_payload(decision: dict[str, Any]) -> dict[str, Any]:
    return {field: decision.get(field) for field in SHARED_RELATION_FIELDS}


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _diagnostic(stage: str, failure_class: str, subcode: str, message: str, markers: list[str] | None = None) -> dict[str, Any]:
    return {
        "checker_id": "topology-capacity-properties",
        "status": "rejected",
        "exit_code": 1,
        "earliest_stage": stage,
        "failure_class": failure_class,
        "failure_subcode": subcode,
        "downstream_invalidated": [item for item in STAGES if int(item) > int(stage)],
        "required_diagnostic_markers": markers or [],
        "message": message,
        "non_claim": "structural rejection is not a semantic verdict",
    }


def _accepted(checked_through: str = "08") -> dict[str, Any]:
    return {
        "checker_id": "topology-capacity-properties",
        "status": "accepted",
        "exit_code": 0,
        "earliest_stage": None,
        "failure_class": None,
        "failure_subcode": None,
        "downstream_invalidated": [],
        "checked_through": checked_through,
        "non_claim": "structural probes are not semantic truth",
    }


def _duplicates(values: list[str]) -> list[str]:
    return sorted({item for item in values if values.count(item) > 1})


def _has_cycle(nodes: list[str], edges: list[list[str]]) -> bool:
    outgoing = {node: [] for node in nodes}
    indegree = {node: 0 for node in nodes}
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2 or edge[0] not in outgoing or edge[1] not in outgoing:
            return True
        outgoing[edge[0]].append(edge[1])
        indegree[edge[1]] += 1
    ready = sorted(node for node, degree in indegree.items() if degree == 0)
    seen = 0
    while ready:
        node = ready.pop(0)
        seen += 1
        for target in outgoing[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()
    return seen != len(nodes)


def _stage(directory: Path, number: str) -> dict[str, Any] | None:
    path = directory / STAGE_FILES[number]
    return _load(path) if path.exists() else None


def _target_stage(value: str | None) -> str:
    if value is None:
        return "08"
    for number in STAGES:
        if value == number or value.startswith(f"stage-{number}"):
            return number
    raise ValueError(f"unknown through-stage {value}")


def extract_actual_dimensions(directory: Path) -> dict[str, Any]:
    """Extract actual record dimensions without using expected-manifest derivation."""
    s1, s2, s3, s5 = (_stage(directory, number) or {} for number in ("01", "02", "03", "05"))
    lifecycle = s5.get("lifecycle", [])
    return {
        "source_observation_ids": [row.get("observation_id") for row in s1.get("observations", [])],
        "pressure_ids": [row.get("pressure_id") for row in s2.get("pressures", [])],
        "candidate_state_ids": [row.get("candidate_id") for row in s2.get("candidates", [])],
        "candidate_hyperedge_ids": [row.get("hyperedge_id") for row in s2.get("hyperedges", [])],
        "baseline_burden_ids": list(s2.get("baseline_burden_ids", [])),
        "generated_burden_ids": [row.get("burden_id") for row in lifecycle if row.get("origin") == "B_MRP"],
        "held_baseline_burden_ids": [row.get("burden_id") for row in lifecycle if row.get("origin") == "B_LA" and row.get("activated_from_hold")],
        "preempted_candidate_ids": [row.get("candidate_id") for row in s2.get("preempted_candidates", [])],
        "obligation_ids": [row.get("obligation_id") for row in s3.get("obligations", [])],
        "route_candidate_kinds": [row.get("kind") for row in s3.get("routes", [])],
        "event_ids": list(s5.get("event_ids", [])),
        "event_edges": list(s5.get("event_edges", [])),
        "noetic_edges_pre_loopbreak": list(s2.get("noetic_edges_pre_loopbreak", [])),
        "noetic_edges_post_loopbreak": list(s2.get("noetic_edges_post_loopbreak", [])),
    }


def dimension_signature(directory: Path) -> dict[str, int | str]:
    actual = extract_actual_dimensions(directory)
    manifest = _load(directory / "topology-dimensions.json")
    return {
        "dependency_shape": manifest["dependency_shape"],
        "observations": len(actual["source_observation_ids"]),
        "pressures": len(actual["pressure_ids"]),
        "candidates": len(actual["candidate_state_ids"]),
        "hyperedges": len(actual["candidate_hyperedge_ids"]),
        "baseline_burdens": len(actual["baseline_burden_ids"]),
        "generated_burdens": len(actual["generated_burden_ids"]),
        "preempted": len(actual["preempted_candidate_ids"]),
        "obligations": len(actual["obligation_ids"]),
        "event_edges": len(actual["event_edges"]),
        "noetic_pre_edges": len(actual["noetic_edges_pre_loopbreak"]),
        "noetic_post_edges": len(actual["noetic_edges_post_loopbreak"]),
    }


def _compare_expected(actual: dict[str, Any], manifest: dict[str, Any], keys: tuple[str, ...], stage: str) -> dict[str, Any] | None:
    for key in keys:
        if set(actual.get(key, [])) != set(manifest.get(key, [])):
            return _diagnostic(stage, "dimension-manifest-parity", f"{key}-mismatch", f"actual {key} differs from independent expected manifest", [key])
    return None


def _manifest_source_parity(producer: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any] | None:
    set_keys = (
        "source_observation_ids",
        "pressure_ids",
        "candidate_state_ids",
        "candidate_hyperedge_ids",
        "baseline_burden_ids",
        "generated_burden_ids",
        "held_baseline_burden_ids",
        "preempted_candidate_ids",
        "obligation_ids",
        "route_candidate_kinds",
        "event_ids",
    )
    for key in set_keys:
        if set(producer.get(key, [])) != set(expected.get(key, [])):
            return _diagnostic("01", "source-spec-parity", f"manifest-{key}-mismatch", f"producer manifest {key} differs from checker-owned source-spec derivation", [key])
    exact_keys = (
        "source_spec_sha256",
        "dependency_shape",
        "baseline_declaration_order",
        "obligations",
        "pressure_partition_decisions",
        "shared_operation_authorizations",
        "generation",
        "burden_cycles",
        "cycle_events",
        "noetic_edges_pre_loopbreak",
        "noetic_edges_post_loopbreak",
        "event_edges",
        "closure_policy",
    )
    for key in exact_keys:
        if producer.get(key) != expected.get(key):
            return _diagnostic("01", "source-spec-parity", f"manifest-{key}-mismatch", f"producer manifest {key} differs from checker-owned source-spec derivation", [key])
    return None


def check_generated_directory(directory: Path, through_stage: str | None = None) -> dict[str, Any]:
    target = _target_stage(through_stage)
    spec_path = directory / SPEC_FILE
    if not spec_path.exists():
        return _diagnostic("01", "source-spec-parity", "source-spec-missing", "canonical topology source spec is absent", [SPEC_FILE])
    try:
        source_spec = validate_spec(_load(spec_path))
    except (ValueError, json.JSONDecodeError) as exc:
        return _diagnostic("01", "source-spec-parity", "source-spec-invalid", str(exc), [SPEC_FILE])
    expected = _checker_expected_from_spec(source_spec)
    manifest_path = directory / MANIFEST_FILE
    if not manifest_path.exists():
        return _diagnostic("01", "dimension-manifest-parity", "manifest-missing", "topology-dimensions.json is absent", ["topology-dimensions.json"])
    producer_manifest = _load(manifest_path)
    mismatch = _manifest_source_parity(producer_manifest, expected)
    if mismatch:
        return mismatch
    manifest = expected
    actual = extract_actual_dimensions(directory)
    s1 = _stage(directory, "01")
    if s1 is None:
        return _diagnostic("01", "source-pressure-conservation", "stage01-missing", "Stage01 record is absent")
    observations = s1.get("observations", [])
    observation_ids = [row.get("observation_id") for row in observations]
    if None in observation_ids or _duplicates(observation_ids):
        return _diagnostic("01", "source-pressure-conservation", "observation-identity", "observations require unique identities")
    if any(not row.get("pressure_id") and not row.get("disposition") for row in observations):
        return _diagnostic("01", "source-pressure-conservation", "observation-unaccounted", "each observation needs a pressure or disposition")
    mismatch = _compare_expected(actual, manifest, ("source_observation_ids",), "01")
    if mismatch:
        return mismatch
    if target == "01":
        return _accepted(target)

    s2 = _stage(directory, "02")
    if s2 is None:
        return _diagnostic("02", "candidate-terminal-accounting", "stage02-missing", "Stage02 record is absent")
    candidates = s2.get("candidates", [])
    allowed = {"selected", "held", "merged", "rejected"}
    if any(row.get("status") not in allowed or not row.get("basis") for row in candidates):
        return _diagnostic("02", "candidate-terminal-accounting", "candidate-nonterminal", "every candidate requires terminal status and basis")
    if any(row.get("status") == "merged" and row.get("merged_into") not in actual["candidate_state_ids"] for row in candidates):
        return _diagnostic("02", "split-merge-conservation", "merge-receiver-missing", "merged candidate requires an existing receiver")
    pressure_ids = set(actual["pressure_ids"])
    burden_ids = set(actual["baseline_burden_ids"])
    partition_decisions = s2.get("pressure_partition_decisions", [])
    shared_authorizations = s2.get("shared_operation_authorizations", [])
    if partition_decisions != manifest["pressure_partition_decisions"]:
        return _diagnostic(
            "02",
            "split-merge-conservation",
            "pressure-partition-inventory-mismatch",
            "Stage02 pressure partition inventory differs from checker-derived retained source authority",
        )
    if shared_authorizations != manifest["shared_operation_authorizations"]:
        return _diagnostic(
            "02",
            "split-merge-conservation",
            "shared-authorization-inventory-mismatch",
            "Stage02 shared-operation authority differs from checker-derived retained source authority",
        )
    partition_by_id = {row["decision_id"]: row for row in partition_decisions}
    actual_pressure_routes = {
        row.get("pressure_id"): row.get("burden_id") for row in s2.get("pressures", [])
    }
    expected_pressure_routes = {
        mapping["pressure_id"]: mapping["burden_id"]
        for decision in partition_decisions
        for mapping in decision["pressure_to_burden"]
    }
    if actual_pressure_routes != expected_pressure_routes or set(actual_pressure_routes) != pressure_ids:
        return _diagnostic(
            "02",
            "split-merge-conservation",
            "pressure-partition-route-mismatch",
            "every pressure must be routed exactly once by the canonical pressure-partition inventory",
        )
    for edge in s2.get("hyperedges", []):
        if (
            not set(edge.get("incoming_pressure_ids", [])).issubset(pressure_ids)
            or edge.get("receiving_burden_id") not in burden_ids
        ):
            return _diagnostic("02", "split-merge-conservation", "hyperedge-unreconstructible", "candidate hyperedge has an unknown pressure or receiver")
        if edge.get("derivative_proof") is not None:
            return _diagnostic(
                "02",
                "split-merge-conservation",
                "partition-authorization-missing",
                "free-form hyperedge derivative proof is not canonical pressure-partition authority",
            )
        if edge.get("decision") in {"merge-with-derivative-proof", "merge_same_function"}:
            decision = partition_by_id.get(edge.get("partition_decision_id"))
            if (
                not decision
                or decision["relation_type"] != "merge_same_function"
                or edge.get("partition_authorization_sha256") != decision["authorization_sha256"]
                or edge.get("incoming_pressure_ids") != decision["pressure_ids"]
                or [edge.get("receiving_burden_id")] != decision["receiving_burden_ids"]
                or decision["same_function_proof"] != CHECKER_SAME_FUNCTION_PROOF
            ):
                return _diagnostic(
                    "02",
                    "split-merge-conservation",
                    "partition-authorization-mismatch",
                    "merge hyperedge does not cite the exact canonical upstream decision and hash",
                )
    mismatch = _compare_expected(actual, manifest, ("pressure_ids", "candidate_state_ids", "candidate_hyperedge_ids", "baseline_burden_ids", "preempted_candidate_ids"), "02")
    if mismatch:
        return mismatch
    if target == "02":
        return _accepted(target)

    s3 = _stage(directory, "03")
    if s3 is None:
        return _diagnostic("03", "owner-obligation-coverage", "stage03-missing", "Stage03 record is absent")
    obligations = s3.get("obligations", [])
    obligation_ids = [row.get("obligation_id") for row in obligations]
    if None in obligation_ids or _duplicates(obligation_ids):
        return _diagnostic("03", "owner-obligation-coverage", "obligation-identity", "obligations require unique identities")
    required = {"obligation_id", "burden_id", "pressure_id", "owner_id", "register_id", "operation", "body_ref", "cycle_id"}
    for row in obligations:
        missing = sorted(required - set(row))
        if missing:
            return _diagnostic("03", "owner-obligation-coverage", "eligible-owner-missing", f"obligation {row.get('obligation_id')} lacks {missing}", [row.get("obligation_id", "unknown"), *missing])
    for route in s3.get("routes", []):
        if route.get("kind") not in KNOWN_ROUTE_KINDS and (
            route.get("disposition") not in {"HOLD", "PARTIAL"}
            or not route.get("differentiator")
            or not route.get("next_action")
        ):
            return _diagnostic("03", "open-route-accounting", "unknown-route-closed", "every unrecognized route must remain HOLD/PARTIAL with differentiator and next action")
    stage03_cycles = s3.get("burden_cycles", [])
    expected_stage03_cycles, expected_stage04_cycles, expected_stage05_cycles = (
        _expected_cycle_stage_rows(manifest)
    )
    expected_cycle_ids = {row["cycle_id"] for row in manifest["burden_cycles"]}
    if {row.get("cycle_id") for row in stage03_cycles} != expected_cycle_ids:
        return _diagnostic("03", "burden-cycle-reentry", "stage03-cycle-universe", "Stage03 cycle universe differs from source-spec derivation")
    if any(not row.get("stage03_cycle_ref") or row.get("generation_depth") is None for row in stage03_cycles):
        return _diagnostic("03", "burden-cycle-reentry", "stage03-cycle-reference", "Stage03 burden cycle lacks explicit reference/depth")
    if stage03_cycles != expected_stage03_cycles:
        return _diagnostic(
            "03",
            "burden-cycle-reentry",
            "stage03-cycle-source-mismatch",
            "Stage03 burden cycles differ in source burden, origin, parent, depth, event joins, or exact order",
        )
    expected_obligations_by_id = {
        row["obligation_id"]: row for row in manifest["obligations"]
    }
    if {
        row.get("obligation_id"): row for row in obligations
    } != expected_obligations_by_id:
        return _diagnostic(
            "03",
            "owner-obligation-coverage",
            "obligation-source-relation-mismatch",
            "Stage03 obligation pressure, burden, owner, operation, register, body, or cycle relation differs from source-spec derivation",
        )
    stage03_shared_decisions = s3.get("shared_operation_decisions", [])
    upstream_shared_by_id = {
        row["shared_authorization_id"]: row for row in shared_authorizations
    }
    referenced_upstream_shared_ids = []
    for decision in stage03_shared_decisions:
        upstream_id = decision.get("upstream_shared_authorization_id")
        upstream = upstream_shared_by_id.get(upstream_id)
        if upstream is None:
            return _diagnostic(
                "03",
                "split-merge-conservation",
                "shared-operation-upstream-authority-missing",
                "Stage03 shared operation is locally asserted without retained Stage02 source authority",
            )
        referenced_upstream_shared_ids.append(upstream_id)
        if (
            decision.get("upstream_shared_authorization_sha256")
            != upstream["authorization_sha256"]
            or decision.get("upstream_partition_decision_ids")
            != upstream["upstream_partition_decision_ids"]
            or decision.get("upstream_partition_authorization_sha256")
            != upstream["upstream_partition_authorization_sha256"]
        ):
            return _diagnostic(
                "03",
                "split-merge-conservation",
                "shared-operation-upstream-authority-mismatch",
                "Stage03 shared operation substitutes or mis-hashes its exact upstream partition authority",
            )
    if (
        len(referenced_upstream_shared_ids) != len(set(referenced_upstream_shared_ids))
        or set(referenced_upstream_shared_ids) != set(upstream_shared_by_id)
    ):
        return _diagnostic(
            "03",
            "split-merge-conservation",
            "shared-operation-upstream-authority-unused",
            "every retained Stage02 shared authority must be used exactly once at Stage03",
        )
    mismatch = _compare_expected(actual, manifest, ("obligation_ids", "route_candidate_kinds"), "03")
    if mismatch:
        return mismatch
    if target == "03":
        return _accepted(target)

    s4 = _stage(directory, "04")
    if s4 is None:
        return _diagnostic("04", "owner-obligation-coverage", "stage04-missing", "Stage04 record is absent")
    acts, dispositions = s4.get("acts", []), s4.get("dispositions", [])
    act_obligation_ids = [row.get("obligation_id") for row in acts]
    disposition_ids = [row.get("obligation_id") for row in dispositions]
    if set(act_obligation_ids) != set(obligation_ids) or _duplicates(act_obligation_ids):
        missing = sorted(set(obligation_ids) - set(act_obligation_ids))
        return _diagnostic("04", "owner-obligation-coverage", "eligible-obligation-unpaid", f"Stage03 obligations have no Stage04 terminal disposition: {missing}", missing + ["eligible-obligation-unpaid"])
    if not set(disposition_ids).issubset(set(obligation_ids)) or _duplicates(disposition_ids):
        return _diagnostic("04", "owner-obligation-coverage", "hold-disposition-unjoined", "Stage04 HOLD history must join unique Stage03 obligations")
    body_refs = [row.get("body_ref") for row in acts]
    semantic_hashes = [row.get("semantic_body_sha256") for row in acts]
    if None in body_refs or _duplicates(body_refs) or None in semantic_hashes:
        return _diagnostic("04", "operation-body-identity", "padding-no-credit", "ACT bodies require obligation-bound semantic identities")
    act_required = {"before_state", "performed_evidence", "delta", "residual", "land_contribution", "semantic_payload"}
    if any(not act_required.issubset(row) for row in acts):
        return _diagnostic("04", "operation-body-identity", "operation-evidence-incomplete", "ACT body evidence is incomplete")
    for row in acts:
        if row.get("semantic_body_sha256") != canonical_sha256(row.get("semantic_payload")):
            return _diagnostic(
                "04",
                "operation-body-identity",
                "semantic-body-hash-mismatch",
                f"{row.get('obligation_id')} semantic payload does not match its operation body identity",
                [str(row.get("obligation_id")), "semantic_body_sha256"],
            )
        normalized = _normalize_evidence(row.get("semantic_payload", ""))
        if row.get("normalized_evidence_sha256") != canonical_sha256(normalized):
            return _diagnostic(
                "04",
                "operation-body-identity",
                "normalized-evidence-hash-mismatch",
                f"{row.get('obligation_id')} normalized evidence hash is stale or identity/padding-derived",
                [str(row.get("obligation_id")), "normalized_evidence_sha256"],
            )
    normalized_groups: dict[str, list[dict[str, Any]]] = {}
    for row in acts:
        normalized_groups.setdefault(row["normalized_evidence_sha256"], []).append(row)
    decisions = {row.get("decision_id"): row for row in s3.get("shared_operation_decisions", []) if isinstance(row, dict)}
    for normalized_hash, group in normalized_groups.items():
        if len(group) < 2:
            continue
        decision_ids = {row.get("shared_operation_decision_id") for row in group}
        if len(decision_ids) != 1 or None in decision_ids:
            return _diagnostic("04", "operation-body-identity", "repeated-body-without-shared-decision", "normalized repeated evidence requires one explicit shared-operation/merge decision")
        decision = decisions.get(next(iter(decision_ids)))
        if not decision or not decision.get("authorization_sha256"):
            return _diagnostic(
                "04",
                "operation-body-identity",
                "shared-decision-authorization-missing",
                "shared operation decision requires a canonical source-relation authorization hash",
            )
        upstream = upstream_shared_by_id.get(
            decision.get("upstream_shared_authorization_id")
        ) if decision else None
        expected_relation = {
            "relation_schema": "daee-shared-operation-relation-v1",
            "source_relation": "same-function-source-frame-restoration-vector",
            "decision_id": next(iter(decision_ids)),
            "upstream_shared_authorization_id": upstream.get("shared_authorization_id") if upstream else None,
            "upstream_shared_authorization_sha256": upstream.get("authorization_sha256") if upstream else None,
            "upstream_partition_decision_ids": upstream.get("upstream_partition_decision_ids") if upstream else None,
            "upstream_partition_authorization_sha256": upstream.get("upstream_partition_authorization_sha256") if upstream else None,
            "obligation_ids": sorted(row["obligation_id"] for row in group),
            "pressure_ids": sorted(row["pressure_id"] for row in group),
            "owner_id": group[0]["owner_id"],
            "operation": group[0]["operation"],
            "register_id": group[0]["register_id"],
            "target_burden_ids": sorted(row["burden_id"] for row in group),
            "normalized_evidence_sha256": normalized_hash,
        }
        same_function = all(
            row["owner_id"] == group[0]["owner_id"]
            and row["operation"] == group[0]["operation"]
            and row["register_id"] == group[0]["register_id"]
            for row in group
        )
        obligations_match = all(
            expected_obligations_by_id.get(row["obligation_id"], {}).get(field)
            == row.get(field)
            for row in group
            for field in (
                "pressure_id",
                "burden_id",
                "owner_id",
                "operation",
                "register_id",
                "body_ref",
                "cycle_id",
            )
        )
        upstream_scope_matches = bool(upstream) and (
            upstream["pressure_ids"] == [row["pressure_id"] for row in group]
            and upstream["receiving_burden_ids"] == [row["burden_id"] for row in group]
            and upstream["owner_id"] == group[0]["owner_id"]
            and upstream["operation"] == group[0]["operation"]
            and upstream["register_id"] == group[0]["register_id"]
            and upstream["evidence_identity"] == normalized_hash
            and upstream["same_function_proof"] == CHECKER_SAME_FUNCTION_PROOF
        )
        if (
            not same_function
            or not obligations_match
            or not upstream_scope_matches
            or _shared_relation_payload(decision) != expected_relation
        ):
            return _diagnostic(
                "04",
                "operation-body-identity",
                "shared-decision-relation-mismatch",
                "shared operation authorization does not match pressure, owner, operation, register, target, and obligation membership",
            )
        if decision["authorization_sha256"] != canonical_sha256(expected_relation):
            return _diagnostic(
                "04",
                "operation-body-identity",
                "shared-decision-authorization-hash-mismatch",
                "shared operation authorization hash does not bind the canonical source relation",
            )
        if any(
            row.get("shared_operation_authorization_sha256")
            != decision["authorization_sha256"]
            for row in group
        ):
            return _diagnostic(
                "04",
                "operation-body-identity",
                "act-shared-authorization-mismatch",
                "every Stage04 ACT using shared evidence must cite the exact Stage03 decision authorization hash",
            )
    stage04_cycles = s4.get("burden_cycles", [])
    if {row.get("cycle_id") for row in stage04_cycles} != expected_cycle_ids:
        return _diagnostic("04", "burden-cycle-reentry", "stage04-cycle-universe", "Stage04 cycle universe differs from Stage03/source spec")
    stage03_ref_by_cycle = {row["cycle_id"]: row["stage03_cycle_ref"] for row in stage03_cycles}
    if any(row.get("stage03_cycle_ref") != stage03_ref_by_cycle.get(row.get("cycle_id")) or not row.get("stage04_cycle_ref") for row in stage04_cycles):
        return _diagnostic("04", "burden-cycle-reentry", "stage04-cycle-reference", "Stage04 cycle does not reference its Stage03 re-entry")
    if [row.get("cycle_id") for row in stage04_cycles] != [
        row.get("cycle_id") for row in stage03_cycles
    ]:
        return _diagnostic(
            "04",
            "burden-cycle-reentry",
            "cross-stage-component-order-mismatch",
            "Stage04 component blocks do not preserve the Stage03 declaration order",
        )
    if stage04_cycles != expected_stage04_cycles:
        return _diagnostic(
            "04",
            "burden-cycle-reentry",
            "stage04-cycle-source-mismatch",
            "Stage04 burden cycles differ in burden, execution/hold event joins, Stage03 reference, or exact order",
        )
    for row in acts:
        expected_obligation = expected_obligations_by_id.get(row.get("obligation_id"))
        if not expected_obligation or any(
            row.get(field) != expected_obligation[field]
            for field in (
                "burden_id",
                "pressure_id",
                "owner_id",
                "register_id",
                "operation",
                "body_ref",
                "cycle_id",
            )
        ):
            return _diagnostic(
                "04",
                "owner-obligation-coverage",
                "act-obligation-relation-mismatch",
                "Stage04 ACT does not preserve its Stage03 pressure, burden, owner, operation, register, body, and cycle joins",
            )
    by_burden: dict[str, set[str]] = {}
    for row in obligations:
        by_burden.setdefault(row["burden_id"], set()).add(row["obligation_id"])
    if any(not ids for ids in by_burden.values()):
        return _diagnostic("04", "burden-local-completeness", "empty-burden-obligations", "instantiated burden has no obligations")
    if target == "04":
        return _accepted(target)

    s5 = _stage(directory, "05")
    if s5 is None:
        return _diagnostic("05", "reread-terminal-coverage", "stage05-missing", "Stage05 record is absent")
    lifecycle = s5.get("lifecycle", [])
    lifecycle_ids = [row.get("burden_id") for row in lifecycle]
    if _duplicates(lifecycle_ids):
        return _diagnostic("05", "lifecycle-partition", "duplicate-instantiated-burden", "lifecycle burden identities overlap")
    baseline_actual = {row.get("burden_id") for row in lifecycle if row.get("origin") == "B_LA"}
    generated_actual = {row.get("burden_id") for row in lifecycle if row.get("origin") == "B_MRP"}
    if baseline_actual & generated_actual or baseline_actual != set(manifest["baseline_burden_ids"]) or generated_actual != set(manifest["generated_burden_ids"]):
        return _diagnostic("05", "lifecycle-partition", "generated-held-alias", "B_LA and B_MRP must be disjoint and exhaustive")
    if set(manifest["preempted_candidate_ids"]) & set(lifecycle_ids):
        return _diagnostic("05", "lifecycle-partition", "preempted-instantiated", "preempted candidate became a graph node")
    stage05_cycles = s5.get("burden_cycles", [])
    if {row.get("cycle_id") for row in stage05_cycles} != expected_cycle_ids:
        return _diagnostic("05", "burden-cycle-reentry", "stage05-cycle-universe", "Stage05 cycle universe differs from Stage03/04/source spec")
    if stage05_cycles != expected_stage05_cycles:
        return _diagnostic(
            "05",
            "burden-cycle-reentry",
            "stage05-cycle-source-mismatch",
            "Stage05 burden cycles differ in source relation, custody references, lifecycle events, or exact order",
        )
    stage04_ref_by_cycle = {row["cycle_id"]: row["stage04_cycle_ref"] for row in stage04_cycles}
    expected_cycle_by_id = {row["cycle_id"]: row for row in manifest["burden_cycles"]}
    cycle_position = {row.get("cycle_id"): index for index, row in enumerate(stage05_cycles)}
    for row in stage05_cycles:
        cycle_id = row.get("cycle_id")
        expected_cycle = expected_cycle_by_id.get(cycle_id)
        if (
            row.get("stage03_cycle_ref") != stage03_ref_by_cycle.get(cycle_id)
            or row.get("stage04_cycle_ref") != stage04_ref_by_cycle.get(cycle_id)
        ):
            return _diagnostic("05", "burden-cycle-reentry", "cross-stage-cycle-reference", f"{cycle_id} lacks exact Stage03/04 cycle references")
        if not expected_cycle or row.get("event_ids") != expected_cycle["event_ids"] or row.get("event_kinds") != expected_cycle["event_kinds"]:
            return _diagnostic("05", "burden-cycle-reentry", "cycle-event-order", f"{cycle_id} has missing or out-of-order re-entry events")
        parent_cycle_id = row.get("parent_cycle_id")
        if row.get("origin") == "B_MRP":
            parent = next((item for item in stage05_cycles if item.get("cycle_id") == parent_cycle_id), None)
            if parent is None or cycle_position[parent_cycle_id] >= cycle_position[cycle_id]:
                return _diagnostic("05", "burden-cycle-reentry", "parent-after-child", f"{cycle_id} is not ordered after its parent cycle")
            if row.get("generation_depth") != parent.get("generation_depth") + 1:
                return _diagnostic("05", "burden-cycle-reentry", "generation-depth-nonincrementing", f"{cycle_id} depth is not parent depth plus one")
        elif row.get("generation_depth") != 0 or parent_cycle_id is not None:
            return _diagnostic("05", "burden-cycle-reentry", "baseline-cycle-depth", f"{cycle_id} baseline cycle has generated provenance")
        if row.get("activated_from_hold") and row.get("event_kinds")[:5] != ["hold", "hold-disposition", "activate", "stage03-reentry", "execute"]:
            return _diagnostic("05", "burden-cycle-reentry", "held-activation-sequence", f"{cycle_id} held burden did not activate through Stage03/04 re-entry")
    for row in lifecycle:
        if not row.get("terminal_state"):
            return _diagnostic("05", "reread-terminal-coverage", "instantiated-burden-nonterminal", f"{row.get('burden_id')} lacks terminal state")
        if not row.get("reread_id"):
            marker = row.get("mutation_marker", row.get("burden_id", "unknown"))
            return _diagnostic("05", "reread-terminal-coverage", "instantiated-burden-missing-reread", f"{marker} instantiated burden lacks reread", [str(marker), "reread"])
        if row.get("cycle_id") not in expected_cycle_ids:
            return _diagnostic("05", "burden-cycle-reentry", "lifecycle-cycle-join", f"{row.get('burden_id')} lifecycle lacks a cycle join")
        if row.get("origin") == "B_MRP" and (not row.get("parent_id") or not isinstance(row.get("generation_depth"), int) or row["generation_depth"] < 1):
            return _diagnostic("05", "lifecycle-partition", "generated-provenance", "generated burden lacks parent/depth provenance")
    generation_by_burden = {
        row["burden_id"]: row for row in manifest["generation"]
    }
    expected_lifecycle = [
        {
            "burden_id": row["burden_id"],
            "cycle_id": row["cycle_id"],
            "origin": row["origin"],
            "parent_id": generation_by_burden.get(row["burden_id"], {}).get(
                "parent_id"
            ),
            "generation_depth": row["generation_depth"],
            "activated_from_hold": row["activated_from_hold"],
            "terminal_state": "LANDED",
            "reread_id": row["reread_id"],
        }
        for row in expected_stage05_cycles
    ]
    if lifecycle != expected_lifecycle:
        return _diagnostic(
            "05",
            "burden-cycle-reentry",
            "lifecycle-source-mismatch",
            "Stage05 lifecycle differs in burden, origin, parent, parent-derived depth, terminal state, reread, or exact order",
        )
    event_ids = s5.get("event_ids", [])
    if s5.get("event_nodes") != manifest.get("cycle_events"):
        return _diagnostic("05", "burden-cycle-reentry", "cycle-event-node-parity", "Stage05 ordered event nodes differ from source-spec cycle derivation")
    if _has_cycle(event_ids, s5.get("event_edges", [])):
        marker = s5.get("mutation_marker", "event graph")
        return _diagnostic("05", "dependency-event-dag-integrity", "event-dag-cycle", f"{marker} creates a cycle in the event/provenance DAG", [str(marker), "cycle"])
    pre_edges = s2.get("noetic_edges_pre_loopbreak", [])
    post_edges = s2.get("noetic_edges_post_loopbreak", [])
    if manifest["dependency_shape"] == "noetic-cycle-loopbreak" and (not _has_cycle(list(baseline_actual), pre_edges) or _has_cycle(list(baseline_actual), post_edges) or not s2.get("loopbreak")):
        return _diagnostic("05", "noetic-loopbreak-integrity", "cycle-loopbreak-loss", "noetic cycle must persist until explicit LoopBreak then become acyclic")
    snapshots = s5.get("closure_snapshots", [])
    previous: set[str] | None = None
    for snapshot in snapshots:
        current = set(snapshot.get("remaining_live_ids", []))
        if previous is not None and not current.issubset(previous):
            return _diagnostic("05", "monotonic-closure", "remaining-live-increased", "remaining-live state must be monotonic")
        if snapshot.get("closure") and current:
            return _diagnostic("05", "monotonic-closure", "closed-with-live-state", "closure cannot be true with remaining live IDs")
        previous = current
    if target == "05":
        return _accepted(target)

    s6 = _stage(directory, "06")
    if s6 is None:
        return _diagnostic("06", "witness-projection-parity", "stage06-missing", "Stage06 record is absent")
    nar_ids = [row.get("obligation_id") for row in s6.get("nar_rows", [])]
    act_ids = [row.get("obligation_id") for row in acts]
    if set(nar_ids) != set(act_ids) or _duplicates(nar_ids):
        return _diagnostic("06", "witness-projection-parity", "nar-activation-mismatch", "structured NAR rows must exactly cover executed ACTs", sorted(set(act_ids) - set(nar_ids)) + ["NAR"])
    projection = s6.get("projection", {})
    if (
        set(projection.get("obligation_ids", [])) != set(obligation_ids)
        or set(projection.get("reread_ids", [])) != {row["reread_id"] for row in lifecycle}
        or set(projection.get("cycle_ids", [])) != expected_cycle_ids
    ):
        return _diagnostic("06", "witness-projection-parity", "stage06-topology-mismatch", "Stage06 projection differs from Stage03-05 topology")
    if target == "06":
        return _accepted(target)

    s7 = _stage(directory, "07")
    if s7 is None:
        return _diagnostic("07", "public-projection-parity", "stage07-missing", "Stage07 record is absent")
    if s7.get("projection") != projection or s7.get("operations") != acts:
        return _diagnostic("07", "public-projection-parity", "projection-join-missing", "Stage07 public projection must equal Stage06 topology", ["projection", "join"])
    expected_segments = _public_segments(acts)
    if s7.get("segments") != expected_segments:
        return _diagnostic(
            "07",
            "public-projection-parity",
            "public-segment-join-mismatch",
            "Stage07 public segments must reconstruct exactly from validated operations",
            ["segments", "operations"],
        )
    if s7.get("T_lang", {}).get("uptake_guaranteed") is not False:
        return _diagnostic("07", "public-projection-parity", "t-lang-overclaim", "T_lang cannot guarantee uptake")
    public_path = directory / PUBLIC_OUTPUT_FILE
    if not public_path.exists() or not isinstance(s7.get("public_output_sha256"), str):
        return _diagnostic("07", "public-projection-parity", "public-output-binding", "Stage07 does not declare the exact public output binding", [PUBLIC_OUTPUT_FILE])
    public_bytes = public_path.read_bytes()
    if s7["public_output_sha256"] != hashlib.sha256(public_bytes).hexdigest():
        return _diagnostic(
            "07",
            "public-projection-parity",
            "public-output-hash-stale",
            "Stage07 declared public output hash does not match the exact retained bytes",
            [PUBLIC_OUTPUT_FILE, "public_output_sha256"],
        )
    if public_bytes != _expected_public_output_bytes(s7):
        return _diagnostic(
            "07",
            "public-projection-parity",
            "public-output-reconstruction-mismatch",
            "retained public output bytes do not reconstruct from validated Stage07 projection, operations, and segments",
            [PUBLIC_OUTPUT_FILE, "segments"],
        )
    if target == "07":
        return _accepted(target)

    s8 = _stage(directory, "08")
    if s8 is None:
        return _diagnostic("08", "sidecar-custody", "stage08-missing", "Stage08 record is absent")
    expected_sidecars = {
        STATE_FILE: {
            "schema": "daee-topology-state-capsule-v1",
            "B_LA": [row["burden_id"] for row in lifecycle if row["origin"] == "B_LA"],
            "B_MRP": [row["burden_id"] for row in lifecycle if row["origin"] == "B_MRP"],
            "burden_cycle_ids": [row["cycle_id"] for row in lifecycle],
            "terminal_states": {
                row["burden_id"]: row["terminal_state"] for row in lifecycle
            },
            "remaining_live_ids": snapshots[-1]["remaining_live_ids"],
        },
        WITNESS_FILE: {
            "schema": "daee-topology-field-witness-v1",
            "projection": projection,
            "nar_rows": s6["nar_rows"],
            "burden_cycles": stage05_cycles,
            "non_claims": ["structural parity is not semantic truth"],
        },
        PROJECTION_FILE: {
            "schema": "daee-topology-stage-projection-v1",
            "stage06": projection,
            "stage07": s7["projection"],
            "equal": True,
        },
    }
    sidecar_subcodes = {
        STATE_FILE: "state-capsule-parity",
        WITNESS_FILE: "field-witness-parity",
        PROJECTION_FILE: "stage-projection-parity",
    }
    for name, expected_sidecar in expected_sidecars.items():
        sidecar_path = directory / name
        try:
            sidecar = _load(sidecar_path)
        except (FileNotFoundError, json.JSONDecodeError):
            sidecar = None
        if sidecar != expected_sidecar:
            return _diagnostic(
                "08",
                "sidecar-structure",
                sidecar_subcodes[name],
                f"{name} does not structurally reconstruct from validated Stage05-Stage07 records",
                [name],
            )
    required_artifacts = {
        SPEC_FILE,
        MANIFEST_FILE,
        *(STAGE_FILES[number] for number in STAGES[:-1]),
        STATE_FILE,
        WITNESS_FILE,
        PROJECTION_FILE,
        PUBLIC_OUTPUT_FILE,
    }
    bindings = s8.get("artifact_sha256", {})
    if set(bindings) != required_artifacts:
        return _diagnostic("08", "sidecar-custody", "artifact-binding-universe", "Stage08 must bind every required stage, sidecar, source spec, manifest, and public output", sorted(required_artifacts - set(bindings)))
    for name in sorted(required_artifacts):
        path = directory / name
        if not path.is_file() or bindings.get(name) != _raw_sha256(path):
            return _diagnostic("08", "sidecar-custody", "artifact-hash-mismatch", f"Stage08 binding mismatch for {name}", [name])
    if s8.get("source_spec_sha256") != canonical_sha256(source_spec):
        return _diagnostic("08", "sidecar-custody", "source-spec-hash-mismatch", "Stage08 source spec hash mismatch", [SPEC_FILE])
    return _accepted(target)


def check_spec_path(spec_path: Path, output_dir: Path) -> dict[str, Any]:
    destination = output_dir if not output_dir.exists() else output_dir / "generated-case"
    generate_case(spec_path, destination)
    result = check_generated_directory(destination)
    result["artifact_root"] = str(destination)
    return result


def _expectation_for(spec_path: Path) -> dict[str, Any] | None:
    path = spec_path.with_suffix(".expectation.json")
    return _load(path) if path.exists() else None


def check_probe_set(probe_set_path: Path, through_stage: str | None = None) -> dict[str, Any]:
    payload = _load(probe_set_path)
    root = probe_set_path.parent
    observed_burdens: set[int] = set()
    observed_submoves: set[int] = set()
    rows = []
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="daee-topology-probes-") as parent:
        for index, relative in enumerate(payload.get("specs", [])):
            spec_path = root / relative
            spec = validate_spec(_load(spec_path))
            destination = Path(parent) / f"valid-{index}"
            generate_case(spec_path, destination)
            diagnostic = check_generated_directory(destination, through_stage)
            if diagnostic["exit_code"]:
                return {"exit_code": 1, "status": "FAIL", "case": relative, "diagnostic": diagnostic}
            observed_burdens.add(spec["dimensions"]["baseline_burdens"])
            observed_submoves.add(spec["dimensions"]["submoves_per_burden"])
            rows.append({"spec": relative, "status": "accepted", "signature": dimension_signature(destination)})
        for index, relative in enumerate(payload.get("invalid_specs", [])):
            spec_path = root / relative
            expectation = _expectation_for(spec_path)
            if expectation and int(expectation["expected_earliest_stage"]) > int(_target_stage(through_stage)):
                rows.append({"spec": relative, "status": "not-applicable-after-bound", "through_stage": _target_stage(through_stage)})
                continue
            destination = Path(parent) / f"invalid-{index}"
            generate_case(spec_path, destination)
            diagnostic = check_generated_directory(destination, through_stage)
            if not expectation or any(
                diagnostic.get(actual) != expectation.get(expected)
                for actual, expected in (
                    ("exit_code", "expected_exit_code"),
                    ("earliest_stage", "expected_earliest_stage"),
                    ("failure_class", "expected_failure_class"),
                    ("failure_subcode", "expected_failure_subcode"),
                    ("downstream_invalidated", "expected_downstream_invalidated"),
                )
            ):
                return {"exit_code": 1, "status": "FAIL", "case": relative, "diagnostic": diagnostic, "expectation": expectation}
            forbidden = [item for item in expectation["forbidden_artifacts"] if (destination / item).exists()]
            if forbidden:
                return {"exit_code": 1, "status": "FAIL", "case": relative, "forbidden_artifacts_present": forbidden}
            rows.append({"spec": relative, "status": "right-reason-rejected", "diagnostic": diagnostic})
    return {
        "checker_id": "topology-capacity-properties",
        "status": "PASS",
        "exit_code": 0,
        "cases": rows,
        "observed": {"burdens": sorted(observed_burdens), "submoves": sorted(observed_submoves)},
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        "non_claim": "structural probes are not semantic truth",
    }


def _write_spec(path: Path, payload: dict[str, Any]) -> None:
    path.write_bytes(canonical_bytes(validate_spec(payload)))


def _metamorphic_partition_authorization(
    authorization_key: str,
    relation_type: str,
    pressure_ordinals: list[int],
    receiving_burden_ordinals: list[int],
    owner_ordinal: int,
    proof: dict[str, str],
) -> dict[str, Any]:
    payload = {
        "authorization_key": authorization_key,
        "relation_type": relation_type,
        "pressure_ordinals": pressure_ordinals,
        "receiving_burden_ordinals": receiving_burden_ordinals,
        "owner_ordinal": owner_ordinal,
        "operation": f"neutral-operation-{owner_ordinal}",
        "register_ordinal": owner_ordinal,
        "evidence_identity": _checker_canonical_sha256(
            {
                "authorization_key": authorization_key,
                "relation_type": relation_type,
                "pressure_ordinals": pressure_ordinals,
                "receiving_burden_ordinals": receiving_burden_ordinals,
            }
        ),
        "same_function_proof": copy.deepcopy(proof),
    }
    payload["authorization_sha256"] = _checker_canonical_sha256(payload)
    return payload


def _replace_partition_scope(
    spec: dict[str, Any],
    pressure_ordinals: set[int],
    replacement: dict[str, Any],
) -> None:
    spec["partition_authorizations"] = [
        row
        for row in spec["partition_authorizations"]
        if not pressure_ordinals.intersection(row["pressure_ordinals"])
    ] + [replacement]


def _instantiated_components_from_expected(
    expected: dict[str, Any],
) -> list[list[str]]:
    nodes = expected["baseline_burden_ids"] + expected["generated_burden_ids"]
    neighbors = {node: set() for node in nodes}
    edges = list(expected["noetic_edges_pre_loopbreak"]) + [
        [row["parent_id"], row["burden_id"]] for row in expected["generation"]
    ]
    for source, target in edges:
        neighbors[source].add(target)
        neighbors[target].add(source)
    components = []
    remaining = set(nodes)
    for root in nodes:
        if root not in remaining:
            continue
        stack = [root]
        remaining.remove(root)
        component = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(neighbors[node]):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _permutation_applicability(spec: dict[str, Any]) -> dict[str, Any]:
    expected = _checker_expected_from_spec(spec)
    components = _instantiated_components_from_expected(expected)
    canonical_baseline = _checker_ids(
        spec["seed"], "burden", spec["dimensions"]["baseline_burdens"]
    )
    ordinal_by_burden = {
        burden_id: index for index, burden_id in enumerate(canonical_baseline, 1)
    }
    ordinal_components = [
        [ordinal_by_burden[node] for node in canonical_baseline if node in component]
        for component in components
    ]
    ordinal_components = [component for component in ordinal_components if component]
    applicable = len(components) >= 2 and len(ordinal_components) >= 2
    return {
        "applicable": applicable,
        "reason": (
            "independent-component-blocks-available"
            if applicable
            else "fewer-than-two-independent-components"
        ),
        "component_count": len(components),
        "component_membership": ordinal_components,
    }


def normalized_oracle(directory: Path) -> dict[str, Any]:
    s1, s2, s3, s4, s5, s6 = (
        _stage(directory, number) or {}
        for number in ("01", "02", "03", "04", "05", "06")
    )
    cycles = s5.get("burden_cycles", [])
    baseline = list(s2.get("baseline_burden_ids", []))
    generated = [row.get("burden_id") for row in cycles if row.get("origin") == "B_MRP"]
    burden_labels = {
        **{burden_id: f"B{index}" for index, burden_id in enumerate(baseline, 1)},
        **{burden_id: f"G{index}" for index, burden_id in enumerate(generated, 1)},
    }
    cycle_labels = {
        row.get("cycle_id"): burden_labels.get(row.get("burden_id"), "unknown")
        for row in cycles
    }
    obligation_rows = {
        row.get("obligation_id"): row for row in s3.get("obligations", [])
    }
    acts = s4.get("acts", [])
    body_to_obligation = {
        row.get("body_ref"): row.get("obligation_id") for row in acts
    }
    lifecycle = s5.get("lifecycle", [])
    reread_to_burden = {
        row.get("reread_id"): row.get("burden_id") for row in lifecycle
    }
    projection = s6.get("projection", {})
    event_labels = {}
    for row in s5.get("event_nodes", []):
        event_labels[row.get("event_id")] = (
            cycle_labels.get(row.get("cycle_id"), "unknown"),
            row.get("kind"),
        )

    def obligation_relation(obligation_id: str) -> tuple[Any, ...]:
        row = obligation_rows.get(obligation_id, {})
        return (
            burden_labels.get(row.get("burden_id"), "unknown"),
            row.get("operation"),
        )

    dependency_graph = sorted(
        (
            burden_labels.get(source, "unknown"),
            burden_labels.get(target, "unknown"),
        )
        for source, target in s2.get("noetic_edges_pre_loopbreak", [])
    )
    generation_graph = sorted(
        (
            cycle_labels.get(row.get("cycle_id"), "unknown"),
            cycle_labels.get(row.get("parent_cycle_id"), "unknown"),
            row.get("generation_depth"),
        )
        for row in cycles
        if row.get("origin") == "B_MRP"
    )
    parent_relations = sorted(
        (
            burden_labels.get(row.get("burden_id"), "unknown"),
            burden_labels.get(row.get("parent_id"), "unknown"),
            row.get("generation_depth"),
        )
        for row in lifecycle
        if row.get("origin") == "B_MRP"
    )
    projection_relations = {
        "obligations": sorted(
            obligation_relation(item) for item in projection.get("obligation_ids", [])
        ),
        "bodies": sorted(
            obligation_relation(body_to_obligation.get(item))
            for item in projection.get("body_refs", [])
        ),
        "burden_states": sorted(
            (burden_labels.get(key, "unknown"), value)
            for key, value in projection.get("burden_states", {}).items()
        ),
        "rereads": sorted(
            burden_labels.get(reread_to_burden.get(item), "unknown")
            for item in projection.get("reread_ids", [])
        ),
        "cycles": sorted(
            cycle_labels.get(item, "unknown")
            for item in projection.get("cycle_ids", [])
        ),
        "dependency_pre": dependency_graph,
        "dependency_post": sorted(
            (
                burden_labels.get(source, "unknown"),
                burden_labels.get(target, "unknown"),
            )
            for source, target in projection.get("noetic_edges_post_loopbreak", [])
        ),
    }
    event_relations = {
        "cycle_patterns": sorted(
            (cycle_labels.get(row.get("cycle_id"), "unknown"), tuple(row.get("event_kinds", [])))
            for row in cycles
        ),
        "edges": sorted(
            (event_labels.get(source, ("unknown", None)), event_labels.get(target, ("unknown", None)))
            for source, target in s5.get("event_edges", [])
        ),
    }
    lifecycle_relations = sorted(
        (
            burden_labels.get(row.get("burden_id"), "unknown"),
            row.get("origin"),
            burden_labels.get(row.get("parent_id"), None),
            row.get("generation_depth"),
            bool(row.get("activated_from_hold")),
            row.get("terminal_state"),
            bool(row.get("reread_id")),
        )
        for row in lifecycle
    )
    raw_nodes = baseline + generated
    raw_neighbors = {node: set() for node in raw_nodes}
    raw_edges = list(s2.get("noetic_edges_pre_loopbreak", [])) + [
        [row.get("parent_id"), row.get("burden_id")]
        for row in lifecycle
        if row.get("origin") == "B_MRP"
    ]
    for source, target in raw_edges:
        if source in raw_neighbors and target in raw_neighbors:
            raw_neighbors[source].add(target)
            raw_neighbors[target].add(source)
    component_semantics = []
    remaining_nodes = set(raw_nodes)
    cycle_by_burden = {row.get("burden_id"): row for row in cycles}
    lifecycle_by_burden = {row.get("burden_id"): row for row in lifecycle}
    operations_by_burden: dict[str, list[str]] = {}
    for row in s3.get("obligations", []):
        operations_by_burden.setdefault(row.get("burden_id"), []).append(
            row.get("operation")
        )
    for root in raw_nodes:
        if root not in remaining_nodes:
            continue
        stack = [root]
        remaining_nodes.remove(root)
        component = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(raw_neighbors[node]):
                if neighbor in remaining_nodes:
                    remaining_nodes.remove(neighbor)
                    stack.append(neighbor)
        node_semantics = []
        for node in component:
            cycle = cycle_by_burden[node]
            life = lifecycle_by_burden[node]
            node_semantics.append(
                (
                    life.get("origin"),
                    life.get("generation_depth"),
                    bool(life.get("activated_from_hold")),
                    life.get("terminal_state"),
                    tuple(sorted(operations_by_burden.get(node, []))),
                    tuple(cycle.get("event_kinds", [])),
                    len(raw_neighbors[node]),
                )
            )
        component_semantics.append(
            (
                len(component),
                tuple(sorted(node_semantics)),
                len(
                    [
                        edge
                        for edge in raw_edges
                        if edge[0] in component and edge[1] in component
                    ]
                ),
            )
        )
    component_semantics.sort()
    return {
        "observations": len(s1.get("observations", [])),
        "pressures": len(s2.get("pressures", [])),
        "candidates": len(s2.get("candidates", [])),
        "hyperedges": len(s2.get("hyperedges", [])),
        "baseline_burdens": len([row for row in cycles if row.get("origin") == "B_LA"]),
        "generated_burdens": len([row for row in cycles if row.get("origin") == "B_MRP"]),
        "preempted": len(s2.get("preempted_candidates", [])),
        "obligations": len(s3.get("obligations", [])),
        "acts": len(s4.get("acts", [])),
        "cycles": len(cycles),
        "max_generation_depth": max((row.get("generation_depth", 0) for row in cycles), default=0),
        "hold_routes": len([row for row in s3.get("routes", []) if row.get("disposition") in {"HOLD", "PARTIAL"}]),
        "closure": bool(s5.get("closure_snapshots", [{}])[-1].get("closure")),
        "event_patterns": sorted(tuple(row.get("event_kinds", [])) for row in cycles),
        "normalized_evidence": sorted(row.get("normalized_evidence_sha256") for row in s4.get("acts", [])),
        "dependency_graph": dependency_graph,
        "generation_graph": generation_graph,
        "parent_relations": parent_relations,
        "projection_relations": projection_relations,
        "event_relations": event_relations,
        "lifecycle_relations": lifecycle_relations,
        "component_semantics": component_semantics,
    }


def _rewrite_json(path: Path, payload: Any) -> None:
    path.write_bytes(canonical_bytes(payload))


def _relation_core(oracle: dict[str, Any]) -> dict[str, Any]:
    return {
        key: oracle[key]
        for key in (
            "baseline_burdens",
            "generated_burdens",
            "preempted",
            "obligations",
            "acts",
            "cycles",
            "max_generation_depth",
            "event_patterns",
            "normalized_evidence",
            "dependency_graph",
            "generation_graph",
            "parent_relations",
            "projection_relations",
            "event_relations",
            "lifecycle_relations",
        )
    }


def _expected_normalized_dependency(spec: dict[str, Any]) -> list[tuple[str, str]]:
    labels = [f"B{index}" for index in range(1, spec["dimensions"]["baseline_burdens"] + 1)]
    return sorted(tuple(edge) for edge in _checker_dependency_edges(spec["dependency_shape"], labels))


def _relation_rows_preserved(before: Any, after: Any) -> bool:
    if isinstance(before, dict) and isinstance(after, dict):
        return set(before) == set(after) and all(
            _relation_rows_preserved(before[key], after[key]) for key in before
        )
    if isinstance(before, list) and isinstance(after, list):
        return all(row in after for row in before)
    return before == after


def _event_cycle_relations_preserved(
    before: dict[str, Any], after: dict[str, Any]
) -> bool:
    before_local = [edge for edge in before["edges"] if edge[0][0] == edge[1][0]]
    return _relation_rows_preserved(
        before["cycle_patterns"], after["cycle_patterns"]
    ) and _relation_rows_preserved(before_local, after["edges"])


def _relation_holds(relation: str, before: dict[str, Any], after: dict[str, Any], sibling: Path, sibling_spec: dict[str, Any]) -> bool:
    if relation in {"alpha-rename", "payload-length"}:
        return before == after
    if relation == "permutation":
        return (
            before["component_semantics"] == after["component_semantics"]
            and before["observations"] == after["observations"]
            and before["pressures"] == after["pressures"]
            and before["baseline_burdens"] == after["baseline_burdens"]
            and before["generated_burdens"] == after["generated_burdens"]
            and before["obligations"] == after["obligations"]
            and before["acts"] == after["acts"]
            and before["closure"] == after["closure"]
            and before["normalized_evidence"] == after["normalized_evidence"]
        )
    if relation == "split-conservation":
        submoves = sibling_spec["dimensions"]["submoves_per_burden"]
        decisions = _stage(sibling, "02").get("pressure_partition_decisions", [])
        return (
            after["baseline_burdens"] == before["baseline_burdens"] + 1
            and after["pressures"] == before["pressures"] + 1
            and after["hyperedges"] == before["hyperedges"] + 1
            and after["obligations"] == before["obligations"] + submoves
            and after["dependency_graph"] == _expected_normalized_dependency(sibling_spec)
            and _relation_rows_preserved(before["generation_graph"], after["generation_graph"])
            and _relation_rows_preserved(before["parent_relations"], after["parent_relations"])
            and _event_cycle_relations_preserved(before["event_relations"], after["event_relations"])
            and _relation_rows_preserved(before["lifecycle_relations"], after["lifecycle_relations"])
            and any(
                row.get("relation_type") == "split_distinct_functions"
                and len(row.get("pressure_ids", [])) >= 2
                and len(row.get("receiving_burden_ids", [])) >= 2  # topology-relation-arity
                and any(
                    value == "distinct"
                    for value in row.get("same_function_proof", {}).values()
                )
                for row in decisions
            )
        )
    if relation == "merge-with-proof":
        decisions = _stage(sibling, "02").get("pressure_partition_decisions", [])
        return _relation_core(before) == _relation_core(after) and any(
            row.get("relation_type") == "merge_same_function"
            and len(row.get("pressure_ids", [])) >= 2
            and row.get("same_function_proof") == CHECKER_SAME_FUNCTION_PROOF
            and bool(row.get("source_authorization_sha256"))
            and bool(row.get("authorization_sha256"))
            for row in decisions
        )
    if relation == "irrelevant-filler":
        return _relation_core(before) == _relation_core(after) and after["observations"] == before["observations"] + 1
    if relation == "valid-hold":
        return _relation_core(before) == _relation_core(after) and after["hold_routes"] >= before["hold_routes"] + 1 and not after["closure"]
    if relation == "generated-child":
        return (
            after["generated_burdens"] == before["generated_burdens"] + 1
            and after["cycles"] == before["cycles"] + 1
            and after["max_generation_depth"] >= before["max_generation_depth"]
            and after["dependency_graph"] == before["dependency_graph"]
            and _relation_rows_preserved(before["generation_graph"], after["generation_graph"])
            and _relation_rows_preserved(before["parent_relations"], after["parent_relations"])
            and _relation_rows_preserved(before["projection_relations"], after["projection_relations"])
            and _relation_rows_preserved(before["event_relations"], after["event_relations"])
            and _relation_rows_preserved(before["lifecycle_relations"], after["lifecycle_relations"])
        )
    if relation == "preempt-resultant":
        return after["preempted"] == before["preempted"] + 1 and after["cycles"] == before["cycles"]
    raise ValueError(f"unknown metamorphic relation {relation}")


def evaluate_metamorphic_relation(base_spec_path: Path, relation: str, sabotage: bool = False) -> dict[str, Any]:
    if relation not in POSITIVE_RELATIONS:
        raise ValueError(f"unknown metamorphic relation {relation}")
    base_spec_path = base_spec_path.resolve()
    base_spec = validate_spec(_load(base_spec_path))
    applicability = (
        _permutation_applicability(base_spec)
        if relation == "permutation"
        else {
            "applicable": True,
            "reason": "deterministic-transform-defined",
            "component_count": None,
            "component_membership": None,
        }
    )
    if not applicability["applicable"]:
        return {
            "exit_code": 0,
            "status": "not-applicable",
            "name": relation,
            "relation": relation,
            "base_spec": str(base_spec_path),
            "reason": applicability["reason"],
            "component_count": applicability["component_count"],
            "component_membership": applicability["component_membership"],
            "transformed": False,
        }
    with tempfile.TemporaryDirectory(prefix=f"daee-topology-{relation}-") as parent:
        parent_path = Path(parent)
        base_dir = parent_path / "base"
        sibling_dir = parent_path / "sibling"
        generate_case(base_spec_path, base_dir)
        sibling_spec = copy.deepcopy(base_spec)
        if relation == "alpha-rename":
            sibling_spec["seed"] += 1000003
            if sabotage:
                sibling_spec["dimensions"]["baseline_burdens"] += 1
        elif relation == "permutation":
            sibling_spec["baseline_declaration_order"] = [
                ordinal
                for component in reversed(applicability["component_membership"])
                for ordinal in component
            ]
        elif relation == "split-conservation":
            sibling_spec["dimensions"]["input_observations"] += 1
            sibling_spec["dimensions"]["input_pressures"] += 1
            sibling_spec["dimensions"]["baseline_burdens"] += 1
            sibling_spec["dimensions"]["candidate_hyperedges"] += 1
            if sibling_spec["dimensions"]["held_baseline_burdens"]:
                sibling_spec["dimensions"]["held_baseline_burdens"] += 1
            new_pressure = sibling_spec["dimensions"]["input_pressures"]
            new_burden = sibling_spec["dimensions"]["baseline_burdens"]
            split_proof = copy.deepcopy(CHECKER_SAME_FUNCTION_PROOF)
            split_proof["tau_relation"] = "distinct"
            _replace_partition_scope(
                sibling_spec,
                {1, new_pressure},
                _metamorphic_partition_authorization(
                    "metamorphic-split-1",
                    "split_distinct_functions",
                    [1, new_pressure],
                    [1, new_burden],
                    1,
                    split_proof,
                ),
            )
        elif relation == "merge-with-proof":
            sibling_spec["dimensions"]["input_pressures"] = max(2, sibling_spec["dimensions"]["input_pressures"])
            _replace_partition_scope(
                sibling_spec,
                {1, 2},
                _metamorphic_partition_authorization(
                    "metamorphic-merge-1",
                    "merge_same_function",
                    [1, 2],
                    [1],
                    1,
                    CHECKER_SAME_FUNCTION_PROOF,
                ),
            )
        elif relation == "irrelevant-filler":
            sibling_spec["dimensions"]["input_observations"] += 1
        elif relation == "valid-hold":
            sibling_spec["closure_policy"] = "partial-with-live-obligations"
            sibling_spec["dimensions"]["route_candidate_kinds"] = list(sibling_spec["dimensions"]["route_candidate_kinds"]) + [f"unrecognized-route-{sibling_spec['seed']}"]
        elif relation == "generated-child":
            prior_generated = sibling_spec["dimensions"]["generated_burdens"]
            prior_depth = sibling_spec["dimensions"]["generation_depth"]
            sibling_spec["dimensions"]["generated_burdens"] += 1
            if prior_generated == 0 or prior_depth == prior_generated:
                sibling_spec["dimensions"]["generation_depth"] = prior_depth + 1
        elif relation == "preempt-resultant":
            sibling_spec["dimensions"]["preempted_candidates"] += 1
        sibling_spec_path = parent_path / "sibling-spec.json"
        _write_spec(sibling_spec_path, sibling_spec)
        generate_case(sibling_spec_path, sibling_dir)

        if relation == "irrelevant-filler":
            path = sibling_dir / STAGE_FILES["01"]
            payload = _load(path)
            payload["observations"][-1].pop("pressure_id", None)
            payload["observations"][-1]["disposition"] = "non_load_bearing"
            payload["observations"][-1]["payload"] = "irrelevant neutral context"
            _rewrite_json(path, payload)
        elif relation == "payload-length":
            path = sibling_dir / STAGE_FILES["01"]
            payload = _load(path)
            for index, row in enumerate(payload["observations"]):
                row["payload"] = "neutral payload " * (index + 2)
            _rewrite_json(path, payload)

        if sabotage:
            if relation == "permutation":
                path = sibling_dir / STAGE_FILES["04"]
                payload = _load(path)
                payload["burden_cycles"][0], payload["burden_cycles"][1] = (
                    payload["burden_cycles"][1],
                    payload["burden_cycles"][0],
                )
                _rewrite_json(path, payload)
            elif relation == "split-conservation":
                path = sibling_dir / STAGE_FILES["02"]
                payload = _load(path)
                split = next(
                    row
                    for row in payload["pressure_partition_decisions"]
                    if row["relation_type"] == "split_distinct_functions"
                )
                split["source_authorization_sha256"] = "0" * 64
                _rewrite_json(path, payload)
            elif relation == "merge-with-proof":
                path = sibling_dir / STAGE_FILES["02"]
                payload = _load(path)
                merge = next(
                    row
                    for row in payload["pressure_partition_decisions"]
                    if row["relation_type"] == "merge_same_function"
                )
                merge["authorization_sha256"] = "0" * 64
                _rewrite_json(path, payload)
            elif relation == "irrelevant-filler":
                path = sibling_dir / STAGE_FILES["01"]
                payload = _load(path)
                payload["observations"][-1].pop("disposition", None)
                _rewrite_json(path, payload)
            elif relation == "payload-length":
                path = sibling_dir / STAGE_FILES["01"]
                payload = _load(path)
                payload["observations"][0].pop("pressure_id", None)
                _rewrite_json(path, payload)
            elif relation == "valid-hold":
                path = sibling_dir / STAGE_FILES["03"]
                payload = _load(path)
                payload["routes"][-1].pop("differentiator", None)
                _rewrite_json(path, payload)
            elif relation == "generated-child":
                path = sibling_dir / STAGE_FILES["05"]
                payload = _load(path)
                generated = [row for row in payload["burden_cycles"] if row["origin"] == "B_MRP"]
                target = generated[-1]
                target["generation_depth"] = max(0, target["generation_depth"] - 1)
                for row in payload["lifecycle"]:
                    if row["burden_id"] == target["burden_id"]:
                        row["generation_depth"] = target["generation_depth"]
                _rewrite_json(path, payload)
            elif relation == "preempt-resultant":
                path = sibling_dir / STAGE_FILES["05"]
                payload = _load(path)
                preempted_id = _stage(sibling_dir, "02")["preempted_candidates"][-1]["candidate_id"]
                payload["lifecycle"].append({"burden_id": preempted_id, "cycle_id": "invalid", "origin": "B_MRP", "parent_id": None, "generation_depth": 1, "terminal_state": "LANDED", "reread_id": "invalid"})
                _rewrite_json(path, payload)
        refresh_case_bindings(sibling_dir)
        before = normalized_oracle(base_dir)
        after = normalized_oracle(sibling_dir)
        base_declaration_order = _stage(base_dir, "02")["baseline_burden_ids"]
        sibling_declaration_order = _stage(sibling_dir, "02")["baseline_burden_ids"]
        diagnostic = check_generated_directory(sibling_dir)
        holds = diagnostic["exit_code"] == 0 and _relation_holds(relation, before, after, sibling_dir, sibling_spec)
        if sabotage:
            if diagnostic["exit_code"] or not holds:
                return {"exit_code": 1, "status": "rejected", "failure_class": "metamorphic-oracle-sabotage-detected", "relation": relation, "base_spec": str(base_spec_path), "base_dependency_shape": base_spec["dependency_shape"], "sibling_dependency_shape": sibling_spec["dependency_shape"], "component_count": applicability["component_count"], "component_membership": applicability["component_membership"], "base_declaration_order": base_declaration_order, "sibling_declaration_order": sibling_declaration_order, "declaration_order_changed": base_declaration_order != sibling_declaration_order, "transformed": True, "diagnostic": diagnostic, "oracle_before": before, "oracle_after": after}
            return {"exit_code": 0, "status": "false-pass", "relation": relation, "base_spec": str(base_spec_path), "base_dependency_shape": base_spec["dependency_shape"], "sibling_dependency_shape": sibling_spec["dependency_shape"], "oracle_before": before, "oracle_after": after}
        if not holds:
            return {"exit_code": 1, "status": "FAIL", "failure_class": "metamorphic-oracle-mismatch", "relation": relation, "diagnostic": diagnostic, "oracle_before": before, "oracle_after": after}
        return {"exit_code": 0, "status": "preserved", "name": relation, "relation": relation, "base_spec": str(base_spec_path), "base_dependency_shape": base_spec["dependency_shape"], "sibling_dependency_shape": sibling_spec["dependency_shape"], "component_count": applicability["component_count"], "component_membership": applicability["component_membership"], "base_declaration_order": base_declaration_order, "sibling_declaration_order": sibling_declaration_order, "declaration_order_changed": base_declaration_order != sibling_declaration_order, "transformed": True, "sibling_sha256": directory_digest(sibling_dir), "oracle_before": before, "oracle_after": after}


def _selected_specs(path: Path) -> tuple[Path, list[Path]]:
    payload = _load(path)
    if payload.get("schema") == "daee-topology-capacity-probe-set-v1":
        return path.parent, [path.parent / relative for relative in payload.get("specs", [])]
    validate_spec(payload)
    return path.parent, [path]


def run_metamorphic_suite(probe_or_spec_path: Path) -> dict[str, Any]:
    probe_or_spec_path = probe_or_spec_path.resolve()
    _root, specs = _selected_specs(probe_or_spec_path)
    relations = []
    sabotage_relations = []
    applicability_matrix = []
    not_applicable_rows = []
    for spec_path in specs:
        spec = validate_spec(_load(spec_path))
        for relation in POSITIVE_RELATIONS:
            applicability = (
                _permutation_applicability(spec)
                if relation == "permutation"
                else {
                    "applicable": True,
                    "reason": "deterministic-transform-defined",
                    "component_count": None,
                    "component_membership": None,
                }
            )
            applicability_row = {
                "base_spec": str(spec_path.resolve()),
                "relation": relation,
                **applicability,
                "transformed": applicability["applicable"],
            }
            applicability_matrix.append(
                applicability_row
            )
            if not applicability["applicable"]:
                not_applicable_rows.append(applicability_row)
                continue
            result = evaluate_metamorphic_relation(spec_path, relation)
            if result["exit_code"]:
                return result
            relations.append(result)
            sabotage = evaluate_metamorphic_relation(spec_path, relation, sabotage=True)
            if sabotage.get("failure_class") != "metamorphic-oracle-sabotage-detected":
                return {
                    "exit_code": 1,
                    "status": "FAIL",
                    "failure_class": "metamorphic-sabotage-false-pass",
                    "base_spec": str(spec_path.resolve()),
                    "relation": relation,
                    "diagnostic": sabotage,
                }
            sabotage_relations.append(sabotage)
    negatives = {
        "delete-owner": ("03", "owner-obligation-coverage", "eligible-owner-missing"),
        "delete-act": ("04", "owner-obligation-coverage", "eligible-obligation-unpaid"),
        "delete-reread": ("05", "reread-terminal-coverage", "instantiated-burden-missing-reread"),
        "delete-nar": ("06", "witness-projection-parity", "nar-activation-mismatch"),
        "delete-projection-join": ("07", "public-projection-parity", "projection-join-missing"),
    }
    base = validate_spec(_load(specs[0]))
    with tempfile.TemporaryDirectory(prefix="daee-topology-negative-metamorphic-") as parent:
        parent_path = Path(parent)
        for index, (operation, expected) in enumerate(negatives.items()):
            spec = copy.deepcopy(base)
            spec["mutation"] = {"operation": operation, "target": "generated:1" if operation == "delete-reread" else "first"}
            if operation == "delete-reread" and not spec["dimensions"]["generated_burdens"]:
                spec["dimensions"]["generated_burdens"] = 1
                spec["dimensions"]["generation_depth"] = 1
            spec_path = parent_path / f"{operation}.json"
            _write_spec(spec_path, spec)
            destination = parent_path / f"case-{index}"
            generate_case(spec_path, destination)
            diagnostic = check_generated_directory(destination)
            observed = (diagnostic.get("earliest_stage"), diagnostic.get("failure_class"), diagnostic.get("failure_subcode"))
            if observed != expected:
                return {"exit_code": 1, "status": "FAIL", "name": operation, "expected": expected, "observed": observed, "diagnostic": diagnostic}
            relations.append({"name": operation, "status": "right-reason-rejected", "base_spec": str(specs[0]), "sibling_sha256": directory_digest(destination), "oracle_before": None, "oracle_after": None, "diagnostic": diagnostic})
    return {
        "checker_id": "topology-capacity-properties",
        "status": "PASS",
        "exit_code": 0,
        "probe_set": str(probe_or_spec_path),
        "selected_relation_rows": len(specs) * len(POSITIVE_RELATIONS),
        "executed_positive_relations": len(relations) - len(negatives),
        "executed_sabotage_relations": len(sabotage_relations),
        "not_applicable_relations": len(not_applicable_rows),
        "applicability_matrix": applicability_matrix,
        "not_applicable_rows": not_applicable_rows,
        "sabotage_relations": sabotage_relations,
        "relations": relations,
        "non_claim": "metamorphic structural oracles are not semantic truth",
    }


def run_full_matrix(root: Path) -> dict[str, Any]:
    burdens_axis = (1, 10, 20, 21)
    submoves_axis = (1, 3, 6, 8)
    shape_axis = (
        "independent",
        "chain",
        "fan-out",
        "fan-in",
        "diamond",
        "mixed",
        "held-activation",
        "generated-chain",
        "generated-fan-out",
        "pre-emption",
        "noetic-cycle-loopbreak",
    )
    rows = []
    generated_bytes = 0
    max_case_bytes = 0
    generation_ms = 0.0
    validation_ms = 0.0
    tracemalloc.start()
    try:
        with tempfile.TemporaryDirectory(prefix="daee-topology-full-matrix-") as parent:
            parent_path = Path(parent)
            for index, (burdens, submoves, shape) in enumerate(itertools.product(burdens_axis, submoves_axis, shape_axis)):
                generated_count = 3 if shape in {"generated-chain", "generated-fan-out"} else 2 if shape == "mixed" else 0
                depth = 3 if shape == "generated-chain" else 2 if shape == "mixed" else 1 if shape == "generated-fan-out" else 0
                unknown = burdens == 21 and submoves == 8  # telemetry-canary-selection
                spec = {
                    "schema": "daee-topology-capacity-spec-v1",
                    "seed": 900000 + index,
                    "dimensions": {
                        "input_observations": max(2, burdens),
                        "input_pressures": max(2, burdens),
                        "candidate_states": 4,
                        "candidate_hyperedges": 2,
                        "baseline_burdens": burdens,
                        "submoves_per_burden": submoves,
                        "held_baseline_burdens": 1 if shape == "held-activation" else 0,
                        "generated_burdens": generated_count,
                        "generation_depth": depth,
                        "preempted_candidates": 1 if shape == "pre-emption" else 0,
                        "route_candidate_kinds": ["direct", f"full-matrix-unknown-{index}"] if unknown else ["direct"],
                    },
                    "dependency_shape": shape,
                    "closure_policy": "partial-with-live-obligations" if unknown else "complete-when-no-live-obligations",
                }
                spec_path = parent_path / f"spec-{index}.json"
                case_dir = parent_path / f"case-{index}"
                _write_spec(spec_path, spec)
                started = time.perf_counter()
                generate_case(spec_path, case_dir)
                generation_ms += (time.perf_counter() - started) * 1000
                case_bytes = sum(path.stat().st_size for path in case_dir.iterdir() if path.is_file())
                generated_bytes += case_bytes
                max_case_bytes = max(max_case_bytes, case_bytes)
                started = time.perf_counter()
                diagnostic = check_generated_directory(case_dir)
                validation_ms += (time.perf_counter() - started) * 1000
                if diagnostic["exit_code"]:
                    return {"checker_id": "topology-capacity-properties", "mode": "full-matrix", "status": "FAIL", "exit_code": 1, "case": index, "spec": spec, "diagnostic": diagnostic}
                rows.append({"burdens": burdens, "submoves": submoves, "shape": shape, "signature": dimension_signature(case_dir)})
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
    return {
        "checker_id": "topology-capacity-properties",
        "mode": "full-matrix",
        "status": "PASS",
        "exit_code": 0,
        "matrix_cases": len(rows),
        "axes": {"burdens": list(burdens_axis), "submoves": list(submoves_axis), "shapes": list(shape_axis)},
        "resource_telemetry": {
            "generated_bytes": generated_bytes,
            "max_case_bytes": max_case_bytes,
            "generation_ms": round(generation_ms, 3),
            "validation_ms": round(validation_ms, 3),
            "peak_traced_bytes": peak,
            "telemetry_only": "resource measurements are not semantic floors, ceilings, or runtime law",
        },
        "non_claim": "finite deterministic matrix coverage is not universal semantic correctness",
    }


def self_test(root: Path) -> dict[str, Any]:
    result = check_probe_set(root / "tests" / "topology-capacity" / "probe-set.json")
    if result["exit_code"]:
        return result
    meta = run_metamorphic_suite(root / "tests" / "topology-capacity" / "probe-set.json")
    if meta["exit_code"]:
        return meta
    return {"checker_id": "topology-capacity-properties", "status": "PASS", "exit_code": 0, "probe_cases": len(result["cases"]), "metamorphic_relations": len(meta["relations"]), "non_claim": "structural probes are not semantic truth"}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--probe-set", type=Path)
    parser.add_argument("--through-stage")
    parser.add_argument("--metamorphic", action="store_true")
    parser.add_argument("--explain-case", type=Path)
    parser.add_argument("--replay-run", type=Path)
    parser.add_argument("--full-matrix", action="store_true")
    parser.add_argument("--json", dest="json_out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(__file__).resolve().parents[1]
    if args.explain_case:
        with tempfile.TemporaryDirectory(prefix="daee-topology-explain-") as parent:
            result = check_spec_path(args.explain_case, Path(parent))
    elif args.replay_run:
        result = check_generated_directory(args.replay_run, args.through_stage)
    elif args.probe_set:
        result = run_metamorphic_suite(args.probe_set) if args.metamorphic else check_probe_set(args.probe_set, args.through_stage)
    elif args.full_matrix:
        result = run_full_matrix(root)
    elif args.self_test:
        result = self_test(root)
    else:
        parser.error("select --self-test, --probe-set, --explain-case, --replay-run, or --full-matrix")
    encoded = json.dumps(result, sort_keys=True)
    if args.json_out:
        if args.json_out.exists():
            raise SystemExit("refusing to overwrite JSON report")
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return int(result.get("exit_code", 1))


if __name__ == "__main__":
    raise SystemExit(main())
