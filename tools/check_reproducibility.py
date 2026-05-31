#!/usr/bin/env python3
"""Check A.12 normalized-activation-record reproducibility.

This harness compares structural execution records, not prose. It requires
field_witness.normalized_activation_record and validates each output through
the field_witness convergence checker before comparing runs.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from closure_witness_lib import (
    BURDEN_ID_RE,
    extract_embedded_field_witness,
    extract_field_witness,
    normalize_burden_id,
)
from check_field_witness_convergence import convergence_errors


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "reproducibility"
ACADEMIC_SOURCE_ORDER_N_FRAME = "mixed-academic-source-order-shubhah"
ACADEMIC_SOURCE_ORDER_N_FRAME_ALIASES = {
    ACADEMIC_SOURCE_ORDER_N_FRAME,
    "mixed-academic-public-knowledge-shubhah",
    "mixed-academic-respectability-shubhah",
    "mixed-academic-secular-identity-shubhah",
}

REGISTER_ALIASES = {
    "omega": "Omega",
    "Ω": "Omega",
    "xi": "xi",
    "ξ": "xi",
    "mu": "mu",
    "μ": "mu",
    "kappa": "kappa",
    "κ": "kappa",
    "heart": "heart",
    "♥": "heart",
}


@dataclass(frozen=True)
class NarReport:
    path: Path
    record: dict[str, Any] | None
    fingerprint: str
    errors: list[str]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


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


def canon_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def canonical_register(value: Any) -> str:
    text = str(value or "").strip()
    return REGISTER_ALIASES.get(text, REGISTER_ALIASES.get(text.lower(), text))


def list_values(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,;/|]+", value) if part.strip()]
    return []


def int_value(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        return int(value.strip())
    return None


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def canonical_burden(value: Any) -> str:
    burden = normalize_burden_id(str(value or ""))
    return burden if BURDEN_ID_RE.fullmatch(burden) else str(value or "").strip()


def canonical_nar(raw: dict[str, Any]) -> dict[str, Any]:
    per_burden: list[dict[str, Any]] = []
    for item in raw.get("per_burden") or []:
        if not isinstance(item, dict):
            continue
        burden = canonical_burden(item.get("burden_id") or item.get("id") or item.get("burden"))
        per_burden.append(
            {
                "burden_id": burden,
                "owner_id": str(item.get("owner_id") or item.get("owner") or "").strip().upper(),
                "operation": canon_text(item.get("operation") or item.get("operation_family")),
                "delta_result": canon_text(item.get("delta_result")),
                "mrp_route_result_type": str(item.get("mrp_route_result_type") or item.get("route_result_type") or "").strip(),
                "terminal_state": str(item.get("terminal_state") or "").strip(),
                "generation_depth": int_value(item.get("generation_depth")),
            }
        )
    per_burden.sort(key=lambda row: row["burden_id"])
    live_registers = sorted(
        {
            register
            for value in list_values(raw.get("live_registers"))
            if (register := canonical_register(value))
        }
    )
    burden_floor = [
        burden
        for value in list_values(raw.get("burden_floor"))
        if (burden := canonical_burden(value))
    ]
    return {
        "n_frame": canon_text(raw.get("n_frame")),
        "live_registers": live_registers,
        "burden_floor": burden_floor,
        "per_burden": per_burden,
    }


def nar_record_errors(path: Path, record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    n_frame = str(record.get("n_frame") or "")
    if n_frame in ACADEMIC_SOURCE_ORDER_N_FRAME_ALIASES and n_frame != ACADEMIC_SOURCE_ORDER_N_FRAME:
        errors.append(
            f"{rel(path)}: n_frame {n_frame!r} is an academic source-order alias; "
            f"use {ACADEMIC_SOURCE_ORDER_N_FRAME!r}"
        )

    for index, row in enumerate(record.get("per_burden") or [], start=1):
        if not isinstance(row, dict):
            continue
        owner = str(row.get("owner_id") or "").upper()
        if (
            row.get("burden_id") == "B5"
            and owner in {"SOURCE", "SOURCE-STATUS-REPAIR", "AUTHORITY-ORDER-REPAIR"}
            and row.get("operation") == "source-order"
            and row.get("generation_depth") == 1
            and row.get("delta_result") != "hidden-support-blocked"
        ):
            errors.append(
                f"{rel(path)}: normalized_activation_record.per_burden[{index}] "
                "uses source-order recoil B5; delta_result must be 'hidden-support-blocked'"
            )
    return errors


def parse_report(path: Path) -> NarReport:
    if not path.exists():
        return NarReport(path, None, "", [f"{rel(path)}: output path not found"])
    text = read_text(path)
    errors = convergence_errors(path, text)
    payload = extract_embedded_field_witness(text)
    field_witness = extract_field_witness(payload) if payload is not None else None
    if field_witness is None:
        return NarReport(path, None, "", errors + [f"{rel(path)}: field_witness object missing"])
    raw = field_witness.get("normalized_activation_record")
    if raw is None:
        return NarReport(path, None, "", errors + [f"{rel(path)}: field_witness.normalized_activation_record missing"])
    if not isinstance(raw, dict):
        return NarReport(path, None, "", errors + [f"{rel(path)}: field_witness.normalized_activation_record must be an object"])
    record = canonical_nar(raw)
    errors.extend(nar_record_errors(path, record))
    return NarReport(path, record, digest(record), errors)


def field_diffs(left: Any, right: Any, path: str = "$") -> list[dict[str, Any]]:
    if type(left) is not type(right):
        return [{"path": path, "left": left, "right": right}]
    if isinstance(left, dict):
        diffs: list[dict[str, Any]] = []
        for key in sorted(set(left) | set(right)):
            child_path = f"{path}.{key}"
            if key not in left:
                diffs.append({"path": child_path, "left": None, "right": right[key]})
            elif key not in right:
                diffs.append({"path": child_path, "left": left[key], "right": None})
            else:
                diffs.extend(field_diffs(left[key], right[key], child_path))
        return diffs
    if isinstance(left, list):
        diffs = []
        for index in range(max(len(left), len(right))):
            child_path = f"{path}[{index}]"
            if index >= len(left):
                diffs.append({"path": child_path, "left": None, "right": right[index]})
            elif index >= len(right):
                diffs.append({"path": child_path, "left": left[index], "right": None})
            else:
                diffs.extend(field_diffs(left[index], right[index], child_path))
        return diffs
    if left != right:
        return [{"path": path, "left": left, "right": right}]
    return []


def comparison_report(paths: list[Path]) -> dict[str, Any]:
    reports = [parse_report(path) for path in paths]
    errors = [error for report in reports for error in report.errors]
    if len(reports) < 3:
        errors.append("reproducibility comparison requires at least three outputs")

    pairs: list[dict[str, Any]] = []
    diffs: list[dict[str, Any]] = []
    for left_index in range(len(reports)):
        for right_index in range(left_index + 1, len(reports)):
            left = reports[left_index]
            right = reports[right_index]
            pair = {
                "left": rel(left.path),
                "right": rel(right.path),
                "left_fingerprint": left.fingerprint[:12],
                "right_fingerprint": right.fingerprint[:12],
                "isomorphic": bool(left.record is not None and right.record is not None and left.fingerprint == right.fingerprint),
            }
            pairs.append(pair)
            if left.record is not None and right.record is not None and left.fingerprint != right.fingerprint:
                for diff in field_diffs(left.record, right.record):
                    diffs.append({"left": rel(left.path), "right": rel(right.path), **diff})

    return {
        "isomorphic": not errors and bool(pairs) and all(pair["isomorphic"] for pair in pairs),
        "pairs": pairs,
        "field_diffs": diffs,
        "errors": errors,
    }


def group_dirs(root: Path, kind: str) -> list[Path]:
    base = root / kind
    if not base.exists():
        return []
    return sorted(path for path in base.iterdir() if path.is_dir())


def direct_fixtures(root: Path, kind: str) -> list[Path]:
    base = root / kind
    if not base.exists():
        return []
    return sorted(base.glob("*.md"))


def run_fixture_suite(root: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    if not root.exists():
        return errors, valid_checked, invalid_checked

    for path in direct_fixtures(root, "valid"):
        report = parse_report(path)
        if report.errors:
            errors.extend(report.errors)
        else:
            valid_checked += 1

    for path in direct_fixtures(root, "invalid"):
        report = parse_report(path)
        if report.errors:
            invalid_checked += 1
        else:
            errors.append(f"{rel(path)}: expected-invalid reproducibility fixture unexpectedly passed")

    for directory in group_dirs(root, "valid"):
        paths = sorted(directory.glob("*.md"))
        report = comparison_report(paths)
        if report["isomorphic"]:
            valid_checked += 1
        else:
            errors.append(f"{rel(directory)}: expected-valid reproducibility group failed")
            errors.extend(f"{rel(directory)}: {error}" for error in report["errors"])
            for diff in report["field_diffs"]:
                errors.append(f"{rel(directory)}: NAR diff {diff['path']} between {diff['left']} and {diff['right']}")

    for directory in group_dirs(root, "invalid"):
        paths = sorted(directory.glob("*.md"))
        report = comparison_report(paths)
        if report["isomorphic"]:
            errors.append(f"{rel(directory)}: expected-invalid reproducibility group unexpectedly passed")
        else:
            invalid_checked += 1
    return errors, valid_checked, invalid_checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FIXTURE_ROOT)
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    parser.add_argument("--compare-runs", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0
    compare_payload: dict[str, Any] | None = None

    suite_errors, valid_checked, invalid_checked = run_fixture_suite(args.root)
    errors.extend(suite_errors)

    for path in expand_paths(args.outputs):
        report = parse_report(path)
        if report.errors:
            errors.extend(report.errors)
        else:
            output_checked += 1

    if args.compare_runs:
        compare_payload = comparison_report(expand_paths(args.compare_runs))
        if not compare_payload["isomorphic"]:
            errors.extend(compare_payload["errors"])
            for diff in compare_payload["field_diffs"]:
                errors.append(f"NAR diff {diff['path']} between {diff['left']} and {diff['right']}")

    if errors:
        print("reproducibility check: FAIL")
        for error in errors:
            print(f"- {error}")
        if compare_payload is not None:
            print(json.dumps(compare_payload, indent=2, sort_keys=True))
        return 1

    print("reproducibility check: PASS")
    print(f"Valid fixture groups checked: {valid_checked}")
    print(f"Invalid fixture groups checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    if compare_payload is not None:
        print(json.dumps(compare_payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
