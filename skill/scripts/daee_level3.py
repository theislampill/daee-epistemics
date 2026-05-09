#!/usr/bin/env python3
"""One-command Level 3 pilot runner for daee-epistemics.

This wrapper turns an input into:
features.json -> route_plan.json -> validation/reconstruction verdicts ->
execution_prompt.md -> optional post-output execution verdict.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from check_execution import check_execution
from diagnose import extract
from level3_lib import default_skill_root, owner_ids, route_state_signature, write_json
from reconstruct import reconstruct
from route import compute_route
from validate import validate as validate_route


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _json_text(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def execution_prompt(route_plan: dict[str, Any], reconstruction: dict[str, Any]) -> str:
    first_live = owner_ids(route_plan.get("first_live", []))
    held = owner_ids(route_plan.get("held", []))
    deferred = owner_ids(route_plan.get("deferred", []))
    continuation = route_plan.get("continuation_queue", [])
    return f"""# Level 3 Binding Execution Prompt

Execute the route plan below. Do not reroute from topic cues.

Level 3 honesty boundary:
- Routing is deterministic given extracted features.
- Feature extraction can remain model/heuristic assisted and is only accepted with input-span support.
- Transformer execution can still fail or compress, especially on highest-complexity burdens.
- Direct skill invocation without this wrapper remains Level 1/2 behavior.

Live burden: {route_plan.get("live_burden")}
Governance verdict: {route_plan.get("governance_verdict")}
First-live owners: {", ".join(first_live)}
Held owners: {", ".join(held) if held else "none"}
Deferred owners: {", ".join(deferred) if deferred else "none"}
Continuation queue owners: {", ".join(owner for entry in continuation for owner in owner_ids(entry.get("owners", []))) if continuation else "none"}

Reconstruction fidelity: {reconstruction.get("reconstruction_fidelity")}

Land(B) requirements:
{_json_text(route_plan.get("land_requirements", []))}

Continuation queue:
{_json_text(continuation)}

Closure gate:
{_json_text(route_plan.get("closure_gate", {}))}

Required execution shape:
1. Execute the first-live owner(s) as Burden 1.
2. For each first-live owner, emit owner-floor evidence as:
   Owner-floor: <owner id> - <owner-specific floor>
   Target: <input-grounded target>
   Operation: <case-specific operation>
   Result: <changed claim-state>
3. Render B1.s -> Land(B1) -> R(H,Delta).
4. If the continuation queue is non-empty, continue in order. For each queued burden:
   - cite the input span(s) that anchor it;
   - emit Owner-floor / Target / Operation / Result for the queued owner(s);
   - render B<N>.s -> Land(B<N>) -> R(H,Delta);
   - say what the prior burden cleared and why this burden is now licensed.
