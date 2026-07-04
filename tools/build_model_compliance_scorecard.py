#!/usr/bin/env python3
"""Offline model-compliance scorecard runner — Plan 15 (Lane F).

Given a directory of ALREADY-CAPTURED governed outputs (.md), runs each through
the existing deterministic structural detectors and emits a
`model-compliance-scorecard-v1` (see docs/model-compliance-scorecard.md).

Strictly OFFLINE: it shells only to local `tools/check_*.py` detectors. It makes
NO model call, network request, or spend, and carries no safety/refusal framing.
A PASS row means the wired detector accepted the captured output — structural
conformance only, not semantic truth, uptake, or cross-host behavior.

Two of the eight mapped failure shapes are marked NOT-RUN by construction: their
detectors operate on JSON handshake records / retained manifests, not on a
captured `.md` output, so they are not runnable from an output file alone.

Usage:
  python tools/build_model_compliance_scorecard.py --outputs-dir <dir> [--out sc.json] [--markdown-out sc.md]
  python tools/build_model_compliance_scorecard.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "model-compliance-scorecard-v1"

# (failure_shape, detector tool, runnable-over-a-captured-.md?)
DETECTORS: list[tuple[str, str, bool]] = [
    ("burden-loss", "check_mrp_generated_burden", True),
    ("mrp-skip", "check_mrp_route_invariants", True),
    ("premature-closure", "check_mid_reread_pressure", True),
    ("symbol-theater", "check_act_surface_syntax", True),
    ("fabricated-verdict", "check_manual_smoke_render_contract", True),
    ("uptake-claim", "check_tlang_response_closure", True),
    # detectors below operate on JSON handshake records / retained manifests, not a .md output:
    ("parser-unstable-stage05", "check_staged_runtime_handshake", False),
    ("sidecar-reliance", "check_retained_proof_corpus", False),
]


def _detector_accepts(detector: str, output_path: Path) -> bool:
    """Run one --outputs-capable detector over one output; True == accepted (exit 0)."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / f"{detector}.py"), "--outputs", str(output_path)],
        capture_output=True,
    )
    return proc.returncode == 0


def build_scorecard(outputs: list[Path], host: str = "reference") -> dict:
    """Aggregate over the output set: PASS iff every output is accepted; FAIL iff any is rejected."""
    rows = []
    for shape, detector, runnable in DETECTORS:
        if not runnable or not outputs:
            verdict = "NOT-RUN"
        else:
            verdict = "PASS" if all(_detector_accepts(detector, o) for o in outputs) else "FAIL"
        rows.append({"failure_shape": shape, "detector": f"{detector}.py", "mode": "structural", "verdict": verdict})
    return {
        "schema": SCHEMA,
        "capture_meta": {"host": host, "captured_from": "fixtures", "output_count": len(outputs)},
        "rows": rows,
        "non_claims": [
            "structural-conformance only; not a semantic-truth, uptake, or cross-host verdict",
            "a PASS row means the wired detector accepted the captured output, nothing more",
        ],
    }


def validate_scorecard(sc: dict) -> list[str]:
    """Pure validator (unit-tested): a scorecard missing non_claims (or malformed) is rejected."""
    errors = []
    if sc.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA!r}")
    if not sc.get("non_claims"):
        errors.append("scorecard must carry a non-empty non_claims block")
    for row in sc.get("rows", []):
        if row.get("verdict") not in {"PASS", "FAIL", "NOT-RUN"}:
            errors.append(f"row {row.get('failure_shape')!r} has invalid verdict {row.get('verdict')!r}")
    return errors


def to_markdown(sc: dict) -> str:
    lines = [f"# Model-compliance scorecard ({sc['capture_meta']['host']})", "",
             "| failure_shape | detector | mode | verdict |", "| --- | --- | --- | --- |"]
    for r in sc["rows"]:
        lines.append(f"| {r['failure_shape']} | {r['detector']} | {r['mode']} | {r['verdict']} |")
    lines += ["", "non_claims:"] + [f"- {n}" for n in sc["non_claims"]]
    return "\n".join(lines) + "\n"


def self_test() -> int:
    seed = ROOT / "tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/cases/a9-science-source/output.md"
    checks = []
    # no network/model in the detector map (only local check_* tools)
    checks.append(("detectors are local check_* only",
                   all(d.startswith("check_") for _, d, _ in DETECTORS)))
    # validator rejects a scorecard without non_claims
    checks.append(("validator rejects missing non_claims",
                   any("non_claims" in e for e in validate_scorecard({"schema": SCHEMA, "rows": []}))))
    if seed.is_file():
        sc = build_scorecard([seed])
        checks.append(("scorecard validates", validate_scorecard(sc) == []))
        checks.append(("8 rows", len(sc["rows"]) == 8))
        checks.append(("2 NOT-RUN (non-.md detectors)",
                       sum(1 for r in sc["rows"] if r["verdict"] == "NOT-RUN") == 2))
        checks.append(("6 runnable shapes not NOT-RUN",
                       sum(1 for r in sc["rows"] if r["verdict"] in {"PASS", "FAIL"}) == 6))
    else:
        checks.append(("seed output present", False))
    ok = all(p for _, p in checks)
    for name, p in checks:
        print(f"  self-test {'PASS' if p else 'FAIL'}: {name}")
    print(f"model-compliance-scorecard self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline model-compliance scorecard runner (Plan 15)")
    parser.add_argument("--outputs-dir", type=Path, help="directory of captured governed outputs (*.md)")
    parser.add_argument("--host", default="reference", help="capture host label")
    parser.add_argument("--out", type=Path, help="write scorecard JSON here")
    parser.add_argument("--markdown-out", type=Path, help="write scorecard Markdown here")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic self-test")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.outputs_dir:
        print("usage: build_model_compliance_scorecard.py --outputs-dir <dir> | --self-test")
        return 2
    outputs = [Path(p) for p in sorted(glob.glob(str(args.outputs_dir / "**" / "*.md"), recursive=True))]
    sc = build_scorecard(outputs, host=args.host)
    errors = validate_scorecard(sc)
    if errors:
        for e in errors:
            print(f"scorecard invalid: {e}", file=sys.stderr)
        return 1
    if args.out:
        args.out.write_text(json.dumps(sc, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.write_text(to_markdown(sc), encoding="utf-8")
    print(json.dumps(sc, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
