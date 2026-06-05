#!/usr/bin/env python3
"""Shared Stage05 terminal-state detail basis contract."""

from __future__ import annotations

from typing import Any


def normalize_terminal_detail_basis(value: Any) -> tuple[Any, str | None]:
    """Return a normalized basis value, or an error message for invalid shape."""
    if value is None:
        return None, None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None, "must be a non-empty string or non-empty list of non-empty strings when present"
        return stripped, None
    if isinstance(value, list):
        if not value:
            return None, "must be a non-empty string or non-empty list of non-empty strings when present"
        normalized: list[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                return (
                    None,
                    "must be a non-empty string or non-empty list of non-empty strings "
                    f"when present; list item {index} is empty or not a string",
                )
            normalized.append(item.strip())
        return normalized, None
    return None, "must be a non-empty string or non-empty list of non-empty strings when present"
