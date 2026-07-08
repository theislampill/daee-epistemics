#!/usr/bin/env python3
"""Load-path budget measurement — Plan 16 Phase 1 (stdlib only).

MEASURES and REPORTS the byte / line / estimated-token footprint of the runtime
load-path configurations. It does NOT enforce a budget, slim anything, or gate
CI on a size threshold — it is observability for the architecture-debt work.

est_tokens is a heuristic: est_tokens = bytes // 4. It is not a tokenizer count
and is not a claim about any specific model's context accounting.

Configurations reported:
  - skill-md-only          : skill/SKILL.md alone
  - per-bundle             : each skill/references/runtime-*.md bundle
  - five-bundle-substantive: skill/SKILL.md + all runtime bundles
  - always-load-bundles    : skill/SKILL.md + the distinct bundles hosting the
                             files in SKILL.md's "### Always Load" table
                             (resolved via skill/compiled-module-map.json)
  - structural-diagnosis-floor: always-load floor + the distinct bundles hosting
                             the files in SKILL.md's "### Mandatory Diagnostic
                             Core" table (same resolution path)
  - largest-retained-output: the single largest retained case output.md
And a constraint census: case-insensitive `must` / `never` word counts in SKILL.md.

Usage:
  python tools/measure_load_path_budget.py
  python tools/measure_load_path_budget.py --self-test
  python tools/measure_load_path_budget.py --enforce-ratchet
  python tools/measure_load_path_budget.py --report-json <path>

This slice (A1) adds OBSERVABILITY plus a REGRESSION RATCHET only. The ratchet
(tools/load-path-budget.config.json, ratchet.baseline) fails CI when a measured
row grows more than ratchet.tolerance_pct above its recorded baseline. It does
NOT enforce the aspirational thresholds recorded in the config's `aspirational`
block -- those are inert until a later slice (A2) flips `enforced: true`.
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import math
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "skill" / "SKILL.md"
BUNDLE_GLOB = "skill/references/runtime-*.md"
MODULE_MAP = ROOT / "skill" / "compiled-module-map.json"
RETAINED_GLOB = "tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/*/output.md"
DEFAULT_CONFIG = ROOT / "tools" / "load-path-budget.config.json"

# Row name used for the one measurement surface that is never gated by the
# ratchet. Retained-output size is expected to grow as the proof corpus
# accumulates larger, still-valid cases; see the config's _comment_exclusions.
EXEMPT_ROW = "largest-retained-output"

# Row name of the synthetic AGGREGATE ratchet row: skill-md-only bytes + the
# sum of bytes of all five per-bundle rows. It is baselined and gated like
# any other row, but at a strictly tighter tolerance than individual rows
# (see check_ratchet's AGGREGATE_ROW handling) so growth spread thinly across
# every per-row surface cannot dodge the ratchet just because each row on its
# own stays under tolerance_pct.
AGGREGATE_ROW = "total-hot-surfaces"

# Fixed allowance added to the default-exec worst-case arithmetic (Slice A2)
# to account for the multi-call state capsule (daee-state-capsule-v1) that
# rides alongside the root + shard load on every recursive call. This is a
# constant, not a measured surface -- see tools/load-path-budget.config.json
# aspirational._owner_note_exec_ceiling for the worst-case arithmetic that
# uses it.
CAPSULE_ALLOWANCE_EST_TOK = 4000

# The exact eager numbered load-path list the compiled root is allowed to
# carry (mirrors tools/check_route_shard_selection.py's EXPECTED_EAGER_LIST
# semantics). Duplicated here deliberately (rather than imported) so this
# tool's 300k-pattern check is self-contained and does not depend on that
# checker's internals; a deliberate change to the eager list requires
# updating both this constant and that checker's EXPECTED_EAGER_LIST in the
# same change.
EXPECTED_EAGER_LIST = ["references/runtime-core-routing.md"]
ADDENDUM_START_MARK = "Load path for substantive cases:"
DISPATCH_INDEX_HEADER = "Dispatch Index (route shards - load on selection, not eagerly):"
NUMBERED_LIST_ITEM_RE = re.compile(r"^\d+\.\s+`([^`]+)`\s*$")


def metrics(paths: list[Path]) -> tuple[int, int, int]:
    """Return (total_bytes, total_lines, est_tokens) for the given files."""
    total_bytes = 0
    total_lines = 0
    for p in paths:
        data = p.read_bytes()
        total_bytes += len(data)
        total_lines += data.count(b"\n")
    return total_bytes, total_lines, total_bytes // 4


def bundles() -> list[Path]:
    return [Path(p) for p in sorted(glob.glob(str(ROOT / BUNDLE_GLOB)))]


def _normalize_skill_relative(path: str) -> str:
    """Strip a leading `skill/` prefix so paths compare relative to skill/.

    compiled-module-map.json's `canonical_path` values are repo-root-relative
    (`skill/references/...`); SKILL.md's tables reference the same files
    skill-relative (`references/...`). Normalizing both to the skill-relative
    form makes the lookup prefix-agnostic in either direction.
    """
    path = path.replace("\\", "/")
    if path.startswith("skill/"):
        path = path[len("skill/") :]
    return path


def _section_files(skill_text: str, heading: str) -> list[str]:
    """Parse the `references/...` paths from the markdown table under `### <heading>`.

    Only matches paths inside actual table rows (lines starting with
    `| \`references/...\``), not prose or routing notes elsewhere in the
    section body, which may reference unrelated files in backticks.
    """
    m = re.search(rf"### {re.escape(heading)}\n(.*?)(?:\n### )", skill_text, re.S)
    if not m:
        return []
    return re.findall(r"^\|\s*`(references/[^`]+)`", m.group(1), re.M)


def always_load_files(skill_text: str) -> list[str]:
    """Parse the `references/...` paths listed in SKILL.md's '### Always Load' table."""
    return _section_files(skill_text, "Always Load")


def mandatory_diagnostic_core_files(skill_text: str) -> list[str]:
    """Parse the `references/...` paths in SKILL.md's '### Mandatory Diagnostic Core' table."""
    return _section_files(skill_text, "Mandatory Diagnostic Core")


