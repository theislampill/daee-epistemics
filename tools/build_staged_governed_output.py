#!/usr/bin/env python3
"""Assemble a staged governed output from hash-checked section artifacts.

This is repo/dev tooling for Brandolini-safe staged output construction. It
does not author reasoning, run validators, build sidecars, or promote retained
proof. It only compiles an output from bounded sections after checking the
assembly manifest, paths, hashes, section order, and public-output non-claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Callable


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
ASSEMBLY_SCHEMA = "staged-governed-output-assembly-v1"
HASH_RECORD_SCHEMA = "staged-governed-output-assembly-hashes-v1"
REQUIRED_NON_CLAIMS = {
    "not_release_provenance",
    "not_model_behavior_by_itself",
    "not_sidecar_proof",
}
ROLE_ORDER = [
    "visible_opening",
    "layer_a",
    "act_body",
    "mrp",
    "field_witness",
    "restorative_response",
]
ROLE_INDEX = {role: index for index, role in enumerate(ROLE_ORDER)}
SINGLETON_ROLES = {
    "visible_opening",
    "layer_a",
    "mrp",
    "field_witness",
    "restorative_response",
}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "harness commentary",
        re.compile(
            r"You are executing stage-|Validated compact stage state|Return exactly one JSON object|"
            r"assembly manifest|staged-governed-output-assembly-v1|compiler note|repo/dev scratch",
            re.IGNORECASE,
        ),
    ),
    (
        "package/provenance/release claim",
        re.compile(
            r"GitHub Release|release asset|release package|package provenance|published provenance|"
            r"provenance (?:asset|publication|proof)|\.skill archive",
            re.IGNORECASE,
        ),
    ),
    (
        "guaranteed T_lang uptake claim",
        re.compile(
            r"T_lang\s+guarantees|guarantees\s+interlocutor\s+uptake|guarantees\s+uptake",
            re.IGNORECASE,
        ),
    ),
    (
        "sidecar proof claim before Stage 8",
        re.compile(
            r"Stage\s*8[^.\n]{0,80}\b(?:pass|passed|proof)\b|"
            r"\bsidecar[^.\n]{0,80}\b(?:proves|proof|passed|built)\b|"
            r"\bcollapse certificate[^.\n]{0,80}\b(?:proves|passed)\b|"
            r"\bGrapher[^.\n]{0,80}\bproof\b",
            re.IGNORECASE,
        ),
    ),
]


class AssemblyError(Exception):
    """Raised when a staged output assembly manifest is unsafe or invalid."""


def rel(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssemblyError(f"{rel(path)}: invalid JSON: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def require_under_root(root: Path, path: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise AssemblyError(f"{label}: path escapes root: {path}") from exc
    return resolved


def reject_unsafe_relative(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise AssemblyError(f"{label}: must be a non-empty relative path string")
    path = Path(value)
    if path.is_absolute():
        raise AssemblyError(f"{label}: absolute paths are not allowed")
    if any(part == ".." for part in path.parts):
        raise AssemblyError(f"{label}: '..' path components are not allowed")
    return path


def resolve_section_path(root: Path, manifest_dir: Path, value: Any, label: str) -> Path:
    relative = reject_unsafe_relative(value, label)
    manifest_candidate = require_under_root(root, manifest_dir / relative, label)
    root_candidate = require_under_root(root, root / relative, label)
    chosen = manifest_candidate if manifest_candidate.exists() else root_candidate
    if not chosen.exists():
        raise AssemblyError(f"{label}: section path does not exist: {value}")
    if not chosen.is_file():
        raise AssemblyError(f"{label}: section path must be a file: {value}")
    return chosen


def resolve_output_path(root: Path, manifest_dir: Path, value: Any, label: str) -> Path:
    relative = reject_unsafe_relative(value, label)
    return require_under_root(root, manifest_dir / relative, label)


def forbidden_text_errors(text: str, label: str) -> list[str]:
    return [f"{label}: forbidden {name}" for name, pattern in FORBIDDEN_PATTERNS if pattern.search(text)]


def validate_non_claims(non_claims: Any) -> list[str]:
    if not isinstance(non_claims, dict):
        return ["non_claims: must be an object"]
    return [
        f"non_claims.{key}: must be true"
        for key in sorted(REQUIRED_NON_CLAIMS)
        if non_claims.get(key) is not True
    ]


def section_payload_errors(section: Any, index: int) -> list[str]:
    label = f"sections[{index}]"
    if not isinstance(section, dict):
        return [f"{label}: must be an object"]
    errors: list[str] = []
    for key in ("id", "path", "sha256", "role"):
        if not isinstance(section.get(key), str) or not section[key].strip():
            errors.append(f"{label}.{key}: must be a non-empty string")
    role = section.get("role")
    if isinstance(role, str) and role not in ROLE_INDEX:
        errors.append(f"{label}.role: unsupported role {role!r}")
    expected_hash = section.get("sha256")
    if isinstance(expected_hash, str) and not SHA256_RE.match(expected_hash):
        errors.append(f"{label}.sha256: must be a SHA-256 hex digest")
    return errors


def assemble_manifest(manifest_path: Path, *, root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = require_under_root(root, manifest_path, "manifest")
    manifest_dir = manifest_path.parent
    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        raise AssemblyError(f"{rel(manifest_path, root)}: manifest root must be an object")

    errors: list[str] = []
    if payload.get("schema") != ASSEMBLY_SCHEMA:
        errors.append(f"schema: must be {ASSEMBLY_SCHEMA!r}")
    if not isinstance(payload.get("case_id"), str) or not payload["case_id"].strip():
        errors.append("case_id: must be a non-empty string")
    errors.extend(validate_non_claims(payload.get("non_claims")))

    output = payload.get("output")
    if not isinstance(output, dict):
        errors.append("output: must be an object")
        output_path = manifest_dir / "output.md"
    else:
        try:
            output_path = resolve_output_path(root, manifest_dir, output.get("path"), "output.path")
        except AssemblyError as exc:
            errors.append(str(exc))
            output_path = manifest_dir / "output.md"

    sections = payload.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("sections: must be a non-empty list")
        sections = []

    section_texts: list[str] = []
    section_records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    role_counts: dict[str, int] = {role: 0 for role in ROLE_ORDER}
    previous_role_index = -1

    for index, section in enumerate(sections):
        label = f"sections[{index}]"
        found = section_payload_errors(section, index)
        errors.extend(found)
        if found:
            continue

        assert isinstance(section, dict)
        section_id = str(section["id"])
        role = str(section["role"])
        if section_id in seen_ids:
            errors.append(f"{label}.id: duplicate section id {section_id!r}")
        seen_ids.add(section_id)

        role_index = ROLE_INDEX[role]
        if role_index < previous_role_index:
            errors.append(f"{label}.role: role {role!r} is out of order")
        previous_role_index = role_index
        role_counts[role] += 1

        try:
            section_path = resolve_section_path(root, manifest_dir, section["path"], f"{label}.path")
        except AssemblyError as exc:
            errors.append(str(exc))
            continue

        expected_hash = str(section["sha256"]).upper()
        actual_hash = sha256_file(section_path)
        if expected_hash != actual_hash:
            errors.append(f"{label}.sha256: expected {expected_hash} but found {actual_hash}")
        text = section_path.read_text(encoding="utf-8", errors="replace")
        errors.extend(forbidden_text_errors(text, label))
        section_texts.append(text)
        section_records.append(
            {
                "id": section_id,
                "role": role,
                "path": rel(section_path, root),
                "sha256": actual_hash,
                "bytes": len(text.encode("utf-8")),
            }
        )

    missing_roles = [role for role in ROLE_ORDER if role_counts.get(role, 0) == 0]
    if missing_roles:
        errors.append(f"sections: missing required role(s): {missing_roles}")
    duplicate_singletons = [role for role in sorted(SINGLETON_ROLES) if role_counts.get(role, 0) > 1]
    if duplicate_singletons:
        errors.append(f"sections: singleton role(s) repeated: {duplicate_singletons}")

    assembled = ""
    for text in section_texts:
        if assembled and not assembled.endswith("\n"):
            assembled += "\n"
        assembled += text
        if not assembled.endswith("\n"):
            assembled += "\n"
    errors.extend(forbidden_text_errors(assembled, "assembled output"))

    if errors:
        raise AssemblyError("\n- ".join(["staged governed output assembly failed:", *errors]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(assembled, encoding="utf-8", newline="\n")
    output_hash = sha256_file(output_path)
    hash_record_path = output_path.with_suffix(output_path.suffix + ".assembly.hashes.json")
    record = {
        "schema": HASH_RECORD_SCHEMA,
        "assembly_manifest": {"path": rel(manifest_path, root), "sha256": sha256_file(manifest_path)},
        "case_id": payload["case_id"],
        "source_input": payload.get("source_input"),
        "output": {
            "path": rel(output_path, root),
            "sha256": output_hash,
            "bytes": output_path.stat().st_size,
        },
        "sections": section_records,
        "non_claims": {key: payload["non_claims"].get(key) for key in sorted(REQUIRED_NON_CLAIMS)},
    }
    write_json(hash_record_path, record)
    record["hash_record"] = {"path": rel(hash_record_path, root), "sha256": sha256_file(hash_record_path)}
    write_json(hash_record_path, record)
    return record


def manifest_for_sections(
    case_dir: Path,
    *,
    case_id: str,
    source_input: str,
    section_specs: list[tuple[str, str, str]],
    output_name: str = "output.md",
) -> Path:
    sections_dir = case_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    sections_payload: list[dict[str, str]] = []
    for index, (section_id, role, text) in enumerate(section_specs):
        path = sections_dir / f"{index:02d}-{section_id}.md"
        path.write_text(text, encoding="utf-8", newline="\n")
        sections_payload.append(
            {
                "id": section_id,
                "path": path.relative_to(case_dir).as_posix(),
                "sha256": sha256_file(path),
                "role": role,
            }
        )
    manifest_path = case_dir / "assembly.manifest.json"
    write_json(
        manifest_path,
        {
            "schema": ASSEMBLY_SCHEMA,
            "case_id": case_id,
            "source_input": source_input,
            "sections": sections_payload,
            "output": {"path": output_name},
            "non_claims": {
                "not_release_provenance": True,
                "not_model_behavior_by_itself": True,
                "not_sidecar_proof": True,
            },
        },
    )
    return manifest_path


def small_sections(*, act_text: str = "Layer B ACT body_ref=B1.s1.\nLand(B1): landed.\n") -> list[tuple[str, str, str]]:
    return [
        ("opening", "visible_opening", "NOETIC FIELD EXECUTION\nCase opening preserved.\n"),
        ("layer-a", "layer_a", "Layer A / Diagnostic IR Header\nN: source-order.\n"),
        ("act-body", "act_body", act_text),
        ("mrp", "mrp", "MRP(B1): terminal reread.\nR(H,Delta): neutral.\n"),
        (
            "field-witness",
            "field_witness",
            "field_witness\ncoverage_proof: divergence_check=neutral; curl_check=null.\nNAR: B1 landed.\n",
        ),
        ("release", "restorative_response", "Restorative Response\nClosing Formulation\n"),
    ]


def expect_invalid(
    root: Path,
    base_dir: Path,
    name: str,
    mutate: Callable[[dict[str, Any], Path], None],
) -> None:
    case_dir = base_dir / name
    manifest_path = manifest_for_sections(
        case_dir,
        case_id=name,
        source_input=f"{name}/input.md",
        section_specs=small_sections(),
    )
    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        raise AssertionError("self-test manifest payload must be an object")
    mutate(payload, case_dir)
    write_json(manifest_path, payload)
    try:
        assemble_manifest(manifest_path, root=root)
    except AssemblyError:
        return
    raise AssemblyError(f"self-test expected invalid assembly to fail: {name}")


def replace_section_text(payload: dict[str, Any], case_dir: Path, index: int, text: str) -> None:
    path = case_dir / payload["sections"][index]["path"]
    path.write_text(text, encoding="utf-8", newline="\n")
    payload["sections"][index]["sha256"] = sha256_file(path)


def run_self_test(root: Path) -> int:
    base_dir = root / ".daee" / "validation" / f"staged-governed-output-assembly-self-test-{uuid.uuid4().hex}"
    base_dir.mkdir(parents=True, exist_ok=True)

    small_manifest = manifest_for_sections(
        base_dir / "valid-small",
        case_id="valid-small",
        source_input="valid-small/input.md",
        section_specs=small_sections(),
    )
    small_record = assemble_manifest(small_manifest, root=root)
    if small_record["output"]["bytes"] <= 0:
        raise AssemblyError("self-test valid small assembly wrote an empty output")

    large_act_chunks = [
        (
            f"act-body-{index}",
            "act_body",
            ("Layer B ACT body_ref=B1.s%s.\nOperation: bounded section work.\nLand(B1): landed.\n" % index) * 900,
        )
        for index in range(1, 5)
    ]
    large_manifest = manifest_for_sections(
        base_dir / "valid-large",
        case_id="valid-large",
        source_input="valid-large/input.md",
        section_specs=[
            *small_sections(act_text="Layer B opening ACT body_ref=B1.s0.\nLand(B1): landed.\n")[:2],
            *large_act_chunks,
            *small_sections()[3:],
        ],
    )
    large_record = assemble_manifest(large_manifest, root=root)
    if large_record["output"]["bytes"] < 200 * 1024:
        raise AssemblyError("self-test valid large assembly did not reach 200KB")

    expect_invalid(
        root,
        base_dir,
        "invalid-missing-section",
        lambda payload, _case_dir: payload.__setitem__(
            "sections", [section for section in payload["sections"] if section["role"] != "mrp"]
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-hash-mismatch",
        lambda payload, _case_dir: payload["sections"][0].__setitem__("sha256", "0" * 64),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-out-of-order",
        lambda payload, _case_dir: payload.__setitem__(
            "sections", [payload["sections"][4], *payload["sections"][:4], payload["sections"][5]]
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-path-escape",
        lambda payload, _case_dir: payload["sections"][0].__setitem__("path", "../escape.md"),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-harness-commentary",
        lambda payload, case_dir: replace_section_text(
            payload, case_dir, 0, "You are executing stage-07-release-output.\n"
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-package-provenance-claim",
        lambda payload, case_dir: replace_section_text(
            payload, case_dir, 5, "This publishes provenance in a GitHub Release.\n"
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-guaranteed-uptake-claim",
        lambda payload, case_dir: replace_section_text(
            payload, case_dir, 5, "T_lang guarantees interlocutor uptake.\n"
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-sidecar-proof-claim",
        lambda payload, case_dir: replace_section_text(payload, case_dir, 5, "Stage 8 sidecar proof PASS.\n"),
    )
    print("staged governed output assembly self-test: PASS")
    print(f"self-test run dir: {rel(base_dir, root)}")
    print(f"large output bytes: {large_record['output']['bytes']}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if args.self_test:
        return run_self_test(root)
    if args.manifest is None:
        raise SystemExit("--manifest is required unless --self-test is used")
    record = assemble_manifest(args.manifest, root=root)
    print("staged governed output assembly: PASS")
    print(f"output: {record['output']['path']}")
    print(f"output sha256: {record['output']['sha256']}")
    print(f"output bytes: {record['output']['bytes']}")
    print(f"hash record: {record['hash_record']['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
