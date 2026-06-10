#!/usr/bin/env python3
"""Validate the static trigger-eval taxonomy manifest.

No-model taxonomy discipline only. This checker validates manifest schema,
controlled expected-class vocabulary, unique IDs, contradictory duplicate
prompts, rationale presence, and basic activation-surface coverage against the
canonical skill frontmatter description in atomics/skill/SKILL.md.

It does not run hosts or models, and a PASS must never be cited as
installed-skill trigger behavior, live host activation proof, or release
evidence. The manifest is taxonomy discipline for the activation surface; any
model-lane grading is a separate, explicitly authorized future lane.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "tests" / "trigger-eval" / "manifest.json"
CANONICAL_SKILL_SOURCE = "atomics/skill/SKILL.md"

EXPECTED_CLASSES = ("should-trigger", "should-not-trigger", "ambiguous-trigger")
AMBIGUOUS_DISPOSITIONS = ("activate-with-clarification", "decline-with-boundary")
ALLOWED_ROOT_KEYS = {
    "schema_version",
    "scope",
    "non_claims",
    "activation_surface",
    "cases",
}
REQUIRED_NON_CLAIMS = (
    "not_live_host_behavior_proof",
    "not_installed_skill_trigger_proof",
    "not_release_evidence",
)
ALLOWED_ACTIVATION_SURFACE_KEYS = {"source_path", "description_tokens"}
ALLOWED_CASE_KEYS = {
    "id",
    "prompt",
    "expected_class",
    "rationale",
    "activation_surface_tokens",
    "ambiguous_disposition",
    "notes",
}
CASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MIN_RATIONALE_CHARS = 20


def extract_frontmatter_description(skill_md_text: str) -> str | None:
    """Extract the YAML frontmatter description without a YAML dependency.

    Supports plain scalars and folded/literal block scalars for the
    `description:` key inside the first `---` delimited frontmatter block.
    """
    lines = skill_md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    parts: list[str] = []
    in_description = False
    for raw in lines[1:end]:
        if not in_description:
            match = re.match(r"^description:\s*(.*)$", raw)
            if match:
                in_description = True
                tail = match.group(1).strip()
                if tail and tail not in {">", ">-", ">+", "|", "|-", "|+"}:
                    parts.append(tail)
            continue
        if raw and not raw[0].isspace():
            break
        stripped = raw.strip()
        if stripped:
            parts.append(stripped)
    if not parts:
        return None
    return " ".join(parts)


def normalize_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", prompt.strip().casefold())


def validate_manifest(manifest: object, description: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest root must be a JSON object"]

    unknown_root = sorted(set(manifest) - ALLOWED_ROOT_KEYS)
    if unknown_root:
        errors.append(f"unexpected root keys: {unknown_root}")
    missing_root = sorted(ALLOWED_ROOT_KEYS - set(manifest))
    if missing_root:
        errors.append(f"missing root keys: {missing_root}")
        return errors

    if manifest["schema_version"] != 1:
        errors.append("schema_version must be 1")
    if not isinstance(manifest["scope"], str) or not manifest["scope"].strip():
        errors.append("scope must be a non-empty string")

    non_claims = manifest["non_claims"]
    if not isinstance(non_claims, dict):
        errors.append("non_claims must be an object")
    else:
        for key in REQUIRED_NON_CLAIMS:
            if non_claims.get(key) is not True:
                errors.append(f"non_claims.{key} must be present and true")

    surface = manifest["activation_surface"]
    declared_tokens: list[str] = []
    if not isinstance(surface, dict):
        errors.append("activation_surface must be an object")
    else:
        unknown_surface = sorted(set(surface) - ALLOWED_ACTIVATION_SURFACE_KEYS)
        if unknown_surface:
            errors.append(f"activation_surface unexpected keys: {unknown_surface}")
        if surface.get("source_path") != CANONICAL_SKILL_SOURCE:
            errors.append(
                "activation_surface.source_path must be "
                f"'{CANONICAL_SKILL_SOURCE}'"
            )
        tokens = surface.get("description_tokens")
        if not isinstance(tokens, list) or not tokens:
            errors.append("activation_surface.description_tokens must be a non-empty list")
        else:
            seen_tokens: set[str] = set()
            description_fold = description.casefold()
            for token in tokens:
                if not isinstance(token, str) or not token.strip():
                    errors.append("description_tokens entries must be non-empty strings")
                    continue
                fold = token.casefold()
                if fold in seen_tokens:
                    errors.append(f"duplicate description token: {token}")
                seen_tokens.add(fold)
                if fold not in description_fold:
                    errors.append(
                        f"declared token not found in skill description: {token}"
                    )
                declared_tokens.append(fold)

    cases = manifest["cases"]
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        return errors

    ids_seen: set[str] = set()
    prompt_class: dict[str, tuple[str, str]] = {}
    class_counts = {name: 0 for name in EXPECTED_CLASSES}
    covered_tokens: set[str] = set()

    for index, case in enumerate(cases):
        label = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label}: case must be an object")
            continue
        unknown_keys = sorted(set(case) - ALLOWED_CASE_KEYS)
        if unknown_keys:
            errors.append(
                f"{label}: unexpected keys {unknown_keys}; manifest rows must not "
                "carry live host behavior fields"
            )

        case_id = case.get("id")
        if not isinstance(case_id, str) or not CASE_ID_RE.match(case_id):
            errors.append(f"{label}: id must match {CASE_ID_RE.pattern}")
        elif case_id in ids_seen:
            errors.append(f"{label}: duplicate id '{case_id}'")
        else:
            ids_seen.add(case_id)
            label = f"cases[{case_id}]"

        prompt = case.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{label}: prompt must be a non-empty string")
            prompt = ""
        expected = case.get("expected_class")
        if expected not in EXPECTED_CLASSES:
            errors.append(
                f"{label}: expected_class must be one of {list(EXPECTED_CLASSES)}"
            )
            expected = None
        else:
            class_counts[expected] += 1

        if prompt:
            norm = normalize_prompt(prompt)
            if norm in prompt_class:
                prior_id, prior_class = prompt_class[norm]
                if expected is not None and prior_class != expected:
                    errors.append(
                        f"{label}: contradictory duplicate prompt of "
                        f"'{prior_id}' with different expected_class"
                    )
                else:
                    errors.append(
                        f"{label}: duplicate prompt of '{prior_id}'"
                    )
            elif expected is not None:
                prompt_class[norm] = (case_id or label, expected)

        rationale = case.get("rationale")
        if not isinstance(rationale, str) or len(rationale.strip()) < MIN_RATIONALE_CHARS:
            errors.append(
                f"{label}: rationale must be a string of at least "
                f"{MIN_RATIONALE_CHARS} characters"
            )

        tokens = case.get("activation_surface_tokens")
        disposition = case.get("ambiguous_disposition")

        if expected == "should-trigger":
            if disposition is not None:
                errors.append(f"{label}: ambiguous_disposition is ambiguous-only")
            if not isinstance(tokens, list) or not tokens:
                errors.append(
                    f"{label}: should-trigger cases need activation_surface_tokens"
                )
                tokens = []
        elif expected == "should-not-trigger":
            if disposition is not None:
                errors.append(f"{label}: ambiguous_disposition is ambiguous-only")
            if tokens not in (None, []):
                errors.append(
                    f"{label}: should-not-trigger cases must not claim "
                    "activation_surface_tokens"
                )
            tokens = []
        elif expected == "ambiguous-trigger":
            if disposition not in AMBIGUOUS_DISPOSITIONS:
                errors.append(
                    f"{label}: ambiguous-trigger cases need ambiguous_disposition "
                    f"in {list(AMBIGUOUS_DISPOSITIONS)}"
                )
            if tokens is None:
                tokens = []
            elif not isinstance(tokens, list):
                errors.append(f"{label}: activation_surface_tokens must be a list")
                tokens = []
        else:
            tokens = tokens if isinstance(tokens, list) else []

        for token in tokens:
            if not isinstance(token, str):
                errors.append(f"{label}: activation_surface_tokens entries must be strings")
                continue
            fold = token.casefold()
            if declared_tokens and fold not in declared_tokens:
                errors.append(
                    f"{label}: token '{token}' is not declared in "
                    "activation_surface.description_tokens"
                )
            elif expected == "should-trigger":
                covered_tokens.add(fold)

    for name in EXPECTED_CLASSES:
        if class_counts[name] == 0:
            errors.append(f"manifest must contain at least one {name} case")

    uncovered = [t for t in declared_tokens if t not in covered_tokens]
    if uncovered:
        errors.append(
            "declared description tokens lack should-trigger coverage: "
            f"{uncovered}"
        )

    return errors


def run_check(manifest_path: Path, skill_root: Path) -> int:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"trigger-eval manifest check: FAIL ({manifest_path}: {exc})")
        return 1

    skill_path = skill_root / CANONICAL_SKILL_SOURCE
    try:
        skill_text = skill_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"trigger-eval manifest check: FAIL (cannot read {skill_path}: {exc})")
        return 1
    description = extract_frontmatter_description(skill_text)
    if description is None:
        print(
            "trigger-eval manifest check: FAIL "
            f"(no frontmatter description found in {skill_path})"
        )
        return 1

    errors = validate_manifest(manifest, description)
    if errors:
        for error in errors:
            print(f"- {error}")
        print(f"trigger-eval manifest check: FAIL ({len(errors)} errors)")
        return 1

    cases = manifest["cases"]
    counts = {name: 0 for name in EXPECTED_CLASSES}
    for case in cases:
        counts[case["expected_class"]] += 1
    token_count = len(manifest["activation_surface"]["description_tokens"])
    print("trigger-eval manifest check: PASS")
    print(
        f"Cases checked: {len(cases)} "
        f"(should-trigger: {counts['should-trigger']}, "
        f"should-not-trigger: {counts['should-not-trigger']}, "
        f"ambiguous-trigger: {counts['ambiguous-trigger']})"
    )
    print(f"Declared activation tokens covered: {token_count}/{token_count}")
    return 0


def _good_manifest() -> dict:
    return {
        "schema_version": 1,
        "scope": "self-test taxonomy",
        "non_claims": {
            "not_live_host_behavior_proof": True,
            "not_installed_skill_trigger_proof": True,
            "not_release_evidence": True,
        },
        "activation_surface": {
            "source_path": CANONICAL_SKILL_SOURCE,
            "description_tokens": ["theological", "objection"],
        },
        "cases": [
            {
                "id": "st-sample",
                "prompt": "A theological objection sample prompt.",
                "expected_class": "should-trigger",
                "rationale": "Names a live theological objection directly.",
                "activation_surface_tokens": ["theological", "objection"],
            },
            {
                "id": "snt-sample",
                "prompt": "Fix my failing unit test in pytest.",
                "expected_class": "should-not-trigger",
                "rationale": "Pure software engineering request with no noetic burden.",
            },
            {
                "id": "amb-sample",
                "prompt": "What do you think about religion?",
                "expected_class": "ambiguous-trigger",
                "rationale": "Underdetermined probe; clarification must precede diagnosis.",
                "ambiguous_disposition": "activate-with-clarification",
            },
        ],
    }


SELF_TEST_DESCRIPTION = (
    "Activate for theological and objection prompts in the self-test surface."
)


def run_self_test() -> int:
    failures: list[str] = []

    good = _good_manifest()
    good_errors = validate_manifest(good, SELF_TEST_DESCRIPTION)
    if good_errors:
        failures.append(f"good manifest unexpectedly failed: {good_errors}")

    def expect_error(mutate, expected_substring: str, name: str) -> None:
        manifest = _good_manifest()
        mutate(manifest)
        errors = validate_manifest(manifest, SELF_TEST_DESCRIPTION)
        if not any(expected_substring in error for error in errors):
            failures.append(
                f"self-test '{name}' did not produce expected error "
                f"'{expected_substring}'; got {errors}"
            )

    expect_error(
        lambda m: m.update({"observed_behavior": "fired"}),
        "unexpected root keys",
        "root live-claim key",
    )
    expect_error(
        lambda m: m.update({"schema_version": 2}),
        "schema_version must be 1",
        "schema version",
    )
    expect_error(
        lambda m: m["non_claims"].update({"not_live_host_behavior_proof": False}),
        "non_claims.not_live_host_behavior_proof",
        "non-claims flag",
    )
    expect_error(
        lambda m: m["activation_surface"]["description_tokens"].append("memetics"),
        "not found in skill description",
        "undeclared description token",
    )
    expect_error(
        lambda m: m["cases"].append(dict(m["cases"][0])),
        "duplicate id",
        "duplicate id",
    )

    def contradictory(m: dict) -> None:
        clone = dict(m["cases"][0])
        clone["id"] = "st-sample-clone"
        clone["expected_class"] = "should-not-trigger"
        clone.pop("activation_surface_tokens", None)
        m["cases"].append(clone)

    expect_error(contradictory, "contradictory duplicate prompt", "contradictory prompt")
    expect_error(
        lambda m: m["cases"][0].update({"expected_class": "maybe"}),
        "expected_class must be one of",
        "controlled vocabulary",
    )
    expect_error(
        lambda m: m["cases"][0].update({"rationale": "too short"}),
        "rationale must be a string",
        "rationale floor",
    )
    expect_error(
        lambda m: m["cases"][0].pop("activation_surface_tokens"),
        "need activation_surface_tokens",
        "should-trigger tokens required",
    )
    expect_error(
        lambda m: m["cases"][1].update({"activation_surface_tokens": ["objection"]}),
        "must not claim",
        "should-not-trigger token ban",
    )
    expect_error(
        lambda m: m["cases"][2].pop("ambiguous_disposition"),
        "need ambiguous_disposition",
        "ambiguous disposition required",
    )
    expect_error(
        lambda m: m["cases"][0].update({"activation_surface_tokens": ["theological"]}),
        "lack should-trigger coverage",
        "token coverage",
    )
    expect_error(
        lambda m: m["cases"][0].update({"host_result": "activated"}),
        "unexpected keys",
        "case live-claim key",
    )

    if failures:
        for failure in failures:
            print(f"- {failure}")
        print(f"trigger-eval manifest self-test: FAIL ({len(failures)} failures)")
        return 1
    print("trigger-eval manifest self-test: PASS")
    print("Good manifests checked: 1")
    print("Invalid manifests checked: 13")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    return run_check(args.manifest, args.root)


if __name__ == "__main__":
    sys.exit(main())
