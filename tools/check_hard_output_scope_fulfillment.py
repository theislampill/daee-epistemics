#!/usr/bin/env python3
"""Check hard-output prompt-scope fulfillment for retained/exact smokes.

This checker is deliberately prose-facing. It does not replace the structural
MRP, field_witness, Grapher, or convergence validators. Its job is narrower:
make sure a high-mass governed output visibly answers the actual prompt family
instead of merely rendering proof scaffolding or generic advice.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "hard-output-scope-fulfillment"


@dataclass(frozen=True)
class ScopeGroup:
    label: str
    patterns: tuple[re.Pattern[str], ...]


@dataclass(frozen=True)
class CaseSpec:
    aliases: tuple[str, ...]
    groups: tuple[ScopeGroup, ...]


def rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


CASE_SPECS: dict[str, CaseSpec] = {}


def register(name: str, aliases: tuple[str, ...], groups: tuple[ScopeGroup, ...]) -> None:
    spec = CaseSpec(aliases=(name, *aliases), groups=groups)
    for alias in spec.aliases:
        CASE_SPECS[alias] = spec


register(
    "tst-lillard",
    ("tst", "lillard", "tst-eternal-punishment"),
    (
        ScopeGroup("named TST/Lillard source context", (rx(r"\bLillard\b"), rx(r"\bSatanist Temple\b|\bTST\b|\bSatanist\b"))),
        ScopeGroup("eternal punishment / fire pressure", (rx(r"\beternal\b"), rx(r"\b(?:hell|hellfire|lake of fire|Jahannam|punishment)\b"))),
        ScopeGroup("bare non-belief / accountability compression", (rx(r"\bnon[- ]belief\b|\bkufr\b"), rx(r"\baccountability\b|\bhujjah\b|\bproof\b|\bculpability\b"))),
        ScopeGroup("convincing-every-person hiddenness pressure", (rx(r"\bconvinc(?:e|ing)\b"), rx(r"\bguidance\b|\bcoerc(?:e|ive|ion)\b|\bhiddenness\b"))),
        ScopeGroup("moral-protest adjectives", (rx(r"\bcruel\b|\bcruelty\b"), rx(r"\binhumane\b|\bkind\b|\bgenerous\b|\bworship[- ]worth(?:y|iness)\b"))),
        ScopeGroup("moral tribunal / source-order work", (rx(r"\bmoral tribunal\b|\btribunal\b"), rx(r"\bsource[- ]order\b|\bsource status\b|\bimported\b|\bforeign premise\b"))),
        ScopeGroup("mercy/justice restoration", (rx(r"\bmercy\b|\bmerciful\b"), rx(r"\bjustice\b|\bjust\b|\bwrong(?:s|ed)? no one\b"))),
    ),
)

register(
    "secularism",
    ("refute-secularism", "secularism-exact"),
    (
        ScopeGroup("secularism target", (rx(r"\bsecularism\b|\bsecular\b"),)),
        ScopeGroup("neutrality / public reason claim", (rx(r"\bneutral(?:ity)?\b|\bpublic reason\b|\bpublic-neutral\b"),)),
        ScopeGroup("source-order / revelation boundary", (rx(r"\bsource[- ]order\b|\bsource status\b"), rx(r"\brevelation\b|\bprivate preference\b|\bprivate\b"))),
        ScopeGroup("ontology / reduction pressure", (rx(r"\bontology\b|\bontological\b|\bmatter\b|\blaws?\b|\bnature\b|\bmaterial\b"),)),
        ScopeGroup("moral or rational normativity", (rx(r"\bmoral\b|\bnormativity\b|\breason\b|\brational\b"),)),
        ScopeGroup("tawhid / fitrah / God restoration", (rx(r"\btawhid\b|\bfitrah\b|\bGod\b|\bAllah\b"),)),
        ScopeGroup("bounded closure / reopen condition", (rx(r"\breopen\b|\bbounded\b|\bstop condition\b|\bscope boundary\b"),)),
    ),
)

register(
    "trinitarian-j173",
    ("trinitarian", "john17", "john-17-3", "j173"),
    (
        ScopeGroup("John 17:3 target", (rx(r"\bJohn\s+17:3\b"),)),
        ScopeGroup("Father as only true God", (rx(r"\bFather\b"), rx(r"\bonly true God\b"))),
        ScopeGroup("Jesus/Son distinction", (rx(r"\bJesus\b|\bSon\b"), rx(r"\bsent\b|\bsender\b|\bChrist\b"))),
        ScopeGroup("Trinity / Trinitarian model", (rx(r"\bTrinity\b|\bTrinitarian\b"),)),
        ScopeGroup("only-placement / arithmetic analogy", (rx(r"\bonly\b"), rx(r"\b2\s*\+\s*2\b|\barithmetic\b|\banalogy\b"))),
        ScopeGroup("cross-text proof stack", (rx(r"\bJohn\s+1:1\b"), rx(r"\b1\s+John\s+5:20\b"))),
        ScopeGroup("eternal-life entailment", (rx(r"\beternal life\b"), rx(r"\bentail(?:ment)?\b|\bknowing Jesus\b|\bknowing\b"))),
        ScopeGroup("person/nature predication", (rx(r"\bperson\b|\bnature\b"), rx(r"\bpredicat(?:e|ion)\b|\bcategory\b"))),
        ScopeGroup("source-order / hidden support", (rx(r"\bsource[- ]order\b|\bproof[- ]stack\b"), rx(r"\bhidden support\b|\bsacred doctrine\b"))),
        ScopeGroup("DO-12 attribute-precision execution", (rx(r"\bdo-attribute-precision\b|\battribute(?:s| precision)?\b"), rx(r"\bperson/nature\b|\bperson\b.*\bnature\b|\bnature\b.*\bperson\b"))),
        ScopeGroup("identity/counting pressure", (rx(r"\bone\b|\bthree\b|\bcount(?:ing)?\b"), rx(r"\bis God\b|\bGod-language\b|\btrue God\b"))),
        ScopeGroup("Trinitarian model-family discriminator", (rx(r"\bmodel\b"), rx(r"\bLatin\b|\bSocial\b|\brelative identity\b|\bstrict identity\b|\bmodalism\b|\btritheism\b|\bmissing discriminator\b|\bmodel family\b"))),
        ScopeGroup("worship/lordship referent", (rx(r"\bworship\b|\blordship\b|\bworship-status\b|\bLord\b"),)),
    ),
)


def visible_body(text: str) -> str:
    markers = ["\nfield_witness", "\n```json", "\n{", "\nClosure witness"]
    cut = len(text)
    for marker in markers:
        idx = text.find(marker)
        if idx > 0:
            cut = min(cut, idx)
    return text[:cut]


def count_burdens(text: str) -> int:
    return len(re.findall(r"(?im)^\s*##\s+Burden\s+\d+\b", text))


def count_acts(text: str) -> int:
    return len(re.findall(r"\u27e6ACT\s+", text))


def count_mrp(text: str) -> int:
    return len(re.findall(r"(?i)\bMRP\s*\(|MRP route result type|MRP resultant", text))


def check_case(case: str, input_path: Path | None, output_path: Path, args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    spec = CASE_SPECS.get(case)
    if spec is None:
        errors.append(f"unknown case '{case}'")
        return errors

    text = output_path.read_text(encoding="utf-8")
    body = visible_body(text)
    input_text = input_path.read_text(encoding="utf-8") if input_path else ""

    if args.min_bytes is not None and len(text.encode("utf-8")) < args.min_bytes:
        errors.append(f"{output_path}: output is below hard-output byte floor: {len(text.encode('utf-8'))} < {args.min_bytes}")
    if count_burdens(text) < args.min_burdens:
        errors.append(f"{output_path}: burden count below floor: {count_burdens(text)} < {args.min_burdens}")
    if count_acts(text) < args.min_submoves:
        errors.append(f"{output_path}: ACT/submove count below floor: {count_acts(text)} < {args.min_submoves}")
    if count_mrp(text) < args.min_mrp:
        errors.append(f"{output_path}: MRP evidence count below floor: {count_mrp(text)} < {args.min_mrp}")

    required_visible = {
        "Target field": r"(?im)^\s*Target\s*:",
        "Operation field": r"(?im)^\s*Operation\s*:",
        "Result/state-change field": r"(?im)^\s*(?:Result(?:/state-change)?|Result)\s*:",
        "Contribution-to-Land field": r"(?im)^\s*Contribution-to-Land",
        "Restorative Response": r"(?im)^\s*(?:#+\s*)?(?:Final\s+)?Restorative Response\s*$",
        "Closing Formulation": r"(?im)^\s*(?:#+\s*)?(?:Final\s+)?Closing Formulation\s*$",
    }
    for label, pattern in required_visible.items():
        if not re.search(pattern, body):
            errors.append(f"{output_path}: visible body missing {label}")

    required_anywhere = {
        "field_witness": r"field_witness",
        "formal_reread_states": r"formal_reread_states",
        "owner_activations": r"owner_activations",
        "normalized_activation_record": r"normalized_activation_record",
    }
    for label, pattern in required_anywhere.items():
        if not re.search(pattern, text):
            errors.append(f"{output_path}: output missing {label}")

    for group in spec.groups:
        if not all(pattern.search(body) for pattern in group.patterns):
            errors.append(f"{output_path}: visible prose does not satisfy scope group: {group.label}")

    if input_text:
        lower_body = body.lower()
        meaningful = [
            token
            for token in re.findall(r"[A-Za-z][A-Za-z0-9'+-]{4,}", input_text)
            if token.lower() not in {"daee-epistemics", "refute", "reply", "from", "this", "that", "with", "would", "could", "should", "someone", "person"}
        ]
        hits = sum(1 for token in set(meaningful) if token.lower() in lower_body)
        if meaningful and hits < min(5, len(set(meaningful))):
            errors.append(f"{output_path}: visible prose has too few direct prompt-anchor echoes: {hits}")

    return errors


def fixture_case(path: Path) -> str | None:
    match = re.search(r"<!--\s*case:\s*([A-Za-z0-9_.-]+)\s*-->", path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def run_fixtures() -> list[str]:
    errors: list[str] = []
    valid = sorted((FIXTURE_ROOT / "valid").glob("*.md"))
    invalid = sorted((FIXTURE_ROOT / "invalid").glob("*.md"))
    fixture_args = argparse.Namespace(min_bytes=None, min_burdens=1, min_submoves=1, min_mrp=1)
    for path in valid:
        case = fixture_case(path)
        if not case:
            errors.append(f"{path}: missing <!-- case: ... --> marker")
            continue
        found = check_case(case, None, path, fixture_args)
        errors.extend(found)
    for path in invalid:
        case = fixture_case(path)
        if not case:
            errors.append(f"{path}: missing <!-- case: ... --> marker")
            continue
        found = check_case(case, None, path, fixture_args)
        if not found:
            errors.append(f"{path}: invalid fixture unexpectedly passed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(CASE_SPECS), help="prompt family to check")
    parser.add_argument("--input", type=Path, help="input prompt text for direct prompt-anchor echo checks")
    parser.add_argument("--output", type=Path, help="governed output to check")
    parser.add_argument("--min-bytes", type=int, default=None, help="optional live hard-output byte floor")
    parser.add_argument("--min-burdens", type=int, default=3)
    parser.add_argument("--min-submoves", type=int, default=8)
    parser.add_argument("--min-mrp", type=int, default=3)
    args = parser.parse_args()

    errors: list[str] = []
    if args.case or args.output or args.input:
        if not args.case or not args.output:
            parser.error("--case and --output are required together")
        errors.extend(check_case(args.case, args.input, args.output, args))
    else:
        errors.extend(run_fixtures())

    if errors:
        print("hard-output scope fulfillment check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.output:
        print(f"hard-output scope fulfillment check: PASS - {args.case}: {args.output}")
    else:
        print("hard-output scope fulfillment check: PASS - fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
