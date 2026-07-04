#!/usr/bin/env python3
"""Profile-catalogue vocabulary hygiene (Plan 07 / safety custody rule AM-3).

The per-interlocutor profile catalogue
(`atomics/skill/references/case-library/profiles/`) must not describe diagnosed
structures with offensive-register targeting verbs. Calling a restoration target
something to "exploit" or "weaponize" reframes bounded, restorative diagnosis as
an attack plan — the dual-use inversion the safety boundary forbids
(`docs/non-claims.md`; the non-manipulation / no-adversarial-memetic-design
boundary in `references/rubrics/output-release.md`). The hardening pass reworded
the one prior occurrence ("pressure point to exploit" -> restoration vocabulary);
this gate pins that clean state so the offensive register cannot silently return.

SCOPE: the profile catalogue only. Defensive descriptions elsewhere (e.g. "doubts
weaponized against sound knowledge" in VISION.md) are legitimate diagnosis of the
adversary's move and are intentionally out of scope. This is a lexical hygiene
gate, not a semantic manipulation-proofness claim (see docs/non-claims.md).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "atomics/skill/references/case-library/profiles"

# Offensive-register targeting verbs, whole-word, case-insensitive.
BANNED = re.compile(r"(?i)\b(exploit(?:s|ed|ing)?|weaponi[sz]e(?:s|d)?)\b")


def scan_text(rel_path: str, text: str) -> list[str]:
    """Pure scan: return one error per offensive-register hit (unit-tested)."""
    errors: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        match = BANNED.search(line)
        if match:
            errors.append(
                f"{rel_path}:{lineno}: offensive-register term {match.group(0)!r} in the profile "
                f"catalogue; use restoration vocabulary (e.g. 'restoration target' / 'live pressure')"
            )
    return errors


def self_test() -> int:
    bad = scan_text("x", "the Ashʿarī softening is a distinct pressure point to exploit.")
    good = scan_text("x", "the Ashʿarī softening is a distinct restoration target / live pressure.")
    defensive = scan_text("x", "weaponized")  # bare form still flagged inside profiles by design
    checks = [
        ("banned term flagged", len(bad) == 1),
        ("clean text accepted", good == []),
        ("weaponize flagged", len(defensive) == 1),
    ]
    ok = all(p for _, p in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"profile vocabulary-hygiene self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if not PROFILES.is_dir():
        print(f"profile catalogue not found: {PROFILES.relative_to(ROOT)}")
        return 1
    files = sorted(PROFILES.rglob("*.md"))
    errors: list[str] = []
    for path in files:
        errors.extend(scan_text(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8")))
    if errors:
        print("profile vocabulary-hygiene check: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print(f"profile vocabulary-hygiene check: PASS ({len(files)} profile files clean)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
