#!/usr/bin/env python3
"""Guard the Pipeline #2 derived/conditional bridge against drift."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


REGISTER_SCHEMA_KEYS = {
    "heart",
    "xi",
    "Omega",
    "omega",
    "mu",
    "kappa",
    "♥",
    "ξ",
    "Ω",
    "μ",
    "κ",
}

REQUIRED_TOKENS = {
    "docs/algebraic-notation-and-noetic-formalism.md": [
        "Pipeline #2 is implemented in this repo as",
        "a derived/conditional bridge",
        "𝓝 ⊢ D₀ ⇝ Ψᴺ",
        "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
        "R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)",
        "𝒞(Ψᴺ)",
        "N_fiṭrī ∧ ʿaql ṣarīḥ",
        "Shannon entropy measures truth",
        "Symbol theater",
        "not mandatory schema fields",
    ],
    "docs/pipeline2-implementation-ledger.md": [
        "| `𝓝` noetic-structure selection space |",
        "| `D₀` surface discourse / signal |",
        "| `Ψᴺ` encoded noetic signal-state |",
        "| `N∈𝓝` runtime-selected noetic frame |",
        "| `IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` derived bridge |",
        "| `♥` affective-discursive register / release-posture control |",
        "| `ξ` epistemic/warrant grammar |",
        "| `Ω` ontological/predication grammar |",
        "| `μ` meta-noetic memetic carrier/stabilizer |",
        "| `κ` collapse radius / downstream dependency set |",
        "| `Δκ` reread input after burden landing |",
        "| `𝒞(Ψᴺ)` constrained noetic collapse / discursive resolution |",
        "| `N_fiṭrī ∧ ʿaql ṣarīḥ` restorative terminal-state formalism |",
        "DEFERRED WITH BLOCKER",
        "breaks current Diagnostic IR schema",
    ],
    "atomics/skill/references/diagnostics/nomenclature-normalization.md": [
        "Pipeline #2 theory/specification bridge",
        "derived/conditional",
        "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
        "Current hard schema remains",
        "kappa",
    ],
    "atomics/skill/references/diagnostics/diagnostic-ir.md": [
        "Pipeline #2 bridge status",
        "D0 -> PsiN<N,m,tau,sigma,H>",
        "𝓝 ⊢ D₀ ⇝ Ψᴺ",
        "derived/conditional runtime bridge",
        "mandatory JSON/schema fields",
        "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
        "evidence, testimony, authority, proof-method",
        "predication, modality, dependence",
        "carrier, compression, stabilizer",
    ],
    "atomics/skill/references/diagnostics/noetic-reading-checklist.md": [
        "Pipeline #2 signal-state bridge",
        "D0",
        "PsiN",
        "N in N_space",
        "Derived register bridge",
    ],
    "atomics/skill/references/diagnostics/recursive-state-transitions.md": [
        "Sameτ ∧ Sameξ ∧ SameΩ ∧ Sameσ ∧ Sameκ",
        "ⁿBᵢ[OP] : target -> operation -> result -> ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ",
        "R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)",
        "not a generic TODO list",
        "Terminal formalism",
        "𝒞(Ψᴺ)",
        "N_fiṭrī ∧ ʿaql ṣarīḥ",
    ],
    "atomics/skill/references/rubrics/output-release.md": [
        "Derived register release discipline",
        "Terminal release boundary",
        "owner/TTP execution",
        "ΔⁿB",
        "`κ` is not a TODO list",
        "R(H,Delta)",
    ],
    "atomics/skill/references/rubrics/diagnostic-render-contract.md": [
        "Expanded formalism render boundary",
        "Anti-symbol-theater rule",
        "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
        "N_fiṭrī ∧ ʿaql ṣarīḥ",
    ],
    "atomics/skill/references/diagnostics/framework-pipeline.yaml": [
        "Pipeline #2 derived bridge maps D0 -> PsiN -> IR without hard schema fields",
        "pipeline2_derived_bridge",
        "ⁿBᵢ[OP] : target -> operation -> result -> ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ",
        "Delta-kappa dependency-radius changes are consumed before closure",
    ],
    "README.md": [
        "Pipeline #2 derived/conditional bridge",
        "docs/pipeline2-implementation-ledger.md",
        "not mandatory runtime schema fields",
    ],
    "TODO.md": [
        "Pipeline #2 Hard Schema / Release Migration Decision",
        "derived/conditional bridge semantics are now canonical",
        "Do not claim v0.4.0.0 readiness",
    ],
    "AGENTS.md": [
        "python tools/check_pipeline2_bridge.py",
        "Pipeline #2 derived/conditional bridge semantics are",
        "do not claim a release-line migration from the index page alone",
    ],
}

GENERATED_REQUIRED = {
    "skill/references/runtime-dispatch-gate.md": [
        "Pipeline #2 bridge status",
        "derived/conditional runtime bridge",
        "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
        "Sameτ ∧ Sameξ ∧ SameΩ ∧ Sameσ ∧ Sameκ",
        "R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)",
        "Terminal formalism",
    ],
    "skill/references/runtime-output-governance.md": [
        "Derived register release discipline",
        "Terminal release boundary",
        "Anti-symbol-theater rule",
        "Expanded formalism render boundary",
    ],
}

INDEX_REQUIRED = [
    "algebraic-notation-and-noetic-formalism.md",
    "pipeline2-implementation-ledger.md",
    "Pipeline #1",
    "Pipeline #2",
    "derived/conditional bridge",
    "hard schema",
    "current runtime state",
    "Shannon entropy measures truth",
]

INDEX_FORBIDDEN = [
    "Pipeline #2 — target repo state",
    "Pipeline #2 - target repo state",
    "not yet first-class registers",
    "Defer as runtime",
    "Pipeline #2 as current runtime architecture",
]


def read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def check_required_tokens(root: Path, errors: list[str]) -> None:
    for rel, tokens in REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: missing")
            continue
        text = read(root, rel)
        for token in tokens:
            if token not in text:
                errors.append(f"{rel}: missing token {token!r}")


def check_generated_tokens(root: Path, errors: list[str]) -> None:
    if not out_dir(root).exists():
        errors.append("skill/: generated runtime missing; run build_compiled_runtime.py first")
        return
    for rel, tokens in GENERATED_REQUIRED.items():
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: generated file missing")
            continue
        text = read(root, rel)
        for token in tokens:
            if token not in text:
                errors.append(f"{rel}: missing generated token {token!r}")


def iter_schema_field_names(node: object) -> list[str]:
    names: list[str] = []
    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key, value in properties.items():
                if isinstance(key, str):
                    names.append(key)
                names.extend(iter_schema_field_names(value))

        required = node.get("required")
        if isinstance(required, list):
            names.extend(item for item in required if isinstance(item, str))

        for key, value in node.items():
            if key in {"properties", "required"}:
                continue
            names.extend(iter_schema_field_names(value))
    elif isinstance(node, list):
        for item in node:
            names.extend(iter_schema_field_names(item))
    return names


def check_schema_guard(root: Path, errors: list[str]) -> None:
    for rel in (
        "atomics/skill/references/diagnostics/diagnostic-ir.schema.json",
        "skill/references/diagnostics/diagnostic-ir.schema.json",
    ):
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: schema missing")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        forbidden = sorted(set(iter_schema_field_names(data)) & REGISTER_SCHEMA_KEYS)
        if forbidden:
            errors.append(f"{rel}: hard Pipeline #2 register schema fields present: {forbidden}")


def check_ledger_status(root: Path, errors: list[str]) -> None:
    text = read(root, "docs/pipeline2-implementation-ledger.md")
    implemented_rows = [
        "`𝓝` noetic-structure selection space",
        "`D₀` surface discourse / signal",
        "`Ψᴺ` encoded noetic signal-state",
        "`N∈𝓝` runtime-selected noetic frame",
        "`IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` derived bridge",
        "`♥` affective-discursive register",
        "`ξ` epistemic/warrant grammar",
        "`Ω` ontological/predication grammar",
        "`μ` meta-noetic memetic carrier",
        "`κ` collapse radius",
        "`Δκ` reread input",
        "`𝒞(Ψᴺ)` constrained noetic collapse",
        "`N_fiṭrī ∧ ʿaql ṣarīḥ` restorative terminal-state formalism",
        "Same-burden / next-burden algebra",
        "Shannon analogy boundary",
        "Anti-symbol-theater guard",
        "Anti-schema-bloat guard",
    ]
    for label in implemented_rows:
        matching_lines = [line for line in text.splitlines() if label in line]
        if not matching_lines:
            errors.append(f"ledger: missing row {label!r}")
            continue
        if not any("| IMPLEMENTED |" in line for line in matching_lines):
            errors.append(f"ledger: row {label!r} is not IMPLEMENTED")


def check_index(root: Path, errors: list[str]) -> None:
    path = root / "docs/index.html"
    if not path.exists():
        errors.append("docs/index.html: missing")
        return
    text = path.read_text(encoding="utf-8")
    if len(text) < 1_000_000:
        errors.append("docs/index.html: rich interactive page appears flattened (<1MB)")
    for token in INDEX_REQUIRED:
        if token not in text:
            errors.append(f"docs/index.html: missing token {token!r}")
    for token in INDEX_FORBIDDEN:
        if token in text:
            errors.append(f"docs/index.html: stale/proposal token remains {token!r}")


def main() -> int:
    root = repo_root()
    errors: list[str] = []
    check_required_tokens(root, errors)
    check_generated_tokens(root, errors)
    check_schema_guard(root, errors)
    check_ledger_status(root, errors)
    check_index(root, errors)
    return fail_with_errors("pipeline2 bridge", errors)


if __name__ == "__main__":
    raise SystemExit(main())
