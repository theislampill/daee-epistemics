#!/usr/bin/env python3
"""Check modeled compiled-runtime file-call budgets."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


SKILL = "skill/SKILL.md"
FOUNDATION = "skill/references/runtime-foundation.md"
CORE = "skill/references/runtime-diagnostic-core.md"
PHASE2 = "skill/references/runtime-phase2-passes.md"
GATE = "skill/references/runtime-dispatch-gate.md"
OUTPUT = "skill/references/runtime-output-governance.md"
PROFILES = "skill/references/omnibus/OMNIBUS-profiles.md"
DO = "skill/references/omnibus/OMNIBUS-do-families.md"
RT = "skill/references/omnibus/OMNIBUS-rt-transmission.md"
TACTICS = "skill/references/omnibus/OMNIBUS-tactics.md"
TECHNIQUES = "skill/references/omnibus/OMNIBUS-techniques.md"
PROCEDURES = "skill/references/omnibus/OMNIBUS-procedures.md"
SPECIALTY = "skill/references/omnibus/OMNIBUS-specialty-diagnostics.md"


@dataclass(frozen=True)
class CaseClass:
    name: str
    category: str
    load_path: tuple[str, ...]
    normal: bool = True

    @property
    def threshold(self) -> int | None:
        if not self.normal:
            return None
        if self.category == "simple":
            return 5
        if self.category == "ordinary":
            return 12
        if self.category == "complex":
            return 20
        raise ValueError(f"unknown category: {self.category}")


CASES = [
    CaseClass("Simple glossary / factual query", "simple", (SKILL, FOUNDATION)),
    CaseClass("Ordinary theological or philosophical objection", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, DO, TACTICS)),
    CaseClass("Atheist / naturalist objection", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, PROFILES, TACTICS, TECHNIQUES)),
    CaseClass("Christian Trinity / incarnation / philosopher's-God case", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, DO, TACTICS, TECHNIQUES, SPECIALTY)),
    CaseClass("Revelation / transmission / canon case", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, RT, TECHNIQUES, TACTICS)),
    CaseClass("Hadith-authentication case", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, SPECIALTY, RT)),
    CaseClass("Kalamic / Maturidi evidentialist case", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, PROFILES, SPECIALTY, TECHNIQUES, TACTICS)),
    CaseClass("Grief-primary / identity-performance / thin-basis case", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, PROCEDURES, TACTICS)),
    CaseClass("Complex mixed higher-order case", "complex", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, PROFILES, DO, RT, TACTICS, TECHNIQUES, PROCEDURES, SPECIALTY)),
    CaseClass("Maximal audit / regression case", "audit", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, PROFILES, DO, RT, TACTICS, TECHNIQUES, PROCEDURES, SPECIALTY), normal=False),
]


def main() -> int:
    root = repo_root()
    errors: list[str] = []
    if not out_dir(root).is_dir():
        return fail_with_errors("consolidation call budget", ["skill runtime root is absent"])

    print("Case class call budget")
    print("------------------------------------------------------------")
    for case in CASES:
        count = len(case.load_path)
        threshold = case.threshold
        status = "PASS"
        if threshold is not None and count > threshold:
            status = "FAIL"
            errors.append(f"{case.name}: {count} calls exceeds threshold {threshold}")
        if threshold is None and count > 20 and case.normal:
            status = "FAIL"
            errors.append(f"{case.name}: exceeds 20 but is not marked non-normal")
        for rel in case.load_path:
            if not (root / rel).is_file():
                errors.append(f"{case.name}: load path missing: {rel}")
                status = "FAIL"
        label = f"<= {threshold}" if threshold is not None else "non-normal"
        print(f"{status:4} {count:2} calls ({label}): {case.name}")
    print("------------------------------------------------------------")

    return fail_with_errors("consolidation call budget", errors)


if __name__ == "__main__":
    sys.exit(main())
