#!/usr/bin/env python3
"""Reject common mojibake and visible BOM residue in release-facing surfaces."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = (
    "README.md",
    "CHANGELOG.md",
    "TODO.md",
    "AGENTS.md",
    "docs",
    "tools",
    "atomics/skill",
    "skill",
    "tests",
    "smokes/runtime-grounding-v5",
)

MOJIBAKE_TOKENS = {
    b"\xc3\x82\xc2\xa7": "section-sign mojibake",
    b"\xc3\xa2\xe2\x82\xac\xe2\x80\x9d": "em-dash mojibake",
    b"\xc3\xa2\xe2\x82\xac\xc2\xa0": "arrow mojibake",
    b"\xc3\xa2\xe2\x80\x94": "bullet/dash mojibake",
    b"\xc3\xaf\xc2\xbb\xc2\xbf": "visible BOM mojibake",
}
UTF8_BOM = b"\xef\xbb\xbf"


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        resolved = path if path.is_absolute() else ROOT / path
        if not resolved.exists():
            continue
        if resolved.is_file():
            files.append(resolved)
            continue
        files.extend(
            child
            for child in resolved.rglob("*")
            if child.is_file()
            and ".git" not in child.parts
            and "__pycache__" not in child.parts
            and child.suffix != ".pyc"
            and "tests/output" not in child.as_posix().replace("\\", "/")
        )
    return sorted(set(files))


def line_number(data: bytes, offset: int) -> int:
    return data.count(b"\n", 0, offset) + 1


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def scan_file(path: Path) -> list[str]:
    data = path.read_bytes()
    errors: list[str] = []
    if data.startswith(UTF8_BOM):
        errors.append(f"{display_path(path)}:1: UTF-8 BOM at file start")
    for token, label in MOJIBAKE_TOKENS.items():
        start = 0
        while True:
            index = data.find(token, start)
            if index == -1:
                break
            errors.append(
                f"{display_path(path)}:{line_number(data, index)}: mojibake token {label}"
            )
            start = index + len(token)
    return errors


def validate_bad_samples() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="daee-encoding-hygiene-") as tmp:
        sample_path = Path(tmp) / "__encoding_hygiene_bad_sample__.md"
        sample_path.write_bytes(b"owner \xc3\x82\xc2\xa7Anchor\n")
        found = scan_file(sample_path)
        if not any("mojibake token" in item for item in found):
            errors.append("bad sample with mojibake section sign was not rejected")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Additional or replacement path to scan. May be repeated.",
    )
    parser.add_argument("--samples-only", action="store_true")
    args = parser.parse_args(argv)

    errors = validate_bad_samples()
    if not args.samples_only:
        targets = [Path(item) for item in (args.path or DEFAULT_TARGETS)]
        for path in iter_files(targets):
            errors.extend(scan_file(path))

    if errors:
        print("encoding hygiene: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("encoding hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
