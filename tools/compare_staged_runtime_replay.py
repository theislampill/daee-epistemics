#!/usr/bin/env python3
"""Compare a staged current-skill record to a retained replay target shape.

This comparator is diagnostic only. It does not prove model behavior or mutate
retained proof-corpus artifacts.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPLAY_RECORD = (
    ROOT / "tests" / "staged-runtime-handshake" / "valid" / "retained-a9-science-source.json"
)
FIELDS_BY_STAGE = {
    "stage-02-layer-a-diagnostic-ir": ["burden_floor", "selected_n_frame", "live_registers"],
    "stage-03-routing-owner-gate": ["route_targets", "owner_routes"],
    "stage-04-burden-execution-act": ["act_targets", "act_body_refs", "act_rows"],
    "stage-05-mrp-reread-terminal-state": [
        "terminal_states",
        "dependency_graph_edges",
        "no_new_resultant_proof",
    ],
    "stage-06-field-witness-nar": [
        "field_witness_body_refs",
        "nar_burdens",
        "normalized_activation_record",
    ],
    "stage-08-verifier-sidecars": ["verifier_sidecars"],
}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stage_map(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stages = record.get("stages")
    if not isinstance(stages, list):
        return {}
    return {
        stage["id"]: stage
        for stage in stages
        if isinstance(stage, dict) and isinstance(stage.get("id"), str)
    }


def comparable(value: Any) -> Any:
    if isinstance(value, list):
        if all(isinstance(item, str) for item in value):
            return sorted(value)
        return value
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, nested in sorted(value.items()):
            if key in {"path", "sha256"}:
                continue
            normalized[key] = comparable(nested)
        return normalized
    return value


def compare_records(record: dict[str, Any], replay: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    record_stages = stage_map(record)
    replay_stages = stage_map(replay)
    record_order = [stage.get("id") for stage in record.get("stages", []) if isinstance(stage, dict)]
    replay_order = [stage.get("id") for stage in replay.get("stages", []) if isinstance(stage, dict)]
    if record_order != replay_order:
        mismatches.append(f"stage order differs: record={record_order}; replay={replay_order}")
    for stage_id, replay_stage in replay_stages.items():
        record_stage = record_stages.get(stage_id)
        if record_stage is None:
            mismatches.append(f"{stage_id}: missing from record")
            continue
        if record_stage.get("status") != replay_stage.get("status"):
            mismatches.append(
                f"{stage_id}: status differs: record={record_stage.get('status')!r}; "
                f"replay={replay_stage.get('status')!r}"
            )
        for field in FIELDS_BY_STAGE.get(stage_id, []):
            if comparable(record_stage.get(field)) != comparable(replay_stage.get(field)):
                mismatches.append(
                    f"{stage_id}.{field}: record={comparable(record_stage.get(field))!r}; "
                    f"replay={comparable(replay_stage.get(field))!r}"
                )
    return mismatches


def write_report(path: Path, *, record_path: Path, replay_path: Path, mismatches: list[str]) -> None:
    lines = [
        "# Staged Runtime Replay Comparison",
        "",
        f"- Record: `{rel(record_path)}`",
        f"- Replay target: `{rel(replay_path)}`",
        f"- Mismatches: `{len(mismatches)}`",
        "",
    ]
    if mismatches:
        lines.append("## Mismatches")
        lines.extend(f"- {item}" for item in mismatches)
    else:
        lines.append("Replay comparison: PASS")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def run_self_test() -> int:
    replay = load_json(DEFAULT_REPLAY_RECORD)
    if compare_records(replay, replay):
        print("compare staged runtime replay self-test: FAIL")
        print("- identical replay record produced mismatches")
        return 1
    modified = copy.deepcopy(replay)
    stage = stage_map(modified)["stage-03-routing-owner-gate"]
    stage["route_targets"] = ["B999"]
    mismatches = compare_records(modified, replay)
    if not any("stage-03-routing-owner-gate.route_targets" in item for item in mismatches):
        print("compare staged runtime replay self-test: FAIL")
        print("- modified route target was not detected")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "comparison.md"
        write_report(report, record_path=DEFAULT_REPLAY_RECORD, replay_path=DEFAULT_REPLAY_RECORD, mismatches=[])
        if "Replay comparison: PASS" not in report.read_text(encoding="utf-8"):
            print("compare staged runtime replay self-test: FAIL")
            print("- report did not contain PASS marker")
            return 1
    print("compare staged runtime replay self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--replay-record", type=Path, default=DEFAULT_REPLAY_RECORD)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    if args.record is None:
        parser.error("--record is required unless --self-test is used")
    record = load_json(args.record)
    replay = load_json(args.replay_record)
    mismatches = compare_records(record, replay)
    if args.out:
        write_report(args.out, record_path=args.record, replay_path=args.replay_record, mismatches=mismatches)
    if mismatches:
        print("staged runtime replay comparison: MISMATCH")
        for mismatch in mismatches:
            print(f"- {mismatch}")
        return 1
    print("staged runtime replay comparison: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
