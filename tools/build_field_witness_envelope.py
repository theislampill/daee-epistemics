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
from pathlib import Path
from typing import Any

# Sibling imports resolve because tools/ is the script dir on sys.path.
from check_retained_proof_corpus import sha256_artifact_bytes
from closure_witness_lib import extract_embedded_field_witness
from check_mrp_generated_burden import ActRecord, parse_act_records
from check_nla_decode_semantic_faithfulness import public_execution_text

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "field-witness-artifact-binding-v1"
CANONICALIZATION = "daee-canon-eol-v1"
PROOF_CLASS = "sidecar-backed-structural"
BINDING_STATUS_VALUES = ("current_bound", "legacy_unbound", "known_contract_drift")
NON_CLAIMS = ["hash binding does not prove semantic correctness or fresh generation"]
# The 8 semantic ActRecord fields; the raw `record` line is excluded so the projection
# does not couple to incidental whitespace.
ACT_PROJECTION_FIELDS = ("submove_ref", "owner", "operation", "pi", "body_ref", "delta", "delta_result", "land")


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
    """Compute the envelope for one retained case from its public output.md. Read-only."""
    if binding_status not in BINDING_STATUS_VALUES:
        raise ValueError(f"binding_status must be one of {BINDING_STATUS_VALUES}, got {binding_status!r}")
    output_bytes = output_md_path.read_bytes()
    text = output_bytes.decode("utf-8")
    field_witness = extract_embedded_field_witness(text)
    if field_witness is None:
        raise ValueError(f"no embedded field_witness found in {output_md_path}")
    records, act_errors = parse_act_records(public_execution_text(text))
    if act_errors:
        raise ValueError(f"ACT parse errors in {output_md_path}: {act_errors}")
    owner_ordering = field_witness.get("owner_activation_ordering")
    return {
        "schema_version": SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "source_commit": source_commit,
        "output_sha256": sha256_artifact_bytes(output_bytes),
        "sidecar_sha256": sha256_artifact_bytes(canonical_sidecar_bytes(field_witness)),
        "origin_sha256": None,
        "act_rows_hash": projection_hash(act_rows_projection(records)),
        "nar_hash": projection_hash(field_witness.get("normalized_activation_record")),
        "owner_activation_ordering_hash": projection_hash(owner_ordering) if isinstance(owner_ordering, dict) else None,
        "proof_class": PROOF_CLASS,
        "binding_status": binding_status,
        "non_claims": NON_CLAIMS,
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
