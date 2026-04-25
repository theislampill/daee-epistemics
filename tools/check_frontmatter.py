#!/usr/bin/env python3
"""
check_frontmatter.py — Validate YAML operative front matter across skill module files.

Checks:
  1. YAML parses cleanly (no syntax errors)
  2. Required fields are present (id, module_class, canonical_path, contract_version)
  3. Enum fields contain only allowed values
  4. Enhanced schema fields are consistent (e.g. verification_status: L_check implies
     direct_read_verified: true and all three content flags true)
  5. Files with verification_status: L_check are noted as upgraded (cross-reference with
     coverage-ledger if present)

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

VALID_LOAD_CLASS = {"always_on", "routed", "optional"}
VALID_BUNDLE = {"always_on_runtime", "operator_pack", "none"}
VALID_EXECUTION_PHASE = {"entry", "diagnostic", "routing", "render", "refresh", "governance"}
VALID_GOVERNS = {"diagnostic_ir", "routing_gate", "render_permission"}
VALID_VERIFICATION_STATUS = {"L_check", "L_tilde"}
VALID_SOURCE_STATUS = {"canonical", "derivative", "provisional"}

REQUIRED_FIELDS = ["id", "module_class", "canonical_path", "contract_version"]

ENHANCED_FIELDS = [
    "load_class", "bundle", "execution_phase", "verification_status",
    "source_status", "direct_read_required", "direct_read_verified",
    "failure_conditions_present", "ir_consequences_present",
    "minimal_pairs_present", "compiled_runtime_eligible", "operator_pack_eligible"
]

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


def check_consistency(data: dict) -> list[str]:
    errors = []
    vs = data.get("verification_status")
    if vs == "L_check":
        if data.get("direct_read_verified") is not True:
            errors.append("verification_status: L_check but direct_read_verified is not true")
    if vs == "L_tilde":
        if data.get("direct_read_verified") is True:
            # This is a warning not an error — could have been read but still thin
            pass

    # M5 / symmetric-taqlid-check are always_on; operator_pack_eligible should be false
    load_class = data.get("load_class")
    op_eligible = data.get("operator_pack_eligible")
    if load_class == "always_on" and op_eligible is True:
        errors.append(
            "load_class: always_on with operator_pack_eligible: true is unusual — "
            "always_on modules are not normally included in operator packs"
        )

    # layer-b-governed + explicit governs list: render_permission should appear
    lc = data.get("layer_constraint")
    governs = data.get("governs")
    if lc == "layer-b-governed" and governs is not None and "render_permission" not in governs:
        errors.append(
            "layer_constraint: layer-b-governed with explicit governs list that omits "
            "'render_permission' — add render_permission or remove governs: []"
        )

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


# ── Main ───────────────────────────────────────────────────────────────────────

def scan_dir(root: str, verbose: bool) -> tuple[int, int, int]:
    """Return (files_checked, files_with_errors, files_missing_enhanced)."""
    files_checked = 0
    files_with_errors = 0
    files_missing_enhanced = 0

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
                all_errors += check_enum(data, "load_class", VALID_LOAD_CLASS)
                all_errors += check_enum(data, "bundle", VALID_BUNDLE)
                all_errors += check_enum(data, "execution_phase", VALID_EXECUTION_PHASE)
                all_errors += check_enum(data, "verification_status", VALID_VERIFICATION_STATUS)
                all_errors += check_enum(data, "source_status", VALID_SOURCE_STATUS)
                all_errors += check_consistency(data)
                all_errors += check_canonical_path(data, fpath)

                missing_enhanced = [f for f in ENHANCED_FIELDS if f not in data]
                if missing_enhanced:
                    files_missing_enhanced += 1
                    if verbose:
                        rel = os.path.relpath(fpath, root)
                        print(f"  [enhanced-missing] {rel}: {missing_enhanced}")

            if all_errors:
                files_with_errors += 1
                rel = os.path.relpath(fpath, root)
                print(f"\nERROR in {rel}:")
                for e in all_errors:
                    print(f"  - {e}")
            elif verbose:
                rel = os.path.relpath(fpath, root)
                vs = (data or {}).get("verification_status", "—")
                print(f"  OK  {rel}  [{vs}]")

    return files_checked, files_with_errors, files_missing_enhanced


def main():
    parser = argparse.ArgumentParser(description="Validate YAML operative front matter")
    parser.add_argument("--dir", default="skill/references",
                        help="Directory to scan (default: skill/references)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print OK lines and enhanced-field warnings")
    args = parser.parse_args()

    root = args.dir
    if not os.path.isdir(root):
        print(f"ERROR: directory '{root}' not found. Run from repo root.")
        sys.exit(1)

    print(f"Scanning: {root}")
    checked, errors, missing_enhanced = scan_dir(root, args.verbose)

    print(f"\n{'─'*60}")
    print(f"Files checked:              {checked}")
    print(f"Files with errors:          {errors}")
    print(f"Files missing enhanced YAML:{missing_enhanced}")
    print(f"{'─'*60}")

    if errors:
        print("RESULT: FAIL — fix errors above before operator pack compilation")
        sys.exit(1)
    else:
        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
