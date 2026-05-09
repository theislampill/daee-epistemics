#!/usr/bin/env python3
"""Validate IR reconstruction and routing-stability regression fixtures."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from compiled_runtime_lib import fail_with_errors, repo_root
from check_ir_instance_integrity import (
    load_compiled_modules,
    load_catalogue,
    load_json,
    validate_instance,
)


FIXTURE_PATH = Path("tests/reconstruction-fixtures/required-contrast-and-stability.json")
REQUIRED_FIXTURE_IDS = {
    "trinitarian-claim-cluster-neighbor-contrast",
    "imported-tribunal-protest",
    "grief-coded-register-hold",
    "genuine-shubhah-after-clearing",
    "mushabara-fasida-specialty",
    "ttp-named-without-trigger-negative",
}
REQUIRED_STABILITY_GROUPS = {"imported-tribunal-repeatability-5x"}
STOPWORDS = {
    "after",
    "before",
    "because",
    "current",
    "direct",
    "expected",
    "first",
    "from",
    "generic",
    "land",
    "lands",
    "live",
    "rather",
    "that",
    "this",
    "through",
    "with",
    "without",
}


def words(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) >= 4 and token not in STOPWORDS
    }


def overlap_enough(needle: str, haystack: str, minimum: int = 2) -> bool:
    target = words(needle)
    if len(target) < minimum:
        minimum = max(1, len(target))
    return len(target & words(haystack)) >= minimum


def module_ids(ir: dict[str, Any]) -> set[str]:
    matched = ir.get("matched_modules") or []
    return {
        item["id"]
        for item in matched
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def reconstruction_text(ir: dict[str, Any]) -> str:
    keys = [
        "restoration_target",
        "next_move",
        "load_bearing_node",
        "intervention_target",
        "what_is_withheld_and_why",
        "what_remains_live",
        "reconstructor_notes",
    ]
    gate = ir.get("post_render_gate") if isinstance(ir.get("post_render_gate"), dict) else {}
    parts = [str(ir.get(key, "")) for key in keys]
    parts.extend(str(gate.get(key, "")) for key in ("cleared_this_pass", "remaining_live_distortions"))
    return " ".join(parts)


def non_catalogue_owner_supported(owner: str, ir: dict[str, Any]) -> bool:
    upstream = set(ir.get("upstream_findings") or [])
    deformation = str(ir.get("deformation", "")).lower()
    foreign_premise = str(ir.get("foreign_premise", "")).strip().lower()
    if owner == "foreign-premise-detection":
        return bool(foreign_premise) or bool({"criterion-import", "tribunal-installation"} & upstream)
    if owner in {"mushabara-fasida", "seven-deformations:1-A"}:
        return "mushabara" in deformation or "false resemblance" in deformation or "seven-deformations 1-a" in deformation
    return False


def check_fixture(
    fixture: dict[str, Any],
    schema: dict[str, Any],
    catalogue: dict[str, dict[str, Any]],
    compiled_modules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    fixture_id = fixture.get("id", "<missing-id>")
    expected = fixture.get("expected")
    ir = fixture.get("candidate_ir")
    if not isinstance(expected, dict):
        return [f"{fixture_id}: expected block missing"]
    if not isinstance(ir, dict):
        return [f"{fixture_id}: candidate_ir missing"]

    errors.extend(validate_instance(f"{fixture_id}.candidate_ir", ir, schema, catalogue, compiled_modules))

    expected_fidelity = expected.get("reconstruction_fidelity")
    actual_fidelity = ir.get("reconstruction_fidelity")
    if actual_fidelity != expected_fidelity:
        errors.append(
            f"{fixture_id}: reconstruction_fidelity {actual_fidelity!r} != expected {expected_fidelity!r}"
        )

    selected = set(expected.get("selected_owners") or [])
    coactive = set(expected.get("coactive_owners") or [])
    held = set(expected.get("held_or_deferred") or [])
    matched = module_ids(ir)

    for owner in sorted(selected | coactive):
        if owner in catalogue:
            if owner not in matched:
                errors.append(f"{fixture_id}: selected catalogue owner {owner} not present in matched_modules")
        elif not non_catalogue_owner_supported(owner, ir):
            errors.append(f"{fixture_id}: non-catalogue owner {owner} lacks reconstructible IR signal")

    for owner in sorted(held - selected - coactive):
        if owner in matched:
            errors.append(f"{fixture_id}: held/deferred owner {owner} appears active in matched_modules")

    text = reconstruction_text(ir)
    first_live = str(expected.get("first_live_burden", ""))
    if first_live and expected_fidelity == "pass" and not overlap_enough(first_live, text):
        errors.append(f"{fixture_id}: first-live burden is not recoverable from candidate IR")

    expected_land = str(expected.get("expected_land", ""))
    if expected_land and expected_fidelity == "pass" and not overlap_enough(expected_land, text):
        errors.append(f"{fixture_id}: expected Land(B) is not recoverable from candidate IR")

    gate = ir.get("post_render_gate") if isinstance(ir.get("post_render_gate"), dict) else {}
    expected_verdict = expected.get("governance_verdict")
    if expected_verdict and gate.get("recursion_decision") != expected_verdict:
        errors.append(
            f"{fixture_id}: governance verdict {gate.get('recursion_decision')!r} != {expected_verdict!r}"
        )

    if expected_fidelity in {"partial", "fail"} and not ir.get("reconstructor_notes"):
        errors.append(f"{fixture_id}: partial/fail reconstruction lacks reconstructor_notes")

    return errors


def normalize_burden(value: str) -> str:
    return " ".join(sorted(words(value)))


def selected_tuple(run: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(owner for owner in run.get("selected_owners", []) if isinstance(owner, str)))


def check_stability_group(group: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    group_id = group.get("id", "<missing-id>")
    runs = group.get("runs")
    if not isinstance(runs, list) or len(runs) != 5:
        return [f"{group_id}: stability group must contain exactly five runs"]

    for field in ("case_family", "claim_type", "claim_level", "governance_verdict"):
        values = {run.get(field) for run in runs}
        if len(values) != 1:
            errors.append(f"{group_id}: {field} drift across runs: {sorted(values)!r}")

    burdens = {normalize_burden(str(run.get("live_burden", ""))) for run in runs}
    if len(burdens) != 1:
        errors.append(f"{group_id}: live_burden drift across runs")

    selections = [selected_tuple(run) for run in runs]
    modal, _count = Counter(selections).most_common(1)[0]
    neighbors = set(group.get("plausible_neighbor_owners") or [])
    differing_runs = 0
    for selection in selections:
        if selection == modal:
            continue
        differing_runs += 1
        selected = set(selection)
        modal_set = set(modal)
        added = selected - modal_set
        removed = modal_set - selected
        if len(added) + len(removed) > 2:
            errors.append(f"{group_id}: selected TTP drift exceeds one neighboring owner: {modal} -> {selection}")
        if not added <= neighbors:
            errors.append(f"{group_id}: added owner(s) not documented as plausible neighbor: {sorted(added - neighbors)}")
        if len(removed) > 1:
            errors.append(f"{group_id}: more than one modal owner disappeared: {sorted(removed)}")

    expected = group.get("expected_stability")
    if expected == "stable" and differing_runs:
        errors.append(f"{group_id}: expected stable but saw {differing_runs} differing run(s)")
    if expected == "near-stable" and differing_runs > 1:
        errors.append(f"{group_id}: expected near-stable but saw {differing_runs} differing run(s)")
    if expected not in {"stable", "near-stable"}:
        errors.append(f"{group_id}: expected_stability must be stable or near-stable")

    return errors


def main() -> int:
    root = repo_root()
    payload = json.loads((root / FIXTURE_PATH).read_text(encoding="utf-8"))
    schema = load_json(root / "atomics/skill/references/diagnostics/diagnostic-ir.schema.json")
    catalogue = load_catalogue(root)
    compiled_modules = load_compiled_modules(root)

    errors: list[str] = []
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        errors.append(f"{FIXTURE_PATH}: fixtures must be a list")
        fixtures = []
    ids = {fixture.get("id") for fixture in fixtures if isinstance(fixture, dict)}
    missing = REQUIRED_FIXTURE_IDS - ids
    if missing:
        errors.append(f"{FIXTURE_PATH}: missing required fixture(s): {', '.join(sorted(missing))}")
    for fixture in fixtures:
        if isinstance(fixture, dict):
            errors.extend(check_fixture(fixture, schema, catalogue, compiled_modules))

    groups = payload.get("stability_groups")
    if not isinstance(groups, list):
        errors.append(f"{FIXTURE_PATH}: stability_groups must be a list")
        groups = []
    group_ids = {group.get("id") for group in groups if isinstance(group, dict)}
    missing_groups = REQUIRED_STABILITY_GROUPS - group_ids
    if missing_groups:
        errors.append(f"{FIXTURE_PATH}: missing required stability group(s): {', '.join(sorted(missing_groups))}")
    for group in groups:
        if isinstance(group, dict):
            errors.extend(check_stability_group(group))

    if not errors:
        print("IR reconstruction fixture summary")
        print("------------------------------------------------------------")
        print(f"Reconstruction fixtures checked: {len(fixtures)}")
        print(f"Stability groups checked: {len(groups)}")
        print("Required contrast fixtures: PASS")
        print("Bounded stability thresholds: PASS")
        print("------------------------------------------------------------")
    return fail_with_errors("IR reconstruction fixtures", errors)


if __name__ == "__main__":
    sys.exit(main())
