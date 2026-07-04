#!/usr/bin/env python3
"""Field-witness binding checker — Plan 03 (Lane C, Phase 1 binding).

Two deterministic, current-artifact checks:

  1. Single-source consistency: schema/field-witness.schema.json's `required` and
     optional properties are asserted EQUAL to check_ir_instance_integrity's
     FIELD_WITNESS_KEYS / FIELD_WITNESS_OPTIONAL_KEYS, and additionalProperties is
     false. This makes the schema and the Python key sets one source; changing one
     without the other fails the check.
  2. Committed-artifact validation: the one committed standalone field_witness
     artifact (tests/live-witness-fixtures/valid/*.field_witness.json) conforms to
     the top-level key contract (all required keys present; no key outside
     required|optional).

Scope discipline: this is a STRUCTURAL top-level key contract only, not a
semantic-faithfulness, uptake, provenance, or release claim, and it does NOT
recompute hashes or bind an output envelope (that is the artifact-gated Phase 3,
not built here). It does NOT validate embedded field_witness in historical
retained outputs, so it cannot retroactively break a legacy output.

Usage:
  python tools/check_field_witness_binding.py
  python tools/check_field_witness_binding.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema" / "field-witness.schema.json"
STANDALONE_GLOB = "tests/live-witness-fixtures/valid/*.field_witness.json"


def schema_consistency(schema: dict, py_required: set[str], py_optional: set[str]) -> list[str]:
    """Pure core (unit-tested): schema key sets must equal the Python key sets."""
    errors: list[str] = []
    req = set(schema.get("required", []))
    props = set(schema.get("properties", {}))
    opt = props - req
    if req != py_required:
        errors.append(
            f"schema required != FIELD_WITNESS_KEYS "
            f"(schema-only={sorted(req - py_required)}, python-only={sorted(py_required - req)})"
        )
    if opt != py_optional:
        errors.append(
            f"schema optional properties != FIELD_WITNESS_OPTIONAL_KEYS "
            f"(schema-only={sorted(opt - py_optional)}, python-only={sorted(py_optional - opt)})"
        )
    if schema.get("additionalProperties") is not False:
        errors.append("schema additionalProperties must be false (top-level key contract is closed)")
    return errors


def witness_key_errors(keys: set[str], required: set[str], optional: set[str], label: str) -> list[str]:
    """Pure core (unit-tested): required present, no key outside required|optional."""
    errors: list[str] = []
    missing = sorted(required - keys)
    if missing:
        errors.append(f"{label}: missing required field_witness keys: {missing}")
    unknown = sorted(keys - required - optional)
    if unknown:
        errors.append(f"{label}: unknown top-level field_witness keys: {unknown}")
    return errors


def _real_run() -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    sys.path.insert(0, str(ROOT / "tools"))
    import check_ir_instance_integrity as ir
    errors = schema_consistency(schema, set(ir.FIELD_WITNESS_KEYS), set(ir.FIELD_WITNESS_OPTIONAL_KEYS))
    required = set(schema.get("required", []))
    optional = set(schema.get("properties", {})) - required
    artifacts = sorted(glob.glob(str(ROOT / STANDALONE_GLOB)))
    if not artifacts:
        errors.append(f"no committed standalone field_witness artifact matched {STANDALONE_GLOB}")
    for path in artifacts:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        rel = str(Path(path).relative_to(ROOT)).replace("\\", "/")
        errors.extend(witness_key_errors(set(data), required, optional, rel))
    return errors


def self_test() -> int:
    req = {"a", "b", "c"}
    opt = {"x", "y"}
    good_schema = {"required": sorted(req), "properties": {k: {} for k in req | opt}, "additionalProperties": False}
    cases = [
        ("consistent schema -> ok", schema_consistency(good_schema, req, opt) == []),
        ("required drift flagged",
         any("required !=" in e for e in schema_consistency({**good_schema, "required": ["a", "b"]}, req, opt))),
        ("optional drift flagged",
         any("optional properties !=" in e for e in
             schema_consistency({"required": sorted(req), "properties": {k: {} for k in req | {"z"}}, "additionalProperties": False}, req, opt))),
        ("additionalProperties!=false flagged",
         any("additionalProperties" in e for e in schema_consistency({**good_schema, "additionalProperties": True}, req, opt))),
        ("valid keys -> ok", witness_key_errors(req, req, opt, "w") == []),
        ("valid + optional key -> ok", witness_key_errors(req | {"x"}, req, opt, "w") == []),
        ("missing required flagged", any("missing required" in e for e in witness_key_errors({"a", "b"}, req, opt, "w"))),
        ("unknown key flagged", any("unknown top-level" in e for e in witness_key_errors(req | {"Q"}, req, opt, "w"))),
    ]
    ok = all(p for _, p in cases)
    for name, p in cases:
        print(f"  self-test {'PASS' if p else 'FAIL'}: {name}")
    print(f"field-witness-binding self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Field-witness binding checker (Plan 03 Lane C)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic pure-core self-test")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not SCHEMA.is_file():
        print(f"field-witness binding: FAIL (missing {SCHEMA})")
        return 1
    errors = _real_run()
    if errors:
        print(f"field-witness binding: FAIL ({len(errors)} problem(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("field-witness binding: PASS (schema<->key-set consistency + committed standalone artifact conform)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
