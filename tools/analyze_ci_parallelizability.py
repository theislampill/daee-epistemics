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

Also exposes benchmark_summary(timings): a pure helper that, from measured
per-command wall times, computes the phase-staged parallelization ceiling (serial
generate+git prefix, read-only phase divided across N workers). It performs no
live timing itself -- a live --benchmark runner (which would re-run generators
and race shared files) is a deferred, manual, non-lane-wired follow-up. The
ceiling is an upper bound (perfect balance, zero overhead), not a measured run,
and does not authorize adopting parallelization.
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


def benchmark_summary(timings: dict[str, float], workers: tuple[int, ...] = (2, 4, 8)) -> dict:
    """Pure core (unit-tested): phase-staged parallelization ceiling from measured
    per-command wall times.

    Model: shared-writers and git-gates stay serial (the generate-then-verify
    prefix); only the read-only phase parallelizes across N workers. So the best
    achievable wall clock is ``ceiling(N) = shared_writer_s + git_gate_s +
    read_only_s / N`` and ``speedup(N) = serial_total / ceiling(N)``. This is an
    upper bound (perfect balance, zero overhead), not a measured parallel run, and
    is not authorization to adopt parallelization.
    """
    phase = {SHARED_WRITER: 0.0, GIT_GATE: 0.0, READ_ONLY: 0.0}
    for command, seconds in timings.items():
        phase[classify(command)] += float(seconds)
    serial_total = sum(phase.values())
    serial_prefix = phase[SHARED_WRITER] + phase[GIT_GATE]
    summary: dict = {
        "serial_total": serial_total,
        "shared_writer_s": phase[SHARED_WRITER],
        "git_gate_s": phase[GIT_GATE],
        "read_only_s": phase[READ_ONLY],
        "serial_prefix": serial_prefix,
        "ceiling": {},
        "speedup": {},
    }
    for n in workers:
        ceiling = serial_prefix + phase[READ_ONLY] / n
        summary["ceiling"][f"{n}x"] = ceiling
        summary["speedup"][f"{n}x"] = serial_total / ceiling if ceiling else 1.0
    return summary


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
    bench = benchmark_summary(
        {
            "python tools/build_compiled_runtime.py": 4.0,   # shared-writer
            "git diff --exit-code -- skill/SKILL.md": 1.0,    # git-gate
            "python tools/check_frontmatter.py": 2.0,         # read-only
            "python tools/check_coverage.py": 6.0,            # read-only
        }
    )
    cases += [
        ("benchmark serial_total sums all phases", bench["serial_total"] == 13.0),
        ("benchmark buckets by classify", (bench["shared_writer_s"], bench["git_gate_s"], bench["read_only_s"]) == (4.0, 1.0, 8.0)),
        ("benchmark serial_prefix = shared + git", bench["serial_prefix"] == 5.0),
        ("benchmark ceiling(N) = prefix + read/N", (bench["ceiling"]["2x"], bench["ceiling"]["4x"], bench["ceiling"]["8x"]) == (9.0, 7.0, 6.0)),
        ("benchmark speedup rises with workers", bench["speedup"]["2x"] < bench["speedup"]["4x"] < bench["speedup"]["8x"]),
        ("benchmark speedup bounded by total/prefix", bench["speedup"]["8x"] <= bench["serial_total"] / bench["serial_prefix"] + 1e-9),
        ("benchmark empty timings is safe", benchmark_summary({})["serial_total"] == 0.0),
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
