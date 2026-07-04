#!/usr/bin/env python3
"""Check the narrow T_lang response-closure boundary.

This checker does not claim interlocutor uptake. It verifies only the
runtime-side public-language obligation: when field_witness exposes a generated
MRP burden with generated owner activation pressure, the Restorative Response
must visibly reflect that generated pressure instead of leaving it only in the
proof machinery.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from closure_witness_lib import extract_embedded_field_witness, extract_field_witness, field_witness_ledger, normalize_burden_id
from check_mrp_generated_burden import graph_normalized_text, visible_keywords


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "tlang-response-closure"
GENERATED_SOURCE_RE = re.compile(r"(?i)^\s*(?:MRP\(|generated\b)")
UPTAKE_ASSERTION_RE = re.compile(
    r"(?i)\b(?:"
    r"interlocutor\s+(?:will|must|now)\s+(?:accept|concede|see|recognize|submit)|"
    r"(?:will|must|now)\s+(?:accept|concede|see|recognize|submit)\s+(?:the\s+)?(?:truth|claim|answer)|"
    r"cannot\s+(?:deny|resist|avoid\s+conceding)|"
    r"has\s+no\s+choice\s+but\s+(?:to\s+)?(?:accept|concede|submit)|"
    r"this\s+resolves\s+(?:his|her|their|the)\s+doubt"
    r")\b"
)


@dataclass
class CheckResult:
    errors: list[str]
    partials: list[str]
    obligations: int = 0
    closed: int = 0


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def expected_diagnostic_failures(fixture_path: Path, emitted: list[str]) -> list[str]:
    """Optional expected-diagnostic sidecar (schema expected-diagnostic-v1).

    If <fixture-stem>.expected.json exists next to an invalid fixture, require every
    `expected_error_substrings` entry (>= 12 chars, not the fixture name/path) to be a
    substring of at least one emitted error, so the fixture is pinned to fail for the
    RIGHT reason. Sidecars are opt-in: a fixture without one is unaffected."""
    sidecar = fixture_path.parent / (fixture_path.stem + ".expected.json")
    if not sidecar.is_file():
        return []
    out: list[str] = []
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    if data.get("schema") != "expected-diagnostic-v1":
        return [f"{rel(sidecar)}: schema must be 'expected-diagnostic-v1'"]
    if data.get("fixture") != fixture_path.name:
        out.append(f"{rel(sidecar)}: fixture must be {fixture_path.name!r}")
    blob = "\n".join(emitted)
    for sub in data.get("expected_error_substrings", []):
        if not isinstance(sub, str) or len(sub) < 12:
            out.append(f"{rel(sidecar)}: expected_error_substrings entry must be a string >= 12 chars: {sub!r}")
        elif sub in {fixture_path.name, rel(fixture_path)}:
            out.append(f"{rel(sidecar)}: expected_error_substrings must not equal the fixture path/name")
        elif sub not in blob:
            out.append(f"{rel(fixture_path)}: expected diagnostic not observed: {sub!r}")
    return out


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


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


def public_execution_text(text: str) -> str:
    match = re.search(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\s*$", text)
    return text[: match.start()] if match else text


def section_after_heading(text: str, heading: str) -> str:
    pattern = re.compile(rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(heading)}\s*$")
    match = pattern.search(text)
    if not match:
        return ""
    next_heading = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:Closing Formulation|Closure/Reconstruction Witness|Held-node Accounting|field_witness|Legend)\s*$",
        text[match.end() :],
    )
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end() : end]


def parse_field_witness(path: Path, text: str) -> tuple[dict[str, Any] | None, list[str]]:
    payload = extract_embedded_field_witness(text)
    if payload is None:
        return None, [f"{rel(path)}: field_witness parser-stable JSON payload missing"]
    field_witness = extract_field_witness(payload)
    if field_witness is None:
        return None, [f"{rel(path)}: field_witness object missing"]
    return field_witness, []


def words(value: str) -> set[str]:
    normalized = re.sub(r"[-_/]", " ", graph_normalized_text(value).lower())
    return set(re.findall(r"[a-z0-9][a-z0-9']{3,}", normalized))


def pressure_reflected(label: str, response: str) -> bool:
    label_norm = re.sub(r"\s+", " ", graph_normalized_text(label).strip().lower())
    response_norm = re.sub(r"\s+", " ", graph_normalized_text(response).strip().lower())
    if label_norm and label_norm in response_norm:
        return True

    keywords = visible_keywords(label_norm)
    if not keywords:
        return False
    hits = set(keywords).intersection(words(response))
    return len(hits) >= min(2, len(set(keywords)))


def generated_burden_records(field_witness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = field_witness.get("generated_burdens")
    result: dict[str, dict[str, Any]] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            burden = normalize_burden_id(str(key))
            result[burden] = value if isinstance(value, dict) else {"value": value}
    elif isinstance(raw, list):
        for value in raw:
            if not isinstance(value, dict):
                continue
            burden = normalize_burden_id(str(value.get("id", "")))
            if burden:
                result[burden] = value
    return result


def activation_is_generated(activation: dict[str, Any], generated_records: dict[str, dict[str, Any]]) -> bool:
    target = normalize_burden_id(str(activation.get("target", "")))
    source = str(activation.get("source", "") or activation.get("provenance", ""))
    generated_by = str(activation.get("generated_by", ""))
    return (
        target in generated_records
        or bool(GENERATED_SOURCE_RE.search(source))
        or bool(GENERATED_SOURCE_RE.search(generated_by))
    )


def generated_pressure_obligations(field_witness: dict[str, Any]) -> dict[str, list[str]]:
    ledgers = field_witness_ledger(field_witness)
    b_mrp = set(ledgers["B_MRP"])
    generated_records = generated_burden_records(field_witness)
    obligations: dict[str, list[str]] = {burden: [] for burden in b_mrp}

    raw_activations = field_witness.get("owner_activations")
    if isinstance(raw_activations, list):
        for activation in raw_activations:
            if not isinstance(activation, dict):
                continue
            target = normalize_burden_id(str(activation.get("target", "")))
            if target not in b_mrp or not activation_is_generated(activation, generated_records):
                continue
            for key in ("pressure_label", "pressure", "pi", "target_pressure"):
                value = str(activation.get(key, "")).strip()
                if value:
                    obligations.setdefault(target, []).append(value)

    for burden, record in generated_records.items():
        if burden not in b_mrp:
            continue
        for key in ("pressure_label", "pressure", "reason", "label"):
            value = str(record.get(key, "")).strip()
            if value:
                obligations.setdefault(burden, []).append(value)

    return {burden: list(dict.fromkeys(labels)) for burden, labels in obligations.items()}


def check_text(path: Path, text: str) -> CheckResult:
    field_witness, errors = parse_field_witness(path, text)
    if field_witness is None:
        return CheckResult(errors=errors, partials=[])

    obligations = generated_pressure_obligations(field_witness)
    public_text = public_execution_text(text)
    if UPTAKE_ASSERTION_RE.search(public_text):
        errors.append(
            f"{rel(path)}: public T_lang surface claims guaranteed uptake or compliance-side success"
        )
    restorative = section_after_heading(public_text, "Restorative Response")
    partials: list[str] = []
    closed = 0

    for burden, labels in obligations.items():
        if not labels:
            partials.append(
                f"{rel(path)}: T_lang PARTIAL for {burden}: generated B_MRP burden lacks pressure labels for response mapping"
            )
            continue
        if not restorative.strip():
            partials.append(
                f"{rel(path)}: T_lang PARTIAL for {burden}: Restorative Response section missing"
            )
            continue
        matched = [label for label in labels if pressure_reflected(label, restorative)]
        if matched:
            closed += 1
            continue
        partials.append(
            f"{rel(path)}: T_lang PARTIAL for {burden}: Restorative Response does not reflect generated pressure labels "
            + repr(labels)
        )

    return CheckResult(errors=errors, partials=partials, obligations=len(obligations), closed=closed)


def fixture_paths(kind: str) -> list[Path]:
    root = FIXTURE_ROOT / kind
    return sorted(root.glob("*.md")) if root.exists() else []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", nargs="*", type=Path, default=[], help="Hosted/current outputs to classify.")
    parser.add_argument("--allow-partial", action="store_true", help="Return 0 when hosted outputs are PARTIAL.")
    args = parser.parse_args()

    failures: list[str] = []
    total_valid = 0
    total_invalid = 0
    output_results: list[tuple[Path, CheckResult]] = []

    for path in fixture_paths("valid"):
        total_valid += 1
        result = check_text(path, read_text(path))
        if result.errors or result.partials:
            failures.extend(result.errors)
            failures.extend(result.partials)

    for path in fixture_paths("invalid"):
        total_invalid += 1
        result = check_text(path, read_text(path))
        emitted = list(result.errors) + list(result.partials)
        if not emitted:
            failures.append(f"{rel(path)}: invalid T_lang canary unexpectedly closed")
        else:
            failures.extend(expected_diagnostic_failures(path, emitted))

    for path in expand_paths(args.outputs):
        result = check_text(path, read_text(path))
        output_results.append((path, result))

    output_errors = [item for _, result in output_results for item in result.errors]
    output_partials = [item for _, result in output_results for item in result.partials]
    failures.extend(output_errors)

    if failures:
        print("T_lang response closure check: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    if output_partials:
        print("T_lang response closure check: PARTIAL")
        for partial in output_partials:
            print(f"- {partial}")
        print(f"Valid fixtures checked: {total_valid}")
        print(f"Invalid canaries checked: {total_invalid}")
        print(f"Hosted/live outputs checked: {len(output_results)}")
        return 0 if args.allow_partial else 2

    print("T_lang response closure check: PASS")
    print(f"Valid fixtures checked: {total_valid}")
    print(f"Invalid canaries checked: {total_invalid}")
    if output_results:
        print(f"Hosted/live outputs checked: {len(output_results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
