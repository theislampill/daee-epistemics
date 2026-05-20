#!/usr/bin/env python3
"""Targeted Trinitarian RC2 hotfix regression guard.

This checker validates the three narrow Trinitarian smoke defects:

- STOP cannot precede a later B4 / Layer B traversal.
- Linear B1 -> B2 -> B3 -> B4 dependency pressure uses ∇·T, not ∇×T.
- Trinitarian named authority plus Islamic tawḥīd restoration is not LOCAL CLAIM.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from check_mid_reread_pressure import (
    MrpBlock,
    curl_diagnostic_errors,
    first_state,
    parse_mrps,
    stop_before_continuation_errors,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


FIELD_RE = re.compile(r"(?im)^\s*║?\s*field\s*:\s*(?P<field>[A-Z -]+)\b")
TRINITY_RE = re.compile(r"(?i)\b(?:Trinitarian|Trinity|John\s+17:3|1\s+John\s+5:20|μόνον)\b")
TAWHID_RE = re.compile(r"(?i)\b(?:tawḥīd|tawhid|Islamic|Qur[ʾ'’`]?ān|ʿĪsā|Isa)\b")
B4_RE = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?(?:Burden\s+4\b|B4\b|Layer B\s*[-—]\s*Governed Operation Body)")
GRAPH_RE = re.compile(r"(?im)^\s*(?:-?\s*)?Burden dependency graph\s*:\s*(?P<body>.+)$")
EDGE_RE = re.compile(r"\b(B\d+)\b\s*(?:->|→)\s*\b(B\d+)\b")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def field_value(text: str) -> str:
    match = FIELD_RE.search(text)
    return match.group("field").strip() if match else ""


def graph_edges(text: str) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for match in GRAPH_RE.finditer(text):
        for source, target in EDGE_RE.findall(match.group("body")):
            edges.add((source, target))
    return edges


def block_target(block: MrpBlock) -> str:
    match = re.search(r"\bB\d+\b", block.target)
    return match.group(0) if match else ""


def graph_delta_has_edge(block: MrpBlock, source: str, target: str) -> bool:
    pattern = re.compile(rf"\b{re.escape(source)}\b\s*(?:->|→)\s*\b{re.escape(target)}\b")
    return bool(pattern.search(block.graph_delta) or pattern.search(block.mrp_resultant))


def check_text(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    errors.extend(stop_before_continuation_errors(path, text))

    field = field_value(text)
    if field == "LOCAL CLAIM" and TRINITY_RE.search(text) and TAWHID_RE.search(text):
        errors.append(
            f"{path}: Trinitarian named authority plus Islamic tawḥīd restoration must classify as MIXED NOETIC FIELD, not LOCAL CLAIM"
        )

    blocks = parse_mrps(text)
    for index, block in enumerate(blocks, start=1):
        label = f"{path}: MRP block {index}"
        errors.extend(curl_diagnostic_errors(path, block, label))
        target = block_target(block)
        if target == "B3" and block.route == "STOP" and B4_RE.search(text):
            errors.append(f"{path}: B3 MRP cannot Route: STOP when B4 follows as live Layer B/restoration work")
        if target in {"B1", "B2", "B3"} and first_state(block.divergence) in {"neutral", "settled"}:
            if re.search(r"\bB[234]\b.*\bremain(?:s)? live\b|\bB4\b.*\bfollows\b", block.body, re.I):
                errors.append(f"{label}: downstream burdens remaining live require non-neutral ∇·T")

    edges = graph_edges(text)
    if ("B3", "B4") in edges:
        backed = any(
            block_target(block) == "B3"
            and block.finding == "genuine-dependent"
            and block.route == "RECURSE"
            and graph_delta_has_edge(block, "B3", "B4")
            for block in blocks
        )
        if not backed:
            errors.append(f"{path}: closure graph edge B3 -> B4 must be backed by a B3 MRP genuine-dependent RECURSE resultant")

    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("tests/trinitarian-mrp-hotfix"))
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0

    for path in valid:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = check_text(path, read_text(path))
        if not found:
            errors.append(f"{path}: expected-invalid Trinitarian hotfix fixture unexpectedly passed")
        else:
            invalid_checked += 1
    output_checked = 0
    for path in args.outputs:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("trinitarian MRP hotfix check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("trinitarian MRP hotfix check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
