#!/usr/bin/env python3
"""CI registry coverage checker — Plan 08 Phase 1.

Closes gap #1 from Plan 08: a `tools/check_*.py` file can exist without anyone
being able to say, from the repo alone, whether it is a required lane check, an
advisory probe, a release-only check, an indirectly-invoked check, a slow manual
check, a sample suite, or dead. This checker makes `tools/ci_registry.json` a
declared source of truth that MUST match reality:

  1. Every `tools/check_*.py` file has exactly one registry entry (no
     unregistered checker, no stale entry).
  2. Every entry's `class` is in the fixed vocabulary.
  3. The required<->wired invariant holds: a checker is wired into
     `tools/run_local_ci.py` COMMANDS iff its registry class is `required`.

It does NOT adjudicate whether a non-required label is the *correct* label — that
is owner work (Plan 08 Phase 2 / Plan 19). It only enforces that the accounting
exists and that the lane wiring matches the declared intent, so a checker can no
longer silently drop out of (or into) the required lane unnoticed.

This is structural/checker-replay evidence only; it makes no claim about output
correctness or release state.

Usage:
  python tools/check_ci_registry_coverage.py
  python tools/check_ci_registry_coverage.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tools" / "ci_registry.json"

REQUIRED_CLASS = "required"
NON_REQUIRED_CLASSES = {
    "advisory",
    "release-only",
    "indirect",
    "manual-slow",
    "sample-suite",
    "deprecated-candidate",
}
VALID_CLASSES = {REQUIRED_CLASS} | NON_REQUIRED_CLASSES


def evaluate(checker_files: set[str], wired: set[str], entries: dict[str, dict]) -> list[str]:
    """Pure core (unit-tested): return sorted error strings; empty == PASS.

    checker_files: basenames of tools/check_*.py that exist on disk.
    wired: subset of checker_files whose basename is invoked in run_local_ci COMMANDS.
    entries: registry `checkers` mapping name -> {"class": ...}.
    """
    errors: list[str] = []
    registered = set(entries)

    for name in sorted(checker_files - registered):
        errors.append(f"unregistered checker: {name} (add it to ci_registry.json with a class)")
    for name in sorted(registered - checker_files):
        errors.append(f"stale registry entry: {name} (no such tools/{name})")

    for name in sorted(checker_files & registered):
        cls = entries[name].get("class")
        if cls not in VALID_CLASSES:
            errors.append(f"bad class for {name}: {cls!r} (allowed: {sorted(VALID_CLASSES)})")
            continue
        is_wired = name in wired
        if is_wired and cls != REQUIRED_CLASS:
            errors.append(
                f"{name} is wired into run_local_ci but registry class is {cls!r} "
                f"(wired checkers must be class 'required')"
            )
        if (not is_wired) and cls == REQUIRED_CLASS:
            errors.append(
                f"{name} registry class is 'required' but it is NOT wired into run_local_ci "
                f"(required checkers must be in the lane)"
            )
    return errors


def _load_commands() -> list[str]:
    spec = importlib.util.spec_from_file_location("_rlc", ROOT / "tools" / "run_local_ci.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # module guards real work behind __main__
    return list(module.COMMANDS)


def _disk_state() -> tuple[set[str], set[str], dict[str, dict]]:
    checker_files = {os.path.basename(p) for p in glob.glob(str(ROOT / "tools" / "check_*.py"))}
    commands = _load_commands()
    wired = {name for name in checker_files if any(f"tools/{name}" in c for c in commands)}
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return checker_files, wired, data.get("checkers", {})


def self_test() -> int:
    files = {"check_a.py", "check_b.py", "check_c.py", "check_d.py"}
    wired = {"check_a.py", "check_b.py"}
    good = {
        "check_a.py": {"class": "required"},
        "check_b.py": {"class": "required"},
        "check_c.py": {"class": "advisory"},
        "check_d.py": {"class": "release-only"},
    }
    cases = [
        ("clean registry -> no errors", evaluate(files, wired, good) == []),
        ("unregistered checker flagged",
         any("unregistered checker: check_e.py" in e
             for e in evaluate(files | {"check_e.py"}, wired, good))),
        ("stale entry flagged",
         any("stale registry entry: check_z.py" in e
             for e in evaluate(files, wired, {**good, "check_z.py": {"class": "advisory"}}))),
        ("wired-but-not-required flagged",
         any("wired checkers must be class 'required'" in e
             for e in evaluate(files, wired, {**good, "check_a.py": {"class": "advisory"}}))),
        ("required-but-not-wired flagged",
         any("required checkers must be in the lane" in e
             for e in evaluate(files, wired, {**good, "check_c.py": {"class": "required"}}))),
        ("bad class flagged",
         any("bad class for check_c.py" in e
             for e in evaluate(files, wired, {**good, "check_c.py": {"class": "mystery"}}))),
    ]
    ok = all(passed for _, passed in cases)
    for name, passed in cases:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"ci-registry-coverage self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="CI registry coverage checker (Plan 08 Phase 1)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic evaluate() self-test")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if not REGISTRY.is_file():
        print(f"ci registry coverage: FAIL (missing {REGISTRY})")
        return 1
    checker_files, wired, entries = _disk_state()
    errors = evaluate(checker_files, wired, entries)
    if errors:
        print(f"ci registry coverage: FAIL ({len(errors)} problem(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        f"ci registry coverage: PASS ({len(checker_files)} checkers registered; "
        f"{len(wired)} required/wired, {len(checker_files) - len(wired)} non-required)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
