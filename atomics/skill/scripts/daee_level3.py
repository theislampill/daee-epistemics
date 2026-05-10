#!/usr/bin/env python3
"""One-command Level 3 covered-scope route runner for daee-epistemics.

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
from level3_lib import condition_satisfied, default_skill_root, owner_ids, route_state_signature, write_json
from reconstruct import reconstruct
from route import compute_route
from validate import validate as validate_route


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _json_text(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _hard_case_quality_guidance(route_plan: dict[str, Any]) -> str:
    feature_ids = {str(item) for item in route_plan.get("feature_ids", [])}
    continuation = route_plan.get("continuation_queue", [])
    hard_signals = {
        "feature.moral_tribunal",
        "feature.imported_criterion",
        "feature.accountability_compression",
        "feature.coercive_guidance_demand",
        "feature.criterion_bearing_source_worldview",
        "feature.source_substantiation_request",
        "feature.mercy_worthiness_protest",
        "feature.worldview_refutation_request",
        "feature.predication_confusion",
        "feature.attribute_resemblance",
        "feature.false_resemblance",
        "feature.deformation_signal",
        "feature.necessary_knowledge_shubhah",
        "feature.grief_register",
        "feature.trauma_register",
        "feature.imported_tribunal_pressure",
    }
    hard_case = (len(continuation) >= 2 or len(route_plan.get("first_live", [])) > 1) and bool(feature_ids.intersection(hard_signals))
    source_requested = bool(feature_ids.intersection({"feature.source_substantiation_request", "feature.source_request"}))
    worldview_live = bool(feature_ids.intersection({"feature.criterion_bearing_source_worldview", "feature.opponent_worldview_frame"}))
    if not hard_case and not source_requested and not worldview_live:
        return ""

    lines = [
        "Hard-case qualitative execution floor:",
        "- Do not optimize for the smallest checker-compliant answer. Marker presence is not execution.",
        "- A non-PARTIAL hard/compound/deformed answer must be burden-complete, owner-floor faithful, source-operative where needed, and restorative enough for a da'i to use.",
        "- This applies across moral protest, imported-criterion, higher-order reason/authority, transmission/testimony, predication/attribute, source-worldview transfer, necessary-knowledge, and grief/register cases.",
        "- Each routed owner may carry pressure_dimensions in the route plan. Land those dimensions inside that owner's local Target/Operation/Result window, or mark PARTIAL with the missing dimension.",
        "- Every executed owner gets its own submove marker before its owner-floor, such as `B1.s1:` then `B1.s2:` for two first-live owners. Do not merge multiple owners into one `B1.s` summary.",
        "- The Target line for every owner must quote or closely repeat at least one route input span for that burden. If the owner window has no input-anchor pressure, the burden is PARTIAL.",
        "- Within each executed burden, split materially active mechanisms into visible operative submoves under the routed owner instead of compressing them into one generic Target/Operation/Result paragraph.",
        "- Target/Operation/Result must pressure the input's actual premise, criterion, warrant, or source-worldview role; generic route-proving prose is PARTIAL.",
        "- In hard/compound cases, include a visible `Hidden Premises` section and a burden-local `Core Formulation` before owner execution. These are content units, not word-count padding.",
        "- Hidden Premises should surface the actual suppressed warrants as HP-1, HP-2, etc.; a single umbrella sentence is not enough for a hard/compound case.",
        "- Each burden's Core Formulation should name the exact claim-state being transformed before the owner submoves begin.",
        "- Each pressure_dimension should become its own `Pressure <dimension-id>:` execution line inside the owner window, with case-specific pressure rather than a dimension-name restatement.",
        "- A `Pressure <dimension-id>:` line may be paragraph-level when needed. It should carry the input anchor, the noetic control point, the corrective operation, and the state delta produced by that pressure.",
        "- If a pressure dimension includes required terms, treat them as source-function coverage, not word-count targets: the owner window must perform that doctrinal/noetic function or mark PARTIAL.",
        "- The diagnostic opening must do real case typing, not merely restate the route. In hard cases Layer A must name claim_level, pattern_profile, reason-category, concealment, deformation, DO-orient, current live noetic burden, source-status/noetic-frame if input-anchored, held/released burdens, and the gate/release decision.",
        "- Those Layer A fields are compact control state: they reconstruct how the surface discourse became a typed noetic burden before argument begins. A thin list of route labels is PARTIAL in hard cases.",
        "- Layer B may be longer than compact prose when the burden needs it. Compactness removes padding and source parade; it does not remove warranted diagnosis, source operation, or restoration force.",
    ]
    if source_requested:
        lines.extend([
            "- Because the input explicitly asks for sources, include direct quoted or precisely cited Qur'an/hadith evidence where it performs diagnostic or restorative work.",
            "- For each operative source, quote enough of the text to make its mechanism visible, then immediately explain what burden it lands. Do not use bare citation labels as source padding.",
            "- Put operative source texts on visually distinct blockquote lines beginning with `>`, using `Qur'an`, `hadith`, `Bukhari`, `Muslim`, or a surah/ayah citation on the same quoted line. Inline paraphrases alone are PARTIAL for source-request burdens.",
            "- Put those quote lines under an `Operative source deployment:` label inside the burden where the source lands.",
            "- Do not concentrate all source texts in the final restoration. When a routed pressure dimension is source-operative, the quote belongs in that owner submove and must be explained there.",
            "- Source operation should follow the burden it governs: accountability texts land accountability, guidance texts land guidance, reason/proof texts land reason-order, source-frame texts land criterion/source consequences, and restoration texts land mercy/justice/worship-worthiness.",
            "- For source-request hard cases, cover the source functions that the route actually calls for. Do not use one generic proof text to stand in for hujjah, fitrah/ayat, guidance/non-compulsion, mercy/justice, repentance, and worship-worthiness if those are separate pressure dimensions.",
            "- Include hadith where a routed burden turns on prophetic clarification, fitrah, repentance, mercy, or accountable practice and a directly operative hadith is available; otherwise do not pad.",
            "- If source deployment is held by a valid gate, say which gate holds it and what remains live; otherwise a citation-thin answer is PARTIAL.",
        ])
    if worldview_live:
        lines.extend([
            "- Treat source-status and personal identity as non-operative for ad hominem judgment, but treat an input-anchored worldview frame as operative when it supplies the criterion or tribunal.",
            "- Source-worldview analysis tied to input spans is FPD/M8 work, not source parade. Dismantle the criterion-bearing belief structure without making interior motive claims.",
        ])
    lines.extend([
        "- The final restoration must do more than summarize. It should convert the cleared burdens into a da'wah-facing invitation and worship-worthiness re-ordering.",
        "- Hard cases with P1/final restoration require a separate `Restorative Response` section before `Closing Formulation`; closure must not do all restorative work by itself.",
        "- Include a compact `TTP/operator trace` after the burden traversal to show which owner operations actually transformed the state.",
        "- If you cannot meet this qualitative floor in the current runtime, mark PARTIAL and name the first missing burden or submove.",
    ])
    return "\n".join(lines) + "\n\n"


def _short_span_list(spans: list[Any], *, limit: int = 4) -> str:
    texts: list[str] = []
    for span in spans:
        if not isinstance(span, dict):
            continue
        text = " ".join(str(span.get("text", "")).split())
        if text and text not in texts:
            texts.append(text)
        if len(texts) >= limit:
            break
    return "; ".join(f'"{text}"' for text in texts) if texts else "no explicit span listed"


def _dimension_line(dimension: dict[str, Any], route_feature_ids: set[str]) -> str:
    label = str(dimension.get("label") or dimension.get("id") or "pressure dimension")
    dim_id = str(dimension.get("id") or label)
    required_tokens = ", ".join(str(token) for token in dimension.get("requires_any", [])[:6])
    required_all = ", ".join(str(token) for token in dimension.get("requires_all", [])[:6])
    source_quote_conditions = {str(item) for item in dimension.get("source_quote_when_features", [])}
    quote_required = bool(route_feature_ids.intersection(source_quote_conditions))
    suffix = "; blockquoted operative source required" if quote_required else ""
    required_text = f"; required coverage: {required_all}" if required_all else ""
    return f"{dim_id}: {label}; pressure terms: {required_tokens}{required_text}{suffix}"


def _dimension_active(dimension: dict[str, Any], route_feature_ids: set[str]) -> bool:
    conditions = [str(condition) for condition in dimension.get("when_features", [])]
    if not conditions:
        return True
    return any(condition_satisfied(condition, route_feature_ids) for condition in conditions)


def _owner_execution_checklist(route_plan: dict[str, Any]) -> str:
    route_feature_ids = {str(item) for item in route_plan.get("feature_ids", [])}
    lines = [
        "Owner execution checklist (binding, not public commentary):",
        "- Use this checklist to execute the response; do not print raw JSON or call it a checklist in the final answer.",
        "- For each row, emit the named B.s marker before `Owner-floor`, quote one listed input anchor in `Target:`, land every pressure dimension as `Pressure <dimension-id>:` inside `Operation:`/`Result:`, and add a `>` operative source quote where marked.",
    ]
    first_live_burden = route_plan.get("first_live_burden")
    if isinstance(first_live_burden, dict):
        steps: list[tuple[int, dict[str, Any]]] = [(1, first_live_burden)]
    else:
        steps = [(1, {
            "owners": route_plan.get("first_live", []),
            "input_spans": [],
            "land_requirements": route_plan.get("land_requirements", []),
        })]
    for index, entry in enumerate(route_plan.get("continuation_queue", []), start=2):
        if isinstance(entry, dict):
            steps.append((index, entry))

    for burden_index, step in steps:
        owners = [owner for owner in step.get("owners", []) if isinstance(owner, dict)]
        if not owners:
            continue
        lines.append(f"- B{burden_index}: anchors: {_short_span_list(step.get('input_spans', []))}")
        for submove_index, owner in enumerate(owners, start=1):
            owner_id = str(owner.get("id", "unknown-owner"))
            dimensions = [
                _dimension_line(dimension, route_feature_ids)
                for dimension in owner.get("pressure_dimensions", [])
                if isinstance(dimension, dict) and _dimension_active(dimension, route_feature_ids)
            ]
            dimension_text = " | ".join(dimensions) if dimensions else "no pressure dimensions listed; execute owner floor literally"
            floor = "; ".join(str(item) for item in owner.get("land_requires", [])) or "owner-specific floor"
            lines.append(
                f"  - B{burden_index}.s{submove_index} owner `{owner_id}`; floor: {floor}; pressure: {dimension_text}"
            )
    return "\n".join(lines) + "\n\n"


def execution_prompt(route_plan: dict[str, Any], reconstruction: dict[str, Any]) -> str:
    first_live = owner_ids(route_plan.get("first_live", []))
    held = owner_ids(route_plan.get("held", []))
    deferred = owner_ids(route_plan.get("deferred", []))
    continuation = route_plan.get("continuation_queue", [])
    hard_case_guidance = _hard_case_quality_guidance(route_plan)
    owner_checklist = _owner_execution_checklist(route_plan)
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

Burden-local state envelopes:
{_json_text([route_plan.get("first_live_burden", {}).get("state_envelope", {})] + [entry.get("state_envelope", {}) for entry in continuation])}

Closure gate:
{_json_text(route_plan.get("closure_gate", {}))}

{hard_case_guidance}Anti-checker-shaped execution rule:
- Passing `check_execution.py` is necessary but not sufficient for hard cases.
- Do not write a route-shaped answer whose main achievement is that every label appears.
- `Owner-floor`, `Target`, `Operation`, and `Result` are control surfaces for substantive work: each must visibly narrow, expose, disambiguate, test, or restore the live claim-state.
- A hard case fails qualitatively if it contains all route labels but lacks direct burden pressure, operative source deployment when requested, and restoration force.

{owner_checklist}Pre-final self-check:
- Before finalizing, verify every routed owner has a distinct `B<N>.s<M>:` marker, `Owner-floor`, `Target`, `Operation`, and `Result` in the same burden.
- Verify every `Target:` quotes or closely repeats a listed input anchor for that burden.
- Verify every pressure dimension in the checklist has its own `Pressure <dimension-id>:` line and is visibly landed by specific claim-state work, not by saying "pressure dimensions satisfied."
- If a checklist row says blockquoted operative source required, include a `>` quote line inside that same owner window and immediately explain what it lands.
- Verify source quotes are not parked in a global list: each quote should sit inside the burden/owner that uses it and be followed by its diagnostic or restorative operation.
- Verify hard/compound output includes HP-numbered Hidden Premises, Core Formulation content units, a TTP/operator trace, and a separate Restorative Response where restoration is routed.
- If any row cannot be met, mark PARTIAL and name the missing burden/owner/dimension instead of closing.

Required execution shape:
1. Emit `Layer A - Compact DSL/IR Header [Burden 1]` before executing the first-live owner(s).
   For hard/compound/deformed cases, include compact field lines for:
   `claim_level`, `pattern_profile`, `reason-category`, `concealment`, `deformation`,
   `DO-orient`, `current live noetic burden`, `source-status/noetic-frame`, `held/released`,
   and `gate/release decision`. These are not raw IR; they are the reconstruction-faithful
   noetic control frame that licenses Layer B.
   It must also name selected owner(s), held/deferred/rejected alternatives, release condition,
   and governance verdict.
2. Emit `Layer B - Governed Response [Burden 1]`.
3. In hard/compound cases, emit `Hidden Premises` and `Core Formulation` before the first owner-floor.
4. For each first-live owner, emit owner-floor evidence as:
   B1.s<M>: execute first-live owner <owner-id>
   Owner-floor: <owner-id> - <owner-specific floor>
   Target: <input-grounded target that quotes or closely repeats a listed route input span>
   Operation: <case-specific operation>
   Pressure <dimension-id>: <case-specific pressure execution for each listed pressure dimension>
   Result: <changed claim-state>
   If the route owner lists pressure_dimensions, land each dimension in this local
   Target/Operation/Result window; do not rely on the owner label itself to satisfy it.
5. Render Land(B1) -> R(H,Delta) after all B1.s<M> owner submoves are complete.
6. If the continuation queue is non-empty, treat it as a planned route, not an unconditional command.
   After each Land(B<N>) and R(H,Delta), re-read the state before B<N+1>.
   Continue only if the next queued burden remains input-anchored and licensed.
   If it is no longer live or is blocked, mark HOLD, SKIP, PARTIAL, or bounded-reroute need with the state-delta reason.
7. For each queued burden that remains licensed:
   - emit `Layer A - Compact DSL/IR Header [Burden N]` before Layer B;
   - cite the input span(s), noetic frame update, held/released burden state, and release condition still satisfied after R(H,Delta);
   - emit `Layer B - Governed Response [Burden N]`;
   - in hard/compound cases, emit `Core Formulation` before owner execution for this burden;
   - before each queued owner, emit `B<N>.s<M>: execute queued owner <owner-id>`;
   - for each queued owner, emit exactly `Owner-floor: <owner-id> - <owner-specific floor>`;
   - then emit Target:, Operation:, and Result: lines for the same owner;
   - land any listed pressure_dimensions as separate `Pressure <dimension-id>:` lines inside those same Target/Operation/Result lines;
   - render Land(B<N>) -> R(H,Delta) after all B<N>.s<M> owner submoves are complete;
   - say what the prior burden cleared and why this burden is now licensed.
8. After traversal, emit `TTP/operator trace` naming each executed owner and its state change.
9. If restoration owner P1-fitrah-restoration executed, emit `Restorative Response` before `Closing Formulation`.
10. Do not execute held/deferred owners outside first-live or continuation_queue.
11. Do not pad: if a queued burden lacks a real input span, mark PARTIAL instead of inventing it.
12. Do not emit Closing Formulation unless the closure gate is satisfied and R(H,Delta) names no remaining input-anchored burdens.
13. If transformer limits prevent a queued burden, emit a visible PARTIAL banner naming the exact missing queue entry.
"""


