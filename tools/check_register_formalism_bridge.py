#!/usr/bin/env python3
"""Guard the schema-light register-formalism bridge against drift."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


REGISTER_FORMALISM_FIXTURE_DIR = Path(
    os.environ.get("REGISTER_FORMALISM_FIXTURE_DIR", "tests/register-formalism-bridge-fixtures")
)
ALGEBRAIC_SYMBOL_AUDIT_DOC = Path(
    os.environ.get(
        "REGISTER_FORMALISM_SYMBOL_AUDIT",
        "docs/audits/v0.4.1.0-algebraic-symbol-operativity-audit.md",
    )
)
NLA_OPERATIVITY_AUDIT_DOC = Path(
    os.environ.get(
        "REGISTER_FORMALISM_NLA_AUDIT",
        "docs/audits/v0.4.1.0-nla-operativity-audit.md",
    )
)
SKILL_COMPLIANCE_AUDIT_DOC = Path(
    os.environ.get(
        "REGISTER_FORMALISM_SKILL_COMPLIANCE_AUDIT",
        "docs/audits/v0.4.1.0-skill-compliance-audit.md",
    )
)

APPROVED_SYMBOL_CLASSIFICATIONS = {
    "OPERATIVE",
    "AUDIT_DIAGNOSTIC_ALLOWED",
    "DEFAULT_RUNTIME_FORBIDDEN",
    "DEFAULT_COMPACT_STATE_MARKER_ALLOWED",
    "DEFAULT_FORMALISM_EXPOSITION_FORBIDDEN",
    "DOCS_ONLY",
    "HISTORICAL_ONLY",
    "ORNAMENTAL_RISK",
    "NEEDS_PATCH",
}

ALLOWED_SYMBOL_OWNER_FILES = {
    "docs/algebraic-notation-and-noetic-formalism.md",
    "docs/register-formalism-implementation-ledger.md",
    "atomics/skill/SKILL.md",
    "atomics/skill/references/diagnostics/recursive-state-transitions.md",
    "atomics/skill/references/rubrics/diagnostic-render-contract.md",
    "atomics/skill/references/rubrics/output-release.md",
    "atomics/skill/references/diagnostics/diagnostic-ir.md",
    "atomics/skill/references/diagnostics/case-state-schema.md",
    "atomics/skill/references/diagnostics/framework-pipeline.yaml",
    "checker/tool owner",
    "historical archive only",
}

CONTROL_EFFECT_ALLOWLIST = {
    "changes IR/case-state formation",
    "changes candidate/held noetic-frame selection",
    "changes register activation",
    "changes owner/TTP eligibility",
    "changes held material",
    "changes hold/release posture",
    "changes burden selection",
    "changes dependency/collapse radius",
    "changes `Land(B)`",
    "changes `R(H,Delta)`",
    "changes STOP/HOLD/PARTIAL/RECURSE/COMPLETE",
    "changes terminal restoration boundary",
    "changes checker outcome",
    "changes package/render admissibility",
}

SYMBOL_OPERATIVITY_REQUIRED = [
    "𝓝",
    "N_space",
    "D₀",
    "D0",
    "Ψᴺ",
    "PsiN",
    "N∈𝓝",
    "selected N",
    "held N",
    "IR(N,m,τ,σ)",
    "IR(N,m,tau,sigma)",
    "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
    "IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)",
    "♥",
    "heart",
    "ξ",
    "xi",
    "Ω",
    "Omega",
    "μ",
    "mu",
    "κ",
    "kappa",
    "σ",
    "sigma",
    "H",
    "ⁿB",
    "nB",
    "ⁿBᵢ",
    "nBi",
    "OPᵢ",
    "OPi",
    "ⁿBᵢ[OPᵢ]",
    "target -> operation -> result",
    "Land(B)",
    "Land(ⁿB)",
    "Delta-nB",
    "ΔⁿB",
    "Delta-kappa",
    "Δκ",
    "R(H,Delta)",
    "R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)",
    "STOP",
    "HOLD",
    "PARTIAL",
    "RECURSE",
    "COMPLETE",
    "ⁿ⁺¹B",
    "n-plus-1B",
    "𝒞(Ψᴺ)",
    "C(PsiN)",
    "N_fiṭrī",
    "N_fitri",
    "ʿaql ṣarīḥ",
    "aql_sarih",
    "∇·",
    "∇×",
    "del-dot",
    "del dot",
    "del-cross",
    "del cross",
    "divergence",
    "curl",
    "nabla dot",
    "nabla cross",
    "antisymmetric Jacobian",
    "exterior derivative",
    "NLA",
    "Natural Language Autoencoder",
    "linearization",
    "activation verbalizer",
    "activation reconstructor",
    "reconstruction loss",
    "FVE",
    "residual stream",
    "signal",
    "encoding",
    "channel",
    "noise",
    "distortion",
    "compression",
    "capacity",
    "entropy",
    "Shannon",
    "symbol theater",
    "anti-symbol-theater",
]

FIXTURE_MATRIX_REQUIRED = {
    "local_transition",
    "register_activation",
    "held_frame",
    "closure_prevention",
    "divergence_curl",
    "anti_symbol_theater",
    "shannon_nla_boundary",
    "nla_reconstruction",
}

REGISTER_TTP_REQUIREMENTS = {
    "xi": ("warrant", "proof", "testimony", "authority", "owner/TTP eligibility"),
    "Omega": ("ontology", "predication", "dependence", "owner/TTP eligibility"),
    "mu": ("memetic carrier", "compression", "stabilizer", "burden selection"),
    "kappa": ("held burden", "dependency", "reread", "closure"),
    "heart": ("affective", "release posture", "softness", "closure posture"),
    "sigma": ("discourse", "pattern state", "routing"),
}

NLA_REQUIRED_PHRASES = (
    "Natural-language bottleneck for noetic-state reconstruction",
    "Natural Language Autoencoder",
    "activation verbalizer",
    "activation reconstructor",
    "reconstruction fidelity",
    "confabulation",
    "IR reconstruction pass",
    "R(H,Delta)",
    "anti-symbol-theater",
    "not generic linear algebra",
    "does not measure truth",
    "does not measure warrant",
)

NLA_MAPPING_COMPONENTS = (
    "activation h",
    "AV / activation verbalizer",
    "explanation z",
    "AR / activation reconstructor",
    "reconstruction loss",
    "confabulation",
    "causal intervention / steering",
)

NLA_CONTROL_EFFECTS = (
    "Layer A / Diagnostic IR shape",
    "IR reconstruction pass",
    "selected/held noetic-frame recovery",
    "register recovery",
    "owner/TTP eligibility",
    "burden selection",
    "held material",
    "κ/H dependency state",
    "R(H,Delta)",
    "PARTIAL/RECURSE/COMPLETE",
    "checker outcome",
)

NLA_FAILURE_MODES = (
    "Confabulation",
    "Excessive expressivity",
    "Lack of mechanistic grounding",
    "Degenerate bottleneck",
    "Reconstruction failure",
)

SKILL_COMPLIANCE_LAYER_TERMS = {
    "Algebraic/register formalism": (
        "N_space",
        "selected/held",
        "Delta-nB",
        "Delta-kappa",
        "R(H,Delta)",
        "owner/TTP eligibility",
    ),
    "Divergence/curl diagnostics": (
        "field-level diagnostics",
        "Delta-produced",
        "not Delta replacements",
        "compact governance state markers",
        "long formalism exposition",
    ),
    "NLA reconstruction fidelity": (
        "Natural Language Autoencoder",
        "AV analogue",
        "AR analogue",
        "Layer A / Diagnostic IR / noetic-field banner",
        "reconstruction/reread",
        "not generic algebra",
        "not Shannon theory",
        "not truth/warrant metric",
    ),
    "Shannon compression boundary": (
        "signal",
        "encoding",
        "channel",
        "noise",
        "distortion",
        "redundancy",
        "compression",
        "capacity",
        "not truth",
        "not meaning",
        "not warrant",
        "not revelation",
        "not fitrah",
        "not sound reason",
        "not NLA",
    ),
}

CROSS_LAYER_FORBIDDEN_REDUCTIONS = (
    "nla is generic algebra",
    "nla is generic linear algebra",
    "nla = linear algebra",
    "nla is shannon theory",
    "nla = shannon theory",
    "nla measures truth",
    "nla measures warrant",
    "shannon measures truth",
    "shannon measures warrant",
    "shannon measures meaning",
    "entropy measures truth",
    "entropy measures warrant",
    "entropy measures meaning",
)

DIVERGENCE_CURL_OPERATOR_FORMS = {
    "unicode_divergence": "∇·",
    "unicode_curl": "∇×",
    "divergence_aliases": ("del-dot", "del dot", "divergence", "nabla dot"),
    "curl_aliases": ("del-cross", "del cross", "curl", "nabla cross"),
}

DIVERGENCE_CURL_CLASSIFICATIONS = {
    "AUDIT_DIAGNOSTIC_ALLOWED",
    "DEFAULT_COMPACT_STATE_MARKER_ALLOWED",
    "DEFAULT_FORMALISM_EXPOSITION_FORBIDDEN",
    "HISTORICAL_ONLY",
    "ORNAMENTAL_RISK",
    "NEEDS_PATCH",
}

DIVERGENCE_CURL_CONTROL_TERMS = (
    "R(H,Delta)",
    "PARTIAL",
    "RECURSE",
    "COMPLETE",
    "dependency-radius",
    "target-explicit",
    "field target",
    "relational field",
    "scalar collapse",
    "loop",
    "circulation",
    "held-burden",
    "checker",
)

DEFAULT_FIELD_DIAGNOSTIC_MARKERS = (
    "∇·",
    "∇×",
)

DEFAULT_FORBIDDEN_FORMALISM_EXPOSITION = (
    "del-dot",
    "del-cross",
    "nabla dot",
    "nabla cross",
    "antisymmetric jacobian",
    "exterior derivative",
)

DEFAULT_FORMAL_MARKER_CONTROL_TERMS = (
    "state",
    "κ",
    "kappa",
    "r(h,δ)",
    "r(h,delta)",
    "δκ",
    "delta-kappa",
    "dependency",
    "pressure",
    "loop",
    "partial",
    "recurse",
    "complete",
    "closure",
    "held",
    "live",
    "checker",
    "control",
    "land(b)",
    "burden",
    "governance",
)

DEFAULT_RUNTIME_CLAIM_FORBIDDEN = (
    "Shannon entropy measures truth",
    "meaning entropy",
    "warrant entropy",
    "lower entropy proves",
    "entropy proves",
    "entropy measures warrant",
    "entropy measures meaning",
    "divergence measures truth",
    "divergence measures warrant",
    "curl measures truth",
    "curl measures warrant",
    "nabla measures truth",
    "nabla measures warrant",
)

DEFAULT_RUNTIME_NLA_FORBIDDEN = (
    "NLA",
    "Natural Language Autoencoder",
    "activation verbalizer",
    "activation reconstructor",
    "reconstruction loss",
    "FVE",
    "residual stream",
)

DEFAULT_RUNTIME_CONTEXTUAL_FORMALISM = (
    "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
    "IR(N,m,tau,sigma,heart,xi,Omega,mu,kappa)",
)

DEFAULT_RUNTIME_CONTEXT_REQUIRED = (
    "do not print",
    "not default",
    "audit/formalism",
    "forbidden default",
    "forbidden default exposition",
    "forbidden example",
    "formal/spec notation",
    "expanded formalism render boundary",
    "anti-symbol-theater",
    "long formalism exposition",
    "target-explicit",
    "explicit target field",
    "explicit field target",
    "operator distinction",
    "not restricted",
)

DIVERGENCE_CURL_AUDIT_DOCS = (
    "docs/audits/v0.4.1.0-formalism-operativity-audit.md",
    "docs/audits/v0.4.1.0-skill-compliance-audit.md",
    "docs/audits/v0.4.1.0-ci-release-operativity-audit.md",
)

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
        "The schema-light register bridge is implemented in this repo",
        "tests/register-formalism-bridge-fixtures/",
        "a derived/conditional bridge",
        "𝓝 ⊢ D₀ ⇝ Ψᴺ",
        "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
        "R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)",
        "𝒞(Ψᴺ)",
        "N_fiṭrī ∧ ʿaql ṣarīḥ",
        "Shannon entropy measures truth",
        "Symbol theater",
        "not mandatory schema fields",
        "Delta / Divergence / Curl Operator Distinction",
        "Divergence / Curl Diagnostic Boundary",
        "`Delta-nB` is the burden-event delta",
        "`Delta-kappa` is the dependency-radius delta",
        "`∇·`",
        "`∇×`",
        "del-dot",
        "del-cross",
        "nabla dot",
        "nabla cross",
        "antisymmetric part of the",
        "Jacobian / exterior",
        "Neither `∇·` nor `∇×` replaces",
        "compact markers",
        "long formalism exposition",
        "target-explicit",
        "restricted to `κ`",
        "scalar collapse is an execution failure",
        "∇·B",
        "∇×B",
        "∇·♥",
        "∇×ξ",
        "The diagnostic is operative only when it changes owner/TTP eligibility",
        "Shannon language remains bounded",
    ],
    "docs/register-formalism-implementation-ledger.md": [
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
        "PROVEN IMPLEMENTED",
        "DEFERRED WITH BLOCKER",
        "tests/register-formalism-bridge-fixtures/",
        "breaks current Diagnostic IR schema",
    ],
    "atomics/skill/references/diagnostics/nomenclature-normalization.md": [
        "schema-light register bridge",
        "derived/conditional",
        "IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)",
        "Current hard schema remains",
        "kappa",
    ],
    "atomics/skill/references/diagnostics/diagnostic-ir.md": [
        "register-formalism bridge status",
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
        "register-formalism signal-state bridge",
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
        "schema-light register bridge maps D0 -> PsiN -> IR without hard schema fields",
        "register_formalism_bridge",
        "ⁿBᵢ[OP] : target -> operation -> result -> ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ",
        "Delta-kappa dependency-radius changes are consumed before closure",
    ],
    "README.md": [
        "schema-light register bridge",
        "docs/register-formalism-implementation-ledger.md",
        "tests/register-formalism-bridge-fixtures/",
        "not a mandatory register-field schema",
        "not a v0.4.0.0 release/package readiness",
        "recorded installed-skill hard-smoke audit",
    ],
    "TODO.md": [
        "Register-Formalism Live Smoke / Hard Schema / Release Migration Decision",
        "tools/check_register_formalism_bridge.py",
        "Required verification already present for bridge behavior",
        "v0.4.0.0 release consideration",
    ],
    "AGENTS.md": [
        "python tools/check_register_formalism_bridge.py",
        "schema-light register bridge semantics are",
        "tests/register-formalism-bridge-fixtures/",
        "Bridge live-smoke proof",
        "do not claim a release-line migration from the index page",
    ],
}

GENERATED_REQUIRED = {
    "skill/references/runtime-dispatch-gate.md": [
        "register-formalism bridge status",
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
    "register-formalism-implementation-ledger.md",
    "Canonical Architecture Runtime",
    "compact runtime spine",
    "schema-light register bridge",
    "baseline register formalism",
    "hard schema",
    "diagnostic navigation aid",
    "source-governance",
    "fixture-backed",
    "Shannon entropy measures truth",
]

INDEX_FORBIDDEN = [
    "register-formalism bridge " + "\u2014 target repo " + "state",
    "register-formalism bridge - target repo " + "state",
    "live <code>♥/ξ/Ω/μ/κ</code> register controls",
    "register-formalism bridge now implements",
    "register-formalism bridge — implemented derived/conditional bridge",
    "Bridge implementation merge",
    "not yet first-class registers",
    "Defer as runtime",
    "register-formalism bridge as current runtime " + "architecture",
]

BRIDGE_REQUIRED_COVERAGE = {
    "N_space",
    "D0",
    "PsiN",
    "selected_N",
    "expanded_IR",
    "heart",
    "xi",
    "Omega",
    "mu",
    "kappa",
    "Delta-kappa",
    "burden_notation",
    "operator_signature",
    "expanded_R",
    "C(PsiN)",
    "terminal_restoration",
    "same_burden_algebra",
    "shannon_boundary",
    "anti_symbol_theater",
    "divergence_curl_operators",
    "nla_reconstruction",
}

REGISTER_EFFECT_REQUIREMENTS = {
    "heart": {"hold_release", "owner_choice"},
    "xi": {"owner_choice", "burden_selection"},
    "Omega": {"owner_choice", "burden_selection"},
    "mu": {"hold_release", "burden_selection"},
    "kappa": {"reread"},
    "Delta-kappa": {"reread"},
}

BEHAVIOR_EFFECTS_REQUIRED = {
    "owner_choice",
    "hold_release",
    "burden_selection",
    "reread",
    "restoration",
    "partial_behavior",
}

POST_RENDER_DECISIONS = {"STOP", "HOLD", "RECURSE", "PARTIAL"}
NONEISH = {"", "none", "n/a", "null", "no"}


def read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def load_json(path: Path, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.as_posix()}: JSON parse error: {exc}")
        return None


def string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def is_noneish(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in NONEISH or value.strip().lower().startswith("none ")
    if isinstance(value, list):
        return len(value) == 0 or all(is_noneish(item) for item in value)
    return False


def nested_dict_keys(node: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(key, str):
                keys.add(key)
            keys.update(nested_dict_keys(value))
    elif isinstance(node, list):
        for item in node:
            keys.update(nested_dict_keys(item))
    return keys


def audit_doc_path(root: Path) -> Path:
    if ALGEBRAIC_SYMBOL_AUDIT_DOC.is_absolute():
        return ALGEBRAIC_SYMBOL_AUDIT_DOC
    return root / ALGEBRAIC_SYMBOL_AUDIT_DOC


def nla_audit_doc_path(root: Path) -> Path:
    if NLA_OPERATIVITY_AUDIT_DOC.is_absolute():
        return NLA_OPERATIVITY_AUDIT_DOC
    return root / NLA_OPERATIVITY_AUDIT_DOC


def skill_compliance_audit_doc_path(root: Path) -> Path:
    if SKILL_COMPLIANCE_AUDIT_DOC.is_absolute():
        return SKILL_COMPLIANCE_AUDIT_DOC
    return root / SKILL_COMPLIANCE_AUDIT_DOC


def clean_table_cell(cell: str) -> str:
    return cell.strip().replace("<br>", " ").replace("<br/>", " ")


def split_table_line(line: str) -> list[str]:
    return [clean_table_cell(cell) for cell in line.strip().strip("|").split("|")]


def split_classifications(cell: str) -> set[str]:
    cleaned = cell.replace("`", "")
    return {part.strip() for part in re.split(r"\s*;\s*", cleaned) if part.strip()}


def parse_symbol_classification_table(text: str) -> dict[str, dict[str, str]]:
    lines = text.splitlines()
    in_table = False
    headers: list[str] = []
    rows: dict[str, dict[str, str]] = {}

    for line in lines:
        if re.match(r"^##\s+Symbol Classification Table\s*$", line.strip(), re.I):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.strip().startswith("|"):
            continue
        cells = split_table_line(line)
        if not headers:
            headers = cells
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells):
            continue
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        symbol = row.get("Symbol / alias", "").strip("`").strip()
        if symbol:
            rows[symbol] = row
    return rows


def parse_table_after_heading(text: str, heading: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    in_table = False
    headers: list[str] = []
    rows: list[dict[str, str]] = []

    heading_pattern = rf"^##\s+{re.escape(heading)}\s*$"
    for line in lines:
        if re.match(heading_pattern, line.strip(), re.I):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.strip().startswith("|"):
            continue
        cells = split_table_line(line)
        if not headers:
            headers = cells
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells):
            continue
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def cell_has_allowed_control_effect(cell: str) -> bool:
    lower = cell.lower()
    return any(effect.lower() in lower for effect in CONTROL_EFFECT_ALLOWLIST)


def check_nla_operativity_audit(root: Path, errors: list[str]) -> None:
    path = nla_audit_doc_path(root)
    display_path = path if path.is_absolute() else Path(NLA_OPERATIVITY_AUDIT_DOC)
    if not path.exists():
        errors.append(f"{display_path.as_posix()}: missing NLA operativity audit")
        return

    text = path.read_text(encoding="utf-8")
    lower = text.lower()
    required_headings = (
        "## Required NLA Definition",
        "## Natural Language Autoencoder Mapping",
        "## Operativity Standard",
        "## NLA Failure Modes in daee-epistemics",
        "## Relation To Delta And Divergence/Curl",
        "## Runtime Boundary",
        "## Checker And Fixture Proof",
    )
    for heading in required_headings:
        if heading.lower() not in lower:
            errors.append(f"{display_path.as_posix()}: missing heading {heading}")

    for phrase in NLA_REQUIRED_PHRASES:
        if phrase.lower() not in lower:
            errors.append(f"{display_path.as_posix()}: missing NLA required phrase {phrase!r}")

    mapping_rows = parse_table_after_heading(text, "Natural Language Autoencoder Mapping")
    components = {row.get("NLA paper component", "").strip("`") for row in mapping_rows}
    missing_components = [component for component in NLA_MAPPING_COMPONENTS if component not in components]
    if missing_components:
        errors.append(f"{display_path.as_posix()}: NLA mapping table missing components: {missing_components}")
    if mapping_rows and "control effect" not in " ".join(mapping_rows[0].keys()).lower():
        errors.append(f"{display_path.as_posix()}: NLA mapping table missing Control effect column")

    for effect in NLA_CONTROL_EFFECTS:
        if effect.lower() not in lower:
            errors.append(f"{display_path.as_posix()}: missing NLA control effect {effect!r}")
    for failure_mode in NLA_FAILURE_MODES:
        if failure_mode.lower() not in lower:
            errors.append(f"{display_path.as_posix()}: missing NLA failure mode {failure_mode!r}")

    forbidden_reductions = (
        "nla = linear algebra",
        "nla means nonlinear architecture",
        "nla measures truth",
        "nla measures warrant",
        "fve proves truth",
        "residual stream proves warrant",
    )
    for phrase in forbidden_reductions:
        if phrase in lower:
            errors.append(f"{display_path.as_posix()}: contains forbidden NLA reduction {phrase!r}")


def check_cross_layer_consistency(root: Path, errors: list[str]) -> None:
    algebraic_path = audit_doc_path(root)
    nla_path = nla_audit_doc_path(root)
    skill_path = skill_compliance_audit_doc_path(root)

    for path, label in (
        (algebraic_path, ALGEBRAIC_SYMBOL_AUDIT_DOC),
        (nla_path, NLA_OPERATIVITY_AUDIT_DOC),
        (skill_path, SKILL_COMPLIANCE_AUDIT_DOC),
    ):
        display_path = path if path.is_absolute() else Path(label)
        if not path.exists():
            errors.append(f"{display_path.as_posix()}: missing cross-layer audit input")
            return

    algebraic_text = algebraic_path.read_text(encoding="utf-8")
    nla_text = nla_path.read_text(encoding="utf-8")
    skill_text = skill_path.read_text(encoding="utf-8")
    algebraic_lower = algebraic_text.lower()
    nla_lower = nla_text.lower()
    skill_lower = skill_text.lower()

    algebraic_required = (
        "nla is not an algebraic-symbol family",
        "boundary-vocabulary controls",
        "not algebraic/register symbol rows",
        "separate natural language autoencoder",
        "do not conflate nla",
    )
    for phrase in algebraic_required:
        if phrase not in algebraic_lower:
            errors.append(
                f"{ALGEBRAIC_SYMBOL_AUDIT_DOC.as_posix()}: missing algebraic/NLA separation phrase {phrase!r}"
            )

    nla_required = (
        "not as generic linear algebra",
        "shannon theory",
        "does not measure truth",
        "does not measure warrant",
        "do not conflate nla",
        "verbalization/reconstruction bottleneck",
    )
    for phrase in nla_required:
        if phrase not in nla_lower:
            errors.append(f"{NLA_OPERATIVITY_AUDIT_DOC.as_posix()}: missing NLA boundary phrase {phrase!r}")

    rows = parse_table_after_heading(skill_text, "Four-Layer Formalism Boundary")
    if not rows:
        errors.append(f"{SKILL_COMPLIANCE_AUDIT_DOC.as_posix()}: missing Four-Layer Formalism Boundary table")
    else:
        found_layers = {row.get("layer", "").strip("`") for row in rows}
        missing_layers = [layer for layer in SKILL_COMPLIANCE_LAYER_TERMS if layer not in found_layers]
        if missing_layers:
            errors.append(
                f"{SKILL_COMPLIANCE_AUDIT_DOC.as_posix()}: missing four-layer rows: {missing_layers}"
            )
        for layer, terms in SKILL_COMPLIANCE_LAYER_TERMS.items():
            layer_rows = [row for row in rows if row.get("layer", "").strip("`") == layer]
            haystack = " ".join(" ".join(row.values()) for row in layer_rows).lower()
            for term in terms:
                if term.lower() not in haystack:
                    errors.append(
                        f"{SKILL_COMPLIANCE_AUDIT_DOC.as_posix()}: {layer}: missing term {term!r}"
                    )

    for phrase in CROSS_LAYER_FORBIDDEN_REDUCTIONS:
        if phrase in nla_lower:
            errors.append(f"{NLA_OPERATIVITY_AUDIT_DOC.as_posix()}: contains forbidden reduction {phrase!r}")
        if phrase in skill_lower:
            errors.append(f"{SKILL_COMPLIANCE_AUDIT_DOC.as_posix()}: contains forbidden reduction {phrase!r}")


def check_algebraic_symbol_audit(root: Path, errors: list[str]) -> None:
    path = audit_doc_path(root)
    display_path = path if path.is_absolute() else Path(ALGEBRAIC_SYMBOL_AUDIT_DOC)
    if not path.exists():
        errors.append(f"{display_path.as_posix()}: missing algebraic symbol operativity audit")
        return

    text = path.read_text(encoding="utf-8")
    lower = text.lower()
    required_headings = (
        "## Search Scope",
        "## Approved Classifications",
        "## Symbol Classification Table",
        "## Default Runtime Absence Proof",
        "## Fixture Matrix",
        "## Register To TTP Relation Check",
        "## Negative-Control Expectations",
    )
    for heading in required_headings:
        if heading.lower() not in lower:
            errors.append(f"{display_path.as_posix()}: missing heading {heading}")

    rows = parse_symbol_classification_table(text)
    missing_rows = [symbol for symbol in SYMBOL_OPERATIVITY_REQUIRED if symbol not in rows]
    if missing_rows:
        errors.append(f"{display_path.as_posix()}: symbol classification table missing rows: {missing_rows}")

    for symbol, row in rows.items():
        classifications = split_classifications(row.get("Runtime classification", ""))
        if not classifications:
            errors.append(f"{display_path.as_posix()}: {symbol}: missing runtime classification")
            continue
        invalid = sorted(classifications - APPROVED_SYMBOL_CLASSIFICATIONS)
        if invalid:
            errors.append(f"{display_path.as_posix()}: {symbol}: invalid classification(s): {invalid}")

        owner = row.get("Owner file", "").strip("`").strip()
        if owner not in ALLOWED_SYMBOL_OWNER_FILES:
            errors.append(f"{display_path.as_posix()}: {symbol}: invalid owner file {owner!r}")
        elif owner not in {"checker/tool owner", "historical archive only"} and not (root / owner).exists():
            errors.append(f"{display_path.as_posix()}: {symbol}: owner file missing: {owner}")

        default_allowed = row.get("Default runtime allowed?", "").strip()
        audit_allowed = row.get("Audit/formalism allowed?", "").strip()
        if default_allowed not in {"Yes", "No", "Conditional"}:
            errors.append(f"{display_path.as_posix()}: {symbol}: default runtime allowed must be Yes/No/Conditional")
        if audit_allowed not in {"Yes", "No", "Conditional"}:
            errors.append(f"{display_path.as_posix()}: {symbol}: audit/formalism allowed must be Yes/No/Conditional")

        proof = row.get("Checker / fixture proof", "").strip()
        risk = row.get("Risk", "").strip()
        action = row.get("Action", "").strip()
        if not proof:
            errors.append(f"{display_path.as_posix()}: {symbol}: missing checker/fixture proof")
        if not risk:
            errors.append(f"{display_path.as_posix()}: {symbol}: missing risk")
        if not action:
            errors.append(f"{display_path.as_posix()}: {symbol}: missing action")

        if {"OPERATIVE", "AUDIT_DIAGNOSTIC_ALLOWED"} & classifications:
            control_cell = row.get("Control effect required", "")
            if not cell_has_allowed_control_effect(control_cell):
                errors.append(f"{display_path.as_posix()}: {symbol}: operative/audit row lacks allowed control effect")

    section_match = re.search(
        r"(?is)^##\s+Register To TTP Relation Check\s*(.*?)(?:^##\s+|\Z)",
        text,
        re.M,
    )
    relation_text = section_match.group(1) if section_match else ""
    for register, required_terms in REGISTER_TTP_REQUIREMENTS.items():
        if register.lower() not in relation_text.lower():
            errors.append(f"{display_path.as_posix()}: register/TTP section missing {register}")
            continue
        for term in required_terms:
            if term.lower() not in relation_text.lower():
                errors.append(f"{display_path.as_posix()}: register/TTP section missing {register} term {term!r}")
    if "ORNAMENTAL_RISK" not in relation_text:
        errors.append(f"{display_path.as_posix()}: register/TTP section must name ORNAMENTAL_RISK fallback")


def has_all_operator_forms(text: str) -> bool:
    lower = text.lower()
    if DIVERGENCE_CURL_OPERATOR_FORMS["unicode_divergence"] not in text:
        return False
    if DIVERGENCE_CURL_OPERATOR_FORMS["unicode_curl"] not in text:
        return False
    for alias in DIVERGENCE_CURL_OPERATOR_FORMS["divergence_aliases"]:
        if alias not in lower:
            return False
    for alias in DIVERGENCE_CURL_OPERATOR_FORMS["curl_aliases"]:
        if alias not in lower:
            return False
    return True


def has_control_effect(text: str) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in DIVERGENCE_CURL_CONTROL_TERMS)


def check_divergence_curl_audit_docs(root: Path, errors: list[str]) -> None:
    for rel in DIVERGENCE_CURL_AUDIT_DOCS:
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: missing divergence/curl audit doc")
            continue
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        if "## divergence / curl operator detection" not in lower:
            errors.append(f"{rel}: missing ## Divergence / Curl Operator Detection")
        if rel.endswith("formalism-operativity-audit.md"):
            if "## delta / divergence / curl operator distinction" not in lower:
                errors.append(f"{rel}: missing ## Delta / Divergence / Curl Operator Distinction")
        if not has_all_operator_forms(text):
            errors.append(f"{rel}: missing one or more divergence/curl operator spellings")
        for classification in DIVERGENCE_CURL_CLASSIFICATIONS:
            if classification not in text:
                errors.append(f"{rel}: missing classification {classification}")
        if "operative" in lower and not has_control_effect(text):
            errors.append(f"{rel}: claims divergence/curl operativity without a control effect")
        if "mere metaphor" in lower and "ORNAMENTAL_RISK" not in text:
            errors.append(f"{rel}: uses mere-metaphor wording without ORNAMENTAL_RISK classification")
        if (
            ("only 3d" in lower or "only three-dimensional" in lower)
            and "not only 3d" not in lower
            and "antisymmetric" not in lower
        ):
            errors.append(f"{rel}: dismisses curl because standard curl is 3D")
        if "replaces `delta" in lower or "replace `delta" in lower:
            if "neither" not in lower and "not" not in lower:
                errors.append(f"{rel}: may conflate delta and divergence/curl operators")


def check_default_runtime_operator_boundary(root: Path, errors: list[str]) -> None:
    runtime_root = out_dir(root)
    for rel in (
        "SKILL.md",
        "references/runtime-output-governance.md",
        "references/runtime-dispatch-gate.md",
    ):
        path = runtime_root / rel
        if not path.exists():
            errors.append(f"skill/{rel}: generated runtime file missing for operator boundary check")
            continue
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        lines = text.splitlines()
        for index, line in enumerate(lines):
            window = "\n".join(lines[max(0, index - 2) : min(len(lines), index + 3)])
            window_lower = window.lower()
            boundary_context = any(context in window_lower for context in DEFAULT_RUNTIME_CONTEXT_REQUIRED)
            for token in DEFAULT_FIELD_DIAGNOSTIC_MARKERS:
                if (
                    token in line
                    and not any(term in window_lower for term in DEFAULT_FORMAL_MARKER_CONTROL_TERMS)
                    and not boundary_context
                ):
                    errors.append(
                        f"skill/{rel}: compact field diagnostic marker {token!r} "
                        f"lacks control-bound context near line {index + 1}"
                    )
            line_lower = line.lower()
            for token in DEFAULT_FORBIDDEN_FORMALISM_EXPOSITION:
                if token in line_lower and not any(context in window_lower for context in DEFAULT_RUNTIME_CONTEXT_REQUIRED):
                    errors.append(
                        f"skill/{rel}: formalism exposition token {token!r} appears "
                        f"without explicit boundary/example context near line {index + 1}"
                    )
        for claim in DEFAULT_RUNTIME_CLAIM_FORBIDDEN:
            if claim.lower() in lower:
                errors.append(f"skill/{rel}: default runtime contains forbidden NLA/Shannon claim {claim!r}")
        for token in DEFAULT_RUNTIME_NLA_FORBIDDEN:
            haystack = text if token in {"NLA", "FVE"} else lower
            needle = token if token in {"NLA", "FVE"} else token.lower()
            if needle in haystack:
                errors.append(f"skill/{rel}: default runtime contains forbidden NLA jargon {token!r}")
        if "symbol theater" in lower and "control effect" not in lower:
            errors.append(f"skill/{rel}: symbol-theater language appears without control-effect boundary")
        for token in DEFAULT_RUNTIME_CONTEXTUAL_FORMALISM:
            if token in text and not any(context in lower for context in DEFAULT_RUNTIME_CONTEXT_REQUIRED):
                errors.append(
                    f"skill/{rel}: raw expanded formalism {token!r} appears without "
                    "audit/formalism or do-not-print boundary"
                )


def compiled_modules(root: Path) -> dict[str, dict[str, object]]:
    path = out_dir(root) / "compiled-module-map.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    modules = data.get("modules")
    return modules if isinstance(modules, dict) else {}


def validate_post_render_gate(
    fixture_id: str,
    gate: object,
    errors: list[str],
) -> str | None:
    if not isinstance(gate, dict):
        errors.append(f"{fixture_id}: ir_projection.post_render_gate must be an object")
        return None

    decision = gate.get("recursion_decision")
    if decision not in POST_RENDER_DECISIONS:
        errors.append(f"{fixture_id}: invalid recursion_decision {decision!r}")
        return None

    remaining = gate.get("remaining_live_distortions")
    newly = gate.get("newly_released_routes")
    held = gate.get("held_routes_rechecked")
    next_pass = gate.get("next_eligible_pass")

    if not isinstance(newly, list):
        errors.append(f"{fixture_id}: post_render_gate.newly_released_routes must be an array")
    if not isinstance(held, list):
        errors.append(f"{fixture_id}: post_render_gate.held_routes_rechecked must be an array")

    if decision == "STOP":
        if not is_noneish(remaining):
            errors.append(f"{fixture_id}: STOP requires no remaining_live_distortions")
        if not is_noneish(newly):
            errors.append(f"{fixture_id}: STOP requires no newly_released_routes")
        if not is_noneish(next_pass):
            errors.append(f"{fixture_id}: STOP requires next_eligible_pass none")
    elif decision == "HOLD":
        if not is_noneish(newly):
            errors.append(f"{fixture_id}: HOLD invalid while newly_released_routes is non-empty")
        if is_noneish(remaining) and is_noneish(held):
            errors.append(f"{fixture_id}: HOLD requires remaining or held material")
    elif decision == "RECURSE":
        if is_noneish(next_pass):
            errors.append(f"{fixture_id}: RECURSE requires next_eligible_pass")
        if is_noneish(remaining) and is_noneish(newly):
            errors.append(f"{fixture_id}: RECURSE requires remaining_live_distortions or newly_released_routes")
    elif decision == "PARTIAL":
        if is_noneish(next_pass) and is_noneish(remaining):
            errors.append(f"{fixture_id}: PARTIAL requires remaining_live_distortions or next_eligible_pass")

    return decision


def validate_bridge_fixture(
    root: Path,
    path: Path,
    modules: dict[str, dict[str, object]],
    errors: list[str],
) -> tuple[set[str], set[str], str | None]:
    payload = load_json(path, errors)
    if not isinstance(payload, dict):
        errors.append(f"{path.as_posix()}: fixture must be a JSON object")
        return set(), set(), None

    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.as_posix()
    fixture_id = payload.get("id")
    if not isinstance(fixture_id, str) or not fixture_id:
        errors.append(f"{rel}: missing fixture id")
        fixture_id = rel

    kind = payload.get("kind")
    if kind not in {"positive", "negative"}:
        errors.append(f"{fixture_id}: kind must be positive or negative")

    covers = set(string_list(payload.get("covers")))
    if not covers:
        errors.append(f"{fixture_id}: covers must list register-formalism terms")

    matrix_cases = set(string_list(payload.get("matrix_cases")))
    invalid_matrix_cases = sorted(matrix_cases - FIXTURE_MATRIX_REQUIRED)
    if invalid_matrix_cases:
        errors.append(f"{fixture_id}: unknown fixture matrix case(s): {invalid_matrix_cases}")
    flattened_payload = json.dumps(payload, ensure_ascii=False).lower()
    if "local_transition" in matrix_cases:
        if "delta-nb" not in flattened_payload or "delta-kappa" not in flattened_payload:
            errors.append(f"{fixture_id}: local_transition matrix case must name Delta-nB and Delta-kappa")
        if not (
            "delta-nb is not delta-kappa" in flattened_payload
            or "not the same thing" in flattened_payload
            or "distinguish" in flattened_payload
        ):
            errors.append(f"{fixture_id}: local_transition matrix case must preserve Delta-nB/Delta-kappa distinction")
    if "register_activation" in matrix_cases and not {"xi", "Omega", "mu", "kappa"}.issubset(covers):
        errors.append(f"{fixture_id}: register_activation matrix case must cover xi/Omega/mu/kappa")
    if "held_frame" in matrix_cases and "selected_N" not in covers:
        errors.append(f"{fixture_id}: held_frame matrix case must cover selected_N")
    if "shannon_nla_boundary" in matrix_cases and "shannon_boundary" not in covers:
        errors.append(f"{fixture_id}: shannon_nla_boundary matrix case must cover shannon_boundary")
    if "nla_reconstruction" in matrix_cases and "nla_reconstruction" not in covers:
        errors.append(f"{fixture_id}: nla_reconstruction matrix case must cover nla_reconstruction")

    bridge_terms = payload.get("bridge_terms")
    if not isinstance(bridge_terms, dict) or not bridge_terms:
        errors.append(f"{fixture_id}: bridge_terms must be a non-empty object")
    else:
        missing_terms = sorted(term for term in covers if term not in bridge_terms and term not in {"burden_notation", "operator_signature", "expanded_R", "same_burden_algebra"})
        if missing_terms:
            errors.append(f"{fixture_id}: bridge_terms missing covered term explanations: {missing_terms}")

    control_effects = payload.get("control_effects")
    effect_keys = set(control_effects) if isinstance(control_effects, dict) else set()
    if not effect_keys:
        errors.append(f"{fixture_id}: control_effects must name a runtime control effect")
    if "closure_prevention" in matrix_cases and "partial_behavior" not in effect_keys:
        errors.append(f"{fixture_id}: closure_prevention matrix case must exercise partial_behavior")

    projection = payload.get("ir_projection")
    decision: str | None = None
    if not isinstance(projection, dict):
        errors.append(f"{fixture_id}: ir_projection must be present and object")
    else:
        forbidden = sorted(nested_dict_keys(projection) & REGISTER_SCHEMA_KEYS)
        if forbidden:
            errors.append(f"{fixture_id}: fixture projection uses hard register-formalism bridge schema fields: {forbidden}")

        matched = string_list(projection.get("matched_modules"))
        if not matched:
            errors.append(f"{fixture_id}: ir_projection.matched_modules must list existing controls")
        for module_id in matched:
            entry = modules.get(module_id)
            if entry is None:
                errors.append(f"{fixture_id}: matched module not found in compiled-module-map.json: {module_id}")
            elif not entry.get("bundle_path"):
                errors.append(f"{fixture_id}: matched module lacks bundle_path: {module_id}")

        decision = validate_post_render_gate(fixture_id, projection.get("post_render_gate"), errors)

    for source_ref in string_list(payload.get("source_governance_refs")):
        if not (root / source_ref).is_file():
            errors.append(f"{fixture_id}: source_governance_ref missing: {source_ref}")

    if "same_burden_algebra" in covers:
        same = payload.get("same_burden_test")
        required = {"same_tau", "same_xi", "same_omega", "same_sigma", "same_kappa", "expected"}
        if not isinstance(same, dict) or not required.issubset(same):
            errors.append(f"{fixture_id}: same_burden_algebra coverage requires same_burden_test with {sorted(required)}")

    if "terminal_restoration" in covers:
        terminal = payload.get("terminal_formalism")
        if not isinstance(terminal, dict):
            errors.append(f"{fixture_id}: terminal coverage requires terminal_formalism object")
        elif terminal.get("requires_stop_decision") is not True:
            errors.append(f"{fixture_id}: terminal_formalism must require STOP decision")
        if decision != "STOP":
            errors.append(f"{fixture_id}: terminal coverage requires post_render_gate STOP")

    if "shannon_boundary" in covers:
        forbidden_claims = string_list(payload.get("forbidden_claims"))
        if len(forbidden_claims) < 3:
            errors.append(f"{fixture_id}: shannon_boundary coverage requires multiple forbidden_claims")
        blocker = payload.get("expected_blocker")
        if not isinstance(blocker, str) or "truth" not in blocker.lower() or "warrant" not in blocker.lower():
            errors.append(f"{fixture_id}: shannon_boundary expected_blocker must forbid truth/meaning/warrant entropy")

    if "anti_symbol_theater" in covers:
        policy = payload.get("visible_symbol_policy")
        has_forbidden_symbols = bool(string_list(payload.get("forbidden_visible_symbols")))
        if not isinstance(policy, dict) and not has_forbidden_symbols:
            errors.append(f"{fixture_id}: anti_symbol_theater coverage requires visible_symbol_policy or forbidden_visible_symbols")
        if isinstance(policy, dict) and policy.get("requires_control_effect") is not True:
            errors.append(f"{fixture_id}: visible_symbol_policy must require a control effect")

    if "divergence_curl_operators" in covers:
        detection = payload.get("operator_detection")
        if not isinstance(detection, dict):
            errors.append(f"{fixture_id}: divergence_curl_operators coverage requires operator_detection object")
        else:
            flattened = json.dumps(detection, ensure_ascii=False).lower()
            if not has_all_operator_forms(json.dumps(detection, ensure_ascii=False)):
                errors.append(f"{fixture_id}: operator_detection missing one or more ∇/del/nabla operator forms")
            classifications = detection.get("classification")
            if not isinstance(classifications, dict):
                errors.append(f"{fixture_id}: operator_detection.classification must be an object")
            else:
                used = {value for value in classifications.values() if isinstance(value, str)}
                missing_classes = sorted(
                    required for required in DIVERGENCE_CURL_CLASSIFICATIONS if required not in used
                )
                if missing_classes:
                    errors.append(f"{fixture_id}: operator_detection missing classifications: {missing_classes}")
            required_terms = (
                "not replacement",
                "audit/formalism",
                "default runtime",
                "target-explicit",
                "not restricted",
                "scalar",
                "burden",
                "register",
                "expansion",
                "contraction",
                "loop",
                "circulation",
                "partial",
                "recurse",
                "closure",
            )
            for term in required_terms:
                if term not in flattened:
                    errors.append(f"{fixture_id}: operator_detection missing control/boundary term {term!r}")

        policy = payload.get("visible_symbol_policy")
        if not isinstance(policy, dict):
            errors.append(f"{fixture_id}: divergence/curl coverage requires visible_symbol_policy")
        else:
            policy_text = json.dumps(policy, ensure_ascii=False).lower()
            if "default" not in policy_text or "audit/formalism" not in policy_text:
                errors.append(f"{fixture_id}: visible_symbol_policy must distinguish default from audit/formalism visibility")
            if policy.get("requires_control_effect") is not True:
                errors.append(f"{fixture_id}: divergence/curl visible_symbol_policy must require a control effect")
        if not ({"partial_behavior", "reread"} & effect_keys):
            errors.append(f"{fixture_id}: divergence/curl coverage must affect reread or PARTIAL/RECURSE behavior")

    if "nla_reconstruction" in covers:
        nla_mapping = payload.get("nla_mapping")
        if not isinstance(nla_mapping, dict):
            errors.append(f"{fixture_id}: nla_reconstruction coverage requires nla_mapping object")
        else:
            flattened = json.dumps(nla_mapping, ensure_ascii=False).lower()
            required_terms = (
                "activation verbalizer",
                "activation reconstructor",
                "layer a",
                "ir verbalization",
                "r(h,delta)",
                "reconstruction",
                "partial",
                "recurse",
                "checker",
                "confabulation",
                "truth",
                "warrant",
            )
            for term in required_terms:
                if term not in flattened:
                    errors.append(f"{fixture_id}: nla_mapping missing term {term!r}")
            if "generic linear algebra" in flattened and "not generic linear algebra" not in flattened:
                errors.append(f"{fixture_id}: nla_mapping may reduce NLA to generic linear algebra")
        if not ({"reread", "burden_selection", "owner_choice", "partial_behavior"} & effect_keys):
            errors.append(f"{fixture_id}: nla_reconstruction must affect reconstruction, routing, or closure")

    if kind == "negative":
        if not string_list(payload.get("forbidden_claims")) and not string_list(payload.get("forbidden_visible_symbols")):
            errors.append(f"{fixture_id}: negative fixture must forbid claims or visible symbols")
        if not isinstance(payload.get("expected_blocker"), str) or not payload["expected_blocker"].strip():
            errors.append(f"{fixture_id}: negative fixture must name expected_blocker")

    return covers, effect_keys, decision


def check_bridge_fixtures(root: Path, errors: list[str]) -> None:
    fixture_root = root / REGISTER_FORMALISM_FIXTURE_DIR
    if not fixture_root.is_dir():
        errors.append(f"{REGISTER_FORMALISM_FIXTURE_DIR.as_posix()}: missing register-formalism bridge behavior fixtures")
        return

    modules = compiled_modules(root)
    paths = sorted(fixture_root.glob("*.json"))
    if len(paths) < 8:
        errors.append(f"{REGISTER_FORMALISM_FIXTURE_DIR.as_posix()}: expected at least 8 fixtures, found {len(paths)}")

    coverage: set[str] = set()
    effect_coverage: set[str] = set()
    matrix_coverage: set[str] = set()
    register_effects: dict[str, set[str]] = {register: set() for register in REGISTER_EFFECT_REQUIREMENTS}
    decisions: set[str] = set()
    positive_count = 0
    negative_count = 0

    for path in paths:
        payload = load_json(path, errors)
        if isinstance(payload, dict):
            if payload.get("kind") == "positive":
                positive_count += 1
            elif payload.get("kind") == "negative":
                negative_count += 1
            matrix_coverage.update(string_list(payload.get("matrix_cases")))

        covers, effects, decision = validate_bridge_fixture(root, path, modules, errors)
        coverage.update(covers)
        effect_coverage.update(effects)
        if decision:
            decisions.add(decision)
        for register in register_effects:
            if register in covers:
                register_effects[register].update(effects)

    missing_coverage = sorted(BRIDGE_REQUIRED_COVERAGE - coverage)
    if missing_coverage:
        errors.append(f"register-formalism fixtures missing coverage: {missing_coverage}")

    missing_effects = sorted(BEHAVIOR_EFFECTS_REQUIRED - effect_coverage)
    if missing_effects:
        errors.append(f"register-formalism fixtures missing behavior effects: {missing_effects}")

    missing_matrix = sorted(FIXTURE_MATRIX_REQUIRED - matrix_coverage)
    if missing_matrix:
        errors.append(f"register-formalism fixtures missing matrix cases: {missing_matrix}")

    for register, required_effects in REGISTER_EFFECT_REQUIREMENTS.items():
        missing = sorted(required_effects - register_effects[register])
        if missing:
            errors.append(f"register-formalism fixture for {register} missing control effects: {missing}")

    for required_decision in ("STOP", "HOLD", "RECURSE", "PARTIAL"):
        if required_decision not in decisions:
            errors.append(f"register-formalism fixtures do not exercise post-render decision: {required_decision}")

    if positive_count < 6:
        errors.append(f"register-formalism fixtures need at least 6 positive fixtures, found {positive_count}")
    if negative_count < 2:
        errors.append(f"register-formalism fixtures need at least 2 negative fixtures, found {negative_count}")


def check_required_tokens(root: Path, errors: list[str]) -> None:
    for rel, tokens in REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: missing")
            continue
        text = read(root, rel)
        lower = text.lower()
        for token in tokens:
            if token not in text and token.lower() not in lower:
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
            errors.append(f"{rel}: hard register-formalism bridge register schema fields present: {forbidden}")


def check_ledger_status(root: Path, errors: list[str]) -> None:
    text = read(root, "docs/register-formalism-implementation-ledger.md")
    required = [
        "PROVEN IMPLEMENTED",
        "DEFERRED WITH BLOCKER",
        "tests/register-formalism-bridge-fixtures/",
        "installed-skill live smoke proof",
        "current-release package artifact smokes",
    ]
    for token in required:
        if token not in text:
            errors.append(f"ledger: missing proof-boundary token {token!r}")
    if "| IMPLEMENTED |" in text:
        errors.append("ledger: bare IMPLEMENTED status is forbidden; use proof-boundary statuses")
    if (
        "It does not mean current-release package artifact" not in text
        or "smokes have passed" not in text
    ):
        errors.append("ledger: missing release-package proof caveat")

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
    check_algebraic_symbol_audit(root, errors)
    check_nla_operativity_audit(root, errors)
    check_cross_layer_consistency(root, errors)
    check_divergence_curl_audit_docs(root, errors)
    check_default_runtime_operator_boundary(root, errors)
    check_bridge_fixtures(root, errors)
    return fail_with_errors("register-formalism bridge", errors)


if __name__ == "__main__":
    raise SystemExit(main())
