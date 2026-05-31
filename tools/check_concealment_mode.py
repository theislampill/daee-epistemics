#!/usr/bin/env python3
"""Validate compact concealment-mode discipline in rendered outputs.

The checker is intentionally narrow. It does not infer a person's interior state or
replace the modes-of-concealment taxonomy. It catches the regression where an output
calls concealment "None detected" while the same Layer A read marks an imported or
identity-stabilizing framework as operative, and the follow-on regression where a
loose gloss such as "framework-concealed" replaces the source-owned concealment mode.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


CONCEALMENT_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?(?P<label>concealment(?:[_ -]?mode)?)(?:\*\*)?\s*:\s*(?P<value>.*)$"
)
BLOCK_START_RE = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:Layer A|Burden\s+\d+|Closure/Reconstruction Witness)\b")
NONE_PLACEHOLDER_RE = re.compile(r"(?i)^(?:none|none detected|none confirmed|not detected|n/?a|nil|null|unknown|[-–—]+)\b|^[-–—]+$")
CLEAR_VALUE_RE = re.compile(r"(?i)^(?:clear|none|none detected|none confirmed|not detected)\b")
FRAMEWORK_SIGNAL_RE = re.compile(
    r"(?i)\b(?:"
    r"D6|D3|imported\s+(?:foreign\s+)?framework|imported[- ]framework|"
    r"pseudo-neutral|neutral\s+(?:exegesis|reading|grammar|criterion|tribunal)|"
    r"reading\s+criterion|identity-stabili[sz]ation|doctrinal\s+apparatus|"
    r"Trinitarian\s+(?:person/nature|model|grammar|framework)|person/nature\s+grammar|"
    r"later\s+(?:Trinitarian|doctrinal)\s+(?:model|apparatus|grammar)|"
    r"doctrine-(?:import|preserving)|doctrine\s+import|imported\s+model-language|"
    r"creedal\s+(?:framework|commitment|lens)|framework\s+presents\s+as\s+neutral|"
    r"source-worldview|worldview\s+pressure|"
    r"named\s+worldview|field\s*:\s*NAMED WORLDVIEW|governing\s+worldview|"
    r"governing\s+(?:lens|framework|criterion)|operates?\s+from\s+inside\s+the\s+worldview"
    r")\b"
)
ACTIVE_HIDDEN_FRAMEWORK_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?hidden-framework-recoil\s*:\s*"
    r"(?!(?:pressure\s+class\s*:\s*)?(?:none|cleared)\b).+"
)
CLEAR_EXCEPTION_RE = re.compile(
    r"(?i)\b(?:positively\s+(?:exposed|cleared)|no\s+longer\s+governs|"
    r"framework\s+(?:cleared|no\s+longer\s+operative)|non-operative\s+finding|"
    r"operative\s+covering\s+(?:cleared|absent)|no\s+longer\s+diagnosing\s+hidden|"
    r"no\s+longer\s+diagnosing\s+framework|current\s+pass\s+is\s+(?:restor(?:ing|ation)|no\s+longer\s+diagnosing))\b"
)
SOURCE_MODE_RE = re.compile(
    r"(?i)\b(?:irad|juhud|inkar|istikbar|nifaq|mixed)\b|"
    r"iʿrāḍ|juḥūd|inkār|istikbār|nifāq"
)
SOURCE_COMPONENT_MODE_RE = re.compile(
    r"(?i)\b(?:irad|juhud|inkar|istikbar|nifaq)\b|"
    r"iʿrāḍ|juḥūd|inkār|istikbār|nifāq"
)
SOURCE_COMPONENT_TOKEN_RE = re.compile(
    r"(?i)\b(?:i['`]?rad|irad|juhud|inkar|istikbar|nifaq)\b|"
    r"iʿrāḍ|juḥūd|inkār|istikbār|nifāq"
)
MODE_UNKNOWN_RE = re.compile(r"(?i)\bmode-\?\b")
UNRESOLVED_MODE_RE = re.compile(r"(?i)\b(?:underdetermined|unreadable|provisional|insufficient(?:ly)?\s+signalled|insufficient\s+basis)\b")
LOOSE_GLOSS_RE = re.compile(
    r"(?i)\b(?:surface-open|framework-concealed|hidden-framework|predicate-concealed|"
    r"entailment-concealed|source-worldview|identity-stabili[sz]ed|framework-cover(?:ed|ing)|"
    r"formal-shell|moral-predicate transfer)\b"
)
CLARIFICATION_PRESSURE_RE = re.compile(
    r"(?i)\b(?:clarification\s+pressure|clarification\s*/\s*shubh?a?h|"
    r"shubh?a?h|shakk|rayb|rāyb|tawahhum|wasw[āa]s|doubt-pressure|doubt\s+pressure|"
    r"sincere\s+(?:uncertainty|clarification|inquiry)|ḥanīf\s+restoration|hanif\s+restoration)\b"
)
REFUSAL_MODE_RE = re.compile(r"(?i)\b(?:juhud|inkar|istikbar|nifaq)\b|juḥūd|inkār|istikbār|nifāq")
REFUSAL_SIGNAL_RE = re.compile(
    r"(?i)\b(?:refus|repudiat|recognition\s+pressure|outward\s+denial|"
    r"acknowledg(?:e|ment).*refus|pride|status\s+obstruction|volitional\s+alignment|"
    r"surface\s+acceptance\s+without\s+genuine|performative\s+agreement)\b"
)
CLARIFICATION_ROUTE_RE = re.compile(
    r"(?i)\b(?:route[sd]?\s+(?:toward|to|through)\s+clarification|"
    r"clarification\s+(?:route|path)|not\s+(?:functioning\s+as\s+)?refusal|"
    r"not\s+routed\s+to\s+refusal|not\s+(?:juḥūd|juhud|inkār|inkar|istikbār|istikbar|nifāq|nifaq)|"
    r"rather\s+than\s+(?:refusal|denial|obstinacy)|bounded\s+reassurance|"
    r"source[- ]order\s+repair|fiṭrah\s+anchoring|fitrah\s+anchoring|V9)\b"
)
BAD_CLARIFICATION_REFUSAL_ROUTE_RE = re.compile(
    r"(?i)\b(?:shubh?a?h|shakk|rayb|rāyb|clarification\s+pressure|sincere\s+uncertainty)"
    r"[^.\n;]*(?:route[sd]?\s+(?:to|into)|assigned\s+to|classified\s+as|read\s+as|folded\s+into)"
    r"[^.\n;]*(?:refusal|juḥūd|juhud|inkār|inkar|istikbār|istikbar|nifāq|nifaq)\b"
)
REQUESTER_SCOPE_RE = re.compile(
    r"(?i)\b(?:user|requester|asker|the\s+person\s+asking|the\s+Muslim\s+asking|the\s+da[ʿ'`]?i\s+asking)\b"
)
REQUESTER_ALLOWED_RE = re.compile(
    r"(?i)\b(?:diagnostic[_ -]?target\s*:\s*requester-self-state|"
    r"concealment[_ -]?applies[_ -]?to\s*:\s*requester|"
    r"not\s+(?:the\s+)?requester|requester\s+(?:is\s+)?(?:not|non[- ]diagnostic)|"
    r"requester\s+(?:explicitly\s+)?(?:presents|states|asks\s+about)\s+(?:their|his|her|my)\s+own|"
    r"\bI\s+(?:am|have|feel|believe|refuse|deny)\b|my\s+(?:doubt|shubh?a?h|belief|refusal|state))\b"
)
BOUNDARY_RE = re.compile(
    r"(?i)\b(?:Boundary\s*:|diagnostic\s+noetic|visible\s+discourse\s+diagnosis|"
    r"no\s+(?:hidden\s+)?soul[- ]state|no\s+takf[īi]r|not\s+a\s+takf[īi]r|"
    r"not\s+(?:a\s+)?(?:hidden\s+)?(?:soul[- ]state|culpability)\s+judg)"
)
SOURCE_STACK_AMBIGUITY_RE = re.compile(
    r"(?is)\b(?:source[- ]stack|stack\s+of\s+names|names\s+and\s+quotations)\b"
    r".{0,220}\b(?:ambiguous|ambiguously|prestige\s+signal|identity\s+signal|"
    r"as\s+(?:proof|evidence|prestige|contrast)|contrast|genealogy)\b|"
    r"\b(?:AS-8|source\s+as\s+evidence\s+vs\s+source\s+as\s+identity\s+signal)\b"
)
SOURCE_USE_FUNCTION_RE = re.compile(
    r"(?is)\b(?:AS-8|source[- ]use(?:\s+function)?|source\s+function|source-status)\b"
    r".{0,280}\b(?:evidence|contrast|genealogy|identity\s+signal|prestige\s+signal|"
    r"held\s+material|bounded\s+comparison)\b"
)
SOURCE_PARADE_BLOCK_RE = re.compile(
    r"(?is)\b(?:argument[- ]bank|source[- ]parade)\b.{0,180}"
    r"\b(?:blocked|held|withheld|not\s+released|forbidden|stopped)\b|"
    r"\b(?:block|blocks|blocked|withhold|withheld|hold)\b.{0,140}"
    r"\b(?:argument[- ]bank|source[- ]parade)\b"
)
IRAD_CONTEXT_RE = re.compile(
    r"(?i)\b(?:attention\s+(?:has\s+)?not\s+yet\s+(?:been\s+)?given|"
    r"matter\s+(?:has\s+)?not\s+yet\s+(?:been\s+)?allowed\s+to\s+press|"
    r"not\s+yet\s+allowed\s+to\s+press|pre-inquiry|pre\s+inquiry)\b"
)
JUHUD_CONTEXT_RE = re.compile(
    r"(?i)\b(?:acknowledg(?:e|ment)\s+(?:is\s+)?refus|refused\s+once\s+attention\s+has\s+landed|"
    r"once\s+the\s+matter\s+has\s+pressed|after\s+pressure\s+landed|post-engagement\s+refusal)\b"
)


def has_source_mode(value: str) -> bool:
    return bool(SOURCE_MODE_RE.search(value))


def is_mode_unknown(value: str) -> bool:
    return bool(MODE_UNKNOWN_RE.search(value))


def is_mixed(value: str) -> bool:
    return bool(re.search(r"(?i)\bmixed\b", value))


def has_source_component(value: str, block: str) -> bool:
    return bool(SOURCE_COMPONENT_MODE_RE.search(value) or SOURCE_COMPONENT_MODE_RE.search(block))


def source_components(value: str) -> set[str]:
    components: set[str] = set()
    aliases = {
        "iʿrāḍ": "irad",
        "i'rad": "irad",
        "i`rad": "irad",
        "irad": "irad",
        "juḥūd": "juhud",
        "juhud": "juhud",
        "inkār": "inkar",
        "inkar": "inkar",
        "istikbār": "istikbar",
        "istikbar": "istikbar",
        "nifāq": "nifaq",
        "nifaq": "nifaq",
    }
    for match in SOURCE_COMPONENT_TOKEN_RE.finditer(value):
        token = match.group(0).lower()
        components.add(aliases.get(token, token))
    return components


def has_clarification_pressure(value: str, block: str) -> bool:
    return bool(CLARIFICATION_PRESSURE_RE.search(value) or CLARIFICATION_PRESSURE_RE.search(block))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def surrounding_block(text: str, start: int) -> str:
    """Return the current compact diagnostic/burden block around a concealment line."""
    prior = list(BLOCK_START_RE.finditer(text, 0, start))
    block_start = prior[-1].start() if prior else max(0, start - 800)
    next_match = BLOCK_START_RE.search(text, start + 1)
    block_end = next_match.start() if next_match else min(len(text), start + 1600)
    return text[block_start:block_end]


def check_text(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    matches = list(CONCEALMENT_LINE_RE.finditer(text))
    framework_active = bool(FRAMEWORK_SIGNAL_RE.search(text) or ACTIVE_HIDDEN_FRAMEWORK_RE.search(text))
    exception_visible = bool(CLEAR_EXCEPTION_RE.search(text))
    source_stack_ambiguous = bool(SOURCE_STACK_AMBIGUITY_RE.search(text))
    if source_stack_ambiguous:
        if not SOURCE_USE_FUNCTION_RE.search(text):
            errors.append(
                f"{path}: AS-8 source-stack ambiguity requires a visible source-use function "
                "classification before content/proof release"
            )
        if not SOURCE_PARADE_BLOCK_RE.search(text):
            errors.append(
                f"{path}: AS-8 source-stack ambiguity must block argument-bank/source-parade release"
            )
    if framework_active and not matches:
        errors.append(f"{path}: operative framework/worldview covering requires a visible Concealment mode line")
    if framework_active and matches and not any("mode" in match.group("label").lower() for match in matches):
        errors.append(f"{path}: operative framework/worldview covering must use exact `Concealment mode:` label, not bare `concealment:`")
    for match in matches:
        value = match.group("value").strip().strip("*").strip()
        block = surrounding_block(text, match.start())
        if not value or NONE_PLACEHOLDER_RE.search(value):
            errors.append(f"{path}: concealment must not use placeholder {value!r}; use clear, mode-?, or an anchored mode")
        if REQUESTER_SCOPE_RE.search(value) and REFUSAL_MODE_RE.search(value) and not REQUESTER_ALLOWED_RE.search(block):
            errors.append(
                f"{path}: Concealment mode appears attached to the requester rather than the diagnostic target"
            )
        if CLEAR_VALUE_RE.search(value) and (
            FRAMEWORK_SIGNAL_RE.search(block) or ACTIVE_HIDDEN_FRAMEWORK_RE.search(text)
        ) and not (CLEAR_EXCEPTION_RE.search(block) or exception_visible):
            errors.append(
                f"{path}: concealment {value!r} conflicts with operative framework/worldview covering"
            )
        is_clear = bool(CLEAR_VALUE_RE.search(value))
        if not is_clear and not NONE_PLACEHOLDER_RE.search(value):
            source_mode = has_source_mode(value)
            unresolved_only = is_mode_unknown(value) and UNRESOLVED_MODE_RE.search(block) and not (
                FRAMEWORK_SIGNAL_RE.search(block) or ACTIVE_HIDDEN_FRAMEWORK_RE.search(text)
            )
            clarification_pressure = has_clarification_pressure(value, block) and not (
                FRAMEWORK_SIGNAL_RE.search(block) or ACTIVE_HIDDEN_FRAMEWORK_RE.search(block)
            )
            if not source_mode and not unresolved_only and not clarification_pressure:
                errors.append(
                    f"{path}: non-clear Concealment mode must name a source-owned mode "
                    "(iʿrāḍ/irad, juḥūd/juhud, inkār/inkar, istikbār/istikbar, nifāq/nifaq, mixed, "
                    "or a bounded clarification/shubhah pressure); "
                    f"loose gloss found: {value!r}"
                )
            if LOOSE_GLOSS_RE.search(value) and not source_mode:
                errors.append(f"{path}: loose concealment gloss cannot replace the source-owned mode: {value!r}")
            if (source_mode or clarification_pressure) and not BOUNDARY_RE.search(block):
                errors.append(
                    f"{path}: non-clear Concealment mode must preserve the diagnostic boundary "
                    "(no hidden soul-state / takfīr judgment)"
                )
            mixed_components = source_components(value)
            if is_mixed(value) and len(mixed_components) < 2:
                errors.append(
                    f"{path}: mixed Concealment mode must name at least two dominant source-owned component "
                    "pressures in the mode line itself (iʿrāḍ/juḥūd/inkār/istikbār/nifāq), not only a loose gloss"
                )
            if (
                is_mixed(value)
                and has_clarification_pressure(value, block)
                and BAD_CLARIFICATION_REFUSAL_ROUTE_RE.search(value + "\n" + block)
                and not CLARIFICATION_ROUTE_RE.search(value + "\n" + block)
            ):
                errors.append(
                    f"{path}: mixed Concealment mode routes sincere shubhah/shakk-rāyb pressure into refusal language"
                )
            if (
                is_mixed(value)
                and has_clarification_pressure(value, block)
                and not REFUSAL_SIGNAL_RE.search(block)
                and not CLARIFICATION_ROUTE_RE.search(value + "\n" + block)
            ):
                errors.append(
                    f"{path}: mixed Concealment mode with sincere shubhah/shakk-rāyb pressure must route that pressure through clarification rather than refusal"
                )
            if REFUSAL_MODE_RE.search(value) and not is_mixed(value) and CLARIFICATION_PRESSURE_RE.search(block) and not REFUSAL_SIGNAL_RE.search(block):
                errors.append(
                    f"{path}: sincere shubhah/shakk-rāyb clarification pressure is misrouted into a refusal mode"
                )
            if not is_mixed(value):
                if re.search(r"(?i)\bjuhud\b|juḥūd", value) and IRAD_CONTEXT_RE.search(block) and not JUHUD_CONTEXT_RE.search(block):
                    errors.append(f"{path}: juḥūd/juhud is misrouted where attention has not yet been allowed to press")
                if re.search(r"(?i)\birad\b|iʿrāḍ", value) and JUHUD_CONTEXT_RE.search(block) and not IRAD_CONTEXT_RE.search(block):
                    errors.append(f"{path}: iʿrāḍ/irad is misrouted where acknowledgment is already refused after pressure landed")
    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("tests/concealment-mode"))
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    errors: list[str] = []
    valid, invalid = iter_fixtures(args.root)
    if not args.root.exists():
        errors.append(f"{args.root}: concealment fixture root is missing")
    elif not valid or not invalid:
        errors.append(
            f"{args.root}: concealment fixture root must contain at least one valid and one invalid fixture"
        )
    valid_checked = 0
    invalid_checked = 0
    output_checked = 0

    for path in valid:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            valid_checked += 1
    for path in invalid:
        found = check_text(path, read_text(path))
        if not found:
            errors.append(f"{path}: expected-invalid concealment fixture unexpectedly passed")
        else:
            invalid_checked += 1
    for path in args.outputs:
        found = check_text(path, read_text(path))
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("concealment-mode check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("concealment-mode check: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Hosted/live outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
