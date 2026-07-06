#!/usr/bin/env python3
"""Terminal-cover A/B measurement harness (Plan 16, measurement-only).

MEASURES and REPORTS the per-case terminal-cover state of the 24 retained proof
outputs, and -- given a candidate strengthened checker -- the delta a
strengthening would introduce. It does NOT strengthen any checker, gate CI,
mutate any retained output, or change terminal-cover semantics. It is the
evidence instrument for the A/B-gated Plan 16 terminal-cover strengthening
decision: it lets the owner see, in one command, exactly which retained cases a
candidate would newly fail before that candidate is ever wired.

"Terminal cover" is the ``no_new_resultant_terminal_proof`` graph condition in
``tools/check_graph_completeness.py``: a claimed terminal STOP must be backed by
an actual terminal-stop proof count, not an empty terminal claim. Per case,
terminal-cover PASSES iff that condition is absent from the case's ``--json``
``failures`` list. This is the same per-condition surface that
``tools/check_retained_row_claims.py`` consumes; the underlying checker's overall
exit code is deliberately ignored (it reflects unrelated conditions over the
retained outputs), so the measurement reads only the terminal-cover boolean.

Each case is classified:
  - BOUND    -> its terminal-cover claim is enforced by a manifest ``graph-keys``
               coverage target (keys ``ALL`` or ``no_new_resultant_terminal_proof``).
               A candidate that newly fails a BOUND case is a hard regression --
               it would break ``check_retained_row_claims`` -- never allowlistable.
  - ADVISORY -> not bound by such a target; a newly-failing ADVISORY case is
               allowlist-eligible, not a hard regression.

With no ``--candidate`` the candidate equals the current checker, the delta is
empty, and the tool prints the current baseline snapshot for the 24 cases. With
``--candidate <path>`` it additionally prints the newly-failing cases split
BOUND/ADVISORY.

The pass/fail comparison is a pure function (``summarize``) that ``--self-test``
exercises with synthetic inputs, so the self-test is deterministic and runs no
subprocess. Measurement only; never a semantic or provenance claim; a live run
always exits 0 (like ``tools/measure_load_path_budget.py``). Only ``--self-test``
gates.
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
CURRENT_CHECKER = ROOT / "tools" / "check_graph_completeness.py"
TERMINAL_COVER_KEY = "no_new_resultant_terminal_proof"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def case_ids() -> list[str]:
    return sorted(p.name for p in (CORPUS / "cases").iterdir() if (p / "output.md").exists())


def case_output(case: str) -> Path:
    return CORPUS / "cases" / case / "output.md"


def bound_case_ids(manifest, key: str = TERMINAL_COVER_KEY) -> set[str]:
    """Cases whose terminal-cover is a bound claim.

    A case is BOUND iff it appears in a ``graph-keys`` coverage target whose keys
    are ``["ALL"]`` or explicitly include the terminal-cover key.
    """
    bound: set[str] = set()
    for target in manifest.get("coverage_targets", []):
        binding = target.get("validator_binding", {})
        if binding.get("kind") == "graph-keys":
            keys = binding.get("keys", [])
            if keys == ["ALL"] or key in keys:
                bound.update(target.get("case_ids", []))
    return bound


def parse_graph_json(stdout: str) -> dict[str, list[str]]:
    """Map case id -> failing condition keys from graph ``--json`` output.

    Mirrors ``tools/check_retained_row_claims.parse_graph_json``: the JSON array
    is printed after human-readable summary lines, so start at the first line
    that is exactly ``[``.
    """
    lines = stdout.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "["), None)
    if start is None:
        raise ValueError("graph checker emitted no JSON payload")
    records = json.loads("\n".join(lines[start:]))
    failing: dict[str, list[str]] = {}
    for record in records:
        parts = Path(record.get("path", "")).parts
        cid = parts[parts.index("cases") + 1] if "cases" in parts else record.get("path", "?")
        failing[cid] = sorted(record.get("failures") or [])
    return failing


def terminal_cover_state(
    failing_by_case: dict[str, list[str]], cases: list[str], key: str = TERMINAL_COVER_KEY
) -> dict[str, bool]:
    """Per case, True iff terminal-cover holds (the key is absent from failures)."""
    return {case: key not in failing_by_case.get(case, []) for case in cases}


def summarize(current: dict[str, bool], candidate: dict[str, bool], bound: set[str]) -> dict:
    """Pure comparison core (deterministic; unit-tested by ``--self-test``).

    Newly-failing = cases where current terminal-cover PASSES but candidate
    FAILS. Split into ``bound_regressions`` (hard) and ``advisory_deltas``
    (allowlist-eligible).
    """
    newly_failing = sorted(case for case in current if current.get(case) and not candidate.get(case, True))
    return {
        "current_pass": sorted(case for case, ok in current.items() if ok),
        "current_fail": sorted(case for case, ok in current.items() if not ok),
        "current_pass_count": sum(1 for ok in current.values() if ok),
        "candidate_pass_count": sum(1 for ok in candidate.values() if ok),
        "newly_failing": newly_failing,
        "bound_regressions": [case for case in newly_failing if case in bound],
        "advisory_deltas": [case for case in newly_failing if case not in bound],
    }


def run_terminal_cover(checker: Path, outputs: list[Path]) -> dict[str, list[str]]:
    """Live: run ``<checker> --json --outputs <paths>``; return case -> failing keys.

    The checker's exit code is intentionally not consulted; only its per-case
    ``--json`` condition report is read.
    """
    proc = subprocess.run(
        [sys.executable, str(checker), "--json", "--outputs", *[str(p) for p in outputs]],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return parse_graph_json(proc.stdout)


def render_report(
    current: dict[str, bool], candidate: dict[str, bool] | None, bound: set[str], candidate_label: str | None
) -> str:
    cases = sorted(current)
    header = "| case | class | current terminal-cover |"
    divider = "| --- | --- | --- |"
    if candidate is not None:
        header += " candidate |"
        divider += " --- |"
    out = [header, divider]
    for case in cases:
        cls = "BOUND" if case in bound else "ADVISORY"
        row = f"| {case} | {cls} | {'PASS' if current[case] else 'FAIL'} |"
        if candidate is not None:
            row += f" {'PASS' if candidate.get(case) else 'FAIL'} |"
        out.append(row)
    out.append("")
    bound_n = sum(1 for case in cases if case in bound)
    if candidate is None:
        passes = sum(1 for ok in current.values() if ok)
        out.append(
            f"baseline: {passes}/{len(cases)} cases pass terminal-cover; "
            f"{bound_n} BOUND, {len(cases) - bound_n} ADVISORY. "
            "No candidate supplied; delta is empty by construction."
        )
    else:
        summary = summarize(current, candidate, bound)
        out.append(f"candidate: {candidate_label}")
        out.append(
            f"newly-failing under candidate: {len(summary['newly_failing'])} "
            f"(BOUND regressions={len(summary['bound_regressions'])}, "
            f"ADVISORY deltas={len(summary['advisory_deltas'])})"
        )
        if summary["bound_regressions"]:
            out.append(
                "BOUND regressions (hard; would break check_retained_row_claims): "
                + ", ".join(summary["bound_regressions"])
            )
        if summary["advisory_deltas"]:
            out.append("ADVISORY deltas (allowlist-eligible): " + ", ".join(summary["advisory_deltas"]))
    return "\n".join(out)


def self_test() -> int:
    manifest = {
        "coverage_targets": [
            {"validator_binding": {"kind": "graph-keys", "keys": ["ALL"]}, "case_ids": ["a", "b"]},
            {"validator_binding": {"kind": "graph-keys", "keys": ["two_track_mrp_closure"]}, "case_ids": ["c"]},
            {"validator_binding": {"kind": "graph-keys", "keys": [TERMINAL_COVER_KEY]}, "case_ids": ["d"]},
            {"validator_binding": {"kind": "outputs-checker", "tool": "x"}, "case_ids": ["e"]},
        ]
    }
    bound = bound_case_ids(manifest)
    failing = {"a": [TERMINAL_COVER_KEY], "b": ["two_track_mrp_closure"]}
    state = terminal_cover_state(failing, ["a", "b", "d"])
    current = {"a": True, "b": True, "c": True, "d": True}
    candidate = {"a": True, "b": False, "c": False, "d": False}
    summary = summarize(current, candidate, {"a", "d"})
    sample_stdout = "graph-completeness check: FAIL\n[\n" + json.dumps(
        {"path": "tests/x/cases/case-z/output.md", "failures": [TERMINAL_COVER_KEY], "conditions": {}}
    ) + "\n]"
    checks = [
        ("bound = ALL-target + key-target cases", bound == {"a", "b", "d"}),
        ("terminal-cover FAILS when key present", state["a"] is False),
        ("terminal-cover PASSES when key absent", state["b"] is True and state["d"] is True),
        ("newly-failing = current-pass & candidate-fail", summary["newly_failing"] == ["b", "c", "d"]),
        ("bound regression isolates the bound case", summary["bound_regressions"] == ["d"]),
        ("advisory deltas isolate unbound cases", summary["advisory_deltas"] == ["b", "c"]),
        ("no delta when candidate == current", summarize(current, current, {"a", "d"})["newly_failing"] == []),
        ("parse_graph_json maps case -> failures", parse_graph_json(sample_stdout) == {"case-z": [TERMINAL_COVER_KEY]}),
    ]
    ok = all(passed for _, passed in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"terminal-cover-ab self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Terminal-cover A/B measurement (Plan 16, measurement only)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic logic self-test and exit")
    parser.add_argument(
        "--candidate",
        type=Path,
        default=None,
        help="path to a candidate strengthened terminal-cover checker (default: the current checker)",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    cases = case_ids()
    outputs = [case_output(case) for case in cases]
    manifest = load_json(MANIFEST)
    bound = bound_case_ids(manifest)

    current = terminal_cover_state(run_terminal_cover(CURRENT_CHECKER, outputs), cases)
    candidate: dict[str, bool] | None = None
    candidate_label: str | None = None
    if args.candidate is not None:
        candidate = terminal_cover_state(run_terminal_cover(args.candidate, outputs), cases)
        candidate_label = str(args.candidate)

    print(
        f"Terminal-cover A/B (measurement only; {len(cases)} retained cases; "
        f"condition={TERMINAL_COVER_KEY})"
    )
    print()
    print(render_report(current, candidate, bound, candidate_label))
    return 0


if __name__ == "__main__":
    sys.exit(main())
