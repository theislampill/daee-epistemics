#!/usr/bin/env python3
"""Cheap malformed-ACT / ledger surface scanner for fresh smoke outputs.

This is a fast pre-validator only. Passing it does not prove owner activation,
body dereference, witness agreement, or Brandolini sufficiency.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from dataclasses import dataclass
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class SurfaceError:
    path: Path
    line: int
    code: str
    message: str
    snippet: str


TOKEN_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("delta-act", "malformed ACT prefix `ΔACT`", re.compile(r"ΔACT")),
    ("pi-uppercase", "malformed ACT field marker `Π=`; use lowercase `π=`", re.compile(r"Π=")),
    ("tau-uppercase", "malformed ACT field marker `Τ=`", re.compile(r"Τ=")),
    ("sigma-uppercase", "malformed ACT field marker `Σ=`", re.compile(r"Σ=")),
    ("lambda-uppercase", "malformed ACT field marker `Λ=`", re.compile(r"Λ=")),
    ("xi-uppercase", "malformed ACT field marker `Ξ=`", re.compile(r"Ξ=")),
    ("tau-pressure", "malformed pressure substitute `τ=`; use `π=`", re.compile(r"τ=")),
    ("pressure-field", "malformed pressure field `pressure=`; use `π=`", re.compile(r"\bpressure\s*=")),
    ("target-field", "malformed pressure field `target=`; use `π=`", re.compile(r"\btarget\s*=")),
    ("delta-field", "malformed delta field `delta=`; use `Δ=`", re.compile(r"\bdelta\s*=")),
    ("ascii-delta-b", "malformed ASCII delta `DeltaB`; use `ΔⁿB`", re.compile(r"DeltaB")),
    ("ascii-delta-k", "malformed ASCII delta `DeltaK`; use `Δκ`", re.compile(r"DeltaK")),
)

LAND_SUFFIX_RE = re.compile(r"Land\([^)]*\)\+\s*(?:MRP\b|R\b|✓|Δ)")
VISIBLE_LEDGER_PLUS_RE = re.compile(
    r"(?:𝔅_total(?:\s*\(B_total\))?|B_total)\s*=\s*"
    r"(?:𝔅_LA|B_LA)\s*\+\s*(?:𝔅_MRP|B_MRP)"
)
ASCII_ACT_REF_RE = re.compile(r"\bB\d+_\d+\b")
BARE_ACT_RE = re.compile(r"^\s*(?:[-*]\s*)?ACT\s+\S.*::")
ACT_HEADING_RE = re.compile(r"^\s*(?:#+\s*)?ACT records\s*:\s*$", re.IGNORECASE)


def expand_paths(raw_paths: list[str]) -> tuple[list[Path], list[str]]:
    paths: list[Path] = []
    errors: list[str] = []
    for raw in raw_paths:
        matches = glob.glob(raw)
        if not matches:
            path = Path(raw)
            if path.exists():
                matches = [raw]
            else:
                errors.append(f"no such output: {raw}")
                continue
        for match in matches:
            path = Path(match)
            if path.is_file():
                paths.append(path)
            else:
                errors.append(f"not a file: {match}")
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(path)
    return deduped, errors


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def line_at(text: str, lineno: int) -> str:
    lines = text.splitlines()
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()
    return ""


def add_match_errors(
    errors: list[SurfaceError],
    path: Path,
    text: str,
    code: str,
    message: str,
    pattern: re.Pattern[str],
) -> None:
    for match in pattern.finditer(text):
        lineno = line_number(text, match.start())
        errors.append(SurfaceError(path, lineno, code, message, line_at(text, lineno)))


def check_text(path: Path, text: str) -> list[SurfaceError]:
    errors: list[SurfaceError] = []
    for code, message, pattern in TOKEN_PATTERNS:
        add_match_errors(errors, path, text, code, message, pattern)

    add_match_errors(
        errors,
        path,
        text,
        "bad-land-suffix",
        "malformed Land suffix; ACT records end with `Land(ⁿB)+⟧` only",
        LAND_SUFFIX_RE,
    )
    add_match_errors(
        errors,
        path,
        text,
        "visible-ledger-plus",
        "visible burden ledger uses `+`; public proof must use `𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP`",
        VISIBLE_LEDGER_PLUS_RE,
    )

    for lineno, line in enumerate(text.splitlines(), start=1):
        if "ACT" not in line:
            continue
        stripped = line.strip()
        if ACT_HEADING_RE.match(stripped):
            continue
        if "⟦ACT" in line and "⟧" not in line:
            errors.append(
                SurfaceError(
                    path,
                    lineno,
                    "missing-act-close",
                    "ACT record has opening `⟦ACT` but no closing `⟧` on the same line",
                    stripped,
                )
            )
        if "⟦ACT" in line and ASCII_ACT_REF_RE.search(line):
            errors.append(
                SurfaceError(
                    path,
                    lineno,
                    "ascii-act-burden-ref",
                    "ACT record uses ASCII burden/submove ref such as `B1_1`; use canonical `¹B₁` form",
                    stripped,
                )
            )
        if "⟦ACT" not in line and BARE_ACT_RE.search(line):
            errors.append(
                SurfaceError(
                    path,
                    lineno,
                    "bare-act",
                    "bare `ACT` line is not inside `⟦ACT ... ⟧`",
                    stripped,
                )
            )
    return errors


def run_self_test() -> int:
    valid = "ACT records:\n⟦ACT ¹B₁[M9.repair] :: π=predicate-transfer :: body_ref=¹B₁ :: Δ=Δ¹B:blocked transfer :: Land(¹B)+⟧\n𝔅_total (B_total) = 𝔅_LA ∪ 𝔅_MRP\n"
    invalid_examples = {
        "delta-act": "ΔACT ¹B₁[M9.repair] :: π=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+⟧",
        "bare-act": "ACT ¹B₁[M9.repair] :: π=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+⟧",
        "pi-uppercase": "⟦ACT ¹B₁[M9.repair] :: Π=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+⟧",
        "tau-uppercase": "⟦ACT ¹B₁[M9.repair] :: Τ=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+⟧",
        "sigma-uppercase": "⟦ACT ¹B₁[M9.repair] :: Σ=Δ¹B:blocked :: body_ref=¹B₁ :: Land(¹B)+⟧",
        "lambda-uppercase": "⟦ACT ¹B₁[M9.repair] :: Λ=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+⟧",
        "xi-uppercase": "⟦ACT ¹B₁[M9.repair] :: Ξ=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+⟧",
        "tau-pressure": "⟦ACT ¹B₁[M9.repair] :: τ=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+⟧",
        "bad-land-check": "⟦ACT ¹B₁[M9.repair] :: π=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+✓⟧",
        "bad-land-r": "⟦ACT ¹B₁[M9.repair] :: π=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+R⟧",
        "bad-land-delta": "⟦ACT ¹B₁[M9.repair] :: π=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+Δ⟧",
        "bad-land-mrp": "⟦ACT ¹B₁[M9.repair] :: π=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+MRP⟧",
        "ascii-delta-b": "⟦ACT ¹B₁[M9.repair] :: π=x :: body_ref=¹B₁ :: Δ=DeltaB:blocked :: Land(¹B)+⟧",
        "ascii-act-ref": "⟦ACT B1_1[M9.repair] :: π=x :: body_ref=B1_1 :: Δ=Δ¹B:blocked :: Land(¹B)+⟧",
        "missing-close": "⟦ACT ¹B₁[M9.repair] :: π=x :: body_ref=¹B₁ :: Δ=Δ¹B:blocked :: Land(¹B)+",
        "visible-ledger-plus": "𝔅_total = 𝔅_LA + 𝔅_MRP",
    }
    valid_errors = check_text(Path("<valid-self-test>"), valid)
    if valid_errors:
        for error in valid_errors:
            print(format_error(error))
        print("act surface syntax self-test: FAIL (valid canary rejected)")
        return 1
    missed = []
    for code, text in invalid_examples.items():
        errors = check_text(Path(f"<invalid-{code}>"), text)
        if not errors:
            missed.append(code)
    if missed:
        print(f"act surface syntax self-test: FAIL (missed invalid canaries: {', '.join(missed)})")
        return 1
    print(f"act surface syntax self-test: PASS ({len(invalid_examples)} invalid canaries rejected)")
    return 0


def format_error(error: SurfaceError) -> str:
    return f"{error.path}:{error.line}: {error.code}: {error.message}: {error.snippet}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", nargs="+", help="Smoke output Markdown files to scan.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in positive/negative canaries.")
    args = parser.parse_args(argv)

    status = 0
    if args.self_test:
        status = run_self_test()
        if status != 0:
            return status

    if not args.outputs:
        if args.self_test:
            return 0
        parser.error("--outputs is required unless --self-test is used")

    paths, path_errors = expand_paths(args.outputs)
    errors: list[SurfaceError] = []
    for message in path_errors:
        print(f"ERROR: {message}")
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"ERROR: cannot read {path}: {exc}")
            status = 1
            continue
        errors.extend(check_text(path, text))

    for error in errors:
        print(format_error(error))

    if path_errors or errors:
        print(
            "act surface syntax check: FAIL "
            f"({len(paths)} outputs checked, {len(errors)} malformed surface findings)"
        )
        return 1
    print(f"act surface syntax check: PASS ({len(paths)} outputs checked)")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