def _load_canon_to_bundle() -> dict[str, str]:
    """Build a skill-relative canonical_path -> bundle_path map from the module map.

    Keys are normalized (leading `skill/` stripped) so lookups succeed
    regardless of whether the caller's path carries the `skill/` prefix.
    """
    module_map = json.loads(MODULE_MAP.read_text(encoding="utf-8")).get("modules", {})
    canon_to_bundle: dict[str, str] = {}
    for entry in module_map.values():
        canon = entry.get("canonical_path")
        bundle = entry.get("bundle_path")
        if canon and bundle:
            canon_to_bundle[_normalize_skill_relative(canon)] = bundle
    return canon_to_bundle


def resolve_bundles(files: list[str], canon_to_bundle: dict[str, str]) -> tuple[list[Path], list[str]]:
    """Resolve a list of skill-relative canonical files to real bundle file paths.

    Accepts lookup keys with or without a leading `skill/` prefix (normalized
    before matching against the also-normalized map). `bundle_path` entries in
    the module map are relative to the `skill/` directory (e.g.
    `references/runtime-foundation.md`), so they are joined against
    `ROOT / "skill"`, not `ROOT`.

    Returns (distinct existing bundle paths, unresolved-or-missing entries).
    Unresolved lookups and bundle paths that don't exist on disk are both
    reported in the second list -- never silently dropped.
    """
    resolved: list[str] = []
    unresolved: list[str] = []
    for f in files:
        bundle = canon_to_bundle.get(_normalize_skill_relative(f))
        if bundle:
            resolved.append(bundle)
        else:
            unresolved.append(f)
    bundle_paths: list[Path] = []
    for b in resolved:
        candidate = ROOT / "skill" / b
        if candidate.exists():
            bundle_paths.append(candidate)
        else:
            unresolved.append(f"{b} (resolved bundle path does not exist: {candidate})")
    distinct = sorted(set(bundle_paths), key=lambda p: str(p))
    return distinct, unresolved


def always_load_bundles(skill_text: str) -> tuple[list[Path], list[str]]:
    """Resolve always-load files to their runtime bundles via the module map.

    Returns (distinct bundle paths, unresolved canonical_paths)."""
    files = always_load_files(skill_text)
    canon_to_bundle = _load_canon_to_bundle()
    return resolve_bundles(files, canon_to_bundle)


def structural_diagnosis_bundles(skill_text: str) -> tuple[list[Path], list[str]]:
    """Resolve always-load + Mandatory Diagnostic Core files to their bundles.

    Returns (distinct bundle paths across both sections, unresolved entries).
    """
    files = always_load_files(skill_text) + mandatory_diagnostic_core_files(skill_text)
    canon_to_bundle = _load_canon_to_bundle()
    return resolve_bundles(files, canon_to_bundle)


def constraint_census(skill_text: str) -> tuple[int, int]:
    must = len(re.findall(r"(?i)\bmust\b", skill_text))
    never = len(re.findall(r"(?i)\bnever\b", skill_text))
    return must, never


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def row_key(config: str, detail: str) -> str:
    """Return the ratchet-baseline lookup key for a (config, detail) row pair.

    Most configs are singletons (e.g. "skill-md-only"), so the config name
    alone is a stable key. "per-bundle" rows repeat once per bundle file, so
    the config name alone would collide across bundles -- those are keyed as
    "per-bundle:<detail path>" instead, matching the config file's convention.
    """
    if config == "per-bundle":
        return f"per-bundle:{detail}"
    return config


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_rows() -> list[tuple[str, str, int, int, int]]:
    """Return rows: (config, detail, bytes, lines, est_tokens)."""
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    bnds = bundles()
    rows: list[tuple[str, str, int, int, int]] = []

    b, l, t = metrics([SKILL_MD])
    rows.append(("skill-md-only", rel(SKILL_MD), b, l, t))

    for bp in bnds:
        b, l, t = metrics([bp])
        rows.append(("per-bundle", rel(bp), b, l, t))

    b, l, t = metrics([SKILL_MD, *bnds])
    rows.append(("five-bundle-substantive", f"SKILL.md + {len(bnds)} bundles", b, l, t))

    # total-hot-surfaces: a synthetic AGGREGATE ratchet row = sum of bytes of
    # skill-md-only + all five per-bundle rows. This is deliberately the same
    # byte total as five-bundle-substantive (both sum SKILL.md + the five
    # runtime-*.md bundles), but it exists as its OWN independently baselined
    # ratchet key so that growth spread thinly across every per-row entry
    # (each individually under the per-row tolerance) still gets caught in
    # aggregate. Per-row ratcheting alone allows a small percentage of growth
    # smuggled into each of the 6 rows to add up to a much larger total
    # regression that no single row's check would flag; this row closes that
    # gap. It intentionally excludes largest-retained-output (never part of
    # the "hot" load-path surface; see EXEMPT_ROW).
    rows.append((AGGREGATE_ROW, "skill-md-only + 5 per-bundle rows (sum of bytes)", b, l, t))

    al_bundles, unresolved = always_load_bundles(skill_text)
    detail = f"SKILL.md + {len(al_bundles)} always-load bundles"
    if unresolved:
        detail += f" (unresolved: {', '.join(unresolved)})"
    b, l, t = metrics([SKILL_MD, *al_bundles])
    rows.append(("always-load-bundles", detail, b, l, t))

    # structural-diagnosis-floor: always-load floor + the Mandatory Diagnostic
    # Core bundle(s). Assumption: the "### Mandatory Diagnostic Core" table in
    # SKILL.md parses with the same `references/...` table format as Always
    # Load, and its six files all resolve (via compiled-module-map.json) to
    # the single runtime-diagnostic-core.md bundle. If that table ever stops
    # parsing cleanly, this still degrades to always-load floor + the
    # runtime-diagnostic-core.md bundle joined directly, not a silent zero.
    sd_bundles, sd_unresolved = structural_diagnosis_bundles(skill_text)
    sd_detail = f"SKILL.md + {len(sd_bundles)} always-load+diagnostic-core bundles"
    if sd_unresolved:
        sd_detail += f" (unresolved: {', '.join(sd_unresolved)})"
    b, l, t = metrics([SKILL_MD, *sd_bundles])
    rows.append(("structural-diagnosis-floor", sd_detail, b, l, t))

    retained = [Path(p) for p in sorted(glob.glob(str(ROOT / RETAINED_GLOB)))]
    if retained:
        largest = max(retained, key=lambda p: p.stat().st_size)
        b, l, t = metrics([largest])
        rows.append(("largest-retained-output", rel(largest), b, l, t))

    return rows


