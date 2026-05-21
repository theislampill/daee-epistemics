"""Guard MRP runtime owners against smoke-case hard-coding.

The MRP runtime may define generic ledger and field-pressure semantics. Named
smoke cases belong in fixtures, audits, and case-library owners, not in the
always-loaded MRP architecture or render/release contracts.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]

RUNTIME_OWNER_PATHS = [
    "atomics/skill/SKILL.md",
    "atomics/skill/references/tactics/TTP-MRP-mid-reread-pressure.md",
    "atomics/skill/references/diagnostics/recursive-state-transitions.md",
    "atomics/skill/references/rubrics/diagnostic-render-contract.md",
    "atomics/skill/references/rubrics/output-release.md",
    "tools/build_compiled_runtime.py",
    "skill/SKILL.md",
    "skill/references/runtime-output-governance.md",
    "skill/references/omnibus/OMNIBUS-tactics.md",
]

CASE_HARDCODE_PATTERNS = [
    r"\bTrinitarian\s+D3/D6\b",
    r"\bTrinitarian\s+prooftext\b",
    r"\bJohn\s+17(?::3)?\b",
    r"\bTST\s*/\s*Satanic\b",
    r"\bSatanic\s+Temple\b",
    r"\bKhaybar\s*/\s*prophetic-protection\b",
    r"\bmystery-shield\b",
    r"\bmystery\s+shield\b",
    r"\bincomprehensibility\s+shield\b",
    r"\bcreedal-immunity\b",
    r"\bsacred-doctrine\s+immunity\b",
    r"\bborrowed\s+moral\s+capital\b",
    r"\brebellion-as-virtue\b",
    r"\bfailed-protection\s+optics\b",
    r"\bmartyrdom-concession\b",
    r"\bgenerated\s+recoil\b",
]

CASE_HARDCODE_RE = re.compile("|".join(CASE_HARDCODE_PATTERNS), re.IGNORECASE)

GENERIC_REQUIRED = [
    "𝔅_LA",
    "𝔅_MRP",
    "𝔅_total",
    "held_burden_activation",
    "generated_burden_instantiation",
    "Route-gradient",
    "MRP route result type",
    "[generated-by: MRP(",
    "R(H,Δ)",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    errors: list[str] = []
    checked = 0
    for rel in RUNTIME_OWNER_PATHS:
        path = ROOT / rel
        if not path.exists():
            continue
        checked += 1
        text = read(path)
        for match in CASE_HARDCODE_RE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            snippet = text[match.start() : match.end()]
            errors.append(
                f"{rel}:{line}: case-specific MRP obligation/probe is not allowed in runtime owner: {snippet!r}"
            )

    source_text = "\n".join(read(ROOT / rel) for rel in RUNTIME_OWNER_PATHS[:5] if (ROOT / rel).exists())
    for token in GENERIC_REQUIRED:
        if token not in source_text:
            errors.append(f"generic MRP formalism token missing from atomics runtime owners: {token}")

    if errors:
        print("MRP de-specialization check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"MRP de-specialization check passed ({checked} runtime owner surfaces checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
