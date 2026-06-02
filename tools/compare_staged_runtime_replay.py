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
STAGE_ORDER = [
    "stage-01-intake",
    "stage-02-layer-a-diagnostic-ir",
    "stage-03-routing-owner-gate",
    "stage-04-burden-execution-act",
    "stage-05-mrp-reread-terminal-state",
    "stage-06-field-witness-nar",
    "stage-07-release-output",
    "stage-08-verifier-sidecars",
]
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
        "owner_activations",
        "owner_activation_details",
        "normalized_activation_record",
        "normalized_activation_record_details",
        "register_deltas",
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


def comparable_field(stage_id: str, field: str, value: Any) -> Any:
    if stage_id == "stage-03-routing-owner-gate" and field == "owner_routes":
        if not isinstance(value, list):
            return comparable(value)
        route_ids: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                return comparable(value)
            route_ids.append(
                {
                    "burden_id": item.get("burden_id"),
                    "owner_id": item.get("owner_id"),
                }
            )
        return comparable(route_ids)
    if stage_id == "stage-06-field-witness-nar" and field == "owner_activations":
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return sorted(value)
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            return sorted(item.get("body_ref") for item in value)
        return comparable(value)
    if stage_id == "stage-06-field-witness-nar" and field == "owner_activation_details":
        if value is None:
            return None
        if not isinstance(value, list):
            return comparable(value)
        rows: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                return comparable(value)
            burden_id = item.get("burden_id") or item.get("target") or item.get("source")
            owner_id = item.get("owner_id") or item.get("owner")
            terminal_state = item.get("terminal_state")
            if terminal_state is None and isinstance(item.get("land"), str) and item["land"].startswith("Land("):
                terminal_state = "landed"
            rows.append(
                {
                    "body_ref": item.get("body_ref"),
                    "burden_id": burden_id,
                    "owner_id": owner_id,
                    "operation": item.get("operation"),
                    "terminal_state": terminal_state,
                }
            )
        return comparable(rows)
    if stage_id == "stage-06-field-witness-nar" and field == "normalized_activation_record":
        if value is True or isinstance(value, dict):
            return True
        return comparable(value)
    if stage_id == "stage-06-field-witness-nar" and field == "normalized_activation_record_details":
        if value is None:
            return None
        if not isinstance(value, dict):
            return comparable(value)
        result: dict[str, Any] = {
            "n_frame": value.get("n_frame"),
            "live_registers": comparable(value.get("live_registers")),
            "burden_floor": comparable(value.get("burden_floor")),
        }
        rows = value.get("per_burden")
        if isinstance(rows, list):
            result["per_burden"] = comparable(
                [
                    {
                        "burden_id": row.get("burden_id"),
                        "owner_id": row.get("owner_id"),
                        "operation": row.get("operation"),
                        "terminal_state": row.get("terminal_state"),
                        "generation_depth": row.get("generation_depth"),
                    }
                    for row in rows
                    if isinstance(row, dict)
                ]
            )
        else:
            result["per_burden"] = comparable(rows)
        return result
    return comparable(value)


def stage_field_value(stage_id: str, field: str, stage: dict[str, Any]) -> Any:
    value = stage.get(field)
    if (
        stage_id == "stage-06-field-witness-nar"
        and field == "normalized_activation_record_details"
        and value is None
        and isinstance(stage.get("normalized_activation_record"), dict)
    ):
        return stage["normalized_activation_record"]
    return value


def comparable_no_new_resultant(value: Any) -> Any:
    if value is True:
        return {"proved": True, "unresolved_burdens": []}
    if isinstance(value, dict):
        return {
            "proved": bool(value.get("proved")),
            "unresolved_burdens": comparable(value.get("unresolved_burdens") or []),
        }
    return comparable(value)


def is_empty_register_deltas(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, dict):
        return not value
    if isinstance(value, list):
        return not value
    return False


def field_matches(stage_id: str, field: str, record_stage: dict[str, Any], replay_stage: dict[str, Any]) -> bool:
    record_raw = stage_field_value(stage_id, field, record_stage)
    replay_raw = stage_field_value(stage_id, field, replay_stage)
    if stage_id == "stage-05-mrp-reread-terminal-state" and field == "no_new_resultant_proof":
        return comparable_no_new_resultant(record_raw) == comparable_no_new_resultant(replay_raw)
    if stage_id == "stage-06-field-witness-nar" and field == "register_deltas":
        # Historical retained replay targets can lack register-delta evidence while
        # a fresh Stage 06 retry emits parser-stable deltas. This is directional:
        # a richer replay target still requires the candidate to match it.
        if is_empty_register_deltas(replay_raw) and not is_empty_register_deltas(record_raw):
            return True
    return comparable_field(stage_id, field, record_raw) == comparable_field(stage_id, field, replay_raw)


