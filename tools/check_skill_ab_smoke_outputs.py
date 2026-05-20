"""Validate local SKILL A/B smoke outputs without promoting them to release proof."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


CASE_RE = re.compile(r"^(?P<label>[A-Z])(?P<number>\d+)-output\.md$")
FIELD_VALUES_RE = re.compile(
    r"^field:\s+(LOCAL CLAIM|NAMED WORLDVIEW|SOURCE-AUTHENTICATION|MIXED NOETIC FIELD)\b"
)
GOVERNED_BANNER_RE = re.compile(r"\bNOETIC FIELD EXECUTION\b")
REREAD_RE = re.compile(r"R\(H,?\s*(Delta|\u0394)\)")
MOJIBAKE_RE = re.compile(r"[\uFFFD\u00CE\u00E2]")
ASCII_FORMALISM_RE = re.compile(r"\b(PsiN|PsiI|Psi\^N|Psi\^I)\b")
FORMALISM_REQUIRED_TOKENS = {
    5: ["∇", "Δ", "R(H,Δ)", "𝒞(Ψᴺ)", "T_lang"],
    6: [
        "Ψᴺ",
        "Ψᴵ",
        "T_lang: Ψᴺ ⇢ Ψᴵ",
        "N_fiṭrī",
        "ʿaql ṣarīḥ",
        "∇·T",
        "∇×T",
        "LoopBreak(∇×T)",
        "ΔⁿB",
        "Δκ",
        "R(H,Δ)",
        "𝒞(Ψᴺ)",
    ],
}


@dataclass
class SmokeResult:
    phase: str
    case: str
    path: Path
    passed: bool
    first_visible: str
    failed: list[str]
    warnings: list[str]
    suspected_cause: str


def read_text_auto(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig", errors="replace")
    return data.decode("utf-8", errors="replace")


def first_visible_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def first_visible_lines(text: str, limit: int = 10) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        if line.strip():
            lines.append(line.strip())
        if len(lines) >= limit:
            break
    return lines


def normalize_banner_line(line: str) -> str:
    return line.strip().strip("║").strip()


def text_has_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def has_unnegated_phrase(text: str, phrase: str, negations: list[str]) -> bool:
    lowered = text.lower()
    for match in re.finditer(re.escape(phrase), lowered):
        start = max(0, match.start() - 100)
        end = min(len(lowered), match.end() + 40)
        window = lowered[start:end]
        if any(negated in window for negated in negations):
            continue
        prefix = lowered[start : match.start()]
        if re.search(r"\b(no|not|without|does not|do not|cannot|never|doesn't|don't)\b.{0,100}$", prefix):
            continue
        return True
    return False


def printable(value: str, limit: int = 140) -> str:
    value = value.replace("|", "\\|")
    if len(value) > limit:
        value = value[: limit - 3] + "..."
    return value.encode("ascii", "backslashreplace").decode("ascii")


def is_witness_case(case_name: str) -> bool:
    match = re.match(r"^[A-Z](\d+)$", case_name)
    return bool(match and int(match.group(1)) in {1, 2, 3})


def case_number(case_name: str) -> int | None:
    match = re.match(r"^[A-Z](\d+)$", case_name)
    return int(match.group(1)) if match else None


def is_formalism_phase(phase: str) -> bool:
    return "formalism-smoke" in phase


def is_smoke_phase_dir(path: Path) -> bool:
    return path.is_dir() and "smoke-" in path.name


def classify_cause(log_text: str, first_line: str, failures: list[str]) -> str:
    if not failures:
        return "none"
    if not first_line:
        if "tokens used" in log_text.lower() or "exec" in log_text.lower():
            return "transport-or-empty-output"
        return "empty-output"
    if "CreateProcessWithLogonW failed: 1326" in log_text:
        return "runtime-load-failed-read-only-sandbox"
    if "RUNTIME_INLINE_BEGIN" in log_text:
        return "content-or-model-compliance"
    if "Read and follow the local generated runtime entrypoint" in log_text:
        return "runtime-loading-unverified"
    return "content-or-checker-expectation"


def validate_output(path: Path) -> SmokeResult:
    text = read_text_auto(path)
    first_line = first_visible_line(text)
    visible_head = first_visible_lines(text)
    phase = path.parent.name
    match = CASE_RE.match(path.name)
    case = path.stem.replace("-output", "")
    log_path = path.with_name(path.name.replace("-output.md", "-codex.log"))
    log_text = read_text_auto(log_path) if log_path.exists() else ""

    failures: list[str] = []
    warnings: list[str] = []

    if not text.strip():
        failures.append("output is empty")
    if not first_line:
        failures.append("missing first visible line")
    elif first_line.startswith("```"):
        failures.append("first visible line is a Markdown fence, not governed execution banner")
    else:
        banner_window = "\n".join(visible_head[:8])
        has_governed_banner = bool(GOVERNED_BANNER_RE.search(banner_window))
        has_field_line = any(FIELD_VALUES_RE.match(normalize_banner_line(line)) for line in visible_head[:8])
        if not has_governed_banner:
            failures.append("first visible surface lacks governed NOETIC FIELD EXECUTION signature")
        if not has_field_line:
            failures.append("governed banner lacks canonical field line")
        if FIELD_VALUES_RE.match(first_line) and not has_governed_banner:
            failures.append("first visible surface collapsed to bare field:")

    if MOJIBAKE_RE.search(text):
        warnings.append("possible notation mojibake in captured output")
    if "𝒞(ΨN)" in text or "ΨN" in text or "ΨI" in text:
        failures.append("notation simplified: preserve Ψᴺ / Ψᴵ superscript boundary")
    if not is_witness_case(case) and "??" in text and text_has_any(text, ["T_lang", "𝒞("]):
        failures.append("notation mangled to question-mark placeholders")
    if is_formalism_phase(phase):
        if ASCII_FORMALISM_RE.search(text):
            failures.append("formalism notation ASCII-normalized: preserve Ψᴺ / Ψᴵ")
        if "??" in text and text_has_any(text, ["T_lang", "LoopBreak", "R(H", "∇", "𝒞(", "Ψ"]):
            failures.append("formalism notation mangled to question-mark placeholders")
        for token in FORMALISM_REQUIRED_TOKENS.get(case_number(case) or -1, []):
            if token not in text:
                failures.append(f"missing formalism notation token: {token}")

    if is_witness_case(case):
        witness_checks = {
            "burden-cycle or burden graph": text_has_any(
                text, ["Burden-Cycle", "Burden / Operation", "Burden dependency graph"]
            ),
            "field diagnostics": text_has_any(text, ["Field diagnostics", "field diagnostics"]),
            "R(H,Delta) reread": bool(REREAD_RE.search(text)),
            "closure witness": "Closure/Reconstruction Witness" in text,
            "restorative response": "Restorative Response" in text,
            "non-claim boundary": text_has_any(
                text,
                [
                    "Non-claim boundary",
                    "not a truth meter",
                    "not guaranteed uptake",
                    "not a soul/interlocutor rewrite",
                ],
            ),
        }
        for label, ok in witness_checks.items():
            if not ok:
                failures.append(f"missing witness surface: {label}")
    else:
        governed_signal = text_has_any(
            text,
            [
                "Layer A",
                "live noetic burden",
                "gate/release decision",
                "Burden",
                "Target:",
                "Operation:",
                "R(H,Delta)",
                "R(H,\u0394)",
                "Field diagnostics",
            ],
        )
        if not governed_signal:
            failures.append("ordinary output lacks minimal governed-output signal")

        overclaim_checks = [
            ("truth meter", ["not a truth meter"]),
            (
                "guaranteed uptake",
                [
                    "not guaranteed uptake",
                    "no claim of guaranteed uptake",
                    "does not claim access",
                ],
            ),
            ("soul/interlocutor rewrite", ["not a soul/interlocutor rewrite"]),
        ]
        lowered = text.lower()
        for phrase, negations in overclaim_checks:
            if has_unnegated_phrase(text, phrase, negations):
                failures.append(f"possible overclaim language: {phrase}")

    cause = classify_cause(log_text, first_line, failures)
    return SmokeResult(
        phase=phase,
        case=case,
        path=path,
        passed=not failures,
        first_visible=first_line,
        failed=failures,
        warnings=warnings,
        suspected_cause=cause,
    )


def phase_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"(?:^|-)smoke-([a-z])(?:-|$)", path.name)
    if not match:
        return (100, path.name)
    token = match.group(1)
    return (ord(token) - ord("a"), path.name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".daee/skill-ab-v0.4.2.0", help="A/B smoke root")
    parser.add_argument("--phase", help="Validate only one phase directory, e.g. smoke-d")
    parser.add_argument(
        "--fail-all-phases",
        action="store_true",
        help="Exit nonzero if any reported phase fails; default fails only latest phase.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"skill-ab smoke output check: FAIL root missing: {root}")
        return 1

    if args.phase:
        phase_dirs = [root / args.phase]
    else:
        phase_dirs = sorted(
            [p for p in root.iterdir() if is_smoke_phase_dir(p)],
            key=phase_sort_key,
        )

    phase_dirs = [p for p in phase_dirs if p.exists()]
    if not phase_dirs:
        print(f"skill-ab smoke output check: FAIL no smoke-* directories under {root}")
        return 1

    results: list[SmokeResult] = []
    for phase_dir in phase_dirs:
        for output in sorted(phase_dir.glob("*-output.md")):
            if CASE_RE.match(output.name):
                results.append(validate_output(output))

    if not results:
        print("skill-ab smoke output check: FAIL no *-output.md files found")
        return 1

    latest_phase = phase_dirs[-1].name
    print("skill-ab smoke output check")
    print(f"Root: {root}")
    print(f"Latest phase for exit status: {latest_phase}")
    print("Phase | Case | Result | Suspected cause | First visible line | Evidence")
    print("--- | --- | --- | --- | --- | ---")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        first = printable(result.first_visible)
        print(
            f"{result.phase} | {result.case} | {status} | {result.suspected_cause} | "
            f"{first} | {result.path}"
        )
        for failure in result.failed:
            print(f"  - failed condition: {failure}")
        for warning in result.warnings:
            print(f"  - warning: {warning}")

    if args.fail_all_phases:
        failing = [r for r in results if not r.passed]
    else:
        failing = [r for r in results if r.phase == latest_phase and not r.passed]

    if failing:
        print(f"skill-ab smoke output check: FAIL ({len(failing)} failing case(s) in scope)")
        return 1

    print("skill-ab smoke output check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
