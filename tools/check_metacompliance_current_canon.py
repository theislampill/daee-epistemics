#!/usr/bin/env python3
"""Guard current metacompliance canon against control-plane and docs drift."""

from __future__ import annotations

import sys
from pathlib import Path
import re

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


ROOT_MAX_CHARS = 80_000

ROOT_REQUIRED = [
    "## EXECUTION SPINE",
    "Input -> IR(N,m,",
    "Top-salient invariants",
    "Default = noetic-field banner + Layer A(compact DSL/IR header) + Layer B(bounded governed response) + R",
    "Tactics / Techniques / Procedures Owner Map",
    "## I. Thesis / Epistemological Standpoint Pointers",
    "## V. Burden-Governed Render Protocol",
    "Default forbids raw Diagnostic IR, full Case State",
    "Pattern(deformation/concealment/unsoundness) > denomination/source-label",
    "Named frameworks/schools/authors/genealogies are not public-render material",
    "all gate checks must pass before any content",
    "Owner-loadform map for common hard-output owners",
    "TTP label recognition is not owner-body execution",
    "matched module label is not owner floor loaded",
    "OWNER-BODY-NOT-LOADED",
]

ROOT_FORBIDDEN_REEXPANSION = [
    "### Tactics Subfolder",
    "### Techniques Subfolder",
    "### Procedures Subfolder",
    "## IV. Diagnostic Protocol - Run Before Every Response",
    "### IV.A - Input Type",
    "### IV.B - Epistemological Position",
    "### IV.C - Modes of Concealment (Summary)",
    "### IV.D - Seven Deformations",
    "### V.A - Two-Layer Output Contract",
    "Default-Mode Worked Example\n\n**Input",
]

GENERATED_REQUIRED = [
    "Default mode suppresses raw visible IR",
    "Default Output Surface Invariant",
    "compact DSL/IR header",
    "Layer B",
    "bounded governed response",
    "Hidden Premises",
    "Restorative Response",
    "Core Formulation",
    "Bounded Response / operative submoves",
    "Closing Formulation",
    "TTP/operator trace",
    "burden-complete",
    "State/noetic re-read",
    "scholar/source/citation parade",
    "Pattern(deformation/concealment/unsoundness) > denomination/source-label",
    "Named frameworks/schools/authors/genealogies are not public-render material",
    "Default output must not print:",
    "raw Diagnostic IR",
    "full Case State",
    "matched_modules",
    "route ledger",
    "load ledger",
    "composition narration",
    "Owner-loadform map for common hard-output owners",
    "TTP label recognition is not owner-body execution",
    "matched module label is not owner floor loaded",
    "OWNER-BODY-NOT-LOADED",
]

OWNER_REQUIRED = {
    "atomics/skill/references/diagnostics/recursive-state-transitions.md": [
        "Source-Status & Noetic-Frame Non-Equivalence Discipline",
        "N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡ N_Wahhābī",
        "family label != operative N",
        "shared vocabulary != shared warrant",
        "source-status discipline and noetic-frame non-equivalence",
        "Operative warrant:",
        "specific non-premise clause",
        "Held-routes carry rule",
        "Released: <item>",
        "held-route semantic leakage",
        "Burden completeness rule",
        "not licensed until",
        "Method-source non-branding rule",
        "default output",
        "not public-render material",
        "Default citation allowance is restricted to Qurʾān",
    ],
    "atomics/skill/references/diagnostics/diagnostic-ir.md": [
        "IR(pattern_profile, claim_level, reason-category, concealment, deformation, DO-orient)",
        "matched TTP/operator",
        "public-render",
        "topic-specific argument bank",
    ],
    "atomics/skill/references/diagnostics/pattern-profiling.md": [
        "claims, criteria, authorities, and",
        "identity-stabilizers dock into a noetic structure",
        "sociological commentary",
    ],
    "atomics/skill/references/diagnostics/anti-patterns.md": [
        "Denomination-First / Source-Label Routing",
        "Pattern(deformation/concealment/unsoundness) > denomination/source-label",
        "not public-render material by default",
    ],
    "atomics/skill/references/rubrics/diagnostic-render-contract.md": [
        "source-status/noetic-frame:",
        "Layer B governed-response shape",
        "Restorative Response",
        "Core Formulation",
        "Closing Formulation",
        "TTP/operator invocation trace",
        "Burden-complete operator routing",
        "Default source/citation restriction",
        "Method-source branding",
        "how sound/innate reason has been deformed",
        "what criterion/source/warrant is returned to its proper place",
        "Operative warrant:",
        "specific non-premise clause",
        "Held-route semantic leakage",
        "Released: <item>",
    ],
    "atomics/skill/references/rubrics/output-release.md": [
        "Source-status & noetic-frame release check",
        "prompt-level self-check",
        "live chat response unless the output is captured",
        "Operative warrant:",
        "specific non-premise clause",
        "Held Material Is Actually Held, Then Reassessed",
        "Released: <item>",
        "held-route semantic",
        "released burden is burden-complete",
        "no headline-only answer",
        "TTP/operator trace",
        "Restorative Response identifies restored order",
    ],
    "atomics/skill/references/diagnostics/routing-precedence.md": [
        "pattern-first",
        "not abstract universalism",
        "neutral comparative system",
        "Named denomination/source identity is never sufficient to route content",
        "burden-complete",
        "no headline-only answer",
    ],
}

