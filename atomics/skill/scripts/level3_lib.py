#!/usr/bin/env python3
"""Shared helpers for the daee-epistemics Level 3 pilot.

The pilot deliberately keeps routing deterministic after feature extraction.
Feature extraction can remain interpretive; route.py must not call an LLM.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


LEVEL3_VERSION = "0.1.0"


def default_skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(payload: Any) -> str:
    return sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def span_record(feature_id: str, match: re.Match[str], source: str) -> dict[str, Any]:
    return {
        "feature_id": feature_id,
        "text": match.group(0),
        "start": match.start(),
        "end": match.end(),
        "source": source,
    }


def find_spans(text: str, feature_id: str, patterns: list[str], source: str) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            spans.append(span_record(feature_id, match, source))
    unique: dict[tuple[int, int, str], dict[str, Any]] = {}
    for span in spans:
        unique[(int(span["start"]), int(span["end"]), str(span["feature_id"]))] = span
    return sorted(unique.values(), key=lambda item: (int(item["start"]), int(item["end"]), str(item["feature_id"])))


def load_catalogue(skill_root: Path) -> dict[str, Any]:
    return read_json(skill_root / "data" / "module-catalogue.json")


def load_trigger_matrix(skill_root: Path) -> dict[str, Any]:
    return read_json(skill_root / "data" / "trigger-matrix.json")


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the small, list-only YAML files used by the Level 3 pilot.

    This is intentionally not a general YAML parser; keeping the data shape
    small avoids a runtime dependency inside the skill package.
    """

    result: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value:
                result[key] = _yaml_scalar(value)
            else:
                result[key] = []
            continue
        if current_key and line.strip().startswith("- "):
            result.setdefault(current_key, [])
            result[current_key].append(_yaml_scalar(line.strip()[2:].strip()))
    return result


def _yaml_scalar(value: str) -> Any:
    if value.isdigit():
        return int(value)
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def load_routing_precedence(skill_root: Path) -> dict[str, Any]:
    return parse_simple_yaml(skill_root / "data" / "routing-precedence.yaml")


def load_ontology(skill_root: Path) -> dict[str, Any]:
    return parse_simple_yaml(skill_root / "data" / "ontology-licenses.yaml")


def condition_satisfied(condition: str, feature_ids: set[str]) -> bool:
    return condition in feature_ids


def owner_by_id(catalogue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(owner["id"]): owner for owner in catalogue.get("owners", [])}


def rule_by_id(trigger_matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(rule["id"]): rule for rule in trigger_matrix.get("rules", [])}


def feature_spans(features: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    spans: dict[str, list[dict[str, Any]]] = {}
    for section_name in ("mechanical", "llm_assisted"):
        for feature in features.get(section_name, []):
            feature_id = str(feature.get("id", ""))
            if not feature_id:
                continue
            spans.setdefault(feature_id, [])
            spans[feature_id].extend(feature.get("spans", []))
    return spans


def precedence_index(precedence: dict[str, Any], owner_id: str) -> int:
    order = [str(item) for item in precedence.get("priority_order", [])]
    if owner_id in order:
        return order.index(owner_id)
    return len(order) + 100


def governance_verdict(governance_classes: list[str], precedence: dict[str, Any] | None = None) -> str:
    if precedence is None:
        order = ["partials", "holds", "recurses", "routes"]
    else:
        order = [str(item) for item in precedence.get("governance_order", ["partials", "holds", "recurses", "routes"])]
    for item in order:
        if item in governance_classes:
            return {
                "partials": "PARTIAL",
                "holds": "HOLD",
                "recurses": "RECURSE",
                "routes": "STOP",
            }.get(item, "PARTIAL")
    return "PARTIAL"


def derive_live_burden(feature_ids: set[str]) -> str:
    if "feature.grief_register" in feature_ids or "feature.trauma_register" in feature_ids:
        return "grief-coded register hold"
    if "feature.imported_criterion" in feature_ids or "feature.moral_tribunal" in feature_ids:
        return "imported moral tribunal / criterion-smuggling burden"
    if "feature.false_resemblance" in feature_ids:
        return "false resemblance / mushabara fasida deformation"
    if "feature.necessary_knowledge_shubhah" in feature_ids:
        return "genuine shubhah after deformation clearing"
    if "feature.predication_confusion" in feature_ids:
        return "predication-mode and attribute-language burden"
    if "term.secularism" in feature_ids or "feature.worldview_refutation_request" in feature_ids:
        return "broad secularism reason-repair burden"
    return "ambiguous noetic burden"


def route_state_signature(route_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "first_live": route_plan.get("first_live", []),
        "held": route_plan.get("held", []),
        "deferred": route_plan.get("deferred", []),
        "continuation_queue": route_plan.get("continuation_queue", []),
        "closure_gate": route_plan.get("closure_gate", {}),
        "governance_verdict": route_plan.get("governance_verdict"),
        "live_burden": route_plan.get("live_burden"),
        "land_requirements": route_plan.get("land_requirements", []),
    }


def owner_ids(items: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("id")) for item in items]
