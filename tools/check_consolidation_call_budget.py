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
# GATE and OUTPUT were single-file bundles pre-Slice-C (runtime-dispatch-gate.md,
# runtime-output-governance.md). Slice C split each into route shards (see
# tools/compiled_runtime_lib.py BUNDLE_SOURCES). Each is now a TUPLE of the
# successor shard paths, but is still counted as ONE LOGICAL UNIT in the call-budget
# math below (see logical_call_count()) -- the split relocates modules into
# separately loadable files but does not change how many "logical" gate/output
# calls a case makes, so the split must not silently tighten these thresholds by
# inflating a single conceptual load into many counted calls.
GATE = (
    "skill/references/runtime-core-ir.md",
    "skill/references/runtime-core-pipeline.md",
    "skill/references/runtime-core-recursion.md",
    "skill/references/runtime-core-routing.md",
    "skill/references/runtime-shard-ir-support.md",
    "skill/references/runtime-shard-diagnostic.md",
    "skill/references/runtime-shard-audit.md",
    "skill/references/runtime-shard-thesis.md",
    "skill/references/runtime-shard-restoration.md",
)
OUTPUT = (
    "skill/references/runtime-shard-output-release.md",
    "skill/references/runtime-shard-render-contract.md",
)
PROFILES = "skill/references/omnibus/OMNIBUS-profiles.md"
DO = "skill/references/omnibus/OMNIBUS-do-families.md"
RT = "skill/references/omnibus/OMNIBUS-rt-transmission.md"
TACTICS = "skill/references/omnibus/OMNIBUS-tactics.md"
TECHNIQUES = "skill/references/omnibus/OMNIBUS-techniques.md"
PROCEDURES = "skill/references/omnibus/OMNIBUS-procedures.md"
SPECIALTY = "skill/references/omnibus/OMNIBUS-specialty-diagnostics.md"


def flatten_load_path(load_path: tuple[str | tuple[str, ...], ...]) -> list[str]:
    """Flatten a load_path whose entries may be single files or logical-unit tuples."""
    flattened: list[str] = []
    for entry in load_path:
        if isinstance(entry, tuple):
            flattened.extend(entry)
        else:
            flattened.append(entry)
    return flattened


def logical_call_count(load_path: tuple[str | tuple[str, ...], ...]) -> int:
    """Count each top-level entry as ONE logical call, even if it is a multi-file
    shard-group tuple (GATE, OUTPUT). This preserves the pre-split threshold math:
    a case that used to make one dispatch-gate call and one output-governance call
    still counts as making exactly those two logical calls, regardless of how many
    physical shard files those bundles were divided into.
    """
    return len(load_path)


@dataclass(frozen=True)
class CaseClass:
    name: str
    category: str
    load_path: tuple[str | tuple[str, ...], ...]
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
    CaseClass("Ḥadīth-authentication case", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, SPECIALTY, RT)),
    CaseClass("Kalāmic / Māturīdī evidentialist case", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, PROFILES, SPECIALTY, TECHNIQUES, TACTICS)),
    CaseClass("Grief-primary / identity-performance / thin-basis case", "ordinary", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, PROCEDURES, TACTICS)),
    CaseClass("Complex mixed higher-order case", "complex", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, PROFILES, DO, RT, TACTICS, TECHNIQUES, PROCEDURES, SPECIALTY)),
    CaseClass("Maximal audit / regression case", "audit", (SKILL, FOUNDATION, CORE, PHASE2, GATE, OUTPUT, PROFILES, DO, RT, TACTICS, TECHNIQUES, PROCEDURES, SPECIALTY), normal=False),
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    root = repo_root()
    errors: list[str] = []
    if not out_dir(root).is_dir():
        return fail_with_errors("consolidation call budget", ["skill runtime root is absent"])

    print("Case class call budget")
    print("------------------------------------------------------------")
    for case in CASES:
        count = logical_call_count(case.load_path)
        threshold = case.threshold
        status = "PASS"
        if threshold is not None and count > threshold:
            status = "FAIL"
            errors.append(f"{case.name}: {count} calls exceeds threshold {threshold}")
        if threshold is None and count > 20 and case.normal:
            status = "FAIL"
            errors.append(f"{case.name}: exceeds 20 but is not marked non-normal")
        for rel in flatten_load_path(case.load_path):
            if not (root / rel).is_file():
                errors.append(f"{case.name}: load path missing: {rel}")
                status = "FAIL"
        label = f"<= {threshold}" if threshold is not None else "non-normal"
        print(f"{status:4} {count:2} calls ({label}): {case.name}")
    print("------------------------------------------------------------")

    return fail_with_errors("consolidation call budget", errors)


if __name__ == "__main__":
    sys.exit(main())
