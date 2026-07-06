#!/usr/bin/env python3
"""Assemble a staged governed output from hash-checked section artifacts.

This is repo/dev tooling for Brandolini-safe staged output construction. It
does not author reasoning, run validators, build sidecars, or promote retained
proof. It only compiles an output from bounded sections after checking the
assembly manifest, paths, hashes, section order, and public-output non-claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Callable


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
ASSEMBLY_SCHEMA = "staged-governed-output-assembly-v1"
HASH_RECORD_SCHEMA = "staged-governed-output-assembly-hashes-v1"
ACT_PARTITION_SCHEMA = "staged-act-partition-v1"
SECTION_BUDGET_SCHEMA = "staged-section-budget-v1"
SECTION_EXPANSIONS_SCHEMA = "staged-section-expansions-v1"
CANONICAL_SCAFFOLD_SCHEMA = "staged-canonical-scaffold-v1"
REQUIRED_NON_CLAIMS = {
    "not_release_provenance",
    "not_model_behavior_by_itself",
    "not_sidecar_proof",
}
ROLE_ORDER = [
    "visible_opening",
    "layer_a_diagnostic_ir",
    "layer_b_act",
    "mrp_reread_terminal",
    "restorative_response",
    "closing_formulation",
    "field_witness_nar",
]
ROLE_INDEX = {role: index for index, role in enumerate(ROLE_ORDER)}
SINGLETON_ROLES = {
    "visible_opening",
    "layer_a_diagnostic_ir",
    "mrp_reread_terminal",
    "field_witness_nar",
    "restorative_response",
    "closing_formulation",
}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def public_heading_pattern(heading: str) -> re.Pattern[str]:
    escaped = re.escape(heading)
    return re.compile(
        rf"(?im)^\s*(?:#+\s*)?"
        rf"(?:(?P<decor>\*\*|__|\*|_)\s*)?"
        rf"{escaped}"
        rf"(?(decor)\s*(?P=decor))"
        rf"\s*(?:#+\s*)?$"
    )


def decorated_public_heading_variant_pattern(heading: str) -> re.Pattern[str]:
    escaped = re.escape(heading)
    return re.compile(rf"(?i)^(?P<decor>\*\*|__|\*|_)\s*{escaped}\s*(?P=decor)$")


def embedded_decorated_public_heading_pattern(heading: str) -> re.Pattern[str]:
    escaped = re.escape(heading)
    return re.compile(rf"(?i)(?:\*\*|__|\*|_)\s*{escaped}\s*(?:\*\*|__|\*|_)")


CANONICAL_ROLE_HEADINGS = {
    "field_witness_nar": {
        "heading": "Closure/Reconstruction Witness",
        "variants": [re.compile(r"^Closure\s*/\s*Reconstruction\s+Witness$", re.IGNORECASE)],
        "insert_if_missing": True,
    },
    "restorative_response": {
        "heading": "Restorative Response",
        "variants": [decorated_public_heading_variant_pattern("Restorative Response")],
        "insert_if_missing": True,
    },
    "closing_formulation": {
        "heading": "Closing Formulation",
        "variants": [decorated_public_heading_variant_pattern("Closing Formulation")],
        "insert_if_missing": True,
    },
}
FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "harness commentary",
        re.compile(
            r"You are executing stage-|Validated compact stage state|Return exactly one JSON object|"
            r"assembly manifest|staged-governed-output-assembly-v1|compiler note|repo/dev scratch",
            re.IGNORECASE,
        ),
    ),
    (
        "package/provenance/release claim",
        re.compile(
            r"GitHub Release|release asset|release package|package provenance|published provenance|"
            r"provenance (?:asset|publication|proof)|\.skill archive",
            re.IGNORECASE,
        ),
    ),
    (
        "guaranteed T_lang uptake claim",
        re.compile(
            r"T_lang\s+guarantees|guaranteed\s+T_lang\s+uptake|"
            r"guarantees\s+interlocutor\s+uptake|guarantees\s+uptake",
            re.IGNORECASE,
        ),
    ),
    (
        "sidecar proof claim before Stage 8",
        re.compile(
            r"Stage\s*8[^.\n]{0,80}\b(?:pass|passed|proof)\b|"
            r"\bsidecar[^.\n]{0,80}\b(?:proves|proof|passed|built)\b|"
            r"\bcollapse certificate[^.\n]{0,80}\b(?:proves|passed)\b|"
            r"\bGrapher[^.\n]{0,80}\bproof\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Graphify/ActiveGraph proof claim",
        re.compile(r"Graphify[^.\n]{0,80}\bproof\b|ActiveGraph[^.\n]{0,80}\bproof\b", re.IGNORECASE),
    ),
]
TLANG_UPTAKE_NONCLAIM_RE = re.compile(
    r"(?is)\b(?:does\s+not\s+(?:claim|imply)|may\s+not\s+say|"
    r"not\s+(?:claim|guarantee)|no|without)\b"
    r"[^.\n;]{0,180}\b(?:guarantees?\s+uptake|guaranteed\s+(?:T_lang\s+)?uptake|"
    r"interlocutor\s+uptake)\b"
)
SIDECAR_PROOF_NONCLAIM_RE = re.compile(
    r"(?is)\b(?:does\s+not|do\s+not|not|no|without)\b[^.\n;]{0,180}"
    r"\b(?:create|claim|build|produce|emit|include|make|generated?)?\b[^.\n;]{0,80}"
    r"\b(?:verifier\s+sidecars?|sidecar\s+proof|release\s+proof|proof\s+artifacts?|"
    r"downstream\s+artifacts?|Stage\s*8)\b"
)
PACKAGE_PROVENANCE_RELEASE_NONCLAIM_RE = re.compile(
    r"(?is)\b(?:does\s+not|do\s+not|not|no|without|non-claim)\b[^.\n;]{0,220}"
    r"\b(?:GitHub\s+Release|release\s+(?:asset|package|evidence|proof)|"
    r"package\s+provenance|published\s+provenance|"
    r"provenance\s+(?:asset|publication|proof)|\.skill\s+archive)\b"
)


def match_sentence(text: str, start: int, end: int) -> str:
    left = max(text.rfind("\n", 0, start), text.rfind(".", 0, start), text.rfind(";", 0, start))
    right_candidates = [pos for pos in (text.find("\n", end), text.find(".", end), text.find(";", end)) if pos != -1]
    right = min(right_candidates) if right_candidates else len(text)
    return text[left + 1 : right]

OPTIONAL_TOOLING_PROOF_NONCLAIM_RE = re.compile(
    r"(?:"
    r"\b(?:no|not|without)\b[^.\n]{0,80}\b(?:Graphify|ActiveGraph)\b"
    r"[^.\n]{0,120}\b(?:proof|proofs|claim|claimed|claims)\b"
    r"|"
    r"\b(?:Graphify|ActiveGraph)\b[^.\n]{0,80}\b(?:proof|proofs|claim|claims)\b"
    r"[^.\n]{0,120}\b(?:remain(?:s)?\s+held|held|not\s+(?:claimed|inferred)|non[- ]claim)\b"
    r")",
    re.IGNORECASE,
)
OPTIONAL_TOOLING_POSITIVE_PROOF_RE = re.compile(
    r"\b(?:Graphify|ActiveGraph)\b[^.\n]{0,80}\b"
    r"(?:proves|proved|passed|verified|built|complete|success|certifies|certified)\b",
    re.IGNORECASE,
)
PUBLIC_META_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "private planning or self-talk in public section",
        re.compile(
            r"(?im)^\s*(?:"
            r"Final answer only text\?|"
            r"Need (?:include|public|length|process|not|ensure|maybe|final|to)\b|"
            r"Let's (?:produce|write|craft|answer)\b|"
            r"Now final\b|"
            r"Hmm\b|"
            r"Potential exact quote\b|"
            r"Safety:\b|"
            r"Desired oververbosity\b"
            r")"
        ),
    ),
]
SURFACE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("visible noetic-field opening/header", re.compile(r"NOETIC FIELD EXECUTION|noetic-field", re.IGNORECASE)),
    (
        "compact Layer A / Diagnostic IR header",
        re.compile(r"Layer A\b.*(?:DSL/IR|Diagnostic IR|Header)", re.IGNORECASE | re.DOTALL),
    ),
    (
        "Layer A initial burden ledger",
        re.compile(r"Initial burden set\b.*B[_ -]?LA|B[_ -]?LA\b.*Initial burden set", re.IGNORECASE | re.DOTALL),
    ),
    ("governed Layer B / ACT surface", re.compile(r"Layer B\b.*(?:ACT|Bounded Governed Response)", re.IGNORECASE | re.DOTALL)),
    ("ACT body_ref tokens", re.compile(r"\bbody_ref=", re.IGNORECASE)),
    ("Land surface", re.compile(r"Land\(", re.IGNORECASE)),
    (
        "MRP / reread / terminal-state surface",
        re.compile(r"(?:\[Mid-Reread Pressure\]|MRP\(|R\(H,|Terminal states|MRP route result type)", re.IGNORECASE),
    ),
    (
        "parser-stable field_witness surface",
        re.compile(r"(?im)^\s*(?:#+\s*)?field_witness\b"),
    ),
    (
        "normalized_activation_record / NAR evidence",
        re.compile(r"normalized_activation_record|\bNAR\b", re.IGNORECASE),
    ),
    ("Closure/Reconstruction Witness", re.compile(r"Closure/Reconstruction Witness", re.IGNORECASE)),
    ("Restorative Response", public_heading_pattern("Restorative Response")),
    ("Closing Formulation", public_heading_pattern("Closing Formulation")),
]
BODY_REF_TOKEN_RE = re.compile(r"\bbody_ref=([^\s:⟧]+)")
SUP_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
SUB_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
BODY_REF_BURDEN_RE = re.compile(r"^(?P<burden>[⁰¹²³⁴⁵⁶⁷⁸⁹]+B|B[1-9][0-9]*)(?:[₀₁₂₃₄₅₆₇₈₉]+|[_\.s][0-9]+)?$")
ASCII_BODY_REF_RE = re.compile(r"^(?P<burden>[1-9][0-9]*)B[1-9][0-9]*$")
FIELD_WITNESS_LABEL_RE = re.compile(r"(?im)^\s*(?:#+\s*)?field_witness\b")
FINAL_PUBLIC_TAIL_ORDER = (
    "restorative_response",
    "closing_formulation",
    "closure_witness",
    "field_witness",
)
FINAL_PUBLIC_TAIL_LABELS = {
    "restorative_response": "Restorative Response",
    "closing_formulation": "Closing Formulation",
    "closure_witness": "Closure/Reconstruction Witness",
    "field_witness": "field_witness",
}
OWNER_ORDERING_POLICY_ID = "diagnostic-ir-pressure-owner-floor-v1"
OWNER_ORDERING_FAMILY_ALIASES = {
    "AUTHORITY-ORDER-REPAIR": "SOURCE",
    "DO-ATTRIBUTE-PRECISION": "DO_ATTRIBUTE",
    "DO-CHRISTIAN-EXTENSIONS": "DO_CHRISTIAN",
    "DO-SECOND-LOOP": "DO_SECOND_LOOP",
    "DOUBT-VS-SKEPTICISM": "DOUBT_SKEPTICISM",
    "PROOF-METHOD-AUDIT": "PROOF_METHOD",
    "SOURCE-STATUS-REPAIR": "SOURCE",
}
OWNER_ORDERING_CODE_RE = re.compile(r"^(?:M1-P|M[1-9]|P[1-7]|R[1-3]|FPD)$")
ORDERING_ROLES = {"required", "parallel", "contingent", "optional_non_load_bearing", "hold_partial"}
ASCII_TO_SUP_DIGITS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
ASCII_TO_SUB_DIGITS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
PUBLIC_SUBMOVE_HEADING_RE = re.compile(
    r"(?m)^(?P<prefix>\s*(?:#{1,6}\s*)?)"
    r"(?P<ref>(?:B(?P<ascii_burden>[1-9][0-9]*)[_\.](?P<ascii_sub>[1-9][0-9]*)|"
    r"(?P<public_burden>[⁰¹²³⁴⁵⁶⁷⁸⁹]+)B(?P<public_sub>[₀₁₂₃₄₅₆₇₈₉]+)))"
    r"(?P<owner>\s*\[[A-Za-z][A-Za-z0-9_.\-/]*\])"
    r"(?P<tail>(?:\s*\([^)]*\))?\s*(?:[-—:]).*)$"
)
PUBLIC_GRAPH_CONTEXT_RE = re.compile(
    r"(?i)^\s*(?:[-*]\s*)?(?:"
    r"Initial burden set|Held burden set|Held routes|Burden dependency graph|"
    r"Target|R\(H,|Route-gradient|MRP resultant|Graph delta|Graph-delta|"
    r"Terminal states|MRP\(|formal_reread_state|∇ route pressure"
    r")\b"
)


class AssemblyError(Exception):
    """Raised when a staged output assembly manifest is unsafe or invalid."""


def rel(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssemblyError(f"{rel(path)}: invalid JSON: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def require_under_root(root: Path, path: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise AssemblyError(f"{label}: path escapes root: {path}") from exc
    return resolved


def reject_unsafe_relative(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise AssemblyError(f"{label}: must be a non-empty relative path string")
    path = Path(value)
    if path.is_absolute():
        raise AssemblyError(f"{label}: absolute paths are not allowed")
    if any(part == ".." for part in path.parts):
        raise AssemblyError(f"{label}: '..' path components are not allowed")
    return path


def resolve_section_path(root: Path, manifest_dir: Path, value: Any, label: str) -> Path:
    relative = reject_unsafe_relative(value, label)
    manifest_candidate = require_under_root(root, manifest_dir / relative, label)
    root_candidate = require_under_root(root, root / relative, label)
    chosen = manifest_candidate if manifest_candidate.exists() else root_candidate
    if not chosen.exists():
        raise AssemblyError(f"{label}: section path does not exist: {value}")
    if not chosen.is_file():
        raise AssemblyError(f"{label}: section path must be a file: {value}")
    return chosen


def resolve_output_path(root: Path, manifest_dir: Path, value: Any, label: str) -> Path:
    relative = reject_unsafe_relative(value, label)
    return require_under_root(root, manifest_dir / relative, label)


def forbidden_text_errors(text: str, label: str) -> list[str]:
    errors: list[str] = []
    for name, pattern in FORBIDDEN_PATTERNS:
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        if name == "guaranteed T_lang uptake claim":
            positive_matches = [
                match
                for match in matches
                if not TLANG_UPTAKE_NONCLAIM_RE.search(match_sentence(text, match.start(), match.end()))
            ]
            if not positive_matches:
                continue
        if name == "sidecar proof claim before Stage 8":
            positive_matches = [
                match
                for match in matches
                if not SIDECAR_PROOF_NONCLAIM_RE.search(match_sentence(text, match.start(), match.end()))
            ]
            if not positive_matches:
                continue
        if name == "package/provenance/release claim":
            positive_matches = [
                match
                for match in matches
                if not PACKAGE_PROVENANCE_RELEASE_NONCLAIM_RE.search(
                    match_sentence(text, match.start(), match.end())
                )
            ]
            if not positive_matches:
                continue
        if (
            name == "Graphify/ActiveGraph proof claim"
            and OPTIONAL_TOOLING_PROOF_NONCLAIM_RE.search(text)
            and not OPTIONAL_TOOLING_POSITIVE_PROOF_RE.search(text)
        ):
            continue
        errors.append(f"{label}: forbidden {name}")
    return errors


def public_meta_text_errors(text: str, label: str) -> list[str]:
    return [f"{label}: forbidden {name}" for name, pattern in PUBLIC_META_PATTERNS if pattern.search(text)]


def required_surface_errors(text: str) -> list[str]:
    return [
        f"assembled output: missing {label}"
        for label, pattern in SURFACE_PATTERNS
        if pattern.search(text) is None
    ]


def final_public_tail_heading_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [
        ("restorative_response", "Restorative Response", public_heading_pattern("Restorative Response")),
        ("closing_formulation", "Closing Formulation", public_heading_pattern("Closing Formulation")),
        (
            "closure_witness",
            "Closure/Reconstruction Witness",
            re.compile(r"(?im)^\s*(?:#{1,6}\s*)?Closure\s*/\s*Reconstruction\s+Witness\s*$"),
        ),
        ("field_witness", "field_witness", FIELD_WITNESS_LABEL_RE),
    ]


def final_public_tail_errors(text: str, label: str) -> list[str]:
    errors: list[str] = []
    positions: list[tuple[int, str]] = []
    for role, display, pattern in final_public_tail_heading_patterns():
        matches = list(pattern.finditer(text))
        if len(matches) == 0:
            errors.append(f"{label}: missing singleton final public heading {display!r}")
            continue
        if len(matches) > 1:
            errors.append(f"{label}: duplicate singleton final public heading {display!r}")
        positions.append((matches[0].start(), role))
    if len(positions) == len(FINAL_PUBLIC_TAIL_ORDER):
        observed = [role for _index, role in sorted(positions)]
        if tuple(observed) != FINAL_PUBLIC_TAIL_ORDER:
            expected = " -> ".join(FINAL_PUBLIC_TAIL_LABELS[role] for role in FINAL_PUBLIC_TAIL_ORDER)
            found = " -> ".join(FINAL_PUBLIC_TAIL_LABELS[role] for role in observed)
            errors.append(f"{label}: final public tail order must be {expected}; found {found}")
    return errors


def public_heading_text(line: str) -> str:
    value = line.strip().lstrip("#").strip()
    return value.rstrip("#").strip()


def canonical_heading_pattern(heading: str) -> re.Pattern[str]:
    return public_heading_pattern(heading)


def json_object_span_after(text: str, start: int) -> tuple[int, int] | None:
    object_start = text.find("{", start)
    if object_start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(object_start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return object_start, index + 1
    return None


def field_witness_payload_ref(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    nested = payload.get("field_witness")
    if isinstance(nested, dict):
        return nested
    return payload


def activation_target(activation: Any) -> str:
    if not isinstance(activation, dict):
        return ""
    for key in ("target", "burden_id", "source", "land_target"):
        value = activation.get(key)
        if isinstance(value, str) and value.strip():
            match = re.search(r"\bB\d+\b", value, flags=re.IGNORECASE)
            return match.group(0).upper() if match else value.strip()
    return ""


def activation_owner(activation: Any) -> str:
    if not isinstance(activation, dict):
        return ""
    for key in ("owner", "owner_id"):
        value = activation.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def owner_ordering_family(owner: str) -> str:
    token = str(owner or "").strip()
    if "." in token:
        token = token.split(".", 1)[0]
    token = token.upper().replace("_", "-").replace(" ", "-")
    if not token:
        return ""
    if token in OWNER_ORDERING_FAMILY_ALIASES:
        return OWNER_ORDERING_FAMILY_ALIASES[token]
    if OWNER_ORDERING_CODE_RE.fullmatch(token):
        return token
    return token


def owner_ordering_token(owner: str) -> str:
    token = str(owner or "").strip()
    if "." in token:
        token = token.split(".", 1)[0]
    return token.upper().replace("_", "-").replace(" ", "-")


def derive_owner_activation_ordering(field_witness: dict[str, Any]) -> dict[str, Any] | None:
    activations = field_witness.get("owner_activations")
    if not isinstance(activations, list):
        return None

    by_target: dict[str, list[str]] = {}
    tokens_by_target: dict[str, set[str]] = {}
    for activation in activations:
        target = activation_target(activation)
        owner = activation_owner(activation)
        if not target or not owner:
            continue
        token = owner_ordering_token(owner)
        if not token:
            continue
        seen = tokens_by_target.setdefault(target, set())
        if token in seen:
            continue
        seen.add(token)
        owners = by_target.setdefault(target, [])
        owners.append(owner)

    required_before: list[dict[str, str]] = []
    for target, owners in sorted(by_target.items()):
        for before_owner, after_owner in zip(owners, owners[1:]):
            required_before.append(
                {
                    "target": target,
                    "before_owner": before_owner,
                    "after_owner": after_owner,
                }
            )

    if not required_before:
        return None
    return {
        "policy_id": OWNER_ORDERING_POLICY_ID,
        "parallel_groups": [],
        "required_before": required_before,
    }


def owner_ordering_rule_key(rule: dict[str, Any], *, family: bool = False) -> tuple[str, str, str]:
    target = activation_target({"target": rule.get("target")})
    before = str(rule.get("before_owner") or rule.get("before") or "")
    after = str(rule.get("after_owner") or rule.get("after") or "")
    if family:
        before_owner = owner_ordering_family(before) or owner_ordering_token(before)
        after_owner = owner_ordering_family(after) or owner_ordering_token(after)
    else:
        before_owner = owner_ordering_token(before)
        after_owner = owner_ordering_token(after)
    return target, before_owner, after_owner


def merge_owner_activation_ordering(field_witness: dict[str, Any]) -> dict[str, Any]:
    ordering = derive_owner_activation_ordering(field_witness)
    if ordering is None:
        return {}

    raw = field_witness.get("owner_activation_ordering")
    if not isinstance(raw, dict):
        field_witness["owner_activation_ordering"] = ordering
        return {
            "inserted_owner_activation_ordering": True,
            "required_before_count": len(ordering["required_before"]),
        }

    raw.setdefault("policy_id", OWNER_ORDERING_POLICY_ID)
    if not isinstance(raw.get("parallel_groups"), list):
        raw["parallel_groups"] = []
    required_before = raw.get("required_before")
    if not isinstance(required_before, list):
        required_before = []
        raw["required_before"] = required_before

    existing_token_keys = {
        owner_ordering_rule_key(rule)
        for rule in required_before
        if isinstance(rule, dict)
    }
    existing_family_keys = {
        owner_ordering_rule_key(rule, family=True)
        for rule in required_before
        if isinstance(rule, dict)
    }
    added = 0
    for rule in ordering["required_before"]:
        token_key = owner_ordering_rule_key(rule)
        family_key = owner_ordering_rule_key(rule, family=True)
        if token_key in existing_token_keys or family_key in existing_family_keys:
            continue
        required_before.append(rule)
        existing_token_keys.add(token_key)
        existing_family_keys.add(family_key)
        added += 1

    if not added:
        return {}
    return {
        "merged_owner_activation_ordering": True,
        "required_before_added_count": added,
    }


def canonical_ordering_role(value: Any) -> str:
    role = str(value or "required").strip().lower().replace("-", "_")
    if role not in ORDERING_ROLES:
        return "required"
    return role


def strip_trailing_line_whitespace(text: str) -> tuple[str, int]:
    normalized: list[str] = []
    changed = 0
    for line in text.splitlines(keepends=True):
        newline = ""
        body = line
        for suffix in ("\r\n", "\n", "\r"):
            if line.endswith(suffix):
                newline = suffix
                body = line[: -len(suffix)]
                break
        trimmed = body.rstrip(" \t")
        if trimmed != body:
            changed += 1
        normalized.append(trimmed + newline)
    return "".join(normalized), changed


def canonicalize_owner_activation_ordering_roles(field_witness: dict[str, Any]) -> int:
    activations = field_witness.get("owner_activations")
    if not isinstance(activations, list):
        return 0

    inserted = 0
    for activation in activations:
        if not isinstance(activation, dict):
            continue
        if activation.get("ordering_role") is not None:
            continue
        activation["ordering_role"] = canonical_ordering_role(activation.get("role"))
        inserted += 1
    return inserted


def canonicalize_formal_reread_curl_states(field_witness: dict[str, Any]) -> int:
    states = field_witness.get("formal_reread_states")
    if not isinstance(states, list):
        return 0

    normalized = 0
    for state in states:
        if not isinstance(state, dict):
            continue
        if state.get("curl_state") is None and "curl_state" in state:
            state["curl_state"] = "null"
            normalized += 1
    return normalized


def canonicalize_field_witness_per_burden_mirrors(
    field_witness: dict[str, Any],
    entry_by_burden: dict[str, dict[str, Any]] | None,
) -> int:
    if not entry_by_burden:
        return 0

    normalized = 0
    resultants = field_witness.get("mrp_resultants")
    if isinstance(resultants, list):
        for row in resultants:
            if not isinstance(row, dict):
                continue
            source = str(row.get("source") or "").strip()
            entry = entry_by_burden.get(source)
            if not entry:
                continue
            expected = {
                "type": str(entry.get("route_result_type") or ""),
                "finding": str(entry.get("finding") or ""),
                "graph": str(entry.get("graph_delta") or ""),
                "route": str(entry.get("route") or ""),
            }
            for key, value in expected.items():
                if value and row.get(key) != value:
                    row[key] = value
                    normalized += 1

    states = field_witness.get("formal_reread_states")
    if isinstance(states, list):
        for state in states:
            if not isinstance(state, dict):
                continue
            source = str(state.get("source_burden") or "").strip()
            entry = entry_by_burden.get(source)
            if not entry:
                continue
            expected = {
                "route_result_type": str(entry.get("route_result_type") or ""),
                "mrp_resultant": str(entry.get("mrp_resultant") or ""),
                "graph_delta": str(entry.get("graph_delta") or ""),
                "route": str(entry.get("route") or ""),
            }
            for key, value in expected.items():
                if value and state.get(key) != value:
                    state[key] = value
                    normalized += 1

    nar = field_witness.get("normalized_activation_record")
    rows = nar.get("per_burden") if isinstance(nar, dict) else None
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            burden = str(row.get("burden_id") or "").strip()
            entry = entry_by_burden.get(burden)
            if not entry:
                continue
            route_type = str(entry.get("route_result_type") or "")
            if route_type and row.get("mrp_route_result_type") != route_type:
                row["mrp_route_result_type"] = route_type
                normalized += 1
    return normalized


def canonicalize_field_witness_ordering(
    text: str,
    entry_by_burden: dict[str, dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any] | None]:
    label = FIELD_WITNESS_LABEL_RE.search(text)
    if label is None:
        return text, None
    span = json_object_span_after(text, label.end())
    if span is None:
        return text, None
    start, end = span
    try:
        payload = json.loads(text[start:end])
    except json.JSONDecodeError:
        return text, None
    field_witness = field_witness_payload_ref(payload)
    if field_witness is None:
        return text, None
    roles_inserted = canonicalize_owner_activation_ordering_roles(field_witness)
    null_curl_states = canonicalize_formal_reread_curl_states(field_witness)
    per_burden_mirrors = canonicalize_field_witness_per_burden_mirrors(
        field_witness,
        entry_by_burden,
    )
    event: dict[str, Any] = merge_owner_activation_ordering(field_witness)
    if roles_inserted:
        event["inserted_owner_activation_ordering_roles"] = roles_inserted
    if null_curl_states:
        event["normalized_formal_reread_null_curl_states"] = null_curl_states
    if per_burden_mirrors:
        event["normalized_per_burden_mirror_fields"] = per_burden_mirrors
    if not event:
        return text, None
    replacement = json.dumps(payload, indent=2, ensure_ascii=False)
    return text[:start] + replacement + text[end:], event


def public_burden_token(value: str) -> str:
    return f"{str(value).translate(ASCII_TO_SUP_DIGITS)}B"


def canonical_submove_ref(value: str) -> str:
    text = str(value or "").strip()
    match = re.fullmatch(r"B([1-9][0-9]*)[_\.]([1-9][0-9]*)", text)
    if match:
        return f"B{match.group(1)}_{match.group(2)}"
    match = re.fullmatch(r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B([₀₁₂₃₄₅₆₇₈₉]+)", text)
    if match:
        return f"B{match.group(1).translate(SUP_DIGITS)}_{match.group(2).translate(SUB_DIGITS)}"
    return text


def public_submove_token(value: str) -> str:
    canonical = canonical_submove_ref(value)
    match = re.fullmatch(r"B([1-9][0-9]*)_([1-9][0-9]*)", canonical)
    if not match:
        return value
    return f"{match.group(1).translate(ASCII_TO_SUP_DIGITS)}B{match.group(2).translate(ASCII_TO_SUB_DIGITS)}"


def canonicalize_public_submove_headings(text: str) -> tuple[str, dict[str, Any] | None]:
    seen: set[str] = set()
    canonicalized = 0
    demoted_duplicates = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal canonicalized, demoted_duplicates
        ref = match.group("ref")
        canonical_ref = canonical_submove_ref(ref)
        public_ref = public_submove_token(canonical_ref)
        if public_ref != ref:
            canonicalized += 1
        tail = match.group("tail")
        if canonical_ref in seen:
            demoted_duplicates += 1
            return f"{match.group('prefix')}Additional detail for {public_ref}{tail}"
        seen.add(canonical_ref)
        return f"{match.group('prefix')}{public_ref}{match.group('owner')}{tail}"

    updated = PUBLIC_SUBMOVE_HEADING_RE.sub(replace, text)
    if canonicalized == 0 and demoted_duplicates == 0:
        return text, None
    return updated, {
        "canonicalized_public_submove_headings": canonicalized,
        "demoted_duplicate_submove_headings": demoted_duplicates,
    }


def canonicalize_public_graph_alias_line(line: str) -> str:
    updated = line
    protected_machine_row = "body_ref=" in updated or "⟦ACT " in updated
    if not protected_machine_row and re.search(r"(?i)\b(?:no|not|without|absent)\b", updated):
        updated = re.sub(
            r"\bB([5-9][0-9]*)\b",
            lambda match: f"additional burden {match.group(1)}",
            updated,
        )
    updated = re.sub(r"\bR\(H,\s*Delta\)", "R(H,Δ)", updated)
    updated = re.sub(
        r"\bMRP\(\s*B([1-9][0-9]*)\s*\)",
        lambda match: f"MRP({public_burden_token(match.group(1))})",
        updated,
        flags=re.IGNORECASE,
    )
    updated = re.sub(
        r"\b(Land|HOLD)\(\s*B([1-9][0-9]*)\s*\)",
        lambda match: f"{match.group(1)}({public_burden_token(match.group(2))})",
        updated,
        flags=re.IGNORECASE,
    )
    updated = re.sub(
        r"(?i)(formal_reread_state)\(\s*B([1-9][0-9]*)\s*\)",
        lambda match: f"{match.group(1)}({public_burden_token(match.group(2))})",
        updated,
    )
    updated = re.sub(
        r"(?i)^(\s*(?:[-*]\s*)?Target\s*:\s*)B([1-9][0-9]*)\b",
        lambda match: f"{match.group(1)}MRP({public_burden_token(match.group(2))})",
        updated,
    )
    updated = re.sub(
        r"(?m)^(\s*(?:[-*]\s*)?)B([1-9][0-9]*)(?=\s*:)",
        lambda match: f"{match.group(1)}{public_burden_token(match.group(2))}",
        updated,
    )
    if PUBLIC_GRAPH_CONTEXT_RE.search(updated) and "body_ref=" not in updated:
        updated = re.sub(
            r"\bB([1-9][0-9]*)\b",
            lambda match: public_burden_token(match.group(1)),
            updated,
        )
    if "body_ref=" not in updated:
        updated = re.sub(
            r"(?<![A-Za-z0-9_Δ])B([1-9][0-9]*)\b(?![._])",
            lambda match: public_burden_token(match.group(1)),
            updated,
        )
    return updated


def canonicalize_public_graph_alias_scope(text: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    changed = 0
    updated_lines: list[str] = []
    for line in lines:
        updated = canonicalize_public_graph_alias_line(line)
        if updated != line:
            changed += 1
        updated_lines.append(updated)
    return "".join(updated_lines), changed


def canonicalize_public_graph_aliases(text: str) -> tuple[str, dict[str, Any] | None]:
    label = FIELD_WITNESS_LABEL_RE.search(text)
    span = json_object_span_after(text, label.end()) if label is not None else None
    if span is None:
        updated, changed = canonicalize_public_graph_alias_scope(text)
    else:
        start, end = span
        prefix, prefix_changed = canonicalize_public_graph_alias_scope(text[:start])
        suffix, suffix_changed = canonicalize_public_graph_alias_scope(text[end:])
        updated = prefix + text[start:end] + suffix
        changed = prefix_changed + suffix_changed
    if changed == 0:
        return text, None
    return updated, {
        "canonicalized_public_graph_aliases": True,
        "public_graph_alias_line_count": changed,
    }


def mark_canonical_scaffold_non_evidence(event: dict[str, Any]) -> dict[str, Any]:
    event.setdefault("proof_authority", "none")
    event.setdefault("proof_role", "non_evidence_canonicalization")
    event.setdefault("proof_claim", False)
    return event


def normalize_section_scaffold(
    section_id: str,
    role: str,
    text: str,
    *,
    entry_by_burden: dict[str, dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any] | None]:
    spec = CANONICAL_ROLE_HEADINGS.get(role)
    ordering_event: dict[str, Any] | None = None
    submove_event: dict[str, Any] | None = None
    if role == "field_witness_nar":
        text, ordering_event = canonicalize_field_witness_ordering(text, entry_by_burden)
    if role == "layer_b_act":
        text, submove_event = canonicalize_public_submove_headings(text)
    if spec is None:
        text, graph_event = canonicalize_public_graph_aliases(text)
        if ordering_event is None and graph_event is None and submove_event is None:
            return text, None
        event = {
            "section_id": section_id,
            "role": role,
        }
        if submove_event is not None:
            event.update(submove_event)
        if ordering_event is not None:
            event.update(ordering_event)
        if graph_event is not None:
            event.update(graph_event)
        return text, mark_canonical_scaffold_non_evidence(event)

    heading = str(spec["heading"])
    variant_patterns = list(spec["variants"])
    embedded_variant = embedded_decorated_public_heading_pattern(heading)
    lines = text.splitlines(keepends=True)
    model_variants: list[str] = []

    for line in lines:
        public_text = public_heading_text(line)
        is_public_heading = canonical_heading_pattern(heading).fullmatch(line.strip()) is not None
        is_model_variant = any(pattern.fullmatch(public_text) for pattern in variant_patterns)
        if embedded_variant.search(line) and not is_public_heading and not is_model_variant:
            raise AssemblyError(f"{section_id}: embedded decorated {heading} heading is not a public heading")

    first_content_index = next((index for index, line in enumerate(lines) if line.strip()), None)
    if first_content_index is not None:
        first_heading = public_heading_text(lines[first_content_index])
        if any(pattern.fullmatch(first_heading) for pattern in variant_patterns):
            model_variants.append(first_heading)
            del lines[first_content_index]
            text = "".join(lines).lstrip("\ufeff")

    inserted_headings: list[str] = []
    insert_if_missing = bool(spec.get("insert_if_missing", False))
    if role == "field_witness_nar" and not model_variants and FIELD_WITNESS_LABEL_RE.search(text) is None:
        return text, None
    if canonical_heading_pattern(heading).search(text) is None:
        if not insert_if_missing and not model_variants:
            return text, None
        text = f"{heading}\n{text.lstrip()}"
        inserted_headings.append(heading)
    text, graph_event = canonicalize_public_graph_aliases(text)

    if not inserted_headings and not model_variants and ordering_event is None and graph_event is None and submove_event is None:
        return text, None
    event = {
        "section_id": section_id,
        "role": role,
        "inserted_headings": inserted_headings,
        "model_heading_variants_seen": model_variants,
    }
    if ordering_event is not None:
        event.update(ordering_event)
    if graph_event is not None:
        event.update(graph_event)
    if submove_event is not None:
        event.update(submove_event)
    return text, mark_canonical_scaffold_non_evidence(event)


def parse_output_targets(output: Any) -> tuple[int, int, list[str]]:
    if not isinstance(output, dict):
        return 0, 0, []
    errors: list[str] = []
    target_output_kb = output.get("target_output_kb", 0)
    target_min_bytes = output.get("target_min_bytes", 0)
    if target_output_kb in (None, ""):
        target_output_kb = 0
    if target_min_bytes in (None, ""):
        target_min_bytes = 0
    if not isinstance(target_output_kb, int) or target_output_kb < 0:
        errors.append("output.target_output_kb: must be a non-negative integer")
        target_output_kb = 0
    if not isinstance(target_min_bytes, int) or target_min_bytes < 0:
        errors.append("output.target_min_bytes: must be a non-negative integer")
        target_min_bytes = 0
    min_bytes = max(target_min_bytes, target_output_kb * 1024)
    return target_output_kb, min_bytes, errors


def section_budget_errors(
    section_budgets: Any,
    *,
    section_records: list[dict[str, Any]],
    allow_under_target: bool = False,
) -> tuple[list[str], dict[str, Any] | None]:
    if section_budgets is None:
        return [], None
    if not isinstance(section_budgets, dict):
        return ["section_budgets: must be an object"], None

    errors: list[str] = []
    if section_budgets.get("schema") != SECTION_BUDGET_SCHEMA:
        errors.append(f"section_budgets.schema: must be {SECTION_BUDGET_SCHEMA!r}")

    target_output_bytes = section_budgets.get("target_output_bytes", 0)
    if not isinstance(target_output_bytes, int) or target_output_bytes < 0:
        errors.append("section_budgets.target_output_bytes: must be a non-negative integer")

    role_min_bytes = section_budgets.get("role_min_bytes", {})
    if role_min_bytes is not None and not isinstance(role_min_bytes, dict):
        errors.append("section_budgets.role_min_bytes: must be an object when present")
    elif isinstance(role_min_bytes, dict):
        for role, value in role_min_bytes.items():
            if role not in ROLE_INDEX:
                errors.append(f"section_budgets.role_min_bytes.{role}: unsupported role")
            if not isinstance(value, int) or value < 0:
                errors.append(f"section_budgets.role_min_bytes.{role}: must be a non-negative integer")

    min_section_bytes = section_budgets.get("min_section_bytes", {})
    if not isinstance(min_section_bytes, dict):
        errors.append("section_budgets.min_section_bytes: must be an object")
        min_section_bytes = {}

    record_by_id = {str(record["id"]): record for record in section_records}
    for section_id, value in min_section_bytes.items():
        if section_id not in record_by_id:
            errors.append(f"section_budgets.min_section_bytes.{section_id}: unknown section id")
            continue
        if not isinstance(value, int) or value < 0:
            errors.append(f"section_budgets.min_section_bytes.{section_id}: must be a non-negative integer")
            continue
        assembled_bytes = int(record_by_id[section_id].get("assembled_bytes", record_by_id[section_id]["bytes"]))
        if value and assembled_bytes < value and not allow_under_target:
            errors.append(
                f"sections[{section_id}]: under section budget ({assembled_bytes} bytes < {value} bytes)"
            )

    if errors:
        return errors, None
    return [], {
        "schema": SECTION_BUDGET_SCHEMA,
        "target_output_bytes": target_output_bytes,
        "role_min_bytes": dict(role_min_bytes or {}),
        "min_section_bytes": dict(min_section_bytes),
    }


def validate_section_expansions(
    section_expansions: Any,
    *,
    root: Path,
    manifest_dir: Path,
    section_role_by_id: dict[str, str],
) -> tuple[list[str], dict[str, Any] | None]:
    if section_expansions is None:
        return [], None
    if not isinstance(section_expansions, dict):
        return ["section_expansions: must be an object"], None

    errors: list[str] = []
    if section_expansions.get("schema") != SECTION_EXPANSIONS_SCHEMA:
        errors.append(f"section_expansions.schema: must be {SECTION_EXPANSIONS_SCHEMA!r}")
    rounds_allowed = section_expansions.get("rounds_allowed", 0)
    if not isinstance(rounds_allowed, int) or rounds_allowed < 0:
        errors.append("section_expansions.rounds_allowed: must be a non-negative integer")

    records = section_expansions.get("records", [])
    if not isinstance(records, list):
        errors.append("section_expansions.records: must be a list")
        records = []

    normalized_records: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        label = f"section_expansions.records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label}: must be an object")
            continue
        section_id = record.get("section_id")
        role = record.get("role")
        round_index = record.get("round")
        path_value = record.get("path")
        expected_hash = record.get("sha256")
        if not isinstance(section_id, str) or section_id not in section_role_by_id:
            errors.append(f"{label}.section_id: unknown section id")
        if not isinstance(role, str) or (isinstance(section_id, str) and section_role_by_id.get(section_id) != role):
            errors.append(f"{label}.role: must match the section role")
        if not isinstance(round_index, int) or round_index < 1:
            errors.append(f"{label}.round: must be a positive integer")
        if not isinstance(expected_hash, str) or SHA256_RE.fullmatch(expected_hash) is None:
            errors.append(f"{label}.sha256: must be a SHA256 hex string")
        try:
            expansion_path = resolve_section_path(root, manifest_dir, path_value, f"{label}.path")
        except AssemblyError as exc:
            errors.append(str(exc))
            continue
        actual_hash = sha256_file(expansion_path)
        if isinstance(expected_hash, str) and expected_hash.upper() != actual_hash:
            errors.append(f"{label}.sha256: expected {expected_hash.upper()} but found {actual_hash}")
        normalized_records.append(
            {
                "section_id": section_id,
                "role": role,
                "round": round_index,
                "path": rel(expansion_path, root),
                "sha256": actual_hash,
                "bytes": expansion_path.stat().st_size,
            }
        )

    if errors:
        return errors, None
    return [], {
        "schema": SECTION_EXPANSIONS_SCHEMA,
        "rounds_allowed": rounds_allowed,
        "records": normalized_records,
    }


def validate_non_claims(non_claims: Any) -> list[str]:
    if not isinstance(non_claims, dict):
        return ["non_claims: must be an object"]
    return [
        f"non_claims.{key}: must be true"
        for key in sorted(REQUIRED_NON_CLAIMS)
        if non_claims.get(key) is not True
    ]


def clean_body_ref(value: str) -> str:
    return value.strip().rstrip(".,;")


def body_ref_burden_id(value: str) -> str:
    ref = clean_body_ref(str(value or ""))
    match = BODY_REF_BURDEN_RE.fullmatch(ref)
    if match:
        burden = match.group("burden")
        if re.fullmatch(r"B[1-9][0-9]*", burden):
            return burden
        if re.fullmatch(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+B", burden):
            return f"B{burden[:-1].translate(SUP_DIGITS)}"
    match = ASCII_BODY_REF_RE.fullmatch(ref)
    if match:
        return f"B{match.group('burden')}"
    return ""


def body_ref_grouping_errors(refs: list[str], label: str) -> list[str]:
    errors: list[str] = []
    groups: list[str] = []
    for ref in refs:
        burden_id = body_ref_burden_id(ref)
        if not burden_id:
            continue
        if not groups or groups[-1] != burden_id:
            groups.append(burden_id)
    seen: set[str] = set()
    previous_number = 0
    for burden_id in groups:
        if burden_id in seen:
            errors.append(f"{label}: burden {burden_id} body_ref assignments are not contiguous")
        seen.add(burden_id)
        number = int(burden_id[1:])
        if number < previous_number:
            errors.append(f"{label}: burden {burden_id} appears after a later burden group")
        previous_number = max(previous_number, number)
    return errors


def body_refs_in_act_section(text: str) -> list[str]:
    refs: list[str] = []
    for match in BODY_REF_TOKEN_RE.finditer(text):
        ref = clean_body_ref(match.group(1))
        if ref:
            refs.append(ref)
    return refs


PER_BURDEN_REREAD_FIELD = "per_burden_reread"
PER_BURDEN_PRESSURE_KEY_ORDER = (
    "freeze-landed-move",
    "dependency-tug",
    "hidden-framework-recoil",
    "entailment-pressure",
    "doubt-churn-guard",
    "reorientation-reminder",
)
PER_BURDEN_PRESSURE_KEYS = frozenset(PER_BURDEN_PRESSURE_KEY_ORDER)
PER_BURDEN_FINDINGS = {
    "stable",
    "genuine-dependent",
    "partial-real",
    "hidden-framework-recoil",
    "doubt-churn",
    "reorientation",
}
PER_BURDEN_ROUTE_RESULT_TYPES = {
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "loopbreak",
    "hold_partial",
}
PER_BURDEN_ROUTES = {"STOP", "HOLD", "RECURSE", "LoopBreak(∇×T)"}
PER_BURDEN_PREEMPTION_BASES = {"none", "graph-bound", "commitment-bound", "framework-bound"}
PER_BURDEN_BOUNDARY_PREFIX = "T_lang does not imply guaranteed uptake"
PER_BURDEN_DIVERGENCE_HEADS = {"neutral", "settled", "bounded", "non-neutral"}
PER_BURDEN_CURL_HEADS = {"null", "resolved", "held", "non-null"}
PER_BURDEN_REQUIRED_STRING_FIELDS = (
    "burden_id",
    "target",
    "reread",
    "landed_delta",
    "route_gradient",
    "divergence",
    "curl",
    "finding",
    "route_result_type",
    "mrp_resultant",
    "graph_delta",
    "preemption_basis",
    "route",
    "boundary",
)
PER_BURDEN_OPTIONAL_STRING_FIELDS = ("loopbreak", "matched_route")
PER_BURDEN_ALLOWED_FIELDS = frozenset(PER_BURDEN_REQUIRED_STRING_FIELDS) | frozenset(
    PER_BURDEN_OPTIONAL_STRING_FIELDS
) | {"pressure_activations"}
PER_BURDEN_FORBIDDEN_SLOT_VALUES = {"none", "cleared", "n/a", "na", "-"}
PER_BURDEN_SLOT_START_RE = re.compile(
    r"^(?:pressure class:|coverage gap:|FPD\b|M1P\b|M\d+\b|V\d+\b|R\d+\b|P\d+\b|LoopBreak\b|"
    r"field_witness\b|[A-Za-z0-9]+-[A-Za-z0-9-]+\b)"
)
PER_BURDEN_BURDEN_ID_RE = re.compile(r"^B[1-9][0-9]*$")
PER_BURDEN_GRAPH_EDGE_RE = re.compile(r"^B[1-9][0-9]* -> B[1-9][0-9]*$")
PER_BURDEN_DIVERGENCE_PREFIX_RE = re.compile(r"^(?:∇\s*·\s*B|del[- ]dot\s*B)\s*:\s*", re.IGNORECASE)
PER_BURDEN_CURL_PREFIX_RE = re.compile(r"^(?:∇\s*×\s*(?:κ|kappa)|del[- ]cross\s*(?:κ|kappa))\s*:\s*", re.IGNORECASE)
MRP_HEADING_TEXT = "[Mid-Reread Pressure]"
# Mirrors tools/check_mid_reread_pressure.py MRP_HEADING_RE so the producer
# forbids exactly what the checker would recognize as a block heading.
MRP_HEADING_LINE_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:[-*]\s*)?(?:\*\*)?\[Mid-Reread Pressure\](?:\*\*)?\s*$"
)
# Mirrors tools/check_mid_reread_pressure.py LAND_GATE_RE: superscript-only and
# line-start so ASCII Land(B1) machine rows never count as public landing gates.
LAND_GATE_LINE_RE = re.compile(r"(?m)^Land\((?P<burden>[¹²³⁴⁵⁶⁷⁸⁹]B)\):")


def per_burden_diag_body(value: str, prefix_re: re.Pattern[str]) -> str:
    return prefix_re.sub("", str(value or "").strip(), count=1).strip()


def per_burden_diag_errors(label: str, value: str, prefix_re: re.Pattern[str], heads: set[str]) -> list[str]:
    body = per_burden_diag_body(value, prefix_re)
    errors: list[str] = []
    if ";" in body or "\n" in body:
        errors.append(f"{label} must be a single-line value without ';'")
        return errors
    head, separator, reason = body.partition("/")
    if head.strip() not in heads:
        errors.append(f"{label} head must be one of {sorted(heads)}")
    if not separator or not reason.strip():
        errors.append(f"{label} must carry '<head> / <reason>'")
    return errors


def per_burden_reread_entry_errors(
    entries: Any,
    *,
    label: str = PER_BURDEN_REREAD_FIELD,
    terminal_state_ids: set[str] | None = None,
) -> list[str]:
    """Shared producer-side validator for stage-05 per_burden_reread entries.

    One entry per terminal burden; entries are the only licensed source for the
    visible [Mid-Reread Pressure] blocks. Stage07 must not fill, infer, or
    repair missing fields, so this validator fails early and lists every
    problem instead of letting downstream rendering guess.
    """
    if not isinstance(entries, list) or not entries:
        return [f"{label}: must be a non-empty list of per-burden reread records"]
    errors: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        entry_label = f"{label}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{entry_label}: must be an object")
            continue
        unknown = sorted(set(entry) - PER_BURDEN_ALLOWED_FIELDS)
        if unknown:
            errors.append(f"{entry_label}: unknown field(s) {unknown}; allowed fields are {sorted(PER_BURDEN_ALLOWED_FIELDS)}")
        for field_name in PER_BURDEN_REQUIRED_STRING_FIELDS:
            value = entry.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{entry_label}.{field_name}: must be a non-empty string")
            elif "\n" in value:
                errors.append(f"{entry_label}.{field_name}: must be a single-line value")
            else:
                errors.extend(forbidden_text_errors(value, f"{entry_label}.{field_name}"))
        for field_name in PER_BURDEN_OPTIONAL_STRING_FIELDS:
            if field_name in entry:
                value = entry.get(field_name)
                if not isinstance(value, str) or not value.strip() or "\n" in value:
                    errors.append(f"{entry_label}.{field_name}: must be a non-empty single-line string when present")
                else:
                    errors.extend(forbidden_text_errors(value, f"{entry_label}.{field_name}"))
        burden_id = entry.get("burden_id")
        if isinstance(burden_id, str) and burden_id:
            if not PER_BURDEN_BURDEN_ID_RE.match(burden_id):
                errors.append(f"{entry_label}.burden_id: must be machine form B<n>")
            if burden_id in seen:
                errors.append(f"{entry_label}.burden_id: duplicates {burden_id}")
            seen.add(burden_id)
        target = entry.get("target")
        if isinstance(target, str) and target and "B" not in target:
            errors.append(f"{entry_label}.target: must name a burden")
        reread = entry.get("reread")
        if isinstance(reread, str) and reread:
            if not reread.startswith("R(H,"):
                errors.append(f"{entry_label}.reread: must start with the R(H,Δ) reread invocation")
            for marker in ("held routes rechecked", "live remainder:", "release/next:"):
                if marker not in reread:
                    errors.append(f"{entry_label}.reread: must record '{marker}'")
        landed_delta = entry.get("landed_delta")
        if isinstance(landed_delta, str) and landed_delta and "Δ" not in landed_delta and "Delta" not in landed_delta:
            errors.append(f"{entry_label}.landed_delta: must name Δ/Delta")
        if entry.get("finding") not in PER_BURDEN_FINDINGS:
            errors.append(f"{entry_label}.finding: must be a controlled finding token")
        if entry.get("route_result_type") not in PER_BURDEN_ROUTE_RESULT_TYPES:
            errors.append(f"{entry_label}.route_result_type: must be a controlled MRP route result type")
        if entry.get("route") not in PER_BURDEN_ROUTES:
            errors.append(f"{entry_label}.route: must be STOP, HOLD, RECURSE, or LoopBreak(∇×T)")
        if entry.get("preemption_basis") not in PER_BURDEN_PREEMPTION_BASES:
            errors.append(f"{entry_label}.preemption_basis: must be none, graph-bound, commitment-bound, or framework-bound")
        boundary = entry.get("boundary")
        if isinstance(boundary, str) and boundary and not boundary.startswith(PER_BURDEN_BOUNDARY_PREFIX):
            errors.append(f"{entry_label}.boundary: must begin with the T_lang non-uptake boundary")
        divergence = entry.get("divergence")
        if isinstance(divergence, str) and divergence:
            errors.extend(
                per_burden_diag_errors(
                    f"{entry_label}.divergence", divergence, PER_BURDEN_DIVERGENCE_PREFIX_RE, PER_BURDEN_DIVERGENCE_HEADS
                )
            )
        curl = entry.get("curl")
        if isinstance(curl, str) and curl:
            errors.extend(
                per_burden_diag_errors(f"{entry_label}.curl", curl, PER_BURDEN_CURL_PREFIX_RE, PER_BURDEN_CURL_HEADS)
            )
        graph_delta = entry.get("graph_delta")
        has_edge = False
        if isinstance(graph_delta, str) and graph_delta:
            if PER_BURDEN_GRAPH_EDGE_RE.match(graph_delta):
                has_edge = True
            elif graph_delta != "none":
                errors.append(f"{entry_label}.graph_delta: must be 'none' or one ASCII edge 'Bn -> Bm'")
        activations = entry.get("pressure_activations")
        if not isinstance(activations, dict):
            errors.append(f"{entry_label}.pressure_activations: must be an object carrying the six fixed slots")
        else:
            missing = sorted(PER_BURDEN_PRESSURE_KEYS - set(activations))
            extra = sorted(set(activations) - PER_BURDEN_PRESSURE_KEYS)
            if missing:
                errors.append(f"{entry_label}.pressure_activations: missing slot(s) {missing}")
            if extra:
                errors.append(f"{entry_label}.pressure_activations: unknown slot(s) {extra}")
            for key in sorted(set(activations) & PER_BURDEN_PRESSURE_KEYS):
                value = activations.get(key)
                if not isinstance(value, str) or not value.strip() or "\n" in value:
                    errors.append(f"{entry_label}.pressure_activations.{key}: must be a non-empty single-line string")
                    continue
                if value.strip().rstrip(".").lower() in PER_BURDEN_FORBIDDEN_SLOT_VALUES:
                    errors.append(
                        f"{entry_label}.pressure_activations.{key}: placeholder value forbidden; record the real owner/TTP, pressure class, or coverage gap read"
                    )
                elif not PER_BURDEN_SLOT_START_RE.match(value.strip()):
                    errors.append(
                        f"{entry_label}.pressure_activations.{key}: must begin with an owner/TTP id, 'pressure class:', or 'coverage gap:'"
                    )
                errors.extend(forbidden_text_errors(value, f"{entry_label}.pressure_activations.{key}"))
        # Fail-early consistency rules mirroring tools/check_mid_reread_pressure.py.
        finding = entry.get("finding")
        route = entry.get("route")
        if finding == "stable" and (route != "STOP" or graph_delta != "none"):
            errors.append(f"{entry_label}: stable finding requires route STOP and graph_delta none")
        if finding == "genuine-dependent" and (route != "RECURSE" or not has_edge):
            errors.append(f"{entry_label}: genuine-dependent finding requires route RECURSE and a graph edge")
        if finding == "partial-real" and route != "HOLD":
            errors.append(f"{entry_label}: partial-real finding requires route HOLD")
        if has_edge and entry.get("preemption_basis") == "none":
            errors.append(f"{entry_label}: graph-edge pre-emption requires graph/commitment/framework-bound basis")
    if terminal_state_ids is not None and not errors:
        missing_entries = sorted(terminal_state_ids - seen)
        extra_entries = sorted(seen - terminal_state_ids)
        if missing_entries:
            errors.append(f"{label}: missing entry for terminal burden(s) {missing_entries}")
        if extra_entries:
            errors.append(f"{label}: entry burden(s) {extra_entries} not present in terminal_states")
    return errors


def public_per_burden_graph_value(value: str) -> str:
    rendered = re.sub(
        r"\bB([1-9][0-9]*)\b",
        lambda match: public_burden_token(match.group(1)),
        str(value or ""),
    )
    return rendered.replace("->", "→")


def public_per_burden_mrp_resultant_value(value: str) -> str:
    rendered = re.sub(
        r"\bB([1-9][0-9]*)\s*(?:->|→)\s*B([1-9][0-9]*)\b",
        lambda match: f"{public_burden_token(match.group(1))} → {public_burden_token(match.group(2))}",
        str(value or ""),
    )
    return public_per_burden_text_value(rendered)


def public_per_burden_text_value(value: str) -> str:
    text = str(value or "")
    protected_delta_identities: list[str] = []

    def protect_delta_identity(match: re.Match[str]) -> str:
        protected_delta_identities.append(match.group(0))
        return f"@@DAEE_DELTA_IDENTITY_{len(protected_delta_identities) - 1}@@"

    text = re.sub(r"(?i)Delta\(\s*B[1-9][0-9]*\s*\)", protect_delta_identity, text)
    text = re.sub(
        r"(?i)\bB[knm]\s*(?:->|→)\s*B[knm](?:\s+edge)?\b",
        "burden-to-burden edge",
        text,
    )
    text = re.sub(
        r"ΔB([1-9][0-9]*)\b",
        lambda match: f"Δ{public_burden_token(match.group(1))}",
        text,
    )
    text = re.sub(
        r"\b(MRP|Land|HOLD)\(\s*B([1-9][0-9]*)\s*\)",
        lambda match: f"{match.group(1)}({public_burden_token(match.group(2))})",
        text,
    )
    text = re.sub(
        r"\bB([1-9][0-9]*)\s*-\s*B([1-9][0-9]*)\b",
        lambda match: f"{public_burden_token(match.group(1))}-{public_burden_token(match.group(2))}",
        text,
    )
    text = re.sub(
        r"\bB([1-9][0-9]*)\b",
        lambda match: public_burden_token(match.group(1)),
        text,
    )
    for index, original in enumerate(protected_delta_identities):
        text = text.replace(f"@@DAEE_DELTA_IDENTITY_{index}@@", original)
    return text


def render_mrp_block(entry: dict[str, Any]) -> str:
    """Render one checker-canonical [Mid-Reread Pressure] block from one record.

    The line shape mirrors tools/check_mid_reread_pressure.py field parsing.
    Every visible value comes from the validated per_burden_reread entry; the
    renderer adds no content beyond the canonical field labels.
    """
    activations = entry.get("pressure_activations") or {}
    lines = [
        MRP_HEADING_TEXT,
        f"Target: {public_per_burden_text_value(entry['target'])}",
        public_per_burden_text_value(str(entry["reread"])),
        f"Landed delta: {public_per_burden_text_value(entry['landed_delta'])}",
        "Pressure activations:",
    ]
    lines.extend(
        f"- {key}: {public_per_burden_text_value(activations[key])}"
        for key in PER_BURDEN_PRESSURE_KEY_ORDER
    )
    matched_route = str(entry.get("matched_route") or "").strip()
    if matched_route:
        matched_route = public_per_burden_text_value(matched_route)
        if re.match(r"(?i)^\s*Matched owner/TTP route\s*:", matched_route):
            lines.append(matched_route)
        else:
            lines.append(f"Matched owner/TTP route: {matched_route}")
    divergence = per_burden_diag_body(entry["divergence"], PER_BURDEN_DIVERGENCE_PREFIX_RE)
    curl = per_burden_diag_body(entry["curl"], PER_BURDEN_CURL_PREFIX_RE)
    lines.extend(
        [
            f"Field diagnostics: ∇·B: {public_per_burden_text_value(divergence)}; ∇×κ: {public_per_burden_text_value(curl)}",
            f"Route-gradient: {public_per_burden_text_value(entry['route_gradient'])}",
            f"Finding: {entry['finding']}",
            f"MRP route result type: {entry['route_result_type']}",
            f"MRP resultant: {public_per_burden_mrp_resultant_value(entry['mrp_resultant'])}",
            f"Graph delta: {public_per_burden_graph_value(entry['graph_delta'])}",
            f"Pre-emption basis: {public_per_burden_text_value(entry['preemption_basis'])}",
            f"LoopBreak: {public_per_burden_text_value(entry.get('loopbreak') or 'not needed')}",
            f"Route: {entry['route']}",
            f"Boundary: {public_per_burden_text_value(entry['boundary'])}",
        ]
    )
    return "\n".join(lines)


def inject_per_burden_mrp_blocks(
    text: str,
    entry_by_burden: dict[str, dict[str, Any]],
    label: str,
) -> tuple[str, list[str], list[str]]:
    """Inject one canonical MRP block after each superscript Land(ⁿB): gate line.

    Returns (new_text, gated_burden_ids_in_order, errors). Gates without a
    per_burden_reread record are hard errors; Stage07 never invents block
    content from terminal states, resultants, or prose.
    """
    errors: list[str] = []
    gates: list[str] = []
    out_lines: list[str] = []
    for line in text.splitlines():
        out_lines.append(line)
        match = LAND_GATE_LINE_RE.match(line)
        if not match:
            continue
        public_burden = match.group("burden")
        burden_id = f"B{public_burden[:-1].translate(SUP_DIGITS)}"
        gates.append(burden_id)
        entry = entry_by_burden.get(burden_id)
        if entry is None:
            errors.append(
                f"{label}: Land({public_burden}): gate has no {PER_BURDEN_REREAD_FIELD} record for {burden_id}"
            )
            continue
        out_lines.append("")
        out_lines.extend(render_mrp_block(entry).splitlines())
        out_lines.append("")
    new_text = "\n".join(out_lines)
    if text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, gates, errors


def land_gate_burdens(text: str) -> list[str]:
    return [
        f"B{match.group('burden')[:-1].translate(SUP_DIGITS)}"
        for match in LAND_GATE_LINE_RE.finditer(text)
    ]


PER_BURDEN_REREAD_NORMALIZE_RE = re.compile(
    r"R\(H,\s*Delta(?:(?:B[1-9][0-9]*)|\(B[1-9][0-9]*\)|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)?\)"
)


def per_burden_block_field_parity_errors(label: str, block: Any, entry: dict[str, Any]) -> list[str]:
    """Compare one parsed visible [Mid-Reread Pressure] block to one record.

    Visible values must equal the per_burden_reread record verbatim (graph
    delta compared through the canonical public rendering; R(H,Delta) spelling
    normalized to R(H,Δ)). A valid-shaped block that diverges from the hidden
    record is a parity failure, never a pass.
    """
    errors: list[str] = []

    def expected(field_name: str) -> str:
        return str(entry.get(field_name) or "")

    def mismatch(display: str, visible: Any, wanted: str) -> None:
        errors.append(
            f"{label} {display} diverges from per_burden_reread: visible {str(visible)!r} != record {wanted!r}"
        )

    def normalize_reread(value: Any) -> str:
        return PER_BURDEN_REREAD_NORMALIZE_RE.sub("R(H,Δ)", str(value or "").strip())

    if block.target != public_per_burden_text_value(expected("target")):
        mismatch("Target", block.target, public_per_burden_text_value(expected("target")))
    if normalize_reread(block.reread) != normalize_reread(public_per_burden_text_value(expected("reread"))):
        mismatch("R(H,Δ) reread", block.reread, public_per_burden_text_value(expected("reread")))
    if block.landed_delta != public_per_burden_text_value(expected("landed_delta")):
        mismatch("Landed delta", block.landed_delta, public_per_burden_text_value(expected("landed_delta")))
    activations = entry.get("pressure_activations") or {}
    for key in PER_BURDEN_PRESSURE_KEY_ORDER:
        wanted = public_per_burden_text_value(str(activations.get(key) or ""))
        visible = block.pressure_lines.get(key)
        if visible is None:
            errors.append(f"{label} pressure slot {key} is missing from the visible block")
        elif visible != wanted:
            mismatch(f"pressure slot {key}", visible, wanted)
    expected_divergence = public_per_burden_text_value(
        per_burden_diag_body(expected("divergence"), PER_BURDEN_DIVERGENCE_PREFIX_RE)
    )
    expected_curl = public_per_burden_text_value(
        per_burden_diag_body(expected("curl"), PER_BURDEN_CURL_PREFIX_RE)
    )
    if str(block.divergence or "").strip() != expected_divergence:
        mismatch("field diagnostics ∇·B", block.divergence, expected_divergence)
    if str(block.curl or "").strip() != expected_curl:
        mismatch("field diagnostics ∇×κ", block.curl, expected_curl)
    if block.route_gradient != public_per_burden_text_value(expected("route_gradient")):
        mismatch("Route-gradient", block.route_gradient, public_per_burden_text_value(expected("route_gradient")))
    if block.finding != expected("finding"):
        mismatch("Finding", block.finding, expected("finding"))
    if block.route_result_type != expected("route_result_type"):
        mismatch("MRP route result type", block.route_result_type, expected("route_result_type"))
    expected_mrp_resultant = public_per_burden_mrp_resultant_value(expected("mrp_resultant"))
    if block.mrp_resultant != expected_mrp_resultant:
        mismatch("MRP resultant", block.mrp_resultant, expected_mrp_resultant)
    expected_graph = public_per_burden_graph_value(expected("graph_delta"))
    if block.graph_delta != expected_graph:
        mismatch("Graph delta", block.graph_delta, expected_graph)
    if block.preemption_basis != public_per_burden_text_value(expected("preemption_basis")):
        mismatch(
            "Pre-emption basis",
            block.preemption_basis,
            public_per_burden_text_value(expected("preemption_basis")),
        )
    if block.route != expected("route"):
        mismatch("Route", block.route, expected("route"))
    if block.boundary != public_per_burden_text_value(expected("boundary")):
        mismatch("Boundary", block.boundary, public_per_burden_text_value(expected("boundary")))
    return errors


def visible_block_parity_errors(
    output_text: str,
    per_burden_reread: Any,
    *,
    label: str = "mrp record-surface parity",
) -> list[str]:
    """Require every visible [Mid-Reread Pressure] block to mirror its record.

    This is the single-source record↔surface tooth: one block per line-start
    superscript Land(ⁿB): landing window, every block field equal to the
    stage-05 per_burden_reread record for that burden, and no unmatched
    blocks, records, or gates in either direction. Block parsing reuses
    tools/check_mid_reread_pressure.py so parse semantics cannot fork.
    """
    import check_mid_reread_pressure as mrp_checker

    if (
        not isinstance(per_burden_reread, list)
        or not per_burden_reread
        or not all(isinstance(entry, dict) for entry in per_burden_reread)
    ):
        return [f"{label}: stage-05 per_burden_reread records are required for record-surface parity"]
    errors: list[str] = []
    entry_by_burden: dict[str, dict[str, Any]] = {}
    for entry in per_burden_reread:
        burden_id = str(entry.get("burden_id") or "")
        if not burden_id:
            errors.append(f"{label}: per_burden_reread entry without burden_id")
            continue
        if burden_id in entry_by_burden:
            errors.append(f"{label}: duplicate per_burden_reread entry for {burden_id}")
        entry_by_burden[burden_id] = entry

    gates = list(LAND_GATE_LINE_RE.finditer(output_text))
    gate_burdens = [
        f"B{match.group('burden')[:-1].translate(SUP_DIGITS)}" for match in gates
    ]
    duplicate_gates = sorted({burden for burden in gate_burdens if gate_burdens.count(burden) > 1})
    if duplicate_gates:
        errors.append(f"{label}: duplicate Land(ⁿB): landing gate(s) for {duplicate_gates}")
    gateless_records = sorted(set(entry_by_burden) - set(gate_burdens))
    if gateless_records:
        errors.append(
            f"{label}: per_burden_reread record(s) {gateless_records} have no visible Land(ⁿB): landing gate"
        )
    recordless_gates = sorted({burden for burden in gate_burdens if burden not in entry_by_burden})
    if recordless_gates:
        errors.append(
            f"{label}: Land(ⁿB): landing gate(s) {recordless_gates} have no per_burden_reread record"
        )

    headings = [
        match.start()
        for match in re.finditer(mrp_checker.MRP_HEADING_RE, output_text, re.MULTILINE)
    ]
    blocks = mrp_checker.parse_mrps(output_text)
    if len(blocks) != len(headings):
        errors.append(
            f"{label}: parsed {len(blocks)} block body(ies) for {len(headings)} visible heading(s)"
        )
        return errors
    heading_blocks = list(zip(headings, blocks))
    first_gate_start = gates[0].start() if gates else len(output_text)
    stray_blocks = [position for position in headings if position < first_gate_start]
    if stray_blocks:
        errors.append(
            f"{label}: {len(stray_blocks)} visible [Mid-Reread Pressure] block(s) appear before any "
            "Land(ⁿB): landing gate and match no record"
        )
    for index, gate in enumerate(gates):
        window_end = gates[index + 1].start() if index + 1 < len(gates) else len(output_text)
        in_window = [
            (position, block)
            for position, block in heading_blocks
            if gate.end() <= position < window_end
        ]
        burden_id = gate_burdens[index]
        gate_label = f"{label}: Land({gate.group('burden')}):"
        if not in_window:
            errors.append(
                f"{gate_label} no visible [Mid-Reread Pressure] block mirrors the {burden_id} record"
            )
            continue
        if len(in_window) > 1:
            errors.append(
                f"{gate_label} {len(in_window)} visible blocks in one landing window; exactly one is licensed"
            )
        entry = entry_by_burden.get(burden_id)
        if entry is None:
            continue
        errors.extend(per_burden_block_field_parity_errors(gate_label, in_window[0][1], entry))
    return errors


def act_partition_errors(
    partition: Any,
    *,
    section_text_by_id: dict[str, str],
    section_role_by_id: dict[str, str],
) -> list[str]:
    if partition is None:
        return []
    if not isinstance(partition, dict):
        return ["act_partition: must be an object"]

    errors: list[str] = []
    if partition.get("schema") != ACT_PARTITION_SCHEMA:
        errors.append(f"act_partition.schema: must be {ACT_PARTITION_SCHEMA!r}")
    if partition.get("no_duplicate_body_refs") is not True:
        errors.append("act_partition.no_duplicate_body_refs: must be true")
    if partition.get("all_assigned_refs_present") is not True:
        errors.append("act_partition.all_assigned_refs_present: must be true")

    raw_assignments = partition.get("assignments")
    if not isinstance(raw_assignments, list) or not raw_assignments:
        return errors + ["act_partition.assignments: must be a non-empty list"]

    assignments: dict[str, list[str]] = {}
    assigned_owner: dict[str, str] = {}
    assigned_sequence: list[str] = []
    for index, raw in enumerate(raw_assignments):
        label = f"act_partition.assignments[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{label}: must be an object")
            continue
        section_id = raw.get("section_id")
        if not isinstance(section_id, str) or not section_id.strip():
            errors.append(f"{label}.section_id: must be a non-empty string")
            continue
        section_id = section_id.strip()
        if section_id not in section_text_by_id:
            errors.append(f"{label}.section_id: unknown section {section_id!r}")
        elif section_role_by_id.get(section_id) != "layer_b_act":
            errors.append(f"{label}.section_id: section {section_id!r} is not a layer_b_act section")

        body_refs = raw.get("body_refs")
        if not isinstance(body_refs, list) or not all(isinstance(item, str) and item.strip() for item in body_refs):
            errors.append(f"{label}.body_refs: must be a list of non-empty strings")
            continue
        cleaned_refs = [clean_body_ref(item) for item in body_refs]
        if len(cleaned_refs) != len(set(cleaned_refs)):
            errors.append(f"{label}.body_refs: duplicate body_ref assignment inside section")
        assignments[section_id] = cleaned_refs
        assigned_sequence.extend(cleaned_refs)
        for ref in cleaned_refs:
            previous = assigned_owner.get(ref)
            if previous and previous != section_id:
                errors.append(f"act_partition.assignments: body_ref {ref!r} assigned to both {previous!r} and {section_id!r}")
            assigned_owner[ref] = section_id

    layer_b_sections = [section_id for section_id, role in section_role_by_id.items() if role == "layer_b_act"]
    for section_id in layer_b_sections:
        if section_id not in assignments:
            errors.append(f"act_partition.assignments: missing layer_b_act section {section_id!r}")

    visible_refs_by_section: dict[str, list[str]] = {}
    all_visible_refs: list[str] = []
    for section_id in layer_b_sections:
        visible_refs = body_refs_in_act_section(section_text_by_id.get(section_id, ""))
        visible_refs_by_section[section_id] = visible_refs
        all_visible_refs.extend(visible_refs)
        assigned = set(assignments.get(section_id, []))
        extra = sorted({ref for ref in visible_refs if ref not in assigned})
        if extra:
            errors.append(f"act_partition.{section_id}: unassigned body_ref(s) emitted: {extra}")
        missing = sorted(ref for ref in assignments.get(section_id, []) if ref not in visible_refs)
        if missing:
            errors.append(f"act_partition.{section_id}: assigned body_ref(s) missing from section: {missing}")
        if len(visible_refs) != len(set(visible_refs)):
            errors.append(f"act_partition.{section_id}: duplicate visible ACT body_ref inside section")

    if len(all_visible_refs) != len(set(all_visible_refs)):
        duplicates = sorted({ref for ref in all_visible_refs if all_visible_refs.count(ref) > 1})
        errors.append(f"act_partition: duplicate visible ACT body_ref(s) across sections: {duplicates}")

    assigned_refs = set(assigned_owner)
    unassigned_visible = sorted(ref for ref in set(all_visible_refs) if ref not in assigned_refs)
    if unassigned_visible:
        errors.append(f"act_partition: visible ACT body_ref(s) not assigned: {unassigned_visible}")
    missing_visible = sorted(ref for ref in assigned_refs if ref not in set(all_visible_refs))
    if missing_visible:
        errors.append(f"act_partition: assigned body_ref(s) not present in visible ACT output: {missing_visible}")
    errors.extend(body_ref_grouping_errors(assigned_sequence, "act_partition.assignments"))
    errors.extend(body_ref_grouping_errors(all_visible_refs, "act_partition.visible"))
    return errors


def section_payload_errors(section: Any, index: int) -> list[str]:
    label = f"sections[{index}]"
    if not isinstance(section, dict):
        return [f"{label}: must be an object"]
    errors: list[str] = []
    for key in ("id", "path", "sha256", "role"):
        if not isinstance(section.get(key), str) or not section[key].strip():
            errors.append(f"{label}.{key}: must be a non-empty string")
    role = section.get("role")
    if isinstance(role, str) and role not in ROLE_INDEX:
        errors.append(f"{label}.role: unsupported role {role!r}")
    expected_hash = section.get("sha256")
    if isinstance(expected_hash, str) and not SHA256_RE.match(expected_hash):
        errors.append(f"{label}.sha256: must be a SHA-256 hex digest")
    return errors


def assemble_manifest(manifest_path: Path, *, root: Path = ROOT, allow_under_target: bool = False) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = require_under_root(root, manifest_path, "manifest")
    manifest_dir = manifest_path.parent
    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        raise AssemblyError(f"{rel(manifest_path, root)}: manifest root must be an object")

    errors: list[str] = []
    if payload.get("schema") != ASSEMBLY_SCHEMA:
        errors.append(f"schema: must be {ASSEMBLY_SCHEMA!r}")
    if not isinstance(payload.get("case_id"), str) or not payload["case_id"].strip():
        errors.append("case_id: must be a non-empty string")
    errors.extend(validate_non_claims(payload.get("non_claims")))

    per_burden_entries = payload.get(PER_BURDEN_REREAD_FIELD)
    per_burden_errors = per_burden_reread_entry_errors(per_burden_entries, label=PER_BURDEN_REREAD_FIELD)
    errors.extend(per_burden_errors)
    entry_by_burden: dict[str, dict[str, Any]] = {}
    if not per_burden_errors and isinstance(per_burden_entries, list):
        entry_by_burden = {str(entry["burden_id"]): entry for entry in per_burden_entries}

    output = payload.get("output")
    target_output_kb = 0
    target_min_bytes = 0
    if not isinstance(output, dict):
        errors.append("output: must be an object")
        output_path = manifest_dir / "output.md"
    else:
        target_output_kb, target_min_bytes, target_errors = parse_output_targets(output)
        errors.extend(target_errors)
        try:
            output_path = resolve_output_path(root, manifest_dir, output.get("path"), "output.path")
        except AssemblyError as exc:
            errors.append(str(exc))
            output_path = manifest_dir / "output.md"

    sections = payload.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("sections: must be a non-empty list")
        sections = []

    section_texts: list[str] = []
    section_records: list[dict[str, Any]] = []
    section_text_by_id: dict[str, str] = {}
    section_role_by_id: dict[str, str] = {}
    seen_ids: set[str] = set()
    role_counts: dict[str, int] = {role: 0 for role in ROLE_ORDER}
    previous_role_index = -1
    land_gate_sequence: list[str] = []

    for index, section in enumerate(sections):
        label = f"sections[{index}]"
        found = section_payload_errors(section, index)
        errors.extend(found)
        if found:
            continue

        assert isinstance(section, dict)
        section_id = str(section["id"])
        role = str(section["role"])
        if section_id in seen_ids:
            errors.append(f"{label}.id: duplicate section id {section_id!r}")
        seen_ids.add(section_id)

        role_index = ROLE_INDEX[role]
        if role_index < previous_role_index:
            errors.append(f"{label}.role: role {role!r} is out of order")
        previous_role_index = role_index
        role_counts[role] += 1

        try:
            section_path = resolve_section_path(root, manifest_dir, section["path"], f"{label}.path")
        except AssemblyError as exc:
            errors.append(str(exc))
            continue

        expected_hash = str(section["sha256"]).upper()
        actual_hash = sha256_file(section_path)
        if expected_hash != actual_hash:
            errors.append(f"{label}.sha256: expected {expected_hash} but found {actual_hash}")
        original_text = section_path.read_text(encoding="utf-8", errors="replace")
        errors.extend(forbidden_text_errors(original_text, label))
        errors.extend(public_meta_text_errors(original_text, label))
        if MRP_HEADING_LINE_RE.search(original_text):
            errors.append(
                f"{label}: model-authored [Mid-Reread Pressure] heading is forbidden; "
                f"canonical blocks are harness-injected from {PER_BURDEN_REREAD_FIELD} records"
            )
        text, scaffold_event = normalize_section_scaffold(
            section_id,
            role,
            original_text,
            entry_by_burden=entry_by_burden,
        )
        text, trimmed_trailing_whitespace_lines = strip_trailing_line_whitespace(text)
        injected_block_count = 0
        if role == "layer_b_act":
            text, section_gates, injection_errors = inject_per_burden_mrp_blocks(text, entry_by_burden, label)
            errors.extend(injection_errors)
            land_gate_sequence.extend(section_gates)
            injected_block_count = sum(1 for burden_id in section_gates if burden_id in entry_by_burden)
        else:
            stray_gates = land_gate_burdens(text)
            if stray_gates:
                errors.append(
                    f"{label}: superscript Land(ⁿB): landing gate(s) {sorted(set(stray_gates))} "
                    "are only allowed inside layer_b_act sections"
                )
        errors.extend(forbidden_text_errors(text, label))
        errors.extend(public_meta_text_errors(text, label))
        section_texts.append(text)
        section_text_by_id[section_id] = text
        section_role_by_id[section_id] = role
        record = {
            "id": section_id,
            "role": role,
            "path": rel(section_path, root),
            "sha256": actual_hash,
            "bytes": len(original_text.encode("utf-8")),
            "assembled_bytes": len(text.encode("utf-8")),
        }
        if injected_block_count:
            record["injected_mrp_blocks"] = injected_block_count
        if trimmed_trailing_whitespace_lines:
            record["trimmed_trailing_whitespace_lines"] = trimmed_trailing_whitespace_lines
        if scaffold_event is not None:
            record["canonical_scaffold"] = scaffold_event
        section_records.append(record)

    missing_roles = [role for role in ROLE_ORDER if role_counts.get(role, 0) == 0]
    if missing_roles:
        errors.append(f"sections: missing required role(s): {missing_roles}")
    duplicate_singletons = [role for role in sorted(SINGLETON_ROLES) if role_counts.get(role, 0) > 1]
    if duplicate_singletons:
        errors.append(f"sections: singleton role(s) repeated: {duplicate_singletons}")

    duplicate_gates = sorted({burden_id for burden_id in land_gate_sequence if land_gate_sequence.count(burden_id) > 1})
    if duplicate_gates:
        errors.append(f"{PER_BURDEN_REREAD_FIELD}: duplicate Land(ⁿB): landing gate(s) for {duplicate_gates}")
    if not per_burden_errors and entry_by_burden:
        ungated_entries = sorted(set(entry_by_burden) - set(land_gate_sequence))
        if ungated_entries:
            errors.append(
                f"{PER_BURDEN_REREAD_FIELD}: entry burden(s) {ungated_entries} have no visible Land(ⁿB): landing gate"
            )

    assembled = ""
    for text in section_texts:
        if assembled and not assembled.endswith("\n"):
            assembled += "\n"
        assembled += text
        if not assembled.endswith("\n"):
            assembled += "\n"
    errors.extend(forbidden_text_errors(assembled, "assembled output"))
    errors.extend(public_meta_text_errors(assembled, "assembled output"))
    errors.extend(required_surface_errors(assembled))
    errors.extend(final_public_tail_errors(assembled, "assembled output"))
    errors.extend(
        act_partition_errors(
            payload.get("act_partition"),
            section_text_by_id=section_text_by_id,
            section_role_by_id=section_role_by_id,
        )
    )
    budget_found, normalized_budgets = section_budget_errors(
        payload.get("section_budgets"),
        section_records=section_records,
        allow_under_target=allow_under_target,
    )
    errors.extend(budget_found)
    expansion_found, normalized_expansions = validate_section_expansions(
        payload.get("section_expansions"),
        root=root,
        manifest_dir=manifest_dir,
        section_role_by_id=section_role_by_id,
    )
    errors.extend(expansion_found)
    assembled_bytes = len(assembled.encode("utf-8"))
    if target_min_bytes and assembled_bytes < target_min_bytes and not allow_under_target:
        errors.append(
            "assembled output: under target size "
            f"({assembled_bytes} bytes < {target_min_bytes} bytes)"
        )

    if errors:
        raise AssemblyError("\n- ".join(["staged governed output assembly failed:", *errors]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(assembled, encoding="utf-8", newline="\n")
    output_hash = sha256_file(output_path)
    hash_record_path = output_path.with_suffix(output_path.suffix + ".assembly.hashes.json")
    record = {
        "schema": HASH_RECORD_SCHEMA,
        "assembly_manifest": {"path": rel(manifest_path, root), "sha256": sha256_file(manifest_path)},
        "case_id": payload["case_id"],
        "source_input": payload.get("source_input"),
        "output": {
            "path": rel(output_path, root),
            "sha256": output_hash,
            "bytes": output_path.stat().st_size,
            "target_output_kb": target_output_kb,
            "target_min_bytes": target_min_bytes,
            "under_target_allowed": allow_under_target,
        },
        "sections": section_records,
        "per_burden_mrp": {
            "entry_burdens": sorted(entry_by_burden),
            "land_gates": land_gate_sequence,
        },
        "non_claims": {key: payload["non_claims"].get(key) for key in sorted(REQUIRED_NON_CLAIMS)},
    }
    if payload.get("act_partition") is not None:
        record["act_partition"] = payload["act_partition"]
    scaffold_events = [
        section_record["canonical_scaffold"]
        for section_record in section_records
        if section_record.get("canonical_scaffold") is not None
    ]
    if scaffold_events:
        record["canonical_scaffold"] = {
            "schema": CANONICAL_SCAFFOLD_SCHEMA,
            "events": scaffold_events,
        }
    if normalized_budgets is not None:
        record["section_budgets"] = normalized_budgets
    if normalized_expansions is not None:
        record["section_expansions"] = normalized_expansions
    write_json(hash_record_path, record)
    record["hash_record"] = {"path": rel(hash_record_path, root), "sha256": sha256_file(hash_record_path)}
    write_json(hash_record_path, record)
    return record


def self_test_per_burden_entry(burden_id: str, *, next_burden_id: str | None = None) -> dict[str, Any]:
    public = public_burden_token(burden_id[1:])
    if next_burden_id is None:
        reread = (
            f"R(H,Δ): held routes rechecked: none; live remainder: no remaining burden; "
            f"release/next: STOP after {public}."
        )
        entry_tail: dict[str, Any] = {
            "route_gradient": f"plain-gradient points to STOP after {public}; no live pressure remains.",
            "finding": "stable",
            "route_result_type": "no_new_resultant",
            "mrp_resultant": "stable -> no new graph edge; STOP",
            "graph_delta": "none",
            "preemption_basis": "none",
            "route": "STOP",
        }
        dependency_tug = "pressure class: dependency-scan — no κ dependency remains live."
        entailment = "M8 — no entailment pressure remains against the bounded close."
    else:
        next_public = public_burden_token(next_burden_id[1:])
        reread = (
            f"R(H,Δ): held routes rechecked: {next_public}; live remainder: {next_public}; "
            f"release/next: RECURSE to {next_public}."
        )
        entry_tail = {
            "route_gradient": (
                f"already-held {next_public} from the initial burden set carries the highest pressure after R(H,Δ)."
            ),
            "finding": "genuine-dependent",
            "route_result_type": "held_burden_activation",
            "mrp_resultant": f"genuine-dependent -> graph {burden_id} -> {next_burden_id}; RECURSE",
            "graph_delta": f"{burden_id} -> {next_burden_id}",
            "preemption_basis": "graph-bound",
            "route": "RECURSE",
        }
        dependency_tug = f"pressure class: dependency-scan — {next_public} dependency stays live."
        entailment = f"M8 — entailment presses toward {next_public}."
    return {
        "burden_id": burden_id,
        "target": f"{public} / bounded self-test burden",
        "reread": reread,
        "landed_delta": f"Δ{public} / Delta({burden_id}): bounded-self-test-delta recorded.",
        "pressure_activations": {
            "freeze-landed-move": f"diagnostic-render-contract — Land({public}) frozen before reread.",
            "dependency-tug": dependency_tug,
            "hidden-framework-recoil": "FPD — no hidden framework support reopens the landed move.",
            "entailment-pressure": entailment,
            "doubt-churn-guard": "doubt-vs-skepticism — no churn or proof-carousel loop is live.",
            "reorientation-reminder": "P1 — reorientation reminder cleared toward landed signs.",
        },
        "divergence": "∇·B: neutral / no remaining burden pressure",
        "curl": "∇×κ: null / no circular dependency",
        **entry_tail,
        "boundary": "T_lang does not imply guaranteed uptake.",
    }


def self_test_per_burden_chain(burden_ids: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for index, burden_id in enumerate(burden_ids):
        next_burden_id = burden_ids[index + 1] if index + 1 < len(burden_ids) else None
        entries.append(self_test_per_burden_entry(burden_id, next_burden_id=next_burden_id))
    return entries


def manifest_for_sections(
    case_dir: Path,
    *,
    case_id: str,
    source_input: str,
    section_specs: list[tuple[str, str, str]],
    output_name: str = "output.md",
    target_output_kb: int = 0,
    act_partition: dict[str, Any] | None = None,
    section_budgets: dict[str, Any] | None = None,
    section_expansions: dict[str, Any] | None = None,
    per_burden_reread: list[dict[str, Any]] | None = None,
) -> Path:
    sections_dir = case_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    sections_payload: list[dict[str, str]] = []
    for index, (section_id, role, text) in enumerate(section_specs):
        path = sections_dir / f"{index:02d}-{section_id}.md"
        path.write_text(text, encoding="utf-8", newline="\n")
        sections_payload.append(
            {
                "id": section_id,
                "path": path.relative_to(case_dir).as_posix(),
                "sha256": sha256_file(path),
                "role": role,
            }
        )
    manifest_path = case_dir / "assembly.manifest.json"
    payload: dict[str, Any] = {
        "schema": ASSEMBLY_SCHEMA,
        "case_id": case_id,
        "source_input": source_input,
        "sections": sections_payload,
        "output": {"path": output_name, "target_output_kb": target_output_kb},
        PER_BURDEN_REREAD_FIELD: (
            per_burden_reread
            if per_burden_reread is not None
            else [self_test_per_burden_entry("B1")]
        ),
        "non_claims": {
            "not_release_provenance": True,
            "not_model_behavior_by_itself": True,
            "not_sidecar_proof": True,
        },
    }
    if act_partition is not None:
        payload["act_partition"] = act_partition
    if section_budgets is not None:
        payload["section_budgets"] = section_budgets
    if section_expansions is not None:
        payload["section_expansions"] = section_expansions
    write_json(manifest_path, payload)
    return manifest_path


def small_sections(*, act_text: str = "Layer B - Bounded Governed Response\nACT row body_ref=¹B₁.\nLand(¹B): landed.\n") -> list[tuple[str, str, str]]:
    return [
        ("opening", "visible_opening", "daee-epistemics — NOETIC FIELD EXECUTION\nCase opening preserved.\n"),
        (
            "layer-a",
            "layer_a_diagnostic_ir",
            "Layer A - Compact DSL/IR Header\n"
            "- Initial burden set: [¹B]\n"
            "- 𝔅_LA (B_LA) = {¹B}\n"
            "- 𝔅_MRP (B_MRP) = {}\n"
            "- 𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {¹B}\n",
        ),
        ("act-body", "layer_b_act", act_text),
        (
            "mrp",
            "mrp_reread_terminal",
            "MRP terminal reconstruction floor\n"
            "Route-state ledger:\n"
            "- MRP(B1): type=no_new_resultant; finding=stable; graph=none; route=STOP\n"
            "Terminal states: B1=landed.\n"
            "Field diagnostics: ∇·B: neutral / no remaining burden; ∇×κ: null / no circular dependency.\n"
        ),
        ("release", "restorative_response", "Restorative Response\nRestored orientation.\n"),
        (
            "closing",
            "closing_formulation",
            "Closing Formulation\n"
            "### Established failure\nFailure established.\n"
            "### Restored criterion/orientation\nRestored orientation.\n"
            "### Scoped boundary\nScoped boundary.\n",
        ),
        (
            "field-witness",
            "field_witness_nar",
            "Closure/Reconstruction Witness\n"
            "Initial burden set: [¹B]\n"
            "𝔅_LA (B_LA) = {¹B}\n"
            "𝔅_MRP (B_MRP) = {}\n"
            "𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {¹B}\n"
            "Burden dependency graph:\n"
            "¹B (root)\n"
            "Terminal states:\n"
            "¹B: landed / ACT owners / landed by visible owner activations\n"
            "MRP resultants:\n"
            "MRP(¹B): type=no_new_resultant; finding=stable; graph=none; route=STOP\n"
            "∇·B: neutral / no remaining burden\n"
            "∇×κ: null / no circular dependency\n"
            "𝒞(Ψᴺ): COMPLETE / coverage_complete=true; runtime execution field remains bounded to this reply\n"
            "T_lang: Ψᴺ -> Ψᴵ: partial coupling boundary; no guaranteed uptake\n"
            "field_witness\n"
            "{\n"
            "  \"B_LA\": [\"B1\"],\n"
            "  \"B_MRP\": [],\n"
            "  \"B_total\": [\"B1\"],\n"
            "  \"coverage_proof\": {\n"
            "    \"divergence_check\": \"neutral\",\n"
            "    \"curl_check\": \"null\"\n"
            "  },\n"
            "  \"normalized_activation_record\": {\n"
            "    \"n_frame\": \"self-test\",\n"
            "    \"live_registers\": [\"xi\"],\n"
            "    \"burden_floor\": [\"B1\"],\n"
            "    \"per_burden\": []\n"
            "  }\n"
            "}\n",
        ),
    ]


def expect_invalid(
    root: Path,
    base_dir: Path,
    name: str,
    mutate: Callable[[dict[str, Any], Path], None],
) -> None:
    case_dir = base_dir / name
    manifest_path = manifest_for_sections(
        case_dir,
        case_id=name,
        source_input=f"{name}/input.md",
        section_specs=small_sections(),
    )
    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        raise AssertionError("self-test manifest payload must be an object")
    mutate(payload, case_dir)
    write_json(manifest_path, payload)
    try:
        assemble_manifest(manifest_path, root=root)
    except AssemblyError:
        return
    raise AssemblyError(f"self-test expected invalid assembly to fail: {name}")


def replace_section_text(payload: dict[str, Any], case_dir: Path, index: int, text: str) -> None:
    path = case_dir / payload["sections"][index]["path"]
    path.write_text(text, encoding="utf-8", newline="\n")
    payload["sections"][index]["sha256"] = sha256_file(path)


def act_partition_payload(assignments: list[tuple[str, list[str]]]) -> dict[str, Any]:
    return {
        "schema": ACT_PARTITION_SCHEMA,
        "assignments": [
            {"section_id": section_id, "body_refs": body_refs}
            for section_id, body_refs in assignments
        ],
        "no_duplicate_body_refs": True,
        "all_assigned_refs_present": True,
    }


def act_section(
    section_id: str,
    *body_refs: str,
    land_burdens: list[str] | None = None,
) -> tuple[str, str, str]:
    rows = []
    burdens_in_order: list[str] = []
    for body_ref in body_refs:
        burden_id = body_ref_burden_id(body_ref) or "B1"
        if burden_id not in burdens_in_order:
            burdens_in_order.append(burden_id)
        rows.append(
            f"⟦ACT {body_ref}[M9.predication-repair] :: π=predicate-transfer :: "
            f"body_ref={body_ref} :: Δ=Δ{burden_id}:predicate-transfer-blocked :: Land({burden_id})+⟧"
        )
    if land_burdens is None:
        land_burdens = burdens_in_order or ["B1"]
    gate_lines = "".join(
        f"Land({public_burden_token(burden_id[1:])}): landed.\n" for burden_id in land_burdens
    )
    return (
        section_id,
        "layer_b_act",
        "Layer B - Bounded Governed Response\nACT records:\n" + "\n".join(rows) + "\n" + gate_lines,
    )


def assert_scaffold_events_non_evidence(record: dict[str, Any], label: str) -> None:
    scaffold = record.get("canonical_scaffold")
    if not isinstance(scaffold, dict):
        return
    events = scaffold.get("events")
    if not isinstance(events, list):
        return
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            raise AssemblyError(f"self-test {label} canonical scaffold event {index} is not an object")
        if event.get("proof_authority") != "none" or event.get("proof_role") != "non_evidence_canonicalization":
            raise AssemblyError(f"self-test {label} canonical scaffold event {index} lacked non-evidence proof metadata")
        if event.get("proof_claim") is not False:
            raise AssemblyError(f"self-test {label} canonical scaffold event {index} claimed proof")


def run_self_test(root: Path) -> int:
    base_dir = root / ".daee" / "validation" / f"staged-governed-output-assembly-self-test-{uuid.uuid4().hex}"
    base_dir.mkdir(parents=True, exist_ok=True)

    # No-model canary: the pressure_activation admissible-prefix contract must REJECT bare
    # family aliases (SOURCE/AUTHORITY/OWNER/OP/MRP/DEFINITION/RESTORATION are loose aliases
    # per references/module-codes.md and do not satisfy owner/TTP fields) while ACCEPTING a
    # specific routed owner/TTP id or the literal pressure class:/coverage gap: marker. This
    # pins the contract the Stage 05 producer prompt now advertises to the model, so the two
    # never drift: the checker stays strict (no bare-alias whitelisting) and the prompt warns.
    for _reject in (
        "SOURCE pressure class: x", "AUTHORITY pressure class: x", "OWNER pressure class: x",
        "OP pressure class: x", "MRP pressure class: x", "DEFINITION pressure class: x",
        "RESTORATION pressure class: x",
    ):
        if PER_BURDEN_SLOT_START_RE.match(_reject):
            raise AssemblyError(
                f"self-test: pressure-activation prefix contract wrongly accepted a loose family alias: {_reject!r}"
            )
    for _accept in (
        "authority-order-repair pressure class: x", "source-lineage pressure class: x",
        "M7 pressure class: x", "FPD pressure class: x", "pressure class: x", "coverage gap: x",
    ):
        if not PER_BURDEN_SLOT_START_RE.match(_accept):
            raise AssemblyError(
                f"self-test: pressure-activation prefix contract wrongly rejected an admissible prefix: {_accept!r}"
            )

    small_manifest = manifest_for_sections(
        base_dir / "valid-small",
        case_id="valid-small",
        source_input="valid-small/input.md",
        section_specs=small_sections(),
    )
    small_record = assemble_manifest(small_manifest, root=root)
    if small_record["output"]["bytes"] <= 0:
        raise AssemblyError("self-test valid small assembly wrote an empty output")
    small_output = (base_dir / "valid-small" / "output.md").read_text(encoding="utf-8")
    if small_output.count("[Mid-Reread Pressure]") != 1:
        raise AssemblyError("self-test valid small assembly must inject exactly one MRP block")
    small_gate_at = small_output.find("Land(¹B):")
    small_block_at = small_output.find("[Mid-Reread Pressure]")
    if small_gate_at < 0 or small_block_at < 0 or small_block_at < small_gate_at:
        raise AssemblyError("self-test valid small assembly must inject the MRP block after the landing gate")
    for required in (
        "Target: ¹B / bounded self-test burden",
        "- freeze-landed-move: diagnostic-render-contract — Land(¹B) frozen before reread.",
        "Field diagnostics: ∇·B: neutral / no remaining burden pressure; ∇×κ: null / no circular dependency",
        "MRP route result type: no_new_resultant",
        "Pre-emption basis: none",
        "LoopBreak: not needed",
        "Boundary: T_lang does not imply guaranteed uptake.",
    ):
        if required not in small_output:
            raise AssemblyError(f"self-test valid small injected MRP block omitted {required}")
    if not any(
        section.get("injected_mrp_blocks") == 1
        for section in small_record.get("sections", [])
        if isinstance(section, dict)
    ):
        raise AssemblyError("self-test valid small assembly did not record injected MRP block metadata")
    if small_record.get("per_burden_mrp") != {"entry_burdens": ["B1"], "land_gates": ["B1"]}:
        raise AssemblyError("self-test valid small assembly did not record per-burden MRP accounting")
    if not public_meta_text_errors("Final answer only text?\nNeed include public rows.\n", "self-test"):
        raise AssemblyError("self-test public meta guard did not catch planning prose")

    expect_invalid(
        root,
        base_dir,
        "invalid-public-planning-text",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            2,
            "Layer B - Bounded Governed Response\n"
            "ACT row body_ref=¹B₁.\n"
            "Final answer only text? Need include the assigned ACT row.\n"
            "Land(¹B): landed.\n",
        ),
    )

    trailing_whitespace_sections = list(small_sections())
    trailing_whitespace_sections[0] = (
        "opening",
        "visible_opening",
        "daee-epistemics - NOETIC FIELD EXECUTION  \nCase opening preserved.\t\n",
    )
    trailing_whitespace_manifest = manifest_for_sections(
        base_dir / "valid-trailing-whitespace-normalization",
        case_id="valid-trailing-whitespace-normalization",
        source_input="valid-trailing-whitespace-normalization/input.md",
        section_specs=trailing_whitespace_sections,
    )
    trailing_whitespace_record = assemble_manifest(trailing_whitespace_manifest, root=root)
    trailing_whitespace_output = (
        base_dir / "valid-trailing-whitespace-normalization" / "output.md"
    ).read_text(encoding="utf-8")
    if any(line.rstrip(" \t") != line for line in trailing_whitespace_output.splitlines()):
        raise AssemblyError("self-test valid trailing whitespace normalization left line-end whitespace")
    if not any(
        section.get("trimmed_trailing_whitespace_lines") == 2
        for section in trailing_whitespace_record.get("sections", [])
        if isinstance(section, dict)
    ):
        raise AssemblyError("self-test valid trailing whitespace normalization metadata missing")

    large_act_chunks = [
        (
            f"act-body-{index}",
            "layer_b_act",
            (
                "Layer B - Bounded Governed Response\n"
                f"ACT body_ref=B{index}.s1.\n"
                "Operation: bounded section work.\n"
                "Result/state-change: bounded section landing notes continue.\n"
            )
            * 900
            + f"Land({public_burden_token(str(index))}): landed.\n",
        )
        for index in range(1, 5)
    ]
    large_manifest = manifest_for_sections(
        base_dir / "valid-large",
        case_id="valid-large",
        source_input="valid-large/input.md",
        section_specs=[
            *small_sections(act_text="Layer B opening ACT body_ref=B1.s0.\nLand(B1): landed.\n")[:2],
            *large_act_chunks,
            *small_sections()[3:],
        ],
        target_output_kb=200,
        per_burden_reread=self_test_per_burden_chain(["B1", "B2", "B3", "B4"]),
    )
    large_record = assemble_manifest(large_manifest, root=root)
    if large_record["output"]["bytes"] < 200 * 1024:
        raise AssemblyError("self-test valid large assembly did not reach 200KB")
    large_output = (base_dir / "valid-large" / "output.md").read_text(encoding="utf-8")
    if large_output.count("[Mid-Reread Pressure]") != 4:
        raise AssemblyError("self-test valid large assembly must inject one MRP block per landing gate")

    valid_100kb_manifest = manifest_for_sections(
        base_dir / "valid-100kb",
        case_id="valid-100kb",
        source_input="valid-100kb/input.md",
        section_specs=[
            *small_sections(act_text="Layer B - Bounded Governed Response\nACT body_ref=B1.s0.\nLand(B1): landed.\n")[:2],
            *large_act_chunks[:2],
            *small_sections()[3:],
        ],
        target_output_kb=100,
        per_burden_reread=self_test_per_burden_chain(["B1", "B2"]),
    )
    valid_100kb_record = assemble_manifest(valid_100kb_manifest, root=root)
    if valid_100kb_record["output"]["bytes"] < 100 * 1024:
        raise AssemblyError("self-test valid 100KB assembly did not reach 100KB")

    scaffold_manifest = manifest_for_sections(
        base_dir / "valid-canonical-scaffold",
        case_id="valid-canonical-scaffold",
        source_input="valid-canonical-scaffold/input.md",
        section_specs=[
            *small_sections()[:6],
            (
                "field-witness",
                "field_witness_nar",
                "Closure / Reconstruction Witness\n"
                "field_witness\n"
                "{\n"
                "  \"B_LA\": [\"B1\"],\n"
                "  \"B_MRP\": [],\n"
                "  \"B_total\": [\"B1\"],\n"
                "  \"coverage_proof\": {\"divergence_check\": \"neutral\", \"curl_check\": \"null\"},\n"
                "  \"normalized_activation_record\": {\"n_frame\": \"self-test\", \"live_registers\": [\"xi\"]}\n"
                "}\n",
            ),
        ],
    )
    scaffold_record = assemble_manifest(scaffold_manifest, root=root)
    assert_scaffold_events_non_evidence(scaffold_record, "canonical scaffold")
    scaffold_output = (base_dir / "valid-canonical-scaffold" / "output.md").read_text(encoding="utf-8")
    if "Closure/Reconstruction Witness" not in scaffold_output:
        raise AssemblyError("self-test canonical scaffold did not insert exact closure witness heading")
    if "Closure / Reconstruction Witness" in scaffold_output:
        raise AssemblyError("self-test canonical scaffold left the model heading variant visible")
    if not scaffold_record.get("canonical_scaffold"):
        raise AssemblyError("self-test canonical scaffold did not record scaffold metadata")

    decorated_heading_manifest = manifest_for_sections(
        base_dir / "valid-decorated-public-headings",
        case_id="valid-decorated-public-headings",
        source_input="valid-decorated-public-headings/input.md",
        section_specs=[
            *small_sections()[:4],
            ("release", "restorative_response", "**Restorative Response**\nRestored orientation.\n"),
            ("closing", "closing_formulation", "# __Closing Formulation__\nScoped boundary.\n"),
            small_sections()[6],
        ],
    )
    decorated_heading_record = assemble_manifest(decorated_heading_manifest, root=root)
    decorated_heading_output = (
        base_dir / "valid-decorated-public-headings" / "output.md"
    ).read_text(encoding="utf-8")
    if "**Restorative Response**" in decorated_heading_output:
        raise AssemblyError("self-test decorated Restorative Response heading was not canonicalized")
    if "__Closing Formulation__" in decorated_heading_output:
        raise AssemblyError("self-test decorated Closing Formulation heading was not canonicalized")
    if "Restorative Response\nRestored orientation." not in decorated_heading_output:
        raise AssemblyError("self-test decorated Restorative Response heading was not preserved canonically")
    if "Closing Formulation\nScoped boundary." not in decorated_heading_output:
        raise AssemblyError("self-test decorated Closing Formulation heading was not preserved canonically")
    decorated_scaffold = decorated_heading_record.get("canonical_scaffold")
    decorated_events = (
        decorated_scaffold.get("events", [])
        if isinstance(decorated_scaffold, dict)
        else []
    )
    decorated_roles = {event.get("role") for event in decorated_events if isinstance(event, dict)}
    if {"restorative_response", "closing_formulation"} - decorated_roles:
        raise AssemblyError("self-test decorated heading scaffold metadata missing")
    decorated_order = [
        decorated_heading_output.find("Restorative Response"),
        decorated_heading_output.find("Closing Formulation"),
        decorated_heading_output.find("Closure/Reconstruction Witness"),
        decorated_heading_output.find("field_witness"),
    ]
    if any(index < 0 for index in decorated_order) or decorated_order != sorted(decorated_order):
        raise AssemblyError("self-test decorated output did not preserve Restorative -> Closing -> witness -> field_witness order")

    missing_heading_manifest = manifest_for_sections(
        base_dir / "valid-missing-role-headings",
        case_id="valid-missing-role-headings",
        source_input="valid-missing-role-headings/input.md",
        section_specs=[
            *small_sections()[:4],
            ("release", "restorative_response", "Restored orientation without role heading.\n"),
            (
                "closing",
                "closing_formulation",
                "### Established failure\nFailure established.\n"
                "### Restored criterion/orientation\nRestored orientation.\n"
                "### Scoped boundary\nScoped boundary.\n",
            ),
            small_sections()[6],
        ],
    )
    missing_heading_record = assemble_manifest(missing_heading_manifest, root=root)
    missing_heading_output = (
        base_dir / "valid-missing-role-headings" / "output.md"
    ).read_text(encoding="utf-8")
    if "Restorative Response\nRestored orientation without role heading." not in missing_heading_output:
        raise AssemblyError("self-test missing Restorative Response heading was not inserted")
    if "Closing Formulation\n### Established failure" not in missing_heading_output:
        raise AssemblyError("self-test missing Closing Formulation heading was not inserted")
    missing_scaffold = missing_heading_record.get("canonical_scaffold")
    missing_events = (
        missing_scaffold.get("events", [])
        if isinstance(missing_scaffold, dict)
        else []
    )
    missing_roles = {event.get("role") for event in missing_events if isinstance(event, dict)}
    if {"restorative_response", "closing_formulation"} - missing_roles:
        raise AssemblyError("self-test missing role-heading scaffold metadata missing")

    ordering_field_witness = (
        "Closure/Reconstruction Witness\n"
        "Initial burden set: [¹B]\n"
        "𝔅_LA (B_LA) = {¹B}\n"
        "𝔅_MRP (B_MRP) = {}\n"
        "𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {¹B}\n"
        "Burden dependency graph:\n"
        "¹B (root)\n"
        "Terminal states:\n"
        "¹B: landed / ACT owners / landed by visible owner activations\n"
        "MRP resultants:\n"
        "MRP(¹B): type=no_new_resultant; finding=stable; graph=none; route=STOP\n"
        "∇·B: neutral / no remaining burden\n"
        "∇×κ: null / no circular dependency\n"
        "𝒞(Ψᴺ): COMPLETE / coverage_complete=true; runtime execution field remains bounded to this reply\n"
        "T_lang: Ψᴺ -> Ψᴵ: partial coupling boundary; no guaranteed uptake\n"
        "field_witness\n"
        "{\n"
        "  \"B_LA\": [\"B1\"],\n"
        "  \"B_MRP\": [],\n"
        "  \"B_total\": [\"B1\"],\n"
        "  \"owner_activations\": [\n"
        "    {\"target\": \"B1\", \"owner\": \"source-status-repair\", \"operation\": \"source-order\", \"body_ref\": \"¹B₁\"},\n"
        "    {\"target\": \"B1\", \"owner\": \"M1\", \"operation\": \"self-grounding-test\", \"body_ref\": \"¹B₂\"}\n"
        "  ],\n"
        "  \"coverage_proof\": {\"divergence_check\": \"neutral\", \"curl_check\": \"null\"},\n"
        "  \"normalized_activation_record\": {\"n_frame\": \"self-test\", \"live_registers\": [\"xi\"], \"burden_floor\": [\"B1\"], \"per_burden\": []}\n"
        "}\n"
    )
    ordering_manifest = manifest_for_sections(
        base_dir / "valid-owner-activation-ordering-insertion",
        case_id="valid-owner-activation-ordering-insertion",
        source_input="valid-owner-activation-ordering-insertion/input.md",
        section_specs=[*small_sections()[:6], ("field-witness", "field_witness_nar", ordering_field_witness)],
    )
    ordering_record = assemble_manifest(ordering_manifest, root=root)
    ordering_output = (
        base_dir / "valid-owner-activation-ordering-insertion" / "output.md"
    ).read_text(encoding="utf-8")
    for required in (
        '"owner_activation_ordering"',
        '"policy_id": "diagnostic-ir-pressure-owner-floor-v1"',
        '"before_owner": "source-status-repair"',
        '"after_owner": "M1"',
        '"ordering_role": "required"',
    ):
        if required not in ordering_output:
            raise AssemblyError(f"self-test owner activation ordering insertion omitted {required}")
    ordering_scaffold = ordering_record.get("canonical_scaffold")
    ordering_events = (
        ordering_scaffold.get("events", [])
        if isinstance(ordering_scaffold, dict)
        else []
    )
    if not any(
        event.get("inserted_owner_activation_ordering") is True
        and event.get("required_before_count") == 1
        for event in ordering_events
        if isinstance(event, dict)
    ):
        raise AssemblyError("self-test owner activation ordering scaffold metadata missing")
    if not any(
        event.get("inserted_owner_activation_ordering_roles") == 2
        for event in ordering_events
        if isinstance(event, dict)
    ):
        raise AssemblyError("self-test owner activation ordering role metadata missing")

    repeated_owner_field_witness = ordering_field_witness.replace(
        "    {\"target\": \"B1\", \"owner\": \"source-status-repair\", \"operation\": \"source-order\", \"body_ref\": \"¹B₁\"},\n"
        "    {\"target\": \"B1\", \"owner\": \"M1\", \"operation\": \"self-grounding-test\", \"body_ref\": \"¹B₂\"}\n",
        "    {\"target\": \"B1\", \"owner\": \"do-christian-extensions\", \"operation\": \"model-identification\", \"body_ref\": \"¹B₁\"},\n"
        "    {\"target\": \"B1\", \"owner\": \"M9\", \"operation\": \"predication-repair\", \"body_ref\": \"¹B₂\"},\n"
        "    {\"target\": \"B1\", \"owner\": \"do-attribute-precision\", \"operation\": \"attribute-precision\", \"body_ref\": \"¹B₃\"},\n"
        "    {\"target\": \"B1\", \"owner\": \"M9\", \"operation\": \"predication-repair\", \"body_ref\": \"¹B₄\"}\n",
    )
    repeated_owner_manifest = manifest_for_sections(
        base_dir / "valid-owner-activation-ordering-repeated-family",
        case_id="valid-owner-activation-ordering-repeated-family",
        source_input="valid-owner-activation-ordering-repeated-family/input.md",
        section_specs=[*small_sections()[:6], ("field-witness", "field_witness_nar", repeated_owner_field_witness)],
    )
    repeated_owner_record = assemble_manifest(repeated_owner_manifest, root=root)
    repeated_owner_output = (
        base_dir / "valid-owner-activation-ordering-repeated-family" / "output.md"
    ).read_text(encoding="utf-8")
    if '"before_owner": "do-attribute-precision",\n        "after_owner": "M9"' in repeated_owner_output:
        raise AssemblyError("self-test owner ordering repeated-family insertion created a false cycle")
    for required in (
        '"before_owner": "do-christian-extensions"',
        '"after_owner": "M9"',
        '"before_owner": "M9"',
        '"after_owner": "do-attribute-precision"',
    ):
        if required not in repeated_owner_output:
            raise AssemblyError(f"self-test owner ordering repeated-family insertion omitted {required}")
    repeated_owner_events = (
        (repeated_owner_record.get("canonical_scaffold") or {}).get("events", [])
        if isinstance(repeated_owner_record.get("canonical_scaffold"), dict)
        else []
    )
    if not any(
        event.get("inserted_owner_activation_ordering") is True
        and event.get("required_before_count") == 2
        for event in repeated_owner_events
        if isinstance(event, dict)
    ):
        raise AssemblyError("self-test owner ordering repeated-family metadata missing")

    preplanned_field_witness = ordering_field_witness.replace(
        '  "owner_activations": [',
        '  "owner_activation_ordering": {\n'
        '    "policy_id": "diagnostic-ir-pressure-owner-floor-v1",\n'
        '    "parallel_groups": [],\n'
        '    "required_before": [\n'
        '      {"target": "B1", "before_owner": "source-status-repair", "after_owner": "M1"}\n'
        '    ]\n'
        '  },\n'
        '  "owner_activations": [',
    )
    preplanned_manifest = manifest_for_sections(
        base_dir / "valid-owner-activation-ordering-role-insertion",
        case_id="valid-owner-activation-ordering-role-insertion",
        source_input="valid-owner-activation-ordering-role-insertion/input.md",
        section_specs=[*small_sections()[:6], ("field-witness", "field_witness_nar", preplanned_field_witness)],
    )
    preplanned_record = assemble_manifest(preplanned_manifest, root=root)
    preplanned_output = (
        base_dir / "valid-owner-activation-ordering-role-insertion" / "output.md"
    ).read_text(encoding="utf-8")
    if preplanned_output.count('"ordering_role": "required"') != 2:
        raise AssemblyError("self-test owner activation ordering role insertion missed preplanned activations")
    preplanned_events = (
        (preplanned_record.get("canonical_scaffold") or {}).get("events", [])
        if isinstance(preplanned_record.get("canonical_scaffold"), dict)
        else []
    )
    if not any(
        event.get("inserted_owner_activation_ordering_roles") == 2
        and event.get("inserted_owner_activation_ordering") is not True
        for event in preplanned_events
        if isinstance(event, dict)
    ):
        raise AssemblyError("self-test preplanned owner activation ordering role metadata missing")

    partial_plan_field_witness = (
        "Closure/Reconstruction Witness\n"
        "Initial burden set: [¹B, ³B]\n"
        "𝔅_LA (B_LA) = {¹B, ³B}\n"
        "𝔅_MRP (B_MRP) = {}\n"
        "𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP = {¹B, ³B}\n"
        "Burden dependency graph:\n"
        "¹B (root); ³B (root)\n"
        "Terminal states:\n"
        "¹B: landed / ACT owners / landed by visible owner activations\n"
        "³B: landed / ACT owners / landed by visible owner activations\n"
        "MRP resultants:\n"
        "MRP(¹B): type=no_new_resultant; finding=stable; graph=none; route=STOP\n"
        "MRP(³B): type=no_new_resultant; finding=stable; graph=none; route=STOP\n"
        "∇·B: neutral / no remaining burden\n"
        "∇×κ: null / no circular dependency\n"
        "𝒞(Ψᴺ): COMPLETE / coverage_complete=true; runtime execution field remains bounded to this reply\n"
        "T_lang: Ψᴺ -> Ψᴵ: partial coupling boundary; no guaranteed uptake\n"
        "field_witness\n"
        "{\n"
        "  \"B_LA\": [\"B1\", \"B3\"],\n"
        "  \"B_MRP\": [],\n"
        "  \"B_total\": [\"B1\", \"B3\"],\n"
        "  \"owner_activation_ordering\": {\n"
        "    \"policy_id\": \"diagnostic-ir-pressure-owner-floor-v1\",\n"
        "    \"parallel_groups\": [],\n"
        "    \"required_before\": [\n"
        "      {\"target\": \"B1\", \"before_owner\": \"source-status-repair\", \"after_owner\": \"M1\"}\n"
        "    ]\n"
        "  },\n"
        "  \"owner_activations\": [\n"
        "    {\"target\": \"B1\", \"owner\": \"source-status-repair\", \"operation\": \"source-order\", \"body_ref\": \"¹B₁\"},\n"
        "    {\"target\": \"B1\", \"owner\": \"M1\", \"operation\": \"self-grounding-test\", \"body_ref\": \"¹B₂\"},\n"
        "    {\"target\": \"B3\", \"owner\": \"source-status-repair\", \"operation\": \"source-order\", \"body_ref\": \"³B₁\"},\n"
        "    {\"target\": \"B3\", \"owner\": \"authority-order-repair\", \"operation\": \"sort\", \"body_ref\": \"³B₂\"}\n"
        "  ],\n"
        "  \"coverage_proof\": {\"divergence_check\": \"neutral\", \"curl_check\": \"null\"},\n"
        "  \"normalized_activation_record\": {\"n_frame\": \"self-test\", \"live_registers\": [\"xi\"], \"burden_floor\": [\"B1\", \"B3\"], \"per_burden\": []}\n"
        "}\n"
    )
    partial_plan_manifest = manifest_for_sections(
        base_dir / "valid-owner-activation-ordering-partial-plan-merge",
        case_id="valid-owner-activation-ordering-partial-plan-merge",
        source_input="valid-owner-activation-ordering-partial-plan-merge/input.md",
        section_specs=[*small_sections()[:6], ("field-witness", "field_witness_nar", partial_plan_field_witness)],
    )
    partial_plan_record = assemble_manifest(partial_plan_manifest, root=root)
    partial_plan_output = (
        base_dir / "valid-owner-activation-ordering-partial-plan-merge" / "output.md"
    ).read_text(encoding="utf-8")
    partial_label = FIELD_WITNESS_LABEL_RE.search(partial_plan_output)
    if partial_label is None:
        raise AssemblyError("self-test partial owner ordering output omitted field_witness label")
    partial_span = json_object_span_after(partial_plan_output, partial_label.end())
    if partial_span is None:
        raise AssemblyError("self-test partial owner ordering output omitted field_witness JSON")
    partial_payload = json.loads(partial_plan_output[partial_span[0] : partial_span[1]])
    partial_field_witness = field_witness_payload_ref(partial_payload) or {}
    partial_rules = (
        (partial_field_witness.get("owner_activation_ordering") or {}).get("required_before")
        if isinstance(partial_field_witness.get("owner_activation_ordering"), dict)
        else []
    )
    if not any(
        isinstance(rule, dict)
        and rule.get("target") == "B3"
        and rule.get("before_owner") == "source-status-repair"
        and rule.get("after_owner") == "authority-order-repair"
        for rule in partial_rules
    ):
        raise AssemblyError("self-test partial owner ordering merge omitted the B3 source-order rule")
    partial_plan_events = (
        (partial_plan_record.get("canonical_scaffold") or {}).get("events", [])
        if isinstance(partial_plan_record.get("canonical_scaffold"), dict)
        else []
    )
    if not any(
        event.get("merged_owner_activation_ordering") is True
        and event.get("required_before_added_count") == 1
        for event in partial_plan_events
        if isinstance(event, dict)
    ):
        raise AssemblyError("self-test partial owner ordering merge metadata missing")

    wide_null_curl_states = []
    wide_mrp_resultants = []
    for number in range(1, 7):
        source = f"B{number}"
        if number < 5:
            target = f"B{number + 1}"
            result_type = "held_burden_activation"
            graph = f"{source} -> {target}"
            route = "RECURSE"
            gradient = f"already-held {target} from Initial burden set / B_LA after R(H,Delta)."
            state_extra = f',\n      "next_burden": "{target}",\n      "owner_route": ["held"]'
        elif number == 5:
            target = "B6"
            result_type = "generated_burden_instantiation"
            graph = "B5 -> B6"
            route = "RECURSE"
            gradient = "newly generated B6 absent from B_LA after Delta B5."
            state_extra = ',\n      "next_burden": "B6",\n      "owner_route": ["generated"],\n      "generated_by": "MRP(B5)"'
        else:
            result_type = "no_new_resultant"
            graph = "none"
            route = "STOP"
            gradient = "STOP row is bounded; HOLD/PARTIAL accounting keeps B6 carried-RECURSE."
            state_extra = (
                ',\n      "no_new_resultant_proof": {'
                '"escape_routes_checked": [], '
                '"proved": false, '
                '"basis": "B6 remains carried-RECURSE; no-new-resultant STOP is not licensed for coverage completion."'
                "}"
            )
        finding = "stable" if graph == "none" else "genuine-dependent"
        wide_mrp_resultants.append(
            f'    {{"source": "{source}", "type": "{result_type}", "finding": "{finding}", "graph": "{graph}", "route": "{route}"}}'
        )
        terminal_state = "carried-RECURSE" if number == 6 else "landed"
        wide_null_curl_states.append(
            "    {\n"
            f'      "source_burden": "{source}",\n'
            f'      "prior_land": "Land({source}): terminal state {terminal_state}.",\n'
            f'      "delta": "Delta {source}: terminal state {terminal_state}; MRP route result type {result_type}.",\n'
            '      "reread": "R(H,Delta)",\n'
            f'      "route_gradient": "{gradient}",\n'
            '      "divergence_state": "neutral",\n'
            '      "curl_state": null,\n'
            f'      "route_result_type": "{result_type}",\n'
            f'      "mrp_resultant": "{finding} -> graph {graph}; route {route}",\n'
            f'      "graph_delta": "{graph}",\n'
            '      "preemption_basis": "graph-bound MRP route recorded",\n'
            f'      "route": "{route}"'
            f"{state_extra}\n"
            "    }"
        )
    wide_null_curl_field_witness = (
        "Closure/Reconstruction Witness\n"
        "field_witness\n"
        "{\n"
        '  "B_LA": ["B1", "B2", "B3", "B4", "B5"],\n'
        '  "B_MRP": ["B6"],\n'
        '  "B_total": ["B1", "B2", "B3", "B4", "B5", "B6"],\n'
        '  "mrp_resultants": [\n'
        + ",\n".join(wide_mrp_resultants)
        + "\n  ],\n"
        '  "formal_reread_states": [\n'
        + ",\n".join(wide_null_curl_states)
        + "\n  ],\n"
        '  "coverage_proof": {"divergence_check": "non-neutral", "curl_check": "unresolved", "coverage_complete": false},\n'
        '  "normalized_activation_record": {"n_frame": "self-test", "live_registers": ["xi"], "burden_floor": ["B1", "B2", "B3", "B4", "B5"], "per_burden": []}\n'
        "}\n"
    )
    wide_null_curl_manifest = manifest_for_sections(
        base_dir / "valid-wide-null-curl-normalization",
        case_id="valid-wide-null-curl-normalization",
        source_input="valid-wide-null-curl-normalization/input.md",
        section_specs=[*small_sections()[:6], ("field-witness", "field_witness_nar", wide_null_curl_field_witness)],
    )
    wide_null_curl_record = assemble_manifest(wide_null_curl_manifest, root=root)
    wide_null_curl_output = (
        base_dir / "valid-wide-null-curl-normalization" / "output.md"
    ).read_text(encoding="utf-8")
    if '"curl_state": null' in wide_null_curl_output:
        raise AssemblyError("self-test wide null curl normalization left JSON null curl_state")
    if wide_null_curl_output.count('"curl_state": "null"') != 6:
        raise AssemblyError("self-test wide null curl normalization did not preserve six parser-stable curl_state values")
    wide_null_curl_events = (
        (wide_null_curl_record.get("canonical_scaffold") or {}).get("events", [])
        if isinstance(wide_null_curl_record.get("canonical_scaffold"), dict)
        else []
    )
    if not any(
        event.get("normalized_formal_reread_null_curl_states") == 6
        for event in wide_null_curl_events
        if isinstance(event, dict)
    ):
        raise AssemblyError("self-test wide null curl normalization metadata missing")

    graph_alias_manifest = manifest_for_sections(
        base_dir / "valid-public-graph-alias-canonicalization",
        case_id="valid-public-graph-alias-canonicalization",
        source_input="valid-public-graph-alias-canonicalization/input.md",
        section_specs=small_sections(
            act_text=(
                "Layer B - Bounded Governed Response\n"
                "B1: public source-order burden.\n"
                "B1 [xi] status=initial-live.\n"
                "∇ route pressure is live on B1 through the source-order problem.\n"
                "ACT row body_ref=¹B₁.\n"
                "Contribution-to-Land(B1): visible contribution.\n"
                "Graph-delta reading: there is no B5 generated because B1 is already landed.\n"
                "Land(B1): landed.\n"
            )
        ),
    )
    graph_alias_record = assemble_manifest(graph_alias_manifest, root=root)
    assert_scaffold_events_non_evidence(graph_alias_record, "public graph alias")
    graph_alias_output = (
        base_dir / "valid-public-graph-alias-canonicalization" / "output.md"
    ).read_text(encoding="utf-8")
    for forbidden in ("Land(B1)", "Contribution-to-Land(B1)", "Target: B1", "R(H,Delta)", "no B5 generated"):
        if forbidden in graph_alias_output:
            raise AssemblyError(f"self-test public graph alias canonicalization retained {forbidden}")
    for required in (
        "¹B: public source-order burden.",
        "¹B [xi] status=initial-live.",
        "∇ route pressure is live on ¹B through the source-order problem.",
        "Contribution-to-Land(¹B)",
        "no additional burden 5 generated because ¹B is already landed",
        "Land(¹B)",
        "[Mid-Reread Pressure]",
        "Target: ¹B / bounded self-test burden",
        "R(H,Δ)",
    ):
        if required not in graph_alias_output:
            raise AssemblyError(f"self-test public graph alias canonicalization omitted {required}")
    if '"B_LA": ["B1"]' not in graph_alias_output:
        raise AssemblyError("self-test public graph alias canonicalization changed field_witness JSON machine IDs")
    protected_act_alias = canonicalize_public_graph_alias_line(
        "⟦ACT B5_1[M7.definition-anchor] :: π=logic shifts without anchored predicates :: "
        "body_ref=B5_1 :: Δ=ΔB5:definition-anchored :: Land(B5)+⟧"
    )
    if "Land(additional burden 5)" in protected_act_alias or "body_ref=⁵B" in protected_act_alias:
        raise AssemblyError("self-test public graph alias canonicalization rewrote a machine ACT Land/body_ref row")
    if "Land(⁵B)+" not in protected_act_alias or "body_ref=B5_1" not in protected_act_alias:
        raise AssemblyError("self-test public graph alias canonicalization failed to preserve ACT Land/body_ref identity")
    graph_alias_scaffold = graph_alias_record.get("canonical_scaffold")
    graph_alias_events = (
        graph_alias_scaffold.get("events", [])
        if isinstance(graph_alias_scaffold, dict)
        else []
    )
    if not any(
        event.get("canonicalized_public_graph_aliases") is True
        for event in graph_alias_events
        if isinstance(event, dict)
    ):
        raise AssemblyError("self-test public graph alias canonicalization metadata missing")

    public_submove_sections = list(small_sections())
    public_submove_sections[2] = (
        "act-body",
        "layer_b_act",
        "Layer B - Bounded Governed Response\n"
        "ACT records:\n"
        "⟦ACT B2_2[M9.predication-repair] :: π=predicate-transfer :: body_ref=B2_2 :: Δ=ΔB2:predicate-transfer-blocked :: Land(B2)+⟧\n"
        "⟦ACT B3_1[V10.source-status] :: π=source-stack :: body_ref=B3_1 :: Δ=ΔB3:source-status-ordered :: Land(B3)+⟧\n"
        "### B2_2[M9] - predication repair over predicate-transfer\n"
        "Target: predicate-transfer.\n"
        "Operation: predication-repair blocks category transfer.\n"
        "Result/state-change: predicate-transfer-blocked.\n"
        "Contribution-to-Land(B2): the predicate transfer is blocked.\n"
        "### B2_2[M9] - additional owner operation body\n"
        "Target: additional predication detail.\n"
        "Operation: predication-repair explains retained category consequence.\n"
        "Result/state-change: retained-category-clarified.\n"
        "Contribution-to-Land(B2): additional detail must not become a second body_ref body.\n"
        "### B3_1[V10] - source-status ordering over source-stack\n"
        "Target: source-stack.\n"
        "Operation: source-status orders the cited source stack.\n"
        "Result/state-change: source-stack-ordered.\n"
        "Contribution-to-Land(B3): source status is ordered.\n"
        "Land(B2): landed.\n"
        "Land(B3): landed.\n",
    )
    public_submove_manifest = manifest_for_sections(
        base_dir / "valid-public-submove-heading-canonicalization",
        case_id="valid-public-submove-heading-canonicalization",
        source_input="valid-public-submove-heading-canonicalization/input.md",
        section_specs=public_submove_sections,
        per_burden_reread=self_test_per_burden_chain(["B2", "B3"]),
    )
    public_submove_record = assemble_manifest(public_submove_manifest, root=root)
    assert_scaffold_events_non_evidence(public_submove_record, "public submove")
    public_submove_output = (
        base_dir / "valid-public-submove-heading-canonicalization" / "output.md"
    ).read_text(encoding="utf-8")
    if re.search(r"(?m)^\s*#{1,6}\s*B2_2\[M9\]", public_submove_output):
        raise AssemblyError("self-test public submove canonicalization retained ASCII B2_2 heading")
    if re.search(r"(?m)^\s*#{1,6}\s*B3_1\[V10\]", public_submove_output):
        raise AssemblyError("self-test public submove canonicalization retained ASCII B3_1 heading")
    if len(re.findall(r"(?m)^\s*#{1,6}\s*²B₂\[M9\]", public_submove_output)) != 1:
        raise AssemblyError("self-test public submove canonicalization did not preserve exactly one B2_2 body")
    if len(re.findall(r"(?m)^\s*#{1,6}\s*³B₁\[V10\]", public_submove_output)) != 1:
        raise AssemblyError("self-test public submove canonicalization did not preserve exactly one B3_1 body")
    if "Additional detail for ²B₂ - additional owner operation body" not in public_submove_output:
        raise AssemblyError("self-test public submove canonicalization did not demote duplicate B2_2 detail")
    public_submove_scaffold = public_submove_record.get("canonical_scaffold")
    public_submove_events = (
        public_submove_scaffold.get("events", [])
        if isinstance(public_submove_scaffold, dict)
        else []
    )
    if not any(
        event.get("canonicalized_public_submove_headings", 0) >= 3
        and event.get("demoted_duplicate_submove_headings") == 1
        for event in public_submove_events
        if isinstance(event, dict)
    ):
        raise AssemblyError("self-test public submove canonicalization metadata missing")

    expect_invalid(
        root,
        base_dir,
        "invalid-under-section-budget",
        lambda payload, _case_dir: payload.__setitem__(
            "section_budgets",
            {
                "schema": SECTION_BUDGET_SCHEMA,
                "target_output_bytes": 0,
                "role_min_bytes": {},
                "min_section_bytes": {"opening": 100_000},
            },
        ),
    )

    expanded_sections = small_sections()
    expanded_sections[0] = (
        "opening",
        "visible_opening",
        "NOETIC FIELD EXECUTION\n" + ("Expanded opening detail.\n" * 80),
    )
    expanded_case_dir = base_dir / "valid-section-budget-with-expansion"
    expanded_manifest = manifest_for_sections(
        expanded_case_dir,
        case_id="valid-section-budget-with-expansion",
        source_input="valid-section-budget-with-expansion/input.md",
        section_specs=expanded_sections,
        section_budgets={
            "schema": SECTION_BUDGET_SCHEMA,
            "target_output_bytes": 0,
            "role_min_bytes": {},
            "min_section_bytes": {"opening": 1_000},
        },
    )
    expansion_path = expanded_case_dir / "expansions" / "opening-round-1.md"
    expansion_path.parent.mkdir(parents=True, exist_ok=True)
    expansion_path.write_text("Expanded opening detail.\n" * 40, encoding="utf-8", newline="\n")
    expanded_payload = read_json(expanded_manifest)
    if not isinstance(expanded_payload, dict):
        raise AssertionError("expanded self-test manifest payload must be an object")
    expanded_payload["section_expansions"] = {
        "schema": SECTION_EXPANSIONS_SCHEMA,
        "rounds_allowed": 1,
        "records": [
            {
                "section_id": "opening",
                "role": "visible_opening",
                "round": 1,
                "path": expansion_path.relative_to(expanded_case_dir).as_posix(),
                "sha256": sha256_file(expansion_path),
            }
        ],
    }
    write_json(expanded_manifest, expanded_payload)
    expanded_record = assemble_manifest(expanded_manifest, root=root)
    if not expanded_record.get("section_budgets") or not expanded_record.get("section_expansions"):
        raise AssemblyError("self-test section budget/expansion metadata was not recorded")

    expect_invalid(
        root,
        base_dir,
        "invalid-expansion-forbidden-claim",
        lambda payload, case_dir: (
            replace_section_text(
                payload,
                case_dir,
                0,
                "NOETIC FIELD EXECUTION\nGitHub Release asset proof claim.\n",
            ),
            payload.__setitem__(
                "section_budgets",
                {
                    "schema": SECTION_BUDGET_SCHEMA,
                    "target_output_bytes": 0,
                    "role_min_bytes": {},
                    "min_section_bytes": {"opening": 1},
                },
            ),
        ),
    )

    def assemble_partition_case(
        name: str,
        act_sections: list[tuple[str, str, str]],
        assignments: list[tuple[str, list[str]]],
        *,
        valid: bool,
        per_burden: list[dict[str, Any]] | None = None,
    ) -> None:
        manifest = manifest_for_sections(
            base_dir / name,
            case_id=name,
            source_input=f"{name}/input.md",
            section_specs=[*small_sections()[:2], *act_sections, *small_sections()[3:]],
            act_partition=act_partition_payload(assignments),
            per_burden_reread=per_burden,
        )
        try:
            assemble_manifest(manifest, root=root)
        except AssemblyError:
            if valid:
                raise
            return
        if not valid:
            raise AssemblyError(f"self-test expected invalid ACT partition to fail: {name}")

    assemble_partition_case(
        "valid-act-partition-disjoint",
        [
            act_section("act-body-1", "B1_1", land_burdens=[]),
            act_section("act-body-2", "B1_2", land_burdens=["B1"]),
        ],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_2"])],
        valid=True,
    )
    assemble_partition_case(
        "valid-act-partition-declared-generated",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", "B2_1")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B2_1"])],
        valid=True,
        per_burden=self_test_per_burden_chain(["B1", "B2"]),
    )
    assemble_partition_case(
        "valid-act-partition-contiguous-burden-groups",
        [act_section("act-body-1", "B1_1", "B1_2"), act_section("act-body-2", "B2_1", "B2_2", "B3_1")],
        [("act-body-1", ["B1_1", "B1_2"]), ("act-body-2", ["B2_1", "B2_2", "B3_1"])],
        valid=True,
        per_burden=self_test_per_burden_chain(["B1", "B2", "B3"]),
    )
    assemble_partition_case(
        "valid-act-partition-unicode-contiguous-burden-groups",
        [act_section("act-body-1", "¹B₁", "¹B₂", "¹B₃"), act_section("act-body-2", "²B₁", "²B₂")],
        [("act-body-1", ["¹B₁", "¹B₂", "¹B₃"]), ("act-body-2", ["²B₁", "²B₂"])],
        valid=True,
        per_burden=self_test_per_burden_chain(["B1", "B2"]),
    )
    assemble_partition_case(
        "invalid-act-partition-spliced-burden-groups",
        [
            act_section("act-body-1", "B1_1", "B3_1", land_burdens=["B3"]),
            act_section("act-body-2", "B1_2", "B2_1", land_burdens=["B1", "B2"]),
        ],
        [("act-body-1", ["B1_1", "B3_1"]), ("act-body-2", ["B1_2", "B2_1"])],
        valid=False,
        per_burden=self_test_per_burden_chain(["B1", "B2", "B3"]),
    )
    assemble_partition_case(
        "invalid-act-partition-unicode-burden-submove-axis-swap",
        [
            act_section("act-body-1", "¹B₁", "²B₁", "³B₁", land_burdens=["B3"]),
            act_section("act-body-2", "¹B₂", "²B₂", land_burdens=["B1", "B2"]),
        ],
        [("act-body-1", ["¹B₁", "²B₁", "³B₁"]), ("act-body-2", ["¹B₂", "²B₂"])],
        valid=False,
        per_burden=self_test_per_burden_chain(["B1", "B2", "B3"]),
    )
    assemble_partition_case(
        "invalid-act-partition-duplicate-visible",
        [
            act_section("act-body-1", "B1_1", land_burdens=[]),
            act_section("act-body-2", "B1_1", land_burdens=["B1"]),
        ],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_1"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-missing-assigned",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", land_burdens=[])],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_2"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-unassigned-visible",
        [
            act_section("act-body-1", "B1_1", land_burdens=[]),
            act_section("act-body-2", "B1_2", land_burdens=["B1"]),
        ],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B2_1"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-section-emits-all-rows",
        [
            act_section("act-body-1", "B1_1", "B1_2", land_burdens=[]),
            act_section("act-body-2", "B1_2", land_burdens=["B1"]),
        ],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_2"])],
        valid=False,
    )

    expect_invalid(
        root,
        base_dir,
        "invalid-missing-per-burden-reread",
        lambda payload, _case_dir: payload.pop(PER_BURDEN_REREAD_FIELD),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-per-burden-missing-field",
        lambda payload, _case_dir: payload[PER_BURDEN_REREAD_FIELD][0].pop("finding"),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-per-burden-missing-pressure-slot",
        lambda payload, _case_dir: payload[PER_BURDEN_REREAD_FIELD][0]["pressure_activations"].pop("dependency-tug"),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-per-burden-placeholder-pressure-slot",
        lambda payload, _case_dir: payload[PER_BURDEN_REREAD_FIELD][0]["pressure_activations"].__setitem__(
            "dependency-tug", "none"
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-per-burden-preemption-literal",
        lambda payload, _case_dir: payload[PER_BURDEN_REREAD_FIELD][0].__setitem__(
            "preemption_basis", "terminal states landed; B_MRP empty; no generated burden remains"
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-model-authored-mrp-heading",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            2,
            "Layer B - Bounded Governed Response\n"
            "ACT row body_ref=¹B₁.\n"
            "\n"
            "[Mid-Reread Pressure]\n"
            "Target: ¹B\n"
            "Land(¹B): landed.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-gate-without-entry",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            2,
            "Layer B - Bounded Governed Response\n"
            "ACT row body_ref=¹B₁.\n"
            "Land(¹B): landed.\n"
            "ACT row body_ref=²B₁.\n"
            "Land(²B): landed.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-entry-without-gate",
        lambda payload, _case_dir: payload[PER_BURDEN_REREAD_FIELD][0].__setitem__("burden_id", "B2"),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-duplicate-land-gate",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            2,
            "Layer B - Bounded Governed Response\n"
            "ACT row body_ref=¹B₁.\n"
            "Land(¹B): landed.\n"
            "Additional bounded detail.\n"
            "Land(¹B): landed.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-gate-outside-act-section",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            4,
            "Restorative Response\nRestored orientation.\nLand(¹B): landed.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-missing-section",
        lambda payload, _case_dir: payload.__setitem__(
            "sections", [section for section in payload["sections"] if section["role"] != "mrp_reread_terminal"]
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-hash-mismatch",
        lambda payload, _case_dir: payload["sections"][0].__setitem__("sha256", "0" * 64),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-out-of-order",
        lambda payload, _case_dir: payload.__setitem__(
            "sections", [payload["sections"][6], *payload["sections"][:6]]
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-path-escape",
        lambda payload, _case_dir: payload["sections"][0].__setitem__("path", "../escape.md"),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-missing-visible-opening",
        lambda payload, case_dir: replace_section_text(payload, case_dir, 0, "Opening without noetic header.\n"),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-missing-field-witness-nar",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            6,
            "Closure/Reconstruction Witness\nField Witness prose only.\nNormalized Activation Record prose only.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-missing-closing-formulation",
        lambda payload, _case_dir: payload.__setitem__(
            "sections", [section for section in payload["sections"] if section["role"] != "closing_formulation"]
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-restorative-embedded-decoration",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            4,
            "This paragraph mentions **Restorative Response** but is not a heading.\nRestored orientation.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-restorative-malformed-decoration",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            4,
            "**Restorative Response*\nRestored orientation.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-closing-malformed-decoration",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            5,
            "__Closing Formulation_\nScoped boundary.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-under-target-size",
        lambda payload, _case_dir: payload["output"].__setitem__("target_output_kb", 100),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-duplicate-required-role",
        lambda payload, _case_dir: payload["sections"].insert(1, dict(payload["sections"][0])),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-duplicate-restorative-heading-in-section",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            4,
            "Restorative Response\nRestored orientation.\n\nRestorative Response\nSecond restorative tail.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-closure-witness-inside-closing-section",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            5,
            "Closing Formulation\nScoped close.\n\nClosure/Reconstruction Witness\nPremature proof tail.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-harness-commentary",
        lambda payload, case_dir: replace_section_text(
            payload, case_dir, 0, "You are executing stage-07-release-output.\n"
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-package-provenance-claim",
        lambda payload, case_dir: replace_section_text(
            payload, case_dir, 5, "This publishes provenance in a GitHub Release.\n"
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-guaranteed-uptake-claim",
        lambda payload, case_dir: replace_section_text(
            payload, case_dir, 5, "T_lang guarantees interlocutor uptake.\n"
        ),
    )
    valid_nonclaim_dir = base_dir / "valid-guaranteed-uptake-nonclaim"
    valid_nonclaim_manifest = manifest_for_sections(
        valid_nonclaim_dir,
        case_id="valid-guaranteed-uptake-nonclaim",
        source_input="valid-guaranteed-uptake-nonclaim/input.md",
        section_specs=small_sections(),
    )
    valid_nonclaim_payload = read_json(valid_nonclaim_manifest)
    if not isinstance(valid_nonclaim_payload, dict):
        raise AssemblyError("self-test valid nonclaim manifest payload must be an object")
    replace_section_text(
        valid_nonclaim_payload,
        valid_nonclaim_dir,
        5,
        "Closing Formulation\n"
        "This scoped close does not claim that this formulation guarantees uptake by the interlocutor.\n",
    )
    write_json(valid_nonclaim_manifest, valid_nonclaim_payload)
    assemble_manifest(valid_nonclaim_manifest, root=root)
    valid_may_not_say_nonclaim_dir = base_dir / "valid-guaranteed-uptake-may-not-say-nonclaim"
    valid_may_not_say_nonclaim_manifest = manifest_for_sections(
        valid_may_not_say_nonclaim_dir,
        case_id="valid-guaranteed-uptake-may-not-say-nonclaim",
        source_input="valid-guaranteed-uptake-may-not-say-nonclaim/input.md",
        section_specs=small_sections(),
    )
    valid_may_not_say_nonclaim_payload = read_json(valid_may_not_say_nonclaim_manifest)
    if not isinstance(valid_may_not_say_nonclaim_payload, dict):
        raise AssemblyError("self-test valid may-not-say uptake nonclaim manifest payload must be an object")
    replace_section_text(
        valid_may_not_say_nonclaim_payload,
        valid_may_not_say_nonclaim_dir,
        5,
        "Closing Formulation\n"
        "This closes the public burden at the assertion level. It may not say: this particular "
        "person's inward state is known, that every non-believer has identical culpability, "
        "or that the answer guarantees uptake.\n",
    )
    write_json(valid_may_not_say_nonclaim_manifest, valid_may_not_say_nonclaim_payload)
    assemble_manifest(valid_may_not_say_nonclaim_manifest, root=root)
    expect_invalid(
        root,
        base_dir,
        "invalid-sidecar-proof-claim",
        lambda payload, case_dir: replace_section_text(payload, case_dir, 5, "Stage 8 sidecar proof PASS.\n"),
    )
    valid_sidecar_nonclaim_dir = base_dir / "valid-sidecar-proof-nonclaim"
    valid_sidecar_nonclaim_manifest = manifest_for_sections(
        valid_sidecar_nonclaim_dir,
        case_id="valid-sidecar-proof-nonclaim",
        source_input="valid-sidecar-proof-nonclaim/input.md",
        section_specs=small_sections(),
    )
    valid_sidecar_nonclaim_payload = read_json(valid_sidecar_nonclaim_manifest)
    if not isinstance(valid_sidecar_nonclaim_payload, dict):
        raise AssemblyError("self-test valid sidecar nonclaim manifest payload must be an object")
    replace_section_text(
        valid_sidecar_nonclaim_payload,
        valid_sidecar_nonclaim_dir,
        5,
        "Closing Formulation\n"
        "Stage 05 does not create public sources, verifier sidecars, release proof, "
        "or downstream artifacts.\n",
    )
    write_json(valid_sidecar_nonclaim_manifest, valid_sidecar_nonclaim_payload)
    assemble_manifest(valid_sidecar_nonclaim_manifest, root=root)
    valid_release_nonclaim_dir = base_dir / "valid-release-provenance-nonclaim"
    valid_release_nonclaim_manifest = manifest_for_sections(
        valid_release_nonclaim_dir,
        case_id="valid-release-provenance-nonclaim",
        source_input="valid-release-provenance-nonclaim/input.md",
        section_specs=small_sections(),
    )
    valid_release_nonclaim_payload = read_json(valid_release_nonclaim_manifest)
    if not isinstance(valid_release_nonclaim_payload, dict):
        raise AssemblyError("self-test valid release/provenance nonclaim manifest payload must be an object")
    replace_section_text(
        valid_release_nonclaim_payload,
        valid_release_nonclaim_dir,
        1,
        "Layer A - Diagnostic IR\n"
        "Non-claim: Layer A records diagnostic state and burden floor only; it is not "
        "downstream proof, release evidence, provenance proof, or a guarantee of uptake.\n",
    )
    write_json(valid_release_nonclaim_manifest, valid_release_nonclaim_payload)
    assemble_manifest(valid_release_nonclaim_manifest, root=root)

    def parity_text(entries: list[dict[str, Any]], rendered: list[dict[str, Any]] | None = None) -> str:
        rendered_entries = rendered if rendered is not None else entries
        parts = ["Layer B - Bounded Governed Response"]
        for entry in rendered_entries:
            public = public_burden_token(str(entry["burden_id"])[1:])
            parts.append(f"Land({public}): landed.")
            parts.append("")
            parts.append(render_mrp_block(entry))
            parts.append("")
        return "\n".join(parts) + "\n"

    parity_entries = self_test_per_burden_chain(["B1", "B2"])
    if visible_block_parity_errors(parity_text(parity_entries), parity_entries):
        raise AssemblyError("self-test parity rejected a faithful record-rendered surface")
    public_alias_entry = self_test_per_burden_entry("B5")
    public_alias_entry["reread"] = (
        "R(H,Δ): held routes rechecked: B1-B4 already landed; live remainder: B5 closes."
    )
    public_alias_entry["pressure_activations"] = dict(public_alias_entry["pressure_activations"])
    public_alias_entry["pressure_activations"][
        "dependency-tug"
    ] = "P1: reread finds B1-B4 already landed while B5 remains the local closure target."
    public_alias_entry["mrp_resultant"] = "none / B5 produces no generated burden and no remaining dependency edge"
    public_alias_block = render_mrp_block(public_alias_entry)
    public_alias_probe = re.sub(r"(?i)Delta\(\s*B[1-9][0-9]*\s*\)", "", public_alias_block)
    if re.search(r"\bB[1-9][0-9]*\b", public_alias_probe):
        raise AssemblyError("self-test MRP renderer leaked public ASCII burden aliases")
    if "¹B-⁴B" not in public_alias_block or "⁵B" not in public_alias_block:
        raise AssemblyError("self-test MRP renderer failed to publicize burden range prose")
    generic_edge_probe = public_per_burden_text_value(
        "no remaining chronology edge because the operation produced no remaining Bn -> Bm edge"
    )
    if "Bn" in generic_edge_probe or "Bm" in generic_edge_probe or "->" in generic_edge_probe:
        raise AssemblyError("self-test MRP renderer leaked generic Bn -> Bm placeholder prose")
    single_entry = [self_test_per_burden_entry("B1")]
    burden_qualified_delta_entry = self_test_per_burden_entry("B1")
    burden_qualified_delta_entry["reread"] = (
        "R(H,DeltaB1): held routes rechecked: none; live remainder: none; release/next: STOP"
    )
    burden_qualified_delta_errors = visible_block_parity_errors(
        parity_text([burden_qualified_delta_entry]),
        [burden_qualified_delta_entry],
    )
    if burden_qualified_delta_errors:
        raise AssemblyError(
            "self-test parity rejected burden-qualified Delta reread projection: "
            + "; ".join(burden_qualified_delta_errors)
        )

    def parity_must_fail(name: str, text: str, entries: list[dict[str, Any]], needle: str) -> None:
        found = visible_block_parity_errors(text, entries)
        if not found:
            raise AssemblyError(f"self-test parity canary unexpectedly passed: {name}")
        if not any(needle in error for error in found):
            raise AssemblyError(f"self-test parity canary {name} missed expected error {needle!r}: {found}")

    for field_name, needle in (
        ("finding", "Finding diverges"),
        ("route_result_type", "MRP route result type diverges"),
        ("route", "Route diverges"),
        ("graph_delta", "Graph delta diverges"),
        ("preemption_basis", "Pre-emption basis diverges"),
        ("target", "Target diverges"),
        ("landed_delta", "Landed delta diverges"),
        ("route_gradient", "Route-gradient diverges"),
        ("mrp_resultant", "MRP resultant diverges"),
        ("boundary", "Boundary diverges"),
        ("reread", "reread diverges"),
    ):
        drifted = [dict(single_entry[0])]
        drifted[0][field_name] = (
            "B1 -> B2" if field_name == "graph_delta" else f"{drifted[0][field_name]} [surface-drift]"
        )
        parity_must_fail(
            f"visible-{field_name}-drift",
            parity_text(single_entry, rendered=drifted),
            single_entry,
            needle,
        )
    drifted_slot = [dict(single_entry[0])]
    drifted_slot[0]["pressure_activations"] = dict(single_entry[0]["pressure_activations"])
    drifted_slot[0]["pressure_activations"]["dependency-tug"] = "M8 — drifted slot read."
    parity_must_fail(
        "visible-pressure-slot-drift",
        parity_text(single_entry, rendered=drifted_slot),
        single_entry,
        "pressure slot dependency-tug diverges",
    )
    drifted_diag = [dict(single_entry[0])]
    drifted_diag[0]["divergence"] = "∇·B: settled / drifted reason"
    parity_must_fail(
        "visible-divergence-drift",
        parity_text(single_entry, rendered=drifted_diag),
        single_entry,
        "field diagnostics ∇·B diverges",
    )
    missing_block_text = "Layer B - Bounded Governed Response\nLand(¹B): landed.\nNo block follows.\n"
    parity_must_fail("record-without-visible-block", missing_block_text, single_entry, "no visible [Mid-Reread Pressure] block")
    no_record_text = parity_text([self_test_per_burden_entry("B2")])
    parity_must_fail("visible-block-without-record", no_record_text, single_entry, "have no visible Land")
    stray_block_text = render_mrp_block(single_entry[0]) + "\n\n" + parity_text(single_entry)
    parity_must_fail("block-before-any-gate", stray_block_text, single_entry, "before any")
    double_block_text = parity_text(single_entry).replace(
        "Boundary: T_lang does not imply guaranteed uptake.\n",
        "Boundary: T_lang does not imply guaranteed uptake.\n\n" + render_mrp_block(single_entry[0]) + "\n",
        1,
    )
    parity_must_fail("two-blocks-one-window", double_block_text, single_entry, "exactly one is licensed")

    # The exact R1 false-pass shape: the hidden record says stable/no_new_resultant/STOP,
    # the visible block says genuine-dependent/held_burden_activation/RECURSE. Both sides
    # are individually valid under the shared entry contract; only parity may catch it.
    r1_record = [self_test_per_burden_entry("B1")]
    r1_surface = [self_test_per_burden_entry("B1", next_burden_id="B2")]
    if per_burden_reread_entry_errors(r1_record):
        raise AssemblyError("self-test R1 canary record side must be individually valid")
    if per_burden_reread_entry_errors(r1_surface):
        raise AssemblyError("self-test R1 canary surface side must be individually valid")
    r1_errors = visible_block_parity_errors(parity_text(r1_record, rendered=r1_surface), r1_record)
    for needle in (
        "Finding diverges",
        "MRP route result type diverges",
        "Route diverges",
        "Graph delta diverges",
        "Pre-emption basis diverges",
    ):
        if not any(needle in error for error in r1_errors):
            raise AssemblyError(f"self-test R1 false-pass canary missed {needle!r}: {r1_errors}")

    optional_nonclaim_entry = self_test_per_burden_entry("B1")
    optional_nonclaim_entry["pressure_activations"]["reorientation-reminder"] = (
        "coverage gap: no Graphify, ActiveGraph, package, or release proof is claimed."
    )
    if per_burden_reread_entry_errors([optional_nonclaim_entry]):
        raise AssemblyError("self-test rejected explicit optional-tooling proof nonclaim")
    optional_held_nonclaim_entry = self_test_per_burden_entry("B1")
    optional_held_nonclaim_entry["reread"] = (
        "R(H,\u0394\u00b9B): held routes rechecked: case-library retrieval, release provenance, "
        "Graphify proof, and general model behavior remain held; live remainder: none; "
        "release/next: STOP."
    )
    if per_burden_reread_entry_errors([optional_held_nonclaim_entry]):
        raise AssemblyError("self-test rejected held optional-tooling proof nonclaim")
    optional_claim_entry = self_test_per_burden_entry("B1")
    optional_claim_entry["pressure_activations"]["reorientation-reminder"] = (
        "coverage gap: Graphify proof passed this stage-local MRP terminal reread."
    )
    optional_claim_errors = per_burden_reread_entry_errors([optional_claim_entry])
    if not any("Graphify/ActiveGraph proof claim" in error for error in optional_claim_errors):
        raise AssemblyError("self-test accepted positive optional-tooling proof claim")

    print("staged governed output assembly self-test: PASS")
    print(f"self-test run dir: {rel(base_dir, root)}")
    print(f"large output bytes: {large_record['output']['bytes']}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--allow-under-target", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if args.self_test:
        return run_self_test(root)
    if args.manifest is None:
        raise SystemExit("--manifest is required unless --self-test is used")
    record = assemble_manifest(args.manifest, root=root, allow_under_target=args.allow_under_target)
    print("staged governed output assembly: PASS")
    print(f"output: {record['output']['path']}")
    print(f"output sha256: {record['output']['sha256']}")
    print(f"output bytes: {record['output']['bytes']}")
    print(f"hash record: {record['hash_record']['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
