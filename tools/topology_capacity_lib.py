#!/usr/bin/env python3
"""Pure deterministic semantics for topic-neutral topology capacity probes."""

from __future__ import annotations

import copy
import hashlib
import json
import random
import re
from typing import Any, Iterable


SPEC_SCHEMA = "daee-topology-capacity-spec-v1"
SHAPES = {
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
    "event-dag-cycle",
    "noetic-cycle-loopbreak",
}
POSITIVE_COUNTS = (
    "input_observations",
    "input_pressures",
    "candidate_states",
    "candidate_hyperedges",
    "baseline_burdens",
    "submoves_per_burden",
)
NONNEGATIVE_COUNTS = (
    "held_baseline_burdens",
    "generated_burdens",
    "generation_depth",
    "preempted_candidates",
)
DIMENSION_KEYS = set(POSITIVE_COUNTS + NONNEGATIVE_COUNTS + ("route_candidate_kinds",))
SPEC_KEYS = {
    "schema",
    "seed",
    "dimensions",
    "dependency_shape",
    "closure_policy",
    "baseline_declaration_order",
    "partition_authorizations",
    "shared_operation_authorizations",
    "mutation",
    "taint",
}
KNOWN_ROUTE_KINDS = {"direct", "held-activation", "generated", "preempted", "loopbreak"}
IDENTITY_TOKEN_RE = re.compile(
    r"\b(?:obs|pressure|candidate|hyperedge|burden|generated|preempted|obligation|owner|register|body|route|cycle|event|reread)-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
FILLER_RE = re.compile(r"\b(?:neutral\s+)?filler\b", re.IGNORECASE)
PARTITION_AUTHORIZATION_FIELDS = (
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
SHARED_OPERATION_SOURCE_FIELDS = (
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
SAME_FUNCTION_PROOF = {
    "tau_relation": "same",
    "source_frame_relation": "same",
    "claim_cluster_relation": "same",
    "register_transition_relation": "compatible",
    "owner_operation_relation": "compatible",
    "restoration_vector_relation": "same",
    "collapse_dependency_relation": "same",
}


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def normalized_evidence_body(value: str) -> str:
    """Normalize evidence independently of record IDs, padding, and spacing."""
    text = IDENTITY_TOKEN_RE.sub("<identity>", value.lower())
    text = FILLER_RE.sub(" ", text)
    return " ".join(text.split())


def make_partition_authorization(
    authorization_key: str,
    relation_type: str,
    pressure_ordinals: Iterable[int],
    receiving_burden_ordinals: Iterable[int],
    owner_ordinal: int,
    evidence_identity: str,
    same_function_proof: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = {
        "authorization_key": authorization_key,
        "relation_type": relation_type,
        "pressure_ordinals": list(pressure_ordinals),
        "receiving_burden_ordinals": list(receiving_burden_ordinals),
        "owner_ordinal": owner_ordinal,
        "operation": f"neutral-operation-{owner_ordinal}",
        "register_ordinal": owner_ordinal,
        "evidence_identity": evidence_identity,
        "same_function_proof": copy.deepcopy(
            same_function_proof if same_function_proof is not None else SAME_FUNCTION_PROOF
        ),
    }
    payload["authorization_sha256"] = canonical_sha256(payload)
    return payload


def make_shared_operation_authorization(
    authorization_key: str,
    upstream_partition_keys: Iterable[str],
    pressure_ordinals: Iterable[int],
    receiving_burden_ordinals: Iterable[int],
    owner_ordinal: int,
    evidence_identity: str,
) -> dict[str, Any]:
    payload = {
        "authorization_key": authorization_key,
        "upstream_partition_keys": list(upstream_partition_keys),
        "pressure_ordinals": list(pressure_ordinals),
        "receiving_burden_ordinals": list(receiving_burden_ordinals),
        "owner_ordinal": owner_ordinal,
        "operation": f"neutral-operation-{owner_ordinal}",
        "register_ordinal": owner_ordinal,
        "evidence_identity": evidence_identity,
        "same_function_proof": copy.deepcopy(SAME_FUNCTION_PROOF),
    }
    payload["authorization_sha256"] = canonical_sha256(payload)
    return payload


def resolve_partition_authorizations(
    spec: dict[str, Any],
    pressures: list[str],
    canonical_baseline: list[str],
) -> list[dict[str, Any]]:
    resolved = []
    seed = spec["seed"]
    for index, source in enumerate(spec.get("partition_authorizations", []), 1):
        payload = {
            "decision_id": stable_id(seed, "partition", index),
            "source_authorization_key": source["authorization_key"],
            "source_authorization_sha256": source["authorization_sha256"],
            "relation_type": source["relation_type"],
            "pressure_ids": [pressures[item - 1] for item in source["pressure_ordinals"]],
            "receiving_burden_ids": [
                canonical_baseline[item - 1]
                for item in source["receiving_burden_ordinals"]
            ],
            "owner_id": stable_id(seed, "owner", source["owner_ordinal"]),
            "operation": source["operation"],
            "register_id": stable_id(seed, "register", source["register_ordinal"]),
            "evidence_identity": source["evidence_identity"],
            "same_function_proof": copy.deepcopy(source["same_function_proof"]),
        }
        receiving = payload["receiving_burden_ids"]
        payload["pressure_to_burden"] = [
            {
                "pressure_id": pressure_id,
                "burden_id": receiving[0] if len(receiving) == 1 else receiving[position],
            }
            for position, pressure_id in enumerate(payload["pressure_ids"])
        ]
        payload["authorization_sha256"] = canonical_sha256(payload)
        resolved.append(payload)
    return resolved


def resolve_shared_operation_authorizations(
    spec: dict[str, Any],
    pressures: list[str],
    canonical_baseline: list[str],
    partition_decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    partition_by_key = {
        row["source_authorization_key"]: row for row in partition_decisions
    }
    resolved = []
    seed = spec["seed"]
    for index, source in enumerate(spec.get("shared_operation_authorizations", []), 1):
        upstream = [partition_by_key[key] for key in source["upstream_partition_keys"]]
        payload = {
            "shared_authorization_id": stable_id(seed, "sharedauth", index),
            "source_authorization_key": source["authorization_key"],
            "source_authorization_sha256": source["authorization_sha256"],
            "upstream_partition_decision_ids": [row["decision_id"] for row in upstream],
            "upstream_partition_authorization_sha256": [
                row["authorization_sha256"] for row in upstream
            ],
            "pressure_ids": [pressures[item - 1] for item in source["pressure_ordinals"]],
            "receiving_burden_ids": [
                canonical_baseline[item - 1]
                for item in source["receiving_burden_ordinals"]
            ],
            "owner_id": stable_id(seed, "owner", source["owner_ordinal"]),
            "operation": source["operation"],
            "register_id": stable_id(seed, "register", source["register_ordinal"]),
            "evidence_identity": source["evidence_identity"],
            "same_function_proof": copy.deepcopy(source["same_function_proof"]),
        }
        payload["authorization_sha256"] = canonical_sha256(payload)
        resolved.append(payload)
    return resolved


def validate_spec(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("spec must be an object")
    value = copy.deepcopy(value)
    if value.get("schema") != SPEC_SCHEMA:
        raise ValueError(f"schema must be {SPEC_SCHEMA}")
    unknown_top = sorted(set(value) - SPEC_KEYS)
    if unknown_top:
        raise ValueError(f"unknown spec fields: {unknown_top}")
    seed = value.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("dimensions must be an object")
    unknown_dimensions = sorted(set(dimensions) - DIMENSION_KEYS)
    if unknown_dimensions:
        raise ValueError(f"unknown dimension fields: {unknown_dimensions}")
    for key in POSITIVE_COUNTS:
        item = dimensions.get(key)
        if not isinstance(item, int) or isinstance(item, bool) or item < 1:
            raise ValueError(f"dimensions.{key} must be a positive integer")
    for key in NONNEGATIVE_COUNTS:
        item = dimensions.get(key)
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            raise ValueError(f"dimensions.{key} must be a nonnegative integer")
    if dimensions["held_baseline_burdens"] > dimensions["baseline_burdens"]:
        raise ValueError("held_baseline_burdens cannot exceed baseline_burdens")
    if dimensions["generated_burdens"] and not dimensions["generation_depth"]:
        raise ValueError("generated burdens require positive generation_depth")
    if not dimensions["generated_burdens"] and dimensions["generation_depth"]:
        raise ValueError("generation_depth requires generated burdens")
    if dimensions["generation_depth"] > dimensions["generated_burdens"]:
        raise ValueError("generation_depth cannot exceed generated_burdens")
    routes = dimensions.get("route_candidate_kinds")
    if not isinstance(routes, list) or not routes or any(not isinstance(x, str) or not x for x in routes):
        raise ValueError("route_candidate_kinds must be a nonempty unique string array")
    if len(routes) != len(set(routes)):
        raise ValueError("route_candidate_kinds must be unique")
    if value.get("dependency_shape") not in SHAPES:
        raise ValueError("dependency_shape is not registered")
    if value.get("closure_policy") not in {
        "complete-when-no-live-obligations",
        "partial-with-live-obligations",
    }:
        raise ValueError("closure_policy is not registered")
    declaration_order = value.get("baseline_declaration_order")
    if declaration_order is not None and (
        not isinstance(declaration_order, list)
        or any(not isinstance(item, int) or isinstance(item, bool) for item in declaration_order)
        or sorted(declaration_order) != list(range(1, dimensions["baseline_burdens"] + 1))
    ):
        raise ValueError(
            "baseline_declaration_order must be an exact permutation of baseline burden ordinals"
        )
    if "partition_authorizations" not in value:
        value["partition_authorizations"] = [
            make_partition_authorization(
                authorization_key=f"pressure-partition-{ordinal}",
                relation_type="one_to_one",
                pressure_ordinals=[ordinal],
                receiving_burden_ordinals=[
                    ((ordinal - 1) % dimensions["baseline_burdens"]) + 1
                ],
                owner_ordinal=((ordinal - 1) % dimensions["submoves_per_burden"]) + 1,
                evidence_identity=canonical_sha256(
                    {
                        "pressure_ordinal": ordinal,
                        "source_frame": "neutral-source-frame",
                    }
                ),
            )
            for ordinal in range(1, dimensions["input_pressures"] + 1)
        ]
    authorizations = value.get("partition_authorizations", [])
    if not isinstance(authorizations, list):
        raise ValueError("partition_authorizations must be an array")
    seen_keys: set[str] = set()
    for authorization in authorizations:
        if not isinstance(authorization, dict):
            raise ValueError("partition authorization must be an object")
        if set(authorization) != set(PARTITION_AUTHORIZATION_FIELDS) | {
            "authorization_sha256"
        }:
            raise ValueError("partition authorization fields are not canonical")
        key = authorization.get("authorization_key")
        if not isinstance(key, str) or not key or key in seen_keys:
            raise ValueError("partition authorization keys must be unique nonempty strings")
        seen_keys.add(key)
        relation_type = authorization.get("relation_type")
        if relation_type not in {
            "one_to_one",
            "split_distinct_functions",
            "keep_distinct",
            "merge_same_function",
            "hold_unresolved",
        }:
            raise ValueError("partition authorization relation_type is invalid")
        pressure_ordinals = authorization.get("pressure_ordinals")
        burden_ordinals = authorization.get("receiving_burden_ordinals")
        if (
            not isinstance(pressure_ordinals, list)
            or not pressure_ordinals
            or len(pressure_ordinals) != len(set(pressure_ordinals))
            or any(
                not isinstance(item, int)
                or isinstance(item, bool)
                or item < 1
                or item > dimensions["input_pressures"]
                for item in pressure_ordinals
            )
        ):
            raise ValueError("partition authorization pressure ordinals are invalid")
        if (
            not isinstance(burden_ordinals, list)
            or not burden_ordinals
            or len(burden_ordinals) != len(set(burden_ordinals))
            or any(
                not isinstance(item, int)
                or isinstance(item, bool)
                or item < 1
                or item > dimensions["baseline_burdens"]
                for item in burden_ordinals
            )
        ):
            raise ValueError("partition authorization burden ordinals are invalid")
        owner_ordinal = authorization.get("owner_ordinal")
        register_ordinal = authorization.get("register_ordinal")
        if (
            not isinstance(owner_ordinal, int)
            or isinstance(owner_ordinal, bool)
            or not 1 <= owner_ordinal <= dimensions["submoves_per_burden"]
            or register_ordinal != owner_ordinal
            or authorization.get("operation") != f"neutral-operation-{owner_ordinal}"
        ):
            raise ValueError("partition authorization owner/operation/register axes are invalid")
        evidence_identity = authorization.get("evidence_identity")
        if not isinstance(evidence_identity, str) or re.fullmatch(r"[0-9a-f]{64}", evidence_identity) is None:
            raise ValueError("partition authorization evidence identity must be sha256")
        proof = authorization.get("same_function_proof")
        if not isinstance(proof, dict) or set(proof) != set(SAME_FUNCTION_PROOF):
            raise ValueError("partition authorization same_function_proof axes are incomplete")
        if relation_type == "merge_same_function" and (
            len(pressure_ordinals) < 2
            or proof != SAME_FUNCTION_PROOF
        ):
            raise ValueError("merge authorization requires every Plan03 same-function axis")
        if relation_type == "split_distinct_functions" and (
            len(pressure_ordinals) < 2
            or len(burden_ordinals) < 2  # topology-relation-arity: split has plural receivers
            or not any(value == "distinct" for value in proof.values())
        ):
            raise ValueError("split authorization requires distinct-function axes and routes")
        if relation_type == "one_to_one" and (
            len(pressure_ordinals) != 1 or len(burden_ordinals) != 1
        ):
            raise ValueError("one_to_one authorization requires one pressure and one burden")
        if len(burden_ordinals) not in {1, len(pressure_ordinals)}:
            raise ValueError("partition authorization mapping arity is invalid")
        source_payload = {
            field: copy.deepcopy(authorization[field])
            for field in PARTITION_AUTHORIZATION_FIELDS
        }
        if authorization.get("authorization_sha256") != canonical_sha256(source_payload):
            raise ValueError("partition authorization hash mismatch")
    pressure_coverage = [
        item
        for authorization in authorizations
        for item in authorization["pressure_ordinals"]
    ]
    if sorted(pressure_coverage) != list(range(1, dimensions["input_pressures"] + 1)):
        raise ValueError(
            "partition authorizations must cover each pressure exactly once"
        )
    partition_by_key = {
        authorization["authorization_key"]: authorization
        for authorization in authorizations
    }
    shared_authorizations = value.get("shared_operation_authorizations", [])
    if not isinstance(shared_authorizations, list):
        raise ValueError("shared_operation_authorizations must be an array")
    seen_shared_keys: set[str] = set()
    seen_shared_scopes: set[tuple[Any, ...]] = set()
    for authorization in shared_authorizations:
        if not isinstance(authorization, dict) or set(authorization) != set(
            SHARED_OPERATION_SOURCE_FIELDS
        ) | {"authorization_sha256"}:
            raise ValueError("shared operation source authorization fields are not canonical")
        key = authorization.get("authorization_key")
        if not isinstance(key, str) or not key or key in seen_shared_keys:
            raise ValueError("shared operation authorization keys must be unique")
        seen_shared_keys.add(key)
        upstream_keys = authorization.get("upstream_partition_keys")
        if (
            not isinstance(upstream_keys, list)
            or not upstream_keys
            or len(upstream_keys) != len(set(upstream_keys))
            or any(item not in partition_by_key for item in upstream_keys)
        ):
            raise ValueError("shared operation upstream partition keys are invalid")
        pressure_ordinals = authorization.get("pressure_ordinals")
        burden_ordinals = authorization.get("receiving_burden_ordinals")
        upstream_pressures = [
            pressure
            for upstream_key in upstream_keys
            for pressure in partition_by_key[upstream_key]["pressure_ordinals"]
        ]
        upstream_burdens = {
            burden
            for upstream_key in upstream_keys
            for burden in partition_by_key[upstream_key]["receiving_burden_ordinals"]
        }
        if (
            not isinstance(pressure_ordinals, list)
            or len(pressure_ordinals) < 2
            or pressure_ordinals != upstream_pressures
            or not isinstance(burden_ordinals, list)
            or not burden_ordinals
            or not set(burden_ordinals).issubset(upstream_burdens)
        ):
            raise ValueError("shared operation scope does not match upstream partitions")
        owner_ordinal = authorization.get("owner_ordinal")
        if (
            not isinstance(owner_ordinal, int)
            or isinstance(owner_ordinal, bool)
            or not 1 <= owner_ordinal <= dimensions["submoves_per_burden"]
            or authorization.get("register_ordinal") != owner_ordinal
            or authorization.get("operation") != f"neutral-operation-{owner_ordinal}"
            or authorization.get("same_function_proof") != SAME_FUNCTION_PROOF
            or re.fullmatch(r"[0-9a-f]{64}", str(authorization.get("evidence_identity"))) is None
        ):
            raise ValueError("shared operation Plan03 axes are invalid")
        source_payload = {
            field: copy.deepcopy(authorization[field])
            for field in SHARED_OPERATION_SOURCE_FIELDS
        }
        if authorization.get("authorization_sha256") != canonical_sha256(source_payload):
            raise ValueError("shared operation source authorization hash mismatch")
        scope = (
            tuple(upstream_keys),
            tuple(pressure_ordinals),
            tuple(burden_ordinals),
            owner_ordinal,
            authorization["operation"],
            authorization["register_ordinal"],
            authorization["evidence_identity"],
        )
        if scope in seen_shared_scopes:
            raise ValueError("duplicate shared operation source authorization")
        seen_shared_scopes.add(scope)
    mutation = value.get("mutation")
    if mutation is not None and (
        not isinstance(mutation, dict)
        or not isinstance(mutation.get("operation"), str)
        or not isinstance(mutation.get("target"), str)
    ):
        raise ValueError("mutation requires operation and target strings")
    return value


def stable_id(seed: int, namespace: str, ordinal: int) -> str:
    digest = hashlib.sha256(f"{seed}:{namespace}:{ordinal}".encode("ascii")).hexdigest()[:12]
    return f"{namespace}-{digest}"


def stable_ids(seed: int, namespace: str, count: int) -> list[str]:
    return [stable_id(seed, namespace, index + 1) for index in range(count)]


def stable_order(seed: int, namespace: str, values: Iterable[str]) -> list[str]:
    ordered = list(values)
    random.Random(f"{seed}:{namespace}").shuffle(ordered)
    return ordered


def dependency_edges(shape: str, burdens: list[str]) -> list[list[str]]:
    if shape == "noetic-cycle-loopbreak" and burdens:
        return [[burdens[i], burdens[(i + 1) % len(burdens)]] for i in range(len(burdens))]
    if len(burdens) < 2 or shape in {"independent", "pre-emption"}:  # topology-constructor-arity
        return []
    if shape in {"chain", "generated-chain", "held-activation"}:
        return [[burdens[i], burdens[i + 1]] for i in range(len(burdens) - 1)]
    if shape in {"fan-out", "generated-fan-out"}:
        return [[burdens[0], item] for item in burdens[1:]]
    if shape == "fan-in":
        return [[item, burdens[-1]] for item in burdens[:-1]]
    if shape == "diamond" and len(burdens) >= 4:  # topology-constructor-arity
        return [[burdens[0], burdens[1]], [burdens[0], burdens[2]], [burdens[1], burdens[3]], [burdens[2], burdens[3]]]
    midpoint = max(1, len(burdens) // 2)
    return [[burdens[i], burdens[i + 1]] for i in range(midpoint - 1)] + [
        [burdens[0], item] for item in burdens[midpoint:]
    ]


def acyclic_after_loopbreak(edges: list[list[str]]) -> list[list[str]]:
    return edges[:-1] if edges else []


def expected_dimension_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    spec = validate_spec(spec)
    seed = spec["seed"]
    dims = spec["dimensions"]
    observations = stable_ids(seed, "obs", dims["input_observations"])
    pressures = stable_ids(seed, "pressure", dims["input_pressures"])
    candidates = stable_ids(seed, "candidate", dims["candidate_states"])
    hyperedges = stable_ids(seed, "hyperedge", dims["candidate_hyperedges"])
    canonical_baseline = stable_ids(seed, "burden", dims["baseline_burdens"])
    declaration_order = spec.get(
        "baseline_declaration_order",
        list(range(1, dims["baseline_burdens"] + 1)),
    )
    baseline = [canonical_baseline[index - 1] for index in declaration_order]
    generated = stable_ids(seed, "generated", dims["generated_burdens"])
    preempted = stable_ids(seed, "preempted", dims["preempted_candidates"])
    all_burdens = baseline + generated
    canonical_all_burdens = canonical_baseline + generated
    canonical_cycle_by_burden = {
        burden_id: stable_id(seed, "cycle", index + 1)
        for index, burden_id in enumerate(canonical_all_burdens)
    }
    cycle_rows: list[dict[str, Any]] = []
    for burden_id in all_burdens:
        cycle_rows.append(
            {
                "cycle_id": canonical_cycle_by_burden[burden_id],
                "burden_id": burden_id,
                "origin": "B_LA" if burden_id in baseline else "B_MRP",
            }
        )
    cycle_by_burden = {row["burden_id"]: row["cycle_id"] for row in cycle_rows}
    obligations_by_burden: dict[str, list[dict[str, Any]]] = {}
    for burden_index, burden_id in enumerate(canonical_all_burdens):
        rows = []
        for ordinal in range(1, dims["submoves_per_burden"] + 1):
            obligation_id = stable_id(seed, "obligation", burden_index * dims["submoves_per_burden"] + ordinal)
            rows.append(
                {
                    "obligation_id": obligation_id,
                    "burden_id": burden_id,
                    "pressure_id": pressures[burden_index % len(pressures)],
                    "owner_id": stable_id(seed, "owner", ordinal),
                    "register_id": stable_id(seed, "register", ordinal),
                    "operation": f"neutral-operation-{ordinal}",
                    "body_ref": stable_id(seed, "body", burden_index * dims["submoves_per_burden"] + ordinal),
                    "cycle_id": cycle_by_burden[burden_id],
                }
            )
        obligations_by_burden[burden_id] = rows
    obligation_rows = [
        row for burden_id in all_burdens for row in obligations_by_burden[burden_id]
    ]
    obligations = [row["obligation_id"] for row in obligation_rows]
    held = canonical_baseline[-dims["held_baseline_burdens"] :] if dims["held_baseline_burdens"] else []
    generation: list[dict[str, Any]] = []
    requested_depth = dims["generation_depth"]
    for index, child in enumerate(generated):
        if index < requested_depth:
            parent = canonical_baseline[0] if index == 0 else generated[index - 1]
        elif requested_depth <= 1:
            parent = canonical_baseline[0]
        else:
            parent = generated[requested_depth - 2]
        parent_depth = 0
        if parent in generated:
            parent_depth = next(row["depth"] for row in generation if row["burden_id"] == parent)
        depth = parent_depth + 1
        generation.append(
            {
                "burden_id": child,
                "parent_id": parent,
                "parent_cycle_id": cycle_by_burden[parent],
                "cycle_id": cycle_by_burden[child],
                "depth": depth,
            }
        )
    generation_by_burden = {row["burden_id"]: row for row in generation}
    for row in cycle_rows:
        generated_row = generation_by_burden.get(row["burden_id"])
        row["parent_cycle_id"] = generated_row["parent_cycle_id"] if generated_row else None
        row["generation_depth"] = generated_row["depth"] if generated_row else 0
        row["activated_from_hold"] = row["burden_id"] in held
    noetic_pre = dependency_edges(spec["dependency_shape"], canonical_baseline)
    if spec["dependency_shape"] == "noetic-cycle-loopbreak":
        noetic_post = acyclic_after_loopbreak(noetic_pre)
    else:
        noetic_post = list(noetic_pre)
    cycle_events: list[dict[str, Any]] = []
    event_ordinal = 0
    for cycle in cycle_rows:
        if cycle["origin"] == "B_MRP":
            kinds = ("instantiate", "stage03-reentry", "execute", "land", "reread")
        elif cycle["activated_from_hold"]:
            kinds = ("hold", "hold-disposition", "activate", "stage03-reentry", "execute", "land", "reread")
        else:
            kinds = ("route", "execute", "land", "reread")
        ids = []
        for kind in kinds:
            event_ordinal += 1
            event_id = stable_id(seed, "event", event_ordinal)
            ids.append(event_id)
            cycle_events.append(
                {
                    "event_id": event_id,
                    "cycle_id": cycle["cycle_id"],
                    "kind": kind,
                    "ordinal": event_ordinal,
                }
            )
        cycle["event_ids"] = ids
        cycle["event_kinds"] = list(kinds)
    event_ids = [row["event_id"] for row in cycle_events]
    event_edges = [[event_ids[i], event_ids[i + 1]] for i in range(len(event_ids) - 1)]
    partition_decisions = resolve_partition_authorizations(
        spec, pressures, canonical_baseline
    )
    shared_authorizations = resolve_shared_operation_authorizations(
        spec, pressures, canonical_baseline, partition_decisions
    )
    return {
        "schema": "daee-topology-dimensions-v1",
        "seed": seed,
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
        "obligation_ids": obligations,
        "obligations": obligation_rows,
        "pressure_partition_decisions": partition_decisions,
        "shared_operation_authorizations": shared_authorizations,
        "burden_cycles": cycle_rows,
        "cycle_events": cycle_events,
        "generation": generation,
        "route_candidate_kinds": list(dims["route_candidate_kinds"]),
        "noetic_edges_pre_loopbreak": noetic_pre,
        "noetic_edges_post_loopbreak": noetic_post,
        "event_ids": event_ids,
        "event_edges": event_edges,
        "closure_policy": spec["closure_policy"],
    }


def build_stage_records(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = expected_dimension_manifest(spec)
    seed = manifest["seed"]
    observations = [
        {
            "observation_id": item,
            "payload": f"neutral observation payload {index + 1}",
            "pressure_id": manifest["pressure_ids"][index % len(manifest["pressure_ids"])],
        }
        for index, item in enumerate(manifest["source_observation_ids"])
    ]
    statuses = ("selected", "held", "merged", "rejected")
    candidates = []
    for index, item in enumerate(manifest["candidate_state_ids"]):
        status = statuses[index % len(statuses)]
        row = {"candidate_id": item, "status": status, "basis": f"neutral terminal basis {index + 1}"}
        if status == "merged":
            row["merged_into"] = manifest["candidate_state_ids"][0]
        candidates.append(row)
    pressure_route_by_id = {
        mapping["pressure_id"]: mapping["burden_id"]
        for decision in manifest["pressure_partition_decisions"]
        for mapping in decision["pressure_to_burden"]
    }
    pressure_rows = [
        {
            "pressure_id": pressure,
            "observation_id": manifest["source_observation_ids"][index % len(manifest["source_observation_ids"])],
            "status": "routed",
            "burden_id": pressure_route_by_id[pressure],
        }
        for index, pressure in enumerate(manifest["pressure_ids"])
    ]
    hyperedges = [
        {
            "hyperedge_id": item,
            "incoming_pressure_ids": [manifest["pressure_ids"][index % len(manifest["pressure_ids"])]],
            "receiving_burden_id": manifest["baseline_burden_ids"][index % len(manifest["baseline_burden_ids"])],
            "decision": "candidate-relation",
        }
        for index, item in enumerate(manifest["candidate_hyperedge_ids"])
    ]
    route_rows = []
    for index, kind in enumerate(manifest["route_candidate_kinds"]):
        unknown = kind not in KNOWN_ROUTE_KINDS
        route_rows.append(
            {
                "route_id": stable_id(seed, "route", index + 1),
                "kind": kind,
                "disposition": "HOLD" if unknown else "selected",
                "differentiator": "classify unrecognized route kind" if unknown else None,
                "next_action": "retain visible route and observe differentiator" if unknown else "execute obligations",
            }
        )
    cycle_manifest = manifest["burden_cycles"]
    stage03_cycles = []
    stage04_cycles = []
    stage05_cycles = []
    for index, cycle in enumerate(cycle_manifest):
        stage03_ref = stable_id(seed, "stage03cycle", index + 1)
        stage04_ref = stable_id(seed, "stage04cycle", index + 1)
        stage03_cycles.append(
            {
                "stage03_cycle_ref": stage03_ref,
                "cycle_id": cycle["cycle_id"],
                "burden_id": cycle["burden_id"],
                "origin": cycle["origin"],
                "parent_cycle_id": cycle["parent_cycle_id"],
                "generation_depth": cycle["generation_depth"],
                "route_event_id": cycle["event_ids"][0],
                "reentry_event_id": next(
                    (event_id for event_id, kind in zip(cycle["event_ids"], cycle["event_kinds"]) if kind == "stage03-reentry"),
                    None,
                ),
            }
        )
        stage04_cycles.append(
            {
                "stage04_cycle_ref": stage04_ref,
                "stage03_cycle_ref": stage03_ref,
                "cycle_id": cycle["cycle_id"],
                "burden_id": cycle["burden_id"],
                "execution_event_id": next(event_id for event_id, kind in zip(cycle["event_ids"], cycle["event_kinds"]) if kind == "execute"),
                "hold_disposition_event_id": next(
                    (event_id for event_id, kind in zip(cycle["event_ids"], cycle["event_kinds"]) if kind == "hold-disposition"),
                    None,
                ),
            }
        )
        stage05_cycles.append(
            {
                **copy.deepcopy(cycle),
                "stage03_cycle_ref": stage03_ref,
                "stage04_cycle_ref": stage04_ref,
                "land_event_id": next(event_id for event_id, kind in zip(cycle["event_ids"], cycle["event_kinds"]) if kind == "land"),
                "reread_id": stable_id(seed, "reread", index + 1),
                "terminal_state": "LANDED",
            }
        )
    obligations = [dict(row) for row in manifest["obligations"]]
    held_set = set(manifest["held_baseline_burden_ids"])
    acts = []
    dispositions = []
    for index, row in enumerate(obligations):
        if row["burden_id"] in held_set:
            dispositions.append(
                {
                    "obligation_id": row["obligation_id"],
                    "disposition": "HOLD_THEN_ACTIVATED",
                    "gate": "parent land and neutral activation evidence",
                    "next_action": "stage03 re-entry then execute",
                }
            )
        payload = f"performed evidence axis {index + 1} operation {row['operation']}"
        body = {
            **row,
            "before_state": canonical_sha256([row["obligation_id"], "before"]),
            "performed_evidence": canonical_sha256([row["obligation_id"], "performed"]),
            "delta": canonical_sha256([row["obligation_id"], "delta"]),
            "residual": canonical_sha256([row["obligation_id"], "residual"]),
            "land_contribution": canonical_sha256([row["obligation_id"], "land"]),
            "semantic_payload": payload,
            "shared_operation_decision_id": None,
            "shared_operation_authorization_sha256": None,
        }
        body["semantic_body_sha256"] = canonical_sha256(payload)
        body["normalized_evidence_sha256"] = canonical_sha256(normalized_evidence_body(payload))
        acts.append(body)
    lifecycle = [
        {
            "burden_id": row["burden_id"],
            "cycle_id": row["cycle_id"],
            "origin": row["origin"],
            "parent_id": next(
                (item["parent_id"] for item in manifest["generation"] if item["burden_id"] == row["burden_id"]),
                None,
            ),
            "generation_depth": row["generation_depth"],
            "activated_from_hold": row["activated_from_hold"],
            "terminal_state": "LANDED",
            "reread_id": row["reread_id"],
        }
        for row in stage05_cycles
    ]
    loopbreak = None
    if spec["dependency_shape"] == "noetic-cycle-loopbreak":
        loopbreak = {
            "operation_id": stable_id(seed, "loopbreak", 1),
            "interrupted_edge": manifest["noetic_edges_pre_loopbreak"][-1],
        }
    live_ids = [row["route_id"] for row in route_rows if row["disposition"] == "HOLD"]
    if spec["closure_policy"] == "partial-with-live-obligations" and not live_ids:
        live_ids.append(stable_id(seed, "policy-live", 1))
    closure_snapshots = [
        {
            "ordinal": 0,
            "remaining_live_ids": sorted([row["obligation_id"] for row in obligations] + live_ids),
            "closure": False,
        },
        {"ordinal": 1, "remaining_live_ids": sorted(live_ids), "closure": not live_ids},
    ]
    projection = {
        "obligation_ids": [row["obligation_id"] for row in obligations],
        "body_refs": [row["body_ref"] for row in acts],
        "burden_states": {row["burden_id"]: row["terminal_state"] for row in lifecycle},
        "reread_ids": [row["reread_id"] for row in lifecycle],
        "cycle_ids": [row["cycle_id"] for row in stage05_cycles],
        "noetic_edges_pre_loopbreak": manifest["noetic_edges_pre_loopbreak"],
        "noetic_edges_post_loopbreak": manifest["noetic_edges_post_loopbreak"],
        "closure_snapshots": closure_snapshots,
    }
    nar_rows = [
        {
            "obligation_id": row["obligation_id"],
            "burden_id": row["burden_id"],
            "body_ref": row["body_ref"],
            "resultant_sha256": row["delta"],
        }
        for row in acts
    ]
    public_segments = [
        {
            "ordinal": index,
            "obligation_id": row["obligation_id"],
            "body_ref": row["body_ref"],
            "semantic_payload": row["semantic_payload"],
        }
        for index, row in enumerate(acts, 1)
    ]
    return manifest, {
        "01": {"schema": "daee-topology-stage-01-v1", "observations": observations},
        "02": {
            "schema": "daee-topology-stage-02-v1",
            "candidates": candidates,
            "pressures": pressure_rows,
            "hyperedges": hyperedges,
            "pressure_partition_decisions": copy.deepcopy(
                manifest["pressure_partition_decisions"]
            ),
            "shared_operation_authorizations": copy.deepcopy(
                manifest["shared_operation_authorizations"]
            ),
            "baseline_burden_ids": manifest["baseline_burden_ids"],
            "preempted_candidates": [
                {"candidate_id": item, "status": "preempted", "basis": "superseded before instantiation"}
                for item in manifest["preempted_candidate_ids"]
            ],
            "noetic_edges_pre_loopbreak": manifest["noetic_edges_pre_loopbreak"],
            "loopbreak": loopbreak,
            "noetic_edges_post_loopbreak": manifest["noetic_edges_post_loopbreak"],
        },
        "03": {
            "schema": "daee-topology-stage-03-v1",
            "obligations": obligations,
            "routes": route_rows,
            "burden_cycles": stage03_cycles,
            "shared_operation_decisions": [],
        },
        "04": {
            "schema": "daee-topology-stage-04-v1",
            "acts": acts,
            "dispositions": dispositions,
            "burden_cycles": stage04_cycles,
        },
        "05": {
            "schema": "daee-topology-stage-05-v1",
            "lifecycle": lifecycle,
            "burden_cycles": stage05_cycles,
            "event_nodes": manifest["cycle_events"],
            "event_ids": manifest["event_ids"],
            "event_edges": copy.deepcopy(manifest["event_edges"]),
            "closure_snapshots": closure_snapshots,
        },
        "06": {"schema": "daee-topology-stage-06-v1", "nar_rows": nar_rows, "projection": projection},
        "07": {
            "schema": "daee-topology-stage-07-v1",
            "operations": copy.deepcopy(acts),
            "segments": public_segments,
            "projection": copy.deepcopy(projection),
            "T_lang": {"projection": "partial_coupling", "uptake_guaranteed": False},
        },
    }


def mutation_stage(operation: str) -> str:
    return {
        "delete-owner": "03",
        "delete-act": "04",
        "delete-reread": "05",
        "add-event-cycle": "05",
        "delete-nar": "06",
        "delete-projection-join": "07",
        "add-filler": "07",
    }[operation]


def apply_mutation(spec: dict[str, Any], manifest: dict[str, Any], stages: dict[str, dict[str, Any]]) -> str | None:
    mutation = spec.get("mutation")
    if not mutation:
        return None
    operation = mutation["operation"]
    target = mutation["target"]
    if operation == "delete-owner":
        stages["03"]["obligations"][0].pop("owner_id", None)
    elif operation == "delete-act":
        stages["04"]["acts"] = stages["04"]["acts"][1:]
    elif operation == "delete-reread":
        rows = stages["05"]["lifecycle"]
        if target.startswith("generated:"):
            index = int(target.split(":", 1)[1]) - 1
            target_id = manifest["generated_burden_ids"][index]
        else:
            target_id = target
        for row in rows:
            if row["burden_id"] == target_id:
                row.pop("reread_id", None)
                row["mutation_marker"] = target
                break
    elif operation == "add-event-cycle":
        ids = stages["05"]["event_ids"]
        if len(ids) == 1:
            stages["05"]["event_edges"].append([ids[0], ids[0]])
        else:
            stages["05"]["event_edges"].append([ids[-1], ids[0]])
        stages["05"]["mutation_marker"] = target
    elif operation == "delete-nar":
        stages["06"]["nar_rows"] = stages["06"]["nar_rows"][1:]
    elif operation == "delete-projection-join":
        stages["07"]["projection"]["reread_ids"] = stages["07"]["projection"]["reread_ids"][1:]
    elif operation == "add-filler":
        stages["07"]["irrelevant_filler"] = "neutral filler " * 50
    else:
        raise ValueError(f"unknown mutation operation {operation}")
    return mutation_stage(operation)
