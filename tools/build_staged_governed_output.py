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
ACT_PARTITION_SCHEMA = "staged-act-partition-v1"
REQUIRED_NON_CLAIMS = {
    "not_release_provenance",
    "not_model_behavior_by_itself",
    "not_sidecar_proof",
}
ROLE_ORDER = [
    "visible_opening",
    "layer_a_diagnostic_ir",
    "layer_b_act",
    "mrp_reread_terminal",
    "field_witness_nar",
    "restorative_response",
    "closing_formulation",
]
ROLE_INDEX = {role: index for index, role in enumerate(ROLE_ORDER)}
SINGLETON_ROLES = {
    "visible_opening",
    "layer_a_diagnostic_ir",
    "mrp_reread_terminal",
    "field_witness_nar",
    "restorative_response",
    "closing_formulation",
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
    (
        "Graphify/ActiveGraph proof claim",
        re.compile(r"Graphify[^.\n]{0,80}\bproof\b|ActiveGraph[^.\n]{0,80}\bproof\b", re.IGNORECASE),
    ),
]
SURFACE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("visible noetic-field opening/header", re.compile(r"NOETIC FIELD EXECUTION|noetic-field", re.IGNORECASE)),
    (
        "compact Layer A / Diagnostic IR header",
        re.compile(r"Layer A\b.*(?:DSL/IR|Diagnostic IR|Header)", re.IGNORECASE | re.DOTALL),
    ),
    (
        "Layer A initial burden ledger",
        re.compile(r"Initial burden set\b.*B[_ -]?LA|B[_ -]?LA\b.*Initial burden set", re.IGNORECASE | re.DOTALL),
    ),
    ("governed Layer B / ACT surface", re.compile(r"Layer B\b.*(?:ACT|Bounded Governed Response)", re.IGNORECASE | re.DOTALL)),
    ("ACT body_ref tokens", re.compile(r"\bbody_ref=", re.IGNORECASE)),
    ("Land surface", re.compile(r"Land\(", re.IGNORECASE)),
    (
        "MRP / reread / terminal-state surface",
        re.compile(r"(?:\[Mid-Reread Pressure\]|MRP\(|R\(H,|Terminal states|MRP route result type)", re.IGNORECASE),
    ),
    (
        "parser-stable field_witness surface",
        re.compile(r"(?im)^\s*(?:#+\s*)?field_witness\b"),
    ),
    (
        "normalized_activation_record / NAR evidence",
        re.compile(r"normalized_activation_record|\bNAR\b", re.IGNORECASE),
    ),
    ("Closure/Reconstruction Witness", re.compile(r"Closure/Reconstruction Witness", re.IGNORECASE)),
    ("Restorative Response", re.compile(r"(?im)^\s*(?:#+\s*)?Restorative Response\b")),
    ("Closing Formulation", re.compile(r"(?im)^\s*(?:#+\s*)?Closing Formulation\b")),
]
BODY_REF_TOKEN_RE = re.compile(r"\bbody_ref=([^\s:⟧]+)")


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


def required_surface_errors(text: str) -> list[str]:
    return [
        f"assembled output: missing {label}"
        for label, pattern in SURFACE_PATTERNS
        if pattern.search(text) is None
    ]


def parse_output_targets(output: Any) -> tuple[int, int, list[str]]:
    if not isinstance(output, dict):
        return 0, 0, []
    errors: list[str] = []
    target_output_kb = output.get("target_output_kb", 0)
    target_min_bytes = output.get("target_min_bytes", 0)
    if target_output_kb in (None, ""):
        target_output_kb = 0
    if target_min_bytes in (None, ""):
        target_min_bytes = 0
    if not isinstance(target_output_kb, int) or target_output_kb < 0:
        errors.append("output.target_output_kb: must be a non-negative integer")
        target_output_kb = 0
    if not isinstance(target_min_bytes, int) or target_min_bytes < 0:
        errors.append("output.target_min_bytes: must be a non-negative integer")
        target_min_bytes = 0
    min_bytes = max(target_min_bytes, target_output_kb * 1024)
    return target_output_kb, min_bytes, errors


def validate_non_claims(non_claims: Any) -> list[str]:
    if not isinstance(non_claims, dict):
        return ["non_claims: must be an object"]
    return [
        f"non_claims.{key}: must be true"
        for key in sorted(REQUIRED_NON_CLAIMS)
        if non_claims.get(key) is not True
    ]


def clean_body_ref(value: str) -> str:
    return value.strip().rstrip(".,;")


def body_refs_in_act_section(text: str) -> list[str]:
    refs: list[str] = []
    for match in BODY_REF_TOKEN_RE.finditer(text):
        ref = clean_body_ref(match.group(1))
        if ref:
            refs.append(ref)
    return refs


