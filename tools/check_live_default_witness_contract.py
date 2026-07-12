#!/usr/bin/env python3
"""Check live default daee-epistemics output witness surfaces.

This checker is intentionally structural rather than exact-output brittle. It is
for captured installed-runtime smokes, especially hard/multi-burden default
answers where the runtime must report its own field state. It rejects empty
witness labels and uptake/closure overclaims, but it does not grade the
philosophical quality of an answer.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

from closure_witness_lib import closure_witness_errors, parse_burden_list, parse_closure_witness
from check_field_witness_convergence import current_public_convergence_errors
from closure_witness_lib import (
    extract_embedded_field_witness,
    extract_field_witness,
    public_graph_integrity_diagnostics,
)
from witness_artifact_roles import validate_role


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROUTE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:(?:gate/release decision|release gate)\s*:\s*)?"
    r"(?:\u2207\s*route|route-gradient)\s*:\s*(?P<body>\S.+)$"
)
FIELD_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Field diagnostics\s*:\s*(?P<body>\S.*)$")
DEL_DOT_TARGET_RE = re.compile(
    r"(?:\u2207\u00b7\s*[\w\u207f\u03ba\u03be\u03a9\u2665\u03bc-]+|"
    r"del[- ]dot\s*(?:\(|:)?\s*[\w-]+)",
    re.IGNORECASE,
)
DEL_CROSS_TARGET_RE = re.compile(
    r"(?:\u2207\u00d7\s*[\w\u207f\u03ba\u03be\u03a9\u2665\u03bc-]+|"
    r"del[- ]cross\s*(?:\(|:)?\s*[\w-]+)",
    re.IGNORECASE,
)
LOOPBREAK_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?LoopBreak\s*:\s*(?P<body>\S.*)$")
REREAD_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:`?)R\(H,\s*(?:\u0394|Delta)\)(?:`?)\s*:"
)
CLOSURE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?`?(?:\U0001d49e\(\u03a8\u1d3a\)|C\(PsiN\))`?\s*:\s*(?P<body>\S.*)$"
)
T_LANG_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?`?T_lang\s*:\s*(?:\u03a8\u1d3a|PsiN)\s*(?:\u21e2|->)\s*"
    r"(?:\u03a8\u1d35|PsiI)`?(?:\s+(?:coupling|boundary|coupling boundary))?\s*:\s*(?P<body>\S.*)$"
)
RESTORATIVE_RE = re.compile(r"(?im)^\s*(?:#{2,5}\s*)?Restorative Response\b")
CLOSING_RE = re.compile(r"(?im)^\s*(?:#{2,5}\s*)?Closing Formulation\b")
CLOSURE_HEADING_RE = re.compile(r"(?im)^\s*(?:#{2,5}\s*)?Closure/Reconstruction Witness\b")
INITIAL_BURDEN_SET_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?Initial burden set\s*:\s*\[(?P<body>[^\]]*)\]")
B_LA_BURDEN_SET_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:B_LA|𝔅_LA)\s+baseline ledger\s*:\s*\[(?P<body>[^\]]*)\]")
RETROACTIVE_INITIAL_BURDEN_RE = re.compile(
    r"(?is)Initial burden set.{0,120}(?:updated after execution|retroactively added|retroactive|after execution)"
)
BANNER_RE = re.compile(r"NOETIC FIELD EXECUTION")
LAYER_A_RE = re.compile(r"(?i)\b(?:Layer A|DSL/IR|Diagnostic IR|compact DSL)\b")


FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "decorative route-gradient proof",
        re.compile(
            r"(?is)\u2207.{0,80}(?:proves|guarantees|certifies).{0,80}"
            r"(?:truth|warrant|execution)"
        ),
    ),
    (
        "closure guarantees uptake",
        re.compile(
            r"(?is)\U0001d49e\(\u03a8\u1d3a\).{0,120}"
            r"(?:guarantees|ensures|proves).{0,80}(?:uptake|acceptance|conversion)"
        ),
    ),
    (
        "T_lang guarantees uptake",
        re.compile(
            r"(?is)T_lang.{0,120}(?:guarantees|ensures|proves).{0,80}"
            r"(?:uptake|acceptance|conversion)"
        ),
    ),
    (
        "T_lang claims interlocutor rewrite",
        re.compile(r"(?is)T_lang.{0,120}(?:rewrites|converts|controls).{0,80}(?:\u03a8|interlocutor|soul|heart)"),
    ),
]


def line_context(lines: list[str], index: int, radius: int = 1) -> str:
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return "\n".join(lines[start:end])


def require_pattern(text: str, pattern: re.Pattern[str], label: str, path: Path, errors: list[str]) -> re.Match[str] | None:
    match = pattern.search(text)
    if not match:
        errors.append(f"{path}: missing {label}")
        return None
    body = match.groupdict().get("body")
    if body is not None and not body.strip():
        errors.append(f"{path}: empty {label}")
    return match


def check_field_diagnostics(path: Path, text: str, errors: list[str]) -> int:
    matches = list(FIELD_RE.finditer(text))
    if not matches:
        errors.append(f"{path}: missing target-explicit field diagnostics")
        return 0
    for match in matches:
        body = match.group("body")
        if not DEL_DOT_TARGET_RE.search(body):
            errors.append(f"{path}: Field diagnostics lacks target-explicit del-dot/∇· witness")
        if not DEL_CROSS_TARGET_RE.search(body):
            errors.append(f"{path}: Field diagnostics lacks target-explicit del-cross/∇× witness")
    return len(matches)


def check_loopbreak(path: Path, text: str, errors: list[str]) -> None:
    match = require_pattern(text, LOOPBREAK_RE, "LoopBreak status", path, errors)
    if not match:
        return
    body = match.group("body").strip()
    if re.search(r"(?i)\b(?:none|not needed|not licensed|not applicable|absent|no live loop|null|held with reason)\b", body):
        return
    required = {
        "target": r"(?i)\btarget\b",
        "ground/source": r"(?i)\b(?:ground|source|licensed)\b",
        "delta/effect": r"(?i)(?:\u0394|Delta|\beffect\b)",
        "reread": r"(?i)\b(?:reread|R\(H,)",
    }
    for label, pattern in required.items():
        if not re.search(pattern, body):
            errors.append(f"{path}: licensed LoopBreak lacks {label} evidence")


def check_rereads(path: Path, text: str, field_count: int, errors: list[str]) -> None:
    lines = text.splitlines()
    rereads = [(index, line) for index, line in enumerate(lines) if REREAD_RE.search(line)]
    if not rereads:
        errors.append(f"{path}: missing R(H,Δ)/R(H,Delta) reread witness")
        return
    if len(rereads) > 1 and field_count < len(rereads):
        errors.append(
            f"{path}: field diagnostics not repeated for each R(H,Δ)/R(H,Delta) "
            f"({field_count} diagnostics for {len(rereads)} rereads)"
        )
    for index, line in rereads:
        context = line_context(lines, index, radius=3)
        categories = {
            "reread": r"(?i)\b(?:reread|re-read|rechecked|reassess|refresh|R\(H,)",
            "held set": r"(?i)\b(?:held|H\s*=|held set|held routes)",
            "live remainder": r"(?i)\b(?:live|remainder|remaining|residual|still governs|generated)",
            "release/block": r"(?i)\b(?:release|released|generated|blocked route|cleared|licensed)",
            "next pass": r"(?i)\b(?:next|eligible|pass|STOP|HOLD|RECURSE|PARTIAL|COMPLETE|closure|no remaining)",
        }
        satisfied = [label for label, pattern in categories.items() if re.search(pattern, context)]
        if len(satisfied) < 3:
            errors.append(
                f"{path}: R(H,Δ) witness lacks held/live-remainder/next-pass reread content "
                f"({', '.join(satisfied) or 'none'} found): {line.strip()}"
            )


def check_closure_and_transfer(path: Path, text: str, errors: list[str]) -> None:
    closure = require_pattern(text, CLOSURE_RE, "closure-field condition", path, errors)
    if closure:
        body = closure.group("body")
        if not re.search(r"(?i)\b(?:agent|runtime|execution field|agent field|stated|bounded|governed|compact governed|for this reply)\b", body):
            errors.append(f"{path}: 𝒞(Ψᴺ) witness lacks agent/runtime closure-field semantics")
        if not re.search(r"(?i)\b(?:COMPLETE|STOP|HOLD|RECURSE|PARTIAL|closed|closure|held|residual)\b", body):
            errors.append(f"{path}: 𝒞(Ψᴺ) witness lacks bounded closure decision/status")
    transfer = require_pattern(text, T_LANG_RE, "T_lang boundary", path, errors)
    if transfer:
        body = transfer.group("body")
        if not re.search(r"(?i)\b(?:attempt|coupling|release|public|boundary|language-mediated)\b", body):
            errors.append(f"{path}: T_lang witness lacks coupling-attempt/public-boundary semantics")


def check_closure_witness(path: Path, text: str, errors: list[str]) -> None:
    heading = CLOSURE_HEADING_RE.search(text)
    if not heading:
        return
    if RETROACTIVE_INITIAL_BURDEN_RE.search(text):
        errors.append(f"{path}: Initial burden set must not be retroactively updated after execution")
    witness = parse_closure_witness(text)
    for error in closure_witness_errors(witness):
        errors.append(f"{path}: {error}")
    if witness is None:
        return
    pre_release = text[: heading.start()]
    pre_matches = list(INITIAL_BURDEN_SET_RE.finditer(pre_release))
    if not pre_matches:
        pre_matches = list(B_LA_BURDEN_SET_RE.finditer(pre_release))
    if not pre_matches:
        errors.append(
            f"{path}: Initial burden set must be declared in pre-release Layer A / Diagnostic IR before Closure/Reconstruction Witness"
        )
        return
    pre_initial = parse_burden_list(pre_matches[-1].group("body"))
    if set(pre_initial) != set(witness.initial_burdens):
        errors.append(
            f"{path}: pre-release Initial burden set {pre_initial} does not match closure witness Initial burden set {witness.initial_burdens}"
        )


def check_restorative_order(path: Path, text: str, errors: list[str]) -> None:
    restorative = RESTORATIVE_RE.search(text)
    if not restorative:
        errors.append(f"{path}: missing Restorative Response")
        return
    closing = CLOSING_RE.search(text)
    if not closing:
        errors.append(f"{path}: missing Closing Formulation")
    elif closing.start() < restorative.start():
        errors.append(f"{path}: Closing Formulation must follow Restorative Response")
    before = text[: restorative.start()]
    if not BANNER_RE.search(before):
        errors.append(f"{path}: Restorative Response appears before noetic-field banner")
    if not LAYER_A_RE.search(before):
        errors.append(f"{path}: Restorative Response appears without prior Layer A / DSL governance")
    if not FIELD_RE.search(before) or not REREAD_RE.search(before):
        errors.append(f"{path}: Restorative Response bypasses field diagnostics or R(H,Δ) reread")
    closure_heading = CLOSURE_HEADING_RE.search(text)
    if not closure_heading:
        errors.append(f"{path}: missing Closure/Reconstruction Witness")
    elif closing and closure_heading.start() < closing.start():
        errors.append(f"{path}: Closure/Reconstruction Witness must follow Closing Formulation in graphable default output")
    field_witness = re.search(r"(?im)^\s*(?:#{2,5}\s*)?field_witness\b", text)
    if not field_witness and not re.search(r"(?i)\b(?:minimal|short|no-graph)\b.{0,120}\bgraph(?:ing)?\s+(?:unsupported|partial)", text):
        errors.append(f"{path}: missing field_witness / graphable reconstruction payload")
    elif field_witness and closure_heading and field_witness.start() < closure_heading.start():
        errors.append(f"{path}: field_witness must follow Closure/Reconstruction Witness")


def check_field_witness_consistency(path: Path, text: str, errors: list[str]) -> None:
    field_heading = re.search(r"(?im)^\s*(?:#{2,5}\s*)?field_witness\b", text)
    if not field_heading:
        return
    payload = extract_embedded_field_witness(text)
    if payload is None:
        errors.append(f"{path}: field_witness heading present but parser-stable JSON payload missing or invalid")
        return
    if isinstance(payload, dict) and "field_witness" in payload:
        errors.append(f"{path}: field_witness payload is nested under a wrapper; emit the parser-stable field_witness object itself")
    field_witness = extract_field_witness(payload)
    if field_witness is None:
        errors.append(f"{path}: field_witness / graphable reconstruction payload required for normal governed output")
        return
    role_diagnostics = validate_role(field_witness, "public_graph", "current")
    if role_diagnostics:
        errors.extend(
            f"{path}: {diagnostic.failure_subcode}: {diagnostic.message}"
            for diagnostic in role_diagnostics
        )
        return
    integrity = public_graph_integrity_diagnostics(field_witness, compatibility="current")
    if integrity:
        errors.extend(
            f"{path}: {diagnostic['failure_subcode']}: {diagnostic['message']}"
            for diagnostic in integrity
        )
        return
    errors.extend(current_public_convergence_errors(path, text, field_witness))


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    require_pattern(text, BANNER_RE, "noetic-field banner", path, errors)
    require_pattern(text, ROUTE_RE, "non-empty route-gradient witness", path, errors)
    field_count = check_field_diagnostics(path, text, errors)
    check_loopbreak(path, text, errors)
    check_rereads(path, text, field_count, errors)
    check_closure_and_transfer(path, text, errors)
    check_closure_witness(path, text, errors)
    check_restorative_order(path, text, errors)
    check_field_witness_consistency(path, text, errors)
    for label, pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            errors.append(f"{path}: forbidden {label}")
    return errors


def expand_output_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        raw = str(path)
        if any(char in raw for char in "*?["):
            matches = sorted(Path(match) for match in glob.glob(raw))
            expanded.extend(matches or [path])
        else:
            expanded.append(path)
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("outputs", nargs="+", type=Path, help="Captured live default output files")
    args = parser.parse_args()
    outputs = expand_output_paths(args.outputs)

    errors: list[str] = []
    for output in outputs:
        if not output.exists():
            errors.append(f"{output}: missing")
            continue
        errors.extend(check(output))

    if errors:
        print("live default witness contract: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("live default witness contract: PASS")
    for output in outputs:
        print(f"- {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