def simulated_output(route_plan: dict[str, Any]) -> str:
    lines = [
        "# Level 3 Simulated Validator Output",
        "",
        "Layer A - Compact DSL/IR Header [Burden 1]",
        f"- current live noetic burden: {route_plan.get('live_burden')}",
        f"- selected owner(s): {', '.join(owner_ids(route_plan.get('first_live', [])))}",
        f"- held/deferred/rejected alternatives: {', '.join(owner_ids(route_plan.get('held', [])) + owner_ids(route_plan.get('deferred', [])) + owner_ids(route_plan.get('rejected', []))) or 'none'}",
        f"- release condition / governance verdict: {route_plan.get('governance_verdict')}",
        "",
        "Layer B - Governed Response [Burden 1]",
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
            f"Layer A - Compact DSL/IR Header [Burden {burden_index}]",
            f"- current live noetic burden: {entry.get('name')}",
            "- active deformation / pattern signals: span-backed continuation burden",
            f"- selected owner(s): {', '.join(owner_ids(entry.get('owners', [])))}",
            "- held/deferred/rejected alternatives: rechecked from route plan",
            f"- release condition / governance verdict: {', '.join(str(value) for value in entry.get('release_conditions', []))}",
            "",
            f"Layer B - Governed Response [Burden {burden_index}]",
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

    if blocked:
        smoke_kind = "route-blocked"
    elif simulate_output_flag:
        smoke_kind = "simulated-route-check"
    elif model_output is not None:
        smoke_kind = "model-execution-check"
    else:
        smoke_kind = "route-generation-only"

    summary = {
        "smoke_kind": smoke_kind,
        "input": str(input_path),
        "output_dir": str(output_dir),
        "route_state": route_state_signature(route_plan),
        "validation_fidelity": validation.get("validation_fidelity"),
        "reconstruction_fidelity": reconstruction.get("reconstruction_fidelity"),
        "execution_fidelity": execution.get("execution_fidelity") if execution else "not-run",
        "execution_state_envelopes": execution.get("state_envelopes", []) if execution else [],
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def _fixture_dirs(skill_root: Path) -> list[Path]:
    fixtures_root = skill_root / "tests" / "fixtures"
    if not fixtures_root.is_dir():
        return []
    return sorted(path for path in fixtures_root.iterdir() if (path / "input.md").is_file())


def _load_expected(skill_root: Path, fixture_id: str) -> dict[str, Any] | None:
    path = skill_root / "tests" / "expected" / f"{fixture_id}.json"
    if not path.is_file():
        return None
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


def _closure_matcher_regressions() -> list[str]:
    errors: list[str] = []

    def owner(owner_id: str, pressure_dimensions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        item = {"id": owner_id, "land_requires": [f"{owner_id} owner-floor result"]}
        if pressure_dimensions is not None:
            item["pressure_dimensions"] = pressure_dimensions
        return item

    def queue_entry(
        name: str,
        owner_id: str,
        pressure_dimensions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "name": name,
            "owners": [owner(owner_id, pressure_dimensions)],
            "input_spans": [{"text": f"span for {name}"}],
            "land_requirements": [{"owner": owner_id, "requires": [f"{owner_id} owner-floor result"]}],
        }

    b3_plan = {
        "live_burden": "synthetic imported criterion burden",
        "governance_verdict": "RECURSE",
        "first_live": [owner("foreign-premise-detection")],
        "continuation_queue": [
            queue_entry("reason-repair", "V2-reconstituting-reason"),
            queue_entry("moral-tribunal-check", "M8-reductio"),
        ],
        "held": [],
        "deferred": [],
    }
    b3_output = """# Synthetic route execution
Layer A - Compact DSL/IR Header [Burden 1]
- current live noetic burden: synthetic imported criterion burden
- selected owner(s): foreign-premise-detection
- held/deferred/rejected alternatives: V2-reconstituting-reason, M8-reductio
- release condition / governance verdict: RECURSE
Layer B - Governed Response [Burden 1]
First Burden: synthetic imported criterion burden
B1.s1: execute first-live owner
Owner-floor: foreign-premise-detection - foreign-premise-detection owner-floor result
Target: first span
Operation: expose the imported criterion
Result: foreign-premise-detection owner-floor result
Land(B1): first burden landed
R(H,Delta): RECURSE - next span-backed burden released

Layer A - Compact DSL/IR Header [Burden 2]
- current live noetic burden: reason-repair
- selected owner(s): V2-reconstituting-reason
- held/deferred/rejected alternatives: M8-reductio
- release condition / governance verdict: B1 landed; B2 remains input-anchored and licensed
Layer B - Governed Response [Burden 2]
Second Burden: reason-repair
Operative Submove: execute queued owner
Owner-floor: V2-reconstituting-reason - V2-reconstituting-reason owner-floor result
Target: second span
Operation: repair the proof-status inversion
Result: V2-reconstituting-reason owner-floor result
Land(B2): second burden landed
R(H,Delta): RECURSE - next span-backed burden released

Layer A - Compact DSL/IR Header [Burden 3]
- current live noetic burden: moral-tribunal-check
- selected owner(s): M8-reductio
- held/deferred/rejected alternatives: none
- release condition / governance verdict: B2 landed; B3 remains input-anchored and licensed
Layer B - Governed Response [Burden 3]
Third Burden: moral-tribunal-check
Operative Submove: execute queued owner
Owner-floor: M8-reductio - M8-reductio owner-floor result
Target: third span
Operation: check the moral tribunal against its own premise
Result: M8-reductio owner-floor result
Land(B3): third burden landed
R(H,Delta): RECURSE - no remaining input-anchored burdens
Closing Formulation: closure licensed; no remaining input-anchored burden.
"""
    b3_verdict = check_execution(b3_plan, b3_output)
    if b3_verdict.get("execution_fidelity") != "pass":
        errors.append(f"closure-regression B3 ordinal output failed: {b3_verdict}")

    b3_missing_final = b3_output.split("Third Burden:", 1)[0] + (
        "R(H,Delta): HOLD - final queued burden omitted.\n"
    )
    b3_missing_verdict = check_execution(b3_plan, b3_missing_final)
    if b3_missing_verdict.get("execution_fidelity") == "pass":
        errors.append("closure-regression missing B3 content unexpectedly passed")

    b3_missing_layer_a = b3_output.replace("Layer A - Compact DSL/IR Header [Burden 2]", "Diagnostic header omitted [Burden 2]")
    b3_missing_layer_verdict = check_execution(b3_plan, b3_missing_layer_a)
    if b3_missing_layer_verdict.get("execution_fidelity") == "pass":
        errors.append("layer-regression missing B2 Layer A unexpectedly passed")

    b3_detached_owners = """# Synthetic detached marker route execution
Owner-floor: foreign-premise-detection - foreign-premise-detection owner-floor result
Owner-floor: V2-reconstituting-reason - V2-reconstituting-reason owner-floor result
Owner-floor: M8-reductio - M8-reductio owner-floor result

Layer A - Compact DSL/IR Header [Burden 1]
- current live noetic burden: synthetic imported criterion burden
- selected owner(s): foreign-premise-detection
Layer B - Governed Response [Burden 1]
First Burden: synthetic imported criterion burden
B1.s1: execute first-live owner
Target: first span
Operation: expose the imported criterion
Result: foreign-premise-detection owner-floor result
Land(B1): first burden landed
R(H,Delta): RECURSE - next span-backed burden released

Layer A - Compact DSL/IR Header [Burden 2]
- current live noetic burden: reason-repair
- selected owner(s): V2-reconstituting-reason
Layer B - Governed Response [Burden 2]
Second Burden: reason-repair
Target: second span
Operation: repair the proof-status inversion
Result: V2-reconstituting-reason owner-floor result
Land(B2): second burden landed
R(H,Delta): RECURSE - next span-backed burden released

Layer A - Compact DSL/IR Header [Burden 3]
- current live noetic burden: moral-tribunal-check
- selected owner(s): M8-reductio
Layer B - Governed Response [Burden 3]
Third Burden: moral-tribunal-check
Target: third span
Operation: check the moral tribunal against its own premise
Result: M8-reductio owner-floor result
Land(B3): third burden landed
R(H,Delta): RECURSE - no remaining input-anchored burdens
Closing Formulation: closure licensed; no remaining input-anchored burden.
"""
    b3_detached_verdict = check_execution(b3_plan, b3_detached_owners)
    if b3_detached_verdict.get("execution_fidelity") == "pass":
        errors.append("structural-attachment detached owner-floor markers unexpectedly passed")
    retry_prompt = str(b3_detached_verdict.get("retry_prompt", ""))
    if "B1" not in retry_prompt or "foreign-premise-detection" not in retry_prompt:
        errors.append("structural-attachment retry prompt lost failed burden/owner identity")

    b3_single_reread = b3_output.replace(
        "R(H,Delta): RECURSE - next span-backed burden released",
        "State read: next span-backed burden released",
        2,
    )
    b3_single_reread_verdict = check_execution(b3_plan, b3_single_reread)
    if b3_single_reread_verdict.get("execution_fidelity") == "pass":
        errors.append("structural-attachment multi-burden output with one R(H,Delta) unexpectedly passed")

    b3_no_reread = b3_output.replace("R(H,Delta): RECURSE - next span-backed burden released\n\nLayer A - Compact DSL/IR Header [Burden 2]", "Layer A - Compact DSL/IR Header [Burden 2]", 1)
    b3_no_reread_verdict = check_execution(b3_plan, b3_no_reread)
    if b3_no_reread_verdict.get("execution_fidelity") == "pass":
        errors.append("layer-regression B2 without prior R(H,Delta) unexpectedly passed")

    b3_valid_hold = """# Synthetic governed hold
Layer A - Compact DSL/IR Header [Burden 1]
- current live noetic burden: synthetic imported criterion burden
- selected owner(s): foreign-premise-detection
- held/deferred/rejected alternatives: V2-reconstituting-reason, M8-reductio
- release condition / governance verdict: RECURSE
Layer B - Governed Response [Burden 1]
First Burden: synthetic imported criterion burden
B1.s1: execute first-live owner
Owner-floor: foreign-premise-detection - foreign-premise-detection owner-floor result
Target: first span
Operation: expose the imported criterion
Result: foreign-premise-detection owner-floor result
Land(B1): first burden landed
R(H,Delta): RECURSE - next span-backed burden rechecked

Layer A - Compact DSL/IR Header [Burden 2]
- current live noetic burden: reason-repair
- release condition / governance verdict: HOLD because refreshed state shows the queued burden is not licensed after B1 landed
- held/deferred/rejected alternatives: V2-reconstituting-reason held by state delta
HOLD: B2 is held with a state-delta reason, not mechanically executed.

Layer A - Compact DSL/IR Header [Burden 3]
- current live noetic burden: moral-tribunal-check
- release condition / governance verdict: HOLD because refreshed state says M8-reductio is not licensed after B2 hold
- held/deferred/rejected alternatives: M8-reductio held by state delta
HOLD: B3 / M8-reductio is held with a state-delta reason; next-live state remains capability-bound.
"""
    b3_valid_hold_verdict = check_execution(b3_plan, b3_valid_hold)
    if b3_valid_hold_verdict.get("execution_fidelity") == "fail":
        errors.append(f"layer-regression valid governed hold failed: {b3_valid_hold_verdict}")

    b5_plan = {
        "live_burden": "synthetic multi-burden route",
        "governance_verdict": "RECURSE",
        "first_live": [owner("foreign-premise-detection")],
        "continuation_queue": [
            queue_entry("second-loop", "do-second-loop"),
            queue_entry("reason-repair", "V2-reconstituting-reason"),
            queue_entry("internal-check", "M8-reductio"),
            queue_entry("restoration", "P1-fitrah-restoration"),
        ],
        "held": [],
        "deferred": [],
    }
    b5_output = """# Synthetic five-burden route execution
Layer A - Compact DSL/IR Header [Burden 1]
- current live noetic burden: first-live burden
- selected owner(s): foreign-premise-detection
- held/deferred/rejected alternatives: queued owners
- release condition / governance verdict: RECURSE
Layer B - Governed Response [Burden 1]
First Burden: first-live burden
B1.s1: execute first-live owner
Owner-floor: foreign-premise-detection - foreign-premise-detection owner-floor result
Target: first span
Operation: expose the imported criterion
Result: foreign-premise-detection owner-floor result
Land(B1): first burden landed
R(H,Delta): RECURSE - next burden released

Layer A - Compact DSL/IR Header [Burden 2]
- current live noetic burden: second-loop
- selected owner(s): do-second-loop
- release condition / governance verdict: B1 landed; B2 remains licensed
Layer B - Governed Response [Burden 2]
Second Burden: second-loop
Operative Submove: execute queued owner
Owner-floor: do-second-loop - do-second-loop owner-floor result
Target: second span
Operation: run the second loop
Result: do-second-loop owner-floor result
Land(B2): second burden landed
R(H,Delta): RECURSE - next burden released

Layer A - Compact DSL/IR Header [Burden 3]
- current live noetic burden: reason-repair
- selected owner(s): V2-reconstituting-reason
- release condition / governance verdict: B2 landed; B3 remains licensed
Layer B - Governed Response [Burden 3]
Third Burden: reason-repair
Operative Submove: execute queued owner
Owner-floor: V2-reconstituting-reason - V2-reconstituting-reason owner-floor result
Target: third span
Operation: repair the proof-status inversion
Result: V2-reconstituting-reason owner-floor result
Land(B3): third burden landed
R(H,Delta): RECURSE - next burden released

Layer A - Compact DSL/IR Header [Burden 4]
- current live noetic burden: internal-check
- selected owner(s): M8-reductio
- release condition / governance verdict: B3 landed; B4 remains licensed
Layer B - Governed Response [Burden 4]
Fourth Burden: internal-check
Operative Submove: execute queued owner
Owner-floor: M8-reductio - M8-reductio owner-floor result
Target: fourth span
Operation: test the internal criterion
Result: M8-reductio owner-floor result
Land(B4): fourth burden landed
R(H,Delta): RECURSE - next burden released

Layer A - Compact DSL/IR Header [Burden 5]
- current live noetic burden: restoration
- selected owner(s): P1-fitrah-restoration
- release condition / governance verdict: B4 landed; B5 remains licensed
Layer B - Governed Response [Burden 5]
Fifth Burden: restoration
Operative Submove: execute queued owner
Owner-floor: P1-fitrah-restoration - P1-fitrah-restoration owner-floor result
Target: fifth span
Operation: restore the fitrah-facing landing
Result: P1-fitrah-restoration owner-floor result
Land(B5): fifth burden landed
R(H,Delta): RECURSE - no remaining input-anchored burdens
Closing Formulation: closure gate satisfied; remaining input-anchored burdens: none.
"""
    b5_verdict = check_execution(b5_plan, b5_output)
    if b5_verdict.get("execution_fidelity") != "pass":
        errors.append(f"closure-regression B5 ordinal output failed: {b5_verdict}")

    simple_plan = {
        "live_burden": "synthetic single burden",
        "governance_verdict": "STOP",
        "first_live": [owner("V2-reconstituting-reason")],
        "continuation_queue": [],
        "held": [],
        "deferred": [],
    }
    simple_output = """# Synthetic single-burden route execution
Burden 1: synthetic single burden
B1.s1: execute first-live owner
Owner-floor: V2-reconstituting-reason - V2-reconstituting-reason owner-floor result
Target: first span
Operation: repair the proof-status inversion
Result: V2-reconstituting-reason owner-floor result
Land(B1): first burden landed
R(H,Delta): STOP - no remaining input-anchored burden
Closing Formulation: no remaining input-anchored burden.
"""
    simple_verdict = check_execution(simple_plan, simple_output)
    if simple_verdict.get("execution_fidelity") != "pass":
        errors.append(f"closure-regression simple B1 output failed: {simple_verdict}")

    predication_hard_plan = {
        "feature_ids": ["term.trinity", "feature.predication_confusion", "feature.attribute_resemblance"],
        "live_burden": "synthetic predication and attribute burden",
        "governance_verdict": "RECURSE",
        "first_live": [
            owner(
                "M9-predication-mode",
                [
                    {
                        "id": "predication-mode",
                        "label": "predication mode named before verdict",
                        "requires_any": ["predication", "mode", "predicate", "equivocal", "category"],
                    }
                ],
            )
        ],
        "first_live_burden": {
            "name": "synthetic predication and attribute burden",
            "owners": [
                owner(
                    "M9-predication-mode",
                    [
                        {
                            "id": "predication-mode",
                            "label": "predication mode named before verdict",
                            "requires_any": ["predication", "mode", "predicate", "equivocal", "category"],
                        }
                    ],
                )
            ],
            "input_spans": [{"text": "The Trinity is three persons but one God, so predication seems incoherent."}],
            "land_requirements": [{"owner": "M9-predication-mode", "requires": ["predication mode named"]}],
        },
        "continuation_queue": [
            queue_entry(
                "attribute precision",
                "do-attribute-precision",
                [
                    {
                        "id": "predicate-identity-separation",
                        "label": "predicate terms separated from identity collapse",
                        "requires_any": ["predicate", "attribute", "identity", "collapse", "term"],
                    }
                ],
            ),
            queue_entry(
                "bila kayf anchor",
                "V8-bila-kayf-anchor",
                [
                    {
                        "id": "modality-blocked",
                        "label": "creaturely modality blocked",
                        "requires_any": ["modality", "how", "creaturely", "bila kayf", "without asking how"],
                    }
                ],
            ),
        ],
        "held": [],
        "deferred": [],
    }
    non_canary_thin_output = """# Synthetic non-canary hard route execution
Layer A - Compact DSL/IR Header [Burden 1]
- current live noetic burden: synthetic predication and attribute burden
- selected owner(s): M9-predication-mode
- release condition / governance verdict: RECURSE
Layer B - Governed Response [Burden 1]
First Burden: synthetic predication and attribute burden
B1.s1: execute first-live owner
Owner-floor: M9-predication-mode - predication mode named
Target: the claim is addressed.
Operation: perform the owner.
Result: owner-floor result.
Land(B1): first burden landed
R(H,Delta): RECURSE - next burden released

Layer A - Compact DSL/IR Header [Burden 2]
- current live noetic burden: attribute precision
- selected owner(s): do-attribute-precision
- release condition / governance verdict: B1 landed; B2 remains licensed
Layer B - Governed Response [Burden 2]
Second Burden: attribute precision
Operative Submove: execute queued owner
Owner-floor: do-attribute-precision - attribute/predicate terms separated from identity collapse
Target: the claim is addressed.
Operation: perform the owner.
Result: owner-floor result.
Land(B2): second burden landed
R(H,Delta): RECURSE - next burden released

Layer A - Compact DSL/IR Header [Burden 3]
- current live noetic burden: bila kayf anchor
- selected owner(s): V8-bila-kayf-anchor
- release condition / governance verdict: B2 landed; B3 remains licensed
Layer B - Governed Response [Burden 3]
Third Burden: bila kayf anchor
Operative Submove: execute queued owner
Owner-floor: V8-bila-kayf-anchor - creaturely modality blocked
Target: the claim is addressed.
Operation: perform the owner.
Result: owner-floor result.
Land(B3): third burden landed
R(H,Delta): RECURSE - no remaining input-anchored burdens
Closing Formulation: closure licensed; no remaining input-anchored burden.
"""
    non_canary_thin_verdict = check_execution(predication_hard_plan, non_canary_thin_output)
    if non_canary_thin_verdict.get("execution_fidelity") == "pass":
        errors.append("hard-case quality regression: generic checker-shaped predication output unexpectedly passed")

    return errors


def run_fixtures(
    skill_root: Path,
    output_dir: Path,
    repeat_stability: int,
    simulate_output_flag: bool,
    *,
    fail_on_partial: bool = False,
) -> int:
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
        if expected is None:
            errors.append(f"{fixture_id}: expected fixture file missing")
            continue
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
        if fail_on_partial:
            for key in ("validation_fidelity", "reconstruction_fidelity", "execution_fidelity"):
                if summary.get(key) in {"partial", "not-run"}:
                    errors.append(f"{fixture_id}: {key} is {summary.get(key)} under --fail-on-partial")

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

    errors.extend(_closure_matcher_regressions())

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
    parser = argparse.ArgumentParser(description="Run the daee-epistemics Level 3 covered-scope pipeline.")
    parser.add_argument("--input", help="Single input.md path.")
    parser.add_argument("--output-dir", "--out", dest="output_dir", default="level3-runs", help="Output directory.")
    parser.add_argument("--skill-root", default=str(default_skill_root()), help="Skill package root.")
    parser.add_argument("--model-output", help="Existing model output to validate.")
    parser.add_argument("--simulate-output", action="store_true", help="Generate deterministic simulated output for validator testing.")
    parser.add_argument("--run-fixtures", action="store_true", help="Run all bundled Level 3 fixtures.")
    parser.add_argument("--repeat-stability", type=int, default=5, help="Stability repetitions for stability-repetition fixture.")
    parser.add_argument(
        "--fail-on-partial",
        action="store_true",
        help="Fail when validation/reconstruction/execution is partial, not-run, or unvalidated.",
    )
    args = parser.parse_args(argv)

    skill_root = Path(args.skill_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    if args.run_fixtures:
        return run_fixtures(
            skill_root,
            output_dir,
            args.repeat_stability,
            args.simulate_output,
            fail_on_partial=args.fail_on_partial,
        )
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
    if args.fail_on_partial:
        for key in ("validation_fidelity", "reconstruction_fidelity", "execution_fidelity"):
            if summary.get(key) in {"partial", "not-run"}:
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
