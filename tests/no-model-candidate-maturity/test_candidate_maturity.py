#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_candidate_package_record as candidate_builder  # noqa: E402
import build_no_model_candidate_maturity_verdict as maturity_builder  # noqa: E402
import check_evidence_retention_manifest as retention_checker  # noqa: E402
import check_no_model_candidate_maturity as maturity_checker  # noqa: E402
import check_package_harness_parity as parity_checker  # noqa: E402
import check_runtime_context_delivery as context_checker  # noqa: E402
import export_cycle_evidence_bundle as retention_exporter  # noqa: E402
from a16_immutable_custody import canonical_json_bytes  # noqa: E402


IMPLEMENTATION_OWNER = "/root/task5_retention"
AUTHORIZATION_ISSUER = "/root"


def content_hash(value: dict, field: str) -> str:
    unsigned = {key: copy.deepcopy(item) for key, item in value.items() if key != field}
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def review_authorization_id(value: dict) -> str:
    unsigned = {key: copy.deepcopy(item) for key, item in value.items() if key != "authorization_id"}
    return hashlib.sha256(
        b"daee-task5-independent-review-authorization-v1\0" + canonical_json_bytes(unsigned)
    ).hexdigest()


def review_freeze(value: dict) -> str:
    if value["kind"] == "live-escape-independent-review":
        fields = (
            "kind", "review_id", "source", "ci_receipt", "registry_template",
            "escape_schema", "escape_checker", "review_protocol",
        )
        domain = b"daee-task5-live-escape-review-freeze-v1\0"
    else:
        fields = (
            "kind", "review_id", "source", "ci_receipt", "source_preflight",
            "candidate", "package_evidence", "evidence_manifest", "retention_receipt",
        )
        domain = b"daee-task5-candidate-readiness-review-freeze-v1\0"
    frozen = {key: copy.deepcopy(value[key]) for key in fields}
    return hashlib.sha256(domain + canonical_json_bytes(frozen)).hexdigest()


def review_claim_locator(authorization_path: str, scope: str, review_id: str) -> str:
    parent = PurePosixPath(authorization_path).parent
    review_digest = hashlib.sha256(review_id.encode("utf-8")).hexdigest()
    return (parent / "claims" / f"{scope}-{review_digest}.claim.json").as_posix()


def build_review_authorization(
    review: dict,
    *,
    scope: str,
    candidate: dict | None,
    issued_at: str,
    authorization_path: str,
) -> dict:
    value = {
        "schema": "daee-task5-independent-review-authorization-v1",
        "authorization_id": "",
        "issuer_identity": AUTHORIZATION_ISSUER,
        "implementation_owner_identity": IMPLEMENTATION_OWNER,
        "reviewer_identity": review["independent_reviewer"],
        "scope": scope,
        "review_id": review["review_id"],
        "source": copy.deepcopy(review["source"]),
        "candidate": copy.deepcopy(candidate),
        "freeze_sha256": review_freeze(review),
        "consumption_claim_path": review_claim_locator(
            authorization_path,
            scope,
            review["review_id"],
        ),
        "issued_at": issued_at,
        "one_use": True,
        "owner_acceptance": False,
        "model_execution_authorized": False,
        "terminal_claim": False,
    }
    value["authorization_id"] = review_authorization_id(value)
    return value


def full_ref(root: Path, relative: str) -> dict[str, object]:
    raw = (root / relative).read_bytes()
    return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "byte_count": len(raw)}


def short_ref(root: Path, relative: str) -> dict[str, str]:
    raw = (root / relative).read_bytes()
    return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def copy_from_root(destination_root: Path, relative: str) -> None:
    target = destination_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / relative, target)


class CandidateMaturityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="task5-candidate-maturity-", dir=HERE)
        cls.repo = Path(cls.temporary.name)
        cls._prepare_repo_dependencies()
        cls._prepare_source_preflight_fixture()
        cls._build_unused_candidate()
        cls._prepare_package_evidence()
        cls._prepare_retention_export()
        cls._prepare_independent_review()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    @classmethod
    def _prepare_repo_dependencies(cls) -> None:
        for relative in (
            "docs/audits/v0.4.6.0-wip-andon-closure-ledger.json",
            "docs/audits/v0.4.6.0-wip-andon-contract-registry.json",
            "docs/audits/v0.4.6.0-wip-architecture-decisions.json",
            "schema/model-smoke-escape.schema.json",
            "tests/ci-readback/valid/required-checks-bound-to-pushed-sha.json",
            "tests/model-smoke-escape/registry.json",
            "tests/smoke-matrix/reviewed-five-smoke-protocol.json",
            "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json",
            "tools/campaign_usage_ledger.py",
            "tools/check_model_smoke_escape_registry.py",
            "tools/check_runtime_context_delivery.py",
            "tools/producer-contract-registry.json",
            "tools/runtime_call_context_adapter.py",
            "tools/runtime_context_resolver.py",
            "tools/validation-registry.json",
        ):
            copy_from_root(cls.repo, relative)
        source_receipt = cls.repo / "evidence/source-commit.json"
        source_receipt.parent.mkdir(parents=True, exist_ok=True)
        source_receipt.write_bytes(b'{"status":"SOURCE_RECEIPT_FIXTURE"}\n')

    @classmethod
    def _prepare_source_preflight_fixture(cls) -> None:
        ci_source = "tests/ci-readback/valid/required-checks-bound-to-pushed-sha.json"
        ci_value = json.loads((ROOT / ci_source).read_text(encoding="utf-8"))
        source = {
            "repository": ci_value["repository"]["full_name"],
            "remote_url": ci_value["repository"]["remote_url"],
            "branch": ci_value["repository"]["branch"],
            "ref": ci_value["repository"]["ref"],
            "commit_sha": ci_value["source"]["commit_sha"],
            "tree_oid": ci_value["source"]["tree_oid"],
        }
        review = {
            "schema": "daee-no-model-candidate-maturity-v1",
            "kind": "live-escape-independent-review",
            "review_id": "candidate-maturity-live-escape-review",
            "verdict": "ACCEPT",
            "accountable_owner": IMPLEMENTATION_OWNER,
            "independent_reviewer": "/root/task5_live_escape_reviewer",
            "source": source,
            "ci_receipt": full_ref(cls.repo, ci_source),
            "registry_template": full_ref(cls.repo, "tests/model-smoke-escape/registry.json"),
            "escape_schema": full_ref(cls.repo, "schema/model-smoke-escape.schema.json"),
            "escape_checker": full_ref(cls.repo, "tools/check_model_smoke_escape_registry.py"),
            "review_protocol": full_ref(cls.repo, "tests/smoke-matrix/reviewed-five-smoke-protocol.json"),
            "independent_from_owner": True,
            "reviewed_at": "2026-07-12T12:22:00Z",
            "terminal_claim": False,
            "model_execution_authorized": False,
            "non_claims": [
                "escape review is not candidate maturity",
                "escape review does not authorize model execution",
                "escape review is not owner acceptance",
            ],
        }
        review_authorization = build_review_authorization(
            review,
            scope="live-escape-review",
            candidate=None,
            issued_at="2026-07-12T12:21:00Z",
            authorization_path="evidence/live-escape-review-authorization.json",
        )
        review_authorization_path = cls.repo / "evidence/live-escape-review-authorization.json"
        write_json(review_authorization_path, review_authorization)
        review["review_authorization_id"] = review_authorization["authorization_id"]
        review["review_authorization"] = full_ref(cls.repo, "evidence/live-escape-review-authorization.json")
        review["review_sha256"] = content_hash(review, "review_sha256")
        review_path = cls.repo / "evidence/live-escape-review.json"
        write_json(review_path, review)
        review_ref = full_ref(cls.repo, "evidence/live-escape-review.json")

        template = json.loads((cls.repo / "tests/model-smoke-escape/registry.json").read_text(encoding="utf-8"))
        live = copy.deepcopy(template)
        live["registry_id"] = f"daee-live-escape-{source['commit_sha']}"
        live["registry_role"] = "LIVE_EVIDENCE"
        source_scope = hashlib.sha256(canonical_json_bytes({
            "repository": source["repository"],
            "commit_sha": source["commit_sha"],
            "tree_oid": source["tree_oid"],
        })).hexdigest()
        for row in live["escapes"]:
            row["scope"].update({
                "source_sha256": source_scope,
                "schema_sha256": full_ref(cls.repo, "schema/model-smoke-escape.schema.json")["sha256"],
                "checker_sha256": full_ref(cls.repo, "tools/check_model_smoke_escape_registry.py")["sha256"],
                "model_protocol_sha256": full_ref(cls.repo, "tests/smoke-matrix/reviewed-five-smoke-protocol.json")["sha256"],
            })
            row["causal_control"]["independent_concurrence"] = {
                "accountable_owner": review["accountable_owner"],
                "independent_reviewer": review["independent_reviewer"],
                "basis": "exact live source/schema/checker/protocol scope",
                "review": review_ref,
            }
        live_path = cls.repo / "registries/live-escape.json"
        write_json(live_path, live)

        receipt = ci_value
        preflight = {
            "schema": "daee-no-model-candidate-maturity-v1",
            "kind": "source-preflight",
            "status": "NO_MODEL_SOURCE_PREFLIGHT_GREEN",
            "source": source,
            "source_binding": receipt["source_binding"],
            "ci_receipt": full_ref(cls.repo, ci_source),
            "tracked_source_binding": full_ref(cls.repo, "docs/audits/v0.4.6.0-wip-andon-closure-ledger.json"),
            "deterministic_evidence": receipt["deterministic_verdicts"],
            "registries": {
                "input": full_ref(cls.repo, "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json"),
                "validation": full_ref(cls.repo, "tools/validation-registry.json"),
                "producer": full_ref(cls.repo, "tools/producer-contract-registry.json"),
                "escape": full_ref(cls.repo, "registries/live-escape.json"),
                "review_protocol": full_ref(cls.repo, "tests/smoke-matrix/reviewed-five-smoke-protocol.json"),
            },
            "live_escape_review": review_ref,
            "closure_evidence": {
                "closure_ledger": full_ref(cls.repo, "docs/audits/v0.4.6.0-wip-andon-closure-ledger.json"),
                "contract_registry": full_ref(cls.repo, "docs/audits/v0.4.6.0-wip-andon-contract-registry.json"),
                "architecture_ledger": full_ref(cls.repo, "docs/audits/v0.4.6.0-wip-architecture-decisions.json"),
            },
            "model_execution_authorized": False,
            "terminal_claim": False,
            "non_claims": [
                "source preflight is not candidate maturity",
                "source preflight does not authorize model execution",
                "source preflight is not owner acceptance",
            ],
        }
        preflight["verdict_sha256"] = content_hash(preflight, "verdict_sha256")
        cls.source_preflight_path = cls.repo / "evidence/source-preflight.json"
        write_json(cls.source_preflight_path, preflight)
        cls.source_preflight = preflight

    @classmethod
    def _candidate_authorization(cls) -> dict:
        value = {
            "schema": "daee-smoke-matrix-v1",
            "kind": "candidate-build-authorization",
            "authorization_id": "task5-candidate-build-fixture",
            "action": "BUILD_EXECUTION_MINI_CANDIDATE",
            "one_use": True,
            "issued_at": "2026-07-12T00:00:00Z",
            "expires_at": "2026-07-13T00:00:00Z",
            "branch": cls.source_preflight["source"]["branch"],
            "ref": cls.source_preflight["source"]["ref"],
            "source_commit": cls.source_preflight["source"]["commit_sha"],
            "source_commit_receipt": short_ref(cls.repo, "evidence/source-commit.json"),
            "ci_readback": short_ref(cls.repo, "tests/ci-readback/valid/required-checks-bound-to-pushed-sha.json"),
            "source_preflight": short_ref(cls.repo, "evidence/source-preflight.json"),
            "package_profile": "execution-mini",
            "candidate_id": "task5-candidate-fixture",
            "custody_root": "candidate-custody",
            "candidate_root": "candidate-custody/candidates/task5-candidate-fixture",
            "claim_path": "candidate-custody/claims/task5-candidate-build-fixture.claim.json",
            "archive_name": "daee-epistemics-v0.4.6.0-execution-mini.skill.zip",
            "max_archive_bytes": 16 * 1024 * 1024,
            "max_extracted_bytes": 16 * 1024 * 1024,
            "max_archive_entries": 500,
            "input_registry": short_ref(cls.repo, "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json"),
            "validation_registry": short_ref(cls.repo, "tools/validation-registry.json"),
            "producer_registry": short_ref(cls.repo, "tools/producer-contract-registry.json"),
            "escape_registry": short_ref(cls.repo, "registries/live-escape.json"),
            "usage_writer": short_ref(cls.repo, "tools/campaign_usage_ledger.py"),
            "review_protocol": short_ref(cls.repo, "tests/smoke-matrix/reviewed-five-smoke-protocol.json"),
            "model_execution_authorized": False,
            "terminal_claim": False,
            "non_claims": [
                "candidate build is not candidate maturity",
                "candidate build is not model execution authorization",
                "candidate build is not owner acceptance",
            ],
        }
        value["authorization_sha256"] = content_hash(value, "authorization_sha256")
        return value

    @staticmethod
    def _archive_builder(_repo_root: Path, output: Path, profile: str = "execution-mini") -> tuple[int, str]:
        if profile != "execution-mini":
            raise AssertionError(profile)
        output.parent.mkdir(parents=True, exist_ok=True)
        members = [path for path in sorted((ROOT / "skill").rglob("*")) if path.is_file()]
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in members:
                archive.writestr(path.relative_to(ROOT / "skill").as_posix(), path.read_bytes())
        return len(members), hashlib.sha256(output.read_bytes()).hexdigest().upper()

    @classmethod
    def _build_unused_candidate(cls) -> None:
        (cls.repo / "candidate-custody/authorizations").mkdir(parents=True, exist_ok=True)
        auth = cls._candidate_authorization()
        auth_path = cls.repo / "candidate-custody/authorizations/task5-candidate-build-fixture.json"
        write_json(auth_path, auth)
        cls.candidate_record = candidate_builder.build_authorized_candidate(
            repo_root=cls.repo,
            authorization_path=auth_path,
            now=datetime(2026, 7, 12, 0, 2, tzinfo=timezone.utc),
            archive_builder=cls._archive_builder,
        )
        cls.candidate_root = cls.repo / auth["candidate_root"]
        cls.candidate_record_path = cls.candidate_root / "candidate-record.json"
        cls.candidate_readiness_path = cls.candidate_root / "candidate-readiness.json"

    @classmethod
    def _prepare_package_evidence(cls) -> None:
        cls.package_evidence_root = cls.repo / "package-evidence"
        cls.package_evidence_root.mkdir()
        package_root = cls.candidate_root / "extracted"
        parity = parity_checker.build_record(package_root, cls.package_evidence_root, False)
        context_path = cls.package_evidence_root / "context.json"
        context = json.loads(context_path.read_text(encoding="utf-8"))
        context["runtime"]["source_commit"] = cls.source_preflight["source"]["commit_sha"]
        write_json(context_path, context)
        for row in parity["artifacts"]:
            if row["kind"] == "call-context":
                row["sha256"] = hashlib.sha256(context_path.read_bytes()).hexdigest()
                row["byte_count"] = context_path.stat().st_size
        cls.parity_path = cls.package_evidence_root / "package-harness-parity.json"
        write_json(cls.parity_path, parity)
        if context_checker.validate(context, package_root, cls.package_evidence_root)["status"] != "pass":
            raise AssertionError("runtime-context fixture failed")
        if parity_checker.validate(parity, package_root, cls.package_evidence_root, cls.repo)["classification"] != "package-faithful":
            raise AssertionError("package-harness fixture failed")

    @classmethod
    def _retention_source_ref(cls, source: Path, relative: str, payload: bytes) -> dict[str, object]:
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return full_ref(source, relative)

    @classmethod
    def _prepare_retention_export(cls) -> None:
        source = cls.repo / "retention-source"
        source.mkdir()
        refs = {
            "source-commit-receipt": cls._retention_source_ref(source, "receipts/source-commit.json", (cls.repo / "evidence/source-commit.json").read_bytes()),
            "ci-readback": cls._retention_source_ref(source, "receipts/ci-readback.json", (cls.repo / "tests/ci-readback/valid/required-checks-bound-to-pushed-sha.json").read_bytes()),
            "candidate-record": cls._retention_source_ref(source, "candidate/candidate-record.json", cls.candidate_record_path.read_bytes()),
            "candidate-readiness": cls._retention_source_ref(source, "candidate/candidate-readiness.json", cls.candidate_readiness_path.read_bytes()),
            "candidate-archive": cls._retention_source_ref(source, "candidate/package.skill.zip", (cls.candidate_root / cls.candidate_record["archive"]["path"]).read_bytes()),
            "source-preflight": cls._retention_source_ref(source, "evidence/source-preflight.json", cls.source_preflight_path.read_bytes()),
            "live-escape": cls._retention_source_ref(source, "evidence/live-escape.json", (cls.repo / "registries/live-escape.json").read_bytes()),
            "review-protocol": cls._retention_source_ref(source, "evidence/review-protocol.json", (cls.repo / "tests/smoke-matrix/reviewed-five-smoke-protocol.json").read_bytes()),
            "runtime-context": cls._retention_source_ref(source, "evidence/runtime-context.json", (cls.package_evidence_root / "context.json").read_bytes()),
            "package-harness-parity": cls._retention_source_ref(source, "evidence/package-harness-parity.json", cls.parity_path.read_bytes()),
        }
        export_id = "task5-candidate-retention"
        candidate_id = cls.candidate_record["candidate_id"]
        custody = cls.repo / "retention-custody"
        auth = {
            "schema": "daee-evidence-export-authorization-v1",
            "kind": "evidence-export-authorization",
            "manifest_kind": "candidate-readiness-final-manifest",
            "export_id": export_id,
            "scope_id": candidate_id,
            "one_use": True,
            "issued_at": "2026-07-12T12:00:00Z",
            "exported_at": "2026-07-12T12:01:00Z",
            "source_root": str(source.resolve()),
            "evidence_custody_root": str(custody.resolve()),
            "staging_path": f".staging/{export_id}",
            "claim_path": f"claims/{export_id}.json",
            "final_path": f"candidates/{candidate_id}/retention/{export_id}",
            "receipt_path": f"receipts/{export_id}.json",
            "pointer_path": f"pointers/{candidate_id}/head.json",
            "expected_pointer_sha256": None,
            "source_identity": {
                "repository": cls.source_preflight["source"]["repository"],
                "branch": cls.source_preflight["source"]["branch"],
                "ref": cls.source_preflight["source"]["ref"],
                "commit_sha": cls.source_preflight["source"]["commit_sha"],
                "tree_sha": cls.source_preflight["source"]["tree_oid"],
                "source_commit_receipt": refs["source-commit-receipt"],
                "ci_readback": refs["ci-readback"],
            },
            "candidate_identity": {
                "candidate_id": candidate_id,
                "candidate_record": refs["candidate-record"],
                "candidate_readiness": refs["candidate-readiness"],
                "package_sha256": cls.candidate_record["archive"]["sha256"],
                "package_tree_sha256": cls.candidate_record["extracted_tree_sha256"],
                "tree_digest_algorithm": cls.candidate_record["tree_digest_algorithm"],
                "status": "READY_UNUSED",
            },
            "cycle_identity": None,
            "inventory_spec": [
                {
                    "artifact_id": artifact_id,
                    "source_path": reference["path"],
                    "retained_path": reference["path"],
                    "classification": "CONTROL_RECORD",
                    "required": True,
                    "expected_state": "PRESENT",
                }
                for artifact_id, reference in sorted(refs.items())
            ],
            "retention_policy": {
                "mode": "RETAIN_INDEFINITELY",
                "pruning_authorized": False,
                "separate_owner_authorization_required": True,
                "permanent_removal_residue_required": True,
            },
            "model_execution_authorized": False,
            "terminal_claim": False,
            "non_claims": [
                "retention export is not candidate maturity",
                "retention export is not model execution authorization",
                "retention export is not owner acceptance",
            ],
        }
        auth["authorization_sha256"] = content_hash(auth, "authorization_sha256")
        auth_path = cls.repo / "retention-export-authorization.json"
        write_json(auth_path, auth)
        cls.retention_manifest = retention_exporter.export_evidence_bundle(auth_path)
        cls.retention_custody = custody
        cls.retention_final_directory = auth["final_path"]
        cls.retention_manifest_path = custody / auth["final_path"] / "manifest.json"
        cls.retention_receipt_path = custody / auth["receipt_path"]
        if retention_checker.validate_export(custody, custody / auth["final_path"]):
            raise AssertionError("retention fixture failed")

    @classmethod
    def _candidate_identity(cls) -> dict:
        archive_path = cls.candidate_root / cls.candidate_record["archive"]["path"]
        return {
            "candidate_id": cls.candidate_record["candidate_id"],
            "status": "READY_UNUSED",
            "claim_status": "UNCLAIMED",
            "candidate_root": cls.candidate_record["candidate_root"],
            "package_profile": "execution-mini",
            "candidate_record": full_ref(cls.repo, cls.candidate_record_path.relative_to(cls.repo).as_posix()),
            "candidate_readiness": full_ref(cls.repo, cls.candidate_readiness_path.relative_to(cls.repo).as_posix()),
            "archive": full_ref(cls.repo, archive_path.relative_to(cls.repo).as_posix()),
            "tree_digest_algorithm": cls.candidate_record["tree_digest_algorithm"],
            "package_tree_sha256": cls.candidate_record["extracted_tree_sha256"],
        }

    @classmethod
    def _package_evidence(cls) -> dict:
        return {
            "evidence_root": cls.package_evidence_root.relative_to(cls.repo).as_posix(),
            "runtime_context": full_ref(cls.repo, (cls.package_evidence_root / "context.json").relative_to(cls.repo).as_posix()),
            "runtime_context_status": "PASS",
            "runtime_context_proof_mode": "package-faithful",
            "package_harness_parity": full_ref(cls.repo, cls.parity_path.relative_to(cls.repo).as_posix()),
            "package_harness_status": "PASS",
            "package_harness_classification": "package-faithful",
        }

    @classmethod
    def _retention_evidence(cls) -> dict:
        return {
            "custody_root": cls.retention_custody.relative_to(cls.repo).as_posix(),
            "final_directory": cls.retention_final_directory,
            "manifest": full_ref(cls.repo, cls.retention_manifest_path.relative_to(cls.repo).as_posix()),
            "receipt": full_ref(cls.repo, cls.retention_receipt_path.relative_to(cls.repo).as_posix()),
            "status": "RETENTION_GREEN",
            "completeness": "COMPLETE",
            "retained_tree_sha256": cls.retention_manifest["retained_tree_sha256"],
        }

    @classmethod
    def _prepare_independent_review(cls) -> None:
        review = {
            "schema": "daee-no-model-candidate-maturity-v1",
            "kind": "candidate-readiness-independent-review",
            "review_id": "task5-candidate-readiness-review",
            "verdict": "ACCEPT",
            "accountable_owner": IMPLEMENTATION_OWNER,
            "independent_reviewer": "/root/task5_candidate_reviewer",
            "source": copy.deepcopy(cls.source_preflight["source"]),
            "ci_receipt": copy.deepcopy(cls.source_preflight["ci_receipt"]),
            "source_preflight": full_ref(cls.repo, "evidence/source-preflight.json"),
            "candidate": cls._candidate_identity(),
            "package_evidence": cls._package_evidence(),
            "evidence_manifest": full_ref(cls.repo, cls.retention_manifest_path.relative_to(cls.repo).as_posix()),
            "retention_receipt": full_ref(cls.repo, cls.retention_receipt_path.relative_to(cls.repo).as_posix()),
            "independent_from_owner": True,
            "reviewed_at": "2026-07-12T12:24:00Z",
            "terminal_claim": False,
            "model_execution_authorized": False,
            "non_claims": [
                "candidate readiness review is not model execution authorization",
                "candidate readiness review is not reviewed smoke success",
                "candidate readiness review is not owner acceptance",
            ],
        }
        authorization = build_review_authorization(
            review,
            scope="candidate-readiness-review",
            candidate={
                "candidate_id": review["candidate"]["candidate_id"],
                "package_tree_sha256": review["candidate"]["package_tree_sha256"],
            },
            issued_at="2026-07-12T12:23:00Z",
            authorization_path="evidence/candidate-readiness-review-authorization.json",
        )
        cls.review_authorization_path = cls.repo / "evidence/candidate-readiness-review-authorization.json"
        write_json(cls.review_authorization_path, authorization)
        review["review_authorization_id"] = authorization["authorization_id"]
        review["review_authorization"] = full_ref(
            cls.repo,
            cls.review_authorization_path.relative_to(cls.repo).as_posix(),
        )
        review["review_sha256"] = content_hash(review, "review_sha256")
        cls.review_path = cls.repo / "evidence/candidate-readiness-review.json"
        write_json(cls.review_path, review)
        cls.inputs = {
            "source_preflight": full_ref(cls.repo, "evidence/source-preflight.json"),
            "candidate_root": cls.candidate_record["candidate_root"],
            "package_evidence_root": cls.package_evidence_root.relative_to(cls.repo).as_posix(),
            "runtime_context": full_ref(cls.repo, (cls.package_evidence_root / "context.json").relative_to(cls.repo).as_posix()),
            "package_harness_parity": full_ref(cls.repo, cls.parity_path.relative_to(cls.repo).as_posix()),
            "retention_custody_root": cls.retention_custody.relative_to(cls.repo).as_posix(),
            "retention_final_directory": cls.retention_final_directory,
            "candidate_readiness_review": full_ref(cls.repo, cls.review_path.relative_to(cls.repo).as_posix()),
        }

    def setUp(self) -> None:
        authorization = json.loads(self.review_authorization_path.read_text(encoding="utf-8"))
        claim_path = self.repo / authorization["consumption_claim_path"]
        if claim_path.exists():
            claim_path.unlink()

    @contextmanager
    def _temporary_bytes(self, path: Path, replacement: bytes):
        original = path.read_bytes()
        path.write_bytes(replacement)
        try:
            yield
        finally:
            path.write_bytes(original)

    def _valid_verdict(self) -> dict:
        with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
            return maturity_builder.build_candidate_maturity(self.repo, copy.deepcopy(self.inputs))

    def test_candidate_maturity_is_derived_from_complete_no_model_chain(self) -> None:
        verdict = self._valid_verdict()
        self.assertEqual("NO_MODEL_CANDIDATE_MATURE", verdict["status"])
        self.assertEqual("READY_UNUSED", verdict["candidate"]["status"])
        self.assertFalse(verdict["terminal_claim"])
        self.assertFalse(verdict["model_execution_authorized"])
        with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
            self.assertEqual([], maturity_checker.validate_candidate_maturity(verdict, root=self.repo))

    def test_candidate_maturity_publication_is_create_once(self) -> None:
        output = self.repo / "candidate-custody/candidates/task5-candidate-fixture/candidate-maturity.json"
        with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
            maturity_builder.publish_candidate_maturity(self.repo, copy.deepcopy(self.inputs), output)
            with self.assertRaisesRegex(ValueError, "create-once|already exists|replay"):
                maturity_builder.publish_candidate_maturity(self.repo, copy.deepcopy(self.inputs), output)

    def test_unit_source_preflight_is_rejected_by_default_production_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "source preflight|CI receipt|locator|carrier"):
            maturity_builder.build_candidate_maturity(self.repo, copy.deepcopy(self.inputs))

    def test_self_declared_maturity_input_is_rejected(self) -> None:
        inputs = copy.deepcopy(self.inputs)
        inputs["status"] = "NO_MODEL_CANDIDATE_MATURE"
        with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
            with self.assertRaisesRegex(ValueError, "exact|input|self-declared"):
                maturity_builder.build_candidate_maturity(self.repo, inputs)

    def test_candidate_record_claimed_quarantined_and_terminal_states_are_rejected(self) -> None:
        original = json.loads(self.candidate_record_path.read_text(encoding="utf-8"))
        for field, value in (
            ("status", "QUARANTINED"),
            ("status", "CONSUMED_OBSERVED"),
            ("claim_status", "CLAIMED"),
            ("model_execution_authorized", True),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed[field] = value
                changed["record_sha256"] = content_hash(changed, "record_sha256")
                with self._temporary_bytes(self.candidate_record_path, canonical_json_bytes(changed)):
                    with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
                        with self.assertRaisesRegex(ValueError, "candidate|readiness|status|claim|authorization"):
                            maturity_builder.build_candidate_maturity(self.repo, copy.deepcopy(self.inputs))

    def test_escape_maturity_boundary_rejects_open_illustrative_sentinel_and_self_declared(self) -> None:
        source = copy.deepcopy(self.source_preflight)
        live = json.loads((self.repo / "registries/live-escape.json").read_text(encoding="utf-8"))
        variants = []
        illustrative = copy.deepcopy(live); illustrative["registry_role"] = "ILLUSTRATIVE_FIXTURE"; variants.append(illustrative)
        sentinel = copy.deepcopy(live); sentinel["escapes"][0]["scope"]["source_sha256"] = "1" * 64; variants.append(sentinel)
        open_yes = copy.deepcopy(live); open_yes["escapes"][0].update({"deterministic_detectability": "YES", "status": "OPEN", "paid_cycle_eligible": False}); variants.append(open_yes)
        opened = copy.deepcopy(live); opened["escapes"][0].update({"deterministic_detectability": "UNKNOWN", "status": "OPEN", "paid_cycle_eligible": False}); variants.append(opened)
        declared = copy.deepcopy(live); declared["candidate_maturity_status"] = "MATURE"; variants.append(declared)
        for value in variants:
            with self.subTest(role=value.get("registry_role"), declared="candidate_maturity_status" in value):
                with self.assertRaisesRegex(ValueError, "escape|LIVE_EVIDENCE|scope|maturity|UNKNOWN|illustrative"):
                    maturity_checker._validate_escape_for_maturity(value, source, root=self.repo)

    def test_registry_and_protocol_role_substitution_is_rejected(self) -> None:
        record = copy.deepcopy(self.candidate_record)
        source = copy.deepcopy(self.source_preflight)
        for field, source_role in (("input_registry", "input"), ("validation_registry", "validation"), ("producer_registry", "producer"), ("escape_registry", "escape"), ("review_protocol", "review_protocol")):
            with self.subTest(field=field):
                changed = copy.deepcopy(record)
                changed[field] = changed["usage_writer"]
                with self.assertRaisesRegex(ValueError, "registry|protocol|role"):
                    maturity_checker._validate_candidate_registry_joins(changed, source)
                self.assertEqual(source["registries"][source_role]["sha256"], record[field]["sha256"])

    def test_source_commit_tree_ref_and_candidate_identity_drift_are_rejected(self) -> None:
        verdict = self._valid_verdict()
        mutations = (
            ("source-commit", lambda v: v["source"].__setitem__("commit_sha", "9" * 40)),
            ("source-tree", lambda v: v["source"].__setitem__("tree_oid", "8" * 40)),
            ("source-ref", lambda v: v["source"].__setitem__("ref", "refs/heads/other")),
            ("candidate-tree", lambda v: v["candidate"].__setitem__("package_tree_sha256", "7" * 64)),
            ("candidate-status", lambda v: v["candidate"].__setitem__("status", "QUARANTINED")),
            ("terminal-claim", lambda v: v.__setitem__("terminal_claim", True)),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(verdict)
                mutate(changed)
                changed["verdict_sha256"] = content_hash(changed, "verdict_sha256")
                with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
                    self.assertTrue(maturity_checker.validate_candidate_maturity(changed, root=self.repo))

    def test_package_runtime_context_and_parity_drift_are_rejected(self) -> None:
        verdict = self._valid_verdict()
        for field in ("runtime_context", "package_harness_parity"):
            with self.subTest(field=field):
                changed = copy.deepcopy(verdict)
                changed["package_evidence"][field]["sha256"] = "0" * 64
                changed["verdict_sha256"] = content_hash(changed, "verdict_sha256")
                with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
                    self.assertTrue(maturity_checker.validate_candidate_maturity(changed, root=self.repo))

    def test_retention_manifest_and_receipt_drift_are_rejected(self) -> None:
        for path in (self.retention_manifest_path, self.retention_receipt_path):
            with self.subTest(path=path.name):
                with self._temporary_bytes(path, path.read_bytes() + b" "):
                    with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
                        with self.assertRaisesRegex(ValueError, "retention|hash|receipt|manifest|export"):
                            maturity_builder.build_candidate_maturity(self.repo, copy.deepcopy(self.inputs))

    def test_independent_review_separation_and_exact_evidence_binding_are_required(self) -> None:
        review = json.loads(self.review_path.read_text(encoding="utf-8"))
        mutations = (
            lambda v: v.__setitem__("independent_reviewer", v["accountable_owner"]),
            lambda v: v["candidate"]["archive"].__setitem__("sha256", "0" * 64),
            lambda v: v["evidence_manifest"].__setitem__("sha256", "0" * 64),
        )
        for mutate in mutations:
            changed = copy.deepcopy(review)
            mutate(changed)
            changed["review_sha256"] = content_hash(changed, "review_sha256")
            with self._temporary_bytes(self.review_path, canonical_json_bytes(changed)):
                inputs = copy.deepcopy(self.inputs)
                inputs["candidate_readiness_review"] = full_ref(self.repo, self.review_path.relative_to(self.repo).as_posix())
                with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
                    with self.assertRaisesRegex(ValueError, "review|owner|candidate|manifest|evidence"):
                        maturity_builder.build_candidate_maturity(self.repo, inputs)

    def test_candidate_review_authorization_binds_candidate_tree_freeze_and_review_order(self) -> None:
        review = json.loads(self.review_path.read_text(encoding="utf-8"))
        authorization = json.loads(self.review_authorization_path.read_text(encoding="utf-8"))
        cases = (
            ("candidate-id", lambda a: a["candidate"].__setitem__("candidate_id", "invented-candidate"), None),
            ("candidate-tree", lambda a: a["candidate"].__setitem__("package_tree_sha256", "7" * 64), None),
            ("source", lambda a: a["source"].__setitem__("commit_sha", "8" * 40), None),
            ("freeze", lambda a: a.__setitem__("freeze_sha256", "6" * 64), None),
            ("replay", None, lambda r: r.__setitem__("review_id", "replayed-candidate-review")),
            ("reviewer-mismatch", None, lambda r: r.__setitem__("independent_reviewer", "/root/different_candidate_reviewer")),
            ("ordering", lambda a: a.__setitem__("issued_at", "2026-07-12T12:25:00Z"), None),
            ("one-use", lambda a: a.__setitem__("one_use", False), None),
        )
        for label, mutate_authorization, mutate_review in cases:
            with self.subTest(label=label):
                changed_authorization = copy.deepcopy(authorization)
                changed_review = copy.deepcopy(review)
                if mutate_authorization is not None:
                    mutate_authorization(changed_authorization)
                    changed_authorization["authorization_id"] = review_authorization_id(changed_authorization)
                changed_authorization_path = self.repo / f"evidence/{label}-candidate-review-authorization.json"
                write_json(changed_authorization_path, changed_authorization)
                changed_review["review_authorization_id"] = changed_authorization["authorization_id"]
                changed_review["review_authorization"] = full_ref(
                    self.repo,
                    changed_authorization_path.relative_to(self.repo).as_posix(),
                )
                if mutate_review is not None:
                    mutate_review(changed_review)
                changed_review["review_sha256"] = content_hash(changed_review, "review_sha256")
                with self._temporary_bytes(self.review_path, canonical_json_bytes(changed_review)):
                    inputs = copy.deepcopy(self.inputs)
                    inputs["candidate_readiness_review"] = full_ref(
                        self.repo,
                        self.review_path.relative_to(self.repo).as_posix(),
                    )
                    with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
                        with self.assertRaisesRegex(ValueError, "authorization|candidate|tree|source|freeze|reviewer|timestamp|one.use|review"):
                            maturity_builder.build_candidate_maturity(self.repo, inputs)

    def test_candidate_review_rejects_same_authorization_and_review_id_with_changed_reviewed_at(self) -> None:
        with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
            maturity_builder.build_candidate_maturity(self.repo, copy.deepcopy(self.inputs))
        authorization = json.loads(self.review_authorization_path.read_text(encoding="utf-8"))
        claim_path = self.repo / authorization["consumption_claim_path"]
        self.assertTrue(claim_path.is_file())
        claim_before = claim_path.read_bytes()
        review = json.loads(self.review_path.read_text(encoding="utf-8"))
        review["reviewed_at"] = "2026-07-12T12:24:01Z"
        review["review_sha256"] = content_hash(review, "review_sha256")
        with self._temporary_bytes(self.review_path, canonical_json_bytes(review)):
            inputs = copy.deepcopy(self.inputs)
            inputs["candidate_readiness_review"] = full_ref(
                self.repo,
                self.review_path.relative_to(self.repo).as_posix(),
            )
            with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
                with self.assertRaisesRegex(ValueError, "authorization|claim|consum|replay|review"):
                    maturity_builder.build_candidate_maturity(self.repo, inputs)
        self.assertEqual(claim_before, claim_path.read_bytes())

    def test_candidate_review_rejects_duplicated_authorization_locator(self) -> None:
        with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
            maturity_builder.build_candidate_maturity(self.repo, copy.deepcopy(self.inputs))
        authorization = json.loads(self.review_authorization_path.read_text(encoding="utf-8"))
        claim_path = self.repo / authorization["consumption_claim_path"]
        claim_before = claim_path.read_bytes()
        duplicate_path = self.repo / "evidence/duplicate-candidate-review-authorization.json"
        write_json(duplicate_path, authorization)
        review = json.loads(self.review_path.read_text(encoding="utf-8"))
        review["review_authorization"] = full_ref(
            self.repo,
            duplicate_path.relative_to(self.repo).as_posix(),
        )
        review["review_sha256"] = content_hash(review, "review_sha256")
        with self._temporary_bytes(self.review_path, canonical_json_bytes(review)):
            inputs = copy.deepcopy(self.inputs)
            inputs["candidate_readiness_review"] = full_ref(
                self.repo,
                self.review_path.relative_to(self.repo).as_posix(),
            )
            with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
                with self.assertRaisesRegex(ValueError, "authorization|claim|consum|collision|locator|replay"):
                    maturity_builder.build_candidate_maturity(self.repo, inputs)
        self.assertEqual(claim_before, claim_path.read_bytes())

    def test_verdict_exact_nonclaims_cannot_be_replaced(self) -> None:
        verdict = self._valid_verdict()
        verdict["non_claims"] = [
            "model execution authorized",
            "reviewed smoke succeeded",
            "owner acceptance recorded",
        ]
        verdict["verdict_sha256"] = content_hash(verdict, "verdict_sha256")
        with patch.object(maturity_checker, "validate_source_preflight", return_value=[]):
            self.assertTrue(maturity_checker.validate_candidate_maturity(verdict, root=self.repo))


if __name__ == "__main__":
    unittest.main()
