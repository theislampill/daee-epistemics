#!/usr/bin/env python3
"""Post-output validator for Level 3 route-plan execution."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from level3_lib import default_skill_root, owner_ids, read_json, write_json


def _has_owner_floor(output: str, owner_id: str) -> bool:
    return re.search(rf"Owner-floor:\s*{re.escape(owner_id)}\b", output, flags=re.IGNORECASE) is not None


_ORDINAL_WORDS = {
    1: "first",
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
    8: "eighth",
    9: "ninth",
    10: "tenth",
    11: "eleventh",
    12: "twelfth",
    13: "thirteenth",
    14: "fourteenth",
    15: "fifteenth",
    16: "sixteenth",
    17: "seventeenth",
    18: "eighteenth",
    19: "nineteenth",
    20: "twentieth",
}


def _has_burden_marker(output: str, burden_index: int) -> bool:
    """Detect a visible burden-structure label for burden N.

    Keep this anchored to line-level structure so a stray ordinal word or a
    `Land(BN)` citation does not satisfy traversal by itself.
    """

    ordinal = _ORDINAL_WORDS.get(burden_index)
    labels = [
        rf"B{burden_index}(?:\.s\d*)?\b",
        rf"[Bb]urden\s+{burden_index}\b",
    ]
    if ordinal:
        labels.append(rf"{ordinal}\s+[Bb]urden\b")
    pattern = rf"(?im)^\s*(?:#{{1,6}}\s*)?(?:[-*]\s*)?(?:{'|'.join(labels)})"
    return re.search(pattern, output) is not None


def _closure_gate_satisfied(output: str, continuation_entries: list[dict[str, Any]]) -> bool:
    """Allow final close only when queued burdens visibly landed and no burden remains."""
    if continuation_entries:
        last_index = 1 + len(continuation_entries)
        if f"Land(B{last_index}" not in output:
            return False
        if not _has_burden_marker(output, last_index):
            return False
    closure_markers = (
        r"no remaining input-anchored burden",
        r"no remaining input anchored burden",
        r"remaining input-anchored burdens:\s*none",
        r"none requiring release",
        r"no route-plan burden remains",
        r"no other queued owner remains",
        r"closure gate satisfied",
        r"closure licensed",
    )
    return any(re.search(marker, output, flags=re.IGNORECASE) for marker in closure_markers)


def check_execution(route_plan: dict[str, Any], output: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    first_live_ids = owner_ids(route_plan.get("first_live", []))
    continuation_entries = route_plan.get("continuation_queue", [])
    continuation_ids = [
        owner_id
        for entry in continuation_entries
        for owner_id in owner_ids(entry.get("owners", []))
    ]
    held_ids = owner_ids(route_plan.get("held", []))
    deferred_ids = owner_ids(route_plan.get("deferred", []))
    verdict = str(route_plan.get("governance_verdict", "PARTIAL"))

    for owner_id in first_live_ids + continuation_ids:
        if owner_id not in output:
            errors.append(f"{owner_id}: routed owner absent from output")
        if not _has_owner_floor(output, owner_id):
            errors.append(f"{owner_id}: visible owner-floor evidence absent")

    for marker in ("Target:", "Operation:", "Result:"):
        if marker not in output:
            errors.append(f"owner-floor target-operation-result marker missing: {marker}")

    if "B1.s" not in output and "B.s" not in output and "Operative Submove" not in output:
        errors.append("visible B.s submove evidence absent")
    if "Land(B" not in output:
        errors.append("Land(B) evidence absent")
    if "R(H,Delta)" not in output and "R(H, Delta)" not in output:
        errors.append("R(H,Delta) state re-read evidence absent")

    required_steps = 1 + len(continuation_entries)
    for index in range(2, required_steps + 1):
        if not _has_burden_marker(output, index):
            errors.append(f"B{index}: continuation queue entry not visibly traversed")
        if f"Land(B{index}" not in output:
            errors.append(f"B{index}: continuation Land(B) evidence absent")

    for owner_id in held_ids + deferred_ids:
        if owner_id in continuation_ids:
            continue
        if _has_owner_floor(output, owner_id) or f"EXECUTE:{owner_id}" in output:
            errors.append(f"{owner_id}: held/deferred owner invoked as executed")

    close_markers = (
        "Closing Formulation:",
        "## Closing Formulation",
        "### Closing Formulation",
    )
    closure_satisfied = _closure_gate_satisfied(output, continuation_entries)
    if verdict != "STOP" and any(marker in output for marker in close_markers) and not closure_satisfied:
        errors.append("public close emitted before non-STOP governance cleared")
    if verdict != "STOP" and not closure_satisfied and "PARTIAL" not in output and "HOLD" not in output and "RECURSE" not in output:
        warnings.append("non-STOP governance lacks visible continuation/hold/partial marker")
    if continuation_entries and "R(H,Delta)" not in output:
        errors.append("continuation queue present but state re-read marker absent")

    fidelity = "fail" if errors else ("partial" if warnings else "pass")
    retry_prompt = ""
    user_visible_banner = ""
    if fidelity != "pass":
        specific_defect = errors[0] if errors else warnings[0]
        user_visible_banner = f"PARTIAL - Level 3 execution check: {specific_defect}"
        retry_prompt = (
            "Retry from the existing Level 3 route plan. Execute first_live owners, "
            "then execute continuation_queue entries in order when release conditions are met. "
            "For every executed owner emit `Owner-floor: <owner-id>` followed by "
            "Target, Operation, Result, B.s, Land(B), and R(H,Delta), "
            "and do not close unless R(H,Delta) names no remaining input-anchored burdens."
        )

    return {
        "checker": "check_execution.py",
        "execution_fidelity": fidelity,
        "governance_verdict": verdict,
        "errors": errors,
        "warnings": warnings,
        "user_visible_banner": user_visible_banner,
        "retry_prompt": retry_prompt,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate output against a Level 3 route plan.")
    parser.add_argument("--route-plan", "--route", dest="route_plan", required=True, help="route_plan.json path.")
    parser.add_argument("--model-output", "--output", dest="model_output", required=True, help="Model output markdown path.")
    parser.add_argument("--verdict-output", help="execution_verdict.json path.")
    parser.add_argument("--skill-root", default=str(default_skill_root()), help="Skill package root.")
    args = parser.parse_args(argv)

    del args.skill_root
    route_path = Path(args.route_plan)
    output_path = Path(args.model_output)
    if not route_path.is_file():
        print(f"check_execution: route plan missing: {route_path}", file=sys.stderr)
        return 2
    if not output_path.is_file():
        print(f"check_execution: model output missing: {output_path}", file=sys.stderr)
        return 2
    verdict = check_execution(read_json(route_path), output_path.read_text(encoding="utf-8"))
    if args.verdict_output:
        write_json(Path(args.verdict_output), verdict)
    else:
        print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0 if verdict["execution_fidelity"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
