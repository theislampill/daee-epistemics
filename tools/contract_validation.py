#!/usr/bin/env python3
"""Shared stdlib contract-schema and repository-path custody helpers."""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any


@dataclass(frozen=True)
class SchemaIssue:
    path: str
    keyword: str
    message: str


class SchemaDefinitionError(ValueError):
    """Raised when a schema uses an unsupported or unresolved feature."""


class PathCustodyError(ValueError):
    """Raised when a path leaves the authorized repository root."""

    def __init__(self, message: str, *, subcode: str = "path-custody") -> None:
        super().__init__(message)
        self.subcode = subcode


_ANNOTATIONS = {"$schema", "$id", "title", "description"}
_VALIDATION_KEYWORDS = {
    "$defs", "$ref", "type", "const", "enum", "properties", "required",
    "additionalProperties", "items", "minItems", "maxItems", "uniqueItems",
    "pattern", "minLength", "minimum", "maximum", "oneOf", "anyOf",
}
_SUPPORTED_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}


def _pointer_get(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise SchemaDefinitionError(f"only local JSON pointers are supported: {reference!r}")
    value: Any = root_schema
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or part not in value:
            raise SchemaDefinitionError(f"unresolved local schema reference: {reference!r}")
        value = value[part]
    if not isinstance(value, dict):
        raise SchemaDefinitionError(f"schema reference does not resolve to an object: {reference!r}")
    return value


def _check_schema_definition(node: Any, root_schema: dict[str, Any], pointer: str) -> None:
    if not isinstance(node, dict):
        raise SchemaDefinitionError(f"schema node {pointer} must be an object")
    unsupported = sorted(set(node) - _ANNOTATIONS - _VALIDATION_KEYWORDS)
    if unsupported:
        raise SchemaDefinitionError(f"unsupported schema keyword at {pointer}: {unsupported[0]}")
    if "$ref" in node:
        if not isinstance(node["$ref"], str):
            raise SchemaDefinitionError(f"$ref at {pointer} must be a string")
        _pointer_get(root_schema, node["$ref"])
    declared_type = node.get("type")
    if declared_type is not None:
        values = declared_type if isinstance(declared_type, list) else [declared_type]
        if not values or any(value not in _SUPPORTED_TYPES for value in values):
            raise SchemaDefinitionError(f"unsupported type declaration at {pointer}: {declared_type!r}")
    properties = node.get("properties")
    if properties is not None:
        if not isinstance(properties, dict):
            raise SchemaDefinitionError(f"properties at {pointer} must be an object")
        for name, child in properties.items():
            _check_schema_definition(child, root_schema, f"{pointer}/properties/{name}")
    definitions = node.get("$defs")
    if definitions is not None:
        if not isinstance(definitions, dict):
            raise SchemaDefinitionError(f"$defs at {pointer} must be an object")
        for name, child in definitions.items():
            _check_schema_definition(child, root_schema, f"{pointer}/$defs/{name}")
    items = node.get("items")
    if items is not None:
        _check_schema_definition(items, root_schema, f"{pointer}/items")
    additional = node.get("additionalProperties")
    if not isinstance(additional, (type(None), bool, dict)):
        raise SchemaDefinitionError(f"additionalProperties at {pointer} must be boolean or schema")
    if isinstance(additional, dict):
        _check_schema_definition(additional, root_schema, f"{pointer}/additionalProperties")
    for keyword in ("oneOf", "anyOf"):
        branches = node.get(keyword)
        if branches is not None:
            if not isinstance(branches, list) or not branches:
                raise SchemaDefinitionError(f"{keyword} at {pointer} must be a non-empty array")
            for index, child in enumerate(branches):
                _check_schema_definition(child, root_schema, f"{pointer}/{keyword}/{index}")
    if "pattern" in node:
        if not isinstance(node["pattern"], str):
            raise SchemaDefinitionError(f"pattern at {pointer} must be a string")
        try:
            re.compile(node["pattern"])
        except re.error as exc:
            raise SchemaDefinitionError(f"invalid pattern at {pointer}: {exc}") from exc


def validate_schema_definition(schema: dict[str, Any]) -> None:
    """Reject every schema keyword/reference outside the implemented subset."""
    _check_schema_definition(schema, schema, "#")


def _json_type_matches(value: Any, declared: str) -> bool:
    if declared == "object":
        return isinstance(value, dict)
    if declared == "array":
        return isinstance(value, list)
    if declared == "string":
        return isinstance(value, str)
    if declared == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if declared == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if declared == "boolean":
        return isinstance(value, bool)
    if declared == "null":
        return value is None
    raise SchemaDefinitionError(f"unsupported JSON type: {declared}")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _validate(instance: Any, schema: dict[str, Any], root_schema: dict[str, Any], path: str) -> list[SchemaIssue]:
    issues: list[SchemaIssue] = []
    if "$ref" in schema:
        issues.extend(_validate(instance, _pointer_get(root_schema, schema["$ref"]), root_schema, path))
    declared_type = schema.get("type")
    if declared_type is not None:
        declared = declared_type if isinstance(declared_type, list) else [declared_type]
        if not any(_json_type_matches(instance, kind) for kind in declared):
            return [SchemaIssue(path, "type", f"expected type {declared_type!r}")]
    if "const" in schema and instance != schema["const"]:
        issues.append(SchemaIssue(path, "const", f"must equal {schema['const']!r}"))
    if "enum" in schema and instance not in schema["enum"]:
        issues.append(SchemaIssue(path, "enum", f"must be one of {schema['enum']!r}"))
    if "oneOf" in schema:
        matches = sum(not _validate(instance, branch, root_schema, path) for branch in schema["oneOf"])
        if matches != 1:
            issues.append(SchemaIssue(path, "oneOf", f"must match exactly one branch; matched {matches}"))
    if "anyOf" in schema:
        matches = sum(not _validate(instance, branch, root_schema, path) for branch in schema["anyOf"])
        if matches == 0:
            issues.append(SchemaIssue(path, "anyOf", "must match at least one branch"))
    if isinstance(instance, dict):
        required = schema.get("required", [])
        for name in required:
            if name not in instance:
                issues.append(SchemaIssue(path, "required", f"missing required property {name!r}"))
        properties = schema.get("properties", {})
        for name, value in instance.items():
            child_path = f"{path}.{name}"
            if name in properties:
                issues.extend(_validate(value, properties[name], root_schema, child_path))
            elif schema.get("additionalProperties") is False:
                issues.append(SchemaIssue(child_path, "additionalProperties", f"unexpected property {name!r}"))
            elif isinstance(schema.get("additionalProperties"), dict):
                issues.extend(_validate(value, schema["additionalProperties"], root_schema, child_path))
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            issues.append(SchemaIssue(path, "minItems", f"requires at least {schema['minItems']} items"))
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            issues.append(SchemaIssue(path, "maxItems", f"allows at most {schema['maxItems']} items"))
        if schema.get("uniqueItems"):
            encoded = [_canonical(value) for value in instance]
            if len(encoded) != len(set(encoded)):
                issues.append(SchemaIssue(path, "uniqueItems", "array items must be unique"))
        if "items" in schema:
            for index, value in enumerate(instance):
                issues.extend(_validate(value, schema["items"], root_schema, f"{path}[{index}]"))
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            issues.append(SchemaIssue(path, "minLength", f"requires length >= {schema['minLength']}"))
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            issues.append(SchemaIssue(path, "pattern", f"does not match {schema['pattern']!r}"))
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            issues.append(SchemaIssue(path, "minimum", f"must be >= {schema['minimum']}"))
        if "maximum" in schema and instance > schema["maximum"]:
            issues.append(SchemaIssue(path, "maximum", f"must be <= {schema['maximum']}"))
    return issues


def validate_schema_subset(instance: Any, schema: dict[str, Any]) -> list[SchemaIssue]:
    """Validate an instance against the complete schema subset used by A11."""
    validate_schema_definition(schema)
    return _validate(instance, schema, schema, "$")


def resolve_repo_path(
    root: Path,
    candidate: str | Path,
    *,
    must_exist: bool = False,
    expect_file: bool = False,
    expect_dir: bool = False,
) -> Path:
    """Resolve one repository-relative path without allowing custody escape."""
    root_resolved = root.resolve(strict=True)
    raw = os.fspath(candidate)
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise PathCustodyError("path must be a non-empty text value", subcode="path-shape")
    windows = PureWindowsPath(raw)
    native = Path(raw)
    if native.is_absolute() or windows.is_absolute() or bool(windows.drive) or raw.startswith(("\\\\", "//")):
        raise PathCustodyError(f"absolute, drive-qualified, or UNC path is forbidden: {raw}", subcode="absolute-path")
    normalized_parts = PureWindowsPath(raw.replace("/", "\\")).parts
    if ".." in normalized_parts:
        raise PathCustodyError(f"parent traversal is forbidden: {raw}", subcode="path-traversal")
    lexical = root_resolved / native
    try:
        resolved = lexical.resolve(strict=must_exist)
    except FileNotFoundError as exc:
        raise PathCustodyError(f"required path does not exist: {raw}", subcode="missing-path") from exc
    except OSError as exc:
        raise PathCustodyError(f"path resolution failed for {raw}: {exc}", subcode="path-resolution") from exc
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PathCustodyError(f"resolved path leaves repository root: {raw} -> {resolved}", subcode="symlink-escape") from exc
    if must_exist and not resolved.exists():
        raise PathCustodyError(f"required path does not exist: {raw}", subcode="missing-path")
    if expect_file and not resolved.is_file():
        raise PathCustodyError(f"required file is absent or not regular: {raw}", subcode="not-file")
    if expect_dir and not resolved.is_dir():
        raise PathCustodyError(f"required directory is absent: {raw}", subcode="not-directory")
    return resolved


def _self_test() -> int:
    root = Path(__file__).resolve().parents[1]
    schema_paths = (
        "schema/validation-registry.schema.json",
        "schema/checker-replay-verdict.schema.json",
        "schema/model-smoke-escape.schema.json",
        "schema/negative-fixture-expectation.schema.json",
    )
    for relative in schema_paths:
        path = resolve_repo_path(root, relative, must_exist=True, expect_file=True)
        validate_schema_definition(json.loads(path.read_text(encoding="utf-8")))
    probe_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["items", "choice"],
        "properties": {
            "items": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"$ref": "#/$defs/token"}},
            "choice": {"oneOf": [{"const": "yes"}, {"type": "integer", "minimum": 1}]},
        },
        "$defs": {"token": {"type": "string", "minLength": 1, "pattern": "^[a-z]+$"}},
    }
    invalid = {"items": ["ok", "ok"], "choice": 0, "unexpected": True}
    keywords = {issue.keyword for issue in validate_schema_subset(invalid, probe_schema)}
    required = {"uniqueItems", "oneOf", "additionalProperties"}
    if not required.issubset(keywords):
        print(json.dumps({"keywords": sorted(keywords), "status": "FAIL"}, sort_keys=True))
        return 1
    for candidate in ("../escape", str(root / "schema"), "C:\\outside\\artifact.json", "\\\\server\\share\\artifact.json"):
        try:
            resolve_repo_path(root, candidate)
        except PathCustodyError:
            continue
        print(json.dumps({"accepted_path": candidate, "status": "FAIL"}, sort_keys=True))
        return 1
    print(json.dumps({"schemas": len(schema_paths), "status": "PASS", "subset_keywords_exercised": sorted(keywords)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        raise SystemExit(_self_test())
    raise SystemExit("usage: contract_validation.py --self-test")
