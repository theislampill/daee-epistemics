#!/usr/bin/env python3
"""Advisory-drift gate for the retained proof corpus (Plan 05).

Runs the six visible-output probes over the 24 retained outputs and enforces a
dated allowlist of KNOWN advisory drift, so new drift cannot slip in unnoticed
and repaired cases cannot keep a stale grandfathering entry.

Each (checker, case) failure is classified:
  - BOUND  -> the pair is already enforced by a manifest `outputs-checker`
             coverage target (i.e. check_retained_row_claims owns it). A BOUND
             failure must be fixed there, never laundered through this allowlist.
  - ADVISORY -> not bound by any coverage target; recorded in the dated allowlist.

Exit 1 (fail) when:
  - an ADVISORY failure is not in the allowlist (new drift),
  - an allowlisted pair now PASSES (stale entry — repaired, drop it),
  - an allowlist case_id is not in the manifest,
  - a BOUND pair fails (belongs to check_retained_row_claims, not here).

Probe capture is by per-output subprocess EXIT CODE — deterministic, no stdout
parsing. The pass/fail comparison logic is a pure function (`evaluate`) that
`--self-test` exercises with synthetic inputs, so the self-test is deterministic
and does not depend on running the probes.

This is a structural drift gate, not a semantic or provenance claim. See
docs/audits/retained-corpus-requalification-ledger.md and docs/non-claims.md.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed"
MANIFEST = CORPUS / "manifest.json"
ALLOWLIST = ROOT / "tests/retained-proof-corpus/advisory-allowlist.json"
ALLOWLIST_SCHEMA = "retained-corpus-advisory-allowlist-v1"

PROBES = [
    "check_act_surface_syntax",
    "check_public_burden_grouping",
    "check_mid_reread_pressure",
    "check_mrp_route_invariants",
    "check_manual_smoke_render_contract",
    "check_concealment_mode",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def case_ids() -> list[str]:
    return sorted(p.name for p in (CORPUS / "cases").iterdir() if (p / "output.md").exists())


def manifest_case_ids(manifest) -> set[str]:
    return {c["id"] for c in manifest.get("cases", []) if isinstance(c, dict) and "id" in c}


def bound_pairs(manifest) -> set[tuple[str, str]]:
    """(checker_stem, case_id) pairs enforced by manifest outputs-checker bindings."""
    pairs: set[tuple[str, str]] = set()
    for target in manifest.get("coverage_targets", []):
        binding = target.get("validator_binding", {})
        if binding.get("kind") == "outputs-checker":
            checker = Path(binding["tool"]).stem
            for case in target.get("case_ids", []):
                pairs.add((checker, case))
    return pairs


def probe_passes(checker: str, case: str) -> bool:
    """True iff the checker accepts this single retained output (exit 0)."""
    output = CORPUS / "cases" / case / "output.md"
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / f"{checker}.py"), "--outputs", str(output)],
        capture_output=True,
    )
    return result.returncode == 0


def scan_failing_pairs() -> set[tuple[str, str]]:
    """Run every probe over every case; return the failing (checker, case) pairs."""
    failing: set[tuple[str, str]] = set()
    for checker in PROBES:
        for case in case_ids():
            if not probe_passes(checker, case):
                failing.add((checker, case))
    return failing


def load_allowlist() -> tuple[dict, set[tuple[str, str]]]:
    data = load_json(ALLOWLIST)
    pairs = {(e["checker"], e["case_id"]) for e in data.get("entries", [])}
    return data, pairs


def evaluate(
    failing: set[tuple[str, str]],
    bound: set[tuple[str, str]],
    allowlist_pairs: set[tuple[str, str]],
    manifest_cases: set[str],
) -> list[str]:
    """Pure comparison core (deterministic; unit-tested by --self-test)."""
    errors: list[str] = []

    # A BOUND pair that fails belongs to check_retained_row_claims, not here.
    for checker, case in sorted(failing & bound):
        errors.append(
            f"BOUND failure not allowlistable here: ({checker}, {case}) is enforced by a "
            f"manifest outputs-checker binding; fix it at check_retained_row_claims"
        )

    advisory_failing = failing - bound
    # New advisory drift: an advisory failure with no allowlist entry.
    for checker, case in sorted(advisory_failing - allowlist_pairs):
        errors.append(f"new advisory drift (not allowlisted): ({checker}, {case})")

    # Stale entry: an allowlisted pair that now passes.
    for checker, case in sorted(allowlist_pairs - failing):
        errors.append(f"stale allowlist entry (case now passes; remove it): ({checker}, {case})")

    # Allowlist hygiene: every allowlisted case must exist in the manifest, and
    # every allowlisted checker must be a known probe.
    for checker, case in sorted(allowlist_pairs):
        if case not in manifest_cases:
            errors.append(f"allowlist case not in manifest: {case}")
        if checker not in PROBES:
            errors.append(f"allowlist checker not a known probe: {checker}")

    return errors


def emit_allowlist() -> int:
    """Bootstrap: write the allowlist from the current ADVISORY failing set."""
    manifest = load_json(MANIFEST)
    bound = bound_pairs(manifest)
    failing = scan_failing_pairs()
    advisory = sorted(failing - bound)
    blocked = sorted(failing & bound)
    if blocked:
        print("refusing to emit: BOUND failures present (fix at check_retained_row_claims):")
        for checker, case in blocked:
            print(f"  ({checker}, {case})")
        return 1
    entries = [
        {
            "case_id": case,
            "checker": checker,
            "status": "known_contract_drift",
            "note_ref": "docs/audits/retained-corpus-requalification-ledger.md",
            "as_of": "2026-07-04",
        }
        for checker, case in advisory
    ]
    payload = {
        "schema": ALLOWLIST_SCHEMA,
        "description": (
            "Dated allowlist of known advisory (non-bound) drift of retained corpus outputs "
            "vs current visible-output probes. Bound failures are enforced by "
            "check_retained_row_claims, not here. See the requalification ledger."
        ),
        "entries": entries,
    }
    ALLOWLIST.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {ALLOWLIST.relative_to(ROOT)} with {len(entries)} advisory entries")
    return 0


def self_test() -> int:
    """Deterministic unit test of evaluate() with synthetic inputs (no probes run)."""
    bound = {("check_concealment_mode", "cd9a-mixed-concealment")}
    manifest_cases = {"cd9a-mixed-concealment", "gate88-khaybar", "exact-secularism", "repaired-case"}
    allowlist = {
        ("check_mrp_route_invariants", "gate88-khaybar"),
        ("check_concealment_mode", "exact-secularism"),
        ("check_mid_reread_pressure", "repaired-case"),  # will be "stale" below
    }
    # Scenario: gate88-khaybar advisory failure is allowlisted (ok);
    #   a NEW advisory drift appears; a BOUND pair fails; the repaired-case entry is stale.
    failing = {
        ("check_mrp_route_invariants", "gate88-khaybar"),      # allowlisted advisory -> ok
        ("check_public_burden_grouping", "gate88-khaybar"),    # NEW advisory drift -> error
        ("check_concealment_mode", "cd9a-mixed-concealment"),  # BOUND failure -> error
        # ("check_mid_reread_pressure", "repaired-case") absent -> stale entry error
    }
    errors = evaluate(failing, bound, allowlist, manifest_cases)
    checks = [
        ("new-drift detected", any("new advisory drift" in e and "gate88-khaybar" in e for e in errors)),
        ("bound failure detected", any("BOUND failure" in e and "cd9a-mixed-concealment" in e for e in errors)),
        ("stale entry detected", any("stale allowlist entry" in e and "repaired-case" in e for e in errors)),
    ]
    # Negative control: a clean scenario must yield no errors.
    clean = evaluate(
        {("check_mrp_route_invariants", "gate88-khaybar")},
        set(),
        {("check_mrp_route_invariants", "gate88-khaybar")},
        {"gate88-khaybar"},
    )
    checks.append(("clean scenario has no errors", clean == []))
    ok = all(passed for _, passed in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"retained-corpus advisory self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run deterministic logic self-test and exit")
    parser.add_argument("--emit-allowlist", action="store_true", help="bootstrap the allowlist from current advisory drift")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.emit_allowlist:
        return emit_allowlist()

    if not ALLOWLIST.exists():
        print(f"missing allowlist: {ALLOWLIST.relative_to(ROOT)} (run --emit-allowlist to bootstrap)")
        return 1

    manifest = load_json(MANIFEST)
    bound = bound_pairs(manifest)
    _, allowlist_pairs = load_allowlist()
    failing = scan_failing_pairs()
    errors = evaluate(failing, bound, allowlist_pairs, manifest_case_ids(manifest))

    if errors:
        print("retained-corpus advisory drift check: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print(
        f"retained-corpus advisory drift check: PASS "
        f"({len(failing - bound)} advisory failures, all allowlisted; {len(failing & bound)} bound)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
