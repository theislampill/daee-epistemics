#!/usr/bin/env python3
"""Validate hard-compound MRP smoke outputs.

This checker is stricter than the ordinary MRP fixture checker. It is meant for
large live-output smokes where MRP must govern the burden economy between
burdens, not merely appear as a final block.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


KB = 1024
BASE_KB = 8
FULL_BURDEN_KB = 10
PARTIAL_BURDEN_KB = 5
MRP_KB = 4
CLOSURE_KB = 8
RESTORATIVE_KB = 10
SMOKE6_SERIOUS_ANDON_KB = 60
SMOKE6_CALIBRATED_MIN_KB = 75
BURDEN_RE = re.compile(r"(?im)^\s*(?:Layer A\s+[-—]\s+)?Burden\s+(?P<num>\d+)\b|^\s*live noetic burden\s*:.*\bB[1-9]\b")
MRP_RE = re.compile(r"(?im)^\s*\[Mid-Reread Pressure\]\s*$")
LAND_RE = re.compile(r"(?im)^\s*Land\((?:B1|¹B|1B)\)\s*:")
ROUTE_RE = re.compile(r"(?im)^\s*Route\s*:\s*(?P<route>STOP|HOLD|RECURSE|LoopBreak\(∇×T\))\b")
GRAPH_EDGE_RE = re.compile(r"(?im)^\s*Graph delta\s*:\s*(?P<body>.*(?:B1|¹B).*(?:->|→).*(?:B2|B3|B4).*)$")
RESULTANT_RE = re.compile(r"(?im)^\s*MRP resultant\s*:\s*(?P<body>\S.*)$")
PRESSURE_SLOT_RE = re.compile(
    r"(?im)^\s*-\s*(freeze-landed-move|dependency-tug|hidden-framework-recoil|"
    r"entailment-pressure|doubt-churn-guard|reorientation-reminder)\s*:\s*\S"
)
SUBMOVE_RE = re.compile(r"(?im)^\s*(?:Operative Submove|Submove|[¹1]B[₁₂₃₄₅₆₇₈₉0-9]|\s*Target\s*:)")
CLOSURE_RE = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?Closure/Reconstruction Witness\b|^\s*(?:#{1,6}\s*)?Closure Audit\b")
RESTORATIVE_RE = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?Restorative Response\b")
Closing_RE = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?Closing Formulation\b")
MRP_RESULTANTS_RE = re.compile(r"(?im)^\s*MRP resultants?\s*:")
ROOT_MARKER_RE = re.compile(r"\bB\d+\b\s*\(root\)")
INITIAL_RE = re.compile(r"(?im)^\s*Initial burden set\s*:\s*\[(?P<body>[^\]]+)\]")
TERMINAL_RE = re.compile(r"(?im)^\s*Terminal states\s*:")
LAYER_B_RE = re.compile(r"(?im)^\s*(?:Layer B\b|governed Layer B\b)")
DIVERGENCE_RE = re.compile(r"(?im)^\s*(?:∇·B|del[- ]dot\s*B)\s*:\s*(?:neutral|non-neutral)\b")
CURL_RE = re.compile(r"(?im)^\s*(?:∇×κ|del[- ]cross\s*kappa)\s*:\s*(?:null|resolved|non-null)\b")
CLOSURE_FIELD_RE = re.compile(r"(?im)^\s*(?:𝒞\(Ψᴺ\)|C\(PsiN\))\s*:\s*coverage_complete\s*=\s*(?:true|false)\s*;")
TRANSFER_RE = re.compile(
    r"(?im)^\s*T_lang\s*:\s*(?:Ψᴺ|PsiN)\s*(?:⇢|->)\s*(?:Ψᴵ|PsiI)\s*:\s*"
    r".*(?:partial coupling|language-mediated|no guaranteed uptake)"
)
OWNER_SUBMOVE_RE = re.compile(
    r"(?im)^\s*(?:"
    r"B\d+[_\.-]?\d+|"
    r"\d+B\d+|"
    r"[¹²³⁴⁵⁶⁷⁸⁹]B[₁₂₃₄₅₆₇₈₉0-9]+|"
    r")\s*\[[A-Za-z][A-Za-z0-9/-]*\]\s*(?:[-—:])"
)
BAD_OWNER_LABEL_RE = re.compile(r"(?im)^\s*B\d+[_\.-]?\d+\s*\[[^\]\r\n]*\s+[^\]\r\n]*\]\s*(?:[-—:])")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def line_pos(text: str, pattern: re.Pattern[str]) -> int | None:
    match = pattern.search(text)
    return match.start() if match else None


def unique_burdens(text: str) -> set[str]:
    found = {f"B{match.group('num')}" for match in BURDEN_RE.finditer(text) if match.groupdict().get("num")}
    initial = INITIAL_RE.search(text)
    if initial:
        found.update(re.findall(r"\bB\d+\b", initial.group("body")))
    found.update(re.findall(r"\blive noetic burden\s*:.*?\b(B\d+)\b", text, flags=re.IGNORECASE | re.DOTALL))
    return found


def explicit_submove_count(text: str) -> int:
    return len(OWNER_SUBMOVE_RE.findall(text))


def terminal_states(text: str) -> dict[str, str]:
    states: dict[str, str] = {}
    in_states = False
    for line in text.splitlines():
        if re.match(r"(?i)^\s*Terminal states\s*:", line):
            in_states = True
            continue
        if in_states and not line.strip():
            break
        if in_states and re.match(r"(?i)^\s*(?:Burden dependency graph|∇|C\(|𝒞|T_lang|Restorative Response|Closing)", line):
            break
        if not in_states:
            continue
        match = re.match(r"^\s*(?:[-*]\s*)?(B\d+)\s*:\s*([A-Za-z-]+)\b", line)
        if match:
            states[match.group(1)] = match.group(2)
    return states


def estimated_minimum_bytes(text: str) -> tuple[int, dict[str, tuple[int, int, bool, str]]]:
    burdens = unique_burdens(text)
    states = terminal_states(text)
    mrp_count = len(MRP_RE.findall(text))
    submove_count = explicit_submove_count(text)
    layer_b_count = len(LAYER_B_RE.findall(text))
    has_closure = bool(CLOSURE_RE.search(text))
    has_restorative = bool(RESTORATIVE_RE.search(text))

    partial_states = {"held-with-reason", "carried-PARTIAL", "carried-RECURSE"}
    full_count = 0
    partial_count = 0
    for burden in burdens:
        state = states.get(burden, "")
        if state in partial_states:
            partial_count += 1
        else:
            full_count += 1

    rows: dict[str, tuple[int, int, bool, str]] = {}
    rows["governed surface + Layer A"] = (1, BASE_KB, "NOETIC FIELD EXECUTION" in text and "Layer A" in text, "")
    required_submoves = 15 if len(burdens) >= 5 else max(3, len(burdens) * 3)
    rows["Layer B operation bodies"] = (
        layer_b_count,
        0,
        layer_b_count > 0,
        "required for hard-compound full traversal; mass included in burden cycles",
    )
    rows["explicit submove / owner activations"] = (
        submove_count,
        0,
        submove_count >= required_submoves,
        f"required>={required_submoves} when full traversal is claimed; mass included in burden cycles",
    )
    rows["full burden cycles"] = (full_count, full_count * FULL_BURDEN_KB, full_count > 0, f"burdens={sorted(burdens)}")
    rows["partial / held burdens"] = (partial_count, partial_count * PARTIAL_BURDEN_KB, partial_count > 0, f"terminal={states}")
    rows["MRP invocations"] = (mrp_count, mrp_count * MRP_KB, mrp_count > 0, "")
    rows["graph / field_witness accounting"] = (1, 0, "Graph delta:" in text or "Burden dependency graph:" in text or "field_witness" in text, "")
    rows["closure witness"] = (1 if has_closure else 0, CLOSURE_KB if has_closure else 0, has_closure, "")
    rows["restorative response"] = (1 if has_restorative else 0, RESTORATIVE_KB if has_restorative else 0, has_restorative, "")

    total_kb = BASE_KB + full_count * FULL_BURDEN_KB + partial_count * PARTIAL_BURDEN_KB + mrp_count * MRP_KB
    if has_closure:
        total_kb += CLOSURE_KB
    if has_restorative:
        total_kb += RESTORATIVE_KB
    return total_kb * KB, rows


def calibrated_mass_floor_bytes(text: str, component_estimate: int) -> int:
    """Return the deterministic fail floor, after empirical/audit calibration.

    The component estimate remains visible as an execution-cost audit, but Smoke-6-shaped
    hard-compound outputs were calibrated against old successful outputs and the E/F/G/H
    audits. For 5+ burden, MRP-heavy full traversals, roughly 60KB is a serious Andon and
    75KB is the deterministic minimum plausible mass; 75-100KB is the normal band.
    """
    burdens = unique_burdens(text)
    mrp_count = len(MRP_RE.findall(text))
    if claims_full_traversal(text) and len(burdens) >= 5 and mrp_count >= 5:
        return min(component_estimate, SMOKE6_CALIBRATED_MIN_KB * KB)
    return component_estimate


def claims_full_traversal(text: str) -> bool:
    return bool(
        re.search(r"(?i)\b(?:coverage_complete\s*=\s*true|all input-anchored burdens|all live burdens|no remaining|closure licensed)\b", text)
        or CLOSURE_RE.search(text)
    )


def check_path(path: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []
    size = path.stat().st_size
    estimated_min, rows = estimated_minimum_bytes(text)
    calibrated_floor = calibrated_mass_floor_bytes(text, estimated_min)

    if "NOETIC FIELD EXECUTION" not in text:
        errors.append(f"{path}: missing governed execution banner")
    if "Layer A" not in text:
        errors.append(f"{path}: missing Layer A compact header")

    burdens = unique_burdens(text)
    if len(burdens) < 4:
        errors.append(f"{path}: hard-compound smoke must expose at least four burden nodes; found {sorted(burdens)}")
    claims_full = claims_full_traversal(text)
    submove_count = explicit_submove_count(text)
    required_submoves = 15 if len(burdens) >= 5 else max(3, len(burdens) * 3)
    if not OWNER_SUBMOVE_RE.search(text):
        errors.append(f"{path}: missing explicit owner-bearing submove labels")
    bad_labels = BAD_OWNER_LABEL_RE.findall(text)
    if bad_labels:
        errors.append(
            f"{path}: owner-bearing submove brackets must use compact no-space owner IDs; found {len(bad_labels)} phrase label(s)"
        )
    if claims_full and not LAYER_B_RE.search(text):
        errors.append(f"{path}: full hard-compound traversal missing explicit Layer B operation body")
    if claims_full and submove_count < required_submoves:
        errors.append(
            f"{path}: full hard-compound traversal has only {submove_count} explicit owner-bearing submoves; expected at least {required_submoves}"
        )
    if claims_full and not DIVERGENCE_RE.search(text):
        errors.append(f"{path}: full closure missing parseable ∇·B status")
    if claims_full and not CURL_RE.search(text):
        errors.append(f"{path}: full closure missing parseable ∇×κ status")
    if claims_full and not CLOSURE_FIELD_RE.search(text):
        errors.append(f"{path}: full closure missing parseable 𝒞(Ψᴺ) coverage field")
    if claims_full and not TRANSFER_RE.search(text):
        errors.append(f"{path}: full closure missing parseable T_lang Ψᴺ ⇢ Ψᴵ / PsiN -> PsiI boundary")
    if claims_full and re.search(r"(?im)^\s*(?:∇·\s*result|∇×\s*result|remaining kappa|coverage_complete\s*=\s*true)\s*:?", text):
        errors.append(f"{path}: full closure uses substitute closure fields instead of parseable witness fields")
    if claims_full and not MRP_RESULTANTS_RE.search(text):
        errors.append(f"{path}: full closure missing MRP resultants ledger in Closure/Reconstruction Witness")
    if claims_full and not ROOT_MARKER_RE.search(text):
        errors.append(f"{path}: full closure dependency graph must mark root as exact '(root)'")
    if not LAND_RE.search(text):
        errors.append(f"{path}: missing Land(B1) / partial Land(B1)")

    mrp_positions = [match.start() for match in MRP_RE.finditer(text)]
    if not mrp_positions:
        errors.append(f"{path}: missing [Mid-Reread Pressure] block")
        return errors

    land_pos = line_pos(text, LAND_RE)
    closure_pos = line_pos(text, CLOSURE_RE)
    restorative_pos = line_pos(text, RESTORATIVE_RE)
    closing_pos = line_pos(text, Closing_RE)
    if land_pos is not None:
        interstitial = [pos for pos in mrp_positions if pos > land_pos and (closure_pos is None or pos < closure_pos)]
        if not interstitial:
            errors.append(f"{path}: no inter-burden MRP after Land(B1) and before closure")
    if restorative_pos is not None and all(pos > restorative_pos for pos in mrp_positions):
        errors.append(f"{path}: MRP appears only after final/restorative material")
    if claims_full:
        if closure_pos is not None and restorative_pos is not None and closure_pos > restorative_pos:
            errors.append(f"{path}: hard/full closure witness must appear before Restorative Response")
        if closure_pos is not None and closing_pos is not None and closure_pos > closing_pos:
            errors.append(f"{path}: hard/full closure witness must appear before Closing Formulation")
        stop_matches = list(re.finditer(r"(?im)^\s*Route\s*:\s*STOP\b", text))
        completion_after_stop = re.search(
            r"(?im)^\s*(?:Layer B\s*[-—]\s*Burden-Local Completion Body|Supplemental|Appendix|B\d+[_\.-]?\d+\s*\[)",
            text[stop_matches[-1].end() :] if stop_matches else "",
        )
        if stop_matches and completion_after_stop and (closure_pos is None or stop_matches[-1].end() < closure_pos):
            errors.append(f"{path}: no burden-local completion/submove work may appear after final Route: STOP and before closure")

    first_mrp_start = mrp_positions[0]
    next_mrp_start = mrp_positions[1] if len(mrp_positions) > 1 else len(text)
    first_mrp = text[first_mrp_start:next_mrp_start]
    slots = PRESSURE_SLOT_RE.findall(first_mrp)
    if len(set(slots)) < 6:
        errors.append(f"{path}: first interstitial MRP lacks all six pressure slots")
    if not RESULTANT_RE.search(first_mrp):
        errors.append(f"{path}: first interstitial MRP missing MRP resultant")
    if not GRAPH_EDGE_RE.search(first_mrp):
        errors.append(f"{path}: first interstitial MRP missing graph delta B1 -> B2/B3/B4")
    route = ROUTE_RE.search(first_mrp)
    if not route:
        errors.append(f"{path}: first interstitial MRP missing route")
    elif route.group("route") == "STOP":
        errors.append(f"{path}: first interstitial MRP must not STOP while downstream burdens remain live")

    if "R(H,Delta)" not in text and "R(H,Δ)" not in text:
        errors.append(f"{path}: missing R(H,Delta) reread")
    if not INITIAL_RE.search(text) and "HOLD" not in first_mrp:
        errors.append(f"{path}: missing initial burden set for reconstructibility")
    if not TERMINAL_RE.search(text) and "HOLD" not in first_mrp:
        errors.append(f"{path}: missing terminal-state accounting for reconstructibility")
    if "T_lang" not in text:
        errors.append(f"{path}: missing T_lang non-guaranteed-uptake boundary")
    if claims_full and len(burdens) >= 5 and len(MRP_RE.findall(text)) >= 5 and size < SMOKE6_SERIOUS_ANDON_KB * KB:
        errors.append(
            f"{path}: FAIL - UNDER-EXECUTED HARD-COMPOUND: actual {size} bytes below serious Andon floor {SMOKE6_SERIOUS_ANDON_KB * KB} bytes while claiming full traversal"
        )
    elif size < calibrated_floor and claims_full:
        errors.append(
            f"{path}: FAIL - UNDER-EXECUTED HARD-COMPOUND: actual {size} bytes below calibrated minimum {calibrated_floor} bytes while claiming full traversal"
        )
    elif size < calibrated_floor:
        errors.append(
            f"{path}: output below calibrated minimum {calibrated_floor} bytes; requires explicit adjudicator size waiver"
        )
    return errors


def print_mass_table(path: Path) -> None:
    text = read_text(path)
    estimated_min, rows = estimated_minimum_bytes(text)
    calibrated_floor = calibrated_mass_floor_bytes(text, estimated_min)
    actual = path.stat().st_size
    print(f"\n{path}")
    print("Component | Count | Expected minimum | Present? | Notes")
    print("--- | ---: | ---: | --- | ---")
    for component, (count, kb, present, notes) in rows.items():
        print(f"{component} | {count} | {kb} KB | {'yes' if present else 'no'} | {notes}")
    print(f"Component estimate: {estimated_min} bytes ({estimated_min / KB:.1f} KB)")
    print(f"Calibrated minimum: {calibrated_floor} bytes ({calibrated_floor / KB:.1f} KB)")
    print(f"Actual: {actual} bytes ({actual / KB:.1f} KB)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outputs", nargs="+", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in args.outputs:
        print_mass_table(path)
        errors.extend(check_path(path))
    if errors:
        print("hard-compound MRP smoke check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("hard-compound MRP smoke check: PASS")
    print(f"Outputs checked: {len(args.outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