def scoped_stage_ids(through_stage: str | None) -> list[str] | None:
    if through_stage is None:
        return None
    return STAGE_ORDER[: STAGE_ORDER.index(through_stage) + 1]


def compare_records(record: dict[str, Any], replay: dict[str, Any], *, through_stage: str | None = None) -> list[str]:
    mismatches: list[str] = []
    record_stages = stage_map(record)
    replay_stages = stage_map(replay)
    record_order = [stage.get("id") for stage in record.get("stages", []) if isinstance(stage, dict)]
    replay_order = [stage.get("id") for stage in replay.get("stages", []) if isinstance(stage, dict)]
    stage_ids = scoped_stage_ids(through_stage)
    if stage_ids is not None:
        record_order = [stage_id for stage_id in record_order if stage_id in stage_ids]
        replay_order = [stage_id for stage_id in replay_order if stage_id in stage_ids]
    if record_order != replay_order:
        mismatches.append(f"stage order differs: record={record_order}; replay={replay_order}")
    ordered_stage_ids = stage_ids or list(replay_stages)
    for stage_id in ordered_stage_ids:
        replay_stage = replay_stages.get(stage_id)
        if replay_stage is None:
            continue
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
            record_value = comparable_field(stage_id, field, stage_field_value(stage_id, field, record_stage))
            replay_value = comparable_field(stage_id, field, stage_field_value(stage_id, field, replay_stage))
            if not field_matches(stage_id, field, record_stage, replay_stage):
                mismatches.append(
                    f"{stage_id}.{field}: record={record_value!r}; "
                    f"replay={replay_value!r}"
                )
    return mismatches