def act_partition_errors(
    partition: Any,
    *,
    section_text_by_id: dict[str, str],
    section_role_by_id: dict[str, str],
) -> list[str]:
    if partition is None:
        return []
    if not isinstance(partition, dict):
        return ["act_partition: must be an object"]

    errors: list[str] = []
    if partition.get("schema") != ACT_PARTITION_SCHEMA:
        errors.append(f"act_partition.schema: must be {ACT_PARTITION_SCHEMA!r}")
    if partition.get("no_duplicate_body_refs") is not True:
        errors.append("act_partition.no_duplicate_body_refs: must be true")
    if partition.get("all_assigned_refs_present") is not True:
        errors.append("act_partition.all_assigned_refs_present: must be true")

    raw_assignments = partition.get("assignments")
    if not isinstance(raw_assignments, list) or not raw_assignments:
        return errors + ["act_partition.assignments: must be a non-empty list"]

    assignments: dict[str, list[str]] = {}
    assigned_owner: dict[str, str] = {}
    for index, raw in enumerate(raw_assignments):
        label = f"act_partition.assignments[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{label}: must be an object")
            continue
        section_id = raw.get("section_id")
        if not isinstance(section_id, str) or not section_id.strip():
            errors.append(f"{label}.section_id: must be a non-empty string")
            continue
        section_id = section_id.strip()
        if section_id not in section_text_by_id:
            errors.append(f"{label}.section_id: unknown section {section_id!r}")
        elif section_role_by_id.get(section_id) != "layer_b_act":
            errors.append(f"{label}.section_id: section {section_id!r} is not a layer_b_act section")

        body_refs = raw.get("body_refs")
        if not isinstance(body_refs, list) or not all(isinstance(item, str) and item.strip() for item in body_refs):
            errors.append(f"{label}.body_refs: must be a list of non-empty strings")
            continue
        cleaned_refs = [clean_body_ref(item) for item in body_refs]
        if len(cleaned_refs) != len(set(cleaned_refs)):
            errors.append(f"{label}.body_refs: duplicate body_ref assignment inside section")
        assignments[section_id] = cleaned_refs
        for ref in cleaned_refs:
            previous = assigned_owner.get(ref)
            if previous and previous != section_id:
                errors.append(f"act_partition.assignments: body_ref {ref!r} assigned to both {previous!r} and {section_id!r}")
            assigned_owner[ref] = section_id

    layer_b_sections = [section_id for section_id, role in section_role_by_id.items() if role == "layer_b_act"]
    for section_id in layer_b_sections:
        if section_id not in assignments:
            errors.append(f"act_partition.assignments: missing layer_b_act section {section_id!r}")

    visible_refs_by_section: dict[str, list[str]] = {}
    all_visible_refs: list[str] = []
    for section_id in layer_b_sections:
        visible_refs = body_refs_in_act_section(section_text_by_id.get(section_id, ""))
        visible_refs_by_section[section_id] = visible_refs
        all_visible_refs.extend(visible_refs)
        assigned = set(assignments.get(section_id, []))
        extra = sorted({ref for ref in visible_refs if ref not in assigned})
        if extra:
            errors.append(f"act_partition.{section_id}: unassigned body_ref(s) emitted: {extra}")
        missing = sorted(ref for ref in assignments.get(section_id, []) if ref not in visible_refs)
        if missing:
            errors.append(f"act_partition.{section_id}: assigned body_ref(s) missing from section: {missing}")
        if len(visible_refs) != len(set(visible_refs)):
            errors.append(f"act_partition.{section_id}: duplicate visible ACT body_ref inside section")

    if len(all_visible_refs) != len(set(all_visible_refs)):
        duplicates = sorted({ref for ref in all_visible_refs if all_visible_refs.count(ref) > 1})
        errors.append(f"act_partition: duplicate visible ACT body_ref(s) across sections: {duplicates}")

    assigned_refs = set(assigned_owner)
    unassigned_visible = sorted(ref for ref in set(all_visible_refs) if ref not in assigned_refs)
    if unassigned_visible:
        errors.append(f"act_partition: visible ACT body_ref(s) not assigned: {unassigned_visible}")
    missing_visible = sorted(ref for ref in assigned_refs if ref not in set(all_visible_refs))
    if missing_visible:
        errors.append(f"act_partition: assigned body_ref(s) not present in visible ACT output: {missing_visible}")
    return errors


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


