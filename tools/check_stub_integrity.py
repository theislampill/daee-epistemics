#!/usr/bin/env python3
"""Check canonical atomics source and compiled map integrity."""

from __future__ import annotations

import argparse
import re
import sys

from compiled_runtime_lib import (
    LEGACY_SOURCE_ROOT_REL,
    SOURCE_ROOT_REL,
    catalogue_by_id,
    fail_with_errors,
    parse_frontmatter,
    repo_root,
    source_path_for,
    source_rel_from_legacy,
    source_root,
)


DIAGNOSTIC_IR_REL = f"{SOURCE_ROOT_REL}/references/diagnostics/diagnostic-ir.md"
HISTORICAL_TRUNCATION_END = "Framing notes: do not treat anatta as simple mate"
BUDDHIST_ANATTA_HEADING = "### 6. Buddhist anatta / impermanence"
PIPELINE_CONNECTION_HEADING = "## Connection to Framework Pipeline"
FAILURE_TESTS_HEADING = "## Failure Tests"
FENCE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")


def markdown_source_errors(raw: bytes, rel: str) -> list[str]:
    """Return byte- and structure-level errors for canonical Markdown source."""
    errors: list[str] = []
    if not raw.endswith(b"\n"):
        errors.append(f"{rel}: canonical Markdown must end with a deliberate final LF")

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        errors.append(f"{rel}: canonical Markdown is not strict UTF-8: {exc}")
        return errors

    lines = text.splitlines()
    open_fence: tuple[str, int, int] | None = None
    fence_spans: list[tuple[int, int]] = []
    outside_lines: set[int] = set()
    for line_number, line in enumerate(lines, start=1):
        match = FENCE_RE.match(line)
        if open_fence is None and not match:
            outside_lines.add(line_number)
            continue
        if not match:
            continue
        fence = match.group("fence")
        rest = match.group("rest")
        marker = fence[0]
        if open_fence is not None:
            open_marker, open_length, _open_line = open_fence
            if marker == open_marker and len(fence) >= open_length and not rest.strip():
                fence_spans.append((_open_line, line_number))
                open_fence = None
            continue
        if marker == "`" and "`" in rest:
            outside_lines.add(line_number)
            continue
        open_fence = (marker, len(fence), line_number)

    if open_fence is not None:
        marker, length, line_number = open_fence
        errors.append(
            f"{rel}: unclosed fenced block opened at line {line_number} "
            f"with {length} {marker!r} markers"
        )

    if rel.replace("\\", "/") == DIAGNOSTIC_IR_REL:
        stripped = text.rstrip("\r\n")
        if stripped.endswith(HISTORICAL_TRUNCATION_END):
            errors.append(f"{rel}: ends at the historical truncation boundary")

        def outside_exact(value: str) -> list[int]:
            return [line_number for line_number in sorted(outside_lines) if lines[line_number - 1] == value]

        def next_nonblank(after: int) -> int | None:
            return next(
                (line_number for line_number in range(after + 1, len(lines) + 1) if lines[line_number - 1].strip()),
                None,
            )

        def previous_nonblank(before: int) -> int | None:
            return next(
                (line_number for line_number in range(before - 1, 0, -1) if lines[line_number - 1].strip()),
                None,
            )

        buddhist_headings = outside_exact(BUDDHIST_ANATTA_HEADING)
        connection_headings = outside_exact(PIPELINE_CONNECTION_HEADING)
        failure_headings = outside_exact(FAILURE_TESTS_HEADING)
        terminal_bullets = [
            line_number
            for line_number in sorted(outside_lines)
            if lines[line_number - 1].startswith("- ")
            and "recursion_decision: STOP" in lines[line_number - 1]
            and "next_eligible_pass: none" in lines[line_number - 1]
        ]
        outside_h2s = [
            (line_number, lines[line_number - 1])
            for line_number in sorted(outside_lines)
            if lines[line_number - 1].startswith("## ")
        ]
        last_nonblank = next(
            (line_number for line_number in range(len(lines), 0, -1) if lines[line_number - 1].strip()),
            None,
        )

        buddhist_span: tuple[int, int] | None = None
        boundary_ok = False
        if len(buddhist_headings) == 1:
            expected_open = next_nonblank(buddhist_headings[0])
            buddhist_span = next((span for span in fence_spans if span[0] == expected_open), None)
            if buddhist_span is not None:
                boundary_line = previous_nonblank(buddhist_span[1])
                boundary_ok = (
                    boundary_line is not None
                    and buddhist_span[0] < boundary_line < buddhist_span[1]
                    and lines[boundary_line - 1].startswith("Must not dump:")
                )

        has_terminal_end = (
            buddhist_span is not None
            and boundary_ok
            and len(connection_headings) == 1
            and len(failure_headings) == 1
            and len(terminal_bullets) == 1
            and buddhist_headings[0]
            < buddhist_span[0]
            < buddhist_span[1]
            < connection_headings[0]
            < failure_headings[0]
            < terminal_bullets[0]
            and outside_h2s
            and outside_h2s[-1] == (failure_headings[0], FAILURE_TESTS_HEADING)
            and terminal_bullets[0] == last_nonblank
        )
        if not has_terminal_end:
            errors.append(
                f"{rel}: missing the expected terminal Failure Tests ending outside fenced blocks "
                "or Buddhist-anatta fence boundary/order is invalid"
            )

    return errors


