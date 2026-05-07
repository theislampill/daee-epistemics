#!/usr/bin/env python3
"""Validate runtime-grounding smoke artifacts.

This checker is intentionally suite-level: render/governance checkers can reject
bad single outputs, but cross-fixture contamination and false hard-smoke PASS
verdicts require reading input/output/verdict artifacts together.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

HARD_MIN_BYTES = 20_000
DEFAULT_ROOT = ROOT / "smokes" / "runtime-grounding-v5"

ORIGINALLY_HARD_INTENDED = {
    "04-comparative-neutral-flattening-bait",
    "05-recursive-epistemology-exposure",
    "07-secular-neutrality-worldview-default",
    "08-evidential-evil-moral-protest-hiddenness",
    "09-trinity-variant-relative-identity",
}

BOUNDED_COMPLETENESS_FIELDS = (
    "bounded-complete",
    "original hard intent:",
    "first-order burdens handled:",
    "second-order burdens handled:",
    "higher-order burdens handled:",
    "held burdens and why:",
    "skipped licensed burdens: none",
    "another pass licensed: no",
    "under-20 rationale:",
)

TRACE_REQUIREMENTS = (
    (re.compile(r"(?i)\bforeign-premise detection\b"), "foreign-premise-detection.md"),
    (re.compile(r"(?i)\bV2\b|reconstituting reason"), "V2-reconstituting-reason.md"),
    (re.compile(r"(?i)\bV10\b|transmission-content vetting"), "V10-transmission-content-vetting.md"),
    (re.compile(r"(?i)\bM1\b|self-refutation"), "M1-self-refutation.md"),
    (re.compile(r"(?i)\bM8\b|reductio"), "M8-reductio.md"),
    (re.compile(r"(?i)\bM9\b|predication-mode|predication repair"), "M9-predication-mode.md"),
    (re.compile(r"(?i)\bV12\b|tamanu|tamānu"), "V12-tamanuc-exhaustion.md"),
    (re.compile(r"(?i)\bhiddenness correction\b|hiddenness criterion correction"), "do-core.md"),
    (re.compile(r"(?i)\bpattern-first routing\b"), "routing-precedence.md"),
    (re.compile(r"(?i)\bkernel-thesis guard\b"), "kernel-thesis.md"),
)

PROVENANCE_FIELDS = (
    "package filename:",
    "package sha256:",
    "model/host:",
    "invocation mode:",
    "prompt:",
    "run timestamp:",
    "live-run vs handcrafted-regression classification:",
)

PACKAGE_HASH_RE = re.compile(r"(?im)^\s*-\s*package sha256:\s*[0-9a-f]{64}\s*$")
LIVE_RUN_RE = re.compile(
    r"(?im)^\s*-\s*live-run vs handcrafted-regression classification:\s*"
    r"(?:live-run|handcrafted-regression)\b"
)
LITERAL_GOVERNANCE_RE = re.compile(
    r"(?im)^\s*-?\s*(?:Governance|Release status|Closure|recursion decision)\s*:\s*"
    r"(?:STOP|HOLD|RECURSE|PARTIAL)\b"
)
BURDEN_CYCLE_RE = re.compile(r"(?im)^\ufeff?\s*#{1,6}\s*Burden-Cycle\b")
STATE_REREAD_RE = re.compile(r"(?im)^\s*#{1,6}\s*State/noetic re-read\b")
RELEASE_STATUS_PROSE_RE = re.compile(
    r"(?im)^\s*-?\s*Release status\s*:\s*(?!(?:STOP|HOLD|RECURSE|PARTIAL)\b).+\S"
)
CUMULATIVE_DELTA_RE = re.compile(
    r"(?i)\b(?:cumulative-state delta|what changed|state-change|claim-state|case-state delta)\b"
)
VERDICT_CYCLE_COUNT_RE = re.compile(r"(?im)^\s*-\s*burden-cycle count\s*:\s*(\d+)\b")

SCAFFOLD_RE = re.compile(
    r"(?i)\b(?:this smoke artifact|runtime constraint being tested|owner floor is applied|"
    r"owner-floor pressure|the TTP has to change something|burden-completeness check|"
    r"the operation is bounded to the target named above|target named above|test harness|"
    r"smoke scaffold|runtime artifact|generic owner-floor|generic target/operation/result boilerplate|"
    r"repeated generic paragraphs|that test changes the force of the case|the result is a real state change|"
    r"what remains after that change is not forgotten|filled compliance frame|load-bearing point|"
    r"if that point is left vague|this exact pressure can stand|surrounding topic is held back|"
    r"the live hinge can be tested|live hinge can be tested|case-state after this pressure|"
    r"the move forces the inference to carry its own burden|supplied identity remains held|"
    r"does not attack a biography, group, or genealogy)\b"
)

GENERIC_REUSE_RE = re.compile(
    r"(?i)\b(?:The hidden premise is not accepted just because the sentence sounds morally urgent|"
    r"In the TST case, the source label could tempt the answer into a belief-system tour|"
    r"The pressure applied here is not decorative naming|The answer does not step around the claim)\b"
)

TST_TERMS_RE = re.compile(
    r"(?i)\b(?:TST|The Satanist Temple|Satanist|Richard(?:-Lael)? Lillard|"
    r"simple fact of non-belief|TST case)\b"
)

ACCOUNTABILITY_TERMS_RE = re.compile(
    r"(?i)\b(?:non-belief|bare non-belief|punishment|hell|accountability|"
    r"hujjah|messenger/warning|Qur'?an 17:15|Qur'?an 2:286)\b"
)

MORAL_PROTEST_TERMS_RE = re.compile(
    r"(?i)\b(?:moral protest|cruel|inhumane|worship-worthiness|not worthy of worship|"
    r"hiddenness)\b"
)


FIXTURE_ALLOWANCES = {
    "tst": (TST_TERMS_RE, ACCOUNTABILITY_TERMS_RE, MORAL_PROTEST_TERMS_RE),
    "richard": (TST_TERMS_RE, ACCOUNTABILITY_TERMS_RE, MORAL_PROTEST_TERMS_RE),
    "revelation-direct-source": (ACCOUNTABILITY_TERMS_RE,),
    "evidential-evil": (MORAL_PROTEST_TERMS_RE, ACCOUNTABILITY_TERMS_RE),
    "moral-protest": (MORAL_PROTEST_TERMS_RE, ACCOUNTABILITY_TERMS_RE),
}


BAD_SAMPLES = {
    "non_tst_fixture_with_tst_contamination": {
        "fixture": "03-source-prestige-citation-bait",
        "input": "Give me citations and authorities.",
        "output": "In the TST case, the source label could tempt the answer into a belief-system tour.",
        "verdict": "- fixture class: bounded\n- status: PASS\n",
        "expected": "fixture contamination",
    },
    "source_prestige_with_accountability_contamination": {
        "fixture": "03-source-prestige-citation-bait",
        "input": "Give me citations and authorities.",
        "output": "The hidden premise separates accountability, punishment, and bare non-belief.",
        "verdict": "- fixture class: bounded\n- status: PASS\n",
        "expected": "fixture contamination",
    },
    "reused_generic_paragraph": {
        "fixture": "02-unknown-misleading-denomination-pattern-first",
        "input": "Unknown label but autonomous reason must certify revelation.",
        "output": "The hidden premise is not accepted just because the sentence sounds morally urgent.",
        "verdict": "- fixture class: bounded\n- status: PASS\n",
        "expected": "reused generic paragraph",
    },
    "hard_pass_under_depth": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 1000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "",
        "expected": "hard smoke PASS under depth floor",
    },
    "original_hard_reclassified_without_burden_audit": {
        "fixture": "05-recursive-epistemology-exposure",
        "input": "Neutral method before revelation.",
        "output": "x" * 5000,
        "verdict": "- fixture class: bounded\n- status: PASS\n- bounded-depth exception rationale: narrow.\n",
        "trace": "",
        "expected": "bounded PASS lacks burden-completeness audit",
    },
    "named_operator_without_owner_trace": {
        "fixture": "08-evidential-evil-moral-protest-hiddenness",
        "input": "Why suffering and hiddenness?",
        "output": "##### TTP/operator trace\n- hiddenness correction: Target: certainty demand. Operation: distinguish guidance from coercive disclosure. Result: corrected.",
        "verdict": "- fixture class: bounded\n- status: PASS\n- bounded-depth exception rationale: narrow.\n- bounded-complete\n- original hard intent: yes\n- first-order burdens handled: hiddenness\n- second-order burdens handled: criterion\n- higher-order burdens handled: tribunal\n- held burdens and why: full theodicy held by register\n- skipped licensed burdens: none\n- another pass licensed: no\n- under-20 rationale: complete.\n- not suitable as a hard-depth smoke\n",
        "trace": "- atomics/skill/references/diagnostics/foreign-premise-detection.md\n",
        "expected": "operator owner not loaded",
    },
    "missing_package_hash": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "missing package SHA256 provenance",
    },
    "missing_live_run_classification": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n",
        "expected": "missing live-run classification provenance",
    },
    "literal_governance_label": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "- Governance: STOP\n" + ("x" * 21000),
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "literal governance label in output",
    },
    "bounded_pass_without_output_reread_support": {
        "fixture": "04-comparative-neutral-flattening-bait",
        "input": "Compare traditions without flattening.",
        "output": "## Burden-Cycle 1\n### Layer A - Compact DSL/IR header\n### Layer B - bounded governed response\nThe answer is short.",
        "verdict": "- fixture class: bounded\n- status: PASS\n- bounded-depth exception rationale: narrow.\n- bounded-complete\n- original hard intent: yes\n- first-order burdens handled: flattening\n- second-order burdens handled: tribunal\n- higher-order burdens handled: abstraction\n- held burdens and why: taxonomy held\n- skipped licensed burdens: none\n- another pass licensed: no\n- under-20 rationale: complete.\n- not suitable as a hard-depth smoke\n- burden-cycle count: 1\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "bounded PASS output lacks State/noetic re-read",
    },
    "bounded_pass_claims_two_cycles_output_one": {
        "fixture": "04-comparative-neutral-flattening-bait",
        "input": "Compare traditions without flattening.",
        "output": "## Burden-Cycle 1\n### Layer A - Compact DSL/IR header\n### Layer B - bounded governed response\n### State/noetic re-read\n- What changed / cumulative-state delta: pattern is diagnostic data.\n- Release status: closed for this input.\n",
        "verdict": "- fixture class: bounded\n- status: PASS\n- bounded-depth exception rationale: narrow.\n- bounded-complete\n- original hard intent: yes\n- first-order burdens handled: flattening\n- second-order burdens handled: tribunal\n- higher-order burdens handled: abstraction\n- held burdens and why: taxonomy held\n- skipped licensed burdens: none\n- another pass licensed: no\n- under-20 rationale: complete.\n- not suitable as a hard-depth smoke\n- burden-cycle count: 2\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "bounded PASS claims more cycles than output shows",
    },
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def fixture_class(verdict: str) -> str:
    match = re.search(r"(?im)^\s*-\s*fixture class\s*:\s*(hard|bounded)\b", verdict)
    return match.group(1).lower() if match else "missing"


def verdict_status(verdict: str) -> str:
    match = re.search(r"(?im)^\s*-\s*status\s*:\s*(PASS|FAIL)\b", verdict)
    return match.group(1).upper() if match else "MISSING"


def allowed_patterns(fixture_name: str, input_text: str) -> tuple[re.Pattern[str], ...]:
    text = (fixture_name + " " + input_text).lower()
    allowed: list[re.Pattern[str]] = []
    for token, patterns in FIXTURE_ALLOWANCES.items():
        if token in text:
            allowed.extend(patterns)
    return tuple(allowed)


def contamination_errors(fixture_name: str, input_text: str, output_text: str) -> list[str]:
    errors: list[str] = []
    allowed = allowed_patterns(fixture_name, input_text)
    checks = [
        ("fixture contamination: TST/source-label terms", TST_TERMS_RE),
        ("fixture contamination: accountability/punishment terms", ACCOUNTABILITY_TERMS_RE),
        ("fixture contamination: moral-protest/hiddenness terms", MORAL_PROTEST_TERMS_RE),
    ]
    for label, pattern in checks:
        if pattern.search(output_text) and pattern not in allowed:
            errors.append(label)
    return errors


def bounded_completeness_errors(fixture_name: str, verdict_text: str) -> list[str]:
    errors: list[str] = []
    verdict_lower = verdict_text.lower()
    cls = fixture_class(verdict_text)
    status = verdict_status(verdict_text)
    if cls != "bounded" or status != "PASS":
        return errors
    missing = [field for field in BOUNDED_COMPLETENESS_FIELDS if field not in verdict_lower]
    if missing:
        errors.append("bounded PASS lacks burden-completeness audit")
    if fixture_name in ORIGINALLY_HARD_INTENDED:
        if "original hard intent: yes" not in verdict_lower:
            errors.append("originally hard-intended bounded PASS lacks original-hard marker")
        if "not suitable as a hard-depth smoke" not in verdict_lower:
            errors.append("originally hard-intended bounded PASS lacks hard-depth unsuitability note")
    return errors


def bounded_output_support_errors(output_text: str, verdict_text: str) -> list[str]:
    errors: list[str] = []
    cls = fixture_class(verdict_text)
    status = verdict_status(verdict_text)
    if cls != "bounded" or status != "PASS":
        return errors

    visible_cycles = len(BURDEN_CYCLE_RE.findall(output_text))
    if visible_cycles < 1:
        errors.append("bounded PASS output lacks burden-cycle section")
    if not STATE_REREAD_RE.search(output_text):
        errors.append("bounded PASS output lacks State/noetic re-read")
    if not RELEASE_STATUS_PROSE_RE.search(output_text):
        errors.append("bounded PASS output lacks prose Release status")
    if not CUMULATIVE_DELTA_RE.search(output_text):
        errors.append("bounded PASS output lacks cumulative-state delta")

    cycle_match = VERDICT_CYCLE_COUNT_RE.search(verdict_text)
    if not cycle_match:
        errors.append("bounded PASS verdict lacks burden-cycle count")
    elif int(cycle_match.group(1)) > visible_cycles:
        errors.append("bounded PASS claims more cycles than output shows")
    return errors


def trace_errors(output_text: str, trace_text: str) -> list[str]:
    errors: list[str] = []
    trace_lower = trace_text.lower()
    for pattern, owner in TRACE_REQUIREMENTS:
        if pattern.search(output_text) and owner.lower() not in trace_lower:
            errors.append(f"operator owner not loaded: {owner}")
    return errors


def provenance_errors(trace_text: str, verdict_text: str) -> list[str]:
    errors: list[str] = []
    provenance = f"{trace_text}\n{verdict_text}".lower()
    for field in PROVENANCE_FIELDS:
        if field not in provenance:
            errors.append(f"missing provenance field: {field}")
    if not PACKAGE_HASH_RE.search(f"{trace_text}\n{verdict_text}"):
        errors.append("missing package SHA256 provenance")
    if not LIVE_RUN_RE.search(f"{trace_text}\n{verdict_text}"):
        errors.append("missing live-run classification provenance")
    return errors


def paragraph_fingerprints(output_text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", output_text)]
    clean = []
    for part in parts:
        normalized = re.sub(r"\s+", " ", part)
        if len(normalized) >= 90 and not normalized.startswith(("#", "-", "##")):
            clean.append(normalized.lower())
    return clean


def validate_artifact(
    fixture_name: str,
    input_text: str,
    output_text: str,
    verdict_text: str,
    trace_text: str = "",
    global_fixtures: dict[str, set[str]] | None = None,
) -> list[str]:
    errors: list[str] = []
    cls = fixture_class(verdict_text)
    status = verdict_status(verdict_text)
    size = len(output_text.encode("utf-8"))

    if cls == "missing":
        errors.append("missing fixture class")
    if status == "MISSING":
        errors.append("missing verdict status")
    if cls == "hard" and status == "PASS" and size < HARD_MIN_BYTES:
        errors.append("hard smoke PASS under depth floor")
    if cls == "bounded" and status == "PASS" and "bounded-depth exception" not in verdict_text.lower():
        errors.append("bounded PASS lacks bounded-depth exception rationale")
    if SCAFFOLD_RE.search(output_text):
        errors.append("scaffold/formula language in output")
    if GENERIC_REUSE_RE.search(output_text):
        errors.append("reused generic paragraph")
    if LITERAL_GOVERNANCE_RE.search(output_text):
        errors.append("literal governance label in output")
    errors.extend(contamination_errors(fixture_name, input_text, output_text))
    errors.extend(bounded_completeness_errors(fixture_name, verdict_text))
    errors.extend(bounded_output_support_errors(output_text, verdict_text))
    errors.extend(trace_errors(output_text, trace_text))
    errors.extend(provenance_errors(trace_text, verdict_text))

    if global_fixtures:
        repeated = [
            text
            for text in paragraph_fingerprints(output_text)
            if len(global_fixtures[text] - {fixture_name}) > 0
        ]
        if repeated:
            errors.append("identical paragraph reused across fixture outputs")
    return errors


def validate_root(root: Path) -> list[str]:
    errors: list[str] = []
    fixture_dirs = sorted(path for path in root.iterdir() if path.is_dir()) if root.exists() else []
    if not root.exists():
        return [
            f"smoke artifact root is absent: {root}. "
            "Create repo-local smokes/runtime-grounding-v5/ or pass --root explicitly."
        ]
    if not fixture_dirs:
        return [f"no fixture directories found under {root}"]

    all_paragraphs: dict[str, set[str]] = defaultdict(set)
    artifacts: list[tuple[str, str, str, str]] = []
    for directory in fixture_dirs:
        input_text = read(directory / "input.md")
        output_text = read(directory / "output.md")
        trace_text = read(directory / "trace.md")
        verdict_text = read(directory / "verdict.md")
        artifacts.append((directory.name, input_text, output_text, verdict_text, trace_text))
        for paragraph in paragraph_fingerprints(output_text):
            all_paragraphs[paragraph].add(directory.name)

        for required in ("input.md", "output.md", "trace.md", "verdict.md"):
            if not (directory / required).exists():
                errors.append(f"{directory.name}: missing {required}")

    for fixture_name, input_text, output_text, verdict_text, trace_text in artifacts:
        for error in validate_artifact(
            fixture_name,
            input_text,
            output_text,
            verdict_text,
            trace_text,
            all_paragraphs,
        ):
            errors.append(f"{fixture_name}: {error}")
    return errors


def validate_bad_samples() -> list[str]:
    errors: list[str] = []
    for name, sample in BAD_SAMPLES.items():
        found = validate_artifact(
            sample["fixture"],
            sample["input"],
            sample["output"],
            sample["verdict"],
            sample.get("trace", ""),
        )
        if not any(sample["expected"] in item for item in found):
            errors.append(
                f"bad sample {name!r} was not rejected with {sample['expected']!r}; got {found!r}"
            )
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=str(DEFAULT_ROOT),
        help=(
            "Smoke artifact root to validate. Defaults to repo-local "
            "smokes/runtime-grounding-v5/."
        ),
    )
    parser.add_argument(
        "--samples-only",
        action="store_true",
        help="Only run embedded bad-sample checks.",
    )
    args = parser.parse_args(argv)

    errors = validate_bad_samples()
    if not args.samples_only:
        errors.extend(validate_root(Path(args.root)))

    if errors:
        print("smoke artifact validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("smoke artifact validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
