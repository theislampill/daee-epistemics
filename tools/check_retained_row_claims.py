#!/usr/bin/env python3
"""Replay retained-corpus row claims against their bound validators.

The retained proof corpus makes row-scoped claims: each case claims specific
rows, and each coverage target binds a row to the validator evidence that
guards it (`validator_binding`). This driver executes exactly that binding
scope, so a claim failure means a claimed row is no longer supported under
current validator semantics, while validator behavior on unclaimed surfaces
remains advisory context rather than claim failure.

It does not weaken or replace any validator: graph-key bindings consume
`tools/check_graph_completeness.py --json` per-condition results, and
outputs-checker bindings invoke the bound checker unchanged over exactly the
claiming cases. `corpus-integrity` bindings are enforced by
`tools/check_retained_proof_corpus.py`, and `documented-evidence` bindings
name their ledger surface; both are reported, not re-executed here.

A PASS is corpus row-claim truthfulness only. It is not release/provenance
proof, not model-behavior proof, and not evidence for unclaimed rows.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MANIFEST = (
    ROOT
    / "tests"
    / "retained-proof-corpus"
    / "v0.4.3.0-schema-light"
    / "valid"
    / "sidecar-backed"
    / "manifest.json"
)
GRAPH_CHECKER = "tools/check_graph_completeness.py"
BINDING_KINDS = {"graph-keys", "outputs-checker", "corpus-integrity", "documented-evidence"}


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def claimed_row_coverage_gaps(cases: list[dict], targets: list[dict]) -> list[str]:
    """Every row claimed by any case must be covered by >=1 coverage target."""
    covered: set[str] = set()
    for target in targets:
        covered.update(target.get("rows") or [])
    gaps: list[str] = []
    for case in cases:
        for row in case.get("rows") or []:
            if row not in covered:
                gaps.append(f"row {row} claimed by {case.get('id')} has no coverage target")
    return gaps


def missing_binding_errors(targets: list[dict]) -> list[str]:
    errors: list[str] = []
    for target in targets:
        binding = target.get("validator_binding")
        if not isinstance(binding, dict) or binding.get("kind") not in BINDING_KINDS:
            errors.append(
                f"coverage target {target.get('id')} lacks a valid validator_binding"
            )
    return errors


def evaluate_graph_binding(keys: list[str], failing_keys: list[str]) -> list[str]:
    """Return the bound keys that fail for one case."""
    if keys == ["ALL"]:
        return list(failing_keys)
    return [key for key in keys if key in failing_keys]


def parse_graph_json(stdout: str) -> dict[str, list[str]]:
    """Map case id -> failing condition keys from graph --json output."""
    lines = stdout.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "["), None)
    if start is None:
        raise ValueError("graph checker emitted no JSON payload")
    records = json.loads("\n".join(lines[start:]))
    failing: dict[str, list[str]] = {}
    for record in records:
        parts = Path(record.get("path", "")).parts
        case_id = parts[parts.index("cases") + 1] if "cases" in parts else record.get("path", "?")
        failing[case_id] = sorted(record.get("failures") or [])
    return failing


def case_output_path(manifest_path: Path, case: dict) -> Path:
    return (manifest_path.parent / case["output"]).resolve()


def run_claims(manifest_path: Path) -> int:
    manifest = load_manifest(manifest_path)
    cases = manifest.get("cases") or []
    targets = manifest.get("coverage_targets") or []
    cases_by_id = {case["id"]: case for case in cases}

    errors: list[str] = []
    errors.extend(missing_binding_errors(targets))
    errors.extend(claimed_row_coverage_gaps(cases, targets))
    if errors:
        for error in errors:
            print(f"- {error}")
        print(f"retained row-claim check: FAIL ({len(errors)} structural errors)")
        return 1

    graph_targets = [t for t in targets if t["validator_binding"]["kind"] == "graph-keys"]
    graph_case_ids: list[str] = []
    for target in graph_targets:
        for case_id in target["case_ids"]:
            if case_id not in graph_case_ids:
                graph_case_ids.append(case_id)

    failing_by_case: dict[str, list[str]] = {}
    if graph_case_ids:
        outputs = [str(case_output_path(manifest_path, cases_by_id[c])) for c in graph_case_ids]
        proc = subprocess.run(
            [sys.executable, str(ROOT / GRAPH_CHECKER), "--json", "--outputs", *outputs],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        try:
            failing_by_case = parse_graph_json(proc.stdout)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"- graph checker JSON parse failed: {exc}")
            print("retained row-claim check: FAIL (graph evidence unavailable)")
            return 1

    failures: list[str] = []
    executed = informational = 0
    for target in targets:
        binding = target["validator_binding"]
        kind = binding["kind"]
        target_id = target["id"]
        case_ids = target["case_ids"]
        if kind == "graph-keys":
            executed += 1
            bad: list[str] = []
            for case_id in case_ids:
                failed = evaluate_graph_binding(binding["keys"], failing_by_case.get(case_id, []))
                if failed:
                    bad.append(f"{case_id}:{','.join(failed)}")
            verdict = "PASS" if not bad else "FAIL"
            print(f"{target_id} | graph-keys {binding['keys']} | cases={len(case_ids)} | {verdict}")
            if bad:
                failures.append(f"{target_id}: {'; '.join(bad)}")
        elif kind == "outputs-checker":
            executed += 1
            outputs = [str(case_output_path(manifest_path, cases_by_id[c])) for c in case_ids]
            command = [sys.executable, str(ROOT / binding["tool"]), *binding.get("args", []), *outputs]
            proc = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
            verdict = "PASS" if proc.returncode == 0 else "FAIL"
            print(f"{target_id} | {binding['tool']} | cases={len(case_ids)} | {verdict}")
            if proc.returncode != 0:
                tail = [line for line in proc.stdout.splitlines() if line.strip()][-3:]
                failures.append(f"{target_id}: exit {proc.returncode}; " + " / ".join(tail))
        elif kind == "corpus-integrity":
            informational += 1
            print(
                f"{target_id} | corpus-integrity | cases={len(case_ids)} | "
                "ENFORCED-BY check_retained_proof_corpus.py"
            )
        else:
            informational += 1
            print(
                f"{target_id} | documented-evidence | cases={len(case_ids)} | "
                f"SEE {binding['evidence']}"
            )

    if failures:
        for failure in failures:
            print(f"- {failure}")
        print(
            f"retained row-claim check: FAIL ({len(failures)} bound targets failed; "
            f"{executed} executed, {informational} informational)"
        )
        return 1
    print("retained row-claim check: PASS")
    print(f"Coverage targets replayed: {executed} executed, {informational} informational")
    print(f"Cases in corpus: {len(cases)}")
    return 0


def run_self_test() -> int:
    failures: list[str] = []

    if evaluate_graph_binding(["ALL"], []) != []:
        failures.append("ALL binding should pass with no failing keys")
    if evaluate_graph_binding(["ALL"], ["two_track_mrp_closure"]) != ["two_track_mrp_closure"]:
        failures.append("ALL binding must surface any failing key")
    if evaluate_graph_binding(["no_new_resultant_terminal_proof"], ["two_track_mrp_closure"]) != []:
        failures.append("key-scoped binding must ignore unclaimed failing keys")
    if evaluate_graph_binding(["two_track_mrp_closure"], ["two_track_mrp_closure"]) != [
        "two_track_mrp_closure"
    ]:
        failures.append("key-scoped binding must fail on its claimed key")

    cases = [{"id": "c1", "rows": ["B.1", "C.8"]}]
    targets = [{"id": "t1", "rows": ["B.1"], "case_ids": ["c1"]}]
    gaps = claimed_row_coverage_gaps(cases, targets)
    if gaps != ["row C.8 claimed by c1 has no coverage target"]:
        failures.append(f"row coverage gap not detected: {gaps}")
    targets.append({"id": "t2", "rows": ["C.8"], "case_ids": ["c1"]})
    if claimed_row_coverage_gaps(cases, targets):
        failures.append("covered rows must not report gaps")

    if not missing_binding_errors([{"id": "t3", "rows": ["B.1"], "case_ids": ["c1"]}]):
        failures.append("missing validator_binding must be a structural error")
    if missing_binding_errors(
        [{"id": "t4", "rows": ["B.1"], "case_ids": ["c1"], "validator_binding": {"kind": "graph-keys", "keys": ["ALL"]}}]
    ):
        failures.append("valid binding must not be a structural error")

    sample_stdout = "\n".join(
        [
            "graph-completeness check: FAIL",
            "[",
            json.dumps(
                {
                    "path": "tests/x/cases/sample-case/output.md",
                    "failures": ["two_track_mrp_closure"],
                    "conditions": {},
                }
            ),
            "]",
        ]
    )
    parsed = parse_graph_json(sample_stdout)
    if parsed != {"sample-case": ["two_track_mrp_closure"]}:
        failures.append(f"graph JSON parsing failed: {parsed}")

    if failures:
        for failure in failures:
            print(f"- {failure}")
        print(f"retained row-claim self-test: FAIL ({len(failures)} failures)")
        return 1
    print("retained row-claim self-test: PASS")
    print("Logic scenarios checked: 9")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=CANONICAL_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    return run_claims(args.manifest)


if __name__ == "__main__":
    sys.exit(main())
