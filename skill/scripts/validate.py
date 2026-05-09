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
    feature_spans,
    load_catalogue,
    load_ontology,
    load_trigger_matrix,
    owner_by_id,
    owner_ids,
    read_json,
    rule_by_id,
    sha256_json,
    write_json,
)


ROUTE_PLAN_TOP_LEVEL = {
    "level3_version",
    "router",
    "routing_claim",
    "feature_hash",
    "input_sha256",
    "feature_ids",
    "live_burden",
    "first_live_burden",
    "candidate_ttps",
    "first_live",
    "held",
    "deferred",
    "continuation_queue",
    "closure_gate",
    "rejected",
    "land_requirements",
    "governance_verdict",
    "execution_constraints",
    "route_plan_sha256",
}

OWNER_ITEM_KEYS = {
    "id",
    "priority",
    "governance_class",
    "triggered_by",
    "requires_any",
    "requires_all",
    "land_requires",
    "reason",
    "missing",
    "by",
    "to",
    "canonical_deformation_code",
    "parent_deformation_code",
    "source_marker",
    "marker_kind",
    "aliases",
    "source_basis_role",
    "noetic_categories",
    "fallback_reason_code",
}

BURDEN_STEP_KEYS = {
    "id",
    "name",
    "relation",
    "owners",
    "owner_ids",
    "input_spans",
    "release_conditions",
    "land_requirements",
    "reread_required",
    "state_envelope",
}

SPAN_KEYS = {"feature_id", "text", "start", "end", "source"}
LAND_KEYS = {"owner", "requires"}
STATE_ENVELOPE_KEYS = {
    "current_burden_id",
    "owner_ids",
    "input_span_refs",
    "landed",
    "checker_status",
    "continuation_queue_remaining",
    "hold_or_partial_reason",
    "next_required_action",
    "state_delta",
    "reread_required",
}
CHECKER_STATUSES = {"not-run", "pass", "partial", "fail", "held", "skipped", "blocked"}


def _expect_keys(label: str, payload: dict[str, Any], allowed: set[str], errors: list[str]) -> None:
    extra = sorted(set(payload) - allowed)
    if extra:
        errors.append(f"{label}: unknown key(s): {', '.join(extra)}")


