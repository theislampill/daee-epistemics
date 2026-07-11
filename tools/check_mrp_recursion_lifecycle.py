#!/usr/bin/env python3
"""Validate ordered MRP recursion lifecycle fixtures and Plan 11 expectations."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from mrp_recursion_lib import (
    CHECKER_ID,
    DOWNSTREAM_INVALIDATED,
    Finding,
    ReductionState,
    finding_diagnostic,
    validate_lifecycle_record,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "mrp-recursion-lifecycle"
VALID_ROOT = FIXTURE_ROOT / "valid"
INVALID_ROOT = FIXTURE_ROOT / "invalid"
STATE_V2_VALID_ROOT = ROOT / "tests" / "state-capsule-v2" / "valid"
MUTATION_SCHEMA = "daee-mrp-recursion-lifecycle-mutation-v1"
EXPECTATION_SCHEMA = "daee-negative-fixture-expectation-v1"
FORBIDDEN_ARTIFACTS = ["stage06-record.json", "stage07-record.json", "stage08-record.json", "promotion-verdict.json"]
EXPECTATION_REQUIRED = {
    "schema",
    "fixture",
    "kind",
    "expected_checker_id",
    "expected_exit_category",
    "expected_exit_code",
    "expected_earliest_stage",
    "expected_failure_class",
    "expected_downstream_invalidated",
    "required_diagnostic_markers",
    "forbidden_artifacts",
    "provenance",
}
EXPECTATION_ALLOWED = EXPECTATION_REQUIRED | {"expected_failure_subcode", "notes"}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _pointer_parent(document: Any, pointer: str) -> tuple[Any, str]:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer {pointer!r}")
    tokens = [token.replace("~1", "/").replace("~0", "~") for token in pointer.split("/")[1:]]
    if not tokens:
        raise ValueError("root mutation is not supported")
    current = document
    for token in tokens[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current, tokens[-1]


def _apply_operation(document: Any, operation: Any) -> None:
    if not isinstance(operation, dict):
        raise ValueError(f"mutation operation must be an object: {operation!r}")
    parent, key = _pointer_parent(document, operation.get("path"))
    op = operation.get("op")
    if op == "set":
        if isinstance(parent, list):
            parent[int(key)] = copy.deepcopy(operation.get("value"))
        else:
            parent[key] = copy.deepcopy(operation.get("value"))
    elif op == "remove":
        if isinstance(parent, list):
            parent.pop(int(key))
        else:
            del parent[key]
    elif op == "append":
        target = parent[int(key)] if isinstance(parent, list) else parent[key]
        if not isinstance(target, list):
            raise ValueError(f"append target {operation.get('path')} is not an array")
        target.append(copy.deepcopy(operation.get("value")))
    elif op == "merge":
        target = parent[int(key)] if isinstance(parent, list) else parent[key]
        value = operation.get("value")
        if not isinstance(target, dict) or not isinstance(value, dict):
            raise ValueError(f"merge target {operation.get('path')} and value must be objects")
        target.update(copy.deepcopy(value))
    else:
        raise ValueError(f"unsupported mutation operation {op!r}")


def _canonical_hash(value: dict[str, Any], self_field: str) -> str:
    body = copy.deepcopy(value)
    body.pop(self_field, None)
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _rehash_mutation(document: Any, operations: list[Any]) -> None:
    if not isinstance(document, dict) or document.get("validation_profile") != "current-a07-v2":
        return
    explicit_paths = {
        operation.get("path")
        for operation in operations
        if isinstance(operation, dict) and isinstance(operation.get("path"), str)
    }
    for cycle_index, cycle in enumerate(document.get("burden_cycles", [])):
        if not isinstance(cycle, dict):
            continue
        raw_exit = cycle.get("reread", {}).get("raw_exit")
        if not isinstance(raw_exit, dict):
            continue
        raw_prefix = f"/burden_cycles/{cycle_index}/reread/raw_exit"
        graphs: list[tuple[str, Any]] = [(f"{raw_prefix}/noetic_dependency_graph", raw_exit.get("noetic_dependency_graph"))]
        loopbreak = raw_exit.get("loopbreak")
        if isinstance(loopbreak, dict):
            graphs.extend(
                [
                    (f"{raw_prefix}/loopbreak/pre_break_graph", loopbreak.get("pre_break_graph")),
                    (f"{raw_prefix}/loopbreak/post_break_graph", loopbreak.get("post_break_graph")),
                ]
            )
        for graph_prefix, graph in graphs:
            if isinstance(graph, dict) and f"{graph_prefix}/graph_sha256" not in explicit_paths:
                graph["graph_sha256"] = _canonical_hash(graph, "graph_sha256")
        if isinstance(loopbreak, dict) and f"{raw_prefix}/loopbreak/loopbreak_sha256" not in explicit_paths:
            loopbreak["loopbreak_sha256"] = _canonical_hash(loopbreak, "loopbreak_sha256")
        if f"{raw_prefix}/raw_exit_sha256" not in explicit_paths:
            raw_exit["raw_exit_sha256"] = _canonical_hash(raw_exit, "raw_exit_sha256")


def materialize(path: Path) -> Any:
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("fixture_schema") != MUTATION_SCHEMA:
        return payload
    base = payload.get("base")
    if not isinstance(base, str):
        raise ValueError(f"{rel(path)}: mutation fixture requires base")
    base_path = (ROOT / base).resolve()
    allowed_roots = (VALID_ROOT.resolve(), STATE_V2_VALID_ROOT.resolve())
    if not any(base_path.is_relative_to(root) for root in allowed_roots):
        raise ValueError(
            f"{rel(path)}: mutation base must remain under {rel(VALID_ROOT)} or {rel(STATE_V2_VALID_ROOT)}"
        )
    document = copy.deepcopy(read_json(base_path))
    operations = payload.get("operations", [])
    for operation in operations:
        _apply_operation(document, operation)
    document["fixture_id"] = path.stem
    _rehash_mutation(document, operations if isinstance(operations, list) else [])
    return document


def validate_path(path: Path, *, release_bearing: bool = False) -> ReductionState:
    return validate_lifecycle_record(materialize(path), release_bearing=release_bearing)


def pass_diagnostic(path: Path, state: ReductionState, payload: Any) -> dict[str, Any]:
    return {
        "artifact": rel(path),
        "B_LA": list(state.b_la),
        "B_MRP": list(state.b_mrp),
        "checker": "tools/check_mrp_recursion_lifecycle.py",
        "checker_id": CHECKER_ID,
        "cycle_count": len(state.cycle_order),
        "event_dag_edges": [list(edge) for edge in state.event_dag_edges],
        "lifecycle_partitions": {name: list(values) for name, values in state.lifecycle_partitions},
        "maximum_generation_depth": state.maximum_generation_depth,
        "reread_signature_history": [list(row) for row in state.reread_signature_history],
        "state_signature_sha256": state.state_signature_sha256,
        "status": "PASS",
        "terminal_disposition": state.terminal_disposition,
        "validation_profile": payload.get("validation_profile") if isinstance(payload, dict) else None,
        "promotion_eligible": payload.get("promotion_eligible") if isinstance(payload, dict) else False,
    }


def run_one(path: Path, *, explain: bool, release_bearing: bool = False) -> int:
    try:
        payload = materialize(path)
        state = validate_lifecycle_record(payload, release_bearing=release_bearing)
    except (IndexError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        state = validate_lifecycle_record({})
        state = ReductionState(
            state.b_la,
            state.b_mrp,
            state.cycle_order,
            state.cycle_exits,
            state.event_dag_edges,
            state.candidate_dispositions,
            state.lifecycle_partitions,
            state.live_candidate_ids,
            state.live_obligation_ids,
            state.terminal_disposition,
            state.maximum_generation_depth,
            state.reread_signature_history,
            state.state_signature_sha256,
            (Finding("fixture_or_json", str(exc)),),
        )
    if state.findings:
        diagnostic = finding_diagnostic(rel(path), state.findings[0])
        print(json.dumps(diagnostic, sort_keys=True, ensure_ascii=False) if explain else f"MRP recursion lifecycle: FAIL [{diagnostic['failure_subcode']}]: {diagnostic['message']}")
        return 1
    diagnostic = pass_diagnostic(path, state, payload)
    print(json.dumps(diagnostic, sort_keys=True, ensure_ascii=False) if explain else f"MRP recursion lifecycle: PASS ({rel(path)})")
    return 0


def _expectation_problems(fixture: Path, state: ReductionState) -> list[str]:
    problems: list[str] = []
    sidecar = fixture.with_suffix(".expectation.json")
    if not sidecar.is_file():
        return [f"{rel(fixture)}: missing same-stem expectation"]
    expectation = read_json(sidecar)
    if not isinstance(expectation, dict):
        return [f"{rel(sidecar)}: expectation must be an object"]
    missing = sorted(EXPECTATION_REQUIRED - set(expectation))
    extra = sorted(set(expectation) - EXPECTATION_ALLOWED)
    if missing:
        problems.append(f"{rel(sidecar)}: missing required fields {missing}")
    if extra:
        problems.append(f"{rel(sidecar)}: unknown fields {extra}")
    if expectation.get("schema") != EXPECTATION_SCHEMA:
        problems.append(f"{rel(sidecar)}: wrong expectation schema")
    if expectation.get("fixture") != fixture.name:
        problems.append(f"{rel(sidecar)}: fixture name mismatch")
    if expectation.get("kind") != "invalid-single-signature":
        problems.append(f"{rel(sidecar)}: active lifecycle negatives must be invalid-single-signature")
    if not state.findings:
        problems.append(f"{rel(fixture)}: invalid fixture survived")
        return problems
    diagnostic = finding_diagnostic(rel(fixture), state.findings[0])
    expected_pairs = {
        "expected_checker_id": diagnostic["checker_id"],
        "expected_exit_category": diagnostic["exit_category"],
        "expected_exit_code": diagnostic["exit_code"],
        "expected_earliest_stage": diagnostic["earliest_stage"],
        "expected_failure_class": diagnostic["failure_class"],
        "expected_failure_subcode": diagnostic["failure_subcode"],
        "expected_downstream_invalidated": diagnostic["downstream_invalidated"],
    }
    for key, observed in expected_pairs.items():
        if expectation.get(key) != observed:
            problems.append(f"{rel(sidecar)}: {key} expected {observed!r}, got {expectation.get(key)!r}")
    rendered = json.dumps(diagnostic, sort_keys=True, ensure_ascii=False)
    for marker in expectation.get("required_diagnostic_markers", []):
        if marker not in rendered:
            problems.append(f"{rel(fixture)}: required diagnostic marker {marker!r} absent")
    if expectation.get("forbidden_artifacts") != FORBIDDEN_ARTIFACTS:
        problems.append(f"{rel(sidecar)}: forbidden_artifacts must equal {FORBIDDEN_ARTIFACTS!r}")
    for artifact in expectation.get("forbidden_artifacts", []):
        if (ROOT / artifact).exists():
            problems.append(f"{rel(fixture)}: forbidden artifact escaped: {artifact}")
    return problems


def fixture_suite(*, emit: bool = True) -> tuple[int, int, list[str]]:
    valid = sorted(VALID_ROOT.glob("*.json"))
    invalid = sorted(path for path in INVALID_ROOT.glob("*.json") if not path.name.endswith(".expectation.json"))
    problems: list[str] = []
    for path in valid:
        state = validate_path(path)
        if state.findings:
            first = state.findings[0]
            problems.append(f"{rel(path)}: [{first.subcode}] {first.message}")
    for path in invalid:
        state = validate_path(path)
        problems.extend(_expectation_problems(path, state))
    orphan_sidecars = sorted(
        sidecar for sidecar in INVALID_ROOT.glob("*.expectation.json")
        if not sidecar.with_name(read_json(sidecar).get("fixture", "")).is_file()
    )
    problems.extend(f"{rel(sidecar)}: expectation references missing fixture" for sidecar in orphan_sidecars)
    if emit:
        if problems:
            for problem in problems:
                print(f"FAIL: {problem}")
            print(f"MRP recursion lifecycle fixture suite: FAIL ({len(problems)} problem(s))")
        else:
            print(f"MRP recursion lifecycle fixture suite: PASS ({len(valid)} valid, {len(invalid)} invalid)")
    return len(valid), len(invalid), problems


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _capacity_record(*, generated_depth: int = 0, baseline_width: int = 1) -> dict[str, Any]:
    if generated_depth and baseline_width != 1:
        raise ValueError("capacity dimensions are exercised independently")
    cycle_count = generated_depth + 1 if generated_depth else baseline_width
    cycles: list[dict[str, Any]] = []
    event_dag_edges: list[list[str]] = []
    for offset in range(cycle_count):
        number = offset + 1
        cycle_id = f"C{number}"
        burden_id = f"B{number}"
        has_next = number < cycle_count
        is_generated = generated_depth > 0 and number > 1
        candidate = None
        if has_next:
            candidate = {
                "candidate_event_id": f"CE-{cycle_id}-K{number}-1",
                "candidate_id": f"K{number}",
                "previous_candidate_event_id": None,
                "event_index": offset * 100 + 50,
                "kind": "generated_instantiation" if generated_depth else "held_activation",
                "disposition": "instantiate_generated" if generated_depth else "activate_held",
                "target_burden_id": f"B{number + 1}",
                "next_cycle_id": f"C{number + 1}",
                "basis_refs": ["Observed eligibility preserves ordered lifecycle custody."],
                "gate": None,
                "next_action": f"Execute C{number + 1}.",
            }
            event_dag_edges.append([cycle_id, f"C{number + 1}"])
        noetic_graph: dict[str, Any] = {"nodes": [], "edges": []}
        noetic_graph["graph_sha256"] = _canonical_hash(noetic_graph, "graph_sha256")
        event: dict[str, Any] = {
            "event_id": f"E{number}",
            "event_index": offset * 100 + 90,
            "exit_disposition": "RECURSE" if has_next else "STOP",
            "candidate_events": [candidate] if candidate else [],
            "field_diagnostics": [],
            "noetic_dependency_graph": noetic_graph,
            "no_new_resultant": None,
            "loopbreak": None,
            "resource_exhaustion": None,
        }
        if not has_next:
            event["no_new_resultant"] = {
                "observed": True,
                "live_obligation_ids": [],
                "unresolved_candidate_ids": [],
            }
        event["raw_exit_sha256"] = _canonical_hash(event, "raw_exit_sha256")
        cycles.append(
            {
                "cycle_id": cycle_id,
                "burden_id": burden_id,
                "origin": "B_MRP" if is_generated else "B_LA",
                "generation_depth": offset if generated_depth else 0,
                "parent_cycle_id": f"C{number - 1}" if is_generated else None,
                "route": {"record_id": f"S03-{cycle_id}", "sha256": _sha(f"route-{cycle_id}"), "target_burden_id": burden_id},
                "operation": {"record_id": f"S04-{cycle_id}", "sha256": _sha(f"operation-{cycle_id}"), "performed": True, "local_delta": {"state": f"{burden_id}-landable"}},
                "land": {"status": "landed", "event_index": offset * 100 + 40},
                "reread": {"record_id": f"S05-{cycle_id}", "sha256": _sha(f"reread-{cycle_id}"), "raw_exit": event},
                "lifecycle_status": "landed",
                "terminal_state": "landed",
            }
        )
    resource_policy: dict[str, Any] = {
        "policy_id": "runtime-budget-v1",
        "semantic_depth_cap": None,
        "on_exhaustion": "PARTIAL",
    }
    resource_policy["policy_sha256"] = _canonical_hash(resource_policy, "policy_sha256")
    return {
        "schema": "daee-mrp-recursion-lifecycle-fixture-v1",
        "fixture_id": f"capacity-d{generated_depth}-w{baseline_width}",
        "validation_profile": "current-a07-v2",
        "promotion_eligible": True,
        "trace_id": f"TRACE-capacity-d{generated_depth}-w{baseline_width}",
        "predecessor_trace_id": None,
        "event_dag_edges": event_dag_edges,
        "resource_policy": resource_policy,
        "burden_cycles": cycles,
        "non_claims": ["Finite capacity observation only."],
    }


def self_test() -> int:
    valid_count, invalid_count, problems = fixture_suite(emit=True)
    if problems:
        return 1
    depth_state = validate_lifecycle_record(_capacity_record(generated_depth=12))
    width_state = validate_lifecycle_record(_capacity_record(baseline_width=21))
    if depth_state.findings or depth_state.maximum_generation_depth != 12:
        print(f"FAIL: depth capacity probe: {depth_state.findings!r}")
        return 1
    if width_state.findings or len(width_state.b_la) != 21:
        print(f"FAIL: width capacity probe: {width_state.findings!r}")
        return 1
    print(f"mutation/right-reason proof: PASS ({invalid_count} single-signature mutations, {valid_count} neighboring valid controls)")
    print("capacity probes: PASS (depth=12, width=21; observations are not semantic quotas)")
    print("MRP recursion lifecycle self-test: PASS")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?")
    parser.add_argument("--fixture")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--release-bearing", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    selected = args.fixture or args.artifact
    if selected:
        path = Path(selected)
        if not path.is_absolute():
            path = ROOT / path
        return run_one(path.resolve(), explain=args.explain, release_bearing=args.release_bearing)
    _valid, _invalid, problems = fixture_suite(emit=True)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
