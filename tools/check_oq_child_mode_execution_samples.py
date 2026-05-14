#!/usr/bin/env python3
"""Validate local Stage-6.5 OQ child-mode execution samples.

This checker is intentionally repo/dev-local. It validates retained ignored
samples under .daee; it is not package/release smoke proof, not a live runner,
and not a universal semantic grader. Its narrow purpose is to reject OQ samples
that merely name child modes or print Target/Operation/Result headings without
executing ontological role typing, burden-state change, and the
heart/M5 plus M9/PM/AS/DW/DA/DS/HK/P7/FPD handoff guardrails.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / ".daee" / "stage6.5-oq-child-live-smokes-20260514"

BANNED_OUTPUT_LEAKAGE = (
    re.compile(r"\bowner-floor applied\b", re.IGNORECASE),
    re.compile(r"\bvalidation passed\b", re.IGNORECASE),
    re.compile(r"\bexecute queued owner\b", re.IGNORECASE),
    re.compile(r"\broute_plan\b", re.IGNORECASE),
    re.compile(r"\bfeatures\.json\b", re.IGNORECASE),
    re.compile(r"\bcheck_execution\b", re.IGNORECASE),
    re.compile(r"\bI applied OQ\b", re.IGNORECASE),
)

GENERIC_OPERATION_START = re.compile(
    r"^\s*(?:address|discuss|engage|consider|respond to|deal with|explain the issue|analyze generally)\b",
    re.IGNORECASE,
)

ALLOWED_OPERATION_START = re.compile(
    r"^\s*(?:distinguish|audit|classify|split|narrow|expose|clear|refuse transfer of|hold)\b",
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
)

GENERIC_ONTOLOGY_TALK = (
    re.compile(r"\bgeneric ontology talk:\s*(?:sufficient|passes|enough|yes)\b", re.IGNORECASE),
    re.compile(r"\bthe issue is simply generic ontology\b", re.IGNORECASE),
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
        child_mode="OQ-5",
        prompt_needles=("general concept", "concrete thing", "extra entity"),
        target_patterns=(
            pat(r"relation between universal, particular, concept, instance, and predication"),
            pat(r"universal/class concept"),
            pat(r"particular instance"),
            pat(r"mental classification to external ontology|extra entity|real part"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"universal/class concept from particular instance"),
            pat(r"mental classification to external ontology"),
            pat(r"predicating a term"),
            pat(r"extra-mental structure"),
        ),
        result_patterns=(
            pat(r"Universal/particular transfer is blocked"),
            pat(r"classification remains classification"),
            pat(r"extra-mental entity/part claims are held"),
        ),
        land_patterns=(
            pat(r"concept/instance relation is typed"),
            pat(r"classification proves an entity/part"),
            pat(r"external ontology is separately established"),
        ),
        reread_patterns=(
            pat(r"M9"),
            pat(r"PM|proof-method"),
            pat(r"FPD|V2"),
            pat(r"AS"),
            pat(r"DW|P7"),
            pat(r"DA/DS/HK|DA"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released: OQ-5"),
            pat(r"Held:.*proof route.*predication route.*category claims"),
            pat(r"universal/particular status is typed"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"technical-overcomplexity|prestige pressure|anxious"),
            pat(r"bounded|held"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"genuine ontology/predication pressure"),
            pat(r"shubhah|inherited jargon|zann|overcomplexity"),
            pat(r"deformation label does not execute OQ-5"),
        ),
        handoff_patterns=(
            pat(r"M9/PM/AS/DW/DA/DS/HK/P7/FPD Handoff"),
            pat(r"M9"),
            pat(r"PM/FPD/V2|FPD/V2|V2"),
            pat(r"AS"),
            pat(r"DW/P7"),
            pat(r"DA/DS/HK"),
        ),
    ),
    SampleSpec(
        child_mode="OQ-6",
        prompt_needles=("distinction made in thought", "external separability", "real composition"),
        target_patterns=(
            pat(r"relation between mental distinction, conceptual model, and external ontology"),
            pat(r"mental distinction"),
            pat(r"external separability"),
            pat(r"real composition|external ontology"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"mental/conceptual distinction from external ontological claim"),
            pat(r"audit what is\s+actually instantiated"),
            pat(r"conceptual distinction"),
            pat(r"external separability"),
        ),
        result_patterns=(
            pat(r"Mental/external transfer is blocked"),
            pat(r"conceptual distinction remains available"),
            pat(r"external separability is not granted"),
            pat(r"real composition requires separate proof"),
        ),
        land_patterns=(
            pat(r"conceptual distinction no longer proves external\s+separability/composition"),
            pat(r"thought-distinction was treated as ontology-proof"),
            pat(r"transfer is blocked"),
        ),
        reread_patterns=(
            pat(r"M9"),
            pat(r"Do-attribute|do-attribute"),
            pat(r"PM|proof-method"),
            pat(r"FPD|V2"),
            pat(r"AS"),
            pat(r"DW|P7"),
            pat(r"DA/DS/HK|DA"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released: OQ-6"),
            pat(r"Held:.*composition.*attribute.*proof"),
            pat(r"mental\s+distinction and external ontology are separated"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"anxiety around complexity|composition"),
            pat(r"bounded|held|proof-stack"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"true ontology pressure"),
            pat(r"shubhah|overcomplexity|wiswas|inherited jargon|zann"),
            pat(r"deformation label does not execute OQ-6"),
        ),
        handoff_patterns=(
            pat(r"M9/PM/AS/DW/DA/DS/HK/P7/FPD Handoff"),
            pat(r"M9"),
            pat(r"PM/FPD/V2|FPD/V2|V2"),
            pat(r"AS"),
            pat(r"DW/P7"),
            pat(r"DA/DS/HK"),
        ),
    ),
    SampleSpec(
        child_mode="OQ-8",
        prompt_needles=("cause", "condition", "autonomous necessity"),
        target_patterns=(
            pat(r"causal relation among cause, condition, impediment, tendency, effect"),
            pat(r"divine governance"),
            pat(r"necessity/autonomy claim"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"cause, condition, impediment, tendency, effect, and necessity"),
            pat(r"metaphysical conclusions"),
            pat(r"conditions from the cause itself"),
            pat(r"autonomous necessity"),
        ),
        result_patterns=(
            pat(r"Causal relation is typed"),
            pat(r"autonomy, necessity, or occasionalist flattening is blocked"),
            pat(r"causes can remain real without becoming self-sufficient"),
        ),
        land_patterns=(
            pat(r"cause/condition/impediment are no longer collapsed"),
            pat(r"autonomous necessity"),
            pat(r"flattening is blocked"),
        ),
        reread_patterns=(
            pat(r"causal-series"),
            pat(r"PM|proof-method"),
            pat(r"FPD|V2"),
            pat(r"naturalism"),
            pat(r"DA/DS/HK|DA"),
            pat(r"M9"),
            pat(r"AS"),
            pat(r"DW|P7"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released: OQ-8"),
            pat(r"Held:.*naturalism route.*proof-family route.*divine-action route"),
            pat(r"causal role is typed"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"proof anxiety|scientistic prestige"),
            pat(r"bounded|proof-dump"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"causal ontology burden"),
            pat(r"shubhah|inherited framework|zann|identity-performance"),
            pat(r"deformation label does not execute OQ-8"),
        ),
        handoff_patterns=(
            pat(r"M9/PM/AS/DW/DA/DS/HK/P7/FPD Handoff"),
            pat(r"PM/FPD/V2|FPD/V2|V2"),
            pat(r"M9"),
            pat(r"AS"),
            pat(r"DW/P7"),
            pat(r"DA/DS/HK"),
            pat(r"causal-series-taxonomy"),
        ),
    ),
    SampleSpec(
        child_mode="OQ-9",
        prompt_needles=("created effect", "detached from source", "signification"),
        target_patterns=(
            pat(r"relation among source, action, intention, sign, effect"),
            pat(r"created product"),
            pat(r"severance claim"),
            pat(r"non-signifying|signification"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"source, action, intention, sign, effect, and product"),
            pat(r"being severed from or collapsed into the source/action"),
            pat(r"created product from the source and action"),
            pat(r"signification"),
        ),
        result_patterns=(
            pat(r"Sign/action/effect relation is restored, narrowed, or held"),
            pat(r"created effect remains created"),
            pat(r"signification is not severed"),
        ),
        land_patterns=(
            pat(r"source/action/effect relation is typed"),
            pat(r"lost signification"),
            pat(r"severance is\s+blocked"),
        ),
        reread_patterns=(
            pat(r"DA/DS/HK"),
            pat(r"M9"),
            pat(r"PM|proof"),
            pat(r"FPD|V2"),
            pat(r"AS"),
            pat(r"DW|P7"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released: OQ-9"),
            pat(r"Held:.*miracle.*divine action.*purpose.*proof.*source-status"),
            pat(r"relation is typed"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"moral protest|spectacle demand|identity pressure"),
            pat(r"bounded|source parade|public denunciation"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"genuine source/action/effect burden"),
            pat(r"shubhah|zann|identity-performance|inherited framework"),
            pat(r"deformation label does not execute OQ-9"),
        ),
        handoff_patterns=(
            pat(r"M9/PM/AS/DW/DA/DS/HK/P7/FPD Handoff"),
            pat(r"DA/DS/HK"),
            pat(r"M9"),
            pat(r"PM/FPD/V2|FPD/V2|V2"),
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
        return None, ["could not infer OQ child mode"]
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

    if any(pattern.search(output_text) for pattern in BANNED_OUTPUT_LEAKAGE):
        errors.append("route/check harness leakage in public output")
    if PACKAGE_OVERCLAIM.search("\n".join((output_text, trace_text, verdict_text))):
        errors.append("package/release proof overclaim")
    if any(pattern.search(output_text) for pattern in SOURCE_PARADE):
        errors.append("source parade / argument-bank release")
    if any(pattern.search(output_text) for pattern in PUBLIC_DENUNCIATION):
        errors.append("public denunciation / person-level overreach")
    if any(pattern.search(output_text) for pattern in GENERIC_ONTOLOGY_TALK):
        errors.append("generic ontology talk instead of OQ pressure")

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
        "operation": 240,
        "result": 180,
        "Land(B)": 210,
        "R(H,Delta)/kappa": 260,
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
        errors.append(f"operation does not start with allowed OQ verb: {operation_first_line}")
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
    require_patterns(errors, "M9/PM/AS/DW/DA/DS/HK/P7/FPD handoff", output_text, spec.handoff_patterns)

    if not re.search(r"\b(held|released|blocked|bounded|typed|lands|state changes?|restored|narrowed)\b", land, re.IGNORECASE):
        errors.append("Land(B) lacks visible burden-state delta")
    if not re.search(r"\b(held|released|blocked|reread|narrows|eligible|consumes|restored|typed)\b", reread, re.IGNORECASE):
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
        ("ambiguous/missing OQ child mode", "could not infer" in joined or "ambiguous child mode" in joined),
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
        ("missing M9/PM/AS/DW/DA/DS/HK/P7/FPD handoff", "m9/pm/as/dw/da/ds/hk/p7/fpd handoff missing pattern" in joined),
        ("source parade / argument-bank release", "source parade / argument-bank release" in joined),
        ("public denunciation / person-level overreach", "public denunciation / person-level overreach" in joined),
        ("generic ontology talk instead of OQ pressure", "generic ontology talk instead of oq pressure" in joined),
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
        help="Root containing Stage-6.5 OQ child-mode smoke directories.",
    )
    args = parser.parse_args(argv)
    root = args.root if args.root.is_absolute() else (ROOT / args.root)

    if not root.exists():
        print("OQ child-mode execution sample validation: FAIL")
        print(f"- root does not exist: {root}")
        return 1

    sample_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not sample_dirs:
        print("OQ child-mode execution sample validation: FAIL")
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
        print("OQ child-mode execution sample validation: FAIL")
        for directory, errors in all_errors.items():
            print(f"- {directory}: {summarize_errors(errors)}")
        return 1

    print("OQ child-mode execution sample validation: PASS")
    print(f"- root: {root}")
    print(f"- samples checked: {len(sample_dirs)}")
    print(f"- checked modes: {', '.join(sorted(set(checked_modes)))}")
    print("- evidence boundary: local ignored samples; not package/release smoke proof")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
