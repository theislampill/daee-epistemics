#!/usr/bin/env python3
"""Check Phase 6 recursive traversal governance in source and runtime."""

from __future__ import annotations

import sys
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


SOURCE_FILES = [
    "atomics/skill/SKILL.md",
    "atomics/skill/references/diagnostics/diagnostic-ir.md",
    "atomics/skill/references/diagnostics/framework-pipeline.md",
    "atomics/skill/references/rubrics/output-release.md",
    "atomics/skill/references/rubrics/diagnostic-render-contract.md",
    "atomics/skill/references/procedures/P7-restoration-stops.md",
]

RUNTIME_FILES = [
    "SKILL.md",
    "references/runtime-dispatch-gate.md",
    "references/runtime-output-governance.md",
]

GLOBAL_INVARIANTS = [
    "State Refresh",
    "eligible live door",
    "held routes rechecked",
    "STOP / HOLD / RECURSE / PARTIAL",
    "no premature STOP",
    "recursion is not argument dump",
    "one door at a time",
    "traversal-delayed, not permanently suppressed",
]

DECISION_INVARIANTS = [
    "STOP is valid only",
    "no eligible live door",
    "RECURSE",
    "PARTIAL",
    "HOLD",
    "absent release signal",
    "limits prevent",
]

PASS_SHAPE_INVARIANTS = [
    "Live door:",
    "Why already present:",
    "Released module(s):",
    "Bounded move:",
    "State refresh:",
    "Governance: STOP",
]


def read_file(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing file: {path.as_posix()}")
        return ""
    return path.read_text(encoding="utf-8")


def contains(corpus: str, token: str) -> bool:
    return token.lower() in corpus.lower()


def check_tokens(label: str, corpus: str, tokens: list[str], errors: list[str]) -> None:
    for token in tokens:
        if not contains(corpus, token):
            errors.append(f"{label}: missing invariant token: {token!r}")


def main() -> int:
    root = repo_root()
    compiled_root = out_dir(root)
    errors: list[str] = []

    source_texts = [read_file(root / rel, errors) for rel in SOURCE_FILES]
    source_corpus = "\n".join(source_texts)

    if not compiled_root.is_dir():
        return fail_with_errors("recursive traversal governance", ["skill runtime root is absent"])

    runtime_texts = [read_file(compiled_root / rel, errors) for rel in RUNTIME_FILES]
    runtime_corpus = "\n".join(runtime_texts)

    check_tokens("atomized source", source_corpus, GLOBAL_INVARIANTS, errors)
    check_tokens("generated runtime", runtime_corpus, GLOBAL_INVARIANTS, errors)
    check_tokens("generated runtime decision semantics", runtime_corpus, DECISION_INVARIANTS, errors)
    check_tokens("generated runtime recursive pass shape", runtime_corpus, PASS_SHAPE_INVARIANTS, errors)

    # Make sure the critical STOP/RECURSE distinction is represented in more
    # than one generated surface, so it is not lost if one section is skipped.
    stop_surfaces = sum(1 for text in runtime_texts if contains(text, "no premature STOP"))
    door_surfaces = sum(1 for text in runtime_texts if contains(text, "eligible live door"))
    if stop_surfaces < 2:
        errors.append("generated runtime: no premature STOP invariant appears in fewer than two runtime surfaces")
    if door_surfaces < 2:
        errors.append("generated runtime: eligible live door invariant appears in fewer than two runtime surfaces")

    print("Recursive traversal governance summary")
    print("------------------------------------------------------------")
    print(f"Source files checked: {len(SOURCE_FILES)}")
    print(f"Runtime files checked: {len(RUNTIME_FILES)}")
    print(f"Global invariants checked: {len(GLOBAL_INVARIANTS)}")
    print(f"Decision invariants checked: {len(DECISION_INVARIANTS)}")
    print(f"Pass-shape invariants checked: {len(PASS_SHAPE_INVARIANTS)}")
    print(f"Runtime no-premature-STOP surfaces: {stop_surfaces}")
    print(f"Runtime eligible-live-door surfaces: {door_surfaces}")
    print("------------------------------------------------------------")
    return fail_with_errors("recursive traversal governance", errors)


if __name__ == "__main__":
    sys.exit(main())
