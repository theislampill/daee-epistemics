#!/usr/bin/env python3
"""Field-witness artifact-binding envelope generator (Plan 03, Phase 3).

Emits a ``field-witness-artifact-binding-v1`` envelope for a retained proof case from
its PUBLIC artifacts (``output.md`` alone), closing the output-side binding gap (F1)
that lets two byte-identical certificates bind different outputs. Computed fields:

  - ``output_sha256``   : daee-canon-eol-v1 hash of the ``output.md`` bytes.
  - ``sidecar_sha256``  : daee-canon-eol-v1 hash of the embedded ``field_witness`` block,
                          canonicalized (sort_keys, tight separators) before hashing --
                          the retained "sidecar" is embedded in ``output.md``, not a
                          separate file, so the stable canonical projection is hashed.
  - ``origin_sha256``   : null. Origin lives under the git-ignored ``.daee/`` tree, absent
                          from a clone (finding F3); it is structurally unavailable, not a gap.
  - ``act_rows_hash``   : canonical-JSON hash of the visible ACT rows (the 8 semantic
                          ``ActRecord`` fields; the raw ``record`` line is excluded to keep
                          the projection whitespace-stable). Order-preserving: the ACT
                          sequence is content, not a set.
  - ``nar_hash``        : canonical-JSON hash of ``field_witness.normalized_activation_record``.
  - ``owner_activation_ordering_hash`` : canonical-JSON hash of
                          ``field_witness.owner_activation_ordering`` (a schema-optional key),
                          or null when absent.

Write-safety: it WRITES NOTHING by default (prints the envelope JSON to stdout); it
writes a NEW envelope file only with an explicit ``--out PATH``, and it NEVER mutates any
retained artifact (it reads ``output.md`` bytes only). ``--self-test`` writes nothing.

``binding_status`` is NOT auto-stamped -- assigning it over 24 legacy cases is an owner
evidentiary claim (OD-1). It is an explicit input, defaulting to the honest
``legacy_unbound``; ``current_bound`` is never stamped automatically.

Non-claims: a hash binding does not prove semantic correctness, faithful generation,
interlocutor uptake, or cross-host behavior; a regenerated envelope never impersonates a
released asset. This is byte / projection provenance only -- no safety, refusal, or
policy semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Any

# Sibling imports resolve because tools/ is the script dir on sys.path.
from check_retained_proof_corpus import sha256_artifact_bytes
from closure_witness_lib import extract_embedded_field_witness
from check_mrp_generated_burden import ActRecord, parse_act_records
from check_nla_decode_semantic_faithfulness import public_execution_text
from witness_artifact_roles import canonical_json_sha256

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "field-witness-artifact-binding-v1"
CANONICALIZATION = "daee-canon-eol-v1"
PROOF_CLASS = "sidecar-backed-structural"
BINDING_STATUS_VALUES = ("current_bound", "legacy_unbound", "known_contract_drift")
NON_CLAIMS = ["hash binding does not prove semantic correctness or fresh generation"]
# The 8 semantic ActRecord fields; the raw `record` line is excluded so the projection
# does not couple to incidental whitespace.
ACT_PROJECTION_FIELDS = ("submove_ref", "owner", "operation", "pi", "body_ref", "delta", "delta_result", "land")


def build_artifact_binding(
    public_graph: dict[str, Any],
    audit_envelope_projection: dict[str, Any],
    *,
    source_commit: str,
    output_sha256: str,
    stage04_projection_sha256: str,
    stage06_projection_sha256: str,
    stage07_projection_sha256: str,
    act_rows_hash: str,
    nar_hash: str,
    owner_activation_ordering_hash: str,
    binding_status: str,
) -> dict[str, Any]:
    """Build the subordinate canonical binding record from validated objects."""
    if binding_status not in BINDING_STATUS_VALUES:
        raise ValueError(f"binding_status must be one of {BINDING_STATUS_VALUES}, got {binding_status!r}")
    fingerprint = public_graph.get("activation_lifecycle_fingerprint_sha256")
    if not isinstance(fingerprint, str):
        raise ValueError("current public graph requires activation_lifecycle_fingerprint_sha256")
    return {
        "schema_version": SCHEMA_VERSION,
        "canonicalization": "daee-canonical-json-v1",
        "source_commit": source_commit,
        "output_sha256": output_sha256,
        "public_field_witness_sha256": canonical_json_sha256(public_graph),
        "audit_envelope_projection_sha256": canonical_json_sha256(audit_envelope_projection),
        "activation_lifecycle_fingerprint_sha256": fingerprint,
        "stage04_projection_sha256": stage04_projection_sha256,
        "stage06_projection_sha256": stage06_projection_sha256,
        "stage07_projection_sha256": stage07_projection_sha256,
        "act_rows_hash": act_rows_hash,
        "nar_hash": nar_hash,
        "owner_activation_ordering_hash": owner_activation_ordering_hash,
        "proof_class": "stage08-structural-audit" if binding_status == "current_bound" else "historical-structural-binding",
        "binding_status": binding_status,
        "non_claims": ["Hash binding does not establish semantic truth or fresh generation."],
    }


def attach_artifact_binding(audit_envelope_projection: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    """Return a new audit envelope with the subordinate binding attached."""
    if audit_envelope_projection.get("schema_version") != "field-witness-envelope-v1":
        raise ValueError("audit envelope projection must use field-witness-envelope-v1")
    if "artifact_binding" in audit_envelope_projection:
        raise ValueError("audit envelope projection must not already contain artifact_binding")
    envelope = json.loads(json.dumps(audit_envelope_projection, ensure_ascii=False))
    envelope["artifact_binding"] = json.loads(json.dumps(binding, ensure_ascii=False))
    return envelope


def projection_hash(obj: Any) -> str:
    """Canonical-JSON projection hash (docs/field-witness-canonicalization-spec.md):
    sort_keys + tight separators -> UTF-8 -> SHA-256 -> uppercase hex."""
    encoded = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def act_rows_projection(records: list[ActRecord]) -> list[dict[str, str]]:
    """Ordered list of the 8 semantic ACT fields per row (order-preserving)."""
    return [{field: getattr(record, field) for field in ACT_PROJECTION_FIELDS} for record in records]


def canonical_sidecar_bytes(field_witness: dict[str, Any]) -> bytes:
    """Canonical byte projection of the embedded field_witness for sidecar_sha256."""
    return json.dumps(field_witness, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def build_envelope(output_md_path: Path, *, source_commit: str, binding_status: str) -> dict[str, Any]:
    """Deprecated compatibility wrapper: compute a historical binding record.

    The filename/function name predates ADR-046-005. It now resolves to the
    subordinate ``artifact_binding`` role and never claims to build the current
    Stage08 audit envelope.
    """
    if binding_status not in BINDING_STATUS_VALUES:
        raise ValueError(f"binding_status must be one of {BINDING_STATUS_VALUES}, got {binding_status!r}")
    warnings.warn(
        "build_envelope() is a compatibility wrapper for artifact_binding; use build_artifact_binding() for current triplets",
        DeprecationWarning,
        stacklevel=2,
    )
    output_bytes = output_md_path.read_bytes()
    text = output_bytes.decode("utf-8")
    field_witness = extract_embedded_field_witness(text)
    if field_witness is None:
        raise ValueError(f"no embedded field_witness found in {output_md_path}")
    records, act_errors = parse_act_records(public_execution_text(text))
    if act_errors:
        raise ValueError(f"ACT parse errors in {output_md_path}: {act_errors}")
    owner_ordering = field_witness.get("owner_activation_ordering")
    act_hash = canonical_json_sha256(act_rows_projection(records))
    nar_hash = canonical_json_sha256(field_witness.get("normalized_activation_record"))
    ordering_hash = canonical_json_sha256(owner_ordering)
    graph_hash = canonical_json_sha256(field_witness)
    fingerprint = canonical_json_sha256({"owner_activations": field_witness.get("owner_activations"), "normalized_activation_record": field_witness.get("normalized_activation_record"), "B_total": field_witness.get("B_total")})
    return {
        "schema_version": SCHEMA_VERSION,
        "canonicalization": "daee-canonical-json-v1",
        "source_commit": source_commit,
        "output_sha256": sha256_artifact_bytes(output_bytes).lower(),
        "public_field_witness_sha256": graph_hash,
        "audit_envelope_projection_sha256": canonical_json_sha256(None),
        "activation_lifecycle_fingerprint_sha256": fingerprint,
        "stage04_projection_sha256": act_hash,
        "stage06_projection_sha256": nar_hash,
        "stage07_projection_sha256": graph_hash,
        "act_rows_hash": act_hash,
        "nar_hash": nar_hash,
        "owner_activation_ordering_hash": ordering_hash,
        "proof_class": "historical-public-only-binding",
        "binding_status": binding_status,
        "non_claims": ["Hash binding does not establish semantic truth or fresh generation.", "Historical wrapper has no current Stage08 audit envelope projection."],
    }


def git_head() -> str:
    result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)
    head = result.stdout.strip()
    return head if re.fullmatch(r"[0-9a-f]{40}", head) else "0" * 40


def self_test() -> int:
    checks: list[tuple[str, bool]] = []
    a = projection_hash({"n_frame": 1, "live_registers": [2, 3], "burden_floor": {"x": 1}})
    b = projection_hash({"burden_floor": {"x": 1}, "live_registers": [2, 3], "n_frame": 1})
    checks.append(("projection_hash is key-order insensitive", a == b))
    checks.append(("projection hash is uppercase 64-hex", re.fullmatch(r"[A-F0-9]{64}", a) is not None))
    # daee-canon-eol-v1 portability (reuse sha256_artifact_bytes, do not reimplement)
    checks.append(("CRLF/LF twins hash equal", sha256_artifact_bytes(b"a\r\nb\n") == sha256_artifact_bytes(b"a\nb\n")))
    checks.append(("NUL twin hashes differ", sha256_artifact_bytes(b"a\x00b") != sha256_artifact_bytes(b"ab")))
    rows = [
        ActRecord(record="r1", submove_ref="B1", owner="o", operation="op", pi="pi", body_ref="br", delta="d", delta_result="dr", land="L"),
        ActRecord(record="r2", submove_ref="B2", owner="o", operation="op", pi="pi", body_ref="br", delta="d", delta_result="dr", land="L"),
    ]
    forward = projection_hash(act_rows_projection(rows))
    reverse = projection_hash(act_rows_projection(list(reversed(rows))))
    checks.append(("ACT projection is order-preserving (sequence is content)", forward != reverse))
    projected = act_rows_projection(rows[:1])[0]
    checks.append(("ACT projection excludes raw record field", "record" not in projected and set(projected) == set(ACT_PROJECTION_FIELDS)))
    current_root = ROOT / "tests" / "witness-artifact-roles" / "valid" / "current-triplet"
    graph = json.loads((current_root / "public-graph.json").read_text(encoding="utf-8"))
    envelope = json.loads((current_root / "audit-envelope.json").read_text(encoding="utf-8"))
    expected_binding = json.loads((current_root / "artifact-binding.json").read_text(encoding="utf-8"))
    projection = dict(envelope)
    projection.pop("artifact_binding")
    built = build_artifact_binding(
        graph, projection,
        source_commit=expected_binding["source_commit"], output_sha256=expected_binding["output_sha256"],
        stage04_projection_sha256=expected_binding["stage04_projection_sha256"],
        stage06_projection_sha256=expected_binding["stage06_projection_sha256"],
        stage07_projection_sha256=expected_binding["stage07_projection_sha256"],
        act_rows_hash=expected_binding["act_rows_hash"], nar_hash=expected_binding["nar_hash"],
        owner_activation_ordering_hash=expected_binding["owner_activation_ordering_hash"], binding_status="current_bound",
    )
    checks.append(("current binding builder matches canonical triplet", built == expected_binding))
    checks.append(("binding attaches without changing projection", attach_artifact_binding(projection, built) == envelope))
    try:
        build_envelope(Path("__field_witness_envelope_selftest_nonexistent__"), source_commit="0" * 40, binding_status="bogus")
        checks.append(("build_envelope validates binding_status before reading", False))
    except ValueError:
        checks.append(("build_envelope validates binding_status before reading", True))
    ok = all(passed for _, passed in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"field-witness-envelope self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Field-witness envelope generator (Plan 03, Phase 3)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic self-test and exit (writes nothing)")
    parser.add_argument("--output", type=Path, help="path to a case output.md to build an envelope from")
    parser.add_argument("--source-commit", default=None, help="40-hex source commit (default: git rev-parse HEAD)")
    parser.add_argument(
        "--binding-status",
        default="legacy_unbound",
        choices=BINDING_STATUS_VALUES,
        help="binding_status for the case (default legacy_unbound; NEVER auto-current_bound -- OD-1 owner claim)",
    )
    parser.add_argument("--out", type=Path, default=None, help="write the envelope JSON to this NEW path (default: print to stdout, write nothing)")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.output is None:
        parser.error("--output <case output.md> is required (or use --self-test)")
    print("DEPRECATION witness-role: build_field_witness_envelope --output builds artifact_binding compatibility output, not audit_envelope", file=sys.stderr)
    envelope = build_envelope(args.output, source_commit=args.source_commit or git_head(), binding_status=args.binding_status)
    rendered = json.dumps(envelope, indent=2, ensure_ascii=False)
    if args.out is not None:
        args.out.write_text(rendered + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
