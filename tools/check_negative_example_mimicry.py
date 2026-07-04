#!/usr/bin/env python3
"""Check formal owner-contract negative examples as anti-mimicry fixtures.

The formal owner contracts define `negative_examples` as label-shaped moves that
must not count as owner execution. This checker keeps a manifest-backed corpus
in sync with those contract entries and runs each synthetic mimicry output
through the existing NLA/ACT structural validator. A negative example is closed
only when that validator rejects the output.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from check_nla_decode_semantic_faithfulness import nla_decode_errors
from check_ttp_operator_contracts import extract_formal_owner_contract, string_list
from compiled_runtime_lib import fail_with_errors, repo_root


CONTRACT_ROOT = Path("atomics/skill/references")
MANIFEST_PATH = Path("tests/negative-example-mimicry/manifest.json")
SCHEMA = "negative-example-mimicry-v1"


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "case"


def formal_contracts(root: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
    contracts: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted((root / CONTRACT_ROOT).rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        contract, parse_error = extract_formal_owner_contract(text)
        if parse_error:
            raise ValueError(f"{path.relative_to(root).as_posix()}: {parse_error}")
        if not contract:
            continue
        owner_id = str(contract.get("owner_id") or "").strip()
        if not owner_id:
            raise ValueError(f"{path.relative_to(root).as_posix()}: formal owner contract lacks owner_id")
        contracts[owner_id] = (path.relative_to(root), contract)
    return contracts


def expected_rows(contracts: dict[str, tuple[Path, dict[str, Any]]]) -> dict[tuple[str, str], dict[str, str]]:
    rows: dict[tuple[str, str], dict[str, str]] = {}
    for owner_id, (source_path, contract) in sorted(contracts.items()):
        operations = string_list(contract.get("operation_token"))
        deltas = string_list(contract.get("delta_result"))
        negatives = string_list(contract.get("negative_examples"))
        if not operations or not deltas or not negatives:
            continue
        for negative in negatives:
            rows[(owner_id, negative)] = {
                "owner_id": owner_id,
                "source_path": source_path.as_posix(),
                "negative_example": negative,
                "operation": operations[0],
                "delta_result": deltas[0],
                "fixture_path": f"tests/negative-example-mimicry/invalid/{slug(owner_id)}-{slug(negative)}.md",
            }
    return rows


def load_manifest(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    path = root / MANIFEST_PATH
    if not path.is_file():
        return [], [f"{MANIFEST_PATH.as_posix()}: missing"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [f"{MANIFEST_PATH.as_posix()}: invalid JSON: {exc}"]
    if not isinstance(payload, dict):
        return [], [f"{MANIFEST_PATH.as_posix()}: manifest must be a JSON object"]
    errors: list[str] = []
    if payload.get("schema") != SCHEMA:
        errors.append(f"{MANIFEST_PATH.as_posix()}: schema must be {SCHEMA!r}")
    rows = payload.get("fixtures")
    if not isinstance(rows, list):
        errors.append(f"{MANIFEST_PATH.as_posix()}: fixtures must be a list")
        return [], errors
    return [row for row in rows if isinstance(row, dict)], errors


def mimicry_text(row: dict[str, Any]) -> str:
    owner = str(row["owner_id"])
    operation = str(row["operation"])
    delta = str(row["delta_result"])
    negative = str(row["negative_example"])
    return f"""NOETIC FIELD EXECUTION

## Layer A - Compact DSL/IR Header
- Initial burden set: [B1]

## Layer B - Bounded Governed Response

⟦ACT B1_1[{owner}.{operation}] :: π=negative-example-mimicry-pressure :: body_ref=B1_1 :: Δ=ΔB1:{delta} :: Land(B1)+⟧

B1_1[{owner}] - negative example mimicry
- Target: label mimicry.
- Operation: {negative}. This names {owner} but does not execute owner-local mechanics.
- Result/state-change: The label is echoed and claimed as landed.
- Contribution-to-Land(B1): Land(B1) is claimed from the label echo.

Land(B1): mimicry is claimed as landed.

