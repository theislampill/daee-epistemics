#!/usr/bin/env python3
"""Shared Stage 04 owner/register-axis contract."""

from __future__ import annotations

from typing import Any


REGISTER_AXIS_ALIASES = {
    "N": "N",
    "n": "N",
    "m": "m",
    "mode": "m",
    "tau": "τ",
    "τ": "τ",
    "sigma": "σ",
    "σ": "σ",
    "source-status": "σ",
    "source_status": "σ",
    "heart": "♥",
    "♥": "♥",
    "xi": "ξ",
    "ξ": "ξ",
    "Omega": "Ω",
    "omega": "Ω",
    "Ω": "Ω",
    "mu": "μ",
    "μ": "μ",
    "kappa": "κ",
    "κ": "κ",
    "H": "H",
    "h": "H",
}


OWNER_REGISTER_AXIS_FLOORS = {
    "SOURCE": {"σ", "H", "κ", "μ", "ξ"},
    "source-status-repair": {"σ"},
    "authority-order-repair": {"σ", "ξ"},
    "M3": {"♥", "ξ", "Ω", "μ"},
    "M9": {"μ", "ξ", "Ω"},
    "PATTERN_PROFILE": {"μ", "κ", "σ", "ξ"},
    "pattern-profiling": {"μ", "κ", "σ", "ξ"},
    "V2": {"ξ", "κ", "μ", "Ω"},
    "V2-reconstituting-reason": {"ξ", "κ", "μ", "Ω"},
    "proof-method-audit": {"σ", "ξ", "μ", "κ"},
    "do-second-loop": {"♥", "ξ", "Ω", "κ", "σ"},
    "P3-reason-revelation-tension": {"Ω", "κ", "σ"},
}


OWNER_OPERATION_REGISTER_AXIS_FLOORS = {
    ("do-second-loop", "punishment-proportionality-accountability"): {"♥", "ξ", "Ω", "κ", "σ", "τ"},
    ("proof-method-audit", "proof-family-and-carrier-audit"): {"σ", "ξ", "μ", "κ", "τ"},
    ("proof-method-audit", "proof-route-status-audit"): {"σ", "ξ", "μ", "κ", "τ"},
    ("proof-method-audit", "proof-overreach-audit"): {"σ", "ξ", "μ", "κ", "τ"},
}


def canonicalize_register_axis(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return REGISTER_AXIS_ALIASES.get(value.strip())


def register_axis_floor(owner_id: Any, operation: Any = None) -> set[str] | None:
    owner = str(owner_id or "").strip()
    op = str(operation or "").strip()
    if owner and op:
        floor = OWNER_OPERATION_REGISTER_AXIS_FLOORS.get((owner, op))
        if floor is not None:
            return floor
    return OWNER_REGISTER_AXIS_FLOORS.get(owner)


def register_axis_errors(label: str, owner_id: Any, operation: Any, raw_axis: Any) -> list[str]:
    axis = canonicalize_register_axis(raw_axis)
    if axis is None:
        return [f"{label}.register_axis is required"]
    allowed_axes = register_axis_floor(owner_id, operation)
    if allowed_axes is not None and axis not in allowed_axes:
        owner = str(owner_id or "").strip()
        op = str(operation or "").strip()
        operation_suffix = f".{op}" if op else ""
        return [f"{label}.register_axis {axis!r} is not approved for owner {owner}{operation_suffix}"]
    return []
