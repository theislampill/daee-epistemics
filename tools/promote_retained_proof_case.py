#!/usr/bin/env python3
"""Promote a governed smoke into the retained schema-light proof corpus.

This helper copies the canonical raw input, output, checker-owned collapse
certificate, and warning-clean certificate-backed Grapher HTML into a retained
case directory, then writes the manifest entry with repository-normalized text
hashes. It is a promotion helper only; row-specific validators remain the proof
authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from check_collapse_certificate_schema import certificate_errors
from check_graph_completeness import input_fingerprint_for_path
from check_retained_proof_corpus import SCHEMA_VERSION, manifest_errors


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    ROOT
    / "tests"
    / "retained-proof-corpus"
    / "v0.4.3.0-schema-light"
    / "valid"
    / "sidecar-backed"
    / "manifest.json"
)
ARTIFACT_NAMES = {
    "input": "input.txt",
    "output": "output.md",
    "collapse_certificate": "collapse-certificate.json",
    "grapher_html": "grapher.html",
}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    if b"\x00" not in data:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest().upper()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def resolve_existing(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.exists() or not resolved.is_file():
        raise SystemExit(f"{label} does not exist or is not a file: {path}")
    return resolved


def require_under_root(path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"{label} must resolve inside repository root: {path}") from exc
    return resolved


def manifest_relative(manifest_path: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(manifest_path.parent.resolve()).as_posix()
    except ValueError as exc:
        raise SystemExit(f"retained path must be under manifest directory: {path}") from exc


def validate_source_artifacts(input_path: Path, output_path: Path, cert_path: Path, graph_path: Path) -> None:
    cert = load_json(cert_path)
    errors = certificate_errors(cert)
    if errors:
        joined = "\n- ".join(errors)
        raise SystemExit(f"collapse certificate failed schema checks:\n- {joined}")

    expected_fingerprint = input_fingerprint_for_path(input_path)
    if cert.get("input_fingerprint") != expected_fingerprint:
        raise SystemExit(
            "collapse certificate input_fingerprint does not match input: "
            f"expected {expected_fingerprint}, found {cert.get('input_fingerprint')}"
        )
    if cert.get("collapse_positive") is not True:
        raise SystemExit("collapse certificate must have collapse_positive=true")
    if cert.get("coverage_complete") is not True:
        raise SystemExit("collapse certificate must have coverage_complete=true")

    graph_text = graph_path.read_text(encoding="utf-8", errors="replace")
    if "Verdict: reconstructible" not in graph_text:
        raise SystemExit("Grapher HTML is missing the reconstructible verdict")
    if "No warnings." not in graph_text:
        raise SystemExit("Grapher HTML is not warning-clean")

    output_text = output_path.read_text(encoding="utf-8", errors="replace")
    if "field_witness" not in output_text:
        raise SystemExit("output is missing field_witness")
    if "MRP(" not in output_text:
        raise SystemExit("output is missing MRP trace")


def build_entry(
    manifest_path: Path,
    case_id: str,
    rows: list[str],
    generated_skill_sha: str,
    origin: str,
    retained_paths: dict[str, Path],
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "id": case_id,
        "classification": "SIDECAR_BACKED_PROOF",
        "rows": rows,
        "generated_skill_sha": generated_skill_sha,
        "origin": origin.replace("\\", "/"),
        "input": manifest_relative(manifest_path, retained_paths["input"]),
        "output": manifest_relative(manifest_path, retained_paths["output"]),
        "collapse_certificate": manifest_relative(manifest_path, retained_paths["collapse_certificate"]),
        "grapher_html": manifest_relative(manifest_path, retained_paths["grapher_html"]),
        "hashes": {
            "input": sha256_file(source_paths["input"]),
            "output": sha256_file(source_paths["output"]),
            "collapse_certificate": sha256_file(source_paths["collapse_certificate"]),
            "grapher_html": sha256_file(source_paths["grapher_html"]),
        },
    }


def find_case(manifest: dict[str, Any], case_id: str) -> tuple[int | None, dict[str, Any] | None]:
    for index, case in enumerate(manifest.get("cases", [])):
        if isinstance(case, dict) and case.get("id") == case_id:
            return index, case
    return None, None


def compare_existing(manifest_path: Path, expected: dict[str, Any]) -> list[str]:
    manifest = load_json(manifest_path)
    _, existing = find_case(manifest, expected["id"])
    if existing is None:
        return [f"case id not present in manifest: {expected['id']}"]
    if existing != expected:
        return [
            "existing manifest entry differs from proposed entry",
            f"expected={json.dumps(expected, sort_keys=True, ensure_ascii=False)}",
            f"found={json.dumps(existing, sort_keys=True, ensure_ascii=False)}",
        ]

    errors: list[str] = []
    for field in ARTIFACT_NAMES:
        retained_path = (manifest_path.parent / existing[field]).resolve()
        expected_hash = expected["hashes"][field]
        if not retained_path.exists():
            errors.append(f"{existing[field]} missing")
            continue
        actual_hash = sha256_file(retained_path)
        if actual_hash != expected_hash:
            errors.append(f"{existing[field]} hash drift: expected {expected_hash}, found {actual_hash}")
    return errors


def promote(manifest_path: Path, expected: dict[str, Any], source_paths: dict[str, Path], replace: bool) -> None:
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise SystemExit("manifest root must be a JSON object")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit(f"manifest schema_version must be {SCHEMA_VERSION}")
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        raise SystemExit("manifest cases must be an array")

    index, existing = find_case(manifest, expected["id"])
    if existing is not None and not replace:
        raise SystemExit(f"case already exists; pass --replace to update: {expected['id']}")

    retained_paths = {
        field: (manifest_path.parent / expected[field]).resolve()
        for field in ARTIFACT_NAMES
    }
    for path in retained_paths.values():
        require_under_root(path, "retained artifact path")
        path.parent.mkdir(parents=True, exist_ok=True)
    for field, source in source_paths.items():
        shutil.copyfile(source, retained_paths[field])

    if index is None:
        cases.append(expected)
    else:
        cases[index] = expected
    write_json(manifest_path, manifest)

    errors = manifest_errors(manifest_path)
    if errors:
        joined = "\n- ".join(errors)
        raise SystemExit(f"updated manifest failed validation:\n- {joined}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--rows", nargs="+", required=True)
    parser.add_argument("--generated-skill-sha", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--collapse-certificate", type=Path, required=True)
    parser.add_argument("--grapher-html", type=Path, required=True)
    parser.add_argument("--case-dir", type=Path)
    parser.add_argument("--check", action="store_true", help="validate against an existing retained case without writing")
    parser.add_argument("--replace", action="store_true", help="replace an existing manifest case in write mode")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = require_under_root(args.manifest, "manifest")
    if not manifest_path.exists():
        raise SystemExit(f"manifest does not exist: {manifest_path}")

    source_paths = {
        "input": resolve_existing(args.input, "input"),
        "output": resolve_existing(args.output, "output"),
        "collapse_certificate": resolve_existing(args.collapse_certificate, "collapse certificate"),
        "grapher_html": resolve_existing(args.grapher_html, "Grapher HTML"),
    }
    validate_source_artifacts(
        source_paths["input"],
        source_paths["output"],
        source_paths["collapse_certificate"],
        source_paths["grapher_html"],
    )

    case_dir = args.case_dir or (manifest_path.parent / "cases" / args.case_id)
    case_dir = require_under_root(case_dir, "case directory")
    retained_paths = {
        field: case_dir / artifact_name
        for field, artifact_name in ARTIFACT_NAMES.items()
    }
    expected = build_entry(
        manifest_path,
        args.case_id,
        args.rows,
        args.generated_skill_sha,
        args.origin,
        retained_paths,
        source_paths,
    )

    if args.check:
        errors = compare_existing(manifest_path, expected)
        if errors:
            print("retained proof case promotion check: FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print("retained proof case promotion check: PASS")
        print(f"case: {args.case_id}")
        print(f"manifest: {rel(manifest_path)}")
        return 0

    promote(manifest_path, expected, source_paths, args.replace)
    print("retained proof case promotion: PASS")
    print(f"case: {args.case_id}")
    print(f"manifest: {rel(manifest_path)}")
    print(f"case_dir: {rel(case_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