CURRENT_DOC_REQUIRED = {
    "docs/proof-class-taxonomy.md": [
        "Proof Class Taxonomy",
        "sidecar-backed-structural",
        "semantic-replay",
        "kernel-assumption",
        "public-readback",
        "owner-decision",
        "Assignment rule",
    ],
    "README.md": [
        "compact DSL/IR",
        "State/noetic re-read",
        "Hidden Premises",
        "TTP/operator trace",
        "Restorative Response",
        "Closing Formulation",
        "not abstract universalism",
        "Pattern(deformation/concealment/unsoundness) > denomination/source-label",
        "/daee-epistemics:audit",
        "deprecated as a public render mode",
        "docs/non-claims.md",
        "Chat outputs are unchecked unless captured and validated",
    ],
    "AGENTS.md": [
        "compact DSL/IR",
        "State/noetic re-read",
        "Hidden Premises",
        "TTP/operator trace",
        "/daee-epistemics:audit",
        "deprecated as public output",
    ],
    "TODO.md": [
        "compact DSL/IR",
        "bounded governed Layer B",
        "Restorative Response",
        "Core Formulation",
        "Closing Formulation",
        "Hidden Premises",
        "TTP/operator trace",
        "state/noetic re-read",
        "`:audit` as public output",
    ],
    "CHANGELOG.md": [
        "Current runtime canon supersedes older terminology",
        "compact DSL/IR",
        "state/noetic",
        "Hidden Premises",
        "TTP/operator",
        "`:audit` is deprecated as public output",
        "historical release states, not current guidance",
    ],
    "docs/non-claims.md": [
        "No guaranteed uptake",
        "No interior-state certification",
        "No arbitrary-input correctness claim",
        "No universal semantic grader",
        "They make violations legible; they do not prove semantic impossibility",
    ],
    "docs/compiled-runtime-tools.md": [
        "default compact DSL/IR visibility",
        "Hidden Premises",
        "TTP/operator trace",
        "deprecated internal/development `/daee-epistemics:audit` compatibility",
    ],
    "docs/recursive-traversal-governance.md": [
        "compact DSL/IR header",
        "Hidden Premises",
        "TTP/operator trace",
        "/daee-epistemics:audit = deprecated internal/development compatibility surface",
        "not as the public place where governance becomes real",
    ],
    "docs/algebraic-notation-and-noetic-formalism.md": [
        "theory/specification surface",
        "Current compact runtime spine",
        "IR(N,m,tau,sigma)",
        "IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)",
        "not mandatory schema fields",
        "Delta-nB",
        "n-plus-1B",
        "`κ` as a generic TODO list",
        "Shannon",
        "Symbol theater",
    ],
    "docs/register-formalism-implementation-ledger.md": [
        "schema-light register bridge Implementation Ledger",
        "`IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` derived bridge",
        "IMPLEMENTED",
        "DEFERRED WITH BLOCKER",
    ],
}

CURRENT_DOCS_FOR_STALE_SCAN = [
    "README.md",
    "AGENTS.md",
    "TODO.md",
    "docs/compiled-runtime-tools.md",
    "docs/recursive-traversal-governance.md",
]

STALE_CURRENT_GUIDANCE = [
    "clean default `/daee-epistemics` mode",
    "clean default response with internal recursive governance",
    "fuller `/daee-epistemics:audit` mode",
    "fuller procedural audit",
    "eligible live door",
    "eligible-live-door",
    "live door:",
    "one door at a time",
    "state refresh",
    "recursive governance remains internal unless",
    "default is prose-only",
]

VERSION_HEADING_RE = re.compile(r"^## \[(v\d+\.\d+\.\d+\.\d+)\]", re.MULTILINE)
RELEASE_ARTIFACT_RE = re.compile(r"^## (v\d+\.\d+\.\d+\.\d+) Release Package", re.MULTILINE)


