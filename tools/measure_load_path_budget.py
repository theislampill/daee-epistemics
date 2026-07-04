#!/usr/bin/env python3
"""Load-path budget measurement — Plan 16 Phase 1 (stdlib only).

MEASURES and REPORTS the byte / line / estimated-token footprint of the runtime
load-path configurations. It does NOT enforce a budget, slim anything, or gate
CI on a size threshold — it is observability for the architecture-debt work.

est_tokens is a heuristic: est_tokens = bytes // 4. It is not a tokenizer count
and is not a claim about any specific model's context accounting.

Configurations reported:
  - skill-md-only          : skill/SKILL.md alone
  - per-bundle             : each skill/references/runtime-*.md bundle
  - five-bundle-substantive: skill/SKILL.md + all runtime bundles
  - always-load-bundles    : skill/SKILL.md + the distinct bundles hosting the
                             files in SKILL.md's "### Always Load" table
                             (resolved via skill/compiled-module-map.json)
  - largest-retained-output: the single largest retained case output.md
And a constraint census: case-insensitive `must` / `never` word counts in SKILL.md.

Usage:
  python tools/measure_load_path_budget.py
  python tools/measure_load_path_budget.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "skill" / "SKILL.md"
BUNDLE_GLOB = "skill/references/runtime-*.md"
MODULE_MAP = ROOT / "skill" / "compiled-module-map.json"
RETAINED_GLOB = "tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/*/output.md"


def metrics(paths: list[Path]) -> tuple[int, int, int]:
    """Return (total_bytes, total_lines, est_tokens) for the given files."""
    total_bytes = 0
    total_lines = 0
    for p in paths:
        data = p.read_bytes()
        total_bytes += len(data)
        total_lines += data.count(b"\n")
    return total_bytes, total_lines, total_bytes // 4


def bundles() -> list[Path]:
    return [Path(p) for p in sorted(glob.glob(str(ROOT / BUNDLE_GLOB)))]


def always_load_files(skill_text: str) -> list[str]:
    """Parse the `references/...` paths listed in SKILL.md's '### Always Load' table."""
    m = re.search(r"### Always Load\n(.*?)(?:\n### )", skill_text, re.S)
    if not m:
        return []
    return re.findall(r"`(references/[^`]+)`", m.group(1))


def always_load_bundles(skill_text: str) -> tuple[list[Path], list[str]]:
    """Resolve always-load files to their runtime bundles via the module map.

    Returns (distinct bundle paths, unresolved canonical_paths)."""
    files = always_load_files(skill_text)
    module_map = json.loads(MODULE_MAP.read_text(encoding="utf-8")).get("modules", {})
    canon_to_bundle: dict[str, str] = {}
    for entry in module_map.values():
        canon = entry.get("canonical_path")
        bundle = entry.get("bundle_path")
        if canon and bundle:
            canon_to_bundle[canon] = bundle
    resolved: list[str] = []
    unresolved: list[str] = []
    for f in files:
        bundle = canon_to_bundle.get(f)
        if bundle:
            resolved.append(bundle)
        else:
            unresolved.append(f)
    bundle_paths = sorted({ROOT / b for b in resolved}, key=lambda p: str(p))
    return bundle_paths, unresolved


def constraint_census(skill_text: str) -> tuple[int, int]:
    must = len(re.findall(r"(?i)\bmust\b", skill_text))
    never = len(re.findall(r"(?i)\bnever\b", skill_text))
    return must, never


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def build_rows() -> list[tuple[str, str, int, int, int]]:
    """Return rows: (config, detail, bytes, lines, est_tokens)."""
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    bnds = bundles()
    rows: list[tuple[str, str, int, int, int]] = []

    b, l, t = metrics([SKILL_MD])
    rows.append(("skill-md-only", rel(SKILL_MD), b, l, t))

    for bp in bnds:
        b, l, t = metrics([bp])
        rows.append(("per-bundle", rel(bp), b, l, t))

    b, l, t = metrics([SKILL_MD, *bnds])
    rows.append(("five-bundle-substantive", f"SKILL.md + {len(bnds)} bundles", b, l, t))

    al_bundles, unresolved = always_load_bundles(skill_text)
    detail = f"SKILL.md + {len(al_bundles)} always-load bundles"
    if unresolved:
        detail += f" (unresolved: {', '.join(unresolved)})"
    b, l, t = metrics([SKILL_MD, *al_bundles])
    rows.append(("always-load-bundles", detail, b, l, t))

    retained = [Path(p) for p in sorted(glob.glob(str(ROOT / RETAINED_GLOB)))]
    if retained:
        largest = max(retained, key=lambda p: p.stat().st_size)
        b, l, t = metrics([largest])
        rows.append(("largest-retained-output", rel(largest), b, l, t))

    return rows


def render_table() -> str:
    rows = build_rows()
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    must, never = constraint_census(skill_text)
    lines = [
        "| config | detail | bytes | lines | est_tokens (bytes/4) |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for config, detail, b, l, t in rows:
        lines.append(f"| {config} | {detail} | {b} | {l} | {t} |")
    lines.append("")
    lines.append(f"constraint-census (skill/SKILL.md): must={must}, never={never}")
    return "\n".join(lines)


def self_test() -> int:
    checks = []
    # est_tokens formula
    checks.append(("est_tokens = bytes//4", metrics([SKILL_MD])[2] == metrics([SKILL_MD])[0] // 4))
    # five-bundle-substantive total == skill-md + sum(per-bundle)
    skill_b = metrics([SKILL_MD])[0]
    per_bundle_sum = sum(metrics([bp])[0] for bp in bundles())
    combined = metrics([SKILL_MD, *bundles()])[0]
    checks.append(("five-bundle total == skill + sum(bundles)", combined == skill_b + per_bundle_sum))
    # rows present and non-empty
    rows = build_rows()
    checks.append(("has skill-md-only row", any(r[0] == "skill-md-only" for r in rows)))
    checks.append(("has five-bundle-substantive row", any(r[0] == "five-bundle-substantive" for r in rows)))
    checks.append(("all byte counts positive", all(r[2] > 0 for r in rows)))
    ok = all(p for _, p in checks)
    for name, p in checks:
        print(f"  self-test {'PASS' if p else 'FAIL'}: {name}")
    print(f"measure-load-path-budget self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Load-path budget measurement (Plan 16 Phase 1)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic arithmetic self-test")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    print("Load-path budget (measurement only; est_tokens = bytes // 4 heuristic)")
    print()
    print(render_table())
    return 0


if __name__ == "__main__":
    sys.exit(main())
