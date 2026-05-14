#!/usr/bin/env python3
"""Validate local Stage-7.5 MM child-mode execution samples.

This checker is intentionally repo/dev-local. It validates retained ignored
samples under .daee; it is not package/release smoke proof, not a live runner,
and not a universal semantic grader. Its narrow purpose is to reject MM samples
that merely name child modes or print Target/Operation/Result headings without
executing carrier/reproduction pressure, burden-state change, Land(B),
R(H,Delta)/kappa, held-route discipline, and guardrail handoffs.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / ".daee" / "stage7.5-mm-child-live-smokes-20260514"

BANNED_OUTPUT_LEAKAGE = (
    re.compile(r"\bowner-floor applied\b", re.IGNORECASE),
    re.compile(r"\bvalidation passed\b", re.IGNORECASE),
    re.compile(r"\bexecute queued owner\b", re.IGNORECASE),
    re.compile(r"\broute_plan\b", re.IGNORECASE),
    re.compile(r"\bfeatures\.json\b", re.IGNORECASE),
    re.compile(r"\bcheck_execution\b", re.IGNORECASE),
    re.compile(r"\bI applied MM\b", re.IGNORECASE),
)

PACKAGE_OVERCLAIM = re.compile(
    r"\b(?:package/release proof:\s*yes|release-proven|package-bound proof|package smoke proof)\b",
    re.IGNORECASE,
)

GENERIC_OPERATION_START = re.compile(
    r"^\s*(?:address|discuss|engage|consider|respond to|deal with|explain generally|analyze generally)\b",
    re.IGNORECASE,
)

ALLOWED_OPERATION_START = re.compile(
    r"^\s*(?:audit|reconstruct|track|map|classify|distinguish|expose|narrow|hold|re-read)\b",
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
    re.compile(r"\bdenounce(?:d|s)?\s+(?:the person|them|the group)\b", re.IGNORECASE),
)

INTERIOR_ATTRIBUTION = (
    re.compile(r"\b(?:their|his|her|the person's)\s+(?:motive|sincerity|culpability|soul-state)\s+(?:is|are)\b", re.IGNORECASE),
    re.compile(r"\b(?:motive|sincerity|culpability|soul-state)\s*:\s*(?:guilty|corrupt|insincere|known)\b", re.IGNORECASE),
)

GENERIC_MEMETIC_TALK = (
    re.compile(r"\bthis is memetic\b(?!.*(?:carrier|packet|mutation|collapse|dependency|proof|label))", re.IGNORECASE),
    re.compile(r"\bgeneric memetic talk\b", re.IGNORECASE),
    re.compile(r"\bmemetic issue\b.*\btherefore\b.*\bpasses\b", re.IGNORECASE | re.DOTALL),
)


@dataclass(frozen=True)
class SampleSpec:
    child_mode: str
    prompt_needles: tuple[str, ...]
    operation_start: re.Pattern[str]
    target_patterns: tuple[re.Pattern[str], ...]
    operation_patterns: tuple[re.Pattern[str], ...]
    result_patterns: tuple[re.Pattern[str], ...]
    land_patterns: tuple[re.Pattern[str], ...]
    reread_patterns: tuple[re.Pattern[str], ...]
    downstream_patterns: tuple[re.Pattern[str], ...]
    heart_patterns: tuple[re.Pattern[str], ...]
    deformation_patterns: tuple[re.Pattern[str], ...]
    handoff_patterns: tuple[re.Pattern[str], ...]
    wrong_pressure_patterns: tuple[re.Pattern[str], ...]


def pat(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)


SPECS = (
    SampleSpec(
        child_mode="MM-2",
        prompt_needles=("label", "ontology", "proof rule", "shame signal"),
        operation_start=pat(r"^\s*audit\b"),
        target_patterns=(
            pat(r"label as (?:a )?noetic carrier"),
            pat(r"ontology"),
            pat(r"proof(?:-| )denominator|proof rule"),
            pat(r"source-status|authority-order|identity"),
        ),
        operation_patterns=(
            pat(r"audit the label as a noetic carrier"),
            pat(r"ontology.*proof"),
            pat(r"source-status.*authority-order|authority-order.*source-status"),
            pat(r"M9.*PM.*AS.*OQ|M9.*AS.*OQ"),
        ),
        result_patterns=(
            pat(r"label no longer reproduces|stops reproducing"),
            pat(r"reclassified as carrier-pressure|carrier function"),
            pat(r"topical (?:rebuttal|content).*held|content is held"),
        ),
        land_patterns=(
            pat(r"carrier function is typed"),
            pat(r"not merely when the word is defined|defining the word is not enough"),
            pat(r"ontology.*proof(?:-| )denominator.*source-status.*authority-order"),
        ),
        reread_patterns=(
            pat(r"R\(H,Delta\)/kappa"),
            pat(r"M9"),
            pat(r"PM"),
            pat(r"AS"),
            pat(r"OQ"),
            pat(r"FPD|V2"),
            pat(r"collapse-radius|kappa"),
            pat(r"label|carrier"),
        ),
        downstream_patterns=(
            pat(r"Released if live:.*M9.*PM.*AS.*OQ"),
            pat(r"Held:.*topical.*doctrinal.*proof.*public verdict"),
            pat(r"until carrier function lands"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"shame|public prestige|identity-cost|polemical"),
            pat(r"bounded"),
            pat(r"humiliat|public denunciation"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"carrier/reproduction burden"),
            pat(r"not infer motive|culpability|soul-state"),
        ),
        handoff_patterns=(
            pat(r"Source-Worldview / Tribunal Consequence|Handoff"),
            pat(r"imported tribunal|authority-order inversion"),
            pat(r"FPD/V2/PM/AS|FPD.*V2.*PM.*AS"),
        ),
        wrong_pressure_patterns=(
            pat(r"only locally ambiguous"),
            pat(r"M9-LD can settle it"),
        ),
    ),
    SampleSpec(
        child_mode="MM-5",
        prompt_needles=("quote-fragment", "proof", "authority", "premises"),
        operation_start=pat(r"^\s*reconstruct\b"),
        target_patterns=(
            pat(r"proof packet as compression|compressed proof packet"),
            pat(r"hidden premises"),
            pat(r"proof family"),
            pat(r"source-status"),
            pat(r"conclusion scope"),
        ),
        operation_patterns=(
            pat(r"reconstruct the proof packet"),
            pat(r"premise.*inference.*conclusion scope.*source-status.*tribunal"),
            pat(r"PM.*AS|AS.*PM"),
        ),
        result_patterns=(
            pat(r"no longer functions as an opaque warrant"),
            pat(r"held material"),
            pat(r"PM.*AS.*FPD.*M9|PM.*AS.*M9"),
        ),
        land_patterns=(
            pat(r"proof packet is expanded enough to route"),
            pat(r"does not carry the conclusion by itself"),
            pat(r"premise.*inference.*authority function.*conclusion scope"),
        ),
        reread_patterns=(
            pat(r"R\(H,Delta\)/kappa"),
            pat(r"PM"),
            pat(r"AS"),
            pat(r"FPD|V2"),
            pat(r"M9"),
            pat(r"OQ"),
            pat(r"source-status"),
            pat(r"packet|reconstruction"),
        ),
        downstream_patterns=(
            pat(r"Released if live:.*PM.*AS.*FPD/V2.*M9"),
            pat(r"Held:.*proof answer.*source stack.*doctrinal conclusion"),
            pat(r"until reconstruction"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"Prestige|shame"),
            pat(r"bounded"),
            pat(r"authority fatigue|humiliation"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"inherited framework"),
            pat(r"taqlid|zann|genuine shubhah"),
            pat(r"not proof of motive|culpability"),
        ),
        handoff_patterns=(
            pat(r"Source-Worldview / Tribunal Consequence|Handoff"),
            pat(r"proof denominator|external proof denominator|tribunal"),
            pat(r"PM/V2/FPD|FPD/V2/PM"),
        ),
        wrong_pressure_patterns=(
            pat(r"only maps collapse radius"),
            pat(r"dependency radius is the whole operation"),
        ),
    ),
    SampleSpec(
        child_mode="MM-7",
        prompt_needles=("hidden premise", "wording changes", "same burden", "same proof standard"),
        operation_start=pat(r"^\s*track\b"),
        target_patterns=(
            pat(r"mutation rule"),
            pat(r"old carrier"),
            pat(r"new formulation|new wording"),
            pat(r"preserved function|proof standard"),
            pat(r"regenerated downstream burden"),
        ),
        operation_patterns=(
            pat(r"track mutation after challenge"),
            pat(r"old carrier.*new (?:wording|formulation).*preserved"),
            pat(r"downstream burden.*regenerated|regenerated downstream burden"),
            pat(r"NewB|same-burden"),
        ),
        result_patterns=(
            pat(r"cannot escape correction by swapping slogans"),
            pat(r"held as a possible mutation"),
            pat(r"genuinely new premises|same burden"),
        ),
        land_patterns=(
            pat(r"mutation is typed as same-function survival or a genuinely new burden"),
            pat(r"wording changed does not by itself license"),
            pat(r"new topical answer"),
        ),
        reread_patterns=(
            pat(r"R\(H,Delta\)/kappa"),
            pat(r"NewB"),
            pat(r"P7/DW|DW/P7"),
            pat(r"M5"),
            pat(r"PM"),
            pat(r"AS"),
            pat(r"M9"),
            pat(r"collapse radius|kappa"),
            pat(r"same proof standard|downstream burden"),
        ),
        downstream_patterns=(
            pat(r"Released if live:.*DW/P7.*M5.*PM.*AS.*M9"),
            pat(r"Held:.*next topical answer"),
            pat(r"same-function survival versus NewB"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"identity-performance|anxiety|polemical"),
            pat(r"bounded"),
            pat(r"avoid escalation|public denunciation"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"zann|taqlid|inherited framework|hawa/gharad|stable shubhah"),
            pat(r"does not infer motive|sincerity|culpability|soul-state"),
        ),
        handoff_patterns=(
            pat(r"Source-Worldview / Tribunal Consequence|Handoff"),
            pat(r"preserves the same tribunal"),
            pat(r"FPD/V2/PM|FPD.*V2.*PM"),
        ),
        wrong_pressure_patterns=(
            pat(r"new claim is genuinely distinct"),
        ),
    ),
    SampleSpec(
        child_mode="MM-8",
        prompt_needles=("loaded assumption", "downstream claims", "node", "answer every downstream topic"),
        operation_start=pat(r"^\s*map\b"),
        target_patterns=(
            pat(r"loaded assumption"),
            pat(r"downstream dependency set"),
            pat(r"immediate routes"),
            pat(r"distant routes|downstream routes"),
        ),
        operation_patterns=(
            pat(r"map collapse radius"),
            pat(r"immediate and downstream routes"),
            pat(r"depend on the node"),
            pat(r"bind reread to that dependency set"),
        ),
        result_patterns=(
            pat(r"Downstream claims are no longer answered or left live silently"),
            pat(r"marked held"),
            pat(r"which routes remain live"),
            pat(r"STOP.*HOLD.*PARTIAL.*RECURSE|HOLD.*PARTIAL.*RECURSE"),
        ),
        land_patterns=(
            pat(r"node and dependency radius are typed"),
            pat(r"Clearing the node is not the same as answering every dependent topic"),
            pat(r"downstream routes still deserve release"),
        ),
        reread_patterns=(
            pat(r"R\(H,Delta\)/kappa"),
            pat(r"mapped radius|dependency radius"),
            pat(r"all dependent claims/routes"),
            pat(r"STOP"),
            pat(r"HOLD"),
            pat(r"PARTIAL"),
            pat(r"RECURSE"),
            pat(r"NewB"),
        ),
        downstream_patterns=(
            pat(r"Released if live:.*M9.*PM.*AS.*DW/P7.*OQ.*DA/DS/HK"),
            pat(r"Held:.*downstream topic answers"),
            pat(r"dependency map and reread permit release"),
        ),
        heart_patterns=(
            pat(r"Heart/Register Consequence"),
            pat(r"overload|anxiety"),
            pat(r"bounded|PARTIAL"),
        ),
        deformation_patterns=(
            pat(r"M5/V1 Deformation Release Condition"),
            pat(r"topic tour|argument dump|proof pile"),
            pat(r"DW/P7"),
        ),
        handoff_patterns=(
            pat(r"Source-Worldview / Tribunal Consequence|Handoff"),
            pat(r"imported tribunal"),
            pat(r"FPD/V2/PM|FPD.*V2.*PM"),
            pat(r"M9.*AS.*OQ.*DA/DS/HK|M9.*OQ.*DA/DS/HK"),
        ),
        wrong_pressure_patterns=(
            pat(r"only reconstructs a proof packet"),
            pat(r"proof packet is the whole operation"),
        ),
    ),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, title: str) -> str:
    match = re.search(rf"(?ims)^#+\s*{re.escape(title)}\s*$\n(?P<body>.*?)(?=^#+\s|\Z)", text)
    return match.group("body").strip() if match else ""


def operation_body(text: str) -> str:
    body = section(text, "Operation")
    if body:
        return body
    match = re.search(r"(?im)^\s*operation\s*:\s*(.+)$", text)
    return match.group(1).strip() if match else ""


def all_match(patterns: tuple[re.Pattern[str], ...], text: str) -> bool:
    return all(pattern.search(text) for pattern in patterns)


def infer_spec(input_text: str, combined: str) -> tuple[SampleSpec | None, list[str]]:
    matches: list[SampleSpec] = []
    lower_input = input_text.lower()
    for spec in SPECS:
        label_hit = re.search(rf"\b{re.escape(spec.child_mode)}\b", combined, re.IGNORECASE)
        prompt_hit = all(needle.lower() in lower_input for needle in spec.prompt_needles)
        if label_hit or prompt_hit:
            matches.append(spec)
    if len(matches) == 1:
        return matches[0], []
    if not matches:
        return None, ["ambiguous or missing MM child mode: no child mode inferred"]
    return None, [f"ambiguous or missing MM child mode: {', '.join(spec.child_mode for spec in matches)}"]


def check_forbidden(output_text: str) -> list[str]:
    errors: list[str] = []
    for pattern in BANNED_OUTPUT_LEAKAGE:
        if pattern.search(output_text):
            errors.append(f"route/check harness leakage: {pattern.pattern}")
    if PACKAGE_OVERCLAIM.search(output_text):
        errors.append("package/release proof overclaim")
    if any(pattern.search(output_text) for pattern in SOURCE_PARADE):
        errors.append("source parade or argument-bank release")
    if any(pattern.search(output_text) for pattern in PUBLIC_DENUNCIATION):
        errors.append("public denunciation / person-level overreach")
    if any(pattern.search(output_text) for pattern in INTERIOR_ATTRIBUTION):
        errors.append("motive/sincerity/culpability/soul-state attribution")
    if any(pattern.search(output_text) for pattern in GENERIC_MEMETIC_TALK):
        errors.append("generic memetic talk instead of carrier/reproduction operation")
    return errors


def check_sample(sample_dir: Path) -> tuple[str, str | None, list[str]]:
    errors: list[str] = []
    missing = [name for name in ("input.md", "output.md", "trace.md", "verdict.md") if not (sample_dir / name).is_file()]
    if missing:
        return sample_dir.name, None, [f"missing required files: {', '.join(missing)}"]

    input_text = read_text(sample_dir / "input.md")
    output_text = read_text(sample_dir / "output.md")
    trace_text = read_text(sample_dir / "trace.md")
    verdict_text = read_text(sample_dir / "verdict.md")
    combined = "\n".join((input_text, output_text, trace_text, verdict_text))

    spec, mode_errors = infer_spec(input_text, combined)
    if mode_errors:
        return sample_dir.name, None, mode_errors
    assert spec is not None

    errors.extend(check_forbidden(output_text))

    op = operation_body(output_text)
    if not op:
        errors.append("missing operation section")
    else:
        first_line = next((line.strip() for line in op.splitlines() if line.strip()), "")
        if GENERIC_OPERATION_START.search(first_line):
            errors.append("generic operation verb")
        if not spec.operation_start.search(first_line):
            errors.append("operation does not start with allowed child-specific verb")

    if not section(output_text, "Target"):
        errors.append("missing case-specific target")
    elif not all_match(spec.target_patterns, section(output_text, "Target") + "\n" + output_text):
        errors.append("missing case-specific target pressure")

    if op and not all_match(spec.operation_patterns, op + "\n" + output_text):
        errors.append("missing child-specific carrier/reproduction operation")

    result = section(output_text, "Result")
    if not result:
        errors.append("missing result/state change")
    elif not all_match(spec.result_patterns, result + "\n" + output_text):
        errors.append("missing burden-state change")

    land = section(output_text, "Land(B)")
    if not land:
        errors.append("missing Land(B)")
    elif re.fullmatch(r"(?is)\s*(?:Land\(B\):\s*)?burden lands\.?\s*", land):
        errors.append("unsupported Land(B)")
    elif not all_match(spec.land_patterns, land + "\n" + output_text):
        errors.append("unsupported Land(B)")

    reread = section(output_text, "R(H,Delta)/kappa")
    if not reread:
        errors.append("missing R(H,Delta)/kappa")
    elif not all_match(spec.reread_patterns, reread + "\n" + output_text):
        errors.append("R(H,Delta)/kappa does not consume result")

    if not all_match(spec.downstream_patterns, output_text):
        errors.append("missing downstream held/released route")
    if not all_match(spec.heart_patterns, output_text):
        errors.append("missing heart/register consequence")
    if not all_match(spec.deformation_patterns, output_text):
        errors.append("missing M5/V1 deformation release condition")
    if not all_match(spec.handoff_patterns, output_text):
        errors.append("missing M9/PM/AS/DW/OQ/DA/DS/HK/P7/FPD handoff when live")
    if any(pattern.search(output_text) for pattern in spec.wrong_pressure_patterns):
        errors.append("wrong child pressure")

    return sample_dir.name, spec.child_mode, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="local .daee sample root")
    args = parser.parse_args()

    root = args.root if args.root.is_absolute() else ROOT / args.root
    if not root.exists():
        print(f"FAIL: root not found: {root}")
        return 1

    sample_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not sample_dirs:
        print(f"FAIL: no sample directories found under {root}")
        return 1

    failures: list[str] = []
    modes: list[str] = []
    for sample_dir in sample_dirs:
        name, mode, errors = check_sample(sample_dir)
        if mode:
            modes.append(mode)
        if errors:
            failures.append(f"{name}: " + "; ".join(errors))

    if failures:
        print(f"FAIL: {len(failures)} of {len(sample_dirs)} samples failed")
        for failure in failures:
            print(f"- {failure}")
        return 1

    unique_modes = sorted(set(modes))
    expected_modes = ["MM-2", "MM-5", "MM-7", "MM-8"]
    if unique_modes != expected_modes:
        print(f"FAIL: expected modes {expected_modes}, got {unique_modes}")
        return 1
    print(f"PASS: {len(sample_dirs)} samples checked (modes: {', '.join(unique_modes)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
