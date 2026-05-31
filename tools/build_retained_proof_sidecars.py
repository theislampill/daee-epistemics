#!/usr/bin/env python3
"""Build checker-owned retained proof sidecars for a governed output.

This helper is a B.2/B.4 convenience wrapper. It emits the collapse
certificate and warning-clean certificate-backed Grapher HTML from the current
checker stack, then writes repository-normalized hashes. It is not proof by
itself: row-specific validators and orchestrator evidence remain required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from check_collapse_certificate_schema import certificate_errors
from check_graph_completeness import input_fingerprint_for_path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "v0.4.3.0-retained-proof-sidecars-v1"
SELF_TEST_CASE = (
    ROOT
    / "tests"
    / "retained-proof-corpus"
    / "v0.4.3.0-schema-light"
    / "valid"
    / "sidecar-backed"
    / "cases"
    / "a9-science-source"
)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_artifact_bytes(data: bytes) -> str:
    if b"\x00" not in data:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_artifact_bytes(path.read_bytes())


def resolve_existing(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise SystemExit(f"{label} does not exist or is not a file: {path}")
    return resolved


def ensure_writable(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        joined = " ".join(command)
        raise SystemExit(
            f"command failed ({result.returncode}): {joined}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def load_certificate(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"collapse certificate command did not emit JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("collapse certificate command emitted a non-object JSON payload")
    errors = certificate_errors(payload)
    if errors:
        joined = "\n- ".join(errors)
        raise SystemExit(f"collapse certificate failed schema validation:\n- {joined}")
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def build_sidecars(input_path: Path, output_path: Path, out_dir: Path, prefix: str, force: bool) -> dict[str, Path]:
    input_path = resolve_existing(input_path, "input")
    output_path = resolve_existing(output_path, "output")
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    certificate_path = out_dir / f"{prefix}.collapse-certificate.json"
    grapher_path = out_dir / f"{prefix}.grapher.html"
    hashes_path = out_dir / f"{prefix}.hashes.json"
    for path in (certificate_path, grapher_path, hashes_path):
        ensure_writable(path, force)

    cert_result = run_command(
        [
            sys.executable,
            str(ROOT / "tools" / "check_graph_completeness.py"),
            "--outputs",
            str(output_path),
            "--certificate",
            "--input",
            str(input_path),
        ]
    )
    certificate = load_certificate(cert_result.stdout)
    expected_fingerprint = input_fingerprint_for_path(input_path)
    if certificate.get("input_fingerprint") != expected_fingerprint:
        raise SystemExit(
            "generated certificate input_fingerprint does not match raw input: "
            f"expected {expected_fingerprint}, found {certificate.get('input_fingerprint')}"
        )
    write_json(certificate_path, certificate)

    run_command(
        [
            sys.executable,
            str(ROOT / "tools" / "check_collapse_certificate_schema.py"),
            "--certificates",
            str(certificate_path),
        ]
    )

    run_command(
        [
            sys.executable,
            str(ROOT / "tools" / "check_output_grapher.py"),
            "--skill-output",
            str(output_path),
            "--expect-reconstructible",
            "--fail-on-warnings",
            "--input",
            str(input_path),
            "--collapse-certificate",
            str(certificate_path),
            "--out",
            str(grapher_path),
        ]
    )

    hashes = {
        "schema_version": SCHEMA_VERSION,
        "input": rel(input_path),
        "output": rel(output_path),
        "artifacts": {
            "input": sha256_file(input_path),
            "output": sha256_file(output_path),
            "collapse_certificate": sha256_file(certificate_path),
            "grapher_html": sha256_file(grapher_path),
        },
    }
    write_json(hashes_path, hashes)

    graph_text = grapher_path.read_text(encoding="utf-8", errors="replace")
    if "Verdict: reconstructible" not in graph_text:
        raise SystemExit("generated Grapher HTML is missing reconstructible verdict")
    if "No warnings." not in graph_text:
        raise SystemExit("generated Grapher HTML is not warning-clean")

    return {
        "collapse_certificate": certificate_path,
        "grapher_html": grapher_path,
        "hashes": hashes_path,
    }


def run_self_test() -> int:
    input_path = SELF_TEST_CASE / "input.txt"
    output_path = SELF_TEST_CASE / "output.md"
    with tempfile.TemporaryDirectory(prefix="retained-sidecars-") as raw_tmp:
        paths = build_sidecars(input_path, output_path, Path(raw_tmp), "self-test", force=False)
        for label, path in paths.items():
            if not path.is_file():
                raise SystemExit(f"self-test did not write {label}: {path}")
    print("retained proof sidecar builder self-test: PASS")
    print(f"input: {rel(input_path)}")
    print(f"output: {rel(output_path)}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Raw D0 input sidecar.")
    parser.add_argument("--output", type=Path, help="Governed output Markdown.")
    parser.add_argument("--out-dir", type=Path, help="Directory for generated sidecars.")
    parser.add_argument("--prefix", default="", help="Output filename prefix. Defaults to the output stem.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing sidecar files.")
    parser.add_argument("--self-test", action="store_true", help="Run a non-destructive smoke using a retained corpus case.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()
    if args.input is None or args.output is None or args.out_dir is None:
        raise SystemExit("--input, --output, and --out-dir are required unless --self-test is used")
    prefix = args.prefix or args.output.stem
    paths = build_sidecars(args.input, args.output, args.out_dir, prefix, force=args.force)
    print("retained proof sidecar build: PASS")
    for label, path in paths.items():
        print(f"{label}: {rel(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