def _string_list(value: Any, label: str, errors: list[str], *, non_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return []
    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or (non_empty and not item.strip()):
            errors.append(f"{label}[{index}] must be a non-empty string")
            continue
        items.append(item)
    return items


def _duplicate_values(items: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for item in items:
        if item in seen and item not in duplicates:
            duplicates.append(item)
        seen.add(item)
    return duplicates


def _span_index(features: dict[str, Any]) -> set[tuple[str, int, int, str]]:
    index: set[tuple[str, int, int, str]] = set()
    for feature_id, spans in feature_spans(features).items():
        for span in spans:
            try:
                start = int(span.get("start"))
                end = int(span.get("end"))
            except (TypeError, ValueError):
                continue
            index.add((str(feature_id), start, end, str(span.get("text", ""))))
    return index


def _validate_span(
    label: str,
    span: Any,
    *,
    feature_ids: set[str],
    feature_span_index: set[tuple[str, int, int, str]],
    errors: list[str],
) -> None:
    if not isinstance(span, dict):
        errors.append(f"{label}: input span must be object")
        return
    _expect_keys(label, span, SPAN_KEYS, errors)
    feature_id = span.get("feature_id")
    if not isinstance(feature_id, str) or not feature_id:
        errors.append(f"{label}: span feature_id must be a non-empty string")
        return
    if feature_id not in feature_ids:
        errors.append(f"{label}: span feature_id not present in route feature_ids: {feature_id}")
    try:
        start = int(span.get("start"))
        end = int(span.get("end"))
    except (TypeError, ValueError):
        errors.append(f"{label}: span start/end must be integers")
        return
    if start < 0 or end <= start:
        errors.append(f"{label}: invalid span range {start}:{end}")
    text = span.get("text")
    if not isinstance(text, str) or not text:
        errors.append(f"{label}: span text must be a non-empty string")
        return
    if (feature_id, start, end, text) not in feature_span_index:
        errors.append(f"{label}: span does not match any extracted feature span: {feature_id}@{start}:{end}")


def _validate_owner_item(
    label: str,
    item: Any,
    *,
    owners: dict[str, dict[str, Any]],
    rules: dict[str, dict[str, Any]],
    ontology: dict[str, Any],
    errors: list[str],
) -> str:
    if not isinstance(item, dict):
        errors.append(f"{label}: owner item must be object")
        return ""
    _expect_keys(label, item, OWNER_ITEM_KEYS, errors)
    owner_id = str(item.get("id", ""))
    if not owner_id:
        errors.append(f"{label}: owner id missing")
        return ""
    if owner_id not in owners:
        errors.append(f"{label}: owner absent from Level 3 covered-scope catalogue: {owner_id}")
    if owner_id not in rules:
        errors.append(f"{label}: owner absent from trigger matrix: {owner_id}")
    governance = str(item.get("governance_class", ""))
    if governance and governance not in ontology.get("licensed_governance_classes", []):
        errors.append(f"{label}: unlicensed governance class for {owner_id}: {governance}")
    for field in ("triggered_by", "requires_any", "requires_all", "land_requires"):
        _string_list(item.get(field, []), f"{label}.{field}", errors)
    if "priority" in item and not isinstance(item.get("priority"), int):
        errors.append(f"{label}: priority must be integer")
    if "aliases" in item:
        _string_list(item.get("aliases"), f"{label}.aliases", errors, non_empty=True)
    return owner_id


def _validate_land_requirements(
    label: str,
    items: Any,
    *,
    route_owner_ids: set[str],
    errors: list[str],
) -> None:
    if not isinstance(items, list):
        errors.append(f"{label}: land_requirements must be an array")
        return
    for index, land in enumerate(items):
        item_label = f"{label}[{index}]"
        if not isinstance(land, dict):
            errors.append(f"{item_label}: land requirement must be object")
            continue
        _expect_keys(item_label, land, LAND_KEYS, errors)
        owner_id = str(land.get("owner", ""))
        if owner_id not in route_owner_ids:
            errors.append(f"{item_label}: land requirement references unknown route owner: {owner_id}")
        requires = _string_list(land.get("requires", []), f"{item_label}.requires", errors, non_empty=True)
        if not requires:
            errors.append(f"{item_label}: land requirement empty for {owner_id}")


def _validate_state_envelope(
    label: str,
    envelope: Any,
    *,
    step_id: str,
    step_owner_ids: list[str],
    step_input_spans: list[Any],
    feature_ids: set[str],
    feature_span_index: set[tuple[str, int, int, str]],
    errors: list[str],
) -> None:
    if not isinstance(envelope, dict):
        errors.append(f"{label}: state_envelope must be object")
        return
    _expect_keys(f"{label}.state_envelope", envelope, STATE_ENVELOPE_KEYS, errors)
    if envelope.get("current_burden_id") != step_id:
        errors.append(f"{label}.state_envelope.current_burden_id must equal {step_id}")
    envelope_owner_ids = _string_list(
        envelope.get("owner_ids", []),
        f"{label}.state_envelope.owner_ids",
        errors,
        non_empty=True,
    )
    if envelope_owner_ids != step_owner_ids:
        errors.append(f"{label}.state_envelope.owner_ids {envelope_owner_ids!r} != step owner_ids {step_owner_ids!r}")
    span_refs = envelope.get("input_span_refs")
    if not isinstance(span_refs, list):
        errors.append(f"{label}.state_envelope.input_span_refs must be an array")
    else:
        if span_refs != step_input_spans:
            errors.append(f"{label}.state_envelope.input_span_refs must mirror input_spans")
        for index, span in enumerate(span_refs):
            _validate_span(
                f"{label}.state_envelope.input_span_refs[{index}]",
                span,
                feature_ids=feature_ids,
                feature_span_index=feature_span_index,
                errors=errors,
            )
    if not isinstance(envelope.get("landed"), bool):
        errors.append(f"{label}.state_envelope.landed must be boolean")
    checker_status = envelope.get("checker_status")
    if checker_status not in CHECKER_STATUSES:
        errors.append(f"{label}.state_envelope.checker_status must be one of {sorted(CHECKER_STATUSES)}")
    _string_list(
        envelope.get("continuation_queue_remaining", []),
        f"{label}.state_envelope.continuation_queue_remaining",
        errors,
        non_empty=True,
    )
    reason = envelope.get("hold_or_partial_reason")
    if reason is not None and (not isinstance(reason, str) or not reason.strip()):
        errors.append(f"{label}.state_envelope.hold_or_partial_reason must be null or non-empty string")
    for field in ("next_required_action", "state_delta"):
        if not isinstance(envelope.get(field), str) or not envelope[field].strip():
            errors.append(f"{label}.state_envelope.{field} must be a non-empty string")
    if envelope.get("reread_required") is not True:
        errors.append(f"{label}.state_envelope.reread_required must be true")


def _validate_burden_step(
    label: str,
    step: Any,
    *,
    expected_id: str | None,
    owners: dict[str, dict[str, Any]],
    rules: dict[str, dict[str, Any]],
    ontology: dict[str, Any],
    feature_ids: set[str],
    feature_span_index: set[tuple[str, int, int, str]],
    errors: list[str],
) -> list[str]:
    if not isinstance(step, dict):
        errors.append(f"{label}: burden step must be object")
        return []
    _expect_keys(label, step, BURDEN_STEP_KEYS, errors)
    if expected_id and step.get("id") != expected_id:
        errors.append(f"{label}: id {step.get('id')!r} != expected {expected_id!r}")
    for field in ("id", "name", "relation"):
        if not isinstance(step.get(field), str) or not step[field].strip():
            errors.append(f"{label}: {field} must be a non-empty string")
    step_owner_ids: list[str] = []
    step_owners = step.get("owners")
    if not isinstance(step_owners, list) or not step_owners:
        errors.append(f"{label}: owners must be a non-empty array")
    else:
        for index, owner in enumerate(step_owners):
            owner_id = _validate_owner_item(
                f"{label}.owners[{index}]",
                owner,
                owners=owners,
                rules=rules,
                ontology=ontology,
                errors=errors,
            )
            if owner_id:
                step_owner_ids.append(owner_id)
    declared_owner_ids = _string_list(step.get("owner_ids", []), f"{label}.owner_ids", errors, non_empty=True)
    if declared_owner_ids != step_owner_ids:
        errors.append(f"{label}: owner_ids {declared_owner_ids!r} != owners ids {step_owner_ids!r}")
    spans = step.get("input_spans")
    step_input_spans: list[Any] = []
    if not isinstance(spans, list):
        errors.append(f"{label}: input_spans must be an array")
    else:
        step_input_spans = spans
        for index, span in enumerate(spans):
            _validate_span(
                f"{label}.input_spans[{index}]",
                span,
                feature_ids=feature_ids,
                feature_span_index=feature_span_index,
                errors=errors,
            )
    release_conditions = _string_list(step.get("release_conditions", []), f"{label}.release_conditions", errors, non_empty=True)
    if not release_conditions:
        errors.append(f"{label}: missing release conditions")
    if step.get("reread_required") is not True:
        errors.append(f"{label}: reread_required must be true")
    _validate_land_requirements(
        f"{label}.land_requirements",
        step.get("land_requirements", []),
        route_owner_ids=set(step_owner_ids),
        errors=errors,
    )
    _validate_state_envelope(
        label,
        step.get("state_envelope"),
        step_id=str(step.get("id", "")),
        step_owner_ids=step_owner_ids,
        step_input_spans=step_input_spans,
        feature_ids=feature_ids,
        feature_span_index=feature_span_index,
        errors=errors,
    )
    return step_owner_ids


def validate(features: dict[str, Any], route_plan: dict[str, Any], skill_root: Path) -> dict[str, Any]:
    catalogue = load_catalogue(skill_root)
    trigger_matrix = load_trigger_matrix(skill_root)
    ontology = load_ontology(skill_root)
    owners = owner_by_id(catalogue)
    rules = rule_by_id(trigger_matrix)

    errors: list[str] = []
    warnings: list[str] = []
    _expect_keys("route_plan", route_plan, ROUTE_PLAN_TOP_LEVEL, errors)
    for field in ROUTE_PLAN_TOP_LEVEL - {"route_plan_sha256"}:
        if field not in route_plan:
            errors.append(f"route_plan: missing required field {field}")

    route_hash = route_plan.get("route_plan_sha256")
    if not isinstance(route_hash, str) or not route_hash:
        errors.append("route_plan_sha256 missing or not string")
    else:
        unsigned = dict(route_plan)
        unsigned.pop("route_plan_sha256", None)
        if sha256_json(unsigned) != route_hash:
            errors.append("route_plan_sha256 mismatch")

    feature_ids_from_features = sorted(str(item) for item in features.get("feature_ids", []))
    feature_ids_from_route = route_plan.get("feature_ids", [])
    if feature_ids_from_route != feature_ids_from_features:
        errors.append(f"feature_ids mismatch: route {feature_ids_from_route!r} != features {feature_ids_from_features!r}")
    if route_plan.get("feature_hash") != sha256_json(features.get("feature_ids", [])):
        errors.append("feature_hash mismatch between features and route_plan")
    feature_id_set = set(feature_ids_from_features)
    feature_span_index = _span_index(features)

    if not isinstance(route_plan.get("execution_constraints"), list) or not all(
        isinstance(item, str) and item.strip() for item in route_plan.get("execution_constraints", [])
    ):
        errors.append("execution_constraints must be an array of non-empty strings")

    closure_gate = route_plan.get("closure_gate")
    if not isinstance(closure_gate, dict):
        errors.append("closure_gate must be object")
    else:
        closure_allowed = {"condition", "reread_required_after_each_burden", "padding_guard"}
        _expect_keys("closure_gate", closure_gate, closure_allowed, errors)
        for field in ("condition", "padding_guard"):
            if not isinstance(closure_gate.get(field), str) or not closure_gate[field].strip():
                errors.append(f"closure_gate.{field} must be a non-empty string")
        if closure_gate.get("reread_required_after_each_burden") is not True:
            errors.append("closure_gate.reread_required_after_each_burden must be true")

    prefixes = [str(item) for item in ontology.get("licensed_feature_prefixes", [])]
    for feature_id in route_plan.get("feature_ids", []):
        if not any(str(feature_id).startswith(prefix) for prefix in prefixes):
            errors.append(f"unlicensed feature prefix: {feature_id}")

    for section_name in ("first_live", "held", "deferred", "candidate_ttps"):
        section = route_plan.get(section_name, [])
        if not isinstance(section, list):
            errors.append(f"{section_name} must be an array")
            continue
        seen_section_ids: list[str] = []
        for index, item in enumerate(section):
            owner_id = _validate_owner_item(
                f"{section_name}[{index}]",
                item,
                owners=owners,
                rules=rules,
                ontology=ontology,
                errors=errors,
            )
            if owner_id:
                seen_section_ids.append(owner_id)
        duplicates = _duplicate_values(seen_section_ids)
        if duplicates:
            errors.append(f"{section_name}: duplicate owner id(s): {', '.join(duplicates)}")

    if not route_plan.get("first_live"):
        errors.append("route_plan has no first_live owner")

    route_owner_ids = [str(item.get("id")) for item in route_plan.get("first_live", [])]
    duplicates = _duplicate_values(route_owner_ids)
    if duplicates:
        errors.append("first_live duplicate owner id(s): " + ", ".join(duplicates))

    first_live_burden_owner_ids = _validate_burden_step(
        "first_live_burden",
        route_plan.get("first_live_burden"),
        expected_id="B1",
        owners=owners,
        rules=rules,
        ontology=ontology,
        feature_ids=feature_id_set,
        feature_span_index=feature_span_index,
        errors=errors,
    )
    if first_live_burden_owner_ids != route_owner_ids:
        errors.append(f"first_live_burden owners {first_live_burden_owner_ids!r} != first_live {route_owner_ids!r}")

    queue = route_plan.get("continuation_queue", [])
    if not isinstance(queue, list):
        errors.append("continuation_queue must be an array")
        queue = []
    for index, queue_entry in enumerate(queue, start=2):
        queue_ids = _validate_burden_step(
            f"continuation_queue[{index - 2}]",
            queue_entry,
            expected_id=f"B{index}",
            owners=owners,
            rules=rules,
            ontology=ontology,
            feature_ids=feature_id_set,
            feature_span_index=feature_span_index,
            errors=errors,
        )
        route_owner_ids.extend(queue_ids)

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
