#!/usr/bin/env python3
"""Load the source-owned owner-local delta_result vocabulary."""

from __future__ import annotations

import json
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


def canonical_delta_owner(owner: str) -> str:
    for form in owner_key_forms(owner):
        if form in DELTA_RESULT_OWNER_ALIASES:
            return DELTA_RESULT_OWNER_ALIASES[form]
        if form in DELTA_RESULT_VOCABULARY:
            return form
    return ""


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
