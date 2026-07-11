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

Wiring requires a direct checker execution command. Python launcher argv is
classified without execution: value-taking options are consumed, terminal
command/module modes stop, and only the resulting script slot is evidence. A
help-only invocation or checker filename appearing only as another command's
argument is not evidence.

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
import re
import shlex
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
ALWAYS_NON_GATING_FLAGS = {"-h", "--help"}
NON_GATING_FLAGS_BY_CHECKER = {
    "check_ci_registry_coverage.py": {"--report"},
}


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


def _python_launcher_kind(executable: str) -> str | None:
    leaf = executable.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if leaf in {"py", "py.exe"}:
        return "py"
    if re.fullmatch(
        r"(?:pythonw?(?:\d+(?:\.\d+)*t?)?|pypy(?:\d+(?:\.\d+)*)?)(?:\.exe)?",
        leaf,
    ):
        return "python"
    return None


def _python_script_index(parts: list[str], launcher_kind: str) -> int | None:
    flag_only = {
        "-B", "-d", "-E", "-i", "-I", "-P", "-q", "-R", "-s", "-S", "-u", "-v", "-x",
        "--debug", "--dont-write-bytecode", "--ignore-environment", "--inspect", "--isolated",
        "--no-site", "--no-user-site", "--optimize", "--quiet", "--safe-path", "--unbuffered",
        "--verbose",
    }
    consumes_value = {"-W", "-X", "--check-hash-based-pycs"}
    terminal = {"-", "-c", "-m", "-h", "--help", "-V", "--version"}
    index = 1
    while index < len(parts):
        token = parts[index]
        if launcher_kind == "py" and token in {"-0", "-0p", "--list", "--list-paths"}:
            return None
        if launcher_kind == "py" and (
            re.fullmatch(r"-\d+(?:\.\d+)*(?:-\d+)?", token)
            or re.fullmatch(r"-V:.+", token, flags=re.IGNORECASE)
        ):
            index += 1
            continue
        if token == "--":
            return index + 1 if index + 1 < len(parts) else None
        if (
            token in terminal
            or (token.startswith("-c") and token != "-c")
            or (token.startswith("-m") and token != "-m")
        ):
            return None
        if token in consumes_value:
            if index + 1 >= len(parts):
                return None
            index += 2
            continue
        if (
            token in flag_only
            or re.fullmatch(r"-(?:b+|O+|q+|v+)", token)
            or (token.startswith("-W") and token != "-W")
            or (token.startswith("-X") and token != "-X")
            or token.startswith("--check-hash-based-pycs=")
        ):
            index += 1
            continue
        if token.startswith("-"):
            return None
        return index
    return None


def wired_checkers(checker_files: set[str], commands: list[str]) -> set[str]:
    """Return checkers directly executed in an owner-gating local-CI mode.

    A checker filename in an argument, comment-like string, generic help probe,
    or checker-owned explicitly non-gating mode is not execution evidence.
    """
    wired: set[str] = set()
    for command in commands:
        try:
            parts = shlex.split(command, posix=False)
        except ValueError:
            continue
        parts = [
            part[1:-1]
            if len(part) >= 2 and part[0] == part[-1] and part[0] in {"'", '"'}
            else part
            for part in parts
        ]
        if not parts:
            continue

        launcher_kind = _python_launcher_kind(parts[0])
        script_index: int | None = None
        if launcher_kind is not None:
            script_index = _python_script_index(parts, launcher_kind)
        elif parts[0].lower().endswith(".py"):
            script_index = 0

        if script_index is None:
            continue
        script = parts[script_index]
        checker_args = parts[script_index + 1:]
        if any(part in ALWAYS_NON_GATING_FLAGS for part in checker_args):
            continue
        normalized = script.replace("\\", "/").removeprefix("./")
        if not normalized.startswith("tools/"):
            continue
        name = normalized.removeprefix("tools/")
        if any(part in NON_GATING_FLAGS_BY_CHECKER.get(name, set()) for part in checker_args):
            continue
        if "/" not in name and name in checker_files:
            wired.add(name)
    return wired


