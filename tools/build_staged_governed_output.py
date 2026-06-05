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
            r"T_lang\s+guarantees|guarantees\s+interlocutor\s+uptake|guarantees\s+uptake",
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
    return [f"{label}: forbidden {name}" for name, pattern in FORBIDDEN_PATTERNS if pattern.search(text)]


def public_meta_text_errors(text: str, label: str) -> list[str]:
    return [f"{label}: forbidden {name}" for name, pattern in PUBLIC_META_PATTERNS if pattern.search(text)]


def required_surface_errors(text: str) -> list[str]:
    return [
        f"assembled output: missing {label}"
        for label, pattern in SURFACE_PATTERNS
        if pattern.search(text) is None
    ]


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


def canonicalize_field_witness_ordering(text: str) -> tuple[str, dict[str, Any] | None]:
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
    event: dict[str, Any] = merge_owner_activation_ordering(field_witness)
    if roles_inserted:
        event["inserted_owner_activation_ordering_roles"] = roles_inserted
    if null_curl_states:
        event["normalized_formal_reread_null_curl_states"] = null_curl_states
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
    if re.search(r"(?i)\b(?:no|not|without|absent)\b", updated):
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


def normalize_section_scaffold(section_id: str, role: str, text: str) -> tuple[str, dict[str, Any] | None]:
    spec = CANONICAL_ROLE_HEADINGS.get(role)
    ordering_event: dict[str, Any] | None = None
    submove_event: dict[str, Any] | None = None
    if role == "field_witness_nar":
        text, ordering_event = canonicalize_field_witness_ordering(text)
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
        text, scaffold_event = normalize_section_scaffold(section_id, role, original_text)
        text, trimmed_trailing_whitespace_lines = strip_trailing_line_whitespace(text)
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
            "[Mid-Reread Pressure]\n"
            "Target: B1\n"
            "R(H,Delta): held routes rechecked: none; live remainder: none; release/next: closure.\n"
            "MRP route result type: no_new_resultant\n"
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


def act_section(section_id: str, *body_refs: str) -> tuple[str, str, str]:
    rows = [
        f"⟦ACT {body_ref}[M9.repair] :: π=predicate-transfer :: "
        f"body_ref={body_ref} :: Δ=ΔB1:predicate-transfer-blocked :: Land(B1)+⟧"
        for body_ref in body_refs
    ]
    return (
        section_id,
        "layer_b_act",
        "Layer B - Bounded Governed Response\nACT records:\n" + "\n".join(rows) + "\nLand(B1): landed.\n",
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

    small_manifest = manifest_for_sections(
        base_dir / "valid-small",
        case_id="valid-small",
        source_input="valid-small/input.md",
        section_specs=small_sections(),
    )
    small_record = assemble_manifest(small_manifest, root=root)
    if small_record["output"]["bytes"] <= 0:
        raise AssemblyError("self-test valid small assembly wrote an empty output")
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
            ("Layer B - Bounded Governed Response\nACT body_ref=B1.s%s.\nOperation: bounded section work.\nLand(B1): landed.\n" % index) * 900,
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
    )
    large_record = assemble_manifest(large_manifest, root=root)
    if large_record["output"]["bytes"] < 200 * 1024:
        raise AssemblyError("self-test valid large assembly did not reach 200KB")

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
        "Target: MRP(¹B)",
        "R(H,Δ)",
    ):
        if required not in graph_alias_output:
            raise AssemblyError(f"self-test public graph alias canonicalization omitted {required}")
    if '"B_LA": ["B1"]' not in graph_alias_output:
        raise AssemblyError("self-test public graph alias canonicalization changed field_witness JSON machine IDs")
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
    ) -> None:
        manifest = manifest_for_sections(
            base_dir / name,
            case_id=name,
            source_input=f"{name}/input.md",
            section_specs=[*small_sections()[:2], *act_sections, *small_sections()[3:]],
            act_partition=act_partition_payload(assignments),
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
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", "B1_2")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_2"])],
        valid=True,
    )
    assemble_partition_case(
        "valid-act-partition-declared-generated",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", "B2_1")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B2_1"])],
        valid=True,
    )
    assemble_partition_case(
        "valid-act-partition-contiguous-burden-groups",
        [act_section("act-body-1", "B1_1", "B1_2"), act_section("act-body-2", "B2_1", "B2_2", "B3_1")],
        [("act-body-1", ["B1_1", "B1_2"]), ("act-body-2", ["B2_1", "B2_2", "B3_1"])],
        valid=True,
    )
    assemble_partition_case(
        "invalid-act-partition-spliced-burden-groups",
        [act_section("act-body-1", "B1_1", "B3_1"), act_section("act-body-2", "B1_2", "B2_1")],
        [("act-body-1", ["B1_1", "B3_1"]), ("act-body-2", ["B1_2", "B2_1"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-duplicate-visible",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", "B1_1")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_1"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-missing-assigned",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_2"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-unassigned-visible",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", "B1_2")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B2_1"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-section-emits-all-rows",
        [act_section("act-body-1", "B1_1", "B1_2"), act_section("act-body-2", "B1_2")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_2"])],
        valid=False,
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
    expect_invalid(
        root,
        base_dir,
        "invalid-sidecar-proof-claim",
        lambda payload, case_dir: replace_section_text(payload, case_dir, 5, "Stage 8 sidecar proof PASS.\n"),
    )
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
