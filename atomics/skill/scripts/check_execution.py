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


def _burden_marker_pos(output: str, burden_index: int) -> int:
    ordinal = _ORDINAL_WORDS.get(burden_index)
    labels = [
        rf"B{burden_index}(?:\.s\d*)?\b",
        rf"[Bb]urden\s+{burden_index}\b",
    ]
    if ordinal:
        labels.append(rf"{ordinal}\s+[Bb]urden\b")
    pattern = rf"(?im)^\s*(?:#{{1,6}}\s*)?(?:[-*]\s*)?(?:{'|'.join(labels)})"
    match = re.search(pattern, output)
    return match.start() if match else -1


def _burden_segment(output: str, burden_index: int) -> str:
    starts = [
        _first_layer_pos(output, "A", burden_index),
        _first_layer_pos(output, "B", burden_index),
        _burden_marker_pos(output, burden_index),
    ]
    start = min([pos for pos in starts if pos >= 0], default=0 if burden_index == 1 else -1)
    if start < 0:
        return ""
    next_starts = [
        _first_layer_pos(output, "A", burden_index + 1),
        _first_layer_pos(output, "B", burden_index + 1),
        _burden_marker_pos(output, burden_index + 1),
    ]
    next_start = min([pos for pos in next_starts if pos > start], default=len(output))
    return output[start:next_start]


def _owner_floor_match(segment: str, owner_id: str) -> re.Match[str] | None:
    return re.search(rf"Owner-floor:\s*{re.escape(owner_id)}\b", segment, flags=re.IGNORECASE)


def _has_local_owner_operation(output: str, burden_index: int, owner_id: str) -> bool:
    """Require owner-floor and Target/Operation/Result to stay in the same burden step."""

    segment = _burden_segment(output, burden_index)
    owner_match = _owner_floor_match(segment, owner_id)
    if owner_match is None:
        return False
    next_owner = re.search(r"(?im)^\s*Owner-floor:\s*", segment[owner_match.end():])
    end = owner_match.end() + next_owner.start() if next_owner else min(len(segment), owner_match.end() + 1400)
    window = segment[owner_match.end():end]
    return all(marker in window for marker in ("Target:", "Operation:", "Result:"))


def _valid_nonexecution_decision(output: str, burden_index: int, queue_entry: dict[str, Any] | None = None) -> bool:
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
        r"\b(?:because|reason|state|delta|state-delta|after|landed|blocked|no longer|not input-anchored|not licensed|hold gate|register|semantic|thin-basis|source-use|capability-bound|insufficient evidence|unsupported|ambiguous|failed extraction)\b",
        segment,
        flags=re.IGNORECASE,
    )
    burden_named = re.search(rf"\b(?:B{burden_index}|Burden\s+{burden_index})\b", segment, flags=re.IGNORECASE)
    queued_ids = owner_ids((queue_entry or {}).get("owners", []))
    owner_named = any(owner_id in segment for owner_id in queued_ids)
    specific_reason = re.search(
        r"\b(?:state-delta|register|semantic|thin-basis|source-use|capability-bound|insufficient evidence|not input-anchored|not licensed|hold gate|unsupported|ambiguous|failed extraction|next live burden|next-live)\b",
        segment,
        flags=re.IGNORECASE,
    )
    return bool(decision and reason and burden_named and (owner_named or specific_reason))


def _route_envelope(step: dict[str, Any] | None, burden_index: int, owner_id_list: list[str]) -> dict[str, Any]:
    envelope = dict((step or {}).get("state_envelope", {}))
    envelope.setdefault("current_burden_id", f"B{burden_index}")
    envelope.setdefault("owner_ids", owner_id_list)
    envelope.setdefault("input_span_refs", (step or {}).get("input_spans", []))
    envelope.setdefault("continuation_queue_remaining", [])
    envelope.setdefault("hold_or_partial_reason", None)
    envelope.setdefault("next_required_action", "execute-if-licensed")
    envelope.setdefault("state_delta", "pending")
    envelope.setdefault("reread_required", True)
    return envelope


