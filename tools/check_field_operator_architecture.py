#!/usr/bin/env python3
"""Guard the field-operator architecture upgrade against ornamental drift.

The checker proves that the four v0.4.1.0 field-operator additions are
owner-defined, rendered in generated docs, fixture-backed, and protected by
negative boundaries:

* plain ∇ as owner-gated route-gradient pressure;
* LoopBreak(∇×T) as a target/ground/Delta/reread loop-breaking submove;
* 𝒞(Ψᴺ) as a positive closure-field condition;
* Ψᴺ / Ψᴵ language-mediated coupling without uptake or soul-access claims.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, repo_root

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


OWNER_TOKEN_REQUIREMENTS: dict[str, list[str]] = {
    "atomics/skill/references/diagnostics/recursive-state-transitions.md": [
        "Plain `∇` is the route-gradient read over the live field",
        "Routing remains owner-gated and catalogue-constrained",
        "not a bypass around gates",
        "not a replacement for\n`Δ`, `∇·`, or `∇×`",
        "LoopBreak(∇×T)",
        "target loop",
        "grounding source",
        "post-break `∇×T` reread",
        "Terminal formalism: `𝒞(Ψᴺ)` names the positive closure-field condition over the agent execution\nfield",
        "not a claim that the interlocutor has internally accepted truth",
        "`Ψᴺ` names the agent/runtime noetic execution field",
        "`Ψᴵ` names the diagnosed\ninterlocutor noetic field",
        "T_lang: Ψᴺ ⇢ Ψᴵ",
        "does not assert access to the interlocutor's soul",
        "guarantee acceptance",
        "claim the agent controls guidance",
    ],
    "atomics/skill/references/diagnostics/diagnostic-ir.md": [
        "∇ route-gradient",
        "`PsiN` / `Ψᴺ` is the agent/runtime execution field",
        "diagnosed interlocutor field `PsiI` / `Ψᴵ`",
        "must not claim access to the interlocutor's soul",
        "guaranteed uptake",
    ],
    "atomics/skill/references/rubrics/output-release.md": [
        "∇ route-gradient over eligible live pressure",
        "LoopBreak(∇×T)",
        "𝒞(Ψᴺ)",
        "Ψᴵ",
        "T_lang",
    ],
    "atomics/skill/references/rubrics/diagnostic-render-contract.md": [
        "∇ route: B2 pressure highest",
        "LoopBreak(∇×T)",
        "𝒞(Ψᴺ)",
        "T_lang: Ψᴺ ⇢ Ψᴵ",
    ],
    "docs/algebraic-notation-and-noetic-formalism.md": [
        "| `∇` |",
        "| `LoopBreak(∇×T)`",
        "| `𝒞(Ψᴺ)`",
        "| `Ψᴵ`",
        "| `T_lang: Ψᴺ ⇢ Ψᴵ`",
        "Operator Typing / Schema-Light Formal Types",
        "route-ranking functional",
        "preorder/scored ordering",
        "Small-Step Transition Model",
        "partial coupling relation",
        "not an isomorphism",
        "not a surjection",
        "Plain `∇` is the route-gradient operator",
        "LoopBreak(∇×T)",
        "positive closure-field condition",
        "language-mediated coupling",
    ],
    "docs/package-smoke-readiness.md": [
        "Marker-Theater Trap",
        "Witness labels present but local target/operation/result work absent",
        "Route-pressure stability under paraphrase",
        "False-route resistance under tempting but disallowed operators",
        "Marker presence remains structural/render evidence only",
    ],
    "docs/register-formalism-implementation-ledger.md": [
        "| `∇` route-gradient pressure |",
        "| `LoopBreak(∇×T)` curl-resolution submove |",
        "| `𝒞(Ψᴺ)` positive closure-field condition |",
        "| `Ψᴵ` and `T_lang: Ψᴺ ⇢ Ψᴵ` coupling boundary |",
    ],
    "atomics/skill/references/diagnostics/framework-pipeline.yaml": [
        "ROUTE-GRADIENT PRESSURE",
        "FIELD DIAGNOSTICS",
        "LOOP-BREAKING SUBMOVE",
        "C(PsiN) CLOSURE-FIELD CONDITION",
        "LANGUAGE-MEDIATED COUPLING",
        "route_gradient_pressure",
        "loop_breaking_submove",
        "closure_field_condition",
        "agent_interlocutor_field_boundary",
    ],
}

DOCS_INDEX_SOURCE_TOKENS = {
    "docs/index/sections/architecture.html": [
        "Gate/routing + ∇ route-gradient",
        "LoopBreak if ∇×T nonzero",
        "∇·T / ∇×T target-explicit diagnostics",
        "T ∈ {κ, ⁿB, ξ, Ω, ♥, μ, H, route, register, Ψᴺ-slice}",
        "LoopBreak(∇×T) ⊢ target loop + G + ⁿBᵢ[OPᵢ] + Δ + R",
        "G ∈ {fiṭrah, ʿaql ṣarīḥ, necessary knowledge, definition discipline, direct contradiction exposure, source-status correction}",
        "𝒞(Ψᴺ)",
        "T_lang: Ψᴺ ⇢ Ψᴵ",
    ],
    "docs/index/sections/theory.html": [
        "data-k=\"gradient\"",
        "data-k=\"loopBreak\"",
        "goConceptField('PsiI')",
        "data-k=\"coupling\"",
        "goConceptField('gradient')",
        "goConceptField('loopBreak')",
        "goConceptField('PsiI')",
        "goConceptField('coupling')",
        "LoopBreak(∇×T)",
        "LoopBreak(∇×T) ⊢ target loop + G + ⁿBᵢ[OPᵢ] + Δ + R",
        "T ∈ {κ, ⁿB, ξ, Ω, ♥, μ, H, route, register, Ψᴺ-slice}",
        "∇ ranks eligible route pressure before release",
        "Δ produces the changed field state",
        "∇·T / ∇×T diagnose target-explicit post-Δ field pressure",
        "R(H,Δ) rereads the changed field",
        "𝒞(Ψᴺ) licenses closure as field condition",
        "T_lang: Ψᴺ ⇢ Ψᴵ marks public coupling without guaranteed uptake",
        "𝒞(Ψᴺ)",
        "T_lang: Ψᴺ ⇢ Ψᴵ",
    ],
    "docs/index/templates/index.html.tpl": [
        "field-operator-architecture-v19",
        "id:'gradient'",
        "id:'loopBreak'",
        "id:'PsiI'",
        "id:'coupling'",
        "rel-live-field-gradient",
        "rel-gradient-gate-constrained",
        "rel-curl-loopbreak",
        "rel-closure-field-condition",
        "rel-agent-interlocutor-coupling",
    ],
}

GENERATED_DOC_TOKENS = {
    "docs/index.html": [
        "field-operator-architecture-v19",
        "id:'gradient'",
        "id:'loopBreak'",
        "id:'PsiI'",
        "id:'coupling'",
        "Gate/routing + ∇ route-gradient",
        "LoopBreak if ∇×T nonzero",
        "∇·T / ∇×T target-explicit diagnostics",
        "LoopBreak(∇×T) ⊢ target loop + G + ⁿBᵢ[OPᵢ] + Δ + R",
        "T ∈ {κ, ⁿB, ξ, Ω, ♥, μ, H, route, register, Ψᴺ-slice}",
        "∇ ranks eligible route pressure before release",
        "Δ produces the changed field state",
        "∇·T / ∇×T diagnose target-explicit post-Δ field pressure",
        "R(H,Δ) rereads the changed field",
        "𝒞(Ψᴺ) licenses closure as field condition",
        "T_lang: Ψᴺ ⇢ Ψᴵ marks public coupling without guaranteed uptake",
        "𝒞(Ψᴺ)",
        "T_lang: Ψᴺ ⇢ Ψᴵ",
    ],
    "docs/daee-epistemics-pipeline.html": [
        "ROUTE-GRADIENT PRESSURE",
        "LOOP-BREAKING SUBMOVE",
        "𝒞(Ψᴺ) CLOSURE-FIELD CONDITION",
        "T_lang: Ψᴺ ⇢ Ψᴵ",
    ],
}

FIXTURE = Path("tests/register-formalism-bridge-fixtures/10-field-gradient-loop-closure-coupling.json")

FORBIDDEN_PATTERNS = {
    "gradient-replaces-delta": re.compile(r"∇.{0,60}(?:replaces|substitutes for).{0,60}Δ", re.I | re.S),
    "gradient-bypasses-gates": re.compile(r"∇.{0,80}(?:bypasses|overrides).{0,80}(?:gate|catalogue|IR|routing)", re.I | re.S),
    "gradient-truth-metric": re.compile(r"∇.{0,80}(?:measures|proves|guarantees).{0,80}(?:truth|warrant)", re.I | re.S),
    "loopbreak-arbitrary": re.compile(r"LoopBreak.{0,80}(?:arbitrary assertion|ungrounded assertion)", re.I | re.S),
    "closure-guarantees-uptake": re.compile(r"𝒞\(Ψᴺ\).{0,100}(?:guarantees|ensures|proves).{0,80}(?:conversion|acceptance|uptake)", re.I | re.S),
    "psi-i-soul-access": re.compile(r"Ψᴵ.{0,100}(?:access to|reads|knows).{0,80}(?:soul|qalb)", re.I | re.S),
    "agent-controls-guidance": re.compile(r"(?:agent|runtime).{0,80}(?:controls|guarantees).{0,80}guidance", re.I | re.S),
}


def read(root: Path, rel: str, errors: list[str]) -> str:
    path = root / rel
    if not path.exists():
        errors.append(f"{rel}: missing")
        return ""
    return path.read_text(encoding="utf-8")


def require_tokens(root: Path, rel: str, tokens: list[str], errors: list[str]) -> None:
    text = read(root, rel, errors)
    lower = text.lower()
    for token in tokens:
        if token not in text and token.lower() not in lower:
            errors.append(f"{rel}: missing field-operator token {token!r}")


def check_forbidden_claims(root: Path, rels: list[str], errors: list[str]) -> None:
    for rel in rels:
        text = read(root, rel, errors)
        for label, pattern in FORBIDDEN_PATTERNS.items():
            for match in pattern.finditer(text):
                window = text[max(0, match.start() - 240) : match.end() + 160].lower()
                if (
                    "not " in window
                    or "not\n" in window
                    or "does not " in window
                    or "cannot " in window
                    or "must not " in window
                ):
                    continue
                errors.append(f"{rel}: forbidden field-operator claim {label}: {match.group(0)!r}")


def check_fixture(root: Path, errors: list[str]) -> None:
    path = root / FIXTURE
    if not path.exists():
        errors.append(f"{FIXTURE.as_posix()}: missing field-operator fixture")
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    flattened = json.dumps(payload, ensure_ascii=False).lower()
    for token in (
        "field_gradient_loop_closure_coupling",
        "route-gradient",
        "loopbreak",
        "target loop",
        "grounding source",
        "delta effect",
        "post-break",
        "closure-field condition",
        "psii",
        "t_lang",
        "does not guarantee acceptance",
        "does not assert access to the soul",
    ):
        if token.lower() not in flattened:
            errors.append(f"{FIXTURE.as_posix()}: missing fixture token {token!r}")
    forbidden_claims = payload.get("forbidden_claims")
    if not isinstance(forbidden_claims, list) or len(forbidden_claims) < 5:
        errors.append(f"{FIXTURE.as_posix()}: must list field-operator negative controls")


def check_ttp_inheritance(root: Path, errors: list[str]) -> None:
    text = read(root, "tools/check_ttp_operator_contracts.py", errors)
    for token in (
        "INHERITED_FIELD_OPERATOR_REQUIREMENTS",
        "route-gradient",
        "LoopBreak(∇×T)",
        "𝒞(Ψᴺ)",
        "Ψᴵ",
        "T_lang",
    ):
        if token not in text:
            errors.append(f"tools/check_ttp_operator_contracts.py: missing inherited guard token {token!r}")


def main() -> int:
    root = repo_root()
    errors: list[str] = []

    for rel, tokens in OWNER_TOKEN_REQUIREMENTS.items():
        require_tokens(root, rel, tokens, errors)
    for rel, tokens in DOCS_INDEX_SOURCE_TOKENS.items():
        require_tokens(root, rel, tokens, errors)
    for rel, tokens in GENERATED_DOC_TOKENS.items():
        require_tokens(root, rel, tokens, errors)
    check_fixture(root, errors)
    check_ttp_inheritance(root, errors)
    check_forbidden_claims(
        root,
        sorted(set(OWNER_TOKEN_REQUIREMENTS) | set(DOCS_INDEX_SOURCE_TOKENS) | set(GENERATED_DOC_TOKENS)),
        errors,
    )

    if not errors:
        print("field-operator architecture check passed")
        print("- plain ∇ route-gradient owner/docs/fixture coverage: pass")
        print("- LoopBreak(∇×T) owner/docs/fixture coverage: pass")
        print("- 𝒞(Ψᴺ) closure-field condition coverage: pass")
        print("- Ψᴺ / Ψᴵ coupling boundary coverage: pass")

    return fail_with_errors("field-operator architecture", errors)


if __name__ == "__main__":
    raise SystemExit(main())
