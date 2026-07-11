#!/usr/bin/env python3
"""Load the sole data-only five-smoke input registry."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "tests" / "smoke-matrix" / "v0.4.6.0-wip-five-smoke.json"
CANONICAL_REGISTRY_DIGEST = "eedddd82637438c49ae51bce428a44e758b2a2910020ec3b40303458e38f6d4a"
TOP_KEYS = {"schema", "kind", "matrix_id", "cases", "forbidden_case_fields"}
CASE_KEYS = {"case_id", "input_path", "raw_bytes", "raw_sha256"}
FORBIDDEN_CASE_FIELDS = ["expected_burdens", "expected_submoves", "expected_route", "expected_citations", "expected_answer", "expected_output_bytes"]


def _error(failure_class: str, message: str) -> dict[str, str]:
    return {"failure_class": failure_class, "message": message}


def validate_registry(data: object, root: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not isinstance(data, dict):
        return [_error("registry_shape", "registry must be an object")]
    digest=hashlib.sha256((json.dumps(data,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
    if digest!=CANONICAL_REGISTRY_DIGEST:
        return [_error("registry_identity","registry must equal the immutable v0.4.6.0-wip canonical five tuples")]
    if set(data) != TOP_KEYS:
        return [_error("registry_metadata", f"registry keys must be identity/input custody only: {sorted(TOP_KEYS)}")]
    if data.get("schema") != "daee-smoke-matrix-v1" or data.get("kind") != "input-registry":
        return [_error("registry_discriminator", "registry discriminator mismatch")]
    if data.get("forbidden_case_fields") != FORBIDDEN_CASE_FIELDS:
        return [_error("registry_anti_bank_contract", "forbidden_case_fields must equal the canonical anti-answer-bank field list")]
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != 5:
        return [_error("registry_case_count", "registry must contain exactly five cases")]
    ids: set[str] = set()
    paths: set[str] = set()
    resolved_root = root.resolve()
    for index, row in enumerate(cases):
        if not isinstance(row, dict) or set(row) != CASE_KEYS:
            return [_error("registry_case_metadata", f"case {index} must contain only identity/input custody fields")]
        case_id = row.get("case_id")
        rel = row.get("input_path")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            return [_error("registry_duplicate_id", f"case {index} has an empty or duplicate case_id")]
        if not isinstance(rel, str) or not rel or rel in paths:
            return [_error("registry_duplicate_path", f"case {index} has an empty or duplicate input_path")]
        ids.add(case_id); paths.add(rel)
        pure = PurePosixPath(rel.replace("\\", "/"))
        if pure.is_absolute() or ".." in pure.parts:
            return [_error("registry_path_escape", f"case {case_id} input path escapes repository")]
        path = (root / Path(*pure.parts)).resolve()
        if path != resolved_root and resolved_root not in path.parents:
            return [_error("registry_path_escape", f"case {case_id} input path escapes repository")]
        if not path.is_file():
            return [_error("registry_input_missing", f"case {case_id} input is missing")]
        raw = path.read_bytes()
        if not raw:
            return [_error("registry_input_empty", f"case {case_id} input is empty")]
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            return [_error("registry_input_encoding", f"case {case_id} input is not UTF-8")]
        if b"\r" in raw:
            return [_error("registry_input_line_endings", f"case {case_id} input must use LF only")]
        if row.get("raw_bytes") != len(raw):
            return [_error("registry_input_bytes", f"case {case_id} byte count mismatch")]
        digest = hashlib.sha256(raw).hexdigest().upper()
        if row.get("raw_sha256") != digest:
            return [_error("registry_input_hash", f"case {case_id} raw SHA-256 mismatch")]
    return errors


def load_registry(path: Path = DEFAULT_REGISTRY, root: Path = ROOT) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_registry(data, root)
    if errors:
        raise ValueError(json.dumps(errors[0], sort_keys=True))
    return data


def self_test() -> int:
    base=json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"));checks=[("valid canonical custody registry",not validate_registry(base,ROOT))]
    mutations=[]
    changed=json.loads(json.dumps(base));changed["cases"][0]["case_id"]+="-changed";mutations.append(changed)
    changed=json.loads(json.dumps(base));changed["cases"][0]["input_path"]=changed["cases"][1]["input_path"];mutations.append(changed)
    changed=json.loads(json.dumps(base));changed["cases"][0]["raw_sha256"]="0"*64;mutations.append(changed)
    checks.extend((f"canonical tuple mutation {index} rejected",validate_registry(value,ROOT)[0]["failure_class"]=="registry_identity") for index,value in enumerate(mutations,1))
    with tempfile.TemporaryDirectory() as td:
        mirror=Path(td)
        for row in base["cases"]:
            target=mirror/row["input_path"];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/row["input_path"],target)
        first=mirror/base["cases"][0]["input_path"];first.write_bytes(first.read_bytes()+b"changed\n")
        checks.append(("prompt-text mutation rejected",validate_registry(base,mirror)[0]["failure_class"] in {"registry_input_bytes","registry_input_hash"}))
    for name, ok in checks: print(f"  self-test {'PASS' if ok else 'FAIL'}: {name}")
    ok = all(result for _, result in checks)
    print(f"smoke-matrix-registry self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", "--manifest", dest="registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--emit-cases-json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test: return self_test()
    try: data = load_registry(args.registry)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True)); return 1
    if args.emit_cases_json:
        print(json.dumps(data["cases"], ensure_ascii=False, sort_keys=True))
        return 0
    print(json.dumps({"status": "PASS", "matrix_id": data["matrix_id"], "case_count": len(data["cases"])}, sort_keys=True)); return 0


if __name__ == "__main__": sys.exit(main())