def self_test() -> int:
    root = repo_root()
    fixtures = root / "tests" / "source-integrity" / "fixtures"
    positive = (fixtures / "valid" / "diagnostic-ir-intact.md").read_bytes()
    historical = (fixtures / "invalid" / "diagnostic-ir-historical-truncation.md").read_bytes()
    relocated_close = (fixtures / "invalid" / "diagnostic-ir-relocated-close.md").read_bytes()
    cases = [
        ("intact diagnostic-ir fixture passes", markdown_source_errors(positive, DIAGNOSTIC_IR_REL) == []),
        (
            "historical simple-mate truncation is rejected",
            any(
                "historical truncation boundary" in error
                for error in markdown_source_errors(historical, DIAGNOSTIC_IR_REL)
            ),
        ),
        (
            "historical unclosed fence is rejected",
            any("unclosed fenced block" in error for error in markdown_source_errors(historical, DIAGNOSTIC_IR_REL)),
        ),
        (
            "historical truncation fixture preserves the observed final LF",
            not any("final LF" in error for error in markdown_source_errors(historical, DIAGNOSTIC_IR_REL)),
        ),
        (
            "relocated close cannot swallow terminal headings",
            any(
                "outside fenced blocks" in error
                for error in markdown_source_errors(relocated_close, DIAGNOSTIC_IR_REL)
            ),
        ),
        (
            "invalid UTF-8 is rejected",
            any("strict UTF-8" in error for error in markdown_source_errors(positive + b"\xff\n", DIAGNOSTIC_IR_REL)),
        ),
        (
            "missing final LF is rejected",
            any("final LF" in error for error in markdown_source_errors(positive.rstrip(b"\n"), DIAGNOSTIC_IR_REL)),
        ),
    ]
    passed = all(ok for _name, ok in cases)
    for name, ok in cases:
        print(f"  self-test {'PASS' if ok else 'FAIL'}: {name}")
    print(f"stub/source integrity self-test: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def live_check() -> int:
    root = repo_root()
    errors: list[str] = []
    atomics_root = source_root(root)
    references_root = atomics_root / "references"
    source_skill = atomics_root / "SKILL.md"
    if not source_skill.is_file():
        errors.append("atomics/skill/SKILL.md is absent")
    else:
        raw = source_skill.read_bytes()
        errors.extend(markdown_source_errors(raw, source_skill.relative_to(root).as_posix()))
        try:
            parse_frontmatter(raw.decode("utf-8", errors="strict"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"atomics/skill/SKILL.md: YAML front matter missing or invalid: {exc}")

    if not references_root.is_dir():
        return fail_with_errors("stub/source integrity", ["atomics/skill/references is absent"])

    for path in sorted(references_root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        source_relative = path.relative_to(atomics_root).as_posix()
        legacy_rel = f"{LEGACY_SOURCE_ROOT_REL}/{source_relative}"
        raw = path.read_bytes()
        errors.extend(markdown_source_errors(raw, rel))
        try:
            text = raw.decode("utf-8", errors="strict")
            data, _raw, _body = parse_frontmatter(text)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{rel}: YAML front matter missing or invalid: {exc}")
            continue
        if data.get("canonical_path") not in {rel, legacy_rel}:
            errors.append(f"{rel}: canonical_path mismatch: {data.get('canonical_path')!r}")
        if not data.get("id"):
            errors.append(f"{rel}: missing id")
        if not data.get("module_class"):
            errors.append(f"{rel}: missing module_class")

    for module_id, entry in sorted(catalogue_by_id(root).items()):
        rel = entry.get("path", "")
        path = source_path_for(root, rel)
        physical_rel = f"{SOURCE_ROOT_REL}/{source_rel_from_legacy(rel)}"
        if not path.is_file():
            errors.append(f"catalogue path missing for {module_id}: {rel}")
            continue
        try:
            data, _raw, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{rel}: catalogue source has invalid YAML: {exc}")
            continue
        if physical_rel != path.relative_to(root).as_posix():
            errors.append(f"{rel}: resolved source path mismatch: {physical_rel}")
        if data.get("id") != module_id:
            errors.append(f"{rel}: YAML id {data.get('id')!r} != catalogue id {module_id!r}")
        if data.get("module_class") != entry.get("module_class"):
            errors.append(
                f"{rel}: YAML class {data.get('module_class')!r} != catalogue class {entry.get('module_class')!r}"
            )

    return fail_with_errors("stub/source integrity", errors)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check canonical atomics source and compiled map integrity")
    parser.add_argument("--self-test", action="store_true", help="run deterministic source-integrity canaries")
    args = parser.parse_args()
    return self_test() if args.self_test else live_check()


if __name__ == "__main__":
    sys.exit(main())
