#!/usr/bin/env python3
"""Validate Diagnostic IR instance integrity.

This checker is intentionally schema-adjacent/custom rather than a jsonschema
runtime. It covers the schema enums, required fields, conditional
decisive_missing_differentiator rule, and repo-specific executable constraints
that JSON Schema alone cannot prove: catalogue membership, compiled-module-map
resolution, source_basis coverage, ghost-load rejection, and post-render
decision consistency. It validates any IR fixture/artifact passed by --file or
discovered under --root, and treats files under tests/ir-fixtures/invalid/ as
expected-invalid regression fixtures. Smoke sidecars named
smokes/runtime-grounding-v*/<fixture>/ir.json are expected-valid by default.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from compiled_runtime_lib import fail_with_errors, out_dir, repo_root


OMNIBUS_RE = re.compile(r"(?i)(?:^OMNIBUS-|/omnibus/|\\omnibus\\|\.md$|\.json$|\.ya?ml$|/|\\)")
NONE_VALUES = {"", "none", "none.", "n/a", "no", "null"}
DECISIONS = {"STOP", "HOLD", "RECURSE", "PARTIAL"}
REASON_CATEGORY_VALUES = {1, 2, 3, 4, "1", "2", "3", "4"}
MATCHED_MODULE_KEYS = {"id", "module_class"}
SOURCE_BASIS_KEYS = {"entries"}
SOURCE_BASIS_ENTRY_KEYS = {"basis_type", "claim", "source_kind", "module_id", "source_ref", "section", "notes"}
SOURCE_BASIS_TYPES = {"anchored", "inference", "speculative", "synthesis"}
SOURCE_KINDS = {"input", "module", "schema", "catalogue", "operator"}
POST_RENDER_GATE_KEYS = {
    "cleared_this_pass",
    "remaining_live_distortions",
    "held_routes_rechecked",
    "newly_released_routes",
    "next_eligible_pass",
    "recursion_decision",
}


POSITIVE_SAMPLE: dict[str, Any] = {
    "case_family": "criterion-import",
    "claim_type": "moral",
    "claim_level": "meta-epistemic",
    "pattern_profile": "PF-10",
    "deformation": "imported moral tribunal",
    "concealment_mode": "clear",
    "do_orient": "mixed",
    "read_status": "dominant",
    "confidence": "strong",
    "alignment_state": "tribunal-loosened",
    "recognition_strength": "medium",
    "continuation_eligibility": "blocked",
    "p7_stops_active": ["none"],
    "reason_category": 3,
    "routing_gate": "open",
    "matched_modules": [
        {"id": "M1-self-refutation", "module_class": "tactic"},
        {"id": "M8-reductio", "module_class": "tactic"},
    ],
    "source_basis": {
        "entries": [
            {
                "basis_type": "anchored",
                "claim": "routing fork: imported criterion requires self-refutation pressure",
                "source_kind": "module",
                "module_id": "M1-self-refutation",
                "source_ref": "atomics/skill/references/tactics/M1-self-refutation.md",
            },
            {
                "basis_type": "anchored",
                "claim": "claim: reductio traces the criterion's consequence",
                "source_kind": "module",
                "module_id": "M8-reductio",
                "source_ref": "atomics/skill/references/tactics/M8-reductio.md",
            },
        ]
    },
    "restoration_target": "return moral criterion to warranted order",
    "reconstruction_fidelity": "pass",
    "reconstructor_notes": "burden, owner contrast, Land(B), and STOP verdict recover from input plus IR",
    "next_move": "test imported criterion before downstream content",
    "output_shape": "single-response",
    "post_render_gate": {
        "cleared_this_pass": "imported tribunal no longer governs as neutral judge",
        "remaining_live_distortions": "none",
        "held_routes_rechecked": [],
        "newly_released_routes": [],
        "next_eligible_pass": "none",
        "recursion_decision": "STOP",
    },
}


BAD_SAMPLES: dict[str, tuple[dict[str, Any], str]] = {}


def _sample_with(mutator) -> dict[str, Any]:  # noqa: ANN001
    sample = deepcopy(POSITIVE_SAMPLE)
    mutator(sample)
    return sample


BAD_SAMPLES["invented_module_id"] = (
    _sample_with(lambda s: s["matched_modules"].append({"id": "invented-owner", "module_class": "tactic"})),
    "module id not found in catalogue",
)
BAD_SAMPLES["module_class_mismatch"] = (
    _sample_with(lambda s: s["matched_modules"][0].update({"module_class": "technique"})),
    "module_class mismatch",
)
BAD_SAMPLES["omnibus_active_module"] = (
    _sample_with(lambda s: s["matched_modules"].append({"id": "OMNIBUS-tactics", "module_class": "tactic"})),
    "omnibus/path used as matched module id",
)
BAD_SAMPLES["missing_source_basis"] = (
    _sample_with(lambda s: s.pop("source_basis")),
    "source_basis missing while matched_modules present",
)
BAD_SAMPLES["ghost_load"] = (
    _sample_with(lambda s: s["source_basis"]["entries"].pop()),
    "ghost-load",
)
BAD_SAMPLES["source_basis_module_mismatch"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"module_id": "M8-reductio"})),
    "ghost-load",
)
BAD_SAMPLES["source_basis_invalid_module"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"module_id": "invented-owner"})),
    "source_basis module_id not found",
)
BAD_SAMPLES["source_basis_without_claim"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"claim": ""})),
    "module source_basis entry lacks claim",
)
BAD_SAMPLES["source_basis_vague_claim"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"claim": "module used"})),
    "module source_basis entry uses vague claim",
)
BAD_SAMPLES["stop_with_next_pass"] = (
    _sample_with(lambda s: s["post_render_gate"].update({"next_eligible_pass": "model/predication"})),
    "STOP requires next_eligible_pass none",
)
BAD_SAMPLES["weak_confidence_without_differentiator"] = (
    _sample_with(lambda s: s.update({"confidence": "provisional"})),
    "missing required field: decisive_missing_differentiator",
)
BAD_SAMPLES["distributed_read_without_differentiator"] = (
    _sample_with(lambda s: s.update({"read_status": "distributed"})),
    "missing required field: decisive_missing_differentiator",
)
BAD_SAMPLES["reconstruction_partial_without_notes"] = (
    _sample_with(lambda s: (s.update({"reconstruction_fidelity": "partial"}), s.pop("reconstructor_notes", None))),
    "missing required field: reconstructor_notes",
)
BAD_SAMPLES["p7_none_combined_with_stop"] = (
    _sample_with(lambda s: s.update({"p7_stops_active": ["none", "Stop-1"]})),
    "p7_stops_active cannot combine none with active stops",
)
BAD_SAMPLES["invalid_reason_category"] = (
    _sample_with(lambda s: s.update({"reason_category": "unknown"})),
    "reason_category invalid oneOf value",
)
BAD_SAMPLES["matched_module_extra_key"] = (
    _sample_with(lambda s: s["matched_modules"][0].update({"extra": "leak"})),
    "matched_modules[0] additional property not allowed",
)
BAD_SAMPLES["source_basis_extra_key"] = (
    _sample_with(lambda s: s["source_basis"].update({"extra": "leak"})),
    "source_basis additional property not allowed",
)
BAD_SAMPLES["source_basis_entry_extra_key"] = (
    _sample_with(lambda s: s["source_basis"]["entries"][0].update({"extra": "leak"})),
    "source_basis.entries[0] additional property not allowed",
)
BAD_SAMPLES["post_render_gate_extra_key"] = (
    _sample_with(lambda s: s["post_render_gate"].update({"extra": "leak"})),
    "post_render_gate additional property not allowed",
)

COMPILED_MAP_BAD_SAMPLES = {
    "matched_module_absent_from_compiled_map": (
        _sample_with(lambda s: None),
        "matched module does not resolve in compiled-module-map.json",
        "M1-self-refutation",
    )
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_ir_like(payload: Any) -> bool:
    return isinstance(payload, dict) and (
        "matched_modules" in payload
        or "post_render_gate" in payload
        or "case_family" in payload
    )


def as_instances(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if is_ir_like(item)]
    return [payload] if is_ir_like(payload) else []


def is_noneish(value: Any) -> bool:
    if isinstance(value, str):
        stripped = value.strip().lower()
        return stripped in NONE_VALUES or stripped.startswith("none ")
    if isinstance(value, list):
        return len(value) == 0 or all(is_noneish(item) for item in value)
    return value is None


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def schema_errors(instance: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = schema.get("required") or []
    for field in required:
        if field not in instance:
            errors.append(f"schema: missing required field: {field}")

    allowed = set(schema.get("properties") or {})
    for field in instance:
        if field not in allowed:
            errors.append(f"schema: additional property not allowed: {field}")

    properties = schema.get("properties") or {}
    for field, spec in properties.items():
        if field not in instance:
            continue
        value = instance[field]
        enum = spec.get("enum")
        if enum is not None and value not in enum:
            errors.append(f"schema: {field} invalid enum value: {value!r}")
        if spec.get("type") == "string":
            if not isinstance(value, str):
                errors.append(f"schema: {field} must be string")
            elif spec.get("minLength", 0) and len(value) < spec["minLength"]:
                errors.append(f"schema: {field} must be non-empty")
        if spec.get("type") == "array" and not isinstance(value, list):
            errors.append(f"schema: {field} must be array")
        if spec.get("type") == "object" and not isinstance(value, dict):
            errors.append(f"schema: {field} must be object")

    if "reason_category" in instance and instance.get("reason_category") not in REASON_CATEGORY_VALUES:
        errors.append(f"schema: reason_category invalid oneOf value: {instance.get('reason_category')!r}")
    p7_stops = instance.get("p7_stops_active")
    if isinstance(p7_stops, list):
        if "none" in p7_stops and len(p7_stops) > 1:
            errors.append("schema: p7_stops_active cannot combine none with active stops")
        if len(set(p7_stops)) != len(p7_stops):
            errors.append("schema: p7_stops_active must have unique items")

    if instance.get("confidence") != "strong" and "decisive_missing_differentiator" not in instance:
        errors.append("schema: missing required field: decisive_missing_differentiator")
    if instance.get("read_status") != "dominant" and "decisive_missing_differentiator" not in instance:
        errors.append("schema: missing required field: decisive_missing_differentiator")
    if instance.get("read_status") == "underdetermined" and instance.get("confidence") == "strong":
        errors.append("schema: read_status underdetermined cannot pair with strong confidence")
    if instance.get("reconstruction_fidelity") in {"partial", "fail"} and "reconstructor_notes" not in instance:
        errors.append("schema: missing required field: reconstructor_notes")

    matched = instance.get("matched_modules")
    if matched is not None:
        if not isinstance(matched, list) or not matched:
            errors.append("schema: matched_modules must be a non-empty array")
        else:
            for index, item in enumerate(matched):
                if not isinstance(item, dict):
                    errors.append(f"schema: matched_modules[{index}] must be object")
                    continue
                extra = sorted(set(item) - MATCHED_MODULE_KEYS)
                if extra:
                    errors.append(f"schema: matched_modules[{index}] additional property not allowed: {', '.join(extra)}")
                for field in ("id", "module_class"):
                    if not isinstance(item.get(field), str) or not item[field].strip():
                        errors.append(f"schema: matched_modules[{index}].{field} must be non-empty string")
            if "source_basis" not in instance:
                errors.append("schema: source_basis required when matched_modules present")

    source_basis = instance.get("source_basis")
    if source_basis is not None:
        entries = source_basis.get("entries") if isinstance(source_basis, dict) else None
        if isinstance(source_basis, dict):
            extra = sorted(set(source_basis) - SOURCE_BASIS_KEYS)
            if extra:
                errors.append("schema: source_basis additional property not allowed: " + ", ".join(extra))
        if not isinstance(entries, list) or not entries:
            errors.append("schema: source_basis.entries must be a non-empty array")
        else:
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    errors.append(f"schema: source_basis.entries[{index}] must be object")
                    continue
                extra = sorted(set(entry) - SOURCE_BASIS_ENTRY_KEYS)
                if extra:
                    errors.append(f"schema: source_basis.entries[{index}] additional property not allowed: {', '.join(extra)}")
                for field in ("basis_type", "claim", "source_kind"):
                    if not isinstance(entry.get(field), str) or not entry[field].strip():
                        errors.append(f"schema: source_basis.entries[{index}].{field} must be non-empty string")
                if entry.get("basis_type") not in SOURCE_BASIS_TYPES:
                    errors.append(f"schema: source_basis.entries[{index}].basis_type invalid enum value: {entry.get('basis_type')!r}")
                if entry.get("source_kind") not in SOURCE_KINDS:
                    errors.append(f"schema: source_basis.entries[{index}].source_kind invalid enum value: {entry.get('source_kind')!r}")
                if entry.get("source_kind") == "module" and not isinstance(entry.get("module_id"), str):
                    errors.append(f"schema: source_basis.entries[{index}].module_id required for module source")
                if entry.get("basis_type") in {"anchored", "inference", "speculative"} and not isinstance(entry.get("source_ref"), str):
                    errors.append(f"schema: source_basis.entries[{index}].source_ref required for anchored/inference/speculative basis")

    post_gate = instance.get("post_render_gate")
    if isinstance(post_gate, dict):
        extra = sorted(set(post_gate) - POST_RENDER_GATE_KEYS)
        if extra:
            errors.append("schema: post_render_gate additional property not allowed: " + ", ".join(extra))
        required_gate = (properties.get("post_render_gate", {}).get("required") or [])
        for field in required_gate:
            if field not in post_gate:
                errors.append(f"schema: post_render_gate missing required field: {field}")
        for field in ("cleared_this_pass", "remaining_live_distortions", "next_eligible_pass"):
            if field in post_gate and (not isinstance(post_gate.get(field), str) or not post_gate[field].strip()):
                errors.append(f"schema: post_render_gate.{field} must be non-empty string")
        for field in ("held_routes_rechecked", "newly_released_routes"):
            if field in post_gate:
                values = post_gate.get(field)
                if not isinstance(values, list):
                    errors.append(f"schema: post_render_gate.{field} must be array")
                elif len(set(values)) != len(values):
                    errors.append(f"schema: post_render_gate.{field} must have unique items")
        decision = post_gate.get("recursion_decision")
        if decision not in DECISIONS:
            errors.append(f"schema: post_render_gate.recursion_decision invalid: {decision!r}")
    elif post_gate is not None:
        errors.append("schema: post_render_gate must be object")

    return errors


def integrity_errors(
    instance: dict[str, Any],
    catalogue: dict[str, dict[str, Any]],
    compiled_modules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    matched = instance.get("matched_modules") or []
    if not isinstance(matched, list):
        return errors

    matched_ids: list[str] = []
    for item in matched:
        if not isinstance(item, dict):
            continue
        module_id = item.get("id")
        module_class = item.get("module_class")
        if not isinstance(module_id, str):
            continue
        matched_ids.append(module_id)
        if OMNIBUS_RE.search(module_id):
            errors.append(f"omnibus/path used as matched module id: {module_id}")
        catalogue_entry = catalogue.get(module_id)
        if catalogue_entry is None:
            errors.append(f"module id not found in catalogue: {module_id}")
        elif catalogue_entry.get("module_class") != module_class:
            errors.append(
                f"module_class mismatch for {module_id}: "
                f"{module_class!r} != {catalogue_entry.get('module_class')!r}"
            )
        compiled_entry = compiled_modules.get(module_id)
        if compiled_entry is None:
            errors.append(f"matched module does not resolve in compiled-module-map.json: {module_id}")
        elif not compiled_entry.get("bundle_path"):
            errors.append(f"matched module lacks compiled bundle_path: {module_id}")

    if matched_ids and "source_basis" not in instance:
        errors.append("source_basis missing while matched_modules present")
        return errors

    source_basis = instance.get("source_basis") or {}
    entries = source_basis.get("entries") if isinstance(source_basis, dict) else []
    module_entries = [entry for entry in entries if isinstance(entry, dict) and entry.get("source_kind") == "module"]
    for entry in module_entries:
        module_id = entry.get("module_id")
        if not isinstance(module_id, str) or not module_id.strip():
            errors.append("module source_basis entry lacks module_id")
            continue
        if module_id not in catalogue:
            errors.append(f"source_basis module_id not found in catalogue: {module_id}")
        claim = entry.get("claim")
        if not isinstance(claim, str) or not claim.strip():
            errors.append(f"module source_basis entry lacks claim/routing fork: {module_id}")
        elif re.fullmatch(r"(?i)\s*(?:module used|supporting source|source|module|support)\s*\.?", claim):
            errors.append(f"module source_basis entry uses vague claim/routing fork: {module_id}")

    for module_id in matched_ids:
        if not any(entry.get("module_id") == module_id for entry in module_entries):
            errors.append(f"ghost-load: {module_id} lacks matching module source_basis entry")

    gate = instance.get("post_render_gate")
    if not isinstance(gate, dict):
        errors.append("post_render_gate missing or not object")
        return errors

    decision = gate.get("recursion_decision")
    remaining = gate.get("remaining_live_distortions")
    newly_released = gate.get("newly_released_routes")
    next_pass = gate.get("next_eligible_pass")
    held = gate.get("held_routes_rechecked")

    if decision == "STOP":
        if not is_noneish(remaining):
            errors.append("STOP requires remaining_live_distortions none")
        if not is_noneish(newly_released):
            errors.append("STOP requires newly_released_routes empty")
        if not is_noneish(next_pass):
            errors.append("STOP requires next_eligible_pass none")
    elif decision == "HOLD":
        if not is_noneish(newly_released):
            errors.append("HOLD invalid while newly_released_routes is non-empty")
        if not is_noneish(next_pass):
            errors.append("HOLD invalid while next_eligible_pass is live")
        if is_noneish(remaining) and is_noneish(held):
            errors.append("HOLD requires remaining or held material")
    elif decision == "RECURSE":
        if is_noneish(next_pass):
            errors.append("RECURSE requires next_eligible_pass")
        if is_noneish(remaining) and is_noneish(newly_released):
            errors.append("RECURSE requires remaining_live_distortions or newly_released_routes")
    elif decision == "PARTIAL":
        if is_noneish(next_pass) and is_noneish(remaining):
            errors.append("PARTIAL requires remaining_live_distortions or next_eligible_pass")

    # Defensive type check for fields the consistency rules depend on.
    if not isinstance(newly_released, list):
        errors.append("post_render_gate.newly_released_routes must be array")
    if not isinstance(held, list):
        errors.append("post_render_gate.held_routes_rechecked must be array")
    for value in string_list(newly_released) + string_list(held):
        if not value.strip():
            errors.append("post_render_gate route arrays must not contain blank entries")

    return errors


def load_catalogue(root: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(root / "atomics/skill/references/diagnostics/module-catalogue.json")
    return {entry["id"]: entry for entry in payload.get("modules", [])}


def load_compiled_modules(root: Path) -> dict[str, Any]:
    payload = load_json(out_dir(root) / "compiled-module-map.json")
    modules = payload.get("modules")
    return modules if isinstance(modules, dict) else {}


def iter_json_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.json") if ".git" not in path.parts)


def validate_instance(
    label: str,
    instance: dict[str, Any],
    schema: dict[str, Any],
    catalogue: dict[str, dict[str, Any]],
    compiled_modules: dict[str, Any],
) -> list[str]:
    errors = schema_errors(instance, schema)
    # The catalogue/source-basis checks still run after schema checks so one
    # bad fixture can expose every relevant failure in one pass.
    errors.extend(integrity_errors(instance, catalogue, compiled_modules))
    return [f"{label}: {error}" for error in errors]


def check_bad_samples(
    schema: dict[str, Any],
    catalogue: dict[str, dict[str, Any]],
    compiled_modules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    positive_errors = validate_instance("positive sample", POSITIVE_SAMPLE, schema, catalogue, compiled_modules)
    if positive_errors:
        errors.extend(positive_errors)
    for name, (sample, expected) in BAD_SAMPLES.items():
        found = validate_instance(name, sample, schema, catalogue, compiled_modules)
        if not any(expected in error for error in found):
            errors.append(f"bad sample {name!r} was not rejected with {expected!r}; got {found!r}")
    for name, (sample, expected, missing_module_id) in COMPILED_MAP_BAD_SAMPLES.items():
        compiled_without_module = dict(compiled_modules)
        compiled_without_module.pop(missing_module_id, None)
        found = validate_instance(name, sample, schema, catalogue, compiled_without_module)
        if not any(expected in error for error in found):
            errors.append(f"bad sample {name!r} was not rejected with {expected!r}; got {found!r}")
    return errors


def expected_invalid_fixture(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to((root / "tests/ir-fixtures/invalid").resolve())
    except ValueError:
        return False
    return relative.parts != ()


def smoke_sidecar(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to((root / "smokes").resolve())
    except ValueError:
        return False
    return (
        len(relative.parts) == 3
        and re.fullmatch(r"runtime-grounding-v\d+", relative.parts[0]) is not None
        and relative.name == "ir.json"
    )


def valid_fixture(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to((root / "tests/ir-fixtures/valid").resolve())
    except ValueError:
        return False
    return relative.parts != ()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", action="append", default=[], help="IR JSON artifact to validate.")
    parser.add_argument("--root", action="append", default=[], help="Directory tree containing IR JSON artifacts.")
    parser.add_argument("--samples-only", action="store_true", help="Only run embedded sample checks.")
    parser.add_argument(
        "--include-smoke-sidecars",
        dest="include_smoke_sidecars",
        action="store_true",
        default=True,
        help="Include smokes/runtime-grounding-v*/<fixture>/ir.json sidecars when scanning defaults.",
    )
    parser.add_argument(
        "--no-include-smoke-sidecars",
        dest="include_smoke_sidecars",
        action="store_false",
        help="Do not include smoke ir.json sidecars in the default scan.",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    schema = load_json(root / "atomics/skill/references/diagnostics/diagnostic-ir.schema.json")
    catalogue = load_catalogue(root)
    compiled_modules = load_compiled_modules(root)

    errors = check_bad_samples(schema, catalogue, compiled_modules)
    files_checked = 0
    instances_checked = 0
    valid_fixtures_checked = 0
    expected_invalid_checked = 0
    smoke_sidecars_checked = 0
    smoke_sidecar_paths_checked: set[Path] = set()
    ignored = 0

    paths: list[Path] = []
    explicit_paths = [Path(item) for item in args.file] + [Path(item) for item in args.root]
    if explicit_paths:
        for path in explicit_paths:
            resolved = path if path.is_absolute() else root / path
            if not resolved.exists():
                errors.append(f"IR artifact path does not exist: {resolved}")
                continue
            paths.extend(iter_json_files(resolved))
    elif not args.samples_only:
        default_root = root / "tests/ir-fixtures"
        paths.extend(iter_json_files(default_root))
        if args.include_smoke_sidecars:
            smoke_root = root / "smokes"
            if smoke_root.exists():
                paths.extend(sorted(smoke_root.glob("runtime-grounding-v*/*/ir.json")))

    if not args.samples_only:
        for path in paths:
            try:
                payload = load_json(path)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}: JSON parse error: {exc}")
                continue
            files_checked += 1
            instances = as_instances(payload)
            if not instances:
                if expected_invalid_fixture(path, root):
                    errors.append(f"{path.relative_to(root).as_posix()}: expected-invalid fixture is not IR-like")
                ignored += 1
                continue
            for index, instance in enumerate(instances):
                label = f"{path.relative_to(root).as_posix()}[{index}]"
                found = validate_instance(label, instance, schema, catalogue, compiled_modules)
                if expected_invalid_fixture(path, root):
                    expected_invalid_checked += 1
                    if not found:
                        errors.append(f"{label}: expected-invalid fixture unexpectedly passed")
                else:
                    errors.extend(found)
                    instances_checked += 1
                    if valid_fixture(path, root):
                        valid_fixtures_checked += 1
                    elif smoke_sidecar(path, root):
                        smoke_sidecar_paths_checked.add(path)
                        smoke_sidecars_checked += 1

    if not errors:
        print("Diagnostic IR instance integrity summary")
        print("------------------------------------------------------------")
        print(f"Embedded bad samples checked: {len(BAD_SAMPLES) + len(COMPILED_MAP_BAD_SAMPLES)}")
        print(f"tests/ir-fixtures valid checked: {valid_fixtures_checked}")
        print(f"tests/ir-fixtures invalid checked: {expected_invalid_checked}")
        print(f"smoke sidecars checked: {len(smoke_sidecar_paths_checked)}")
        print(f"smoke sidecar IR instances checked: {smoke_sidecars_checked}")
        print(f"Non-IR JSON files ignored: {ignored}")
        print(f"Total JSON files scanned: {files_checked}")
        print(f"Total expected-valid IR instances checked: {instances_checked}")
        print("------------------------------------------------------------")
    return fail_with_errors("diagnostic IR instance integrity", errors)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
