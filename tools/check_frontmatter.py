#!/usr/bin/env python3
"""
check_frontmatter.py — Validate YAML operative front matter across skill module files.

Checks:
  1. YAML parses cleanly (no syntax errors)
  2. Required fields are present (id, module_class, canonical_path, contract_version)
  3. canonical_path matches the actual repo-relative path
  4. Runtime enum fields contain only allowed values
  5. Verification/status fields, when present, are internally consistent
  6. Deprecated transitional fields are absent from packaged front matter
  7. Legacy post-YAML blockquote metadata blocks are absent

Usage:
  python3 tools/check_frontmatter.py [--dir skill/references] [--verbose]
"""

import os
import sys
import re
import argparse

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

# ── Enums ──────────────────────────────────────────────────────────────────────

VALID_MODULE_CLASS = {
    "tactic", "technique", "procedure", "diagnostic",
    "case-library", "case_library", "governance", "rubric"
}

VALID_OUTPUT_SHAPES = {
    "bounded-single-pass", "held-pending-upstream",
    "recursive-traversal-permitted", "pass-through"
}

VALID_LAYER_CONSTRAINT = {
    "layer-a-only", "layer-b-permitted", "layer-b-governed"
}

VALID_VERIFICATION_STATUS = {"L_check", "L_tilde"}

REQUIRED_FIELDS = ["id", "module_class", "canonical_path", "contract_version"]

VERIFICATION_FLAGS = [
    "direct_read_verified",
    "failure_conditions_present",
    "ir_consequences_present",
    "minimal_pairs_present",
    "hold_release_rules_present",
    "compiled_runtime_eligible",
    "operator_pack_eligible",
]

LEGACY_BLOCKQUOTE_METADATA = {
    "role:",
    "use when:",
    "do not use when:",
    "output:",
}

