#!/usr/bin/env python3
"""Derive and create-once publish no-model source or candidate maturity verdicts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from a16_immutable_custody import CustodyError, canonical_json_bytes, claim_json_once, strict_snapshot
from check_ci_readback import validate_receipt
from check_no_model_candidate_maturity import (
    _derive_live_escape_registry,
    _load_ref,
    _validate_source_carrier,
    _validate_source_roles,
    _validated_live_escape_review,
    derive_candidate_maturity_evidence,
    validate_candidate_maturity,
    validate_live_escape_registry,
    validate_verdict,
)
from source_provenance import strict_json_loads

ROOT = Path(__file__).resolve().parents[1]
NON_CLAIMS = [
    "source preflight is not candidate maturity",
    "source preflight does not authorize model execution",
    "source preflight is not owner acceptance",
]
CANDIDATE_NON_CLAIMS = [
    "no-model candidate maturity is not model execution authorization",
    "no-model candidate maturity is not reviewed smoke success",
    "no-model candidate maturity is not owner acceptance",
]


def build_live_escape_registry(
    repo_root: Path,
    *,
    ci_receipt: dict[str, Any],
    review_protocol: dict[str, Any],
    independent_review: dict[str, Any],
    allow_test_fixture: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    review, receipt = _validated_live_escape_review(
        repo_root,
        ci_receipt=ci_receipt,
        review_protocol=review_protocol,
        independent_review=independent_review,
        allow_test_fixture=allow_test_fixture,
        consume_authorization=True,
    )
    template, _ = _load_ref(repo_root, review["registry_template"], "escape.registry_template")
    if template.get("registry_role") != "LIVE_EVIDENCE":
        raise ValueError("live escape registry source is not the tracked LIVE_EVIDENCE owner")
    value = _derive_live_escape_registry(
        template,
        root=repo_root,
        review=review,
        receipt=receipt,
        review_protocol=review_protocol,
        independent_review=independent_review,
    )
    findings = validate_live_escape_registry(
        value,
        root=repo_root,
        ci_receipt=ci_receipt,
        review_protocol=review_protocol,
        independent_review=independent_review,
        allow_test_fixture=allow_test_fixture,
    )
    if findings:
        finding = findings[0]
        raise ValueError(f"live escape registry rejected [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    return value


def publish_live_escape_registry(
    repo_root: Path,
    output: Path,
    *,
    ci_receipt: dict[str, Any],
    review_protocol: dict[str, Any],
    independent_review: dict[str, Any],
    allow_test_fixture: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    value = build_live_escape_registry(
        repo_root,
        ci_receipt=ci_receipt,
        review_protocol=review_protocol,
        independent_review=independent_review,
        allow_test_fixture=allow_test_fixture,
    )
    try:
        claim_json_once(repo_root, output, value)
    except CustodyError as exc:
        raise ValueError(f"live escape registry create-once publication failed: {exc}") from exc
    observed, _raw, _sha = strict_snapshot(output)
    if observed != value:
        raise ValueError("live escape registry create-once readback drift")
    return value


def _verdict_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def build_source_preflight(
    repo_root: Path,
    inputs: dict[str, Any],
    *,
    allow_test_fixture: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    receipt, _ = _load_ref(repo_root, inputs.get("ci_receipt"), "ci_receipt")
    receipt_findings = validate_receipt(receipt, root=repo_root)
    if receipt_findings:
        finding = receipt_findings[0]
        raise ValueError(f"ci_receipt rejected [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    if receipt.get("status") != "EXACT_SHA_CI_GREEN":
        raise ValueError("ci_receipt is not exact-SHA green")
    if not isinstance(inputs.get("tracked_source_binding"), dict):
        raise ValueError("tracked source binding reference is required")
    registries = inputs.get("registries")
    closure = inputs.get("closure_evidence")
    if not isinstance(registries, dict) or set(registries) != {"input", "validation", "producer", "escape", "review_protocol"}:
        raise ValueError("registries must contain the exact source-preflight registry set")
    if not isinstance(closure, dict) or set(closure) != {"closure_ledger", "contract_registry", "architecture_ledger"}:
        raise ValueError("closure_evidence must contain the exact deterministic ledger set")
    if not isinstance(inputs.get("live_escape_review"), dict):
        raise ValueError("live_escape_review reference is required")
    unsigned: dict[str, Any] = {
        "schema": "daee-no-model-candidate-maturity-v1",
        "kind": "source-preflight",
        "status": "NO_MODEL_SOURCE_PREFLIGHT_GREEN",
        "source": {
            "repository": receipt["repository"]["full_name"],
            "remote_url": receipt["repository"]["remote_url"],
            "branch": receipt["repository"]["branch"],
            "ref": receipt["repository"]["ref"],
            "commit_sha": receipt["source"]["commit_sha"],
            "tree_oid": receipt["source"]["tree_oid"],
        },
        "source_binding": receipt["source_binding"],
        "ci_receipt": inputs["ci_receipt"],
        "tracked_source_binding": inputs["tracked_source_binding"],
        "deterministic_evidence": receipt["deterministic_verdicts"],
        "registries": registries,
        "live_escape_review": inputs["live_escape_review"],
        "closure_evidence": closure,
        "model_execution_authorized": False,
        "terminal_claim": False,
        "non_claims": NON_CLAIMS,
    }
    prospective = {**unsigned, "verdict_sha256": _verdict_hash(unsigned)}
    _validate_source_carrier(repo_root, prospective["tracked_source_binding"], receipt, allow_test_fixture=allow_test_fixture)
    _validate_source_roles(prospective, root=repo_root, receipt=receipt, allow_test_fixture=allow_test_fixture)
    return prospective


def publish_source_preflight(
    repo_root: Path,
    inputs: dict[str, Any],
    output: Path,
    *,
    allow_test_fixture: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    verdict = build_source_preflight(repo_root, inputs, allow_test_fixture=allow_test_fixture)
    findings = validate_verdict(verdict, root=repo_root, allow_test_fixture=allow_test_fixture)
    if findings:
        finding = findings[0]
        raise ValueError(f"source preflight rejected [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    try:
        claim_json_once(repo_root, output, verdict)
    except CustodyError as exc:
        raise ValueError(f"source preflight create-once publication failed: {exc}") from exc
    observed, _raw, _sha = strict_snapshot(output)
    if observed != verdict:
        raise ValueError("source preflight create-once readback drift")
    return verdict


def build_candidate_maturity(repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    evidence = derive_candidate_maturity_evidence(
        repo_root,
        inputs,
        consume_review_authorization=True,
    )
    unsigned: dict[str, Any] = {
        "schema": "daee-no-model-candidate-maturity-v1",
        "kind": "candidate-maturity",
        "status": "NO_MODEL_CANDIDATE_MATURE",
        **evidence,
        "model_execution_authorized": False,
        "terminal_claim": False,
        "non_claims": CANDIDATE_NON_CLAIMS,
    }
    verdict = {**unsigned, "verdict_sha256": _verdict_hash(unsigned)}
    findings = validate_candidate_maturity(verdict, root=repo_root)
    if findings:
        finding = findings[0]
        raise ValueError(f"candidate maturity rejected [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    return verdict


def publish_candidate_maturity(
    repo_root: Path,
    inputs: dict[str, Any],
    output: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    verdict = build_candidate_maturity(repo_root, inputs)
    try:
        claim_json_once(repo_root, output, verdict)
    except CustodyError as exc:
        raise ValueError(f"candidate maturity create-once publication failed: {exc}") from exc
    observed, _raw, _sha = strict_snapshot(output)
    if observed != verdict:
        raise ValueError("candidate maturity create-once readback drift")
    findings = validate_candidate_maturity(observed, root=repo_root)
    if findings:
        finding = findings[0]
        raise ValueError(f"candidate maturity readback rejected [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
    return verdict


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--source-inputs", type=Path)
    inputs.add_argument("--candidate-inputs", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        input_path = args.source_inputs or args.candidate_inputs
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if args.source_inputs is not None:
            verdict = publish_source_preflight(args.repo_root, payload, args.out)
        else:
            verdict = publish_candidate_maturity(args.repo_root, payload, args.out)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"no-model maturity builder: FAIL: {exc}")
        return 1
    print(json.dumps({"kind": verdict["kind"], "status": verdict["status"], "source_commit": verdict["source"]["commit_sha"], "verdict_sha256": verdict["verdict_sha256"], "terminal_claim": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