def _execution_state_envelopes(
    route_plan: dict[str, Any],
    output: str,
    nonexecuted_continuation_ids: set[str],
) -> list[dict[str, Any]]:
    steps: list[tuple[int, dict[str, Any] | None, list[str]]] = [
        (1, route_plan.get("first_live_burden"), owner_ids(route_plan.get("first_live", []))),
    ]
    for index, entry in enumerate(route_plan.get("continuation_queue", []), start=2):
        steps.append((index, entry, owner_ids(entry.get("owners", []))))

    envelopes: list[dict[str, Any]] = []
    for index, step, step_owner_ids in steps:
        envelope = _route_envelope(step, index, step_owner_ids)
        segment = _burden_segment(output, index)
        nonexecuted = index > 1 and all(owner_id in nonexecuted_continuation_ids for owner_id in step_owner_ids)
        landed = f"Land(B{index}" in segment
        local_owner_ok = all(_has_local_owner_operation(output, index, owner_id) for owner_id in step_owner_ids)
        reread_present = _STATE_REREAD_RE.search(segment) is not None
        if nonexecuted:
            status = "held"
            reason = envelope.get("hold_or_partial_reason") or "burden-local nonexecution decision present"
        elif landed and local_owner_ok and reread_present:
            status = "pass"
            reason = None
        elif not segment.strip():
            status = "not-run"
            reason = "burden segment absent"
        else:
            status = "fail"
            reason = "burden-local owner/TOR/Land/R attachment incomplete"
        envelope.update({
            "landed": landed,
            "checker_status": status,
            "hold_or_partial_reason": reason,
            "state_delta": "reread-present" if reread_present else "missing-burden-local-reread",
        })
        envelopes.append(envelope)
    return envelopes


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
    executed_steps: list[tuple[int, list[str]]] = [(1, first_live_ids)]

    for index, entry in enumerate(continuation_entries, start=2):
        queued_ids = owner_ids(entry.get("owners", []))
        has_execution_evidence = (
            _has_layer_marker(output, "B", index)
            or f"Land(B{index}" in output
            or any(_has_owner_floor(output, owner_id) for owner_id in queued_ids)
        )
        if not has_execution_evidence and _valid_nonexecution_decision(output, index, entry):
            nonexecuted_continuation_ids.update(queued_ids)
        else:
            executed_steps.append((index, queued_ids))

    for burden_index, step_owner_ids in executed_steps:
        for owner_id in step_owner_ids:
            if owner_id not in output:
                errors.append(f"B{burden_index}/{owner_id}: routed owner absent from output")
            if not _has_owner_floor(output, owner_id):
                errors.append(f"B{burden_index}/{owner_id}: visible owner-floor evidence absent")
            elif not _has_local_owner_operation(output, burden_index, owner_id):
                errors.append(
                    f"B{burden_index}/{owner_id}: owner-floor Target/Operation/Result evidence detached from burden"
                )

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
        entry = continuation_entries[index - 2]
        if not _has_layer_marker(output, "A", index):
            errors.append(f"B{index}: Layer A compact diagnostic control state absent")
        elif not _has_transition_reread(output, index - 1, index):
            prior_entry = continuation_entries[index - 3] if index > 2 else None
            prior_was_held = bool(prior_entry and _valid_nonexecution_decision(output, index - 1, prior_entry))
            if not prior_was_held:
                errors.append(f"B{index}: prior Land(B) lacks R(H,Delta) state re-read before Layer A")
        if _valid_nonexecution_decision(output, index, entry):
            continue
        if not _has_layer_marker(output, "B", index):
            errors.append(f"B{index}: Layer B governed response absent")
        if not _has_burden_marker(output, index):
            errors.append(f"B{index}: continuation queue entry not visibly traversed")
        if f"Land(B{index}" not in output:
            errors.append(f"B{index}: continuation Land(B) evidence absent")

    reread_count = len(_STATE_REREAD_RE.findall(output))
    if len(executed_steps) > 1 and reread_count < len(executed_steps):
        errors.append(
            f"R(H,Delta) state re-read appears {reread_count} time(s) for {len(executed_steps)} executed burden(s)"
        )

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
    state_envelopes = _execution_state_envelopes(route_plan, output, nonexecuted_continuation_ids)
    failed_burdens = sorted(set(re.findall(r"\bB\d+\b", "\n".join(errors + warnings))))
    failed_owner_ids = sorted({
        owner_id
        for owner_id in first_live_ids + continuation_ids
        if any(owner_id in message for message in errors + warnings)
    })
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
            "If a queued burden is no longer live, mark HOLD/SKIP/PARTIAL/reroute need with the state-delta reason. "
            f"Failed burden(s): {', '.join(failed_burdens) if failed_burdens else 'unspecified'}. "
            f"Failed owner(s): {', '.join(failed_owner_ids) if failed_owner_ids else 'unspecified'}."
        )

    return {
        "checker": "check_execution.py",
        "execution_fidelity": fidelity,
        "governance_verdict": verdict,
        "state_envelopes": state_envelopes,
        "failed_burdens": failed_burdens,
        "failed_owner_ids": failed_owner_ids,
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
    parser.add_argument("--fail-on-partial", action="store_true", help="Exit nonzero on partial execution fidelity.")
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
    if verdict["execution_fidelity"] == "fail":
        return 1
    if args.fail_on_partial and verdict["execution_fidelity"] == "partial":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
