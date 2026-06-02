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
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from check_collapse_certificate_schema import certificate_errors
from check_graph_completeness import input_fingerprint_for_path
from check_retained_proof_corpus import (
    B5_FULL_IR_SIDECAR_BUILDER,
    B5_FULL_IR_SIDECAR_FIELD,
    B5_FULL_IR_SIDECAR_SCHEMA,
    PROOF_MODE_FULL_IR_TARGET_ID,
    SCHEMA_VERSION,
    manifest_errors,
)
from check_smoke_artifacts import validate_hash_record_file


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
OPTIONAL_ARTIFACT_NAMES = {
    B5_FULL_IR_SIDECAR_FIELD: "b5-full-ir-projection-sidecar.json",
}
OPTIONAL_CASE_FIELDS = {B5_FULL_IR_SIDECAR_FIELD}
HASH_RECORD_ARTIFACT_MAP = {
    "input": ("proof_sidecars", "raw_input"),
    "output": ("output",),
    "collapse_certificate": ("proof_sidecars", "collapse_certificate"),
    "grapher_html": ("proof_sidecars", "grapher_html"),
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


def raw_sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def run_checked(command: list[str]) -> None:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        raise SystemExit(result.stdout.strip() or f"command failed: {' '.join(command)}")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_self_test_hash_record(
    path: Path,
    *,
    case_name: str,
    generated_skill_sha: str,
    output_path: Path,
    input_path: Path,
    cert_path: Path,
    graph_path: Path,
    sidecar_hashes_path: Path,
    output_sha: str | None = None,
) -> None:
    write_json(
        path,
        {
            "case_name": case_name,
            "skill": {
                "sha256": generated_skill_sha,
            },
            "output": {
                "path": str(output_path),
                "sha256": output_sha or raw_sha256_file(output_path),
            },
            "proof_sidecars": {
                "raw_input": {
                    "path": str(input_path),
                    "sha256": raw_sha256_file(input_path),
                },
                "collapse_certificate": {
                    "path": str(cert_path),
                    "sha256": raw_sha256_file(cert_path),
                },
                "grapher_html": {
                    "path": str(graph_path),
                    "sha256": raw_sha256_file(graph_path),
                },
                "hashes": {
                    "path": str(sidecar_hashes_path),
                    "sha256": raw_sha256_file(sidecar_hashes_path),
                },
                "command": "self-test",
            },
        },
    )


def resolve_existing(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.exists() or not resolved.is_file():
        raise SystemExit(f"{label} does not exist or is not a file: {path}")
    return resolved


def resolve_record_path(path_value: str, record_path: Path) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate
    return record_path.parent / candidate


def hash_record_entry(payload: dict[str, Any], path_keys: tuple[str, ...], label: str) -> dict[str, Any]:
    value: Any = payload
    for key in path_keys:
        if not isinstance(value, dict) or key not in value:
            raise SystemExit(f"hash record missing {label} entry")
        value = value[key]
    if not isinstance(value, dict):
        raise SystemExit(f"hash record {label} entry must be an object")
    return value


def path_from_hash_record(payload: dict[str, Any], record_path: Path, path_keys: tuple[str, ...], label: str) -> Path:
    entry = hash_record_entry(payload, path_keys, label)
    path_value = entry.get("path")
    if not isinstance(path_value, str) or not path_value.strip():
        raise SystemExit(f"hash record {label} entry lacks path")
    source_path = resolve_existing(resolve_record_path(path_value, record_path), label)
    sha_value = entry.get("sha256")
    if isinstance(sha_value, str) and sha_value.strip():
        actual = raw_sha256_file(source_path)
        expected = sha_value.strip().upper()
        if actual != expected:
            raise SystemExit(
                f"hash record {label} sha256 mismatch: expected {expected}, found {actual}"
            )
    return source_path


def source_paths_from_hash_record(record_path: Path) -> tuple[dict[str, Path], str | None, str | None]:
    record_path = require_under_root(record_path, "hash record")
    record_path = resolve_existing(record_path, "hash record")
    errors = validate_hash_record_file(record_path)
    if errors:
        joined = "\n- ".join(errors)
        raise SystemExit(f"hash record failed proof_sidecars validation:\n- {joined}")

    payload = load_json(record_path)
    if not isinstance(payload, dict):
        raise SystemExit("hash record root must be a JSON object")

    source_paths = {
        field: path_from_hash_record(payload, record_path, path_keys, field)
        for field, path_keys in HASH_RECORD_ARTIFACT_MAP.items()
    }
    for field, source_path in source_paths.items():
        require_under_root(source_path, f"hash record {field}")

    origin = None
    output_entry = hash_record_entry(payload, ("output",), "output")
    output_path_value = output_entry.get("path")
    if isinstance(output_path_value, str) and output_path_value.strip():
        origin = output_path_value.replace("\\", "/")

    generated_skill_sha = None
    skill_entry = payload.get("skill")
    if isinstance(skill_entry, dict):
        skill_sha = skill_entry.get("sha256")
        if isinstance(skill_sha, str) and skill_sha.strip():
            generated_skill_sha = skill_sha.strip().upper()
    return source_paths, origin, generated_skill_sha


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
    entry = {
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
    if B5_FULL_IR_SIDECAR_FIELD in source_paths:
        sidecar_path = retained_paths[B5_FULL_IR_SIDECAR_FIELD]
        entry[B5_FULL_IR_SIDECAR_FIELD] = {
            "schema": B5_FULL_IR_SIDECAR_SCHEMA,
            "path": manifest_relative(manifest_path, sidecar_path),
            "sha256": sha256_file(source_paths[B5_FULL_IR_SIDECAR_FIELD]),
            "builder": B5_FULL_IR_SIDECAR_BUILDER,
        }
    return entry


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
    extra_fields = sorted(set(existing) - set(expected) - OPTIONAL_CASE_FIELDS)
    missing_fields = sorted(set(expected) - set(existing))
    projected_existing = {key: existing.get(key) for key in expected}
    if missing_fields or extra_fields or projected_existing != expected:
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
    if B5_FULL_IR_SIDECAR_FIELD in expected and B5_FULL_IR_SIDECAR_FIELD in existing:
        retained_path = (manifest_path.parent / existing[B5_FULL_IR_SIDECAR_FIELD]["path"]).resolve()
        expected_hash = expected[B5_FULL_IR_SIDECAR_FIELD]["sha256"]
        if not retained_path.exists():
            errors.append(f"{existing[B5_FULL_IR_SIDECAR_FIELD]['path']} missing")
        else:
            actual_hash = sha256_file(retained_path)
            if actual_hash != expected_hash:
                errors.append(
                    f"{existing[B5_FULL_IR_SIDECAR_FIELD]['path']} hash drift: "
                    f"expected {expected_hash}, found {actual_hash}"
                )
    return errors


def add_case_to_coverage_targets(manifest: dict[str, Any], expected: dict[str, Any]) -> None:
    targets = manifest.get("coverage_targets")
    if not isinstance(targets, list):
        return
    case_id = expected["id"]
    case_rows = set(expected.get("rows") or [])
    has_b5_sidecar = B5_FULL_IR_SIDECAR_FIELD in expected
    for target in targets:
        if not isinstance(target, dict):
            continue
        target_rows = target.get("rows")
        case_ids = target.get("case_ids")
        if not isinstance(target_rows, list) or not isinstance(case_ids, list):
            continue
        target_id = target.get("id")
        should_add = set(target_rows).issubset(case_rows)
        if target_id == PROOF_MODE_FULL_IR_TARGET_ID:
            should_add = has_b5_sidecar and "B.5" in case_rows
        if should_add and case_id not in case_ids:
            case_ids.append(case_id)


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
    if B5_FULL_IR_SIDECAR_FIELD in expected:
        retained_paths[B5_FULL_IR_SIDECAR_FIELD] = (
            manifest_path.parent / expected[B5_FULL_IR_SIDECAR_FIELD]["path"]
        ).resolve()
    for path in retained_paths.values():
        require_under_root(path, "retained artifact path")
        path.parent.mkdir(parents=True, exist_ok=True)
    for field, source in source_paths.items():
        if field == B5_FULL_IR_SIDECAR_FIELD:
            continue
        shutil.copyfile(source, retained_paths[field])
    if B5_FULL_IR_SIDECAR_FIELD in source_paths:
        run_checked(
            [
                sys.executable,
                str(ROOT / B5_FULL_IR_SIDECAR_BUILDER),
                "--input",
                str(retained_paths["input"]),
                "--output",
                str(retained_paths["output"]),
                "--collapse-certificate",
                str(retained_paths["collapse_certificate"]),
                "--grapher-html",
                str(retained_paths["grapher_html"]),
                "--out",
                str(retained_paths[B5_FULL_IR_SIDECAR_FIELD]),
            ]
        )
        expected[B5_FULL_IR_SIDECAR_FIELD]["sha256"] = sha256_file(
            retained_paths[B5_FULL_IR_SIDECAR_FIELD]
        )

    if index is None:
        cases.append(expected)
    else:
        cases[index] = expected
    add_case_to_coverage_targets(manifest, expected)
    write_json(manifest_path, manifest)

    errors = manifest_errors(manifest_path)
    if errors:
        joined = "\n- ".join(errors)
        raise SystemExit(f"updated manifest failed validation:\n- {joined}")


def self_test() -> int:
    manifest_path = DEFAULT_MANIFEST
    rows = ["A.9", "B.1", "B.2", "B.3", "B.4", "B.5"]
    origin = (
        ".daee/a9-delta-vocabulary-smokes/"
        "20260530-current-skill-60a9-science-source-v1/"
        "a9-science-source-current-skill-60a9-run1.md"
    )
    generated_skill_sha = "60A90DCA3AAEFD9BCCD2981A5FF9D8BCB4906D49026EED89F7392CCACED565D3"
    case_dir = manifest_path.parent / "cases" / "a9-science-source"
    retained_paths = {
        field: case_dir / artifact_name
        for field, artifact_name in ARTIFACT_NAMES.items()
    }

    scratch_root = ROOT / ".daee" / "validation"
    scratch_root.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="promote-hash-record-", dir=scratch_root) as scratch_dir_name:
        scratch_dir = Path(scratch_dir_name)
        sidecar_hashes = scratch_dir / "sidecar.hashes.json"
        write_json(
            sidecar_hashes,
            {
                "schema_version": "v0.4.3.0-retained-proof-sidecars-v1",
                "input": rel(retained_paths["input"]),
                "output": rel(retained_paths["output"]),
                "artifacts": {
                    "input": sha256_file(retained_paths["input"]),
                    "output": sha256_file(retained_paths["output"]),
                    "collapse_certificate": sha256_file(retained_paths["collapse_certificate"]),
                    "grapher_html": sha256_file(retained_paths["grapher_html"]),
                },
            },
        )

        valid_record = scratch_dir / "smoke.hashes.json"
        write_self_test_hash_record(
            valid_record,
            case_name="promote-a9-from-smoke-hash-record",
            generated_skill_sha=generated_skill_sha,
            output_path=retained_paths["output"],
            input_path=retained_paths["input"],
            cert_path=retained_paths["collapse_certificate"],
            graph_path=retained_paths["grapher_html"],
            sidecar_hashes_path=sidecar_hashes,
        )
        source_paths, _, record_generated_skill_sha = source_paths_from_hash_record(valid_record)
        if record_generated_skill_sha != generated_skill_sha:
            print("retained proof case promotion self-test: FAIL")
            print("- generated skill SHA did not round-trip from hash record")
            return 1
        validate_source_artifacts(
            source_paths["input"],
            source_paths["output"],
            source_paths["collapse_certificate"],
            source_paths["grapher_html"],
        )
        expected = build_entry(
            manifest_path,
            "a9-science-source",
            rows,
            generated_skill_sha,
            origin,
            retained_paths,
            source_paths,
        )
        errors = compare_existing(manifest_path, expected)
        if errors:
            print("retained proof case promotion self-test: FAIL")
            for error in errors:
                print(f"- {error}")
            return 1

        invalid_record = scratch_dir / "stale-output.hashes.json"
        write_self_test_hash_record(
            invalid_record,
            case_name="promotion-stale-output",
            generated_skill_sha=generated_skill_sha,
            output_path=retained_paths["output"],
            input_path=retained_paths["input"],
            cert_path=retained_paths["collapse_certificate"],
            graph_path=retained_paths["grapher_html"],
            sidecar_hashes_path=sidecar_hashes,
            output_sha="0" * 64,
        )
        try:
            source_paths_from_hash_record(invalid_record)
        except SystemExit as exc:
            stale_output_markers = (
                "hash record output sha256 mismatch",
                "output sha256 mismatch",
            )
            if not any(marker in str(exc) for marker in stale_output_markers):
                print("retained proof case promotion self-test: FAIL")
                print(f"- stale-output canary failed with unexpected error: {exc}")
                return 1
        else:
            print("retained proof case promotion self-test: FAIL")
            print("- stale-output canary was not rejected")
            return 1

    print("retained proof case promotion self-test: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--case-id")
    parser.add_argument("--rows", nargs="+")
    parser.add_argument("--generated-skill-sha")
    parser.add_argument("--origin")
    parser.add_argument("--hash-record", type=Path, help="read output and proof sidecar paths from a smoke *.hashes.json record")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--collapse-certificate", type=Path)
    parser.add_argument("--grapher-html", type=Path)
    parser.add_argument("--b5-full-ir-projection-sidecar", type=Path)
    parser.add_argument("--case-dir", type=Path)
    parser.add_argument("--check", action="store_true", help="validate against an existing retained case without writing")
    parser.add_argument("--source-only", action="store_true", help="validate source artifacts or hash-record inputs without comparing or writing a retained manifest")
    parser.add_argument("--replace", action="store_true", help="replace an existing manifest case in write mode")
    parser.add_argument("--self-test", action="store_true", help="run promotion-helper hash-record self-tests")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    if args.source_only:
        if args.hash_record:
            manual_artifacts = [args.input, args.output, args.collapse_certificate, args.grapher_html]
            if any(manual_artifacts):
                raise SystemExit("--hash-record cannot be combined with manual artifact path arguments")
            source_paths, _, _ = source_paths_from_hash_record(args.hash_record)
            if args.b5_full_ir_projection_sidecar:
                source_paths[B5_FULL_IR_SIDECAR_FIELD] = resolve_existing(
                    args.b5_full_ir_projection_sidecar,
                    "B.5 full-IR projection sidecar",
                )
        else:
            if not all([args.input, args.output, args.collapse_certificate, args.grapher_html]):
                raise SystemExit(
                    "--source-only requires --hash-record or manual --input, --output, "
                    "--collapse-certificate, and --grapher-html"
                )
            source_paths = {
                "input": resolve_existing(args.input, "input"),
                "output": resolve_existing(args.output, "output"),
                "collapse_certificate": resolve_existing(args.collapse_certificate, "collapse certificate"),
                "grapher_html": resolve_existing(args.grapher_html, "Grapher HTML"),
            }
            if args.b5_full_ir_projection_sidecar:
                source_paths[B5_FULL_IR_SIDECAR_FIELD] = resolve_existing(
                    args.b5_full_ir_projection_sidecar,
                    "B.5 full-IR projection sidecar",
                )
        validate_source_artifacts(
            source_paths["input"],
            source_paths["output"],
            source_paths["collapse_certificate"],
            source_paths["grapher_html"],
        )
        print("retained proof case promotion source-artifact check: PASS")
        return 0
    if not args.case_id:
        raise SystemExit("--case-id is required")
    if not args.rows:
        raise SystemExit("--rows is required")

    manifest_path = require_under_root(args.manifest, "manifest")
    if not manifest_path.exists():
        raise SystemExit(f"manifest does not exist: {manifest_path}")

    if args.hash_record:
        manual_artifacts = [args.input, args.output, args.collapse_certificate, args.grapher_html]
        if any(manual_artifacts):
            raise SystemExit("--hash-record cannot be combined with manual artifact path arguments")
        source_paths, record_origin, record_generated_skill_sha = source_paths_from_hash_record(args.hash_record)
        origin = args.origin or record_origin
        generated_skill_sha = args.generated_skill_sha or record_generated_skill_sha
        if args.b5_full_ir_projection_sidecar:
            source_paths[B5_FULL_IR_SIDECAR_FIELD] = resolve_existing(
                args.b5_full_ir_projection_sidecar,
                "B.5 full-IR projection sidecar",
            )
    else:
        if not all([args.input, args.output, args.collapse_certificate, args.grapher_html]):
            raise SystemExit(
                "manual promotion requires --input, --output, --collapse-certificate, and --grapher-html"
            )
        source_paths = {
            "input": resolve_existing(args.input, "input"),
            "output": resolve_existing(args.output, "output"),
            "collapse_certificate": resolve_existing(args.collapse_certificate, "collapse certificate"),
            "grapher_html": resolve_existing(args.grapher_html, "Grapher HTML"),
        }
        if args.b5_full_ir_projection_sidecar:
            source_paths[B5_FULL_IR_SIDECAR_FIELD] = resolve_existing(
                args.b5_full_ir_projection_sidecar,
                "B.5 full-IR projection sidecar",
            )
        origin = args.origin
        generated_skill_sha = args.generated_skill_sha
    if not origin:
        raise SystemExit("--origin is required when it cannot be derived from --hash-record")
    if not generated_skill_sha:
        raise SystemExit("--generated-skill-sha is required when it cannot be derived from --hash-record")

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
    if B5_FULL_IR_SIDECAR_FIELD in source_paths:
        retained_paths[B5_FULL_IR_SIDECAR_FIELD] = (
            case_dir / OPTIONAL_ARTIFACT_NAMES[B5_FULL_IR_SIDECAR_FIELD]
        )
    expected = build_entry(
        manifest_path,
        args.case_id,
        args.rows,
        generated_skill_sha,
        origin,
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
