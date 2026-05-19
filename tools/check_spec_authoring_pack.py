"""Low-noise checks for PACK-SPEC and operating-discipline governance wiring."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_FILES = [
    Path("AGENTS.md"),
    Path("docs/spec-authoring-pack.md"),
    Path("docs/governance/operating-discipline.md"),
]

REQUIRED_AGENTS_TERMS = [
    "PACK-SPEC",
    "Gemba",
    "Hoshin Kanri",
    "Nemawashi",
    "Muda / Mura / Muri",
    "Kaizen",
    "PDCA",
    "Andon",
    "Hansei",
    "5 Whys",
    "Smoke Before Claim",
    "Plan Closure",
]

REQUIRED_PACK_DOC_TERMS = [
    "RFC 2119/8174",
    "Stop reason pattern",
    "When not to use PACK-SPEC",
]

REQUIRED_OPERATING_DOC_TERMS = [
    "Gemba",
    "Hoshin Kanri",
    "Nemawashi",
    "Muda / Mura / Muri",
    "Kaizen",
    "PDCA",
    "Andon",
    "Hansei",
    "5 Whys",
    "Smoke Before Claim",
    "Plan Closure",
]

CONTRACT_OWNER_POINTERS = [
    Path("atomics/skill/references/rubrics/diagnostic-render-contract.md"),
    Path("atomics/skill/references/rubrics/output-release.md"),
    Path("atomics/skill/references/diagnostics/diagnostic-ir.md"),
    Path("atomics/skill/references/diagnostics/recursive-state-transitions.md"),
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def require_contains(path: Path, terms: list[str], errors: list[str]) -> None:
    text = read(path)
    for term in terms:
        if term not in text:
            errors.append(f"{path}: missing `{term}`")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-owner-pointers",
        action="store_true",
        help="Only check top-level governance docs, not contract-owner PACK-SPEC notes.",
    )
    args = parser.parse_args()

    errors: list[str] = []

    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"{path}: missing required governance file")

    if not errors:
        require_contains(Path("AGENTS.md"), REQUIRED_AGENTS_TERMS, errors)
        require_contains(Path("docs/spec-authoring-pack.md"), REQUIRED_PACK_DOC_TERMS, errors)
        require_contains(
            Path("docs/governance/operating-discipline.md"),
            REQUIRED_OPERATING_DOC_TERMS,
            errors,
        )

    if not args.skip_owner_pointers:
        for path in CONTRACT_OWNER_POINTERS:
            if not path.exists():
                errors.append(f"{path}: missing contract owner")
                continue
            text = read(path)
            if "PACK-SPEC note:" not in text or "docs/spec-authoring-pack.md" not in text:
                errors.append(f"{path}: missing PACK-SPEC owner pointer")

    if errors:
        print("PACK-SPEC governance check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PACK-SPEC governance check: PASS")
    print(f"Governance files checked: {len(REQUIRED_FILES)}")
    if not args.skip_owner_pointers:
        print(f"Contract owner pointers checked: {len(CONTRACT_OWNER_POINTERS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
