#!/usr/bin/env python3
"""Guard the Pipeline #2 derived/conditional bridge against drift."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


PIPELINE2_FIXTURE_DIR = Path("tests/pipeline2-bridge-fixtures")

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
        "Pipeline #2 is implemented in this repo",
        "tests/pipeline2-bridge-fixtures/",
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
        "PROVEN IMPLEMENTED",
        "DEFERRED WITH BLOCKER",
        "tests/pipeline2-bridge-fixtures/",
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
        "tests/pipeline2-bridge-fixtures/",
        "not a mandatory register-field schema migration",
        "not a v0.4.0.0 readiness",
    ],
    "TODO.md": [
        "Pipeline #2 Live Smoke / Hard Schema / Release Migration Decision",
        "tools/check_pipeline2_bridge.py",
        "Required verification already present for bridge behavior",
        "v0.4.0.0 release consideration",
    ],
    "AGENTS.md": [
        "python tools/check_pipeline2_bridge.py",
        "Pipeline #2 derived/conditional bridge semantics are",
        "tests/pipeline2-bridge-fixtures/",
        "Bridge live-smoke proof",
        "do not claim a release-line migration from the index page",
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
    "Retained compact runtime spine",
    "historical baseline",
    "Pipeline #2",
    "derived/conditional bridge",
    "hard schema",
    "current runtime state",
    "source-governance",
    "fixture-proven",
    "Shannon entropy measures truth",
]

INDEX_FORBIDDEN = [
    "Pipeline #2 — target repo state",
    "Pipeline #2 - target repo state",
    "live <code>♥/ξ/Ω/μ/κ</code> register controls",
    "Pipeline #2 bridge now implements",
    "Pipeline #2 — implemented derived/conditional bridge",
    "Bridge implementation merge",
    "not yet first-class registers",
    "Defer as runtime",
    "Pipeline #2 as current runtime architecture",
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

    rel = path.relative_to(root).as_posix()
    fixture_id = payload.get("id")
    if not isinstance(fixture_id, str) or not fixture_id:
        errors.append(f"{rel}: missing fixture id")
        fixture_id = rel

    kind = payload.get("kind")
    if kind not in {"positive", "negative"}:
        errors.append(f"{fixture_id}: kind must be positive or negative")

    covers = set(string_list(payload.get("covers")))
    if not covers:
        errors.append(f"{fixture_id}: covers must list Pipeline #2 terms")

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

    projection = payload.get("ir_projection")
    decision: str | None = None
    if not isinstance(projection, dict):
        errors.append(f"{fixture_id}: ir_projection must be present and object")
    else:
        forbidden = sorted(nested_dict_keys(projection) & REGISTER_SCHEMA_KEYS)
        if forbidden:
            errors.append(f"{fixture_id}: fixture projection uses hard Pipeline #2 schema fields: {forbidden}")

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

    if kind == "negative":
        if not string_list(payload.get("forbidden_claims")) and not string_list(payload.get("forbidden_visible_symbols")):
            errors.append(f"{fixture_id}: negative fixture must forbid claims or visible symbols")
        if not isinstance(payload.get("expected_blocker"), str) or not payload["expected_blocker"].strip():
            errors.append(f"{fixture_id}: negative fixture must name expected_blocker")

    return covers, effect_keys, decision


def check_bridge_fixtures(root: Path, errors: list[str]) -> None:
    fixture_root = root / PIPELINE2_FIXTURE_DIR
    if not fixture_root.is_dir():
        errors.append(f"{PIPELINE2_FIXTURE_DIR.as_posix()}: missing Pipeline #2 behavior fixtures")
        return

    modules = compiled_modules(root)
    paths = sorted(fixture_root.glob("*.json"))
    if len(paths) < 8:
        errors.append(f"{PIPELINE2_FIXTURE_DIR.as_posix()}: expected at least 8 fixtures, found {len(paths)}")

    coverage: set[str] = set()
    effect_coverage: set[str] = set()
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
        errors.append(f"Pipeline #2 fixtures missing coverage: {missing_coverage}")

    missing_effects = sorted(BEHAVIOR_EFFECTS_REQUIRED - effect_coverage)
    if missing_effects:
        errors.append(f"Pipeline #2 fixtures missing behavior effects: {missing_effects}")

    for register, required_effects in REGISTER_EFFECT_REQUIREMENTS.items():
        missing = sorted(required_effects - register_effects[register])
        if missing:
            errors.append(f"Pipeline #2 fixture for {register} missing control effects: {missing}")

    for required_decision in ("STOP", "HOLD", "RECURSE", "PARTIAL"):
        if required_decision not in decisions:
            errors.append(f"Pipeline #2 fixtures do not exercise post-render decision: {required_decision}")

    if positive_count < 6:
        errors.append(f"Pipeline #2 fixtures need at least 6 positive fixtures, found {positive_count}")
    if negative_count < 2:
        errors.append(f"Pipeline #2 fixtures need at least 2 negative fixtures, found {negative_count}")


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
    required = [
        "PROVEN IMPLEMENTED",
        "DEFERRED WITH BLOCKER",
        "tests/pipeline2-bridge-fixtures/",
        "fresh live/package-bound smokes",
    ]
    for token in required:
        if token not in text:
            errors.append(f"ledger: missing proof-boundary token {token!r}")
    if "| IMPLEMENTED |" in text:
        errors.append("ledger: bare IMPLEMENTED status is forbidden; use proof-boundary statuses")
    if "It does not mean fresh live/package-bound smokes have passed" not in text:
        errors.append("ledger: missing live-smoke proof caveat")

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
    check_bridge_fixtures(root, errors)
    return fail_with_errors("pipeline2 bridge", errors)


if __name__ == "__main__":
    raise SystemExit(main())
