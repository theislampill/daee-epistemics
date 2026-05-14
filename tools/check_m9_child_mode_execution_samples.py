#!/usr/bin/env python3
"""Validate local Stage-1.5 M9 child-mode execution samples.

This checker is intentionally dev/local. It does not validate package-bound
smoke provenance and it does not replace tools/check_smoke_artifacts.py. Its
job is narrower: reject retained local M9 samples that only name child modes or
only include Target/Operation/Result headings without child-specific pressure.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / ".daee" / "stage1.5-m9-child-live-smokes-20260514"

BANNED_LEAKAGE = (
    re.compile(r"\bowner-floor applied\b", re.IGNORECASE),
    re.compile(r"\bvalidation passed\b", re.IGNORECASE),
    re.compile(r"\bexecute queued owner\b", re.IGNORECASE),
    re.compile(r"\broute_plan\b", re.IGNORECASE),
    re.compile(r"\bfeatures\.json\b", re.IGNORECASE),
    re.compile(r"\bcheck_execution\b", re.IGNORECASE),
    re.compile(r"\bI applied M9\b", re.IGNORECASE),
)

GENERIC_OPERATION_START = re.compile(
    r"^\s*(?:address|discuss|engage|consider|talk about|respond to|deal with)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SampleSpec:
    directory: str
    child_mode: str
    prompt_needles: tuple[str, ...]
    target_patterns: tuple[re.Pattern[str], ...]
    operation_start: re.Pattern[str]
    operation_patterns: tuple[re.Pattern[str], ...]
    result_patterns: tuple[re.Pattern[str], ...]
    land_patterns: tuple[re.Pattern[str], ...]
    reread_patterns: tuple[re.Pattern[str], ...]
    downstream_patterns: tuple[re.Pattern[str], ...]


def pat(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)


SPECS = (
    SampleSpec(
        directory="A-M9-SR-semantic-reception",
        child_mode="M9-SR",
        prompt_needles=("first audience", "later technical theory", "reassigned"),
        target_patterns=(
            pat(r"reception bridge"),
            pat(r"wording.*usage.*context.*first audience"),
            pat(r"later technical theory.*reassign"),
        ),
        operation_start=pat(r"^\s*audit\b"),
        operation_patterns=(
            pat(r"speaker intent"),
            pat(r"usage"),
            pat(r"context"),
            pat(r"direct-audience availability"),
            pat(r"semantic override"),
        ),
        result_patterns=(
            pat(r"later reinterpretation is held"),
            pat(r"cannot govern.*reception-grounded access"),
            pat(r"changes the semantic state"),
        ),
        land_patterns=(
            pat(r"semantic hold"),
            pat(r"does not automatically outrank.*first audience"),
            pat(r"missing discriminator.*wording.*usage.*context.*direct-audience"),
        ),
        reread_patterns=(
            pat(r"M9-SR remains active"),
            pat(r"V8 is held"),
            pat(r"Do-attribute remains held"),
            pat(r"collapse-radius"),
        ),
        downstream_patterns=(pat(r"Release V8 only after meaning is received"),),
    ),
    SampleSpec(
        directory="B-M9-ZM-zahir-majaz",
        child_mode="M9-ZM",
        prompt_needles=("figurative", "speech situation", "received apparent meaning"),
        target_patterns=(
            pat(r"verdict-label"),
            pat(r"figurative"),
            pat(r"received apparent meaning"),
        ),
        operation_start=pat(r"^\s*split\b"),
        operation_patterns=(
            pat(r"received apparent sense"),
            pat(r"figurative usage claim"),
            pat(r"claimed reality/literal truth"),
            pat(r"which one carries the inference"),
        ),
        result_patterns=(
            pat(r"label no longer decides"),
            pat(r"claim inside the case"),
            pat(r"denies label-as-verdict"),
        ),
        land_patterns=(
            pat(r"semantic function of the label"),
            pat(r"Figurative.*not sufficient"),
            pat(r"Missing discriminator.*usage.*context.*first-audience"),
        ),
        reread_patterns=(
            pat(r"M9-ZM remains active"),
            pat(r"V8 stays held"),
            pat(r"collapse-radius"),
        ),
        downstream_patterns=(
            pat(r"Release V8 if a stable meaning is identified"),
            pat(r"Keep M9 active"),
        ),
    ),
    SampleSpec(
        directory="C-M9-MQ-modality-quarantine",
        child_mode="M9-MQ",
        prompt_needles=("movement through locations", "only mode"),
        target_patterns=(
            pat(r"creaturely modality entailment"),
            pat(r"movement through created locations"),
            pat(r"no other mode"),
        ),
        operation_start=pat(r"^\s*split\b"),
        operation_patterns=(
            pat(r"semantic core"),
            pat(r"imagined modality"),
            pat(r"asserted entailment"),
            pat(r"refusing unsupported modality transfer"),
        ),
        result_patterns=(
            pat(r"Meaning can remain affirmed"),
            pat(r"likeness is denied"),
            pat(r"modality is withheld"),
            pat(r"show the entailment"),
        ),
        land_patterns=(
            pat(r"asserted entailment"),
            pat(r"Creaturely imagination is not an entailment engine"),
            pat(r"Missing discriminator.*semantic core.*movement through created locations"),
        ),
        reread_patterns=(
            pat(r"M9-MQ clears"),
            pat(r"V8 becomes eligible"),
            pat(r"collapse-radius"),
        ),
        downstream_patterns=(
            pat(r"Release V8.*modality has been quarantined"),
            pat(r"Hold do-attribute"),
        ),
    ),
    SampleSpec(
        directory="D-M9-LD-loaded-label-deflation",
        child_mode="M9-LD",
        prompt_needles=("body", "above-ness", "body-like composition"),
        target_patterns=(
            pat(r"loaded label"),
            pat(r"body"),
            pat(r"hidden ontology"),
            pat(r"real above-ness or action"),
        ),
        operation_start=pat(r"^\s*disambiguate\b"),
        operation_patterns=(
            pat(r"intended sense"),
            pat(r"true rejected meaning"),
            pat(r"smuggled technical negation"),
            pat(r"refuse jurisdiction"),
        ),
        result_patterns=(
            pat(r"label stops functioning as a silent tribunal"),
            pat(r"prove that real above-ness or real action entails created composition"),
            pat(r"refusing the yes/no trap"),
        ),
        land_patterns=(
            pat(r"semantic and ontological split"),
            pat(r"created-composite sense.*rejected"),
            pat(r"unresolved label is refused"),
            pat(r"Missing discriminator.*real above-ness or real action entails body-like composition"),
        ),
        reread_patterns=(
            pat(r"M9-LD remains active"),
            pat(r"V8 remains held"),
            pat(r"Do-attribute remains held"),
            pat(r"collapse-radius"),
        ),
        downstream_patterns=(
            pat(r"Release V8"),
            pat(r"Release do-attribute"),
            pat(r"Keep M9-LD active"),
        ),
    ),
)
SPEC_BY_MODE = {spec.child_mode: spec for spec in SPECS}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def section(text: str, start: str, stops: tuple[str, ...]) -> str:
    start_match = re.search(rf"(?im)^\s*{re.escape(start)}\s*$", text)
    if not start_match:
        return ""
    tail = text[start_match.end() :]
    stop_positions: list[int] = []
    for stop in stops:
        stop_match = re.search(rf"(?im)^\s*{re.escape(stop)}\s*$", tail)
        if stop_match:
            stop_positions.append(stop_match.start())
    if stop_positions:
        tail = tail[: min(stop_positions)]
    return tail.strip()


def first_content_line(block: str) -> str:
    for line in block.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def require_patterns(
    errors: list[str],
    label: str,
    block: str,
    patterns: tuple[re.Pattern[str], ...],
) -> None:
    for pattern in patterns:
        if not pattern.search(block):
            errors.append(f"{label} missing pattern: {pattern.pattern}")


def infer_spec(sample_root: Path, input_text: str, output_text: str, verdict_text: str) -> tuple[SampleSpec | None, list[str]]:
    haystack = "\n".join((sample_root.name, input_text, output_text, verdict_text)).lower()
    matches = [spec for spec in SPECS if spec.child_mode.lower() in haystack]
    if not matches:
        return None, ["could not infer M9 child mode from directory/input/output/verdict"]
    if len(matches) > 1:
        matched = ", ".join(spec.child_mode for spec in matches)
        return None, [f"ambiguous child mode references: {matched}"]
    return matches[0], []


def validate_sample_dir(sample_root: Path) -> list[str]:
    input_text = read(sample_root / "input.md")
    output_text = read(sample_root / "output.md")
    trace_text = read(sample_root / "trace.md")
    verdict_text = read(sample_root / "verdict.md")
    errors: list[str] = []

    if not input_text:
        errors.append("missing input.md")
    if not output_text:
        errors.append("missing output.md")
    if not trace_text:
        errors.append("missing trace.md")
    if not verdict_text:
        errors.append("missing verdict.md")
    if errors:
        return errors

    spec, spec_errors = infer_spec(sample_root, input_text, output_text, verdict_text)
    if spec is None:
        return spec_errors

    for needle in spec.prompt_needles:
        if needle.lower() not in input_text.lower():
            errors.append(f"prompt missing expected label-stripped pressure: {needle}")

    if spec.child_mode.lower() not in output_text.lower():
        errors.append(f"output missing child-mode anchor: {spec.child_mode}")
    if "school" in output_text.lower() and "does not" not in output_text.lower():
        errors.append("output appears to depend on a school label")

    for pattern in BANNED_LEAKAGE:
        if pattern.search(output_text):
            errors.append(f"route/check harness leakage: {pattern.pattern}")

    target = section(output_text, "Target:", ("Operation:", "Result:", "## Land(B)", "## R(H,Delta)"))
    operation = section(output_text, "Operation:", ("Result:", "## Land(B)", "## R(H,Delta)"))
    result = section(output_text, "Result:", ("## Land(B)", "## R(H,Delta)"))
    land = section(output_text, "## Land(B)", ("## R(H,Delta)", "## Non-Execution Traps Avoided"))
    reread = section(output_text, "## R(H,Delta)", ("## Non-Execution Traps Avoided", "## Final Answer Shape"))

    blocks = {
        "target": target,
        "operation": operation,
        "result": result,
        "Land(B)": land,
        "R(H,Delta)": reread,
    }
    minimum_lengths = {
        "target": 100,
        "operation": 250,
        "result": 150,
        "Land(B)": 300,
        "R(H,Delta)": 300,
    }
    for name, block in blocks.items():
        if not block:
            errors.append(f"missing {name} block")
        elif len(block) < minimum_lengths[name]:
            errors.append(f"{name} block too short for semantic review: {len(block)}")

    operation_first_line = first_content_line(operation)
    if operation_first_line and GENERIC_OPERATION_START.search(operation_first_line):
        errors.append(f"operation starts with generic verb: {operation_first_line}")
    if operation_first_line and not spec.operation_start.search(operation_first_line):
        errors.append(
            f"operation does not start with expected child verb "
            f"({spec.operation_start.pattern}): {operation_first_line}"
        )

    require_patterns(errors, "target", target, spec.target_patterns)
    require_patterns(errors, "operation", operation, spec.operation_patterns)
    require_patterns(errors, "result", result, spec.result_patterns)
    require_patterns(errors, "Land(B)", land, spec.land_patterns)
    require_patterns(errors, "R(H,Delta)", reread, spec.reread_patterns)
    require_patterns(errors, "downstream route handling", reread, spec.downstream_patterns)

    anti_label_guard = (
        "not merely print" in output_text.lower()
        or "magic label" in output_text.lower()
        or "does not count" in output_text.lower()
    )
    if "label" in output_text.lower() and not anti_label_guard:
        errors.append("label language present without explicit anti-label-only execution guard")
    if "held" not in land.lower() and "release" not in reread.lower():
        errors.append("no visible hold/release state change")
    if "collapse-radius" not in reread.lower():
        errors.append("R(H,Delta) lacks collapse-radius/kappa update")

    if "- status: PASS" not in verdict_text:
        errors.append("verdict.md does not record PASS")
    if f"- child mode: {spec.child_mode}" not in verdict_text:
        errors.append("verdict.md child mode mismatch")
    if "package/release evidence: no" not in trace_text.lower():
        errors.append("trace.md must preserve non-package evidence boundary")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Root containing the four Stage-1.5 M9 child-mode smoke directories.",
    )
    args = parser.parse_args(argv)
    root = args.root if args.root.is_absolute() else (ROOT / args.root)

    if not root.exists():
        print(f"M9 child-mode execution sample validation: FAIL")
        print(f"- root does not exist: {root}")
        return 1

    sample_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not sample_dirs:
        print("M9 child-mode execution sample validation: FAIL")
        print(f"- no sample directories under: {root}")
        return 1

    all_errors: dict[str, list[str]] = {}
    checked_modes: list[str] = []
    for sample_dir in sample_dirs:
        sample_text = "\n".join(
            (
                sample_dir.name,
                read(sample_dir / "input.md"),
                read(sample_dir / "output.md"),
                read(sample_dir / "verdict.md"),
            )
        ).lower()
        for spec in SPECS:
            if spec.child_mode.lower() in sample_text:
                checked_modes.append(spec.child_mode)
                break
        errors = validate_sample_dir(sample_dir)
        if errors:
            all_errors[sample_dir.name] = errors

    if all_errors:
        print("M9 child-mode execution sample validation: FAIL")
        for directory, errors in all_errors.items():
            for error in errors:
                print(f"- {directory}: {error}")
        return 1

    print("M9 child-mode execution sample validation: PASS")
    print(f"- root: {root}")
    print(f"- samples checked: {len(sample_dirs)}")
    print(f"- checked modes: {', '.join(sorted(set(checked_modes)))}")
    print("- evidence boundary: local ignored samples; not package/release smoke proof")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
