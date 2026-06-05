#!/usr/bin/env python3
"""Validate no-model TTP availability versus activation canaries.

This checker is intentionally narrow: it proves that fixture-declared TTP
availability is not treated as activation, while selected/applicable owners
still have concrete ACT/body_ref/owner_activation/NAR/reread surfaces.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "ttp-availability"
VALID_DIR = FIXTURE_ROOT / "valid"
INVALID_DIR = FIXTURE_ROOT / "invalid"
MODULE_CATALOGUE = ROOT / "atomics" / "skill" / "references" / "diagnostics" / "module-catalogue.json"
DELTA_VOCABULARY = ROOT / "atomics" / "skill" / "references" / "diagnostics" / "delta-result-vocabulary.json"

SCHEMA = "ttp-availability-canary-v1"
PASS_THROUGH_GUIDANCE = {"V1", "V1-diagnostic", "heuristics"}
HELD_GENERATED_STATE_RE = re.compile(r"(?i)\b(?:held|hold|partial|carried|recurse|unresolved)\b")
EXECUTED_GENERATED_STATE_RE = re.compile(r"(?i)\b(?:landed|executed|resolved)\b")
REQUIRED_SURFACE_KEYS = (
    "act_row",
    "body_ref",
    "body_ref_dereference",
    "owner_activation",
    "nar",
    "field_witness",
    "mrp_reread",
)
OWNER_ALIASES = {
    "authority-order-repair": "SOURCE",
    "do-attribute-precision": "DO_ATTRIBUTE",
    "do-christian-extensions": "DO_CHRISTIAN",
    "doubt-vs-skepticism": "DOUBT_SKEPTICISM",
    "foreign-premise-detection": "FPD",
    "husn-al-nazar": "HUSN_AL_NAZAR",
    "husn-al-nazar-arguments": "HUSN_AL_NAZAR",
    "inductive-fitri": "INDUCTIVE_FITRI",
    "inductive-fitri-method": "INDUCTIVE_FITRI",
    "M1P": "M1-P",
    "M1P-performative-self-refutation": "M1-P",
    "P2-objection-mapping": "P2",
    "P4-maieutic": "P4",
    "P5-already-believing": "P5",
    "P6-universal-aqidah-principle": "P6",
    "source-status-repair": "SOURCE",
    "symmetric-taqlid": "SYMMETRIC_TAQLID",
    "symmetric-taqlid-check": "SYMMETRIC_TAQLID",
    "V3-regress-dissolution": "V3",
    "V6-convergence": "V6",
    "V12-tamanuc-exhaustion": "V12",
}
OWNER_SPECIFIC_BODY_RE = {
    "DO_ATTRIBUTE": re.compile(r"(?i)\b(?:attribute|person|nature|predicate|category|transfer)\b"),
    "DO_CHRISTIAN": re.compile(r"(?i)\b(?:model|trinitarian|route|family|fan[- ]out)\b"),
    "DOUBT_SKEPTICISM": re.compile(r"(?i)\b(?:doubt|skepticism|method|question)\b"),
    "FPD": re.compile(r"(?i)\b(?:foreign|premise|criterion|tribunal|support)\b"),
    "HUSN_AL_NAZAR": re.compile(r"(?i)\b(?:proof|readiness|infer|argument|nazar|evidence)\b"),
    "INDUCTIVE_FITRI": re.compile(r"(?i)\b(?:fitri|inductive|foundation|sign|superstructure)\b"),
    "M1": re.compile(r"(?i)\b(?:self|ground|standard|contradiction|authorize)\b"),
    "M1-P": re.compile(r"(?i)\b(?:performative|speech[- ]act|presupposition|contradiction)\b"),
    "M7": re.compile(r"(?i)\b(?:definition|anchor|semantic|meaning|term)\b"),
    "M8": re.compile(r"(?i)\b(?:dependency|consequence|trace|entail|implication)\b"),
    "M9": re.compile(r"(?i)\b(?:predication|person|nature|referent|sense|category)\b"),
    "P1": re.compile(r"(?i)\b(?:fitrah|tawhid|orientation|restore|worship)\b"),
    "P2": re.compile(r"(?i)\b(?:objection|topology|sequence|mapping)\b"),
    "P3": re.compile(r"(?i)\b(?:reason|revelation|order|stabiliz)\b"),
    "P4": re.compile(r"(?i)\b(?:maieutic|recognition|question|elicit)\b"),
    "P5": re.compile(r"(?i)\b(?:belief|article|strengthen|conviction)\b"),
    "P6": re.compile(r"(?i)\b(?:worldview|aqidah|binding|neutrality|principle)\b"),
    "P7": re.compile(r"(?i)\b(?:scope|boundary|STOP|HOLD|PARTIAL|closure|reopen)\b"),
    "SOURCE": re.compile(r"(?i)\b(?:source|authority|testimony|proof|witness|transmission|status|order)\b"),
    "SYMMETRIC_TAQLID": re.compile(r"(?i)\b(?:taqlid|symmetric|imitation|authority|parity)\b"),
    "V3": re.compile(r"(?i)\b(?:regress|dissolve|infinite|grounding)\b"),
    "V6": re.compile(r"(?i)\b(?:convergence|register|conflict|integrat)\b"),
    "V12": re.compile(r"(?i)\b(?:exhaust|plurality|tamanuc|refused)\b"),
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def catalogue_tokens() -> set[str]:
    tokens: set[str] = set()
    catalogue = load_json(MODULE_CATALOGUE)
    for entry in catalogue.get("modules") or []:
        if not isinstance(entry, dict):
            continue
        for key in ("id", "owner_family"):
            value = str(entry.get(key) or "").strip()
            if value:
                tokens.add(value)
        for alias in entry.get("aliases") or []:
            value = str(alias or "").strip()
            if value:
                tokens.add(value)
        path = str(entry.get("path") or "").strip()
        if path:
            tokens.add(Path(path).stem)

    vocabulary = load_json(DELTA_VOCABULARY)
    aliases = vocabulary.get("owner_aliases") or {}
    if isinstance(aliases, dict):
        tokens.update(str(key) for key in aliases)
        tokens.update(str(value) for value in aliases.values())
    families = vocabulary.get("owner_families") or {}
    if isinstance(families, dict):
        tokens.update(str(key) for key in families)

    for number in range(1, 13):
        tokens.add(f"M{number}")
        tokens.add(f"V{number}")
    for number in range(1, 8):
        tokens.add(f"P{number}")
    tokens.update({"M1-P", "M1P", "FPD", "SOURCE"})
    return tokens


CATALOGUE_TOKENS = catalogue_tokens()


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def owner_known(owner: str) -> bool:
    return owner in CATALOGUE_TOKENS


def explicit_owner_contract_for(data: dict[str, Any], owner: str) -> bool:
    contracts = data.get("explicit_owner_contracts")
    if not isinstance(contracts, dict):
        return False
    contract = contracts.get(owner)
    if not isinstance(contract, dict):
        return False
    return contract.get("load_bearing_layer_b_act") is True


def surface_owner(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if isinstance(value, dict):
        return str(value.get("owner") or value.get("owner_id") or "").strip()
    return str(value or "").strip()


def surface_body_ref(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if isinstance(value, dict):
        return str(value.get("body_ref") or "").strip()
    return str(value or "").strip()


def row_owner(row: dict[str, Any]) -> str:
    return str(row.get("owner") or "").strip()


def owner_family_token(owner: str) -> str:
    token = owner.strip()
    if token in OWNER_ALIASES:
        return OWNER_ALIASES[token]
    upper = token.upper()
    if upper in OWNER_ALIASES:
        return OWNER_ALIASES[upper]
    if re.fullmatch(r"M\d+(?:-P)?|P\d+|V\d+|FPD|SOURCE", upper):
        return upper
    return token


def act_mentions_owner_and_ref(row: dict[str, Any], owner: str, body_ref: str) -> bool:
    act = str(row.get("act_row") or "")
    if not act or not body_ref:
        return False
    return f"[{owner}" in act and f"body_ref={body_ref}" in act and "Land(" in act


def row_is_complete(row: dict[str, Any], owner: str) -> list[str]:
    errors: list[str] = []
    body_ref = surface_body_ref(row, "body_ref")
    if not act_mentions_owner_and_ref(row, owner, body_ref):
        errors.append(f"{owner}: ACT row must name owner, body_ref={body_ref}, and Land(...)")

    deref = row.get("body_ref_dereference")
    if not isinstance(deref, dict):
        errors.append(f"{owner}: body_ref_dereference must be an object")
    else:
        if str(deref.get("body_ref") or "").strip() != body_ref:
            errors.append(f"{owner}: body_ref_dereference must match body_ref")
        if str(deref.get("owner") or "").strip() != owner:
            errors.append(f"{owner}: body_ref_dereference must carry selected owner")
        body = " ".join(str(deref.get(key) or "") for key in ("target", "operation", "result", "contribution"))
        if not re.search(r"(?i)\b(?:target|pressure|operation|result|delta|land|bounded|exposed|routed|separated)\b", body):
            errors.append(f"{owner}: body_ref_dereference lacks operation/result/Land shape")
        family = owner_family_token(owner)
        owner_specific = OWNER_SPECIFIC_BODY_RE.get(family)
        if owner_specific is not None and not owner_specific.search(body):
            errors.append(f"{owner}: body_ref_dereference lacks selected-owner operation semantics")

    for key in ("owner_activation", "nar", "field_witness"):
        if surface_owner(row, key) != owner:
            errors.append(f"{owner}: {key} must mirror selected owner")
    if surface_body_ref(row, "owner_activation") != body_ref:
        errors.append(f"{owner}: owner_activation must mirror body_ref")
    if surface_body_ref(row, "field_witness") != body_ref:
        errors.append(f"{owner}: field_witness must mirror body_ref")

    reread = row.get("mrp_reread")
    if not isinstance(reread, dict):
        errors.append(f"{owner}: mrp_reread must be an object")
    else:
        route_type = str(reread.get("route_result_type") or "").strip()
        if route_type not in {"no_new_resultant", "held_burden_activation", "generated_burden_instantiation", "hold_partial"}:
            errors.append(f"{owner}: mrp_reread route_result_type is unsupported")
        owner_route = {str(value).strip() for value in as_list(reread.get("owner_route"))}
        if owner not in owner_route:
            errors.append(f"{owner}: mrp_reread.owner_route must include selected owner")
    return errors


def surface_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in as_list(data.get("surface_rows")) if isinstance(row, dict)]


def owners_on_surfaces(data: dict[str, Any]) -> set[str]:
    owners: set[str] = set()
    for row in surface_rows(data):
        owner = row_owner(row)
        if owner:
            owners.add(owner)
        for key in ("owner_activation", "nar", "field_witness"):
            found = surface_owner(row, key)
            if found:
                owners.add(found)
    return owners


def generated_burden_errors(data: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    b_la = {str(value).strip() for value in as_list(data.get("B_LA")) if str(value).strip()}
    b_mrp = {str(value).strip() for value in as_list(data.get("B_MRP")) if str(value).strip()}
    generated = [item for item in as_list(data.get("generated_burdens")) if isinstance(item, dict)]
    edges = {
        (str(item[0]).strip(), str(item[1]).strip())
        for item in as_list(data.get("dependency_graph_edges"))
        if isinstance(item, list) and len(item) == 2
    }
    for burden in b_mrp:
        if burden in b_la:
            errors.append(f"{label}: generated burden {burden} must not be in B_LA")
        record = next((item for item in generated if str(item.get("id") or "").strip() == burden), None)
        if record is None:
            errors.append(f"{label}: B_MRP burden {burden} lacks generated_burdens record")
            continue
        generated_by = str(record.get("generated_by") or "").strip()
        match = re.fullmatch(r"MRP\(([^)]+)\)", generated_by)
        if not match:
            errors.append(f"{label}: generated burden {burden} must have generated_by=MRP(parent)")
            continue
        parent = match.group(1)
        if (parent, burden) not in edges:
            errors.append(f"{label}: dependency_graph_edges must include {parent}->{burden}")
        if str(record.get("cause") or "").strip() == "catalogue_presence":
            errors.append(f"{label}: catalogue presence alone cannot generate {burden}")
        state = str(record.get("state") or record.get("terminal_state") or "").strip()
        held_state = bool(HELD_GENERATED_STATE_RE.search(state)) and not bool(EXECUTED_GENERATED_STATE_RE.search(state))
        if held_state:
            if data.get("coverage_complete") is not False:
                errors.append(f"{label}: held generated burden {burden} requires coverage_complete=false")
            for claim in as_list(data.get("land_claims")):
                if re.search(rf"\bLand\({re.escape(burden)}\)", str(claim or "")):
                    errors.append(f"{label}: held generated burden {burden} must not claim Land({burden})")
            for row in surface_rows(data):
                body_ref = surface_body_ref(row, "body_ref")
                act = str(row.get("act_row") or "")
                if re.match(rf"^{re.escape(burden)}(?:_|$)", body_ref) or re.search(rf"\bLand\({re.escape(burden)}\)", act):
                    errors.append(f"{label}: held generated burden {burden} must not fake ACT/Land surfaces")
    return errors


def validate_case(path: Path, data: dict[str, Any]) -> list[str]:
    label = rel(path)
    errors: list[str] = []
    if data.get("schema") != SCHEMA:
        return [f"{label}: schema must be {SCHEMA!r}"]
    scenario = str(data.get("scenario") or "").strip()
    if scenario not in {
        "callable_applicable",
        "callable_inert",
        "applicable_owner_body_not_loaded",
        "generated_by_mrp",
    }:
        errors.append(f"{label}: unsupported scenario {scenario!r}")

    catalogue_present = [str(value).strip() for value in as_list(data.get("catalogue_present")) if str(value).strip()]
    selected = [str(value).strip() for value in as_list(data.get("selected")) if str(value).strip()]
    unselected = [str(value).strip() for value in as_list(data.get("unselected")) if str(value).strip()]

    for owner in catalogue_present + selected + unselected:
        if owner and not owner_known(owner):
            errors.append(f"{label}: owner/TTP {owner!r} is not catalogue/vocabulary-known")

    for owner in PASS_THROUGH_GUIDANCE:
        if owner in selected and not explicit_owner_contract_for(data, owner):
            errors.append(f"{label}: {owner} is pass-through guidance and cannot be load-bearing ACT without explicit owner contract")

    surface_owner_set = owners_on_surfaces(data)

    if scenario == "callable_applicable":
        rows_by_owner = {row_owner(row): row for row in surface_rows(data)}
        for owner in selected:
            row = rows_by_owner.get(owner)
            if row is None:
                errors.append(f"{label}: selected owner {owner} lacks surface row")
                continue
            errors.extend(f"{label}: {error}" for error in row_is_complete(row, owner))
        for owner in unselected:
            if owner in surface_owner_set:
                errors.append(f"{label}: unselected owner {owner} appears on activation surfaces")

    if scenario == "callable_inert":
        if data.get("B_MRP"):
            errors.append(f"{label}: inert catalogue presence must not create B_MRP")
        if data.get("generated_burdens"):
            errors.append(f"{label}: inert catalogue presence must not create generated_burdens")
        for owner in unselected:
            if owner in surface_owner_set:
                errors.append(f"{label}: unselected catalogue owner {owner} must remain inert")

    if scenario == "applicable_owner_body_not_loaded":
        if not selected:
            errors.append(f"{label}: owner-body-not-loaded requires at least one selected owner")
        owner_body_status = data.get("owner_body_status")
        if not isinstance(owner_body_status, dict):
            errors.append(f"{label}: owner-body-not-loaded requires owner_body_status object")
        else:
            for owner in selected:
                if str(owner_body_status.get(owner) or "").strip() != "not_loaded":
                    errors.append(f"{label}: selected owner {owner} must have owner_body_status=not_loaded")
        if str(data.get("route") or "").upper() != "HOLD":
            errors.append(f"{label}: owner-body-not-loaded must route HOLD")
        boundary = str(data.get("boundary") or "")
        if "OWNER-BODY-NOT-LOADED" not in boundary or "PARTIAL" not in boundary:
            errors.append(f"{label}: owner-body-not-loaded boundary must name PARTIAL / OWNER-BODY-NOT-LOADED")
        if data.get("coverage_complete") is not False:
            errors.append(f"{label}: owner-body-not-loaded must keep coverage_complete=false")
        if data.get("retained_promotion_eligible") is not False:
            errors.append(f"{label}: owner-body-not-loaded must not be retained-promotion eligible")
        if surface_owner_set:
            errors.append(f"{label}: owner-body-not-loaded must not fake ACT/owner_activation surfaces")
        if data.get("land_claims"):
            errors.append(f"{label}: owner-body-not-loaded must not fake Land(B)")

    if scenario == "generated_by_mrp":
        if not data.get("B_MRP"):
            errors.append(f"{label}: generated_by_mrp requires non-empty B_MRP")
        errors.extend(generated_burden_errors(data, label))
        cause = str(data.get("generation_cause") or "").strip()
        if cause != "live_pressure":
            errors.append(f"{label}: generated burden must be caused by live_pressure, not catalogue presence")

    return errors


def iter_json_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("*.json") if path.is_file())


def run_suite(root: Path) -> tuple[list[str], int, int]:
    valid = iter_json_files(root / "valid")
    invalid = iter_json_files(root / "invalid")
    errors: list[str] = []
    for path in valid:
        data = load_json(path)
        errors.extend(validate_case(path, data))
    for path in invalid:
        data = load_json(path)
        found = validate_case(path, data)
        if not found:
            errors.append(f"{rel(path)}: invalid fixture unexpectedly passed")
    return errors, len(valid), len(invalid)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    args = parser.parse_args()

    errors, valid_count, invalid_count = run_suite(args.root)
    if errors:
        print("TTP availability canary check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("TTP availability canary check: PASS")
    print(f"Valid fixtures checked: {valid_count}")
    print(f"Invalid fixtures checked: {invalid_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
