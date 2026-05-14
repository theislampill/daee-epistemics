#!/usr/bin/env python3
"""Validate local Stage-4.5 DW/doubt-ecology child-mode samples.

This checker is intentionally repo/dev-local. It validates retained ignored
samples under .daee; it is not package/release smoke proof, not a live runner,
and not a universal semantic grader. Its narrow purpose is to reject DW samples
that merely name child modes or print Target/Operation/Result headings without
executing doubt-function pressure, stop/hold release posture, and the
heart/M5/P7 plus FPD/PM/M9/AS handoff guardrails.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / ".daee" / "stage4.5-dw-child-live-smokes-20260514"

BANNED_OUTPUT_LEAKAGE = (
    re.compile(r"\bowner-floor applied\b", re.IGNORECASE),
    re.compile(r"\bvalidation passed\b", re.IGNORECASE),
    re.compile(r"\bexecute queued owner\b", re.IGNORECASE),
    re.compile(r"\broute_plan\b", re.IGNORECASE),
    re.compile(r"\bfeatures\.json\b", re.IGNORECASE),
    re.compile(r"\bcheck_execution\b", re.IGNORECASE),
    re.compile(r"\bI applied DW\b", re.IGNORECASE),
)

GENERIC_OPERATION_START = re.compile(
    r"^\s*(?:address|discuss|engage|consider|respond to|deal with|explain the issue|analyze generally)\b",
    re.IGNORECASE,
)

ALLOWED_OPERATION_START = re.compile(
    r"^\s*(?:distinguish|audit|classify|narrow|hold|stop|bound|re-read|clear|refuse escalation of)\b",
    re.IGNORECASE,
)

PACKAGE_OVERCLAIM = re.compile(
    r"\b(?:package/release proof:\s*yes|release-proven|package-bound proof|package smoke proof)\b",
    re.IGNORECASE,
)

PROOF_DUMP = (
    re.compile(r"\bproof dump:\s*(?:released|performed|provided|yes)\b", re.IGNORECASE),
    re.compile(r"\bproof list:\s*(?:released|provided|expanded|yes)\b", re.IGNORECASE),
    re.compile(r"(?im)^\s*(?:1\.|-\s*)\s*Proof\s+\d+\s*:", re.IGNORECASE),
)

SOURCE_PARADE = (
    re.compile(r"\bsource parade:\s*(?:released|performed|provided|yes)\b", re.IGNORECASE),
    re.compile(r"\bsource dump:\s*(?:released|performed|provided|yes)\b", re.IGNORECASE),
    re.compile(r"\bargument bank\b(?!.*(?:blocked|held|refused|avoid))", re.IGNORECASE),
    re.compile(r"(?im)^\s*-\s*(?:name|quote)\s*\d+\s*:", re.IGNORECASE),
)

PATHOLOGIZE_STABLE_OBJECTION = (
    re.compile(r"\bstable objection\b.*\b(?:pathology|pathological|wiswas only|not real)\b", re.IGNORECASE),
    re.compile(r"\btherefore\s+(?:this|the objection)\s+is\s+(?:just|only)\s+(?:wiswas|compulsion|anxiety)\b", re.IGNORECASE),
)

CONTENT_ESCALATION = (
    re.compile(r"\bnow give (?:another|more|a full) proof", re.IGNORECASE),
    re.compile(r"\brelease full technical answer\b", re.IGNORECASE),
    re.compile(r"\bcontinue with more content\b", re.IGNORECASE),
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
    p7_patterns: tuple[re.Pattern[str], ...]
    handoff_patterns: tuple[re.Pattern[str], ...]


def pat(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)


SPECS = (
    SampleSpec(
        child_mode="DW-1",
        prompt_needles=("keeps saying they have a doubt", "question keeps mutating", "no stable premise"),
        target_patterns=(
            pat(r"doubt function"),
            pat(r"release posture"),
            pat(r"stable premise"),
            pat(r"mutation|mutating"),
        ),
        operation_start=pat(r"^\s*distinguish\b"),
        operation_patterns=(
            pat(r"serious shubhah"),
            pat(r"ideological skepticism"),
            pat(r"compulsive doubt"),
            pat(r"underdetermined register"),
            pat(r"before content release"),
        ),
        result_patterns=(
            pat(r"content route.*held|content route.*bounded|held/bounded|bounded rather than released"),
            pat(r"stable premise"),
            pat(r"proof-method.*held|PM.*held"),
        ),
        land_patterns=(
            pat(r"burden lands on typing the doubt function"),
            pat(r"content release depends|content no longer releases"),
            pat(r'"doubt" was treated|doubt-language appears'),
            pat(r"state one stable premise|stable premise"),
        ),
        reread_patterns=(
            pat(r"P7"),
            pat(r"PM"),
            pat(r"M9"),
            pat(r"V2|FPD"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released:.*bounded reassurance|bounded reassurance"),
            pat(r"Held:.*proof-stacking|proof-stacking.*held"),
            pat(r"source parade"),
            pat(r"doctrinal content|doctrinal sprawl"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"anxiety|wiswas|overcomplexity"),
            pat(r"hold|bounded|PARTIAL"),
            pat(r"not.*pathology|not.*sincere|does not pathologize|should not say"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"shubhah"),
            pat(r"zann|taqlid|hawa/gharad|inherited framework|ada"),
            pat(r"deformation label does not count|label does not count"),
        ),
        p7_patterns=(
            pat(r"P7"),
            pat(r"HOLD|PARTIAL"),
            pat(r"content.*held|held content"),
        ),
        handoff_patterns=(
            pat(r"FPD/V2/PM/M9/AS Handoff"),
            pat(r"PM"),
            pat(r"M9"),
            pat(r"AS"),
            pat(r"FPD/V2|V2/FPD"),
        ),
    ),
    SampleSpec(
        child_mode="DW-2",
        prompt_needles=("too simple", "technical proof", "live issue has not changed"),
        target_patterns=(
            pat(r"complexity pressure"),
            pat(r"proof-stacking loop"),
            pat(r"live issue"),
            pat(r"technical proof"),
        ),
        operation_start=pat(r"^\s*audit\b"),
        operation_patterns=(
            pat(r"added complexity"),
            pat(r"restores sound reason"),
            pat(r"feeds deformation"),
            pat(r"stable burden|live burden"),
        ),
        result_patterns=(
            pat(r"narrowed to the live burden"),
            pat(r"unnecessary proof expansion is held"),
            pat(r"technical expansion\s+must\s+earn release"),
        ),
        land_patterns=(
            pat(r"overcomplexity no longer functions as authority or rigor"),
            pat(r"burden now lands on the complexity demand"),
            pat(r"technicality\s+is\s+allowed\s+only\s+if"),
        ),
        reread_patterns=(
            pat(r"PM"),
            pat(r"V2|FPD"),
            pat(r"P7"),
            pat(r"DW-1"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released:.*burden narrowing|burden narrowing"),
            pat(r"Held:.*proof dumps|proof dumps"),
            pat(r"technical excursions"),
            pat(r"source stacks"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"anxiety|overcomplexity|authority-fatigue|compulsion"),
            pat(r"bound|bounded|blocks proof-dumping"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"zann|inherited framework|ada|argument-absorbent"),
            pat(r"before further (?:proof-method|PM) release"),
        ),
        p7_patterns=(
            pat(r"P7 Stop/Hold/Partial Consequence"),
            pat(r"HOLD"),
            pat(r"PARTIAL"),
            pat(r"STOP"),
        ),
        handoff_patterns=(
            pat(r"FPD/V2/PM/M9/AS Handoff"),
            pat(r"PM"),
            pat(r"FPD/V2|V2/FPD"),
            pat(r"M9"),
            pat(r"AS"),
        ),
    ),
    SampleSpec(
        child_mode="DW-3",
        prompt_needles=("absorbed as new material", "objection-generation", "another proof list"),
        target_patterns=(
            pat(r"escalation loop"),
            pat(r"next-content release"),
            pat(r"objection material|objection-generation"),
            pat(r"proof list"),
        ),
        operation_start=pat(r"^\s*stop\b"),
        operation_patterns=(
            pat(r"content escalation"),
            pat(r"more answer now would feed"),
            pat(r"hold or PARTIAL"),
            pat(r"downstream route"),
        ),
        result_patterns=(
            pat(r"refuses proof/content sprawl"),
            pat(r"live next burden as held"),
            pat(r"proof-list request.*no longer|request for \"another proof list\".*no longer"),
        ),
        land_patterns=(
            pat(r"escalation pressure lands as stop/hold discipline"),
            pat(r"give me another proof\s+list"),
            pat(r"test one thing|one point"),
        ),
        reread_patterns=(
            pat(r"P7"),
            pat(r"STOP"),
            pat(r"HOLD"),
            pat(r"PARTIAL"),
            pat(r"PM"),
            pat(r"M9"),
            pat(r"AS"),
            pat(r"FPD/V2|V2/FPD"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released:.*P7 stop/hold|P7 stop/hold"),
            pat(r"Held:.*proof lists|proof lists"),
            pat(r"source parade"),
            pat(r"speculative theology"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"anxiety|compulsion|stimulation|identity-performance"),
            pat(r"protective|non-humiliating|not accuse"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"argument-absorbent"),
            pat(r"zann|hawa/gharad|identity-performance|shubhah"),
        ),
        p7_patterns=(
            pat(r"P7 Stop/Hold/Partial Consequence"),
            pat(r"STOP"),
            pat(r"HOLD"),
            pat(r"PARTIAL"),
            pat(r"not licensed unless"),
        ),
        handoff_patterns=(
            pat(r"FPD/V2/PM/M9/AS Handoff"),
            pat(r"PM"),
            pat(r"M9"),
            pat(r"AS"),
            pat(r"FPD/V2|V2/FPD"),
        ),
    ),
    SampleSpec(
        child_mode="DW-6",
        prompt_needles=("needs reassurance", "full technical answer", "intensify the cycle"),
        target_patterns=(
            pat(r"reassurance boundary"),
            pat(r"held material"),
            pat(r"full technical content"),
            pat(r"release later"),
        ),
        operation_start=pat(r"^\s*bound\b"),
        operation_patterns=(
            pat(r"reassurance"),
            pat(r"holding unreleased proof/content|hold unreleased proof/content"),
            pat(r"naming what would\s+release"),
        ),
        result_patterns=(
            pat(r"Confidence is restored"),
            pat(r"without feeding content escalation"),
            pat(r"technical proof stack remains held"),
        ),
        land_patterns=(
            pat(r"reassurance lands as bounded orientation"),
            pat(r"not argument completion"),
            pat(r"safe orientation"),
        ),
        reread_patterns=(
            pat(r"P7"),
            pat(r"HOLD"),
            pat(r"PARTIAL"),
            pat(r"STOP"),
            pat(r"PM"),
            pat(r"M9"),
            pat(r"AS"),
            pat(r"FPD/V2|V2/FPD"),
            pat(r"kappa|collapse radius"),
        ),
        downstream_patterns=(
            pat(r"Released:.*bounded reassurance|bounded reassurance"),
            pat(r"Held:.*full technical proof|full technical proof"),
            pat(r"source parade"),
            pat(r"speculative theology"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"anxiety|wiswas|grief|identity-cost"),
            pat(r"warm|brief|non-escalating|bounded"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"wiswas|anxiety"),
            pat(r"zann|ada|shubhah|argument-absorbent"),
        ),
        p7_patterns=(
            pat(r"P7 Stop/Hold/Partial Consequence"),
            pat(r"HOLD"),
            pat(r"PARTIAL"),
            pat(r"STOP"),
            pat(r"RECURSE"),
        ),
        handoff_patterns=(
            pat(r"FPD/V2/PM/M9/AS Handoff"),
            pat(r"PM"),
            pat(r"M9"),
            pat(r"AS"),
            pat(r"FPD/V2|V2/FPD"),
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
    name_modes = sorted(set(re.findall(r"\bDW-[1236]\b", sample_root.name)))
    if len(name_modes) == 1:
        return SPEC_BY_MODE[name_modes[0]], []
    if len(name_modes) > 1:
        return None, [f"ambiguous DW child mode references in directory: {', '.join(name_modes)}"]

    verdict_match = re.search(r"(?im)^\s*-\s*child mode:\s*(DW-[1236])\b", verdict_text)
    if verdict_match:
        return SPEC_BY_MODE[verdict_match.group(1)], []

    output_modes = sorted(set(re.findall(r"(?im)^\s*(?:#.*\b|Local anchor:\s*)(DW-[1236])\b", output_text)))
    if len(output_modes) == 1:
        return SPEC_BY_MODE[output_modes[0]], []
    if not output_modes:
        return None, ["could not infer DW child mode from directory, verdict, or output"]
    return None, [f"ambiguous DW child mode references in output: {', '.join(output_modes)}"]


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

    proof_dump = has_forbidden(PROOF_DUMP, output_text)
    if proof_dump:
        errors.append(f"proof-dump/content escalation release: {proof_dump.pattern}")

    source_parade = has_forbidden(SOURCE_PARADE, output_text)
    if source_parade:
        errors.append(f"source parade / argument-bank release: {source_parade.pattern}")

    pathologizing = has_forbidden(PATHOLOGIZE_STABLE_OBJECTION, output_text)
    if pathologizing:
        errors.append(f"pathologizing stable intellectual objection: {pathologizing.pattern}")

    escalation = has_forbidden(CONTENT_ESCALATION, output_text)
    if escalation:
        errors.append(f"content escalation despite stop/hold pressure: {escalation.pattern}")

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
        (
            r"(?im)^##\s*Heart/Register",
            r"(?im)^##\s*M5/V1",
            r"(?im)^##\s*P7",
            r"(?im)^##\s*FPD/V2",
            r"(?im)^##\s*Downstream",
        ),
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
        "operation": 260,
        "result": 180,
        "Land(B)": 220,
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
        errors.append(f"operation does not start with allowed DW verb: {operation_first_line}")
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
    require_patterns(errors, "P7 stop/hold/partial consequence", output_text, spec.p7_patterns)
    require_patterns(errors, "FPD/V2/PM/M9/AS handoff", output_text, spec.handoff_patterns)

    if not re.search(r"\b(held|released|bounded|partial|stop|hold|narrowed|typed|lands|state changes?)\b", land, re.IGNORECASE):
        errors.append("Land(B) lacks visible burden-state delta")
    if not re.search(r"\b(held|released|bounded|reread|contracts|narrows|constrained|eligible|licenses)\b", reread, re.IGNORECASE):
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
        ("ambiguous/missing DW child mode", "could not infer" in joined or "ambiguous dw child mode" in joined),
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
        ("missing P7 stop/hold/partial consequence", "p7 stop/hold/partial consequence missing pattern" in joined),
        ("missing FPD/V2/PM/M9/AS handoff", "fpd/v2/pm/m9/as handoff missing pattern" in joined),
        ("proof-dump/content escalation release", "proof-dump/content escalation release" in joined or "content escalation despite stop/hold pressure" in joined),
        ("source parade / argument-bank release", "source parade / argument-bank release" in joined),
        ("pathologizing stable intellectual objection", "pathologizing stable intellectual objection" in joined),
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
        help="Root containing Stage-4.5 DW/doubt-ecology child-mode smoke directories.",
    )
    args = parser.parse_args(argv)
    root = args.root if args.root.is_absolute() else (ROOT / args.root)

    if not root.exists():
        print("DW child-mode execution sample validation: FAIL")
        print(f"- root does not exist: {root}")
        return 1

    sample_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not sample_dirs:
        print("DW child-mode execution sample validation: FAIL")
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
        print("DW child-mode execution sample validation: FAIL")
        for directory, errors in all_errors.items():
            print(f"- {directory}: {summarize_errors(errors)}")
        return 1

    print("DW child-mode execution sample validation: PASS")
    print(f"- root: {root}")
    print(f"- samples checked: {len(sample_dirs)}")
    print(f"- checked modes: {', '.join(sorted(set(checked_modes)))}")
    print("- evidence boundary: local ignored samples; not package/release smoke proof")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
