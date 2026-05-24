#!/usr/bin/env python3
"""Check Shannon/integral-safe finite-fold trace discipline.

This checker does not implement literal entropy, dB, H(Phi), H_fitrah, or an
integral theorem. It verifies the implementable finite fold over B_total:
every burden has terminal accounting, landed burdens have verified activation
and Land contribution facts, generated B_MRP nodes have provenance/edges, and
literal Shannon/integral proof claims are rejected.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path
from typing import Any

from closure_witness_lib import (
    BURDEN_ID_RE,
    extract_embedded_field_witness,
    extract_field_witness,
    field_witness_graph_errors,
    field_witness_ledger,
    field_witness_mrp_resultants,
    normalize_burden_id,
)
from check_formal_reread_state_semantics import (
    CLOSED_STATES,
    complete_claimed,
    coverage_edges,
    generated_burden_sources,
)
from check_mrp_generated_burden import (
    GENERIC_ACT_VALUE_RE,
    UNTRUSTED_ACTIVATION_SELF_CLAIMS,
    graph_burden_id,
    graph_submove_id,
    land_targets,
    strict_owner_family,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "shannon-finite-fold"

LIVE_STATES = {"carried-partial", "carried-recurse", "partial", "hold", "held"}
SHANNON_OVERCLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "truth/meaning/warrant entropy metric",
        re.compile(
            r"(?i)\b(?:shannon\s+)?entropy\s+(?:measures|proves|establishes|reduces|settles)\s+"
            r"(?:truth|meaning|warrant|fitrah|fiṭrah|revelation)"
        ),
    ),
    ("lower entropy proof claim", re.compile(r"(?i)\blower\s+entropy\s+proves\b")),
    ("literal Shannon theorem proof", re.compile(r"(?i)\bliteral\s+Shannon\s+(?:theorem|proof)\b")),
    ("literal integral theorem proof", re.compile(r"(?i)\bliteral\s+integral\s+(?:theorem|proof)\b")),
    ("Collapse integral proof", re.compile(r"(?i)Collapse\((?:Φ|Phi)\)\s*=\s*(?:∫|integral)")),
    ("undefined H(Phi)", re.compile(r"(?i)\bH\((?:Φ|Phi)\)\s*(?:=|<|>|is|minimi|proves|measures)")),
    ("undefined H_fitrah", re.compile(r"(?i)\bH_fi(?:ṭ|t)rah\b.*(?:=|<|>|is|minimi|proves|measures)")),
    ("undefined dB proof", re.compile(r"(?i)\bdB\b.*\b(?:proves|measures|establishes|integral)\b")),
)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def expand_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        raw = str(path)
        if any(char in raw for char in "*?["):
            matches = sorted(Path(match) for match in glob.glob(raw))
            expanded.extend(matches or [path])
        else:
            expanded.append(path)
    return expanded


def public_text(text: str) -> str:
    match = re.search(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\b", text)
    return text[: match.start()] if match else text


def parse_field_witness(path: Path, text: str) -> tuple[dict[str, Any] | None, list[str]]:
    payload = extract_embedded_field_witness(text)
    if payload is None:
        return None, [f"{rel(path)}: field_witness parser-stable JSON payload missing"]
    field_witness = extract_field_witness(payload)
    if field_witness is None:
        return None, [f"{rel(path)}: field_witness object missing"]
    return field_witness, []


def terminal_payloads(field_witness: dict[str, Any]) -> dict[str, dict[str, str]]:
    coverage = field_witness.get("coverage_proof") if isinstance(field_witness.get("coverage_proof"), dict) else {}
    raw = coverage.get("terminal_states")
    if not isinstance(raw, dict):
        raw = field_witness.get("terminal_states")
    if not isinstance(raw, dict):
        return {}
    terminals: dict[str, dict[str, str]] = {}
    for raw_burden, raw_payload in raw.items():
        burden = normalize_burden_id(str(raw_burden))
        if not BURDEN_ID_RE.fullmatch(burden):
            continue
        if isinstance(raw_payload, dict):
            state = str(raw_payload.get("state") or raw_payload.get("status") or "").strip()
            detail = " / ".join(
                str(value).strip()
                for key, value in raw_payload.items()
                if key not in {"state", "status"} and value is not None and str(value).strip()
            )
        else:
            text = str(raw_payload or "").strip()
            state, _, detail = text.partition("/")
            state = state.strip()
            detail = detail.strip()
        terminals[burden] = {"state": state, "detail": detail}
    return terminals


def diagnostic_status(field_witness: dict[str, Any], *keys: str) -> str:
    coverage = field_witness.get("coverage_proof") if isinstance(field_witness.get("coverage_proof"), dict) else {}
    for key in keys:
        value = coverage.get(key)
        if isinstance(value, str) and value.strip():
            return value
    diagnostics = field_witness.get("field_diagnostics")
    if isinstance(diagnostics, dict):
        for key in keys:
            value = diagnostics.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return ""


def status_head(value: str) -> str:
    return re.split(r"[/;]", str(value or "").strip(), maxsplit=1)[0].strip().lower()


def shannon_overclaim_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    scope = public_text(text)
    for label, pattern in SHANNON_OVERCLAIM_PATTERNS:
        if pattern.search(scope):
            errors.append(f"{rel(path)}: literal Shannon/integral overclaim rejected: {label}")
    return errors


def activation_land_target(value: Any) -> str:
    targets = [graph_burden_id(item) for item in land_targets(str(value or ""))]
    return targets[0] if targets else ""


def activation_errors(path: Path, field_witness: dict[str, Any]) -> tuple[dict[str, int], list[str]]:
    errors: list[str] = []
    counts: dict[str, int] = {}
    raw = field_witness.get("owner_activations")
    if not isinstance(raw, list):
        return counts, [f"{rel(path)}: field_witness.owner_activations must be a list for finite-fold verification"]
    for index, item in enumerate(raw, start=1):
        label = f"{rel(path)}: owner_activations[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label}: activation must be a JSON object")
            continue
        self_claims = sorted(UNTRUSTED_ACTIVATION_SELF_CLAIMS.intersection(item))
        if self_claims:
            errors.append(f"{label}: model-authored activation verification fields are not proof: {', '.join(self_claims)}")
        owner = strict_owner_family(str(item.get("owner") or ""))
        if not owner:
            errors.append(f"{label}: owner is not catalogue-backed")
        operation = str(item.get("operation") or "").strip()
        pressure = str(item.get("pressure") or "").strip()
        delta = str(item.get("delta") or "").strip()
        body_ref = graph_submove_id(item.get("body_ref"))
        target = graph_burden_id(item.get("target"))
        land_target = activation_land_target(item.get("land"))
        missing = [
            key
            for key, value in {
                "target": target,
                "operation": operation,
                "pressure": pressure,
                "body_ref": body_ref,
                "delta": delta,
                "land": land_target,
            }.items()
            if not value
        ]
        if missing:
            errors.append(f"{label}: missing finite-fold activation fields: {', '.join(missing)}")
            continue
        if GENERIC_ACT_VALUE_RE.fullmatch(operation) or GENERIC_ACT_VALUE_RE.fullmatch(pressure):
            errors.append(f"{label}: operation/pressure must be concrete, not generic")
        if not re.search(r"(?i)(?:Δ|Delta)", delta):
            errors.append(f"{label}: delta must name a concrete Delta/Δ transition")
        if land_target != target:
            errors.append(f"{label}: land target Land({land_target}) does not match activation target {target}")
        if body_ref and target and not body_ref.startswith(f"{target}_"):
            errors.append(f"{label}: body_ref {body_ref!r} does not belong to target {target}")
        if target:
            counts[target] = counts.get(target, 0) + 1
    return counts, errors


def resultant_has_generated_edge(item: dict[str, str], source: str, target: str) -> bool:
    graph = str(item.get("graph") or "").replace(" ", "")
    return f"{source}->{target}" in graph


def finite_fold_errors(path: Path, text: str) -> list[str]:
    errors = shannon_overclaim_errors(path, text)
    field_witness, found = parse_field_witness(path, text)
    errors.extend(found)
    if field_witness is None:
        return errors

    prefix = f"{rel(path)}: "
    errors.extend(prefix + error for error in field_witness_graph_errors(field_witness))
    ledgers = field_witness_ledger(field_witness)
    b_total = ledgers["B_total"]
    if not b_total:
        errors.append(f"{rel(path)}: finite fold requires non-empty B_total")
    b_total_set = set(b_total)
    terminals = terminal_payloads(field_witness)
    activation_counts, activation_found = activation_errors(path, field_witness)
    errors.extend(activation_found)

    claims_complete = complete_claimed(field_witness)
    for burden in b_total:
        terminal = terminals.get(burden)
        if terminal is None:
            errors.append(f"{rel(path)}: finite fold missing terminal accounting for {burden}")
            continue
        state = terminal.get("state", "").strip()
        state_key = state.lower()
        detail = terminal.get("detail", "").strip()
        if state in CLOSED_STATES or state_key in CLOSED_STATES:
            if state_key == "landed" and activation_counts.get(burden, 0) < 1:
                errors.append(f"{rel(path)}: landed fold node {burden} lacks owner activation/Land contribution evidence")
            continue
        if state_key in LIVE_STATES:
            if not detail:
                errors.append(f"{rel(path)}: live finite-fold terminal {burden}:{state} must name the remaining pressure/reason")
            if claims_complete:
                errors.append(f"{rel(path)}: complete closure cannot claim finite fold over live terminal {burden}:{state}")
            continue
        errors.append(f"{rel(path)}: finite fold terminal {burden}:{state} is neither closed nor honest HOLD/PARTIAL")

    generated_sources = generated_burden_sources(field_witness)
    resultants = field_witness_mrp_resultants(field_witness)
    coverage_edge_set = set(coverage_edges(field_witness))
    for burden in ledgers["B_MRP"]:
        source = generated_sources.get(burden)
        if not source:
            errors.append(f"{rel(path)}: B_MRP node {burden} lacks generated_burdens provenance")
            continue
        if source not in b_total_set:
            errors.append(f"{rel(path)}: generated source {source} for {burden} is outside B_total")
        matches = [
            item
            for item in resultants
            if item.get("source") == source and item.get("type") == "generated_burden_instantiation"
        ]
        if not matches:
            errors.append(f"{rel(path)}: B_MRP node {burden} lacks generated_burden_instantiation resultant from MRP({source})")
        elif not any(resultant_has_generated_edge(item, source, burden) for item in matches):
            errors.append(f"{rel(path)}: generated resultant MRP({source}) lacks graph edge {source}->{burden}")
        if coverage_edge_set and (source, burden) not in coverage_edge_set:
            errors.append(f"{rel(path)}: coverage graph lacks generated edge {source}->{burden}")
    for burden in sorted(set(generated_sources) - set(ledgers["B_MRP"])):
        errors.append(f"{rel(path)}: generated_burdens lists {burden} outside B_MRP")

    if claims_complete:
        divergence = status_head(diagnostic_status(field_witness, "divergence_check", "del_dot_B", "del_dot_T"))
        curl = status_head(diagnostic_status(field_witness, "curl_check", "del_cross_kappa", "del_cross_T"))
        if divergence and divergence != "neutral":
            errors.append(f"{rel(path)}: complete finite fold requires neutral divergence, found {divergence!r}")
        if curl and curl not in {"null", "resolved"}:
            errors.append(f"{rel(path)}: complete finite fold requires null/resolved curl, found {curl!r}")
    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0

    for path in valid:
        found = finite_fold_errors(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = finite_fold_errors(path, read_text(path))
        if not found:
            errors.append(f"{rel(path)}: expected-invalid Shannon finite-fold fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in expand_paths(args.outputs):
        if not path.exists():
            errors.append(f"{path}: output path not found")
            continue
        found = finite_fold_errors(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("Shannon finite-fold check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Shannon finite-fold check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