def assemble_manifest(manifest_path: Path, *, root: Path = ROOT, allow_under_target: bool = False) -> dict[str, Any]:
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
    target_output_kb = 0
    target_min_bytes = 0
    if not isinstance(output, dict):
        errors.append("output: must be an object")
        output_path = manifest_dir / "output.md"
    else:
        target_output_kb, target_min_bytes, target_errors = parse_output_targets(output)
        errors.extend(target_errors)
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
    section_text_by_id: dict[str, str] = {}
    section_role_by_id: dict[str, str] = {}
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
        section_text_by_id[section_id] = text
        section_role_by_id[section_id] = role
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
    errors.extend(required_surface_errors(assembled))
    errors.extend(
        act_partition_errors(
            payload.get("act_partition"),
            section_text_by_id=section_text_by_id,
            section_role_by_id=section_role_by_id,
        )
    )
    assembled_bytes = len(assembled.encode("utf-8"))
    if target_min_bytes and assembled_bytes < target_min_bytes and not allow_under_target:
        errors.append(
            "assembled output: under target size "
            f"({assembled_bytes} bytes < {target_min_bytes} bytes)"
        )

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
            "target_output_kb": target_output_kb,
            "target_min_bytes": target_min_bytes,
            "under_target_allowed": allow_under_target,
        },
        "sections": section_records,
        "non_claims": {key: payload["non_claims"].get(key) for key in sorted(REQUIRED_NON_CLAIMS)},
    }
    if payload.get("act_partition") is not None:
        record["act_partition"] = payload["act_partition"]
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
    target_output_kb: int = 0,
    act_partition: dict[str, Any] | None = None,
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
    payload: dict[str, Any] = {
        "schema": ASSEMBLY_SCHEMA,
        "case_id": case_id,
        "source_input": source_input,
        "sections": sections_payload,
        "output": {"path": output_name, "target_output_kb": target_output_kb},
        "non_claims": {
            "not_release_provenance": True,
            "not_model_behavior_by_itself": True,
            "not_sidecar_proof": True,
        },
    }
    if act_partition is not None:
        payload["act_partition"] = act_partition
    write_json(manifest_path, payload)
    return manifest_path


