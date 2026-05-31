#!/usr/bin/env python3
"""Validate D.1 retained hard-smoke corpus manifests.

The manifest is a corpus contract, not proof by itself. It binds raw input,
governed output, hashes, collapse certificate, Grapher output, surface evidence,
and validator records so a future D.1 governed smoke cannot be mistaken for a
loose historical artifact.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from check_collapse_certificate_schema import certificate_errors
from check_graph_completeness import input_fingerprint_for_path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "hard-smoke-manifest.schema.json"
FIXTURE_ROOT = ROOT / "tests" / "hard-smokes" / "v0.4.3.0-rc4-surfaces"

SCHEMA_VERSION = "d1-hard-smoke-manifest-v1"
CORPUS_ID = "v0.4.3.0-rc4-surfaces"
STOP_CONDITION = "stop_on_first_failing_validator"
FROZEN_RELEASE_STATUS = "frozen"

SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

REQUIRED_SURFACES = {
    "formal_reread_states_every_mrp_cycle",
    "mixed_concealment_secondary_clarification",
    "closing_formulation_three_slot",
    "owner_activation_ordering_object",
    "two_track_primary_restoration_mrp",
    "graph_completeness_collapse_certificate_binding",
    "output_grapher_warning_clean_certificate_input_agreement",
}

REQUIRED_VALIDATOR_ORDER = [
    "act_surface_syntax",
    "mrp_generated_burden",
    "manual_smoke_render_contract",
    "live_default_witness_contract",
    "mid_reread_pressure",
    "formal_reread_state_semantics",
    "field_witness_convergence",
    "graph_completeness",
    "collapse_certificate_schema",
    "owner_activation_ordering",
    "output_grapher",
]

COMMAND_SNIPPETS = {
    "act_surface_syntax": ["tools/check_act_surface_syntax.py", "--outputs"],
    "mrp_generated_burden": ["tools/check_mrp_generated_burden.py", "--outputs"],
    "manual_smoke_render_contract": ["tools/check_manual_smoke_render_contract.py", "--outputs"],
    "live_default_witness_contract": ["tools/check_live_default_witness_contract.py"],
    "mid_reread_pressure": ["tools/check_mid_reread_pressure.py", "--outputs"],
    "formal_reread_state_semantics": ["tools/check_formal_reread_state_semantics.py", "--outputs"],
    "field_witness_convergence": ["tools/check_field_witness_convergence.py", "--outputs"],
    "graph_completeness": ["tools/check_graph_completeness.py", "--outputs"],
    "collapse_certificate_schema": ["tools/check_collapse_certificate_schema.py", "--certificates"],
    "owner_activation_ordering": ["tools/check_owner_activation_ordering.py", "--require-plan", "--outputs"],
    "output_grapher": [
        "tools/check_output_grapher.py",
        "--skill-output",
        "--expect-reconstructible",
        "--fail-on-warnings",
        "--input",
        "--collapse-certificate",
        "--out",
    ],
}

ARTIFACT_FIELDS = ("input", "output", "hashes", "collapse_certificate", "grapher_html")
REQUIRED_MANIFEST_FIELDS = {
    "schema_version",
    "corpus_id",
    "generated_skill_sha",
    "release_provenance_status",
    "stop_condition",
    "validator_order",
    "cases",
}
ALLOWED_MANIFEST_FIELDS = set(REQUIRED_MANIFEST_FIELDS)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    if not path.exists():
        return None, [f"{rel(path)}: file not found"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)}: invalid JSON: {exc}"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalize_command(text: str) -> str:
    return text.replace("\\", "/")


def resolve_manifest_path(manifest_path: Path, value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "path must be a non-empty string"
    raw = Path(value)
    path = raw if raw.is_absolute() else manifest_path.parent / raw
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        return None, f"{value}: path escapes repository root"
    return resolved, None


def hash_manifest(path: Path) -> tuple[dict[str, str], dict[str, str], list[str]]:
    payload, errors = load_json(path)
    if errors:
        return {}, {}, errors
    if not isinstance(payload, dict):
        return {}, {}, [f"{rel(path)}: hashes root must be an object"]

    entries: dict[str, str] = {}
    metadata: dict[str, str] = {}
    for key in ("raw_input_sha256", "normalized_input_fingerprint"):
        value = payload.get(key)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            errors.append(f"{rel(path)}: {key} must be SHA-256")
        else:
            metadata[key] = value.upper()
    if isinstance(payload.get("files"), list):
        for index, item in enumerate(payload["files"]):
            if not isinstance(item, dict):
                errors.append(f"{rel(path)}: files[{index}] must be an object")
                continue
            raw_path = item.get("path")
            raw_sha = item.get("sha256")
            if not isinstance(raw_path, str) or not raw_path.strip():
                errors.append(f"{rel(path)}: files[{index}].path must be non-empty")
                continue
            if not isinstance(raw_sha, str) or not SHA256_RE.fullmatch(raw_sha):
                errors.append(f"{rel(path)}: files[{index}].sha256 must be SHA-256")
                continue
            if raw_path in entries:
                errors.append(f"{rel(path)}: duplicate hash entry for {raw_path}")
            entries[raw_path] = raw_sha.upper()
    else:
        for raw_path, raw_sha in payload.items():
            if raw_path in {"raw_input_sha256", "normalized_input_fingerprint"}:
                continue
            if not isinstance(raw_sha, str) or not SHA256_RE.fullmatch(raw_sha):
                errors.append(f"{rel(path)}: hash for {raw_path!r} must be SHA-256")
                continue
            entries[str(raw_path)] = raw_sha.upper()

    if not entries:
        errors.append(f"{rel(path)}: hashes file must contain at least one file entry")
    return entries, metadata, errors


def command_errors(validator_id: str, command: Any) -> list[str]:
    if not isinstance(command, str) or not command.strip():
        return [f"{validator_id}: command must be non-empty"]
    normalized = normalize_command(command)
    return [
        f"{validator_id}: command missing {snippet!r}"
        for snippet in COMMAND_SNIPPETS[validator_id]
        if snippet not in normalized
    ]


def validator_result_errors(validator: dict[str, Any]) -> list[str]:
    validator_id = validator.get("id")
    prefix = str(validator_id)
    errors: list[str] = []
    if validator.get("verdict") != "PASS":
        errors.append(f"{prefix}: validator verdict must be PASS")
    result = validator.get("result")
    if result is not None and not isinstance(result, dict):
        errors.append(f"{prefix}: result must be an object when present")
        return errors

    if validator_id == "graph_completeness" and isinstance(result, dict):
        if result.get("collapse_positive") is not True:
            errors.append("graph_completeness: result.collapse_positive must be true")
        failures = result.get("failures")
        if failures not in (None, []):
            errors.append("graph_completeness: result.failures must be empty")
    if validator_id == "collapse_certificate_schema" and isinstance(result, dict):
        if result.get("certificate_valid") is not True:
            errors.append("collapse_certificate_schema: result.certificate_valid must be true")
    if validator_id == "output_grapher" and isinstance(result, dict):
        if result.get("reconstructible") is not True:
            errors.append("output_grapher: result.reconstructible must be true")
        warnings = result.get("warnings")
        if warnings not in (None, []):
            errors.append("output_grapher: result.warnings must be empty for --fail-on-warnings proof mode")
    return errors


def surface_errors(manifest_path: Path, case: dict[str, Any]) -> list[str]:
    entries = case.get("surface_evidence")
    if not isinstance(entries, list) or not entries:
        return ["surface_evidence: must be a non-empty array"]
    errors: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(entries):
        label = f"surface_evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label}: must be an object")
            continue
        surface = item.get("surface")
        if surface not in REQUIRED_SURFACES:
            errors.append(f"{label}.surface: unsupported surface {surface!r}")
            continue
        seen.add(surface)
        path, error = resolve_manifest_path(manifest_path, item.get("path"))
        if error:
            errors.append(f"{label}.path: {error}")
            continue
        assert path is not None
        if not path.exists():
            errors.append(f"{label}.path: {rel(path)} missing")
            continue
        needles = item.get("needles")
        if isinstance(item.get("needle"), str):
            needles = [item["needle"]]
        if not isinstance(needles, list) or not needles or not all(isinstance(value, str) and value for value in needles):
            errors.append(f"{label}.needles: must be a non-empty array of strings")
            continue
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                errors.append(f"{label}: needle {needle!r} not found in {rel(path)}")
    missing = sorted(REQUIRED_SURFACES - seen)
    if missing:
        errors.append(f"surface_evidence: missing required surfaces {missing}")
    return errors


def artifact_errors(manifest_path: Path, case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    paths: dict[str, Path] = {}
    for field in ARTIFACT_FIELDS:
        path, error = resolve_manifest_path(manifest_path, case.get(field))
        if error:
            errors.append(f"{field}: {error}")
            continue
        assert path is not None
        paths[field] = path
        if not path.exists():
            errors.append(f"{field}: {rel(path)} missing")

    hashes_path = paths.get("hashes")
    if hashes_path is not None and hashes_path.exists():
        hash_entries, metadata, found = hash_manifest(hashes_path)
        errors.extend(found)
        for field in ("input", "output", "collapse_certificate", "grapher_html"):
            path = paths.get(field)
            if path is None or not path.exists():
                continue
            rel_to_manifest = str(Path(case[field]).as_posix()) if isinstance(case.get(field), str) else field
            expected = hash_entries.get(rel_to_manifest)
            if expected is None:
                errors.append(f"hashes: missing entry for {rel_to_manifest}")
                continue
            actual = sha256_file(path)
            if expected != actual:
                errors.append(f"hashes: {rel_to_manifest} expected {expected} but found {actual}")
        input_path = paths.get("input")
        if input_path is not None and input_path.exists():
            raw_input_sha = sha256_file(input_path)
            if metadata.get("raw_input_sha256") != raw_input_sha:
                errors.append(
                    "hashes: raw_input_sha256 must match input.md byte SHA-256 "
                    f"{raw_input_sha}"
                )
            normalized_fingerprint = input_fingerprint_for_path(input_path).upper()
            if metadata.get("normalized_input_fingerprint") != normalized_fingerprint:
                errors.append(
                    "hashes: normalized_input_fingerprint must match B.4-normalized "
                    f"input fingerprint {normalized_fingerprint}"
                )

    cert_path = paths.get("collapse_certificate")
    input_path = paths.get("input")
    if cert_path is not None and cert_path.exists():
        cert, found = load_json(cert_path)
        errors.extend(found)
        if isinstance(cert, dict):
            errors.extend(f"collapse_certificate: {error}" for error in certificate_errors(cert))
            if input_path is not None and input_path.exists():
                expected_fingerprint = input_fingerprint_for_path(input_path)
                if cert.get("input_fingerprint") != expected_fingerprint:
                    errors.append(
                        "collapse_certificate: input_fingerprint does not match "
                        f"B.4-normalized input hash {expected_fingerprint}"
                    )
        elif cert is not None:
            errors.append("collapse_certificate: root must be an object")
    return errors


def case_errors(manifest_path: Path, case: Any) -> list[str]:
    if not isinstance(case, dict):
        return ["case entry must be an object"]
    errors: list[str] = []
    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        errors.append("id: must be non-empty")
    prompt_sha = case.get("prompt_sha")
    if not isinstance(prompt_sha, str) or not SHA256_RE.fullmatch(prompt_sha):
        errors.append("prompt_sha: must be SHA-256")

    validators = case.get("validators")
    if not isinstance(validators, list):
        errors.append("validators: must be an array")
    else:
        seen: list[str] = []
        for index, validator in enumerate(validators):
            if not isinstance(validator, dict):
                errors.append(f"validators[{index}]: must be an object")
                continue
            validator_id = validator.get("id")
            if validator_id not in REQUIRED_VALIDATOR_ORDER:
                errors.append(f"validators[{index}].id: unsupported validator {validator_id!r}")
                continue
            seen.append(validator_id)
            errors.extend(command_errors(validator_id, validator.get("command")))
            errors.extend(validator_result_errors(validator))
        if seen != REQUIRED_VALIDATOR_ORDER:
            errors.append(f"validators: must appear in required D.1 order {REQUIRED_VALIDATOR_ORDER}")

    errors.extend(artifact_errors(manifest_path, case))
    errors.extend(surface_errors(manifest_path, case))
    return errors


def manifest_errors(path: Path) -> list[str]:
    payload, errors = load_json(path)
    if errors:
        return errors
    if not isinstance(payload, dict):
        return [f"{rel(path)}: manifest root must be an object"]

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: must be {SCHEMA_VERSION!r}")
    if payload.get("corpus_id") != CORPUS_ID:
        errors.append(f"corpus_id: must be {CORPUS_ID!r}")
    skill_sha = payload.get("generated_skill_sha")
    if not isinstance(skill_sha, str) or not SHA256_RE.fullmatch(skill_sha):
        errors.append("generated_skill_sha: must be SHA-256")
    if payload.get("release_provenance_status") != FROZEN_RELEASE_STATUS:
        errors.append(f"release_provenance_status: must be {FROZEN_RELEASE_STATUS!r}")
    if payload.get("stop_condition") != STOP_CONDITION:
        errors.append(f"stop_condition: must be {STOP_CONDITION!r}")
    if payload.get("validator_order") != REQUIRED_VALIDATOR_ORDER:
        errors.append("validator_order: must match the required D.1 validator order")

    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases: must be a non-empty array")
    else:
        seen_cases: set[str] = set()
        for index, case in enumerate(cases):
            case_id = case.get("id") if isinstance(case, dict) else f"case-{index}"
            prefix = f"cases[{index}]"
            if isinstance(case_id, str) and case_id in seen_cases:
                errors.append(f"{prefix}: duplicate case id {case_id}")
            elif isinstance(case_id, str):
                seen_cases.add(case_id)
            errors.extend(f"{prefix}: {error}" for error in case_errors(path, case))
    return errors


def schema_errors(schema_path: Path = SCHEMA_PATH) -> list[str]:
    payload, errors = load_json(schema_path)
    if errors:
        return errors
    if not isinstance(payload, dict):
        return [f"{rel(schema_path)}: schema root must be an object"]
    result: list[str] = []
    if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        result.append(f"{rel(schema_path)}: unexpected $schema")
    if payload.get("$id") != "schema/hard-smoke-manifest.schema.json":
        result.append(f"{rel(schema_path)}: unexpected $id")
    if payload.get("type") != "object":
        result.append(f"{rel(schema_path)}: root type must be object")
    if payload.get("additionalProperties") is not False:
        result.append(f"{rel(schema_path)}: root additionalProperties must be false")
    required = set(payload.get("required", []))
    if required != REQUIRED_MANIFEST_FIELDS:
        result.append(
            f"{rel(schema_path)}: required fields mismatch: "
            f"{sorted(required ^ REQUIRED_MANIFEST_FIELDS)}"
        )
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        result.append(f"{rel(schema_path)}: properties must be an object")
    else:
        missing = sorted(REQUIRED_MANIFEST_FIELDS - set(properties))
        extra = sorted(set(properties) - ALLOWED_MANIFEST_FIELDS)
        if missing:
            result.append(f"{rel(schema_path)}: required properties missing schema entries: {missing}")
        if extra:
            result.append(f"{rel(schema_path)}: unexpected root properties: {extra}")
    return result


def manifest_paths(root: Path, kind: str) -> list[Path]:
    base = root / kind
    if not base.exists():
        return []
    return sorted(base.glob("*/manifest.json"))


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


def run_fixture_suite(root: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    if not root.exists():
        return [f"{rel(root)}: fixture root missing"], valid_checked, invalid_checked

    for path in manifest_paths(root, "valid"):
        found = manifest_errors(path)
        if found:
            errors.append(f"{rel(path)}: expected-valid manifest failed")
            errors.extend(f"{rel(path)}: {error}" for error in found)
        else:
            valid_checked += 1

    for path in manifest_paths(root, "invalid"):
        found = manifest_errors(path)
        if found:
            invalid_checked += 1
        else:
            errors.append(f"{rel(path)}: expected-invalid manifest unexpectedly passed")
    return errors, valid_checked, invalid_checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--manifests", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors = schema_errors(args.schema)
    suite_errors, valid_checked, invalid_checked = run_fixture_suite(args.root)
    errors.extend(suite_errors)

    direct_checked = 0
    for path in expand_paths(args.manifests):
        found = manifest_errors(path)
        if found:
            errors.extend(f"{rel(path)}: {error}" for error in found)
        else:
            direct_checked += 1

    if errors:
        print("hard-smoke manifest check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("hard-smoke manifest check: PASS")
    print(f"Valid manifests checked: {valid_checked}")
    print(f"Invalid manifests checked: {invalid_checked}")
    if args.manifests:
        print(f"Direct manifests checked: {direct_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
