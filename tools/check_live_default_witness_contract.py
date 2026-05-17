#!/usr/bin/env python3
"""Check live default daee-epistemics output witness surfaces.

This checker is intentionally structural rather than exact-output brittle. It is
for captured installed-runtime smokes, especially hard/multi-burden default
answers where the runtime must report its own field state.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


REQUIRED_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("noetic-field banner", re.compile(r"NOETIC FIELD EXECUTION")),
    ("route-gradient witness", re.compile(r"∇\s*route\s*:")),
    (
        "target-explicit field diagnostics",
        re.compile(r"(?is)Field diagnostics\s*:.*?(?:∇·|del-dot).*?(?:∇×|del-cross)"),
    ),
    ("LoopBreak status", re.compile(r"(?im)^\s*-?\s*LoopBreak\s*:")),
    ("Closure/Reconstruction Witness", re.compile(r"(?im)^\s*#{2,5}\s*Closure/Reconstruction Witness\b")),
    ("closure-field condition", re.compile(r"`?𝒞\(Ψᴺ\)`?\s*:")),
    ("T_lang boundary", re.compile(r"`?T_lang:\s*Ψᴺ\s*⇢\s*Ψᴵ`?\s*:")),
    ("Restorative Response", re.compile(r"(?im)^\s*#{2,5}\s*Restorative Response\b")),
]

FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "decorative route-gradient proof",
        re.compile(r"(?is)∇.{0,80}(?:proves|guarantees|certifies).{0,80}(?:truth|warrant|execution)"),
    ),
    (
        "closure guarantees uptake",
        re.compile(r"(?is)𝒞\(Ψᴺ\).{0,120}(?:guarantees|ensures|proves).{0,80}(?:uptake|acceptance|conversion)"),
    ),
    (
        "T_lang guarantees uptake",
        re.compile(r"(?is)T_lang.{0,120}(?:guarantees|ensures|proves).{0,80}(?:uptake|acceptance|conversion)"),
    ),
]


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    for label, pattern in REQUIRED_PATTERNS:
        if not pattern.search(text):
            errors.append(f"{path}: missing {label}")
    field_line = re.compile(r"(?i)Field diagnostics\s*:.*?(?:∇·|del-dot).*?(?:∇×|del-cross)")
    reread_line = re.compile(r"R\(H,(?:Δ|Delta)\)")
    field_count = sum(1 for line in text.splitlines() if field_line.search(line))
    r_count = sum(1 for line in text.splitlines() if reread_line.search(line))
    if r_count > 1 and field_count < r_count:
        errors.append(
            f"{path}: field diagnostics not repeated for each R(H,Δ)/R(H,Delta) "
            f"({field_count} diagnostics for {r_count} rereads)"
        )
    for label, pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            errors.append(f"{path}: forbidden {label}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("outputs", nargs="+", type=Path, help="Captured live default output files")
    args = parser.parse_args()

    errors: list[str] = []
    for output in args.outputs:
        if not output.exists():
            errors.append(f"{output}: missing")
            continue
        errors.extend(check(output))

    if errors:
        print("live default witness contract: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("live default witness contract: PASS")
    for output in args.outputs:
        print(f"- {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
