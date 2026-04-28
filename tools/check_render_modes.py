#\!/usr/bin/env python3
"""Check v0.3.0.0 render-mode governance in the generated runtime.

Invariants verified:
  - All three canonical render modes are named in the runtime.
  - Default mode is prose-first with no giant ledger by default.
  - [Diagnostic IR] code-fenced block is prohibited in default output.
  - Discipline-universal / printout-mode-specific invariant is present.
  - :dsl owns compact diagnostic / lab-report output.
  - :audit owns full procedural audit output.
  - grim-reaper discipline applies universally; printout belongs to :audit.
  - Recursive traversal governance is universal across modes.
  - Forbidden claims (behavioral parity, mandatory ledger, etc.) are absent.
"""

from __future__ import annotations

import sys
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


RUNTIME_FILES = [
    "SKILL.md",
    "references/runtime-output-governance.md",
    "references/runtime-dispatch-gate.md",
]

# Tokens that must appear somewhere in the combined runtime surfaces.
REQUIRED_TOKENS = [
    # Three canonical render modes
    "/daee-epistemics",
    "/daee-epistemics:dsl",
    "/daee-epistemics:audit",
    # Default mode is prose-first
    "default render mode",
    "no giant load ledger by default",
    "prose-first",
    # Discipline is universal; printout is mode-specific
    "discipline is universal",
    "printout is mode-specific",
    # grim-reaper discipline vs printout distinction
    "grim-reaper discipline applies",
    "grim-reaper printout",
    # IR is internal, not a printout template
    "internal state object",
    "not a printout template",
    # Default mode prohibition: IR block must not appear
    "must not appear in the public response",
    # DSL mode owns compact diagnostic
    "compact diagnostic",
    # Audit mode owns full procedural
    "procedural audit",
    # Recursive governance is universal
    "Diagnostic IR",
    "State Refresh",
    "live door",
    "held routes",
    "STOP / HOLD / RECURSE / PARTIAL",
    # Path resolution invariants
    "bundle availability is not activation",
    "compiled-module-map.json",
    # Deprecated grim-reaper prompt
    "old grim-reaper prompt is deprecated",
]

# Tokens that must NOT appear in the generated runtime.
FORBIDDEN_TOKENS = [
    "grim-reaper prompt required",
    "giant load ledger required",
    "omnibus names as matched_modules",
    "behavioral parity guaranteed",
    "full audit render is the default",
]

# Tokens that must appear in the dispatch-gate bundle specifically,
# confirming the IR render-mode policy was compiled in.
DISPATCH_GATE_REQUIRED = [
    "render-mode policy",
    "internal state object",
    "must not appear in the public response",
    "discipline is universal",
    "printout is mode-specific",
]


def read_runtime(root: Path, errors: list) -> str:
    runtime_root = out_dir(root)
    if not runtime_root.is_dir():
        errors.append("skill runtime root is absent")
        return ""
    parts = []
    for rel_path in RUNTIME_FILES:
        path = runtime_root / rel_path
        if not path.is_file():
            errors.append(f"missing runtime render-mode surface: skill/{rel_path}")
            continue
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def read_dispatch_gate(root: Path, errors: list) -> str:
    path = out_dir(root) / "references/runtime-dispatch-gate.md"
    if not path.is_file():
        errors.append("dispatch-gate bundle missing for render-mode policy check")
        return ""
    return path.read_text(encoding="utf-8")


def main() -> int:
    root = repo_root()
    errors = []

    corpus = read_runtime(root, errors)
    lower = corpus.lower()

    for token in REQUIRED_TOKENS:
        if token.lower() not in lower:
            errors.append(f"missing render-mode invariant in generated runtime: {token!r}")

    for token in FORBIDDEN_TOKENS:
        if token.lower() in lower:
            errors.append(f"forbidden render-mode claim in generated runtime: {token!r}")

    gate_text = read_dispatch_gate(root, errors)
    gate_lower = gate_text.lower()
    for token in DISPATCH_GATE_REQUIRED:
        if token.lower() not in gate_lower:
            errors.append(
                f"dispatch-gate bundle missing render-mode policy token: {token!r}"
            )

    if not errors:
        print("Render mode governance summary")
        print("-" * 60)
        print(f"Runtime files checked: {len(RUNTIME_FILES)}")
        print(f"Required invariants checked: {len(REQUIRED_TOKENS)}")
        print(f"Forbidden claims checked: {len(FORBIDDEN_TOKENS)}")
        print(f"Dispatch-gate policy tokens checked: {len(DISPATCH_GATE_REQUIRED)}")
        print("-" * 60)

    return fail_with_errors("render mode governance", errors)


if __name__ == "__main__":
    sys.exit(main())