def write_report(
    path: Path,
    *,
    record_path: Path,
    replay_path: Path,
    mismatches: list[str],
    through_stage: str | None,
) -> None:
    lines = [
        "# Staged Runtime Replay Comparison",
        "",
        f"- Record: `{rel(record_path)}`",
        f"- Replay target: `{rel(replay_path)}`",
        f"- Through stage: `{through_stage or 'full'}`",
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
    richer_owner_routes = copy.deepcopy(replay)
    for route in stage_map(richer_owner_routes)["stage-03-routing-owner-gate"]["owner_routes"]:
        route["operation"] = "richer-metadata"
        route["pressure"] = "diagnostic-detail"
    if compare_records(richer_owner_routes, replay):
        print("compare staged runtime replay self-test: FAIL")
        print("- richer owner-route metadata should compare by route identity")
        return 1
    wrong_owner = copy.deepcopy(replay)
    stage_map(wrong_owner)["stage-03-routing-owner-gate"]["owner_routes"][0]["owner_id"] = "wrong-owner"
    if not any("stage-03-routing-owner-gate.owner_routes" in item for item in compare_records(wrong_owner, replay)):
        print("compare staged runtime replay self-test: FAIL")
        print("- owner-route identity mismatch was not detected")
        return 1
    prefix = copy.deepcopy(replay)
    stage_prefix = scoped_stage_ids("stage-04-burden-execution-act")
    assert stage_prefix is not None
    prefix["stage_order"] = stage_prefix
    prefix["stages"] = [
        stage
        for stage in prefix.get("stages", [])
        if isinstance(stage, dict) and stage.get("id") in stage_prefix
    ]
    if compare_records(prefix, replay, through_stage="stage-04-burden-execution-act"):
        print("compare staged runtime replay self-test: FAIL")
        print("- Stage 04 prefix replay comparison produced mismatches")
        return 1
    if not compare_records(prefix, replay):
        print("compare staged runtime replay self-test: FAIL")
        print("- unscoped Stage 04 prefix record should not compare as a full replay")
        return 1
    stage05_prefix = copy.deepcopy(replay)
    stage05_ids = scoped_stage_ids("stage-05-mrp-reread-terminal-state")
    assert stage05_ids is not None
    stage05_prefix["stage_order"] = stage05_ids
    stage05_prefix["stages"] = [
        stage
        for stage in stage05_prefix.get("stages", [])
        if isinstance(stage, dict) and stage.get("id") in stage05_ids
    ]
    if compare_records(stage05_prefix, replay, through_stage="stage-05-mrp-reread-terminal-state"):
        print("compare staged runtime replay self-test: FAIL")
        print("- Stage 05 prefix replay comparison produced mismatches")
        return 1
    stage05_structured_proof = copy.deepcopy(stage05_prefix)
    stage_map(stage05_structured_proof)["stage-05-mrp-reread-terminal-state"]["no_new_resultant_proof"] = {
        "proved": True,
        "basis": "equivalent structured proof text",
        "unresolved_burdens": [],
    }
    if compare_records(stage05_structured_proof, replay, through_stage="stage-05-mrp-reread-terminal-state"):
        print("compare staged runtime replay self-test: FAIL")
        print("- Stage 05 structured no_new_resultant proof should compare to legacy true")
        return 1
    stage05_mismatch = copy.deepcopy(stage05_prefix)
    stage_map(stage05_mismatch)["stage-05-mrp-reread-terminal-state"]["terminal_states"] = {"B1": "held"}
    if not any(
        "stage-05-mrp-reread-terminal-state.terminal_states" in item
        for item in compare_records(stage05_mismatch, replay, through_stage="stage-05-mrp-reread-terminal-state")
    ):
        print("compare staged runtime replay self-test: FAIL")
        print("- Stage 05 terminal-state mismatch was not detected")
        return 1
    stage06_prefix = copy.deepcopy(replay)
    stage06_ids = scoped_stage_ids("stage-06-field-witness-nar")
    assert stage06_ids is not None
    stage06_prefix["stage_order"] = stage06_ids
    stage06_prefix["stages"] = [
        stage
        for stage in stage06_prefix.get("stages", [])
        if isinstance(stage, dict) and stage.get("id") in stage06_ids
    ]
    if compare_records(stage06_prefix, replay, through_stage="stage-06-field-witness-nar"):
        print("compare staged runtime replay self-test: FAIL")
        print("- Stage 06 prefix replay comparison produced mismatches")
        return 1
    stage06_live_shape = copy.deepcopy(stage06_prefix)
    stage06_stage = stage_map(stage06_live_shape)["stage-06-field-witness-nar"]
    nar_details = stage06_stage.pop("normalized_activation_record_details")
    stage06_stage["normalized_activation_record"] = nar_details
    stage06_stage["owner_activation_details"] = [
        {
            "source": "B1",
            "target": "B1",
            "owner": "source-status-repair",
            "operation": "source-order",
            "body_ref": "¹B₁",
            "land": "Land(¹B)+",
        },
        {
            "source": "B1",
            "target": "B1",
            "owner": "M1",
            "operation": "self-grounding-test",
            "body_ref": "¹B₂",
            "land": "Land(¹B)+",
        },
    ]
    stage06_stage["register_deltas"] = [
        {"register": "xi", "delta": "science-source-bounded", "burden_id": "B1", "body_ref": "¹B₁"}
    ]
    if compare_records(stage06_live_shape, replay, through_stage="stage-06-field-witness-nar"):
        print("compare staged runtime replay self-test: FAIL")
        print("- Stage 06 live-model shape should compare to retained replay target")
        return 1
    stage06_richer_replay = copy.deepcopy(replay)
    stage06_candidate_missing_delta = copy.deepcopy(stage06_prefix)
    replay_stage06 = stage_map(stage06_richer_replay)["stage-06-field-witness-nar"]
    replay_stage06["register_deltas"] = [
        {"register": "xi", "delta": "science-source-bounded", "burden_id": "B1", "body_ref": "¹B₁"}
    ]
    candidate_stage06 = stage_map(stage06_candidate_missing_delta)["stage-06-field-witness-nar"]
    candidate_stage06["register_deltas"] = {}
    if not any(
        "stage-06-field-witness-nar.register_deltas" in item
        for item in compare_records(
            stage06_candidate_missing_delta,
            stage06_richer_replay,
            through_stage="stage-06-field-witness-nar",
        )
    ):
        print("compare staged runtime replay self-test: FAIL")
        print("- richer replay register_delta target should require candidate matching")
        return 1
    stage06_mismatch = copy.deepcopy(stage06_prefix)
    stage_map(stage06_mismatch)["stage-06-field-witness-nar"]["field_witness_body_refs"] = ["wrong"]
    if not any(
        "stage-06-field-witness-nar.field_witness_body_refs" in item
        for item in compare_records(stage06_mismatch, replay, through_stage="stage-06-field-witness-nar")
    ):
        print("compare staged runtime replay self-test: FAIL")
        print("- Stage 06 field_witness_body_refs mismatch was not detected")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "comparison.md"
        write_report(
            report,
            record_path=DEFAULT_REPLAY_RECORD,
            replay_path=DEFAULT_REPLAY_RECORD,
            mismatches=[],
            through_stage=None,
        )
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
    parser.add_argument("--through-stage", choices=STAGE_ORDER)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    if args.record is None:
        parser.error("--record is required unless --self-test is used")
    record = load_json(args.record)
    replay = load_json(args.replay_record)
    mismatches = compare_records(record, replay, through_stage=args.through_stage)
    if args.out:
        write_report(
            args.out,
            record_path=args.record,
            replay_path=args.replay_record,
            mismatches=mismatches,
            through_stage=args.through_stage,
        )
    if mismatches:
        print("staged runtime replay comparison: MISMATCH")
        for mismatch in mismatches:
            print(f"- {mismatch}")
        return 1
    print("staged runtime replay comparison: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
