#!/usr/bin/env python3
"""Baseline TTP operator-contract integrity checker.

This checker is intentionally conservative. It proves that the live module
catalogue resolves to tracked owner files and that owner files do not contain
known field-accounting anti-patterns. It does not claim every TTP has already
received the full runtime-operator contract; that remediation is tracked in
the v0.4.1.0 TTP end-to-end operativity audit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from compiled_runtime_lib import fail_with_errors, repo_root


CATALOGUE = Path("atomics/skill/references/diagnostics/module-catalogue.json")
AUDIT_JSON = Path("docs/audits/v0.4.1.0-ttp-end-to-end-operativity-audit.json")
ALLOWED_CLASSES = {"case-library", "diagnostic", "procedure", "tactic", "technique"}
INHERITED_FIELD_OPERATOR_REQUIREMENTS = {
    "atomics/skill/references/diagnostics/recursive-state-transitions.md": (
        "Plain `∇` is the route-gradient read over the live field",
        "Routing remains owner-gated and catalogue-constrained",
        "LoopBreak(∇×T)",
        "Terminal formalism: `𝒞(Ψᴺ)` names the positive closure-field condition",
        "`Ψᴵ` names the diagnosed",
        "T_lang: Ψᴺ ⇢ Ψᴵ",
    ),
    "atomics/skill/references/rubrics/output-release.md": (
        "∇ route-gradient over eligible live pressure",
        "LoopBreak(∇×T)",
        "𝒞(Ψᴺ)",
        "T_lang",
    ),
}
REQUIRED_FRONTMATTER_KEYS = {
    "id",
    "module_class",
    "canonical_path",
    "contract_version",
    "load_when",
    "output_shapes",
}

FIELD_TARGET_TERMS = (
    "target",
    "noetic",
    "burden",
    "dependency",
    "register",
    "route",
    "criterion",
    "tribunal",
    "authority",
    "concealment",
    "deformation",
    "kappa",
    "heart",
    "xi",
    "omega",
    "mu",
)

FORBIDDEN_PATTERNS = {
    "nabla-replaces-delta": re.compile(
        r"(?:∇|del-dot|del-cross|divergence|curl).{0,80}"
        r"(?:replaces|substitutes for|instead of).{0,80}(?:Δ|Delta)",
        re.I | re.S,
    ),
    "nabla-proof-by-symbol": re.compile(
        r"(?:∇|del-dot|del-cross|divergence|curl).{0,80}"
        r"(?:proves|certifies|guarantees).{0,80}"
        r"(?:truth|warrant|TTP|execution|executed)",
        re.I | re.S,
    ),
    "truth-warrant-metric": re.compile(
        r"(?:Shannon|entropy|NLA|Natural Language Autoencoder|∇|divergence|curl)"
        r".{0,80}(?:measures|proves|certifies|guarantees).{0,80}"
        r"(?:truth|meaning|warrant|revelation|fitrah|sound reason)",
        re.I | re.S,
    ),
    "del-dot-separate-operator": re.compile(
        r"del-dot.{0,80}(?:separate|distinct|independent).{0,40}operator",
        re.I | re.S,
    ),
    "del-cross-separate-operator": re.compile(
        r"del-cross.{0,80}(?:separate|distinct|independent).{0,40}operator",
        re.I | re.S,
    ),
    "selected-path-is-whole-field": re.compile(
        r"selected execution path.{0,60}(?:is|equals|=).{0,20}(?:the )?whole field",
        re.I | re.S,
    ),
    "nla-branding": re.compile(
        r"(?:NLA|Natural Language Autoencoder).{0,80}(?:branding|decorative)",
        re.I | re.S,
    ),
    "gradient-bypasses-gates": re.compile(
        r"(?:∇|route-gradient).{0,80}(?:bypasses|overrides).{0,80}"
        r"(?:gate|gates|catalogue|IR|routing)",
        re.I | re.S,
    ),
    "loopbreak-arbitrary": re.compile(
        r"LoopBreak.{0,80}(?:arbitrary assertion|ungrounded assertion)",
        re.I | re.S,
    ),
    "closure-conversion-guarantee": re.compile(
        r"(?:𝒞\(Ψᴺ\)|closure-field).{0,100}"
        r"(?:guarantees|ensures|proves).{0,80}(?:conversion|acceptance|uptake)",
        re.I | re.S,
    ),
    "psi-i-soul-access": re.compile(
        r"(?:Ψᴵ|PsiI|interlocutor field).{0,100}(?:access to|reads|knows).{0,80}(?:soul|qalb)",
        re.I | re.S,
    ),
    "agent-controls-guidance": re.compile(
        r"(?:agent|runtime).{0,80}(?:controls|guarantees).{0,80}guidance",
        re.I | re.S,
    ),
}

DELTA = "\u0394"
NABLA = "\u2207"

CONTRACT_HEADINGS = (
    "## Runtime operator contract",
    "## Runtime field-accounting contract",
)

STRICT_COMMON_FIELDS = (
    "Field target:",
    f"{DELTA} effect:",
    f"Possible {NABLA} reread:",
    f"R(H,{DELTA}) obligation:",
    "Hold/release/closure effect:",
    "Output boundary:",
    "Negative constraints:",
    "Fixture/checker:",
)

STRICT_OPERATOR_FIELDS = (
    "Activation:",
    "Burden/submove form:",
)

STRICT_FIELD_ACCOUNTING_FIELDS = (
    "Activation/profile condition:",
    "Burden pressures usually exposed:",
)


def parse_frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    frontmatter = text[: end + 4]
    data: dict[str, object] = {}
    current: str | None = None
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped == "---" or not stripped:
            continue
        if re.match(r"^[A-Za-z0-9_-]+:", line):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if value:
                data[key] = value
                current = None
            else:
                data[key] = []
                current = key
            continue
        if current and stripped.startswith("- "):
            existing = data.setdefault(current, [])
            if isinstance(existing, list):
                existing.append(stripped[2:])
    return data


def resolve_owner(root: Path, legacy_path: str) -> Path:
    if legacy_path.startswith("skill/"):
        return root / "atomics/skill" / legacy_path[len("skill/") :]
    return root / legacy_path


def has_field_target(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in FIELD_TARGET_TERMS)


def contains_field_diagnostic(text: str) -> bool:
    lowered = text.lower()
    return any(
        token in text or token in lowered
        for token in ("∇·", "∇×", "del-dot", "del-cross", "divergence", "curl")
    )


def has_field_diagnostic_boundary(text: str) -> bool:
    lowered = text.lower()
    if not contains_field_diagnostic(text):
        return True
    required_any = (
        "target-explicit",
        "field target",
        "explicit target",
        "not a transition",
        "not transition operators",
        "not substitutes",
        "not restricted",
        "control effect",
        "closure",
        "recurse",
        "partial",
        "r(h,delta)",
        "r(h,δ)",
    )
    return any(term in lowered for term in required_any)


def extract_runtime_contract(text: str) -> tuple[str | None, str]:
    heading_positions = [
        (text.find(heading), heading)
        for heading in CONTRACT_HEADINGS
        if text.find(heading) != -1
    ]
    if not heading_positions:
        return None, ""
    start, heading = min(heading_positions, key=lambda item: item[0])
    next_heading = re.search(r"(?m)^##\s+", text[start + len(heading) :])
    end = start + len(heading) + next_heading.start() if next_heading else len(text)
    return heading, text[start:end]


def check_strict_contract(module_id: str, text: str, errors: list[str]) -> None:
    heading, contract = extract_runtime_contract(text)
    if not heading:
        if "NOT_APPLICABLE" in text and "runtime operator contract" in text.lower():
            return
        errors.append(f"{module_id}: missing Runtime operator/field-accounting contract")
        return

    expected = list(STRICT_COMMON_FIELDS)
    if heading == "## Runtime field-accounting contract":
        expected.extend(STRICT_FIELD_ACCOUNTING_FIELDS)
    else:
        expected.extend(STRICT_OPERATOR_FIELDS)

    for field in expected:
        if field not in contract:
            errors.append(f"{module_id}: runtime contract missing field {field!r}")

    lowered = contract.lower()
    if "target-explicit" not in lowered:
        errors.append(f"{module_id}: runtime contract must require target-explicit field diagnostics")
    if "r(h," not in lowered:
        errors.append(f"{module_id}: runtime contract must bind action to R(H,Delta)/R(H,Δ)")
    if "truth-or-warrant" not in lowered and "truth/warrant" not in lowered:
        errors.append(f"{module_id}: runtime contract must forbid truth/warrant overclaim")
    if "proof-by-symbol" not in lowered:
        errors.append(f"{module_id}: runtime contract must forbid proof-by-symbol")
    if "no scalar" not in lowered and "scalar summary" not in lowered:
        errors.append(f"{module_id}: runtime contract must guard against scalar closure/collapse")
    if "? effect:" in contract or "Possible ? reread:" in contract or "R(H,?) obligation:" in contract:
        errors.append(f"{module_id}: runtime contract contains placeholder question-mark notation")


def check_inherited_field_operator_requirements(root: Path, errors: list[str]) -> None:
    """Ensure per-module contracts inherit the shared field-operator architecture."""
    for rel, tokens in INHERITED_FIELD_OPERATOR_REQUIREMENTS.items():
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: missing inherited field-operator owner")
            continue
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        for token in tokens:
            if token not in text and token.lower() not in lower:
                errors.append(f"{rel}: missing inherited field-operator token {token!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="require every catalogue owner to expose a runtime operator/field-accounting contract",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    errors: list[str] = []

    catalogue_path = root / CATALOGUE
    if not catalogue_path.is_file():
        return fail_with_errors("TTP operator contracts", [f"{CATALOGUE.as_posix()}: missing"])

    payload = json.loads(catalogue_path.read_text(encoding="utf-8"))
    modules = payload.get("modules")
    if not isinstance(modules, list) or not modules:
        return fail_with_errors("TTP operator contracts", ["module catalogue has no modules list"])

    check_inherited_field_operator_requirements(root, errors)

    seen: set[str] = set()
    for index, entry in enumerate(modules):
        if not isinstance(entry, dict):
            errors.append(f"module entry {index}: not an object")
            continue
        module_id = entry.get("id")
        module_class = entry.get("module_class")
        legacy_path = entry.get("path")
        if not isinstance(module_id, str) or not module_id:
            errors.append(f"module entry {index}: missing id")
            continue
        if module_id in seen:
            errors.append(f"duplicate module id in catalogue: {module_id}")
        seen.add(module_id)
        if module_class not in ALLOWED_CLASSES:
            errors.append(f"{module_id}: invalid module_class {module_class!r}")
        if not isinstance(legacy_path, str) or not legacy_path:
            errors.append(f"{module_id}: missing path")
            continue
        owner = resolve_owner(root, legacy_path)
        if not owner.is_file():
            errors.append(f"{module_id}: owner file missing: {legacy_path} -> {owner}")
            continue
        text = owner.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)
        for key in REQUIRED_FRONTMATTER_KEYS:
            if key not in frontmatter:
                errors.append(f"{module_id}: front matter missing {key!r}")
        if frontmatter.get("id") != module_id:
            errors.append(f"{module_id}: front matter id mismatch: {frontmatter.get('id')!r}")
        if frontmatter.get("module_class") != module_class:
            errors.append(
                f"{module_id}: front matter module_class mismatch: {frontmatter.get('module_class')!r}"
            )
        if frontmatter.get("canonical_path") != legacy_path:
            errors.append(
                f"{module_id}: canonical_path does not match catalogue path {legacy_path!r}"
            )
        if "catalogue_registered: true" not in text:
            errors.append(f"{module_id}: owner does not mark catalogue_registered: true")
        if not has_field_target(text):
            errors.append(f"{module_id}: owner lacks field-target/pressure language")
        if not has_field_diagnostic_boundary(text):
            errors.append(
                f"{module_id}: field-diagnostic notation lacks target/control boundary"
            )
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{module_id}: forbidden TTP operator claim: {label}")
        if args.strict:
            check_strict_contract(module_id, text, errors)

    audit_path = root / AUDIT_JSON
    if not audit_path.is_file():
        errors.append(f"{AUDIT_JSON.as_posix()}: missing TTP operativity audit JSON")
    else:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit.get("catalogue_count") != len(modules):
            errors.append(
                f"{AUDIT_JSON.as_posix()}: catalogue_count does not match live catalogue"
            )
        audited_ids = {
            module.get("id")
            for module in audit.get("modules", [])
            if isinstance(module, dict)
        }
        missing_ids = sorted(seen - audited_ids)
        if missing_ids:
            errors.append(f"{AUDIT_JSON.as_posix()}: missing audited IDs: {missing_ids}")

    if not errors:
        print("TTP operator contract baseline summary")
        print("-" * 60)
        print(f"Catalogue entries checked: {len(modules)}")
        print(f"Allowed classes: {', '.join(sorted(ALLOWED_CLASSES))}")
        print("Owner path/frontmatter integrity: pass")
        print("Forbidden operator claims: pass")
        print("Inherited route-gradient / LoopBreak / closure-field / coupling guard: pass")
        print("Audit JSON parity: pass")
        print(f"Strict runtime contracts: {'on' if args.strict else 'off'}")
        print("-" * 60)

    return fail_with_errors("TTP operator contracts", errors)


if __name__ == "__main__":
    sys.exit(main())
