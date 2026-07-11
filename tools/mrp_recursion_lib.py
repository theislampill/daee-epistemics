#!/usr/bin/env python3
"""Pure ordered reduction for DAEE MRP burden-cycle lifecycle records.

The reducer consumes only ``burden_cycles`` for semantic ordering.  A hash-bound
resource policy is validation context; it never supplies semantic state or a
recursion quota.  Retained Stage03/04/05 records stay external and are represented
only by their IDs and hashes in each cycle.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence


CHECKER_ID = "mrp-recursion-lifecycle"
STAGE = "05"
DOWNSTREAM_INVALIDATED = ("06", "07", "08")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")

CURRENT_PROFILE = "current-a07-v2"
HISTORICAL_PROFILE = "historical-raw-complete-v1"
EXIT_DISPOSITIONS = frozenset({"STOP", "COMPLETE", "RECURSE", "HOLD", "PARTIAL", "HANDOFF"})
CANDIDATE_DISPOSITIONS = frozenset(
    {"activate_held", "instantiate_generated", "defer_preempted", "non_load_bearing", "hold_partial"}
)
SEMANTIC_EVENT_KEYS = frozenset(
    {"exit_disposition", "candidates", "terminal_state", "no_new_resultant", "loopbreak", "resource_exhaustion"}
)


@dataclass(frozen=True, order=True)
class Finding:
    """Stable structural diagnostic emitted by the pure reducer."""

    subcode: str
    message: str
    cycle_id: str | None = None

    @property
    def failure_class(self) -> str:
        return "mrp"


@dataclass(frozen=True)
class ReductionState:
    """Lossless structural projection derived from ordered cycle events."""

    b_la: tuple[str, ...]
    b_mrp: tuple[str, ...]
    cycle_order: tuple[str, ...]
    cycle_exits: tuple[tuple[str, str], ...]
    event_dag_edges: tuple[tuple[str, str], ...]
    candidate_dispositions: tuple[tuple[str, str], ...]
    lifecycle_partitions: tuple[tuple[str, tuple[str, ...]], ...]
    live_candidate_ids: tuple[str, ...]
    live_obligation_ids: tuple[str, ...]
    terminal_disposition: str | None
    maximum_generation_depth: int
    reread_signature_history: tuple[tuple[str, str, str], ...]
    state_signature_sha256: str
    findings: tuple[Finding, ...]

    @property
    def valid(self) -> bool:
        return not self.findings


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _hash_ok(value: Any) -> bool:
    return isinstance(value, str) and HASH_RE.fullmatch(value) is not None


def _cycle_error(subcode: str, cycle_id: Any, message: str) -> Finding:
    label = str(cycle_id) if cycle_id is not None else None
    return Finding(subcode, message, label)


def _graph_edge_error(edges: Any) -> str | None:
    if not isinstance(edges, list):
        return "must be an array"
    for index, edge in enumerate(edges):
        if (
            not isinstance(edge, list)
            or len(edge) != 2
            or not all(_nonempty(node) for node in edge)
        ):
            return f"edge {index} must be a pair of non-empty node IDs"
    return None


def _graph_object_error(graph: Any) -> str | None:
    if not _is_mapping(graph):
        return "must be an object"
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not all(_nonempty(node) for node in nodes):
        return "nodes must be an array of non-empty node IDs"
    if len(set(str(node) for node in nodes)) != len(nodes):
        return "nodes must be unique"
    edge_error = _graph_edge_error(edges)
    if edge_error is not None:
        return edge_error
    edge_pairs = [tuple(str(node) for node in edge) for edge in edges]
    if len(set(edge_pairs)) != len(edge_pairs):
        return "edges must be unique"
    node_set = {str(node) for node in nodes}
    if any(left not in node_set or right not in node_set for left, right in edge_pairs):
        return "every edge endpoint must resolve in nodes"
    observed_hash = graph.get("graph_sha256")
    if not _hash_ok(observed_hash) or observed_hash != _canonical_object_hash(graph, "graph_sha256"):
        return "graph_sha256 does not match canonical graph"
    return None


def _graph_has_cycle(edges: Iterable[Sequence[Any]]) -> bool:
    graph: dict[str, set[str]] = {}
    nodes: set[str] = set()
    for edge in edges:
        left, right = str(edge[0]), str(edge[1])
        nodes.update((left, right))
        graph.setdefault(left, set()).add(right)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(child) for child in graph.get(node, set())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in sorted(nodes))


def _signature(parts: Any) -> str:
    encoded = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_object_hash(value: Mapping[str, Any], self_field: str) -> str:
    body = dict(value)
    body.pop(self_field, None)
    return _signature(body)


def _state_v2_hash(value: Mapping[str, Any], self_field: str) -> str:
    body = dict(value)
    body.pop(self_field, None)
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _unique_in_order(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _diagnostic_state(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    fields = ("operator", "target", "status", "delta_ref", "basis_refs")
    projected = [
        {
            field: sorted(row.get(field)) if field == "basis_refs" and isinstance(row.get(field), list) else row.get(field)
            for field in fields
            if field in row
        }
        for row in rows
        if _is_mapping(row)
    ]
    return sorted(projected, key=_signature)


def _graph_state(graph: Any) -> dict[str, Any] | None:
    if not _is_mapping(graph):
        return None
    edges = graph.get("edges")
    canonical_edges = []
    if isinstance(edges, list):
        for edge in edges:
            if _is_mapping(edge):
                canonical_edges.append({"from": edge.get("from"), "to": edge.get("to")})
            elif isinstance(edge, (list, tuple)) and len(edge) == 2:
                canonical_edges.append({"from": edge[0], "to": edge[1]})
    return {
        "nodes": sorted(graph.get("nodes", [])) if isinstance(graph.get("nodes"), list) else graph.get("nodes"),
        "edges": sorted(canonical_edges, key=_signature),
    }


def _operation_semantic_state(value: Any) -> dict[str, Any]:
    if not _is_mapping(value):
        return {}
    capsules = value.get("operation_capsules")
    if not isinstance(capsules, list):
        capsules = []
    projected_capsules = []
    for capsule in capsules:
        if not _is_mapping(capsule):
            continue
        before = capsule.get("before_state")
        after = capsule.get("after_state")
        delta = capsule.get("delta")
        contribution = capsule.get("land_contribution")
        projected_capsules.append({
            "owner_id": capsule.get("owner_id"),
            "operation": capsule.get("operation"),
            "register_axis": capsule.get("register_axis"),
            "pressure_ids": sorted(capsule.get("pressure_ids", [])) if isinstance(capsule.get("pressure_ids"), list) else capsule.get("pressure_ids"),
            "before_state": {key: item for key, item in before.items() if key != "state_id"} if _is_mapping(before) else before,
            "performed_operation": capsule.get("performed_operation"),
            "after_state": {key: item for key, item in after.items() if key != "state_id"} if _is_mapping(after) else after,
            "delta": {key: item for key, item in delta.items() if key != "delta_id"} if _is_mapping(delta) else delta,
            "residual": capsule.get("residual"),
            "land_contribution": {key: item for key, item in contribution.items() if key != "delta_ref"} if _is_mapping(contribution) else contribution,
        })
    local_delta = value.get("local_delta")
    projected_local_delta = None
    if _is_mapping(local_delta):
        projected_local_delta = {
            key: item for key, item in local_delta.items()
            if key not in {"delta_id", "source_operation_capsule_ids"}
        }
    return {
        "performed": value.get("performed"),
        "local_delta": projected_local_delta,
        "operation_capsules": sorted(projected_capsules, key=_signature),
    }


def _cycle_semantic_state(value: Any) -> dict[str, Any]:
    if not _is_mapping(value):
        return {}
    operation = value.get("operation") if _is_mapping(value.get("operation")) else value
    land = value.get("land")
    post_land = value.get("post_land_delta")
    operation_state = _operation_semantic_state(operation)
    post_land_state = {
        "basis_refs": sorted(post_land.get("basis_refs", [])) if isinstance(post_land.get("basis_refs"), list) else post_land.get("basis_refs")
    } if _is_mapping(post_land) else post_land
    return {
        "operation": operation_state,
        "land": {"status": land.get("status")} if _is_mapping(land) else land,
        "post_land_delta": post_land_state,
    }


def _loopbreak_state(loopbreak: Any) -> dict[str, Any] | None:
    if not _is_mapping(loopbreak):
        return None
    post_reread = loopbreak.get("post_break_reread")
    post_graph = loopbreak.get("post_break_graph")
    return {
        "observed_loop": loopbreak.get("observed_loop"),
        "owner_ground_sha256": (
            loopbreak.get("owner_ground_ref", {}).get("sha256")
            if _is_mapping(loopbreak.get("owner_ground_ref"))
            else None
        ),
        "performed_operation_sha256": (
            loopbreak.get("performed_operation_ref", {}).get("sha256")
            if _is_mapping(loopbreak.get("performed_operation_ref"))
            else None
        ),
        "local_delta_sha256": (
            loopbreak.get("local_delta_ref", {}).get("sha256")
            if _is_mapping(loopbreak.get("local_delta_ref"))
            else None
        ),
        "post_break_graph": _graph_state(post_graph),
        "post_break_diagnostics": (
            _diagnostic_state(post_reread.get("field_diagnostics"))
            if _is_mapping(post_reread)
            else []
        ),
    }


def _reread_state_signature(
    *,
    b_la: Sequence[str],
    b_mrp: Sequence[str],
    burden_terminal_states: Mapping[str, str],
    candidate_history: Mapping[str, tuple[str | None, str]],
    live_candidates: set[str],
    live_obligations: set[str],
    event: Mapping[str, Any],
    cycle_semantics: Mapping[str, Any] | None = None,
) -> str:
    """Canonical topic-neutral governed state at one completed reread."""

    no_new = event.get("no_new_resultant")
    remaining_obligations = set(live_obligations)
    if _is_mapping(no_new) and isinstance(no_new.get("live_obligation_ids"), list):
        remaining_obligations.update(str(value) for value in no_new["live_obligation_ids"])
    kappa = event.get("kappa_residual")
    if kappa is None and _is_mapping(no_new):
        kappa = no_new.get("kappa_residual")
    if kappa is None:
        kappa = [
            row
            for row in _diagnostic_state(event.get("field_diagnostics"))
            if str(row.get("operator")) in {"kappa", "κ"}
        ]
    parts = {
        "B_LA": list(b_la),
        "B_MRP_prefix": list(b_mrp),
        "burden_terminal_state": sorted(burden_terminal_states.items()),
        "live_candidate_identities_dispositions": sorted(
            (candidate_id, candidate_history[candidate_id][1])
            for candidate_id in live_candidates
            if candidate_id in candidate_history
        ),
        "remaining_obligations": sorted(remaining_obligations),
        "field_diagnostics": _diagnostic_state(event.get("field_diagnostics")),
        "noetic_dependency_graph": _graph_state(event.get("noetic_dependency_graph")),
        "loopbreak": _loopbreak_state(event.get("loopbreak")),
        "cycle_semantics": _cycle_semantic_state(cycle_semantics),
        "route_result": event.get("exit_disposition"),
        "residual_kappa_scope": kappa,
    }
    return _signature(parts)


def _empty_state(finding: Finding) -> ReductionState:
    names = ("candidate", "held", "preempted", "active", "landed", "generated", "partial", "recurse", "closure_candidate", "complete")
    return ReductionState((), (), (), (), (), (), tuple((name, ()) for name in names), (), (), None, 0, (), _signature({}), (finding,))


def _finish(
    *,
    b_la: list[str],
    b_mrp: list[str],
    cycle_order: list[str],
    cycle_exits: list[tuple[str, str]],
    event_edges: list[tuple[str, str]],
    candidate_dispositions: list[tuple[str, str]],
    lifecycle_partitions: dict[str, set[str]],
    live_candidates: set[str],
    live_obligations: set[str],
    terminal: str | None,
    maximum_depth: int,
    reread_signatures: list[tuple[str, str, str]],
    finding: Finding | None = None,
) -> ReductionState:
    names = ("candidate", "held", "preempted", "active", "landed", "generated", "partial", "recurse", "closure_candidate", "complete")
    frozen_partitions = tuple((name, tuple(sorted(lifecycle_partitions.get(name, set())))) for name in names)
    ordered_event_edges = list(dict.fromkeys(event_edges))
    signature_parts = {
        "B_LA": b_la,
        "B_MRP": b_mrp,
        "cycle_order": cycle_order,
        "cycle_exits": cycle_exits,
        "event_dag_edges": ordered_event_edges,
        "candidate_dispositions": candidate_dispositions,
        "lifecycle_partitions": frozen_partitions,
        "live_candidate_ids": sorted(live_candidates),
        "live_obligation_ids": sorted(live_obligations),
        "terminal_disposition": terminal,
        "maximum_generation_depth": maximum_depth,
        "reread_signature_history": reread_signatures,
    }
    return ReductionState(
        tuple(b_la),
        tuple(b_mrp),
        tuple(cycle_order),
        tuple(cycle_exits),
        tuple(ordered_event_edges),
        tuple(candidate_dispositions),
        frozen_partitions,
        tuple(sorted(live_candidates)),
        tuple(sorted(live_obligations)),
        terminal,
        maximum_depth,
        tuple(reread_signatures),
        _signature(signature_parts),
        (finding,) if finding else (),
    )


def reduce_burden_cycles(
    burden_cycles: Any,
    *,
    resource_policy: Any = None,
    validation_profile: str | None = None,
    predecessor_trace_id: str | None = None,
) -> ReductionState:
    """Validate and reduce one ordered cycle array without external effects."""

    if not isinstance(burden_cycles, list) or not burden_cycles:
        return _empty_state(Finding("cycle_array_required", "burden_cycles must be a non-empty ordered array"))
    if not _is_mapping(resource_policy):
        return _empty_state(Finding("resource_policy_invalid", "resource_policy must be hash-bound validation context"))
    if resource_policy.get("semantic_depth_cap") is not None:
        return _empty_state(
            Finding(
                "semantic_depth_cap",
                "semantic_depth_cap must be null; resource policy cannot impose a semantic depth limit",
            )
        )
    if not _nonempty(resource_policy.get("policy_id")) or not _hash_ok(resource_policy.get("policy_sha256")):
        return _empty_state(Finding("resource_policy_invalid", "resource policy requires policy_id and policy_sha256"))
    expected_policy_hash = _canonical_object_hash(resource_policy, "policy_sha256")
    if resource_policy.get("policy_sha256") != expected_policy_hash:
        return _empty_state(
            Finding(
                "resource_policy_hash_mismatch",
                f"resource_policy_hash_mismatch: resource policy policy_sha256 does not match canonical contents; expected {expected_policy_hash}",
            )
        )
    if resource_policy.get("on_exhaustion") not in {"PARTIAL", "HANDOFF"}:
        return _empty_state(Finding("resource_policy_invalid", "on_exhaustion must be PARTIAL or HANDOFF"))

    cycles: list[Mapping[str, Any]] = []
    for position, raw_cycle in enumerate(burden_cycles):
        if not _is_mapping(raw_cycle):
            return _empty_state(Finding("cycle_shape", f"burden_cycles[{position}] must be an object"))
        cycles.append(raw_cycle)

    cycle_ids = [str(cycle.get("cycle_id", "")) for cycle in cycles]
    burden_ids = [str(cycle.get("burden_id", "")) for cycle in cycles]
    if any(not value for value in cycle_ids) or len(set(cycle_ids)) != len(cycle_ids):
        return _empty_state(Finding("cycle_identity", "cycle_id values must be present and unique"))
    if any(not value for value in burden_ids):
        return _empty_state(Finding("burden_identity", "burden_id values must be present"))

    index_by_cycle = {cycle_id: index for index, cycle_id in enumerate(cycle_ids)}
    cycle_by_id = {cycle_id: cycles[index] for index, cycle_id in enumerate(cycle_ids)}
    cycles_by_burden: dict[str, list[Mapping[str, Any]]] = {}
    for index, burden_id in enumerate(burden_ids):
        cycles_by_burden.setdefault(burden_id, []).append(cycles[index])
    b_la = _unique_in_order(
        burden_ids[index] for index, cycle in enumerate(cycles) if cycle.get("origin") == "B_LA"
    )

    state_args: dict[str, Any] = {
        "b_la": b_la,
        "b_mrp": [],
        "cycle_order": [],
        "cycle_exits": [],
        "event_edges": [],
        "candidate_dispositions": [],
        "lifecycle_partitions": {
            name: set()
            for name in ("candidate", "held", "preempted", "active", "landed", "generated", "partial", "recurse", "closure_candidate", "complete")
        },
        "live_candidates": set(),
        "live_obligations": set(),
        "terminal": None,
        "maximum_depth": 0,
        "reread_signatures": [],
    }

    def stop(finding: Finding) -> ReductionState:
        return _finish(**state_args, finding=finding)

    event_by_cycle: dict[str, Mapping[str, Any]] = {}
    governed_event_indices: set[int] = set()
    for cycle in cycles:
        cycle_id = str(cycle.get("cycle_id"))
        state_args["cycle_order"].append(cycle_id)
        reread = cycle.get("reread")
        raw_events = reread.get("raw_events") if _is_mapping(reread) else None
        if validation_profile == CURRENT_PROFILE:
            if isinstance(raw_events, list) and any(
                _is_mapping(candidate_exit) and candidate_exit.get("exit_disposition") == "COMPLETE"
                for candidate_exit in raw_events
            ):
                return stop(
                    _cycle_error(
                        "raw_complete_forbidden",
                        cycle_id,
                        f"raw_complete_forbidden: current profile {CURRENT_PROFILE} cycle {cycle_id} cannot use raw COMPLETE",
                    )
                )
            raw_exit = reread.get("raw_exit") if _is_mapping(reread) else None
            if not _is_mapping(raw_exit) or raw_events is not None:
                return stop(
                    _cycle_error(
                        "raw_exit_cardinality",
                        cycle_id,
                        f"cycle {cycle_id} current profile requires exactly one raw_exit object and no raw_events array",
                    )
                )
            if raw_exit.get("exit_disposition") == "COMPLETE":
                return stop(
                    _cycle_error(
                        "raw_complete_forbidden",
                        cycle_id,
                        f"raw_complete_forbidden: current profile {CURRENT_PROFILE} cycle {cycle_id} cannot use raw COMPLETE",
                    )
                )
            event = raw_exit
        else:
            if not isinstance(raw_events, list) or len(raw_events) != 1:
                return stop(
                    _cycle_error(
                        "multiple_cycle_exits",
                        cycle_id,
                        f"cycle {cycle_id} must preserve exactly one governed raw exit; got {0 if not isinstance(raw_events, list) else len(raw_events)}",
                    )
                )
            event = raw_events[0]
        if not _is_mapping(event):
            return stop(_cycle_error("cycle_exit_shape", cycle_id, f"cycle {cycle_id} raw exit must be an object"))
        if validation_profile == CURRENT_PROFILE:
            required_raw_fields = {
                "event_id",
                "event_index",
                "raw_exit_sha256",
                "exit_disposition",
                "candidate_events",
                "field_diagnostics",
                "noetic_dependency_graph",
                "no_new_resultant",
                "loopbreak",
                "resource_exhaustion",
            }
            missing_raw_fields = sorted(required_raw_fields - set(event))
            if missing_raw_fields:
                return stop(
                    _cycle_error(
                        "raw_exit_shape",
                        cycle_id,
                        f"raw_exit_shape: cycle {cycle_id} raw exit lacks {missing_raw_fields[0]}",
                    )
                )
            if not _nonempty(event.get("event_id")):
                return stop(_cycle_error("raw_exit_shape", cycle_id, f"raw_exit_shape: cycle {cycle_id} event_id must be non-empty"))
            if not isinstance(event.get("candidate_events"), list):
                return stop(_cycle_error("raw_exit_shape", cycle_id, f"raw_exit_shape: cycle {cycle_id} candidate_events must be an array"))
            if not isinstance(event.get("field_diagnostics"), list):
                return stop(_cycle_error("raw_exit_shape", cycle_id, f"raw_exit_shape: cycle {cycle_id} field_diagnostics must be an array"))
            observed_raw_hash = event.get("raw_exit_sha256")
            expected_raw_hash = _canonical_object_hash(event, "raw_exit_sha256")
            if not _hash_ok(observed_raw_hash) or observed_raw_hash != expected_raw_hash:
                return stop(
                    _cycle_error(
                        "raw_exit_hash_mismatch",
                        cycle_id,
                        f"raw_exit_hash_mismatch: cycle {cycle_id} raw_exit_sha256 does not match canonical raw exit",
                    )
                )
        event_by_cycle[cycle_id] = event

        normalized = reread.get("normalized_event") if _is_mapping(reread) else None
        if normalized is not None:
            if not _is_mapping(normalized):
                return stop(_cycle_error("semantic_hydration", cycle_id, f"cycle {cycle_id} normalized_event is not structural"))
            raw_exit = event.get("exit_disposition")
            normalized_exit = normalized.get("exit_disposition")
            if normalized_exit is not None and normalized_exit != raw_exit:
                return stop(
                    _cycle_error(
                        "synthetic_recursion",
                        cycle_id,
                        f"cycle {cycle_id} normalized event rewrites raw {raw_exit} as {normalized_exit}",
                    )
                )
            hydrated = sorted(key for key in SEMANTIC_EVENT_KEYS if key in normalized and key not in event)
            if hydrated:
                hydrated_values = {key: normalized.get(key) for key in hydrated}
                return stop(
                    _cycle_error(
                        "semantic_hydration",
                        cycle_id,
                        f"cycle {cycle_id} normalized event hydrates absent semantic fields {hydrated_values}",
                    )
                )
            candidate_key = "candidate_events" if validation_profile == CURRENT_PROFILE else "candidates"
            if candidate_key in normalized and normalized.get(candidate_key) != event.get(candidate_key):
                return stop(_cycle_error("semantic_hydration", cycle_id, f"cycle {cycle_id} normalized candidates differ from raw event"))

        for key, expected_target in (("route", cycle.get("burden_id")),):
            record = cycle.get(key)
            if not _is_mapping(record) or not _nonempty(record.get("record_id")) or not _hash_ok(record.get("sha256")):
                return stop(_cycle_error("retained_record_custody", cycle_id, f"cycle {cycle_id} lacks hash-bound Stage03 route custody"))
            if record.get("target_burden_id") != expected_target:
                return stop(_cycle_error("retained_record_custody", cycle_id, f"cycle {cycle_id} route target does not match {expected_target}"))
        operation = cycle.get("operation")
        if (
            not _is_mapping(operation)
            or not _nonempty(operation.get("record_id"))
            or not _hash_ok(operation.get("sha256"))
            or operation.get("performed") is not True
            or not _is_mapping(operation.get("local_delta"))
            or not operation.get("local_delta")
        ):
            return stop(_cycle_error("operation_not_performed", cycle_id, f"cycle {cycle_id} lacks performed Stage04 operation/local delta custody"))
        land = cycle.get("land")
        if not _is_mapping(land) or land.get("status") != "landed" or not isinstance(land.get("event_index"), int):
            return stop(_cycle_error("land_missing", cycle_id, f"cycle {cycle_id} lacks an observed Land event"))
        if not _is_mapping(reread) or not _nonempty(reread.get("record_id")) or not _hash_ok(reread.get("sha256")):
            return stop(_cycle_error("retained_record_custody", cycle_id, f"cycle {cycle_id} lacks hash-bound Stage05 reread custody"))
        if not isinstance(event.get("event_index"), int) or event.get("event_index") <= land.get("event_index"):
            generated = any(
                _is_mapping(candidate) and candidate.get("disposition") == "instantiate_generated"
                for candidate in event.get("candidate_events" if validation_profile == CURRENT_PROFILE else "candidates", [])
                if isinstance(event.get("candidate_events" if validation_profile == CURRENT_PROFILE else "candidates"), list)
            )
            subcode = "generated_pre_land" if generated else "reread_pre_land"
            return stop(
                _cycle_error(
                    subcode,
                    cycle_id,
                    f"cycle {cycle_id} reread event_index must be after Land event_index",
                )
            )
        if validation_profile == CURRENT_PROFILE:
            land_index = int(land.get("event_index"))
            raw_exit_index = int(event.get("event_index"))
            if land_index in governed_event_indices or raw_exit_index in governed_event_indices:
                return stop(_cycle_error("event_index_replayed", cycle_id, f"cycle {cycle_id} reuses a governed event_index"))
            governed_event_indices.update((land_index, raw_exit_index))
        state_args["lifecycle_partitions"]["active"].add(str(cycle.get("burden_id")))
        state_args["lifecycle_partitions"]["landed"].add(str(cycle.get("burden_id")))

    generated_by_target: dict[str, tuple[str, str | None]] = {}
    preempted: dict[str, str | None] = {}
    candidate_history: dict[str, tuple[str | None, str]] = {}
    candidate_event_ids: set[str] = set()
    scheduled_cycle_custody: dict[str, tuple[str, str, str | None, int | None]] = {}
    last_cycle_for_burden: dict[str, Mapping[str, Any]] = {}
    burden_terminal_states: dict[str, str] = {}
    signature_seen: dict[str, tuple[str, str]] = {}
    b_mrp: list[str] = state_args["b_mrp"]
    terminal_cycle: tuple[str, str] | None = None

    for cycle in cycles:
        cycle_id = str(cycle.get("cycle_id"))
        burden_id = str(cycle.get("burden_id"))
        prior_cycle = last_cycle_for_burden.get(burden_id)
        if prior_cycle is not None:
            custody = scheduled_cycle_custody.get(cycle_id)
            if custody is None or custody[1] != burden_id:
                return stop(
                    _cycle_error(
                        "same_burden_unscheduled",
                        cycle_id,
                        f"same_burden_unscheduled: later cycle {cycle_id} for {burden_id} lacks a prior candidate scheduling event",
                    )
                )
            prior_exit = event_by_cycle[str(prior_cycle.get("cycle_id"))]
            if cycle.get("land", {}).get("event_index", -1) <= prior_exit.get("event_index", -1):
                return stop(
                    _cycle_error(
                        "same_burden_event_order",
                        cycle_id,
                        f"same_burden_event_order: later cycle {cycle_id} events do not follow prior cycle {prior_cycle.get('cycle_id')}",
                    )
                )
            custody_keys = ("route", "operation", "reread")
            replayed = all(
                (
                    cycle.get(key, {}).get("record_id"),
                    cycle.get(key, {}).get("sha256"),
                )
                == (
                    prior_cycle.get(key, {}).get("record_id"),
                    prior_cycle.get(key, {}).get("sha256"),
                )
                for key in custody_keys
            )
            if replayed:
                return stop(
                    _cycle_error(
                        "same_burden_replay",
                        cycle_id,
                        f"same_burden_replay: later cycle {cycle_id} replays route/operation/reread custody for {burden_id}",
                    )
                )
        if terminal_cycle is not None:
            prior_cycle_id, prior_exit = terminal_cycle
            return stop(
                _cycle_error(
                    "cycle_after_terminal",
                    cycle_id,
                    f"cycle_after_terminal: cycle {cycle_id} follows terminal {prior_exit} cycle {prior_cycle_id}",
                )
            )
        event = event_by_cycle[cycle_id]
        exit_disposition = event.get("exit_disposition")
        if exit_disposition not in EXIT_DISPOSITIONS:
            return stop(_cycle_error("exit_disposition", cycle_id, f"cycle {cycle_id} has unknown exit disposition {exit_disposition!r}"))
        state_args["cycle_exits"].append((cycle_id, str(exit_disposition)))
        state_args["terminal"] = str(exit_disposition)
        candidates = event.get("candidate_events" if validation_profile == CURRENT_PROFILE else "candidates")
        if not isinstance(candidates, list):
            return stop(_cycle_error("candidate_accounting", cycle_id, f"cycle {cycle_id} candidates must be an ordered array"))
        scheduled = 0
        scheduled_cycle_ids: list[str] = []
        for candidate in candidates:
            if not _is_mapping(candidate):
                return stop(_cycle_error("candidate_accounting", cycle_id, f"cycle {cycle_id} contains a non-object candidate"))
            candidate_id = candidate.get("candidate_id")
            kind = candidate.get("kind")
            disposition = candidate.get("disposition")
            target = candidate.get("target_burden_id")
            next_cycle_id = candidate.get("next_cycle_id")
            if not _nonempty(candidate_id) or disposition not in CANDIDATE_DISPOSITIONS:
                return stop(_cycle_error("candidate_accounting", cycle_id, f"cycle {cycle_id} candidate lacks governed identity/disposition"))
            candidate_id = str(candidate_id)
            if validation_profile == CURRENT_PROFILE:
                candidate_event_id = candidate.get("candidate_event_id")
                previous_event_id = candidate.get("previous_candidate_event_id")
                candidate_index = candidate.get("event_index")
                basis_refs = candidate.get("basis_refs")
                kind = candidate.get("kind")
                if not _nonempty(candidate_event_id):
                    return stop(_cycle_error("candidate_accounting", cycle_id, f"cycle {cycle_id} candidate {candidate_id} lacks candidate_event_id"))
                candidate_event_id = str(candidate_event_id)
                if candidate_event_id in candidate_event_ids:
                    return stop(
                        _cycle_error(
                            "candidate_event_replayed",
                            cycle_id,
                            f"candidate_event_replayed: cycle {cycle_id} reuses candidate event {candidate_event_id}",
                        )
                    )
                if (
                    not isinstance(candidate_index, int)
                    or candidate_index <= cycle.get("land", {}).get("event_index")
                    or candidate_index >= event.get("event_index")
                ):
                    return stop(
                        _cycle_error(
                            "post_land_order",
                            cycle_id,
                            f"post_land_order: cycle {cycle_id} candidate_event {candidate_event_id} must be after Land and before raw exit",
                        )
                    )
                if candidate_index in governed_event_indices:
                    return stop(_cycle_error("event_index_replayed", cycle_id, f"candidate event {candidate_event_id} reuses event_index {candidate_index}"))
                if not isinstance(basis_refs, list) or not basis_refs or not all(_nonempty(ref) for ref in basis_refs):
                    return stop(_cycle_error("candidate_accounting", cycle_id, f"candidate {candidate_id} requires non-empty basis_refs"))
                if len(set(str(ref) for ref in basis_refs)) != len(basis_refs):
                    return stop(_cycle_error("candidate_accounting", cycle_id, f"candidate {candidate_id} basis_refs must be unique"))
                if not _nonempty(kind):
                    return stop(_cycle_error("candidate_accounting", cycle_id, f"candidate {candidate_id} kind must be a non-empty open-world identifier"))
                prior_event = candidate_history.get(candidate_id)
                if prior_event is None:
                    if previous_event_id is not None:
                        return stop(
                            _cycle_error(
                                "candidate_predecessor_mismatch",
                                cycle_id,
                                f"candidate_predecessor_mismatch: first event for {candidate_id} cannot name {previous_event_id}",
                            )
                        )
                else:
                    expected_previous, prior_disposition = prior_event
                    if previous_event_id != expected_previous:
                        return stop(
                            _cycle_error(
                                "candidate_predecessor_mismatch",
                                cycle_id,
                                f"candidate_predecessor_mismatch: candidate {candidate_id} names {previous_event_id}; expected {expected_previous} in cycle {cycle_id}",
                            )
                        )
                    if prior_disposition in {"activate_held", "instantiate_generated", "non_load_bearing"}:
                        return stop(
                            _cycle_error(
                                "candidate_transition_invalid",
                                cycle_id,
                                f"candidate_transition_invalid: candidate {candidate_id} cannot transition from terminal {prior_disposition} to {disposition}",
                            )
                        )
                    if prior_disposition == "hold_partial" and not _nonempty(predecessor_trace_id):
                        return stop(
                            _cycle_error(
                                "candidate_transition_invalid",
                                cycle_id,
                                f"candidate_transition_invalid: held candidate {candidate_id} may transition only in a resumed trace",
                            )
                        )
                known_kinds = {"held_activation", "generated_instantiation", "escape_route", "unclassified"}
                if str(kind) not in known_kinds and disposition != "hold_partial":
                    return stop(
                        _cycle_error(
                            "unknown_candidate_not_held",
                            cycle_id,
                            f"unknown_candidate_not_held: candidate {candidate_id} kind {kind} must remain hold_partial",
                        )
                    )
                candidate_event_ids.add(candidate_event_id)
                governed_event_indices.add(candidate_index)
                candidate_history[candidate_id] = (candidate_event_id, str(disposition))
            state_args["candidate_dispositions"].append((candidate_id, str(disposition)))
            state_args["lifecycle_partitions"]["candidate"].add(candidate_id)
            if validation_profile != CURRENT_PROFILE:
                prior = candidate_history.get(candidate_id)
                prior_disposition = prior[1] if prior is not None else None
                if prior_disposition is not None and (prior_disposition, disposition) != ("defer_preempted", "activate_held"):
                    return stop(
                        _cycle_error(
                            "candidate_transition_invalid",
                            cycle_id,
                            f"candidate_transition_invalid: candidate {candidate_id} cannot transition from {prior_disposition} to {disposition}",
                        )
                    )
                candidate_history[candidate_id] = (None, str(disposition))

            allowed = {
                "held_activation": {"activate_held"},
                "generated_instantiation": {"instantiate_generated"},
                "escape_route": {"defer_preempted", "non_load_bearing", "hold_partial"},
                "unclassified": {"hold_partial"},
            }.get(str(kind), {"hold_partial"} if validation_profile == CURRENT_PROFILE else set())
            if disposition not in allowed:
                return stop(
                    _cycle_error(
                        "candidate_conflation",
                        cycle_id,
                        f"candidate {candidate_id} kind {kind} cannot use disposition {disposition}",
                    )
                )

            if disposition == "non_load_bearing":
                has_basis = (
                    isinstance(candidate.get("basis_refs"), list) and bool(candidate.get("basis_refs"))
                    if validation_profile == CURRENT_PROFILE
                    else _nonempty(candidate.get("basis"))
                )
                if not has_basis or target is not None or next_cycle_id is not None:
                    return stop(
                        _cycle_error(
                            "candidate_conflation",
                            cycle_id,
                            f"non_load_bearing candidate {candidate_id} cannot instantiate or schedule {next_cycle_id}",
                        )
                    )
                continue

            if disposition == "defer_preempted":
                has_basis = (
                    isinstance(candidate.get("basis_refs"), list) and bool(candidate.get("basis_refs"))
                    if validation_profile == CURRENT_PROFILE
                    else _nonempty(candidate.get("basis"))
                )
                if not has_basis or not _nonempty(target) or next_cycle_id is not None:
                    return stop(_cycle_error("candidate_accounting", cycle_id, f"deferred candidate {candidate_id} lacks durable target/basis"))
                preempted[candidate_id] = str(target)
                state_args["live_candidates"].add(candidate_id)
                state_args["lifecycle_partitions"]["preempted"].add(candidate_id)
                continue

            if disposition == "hold_partial":
                has_basis = (
                    isinstance(candidate.get("basis_refs"), list) and bool(candidate.get("basis_refs"))
                    if validation_profile == CURRENT_PROFILE
                    else _nonempty(candidate.get("basis"))
                )
                if not has_basis:
                    return stop(_cycle_error("candidate_accounting", cycle_id, f"held candidate {candidate_id} lacks basis"))
                state_args["live_candidates"].add(candidate_id)
                state_args["lifecycle_partitions"]["held"].add(candidate_id)
                continue

            if not _nonempty(target):
                return stop(_cycle_error("candidate_accounting", cycle_id, f"candidate {candidate_id} lacks target burden"))
            target = str(target)
            if next_cycle_id is not None and str(next_cycle_id) not in cycle_by_id:
                subcode = "generated_not_executed" if disposition == "instantiate_generated" else "scheduled_cycle_omitted"
                return stop(
                    _cycle_error(
                        subcode,
                        cycle_id,
                        f"candidate {candidate_id} target {target} names missing later cycle {next_cycle_id}",
                    )
                )
            if candidate_id in preempted:
                if preempted[candidate_id] != target:
                    return stop(_cycle_error("candidate_conflation", cycle_id, f"candidate {candidate_id} activation changes its retained target"))
                del preempted[candidate_id]
                state_args["live_candidates"].discard(candidate_id)

            if disposition == "activate_held":
                if target not in b_la:
                    return stop(
                        _cycle_error(
                            "candidate_conflation",
                            cycle_id,
                            f"held activation candidate {candidate_id} targets non-baseline burden {target}",
                        )
                    )
            elif disposition == "instantiate_generated":
                if target in b_la:
                    return stop(
                        _cycle_error(
                            "generated_track_violation",
                            cycle_id,
                            f"generated target {target} overlaps immutable B_LA baseline track",
                        )
                    )
                if target in generated_by_target:
                    return stop(_cycle_error("generated_duplicate", cycle_id, f"generated target {target} has more than one instantiation event"))
                generated_by_target[target] = (cycle_id, str(next_cycle_id) if next_cycle_id is not None else None)
                b_mrp.append(target)
                state_args["lifecycle_partitions"]["generated"].add(target)

            if next_cycle_id is not None:
                next_cycle_id = str(next_cycle_id)
                scheduled += 1
                scheduled_cycle_ids.append(next_cycle_id)
                candidate_event_identity = (
                    str(candidate.get("candidate_event_id"))
                    if _nonempty(candidate.get("candidate_event_id"))
                    else None
                )
                candidate_event_index = candidate.get("event_index") if isinstance(candidate.get("event_index"), int) else None
                if next_cycle_id in scheduled_cycle_custody:
                    return stop(
                        _cycle_error(
                            "scheduled_cycle_replayed",
                            cycle_id,
                            f"scheduled cycle {next_cycle_id} has more than one predecessor custody event",
                        )
                    )
                scheduled_cycle_custody[next_cycle_id] = (
                    cycle_id,
                    target,
                    candidate_event_identity,
                    candidate_event_index,
                )
                state_args["event_edges"].append((cycle_id, next_cycle_id))
                if next_cycle_id not in cycle_by_id:
                    subcode = "generated_not_executed" if disposition == "instantiate_generated" else "scheduled_cycle_omitted"
                    return stop(
                        _cycle_error(
                            subcode,
                            cycle_id,
                            f"candidate {candidate_id} target {target} names missing later cycle {next_cycle_id}",
                        )
                    )
                if index_by_cycle[next_cycle_id] <= index_by_cycle[cycle_id]:
                    return stop(_cycle_error("event_dag_cycle", cycle_id, f"custody edge {cycle_id}->{next_cycle_id} is not forward ordered"))
                if cycle_by_id[next_cycle_id].get("burden_id") != target:
                    return stop(_cycle_error("scheduled_target_mismatch", cycle_id, f"cycle {next_cycle_id} does not execute target {target}"))
            elif exit_disposition not in {"PARTIAL", "HANDOFF", "HOLD"}:
                subcode = "generated_not_executed" if disposition == "instantiate_generated" else "scheduled_cycle_omitted"
                return stop(
                    _cycle_error(
                        subcode,
                        cycle_id,
                        f"candidate {candidate_id} target {target} has no later cycle before terminal {exit_disposition}",
                    )
                )

        if exit_disposition == "RECURSE" and scheduled != 1:
            return stop(
                _cycle_error(
                    "recurse_schedule_cardinality" if scheduled > 1 else "synthetic_recursion",
                    cycle_id,
                    f"recurse_schedule_cardinality: cycle {cycle_id} RECURSE schedules {scheduled} next cycles; expected exactly 1",
                )
            )
        if exit_disposition in {"STOP", "COMPLETE", "HOLD", "PARTIAL", "HANDOFF"} and scheduled_cycle_ids:
            return stop(
                _cycle_error(
                    "terminal_schedules_cycle",
                    cycle_id,
                    f"terminal_schedules_cycle: terminal {exit_disposition} cycle {cycle_id} schedules {scheduled_cycle_ids[0]}",
                )
            )

        resource = event.get("resource_exhaustion")
        if resource is not None:
            if exit_disposition not in {"PARTIAL", "HANDOFF"}:
                return stop(
                    _cycle_error(
                        "resource_exhaustion_stop",
                        cycle_id,
                        f"resource exhaustion requires PARTIAL or HANDOFF, never {exit_disposition}",
                    )
                )
            if not _is_mapping(resource) or resource.get("observed") is not True:
                return stop(_cycle_error("resource_exhaustion_custody", cycle_id, f"cycle {cycle_id} lacks observed exhaustion"))
            if resource.get("policy_sha256") != resource_policy.get("policy_sha256"):
                return stop(_cycle_error("resource_exhaustion_custody", cycle_id, f"cycle {cycle_id} exhaustion policy hash is unbound"))
            continuation = resource.get("continuation")
            if (
                not _is_mapping(continuation)
                or not _nonempty(continuation.get("next_burden_id"))
                or not _nonempty(continuation.get("next_action"))
                or not _hash_ok(continuation.get("capsule_sha256"))
            ):
                return stop(_cycle_error("resource_exhaustion_custody", cycle_id, f"cycle {cycle_id} lacks resumable continuation"))
            obligations = resource.get("live_obligation_ids")
            if not isinstance(obligations, list) or not obligations or not all(_nonempty(item) for item in obligations):
                return stop(_cycle_error("resource_exhaustion_custody", cycle_id, f"cycle {cycle_id} exhaustion must preserve live obligations"))
            state_args["live_obligations"].update(str(item) for item in obligations)
        elif exit_disposition in {"PARTIAL", "HANDOFF"}:
            return stop(_cycle_error("resource_exhaustion_custody", cycle_id, f"cycle {cycle_id} open exhaustion exit lacks policy-bound continuation"))

        loopbreak = event.get("loopbreak")
        graph = event.get("noetic_dependency_graph")
        if validation_profile == CURRENT_PROFILE:
            graph_error = _graph_object_error(graph)
            if graph_error is not None:
                subcode = "graph_hash_mismatch" if "graph_sha256" in graph_error else "malformed_graph_edge"
                return stop(_cycle_error(subcode, cycle_id, f"{subcode}: cycle {cycle_id} noetic_dependency_graph {graph_error}"))
            if loopbreak is not None:
                required = (
                    "loopbreak_id",
                    "observed_loop",
                    "observed_loop_event_index",
                    "pre_break_graph",
                    "owner_ground_ref",
                    "performed_operation_ref",
                    "local_delta_ref",
                    "interruption_event_index",
                    "post_break_graph",
                    "post_break_reread",
                    "loopbreak_sha256",
                )
                missing = [key for key in required if not _is_mapping(loopbreak) or key not in loopbreak]
                if missing:
                    return stop(
                        _cycle_error(
                            "incomplete_loopbreak",
                            cycle_id,
                            f"incomplete_loopbreak: cycle {cycle_id} LoopBreak lacks {missing[0]}",
                        )
                    )
                if not _nonempty(loopbreak.get("loopbreak_id")):
                    return stop(_cycle_error("incomplete_loopbreak", cycle_id, f"incomplete_loopbreak: cycle {cycle_id} loopbreak_id must be non-empty"))
                observed_loop = loopbreak.get("observed_loop")
                if (
                    not isinstance(observed_loop, list)
                    or len(observed_loop) < 3
                    or observed_loop[0] != observed_loop[-1]
                    or not all(_nonempty(node) for node in observed_loop)
                ):
                    return stop(
                        _cycle_error(
                            "incomplete_loopbreak",
                            cycle_id,
                            f"incomplete_loopbreak: cycle {cycle_id} observed_loop must name a non-empty closed loop",
                        )
                    )
                pre_break_graph = loopbreak.get("pre_break_graph")
                post_break_graph = loopbreak.get("post_break_graph")
                for graph_name, graph_value in (("pre_break_graph", pre_break_graph), ("post_break_graph", post_break_graph)):
                    nested_error = _graph_object_error(graph_value)
                    if nested_error is not None:
                        subcode = "graph_hash_mismatch" if "graph_sha256" in nested_error else "malformed_graph_edge"
                        return stop(_cycle_error(subcode, cycle_id, f"{subcode}: cycle {cycle_id} {graph_name} {nested_error}"))
                owner_ground_ref = loopbreak.get("owner_ground_ref")
                if not _is_mapping(owner_ground_ref) or not _nonempty(owner_ground_ref.get("ref_id")) or not _hash_ok(owner_ground_ref.get("sha256")):
                    return stop(_cycle_error("incomplete_loopbreak", cycle_id, f"incomplete_loopbreak: cycle {cycle_id} owner_ground_ref lacks ref_id/sha256 custody"))
                operation_ref = loopbreak.get("performed_operation_ref")
                if not _is_mapping(operation_ref) or not _nonempty(operation_ref.get("ref_id")) or not _hash_ok(operation_ref.get("sha256")):
                    return stop(_cycle_error("incomplete_loopbreak", cycle_id, f"incomplete_loopbreak: cycle {cycle_id} performed_operation_ref lacks ref_id/sha256 custody"))
                local_delta_ref = loopbreak.get("local_delta_ref")
                if not _is_mapping(local_delta_ref) or not _nonempty(local_delta_ref.get("delta_id")) or not _hash_ok(local_delta_ref.get("sha256")):
                    return stop(_cycle_error("incomplete_loopbreak", cycle_id, f"incomplete_loopbreak: cycle {cycle_id} local_delta_ref lacks delta_id/sha256 custody"))
                post_reread = loopbreak.get("post_break_reread")
                if (
                    not _is_mapping(post_reread)
                    or not _nonempty(post_reread.get("record_id"))
                    or not _hash_ok(post_reread.get("record_sha256"))
                    or not isinstance(post_reread.get("event_index"), int)
                    or not isinstance(post_reread.get("field_diagnostics"), list)
                ):
                    return stop(_cycle_error("incomplete_loopbreak", cycle_id, f"incomplete_loopbreak: cycle {cycle_id} post_break_reread lacks retained whole-field custody"))
                if (
                    not _hash_ok(loopbreak.get("loopbreak_sha256"))
                    or loopbreak.get("loopbreak_sha256") != _canonical_object_hash(loopbreak, "loopbreak_sha256")
                ):
                    return stop(_cycle_error("loopbreak_hash_mismatch", cycle_id, f"loopbreak_hash_mismatch: cycle {cycle_id} loopbreak_sha256 is not canonical"))
                observed_index = loopbreak.get("observed_loop_event_index")
                interruption_index = loopbreak.get("interruption_event_index")
                reread_index = post_reread.get("event_index")
                order = (cycle.get("land", {}).get("event_index"), observed_index, interruption_index, reread_index, event.get("event_index"))
                if not all(isinstance(index, int) for index in order) or list(order) != sorted(order) or len(set(order)) != len(order):
                    return stop(
                        _cycle_error(
                            "loopbreak_event_order",
                            cycle_id,
                            f"loopbreak_event_order: cycle {cycle_id} requires Land < observed loop < interruption < post-break reread < raw exit; got {order}",
                        )
                    )
                for middle_index in (observed_index, interruption_index, reread_index):
                    if middle_index in governed_event_indices:
                        return stop(_cycle_error("event_index_replayed", cycle_id, f"cycle {cycle_id} LoopBreak reuses event_index {middle_index}"))
                    governed_event_indices.add(middle_index)
                pre_edges = {tuple(edge) for edge in pre_break_graph.get("edges", [])}
                post_edges = {tuple(edge) for edge in post_break_graph.get("edges", [])}
                named_edges = list(zip(observed_loop, observed_loop[1:]))
                if any(edge not in pre_edges for edge in named_edges):
                    return stop(_cycle_error("incomplete_loopbreak", cycle_id, f"incomplete_loopbreak: cycle {cycle_id} observed_loop is absent from pre_break_graph"))
                if all(edge in post_edges for edge in named_edges):
                    return stop(
                        _cycle_error(
                            "loopbreak_named_loop_unchanged",
                            cycle_id,
                            f"loopbreak_named_loop_unchanged: cycle {cycle_id} named loop {observed_loop} survives unchanged",
                        )
                    )
                if graph.get("nodes") != post_break_graph.get("nodes") or graph.get("edges") != post_break_graph.get("edges"):
                    return stop(_cycle_error("incomplete_loopbreak", cycle_id, f"incomplete_loopbreak: cycle {cycle_id} noetic_dependency_graph must equal post_break_graph"))
                if _graph_has_cycle(post_break_graph.get("edges", [])) and exit_disposition not in {"RECURSE", "HOLD", "PARTIAL"}:
                    return stop(
                        _cycle_error(
                            "loopbreak_remaining_cycle_exit",
                            cycle_id,
                            f"loopbreak_remaining_cycle_exit: cycle {cycle_id} residual noetic cycle forbids {exit_disposition}; use RECURSE, HOLD, or PARTIAL",
                        )
                    )
            elif _graph_has_cycle(graph.get("edges", [])) and exit_disposition == "STOP":
                return stop(_cycle_error("incomplete_loopbreak", cycle_id, f"incomplete_loopbreak: cycle {cycle_id} cannot STOP with an unaccounted noetic loop"))
        elif loopbreak is not None:
            return stop(_cycle_error("historical_loopbreak_unsupported", cycle_id, f"historical profile cycle {cycle_id} cannot promote LoopBreak evidence"))

        lifecycle = cycle.get("lifecycle_status")
        terminal_state = cycle.get("terminal_state")
        expected_status = {
            "STOP": ("landed", "landed"),
            "COMPLETE": ("complete", "complete"),
            "RECURSE": ("landed", "landed"),
            "PARTIAL": ("partial", "partial"),
            "HANDOFF": ("partial", "partial"),
            "HOLD": ("held", "held"),
        }[str(exit_disposition)]
        partition_name = {
            "STOP": "closure_candidate",
            "COMPLETE": "complete",
            "RECURSE": "recurse",
            "PARTIAL": "partial",
            "HANDOFF": "partial",
            "HOLD": "held",
        }[str(exit_disposition)]
        state_args["lifecycle_partitions"][partition_name].add(str(cycle.get("burden_id")))
        if (lifecycle, terminal_state) != expected_status:
            return stop(
                _cycle_error(
                    "lifecycle_accounting",
                    cycle_id,
                    f"cycle {cycle_id} {exit_disposition} requires lifecycle/terminal {expected_status}, got {(lifecycle, terminal_state)}",
                )
            )
        if exit_disposition in {"STOP", "COMPLETE"}:
            if preempted:
                candidate_id = sorted(preempted)[0]
                return stop(
                    _cycle_error(
                        "preempted_dropped",
                        cycle_id,
                        f"{exit_disposition} drops live preempted candidate {candidate_id}",
                    )
                )
            if state_args["live_candidates"]:
                candidate_id = sorted(state_args["live_candidates"])[0]
                return stop(
                    _cycle_error(
                        "live_candidate_stop" if exit_disposition == "STOP" else "live_candidate_complete",
                        cycle_id,
                        f"live_candidate_{exit_disposition.lower()}: {exit_disposition} cannot coexist with live candidate {candidate_id}",
                    )
                )
            no_new = event.get("no_new_resultant")
            if (
                not _is_mapping(no_new)
                or no_new.get("observed") is not True
                or no_new.get("live_obligation_ids") != []
                or no_new.get("unresolved_candidate_ids") != []
            ):
                return stop(_cycle_error("no_new_not_observed", cycle_id, f"cycle {cycle_id} {exit_disposition} lacks observed no-new proof"))
        burden_terminal_states[burden_id] = str(terminal_state)
        reread_signature = _reread_state_signature(
            b_la=b_la,
            b_mrp=b_mrp,
            burden_terminal_states=burden_terminal_states,
            candidate_history=candidate_history,
            live_candidates=state_args["live_candidates"],
            live_obligations=state_args["live_obligations"],
            event=event,
            cycle_semantics={
                "operation": cycle.get("operation"),
                "land": cycle.get("land"),
                "post_land_delta": cycle.get("post_land_delta"),
            },
        )
        event_id = str(event.get("event_id"))
        state_args["reread_signatures"].append((cycle_id, event_id, reread_signature))
        prior_signature = signature_seen.get(reread_signature)
        if prior_signature is not None and exit_disposition == "RECURSE":
            prior_cycle_id, prior_event_id = prior_signature
            return stop(
                _cycle_error(
                    "repeated_state_detected",
                    cycle_id,
                    f"repeated_state_detected: cycle {cycle_id}/{event_id} repeats governed reread state from {prior_cycle_id}/{prior_event_id}; ordinary RECURSE cannot silently retry",
                )
            )
        signature_seen.setdefault(reread_signature, (cycle_id, event_id))
        last_cycle_for_burden[burden_id] = cycle
        if exit_disposition in {"STOP", "COMPLETE", "HOLD", "PARTIAL", "HANDOFF"}:
            terminal_cycle = (cycle_id, str(exit_disposition))

    for cycle in cycles:
        cycle_id = str(cycle.get("cycle_id"))
        burden_id = str(cycle.get("burden_id"))
        origin = cycle.get("origin")
        depth = cycle.get("generation_depth")
        parent_id = cycle.get("parent_cycle_id")
        if origin == "B_LA":
            if depth != 0 or parent_id is not None:
                return stop(_cycle_error("baseline_provenance", cycle_id, f"B_LA cycle {cycle_id} requires depth 0 and parent null"))
            continue
        if origin != "B_MRP":
            return stop(_cycle_error("origin_invalid", cycle_id, f"cycle {cycle_id} origin must be B_LA or B_MRP"))
        if parent_id is None:
            return stop(_cycle_error("parent_missing", cycle_id, f"generated cycle {cycle_id} burden {burden_id} has missing parent_cycle_id"))
        parent_id = str(parent_id)
        generation = generated_by_target.get(burden_id)
        if generation is None:
            return stop(_cycle_error("generation_event_missing", cycle_id, f"B_MRP burden {burden_id} lacks an earlier instantiation event"))
        observed_parent, expected_cycle = generation
        if parent_id != observed_parent:
            return stop(
                _cycle_error(
                    "parent_mismatch",
                    cycle_id,
                    f"generated cycle {cycle_id} parent {parent_id} mismatches instantiating parent {observed_parent}; expected {observed_parent}",
                )
            )
        if expected_cycle != cycle_id:
            return stop(_cycle_error("scheduled_target_mismatch", cycle_id, f"generated burden {burden_id} was scheduled for {expected_cycle}, not {cycle_id}"))
        if parent_id not in index_by_cycle or index_by_cycle[parent_id] >= index_by_cycle[cycle_id]:
            return stop(_cycle_error("event_dag_cycle", cycle_id, f"generated parent {parent_id} is not earlier than {cycle_id}"))
        parent_depth = cycle_by_id[parent_id].get("generation_depth")
        expected_depth = parent_depth + 1 if isinstance(parent_depth, int) else None
        if depth != expected_depth:
            return stop(
                _cycle_error(
                    "depth_mismatch",
                    cycle_id,
                    f"generated cycle {cycle_id} has depth {depth}; expected depth {expected_depth}",
                )
            )
        state_args["maximum_depth"] = max(state_args["maximum_depth"], int(depth))

    for target, (source_cycle, expected_cycle) in generated_by_target.items():
        if target not in cycles_by_burden:
            source_exit = event_by_cycle[source_cycle].get("exit_disposition")
            if source_exit not in {"PARTIAL", "HANDOFF", "HOLD"}:
                return stop(
                    _cycle_error(
                        "generated_not_executed",
                        source_cycle,
                        f"generated burden {target} never entered later Stage03/04/Land/Stage05 cycle {expected_cycle}",
                    )
                )

    if _graph_has_cycle(state_args["event_edges"]):
        return stop(Finding("event_dag_cycle", "custody/provenance event DAG contains a cycle"))
    state_args["live_candidates"].update(preempted)
    return _finish(**state_args)


def _state_v2_graph_projection(
    graph: Any,
    *,
    cycle_id: str,
    identity: str,
) -> tuple[dict[str, Any] | None, Finding | None]:
    if not _is_mapping(graph):
        return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, f"state-v2 {identity} must be an object")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if (
        not isinstance(nodes, list)
        or not all(_nonempty(node) for node in nodes)
        or len(set(str(node) for node in nodes)) != len(nodes)
        or not isinstance(edges, list)
    ):
        return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, f"state-v2 {identity} has malformed nodes/edges")
    node_set = {str(node) for node in nodes}
    projected_edges: list[list[str]] = []
    for edge in edges:
        if not _is_mapping(edge) or not _nonempty(edge.get("from")) or not _nonempty(edge.get("to")):
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, f"state-v2 {identity} edge must have from/to")
        left, right = str(edge["from"]), str(edge["to"])
        if left not in node_set or right not in node_set:
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, f"state-v2 {identity} edge endpoint is unresolved")
        projected_edges.append([left, right])
    if graph.get("graph_sha256") != _state_v2_hash(graph, "graph_sha256"):
        return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, f"state-v2 {identity} graph_sha256 mismatch")
    projection: dict[str, Any] = {"nodes": list(nodes), "edges": projected_edges}
    projection["graph_sha256"] = _canonical_object_hash(projection, "graph_sha256")
    return projection, None


def _adapt_state_v2_loopbreak(
    loopbreak: Any,
    *,
    cycle_id: str,
) -> tuple[dict[str, Any] | None, Finding | None]:
    if loopbreak is None:
        return None, None
    required = {
        "loopbreak_id", "observed_loop", "observed_loop_event_index", "pre_break_graph",
        "owner_ground_ref", "performed_operation_ref", "local_delta_ref", "interruption_event_index",
        "post_break_graph", "post_break_reread", "loopbreak_sha256",
    }
    if not _is_mapping(loopbreak) or required - set(loopbreak):
        return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 LoopBreak is incomplete")
    if loopbreak.get("loopbreak_sha256") != _state_v2_hash(loopbreak, "loopbreak_sha256"):
        return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 LoopBreak self-hash mismatch")
    pre_graph, finding = _state_v2_graph_projection(loopbreak.get("pre_break_graph"), cycle_id=cycle_id, identity="pre_break_graph")
    if finding:
        return None, finding
    post_graph, finding = _state_v2_graph_projection(loopbreak.get("post_break_graph"), cycle_id=cycle_id, identity="post_break_graph")
    if finding:
        return None, finding
    post = loopbreak.get("post_break_reread")
    if not _is_mapping(post) or post.get("record_sha256") != _state_v2_hash(post, "record_sha256"):
        return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 LoopBreak post-break reread hash mismatch")
    for diagnostic in post.get("field_diagnostics", []):
        if not _is_mapping(diagnostic) or diagnostic.get("event_sha256") != _state_v2_hash(diagnostic, "event_sha256"):
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 LoopBreak post-break diagnostic hash mismatch")
    owner_ref = loopbreak.get("owner_ground_ref")
    operation_ref = loopbreak.get("performed_operation_ref")
    delta_ref = loopbreak.get("local_delta_ref")
    if not all(_is_mapping(value) for value in (owner_ref, operation_ref, delta_ref)):
        return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 LoopBreak refs are malformed")
    projection: dict[str, Any] = {
        "loopbreak_id": loopbreak["loopbreak_id"],
        "observed_loop": loopbreak["observed_loop"],
        "observed_loop_event_index": loopbreak["observed_loop_event_index"],
        "pre_break_graph": pre_graph,
        "owner_ground_ref": {"ref_id": owner_ref.get("id"), "sha256": owner_ref.get("sha256")},
        "performed_operation_ref": {"ref_id": operation_ref.get("id"), "sha256": operation_ref.get("sha256")},
        "local_delta_ref": {"delta_id": delta_ref.get("delta_id"), "sha256": delta_ref.get("sha256")},
        "interruption_event_index": loopbreak["interruption_event_index"],
        "post_break_graph": post_graph,
        "post_break_reread": {
            "record_id": post.get("record_id"),
            "record_sha256": post.get("record_sha256"),
            "event_index": post.get("event_index"),
            "field_diagnostics": post.get("field_diagnostics", []),
        },
    }
    projection["loopbreak_sha256"] = _canonical_object_hash(projection, "loopbreak_sha256")
    return projection, None


def _adapt_state_v2_payload(payload: Mapping[str, Any]) -> tuple[dict[str, Any] | None, Finding | None]:
    """Fail-closed pure adapter from corrected state-capsule-v2 cycle custody."""

    policy = payload.get("resource_policy")
    if not _is_mapping(policy):
        return None, Finding("resource_policy_invalid", "state-v2 resource_policy must be an object")
    if policy.get("policy_sha256") != _canonical_object_hash(policy, "policy_sha256"):
        return None, Finding(
            "resource_policy_hash_mismatch",
            "resource_policy_hash_mismatch: state-v2 resource policy policy_sha256 does not match canonical contents",
        )
    owner_routes = payload.get("owner_routes")
    act_rows = payload.get("act_row_details")
    dispositions = payload.get("owner_execution_dispositions")
    obligation_state = payload.get("owner_obligation_state")
    operation_capsules = payload.get("operation_capsules")
    cycles = payload.get("burden_cycles")
    if not isinstance(owner_routes, list):
        return None, Finding("state_v2_obligation_invalid", "state-v2 owner_routes must be an array")
    if not isinstance(act_rows, list):
        return None, Finding("state_v2_act_row_invalid", "state-v2 act_row_details must be an array")
    if not isinstance(dispositions, list):
        return None, Finding("state_v2_disposition_invalid", "state-v2 owner_execution_dispositions must be an array")
    if not _is_mapping(obligation_state):
        return None, Finding("state_v2_obligation_state_invalid", "state-v2 owner_obligation_state must be an object")
    if not isinstance(operation_capsules, list):
        return None, Finding("state_v2_operation_event_invalid", "state-v2 operation_capsules must be an array")
    if not isinstance(cycles, list) or not cycles:
        return None, Finding("cycle_array_required", "state-v2 burden_cycles must be a non-empty ordered array")

    obligation_by_id = {str(row.get("obligation_id")): row for row in owner_routes if _is_mapping(row) and _nonempty(row.get("obligation_id"))}
    act_by_id = {str(row.get("obligation_id")): row for row in act_rows if _is_mapping(row) and _nonempty(row.get("obligation_id"))}
    disposition_by_id = {str(row.get("obligation_id")): row for row in dispositions if _is_mapping(row) and _nonempty(row.get("obligation_id"))}
    operation_by_id = {
        str(row.get("capsule_id")): row for row in operation_capsules if _is_mapping(row) and _nonempty(row.get("capsule_id"))
    }
    if len(obligation_by_id) != len(owner_routes):
        return None, Finding("state_v2_obligation_invalid", "state-v2 obligation identities must be present and unique")
    if set(act_by_id) - set(obligation_by_id) or set(disposition_by_id) - set(obligation_by_id):
        return None, Finding("state_v2_obligation_invalid", "state-v2 owner routes must cover all downstream obligation custody")
    if len(act_by_id) != len(act_rows) or set(act_by_id) != set(obligation_by_id):
        return None, Finding("state_v2_act_row_invalid", "state-v2 act rows must uniquely cover owner routes")
    if len(disposition_by_id) != len(dispositions) or set(disposition_by_id) != set(obligation_by_id):
        return None, Finding("state_v2_disposition_invalid", "state-v2 execution dispositions must uniquely cover owner routes")
    expected_obligation_state = {
        "declared_ids": list(obligation_by_id),
        "executed_ids": [str(row.get("obligation_id")) for row in dispositions if row.get("disposition") == "executed"],
        "held_ids": [str(row.get("obligation_id")) for row in dispositions if row.get("disposition") == "held"],
        "partial_ids": [str(row.get("obligation_id")) for row in dispositions if row.get("disposition") == "partial"],
        "terminal_disposition_sha256": _signature(dispositions),
    }
    if dict(obligation_state) != expected_obligation_state:
        return None, Finding("state_v2_obligation_state_invalid", "state-v2 obligation state is not the exact declared/executed/held/partial disposition projection")
    route_core = ("obligation_id", "burden_id", "pressure_ids", "owner_id", "operation", "register_axis")
    disposition_field = {"executed": "executed_ids", "held": "held_ids", "partial": "partial_ids"}
    for obligation_id, route_row in obligation_by_id.items():
        act_row = act_by_id[obligation_id]
        disposition_row = disposition_by_id[obligation_id]
        if any(act_row.get(key) != route_row.get(key) for key in route_core):
            return None, Finding("state_v2_act_row_invalid", f"state-v2 act row {obligation_id} diverges from its owner route")
        terminal_field = disposition_field.get(str(disposition_row.get("disposition")))
        if terminal_field is not None and obligation_id not in obligation_state.get(terminal_field, []):
            return None, Finding("state_v2_disposition_invalid", f"state-v2 disposition {obligation_id} diverges from obligation state")
        if disposition_row.get("burden_id") != route_row.get("burden_id"):
            return None, Finding("state_v2_disposition_invalid", f"state-v2 disposition {obligation_id} targets another burden")
    if len(operation_by_id) != len(operation_capsules):
        return None, Finding("state_v2_operation_event_invalid", "state-v2 operation capsule identities must be present and unique")

    projected_cycles: list[dict[str, Any]] = []
    projected_edges: list[list[str]] = []
    freeze = payload.get("stage02_freeze")
    if not _is_mapping(freeze) or not isinstance(freeze.get("event_index"), int):
        return None, Finding("state_v2_route_invalid", "state-v2 stage02 freeze event custody is required before cycle routing")
    last_global_index = int(freeze["event_index"])
    global_indices: set[int] = {last_global_index}
    for raw_cycle in cycles:
        if not _is_mapping(raw_cycle):
            return None, Finding("cycle_shape", "state-v2 burden cycle must be an object")
        cycle_id = str(raw_cycle.get("cycle_id"))
        burden_id = str(raw_cycle.get("burden_id"))

        route = raw_cycle.get("route_gradient")
        route_required = {"event_id", "event_index", "record_id", "record_sha256", "target_burden_id", "source_refs", "basis_refs", "event_sha256"}
        if not _is_mapping(route) or route_required - set(route) or route.get("target_burden_id") != burden_id:
            return None, _cycle_error("state_v2_route_invalid", cycle_id, "state-v2 route_gradient is missing, incomplete, or targets another burden")
        expected_route_record = _state_v2_hash(
            {key: route[key] for key in ("record_id", "target_burden_id", "source_refs", "basis_refs")},
            "__absent__",
        )
        if route.get("record_sha256") != expected_route_record or route.get("event_sha256") != _state_v2_hash(route, "event_sha256"):
            return None, _cycle_error("state_v2_route_invalid", cycle_id, "state-v2 route_gradient hash mismatch")

        obligation_ids = raw_cycle.get("obligation_ids")
        if not isinstance(obligation_ids, list) or len(set(obligation_ids)) != len(obligation_ids):
            return None, _cycle_error("state_v2_obligation_invalid", cycle_id, "state-v2 cycle obligation_ids must be a unique array")
        if raw_cycle.get("obligation_set_sha256") != _signature(sorted(obligation_ids)):
            return None, _cycle_error("state_v2_obligation_invalid", cycle_id, "state-v2 obligation_set_sha256 mismatch")
        for obligation_id in obligation_ids:
            obligation = obligation_by_id.get(str(obligation_id))
            if obligation is None or obligation.get("burden_id") != burden_id:
                return None, _cycle_error("state_v2_obligation_invalid", cycle_id, f"state-v2 obligation {obligation_id!r} is unresolved or belongs to another burden")

        operation_ids = raw_cycle.get("operation_capsule_ids")
        events = raw_cycle.get("operation_events")
        if not isinstance(operation_ids, list) or not isinstance(events, list):
            return None, _cycle_error("state_v2_operation_event_invalid", cycle_id, "state-v2 operation capsules/events must be arrays")
        expected_kinds = ["before_state", "owner.operation", "performed_evidence", "local_delta", "residual", "land_contribution"]
        contributions: list[str] = []
        operation_indices: list[int] = []
        for ordinal, operation_id in enumerate(operation_ids):
            capsule = operation_by_id.get(str(operation_id))
            if (
                capsule is None
                or capsule.get("cycle_id") != cycle_id
                or capsule.get("burden_id") != burden_id
                or not isinstance(capsule.get("obligation_ids"), list)
                or not set(capsule.get("obligation_ids", [])).issubset(set(obligation_ids))
            ):
                return None, _cycle_error("state_v2_operation_event_invalid", cycle_id, f"state-v2 operation capsule {operation_id!r} is unbound")
            if capsule.get("operation_capsule_sha256") != "sha256:" + _state_v2_hash(capsule, "operation_capsule_sha256"):
                return None, _cycle_error("state_v2_operation_hash_mismatch", cycle_id, f"state-v2 operation capsule {operation_id!r} self-hash does not cover governed content")
            for obligation_id in capsule.get("obligation_ids", []):
                route_row = obligation_by_id[str(obligation_id)]
                act_row = act_by_id[str(obligation_id)]
                if (
                    any(capsule.get(key) != route_row.get(key) for key in ("burden_id", "pressure_ids", "owner_id", "operation", "register_axis"))
                    or capsule.get("body_ref") != act_row.get("body_ref")
                ):
                    return None, _cycle_error("state_v2_operation_event_invalid", cycle_id, f"state-v2 operation capsule {operation_id!r} diverges from Plan04 custody")
            group = events[ordinal * 6:(ordinal + 1) * 6]
            expected_refs = [
                f"capsule:{operation_id}#before_state",
                f"route:{capsule.get('obligation_ids', [None])[0]}#owner.operation",
                f"capsule:{operation_id}#performed_operation",
                f"capsule:{operation_id}#delta",
                f"capsule:{operation_id}#residual",
                f"capsule:{operation_id}#land_contribution",
            ]
            if (
                len(group) != 6
                or [row.get("sequence") for row in group if _is_mapping(row)] != list(range(1, 7))
                or [row.get("kind") for row in group if _is_mapping(row)] != expected_kinds
                or [row.get("ref") for row in group if _is_mapping(row)] != expected_refs
                or any(row.get("operation_capsule_id") != operation_id for row in group if _is_mapping(row))
            ):
                return None, _cycle_error("state_v2_operation_event_invalid", cycle_id, "state-v2 operation event chronology/cardinality mismatch")
            for row in group:
                if not _is_mapping(row) or row.get("event_sha256") != _state_v2_hash(row, "event_sha256") or not isinstance(row.get("event_index"), int):
                    return None, _cycle_error("state_v2_operation_event_invalid", cycle_id, "state-v2 operation event is malformed or hash-invalid")
                operation_indices.append(row["event_index"])
            contributions.append(f"capsule:{operation_id}#land_contribution")
        if len(events) != 6 * len(operation_ids):
            return None, _cycle_error("state_v2_operation_event_invalid", cycle_id, "state-v2 operation event cardinality must equal six per capsule")

        land = raw_cycle.get("land")
        if (
            not _is_mapping(land)
            or land.get("status") != "landed"
            or land.get("operation_capsule_ids") != operation_ids
            or land.get("contribution_refs") != contributions
            or not isinstance(land.get("event_index"), int)
            or (operation_indices and land["event_index"] <= max(operation_indices))
        ):
            return None, _cycle_error("state_v2_land_invalid", cycle_id, "state-v2 Land is missing, early, or unbound")
        expected_land_record = _state_v2_hash(
            {key: land[key] for key in ("record_id", "status", "operation_capsule_ids", "contribution_refs")},
            "__absent__",
        )
        if land.get("record_sha256") != expected_land_record or land.get("event_sha256") != _state_v2_hash(land, "event_sha256"):
            return None, _cycle_error("state_v2_land_invalid", cycle_id, "state-v2 Land record/event hash mismatch")

        delta = raw_cycle.get("post_land_delta")
        if (
            not _is_mapping(delta)
            or not isinstance(delta.get("event_index"), int)
            or delta["event_index"] <= land["event_index"]
            or delta.get("source_land_event_id") != land.get("event_id")
            or delta.get("source_operation_capsule_ids") != operation_ids
        ):
            return None, _cycle_error("state_v2_post_land_invalid", cycle_id, "state-v2 post-Land delta is missing, early, or unbound")
        expected_delta = _state_v2_hash(
            {key: delta[key] for key in ("delta_id", "source_land_event_id", "source_operation_capsule_ids", "basis_refs")},
            "__absent__",
        )
        if delta.get("delta_sha256") != expected_delta or delta.get("event_sha256") != _state_v2_hash(delta, "event_sha256"):
            return None, _cycle_error("state_v2_post_land_invalid", cycle_id, "state-v2 post-Land delta hash mismatch")

        reread = raw_cycle.get("reread")
        if (
            not _is_mapping(reread)
            or reread.get("target_burden_id") != burden_id
            or reread.get("source_land_event_id") != land.get("event_id")
            or reread.get("source_delta_event_id") != delta.get("event_id")
        ):
            return None, _cycle_error("state_v2_reread_invalid", cycle_id, "state-v2 reread is missing or unbound from Land/post-Land delta")
        raw_exit = reread.get("raw_exit")
        raw_required = {"event_id", "event_index", "raw_exit_sha256", "exit_disposition", "candidate_events", "field_diagnostics", "noetic_dependency_graph", "no_new_resultant", "loopbreak", "resource_exhaustion"}
        if not _is_mapping(raw_exit) or raw_required - set(raw_exit):
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 raw_exit is missing or incomplete")
        if raw_exit.get("exit_disposition") == "COMPLETE" or raw_exit.get("exit_disposition") not in {"STOP", "RECURSE", "HOLD", "PARTIAL", "HANDOFF"}:
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 raw exit must preserve STOP/RECURSE/HOLD/PARTIAL/HANDOFF; raw COMPLETE is forbidden")

        projected_candidates: list[dict[str, Any]] = []
        for candidate in raw_exit.get("candidate_events", []):
            if not _is_mapping(candidate):
                return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 candidate event must be an object")
            disposition = candidate.get("disposition")
            if disposition not in CANDIDATE_DISPOSITIONS:
                return None, _cycle_error(
                    "state_v2_candidate_disposition_delta",
                    cycle_id,
                    "state_v2_candidate_disposition_delta: state-v2 must use exact canonical A07 activate_held|instantiate_generated|defer_preempted|non_load_bearing|hold_partial vocabulary; ambiguous mapping is rejected",
                )
            kind = candidate.get("kind")
            allowed_by_kind = {
                "held_activation": {"activate_held"},
                "generated_instantiation": {"instantiate_generated"},
                "escape_route": {"defer_preempted", "non_load_bearing", "hold_partial"},
                "unclassified": {"hold_partial"},
            }
            if kind in allowed_by_kind and disposition not in allowed_by_kind[kind]:
                return None, _cycle_error("state_v2_candidate_kind_delta", cycle_id, "state-v2 candidate kind/disposition pairing is not canonical A07")
            if kind not in allowed_by_kind and disposition != "hold_partial":
                return None, _cycle_error("state_v2_candidate_kind_delta", cycle_id, "state-v2 unknown candidate kind must remain explicitly held")
            if candidate.get("candidate_event_sha256") != _state_v2_hash(candidate, "candidate_event_sha256"):
                return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 candidate event hash mismatch")
            projected = {key: candidate.get(key) for key in (
                "candidate_event_id", "candidate_id", "previous_candidate_event_id", "event_index", "disposition",
                "target_burden_id", "next_cycle_id", "basis_refs", "gate", "next_action",
            )}
            projected["kind"] = kind
            projected_candidates.append(projected)
            if candidate.get("next_cycle_id") is not None:
                projected_edges.append([cycle_id, str(candidate.get("next_cycle_id"))])

        for diagnostic in raw_exit.get("field_diagnostics", []):
            if not _is_mapping(diagnostic) or diagnostic.get("event_sha256") != _state_v2_hash(diagnostic, "event_sha256"):
                return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 field diagnostic hash mismatch")
        graph, finding = _state_v2_graph_projection(raw_exit.get("noetic_dependency_graph"), cycle_id=cycle_id, identity="noetic_dependency_graph")
        if finding:
            return None, finding
        loopbreak, finding = _adapt_state_v2_loopbreak(raw_exit.get("loopbreak"), cycle_id=cycle_id)
        if finding:
            return None, finding
        no_new = raw_exit.get("no_new_resultant")
        projected_no_new = None
        if no_new is not None:
            if (
                not _is_mapping(no_new)
                or no_new.get("sha256") != _state_v2_hash(no_new, "sha256")
                or (raw_exit.get("exit_disposition") == "STOP" and no_new.get("stop_licensed") is not True)
            ):
                return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 no_new_resultant is unlicensed or hash-invalid")
            projected_no_new = {
                "observed": no_new.get("observed"),
                "live_obligation_ids": no_new.get("live_obligation_ids"),
                "unresolved_candidate_ids": no_new.get("unresolved_candidate_ids"),
            }
        if raw_exit.get("resource_exhaustion") is not None:
            return None, _cycle_error("state_v2_resource_exhaustion_delta", cycle_id, "state-v2 resource_exhaustion has no unambiguous A07 continuation mapping")
        if raw_exit.get("raw_exit_sha256") != _state_v2_hash(raw_exit, "raw_exit_sha256"):
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 raw_exit self-hash mismatch")
        if reread.get("record_sha256") != _state_v2_hash(reread, "record_sha256"):
            return None, _cycle_error("state_v2_reread_invalid", cycle_id, "state-v2 reread record hash mismatch")
        if raw_cycle.get("cycle_sha256") != _state_v2_hash(raw_cycle, "cycle_sha256"):
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 cycle self-hash mismatch")

        post_indices = [candidate.get("event_index") for candidate in raw_exit.get("candidate_events", [])]
        post_indices.extend(diagnostic.get("event_index") for diagnostic in raw_exit.get("field_diagnostics", []))
        if loopbreak is not None:
            post_indices.extend([
                loopbreak.get("observed_loop_event_index"), loopbreak.get("interruption_event_index"),
                loopbreak.get("post_break_reread", {}).get("event_index"),
            ])
            post_indices.extend(diagnostic.get("event_index") for diagnostic in loopbreak.get("post_break_reread", {}).get("field_diagnostics", []))
        event_indices = [route.get("event_index"), *operation_indices, land.get("event_index"), delta.get("event_index"), *post_indices]
        event_indices.append(raw_exit.get("event_index"))
        if not all(isinstance(index, int) for index in event_indices) or len(event_indices) != len(set(event_indices)):
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 cycle event indices must be present and unique")
        route_index = int(route["event_index"])
        raw_index = int(raw_exit["event_index"])
        if route_index <= last_global_index:
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 event DAG order must advance after the prior cycle/freeze")
        if operation_indices and (operation_indices != sorted(operation_indices) or route_index >= min(operation_indices)):
            return None, _cycle_error("state_v2_operation_event_invalid", cycle_id, "state-v2 route must precede ordered operation events")
        if any(int(index) <= int(delta["event_index"]) for index in post_indices) or raw_index <= max([int(delta["event_index"]), *[int(index) for index in post_indices]]):
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 candidate/diagnostic/LoopBreak events must follow post-Land delta and precede raw exit")
        if global_indices.intersection(event_indices):
            return None, _cycle_error("state_v2_raw_exit_invalid", cycle_id, "state-v2 global event index is replayed")
        global_indices.update(event_indices)
        last_global_index = raw_index

        projected_raw: dict[str, Any] = {
            "event_id": raw_exit.get("event_id"), "event_index": raw_exit.get("event_index"),
            "exit_disposition": raw_exit.get("exit_disposition"), "candidate_events": projected_candidates,
            "field_diagnostics": raw_exit.get("field_diagnostics", []), "noetic_dependency_graph": graph,
            "no_new_resultant": projected_no_new, "loopbreak": loopbreak, "resource_exhaustion": None,
        }
        projected_raw["raw_exit_sha256"] = _canonical_object_hash(projected_raw, "raw_exit_sha256")
        operation_projection = {
            "operation_capsules": [operation_by_id[str(value)] for value in operation_ids],
            "operation_events": events,
        }
        projected_cycles.append({
            "cycle_id": cycle_id, "burden_id": burden_id, "origin": raw_cycle.get("origin"),
            "generation_depth": raw_cycle.get("generation_depth"), "parent_cycle_id": raw_cycle.get("parent_cycle_id"),
            "route": {"record_id": route.get("record_id"), "sha256": route.get("record_sha256"), "target_burden_id": burden_id},
            "operation": {"record_id": cycle_id, "sha256": _signature(operation_projection), "performed": True,
                "local_delta": dict(delta), "operation_capsules": operation_projection["operation_capsules"],
                "operation_events": operation_projection["operation_events"]},
            "land": dict(land),
            "post_land_delta": dict(delta),
            "reread": {"record_id": reread.get("record_id"), "sha256": reread.get("record_sha256"), "raw_exit": projected_raw},
            "lifecycle_status": raw_cycle.get("lifecycle_status"), "terminal_state": raw_cycle.get("terminal_state"),
        })

    return {
        "schema": "daee-mrp-recursion-lifecycle-fixture-v1",
        "fixture_id": str(payload.get("capsule_id") or payload.get("fixture_id") or "state-v2-adapter"),
        "validation_profile": CURRENT_PROFILE,
        "promotion_eligible": True,
        "trace_id": payload.get("trace_id"),
        "predecessor_trace_id": None,
        "event_dag_edges": projected_edges,
        "resource_policy": dict(policy),
        "burden_cycles": projected_cycles,
        "non_claims": list(payload.get("non_claims", [])),
    }, None


def validate_lifecycle_record(payload: Any, *, release_bearing: bool = False) -> ReductionState:
    """Validate the test/adapter record and reduce its canonical cycle array."""

    if not _is_mapping(payload):
        return _empty_state(Finding("record_shape", "lifecycle record must be an object"))
    if payload.get("schema") == "daee-state-capsule-v2":
        adapted, finding = _adapt_state_v2_payload(payload)
        if finding is not None:
            return _empty_state(finding)
        if adapted is None:
            return _empty_state(Finding("record_shape", "state-v2 adapter returned no lifecycle projection"))
        state = validate_lifecycle_record(adapted, release_bearing=release_bearing)
        if not state.valid:
            return state
        cycles = payload.get("burden_cycles", [])
        capsules = {
            str(row.get("capsule_id")): row
            for row in payload.get("operation_capsules", [])
            if _is_mapping(row)
        }
        observed_history = payload.get("reread_signature_history")
        if not isinstance(observed_history, list) or len(observed_history) != len(state.reread_signature_history):
            return _empty_state(Finding("state_v2_reread_signature_mismatch", "state-v2 reread signature history cardinality does not match richer A07 reduction"))
        expected_history: list[dict[str, Any]] = []
        for cycle, (cycle_id, raw_exit_event_id, a07_signature), observed in zip(cycles, state.reread_signature_history, observed_history):
            if not _is_mapping(cycle) or not _is_mapping(observed):
                return _empty_state(Finding("state_v2_reread_signature_mismatch", "state-v2 reread signature history row is malformed"))
            capsule_hashes = [
                capsules[str(capsule_id)].get("operation_capsule_sha256")
                for capsule_id in cycle.get("operation_capsule_ids", [])
                if str(capsule_id) in capsules
            ]
            reread_signature = _state_v2_hash({
                "a07_reducer_signature_sha256": a07_signature,
                "performed_operation_capsule_sha256s": capsule_hashes,
                "land_record_sha256": cycle.get("land", {}).get("record_sha256"),
                "land_event_sha256": cycle.get("land", {}).get("event_sha256"),
                "post_land_delta_sha256": cycle.get("post_land_delta", {}).get("delta_sha256"),
                "post_land_delta_event_sha256": cycle.get("post_land_delta", {}).get("event_sha256"),
            }, "__absent__")
            row = {
                "cycle_id": cycle_id,
                "raw_exit_event_id": raw_exit_event_id,
                "a07_reducer_signature_sha256": a07_signature,
                "reread_signature_sha256": reread_signature,
            }
            expected_history.append(row)
            reread = cycle.get("reread")
            if (
                observed != row
                or not _is_mapping(reread)
                or reread.get("a07_reducer_signature_sha256") != a07_signature
                or reread.get("reread_signature_sha256") != reread_signature
            ):
                return _empty_state(Finding(
                    "state_v2_reread_signature_mismatch",
                    f"state-v2 cycle {cycle_id} stored reread signatures are stale against richer canonical A07 operation/Land/post-Land/graph state",
                    cycle_id,
                ))
        if payload.get("reread_signature_history_sha256") != _signature(expected_history):
            return _empty_state(Finding("state_v2_reread_signature_mismatch", "state-v2 reread signature history self-hash is stale against richer A07 reduction"))
        return state
    if payload.get("schema") != "daee-mrp-recursion-lifecycle-fixture-v1":
        return _empty_state(Finding("record_schema", "unsupported lifecycle record schema"))
    if not _nonempty(payload.get("fixture_id")):
        return _empty_state(Finding("record_identity", "fixture_id is required"))
    profile = payload.get("validation_profile")
    promotion_eligible = payload.get("promotion_eligible")
    if profile == CURRENT_PROFILE:
        if promotion_eligible is not True:
            return _empty_state(Finding("validation_profile_invalid", "current-a07-v2 requires promotion_eligible=true"))
        if not _nonempty(payload.get("trace_id")):
            return _empty_state(Finding("trace_identity_missing", "trace_identity_missing: current profile requires trace_id"))
        predecessor_trace_id = payload.get("predecessor_trace_id")
        if predecessor_trace_id is not None and not _nonempty(predecessor_trace_id):
            return _empty_state(Finding("trace_identity_missing", "trace_identity_missing: predecessor_trace_id must be null or non-empty"))
        if not isinstance(payload.get("event_dag_edges"), list):
            return _empty_state(Finding("event_dag_projection_mismatch", "event_dag_projection_mismatch: event_dag_edges must be an array"))
    elif profile == HISTORICAL_PROFILE:
        if promotion_eligible is not False:
            return _empty_state(Finding("validation_profile_invalid", "historical-raw-complete-v1 requires promotion_eligible=false"))
        if release_bearing:
            return _empty_state(
                Finding(
                    "historical_non_promotable",
                    "historical_non_promotable: historical-raw-complete-v1 cannot pass current or release-bearing validation",
                )
            )
    elif profile is None:
        return _empty_state(Finding("validation_profile_missing", "validation_profile_missing: validation_profile is required"))
    else:
        return _empty_state(Finding("validation_profile_invalid", f"unknown validation_profile {profile!r}"))
    state = reduce_burden_cycles(
        payload.get("burden_cycles"),
        resource_policy=payload.get("resource_policy"),
        validation_profile=str(profile) if profile is not None else None,
        predecessor_trace_id=payload.get("predecessor_trace_id"),
    )
    if state.valid and profile == CURRENT_PROFILE:
        observed_edges = payload.get("event_dag_edges")
        well_formed = isinstance(observed_edges, list) and all(
            isinstance(edge, list)
            and len(edge) == 2
            and all(_nonempty(node) for node in edge)
            for edge in observed_edges
        )
        expected_edges = [list(edge) for edge in state.event_dag_edges]
        if not well_formed or observed_edges != expected_edges:
            return replace(
                state,
                findings=(
                    Finding(
                        "event_dag_projection_mismatch",
                        f"event_dag_projection_mismatch: event_dag_edges {observed_edges!r} do not equal reducer-derived {expected_edges!r}",
                    ),
                ),
            )
    return state


def finding_diagnostic(artifact: str, finding: Finding) -> dict[str, Any]:
    """Return the stable Plan 11 diagnostic projection for one finding."""

    return {
        "artifact": artifact,
        "checker": "tools/check_mrp_recursion_lifecycle.py",
        "checker_id": CHECKER_ID,
        "cycle_id": finding.cycle_id,
        "downstream_invalidated": list(DOWNSTREAM_INVALIDATED),
        "earliest_stage": STAGE,
        "exit_category": "structural-rejection",
        "exit_code": 1,
        "failure_class": finding.failure_class,
        "failure_subcode": finding.subcode,
        "message": finding.message,
        "stage": STAGE,
    }


__all__ = [
    "CHECKER_ID",
    "CURRENT_PROFILE",
    "DOWNSTREAM_INVALIDATED",
    "Finding",
    "HISTORICAL_PROFILE",
    "ReductionState",
    "finding_diagnostic",
    "reduce_burden_cycles",
    "validate_lifecycle_record",
]
