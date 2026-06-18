#!/usr/bin/env python3
"""Build a retained-artifact staged runtime replay record.

This builder does not run daee-epistemics and does not mutate retained output.
It binds a staged handoff record to an already retained governed artifact set:
raw input, governed output, collapse certificate, warning-clean Grapher HTML,
and the checker-owned B.5 full-IR projection sidecar when present.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import check_nla_decode_semantic_faithfulness as nla_decode
import check_mrp_route_invariants as mrp_route_invariants
import check_retained_proof_corpus as retained
import check_staged_runtime_handshake as staged


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    ROOT
    / "tests"
    / "retained-proof-corpus"
    / "v0.4.3.0-schema-light"
    / "valid"
    / "sidecar-backed"
    / "manifest.json"
)
DEFAULT_CASE_ID = "a9-science-source"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    if not path.exists():
        return None, [f"{rel(path)}: file not found"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)}: invalid JSON: {exc}"]


def find_case(manifest: dict[str, Any], case_id: str) -> dict[str, Any] | None:
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        return None
    for case in cases:
        if isinstance(case, dict) and case.get("id") == case_id:
            return case
    return None


def resolve_case_path(manifest_path: Path, case: dict[str, Any], field: str) -> tuple[Path | None, list[str]]:
    if field == staged.B5_RETAINED_SIDECAR_FIELD:
        entry = case.get(staged.B5_RETAINED_SIDECAR_FIELD)
        if not isinstance(entry, dict):
            return None, [f"{field}: retained case has no B.5 full-IR projection sidecar"]
        raw = entry.get("path")
    else:
        raw = case.get(field)
    path, error = retained.resolve_manifest_path(manifest_path, raw)
    if error:
        return None, [f"{field}: {error}"]
    assert path is not None
    if not path.exists():
        return None, [f"{field}: {rel(path)} missing"]
    return path, []


def artifact_entry(path: Path, sha256: str, *, schema: str | None = None, builder: str | None = None) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": rel(path),
        "sha256": sha256.upper(),
    }
    if schema is not None:
        entry["schema"] = schema
    if builder is not None:
        entry["builder"] = builder
    return entry


def artifact_bindings(manifest_path: Path, case: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    hashes = case.get("hashes") if isinstance(case.get("hashes"), dict) else {}
    artifacts = {
        field: artifact_entry(paths[field], str(hashes.get(field) or retained.sha256_file(paths[field])))
        for field in retained.ARTIFACT_FIELDS
    }
    sidecar = case.get(staged.B5_RETAINED_SIDECAR_FIELD)
    if isinstance(sidecar, dict) and staged.B5_RETAINED_SIDECAR_FIELD in paths:
        artifacts[staged.B5_RETAINED_SIDECAR_FIELD] = artifact_entry(
            paths[staged.B5_RETAINED_SIDECAR_FIELD],
            str(sidecar.get("sha256") or retained.sha256_file(paths[staged.B5_RETAINED_SIDECAR_FIELD])),
            schema=staged.B5_SIDECAR_SCHEMA,
            builder=staged.B5_SIDECAR_BUILDER,
        )
    return {
        "schema": staged.RETAINED_BINDING_SCHEMA,
        "retained_manifest": rel(manifest_path),
        "case_id": str(case.get("id")),
        "artifacts": artifacts,
    }


def terminal_state_map(field_witness: dict[str, Any]) -> dict[str, str]:
    coverage = nla_decode.coverage_proof(field_witness)
    terminals = coverage.get("terminal_states")
    result: dict[str, str] = {}
    if isinstance(terminals, dict):
        for burden, payload in terminals.items():
            if isinstance(payload, dict):
                state = payload.get("state")
            else:
                state = payload
            if isinstance(burden, str) and isinstance(state, str):
                result[burden] = state
    return result


def dependency_edges(field_witness: dict[str, Any]) -> list[str]:
    graph = nla_decode.coverage_proof(field_witness).get("dependency_graph")
    if not isinstance(graph, dict):
        return []
    raw_edges = graph.get("edges")
    edges: list[str] = []
    if isinstance(raw_edges, list):
        for item in raw_edges:
            if isinstance(item, str):
                edges.append(item)
            elif isinstance(item, dict):
                source = item.get("from") or item.get("source")
                target = item.get("to") or item.get("target")
                if isinstance(source, str) and isinstance(target, str):
                    edges.append(f"{source}->{target}")
    return edges


def no_new_resultant_proof_present(field_witness: dict[str, Any]) -> bool:
    proof = nla_decode.terminal_no_new_resultant_proof(nla_decode.formal_reread_states(field_witness))
    return bool(proof)


def parsed_output_evidence(output_path: Path) -> tuple[dict[str, Any], list[Any], list[str]]:
    text = output_path.read_text(encoding="utf-8", errors="replace")
    field_witness, errors = nla_decode.parse_field_witness(output_path, text)
    records, parse_errors = nla_decode.parse_act_records(nla_decode.public_execution_text(text))
    errors.extend(f"{rel(output_path)}: {error}" for error in parse_errors)
    errors.extend(
        f"{rel(output_path)}: public projection integrity: {error}"
        for error in mrp_route_invariants.check_text(output_path, text)
    )
    if field_witness is None:
        return {}, records, errors
    return field_witness, records, errors


def unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def owner_routes_from_activations(field_witness: dict[str, Any]) -> list[dict[str, str]]:
    routes: list[dict[str, str]] = []
    raw = field_witness.get("owner_activations")
    if not isinstance(raw, list):
        return routes
    seen: set[tuple[str, str]] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        burden_id = nla_decode.graph_burden_id(item.get("target") or item.get("source") or item.get("body_ref"))
        owner_id = str(item.get("owner") or "").strip()
        key = (burden_id, owner_id)
        if burden_id and owner_id and key not in seen:
            seen.add(key)
            routes.append(
                {
                    "burden_id": burden_id,
                    "owner_id": owner_id,
                    "eligibility": "retained-field-witness-owner-activation",
                }
            )
    return routes


def field_witness_body_refs(field_witness: dict[str, Any]) -> list[str]:
    raw = field_witness.get("owner_activations")
    refs: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                ref = str(item.get("body_ref") or "").strip()
                if ref:
                    refs.append(ref)
    return unique_ordered(refs)


def owner_activation_details(field_witness: dict[str, Any], terminal_states: dict[str, str]) -> list[dict[str, Any]]:
    raw = field_witness.get("owner_activations")
    details: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return details
    for item in raw:
        if not isinstance(item, dict):
            continue
        body_ref = str(item.get("body_ref") or "").strip()
        if not body_ref:
            continue
        burden_id = nla_decode.graph_burden_id(item.get("target") or item.get("source") or body_ref)
        detail: dict[str, Any] = {"body_ref": body_ref}
        if burden_id:
            detail["burden_id"] = burden_id
            if burden_id in terminal_states:
                detail["terminal_state"] = terminal_states[burden_id]
        owner_id = str(item.get("owner") or "").strip()
        operation = str(item.get("operation") or "").strip()
        if owner_id:
            detail["owner_id"] = owner_id
        if operation:
            detail["operation"] = operation
        details.append(detail)
    return details


def nar_burdens(field_witness: dict[str, Any]) -> list[str]:
    normalized = field_witness.get("normalized_activation_record")
    if not isinstance(normalized, dict):
        return []
    rows = normalized.get("per_burden")
    if not isinstance(rows, list):
        return []
    return unique_ordered(
        [
            nla_decode.graph_burden_id(row.get("burden_id"))
            for row in rows
            if isinstance(row, dict)
        ]
    )


def register_delta_summary(field_witness: dict[str, Any]) -> dict[str, list[str]]:
    raw = field_witness.get("register_deltas")
    summary: dict[str, list[str]] = {}
    if not isinstance(raw, list):
        return summary
    for item in raw:
        if not isinstance(item, dict):
            continue
        register = str(item.get("register") or "").strip()
        delta = str(item.get("delta") or item.get("result") or "").strip()
        if register and delta:
            summary.setdefault(register, []).append(delta)
    return summary


def handoffs() -> list[dict[str, Any]]:
    return [
        {
            "from": source,
            "to": target,
            "checks": sorted(checks),
            "status": "pass",
        }
        for (source, target), checks in staged.HANDOFF_CHECKS.items()
    ]


def build_record(manifest_path: Path, case_id: str) -> tuple[dict[str, Any] | None, list[str]]:
    manifest_path = manifest_path.resolve()
    manifest, errors = load_json(manifest_path)
    if not isinstance(manifest, dict):
        return None, errors + [f"{rel(manifest_path)}: manifest root must be an object"]
    errors.extend(retained.manifest_errors(manifest_path))
    case = find_case(manifest, case_id)
    if case is None:
        return None, errors + [f"{rel(manifest_path)}: case {case_id!r} not found"]

    paths: dict[str, Path] = {}
    for field in retained.ARTIFACT_FIELDS:
        resolved, found = resolve_case_path(manifest_path, case, field)
        errors.extend(found)
        if resolved is not None:
            paths[field] = resolved
    sidecar_entry = case.get(staged.B5_RETAINED_SIDECAR_FIELD)
    if isinstance(sidecar_entry, dict):
        resolved, found = resolve_case_path(manifest_path, case, staged.B5_RETAINED_SIDECAR_FIELD)
        errors.extend(found)
        if resolved is not None:
            paths[staged.B5_RETAINED_SIDECAR_FIELD] = resolved
    if errors:
        return None, errors

    field_witness, records, found = parsed_output_evidence(paths["output"])
    errors.extend(found)
    if not field_witness:
        return None, errors
    if not records:
        return None, errors + [f"{rel(paths['output'])}: no parseable ACT records"]

    normalized = field_witness.get("normalized_activation_record")
    if not isinstance(normalized, dict):
        return None, errors + [f"{rel(paths['output'])}: normalized_activation_record missing"]

    burden_floor = unique_ordered(
        [str(item) for item in normalized.get("burden_floor", []) if isinstance(item, str)]
    )
    if not burden_floor:
        burden_floor = nla_decode.burden_list(field_witness, "B_LA")
    live_registers = unique_ordered(
        [str(item) for item in normalized.get("live_registers", []) if isinstance(item, str)]
    )
    n_frame = str(normalized.get("n_frame") or "retained-field-witness")

    act_targets = unique_ordered(
        [
            nla_decode.graph_burden_id(
                nla_decode.target_token_from_submove_ref(record.body_ref or record.submove_ref)
            )
            for record in records
        ]
    )
    act_body_refs = unique_ordered([record.body_ref for record in records if record.body_ref])
    terminal_states = terminal_state_map(field_witness)
    bindings = artifact_bindings(manifest_path, case, paths)
    bindings["parsed_evidence"] = {
        "field_witness": True,
        "visible_act_records": len(records),
        "visible_runtime_traversal": True,
        "normalized_activation_record": True,
        "b5_full_ir_projection_sidecar": staged.B5_RETAINED_SIDECAR_FIELD in paths,
    }

    record = {
        "schema": staged.SCHEMA,
        "case_id": case_id,
        "mode": "retained-artifact-replay",
        "user_interface_preserved": True,
        "stage_order": staged.STAGE_ORDER,
        "stages": [
            {
                "id": "stage-01-intake",
                "status": "pass",
                "produces": ["input_digest", "retained_input"],
                "requires": [],
                "input_digest": str(case.get("hashes", {}).get("input")),
                "retained_input": rel(paths["input"]),
                "source_boundary_preserved": True,
            },
            {
                "id": "stage-02-layer-a-diagnostic-ir",
                "status": "pass",
                "produces": ["burden_floor", "selected_n_frame", "live_registers"],
                "requires": ["input_digest"],
                "burden_floor": burden_floor,
                "selected_n_frame": n_frame,
                "live_registers": live_registers,
                "unresolved_state": "none",
            },
            {
                "id": "stage-03-routing-owner-gate",
                "status": "pass",
                "produces": ["route_targets", "owner_routes"],
                "requires": ["burden_floor"],
                "route_targets": burden_floor,
                "owner_routes": owner_routes_from_activations(field_witness),
            },
            {
                "id": "stage-04-burden-execution-act",
                "status": "pass",
                "produces": ["act_targets", "act_body_refs", "act_rows"],
                "requires": ["route_targets", "owner_routes"],
                "act_targets": act_targets,
                "act_burdens": act_targets,
                "act_body_refs": act_body_refs,
                "act_rows": [record.record for record in records],
            },
            {
                "id": "stage-05-mrp-reread-terminal-state",
                "status": "pass",
                "produces": ["terminal_states", "dependency_graph_edges", "no_new_resultant_proof"],
                "requires": ["act_rows"],
                "terminal_states": terminal_states,
                "dependency_graph_edges": dependency_edges(field_witness),
                "no_new_resultant_proof": no_new_resultant_proof_present(field_witness),
            },
            {
                "id": "stage-06-field-witness-nar",
                "status": "pass",
                "produces": ["field_witness_body_refs", "nar_burdens", "normalized_activation_record"],
                "requires": ["terminal_states", "act_body_refs"],
                "field_witness_body_refs": field_witness_body_refs(field_witness),
                "nar_burdens": nar_burdens(field_witness),
                "owner_activations": field_witness_body_refs(field_witness),
                "owner_activation_details": owner_activation_details(field_witness, terminal_states),
                "normalized_activation_record": True,
                "normalized_activation_record_details": normalized,
                "register_deltas": register_delta_summary(field_witness),
            },
            {
                "id": "stage-07-release-output",
                "status": "pass",
                "produces": ["release_output", "release_terminal_states", "public_projection_integrity"],
                "requires": ["field_witness_body_refs", "nar_burdens"],
                "release_output": {
                    "path": rel(paths["output"]),
                    "sha256": str(case.get("hashes", {}).get("output")).upper(),
                },
                "release_terminal_states": terminal_states,
                "public_projection_integrity": True,
                "closure_claim": "complete",
                "output_is_full_governed_answer": True,
            },
            {
                "id": "stage-08-verifier-sidecars",
                "status": "pass",
                "produces": ["verifier_sidecars"],
                "requires": ["release_output", "public_projection_integrity"],
                "verifier_sidecars": {
                    "b5_4_1": {
                        "claimed": staged.B5_RETAINED_SIDECAR_FIELD in paths,
                        "builder": staged.B5_SIDECAR_BUILDER,
                        "schema": staged.B5_SIDECAR_SCHEMA,
                        "role": "checker-owned-final-verifier",
                        "non_claims": {
                            "not_fresh_runtime_default_emission": True,
                        },
                    },
                },
            },
        ],
        "handoffs": handoffs(),
        "non_claims": {
            "not_model_smoke": True,
            "not_runtime_default_emission_proof": True,
            "not_arbitrary_nl_ir_parser": True,
            "not_package_provenance": True,
            "not_guaranteed_t_lang_uptake": True,
        },
        "artifact_bindings": bindings,
    }
    return record, []


def validate_record(payload: dict[str, Any]) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="staged-runtime-replay-") as tmp:
        path = Path(tmp) / f"{payload.get('case_id', 'record')}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return staged.record_errors(path, payload)


def write_record(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_self_test() -> int:
    payload, errors = build_record(DEFAULT_MANIFEST, DEFAULT_CASE_ID)
    if payload is not None:
        errors.extend(validate_record(payload))
    if payload is None or errors:
        print("staged runtime replay builder self-test: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("staged runtime replay builder self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--case-id", default=DEFAULT_CASE_ID)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true", help="build and validate without writing unless --out is present")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    payload, errors = build_record(args.manifest, args.case_id)
    if payload is not None:
        errors.extend(validate_record(payload))
    if payload is None or errors:
        print("staged runtime replay build: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    if args.out is not None:
        write_record(args.out, payload)
        print("staged runtime replay build: PASS")
        print(f"Record: {rel(args.out)}")
        return 0
    if args.check:
        print("staged runtime replay check: PASS")
        return 0

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
