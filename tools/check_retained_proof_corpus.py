#!/usr/bin/env python3
"""Validate retained schema-light governed proof corpus manifests.

This checker binds promoted governed-output proof artifacts to their raw input,
checker-owned collapse certificate, warning-clean certificate-backed Grapher
HTML, and repository-normalized text hashes. It is a corpus integrity gate, not
proof by itself; the row-specific validators remain the proof authority.
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
FIXTURE_ROOT = ROOT / "tests" / "retained-proof-corpus" / "v0.4.3.0-schema-light"
SCHEMA_VERSION = "v0.4.3.0-retained-proof-corpus-v1"
CLASSIFICATION = "SIDECAR_BACKED_PROOF"
SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")
CASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ROW_ID_RE = re.compile(r"^(?:A|B|C|D)\.[0-9]+|T_lang$")
ARTIFACT_FIELDS = ("input", "output", "collapse_certificate", "grapher_html")
REQUIRED_CASE_FIELDS = {
    "id",
    "classification",
    "rows",
    "generated_skill_sha",
    "origin",
    "input",
    "output",
    "collapse_certificate",
    "grapher_html",
    "hashes",
}
ALLOWED_CASE_FIELDS = set(REQUIRED_CASE_FIELDS)
REQUIRED_ROOT_FIELDS = {"schema_version", "corpus_id", "proof_boundary", "cases"}
ALLOWED_ROOT_FIELDS = set(REQUIRED_ROOT_FIELDS) | {"coverage_targets"}
CANONICAL_SIDECAR_MANIFEST = FIXTURE_ROOT / "valid" / "sidecar-backed" / "manifest.json"
REQUIRED_COVERAGE_TARGET_FIELDS = {"id", "description", "rows", "case_ids"}
ALLOWED_COVERAGE_TARGET_FIELDS = set(REQUIRED_COVERAGE_TARGET_FIELDS)


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


def sha256_artifact_bytes(data: bytes) -> str:
    if b"\x00" not in data:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_artifact_bytes(path.read_bytes())


def hash_portability_errors() -> list[str]:
    text_lf = sha256_artifact_bytes(b"alpha\nbeta\n")
    text_crlf = sha256_artifact_bytes(b"alpha\r\nbeta\r\n")
    binary_lf = sha256_artifact_bytes(b"alpha\x00\nbeta\n")
    binary_crlf = sha256_artifact_bytes(b"alpha\x00\r\nbeta\r\n")
    errors: list[str] = []
    if text_lf != text_crlf:
        errors.append("hash portability self-test: LF/CRLF text hashes differ")
    if binary_lf == binary_crlf:
        errors.append("hash portability self-test: binary-like hashes were normalized")
    return errors


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


def manifest_paths(root: Path, kind: str) -> list[Path]:
    base = root / kind
    if not base.exists():
        return []
    return sorted(base.glob("*/manifest.json"))


def resolve_manifest_path(manifest_path: Path, value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, "must be a non-empty string"
    path = Path(value)
    if path.is_absolute():
        return None, "must be relative to manifest"
    resolved = (manifest_path.parent / path).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        return None, "must resolve inside repository root"
    return resolved, None


def string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not value:
        return None
    if not all(isinstance(item, str) and item for item in value):
        return None
    return list(value)


def case_errors(manifest_path: Path, case: Any, index: int) -> list[str]:
    prefix = f"cases[{index}]"
    errors: list[str] = []
    if not isinstance(case, dict):
        return [f"{prefix}: must be an object"]

    missing = sorted(REQUIRED_CASE_FIELDS - set(case))
    extra = sorted(set(case) - ALLOWED_CASE_FIELDS)
    if missing:
        errors.append(f"{prefix}: missing fields {missing}")
    if extra:
        errors.append(f"{prefix}: unexpected fields {extra}")

    case_id = case.get("id")
    if not isinstance(case_id, str) or not CASE_ID_RE.match(case_id):
        errors.append(f"{prefix}.id: must be a stable kebab-case id")
        case_id = f"case-{index}"

    if case.get("classification") != CLASSIFICATION:
        errors.append(f"{prefix}.classification: must be {CLASSIFICATION}")

    rows = string_list(case.get("rows"))
    if rows is None:
        errors.append(f"{prefix}.rows: must be a non-empty array of strings")
    else:
        invalid_rows = [row for row in rows if not ROW_ID_RE.match(row)]
        if invalid_rows:
            errors.append(f"{prefix}.rows: invalid row ids {invalid_rows}")

    skill_sha = case.get("generated_skill_sha")
    if not isinstance(skill_sha, str) or not SHA256_RE.match(skill_sha):
        errors.append(f"{prefix}.generated_skill_sha: must be a SHA-256 hex digest")

    if not isinstance(case.get("origin"), str) or not case.get("origin"):
        errors.append(f"{prefix}.origin: must name the retained source artifact")

    paths: dict[str, Path] = {}
    for field in ARTIFACT_FIELDS:
        path, error = resolve_manifest_path(manifest_path, case.get(field))
        if error:
            errors.append(f"{prefix}.{field}: {error}")
            continue
        assert path is not None
        paths[field] = path
        if not path.exists():
            errors.append(f"{prefix}.{field}: {rel(path)} missing")

    hashes = case.get("hashes")
    if not isinstance(hashes, dict):
        errors.append(f"{prefix}.hashes: must be an object")
        hashes = {}
    for field in ARTIFACT_FIELDS:
        expected = hashes.get(field)
        if not isinstance(expected, str) or not SHA256_RE.match(expected):
            errors.append(f"{prefix}.hashes.{field}: must be a SHA-256 hex digest")
            continue
        path = paths.get(field)
        if path is None or not path.exists():
            continue
        actual = sha256_file(path)
        if expected.upper() != actual:
            errors.append(f"{prefix}.hashes.{field}: expected {expected.upper()} but found {actual}")

    cert_path = paths.get("collapse_certificate")
    cert: Any | None = None
    if cert_path is not None and cert_path.exists():
        cert, found = load_json(cert_path)
        errors.extend(f"{prefix}.collapse_certificate: {error}" for error in found)
        if cert is not None:
            errors.extend(f"{prefix}.collapse_certificate: {error}" for error in certificate_errors(cert))

    input_path = paths.get("input")
    if input_path is not None and input_path.exists() and isinstance(cert, dict):
        expected_fingerprint = input_fingerprint_for_path(input_path)
        if cert.get("input_fingerprint") != expected_fingerprint:
            errors.append(
                f"{prefix}.collapse_certificate.input_fingerprint: expected {expected_fingerprint} from input"
            )
        if cert.get("collapse_positive") is not True:
            errors.append(f"{prefix}.collapse_certificate.collapse_positive: must be true")
        if cert.get("coverage_complete") is not True:
            errors.append(f"{prefix}.collapse_certificate.coverage_complete: must be true")

    graph_path = paths.get("grapher_html")
    if graph_path is not None and graph_path.exists():
        text = read_text(graph_path)
        if "Verdict: reconstructible" not in text:
            errors.append(f"{prefix}.grapher_html: missing reconstructible verdict")
        if "No warnings." not in text:
            errors.append(f"{prefix}.grapher_html: missing warning-clean marker")

    output_path = paths.get("output")
    if output_path is not None and output_path.exists():
        text = read_text(output_path)
        if "field_witness" not in text:
            errors.append(f"{prefix}.output: missing field_witness")
        if "MRP(" not in text:
            errors.append(f"{prefix}.output: missing MRP trace")

    return errors


def manifest_errors(path: Path) -> list[str]:
    payload, errors = load_json(path)
    if errors:
        return errors
    if not isinstance(payload, dict):
        return [f"{rel(path)}: manifest root must be an object"]

    missing = sorted(REQUIRED_ROOT_FIELDS - set(payload))
    extra = sorted(set(payload) - ALLOWED_ROOT_FIELDS)
    if missing:
        errors.append(f"root: missing fields {missing}")
    if extra:
        errors.append(f"root: unexpected fields {extra}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: must be {SCHEMA_VERSION}")
    if not isinstance(payload.get("corpus_id"), str) or not payload.get("corpus_id"):
        errors.append("corpus_id: must be a non-empty string")
    if not isinstance(payload.get("proof_boundary"), str) or not payload.get("proof_boundary"):
        errors.append("proof_boundary: must describe the corpus boundary")

    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases: must be a non-empty array")
        return errors

    seen: set[str] = set()
    for index, case in enumerate(cases):
        if isinstance(case, dict) and isinstance(case.get("id"), str):
            if case["id"] in seen:
                errors.append(f"cases[{index}].id: duplicate id {case['id']}")
            seen.add(case["id"])
        errors.extend(case_errors(path, case, index))
    errors.extend(coverage_target_errors(path, payload))
    return errors


def coverage_target_errors(manifest_path: Path, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    targets = payload.get("coverage_targets")
    if targets is None:
        if manifest_path.resolve() == CANONICAL_SIDECAR_MANIFEST.resolve():
            errors.append("coverage_targets: canonical retained sidecar manifest must define row coverage targets")
        return errors
    if not isinstance(targets, list) or not targets:
        return ["coverage_targets: must be a non-empty array when present"]

    cases_by_id: dict[str, dict[str, Any]] = {
        case["id"]: case
        for case in payload.get("cases", [])
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }
    seen_targets: set[str] = set()
    for index, target in enumerate(targets):
        prefix = f"coverage_targets[{index}]"
        if not isinstance(target, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        missing = sorted(REQUIRED_COVERAGE_TARGET_FIELDS - set(target))
        extra = sorted(set(target) - ALLOWED_COVERAGE_TARGET_FIELDS)
        if missing:
            errors.append(f"{prefix}: missing fields {missing}")
        if extra:
            errors.append(f"{prefix}: unexpected fields {extra}")

        target_id = target.get("id")
        if not isinstance(target_id, str) or not CASE_ID_RE.match(target_id):
            errors.append(f"{prefix}.id: must be a stable kebab-case id")
        elif target_id in seen_targets:
            errors.append(f"{prefix}.id: duplicate target id {target_id}")
        else:
            seen_targets.add(target_id)

        if not isinstance(target.get("description"), str) or not target.get("description"):
            errors.append(f"{prefix}.description: must be a non-empty string")

        rows = string_list(target.get("rows"))
        if rows is None:
            errors.append(f"{prefix}.rows: must be a non-empty array of strings")
            rows = []
        else:
            invalid_rows = [row for row in rows if not ROW_ID_RE.match(row)]
            if invalid_rows:
                errors.append(f"{prefix}.rows: invalid row ids {invalid_rows}")

        case_ids = string_list(target.get("case_ids"))
        if case_ids is None:
            errors.append(f"{prefix}.case_ids: must be a non-empty array of strings")
            case_ids = []

        seen_case_ids: set[str] = set()
        for case_id in case_ids:
            if case_id in seen_case_ids:
                errors.append(f"{prefix}.case_ids: duplicate case id {case_id}")
                continue
            seen_case_ids.add(case_id)
            case = cases_by_id.get(case_id)
            if case is None:
                errors.append(f"{prefix}.case_ids: unknown case id {case_id}")
                continue
            case_rows = set(string_list(case.get("rows")) or [])
            missing_rows = [row for row in rows if row not in case_rows]
            if missing_rows:
                errors.append(f"{prefix}.case_ids.{case_id}: missing target rows {missing_rows}")
    return errors


def coverage_target_count(path: Path) -> int:
    payload, errors = load_json(path)
    if errors or not isinstance(payload, dict):
        return 0
    targets = payload.get("coverage_targets")
    return len(targets) if isinstance(targets, list) else 0


def run_fixture_suite(root: Path) -> tuple[list[str], int, int, int]:
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    coverage_targets_checked = 0
    if not root.exists():
        return [f"{rel(root)}: fixture root missing"], valid_checked, invalid_checked, coverage_targets_checked

    for path in manifest_paths(root, "valid"):
        found = manifest_errors(path)
        if found:
            errors.append(f"{rel(path)}: expected-valid manifest failed")
            errors.extend(f"{rel(path)}: {error}" for error in found)
        else:
            valid_checked += 1
            coverage_targets_checked += coverage_target_count(path)

    for path in manifest_paths(root, "invalid"):
        found = manifest_errors(path)
        if found:
            invalid_checked += 1
        else:
            errors.append(f"{rel(path)}: expected-invalid manifest unexpectedly passed")
    return errors, valid_checked, invalid_checked, coverage_targets_checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--manifests", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors, valid_checked, invalid_checked, coverage_targets_checked = run_fixture_suite(args.root)
    direct_checked = 0
    for path in expand_paths(args.manifests):
        found = manifest_errors(path)
        if found:
            errors.extend(f"{rel(path)}: {error}" for error in found)
        else:
            direct_checked += 1
            coverage_targets_checked += coverage_target_count(path)

    errors.extend(hash_portability_errors())

    if errors:
        print("retained proof corpus check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("retained proof corpus check: PASS")
    print(f"Valid manifests checked: {valid_checked}")
    print(f"Invalid manifests checked: {invalid_checked}")
    if coverage_targets_checked:
        print(f"Coverage targets checked: {coverage_targets_checked}")
    if args.manifests:
        print(f"Direct manifests checked: {direct_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
