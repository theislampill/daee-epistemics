#!/usr/bin/env python3
"""Validate compact concealment-mode discipline in rendered outputs.

The checker is intentionally narrow. It does not infer a person's interior state or
replace the modes-of-concealment taxonomy. It catches the regression where an output
calls concealment "None detected" while the same Layer A read marks an imported or
identity-stabilizing framework as operative.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


CONCEALMENT_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?(?P<label>concealment(?:[_ -]?mode)?)(?:\*\*)?\s*:\s*(?P<value>.*)$"
)
BLOCK_START_RE = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:Layer A|Burden\s+\d+|Closure/Reconstruction Witness)\b")
NONE_PLACEHOLDER_RE = re.compile(r"(?i)^(?:none|none detected|none confirmed|not detected|n/?a|nil|null|unknown|[-–—]+)\b|^[-–—]+$")
CLEAR_VALUE_RE = re.compile(r"(?i)^(?:clear|none|none detected|none confirmed|not detected)\b")
FRAMEWORK_SIGNAL_RE = re.compile(
    r"(?i)\b(?:"
    r"D6|D3|imported\s+(?:foreign\s+)?framework|imported[- ]framework|"
    r"pseudo-neutral|neutral\s+(?:exegesis|reading|grammar|criterion|tribunal)|"
    r"reading\s+criterion|identity-stabili[sz]ation|doctrinal\s+apparatus|"
    r"Trinitarian\s+(?:person/nature|model|grammar|framework)|person/nature\s+grammar|"
    r"later\s+(?:Trinitarian|doctrinal)\s+(?:model|apparatus|grammar)|"
    r"doctrine-(?:import|preserving)|doctrine\s+import|imported\s+model-language|"
    r"creedal\s+(?:framework|commitment|lens)|framework\s+presents\s+as\s+neutral|"
    r"named\s+worldview|field\s*:\s*NAMED WORLDVIEW|governing\s+worldview|"
    r"governing\s+(?:lens|framework|criterion)|operates?\s+from\s+inside\s+the\s+worldview"
    r")\b"
)
ACTIVE_HIDDEN_FRAMEWORK_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?hidden-framework-recoil\s*:\s*"
    r"(?!(?:pressure\s+class\s*:\s*)?(?:none|cleared)\b).+"
)
CLEAR_EXCEPTION_RE = re.compile(
    r"(?i)\b(?:positively\s+(?:exposed|cleared)|no\s+longer\s+governs|"
    r"framework\s+(?:cleared|no\s+longer\s+operative)|non-operative\s+finding|"
    r"operative\s+covering\s+(?:cleared|absent))\b"
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def surrounding_block(text: str, start: int) -> str:
    """Return the current compact diagnostic/burden block around a concealment line."""
    prior = list(BLOCK_START_RE.finditer(text, 0, start))
    block_start = prior[-1].start() if prior else max(0, start - 800)
    next_match = BLOCK_START_RE.search(text, start + 1)
    block_end = next_match.start() if next_match else min(len(text), start + 1600)
    return text[block_start:block_end]


def check_text(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    matches = list(CONCEALMENT_LINE_RE.finditer(text))
    framework_active = bool(FRAMEWORK_SIGNAL_RE.search(text) or ACTIVE_HIDDEN_FRAMEWORK_RE.search(text))
    exception_visible = bool(CLEAR_EXCEPTION_RE.search(text))
    if framework_active and not matches:
        errors.append(f"{path}: operative framework/worldview covering requires a visible Concealment mode line")
    if framework_active and matches and not any("mode" in match.group("label").lower() for match in matches):
        errors.append(f"{path}: operative framework/worldview covering must use exact `Concealment mode:` label, not bare `concealment:`")
    for match in matches:
        value = match.group("value").strip().strip("*").strip()
        block = surrounding_block(text, match.start())
        if not value or NONE_PLACEHOLDER_RE.search(value):
            errors.append(f"{path}: concealment must not use placeholder {value!r}; use clear, mode-?, or an anchored mode")
        if CLEAR_VALUE_RE.search(value) and (
            FRAMEWORK_SIGNAL_RE.search(block) or ACTIVE_HIDDEN_FRAMEWORK_RE.search(text)
        ) and not (CLEAR_EXCEPTION_RE.search(block) or exception_visible):
            errors.append(
                f"{path}: concealment {value!r} conflicts with operative framework/worldview covering"
            )
    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("tests/concealment-mode"))
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0

    for path in valid:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = check_text(path, read_text(path))
        if not found:
            errors.append(f"{path}: expected-invalid concealment fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in args.outputs:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("concealment-mode check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("concealment-mode check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