def small_sections(*, act_text: str = "Layer B - Bounded Governed Response\nACT row body_ref=B1.s1.\nLand(B1): landed.\n") -> list[tuple[str, str, str]]:
    return [
        ("opening", "visible_opening", "NOETIC FIELD EXECUTION\nCase opening preserved.\n"),
        (
            "layer-a",
            "layer_a_diagnostic_ir",
            "Layer A - Compact DSL/IR Header\n"
            "- B_LA (B_LA) = {B1}\n"
            "- B_MRP (B_MRP) = {}\n"
            "- B_total (B_total) = B_LA union B_MRP\n"
            "- Initial burden set: [B1]\n",
        ),
        ("act-body", "layer_b_act", act_text),
        (
            "mrp",
            "mrp_reread_terminal",
            "[Mid-Reread Pressure]\n"
            "Target: B1\n"
            "R(H,Delta): held routes rechecked: none; live remainder: none; release/next: closure.\n"
            "MRP route result type: no_new_resultant\n"
            "Terminal states: B1=landed.\n"
            "Field diagnostics: del-dot-B: neutral; del-cross-kappa: null.\n"
        ),
        (
            "field-witness",
            "field_witness_nar",
            "Closure/Reconstruction Witness\n"
            "field_witness\n"
            "{\n"
            "  \"B_LA\": [\"B1\"],\n"
            "  \"B_MRP\": [],\n"
            "  \"B_total\": [\"B1\"],\n"
            "  \"coverage_proof\": {\n"
            "    \"divergence_check\": \"neutral\",\n"
            "    \"curl_check\": \"null\"\n"
            "  },\n"
            "  \"normalized_activation_record\": {\n"
            "    \"n_frame\": \"self-test\",\n"
            "    \"live_registers\": [\"xi\"],\n"
            "    \"burden_floor\": [\"B1\"],\n"
            "    \"per_burden\": []\n"
            "  }\n"
            "}\n",
        ),
        ("release", "restorative_response", "Restorative Response\nRestored orientation.\n"),
        ("closing", "closing_formulation", "Closing Formulation\nScoped boundary.\n"),
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


def act_partition_payload(assignments: list[tuple[str, list[str]]]) -> dict[str, Any]:
    return {
        "schema": ACT_PARTITION_SCHEMA,
        "assignments": [
            {"section_id": section_id, "body_refs": body_refs}
            for section_id, body_refs in assignments
        ],
        "no_duplicate_body_refs": True,
        "all_assigned_refs_present": True,
    }


def act_section(section_id: str, *body_refs: str) -> tuple[str, str, str]:
    rows = [
        f"⟦ACT {body_ref}[M9.repair] :: π=predicate-transfer :: "
        f"body_ref={body_ref} :: Δ=ΔB1:predicate-transfer-blocked :: Land(B1)+⟧"
        for body_ref in body_refs
    ]
    return (
        section_id,
        "layer_b_act",
        "Layer B - Bounded Governed Response\nACT records:\n" + "\n".join(rows) + "\nLand(B1): landed.\n",
    )


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
            "layer_b_act",
            ("Layer B - Bounded Governed Response\nACT body_ref=B1.s%s.\nOperation: bounded section work.\nLand(B1): landed.\n" % index) * 900,
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
        target_output_kb=200,
    )
    large_record = assemble_manifest(large_manifest, root=root)
    if large_record["output"]["bytes"] < 200 * 1024:
        raise AssemblyError("self-test valid large assembly did not reach 200KB")

    valid_100kb_manifest = manifest_for_sections(
        base_dir / "valid-100kb",
        case_id="valid-100kb",
        source_input="valid-100kb/input.md",
        section_specs=[
            *small_sections(act_text="Layer B - Bounded Governed Response\nACT body_ref=B1.s0.\nLand(B1): landed.\n")[:2],
            *large_act_chunks[:2],
            *small_sections()[3:],
        ],
        target_output_kb=100,
    )
    valid_100kb_record = assemble_manifest(valid_100kb_manifest, root=root)
    if valid_100kb_record["output"]["bytes"] < 100 * 1024:
        raise AssemblyError("self-test valid 100KB assembly did not reach 100KB")

    def assemble_partition_case(
        name: str,
        act_sections: list[tuple[str, str, str]],
        assignments: list[tuple[str, list[str]]],
        *,
        valid: bool,
    ) -> None:
        manifest = manifest_for_sections(
            base_dir / name,
            case_id=name,
            source_input=f"{name}/input.md",
            section_specs=[*small_sections()[:2], *act_sections, *small_sections()[3:]],
            act_partition=act_partition_payload(assignments),
        )
        try:
            assemble_manifest(manifest, root=root)
        except AssemblyError:
            if valid:
                raise
            return
        if not valid:
            raise AssemblyError(f"self-test expected invalid ACT partition to fail: {name}")

    assemble_partition_case(
        "valid-act-partition-disjoint",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", "B1_2")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_2"])],
        valid=True,
    )
    assemble_partition_case(
        "valid-act-partition-declared-generated",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", "B2_1")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B2_1"])],
        valid=True,
    )
    assemble_partition_case(
        "invalid-act-partition-duplicate-visible",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", "B1_1")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_1"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-missing-assigned",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_2"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-unassigned-visible",
        [act_section("act-body-1", "B1_1"), act_section("act-body-2", "B1_2")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B2_1"])],
        valid=False,
    )
    assemble_partition_case(
        "invalid-act-partition-section-emits-all-rows",
        [act_section("act-body-1", "B1_1", "B1_2"), act_section("act-body-2", "B1_2")],
        [("act-body-1", ["B1_1"]), ("act-body-2", ["B1_2"])],
        valid=False,
    )

    expect_invalid(
        root,
        base_dir,
        "invalid-missing-section",
        lambda payload, _case_dir: payload.__setitem__(
            "sections", [section for section in payload["sections"] if section["role"] != "mrp_reread_terminal"]
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
            "sections", [payload["sections"][4], *payload["sections"][:4], *payload["sections"][5:]]
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
        "invalid-missing-visible-opening",
        lambda payload, case_dir: replace_section_text(payload, case_dir, 0, "Opening without noetic header.\n"),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-missing-field-witness-nar",
        lambda payload, case_dir: replace_section_text(
            payload,
            case_dir,
            4,
            "Closure/Reconstruction Witness\nField Witness prose only.\nNormalized Activation Record prose only.\n",
        ),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-missing-closing-formulation",
        lambda payload, case_dir: replace_section_text(payload, case_dir, 6, "Scoped boundary only.\n"),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-under-target-size",
        lambda payload, _case_dir: payload["output"].__setitem__("target_output_kb", 100),
    )
    expect_invalid(
        root,
        base_dir,
        "invalid-duplicate-required-role",
        lambda payload, _case_dir: payload["sections"].insert(1, dict(payload["sections"][0])),
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
    parser.add_argument("--allow-under-target", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if args.self_test:
        return run_self_test(root)
    if args.manifest is None:
        raise SystemExit("--manifest is required unless --self-test is used")
    record = assemble_manifest(args.manifest, root=root, allow_under_target=args.allow_under_target)
    print("staged governed output assembly: PASS")
    print(f"output: {record['output']['path']}")
    print(f"output sha256: {record['output']['sha256']}")
    print(f"output bytes: {record['output']['bytes']}")
    print(f"hash record: {record['hash_record']['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
