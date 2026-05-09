#!/usr/bin/env python3
"""Narrow guard for recursion-collapse and noetic-frame control-plane drift."""

from __future__ import annotations

import sys
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


ROOT_REQUIRED = [
    "## EXECUTION SPINE",
    "Input -> IR(N,m,τ,σ) -> B -> {s1...sn} -> Land(B) -> R(H,Δ)",
    "Top-salient invariants",
    "recursive-state-transitions.md §Runtime Notation / Meta-Noetic",
    "Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB",
    "σ != operative warrant",
    "N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡ N_Wahhābī",
    "family label != operative N",
    "shared vocabulary != shared warrant",
    "N_Ashʿarī != N_Māturīdī != N_Taymiyyan",
    "H(n+1) = (Hn ∪ InputLive_n) - Released_n",
]

OWNER_REQUIRED = [
    "## Runtime Notation / Meta-Noetic Memetic Compression Layer",
    "operative compression for existing runtime behavior, not decorative formalism",
    "Input -> IR(N,m,τ,σ) -> B -> {s1...sn} -> Land(B) -> R(H,Δ)",
    "sᵢ != Bᵢ",
    "Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB",
    "σ != operative warrant",
    "N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡ N_Wahhābī",
    "N_Ashʿarī[*], N_Māturīdī[*] = family labels, not automatic operative N",
    "shared vocabulary != shared warrant",
    "N_Ashʿarī != N_Māturīdī != N_Taymiyyan",
    "H(n+1) = (Hn ∪ InputLive_n) - Released_n",
    "Land(B) -> R",
]

RUNTIME_REQUIRED = [
    "Operative submoves are not burden-cycles",
    "hiddenness/punishment/source-status can be operative submoves under one burden",
    "multi-burden does not mean multi-recursion by default",
    "Current bounded operator is one live noetic burden/function",
    "The imported criterion no longer governs as judge",
    "Source-Status & Noetic-Frame Non-Equivalence Discipline",
]

ROOT_FORBIDDEN = [
    "full audit render is the default",
    "normal public audit mode",
    "fuller `/daee-epistemics:audit` mode",
    "clean default `/daee-epistemics` mode",
    "clean default response with internal recursive governance",
]

POSITIVE_FRAME_FORBIDDEN = [
    "all provide acceptable ways to ground the answer",
    "all classically acceptable theological routes here",
    "mutually supportive ashʿarī",
    "ashʿarī/māturīdī support",
    "ashʿarī and māturīdī support",
]


def read(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing file: {path.as_posix()}")
        return ""
    return path.read_text(encoding="utf-8")


def contains(text: str, token: str) -> bool:
    return token.lower() in text.lower()


def main() -> int:
    root = repo_root()
    errors: list[str] = []

    skill_path = root / "atomics/skill/SKILL.md"
    skill_text = read(skill_path, errors)
    skill_lower = skill_text.lower()
    notation_path = root / "atomics/skill/references/diagnostics/recursive-state-transitions.md"
    notation_text = read(notation_path, errors)

    spine_idx = skill_text.find("## EXECUTION SPINE")
    reference_idx = skill_text.find("## Reference Architecture")
    if spine_idx == -1:
        errors.append("atomics/skill/SKILL.md missing EXECUTION SPINE")
    elif reference_idx != -1 and spine_idx > reference_idx:
        errors.append("EXECUTION SPINE appears after Reference Architecture")

    for token in ROOT_REQUIRED:
        if token not in skill_text:
            errors.append(f"root control plane missing notation/invariant: {token!r}")

    for token in OWNER_REQUIRED:
        if token not in notation_text:
            errors.append(f"notation owner missing invariant: {token!r}")

    if len(skill_text) > 80_000:
        errors.append(
            "atomics/skill/SKILL.md appears to have re-expanded beyond control-plane size"
        )

    if "Default-Mode Worked Example\n\n**Input." in skill_text:
        errors.append("worked examples have moved back into root SKILL.md")

    for token in ROOT_FORBIDDEN:
        if contains(skill_text, token):
            errors.append(f"stale public/default render framing in root SKILL.md: {token!r}")

    current_governance = "\n".join(
        read(root / rel, errors)
        for rel in [
            "atomics/skill/SKILL.md",
            "atomics/skill/references/diagnostics/routing-precedence.md",
            "atomics/skill/references/rubrics/diagnostic-render-contract.md",
            "atomics/skill/references/rubrics/output-release.md",
        ]
    ).lower()
    for token in POSITIVE_FRAME_FORBIDDEN:
        if token in current_governance:
            errors.append(f"positive rival-frame support phrase in current governance: {token!r}")

    runtime_text = "\n".join(
        read(out_dir(root) / rel, errors)
        for rel in [
            "SKILL.md",
            "references/runtime-dispatch-gate.md",
            "references/runtime-output-governance.md",
        ]
    )
    for token in RUNTIME_REQUIRED:
        if not contains(runtime_text, token):
            errors.append(f"compiled runtime missing collapse/noetic-frame invariant: {token!r}")

    if not errors:
        print("recursion collapse / noetic-frame guard: PASS")
        print(f"root SKILL.md characters: {len(skill_text)}")

    return fail_with_errors("recursion collapse / noetic-frame guard", errors)


if __name__ == "__main__":
    sys.exit(main())
