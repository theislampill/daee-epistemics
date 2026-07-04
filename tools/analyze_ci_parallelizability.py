#!/usr/bin/env python3
"""CI parallelizability analysis — Plan 08 (Lane K), proof/report only.

STATIC A/B proof: classifies every `tools/run_local_ci.py` COMMANDS entry by its
parallelization safety, without live-running the battery (a live parallel run
would race the shared generated files by construction, which is exactly the
hazard this proves). It does NOT change CI execution.

Categories:
  - shared-writer : mutates shared generated artifacts (build_* without
                    --self-test/--check, run_* smoke, pwsh smoke). Racing two of
                    these corrupts skill/SKILL.md / framework-pipeline.md / .daee.
  - git-gate      : a git command that READS tree state (git diff ...). Must run
                    AFTER the generators that produce what it inspects.
  - read-only     : check_*/verify_*/gen_*/measure_*/*-self-test/py_compile —
                    independent, side-effect-free over already-produced artifacts.

Conclusion (proof): the shared-writers and git-gates are order-sensitive and
cannot run concurrently with each other or with the read-only phase (which
depends on their output). Only the read-only phase could parallelize internally,
gated behind the serial generate-then-verify prefix, and doing so also trades
away the current first-failure-abort semantics for run-all. Therefore drop-in
parallelization is NOT SAFE; parallelization is PARTIAL and phase-staged at best.

Usage:
  python tools/analyze_ci_parallelizability.py
  python tools/analyze_ci_parallelizability.py --self-test
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SHARED_WRITER = "shared-writer"
GIT_GATE = "git-gate"
READ_ONLY = "read-only"


def classify(command: str) -> str:
    """Pure core (unit-tested): parallelization-safety category for one command."""
    c = command.strip()
    if c.startswith("git "):
        return GIT_GATE
    if c.startswith("pwsh "):
        return SHARED_WRITER
    if "--self-test" in c or "--check" in c or "-m py_compile" in c:
        return READ_ONLY
    tool = next((p.split("/")[-1] for p in c.split() if p.startswith("tools/")), "")
    if tool.startswith(("build_", "run_", "promote_")):
        return SHARED_WRITER
    return READ_ONLY


def _load_commands() -> list[str]:
    spec = importlib.util.spec_from_file_location("_rlc", ROOT / "tools" / "run_local_ci.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.COMMANDS)


def analyze(commands: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {SHARED_WRITER: [], GIT_GATE: [], READ_ONLY: []}
    for c in commands:
        groups[classify(c)].append(c)
    return groups


def self_test() -> int:
    cases = [
        ("build w/o flag is shared-writer", classify("python tools/build_compiled_runtime.py") == SHARED_WRITER),
        ("build --self-test is read-only", classify("python tools/build_staged_runtime_replay_record.py --self-test") == READ_ONLY),
        ("docs-index --check is read-only", classify("python tools/build_docs_index.py --check") == READ_ONLY),
        ("git diff is git-gate", classify("git diff --exit-code -- skill/SKILL.md") == GIT_GATE),
        ("pwsh smoke is shared-writer", classify("pwsh -NoProfile -File tools/run_current_skill_smoke.ps1") == SHARED_WRITER),
        ("checker is read-only", classify("python tools/check_frontmatter.py") == READ_ONLY),
        ("py_compile is read-only", classify("python -m py_compile tools/*.py") == READ_ONLY),
    ]
    ok = all(p for _, p in cases)
    for name, p in cases:
        print(f"  self-test {'PASS' if p else 'FAIL'}: {name}")
    print(f"ci-parallelizability self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="CI parallelizability analysis (Plan 08 Lane K)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic classify() self-test")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    groups = analyze(_load_commands())
    total = sum(len(v) for v in groups.values())
    print(f"CI parallelizability analysis ({total} commands):")
    for cat in (SHARED_WRITER, GIT_GATE, READ_ONLY):
        print(f"  {cat} ({len(groups[cat])}):")
        for c in groups[cat]:
            print(f"    - {c}")
    print()
    print("VERDICT: parallelization is NOT SAFE as a drop-in. The shared-writers and "
          "git-gates are order-sensitive; only the read-only phase could parallelize, "
          "gated behind the serial generate-then-verify prefix, and that also changes "
          "first-failure-abort semantics. Parallelization stays PARTIAL / phase-staged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
