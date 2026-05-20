#!/usr/bin/env python3
"""Validate closure witness graph reconstructibility.

This checker is intentionally structural. It validates that a visible
Closure/Reconstruction Witness can reconstruct a burden DAG from text alone and,
when supplied, that a field_witness JSON sidecar matches the visible witness.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from closure_witness_lib import (
    closure_witness_errors,
    compare_visible_to_field_witness,
    extract_field_witness,
    field_witness_graph_errors,
    load_json,
    parse_closure_witness,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check(input_path: Path, field_witness_path: Path | None = None) -> list[str]:
    text = input_path.read_text(encoding="utf-8", errors="replace")
    witness = parse_closure_witness(text)
    errors = [f"{input_path}: {error}" for error in closure_witness_errors(witness)]
    if field_witness_path is not None:
        if not field_witness_path.is_file():
            return errors + [f"{field_witness_path}: field_witness file missing"]
        sidecar = extract_field_witness(load_json(field_witness_path))
        errors.extend(f"{field_witness_path}: {error}" for error in field_witness_graph_errors(sidecar))
        if witness is not None and sidecar is not None:
            errors.extend(
                f"{input_path} <-> {field_witness_path}: {error}"
                for error in compare_visible_to_field_witness(witness, sidecar)
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="Text/Markdown output with Closure/Reconstruction Witness")
    parser.add_argument("--field-witness", type=Path, help="Optional field_witness JSON or full IR JSON sidecar")
    args = parser.parse_args()

    errors = check(args.input, args.field_witness)
    if errors:
        print("closure witness graph check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("closure witness graph check: PASS")
    print(f"- {args.input}")
    if args.field_witness:
        print(f"- {args.field_witness}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
