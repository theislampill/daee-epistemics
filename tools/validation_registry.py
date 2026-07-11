#!/usr/bin/env python3
"""Pure helpers for DAEE validation registry and replay-verdict integrity."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from contract_validation import (
    PathCustodyError,
    SchemaDefinitionError,
    resolve_repo_path,
    validate_schema_subset,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_REL = Path("tools/validation-registry.json")
REGISTRY_PATH = ROOT / REGISTRY_REL
REGISTRY_SCHEMA_REL = Path("schema/validation-registry.schema.json")
VERDICT_SCHEMA_REL = Path("schema/checker-replay-verdict.schema.json")
EXPECTATION_SCHEMA_REL = Path("schema/negative-fixture-expectation.schema.json")
ARTIFACT_TYPES = (
    "output-md", "input-output-pair", "staged-handoff-record", "state-capsule-sequence",
    "prompt-context-manifest", "proof-sidecar-set", "retained-case-manifest",
    "captured-output-custody-manifest",
)
PROFILE_IDS = ("stage07-release", "captured-output-structural", "stage08-proof-surface", "promotion", "scorecard", "advisory")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_POLICY = re.compile(r"(?m)^\s*(BATTERY|DETECTORS|VALIDATORS)\s*(?::[^=]+)?=\s*\[")
_RELEASE_VALIDATOR_MARKER = "def run_release_" "validators("


@dataclass(frozen=True)
class Finding:
    failure_class: str
    message: str
    failure_subcode: str = "registry-integrity"


def _safe(candidate: str | Path, *, root: Path = ROOT, must_exist: bool = False, expect_file: bool = False, expect_dir: bool = False) -> Path:
    return resolve_repo_path(root, candidate, must_exist=must_exist, expect_file=expect_file, expect_dir=expect_dir)


def _repo_relative(path: Path, *, root: Path = ROOT) -> Path:
    return path.resolve().relative_to(root.resolve())


def read_json(path: str | Path, *, root: Path = ROOT) -> Any:
    resolved = _safe(path, root=root, must_exist=True, expect_file=True)
    return json.loads(resolved.read_text(encoding="utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash a path already resolved through the custody helper."""
    return sha256_bytes(path.read_bytes())


def hash_repo_file(path: str | Path, *, root: Path = ROOT) -> str:
    return sha256_file(_safe(path, root=root, must_exist=True, expect_file=True))