DEPRECATED_FIELDS = {
    "load_class", "bundle", "execution_phase", "governs", "must_precede",
    "blocks_if_missing", "trigger_conditions", "operator_pack", "source_status",
    "direct_read_required",
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_frontmatter(path: str) -> tuple[dict | None, list[str]]:
    """Return (parsed_yaml, errors). errors is a list of string messages."""
    errors = []
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return None, [f"Cannot read file: {e}"]

    if not content.startswith("---"):
        return None, ["No YAML front matter (file does not start with '---')"]

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, ["Malformed front matter (only one '---' delimiter found)"]

    raw_yaml = parts[1]
    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        return None, [f"YAML parse error: {e}"]

    if not isinstance(data, dict):
        return None, ["Front matter does not parse to a mapping"]

    return data, errors


def check_required(data: dict) -> list[str]:
    return [f"Missing required field: '{f}'" for f in REQUIRED_FIELDS if f not in data]


def check_enum(data: dict, field: str, valid: set) -> list[str]:
    if field not in data:
        return []
    val = data[field]
    if isinstance(val, list):
        bad = [v for v in val if v not in valid]
        return [f"'{field}' contains invalid value(s): {bad} (allowed: {sorted(valid)})"] if bad else []
    if val not in valid:
        return [f"'{field}' = '{val}' is not a valid value (allowed: {sorted(valid)})"]
    return []


def check_deprecated_fields(data: dict) -> list[str]:
    found = sorted(field for field in DEPRECATED_FIELDS if field in data)
    if not found:
        return []
    return [
        "Deprecated transitional field(s) present in packaged front matter: "
        + ", ".join(found)
    ]


def check_verification_fields(data: dict) -> list[str]:
    present = [field for field in ["verification_status", *VERIFICATION_FLAGS] if field in data]
    if not present:
        return []

    errors = []
    if "verification_status" not in data:
        errors.append("Verification flag(s) present without verification_status")

    for field in VERIFICATION_FLAGS:
        if field in data and not isinstance(data[field], bool):
            errors.append(f"'{field}' must be boolean when present")

    if data.get("verification_status") == "L_check":
        missing = [field for field in VERIFICATION_FLAGS if field not in data]
        if missing:
            errors.append("L_check verification missing required flag(s): " + ", ".join(missing))
        false_flags = [field for field in VERIFICATION_FLAGS if data.get(field) is not True]
        if false_flags:
            errors.append("L_check verification requires true flag(s): " + ", ".join(false_flags))

    return errors


def check_canonical_path(data: dict, actual_path: str) -> list[str]:
    stated = data.get("canonical_path", "")
    if not stated:
        return []
    # canonical_path values use repo-root-relative paths (e.g. skill/references/...)
    # compute relative to cwd, which should be repo root
    rel = os.path.relpath(actual_path, os.getcwd()).replace("\\", "/")
    if stated != rel:
        return [f"canonical_path mismatch: stated '{stated}' vs. actual '{rel}'"]
    return []


def check_legacy_blockquote_metadata(path: str) -> list[str]:
    """Reject old '> role:' style metadata blocks near the top of YAML-bearing files."""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return [f"Cannot read file for legacy metadata check: {e}"]

    if not content.startswith("---"):
        return []

    parts = content.split("---", 2)
    if len(parts) < 3:
        return []

    errors = []
    non_empty_seen = 0
    for offset, line in enumerate(parts[2].splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        non_empty_seen += 1
        if non_empty_seen > 25:
            break
        lowered = line.lower()
        if lowered.startswith("> ") and any(
            lowered.startswith("> " + marker) for marker in LEGACY_BLOCKQUOTE_METADATA
        ):
            errors.append(
                f"Legacy blockquote metadata after YAML front matter at body line {offset}: {line}"
            )

    return errors


# ── Main ───────────────────────────────────────────────────────────────────────

def scan_dir(root: str, verbose: bool) -> tuple[int, int, int, int, int]:
    """Return (files_checked, files_with_errors, files_with_deprecated_fields, files_with_verification_fields, files_with_legacy_blocks)."""
    files_checked = 0
    files_with_errors = 0
    files_with_deprecated = 0
    files_with_verification = 0
    files_with_legacy_blocks = 0

    for dirpath, _dirs, filenames in os.walk(root):
        for fname in sorted(filenames):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(dirpath, fname)
            data, parse_errors = extract_frontmatter(fpath)
            files_checked += 1

            all_errors = list(parse_errors)

            if data is not None:
                all_errors += check_required(data)
                all_errors += check_enum(data, "module_class", VALID_MODULE_CLASS)
                all_errors += check_enum(data, "output_shapes", VALID_OUTPUT_SHAPES)
                all_errors += check_enum(data, "layer_constraint", VALID_LAYER_CONSTRAINT)
                all_errors += check_enum(data, "verification_status", VALID_VERIFICATION_STATUS)
                verification_errors = check_verification_fields(data)
                files_with_verification += 1 if any(
                    field in data for field in ["verification_status", *VERIFICATION_FLAGS]
                ) else 0
                all_errors += verification_errors
                deprecated_errors = check_deprecated_fields(data)
                files_with_deprecated += 1 if deprecated_errors else 0
                all_errors += deprecated_errors
                all_errors += check_canonical_path(data, fpath)
                legacy_errors = check_legacy_blockquote_metadata(fpath)
                files_with_legacy_blocks += 1 if legacy_errors else 0
                all_errors += legacy_errors

            if all_errors:
                files_with_errors += 1
                rel = os.path.relpath(fpath, root)
                print(f"\nERROR in {rel}:")
                for e in all_errors:
                    print(f"  - {e}")
            elif verbose:
                rel = os.path.relpath(fpath, root)
                print(f"  OK  {rel}")

    return files_checked, files_with_errors, files_with_deprecated, files_with_verification, files_with_legacy_blocks


def main():
    parser = argparse.ArgumentParser(description="Validate YAML operative front matter")
    parser.add_argument("--dir", default="skill/references",
                        help="Directory to scan (default: skill/references)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print OK lines")
    args = parser.parse_args()

    root = args.dir
    if not os.path.isdir(root):
        print(f"ERROR: directory '{root}' not found. Run from repo root.")
        sys.exit(1)

    print(f"Scanning: {root}")
    checked, errors, deprecated, verification, legacy_blocks = scan_dir(root, args.verbose)

    print(f"\n{'─'*60}")
    print(f"Files checked:              {checked}")
    print(f"Files with errors:          {errors}")
    print(f"Files with deprecated keys: {deprecated}")
    print(f"Files with verification:    {verification}")
    print(f"Files with legacy blocks:   {legacy_blocks}")
    print(f"{'─'*60}")

    if errors:
        print("RESULT: FAIL — fix errors above before operator pack compilation")
        sys.exit(1)
    else:
        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
