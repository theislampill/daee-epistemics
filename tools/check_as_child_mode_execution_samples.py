#!/usr/bin/env python3
"""Validate local Stage-3.5 AS/source-status child-mode execution samples.

This checker is intentionally repo/dev-local. It validates retained ignored
samples under .daee; it is not package/release smoke proof, not a live runner,
and not a universal semantic grader. Its narrow purpose is to reject AS samples
that merely name child modes or print Target/Operation/Result headings without
executing source-status pressure, release/hold state change, and the
heart/M5/FPD plus PM/M9 handoff guardrails.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / ".daee" / "stage3.5-as-child-live-smokes-20260514"

BANNED_OUTPUT_LEAKAGE = (
    re.compile(r"\bowner-floor applied\b", re.IGNORECASE),
    re.compile(r"\bvalidation passed\b", re.IGNORECASE),
    re.compile(r"\bexecute queued owner\b", re.IGNORECASE),
    re.compile(r"\broute_plan\b", re.IGNORECASE),
    re.compile(r"\bfeatures\.json\b", re.IGNORECASE),
    re.compile(r"\bcheck_execution\b", re.IGNORECASE),
    re.compile(r"\bI applied AS\b", re.IGNORECASE),
)

GENERIC_OPERATION_START = re.compile(
    r"^\s*(?:address|discuss|engage|consider|respond to|deal with|explain the issue|analyze generally)\b",
    re.IGNORECASE,
)

ALLOWED_OPERATION_START = re.compile(
    r"^\s*(?:audit|distinguish|classify|reclassify|split|narrow|expose|clear|refuse jurisdiction of)\b",
    re.IGNORECASE,
)

PACKAGE_OVERCLAIM = re.compile(
    r"\b(?:package/release proof:\s*yes|release-proven|package-bound proof|package smoke proof)\b",
    re.IGNORECASE,
)

SOURCE_PARADE = (
    re.compile(r"\bsource parade:\s*(?!blocked|refused|held|avoid)", re.IGNORECASE),
    re.compile(r"\bsource dump\b", re.IGNORECASE),
    re.compile(r"\bargument bank\b(?!.*(?:blocked|refused|held))", re.IGNORECASE),
    re.compile(r"(?im)^\s*-\s*(?:name|quote)\s*\d+\s*:", re.IGNORECASE),
)

PUBLIC_DENUNCIATION = (
    re.compile(r"\bpublic denunciation:\s*(?!blocked|held|avoided|refused)", re.IGNORECASE),
    re.compile(r"\btherefore\s+(?:they|the person|the group)\s+(?:are|is)\s+(?:deviant|condemned|guilty)\b", re.IGNORECASE),
    re.compile(r"\bperson-level verdict:\s*(?!held|blocked|refused)", re.IGNORECASE),
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
    handoff_patterns: tuple[re.Pattern[str], ...]


def pat(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)


SPECS = (
    SampleSpec(
        child_mode="AS-2",
        prompt_needles=("family label", "proves the doctrine", "operative claim"),
        target_patterns=(
            pat(r"family/source/identity label"),
            pat(r"warrant-function"),
            pat(r"doctrine.*warrant.*noetic-frame|doctrine.*warrant.*N"),
        ),
        operation_start=pat(r"^\s*audit\b"),
        operation_patterns=(
            pat(r"identity signal"),
            pat(r"source-status context"),
            pat(r"operative warrant"),
            pat(r"noetic-state lock"),
        ),
        result_patterns=(
            pat(r"demoted.*bounded.*reclassified|demoted.*reclassified|bounded.*reclassified"),
            pat(r"operative doctrine|explicit claim|proof rule|source-status evidence"),
            pat(r"label.*lost tribunal force|label.*cannot.*choose|label.*not operative warrant|blocks identity/prestige"),
        ),
        land_patterns=(
            pat(r"AS-2 lands"),
            pat(r"label no longer decides"),
            pat(r"identity/prestige"),
            pat(r"cleared.*family label is not operative warrant|family label is not operative warrant"),
        ),
        reread_patterns=(
            pat(r"NS"),
            pat(r"source-status"),
            pat(r"proof-method|PM"),
            pat(r"authority"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Held:.*school profile.*doctrine|school profile.*doctrinal content"),
            pat(r"public verdict"),
            pat(r"PM.*M9.*FPD/V2|PM.*M9.*FPD"),
        ),
        heart_patterns=(
            pat(r"Heart/register consequence"),
            pat(r"unity|shame|public affiliation|identity-cost"),
            pat(r"bound|bounded"),
            pat(r"polemical labeling|identity humiliation|public verdict"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 deformation release condition"),
            pat(r"taqlid|inherited framework|zann|identity-performance"),
            pat(r"source-status burden"),
        ),
        source_patterns=(
            pat(r"FPD/source-worldview consequence"),
            pat(r"tribunal|authority-order inversion"),
            pat(r"FPD/V2|source-status"),
        ),
        handoff_patterns=(
            pat(r"PM/M9 handoff"),
            pat(r"proof-denominator"),
            pat(r"semantic/predication|semantic route|M9"),
        ),
    ),
    SampleSpec(
        child_mode="AS-3",
        prompt_needles=("public affiliation", "conscious doctrine", "operative creed"),
        target_patterns=(
            pat(r"inherited affiliation"),
            pat(r"public identity"),
            pat(r"explicit doctrine"),
            pat(r"operative noetic rule"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"inherited affiliation"),
            pat(r"public identity"),
            pat(r"explicit doctrine"),
            pat(r"operative noetic rule"),
        ),
        result_patterns=(
            pat(r"provisional|composite|unknown-pattern-typed"),
            pat(r"unless operative doctrine is actually anchored|unless.*doctrine.*anchored"),
            pat(r"affiliation.*does not prove conscious doctrine|public affiliation does not prove"),
        ),
        land_patterns=(
            pat(r"AS-3 lands"),
            pat(r"affiliation no longer substitutes for doctrine"),
            pat(r"cleared.*affiliation alone does not prove conscious doctrine|affiliation alone does not prove"),
        ),
        reread_patterns=(
            pat(r"NS selection|noetic-frame selection"),
            pat(r"profile confidence"),
            pat(r"AS-2"),
            pat(r"proof-method|PM"),
            pat(r"public-authority|source-status"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Held:.*school-specific content.*public verdict|school-specific content.*public verdict"),
            pat(r"operative doctrine.*anchored|doctrine anchored|until anchored"),
        ),
        heart_patterns=(
            pat(r"Heart/register consequence"),
            pat(r"identity-cost|unity pressure"),
            pat(r"bound|bounded"),
            pat(r"public denunciation|shame"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 deformation release condition"),
            pat(r"taqlid|inherited framework"),
            pat(r"stabilizer"),
        ),
        source_patterns=(
            pat(r"FPD/source-worldview consequence"),
            pat(r"affiliation.*tribunal|tribunal authority"),
            pat(r"FPD/source-status|FPD"),
        ),
        handoff_patterns=(
            pat(r"PM/M9 handoff"),
            pat(r"proof rule"),
            pat(r"semantic/predication|M9"),
        ),
    ),
    SampleSpec(
        child_mode="AS-4",
        prompt_needles=("mistaken statement", "person", "method", "school-level verdict"),
        target_patterns=(
            pat(r"attribution locus"),
            pat(r"statement"),
            pat(r"person"),
            pat(r"method"),
            pat(r"public use"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"statement"),
            pat(r"person"),
            pat(r"method"),
            pat(r"public use"),
            pat(r"source-status function"),
        ),
        result_patterns=(
            pat(r"verdict is narrowed"),
            pat(r"correct locus"),
            pat(r"person-level.*method-level.*held|person-level.*held.*method-level"),
        ),
        land_patterns=(
            pat(r"AS-4 lands"),
            pat(r"attribution locus is typed"),
            pat(r"over-attribution is blocked"),
            pat(r"cleared.*mistaken statement alone does not automatically settle"),
        ),
        reread_patterns=(
            pat(r"deviation"),
            pat(r"takfir"),
            pat(r"source-status|authority-order"),
            pat(r"public-use"),
            pat(r"collapse-radius|kappa"),
            pat(r"person.*method.*public warning.*school-level"),
        ),
        downstream_patterns=(
            pat(r"Held:.*person verdict.*method verdict.*public warning.*school-level conclusion"),
            pat(r"separately grounded|locus is proven"),
        ),
        heart_patterns=(
            pat(r"Heart/register consequence"),
            pat(r"public polemic|shame|community identity"),
            pat(r"bound|bounded"),
            pat(r"rhetorical escalation|escalat"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 deformation release condition"),
            pat(r"hawa/gharad|identity-performance|zann"),
            pat(r"person-level extension|person-level claims|person-level"),
        ),
        source_patterns=(
            pat(r"FPD/source-worldview consequence"),
            pat(r"method.*tribunal"),
            pat(r"local mistaken statement|local error"),
            pat(r"FPD/V2"),
        ),
        handoff_patterns=(
            pat(r"PM/M9 handoff"),
            pat(r"proof-denominator"),
            pat(r"semantic/predication|semantic route|M9"),
        ),
    ),
    SampleSpec(
        child_mode="AS-8",
        prompt_needles=("stack of names", "proof", "prestige", "identity signal", "contrast"),
        target_patterns=(
            pat(r"source-use function"),
            pat(r"names.*quotations|source stack"),
        ),
        operation_start=pat(r"^\s*classify\b"),
        operation_patterns=(
            pat(r"evidence"),
            pat(r"contrast"),
            pat(r"genealogy"),
            pat(r"identity signal"),
            pat(r"prestige signal"),
            pat(r"held material"),
            pat(r"bounded comparison"),
        ),
        result_patterns=(
            pat(r"Source-use is reclassified|source-use.*reclassified"),
            pat(r"content release"),
            pat(r"argument-bank|source-parade"),
            pat(r"blocked|blocks"),
        ),
        land_patterns=(
            pat(r"AS-8 lands"),
            pat(r"source function and weight are typed"),
            pat(r"before content release"),
            pat(r"source quantity and prestige do not automatically equal proof"),
        ),
        reread_patterns=(
            pat(r"proof-method|PM"),
            pat(r"authority-order"),
            pat(r"source-status"),
            pat(r"downstream claim support"),
            pat(r"public verdict"),
            pat(r"school profile"),
            pat(r"M9"),
            pat(r"FPD/V2"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Held:.*content claim.*source parade.*public verdict.*school profile"),
            pat(r"source function and weight are typed|until typed"),
        ),
        heart_patterns=(
            pat(r"Heart/register consequence"),
            pat(r"public prestige|shame|affiliation pressure|authority fatigue"),
            pat(r"bound|bounded"),
            pat(r"source parade"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 deformation release condition"),
            pat(r"taqlid|inherited framework|zann"),
            pat(r"stabilizer|stabilizing"),
        ),
        source_patterns=(
            pat(r"FPD/source-worldview consequence"),
            pat(r"academic method|school prestige|external authority"),
            pat(r"tribunal"),
            pat(r"FPD/V2"),
        ),
        handoff_patterns=(
            pat(r"PM/M9 handoff"),
            pat(r"proof denominator|proof tool"),
            pat(r"loaded label|predication"),
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


def infer_spec(sample_root: Path, output_text: str, verdict_text: str) -> tuple[SampleSpec | None, list[str]]:
    name_modes = sorted(set(re.findall(r"\bAS-[2348]\b", sample_root.name)))
    if len(name_modes) == 1:
        return SPEC_BY_MODE[name_modes[0]], []
    if len(name_modes) > 1:
        return None, [f"ambiguous AS child mode references in directory: {', '.join(name_modes)}"]

    verdict_match = re.search(r"(?im)^\s*-\s*child mode:\s*(AS-[2348])\b", verdict_text)
    if verdict_match:
        return SPEC_BY_MODE[verdict_match.group(1)], []

    mode_matches = re.findall(r"(?im)^(?:#.*\bAS-[2348]\b|Current child mode:\s*`?(AS-[2348]))", output_text)
    flattened = [item if isinstance(item, str) else "".join(item) for item in mode_matches]
    output_modes = sorted(set(mode for mode in flattened if mode))
    if len(output_modes) == 1:
        return SPEC_BY_MODE[output_modes[0]], []
    if not output_modes:
        return None, ["could not infer AS child mode from directory, verdict, or output"]
    return None, [f"ambiguous AS child mode references in output: {', '.join(output_modes)}"]


def has_forbidden(patterns: tuple[re.Pattern[str], ...], text: str) -> re.Pattern[str] | None:
    for pattern in patterns:
        if pattern.search(text):
            return pattern
    return None


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

    spec, spec_errors = infer_spec(sample_root, output_text, verdict_text)
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

    if PACKAGE_OVERCLAIM.search(output_text) or PACKAGE_OVERCLAIM.search(trace_text) or PACKAGE_OVERCLAIM.search(verdict_text):
        errors.append("package/release proof overclaim")

    source_parade = has_forbidden(SOURCE_PARADE, output_text)
    if source_parade:
        errors.append(f"source parade / argument-bank release: {source_parade.pattern}")

    denunciation = has_forbidden(PUBLIC_DENUNCIATION, output_text)
    if denunciation:
        errors.append(f"public denunciation / person-level overreach: {denunciation.pattern}")

    target = section(
        output_text,
        r"(?im)^\s*(?:##\s*)?Target:?\s*$",
        (r"(?im)^\s*(?:##\s*)?Operation:?\s*$", r"(?im)^##\s*Land\(B\)", r"(?im)^##\s*R\(H,Delta\)"),
    )
    operation = section(
        output_text,
        r"(?im)^\s*(?:##\s*)?Operation:?\s*$",
        (r"(?im)^\s*(?:##\s*)?Result:?\s*$", r"(?im)^##\s*Land\(B\)", r"(?im)^##\s*R\(H,Delta\)"),
    )
    result = section(
        output_text,
        r"(?im)^\s*(?:##\s*)?Result:?\s*$",
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
        "operation": 280,
        "result": 180,
        "Land(B)": 260,
        "R(H,Delta)/kappa": 300,
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
        errors.append(f"operation does not start with allowed AS verb: {operation_first_line}")
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
    require_patterns(errors, "PM/M9 handoff", output_text, spec.handoff_patterns)

    if not re.search(r"\b(cleared|narrowed|held|released|demoted|bounded|reclassified|provisional)\b", land, re.IGNORECASE):
        errors.append("Land(B) lacks visible burden-state delta")
    if not re.search(r"\b(held|released|cleared|narrowed|reread|demoted|reclassified)\b", reread, re.IGNORECASE):
        errors.append("R(H,Delta)/kappa does not consume result as state change")
    if "kappa" not in reread.lower() and "collapse radius" not in reread.lower():
        errors.append("R(H,Delta)/kappa lacks kappa/collapse-radius reread")

    boundary_text = "\n".join((trace_text, verdict_text)).lower()
    if "not package/release" not in boundary_text:
        errors.append("trace/verdict must preserve non-package evidence boundary")
    if "not a general semantic checker" not in boundary_text:
        errors.append("trace/verdict must state this is not a general semantic checker")

    return errors


def summarize_errors(errors: list[str]) -> str:
    summary: list[str] = []
    joined = "\n".join(errors).lower()

    checks = (
        ("missing required file", "missing input.md" in joined or "missing output.md" in joined or "missing trace.md" in joined or "missing verdict.md" in joined),
        ("ambiguous/missing AS child mode", "could not infer" in joined or "ambiguous as child mode" in joined),
        ("generic operation verb", "generic verb" in joined),
        ("missing case-specific target", "target missing pattern" in joined or "target block too short" in joined),
        ("missing child-specific operation pressure", "operation missing pattern" in joined or "expected child verb" in joined),
        ("missing result/state change", "result missing pattern" in joined or "result block too short" in joined),
        ("missing Land(B)", "missing land(b) block" in joined),
        ("unsupported Land(B)", "land(b) block too short" in joined or "land(b) lacks visible burden-state delta" in joined),
        ("missing R(H,Delta)/kappa", "missing r(h,delta)/kappa block" in joined),
        ("reread does not consume result", "r(h,delta)/kappa does not consume result" in joined or "r(h,delta)/kappa missing pattern" in joined),
        ("missing downstream held/released route", "downstream route handling missing pattern" in joined),
        ("missing heart/register consequence", "heart/register consequence missing pattern" in joined),
        ("missing M5/V1 deformation release condition", "m5/v1 deformation release condition missing pattern" in joined),
        ("missing FPD/source-worldview consequence", "fpd/source-worldview consequence missing pattern" in joined),
        ("missing PM/M9 handoff", "pm/m9 handoff missing pattern" in joined),
        ("source parade / argument-bank release", "source parade / argument-bank release" in joined),
        ("public denunciation / person-level overreach", "public denunciation / person-level overreach" in joined),
        ("route/check harness leakage", "route/check harness leakage" in joined),
        ("package/release proof overclaim", "package/release proof overclaim" in joined),
    )
    for label, present in checks:
        if present:
            summary.append(label)

    if not summary:
        summary = errors[:5]
    return "; ".join(summary)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Root containing Stage-3.5 AS/source-status child-mode smoke directories.",
    )
    args = parser.parse_args(argv)
    root = args.root if args.root.is_absolute() else (ROOT / args.root)

    if not root.exists():
        print("AS child-mode execution sample validation: FAIL")
        print(f"- root does not exist: {root}")
        return 1

    sample_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not sample_dirs:
        print("AS child-mode execution sample validation: FAIL")
        print(f"- no sample directories under: {root}")
        return 1

    all_errors: dict[str, list[str]] = {}
    checked_modes: list[str] = []
    for sample_dir in sample_dirs:
        output_text = read(sample_dir / "output.md")
        verdict_text = read(sample_dir / "verdict.md")
        spec, _ = infer_spec(sample_dir, output_text, verdict_text)
        if spec:
            checked_modes.append(spec.child_mode)
        errors = validate_sample_dir(sample_dir)
        if errors:
            all_errors[sample_dir.name] = errors

    if all_errors:
        print("AS child-mode execution sample validation: FAIL")
        for directory, errors in all_errors.items():
            print(f"- {directory}: {summarize_errors(errors)}")
        return 1

    print("AS child-mode execution sample validation: PASS")
    print(f"- root: {root}")
    print(f"- samples checked: {len(sample_dirs)}")
    print(f"- checked modes: {', '.join(sorted(set(checked_modes)))}")
    print("- evidence boundary: local ignored samples; not package/release smoke proof")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
