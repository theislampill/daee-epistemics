#!/usr/bin/env python3
"""Check bounded NLA decode / semantic faithfulness for ACT records.

This is not a universal semantic grader. It treats the checker-derived
CanonicalActivation as the encoded activation, dereferences body_ref, and
checks whether owner, operation, pressure, delta/result, and Land facets can be
recovered from the exact Layer B body and field_witness mirror.
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
from check_mrp_generated_burden import (
    SUB,
    UNTRUSTED_ACTIVATION_SELF_CLAIMS,
    ActRecord,
    canonical_activation_from_record,
    contribution_body,
    contribution_names_land,
    field_body,
    field_body_any,
    graph_burden_id,
    graph_normalized_text,
    graph_submove_id,
    land_targets,
    parse_act_records,
    render_act,
    strict_owner_family,
    submove_block_index,
    submove_block_ref_owner,
    submove_operation_body,
    transition_values_agree,
    visible_keywords,
    GENERIC_ACT_VALUE_RE,
    STATE_CHANGE_RE,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "nla-decode-semantic-faithfulness"


@dataclass(frozen=True)
class DecodedFacets:
    body_ref: str
    owner_family: str
    operation: str
    pressure: str
    delta_result: str
    land_target: str
    body_target: str
    body_owner_family: str
    body_operation: str
    body_result: str
    body_contribution: str
    body_prose: str


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


def public_execution_text(text: str) -> str:
    match = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:Restorative Response|Closing Formulation|"
        r"Closure/Reconstruction Witness|Held-node Accounting|field_witness)\b",
        text,
    )
    return text[: match.start()] if match else text


def parse_field_witness(path: Path, text: str) -> tuple[dict[str, Any] | None, list[str]]:
    payload = extract_embedded_field_witness(text)
    if payload is None:
        return None, [f"{rel(path)}: field_witness parser-stable JSON payload missing"]
    field_witness = extract_field_witness(payload)
    if field_witness is None:
        return None, [f"{rel(path)}: field_witness object missing"]
    return field_witness, []


def target_token_from_submove_ref(ref: str) -> str:
    text = str(ref or "").strip()
    match = re.fullmatch(r"(B\d+)(?:[_\.]\d+)", text)
    if match:
        return match.group(1)
    match = re.fullmatch(rf"(?P<target>.+?)(?:[{SUB}]+|[_\.]\d+)", text)
    return match.group("target") if match else ""


def normalized_words(value: str) -> set[str]:
    normalized = re.sub(r"[-_/]", " ", graph_normalized_text(value).lower())
    return set(re.findall(r"[a-z0-9][a-z0-9']{3,}", normalized))


def keywords_recoverable(label: str, body: str, *, minimum: int = 2) -> bool:
    keywords = visible_keywords(label)
    if not keywords:
        return False
    words = normalized_words(body)
    hits = sum(1 for keyword in keywords if keyword in words)
    return hits >= min(len(keywords), minimum)


def operation_recoverable(operation: str, body_operation: str, body_prose: str) -> bool:
    if GENERIC_ACT_VALUE_RE.fullmatch(operation):
        return False
    operation_norm = graph_normalized_text(operation).lower()
    scope = f"{body_operation}\n{body_prose}"
    if operation_norm and operation_norm in graph_normalized_text(scope).lower():
        return True
    return keywords_recoverable(operation, scope, minimum=2)


def field_witness_activation_by_body_ref(field_witness: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw = field_witness.get("owner_activations")
    if not isinstance(raw, list):
        return {}
    result: dict[str, list[dict[str, Any]]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        body_ref = graph_submove_id(item.get("body_ref"))
        if body_ref:
            result.setdefault(body_ref, []).append(item)
    return result


def activation_mirror_errors(
    path: Path,
    record: ActRecord,
    target: str,
    mirror: dict[str, Any] | None,
) -> list[str]:
    label = f"{rel(path)}: ACT {record.submove_ref}"
    if mirror is None:
        return [f"{label}: field_witness.owner_activations missing mirror for body_ref {record.body_ref}"]

    errors: list[str] = []
    self_claims = sorted(UNTRUSTED_ACTIVATION_SELF_CLAIMS.intersection(mirror))
    if self_claims:
        errors.append(
            f"{label}: model-authored activation verification fields are not proof: "
            + ", ".join(self_claims)
        )

    record_family = strict_owner_family(record.owner)
    mirror_family = strict_owner_family(str(mirror.get("owner") or ""))
    if record_family != mirror_family:
        errors.append(f"{label}: field_witness owner does not decode to ACT owner family")
    if str(mirror.get("operation") or "").strip() != record.operation:
        errors.append(f"{label}: field_witness operation does not match ACT operation")
    if str(mirror.get("pressure") or "").strip() != record.pi:
        errors.append(f"{label}: field_witness pressure does not match ACT pressure")
    if not transition_values_agree(mirror.get("delta"), f"{record.delta}:{record.delta_result}"):
        errors.append(f"{label}: field_witness delta does not match ACT delta/result")
    mirror_land_targets = [graph_burden_id(item) for item in land_targets(str(mirror.get("land") or ""))]
    if target not in mirror_land_targets:
        errors.append(f"{label}: field_witness land does not target Land({target})")
    mirror_target = graph_burden_id(mirror.get("target"))
    if mirror_target and mirror_target != target:
        errors.append(f"{label}: field_witness target {mirror_target} disagrees with ACT Land({target})")
    mirror_ref = graph_submove_id(mirror.get("body_ref"))
    if mirror_ref != graph_submove_id(record.body_ref):
        errors.append(f"{label}: field_witness body_ref does not match ACT body_ref")
    return errors


def decode_facets(path: Path, text: str, record: ActRecord) -> tuple[DecodedFacets | None, list[str]]:
    label = f"{rel(path)}: ACT {record.submove_ref}"
    errors: list[str] = []
    canonical = canonical_activation_from_record(record)
    rendered = render_act(canonical)
    if record.record != rendered:
        errors.append(f"{label}: ACT row does not match checker-rendered CanonicalActivation")
    if record.submove_ref != record.body_ref:
        errors.append(f"{label}: body_ref must equal the encoded submove ref")

    owner_family = strict_owner_family(record.owner)
    if not owner_family:
        errors.append(f"{label}: owner {record.owner!r} is not catalogue-backed")
    if GENERIC_ACT_VALUE_RE.fullmatch(record.operation):
        errors.append(f"{label}: operation is generic and cannot be decoded faithfully")

    land_target_tokens = [graph_burden_id(item) for item in land_targets(record.land)]
    target = land_target_tokens[0] if land_target_tokens else ""
    if not target:
        errors.append(f"{label}: Land clause must name a burden target")
    body_ref_target = graph_submove_id(record.body_ref).split("_", 1)[0]
    if target and body_ref_target and body_ref_target != target:
        errors.append(f"{label}: body_ref {graph_submove_id(record.body_ref)!r} does not belong to Land({target})")

    section = public_execution_text(text)
    raw_target = target_token_from_submove_ref(record.body_ref)
    blocks = submove_block_index(section, raw_target).get(record.body_ref, []) if raw_target else []
    if len(blocks) != 1:
        errors.append(f"{label}: body_ref must dereference to exactly one Layer B submove body")
        return None, errors
    block = blocks[0]
    _block_ref, block_owner = submove_block_ref_owner(block)
    body_owner_family = strict_owner_family(block_owner)
    if owner_family and body_owner_family != owner_family:
        errors.append(f"{label}: body owner {block_owner!r} does not decode to ACT owner family {owner_family}")

    facets = DecodedFacets(
        body_ref=graph_submove_id(record.body_ref),
        owner_family=owner_family,
        operation=record.operation,
        pressure=record.pi,
        delta_result=record.delta_result,
        land_target=target,
        body_target=field_body(block, "Target"),
        body_owner_family=body_owner_family,
        body_operation=field_body_any(block, ("Operation", "What it does")),
        body_result=field_body_any(block, ("Result", "Result/state-change")),
        body_contribution=contribution_body(block),
        body_prose=submove_operation_body(block),
    )
    return facets, errors


def semantic_faithfulness_errors(path: Path, record: ActRecord, facets: DecodedFacets) -> list[str]:
    label = f"{rel(path)}: ACT {record.submove_ref}"
    errors: list[str] = []
    body_scope = "\n".join(
        (
            facets.body_target,
            facets.body_operation,
            facets.body_result,
            facets.body_contribution,
            facets.body_prose,
        )
    )
    result_scope = "\n".join((facets.body_result, facets.body_contribution, facets.body_prose))
    operation_scope = "\n".join((facets.body_operation, facets.body_result, facets.body_contribution, facets.body_prose))

    if not facets.body_target:
        errors.append(f"{label}: dereferenced body missing Target facet")
    if not facets.body_operation:
        errors.append(f"{label}: dereferenced body missing Operation facet")
    if not facets.body_result:
        errors.append(f"{label}: dereferenced body missing Result/state-change facet")
    if not facets.body_contribution:
        errors.append(f"{label}: dereferenced body missing Contribution-to-Land facet")
    if errors:
        return errors

    if not keywords_recoverable(facets.pressure, body_scope):
        errors.append(f"{label}: pressure label is not recoverable from dereferenced body")
    if not operation_recoverable(facets.operation, facets.body_operation, operation_scope):
        errors.append(f"{label}: operation label is not recoverable from dereferenced body")
    if not keywords_recoverable(facets.delta_result, result_scope):
        errors.append(f"{label}: delta/result label is not recoverable from body result or contribution")
    if not STATE_CHANGE_RE.search(result_scope):
        errors.append(f"{label}: body result/contribution lacks a concrete state-change verb")
    if facets.land_target and not contribution_names_land(
        "\n".join((f"Contribution-to-Land({facets.land_target}): {facets.body_contribution}", facets.body_prose)),
        facets.land_target,
    ):
        errors.append(f"{label}: body contribution does not decode to Land({facets.land_target})")
    return errors


def nla_decode_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    field_witness, found = parse_field_witness(path, text)
    errors.extend(found)
    if field_witness is None:
        return errors
    mirrors = field_witness_activation_by_body_ref(field_witness)
    raw_activations = field_witness.get("owner_activations")
    if not isinstance(raw_activations, list):
        errors.append(f"{rel(path)}: field_witness.owner_activations must be a list")

    records, parse_errors = parse_act_records(public_execution_text(text))
    errors.extend(f"{rel(path)}: {message}" for message in parse_errors)
    if not records:
        return errors + [f"{rel(path)}: no visible ACT records to decode"]

    seen_body_refs: set[str] = set()
    for record in records:
        body_ref = graph_submove_id(record.body_ref)
        if body_ref in seen_body_refs:
            errors.append(f"{rel(path)}: duplicate ACT body_ref {body_ref}")
        seen_body_refs.add(body_ref)

        facets, decode_found = decode_facets(path, text, record)
        errors.extend(decode_found)
        target = facets.land_target if facets else ""
        mirror_items = mirrors.get(body_ref, [])
        if len(mirror_items) > 1:
            errors.append(f"{rel(path)}: field_witness.owner_activations has duplicate mirror for {body_ref}")
            mirror = mirror_items[0]
        else:
            mirror = mirror_items[0] if mirror_items else None
        errors.extend(activation_mirror_errors(path, record, target, mirror))
        if facets is not None:
            errors.extend(semantic_faithfulness_errors(path, record, facets))
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
        found = nla_decode_errors(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = nla_decode_errors(path, read_text(path))
        if not found:
            errors.append(f"{rel(path)}: expected-invalid NLA decode fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in expand_paths(args.outputs):
        if not path.exists():
            errors.append(f"{path}: output path not found")
            continue
        found = nla_decode_errors(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("NLA decode semantic-faithfulness check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("NLA decode semantic-faithfulness check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
