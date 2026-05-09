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


_STATE_REREAD_RE = re.compile("R\\(H,\\s*(?:Delta|\u0394)\\)", flags=re.IGNORECASE)


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


def _layer_marker_pattern(layer: str, burden_index: int) -> str:
    return (
        rf"(?im)^\s*(?:#{{1,6}}\s*)?"
        rf"Layer\s+{re.escape(layer)}\b[^\n]*(?:Burden\s+{burden_index}\b|B{burden_index}\b)"
    )


def _has_layer_marker(output: str, layer: str, burden_index: int) -> bool:
    return re.search(_layer_marker_pattern(layer, burden_index), output) is not None


def _first_layer_pos(output: str, layer: str, burden_index: int) -> int:
    match = re.search(_layer_marker_pattern(layer, burden_index), output)
    return match.start() if match else -1


def _has_transition_reread(output: str, prior_burden_index: int, next_burden_index: int) -> bool:
    land_pos = output.find(f"Land(B{prior_burden_index}")
    next_layer_pos = _first_layer_pos(output, "A", next_burden_index)
    if land_pos < 0 or next_layer_pos < 0 or next_layer_pos <= land_pos:
        return False
    segment = output[land_pos:next_layer_pos]
    return _STATE_REREAD_RE.search(segment) is not None


def _valid_nonexecution_decision(output: str, burden_index: int) -> bool:
    """Detect a governed decision not to execute a queued burden.

    This must be tied to the burden's Layer A/state read; a stray HOLD/SKIP word
    elsewhere is not enough.
    """

    start = _first_layer_pos(output, "A", burden_index)
    if start < 0:
        return False
    next_layer = _first_layer_pos(output, "B", burden_index)
    end_candidates = [pos for pos in [next_layer, _first_layer_pos(output, "A", burden_index + 1)] if pos > start]
    end = min(end_candidates) if end_candidates else min(len(output), start + 1200)
    segment = output[start:end]
    decision = re.search(
        r"\b(?:HOLD|HELD|DEFER|DEFERRED|SKIP|SKIPPED|PARTIAL|REROUTE|not licensed|no longer live|blocked)\b",
        segment,
        flags=re.IGNORECASE,
    )
    reason = re.search(
        r"\b(?:because|reason|state|delta|after|landed|blocked|no longer|not input-anchored|not licensed|hold gate|register|semantic|thin-basis)\b",
        segment,
        flags=re.IGNORECASE,
    )
    return bool(decision and reason)


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
    nonexecuted_continuation_ids: set[str] = set()

    queue_blocked_from: int | None = None
    for index, entry in enumerate(continuation_entries, start=2):
        queued_ids = owner_ids(entry.get("owners", []))
        has_execution_evidence = (
            _has_layer_marker(output, "B", index)
            or f"Land(B{index}" in output
            or any(_has_owner_floor(output, owner_id) for owner_id in queued_ids)
        )
        if not has_execution_evidence and _valid_nonexecution_decision(output, index):
            queue_blocked_from = index
            for remaining in continuation_entries[index - 2:]:
                nonexecuted_continuation_ids.update(owner_ids(remaining.get("owners", [])))
            break

    for owner_id in first_live_ids + [owner_id for owner_id in continuation_ids if owner_id not in nonexecuted_continuation_ids]:
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
    if not _STATE_REREAD_RE.search(output):
        errors.append("R(H,Delta) state re-read evidence absent")

    required_steps = 1 + len(continuation_entries)
    if continuation_entries:
        if not _has_layer_marker(output, "A", 1):
            errors.append("B1: Layer A compact diagnostic control state absent")
        if not _has_layer_marker(output, "B", 1):
            errors.append("B1: Layer B governed response absent")
    for index in range(2, required_steps + 1):
        if queue_blocked_from is not None and index > queue_blocked_from:
            break
        if not _has_layer_marker(output, "A", index):
            errors.append(f"B{index}: Layer A compact diagnostic control state absent")
        elif not _has_transition_reread(output, index - 1, index):
            errors.append(f"B{index}: prior Land(B) lacks R(H,Delta) state re-read before Layer A")
        if _valid_nonexecution_decision(output, index):
            continue
        if not _has_layer_marker(output, "B", index):
            errors.append(f"B{index}: Layer B governed response absent")
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
    if continuation_entries and not _STATE_REREAD_RE.search(output):
        errors.append("continuation queue present but state re-read marker absent")

    fidelity = "fail" if errors else ("partial" if warnings else "pass")
    retry_prompt = ""
    user_visible_banner = ""
    if fidelity != "pass":
        specific_defect = errors[0] if errors else warnings[0]
        user_visible_banner = f"PARTIAL - Level 3 execution check: {specific_defect}"
        retry_prompt = (
            "Retry from the existing Level 3 route plan. Execute first_live owners, "
            "then re-read state after each Land(B) before executing continuation_queue entries. "
            "For each executed burden emit `Layer A - Compact DSL/IR Header [Burden N]` "
            "and `Layer B - Governed Response [Burden N]`. "
            "For every executed owner emit `Owner-floor: <owner-id>` followed by "
            "Target, Operation, Result, B.s, Land(B), and R(H,Delta), "
            "and do not close unless R(H,Delta) names no remaining input-anchored burdens. "
            "If a queued burden is no longer live, mark HOLD/SKIP/PARTIAL/reroute need with the state-delta reason."
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
