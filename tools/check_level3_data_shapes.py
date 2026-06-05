#!/usr/bin/env python3
"""Validate Level 3 catalogue, trigger, precedence, and license data shapes."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from compiled_runtime_lib import fail_with_errors, parse_simple_yaml, repo_root


SHA_SCOPE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
OWNER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_'.-]*$")

CATALOGUE_KEYS = {"schema_version", "scope", "note", "owners"}
CATALOGUE_REQUIRED_KEYS = {"schema_version", "scope", "note", "owners"}
OWNER_KEYS = {
    "id",
    "module_class",
    "path",
    "owner_floor",
    "canonical_deformation_code",
    "parent_deformation_code",
    "source_marker",
    "marker_kind",
    "aliases",
}
OWNER_REQUIRED_KEYS = {"id", "module_class", "path", "owner_floor"}
OWNER_CLASSES = {"case-library", "tactic", "technique", "procedure", "diagnostic", "diagnostic-marker"}
TRIGGER_KEYS = {"schema_version", "scope", "note", "rules"}
TRIGGER_REQUIRED_KEYS = {"schema_version", "scope", "note", "rules"}
RULE_KEYS = {
    "id",
    "requires_any",
    "requires_all",
    "blocks",
    "yields_to",
    "priority",
    "land_requires",
    "governance_class",
    "canonical_deformation_code",
    "parent_deformation_code",
    "source_marker",
    "marker_kind",
    "aliases",
    "pressure_dimensions",
}
RULE_REQUIRED_KEYS = {
    "id",
    "requires_any",
    "requires_all",
    "blocks",
    "yields_to",
    "priority",
    "land_requires",
    "governance_class",
}
PRECEDENCE_KEYS = {"schema_version", "scope", "priority_order", "governance_order", "determinism_claim"}
PRECEDENCE_REQUIRED_KEYS = PRECEDENCE_KEYS
ONTOLOGY_KEYS = {
    "schema_version",
    "scope",
    "licensed_feature_prefixes",
    "licensed_governance_classes",
    "licensed_verdicts",
    "licensed_noetic_categories",
    "licensed_reason_roles",
    "licensed_source_worldview_roles",
    "licensed_fallback_reason_codes",
}
ONTOLOGY_REQUIRED_KEYS = ONTOLOGY_KEYS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml_dict(path: Path) -> dict[str, Any]:
    return parse_simple_yaml(path.read_text(encoding="utf-8"))


def unknown_keys(
    label: str,
    payload: dict[str, Any],
    allowed: set[str],
    *,
    required: set[str] | None = None,
) -> list[str]:
    extra = sorted(set(payload) - allowed)
    missing = sorted((required or allowed) - set(payload))
    errors: list[str] = []
    if extra:
        errors.append(f"{label}: unknown key(s): {', '.join(extra)}")
    if missing:
        errors.append(f"{label}: missing key(s): {', '.join(missing)}")
    return errors


def string_list(label: str, value: Any, *, allow_empty: bool = True) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if not isinstance(value, list):
        return [], [f"{label}: must be an array"]
    if not allow_empty and not value:
        errors.append(f"{label}: must not be empty")
    values: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{label}[{index}]: must be non-empty string")
            continue
        if item in seen:
            errors.append(f"{label}: duplicate value {item!r}")
        seen.add(item)
        values.append(item)
    return values, errors


def validate_catalogue(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, str], list[str]]:
    errors: list[str] = []
    payload = load_json(path)
    if not isinstance(payload, dict):
        return {}, {}, [f"{path}: must be JSON object"]
    errors.extend(unknown_keys(path.as_posix(), payload, CATALOGUE_KEYS, required=CATALOGUE_REQUIRED_KEYS))
    if payload.get("schema_version") not in {1, "1"}:
        errors.append(f"{path}: schema_version must be 1")
    scope = payload.get("scope")
    if not isinstance(scope, str) or not SHA_SCOPE_RE.fullmatch(scope):
        errors.append(f"{path}: scope must be a normalized string")
    owners = payload.get("owners")
    if not isinstance(owners, list) or not owners:
        return {}, {}, errors + [f"{path}: owners must be a non-empty array"]

    by_id: dict[str, dict[str, Any]] = {}
    aliases: dict[str, str] = {}
    for index, owner in enumerate(owners):
        label = f"{path.as_posix()}: owners[{index}]"
        if not isinstance(owner, dict):
            errors.append(f"{label}: must be object")
            continue
        errors.extend(unknown_keys(label, owner, OWNER_KEYS, required=OWNER_REQUIRED_KEYS))
        owner_id = owner.get("id")
        if not isinstance(owner_id, str) or not OWNER_ID_RE.fullmatch(owner_id):
            errors.append(f"{label}: invalid owner id {owner_id!r}")
            continue
        if owner_id in by_id:
            errors.append(f"{label}: duplicate owner id {owner_id}")
        by_id[owner_id] = owner
        if owner.get("module_class") not in OWNER_CLASSES:
            errors.append(f"{label}: invalid module_class {owner.get('module_class')!r}")
        path_value = owner.get("path")
        if not isinstance(path_value, str) or not path_value.startswith("references/"):
            errors.append(f"{label}: path must start with references/")
        if not isinstance(owner.get("owner_floor"), str) or not owner["owner_floor"].strip():
            errors.append(f"{label}: owner_floor must be non-empty string")
        owner_aliases, alias_errors = string_list(f"{label}.aliases", owner.get("aliases", []))
        errors.extend(alias_errors)
        source_marker = owner.get("source_marker")
        if isinstance(source_marker, str) and source_marker:
            owner_aliases.append(source_marker)
        for alias in owner_aliases:
            if alias == owner_id:
                errors.append(f"{label}: alias duplicates canonical id {owner_id}")
            elif alias in aliases and aliases[alias] != owner_id:
                errors.append(f"{label}: alias {alias!r} already maps to {aliases[alias]}")
            else:
                aliases[alias] = owner_id
    return by_id, aliases, errors


def resolve_owner(value: str, owner_ids: set[str], aliases: dict[str, str]) -> str | None:
    if value in owner_ids:
        return value
    return aliases.get(value)


def validate_trigger_matrix(
    path: Path,
    owner_ids: set[str],
    aliases: dict[str, str],
    ontology: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    payload = load_json(path)
    if not isinstance(payload, dict):
        return {}, [f"{path}: must be JSON object"]
    errors.extend(unknown_keys(path.as_posix(), payload, TRIGGER_KEYS, required=TRIGGER_REQUIRED_KEYS))
    if payload.get("schema_version") not in {1, "1"}:
        errors.append(f"{path}: schema_version must be 1")
    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        return {}, errors + [f"{path}: rules must be a non-empty array"]

    licensed_prefixes, prefix_errors = string_list(
        "ontology licensed_feature_prefixes",
        ontology.get("licensed_feature_prefixes", []),
        allow_empty=False,
    )
    errors.extend(prefix_errors)
    governance_classes, class_errors = string_list(
        "ontology licensed_governance_classes",
        ontology.get("licensed_governance_classes", []),
        allow_empty=False,
    )
    errors.extend(class_errors)

    by_id: dict[str, dict[str, Any]] = {}
    for index, rule in enumerate(rules):
        label = f"{path.as_posix()}: rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{label}: must be object")
            continue
        errors.extend(unknown_keys(label, rule, RULE_KEYS, required=RULE_REQUIRED_KEYS))
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or resolve_owner(rule_id, owner_ids, aliases) is None:
            errors.append(f"{label}: id must resolve to catalogue owner: {rule_id!r}")
            continue
        canonical = resolve_owner(rule_id, owner_ids, aliases) or rule_id
        if canonical != rule_id:
            errors.append(f"{label}: rule id must use canonical owner id {canonical}, not alias {rule_id}")
        if rule_id in by_id:
            errors.append(f"{label}: duplicate rule id {rule_id}")
        by_id[rule_id] = rule
        for field in ("requires_any", "requires_all", "blocks", "yields_to", "land_requires"):
            values, value_errors = string_list(f"{label}.{field}", rule.get(field, []))
            errors.extend(value_errors)
            if field in {"blocks", "yields_to"}:
                for item in values:
                    if resolve_owner(item, owner_ids, aliases) is None:
                        errors.append(f"{label}.{field}: owner does not resolve: {item}")
                    elif item not in owner_ids:
                        errors.append(f"{label}.{field}: use canonical owner id, not alias: {item}")
            if field in {"requires_any", "requires_all"}:
                for item in values:
                    if not any(item.startswith(prefix) for prefix in licensed_prefixes):
                        errors.append(f"{label}.{field}: unlicensed feature condition {item!r}")
        dimensions = rule.get("pressure_dimensions", [])
        if dimensions is not None:
            if not isinstance(dimensions, list):
                errors.append(f"{label}.pressure_dimensions: must be array")
            for dim_index, dimension in enumerate(dimensions):
                dim_label = f"{label}.pressure_dimensions[{dim_index}]"
                if not isinstance(dimension, dict):
                    errors.append(f"{dim_label}: must be object")
                    continue
                dim_extra = set(dimension) - {"id", "label", "requires_any", "requires_all", "source_quote_when_features", "when_features"}
                if dim_extra:
                    errors.append(f"{dim_label}: unknown key(s): {', '.join(sorted(dim_extra))}")
                for required in ("id", "label", "requires_any"):
                    if required not in dimension:
                        errors.append(f"{dim_label}: missing {required}")
                if not isinstance(dimension.get("id"), str) or not SHA_SCOPE_RE.match(str(dimension.get("id", ""))):
                    errors.append(f"{dim_label}.id: invalid id")
                if not isinstance(dimension.get("label"), str) or not dimension.get("label"):
                    errors.append(f"{dim_label}.label: must be non-empty string")
                dim_values, dim_errors = string_list(f"{dim_label}.requires_any", dimension.get("requires_any", []), allow_empty=False)
                errors.extend(dim_errors)
                for value in dim_values:
                    if len(value.strip()) < 3:
                        errors.append(f"{dim_label}.requires_any: token too short: {value!r}")
                dim_all_values, dim_all_errors = string_list(f"{dim_label}.requires_all", dimension.get("requires_all", []))
                errors.extend(dim_all_errors)
                for value in dim_all_values:
                    if len(value.strip()) < 3:
                        errors.append(f"{dim_label}.requires_all: token too short: {value!r}")
                source_when, source_when_errors = string_list(
                    f"{dim_label}.source_quote_when_features",
                    dimension.get("source_quote_when_features", []),
                )
                errors.extend(source_when_errors)
                for feature in source_when:
                    if not any(feature.startswith(prefix) for prefix in licensed_prefixes):
                        errors.append(f"{dim_label}.source_quote_when_features: unlicensed feature condition {feature!r}")
                active_when, active_when_errors = string_list(
                    f"{dim_label}.when_features",
                    dimension.get("when_features", []),
                )
                errors.extend(active_when_errors)
                for feature in active_when:
                    if not any(feature.startswith(prefix) for prefix in licensed_prefixes):
                        errors.append(f"{dim_label}.when_features: unlicensed feature condition {feature!r}")
        if not isinstance(rule.get("priority"), int):
            errors.append(f"{label}: priority must be integer")
        if rule.get("governance_class") not in governance_classes:
            errors.append(f"{label}: governance_class not licensed: {rule.get('governance_class')!r}")
        if rule_id in {"M8-reductio", "V2-reconstituting-reason"}:
            if "feature.worldview_refutation_request" in set(rule.get("requires_any", [])):
                errors.append(f"{label}: request verbs must not route {rule_id} as noetic pressure by themselves")
        if rule_id == "M8-reductio" and "feature.opponent_worldview_frame" in set(rule.get("requires_any", [])):
            errors.append(f"{label}: source-worldview label alone must not route M8-reductio")
        if not rule.get("pressure_dimensions"):
            errors.append(f"{label}: Level 3 covered-scope rule must define pressure_dimensions")
    return by_id, errors


def validate_precedence(
    path: Path,
    owner_ids: set[str],
    aliases: dict[str, str],
    ontology: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    payload = load_yaml_dict(path)
    errors.extend(unknown_keys(path.as_posix(), payload, PRECEDENCE_KEYS, required=PRECEDENCE_REQUIRED_KEYS))
    if payload.get("schema_version") not in {1, "1"}:
        errors.append(f"{path}: schema_version must be 1")
    priority_order, priority_errors = string_list(f"{path}.priority_order", payload.get("priority_order", []), allow_empty=False)
    errors.extend(priority_errors)
    for item in priority_order:
        if resolve_owner(item, owner_ids, aliases) is None:
            errors.append(f"{path}: priority_order owner does not resolve: {item}")
        elif item not in owner_ids:
            errors.append(f"{path}: priority_order must use canonical owner id, not alias: {item}")
    governance_order, governance_errors = string_list(
        f"{path}.governance_order",
        payload.get("governance_order", []),
        allow_empty=False,
    )
    errors.extend(governance_errors)
    licensed = set(ontology.get("licensed_governance_classes", []))
    for item in governance_order:
        if item not in licensed:
            errors.append(f"{path}: governance_order value not licensed: {item}")
    if payload.get("determinism_claim") != "routing-given-features-only":
        errors.append(f"{path}: determinism_claim must be routing-given-features-only")
    return errors


def validate_ontology(path: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    payload = load_yaml_dict(path)
    errors.extend(unknown_keys(path.as_posix(), payload, ONTOLOGY_KEYS, required=ONTOLOGY_REQUIRED_KEYS))
    if payload.get("schema_version") not in {1, "1"}:
        errors.append(f"{path}: schema_version must be 1")
    for field in ONTOLOGY_KEYS - {"schema_version", "scope"}:
        _values, value_errors = string_list(f"{path}.{field}", payload.get(field, []), allow_empty=False)
        errors.extend(value_errors)
    verdicts = set(payload.get("licensed_verdicts", []))
    missing = {"STOP", "HOLD", "RECURSE", "PARTIAL"} - verdicts
    if missing:
        errors.append(f"{path}: licensed_verdicts missing {', '.join(sorted(missing))}")
    return payload, errors


def check_tree(root: Path, prefix: str) -> list[str]:
    data_root = root / prefix / "data"
    errors: list[str] = []
    ontology, ontology_errors = validate_ontology(data_root / "ontology-licenses.yaml")
    errors.extend(ontology_errors)
    owners, aliases, catalogue_errors = validate_catalogue(data_root / "module-catalogue.json")
    errors.extend(catalogue_errors)
    _rules, trigger_errors = validate_trigger_matrix(
        data_root / "trigger-matrix.json",
        set(owners),
        aliases,
        ontology,
    )
    errors.extend(trigger_errors)
    errors.extend(validate_precedence(data_root / "routing-precedence.yaml", set(owners), aliases, ontology))
    return errors


def load_script_module(path: Path, module_name: str) -> Any:
    scripts_dir = str(path.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def route_ids_for_text(root: Path, text: str) -> tuple[set[str], list[str]]:
    scripts_root = root / "atomics" / "skill" / "scripts"
    skill_root = root / "atomics" / "skill"
    diagnose = load_script_module(scripts_root / "diagnose.py", "level3_diagnose_canary")
    route = load_script_module(scripts_root / "route.py", "level3_route_canary")
    features = diagnose.extract(text, skill_root)
    route_plan = route.compute_route(features, skill_root)
    first_live = [str(item.get("id")) for item in route_plan.get("first_live", []) if isinstance(item, dict)]
    held = [str(item.get("id")) for item in route_plan.get("held", []) if isinstance(item, dict)]
    deferred = [str(item.get("id")) for item in route_plan.get("deferred", []) if isinstance(item, dict)]
    return set(features.get("feature_ids", [])), [*first_live, *held, *deferred]


def formal_route_canary_errors(root: Path) -> list[str]:
    errors: list[str] = []
    bare_features, bare_routes = route_ids_for_text(
        root,
        "Catalogue note: Trinity is a label here, with no claim, no relation, and no objection.",
    )
    if "term.trinity" not in bare_features:
        errors.append("formal route canary: bare label did not exercise term.trinity extraction")
    if "do-christian-extensions" in bare_routes:
        errors.append("formal route canary: bare topic label routed do-christian-extensions")

    formal_features, formal_routes = route_ids_for_text(
        root,
        "The proposal says three persons share one divine nature, and the predicate/category transfer is unclear.",
    )
    if "feature.predication_confusion" not in formal_features:
        errors.append("formal route canary: neutral person/nature predicate relation did not derive feature.predication_confusion")
    if "do-christian-extensions" not in formal_routes:
        errors.append("formal route canary: neutral formal predication pressure did not route do-christian-extensions")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="Also validate skill/data after rebuild.",
    )
    args = parser.parse_args(argv)
    root = repo_root()
    errors = check_tree(root, "atomics/skill")
    errors.extend(formal_route_canary_errors(root))
    if args.include_generated:
        errors.extend(check_tree(root, "skill"))
    if not errors:
        print("Level 3 data shape check: PASS")
    return fail_with_errors("Level 3 data shapes", errors)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
