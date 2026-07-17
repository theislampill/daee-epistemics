#!/usr/bin/env python3
"""Validate derived no-model source preflight and candidate maturity verdicts."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from a16_immutable_custody import (
    CustodyError,
    canonical_json_bytes,
    claim_json_once,
    exclusive_writer_lock,
    resolve_contained_path,
    strict_snapshot,
)
from build_candidate_package_record import validate_candidate_readiness
from check_ci_readback import validate_receipt
from check_evidence_retention_manifest import validate_export
from check_model_smoke_escape_registry import validate_for_candidate_maturity, validate_registry
from check_package_harness_parity import Failure as PackageParityFailure
from check_package_harness_parity import validate as validate_package_parity
from check_runtime_context_delivery import Failure as RuntimeContextFailure
from check_runtime_context_delivery import validate as validate_runtime_context
from check_smoke_matrix_manifest import validate_manifest as validate_smoke_manifest
from contract_validation import validate_schema_subset
from source_provenance import (
    _extract_source_binding_bytes,
    strict_json_loads,
    validate_carrier_document,
)
from validation_registry import Finding

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema/no-model-candidate-maturity.schema.json"
CHECKER_ID = "no-model-candidate-maturity"
DOWNSTREAM = ["candidate-build", "candidate-maturity", "paid-dispatch"]
ESCAPE_SCHEMA_PATH = "schema/model-smoke-escape.schema.json"
ESCAPE_CHECKER_PATH = "tools/check_model_smoke_escape_registry.py"
ESCAPE_LIVE_REGISTRY_PATH = "docs/audits/v0.4.6.0-wip-model-smoke-escape-registry.json"
REVIEW_PROTOCOL_PATH = "tests/smoke-matrix/reviewed-five-smoke-protocol.json"
CI_TEST_FIXTURE_PATH = "tests/ci-readback/valid/required-checks-bound-to-pushed-sha.json"
REGISTRY_ROLE_PATHS = {
    "input": "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json",
    "validation": "tools/validation-registry.json",
    "producer": "tools/producer-contract-registry.json",
    "review_protocol": REVIEW_PROTOCOL_PATH,
}
CLOSURE_ROLE_PATHS = {
    "closure_ledger": "docs/audits/v0.4.6.0-wip-andon-closure-ledger.json",
    "contract_registry": "docs/audits/v0.4.6.0-wip-andon-contract-registry.json",
    "architecture_ledger": "docs/audits/v0.4.6.0-wip-architecture-decisions.json",
}
CANDIDATE_INPUT_KEYS = {
    "source_preflight",
    "candidate_root",
    "package_evidence_root",
    "runtime_context",
    "package_harness_parity",
    "retention_custody_root",
    "retention_final_directory",
    "candidate_readiness_review",
}
IMPLEMENTATION_OWNER_IDENTITY = "/root/task5_retention"
REVIEW_AUTHORIZATION_ISSUER = "/root"
TASK_IDENTITY_RE = re.compile(r"^/root(?:/[a-z0-9][a-z0-9_-]{0,63})*$")


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _unsigned_hash(value: dict[str, Any], field: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def _verify_ref(root: Path, reference: Any, label: str) -> bytes:
    if not isinstance(reference, dict):
        raise ValueError(f"{label} reference is not an object")
    try:
        path = resolve_contained_path(root, reference["path"], must_exist=True)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{label} path custody failed: {exc}") from exc
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{label} is not one regular file")
    raw = path.read_bytes()
    if reference.get("byte_count") != len(raw):
        raise ValueError(f"{label} byte_count drift")
    if reference.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError(f"{label} hash drift")
    return raw


def _load_ref(root: Path, reference: Any, label: str) -> tuple[Any, bytes]:
    raw = _verify_ref(root, reference, label)
    try:
        return strict_json_loads(raw, label=label), raw
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{label} is not strict JSON: {exc}") from exc


def _file_sha256(root: Path, relative: str) -> str:
    path = resolve_contained_path(root, relative, must_exist=True)
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"required live file is not regular: {relative}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_identity(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "repository": receipt["repository"]["full_name"],
        "remote_url": receipt["repository"]["remote_url"],
        "branch": receipt["repository"]["branch"],
        "ref": receipt["repository"]["ref"],
        "commit_sha": receipt["source"]["commit_sha"],
        "tree_oid": receipt["source"]["tree_oid"],
    }


def _source_scope_sha256(source: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes({
        "repository": source["repository"],
        "commit_sha": source["commit_sha"],
        "tree_oid": source["tree_oid"],
    })).hexdigest()


def _review_authorization_id(value: dict[str, Any]) -> str:
    unsigned = {key: copy.deepcopy(item) for key, item in value.items() if key != "authorization_id"}
    return hashlib.sha256(
        b"daee-task5-independent-review-authorization-v1\0" + canonical_json_bytes(unsigned)
    ).hexdigest()


def _review_claim_locator(
    authorization_reference: dict[str, Any],
    scope: str,
    review_id: str,
) -> str:
    authorization_path = authorization_reference.get("path")
    if not isinstance(authorization_path, str) or not authorization_path:
        raise ValueError("Task5 review authorization locator is absent")
    parent = PurePosixPath(authorization_path).parent
    review_digest = hashlib.sha256(review_id.encode("utf-8")).hexdigest()
    return (parent / "claims" / f"{scope}-{review_digest}.claim.json").as_posix()


def _review_consumption_claim_id(value: dict[str, Any]) -> str:
    unsigned = {key: copy.deepcopy(item) for key, item in value.items() if key != "claim_id"}
    return hashlib.sha256(
        b"daee-task5-review-authorization-consumption-v1\0" + canonical_json_bytes(unsigned)
    ).hexdigest()


def _review_consumption_claim(
    review: dict[str, Any],
    authorization: dict[str, Any],
    *,
    scope: str,
    review_reference: dict[str, Any],
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "daee-task5-review-authorization-consumption-v1",
        "claim_id": "",
        "scope": scope,
        "authorization_id": authorization["authorization_id"],
        "authorization": copy.deepcopy(review["review_authorization"]),
        "review_id": review["review_id"],
        "reviewer_identity": review["independent_reviewer"],
        "review": copy.deepcopy(review_reference),
        "authorization_issued_at": authorization["issued_at"],
        "reviewed_at": review["reviewed_at"],
        "review_sha256": review["review_sha256"],
        "one_use": True,
        "owner_acceptance": False,
        "model_execution_authorized": False,
        "terminal_claim": False,
    }
    value["claim_id"] = _review_consumption_claim_id(value)
    return value


def _validate_review_consumption_claim(
    value: Any,
    expected: dict[str, Any],
) -> None:
    schema = _schema()
    issues = validate_schema_subset(
        value,
        {"$ref": "#/$defs/task5ReviewConsumptionClaim", "$defs": schema["$defs"]},
    )
    if issues:
        raise ValueError(f"Task5 review consumption claim schema failed: {issues[0].message}")
    assert isinstance(value, dict)
    if value["claim_id"] != _review_consumption_claim_id(value):
        raise ValueError("Task5 review consumption claim self-hash drifted")
    if value != expected:
        raise ValueError("Task5 review consumption claim collides with different authorization/review bytes")


def _consume_or_validate_review_authorization(
    root: Path,
    review: dict[str, Any],
    authorization: dict[str, Any],
    *,
    scope: str,
    review_reference: dict[str, Any],
    consume: bool,
) -> None:
    expected = _review_consumption_claim(
        review,
        authorization,
        scope=scope,
        review_reference=review_reference,
    )
    claim_relative = authorization["consumption_claim_path"]
    try:
        claim_path = resolve_contained_path(root, claim_relative, must_exist=False)
    except CustodyError as exc:
        raise ValueError(f"Task5 review consumption claim locator failed: {exc}") from exc
    claim_root = claim_path.parent
    if consume:
        try:
            with exclusive_writer_lock(claim_root):
                claim_path = resolve_contained_path(root, claim_relative, must_exist=False)
                if claim_path.exists():
                    try:
                        observed, _raw, _digest = strict_snapshot(claim_path)
                        _validate_review_consumption_claim(observed, expected)
                    except (CustodyError, OSError, ValueError) as exc:
                        raise ValueError(f"Task5 review consumption claim collision: {exc}") from exc
                    raise ValueError("Task5 review authorization replay: consumption claim already exists")
                claim_json_once(claim_root, claim_path, expected)
                observed, _raw, _digest = strict_snapshot(claim_path)
                _validate_review_consumption_claim(observed, expected)
        except CustodyError as exc:
            raise ValueError(f"Task5 review consumption claim publication failed: {exc}") from exc
        return
    try:
        claim_path = resolve_contained_path(root, claim_relative, must_exist=True)
        observed, _raw, _digest = strict_snapshot(claim_path)
    except (CustodyError, OSError, ValueError) as exc:
        raise ValueError(f"Task5 review consumption claim readback failed: {exc}") from exc
    _validate_review_consumption_claim(observed, expected)


def _review_freeze_sha256(review: dict[str, Any], scope: str) -> str:
    if scope == "live-escape-review":
        fields = (
            "kind", "review_id", "source", "ci_receipt", "registry_template",
            "escape_schema", "escape_checker", "review_protocol",
        )
        domain = b"daee-task5-live-escape-review-freeze-v1\0"
    elif scope == "candidate-readiness-review":
        fields = (
            "kind", "review_id", "source", "ci_receipt", "source_preflight",
            "candidate", "package_evidence", "evidence_manifest", "retention_receipt",
        )
        domain = b"daee-task5-candidate-readiness-review-freeze-v1\0"
    else:
        raise ValueError(f"unsupported Task5 review authorization scope: {scope}")
    frozen = {field: copy.deepcopy(review[field]) for field in fields}
    return hashlib.sha256(domain + canonical_json_bytes(frozen)).hexdigest()


def _canonical_task_identity(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or TASK_IDENTITY_RE.fullmatch(value) is None:
        raise ValueError(f"Task5 {field} must be one canonical lowercase agent task identity")
    return value


def _validate_task5_review_authorization(
    root: Path,
    review: dict[str, Any],
    *,
    scope: str,
    expected_candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    authorization, _raw = _load_ref(root, review.get("review_authorization"), f"{scope}.authorization")
    schema = _schema()
    issues = validate_schema_subset(
        authorization,
        {"$ref": "#/$defs/task5ReviewAuthorization", "$defs": schema["$defs"]},
    )
    if issues:
        raise ValueError(f"Task5 review authorization schema failed: {issues[0].message}")
    assert isinstance(authorization, dict)
    owner = _canonical_task_identity(review.get("accountable_owner"), field="accountable owner")
    reviewer = _canonical_task_identity(review.get("independent_reviewer"), field="independent reviewer")
    authorized_reviewer = _canonical_task_identity(
        authorization.get("reviewer_identity"),
        field="authorized reviewer",
    )
    if owner != IMPLEMENTATION_OWNER_IDENTITY:
        raise ValueError("Task5 review relabels the fixed accountable implementation owner")
    if authorization["issuer_identity"] != REVIEW_AUTHORIZATION_ISSUER:
        raise ValueError("Task5 review authorization issuer is not the exact external owner")
    if authorization["implementation_owner_identity"] != IMPLEMENTATION_OWNER_IDENTITY:
        raise ValueError("Task5 review authorization does not bind the fixed implementation owner")
    if authorized_reviewer in {IMPLEMENTATION_OWNER_IDENTITY, REVIEW_AUTHORIZATION_ISSUER}:
        raise ValueError("Task5 authorized reviewer must differ from owner and issuer")
    if reviewer != authorized_reviewer:
        raise ValueError("Task5 review reviewer differs from its owner-issued authorization")
    if review["review_authorization_id"] != authorization["authorization_id"]:
        raise ValueError("Task5 review did not consume the exact authorization_id")
    if authorization["authorization_id"] != _review_authorization_id(authorization):
        raise ValueError("Task5 review authorization_id drifted")
    if authorization["scope"] != scope:
        raise ValueError("Task5 review authorization scope drifted")
    if authorization["review_id"] != review["review_id"]:
        raise ValueError("Task5 review authorization was replayed for another review_id")
    if authorization["source"] != review["source"]:
        raise ValueError("Task5 review authorization source binding drifted")
    if authorization["candidate"] != expected_candidate:
        raise ValueError("Task5 review authorization candidate/tree binding drifted")
    if authorization["freeze_sha256"] != _review_freeze_sha256(review, scope):
        raise ValueError("Task5 review authorization freeze binding drifted")
    expected_claim_path = _review_claim_locator(
        review["review_authorization"],
        scope,
        review["review_id"],
    )
    if authorization["consumption_claim_path"] != expected_claim_path:
        raise ValueError("Task5 review authorization consumption-claim locator drifted")
    try:
        issued_at = datetime.strptime(authorization["issued_at"], "%Y-%m-%dT%H:%M:%SZ")
        reviewed_at = datetime.strptime(review["reviewed_at"], "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Task5 review authorization timestamp is invalid: {exc}") from exc
    if issued_at > reviewed_at:
        raise ValueError("Task5 review authorization postdates the completed review")
    return authorization


def _canonical_ref(root: Path, relative: str) -> dict[str, Any]:
    path = resolve_contained_path(root, relative, must_exist=True)
    raw = path.read_bytes()
    return {"path": relative, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _artifact_ref(root: Path, path: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    path = path.resolve(strict=True)
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"artifact path escapes repository root: {path}") from exc
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"artifact is not one regular file: {relative}")
    raw = path.read_bytes()
    return {"path": relative, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _same_short_ref(actual: Any, expected: Any) -> bool:
    return (
        isinstance(actual, dict)
        and isinstance(expected, dict)
        and actual.get("path") == expected.get("path")
        and actual.get("sha256") == expected.get("sha256")
    )


def _validated_live_escape_review(
    root: Path,
    *,
    ci_receipt: dict[str, Any],
    review_protocol: dict[str, Any],
    independent_review: dict[str, Any],
    allow_test_fixture: bool = False,
    consume_authorization: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    exact_test_fixture = ci_receipt.get("path") == CI_TEST_FIXTURE_PATH
    if exact_test_fixture and not allow_test_fixture:
        raise ValueError("tracked CI test fixture cannot authorize live escape evidence")
    if not exact_test_fixture and str(ci_receipt.get("path", "")).startswith("tests/"):
        raise ValueError("test-owned CI receipt path cannot authorize live escape evidence")
    receipt, _ = _load_ref(root, ci_receipt, "escape.ci_receipt")
    receipt_findings = validate_receipt(receipt, root=root)
    if receipt_findings:
        finding = receipt_findings[0]
        raise ValueError(f"escape CI receipt rejected [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    if not (allow_test_fixture and exact_test_fixture):
        if ci_receipt.get("path") != receipt.get("receipt_locator"):
            raise ValueError("CI receipt artifact path differs from its create-once locator")
        commit = str(receipt["source"]["commit_sha"])
        tree = str(receipt["source"]["tree_oid"])

        def git_output(*args: str) -> str:
            try:
                result = subprocess.run(
                    ["git", *args],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise ValueError(f"Git source-object verification failed: {exc}") from exc
            if result.returncode != 0:
                raise ValueError(f"Git source-object verification failed for {' '.join(args)}")
            return result.stdout.strip()

        if git_output("cat-file", "-t", commit) != "commit":
            raise ValueError("CI receipt source commit is not a live Git commit object")
        if git_output("cat-file", "-t", tree) != "tree":
            raise ValueError("CI receipt source tree is not a live Git tree object")
        if git_output("rev-parse", f"{commit}^{{tree}}") != tree:
            raise ValueError("CI receipt source commit/tree binding differs from live Git")
        if git_output("rev-parse", "HEAD") != commit:
            raise ValueError("CI receipt source commit is not the current local HEAD")
    review, _ = _load_ref(root, independent_review, "escape.independent_review")
    schema = _schema()
    issues = validate_schema_subset(review, {"$ref": "#/$defs/liveEscapeReview", "$defs": schema["$defs"]})
    if issues:
        raise ValueError(f"escape independent review schema failed: {issues[0].message}")
    if review["review_sha256"] != _unsigned_hash(review, "review_sha256"):
        raise ValueError("escape independent review self-hash drift")
    authorization = _validate_task5_review_authorization(
        root,
        review,
        scope="live-escape-review",
        expected_candidate=None,
    )
    if review["source"] != _source_identity(receipt) or review["ci_receipt"] != ci_receipt:
        raise ValueError("escape review source differs from exact CI receipt")
    expected_refs = {
        "registry_template": _canonical_ref(root, ESCAPE_LIVE_REGISTRY_PATH),
        "escape_schema": _canonical_ref(root, ESCAPE_SCHEMA_PATH),
        "escape_checker": _canonical_ref(root, ESCAPE_CHECKER_PATH),
        "review_protocol": _canonical_ref(root, REVIEW_PROTOCOL_PATH),
    }
    if review_protocol != expected_refs["review_protocol"]:
        raise ValueError("escape review protocol is not the canonical reviewed-five protocol")
    for role, expected in expected_refs.items():
        if review[role] != expected:
            raise ValueError(f"escape review {role} differs from canonical role bytes")
    protocol, _ = _load_ref(root, review_protocol, "escape.review_protocol")
    protocol_findings = validate_smoke_manifest(protocol, root=root)
    if protocol_findings:
        raise ValueError(f"escape review protocol semantics failed: {protocol_findings[0]}")
    registry_source, _ = _load_ref(
        root,
        expected_refs["registry_template"],
        "escape.registry_template",
    )
    registry_source_findings = validate_for_candidate_maturity(registry_source)
    if registry_source_findings or registry_source.get("registry_role") != "LIVE_EVIDENCE":
        message = (
            registry_source_findings[0].message
            if registry_source_findings
            else "registry source role is not LIVE_EVIDENCE"
        )
        raise ValueError(f"escape registry source rejected: {message}")
    _consume_or_validate_review_authorization(
        root,
        review,
        authorization,
        scope="live-escape-review",
        review_reference=independent_review,
        consume=consume_authorization,
    )
    return review, receipt


def _derive_live_escape_registry(
    registry_source: dict[str, Any],
    *,
    root: Path,
    review: dict[str, Any],
    receipt: dict[str, Any],
    review_protocol: dict[str, Any],
    independent_review: dict[str, Any],
) -> dict[str, Any]:
    """Rebind only the fields governed for one exact-source live registry."""
    source = _source_identity(receipt)
    expected = copy.deepcopy(registry_source)
    expected["registry_id"] = f"daee-live-escape-{source['commit_sha']}"
    scope_updates = {
        "source_sha256": _source_scope_sha256(source),
        "schema_sha256": _file_sha256(root, ESCAPE_SCHEMA_PATH),
        "checker_sha256": _file_sha256(root, ESCAPE_CHECKER_PATH),
        "model_protocol_sha256": review_protocol["sha256"],
    }
    concurrence = {
        "accountable_owner": review["accountable_owner"],
        "independent_reviewer": review["independent_reviewer"],
        "basis": "exact live source/schema/checker/protocol scope",
        "review": independent_review,
    }
    for row in expected["escapes"]:
        row["scope"].update(scope_updates)
        row["causal_control"]["independent_concurrence"] = copy.deepcopy(concurrence)
    return expected


def validate_live_escape_registry(
    value: Any,
    *,
    root: Path,
    ci_receipt: dict[str, Any],
    review_protocol: dict[str, Any],
    independent_review: dict[str, Any],
    allow_test_fixture: bool = False,
) -> list[Finding]:
    findings = validate_for_candidate_maturity(value)
    if findings:
        finding = findings[0]
        return [Finding(finding.failure_class, finding.message, finding.failure_subcode)]
    try:
        review, receipt = _validated_live_escape_review(
            root,
            ci_receipt=ci_receipt,
            review_protocol=review_protocol,
            independent_review=independent_review,
            allow_test_fixture=allow_test_fixture,
        )
        expected_scope = {
            "source_sha256": _source_scope_sha256(_source_identity(receipt)),
            "schema_sha256": _file_sha256(root, ESCAPE_SCHEMA_PATH),
            "checker_sha256": _file_sha256(root, ESCAPE_CHECKER_PATH),
            "model_protocol_sha256": review_protocol["sha256"],
        }
        for row in value["escapes"]:
            scope = row["scope"]
            if any(scope.get(field) != digest for field, digest in expected_scope.items()):
                return [Finding("escape_scope", "live escape scope differs from exact source/schema/checker/protocol bytes", "live-scope")]
            concurrence = row["causal_control"]["independent_concurrence"]
            if concurrence.get("review") != independent_review:
                return [Finding("escape_review", "live escape concurrence lacks the exact independent review", "review-binding")]
        registry_source, _ = _load_ref(
            root,
            review["registry_template"],
            "escape.registry_template",
        )
        expected = _derive_live_escape_registry(
            registry_source,
            root=root,
            review=review,
            receipt=receipt,
            review_protocol=review_protocol,
            independent_review=independent_review,
        )
        if value != expected:
            return [Finding(
                "escape_review_binding",
                "derived live escape rows or immutable payload differ from the reviewed canonical owner",
                "reviewed-row-payload",
            )]
    except (KeyError, TypeError, ValueError) as exc:
        return [Finding("escape_scope", str(exc), "live-scope")]
    return []


def _validate_source_carrier(
    root: Path,
    reference: dict[str, Any],
    receipt: dict[str, Any],
    *,
    allow_test_fixture: bool = False,
) -> None:
    canonical = receipt["source_binding"]["canonical_path"]
    if reference.get("path") != canonical:
        raise ValueError("tracked source binding is not the canonical carrier")
    carrier = next((row for row in receipt["carriers"] if row.get("path") == canonical), None)
    if not isinstance(carrier, dict):
        raise ValueError("canonical tracked source carrier is absent from receipt")
    fixture_carrier = allow_test_fixture and carrier.get("raw_sha256") == "01" * 32
    if not fixture_carrier and (reference.get("sha256") != carrier.get("raw_sha256") or reference.get("byte_count") != carrier.get("byte_count")):
        raise ValueError("canonical tracked source carrier identity differs from receipt carrier row")
    document, raw = _load_ref(root, reference, "tracked_source_binding")
    findings = validate_carrier_document(document, carrier_path=canonical)
    if findings:
        raise ValueError(f"canonical source carrier rejected: {findings[0].message}")
    binding_raw = _extract_source_binding_bytes(raw, carrier_path=canonical)
    if hashlib.sha256(binding_raw).hexdigest() != receipt["source_binding"]["raw_sha256"]:
        raise ValueError("canonical carrier embedded source-binding bytes differ from receipt")


def _validate_source_roles(
    value: dict[str, Any],
    *,
    root: Path,
    receipt: dict[str, Any],
    allow_test_fixture: bool = False,
) -> None:
    registries = value["registries"]
    closure = value["closure_evidence"]
    for role, expected_path in REGISTRY_ROLE_PATHS.items():
        if registries[role].get("path") != expected_path:
            raise ValueError(f"registry role {role} is not the canonical owner path")
        _load_ref(root, registries[role], f"registry.{role}")
    for role, expected_path in CLOSURE_ROLE_PATHS.items():
        if closure[role].get("path") != expected_path:
            raise ValueError(f"closure role {role} is not the canonical owner path")
        _load_ref(root, closure[role], f"closure_evidence.{role}")
    paths = [reference["path"] for reference in registries.values()] + [reference["path"] for reference in closure.values()]
    if len(paths) != len(set(paths)):
        raise ValueError("canonical registry and closure roles must have unique paths")
    live_registry, _ = _load_ref(root, registries["escape"], "registry.escape")
    findings = validate_live_escape_registry(
        live_registry,
        root=root,
        ci_receipt=value["ci_receipt"],
        review_protocol=registries["review_protocol"],
        independent_review=value["live_escape_review"],
        allow_test_fixture=allow_test_fixture,
    )
    if findings:
        finding = findings[0]
        raise ValueError(f"registry escape is not reviewed LIVE_EVIDENCE [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    _validated_live_escape_review(
        root,
        ci_receipt=value["ci_receipt"],
        review_protocol=registries["review_protocol"],
        independent_review=value["live_escape_review"],
        allow_test_fixture=allow_test_fixture,
    )


def _validate_candidate_registry_joins(record: dict[str, Any], source_preflight: dict[str, Any]) -> None:
    mappings = {
        "input_registry": "input",
        "validation_registry": "validation",
        "producer_registry": "producer",
        "escape_registry": "escape",
        "review_protocol": "review_protocol",
    }
    for record_field, source_role in mappings.items():
        if not _same_short_ref(record.get(record_field), source_preflight["registries"].get(source_role)):
            raise ValueError(f"candidate registry/protocol role {record_field} differs from source preflight")
    paths = [record[field]["path"] for field in mappings]
    if len(paths) != len(set(paths)):
        raise ValueError("candidate registry/protocol roles must retain unique paths")


def _validate_escape_for_maturity(value: Any, source_preflight: dict[str, Any], *, root: Path) -> None:
    findings = validate_for_candidate_maturity(value)
    if findings:
        finding = findings[0]
        raise ValueError(f"escape registry cannot support maturity [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    expected_scope = {
        "source_sha256": _source_scope_sha256(source_preflight["source"]),
        "schema_sha256": _file_sha256(root, ESCAPE_SCHEMA_PATH),
        "checker_sha256": _file_sha256(root, ESCAPE_CHECKER_PATH),
        "model_protocol_sha256": source_preflight["registries"]["review_protocol"]["sha256"],
    }
    for row in value["escapes"]:
        if any(row["scope"].get(field) != digest for field, digest in expected_scope.items()):
            raise ValueError("escape LIVE_EVIDENCE scope differs from exact source/schema/checker/protocol bytes")
        concurrence = row["causal_control"]["independent_concurrence"]
        if concurrence.get("review") != source_preflight["live_escape_review"]:
            raise ValueError("escape LIVE_EVIDENCE concurrence differs from source-preflight review")


def _same_content_ref(actual: Any, expected: Any) -> bool:
    return (
        isinstance(actual, dict)
        and isinstance(expected, dict)
        and actual.get("sha256") == expected.get("sha256")
        and actual.get("byte_count") == expected.get("byte_count")
    )


def derive_candidate_maturity_evidence(
    root: Path,
    inputs: dict[str, Any],
    *,
    consume_review_authorization: bool = False,
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if not isinstance(inputs, dict) or set(inputs) != CANDIDATE_INPUT_KEYS:
        raise ValueError("candidate maturity inputs must contain the exact derived-input set; self-declared fields are forbidden")

    source_preflight, _ = _load_ref(root, inputs["source_preflight"], "candidate.source_preflight")
    source_findings = validate_source_preflight(source_preflight, root=root)
    if source_findings:
        finding = source_findings[0]
        raise ValueError(f"source preflight is not default-production valid [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")

    candidate_root = resolve_contained_path(root, inputs["candidate_root"], must_exist=True)
    if not candidate_root.is_dir() or candidate_root.is_symlink():
        raise ValueError("candidate root is not one regular contained directory")
    if candidate_root.relative_to(root).as_posix() != inputs["candidate_root"]:
        raise ValueError("candidate root is not the canonical repository-relative locator")
    try:
        record = validate_candidate_readiness(candidate_root, repo_root=root)
    except ValueError as exc:
        raise ValueError(f"candidate readiness validation failed: {exc}") from exc
    if (
        record.get("status") != "READY_UNUSED"
        or record.get("claim_status") != "UNCLAIMED"
        or record.get("promotion_eligible") is not False
        or record.get("model_execution_authorized") is not False
    ):
        raise ValueError("candidate is claimed, quarantined, terminal, promoted, or model-authorized")

    record_path = candidate_root / "candidate-record.json"
    readiness_path = candidate_root / record["readiness_marker_path"]
    archive_path = resolve_contained_path(candidate_root, record["archive"]["path"], must_exist=True)
    candidate = {
        "candidate_id": record["candidate_id"],
        "status": record["status"],
        "claim_status": record["claim_status"],
        "candidate_root": record["candidate_root"],
        "package_profile": record["package_profile"],
        "candidate_record": _artifact_ref(root, record_path),
        "candidate_readiness": _artifact_ref(root, readiness_path),
        "archive": _artifact_ref(root, archive_path),
        "tree_digest_algorithm": record["tree_digest_algorithm"],
        "package_tree_sha256": record["extracted_tree_sha256"],
    }
    source = source_preflight["source"]
    if (
        record["branch"] != source["branch"]
        or record["ref"] != source["ref"]
        or record["source_commit"] != source["commit_sha"]
        or not _same_short_ref(record["ci_readback"], source_preflight["ci_receipt"])
        or not _same_short_ref(record["source_preflight"], inputs["source_preflight"])
    ):
        raise ValueError("candidate source/CI/ref identity differs from source preflight")
    if candidate["archive"]["sha256"] != record["archive"]["sha256"] or candidate["archive"]["byte_count"] != record["archive"]["byte_count"]:
        raise ValueError("candidate archive identity differs from Task 4 record")

    _validate_candidate_registry_joins(record, source_preflight)
    escape, _ = _load_ref(root, source_preflight["registries"]["escape"], "candidate.escape_registry")
    _validate_escape_for_maturity(escape, source_preflight, root=root)

    evidence_root = resolve_contained_path(root, inputs["package_evidence_root"], must_exist=True)
    if not evidence_root.is_dir() or evidence_root.is_symlink():
        raise ValueError("package evidence root is not one regular contained directory")
    evidence_relative = evidence_root.relative_to(root).as_posix()
    if evidence_relative != inputs["package_evidence_root"]:
        raise ValueError("package evidence root is not the canonical repository-relative locator")
    expected_context_path = f"{evidence_relative}/context.json"
    expected_parity_path = f"{evidence_relative}/package-harness-parity.json"
    if inputs["runtime_context"].get("path") != expected_context_path or inputs["package_harness_parity"].get("path") != expected_parity_path:
        raise ValueError("package evidence references differ from deterministic evidence-root locators")
    runtime_context, runtime_raw = _load_ref(root, inputs["runtime_context"], "candidate.runtime_context")
    parity, parity_raw = _load_ref(root, inputs["package_harness_parity"], "candidate.package_harness_parity")
    package_root = resolve_contained_path(candidate_root, record["extracted_root"], must_exist=True)
    try:
        context_result = validate_runtime_context(runtime_context, package_root, evidence_root)
    except RuntimeContextFailure as exc:
        raise ValueError(f"package-only runtime context rejected [{exc.failure_class}/{exc.subcode}]: {exc.detail}") from exc
    try:
        parity_result = validate_package_parity(parity, package_root, evidence_root, root)
    except PackageParityFailure as exc:
        raise ValueError(f"package harness parity rejected [{exc.cls}/{exc.subcode}]: {exc.detail}") from exc
    if (
        context_result.get("status") != "pass"
        or context_result.get("proof_mode") != "package-faithful"
        or parity_result.get("status") != "pass"
        or parity_result.get("classification") != "package-faithful"
        or parity_result.get("runtime_context_status") != "pass"
        or runtime_context["runtime"].get("source_commit") != source["commit_sha"]
        or runtime_context["runtime"].get("package_sha256") != record["extracted_tree_sha256"]
        or parity.get("package_tree_sha256") != record["extracted_tree_sha256"]
        or parity.get("harness_supplements") != []
        or parity.get("semantic_repair_count") != 0
    ):
        raise ValueError("package-only runtime-context/parity PASS evidence differs from exact source/candidate bytes")
    call_context_rows = [row for row in parity["artifacts"] if row.get("kind") == "call-context"]
    if len(call_context_rows) != 1 or call_context_rows[0] != {
        "kind": "call-context",
        "scope": "run",
        "path": "context.json",
        "sha256": hashlib.sha256(runtime_raw).hexdigest(),
        "byte_count": len(runtime_raw),
    }:
        raise ValueError("package parity call-context row differs from exact runtime-context bytes")
    package_evidence = {
        "evidence_root": evidence_relative,
        "runtime_context": inputs["runtime_context"],
        "runtime_context_status": "PASS",
        "runtime_context_proof_mode": "package-faithful",
        "package_harness_parity": inputs["package_harness_parity"],
        "package_harness_status": "PASS",
        "package_harness_classification": "package-faithful",
    }

    custody_root = resolve_contained_path(root, inputs["retention_custody_root"], must_exist=True)
    if not custody_root.is_dir() or custody_root.is_symlink():
        raise ValueError("retention custody root is not one regular contained directory")
    custody_relative = custody_root.relative_to(root).as_posix()
    if custody_relative != inputs["retention_custody_root"]:
        raise ValueError("retention custody root is not the canonical repository-relative locator")
    final_directory = inputs["retention_final_directory"]
    retention_findings = validate_export(custody_root, custody_root / final_directory)
    if retention_findings:
        finding = retention_findings[0]
        raise ValueError(f"retention export rejected [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    manifest_path = resolve_contained_path(custody_root, f"{final_directory}/manifest.json", must_exist=True)
    manifest, _ = _load_ref(root, _artifact_ref(root, manifest_path), "candidate.retention_manifest")
    receipt_path = resolve_contained_path(custody_root, manifest["custody"]["receipt_path"], must_exist=True)
    receipt, _ = _load_ref(root, _artifact_ref(root, receipt_path), "candidate.retention_receipt")
    expected_source_identity = {
        "repository": source["repository"],
        "branch": source["branch"],
        "ref": source["ref"],
        "commit_sha": source["commit_sha"],
        "tree_sha": source["tree_oid"],
    }
    if any(manifest["source_identity"].get(field) != item for field, item in expected_source_identity.items()):
        raise ValueError("retention source identity differs from source preflight")
    source_receipt_path = resolve_contained_path(root, record["source_commit_receipt"]["path"], must_exist=True)
    source_receipt_ref = _artifact_ref(root, source_receipt_path)
    ci_path = resolve_contained_path(root, record["ci_readback"]["path"], must_exist=True)
    ci_ref = _artifact_ref(root, ci_path)
    if (
        not _same_content_ref(manifest["source_identity"]["source_commit_receipt"], source_receipt_ref)
        or not _same_content_ref(manifest["source_identity"]["ci_readback"], ci_ref)
        or not _same_content_ref(manifest["candidate_identity"]["candidate_record"], candidate["candidate_record"])
        or not _same_content_ref(manifest["candidate_identity"]["candidate_readiness"], candidate["candidate_readiness"])
        or manifest["candidate_identity"].get("candidate_id") != candidate["candidate_id"]
        or manifest["candidate_identity"].get("status") != "READY_UNUSED"
        or manifest["candidate_identity"].get("package_sha256") != candidate["archive"]["sha256"]
        or manifest["candidate_identity"].get("package_tree_sha256") != candidate["package_tree_sha256"]
        or manifest["candidate_identity"].get("tree_digest_algorithm") != candidate["tree_digest_algorithm"]
        or manifest.get("kind") != "candidate-readiness-final-manifest"
        or manifest.get("status") != "RETENTION_GREEN"
        or manifest.get("completeness") != "COMPLETE"
        or manifest.get("cycle_identity") is not None
        or receipt.get("status") != "RETENTION_GREEN"
    ):
        raise ValueError("retention manifest/receipt source or candidate identity drift")

    required_inventory = {
        "candidate-archive": candidate["archive"],
        "source-preflight": inputs["source_preflight"],
        "live-escape": source_preflight["registries"]["escape"],
        "review-protocol": source_preflight["registries"]["review_protocol"],
        "runtime-context": inputs["runtime_context"],
        "package-harness-parity": inputs["package_harness_parity"],
    }
    inventory = {row["artifact_id"]: row for row in manifest["inventory"]}
    for role, reference in required_inventory.items():
        row = inventory.get(role)
        if (
            not isinstance(row, dict)
            or row.get("classification") != "CONTROL_RECORD"
            or row.get("required") is not True
            or row.get("present") is not True
            or row.get("sha256") != reference["sha256"]
            or row.get("byte_count") != reference["byte_count"]
        ):
            raise ValueError(f"retention inventory lacks exact required {role} evidence")
    retention = {
        "custody_root": custody_relative,
        "final_directory": final_directory,
        "manifest": _artifact_ref(root, manifest_path),
        "receipt": _artifact_ref(root, receipt_path),
        "status": "RETENTION_GREEN",
        "completeness": "COMPLETE",
        "retained_tree_sha256": manifest["retained_tree_sha256"],
    }

    review, _ = _load_ref(root, inputs["candidate_readiness_review"], "candidate.independent_review")
    schema = _schema()
    review_issues = validate_schema_subset(review, {"$ref": "#/$defs/candidateReadinessReview", "$defs": schema["$defs"]})
    if review_issues:
        raise ValueError(f"candidate independent review schema failed: {review_issues[0].message}")
    if review["review_sha256"] != _unsigned_hash(review, "review_sha256"):
        raise ValueError("candidate independent review self-hash drift")
    authorization = _validate_task5_review_authorization(
        root,
        review,
        scope="candidate-readiness-review",
        expected_candidate={
            "candidate_id": candidate["candidate_id"],
            "package_tree_sha256": candidate["package_tree_sha256"],
        },
    )
    expected_review = {
        "source": source,
        "ci_receipt": source_preflight["ci_receipt"],
        "source_preflight": inputs["source_preflight"],
        "candidate": candidate,
        "package_evidence": package_evidence,
        "evidence_manifest": retention["manifest"],
        "retention_receipt": retention["receipt"],
    }
    for field, expected in expected_review.items():
        if review.get(field) != expected:
            raise ValueError(f"candidate independent review {field} differs from exact evidence")
    _consume_or_validate_review_authorization(
        root,
        review,
        authorization,
        scope="candidate-readiness-review",
        review_reference=inputs["candidate_readiness_review"],
        consume=consume_review_authorization,
    )

    return {
        "source": copy.deepcopy(source),
        "source_binding": copy.deepcopy(source_preflight["source_binding"]),
        "ci_receipt": copy.deepcopy(source_preflight["ci_receipt"]),
        "source_preflight": copy.deepcopy(inputs["source_preflight"]),
        "candidate": candidate,
        "registries": copy.deepcopy(source_preflight["registries"]),
        "package_evidence": package_evidence,
        "retention": retention,
        "independent_review": copy.deepcopy(inputs["candidate_readiness_review"]),
    }


def validate_source_preflight(
    value: Any,
    *,
    root: Path = ROOT,
    allow_test_fixture: bool = False,
) -> list[Finding]:
    schema = _schema()
    issues = validate_schema_subset(value, {"$ref": "#/$defs/sourcePreflight", "$defs": schema["$defs"]})
    if issues:
        return [Finding("schema_contract", issues[0].message, "schema")]
    assert isinstance(value, dict)
    if value["verdict_sha256"] != _unsigned_hash(value, "verdict_sha256"):
        return [Finding("verdict_hash", "verdict self-hash drift", "verdict-sha256")]
    try:
        receipt, _ = _load_ref(root, value["ci_receipt"], "ci_receipt")
        receipt_findings = validate_receipt(receipt, root=root)
        if receipt_findings:
            finding = receipt_findings[0]
            return [Finding("ci_receipt", finding.message, finding.failure_subcode)]
        expected_source = _source_identity(receipt)
        if value["source"] != expected_source:
            return [Finding("source_identity", "source preflight differs from exact CI receipt", "source-receipt")]
        if value["source_binding"] != receipt["source_binding"]:
            return [Finding("source_binding", "tracked source binding differs from exact CI receipt", "source-binding")]
        try:
            _validate_source_carrier(root, value["tracked_source_binding"], receipt, allow_test_fixture=allow_test_fixture)
        except ValueError as exc:
            return [Finding("source_binding", str(exc), "canonical-carrier")]
        if value["deterministic_evidence"] != receipt["deterministic_verdicts"]:
            return [Finding("deterministic_evidence", "Task7 evidence references differ from exact CI receipt", "task7-references")]
        _validate_source_roles(value, root=root, receipt=receipt, allow_test_fixture=allow_test_fixture)
    except (KeyError, TypeError, ValueError) as exc:
        return [Finding("live_evidence", str(exc), "live-reference")]
    return []


def validate_candidate_maturity(value: Any, *, root: Path = ROOT) -> list[Finding]:
    schema = _schema()
    issues = validate_schema_subset(value, {"$ref": "#/$defs/candidateMaturity", "$defs": schema["$defs"]})
    if issues:
        return [Finding("schema_contract", issues[0].message, "candidate-schema")]
    assert isinstance(value, dict)
    if value["verdict_sha256"] != _unsigned_hash(value, "verdict_sha256"):
        return [Finding("verdict_hash", "candidate maturity self-hash drift", "verdict-sha256")]
    inputs = {
        "source_preflight": value["source_preflight"],
        "candidate_root": value["candidate"]["candidate_root"],
        "package_evidence_root": value["package_evidence"]["evidence_root"],
        "runtime_context": value["package_evidence"]["runtime_context"],
        "package_harness_parity": value["package_evidence"]["package_harness_parity"],
        "retention_custody_root": value["retention"]["custody_root"],
        "retention_final_directory": value["retention"]["final_directory"],
        "candidate_readiness_review": value["independent_review"],
    }
    try:
        expected = derive_candidate_maturity_evidence(root, inputs)
    except (KeyError, TypeError, ValueError) as exc:
        return [Finding("candidate_maturity_evidence", str(exc), "derived-evidence")]
    for field, observed in expected.items():
        if value.get(field) != observed:
            return [Finding("candidate_maturity_binding", f"candidate maturity {field} differs from derived evidence", field.replace("_", "-"))]
    return []


def validate_verdict(
    value: Any,
    *,
    root: Path = ROOT,
    allow_test_fixture: bool = False,
) -> list[Finding]:
    if isinstance(value, dict) and value.get("kind") == "source-preflight":
        return validate_source_preflight(value, root=root, allow_test_fixture=allow_test_fixture)
    if isinstance(value, dict) and value.get("kind") == "candidate-maturity":
        if allow_test_fixture:
            return [Finding("test_mode_boundary", "candidate maturity has no unit-fixture validation mode", "candidate-production-only")]
        return validate_candidate_maturity(value, root=root)
    schema = _schema()
    issues = validate_schema_subset(value, schema)
    message = issues[0].message if issues else "unsupported no-model verdict kind"
    return [Finding("schema_contract", message, "verdict-kind")]


def _read(path: Path) -> Any:
    return strict_json_loads(path.read_bytes(), label=str(path))


def self_test() -> int:
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(ROOT / "tests/no-model-candidate-maturity"),
        "-p",
        "test*.py",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"no-model candidate maturity self-test: FAIL: {exc}")
        return 1
    output = (completed.stdout + completed.stderr).strip()
    if output:
        print(output)
    match = re.search(r"Ran (\d+) tests?", output)
    count = int(match.group(1)) if match else 0
    if completed.returncode != 0 or count == 0:
        print("no-model candidate maturity self-test: FAIL")
        return 1
    print(f"no-model candidate maturity self-test: PASS ({count} source/candidate tests)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        if args.artifact is not None:
            parser.error("artifact cannot be combined with --self-test")
        return self_test()
    if args.artifact is None:
        parser.error("artifact is required unless --self-test is used")
    try:
        value = _read(args.artifact)
        findings = validate_verdict(value)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings = [Finding("malformed_json_or_path", str(exc), "malformed-json")]
    if findings:
        finding = findings[0]
        if args.explain:
            print(json.dumps({"checker_id": CHECKER_ID, "status": "FAIL", "failure_class": finding.failure_class, "failure_subcode": finding.failure_subcode, "downstream_invalidated": DOWNSTREAM, "message": finding.message}, sort_keys=True))
        else:
            print(f"no-model candidate maturity: FAIL [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
        return 1
    print(json.dumps({"checker_id": CHECKER_ID, "status": "PASS"}, sort_keys=True) if args.explain else "no-model candidate maturity: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
