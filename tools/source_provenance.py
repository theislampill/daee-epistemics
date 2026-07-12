#!/usr/bin/env python3
"""Shared tracked predecessor binding validation for the Branch 10 A16 carriers.

This module validates only tracked predecessor intent.  It deliberately has no
current-HEAD, ancestry, remote, CI, or receipt-validation path.  Those realized
commit claims belong to the external exact-commit receipt owner.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SOURCE_BINDING_SCHEMA_PATH = ROOT / "schema" / "source-binding.schema.json"
CASE_REGISTRY_PATH = ROOT / "tests" / "source-provenance" / "contract-cases.json"

BINDING_SCHEMA = "daee-source-binding-v1"
BINDING_ID = "daee-v0.4.6.0-branch10-predecessor-binding"
CHECKPOINT_COMMIT = "bcccb4e34c75e1f8e363ef020e2deeaabae60435"
CHECKPOINT_TREE = "7238bb567209003adb9b07cb0ec2d1629780cc2e"
CARRIER_PATHS = (
    "docs/audits/v0.4.6.0-wip-andon-closure-ledger.json",
    "docs/audits/v0.4.6.0-wip-andon-contract-registry.json",
    "docs/audits/v0.4.6.0-wip-architecture-decisions.json",
    "docs/audits/v0.4.6.0-wip-state-capsule-v2-migration-ledger.json",
)
WORKFLOW_IDENTITY = {
    "path": ".github/workflows/ci.yml",
    "name": "CI",
    "job": "runtime-checks",
}
FORBIDDEN_BINDING_KEYS = {
    "carrier_hashes",
    "carrier_sha256",
    "current_head",
    "current_tree",
    "future_commit",
    "receipt_hash",
    "receipt_sha256",
    "source_head",
}


class DuplicateObjectKey(ValueError):
    """Raised when strict JSON decoding sees a repeated textual object key."""


@dataclass(frozen=True)
class SourceFinding:
    failure_class: str
    message: str


GitRun = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def rel(path: Path, *, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateObjectKey(f"duplicate object key {key!r}")
        result[key] = value
    return result


def strict_json_loads(raw: bytes, *, label: str) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label}: invalid UTF-8: {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=_strict_object)
    except DuplicateObjectKey as exc:
        raise DuplicateObjectKey(f"{label}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label}: invalid JSON: {exc}") from exc


def strict_json_load(path: Path, *, root: Path = ROOT) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"{rel(path, root=root)}: cannot read file: {exc}") from exc
    return strict_json_loads(raw, label=rel(path, root=root))


def _type_matches(value: Any, declared: str | list[str]) -> bool:
    kinds = [declared] if isinstance(declared, str) else declared
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "null": lambda item: item is None,
    }
    return any(checks.get(kind, lambda _item: True)(value) for kind in kinds)


def json_schema_errors(value: Any, schema: dict[str, Any], location: str = "$") -> list[str]:
    errors: list[str] = []
    declared_type = schema.get("type")
    if declared_type is not None and not _type_matches(value, declared_type):
        return [f"{location}: expected type {declared_type!r}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: expected constant {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: value {value!r} is outside the controlled vocabulary")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{location}: string is shorter than minLength")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{location}: value does not match pattern {pattern!r}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{location}: array has fewer than minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{location}: array has more than maxItems")
        if schema.get("uniqueItems"):
            identities = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(identities) != len(set(identities)):
                errors.append(f"{location}: array items are not unique")
        child_schema = schema.get("items")
        if isinstance(child_schema, dict):
            for index, item in enumerate(value):
                errors.extend(json_schema_errors(item, child_schema, f"{location}[{index}]"))
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for required in schema.get("required", []):
            if required not in value:
                errors.append(f"{location}: missing required property {required!r}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{location}: unexpected property {key!r}")
        for key, child_schema in properties.items():
            if key in value and isinstance(child_schema, dict):
                errors.extend(json_schema_errors(value[key], child_schema, f"{location}.{key}"))
    return errors


def _forbidden_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_BINDING_KEYS:
                return key
            nested = _forbidden_key(child)
            if nested:
                return nested
    elif isinstance(value, list):
        for child in value:
            nested = _forbidden_key(child)
            if nested:
                return nested
    return None


def validate_carrier_document(document: Any, *, carrier_path: str) -> list[SourceFinding]:
    """Validate one parsed active carrier without comparing it to Git HEAD."""
    if not isinstance(document, dict):
        return [SourceFinding("carrier_contract", f"{carrier_path}: carrier must be a JSON object")]
    if "source_head" in document:
        return [
            SourceFinding(
                "legacy_source_head_present",
                f"{carrier_path}: legacy source_head is forbidden; use source_binding predecessor intent",
            )
        ]
    binding = document.get("source_binding")
    if not isinstance(binding, dict):
        return [SourceFinding("missing_source_binding", f"{carrier_path}: source_binding object is required")]
    forbidden = _forbidden_key(binding)
    if forbidden:
        return [
            SourceFinding(
                "current_head_laundering",
                f"{carrier_path}: source_binding key {forbidden!r} is forbidden because tracked bytes cannot certify current identity",
            )
        ]
    schema = strict_json_load(SOURCE_BINDING_SCHEMA_PATH)
    errors = json_schema_errors(binding, schema)
    if errors:
        return [SourceFinding("source_binding_schema", f"{carrier_path}: {errors[0]}")]
    return []


def _skip_json_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index] in " \t\r\n":
        index += 1
    return index


def _scan_json_string_end(text: str, start: int, *, carrier_path: str) -> int:
    if start >= len(text) or text[start] != '"':
        raise ValueError(f"{carrier_path}: expected JSON string token")
    index = start + 1
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == '"':
            return index + 1
        index += 1
    raise ValueError(f"{carrier_path}: unterminated JSON string token")


def _scan_json_value_end(text: str, start: int, *, carrier_path: str) -> int:
    if start >= len(text):
        raise ValueError(f"{carrier_path}: missing JSON value")
    opening = text[start]
    if opening == '"':
        return _scan_json_string_end(text, start, carrier_path=carrier_path)
    if opening in "{[":
        stack = ["}" if opening == "{" else "]"]
        index = start + 1
        while index < len(text) and stack:
            char = text[index]
            if char == '"':
                index = _scan_json_string_end(text, index, carrier_path=carrier_path)
                continue
            if char == "{":
                stack.append("}")
            elif char == "[":
                stack.append("]")
            elif char in "}]":
                if char != stack[-1]:
                    raise ValueError(f"{carrier_path}: mismatched JSON container token {char!r}")
                stack.pop()
            index += 1
        if stack:
            raise ValueError(f"{carrier_path}: unterminated JSON container")
        return index
    index = start
    while index < len(text) and text[index] not in " \t\r\n,}]":
        index += 1
    if index == start:
        raise ValueError(f"{carrier_path}: empty JSON primitive")
    return index


def _extract_source_binding_bytes(raw: bytes, *, carrier_path: str) -> bytes:
    """Return the exact top-level source_binding object bytes.

    The token walk advances over each complete top-level value, so nested keys,
    string contents, and earlier decoy objects cannot be mistaken for the
    carrier's real top-level source_binding member.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{carrier_path}: invalid UTF-8: {exc}") from exc
    index = _skip_json_whitespace(text, 0)
    if index >= len(text) or text[index] != "{":
        raise ValueError(f"{carrier_path}: carrier must begin with a JSON object")
    index += 1
    while True:
        index = _skip_json_whitespace(text, index)
        if index >= len(text):
            raise ValueError(f"{carrier_path}: top-level JSON object is not closed")
        if text[index] == "}":
            break
        key_start = index
        key_end = _scan_json_string_end(text, key_start, carrier_path=carrier_path)
        try:
            key = json.loads(text[key_start:key_end])
        except json.JSONDecodeError as exc:
            raise ValueError(f"{carrier_path}: invalid top-level JSON key: {exc}") from exc
        index = _skip_json_whitespace(text, key_end)
        if index >= len(text) or text[index] != ":":
            raise ValueError(f"{carrier_path}: top-level key {key!r} is missing ':'")
        value_start = _skip_json_whitespace(text, index + 1)
        value_end = _scan_json_value_end(text, value_start, carrier_path=carrier_path)
        if key == "source_binding":
            if text[value_start] != "{":
                raise ValueError(f"{carrier_path}: top-level source_binding is not an object")
            return text[value_start:value_end].encode("utf-8")
        index = _skip_json_whitespace(text, value_end)
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index < len(text) and text[index] == "}":
            break
        raise ValueError(f"{carrier_path}: invalid token after top-level key {key!r}")
    raise ValueError(f"{carrier_path}: top-level source_binding member is missing")


