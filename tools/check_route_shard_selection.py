#!/usr/bin/env python3
"""Shard-selection preflight gate for the Compiled Runtime Routing Addendum.

The compiled root (skill/SKILL.md) carries a "Compiled Runtime Routing
Addendum" section whose routing contract keeps the deployed skill from
reverting to the pre-split, ~300k eager-load path: instead of listing every
runtime bundle inline, the addendum names exactly one always-loaded module
(references/runtime-core-routing.md) and dispatches the rest of the
runtime-*.md shard files through a "Dispatch Index" table that is only
consulted -- not eagerly loaded -- on trigger-signal match.

This checker proves that dispatch contract is not theater:

  1. INDEX PARSES               the Dispatch Index table exists and parses
  2. SHARDS EXIST + MAPPED      every indexed shard exists and is mapped;
                                 every eligible shard on disk is indexed
  3. UNIQUE MODULE HOMES        no module is compiled into two shards
  4. SELECTION LAW PRESENT      the HOLD/PARTIAL/cap/ledger vocabulary is
                                 literally present
  5. ALIAS TABLE PRESENT        the known-aliases block is literally present
  6. LOCKSTEP                   the addendum is byte-identical (modulo line
                                 endings) across all four surfaces that carry
                                 it
  7. NUMBERED LIST BUDGET       the eager load-path list has not regrown into
                                 the pre-split five-bundle eager load

Modes:
  python tools/check_route_shard_selection.py              validate the live repo
  python tools/check_route_shard_selection.py --self-test  synthetic fixtures prove
                                                             each check fails on the
                                                             right bad input, plus a
                                                             live-repo PASS
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKILL_ROOT_REL = "skill/SKILL.md"
COLD_COPY_REL = "skill/references/rubrics/non-droppable-manual-contract.md"
ATOMICS_HOT_REL = "atomics/skill/references/rubrics/manual-contract-digest.md"
ATOMICS_COLD_REL = "atomics/skill/references/rubrics/non-droppable-manual-contract.md"
MODULE_MAP_REL = "skill/compiled-module-map.json"
SKILL_REFERENCES_REL = "skill/references"

ADDENDUM_START_MARK = "Load path for substantive cases:"
ADDENDUM_END_ANCHOR = (
    "Use `references/omnibus/*.md` only after V1, Phase 2, and the Diagnostic "
    "IR authorize the original source module owner."
)

DISPATCH_INDEX_HEADER = "Dispatch Index (route shards - load on selection, not eagerly):"
SELECTION_LAW_HEADER = "Selection law:"
ALIAS_TABLE_HEADER = "Known aliases"

# Deliberate-update pattern (mirrors tools/check_cold_law_digest.py's
# EXPECTED_ADVISORY_CLAUSES / EXPECTED_CLAUSE_IDS convention): the frozen set
# of numbered-load-path entries the live addendum is allowed to carry. Any
# addition here re-grows the eager load path this addendum was built to kill
# -- see tools/load-path-budget.config.json's "_comment_slice_c" note that the
# pre-split "Load path for substantive cases" list named five bundles eagerly.
# A change here requires explicit owner sign-off in the same change.
EXPECTED_EAGER_LIST = ["references/runtime-core-routing.md"]

# Bundle files that are allowed to exist under skill/references/ as
# runtime-*.md without being reachable from the Dispatch Index: the eagerly
# loaded numbered-list entry itself, plus the three always-load kernel
# digests that predate the shard split (runtime-foundation.md,
# runtime-diagnostic-core.md, runtime-phase2-passes.md). Every other
# runtime-*.md bundle on disk must be selectable from the table, or it is
# dead weight: emitted into the package but never reachable by the routing
# contract that is supposed to gate its use.
NUMBERED_LIST_EXEMPT_SHARDS = frozenset(EXPECTED_EAGER_LIST)
ALWAYS_LOAD_KERNEL_EXEMPT_SHARDS = frozenset(
    [
        "references/runtime-foundation.md",
        "references/runtime-diagnostic-core.md",
        "references/runtime-phase2-passes.md",
    ]
)

NUMBERED_LIST_ITEM_RE = re.compile(r"^\d+\.\s+`([^`]+)`\s*$")
TABLE_ROW_SHARD_RE = re.compile(r"`(references/runtime-[a-z0-9-]+\.md)`")
SHARD_PATH_RE = re.compile(r"^references/runtime-[a-z0-9-]+\.md$")

SELECTION_LAW_REQUIRED_STRINGS = (
    "route-ambiguous",
    "owner-not-available",
    "Never fake Land",
    "cap 3",
    "shards_loaded",
)

ALIAS_TABLE_REQUIRED_STRINGS = (
    "source-order",
    "authority-order",
    "hidden-support",
    "definition-discipline",
)
# The tau body-backed rule is checked with a regex rather than a literal
# substring because the source symbol is the Greek letter itself.
TAU_BODY_BACKED_RE = re.compile(r"proof-method-audit applies only when the tribunal/burden role is body-backed")


@dataclass(frozen=True)
class Layout:
    """Filesystem layout for one validation run (live repo or a fixture)."""

    label: str
    skill_root_path: Path
    cold_copy_path: Path
    atomics_hot_path: Path
    atomics_cold_path: Path
    module_map_path: Path
    skill_references_dir: Path
    # Numbered-list-exempt / always-load-kernel-exempt shard basenames (see
    # module-level constants above). Fixtures use small, self-contained sets
    # so a tiny synthetic layout does not have to reproduce the live repo's
    # three always-load kernel digest files.
    numbered_list_exempt: frozenset[str] = field(default_factory=lambda: NUMBERED_LIST_EXEMPT_SHARDS)
    always_load_kernel_exempt: frozenset[str] = field(default_factory=lambda: ALWAYS_LOAD_KERNEL_EXEMPT_SHARDS)
    expected_eager_list: list[str] = field(default_factory=lambda: list(EXPECTED_EAGER_LIST))
    # Row-count floor for INDEX PARSES (check 1). 10 on the live repo (11
    # total shard files minus the 1 always-loaded numbered-list entry); tiny
    # synthetic fixtures supply their own floor so they do not have to
    # reproduce the live repo's full shard count.
    min_index_rows: int = 10


def live_layout() -> Layout:
    return Layout(
        label="live repo",
        skill_root_path=ROOT / SKILL_ROOT_REL,
        cold_copy_path=ROOT / COLD_COPY_REL,
        atomics_hot_path=ROOT / ATOMICS_HOT_REL,
        atomics_cold_path=ROOT / ATOMICS_COLD_REL,
        module_map_path=ROOT / MODULE_MAP_REL,
        skill_references_dir=ROOT / SKILL_REFERENCES_REL,
    )


def fixture_layout(fixture_dir: Path, min_index_rows: int = 2) -> Layout:
    return Layout(
        label=fixture_dir.name,
        skill_root_path=fixture_dir / "root.md",
        cold_copy_path=fixture_dir / "cold_copy.md",
        atomics_hot_path=fixture_dir / "atomics_hot.md",
        atomics_cold_path=fixture_dir / "atomics_cold.md",
        module_map_path=fixture_dir / "compiled-module-map.json",
        skill_references_dir=fixture_dir / "skill_references",
        min_index_rows=min_index_rows,
    )


# ---------------------------------------------------------------------------
# Pure core: each function takes already-loaded data and returns a list of
# error strings (empty = pass). Kept separate from filesystem I/O so the
# self-test can drive them directly with synthetic bad inputs, and so the
# live run and fixture runs share one implementation.
# ---------------------------------------------------------------------------


def extract_addendum(root_text: str) -> tuple[str, list[str]]:
    """Slice the addendum span used by every check: from the numbered
    "Load path for substantive cases:" header through the end of the omnibus
    sentence line (inclusive). Returns (segment_text, errors)."""
    start = root_text.find(ADDENDUM_START_MARK)
    if start == -1:
        return "", [f"compiled root has no {ADDENDUM_START_MARK!r} section"]
    anchor = root_text.find(ADDENDUM_END_ANCHOR, start)
    if anchor == -1:
        return "", [f"compiled root has no omnibus-sentence addendum terminator after {ADDENDUM_START_MARK!r}"]
    end = root_text.find("\n", anchor)
    if end == -1:
        end = len(root_text)
    return root_text[start:end], []


def parse_numbered_load_list(addendum_text: str) -> tuple[list[str], list[str]]:
    """Parse the eager numbered load-path list. Returns (entries, errors)."""
    dispatch_index_pos = addendum_text.find(DISPATCH_INDEX_HEADER)
    if dispatch_index_pos == -1:
        return [], [f"addendum has no {DISPATCH_INDEX_HEADER!r} header"]
    list_block = addendum_text[: dispatch_index_pos]
    entries: list[str] = []
    for line in list_block.splitlines():
        match = NUMBERED_LIST_ITEM_RE.match(line.strip())
        if match:
            entries.append(match.group(1))
    if not entries:
        return [], ["addendum numbered load-path list has no parseable `path` entries"]
    return entries, []


def parse_dispatch_index(addendum_text: str) -> tuple[list[str], list[str]]:
    """Parse the Dispatch Index table. Returns (shard_paths_in_row_order, errors).

    A row is any line inside the table region that is not the header row or
    the `| --- | --- | --- |` separator row and contains a `references/
    runtime-*.md` backtick-quoted path. Every such row must name exactly one
    shard path -- more or less than one is a parse failure, since the index
    is a routing contract, not free text.
    """
    dispatch_index_pos = addendum_text.find(DISPATCH_INDEX_HEADER)
    if dispatch_index_pos == -1:
        return [], [f"addendum has no {DISPATCH_INDEX_HEADER!r} header"]
    selection_law_pos = addendum_text.find(SELECTION_LAW_HEADER, dispatch_index_pos)
    if selection_law_pos == -1:
        return [], [f"addendum has no {SELECTION_LAW_HEADER!r} header after the Dispatch Index"]
    table_block = addendum_text[dispatch_index_pos:selection_law_pos]

    errors: list[str] = []
    shard_rows: list[str] = []
    table_lines = [line for line in table_block.splitlines() if line.strip().startswith("|")]
    if not table_lines:
        return [], ["Dispatch Index header found but no markdown table rows follow it"]
    if len(table_lines) < 2 or not re.match(r"^\|\s*-{2,}", table_lines[1]):
        errors.append("Dispatch Index table is missing its header-separator row")
    data_lines = table_lines[2:] if len(table_lines) >= 2 else []
    for line in data_lines:
        shard_matches = TABLE_ROW_SHARD_RE.findall(line)
        if len(shard_matches) != 1:
            errors.append(
                f"Dispatch Index row does not name exactly one references/runtime-*.md shard "
                f"cell: {line.strip()!r} (found {len(shard_matches)})"
            )
            continue
        shard_rows.append(shard_matches[0])
    return shard_rows, errors


def check_index_parses(addendum_text: str, min_index_rows: int) -> tuple[list[str], list[str]]:
    """Check 1: INDEX PARSES. Returns (shard_rows, errors).

    ``min_index_rows`` is a row-count floor supplied by the Layout (see
    Layout.min_index_rows below): on the live repo this is 10 (11 total shard
    files minus the 1 always-loaded numbered-list entry -- see
    tools/load-path-budget.config.json's "_comment_slice_c" note), but that
    is a live-repo-specific invariant, not a property of the parser itself,
    so fixtures supply their own small floor.
    """
    errors: list[str] = []
    if DISPATCH_INDEX_HEADER not in addendum_text:
        return [], [f"addendum does not contain the exact header {DISPATCH_INDEX_HEADER!r}"]
    shard_rows, parse_errors = parse_dispatch_index(addendum_text)
    errors.extend(parse_errors)
    if errors:
        return [], errors
    if len(shard_rows) < min_index_rows:
        errors.append(
            f"Dispatch Index has only {len(shard_rows)} row(s); expected at least {min_index_rows}"
        )
    for shard in shard_rows:
        if not SHARD_PATH_RE.match(shard):
            errors.append(f"Dispatch Index row names a non-shard path: {shard!r}")
    return shard_rows, errors


def check_shards_exist_and_mapped(
    shard_rows: list[str],
    numbered_list_entries: list[str],
    skill_references_dir: Path,
    module_map: dict,
    numbered_list_exempt: frozenset[str],
    always_load_kernel_exempt: frozenset[str],
) -> list[str]:
    """Check 2: SHARDS EXIST + MAPPED."""
    errors: list[str] = []
    bundle_paths_in_map: set[str] = set()
    modules = module_map.get("modules")
    if isinstance(modules, dict):
        for entry in modules.values():
            if isinstance(entry, dict) and isinstance(entry.get("bundle_path"), str):
                bundle_paths_in_map.add(entry["bundle_path"])
    elif isinstance(modules, list):
        for entry in modules:
            if isinstance(entry, dict) and isinstance(entry.get("bundle_path"), str):
                bundle_paths_in_map.add(entry["bundle_path"])

    indexed_basenames: set[str] = set()
    for shard in sorted(set(shard_rows)):
        basename = Path(shard).name
        indexed_basenames.add(basename)
        shard_file = skill_references_dir / basename
        if not shard_file.is_file():
            errors.append(f"Dispatch Index names {shard!r} but no such file exists under skill/references/")
            continue
        map_key = f"references/{basename}"
        if map_key not in bundle_paths_in_map:
            errors.append(
                f"{shard!r} exists on disk but is not a bundle_path for any module in the compiled module map"
            )

    if not skill_references_dir.is_dir():
        errors.append(f"skill references directory not found: {skill_references_dir}")
        return errors

    numbered_basenames = {Path(entry).name for entry in numbered_list_entries}
    exempt_basenames = {Path(p).name for p in numbered_list_exempt} | {
        Path(p).name for p in always_load_kernel_exempt
    }
    for bundle_file in sorted(skill_references_dir.glob("runtime-*.md")):
        basename = bundle_file.name
        if basename in numbered_basenames or basename in exempt_basenames:
            continue
        if basename not in indexed_basenames:
            errors.append(
                f"skill/references/{basename} is an emitted runtime bundle that the Dispatch Index cannot "
                "select -- dead weight (not reachable via the numbered load-path list, the always-load "
                "kernel exemption list, or any Dispatch Index row)"
            )
    return errors


def check_unique_module_homes(module_map: dict) -> list[str]:
    """Check 3: UNIQUE MODULE HOMES.

    The owner-callable-in-exactly-one-shard invariant at bundle granularity:
    no module_id may resolve to more than one bundle_path. The live map
    stores modules as a dict keyed by module_id, which makes a *duplicate
    key* structurally impossible once JSON is parsed (the later value simply
    wins) -- so this check also accepts a list-of-entries representation
    (used by fixtures) where duplicate module_id entries with divergent
    bundle_path values are directly representable and detectable.
    """
    errors: list[str] = []
    modules = module_map.get("modules")
    homes: dict[str, set[str]] = {}
    if isinstance(modules, dict):
        for module_id, entry in modules.items():
            if not isinstance(entry, dict):
                errors.append(f"{module_id}: module map entry is not an object")
                continue
            bundle_path = entry.get("bundle_path")
            if not isinstance(bundle_path, str):
                errors.append(f"{module_id}: module map entry has no string bundle_path")
                continue
            homes.setdefault(module_id, set()).add(bundle_path)
    elif isinstance(modules, list):
        for entry in modules:
            if not isinstance(entry, dict):
                errors.append("module map has a non-object entry in its modules list")
                continue
            module_id = entry.get("module_id")
            bundle_path = entry.get("bundle_path")
            if not isinstance(module_id, str) or not isinstance(bundle_path, str):
                errors.append("module map list entry is missing a string module_id or bundle_path")
                continue
            homes.setdefault(module_id, set()).add(bundle_path)
    else:
        return ["module map has no 'modules' object or list"]

    for module_id, bundle_paths in sorted(homes.items()):
        if len(bundle_paths) > 1:
            errors.append(
                f"{module_id}: compiled into {len(bundle_paths)} distinct shards {sorted(bundle_paths)} "
                "-- violates owner-callable-in-exactly-one-shard"
            )
    return errors


def check_selection_law_present(addendum_text: str) -> list[str]:
    """Check 4: SELECTION LAW PRESENT."""
    errors: list[str] = []
    selection_law_pos = addendum_text.find(SELECTION_LAW_HEADER)
    if selection_law_pos == -1:
        return [f"addendum has no {SELECTION_LAW_HEADER!r} block"]
    alias_pos = addendum_text.find(ALIAS_TABLE_HEADER, selection_law_pos)
    law_block = addendum_text[selection_law_pos: alias_pos if alias_pos != -1 else len(addendum_text)]
    for required in SELECTION_LAW_REQUIRED_STRINGS:
        if required not in law_block:
            errors.append(f"selection-law block is missing required string {required!r}")
    return errors


def check_alias_table_present(addendum_text: str) -> list[str]:
    """Check 5: ALIAS TABLE PRESENT."""
    errors: list[str] = []
    alias_pos = addendum_text.find(ALIAS_TABLE_HEADER)
    if alias_pos == -1:
        return [f"addendum has no {ALIAS_TABLE_HEADER!r} block"]
    alias_block = addendum_text[alias_pos:]
    for required in ALIAS_TABLE_REQUIRED_STRINGS:
        if required not in alias_block:
            errors.append(f"known-aliases block is missing required string {required!r}")
    if not TAU_BODY_BACKED_RE.search(alias_block):
        errors.append("known-aliases block is missing the tau proof-method-audit body-backed rule")
    return errors


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def check_lockstep(
    root_addendum: str,
    cold_copy_addendum: str,
    atomics_hot_addendum: str,
    atomics_cold_addendum: str,
) -> list[str]:
    """Check 6: LOCKSTEP."""
    errors: list[str] = []
    canonical = normalize_line_endings(root_addendum)
    surfaces = (
        ("shipped cold copy", cold_copy_addendum),
        ("atomics hot copy (manual-contract-digest.md)", atomics_hot_addendum),
        ("atomics cold copy (non-droppable-manual-contract.md)", atomics_cold_addendum),
    )
    for label, text in surfaces:
        if normalize_line_endings(text) != canonical:
            errors.append(f"addendum in {label} has drifted from skill/SKILL.md (byte-for-byte mismatch)")
    return errors


def check_numbered_list_budget(numbered_list_entries: list[str], expected_eager_list: list[str]) -> list[str]:
    """Check 7: NUMBERED LIST BUDGET."""
    if numbered_list_entries != expected_eager_list:
        return [
            f"addendum numbered load-path list is {numbered_list_entries} but EXPECTED_EAGER_LIST is "
            f"{expected_eager_list} -- re-adding eager bundles is the 300k regression canary "
            "(dispatch-gate-remains-monolithic / default-package-requires-all-five-bundles); a "
            "deliberate change requires explicit owner sign-off and an update to EXPECTED_EAGER_LIST"
        ]
    return []


# ---------------------------------------------------------------------------
# Layout-driven orchestration (shared by live mode and fixture-backed
# self-test file cases).
# ---------------------------------------------------------------------------


def load_addendum(path: Path, label: str) -> tuple[str, list[str]]:
    if not path.is_file():
        return "", [f"[{label}] file not found: {path}"]
    text = path.read_text(encoding="utf-8")
    segment, errors = extract_addendum(text)
    return segment, [f"[{label}] {e}" for e in errors]


def run_layout(layout: Layout) -> list[str]:
    errors: list[str] = []

    root_addendum, root_errors = load_addendum(layout.skill_root_path, layout.label)
    errors.extend(root_errors)
    if errors:
        return errors

    numbered_list_entries, list_errors = parse_numbered_load_list(root_addendum)
    errors.extend(f"[{layout.label}] {e}" for e in list_errors)
    if errors:
        return errors

    shard_rows, index_errors = check_index_parses(root_addendum, layout.min_index_rows)
    errors.extend(f"[{layout.label}] {e}" for e in index_errors)
    if errors:
        return errors

    if not layout.module_map_path.is_file():
        return [f"[{layout.label}] compiled module map not found: {layout.module_map_path}"]
    try:
        module_map = json.loads(layout.module_map_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"[{layout.label}] compiled module map is not valid JSON: {exc}"]
    if not isinstance(module_map, dict):
        return [f"[{layout.label}] compiled module map is not a JSON object"]

    errors.extend(
        f"[{layout.label}] {e}"
        for e in check_shards_exist_and_mapped(
            shard_rows,
            numbered_list_entries,
            layout.skill_references_dir,
            module_map,
            layout.numbered_list_exempt,
            layout.always_load_kernel_exempt,
        )
    )
    if errors:
        return errors

    errors.extend(f"[{layout.label}] {e}" for e in check_unique_module_homes(module_map))
    if errors:
        return errors

    errors.extend(f"[{layout.label}] {e}" for e in check_selection_law_present(root_addendum))
    if errors:
        return errors

    errors.extend(f"[{layout.label}] {e}" for e in check_alias_table_present(root_addendum))
    if errors:
        return errors

    cold_copy_addendum, cc_errors = load_addendum(layout.cold_copy_path, layout.label)
    atomics_hot_addendum, ah_errors = load_addendum(layout.atomics_hot_path, layout.label)
    atomics_cold_addendum, ac_errors = load_addendum(layout.atomics_cold_path, layout.label)
    errors.extend(cc_errors)
    errors.extend(ah_errors)
    errors.extend(ac_errors)
    if errors:
        return errors

    errors.extend(
        f"[{layout.label}] {e}"
        for e in check_lockstep(root_addendum, cold_copy_addendum, atomics_hot_addendum, atomics_cold_addendum)
    )
    if errors:
        return errors

    errors.extend(
        f"[{layout.label}] {e}"
        for e in check_numbered_list_budget(numbered_list_entries, layout.expected_eager_list)
    )
    return errors


def summarize_index(layout: Layout) -> str:
    """Produce a short "row -> shard" summary for the acceptance report."""
    root_addendum, errors = load_addendum(layout.skill_root_path, layout.label)
    if errors:
        return "\n".join(errors)
    shard_rows, parse_errors = parse_dispatch_index(root_addendum)
    if parse_errors:
        return "\n".join(parse_errors)
    lines = [f"Dispatch Index: {len(shard_rows)} row(s)"]
    for i, shard in enumerate(shard_rows, start=1):
        lines.append(f"  {i:2d}. {shard}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test: synthetic fixtures under tests/route-shard-fixtures/ prove each
# check fails on the right bad input, plus a live-repo PASS.
# ---------------------------------------------------------------------------

FIXTURES_DIR = ROOT / "tests" / "route-shard-fixtures"

FIXTURE_CASES: list[tuple[str, bool]] = [
    ("valid", True),
    ("invalid/index-missing-shard-file", False),
    ("invalid/dead-shard-not-in-index", False),
    ("invalid/module-in-two-shards", False),
    ("invalid/selection-law-missing-hold-reason", False),
    ("invalid/alias-block-missing", False),
    ("invalid/lockstep-drift", False),
    ("invalid/eager-list-regression", False),
]

FIXTURE_FAIL_REASON: dict[str, str] = {
    "invalid/index-missing-shard-file": "no such file exists under skill/references",
    "invalid/dead-shard-not-in-index": "dead weight",
    "invalid/module-in-two-shards": "owner-callable-in-exactly-one-shard",
    "invalid/selection-law-missing-hold-reason": "selection-law block is missing required string",
    "invalid/alias-block-missing": "addendum has no 'Known aliases' block",
    "invalid/lockstep-drift": "drifted from skill/SKILL.md",
    "invalid/eager-list-regression": "300k regression canary",
}


def self_test() -> int:
    cases: list[tuple[str, bool]] = []

    # --- Embedded synthetic cases exercising the pure core directly ---

    good_addendum = (
        "Load path for substantive cases:\n\n"
        "1. `references/runtime-core-routing.md`\n\n"
        "Dispatch Index (route shards - load on selection, not eagerly):\n\n"
        "| trigger signal | shard | load when |\n"
        "| --- | --- | --- |\n"
        "| t1 | `references/runtime-shard-audit.md` | w1 |\n"
        "| t2 | `references/runtime-shard-thesis.md` | w2 |\n\n"
        "Selection law:\n\n"
        "- If still ambiguous, load ALL candidate shards (cap 3) or route HOLD/PARTIAL with reason "
        "`route-ambiguous`.\n"
        "- Live pressure with 0 candidate shards means route HOLD/PARTIAL with reason "
        "`owner-not-available`.\n"
        "- Never fake Land.\n"
        "- Record `shards_loaded` in the state capsule when available.\n\n"
        "Known aliases (OSM discipline):\n\n"
        "- Surface \"source\" aliases source-order vs authority-order vs hidden-support.\n"
        "- \"definition-discipline\" is a route label, not a callable operation unless mapped.\n"
        "- proof-method-audit applies only when the tribunal/burden role is body-backed.\n\n"
        "Use `references/omnibus/*.md` only after V1, Phase 2, and the Diagnostic IR authorize the "
        "original source module owner.\nnext line\n"
    )
    seg, errs = extract_addendum(good_addendum)
    cases.append(("extract_addendum: well-formed addendum extracts cleanly", errs == []))
    cases.append(("extract_addendum: missing start marker flagged", extract_addendum("nothing here")[1] != []))
    cases.append((
        "extract_addendum: missing omnibus terminator flagged",
        extract_addendum("Load path for substantive cases:\nno terminator")[1] != [],
    ))

    entries, list_errors = parse_numbered_load_list(seg)
    cases.append(("numbered list: parses exactly one entry", entries == ["references/runtime-core-routing.md"]))
    cases.append(("numbered list: no parse errors", list_errors == []))

    shard_rows, index_errors = check_index_parses(seg, min_index_rows=2)
    cases.append(("index parses: two well-formed rows -> no errors", index_errors == []))
    cases.append((
        "index parses: shard rows captured in order",
        shard_rows == ["references/runtime-shard-audit.md", "references/runtime-shard-thesis.md"],
    ))
    cases.append((
        "index parses: row-count floor enforced",
        any("expected at least 3" in e for e in check_index_parses(seg, min_index_rows=3)[1]),
    ))
    bad_row_addendum = good_addendum.replace(
        "| t1 | `references/runtime-shard-audit.md` | w1 |",
        "| t1 | not-a-shard-cell | w1 |",
    )
    bad_seg, _ = extract_addendum(bad_row_addendum)
    _, bad_index_errors = check_index_parses(bad_seg, min_index_rows=2)
    cases.append((
        "index parses: row without a shard cell flagged",
        any("does not name exactly one" in e for e in bad_index_errors),
    ))
    missing_header_seg = seg.replace(DISPATCH_INDEX_HEADER, "Some Other Header:")
    cases.append((
        "index parses: missing Dispatch Index header flagged",
        any(
            "does not contain the exact header" in e
            for e in check_index_parses(missing_header_seg, min_index_rows=2)[1]
        ),
    ))

    module_map_ok = {
        "modules": {
            "mod-a": {"bundle_path": "references/runtime-shard-audit.md"},
            "mod-b": {"bundle_path": "references/runtime-shard-thesis.md"},
        }
    }
    cases.append(("unique module homes: distinct homes -> no errors", check_unique_module_homes(module_map_ok) == []))
    module_map_dup_list = {
        "modules": [
            {"module_id": "mod-a", "bundle_path": "references/runtime-shard-audit.md"},
            {"module_id": "mod-a", "bundle_path": "references/runtime-shard-thesis.md"},
        ]
    }
    cases.append((
        "unique module homes: module in two shards (list form) flagged",
        any("owner-callable-in-exactly-one-shard" in e for e in check_unique_module_homes(module_map_dup_list)),
    ))
    cases.append((
        "unique module homes: missing modules key flagged",
        check_unique_module_homes({}) != [],
    ))

    cases.append(("selection law: complete block -> no errors", check_selection_law_present(seg) == []))
    stripped_law_seg = seg.replace("Never fake Land.\n", "")
    cases.append((
        "selection law: missing 'Never fake Land' flagged",
        any("Never fake Land" in e for e in check_selection_law_present(stripped_law_seg)),
    ))
    cases.append((
        "selection law: missing header entirely flagged",
        check_selection_law_present("no law here") != [],
    ))

    cases.append(("alias table: complete block -> no errors", check_alias_table_present(seg) == []))
    stripped_alias_seg = seg.replace(
        "- proof-method-audit applies only when the tribunal/burden role is body-backed.\n", ""
    )
    cases.append((
        "alias table: missing tau body-backed rule flagged",
        any("tau proof-method-audit" in e for e in check_alias_table_present(stripped_alias_seg)),
    ))
    cases.append((
        "alias table: missing header entirely flagged",
        check_alias_table_present("no aliases here") != [],
    ))

    cases.append((
        "lockstep: four identical copies -> no errors",
        check_lockstep(seg, seg, seg, seg) == [],
    ))
    cases.append((
        "lockstep: crlf-only difference tolerated",
        check_lockstep(seg, seg.replace("\n", "\r\n"), seg, seg) == [],
    ))
    cases.append((
        "lockstep: real drift flagged",
        any("cold copy" in e for e in check_lockstep(seg, seg + "EXTRA", seg, seg)),
    ))

    cases.append((
        "numbered list budget: matches EXPECTED_EAGER_LIST -> no errors",
        check_numbered_list_budget(["references/runtime-core-routing.md"], ["references/runtime-core-routing.md"])
        == [],
    ))
    cases.append((
        "numbered list budget: five-bundle regression flagged",
        any(
            "300k regression canary" in e
            for e in check_numbered_list_budget(
                [
                    "references/runtime-foundation.md",
                    "references/runtime-diagnostic-core.md",
                    "references/runtime-phase2-passes.md",
                    "references/runtime-dispatch-gate.md",
                    "references/runtime-output-governance.md",
                ],
                ["references/runtime-core-routing.md"],
            )
        ),
    ))

    # --- Fixture-backed file cases (tests/route-shard-fixtures/) ---
    for rel, expect_pass in FIXTURE_CASES:
        fixture_dir = FIXTURES_DIR / rel
        if not fixture_dir.is_dir():
            cases.append((f"fixture {rel}: directory exists", False))
            continue
        layout = fixture_layout(fixture_dir)
        errors = run_layout(layout)
        passed = (errors == []) is expect_pass
        reason = FIXTURE_FAIL_REASON.get(rel)
        if passed and not expect_pass and reason is not None:
            passed = any(reason in e for e in errors)
        label = "PASS as expected" if expect_pass else "FAIL as expected (right reason)"
        if not passed:
            for e in errors:
                print(f"  fixture {rel} error: {e}")
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
    print(
        f"route-shard-selection self-test: {'PASS' if ok else 'FAIL'} "
        f"({sum(p for _, p in cases)}/{len(cases)})"
    )
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Shard-selection preflight gate")
    parser.add_argument("--self-test", action="store_true", help="run synthetic + fixture self-test cases")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    layout = live_layout()
    errors = run_layout(layout)
    if errors:
        print("route shard selection: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print("route shard selection: PASS")
    print(summarize_index(layout))
    return 0


if __name__ == "__main__":
    sys.exit(main())
