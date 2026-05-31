#!/usr/bin/env python3
"""Fail on common mojibake markers in tracked UTF-8 text files."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def marker(codepoint: int) -> str:
    return chr(codepoint)


FORBIDDEN_TOKENS: tuple[tuple[str, str], ...] = (
    ("U+00E2 marker", marker(0x00E2)),
    ("U+00C2 marker", marker(0x00C2)),
    ("U+00C3 marker", marker(0x00C3)),
    ("U+00CE marker", marker(0x00CE)),
    ("U+00CF marker", marker(0x00CF)),
    ("U+00D0 marker", marker(0x00D0)),
    ("U+00F0 marker", marker(0x00F0)),
    ("replacement character", marker(0xFFFD)),
    ("common superscript mojibake pair", marker(0x00E1) + marker(0x00B4)),
)


def tracked_files(paths: list[str]) -> list[Path]:
    command = ["git", "-C", str(ROOT), "ls-files", "-z"]
    if paths:
        command.extend(["--", *paths])
    raw = subprocess.check_output(command)
    files = [ROOT / item.decode("utf-8") for item in raw.split(b"\0") if item]
    for item in paths:
        path = Path(item)
        if not path.is_absolute():
            path = ROOT / path
        if path.is_file():
            files.append(path)

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def is_binary(data: bytes) -> bool:
    return b"\0" in data


def excerpt(line: str) -> str:
    return line.strip().encode("unicode_escape", errors="backslashreplace").decode("ascii")[:220]


def scan_file(path: Path) -> list[str]:
    if not path.is_file():
        return []
    data = path.read_bytes()
    if is_binary(data):
        return []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return []

    errors: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for label, token in FORBIDDEN_TOKENS:
            if token in line:
                rel = path.relative_to(ROOT).as_posix()
                errors.append(f"{rel}:{lineno}: {label}: {excerpt(line)}")
    return errors


def validate_bad_sample() -> list[str]:
    bad = "bad " + marker(0x00E2) + marker(0x02C6) + marker(0x2021)
    if any(token in bad for _, token in FORBIDDEN_TOKENS):
        return []
    return ["internal bad-sample validation failed"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Optional tracked paths to scan")
    parser.add_argument("--samples-only", action="store_true")
    args = parser.parse_args(argv)

    errors = validate_bad_sample()
    if not args.samples_only:
        for path in tracked_files(args.paths):
            errors.extend(scan_file(path))

    if errors:
        print("mojibake check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("mojibake check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
