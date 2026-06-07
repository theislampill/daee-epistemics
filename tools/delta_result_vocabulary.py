#!/usr/bin/env python3
"""Load the source-owned owner-local delta_result vocabulary."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VOCABULARY_PATH = ROOT / "atomics" / "skill" / "references" / "diagnostics" / "delta-result-vocabulary.json"


def owner_key_forms(value: str) -> set[str]:
    stripped = str(value or "").strip().strip("[]")
    upper_dash = stripped.upper().replace(" ", "-")
    return {
        stripped,
        upper_dash,
        upper_dash.replace("-", "_"),
    }


def load_delta_result_vocabulary(
    path: Path = VOCABULARY_PATH,
) -> tuple[dict[str, frozenset[str]], dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    owner_families = payload.get("owner_families")
    if not isinstance(owner_families, dict):
        raise ValueError(f"{path}: owner_families must be an object")

    vocabulary: dict[str, frozenset[str]] = {}
    for owner, values in owner_families.items():
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError(f"{path}: owner family keys must be non-empty strings")
        if not isinstance(values, list) or not values:
            raise ValueError(f"{path}: owner family {owner!r} must list at least one token")
        tokens: list[str] = []
        for token in values:
            if not isinstance(token, str) or not token.strip():
                raise ValueError(f"{path}: owner family {owner!r} contains a blank token")
            tokens.append(token.strip())
        if len(set(tokens)) != len(tokens):
            raise ValueError(f"{path}: owner family {owner!r} contains duplicate tokens")
        vocabulary[owner] = frozenset(tokens)

    aliases: dict[str, str] = {}
    raw_aliases = payload.get("owner_aliases") or {}
    if not isinstance(raw_aliases, dict):
        raise ValueError(f"{path}: owner_aliases must be an object when present")
    for alias, target in raw_aliases.items():
        if target not in vocabulary:
            raise ValueError(f"{path}: owner alias {alias!r} targets unknown family {target!r}")
        for form in owner_key_forms(str(alias)):
            aliases[form] = target

    return vocabulary, aliases


DELTA_RESULT_VOCABULARY, DELTA_RESULT_OWNER_ALIASES = load_delta_result_vocabulary()


def load_owner_operation_vocabulary(
    path: Path = VOCABULARY_PATH,
) -> dict[str, frozenset[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    operations = payload.get("owner_operations") or {}
    if not isinstance(operations, dict):
        raise ValueError(f"{path}: owner_operations must be an object when present")
    vocabulary: dict[str, frozenset[str]] = {}
    for owner, values in operations.items():
        if owner not in DELTA_RESULT_VOCABULARY:
            raise ValueError(f"{path}: owner_operations key {owner!r} has no owner_families entry")
        if not isinstance(values, list) or not values:
            raise ValueError(f"{path}: owner_operations {owner!r} must list at least one token")
        tokens: list[str] = []
        for token in values:
            if not isinstance(token, str) or not token.strip():
                raise ValueError(f"{path}: owner_operations {owner!r} contains a blank token")
            tokens.append(token.strip())
        if len(set(tokens)) != len(tokens):
            raise ValueError(f"{path}: owner_operations {owner!r} contains duplicate tokens")
        vocabulary[owner] = frozenset(tokens)
    return vocabulary


OWNER_OPERATION_VOCABULARY = load_owner_operation_vocabulary()
SOURCE_FORMAL_REPAIR_DELTA_OPERATIONS = {
    "authority-order-repaired": "authority-order-repair",
    "source-order-repaired": "source-order-repair",
}
FAMILY_EXECUTION_OWNER_IDS = {
    "DO_ATTRIBUTE": "do-attribute-precision",
    "DO_CHRISTIAN": "do-christian-extensions",
    "DO_SECOND_LOOP": "do-second-loop",
    "DOUBT_SKEPTICISM": "doubt-vs-skepticism",
    "HUSN_AL_NAZAR": "husn-al-nazar-arguments",
    "INDUCTIVE_FITRI": "inductive-fitri-method",
    "PATTERN_PROFILE": "pattern-profiling",
    "PROOF_METHOD": "proof-method-audit",
    "SYMMETRIC_TAQLID": "symmetric-taqlid-check",
}
SOURCE_EXECUTION_OWNER_BY_OPERATION = {
    "authority-order-repair": "authority-order-repair",
    "sort": "authority-order-repair",
    "source-order": "source-status-repair",
    "source-order-repair": "source-status-repair",
}
PROOF_TEXT_HIDDEN_SUPPORT_PRESSURE_TOKENS = ("proof-text", "proof-stack", "backread")
HELD_ROUTE_SIGNAL_KEYS = {
    "body_status",
    "eligibility",
    "owner_body_status",
    "reason",
    "route_state",
    "state",
    "status",
    "terminal_state",
}


def canonical_delta_owner(owner: str) -> str:
    for form in owner_key_forms(owner):
        if form in DELTA_RESULT_OWNER_ALIASES:
            return DELTA_RESULT_OWNER_ALIASES[form]
        if form in DELTA_RESULT_VOCABULARY:
            return form
    return ""


def family_alias_execution_owner(owner: str, operation: str | None = None) -> tuple[str, str]:
    """Return (family, callable_owner) when owner is only a delta family alias."""

    stripped = str(owner or "").strip().strip("[]")
    forms = owner_key_forms(owner)
    operation_token = str(operation or "").strip()
    if "SOURCE" in forms:
        if not operation_token:
            return "", ""
        callable_owner = SOURCE_EXECUTION_OWNER_BY_OPERATION.get(
            operation_token,
            "authority-order-repair or source-status-repair",
        )
        return "SOURCE", callable_owner
    for family, callable_owner in FAMILY_EXECUTION_OWNER_IDS.items():
        if stripped == callable_owner:
            continue
        if family in forms or family.replace("_", "-") in forms:
            return family, callable_owner
    return "", ""


def family_alias_as_executable_owner_errors(
    label: str,
    owner: str,
    operation: str | None = None,
) -> list[str]:
    family, callable_owner = family_alias_execution_owner(owner, operation)
    if not family:
        return []
    return [
        f"{label}: owner token {owner!r} is the {family} delta/register family alias, "
        f"not a callable owner_id; use {callable_owner!r} for executable ACT/Land "
        f"and keep {family!r} only as vocabulary/register classification"
    ]


def load_owner_operation_delta_results(
    path: Path = VOCABULARY_PATH,
) -> dict[str, dict[str, frozenset[str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping = payload.get("owner_operation_delta_results") or {}
    if not isinstance(mapping, dict):
        raise ValueError(f"{path}: owner_operation_delta_results must be an object when present")
    results: dict[str, dict[str, frozenset[str]]] = {}
    for owner, operations in mapping.items():
        family = canonical_delta_owner(str(owner))
        if not family:
            raise ValueError(f"{path}: owner_operation_delta_results key {owner!r} has no owner_families entry")
        if family not in OWNER_OPERATION_VOCABULARY:
            raise ValueError(f"{path}: owner_operation_delta_results key {owner!r} has no owner_operations entry")
        if not isinstance(operations, dict):
            raise ValueError(f"{path}: owner_operation_delta_results {owner!r} must be an object")
        owner_results: dict[str, frozenset[str]] = {}
        for operation, values in operations.items():
            if not isinstance(operation, str) or not operation.strip():
                raise ValueError(f"{path}: owner_operation_delta_results {owner!r} has a blank operation")
            operation_token = operation.strip()
            if operation_token not in OWNER_OPERATION_VOCABULARY[family]:
                raise ValueError(
                    f"{path}: owner_operation_delta_results {owner!r}.{operation_token!r} "
                    "has no owner_operations entry"
                )
            if not isinstance(values, list) or not values:
                raise ValueError(
                    f"{path}: owner_operation_delta_results {owner!r}.{operation_token!r} "
                    "must list at least one delta_result token"
                )
            tokens: list[str] = []
            for token in values:
                if not isinstance(token, str) or not token.strip():
                    raise ValueError(
                        f"{path}: owner_operation_delta_results {owner!r}.{operation_token!r} "
                        "contains a blank token"
                    )
                token_text = token.strip()
                if token_text not in DELTA_RESULT_VOCABULARY[family]:
                    raise ValueError(
                        f"{path}: owner_operation_delta_results {owner!r}.{operation_token!r} "
                        f"uses delta_result {token_text!r} outside {family} vocabulary"
                    )
                tokens.append(token_text)
            if len(set(tokens)) != len(tokens):
                raise ValueError(
                    f"{path}: owner_operation_delta_results {owner!r}.{operation_token!r} "
                    "contains duplicate tokens"
                )
            owner_results[operation_token] = frozenset(tokens)
        results[family] = owner_results
    return results


OWNER_OPERATION_DELTA_RESULTS = load_owner_operation_delta_results()


def delta_result_vocabulary_errors(label: str, owner: str, delta_result: str) -> list[str]:
    family = canonical_delta_owner(owner)
    if not family:
        return []
    token = str(delta_result or "").strip()
    if not token:
        return [f"{label}: delta_result must be a non-empty owner-local token for {family}"]
    vocabulary = DELTA_RESULT_VOCABULARY[family]
    if token not in vocabulary:
        allowed = ", ".join(sorted(vocabulary))
        return [
            f"{label}: delta_result token {token!r} is outside controlled vocabulary "
            f"for {family}; allowed: {allowed}"
        ]
    return []


def pressure_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def source_pressure_delta_errors(label: str, owner: str, pressure: str, delta_result: str) -> list[str]:
    family = canonical_delta_owner(owner)
    if family != "SOURCE":
        return []
    pressure_token = pressure_key(pressure)
    has_hidden_support = (
        "hidden-support" in pressure_token
        or ("hidden" in pressure_token and "support" in pressure_token)
    )
    has_source_recoil = any(token in pressure_token for token in ("recoil", "future-support"))
    if not (has_hidden_support or has_source_recoil):
        return []

    token = str(delta_result or "").strip()
    is_proof_text_hidden_support = has_hidden_support and any(
        marker in pressure_token for marker in PROOF_TEXT_HIDDEN_SUPPORT_PRESSURE_TOKENS
    )
    if is_proof_text_hidden_support:
        if token == "proof-text-hidden-support-blocked":
            return []
        return [
            f"{label}: proof-text/proof-stack hidden-support pressure must use "
            "delta_result token 'proof-text-hidden-support-blocked'"
        ]
    if token == "hidden-support-blocked":
        return []
    return [
        f"{label}: source-order recoil or hidden-support pressure must use "
        "delta_result token 'hidden-support-blocked'"
    ]


def owner_operation_vocabulary_errors(label: str, owner: str, operation: str) -> list[str]:
    family = canonical_delta_owner(owner)
    if not family:
        return []
    token = str(operation or "").strip()
    if not token:
        return [f"{label}: operation must be a non-empty owner-local token for {family}"]
    vocabulary = OWNER_OPERATION_VOCABULARY.get(family)
    if not vocabulary:
        return []
    if token not in vocabulary:
        allowed = ", ".join(sorted(vocabulary))
        return [
            f"{label}: operation token {token!r} is outside controlled operation vocabulary "
            f"for {family}; allowed: {allowed}"
        ]
    return []


def route_is_held_or_partial(route: dict[str, Any]) -> bool:
    for key in HELD_ROUTE_SIGNAL_KEYS:
        value = route.get(key)
        if not isinstance(value, str):
            continue
        normalized = value.strip().upper().replace("_", "-")
        if (
            "HOLD" in normalized
            or "PARTIAL" in normalized
            or "NOT-LOADED" in normalized
            or "INERT" in normalized
        ):
            return True
    return False


def split_owner_operation_token(owner: str, operation: Any = None) -> tuple[str, str]:
    owner_token = str(owner or "").strip().strip("[]")
    operation_token = str(operation or "").strip() if isinstance(operation, str) else ""
    if not owner_token:
        return "", operation_token
    if canonical_delta_owner(owner_token):
        return owner_token, operation_token
    if "." in owner_token:
        owner_part, operation_part = owner_token.split(".", 1)
        if owner_part.strip() and operation_part.strip():
            return owner_part.strip(), operation_token or operation_part.strip()
    return owner_token, operation_token


def owner_operation_delta_result_errors(
    label: str,
    owner: str,
    operation: str,
    delta_result: str,
) -> list[str]:
    family = canonical_delta_owner(owner)
    if not family:
        return []
    operation_token = str(operation or "").strip()
    if not operation_token:
        return []
    allowed = OWNER_OPERATION_DELTA_RESULTS.get(family, {}).get(operation_token)
    if not allowed:
        return []
    token = str(delta_result or "").strip()
    if token in allowed:
        return []
    allowed_text = ", ".join(sorted(allowed))
    return [
        f"{label}: {family}.{operation_token} requires operation-specific delta_result "
        f"{allowed_text!r}; got {token!r}. Family-local delta tokens are hidden transition "
        "states and are not interchangeable surface labels."
    ]


def route_owner_operation_delta_result_errors(
    label: str,
    owner: str,
    operation: str,
    route: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for key in (
        "delta_result",
        "delta_result_floor",
        "delta_result_vocabulary",
        "allowed_delta_results",
        "delta_results",
    ):
        value = route.get(key)
        if value is None:
            continue
        values: list[str] = []
        if isinstance(value, str):
            values = [value]
        elif isinstance(value, list):
            if not all(isinstance(item, str) and item.strip() for item in value):
                errors.append(f"{label}.{key}: delta_result entries must be non-empty strings")
                continue
            values = [item.strip() for item in value]
        else:
            errors.append(f"{label}.{key}: delta_result evidence must be a string or string list")
            continue
        for token in values:
            errors.extend(
                owner_operation_delta_result_errors(
                    f"{label}.{key}",
                    owner,
                    operation,
                    token,
                )
            )
    return errors


def route_owner_vocabulary_errors(label: str, route: dict[str, Any]) -> list[str]:
    if route_is_held_or_partial(route):
        return []
    raw_owner = route.get("owner_id") or route.get("owner")
    if not isinstance(raw_owner, str) or not raw_owner.strip():
        return [f"{label}: owner route must carry a non-empty owner_id"]
    owner, operation = split_owner_operation_token(raw_owner, route.get("operation") or route.get("owner_operation"))
    alias_errors = family_alias_as_executable_owner_errors(label, owner, operation)
    if alias_errors:
        return alias_errors
    family = canonical_delta_owner(owner)
    if not family:
        return [
            f"{label}: executable owner route {raw_owner!r} has no controlled owner family/delta_result vocabulary; "
            "mark the route HOLD/PARTIAL / OWNER-BODY-NOT-LOADED or add source-owned owner vocabulary with canaries"
        ]
    if family not in DELTA_RESULT_VOCABULARY:
        return [f"{label}: executable owner route {raw_owner!r} has no controlled delta_result vocabulary"]
    if family not in OWNER_OPERATION_VOCABULARY:
        return [
            f"{label}: executable owner route {raw_owner!r} has no controlled owner-operation vocabulary; "
            "route labels are not callable ACT owners"
        ]
    if operation:
        errors: list[str] = []
        errors.extend(owner_operation_vocabulary_errors(label, owner, operation))
        errors.extend(route_owner_operation_delta_result_errors(label, owner, operation, route))
        return errors
    return []


def source_formal_delta_operation_errors(
    label: str,
    owner: str,
    operation: str,
    delta_result: str,
) -> list[str]:
    family = canonical_delta_owner(owner)
    if family != "SOURCE":
        return []
    delta_token = str(delta_result or "").strip()
    expected_operation = SOURCE_FORMAL_REPAIR_DELTA_OPERATIONS.get(delta_token)
    if not expected_operation:
        return []
    operation_token = str(operation or "").strip()
    if operation_token == expected_operation:
        return []
    return [
        f"{label}: SOURCE delta_result {delta_token!r} requires operation "
        f"{expected_operation!r}; compact SOURCE repair deltas are typed transition "
        "projections, not proof by generic operation or token presence"
    ]
