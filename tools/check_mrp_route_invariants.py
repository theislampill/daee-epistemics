#!/usr/bin/env python3
"""Generic MRP route/curl/runtime invariant guard.

This checker validates runtime invariants that must hold across case families:

- STOP cannot precede later burden or Layer B work.
- Visible ACT body_ref groups must be contiguous by burden; owner-slot
  coverage in round-robin order is not runtime traversal.
- Public line-start Land(Bn) gates require immediate per-burden MRP traversal
  before later burden work; a single terminal MRP/no_new_resultant cannot cover
  multiple prior landings.
- Closure graph edges must be backed by MRP route/resultant records.
- Directed acyclic downstream pressure belongs to ∇·T, not ∇×T.
- Formal source/worldview frames with active restoration routes must not flatten to LOCAL CLAIM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from check_mid_reread_pressure import (
    MrpBlock,
    closure_over_held_route_errors,
    curl_diagnostic_errors,
    first_state,
    high_leverage_false_closure_errors,
    per_land_mrp_coverage_errors,
    parse_mrps,
    stop_before_continuation_errors,
)
from check_public_burden_grouping import (
    ActRecord,
    body_ref_burden_id,
    burden_group_order,
    normalize_body_ref,
    normalize_burden_id,
    parse_visible_acts,
    visible_public_body,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


FIELD_RE = re.compile(r"(?im)^\s*║?\s*field\s*:\s*(?P<field>[A-Z -]+)\b")
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
BURDEN_TOKEN_RE = re.compile(rf"(?:B\d+|[{SUP}]+B)")
BURDEN_RE = re.compile(r"\bB(?P<num>\d+)\b")
EDGE_RE = re.compile(rf"({BURDEN_TOKEN_RE.pattern})\s*(?:->|→)\s*({BURDEN_TOKEN_RE.pattern})")
GRAPH_HEADING_RE = re.compile(r"(?i)\bBurden dependency graph\s*:")
GRAPH_STOP_RE = re.compile(
    r"(?i)^\s*(?:[-*]\s*)?(?:Terminal states|MRP resultants|field_witness|del-dot|"
    r"∇·B|∇×κ|𝒞|T_lang|Restorative Response|Closing Formulation)\b"
)
MRP_HEADING_LINE_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:[-*]\s*)?(?:\*\*)?\[Mid-Reread Pressure\](?:\*\*)?\s*$"
)
LAND_GATE_LINE_RE = re.compile(r"(?m)^Land\((?P<burden>[¹²³⁴⁵⁶⁷⁸⁹]B|B[1-9][0-9]*)\):")
DOWNSTREAM_LIVE_RE = re.compile(
    r"(?i)\b(?:B\d+\b.*\bremain(?:s)? live|downstream burden(?:s)? remain|"
    r"later burden(?:s)? remain|next burden remains|B\d+\b.*\bfollows)\b"
)
NEGATED_DOWNSTREAM_RE = re.compile(
    r"(?i)\b(?:no|not|without|none)\s+"
    r"(?:input-anchored\s+|downstream\s+|later\s+|next\s+|broad\s+)*"
    r"(?:burden(?:s)?\s+)?(?:remain(?:s)?|live|remaining|follows)\b"
)
FORMAL_NONLOCAL_FIELD_TOKENS = {
    "authority-frame",
    "authority-order",
    "hard-source",
    "hidden-framework",
    "moral-tribunal",
    "named-worldview",
    "proof-stack",
    "source-stack",
    "source-status",
    "source-worldview",
    "worldview",
}
FORMAL_RESTORATION_TOKENS = {
    "active-restoration",
    "fitrah-restoration",
    "restoration-active",
    "restoration-frame",
    "tawhid-restoration",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def field_value(text: str) -> str:
    match = FIELD_RE.search(text)
    return match.group("field").strip() if match else ""


def field_witness_object(text: str) -> dict[str, object] | None:
    match = re.search(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\s*$", text)
    if not match:
        return None
    payload = text[match.end() :].strip()
    fence = re.match(r"(?is)^```(?:json)?\s*(.*?)\s*```", payload)
    if fence:
        payload = fence.group(1).strip()
    start = payload.find("{")
    if start < 0:
        return None
    try:
        decoded, _end = json.JSONDecoder().raw_decode(payload[start:])
    except json.JSONDecodeError:
        return None
    return decoded if isinstance(decoded, dict) else None


def formal_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")


def formal_values(value: object) -> set[str]:
    keys = {
        "authority_order",
        "field_class",
        "n_frame",
        "owner",
        "owner_family",
        "owner_id",
        "operation",
        "restoration_frame",
        "route_class",
        "selected_n_frame",
        "source_status",
        "source_status_class",
        "source_worldview",
    }
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys:
                if isinstance(item, list):
                    found.update(formal_key(entry) for entry in item if formal_key(entry))
                else:
                    token = formal_key(item)
                    if token:
                        found.add(token)
            if isinstance(item, (dict, list)):
                found.update(formal_values(item))
    elif isinstance(value, list):
        for item in value:
            found.update(formal_values(item))
    return found


def formal_token_matches(tokens: set[str], needles: set[str]) -> bool:
    return any(needle in token or token in needle for token in tokens for needle in needles)


def formal_nonlocal_restoration_pressure(payload: dict[str, object]) -> bool:
    tokens = formal_values(payload)
    return formal_token_matches(tokens, FORMAL_NONLOCAL_FIELD_TOKENS) and formal_token_matches(
        tokens,
        FORMAL_RESTORATION_TOKENS,
    )


def block_target(block: MrpBlock) -> str:
    match = BURDEN_TOKEN_RE.search(block.target)
    return match.group(0) if match else ""


def edge_set(text: str) -> set[tuple[str, str]]:
    return {(source, target) for source, target in EDGE_RE.findall(text)}


def closure_graph_text(text: str) -> str:
    lines = text.splitlines()
    captured: list[str] = []
    collecting = False
    for line in lines:
        if GRAPH_HEADING_RE.search(line):
            collecting = True
            captured.append(line)
            continue
        if collecting:
            if not line.strip() or GRAPH_STOP_RE.search(line):
                collecting = False
                continue
            captured.append(line)
    return "\n".join(captured)


def closure_graph_edges(text: str) -> set[tuple[str, str]]:
    return edge_set(closure_graph_text(text))


def mrp_backed_edges(blocks: list[MrpBlock]) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for block in blocks:
        edges.update(edge_set(block.graph_delta))
        edges.update(edge_set(block.mrp_resultant))
    return edges


def route_backed_edges(blocks: list[MrpBlock]) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for block in blocks:
        source = block_target(block)
        if block.finding not in {"genuine-dependent", "partial-real"}:
            continue
        if block.route not in {"RECURSE", "HOLD"}:
            continue
        for edge in edge_set(block.graph_delta) | edge_set(block.mrp_resultant):
            # Runtime MRP blocks use Target for the pressure being reread,
            # not necessarily for the burden token. The graph edge itself is
            # the route-bearing source/target witness; when a token is present
            # in Target, keep the stricter source check.
            if not source or edge[0] == source:
                edges.add(edge)
    return edges


def mixed_field_errors(path: Path, text: str) -> list[str]:
    field = field_value(text)
    if field != "LOCAL CLAIM":
        return []
    payload = field_witness_object(text)
    if payload is not None and formal_nonlocal_restoration_pressure(payload):
        return [
            f"{path}: formal source/worldview frame plus active restoration route must not classify as LOCAL CLAIM"
        ]
    return []


def graph_edge_errors(path: Path, text: str, blocks: list[MrpBlock]) -> list[str]:
    errors: list[str] = []
    if not blocks:
        return errors
    closure_edges = closure_graph_edges(text)
    if not closure_edges:
        return errors
    backed = mrp_backed_edges(blocks)
    route_backed = route_backed_edges(blocks)
    for edge in sorted(closure_edges):
        if edge not in backed:
            errors.append(f"{path}: closure graph edge {edge[0]} -> {edge[1]} lacks MRP graph/resultant backing")
        elif edge not in route_backed:
            errors.append(
                f"{path}: closure graph edge {edge[0]} -> {edge[1]} must be licensed by "
                "Finding: genuine-dependent/partial-real plus Route: RECURSE/HOLD"
            )
    return errors


def downstream_divergence_errors(path: Path, block: MrpBlock, label: str) -> list[str]:
    state = first_state(block.divergence)
    if (
        state in {"neutral", "settled"}
        and DOWNSTREAM_LIVE_RE.search(block.body)
        and not NEGATED_DOWNSTREAM_RE.search(block.body)
    ):
        return [f"{label}: downstream burdens remaining live require non-neutral ∇·T"]
    return []


def graph_delta_route_errors(path: Path, block: MrpBlock, label: str) -> list[str]:
    errors: list[str] = []
    # The per-block route invariant is about the block's own graph movement.
    # A STOP block may legitimately mention an already-recorded closure graph in
    # its resultant prose; only the explicit Graph delta field creates a new
    # route edge for this block.
    edges = edge_set(block.graph_delta)
    if not edges:
        return errors
    if block.finding not in {"genuine-dependent", "partial-real"}:
        errors.append(f"{label}: graph delta requires genuine-dependent or partial-real finding")
    if block.route not in {"RECURSE", "HOLD"}:
        errors.append(f"{label}: graph delta requires Route: RECURSE or Route: HOLD")
    return errors


def burden_number(burden_id: str) -> int:
    match = re.fullmatch(r"B([1-9][0-9]*)", burden_id)
    return int(match.group(1)) if match else 0


def visible_act_order_errors(path: Path, text: str) -> list[str]:
    public_body = visible_public_body(text)
    records = parse_visible_acts(public_body)
    if not records:
        return []

    errors: list[str] = []
    groups = [burden for burden in burden_group_order(records) if burden]
    if len(groups) <= 1:
        return errors

    unique_groups = list(dict.fromkeys(groups))
    if len(groups) > len(unique_groups):
        errors.append(
            f"{path}: visible ACT body_ref groups are interleaved ({' -> '.join(groups)}); "
            "coverage-complete owner slots are not runtime MRP traversal"
        )

    first_group_index: dict[str, int] = {}
    previous_number = 0
    for index, burden_id in enumerate(groups):
        if burden_id in first_group_index:
            span = " -> ".join(groups[first_group_index[burden_id] : index + 1])
            errors.append(
                f"{path}: visible ACT body_ref order is non-contiguous by burden: "
                f"{burden_id} reappears in {span}"
            )
        else:
            first_group_index[burden_id] = index

        number = burden_number(burden_id)
        if number and number < previous_number:
            errors.append(
                f"{path}: visible ACT burden order moves from a later burden back to {burden_id}; "
                "Land(Bn) -> R(H,Delta) must license the next burden before later work"
            )
        previous_number = max(previous_number, number)
    return errors


def terminal_mrp_cannot_cover_prior_land_errors(path: Path, text: str) -> list[str]:
    blocks = parse_mrps(text)
    if len(blocks) != 1:
        return []
    block = blocks[0]
    if block.route != "STOP" or block.route_result_type != "no_new_resultant":
        return []

    heading = MRP_HEADING_LINE_RE.search(text)
    if heading is None:
        return []
    target = normalize_burden_id(block.target)
    prior_land_burdens = []
    for match in LAND_GATE_LINE_RE.finditer(text):
        if match.start() >= heading.start():
            break
        burden = normalize_burden_id(match.group("burden"))
        if burden and burden != target:
            prior_land_burdens.append(burden)
    prior_land_burdens = list(dict.fromkeys(prior_land_burdens))
    if not prior_land_burdens:
        return []
    return [
        f"{path}: terminal no_new_resultant/STOP at {target or 'final MRP'} cannot cover "
        f"prior public Land gates {', '.join(prior_land_burdens)}; each landed burden "
        "requires visible R(H,Delta)/MRP traversal before the next burden-local work"
    ]


def visible_record_start_by_ref(records: list[ActRecord]) -> dict[str, int]:
    starts: dict[str, int] = {}
    for record in records:
        starts.setdefault(record.body_ref, record.start)
    return starts


def false_no_new_resultant_sidecar_errors(path: Path, text: str) -> list[str]:
    payload = field_witness_object(text)
    if not isinstance(payload, dict):
        return []
    activations = payload.get("owner_activations")
    if not isinstance(activations, list):
        return []

    records = parse_visible_acts(visible_public_body(text))
    starts = visible_record_start_by_ref(records)
    errors: list[str] = []
    for item in activations:
        if not isinstance(item, dict):
            continue
        route_type = str(item.get("mrp_route_result_type") or "").strip()
        if route_type != "no_new_resultant":
            continue
        body_ref = normalize_body_ref(item.get("body_ref"))
        start = starts.get(body_ref)
        if start is None:
            continue
        source_burden = body_ref_burden_id(body_ref)
        later = next(
            (
                record
                for record in records
                if record.start > start and (not source_burden or record.burden_id != source_burden)
            ),
            None,
        )
        if later is None:
            continue
        errors.append(
            f"{path}: no_new_resultant claimed for {body_ref} before later visible ACT "
            f"{later.body_ref}; sidecar/formal closure cannot license STOP ahead of public traversal"
        )
        if len(errors) >= 5:
            errors.append(f"{path}: additional premature no_new_resultant sidecar claims suppressed")
            break
    return errors


def sidecar_laundering_errors(path: Path, text: str, visible_errors: list[str]) -> list[str]:
    if not visible_errors:
        return []
    if not re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:field_witness|formal_reread_states|normalized_activation_record)\b",
        text,
    ):
        return []
    return [
        f"{path}: field_witness/formal reread closure cannot compensate for missing visible runtime traversal"
    ]


def visible_runtime_traversal_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    errors.extend(visible_act_order_errors(path, text))
    errors.extend(per_land_mrp_coverage_errors(path, text))
    errors.extend(terminal_mrp_cannot_cover_prior_land_errors(path, text))
    errors.extend(false_no_new_resultant_sidecar_errors(path, text))
    errors.extend(sidecar_laundering_errors(path, text, errors))
    return errors


def check_text(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    errors.extend(stop_before_continuation_errors(path, text))
    errors.extend(closure_over_held_route_errors(path, text))
    errors.extend(mixed_field_errors(path, text))
    errors.extend(visible_runtime_traversal_errors(path, text))

    blocks = parse_mrps(text)
    for index, block in enumerate(blocks, start=1):
        label = f"{path}: MRP block {index}"
        errors.extend(curl_diagnostic_errors(path, block, label))
        errors.extend(high_leverage_false_closure_errors(path, block, label))
        errors.extend(downstream_divergence_errors(path, block, label))
        errors.extend(graph_delta_route_errors(path, block, label))
    errors.extend(graph_edge_errors(path, text, blocks))
    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def run_check(root: Path, outputs: list[Path]) -> tuple[list[str], int, int, int]:
    errors: list[str] = []
    valid, invalid = iter_fixtures(root)
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
            errors.append(f"{path}: expected-invalid MRP route invariant fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in outputs:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1
    return errors, valid_checked, invalid_checked, output_checked


def run_cli(
    default_root: Path = Path("tests/mrp-route-invariants"),
    description: str | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=description or __doc__)
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors, valid_checked, invalid_checked, output_checked = run_check(args.root, args.outputs)
    if errors:
        print("MRP route invariant check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("MRP route invariant check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


def main() -> int:
    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main())
