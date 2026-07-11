#!/usr/bin/env python3
"""Validate public Layer B burden grouping for governed outputs.

This checker guards the Stage 07 compiled-output failure where ACT sections
were assembled in round-robin order: later burdens appeared before earlier
burden groups had landed, and the public body repeated the main Layer B header.
It validates visible public topology only; structural/notation proof remains owned by the
NLA, field_witness, MRP, graph, manual-render, sidecar, and retained-corpus
validators.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from closure_witness_lib import extract_embedded_field_witness, extract_field_witness
from check_mrp_generated_burden import strict_owner_family
from check_mid_reread_pressure import parse_mrps


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUB = "₀₁₂₃₄₅₆₇₈₉"
SUP_TO_ASCII = str.maketrans(SUP, "0123456789")
SUB_TO_ASCII = str.maketrans(SUB, "0123456789")
ASCII_TO_SUP = str.maketrans("0123456789", SUP)
PUBLIC_ACT_RE = re.compile(
    r"(?m)^\s*(?P<row>⟦ACT\s+(?P<head>[^\s\[]+)\[(?P<owner>[^\].\s]+)(?:\.[^\]]+)?\].*?"
    r"\s+body_ref=(?P<body_ref>[^\s:⟧]+).*?⟧)\s*$"
)
LAYER_B_BOUNDED_RE = re.compile(
    r"(?im)^\s*#{1,6}\s*Layer B\s*[-—?]\s*Bounded Governed Response\b"
)
PUBLIC_TAIL_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:Restorative Response|Closing Formulation|Closure/Reconstruction Witness|field_witness)\b"
)
BURDEN_HEADING_RE = re.compile(
    r"(?im)^\s*#{1,6}\s*Burden\s+(?P<number>\d+)\s*/\s*(?P<token>[^\s\[]+).*?$"
)


@dataclass(frozen=True)
class ActRecord:
    body_ref: str
    burden_id: str
    owner: str
    start: int
    end: int
    row: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def public_burden_token(burden_id: str) -> str:
    match = re.fullmatch(r"B([1-9][0-9]*)", burden_id)
    if not match:
        return burden_id
    return f"{match.group(1).translate(ASCII_TO_SUP)}B"


def normalize_burden_id(value: Any) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"B[1-9][0-9]*", text):
        return text
    match = re.fullmatch(rf"([{SUP}]+)B", text)
    if match:
        return f"B{match.group(1).translate(SUP_TO_ASCII)}"
    match = re.fullmatch(r"([1-9][0-9]*)B", text)
    if match:
        return f"B{match.group(1)}"
    match = re.search(rf"([{SUP}]+)B", text)
    if match:
        return f"B{match.group(1).translate(SUP_TO_ASCII)}"
    match = re.search(r"\bB([1-9][0-9]*)\b", text)
    if match:
        return f"B{match.group(1)}"
    return text


def normalize_body_ref(value: Any) -> str:
    text = str(value or "").strip().rstrip(".,;")
    match = re.fullmatch(rf"([{SUP}]+)B([{SUB}]+)", text)
    if match:
        return f"B{match.group(1).translate(SUP_TO_ASCII)}_{match.group(2).translate(SUB_TO_ASCII)}"
    match = re.fullmatch(r"B([1-9][0-9]*)[_\.]([1-9][0-9]*)", text)
    if match:
        return f"B{match.group(1)}_{match.group(2)}"
    match = re.fullmatch(r"([1-9][0-9]*)B([1-9][0-9]*)", text)
    if match:
        return f"B{match.group(1)}_{match.group(2)}"
    return text


def body_ref_burden_id(value: Any) -> str:
    normalized = normalize_body_ref(value)
    match = re.fullmatch(r"B([1-9][0-9]*)_[1-9][0-9]*", normalized)
    return f"B{match.group(1)}" if match else ""


def visible_public_body(text: str) -> str:
    matches = list(PUBLIC_TAIL_RE.finditer(text))
    if not matches:
        return text
    return text[: min(match.start() for match in matches)]


def embedded_field_witness(text: str) -> dict[str, Any] | None:
    payload = extract_embedded_field_witness(text)
    return extract_field_witness(payload) if payload is not None else None


def field_owner_body_refs(field_witness: dict[str, Any] | None) -> list[str]:
    if not isinstance(field_witness, dict):
        return []
    activations = field_witness.get("owner_activations")
    if not isinstance(activations, list):
        return []
    refs: list[str] = []
    for item in activations:
        if not isinstance(item, dict):
            continue
        ref = item.get("body_ref")
        if isinstance(ref, str) and ref.strip():
            refs.append(normalize_body_ref(ref))
    return refs


def field_generated_burdens(field_witness: dict[str, Any] | None) -> list[str]:
    if not isinstance(field_witness, dict):
        return []
    values: list[str] = []
    for key in ("B_MRP", "generated_burdens"):
        raw = field_witness.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    values.append(normalize_burden_id(item))
                elif isinstance(item, dict):
                    value = item.get("id") or item.get("target") or item.get("burden_id")
                    if isinstance(value, str):
                        values.append(normalize_burden_id(value))
    ledger = field_witness.get("ledger")
    if isinstance(ledger, dict) and isinstance(ledger.get("B_MRP"), list):
        values.extend(normalize_burden_id(item) for item in ledger["B_MRP"] if isinstance(item, str))
    return list(dict.fromkeys(value for value in values if re.fullmatch(r"B[1-9][0-9]*", value)))


def field_mrp_sources(field_witness: dict[str, Any] | None) -> list[str]:
    if not isinstance(field_witness, dict):
        return []
    resultants = field_witness.get("mrp_resultants")
    if not isinstance(resultants, list):
        return []
    sources: list[str] = []
    for item in resultants:
        if not isinstance(item, dict):
            continue
        source = item.get("source")
        if isinstance(source, str):
            sources.append(normalize_burden_id(source.replace("MRP(", "").replace(")", "")))
    return list(dict.fromkeys(value for value in sources if re.fullmatch(r"B[1-9][0-9]*", value)))


def normalize_owner(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return strict_owner_family(raw) or raw.lower().replace("_", "-")


def field_owner_ordering_edges(field_witness: dict[str, Any] | None) -> list[tuple[str, str, str]]:
    if not isinstance(field_witness, dict):
        return []
    ordering = field_witness.get("owner_activation_ordering")
    if not isinstance(ordering, dict):
        return []
    required = ordering.get("required_before")
    if not isinstance(required, list):
        return []
    edges: list[tuple[str, str, str]] = []
    for item in required:
        if not isinstance(item, dict):
            continue
        target = normalize_burden_id(item.get("target") or item.get("burden") or "")
        before = normalize_owner(item.get("before_owner") or item.get("before"))
        after = normalize_owner(item.get("after_owner") or item.get("after"))
        if re.fullmatch(r"B[1-9][0-9]*", target) and before and after:
            edges.append((target, before, after))
    return edges


def parse_visible_acts(public_body: str) -> list[ActRecord]:
    records: list[ActRecord] = []
    for match in PUBLIC_ACT_RE.finditer(public_body):
        head_ref = normalize_body_ref(match.group("head"))
        field_ref = normalize_body_ref(match.group("body_ref"))
        chosen = field_ref or head_ref
        records.append(
            ActRecord(
                body_ref=chosen,
                burden_id=body_ref_burden_id(chosen),
                owner=normalize_owner(match.group("owner")),
                start=match.start(),
                end=match.end(),
                row=match.group("row").strip(),
            )
        )
    return records


def burden_group_order(records: list[ActRecord]) -> list[str]:
    groups: list[str] = []
    for record in records:
        if not groups or groups[-1] != record.burden_id:
            groups.append(record.burden_id)
    return groups


def standalone_land_re(burden_id: str) -> re.Pattern[str]:
    public = re.escape(public_burden_token(burden_id))
    ascii_id = re.escape(burden_id)
    return re.compile(rf"(?im)^\s*(?!.*Contribution-to-)Land\(\s*(?:{public}|{ascii_id})\s*\)\s*:")


def burden_heading_has_generated_marker(public_body: str, burden_id: str) -> bool:
    public = re.escape(public_burden_token(burden_id))
    ascii_id = re.escape(burden_id)
    for line in public_body.splitlines():
        if not re.search(rf"(?i)^\s*#{{1,6}}\s*Burden\s+{burden_id[1:]}\b", line):
            continue
        if not re.search(public, line) and not re.search(rf"(?i)\b{ascii_id}\b", line):
            continue
        if re.search(r"(?i)\bgenerated-by\s*:\s*MRP\(|\[generated-by:\s*MRP\(", line):
            return True
        if re.search(rf"(?i)\bMRP\(\s*(?:{public}|{ascii_id})\s*\)", line):
            return True
    return False


def validate_text(text: str, label: str) -> list[str]:
    errors: list[str] = []
    public_body = visible_public_body(text)
    layer_b_count = len(LAYER_B_BOUNDED_RE.findall(public_body))
    if layer_b_count != 1:
        errors.append(f"{label}: expected exactly one public Layer B bounded heading, found {layer_b_count}")

    field_witness = embedded_field_witness(text)
    if field_witness is None:
        errors.append(f"{label}: embedded field_witness JSON is required")

    records = parse_visible_acts(public_body)
    if not records:
        errors.append(f"{label}: no visible ACT records found before proof tail")
        return errors
    for record in records:
        if not re.fullmatch(r"B[1-9][0-9]*_[1-9][0-9]*", record.body_ref):
            errors.append(f"{label}: visible ACT body_ref {record.body_ref!r} is not parser-stable")
        if not record.burden_id:
            errors.append(f"{label}: visible ACT row has no parseable burden id: {record.row}")

    visible_counts: dict[str, int] = {}
    for record in records:
        visible_counts[record.body_ref] = visible_counts.get(record.body_ref, 0) + 1
    for ref, count in sorted(visible_counts.items()):
        if count != 1:
            errors.append(f"{label}: visible ACT body_ref {ref} appears {count} times")

    records_by_burden: dict[str, list[ActRecord]] = {}
    for record in records:
        records_by_burden.setdefault(record.burden_id, []).append(record)
    for target, before, after in field_owner_ordering_edges(field_witness):
        owner_order = [record.owner for record in records_by_burden.get(target, []) if record.owner]
        if before not in owner_order or after not in owner_order:
            continue
        if owner_order.index(before) > owner_order.index(after):
            errors.append(
                f"{label}: public ACT owner order for {target} violates field_witness required_before "
                f"{before} -> {after}"
            )

    owner_refs = field_owner_body_refs(field_witness)
    if owner_refs:
        for ref in owner_refs:
            count = visible_counts.get(ref, 0)
            if count != 1:
                errors.append(f"{label}: field_witness owner_activation body_ref {ref} appears {count} times in visible ACT body")
        for ref in sorted(set(visible_counts) - set(owner_refs)):
            errors.append(f"{label}: visible ACT body_ref {ref} lacks field_witness.owner_activations mirror")

    group_order = burden_group_order(records)
    seen_groups: set[str] = set()
    previous_number = 0
    for burden_id in group_order:
        if burden_id in seen_groups:
            errors.append(f"{label}: burden {burden_id} ACT rows are not contiguous")
        seen_groups.add(burden_id)
        match = re.fullmatch(r"B([1-9][0-9]*)", burden_id)
        if match:
            number = int(match.group(1))
            if number < previous_number:
                errors.append(f"{label}: burden {burden_id} appears after a later burden group")
            previous_number = max(previous_number, number)

    by_burden: dict[str, list[ActRecord]] = {}
    for record in records:
        by_burden.setdefault(record.burden_id, []).append(record)
    ordered_burdens = [burden for burden in group_order if burden in by_burden]
    first_start_by_burden = {burden: by_burden[burden][0].start for burden in ordered_burdens}
    for index, burden_id in enumerate(ordered_burdens):
        burden_records = by_burden[burden_id]
        first = burden_records[0]
        last = burden_records[-1]
        next_start = len(public_body)
        if index + 1 < len(ordered_burdens):
            next_start = first_start_by_burden[ordered_burdens[index + 1]]
        land_pattern = standalone_land_re(burden_id)
        premature_region = public_body[first.end : last.start] if last.start > first.end else ""
        if land_pattern.search(premature_region):
            errors.append(f"{label}: Land({burden_id}) appears before the burden's final ACT submove")
        if not land_pattern.search(public_body[last.end : next_start]):
            errors.append(f"{label}: missing standalone Land({burden_id}) after final ACT submove and before next burden")

    public_mrps = parse_mrps(public_body)
    public_mrp_targets = [
        normalize_burden_id(block.target)
        for block in public_mrps
        if isinstance(block.target, str) and block.target.strip()
    ]
    public_mrp_targets = [target for target in public_mrp_targets if re.fullmatch(r"B[1-9][0-9]*", target)]
    mrp_numbers = [int(target[1:]) for target in public_mrp_targets]
    if mrp_numbers != sorted(mrp_numbers):
        errors.append(f"{label}: public MRP targets are out of visible burden order: {public_mrp_targets}")
    field_sources = field_mrp_sources(field_witness)
    if field_sources:
        cursor = 0
        for source in field_sources:
            try:
                cursor = public_mrp_targets.index(source, cursor) + 1
            except ValueError:
                errors.append(f"{label}: field_witness MRP source {source} has no matching public MRP target in order")
                break

    generated = field_generated_burdens(field_witness)
    for burden_id in generated:
        visible_has_burden = any(record.burden_id == burden_id for record in records) or re.search(
            rf"(?i)\bBurden\s+{burden_id[1:]}\b|{re.escape(public_burden_token(burden_id))}", public_body
        )
        if visible_has_burden and not burden_heading_has_generated_marker(public_body, burden_id):
            errors.append(f"{label}: generated burden {burden_id} lacks visible generated-by MRP provenance")

    return errors


def fixture_paths(root: Path, kind: str) -> list[Path]:
    return sorted((root / "tests" / "public-burden-grouping" / kind).glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs", nargs="*", default=None, help="Additional governed outputs to validate")
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    root = Path(args.root)
    valid = fixture_paths(root, "valid")
    invalid = fixture_paths(root, "invalid")
    failures: list[str] = []

    for path in valid:
        errors = validate_text(read_text(path), str(path))
        if errors:
            failures.extend(errors)
    for path in invalid:
        errors = validate_text(read_text(path), str(path))
        if not errors:
            failures.append(f"{path}: invalid fixture unexpectedly passed")

    hosted = [Path(item) for item in args.outputs or []]
    for path in hosted:
        errors = validate_text(read_text(path), str(path))
        if errors:
            failures.extend(errors)

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        print("public burden grouping check: FAIL")
        return 1
    print(
        "public burden grouping: PASS "
        f"({len(valid)} valid fixtures, {len(invalid)} invalid fixtures, {len(hosted)} hosted outputs)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
