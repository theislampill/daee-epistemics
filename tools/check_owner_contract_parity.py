#!/usr/bin/env python3
"""Owner/TTP contract parity checker — Plan 17 Phase 2 (neutral correctness).

Makes one well-defined, non-brittle consistency invariant a failing check:

  every family used as a key in check_mrp_generated_burden.SOURCE_OWNED_ACT_OPERATIONS
  must exist in delta-result-vocabulary.json's `owner_families`,

unless that family is quarantined in a dated allowlist. This catches the
"silent loosening as sync" risk from the drift inventory (Plan 17 Phase 1,
docs/audits/owner-contract-drift-inventory.md): adding a family to the checker
table that the machine vocabulary never declared would otherwise pass unnoticed.

Scope discipline (this checker does NOT):
  - decide which representation is canonical for any drift,
  - admit, remove, or reword any owner operation / family / contract,
  - author any owner/TTP contract semantics,
  - compare the formal-contract IDs (a different namespace) against families.
Those are owner decisions (Plan 17 Phases 3-5). Known/intentional exceptions go
in tests/owner-contract-parity/allowlist.json with a reason and a date; the
executor never edits an owner representation to make this pass.

The reverse direction (vocabulary families with no SOURCE_OWNED entry) is
reported as coverage information only, never failed — partial coverage is by
design, not drift.

Usage:
  python tools/check_owner_contract_parity.py
  python tools/check_owner_contract_parity.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB = ROOT / "atomics" / "skill" / "references" / "diagnostics" / "delta-result-vocabulary.json"
ALLOWLIST = ROOT / "tests" / "owner-contract-parity" / "allowlist.json"
ALLOWLIST_SCHEMA = "owner-contract-parity-allowlist-v1"


def evaluate(vocab_families: set[str], checker_families: set[str], allowlisted: set[str]) -> list[str]:
    """Pure core (unit-tested): return sorted error strings; empty == PASS."""
    orphans = sorted(checker_families - vocab_families - allowlisted)
    return [
        f"SOURCE_OWNED_ACT_OPERATIONS family {fam!r} is not in "
        f"delta-result-vocabulary owner_families (declare it in the vocabulary, "
        f"or quarantine it in {ALLOWLIST.name} with a reason and date)"
        for fam in orphans
    ]


def _load_allowlist() -> set[str]:
    if not ALLOWLIST.is_file():
        return set()
    data = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    if data.get("schema") != ALLOWLIST_SCHEMA:
        raise SystemExit(f"{ALLOWLIST}: schema must be {ALLOWLIST_SCHEMA!r}")
    return {e["family"] for e in data.get("entries", []) if "family" in e}


def _disk_state() -> tuple[set[str], set[str], set[str]]:
    vocab = json.loads(VOCAB.read_text(encoding="utf-8"))
    vocab_families = set(vocab.get("owner_families", {}))
    sys.path.insert(0, str(ROOT / "tools"))
    import check_mrp_generated_burden as mgb  # heavy import; resolves with tools/ on path
    checker_families = set(mgb.SOURCE_OWNED_ACT_OPERATIONS)
    return vocab_families, checker_families, _load_allowlist()


def self_test() -> int:
    cases = [
        ("clean subset -> pass", evaluate({"A", "B"}, {"A"}, set()) == []),
        ("orphan family flagged",
         any("'X'" in e for e in evaluate({"A"}, {"A", "X"}, set()))),
        ("allowlisted orphan passes", evaluate({"A"}, {"A", "X"}, {"X"}) == []),
        ("multiple orphans sorted",
         [e.split("family ")[1][:3] for e in evaluate({"A"}, {"A", "Z", "M"}, set())] == ["'M'", "'Z'"]),
    ]
    ok = all(p for _, p in cases)
    for name, p in cases:
        print(f"  self-test {'PASS' if p else 'FAIL'}: {name}")
    print(f"owner-contract-parity self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Owner/TTP contract parity checker (Plan 17 Phase 2)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic evaluate() self-test")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    vocab_families, checker_families, allowlisted = _disk_state()
    errors = evaluate(vocab_families, checker_families, allowlisted)
    coverage_gap = sorted(vocab_families - checker_families)
    if errors:
        print(f"owner-contract parity: FAIL ({len(errors)} orphan family/families)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        f"owner-contract parity: PASS "
        f"({len(checker_families)} SOURCE_OWNED families all declared in vocabulary; "
        f"{len(allowlisted)} allowlisted; {len(coverage_gap)} vocabulary families uncovered [info])"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
