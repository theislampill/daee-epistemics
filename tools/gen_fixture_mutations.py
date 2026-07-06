#!/usr/bin/env python3
"""Fixture anti-evasion mutation sweep — Plan 12 Phase 3 (Lane D).

Applies enumerated STRUCTURAL-REMOVAL mutations to valid fixtures and asserts the
owning checker REJECTS each mutant. Only structural-removal operators are used;
Land-gate FORMAT mutations (bold/heading/bullet) are deliberately NOT used because
the hardened LAND_GATE regex tolerates those prefixes by design, so they are
accepted (not evasions) and would produce spurious survivors.

Operators (each a pure text transform; returns None when not applicable):
  - terminal-mrp-collapse : remove all but the last [Mid-Reread Pressure] block
                            (only when >=2 blocks) -> a single terminal MRP can no
                            longer cover multiple prior Lands, so the route checker
                            rejects. Empirically 3/3 applicable valid route fixtures
                            reject, 0 survivors (2026-07-04).
  - witness-strip         : remove a fenced block containing field_witness (only when
                            present). No field_witness lives in the swept families,
                            so it skips there; available for field_witness-bearing
                            families.

NEVER writes under tests/. Mutants go to a temp dir (default: a fresh tempdir).
Exit codes: 0 = every applied mutant rejected; 3 = at least one SURVIVOR (mutant
accepted by its owning checker) -> a FINDING, not a crash; 2 = usage/internal error.

Usage:
  python tools/gen_fixture_mutations.py --self-test
  python tools/gen_fixture_mutations.py [--emit-dir <dir outside tests/>]
"""
from __future__ import annotations

import argparse
import glob
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_mid_reread_pressure as _mr  # for MRP_BLOCK_RE

FENCE_FW_RE = re.compile(r"```[^\n]*\n.*?field_witness.*?```", re.S)

# family valid-dir glob -> owning checker
FAMILY_DETECTORS = {
    "tests/mrp-route-invariants/valid/*.md": "check_mrp_route_invariants",
}


def terminal_mrp_collapse(text: str) -> str | None:
    blocks = list(_mr.MRP_BLOCK_RE.finditer(text))
    if len(blocks) < 2:
        return None
    out, last = [], 0
    for b in blocks[:-1]:
        out.append(text[last:b.start()])
        last = b.end()
    out.append(text[last:])
    return "".join(out)


def witness_strip(text: str) -> str | None:
    m = FENCE_FW_RE.search(text)
    if not m:
        return None
    return text[:m.start()] + text[m.end():]


OPERATORS = {
    "terminal-mrp-collapse": terminal_mrp_collapse,
    "witness-strip": witness_strip,
}


def _run_checker(detector: str, content: str, emit_dir: Path, tag: str) -> int:
    path = emit_dir / f"mut_{tag}.md"
    path.write_text(content, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / f"{detector}.py"), "--outputs", str(path)],
        capture_output=True,
    )
    return proc.returncode


def sweep(emit_dir: Path) -> tuple[list[dict], list[dict]]:
    """Return (applied_rows, skipped_rows). applied row verdict: 'rejected' | 'survivor'."""
    applied, skipped = [], []
    for family_glob, detector in FAMILY_DETECTORS.items():
        for src in sorted(glob.glob(str(ROOT / family_glob))):
            text = Path(src).read_text(encoding="utf-8")
            name = Path(src).name
            for op_name, op in OPERATORS.items():
                mutated = op(text)
                if mutated is None:
                    skipped.append({"fixture": name, "operator": op_name})
                    continue
                code = _run_checker(detector, mutated, emit_dir, f"{op_name}_{name}")
                applied.append({
                    "fixture": name, "operator": op_name,
                    "verdict": "rejected" if code != 0 else "survivor",
                })
    return applied, skipped


def _safe_emit_dir(raw: str | None) -> Path:
    if raw is None:
        return Path(tempfile.mkdtemp(prefix="daee_mut_"))
    p = Path(raw).resolve()
    tests_root = (ROOT / "tests").resolve()
    if tests_root == p or tests_root in p.parents:
        raise SystemExit(f"--emit-dir must not be under tests/: {p}")
    p.mkdir(parents=True, exist_ok=True)
    return p


def self_test() -> int:
    emit_dir = Path(tempfile.mkdtemp(prefix="daee_mut_selftest_"))
    applied, skipped = sweep(emit_dir)
    survivors = [r for r in applied if r["verdict"] == "survivor"]
    collapse_applied = [r for r in applied if r["operator"] == "terminal-mrp-collapse"]
    checks = [
        ("terminal-mrp-collapse applied to >=1 fixture", len(collapse_applied) >= 1),
        ("no survivors (all applied mutants rejected)", len(survivors) == 0),
        ("witness-strip skips where no field_witness",
         any(s["operator"] == "witness-strip" for s in skipped)),
        ("no mutant written under tests/",
         not any(str((ROOT / "tests").resolve()) in str(p.resolve())
                 for p in emit_dir.glob("*.md"))),
        ("emit-dir guard rejects a tests/ path",
         _emit_guard_rejects()),
    ]
    ok = all(p for _, p in checks)
    for name, p in checks:
        print(f"  self-test {'PASS' if p else 'FAIL'}: {name}")
    print(f"  (applied={len(applied)} skipped={len(skipped)} survivors={len(survivors)})")
    print(f"gen-fixture-mutations self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def _emit_guard_rejects() -> bool:
    try:
        _safe_emit_dir(str(ROOT / "tests" / "x"))
        return False
    except SystemExit:
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixture anti-evasion mutation sweep (Plan 12 Phase 3)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic sweep self-test")
    parser.add_argument("--emit-dir", help="where to write mutants (must be outside tests/); default: fresh tempdir")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    emit_dir = _safe_emit_dir(args.emit_dir)
    applied, skipped = sweep(emit_dir)
    survivors = [r for r in applied if r["verdict"] == "survivor"]
    for r in applied:
        print(f"  {r['operator']} {r['fixture']}: {r['verdict']}")
    print(f"applied={len(applied)} skipped={len(skipped)} survivors={len(survivors)} emit_dir={emit_dir}")
    if survivors:
        for r in survivors:
            print(f"FINDING: mutation survived: {r['operator']} on {r['fixture']}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
