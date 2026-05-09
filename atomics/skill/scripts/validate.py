#!/usr/bin/env python3
"""Validate Level 3 route-plan integrity and ontological licensing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from level3_lib import (
    default_skill_root,
    load_catalogue,
    load_ontology,
    load_trigger_matrix,
    owner_by_id,
    read_json,
    rule_by_id,
    write_json,
)


def validate(features: dict[str, Any], route_plan: dict[str, Any], skill_root: Path) -> dict[str, Any]:
    catalogue = load_catalogue(skill_root)
    trigger_matrix = load_trigger_matrix(skill_root)
    ontology = load_ontology(skill_root)
    owners = owner_by_id(catalogue)
    rules = rule_by_id(trigger_matrix)

    errors: list[str] = []
    warnings: list[str] = []

    prefixes = [str(item) for item in ontology.get("licensed_feature_prefixes", [])]
    for feature_id in route_plan.get("feature_ids", []):
        if not any(str(feature_id).startswith(prefix) for prefix in prefixes):
            errors.append(f"unlicensed feature prefix: {feature_id}")

    for section_name in ("first_live", "held", "deferred", "candidate_ttps"):
        for item in route_plan.get(section_name, []):
            owner_id = str(item.get("id", ""))
            if owner_id not in owners:
                errors.append(f"{section_name}: owner absent from Level 3 pilot catalogue: {owner_id}")
            if owner_id not in rules:
                errors.append(f"{section_name}: owner absent from trigger matrix: {owner_id}")
            governance = str(item.get("governance_class", ""))
            if governance and governance not in ontology.get("licensed_governance_classes", []):
                errors.append(f"{section_name}: unlicensed governance class for {owner_id}: {governance}")

    if not route_plan.get("first_live"):
        errors.append("route_plan has no first_live owner")

    route_owner_ids = [str(item.get("id")) for item in route_plan.get("first_live", [])]
    for queue_entry in route_plan.get("continuation_queue", []):
        if not queue_entry.get("owners"):
            errors.append(f"{queue_entry.get('id', 'continuation')}: empty continuation owners")
        if not queue_entry.get("input_spans"):
            errors.append(f"{queue_entry.get('id', 'continuation')}: missing input spans")
        if not queue_entry.get("release_conditions"):
            errors.append(f"{queue_entry.get('id', 'continuation')}: missing release conditions")
        if not queue_entry.get("reread_required"):
            errors.append(f"{queue_entry.get('id', 'continuation')}: reread_required is not true")
        for item in queue_entry.get("owners", []):
            owner_id = str(item.get("id", ""))
            route_owner_ids.append(owner_id)
            if owner_id not in owners:
                errors.append(f"{queue_entry.get('id', 'continuation')}: owner absent from Level 3 pilot catalogue: {owner_id}")
            if owner_id not in rules:
                errors.append(f"{queue_entry.get('id', 'continuation')}: owner absent from trigger matrix: {owner_id}")
            governance = str(item.get("governance_class", ""))
            if governance and governance not in ontology.get("licensed_governance_classes", []):
                errors.append(f"{queue_entry.get('id', 'continuation')}: unlicensed governance class for {owner_id}: {governance}")

    for land in route_plan.get("land_requirements", []):
        owner_id = str(land.get("owner", ""))
        if owner_id not in route_owner_ids:
            errors.append(f"land requirement references non-first-live owner: {owner_id}")
        if not land.get("requires"):
            errors.append(f"land requirement empty for {owner_id}")

    for queue_entry in route_plan.get("continuation_queue", []):
        for land in queue_entry.get("land_requirements", []):
            owner_id = str(land.get("owner", ""))
            if owner_id not in route_owner_ids:
                errors.append(f"{queue_entry.get('id', 'continuation')}: land requirement references unknown owner: {owner_id}")
            if not land.get("requires"):
                errors.append(f"{queue_entry.get('id', 'continuation')}: land requirement empty for {owner_id}")

    verdict = str(route_plan.get("governance_verdict", ""))
    if verdict not in ontology.get("licensed_verdicts", []):
        errors.append(f"unlicensed governance verdict: {verdict}")

    if features.get("input_sha256") != route_plan.get("input_sha256"):
        errors.append("input_sha256 mismatch between features and route_plan")

    fidelity = "fail" if errors else ("partial" if warnings else "pass")
    return {
        "validator": "validate.py",
        "validation_fidelity": fidelity,
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Level 3 route plan.")
    parser.add_argument("--features", required=True, help="features.json path.")
    parser.add_argument("--route-plan", required=True, help="route_plan.json path.")
    parser.add_argument("--output", help="validation.json path.")
    parser.add_argument("--skill-root", default=str(default_skill_root()), help="Skill package root.")
    args = parser.parse_args(argv)

    features_path = Path(args.features)
    route_path = Path(args.route_plan)
    if not features_path.is_file():
        print(f"validate: features missing: {features_path}", file=sys.stderr)
        return 2
    if not route_path.is_file():
        print(f"validate: route plan missing: {route_path}", file=sys.stderr)
        return 2
    verdict = validate(read_json(features_path), read_json(route_path), Path(args.skill_root))
    if args.output:
        write_json(Path(args.output), verdict)
    else:
        print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0 if verdict["validation_fidelity"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
