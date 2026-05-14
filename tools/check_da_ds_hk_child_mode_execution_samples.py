#!/usr/bin/env python3
"""Validate local Stage-5.5 DA/DS/HK child-mode execution samples.

This checker is intentionally repo/dev-local. It validates retained ignored
samples under .daee; it is not package/release smoke proof, not a live runner,
and not a universal semantic grader. Its narrow purpose is to reject DA/DS/HK
samples that merely name child modes or print Target/Operation/Result headings
without executing divine-action/speech/huduth pressure, burden-state change,
and the heart/M5 plus M9/V8/PM/AS/DW/P7/FPD handoff guardrails.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / ".daee" / "stage5.5-da-ds-hk-child-live-smokes-20260514"

BANNED_OUTPUT_LEAKAGE = (
    re.compile(r"\bowner-floor applied\b", re.IGNORECASE),
    re.compile(r"\bvalidation passed\b", re.IGNORECASE),
    re.compile(r"\bexecute queued owner\b", re.IGNORECASE),
    re.compile(r"\broute_plan\b", re.IGNORECASE),
    re.compile(r"\bfeatures\.json\b", re.IGNORECASE),
    re.compile(r"\bcheck_execution\b", re.IGNORECASE),
    re.compile(r"\bI applied (?:DA|DS|HK)\b", re.IGNORECASE),
)

GENERIC_OPERATION_START = re.compile(
    r"^\s*(?:address|discuss|engage|consider|respond to|deal with|explain the issue|analyze generally)\b",
    re.IGNORECASE,
)

ALLOWED_OPERATION_START = re.compile(
    r"^\s*(?:distinguish|audit|classify|split|narrow|expose|clear|refuse jurisdiction of|refuse transfer of|hold)\b",
    re.IGNORECASE,
)

PACKAGE_OVERCLAIM = re.compile(
    r"\b(?:package/release proof:\s*yes|release-proven|package-bound proof|package smoke proof)\b",
    re.IGNORECASE,
)

SOURCE_PARADE = (
    re.compile(r"\bsource parade:\s*(?:released|performed|provided|yes)\b", re.IGNORECASE),
    re.compile(r"\bsource dump:\s*(?:released|performed|provided|yes)\b", re.IGNORECASE),
    re.compile(r"\bargument bank\b(?!.*(?:blocked|held|refused|avoid))", re.IGNORECASE),
    re.compile(r"(?im)^\s*-\s*(?:name|quote)\s*\d+\s*:", re.IGNORECASE),
)

PUBLIC_DENUNCIATION = (
    re.compile(r"\bpublic denunciation:\s*(?:released|performed|provided|yes)\b", re.IGNORECASE),
    re.compile(r"\btherefore\s+(?:they|the person|the group)\s+(?:are|is)\s+(?:deviant|condemned|guilty)\b", re.IGNORECASE),
    re.compile(r"\bperson-level verdict:\s*(?!held|blocked|refused)", re.IGNORECASE),
)

SCHOOL_LABEL_AS_DOCTRINE = (
    re.compile(r"\bschool label\s+(?:is|proves|settles)\s+(?:operative )?doctrine\b", re.IGNORECASE),
    re.compile(r"\b(?:because|since)\s+of\s+the\s+school\s+label\b.*\b(?:doctrine|verdict)\s+(?:is|follows)\b", re.IGNORECASE | re.DOTALL),
)

GENERIC_ATTRIBUTE_TALK = (
    re.compile(r"\bgeneric attribute-talk:\s*(?:sufficient|passes|enough|yes)\b", re.IGNORECASE),
    re.compile(r"\bthe issue is simply a generic attribute issue\b", re.IGNORECASE),
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
    handoff_patterns: tuple[re.Pattern[str], ...]


def pat(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)


SPECS = (
    SampleSpec(
        child_mode="DA-1",
        prompt_needles=("real divine action", "created external product", "creaturely change"),
        target_patterns=(
            pat(r"relation among actor, action, and created effect"),
            pat(r"actor.*Allah"),
            pat(r"action.*real divine act"),
            pat(r"created effect"),
            pat(r"created product|creaturely.*change|creaturely modality"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"actor, action, and effect"),
            pat(r"refuse the collapse"),
            pat(r"created product"),
            pat(r"creaturely modality|creaturely motion|bodily motion"),
        ),
        result_patterns=(
            pat(r"Divine action can be treated as real"),
            pat(r"without making the action a created external object"),
            pat(r"creaturely bodily motion|creaturely motion"),
            pat(r"created effect remains created"),
        ),
        land_patterns=(
            pat(r"action/actor/effect collapse is blocked"),
            pat(r"binary no longer governs|no longer defeated"),
            pat(r"specific entailment"),
        ),
        reread_patterns=(
            pat(r"M9"),
            pat(r"V8"),
            pat(r"PM|proof-method"),
            pat(r"FPD|V2"),
            pat(r"AS"),
            pat(r"DW|P7"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released: DA-1"),
            pat(r"Held:.*V8.*do-attribute.*kalamic.*perfection"),
            pat(r"proof expansion|source stacks|school routes|public verdicts"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"polemical shame|identity-performance|anxiety"),
            pat(r"bounded|held"),
            pat(r"source parade|public denunciation"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"genuine predication/action burden"),
            pat(r"shubhah|zann|inherited labels|identity-performance"),
            pat(r"label does not count as DA-1 execution"),
        ),
        handoff_patterns=(
            pat(r"M9/V8/PM/AS/DW/P7/FPD Handoff"),
            pat(r"M9"),
            pat(r"V8"),
            pat(r"PM/FPD/V2|FPD/V2|V2"),
            pat(r"AS"),
            pat(r"DW/P7"),
        ),
    ),
    SampleSpec(
        child_mode="DA-2",
        prompt_needles=("Divine purpose and wisdom", "purpose in action", "need"),
        target_patterns=(
            pat(r"relation among will, action, effect, wisdom, purpose, need, and cause"),
            pat(r"purpose.*equated with lack or need"),
            pat(r"wisdom.*external cause"),
            pat(r"created effect"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"will, action, created effect, wisdom, purpose, and need"),
            pat(r"narrow the inference"),
            pat(r"purpose to deficiency|purpose.*deficiency"),
            pat(r"need: dependence, lack, or external cause"),
        ),
        result_patterns=(
            pat(r"Purpose/wisdom can be affirmed"),
            pat(r"without making Allah dependent"),
            pat(r"purpose no longer functions"),
            pat(r"wisdom.*without.*need|wise ordering without.*need"),
        ),
        land_patterns=(
            pat(r"purpose no longer entails need"),
            pat(r"purpose-to-need inference\s+is\s+blocked"),
            pat(r"burden-state changes"),
        ),
        reread_patterns=(
            pat(r"perfection-criterion"),
            pat(r"PM|proof-method"),
            pat(r"FPD|V2"),
            pat(r"M9"),
            pat(r"V8"),
            pat(r"AS"),
            pat(r"DW|P7"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released: DA-2"),
            pat(r"Held:.*extended wisdom arguments"),
            pat(r"purpose-to-need inference is typed|need/purpose burden lands"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"moral protest|public polemic|grief|anxiety"),
            pat(r"bounded|held"),
            pat(r"debate sprawl|source parade"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"shubhah"),
            pat(r"identity-performance|inherited framework|zann"),
            pat(r"deformation label does not execute DA-2"),
        ),
        handoff_patterns=(
            pat(r"M9/V8/PM/AS/DW/P7/FPD Handoff"),
            pat(r"M9"),
            pat(r"V8"),
            pat(r"PM/FPD/V2|FPD/V2|V2"),
            pat(r"AS"),
            pat(r"DW/P7"),
        ),
    ),
    SampleSpec(
        child_mode="DS-1",
        prompt_needles=("Revealed speech", "created sounds", "internal meaning"),
        target_patterns=(
            pat(r"relation among divine speech, source, revealed wording, articulation"),
            pat(r"human articulation/recitation"),
            pat(r"sounds/letters"),
            pat(r"createdness attribution"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"speech source, revealed speech, human articulation/recitation"),
            pat(r"created sound-event"),
            pat(r"before assigning createdness"),
            pat(r"denying real speech"),
        ),
        result_patterns=(
            pat(r"Human recitation/articulation can be treated as created"),
            pat(r"without collapsing revealed speech"),
            pat(r"evacuating real speech"),
            pat(r"createdness attribution is localized"),
        ),
        land_patterns=(
            pat(r"speech/source/articulation are separated"),
            pat(r"createdness\s+attribution\s+is\s+localized"),
            pat(r"createdness transfer is blocked"),
        ),
        reread_patterns=(
            pat(r"M9"),
            pat(r"V8"),
            pat(r"kalamic"),
            pat(r"prophetic-discourse"),
            pat(r"AS"),
            pat(r"PM|FPD|V2"),
            pat(r"DW|P7"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released: DS-1"),
            pat(r"Held:.*kalamic school routes"),
            pat(r"recitation debates|public verdicts|proof stacks|source parade"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"public sectarian pressure|identity-cost"),
            pat(r"bounded|held"),
            pat(r"denunciation|school-label sorting"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"speech/predication burden"),
            pat(r"inherited affiliation|taqlid|zann|identity-performance"),
            pat(r"deformation label does not execute DS-1"),
        ),
        handoff_patterns=(
            pat(r"M9/V8/PM/AS/DW/P7/FPD Handoff"),
            pat(r"M9"),
            pat(r"V8"),
            pat(r"PM/FPD/V2|FPD/V2|V2"),
            pat(r"AS"),
            pat(r"DW/P7"),
            pat(r"prophetic-discourse-neutralization"),
        ),
    ),
    SampleSpec(
        child_mode="HK-1",
        prompt_needles=("act occurs", "treated as created", "renewed divine action"),
        target_patterns=(
            pat(r"relation among occurrence, renewal, temporal relation, created product"),
            pat(r"divine act, and attribute"),
            pat(r"createdness is transferred"),
            pat(r"temporal relation"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"huduth/occurrence/renewal"),
            pat(r"khalq/created external product"),
            pat(r"audit whether\s+createdness is being transferred"),
            pat(r"effect\s+to\s+act/attribute"),
        ),
        result_patterns=(
            pat(r"Temporal or relational language no longer automatically proves"),
            pat(r"createdness of divine act or\s+attribute"),
            pat(r"created external products remain created"),
            pat(r"transfer\s+from\s+effect\s+to\s+act/attribute\s+is\s+blocked"),
        ),
        land_patterns=(
            pat(r"huduth/khalq transfer is blocked"),
            pat(r"missing\s+discriminator"),
            pat(r"createdness transfer (?:is not licensed|remains held)"),
        ),
        reread_patterns=(
            pat(r"divine action"),
            pat(r"divine speech"),
            pat(r"PM"),
            pat(r"M9"),
            pat(r"V8"),
            pat(r"kalamic"),
            pat(r"FPD|V2"),
            pat(r"AS"),
            pat(r"DW|P7"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released: HK-1"),
            pat(r"Held:.*divine-speech/action school routes"),
            pat(r"proof-method elaboration|source parade|public verdicts"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"overcomplexity|anxiety|public polemic"),
            pat(r"bounded|held"),
            pat(r"proof-stacking"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"genuine proof/predication pressure"),
            pat(r"shubhah|inherited formalism|zann|overcomplexity"),
            pat(r"deformation label does not execute HK-1"),
        ),
        handoff_patterns=(
            pat(r"M9/V8/PM/AS/DW/P7/FPD Handoff"),
            pat(r"M9"),
            pat(r"V8"),
            pat(r"PM"),
            pat(r"FPD/V2|V2"),
            pat(r"AS"),
            pat(r"DW/P7"),
        ),
    ),
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def required_files_missing(sample_dir: Path) -> list[str]:
    return [name for name in ("input.md", "output.md", "trace.md", "verdict.md") if not (sample_dir / name).exists()]


def infer_spec(sample_dir: Path, output_text: str, verdict_text: str) -> tuple[SampleSpec | None, list[str]]:
    haystack = "\n".join((sample_dir.name, output_text, verdict_text))
    matches = [spec for spec in SPECS if re.search(rf"\b{re.escape(spec.child_mode)}\b", haystack)]
    if not matches:
        return None, ["could not infer DA/DS/HK child mode"]
    if len(matches) > 1:
        return None, [f"ambiguous child mode: {', '.join(spec.child_mode for spec in matches)}"]
    return matches[0], []


def extract_block(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", markdown[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(markdown)
    return markdown[start:end].strip()


def first_content_line(block: str) -> str:
    for line in block.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("-"):
            return stripped
    return ""


def require_patterns(errors: list[str], label: str, text: str, patterns: tuple[re.Pattern[str], ...]) -> None:
    for pattern in patterns:
        if not pattern.search(text):
            errors.append(f"{label} missing pattern: {pattern.pattern}")


def validate_sample_dir(sample_dir: Path) -> list[str]:
    errors: list[str] = []
    missing = required_files_missing(sample_dir)
    if missing:
        return [f"missing {name}" for name in missing]

    input_text = read(sample_dir / "input.md")
    output_text = read(sample_dir / "output.md")
    trace_text = read(sample_dir / "trace.md")
    verdict_text = read(sample_dir / "verdict.md")

    spec, infer_errors = infer_spec(sample_dir, output_text, verdict_text)
    if infer_errors:
        return infer_errors
    assert spec is not None

    combined_public = output_text
    if any(pattern.search(combined_public) for pattern in BANNED_OUTPUT_LEAKAGE):
        errors.append("route/check harness leakage in public output")
    if PACKAGE_OVERCLAIM.search("\n".join((output_text, trace_text, verdict_text))):
        errors.append("package/release proof overclaim")
    if any(pattern.search(output_text) for pattern in SOURCE_PARADE):
        errors.append("source parade / argument-bank release")
    if any(pattern.search(output_text) for pattern in PUBLIC_DENUNCIATION):
        errors.append("public denunciation / person-level overreach")
    if any(pattern.search(output_text) for pattern in SCHOOL_LABEL_AS_DOCTRINE):
        errors.append("school label as operative doctrine")
    if any(pattern.search(output_text) for pattern in GENERIC_ATTRIBUTE_TALK):
        errors.append("generic attribute-talk instead of DA/DS/HK pressure")

    lowered_input = input_text.lower()
    for needle in spec.prompt_needles:
        if needle.lower() not in lowered_input:
            errors.append(f"input prompt missing expected cue: {needle}")

    target = extract_block(output_text, "Target")
    operation = extract_block(output_text, "Operation")
    result = extract_block(output_text, "Result")
    land = extract_block(output_text, "Land(B)")
    reread = extract_block(output_text, "R(H,Delta)/kappa")

    blocks = {
        "target": target,
        "operation": operation,
        "result": result,
        "Land(B)": land,
        "R(H,Delta)/kappa": reread,
    }
    minimum_lengths = {
        "target": 150,
        "operation": 260,
        "result": 190,
        "Land(B)": 220,
        "R(H,Delta)/kappa": 280,
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
        errors.append(f"operation does not start with allowed DA/DS/HK verb: {operation_first_line}")
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
    require_patterns(errors, "downstream route handling", output_text, spec.downstream_patterns)
    require_patterns(errors, "heart/register consequence", output_text, spec.heart_patterns)
    require_patterns(errors, "M5/V1 deformation release condition", output_text, spec.deformation_patterns)
    require_patterns(errors, "M9/V8/PM/AS/DW/P7/FPD handoff", output_text, spec.handoff_patterns)

    if not re.search(r"\b(held|released|blocked|bounded|localized|narrowed|typed|lands|state changes?)\b", land, re.IGNORECASE):
        errors.append("Land(B) lacks visible burden-state delta")
    if not re.search(r"\b(held|released|blocked|localized|reread|narrows|eligible|consumes)\b", reread, re.IGNORECASE):
        errors.append("R(H,Delta)/kappa does not consume result as state change")
    if "kappa" not in reread.lower() and "collapse radius" not in reread.lower():
        errors.append("R(H,Delta)/kappa lacks kappa/collapse-radius reread")

    boundary_text = "\n".join((trace_text, verdict_text)).lower()
    if "not package/release" not in boundary_text:
        errors.append("trace/verdict must preserve non-package evidence boundary")
    if "not a universal semantic grader" not in boundary_text and "not a general semantic checker" not in boundary_text:
        errors.append("trace/verdict must state this is not a universal semantic grader")

    return errors


def summarize_errors(errors: list[str]) -> str:
    summary: list[str] = []
    joined = "\n".join(errors).lower()

    checks = (
        ("missing required file", "missing input.md" in joined or "missing output.md" in joined or "missing trace.md" in joined or "missing verdict.md" in joined),
        ("ambiguous/missing child mode", "could not infer" in joined or "ambiguous child mode" in joined),
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
        ("missing M9/V8/PM/AS/DW/P7/FPD handoff", "m9/v8/pm/as/dw/p7/fpd handoff missing pattern" in joined),
        ("source parade / argument-bank release", "source parade / argument-bank release" in joined),
        ("school label as operative doctrine", "school label as operative doctrine" in joined),
        ("public denunciation / person-level overreach", "public denunciation / person-level overreach" in joined),
        ("generic attribute-talk instead of DA/DS/HK pressure", "generic attribute-talk instead of da/ds/hk pressure" in joined),
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
        help="Root containing Stage-5.5 DA/DS/HK child-mode smoke directories.",
    )
    args = parser.parse_args(argv)
    root = args.root if args.root.is_absolute() else (ROOT / args.root)

    if not root.exists():
        print("DA/DS/HK child-mode execution sample validation: FAIL")
        print(f"- root does not exist: {root}")
        return 1

    sample_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not sample_dirs:
        print("DA/DS/HK child-mode execution sample validation: FAIL")
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
        print("DA/DS/HK child-mode execution sample validation: FAIL")
        for directory, errors in all_errors.items():
            print(f"- {directory}: {summarize_errors(errors)}")
        return 1

    print("DA/DS/HK child-mode execution sample validation: PASS")
    print(f"- root: {root}")
    print(f"- samples checked: {len(sample_dirs)}")
    print(f"- checked modes: {', '.join(sorted(set(checked_modes)))}")
    print("- evidence boundary: local ignored samples; not package/release smoke proof")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