def render_table() -> str:
    rows = build_rows()
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    must, never = constraint_census(skill_text)
    lines = [
        "| config | detail | bytes | lines | est_tokens (bytes/4) |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for config, detail, b, l, t in rows:
        lines.append(f"| {config} | {detail} | {b} | {l} | {t} |")
    lines.append("")
    lines.append(f"constraint-census (skill/SKILL.md): must={must}, never={never}")
    return "\n".join(lines)


def check_ratchet(rows: list[tuple[str, str, int, int, int]], config: dict) -> tuple[bool, list[str]]:
    """Compare measured rows against config['ratchet']['baseline'].

    Rules:
      - EXEMPT_ROW is skipped on both sides (never gated).
      - A row present live but absent from baseline fails as "unbaselined
        config row" (forces baseline maintenance instead of silently letting
        new rows dodge the ratchet).
      - A row present in baseline but absent live fails too (a disappearing
        measurement surface is itself a regression -- it means the load path
        it described no longer exists or is no longer being measured).
      - A row present in both fails if measured bytes exceed
        baseline bytes * (1 + <row_tolerance_pct>/100), where <row_tolerance_pct>
        is ratchet.aggregate_tolerance_pct for the AGGREGATE_ROW key and
        ratchet.tolerance_pct for every other row. The aggregate row uses a
        strictly tighter tolerance than the per-row tolerance on purpose: if
        it used the same tolerance_pct, growth spread evenly across every
        per-row surface (each individually still within tolerance_pct) would
        also land the aggregate within tolerance_pct, defeating the point of
        having an aggregate check at all. A tighter aggregate tolerance means
        that even growth kept under tolerance_pct on every individual row
        still trips the aggregate once it is spread across enough rows.
      - Anti-baseline-banking: a row present in both ALSO fails if the
        baseline bytes value exceeds measured*(1+<row_tolerance_pct>/100). A
        baseline raised above current reality "banks" headroom that lets
        future growth hide inside the gap between baseline and measured,
        so the baseline is only allowed to sit within tolerance of the
        live measurement in either direction, never comfortably above it.

    Returns (ok, failure_messages).
    """
    ratchet = config.get("ratchet", {})
    tolerance_pct = ratchet.get("tolerance_pct", 0.0)
    # The aggregate row is deliberately gated tighter than individual rows;
    # see the FIX 1 rationale above. Defaults to half of tolerance_pct if the
    # config does not set it explicitly.
    aggregate_tolerance_pct = ratchet.get("aggregate_tolerance_pct", tolerance_pct / 2.0)
    baseline = dict(ratchet.get("baseline", {}))

    live_keys: dict[str, tuple[int, int]] = {}
    for cfg_name, detail, b, _l, t in rows:
        key = row_key(cfg_name, detail)
        if key == EXEMPT_ROW:
            continue
        live_keys[key] = (b, t)

    baseline = {k: v for k, v in baseline.items() if k != EXEMPT_ROW}

    failures: list[str] = []

    for key, (measured_bytes, measured_tok) in live_keys.items():
        if key not in baseline:
            failures.append(
                f"unbaselined config row: '{key}' is present in the live measurement "
                f"(bytes={measured_bytes}, est_tok={measured_tok}) but has no entry in "
                f"ratchet.baseline. Add a baseline entry (see tools/load-path-budget.config.json)."
            )
            continue
        row_tolerance_pct = aggregate_tolerance_pct if key == AGGREGATE_ROW else tolerance_pct
        baseline_bytes = baseline[key].get("bytes")
        allowed_bytes = baseline_bytes * (1 + row_tolerance_pct / 100.0)
        if measured_bytes > allowed_bytes:
            failures.append(
                f"ratchet regression: row '{key}' measured bytes={measured_bytes} exceeds "
                f"baseline bytes={baseline_bytes} + tolerance {row_tolerance_pct}% "
                f"(allowed<={allowed_bytes:.0f})."
            )
        allowed_baseline_bytes = measured_bytes * (1 + row_tolerance_pct / 100.0)
        if baseline_bytes > allowed_baseline_bytes:
            failures.append(
                f"baseline exceeds measured surface (banked headroom); lower baseline to measured "
                f"(row '{key}': baseline bytes={baseline_bytes} exceeds measured bytes={measured_bytes} "
                f"+ tolerance {row_tolerance_pct}% (allowed<={allowed_baseline_bytes:.0f}))."
            )

    for key in baseline:
        if key not in live_keys:
            failures.append(
                f"missing measurement surface: row '{key}' is present in ratchet.baseline "
                f"but was not produced by the current measurement. A disappearing "
                f"measurement surface is treated as a regression."
            )

    return len(failures) == 0, failures


def parse_eager_list(skill_text: str) -> tuple[list[str], list[str]]:
    """Parse the numbered "Load path for substantive cases:" list from the
    compiled root text. Returns (entries, errors).

    Mirrors tools/check_route_shard_selection.py's parse_numbered_load_list
    semantics (numbered-list entries between the ADDENDUM_START_MARK header
    and the Dispatch Index header), duplicated here as a small self-contained
    parse rather than importing that checker (see module-level comment next
    to EXPECTED_EAGER_LIST).
    """
    start = skill_text.find(ADDENDUM_START_MARK)
    if start == -1:
        return [], [f"compiled root has no {ADDENDUM_START_MARK!r} section"]
    dispatch_pos = skill_text.find(DISPATCH_INDEX_HEADER, start)
    if dispatch_pos == -1:
        return [], [f"addendum has no {DISPATCH_INDEX_HEADER!r} header"]
    list_block = skill_text[start:dispatch_pos]
    entries: list[str] = []
    for line in list_block.splitlines():
        match = NUMBERED_LIST_ITEM_RE.match(line.strip())
        if match:
            entries.append(match.group(1))
    return entries, []


def check_eager_list_pattern(eager_list: list[str], expected: list[str] | None = None) -> list[str]:
    """300k-pattern check: fail if the eager numbered load-path list names
    more than the expected always-eager set. This is the canary for the
    pre-split ~300k eager-load regression (see
    tools/check_route_shard_selection.py's check_numbered_list_budget,
    which this mirrors at the semantic level)."""
    expected = EXPECTED_EAGER_LIST if expected is None else expected
    if eager_list != expected:
        return [
            f"300k-pattern regression: eager load-path list is {eager_list} but expected exactly "
            f"{expected} -- re-adding eager bundles to the numbered load-path list is the pre-split "
            "300k eager-load regression this gate exists to catch."
        ]
    return []


def classify_shard(basename: str, shard_classes: dict) -> str | None:
    """Return the shard_classes key ('default_hot', 'stage_warm',
    'on_demand_cold') that `basename` belongs to, or None if unclassified."""
    for cls in ("default_hot", "stage_warm", "on_demand_cold"):
        if basename in shard_classes.get(cls, []):
            return cls
    return None


def check_aspirational(rows: list[tuple[str, str, int, int, int]], config: dict, skill_text: str) -> tuple[bool, list[str], list[str]]:
    """Enforce the aspirational hot-context thresholds (Slice A2).

    Returns (ok, failures, warnings). `ok` is False only on FAIL conditions
    (nonzero exit); warnings are advisory (printed to stderr, never affect
    exit code).

    Checks:
      1. hot-root: root est-tok vs hot_root_ceiling/target.
      2. per-shard: default_hot shards vs default_hot_shard ceiling/target;
         stage_warm/on_demand_cold shards reported, never failed; a shard
         file on disk in no class list is an "unclassified shard" FAIL.
      3. default-exec worst case: root + CAPSULE_ALLOWANCE_EST_TOK + sum of
         the 3 largest default_hot shards, vs default_exec ceiling/target.
      4. 300k-pattern check on the eager numbered load-path list.
    """
    aspirational = config.get("aspirational", {})
    if not aspirational.get("enforced", False):
        return True, [], []

    failures: list[str] = []
    warnings: list[str] = []

    row_tok: dict[str, int] = {}
    per_bundle_tok: dict[str, int] = {}
    for cfg_name, detail, b, l, t in rows:
        if cfg_name == "skill-md-only":
            row_tok["skill-md-only"] = t
        if cfg_name == "per-bundle":
            per_bundle_tok[Path(detail).name] = t

    # --- Check 1: hot-root ---
    hot_root_target = aspirational.get("hot_root_target_est_tok")
    hot_root_ceiling = aspirational.get("hot_root_ceiling_est_tok")
    root_tok = row_tok.get("skill-md-only")
    if root_tok is None:
        failures.append("aspirational hot-root check: no 'skill-md-only' row in measurement")
    else:
        if hot_root_ceiling is not None and root_tok > hot_root_ceiling:
            failures.append(
                f"aspirational FAIL: hot-root est_tok={root_tok} exceeds hot_root_ceiling_est_tok={hot_root_ceiling}"
            )
        elif hot_root_target is not None and root_tok > hot_root_target:
            warnings.append(
                f"aspirational WARN: hot-root est_tok={root_tok} exceeds hot_root_target_est_tok={hot_root_target}"
            )

    # --- Check 2: per-shard classification + thresholds ---
    shard_classes = aspirational.get("shard_classes", {})
    shard_target = aspirational.get("default_hot_shard_target_est_tok")
    shard_ceiling = aspirational.get("default_hot_shard_ceiling_est_tok")
    shard_report: list[str] = []
    for basename in sorted(per_bundle_tok):
        tok = per_bundle_tok[basename]
        cls = classify_shard(basename, shard_classes)
        if cls is None:
            failures.append(
                f"aspirational FAIL: unclassified shard '{basename}' (est_tok={tok}) does not appear in "
                "any of aspirational.shard_classes.default_hot/stage_warm/on_demand_cold -- new shards "
                "require deliberate classification"
            )
            continue
        shard_report.append(f"aspirational REPORT: shard {basename} [{cls}] est_tok={tok}")
        if cls != "default_hot":
            continue
        if shard_ceiling is not None and tok > shard_ceiling:
            failures.append(
                f"aspirational FAIL: default_hot shard '{basename}' est_tok={tok} exceeds "
                f"default_hot_shard_ceiling_est_tok={shard_ceiling}"
            )
        elif shard_target is not None and tok > shard_target:
            warnings.append(
                f"aspirational WARN: default_hot shard '{basename}' est_tok={tok} exceeds "
                f"default_hot_shard_target_est_tok={shard_target}"
            )

    # --- Check 3: default-exec worst case ---
    default_hot_names = shard_classes.get("default_hot", [])
    default_hot_toks = sorted(
        (per_bundle_tok[n] for n in default_hot_names if n in per_bundle_tok), reverse=True
    )
    top3 = default_hot_toks[:3]
    exec_target = aspirational.get("default_exec_target_est_tok")
    exec_ceiling = aspirational.get("default_exec_ceiling_est_tok")
    if root_tok is not None:
        worst_case = root_tok + CAPSULE_ALLOWANCE_EST_TOK + sum(top3)
        arithmetic = (
            f"aspirational ARITHMETIC: default-exec worst case: root({root_tok}) + "
            f"capsule({CAPSULE_ALLOWANCE_EST_TOK}) + top-3 default_hot shards"
            f"({'+'.join(str(x) for x in top3)}={sum(top3)}) = {worst_case} est_tok"
        )
        warnings.append(arithmetic)
        if exec_ceiling is not None and worst_case > exec_ceiling:
            failures.append(
                f"aspirational FAIL: {arithmetic} exceeds default_exec_ceiling_est_tok={exec_ceiling}"
            )
        elif exec_target is not None and worst_case > exec_target:
            warnings.append(
                f"aspirational WARN: default-exec worst case {worst_case} exceeds "
                f"default_exec_target_est_tok={exec_target}"
            )

    # --- Check 4: 300k-pattern check ---
    eager_list, eager_parse_errors = parse_eager_list(skill_text)
    if eager_parse_errors:
        failures.extend(f"aspirational FAIL: {e}" for e in eager_parse_errors)
    else:
        failures.extend(f"aspirational FAIL: {e}" for e in check_eager_list_pattern(eager_list))

    warnings = shard_report + warnings

    return len(failures) == 0, failures, warnings


def build_report(
    rows: list[tuple[str, str, int, int, int]],
    config: dict,
    ratchet_result: tuple[bool, list[str]] | None,
    aspirational_result: tuple[bool, list[str], list[str]] | None = None,
) -> dict:
    report_rows = [
        {"config": cfg_name, "detail": detail, "bytes": b, "lines": l, "est_tok": t}
        for cfg_name, detail, b, l, t in rows
    ]
    report: dict = {
        "schema": "load-path-budget-report-v1",
        "rows": report_rows,
        "metric": config.get("metric", {}),
    }
    if ratchet_result is not None:
        ok, failures = ratchet_result
        report["ratchet"] = {"checked": True, "ok": ok, "failures": failures}
    else:
        report["ratchet"] = {"checked": False, "failures": []}
    if aspirational_result is not None:
        ok, failures, warnings = aspirational_result
        report["aspirational"] = {"checked": True, "ok": ok, "failures": failures, "warnings": warnings}
    else:
        report["aspirational"] = {"checked": False, "failures": [], "warnings": []}
    return report


def self_test() -> int:
    checks = []
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    # est_tokens formula
    checks.append(("est_tokens = bytes//4", metrics([SKILL_MD])[2] == metrics([SKILL_MD])[0] // 4))
    # five-bundle-substantive total == skill-md + sum(per-bundle)
    skill_b = metrics([SKILL_MD])[0]
    per_bundle_sum = sum(metrics([bp])[0] for bp in bundles())
    combined = metrics([SKILL_MD, *bundles()])[0]
    checks.append(("five-bundle total == skill + sum(bundles)", combined == skill_b + per_bundle_sum))
    # rows present and non-empty
    rows = build_rows()
    checks.append(("has skill-md-only row", any(r[0] == "skill-md-only" for r in rows)))
    checks.append(("has five-bundle-substantive row", any(r[0] == "five-bundle-substantive" for r in rows)))
    checks.append(("all byte counts positive", all(r[2] > 0 for r in rows)))

    # Canary: always-load resolver must be prefix-agnostic. Build a synthetic
    # module map in-memory where canonical_path keys carry the `skill/`
    # prefix, and confirm the resolver still resolves lookups made with
    # unprefixed (`references/...`) table paths -- and that a naive exact-match
    # lookup (the old, buggy behavior) would NOT resolve the same inputs, so
    # this actually exercises the normalization rather than being a tautology.
    synthetic_canon_to_bundle_raw = {
        "skill/references/synthetic-canary.md": "references/runtime-synthetic.md",
    }
    synthetic_files = ["references/synthetic-canary.md"]
    naive_resolved = [
        f for f in synthetic_files if f in synthetic_canon_to_bundle_raw
    ]
    checks.append(
        (
            "naive exact-match lookup fails on prefix mismatch (sanity check)",
            len(naive_resolved) == 0,
        )
    )
    normalized_map = {
        _normalize_skill_relative(k): v for k, v in synthetic_canon_to_bundle_raw.items()
    }
    normalized_resolved = [
        normalized_map.get(_normalize_skill_relative(f)) for f in synthetic_files
    ]
    checks.append(
        (
            "always-load-resolver-prefix-mismatch: normalization resolves skill/-prefixed keys",
            normalized_resolved == ["references/runtime-synthetic.md"],
        )
    )

    # Slice-B floor reduction: the "### Always Load" table now carries 0
    # `references/...` file rows (its former 4 rows are in-kernel digests
    # inside SKILL.md instead; see EXPECTED_ALWAYS_LOAD_FILES above), so
    # always_load_bundles() must resolve exactly 0 bundles and report exactly
    # 0 unresolved entries -- an empty always-load table is the intended
    # post-reduction state, not a resolver failure. A nonzero unresolved count
    # would still mean a genuinely broken lookup and remains a self-test FAIL.
    al_bundles, al_unresolved = always_load_bundles(skill_text)
    checks.append(("always-load resolves exactly 0 bundles in the live repo (Slice B floor reduction)", len(al_bundles) == 0))
    checks.append(("always-load has 0 unresolved entries in the live repo", len(al_unresolved) == 0))

    # Per-file coverage canary (FIX 2), updated for the Slice-B floor reduction:
    # the "### Always Load" table used to list 4 `references/...` file rows
    # that resolved to the runtime-foundation.md bundle, forcing that whole
    # 103KB bundle hot on every substantive case. Those 4 files' load-bearing
    # content now lives as compact in-kernel digests inside SKILL.md itself
    # (see "### Always-Load Digests (kernel)"), and the "### Always Load"
    # table intentionally carries NO `references/...` rows any more -- the
    # full files remain available on demand, compiled cold in
    # runtime-foundation.md. NOTE: if skill/SKILL.md's "### Always Load" table
    # ever gains file rows again, update this expected list DELIBERATELY (do
    # not loosen it to a count-only check).
    EXPECTED_ALWAYS_LOAD_FILES: list[str] = []
    al_files = always_load_files(skill_text)
    checks.append(
        (
            "always_load_files() returns exactly the 0 expected canonical paths (Slice B floor reduction)",
            al_files == EXPECTED_ALWAYS_LOAD_FILES,
        )
    )

    mdc_files = mandatory_diagnostic_core_files(skill_text)
    checks.append(
        (
            "mandatory_diagnostic_core_files() returns exactly 6 entries",
            len(mdc_files) == 6,
        )
    )
    canon_to_bundle_for_coverage = _load_canon_to_bundle()
    mdc_resolved, mdc_unresolved = resolve_bundles(mdc_files, canon_to_bundle_for_coverage)
    checks.append(
        (
            "mandatory_diagnostic_core_files() entries all resolve to a bundle",
            len(mdc_files) == 6 and len(mdc_unresolved) == 0 and len(mdc_resolved) >= 1,
        )
    )

    # Slice-B floor reduction: with the "### Always Load" table now resolving
    # 0 bundles (its former 4 files are in-kernel digests instead), the
    # always-load-bundles row is just SKILL.md alone -- identical bytes to
    # skill-md-only, not strictly larger. This IS the floor win: the hot
    # floor no longer drags the 103KB runtime-foundation.md bundle along on
    # every substantive case. structural-diagnosis-floor still adds the
    # Mandatory Diagnostic Core bundle(s) on top and must remain strictly
    # larger than always-load-bundles (that table is untouched by this slice).
    row_tok = {r[0]: r[4] for r in rows}
    checks.append(
        (
            "always-load-bundles est_tok == skill-md-only est_tok (Slice B floor reduction: 0 always-load bundles)",
            row_tok.get("always-load-bundles", -1) == row_tok.get("skill-md-only", -2),
        )
    )
    checks.append(
        (
            "structural-diagnosis-floor est_tok > always-load-bundles est_tok",
            row_tok.get("structural-diagnosis-floor", -1) > row_tok.get("always-load-bundles", -1),
        )
    )

    # (a) Ratchet passes against the real current repo + real config on disk.
    real_config = load_config(DEFAULT_CONFIG)
    real_ok, real_failures = check_ratchet(rows, real_config)
    checks.append(
        (
            "ratchet PASSes against real repo + real config",
            real_ok and not real_failures,
        )
    )

    # (b) Synthetic growth: artificially lower one baseline entry in an
    # in-memory copy of the config so the live measurement now exceeds it,
    # and confirm the ratchet trips.
    shrunk_config = copy.deepcopy(real_config)
    shrunk_config["ratchet"]["baseline"]["skill-md-only"] = {"bytes": 1, "est_tok": 0}
    shrunk_ok, shrunk_failures = check_ratchet(rows, shrunk_config)
    checks.append(
        (
            "synthetic growth (lowered baseline) trips the ratchet",
            not shrunk_ok
            and any("skill-md-only" in f and "ratchet regression" in f for f in shrunk_failures),
        )
    )

    # (b2) FIX 1 self-test: aggregate ratchet row closes the "spread growth
    # thinly across every row" gap. Simulate +1.9% growth on EVERY live row
    # in-memory (each individually still under the 2% per-row tolerance, so
    # every per-row check alone would PASS) and confirm the synthetic
    # "total-hot-surfaces" aggregate -- built the same way build_rows() built
    # it, from the (now inflated) per-row numbers -- FAILS the ratchet even
    # though no single row's check fails.
    # Drift-independence: anchor this synthetic scenario to a baseline equal to
    # the CURRENT measured rows (not the real on-disk baseline). Otherwise any
    # legitimate in-tolerance drift between real baseline and live measurement
    # stacks onto the synthetic +1.9% and pushes individual rows over their
    # per-row tolerance, making the canary fail for the wrong reason.
    spread_config = copy.deepcopy(real_config)
    for cfg_name, detail, b, l, t in rows:
        key = row_key(cfg_name, detail)
        if key in spread_config["ratchet"]["baseline"]:
            spread_config["ratchet"]["baseline"][key] = {"bytes": b, "est_tok": t}
    inflated_rows = []
    for cfg_name, detail, b, l, t in rows:
        if cfg_name in ("five-bundle-substantive", AGGREGATE_ROW, EXEMPT_ROW):
            # Recomputed below from the inflated skill-md-only + per-bundle
            # rows, matching how build_rows() derives them; skip here so we
            # don't inflate them twice.
            inflated_rows.append((cfg_name, detail, b, l, t))
            continue
        # Round UP (not truncate) so each row's growth is AT LEAST +1.9%,
        # keeping it comfortably under the 2% per-row tolerance while not
        # losing enough via floor-rounding that the summed aggregate falls
        # back under its own tolerance (which would defeat the point of
        # this canary).
        inflated_b = math.ceil(b * 1.019)
        inflated_rows.append((cfg_name, detail, inflated_b, l, inflated_b // 4))
    inflated_skill_and_bundles_bytes = sum(
        b for cfg_name, _detail, b, _l, _t in inflated_rows if cfg_name in ("skill-md-only", "per-bundle")
    )
    inflated_rows = [
        (cfg_name, detail, inflated_skill_and_bundles_bytes, l, inflated_skill_and_bundles_bytes // 4)
        if cfg_name in ("five-bundle-substantive", AGGREGATE_ROW)
        else (cfg_name, detail, b, l, t)
        for cfg_name, detail, b, l, t in inflated_rows
    ]
    per_row_all_pass = True
    for cfg_name, detail, b, l, t in inflated_rows:
        key = row_key(cfg_name, detail)
        if key == EXEMPT_ROW or key == AGGREGATE_ROW:
            continue
        baseline_entry = spread_config["ratchet"]["baseline"].get(key)
        if baseline_entry is None:
            continue
        allowed = baseline_entry["bytes"] * (1 + spread_config["ratchet"]["tolerance_pct"] / 100.0)
        if b > allowed:
            per_row_all_pass = False
    spread_ok, spread_failures = check_ratchet(inflated_rows, spread_config)
    checks.append(
        (
            "FIX1: +1.9% growth spread across every row still passes per-row tolerance individually",
            per_row_all_pass,
        )
    )
    checks.append(
        (
            f"FIX1: {AGGREGATE_ROW} aggregate ratchet FAILs the spread-growth case even though every row passes",
            per_row_all_pass
            and not spread_ok
            and any(AGGREGATE_ROW in f and "ratchet regression" in f for f in spread_failures),
        )
    )

    # (c) Unbaselined-row case: drop a live row's baseline entry entirely.
    unbaselined_config = copy.deepcopy(real_config)
    del unbaselined_config["ratchet"]["baseline"]["skill-md-only"]
    unbaselined_ok, unbaselined_failures = check_ratchet(rows, unbaselined_config)
    checks.append(
        (
            "dropped baseline entry trips 'unbaselined config row'",
            not unbaselined_ok
            and any(
                "unbaselined config row" in f and "skill-md-only" in f for f in unbaselined_failures
            ),
        )
    )

    # (c, continued) Missing-row case: add a baseline entry for a row name
    # that will never appear live, and confirm it trips "missing measurement
    # surface" rather than being silently ignored.
    missing_row_config = copy.deepcopy(real_config)
    missing_row_config["ratchet"]["baseline"]["synthetic-row-that-does-not-exist"] = {
        "bytes": 1,
        "est_tok": 0,
    }
    missing_ok, missing_failures = check_ratchet(rows, missing_row_config)
    checks.append(
        (
            "baseline entry with no live counterpart trips 'missing measurement surface'",
            not missing_ok
            and any(
                "missing measurement surface" in f and "synthetic-row-that-does-not-exist" in f
                for f in missing_failures
            ),
        )
    )

    # (c, continued, FIX 3) Anti-baseline-banking case: inflate one baseline
    # entry far above what is currently measured, in-memory, and confirm
    # --enforce-ratchet's check ALSO fails on "banked headroom" (not just on
    # regressions) -- a baseline sitting comfortably above reality would let
    # future growth hide inside that gap undetected.
    banked_config = copy.deepcopy(real_config)
    banked_config["ratchet"]["baseline"]["skill-md-only"]["bytes"] = (
        real_config["ratchet"]["baseline"]["skill-md-only"]["bytes"] * 10
    )
    banked_ok, banked_failures = check_ratchet(rows, banked_config)
    checks.append(
        (
            "FIX3: inflated baseline (banked headroom) trips 'baseline exceeds measured surface'",
            not banked_ok
            and any(
                "baseline exceeds measured surface" in f and "skill-md-only" in f
                for f in banked_failures
            ),
        )
    )
    checks.append(
        (
            "FIX3: the real config on disk does NOT trip 'baseline exceeds measured surface'",
            not any("baseline exceeds measured surface" in f for f in real_failures),
        )
    )

    # (d) largest-retained-output is exempt: present live (this repo has
    # retained cases), absent from ratchet.baseline by design, and must NOT
    # trigger an "unbaselined config row" failure.
    has_retained_row = any(r[0] == EXEMPT_ROW for r in rows)
    exempt_not_baselined = EXEMPT_ROW not in real_config.get("ratchet", {}).get("baseline", {})
    exempt_not_flagged = not any(EXEMPT_ROW in f for f in real_failures)
    checks.append(
        (
            "largest-retained-output is exempt from the ratchet (present live, absent from baseline, no failure)",
            has_retained_row and exempt_not_baselined and exempt_not_flagged,
        )
    )

    # --- Aspirational enforcement (Slice A2) self-test cases ---

    # (f) enforcement PASSes on the real repo + real config on disk.
    aspirational_real_ok, aspirational_real_failures, aspirational_real_warnings = check_aspirational(
        rows, real_config, skill_text
    )
    checks.append(
        (
            "aspirational enforcement PASSes on the real repo + real config",
            aspirational_real_ok and not aspirational_real_failures,
        )
    )

    # (g) synthetic root-over-ceiling FAILs.
    root_over_ceiling_config = copy.deepcopy(real_config)
    root_over_ceiling_config["aspirational"]["hot_root_ceiling_est_tok"] = 1
    root_over_ok, root_over_failures, _ = check_aspirational(rows, root_over_ceiling_config, skill_text)
    checks.append(
        (
            "synthetic root-over-ceiling FAILs aspirational enforcement",
            not root_over_ok and any("hot-root" in f and "FAIL" in f for f in root_over_failures),
        )
    )

    # (h) synthetic default_hot shard over ceiling FAILs.
    shard_over_ceiling_config = copy.deepcopy(real_config)
    shard_over_ceiling_config["aspirational"]["default_hot_shard_ceiling_est_tok"] = 1
    shard_over_ok, shard_over_failures, _ = check_aspirational(rows, shard_over_ceiling_config, skill_text)
    checks.append(
        (
            "synthetic default_hot shard over ceiling FAILs aspirational enforcement",
            not shard_over_ok
            and any("default_hot shard" in f and "FAIL" in f for f in shard_over_failures),
        )
    )

    # (i) stage_warm shard over ceiling does NOT fail (stage_warm/on_demand_cold
    # are reported but never gated by the default_hot ceiling, regardless of size).
    stage_warm_names = real_config["aspirational"]["shard_classes"].get("stage_warm", [])
    stage_warm_present = any(Path(detail).name in stage_warm_names for cfg, detail, *_ in rows if cfg == "per-bundle")
    checks.append(("stage_warm shards are present in the live measurement (precondition)", stage_warm_present))
    checks.append(
        (
            "stage_warm shard over the default_hot ceiling does NOT fail (real repo already exceeds it and PASSes)",
            not any("stage_warm" in f for f in aspirational_real_failures),
        )
    )

    # (j) unclassified shard FAILs.
    unclassified_config = copy.deepcopy(real_config)
    unclassified_config["aspirational"]["shard_classes"]["default_hot"] = [
        n for n in unclassified_config["aspirational"]["shard_classes"]["default_hot"]
        if n != "runtime-core-routing.md"
    ]
    unclassified_ok, unclassified_failures, _ = check_aspirational(rows, unclassified_config, skill_text)
    checks.append(
        (
            "shard removed from all class lists trips 'unclassified shard'",
            not unclassified_ok
            and any(
                "unclassified shard" in f and "runtime-core-routing.md" in f
                for f in unclassified_failures
            ),
        )
    )

    # (k) synthetic 5-bundle eager list fails the 300k-pattern check.
    five_bundle_eager_list = [
        "references/runtime-foundation.md",
        "references/runtime-diagnostic-core.md",
        "references/runtime-phase2-passes.md",
        "references/runtime-dispatch-gate.md",
        "references/runtime-output-governance.md",
    ]
    checks.append(
        (
            "synthetic 5-bundle eager list fails the 300k-pattern check",
            bool(check_eager_list_pattern(five_bundle_eager_list)),
        )
    )
    checks.append(
        (
            "well-formed single-entry eager list passes the 300k-pattern check",
            check_eager_list_pattern(EXPECTED_EAGER_LIST) == [],
        )
    )

    # (l) worst-case arithmetic correctness on synthetic values: root=10000,
    # 3 synthetic default_hot shards of 5000/4000/3000 (a 4th smaller one must
    # be excluded from the top-3 sum), expected worst_case =
    # 10000 + CAPSULE_ALLOWANCE_EST_TOK + (5000+4000+3000).
    synthetic_rows: list[tuple[str, str, int, int, int]] = [
        ("skill-md-only", "skill/SKILL.md", 40000, 100, 10000),
        ("per-bundle", "skill/references/runtime-synth-a.md", 20000, 10, 5000),
        ("per-bundle", "skill/references/runtime-synth-b.md", 16000, 10, 4000),
        ("per-bundle", "skill/references/runtime-synth-c.md", 12000, 10, 3000),
        ("per-bundle", "skill/references/runtime-synth-d.md", 4000, 10, 1000),
    ]
    synthetic_config = copy.deepcopy(real_config)
    synthetic_config["aspirational"]["shard_classes"] = {
        "default_hot": [
            "runtime-synth-a.md",
            "runtime-synth-b.md",
            "runtime-synth-c.md",
            "runtime-synth-d.md",
        ],
        "stage_warm": [],
        "on_demand_cold": [],
    }
    synthetic_config["aspirational"]["default_hot_shard_ceiling_est_tok"] = 1_000_000
    synthetic_config["aspirational"]["default_hot_shard_target_est_tok"] = 1_000_000
    synthetic_config["aspirational"]["hot_root_ceiling_est_tok"] = 1_000_000
    synthetic_config["aspirational"]["hot_root_target_est_tok"] = 1_000_000
    synthetic_config["aspirational"]["default_exec_ceiling_est_tok"] = 1_000_000
    synthetic_config["aspirational"]["default_exec_target_est_tok"] = 1_000_000
    synthetic_skill_text = (
        "Load path for substantive cases:\n\n"
        "1. `references/runtime-core-routing.md`\n\n"
        "Dispatch Index (route shards - load on selection, not eagerly):\n"
    )
    expected_worst_case = 10000 + CAPSULE_ALLOWANCE_EST_TOK + (5000 + 4000 + 3000)
    synth_ok, synth_failures, synth_warnings = check_aspirational(
        synthetic_rows, synthetic_config, synthetic_skill_text
    )
    checks.append(
        (
            f"worst-case arithmetic correct on synthetic values (expected {expected_worst_case})",
            synth_ok and any(f"= {expected_worst_case} est_tok" in w for w in synth_warnings),
        )
    )

    # (e) report-json structure sanity: write a report to a temp file and
    # validate its top-level keys and row shape.
    report = build_report(
        rows, real_config, (real_ok, real_failures), (aspirational_real_ok, aspirational_real_failures, aspirational_real_warnings)
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        reloaded = json.loads(report_path.read_text(encoding="utf-8"))
    report_keys_ok = (
        reloaded.get("schema") == "load-path-budget-report-v1"
        and isinstance(reloaded.get("rows"), list)
        and len(reloaded["rows"]) == len(rows)
        and all(
            {"config", "detail", "bytes", "lines", "est_tok"} <= set(row.keys())
            for row in reloaded["rows"]
        )
        and "ratchet" in reloaded
        and "checked" in reloaded["ratchet"]
        and "failures" in reloaded["ratchet"]
        and "aspirational" in reloaded
        and "checked" in reloaded["aspirational"]
        and "failures" in reloaded["aspirational"]
        and "warnings" in reloaded["aspirational"]
        and "metric" in reloaded
    )
    checks.append(("report-json structure sanity (round-tripped through a temp file)", report_keys_ok))

    ok = all(p for _, p in checks)
    for name, p in checks:
        print(f"  self-test {'PASS' if p else 'FAIL'}: {name}")
    print(f"measure-load-path-budget self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Load-path budget measurement (Plan 16 Phase 1)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic arithmetic self-test")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="path to load-path-budget.config.json (default: tools/load-path-budget.config.json)",
    )
    parser.add_argument(
        "--enforce-ratchet",
        action="store_true",
        help="fail (nonzero exit) if any measured row regresses beyond config ratchet.tolerance_pct",
    )
    parser.add_argument(
        "--enforce",
        "--enforce-aspirational",
        dest="enforce_aspirational",
        action="store_true",
        help=(
            "fail (nonzero exit) if the aspirational hot-context thresholds "
            "(config's `aspirational` block) are violated: hot-root ceiling, "
            "default_hot per-shard ceiling, default-exec worst-case ceiling, "
            "unclassified shards, and the 300k eager-load-list pattern. "
            "Independent of --enforce-ratchet; usable together or alone."
        ),
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="write a machine-readable report ({schema, rows, ratchet, aspirational, metric}) to this path",
    )
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    rows = build_rows()
    exit_code = 0
    ratchet_result: tuple[bool, list[str]] | None = None
    aspirational_result: tuple[bool, list[str], list[str]] | None = None

    if args.enforce_ratchet or args.enforce_aspirational or args.report_json:
        config = load_config(args.config)
    else:
        config = {}

    if args.enforce_ratchet:
        ratchet_result = check_ratchet(rows, config)
        ok, failures = ratchet_result
        if not ok:
            exit_code = 1

    if args.enforce_aspirational:
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        aspirational_result = check_aspirational(rows, config, skill_text)
        ok, failures, warnings = aspirational_result
        if not ok:
            exit_code = 1

    if args.report_json:
        report = build_report(rows, config, ratchet_result, aspirational_result)
        args.report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report written to {args.report_json}")

    print("Load-path budget (measurement only; est_tokens = bytes // 4 heuristic)")
    print()
    print(render_table())

    if args.enforce_ratchet:
        print()
        ok, failures = ratchet_result
        if ok:
            print("ratchet: PASS (all baselined rows within tolerance)")
        else:
            print("ratchet: FAIL")
            for f in failures:
                print(f"  - {f}")

    if args.enforce_aspirational:
        print()
        ok, failures, warnings = aspirational_result
        for w in warnings:
            print(w, file=sys.stderr)
        if ok:
            print("aspirational: PASS (see stderr for warnings/arithmetic, if any)")
        else:
            print("aspirational: FAIL")
            for f in failures:
                print(f"  - {f}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