field_witness
{{
  "B_LA": ["B1"],
  "B_MRP": [],
  "B_total": ["B1"],
  "mrp_resultants": [
    {{"source": "B1", "type": "no_new_resultant", "finding": "stable", "graph": "none", "route": "STOP"}}
  ],
  "owner_activations": [
    {{"source": "B1", "target": "B1", "owner": "{owner}", "operation": "{operation}", "pressure": "negative-example-mimicry-pressure", "body_ref": "B1_1", "delta": "ΔB1:{delta}", "land": "Land(B1)+"}}
  ],
  "normalized_activation_record": {{
    "n_frame": "negative-example-mimicry",
    "live_registers": ["xi"],
    "burden_floor": ["B1"],
    "per_burden": [
      {{"burden_id": "B1", "owner_id": "{owner}", "operation": "{operation}", "delta_result": "{delta}", "mrp_route_result_type": "no_new_resultant", "terminal_state": "landed", "generation_depth": 0}}
    ]
  }},
  "coverage_proof": {{
    "initial_burden_set": ["B1"],
    "terminal_states": {{"B1": "landed"}},
    "dependency_graph": {{"nodes": ["B1"], "edges": [], "roots": ["B1"], "acyclic": true}},
    "coverage_complete": true
  }}
}}
"""


def check_manifest_rows(
    root: Path,
    expected: dict[tuple[str, str], dict[str, str]],
    rows: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    expected_keys = set(expected)
    for index, row in enumerate(rows, start=1):
        owner = str(row.get("owner_id") or "").strip()
        negative = str(row.get("negative_example") or "").strip()
        key = (owner, negative)
        if key in seen:
            errors.append(f"{MANIFEST_PATH.as_posix()}: duplicate fixture row {owner!r} / {negative!r}")
            continue
        seen.add(key)
        if key not in expected:
            errors.append(f"{MANIFEST_PATH.as_posix()}: fixture row {index} is not declared by a formal owner contract")
            continue
        for field in ("source_path", "operation", "delta_result", "fixture_path"):
            expected_value = expected[key][field]
            if row.get(field) != expected_value:
                errors.append(
                    f"{MANIFEST_PATH.as_posix()}: row {index} {field} drifted; "
                    f"expected {expected_value!r}, got {row.get(field)!r}"
                )
        expected_errors = row.get("expected_error_substrings")
        if not isinstance(expected_errors, list) or not all(isinstance(item, str) and item for item in expected_errors):
            errors.append(f"{MANIFEST_PATH.as_posix()}: row {index} expected_error_substrings must be a non-empty string list")
            continue
        fixture_path = Path(str(row.get("fixture_path") or expected[key]["fixture_path"]))
        validator_errors = nla_decode_errors(fixture_path, mimicry_text(row))
        if not validator_errors:
            errors.append(f"{fixture_path.as_posix()}: negative example mimicry unexpectedly passed NLA/ACT validation")
            continue
        joined = "\n".join(validator_errors)
        if not any(token in joined for token in expected_errors):
            errors.append(
                f"{fixture_path.as_posix()}: rejection did not include expected diagnostic; "
                f"expected one of {expected_errors!r}; got {validator_errors!r}"
            )

    missing = sorted(expected_keys - seen)
    for owner, negative in missing:
        errors.append(f"{MANIFEST_PATH.as_posix()}: missing fixture for {owner!r} negative example {negative!r}")
    return errors


def main() -> int:
    root = repo_root()
    errors: list[str] = []
    try:
        contracts = formal_contracts(root)
    except ValueError as exc:
        return fail_with_errors("negative-example mimicry", [str(exc)])
    expected = expected_rows(contracts)
    rows, manifest_errors = load_manifest(root)
    errors.extend(manifest_errors)
    if rows:
        errors.extend(check_manifest_rows(root, expected, rows))
    if not errors:
        print("negative-example mimicry: PASS")
        print(f"Formal contracts checked: {len(contracts)}")
        print(f"Negative-example fixtures checked: {len(rows)}")
    return fail_with_errors("negative-example mimicry", errors)


if __name__ == "__main__":
    sys.exit(main())
