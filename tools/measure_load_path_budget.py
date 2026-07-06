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
        baseline bytes * (1 + tolerance_pct/100).

    Returns (ok, failure_messages).
    """
    ratchet = config.get("ratchet", {})
    tolerance_pct = ratchet.get("tolerance_pct", 0.0)
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
        baseline_bytes = baseline[key].get("bytes")
        allowed_bytes = baseline_bytes * (1 + tolerance_pct / 100.0)
        if measured_bytes > allowed_bytes:
            failures.append(
                f"ratchet regression: row '{key}' measured bytes={measured_bytes} exceeds "
                f"baseline bytes={baseline_bytes} + tolerance {tolerance_pct}% "
                f"(allowed<={allowed_bytes:.0f})."
            )

    for key in baseline:
        if key not in live_keys:
            failures.append(
                f"missing measurement surface: row '{key}' is present in ratchet.baseline "
                f"but was not produced by the current measurement. A disappearing "
                f"measurement surface is treated as a regression."
            )

    return len(failures) == 0, failures


def build_report(rows: list[tuple[str, str, int, int, int]], config: dict, ratchet_result: tuple[bool, list[str]] | None) -> dict:
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

    # Real-repo Always-Load resolution must have zero unresolved entries and
    # at least one resolved bundle -- an unresolved entry in the live repo is
    # a self-test FAIL, not a soft warning.
    al_bundles, al_unresolved = always_load_bundles(skill_text)
    checks.append(("always-load resolves >=1 bundle in the live repo", len(al_bundles) >= 1))
    checks.append(("always-load has 0 unresolved entries in the live repo", len(al_unresolved) == 0))

    # always-load-bundles must be strictly larger than skill-md-only (it adds
    # at least the runtime-foundation.md bundle), and structural-diagnosis-floor
    # must be strictly larger than always-load-bundles (it adds the
    # runtime-diagnostic-core.md bundle on top).
    row_tok = {r[0]: r[4] for r in rows}
    checks.append(
        (
            "always-load-bundles est_tok > skill-md-only est_tok",
            row_tok.get("always-load-bundles", -1) > row_tok.get("skill-md-only", -1),
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

    # (e) report-json structure sanity: write a report to a temp file and
    # validate its top-level keys and row shape.
    report = build_report(rows, real_config, (real_ok, real_failures))
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
        "--report-json",
        type=Path,
        default=None,
        help="write a machine-readable report ({schema, rows, ratchet, metric}) to this path",
    )
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    rows = build_rows()
    exit_code = 0
    ratchet_result: tuple[bool, list[str]] | None = None

    if args.enforce_ratchet or args.report_json:
        config = load_config(args.config)
    else:
        config = {}

    if args.enforce_ratchet:
        ratchet_result = check_ratchet(rows, config)
        ok, failures = ratchet_result
        if not ok:
            exit_code = 1

    if args.report_json:
        report = build_report(rows, config, ratchet_result)
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

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