def read(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing file: {path.as_posix()}")
        return ""
    return path.read_text(encoding="utf-8")


def has(text: str, token: str) -> bool:
    return token.lower() in text.lower()


def require_tokens(rel_path: str, text: str, tokens: list[str], errors: list[str]) -> None:
    for token in tokens:
        if not has(text, token):
            errors.append(f"{rel_path} missing current-canon token: {token!r}")


def check_root_control_plane(root: Path, errors: list[str]) -> None:
    rel_path = "atomics/skill/SKILL.md"
    text = read(root / rel_path, errors)
    require_tokens(rel_path, text, ROOT_REQUIRED, errors)

    if len(text) > ROOT_MAX_CHARS:
        errors.append(
            f"{rel_path} exceeds control-plane drift budget: "
            f"{len(text)} chars > {ROOT_MAX_CHARS}"
        )

    for token in ROOT_FORBIDDEN_REEXPANSION:
        if has(text, token):
            errors.append(f"{rel_path} appears to have re-expanded: {token!r}")


def check_generated_default_surface(root: Path, errors: list[str]) -> None:
    rel_path = "skill/SKILL.md"
    text = read(out_dir(root) / "SKILL.md", errors)
    require_tokens(rel_path, text, GENERATED_REQUIRED, errors)

    invariant_idx = text.find("# Default Output Surface Invariant")
    if invariant_idx == -1:
        errors.append("skill/SKILL.md missing Default Output Surface Invariant")
        return

    section = text[invariant_idx:]
    ordered = [
        "Layer A",
        "Layer B",
        "State/noetic re-read",
        "Restorative Response",
        "Closing Formulation",
    ]
    cursor = -1
    for token in ordered:
        idx = section.find(token)
        if idx == -1:
            errors.append(f"skill/SKILL.md default invariant missing ordered token: {token!r}")
        elif idx < cursor:
            errors.append(
                "skill/SKILL.md default invariant order drifted before "
                f"{token!r}"
            )
        else:
            cursor = idx


def check_owner_anchors(root: Path, errors: list[str]) -> None:
    for rel_path, tokens in OWNER_REQUIRED.items():
        text = read(root / rel_path, errors)
        require_tokens(rel_path, text, tokens, errors)


def check_current_docs(root: Path, errors: list[str]) -> None:
    for rel_path, tokens in CURRENT_DOC_REQUIRED.items():
        text = read(root / rel_path, errors)
        require_tokens(rel_path, text, tokens, errors)

    for rel_path in CURRENT_DOCS_FOR_STALE_SCAN:
        text = read(root / rel_path, errors)
        for token in STALE_CURRENT_GUIDANCE:
            if has(text, token):
                errors.append(f"{rel_path} contains stale current guidance: {token!r}")


def version_key(version: str) -> tuple[int, int, int, int]:
    return tuple(int(part) for part in version.removeprefix("v").split("."))  # type: ignore[return-value]


def check_changelog_release_currency(root: Path, errors: list[str]) -> None:
    changelog = read(root / "CHANGELOG.md", errors)
    release_artifacts = read(root / "docs/release-artifacts.md", errors)
    if not changelog or not release_artifacts:
        return

    changelog_versions = set(VERSION_HEADING_RE.findall(changelog))
    release_versions = set(RELEASE_ARTIFACT_RE.findall(release_artifacts))
    if not release_versions:
        errors.append("docs/release-artifacts.md has no release package headings")
        return

    newest_release = max(release_versions, key=version_key)
    missing = sorted(release_versions - changelog_versions, key=version_key)
    if missing:
        errors.append(
            "CHANGELOG.md missing release heading(s) present in docs/release-artifacts.md: "
            + ", ".join(missing)
        )
    if newest_release not in changelog_versions:
        errors.append(
            f"CHANGELOG.md newest release heading is older than current release artifact: {newest_release}"
        )


def main() -> int:
    root = repo_root()
    errors: list[str] = []

    check_root_control_plane(root, errors)
    check_generated_default_surface(root, errors)
    check_owner_anchors(root, errors)
    check_current_docs(root, errors)
    check_changelog_release_currency(root, errors)

    if not errors:
        skill_text = read(root / "atomics/skill/SKILL.md", errors)
        generated_text = read(out_dir(root) / "SKILL.md", errors)
        print("metacompliance current canon summary")
        print("-" * 60)
        print(f"root SKILL.md chars: {len(skill_text)}")
        print(f"generated SKILL.md chars: {len(generated_text)}")
        print(f"owner files checked: {len(OWNER_REQUIRED)}")
        print(f"current docs checked: {len(CURRENT_DOC_REQUIRED)}")
        print(f"stale guidance tokens checked: {len(STALE_CURRENT_GUIDANCE)}")
        print("-" * 60)

    return fail_with_errors("metacompliance current canon", errors)


if __name__ == "__main__":
    sys.exit(main())