5. Do not execute held/deferred owners outside first-live or continuation_queue.
6. Do not pad: if a queued burden lacks a real input span, mark PARTIAL instead of inventing it.
7. Do not emit Closing Formulation unless the closure gate is satisfied and R(H,Delta) names no remaining input-anchored burdens.
8. If transformer limits prevent a queued burden, emit a visible PARTIAL banner naming the exact missing queue entry.
"""


def simulated_output(route_plan: dict[str, Any]) -> str:
    lines = [
        "# Level 3 Simulated Execution Scaffold",
        "",
        f"Burden 1: {route_plan.get('live_burden')}",
    ]
    for index, item in enumerate(route_plan.get("first_live", []), start=1):
        owner_id = str(item.get("id"))
        floor = str(item.get("land_requires", ["owner-floor evidence"])[0])
        triggered = ", ".join(str(value) for value in item.get("triggered_by", []))
        lines.extend([
            f"B1.s{index}: execute first-live owner {owner_id}",
            f"Owner-floor: {owner_id} - {floor}",
            f"Target: input span(s) supporting {triggered}",
            f"Operation: expose {owner_id} against the live burden, not as a label but as target -> operation -> result",
            f"Result: {floor}",
        ])
    land = "; ".join(
        f"{item.get('owner')}: {', '.join(str(value) for value in item.get('requires', []))}"
        for item in route_plan.get("land_requirements", [])
    )
    lines.extend([
        f"Land(B1): {land}",
        f"R(H,Delta): {route_plan.get('governance_verdict')} - first-live burden processed under Level 3 route plan",
    ])
    for burden_index, entry in enumerate(route_plan.get("continuation_queue", []), start=2):
        lines.extend([
            "",
            f"Burden {burden_index}: {entry.get('name')}",
            f"State transition: B{burden_index - 1} landed; this queued burden is input-anchored and released by the route plan.",
        ])
        span_text = "; ".join(str(span.get("text", "")) for span in entry.get("input_spans", [])[:4])
        for sub_index, item in enumerate(entry.get("owners", []), start=1):
            owner_id = str(item.get("id"))
            floor = str(item.get("land_requires", ["owner-floor evidence"])[0])
            lines.extend([
                f"B{burden_index}.s{sub_index}: execute queued owner {owner_id}",
                f"Owner-floor: {owner_id} - {floor}",
                f"Target: input span(s): {span_text}",
                f"Operation: sequence {owner_id} only to the span-anchored queued burden",
                f"Result: {floor}",
            ])
        queue_land = "; ".join(
            f"{land_item.get('owner')}: {', '.join(str(value) for value in land_item.get('requires', []))}"
            for land_item in entry.get("land_requirements", [])
        )
        lines.extend([
            f"Land(B{burden_index}): {queue_land}",
            f"R(H,Delta): RECURSE - queued burden B{burden_index} processed and next queued burden rechecked",
        ])
    if route_plan.get("governance_verdict") == "STOP" and not route_plan.get("continuation_queue"):
        lines.append("Closing Formulation: no remaining input-anchored burden in this simulated route plan.")
    elif route_plan.get("continuation_queue"):
        lines.append("RECURSE complete for simulated route queue; no public close emitted in non-STOP route-plan mode.")
    else:
        lines.append("PARTIAL_NEXT_B: continue only if a remaining input-anchored burden is named by the next route plan.")
    return "\n".join(lines) + "\n"


def run_single(
    input_path: Path,
    output_dir: Path,
    skill_root: Path,
    *,
    simulate_output_flag: bool = False,
    model_output: Path | None = None,
) -> dict[str, Any]:
    text = input_path.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    copied_input = output_dir / "input.md"
    if input_path.resolve() != copied_input.resolve():
        shutil.copyfile(input_path, copied_input)

    features = extract(text, skill_root)
    write_json(output_dir / "features.json", features)

    route_plan = compute_route(features, skill_root)
    write_json(output_dir / "route_plan.json", route_plan)

    validation = validate_route(features, route_plan, skill_root)
    write_json(output_dir / "validation.json", validation)

    reconstruction = reconstruct(text, features, route_plan, skill_root)
    write_json(output_dir / "reconstruction.json", reconstruction)

    blocked = (
        validation.get("validation_fidelity") == "fail"
        or reconstruction.get("reconstruction_fidelity") == "fail"
    )
    if blocked:
        defects = []
        defects.extend(str(error) for error in validation.get("errors", []))
        defects.extend(str(error) for error in reconstruction.get("errors", []))
        defect = defects[0] if defects else "route validation or reconstruction failed"
        _write_text(
            output_dir / "execution_blocked.md",
            f"PARTIAL - Level 3 route generation blocked: {defect}\n",
        )
    else:
        _write_text(output_dir / "execution_prompt.md", execution_prompt(route_plan, reconstruction))

    execution: dict[str, Any] | None = None
    output_path: Path | None = None
    if blocked:
        output_path = None
    elif simulate_output_flag:
        output_path = output_dir / "output.simulated.md"
        _write_text(output_path, simulated_output(route_plan))
    elif model_output is not None:
        output_path = model_output

    if output_path is not None:
        execution = check_execution(route_plan, output_path.read_text(encoding="utf-8"))
        write_json(output_dir / "execution_verdict.json", execution)
        if execution.get("execution_fidelity") != "pass":
            _write_text(output_dir / "partial_banner.md", str(execution.get("user_visible_banner", "")) + "\n")
            _write_text(output_dir / "retry_prompt.md", str(execution.get("retry_prompt", "")))

    summary = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "route_state": route_state_signature(route_plan),
        "validation_fidelity": validation.get("validation_fidelity"),
        "reconstruction_fidelity": reconstruction.get("reconstruction_fidelity"),
        "execution_fidelity": execution.get("execution_fidelity") if execution else "not-run",
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def _fixture_dirs(skill_root: Path) -> list[Path]:
    fixtures_root = skill_root / "tests" / "fixtures"
    if not fixtures_root.is_dir():
        return []
    return sorted(path for path in fixtures_root.iterdir() if (path / "input.md").is_file())


def _load_expected(skill_root: Path, fixture_id: str) -> dict[str, Any]:
    path = skill_root / "tests" / "expected" / f"{fixture_id}.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _compare_expected(summary: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    route_state = summary["route_state"]
    actual_first = [str(item.get("id")) for item in route_state.get("first_live", [])]
    actual_held = [str(item.get("id")) for item in route_state.get("held", [])]
    actual_deferred = [str(item.get("id")) for item in route_state.get("deferred", [])]
    actual_queue = [
        owner_id
        for entry in route_state.get("continuation_queue", [])
        for owner_id in owner_ids(entry.get("owners", []))
    ]

    if expected.get("first_live") is not None and actual_first != expected["first_live"]:
        errors.append(f"first_live expected {expected['first_live']} got {actual_first}")
    for owner_id in expected.get("held_contains", []):
        if owner_id not in actual_held:
            errors.append(f"held missing expected owner {owner_id}; got {actual_held}")
    for owner_id in expected.get("deferred_contains", []):
        if owner_id not in actual_deferred:
            errors.append(f"deferred missing expected owner {owner_id}; got {actual_deferred}")
    for owner_id in expected.get("continuation_queue_contains", []):
        if owner_id not in actual_queue:
            errors.append(f"continuation queue missing expected owner {owner_id}; got {actual_queue}")
    if expected.get("governance_verdict") and route_state.get("governance_verdict") != expected["governance_verdict"]:
        errors.append(f"governance expected {expected['governance_verdict']} got {route_state.get('governance_verdict')}")
    contains = expected.get("live_burden_contains")
    if contains and contains not in str(route_state.get("live_burden", "")):
        errors.append(f"live burden missing {contains!r}: {route_state.get('live_burden')}")
    return errors


def _shallow_first_burden_output(route_plan: dict[str, Any]) -> str:
    lines = [
        "# Shallow first-burden-only output",
        f"Burden 1: {route_plan.get('live_burden')}",
    ]
    for index, item in enumerate(route_plan.get("first_live", []), start=1):
        owner_id = str(item.get("id"))
        floor = str(item.get("land_requires", ["owner-floor evidence"])[0])
        lines.extend([
            f"B1.s{index}: execute first-live owner {owner_id}",
            f"Owner-floor: {owner_id} - {floor}",
            "Target: first-live target only",
            "Operation: expose first-live route only",
            f"Result: {floor}",
        ])
    lines.extend([
        "Land(B1): first-live burden landed only",
        "R(H,Delta): HOLD - downstream material withheld",
        "HOLD: downstream material withheld without traversing continuation queue",
    ])
    return "\n".join(lines) + "\n"


def run_fixtures(skill_root: Path, output_dir: Path, repeat_stability: int, simulate_output_flag: bool) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    summaries: list[dict[str, Any]] = []

    for fixture in _fixture_dirs(skill_root):
        fixture_id = fixture.name
        summary = run_single(
            fixture / "input.md",
            output_dir / fixture_id / "run-1",
            skill_root,
            simulate_output_flag=simulate_output_flag,
        )
        summaries.append({"fixture": fixture_id, **summary})
        expected = _load_expected(skill_root, fixture_id)
        errors.extend([f"{fixture_id}: {error}" for error in _compare_expected(summary, expected)])
        if expected.get("shallow_output_must_fail"):
            route_plan = json.loads((output_dir / fixture_id / "run-1" / "route_plan.json").read_text(encoding="utf-8"))
            shallow_verdict = check_execution(route_plan, _shallow_first_burden_output(route_plan))
            write_json(output_dir / fixture_id / "run-1" / "shallow_output_verdict.json", shallow_verdict)
            if shallow_verdict.get("execution_fidelity") == "pass":
                errors.append(f"{fixture_id}: shallow first-burden-only output unexpectedly passed")
        for key in ("validation_fidelity", "reconstruction_fidelity"):
            if summary.get(key) != "pass":
                errors.append(f"{fixture_id}: {key} is {summary.get(key)}")
        if simulate_output_flag and summary.get("execution_fidelity") != "pass":
            errors.append(f"{fixture_id}: execution_fidelity is {summary.get('execution_fidelity')}")

    stability_fixture = skill_root / "tests" / "fixtures" / "stability-repetition" / "input.md"
    if stability_fixture.is_file():
        signatures: list[dict[str, Any]] = []
        for index in range(1, repeat_stability + 1):
            summary = run_single(
                stability_fixture,
                output_dir / "stability-repetition" / f"repeat-{index}",
                skill_root,
                simulate_output_flag=simulate_output_flag,
            )
            signatures.append(summary["route_state"])
        drift = [signature for signature in signatures if signature != signatures[0]]
        stability = {
            "repetitions": repeat_stability,
            "stable": not drift,
            "baseline": signatures[0],
            "drift_count": len(drift),
            "signatures": signatures,
        }
        write_json(output_dir / "stability-repetition" / "stability_summary.json", stability)
        if drift:
            errors.append(f"stability-repetition: routing drift across {repeat_stability} repetitions")
    else:
        errors.append("stability-repetition fixture missing")

    write_json(output_dir / "fixture_summary.json", {"summaries": summaries, "errors": errors})
    if errors:
        print("Level 3 fixture runner: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Level 3 fixture runner: PASS")
    print(f"Fixtures: {len(summaries)}")
    print(f"Stability repetitions: {repeat_stability}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the daee-epistemics Level 3 pilot pipeline.")
    parser.add_argument("--input", help="Single input.md path.")
    parser.add_argument("--output-dir", "--out", dest="output_dir", default="level3-runs", help="Output directory.")
    parser.add_argument("--skill-root", default=str(default_skill_root()), help="Skill package root.")
    parser.add_argument("--model-output", help="Existing model output to validate.")
    parser.add_argument("--simulate-output", action="store_true", help="Generate deterministic simulated output for validator testing.")
    parser.add_argument("--run-fixtures", action="store_true", help="Run all bundled Level 3 fixtures.")
    parser.add_argument("--repeat-stability", type=int, default=5, help="Stability repetitions for stability-repetition fixture.")
    args = parser.parse_args(argv)

    skill_root = Path(args.skill_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    if args.run_fixtures:
        return run_fixtures(skill_root, output_dir, args.repeat_stability, args.simulate_output)
    if not args.input:
        print("daee_level3: --input is required unless --run-fixtures is used", file=sys.stderr)
        return 2
    summary = run_single(
        Path(args.input),
        output_dir,
        skill_root,
        simulate_output_flag=args.simulate_output,
        model_output=Path(args.model_output) if args.model_output else None,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary.get("validation_fidelity") == "fail" or summary.get("reconstruction_fidelity") == "fail":
        return 1
    if summary.get("execution_fidelity") == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