def _disk_state() -> tuple[set[str], set[str], dict[str, dict]]:
    checker_files = {os.path.basename(p) for p in glob.glob(str(ROOT / "tools" / "check_*.py"))}
    commands = _load_commands()
    wired = wired_checkers(checker_files, commands)
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
        ("wiring requires a direct owner-gating checker invocation",
         wired_checkers(
             files | {"check_ci_registry_coverage.py"},
             [
                 "python tools/check_a.py --help",
                 "python tools/check_ci_registry_coverage.py --report",
                 "python tools/helper.py --example tools/check_b.py",
                 "python tools/check_c.py --self-test",
                 "python tools/check_d.py --report artifact.json",
             ],
         ) == {"check_c.py", "check_d.py"}),
        ("interpreter options consume their values before script selection",
         wired_checkers(
             files,
             [
                 "python -X tools/check_a.py tools/check_b.py",
                 "python -W tools/check_c.py tools/check_d.py",
                 "python --check-hash-based-pycs tools/check_a.py tools/check_c.py",
             ],
         ) == {"check_b.py", "check_c.py", "check_d.py"}),
        ("command and module modes are terminal before later checker arguments",
         wired_checkers(
             files,
             [
                 'python -c "print(1)" tools/check_a.py',
                 'python "-cprint(1)" tools/check_b.py',
                 "python -m http.server tools/check_c.py",
                 "python -mhttp.server tools/check_d.py",
             ],
         ) == set()),
        ("end-of-options and direct checker scripts remain wired",
         wired_checkers(
             files,
             [
                 "python -- tools/check_a.py",
                 "python -B tools/check_b.py",
                 "python tools/check_c.py",
                 "tools/check_d.py --report artifact.json",
             ],
         ) == files),
        ("bounded interpreter launchers selectors and attached options are recognized",
         wired_checkers(
             files,
             [
                 "python3.13t -Xdev tools/check_a.py",
                 "C:/Python313/python3.13t.exe tools/check_a.py",
                 r"C:\Python313\python3.13t.exe tools/check_a.py",
                 r'"C:\Program Files\Python313\python3.13t.exe" tools/check_a.py',
                 "C:/Python312/pythonw.exe -Wignore tools/check_b.py",
                 "py -3 tools/check_c.py",
                 "pypy3.exe tools/check_d.py",
             ],
         ) == files),
        ("near-miss free-threaded names remain non-Python launchers",
         wired_checkers(
             files,
             [
                 "python3.13tx tools/check_a.py",
                 "cpython3.13t tools/check_b.py",
             ],
         ) == set()),
        ("unknown pre-script interpreter options fail closed",
         wired_checkers(files, ["python --future-option tools/check_a.py"]) == set()),
        ("py launcher list modes are terminal",
         wired_checkers(
             files,
             [
                 "py -0 tools/check_a.py",
                 "py -0p tools/check_b.py",
                 "py --list tools/check_c.py",
                 "py --list-paths tools/check_d.py",
             ],
         ) == set()),
        ("non-gating flags apply only after the selected checker script",
         wired_checkers(
             files | {"check_ci_registry_coverage.py"},
             [
                 "python -X --help tools/check_a.py",
                 "python -W --report tools/check_ci_registry_coverage.py",
                 "python --help tools/check_b.py",
                 "python tools/check_c.py --help",
             ],
         ) == {"check_a.py", "check_ci_registry_coverage.py"}),
        ("class breakdown groups by class",
         class_breakdown({"a.py": {"class": "required"}, "b.py": {"class": "advisory"},
                          "c.py": {"class": "required"}}) == {"required": ["a.py", "c.py"], "advisory": ["b.py"]}),
    ]
    ok = all(passed for _, passed in cases)
    for name, passed in cases:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"ci-registry-coverage self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def class_breakdown(entries: dict[str, dict]) -> dict[str, list[str]]:
    """Pure helper (unit-tested): group checker names by declared class, each list sorted."""
    groups: dict[str, list[str]] = {}
    for name in sorted(entries):
        groups.setdefault(entries[name].get("class", "?"), []).append(name)
    return groups


def main() -> int:
    parser = argparse.ArgumentParser(description="CI registry coverage checker (Plan 08 Phase 1)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic evaluate() self-test")
    parser.add_argument("--report", action="store_true", help="print the checker class breakdown and exit 0 (no gating)")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.report:
        if not REGISTRY.is_file():
            print(f"ci registry coverage: FAIL (missing {REGISTRY})")
            return 1
        checker_files, wired, entries = _disk_state()
        groups = class_breakdown(entries)
        print(f"ci registry: {len(entries)} checkers registered, {len(wired)} required/wired")
        for cls in sorted(groups):
            print(f"  {cls} ({len(groups[cls])}):")
            for n in groups[cls]:
                print(f"    - {n}")
        return 0

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
