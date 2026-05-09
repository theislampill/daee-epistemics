#!/usr/bin/env python3
"""Deterministic Level 3 router.

Given features.json, trigger-matrix.json, and routing-precedence.yaml, this
module produces the same route_plan.json every time. It performs no LLM calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from level3_lib import (
    LEVEL3_VERSION,
    condition_satisfied,
    default_skill_root,
    derive_live_burden,
    feature_spans,
    governance_verdict,
    load_routing_precedence,
    load_trigger_matrix,
    owner_ids,
    precedence_index,
    read_json,
    sha256_json,
    write_json,
)


def _rule_satisfied(rule: dict[str, Any], feature_ids: set[str]) -> tuple[bool, list[str], list[str]]:
    requires_all = [str(item) for item in rule.get("requires_all", [])]
    requires_any = [str(item) for item in rule.get("requires_any", [])]
    missing_all = [item for item in requires_all if not condition_satisfied(item, feature_ids)]
    any_hits = [item for item in requires_any if condition_satisfied(item, feature_ids)]
    if missing_all:
        return False, any_hits, missing_all
    if requires_any and not any_hits:
        return False, any_hits, []
    return True, any_hits + [item for item in requires_all if item in feature_ids], []


CONTINUATION_ORDER = {
    "do-second-loop": 10,
    "V2-reconstituting-reason": 20,
    "M8-reductio": 30,
    "P1-fitrah-restoration": 40,
}


HARD_HOLD_BLOCKERS = {
    "P7-restoration-stops",
    "M4-grief-register",
    "mushabara-fasida",
    "M5-deformation-triage",
    "V9-necessary-knowledge-priority",
}

OPTIONAL_RULE_TRACE_FIELDS = (
    "canonical_deformation_code",
    "parent_deformation_code",
    "source_marker",
    "marker_kind",
    "aliases",
    "pressure_dimensions",
)


def _spans_for(item: dict[str, Any], spans: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for feature_id in item.get("triggered_by", []):
        records.extend(spans.get(str(feature_id), []))
    unique: dict[tuple[int, int, str], dict[str, Any]] = {}
    for record in records:
        unique[(int(record.get("start", 0)), int(record.get("end", 0)), str(record.get("feature_id", "")))] = record
    return sorted(unique.values(), key=lambda value: (int(value.get("start", 0)), int(value.get("end", 0)), str(value.get("feature_id", ""))))[:8]


def _continuation_name(owner_id: str) -> str:
    names = {
        "do-second-loop": "hujjah/accountability and coercive-guidance correction",
        "V2-reconstituting-reason": "reason-repair and evidential burden reconstruction",
        "M8-reductio": "source-worldview consequence trace",
        "P1-fitrah-restoration": "mercy and worship-worthiness restoration reread",
    }
    return names.get(owner_id, f"{owner_id} continuation")


def _continuation_release(owner_id: str, first_live_ids: list[str]) -> list[str]:
    upstream = ", ".join(first_live_ids) if first_live_ids else "the prior burden"
    return [
        f"after Land(B1) shows the first-live burden ({upstream}) has landed with owner-floor result",
        "after R(H,Delta) rechecks this owner as input-anchored and no register/source/semantic gate blocks release",
    ]


def _queue_candidate(item: dict[str, Any], first_live_ids: list[str]) -> bool:
    owner_id = str(item.get("id"))
    if owner_id not in CONTINUATION_ORDER:
        return False
    if not item.get("triggered_by"):
        return False
    if any(owner in HARD_HOLD_BLOCKERS for owner in first_live_ids):
        return False
    return bool(first_live_ids)


def _make_burden_step(
    *,
    step_id: str,
    name: str,
    owners: list[dict[str, Any]],
    spans: dict[str, list[dict[str, Any]]],
    relation: str,
    release_conditions: list[str],
    continuation_queue_remaining: list[str] | None = None,
    next_required_action: str = "execute-if-licensed",
    checker_status: str = "not-run",
    landed: bool = False,
    hold_or_partial_reason: str | None = None,
    state_delta: str = "pending",
) -> dict[str, Any]:
    step_owner_ids = owner_ids(owners)
    input_spans = [span for owner in owners for span in _spans_for(owner, spans)]
    return {
        "id": step_id,
        "name": name,
        "relation": relation,
        "owners": owners,
        "owner_ids": step_owner_ids,
        "input_spans": input_spans,
        "release_conditions": release_conditions,
        "land_requirements": [
            {
                "owner": str(owner.get("id")),
                "requires": owner.get("land_requires", []),
                "pressure_dimensions": owner.get("pressure_dimensions", []),
            }
            for owner in owners
        ],
        "reread_required": True,
        "state_envelope": {
            "current_burden_id": step_id,
            "owner_ids": step_owner_ids,
            "input_span_refs": input_spans,
            "landed": landed,
            "checker_status": checker_status,
            "continuation_queue_remaining": continuation_queue_remaining or [],
            "hold_or_partial_reason": hold_or_partial_reason,
            "next_required_action": next_required_action,
            "state_delta": state_delta,
            "reread_required": True,
        },
    }


def compute_route(features: dict[str, Any], skill_root: Path) -> dict[str, Any]:
    trigger_matrix = load_trigger_matrix(skill_root)
    precedence = load_routing_precedence(skill_root)
    feature_ids = {str(item) for item in features.get("feature_ids", [])}
    spans = feature_spans(features)

    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for rule in trigger_matrix.get("rules", []):
        ok, triggered_by, missing = _rule_satisfied(rule, feature_ids)
        entry = {
            "id": str(rule["id"]),
            "priority": int(rule.get("priority", 0)),
            "governance_class": str(rule.get("governance_class", "routes")),
            "triggered_by": sorted(set(triggered_by)),
            "requires_any": rule.get("requires_any", []),
            "requires_all": rule.get("requires_all", []),
            "land_requires": rule.get("land_requires", []),
        }
        for field in OPTIONAL_RULE_TRACE_FIELDS:
            if field in rule:
                entry[field] = rule[field]
        if ok:
            candidates.append(entry)
        else:
            entry["reason"] = "requires_not_satisfied"
            if missing:
                entry["missing"] = missing
            rejected.append(entry)

    candidates = sorted(
        candidates,
        key=lambda item: (-int(item["priority"]), precedence_index(precedence, str(item["id"])), str(item["id"])),
    )
    candidate_ids = {str(item["id"]) for item in candidates}

    rule_lookup = {str(rule["id"]): rule for rule in trigger_matrix.get("rules", [])}
    blocked_ids: dict[str, str] = {}
    for candidate in candidates:
        rule = rule_lookup[str(candidate["id"])]
        for blocked in rule.get("blocks", []):
            if str(blocked) in candidate_ids:
                blocked_ids.setdefault(str(blocked), str(candidate["id"]))

    yielded_ids: dict[str, str] = {}
    for candidate in candidates:
        candidate_id = str(candidate["id"])
        rule = rule_lookup[candidate_id]
        for superior in rule.get("yields_to", []):
            if str(superior) in candidate_ids and candidate_id not in blocked_ids:
                yielded_ids.setdefault(candidate_id, str(superior))

    unsuppressed = [
        item for item in candidates
        if str(item["id"]) not in blocked_ids and str(item["id"]) not in yielded_ids
    ]
    top_priority = max((int(item["priority"]) for item in unsuppressed), default=None)

    first_live: list[dict[str, Any]] = []
    held: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    for item in candidates:
        owner_id = str(item["id"])
        if owner_id in blocked_ids:
            blocked = dict(item)
            blocked["reason"] = "blocked_by"
            blocked["by"] = blocked_ids[owner_id]
            held.append(blocked)
        elif owner_id in yielded_ids:
            yielded = dict(item)
            yielded["reason"] = "yields_to"
            yielded["to"] = yielded_ids[owner_id]
            deferred.append(yielded)
        elif top_priority is not None and int(item["priority"]) == top_priority:
            first_live.append(item)
        else:
            lower = dict(item)
            lower["reason"] = "lower_priority_after_first_live"
            lower["to"] = owner_ids(first_live)
            deferred.append(lower)

    first_live_ids = owner_ids(first_live)
    continuation_source = [dict(item) for item in held + deferred if _queue_candidate(item, first_live_ids)]
    continuation_source = sorted(
        continuation_source,
        key=lambda item: (
            CONTINUATION_ORDER.get(str(item.get("id")), 999),
            -int(item.get("priority", 0)),
            str(item.get("id")),
        ),
    )
    continuation_queue: list[dict[str, Any]] = []
    for index, item in enumerate(continuation_source, start=2):
        remaining = [f"B{next_index}" for next_index in range(index + 1, len(continuation_source) + 2)]
        continuation_queue.append(
            _make_burden_step(
                step_id=f"B{index}",
                name=_continuation_name(str(item.get("id"))),
                owners=[item],
                spans=spans,
                relation="same-input continuation after refreshed state",
                release_conditions=_continuation_release(str(item.get("id")), first_live_ids),
                continuation_queue_remaining=remaining,
                next_required_action="execute-if-still-licensed-after-reread",
            )
        )

    land_requirements: list[dict[str, Any]] = [
        {
            "owner": str(item["id"]),
            "requires": item.get("land_requires", []),
            "pressure_dimensions": item.get("pressure_dimensions", []),
        }
        for item in first_live
    ]
    verdict = governance_verdict([str(item.get("governance_class", "routes")) for item in first_live], precedence)
    if continuation_queue and verdict != "PARTIAL":
        verdict = "RECURSE"

    route_plan: dict[str, Any] = {
        "level3_version": LEVEL3_VERSION,
        "router": "route.py",
        "routing_claim": "deterministic-given-features",
        "feature_hash": sha256_json(features.get("feature_ids", [])),
        "input_sha256": features.get("input_sha256"),
        "feature_ids": sorted(feature_ids),
        "live_burden": derive_live_burden(feature_ids),
        "first_live_burden": _make_burden_step(
            step_id="B1",
            name=derive_live_burden(feature_ids),
            owners=first_live,
            spans=spans,
            relation="first-live burden",
            release_conditions=["selected by deterministic route precedence from span-backed features"],
            continuation_queue_remaining=[str(entry.get("id")) for entry in continuation_queue],
            next_required_action="execute-first-live-then-reread",
        ),
        "candidate_ttps": candidates,
        "first_live": first_live,
        "held": held,
        "deferred": deferred,
        "continuation_queue": continuation_queue,
        "closure_gate": {
            "condition": "close only after every continuation_queue entry is either landed, explicitly held by refreshed state, or marked PARTIAL with the next live burden",
            "reread_required_after_each_burden": True,
            "padding_guard": "every continuation entry must be justified by its input_spans; unanchored burdens are framework dumping",
        },
        "rejected": rejected,
        "land_requirements": land_requirements,
        "governance_verdict": verdict,
        "execution_constraints": [
            "execute first_live owners first",
            "continuation_queue is planned, not unconditional; after each Land(B) and R(H,Delta), continue only when the next entry remains input-anchored and licensed",
            "if refreshed state no longer licenses a queued burden, mark HOLD, SKIP, PARTIAL, or bounded-reroute need with the state-delta reason",
            "do not execute held or deferred owners outside first_live or continuation_queue",
            "emit Layer A compact diagnostic control state and Layer B governed response for every executed burden",
            "render visible owner-floor Target -> Operation -> Result evidence",
            "render B.s -> Land(B) -> R(H,Delta) for every burden entry",
            "preserve burden-local structural attachment; do not flatten owners, checker markers, or state decisions into global blobs",
            "carry state_envelope fields across route_plan, validation, execution check, and retry output",
            "close only if R(H,Delta) names no remaining input-anchored burdens",
        ],
    }
    route_plan["route_plan_sha256"] = sha256_json(route_plan)
    return route_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute a deterministic Level 3 route plan.")
    parser.add_argument("--features", required=True, help="features.json path.")
    parser.add_argument("--output", help="route_plan.json path.")
    parser.add_argument("--skill-root", default=str(default_skill_root()), help="Skill package root.")
    args = parser.parse_args(argv)

    features_path = Path(args.features)
    if not features_path.is_file():
        print(f"route: features missing: {features_path}", file=sys.stderr)
        return 2
    route_plan = compute_route(read_json(features_path), Path(args.skill_root))
    if args.output:
        write_json(Path(args.output), route_plan)
    else:
        print(json.dumps(route_plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
