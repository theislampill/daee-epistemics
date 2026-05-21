#!/usr/bin/env python3
"""Validate MRP generated-burden fixtures and public notation discipline.

This checker distinguishes ordinary held-burden activation from a genuinely
MRP-generated downstream burden. It is intentionally fixture-oriented: old
hosted smokes may retain parser aliases, while these fixtures encode the
public notation and route-result contract expected for new generated burdens.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from check_mid_reread_pressure import MrpBlock, parse_mrps


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROUTE_TYPES = {
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "loopbreak",
    "hold_partial",
}
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUB = "₀₁₂₃₄₅₆₇₈₉"
TOKEN = rf"(?:[{SUP}]+B|B\d+)"
CANONICAL_TOKEN = rf"[{SUP}]+B"
EDGE_RE = re.compile(rf"(?P<src>{TOKEN})\s*(?:→|->)\s*(?P<dst>{TOKEN})")
INITIAL_RE = re.compile(r"(?im)^\s*[-*]?\s*Initial burden set\s*:\s*\[(?P<body>[^\]]*)\]")
HELD_RE = re.compile(
    r"(?im)^\s*[-*]?\s*(?:Held burden set|Held routes|Held)\s*:\s*(?:\[(?P<bracket>[^\]]*)\]|(?P<body>.+))$"
)
MRP_RESULTANT_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?MRP resultants?\s*:")
MRP_CLOSURE_RESULTANT_RE = re.compile(
    rf"(?is)MRP\((?P<src>{TOKEN})\)\s*:\s*type=(?P<route_type>[a-z_]+)\s*;"
    rf"\s*finding=(?P<finding>[^;]+)\s*;\s*graph=(?P<graph>[^;]+)\s*;"
    rf"\s*route=(?P<route>STOP|HOLD|RECURSE|LoopBreak\(∇×T\))"
)
COMMON_EXAMPLE_OWNERS = {"FPD", "M1", "M1-P", "M1P", "M8"}

BAD_PUBLIC_NOTATION: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ASCII graph edge", re.compile(r"\bB\d+\s*->\s*B\d+\b")),
    ("ASCII Land(Bn)", re.compile(r"\bLand\(B\d+\)")),
    ("ASCII R(H,Delta)", re.compile(r"R\(H,\s*Delta\)")),
    ("ASCII del-dot", re.compile(r"\bdel[- ]dot\b", re.IGNORECASE)),
    ("ASCII del-cross", re.compile(r"\bdel[- ]cross\b", re.IGNORECASE)),
    ("ASCII C(PsiN)", re.compile(r"\bC\(PsiN\)", re.IGNORECASE)),
    ("ASCII T_lang", re.compile(r"T_lang\s*:\s*PsiN\s*->\s*PsiI", re.IGNORECASE)),
    ("subscript burden token", re.compile(rf"\bB[{SUB}]+")),
    ("caret burden token", re.compile(r"\bB\^\d+")),
    ("ASCII submove token", re.compile(r"\bB\d+[_\.]\d+\b")),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def burden_tokens(value: str) -> list[str]:
    return re.findall(TOKEN, value)


def initial_burdens(text: str) -> set[str]:
    match = INITIAL_RE.search(text)
    if not match:
        return set()
    return set(burden_tokens(match.group("body")))


def held_burdens(text: str) -> set[str]:
    found: set[str] = set()
    for match in HELD_RE.finditer(text):
        found.update(burden_tokens(match.group("bracket") or match.group("body") or ""))
    return found


def initial_or_held_burdens(text: str) -> set[str]:
    return initial_burdens(text) | held_burdens(text)


def block_target(block: MrpBlock) -> str:
    tokens = burden_tokens(block.target)
    return tokens[0] if tokens else ""


def block_edges(block: MrpBlock) -> list[tuple[str, str]]:
    return [(m.group("src"), m.group("dst")) for m in EDGE_RE.finditer(block.graph_delta + "\n" + block.mrp_resultant)]


def next_section(text: str, start: int) -> str:
    tail = text[start:]
    match = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:Burden\s+\d+\s*/|Closure/Reconstruction Witness|Restorative Response|Closing Formulation)\b",
        tail,
    )
    return tail[: match.start()] if match else tail


def generated_heading(text: str, source: str, target: str) -> re.Match[str] | None:
    return re.search(
        rf"(?im)^\s*#{{1,6}}\s*Burden\s+\d+\s*/\s*{re.escape(target)}[^\n]*"
        rf"\[generated-by:\s*MRP\({re.escape(source)}\)\]",
        text,
    )


def owner_submoves(section: str, target: str) -> list[str]:
    pattern = re.compile(rf"(?im)^\s*{re.escape(target)}[{SUB}]+\[([A-Za-z][A-Za-z0-9/-]*)\]\s*(?:[-—:])")
    return pattern.findall(section)


def notation_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for label, pattern in BAD_PUBLIC_NOTATION:
        if pattern.search(text):
            errors.append(f"{path}: public generated-burden fixture uses forbidden {label}")
    return errors


def generated_burden_errors(path: Path, text: str, block: MrpBlock) -> list[str]:
    errors: list[str] = []
    source = block_target(block)
    edges = block_edges(block)
    if not source:
        return [f"{path}: generated_burden_instantiation target must name canonical burden"]
    if not edges:
        return [f"{path}: generated_burden_instantiation requires graph edge"]
    edge = edges[0]
    target = edge[1]
    if target in initial_burdens(text):
        errors.append(f"{path}: {target} is already in Initial burden set; classify as held_burden_activation")
    if target in held_burdens(text):
        errors.append(f"{path}: {target} is already in held inventory; classify as held_burden_activation")
    if block.route not in {"RECURSE", "HOLD"}:
        errors.append(f"{path}: generated_burden_instantiation must route RECURSE or HOLD")
    if block.preemption_basis == "none":
        errors.append(f"{path}: generated_burden_instantiation requires graph/commitment/framework-bound basis")
    if not block.route_gradient:
        errors.append(f"{path}: generated_burden_instantiation requires Route-gradient")
    elif not re.search(r"(?i)\b(?:generated|new|newly|resultant|not fully present|not present|MRP)\b", block.route_gradient):
        errors.append(f"{path}: generated_burden_instantiation Route-gradient must explain the newly surfaced resultant")
    if not re.fullmatch(CANONICAL_TOKEN, source) or not re.fullmatch(CANONICAL_TOKEN, target):
        errors.append(f"{path}: generated graph edge must use canonical burden notation")
    heading = generated_heading(text, source, target)
    if not heading:
        errors.append(f"{path}: generated burden {target} must appear as a real node with [generated-by: MRP({source})]")
        return errors
    section = next_section(text, heading.end())
    if not re.search(r"(?im)^\s*Layer A\b", section):
        errors.append(f"{path}: generated burden {target} missing Layer A accounting")
    if not re.search(r"(?im)^\s*Layer B\s*[-—]\s*Governed Operation Body\b", section):
        errors.append(f"{path}: generated burden {target} missing Layer B governed operation body")
    owners = owner_submoves(section, target)
    if len(owners) < 3:
        errors.append(f"{path}: generated burden {target} needs at least three owner-bearing submoves")
    if owners and set(owners).issubset(COMMON_EXAMPLE_OWNERS):
        errors.append(f"{path}: generated burden {target} appears hardcoded to FPD/M1/M8 examples")
    if not re.search(rf"(?im)^\s*(?:Land|HOLD)\({re.escape(target)}\)\s*:", section):
        errors.append(f"{path}: generated burden {target} missing Land({target}) or HOLD({target})")
    closure_tail = text[re.search(r"(?im)^\s*(?:#{1,6}\s*)?Closure/Reconstruction Witness\b", text).start() :] if re.search(r"(?im)^\s*(?:#{1,6}\s*)?Closure/Reconstruction Witness\b", text) else ""
    if target not in closure_tail or f"MRP({source})" not in closure_tail:
        errors.append(f"{path}: closure witness must record generated node and MRP provenance")
    if not MRP_RESULTANT_RE.search(closure_tail):
        errors.append(f"{path}: closure witness missing MRP resultants ledger")
    return errors


def held_activation_errors(path: Path, text: str, block: MrpBlock) -> list[str]:
    errors: list[str] = []
    edges = block_edges(block)
    if not edges:
        errors.append(f"{path}: held_burden_activation requires graph provenance edge")
        return errors
    target = edges[0][1]
    if target not in initial_or_held_burdens(text):
        errors.append(f"{path}: held_burden_activation target {target} must be in Initial burden set or held inventory")
    if "[generated-by:" in text:
        errors.append(f"{path}: held_burden_activation fixture must not mark the next burden generated")
    if block.route not in {"RECURSE", "HOLD"}:
        errors.append(f"{path}: held_burden_activation must route RECURSE or HOLD")
    if not block.route_gradient:
        errors.append(f"{path}: held_burden_activation requires Route-gradient")
    elif not re.search(r"(?i)\b(?:held|initial|already[- ]inventoried|already named|H\b)", block.route_gradient):
        errors.append(f"{path}: held_burden_activation Route-gradient must point to an already-held/initial burden")
    return errors


def generated_marker_consistency_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for marker in re.finditer(rf"(?P<target>{TOKEN})\s*\[generated-by:\s*MRP\((?P<src>{TOKEN})\)\]", text):
        source = marker.group("src")
        target = marker.group("target")
        key = (source, target)
        if key in seen:
            continue
        seen.add(key)
        tail = closure_tail(text)
        closure_match = re.search(
            rf"MRP\({re.escape(source)}\)\s*:\s*type=generated_burden_instantiation;[^\n]*graph=[^;\n]*{re.escape(source)}\s*(?:→|->)\s*{re.escape(target)}",
            tail,
            re.IGNORECASE,
        )
        if not closure_match:
            errors.append(f"{path}: generated marker {target} [generated-by: MRP({source})] requires matching closure MRP generated resultant")
    return errors


def block_route_type_errors(path: Path, text: str, block: MrpBlock) -> list[str]:
    route_type = block.route_result_type.strip()
    if not route_type:
        return [f"{path}: MRP block missing MRP route result type"]
    if route_type not in ROUTE_TYPES:
        return [f"{path}: invalid MRP route result type {route_type!r}"]
    if route_type == "generated_burden_instantiation":
        return generated_burden_errors(path, text, block)
    if route_type == "held_burden_activation":
        return held_activation_errors(path, text, block)
    if route_type == "no_new_resultant" and block_edges(block):
        return [f"{path}: no_new_resultant must not create graph edge"]
    if route_type == "loopbreak" and block.route != "LoopBreak(∇×T)":
        return [f"{path}: loopbreak route result type requires Route: LoopBreak(∇×T)"]
    if route_type == "hold_partial" and block.route != "HOLD":
        return [f"{path}: hold_partial route result type requires Route: HOLD"]
    return []


def closure_tail(text: str) -> str:
    match = re.search(r"(?im)^\s*(?:#{1,6}\s*)?Closure/Reconstruction Witness\b", text)
    return text[match.start() :] if match else ""


def closure_resultant_errors(path: Path, text: str) -> list[str]:
    """Validate held/generated route typing in the closure witness ledger.

    Some smoke outputs format compact MRP blocks with Markdown or omit visible route-type
    lines, but still print the machine-facing `MRP resultants` ledger. The ledger must
    obey the same lineage rule: an already-initialized node is held, not generated.
    """
    tail = closure_tail(text)
    if not tail or not MRP_RESULTANT_RE.search(tail):
        return []

    errors: list[str] = []
    initial = initial_burdens(text)
    held = held_burdens(text)
    initial_or_held = initial | held
    for match in MRP_CLOSURE_RESULTANT_RE.finditer(tail):
        source = match.group("src")
        route_type = match.group("route_type")
        graph = " ".join(match.group("graph").split())
        route = match.group("route")
        edges = [(m.group("src"), m.group("dst")) for m in EDGE_RE.finditer(graph)]
        label = f"{path}: closure MRP({source})"

        if route_type not in ROUTE_TYPES:
            errors.append(f"{label}: invalid MRP resultant type {route_type!r}")
            continue
        if route_type == "generated_burden_instantiation":
            if not edges:
                errors.append(f"{label}: generated_burden_instantiation requires graph edge")
                continue
            target = edges[0][1]
            if target in initial:
                errors.append(f"{label}: {target} is already in Initial burden set; classify as held_burden_activation")
            if target in held:
                errors.append(f"{label}: {target} is already in held inventory; classify as held_burden_activation")
            if route not in {"RECURSE", "HOLD"}:
                errors.append(f"{label}: generated_burden_instantiation must route RECURSE or HOLD")
        elif route_type == "held_burden_activation":
            if not edges:
                errors.append(f"{label}: held_burden_activation requires graph provenance edge")
                continue
            target = edges[0][1]
            if target not in initial_or_held:
                errors.append(f"{label}: held_burden_activation target {target} must be in Initial burden set or held inventory")
            if route not in {"RECURSE", "HOLD"}:
                errors.append(f"{label}: held_burden_activation must route RECURSE or HOLD")
        elif route_type == "no_new_resultant" and edges:
            errors.append(f"{label}: no_new_resultant must not create graph edge")
        elif route_type == "loopbreak" and route != "LoopBreak(∇×T)":
            errors.append(f"{label}: loopbreak route result type requires route LoopBreak(∇×T)")
        elif route_type == "hold_partial" and route != "HOLD":
            errors.append(f"{label}: hold_partial route result type requires route HOLD")
    return errors


def check_text(path: Path, text: str) -> list[str]:
    errors = notation_errors(path, text)
    blocks = parse_mrps(text)
    if not blocks:
        errors.append(f"{path}: missing [Mid-Reread Pressure] block")
    route_types: set[str] = set()
    for block in blocks:
        if block.route_result_type:
            route_types.add(block.route_result_type)
        errors.extend(block_route_type_errors(path, text, block))
    errors.extend(generated_marker_consistency_errors(path, text))
    errors.extend(closure_resultant_errors(path, text))
    if path.parent.name == "valid" and path.name.startswith("generated-"):
        if "generated_burden_instantiation" not in route_types:
            errors.append(f"{path}: generated fixture must prove generated_burden_instantiation")
    if path.parent.name == "valid" and path.name.startswith("held-"):
        if "held_burden_activation" not in route_types:
            errors.append(f"{path}: held fixture must prove held_burden_activation")
    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("tests/mrp-generated-burden"))
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0
    for path in valid:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = check_text(path, read_text(path))
        if not found:
            errors.append(f"{path}: expected-invalid generated-burden fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in args.outputs:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("MRP generated-burden check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("MRP generated-burden check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
