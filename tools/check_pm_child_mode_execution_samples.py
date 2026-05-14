#!/usr/bin/env python3
"""Validate local Stage-2.5 proof-method child-mode execution samples.

This checker is intentionally dev/local. It validates retained ignored samples
under .daee; it is not package/release smoke proof, not a live runner, and not a
general semantic grader. Its narrow purpose is to reject PM samples that merely
name child modes or print Target/Operation/Result headings without executing the
child-specific proof-method pressure and the heart/M5/FPD guardrails.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / ".daee" / "stage2.5-pm-child-live-smokes-20260514"

BANNED_OUTPUT_LEAKAGE = (
    re.compile(r"\bowner-floor applied\b", re.IGNORECASE),
    re.compile(r"\bvalidation passed\b", re.IGNORECASE),
    re.compile(r"\bexecute queued owner\b", re.IGNORECASE),
    re.compile(r"\broute_plan\b", re.IGNORECASE),
    re.compile(r"\bfeatures\.json\b", re.IGNORECASE),
    re.compile(r"\bcheck_execution\b", re.IGNORECASE),
    re.compile(r"\bI applied PM\b", re.IGNORECASE),
)

GENERIC_OPERATION_START = re.compile(
    r"^\s*(?:address|discuss|engage|consider|respond to|deal with|explain the issue|analyze generally)\b",
    re.IGNORECASE,
)

ALLOWED_OPERATION_START = re.compile(
    r"^\s*(?:classify|audit|distinguish|reclassify|narrow|expose|clear|refuse jurisdiction of)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SampleSpec:
    child_mode: str
    prompt_needles: tuple[str, ...]
    target_patterns: tuple[re.Pattern[str], ...]
    operation_start: re.Pattern[str]
    operation_patterns: tuple[re.Pattern[str], ...]
    result_patterns: tuple[re.Pattern[str], ...]
    land_patterns: tuple[re.Pattern[str], ...]
    reread_patterns: tuple[re.Pattern[str], ...]
    downstream_patterns: tuple[re.Pattern[str], ...]
    heart_patterns: tuple[re.Pattern[str], ...]
    deformation_patterns: tuple[re.Pattern[str], ...]
    source_patterns: tuple[re.Pattern[str], ...]


def pat(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)


SPECS = (
    SampleSpec(
        child_mode="PM-1",
        prompt_needles=("rational proof", "temporal origination", "whole conclusion"),
        target_patterns=(
            pat(r"unclassified proof family"),
            pat(r"claim.*asked to carry"),
            pat(r"oversized claim"),
        ),
        operation_start=pat(r"^\s*classify\b"),
        operation_patterns=(
            pat(r"proof family"),
            pat(r"premise form"),
            pat(r"inference form"),
            pat(r"conclusion scope"),
        ),
        result_patterns=(
            pat(r"not.*over-credit"),
            pat(r"correct.*route.*selected|held classification state"),
            pat(r"proof.*family.*scope|family.*conclusion scope|proof family.*conclusion scope"),
        ),
        land_patterns=(
            pat(r"PM-1 lands.*proof-family ambiguity"),
            pat(r"family.*scope.*typed|missing discriminator"),
            pat(r"argument dumping|argument dump|downstream proof content|proof route"),
        ),
        reread_patterns=(
            pat(r"downstream routes.*held"),
            pat(r"huduth|causal-series"),
            pat(r"V2"),
            pat(r"FPD"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released:\s*PM-1 classification"),
            pat(r"Held:.*causal-series.*V2.*FPD"),
        ),
        heart_patterns=(
            pat(r"Heart/register consequence"),
            pat(r"released.*proof-method work|bounded"),
            pat(r"overcomplexity|wiswas|destabilized"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 deformation release condition"),
            pat(r"proof-method burden"),
            pat(r"zann|taqlid|inherited framework|hawa|gharad|ada"),
        ),
        source_patterns=(
            pat(r"FPD/source-worldview consequence"),
            pat(r"authority court|tribunal"),
            pat(r"FPD/V2"),
        ),
    ),
    SampleSpec(
        child_mode="PM-2",
        prompt_needles=("formal demonstration", "signs", "fitrah"),
        target_patterns=(
            pat(r"admissibility rule"),
            pat(r"Only formal demonstration counts"),
            pat(r"proof denominator|denominator|admissibility rule"),
        ),
        operation_start=pat(r"^\s*audit\b"),
        operation_patterns=(
            pat(r"what.*admits"),
            pat(r"what.*excludes"),
            pat(r"what.*assumes"),
        ),
        result_patterns=(
            pat(r"hidden proof standard becomes contestable"),
            pat(r"denominator.*no longer neutral"),
            pat(r"criterion"),
        ),
        land_patterns=(
            pat(r"PM-2 lands denominator narrowing"),
            pat(r"criterion exposure"),
            pat(r"signs.*testimony.*fitrah"),
        ),
        reread_patterns=(
            pat(r"signs/testimony/fitrah routes.*held"),
            pat(r"denominator no longer excludes"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released:.*PM-2.*FPD/V2"),
            pat(r"Held:.*signs.*testimony.*fitrah"),
        ),
        heart_patterns=(
            pat(r"Heart/register consequence"),
            pat(r"overcomplexity|wiswas|destabilized"),
            pat(r"do not feed proof-stacking|bounded"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 deformation release condition"),
            pat(r"shubhah|inherited framework|taqlid|zann|mushabara"),
            pat(r"deformation-stabilized filter|ordinary proof content remains held"),
        ),
        source_patterns=(
            pat(r"FPD/source-worldview consequence"),
            pat(r"formal demonstration.*only admissible warrant"),
            pat(r"imported tribunal|FPD/V2"),
        ),
    ),
    SampleSpec(
        child_mode="PM-4",
        prompt_needles=("Temporal origination", "contingency grammar", "possible-being"),
        target_patterns=(
            pat(r"huduth/preponderance route"),
            pat(r"modal contingency/mumkin route"),
            pat(r"proof route and burden scope|route scope"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"huduth/preponderance route"),
            pat(r"modal contingency route"),
            pat(r"audit what each establishes"),
        ),
        result_patterns=(
            pat(r"direct huduth burden is preserved"),
            pat(r"modal taxonomy is held"),
            pat(r"broader.*not automatically|cannot displace|prestige|broader or more philosophical|no longer moved"),
        ),
        land_patterns=(
            pat(r"PM-4 lands route-status clarity"),
            pat(r"broader modal grammar.*not automatically|cannot displace|prestige"),
            pat(r"modal-contingency elaboration.*held"),
        ),
        reread_patterns=(
            pat(r"modal contingency.*held"),
            pat(r"causal-series|huduth"),
            pat(r"necessity/contingency overreach"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released:.*PM-4.*causal-series/huduth"),
            pat(r"Held:.*modal contingency.*V2/FPD"),
        ),
        heart_patterns=(
            pat(r"Heart/register consequence"),
            pat(r"formalism-prestige|overcomplexity"),
            pat(r"hold speculative modal expansion|bounded"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 deformation release condition"),
            pat(r"inherited formalism|prestige attachment|zann-mode"),
            pat(r"genuine proof-method pressure"),
        ),
        source_patterns=(
            pat(r"FPD/source-worldview consequence"),
            pat(r"Aristotelian|Neoplatonic|modal grammar"),
            pat(r"tribunal.*FPD/V2|FPD/V2.*tribunal"),
        ),
    ),
    SampleSpec(
        child_mode="PM-6",
        prompt_needles=("reason itself", "God-talk", "transmitted wording"),
        target_patterns=(
            pat(r"local proof tool.*scope.*tribunal function"),
            pat(r"reason itself"),
            pat(r"transmitted wording"),
        ),
        operation_start=pat(r"^\s*audit\b"),
        operation_patterns=(
            pat(r"premise"),
            pat(r"inference"),
            pat(r"conclusion scope"),
            pat(r"tribunal status"),
        ),
        result_patterns=(
            pat(r"reclassified.*overreaching tribunal"),
            pat(r"local support|secondary route|invalid tribunal|demoted.*source-order judge|overreaching tribunal"),
            pat(r"source-order judge|silent court"),
        ),
        land_patterns=(
            pat(r"PM-6 lands proof-overreach"),
            pat(r"tribunal demotion|refusal"),
            pat(r"source-status|revelation"),
        ),
        reread_patterns=(
            pat(r"FPD/V2|FPD.*V2"),
            pat(r"source-status"),
            pat(r"semantic|predication|M9"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released:.*PM-6.*FPD.*V2.*source-status"),
            pat(r"Held:.*M9.*transmitted wording|Held:.*semantic.*predication"),
        ),
        heart_patterns=(
            pat(r"Heart/register consequence"),
            pat(r"polemical|identity-performance|public-status"),
            pat(r"bounded"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 deformation release condition"),
            pat(r"inherited affiliation|zann-mode|identity-performance"),
            pat(r"proof-method burden"),
        ),
        source_patterns=(
            pat(r"FPD/source-worldview consequence"),
            pat(r"reason-as-validator"),
            pat(r"revelation|source-status"),
        ),
    ),
)
SPEC_BY_MODE = {spec.child_mode: spec for spec in SPECS}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def section(text: str, start_pattern: str, stop_patterns: tuple[str, ...]) -> str:
    start_match = re.search(start_pattern, text, re.IGNORECASE | re.MULTILINE)
    if not start_match:
        return ""
    tail = text[start_match.end() :]
    stop_positions: list[int] = []
    for stop_pattern in stop_patterns:
        stop_match = re.search(stop_pattern, tail, re.IGNORECASE | re.MULTILINE)
        if stop_match:
            stop_positions.append(stop_match.start())
    if stop_positions:
        tail = tail[: min(stop_positions)]
    return tail.strip()


def first_content_line(block: str) -> str:
    for line in block.splitlines():
        stripped = line.strip(" -*")
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


def infer_spec(sample_root: Path, verdict_text: str, output_text: str) -> tuple[SampleSpec | None, list[str]]:
    verdict_match = re.search(r"(?im)^\s*-\s*child mode:\s*(PM-[1246])\b", verdict_text)
    if verdict_match:
        return SPEC_BY_MODE[verdict_match.group(1)], []

    name_matches = [spec for spec in SPECS if spec.child_mode.lower() in sample_root.name.lower()]
    if len(name_matches) == 1:
        return name_matches[0], []

    output_modes = sorted(set(re.findall(r"\bPM-[1246]\b", output_text)))
    if len(output_modes) == 1:
        return SPEC_BY_MODE[output_modes[0]], []
    if not output_modes:
        return None, ["could not infer PM child mode from verdict, directory, or output"]
    return None, [f"ambiguous PM child mode references in output: {', '.join(output_modes)}"]


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

    spec, spec_errors = infer_spec(sample_root, verdict_text, output_text)
    if spec is None:
        return spec_errors

    for needle in spec.prompt_needles:
        if needle.lower() not in input_text.lower():
            errors.append(f"prompt missing expected label-stripped pressure: {needle}")

    if spec.child_mode.lower() not in output_text.lower():
        errors.append(f"output missing child-mode anchor: {spec.child_mode}")

    for pattern in BANNED_OUTPUT_LEAKAGE:
        if pattern.search(output_text):
            errors.append(f"route/check harness leakage in output.md: {pattern.pattern}")

    if re.search(r"\b(school|personality|platform|prestige stack)\b", output_text, re.IGNORECASE):
        errors.append("output appears to depend on school/personality/platform/source-prestige cue")

    target = section(
        output_text,
        r"(?im)^\s*Target:\s*$",
        (r"(?im)^\s*Operation:\s*$", r"(?im)^##\s*Land\(B\)", r"(?im)^##\s*R\(H,Delta\)"),
    )
    operation = section(
        output_text,
        r"(?im)^\s*Operation:\s*$",
        (r"(?im)^\s*Result:\s*$", r"(?im)^##\s*Land\(B\)", r"(?im)^##\s*R\(H,Delta\)"),
    )
    result = section(
        output_text,
        r"(?im)^\s*Result:\s*$",
        (r"(?im)^##\s*Land\(B\)", r"(?im)^##\s*R\(H,Delta\)"),
    )
    land = section(
        output_text,
        r"(?im)^##\s*Land\(B\)",
        (r"(?im)^##\s*R\(H,Delta\)",),
    )
    reread = section(
        output_text,
        r"(?im)^##\s*R\(H,Delta\)(?:/kappa)?",
        (r"(?im)^##\s*Non-Execution", r"(?im)^##\s*Final"),
    )

    blocks = {
        "target": target,
        "operation": operation,
        "result": result,
        "Land(B)": land,
        "R(H,Delta)/kappa": reread,
    }
    minimum_lengths = {
        "target": 130,
        "operation": 300,
        "result": 200,
        "Land(B)": 280,
        "R(H,Delta)/kappa": 320,
    }
    for name, block in blocks.items():
        if not block:
            errors.append(f"missing {name} block")
        elif len(block) < minimum_lengths[name]:
            errors.append(f"{name} block too short for semantic review: {len(block)}")

    operation_first_line = first_content_line(operation)
    if operation_first_line and GENERIC_OPERATION_START.search(operation_first_line):
        errors.append(f"operation starts with generic verb: {operation_first_line}")
    if operation_first_line and not ALLOWED_OPERATION_START.search(operation_first_line):
        errors.append(f"operation does not start with allowed PM verb: {operation_first_line}")
    if operation_first_line and not spec.operation_start.search(operation_first_line):
        errors.append(
            f"operation does not start with expected child verb "
            f"({spec.operation_start.pattern}): {operation_first_line}"
        )

    require_patterns(errors, "target", target, spec.target_patterns)
    require_patterns(errors, "operation", operation, spec.operation_patterns)
    require_patterns(errors, "result", result, spec.result_patterns)
    require_patterns(errors, "Land(B)", land, spec.land_patterns)
    require_patterns(errors, "R(H,Delta)/kappa", reread, spec.reread_patterns)
    require_patterns(errors, "downstream route handling", reread, spec.downstream_patterns)
    require_patterns(errors, "heart/register consequence", output_text, spec.heart_patterns)
    require_patterns(errors, "M5/V1 deformation release condition", output_text, spec.deformation_patterns)
    require_patterns(errors, "FPD/source-worldview consequence", output_text, spec.source_patterns)

    if "held" not in land.lower() and "released" not in land.lower() and "cleared" not in land.lower():
        errors.append("Land(B) lacks visible state delta")
    if not re.search(r"\b(held|released|cleared|narrowed|reclassified|demoted)\b", reread, re.IGNORECASE):
        errors.append("R(H,Delta)/kappa does not consume result as state change")
    if "kappa" not in reread.lower() and "collapse radius" not in reread.lower():
        errors.append("R(H,Delta)/kappa lacks kappa/collapse-radius reread")

    if "- status: PASS" not in verdict_text:
        errors.append("verdict.md does not record PASS")
    if f"- child mode: {spec.child_mode}" not in verdict_text:
        errors.append("verdict.md child mode mismatch")
    if "package/release evidence: no" not in trace_text.lower():
        errors.append("trace.md must preserve non-package evidence boundary")
    if re.search(r"package/release (?:proof|evidence):\s*yes", trace_text, re.IGNORECASE):
        errors.append("trace.md overclaims package/release proof")
    if "not package/release" not in trace_text.lower():
        errors.append("trace.md must state local evidence is not package/release proof")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Root containing Stage-2.5 proof-method child-mode smoke directories.",
    )
    args = parser.parse_args(argv)
    root = args.root if args.root.is_absolute() else (ROOT / args.root)

    if not root.exists():
        print("PM child-mode execution sample validation: FAIL")
        print(f"- root does not exist: {root}")
        return 1

    sample_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not sample_dirs:
        print("PM child-mode execution sample validation: FAIL")
        print(f"- no sample directories under: {root}")
        return 1

    all_errors: dict[str, list[str]] = {}
    checked_modes: list[str] = []
    for sample_dir in sample_dirs:
        verdict_text = read(sample_dir / "verdict.md")
        output_text = read(sample_dir / "output.md")
        spec, _ = infer_spec(sample_dir, verdict_text, output_text)
        if spec:
            checked_modes.append(spec.child_mode)
        errors = validate_sample_dir(sample_dir)
        if errors:
            all_errors[sample_dir.name] = errors

    if all_errors:
        print("PM child-mode execution sample validation: FAIL")
        for directory, errors in all_errors.items():
            for error in errors:
                print(f"- {directory}: {error}")
        return 1

    print("PM child-mode execution sample validation: PASS")
    print(f"- root: {root}")
    print(f"- samples checked: {len(sample_dirs)}")
    print(f"- checked modes: {', '.join(sorted(set(checked_modes)))}")
    print("- evidence boundary: local ignored samples; not package/release smoke proof")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
