#!/usr/bin/env python3
"""Pure, package-root-only DAEE runtime context selection.

The resolver performs no process, network, model, repository-write, or atomics
access.  It returns selected package byte slices; prompt composition and
delivery proof remain separate responsibilities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

STAGE_MANDATORY = {
    "01": ["SKILL.md"],
    "02": ["references/runtime-diagnostic-core.md", "references/runtime-core-ir.md"],
    "03": ["references/runtime-core-routing.md"],
    "04": [],
    "05": ["references/runtime-core-recursion.md"],
    "06": ["references/runtime-core-pipeline.md"],
    "07": ["references/runtime-shard-output-release.md", "references/runtime-shard-render-contract.md"],
}


class ResolutionError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _contained(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ResolutionError(f"package path is not relative: {relative!r}")
    base = root.resolve(strict=True)
    target = (base / relative).resolve(strict=True)
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ResolutionError(f"package path escapes root: {relative}") from exc
    if not target.is_file():
        raise ResolutionError(f"package component is not a file: {relative}")
    return target


def read_package_bytes(root: Path, relative: str) -> bytes:
    return _contained(root, relative).read_bytes()


def exact_line_slice(data: bytes, start: int, end: int) -> bytes:
    if start < 1 or end < start:
        raise ResolutionError("invalid one-based inclusive line span")
    lines = data.splitlines()
    if end > len(lines):
        raise ResolutionError("line span exceeds source")
    # cold-law-manifest-v1 hashes the anchor-delimited content joined by LF,
    # excluding a trailing newline (the convention owned by
    # check_cold_law_digest.parse_clause_spans()).
    return b"\n".join(lines[start - 1:end])


def module_section_span(data: bytes, module_id: str) -> tuple[bytes, int, int]:
    marker = f"## RUNTIME MODULE: {module_id}".encode()
    start = data.find(marker)
    if start < 0:
        raise ResolutionError(f"module section missing: {module_id}")
    next_start = data.find(b"\n## RUNTIME MODULE: ", start + len(marker))
    end = len(data) if next_start < 0 else next_start + 1
    return data[start:end], start, end


def module_section(data: bytes, module_id: str) -> bytes:
    return module_section_span(data, module_id)[0]


def _json(root: Path, relative: str) -> dict[str, Any]:
    try:
        value = json.loads(read_package_bytes(root, relative))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ResolutionError(f"invalid package JSON: {relative}") from exc
    if not isinstance(value, dict):
        raise ResolutionError(f"package JSON must be an object: {relative}")
    return value


def _component(component_id: str, kind: str, path: str, data: bytes, slice_kind: str = "whole-file", start: int = 0, end: int = 0) -> dict[str, Any]:
    return {"component_id": component_id, "kind": kind, "source_path": path,
            "source_slice": {"kind": slice_kind, "start": start, "end": end},
            "sha256": sha256_bytes(data), "byte_count": len(data), "bytes": data}


def resolve_context(
    package_root: Path,
    stage: str,
    validated_state: dict[str, Any],
    previous_capsule: bytes | None,
    candidate_cap: int = 4,
    raw_input: bytes | None = None,
) -> dict[str, Any]:
    root = package_root.resolve(strict=True)
    if stage not in STAGE_MANDATORY:
        raise ResolutionError(f"unsupported model stage: {stage}")
    mandatory_ids = [f"package:{path}" for path in STAGE_MANDATORY[stage]]
    route_paths = list(dict.fromkeys(validated_state.get("route_shards", [])))
    route_ids = [f"package:{path}" for path in route_paths]
    owner_ids = [f"owner:{module_id}" for module_id in validated_state.get("owner_module_ids", [])]
    cold_ids = list(validated_state.get("cold_clause_ids", []))
    transport_ids = ["raw-input"] if stage == "01" else ["state-capsule"]
    candidate_ids = transport_ids + list(dict.fromkeys(mandatory_ids + route_ids + owner_ids + cold_ids))
    if stage == "01" and raw_input is None:
        return {"status": "HOLD", "hold_reason": "raw-input-missing", "components": [],
                "candidate_components": candidate_ids, "selected_components": []}
    if stage != "01" and previous_capsule is None:
        return {"status": "HOLD", "hold_reason": "previous-capsule-missing", "components": [],
                "candidate_components": candidate_ids, "selected_components": []}

    components: list[dict[str, Any]] = []
    if raw_input is not None and stage == "01":
        components.append(_component("raw-input", "raw-input", "transport://raw-input", raw_input))
    if previous_capsule is not None:
        components.append(_component("state-capsule", "state-capsule", "transport://previous-capsule", previous_capsule))

    candidates = list(dict.fromkeys(STAGE_MANDATORY[stage] + route_paths))
    ambiguous = bool(validated_state.get("ambiguous"))
    if ambiguous and len(route_paths) > candidate_cap:
        return {"status": "HOLD", "hold_reason": "route-ambiguous-over-cap", "components": components,
                "candidate_components": candidate_ids, "selected_components": []}

    for rel in candidates:
        data = read_package_bytes(root, rel)
        kind = "kernel" if rel == "SKILL.md" else "route-shard"
        components.append(_component(f"package:{rel}", kind, rel, data))

    module_map = _json(root, "compiled-module-map.json")
    modules = module_map.get("modules", {})
    for module_id in validated_state.get("owner_module_ids", []):
        row = modules.get(module_id)
        if not isinstance(row, dict) or not isinstance(row.get("bundle_path"), str):
            return {"status": "HOLD", "hold_reason": f"owner-module-unavailable:{module_id}", "components": components,
                    "candidate_components": candidate_ids, "selected_components": []}
        rel = row["bundle_path"]
        section, start, end = module_section_span(read_package_bytes(root, rel), module_id)
        components.append(_component(f"owner:{module_id}", "owner-module", rel, section, "bytes", start, end))

    cold = _json(root, "cold-law-manifest.json")
    cold_source = "references/rubrics/non-droppable-manual-contract.md"
    source_bytes = read_package_bytes(root, cold_source)
    clauses = cold.get("clauses", {})
    for clause_id in validated_state.get("cold_clause_ids", []):
        row = clauses.get(clause_id)
        span = row.get("span_lines") if isinstance(row, dict) else None
        if not isinstance(span, list) or len(span) != 2:
            return {"status": "HOLD", "hold_reason": f"cold-law-unavailable:{clause_id}", "components": components,
                    "candidate_components": candidate_ids, "selected_components": []}
        clause = exact_line_slice(source_bytes, int(span[0]), int(span[1]))
        if sha256_bytes(clause) != row.get("sha256"):
            raise ResolutionError(f"cold clause hash mismatch: {clause_id}")
        components.append(_component(clause_id, "cold-law-clause", cold_source, clause, "lines", int(span[0]), int(span[1])))

    semantic_components = [item for item in components if item["kind"] not in {"raw-input", "state-capsule"}]
    if validated_state.get("live_pressure") and not semantic_components:
        return {"status": "HOLD", "hold_reason": "live-pressure-without-semantic-context", "components": components,
                "candidate_components": candidate_ids, "selected_components": []}
    return {"status": "selected", "hold_reason": None, "components": components,
            "candidate_components": candidate_ids, "selected_components": [x["component_id"] for x in components]}


def _public(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _public(v) for k, v in value.items() if k != "bytes"}
    if isinstance(value, list):
        return [_public(v) for v in value]
    return value


def self_test() -> int:
    root = Path(__file__).resolve().parents[1] / "skill"
    checks: list[tuple[str, bool]] = []
    state = {"route_shards": [], "owner_module_ids": [], "cold_clause_ids": [], "live_pressure": False, "ambiguous": False}
    a = resolve_context(root, "03", state, b'{"capsule":2}')
    b = resolve_context(root, "03", {**state, "case_id": "changed", "topic": "changed"}, b'{"capsule":2}')
    checks.append(("case and topic taint do not affect selection", _public(a) == _public(b)))
    checks.append(("stage03 selects routing plus prior capsule", len(a["components"]) == 2 and a["status"] == "selected"))
    hold = resolve_context(root, "03", {**state, "ambiguous": True, "route_shards": [f"references/x{i}.md" for i in range(5)]}, b"{}", 4)
    checks.append(("over-cap ambiguity holds before reading candidates", hold["status"] == "HOLD"))
    owner = resolve_context(root, "04", {**state, "owner_module_ids": ["M1-self-refutation"]}, b"{}")
    checks.append(("owner resolves to exact omnibus section", any(x["kind"] == "owner-module" for x in owner["components"])))
    owner_component = next(x for x in owner["components"] if x["kind"] == "owner-module")
    owner_source = read_package_bytes(root, owner_component["source_path"])
    owner_slice = owner_source[owner_component["source_slice"]["start"]:owner_component["source_slice"]["end"]]
    checks.append(("owner slice coordinates reproduce selected bytes", sha256_bytes(owner_slice) == owner_component["sha256"]))
    cold = resolve_context(root, "04", {**state, "cold_clause_ids": ["clause.execution-mandate-detail"]}, b"{}")
    checks.append(("cold clause resolves exact manifest span", any(x["kind"] == "cold-law-clause" for x in cold["components"])))
    raw = b"case-agnostic raw input bytes\n"
    bootstrap = resolve_context(root, "01", state, None, raw_input=raw)
    raw_component = next((x for x in bootstrap["components"] if x["kind"] == "raw-input"), None)
    checks.append(("stage01 transports exact raw input bytes", raw_component is not None and raw_component["bytes"] == raw and raw_component["sha256"] == sha256_bytes(raw)))
    ok = all(v for _, v in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"runtime context resolver self-test: {'PASS' if ok else 'FAIL'} ({sum(v for _, v in checks)}/{len(checks)})")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--package-root", type=Path)
    parser.add_argument("--stage")
    parser.add_argument("--state", type=Path)
    parser.add_argument("--previous-capsule", type=Path)
    parser.add_argument("--raw-input", type=Path)
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.package_root or not args.stage or not args.state:
        parser.error("--package-root, --stage, and --state are required")
    state = json.loads(args.state.read_text(encoding="utf-8"))
    capsule = args.previous_capsule.read_bytes() if args.previous_capsule else None
    raw_input = args.raw_input.read_bytes() if args.raw_input else None
    print(json.dumps(_public(resolve_context(args.package_root, args.stage, state, capsule, raw_input=raw_input)), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
