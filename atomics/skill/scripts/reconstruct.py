#!/usr/bin/env python3
"""Validate whether a Level 3 route plan is reconstructible from features."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from level3_lib import (
    condition_satisfied,
    default_skill_root,
    feature_spans,
    load_trigger_matrix,
    read_json,
    rule_by_id,
    write_json,
)


def _conditions(rule: dict[str, Any]) -> list[str]:
    return [str(item) for item in rule.get("requires_any", [])] + [str(item) for item in rule.get("requires_all", [])]


def reconstruct(input_text: str, features: dict[str, Any], route_plan: dict[str, Any], skill_root: Path) -> dict[str, Any]:
    del input_text  # Route reconstruction uses hashes and spans; no free-form rerouting.
    rules = rule_by_id(load_trigger_matrix(skill_root))
    ids = {str(item) for item in features.get("feature_ids", [])}
    spans = feature_spans(features)

    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    if not route_plan.get("live_burden") or route_plan.get("live_burden") == "ambiguous noetic burden":
        errors.append("live burden not recoverable from route plan")

    first_live = route_plan.get("first_live", [])
    if not first_live:
        errors.append("selected TTP cannot be recovered: no first_live owner")

    for item in first_live:
        owner_id = str(item.get("id", ""))
        rule = rules.get(owner_id)
        if not rule:
            errors.append(f"{owner_id}: no trigger rule available")
            continue
        requires_all = [str(value) for value in rule.get("requires_all", [])]
        requires_any = [str(value) for value in rule.get("requires_any", [])]
        missing_all = [value for value in requires_all if not condition_satisfied(value, ids)]
        any_hits = [value for value in requires_any if condition_satisfied(value, ids)]
        if missing_all:
            errors.append(f"{owner_id}: missing required feature(s): {', '.join(missing_all)}")
        if requires_any and not any_hits:
            errors.append(f"{owner_id}: no requires_any feature present")
        supporting = [value for value in _conditions(rule) if value in ids]
        if not any(spans.get(value) for value in supporting):
            errors.append(f"{owner_id}: trigger has no input-span support")
        expected_land = [str(value) for value in rule.get("land_requires", [])]
        actual_land = []
        for land in route_plan.get("land_requirements", []):
            if str(land.get("owner")) == owner_id:
                actual_land = [str(value) for value in land.get("requires", [])]
        if expected_land != actual_land:
            errors.append(f"{owner_id}: land_requires mismatch")
        else:
            notes.append(f"{owner_id}: selected from {supporting}; Land(B) requirements recoverable")

    for item in route_plan.get("held", []):
        owner_id = str(item.get("id", ""))
        reason = str(item.get("reason", ""))
        if reason != "blocked_by":
            warnings.append(f"{owner_id}: held alternative lacks blocked_by reason")
        if not item.get("by"):
            warnings.append(f"{owner_id}: held alternative missing blocker")

    for item in route_plan.get("deferred", []):
        owner_id = str(item.get("id", ""))
        reason = str(item.get("reason", ""))
        if reason not in {"yields_to", "lower_priority_after_first_live"}:
            warnings.append(f"{owner_id}: deferred alternative has weak reason: {reason}")

    queue = route_plan.get("continuation_queue", [])
    for entry in queue:
        entry_id = str(entry.get("id", "continuation"))
        if not entry.get("input_spans"):
            errors.append(f"{entry_id}: continuation entry has no input-span anchor")
        if not entry.get("release_conditions"):
            errors.append(f"{entry_id}: continuation entry has no release condition")
        if not entry.get("reread_required"):
            errors.append(f"{entry_id}: continuation entry does not require state re-read")
        for owner in entry.get("owners", []):
            owner_id = str(owner.get("id", ""))
            rule = rules.get(owner_id)
            if not rule:
                errors.append(f"{entry_id}/{owner_id}: no trigger rule available")
                continue
            supporting = [value for value in _conditions(rule) if value in ids]
            if not any(spans.get(value) for value in supporting):
                errors.append(f"{entry_id}/{owner_id}: continuation trigger has no input-span support")
            expected_land = [str(value) for value in rule.get("land_requires", [])]
            actual_land = []
            for land in entry.get("land_requirements", []):
                if str(land.get("owner")) == owner_id:
                    actual_land = [str(value) for value in land.get("requires", [])]
            if expected_land != actual_land:
                errors.append(f"{entry_id}/{owner_id}: continuation land_requires mismatch")
            else:
                notes.append(f"{entry_id}/{owner_id}: continuation recoverable from {supporting}")

    if queue and not route_plan.get("closure_gate"):
        errors.append("continuation queue present without closure gate")

    if route_plan.get("governance_verdict") not in {"STOP", "HOLD", "RECURSE", "PARTIAL"}:
        errors.append("governance verdict not recoverable")

    fidelity = "fail" if errors else ("partial" if warnings else "pass")
    return {
        "reconstructor": "reconstruct.py",
        "reconstruction_fidelity": fidelity,
        "errors": errors,
        "warnings": warnings,
        "reconstructor_notes": notes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Level 3 route-plan reconstruction.")
    parser.add_argument("--input", required=True, help="Original input file.")
    parser.add_argument("--features", required=True, help="features.json path.")
    parser.add_argument("--route-plan", required=True, help="route_plan.json path.")
    parser.add_argument("--output", help="reconstruction.json path.")
    parser.add_argument("--skill-root", default=str(default_skill_root()), help="Skill package root.")
    args = parser.parse_args(argv)

    paths = [Path(args.input), Path(args.features), Path(args.route_plan)]
    for path in paths:
        if not path.is_file():
            print(f"reconstruct: missing file: {path}", file=sys.stderr)
            return 2
    verdict = reconstruct(
        paths[0].read_text(encoding="utf-8"),
        read_json(paths[1]),
        read_json(paths[2]),
        Path(args.skill_root),
    )
    if args.output:
        write_json(Path(args.output), verdict)
    else:
        print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0 if verdict["reconstruction_fidelity"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
