#!/usr/bin/env python3
"""Compile Python source in memory without creating bytecode artifacts."""
from __future__ import annotations

import argparse
import sys
import tokenize
from pathlib import Path
from typing import Sequence


def check(paths: Sequence[str]) -> list[str]:
    findings: list[str] = []
    seen: set[Path] = set()
    for raw_path in paths:
        path = Path(raw_path)
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as exc:
            findings.append(f"{raw_path}: unavailable Python source: {exc}")
            continue
        if resolved in seen:
            findings.append(f"{raw_path}: duplicate Python source")
            continue
        seen.add(resolved)
        if resolved.suffix != ".py" or not resolved.is_file():
            findings.append(f"{raw_path}: expected one regular .py file")
            continue
        try:
            with tokenize.open(resolved) as handle:
                source = handle.read()
            compile(source, str(resolved), "exec", dont_inherit=True, optimize=0)
        except (OSError, SyntaxError, UnicodeError) as exc:
            findings.append(f"{raw_path}: {type(exc).__name__}: {exc}")
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    findings = check(args.paths)
    if findings:
        for finding in findings:
            print(f"python syntax check: FAIL: {finding}", file=sys.stderr)
        return 1
    print(f"python syntax check: PASS ({len(args.paths)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
