#!/usr/bin/env python3
"""Validate B.2 collapse-certificate schema and certificate fixtures.

This is a schema-adjacent checker, following the repo's existing custom
validation style instead of adding a jsonschema runtime dependency. It verifies
the certificate shape and a small set of semantic invariants that the schema
alone cannot express cleanly.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "collapse-certificate.schema.json"
FIXTURE_ROOT = ROOT / "tests" / "collapse-certificate"

REQUIRED_FIELDS = {
    "input_fingerprint",
    "skill_version",
    "collapse_positive",
    "coverage_complete",
    "divergence_state",
    "curl_state",
    "diagnostic_completeness",
    "live_registers_covered",
    "max_generation_depth",
    "loopbreak_count",
    "loopbreak_grounds",
    "verified_activations",
    "hold_partial_nodes",
    "primary_track_closed",
    "restoration_track_closed",
    "divergence_positive_addressed",
    "curl_resolved",
    "terminal_stop_proof_complete",
    "terminal_stop_proof_count",
    "restoration_endpoint_reached",
    "checker_version",
    "timestamp",
}
ALLOWED_FIELDS = set(REQUIRED_FIELDS)
REGISTERS = {"heart", "xi", "Omega", "mu", "kappa"}
DIVERGENCE_STATES = {"neutral", "non-neutral", "bounded", "settled"}
CURL_STATES = {"null", "resolved", "held", "non-null"}
LOOPBREAK_GROUNDS = {
    "fitrah_ground",
    "sound_reason_ground",
    "necessary_knowledge",
    "direct_contradiction_exposure",
    "definition_discipline",
    "source_status_correction",
    "doubt_churn_boundary",
}
HOLD_PARTIAL_STATES = {"held-with-reason", "carried-PARTIAL", "carried-RECURSE"}
SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")
VERSION_RE = re.compile(r"^v?[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:[-+][A-Za-z0-9.-]+)?$")
BURDEN_RE = re.compile(r"^B[0-9]+$")
TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    if not path.exists():
        return None, [f"{rel(path)}: file not found"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)}: invalid JSON: {exc}"]


def expand_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        raw = str(path)
        if any(char in raw for char in "*?["):
            matches = sorted(Path(match) for match in glob.glob(raw))
            expanded.extend(matches or [path])
        else:
            expanded.append(path)
    return expanded


def has_unique_strings(values: Any) -> bool:
    return isinstance(values, list) and all(isinstance(item, str) for item in values) and len(values) == len(set(values))


def check_string_list(
    payload: dict[str, Any],
    key: str,
    allowed: set[str] | None,
    errors: list[str],
) -> list[str]:
    values = payload.get(key)
    if not has_unique_strings(values):
        errors.append(f"{key}: must be an array of unique strings")
        return []
    result = list(values)
    if allowed is not None:
        unknown = [item for item in result if item not in allowed]
        if unknown:
            errors.append(f"{key}: unsupported values {unknown}")
    return result


def schema_errors(schema_path: Path = SCHEMA_PATH) -> list[str]:
    payload, errors = load_json(schema_path)
    if errors:
        return errors
    if not isinstance(payload, dict):
        return [f"{rel(schema_path)}: schema root must be an object"]
    result: list[str] = []
    if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        result.append(f"{rel(schema_path)}: unexpected $schema")
    if payload.get("$id") != "schema/collapse-certificate.schema.json":
        result.append(f"{rel(schema_path)}: unexpected $id")
    if payload.get("type") != "object":
        result.append(f"{rel(schema_path)}: root type must be object")
    if payload.get("additionalProperties") is not False:
        result.append(f"{rel(schema_path)}: root additionalProperties must be false")
    required = set(payload.get("required", []))
    if required != REQUIRED_FIELDS:
        result.append(f"{rel(schema_path)}: required fields mismatch: {sorted(required ^ REQUIRED_FIELDS)}")
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        result.append(f"{rel(schema_path)}: properties must be an object")
    else:
        missing = sorted(REQUIRED_FIELDS - set(properties))
        extra = sorted(set(properties) - ALLOWED_FIELDS)
        if missing:
            result.append(f"{rel(schema_path)}: required properties missing schema entries: {missing}")
        if extra:
            result.append(f"{rel(schema_path)}: unexpected root properties: {extra}")
    return result


def certificate_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["certificate root must be an object"]

    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(payload))
    extra = sorted(set(payload) - ALLOWED_FIELDS)
    if missing:
        errors.append(f"missing required fields: {missing}")
    if extra:
        errors.append(f"unexpected fields: {extra}")

    fingerprint = payload.get("input_fingerprint")
    if not isinstance(fingerprint, str) or not SHA256_RE.fullmatch(fingerprint):
        errors.append("input_fingerprint: must be a 64-character SHA-256 hex string")

    skill_version = payload.get("skill_version")
    if not isinstance(skill_version, str) or not VERSION_RE.fullmatch(skill_version):
        errors.append("skill_version: must be a semver-like string")

    for key in (
        "collapse_positive",
        "coverage_complete",
        "diagnostic_completeness",
        "primary_track_closed",
        "restoration_track_closed",
        "divergence_positive_addressed",
        "curl_resolved",
        "terminal_stop_proof_complete",
        "restoration_endpoint_reached",
    ):
        if not isinstance(payload.get(key), bool):
            errors.append(f"{key}: must be boolean")

    divergence = payload.get("divergence_state")
    if divergence not in DIVERGENCE_STATES:
        errors.append(f"divergence_state: must be one of {sorted(DIVERGENCE_STATES)}")

    curl = payload.get("curl_state")
    if curl not in CURL_STATES:
        errors.append(f"curl_state: must be one of {sorted(CURL_STATES)}")

    check_string_list(payload, "live_registers_covered", REGISTERS, errors)
    grounds = check_string_list(payload, "loopbreak_grounds", LOOPBREAK_GROUNDS, errors)
    activations = check_string_list(payload, "verified_activations", None, errors)
    for burden in activations:
        if not BURDEN_RE.fullmatch(burden):
            errors.append(f"verified_activations: invalid burden id {burden!r}")

    max_depth = payload.get("max_generation_depth")
    if not isinstance(max_depth, int) or isinstance(max_depth, bool) or max_depth < 0:
        errors.append("max_generation_depth: must be a non-negative integer")

    stop_proof_count = payload.get("terminal_stop_proof_count")
    if not isinstance(stop_proof_count, int) or isinstance(stop_proof_count, bool) or stop_proof_count < 0:
        errors.append("terminal_stop_proof_count: must be a non-negative integer")
    elif stop_proof_count > 0 and payload.get("terminal_stop_proof_complete") is not True:
        errors.append("terminal_stop_proof_count>0 requires terminal_stop_proof_complete=true")

    loopbreak_count = payload.get("loopbreak_count")
    if not isinstance(loopbreak_count, int) or isinstance(loopbreak_count, bool) or loopbreak_count < 0:
        errors.append("loopbreak_count: must be a non-negative integer")
    elif loopbreak_count != len(grounds):
        errors.append("loopbreak_count: must equal loopbreak_grounds length")

    hold_nodes = payload.get("hold_partial_nodes")
    if not isinstance(hold_nodes, list):
        errors.append("hold_partial_nodes: must be an array")
    else:
        seen_holds: set[str] = set()
        for index, item in enumerate(hold_nodes):
            label = f"hold_partial_nodes[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label}: must be an object")
                continue
            missing = {"id", "reason"} - set(item)
            extra = set(item) - {"id", "state", "reason"}
            if missing:
                errors.append(f"{label}: missing required fields {sorted(missing)}")
            if extra:
                errors.append(f"{label}: unexpected fields {sorted(extra)}")
            burden_id = item.get("id")
            if not isinstance(burden_id, str) or not BURDEN_RE.fullmatch(burden_id):
                errors.append(f"{label}.id: must be a burden id")
            elif burden_id in seen_holds:
                errors.append(f"{label}.id: duplicate hold/partial node {burden_id}")
            else:
                seen_holds.add(burden_id)
            if "state" in item and item.get("state") not in HOLD_PARTIAL_STATES:
                errors.append(f"{label}.state: must be one of {sorted(HOLD_PARTIAL_STATES)}")
            if not isinstance(item.get("reason"), str) or not item["reason"].strip():
                errors.append(f"{label}.reason: must be non-empty")

    checker_version = payload.get("checker_version")
    if not isinstance(checker_version, str) or not checker_version.strip():
        errors.append("checker_version: must be non-empty")

    timestamp = payload.get("timestamp")
    if not isinstance(timestamp, str) or not TIMESTAMP_RE.fullmatch(timestamp):
        errors.append("timestamp: must use UTC form YYYY-MM-DDTHH:MM:SSZ")

    if payload.get("collapse_positive") is True:
        if payload.get("coverage_complete") is not True:
            errors.append("collapse_positive=true requires coverage_complete=true")
        if payload.get("diagnostic_completeness") is not True:
            errors.append("collapse_positive=true requires diagnostic_completeness=true")
        if payload.get("primary_track_closed") is not True:
            errors.append("collapse_positive=true requires primary_track_closed=true")
        if payload.get("restoration_track_closed") is not True:
            errors.append("collapse_positive=true requires restoration_track_closed=true")
        if payload.get("divergence_positive_addressed") is not True:
            errors.append("collapse_positive=true requires divergence_positive_addressed=true")
        if payload.get("curl_resolved") is not True:
            errors.append("collapse_positive=true requires curl_resolved=true")
        if divergence != "neutral":
            errors.append("collapse_positive=true requires divergence_state=neutral")
        if curl not in {"null", "resolved"}:
            errors.append("collapse_positive=true requires curl_state null/resolved")
        if payload.get("restoration_endpoint_reached") is not True:
            errors.append("collapse_positive=true requires restoration_endpoint_reached=true")
    elif payload.get("restoration_endpoint_reached") is True:
        errors.append("restoration_endpoint_reached=true requires collapse_positive=true")

    return errors


def fixture_paths(root: Path, kind: str) -> list[Path]:
    base = root / kind
    if not base.exists():
        return []
    return sorted(base.glob("*.json"))


def run_fixture_suite(root: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    if not root.exists():
        return [f"{rel(root)}: fixture root missing"], valid_checked, invalid_checked

    for path in fixture_paths(root, "valid"):
        payload, found = load_json(path)
        if found:
            errors.extend(found)
            continue
        found = certificate_errors(payload)
        if found:
            errors.append(f"{rel(path)}: expected-valid certificate failed")
            errors.extend(f"{rel(path)}: {error}" for error in found)
        else:
            valid_checked += 1

    for path in fixture_paths(root, "invalid"):
        payload, found = load_json(path)
        if found:
            invalid_checked += 1
            continue
        found = certificate_errors(payload)
        if found:
            invalid_checked += 1
        else:
            errors.append(f"{rel(path)}: expected-invalid certificate unexpectedly passed")
    return errors, valid_checked, invalid_checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--certificates", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors = schema_errors(args.schema)
    suite_errors, valid_checked, invalid_checked = run_fixture_suite(args.root)
    errors.extend(suite_errors)

    direct_checked = 0
    for path in expand_paths(args.certificates):
        payload, found = load_json(path)
        if found:
            errors.extend(found)
            continue
        found = certificate_errors(payload)
        if found:
            errors.extend(f"{rel(path)}: {error}" for error in found)
        else:
            direct_checked += 1

    if errors:
        print("collapse-certificate schema check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("collapse-certificate schema check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.certificates:
        print(f"Direct certificates checked: {direct_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
