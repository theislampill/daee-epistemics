#!/usr/bin/env python3
"""Verify RC2 direct fixture coverage for the fourteen under-fixtured modules."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COVERAGE_DOC = ROOT / "docs/audits/v0.4.2.0-underfixtured-module-coverage.md"

EXPECTED = {
    "E3-cumulative-case": (
        "tests/routing-fixtures/65-rc2-e3-cumulative-case-positive.json",
        "tests/routing-fixtures/66-rc2-e3-cumulative-case-negative.json",
    ),
    "E4-cross-cultural-check": (
        "tests/routing-fixtures/67-rc2-e4-cross-cultural-check-positive.json",
        "tests/routing-fixtures/68-rc2-e4-cross-cultural-check-negative.json",
    ),
    "F3-practice-epistemic-access": (
        "tests/routing-fixtures/69-rc2-f3-practice-epistemic-access-positive.json",
        "tests/routing-fixtures/70-rc2-f3-practice-epistemic-access-negative.json",
    ),
    "M1P-performative-self-refutation": (
        "tests/routing-fixtures/71-rc2-m1p-performative-self-refutation-positive.json",
        "tests/routing-fixtures/72-rc2-m1p-performative-self-refutation-negative.json",
    ),
    "M6-excluded-middle": (
        "tests/routing-fixtures/73-rc2-m6-excluded-middle-positive.json",
        "tests/routing-fixtures/74-rc2-m6-excluded-middle-negative.json",
    ),
    "M7-definition-anchor": (
        "tests/routing-fixtures/75-rc2-m7-definition-anchor-positive.json",
        "tests/routing-fixtures/76-rc2-m7-definition-anchor-negative.json",
    ),
    "R1-internalist-criterion": (
        "tests/routing-fixtures/77-rc2-r1-internalist-criterion-positive.json",
        "tests/routing-fixtures/78-rc2-r1-internalist-criterion-negative.json",
    ),
    "R2-the-reminder": (
        "tests/routing-fixtures/79-rc2-r2-the-reminder-positive.json",
        "tests/routing-fixtures/80-rc2-r2-the-reminder-negative.json",
    ),
    "R3-warranted-basic-belief": (
        "tests/routing-fixtures/81-rc2-r3-warranted-basic-belief-positive.json",
        "tests/routing-fixtures/82-rc2-r3-warranted-basic-belief-negative.json",
    ),
    "inductive-fitri-method": (
        "tests/routing-fixtures/83-rc2-inductive-fitri-method-positive.json",
        "tests/routing-fixtures/84-rc2-inductive-fitri-method-negative.json",
    ),
    "P2-objection-mapping": (
        "tests/routing-fixtures/85-rc2-p2-objection-mapping-positive.json",
        "tests/routing-fixtures/86-rc2-p2-objection-mapping-negative.json",
    ),
    "P5-already-believing": (
        "tests/routing-fixtures/87-rc2-p5-already-believing-positive.json",
        "tests/routing-fixtures/88-rc2-p5-already-believing-negative.json",
    ),
    "V3-regress-dissolution": (
        "tests/routing-fixtures/89-rc2-v3-regress-dissolution-positive.json",
        "tests/routing-fixtures/90-rc2-v3-regress-dissolution-negative.json",
    ),
    "V6-convergence": (
        "tests/routing-fixtures/91-rc2-v6-convergence-positive.json",
        "tests/routing-fixtures/92-rc2-v6-convergence-negative.json",
    ),
}


def load_fixture(path: Path, errors: list[str]) -> dict[str, object]:
    if not path.is_file():
        errors.append(f"fixture file is absent: {path.relative_to(ROOT).as_posix()}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: JSON parse error: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{path.relative_to(ROOT).as_posix()}: fixture must be a JSON object")
        return {}
    return payload


def expected_object(payload: dict[str, object], rel: str, errors: list[str]) -> dict[str, object]:
    expected = payload.get("expected")
    if not isinstance(expected, dict):
        errors.append(f"{rel}: expected object is absent")
        return {}
    return expected


def main() -> int:
    errors: list[str] = []
    doc_text = COVERAGE_DOC.read_text(encoding="utf-8") if COVERAGE_DOC.is_file() else ""
    if not doc_text:
        errors.append(f"coverage doc is absent: {COVERAGE_DOC.relative_to(ROOT).as_posix()}")

    for module_id, (positive_rel, negative_rel) in EXPECTED.items():
        if module_id not in doc_text:
            errors.append(f"{module_id}: absent from coverage doc")
        for rel in (positive_rel, negative_rel):
            if rel not in doc_text:
                errors.append(f"{module_id}: fixture path absent from coverage doc: {rel}")

        positive = load_fixture(ROOT / positive_rel, errors)
        negative = load_fixture(ROOT / negative_rel, errors)

        if positive:
            expected = expected_object(positive, positive_rel, errors)
            required = expected.get("required_modules")
            if not isinstance(required, list) or module_id not in required:
                errors.append(f"{positive_rel}: required_modules does not include {module_id}")
            if module_id in (expected.get("forbidden_matched_modules") or []):
                errors.append(f"{positive_rel}: target module is also forbidden")

        if negative:
            expected = expected_object(negative, negative_rel, errors)
            forbidden = expected.get("forbidden_matched_modules")
            if not isinstance(forbidden, list) or module_id not in forbidden:
                errors.append(f"{negative_rel}: forbidden_matched_modules does not include {module_id}")
            if module_id in (expected.get("required_modules") or []):
                errors.append(f"{negative_rel}: target module is also required")

    if errors:
        print("under-fixtured module coverage: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("under-fixtured module coverage: PASS")
    print(f"- modules checked: {len(EXPECTED)}")
    print(f"- direct fixture files checked: {len(EXPECTED) * 2}")
    print(f"- coverage doc: {COVERAGE_DOC.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
