#!/usr/bin/env python3
"""Reject topology acceptance laws derived from universal counts or size floors."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any, Iterable


OWNED_LOGIC = (
    "tools/topology_capacity_lib.py",
    "tools/generate_topology_capacity_cases.py",
    "tools/check_topology_capacity_properties.py",
)
SCHEMA_PATH = "schema/topology-capacity-spec.schema.json"
DANGEROUS_SCHEMA_KEYS = {"maximum", "exclusiveMaximum", "maxItems", "maxLength"}
POLICY_TERMS = ("burden", "submove", "source", "citation", "route", "conclusion", "byte", "word")


def _schema_key_findings(value: Any, trail: str = "$") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in DANGEROUS_SCHEMA_KEYS:
                findings.append({"location": f"{trail}.{key}", "reason": "universal schema ceiling"})
            findings.extend(_schema_key_findings(item, f"{trail}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_schema_key_findings(item, f"{trail}[{index}]"))
    return findings


def _numeric_value(node: ast.AST) -> int | float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    return None


def _acceptance_floor_findings(path: Path) -> list[dict[str, Any]]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    findings: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        expression = ast.get_source_segment(source, node) or ""
        source_line = source.splitlines()[node.lineno - 1]
        if any(
            marker in source_line
            for marker in (
                "topology-constructor-arity",
                "topology-relation-arity",
                "telemetry-canary-selection",
            )
        ):
            continue
        lowered = expression.lower()
        if not any(term in lowered for term in POLICY_TERMS):
            continue
        constants = [_numeric_value(node.left), *(_numeric_value(item) for item in node.comparators)]
        if not any(value not in (None, 0, 1) for value in constants):
            continue
        if "probe" in lowered or "telemetry" in lowered or "observed" in lowered:
            continue
        findings.append({"path": path.as_posix(), "line": node.lineno, "expression": expression, "reason": "numeric topology acceptance law"})
    for line_number, line in enumerate(source.splitlines(), 1):
        if re.search(r"(?:minimum|maximum|at least|no more than)\s+\d+\s+(?:burdens?|submoves?|sources?|citations?|routes?|conclusions?|bytes?|words?)", line, re.I):
            findings.append({"path": path.as_posix(), "line": line_number, "expression": line.strip(), "reason": "fixed topology policy prose in acceptance logic"})
    return findings


def scan_repository(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    schema_path = root / SCHEMA_PATH
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    findings.extend({"path": SCHEMA_PATH, **item} for item in _schema_key_findings(schema))
    for relative in OWNED_LOGIC:
        findings.extend(_acceptance_floor_findings(root / relative))
    probe_set = json.loads((root / "tests" / "topology-capacity" / "probe-set.json").read_text(encoding="utf-8"))
    telemetry_values = sorted(
        {
            json.loads((root / "tests" / "topology-capacity" / relative).read_text(encoding="utf-8"))["dimensions"]["baseline_burdens"]
            for relative in probe_set["specs"]
        }
    )
    return {
        "checker_id": "no-fixed-topology-floors",
        "status": "PASS" if not findings else "FAIL",
        "exit_code": 0 if not findings else 1,
        "findings": findings,
        "telemetry_canary_burden_counts": telemetry_values,
        "distinction": "telemetry/canary values are observations; they are never semantic acceptance law",
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = scan_repository(args.root.resolve())
    print(json.dumps(result, sort_keys=True))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
