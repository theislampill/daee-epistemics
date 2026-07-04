#!/usr/bin/env python3
"""Candidate-output verifier — Plan 01 scaffold (operator tooling).

Runs the visible-output structural checker battery over a SINGLE captured
candidate governed output and emits an aggregate verdict. It COMPOSES existing
validators (via their `--outputs` interface) and adds no new detection logic.

This is a post-hoc structural gate for a captured output. It is NOT:
  - a live in-host gate (the packaged scriptless runtime runs no checkers),
  - a semantic-truth, meaning-correctness, or interlocutor-uptake verdict,
  - a provenance or release claim.
A candidate that passes is structurally conformant, nothing more. See
docs/proof-class-taxonomy.md (structural-invariant / checker-replay) and
docs/non-claims.md.

The full live-output custody gate (hash-bound verdict artifact, quarantine,
not_checker_verified custody marker) is a larger subsystem and remains an
owner-scoped follow-up; this scaffold is the minimal composition wrapper.

Usage:
  python tools/verify_candidate_output.py <output.md>
  python tools/verify_candidate_output.py --self-test
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Existing output-facing checkers that accept `--outputs <file>`.
BATTERY = [
    "check_mrp_route_invariants",
    "check_public_burden_grouping",
    "check_mid_reread_pressure",
    "check_manual_smoke_render_contract",
    "check_concealment_mode",
    "check_act_surface_syntax",
]


def verify(output_path: Path) -> dict[str, bool]:
    """Run each battery checker over the candidate; True = accepted (exit 0)."""
    results: dict[str, bool] = {}
    for checker in BATTERY:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / f"{checker}.py"), "--outputs", str(output_path)],
            capture_output=True,
        )
        results[checker] = proc.returncode == 0
    return results


def failing_checkers(results: dict[str, bool]) -> list[str]:
    """Pure aggregation (unit-tested): sorted names of checkers that rejected."""
    return sorted(name for name, ok in results.items() if not ok)


def self_test() -> int:
    checks = [
        ("all-pass -> empty", failing_checkers({"a": True, "b": True}) == []),
        ("one-fail -> named", failing_checkers({"a": True, "b": False}) == ["b"]),
        ("multi-fail sorted", failing_checkers({"z": False, "a": False, "m": True}) == ["a", "z"]),
    ]
    ok = all(passed for _, passed in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"verify-candidate-output self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Candidate-output verifier (Plan 01 scaffold)")
    parser.add_argument("output", nargs="?", help="path to a captured governed output (.md)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic aggregation self-test")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.output:
        print("usage: verify_candidate_output.py <output.md> | --self-test")
        return 2
    path = Path(args.output)
    if not path.is_file():
        print(f"not a file: {path}")
        return 2

    results = verify(path)
    failing = failing_checkers(results)
    if failing:
        print(f"candidate output verdict: FAIL ({len(failing)}/{len(BATTERY)} checkers: {', '.join(failing)})")
        print("NOTE: structural conformance only; not a semantic-truth, provenance, or uptake verdict.")
        return 1
    print(f"candidate output verdict: PASS ({len(BATTERY)} structural checkers; structural conformance only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
