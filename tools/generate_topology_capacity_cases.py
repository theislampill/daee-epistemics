#!/usr/bin/env python3
"""Emit deterministic, ephemeral A15 topology probe records."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Iterable

from topology_capacity_lib import (
    apply_mutation,
    build_stage_records,
    canonical_bytes,
    canonical_sha256,
    validate_spec,
)


STAGE_FILES = {
    "01": "stage-01-intake.json",
    "02": "stage-02-diagnostic-ir.json",
    "03": "stage-03-routing-owner-gate.json",
    "04": "stage-04-burden-execution-act.json",
    "05": "stage-05-mrp-reread-terminal-state.json",
    "06": "stage-06-field-witness.json",
    "07": "stage-07-public-projection.json",
    "08": "stage-08-verifier-sidecars.json",
}
SPEC_FILE = "topology-spec.json"
MANIFEST_FILE = "topology-dimensions.json"
STATE_FILE = "state-capsule.json"
WITNESS_FILE = "field-witness.json"
PROJECTION_FILE = "stage-projection.json"
PUBLIC_OUTPUT_FILE = "public-output.txt"


def load_spec(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return validate_spec(value)


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_bytes(value))


def generated_payload(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]], str | None]:
    manifest, stages = build_stage_records(spec)
    manifest["source_spec_sha256"] = canonical_sha256(spec)
    failed_stage = apply_mutation(spec, manifest, stages)
    return manifest, stages, failed_stage


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _public_segments(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "ordinal": index,
            "obligation_id": row["obligation_id"],
            "body_ref": row["body_ref"],
            "semantic_payload": row["semantic_payload"],
        }
        for index, row in enumerate(operations, 1)
    ]


def _public_output_bytes(stage07: dict[str, Any]) -> bytes:
    return canonical_bytes(
        {
            "schema": "daee-topology-public-output-v1",
            "segments": stage07["segments"],
            "operations": stage07["operations"],
            "projection": stage07["projection"],
            "T_lang": stage07["T_lang"],
            "non_claim": "structural projection is not semantic truth or guaranteed uptake",
        }
    )


def _write_sidecars(output_dir: Path, stages: dict[str, dict[str, Any]]) -> None:
    lifecycle = stages["05"]["lifecycle"]
    stages["07"]["segments"] = _public_segments(stages["07"]["operations"])
    _write_json(
        output_dir / STATE_FILE,
        {
            "schema": "daee-topology-state-capsule-v1",
            "B_LA": [row["burden_id"] for row in lifecycle if row["origin"] == "B_LA"],
            "B_MRP": [row["burden_id"] for row in lifecycle if row["origin"] == "B_MRP"],
            "burden_cycle_ids": [row["cycle_id"] for row in lifecycle],
            "terminal_states": {row["burden_id"]: row["terminal_state"] for row in lifecycle},
            "remaining_live_ids": stages["05"]["closure_snapshots"][-1]["remaining_live_ids"],
        },
    )
    _write_json(
        output_dir / WITNESS_FILE,
        {
            "schema": "daee-topology-field-witness-v1",
            "projection": stages["06"]["projection"],
            "nar_rows": stages["06"]["nar_rows"],
            "burden_cycles": stages["05"]["burden_cycles"],
            "non_claims": ["structural parity is not semantic truth"],
        },
    )
    _write_json(
        output_dir / PROJECTION_FILE,
        {
            "schema": "daee-topology-stage-projection-v1",
            "stage06": stages["06"]["projection"],
            "stage07": stages["07"]["projection"],
            "equal": stages["06"]["projection"] == stages["07"]["projection"],
        },
    )
    public_bytes = _public_output_bytes(stages["07"])
    (output_dir / PUBLIC_OUTPUT_FILE).write_bytes(public_bytes)
    stages["07"]["public_output_sha256"] = hashlib.sha256(public_bytes).hexdigest()
    _write_json(output_dir / STAGE_FILES["07"], stages["07"])


def refresh_case_bindings(output_dir: Path) -> None:
    """Rebuild derived sidecars and Stage08 bindings after a controlled transform."""
    stages = {
        number: json.loads((output_dir / STAGE_FILES[number]).read_text(encoding="utf-8"))
        for number in ("01", "02", "03", "04", "05", "06", "07")
    }
    _write_sidecars(output_dir, stages)
    required = [
        SPEC_FILE,
        MANIFEST_FILE,
        *(STAGE_FILES[number] for number in ("01", "02", "03", "04", "05", "06", "07")),
        STATE_FILE,
        WITNESS_FILE,
        PROJECTION_FILE,
        PUBLIC_OUTPUT_FILE,
    ]
    bindings = {name: _file_sha256(output_dir / name) for name in required}
    spec = json.loads((output_dir / SPEC_FILE).read_text(encoding="utf-8"))
    _write_json(
        output_dir / STAGE_FILES["08"],
        {
            "schema": "daee-topology-stage-08-v1",
            "artifact_sha256": bindings,
            "source_spec_sha256": canonical_sha256(spec),
            "structural_only": True,
        },
    )


def sabotage_case(output_dir: Path, sabotage: str) -> None:
    """Apply one deterministic test sabotage without refreshing custody."""
    if sabotage == "missing-stage04-cycle":
        path = output_dir / STAGE_FILES["04"]
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["burden_cycles"] = payload["burden_cycles"][1:]
        _write_json(path, payload)
        return
    if sabotage == "out-of-order-cycle":
        path = output_dir / STAGE_FILES["05"]
        payload = json.loads(path.read_text(encoding="utf-8"))
        generated = [row for row in payload["burden_cycles"] if row["origin"] == "B_MRP"]
        baseline = [row for row in payload["burden_cycles"] if row["origin"] == "B_LA"]
        payload["burden_cycles"] = list(reversed(generated)) + baseline
        _write_json(path, payload)
        return
    if sabotage == "nonincrementing-depth":
        path = output_dir / STAGE_FILES["05"]
        payload = json.loads(path.read_text(encoding="utf-8"))
        generated = [row for row in payload["burden_cycles"] if row["origin"] == "B_MRP"]
        if len(generated) > 1:
            generated[1]["generation_depth"] = generated[0]["generation_depth"]
            for row in payload["lifecycle"]:
                if row["burden_id"] == generated[1]["burden_id"]:
                    row["generation_depth"] = generated[0]["generation_depth"]
        _write_json(path, payload)
        return
    raise ValueError(f"unknown sabotage {sabotage}")


def generate_case(spec_path: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"output directory must be absent: {output_dir}")
    supplied_spec = load_spec(spec_path)
    spec = {key: value for key, value in supplied_spec.items() if key != "taint"}
    manifest, stages, failed_stage = generated_payload(spec)
    output_dir.mkdir(parents=True)
    _write_json(output_dir / SPEC_FILE, spec)
    _write_json(output_dir / MANIFEST_FILE, manifest)
    for stage in sorted(stages):
        if failed_stage is not None and int(stage) > int(failed_stage):
            continue
        _write_json(output_dir / STAGE_FILES[stage], stages[stage])
    if failed_stage is None:
        refresh_case_bindings(output_dir)
    return {
        "status": "generated-invalid" if failed_stage else "generated-valid",
        "failed_stage": failed_stage,
        "output_dir": str(output_dir),
        "dimension_manifest_sha256": canonical_sha256(manifest),
        "files": sorted(path.name for path in output_dir.iterdir()),
    }


def directory_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(file for file in path.rglob("*") if file.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def check_only(spec_path: Path) -> dict[str, Any]:
    supplied_spec = load_spec(spec_path)
    spec = {key: value for key, value in supplied_spec.items() if key != "taint"}
    manifest, _stages, failed_stage = generated_payload(spec)
    return {
        "status": "valid-spec",
        "mutation_stage": failed_stage,
        "dimension_manifest_sha256": canonical_sha256(manifest),
        "counts": {
            "observations": len(manifest["source_observation_ids"]),
            "burdens": len(manifest["baseline_burden_ids"]) + len(manifest["generated_burden_ids"]),
            "obligations": len(manifest["obligation_ids"]),
        },
    }


def self_test() -> dict[str, Any]:
    sample = {
        "schema": "daee-topology-capacity-spec-v1",
        "seed": 1,
        "dimensions": {
            "input_observations": 2,
            "input_pressures": 2,
            "candidate_states": 2,
            "candidate_hyperedges": 1,
            "baseline_burdens": 2,
            "submoves_per_burden": 1,
            "held_baseline_burdens": 0,
            "generated_burdens": 1,
            "generation_depth": 1,
            "preempted_candidates": 1,
            "route_candidate_kinds": ["direct", "synthetic-unclassified-x"],
        },
        "dependency_shape": "generated-chain",
        "closure_policy": "complete-when-no-live-obligations",
    }
    validate_spec(sample)
    with tempfile.TemporaryDirectory(prefix="daee-topology-generator-") as parent:
        parent_path = Path(parent)
        spec_path = parent_path / "spec.json"
        _write_json(spec_path, sample)
        first, second = parent_path / "a", parent_path / "b"
        generate_case(spec_path, first)
        generate_case(spec_path, second)
        if directory_digest(first) != directory_digest(second):
            raise AssertionError("same seed/spec was not byte deterministic")
    return {"checker_id": "topology-capacity-generator", "status": "PASS"}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.self_test:
            result = self_test()
        elif args.spec and args.check_only:
            result = check_only(args.spec)
        elif args.spec and args.output_dir:
            result = generate_case(args.spec, args.output_dir)
        else:
            parser.error("use --self-test, --spec ... --check-only, or --spec ... --output-dir ABSENT")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, AssertionError, json.JSONDecodeError) as exc:
        print(json.dumps({"checker_id": "topology-capacity-generator", "status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
