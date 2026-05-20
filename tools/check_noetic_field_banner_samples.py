#!/usr/bin/env python3
"""Validate noetic-field banners and generalized algebraic-control audit text."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FIELD_VALUES = {
    "LOCAL CLAIM",
    "NAMED WORLDVIEW",
    "SOURCE-AUTHENTICATION",
    "MIXED NOETIC FIELD",
}
SOURCE_VALUES = {"NONE EXPLICIT", "IMPLICIT", "EXPLICIT"}
USER_TASK_VALUES = {
    "RESPOND",
    "REFUTE",
    "DIAGNOSE",
    "EXPLAIN",
    "SOURCE-AUTHENTICATION",
    "OTHER",
}
AUTHORITY_VALUES = {"NONE DETECTED", "LIVE"}
STATE_VALUES = {"RECURSE", "PARTIAL", "COMPLETE"}

BANNED_DEPTH_LABELS = (
    "SIMPLE CASE",
    "COMPACT EXECUTION",
    "CANONICAL EXECUTION",
    "HARD CASE",
    "SOURCE-ORDER",
)

UNRESOLVED_MARKERS = (
    "partial",
    "remains live",
    "still live",
    "unresolved",
    "not yet landed",
    "next live burden",
    "held for later",
    "kappa remains",
    "h remains",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _clean_banner_line(raw_line: str) -> str:
    return (
        raw_line.replace("║", "")
        .replace("╔", "")
        .replace("╚", "")
        .replace("═", "")
        .replace("╝", "")
        .replace("╗", "")
        .strip()
    )


def extract_banner(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    stripped = text.lstrip("\ufeff\r\n\t ")
    first_chunk = stripped[:1200]
    if "NOETIC FIELD EXECUTION" not in first_chunk:
        errors.append("missing noetic-field banner near start of output")
    if not stripped.startswith("╔"):
        errors.append("output does not begin with banner box")

    fields: dict[str, str] = {}
    for raw_line in stripped.splitlines()[:16]:
        normalized = _clean_banner_line(raw_line)
        match = re.match(
            r"^(field|user task|external source request|source request|authority frame|state):\s*(.*?)\s*$",
            normalized,
            re.I,
        )
        if match:
            key = match.group(1).lower()
            if key == "source request":
                key = "external source request"
            value = match.group(2).strip().strip("<>").strip()
            fields[key] = value

    expected = {
        "field": FIELD_VALUES,
        "user task": USER_TASK_VALUES,
        "external source request": SOURCE_VALUES,
        "authority frame": AUTHORITY_VALUES,
        "state": STATE_VALUES,
    }
    for key, allowed in expected.items():
        value = fields.get(key)
        if not value:
            errors.append(f"missing banner field: {key}")
            continue
        if "|" in value:
            errors.append(f"banner field {key!r} prints or combines choice-list values: {value!r}")
        if value not in allowed:
            errors.append(f"banner field {key!r} has invalid value {value!r}; allowed={sorted(allowed)}")

    upper_head = first_chunk.upper()
    for label in BANNED_DEPTH_LABELS:
        if label in upper_head:
            errors.append(f"banned depth-licensing banner vocabulary present: {label}")

    return fields, errors


def _closure_errors(text: str, fields: dict[str, str]) -> list[str]:
    errors: list[str] = []
    state = fields.get("state", "")
    lower = text.lower()
    tail = lower[-5000:]
    has_closure = "closure" in tail or "closing formulation" in tail or "restorative response" in tail
    closure_start = max(
        lower.rfind("closing formulation"),
        lower.rfind("closure audit"),
        lower.rfind("restorative response"),
    )
    closure_segment = lower[closure_start:] if closure_start >= 0 else tail

    if state == "COMPLETE":
        if not has_closure:
            errors.append("state COMPLETE without visible closure/restoration section")
        for marker in UNRESOLVED_MARKERS:
            if marker in closure_segment:
                errors.append(f"state COMPLETE conflicts with closure marker {marker!r}")
                break
    elif state == "RECURSE":
        burden_count = len(re.findall(r"(?im)^\s*(?:\*\*)?\s*burden\s+\d+\b", text))
        if burden_count < 2 and "r(h,delta)" not in lower:
            errors.append("state RECURSE without visible same-response recursion evidence")
    elif state == "PARTIAL":
        if "partial" not in lower:
            errors.append("state PARTIAL is not reflected in output")

    return errors


def _expectation_errors(
    fields: dict[str, str],
    expected_fields: set[str] | None,
    expected_user_tasks: set[str] | None,
    expected_source: set[str] | None,
    expected_authority: set[str] | None,
    allowed_states: set[str] | None,
) -> list[str]:
    errors: list[str] = []
    checks = (
        ("field", expected_fields),
        ("user task", expected_user_tasks),
        ("external source request", expected_source),
        ("authority frame", expected_authority),
        ("state", allowed_states),
    )
    for key, allowed in checks:
        if allowed and fields.get(key) not in allowed:
            errors.append(f"banner {key!r} expected one of {sorted(allowed)}, got {fields.get(key)!r}")
    return errors


def _audit_errors(path: Path, require_named_movement_overfit: bool = False) -> list[str]:
    text = _read(path)
    lower = text.lower()
    errors: list[str] = []

    required_sections = (
        "## algebraic control audit",
        "## divergence / curl diagnostic",
        "## divergence / curl operator detection",
    )
    for section in required_sections:
        pattern = rf"(?im)^\s*{re.escape(section)}\s*$"
        if not re.search(pattern, lower):
            errors.append(f"missing audit section: {section}")

    required_concepts = {
        "candidate noetic frames": ("candidate", "noetic frame"),
        "selected primary N": ("selected", "primary", "n"),
        "held N/H": ("held",),
        "live registers": ("live register",),
        "owner/TTP": ("owner", "ttp"),
        "Delta-nB": ("delta-nb", "delta-n b", "delta nB", "Δ¹B", "ΔⁿB"),
        "Delta-kappa": ("delta-kappa", "delta kappa", "Δκ"),
        "kappa/H discharge": ("kappa", "h discharge"),
        "R(H,Delta)": ("r(h,delta",),
        "STOP/PARTIAL/RECURSE/COMPLETE": ("stop", "partial", "recurse", "complete"),
        "anti-symbol-theater": ("symbol theater", "symbol-theater"),
        "divergence diagnostic": ("divergence", "∇·"),
        "curl diagnostic": ("curl", "∇×"),
        "del/nabla aliases": ("del-dot", "del-cross", "nabla dot", "nabla cross"),
        "operator classification": (
            "AUDIT_DIAGNOSTIC_ALLOWED",
            "DEFAULT_COMPACT_STATE_MARKER_ALLOWED",
            "DEFAULT_FORMALISM_EXPOSITION_FORBIDDEN",
            "ORNAMENTAL_RISK",
        ),
        "operator control effect": ("R(H,Delta)", "PARTIAL", "RECURSE", "closure"),
        "dependency expansion/contraction": ("expand", "contract", "dependency"),
        "dependency circulation": ("circulation", "loop"),
        "generalized not hardcoded": ("general", "not hardcoded"),
    }
    any_match_concepts = {"Delta-nB", "Delta-kappa", "anti-symbol-theater", "divergence diagnostic", "curl diagnostic"}
    for label, terms in required_concepts.items():
        normalized_terms = tuple(term.lower() for term in terms)
        if label in any_match_concepts:
            if not any(term in lower for term in normalized_terms):
                errors.append(f"missing algebraic-control audit concept: {label}")
        elif not all(term in lower for term in normalized_terms):
            errors.append(f"missing algebraic-control audit concept: {label}")

    if "secularcompact is the design center" in lower:
        errors.append("audit makes secularcompact the design center")

    if require_named_movement_overfit:
        if not re.search(r"(?im)^\s*## tst / named-movement overfit audit\s*$", lower):
            errors.append("missing audit section: ## TST / Named-Movement Overfit Audit")
        named_movement_concepts = {
            "person/claim/movement distinction": ("person", "claim", "movement"),
            "symbolic frame": ("symbolic",),
            "source request vs authority frame": ("source request", "authority frame"),
            "held motive/fate": ("motive", "fate", "held"),
            "no supernatural conflation": ("supernatural", "conflation"),
            "no automatic moral anti-realism": ("anti-realism", "without", "argument"),
            "Delta sequence": ("delta-nb", "delta-kappa"),
            "R(H,Delta) named-movement reread": ("r(h,delta",),
            "PARTIAL/RECURSE if unresolved": ("partial", "recurse", "unresolved"),
        }
        for label, terms in named_movement_concepts.items():
            if not all(term.lower() in lower for term in terms):
                errors.append(f"missing named-movement overfit audit concept: {label}")

    if re.search(r"allows\s+complete[^.\n]{0,80}(?:unresolved|still live|remains live)", lower):
        errors.append("audit allows COMPLETE despite unresolved live dependencies")

    return errors


def check_output_path(
    path: Path,
    expected_fields: set[str] | None,
    expected_user_tasks: set[str] | None,
    expected_source: set[str] | None,
    expected_authority: set[str] | None,
    allowed_states: set[str] | None,
) -> list[str]:
    text = _read(path)
    fields, errors = extract_banner(text)
    if not errors:
        errors.extend(_closure_errors(text, fields))
        errors.extend(
            _expectation_errors(
                fields,
                expected_fields,
                expected_user_tasks,
                expected_source,
                expected_authority,
                allowed_states,
            )
        )
    return errors


def _parse_set(values: list[str] | None) -> set[str] | None:
    return set(values) if values else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--audit", type=Path, action="append", default=[])
    parser.add_argument("--expect-field", choices=sorted(FIELD_VALUES), action="append")
    parser.add_argument("--expect-user-task", choices=sorted(USER_TASK_VALUES), action="append")
    parser.add_argument("--expect-source-request", choices=sorted(SOURCE_VALUES), action="append")
    parser.add_argument("--expect-authority-frame", choices=sorted(AUTHORITY_VALUES), action="append")
    parser.add_argument("--allowed-state", choices=sorted(STATE_VALUES), action="append")
    parser.add_argument(
        "--require-named-movement-overfit",
        action="store_true",
        help="Require the TST / named-movement overfit audit section when checking audit files.",
    )
    args = parser.parse_args()

    failed = False
    checked = 0
    for path in args.paths:
        checked += 1
        errors = check_output_path(
            path,
            _parse_set(args.expect_field),
            _parse_set(args.expect_user_task),
            _parse_set(args.expect_source_request),
            _parse_set(args.expect_authority_frame),
            _parse_set(args.allowed_state),
        )
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"PASS {path}")

    for path in args.audit:
        checked += 1
        errors = _audit_errors(path, args.require_named_movement_overfit)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"PASS {path}")

    if failed:
        print(f"noetic-field banner/algebraic-control samples: FAIL ({checked} checked)")
        return 1
    print(f"noetic-field banner/algebraic-control samples: PASS ({checked} checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
