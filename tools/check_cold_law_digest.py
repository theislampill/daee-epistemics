#!/usr/bin/env python3
"""Cold-law digest anti-theater gate.

skill/cold-law-manifest.json (schema daee-cold-law-manifest-v1) binds clause
digests in the compiled root to cold source spans in
references/rubrics/non-droppable-manual-contract.md (shipped verbatim at
skill/references/rubrics/non-droppable-manual-contract.md, canonical source at
atomics/skill/references/rubrics/non-droppable-manual-contract.md, delimited by
<!-- COLD-LAW-CLAUSE: clause.<id> --> ... <!-- END-COLD-LAW-CLAUSE: clause.<id> -->
anchors). This checker proves that binding is not theater: every clause is
schema-complete, hash-bound to the exact anchored span in both the shipped
cold copy and the atomics source, checker-enforced (or explicitly advisory),
wired into the real CI command list (not just mapped and forgotten), and
digest-referenced from the compiled root (no clause the hot digest silently
never points a reader/model at; no dangling pointer to a clause that does not
exist).

Modes:
  python tools/check_cold_law_digest.py              validate the live repo
  python tools/check_cold_law_digest.py --self-test   synthetic fixtures prove
                                                       each check fails on the
                                                       right bad input, plus a
                                                       live-repo PASS

The eight checks (each reports a clear first-failure message):
  1. MANIFEST PRESENT + SCHEMA
  2. HASH PARITY                    (cold-law-clause-hash-drift)
  3. CHECKER MAPPING                (cold-law-clause-missing-checker)
  4. DIGEST REFERENCE PARITY        (cold-law-pointer-without-digest)
  5. COLD COPY VERBATIM
  6. ADVISORY BUDGET
  7. CLAUSE-ID ALLOWLIST            (cold-law-clause-id-drift)
  8. REVERSE ANCHOR PARITY          (cold-law-anchor-without-manifest)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR_NAME = "tools"

MANIFEST_REL = "skill/cold-law-manifest.json"
COLD_COPY_REL = "skill/references/rubrics/non-droppable-manual-contract.md"
ATOMICS_SOURCE_REL = "atomics/skill/references/rubrics/non-droppable-manual-contract.md"
DIGEST_ROOT_REL = "skill/SKILL.md"
CI_RUNNER_REL = "tools/run_local_ci.py"

EXPECTED_SCHEMA = "daee-cold-law-manifest-v1"
REQUIRED_CLAUSE_KEYS = ("span_lines", "sha256", "checkers", "load_when", "advisory")

# Deliberate-update pattern (mirrors the manifest generator's own
# advisory=True gate): a new advisory clause must not silently slip in. Any
# addition here requires explicit owner sign-off in the same change.
EXPECTED_ADVISORY_CLAUSES = ["clause.preamble-size-partial"]

# Deliberate-update pattern (mirrors EXPECTED_ADVISORY_CLAUSES above): the
# frozen set of clause ids the live manifest is allowed to bind. A coordinated
# removal (delete the manifest entry + both COLD-LAW-CLAUSE anchor pairs + the
# digest pointer) previously passed all checks with zero errors, because
# nothing ever asserted what the *complete* clause-id set should be -- only
# that whatever clauses existed were internally consistent. Any addition or
# removal requires explicit owner-visible justification and a deliberate
# update of this constant in the same change.
EXPECTED_CLAUSE_IDS = frozenset(
    [
        "clause.preamble-size-partial",
        "clause.banner",
        "clause.layer-a-ledger",
        "clause.concealment-mode",
        "clause.canonical-notation",
        "clause.mrp-block-grammar",
        "clause.held-burden-activation",
        "clause.owner-ttp-route",
        "clause.no-burden-shrink",
        "clause.proof-tail-order",
        "clause.field-witness-spec",
        "clause.execution-mandate-detail",
        "clause.output-surface-invariant",
    ]
)

CLAUSE_START_RE = re.compile(r"^<!-- COLD-LAW-CLAUSE: (clause\.[a-z0-9-]+) -->\s*$")
CLAUSE_END_RE = re.compile(r"^<!-- END-COLD-LAW-CLAUSE: (clause\.[a-z0-9-]+) -->\s*$")
POINTER_RE = re.compile(r"cold-law (clause\.[a-z0-9-]+)")


@dataclass(frozen=True)
class Layout:
    """Filesystem layout for one validation run (live repo or a fixture)."""

    label: str
    manifest_path: Path
    cold_copy_path: Path
    atomics_source_path: Path
    digest_root_path: Path
    tools_dir: Path
    ci_commands_text: str
    # ADVISORY BUDGET (check 6) is a live-repo-specific, hardcoded-list
    # invariant (see EXPECTED_ADVISORY_CLAUSES); it does not generalize to
    # synthetic fixtures with unrelated clause ids. None disables the check
    # for a given layout so fixtures can exercise checks 1-5 without being
    # judged against the real repo's clause-id list. The dedicated
    # invalid/unexpected-advisory fixture exercises check 6 directly by
    # passing its own expected list.
    expected_advisory: list[str] | None = None
    # CLAUSE-ID ALLOWLIST (check 7) is the same kind of live-repo-specific,
    # hardcoded-list invariant as expected_advisory above (see
    # EXPECTED_CLAUSE_IDS): it does not generalize to synthetic fixtures using
    # unrelated clause ids. None disables the check for a given layout so
    # fixtures can exercise checks 1-6 and 8 without being judged against the
    # real repo's clause-id list. The dedicated invalid/clause-removed fixture
    # exercises check 7 directly by passing its own expected set.
    expected_clause_ids: frozenset[str] | None = None


def live_layout() -> Layout:
    return Layout(
        label="live repo",
        manifest_path=ROOT / MANIFEST_REL,
        cold_copy_path=ROOT / COLD_COPY_REL,
        atomics_source_path=ROOT / ATOMICS_SOURCE_REL,
        digest_root_path=ROOT / DIGEST_ROOT_REL,
        tools_dir=ROOT / TOOLS_DIR_NAME,
        ci_commands_text=(ROOT / CI_RUNNER_REL).read_text(encoding="utf-8"),
        expected_advisory=EXPECTED_ADVISORY_CLAUSES,
        expected_clause_ids=EXPECTED_CLAUSE_IDS,
    )


def fixture_layout(
    fixture_dir: Path,
    expected_advisory: list[str] | None = None,
    expected_clause_ids: frozenset[str] | None = None,
) -> Layout:
    ci_commands_path = fixture_dir / "ci_commands.txt"
    return Layout(
        label=fixture_dir.name,
        expected_advisory=expected_advisory,
        expected_clause_ids=expected_clause_ids,
        manifest_path=fixture_dir / "manifest.json",
        cold_copy_path=fixture_dir / "cold_copy.md",
        atomics_source_path=fixture_dir / "cold.md",
        digest_root_path=fixture_dir / "root.md",
        tools_dir=fixture_dir / "tools_dir",
        ci_commands_text=ci_commands_path.read_text(encoding="utf-8") if ci_commands_path.is_file() else "",
    )


# ---------------------------------------------------------------------------
# Pure core: each function takes already-loaded data and returns a list of
# error strings (empty = pass). Kept separate from filesystem I/O so the
# self-test can drive them directly with synthetic bad inputs, and so the
# live run and fixture runs share one implementation.
# ---------------------------------------------------------------------------


def check_manifest_schema(manifest: object) -> list[str]:
    """Check 1: MANIFEST PRESENT + SCHEMA."""
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["cold-law manifest is not a JSON object"]
    if manifest.get("schema") != EXPECTED_SCHEMA:
        errors.append(
            f"cold-law manifest schema field is {manifest.get('schema')!r}, expected {EXPECTED_SCHEMA!r}"
        )
    clauses = manifest.get("clauses")
    if not isinstance(clauses, dict) or not clauses:
        errors.append("cold-law manifest has no non-empty 'clauses' object")
        return errors
    for clause_id, entry in clauses.items():
        if not isinstance(entry, dict):
            errors.append(f"{clause_id}: manifest entry is not an object")
            continue
        missing = [key for key in REQUIRED_CLAUSE_KEYS if key not in entry]
        if missing:
            errors.append(f"{clause_id}: manifest entry missing key(s): {missing}")
    return errors


def parse_clause_spans(text: str) -> tuple[dict[str, tuple[int, int, str]], list[str]]:
    """Parse COLD-LAW-CLAUSE anchors out of cold source text.

    Returns (clause_id -> (start_line, end_line, span_text), errors). Mirrors
    tools/build_compiled_runtime.py's build_cold_law_manifest span/hash
    convention exactly: span_lines are 1-indexed [first content line, anchor
    comment closing line]; the hashed text is the exact join of lines
    strictly between the anchors (anchors excluded), joined with "\\n".
    """
    lines = text.split("\n")
    spans: dict[str, tuple[int, int, str]] = {}
    errors: list[str] = []
    current: str | None = None
    current_start_line = 0
    buf: list[str] = []
    for index, line in enumerate(lines):
        start_match = CLAUSE_START_RE.match(line)
        if start_match:
            if current is not None:
                errors.append(f"nested cold-law-clause anchor at line {index + 1}: {current}")
                continue
            current = start_match.group(1)
            current_start_line = index + 2
            buf = []
            continue
        end_match = CLAUSE_END_RE.match(line)
        if end_match:
            clause_id = end_match.group(1)
            if current is None:
                errors.append(f"unmatched end anchor at line {index + 1}: {clause_id}")
                continue
            if clause_id != current:
                errors.append(
                    f"mismatched end anchor at line {index + 1}: expected {current!r}, found {clause_id!r}"
                )
                current = None
                buf = []
                continue
            span_text = "\n".join(buf)
            spans[clause_id] = (current_start_line, index, span_text)
            current = None
            buf = []
            continue
        if current is not None:
            buf.append(line)
    if current is not None:
        errors.append(f"unclosed cold-law-clause anchor: {current}")
    return spans, errors


def check_hash_parity(
    clauses: dict[str, dict],
    cold_copy_spans: dict[str, tuple[int, int, str]],
    atomics_spans: dict[str, tuple[int, int, str]],
) -> list[str]:
    """Check 2: HASH PARITY (cold-law-clause-hash-drift)."""
    errors: list[str] = []
    for clause_id, entry in sorted(clauses.items()):
        manifest_sha = entry.get("sha256")
        manifest_span = entry.get("span_lines")
        for source_label, spans in (("shipped cold copy", cold_copy_spans), ("atomics source", atomics_spans)):
            if clause_id not in spans:
                errors.append(f"{clause_id}: no COLD-LAW-CLAUSE anchor found in {source_label}")
                continue
            start_line, end_line, span_text = spans[clause_id]
            if manifest_span != [start_line, end_line]:
                errors.append(
                    f"{clause_id}: manifest span_lines {manifest_span} does not match anchor-delimited "
                    f"span in {source_label} [{start_line}, {end_line}] "
                    "(cold-law-clause-hash-drift)"
                )
                continue
            actual_sha = hashlib.sha256(span_text.encode("utf-8")).hexdigest()
            if actual_sha != manifest_sha:
                errors.append(
                    f"{clause_id}: sha256 drift against {source_label}: "
                    f"manifest={manifest_sha} actual={actual_sha} (cold-law-clause-hash-drift)"
                )
    return errors


def check_checker_mapping(
    clauses: dict[str, dict],
    existing_tool_files: set[str],
    ci_wired_files: set[str],
) -> list[str]:
    """Check 3: CHECKER MAPPING (cold-law-clause-missing-checker)."""
    errors: list[str] = []
    for clause_id, entry in sorted(clauses.items()):
        checkers = entry.get("checkers") or []
        advisory = bool(entry.get("advisory"))
        if not checkers:
            if not advisory:
                errors.append(
                    f"{clause_id}: no checkers and advisory is not true "
                    "(cold-law-clause-missing-checker)"
                )
            continue
        for checker in checkers:
            checker_name = Path(checker).name
            if checker_name not in existing_tool_files:
                errors.append(
                    f"{clause_id}: checker {checker!r} does not exist as a file under tools/ "
                    "(cold-law-clause-missing-checker)"
                )
                continue
            if checker_name not in ci_wired_files:
                errors.append(
                    f"{clause_id}: checker {checker!r} exists but its filename never appears in "
                    "the CI command list -- mapped but never run is theater "
                    "(cold-law-clause-missing-checker)"
                )
    return errors


def check_digest_reference_parity(clauses: dict[str, dict], digest_text: str) -> list[str]:
    """Check 4: DIGEST REFERENCE PARITY (cold-law-pointer-without-digest)."""
    errors: list[str] = []
    referenced = set(POINTER_RE.findall(digest_text))
    for clause_id in sorted(clauses):
        if clause_id not in referenced:
            errors.append(
                f"{clause_id}: compiled root has no literal 'cold-law {clause_id}' pointer "
                "(cold-law-pointer-without-digest)"
            )
    for pointer_id in sorted(referenced):
        if pointer_id not in clauses:
            errors.append(
                f"{pointer_id}: compiled root contains a 'cold-law {pointer_id}' pointer with no "
                "manifest entry -- dangling pointer (cold-law-pointer-without-digest)"
            )
    return errors


def check_cold_copy_verbatim(cold_copy_bytes: bytes, atomics_bytes: bytes) -> list[str]:
    """Check 5: COLD COPY VERBATIM.

    tools/build_compiled_runtime.py's RUNTIME_METADATA_COPIES loop copies this
    file with metadata_out.write_bytes(source_path.read_bytes()) -- a raw byte
    copy, with no frontmatter stripping (unlike generated_skill_text's
    handling of the manual-contract-digest.md front matter). The invariant is
    therefore byte-for-byte identity of the whole file, not identity after
    stripping front matter.
    """
    if cold_copy_bytes != atomics_bytes:
        return [
            "shipped cold copy is not byte-for-byte identical to the atomics source "
            "(RUNTIME_METADATA_COPIES ships this file as a raw byte copy)"
        ]
    return []


def check_advisory_budget(clauses: dict[str, dict], expected_advisory_list: list[str]) -> list[str]:
    """Check 6: ADVISORY BUDGET."""
    actual_advisory = sorted(clause_id for clause_id, entry in clauses.items() if entry.get("advisory"))
    expected_advisory = sorted(expected_advisory_list)
    if actual_advisory != expected_advisory:
        return [
            f"advisory clause set drifted from the expected list: actual={actual_advisory} "
            f"expected={expected_advisory} -- a new advisory clause requires deliberate owner "
            "sign-off and an update to EXPECTED_ADVISORY_CLAUSES"
        ]
    return []


def check_clause_id_allowlist(clauses: dict[str, dict], expected_clause_ids: frozenset[str]) -> list[str]:
    """Check 7: CLAUSE-ID ALLOWLIST (cold-law-clause-id-drift).

    Closes the coordinated-removal blind spot: deleting a manifest entry plus
    both COLD-LAW-CLAUSE anchor pairs plus the digest pointer previously
    passed checks 1-6 with zero errors, because nothing ever asserted what the
    *complete* clause-id set should be. The live manifest's clause-id set must
    equal EXPECTED_CLAUSE_IDS exactly; missing or extra ids both fail.
    """
    actual = frozenset(clauses.keys())
    if actual == expected_clause_ids:
        return []
    missing = sorted(expected_clause_ids - actual)
    extra = sorted(actual - expected_clause_ids)
    return [
        f"manifest clause-id set drifted from EXPECTED_CLAUSE_IDS: missing={missing} extra={extra} "
        "-- clause removals or additions require a deliberate update of EXPECTED_CLAUSE_IDS with "
        "owner-visible justification (cold-law-clause-id-drift)"
    ]


def check_reverse_anchor_parity(
    clauses: dict[str, dict],
    cold_copy_spans: dict[str, tuple[int, int, str]],
    atomics_spans: dict[str, tuple[int, int, str]],
) -> list[str]:
    """Check 8: REVERSE ANCHOR PARITY (cold-law-anchor-without-manifest).

    Closes the other half of the coordinated-removal blind spot: an anchor
    pair that still exists in the atomics source and/or the shipped cold copy
    but whose manifest entry was silently deleted (or never added) is a fail,
    even if every clause the manifest *does* know about is internally
    consistent.
    """
    errors: list[str] = []
    anchored_ids = set(cold_copy_spans) | set(atomics_spans)
    for clause_id in sorted(anchored_ids):
        if clause_id not in clauses:
            found_in = [
                label
                for label, spans in (("shipped cold copy", cold_copy_spans), ("atomics source", atomics_spans))
                if clause_id in spans
            ]
            errors.append(
                f"{clause_id}: COLD-LAW-CLAUSE anchor found in {', '.join(found_in)} but has no manifest "
                "entry -- anchored-but-unmanifested clause (cold-law-anchor-without-manifest)"
            )
    return errors


# ---------------------------------------------------------------------------
# Layout-driven orchestration (shared by live mode and fixture-backed
# self-test file cases).
# ---------------------------------------------------------------------------


def existing_tool_filenames(tools_dir: Path) -> set[str]:
    if not tools_dir.is_dir():
        return set()
    return {p.name for p in tools_dir.glob("*.py")}


def ci_wired_filenames(ci_commands_text: str) -> set[str]:
    return set(re.findall(r"([A-Za-z0-9_.\-]+\.py)", ci_commands_text))


def run_layout(layout: Layout) -> list[str]:
    errors: list[str] = []

    if not layout.manifest_path.is_file():
        return [f"[{layout.label}] manifest not found: {layout.manifest_path}"]
    try:
        manifest = json.loads(layout.manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"[{layout.label}] manifest is not valid JSON: {exc}"]

    schema_errors = check_manifest_schema(manifest)
    if schema_errors:
        return [f"[{layout.label}] {e}" for e in schema_errors]

    clauses: dict[str, dict] = manifest["clauses"]

    if not layout.cold_copy_path.is_file():
        return [f"[{layout.label}] shipped cold copy not found: {layout.cold_copy_path}"]
    if not layout.atomics_source_path.is_file():
        return [f"[{layout.label}] atomics/cold source not found: {layout.atomics_source_path}"]

    cold_copy_text = layout.cold_copy_path.read_text(encoding="utf-8")
    atomics_text = layout.atomics_source_path.read_text(encoding="utf-8")

    cold_copy_spans, cold_copy_parse_errors = parse_clause_spans(cold_copy_text)
    atomics_spans, atomics_parse_errors = parse_clause_spans(atomics_text)
    errors.extend(f"[{layout.label}] {e}" for e in cold_copy_parse_errors)
    errors.extend(f"[{layout.label}] {e}" for e in atomics_parse_errors)
    if errors:
        return errors

    errors.extend(f"[{layout.label}] {e}" for e in check_hash_parity(clauses, cold_copy_spans, atomics_spans))
    if errors:
        return errors

    errors.extend(
        f"[{layout.label}] {e}"
        for e in check_reverse_anchor_parity(clauses, cold_copy_spans, atomics_spans)
    )
    if errors:
        return errors

    existing_tools = existing_tool_filenames(layout.tools_dir)
    ci_wired = ci_wired_filenames(layout.ci_commands_text)
    errors.extend(f"[{layout.label}] {e}" for e in check_checker_mapping(clauses, existing_tools, ci_wired))
    if errors:
        return errors

    if not layout.digest_root_path.is_file():
        return [f"[{layout.label}] compiled root not found: {layout.digest_root_path}"]
    digest_text = layout.digest_root_path.read_text(encoding="utf-8")
    errors.extend(f"[{layout.label}] {e}" for e in check_digest_reference_parity(clauses, digest_text))
    if errors:
        return errors

    errors.extend(
        f"[{layout.label}] {e}"
        for e in check_cold_copy_verbatim(layout.cold_copy_path.read_bytes(), layout.atomics_source_path.read_bytes())
    )
    if errors:
        return errors

    if layout.expected_advisory is not None:
        errors.extend(f"[{layout.label}] {e}" for e in check_advisory_budget(clauses, layout.expected_advisory))
    if errors:
        return errors

    if layout.expected_clause_ids is not None:
        errors.extend(
            f"[{layout.label}] {e}" for e in check_clause_id_allowlist(clauses, layout.expected_clause_ids)
        )
    return errors


# ---------------------------------------------------------------------------
# Self-test: synthetic + fixture-backed cases proving each check fails on the
# right bad input, plus a live-repo PASS.
# ---------------------------------------------------------------------------

FIXTURES_DIR = ROOT / "tests" / "cold-law-fixtures"


def self_test() -> int:
    cases: list[tuple[str, bool]] = []

    # --- Embedded synthetic cases exercising the pure core directly ---

    good_manifest = {
        "schema": EXPECTED_SCHEMA,
        "generated": True,
        "source": "x.md",
        "clauses": {
            "clause.a": {
                "span_lines": [1, 1],
                "sha256": "deadbeef",
                "checkers": ["tools/check_x.py"],
                "load_when": "always",
                "advisory": False,
            }
        },
    }
    cases.append(("schema: valid manifest -> no errors", check_manifest_schema(good_manifest) == []))
    cases.append((
        "schema: wrong schema field flagged",
        any("schema field" in e for e in check_manifest_schema({**good_manifest, "schema": "wrong-v0"})),
    ))
    bad_entry_manifest = {
        **good_manifest,
        "clauses": {"clause.a": {"span_lines": [1, 1], "sha256": "deadbeef"}},
    }
    cases.append((
        "schema: missing required keys flagged",
        any("missing key" in e for e in check_manifest_schema(bad_entry_manifest)),
    ))

    cold_text = "pre\n<!-- COLD-LAW-CLAUSE: clause.a -->\nbody one\n<!-- END-COLD-LAW-CLAUSE: clause.a -->\npost\n"
    spans, parse_errors = parse_clause_spans(cold_text)
    cases.append(("parse: no parse errors on well-formed anchors", parse_errors == []))
    cases.append(("parse: clause.a span captured", spans.get("clause.a", (0, 0, ""))[2] == "body one"))

    good_sha = hashlib.sha256(b"body one").hexdigest()
    clauses_a = {"clause.a": {"span_lines": [3, 3], "sha256": good_sha}}
    cases.append((
        "hash parity: matching hash + span -> no errors",
        check_hash_parity(clauses_a, spans, spans) == [],
    ))
    tampered_spans, _ = parse_clause_spans(
        "pre\n<!-- COLD-LAW-CLAUSE: clause.a -->\nTAMPERED\n<!-- END-COLD-LAW-CLAUSE: clause.a -->\npost\n"
    )
    cases.append((
        "hash parity: tampered clause text -> hash drift flagged",
        any("cold-law-clause-hash-drift" in e for e in check_hash_parity(clauses_a, tampered_spans, spans)),
    ))
    cases.append((
        "hash parity: missing anchor in one source -> flagged",
        any("no COLD-LAW-CLAUSE anchor" in e for e in check_hash_parity(clauses_a, {}, spans)),
    ))

    cases.append((
        "checker mapping: advisory + empty checkers -> no errors",
        check_checker_mapping({"clause.b": {"checkers": [], "advisory": True}}, set(), set()) == [],
    ))
    cases.append((
        "checker mapping: empty checkers + advisory false -> flagged",
        any(
            "cold-law-clause-missing-checker" in e
            for e in check_checker_mapping({"clause.b": {"checkers": [], "advisory": False}}, set(), set())
        ),
    ))
    cases.append((
        "checker mapping: checker file does not exist -> flagged",
        any(
            "does not exist as a file" in e
            for e in check_checker_mapping(
                {"clause.c": {"checkers": ["tools/check_ghost.py"], "advisory": False}}, set(), set()
            )
        ),
    ))
    cases.append((
        "checker mapping: checker exists but unwired in CI -> flagged",
        any(
            "never appears in" in e
            for e in check_checker_mapping(
                {"clause.d": {"checkers": ["tools/check_real.py"], "advisory": False}},
                {"check_real.py"},
                set(),
            )
        ),
    ))
    cases.append((
        "checker mapping: checker exists and wired -> no errors",
        check_checker_mapping(
            {"clause.e": {"checkers": ["tools/check_real.py"], "advisory": False}},
            {"check_real.py"},
            {"check_real.py"},
        )
        == [],
    ))

    digest_ok = "some text cold-law clause.a more text"
    cases.append((
        "digest reference: pointer present -> no errors",
        check_digest_reference_parity({"clause.a": {}}, digest_ok) == [],
    ))
    cases.append((
        "digest reference: clause with no pointer -> flagged",
        any(
            "cold-law-pointer-without-digest" in e
            for e in check_digest_reference_parity({"clause.a": {}}, "nothing relevant here")
        ),
    ))
    cases.append((
        "digest reference: dangling pointer with no manifest entry -> flagged",
        any(
            "dangling pointer" in e
            for e in check_digest_reference_parity({}, "text with cold-law clause.ghost inside")
        ),
    ))

    cases.append(("cold copy verbatim: identical bytes -> no errors", check_cold_copy_verbatim(b"same", b"same") == []))
    cases.append((
        "cold copy verbatim: differing bytes -> flagged",
        check_cold_copy_verbatim(b"same", b"different") != [],
    ))

    cases.append((
        "advisory budget: exactly expected list -> no errors",
        check_advisory_budget(
            {cid: {"advisory": True} for cid in EXPECTED_ADVISORY_CLAUSES}, EXPECTED_ADVISORY_CLAUSES
        )
        == [],
    ))
    cases.append((
        "advisory budget: unexpected extra advisory clause -> flagged",
        any(
            "advisory clause set drifted" in e
            for e in check_advisory_budget(
                {
                    **{cid: {"advisory": True} for cid in EXPECTED_ADVISORY_CLAUSES},
                    "clause.surprise": {"advisory": True},
                },
                EXPECTED_ADVISORY_CLAUSES,
            )
        ),
    ))

    expected_ids_ab = frozenset({"clause.a", "clause.b"})
    cases.append((
        "clause-id allowlist: exact match -> no errors",
        check_clause_id_allowlist({"clause.a": {}, "clause.b": {}}, expected_ids_ab) == [],
    ))
    cases.append((
        "clause-id allowlist: coordinated removal (missing id) -> flagged",
        any(
            "cold-law-clause-id-drift" in e and "missing=['clause.b']" in e
            for e in check_clause_id_allowlist({"clause.a": {}}, expected_ids_ab)
        ),
    ))
    cases.append((
        "clause-id allowlist: undeclared extra id -> flagged",
        any(
            "cold-law-clause-id-drift" in e and "extra=['clause.c']" in e
            for e in check_clause_id_allowlist({"clause.a": {}, "clause.b": {}, "clause.c": {}}, expected_ids_ab)
        ),
    ))

    cases.append((
        "reverse anchor parity: every anchor manifested -> no errors",
        check_reverse_anchor_parity({"clause.a": {}}, spans, spans) == [],
    ))
    cases.append((
        "reverse anchor parity: anchor present, manifest silent -> flagged",
        any(
            "cold-law-anchor-without-manifest" in e
            for e in check_reverse_anchor_parity({}, spans, spans)
        ),
    ))
    cases.append((
        "reverse anchor parity: anchor in only one source, manifest silent -> flagged",
        any(
            "cold-law-anchor-without-manifest" in e
            for e in check_reverse_anchor_parity({}, spans, {})
        ),
    ))

    # --- Fixture-backed file cases (tests/cold-law-fixtures/) ---

    # Per-fixture ADVISORY BUDGET / CLAUSE-ID ALLOWLIST expectations. Both
    # checks are hardcoded-list invariants scoped to real clause ids (see
    # Layout.expected_advisory / Layout.expected_clause_ids), so each
    # synthetic fixture supplies its own small "expected" values rather than
    # the live repo's. `invalid/unexpected-advisory` passes an empty expected
    # advisory list precisely so its advisory clause is the unexpected one.
    # `invalid/clause-removed` passes an expected_clause_ids set that still
    # includes the removed clause, precisely so its coordinated removal is the
    # detected drift.
    fixture_cases: list[tuple[str, bool, list[str] | None, frozenset[str] | None]] = [
        ("valid", True, ["clause.beta-partial"], frozenset({"clause.alpha", "clause.beta-partial"})),
        ("invalid/hash-drift", False, None, None),
        ("invalid/empty-checkers-not-advisory", False, None, None),
        ("invalid/checker-file-missing", False, None, None),
        ("invalid/checker-unwired", False, None, None),
        ("invalid/digest-missing-pointer", False, None, None),
        ("invalid/dangling-pointer", False, None, None),
        ("invalid/unexpected-advisory", False, [], None),
        ("invalid/cold-copy-mismatch", False, None, None),
        (
            "invalid/clause-removed",
            False,
            None,
            frozenset({"clause.alpha", "clause.beta-partial"}),
        ),
        ("invalid/anchor-without-manifest", False, None, None),
    ]
    for rel, expect_pass, expected_advisory, expected_clause_ids in fixture_cases:
        fixture_dir = FIXTURES_DIR / rel
        if not fixture_dir.is_dir():
            cases.append((f"fixture {rel}: directory exists", False))
            continue
        layout = fixture_layout(
            fixture_dir, expected_advisory=expected_advisory, expected_clause_ids=expected_clause_ids
        )
        errors = run_layout(layout)
        passed = (errors == []) is expect_pass
        label = "PASS as expected" if expect_pass else "FAIL as expected"
        cases.append((f"fixture {rel}: {label}", passed))

    # --- Live repo must PASS ---
    live_errors = run_layout(live_layout())
    cases.append(("live repo: PASS", live_errors == []))
    if live_errors:
        for e in live_errors:
            print(f"  live-repo error: {e}")

    ok = all(passed for _, passed in cases)
    for name, passed in cases:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"cold-law-digest self-test: {'PASS' if ok else 'FAIL'} ({sum(p for _, p in cases)}/{len(cases)})")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Cold-law digest anti-theater gate")
    parser.add_argument("--self-test", action="store_true", help="run synthetic + fixture self-test cases")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    errors = run_layout(live_layout())
    if errors:
        print("cold-law digest: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print("cold-law digest: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
