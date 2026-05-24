#!/usr/bin/env python3
"""Integrated reconstructibility + Mid-Reread Pressure proof harness.

This checker composes the visible closure-witness graph parser, field_witness
sidecar validation, visual/sidecar consistency, MRP fixture checker, and
compiled-runtime inclusion check. It is structural evidence, not package-bound
release proof or live model competence proof.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from check_closure_witness_graph import check as check_closure_witness
from check_manual_smoke_render_contract import check_text as check_manual_smoke_render_text
from check_mid_reread_pressure import check_fixture, has_edge, parse_mrp
from closure_witness_lib import (
    extract_field_witness,
    field_witness_graph_errors,
    load_json,
    parse_closure_witness,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
VISIBLE = ROOT / "tests/live-witness-fixtures/valid/closure-witness-dependency-graph.md"
SIDECAR = ROOT / "tests/live-witness-fixtures/valid/closure-witness-dependency-graph.field_witness.json"
OLD_SIDECAR = ROOT / "tests/live-witness-fixtures/valid/field-witness-dependency-graph.json"
MISMATCH_SIDECAR = ROOT / "tests/live-witness-fixtures/invalid/closure-witness-dependency-graph-mismatch.field_witness.json"
LIVE_INVALID_DIR = ROOT / "tests/live-witness-fixtures/invalid"
LIVE_INVALID_GRAPH_FIXTURES = {
    "closure-witness-cycle.md",
    "closure-witness-edge-unknown-node.md",
    "closure-witness-unparseable-graph.md",
    "missing-terminal-state.md",
    "positive-closure-with-non-neutral-divergence.md",
}
MANUAL_SMOKE_VALID_DIR = ROOT / "tests/manual-smoke-render/valid"
MANUAL_SMOKE_INVALID_DIR = ROOT / "tests/manual-smoke-render/invalid"
MRP_VALID_DIR = ROOT / "tests/mid-reread-pressure/valid"
MRP_INVALID_DIR = ROOT / "tests/mid-reread-pressure/invalid"
COMPILED_MAP = ROOT / "skill/compiled-module-map.json"
TACTICS_BUNDLE = ROOT / "skill/references/omnibus/OMNIBUS-tactics.md"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def record(errors: list[str], label: str, found: list[str], expect_fail: bool = False) -> None:
    if expect_fail:
        if found:
            print(f"PASS expected-fail: {label}")
        else:
            errors.append(f"{label}: expected failure but passed")
        return
    if found:
        errors.extend(f"{label}: {item}" for item in found)
    else:
        print(f"PASS: {label}")


def visible_parser_errors() -> list[str]:
    witness = parse_closure_witness(VISIBLE.read_text(encoding="utf-8", errors="replace"))
    errors: list[str] = []
    if witness is None:
        return ["visible closure witness did not parse"]
    if not witness.initial_burdens:
        errors.append("visible parser did not recover initial burdens")
    if not witness.registers:
        errors.append("visible parser did not recover register notes")
    if not witness.terminal_states:
        errors.append("visible parser did not recover terminal states")
    if not witness.roots:
        errors.append("visible parser did not recover roots")
    if not witness.edges:
        errors.append("visible parser did not recover dependency edges")
    if not witness.parallel_groups:
        errors.append("visible parser did not recover parallel groups")
    if not witness.divergence:
        errors.append("visible parser did not recover ∇· diagnostic")
    if not witness.curl:
        errors.append("visible parser did not recover ∇× diagnostic")
    return errors


def sidecar_only_errors() -> list[str]:
    sidecar = extract_field_witness(load_json(SIDECAR))
    return field_witness_graph_errors(sidecar)


def compiled_runtime_errors() -> list[str]:
    errors: list[str] = []
    if not COMPILED_MAP.is_file():
        return [f"{rel(COMPILED_MAP)} missing; run build_compiled_runtime.py first"]
    payload = json.loads(COMPILED_MAP.read_text(encoding="utf-8"))
    modules = payload.get("modules", {})
    mrp = modules.get("TTP-MRP-mid-reread-pressure")
    if not isinstance(mrp, dict):
        errors.append("compiled-module-map missing TTP-MRP-mid-reread-pressure")
    else:
        if mrp.get("bundle_path") != "references/omnibus/OMNIBUS-tactics.md":
            errors.append("TTP-MRP compiled bundle path is not OMNIBUS-tactics.md")
        if mrp.get("module_class") != "tactic":
            errors.append("TTP-MRP compiled module_class is not tactic")
    if not TACTICS_BUNDLE.is_file():
        errors.append(f"{rel(TACTICS_BUNDLE)} missing")
    elif "TTP-MRP-mid-reread-pressure" not in TACTICS_BUNDLE.read_text(encoding="utf-8", errors="replace"):
        errors.append("compiled tactics bundle does not include TTP-MRP body")
    return errors


def mrp_case_errors() -> list[str]:
    cases = {
        "stable closure": (MRP_VALID_DIR / "stable-reread-closure.md", "stable", "STOP", False),
        "genuine downstream RECURSE": (MRP_VALID_DIR / "genuine-downstream-burden.md", "genuine-dependent", "RECURSE", True),
        "partial HOLD": (MRP_VALID_DIR / "partial-real-burden.md", "partial-real", "HOLD", True),
        "hidden-framework recoil": (MRP_VALID_DIR / "hidden-framework-recoil.md", "hidden-framework-recoil", "STOP", False),
        "doubt-churn LoopBreak": (MRP_VALID_DIR / "doubt-churn-loopbreak.md", "doubt-churn", "LoopBreak(∇×T)", False),
        "reorientation/reminder": (MRP_VALID_DIR / "reorientation-reminder.md", "reorientation", "STOP", False),
    }
    errors: list[str] = []
    for label, (path, finding, route, edge_required) in cases.items():
        block = parse_mrp(path.read_text(encoding="utf-8", errors="replace"))
        if block is None:
            errors.append(f"{label}: missing MRP block")
            continue
        if block.finding != finding:
            errors.append(f"{label}: expected finding {finding!r}, saw {block.finding!r}")
        if block.route != route:
            errors.append(f"{label}: expected route {route!r}, saw {block.route!r}")
        if edge_required and not has_edge(block.graph_delta):
            errors.append(f"{label}: expected graph delta edge")
    preemption_text = (MRP_VALID_DIR / "genuine-downstream-burden.md").read_text(encoding="utf-8", errors="replace")
    preemption = parse_mrp(preemption_text)
    if preemption is None:
        errors.append("pre-emption case: missing MRP block")
    else:
        if preemption.preemption_basis not in {"graph-bound", "commitment-bound", "framework-bound"}:
            errors.append("pre-emption case: missing structural pre-emption basis")
        if not has_edge(preemption.graph_delta):
            errors.append("pre-emption case: missing graph delta")
        if not re.search(r"(?i)\bdispatch(?:es|ed)?\b.+\bM8-reductio\b", preemption_text):
            errors.append("pre-emption case: does not record dispatch to existing matched TTP")
        if not re.search(r"(?i)rather than answering it by MRP itself", preemption_text):
            errors.append("pre-emption case: does not preserve MRP-not-refuter boundary")
    return errors


def main() -> int:
    errors: list[str] = []

    if OLD_SIDECAR.exists():
        errors.append(f"old non-canonical sidecar still exists: {rel(OLD_SIDECAR)}")
    if not SIDECAR.is_file():
        errors.append(f"canonical sidecar missing: {rel(SIDECAR)}")

    record(errors, "visible parser recovers graph/register/diagnostic fields", visible_parser_errors())
    record(errors, "field_witness sidecar validates independently", sidecar_only_errors())
    record(errors, "visible witness and sidecar match", check_closure_witness(VISIBLE, SIDECAR))
    record(errors, "visible witness and mismatched sidecar fail", check_closure_witness(VISIBLE, MISMATCH_SIDECAR), expect_fail=True)

    for name in sorted(LIVE_INVALID_GRAPH_FIXTURES):
        path = LIVE_INVALID_DIR / name
        record(errors, f"closure invalid fixture fails: {rel(path)}", check_closure_witness(path), expect_fail=True)

    for path in sorted(MRP_VALID_DIR.glob("*.md")):
        record(errors, f"MRP valid fixture passes: {rel(path)}", check_fixture(path))
    for path in sorted(MRP_INVALID_DIR.glob("*.md")):
        record(errors, f"MRP invalid fixture fails: {rel(path)}", check_fixture(path), expect_fail=True)

    for path in sorted(MANUAL_SMOKE_VALID_DIR.glob("*.md")):
        record(
            errors,
            f"manual smoke render valid fixture passes: {rel(path)}",
            check_manual_smoke_render_text(path, path.read_text(encoding="utf-8", errors="replace")),
        )
    for path in sorted(MANUAL_SMOKE_INVALID_DIR.glob("*.md")):
        record(
            errors,
            f"manual smoke render invalid fixture fails: {rel(path)}",
            check_manual_smoke_render_text(path, path.read_text(encoding="utf-8", errors="replace")),
            expect_fail=True,
        )

    record(errors, "MRP integrated route matrix", mrp_case_errors())
    record(errors, "TTP-MRP compiled runtime inclusion", compiled_runtime_errors())

    if errors:
        print("reconstructibility + MRP integrated check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("reconstructibility + MRP integrated check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
