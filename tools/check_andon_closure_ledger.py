#!/usr/bin/env python3
"""Validate the DAEE v0.4.6 ANDON closure ledger control plane.

This is a stdlib-only structural checker.  It proves ledger shape and explicit
control-plane invariants; it does not prove semantic truth, model behavior,
candidate maturity, package readiness, or release readiness.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "andon-closure-ledger.schema.json"
LIVE_LEDGER = ROOT / "docs" / "audits" / "v0.4.6.0-wip-andon-closure-ledger.json"
FIXTURE_ROOT = ROOT / "tests" / "andon-closure-ledger"
CHECKER = "tools/check_andon_closure_ledger.py"
CHECKER_ID = "andon-closure-ledger"
STAGE = "control-plane"
FIXTURE_SCHEMA = "daee-checker-fixture-v1"
TERMINAL_COMPLETION = {"VERIFIED_STRUCTURAL", "VERIFIED_SCOPED_MODEL", "CLOSED_OWNER_ACCEPTED"}
EXPECTATION_SCHEMA_PATH = ROOT / "schema" / "negative-fixture-expectation.schema.json"
EXIT_CATEGORY = "structural-rejection"
DOWNSTREAM_INVALIDATED = ["closure-view", "completion-verdict", "candidate-package", "release-action"]
_GIT_BLOB_CACHE: dict[tuple[str, str], tuple[str | None, bytes | None, str | None]] = {}
_FILE_SHA256_CACHE: dict[str, tuple[str | None, str | None]] = {}


class DuplicateObjectKey(ValueError):
    pass


@dataclass(frozen=True)
class Finding:
    failure_class: str
    message: str


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateObjectKey(f"duplicate object key {key!r}")
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    except FileNotFoundError as exc:
        raise ValueError(f"{rel(path)}: file not found") from exc
    except DuplicateObjectKey as exc:
        raise ValueError(f"{rel(path)}: invalid JSON: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{rel(path)}: invalid JSON: {exc}") from exc


def _select(sequence: list[Any], token: str) -> Any:
    if token.isdigit():
        return sequence[int(token)]
    for item in sequence:
        if not isinstance(item, dict):
            continue
        for key in ("andon_id", "decision_id", "milestone_id", "control_id"):
            if item.get(key) == token:
                return item
    raise KeyError(token)


def resolve_path(document: Any, dotted: str) -> Any:
    current = document
    for token in dotted.split("."):
        current = _select(current, token) if isinstance(current, list) else current[token]
    return current


def resolve_parent(document: Any, dotted: str) -> tuple[Any, str]:
    tokens = dotted.split(".")
    parent = document
    for token in tokens[:-1]:
        parent = _select(parent, token) if isinstance(parent, list) else parent[token]
    return parent, tokens[-1]


def apply_common_operation(document: Any, operation: dict[str, Any]) -> bool:
    op = operation.get("op")
    if op == "set":
        parent, key = resolve_parent(document, operation["path"])
        if isinstance(parent, list):
            index = int(key)
            parent[index] = copy.deepcopy(operation.get("value"))
        else:
            parent[key] = copy.deepcopy(operation.get("value"))
        return True
    if op == "append":
        target = resolve_path(document, operation["path"])
        if not isinstance(target, list):
            raise ValueError(f"fixture append target is not an array: {operation['path']}")
        target.append(copy.deepcopy(operation.get("value")))
        return True
    return False


def materialize_fixture(path: Path, allowed_base: Path) -> Any:
    raw = read_json(path)
    if not isinstance(raw, dict) or raw.get("fixture_schema") != FIXTURE_SCHEMA:
        return raw
    base_value = raw.get("base")
    if base_value != rel(allowed_base):
        raise ValueError(f"{rel(path)}: fixture base must be {rel(allowed_base)}")
    document = copy.deepcopy(read_json(allowed_base))
    operations = raw.get("operations")
    if not isinstance(operations, list):
        raise ValueError(f"{rel(path)}: fixture operations must be an array")
    for operation in operations:
        if not isinstance(operation, dict) or not apply_common_operation(document, operation):
            raise ValueError(f"{rel(path)}: unsupported fixture operation: {operation!r}")
    return document


def _type_matches(value: Any, kind: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "null": value is None,
    }.get(kind, True)


def _resolve_ref(root_schema: dict[str, Any], ref_value: str) -> dict[str, Any]:
    if not ref_value.startswith("#/"):
        raise ValueError(f"unsupported external schema reference: {ref_value}")
    current: Any = root_schema
    for token in ref_value[2:].split("/"):
        current = current[token.replace("~1", "/").replace("~0", "~")]
    return current


def schema_findings(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    location: str = "$",
) -> list[str]:
    if "$ref" in schema:
        return schema_findings(value, _resolve_ref(root_schema, schema["$ref"]), root_schema, location)
    if "anyOf" in schema:
        branches = [schema_findings(value, branch, root_schema, location) for branch in schema["anyOf"]]
        if any(not errors for errors in branches):
            return []
        return [f"{location}: does not match any allowed schema branch"]

    errors: list[str] = []
    declared_type = schema.get("type")
    if declared_type is not None:
        kinds = [declared_type] if isinstance(declared_type, str) else declared_type
        if not any(_type_matches(value, kind) for kind in kinds):
            return [f"{location}: expected type {' or '.join(kinds)}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: value {value!r} is outside the controlled vocabulary")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{location}: string is shorter than minLength")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{location}: value does not match pattern {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{location}: number is below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{location}: number is above maximum")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{location}: array has fewer than minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{location}: array has more than maxItems")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{location}: array items are not unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(schema_findings(item, item_schema, root_schema, f"{location}[{index}]"))

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
                errors.extend(schema_findings(value[key], child_schema, root_schema, f"{location}.{key}"))
    return errors


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    repeated: list[str] = []
    for value in values:
        if value in seen and value not in repeated:
            repeated.append(value)
        seen.add(value)
    return repeated


def _cycle(graph: dict[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if state.get(node) == 1:
            start = stack.index(node)
            return stack[start:] + [node]
        if state.get(node) == 2:
            return None
        state[node] = 1
        stack.append(node)
        for dependency in graph.get(node, []):
            found = visit(dependency)
            if found:
                return found
        stack.pop()
        state[node] = 2
        return None

    for candidate in sorted(graph):
        found = visit(candidate)
        if found:
            return found
    return None


def _repo_relative_path(value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "retained_artifact is missing"
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None, f"retained_artifact is not a repository-relative path: {value}"
    resolved = (ROOT / candidate).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return None, f"retained_artifact escapes the repository: {value}"
    return resolved, None


def _git_blob_bytes(commit_sha1: str, path: str) -> tuple[str | None, bytes | None, str | None]:
    cache_key = (commit_sha1, path)
    if cache_key in _GIT_BLOB_CACHE:
        return _GIT_BLOB_CACHE[cache_key]
    object_type = subprocess.run(
        ["git", "cat-file", "-t", commit_sha1],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if object_type.returncode != 0 or object_type.stdout.strip() != "commit":
        shown = object_type.stdout.strip() or object_type.stderr.strip() or "missing"
        result = (None, None, f"commit_sha1_not_commit: expected commit object, got {shown}")
        _GIT_BLOB_CACHE[cache_key] = result
        return result
    rev_parse = subprocess.run(
        ["git", "rev-parse", f"{commit_sha1}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if rev_parse.returncode != 0:
        result = (None, None, rev_parse.stderr.strip() or "git rev-parse failed")
        _GIT_BLOB_CACHE[cache_key] = result
        return result
    blob_sha1 = rev_parse.stdout.strip()
    cat_file = subprocess.run(
        ["git", "cat-file", "blob", blob_sha1],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if cat_file.returncode != 0:
        result = (blob_sha1, None, cat_file.stderr.decode("utf-8", errors="replace").strip() or "git cat-file failed")
        _GIT_BLOB_CACHE[cache_key] = result
        return result
    result = (blob_sha1, cat_file.stdout, None)
    _GIT_BLOB_CACHE[cache_key] = result
    return result


def _retained_file_sha256(path: str) -> tuple[str | None, str | None]:
    if path in _FILE_SHA256_CACHE:
        return _FILE_SHA256_CACHE[path]
    resolved, problem = _repo_relative_path(path)
    if problem or resolved is None:
        result = (None, problem)
    else:
        try:
            result = (hashlib.sha256(resolved.read_bytes()).hexdigest(), None)
        except OSError as exc:
            result = (None, str(exc))
    _FILE_SHA256_CACHE[path] = result
    return result


def semantic_findings(document: Any, *, expected_head: str | None) -> list[Finding]:
    if not isinstance(document, dict) or not isinstance(document.get("rows"), list):
        return []
    rows = [row for row in document["rows"] if isinstance(row, dict)]
    row_ids = [str(row.get("andon_id", "")) for row in rows]
    duplicate_rows = _duplicates(row_ids)
    if duplicate_rows:
        return [Finding("duplicate_andon_id", f"duplicate ANDON row: {duplicate_rows[0]}")]
    by_id = {str(row.get("andon_id")): row for row in rows}

    a16 = by_id.get("A16")
    if a16 and "A16" in a16.get("dependencies", []):
        return [Finding("plan_self_cycle", "A16 depends on itself at plan level; use A16.bootstrap and A16.terminal milestones")]

    actual_head = document.get("source_head")
    if expected_head and actual_head != expected_head:
        return [Finding("stale_evidence_head", f"source_head {actual_head} does not match repository HEAD {expected_head}")]

    for row in rows:
        row_id = str(row.get("andon_id"))
        status = row.get("status")
        bounded_verified = row.get("bounded_verified")
        integration_open = row.get("integration_open") is True
        remaining_joins = row.get("remaining_joins", [])
        owner_gated = row.get("owner_gated") is True
        owner_gate_present = bool(row.get("owner_gates", []))
        artifact_gated = row.get("artifact_gated") is True
        artifact_gate_present = bool(row.get("artifact_gates", []))
        terminal_open = row.get("terminal_open") is True

        if status in {"VERIFIED_STRUCTURAL", "VERIFIED_SCOPED_MODEL"}:
            verification = row.get("verification", {})
            if verification.get("structural_only") is not True:
                return [Finding("semantic_overclaim", f"{row_id} {status} must retain verification.structural_only=true and cannot claim semantic truth")]

        if integration_open and not remaining_joins:
            return [
                Finding(
                    "integration_open_missing_joins",
                    f"{row_id} integration_open=true requires nonempty remaining_joins",
                )
            ]
        if not integration_open and remaining_joins:
            return [
                Finding(
                    "integration_join_dimension_mismatch",
                    f"{row_id} integration_open=false requires empty remaining_joins",
                )
            ]
        if owner_gated != owner_gate_present:
            return [
                Finding(
                    "owner_gate_dimension_mismatch",
                    f"{row_id} owner_gated={str(owner_gated).lower()} does not match "
                    f"owner_gates present={str(owner_gate_present).lower()}",
                )
            ]
        if artifact_gated != artifact_gate_present:
            return [
                Finding(
                    "artifact_gate_dimension_mismatch",
                    f"{row_id} artifact_gated={str(artifact_gated).lower()} does not match "
                    f"artifact_gates present={str(artifact_gate_present).lower()}",
                )
            ]

        for index, evidence in enumerate(row.get("evidence_refs", [])):
            if not isinstance(evidence, dict):
                continue
            kind = evidence.get("kind")
            commit_sha1 = evidence.get("commit_sha1")
            blob_sha1 = evidence.get("blob_sha1")
            sha256 = evidence.get("sha256")
            command = evidence.get("command")
            exit_code = evidence.get("exit_code")
            retained_artifact = evidence.get("retained_artifact")
            unretained_reason = evidence.get("unretained_reason")
            location = f"{row_id} evidence_refs[{index}] {kind}"
            if kind == "source_blob":
                if not all(isinstance(value, str) and value for value in (commit_sha1, blob_sha1, sha256)):
                    return [Finding("source_blob_evidence_incomplete", f"{location} requires exact commit_sha1, blob_sha1, and sha256")]
                if command is not None or exit_code is not None or not retained_artifact or unretained_reason is not None:
                    return [Finding("source_blob_evidence_inconsistent", f"{location} must identify retained source bytes without command or unretained fields")]
                _, path_problem = _repo_relative_path(retained_artifact)
                if path_problem:
                    return [Finding("source_blob_path_invalid", f"{row_id} {path_problem}")]
                actual_blob, blob_bytes, git_problem = _git_blob_bytes(commit_sha1, retained_artifact)
                if git_problem and git_problem.startswith("commit_sha1_not_commit:"):
                    return [Finding("source_commit_not_commit", f"{row_id} {git_problem}")]
                if git_problem or actual_blob is None or blob_bytes is None:
                    return [Finding("source_blob_unavailable", f"{row_id} {retained_artifact} cannot be read from {commit_sha1}: {git_problem}")]
                if actual_blob != blob_sha1:
                    return [Finding("source_blob_id_mismatch", f"{row_id} {retained_artifact} blob mismatch: expected {blob_sha1}, got {actual_blob}")]
                actual_sha256 = hashlib.sha256(blob_bytes).hexdigest()
                if actual_sha256 != sha256:
                    return [Finding("source_blob_sha256_mismatch", f"{row_id} {retained_artifact} source_blob sha256 mismatch: expected {sha256}, got {actual_sha256}")]
                if bounded_verified == "CURRENT":
                    working_sha256, working_problem = _retained_file_sha256(retained_artifact)
                    if working_problem or working_sha256 is None:
                        return [Finding("bounded_current_source_unavailable", f"{row_id} CURRENT evidence cannot read {retained_artifact}: {working_problem}")]
                    if working_sha256 != sha256:
                        return [
                            Finding(
                                "bounded_current_source_drift",
                                f"{row_id} CURRENT evidence for {retained_artifact} has working-tree sha256 "
                                f"{working_sha256}, expected {sha256}",
                            )
                        ]
            elif kind == "file_sha256":
                if not isinstance(sha256, str) or not sha256 or not retained_artifact:
                    return [Finding("file_sha256_evidence_incomplete", f"{location} requires sha256 and retained_artifact")]
                if any(value is not None for value in (commit_sha1, blob_sha1, command, exit_code, unretained_reason)):
                    return [Finding("file_sha256_evidence_inconsistent", f"{location} may carry only retained file SHA-256 evidence")]
                actual_sha256, file_problem = _retained_file_sha256(retained_artifact)
                if file_problem or actual_sha256 is None:
                    return [Finding("file_sha256_unavailable", f"{row_id} {retained_artifact} cannot be read: {file_problem}")]
                if actual_sha256 != sha256:
                    return [Finding("file_sha256_mismatch", f"{row_id} {retained_artifact} file sha256 mismatch: expected {sha256}, got {actual_sha256}")]
            elif kind == "command_result":
                if not isinstance(command, str) or not command.strip() or not isinstance(exit_code, int):
                    return [Finding("command_evidence_incomplete", f"{location} requires an exact command and integer exit_code")]
                if commit_sha1 is not None or blob_sha1 is not None:
                    return [Finding("command_evidence_inconsistent", f"{location} must not impersonate source-blob custody")]
                if retained_artifact:
                    if not isinstance(sha256, str) or not sha256 or unretained_reason is not None:
                        return [Finding("retained_command_evidence_incomplete", f"{location} requires retained artifact SHA-256 and no unretained_reason")]
                    actual_sha256, file_problem = _retained_file_sha256(retained_artifact)
                    if file_problem or actual_sha256 is None:
                        return [Finding("retained_command_evidence_unavailable", f"{row_id} {retained_artifact} cannot be read: {file_problem}")]
                    if actual_sha256 != sha256:
                        return [
                            Finding(
                                "retained_command_evidence_sha256_mismatch",
                                f"{row_id} {retained_artifact} retained command evidence sha256 mismatch: "
                                f"expected {sha256}, got {actual_sha256}",
                            )
                        ]
                else:
                    if sha256 is not None:
                        return [Finding("unretained_evidence_invented_hash", f"{location} cannot carry a transcript SHA-256 without a retained_artifact")]
                    if not isinstance(unretained_reason, str) or not unretained_reason.strip():
                        return [Finding("unretained_evidence_missing_reason", f"{location} requires explicit unretained_reason")]

        if status in TERMINAL_COMPLETION and (integration_open or owner_gated or artifact_gated or terminal_open):
            open_dimensions = [
                name
                for name, value in (
                    ("integration_open", integration_open),
                    ("owner_gated", owner_gated),
                    ("artifact_gated", artifact_gated),
                    ("terminal_open", terminal_open),
                )
                if value
            ]
            return [
                Finding(
                    "terminal_dimension_conflict",
                    f"{row_id} {status} cannot close while {', '.join(f'{name}=true' for name in open_dimensions)}",
                )
            ]
        if status not in TERMINAL_COMPLETION and not terminal_open:
            return [
                Finding(
                    "terminal_dimension_mismatch",
                    f"{row_id} {status} requires terminal_open=true until a terminal completion status is independently reached",
                )
            ]

        milestone_statuses = [m.get("status") for m in row.get("milestones", []) if isinstance(m, dict)]
        if status == "HANDOFF" and any(value in TERMINAL_COMPLETION for value in milestone_statuses):
            completed = next(value for value in milestone_statuses if value in TERMINAL_COMPLETION)
            return [Finding("contradictory_terminal_state", f"{row_id} is HANDOFF while a milestone is {completed}")]

    for row in rows:
        if row.get("status") not in TERMINAL_COMPLETION:
            continue
        row_id = str(row.get("andon_id"))
        for dependency in row.get("dependencies", []):
            dependency_row = by_id.get(dependency)
            dependency_status = dependency_row.get("status") if dependency_row else "MISSING"
            if dependency_status not in TERMINAL_COMPLETION:
                return [Finding("open_dependency", f"{row_id} cannot close because dependency {dependency} is {dependency_status}")]

    milestone_graph: dict[str, list[str]] = {}
    for row in rows:
        for milestone in row.get("milestones", []):
            if not isinstance(milestone, dict) or not isinstance(milestone.get("milestone_id"), str):
                continue
            milestone_graph[milestone["milestone_id"]] = list(milestone.get("depends_on", []))
    for milestone_id, dependencies in milestone_graph.items():
        for dependency in dependencies:
            if dependency not in milestone_graph:
                return [Finding("dangling_milestone_dependency", f"{milestone_id} depends on missing milestone {dependency}")]
    found_cycle = _cycle(milestone_graph)
    if found_cycle:
        return [Finding("milestone_cycle", f"milestone dependency cycle: {' -> '.join(found_cycle)}")]

    if a16:
        milestones = {m.get("milestone_id"): m for m in a16.get("milestones", []) if isinstance(m, dict)}
        bootstrap = milestones.get("A16.bootstrap")
        terminal = milestones.get("A16.terminal")
        if not bootstrap or bootstrap.get("depends_on") != []:
            return [Finding("a16_bootstrap_contract", "A16.bootstrap must exist with no dependencies")]
        if not terminal:
            return [Finding("a16_terminal_contract", "A16.terminal milestone is required")]
        required_terminal = {f"{andon_id}.terminal" for andon_id in document.get("required_andon_ids", []) if andon_id != "A16"}
        actual_terminal = set(terminal.get("depends_on", []))
        if required_terminal and actual_terminal != required_terminal:
            missing = sorted(required_terminal - actual_terminal)
            extra = sorted(actual_terminal - required_terminal)
            return [Finding("a16_terminal_contract", f"A16.terminal dependency mismatch; missing={missing}, extra={extra}")]

    for row in rows:
        if row.get("status") in {"HANDOFF", "BLOCKED"} and not str(row.get("next_action", "")).strip():
            return [Finding("missing_next_action", f"{row.get('andon_id')} {row.get('status')} requires a concrete next_action")]
    return []


def validate_ledger(document: Any, *, expected_head: str | None = None) -> list[Finding]:
    schema = read_json(SCHEMA_PATH)
    errors = schema_findings(document, schema, schema)
    if errors:
        return [Finding("schema_contract", message) for message in errors]
    return semantic_findings(document, expected_head=expected_head)


def diagnostic(path: Path, finding: Finding) -> dict[str, Any]:
    return {
        "artifact": rel(path),
        "checker": CHECKER,
        "checker_id": CHECKER_ID,
        "downstream_invalidated": DOWNSTREAM_INVALIDATED,
        "stage": STAGE,
        "earliest_stage": STAGE,
        "exit_category": EXIT_CATEGORY,
        "exit_code": 1,
        "failure_class": finding.failure_class,
        "message": finding.message,
    }


def run_one(path: Path, *, explain: bool, expected_head: str | None = None) -> int:
    try:
        document = materialize_fixture(path, LIVE_LEDGER)
        findings = validate_ledger(document, expected_head=expected_head)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        findings = [Finding("fixture_or_json", str(exc))]
    if findings:
        first = findings[0]
        if explain:
            print(json.dumps(diagnostic(path, first), sort_keys=True, ensure_ascii=False))
        else:
            print(f"andon closure ledger: FAIL [{first.failure_class}]: {first.message}")
        return 1
    if explain:
        print(json.dumps({"artifact": rel(path), "checker": CHECKER, "status": "PASS"}, sort_keys=True))
    else:
        print(f"andon closure ledger: PASS ({rel(path)})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?", help="ledger or checker fixture JSON")
    parser.add_argument("--ledger", help="canonical closure-ledger JSON")
    parser.add_argument("--explain", action="store_true", help="emit one deterministic JSON result")
    parser.add_argument("--self-test", action="store_true", help="run fixture-based tests")
    return parser


def expectation_problems(
    fixture: Path,
    finding: Finding,
    *,
    checker_id: str,
    downstream_invalidated: list[str],
) -> list[str]:
    expectation_path = fixture.with_suffix(".expectation.json")
    try:
        expectation = read_json(expectation_path)
    except ValueError as exc:
        return [str(exc)]
    problems: list[str] = []
    schema = read_json(EXPECTATION_SCHEMA_PATH)
    schema_errors = schema_findings(expectation, schema, schema)
    problems.extend(f"{rel(expectation_path)}: {message}" for message in schema_errors)
    expected_values = {
        "fixture": fixture.name,
        "expected_checker_id": checker_id,
        "expected_exit_category": EXIT_CATEGORY,
        "expected_exit_code": 1,
        "expected_earliest_stage": STAGE,
        "expected_failure_class": finding.failure_class,
        "expected_downstream_invalidated": downstream_invalidated,
    }
    for key, expected in expected_values.items():
        if expectation.get(key) != expected:
            problems.append(f"{rel(expectation_path)}: {key} expected {expected!r}, got {expectation.get(key)!r}")
    diagnostic_text = json.dumps(
        {
            "checker_id": checker_id,
            "earliest_stage": STAGE,
            "exit_category": EXIT_CATEGORY,
            "exit_code": 1,
            "failure_class": finding.failure_class,
            "message": finding.message,
            "downstream_invalidated": downstream_invalidated,
        },
        sort_keys=True,
    )
    for marker in expectation.get("required_diagnostic_markers", []):
        if marker not in diagnostic_text:
            problems.append(f"{rel(fixture)}: required diagnostic marker {marker!r} absent")
    return problems


def self_test() -> int:
    problems: list[str] = []
    # Fixture semantics are pinned to the canonical ledger's declared source
    # boundary so a later repository commit does not turn every focused fixture
    # into the same stale-head failure.  The live CLI and renderer continue to
    # compare the canonical ledger to git HEAD without an allow-stale path.
    head = str(read_json(LIVE_LEDGER).get("source_head", ""))
    valid_files = sorted((FIXTURE_ROOT / "valid").glob("*.json"))
    invalid_files = sorted(
        path for path in (FIXTURE_ROOT / "invalid").glob("*.json") if not path.name.endswith(".expectation.json")
    )
    for fixture in valid_files:
        try:
            findings = validate_ledger(materialize_fixture(fixture, LIVE_LEDGER), expected_head=head)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            problems.append(f"{rel(fixture)}: {exc}")
            continue
        if findings:
            problems.append(f"{rel(fixture)}: valid fixture rejected [{findings[0].failure_class}] {findings[0].message}")
    for fixture in invalid_files:
        try:
            findings = validate_ledger(materialize_fixture(fixture, LIVE_LEDGER), expected_head=head)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            findings = [Finding("fixture_or_json", str(exc))]
        if not findings:
            problems.append(f"{rel(fixture)}: invalid fixture survived")
            continue
        problems.extend(
            expectation_problems(
                fixture,
                findings[0],
                checker_id=CHECKER_ID,
                downstream_invalidated=DOWNSTREAM_INVALIDATED,
            )
        )
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        print(f"andon closure ledger self-test: FAIL ({len(problems)} problem(s))")
        return 1
    print(f"andon closure ledger self-test: PASS ({len(valid_files)} valid, {len(invalid_files)} invalid)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        return self_test()
    selected = args.ledger or args.artifact
    if not selected:
        selected = rel(LIVE_LEDGER)
    return run_one((ROOT / selected).resolve() if not Path(selected).is_absolute() else Path(selected), explain=args.explain, expected_head=git_head())


if __name__ == "__main__":
    raise SystemExit(main())
