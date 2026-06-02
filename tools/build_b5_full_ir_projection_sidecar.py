#!/usr/bin/env python3
"""Build a checker-owned B.5.4 full-IR projection sidecar.

This builder does not parse arbitrary natural language into IR. It derives a
machine-facing projection only from an already governed output's visible ACT
records, parser-stable field_witness, normalized_activation_record, coverage
proof, and retained sidecar evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import check_nla_decode_semantic_faithfulness as nla_decode
from check_collapse_certificate_schema import certificate_errors
from check_graph_completeness import input_fingerprint_for_path
from check_mrp_generated_burden import graph_burden_id, graph_submove_id, strict_owner_family


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = "tools/build_b5_full_ir_projection_sidecar.py"
SIDECAR_SCHEMA = "b5-retained-proof-mode-full-ir-sidecar-v1"
PROOF_MODE = "retained-proof-corpus-sidecar"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    if not path.exists():
        return None, [f"{rel(path)}: file not found"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)}: invalid JSON: {exc}"]


def require_existing(path: Path, label: str) -> list[str]:
    if not path.exists():
        return [f"{label}: {rel(path)} missing"]
    if not path.is_file():
        return [f"{label}: {rel(path)} is not a file"]
    return []


def mirror_key(item: dict[str, Any]) -> tuple[str, str, str, str]:
    delta_result = str(item.get("delta") or "").split(":", 1)[-1]
    return (
        graph_burden_id(item.get("target") or item.get("source")),
        strict_owner_family(str(item.get("owner") or "")),
        str(item.get("operation") or ""),
        delta_result,
    )


def projection_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        graph_burden_id(row.get("burden_id")),
        strict_owner_family(str(row.get("owner_id") or "")),
        str(row.get("operation") or ""),
        str(row.get("delta_result") or ""),
    )


def mirror_for_projection_row(
    row: dict[str, Any],
    mirrors: list[dict[str, Any]],
    used: set[int],
    errors: list[str],
    index: int,
) -> dict[str, Any] | None:
    wanted = projection_key(row)
    matches = [
        (mirror_index, mirror)
        for mirror_index, mirror in enumerate(mirrors)
        if mirror_index not in used and mirror_key(mirror) == wanted
    ]
    if len(matches) != 1:
        errors.append(
            "normalized_activation_record.per_burden"
            f"[{index}]: expected exactly one owner_activation mirror for {wanted!r}, found {len(matches)}"
        )
        return None
    mirror_index, mirror = matches[0]
    used.add(mirror_index)
    return mirror


def source_basis_object(field_witness: dict[str, Any]) -> dict[str, Any]:
    raw = field_witness.get("source_basis")
    if isinstance(raw, dict):
        basis = raw.get("basis")
        if not isinstance(basis, list) or not all(isinstance(item, str) for item in basis):
            basis = []
        return {
            "source_basis_available": True,
            "sigma_inside_hard_registers": False,
            "basis": basis,
        }
    return {
        "source_basis_available": False,
        "sigma_inside_hard_registers": False,
        "basis": [],
    }


def formal_reread_object(field_witness: dict[str, Any]) -> dict[str, Any]:
    coverage = nla_decode.coverage_proof(field_witness)
    states = nla_decode.formal_reread_states(field_witness)
    final_state = states[-1] if states else {}
    return {
        "states_present": bool(states),
        "divergence_state": final_state.get("divergence_state", coverage.get("divergence_check")),
        "curl_state": final_state.get("curl_state", coverage.get("curl_check")),
        "escape_routes_checked": nla_decode.flattened_escape_routes(states),
        "no_new_resultant_proof": nla_decode.terminal_no_new_resultant_proof(states),
    }


def build_projection(field_witness: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    normalized = field_witness.get("normalized_activation_record")
    if not isinstance(normalized, dict):
        return None, ["field_witness.normalized_activation_record is required"]
    nar_rows = normalized.get("per_burden")
    if not isinstance(nar_rows, list) or not nar_rows:
        return None, ["field_witness.normalized_activation_record.per_burden is required"]

    diagnostic = nla_decode.diagnostic_completeness(field_witness)
    if not isinstance(diagnostic, dict):
        errors.append("field_witness.coverage_proof.diagnostic_completeness is required")
        diagnostic = {}

    mirrors = field_witness.get("owner_activations")
    if not isinstance(mirrors, list) or not mirrors:
        return None, ["field_witness.owner_activations is required"]
    mirror_dicts = [item for item in mirrors if isinstance(item, dict)]
    if len(mirror_dicts) != len(mirrors):
        errors.append("field_witness.owner_activations must contain only objects")

    per_burden: list[dict[str, Any]] = []
    decoded_rows: list[dict[str, Any]] = []
    used_mirrors: set[int] = set()
    for index, raw_row in enumerate(nar_rows):
        if not isinstance(raw_row, dict):
            errors.append(f"normalized_activation_record.per_burden[{index}]: row must be an object")
            continue
        row = nla_decode.canonical_projection_row(raw_row)
        per_burden.append(row)
        mirror = mirror_for_projection_row(row, mirror_dicts, used_mirrors, errors, index)
        if mirror is None:
            continue
        decoded_rows.append(
            {
                **row,
                "pressure": str(mirror.get("pressure") or ""),
                "body_ref": graph_submove_id(mirror.get("body_ref")),
            }
        )

    if len(decoded_rows) != len(per_burden):
        errors.append("decoded_ir.per_burden could not be derived for every projection row")

    projection: dict[str, Any] = {
        "schema": nla_decode.CANONICAL_IR_PROJECTION_SCHEMA,
        "n_frame": normalized.get("n_frame"),
        "live_registers": normalized.get("live_registers"),
        "burden_floor": normalized.get("burden_floor"),
        "per_burden": per_burden,
        "diagnostic_completeness": diagnostic,
    }

    hard_registers = field_witness.get("hard_registers")
    if isinstance(hard_registers, dict):
        projection["diagnostic_ir_schema_version"] = nla_decode.HARD_REGISTER_SCHEMA_VERSION
        projection["hard_registers"] = hard_registers
    register_composition = field_witness.get("register_composition")
    if isinstance(register_composition, dict):
        projection["register_composition"] = register_composition

    decoded_ir: dict[str, Any] = {
        "schema": nla_decode.CANONICAL_IR_DECODE_SCHEMA,
        "source_evidence": [
            "visible_act",
            "field_witness.owner_activations",
            "normalized_activation_record",
            "canonical_ir_projection",
        ],
        "n_frame": projection.get("n_frame"),
        "live_registers": projection.get("live_registers"),
        "burden_floor": projection.get("burden_floor"),
        "per_burden": decoded_rows,
        "diagnostic_completeness": diagnostic,
    }
    if "hard_registers" in projection:
        decoded_ir["hard_registers"] = projection["hard_registers"]
    if "register_composition" in projection:
        decoded_ir["register_composition"] = projection["register_composition"]
    projection["decoded_ir"] = decoded_ir

    coverage = nla_decode.coverage_proof(field_witness)
    dependency_graph = coverage.get("dependency_graph")
    if not isinstance(dependency_graph, dict):
        errors.append("field_witness.coverage_proof.dependency_graph is required")
        dependency_graph = {}

    b_la = set(nla_decode.burden_list(field_witness, "B_LA"))
    generated_map = nla_decode.generated_burden_map(field_witness)
    full_rows: list[dict[str, Any]] = []
    for index, row in enumerate(decoded_rows):
        burden_id = graph_burden_id(row.get("burden_id"))
        generated = generated_map.get(burden_id)
        if generated:
            generated_by = generated.get("generated_by")
            track = generated.get("track")
        elif burden_id in b_la:
            generated_by = None
            track = "baseline"
        else:
            errors.append(f"decoded_ir.per_burden[{index}]: burden is neither B_LA nor generated burden")
            generated_by = None
            track = "baseline"
        full_rows.append(
            {
                **row,
                "graph_role": nla_decode.graph_role_for_burden(burden_id, dependency_graph),
                "generated_by": generated_by,
                "track": track,
            }
        )

    source_evidence = [
        "visible_act",
        "field_witness.owner_activations",
        "normalized_activation_record",
        "canonical_ir_projection",
        "canonical_ir_projection.decoded_ir",
        "field_witness.coverage_proof",
        "field_witness.coverage_proof.dependency_graph",
    ]
    if nla_decode.field_witness_generated_burdens(field_witness):
        source_evidence.append("field_witness.generated_burdens")
    if nla_decode.formal_reread_states(field_witness):
        source_evidence.append("field_witness.formal_reread_states")
    if isinstance(field_witness.get("source_basis"), dict):
        source_evidence.append("field_witness.source_basis")

    full_ir_decode: dict[str, Any] = {
        "schema": nla_decode.FULL_IR_DECODE_SCHEMA,
        "source_evidence": source_evidence,
        "n_frame": projection.get("n_frame"),
        "live_registers": projection.get("live_registers"),
        "burden_floor": projection.get("burden_floor"),
        "B_LA": nla_decode.burden_list(field_witness, "B_LA"),
        "B_MRP": nla_decode.burden_list(field_witness, "B_MRP"),
        "B_total": nla_decode.burden_list(field_witness, "B_total"),
        "dependency_graph": dependency_graph,
        "terminal_states": coverage.get("terminal_states"),
        "diagnostic_completeness": diagnostic,
        "per_burden": full_rows,
        "generated_burdens": nla_decode.field_witness_generated_burdens(field_witness),
        "formal_reread": formal_reread_object(field_witness),
        "source_basis": source_basis_object(field_witness),
    }
    if "hard_registers" in projection:
        full_ir_decode["hard_registers"] = projection["hard_registers"]
    if "register_composition" in projection:
        full_ir_decode["register_composition"] = projection["register_composition"]
    projection["full_ir_decode"] = full_ir_decode

    projection["proof_mode"] = {
        "schema": nla_decode.FULL_IR_PROOF_MODE_SCHEMA,
        "mode": PROOF_MODE,
        "source_evidence": [
            "visible_noetic_field_opening",
            "visible_layer_a_diagnostic_ir_header",
            "field_witness.canonical_ir_projection",
            "field_witness.canonical_ir_projection.decoded_ir",
            "field_witness.canonical_ir_projection.full_ir_decode",
        ],
        "machine_facing": True,
        "schema_light_absent_valid": True,
        "requires_decoded_ir": True,
        "visible_opening_header_preserved": True,
        "arbitrary_nl_ir_parser_claim": False,
        "default_runtime_emission_claim": False,
        "t_lang_uptake_claim": False,
    }

    return (None if errors else projection), errors


def validate_inputs(
    input_path: Path,
    output_path: Path,
    certificate_path: Path,
    grapher_html_path: Path | None,
) -> tuple[dict[str, Any] | None, list[Any] | None, dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    for label, path in (
        ("input", input_path),
        ("output", output_path),
        ("collapse_certificate", certificate_path),
    ):
        errors.extend(require_existing(path, label))
    if grapher_html_path is not None:
        errors.extend(require_existing(grapher_html_path, "grapher_html"))
    if errors:
        return None, None, None, errors

    output_text = read_text(output_path)
    field_witness, found = nla_decode.parse_field_witness(output_path, output_text)
    errors.extend(found)

    records, parse_errors = nla_decode.parse_act_records(nla_decode.public_execution_text(output_text))
    errors.extend(f"{rel(output_path)}: {message}" for message in parse_errors)
    if not records:
        errors.append(f"{rel(output_path)}: no visible ACT records available for sidecar projection")

    nla_errors = nla_decode.nla_decode_errors(output_path, output_text)
    if nla_errors:
        errors.append(f"{rel(output_path)}: schema-light NLA semantic faithfulness must pass before sidecar build")
        errors.extend(nla_errors)

    certificate, cert_load_errors = load_json(certificate_path)
    errors.extend(cert_load_errors)
    if isinstance(certificate, dict):
        errors.extend(f"{rel(certificate_path)}: {error}" for error in certificate_errors(certificate))
        expected_fingerprint = input_fingerprint_for_path(input_path)
        if certificate.get("input_fingerprint") != expected_fingerprint:
            errors.append(
                f"{rel(certificate_path)}: input_fingerprint does not match {rel(input_path)}"
            )
        for key in ("collapse_positive", "coverage_complete", "diagnostic_completeness"):
            if certificate.get(key) is not True:
                errors.append(f"{rel(certificate_path)}: {key} must be true")
    else:
        errors.append(f"{rel(certificate_path)}: collapse certificate must be a JSON object")

    if grapher_html_path is not None:
        grapher_text = read_text(grapher_html_path)
        if "Verdict: reconstructible" not in grapher_text:
            errors.append(f"{rel(grapher_html_path)}: missing reconstructible verdict")
        if "No warnings." not in grapher_text:
            errors.append(f"{rel(grapher_html_path)}: missing warning-clean marker")

    return field_witness, records, certificate if isinstance(certificate, dict) else None, errors


def build_sidecar(
    input_path: Path,
    output_path: Path,
    certificate_path: Path,
    grapher_html_path: Path | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    field_witness, records, _certificate, errors = validate_inputs(
        input_path,
        output_path,
        certificate_path,
        grapher_html_path,
    )
    if errors:
        return None, errors
    assert field_witness is not None
    assert records is not None

    projection, found = build_projection(field_witness)
    errors.extend(found)
    if projection is None:
        return None, errors

    output_text = read_text(output_path)
    projection_errors = nla_decode.canonical_ir_projection_object_errors(
        output_path,
        output_text,
        field_witness,
        records,
        projection,
    )
    if projection_errors:
        errors.append(f"{rel(output_path)}: generated sidecar projection failed semantic validation")
        errors.extend(projection_errors)
        return None, errors

    source = {
        "raw_input": rel(input_path),
        "governed_output": rel(output_path),
        "collapse_certificate": rel(certificate_path),
        "builder": BUILDER_PATH,
    }
    if grapher_html_path is not None:
        source["grapher_html"] = rel(grapher_html_path)

    return {
        "schema": SIDECAR_SCHEMA,
        "source": source,
        "projection": projection,
    }, []


def write_sidecar(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_self_test() -> int:
    case = ROOT / "tests" / "retained-proof-corpus" / "v0.4.3.0-schema-light" / "valid" / "sidecar-backed" / "cases" / "a9-science-source"
    with tempfile.TemporaryDirectory(prefix="b5-full-ir-sidecar-") as tmp:
        sidecar_path = Path(tmp) / "b5-full-ir-projection-sidecar.json"
        payload, errors = build_sidecar(
            case / "input.txt",
            case / "output.md",
            case / "collapse-certificate.json",
            case / "grapher.html",
        )
        if payload is None:
            print("B.5 full-IR sidecar builder self-test: FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        write_sidecar(sidecar_path, payload)
        reread, reread_errors = load_json(sidecar_path)
        if reread_errors or reread != payload:
            print("B.5 full-IR sidecar builder self-test: FAIL")
            for error in reread_errors:
                print(f"- {error}")
            if reread != payload:
                print("- generated sidecar did not round-trip")
            return 1
    print("B.5 full-IR sidecar builder self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--collapse-certificate", type=Path)
    parser.add_argument("--grapher-html", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    missing = [
        name
        for name, value in (
            ("--input", args.input),
            ("--output", args.output),
            ("--collapse-certificate", args.collapse_certificate),
            ("--out", args.out),
        )
        if value is None
    ]
    if missing:
        parser.error("missing required argument(s): " + ", ".join(missing))

    assert args.input is not None
    assert args.output is not None
    assert args.collapse_certificate is not None
    assert args.out is not None
    payload, errors = build_sidecar(
        args.input,
        args.output,
        args.collapse_certificate,
        args.grapher_html,
    )
    if payload is None:
        print("B.5 full-IR sidecar build: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    write_sidecar(args.out, payload)
    print("B.5 full-IR sidecar build: PASS")
    print(f"Sidecar: {rel(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