def _default_git_run(root: Path) -> GitRun:
    def run(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["GIT_NO_REPLACE_OBJECTS"] = "1"
        return subprocess.run(
            ["git", "--no-replace-objects", *arguments],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    return run


def _workflow_file_identity(raw: bytes) -> tuple[str | None, list[str]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, []
    name_match = re.search(r"(?m)^name:\s*['\"]?([^'\"\r\n]+?)['\"]?\s*$", text)
    jobs_match = re.search(r"(?m)^jobs:\s*$", text)
    jobs: list[str] = []
    if jobs_match:
        tail = text[jobs_match.end() :]
        for match in re.finditer(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", tail):
            jobs.append(match.group(1))
    return (name_match.group(1).strip() if name_match else None), jobs


def _carrier_bytes(root: Path, overrides: Mapping[str, bytes] | None) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for carrier_path in CARRIER_PATHS:
        if overrides is not None and carrier_path in overrides:
            result[carrier_path] = overrides[carrier_path]
            continue
        try:
            result[carrier_path] = (root / carrier_path).read_bytes()
        except OSError as exc:
            raise ValueError(f"{carrier_path}: cannot read carrier: {exc}") from exc
    return result


def validate_tracked_only(
    *,
    root: Path = ROOT,
    carrier_overrides: Mapping[str, bytes] | None = None,
    git_run: GitRun | None = None,
) -> tuple[dict[str, Any] | None, list[SourceFinding]]:
    """Validate tracked binding intent without reading or comparing current HEAD."""
    try:
        raw_by_path = _carrier_bytes(root, carrier_overrides)
    except ValueError as exc:
        return None, [SourceFinding("carrier_missing", str(exc))]

    parsed_by_path: dict[str, dict[str, Any]] = {}
    inline_by_path: dict[str, bytes] = {}
    for carrier_path in CARRIER_PATHS:
        raw = raw_by_path[carrier_path]
        try:
            parsed = strict_json_loads(raw, label=carrier_path)
        except DuplicateObjectKey as exc:
            return None, [SourceFinding("duplicate_json_key", str(exc))]
        except ValueError as exc:
            return None, [SourceFinding("carrier_json", str(exc))]
        findings = validate_carrier_document(parsed, carrier_path=carrier_path)
        if findings and findings[0].failure_class in {
            "legacy_source_head_present",
            "missing_source_binding",
            "current_head_laundering",
        }:
            return None, findings
        if not isinstance(parsed, dict):
            return None, [SourceFinding("carrier_contract", f"{carrier_path}: carrier must be a JSON object")]
        parsed_by_path[carrier_path] = parsed
        try:
            inline_by_path[carrier_path] = _extract_source_binding_bytes(raw, carrier_path=carrier_path)
        except ValueError as exc:
            return None, [SourceFinding("missing_source_binding", str(exc))]

    reference_path = CARRIER_PATHS[0]
    reference_inline = inline_by_path[reference_path]
    for carrier_path in CARRIER_PATHS[1:]:
        if inline_by_path[carrier_path] != reference_inline:
            return None, [
                SourceFinding(
                    "source_binding_divergence",
                    f"{carrier_path}: source_binding is not byte-identical to {reference_path}",
                )
            ]
    binding = parsed_by_path[reference_path]["source_binding"]

    paths = binding.get("carrier_paths") if isinstance(binding, dict) else None
    if isinstance(paths, list) and len(paths) != len(set(paths)):
        return None, [SourceFinding("carrier_set_duplicate", "source_binding.carrier_paths contains a duplicate carrier path")]
    expected_paths = list(CARRIER_PATHS)
    if paths != expected_paths:
        actual = paths if isinstance(paths, list) else []
        omitted = sorted(set(expected_paths) - set(actual))
        extra = sorted(set(actual) - set(expected_paths))
        return None, [
            SourceFinding(
                "carrier_set_mismatch",
                f"source_binding.carrier_paths omits={omitted} extra={extra}; exact sorted four-carrier set is required",
            )
        ]

    checkpoint = binding.get("checkpoint") if isinstance(binding, dict) else None
    commit = checkpoint.get("commit") if isinstance(checkpoint, dict) else None
    tree = checkpoint.get("tree") if isinstance(checkpoint, dict) else None
    if not isinstance(commit, str) or not commit:
        return None, [SourceFinding("checkpoint_missing", "source_binding.checkpoint.commit is missing")]
    run_git = git_run or _default_git_run(root)
    object_type = run_git(["cat-file", "-t", commit])
    if object_type.returncode != 0:
        return None, [SourceFinding("checkpoint_missing", f"checkpoint commit object {commit} is missing")]
    observed_type = object_type.stdout.strip()
    if observed_type != "commit":
        return None, [SourceFinding("checkpoint_not_commit", f"checkpoint object {commit} has type {observed_type}, not commit")]
    if commit != CHECKPOINT_COMMIT:
        return None, [
            SourceFinding(
                "checkpoint_identity_mismatch",
                f"checkpoint commit {commit} does not equal required {CHECKPOINT_COMMIT}",
            )
        ]
    tree_result = run_git(["show", "-s", "--format=%T", commit])
    if tree_result.returncode != 0:
        return None, [SourceFinding("checkpoint_tree_unavailable", f"cannot read tree for checkpoint {commit}")]
    actual_tree = tree_result.stdout.strip()
    if tree != actual_tree or tree != CHECKPOINT_TREE:
        return None, [
            SourceFinding(
                "checkpoint_tree_mismatch",
                f"checkpoint tree {tree} does not equal commit tree {actual_tree} and required tree {CHECKPOINT_TREE}",
            )
        ]

    workflow = binding.get("workflow") if isinstance(binding, dict) else None
    if workflow != WORKFLOW_IDENTITY:
        return None, [
            SourceFinding(
                "workflow_identity_mismatch",
                f"tracked workflow identity {workflow!r} does not equal required {WORKFLOW_IDENTITY!r}",
            )
        ]
    workflow_path = root / WORKFLOW_IDENTITY["path"]
    try:
        workflow_raw = workflow_path.read_bytes()
    except OSError as exc:
        return None, [SourceFinding("workflow_identity_mismatch", f"cannot read {WORKFLOW_IDENTITY['path']}: {exc}")]
    workflow_name, workflow_jobs = _workflow_file_identity(workflow_raw)
    if workflow_name != WORKFLOW_IDENTITY["name"] or WORKFLOW_IDENTITY["job"] not in workflow_jobs:
        return None, [
            SourceFinding(
                "workflow_identity_mismatch",
                f"live workflow name/jobs are {workflow_name!r}/{workflow_jobs!r}; required CI/runtime-checks",
            )
        ]

    for carrier_path in CARRIER_PATHS:
        findings = validate_carrier_document(parsed_by_path[carrier_path], carrier_path=carrier_path)
        if findings:
            return None, findings

    verdict = {
        "binding_id": binding["binding_id"],
        "binding_sha256": hashlib.sha256(reference_inline).hexdigest(),
        "carrier_paths": list(CARRIER_PATHS),
        "checkpoint_commit": commit,
        "checkpoint_tree": tree,
        "current_head_compared": False,
        "current_head_ancestry_checked": False,
        "external_receipt_required_for_exact_commit": True,
        "external_receipt_validated": False,
        "strict_successor_proven": False,
        "status": "TRACKED_SOURCE_BINDING_VALID",
        "terminal_claim": False,
        "workflow": dict(WORKFLOW_IDENTITY),
    }
    return verdict, []


def _resolve_parent(document: Any, dotted: str) -> tuple[Any, str]:
    tokens = dotted.split(".")
    parent = document
    for token in tokens[:-1]:
        parent = parent[token]
    return parent, tokens[-1]


def _fixture_overrides(case: dict[str, Any], *, root: Path) -> dict[str, bytes]:
    documents = {
        path: strict_json_loads((root / path).read_bytes(), label=path)
        for path in CARRIER_PATHS
    }
    raw_injections: list[dict[str, Any]] = []
    decoy_injections: list[dict[str, Any]] = []
    for operation in case.get("operations", []):
        if operation.get("op") == "inject-preceding-decoy-and-reformat-top-level":
            decoy_injections.append(operation)
            continue
        carriers = CARRIER_PATHS if operation.get("carrier") == "*" else (operation.get("carrier"),)
        for carrier_path in carriers:
            if carrier_path not in documents:
                raise ValueError(f"unsupported fixture carrier {carrier_path!r}")
            op = operation.get("op")
            if op == "inject-duplicate-key":
                raw_injections.append({**operation, "carrier": carrier_path})
                continue
            parent, key = _resolve_parent(documents[carrier_path], str(operation.get("path", "")))
            if op == "set":
                parent[key] = copy.deepcopy(operation.get("value"))
            elif op == "delete":
                del parent[key]
            elif op == "append":
                parent[key].append(copy.deepcopy(operation.get("value")))
            elif op == "delete-index":
                del parent[key][int(operation["index"])]
            else:
                raise ValueError(f"unsupported fixture operation {operation!r}")
    overrides = {
        path: (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        for path, document in documents.items()
    }
    for operation in raw_injections:
        carrier_path = operation["carrier"]
        raw = overrides[carrier_path]
        duplicate = (
            "{\n  "
            + json.dumps(str(operation["key"]))
            + ": "
            + json.dumps(operation.get("value"), ensure_ascii=False)
            + ","
        ).encode("utf-8")
        if not raw.startswith(b"{"):
            raise ValueError(f"{carrier_path}: fixture carrier must start with an object")
        overrides[carrier_path] = duplicate + raw[1:]
    for operation in decoy_injections:
        decoy_property = str(operation.get("decoy_property", "review_decoy"))
        drift_carrier = str(operation.get("drift_carrier", ""))
        if drift_carrier not in overrides:
            raise ValueError(f"unsupported drift carrier {drift_carrier!r}")
        binding = documents[CARRIER_PATHS[0]]["source_binding"]
        compact_binding = json.dumps(binding, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        decoy_member = (
            "\n  "
            + json.dumps(decoy_property)
            + ": {\"source_binding\":"
        ).encode("utf-8") + compact_binding + b"},"
        for carrier_path in CARRIER_PATHS:
            raw = overrides[carrier_path]
            if carrier_path == drift_carrier:
                top_level_binding = _extract_source_binding_bytes(raw, carrier_path=carrier_path)
                start = raw.index(top_level_binding)
                raw = raw[:start] + compact_binding + raw[start + len(top_level_binding) :]
            if not raw.startswith(b"{"):
                raise ValueError(f"{carrier_path}: fixture carrier must start with an object")
            overrides[carrier_path] = b"{" + decoy_member + raw[1:]
    return overrides


def self_test(*, root: Path = ROOT) -> tuple[list[str], int, int]:
    problems: list[str] = []
    try:
        cases = strict_json_load(CASE_REGISTRY_PATH, root=root)
    except ValueError as exc:
        return [str(exc)], 0, 0
    valid_cases = cases.get("valid_cases", []) if isinstance(cases, dict) else []
    invalid_cases = cases.get("invalid_cases", []) if isinstance(cases, dict) else []
    valid_count = 0
    invalid_count = 0
    for case in valid_cases:
        valid_count += 1
        try:
            overrides = _fixture_overrides(case, root=root)
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"{case.get('case_id')}: fixture error: {exc}")
            continue
        verdict, findings = validate_tracked_only(root=root, carrier_overrides=overrides)
        if findings:
            problems.append(f"{case.get('case_id')}: [{findings[0].failure_class}] {findings[0].message}")
            continue
        if verdict is None or verdict.get("status") != case.get("expected_status"):
            problems.append(f"{case.get('case_id')}: wrong tracked-only status {verdict!r}")
            continue
        if case.get("simulated_current_head") != verdict.get("checkpoint_commit"):
            problems.append(f"{case.get('case_id')}: predecessor-HEAD canary is not checkpoint-bound")
        for key, expected in case.get("expected_nonclaims", {}).items():
            if verdict.get(key) != expected:
                problems.append(f"{case.get('case_id')}: {key} expected {expected!r}, got {verdict.get(key)!r}")
    for case in invalid_cases:
        invalid_count += 1
        try:
            overrides = _fixture_overrides(case, root=root)
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"{case.get('case_id')}: fixture error: {exc}")
            continue
        _verdict, findings = validate_tracked_only(root=root, carrier_overrides=overrides)
        if not findings:
            problems.append(f"{case.get('case_id')}: invalid fixture survived")
            continue
        finding = findings[0]
        if finding.failure_class != case.get("expected_failure_class"):
            problems.append(
                f"{case.get('case_id')}: expected {case.get('expected_failure_class')!r}, "
                f"got {finding.failure_class!r}: {finding.message}"
            )
        diagnostic = f"{finding.failure_class}: {finding.message}"
        for marker in case.get("required_markers", []):
            if str(marker) not in diagnostic:
                problems.append(f"{case.get('case_id')}: required marker {marker!r} absent from {diagnostic!r}")
    return problems, valid_count, invalid_count