def canonical_sha256(value: Any) -> str:
    return sha256_bytes((json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8"))


def rel(path: Path, *, root: Path = ROOT) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _schema_subcode(keyword: str) -> str:
    return {
        "required": "required-field",
        "additionalProperties": "additional-property",
        "uniqueItems": "unique-items",
    }.get(keyword, f"schema-{keyword.lower()}")


def schema_findings(document: Any, schema_path: str | Path, *, root: Path = ROOT) -> list[Finding]:
    try:
        schema = read_json(schema_path, root=root)
        issues = validate_schema_subset(document, schema)
    except (PathCustodyError, SchemaDefinitionError, json.JSONDecodeError, OSError, ValueError) as exc:
        return [Finding("schema_definition", str(exc), "schema-definition")]
    return [Finding("schema_contract", f"{issue.path}: [{issue.keyword}] {issue.message}", _schema_subcode(issue.keyword)) for issue in issues]


def load_registry(path: str | Path = REGISTRY_REL, *, root: Path = ROOT) -> dict[str, Any]:
    value = read_json(path, root=root)
    if not isinstance(value, dict):
        raise ValueError("validation registry root must be an object")
    problems = schema_findings(value, REGISTRY_SCHEMA_REL, root=root)
    if problems:
        raise ValueError(problems[0].message)
    return value


def registry_hash(path: str | Path = REGISTRY_REL, *, root: Path = ROOT) -> str:
    return hash_repo_file(path, root=root)


def _unique_index(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key, ""))
        if value in result:
            raise ValueError(f"duplicate {key}: {value}")
        result[value] = row
    return result


def checker_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return _unique_index((row for row in registry.get("checkers", []) if isinstance(row, dict)), "checker_id")


def profile_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return _unique_index((row for row in registry.get("profiles", []) if isinstance(row, dict)), "profile_id")


def discover_output_tools(root: Path = ROOT) -> set[str]:
    found: set[str] = set()
    for path in sorted((root / "tools").glob("check_*.py")):
        resolved = _safe(path.relative_to(root), root=root, must_exist=True, expect_file=True)
        text = resolved.read_text(encoding="utf-8", errors="replace")
        if "--outputs" in text:
            found.add(path.relative_to(root).as_posix())
    return found


def discover_validation_consumers(root: Path = ROOT) -> set[str]:
    found: set[str] = set()
    for path in sorted((root / "tools").glob("*.py")):
        resolved = _safe(path.relative_to(root), root=root, must_exist=True, expect_file=True)
        text = resolved.read_text(encoding="utf-8", errors="replace")
        if _PRIVATE_POLICY.search(text) or _RELEASE_VALIDATOR_MARKER in text:
            found.add(path.relative_to(root).as_posix())
    return found


def _source_has_private_policy(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return bool(_PRIVATE_POLICY.search(text)) or _RELEASE_VALIDATOR_MARKER in text


def _path_finding(exc: PathCustodyError, context: str) -> Finding:
    if exc.subcode in {"missing-path", "not-file"}:
        return Finding("nonexistent_checker_tool" if "checker" in context else "unregistered_consumer", f"{context}: {exc}", "missing-tool" if "checker" in context else "missing-consumer")
    return Finding("path_custody", f"{context}: {exc}", exc.subcode)


def validate_registry(registry: Any, *, root: Path = ROOT, scan_repo: bool = True) -> list[Finding]:
    schema_errors = schema_findings(registry, REGISTRY_SCHEMA_REL, root=root)
    if schema_errors:
        return schema_errors
    assert isinstance(registry, dict)
    findings: list[Finding] = []
    if tuple(registry["artifact_types"]) != ARTIFACT_TYPES:
        findings.append(Finding("artifact_type_contract", "artifact_types must be the canonical ordered eight", "artifact-types"))
    checkers = registry["checkers"]
    ids = [str(row["checker_id"]) for row in checkers]
    if len(ids) != len(set(ids)):
        return [Finding("duplicate_checker_id", "checker IDs must be unique", "checker-id")]
    aliases: dict[str, str] = {}
    deprecated: dict[str, str] = {}
    for row in checkers:
        checker_id = str(row["checker_id"])
        try:
            source = _safe(row["source_path"], root=root, must_exist=True, expect_file=True)
        except PathCustodyError as exc:
            return [_path_finding(exc, f"checker {checker_id}")]
        if sha256_file(source) != row["source_sha256"]:
            findings.append(Finding("checker_source_hash_drift", f"{checker_id}: source hash drift for {row['source_path']}", "tool-hash-drift"))
        if not set(row["artifact_applicability"]).issubset(ARTIFACT_TYPES):
            findings.append(Finding("unknown_artifact_type", f"{checker_id}: unknown artifact applicability", "artifact-applicability"))
        for alias in row.get("aliases", []):
            if alias in aliases or alias in ids or alias in deprecated:
                return [Finding("duplicate_checker_alias", f"duplicate or colliding alias {alias}", "checker-alias")]
            aliases[str(alias)] = checker_id
        for alias in row.get("deprecated_aliases", []):
            if alias in deprecated or alias in aliases or alias in ids:
                return [Finding("duplicate_checker_alias", f"duplicate or colliding deprecated alias {alias}", "checker-alias")]
            deprecated[str(alias)] = checker_id
    by_id = checker_map(registry)
    profiles = registry["profiles"]
    pids = [str(row["profile_id"]) for row in profiles]
    if len(pids) != len(set(pids)):
        return [Finding("duplicate_profile_id", "profile IDs must be unique", "profile-id")]
    if tuple(pids) != PROFILE_IDS:
        findings.append(Finding("profile_contract", "profiles must be the canonical ordered six", "profiles"))
    for profile in profiles:
        pid = str(profile["profile_id"])
        requirement_ids = [str(row["checker_id"]) for row in profile["requirements"]]
        if len(requirement_ids) != len(set(requirement_ids)):
            findings.append(Finding("duplicate_profile_requirement", f"{pid}: checker requirement IDs must be unique", "profile-requirement"))
        if not set(profile["artifact_types"]).issubset(ARTIFACT_TYPES):
            findings.append(Finding("unknown_artifact_type", f"{pid}: unknown profile artifact type", "artifact-applicability"))
        for requirement in profile["requirements"]:
            cid = str(requirement["checker_id"])
            if cid in deprecated:
                findings.append(Finding("deprecated_checker_alias", f"{pid}: deprecated checker alias {cid}", "deprecated-alias"))
            elif cid not in by_id:
                findings.append(Finding("unknown_checker_id", f"{pid}: unknown checker {cid}", "unknown-checker"))
            elif requirement["required"] and by_id[cid]["requirement_status"] == "inapplicable":
                findings.append(Finding("profile_required_not_run", f"{pid}: required checker {cid} is inapplicable", "required-not-run"))
    consumers = registry["consumers"]
    consumer_ids = [str(row["consumer_id"]) for row in consumers]
    if len(consumer_ids) != len(set(consumer_ids)):
        return [Finding("duplicate_consumer_id", "consumer IDs must be unique", "consumer-id")]
    registered_consumer_paths: set[str] = set()
    for consumer in consumers:
        try:
            path = _safe(consumer["source_path"], root=root, must_exist=True, expect_file=True)
        except PathCustodyError as exc:
            finding = _path_finding(exc, f"consumer {consumer['consumer_id']}")
            if finding.failure_class == "nonexistent_checker_tool":
                finding = Finding("unregistered_consumer", finding.message, "missing-consumer")
            return [finding]
        registered_consumer_paths.add(str(consumer["source_path"]))
        if consumer["profile_id"] not in pids:
            findings.append(Finding("unknown_profile", f"{consumer['consumer_id']}: unknown profile {consumer['profile_id']}", "unknown-profile"))
        if scan_repo and (consumer["policy_source"] != "registry" or _source_has_private_policy(path)):
            findings.append(Finding("private_consumer_battery", f"{consumer['consumer_id']}: private checker policy remains in {consumer['source_path']}", "private-battery"))
    if scan_repo:
        registered_paths = {str(row["source_path"]) for row in checkers}
        for missing in sorted(discover_output_tools(root) - registered_paths):
            findings.append(Finding("unregistered_output_checker", f"output-capable checker is unregistered: {missing}", "unregistered-output-checker"))
        for missing in sorted(discover_validation_consumers(root) - registered_consumer_paths):
            findings.append(Finding("unregistered_consumer", f"validation consumer is unregistered: {missing}", "unregistered-consumer"))
    return findings


def _result_tuple_finding(row: dict[str, Any]) -> Finding | None:
    cid = str(row["checker_id"])
    status, category = row["execution_status"], row["exit_category"]
    exit_code, diag = row["exit_code"], row["diagnostic"]
    flags = (row["timeout"], row["crash"], row["usage_error"], row["malformed_diagnostic"])
    expectation = row["expectation_status"]
    if category == "accepted":
        valid = status == "completed" and exit_code == 0 and not any(flags) and diag is None and expectation == "ACCEPTED"
        return None if valid else Finding("result_tuple_invalid", f"{cid}: accepted requires completed/exit-0/no flags/no diagnostic/ACCEPTED", "result-tuple")
    if category == "structural-rejection":
        valid = status == "completed" and exit_code == 1 and not any(flags) and isinstance(diag, dict) and expectation in {"REJECTED_EXPECTED", "REJECTED_WRONG_REASON"}
        return None if valid else Finding("malformed_diagnostic", f"{cid}: structural rejection requires completed/exit-1/exact diagnostic", "malformed-diagnostic")
    if category == "usage-error":
        valid = status == "completed" and exit_code == 2 and flags == (False, False, True, False) and diag is None and expectation == "INDETERMINATE"
        return Finding("usage_error_not_rejection", f"{cid}: usage error is invalid negative evidence" if valid else f"{cid}: usage tuple is malformed", "usage-error")
    if category == "timeout":
        valid = status == "timeout" and exit_code is None and flags == (True, False, False, False) and diag is None and expectation == "INDETERMINATE"
        return Finding("infrastructure_not_rejection", f"{cid}: timeout is {'valid infrastructure evidence' if valid else 'a malformed tuple'}", "timeout")
    if category == "crash":
        valid = status == "crashed" and isinstance(exit_code, int) and exit_code != 0 and flags == (False, True, False, False) and diag is None and expectation == "INDETERMINATE"
        return Finding("infrastructure_not_rejection", f"{cid}: crash is {'valid infrastructure evidence' if valid else 'a malformed tuple'}", "crash")
    if category == "malformed-diagnostic":
        valid = status == "completed" and exit_code == 1 and flags == (False, False, False, True) and diag is None and expectation == "INDETERMINATE"
        return Finding("malformed_diagnostic", f"{cid}: diagnostic is {'malformed' if valid else 'an invalid tuple'}", "malformed-diagnostic")
    if category == "unavailable":
        return Finding("infrastructure_not_rejection", f"{cid}: unavailable checker cannot satisfy evidence", "unavailable")
    if category == "not-run":
        return Finding("profile_required_not_run", f"{cid}: checker did not run", "required-not-run")
    return Finding("result_tuple_invalid", f"{cid}: unknown result tuple", "result-tuple")


def _aggregate_status(verdict: dict[str, Any], profile: dict[str, Any], results: list[dict[str, Any]]) -> str:
    by_id = {str(row["checker_id"]): row for row in results}
    required = [str(row["checker_id"]) for row in profile["requirements"] if row["required"]]
    if any(cid not in by_id or by_id[cid]["execution_status"] == "not-run" for cid in required):
        return "QUARANTINED_INCOMPLETE_EVIDENCE"
    if not results:
        return "NOT_RUN"
    categories = {str(row["exit_category"]) for row in results}
    if categories & {"usage-error", "timeout", "crash", "malformed-diagnostic", "unavailable"}:
        return "INFRASTRUCTURE_ERROR"
    if "not-run" in categories:
        return "QUARANTINED_INCOMPLETE_EVIDENCE"
    rejections = [row for row in results if row["exit_category"] == "structural-rejection"]
    if any(row["expectation_status"] != "REJECTED_EXPECTED" for row in rejections):
        return "QUARANTINED_INCOMPLETE_EVIDENCE"
    if rejections:
        return "FAIL_STRUCTURAL"
    if all(row["exit_category"] == "accepted" for row in results) and all(by_id[cid]["exit_category"] == "accepted" for cid in required):
        return "PASS_STRUCTURAL"
    return "QUARANTINED_INCOMPLETE_EVIDENCE"


def validate_verdict(verdict: Any, registry: dict[str, Any], *, root: Path = ROOT, verify_files: bool = True) -> list[Finding]:
    schema_errors = schema_findings(verdict, VERDICT_SCHEMA_REL, root=root)
    if schema_errors:
        return schema_errors
    assert isinstance(verdict, dict)
    registry_errors = validate_registry(registry, root=root, scan_repo=False)
    if registry_errors:
        return registry_errors
    try:
        registry_path = _safe(verdict["registry_path"], root=root, must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        return [Finding("path_custody", f"registry_path: {exc}", "registry-path")]
    try:
        referenced_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [Finding("malformed_registry", str(exc), "registry-json")]
    if referenced_registry != registry:
        return [Finding("registry_object_path_mismatch", "referenced registry bytes are not the registry object used for validation", "registry-object-split")]
    if verdict["registry_sha256"] != sha256_file(registry_path):
        return [Finding("registry_hash_drift", "verdict registry hash does not match referenced registry bytes", "registry-hash-drift")]
    profiles = profile_map(registry)
    profile = profiles.get(str(verdict["selected_profile"]))
    if not profile:
        return [Finding("unknown_profile", f"unknown selected profile {verdict['selected_profile']}", "unknown-profile")]
    artifacts = verdict["artifacts"]
    roles = [str(row["role"]) for row in artifacts]
    paths = [str(row["path"]) for row in artifacts]
    if len(roles) != len(set(roles)):
        return [Finding("duplicate_artifact_role", "artifact roles must be unique", "artifact-role")]
    if len(paths) != len(set(paths)):
        return [Finding("duplicate_artifact_path", "artifact paths must be unique", "artifact-path")]
    if roles.count("input") != 1 or roles.count("output") != 1:
        return [Finding("artifact_role_contract", "verdict requires exactly one input and one output artifact", "input-output-role")]
    for row in artifacts:
        if row["artifact_type"] not in ARTIFACT_TYPES:
            return [Finding("unknown_artifact_type", f"artifact {row['role']}: unknown type {row['artifact_type']}", "artifact-applicability")]
        try:
            path = _safe(row["path"], root=root, must_exist=verify_files, expect_file=verify_files)
        except PathCustodyError as exc:
            return [Finding("path_custody", f"artifact {row['role']}: {exc}", "artifact-path")]
        if verify_files and sha256_file(path) != row["sha256"]:
            failure_class = "verdict_output_hash_drift" if row["role"] == "output" else "artifact_hash_drift"
            return [Finding(failure_class, f"bound artifact drift: {row['path']}", "artifact-hash-drift")]
    results = verdict["checker_results"]
    result_ids = [str(row["checker_id"]) for row in results]
    if len(result_ids) != len(set(result_ids)):
        return [Finding("duplicate_checker_result", "checker-result IDs must be unique", "checker-result-id")]
    cmap = checker_map(registry)
    findings: list[Finding] = []
    for row in results:
        cid = str(row["checker_id"])
        checker = cmap.get(cid)
        if checker is None:
            return [Finding("unknown_checker_id", f"verdict references unknown checker {cid}", "unknown-checker")]
        try:
            tool_path = _safe(row["tool_path"], root=root, must_exist=True, expect_file=True)
        except PathCustodyError as exc:
            return [Finding("path_custody", f"checker result {cid}: {exc}", "checker-source-path")]
        if row["tool_path"] != checker["source_path"] or row["tool_sha256"] != checker["source_sha256"] or sha256_file(tool_path) != row["tool_sha256"]:
            return [Finding("checker_source_hash_drift", f"{cid}: verdict tool identity drift", "tool-hash-drift")]
        bound_rows = [
            artifact for artifact in artifacts
            if artifact["sha256"] == row["artifact_sha256"] and artifact["artifact_type"] == row["artifact_type"]
        ]
        if len(bound_rows) != 1:
            return [Finding("checker_artifact_hash_drift", f"{cid}: result artifact hash/type is not bound", "checker-artifact-hash")]
        bound = bound_rows[0]
        if row["artifact_type"] not in checker["artifact_applicability"]:
            return [Finding("checker_artifact_inapplicable", f"{cid}: artifact type {row['artifact_type']} is not applicable", "artifact-applicability")]
        if row["artifact_type"] not in profile["artifact_types"]:
            return [Finding("profile_artifact_inapplicable", f"{cid}: artifact type {row['artifact_type']} is outside profile {profile['profile_id']}", "profile-artifact")]
        tuple_finding = _result_tuple_finding(row)
        if tuple_finding is not None:
            findings.append(tuple_finding)
        if row["exit_category"] not in checker["accepted_exit_categories"]:
            findings.append(Finding("exit_category_not_registered", f"{cid}: category {row['exit_category']} is not accepted by registry", "exit-category"))
        readback_paths = [str(item["path"]) for item in row["forbidden_artifact_readback"]]
        if len(readback_paths) != len(set(readback_paths)):
            return [Finding("duplicate_forbidden_readback_path", f"{cid}: forbidden readback paths must be unique", "forbidden-readback-path")]
        for item in row["forbidden_artifact_readback"]:
            try:
                path = _safe(item["path"], root=root, must_exist=False)
            except PathCustodyError as exc:
                return [Finding("path_custody", f"forbidden artifact {item['path']}: {exc}", "forbidden-artifact-path")]
            actual_exists = path.exists()
            if bool(item["exists"]) != actual_exists:
                return [Finding("forbidden_artifact_readback_mismatch", f"{cid}: recorded readback differs for {item['path']}", "forbidden-readback")]
            if actual_exists:
                return [Finding("forbidden_artifact_exists", f"{cid}: forbidden downstream artifact exists: {item['path']}", "forbidden-artifact")]
    if findings:
        return findings
    by_result = {str(row["checker_id"]): row for row in results}
    for requirement in profile["requirements"]:
        if requirement["required"] and (requirement["checker_id"] not in by_result or by_result[requirement["checker_id"]]["execution_status"] == "not-run"):
            return [Finding("profile_required_not_run", f"required checker {requirement['checker_id']} did not run", "required-not-run")]
    recomputed = _aggregate_status(verdict, profile, results)
    if verdict["aggregate_status"] != recomputed:
        return [Finding("aggregate_status_mismatch", f"declared {verdict['aggregate_status']} but recomputed {recomputed}", "aggregate-status")]
    rejections = [row for row in results if row["exit_category"] == "structural-rejection" and row["expectation_status"] == "REJECTED_EXPECTED"]
    if recomputed == "FAIL_STRUCTURAL":
        if len(rejections) != 1 or verdict["mutation_fault_id"] != rejections[0]["diagnostic"]["failure_subcode"]:
            return [Finding("different_active_fault", "FAIL_STRUCTURAL mutation identity must equal the sole expected rejection subcode", "active-fault-mismatch")]
    elif verdict["mutation_fault_id"] is not None:
        return [Finding("mutation_fault_status_mismatch", "mutation_fault_id is allowed only for one expected structural rejection", "mutation-fault")]
    nonclaims = " ".join(verdict["structural_non_claims"]).lower()
    if not all(token in nonclaims for token in ("structural", "semantic", "model")):
        return [Finding("structural_non_claims_missing", "verdict must disclaim semantic and model proof", "non-claims")]
    return findings


def materialize_fixture(path: str | Path, *, root: Path = ROOT, _seen: set[str] | None = None) -> dict[str, Any]:
    resolved = _safe(path, root=root, must_exist=True, expect_file=True)
    relative = _repo_relative(resolved, root=root)
    seen = set() if _seen is None else set(_seen)
    key = relative.as_posix()
    if key in seen:
        raise ValueError(f"mutation base cycle at {key}")
    seen.add(key)
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("fixture_schema") != "daee-validation-integrity-mutation-v1":
        return raw
    base_value = raw.get("base")
    if not isinstance(base_value, str) or not base_value:
        raise ValueError("mutation base must be a non-empty relative path")
    try:
        base = _safe(relative.parent / Path(base_value), root=root, must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        raise PathCustodyError(f"mutation base: {exc}", subcode="mutation-base") from exc
    value = copy.deepcopy(materialize_fixture(_repo_relative(base, root=root), root=root, _seen=seen))
    for operation in raw.get("operations", []):
        parts = [part.replace("~1", "/").replace("~0", "~") for part in str(operation["path"]).strip("/").split("/") if part]
        if not parts:
            raise ValueError("mutation operation path must not be empty")
        cursor: Any = value
        for part in parts[:-1]:
            cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
        key_part = parts[-1]
        if operation["op"] == "set":
            if isinstance(cursor, list):
                cursor[int(key_part)] = operation.get("value")
            else:
                cursor[key_part] = operation.get("value")
        elif operation["op"] == "delete":
            if isinstance(cursor, list):
                del cursor[int(key_part)]
            else:
                cursor.pop(key_part, None)
        else:
            raise ValueError(f"unsupported fixture operation {operation['op']}")
    return value


def hydrate_fixture(value: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    value = copy.deepcopy(value)
    registry_value = value.get("registry_path", REGISTRY_REL.as_posix())
    reg_path = _safe(registry_value, root=root, must_exist=True, expect_file=True)
    if value.get("registry_sha256") == "AUTO":
        value["registry_sha256"] = sha256_file(reg_path)
    for row in value.get("artifacts", []):
        path = _safe(row.get("path", ""), root=root, must_exist=True, expect_file=True)
        if row.get("sha256") == "AUTO":
            row["sha256"] = sha256_file(path)
    roles = [str(row.get("role")) for row in value.get("artifacts", [])]
    if len(roles) != len(set(roles)):
        raise ValueError("cannot hydrate duplicate artifact roles")
    artifact_map = {str(row["role"]): row for row in value.get("artifacts", [])}
    cmap = checker_map(load_registry(_repo_relative(reg_path, root=root), root=root))
    for row in value.get("checker_results", []):
        checker = cmap.get(str(row.get("checker_id")), {})
        if row.get("tool_sha256") == "AUTO":
            row["tool_sha256"] = checker.get("source_sha256", "0" * 64)
        if row.get("artifact_sha256") == "AUTO":
            row["artifact_sha256"] = artifact_map.get("output", {}).get("sha256", "0" * 64)
    return value


def scan_anti_bank(paths: Iterable[Path], *, root: Path = ROOT) -> list[str]:
    banned_terms = [
        "gate" + "88-", "expected" + "_answer", "expected" + "_topology",
        "maximum" + "_cycles", "maximum" + "_invocations", "fixed" + "_burden",
        "fixed" + "_submove", "fixed" + "_byte", "stop" + "-after-n",
    ]
    problems: list[str] = []
    for path in paths:
        resolved = _safe(path, root=root, must_exist=True, expect_file=True)
        text = resolved.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower().replace("-", "_").replace(" ", "_")
        match = next((term for term in banned_terms if term.replace("-", "_") in lowered), None)
        if match:
            problems.append(f"{rel(resolved, root=root)}: prohibited answer/quota policy token {match!r}")
    return problems


def _self_test() -> int:
    registry = load_registry()
    findings = validate_registry(registry, root=ROOT, scan_repo=False)
    if findings:
        for finding in findings:
            print(f"FAIL: [{finding.failure_class}/{finding.failure_subcode}] {finding.message}")
        return 1
    print(json.dumps({"artifact_types": len(ARTIFACT_TYPES), "checkers": len(registry["checkers"]), "profiles": len(registry["profiles"]), "status": "PASS"}, sort_keys=True))
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.error("only --self-test is supported; use check_validation_registry.py for validation")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
