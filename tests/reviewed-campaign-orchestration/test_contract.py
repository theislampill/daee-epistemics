from __future__ import annotations

import hashlib
import json
import copy
import ntpath
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from check_parallel_dispatch_manifest import validate_dispatch_manifest
from campaign_usage_ledger import _provider_facts, head_snapshot, recover_orphan, reserve, settle, validate_head
from build_cold_review_packet import build as build_cold_review_packet
import execution_tooling_manifest as tooling_manifest
from reviewed_campaign_orchestrator import (
    CampaignError,
    _contained,
    _matrix_ref,
    claim_initial_assessments as _claim_initial_assessments,
    extract_mature_candidate_identity,
    ingest_final_adjudication,
    run_cold_review_cohort,
    run_producer_cohort,
    simulate_paired_gpt_opus_canary,
    validate_retry_lineage,
    record_sha256,
)


def claim_initial_assessments(*args, **kwargs):
    """Legacy deterministic-fake helper; production tests use the real API directly."""
    if "allow_test_fixture" in kwargs:
        raise AssertionError("fake helper owns the explicit test-only compatibility switch")
    return _claim_initial_assessments(*args, allow_test_fixture=True, **kwargs)


CASES = [
    "gate88-secularism",
    "gate88-khaybar",
    "gate88-trinitarian-j173",
    "gate88-tst-lillard",
    "gate88-torah-quran-source-authentication",
]


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def continuation_authorization_id(value: dict[str, object]) -> str:
    unsigned = {key: copy.deepcopy(item) for key, item in value.items() if key != "authorization_id"}
    return hashlib.sha256(b"daee-reviewed-campaign-retry-continuation-v1\0" + canonical(unsigned)).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def write_pretty_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(root: Path, path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def synthetic_execution_tooling_manifest(source_commit: str) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": "daee-stage07-execution-tooling-manifest-v1",
        "kind": "execution-tooling-manifest",
        "source_commit": source_commit,
        "source_tree": "a" * 40,
        "profile": "stage07-release",
        "membership": {"snapshot_roots": ["tools", "schema"], "runtime_resources": ["tests/fixture"]},
        "result_order": ["fixture-check"],
        "file_count": 1,
        "aggregate_algorithm": "sha256-domain-canonical-json-stage07-tooling-v1",
        "aggregate_sha256": "",
        "files": [{"path": "tools/fixture.py", "git_mode": "100644", "blob_oid": "b" * 40, "byte_count": 8, "sha256": "c" * 64}],
    }
    value["aggregate_sha256"] = tooling_manifest._aggregate_sha256(value)
    return value


class MatrixSourceReferenceContractTests(unittest.TestCase):
    def test_live_matrix_admits_exact_hash_bound_governed_source_json_bytes(self) -> None:
        for role, relative in (
            ("input_registry", "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json"),
            ("review_protocol", "tests/smoke-matrix/reviewed-five-smoke-protocol.json"),
        ):
            with self.subTest(role=role):
                path = ROOT / relative
                raw = path.read_bytes()
                self.assertNotEqual(raw, canonical(json.loads(raw)))
                record, admitted_ref, admitted_raw = _matrix_ref(
                    ROOT,
                    {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()},
                    role,
                )
                self.assertIsInstance(record, dict)
                self.assertEqual(admitted_raw, raw)
                self.assertEqual(
                    admitted_ref,
                    {"path": relative, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
                )

    def test_live_matrix_keeps_generated_control_plane_json_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "campaign-authorization.json"
            raw = b'{\n  "schema": "reviewed-campaign-owner-authorization-v1"\n}\n'
            path.write_bytes(raw)
            with self.assertRaisesRegex(
                CampaignError,
                "CAMPAIGN_AUTHORIZATION_CANONICAL_JSON_REQUIRED",
            ):
                _matrix_ref(
                    root,
                    {"path": path.name, "sha256": hashlib.sha256(raw).hexdigest()},
                    "campaign_authorization",
                )

    def test_live_matrix_rejects_duplicate_keys_in_governed_source_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "input-registry.json"
            raw = b'{"schema":"first","schema":"second"}\n'
            path.write_bytes(raw)
            with self.assertRaisesRegex(CampaignError, "INPUT_REGISTRY_JSON_INVALID"):
                _matrix_ref(
                    root,
                    {"path": path.name, "sha256": hashlib.sha256(raw).hexdigest()},
                    "input_registry",
                )

    def test_live_matrix_rejects_governed_source_content_address_drift(self) -> None:
        relative = "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json"
        with self.assertRaisesRegex(CampaignError, "INPUT_REGISTRY_CONTENT_ADDRESS"):
            _matrix_ref(ROOT, {"path": relative, "sha256": "0" * 64}, "input_registry")


class FakeNoDispatchAdapter:
    def __init__(self, *, lane: str = "producer") -> None:
        self.lane = lane
        self.log: list[tuple[str, str]] = []

    def capability(self) -> dict[str, object]:
        return {
            "schema": "reviewed-campaign-provider-capability-v1",
            "adapter_kind": "deterministic-fake-no-dispatch",
            "adapter_version": "deterministic-fake-v1",
            "host_application_version": "deterministic-test-host-v1",
            "test_only": True,
            "paid_provider_reachable": False,
            "live_execution_authorized": False,
        }

    def submit(self, call: dict[str, object]) -> dict[str, object]:
        subject = str(call["subject_id"])
        self.log.append(("submit", subject))
        return {
            "handle_id": f"fake:{subject}",
            "execution_custody_sha256": record_sha256(call),
            "accepted": True,
            "in_flight": True,
        }

    def observe(self, handle: str, call: dict[str, object]) -> dict[str, object]:
        subject = str(call["subject_id"])
        self.log.append(("observe", subject))
        return {
            "content_utf8": f"deterministic fake result for {subject}\n",
            "structural_status": "PASS",
            "provider_call_id": handle,
            "execution_custody_sha256": record_sha256(call),
            "usage": {"status": "RECORDED", "input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "cost": {"unit": "usd", "value": "0"},
        }


class PaidProviderTrap:
    calls = 0

    def capability(self) -> dict[str, object]:
        return {
            "schema": "reviewed-campaign-provider-capability-v1",
            "adapter_kind": "codex-live",
            "adapter_version": "codex-live-v1",
            "host_application_version": "codex-live-host-v1",
            "test_only": False,
            "paid_provider_reachable": True,
            "live_execution_authorized": False,
        }

    def submit(self, _call: dict[str, object]) -> str:
        self.calls += 1
        raise AssertionError("paid provider must remain unreachable")

    def observe(self, _handle: str, _call: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        raise AssertionError("paid provider must remain unreachable")


class FailingObserveAdapter(FakeNoDispatchAdapter):
    def observe(self, handle: str, call: dict[str, object]) -> dict[str, object]:
        subject = str(call["subject_id"])
        self.log.append(("observe-failure", subject))
        raise RuntimeError("deterministic injected observation failure")


class RecordingCustodyAdapter:
    def __init__(self, *, corrupt: str | None = None) -> None:
        self.corrupt = corrupt
        self.submitted: list[dict[str, object]] = []
        self.observed: list[dict[str, object]] = []

    def capability(self) -> dict[str, object]:
        return FakeNoDispatchAdapter().capability()

    def submit(self, execution_custody: dict[str, object]) -> dict[str, object]:
        self.submitted.append(copy.deepcopy(execution_custody))
        custody_sha = record_sha256(execution_custody)
        result: dict[str, object] = {
            "handle_id": f"recording:{execution_custody.get('lane')}:{execution_custody.get('case_id')}",
            "execution_custody_sha256": custody_sha,
            "accepted": True,
            "in_flight": True,
        }
        if self.corrupt == "submit-omit-custody":
            result.pop("execution_custody_sha256")
        elif self.corrupt == "submit-substitute-custody":
            result["execution_custody_sha256"] = "f" * 64
        return result

    def observe(self, handle: str, execution_custody: dict[str, object]) -> dict[str, object]:
        self.observed.append(copy.deepcopy(execution_custody))
        custody_sha = record_sha256(execution_custody)
        result: dict[str, object] = {
            "content_utf8": f"deterministic recording result for {execution_custody.get('case_id')}\n",
            "structural_status": "PASS",
            "provider_call_id": handle,
            "execution_custody_sha256": custody_sha,
            "usage": {"status": "RECORDED", "input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "cost": {"unit": "usd", "value": "0"},
        }
        if self.corrupt == "observe-omit-custody":
            result.pop("execution_custody_sha256")
        elif self.corrupt == "observe-substitute-custody":
            result["execution_custody_sha256"] = "e" * 64
        return result


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        registry_src = ROOT / "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json"
        protocol_src = ROOT / "tests/smoke-matrix/reviewed-five-smoke-protocol.json"
        self.registry = root / "inputs/registry.json"
        self.protocol = root / "inputs/review-protocol.json"
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        self.registry.write_bytes(registry_src.read_bytes())
        self.protocol.write_bytes(protocol_src.read_bytes())
        self.source_commit = "1" * 40
        self.package_sha = "2" * 64
        self.package_tree_sha = "3" * 64
        self.candidate_id = "candidate-task6-test"
        self.candidate = root / "inputs/candidate-maturity.json"
        self.package = root / "inputs/package-record.json"
        self.preflight = root / "inputs/source-preflight.json"
        write_json(
            self.package,
            {
                "schema": "reviewed-campaign-test-package-binding-v1",
                "candidate_id": self.candidate_id,
                "source_commit": self.source_commit,
                "package_sha256": self.package_sha,
                "package_tree_sha256": self.package_tree_sha,
                "registry_sha256": digest(self.registry),
            },
        )
        write_json(
            self.preflight,
            {
                "schema": "reviewed-campaign-test-preflight-v1",
                "kind": "source-preflight",
                "status": "NO_MODEL_SOURCE_PREFLIGHT_GREEN",
                "source_commit": self.source_commit,
                "registry_sha256": digest(self.registry),
                "review_protocol_sha256": digest(self.protocol),
                "model_execution_authorized": False,
                "test_fixture_only": True,
            },
        )
        write_json(
            self.candidate,
            {
                "schema": "reviewed-campaign-test-candidate-maturity-v1",
                "kind": "candidate-maturity",
                "status": "NO_MODEL_CANDIDATE_MATURE",
                "candidate_id": self.candidate_id,
                "candidate_state": "READY_UNUSED",
                "claim_status": "UNCLAIMED",
                "source_commit": self.source_commit,
                "package_record_sha256": digest(self.package),
                "package_sha256": self.package_sha,
                "package_tree_sha256": self.package_tree_sha,
                "source_preflight_sha256": digest(self.preflight),
                "registry_sha256": digest(self.registry),
                "review_protocol_sha256": digest(self.protocol),
                "model_execution_authorized": False,
                "test_fixture_only": True,
            },
        )
        self.authorization = root / "authorizations/producer.json"
        write_json(self.authorization, self.producer_authorization())

    def producer_authorization(self, **changes: object) -> dict[str, object]:
        value: dict[str, object] = {
            "schema": "reviewed-campaign-cohort-authorization-v1",
            "kind": "producer-cohort",
            "authorization_id": "task6-producer-auth-1",
            "one_use": True,
            "execution_mode": "DETERMINISTIC_FAKE_NO_DISPATCH",
            "test_only": True,
            "live_execution_authorized": False,
            "campaign_authorization_sha256": "4" * 64,
            "candidate_id": self.candidate_id,
            "cycle_or_review_batch_id": "task6-cycle-1",
            "source_commit": self.source_commit,
            "candidate_maturity": ref(self.root, self.candidate),
            "package_record": ref(self.root, self.package),
            "source_preflight": ref(self.root, self.preflight),
            "registry": ref(self.root, self.registry),
            "review_protocol": ref(self.root, self.protocol),
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "adapter_version": "deterministic-fake-v1",
            "host_application_version": "deterministic-test-host-v1",
            "provider_settings": {
                "response_surface": "package-faithful",
                "parallelism": 5,
                "fresh_context_per_case": True,
                "submit_before_observe": True,
            },
            "cohort_size": 5,
            "cohort_protocol": "barrier-five-submit-before-await-v1",
            "case_ids": CASES,
            "isolated_root_prefix": "producer/isolated",
            "usage_ledger_root": "usage",
            "authorization_claim_path": "claims/producer-authorization.json",
            "candidate_claim_path": "claims/candidate.json",
            "retry_lineage": {"attempt_index": 1, "continuation_authorization": None},
        }
        value.update(changes)
        return value

    def build_packets(self, completion: dict[str, object]) -> list[dict[str, object]]:
        packet_set: list[dict[str, object]] = []
        results = completion["results"]
        assert isinstance(results, list)
        for index, (case_id, result) in enumerate(zip(CASES, results), 1):
            assert isinstance(result, dict)
            packet_root = self.root / f"private-review-packets/{index:02d}-{case_id}"
            packet_root.mkdir(parents=True, exist_ok=True)
            input_path = packet_root / "input.txt"
            output_path = packet_root / "output.md"
            input_path.write_text(f"canonical input for {case_id}\n", encoding="utf-8", newline="\n")
            output_ref = result["output"]
            assert isinstance(output_ref, dict)
            output_path.write_bytes((self.root / str(output_ref["path"])).read_bytes())
            for stage in range(1, 9):
                write_json(packet_root / f"stage-{stage:02d}.json", {"stage": stage, "case_id": case_id})
            write_json(packet_root / "witness.json", {"case_id": case_id, "kind": "witness"})
            write_json(packet_root / "audit.json", {"case_id": case_id, "kind": "audit"})
            write_json(packet_root / "body.json", {"case_id": case_id, "kind": "body"})
            bindings = {
                "case_id": case_id,
                "cycle_id": completion["cycle_id"],
                "protocol_id": "reviewed-five-smoke-v1",
                "input_sha256": digest(input_path),
                "output_sha256": digest(output_path),
            }
            write_json(
                packet_root / "review-authorization.json",
                {
                    "schema": "daee-review-authorization-v1",
                    **bindings,
                    "authorization_id": f"packet-review-{index:02d}",
                    "one_use": True,
                },
            )
            write_json(
                packet_root / "anti-answer-bank.json",
                {"schema": "daee-anti-answer-bank-proof-v1", **bindings, "status": "PASS"},
            )
            spec = {
                "packet_id": f"packet-{index:02d}",
                "protocol_id": "reviewed-five-smoke-v1",
                "case_id": case_id,
                "cycle_id": completion["cycle_id"],
                "retry_mode": "initial",
                "input": ref(packet_root, input_path),
                "output": ref(packet_root, output_path),
                "purpose": "Cold reconstruction and independent review.",
                "public_rubric": "Reconstruct the answer before grading it.",
                "stage_records": [ref(packet_root, packet_root / f"stage-{stage:02d}.json") for stage in range(1, 9)],
                "witness_refs": [ref(packet_root, packet_root / "witness.json")],
                "audit_refs": [ref(packet_root, packet_root / "audit.json")],
                "body_refs": [ref(packet_root, packet_root / "body.json")],
                "review_authorization": ref(packet_root, packet_root / "review-authorization.json"),
                "anti_answer_bank_proof": ref(packet_root, packet_root / "anti-answer-bank.json"),
            }
            spec_path = packet_root / "spec.json"
            write_json(spec_path, spec)
            manifest, _payload = build_cold_review_packet(spec_path, packet_root, "built")
            packet_set.append(
                {
                    "case_id": case_id,
                    "packet_root": packet_root.relative_to(self.root).as_posix(),
                    "manifest": ref(packet_root, manifest),
                    "input_sha256": digest(input_path),
                    "output_sha256": digest(output_path),
                }
            )
        return packet_set

    def cold_authorization(
        self,
        completion: dict[str, object],
        assessment_claim: dict[str, object],
        packet_set: list[dict[str, object]],
        *,
        output_name: str = "cold-review.json",
        **changes: object,
    ) -> Path:
        completion_path = self.root / "producer/completion.json"
        assessment_path = self.root / "human-initial-assessments/claim.json"
        value: dict[str, object] = {
            "schema": "reviewed-campaign-cohort-authorization-v1",
            "kind": "cold-review-cohort",
            "authorization_id": "task6-cold-review-auth-1",
            "one_use": True,
            "execution_mode": "DETERMINISTIC_FAKE_NO_DISPATCH",
            "test_only": True,
            "live_execution_authorized": False,
            "campaign_authorization_sha256": "4" * 64,
            "candidate_id": self.candidate_id,
            "cycle_or_review_batch_id": "task6-review-1",
            "producer_cycle_id": completion["cycle_id"],
            "source_commit": self.source_commit,
            "candidate_maturity": ref(self.root, self.candidate),
            "package_record": ref(self.root, self.package),
            "source_preflight": ref(self.root, self.preflight),
            "registry": ref(self.root, self.registry),
            "review_protocol": ref(self.root, self.protocol),
            "producer_completion": ref(self.root, completion_path),
            "assessment_claim": ref(self.root, assessment_path),
            "packet_set": packet_set,
            "model": "gpt-5.6-sol",
            "reasoning_effort": "xhigh",
            "adapter_version": "deterministic-fake-v1",
            "host_application_version": "deterministic-test-host-v1",
            "provider_settings": {
                "response_surface": "cold-review-packet",
                "parallelism": 5,
                "fresh_context_per_case": True,
                "prior_conversation_supplied": False,
                "cross_case_context_supplied": False,
                "submit_before_observe": True,
            },
            "cohort_size": 5,
            "cohort_protocol": "independent-cold-review-v1",
            "dispatch_barrier_protocol": "barrier-five-submit-before-await-v1",
            "case_ids": CASES,
            "isolated_root_prefix": "cold-review/isolated",
            "usage_ledger_root": "usage",
            "authorization_claim_path": "claims/cold-review-authorization.json",
            "packet_disclosure_path": "cold-review/packet-disclosure.json",
            "retry_lineage": {"attempt_index": 1, "continuation_authorization": None},
        }
        value.update(changes)
        path = self.root / f"authorizations/{output_name}"
        write_json(path, value)
        return path

    def retry_continuation(
        self,
        *,
        lane: str,
        prior_batch_id: str,
        next_batch_id: str,
        prior_authorization: Path,
        prior_incident: Path,
        prior_finalizer: Path,
        changes: dict[str, object] | None = None,
    ) -> Path:
        value: dict[str, object] = {
            "schema": "reviewed-campaign-retry-continuation-authorization-v1",
            "kind": "retry-continuation",
            "authorization_id": "",
            "issuer_identity": "/root",
            "implementation_owner_identity": "/root/task6_no_dispatch",
            "candidate_id": self.candidate_id,
            "lane": lane,
            "prior_batch_id": prior_batch_id,
            "prior_attempt_index": 1,
            "next_batch_id": next_batch_id,
            "next_attempt_index": 2,
            "prior_cohort_authorization": ref(self.root, prior_authorization),
            "prior_cohort_authorization_sha256": digest(prior_authorization),
            "prior_incident": ref(self.root, prior_incident),
            "prior_finalizer": ref(self.root, prior_finalizer),
            "expected_usage_head_sha256": head_snapshot(self.root / "usage")["head_sha256"],
            "claim_path": f"claims/retry-continuations/{lane}-{next_batch_id}-attempt-02.claim.json",
            "one_use": True,
        }
        if changes:
            value.update(changes)
        value["authorization_id"] = continuation_authorization_id(value)
        path = self.root / f"authorizations/retry-continuations/owner-issued/{lane}-{next_batch_id}-attempt-02.authorization.json"
        write_json(path, value)
        return path


class ReviewedCampaignOrchestrationTests(unittest.TestCase):
    def _prepare_cold_authorization(self, fixture: Fixture) -> Path:
        producer = run_producer_cohort(
            fixture.root,
            fixture.authorization,
            FakeNoDispatchAdapter(),
            allow_test_fixture=True,
        )
        assessments = [
            {
                "case_id": case_id,
                "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest(),
            }
            for case_id in CASES
        ]
        claim = claim_initial_assessments(
            fixture.root,
            producer,
            assessments,
            claimant="human:task6-assessor",
        )
        packets = fixture.build_packets(producer)
        return fixture.cold_authorization(producer, claim, packets)

    def _complete_success_lane(self, fixture: Fixture, lane: str) -> tuple[Path, Path]:
        if lane == "producer":
            authorization = fixture.authorization
            run_producer_cohort(
                fixture.root,
                authorization,
                FakeNoDispatchAdapter(),
                allow_test_fixture=True,
            )
        else:
            authorization = self._prepare_cold_authorization(fixture)
            run_cold_review_cohort(
                fixture.root,
                authorization,
                FakeNoDispatchAdapter(lane="cold-review"),
                allow_test_fixture=True,
            )
        return authorization, fixture.root / lane / "observation-finalizer.json"

    def test_portable_path_custody_rejects_hostile_read_and_write_forms_before_touch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-portable-path-custody-") as temp:
            base = Path(temp)
            custody = base / "custody"
            inside = custody / "inputs/candidate.json"
            outside = base / "escaped-target.json"
            write_json(inside, {"status": "inside"})
            outside.write_bytes(b"outside sentinel\n")
            outside_raw = outside.read_bytes()
            inside_raw = inside.read_bytes()
            drive_relative = f"{outside.drive or 'C:'}escaped-target.json"
            rooted_tail = str(outside).replace(outside.anchor, "", 1).lstrip("\\/")
            hostile = {
                "rooted-backslash": f"\\{rooted_tail}",
                "rooted-forward": f"/{rooted_tail.replace(chr(92), '/')}",
                "drive-absolute": str(outside),
                "drive-relative": drive_relative,
                "unc": f"\\\\localhost\\{(outside.drive or 'C:').rstrip(':')}$\\{rooted_tail}",
                "device": f"\\\\?\\{outside}",
                "traversal": "../escaped-target.json",
                "backslash-alias": "inputs\\candidate.json",
                "ads": "inputs/candidate.json:review",
                "empty": "",
                "dot": ".",
                "empty-component": "inputs//candidate.json",
                "dot-component": "inputs/./candidate.json",
                "trailing-separator": "inputs/candidate.json/",
                "trailing-dot": "inputs/candidate.json.",
                "trailing-space": "inputs/candidate.json ",
                "reserved-device": "inputs/NUL.json",
                "c0-control": "inputs/candidate\x01.json",
            }
            initial_tree = sorted(path.relative_to(custody).as_posix() for path in custody.rglob("*"))
            for lane in ("producer", "cold-review"):
                for boundary, must_exist in (("read", True), ("write", False)):
                    for name, value in hostile.items():
                        with self.subTest(lane=lane, boundary=boundary, path=name):
                            with self.assertRaisesRegex(CampaignError, "PORTABLE_RELATIVE_PATH_REQUIRED"):
                                _contained(
                                    custody,
                                    value,
                                    f"{lane}_{boundary}_canary",
                                    must_exist=must_exist,
                                )
                            self.assertEqual(outside.read_bytes(), outside_raw)
                            self.assertEqual(inside.read_bytes(), inside_raw)
                            self.assertEqual(
                                sorted(path.relative_to(custody).as_posix() for path in custody.rglob("*")),
                                initial_tree,
                            )

    def test_portable_path_custody_accepts_ordinary_contained_read_and_write_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-portable-path-contained-") as temp:
            custody = Path(temp)
            inside = custody / "inputs/candidate.json"
            write_json(inside, {"status": "inside"})
            for lane in ("producer", "cold-review"):
                with self.subTest(lane=lane, boundary="read"):
                    self.assertEqual(
                        _contained(custody, "inputs/candidate.json", f"{lane}_read_canary", must_exist=True),
                        inside,
                    )
                with self.subTest(lane=lane, boundary="write"):
                    destination = _contained(
                        custody,
                        f"claims/{lane}.json",
                        f"{lane}_write_canary",
                        must_exist=False,
                    )
                    self.assertEqual(destination, custody / f"claims/{lane}.json")
                    self.assertFalse(destination.exists())

    def test_isolated_root_prefix_rejects_hostile_forms_before_campaign_mutation_or_dispatch(self) -> None:
        def tree_snapshot(root: Path) -> tuple[list[str], dict[str, bytes]]:
            directories = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())
            files = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            return directories, files

        for lane in ("producer", "cold-review"):
            with tempfile.TemporaryDirectory(prefix=f"daee-task6-isolated-prefix-paths-{lane}-") as temp:
                base = Path(temp)
                custody = base / "custody"
                fixture = Fixture(custody)
                if lane == "producer":
                    authorization = fixture.authorization
                    head_before = None
                else:
                    authorization = self._prepare_cold_authorization(fixture)
                    head_before = head_snapshot(fixture.root / "usage")
                outside = base / "escaped-isolated-root"
                outside.mkdir()
                outside_sentinel = outside / "sentinel.txt"
                outside_sentinel.write_bytes(b"outside sentinel\n")
                rooted_tail = str(outside).replace(outside.anchor, "", 1).lstrip("\\/")
                drive = outside.drive or "C:"
                hostile = {
                    "rooted-backslash": f"\\{rooted_tail}",
                    "rooted-forward": f"/{rooted_tail.replace(chr(92), '/')}",
                    "drive-qualified": str(outside),
                    "drive-relative": f"{drive}escaped-isolated-root",
                    "unc": f"\\\\localhost\\{drive.rstrip(':')}$\\{rooted_tail}",
                    "device": f"\\\\?\\{outside}",
                    "ads": "isolated/workers:review",
                    "reserved-device": "isolated/NUL",
                    "traversal": "../escaped-isolated-root",
                    "backslash-alias": "isolated\\workers",
                    "empty-component": "isolated//workers",
                    "dot-component": "isolated/./workers",
                    "trailing-separator": "isolated/workers/",
                    "trailing-dot": "isolated/workers.",
                    "trailing-space": "isolated/workers ",
                    "control": "isolated/workers\x01",
                }
                for name, prefix in hostile.items():
                    with self.subTest(lane=lane, prefix=name):
                        authorization_value = json.loads(authorization.read_text(encoding="utf-8"))
                        authorization_value["isolated_root_prefix"] = prefix
                        write_json(authorization, authorization_value)
                        custody_before = tree_snapshot(fixture.root)
                        outside_before = outside_sentinel.read_bytes()
                        adapter = FakeNoDispatchAdapter(lane=lane)

                        with self.assertRaisesRegex(CampaignError, "PORTABLE_RELATIVE_PATH_REQUIRED"):
                            if lane == "producer":
                                run_producer_cohort(
                                    fixture.root,
                                    authorization,
                                    adapter,
                                    allow_test_fixture=True,
                                )
                            else:
                                run_cold_review_cohort(
                                    fixture.root,
                                    authorization,
                                    adapter,
                                    allow_test_fixture=True,
                                )

                        self.assertEqual(adapter.log, [])
                        self.assertEqual(tree_snapshot(fixture.root), custody_before)
                        self.assertEqual(outside_sentinel.read_bytes(), outside_before)
                        if lane == "producer":
                            self.assertFalse((fixture.root / "claims").exists())
                            self.assertFalse((fixture.root / "usage").exists())
                        else:
                            self.assertFalse((fixture.root / "claims/cold-review-authorization.json").exists())
                            self.assertFalse((fixture.root / "cold-review/packet-disclosure.json").exists())
                            self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)

    def test_isolated_root_prefix_accepts_ordinary_contained_producer_and_cold_paths(self) -> None:
        for lane, prefix in (
            ("producer", "isolated/producer-workers"),
            ("cold-review", "isolated/cold-workers"),
        ):
            with self.subTest(lane=lane), tempfile.TemporaryDirectory(
                prefix=f"daee-task6-isolated-prefix-contained-{lane}-"
            ) as temp:
                fixture = Fixture(Path(temp))
                if lane == "producer":
                    write_json(
                        fixture.authorization,
                        fixture.producer_authorization(isolated_root_prefix=prefix),
                    )
                    completion = run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        FakeNoDispatchAdapter(),
                        allow_test_fixture=True,
                    )
                else:
                    authorization = self._prepare_cold_authorization(fixture)
                    value = json.loads(authorization.read_text(encoding="utf-8"))
                    value["isolated_root_prefix"] = prefix
                    write_json(authorization, value)
                    completion = run_cold_review_cohort(
                        fixture.root,
                        authorization,
                        FakeNoDispatchAdapter(lane="cold-review"),
                        allow_test_fixture=True,
                    )
                for worker in completion["dispatch_manifest"]["workers"]:
                    self.assertTrue(worker["home"].startswith(f"{prefix}/"))
                    self.assertTrue(worker["cache"].startswith(f"{prefix}/"))
                    self.assertTrue(worker["run_root"].startswith(f"{prefix}/"))

    def test_live_provider_is_blocked_before_any_claim_or_dispatch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-live-block-") as temp:
            fixture = Fixture(Path(temp))
            trap = PaidProviderTrap()
            with self.assertRaisesRegex(CampaignError, "LIVE_PROVIDER_UNSUPPORTED"):
                run_producer_cohort(fixture.root, fixture.authorization, trap, allow_test_fixture=True)
            self.assertEqual(trap.calls, 0)
            self.assertFalse((fixture.root / "claims").exists())
            self.assertFalse((fixture.root / "usage").exists())

    def test_producer_cohort_uses_exact_five_way_barrier_and_settles_usage(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-producer-") as temp:
            fixture = Fixture(Path(temp))
            adapter = FakeNoDispatchAdapter()
            completion = run_producer_cohort(
                fixture.root,
                fixture.authorization,
                adapter,
                allow_test_fixture=True,
            )
            self.assertEqual(completion["status"], "PRODUCER_STRUCTURAL_COMPLETE")
            self.assertEqual(completion["review_protocol"], ref(fixture.root, fixture.protocol))
            self.assertEqual(completion["review_protocol_sha256"], digest(fixture.protocol))
            self.assertEqual(len(completion["results"]), 5)
            self.assertFalse(validate_dispatch_manifest(completion["dispatch_manifest"], 5))
            first_observe = next(i for i, row in enumerate(adapter.log) if row[0] == "observe")
            self.assertEqual(sum(row[0] == "submit" for row in adapter.log[:first_observe]), 5)
            workers = completion["dispatch_manifest"]["workers"]
            for field in ("home", "cache", "run_root"):
                self.assertEqual(len({str(row[field]) for row in workers}), 5)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(head["totals"]["completed"], 5)
            self.assertEqual(head["totals"]["producer_invocations"], 5)
            self.assertFalse(head["unresolved_usage"])
            settlement = json.loads((fixture.root / "usage/transactions" / f"{completion['settlement_sha256']}.json").read_text(encoding="utf-8"))
            self.assertEqual(len(settlement["provider_usage_receipts"]), 5)
            self.assertTrue(all(row["usage"] == {"status": "RECORDED", "input_tokens": 0, "output_tokens": 0, "total_tokens": 0} for row in settlement["provider_usage_receipts"]))
            self.assertEqual(settlement["measured_cost"], {"unit": "usd", "value": "0"})
            self.assertTrue((fixture.root / "claims/producer-authorization.json").is_file())
            self.assertTrue((fixture.root / "claims/candidate.json").is_file())
            finalizer = json.loads((fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8"))
            self.assertEqual(finalizer["candidate_status"], "CONSUMED_OBSERVED")

    def test_provider_receives_exact_hash_bound_producer_execution_custody(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-producer-custody-") as temp:
            fixture = Fixture(Path(temp))
            adapter = RecordingCustodyAdapter()
            run_producer_cohort(fixture.root, fixture.authorization, adapter, allow_test_fixture=True)
            self.assertEqual(len(adapter.submitted), 5)
            self.assertEqual(adapter.submitted, adapter.observed)
            for index, envelope in enumerate(adapter.submitted):
                self.assertEqual(
                    set(envelope),
                    {
                        "schema", "lane", "candidate_id", "source_commit", "candidate_maturity",
                        "package_record", "source_preflight", "registry", "review_protocol",
                        "authorization_sha256", "cycle_or_review_batch_id", "case_id", "subject_id",
                        "model", "reasoning_effort", "provider_settings", "isolated_worker_root", "packet",
                    },
                )
                self.assertEqual(envelope["schema"], "reviewed-campaign-execution-custody-v1")
                self.assertEqual(envelope["lane"], "producer")
                self.assertEqual(envelope["candidate_maturity"], fixture.producer_authorization()["candidate_maturity"])
                self.assertEqual(envelope["package_record"], fixture.producer_authorization()["package_record"])
                self.assertEqual(envelope["source_preflight"], fixture.producer_authorization()["source_preflight"])
                self.assertEqual(envelope["registry"], fixture.producer_authorization()["registry"])
                self.assertEqual(envelope["review_protocol"], fixture.producer_authorization()["review_protocol"])
                self.assertEqual(envelope["case_id"], CASES[index])
                self.assertIsNone(envelope["packet"])
                roots = envelope["isolated_worker_root"]
                self.assertEqual(set(roots), {"worker", "home", "cache", "run_root"})

    def test_provider_custody_acknowledgement_omission_or_substitution_rejects(self) -> None:
        for corrupt in ("submit-omit-custody", "submit-substitute-custody", "observe-omit-custody", "observe-substitute-custody"):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory(prefix=f"daee-task6-custody-{corrupt}-") as temp:
                fixture = Fixture(Path(temp))
                with self.assertRaisesRegex(CampaignError, "EXECUTION_CUSTODY"):
                    run_producer_cohort(fixture.root, fixture.authorization, RecordingCustodyAdapter(corrupt=corrupt), allow_test_fixture=True)
                finalizer = json.loads((fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8"))
                self.assertIn(finalizer["dispatch_status"], {"DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN"})

    def test_binding_and_preflight_drift_fail_before_claim(self) -> None:
        mutations = {
            "registry": lambda f: f.registry.write_bytes(f.registry.read_bytes() + b" "),
            "protocol": lambda f: f.protocol.write_bytes(f.protocol.read_bytes() + b" "),
            "package": lambda f: f.package.write_bytes(f.package.read_bytes() + b" "),
            "preflight": lambda f: f.preflight.write_bytes(f.preflight.read_bytes() + b" "),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix=f"daee-task6-drift-{name}-") as temp:
                fixture = Fixture(Path(temp))
                mutate(fixture)
                with self.assertRaises(CampaignError):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        FakeNoDispatchAdapter(),
                        allow_test_fixture=True,
                    )
                self.assertFalse((fixture.root / "claims").exists())
                self.assertFalse((fixture.root / "usage").exists())

    def test_provider_settings_and_host_version_drift_fail_before_claim(self) -> None:
        mutations = {
            "parallelism": {"provider_settings": {"response_surface": "package-faithful", "parallelism": 4, "fresh_context_per_case": True, "submit_before_observe": True}},
            "host": {"host_application_version": "invented-host-v9"},
        }
        for name, changes in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix=f"daee-task6-settings-{name}-") as temp:
                fixture = Fixture(Path(temp))
                write_json(fixture.authorization, fixture.producer_authorization(**changes))
                with self.assertRaises(CampaignError):
                    run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
                self.assertFalse((fixture.root / "claims").exists())
                self.assertFalse((fixture.root / "usage").exists())

    def test_assessment_claim_requires_exact_five_structural_results_and_is_create_once(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-assessment-") as temp:
            fixture = Fixture(Path(temp))
            completion = run_producer_cohort(
                fixture.root,
                fixture.authorization,
                FakeNoDispatchAdapter(),
                allow_test_fixture=True,
            )
            assessments = [
                {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                for case_id in CASES
            ]
            with self.assertRaisesRegex(CampaignError, "ASSESSMENT_COUNT"):
                claim_initial_assessments(fixture.root, completion, assessments[:4], claimant="human:task6-assessor")
            claim = claim_initial_assessments(fixture.root, completion, assessments, claimant="human:task6-assessor")
            self.assertEqual(claim["status"], "ALL_FIVE_INITIAL_ASSESSMENTS_HASH_CLAIMED")
            self.assertEqual(claim["human_claimant"], "human:task6-assessor")
            with self.assertRaisesRegex(CampaignError, "CREATE_ONCE"):
                claim_initial_assessments(fixture.root, completion, assessments, claimant="human:task6-assessor")

    def test_cli_live_provider_requires_exact_executable_before_claim(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        residue_before = orchestrator.checkout_execution_residue_inventory(ROOT)
        self.assertEqual("PASS", residue_before["status"], residue_before)
        with tempfile.TemporaryDirectory(prefix="daee-task6-cli-") as temp:
            fixture = Fixture(Path(temp))
            proc = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(TOOLS / "run_reviewed_producer_cohort.py"),
                    "--custody-root",
                    str(fixture.root),
                    "--authorization",
                    str(fixture.authorization),
                    "--provider",
                    "codex-live",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=20,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("LIVE_PROVIDER_EXACT_CUSTODY_AUTHORIZATION_AND_EXECUTABLE_REQUIRED", proc.stdout)
            self.assertFalse((fixture.root / "claims").exists())
        residue_after = orchestrator.checkout_execution_residue_inventory(ROOT)
        self.assertEqual(residue_before, residue_after)

    def test_cold_review_requires_assessments_then_discloses_exact_packets_and_uses_barrier(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-cold-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
            packet_set = fixture.build_packets(producer)
            placeholder_claim = {
                "schema": "reviewed-campaign-initial-assessment-claim-v1",
                "status": "ALL_FIVE_INITIAL_ASSESSMENTS_HASH_CLAIMED",
            }
            missing_claim_path = fixture.root / "human-initial-assessments/claim.json"
            write_json(missing_claim_path, placeholder_claim)
            cold_auth = fixture.cold_authorization(producer, placeholder_claim, packet_set)
            missing_claim_path.unlink()
            head_before = validate_head(fixture.root / "usage")
            with self.assertRaisesRegex(CampaignError, "ASSESSMENT"):
                run_cold_review_cohort(fixture.root, cold_auth, FakeNoDispatchAdapter(lane="cold-review"), allow_test_fixture=True)
            self.assertEqual(validate_head(fixture.root / "usage"), head_before)
            self.assertFalse((fixture.root / "claims/cold-review-authorization.json").exists())
            self.assertFalse((fixture.root / "cold-review/packet-disclosure.json").exists())

            assessments = [
                {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                for case_id in CASES
            ]
            claim = claim_initial_assessments(fixture.root, producer, assessments, claimant="human:task6-assessor")
            cold_auth = fixture.cold_authorization(producer, claim, packet_set)
            adapter = FakeNoDispatchAdapter(lane="cold-review")
            completion = run_cold_review_cohort(fixture.root, cold_auth, adapter, allow_test_fixture=True)
            self.assertEqual(completion["status"], "COLD_REVIEW_COHORT_COMPLETE")
            self.assertEqual(len(completion["results"]), 5)
            self.assertFalse(validate_dispatch_manifest(completion["dispatch_manifest"], 5))
            first_observe = next(i for i, row in enumerate(adapter.log) if row[0] == "observe")
            self.assertEqual(sum(row[0] == "submit" for row in adapter.log[:first_observe]), 5)
            disclosure = json.loads((fixture.root / "cold-review/packet-disclosure.json").read_text(encoding="utf-8"))
            self.assertEqual(disclosure["assessment_claim_sha256"], digest(fixture.root / "human-initial-assessments/claim.json"))
            self.assertEqual(len(disclosure["packet_set"]), 5)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(head["totals"]["cold_review_invocations"], 5)
            self.assertEqual(head["totals"]["completed"], 10)
            finalizer = json.loads(
                (fixture.root / "cold-review/observation-finalizer.json").read_text(encoding="utf-8")
            )
            self.assertEqual(finalizer["schema"], "reviewed-campaign-observation-finalizer-v1")
            self.assertEqual(finalizer["lane"], "cold-review")
            self.assertEqual(finalizer["attempt_index"], 1)
            self.assertEqual(finalizer["candidate_status"], "CONSUMED_OBSERVED")
            self.assertEqual(finalizer["completion"]["sha256"], digest(fixture.root / "cold-review/completion.json"))
            self.assertTrue(finalizer["terminal"])

    def test_provider_receives_exact_cold_packet_manifest_and_payload_custody(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-cold-custody-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
            assessments = [
                {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                for case_id in CASES
            ]
            claim = claim_initial_assessments(fixture.root, producer, assessments, claimant="human:task6-assessor")
            packets = fixture.build_packets(producer)
            cold_auth = fixture.cold_authorization(producer, claim, packets)
            adapter = RecordingCustodyAdapter()
            run_cold_review_cohort(fixture.root, cold_auth, adapter, allow_test_fixture=True)
            self.assertEqual(adapter.submitted, adapter.observed)
            self.assertEqual(len(adapter.submitted), 5)
            for index, envelope in enumerate(adapter.submitted):
                self.assertEqual(envelope["lane"], "cold-review")
                self.assertEqual(envelope["case_id"], CASES[index])
                packet = envelope["packet"]
                self.assertEqual(
                    set(packet),
                    {"packet_root", "manifest", "payload", "packet_id", "input_sha256", "output_sha256"},
                )
                self.assertEqual(packet["manifest"], packets[index]["manifest"])
                packet_root = fixture.root / str(packet["packet_root"])
                manifest = json.loads((packet_root / str(packet["manifest"]["path"])).read_text(encoding="utf-8"))
                self.assertEqual(packet["payload"], manifest["payload"])

    def test_protocol_drift_invalidates_entire_review_cohort_before_claim_or_reservation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-protocol-drift-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
            assessments = [
                {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                for case_id in CASES
            ]
            claim = claim_initial_assessments(fixture.root, producer, assessments, claimant="human:task6-assessor")
            packet_set = fixture.build_packets(producer)
            cold_auth = fixture.cold_authorization(producer, claim, packet_set)
            fixture.protocol.write_bytes(fixture.protocol.read_bytes() + b"\n")
            head_before = validate_head(fixture.root / "usage")
            with self.assertRaises(CampaignError):
                run_cold_review_cohort(fixture.root, cold_auth, FakeNoDispatchAdapter(lane="cold-review"), allow_test_fixture=True)
            self.assertEqual(validate_head(fixture.root / "usage"), head_before)
            self.assertFalse((fixture.root / "claims/cold-review-authorization.json").exists())
            self.assertFalse((fixture.root / "cold-review/packet-disclosure.json").exists())

    def test_cold_review_observation_failure_is_conservatively_finalized_unknown(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-cold-unknown-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
            assessments = [
                {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                for case_id in CASES
            ]
            claim = claim_initial_assessments(fixture.root, producer, assessments, claimant="human:task6-assessor")
            packets = fixture.build_packets(producer)
            cold_auth = fixture.cold_authorization(producer, claim, packets)
            adapter = FailingObserveAdapter(lane="cold-review")
            with self.assertRaisesRegex(CampaignError, "PROVIDER_EXECUTION_FAILED"):
                run_cold_review_cohort(fixture.root, cold_auth, adapter, allow_test_fixture=True)
            self.assertEqual(sum(event[0] == "submit" for event in adapter.log), 5)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(head["totals"]["completed"], 5)
            self.assertEqual(head["totals"]["unknown"], 5)
            self.assertEqual(head["totals"]["cold_review_invocations"], 5)
            self.assertTrue(head["unresolved_usage"])
            finalizer = json.loads((fixture.root / "cold-review/observation-finalizer.json").read_text(encoding="utf-8"))
            self.assertEqual(finalizer["review_status"], "DISPATCH_UNKNOWN")
            self.assertTrue((fixture.root / "incidents/cold-review-task6-review-1.json").is_file())

    def test_final_adjudication_requires_exact_five_review_results_and_keeps_owner_acceptance_open(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-adjudication-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
            assessments = [
                {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                for case_id in CASES
            ]
            claim = claim_initial_assessments(fixture.root, producer, assessments, claimant="human:task6-assessor")
            packets = fixture.build_packets(producer)
            cold_auth = fixture.cold_authorization(producer, claim, packets)
            reviews = run_cold_review_cohort(fixture.root, cold_auth, FakeNoDispatchAdapter(lane="cold-review"), allow_test_fixture=True)
            adjudication = {
                "schema": "reviewed-campaign-final-human-adjudication-v1",
                "adjudication_id": "task6-human-final-1",
                "human_adjudicator": "human:task6-adjudicator",
                "candidate_id": fixture.candidate_id,
                "producer_cycle_id": producer["cycle_id"],
                "review_batch_id": reviews["review_batch_id"],
                "review_completion_sha256": hashlib.sha256((fixture.root / "cold-review/completion.json").read_bytes()).hexdigest(),
                "decisions": [{"case_id": case_id, "decision": "ACCEPT"} for case_id in CASES],
                "owner_acceptance_requested": False,
            }
            invalid = {**adjudication, "decisions": adjudication["decisions"][:4]}
            with self.assertRaisesRegex(CampaignError, "ADJUDICATION_CASE_SET"):
                ingest_final_adjudication(fixture.root, reviews, invalid)
            receipt = ingest_final_adjudication(fixture.root, reviews, adjudication)
            self.assertEqual(receipt["status"], "HUMAN_ADJUDICATION_INGESTED_OWNER_ACCEPTANCE_OPEN")
            self.assertFalse(receipt["owner_acceptance"])

    def test_pre_dispatch_failure_is_settled_and_finalized_without_live_dispatch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-finalizer-") as temp:
            fixture = Fixture(Path(temp))
            adapter = FakeNoDispatchAdapter()
            with self.assertRaisesRegex(CampaignError, "INJECTED_PRE_DISPATCH_FAILURE"):
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    adapter,
                    allow_test_fixture=True,
                    fault_at="after-reservation-before-submit",
                )
            self.assertEqual(adapter.log, [])
            head = validate_head(fixture.root / "usage")
            self.assertEqual(head["totals"]["not_dispatched"], 5)
            self.assertEqual(head["totals"]["producer_invocations"], 0)
            self.assertFalse(head["open_reservations"])
            finalizer = json.loads((fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8"))
            self.assertEqual(finalizer["candidate_status"], "CONSUMED_NO_DISPATCH")
            self.assertTrue((fixture.root / "incidents/producer-task6-cycle-1.json").is_file())

    def test_claimed_producer_reservation_failure_finalizes_and_exact_governed_retry_resumes_once(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-producer-reservation-retry-") as temp:
            fixture = Fixture(Path(temp))
            with self.assertRaisesRegex(CampaignError, "RESERVATION"):
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    FakeNoDispatchAdapter(),
                    allow_test_fixture=True,
                    fault_at="after-claims-before-reservation",
                )
            incident_path = fixture.root / "incidents/producer-task6-cycle-1.json"
            finalizer_path = fixture.root / "producer/observation-finalizer.json"
            self.assertTrue(incident_path.is_file())
            self.assertTrue(finalizer_path.is_file())
            finalizer = json.loads(finalizer_path.read_text(encoding="utf-8"))
            self.assertEqual(finalizer["dispatch_classification"], "PROVED_NO_DISPATCH")
            self.assertEqual(finalizer["candidate_status"], "CONSUMED_NO_DISPATCH")
            self.assertTrue(finalizer["resumable_retry"])
            self.assertEqual(finalizer["authorization_claim"]["sha256"], digest(fixture.root / "claims/producer-authorization.json"))
            self.assertEqual(finalizer["candidate_claim"]["sha256"], digest(fixture.root / "claims/candidate.json"))
            self.assertEqual(finalizer["resulting_usage_head_sha256"], head_snapshot(fixture.root / "usage")["head_sha256"])

            next_batch = "task6-cycle-1-retry-2"
            continuation = fixture.retry_continuation(
                lane="producer",
                prior_batch_id="task6-cycle-1",
                next_batch_id=next_batch,
                prior_authorization=fixture.authorization,
                prior_incident=incident_path,
                prior_finalizer=finalizer_path,
            )
            retry_auth = fixture.root / "authorizations/producer-retry-2.json"
            write_json(
                retry_auth,
                fixture.producer_authorization(
                    authorization_id="task6-producer-auth-2",
                    cycle_or_review_batch_id=next_batch,
                    authorization_claim_path="claims/producer-authorization-retry-2.json",
                    retry_lineage={"attempt_index": 2, "continuation_authorization": ref(fixture.root, continuation)},
                ),
            )
            completion = run_producer_cohort(fixture.root, retry_auth, FakeNoDispatchAdapter(), allow_test_fixture=True)
            self.assertEqual(completion["status"], "PRODUCER_STRUCTURAL_COMPLETE")
            continuation_value = json.loads(continuation.read_text(encoding="utf-8"))
            continuation_claim = fixture.root / str(continuation_value["claim_path"])
            self.assertTrue(continuation_claim.is_file())
            self.assertEqual(validate_head(fixture.root / "usage")["totals"]["completed"], 5)
            head_before_replay = validate_head(fixture.root / "usage")
            with self.assertRaisesRegex(CampaignError, "RETRY_CONTINUATION_REPLAY"):
                run_producer_cohort(fixture.root, retry_auth, FakeNoDispatchAdapter(), allow_test_fixture=True)
            self.assertEqual(validate_head(fixture.root / "usage"), head_before_replay)

    def test_attempt_claim_set_atomically_binds_initial_producer_claims(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-attempt-claim-set-") as temp:
            fixture = Fixture(Path(temp))
            completion = run_producer_cohort(
                fixture.root,
                fixture.authorization,
                FakeNoDispatchAdapter(),
                allow_test_fixture=True,
            )
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
            )
            claim_set_ref = finalizer["attempt_claim_set"]
            claim_set_path = fixture.root / claim_set_ref["path"]
            self.assertEqual(claim_set_ref, ref(fixture.root, claim_set_path))
            claim_set = json.loads(claim_set_path.read_text(encoding="utf-8"))
            self.assertEqual("reviewed-campaign-attempt-claim-set-v1", claim_set["schema"])
            self.assertEqual("producer", claim_set["lane"])
            self.assertEqual(1, claim_set["attempt_index"])
            self.assertEqual("CONSUMED", claim_set["status"])
            self.assertTrue(claim_set["one_use"])
            self.assertIsNone(claim_set["retained_candidate_claim"])
            self.assertEqual(
                ["authorization", "candidate"],
                [row["role"] for row in claim_set["claim_projections"]],
            )
            for projection in claim_set["claim_projections"]:
                projection_path = fixture.root / projection["path"]
                self.assertEqual(projection["payload"], json.loads(projection_path.read_text(encoding="utf-8")))
                self.assertEqual(record_sha256(projection["payload"]), projection["payload_sha256"])
            self.assertEqual(completion["authorization_sha256"], claim_set["authorization_sha256"])

    def test_initial_producer_claim_projection_failures_terminalize_from_atomic_set(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        for target_role in ("producer_authorization_claim", "candidate_claim"):
            with self.subTest(target_role=target_role), tempfile.TemporaryDirectory(
                prefix=f"daee-task6-claim-projection-{target_role}-"
            ) as temp:
                fixture = Fixture(Path(temp))
                adapter = FakeNoDispatchAdapter()
                original = orchestrator._publish_once_json

                def fail_after_publication(
                    root: Path,
                    relative: str,
                    value: dict[str, object],
                    role: str,
                ) -> dict[str, object]:
                    published = original(root, relative, value, role)
                    if role == target_role:
                        raise OSError(f"injected failure after {role}")
                    return published

                with mock.patch.object(
                    orchestrator,
                    "_publish_once_json",
                    side_effect=fail_after_publication,
                ):
                    with self.assertRaisesRegex(CampaignError, "ATTEMPT_CLAIM_PROJECTION_FAILURE"):
                        run_producer_cohort(
                            fixture.root,
                            fixture.authorization,
                            adapter,
                            allow_test_fixture=True,
                        )
                self.assertEqual([], adapter.log)
                head = validate_head(fixture.root / "usage")
                self.assertFalse(head["open_reservations"])
                self.assertEqual(0, head["totals"]["producer_invocations"])
                self.assertTrue((fixture.root / "claims/producer-authorization.json").is_file())
                self.assertTrue((fixture.root / "claims/candidate.json").is_file())
                finalizer = json.loads(
                    (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
                )
                self.assertEqual("PROVED_NO_DISPATCH", finalizer["dispatch_classification"])
                self.assertEqual("CONSUMED_NO_DISPATCH", finalizer["candidate_status"])
                self.assertEqual(
                    finalizer["attempt_claim_set"],
                    ref(fixture.root, fixture.root / finalizer["attempt_claim_set"]["path"]),
                )
                replay_adapter = FakeNoDispatchAdapter()
                with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        replay_adapter,
                        allow_test_fixture=True,
                    )
                self.assertEqual([], replay_adapter.log)

    def test_initial_producer_foreign_claim_projection_collisions_terminalize_and_replay(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        cases = (
            ("producer_authorization_claim", "authorization", "authorization_claim"),
            ("candidate_claim", "candidate", "candidate_claim"),
        )
        for target_role, projection_role, finalizer_field in cases:
            with self.subTest(target_role=target_role), tempfile.TemporaryDirectory(
                prefix=f"daee-task6-foreign-claim-projection-{target_role}-"
            ) as temp:
                fixture = Fixture(Path(temp))
                adapter = FakeNoDispatchAdapter()
                original = orchestrator._publish_once_json
                foreign_raw = canonical(
                    {"schema": "test-owned-foreign-claim-v1", "target_role": target_role}
                )
                foreign_path: Path | None = None

                def collide_before_publication(
                    root: Path,
                    relative: str,
                    value: dict[str, object],
                    role: str,
                ) -> dict[str, object]:
                    nonlocal foreign_path
                    if role == target_role and foreign_path is None:
                        foreign_path = root / relative
                        foreign_path.parent.mkdir(parents=True, exist_ok=True)
                        foreign_path.write_bytes(foreign_raw)
                    return original(root, relative, value, role)

                with mock.patch.object(
                    orchestrator,
                    "_publish_once_json",
                    side_effect=collide_before_publication,
                ):
                    with self.assertRaisesRegex(
                        CampaignError,
                        "ATTEMPT_CLAIM_PROJECTION_INCOMPLETE",
                    ):
                        run_producer_cohort(
                            fixture.root,
                            fixture.authorization,
                            adapter,
                            allow_test_fixture=True,
                        )

                self.assertIsNotNone(foreign_path)
                assert foreign_path is not None
                self.assertEqual(foreign_raw, foreign_path.read_bytes())
                self.assertEqual([], adapter.log)
                head = validate_head(fixture.root / "usage")
                self.assertFalse(head["open_reservations"])
                self.assertEqual(0, head["totals"]["producer_invocations"])
                finalizer = json.loads(
                    (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
                )
                self.assertEqual("PROVED_NO_DISPATCH", finalizer["dispatch_classification"])
                states = {row["role"]: row for row in finalizer["claim_projection_states"]}
                self.assertEqual({"authorization", "candidate"}, set(states))
                self.assertEqual("COLLISION", states[projection_role]["status"])
                self.assertEqual(ref(fixture.root, foreign_path), states[projection_role]["observed"])
                self.assertIsNone(finalizer[finalizer_field])
                other_role = "candidate" if projection_role == "authorization" else "authorization"
                other_field = "candidate_claim" if other_role == "candidate" else "authorization_claim"
                self.assertEqual("EXACT", states[other_role]["status"])
                self.assertEqual(finalizer[other_field], states[other_role]["observed"])
                self.assertEqual(
                    projection_role != "candidate",
                    finalizer["resumable_retry"],
                )

                replay_adapter = FakeNoDispatchAdapter()
                with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        replay_adapter,
                        allow_test_fixture=True,
                    )
                self.assertEqual([], replay_adapter.log)
                self.assertEqual(foreign_raw, foreign_path.read_bytes())

    def test_initial_producer_missing_claim_projection_terminalizes_and_replays(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-task6-missing-claim-projection-") as temp:
            fixture = Fixture(Path(temp))
            adapter = FakeNoDispatchAdapter()
            original = orchestrator._publish_once_json

            def keep_authorization_projection_missing(
                root: Path,
                relative: str,
                value: dict[str, object],
                role: str,
            ) -> dict[str, object]:
                if relative == "claims/producer-authorization.json":
                    raise OSError("injected persistent authorization projection failure")
                return original(root, relative, value, role)

            with mock.patch.object(
                orchestrator,
                "_publish_once_json",
                side_effect=keep_authorization_projection_missing,
            ):
                with self.assertRaisesRegex(
                    CampaignError,
                    "ATTEMPT_CLAIM_PROJECTION_INCOMPLETE",
                ):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            self.assertEqual([], adapter.log)
            self.assertFalse((fixture.root / "claims/producer-authorization.json").exists())
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
            )
            states = {row["role"]: row for row in finalizer["claim_projection_states"]}
            self.assertEqual("MISSING", states["authorization"]["status"])
            self.assertIsNone(states["authorization"]["observed"])
            self.assertIsNone(finalizer["authorization_claim"])
            self.assertEqual("EXACT", states["candidate"]["status"])
            self.assertEqual(finalizer["candidate_claim"], states["candidate"]["observed"])
            self.assertTrue(finalizer["resumable_retry"])

            replay_adapter = FakeNoDispatchAdapter()
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_adapter.log)

    def test_initial_cold_claim_projection_failure_terminalizes_from_atomic_set(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-task6-cold-claim-projection-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(
                fixture.root,
                fixture.authorization,
                FakeNoDispatchAdapter(),
                allow_test_fixture=True,
            )
            assessments = [
                {
                    "case_id": case_id,
                    "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest(),
                }
                for case_id in CASES
            ]
            assessment_claim = claim_initial_assessments(
                fixture.root,
                producer,
                assessments,
                claimant="human:task6-assessor",
            )
            packets = fixture.build_packets(producer)
            cold_authorization = fixture.cold_authorization(producer, assessment_claim, packets)
            adapter = FakeNoDispatchAdapter(lane="cold-review")
            original = orchestrator._publish_once_json

            def fail_after_publication(
                root: Path,
                relative: str,
                value: dict[str, object],
                role: str,
            ) -> dict[str, object]:
                published = original(root, relative, value, role)
                if role == "cold-review_authorization_claim":
                    raise OSError("injected failure after cold-review authorization claim")
                return published

            with mock.patch.object(
                orchestrator,
                "_publish_once_json",
                side_effect=fail_after_publication,
            ):
                with self.assertRaisesRegex(CampaignError, "ATTEMPT_CLAIM_PROJECTION_FAILURE"):
                    run_cold_review_cohort(
                        fixture.root,
                        cold_authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            self.assertEqual([], adapter.log)
            head = validate_head(fixture.root / "usage")
            self.assertFalse(head["open_reservations"])
            self.assertEqual(0, head["totals"]["cold_review_invocations"])
            self.assertFalse((fixture.root / "cold-review/packet-disclosure.json").exists())
            finalizer = json.loads(
                (fixture.root / "cold-review/observation-finalizer.json").read_text(encoding="utf-8")
            )
            self.assertEqual("PROVED_NO_DISPATCH", finalizer["dispatch_classification"])
            self.assertEqual("CONSUMED_OBSERVED", finalizer["candidate_status"])
            self.assertEqual(
                finalizer["attempt_claim_set"],
                ref(fixture.root, fixture.root / finalizer["attempt_claim_set"]["path"]),
            )

    def test_cold_review_foreign_authorization_claim_collision_terminalizes_and_replays(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-task6-cold-foreign-claim-projection-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(
                fixture.root,
                fixture.authorization,
                FakeNoDispatchAdapter(),
                allow_test_fixture=True,
            )
            assessments = [
                {
                    "case_id": case_id,
                    "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest(),
                }
                for case_id in CASES
            ]
            assessment_claim = claim_initial_assessments(
                fixture.root,
                producer,
                assessments,
                claimant="human:task6-assessor",
            )
            packets = fixture.build_packets(producer)
            cold_authorization = fixture.cold_authorization(producer, assessment_claim, packets)
            adapter = FakeNoDispatchAdapter(lane="cold-review")
            original = orchestrator._publish_once_json
            foreign_raw = canonical(
                {"schema": "test-owned-foreign-claim-v1", "target_role": "cold-review_authorization_claim"}
            )
            foreign_path: Path | None = None

            def collide_before_publication(
                root: Path,
                relative: str,
                value: dict[str, object],
                role: str,
            ) -> dict[str, object]:
                nonlocal foreign_path
                if role == "cold-review_authorization_claim" and foreign_path is None:
                    foreign_path = root / relative
                    foreign_path.parent.mkdir(parents=True, exist_ok=True)
                    foreign_path.write_bytes(foreign_raw)
                return original(root, relative, value, role)

            with mock.patch.object(
                orchestrator,
                "_publish_once_json",
                side_effect=collide_before_publication,
            ):
                with self.assertRaisesRegex(
                    CampaignError,
                    "ATTEMPT_CLAIM_PROJECTION_INCOMPLETE",
                ):
                    run_cold_review_cohort(
                        fixture.root,
                        cold_authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            self.assertIsNotNone(foreign_path)
            assert foreign_path is not None
            self.assertEqual(foreign_raw, foreign_path.read_bytes())
            self.assertEqual([], adapter.log)
            self.assertFalse((fixture.root / "cold-review/packet-disclosure.json").exists())
            finalizer = json.loads(
                (fixture.root / "cold-review/observation-finalizer.json").read_text(encoding="utf-8")
            )
            self.assertEqual("PROVED_NO_DISPATCH", finalizer["dispatch_classification"])
            self.assertEqual("CONSUMED_OBSERVED", finalizer["candidate_status"])
            self.assertEqual(
                ["authorization"],
                [row["role"] for row in finalizer["claim_projection_states"]],
            )
            state = finalizer["claim_projection_states"][0]
            self.assertEqual("COLLISION", state["status"])
            self.assertEqual(ref(fixture.root, foreign_path), state["observed"])
            self.assertIsNone(finalizer["authorization_claim"])
            self.assertIsNotNone(finalizer["candidate_claim"])
            self.assertTrue(finalizer["resumable_retry"])

            replay_adapter = FakeNoDispatchAdapter(lane="cold-review")
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_cold_review_cohort(
                    fixture.root,
                    cold_authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_adapter.log)
            self.assertEqual(foreign_raw, foreign_path.read_bytes())

    def test_existing_exact_attempt_claim_set_reentry_terminalizes_interrupted_projection(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-task6-claim-set-reentry-") as temp:
            fixture = Fixture(Path(temp))
            original = orchestrator._publish_once_json

            def interrupt_after_authorization(
                root: Path,
                relative: str,
                value: dict[str, object],
                role: str,
            ) -> dict[str, object]:
                published = original(root, relative, value, role)
                if role == "producer_authorization_claim":
                    raise KeyboardInterrupt("simulated process interruption after exact claim projection")
                return published

            with mock.patch.object(
                orchestrator,
                "_publish_once_json",
                side_effect=interrupt_after_authorization,
            ):
                with self.assertRaises(KeyboardInterrupt):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        FakeNoDispatchAdapter(),
                        allow_test_fixture=True,
                    )
            self.assertTrue((fixture.root / "claims/producer-authorization.json").is_file())
            self.assertFalse((fixture.root / "claims/candidate.json").exists())
            self.assertFalse((fixture.root / "producer/observation-finalizer.json").exists())
            recovery_adapter = FakeNoDispatchAdapter()
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_CLAIM_SET_RECOVERY"):
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    recovery_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], recovery_adapter.log)
            self.assertTrue((fixture.root / "claims/candidate.json").is_file())
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
            )
            self.assertEqual("PROVED_NO_DISPATCH", finalizer["dispatch_classification"])
            self.assertFalse(validate_head(fixture.root / "usage")["open_reservations"])

    def test_retry_claim_projection_failures_terminalize_without_consumed_authority_gap(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        for target_role in ("retry_continuation_claim", "producer_authorization_claim"):
            with self.subTest(target_role=target_role), tempfile.TemporaryDirectory(
                prefix=f"daee-task6-retry-claim-projection-{target_role}-"
            ) as temp:
                fixture = Fixture(Path(temp))
                with self.assertRaisesRegex(CampaignError, "RESERVATION"):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        FakeNoDispatchAdapter(),
                        allow_test_fixture=True,
                        fault_at="after-claims-before-reservation",
                    )
                prior_incident = fixture.root / "incidents/producer-task6-cycle-1.json"
                prior_finalizer = fixture.root / "producer/observation-finalizer.json"
                next_batch = "task6-claim-projection-retry-2"
                continuation = fixture.retry_continuation(
                    lane="producer",
                    prior_batch_id="task6-cycle-1",
                    next_batch_id=next_batch,
                    prior_authorization=fixture.authorization,
                    prior_incident=prior_incident,
                    prior_finalizer=prior_finalizer,
                )
                retry_auth = fixture.root / "authorizations/producer-claim-projection-retry-2.json"
                write_json(
                    retry_auth,
                    fixture.producer_authorization(
                        authorization_id="task6-producer-claim-projection-auth-2",
                        cycle_or_review_batch_id=next_batch,
                        authorization_claim_path="claims/producer-claim-projection-authorization-retry-2.json",
                        retry_lineage={
                            "attempt_index": 2,
                            "continuation_authorization": ref(fixture.root, continuation),
                        },
                    ),
                )
                original = orchestrator._publish_once_json

                def fail_after_publication(
                    root: Path,
                    relative: str,
                    value: dict[str, object],
                    role: str,
                ) -> dict[str, object]:
                    published = original(root, relative, value, role)
                    if role == target_role:
                        raise OSError(f"injected failure after {role}")
                    return published

                retry_adapter = FakeNoDispatchAdapter()
                with mock.patch.object(
                    orchestrator,
                    "_publish_once_json",
                    side_effect=fail_after_publication,
                ):
                    with self.assertRaisesRegex(CampaignError, "ATTEMPT_CLAIM_PROJECTION_FAILURE"):
                        run_producer_cohort(
                            fixture.root,
                            retry_auth,
                            retry_adapter,
                            allow_test_fixture=True,
                        )
                self.assertEqual([], retry_adapter.log)
                self.assertFalse(validate_head(fixture.root / "usage")["open_reservations"])
                retry_finalizer = json.loads(
                    (fixture.root / "producer/retry-finalizers/attempt-02.json").read_text(encoding="utf-8")
                )
                self.assertEqual("PROVED_NO_DISPATCH", retry_finalizer["dispatch_classification"])
                claim_set = json.loads(
                    (fixture.root / retry_finalizer["attempt_claim_set"]["path"]).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    ["retry_continuation", "authorization"],
                    [row["role"] for row in claim_set["claim_projections"]],
                )
                self.assertEqual(retry_finalizer["candidate_claim"], claim_set["retained_candidate_claim"])
                replay_adapter = FakeNoDispatchAdapter()
                with self.assertRaisesRegex(CampaignError, "RETRY_CONTINUATION_REPLAY|ATTEMPT_ALREADY_TERMINALIZED"):
                    run_producer_cohort(
                        fixture.root,
                        retry_auth,
                        replay_adapter,
                        allow_test_fixture=True,
                    )
                self.assertEqual([], replay_adapter.log)

    def test_retry_foreign_claim_projection_collisions_terminalize_and_replay(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        cases = (
            ("retry_continuation_claim", "retry_continuation", "continuation_claim"),
            ("producer_authorization_claim", "authorization", "authorization_claim"),
        )
        for target_role, projection_role, finalizer_field in cases:
            with self.subTest(target_role=target_role), tempfile.TemporaryDirectory(
                prefix=f"daee-task6-retry-foreign-claim-{target_role}-"
            ) as temp:
                fixture = Fixture(Path(temp))
                with self.assertRaisesRegex(CampaignError, "RESERVATION"):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        FakeNoDispatchAdapter(),
                        allow_test_fixture=True,
                        fault_at="after-claims-before-reservation",
                    )
                prior_incident = fixture.root / "incidents/producer-task6-cycle-1.json"
                prior_finalizer = fixture.root / "producer/observation-finalizer.json"
                next_batch = f"task6-foreign-claim-retry-{projection_role}"
                continuation = fixture.retry_continuation(
                    lane="producer",
                    prior_batch_id="task6-cycle-1",
                    next_batch_id=next_batch,
                    prior_authorization=fixture.authorization,
                    prior_incident=prior_incident,
                    prior_finalizer=prior_finalizer,
                )
                retry_auth = fixture.root / f"authorizations/producer-foreign-{projection_role}-retry-2.json"
                write_json(
                    retry_auth,
                    fixture.producer_authorization(
                        authorization_id=f"task6-producer-foreign-{projection_role}-auth-2",
                        cycle_or_review_batch_id=next_batch,
                        authorization_claim_path=f"claims/producer-foreign-{projection_role}-authorization-retry-2.json",
                        retry_lineage={
                            "attempt_index": 2,
                            "continuation_authorization": ref(fixture.root, continuation),
                        },
                    ),
                )
                adapter = FakeNoDispatchAdapter()
                original = orchestrator._publish_once_json
                foreign_raw = canonical(
                    {"schema": "test-owned-foreign-claim-v1", "target_role": target_role}
                )
                foreign_path: Path | None = None

                def collide_before_publication(
                    root: Path,
                    relative: str,
                    value: dict[str, object],
                    role: str,
                ) -> dict[str, object]:
                    nonlocal foreign_path
                    if role == target_role and foreign_path is None:
                        foreign_path = root / relative
                        foreign_path.parent.mkdir(parents=True, exist_ok=True)
                        foreign_path.write_bytes(foreign_raw)
                    return original(root, relative, value, role)

                with mock.patch.object(
                    orchestrator,
                    "_publish_once_json",
                    side_effect=collide_before_publication,
                ):
                    with self.assertRaisesRegex(
                        CampaignError,
                        "ATTEMPT_CLAIM_PROJECTION_INCOMPLETE",
                    ):
                        run_producer_cohort(
                            fixture.root,
                            retry_auth,
                            adapter,
                            allow_test_fixture=True,
                        )

                self.assertIsNotNone(foreign_path)
                assert foreign_path is not None
                self.assertEqual(foreign_raw, foreign_path.read_bytes())
                self.assertEqual([], adapter.log)
                finalizer = json.loads(
                    (fixture.root / "producer/retry-finalizers/attempt-02.json").read_text(encoding="utf-8")
                )
                states = {row["role"]: row for row in finalizer["claim_projection_states"]}
                self.assertEqual({"retry_continuation", "authorization"}, set(states))
                self.assertEqual("COLLISION", states[projection_role]["status"])
                self.assertEqual(ref(fixture.root, foreign_path), states[projection_role]["observed"])
                self.assertIsNone(finalizer[finalizer_field])
                other_role = "authorization" if projection_role == "retry_continuation" else "retry_continuation"
                other_field = "authorization_claim" if other_role == "authorization" else "continuation_claim"
                self.assertEqual("EXACT", states[other_role]["status"])
                self.assertEqual(finalizer[other_field], states[other_role]["observed"])
                self.assertIsNotNone(finalizer["candidate_claim"])
                self.assertTrue(finalizer["resumable_retry"])

                replay_adapter = FakeNoDispatchAdapter()
                with self.assertRaisesRegex(
                    CampaignError,
                    "RETRY_CONTINUATION_REPLAY|ATTEMPT_ALREADY_TERMINALIZED",
                ):
                    run_producer_cohort(
                        fixture.root,
                        retry_auth,
                        replay_adapter,
                        allow_test_fixture=True,
                    )
                self.assertEqual([], replay_adapter.log)
                self.assertEqual(foreign_raw, foreign_path.read_bytes())

    def test_retry_exact_claim_set_reentry_terminalizes_interrupted_continuation_projection(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-task6-retry-claim-set-reentry-") as temp:
            fixture = Fixture(Path(temp))
            with self.assertRaisesRegex(CampaignError, "RESERVATION"):
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    FakeNoDispatchAdapter(),
                    allow_test_fixture=True,
                    fault_at="after-claims-before-reservation",
                )
            prior_incident = fixture.root / "incidents/producer-task6-cycle-1.json"
            prior_finalizer = fixture.root / "producer/observation-finalizer.json"
            next_batch = "task6-interrupted-continuation-retry-2"
            continuation = fixture.retry_continuation(
                lane="producer",
                prior_batch_id="task6-cycle-1",
                next_batch_id=next_batch,
                prior_authorization=fixture.authorization,
                prior_incident=prior_incident,
                prior_finalizer=prior_finalizer,
            )
            retry_auth = fixture.root / "authorizations/producer-interrupted-continuation-retry-2.json"
            write_json(
                retry_auth,
                fixture.producer_authorization(
                    authorization_id="task6-producer-interrupted-continuation-auth-2",
                    cycle_or_review_batch_id=next_batch,
                    authorization_claim_path="claims/producer-interrupted-continuation-authorization-retry-2.json",
                    retry_lineage={
                        "attempt_index": 2,
                        "continuation_authorization": ref(fixture.root, continuation),
                    },
                ),
            )
            original = orchestrator._publish_once_json

            def interrupt_after_continuation(
                root: Path,
                relative: str,
                value: dict[str, object],
                role: str,
            ) -> dict[str, object]:
                published = original(root, relative, value, role)
                if role == "retry_continuation_claim":
                    raise KeyboardInterrupt("simulated process interruption after continuation claim")
                return published

            with mock.patch.object(
                orchestrator,
                "_publish_once_json",
                side_effect=interrupt_after_continuation,
            ):
                with self.assertRaises(KeyboardInterrupt):
                    run_producer_cohort(
                        fixture.root,
                        retry_auth,
                        FakeNoDispatchAdapter(),
                        allow_test_fixture=True,
                    )
            continuation_value = json.loads(continuation.read_text(encoding="utf-8"))
            self.assertTrue((fixture.root / continuation_value["claim_path"]).is_file())
            retry_finalizer_path = fixture.root / "producer/retry-finalizers/attempt-02.json"
            self.assertFalse(retry_finalizer_path.exists())
            recovery_adapter = FakeNoDispatchAdapter()
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_CLAIM_SET_RECOVERY"):
                run_producer_cohort(
                    fixture.root,
                    retry_auth,
                    recovery_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], recovery_adapter.log)
            retry_finalizer = json.loads(retry_finalizer_path.read_text(encoding="utf-8"))
            self.assertEqual("PROVED_NO_DISPATCH", retry_finalizer["dispatch_classification"])
            self.assertFalse(validate_head(fixture.root / "usage")["open_reservations"])

    def test_reservation_exception_after_head_publish_adopts_and_settles_own_open_reservation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-open-reservation-") as temp:
            fixture = Fixture(Path(temp))
            with self.assertRaisesRegex(CampaignError, "RESERVATION"):
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    FakeNoDispatchAdapter(),
                    allow_test_fixture=True,
                    fault_at="reservation-exception-after-open",
                )
            head = validate_head(fixture.root / "usage")
            self.assertFalse(head["open_reservations"])
            self.assertEqual(head["totals"]["not_dispatched"], 5)
            finalizer = json.loads((fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8"))
            self.assertIsNotNone(finalizer["reservation_sha256"])
            self.assertIsNotNone(finalizer["settlement_sha256"])
            self.assertEqual(finalizer["dispatch_classification"], "PROVED_NO_DISPATCH")

    def test_claimed_cold_reservation_failures_finalize_and_exact_retry_resumes(self) -> None:
        for fault in ("after-claims-before-reservation", "after-reservation-before-submit", "reservation-exception-after-open"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix=f"daee-task6-cold-reservation-{fault}-") as temp:
                fixture = Fixture(Path(temp))
                producer = run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
                assessments = [
                    {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                    for case_id in CASES
                ]
                claim = claim_initial_assessments(fixture.root, producer, assessments, claimant="human:task6-assessor")
                packets = fixture.build_packets(producer)
                cold_auth = fixture.cold_authorization(producer, claim, packets)
                with self.assertRaises(CampaignError):
                    run_cold_review_cohort(
                        fixture.root,
                        cold_auth,
                        FakeNoDispatchAdapter(lane="cold-review"),
                        allow_test_fixture=True,
                        fault_at=fault,
                    )
                incident_path = fixture.root / "incidents/cold-review-task6-review-1.json"
                finalizer_path = fixture.root / "cold-review/observation-finalizer.json"
                self.assertTrue(incident_path.is_file())
                self.assertTrue(finalizer_path.is_file())
                finalizer = json.loads(finalizer_path.read_text(encoding="utf-8"))
                self.assertEqual(finalizer["dispatch_classification"], "PROVED_NO_DISPATCH")
                self.assertTrue(finalizer["resumable_retry"])
                self.assertFalse(validate_head(fixture.root / "usage")["open_reservations"])

                next_batch = "task6-review-1-retry-2"
                continuation = fixture.retry_continuation(
                    lane="cold-review",
                    prior_batch_id="task6-review-1",
                    next_batch_id=next_batch,
                    prior_authorization=cold_auth,
                    prior_incident=incident_path,
                    prior_finalizer=finalizer_path,
                )
                retry_auth = fixture.cold_authorization(
                    producer,
                    claim,
                    packets,
                    output_name="cold-review-retry-2.json",
                    authorization_id="task6-cold-review-auth-2",
                    cycle_or_review_batch_id=next_batch,
                    authorization_claim_path="claims/cold-review-authorization-retry-2.json",
                    packet_disclosure_path="cold-review/packet-disclosure-retry-2.json",
                    retry_lineage={"attempt_index": 2, "continuation_authorization": ref(fixture.root, continuation)},
                )
                completion = run_cold_review_cohort(fixture.root, retry_auth, FakeNoDispatchAdapter(lane="cold-review"), allow_test_fixture=True)
                self.assertEqual(completion["status"], "COLD_REVIEW_COHORT_COMPLETE")

    def test_cold_packet_disclosure_collision_finalizes_without_reservation_and_exact_retry_is_one_use(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-cold-disclosure-collision-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
            assessments = [
                {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                for case_id in CASES
            ]
            claim = claim_initial_assessments(fixture.root, producer, assessments, claimant="human:task6-assessor")
            packets = fixture.build_packets(producer)
            cold_auth = fixture.cold_authorization(producer, claim, packets)
            disclosure_path = fixture.root / "cold-review/packet-disclosure.json"
            write_json(disclosure_path, {"schema": "preexisting-create-once-collision-v1"})
            head_before = head_snapshot(fixture.root / "usage")
            with self.assertRaisesRegex(CampaignError, "PACKET_DISCLOSURE_FAILURE"):
                run_cold_review_cohort(fixture.root, cold_auth, FakeNoDispatchAdapter(lane="cold-review"), allow_test_fixture=True)
            self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)
            self.assertFalse(validate_head(fixture.root / "usage")["open_reservations"])
            self.assertEqual(validate_head(fixture.root / "usage")["totals"]["cold_review_invocations"], 0)
            self.assertTrue((fixture.root / "claims/cold-review-authorization.json").is_file())
            incident_path = fixture.root / "incidents/cold-review-task6-review-1.json"
            finalizer_path = fixture.root / "cold-review/observation-finalizer.json"
            self.assertTrue(incident_path.is_file())
            self.assertTrue(finalizer_path.is_file())
            finalizer = json.loads(finalizer_path.read_text(encoding="utf-8"))
            self.assertEqual(finalizer["dispatch_classification"], "PROVED_NO_DISPATCH")
            self.assertIsNone(finalizer["reservation_sha256"])
            self.assertIsNone(finalizer["settlement_sha256"])
            self.assertIsNone(finalizer["packet_disclosure"])
            self.assertTrue(finalizer["resumable_retry"])
            self.assertEqual(finalizer["authorization_claim"]["sha256"], digest(fixture.root / "claims/cold-review-authorization.json"))

            next_batch = "task6-review-disclosure-retry-2"
            continuation = fixture.retry_continuation(
                lane="cold-review",
                prior_batch_id="task6-review-1",
                next_batch_id=next_batch,
                prior_authorization=cold_auth,
                prior_incident=incident_path,
                prior_finalizer=finalizer_path,
            )
            retry_auth = fixture.cold_authorization(
                producer,
                claim,
                packets,
                output_name="cold-review-disclosure-retry-2.json",
                authorization_id="task6-cold-review-disclosure-auth-2",
                cycle_or_review_batch_id=next_batch,
                authorization_claim_path="claims/cold-review-disclosure-authorization-retry-2.json",
                packet_disclosure_path="cold-review/packet-disclosure-retry-disclosure-2.json",
                retry_lineage={"attempt_index": 2, "continuation_authorization": ref(fixture.root, continuation)},
            )
            completion = run_cold_review_cohort(fixture.root, retry_auth, FakeNoDispatchAdapter(lane="cold-review"), allow_test_fixture=True)
            self.assertEqual(completion["status"], "COLD_REVIEW_COHORT_COMPLETE")
            continuation_value = json.loads(continuation.read_text(encoding="utf-8"))
            continuation_claim = fixture.root / str(continuation_value["claim_path"])
            self.assertTrue(continuation_claim.is_file())
            head_after = validate_head(fixture.root / "usage")
            with self.assertRaisesRegex(CampaignError, "RETRY_CONTINUATION_REPLAY"):
                run_cold_review_cohort(fixture.root, retry_auth, FakeNoDispatchAdapter(lane="cold-review"), allow_test_fixture=True)
            self.assertEqual(validate_head(fixture.root / "usage"), head_after)

    def test_retry_lineage_rejects_unrelated_self_declared_stale_and_substituted_authority(self) -> None:
        mutations = {
            "unrelated-candidate": lambda f, i, z: {"candidate_id": "unrelated-candidate"},
            "self-issued": lambda f, i, z: {"issuer_identity": "/root/task6_no_dispatch"},
            "owner-relabel": lambda f, i, z: {"implementation_owner_identity": "/root/task6_alias"},
            "wrong-lane": lambda f, i, z: {"lane": "cold-review"},
            "wrong-prior-batch": lambda f, i, z: {"prior_batch_id": "unrelated-batch"},
            "wrong-prior-attempt": lambda f, i, z: {"prior_attempt_index": 0},
            "wrong-next-attempt": lambda f, i, z: {"next_attempt_index": 3},
            "wrong-prior-authorization": lambda f, i, z: {"prior_cohort_authorization_sha256": "9" * 64},
            "incident-substitution": lambda f, i, z: {"prior_incident": ref(f.root, z)},
            "finalizer-substitution": lambda f, i, z: {"prior_finalizer": ref(f.root, i)},
            "stale-head": lambda f, i, z: {"expected_usage_head_sha256": "8" * 64},
            "wrong-next-batch": lambda f, i, z: {"next_batch_id": "unrelated-next"},
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix=f"daee-task6-retry-negative-{name}-") as temp:
                fixture = Fixture(Path(temp))
                with self.assertRaises(CampaignError):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        FakeNoDispatchAdapter(),
                        allow_test_fixture=True,
                        fault_at="after-claims-before-reservation",
                    )
                incident_path = fixture.root / "incidents/producer-task6-cycle-1.json"
                finalizer_path = fixture.root / "producer/observation-finalizer.json"
                next_batch = "task6-cycle-1-retry-2"
                continuation = fixture.retry_continuation(
                    lane="producer",
                    prior_batch_id="task6-cycle-1",
                    next_batch_id=next_batch,
                    prior_authorization=fixture.authorization,
                    prior_incident=incident_path,
                    prior_finalizer=finalizer_path,
                    changes=mutate(fixture, incident_path, finalizer_path),
                )
                retry_auth = fixture.root / "authorizations/producer-retry-2.json"
                write_json(
                    retry_auth,
                    fixture.producer_authorization(
                        authorization_id="task6-producer-auth-2",
                        cycle_or_review_batch_id=next_batch,
                        authorization_claim_path="claims/producer-authorization-retry-2.json",
                        retry_lineage={"attempt_index": 2, "continuation_authorization": ref(fixture.root, continuation)},
                    ),
                )
                head_before = head_snapshot(fixture.root / "usage")
                with self.assertRaisesRegex(CampaignError, "RETRY_CONTINUATION"):
                    run_producer_cohort(fixture.root, retry_auth, FakeNoDispatchAdapter(), allow_test_fixture=True)
                self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)
                continuation_value = json.loads(continuation.read_text(encoding="utf-8"))
                self.assertFalse((fixture.root / str(continuation_value["claim_path"])).exists())
                self.assertFalse((fixture.root / "claims/producer-authorization-retry-2.json").exists())

    def test_producer_retry_validates_retained_candidate_claim_before_consuming_continuation(self) -> None:
        for mutation in ("missing", "drifted"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix=f"daee-task6-producer-retained-claim-{mutation}-") as temp:
                fixture = Fixture(Path(temp))
                with self.assertRaises(CampaignError):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        FakeNoDispatchAdapter(),
                        allow_test_fixture=True,
                        fault_at="after-claims-before-reservation",
                    )
                incident_path = fixture.root / "incidents/producer-task6-cycle-1.json"
                finalizer_path = fixture.root / "producer/observation-finalizer.json"
                next_batch = "task6-producer-retained-claim-retry-2"
                continuation = fixture.retry_continuation(
                    lane="producer",
                    prior_batch_id="task6-cycle-1",
                    next_batch_id=next_batch,
                    prior_authorization=fixture.authorization,
                    prior_incident=incident_path,
                    prior_finalizer=finalizer_path,
                )
                candidate_claim = fixture.root / "claims/candidate.json"
                if mutation == "missing":
                    candidate_claim.unlink()
                else:
                    candidate_claim.write_bytes(candidate_claim.read_bytes() + b" ")
                retry_auth = fixture.root / "authorizations/producer-retained-claim-retry-2.json"
                successor_claim = "claims/producer-retained-claim-authorization-retry-2.json"
                write_json(
                    retry_auth,
                    fixture.producer_authorization(
                        authorization_id="task6-producer-retained-claim-auth-2",
                        cycle_or_review_batch_id=next_batch,
                        authorization_claim_path=successor_claim,
                        retry_lineage={"attempt_index": 2, "continuation_authorization": ref(fixture.root, continuation)},
                    ),
                )
                continuation_value = json.loads(continuation.read_text(encoding="utf-8"))
                continuation_claim = fixture.root / str(continuation_value["claim_path"])
                head_before = head_snapshot(fixture.root / "usage")
                with self.assertRaisesRegex(CampaignError, "RETRY_CONTINUATION_CANDIDATE_CLAIM"):
                    run_producer_cohort(fixture.root, retry_auth, FakeNoDispatchAdapter(), allow_test_fixture=True)
                self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)
                self.assertFalse(continuation_claim.exists())
                self.assertFalse((fixture.root / successor_claim).exists())
                self.assertFalse((fixture.root / "producer/retry-finalizers/attempt-02.json").exists())
                self.assertFalse((fixture.root / f"incidents/producer-{next_batch}.json").exists())

    def test_cold_retry_validates_retained_candidate_claim_before_consuming_continuation(self) -> None:
        for mutation in ("missing", "drifted"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix=f"daee-task6-cold-retained-claim-{mutation}-") as temp:
                fixture = Fixture(Path(temp))
                producer = run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
                assessments = [
                    {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                    for case_id in CASES
                ]
                claim = claim_initial_assessments(fixture.root, producer, assessments, claimant="human:task6-assessor")
                packets = fixture.build_packets(producer)
                cold_auth = fixture.cold_authorization(producer, claim, packets)
                with self.assertRaises(CampaignError):
                    run_cold_review_cohort(
                        fixture.root,
                        cold_auth,
                        FakeNoDispatchAdapter(lane="cold-review"),
                        allow_test_fixture=True,
                        fault_at="after-claims-before-reservation",
                    )
                incident_path = fixture.root / "incidents/cold-review-task6-review-1.json"
                finalizer_path = fixture.root / "cold-review/observation-finalizer.json"
                next_batch = "task6-cold-retained-claim-retry-2"
                continuation = fixture.retry_continuation(
                    lane="cold-review",
                    prior_batch_id="task6-review-1",
                    next_batch_id=next_batch,
                    prior_authorization=cold_auth,
                    prior_incident=incident_path,
                    prior_finalizer=finalizer_path,
                )
                candidate_claim = fixture.root / "claims/candidate.json"
                if mutation == "missing":
                    candidate_claim.unlink()
                else:
                    candidate_claim.write_bytes(candidate_claim.read_bytes() + b" ")
                successor_claim = "claims/cold-retained-claim-authorization-retry-2.json"
                retry_auth = fixture.cold_authorization(
                    producer,
                    claim,
                    packets,
                    output_name="cold-retained-claim-retry-2.json",
                    authorization_id="task6-cold-retained-claim-auth-2",
                    cycle_or_review_batch_id=next_batch,
                    authorization_claim_path=successor_claim,
                    packet_disclosure_path="cold-review/packet-disclosure-retained-claim-retry-2.json",
                    retry_lineage={"attempt_index": 2, "continuation_authorization": ref(fixture.root, continuation)},
                )
                continuation_value = json.loads(continuation.read_text(encoding="utf-8"))
                continuation_claim = fixture.root / str(continuation_value["claim_path"])
                head_before = head_snapshot(fixture.root / "usage")
                with self.assertRaisesRegex(CampaignError, "RETRY_CONTINUATION_CANDIDATE_CLAIM"):
                    run_cold_review_cohort(fixture.root, retry_auth, FakeNoDispatchAdapter(lane="cold-review"), allow_test_fixture=True)
                self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)
                self.assertFalse(continuation_claim.exists())
                self.assertFalse((fixture.root / successor_claim).exists())
                self.assertFalse((fixture.root / "cold-review/retry-finalizers/attempt-02.json").exists())
                self.assertFalse((fixture.root / f"incidents/cold-review-{next_batch}.json").exists())

    def test_post_submit_observation_failure_is_conservatively_finalized_unknown(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-unknown-finalizer-") as temp:
            fixture = Fixture(Path(temp))
            adapter = FailingObserveAdapter()
            with self.assertRaisesRegex(CampaignError, "PROVIDER_EXECUTION_FAILED"):
                run_producer_cohort(fixture.root, fixture.authorization, adapter, allow_test_fixture=True)
            self.assertEqual(sum(event[0] == "submit" for event in adapter.log), 5)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(head["totals"]["unknown"], 5)
            self.assertEqual(head["totals"]["producer_invocations"], 5)
            self.assertTrue(head["unresolved_usage"])
            self.assertFalse(head["open_reservations"])
            finalizer = json.loads((fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8"))
            self.assertEqual(finalizer["candidate_status"], "CONSUMED_DISPATCH_UNKNOWN")
            self.assertTrue((fixture.root / "incidents/producer-task6-cycle-1.json").is_file())

    def test_producer_post_observation_phase_failures_settle_and_terminalize_exactly(self) -> None:
        faults = (
            "after-observation-validation",
            "after-settlement",
            "after-completion",
        )
        for fault in faults:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(
                prefix=f"daee-task6-producer-terminal-{fault}-"
            ) as temp:
                fixture = Fixture(Path(temp))
                adapter = FakeNoDispatchAdapter()
                with self.assertRaisesRegex(CampaignError, "INJECTED_TERMINAL_PHASE_FAILURE"):
                    run_producer_cohort(
                        fixture.root,
                        fixture.authorization,
                        adapter,
                        allow_test_fixture=True,
                        fault_at=fault,
                    )

                self.assertEqual(sum(event[0] == "submit" for event in adapter.log), 5)
                self.assertEqual(sum(event[0] == "observe" for event in adapter.log), 5)
                result_paths = sorted((fixture.root / "producer/results").glob("*.txt"))
                self.assertEqual(len(result_paths), 5)
                head = validate_head(fixture.root / "usage")
                self.assertEqual(head["totals"]["completed"], 5)
                self.assertEqual(head["totals"]["producer_invocations"], 5)
                self.assertFalse(head["open_reservations"])
                self.assertFalse(head["unresolved_usage"])

                incident = json.loads(
                    (fixture.root / "incidents/producer-task6-cycle-1.json").read_text(encoding="utf-8")
                )
                finalizer = json.loads(
                    (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
                )
                self.assertEqual(incident["failure_phase"], fault)
                self.assertEqual(finalizer["failure_phase"], fault)
                self.assertEqual(finalizer["attempt_index"], 1)
                self.assertEqual(finalizer["cycle_or_review_batch_id"], "task6-cycle-1")
                self.assertEqual(finalizer["candidate_status"], "CONSUMED_OBSERVED")
                self.assertEqual(finalizer["dispatch_classification"], "OBSERVED")
                self.assertEqual(len(finalizer["observed_results"]), 5)
                self.assertEqual(
                    {row["output"]["sha256"] for row in finalizer["observed_results"]},
                    {digest(path) for path in result_paths},
                )
                self.assertIsNotNone(finalizer["settlement_sha256"])
                self.assertFalse(finalizer["usage_unresolved"])
                self.assertFalse(finalizer["resumable_retry"])
                self.assertTrue(finalizer["terminal"])
                completion_path = fixture.root / "producer/completion.json"
                self.assertEqual(completion_path.exists(), fault == "after-completion")
                if fault == "after-completion":
                    self.assertEqual(finalizer["completion"]["sha256"], digest(completion_path))
                else:
                    self.assertIsNone(finalizer["completion"])

    def test_cold_post_observation_phase_failures_settle_and_terminalize_exactly(self) -> None:
        faults = (
            "after-observation-validation",
            "after-settlement",
            "after-completion",
        )
        for fault in faults:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(
                prefix=f"daee-task6-cold-terminal-{fault}-"
            ) as temp:
                fixture = Fixture(Path(temp))
                producer = run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    FakeNoDispatchAdapter(),
                    allow_test_fixture=True,
                )
                assessments = [
                    {
                        "case_id": case_id,
                        "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest(),
                    }
                    for case_id in CASES
                ]
                claim = claim_initial_assessments(
                    fixture.root,
                    producer,
                    assessments,
                    claimant="human:task6-assessor",
                )
                packets = fixture.build_packets(producer)
                cold_auth = fixture.cold_authorization(producer, claim, packets)
                adapter = FakeNoDispatchAdapter(lane="cold-review")
                with self.assertRaisesRegex(CampaignError, "INJECTED_TERMINAL_PHASE_FAILURE"):
                    run_cold_review_cohort(
                        fixture.root,
                        cold_auth,
                        adapter,
                        allow_test_fixture=True,
                        fault_at=fault,
                    )

                self.assertEqual(sum(event[0] == "submit" for event in adapter.log), 5)
                self.assertEqual(sum(event[0] == "observe" for event in adapter.log), 5)
                result_paths = sorted((fixture.root / "cold-review/results").glob("*.txt"))
                self.assertEqual(len(result_paths), 5)
                head = validate_head(fixture.root / "usage")
                self.assertEqual(head["totals"]["completed"], 10)
                self.assertEqual(head["totals"]["cold_review_invocations"], 5)
                self.assertFalse(head["open_reservations"])
                self.assertFalse(head["unresolved_usage"])

                incident = json.loads(
                    (fixture.root / "incidents/cold-review-task6-review-1.json").read_text(encoding="utf-8")
                )
                finalizer = json.loads(
                    (fixture.root / "cold-review/observation-finalizer.json").read_text(encoding="utf-8")
                )
                self.assertEqual(incident["failure_phase"], fault)
                self.assertEqual(finalizer["failure_phase"], fault)
                self.assertEqual(finalizer["attempt_index"], 1)
                self.assertEqual(finalizer["cycle_or_review_batch_id"], "task6-review-1")
                self.assertEqual(finalizer["candidate_status"], "CONSUMED_OBSERVED")
                self.assertEqual(finalizer["review_status"], "OBSERVED")
                self.assertEqual(finalizer["dispatch_classification"], "OBSERVED")
                self.assertEqual(len(finalizer["observed_results"]), 5)
                self.assertEqual(
                    {row["review_output"]["sha256"] for row in finalizer["observed_results"]},
                    {digest(path) for path in result_paths},
                )
                self.assertIsNotNone(finalizer["settlement_sha256"])
                self.assertFalse(finalizer["usage_unresolved"])
                self.assertFalse(finalizer["resumable_retry"])
                self.assertTrue(finalizer["terminal"])
                completion_path = fixture.root / "cold-review/completion.json"
                self.assertEqual(completion_path.exists(), fault == "after-completion")
                if fault == "after-completion":
                    self.assertEqual(finalizer["completion"]["sha256"], digest(completion_path))
                else:
                    self.assertIsNone(finalizer["completion"])

    def test_terminal_destination_collisions_fail_before_irreversible_campaign_state(self) -> None:
        for lane in ("producer", "cold-review"):
            for destination in ("incident", "finalizer"):
                with self.subTest(lane=lane, destination=destination), tempfile.TemporaryDirectory(
                    prefix=f"daee-task6-terminal-collision-{lane}-{destination}-"
                ) as temp:
                    fixture = Fixture(Path(temp))
                    if lane == "producer":
                        authorization = fixture.authorization
                        adapter = FakeNoDispatchAdapter()
                        incident_path = fixture.root / "incidents/producer-task6-cycle-1.json"
                        finalizer_path = fixture.root / "producer/observation-finalizer.json"
                        head_before = None
                    else:
                        producer = run_producer_cohort(
                            fixture.root,
                            fixture.authorization,
                            FakeNoDispatchAdapter(),
                            allow_test_fixture=True,
                        )
                        assessments = [
                            {
                                "case_id": case_id,
                                "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest(),
                            }
                            for case_id in CASES
                        ]
                        claim = claim_initial_assessments(
                            fixture.root,
                            producer,
                            assessments,
                            claimant="human:task6-assessor",
                        )
                        packets = fixture.build_packets(producer)
                        authorization = fixture.cold_authorization(producer, claim, packets)
                        adapter = FakeNoDispatchAdapter(lane="cold-review")
                        incident_path = fixture.root / "incidents/cold-review-task6-review-1.json"
                        finalizer_path = fixture.root / "cold-review/observation-finalizer.json"
                        head_before = head_snapshot(fixture.root / "usage")
                    write_json(
                        incident_path if destination == "incident" else finalizer_path,
                        {"schema": "substituted-terminal-publication-v1"},
                    )
                    with self.assertRaisesRegex(CampaignError, "TERMINAL_PUBLICATION_PREFLIGHT"):
                        if lane == "producer":
                            run_producer_cohort(
                                fixture.root,
                                authorization,
                                adapter,
                                allow_test_fixture=True,
                            )
                        else:
                            run_cold_review_cohort(
                                fixture.root,
                                authorization,
                                adapter,
                                allow_test_fixture=True,
                            )
                    self.assertEqual(adapter.log, [])
                    if lane == "producer":
                        self.assertFalse((fixture.root / "claims").exists())
                        self.assertFalse((fixture.root / "usage").exists())
                    else:
                        self.assertFalse((fixture.root / "claims/cold-review-authorization.json").exists())
                        self.assertFalse((fixture.root / "cold-review/packet-disclosure.json").exists())
                        self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)

    def test_standalone_success_finalizer_without_current_claims_or_usage_is_rejected_before_dispatch(self) -> None:
        for lane in ("producer", "cold-review"):
            with self.subTest(lane=lane), tempfile.TemporaryDirectory(
                prefix=f"daee-task6-standalone-success-no-custody-{lane}-"
            ) as temp:
                fixture = Fixture(Path(temp))
                if lane == "producer":
                    authorization = fixture.authorization
                    batch_id = "task6-cycle-1"
                    completion_path = fixture.root / "producer/completion.json"
                else:
                    authorization = self._prepare_cold_authorization(fixture)
                    batch_id = "task6-review-1"
                    completion_path = fixture.root / "cold-review/completion.json"
                auth_sha = digest(authorization)
                reservation_sha = "1" * 64
                settlement_sha = "2" * 64
                completion = {
                    "schema": "reviewed-campaign-producer-completion-v1" if lane == "producer" else "reviewed-campaign-cold-review-completion-v1",
                    "status": "PRODUCER_STRUCTURAL_COMPLETE" if lane == "producer" else "COLD_REVIEW_COHORT_COMPLETE",
                    "candidate_id": "forged-candidate-state",
                    "authorization_sha256": auth_sha,
                    "reservation_sha256": reservation_sha,
                    "settlement_sha256": settlement_sha,
                    "results": [],
                }
                write_json(completion_path, completion)
                finalizer_path = fixture.root / lane / "observation-finalizer.json"
                finalizer = {
                    "schema": "reviewed-campaign-observation-finalizer-v1",
                    "lane": lane,
                    "attempt_index": 1,
                    "candidate_id": fixture.candidate_id,
                    "cycle_or_review_batch_id": batch_id,
                    "authorization_sha256": auth_sha,
                    "authorization_claim": None,
                    "candidate_claim": None,
                    "continuation_claim": None,
                    "candidate_status": "READY_UNUSED",
                    "review_status": "NO_DISPATCH" if lane == "cold-review" else None,
                    "dispatch_status": "DETERMINISTIC_FAKE_COMPLETE",
                    "reservation_sha256": reservation_sha,
                    "settlement_sha256": settlement_sha,
                    "observed_results": [],
                    "completion": ref(fixture.root, completion_path),
                    "resulting_usage_head_sha256": "3" * 64,
                    "terminal": True,
                }
                write_json(finalizer_path, finalizer)
                head_before = head_snapshot(fixture.root / "usage") if lane == "cold-review" else None
                replay = FakeNoDispatchAdapter(lane=lane)

                with self.assertRaisesRegex(CampaignError, "TERMINAL_PUBLICATION_PREFLIGHT"):
                    if lane == "producer":
                        run_producer_cohort(
                            fixture.root,
                            authorization,
                            replay,
                            allow_test_fixture=True,
                        )
                    else:
                        run_cold_review_cohort(
                            fixture.root,
                            authorization,
                            replay,
                            allow_test_fixture=True,
                        )

                self.assertEqual(replay.log, [])
                if lane == "producer":
                    self.assertFalse((fixture.root / "claims").exists())
                    self.assertFalse((fixture.root / "usage").exists())
                else:
                    self.assertFalse((fixture.root / "claims/cold-review-authorization.json").exists())
                    self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)

    def test_standalone_success_finalizer_rejects_retained_artifact_substitutions_before_dispatch(self) -> None:
        for lane in ("producer", "cold-review"):
            fields = ["candidate_state", "claims", "results", "completion", "settlement", "usage_head"]
            if lane == "cold-review":
                fields.append("review_state")
            for field in fields:
                with self.subTest(lane=lane, field=field), tempfile.TemporaryDirectory(
                    prefix=f"daee-task6-standalone-success-substitution-{lane}-{field}-"
                ) as temp:
                    fixture = Fixture(Path(temp))
                    authorization, finalizer_path = self._complete_success_lane(fixture, lane)
                    finalizer = json.loads(finalizer_path.read_text(encoding="utf-8"))
                    if field == "candidate_state":
                        finalizer["candidate_status"] = "READY_UNUSED"
                    elif field == "review_state":
                        finalizer["review_status"] = "NO_DISPATCH"
                    elif field == "claims":
                        finalizer["authorization_claim"] = finalizer["candidate_claim"]
                    elif field == "results":
                        result_field = "output" if lane == "producer" else "review_output"
                        finalizer["observed_results"][0][result_field], finalizer["observed_results"][1][result_field] = (
                            finalizer["observed_results"][1][result_field],
                            finalizer["observed_results"][0][result_field],
                        )
                    elif field in {"completion", "settlement"}:
                        completion_path = fixture.root / str(finalizer["completion"]["path"])
                        completion = json.loads(completion_path.read_text(encoding="utf-8"))
                        substituted_path = fixture.root / lane / f"substituted-{field}-completion.json"
                        if field == "completion":
                            completion["candidate_id"] = "forged-candidate-state"
                        else:
                            completion["settlement_sha256"] = "0" * 64
                            finalizer["settlement_sha256"] = completion["settlement_sha256"]
                        write_json(substituted_path, completion)
                        finalizer["completion"] = ref(fixture.root, substituted_path)
                    elif field == "usage_head":
                        finalizer["resulting_usage_head_sha256"] = "0" * 64
                    else:  # pragma: no cover - test authoring guard
                        raise AssertionError(field)
                    write_json(finalizer_path, finalizer)
                    finalizer_raw = finalizer_path.read_bytes()
                    head_before = head_snapshot(fixture.root / "usage")
                    replay = FakeNoDispatchAdapter(lane=lane)

                    with self.assertRaisesRegex(CampaignError, "TERMINAL_PUBLICATION_PREFLIGHT"):
                        if lane == "producer":
                            run_producer_cohort(
                                fixture.root,
                                authorization,
                                replay,
                                allow_test_fixture=True,
                            )
                        else:
                            run_cold_review_cohort(
                                fixture.root,
                                authorization,
                                replay,
                                allow_test_fixture=True,
                            )

                    self.assertEqual(replay.log, [])
                    self.assertEqual(finalizer_path.read_bytes(), finalizer_raw)
                    self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)

    def test_standalone_success_completion_requires_exact_authoritative_identity_and_field_set(self) -> None:
        mutations = {
            "producer": {
                "source": lambda completion: completion.update({"source_commit": "f" * 40}),
                "protocol": lambda completion: completion.update({"review_protocol_sha256": "0" * 64}),
                "package": lambda completion: completion.update({"package_record_sha256": "0" * 64}),
                "omitted": lambda completion: completion.pop("source_commit"),
                "extra": lambda completion: completion.update({"self_attested_completion": True}),
            },
            "cold-review": {
                "producer_cycle": lambda completion: completion.update({"producer_cycle_id": "forged-producer-cycle"}),
                "protocol": lambda completion: completion.update({"review_protocol_sha256": "0" * 64}),
                "assessment": lambda completion: completion.update({"assessment_claim_sha256": "0" * 64}),
                "omitted": lambda completion: completion.pop("producer_cycle_id"),
                "extra": lambda completion: completion.update({"self_attested_completion": True}),
            },
        }
        for lane, lane_mutations in mutations.items():
            for name, mutate in lane_mutations.items():
                with self.subTest(lane=lane, mutation=name), tempfile.TemporaryDirectory(
                    prefix=f"daee-task6-success-completion-identity-{lane}-{name}-"
                ) as temp:
                    fixture = Fixture(Path(temp))
                    authorization, finalizer_path = self._complete_success_lane(fixture, lane)
                    finalizer = json.loads(finalizer_path.read_text(encoding="utf-8"))
                    completion_path = fixture.root / str(finalizer["completion"]["path"])
                    completion = json.loads(completion_path.read_text(encoding="utf-8"))
                    mutate(completion)
                    write_json(completion_path, completion)
                    finalizer["completion"] = ref(fixture.root, completion_path)
                    write_json(finalizer_path, finalizer)
                    completion_raw = completion_path.read_bytes()
                    finalizer_raw = finalizer_path.read_bytes()
                    head_before = head_snapshot(fixture.root / "usage")
                    replay = FakeNoDispatchAdapter(lane=lane)

                    with self.assertRaisesRegex(CampaignError, "TERMINAL_PUBLICATION_PREFLIGHT"):
                        if lane == "producer":
                            run_producer_cohort(
                                fixture.root,
                                authorization,
                                replay,
                                allow_test_fixture=True,
                            )
                        else:
                            run_cold_review_cohort(
                                fixture.root,
                                authorization,
                                replay,
                                allow_test_fixture=True,
                            )

                    self.assertEqual(replay.log, [])
                    self.assertEqual(completion_path.read_bytes(), completion_raw)
                    self.assertEqual(finalizer_path.read_bytes(), finalizer_raw)
                    self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)

    def test_standalone_success_finalizer_exact_replay_is_zero_dispatch_and_idempotent(self) -> None:
        for lane in ("producer", "cold-review"):
            with self.subTest(lane=lane), tempfile.TemporaryDirectory(
                prefix=f"daee-task6-standalone-success-exact-{lane}-"
            ) as temp:
                fixture = Fixture(Path(temp))
                authorization, finalizer_path = self._complete_success_lane(fixture, lane)
                finalizer_raw = finalizer_path.read_bytes()
                head_before = head_snapshot(fixture.root / "usage")
                replay = FakeNoDispatchAdapter(lane=lane)
                with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED_CREATE_ONCE"):
                    if lane == "producer":
                        run_producer_cohort(
                            fixture.root,
                            authorization,
                            replay,
                            allow_test_fixture=True,
                        )
                    else:
                        run_cold_review_cohort(
                            fixture.root,
                            authorization,
                            replay,
                            allow_test_fixture=True,
                        )
                self.assertEqual(replay.log, [])
                self.assertEqual(finalizer_path.read_bytes(), finalizer_raw)
                self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)

    def test_interrupted_terminal_resume_rejects_well_formed_incident_substitutions_before_dispatch(self) -> None:
        def substitute(incident: dict[str, object], field: str) -> None:
            payload = incident["finalizer_payload"]
            assert isinstance(payload, dict)
            if field == "terminal":
                payload["terminal"] = False
            elif field == "claims":
                payload["authorization_claim"] = payload["candidate_claim"]
            elif field == "results":
                results = payload["observed_results"]
                assert isinstance(results, list) and len(results) == 5
                result_field = "output" if "output" in results[0] else "review_output"
                results[0][result_field], results[1][result_field] = (
                    results[1][result_field],
                    results[0][result_field],
                )
            elif field == "completion":
                payload["completion"] = payload["authorization_claim"]
                incident["completion"] = payload["completion"]
            elif field == "settlement":
                payload["settlement_sha256"] = "0" * 64
                incident["settlement_sha256"] = payload["settlement_sha256"]
            elif field == "phase":
                payload["failure_phase"] = "provider-execution"
                incident["failure_phase"] = payload["failure_phase"]
            elif field == "classification":
                payload["dispatch_classification"] = "OUTCOME_UNKNOWN"
                incident["dispatch_classification"] = payload["dispatch_classification"]
            elif field == "candidate_state":
                payload["candidate_status"] = "READY_UNUSED"
            elif field == "review_state":
                payload["review_status"] = "NO_DISPATCH"
            else:  # pragma: no cover - test authoring guard
                raise AssertionError(field)

        for lane in ("producer", "cold-review"):
            fields = ["terminal", "claims", "results", "completion", "settlement", "phase", "classification", "candidate_state"]
            if lane == "cold-review":
                fields.append("review_state")
            for field in fields:
                with self.subTest(lane=lane, field=field), tempfile.TemporaryDirectory(
                    prefix=f"daee-task6-terminal-substitution-{lane}-{field}-"
                ) as temp:
                    fixture = Fixture(Path(temp))
                    if lane == "producer":
                        authorization = fixture.authorization
                        first = FakeNoDispatchAdapter()
                        with self.assertRaisesRegex(CampaignError, "INJECTED_TERMINAL_PUBLICATION_INTERRUPTION"):
                            run_producer_cohort(
                                fixture.root,
                                authorization,
                                first,
                                allow_test_fixture=True,
                                fault_at="after-incident-publication",
                            )
                        incident_path = fixture.root / "incidents/producer-task6-cycle-1.json"
                        finalizer_path = fixture.root / "producer/observation-finalizer.json"
                    else:
                        producer = run_producer_cohort(
                            fixture.root,
                            fixture.authorization,
                            FakeNoDispatchAdapter(),
                            allow_test_fixture=True,
                        )
                        assessments = [
                            {
                                "case_id": case_id,
                                "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest(),
                            }
                            for case_id in CASES
                        ]
                        claim = claim_initial_assessments(
                            fixture.root,
                            producer,
                            assessments,
                            claimant="human:task6-assessor",
                        )
                        packets = fixture.build_packets(producer)
                        authorization = fixture.cold_authorization(producer, claim, packets)
                        first = FakeNoDispatchAdapter(lane="cold-review")
                        with self.assertRaisesRegex(CampaignError, "INJECTED_TERMINAL_PUBLICATION_INTERRUPTION"):
                            run_cold_review_cohort(
                                fixture.root,
                                authorization,
                                first,
                                allow_test_fixture=True,
                                fault_at="after-incident-publication",
                            )
                        incident_path = fixture.root / "incidents/cold-review-task6-review-1.json"
                        finalizer_path = fixture.root / "cold-review/observation-finalizer.json"

                    self.assertTrue(incident_path.is_file())
                    self.assertFalse(finalizer_path.exists())
                    incident = json.loads(incident_path.read_text(encoding="utf-8"))
                    substitute(incident, field)
                    write_json(incident_path, incident)
                    head_before = head_snapshot(fixture.root / "usage")
                    replay = FakeNoDispatchAdapter(lane=lane)

                    with self.assertRaisesRegex(CampaignError, "TERMINAL_PUBLICATION_PREFLIGHT"):
                        if lane == "producer":
                            run_producer_cohort(
                                fixture.root,
                                authorization,
                                replay,
                                allow_test_fixture=True,
                            )
                        else:
                            run_cold_review_cohort(
                                fixture.root,
                                authorization,
                                replay,
                                allow_test_fixture=True,
                            )

                    self.assertEqual(replay.log, [])
                    self.assertFalse(finalizer_path.exists())
                    self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)

    def test_producer_interruption_after_incident_resumes_exact_finalizer_without_redispatch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-producer-incident-resume-") as temp:
            fixture = Fixture(Path(temp))
            first = FakeNoDispatchAdapter()
            with self.assertRaises(CampaignError) as raised:
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    first,
                    allow_test_fixture=True,
                    fault_at="after-incident-publication",
                )
            self.assertIn("INJECTED_TERMINAL_PHASE_FAILURE", str(raised.exception))
            self.assertIn("INJECTED_TERMINAL_PUBLICATION_INTERRUPTION", str(raised.exception))
            self.assertEqual(sum(event[0] == "submit" for event in first.log), 5)
            self.assertEqual(sum(event[0] == "observe" for event in first.log), 5)
            incident_path = fixture.root / "incidents/producer-task6-cycle-1.json"
            finalizer_path = fixture.root / "producer/observation-finalizer.json"
            self.assertTrue(incident_path.is_file())
            self.assertFalse(finalizer_path.exists())
            head_after_failure = head_snapshot(fixture.root / "usage")
            self.assertFalse(head_after_failure["open_reservations"])

            second = FakeNoDispatchAdapter()
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    second,
                    allow_test_fixture=True,
                )
            self.assertEqual(second.log, [])
            incident = json.loads(incident_path.read_text(encoding="utf-8"))
            finalizer = json.loads(finalizer_path.read_text(encoding="utf-8"))
            self.assertEqual(finalizer, {**incident["finalizer_payload"], "incident": ref(fixture.root, incident_path)})
            finalizer_raw = finalizer_path.read_bytes()
            third = FakeNoDispatchAdapter()
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    third,
                    allow_test_fixture=True,
                )
            self.assertEqual(third.log, [])
            self.assertEqual(finalizer_path.read_bytes(), finalizer_raw)
            self.assertEqual(head_snapshot(fixture.root / "usage"), head_after_failure)

    def test_cold_interruption_after_incident_resumes_exact_finalizer_without_redispatch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-cold-incident-resume-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(
                fixture.root,
                fixture.authorization,
                FakeNoDispatchAdapter(),
                allow_test_fixture=True,
            )
            assessments = [
                {
                    "case_id": case_id,
                    "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest(),
                }
                for case_id in CASES
            ]
            claim = claim_initial_assessments(
                fixture.root,
                producer,
                assessments,
                claimant="human:task6-assessor",
            )
            packets = fixture.build_packets(producer)
            authorization = fixture.cold_authorization(producer, claim, packets)
            first = FakeNoDispatchAdapter(lane="cold-review")
            with self.assertRaises(CampaignError) as raised:
                run_cold_review_cohort(
                    fixture.root,
                    authorization,
                    first,
                    allow_test_fixture=True,
                    fault_at="after-incident-publication",
                )
            self.assertIn("INJECTED_TERMINAL_PHASE_FAILURE", str(raised.exception))
            self.assertIn("INJECTED_TERMINAL_PUBLICATION_INTERRUPTION", str(raised.exception))
            self.assertEqual(sum(event[0] == "submit" for event in first.log), 5)
            self.assertEqual(sum(event[0] == "observe" for event in first.log), 5)
            incident_path = fixture.root / "incidents/cold-review-task6-review-1.json"
            finalizer_path = fixture.root / "cold-review/observation-finalizer.json"
            self.assertTrue(incident_path.is_file())
            self.assertFalse(finalizer_path.exists())
            head_after_failure = head_snapshot(fixture.root / "usage")

            second = FakeNoDispatchAdapter(lane="cold-review")
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_cold_review_cohort(
                    fixture.root,
                    authorization,
                    second,
                    allow_test_fixture=True,
                )
            self.assertEqual(second.log, [])
            incident = json.loads(incident_path.read_text(encoding="utf-8"))
            finalizer = json.loads(finalizer_path.read_text(encoding="utf-8"))
            self.assertEqual(finalizer, {**incident["finalizer_payload"], "incident": ref(fixture.root, incident_path)})
            finalizer_raw = finalizer_path.read_bytes()
            third = FakeNoDispatchAdapter(lane="cold-review")
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_cold_review_cohort(
                    fixture.root,
                    authorization,
                    third,
                    allow_test_fixture=True,
                )
            self.assertEqual(third.log, [])
            self.assertEqual(finalizer_path.read_bytes(), finalizer_raw)
            self.assertEqual(head_snapshot(fixture.root / "usage"), head_after_failure)

    def test_terminal_fault_hook_requires_test_authority_before_claim_or_reservation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-producer-hook-auth-") as temp:
            fixture = Fixture(Path(temp))
            adapter = FakeNoDispatchAdapter()
            with self.assertRaisesRegex(CampaignError, "UNSUPPORTED_FAULT_INJECTION"):
                run_producer_cohort(
                    fixture.root,
                    fixture.authorization,
                    adapter,
                    allow_test_fixture=False,
                    fault_at="after-incident-publication",
                )
            self.assertEqual(adapter.log, [])
            self.assertFalse((fixture.root / "claims").exists())
            self.assertFalse((fixture.root / "usage").exists())

        with tempfile.TemporaryDirectory(prefix="daee-task6-cold-hook-auth-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(
                fixture.root,
                fixture.authorization,
                FakeNoDispatchAdapter(),
                allow_test_fixture=True,
            )
            assessments = [
                {
                    "case_id": case_id,
                    "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest(),
                }
                for case_id in CASES
            ]
            claim = claim_initial_assessments(
                fixture.root,
                producer,
                assessments,
                claimant="human:task6-assessor",
            )
            packets = fixture.build_packets(producer)
            authorization = fixture.cold_authorization(producer, claim, packets)
            adapter = FakeNoDispatchAdapter(lane="cold-review")
            head_before = head_snapshot(fixture.root / "usage")
            with self.assertRaisesRegex(CampaignError, "UNSUPPORTED_FAULT_INJECTION"):
                run_cold_review_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=False,
                    fault_at="after-incident-publication",
                )
            self.assertEqual(adapter.log, [])
            self.assertFalse((fixture.root / "claims/cold-review-authorization.json").exists())
            self.assertFalse((fixture.root / "cold-review/packet-disclosure.json").exists())
            self.assertEqual(head_snapshot(fixture.root / "usage"), head_before)

    def test_authorization_and_candidate_claims_are_irreversible(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-replay-") as temp:
            fixture = Fixture(Path(temp))
            first = FakeNoDispatchAdapter()
            run_producer_cohort(fixture.root, fixture.authorization, first, allow_test_fixture=True)
            head_before = validate_head(fixture.root / "usage")
            second = FakeNoDispatchAdapter()
            with self.assertRaisesRegex(CampaignError, "CREATE_ONCE"):
                run_producer_cohort(fixture.root, fixture.authorization, second, allow_test_fixture=True)
            self.assertEqual(second.log, [])
            self.assertEqual(validate_head(fixture.root / "usage"), head_before)

    def test_retry_lineage_requires_owner_authorized_predecessor_incident(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-retry-") as temp:
            root = Path(temp)
            validate_retry_lineage(root, {"attempt_index": 1, "continuation_authorization": None})
            with self.assertRaisesRegex(CampaignError, "RETRY_LINEAGE"):
                validate_retry_lineage(root, {"attempt_index": 2, "continuation_authorization": None})
            with self.assertRaisesRegex(CampaignError, "RETRY_LINEAGE"):
                validate_retry_lineage(root, {"attempt_index": True, "continuation_authorization": None})

    def test_human_claimant_and_adjudicator_identities_reject_whitespace_aliases(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-human-id-") as temp:
            fixture = Fixture(Path(temp))
            producer = run_producer_cohort(fixture.root, fixture.authorization, FakeNoDispatchAdapter(), allow_test_fixture=True)
            assessments = [
                {"case_id": case_id, "assessment_sha256": hashlib.sha256(f"human:{case_id}".encode()).hexdigest()}
                for case_id in CASES
            ]
            with self.assertRaisesRegex(CampaignError, "HUMAN_CLAIMANT_IDENTITY"):
                claim_initial_assessments(fixture.root, producer, assessments, claimant="human:task6-assessor ")

    def test_actual_candidate_verdict_shape_extracts_exact_campaign_bindings(self) -> None:
        candidate_record = {"path": "candidate/record.json", "byte_count": 10, "sha256": "a" * 64}
        source_preflight = {"path": "source/preflight.json", "byte_count": 11, "sha256": "b" * 64}
        registry = {"path": "registry.json", "byte_count": 12, "sha256": "c" * 64}
        review_protocol = {"path": "review-protocol.json", "byte_count": 13, "sha256": "d" * 64}
        value = {
            "schema": "daee-no-model-candidate-maturity-v1",
            "kind": "candidate-maturity",
            "status": "NO_MODEL_CANDIDATE_MATURE",
            "source": {"commit_sha": "1" * 40},
            "candidate": {
                "candidate_id": "mature-candidate-1",
                "status": "READY_UNUSED",
                "claim_status": "UNCLAIMED",
                "candidate_record": candidate_record,
                "package_tree_sha256": "e" * 64,
            },
            "source_preflight": source_preflight,
            "registries": {"input": registry, "review_protocol": review_protocol},
        }
        identity = extract_mature_candidate_identity(value)
        self.assertEqual(identity["candidate_id"], "mature-candidate-1")
        self.assertEqual(identity["source_commit"], "1" * 40)
        self.assertEqual(identity["package_record"], candidate_record)
        self.assertEqual(identity["source_preflight"], source_preflight)
        self.assertEqual(identity["registry"], registry)
        self.assertEqual(identity["review_protocol"], review_protocol)

    def test_paired_gpt_opus_canary_is_fake_only_and_live_opus_is_unreachable(self) -> None:
        canary = simulate_paired_gpt_opus_canary(["gpt"] * 5, ["opus"] * 5)
        self.assertFalse(validate_dispatch_manifest(canary["dispatch_manifest"], 10))
        self.assertEqual(canary["gpt_fake_results"], 5)
        self.assertEqual(canary["opus_fake_results"], 5)
        self.assertFalse(canary["live_opus_reachable"])
        self.assertFalse(canary["live_opus_authorized"])
        self.assertFalse(canary["authorization_consumed"])

    def test_existing_usage_recovery_consumes_exact_authority_and_fails_closed_unknown_without_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-recovery-") as temp:
            ledger = Path(temp)
            snapshot = head_snapshot(ledger)
            reservation = reserve(
                ledger,
                cohort="gpt-producer",
                calls=5,
                expected_sequence=snapshot["sequence"],
                expected_head_sha256=snapshot["head_sha256"],
                campaign_authorization_sha256="c" * 64,
                authorization_sha256="a" * 64,
                candidate_id="task6-recovery-candidate",
                cycle_or_review_batch_id="task6-recovery-cycle",
                call_subject_ids=[f"subject-{index}" for index in range(5)],
            )
            authorization = {
                "schema": "campaign-usage-recovery-authorization-v1",
                "kind": "orphan-recovery-authorization",
                "authorization_id": "task6-recovery-1",
                "campaign_authorization_sha256": "c" * 64,
                "authorization_sha256": "a" * 64,
                "reservation_sha256": reservation["transaction_sha256"],
                "orphan_id": "task6-orphan-1",
                "candidate_id": "task6-recovery-candidate",
                "expected_usage_head_sha256": head_snapshot(ledger)["head_sha256"],
                "claim_path": "claims/task6-recovery-1.json",
                "dispatch_provider_evidence_path": None,
                "dispatch_provider_evidence_sha256": None,
            }
            auth_path = ledger / "recovery-authorization.json"
            write_json(auth_path, authorization)
            recovered = recover_orphan(
                ledger,
                reservation["transaction_sha256"],
                recovery_authorization=auth_path,
                orphan_id="task6-orphan-1",
                candidate_id="task6-recovery-candidate",
                completed=0,
                failed=0,
                cancelled=0,
                not_dispatched=5,
                unknown=0,
            )
            self.assertEqual(recovered["unknown"], 5)
            self.assertTrue(validate_head(ledger)["unresolved_usage"])
            with self.assertRaisesRegex(ValueError, "recovery_authorization_replay"):
                recover_orphan(
                    ledger,
                    reservation["transaction_sha256"],
                    recovery_authorization=auth_path,
                    orphan_id="task6-orphan-1",
                    candidate_id="task6-recovery-candidate",
                    completed=0,
                    failed=0,
                    cancelled=0,
                    not_dispatched=0,
                    unknown=5,
                )

    def test_orchestrator_self_test_is_no_dispatch(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-B", str(TOOLS / "reviewed_campaign_orchestrator.py"), "--self-test"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("reviewed campaign orchestrator self-test: PASS", proc.stdout)

    def test_cold_review_cli_live_provider_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-cold-cli-") as temp:
            fixture = Fixture(Path(temp))
            proc = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(TOOLS / "run_reviewed_cold_review_cohort.py"),
                    "--custody-root",
                    str(fixture.root),
                    "--authorization",
                    str(fixture.authorization),
                    "--provider",
                    "codex-live",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=20,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("LIVE_PROVIDER_UNSUPPORTED", proc.stdout)
            self.assertFalse((fixture.root / "claims").exists())


class _CompletedCodexProcess:
    def __init__(self, pid: int, log: list[tuple[str, str]], worker: str, *, returncode: int = 0, interrupt: bool = False, timeout: bool = False, already_exited: bool = False, on_success: object | None = None) -> None:
        self.pid = pid
        self._log = log
        self._worker = worker
        self._complete = already_exited
        self._returncode = returncode
        self._interrupt = interrupt
        self._timeout = timeout
        self._on_success = on_success
        self.owned_descendant_active = not already_exited
        self.wait_timeouts: list[float | None] = []

    def poll(self) -> int | None:
        return self._returncode if self._complete else None

    def wait(self, timeout: float | None = None) -> int:
        self._log.append(("observe", self._worker))
        self.wait_timeouts.append(timeout)
        if self._interrupt:
            self._interrupt = False
            raise KeyboardInterrupt("injected observation interrupt")
        if self._timeout:
            self._timeout = False
            raise subprocess.TimeoutExpired("fixture-codex", timeout or 1)
        self._complete = True
        if self._returncode == 0:
            if callable(self._on_success):
                self._on_success()
                self._on_success = None
            self.owned_descendant_active = False
        return self._returncode


class _StartedProcessFailure(RuntimeError):
    def __init__(self, process: _CompletedCodexProcess) -> None:
        super().__init__("injected submit failure after process start")
        self.process = process


class _ScriptedCodexHost:
    """No-network process double for the production adapter boundary."""

    def __init__(self, *, fail_probe: bool = False, fail_start_at: int | None = None, fail_after_start_at: int | None = None, nonzero_at: int | None = None, interrupt_at: int | None = None, timeout_at: int | None = None, already_exited_at: int | None = None, credential_residue_at: int | None = None, credential_residue_encoding: str = "utf-8") -> None:
        self.fail_probe = fail_probe
        self.fail_start_at = fail_start_at
        self.fail_after_start_at = fail_after_start_at
        self.nonzero_at = nonzero_at
        self.interrupt_at = interrupt_at
        self.timeout_at = timeout_at
        self.already_exited_at = already_exited_at
        self.credential_residue_at = credential_residue_at
        self.credential_residue_encoding = credential_residue_encoding
        self.log: list[tuple[str, str]] = []
        self.starts: list[dict[str, object]] = []
        self.processes: list[_CompletedCodexProcess] = []
        self.aborted: list[int] = []
        self.verified: list[int] = []
        self.probe_carriers: list[bool] = []

    def probe(self, executable: Path, *, credential_carrier_available: bool) -> dict[str, object]:
        if type(credential_carrier_available) is not bool:
            raise TypeError("credential carrier availability must be Boolean")
        self.log.append(("probe", executable.name))
        self.probe_carriers.append(credential_carrier_available)
        if self.fail_probe:
            raise RuntimeError("injected local capability failure")
        return {
            "version": "codex-cli 0.130.0-alpha.5",
            "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "catalog_row": {"slug": "gpt-5.5", "supported_reasoning_efforts": ["none", "low", "medium", "high"]},
            "canonical_exec_flags": ["--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "-C", "-s", "-m", "-c", "--output-last-message", "-"],
            "credential_carrier_available": credential_carrier_available,
        }

    def start(
        self,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        prompt_path: Path,
        event_log_path: Path,
        stderr_path: Path,
        output_path: Path,
        worker: str,
    ) -> _CompletedCodexProcess:
        self.log.append(("start", worker))
        ordinal = len(self.starts) + 1
        if self.fail_start_at == ordinal:
            raise RuntimeError("injected submit failure")
        thread_id = f"thread-{len(self.starts) + 1:02d}"
        event_log_path.write_bytes(
            canonical({"type": "thread.started", "thread_id": thread_id})
            + canonical({"type": "turn.started"})
        )
        stderr_path.write_bytes(b"")

        def complete_successfully() -> None:
            event_log_path.write_bytes(
                event_log_path.read_bytes()
                + canonical({"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 20}})
            )
            output_path.write_text(f"captured output for {worker}\n", encoding="utf-8", newline="\n")
        self.starts.append(
            {
                "command": list(command),
                "cwd": cwd,
                "env": dict(env),
                "prompt": prompt_path.read_bytes(),
                "runtime_core_routing": (cwd / "references/runtime-core-routing.md").read_bytes(),
                "event_log_path": event_log_path,
                "output_path": output_path,
                "worker": worker,
            }
        )
        if self.credential_residue_at == ordinal:
            residue = Path(env["TEMP"]) / "credential-residue.bin"
            credential = env.get(
                "CODEX_ACCESS_TOKEN",
                "eyJhbGciOiJub25lIn0.eyJzdWJqZWN0IjoidGVzdCJ9.c3ludGhldGljLXNpZ25hdHVyZQ",
            )
            residue.write_bytes(credential.encode(self.credential_residue_encoding))
        process = _CompletedCodexProcess(
            1000 + len(self.starts), self.log, worker,
            returncode=9 if self.nonzero_at == ordinal else 0,
            interrupt=self.interrupt_at == ordinal,
            timeout=self.timeout_at == ordinal,
            already_exited=self.already_exited_at == ordinal,
            on_success=complete_successfully,
        )
        self.processes.append(process)
        if self.fail_after_start_at == ordinal:
            raise _StartedProcessFailure(process)
        return process

    def terminate_tree(self, process: _CompletedCodexProcess) -> None:
        self.aborted.append(process.pid)
        process._complete = True
        process.owned_descendant_active = False

    def verify_tree_stopped(self, process: _CompletedCodexProcess) -> bool:
        self.verified.append(process.pid)
        return process.poll() is not None and not process.owned_descendant_active


class _ScriptedCodexTestAdapter:
    """Non-provider wrapper for production-shaped adapter contract tests."""

    def __init__(
        self,
        *,
        custody_root: Path,
        codex_executable: Path,
        host: _ScriptedCodexHost,
        command_timeout_seconds: int = 30,
        fixture_token: str | None = "non-provider-scripted-fixture-token",
    ) -> None:
        from codex_live_producer_adapter import CodexLiveProducerAdapter

        if not isinstance(host, _ScriptedCodexHost):
            raise TypeError("scripted Codex test adapter requires the local non-provider test host")
        self._host = host
        self._executable = codex_executable
        self._fixture_token = fixture_token
        self._inner = CodexLiveProducerAdapter(
            custody_root=custody_root,
            codex_executable=codex_executable,
            access_token=fixture_token,
            host=host,
            command_timeout_seconds=command_timeout_seconds,
        )
        self._capability: dict[str, object] | None = None

    def capability(self) -> dict[str, object]:
        probe = self._host.probe(
            self._executable,
            credential_carrier_available=self._inner._credential_carrier_available(),
        )
        self._capability = {
            "schema": "reviewed-campaign-provider-capability-v1",
            "adapter_kind": "codex-scripted-test-no-provider",
            "adapter_version": "codex-scripted-test-v1",
            "host_application_version": probe["version"],
            "codex_executable_sha256": probe["executable_sha256"],
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "test_only": True,
            "paid_provider_reachable": False,
            "live_execution_authorized": False,
        }
        self._inner._capability = copy.deepcopy(self._capability)
        return copy.deepcopy(self._capability)

    def prepare(
        self,
        auth: dict[str, object],
        bindings: dict[str, object],
        *,
        allow_test_fixture: bool = False,
    ) -> None:
        if not allow_test_fixture:
            raise RuntimeError("scripted Codex adapter is test-only")
        if self._capability is None:
            raise RuntimeError("scripted Codex capability must be established first")
        self._inner.prepare(auth, bindings, allow_test_fixture=True)

    def submit(self, execution_custody: dict[str, object]) -> dict[str, object]:
        return self._inner.submit(execution_custody)

    def submit_tail(self, execution_custodies: list[dict[str, object]]) -> list[dict[str, object]]:
        return self._inner.submit_tail(execution_custodies)

    def observe(self, handle: str, execution_custody: dict[str, object]) -> dict[str, object]:
        return self._inner.observe(handle, execution_custody)

    def observe_many(
        self,
        handles: list[str],
        execution_custodies: list[dict[str, object]],
    ) -> tuple[list[dict[str, object] | None], BaseException | None]:
        return self._inner.observe_many(handles, execution_custodies)

    def execution_bindings(self) -> dict[str, dict[str, object]]:
        return self._inner.execution_bindings()

    def attempt_states(self) -> dict[str, dict[str, object]]:
        return self._inner.attempt_states()

    def abort_all(self) -> None:
        self._inner.abort_all()

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)


class LiveProducerContractTests(unittest.TestCase):
    def _live_fixture(
        self,
        root: Path,
        *,
        full_tooling: bool = False,
        command_timeout_seconds: int = 30,
        uppercase_registry_hashes: bool = False,
        pretty_source_documents: bool = False,
    ) -> tuple[Fixture, Path, Path, bytes]:
        fixture = Fixture(root)
        if full_tooling:
            import checker_execution_snapshot as checker_snapshot
            import run_staged_current_skill_smoke as stage_runner

            plan = stage_runner.stage07_release_invocation_plan(
                ROOT,
                ROOT / ".daee" / "production-shaped-tooling-manifest-output.md",
            )
            for relative, source in checker_snapshot.execution_snapshot_sources(root=ROOT, plan=plan).items():
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)

            def git(*arguments: str) -> str:
                completed = subprocess.run(
                    ["git", *arguments],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=120,
                )
                if completed.returncode != 0:
                    raise AssertionError(completed.stdout + completed.stderr)
                return completed.stdout.strip()

            git("init", "--quiet")
            git("config", "core.autocrlf", "false")
            git("config", "user.email", "live-producer-fixture@example.invalid")
            git("config", "user.name", "Live Producer Fixture")
            git("add", "--all", "--", "tools", "schema", "atomics", "tests")
            git("commit", "--quiet", "-m", "exact tooling fixture")
            fixture.source_commit = git("rev-parse", "HEAD")
        package_root = root / "candidate/extracted"
        manifest = json.loads((ROOT / "skill/build-manifest.json").read_text(encoding="utf-8"))
        for listed in manifest["canonical_package_files"]:
            relative = Path(listed.removeprefix("skill/"))
            source = ROOT / "skill" / relative
            destination = package_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        skill_bytes = (package_root / "SKILL.md").read_bytes()
        fixture.package_tree_sha = __import__("artifact_tree").tree_sha256(package_root)
        registry = json.loads(fixture.registry.read_text(encoding="utf-8"))
        for index, row in enumerate(registry["cases"], 1):
            raw = f"canonical input {index} for {row['case_id']}\n".encode()
            target = root / row["input_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            row["raw_bytes"] = len(raw)
            raw_sha256 = hashlib.sha256(raw).hexdigest()
            row["raw_sha256"] = raw_sha256.upper() if uppercase_registry_hashes else raw_sha256
        source_document_writer = write_pretty_json if pretty_source_documents else write_json
        source_document_writer(fixture.registry, registry)
        protocol = json.loads(fixture.protocol.read_text(encoding="utf-8"))
        protocol["input_registry"] = {
            "path": fixture.registry.relative_to(root).as_posix(),
            "sha256": digest(fixture.registry),
        }
        source_document_writer(fixture.protocol, protocol)
        # Refresh the fake Task6 bindings after the exact registry/protocol bytes change.
        package = json.loads(fixture.package.read_text(encoding="utf-8"))
        package["registry_sha256"] = digest(fixture.registry)
        package.update(
            {
                "source_commit": fixture.source_commit,
                "candidate_root": "candidate",
                "extracted_root": "extracted",
                "package_tree_sha256": fixture.package_tree_sha,
                "skill_root": ref(root, package_root / "SKILL.md"),
                "build_manifest": ref(root, package_root / "build-manifest.json"),
            }
        )
        write_json(fixture.package, package)
        preflight = json.loads(fixture.preflight.read_text(encoding="utf-8"))
        preflight["registry_sha256"] = digest(fixture.registry)
        preflight["source_commit"] = fixture.source_commit
        preflight["review_protocol_sha256"] = digest(fixture.protocol)
        write_json(fixture.preflight, preflight)
        candidate = json.loads(fixture.candidate.read_text(encoding="utf-8"))
        candidate["package_record_sha256"] = digest(fixture.package)
        candidate["source_commit"] = fixture.source_commit
        candidate["package_tree_sha256"] = fixture.package_tree_sha
        candidate["source_preflight_sha256"] = digest(fixture.preflight)
        candidate["registry_sha256"] = digest(fixture.registry)
        candidate["review_protocol_sha256"] = digest(fixture.protocol)
        write_json(fixture.candidate, candidate)
        executable = root / "bin/codex.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"bounded codex executable fixture\n")
        initial_head = head_snapshot(root / "usage")
        tooling_path = root / "authorizations/stage07-execution-tooling.json"
        if full_tooling:
            tooling_ref = tooling_manifest.publish_execution_tooling_manifest(
                root=root,
                source_commit=fixture.source_commit,
                output_path=tooling_path.relative_to(root),
            )
        else:
            write_json(tooling_path, synthetic_execution_tooling_manifest(fixture.source_commit))
            tooling_ref = ref(root, tooling_path)
        matrix_tooling_ref = {"path": tooling_ref["path"], "sha256": tooling_ref["sha256"]}
        registry_value = json.loads(fixture.registry.read_text(encoding="utf-8"))
        case_inputs = [
            {"case_id": row["case_id"], "input_sha256": row["raw_sha256"].lower()}
            for row in registry_value["cases"]
        ]
        branch = "codex/v0.4.6.0-runtime-footprint-b11"
        parent = {
            "schema": "reviewed-campaign-owner-authorization-v1",
            "kind": "reviewed-five-smoke-campaign",
            "authorization_id": "owner-five-smoke-01",
            "status": "ACTIVE",
            "revoked": False,
            "valid_not_before": "2026-07-12T00:00:00Z",
            "valid_not_after": "2099-07-12T02:00:00Z",
            "branch": branch,
            "source_commit": fixture.source_commit,
            "source_preflight": {"path": fixture.preflight.relative_to(root).as_posix(), "sha256": digest(fixture.preflight)},
            "candidate_id": fixture.candidate_id,
            "candidate_state": "READY_UNUSED",
            "candidate_claim_status": "UNCLAIMED",
            "package_profile": "execution-mini",
            "package_sha256": fixture.package_sha,
            "package_tree_sha256": fixture.package_tree_sha,
            "input_registry": {"path": fixture.registry.relative_to(root).as_posix(), "sha256": digest(fixture.registry)},
            "review_protocol": {"path": fixture.protocol.relative_to(root).as_posix(), "sha256": digest(fixture.protocol)},
            "action": "RUN_REVIEWED_FIVE_SMOKE",
            "lane": "producer",
            "model_runner": "codex",
            "producer_model": "gpt-5.5",
            "producer_reasoning_effort": "high",
            "authorized_calls": 5,
            "case_inputs": case_inputs,
            "automatic_retry_authorized": False,
            "optional_opus_authorized": False,
        }
        parent["authorization_sha256"] = record_sha256(parent)
        parent_path = root / "authorizations/owner-five-smoke.json"
        write_json(parent_path, parent)
        matrix = {
            "schema": "daee-smoke-matrix-v1",
            "kind": "matrix-authorization",
            "authorization_id": "live-producer-child-01",
            "action": "RUN_REVIEWED_FIVE_SMOKE",
            "one_use": True,
            "candidate_id": fixture.candidate_id,
            "candidate_record": {"path": fixture.package.relative_to(root).as_posix(), "sha256": digest(fixture.package)},
            "candidate_readiness": {"path": fixture.candidate.relative_to(root).as_posix(), "sha256": digest(fixture.candidate)},
            "candidate_maturity": {"path": fixture.candidate.relative_to(root).as_posix(), "sha256": digest(fixture.candidate)},
            "source_commit_receipt": {"path": fixture.preflight.relative_to(root).as_posix(), "sha256": digest(fixture.preflight)},
            "source_preflight": {"path": fixture.preflight.relative_to(root).as_posix(), "sha256": digest(fixture.preflight)},
            "package_sha256": fixture.package_sha,
            "package_tree_sha256": fixture.package_tree_sha,
            "tree_digest_algorithm": "daee-tree-sha256-v1",
            "input_registry": {"path": fixture.registry.relative_to(root).as_posix(), "sha256": digest(fixture.registry)},
            "review_protocol": {"path": fixture.protocol.relative_to(root).as_posix(), "sha256": digest(fixture.protocol)},
            "producer_model": "gpt-5.5",
            "producer_reasoning_effort": "high",
            "cold_review_model": "gpt-5.6-sol",
            "cold_review_reasoning_effort": "xhigh",
            "optional_opus_authorized": False,
            "paid_execution_authorized": True,
            "execution_lane": "producer",
            "execution_mode": "LIVE_CODEX",
            "test_only": False,
            "live_execution_authorized": True,
            "source_commit": fixture.source_commit,
            "branch": branch,
            "campaign_authorization": {"path": parent_path.relative_to(root).as_posix(), "sha256": digest(parent_path)},
            "campaign_authorization_sha256": digest(parent_path),
            "execution_tooling_manifest": matrix_tooling_ref,
            "cycle_id": "live-cycle-01",
            "launch_not_before": "2026-07-12T00:00:00Z",
            "launch_not_after": "2099-07-12T01:00:00Z",
            "expected_campaign_usage_sequence": initial_head["sequence"],
            "expected_campaign_usage_head_sha256": initial_head["head_sha256"],
            "case_inputs": case_inputs,
            "candidate_state_at_authorization": "READY_UNUSED",
            "candidate_claim_status_at_authorization": "UNCLAIMED",
            "candidate_package_root": "candidate/extracted",
            "model_runner": "codex",
            "resolved_model": "gpt-5.5",
            "adapter_version": "codex-live-v1",
            "host_application_version": "codex-cli 0.130.0-alpha.5",
            "codex_executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "provider_settings": {
                "response_surface": "package-faithful",
                "delivery_mode": "explicit-prompt-components",
                "effective_context_limit_bytes": 1000000,
                "command_timeout_seconds": command_timeout_seconds,
                "parallelism": 5,
                "fresh_context_per_case": True,
                "submit_before_observe": True,
                "observation_protocol": "concurrent-five-shared-deadline-v1",
                "sandbox": "read-only",
                "approval_policy": "never",
                "ignore_user_config": True,
                "ignore_rules": True,
                "ephemeral": True,
            },
            "cohort_size": 5,
            "cohort_protocol": "barrier-five-submit-before-await-v1",
            "case_ids": CASES,
            "isolated_root_prefix": "producer/isolated",
            "usage_ledger_root": "usage",
            "authorization_claim_path": "claims/producer-authorization.json",
            "candidate_claim_path": "claims/candidate.json",
            "observation_finalizer_path": "producer/observation-finalizer.json",
            "prompt_retention_root": "producer/prompts",
            "output_retention_root": "producer/raw-outputs",
            "provider_receipt_root": "producer/provider-receipts",
            "structural_evidence_root": "producer/structural-evidence",
        }
        matrix["authorization_sha256"] = record_sha256(matrix)
        matrix_path = root / "authorizations/matrix-live.json"
        write_json(matrix_path, matrix)
        return fixture, matrix_path, executable, skill_bytes

    def test_live_authorization_normalizes_pretty_mature_source_documents(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory() as temp:
            fixture, authorization, _executable, _skill_bytes = self._live_fixture(
                Path(temp),
                pretty_source_documents=True,
            )
            for path in (fixture.registry, fixture.protocol):
                self.assertNotEqual(path.read_bytes(), canonical(json.loads(path.read_bytes())))
            auth, _auth_sha = orchestrator._load_producer_authorization(
                fixture.root,
                authorization,
                allow_test_fixture=True,
            )
            bindings = orchestrator._validate_common_bindings(
                fixture.root,
                auth,
                allow_test_fixture=True,
            )
            self.assertEqual(bindings["registry_sha256"], digest(fixture.registry))
            self.assertEqual(bindings["protocol_sha256"], digest(fixture.protocol))

    def _live_preparation_inputs(
        self,
        root: Path,
    ) -> tuple[Fixture, dict[str, object], dict[str, object], object]:
        import reviewed_campaign_orchestrator as orchestrator

        fixture, authorization, executable, _skill_bytes = self._live_fixture(root)
        auth, auth_sha = orchestrator._load_producer_authorization(
            fixture.root,
            authorization,
            allow_test_fixture=True,
        )
        bindings = orchestrator._validate_common_bindings(
            fixture.root,
            auth,
            allow_test_fixture=True,
        )
        bindings["producer_output_contracts"] = orchestrator._producer_output_contracts(
            auth,
            auth_sha,
            bindings,
        )
        adapter = _ScriptedCodexTestAdapter(
            custody_root=fixture.root,
            codex_executable=executable,
            host=_ScriptedCodexHost(),
            command_timeout_seconds=30,
        )
        adapter.capability()
        return fixture, auth, bindings, adapter

    def _adapter_submission_fixture(
        self,
        root: Path,
        host: _ScriptedCodexHost,
        *,
        timeout: int = 30,
    ) -> tuple[object, dict[str, object], Path, Path]:
        import codex_live_producer_adapter as live_adapter

        executable = root / "bin/codex.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"bounded local adapter executable fixture\n")
        adapter = live_adapter.CodexLiveProducerAdapter(
            custody_root=root,
            codex_executable=executable,
            access_token="fixture-access-token-never-retain",
            host=host,
            command_timeout_seconds=timeout,
        )
        isolated_root = root / "isolated"
        isolated_identity = live_adapter._create_owned_directory(
            isolated_root,
            "adapter test isolation root",
            parents=False,
        )
        adapter._isolated_root_owner = (isolated_root, isolated_identity)
        worker_root = isolated_root / "producer-01"
        worker_identity = live_adapter._create_owned_directory(
            worker_root,
            "adapter test worker",
            parents=False,
        )
        adapter._owned_workers[worker_root] = worker_identity
        home = worker_root / "home"
        workspace = worker_root / "workspace"
        run_root = worker_root / "run"
        cache = worker_root / "cache"
        sqlite_home = worker_root / "sqlite"
        private_temp = worker_root / "temp"
        local_appdata = worker_root / "appdata/local"
        roaming_appdata = worker_root / "appdata/roaming"
        for directory in (home, workspace, run_root, cache, sqlite_home, private_temp, local_appdata, roaming_appdata):
            directory.mkdir(parents=True)
        runtime_reference = workspace / "references/runtime-core-routing.md"
        runtime_reference.parent.mkdir()
        runtime_reference.write_bytes(b"local no-network runtime fixture\n")
        prompt = root / "retained/prompt.md"
        retained_input = root / "retained/input.bin"
        runtime_context = root / "retained/runtime-context.json"
        package_parity = root / "retained/package-parity.json"
        prompt.parent.mkdir(parents=True)
        prompt.write_bytes(b"local no-network prompt fixture\n")
        retained_input.write_bytes(b"local input fixture\n")
        runtime_context.write_bytes(canonical({"schema": "local-runtime-context-v1"}))
        package_parity.write_bytes(canonical({"schema": "local-package-parity-v1"}))
        output_root = root / "raw-output"
        provider_root = root / "provider-receipts"
        capture_root = root / "capture"
        for directory in (output_root, provider_root, capture_root):
            directory.mkdir()
        case_id = CASES[0]
        output_contract = {"schema": "local-adapter-output-contract-v1"}
        capture_bindings: dict[str, object] = {}
        adapter._prepared[case_id] = {
            "case_id": case_id,
            "worker": "producer-01",
            "worker_root": worker_root,
            "worker_identity": worker_identity,
            "home": home,
            "workspace": workspace,
            "run_root": run_root,
            "cache": cache,
            "sqlite_home": sqlite_home,
            "temp": private_temp,
            "local_appdata": local_appdata,
            "roaming_appdata": roaming_appdata,
            "prompt": prompt,
            "input": retained_input,
            "runtime_context": runtime_context,
            "package_harness_parity": package_parity,
            "output_root": output_root,
            "provider_root": provider_root,
            "capture_root": capture_root,
            "capture_bindings": capture_bindings,
            "single_call_output_contract": output_contract,
            "candidate_id": "local-adapter-candidate",
            "source_commit": "2" * 40,
            "package_sha256": "3" * 64,
            "package_tree_sha256": "4" * 64,
            "command_timeout_seconds": timeout,
            "state": "NOT_SUBMITTED",
            "result": None,
            "started_at": None,
            "ended_at": None,
            "host_invocation_id": None,
            "launch_deadline_monotonic": None,
            "credential_scan_status": "PENDING",
            "credential_scan_evidence": None,
            "pre_admission_diagnostic": None,
        }
        adapter._ordered_cases = [case_id]
        execution_custody = {
            "case_id": case_id,
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "provider_settings": {
                "command_timeout_seconds": timeout,
                "observation_protocol": "concurrent-five-shared-deadline-v1",
            },
            "usage_reservation_sha256": "5" * 64,
            "single_call_output_contract": output_contract,
            "capture_bindings": capture_bindings,
        }
        return adapter, execution_custody, isolated_root, provider_root

    def _live_failure_replay_validation_inputs(
        self,
        root: Path,
        *,
        host_args: dict[str, object],
    ) -> tuple[object, Path, dict[str, object], dict[str, object], dict[str, object], str, dict[str, object]]:
        import reviewed_campaign_orchestrator as orchestrator

        fixture, authorization, executable, _skill_bytes = self._live_fixture(
            root,
            command_timeout_seconds=1,
        )
        adapter = _ScriptedCodexTestAdapter(
            custody_root=fixture.root,
            codex_executable=executable,
            host=_ScriptedCodexHost(**host_args),
            command_timeout_seconds=1,
        )
        with self.assertRaises(CampaignError):
            run_producer_cohort(
                fixture.root,
                authorization,
                adapter,
                allow_test_fixture=True,
            )
        incident_path = fixture.root / "incidents/producer-live-cycle-01.json"
        incident = json.loads(incident_path.read_text(encoding="utf-8"))
        payload = copy.deepcopy(incident["finalizer_payload"])
        auth, auth_sha = orchestrator._load_producer_authorization(
            fixture.root,
            authorization,
            require_active_window=False,
            allow_test_fixture=True,
        )
        bindings = orchestrator._validate_common_bindings(
            fixture.root,
            auth,
            allow_test_fixture=True,
        )
        bindings["producer_output_contracts"] = orchestrator._producer_output_contracts(
            auth,
            auth_sha,
            bindings,
        )
        return fixture, authorization, incident, payload, auth, auth_sha, bindings

    def _run_live_success(self, root: Path) -> tuple[Fixture, Path, dict[str, object]]:
        fixture, authorization, executable, _skill_bytes = self._live_fixture(root)
        adapter = _ScriptedCodexTestAdapter(
            custody_root=fixture.root,
            codex_executable=executable,
            host=_ScriptedCodexHost(),
            command_timeout_seconds=30,
        )
        completion = run_producer_cohort(
            fixture.root,
            authorization,
            adapter,
            allow_test_fixture=True,
        )
        return fixture, authorization, completion

    def _rewrite_first_capture(
        self,
        root: Path,
        completion: dict[str, object],
        *,
        mutation: str,
    ) -> dict[str, object]:
        updated = copy.deepcopy(completion)
        result = updated["results"][0]
        capture_path = root / result["capture_evidence"]["path"]
        capture = json.loads(capture_path.read_text(encoding="utf-8"))
        if mutation in {"raw-thread", "raw-usage"}:
            event_path = root / capture["raw_event_log"]["path"]
            events = [json.loads(line) for line in event_path.read_bytes().splitlines()]
            if mutation == "raw-thread":
                next(row for row in events if row.get("type") == "thread.started")["thread_id"] = "forged-thread-id"
            else:
                next(row for row in events if row.get("type") == "turn.completed")["usage"]["input_tokens"] = 11
            event_path.write_bytes(b"".join(canonical(row) for row in events))
            capture["raw_event_log"] = ref(root, event_path)
        elif mutation == "admission-prefix":
            admission_path = root / capture["in_flight_admission"]["path"]
            admission_path.write_bytes(
                canonical({"type": "thread.started", "thread_id": "forged-admission-thread"})
                + canonical({"type": "turn.started"})
            )
            capture["in_flight_admission"] = ref(root, admission_path)
        elif mutation == "host":
            capture["completion_identity"]["host_invocation_id"] = "codex-host:9999:gate88-secularism"
        elif mutation == "timestamp":
            capture["completion_identity"]["started_at"] = "2026-07-11T23:59:59Z"
        elif mutation == "cost":
            capture["cost"] = {"unit": "usd", "value": "1"}
        else:
            raise AssertionError(f"unknown capture mutation: {mutation}")
        write_json(capture_path, capture)
        result["capture_evidence"] = ref(root, capture_path)

        completion_path = root / "producer/completion.json"
        write_json(completion_path, updated)
        finalizer_path = root / "producer/observation-finalizer.json"
        finalizer = json.loads(finalizer_path.read_text(encoding="utf-8"))
        finalizer["observed_results"] = copy.deepcopy(updated["results"])
        finalizer["completion"] = ref(root, completion_path)
        write_json(finalizer_path, finalizer)
        return updated

    def _append_later_usage(self, root: Path, authorization: Path, *, outcome: str) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        matrix = json.loads(authorization.read_text(encoding="utf-8"))
        before = head_snapshot(root / "usage")
        later_authorization_sha = "d" * 64
        reservation = reserve(
            root / "usage",
            cohort="gpt-review",
            calls=5,
            expected_sequence=before["sequence"],
            expected_head_sha256=before["head_sha256"],
            campaign_authorization_sha256=matrix["campaign_authorization_sha256"],
            authorization_sha256=later_authorization_sha,
            candidate_id="later-candidate",
            cycle_or_review_batch_id="later-review-batch",
            call_subject_ids=CASES,
        )
        if outcome == "open":
            return
        if outcome == "resolved":
            receipts = orchestrator._not_dispatched_receipts(reservation)
            counts = {"completed": 0, "failed": 0, "cancelled": 0, "not_dispatched": 5, "unknown": 0}
            cost = {"unit": "usd", "value": "0"}
        elif outcome == "unresolved":
            receipts = orchestrator._unknown_receipts(reservation, positive_dispatch_evidence=False)
            counts = {"completed": 0, "failed": 0, "cancelled": 0, "not_dispatched": 0, "unknown": 5}
            cost = {"unit": "usd", "value": "unknown"}
        else:
            raise AssertionError(f"unknown later usage outcome: {outcome}")
        settle(
            root / "usage",
            reservation["transaction_sha256"],
            **counts,
            provider_usage_receipts=receipts,
            measured_cost=cost,
            candidate_id="later-candidate",
            authorization_sha256=later_authorization_sha,
        )

    def test_live_completion_revalidation_rederives_retained_provider_facts(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        expected_markers = {
            "raw-thread": "RAW_PROVIDER_ADMISSION",
            "raw-usage": "RAW_PROVIDER_USAGE",
            "admission-prefix": "RAW_PROVIDER_ADMISSION",
            "host": "RAW_HOST_IDENTITY",
            "timestamp": "DISPATCH_AUTHORIZATION_WINDOW",
            "cost": "RAW_PROVIDER_COST",
        }
        with tempfile.TemporaryDirectory(prefix="daee-live-revalidation-base-") as temp:
            base_root = Path(temp) / "base"
            base_root.mkdir()
            _fixture, authorization, completion = self._run_live_success(base_root)
            authorization_relative = authorization.relative_to(base_root)
            for mutation, marker in expected_markers.items():
                with self.subTest(mutation=mutation):
                    mutated_root = Path(temp) / mutation
                    shutil.copytree(base_root, mutated_root)
                    mutated = self._rewrite_first_capture(
                        mutated_root,
                        completion,
                        mutation=mutation,
                    )
                    with self.assertRaisesRegex(CampaignError, marker):
                        orchestrator.revalidate_live_producer_completion(
                            mutated_root,
                            mutated_root / authorization_relative,
                            mutated,
                            allow_test_fixture=True,
                        )

    def test_live_completion_revalidation_rejects_nonfinite_json_constants(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-live-nonfinite-revalidation-") as temp:
            base_root = Path(temp) / "base"
            base_root.mkdir()
            _fixture, authorization, completion = self._run_live_success(base_root)
            authorization_relative = authorization.relative_to(base_root)
            for literal in ("NaN", "Infinity", "-Infinity"):
                with self.subTest(literal=literal):
                    mutated_root = Path(temp) / literal.replace("-", "negative-")
                    shutil.copytree(base_root, mutated_root)
                    mutated = copy.deepcopy(completion)
                    result = mutated["results"][0]
                    capture_path = mutated_root / result["capture_evidence"]["path"]
                    capture = json.loads(capture_path.read_text(encoding="utf-8"))
                    event_path = mutated_root / capture["raw_event_log"]["path"]
                    lines = event_path.read_bytes().splitlines()
                    terminal_index = next(
                        index for index, line in enumerate(lines)
                        if b'"type":"turn.completed"' in line
                    )
                    lines[terminal_index] = (
                        lines[terminal_index][:-1]
                        + b',"nonfinite_probe":'
                        + literal.encode("ascii")
                        + b"}"
                    )
                    event_path.write_bytes(b"\n".join(lines) + b"\n")
                    capture["raw_event_log"] = ref(mutated_root, event_path)
                    write_json(capture_path, capture)
                    result["capture_evidence"] = ref(mutated_root, capture_path)
                    completion_path = mutated_root / "producer/completion.json"
                    write_json(completion_path, mutated)
                    finalizer_path = mutated_root / "producer/observation-finalizer.json"
                    finalizer = json.loads(finalizer_path.read_text(encoding="utf-8"))
                    finalizer["observed_results"] = copy.deepcopy(mutated["results"])
                    finalizer["completion"] = ref(mutated_root, completion_path)
                    write_json(finalizer_path, finalizer)

                    with self.assertRaisesRegex(CampaignError, "NONFINITE"):
                        orchestrator.revalidate_live_producer_completion(
                            mutated_root,
                            mutated_root / authorization_relative,
                            mutated,
                            allow_test_fixture=True,
                        )

    def test_historical_live_completion_uses_dispatch_window_not_current_clock(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator
        from codex_live_producer_adapter import CodexLiveProducerAdapter

        class FutureClock(datetime):
            @classmethod
            def now(cls, tz: timezone | None = None) -> datetime:
                value = cls(2100, 1, 1, tzinfo=timezone.utc)
                return value if tz is not None else value.replace(tzinfo=None)

        with tempfile.TemporaryDirectory(prefix="daee-live-historical-window-") as temp:
            fixture, authorization, completion = self._run_live_success(Path(temp))
            with mock.patch.object(orchestrator, "datetime", FutureClock):
                context = orchestrator.revalidate_live_producer_completion_context(
                    fixture.root,
                    authorization,
                    completion,
                    allow_test_fixture=True,
                )
            self.assertEqual(
                {"completion", "authorization", "authorization_sha256", "bindings", "producer_output_contracts"},
                set(context),
            )
            self.assertEqual(completion, context["completion"])
            self.assertEqual(CASES, list(context["producer_output_contracts"]))

            fresh_root = Path(temp) / "fresh-expired"
            fresh_root.mkdir()
            fresh_fixture, fresh_authorization, executable, _skill_bytes = self._live_fixture(fresh_root)
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fresh_fixture.root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            with mock.patch.object(orchestrator, "datetime", FutureClock):
                with self.assertRaisesRegex(CampaignError, "LIVE_AUTHORIZATION_WINDOW"):
                    run_producer_cohort(
                        fresh_fixture.root,
                        fresh_authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

    def test_historical_live_completion_accepts_settlement_ancestor_but_blocks_unsafe_head(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-live-usage-ancestor-") as temp:
            base_root = Path(temp) / "base"
            base_root.mkdir()
            _fixture, authorization, completion = self._run_live_success(base_root)
            authorization_relative = authorization.relative_to(base_root)

            resolved_root = Path(temp) / "resolved"
            shutil.copytree(base_root, resolved_root)
            self._append_later_usage(
                resolved_root,
                resolved_root / authorization_relative,
                outcome="resolved",
            )
            self.assertEqual(
                completion,
                orchestrator.revalidate_live_producer_completion(
                    resolved_root,
                    resolved_root / authorization_relative,
                    completion,
                    allow_test_fixture=True,
                ),
            )

            forged_root = Path(temp) / "forged-settlement-state"
            shutil.copytree(base_root, forged_root)
            forged_finalizer_path = forged_root / "producer/observation-finalizer.json"
            forged_finalizer = json.loads(forged_finalizer_path.read_text(encoding="utf-8"))
            forged_finalizer["usage_unresolved"] = True
            write_json(forged_finalizer_path, forged_finalizer)
            with self.assertRaisesRegex(CampaignError, "USAGE_HEAD"):
                orchestrator.revalidate_live_producer_completion(
                    forged_root,
                    forged_root / authorization_relative,
                    completion,
                    allow_test_fixture=True,
                )

            for outcome, marker in (("open", "OPEN_RESERVATION"), ("unresolved", "UNRESOLVED_USAGE")):
                with self.subTest(outcome=outcome):
                    unsafe_root = Path(temp) / outcome
                    shutil.copytree(base_root, unsafe_root)
                    self._append_later_usage(
                        unsafe_root,
                        unsafe_root / authorization_relative,
                        outcome=outcome,
                    )
                    with self.assertRaisesRegex(CampaignError, marker):
                        orchestrator.revalidate_live_producer_completion(
                            unsafe_root,
                            unsafe_root / authorization_relative,
                            completion,
                            allow_test_fixture=True,
                        )

    def test_live_adapter_uses_schema_owned_child_private_candidate_bytes_and_five_start_barrier(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-producer-") as temp:
            fixture, authorization, executable, skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )
            completion = run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
            import reviewed_campaign_orchestrator as orchestrator
            self.assertEqual(
                completion,
                orchestrator.revalidate_live_producer_completion(
                    fixture.root,
                    authorization,
                    completion,
                    allow_test_fixture=True,
                ),
            )
            first_observe = next(index for index, row in enumerate(host.log) if row[0] == "observe")
            self.assertEqual(5, sum(row[0] == "start" for row in host.log[:first_observe]))
            self.assertEqual(5, len(host.starts))
            self.assertEqual("PRODUCER_CAPTURE_COMPLETE", completion["status"])
            for result in completion["results"]:
                capture_path = fixture.root / result["capture_evidence"]["path"]
                capture = json.loads(capture_path.read_text(encoding="utf-8"))
                admission = fixture.root / capture["in_flight_admission"]["path"]
                events = fixture.root / capture["raw_event_log"]["path"]
                admission_raw = admission.read_bytes()
                self.assertTrue(events.read_bytes().startswith(admission_raw))
                self.assertIn(b'"type":"thread.started"', admission_raw)
                self.assertNotIn(b'"type":"turn.completed"', admission_raw)
            for index, start in enumerate(host.starts):
                command = start["command"]
                self.assertIn("--json", command)
                self.assertIn("--ignore-user-config", command)
                self.assertIn("--ignore-rules", command)
                self.assertIn("--ephemeral", command)
                self.assertIn('model_reasoning_effort="high"', command)
                self.assertNotIn("fixture-access-token-never-retain", " ".join(command))
                self.assertEqual(Path(str(start["cwd"])), Path(start["env"]["CODEX_HOME"]).parent / "workspace")
                self.assertEqual(start["env"]["CODEX_HOME"], start["env"]["HOME"])
                worker_root = Path(str(start["cwd"])).parent
                for field in ("TEMP", "TMP", "LOCALAPPDATA", "APPDATA", "XDG_CACHE_HOME"):
                    self.assertTrue(Path(start["env"][field]).is_relative_to(worker_root), field)
                self.assertEqual(
                    (ROOT / "skill/references/runtime-core-routing.md").read_bytes(),
                    start["runtime_core_routing"],
                )
                self.assertIn(skill_bytes, start["prompt"])
                self.assertIn(CASES[index].encode(), start["prompt"])
            retained = b"\n".join(path.read_bytes() for path in fixture.root.rglob("*") if path.is_file())
            self.assertNotIn(b"fixture-access-token-never-retain", retained)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(5, head["totals"]["completed"])
            authorization_raw_sha = digest(authorization)
            reservation = json.loads(
                (
                    fixture.root
                    / "usage/transactions"
                    / f"{completion['reservation_sha256']}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(authorization_raw_sha, reservation["authorization_sha256"])
            self.assertEqual(5, len(reservation["call_contract"]))
            matrix_authorization = json.loads(authorization.read_text(encoding="utf-8"))
            self.assertEqual(30, matrix_authorization["provider_settings"]["command_timeout_seconds"])
            changed_timeout = copy.deepcopy(matrix_authorization)
            changed_timeout["provider_settings"]["command_timeout_seconds"] = 31
            changed_timeout["authorization_sha256"] = record_sha256(changed_timeout)
            self.assertNotEqual(
                authorization_raw_sha,
                hashlib.sha256(canonical(changed_timeout)).hexdigest(),
            )
            settlement = json.loads((fixture.root / "usage/transactions" / f"{completion['settlement_sha256']}.json").read_text())
            self.assertEqual(
                {"unit": "usd", "value": "unknown", "status": "UNAVAILABLE", "reason": "provider-cost-not-present-in-retained-jsonl", "source": "codex-cli-jsonl-v1"},
                settlement["measured_cost"],
            )
            self.assertTrue(all(row["accepted"] is None and row["in_flight"] is False and row["acknowledgment_origin"] == "ADAPTER_IN_FLIGHT" for row in settlement["provider_usage_receipts"]))
            contradictory = copy.deepcopy(settlement["provider_usage_receipts"])
            contradictory[0]["in_flight"] = True
            with self.assertRaisesRegex(ValueError, "clear adapter in-flight state"):
                _provider_facts(
                    contradictory,
                    candidate_id=settlement["candidate_id"],
                    batch_id=settlement["cycle_or_review_batch_id"],
                    cohort=settlement["cohort"],
                    reserved_calls=settlement["reserved_calls"],
                    call_contract=settlement["call_contract"],
                    paired_opus_contract=settlement.get("paired_opus_contract"),
                    paired_parent_contract=settlement.get("paired_parent_contract"),
                )
            invalid_cached = copy.deepcopy(settlement["provider_usage_receipts"])
            invalid_cached[0]["usage"]["cached_input_tokens"] = 11
            with self.assertRaisesRegex(ValueError, "cached token usage"):
                _provider_facts(
                    invalid_cached,
                    candidate_id=settlement["candidate_id"],
                    batch_id=settlement["cycle_or_review_batch_id"],
                    cohort=settlement["cohort"],
                    reserved_calls=settlement["reserved_calls"],
                    call_contract=settlement["call_contract"],
                    paired_opus_contract=settlement.get("paired_opus_contract"),
                    paired_parent_contract=settlement.get("paired_parent_contract"),
                )
            invalid_cost = copy.deepcopy(settlement["provider_usage_receipts"])
            invalid_cost[0]["cost"].pop("reason")
            with self.assertRaisesRegex(ValueError, "exact usd cost custody"):
                _provider_facts(
                    invalid_cost,
                    candidate_id=settlement["candidate_id"],
                    batch_id=settlement["cycle_or_review_batch_id"],
                    cohort=settlement["cohort"],
                    reserved_calls=settlement["reserved_calls"],
                    call_contract=settlement["call_contract"],
                    paired_opus_contract=settlement.get("paired_opus_contract"),
                    paired_parent_contract=settlement.get("paired_parent_contract"),
                )
            for result in completion["results"]:
                evidence = json.loads((fixture.root / result["capture_evidence"]["path"]).read_text())
                execution_custody = json.loads(
                    (fixture.root / evidence["execution_custody"]["path"]).read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(
                    30,
                    execution_custody["provider_settings"]["command_timeout_seconds"],
                )
                self.assertEqual("CAPTURED", evidence["status"])
                self.assertEqual("UNVERIFIED", evidence["structural_status"])
                self.assertIsNone(evidence["stage01_stage08_evidence"])
                self.assertNotIn("source_file_locators", evidence)
                self.assertEqual({"status": "RECORDED", "input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 20, "total_tokens": 30}, evidence["usage"])
                scan_ref = evidence["credential_residue_scan"]
                scan = json.loads((fixture.root / scan_ref["path"]).read_text())
                self.assertEqual("PASS", scan["status"])
                self.assertEqual(["utf-8", "utf-16-le", "utf-16-be"], scan["encoding_forms_checked"])
                for role, prefix in (("prompt", "producer/prompts/"), ("raw_output", "producer/raw-outputs/"), ("raw_event_log", "producer/provider-receipts/"), ("stderr", "producer/provider-receipts/")):
                    self.assertTrue(evidence[role]["path"].startswith(prefix), (role, evidence[role]))
                self.assertTrue(result["provider_receipt"]["path"].startswith("producer/provider-receipts/"))
                for retained_ref in (result["capture_evidence"], result["provider_receipt"], evidence["prompt"], evidence["raw_output"], evidence["raw_event_log"], evidence["stderr"], scan_ref):
                    retained_path = fixture.root / retained_ref["path"]
                    self.assertEqual(retained_ref["byte_count"], len(retained_path.read_bytes()))
                    self.assertEqual(retained_ref["sha256"], digest(retained_path))
            self.assertEqual(fixture.package_sha, completion["package_sha256"])
            self.assertEqual(fixture.package_tree_sha, completion["package_tree_sha256"])
            finalizer = json.loads((fixture.root / "producer/observation-finalizer.json").read_text())
            self.assertEqual(digest(fixture.root / "producer/completion.json"), finalizer["completion"]["sha256"])
            self.assertFalse((fixture.root / "producer/isolated").exists())

    def test_live_usage_reservation_set_contains_exactly_five_case_bound_members(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-reservation-set-") as temp:
            fixture, authorization, completion = self._run_live_success(Path(temp))
            matrix = json.loads(authorization.read_text(encoding="utf-8"))
            reservation = json.loads(
                (
                    fixture.root
                    / "usage/transactions"
                    / f"{completion['reservation_sha256']}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("campaign-usage-transaction-v2", reservation["schema"])
            self.assertEqual("reservation-set", reservation["kind"])
            members = reservation["reservation_members"]
            self.assertEqual(5, len(members))
            self.assertEqual(5, len({row["reservation_sha256"] for row in members}))
            self.assertEqual(
                [row["reservation_sha256"] for row in members],
                completion["producer_usage_reservation_sha256s"],
            )
            expected_keys = {
                "schema", "reservation_ordinal", "campaign_authorization_sha256",
                "matrix_authorization_sha256", "authorization_sha256", "candidate_id",
                "candidate_maturity_sha256", "candidate_record_sha256", "source_commit",
                "package_sha256", "package_tree_sha256", "execution_tooling_manifest_sha256",
                "cycle_or_review_batch_id", "cohort", "case_id", "subject_id", "input_sha256",
                "model", "reasoning_effort", "cohort_deadline_utc", "worker_timeout_seconds",
                "worker_deadline_rule", "observation_protocol", "reservation_sha256",
            }
            for index, (member, case_input, call_contract) in enumerate(
                zip(members, matrix["case_inputs"], reservation["call_contract"]),
                1,
            ):
                self.assertEqual(expected_keys, set(member))
                self.assertEqual(index, member["reservation_ordinal"])
                self.assertEqual(matrix["campaign_authorization_sha256"], member["campaign_authorization_sha256"])
                self.assertEqual(matrix["authorization_sha256"], member["matrix_authorization_sha256"])
                self.assertEqual(digest(authorization), member["authorization_sha256"])
                self.assertEqual(matrix["candidate_id"], member["candidate_id"])
                self.assertEqual(matrix["candidate_maturity"]["sha256"], member["candidate_maturity_sha256"])
                self.assertEqual(matrix["candidate_record"]["sha256"], member["candidate_record_sha256"])
                self.assertEqual(matrix["source_commit"], member["source_commit"])
                self.assertEqual(matrix["package_sha256"], member["package_sha256"])
                self.assertEqual(matrix["package_tree_sha256"], member["package_tree_sha256"])
                self.assertEqual(matrix["execution_tooling_manifest"]["sha256"], member["execution_tooling_manifest_sha256"])
                self.assertEqual(matrix["cycle_id"], member["cycle_or_review_batch_id"])
                self.assertEqual("gpt-producer", member["cohort"])
                self.assertEqual(case_input["case_id"], member["case_id"])
                self.assertEqual(f"producer:{case_input['case_id']}", member["subject_id"])
                self.assertEqual(case_input["input_sha256"], member["input_sha256"])
                self.assertEqual("gpt-5.5", member["model"])
                self.assertEqual("high", member["reasoning_effort"])
                self.assertEqual(matrix["launch_not_after"], member["cohort_deadline_utc"])
                self.assertEqual(30, member["worker_timeout_seconds"])
                self.assertEqual("min(worker-start-plus-timeout,cohort-deadline)", member["worker_deadline_rule"])
                self.assertEqual("concurrent-five-shared-deadline-v1", member["observation_protocol"])
                unsigned = {key: value for key, value in member.items() if key != "reservation_sha256"}
                expected_sha = hashlib.sha256(
                    b"daee-campaign-usage-reservation-member-v1\0" + canonical(unsigned)
                ).hexdigest()
                self.assertEqual(expected_sha, member["reservation_sha256"])
                self.assertEqual(member["reservation_sha256"], call_contract["usage_reservation_sha256"])

    def test_live_uppercase_registry_hashes_use_lowercase_execution_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-uppercase-registry-hashes-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(
                Path(temp),
                uppercase_registry_hashes=True,
            )
            registry = json.loads(fixture.registry.read_text(encoding="utf-8"))
            matrix = json.loads(authorization.read_text(encoding="utf-8"))
            self.assertTrue(all(row["raw_sha256"] == row["raw_sha256"].upper() for row in registry["cases"]))
            self.assertEqual(
                [row["raw_sha256"].lower() for row in registry["cases"]],
                [row["input_sha256"] for row in matrix["case_inputs"]],
            )

            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            completion = run_producer_cohort(
                fixture.root,
                authorization,
                adapter,
                allow_test_fixture=True,
            )
            reservation = json.loads(
                (
                    fixture.root
                    / "usage/transactions"
                    / f"{completion['reservation_sha256']}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                [row["input_sha256"] for row in matrix["case_inputs"]],
                [row["input_sha256"] for row in reservation["reservation_members"]],
            )
            for result, expected in zip(completion["results"], matrix["case_inputs"]):
                capture = json.loads(
                    (fixture.root / result["capture_evidence"]["path"]).read_text(encoding="utf-8")
                )
                custody = json.loads(
                    (fixture.root / capture["execution_custody"]["path"]).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    expected["input_sha256"],
                    custody["single_call_output_contract"]["input_binding"]["sha256"],
                )

    def test_live_post_observation_failure_terminalizes_unreported_cost_exactly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-observed-failure-cost-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(
                CampaignError,
                r"^INJECTED_TERMINAL_PHASE_FAILURE: after-observation-validation$",
            ):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                    fault_at="after-observation-validation",
                )

            head = validate_head(fixture.root / "usage")
            self.assertEqual(5, head["totals"]["completed"])
            self.assertEqual(5, head["totals"]["producer_invocations"])
            self.assertFalse(head["open_reservations"])
            self.assertFalse(head["unresolved_usage"])
            terminal = json.loads(
                (
                    fixture.root
                    / "usage/transactions"
                    / f"{head['last_transaction_sha256']}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("settlement-set", terminal["kind"])
            self.assertEqual(
                {
                    "unit": "usd",
                    "value": "unknown",
                    "status": "UNAVAILABLE",
                    "reason": "provider-cost-not-present-in-retained-jsonl",
                    "source": "codex-cli-jsonl-v1",
                },
                terminal["measured_cost"],
            )
            member_shas = [
                row["reservation_sha256"] for row in terminal["reservation_members"]
            ]
            self.assertEqual(
                member_shas,
                [row["usage_reservation_sha256"] for row in terminal["provider_usage_receipts"]],
            )
            incident = json.loads(
                (fixture.root / "incidents/producer-live-cycle-01.json").read_text(encoding="utf-8")
            )
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
            )
            self.assertEqual("after-observation-validation", incident["failure_phase"])
            self.assertEqual(member_shas, incident["producer_usage_reservation_sha256s"])
            self.assertEqual(member_shas, finalizer["producer_usage_reservation_sha256s"])
            self.assertEqual(5, len(finalizer["observed_results"]))
            self.assertEqual("OBSERVED", finalizer["dispatch_classification"])
            self.assertFalse(finalizer["usage_unresolved"])
            self.assertTrue(finalizer["terminal"])

    def test_live_result_and_receipt_publication_failures_close_all_completed_usage(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        scenarios = [
            (index, role_kind, f"producer_{role_kind}_{index}")
            for index in range(1, 6)
            for role_kind in ("result", "provider_receipt")
        ]
        for index, role_kind, target_role in scenarios:
            expected_phase = "result-publication" if role_kind == "result" else "provider-receipt-publication"
            with self.subTest(index=index, role_kind=role_kind), tempfile.TemporaryDirectory(
                prefix=f"daee-live-{role_kind}-publication-{index}-"
            ) as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
                host = _ScriptedCodexHost()
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=host,
                    command_timeout_seconds=30,
                )
                original = orchestrator._publish_once_bytes

                def fail_selected_publication(
                    root: Path,
                    relative: str,
                    raw: bytes,
                    role: str,
                ) -> dict[str, object]:
                    if role == target_role:
                        raise OSError(f"injected {role} publication failure")
                    return original(root, relative, raw, role)

                with mock.patch.object(
                    orchestrator,
                    "_publish_once_bytes",
                    side_effect=fail_selected_publication,
                ):
                    with self.assertRaisesRegex(
                        CampaignError,
                        rf"CAMPAIGN_TERMINALIZATION_FAILED\[{expected_phase}\]",
                    ):
                        run_producer_cohort(
                            fixture.root,
                            authorization,
                            adapter,
                            allow_test_fixture=True,
                        )

                head = validate_head(fixture.root / "usage")
                self.assertEqual(5, head["totals"]["completed"])
                self.assertEqual(5, head["totals"]["producer_invocations"])
                self.assertFalse(head["open_reservations"])
                self.assertFalse(head["unresolved_usage"])
                finalizer = json.loads(
                    (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
                )
                self.assertEqual(expected_phase, finalizer["failure_phase"])
                self.assertEqual("OBSERVED", finalizer["dispatch_classification"])
                self.assertEqual("CONSUMED_OBSERVED", finalizer["candidate_status"])
                self.assertEqual(5, len(finalizer["observed_results"]))
                failed_projections = [
                    row
                    for row in finalizer["observed_results"]
                    if row.get("projection_status") == "FAILED"
                ]
                self.assertEqual(6 - index, len(failed_projections))
                for row in failed_projections:
                    capture = json.loads(
                        (fixture.root / row["capture_evidence"]["path"]).read_text(encoding="utf-8")
                    )
                    self.assertEqual(capture["raw_output"], row["output"])
                    self.assertIsNone(row["provider_receipt"])
                replay_host = _ScriptedCodexHost()
                replay_adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=replay_host,
                    command_timeout_seconds=30,
                )
                with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        replay_adapter,
                        allow_test_fixture=True,
                    )
                self.assertEqual([], replay_host.starts)

    def test_live_mixed_outcome_projection_failures_settle_and_replay_exactly(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        for role_kind, target_role in (
            ("result", "producer_result_1"),
            ("provider_receipt", "producer_provider_receipt_1"),
        ):
            expected_phase = (
                "result-publication"
                if role_kind == "result"
                else "provider-receipt-publication"
            )
            with self.subTest(role_kind=role_kind), tempfile.TemporaryDirectory(
                prefix=f"daee-live-mixed-{role_kind}-publication-"
            ) as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
                host = _ScriptedCodexHost(nonzero_at=3)
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=host,
                    command_timeout_seconds=30,
                )
                original = orchestrator._publish_once_bytes

                def fail_selected_publication(
                    root: Path,
                    relative: str,
                    raw: bytes,
                    role: str,
                ) -> dict[str, object]:
                    if role == target_role:
                        raise OSError(f"injected mixed-state {role} publication failure")
                    return original(root, relative, raw, role)

                with mock.patch.object(
                    orchestrator,
                    "_publish_once_bytes",
                    side_effect=fail_selected_publication,
                ):
                    with self.assertRaisesRegex(
                        CampaignError,
                        rf"CAMPAIGN_TERMINALIZATION_FAILED\[{expected_phase}\]",
                    ):
                        run_producer_cohort(
                            fixture.root,
                            authorization,
                            adapter,
                            allow_test_fixture=True,
                        )

                head = validate_head(fixture.root / "usage")
                self.assertEqual(4, head["totals"]["completed"])
                self.assertEqual(1, head["totals"]["unknown"])
                self.assertEqual(5, head["totals"]["producer_invocations"])
                self.assertFalse(head["open_reservations"])
                self.assertTrue(head["unresolved_usage"])
                finalizer = json.loads(
                    (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
                )
                self.assertEqual(expected_phase, finalizer["failure_phase"])
                self.assertEqual("OUTCOME_UNKNOWN", finalizer["dispatch_classification"])
                self.assertEqual("CONSUMED_DISPATCH_UNKNOWN", finalizer["candidate_status"])
                self.assertEqual(4, len(finalizer["observed_results"]))
                self.assertTrue(
                    all(
                        row.get("projection_status") == "FAILED"
                        for row in finalizer["observed_results"]
                    )
                )

                replay_host = _ScriptedCodexHost()
                replay_adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=replay_host,
                    command_timeout_seconds=30,
                )
                with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        replay_adapter,
                        allow_test_fixture=True,
                    )
                self.assertEqual([], replay_host.starts)

    def test_live_result_and_receipt_collisions_preserve_foreign_bytes_and_terminalize(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        for collision_kind in ("result", "provider_receipt"):
            with self.subTest(collision_kind=collision_kind), tempfile.TemporaryDirectory(
                prefix=f"daee-live-{collision_kind}-collision-"
            ) as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
                foreign = b"foreign create-once collision bytes\n"
                original = orchestrator._publish_once_bytes
                if collision_kind == "result":
                    collision_path = fixture.root / f"producer/results/{CASES[0]}.txt"
                    collision_path.parent.mkdir(parents=True, exist_ok=True)
                    collision_path.write_bytes(foreign)
                    publication = mock.patch.object(
                        orchestrator,
                        "_publish_once_bytes",
                        side_effect=original,
                    )
                else:
                    collision_path = None

                    def collide_with_receipt(
                        root: Path,
                        relative: str,
                        raw: bytes,
                        role: str,
                    ) -> dict[str, object]:
                        nonlocal collision_path
                        if role == "producer_provider_receipt_1":
                            collision_path = root / relative
                            collision_path.parent.mkdir(parents=True, exist_ok=True)
                            collision_path.write_bytes(foreign)
                        return original(root, relative, raw, role)

                    publication = mock.patch.object(
                        orchestrator,
                        "_publish_once_bytes",
                        side_effect=collide_with_receipt,
                    )
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=_ScriptedCodexHost(),
                    command_timeout_seconds=30,
                )
                with publication:
                    with self.assertRaisesRegex(CampaignError, "CAMPAIGN_TERMINALIZATION_FAILED"):
                        run_producer_cohort(
                            fixture.root,
                            authorization,
                            adapter,
                            allow_test_fixture=True,
                        )
                self.assertIsNotNone(collision_path)
                self.assertEqual(foreign, collision_path.read_bytes())
                head = validate_head(fixture.root / "usage")
                self.assertEqual(5, head["totals"]["completed"])
                self.assertFalse(head["open_reservations"])
                self.assertFalse(head["unresolved_usage"])
                finalizer = json.loads(
                    (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
                )
                self.assertEqual("OBSERVED", finalizer["dispatch_classification"])
                self.assertEqual(5, len(finalizer["observed_results"]))

    def test_live_concurrent_observation_interface_is_required_before_claim_or_reservation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-observe-many-required-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )
            adapter.observe_many = None  # type: ignore[method-assign]
            before = head_snapshot(fixture.root / "usage")
            with self.assertRaisesRegex(CampaignError, "LIVE_PROVIDER_CONCURRENT_OBSERVATION_UNAVAILABLE"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual(before, head_snapshot(fixture.root / "usage"))
            self.assertEqual([], host.starts)
            self.assertFalse((fixture.root / "claims/producer-authorization.json").exists())
            self.assertFalse((fixture.root / "claims/candidate.json").exists())
            self.assertFalse((fixture.root / "producer/isolated").exists())

    def test_live_terminal_observation_enters_all_five_waits_before_any_can_complete(self) -> None:
        class ConcurrentObservationHost(_ScriptedCodexHost):
            def __init__(self) -> None:
                super().__init__()
                self.observation_entries = 0
                self.maximum_observation_entries = 0
                self._observation_lock = threading.Lock()
                self._all_observers_entered = threading.Event()

            def start(self, *args: object, **kwargs: object) -> _CompletedCodexProcess:
                process = super().start(*args, **kwargs)
                original_wait = process.wait

                def wait(timeout: float | None = None) -> int:
                    with self._observation_lock:
                        self.observation_entries += 1
                        self.maximum_observation_entries = max(
                            self.maximum_observation_entries,
                            self.observation_entries,
                        )
                        if self.observation_entries == 5:
                            self._all_observers_entered.set()
                    if not self._all_observers_entered.wait(timeout=2):
                        raise RuntimeError("terminal observation was serialized")
                    try:
                        return original_wait(timeout)
                    finally:
                        with self._observation_lock:
                            self.observation_entries -= 1

                process.wait = wait  # type: ignore[method-assign]
                return process

        with tempfile.TemporaryDirectory(prefix="daee-live-concurrent-observation-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = ConcurrentObservationHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )
            completion = run_producer_cohort(
                fixture.root,
                authorization,
                adapter,
                allow_test_fixture=True,
            )
            self.assertEqual(5, host.maximum_observation_entries)
            self.assertEqual("PRODUCER_CAPTURE_COMPLETE", completion["status"])
            self.assertEqual(
                "concurrent-five-shared-deadline-v1",
                json.loads(authorization.read_text(encoding="utf-8"))["provider_settings"]["observation_protocol"],
            )
            self.assertFalse((fixture.root / "producer/isolated").exists())

    def test_completed_waits_do_not_expire_during_serial_retention(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-post-wait-deadline-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            original_wait = adapter._inner._wait_for_terminal_process

            def expire_after_terminal(row: dict[str, object]) -> int:
                returncode = original_wait(row)
                row["launch_deadline_monotonic"] = time.monotonic() - 1
                return returncode

            adapter._inner._wait_for_terminal_process = expire_after_terminal
            completion = run_producer_cohort(
                fixture.root,
                authorization,
                adapter,
                allow_test_fixture=True,
            )
            self.assertEqual("PRODUCER_CAPTURE_COMPLETE", completion["status"])
            self.assertEqual(5, len(completion["results"]))
            self.assertFalse((fixture.root / "producer/isolated").exists())

    def test_tail_workers_are_all_started_before_any_tail_admission_wait(self) -> None:
        class TailAdmissionBarrierHost(_ScriptedCodexHost):
            def __init__(self) -> None:
                super().__init__()
                self.withheld: list[tuple[Path, bytes]] = []

            def start(self, *args: object, **kwargs: object) -> _CompletedCodexProcess:
                process = super().start(*args, **kwargs)
                event_log_path = kwargs["event_log_path"]
                assert isinstance(event_log_path, Path)
                ordinal = len(self.starts)
                if 2 <= ordinal < 5:
                    self.withheld.append((event_log_path, event_log_path.read_bytes()))
                    event_log_path.write_bytes(b"")
                elif ordinal == 5:
                    for path, raw in self.withheld:
                        path.write_bytes(raw)
                return process

        with tempfile.TemporaryDirectory(prefix="daee-live-tail-admission-barrier-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = TailAdmissionBarrierHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )
            completion = run_producer_cohort(
                fixture.root,
                authorization,
                adapter,
                allow_test_fixture=True,
            )
            first_observe = next(index for index, row in enumerate(host.log) if row[0] == "observe")
            self.assertEqual(5, sum(row[0] == "start" for row in host.log[:first_observe]))
            dispatch_events = completion["dispatch_manifest"]["events"]
            tail_submit_positions = [
                index
                for index, row in enumerate(dispatch_events)
                if row["event"] == "request_submit_started" and row.get("worker") != "producer-01"
            ]
            tail_admission_positions = [
                index
                for index, row in enumerate(dispatch_events)
                if row["event"] == "call_entered_in_flight" and row.get("worker") != "producer-01"
            ]
            self.assertEqual((4, 4), (len(tail_submit_positions), len(tail_admission_positions)))
            self.assertLess(max(tail_submit_positions), min(tail_admission_positions))
            self.assertEqual("PRODUCER_CAPTURE_COMPLETE", completion["status"])

    def test_live_prepare_requires_exclusive_absent_isolation_root_and_preserves_sentinel(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-existing-root-") as temp:
            fixture, auth, bindings, adapter = self._live_preparation_inputs(Path(temp))
            isolated_root = fixture.root / auth["isolated_root_prefix"]
            isolated_root.mkdir(parents=True)
            sentinel = isolated_root / "preexisting-sentinel.txt"
            sentinel.write_bytes(b"foreign custody must survive\n")

            with self.assertRaises(FileExistsError):
                adapter.prepare(auth, bindings, allow_test_fixture=True)

            self.assertEqual(b"foreign custody must survive\n", sentinel.read_bytes())
            self.assertTrue(isolated_root.is_dir())

    def test_live_prepare_midflight_worker_collision_preserves_foreign_path_and_fails_closed(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-worker-collision-") as temp:
            fixture, auth, bindings, adapter = self._live_preparation_inputs(Path(temp))
            isolated_root = fixture.root / auth["isolated_root_prefix"]
            collision = isolated_root / "producer-02"
            sentinel = collision / "foreign-sentinel.txt"
            original_copy = live_adapter._copy_tree_exact

            def inject_collision(source: Path, destination: Path) -> None:
                original_copy(source, destination)
                if destination.parent.name == "producer-01":
                    collision.mkdir()
                    sentinel.write_bytes(b"mid-prepare foreign custody\n")

            with mock.patch.object(live_adapter, "_copy_tree_exact", side_effect=inject_collision):
                with self.assertRaisesRegex(RuntimeError, "OWNED_ISOLATION_CLEANUP_FAILED_CLOSED"):
                    adapter.prepare(auth, bindings, allow_test_fixture=True)

            self.assertFalse((isolated_root / "producer-01").exists())
            self.assertEqual(b"mid-prepare foreign custody\n", sentinel.read_bytes())
            self.assertTrue(isolated_root.is_dir())

    def test_live_prepare_same_name_replacements_are_preserved_and_fail_closed(self) -> None:
        import codex_live_producer_adapter as live_adapter

        for replacement_kind in ("worker", "root"):
            with self.subTest(replacement_kind=replacement_kind), tempfile.TemporaryDirectory(
                prefix=f"daee-live-{replacement_kind}-replacement-"
            ) as temp:
                fixture, auth, bindings, adapter = self._live_preparation_inputs(Path(temp))
                isolated_root = fixture.root / auth["isolated_root_prefix"]
                replacement: Path | None = None
                sentinel: Path | None = None
                original_copy = live_adapter._copy_tree_exact

                def replace_then_fail(source: Path, destination: Path) -> None:
                    nonlocal replacement, sentinel
                    original_copy(source, destination)
                    replacement = destination.parent if replacement_kind == "worker" else isolated_root
                    shutil.rmtree(replacement)
                    replacement.mkdir(parents=True)
                    sentinel = replacement / "replacement-sentinel.txt"
                    sentinel.write_bytes(f"{replacement_kind} replacement custody\n".encode())
                    raise RuntimeError("injected failure after same-name replacement")

                with mock.patch.object(live_adapter, "_copy_tree_exact", side_effect=replace_then_fail):
                    with self.assertRaisesRegex(RuntimeError, "OWNED_ISOLATION_CLEANUP_FAILED_CLOSED"):
                        adapter.prepare(auth, bindings, allow_test_fixture=True)

                self.assertIsNotNone(replacement)
                self.assertIsNotNone(sentinel)
                self.assertEqual(
                    f"{replacement_kind} replacement custody\n".encode(),
                    sentinel.read_bytes(),
                )
                self.assertTrue(replacement.is_dir())

    def test_live_credential_cleanup_preserves_replaced_worker_and_fails_closed(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-cleanup-replacement-") as temp:
            _fixture, auth, bindings, adapter = self._live_preparation_inputs(Path(temp))
            adapter.prepare(auth, bindings, allow_test_fixture=True)
            adapter._token()
            row = adapter._prepared[CASES[0]]
            worker_root = row["worker_root"]
            sentinel = worker_root / "replacement-sentinel.txt"

            def replace_before_cleanup(_worker_root: Path, _credential: str) -> dict[str, int]:
                shutil.rmtree(worker_root)
                worker_root.mkdir()
                sentinel.write_bytes(b"credential cleanup replacement custody\n")
                raise OSError("injected scan failure after worker replacement")

            with mock.patch.object(
                live_adapter,
                "_scan_private_worker_for_credential",
                side_effect=replace_before_cleanup,
            ):
                with self.assertRaisesRegex(RuntimeError, "OWNED_WORKER_CLEANUP_FAILED_CLOSED"):
                    adapter._credential_readback(row)

            self.assertEqual(b"credential cleanup replacement custody\n", sentinel.read_bytes())
            self.assertTrue(worker_root.is_dir())

    def test_live_package_tree_check_cannot_be_bypassed_as_a_nonfixture(self) -> None:
        import codex_live_producer_adapter as live_adapter
        from reviewed_campaign_orchestrator import (
            _load_producer_authorization,
            _producer_output_contracts,
            _validate_common_bindings,
        )
        with tempfile.TemporaryDirectory(prefix="daee-live-package-binding-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            auth, auth_sha = _load_producer_authorization(
                fixture.root,
                authorization,
                allow_test_fixture=True,
            )
            bindings = _validate_common_bindings(fixture.root, auth, allow_test_fixture=True)
            bindings["producer_output_contracts"] = _producer_output_contracts(auth, auth_sha, bindings)
            adapter = live_adapter.CodexLiveProducerAdapter(
                custody_root=fixture.root, codex_executable=executable,
                access_token="fixture-access-token-never-retain", host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            adapter.capability()
            with self.assertRaisesRegex(ValueError, "candidate package tree differs from authorization"):
                adapter.prepare({**auth, "package_tree_sha256": "f" * 64}, bindings, allow_test_fixture=False)
            self.assertFalse((fixture.root / "producer/isolated").exists())

    def test_fixture_flag_rejects_paid_live_adapter_before_authorization_read(self) -> None:
        from codex_live_producer_adapter import CodexLiveProducerAdapter

        with tempfile.TemporaryDirectory(prefix="daee-live-paid-fixture-escape-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = CodexLiveProducerAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                access_token="fixture-access-token-never-retain",
                host=host,
            )

            with self.assertRaisesRegex(CampaignError, "TEST_FIXTURE_PAID_PROVIDER_FORBIDDEN"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            self.assertEqual([("probe", executable.name)], host.log)
            self.assertFalse((fixture.root / "claims").exists())
            self.assertFalse((fixture.root / "usage").exists())

    def test_paid_live_path_rejects_checkout_bytecode_before_authorization_read(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator
        from codex_live_producer_adapter import CodexLiveProducerAdapter

        with tempfile.TemporaryDirectory(prefix="daee-live-residue-stop-") as temp, tempfile.TemporaryDirectory(
            prefix="daee-live-residue-source-"
        ) as source_temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            source_root = Path(source_temp)
            residue = source_root / "ignored/__pycache__/blocked.pyc"
            residue.parent.mkdir(parents=True)
            residue.write_bytes(b"synthetic checkout residue\n")
            host = _ScriptedCodexHost()
            adapter = CodexLiveProducerAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                access_token="fixture-access-token-never-retain",
                host=host,
            )

            with mock.patch.object(orchestrator, "ROOT", source_root), self.assertRaisesRegex(
                CampaignError,
                "CHECKOUT_EXECUTION_RESIDUE",
            ):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            self.assertEqual([("probe", executable.name)], host.log)
            self.assertFalse((fixture.root / "claims").exists())
            self.assertFalse((fixture.root / "usage").exists())

    def test_paid_live_path_rejects_unreadable_checkout_subtree_before_authorization_read(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-live-residue-traversal-stop-") as temp:
            source_root = Path(temp)
            adapter = mock.Mock()
            adapter.capability.return_value = {
                "schema": "reviewed-campaign-provider-capability-v1",
                "adapter_kind": "codex-live",
                "adapter_version": "codex-live-v1",
                "host_application_version": "synthetic-no-provider-host-v1",
                "codex_executable_sha256": "a" * 64,
                "model": "gpt-5.5",
                "reasoning_effort": "high",
                "test_only": False,
                "paid_provider_reachable": True,
                "live_execution_authorized": True,
            }

            with mock.patch.object(orchestrator, "ROOT", source_root), mock.patch.object(
                orchestrator.os,
                "scandir",
                side_effect=PermissionError("synthetic unreadable checkout subtree"),
            ), mock.patch.object(
                orchestrator,
                "_load_producer_authorization",
                side_effect=CampaignError("AUTHORIZATION_READ_REACHED"),
            ) as authorization_read, self.assertRaisesRegex(
                CampaignError,
                "^CHECKOUT_EXECUTION_RESIDUE_TRAVERSAL_UNAVAILABLE$",
            ):
                run_producer_cohort(
                    source_root,
                    source_root / "must-not-be-read.json",
                    adapter,
                )

            authorization_read.assert_not_called()

    def test_fixture_flag_rejects_paid_live_adapter_preparation(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator
        from codex_live_producer_adapter import CodexLiveProducerAdapter

        with tempfile.TemporaryDirectory(prefix="daee-live-paid-prepare-escape-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            auth, auth_sha = orchestrator._load_producer_authorization(
                fixture.root,
                authorization,
                allow_test_fixture=True,
            )
            bindings = orchestrator._validate_common_bindings(
                fixture.root,
                auth,
                allow_test_fixture=True,
            )
            bindings["producer_output_contracts"] = orchestrator._producer_output_contracts(
                auth,
                auth_sha,
                bindings,
            )
            adapter = CodexLiveProducerAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                access_token="fixture-access-token-never-retain",
                host=_ScriptedCodexHost(),
            )
            adapter.capability()

            with self.assertRaisesRegex(RuntimeError, "paid live adapter cannot use test fixtures"):
                adapter.prepare(auth, bindings, allow_test_fixture=True)

            self.assertFalse((fixture.root / "producer/isolated").exists())

    def test_fixture_common_bindings_reject_live_normalized_authority(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-live-binding-fixture-escape-") as temp:
            fixture, authorization, _executable, _skill_bytes = self._live_fixture(Path(temp))
            auth, _auth_sha = orchestrator._load_producer_authorization(
                fixture.root,
                authorization,
            )

            with self.assertRaisesRegex(CampaignError, "TEST_FIXTURE_LIVE_AUTHORITY_FORBIDDEN"):
                orchestrator._validate_common_bindings(
                    fixture.root,
                    auth,
                    allow_test_fixture=True,
                )

    def test_live_shaped_fixture_normalizes_to_nonlive_test_authority(self) -> None:
        from reviewed_campaign_orchestrator import (
            SCRIPTED_CODEX_TEST_MODE,
            _load_producer_authorization,
        )

        with tempfile.TemporaryDirectory(prefix="daee-live-fixture-authority-") as temp:
            fixture, authorization, _executable, _skill_bytes = self._live_fixture(Path(temp))
            auth, _auth_sha = _load_producer_authorization(
                fixture.root,
                authorization,
                allow_test_fixture=True,
            )

            self.assertEqual(SCRIPTED_CODEX_TEST_MODE, auth["execution_mode"])
            self.assertIs(auth["test_only"], True)
            self.assertIs(auth["live_execution_authorized"], False)

    def test_live_readiness_and_source_receipt_are_exact_preclaim_bindings(self) -> None:
        from codex_live_producer_adapter import CodexLiveProducerAdapter
        for role in ("candidate_readiness", "source_commit_receipt"):
            with self.subTest(role=role), tempfile.TemporaryDirectory(prefix="daee-live-exact-binding-") as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
                matrix = json.loads(authorization.read_text(encoding="utf-8"))
                if role == "candidate_readiness":
                    altered = json.loads(fixture.candidate.read_text(encoding="utf-8"))
                    altered["candidate_id"] = "substituted-candidate"
                else:
                    altered = json.loads(fixture.preflight.read_text(encoding="utf-8"))
                    altered["source_commit"] = "e" * 40
                altered_path = fixture.root / f"inputs/altered-{role}.json"
                write_json(altered_path, altered)
                matrix[role] = {"path": altered_path.relative_to(fixture.root).as_posix(), "sha256": digest(altered_path)}
                matrix["authorization_sha256"] = record_sha256({key: value for key, value in matrix.items() if key != "authorization_sha256"})
                write_json(authorization, matrix)
                host = _ScriptedCodexHost()
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root, codex_executable=executable,
                    host=host,
                )
                marker = "CANDIDATE_READINESS_AUTHORIZATION_BINDING" if role == "candidate_readiness" else "SOURCE_COMMIT_RECEIPT_AUTHORIZATION_BINDING"
                with self.assertRaisesRegex(CampaignError, marker):
                    run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
                self.assertFalse((fixture.root / "claims").exists())
                self.assertEqual([("probe", executable.name)], host.log)

    def test_live_authority_is_rechecked_before_claim_reservation_and_submit(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator
        from codex_live_producer_adapter import CodexLiveProducerAdapter
        with tempfile.TemporaryDirectory(prefix="daee-live-recheck-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root, codex_executable=executable,
                host=host,
            )
            original = orchestrator._load_producer_authorization
            calls = 0

            def drift_on_prereservation(
                root: Path,
                path: Path,
                **kwargs: object,
            ) -> tuple[dict[str, object], str]:
                nonlocal calls
                calls += 1
                value, sha = original(root, path, **kwargs)
                if calls == 3:
                    value = {**value, "package_sha256": "f" * 64}
                return value, sha

            with mock.patch.object(orchestrator, "_load_producer_authorization", side_effect=drift_on_prereservation):
                with self.assertRaisesRegex(CampaignError, "LIVE_AUTHORIZATION_RECHECK_DRIFT"):
                    run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
            self.assertEqual(3, calls)
            self.assertEqual([], host.starts)
            self.assertTrue((fixture.root / "claims/producer-authorization.json").is_file())
            self.assertTrue((fixture.root / "producer/observation-finalizer.json").is_file())

    def test_live_final_presubmit_authority_drift_is_proved_no_dispatch_and_replayable(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-live-final-recheck-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
            )
            original = orchestrator._load_producer_authorization
            calls = 0

            def drift_on_final_presubmit(
                root: Path,
                path: Path,
                **kwargs: object,
            ) -> tuple[dict[str, object], str]:
                nonlocal calls
                calls += 1
                value, sha = original(root, path, **kwargs)
                if calls == 4:
                    value = {**value, "package_sha256": "f" * 64}
                return value, sha

            with mock.patch.object(
                orchestrator,
                "_load_producer_authorization",
                side_effect=drift_on_final_presubmit,
            ):
                with self.assertRaisesRegex(CampaignError, "LIVE_AUTHORIZATION_RECHECK_DRIFT"):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            self.assertEqual(4, calls)
            self.assertEqual([], host.starts)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(5, head["totals"]["not_dispatched"])
            self.assertEqual(0, head["totals"]["producer_invocations"])
            self.assertFalse(head["open_reservations"])
            self.assertFalse(head["unresolved_usage"])
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_text(encoding="utf-8")
            )
            self.assertEqual("pre-dispatch", finalizer["failure_phase"])
            self.assertEqual("PROVED_NO_DISPATCH", finalizer["dispatch_classification"])
            self.assertEqual("CONSUMED_NO_DISPATCH", finalizer["candidate_status"])

            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=replay_host,
            )
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)

    def test_live_path_custody_rejects_existing_reparse_components(self) -> None:
        import codex_live_producer_adapter as live_adapter
        with tempfile.TemporaryDirectory(prefix="daee-live-reparse-") as temp:
            root = Path(temp)
            component = root / "existing"
            component.mkdir()
            original = live_adapter._is_reparse
            with mock.patch.object(live_adapter, "_is_reparse", side_effect=lambda path: path == component or original(path)):
                with self.assertRaisesRegex(ValueError, "symlink/reparse component"):
                    live_adapter._safe_join(root, "existing/child", "canary")

    def test_live_capability_requires_exact_structured_catalog_and_cli_flags(self) -> None:
        from codex_live_producer_adapter import CodexLiveProducerAdapter
        for mutation in ("effort", "flags"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix="daee-live-catalog-") as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))

                class DriftHost(_ScriptedCodexHost):
                    def probe(self, executable: Path, *, credential_carrier_available: bool) -> dict[str, object]:
                        value = super().probe(
                            executable,
                            credential_carrier_available=credential_carrier_available,
                        )
                        if mutation == "effort":
                            value["catalog_row"] = {"slug": "gpt-5.5", "supported_reasoning_efforts": ["medium"]}
                        else:
                            value["canonical_exec_flags"] = value["canonical_exec_flags"][:-1]
                        return value

                host = DriftHost()
                adapter = CodexLiveProducerAdapter(
                    custody_root=fixture.root, codex_executable=executable,
                    access_token="fixture-access-token-never-retain", host=host,
                )
                with self.assertRaisesRegex(CampaignError, "PROVIDER_CAPABILITY_UNAVAILABLE"):
                    run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
                self.assertFalse((fixture.root / "claims").exists())

    def test_production_help_parser_requires_exact_option_declarations(self) -> None:
        from codex_live_producer_adapter import _parse_codex_exec_option_identities
        valid = """Usage: codex exec [OPTIONS] [PROMPT]\n\nOptions:\n  -c, --config <key=value>  Override configuration\n      --json                Emit JSONL\n      --ephemeral           Use ephemeral state\n      --ignore-user-config  Ignore user config\n      --ignore-rules        Ignore rules\n  -C, --cd <DIR>            Set working directory\n  -s, --sandbox <MODE>      Select sandbox\n  -m, --model <MODEL>       Select model\n      --output-last-message <FILE>  Retain final message\n  -h, --help                Print help\n"""
        required = {"-c", "--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "-C", "-s", "-m", "--output-last-message"}
        self.assertTrue(required.issubset(_parse_codex_exec_option_identities(valid)))
        hostile = valid.replace("      --json                Emit JSONL", "      --json-output         Superstring only\n          --json  is mentioned only in prose")
        parsed = _parse_codex_exec_option_identities(hostile)
        self.assertIn("--json-output", parsed)
        self.assertNotIn("--json", parsed)

    def test_capability_probe_routes_every_process_through_owned_launcher(self) -> None:
        import codex_live_producer_adapter as live_adapter

        help_text = """Usage: codex exec [OPTIONS] [PROMPT]\n\nOptions:\n  -c, --config <key=value>  Override configuration\n      --json                Emit JSONL\n      --ephemeral           Use ephemeral state\n      --ignore-user-config  Ignore user config\n      --ignore-rules        Ignore rules\n  -C, --cd <DIR>            Set working directory\n  -s, --sandbox <MODE>      Select sandbox\n  -m, --model <MODEL>       Select model\n      --output-last-message <FILE>  Retain final message\n  -h, --help                Print help\n"""
        with tempfile.TemporaryDirectory(prefix="daee-live-owned-probe-") as temp:
            executable = Path(temp) / "codex.exe"
            executable.write_bytes(b"local no-network capability fixture\n")
            host = live_adapter.SubprocessCodexHost()
            owned_results = [
                subprocess.CompletedProcess([], 0, "codex-cli 0.130.0-alpha.5\n", ""),
                subprocess.CompletedProcess(
                    [],
                    0,
                    json.dumps(
                        {
                            "models": [
                                {
                                    "slug": "gpt-5.5",
                                    "supported_reasoning_efforts": ["none", "low", "medium", "high"],
                                }
                            ]
                        }
                    ),
                    "",
                ),
                subprocess.CompletedProcess([], 0, help_text, ""),
            ]
            with mock.patch.object(
                host,
                "_run_probe_command",
                create=True,
                side_effect=owned_results,
            ) as owned, mock.patch.object(
                live_adapter.subprocess,
                "run",
                side_effect=AssertionError("capability probe bypassed owned process custody"),
            ):
                probe = host.probe(executable, credential_carrier_available=True)

            self.assertEqual(3, owned.call_count)
            self.assertEqual(
                [
                    [str(executable), "--version"],
                    [str(executable), "debug", "models", "--bundled"],
                    [str(executable), "exec", "--help"],
                ],
                [call.args[0] for call in owned.call_args_list],
            )
            self.assertTrue(
                all("CODEX_ACCESS_TOKEN" not in call.kwargs["env"] for call in owned.call_args_list)
            )
            self.assertEqual("gpt-5.5", probe["catalog_row"]["slug"])
            self.assertIs(probe["credential_carrier_available"], True)

    def test_capability_probe_normalizes_current_structured_reasoning_levels(self) -> None:
        import codex_live_producer_adapter as live_adapter

        help_text = """Usage: codex exec [OPTIONS] [PROMPT]\n\nOptions:\n  -c, --config <key=value>  Override configuration\n      --json                Emit JSONL\n      --ephemeral           Use ephemeral state\n      --ignore-user-config  Ignore user config\n      --ignore-rules        Ignore rules\n  -C, --cd <DIR>            Set working directory\n  -s, --sandbox <MODE>      Select sandbox\n  -m, --model <MODEL>       Select model\n      --output-last-message <FILE>  Retain final message\n  -h, --help                Print help\n"""
        with tempfile.TemporaryDirectory(prefix="daee-live-current-catalog-") as temp:
            executable = Path(temp) / "codex.exe"
            executable.write_bytes(b"local no-network capability fixture\n")
            host = live_adapter.SubprocessCodexHost()
            current_catalog = {
                "models": [
                    {
                        "slug": "gpt-5.5",
                        "supported_reasoning_levels": [
                            {"description": "Fast responses", "effort": "low"},
                            {"description": "Greater reasoning depth", "effort": "high"},
                        ],
                    }
                ]
            }
            with mock.patch.object(
                host,
                "_run_probe_command",
                side_effect=[
                    subprocess.CompletedProcess([], 0, "codex-cli 0.130.0-alpha.5\n", ""),
                    subprocess.CompletedProcess([], 0, json.dumps(current_catalog), ""),
                    subprocess.CompletedProcess([], 0, help_text, ""),
                ],
            ):
                try:
                    probe = host.probe(executable, credential_carrier_available=True)
                except RuntimeError as exc:
                    self.fail(f"current structured model catalog was rejected: {exc}")

            self.assertEqual(
                {"slug": "gpt-5.5", "supported_reasoning_efforts": ["low", "high"]},
                probe["catalog_row"],
            )

    def test_live_capability_reads_no_environment_credential_value_and_retains_none(self) -> None:
        import codex_live_producer_adapter as live_adapter

        class MembershipOnlyEnvironment:
            def __contains__(self, key: object) -> bool:
                return key == "CODEX_ACCESS_TOKEN"

            def get(self, *_args: object, **_kwargs: object) -> object:
                raise AssertionError("credential environment value was read")

            def __getitem__(self, _key: object) -> object:
                raise AssertionError("credential environment value was indexed")

            def __iter__(self):
                raise AssertionError("credential environment was iterated")

            def items(self):
                raise AssertionError("credential environment items were read")

            def values(self):
                raise AssertionError("credential environment values were read")

        with tempfile.TemporaryDirectory(prefix="daee-live-secret-free-capability-") as temp:
            root = Path(temp)
            executable = root / "codex.exe"
            executable.write_bytes(b"local no-network capability fixture\n")
            host = _ScriptedCodexHost()
            adapter = live_adapter.CodexLiveProducerAdapter(
                custody_root=root,
                codex_executable=executable,
                host=host,
            )

            with mock.patch.object(live_adapter.os, "environ", MembershipOnlyEnvironment()):
                capability = adapter.capability()

            self.assertEqual("gpt-5.5", capability["model"])
            self.assertEqual([True], host.probe_carriers)
            self.assertIsNone(adapter._credential)

    def test_live_capability_auth_file_carrier_uses_metadata_only(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-carrier-metadata-") as temp:
            root = Path(temp)
            executable = root / "codex.exe"
            executable.write_bytes(b"local no-network capability fixture\n")

            cases = []
            for name, kind, expected in (
                ("absent", "absent", False),
                ("empty", "empty", False),
                ("directory", "directory", False),
                ("regular", "regular", True),
            ):
                home = root / name
                auth = home / ".codex/auth.json"
                auth.parent.mkdir(parents=True)
                if kind == "empty":
                    auth.write_bytes(b"")
                elif kind == "directory":
                    auth.mkdir()
                elif kind == "regular":
                    auth.write_bytes(b"nonempty carrier; not parsed by capability\n")
                cases.append((name, home, expected))

            for name, home, expected in cases:
                with self.subTest(name=name):
                    adapter = live_adapter.CodexLiveProducerAdapter(
                        custody_root=root,
                        codex_executable=executable,
                        host=_ScriptedCodexHost(),
                    )
                    with mock.patch.object(live_adapter.os, "environ", {}), mock.patch.object(
                        live_adapter.Path,
                        "home",
                        return_value=home,
                    ), mock.patch.object(
                        live_adapter.Path,
                        "read_text",
                        side_effect=AssertionError("auth carrier content was read"),
                    ):
                        self.assertIs(adapter._credential_carrier_available(), expected)
                    self.assertIsNone(adapter._credential)

            auth = root / "reparse/.codex/auth.json"
            auth.parent.mkdir(parents=True)
            auth.write_bytes(b"synthetic reparse carrier\n")
            observed = mock.Mock(
                st_mode=stat.S_IFREG | 0o600,
                st_size=24,
                st_file_attributes=live_adapter._REPARSE_POINT,
            )
            adapter = live_adapter.CodexLiveProducerAdapter(
                custody_root=root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
            )
            with mock.patch.object(live_adapter.os, "environ", {}), mock.patch.object(
                live_adapter.Path,
                "home",
                return_value=root / "reparse",
            ), mock.patch.object(
                live_adapter,
                "_lstat_optional",
                return_value=observed,
            ), mock.patch.object(
                live_adapter.Path,
                "read_text",
                side_effect=AssertionError("reparse auth carrier content was read"),
            ):
                self.assertIs(adapter._credential_carrier_available(), False)

    def test_live_managed_auth_transport_never_reframes_or_reads_auth_file_tokens(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-managed-auth-") as temp, tempfile.TemporaryDirectory(
            prefix="daee-live-managed-auth-home-"
        ) as controller_temp:
            root = Path(temp)
            fixture, authorization, executable, _skill_bytes = self._live_fixture(root)
            controller_home = Path(controller_temp)
            auth_file = controller_home / ".codex/auth.json"
            auth_file.parent.mkdir(parents=True)
            auth_bytes = b"synthetic managed auth carrier; deliberately not JSON\n"
            auth_file.write_bytes(auth_bytes)
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                fixture_token=None,
            )

            with mock.patch.object(live_adapter.os, "environ", {}), mock.patch.object(
                live_adapter.Path,
                "home",
                return_value=controller_home,
            ):
                completion = run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            self.assertEqual("PRODUCER_CAPTURE_COMPLETE", completion["status"])
            self.assertEqual(5, len(host.starts))
            self.assertEqual(auth_bytes, auth_file.read_bytes())
            self.assertIsNone(adapter._inner._credential)
            for start in host.starts:
                env = start["env"]
                self.assertNotIn("CODEX_ACCESS_TOKEN", env)
                self.assertEqual(auth_file.parent, Path(env["CODEX_HOME"]))
                worker_root = Path(start["cwd"]).parent
                self.assertTrue(Path(env["HOME"]).is_relative_to(worker_root))
                self.assertTrue(Path(env["USERPROFILE"]).is_relative_to(worker_root))
                self.assertTrue(Path(env["CODEX_SQLITE_HOME"]).is_relative_to(worker_root))
                self.assertNotEqual(env["CODEX_HOME"], env["HOME"])
            for result in completion["results"]:
                capture = json.loads(
                    (fixture.root / result["capture_evidence"]["path"]).read_text(
                        encoding="utf-8"
                    )
                )
                scan = json.loads(
                    (fixture.root / capture["credential_residue_scan"]["path"]).read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual("reviewed-campaign-credential-residue-scan-v2", scan["schema"])
                self.assertEqual("MANAGED_AUTH_STRUCTURAL_MARKERS", scan["scan_mode"])
                self.assertIs(scan["credential_value_loaded_by_adapter"], False)
            retained = b"\n".join(
                path.read_bytes() for path in fixture.root.rglob("*") if path.is_file()
            )
            self.assertNotIn(auth_bytes.rstrip(), retained)

    def test_checkout_execution_residue_inventory_finds_ignored_nested_bytecode(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-checkout-residue-") as temp:
            root = Path(temp)
            (root / ".git/objects").mkdir(parents=True)
            (root / ".git/objects/ignored.pyc").write_bytes(b"git metadata excluded\n")
            (root / "ignored/a/__pycache__").mkdir(parents=True)
            (root / "ignored/b").mkdir(parents=True)
            (root / "ignored/b/orphan.pyc").write_bytes(b"orphan bytecode\n")
            (root / "ignored/c/__pycache__").mkdir(parents=True)
            (root / "ignored/c/__pycache__/module.cpython-312.pyc").write_bytes(
                b"nested bytecode\n"
            )

            report = orchestrator.checkout_execution_residue_inventory(root)

            self.assertEqual("FAIL", report["status"])
            self.assertEqual(4, report["entry_count"])
            self.assertEqual(
                [
                    "ignored/a/__pycache__",
                    "ignored/b/orphan.pyc",
                    "ignored/c/__pycache__",
                    "ignored/c/__pycache__/module.cpython-312.pyc",
                ],
                [row["path"] for row in report["entries"]],
            )
            self.assertNotIn(".git/objects/ignored.pyc", [row["path"] for row in report["entries"]])
            with self.assertRaisesRegex(CampaignError, "CHECKOUT_EXECUTION_RESIDUE"):
                orchestrator.require_checkout_execution_residue_free(root)

    def test_managed_auth_pre_admission_residue_purges_and_replays_terminally(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-managed-auth-residue-") as temp, tempfile.TemporaryDirectory(
            prefix="daee-live-managed-auth-residue-home-"
        ) as controller_temp:
            import codex_live_producer_adapter as live_adapter

            root = Path(temp)
            fixture, authorization, executable, _skill_bytes = self._live_fixture(root)
            controller_home = Path(controller_temp)
            auth_file = controller_home / ".codex/auth.json"
            auth_file.parent.mkdir(parents=True)
            auth_file.write_bytes(b"synthetic managed auth carrier; deliberately not JSON\n")
            host = _ScriptedCodexHost(
                already_exited_at=1,
                nonzero_at=1,
                credential_residue_at=1,
            )
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                fixture_token=None,
            )

            with mock.patch.object(live_adapter.os, "environ", {}), mock.patch.object(
                live_adapter.Path,
                "home",
                return_value=controller_home,
            ), self.assertRaisesRegex(CampaignError, "access credential residue detected"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            self.assertEqual(1, len(host.starts))
            self.assertFalse((fixture.root / "producer/isolated/producer-01").exists())
            head = validate_head(fixture.root / "usage")
            self.assertFalse(head["open_reservations"])
            self.assertTrue(head["unresolved_usage"])
            self.assertEqual(0, head["totals"]["attempted"])
            self.assertEqual(0, head["totals"]["producer_invocations"])
            self.assertEqual(1, head["totals"]["unknown"])
            self.assertEqual(4, head["totals"]["not_dispatched"])
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_text(
                    encoding="utf-8"
                )
            )
            diagnostic = json.loads(
                (
                    fixture.root
                    / finalizer["pre_admission_diagnostics"][0]["path"]
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("PURGED_UNRETAINED", diagnostic["carrier_disposition"])
            scan = json.loads(
                (
                    fixture.root / diagnostic["credential_residue_scan"]["path"]
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("reviewed-campaign-credential-residue-scan-v2", scan["schema"])
            self.assertEqual("FAIL_CLOSED", scan["status"])
            self.assertEqual("CREDENTIAL_RESIDUE", scan["failure_class"])
            self.assertEqual("MANAGED_AUTH_STRUCTURAL_MARKERS", scan["scan_mode"])
            self.assertIs(scan["credential_value_loaded_by_adapter"], False)
            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=replay_host,
                fixture_token=None,
            )
            with mock.patch.object(live_adapter.os, "environ", {}), mock.patch.object(
                live_adapter.Path,
                "home",
                return_value=controller_home,
            ), self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)

    def test_capability_host_rejects_non_boolean_carrier_before_launch(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-host-carrier-type-") as temp:
            executable = Path(temp) / "codex.exe"
            executable.write_bytes(b"local no-network capability fixture\n")
            host = live_adapter.SubprocessCodexHost()
            with mock.patch.object(
                host,
                "_run_probe_command",
                side_effect=AssertionError("invalid carrier reached process launch"),
            ) as launched:
                with self.assertRaisesRegex(TypeError, "credential carrier availability must be Boolean"):
                    host.probe(executable, credential_carrier_available="not-a-Boolean")
            launched.assert_not_called()

    def test_live_token_acquisition_waits_for_claim_and_reservation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-deferred-token-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
            )
            observations: list[tuple[bool, int, int]] = []
            original = adapter._inner._token

            def acquire_after_authority() -> str:
                snapshot = head_snapshot(fixture.root / "usage")
                observations.append(
                    (
                        (fixture.root / "claims/producer-authorization.json").is_file(),
                        len(snapshot["open_reservations"]),
                        len(host.starts),
                    )
                )
                return original()

            self.assertIsNone(adapter._inner._credential)
            with mock.patch.object(adapter._inner, "_token", side_effect=acquire_after_authority):
                completion = run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            self.assertEqual("PRODUCER_CAPTURE_COMPLETE", completion["status"])
            self.assertEqual(5, len(observations))
            self.assertEqual((True, 1, 0), observations[0])

    def test_directory_ownership_rejects_same_device_inode_replacement(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-directory-identity-") as temp:
            path = Path(temp) / "owned"
            identity = live_adapter._create_owned_directory(path, "owned", parents=False)
            shutil.rmtree(path)
            path.mkdir()
            sentinel = path / "foreign-sentinel.txt"
            sentinel.write_bytes(b"same-device-inode replacement must survive\n")
            original_lstat = live_adapter._lstat_optional
            collision = mock.Mock(
                st_mode=stat.S_IFDIR | 0o700,
                st_dev=identity[0],
                st_ino=identity[1],
                st_file_attributes=0,
            )

            def collide(candidate: Path):
                if candidate == path:
                    return collision
                return original_lstat(candidate)

            with mock.patch.object(live_adapter, "_lstat_optional", side_effect=collide):
                with self.assertRaisesRegex(
                    live_adapter.IsolationCleanupError,
                    "ownership witness|creation identity changed",
                ):
                    live_adapter._require_owned_directory(path, identity, "owned")

            self.assertEqual(b"same-device-inode replacement must survive\n", sentinel.read_bytes())

    def test_owned_directory_creation_preserves_same_byte_generation_substitution(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-directory-create-substitution-") as temp:
            path = Path(temp) / "owned"
            witness_path = path / live_adapter._OWNERSHIP_WITNESS_NAME
            state: dict[str, object] = {
                "replaced": False,
                "replacement_bytes": None,
            }
            real_write_once = live_adapter._write_once

            def replace_after_create(candidate: Path, data: bytes):
                created_identity = real_write_once(candidate, data)
                if candidate == witness_path and not state["replaced"]:
                    replacement_bytes = bytes(data)
                    candidate.unlink()
                    candidate.write_bytes(replacement_bytes)
                    state["replaced"] = True
                    state["replacement_bytes"] = replacement_bytes
                return created_identity

            with mock.patch.object(
                live_adapter,
                "_write_once",
                side_effect=replace_after_create,
            ):
                with self.assertRaisesRegex(
                    live_adapter.IsolationCleanupError,
                    "OWNED_ISOLATION_CREATION_IDENTITY_UNAVAILABLE",
                ):
                    live_adapter._create_owned_directory(path, "owned", parents=False)

            self.assertTrue(state["replaced"])
            self.assertIsInstance(state["replacement_bytes"], bytes)
            self.assertTrue(path.is_dir())
            self.assertEqual(state["replacement_bytes"], witness_path.read_bytes())

    def test_owned_directory_creation_cleanup_preserves_post_readback_same_byte_substitution(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-directory-cleanup-substitution-") as temp:
            path = Path(temp) / "owned"
            witness_path = path / live_adapter._OWNERSHIP_WITNESS_NAME
            state: dict[str, object] = {
                "witness_readbacks": 0,
                "replacement_bytes": None,
                "replacement_different_generation": False,
            }
            real_directory_identity = live_adapter._regular_directory_identity
            real_witness_identity = live_adapter._ownership_witness_identity

            def force_parent_mismatch(candidate: Path, label: str):
                identity = real_directory_identity(candidate, label)
                return identity._replace(directory_inode=identity.directory_inode + 1)

            def replace_after_cleanup_readback(candidate: Path, label: str):
                identity = real_witness_identity(candidate, label)
                state["witness_readbacks"] = int(state["witness_readbacks"]) + 1
                if state["witness_readbacks"] == 2:
                    replacement_bytes = candidate.read_bytes()
                    before = candidate.lstat()
                    foreign = candidate.with_name(".foreign-owned-directory-witness")
                    foreign.write_bytes(replacement_bytes)
                    candidate.unlink()
                    foreign.replace(candidate)
                    after = candidate.lstat()
                    state["replacement_bytes"] = replacement_bytes
                    state["replacement_different_generation"] = (
                        before.st_dev,
                        before.st_ino,
                        before.st_ctime_ns,
                    ) != (
                        after.st_dev,
                        after.st_ino,
                        after.st_ctime_ns,
                    )
                return identity

            with mock.patch.object(
                live_adapter,
                "_regular_directory_identity",
                side_effect=force_parent_mismatch,
            ), mock.patch.object(
                live_adapter,
                "_ownership_witness_identity",
                side_effect=replace_after_cleanup_readback,
            ):
                with self.assertRaisesRegex(
                    live_adapter.IsolationCleanupError,
                    "OWNED_ISOLATION_CREATION_IDENTITY_UNAVAILABLE",
                ):
                    live_adapter._create_owned_directory(path, "owned", parents=False)

            self.assertIn(state["witness_readbacks"], (1, 2))
            if state["witness_readbacks"] == 2:
                self.assertTrue(state["replacement_different_generation"])
                self.assertIsInstance(state["replacement_bytes"], bytes)
            else:
                self.assertFalse(state["replacement_different_generation"])
                self.assertIsNone(state["replacement_bytes"])
            self.assertTrue(path.is_dir())
            retained_bytes = witness_path.read_bytes()
            if state["replacement_bytes"] is not None:
                self.assertEqual(state["replacement_bytes"], retained_bytes)
            self.assertEqual(live_adapter._OWNERSHIP_WITNESS_BYTE_COUNT, len(retained_bytes))

    def test_directory_ownership_witness_survives_legitimate_mutations_and_controls_root_cleanup(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-directory-witness-normal-") as temp:
            path = Path(temp) / "owned"
            identity = live_adapter._create_owned_directory(path, "owned", parents=False)
            marker = path / live_adapter._OWNERSHIP_WITNESS_NAME
            self.assertTrue(marker.is_file())

            child = path / "mutable-child"
            child.mkdir()
            payload = child / "payload.bin"
            payload.write_bytes(b"legitimate descendant mutation\n")
            payload.write_bytes(b"legitimate descendant mutation updated\n")
            shutil.rmtree(child)

            self.assertIsNotNone(live_adapter._require_owned_directory(path, identity, "owned"))
            adapter = object.__new__(live_adapter.CodexLiveProducerAdapter)
            adapter._owned_workers = {}
            adapter._isolated_root_owner = (path, identity)
            adapter._remove_owned_root_if_ready()
            self.assertFalse(path.exists())
            self.assertIsNone(adapter._isolated_root_owner)

    def test_directory_ownership_witness_drift_preserves_foreign_path(self) -> None:
        import codex_live_producer_adapter as live_adapter

        for mutation in ("missing", "tampered", "same-byte-recreated", "reparse", "copied-replacement"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(
                prefix=f"daee-live-directory-witness-{mutation}-"
            ) as temp:
                path = Path(temp) / "owned"
                identity = live_adapter._create_owned_directory(path, "owned", parents=False)
                marker = path / live_adapter._OWNERSHIP_WITNESS_NAME
                marker_bytes = marker.read_bytes()
                sentinel = path / "foreign-sentinel.txt"
                original_lstat = live_adapter._lstat_optional

                if mutation == "missing":
                    marker.unlink()
                    sentinel.write_bytes(b"missing witness replacement\n")
                elif mutation == "tampered":
                    marker.write_bytes(b"x" * len(marker_bytes))
                    sentinel.write_bytes(b"tampered witness replacement\n")
                elif mutation == "same-byte-recreated":
                    marker.unlink()
                    marker.write_bytes(marker_bytes)
                    sentinel.write_bytes(b"recreated witness replacement\n")
                elif mutation == "reparse":
                    sentinel.write_bytes(b"reparse witness replacement\n")
                else:
                    shutil.rmtree(path)
                    path.mkdir()
                    marker.write_bytes(marker_bytes)
                    sentinel.write_bytes(b"copied witness replacement\n")

                collision = mock.Mock(
                    st_mode=stat.S_IFDIR | 0o700,
                    st_dev=identity[0],
                    st_ino=identity[1],
                    st_file_attributes=0,
                )
                reparse = mock.Mock(
                    st_mode=stat.S_IFREG | 0o600,
                    st_dev=identity.witness_device,
                    st_ino=identity.witness_inode,
                    st_ctime_ns=identity.witness_ctime_ns,
                    st_size=identity.witness_byte_count,
                    st_file_attributes=live_adapter._REPARSE_POINT,
                )

                def drift(candidate: Path):
                    if mutation == "copied-replacement" and candidate == path:
                        return collision
                    if mutation == "reparse" and candidate == marker:
                        return reparse
                    return original_lstat(candidate)

                with mock.patch.object(live_adapter, "_lstat_optional", side_effect=drift):
                    with self.assertRaisesRegex(
                        live_adapter.IsolationCleanupError,
                        "ownership witness|creation identity changed",
                    ):
                        live_adapter._require_owned_directory(path, identity, "owned")

                self.assertTrue(path.is_dir())
                self.assertTrue(sentinel.is_file())

    @unittest.skipUnless(os.name == "nt", "Windows Job Object custody canary")
    def test_windows_owned_process_survives_disappearing_intermediate_until_job_teardown(self) -> None:
        import ctypes
        from ctypes import wintypes
        from codex_live_producer_adapter import SubprocessCodexHost

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        process = None
        child_handle = None
        wait_timeout = 0x00000102
        wait_object_0 = 0x00000000

        with tempfile.TemporaryDirectory(prefix="daee-live-job-custody-") as temp:
            root = Path(temp)
            script = root / "disappearing-intermediate.py"
            child_pid_path = root / "owned-child.pid"
            prompt = root / "prompt.bin"
            events = root / "events.jsonl"
            stderr = root / "stderr.txt"
            output = root / "output.txt"
            prompt.write_bytes(b"")
            script.write_text(
                "import subprocess, sys\n"
                "intermediate = \"import pathlib, subprocess, sys; "
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding='ascii')\"\n"
                "subprocess.run([sys.executable, '-c', intermediate, sys.argv[1]], check=True)\n",
                encoding="utf-8",
                newline="\n",
            )
            host = SubprocessCodexHost()
            try:
                process = host.start(
                    [sys.executable, "-B", str(script), str(child_pid_path)],
                    cwd=root,
                    env=dict(os.environ),
                    prompt_path=prompt,
                    event_log_path=events,
                    stderr_path=stderr,
                    output_path=output,
                    worker="local-custody-canary",
                )
                self.assertEqual(0, process.wait(timeout=10))
                child_pid = int(child_pid_path.read_text(encoding="ascii"))
                child_handle = kernel32.OpenProcess(0x0001 | 0x100000, False, child_pid)
                self.assertTrue(child_handle, ctypes.WinError(ctypes.get_last_error()))
                self.assertEqual(wait_timeout, kernel32.WaitForSingleObject(child_handle, 0))

                self.assertFalse(host.verify_tree_stopped(process))
                host.terminate_tree(process)
                self.assertTrue(host.verify_tree_stopped(process))
                self.assertEqual(wait_object_0, kernel32.WaitForSingleObject(child_handle, 5000))
            finally:
                if process is not None:
                    try:
                        host.terminate_tree(process)
                    except Exception:
                        pass
                if child_handle:
                    if kernel32.WaitForSingleObject(child_handle, 0) == wait_timeout:
                        kernel32.TerminateProcess(child_handle, 91)
                        kernel32.WaitForSingleObject(child_handle, 5000)
                    kernel32.CloseHandle(child_handle)

    @unittest.skipUnless(os.name == "nt", "Windows Job Object custody canary")
    def test_windows_status_query_failure_kills_owned_descendant_before_escape(self) -> None:
        import ctypes
        from ctypes import wintypes
        from codex_live_producer_adapter import CodexLiveProducerAdapter, SubprocessCodexHost

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        process = None
        child_handle = None
        wait_timeout = 0x00000102
        wait_object_0 = 0x00000000

        with tempfile.TemporaryDirectory(prefix="daee-live-job-query-failure-") as temp:
            root = Path(temp)
            script = root / "disappearing-intermediate.py"
            child_pid_path = root / "owned-child.pid"
            prompt = root / "prompt.bin"
            events = root / "events.jsonl"
            stderr = root / "stderr.txt"
            output = root / "output.txt"
            prompt.write_bytes(b"")
            script.write_text(
                "import subprocess, sys\n"
                "intermediate = \"import pathlib, subprocess, sys; "
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding='ascii')\"\n"
                "subprocess.run([sys.executable, '-c', intermediate, sys.argv[1]], check=True)\n",
                encoding="utf-8",
                newline="\n",
            )
            host = SubprocessCodexHost()
            adapter = object.__new__(CodexLiveProducerAdapter)
            adapter.host = host
            try:
                process = host.start(
                    [sys.executable, "-B", str(script), str(child_pid_path)],
                    cwd=root,
                    env=dict(os.environ),
                    prompt_path=prompt,
                    event_log_path=events,
                    stderr_path=stderr,
                    output_path=output,
                    worker="local-query-failure-canary",
                )
                self.assertEqual(0, process.wait(timeout=10))
                child_pid = int(child_pid_path.read_text(encoding="ascii"))
                child_handle = kernel32.OpenProcess(0x0001 | 0x100000, False, child_pid)
                self.assertTrue(child_handle, ctypes.WinError(ctypes.get_last_error()))
                self.assertEqual(wait_timeout, kernel32.WaitForSingleObject(child_handle, 0))

                job = host._windows_jobs[process]
                with mock.patch.object(
                    job,
                    "active_processes",
                    side_effect=OSError("injected Windows Job Object status query failure"),
                ), mock.patch.object(
                    job,
                    "terminate",
                    side_effect=OSError("injected Windows Job Object terminate cleanup failure"),
                ) as terminate:
                    with self.assertRaises(BaseException) as captured:
                        adapter._teardown_process(process)

                self.assertEqual(wait_object_0, kernel32.WaitForSingleObject(child_handle, 5000))
                terminate.assert_called_once_with(137)
                self.assertIsInstance(captured.exception, RuntimeError)
                self.assertIn(
                    "injected Windows Job Object status query failure",
                    str(captured.exception),
                )
                self.assertIn(
                    "terminate: injected Windows Job Object terminate cleanup failure",
                    str(captured.exception),
                )
                self.assertIsNone(job.handle)
                self.assertNotIn(process, host._windows_jobs)
            finally:
                if process is not None:
                    try:
                        host.terminate_tree(process)
                    except Exception:
                        pass
                if child_handle:
                    if kernel32.WaitForSingleObject(child_handle, 0) == wait_timeout:
                        kernel32.TerminateProcess(child_handle, 91)
                        kernel32.WaitForSingleObject(child_handle, 5000)
                    kernel32.CloseHandle(child_handle)

    def test_already_exited_first_host_fails_before_adapter_in_flight_admission(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-exited-before-admission-") as temp:
            root = Path(temp)
            host = _ScriptedCodexHost(already_exited_at=1, nonzero_at=1)
            adapter, execution_custody, isolated_root, provider_root = self._adapter_submission_fixture(
                root,
                host,
            )
            try:
                with self.assertRaisesRegex(RuntimeError, "exited before adapter in-flight admission"):
                    adapter.submit(execution_custody)
            finally:
                adapter.abort_all()

            self.assertEqual(1, len(host.starts))
            self.assertEqual([], host.processes[0].wait_timeouts)
            self.assertEqual(1, len(list(provider_root.glob("*.credential-scan.json"))))
            state = adapter.attempt_states()[0]
            self.assertEqual("DISPATCH_UNKNOWN", state["state"])
            diagnostic_ref = state["pre_admission_diagnostic"]
            self.assertEqual({"path", "byte_count", "sha256"}, set(diagnostic_ref))
            diagnostic_path = root / diagnostic_ref["path"]
            self.assertEqual(diagnostic_ref["byte_count"], diagnostic_path.stat().st_size)
            self.assertEqual(diagnostic_ref["sha256"], digest(diagnostic_path))
            diagnostic = json.loads(diagnostic_path.read_bytes())
            self.assertEqual(
                {
                    "schema", "status", "failure_kind", "candidate_id", "source_commit",
                    "package_sha256", "package_tree_sha256", "case_id", "model",
                    "reasoning_effort", "dispatch_classification", "admission_status",
                    "provider_invocation_proven", "host_returncode", "host_returncode_status",
                    "host_invocation_id", "started_at", "ended_at", "carrier_disposition", "source_presence",
                    "raw_event_log", "stderr", "raw_output", "credential_residue_scan",
                    "execution_custody_sha256", "execution_custody", "captured_at",
                },
                set(diagnostic),
            )
            self.assertEqual("reviewed-campaign-pre-admission-diagnostic-v1", diagnostic["schema"])
            self.assertEqual("PRE_ADMISSION_DIAGNOSTIC_RETAINED", diagnostic["status"])
            self.assertEqual("HOST_EXITED_BEFORE_ADMISSION", diagnostic["failure_kind"])
            self.assertEqual("DISPATCH_UNKNOWN", diagnostic["dispatch_classification"])
            self.assertEqual("NOT_ADMITTED", diagnostic["admission_status"])
            self.assertFalse(diagnostic["provider_invocation_proven"])
            self.assertEqual("RETAINED", diagnostic["carrier_disposition"])
            self.assertEqual(9, diagnostic["host_returncode"])
            self.assertEqual("RECORDED", diagnostic["host_returncode_status"])
            self.assertEqual(record_sha256(execution_custody), diagnostic["execution_custody_sha256"])
            self.assertEqual(
                {"raw_event_log": True, "stderr": True, "raw_output": False},
                diagnostic["source_presence"],
            )
            self.assertEqual(
                canonical({"type": "thread.started", "thread_id": "thread-01"})
                + canonical({"type": "turn.started"}),
                (root / diagnostic["raw_event_log"]["path"]).read_bytes(),
            )
            self.assertEqual(b"", (root / diagnostic["stderr"]["path"]).read_bytes())
            self.assertEqual(b"", (root / diagnostic["raw_output"]["path"]).read_bytes())
            scan_ref = diagnostic["credential_residue_scan"]
            self.assertEqual({"path", "byte_count", "sha256"}, set(scan_ref))
            scan_path = root / scan_ref["path"]
            self.assertEqual(provider_root.resolve(), scan_path.parent.resolve())
            self.assertEqual(scan_ref["byte_count"], scan_path.stat().st_size)
            self.assertEqual(scan_ref["sha256"], digest(scan_path))
            self.assertEqual(1, len(list(provider_root.glob("*.pre-admission-diagnostic.json"))))
            self.assertFalse(isolated_root.exists())

    def test_eventless_alive_first_host_cannot_yield_adapter_in_flight(self) -> None:
        import codex_live_producer_adapter as live_adapter

        class EventlessAliveHost(_ScriptedCodexHost):
            def start(self, *args: object, **kwargs: object) -> _CompletedCodexProcess:
                process = super().start(*args, **kwargs)
                event_log_path = kwargs["event_log_path"]
                output_path = kwargs["output_path"]
                assert isinstance(event_log_path, Path)
                assert isinstance(output_path, Path)
                event_log_path.write_bytes(b"")
                output_path.write_bytes(b"")
                return process

        with tempfile.TemporaryDirectory(prefix="daee-live-eventless-before-admission-") as temp:
            host = EventlessAliveHost()
            adapter, execution_custody, isolated_root, _provider_root = self._adapter_submission_fixture(
                Path(temp),
                host,
                timeout=1,
            )
            ticks = iter((100.0, 100.0, 101.0, 101.0))
            try:
                with mock.patch.object(
                    live_adapter.time,
                    "monotonic",
                    side_effect=lambda: next(ticks, 101.0),
                ), mock.patch.object(live_adapter.time, "sleep", return_value=None):
                    with self.assertRaisesRegex(RuntimeError, "structured.*admission"):
                        adapter.submit(execution_custody)
            finally:
                adapter.abort_all()

            self.assertEqual(1, len(host.starts))
            self.assertEqual("DISPATCH_UNKNOWN", adapter.attempt_states()[0]["state"])
            self.assertFalse(isolated_root.exists())

    def test_nonfinite_json_constants_cannot_yield_adapter_in_flight(self) -> None:
        class NonfiniteAdmissionHost(_ScriptedCodexHost):
            def __init__(self, literal: str) -> None:
                super().__init__()
                self.literal = literal

            def start(self, *args: object, **kwargs: object) -> _CompletedCodexProcess:
                process = super().start(*args, **kwargs)
                event_log_path = kwargs["event_log_path"]
                assert isinstance(event_log_path, Path)
                event_log_path.write_bytes(
                    b'{"type":"thread.started","thread_id":"thread-01","nonfinite_probe":'
                    + self.literal.encode("ascii")
                    + b"}\n"
                )
                return process

        for literal in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(literal=literal), tempfile.TemporaryDirectory(
                prefix="daee-live-nonfinite-admission-"
            ) as temp:
                host = NonfiniteAdmissionHost(literal)
                adapter, execution_custody, isolated_root, _provider_root = self._adapter_submission_fixture(
                    Path(temp),
                    host,
                    timeout=1,
                )
                try:
                    with self.assertRaisesRegex(RuntimeError, "non-finite"):
                        adapter.submit(execution_custody)
                finally:
                    adapter.abort_all()
                self.assertEqual("DISPATCH_UNKNOWN", adapter.attempt_states()[0]["state"])
                self.assertFalse(isolated_root.exists())

    def test_elapsed_launch_deadline_times_out_without_waiting_live_host(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-elapsed-deadline-") as temp:
            host = _ScriptedCodexHost()
            adapter, execution_custody, isolated_root, _provider_root = self._adapter_submission_fixture(
                Path(temp),
                host,
            )
            ticks = iter([100.0, 131.0])

            with mock.patch.object(live_adapter.time, "monotonic", side_effect=lambda: next(ticks)):
                handle = adapter.submit(execution_custody)["handle_id"]
                with self.assertRaisesRegex(RuntimeError, "producer command timed out"):
                    adapter.observe(str(handle), execution_custody)
            adapter.abort_all()

            self.assertEqual(1, len(host.starts))
            self.assertEqual([], host.processes[0].wait_timeouts)
            self.assertTrue(all(not process.owned_descendant_active for process in host.processes))
            self.assertEqual("OUTCOME_UNKNOWN", adapter.attempt_states()[0]["state"])
            self.assertFalse(isolated_root.exists())

    def test_observation_wait_receives_only_remaining_launch_budget(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(prefix="daee-live-remaining-deadline-") as temp:
            host = _ScriptedCodexHost()
            adapter, execution_custody, isolated_root, _provider_root = self._adapter_submission_fixture(
                Path(temp),
                host,
            )
            ticks = iter([100.0, 112.0])

            with mock.patch.object(live_adapter.time, "monotonic", side_effect=lambda: next(ticks)):
                handle = adapter.submit(execution_custody)["handle_id"]
                result = adapter.observe(str(handle), execution_custody)

            self.assertEqual([18.0], host.processes[0].wait_timeouts)
            self.assertEqual("CAPTURED", result["capture_status"])
            self.assertEqual("COMPLETED", adapter.attempt_states()[0]["state"])
            self.assertFalse(isolated_root.exists())

    def test_post_execution_credential_residue_is_purged_and_terminalized_fail_closed(self) -> None:
        from codex_live_producer_adapter import CodexLiveProducerAdapter
        token = "fixture-access-token-never-retain"
        for encoding in ("utf-8", "utf-16-le", "utf-16-be"):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory(prefix="daee-live-residue-") as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
                host = _ScriptedCodexHost(credential_residue_at=1, credential_residue_encoding=encoding)
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root, codex_executable=executable,
                    host=host, command_timeout_seconds=30, fixture_token=token,
                )
                with self.assertRaisesRegex(CampaignError, "access credential residue"):
                    run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
                self.assertFalse((fixture.root / "producer/isolated/producer-01").exists())
                retained = b"\n".join(path.read_bytes() for path in fixture.root.rglob("*") if path.is_file())
                self.assertNotIn(token.encode(encoding), retained)
                head = validate_head(fixture.root / "usage")
                terminal = json.loads((fixture.root / "usage/transactions" / f"{head['last_transaction_sha256']}.json").read_text())
                self.assertEqual((4, 1, 0), (terminal["completed"], terminal["unknown"], terminal["not_dispatched"]))
                finalizer = json.loads((fixture.root / "producer/observation-finalizer.json").read_text())
                self.assertEqual(4, len(finalizer["observed_results"]))

    def test_scan_unavailable_purges_worker_and_preserves_unknown_terminalization(self) -> None:
        import codex_live_producer_adapter as live_adapter
        with tempfile.TemporaryDirectory(prefix="daee-live-scan-unavailable-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root, codex_executable=executable,
                host=host,
            )
            original = live_adapter._scan_private_worker_for_credential

            def fail_first(worker_root: Path, credential: str) -> dict[str, int]:
                if worker_root.name == "producer-01":
                    raise OSError("injected credential scan readback failure")
                return original(worker_root, credential)

            with mock.patch.object(live_adapter, "_scan_private_worker_for_credential", side_effect=fail_first):
                with self.assertRaisesRegex(CampaignError, "credential residue scan failed closed"):
                    run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
            self.assertFalse((fixture.root / "producer/isolated/producer-01").exists())
            head = validate_head(fixture.root / "usage")
            terminal = json.loads((fixture.root / "usage/transactions" / f"{head['last_transaction_sha256']}.json").read_text())
            self.assertEqual((4, 1, 0), (terminal["completed"], terminal["unknown"], terminal["not_dispatched"]))
            self.assertTrue((fixture.root / "producer/observation-finalizer.json").is_file())

    def test_secondary_worker_abort_residue_cannot_bypass_cohort_terminalization(self) -> None:
        from codex_live_producer_adapter import CodexLiveProducerAdapter
        with tempfile.TemporaryDirectory(prefix="daee-live-secondary-abort-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost(nonzero_at=1, credential_residue_at=2, credential_residue_encoding="utf-16-be")
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root, codex_executable=executable,
                host=host,
            )
            with self.assertRaises(CampaignError):
                run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
            self.assertFalse((fixture.root / "producer/isolated/producer-02").exists())
            head = validate_head(fixture.root / "usage")
            terminal = json.loads((fixture.root / "usage/transactions" / f"{head['last_transaction_sha256']}.json").read_text())
            self.assertEqual((3, 2, 0), (terminal["completed"], terminal["unknown"], terminal["not_dispatched"]))
            finalizer = json.loads((fixture.root / "producer/observation-finalizer.json").read_text())
            self.assertEqual(3, len(finalizer["observed_results"]))
            self.assertEqual("OUTCOME_UNKNOWN", finalizer["dispatch_classification"])

    def test_live_capability_failure_is_preclaim_and_zero_dispatch(self) -> None:
        try:
            from codex_live_producer_adapter import CodexLiveProducerAdapter
        except ModuleNotFoundError as exc:
            self.fail(f"live producer adapter is missing: {exc}")
        with tempfile.TemporaryDirectory(prefix="daee-live-producer-probe-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost(fail_probe=True)
            adapter = CodexLiveProducerAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                access_token="fixture-access-token-never-retain",
                host=host,
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(CampaignError, "PROVIDER_CAPABILITY_UNAVAILABLE"):
                run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
            self.assertEqual([("probe", executable.name)], host.log)
            self.assertFalse((fixture.root / "claims").exists())
            self.assertFalse((fixture.root / "producer/isolated").exists())

    def test_authorized_command_timeout_mismatch_is_preclaim_and_reservation_free(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-timeout-mismatch-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=31,
            )
            with self.assertRaisesRegex(
                CampaignError,
                "LIVE_PROVIDER_COMMAND_TIMEOUT_MISMATCH",
            ):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )
            self.assertFalse((fixture.root / "claims").exists())
            self.assertEqual(0, validate_head(fixture.root / "usage")["sequence"])
            self.assertEqual([("probe", executable.name)], host.log)
            self.assertFalse((fixture.root / "producer/isolated").exists())

    def test_execution_custody_command_timeout_substitution_fails_before_host_start(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-live-timeout-custody-") as temp:
            host = _ScriptedCodexHost()
            adapter, execution_custody, isolated_root, _provider_root = self._adapter_submission_fixture(
                Path(temp),
                host,
            )
            execution_custody["provider_settings"]["command_timeout_seconds"] = 31
            try:
                with self.assertRaisesRegex(RuntimeError, "live command timeout custody drift"):
                    adapter.submit(execution_custody)
            finally:
                adapter.abort_all()
            self.assertEqual([], host.starts)
            self.assertFalse(isolated_root.exists())

    def test_live_parent_and_usage_predecessor_are_preclaim_authority(self) -> None:
        from codex_live_producer_adapter import CodexLiveProducerAdapter
        for mutation, marker in (("parent-revoked", "MATRIX_AUTHORIZATION_INVALID: campaign_authorization_contract"), ("usage-head-drift", "EXPECTED_CAMPAIGN_USAGE_HEAD_DRIFT")):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix="daee-live-authority-") as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
                matrix = json.loads(authorization.read_text(encoding="utf-8"))
                if mutation == "parent-revoked":
                    parent_path = fixture.root / matrix["campaign_authorization"]["path"]
                    parent = json.loads(parent_path.read_text(encoding="utf-8"))
                    parent["status"] = "REVOKED"
                    parent["authorization_sha256"] = record_sha256({key: value for key, value in parent.items() if key != "authorization_sha256"})
                    write_json(parent_path, parent)
                    matrix["campaign_authorization"]["sha256"] = digest(parent_path)
                    matrix["campaign_authorization_sha256"] = digest(parent_path)
                else:
                    matrix["expected_campaign_usage_sequence"] += 1
                matrix["authorization_sha256"] = record_sha256({key: value for key, value in matrix.items() if key != "authorization_sha256"})
                write_json(authorization, matrix)
                host = _ScriptedCodexHost()
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root, codex_executable=executable,
                    host=host, command_timeout_seconds=30,
                )
                with self.assertRaisesRegex(CampaignError, marker):
                    run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
                self.assertFalse((fixture.root / "claims").exists())
                self.assertEqual([("probe", executable.name)], host.log)

    def test_private_candidate_copy_drift_fails_before_claim_and_is_cleaned(self) -> None:
        import codex_live_producer_adapter as live_adapter
        with tempfile.TemporaryDirectory(prefix="daee-live-copy-drift-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root, codex_executable=executable,
                host=host, command_timeout_seconds=30,
            )
            original_copy = live_adapter._copy_tree_exact

            def tampering_copy(source: Path, destination: Path) -> None:
                original_copy(source, destination)
                (destination / "SKILL.md").write_bytes((destination / "SKILL.md").read_bytes() + b"drift")

            with mock.patch.object(live_adapter, "_copy_tree_exact", side_effect=tampering_copy):
                with self.assertRaisesRegex(CampaignError, "private candidate package copy drift"):
                    run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
            self.assertFalse((fixture.root / "claims").exists())
            self.assertFalse((fixture.root / "producer/isolated").exists())
            self.assertEqual([("probe", executable.name)], host.log)

    def test_mixed_failure_replay_requires_every_completed_receipt_result(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-live-mixed-result-replay-") as temp:
            fixture, _authorization, incident, payload, auth, auth_sha, bindings = (
                self._live_failure_replay_validation_inputs(
                    Path(temp),
                    host_args={"nonzero_at": 3},
                )
            )
            self.assertEqual(4, len(payload["observed_results"]))
            orchestrator._validate_failure_resume_payload(
                fixture.root,
                fixture.root / auth["usage_ledger_root"],
                incident,
                payload,
                auth,
                auth_sha,
                bindings,
                lane="producer",
                attempt_index=1,
            )
            payload["observed_results"] = []
            incident["observed_result_count"] = 0
            with self.assertRaisesRegex(CampaignError, "COMPLETED_RECEIPTS"):
                orchestrator._validate_failure_resume_payload(
                    fixture.root,
                    fixture.root / auth["usage_ledger_root"],
                    incident,
                    payload,
                    auth,
                    auth_sha,
                    bindings,
                    lane="producer",
                    attempt_index=1,
                )

    def test_mixed_failure_replay_classification_is_derived_from_unknown_receipts(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        scenarios = [
            ({"nonzero_at": 3}, "OUTCOME_UNKNOWN", "DISPATCH_UNKNOWN"),
            ({"fail_start_at": 1}, "DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN"),
        ]
        for host_args, recorded, substituted in scenarios:
            with self.subTest(recorded=recorded, substituted=substituted), tempfile.TemporaryDirectory(
                prefix="daee-live-classification-replay-"
            ) as temp:
                fixture, _authorization, incident, payload, auth, auth_sha, bindings = (
                    self._live_failure_replay_validation_inputs(
                        Path(temp),
                        host_args=host_args,
                    )
                )
                self.assertEqual(recorded, payload["dispatch_classification"])
                orchestrator._validate_failure_resume_payload(
                    fixture.root,
                    fixture.root / auth["usage_ledger_root"],
                    incident,
                    payload,
                    auth,
                    auth_sha,
                    bindings,
                    lane="producer",
                    attempt_index=1,
                )
                payload["dispatch_classification"] = substituted
                payload["dispatch_status"] = substituted
                incident["dispatch_classification"] = substituted
                with self.assertRaisesRegex(CampaignError, "CLASSIFICATION_RECEIPTS"):
                    orchestrator._validate_failure_resume_payload(
                        fixture.root,
                        fixture.root / auth["usage_ledger_root"],
                        incident,
                        payload,
                        auth,
                        auth_sha,
                        bindings,
                        lane="producer",
                        attempt_index=1,
                    )

    def test_pre_admission_diagnostic_is_bound_into_terminal_failure_and_replay(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-live-pre-admission-terminal-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost(already_exited_at=1, nonzero_at=1)
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(CampaignError, "PROVIDER_EXECUTION_FAILED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            incident_path = fixture.root / "incidents/producer-live-cycle-01.json"
            finalizer_path = fixture.root / "producer/observation-finalizer.json"
            incident = json.loads(incident_path.read_bytes())
            finalizer = json.loads(finalizer_path.read_bytes())
            diagnostics = finalizer["pre_admission_diagnostics"]
            self.assertEqual(diagnostics, incident["finalizer_payload"]["pre_admission_diagnostics"])
            self.assertEqual(1, len(diagnostics))
            diagnostic_ref = diagnostics[0]
            diagnostic_path = fixture.root / diagnostic_ref["path"]
            diagnostic = json.loads(diagnostic_path.read_bytes())
            self.assertEqual(CASES[0], diagnostic["case_id"])
            self.assertEqual("DISPATCH_UNKNOWN", diagnostic["dispatch_classification"])
            self.assertEqual("HOST_EXITED_BEFORE_ADMISSION", diagnostic["failure_kind"])
            self.assertEqual(9, diagnostic["host_returncode"])
            self.assertFalse(diagnostic["provider_invocation_proven"])

            auth, auth_sha = orchestrator._load_producer_authorization(
                fixture.root,
                authorization,
                require_active_window=False,
                allow_test_fixture=True,
            )
            bindings = orchestrator._validate_common_bindings(
                fixture.root,
                auth,
                allow_test_fixture=True,
            )
            orchestrator._validate_failure_resume_payload(
                fixture.root,
                fixture.root / auth["usage_ledger_root"],
                incident,
                incident["finalizer_payload"],
                auth,
                auth_sha,
                bindings,
                lane="producer",
                attempt_index=1,
            )

            role_swapped_diagnostic = copy.deepcopy(diagnostic)
            role_swapped_diagnostic["stderr"], role_swapped_diagnostic["raw_output"] = (
                role_swapped_diagnostic["raw_output"],
                role_swapped_diagnostic["stderr"],
            )
            role_swapped_raw = canonical(role_swapped_diagnostic)
            role_swapped_path = diagnostic_path.parent / (
                f"{hashlib.sha256(role_swapped_raw).hexdigest()}.pre-admission-diagnostic.json"
            )
            role_swapped_path.write_bytes(role_swapped_raw)
            role_swapped_payload = copy.deepcopy(incident["finalizer_payload"])
            role_swapped_payload["pre_admission_diagnostics"] = [
                ref(fixture.root, role_swapped_path)
            ]
            role_swapped_incident = copy.deepcopy(incident)
            role_swapped_incident["finalizer_payload"] = role_swapped_payload
            with self.assertRaisesRegex(
                CampaignError,
                "TERMINAL_PUBLICATION_PREFLIGHT_PRE_ADMISSION_DIAGNOSTIC_CARRIERS",
            ):
                orchestrator._validate_failure_resume_payload(
                    fixture.root,
                    fixture.root / auth["usage_ledger_root"],
                    role_swapped_incident,
                    role_swapped_payload,
                    auth,
                    auth_sha,
                    bindings,
                    lane="producer",
                    attempt_index=1,
                )

            diagnostic_path.write_bytes(b"substituted pre-admission diagnostic\n")
            with self.assertRaisesRegex(CampaignError, "PRE_ADMISSION_DIAGNOSTIC"):
                orchestrator._validate_failure_resume_payload(
                    fixture.root,
                    fixture.root / auth["usage_ledger_root"],
                    incident,
                    incident["finalizer_payload"],
                    auth,
                    auth_sha,
                    bindings,
                    lane="producer",
                    attempt_index=1,
                )

    def test_pre_admission_credential_residue_purges_raw_carriers_and_terminalizes(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        token = "fixture-access-token-never-retain"
        with tempfile.TemporaryDirectory(prefix="daee-live-pre-admission-residue-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost(
                already_exited_at=1,
                nonzero_at=1,
                credential_residue_at=1,
            )
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
                fixture_token=token,
            )
            with self.assertRaisesRegex(CampaignError, "access credential residue"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            worker_root = fixture.root / "producer/isolated/producer-01"
            self.assertFalse(worker_root.exists())
            retained = b"\n".join(
                path.read_bytes()
                for path in fixture.root.rglob("*")
                if path.is_file()
            )
            self.assertNotIn(token.encode("utf-8"), retained)

            head = validate_head(fixture.root / "usage")
            self.assertFalse(head["open_reservations"])
            self.assertTrue(head["unresolved_usage"])
            self.assertEqual(0, head["totals"]["attempted"])
            self.assertEqual(0, head["totals"]["producer_invocations"])
            self.assertEqual(1, head["totals"]["unknown"])
            self.assertEqual(4, head["totals"]["not_dispatched"])
            settlement = json.loads(
                (
                    fixture.root
                    / "usage/transactions"
                    / f"{head['last_transaction_sha256']}.json"
                ).read_bytes()
            )
            self.assertEqual(
                (0, 1, 4),
                (
                    settlement["completed"],
                    settlement["unknown"],
                    settlement["not_dispatched"],
                ),
            )

            incident_path = fixture.root / "incidents/producer-live-cycle-01.json"
            finalizer_path = fixture.root / "producer/observation-finalizer.json"
            incident = json.loads(incident_path.read_bytes())
            finalizer = json.loads(finalizer_path.read_bytes())
            diagnostics = finalizer["pre_admission_diagnostics"]
            self.assertEqual(
                diagnostics,
                incident["finalizer_payload"]["pre_admission_diagnostics"],
            )
            self.assertEqual(1, len(diagnostics))
            diagnostic_path = fixture.root / diagnostics[0]["path"]
            diagnostic = json.loads(diagnostic_path.read_bytes())
            self.assertEqual("PRE_ADMISSION_DIAGNOSTIC_RETAINED", diagnostic["status"])
            self.assertEqual("PURGED_UNRETAINED", diagnostic["carrier_disposition"])
            self.assertEqual(
                {"raw_event_log": False, "stderr": False, "raw_output": False},
                diagnostic["source_presence"],
            )
            for role in ("raw_event_log", "stderr", "raw_output"):
                self.assertEqual(b"", (fixture.root / diagnostic[role]["path"]).read_bytes())
            scan = json.loads(
                (fixture.root / diagnostic["credential_residue_scan"]["path"]).read_bytes()
            )
            self.assertEqual("FAIL_CLOSED", scan["status"])
            self.assertEqual("CREDENTIAL_RESIDUE", scan["failure_class"])
            self.assertEqual("OWNED_WORKER_PURGED", scan["cleanup_status"])

            auth, auth_sha = orchestrator._load_producer_authorization(
                fixture.root,
                authorization,
                require_active_window=False,
                allow_test_fixture=True,
            )
            bindings = orchestrator._validate_common_bindings(
                fixture.root,
                auth,
                allow_test_fixture=True,
            )
            orchestrator._validate_failure_resume_payload(
                fixture.root,
                fixture.root / auth["usage_ledger_root"],
                incident,
                incident["finalizer_payload"],
                auth,
                auth_sha,
                bindings,
                lane="producer",
                attempt_index=1,
            )
            mutations: list[tuple[dict[str, object], str]] = []
            wrong_disposition = copy.deepcopy(diagnostic)
            wrong_disposition["carrier_disposition"] = "RETAINED"
            mutations.append((wrong_disposition, "PRE_ADMISSION_DIAGNOSTIC_CREDENTIAL_SCAN"))
            role_swapped = copy.deepcopy(diagnostic)
            role_swapped["stderr"], role_swapped["raw_output"] = (
                role_swapped["raw_output"],
                role_swapped["stderr"],
            )
            mutations.append((role_swapped, "PRE_ADMISSION_DIAGNOSTIC_CARRIERS"))
            for mutated_diagnostic, expected_error in mutations:
                mutated_raw = canonical(mutated_diagnostic)
                mutated_path = diagnostic_path.parent / (
                    f"{hashlib.sha256(mutated_raw).hexdigest()}.pre-admission-diagnostic.json"
                )
                mutated_path.write_bytes(mutated_raw)
                mutated_payload = copy.deepcopy(incident["finalizer_payload"])
                mutated_payload["pre_admission_diagnostics"] = [
                    ref(fixture.root, mutated_path)
                ]
                mutated_incident = copy.deepcopy(incident)
                mutated_incident["finalizer_payload"] = mutated_payload
                with self.assertRaisesRegex(CampaignError, expected_error):
                    orchestrator._validate_failure_resume_payload(
                        fixture.root,
                        fixture.root / auth["usage_ledger_root"],
                        mutated_incident,
                        mutated_payload,
                        auth,
                        auth_sha,
                        bindings,
                        lane="producer",
                        attempt_index=1,
                    )
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

    def test_nonfirst_pre_admission_credential_purge_binds_actual_worker_identity(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        token = "fixture-access-token-never-retain"
        with tempfile.TemporaryDirectory(prefix="daee-live-nonfirst-pre-admission-residue-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost(
                already_exited_at=2,
                nonzero_at=2,
                credential_residue_at=2,
            )
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
                fixture_token=token,
            )
            with self.assertRaises(CampaignError):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            self.assertFalse((fixture.root / "producer/isolated/producer-02").exists())
            retained = b"\n".join(
                path.read_bytes()
                for path in fixture.root.rglob("*")
                if path.is_file()
            )
            self.assertNotIn(token.encode("utf-8"), retained)
            head = validate_head(fixture.root / "usage")
            self.assertFalse(head["open_reservations"])
            self.assertTrue(head["unresolved_usage"])
            self.assertEqual(5, head["totals"]["unknown"])
            self.assertEqual(0, head["totals"]["not_dispatched"])

            incident = json.loads(
                (fixture.root / "incidents/producer-live-cycle-01.json").read_bytes()
            )
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_bytes()
            )
            diagnostics = [
                (reference, json.loads((fixture.root / reference["path"]).read_bytes()))
                for reference in finalizer["pre_admission_diagnostics"]
            ]
            purged = [
                (reference, diagnostic)
                for reference, diagnostic in diagnostics
                if diagnostic["carrier_disposition"] == "PURGED_UNRETAINED"
            ]
            self.assertEqual(1, len(purged))
            diagnostic_reference, diagnostic = purged[0]
            scan = json.loads(
                (fixture.root / diagnostic["credential_residue_scan"]["path"]).read_bytes()
            )
            self.assertEqual("producer-02", scan["worker"])

            auth, auth_sha = orchestrator._load_producer_authorization(
                fixture.root,
                authorization,
                require_active_window=False,
                allow_test_fixture=True,
            )
            bindings = orchestrator._validate_common_bindings(
                fixture.root,
                auth,
                allow_test_fixture=True,
            )
            orchestrator._validate_failure_resume_payload(
                fixture.root,
                fixture.root / auth["usage_ledger_root"],
                incident,
                incident["finalizer_payload"],
                auth,
                auth_sha,
                bindings,
                lane="producer",
                attempt_index=1,
            )
            scan_mutations: list[tuple[str, dict[str, object]]] = []
            wrong_worker_scan = copy.deepcopy(scan)
            wrong_worker_scan["worker"] = "producer-01"
            scan_mutations.append(("wrong-worker", wrong_worker_scan))
            extra_field_scan = copy.deepcopy(scan)
            extra_field_scan["unexpected_payload"] = "must-not-survive"
            scan_mutations.append(("extra-field", extra_field_scan))
            malformed_time_scan = copy.deepcopy(scan)
            malformed_time_scan["completed_at"] = "not-a-utc-time"
            scan_mutations.append(("malformed-time", malformed_time_scan))
            for mutation_name, mutated_scan in scan_mutations:
                with self.subTest(mutation=mutation_name):
                    mutated_scan_raw = canonical(mutated_scan)
                    mutated_scan_path = (
                        fixture.root / diagnostic["credential_residue_scan"]["path"]
                    ).parent / (
                        f"{hashlib.sha256(mutated_scan_raw).hexdigest()}.credential-scan.json"
                    )
                    mutated_scan_path.write_bytes(mutated_scan_raw)
                    mutated_diagnostic = copy.deepcopy(diagnostic)
                    mutated_diagnostic["credential_residue_scan"] = ref(
                        fixture.root,
                        mutated_scan_path,
                    )
                    mutated_diagnostic_raw = canonical(mutated_diagnostic)
                    mutated_diagnostic_path = (
                        fixture.root / diagnostic_reference["path"]
                    ).parent / (
                        f"{hashlib.sha256(mutated_diagnostic_raw).hexdigest()}"
                        ".pre-admission-diagnostic.json"
                    )
                    mutated_diagnostic_path.write_bytes(mutated_diagnostic_raw)
                    mutated_payload = copy.deepcopy(incident["finalizer_payload"])
                    mutated_payload["pre_admission_diagnostics"] = [
                        ref(fixture.root, mutated_diagnostic_path)
                        if reference == diagnostic_reference
                        else reference
                        for reference in finalizer["pre_admission_diagnostics"]
                    ]
                    mutated_incident = copy.deepcopy(incident)
                    mutated_incident["finalizer_payload"] = mutated_payload
                    with self.assertRaisesRegex(
                        CampaignError,
                        "PRE_ADMISSION_DIAGNOSTIC_CREDENTIAL_SCAN",
                    ):
                        orchestrator._validate_failure_resume_payload(
                            fixture.root,
                            fixture.root / auth["usage_ledger_root"],
                            mutated_incident,
                            mutated_payload,
                            auth,
                            auth_sha,
                            bindings,
                            lane="producer",
                            attempt_index=1,
                        )
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

    def test_live_partial_failures_preserve_exact_call_state_and_verify_teardown(self) -> None:
        from codex_live_producer_adapter import CodexLiveProducerAdapter
        scenarios = [
            ({"fail_after_start_at": 3}, 0, 3, 2, RuntimeError),
            ({"nonzero_at": 3}, 4, 1, 0, RuntimeError),
            ({"timeout_at": 2}, 4, 1, 0, RuntimeError),
            ({"interrupt_at": 2}, 4, 1, 0, KeyboardInterrupt),
        ]
        for host_args, completed, unknown, not_dispatched, error_type in scenarios:
            with self.subTest(host_args=host_args), tempfile.TemporaryDirectory(prefix="daee-live-partial-") as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(
                    Path(temp),
                    command_timeout_seconds=1,
                )
                host = _ScriptedCodexHost(**host_args)
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root, codex_executable=executable,
                    host=host,
                    command_timeout_seconds=1,
                )
                with self.assertRaises(error_type):
                    run_producer_cohort(fixture.root, authorization, adapter, allow_test_fixture=True)
                head = validate_head(fixture.root / "usage")
                terminal = json.loads((fixture.root / "usage/transactions" / f"{head['last_transaction_sha256']}.json").read_text())
                self.assertEqual((completed, unknown, not_dispatched), (terminal["completed"], terminal["unknown"], terminal["not_dispatched"]))
                finalizer = json.loads((fixture.root / "producer/observation-finalizer.json").read_text())
                self.assertEqual(completed, len(finalizer.get("observed_results", [])))
                started_pids = {1000 + index for index in range(1, len(host.starts) + 1)}
                self.assertTrue(started_pids.issubset(set(host.verified)), (started_pids, host.verified))
                self.assertTrue(all(not process.owned_descendant_active for process in host.processes))
                replay_host = _ScriptedCodexHost()
                replay_adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=replay_host,
                    command_timeout_seconds=1,
                )
                with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        replay_adapter,
                        allow_test_fixture=True,
                    )
                self.assertEqual([], replay_host.starts)


    def test_structured_admission_requires_thread_started_before_any_turn_or_terminal_event(self) -> None:
        class OrderedAdmissionHost(_ScriptedCodexHost):
            def __init__(self, preceding_event: dict[str, object]) -> None:
                super().__init__()
                self.preceding_event = preceding_event

            def start(self, *args: object, **kwargs: object) -> _CompletedCodexProcess:
                process = super().start(*args, **kwargs)
                event_log_path = kwargs["event_log_path"]
                assert isinstance(event_log_path, Path)
                event_log_path.write_bytes(
                    canonical(self.preceding_event)
                    + canonical({"type": "thread.started", "thread_id": "thread-01"})
                )
                return process

        preceding_events = (
            ("turn-started", {"type": "turn.started"}),
            (
                "turn-completed",
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 1,
                        "cached_input_tokens": 0,
                        "output_tokens": 1,
                    },
                },
            ),
            ("turn-failed", {"type": "turn.failed", "message": "fixture failure"}),
            ("error", {"type": "error", "message": "fixture error"}),
        )
        for event_name, preceding_event in preceding_events:
            with self.subTest(preceding_event=event_name), tempfile.TemporaryDirectory(
                prefix=f"daee-live-{event_name}-before-thread-"
            ) as temp:
                host = OrderedAdmissionHost(preceding_event)
                adapter, execution_custody, _isolated_root, _provider_root = (
                    self._adapter_submission_fixture(Path(temp), host)
                )
                try:
                    with self.assertRaises(RuntimeError):
                        adapter.submit(execution_custody)
                finally:
                    adapter.abort_all()

    def test_partial_observer_submission_quiesces_submitted_waiters_and_terminalizes_all_cases(self) -> None:
        import codex_live_producer_adapter as live_adapter
        from concurrent.futures import Future

        class PartiallySubmittingExecutor:
            def __init__(self) -> None:
                self.futures: list[Future[int]] = []
                self.shutdown_calls: list[tuple[bool, bool]] = []

            def submit(self, function: object, *args: object) -> Future[int]:
                if len(self.futures) == 2:
                    raise RuntimeError("injected observer submission failure after 2 futures")
                future: Future[int] = Future()
                self.futures.append(future)
                return future

            def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
                self.shutdown_calls.append((wait, cancel_futures))
                if cancel_futures:
                    for future in self.futures:
                        future.cancel()

        with tempfile.TemporaryDirectory(prefix="daee-live-partial-observer-submit-") as temp:
            fixture, authorization, executable, _skill_bytes = (
                self._live_fixture(Path(temp))
            )
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            executor = PartiallySubmittingExecutor()
            with mock.patch.object(live_adapter, "ThreadPoolExecutor", return_value=executor):
                with self.assertRaisesRegex(
                    CampaignError,
                    "observer submission failure after 2 futures",
                ):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            head = validate_head(fixture.root / "usage")
            self.assertFalse(head["open_reservations"])
            self.assertEqual(
                (0, 5, 0),
                (
                    head["totals"]["completed"],
                    head["totals"]["unknown"],
                    head["totals"]["not_dispatched"],
                ),
            )
            settlement = json.loads(
                (
                    fixture.root
                    / "usage/transactions"
                    / f"{head['last_transaction_sha256']}.json"
                ).read_bytes()
            )
            self.assertEqual(
                CASES,
                [row["case_id"] for row in settlement["provider_usage_receipts"]],
            )
            self.assertEqual(
                ["OUTCOME_UNKNOWN"] * 5,
                [row["unknown_kind"] for row in settlement["provider_usage_receipts"]],
            )
            self.assertTrue(
                executor.shutdown_calls,
                "partial observer submission left already-submitted waiters unquiesced",
            )
            self.assertTrue(all(future.cancelled() for future in executor.futures))

    def test_simultaneous_observation_failures_preserve_each_case_cause(self) -> None:
        class SimultaneousFailureHost(_ScriptedCodexHost):
            def __init__(self) -> None:
                super().__init__()
                self.wait_barrier = threading.Barrier(5)
                self.failure_markers: list[str] = []

            def start(self, *args: object, **kwargs: object) -> _CompletedCodexProcess:
                process = super().start(*args, **kwargs)
                ordinal = len(self.starts)
                worker = str(kwargs["worker"])
                marker = f"{CASES[ordinal - 1]}=terminal-cause-{worker}"
                self.failure_markers.append(marker)

                def wait(timeout: float | None = None) -> int:
                    self.log.append(("observe", worker))
                    process.wait_timeouts.append(timeout)
                    self.wait_barrier.wait(timeout=2)
                    raise RuntimeError(marker)

                process.wait = wait  # type: ignore[method-assign]
                return process

        with tempfile.TemporaryDirectory(prefix="daee-live-simultaneous-observer-failures-") as temp:
            fixture, authorization, executable, _skill_bytes = (
                self._live_fixture(Path(temp))
            )
            host = SimultaneousFailureHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(CampaignError, "PROVIDER_EXECUTION_FAILED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            expected_causes = dict(zip(CASES, host.failure_markers))
            retained_causes = {
                row["case_id"]: row.get("terminal_cause")
                for row in adapter.attempt_states()
            }
            self.assertEqual(
                expected_causes,
                retained_causes,
                "scheduler-selected first failure discarded distinct per-case terminal causes",
            )

    def test_pre_admission_cleanup_failures_totalize_with_external_secret_free_witness(self) -> None:
        import codex_live_producer_adapter as live_adapter

        class TeardownStatusFailureHost(_ScriptedCodexHost):
            def verify_tree_stopped(self, process: _CompletedCodexProcess) -> bool:
                self.verified.append(process.pid)
                raise RuntimeError("injected process-tree status failure")

        for failure_mode in ("process-teardown", "scan-and-purge"):
            with self.subTest(failure_mode=failure_mode), tempfile.TemporaryDirectory(
                prefix=f"daee-live-cleanup-totality-{failure_mode}-"
            ) as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
                host = (
                    TeardownStatusFailureHost(already_exited_at=1, nonzero_at=1)
                    if failure_mode == "process-teardown"
                    else _ScriptedCodexHost(
                        already_exited_at=1,
                        nonzero_at=1,
                        credential_residue_at=1,
                    )
                )
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=host,
                    command_timeout_seconds=30,
                    fixture_token="fixture-access-token-never-retain",
                )

                if failure_mode == "process-teardown":
                    with self.assertRaises(CampaignError):
                        run_producer_cohort(
                            fixture.root,
                            authorization,
                            adapter,
                            allow_test_fixture=True,
                        )
                    expected_failure_kind = "PROCESS_TEARDOWN_UNVERIFIED"
                    expected_residual_kind = "PROCESS_GENERATION"
                else:
                    original_scan = live_adapter._scan_private_worker_for_credential
                    original_rmtree = live_adapter.shutil.rmtree

                    def fail_first_scan(worker_root: Path, credential: str) -> dict[str, int]:
                        if worker_root.name == "producer-01":
                            raise OSError("injected credential scan failure")
                        return original_scan(worker_root, credential)

                    def fail_first_purge(path: object, *args: object, **kwargs: object) -> None:
                        if Path(path).name == "producer-01":
                            raise OSError("injected owned-worker purge failure")
                        original_rmtree(path, *args, **kwargs)

                    with mock.patch.object(
                        live_adapter,
                        "_scan_private_worker_for_credential",
                        side_effect=fail_first_scan,
                    ), mock.patch.object(
                        live_adapter.shutil,
                        "rmtree",
                        side_effect=fail_first_purge,
                    ):
                        with self.assertRaises(CampaignError):
                            run_producer_cohort(
                                fixture.root,
                                authorization,
                                adapter,
                                allow_test_fixture=True,
                            )
                    expected_failure_kind = "CREDENTIAL_SCAN_AND_PURGE_FAILED"
                    expected_residual_kind = "OWNED_WORKER"

                head = validate_head(fixture.root / "usage")
                self.assertEqual([], head["open_reservations"])
                self.assertTrue(head["unresolved_usage"])
                self.assertEqual(0, head["totals"]["attempted"])
                self.assertEqual(0, head["totals"]["producer_invocations"])
                self.assertEqual(1, head["totals"]["unknown"])
                self.assertEqual(4, head["totals"]["not_dispatched"])
                settlement = json.loads(
                    (
                        fixture.root
                        / "usage/transactions"
                        / f"{head['last_transaction_sha256']}.json"
                    ).read_bytes()
                )
                self.assertEqual(
                    (0, 1, 4),
                    (
                        settlement["completed"],
                        settlement["unknown"],
                        settlement["not_dispatched"],
                    ),
                )

                incident = json.loads(
                    (fixture.root / "incidents/producer-live-cycle-01.json").read_bytes()
                )
                finalizer = json.loads(
                    (fixture.root / "producer/observation-finalizer.json").read_bytes()
                )
                self.assertEqual("DISPATCH_UNKNOWN", finalizer["dispatch_classification"])
                self.assertEqual(
                    finalizer["pre_admission_diagnostics"],
                    incident["finalizer_payload"]["pre_admission_diagnostics"],
                )
                self.assertEqual(1, len(finalizer["pre_admission_diagnostics"]))
                diagnostic_ref = finalizer["pre_admission_diagnostics"][0]
                diagnostic_path = fixture.root / diagnostic_ref["path"]
                self.assertEqual(diagnostic_ref, ref(fixture.root, diagnostic_path))
                diagnostic = json.loads(diagnostic_path.read_bytes())
                self.assertEqual("UNAVAILABLE", diagnostic["carrier_disposition"])
                self.assertEqual(
                    {"raw_event_log": False, "stderr": False, "raw_output": False},
                    diagnostic["source_presence"],
                )
                for role in ("raw_event_log", "stderr", "raw_output"):
                    carrier_path = fixture.root / diagnostic[role]["path"]
                    self.assertEqual(diagnostic[role], ref(fixture.root, carrier_path))
                    self.assertEqual(b"", carrier_path.read_bytes())
                self.assertIsNone(diagnostic["credential_residue_scan"])

                witness_ref = diagnostic["cleanup_residual_witness"]
                witness_path = fixture.root / witness_ref["path"]
                self.assertEqual(witness_ref, ref(fixture.root, witness_path))
                self.assertFalse(
                    witness_path.relative_to(fixture.root).as_posix().startswith("producer/isolated/")
                )
                witness_raw = witness_path.read_bytes()
                witness = json.loads(witness_raw)
                self.assertEqual("reviewed-campaign-cleanup-residual-witness-v1", witness["schema"])
                self.assertEqual("CLEANUP_INCOMPLETE", witness["status"])
                self.assertEqual(expected_failure_kind, witness["failure_kind"])
                self.assertEqual(expected_residual_kind, witness["residual_kind"])
                self.assertEqual(CASES[0], witness["case_id"])
                self.assertEqual("producer-01", witness["worker"])
                self.assertEqual(
                    diagnostic["execution_custody_sha256"],
                    witness["execution_custody_sha256"],
                )
                self.assertFalse(witness["retained_original_carriers"])
                self.assertNotIn(b"fixture-access-token-never-retain", witness_raw)

    def test_post_admission_outcome_unknown_diagnostics_bind_all_terminal_carriers(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        class PartialTerminalJsonlHost(_ScriptedCodexHost):
            def start(self, *args: object, **kwargs: object) -> _CompletedCodexProcess:
                process = super().start(*args, **kwargs)
                if len(self.starts) != 1:
                    return process
                event_log_path = kwargs["event_log_path"]
                output_path = kwargs["output_path"]
                worker = kwargs["worker"]
                assert isinstance(event_log_path, Path)
                assert isinstance(output_path, Path)
                assert isinstance(worker, str)

                def complete_with_partial_jsonl() -> None:
                    event_log_path.write_bytes(
                        event_log_path.read_bytes()
                        + b'{"type":"turn.completed","usage":{"input_tokens":10'
                    )
                    output_path.write_text(
                        f"captured output for {worker}\n",
                        encoding="utf-8",
                        newline="\n",
                    )

                process._on_success = complete_with_partial_jsonl
                return process

        scenarios = [
            (
                "nonzero",
                lambda: _ScriptedCodexHost(nonzero_at=3),
                CampaignError,
                2,
                "HOST_EXITED_NONZERO",
                9,
                "RETAINED",
                {"raw_event_log": True, "stderr": True, "raw_output": False},
                "PASS",
            ),
            (
                "timeout",
                lambda: _ScriptedCodexHost(timeout_at=2),
                CampaignError,
                1,
                "HOST_TIMEOUT",
                None,
                "RETAINED",
                {"raw_event_log": True, "stderr": True, "raw_output": False},
                "PASS",
            ),
            (
                "interrupt",
                lambda: _ScriptedCodexHost(interrupt_at=2),
                KeyboardInterrupt,
                1,
                "OBSERVATION_INTERRUPTED",
                None,
                "RETAINED",
                {"raw_event_log": True, "stderr": True, "raw_output": False},
                "PASS",
            ),
            (
                "partial-terminal-jsonl",
                PartialTerminalJsonlHost,
                CampaignError,
                0,
                "TERMINAL_EVENT_STREAM_INVALID",
                0,
                "RETAINED",
                {"raw_event_log": True, "stderr": True, "raw_output": True},
                "PASS",
            ),
            (
                "credential-purge",
                lambda: _ScriptedCodexHost(credential_residue_at=1),
                CampaignError,
                0,
                "CREDENTIAL_RESIDUE",
                0,
                "PURGED_UNRETAINED",
                {"raw_event_log": False, "stderr": False, "raw_output": False},
                "FAIL_CLOSED",
            ),
        ]
        for (
            scenario,
            host_factory,
            error_type,
            failed_index,
            failure_kind,
            host_returncode,
            carrier_disposition,
            source_presence,
            scan_status,
        ) in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory(
                prefix=f"daee-live-outcome-diagnostic-{scenario}-"
            ) as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(
                    Path(temp),
                    command_timeout_seconds=1,
                )
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=host_factory(),
                    command_timeout_seconds=1,
                )
                with self.assertRaises(error_type):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

                incident = json.loads(
                    (fixture.root / "incidents/producer-live-cycle-01.json").read_bytes()
                )
                finalizer = json.loads(
                    (fixture.root / "producer/observation-finalizer.json").read_bytes()
                )
                self.assertIn("outcome_unknown_diagnostics", finalizer)
                self.assertEqual(
                    finalizer["outcome_unknown_diagnostics"],
                    incident["finalizer_payload"]["outcome_unknown_diagnostics"],
                )
                self.assertEqual(1, len(finalizer["outcome_unknown_diagnostics"]))
                diagnostic_ref = finalizer["outcome_unknown_diagnostics"][0]
                diagnostic_path = fixture.root / diagnostic_ref["path"]
                self.assertEqual(diagnostic_ref, ref(fixture.root, diagnostic_path))
                diagnostic = json.loads(diagnostic_path.read_bytes())
                self.assertEqual("reviewed-campaign-outcome-unknown-diagnostic-v1", diagnostic["schema"])
                self.assertEqual("OUTCOME_UNKNOWN_DIAGNOSTIC_RETAINED", diagnostic["status"])
                self.assertEqual(CASES[failed_index], diagnostic["case_id"])
                self.assertEqual("OUTCOME_UNKNOWN", diagnostic["dispatch_classification"])
                self.assertEqual("ADMITTED", diagnostic["admission_status"])
                self.assertEqual(failure_kind, diagnostic["failure_kind"])
                self.assertEqual(host_returncode, diagnostic["host_returncode"])
                self.assertEqual(carrier_disposition, diagnostic["carrier_disposition"])
                self.assertEqual(source_presence, diagnostic["source_presence"])
                for role in (
                    "in_flight_admission",
                    "raw_event_log",
                    "stderr",
                    "raw_output",
                    "credential_residue_scan",
                    "execution_custody",
                ):
                    retained_path = fixture.root / diagnostic[role]["path"]
                    self.assertEqual(diagnostic[role], ref(fixture.root, retained_path))
                if carrier_disposition == "PURGED_UNRETAINED":
                    for role in ("raw_event_log", "stderr", "raw_output"):
                        self.assertEqual(b"", (fixture.root / diagnostic[role]["path"]).read_bytes())
                scan = json.loads(
                    (fixture.root / diagnostic["credential_residue_scan"]["path"]).read_bytes()
                )
                self.assertEqual(scan_status, scan["status"])
                self.assertEqual(
                    diagnostic["execution_custody"]["sha256"],
                    diagnostic["execution_custody_sha256"],
                )

                auth, auth_sha = orchestrator._load_producer_authorization(
                    fixture.root,
                    authorization,
                    require_active_window=False,
                    allow_test_fixture=True,
                )
                bindings = orchestrator._validate_common_bindings(
                    fixture.root,
                    auth,
                    allow_test_fixture=True,
                )
                bindings["producer_output_contracts"] = orchestrator._producer_output_contracts(
                    auth,
                    auth_sha,
                    bindings,
                )
                orchestrator._validate_failure_resume_payload(
                    fixture.root,
                    fixture.root / auth["usage_ledger_root"],
                    incident,
                    incident["finalizer_payload"],
                    auth,
                    auth_sha,
                    bindings,
                    lane="producer",
                    attempt_index=1,
                )
                omitted_payload = copy.deepcopy(incident["finalizer_payload"])
                omitted_payload["outcome_unknown_diagnostics"] = []
                omitted_incident = copy.deepcopy(incident)
                omitted_incident["finalizer_payload"] = omitted_payload
                with self.assertRaises(CampaignError):
                    orchestrator._validate_failure_resume_payload(
                        fixture.root,
                        fixture.root / auth["usage_ledger_root"],
                        omitted_incident,
                        omitted_payload,
                        auth,
                        auth_sha,
                        bindings,
                        lane="producer",
                        attempt_index=1,
                    )

    def test_current_generation_failure_replay_rejects_missing_pre_admission_diagnostics(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-live-current-diagnostic-omission-") as temp:
            fixture, _authorization, incident, payload, auth, auth_sha, bindings = (
                self._live_failure_replay_validation_inputs(
                    Path(temp),
                    host_args={"already_exited_at": 1, "nonzero_at": 1},
                )
            )
            self.assertEqual(1, len(payload["pre_admission_diagnostics"]))
            omitted_payload = copy.deepcopy(payload)
            del omitted_payload["pre_admission_diagnostics"]
            omitted_incident = copy.deepcopy(incident)
            omitted_incident["finalizer_payload"] = omitted_payload
            with self.assertRaisesRegex(
                CampaignError,
                "PRE_ADMISSION_DIAGNOSTIC_INVENTORY",
            ):
                orchestrator._validate_failure_resume_payload(
                    fixture.root,
                    fixture.root / auth["usage_ledger_root"],
                    omitted_incident,
                    omitted_payload,
                    auth,
                    auth_sha,
                    bindings,
                    lane="producer",
                    attempt_index=1,
                )

    def test_retained_pass_scan_and_full_execution_custody_reject_semantic_substitutions(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-live-retained-semantic-replay-") as temp:
            fixture, _authorization, incident, payload, auth, auth_sha, bindings = (
                self._live_failure_replay_validation_inputs(
                    Path(temp),
                    host_args={"already_exited_at": 1, "nonzero_at": 1},
                )
            )
            diagnostic_ref = payload["pre_admission_diagnostics"][0]
            diagnostic_path = fixture.root / diagnostic_ref["path"]
            diagnostic = json.loads(diagnostic_path.read_bytes())
            self.assertEqual("RETAINED", diagnostic["carrier_disposition"])
            scan_path = fixture.root / diagnostic["credential_residue_scan"]["path"]
            scan = json.loads(scan_path.read_bytes())
            self.assertEqual("PASS", scan["status"])
            custody_path = fixture.root / diagnostic["execution_custody"]["path"]
            custody = json.loads(custody_path.read_bytes())

            def retained_path(parent: Path, raw: bytes, suffix: str) -> Path:
                path = parent / f"{hashlib.sha256(raw).hexdigest()}{suffix}"
                path.write_bytes(raw)
                return path

            def assert_replay_rejects(mutated_diagnostic: dict[str, object]) -> None:
                mutated_raw = canonical(mutated_diagnostic)
                mutated_path = retained_path(
                    diagnostic_path.parent,
                    mutated_raw,
                    ".pre-admission-diagnostic.json",
                )
                mutated_payload = copy.deepcopy(payload)
                mutated_payload["pre_admission_diagnostics"] = [ref(fixture.root, mutated_path)]
                mutated_incident = copy.deepcopy(incident)
                mutated_incident["finalizer_payload"] = mutated_payload
                with self.assertRaises(CampaignError):
                    orchestrator._validate_failure_resume_payload(
                        fixture.root,
                        fixture.root / auth["usage_ledger_root"],
                        mutated_incident,
                        mutated_payload,
                        auth,
                        auth_sha,
                        bindings,
                        lane="producer",
                        attempt_index=1,
                    )

            scan_mutations: list[tuple[str, bytes]] = []
            wrong_worker_scan = copy.deepcopy(scan)
            wrong_worker_scan["worker"] = "producer-02"
            scan_mutations.append(("wrong-worker", canonical(wrong_worker_scan)))
            extra_field_scan = copy.deepcopy(scan)
            extra_field_scan["unexpected_payload"] = "must-not-survive"
            scan_mutations.append(("extra-field", canonical(extra_field_scan)))
            missing_field_scan = copy.deepcopy(scan)
            del missing_field_scan["encoding_forms_checked"]
            scan_mutations.append(("missing-field", canonical(missing_field_scan)))
            malformed_time_scan = copy.deepcopy(scan)
            malformed_time_scan["completed_at"] = "not-a-utc-time"
            scan_mutations.append(("malformed-time", canonical(malformed_time_scan)))
            scan_mutations.append(
                (
                    "noncanonical-bytes",
                    (json.dumps(scan, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
                )
            )
            for mutation_name, mutated_scan_raw in scan_mutations:
                with self.subTest(scan_mutation=mutation_name):
                    mutated_scan_path = retained_path(
                        scan_path.parent,
                        mutated_scan_raw,
                        ".credential-scan.json",
                    )
                    mutated_diagnostic = copy.deepcopy(diagnostic)
                    mutated_diagnostic["credential_residue_scan"] = ref(
                        fixture.root,
                        mutated_scan_path,
                    )
                    assert_replay_rejects(mutated_diagnostic)

            custody_mutations: list[tuple[str, dict[str, object]]] = []
            wrong_worker_custody = copy.deepcopy(custody)
            prefix = auth["isolated_root_prefix"]
            wrong_worker_custody["isolated_worker_root"] = {
                "worker": "producer-02",
                "home": f"{prefix}/producer-02/home",
                "cache": f"{prefix}/producer-02/cache",
                "run_root": f"{prefix}/producer-02/run",
            }
            custody_mutations.append(("wrong-worker-root", wrong_worker_custody))
            stale_tooling_custody = copy.deepcopy(custody)
            stale_tooling_custody["execution_tooling_manifest"] = copy.deepcopy(
                diagnostic["credential_residue_scan"]
            )
            custody_mutations.append(("wrong-role-tooling-ref", stale_tooling_custody))
            wrong_prompt_custody = copy.deepcopy(custody)
            wrong_prompt_custody["capture_bindings"]["exact_prompt"] = copy.deepcopy(
                wrong_prompt_custody["capture_bindings"]["raw_input"]
            )
            custody_mutations.append(("wrong-prompt-binding", wrong_prompt_custody))
            wrong_output_contract_custody = copy.deepcopy(custody)
            wrong_output_contract_custody["single_call_output_contract"]["case_id"] = CASES[1]
            custody_mutations.append(("wrong-output-contract", wrong_output_contract_custody))
            wrong_candidate_custody = copy.deepcopy(custody)
            wrong_candidate_custody["candidate_maturity"] = copy.deepcopy(
                wrong_candidate_custody["source_preflight"]
            )
            custody_mutations.append(("wrong-candidate-maturity-ref", wrong_candidate_custody))
            wrong_source_custody = copy.deepcopy(custody)
            wrong_source_custody["source_preflight"] = copy.deepcopy(
                wrong_source_custody["package_record"]
            )
            custody_mutations.append(("wrong-source-preflight-ref", wrong_source_custody))
            wrong_timeout_custody = copy.deepcopy(custody)
            wrong_timeout_custody["provider_settings"]["command_timeout_seconds"] += 1
            custody_mutations.append(("wrong-timeout-binding", wrong_timeout_custody))
            for mutation_name, mutated_custody in custody_mutations:
                with self.subTest(custody_mutation=mutation_name):
                    mutated_custody_raw = canonical(mutated_custody)
                    mutated_custody_path = retained_path(
                        custody_path.parent,
                        mutated_custody_raw,
                        ".execution-custody.json",
                    )
                    mutated_diagnostic = copy.deepcopy(diagnostic)
                    mutated_diagnostic["execution_custody"] = ref(
                        fixture.root,
                        mutated_custody_path,
                    )
                    mutated_diagnostic["execution_custody_sha256"] = mutated_diagnostic[
                        "execution_custody"
                    ]["sha256"]
                    assert_replay_rejects(mutated_diagnostic)

    def test_failed_launch_all_not_submitted_after_reservation_is_proved_no_dispatch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-failed-launch-not-submitted-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )
            original_token = adapter._inner._token

            def expire_after_reservation() -> str:
                token = original_token()
                adapter._inner._cohort_deadline_monotonic = time.monotonic() - 1
                return token

            with mock.patch.object(
                adapter._inner,
                "_token",
                side_effect=expire_after_reservation,
            ):
                with self.assertRaisesRegex(CampaignError, "PROVIDER_EXECUTION_FAILED"):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            self.assertEqual([], host.starts)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(0, head["totals"]["attempted"])
            self.assertEqual(5, head["totals"]["not_dispatched"])
            self.assertFalse(head["open_reservations"])
            self.assertFalse(head["unresolved_usage"])
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual("PROVED_NO_DISPATCH", finalizer["dispatch_classification"])
            self.assertEqual("CONSUMED_NO_DISPATCH", finalizer["candidate_status"])
            self.assertTrue(finalizer["resumable_retry"])

            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=replay_host,
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)

    def test_failed_launch_failure_payload_cannot_downgrade_existing_settlement(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-failed-launch-monotone-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(
                CampaignError,
                r"^INJECTED_TERMINAL_PHASE_FAILURE: after-observation-validation$",
            ):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                    fault_at="after-observation-validation",
                )
            incident = json.loads(
                (fixture.root / "incidents/producer-live-cycle-01.json").read_text(
                    encoding="utf-8"
                )
            )
            payload = copy.deepcopy(incident["finalizer_payload"])
            auth, auth_sha = orchestrator._load_producer_authorization(
                fixture.root,
                authorization,
                require_active_window=False,
                allow_test_fixture=True,
            )
            bindings = orchestrator._validate_common_bindings(
                fixture.root,
                auth,
                allow_test_fixture=True,
            )
            bindings["producer_output_contracts"] = orchestrator._producer_output_contracts(
                auth,
                auth_sha,
                bindings,
            )
            settlement_sha = payload["settlement_sha256"]
            settlement = json.loads(
                (
                    fixture.root
                    / "usage/transactions"
                    / f"{settlement_sha}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(5, settlement["completed"])
            self.assertEqual(0, settlement["unknown"])

            downgraded = copy.deepcopy(payload)
            downgraded.update(
                {
                    "failure_phase": "pre-dispatch",
                    "observed_results": [],
                    "completion": None,
                    "candidate_status": "CONSUMED_NO_DISPATCH",
                    "dispatch_status": "PROVED_NOT_DISPATCHED",
                    "dispatch_classification": "PROVED_NO_DISPATCH",
                    "settlement_sha256": None,
                    "resumable_retry": True,
                }
            )
            downgraded.pop("pre_admission_diagnostics", None)
            downgraded_incident = copy.deepcopy(incident)
            downgraded_incident.update(
                {
                    "failure_class": "reservation-or-provider-failure",
                    "failure_phase": "pre-dispatch",
                    "dispatch_classification": "PROVED_NO_DISPATCH",
                    "settlement_sha256": None,
                    "observed_result_count": 0,
                    "completion": None,
                    "finalizer_payload": downgraded,
                }
            )

            with self.assertRaisesRegex(
                CampaignError,
                "TERMINAL_PUBLICATION_PREFLIGHT",
            ):
                orchestrator._validate_failure_resume_payload(
                    fixture.root,
                    fixture.root / auth["usage_ledger_root"],
                    downgraded_incident,
                    downgraded,
                    auth,
                    auth_sha,
                    bindings,
                    lane="producer",
                    attempt_index=1,
                )

            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=replay_host,
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)

    def test_failed_launch_live_after_completion_failure_replays_exactly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-failed-launch-completion-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(
                CampaignError,
                r"^INJECTED_TERMINAL_PHASE_FAILURE: after-completion$",
            ):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                    fault_at="after-completion",
                )
            completion = json.loads(
                (fixture.root / "producer/completion.json").read_text(encoding="utf-8")
            )
            self.assertEqual("PRODUCER_CAPTURE_COMPLETE", completion["status"])

            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=replay_host,
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)

    def test_failed_launch_exact_terminal_adoption_precedes_launch_only_gates(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with self.subTest(state="completion-without-finalizer"), tempfile.TemporaryDirectory(
            prefix="daee-failed-launch-completion-adopt-"
        ) as temp:
            fixture, authorization, _completion = self._run_live_success(Path(temp))
            (fixture.root / "producer/observation-finalizer.json").unlink()
            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=fixture.root / "bin/codex.exe",
                host=replay_host,
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)

        class FutureClock(datetime):
            @classmethod
            def now(cls, tz=None):
                value = cls(2100, 1, 1, tzinfo=timezone.utc)
                return value if tz is not None else value.replace(tzinfo=None)

        with self.subTest(state="expired-exact-terminal"), tempfile.TemporaryDirectory(
            prefix="daee-failed-launch-expired-terminal-"
        ) as temp:
            fixture, authorization, _completion = self._run_live_success(Path(temp))
            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=fixture.root / "bin/codex.exe",
                host=replay_host,
                command_timeout_seconds=30,
            )
            with mock.patch.object(orchestrator, "datetime", FutureClock):
                with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        replay_adapter,
                        allow_test_fixture=True,
                    )
            self.assertEqual([], replay_host.starts)

    def test_failed_launch_append_before_head_failures_recover_exactly_once(self) -> None:
        import campaign_usage_ledger as usage_ledger

        with self.subTest(transition="reservation"), tempfile.TemporaryDirectory(
            prefix="daee-failed-launch-reservation-head-"
        ) as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )
            original_atomic_write = usage_ledger._atomic_write
            failed = False

            def fail_first_reservation_head(path: Path, value: dict[str, object]) -> None:
                nonlocal failed
                if path.name == "head.json" and value.get("sequence") == 1 and not failed:
                    failed = True
                    raise OSError("injected reservation head write failure")
                original_atomic_write(path, value)

            with mock.patch.object(
                usage_ledger,
                "_atomic_write",
                side_effect=fail_first_reservation_head,
            ):
                with self.assertRaisesRegex(CampaignError, "RESERVATION_FAILURE"):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )
            self.assertTrue(failed)
            self.assertEqual([], host.starts)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(5, head["totals"]["not_dispatched"])
            self.assertFalse(head["open_reservations"])
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIsInstance(finalizer["reservation_sha256"], str)
            self.assertIsInstance(finalizer["settlement_sha256"], str)
            self.assertEqual("PROVED_NO_DISPATCH", finalizer["dispatch_classification"])

        with self.subTest(transition="settlement"), tempfile.TemporaryDirectory(
            prefix="daee-failed-launch-settlement-head-"
        ) as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            original_atomic_write = usage_ledger._atomic_write

            def fail_settlement_head(path: Path, value: dict[str, object]) -> None:
                if path.name == "head.json" and value.get("sequence") == 2:
                    raise OSError("injected settlement head write failure")
                original_atomic_write(path, value)

            with mock.patch.object(
                usage_ledger,
                "_atomic_write",
                side_effect=fail_settlement_head,
            ):
                with self.assertRaises(CampaignError):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )
            open_head = validate_head(fixture.root / "usage")
            self.assertEqual(1, len(open_head["open_reservations"]))

            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=replay_host,
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)
            terminal_head = validate_head(fixture.root / "usage")
            self.assertFalse(terminal_head["open_reservations"])
            self.assertEqual(5, terminal_head["totals"]["completed"])

    def test_failed_launch_substituted_terminal_journal_cannot_advance_usage_or_publish_completion(self) -> None:
        import campaign_usage_ledger as usage_ledger

        with tempfile.TemporaryDirectory(prefix="daee-failed-launch-journal-substitution-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=_ScriptedCodexHost(),
                command_timeout_seconds=30,
            )
            original_atomic_write = usage_ledger._atomic_write

            def fail_settlement_head(path: Path, value: dict[str, object]) -> None:
                if path.name == "head.json" and value.get("sequence") == 2:
                    raise OSError("injected settlement head write failure")
                original_atomic_write(path, value)

            with mock.patch.object(
                usage_ledger,
                "_atomic_write",
                side_effect=fail_settlement_head,
            ):
                with self.assertRaises(CampaignError):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            journal_path = fixture.root / "producer/observed-terminal-journal.json"
            journal = json.loads(journal_path.read_bytes())
            journal["observed_results"][0]["case_id"] = CASES[1]
            journal_path.write_bytes(canonical(journal))
            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=replay_host,
                command_timeout_seconds=30,
            )
            with self.assertRaises(CampaignError):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(1, len(head["open_reservations"]))
            self.assertFalse((fixture.root / "producer/completion.json").exists())

    def test_post_capture_cleanup_failure_preserves_completed_results_and_replays_without_dispatch(self) -> None:
        import codex_live_producer_adapter as live_adapter

        for failure_point in ("worker-rmtree", "root-rmdir"):
            with self.subTest(failure_point=failure_point), tempfile.TemporaryDirectory(
                prefix=f"daee-post-capture-{failure_point}-"
            ) as temp:
                fixture, authorization, executable, _skill_bytes = self._live_fixture(
                    Path(temp)
                )
                host = _ScriptedCodexHost()
                adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=host,
                    command_timeout_seconds=30,
                )
                fired = False
                real_rmtree = live_adapter.shutil.rmtree
                real_rmdir = Path.rmdir
                isolated_root = fixture.root / "producer/isolated"

                def one_locked_worker(path: Path, *args, **kwargs):
                    nonlocal fired
                    if Path(path).name == "producer-01" and not fired:
                        fired = True
                        raise PermissionError(
                            "INJECTED_TRANSIENT_WINDOWS_WORKER_LOCK_AFTER_CAPTURE"
                        )
                    return real_rmtree(path, *args, **kwargs)

                def one_locked_root(path: Path):
                    nonlocal fired
                    if path == isolated_root and not fired:
                        fired = True
                        raise PermissionError(
                            "INJECTED_TRANSIENT_WINDOWS_ROOT_LOCK_AFTER_CAPTURE"
                        )
                    return real_rmdir(path)

                patcher = (
                    mock.patch.object(
                        live_adapter.shutil,
                        "rmtree",
                        side_effect=one_locked_worker,
                    )
                    if failure_point == "worker-rmtree"
                    else mock.patch.object(
                        Path,
                        "rmdir",
                        autospec=True,
                        side_effect=one_locked_root,
                    )
                )
                with patcher:
                    with self.assertRaisesRegex(
                        CampaignError,
                        "OWNED_ISOLATION_CLEANUP_INCOMPLETE",
                    ):
                        run_producer_cohort(
                            fixture.root,
                            authorization,
                            adapter,
                            allow_test_fixture=True,
                        )

                self.assertTrue(fired)
                self.assertEqual(5, len(host.starts))
                captures = [
                    json.loads(path.read_bytes())
                    for path in (
                        fixture.root / "producer/structural-evidence"
                    ).glob("*.capture.json")
                ]
                self.assertEqual(5, len(captures))
                self.assertEqual(
                    {case_id: ("CAPTURED", "RECORDED") for case_id in CASES},
                    {
                        row["case_id"]: (row["status"], row["usage"]["status"])
                        for row in captures
                    },
                )
                states = {row["case_id"]: row for row in adapter.attempt_states()}
                self.assertEqual(
                    {case_id: "COMPLETED" for case_id in CASES},
                    {case_id: row["state"] for case_id, row in states.items()},
                )
                self.assertTrue(
                    all(isinstance(row["result"], dict) for row in states.values())
                )

                head = validate_head(fixture.root / "usage")
                self.assertEqual([], head["open_reservations"])
                self.assertFalse(head["unresolved_usage"])
                self.assertEqual(5, head["totals"]["attempted"])
                self.assertEqual(5, head["totals"]["producer_invocations"])
                self.assertEqual(5, head["totals"]["completed"])
                self.assertEqual(0, head["totals"]["unknown"])
                self.assertFalse((fixture.root / "producer/completion.json").exists())
                self.assertFalse(isolated_root.exists())

                finalizer_path = fixture.root / "producer/observation-finalizer.json"
                finalizer = json.loads(finalizer_path.read_bytes())
                self.assertEqual("post-capture-cleanup", finalizer["failure_phase"])
                self.assertEqual("OBSERVED", finalizer["dispatch_classification"])
                self.assertEqual("CONSUMED_OBSERVED", finalizer["candidate_status"])
                self.assertFalse(finalizer["usage_unresolved"])
                self.assertEqual(5, len(finalizer["observed_results"]))
                incident = json.loads(
                    (fixture.root / finalizer["incident"]["path"]).read_bytes()
                )
                self.assertEqual("post-observation-terminal-failure", incident["failure_class"])
                self.assertEqual(5, incident["observed_result_count"])

                head_before = (fixture.root / "usage/head.json").read_bytes()
                finalizer_before = finalizer_path.read_bytes()
                replay_host = _ScriptedCodexHost()
                replay_adapter = _ScriptedCodexTestAdapter(
                    custody_root=fixture.root,
                    codex_executable=executable,
                    host=replay_host,
                    command_timeout_seconds=30,
                )
                with self.assertRaisesRegex(
                    CampaignError,
                    "ATTEMPT_ALREADY_TERMINALIZED",
                ):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        replay_adapter,
                        allow_test_fixture=True,
                    )
                self.assertEqual([], replay_host.starts)
                self.assertEqual(head_before, (fixture.root / "usage/head.json").read_bytes())
                self.assertEqual(finalizer_before, finalizer_path.read_bytes())

    def test_root_cleanup_witness_renewal_rejects_same_path_substitution(self) -> None:
        import codex_live_producer_adapter as live_adapter

        with tempfile.TemporaryDirectory(
            prefix="daee-post-capture-root-witness-substitution-"
        ) as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(
                Path(temp)
            )
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )
            isolated_root = fixture.root / "producer/isolated"
            witness_path = isolated_root / live_adapter._OWNERSHIP_WITNESS_NAME
            state = {
                "rmdir_failed": False,
                "renewal_armed": False,
                "witness_replaced": False,
                "replacement_bytes": None,
            }
            real_rmdir = Path.rmdir
            real_write_once = live_adapter._write_once

            def one_locked_root(path: Path):
                if path == isolated_root and not state["rmdir_failed"]:
                    state["rmdir_failed"] = True
                    state["renewal_armed"] = True
                    raise PermissionError(
                        "INJECTED_TRANSIENT_WINDOWS_ROOT_LOCK_BEFORE_SUBSTITUTION"
                    )
                return real_rmdir(path)

            def replace_renewed_witness(path: Path, data: bytes):
                created_identity = real_write_once(path, data)
                if (
                    path == witness_path
                    and state["renewal_armed"]
                    and not state["witness_replaced"]
                ):
                    replacement_bytes = bytes(data)
                    path.unlink()
                    path.write_bytes(replacement_bytes)
                    state["witness_replaced"] = True
                    state["replacement_bytes"] = replacement_bytes
                return created_identity

            with mock.patch.object(
                Path,
                "rmdir",
                autospec=True,
                side_effect=one_locked_root,
            ), mock.patch.object(
                live_adapter,
                "_write_once",
                side_effect=replace_renewed_witness,
            ):
                with self.assertRaisesRegex(
                    CampaignError,
                    "OWNED_ISOLATION_CLEANUP",
                ):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            self.assertTrue(state["rmdir_failed"])
            self.assertTrue(state["witness_replaced"])
            self.assertEqual(5, len(host.starts))
            self.assertTrue(isolated_root.is_dir())
            self.assertIsInstance(state["replacement_bytes"], bytes)
            self.assertEqual(state["replacement_bytes"], witness_path.read_bytes())

            states = {row["case_id"]: row for row in adapter.attempt_states()}
            self.assertEqual(
                {case_id: "COMPLETED" for case_id in CASES},
                {case_id: row["state"] for case_id, row in states.items()},
            )
            head = validate_head(fixture.root / "usage")
            self.assertEqual([], head["open_reservations"])
            self.assertFalse(head["unresolved_usage"])
            self.assertEqual(5, head["totals"]["completed"])
            self.assertEqual(0, head["totals"]["unknown"])

            finalizer_path = fixture.root / "producer/observation-finalizer.json"
            finalizer = json.loads(finalizer_path.read_bytes())
            self.assertEqual("post-capture-cleanup", finalizer["failure_phase"])
            self.assertEqual("OBSERVED", finalizer["dispatch_classification"])
            self.assertEqual(5, len(finalizer["observed_results"]))

            head_before = (fixture.root / "usage/head.json").read_bytes()
            finalizer_before = finalizer_path.read_bytes()
            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=replay_host,
                command_timeout_seconds=30,
            )
            with self.assertRaisesRegex(
                CampaignError,
                "ATTEMPT_ALREADY_TERMINALIZED",
            ):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)
            self.assertEqual(head_before, (fixture.root / "usage/head.json").read_bytes())
            self.assertEqual(finalizer_before, finalizer_path.read_bytes())
            self.assertTrue(isolated_root.is_dir())
            self.assertEqual(state["replacement_bytes"], witness_path.read_bytes())

    def test_pre_admission_carrier_retention_failure_totalizes_with_secret_free_disposition(self) -> None:
        import codex_live_producer_adapter as live_adapter
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-failed-launch-retention-failure-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost(already_exited_at=1, nonzero_at=1)
            fixture_token = "fixture-access-token-never-retain"
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
                fixture_token=fixture_token,
            )
            original_retain = live_adapter._retain_content_addressed
            injected = False

            def fail_first_event_retention(base: Path, data: bytes, suffix: str) -> Path:
                nonlocal injected
                if suffix == ".pre-admission.events.jsonl" and not injected:
                    injected = True
                    raise OSError("injected safe-carrier retention failure")
                return original_retain(base, data, suffix)

            with mock.patch.object(
                live_adapter,
                "_retain_content_addressed",
                side_effect=fail_first_event_retention,
            ):
                with self.assertRaises(CampaignError):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            self.assertTrue(injected)
            head = validate_head(fixture.root / "usage")
            self.assertEqual([], head["open_reservations"])
            self.assertTrue(head["unresolved_usage"])
            self.assertEqual(
                (0, 0, 1, 4),
                (
                    head["totals"]["attempted"],
                    head["totals"]["producer_invocations"],
                    head["totals"]["unknown"],
                    head["totals"]["not_dispatched"],
                ),
            )
            finalizer = json.loads(
                (fixture.root / "producer/observation-finalizer.json").read_bytes()
            )
            self.assertEqual("DISPATCH_UNKNOWN", finalizer["dispatch_classification"])
            self.assertEqual(1, len(finalizer["pre_admission_diagnostics"]))
            diagnostic_ref = finalizer["pre_admission_diagnostics"][0]
            diagnostic_path = fixture.root / diagnostic_ref["path"]
            diagnostic = json.loads(diagnostic_path.read_bytes())
            self.assertEqual(
                "PRE_ADMISSION_DIAGNOSTIC_RETENTION_FAILED_CLOSED",
                diagnostic["status"],
            )
            self.assertEqual("RETENTION_FAILED", diagnostic["carrier_disposition"])
            self.assertEqual(
                {
                    "schema": "reviewed-campaign-diagnostic-retention-failure-v1",
                    "status": "FAILED_CLOSED",
                    "failed_role": "raw_event_log",
                    "error_class": "OSError",
                    "retained_original_carriers": False,
                },
                diagnostic["retention_failure"],
            )
            self.assertEqual(
                {"raw_event_log": False, "stderr": False, "raw_output": False},
                diagnostic["source_presence"],
            )
            for role in ("raw_event_log", "stderr", "raw_output"):
                self.assertEqual(b"", (fixture.root / diagnostic[role]["path"]).read_bytes())
            self.assertFalse((fixture.root / "producer/isolated").exists())
            for retained in fixture.root.rglob("*"):
                if retained.is_file():
                    self.assertNotIn(fixture_token.encode(), retained.read_bytes())

            auth, _auth_sha = orchestrator._load_producer_authorization(
                fixture.root,
                authorization,
                require_active_window=False,
                allow_test_fixture=True,
            )
            bindings = orchestrator._validate_common_bindings(
                fixture.root,
                auth,
                allow_test_fixture=True,
            )
            settlement = json.loads(
                (
                    fixture.root
                    / "usage/transactions"
                    / f"{head['last_transaction_sha256']}.json"
                ).read_bytes()
            )
            substituted = copy.deepcopy(finalizer)
            invalid_diagnostic = copy.deepcopy(diagnostic)
            invalid_diagnostic["retention_failure"]["failed_role"] = "forged-role"
            invalid_raw = canonical(invalid_diagnostic)
            invalid_path = (
                fixture.root
                / auth["provider_receipt_root"]
                / f"{hashlib.sha256(invalid_raw).hexdigest()}.pre-admission-diagnostic.json"
            )
            invalid_path.write_bytes(invalid_raw)
            substituted["pre_admission_diagnostics"] = [ref(fixture.root, invalid_path)]
            with self.assertRaisesRegex(
                CampaignError,
                "TERMINAL_PUBLICATION_PREFLIGHT_PRE_ADMISSION_DIAGNOSTIC_RETENTION_FAILURE",
            ):
                orchestrator._validate_pre_admission_diagnostics(
                    fixture.root,
                    substituted,
                    auth,
                    settlement,
                    bindings,
                )

            replay_host = _ScriptedCodexHost()
            replay_adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=replay_host,
                command_timeout_seconds=30,
                fixture_token=fixture_token,
            )
            with self.assertRaisesRegex(CampaignError, "ATTEMPT_ALREADY_TERMINALIZED"):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    replay_adapter,
                    allow_test_fixture=True,
                )
            self.assertEqual([], replay_host.starts)

    def test_post_prepare_preclaim_failure_cleans_owned_isolation_and_retains_witness(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        with tempfile.TemporaryDirectory(prefix="daee-post-prepare-preclaim-failure-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )

            with mock.patch.object(
                orchestrator,
                "_recheck_execution_tooling_binding",
                side_effect=CampaignError("INJECTED_POST_PREPARE_PRECLAIM_BINDING_FAILURE"),
            ):
                with self.assertRaisesRegex(
                    CampaignError,
                    "INJECTED_POST_PREPARE_PRECLAIM_BINDING_FAILURE",
                ):
                    run_producer_cohort(
                        fixture.root,
                        authorization,
                        adapter,
                        allow_test_fixture=True,
                    )

            self.assertEqual([], host.starts)
            self.assertFalse((fixture.root / "claims").exists())
            head = validate_head(fixture.root / "usage")
            self.assertEqual(0, head["sequence"])
            self.assertEqual([], head["open_reservations"])
            self.assertFalse((fixture.root / "producer/isolated").exists())
            witnesses = list(
                (fixture.root / "producer/preclaim-cleanup-witnesses").glob(
                    "*.preclaim-cleanup-witness.json"
                )
            )
            self.assertEqual(1, len(witnesses))
            witness = json.loads(witnesses[0].read_bytes())
            self.maxDiff = None
            self.assertEqual(
                {
                    "schema": "reviewed-campaign-preclaim-cleanup-witness-v1",
                    "status": "OWNED_ISOLATION_REMOVED",
                    "failure_phase": "post-prepare-preclaim",
                    "failure_class": "CampaignError",
                    "cleanup_failure_class": None,
                    "authorization_sha256": digest(authorization),
                    "candidate_id": json.loads(authorization.read_bytes())["candidate_id"],
                    "case_ids": CASES,
                    "provider_host_started": False,
                    "claim_consumed": False,
                    "reservation_created": False,
                },
                witness,
            )

    def test_post_prepare_claim_entry_failure_cleans_owned_isolation_and_retains_witness(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-post-prepare-claim-entry-failure-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            matrix = json.loads(authorization.read_bytes())
            claim_path = fixture.root / matrix["authorization_claim_path"]
            foreign_bytes = b"foreign claim collision must remain unchanged\n"
            claim_path.parent.mkdir(parents=True, exist_ok=True)
            claim_path.write_bytes(foreign_bytes)
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )

            with self.assertRaisesRegex(
                CampaignError,
                "CREATE_ONCE_PRODUCER_AUTHORIZATION_CLAIM",
            ):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                )

            self.assertEqual(foreign_bytes, claim_path.read_bytes())
            self.assertEqual([], host.starts)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(0, head["sequence"])
            self.assertEqual([], head["open_reservations"])
            self.assertFalse((fixture.root / "producer/isolated").exists())
            witnesses = list(
                (fixture.root / "producer/preclaim-cleanup-witnesses").glob(
                    "*.preclaim-cleanup-witness.json"
                )
            )
            self.assertEqual(1, len(witnesses))
            witness = json.loads(witnesses[0].read_bytes())
            self.assertEqual("OWNED_ISOLATION_REMOVED", witness["status"])
            self.assertEqual("CampaignError", witness["failure_class"])
            self.assertFalse(witness["provider_host_started"])
            self.assertFalse(witness["claim_consumed"])
            self.assertFalse(witness["reservation_created"])

    def test_post_claim_pre_reservation_failure_cleans_owned_isolation_and_retains_witness(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-post-claim-pre-reservation-failure-") as temp:
            fixture, authorization, executable, _skill_bytes = self._live_fixture(Path(temp))
            host = _ScriptedCodexHost()
            adapter = _ScriptedCodexTestAdapter(
                custody_root=fixture.root,
                codex_executable=executable,
                host=host,
                command_timeout_seconds=30,
            )

            with self.assertRaisesRegex(
                CampaignError,
                "INJECTED_RESERVATION_FAILURE_AFTER_CLAIMS",
            ):
                run_producer_cohort(
                    fixture.root,
                    authorization,
                    adapter,
                    allow_test_fixture=True,
                    fault_at="after-claims-before-reservation",
                )

            self.assertEqual([], host.starts)
            head = validate_head(fixture.root / "usage")
            self.assertEqual(0, head["sequence"])
            self.assertEqual([], head["open_reservations"])
            self.assertFalse((fixture.root / "producer/isolated").exists())
            witnesses = list(
                (fixture.root / "producer/preclaim-cleanup-witnesses").glob(
                    "*.preclaim-cleanup-witness.json"
                )
            )
            self.assertEqual(1, len(witnesses))
            witness = json.loads(witnesses[0].read_bytes())
            self.maxDiff = None
            self.assertEqual(
                {
                    "schema": "reviewed-campaign-preclaim-cleanup-witness-v1",
                    "status": "OWNED_ISOLATION_REMOVED",
                    "failure_phase": "post-claim-pre-reservation",
                    "failure_class": "CampaignError",
                    "cleanup_failure_class": None,
                    "authorization_sha256": digest(authorization),
                    "candidate_id": json.loads(authorization.read_bytes())["candidate_id"],
                    "case_ids": CASES,
                    "provider_host_started": False,
                    "claim_consumed": True,
                    "reservation_created": False,
                },
                witness,
            )

    def test_failed_launch_windows_equivalent_governed_roots_reject_preclaim(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        aliases = (
            ("prompt_retention_root", "isolated_root_prefix"),
            ("provider_receipt_root", "output_retention_root"),
        )
        for mutated_field, aliased_field in aliases:
            with self.subTest(
                mutated_field=mutated_field,
                aliased_field=aliased_field,
            ), tempfile.TemporaryDirectory(
                prefix="daee-failed-launch-windows-root-"
            ) as temp:
                fixture, authorization, _executable, _skill_bytes = self._live_fixture(
                    Path(temp)
                )
                matrix = json.loads(authorization.read_text(encoding="utf-8"))
                alias = matrix[aliased_field].upper()
                self.assertNotEqual(matrix[aliased_field], alias)
                self.assertEqual(
                    ntpath.normcase(ntpath.normpath(matrix[aliased_field])),
                    ntpath.normcase(ntpath.normpath(alias)),
                )
                matrix[mutated_field] = alias
                matrix["authorization_sha256"] = record_sha256(
                    {
                        key: value
                        for key, value in matrix.items()
                        if key != "authorization_sha256"
                    }
                )
                write_json(authorization, matrix)

                with self.assertRaisesRegex(CampaignError, "GOVERNED_ROOT_ALIAS"):
                    orchestrator._load_producer_authorization(
                        fixture.root,
                        authorization,
                        allow_test_fixture=True,
                    )
                self.assertFalse((fixture.root / "claims").exists())
                self.assertFalse((fixture.root / "producer/isolated").exists())


    def test_failed_launch_create_once_crash_is_absent_or_complete_and_recoverable(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        child_script = (
            "import os, pathlib, sys\n"
            "sys.path.insert(0, str(pathlib.Path.cwd() / 'tools'))\n"
            "import reviewed_campaign_orchestrator as orchestrator\n"
            "root = pathlib.Path(sys.argv[1])\n"
            "relative = sys.argv[2]\n"
            "payload = bytes.fromhex(sys.argv[3])\n"
            "original_fdopen = os.fdopen\n"
            "class CrashWriter:\n"
            "    def __init__(self, descriptor, mode):\n"
            "        self.descriptor = descriptor\n"
            "        self.mode = mode\n"
            "        self.handle = None\n"
            "    def __enter__(self):\n"
            "        self.handle = original_fdopen(self.descriptor, self.mode)\n"
            "        return self\n"
            "    def __exit__(self, exc_type, exc, traceback):\n"
            "        return self.handle.__exit__(exc_type, exc, traceback)\n"
            "    def write(self, data):\n"
            "        prefix = data[:max(1, len(data) // 2)]\n"
            "        self.handle.write(prefix)\n"
            "        self.handle.flush()\n"
            "        os.fsync(self.handle.fileno())\n"
            "        os._exit(91)\n"
            "orchestrator.os.fdopen = lambda descriptor, mode, **kwargs: CrashWriter(descriptor, mode)\n"
            "orchestrator._publish_once_bytes(root, relative, payload, 'crash_canary')\n"
            "raise SystemExit(90)\n"
        )
        with tempfile.TemporaryDirectory(prefix="daee-create-once-crash-") as temp:
            root = Path(temp)
            relative = "evidence/create-once.json"
            target = root / relative
            payload = canonical(
                {
                    "schema": "reviewed-campaign-create-once-crash-canary-v1",
                    "value": "strict-prefix-must-never-be-final",
                }
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    child_script,
                    str(root),
                    relative,
                    payload.hex(),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(91, completed.returncode, completed.stdout + completed.stderr)

            observed = target.read_bytes() if target.exists() else None
            violations: list[str] = []
            if observed not in {None, payload}:
                violations.append(
                    f"final path retained strict prefix {observed!r} after process death"
                )
            try:
                reference = orchestrator._publish_once_bytes(
                    root,
                    relative,
                    payload,
                    "crash_canary_recovery",
                )
            except Exception as exc:
                violations.append(
                    f"exact recovery rejected crash residue: {type(exc).__name__}: {exc}"
                )
            else:
                expected_reference = {
                    "path": relative,
                    "byte_count": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
                if reference != expected_reference or target.read_bytes() != payload:
                    violations.append("exact recovery did not publish the complete intended bytes")
                stage_residue = sorted(target.parent.glob(f".{target.name}.stage-*"))
                if stage_residue:
                    violations.append(
                        f"unreclaimed crash-stage residue remained: {stage_residue}"
                    )
            self.assertEqual([], violations, "; ".join(violations))

    def test_failed_launch_writer_lock_is_recoverable_after_holder_process_death(self) -> None:
        import campaign_usage_ledger as usage_ledger

        child_script = (
            "import os, pathlib, sys\n"
            "sys.path.insert(0, str(pathlib.Path.cwd() / 'tools'))\n"
            "import campaign_usage_ledger as usage_ledger\n"
            "root = pathlib.Path(sys.argv[1])\n"
            "marker = pathlib.Path(sys.argv[2])\n"
            "with usage_ledger._lock(root):\n"
            "    marker.write_bytes(b'lock-held-before-process-death')\n"
            "    os._exit(92)\n"
            "raise SystemExit(93)\n"
        )
        with tempfile.TemporaryDirectory(prefix="daee-writer-lock-crash-") as temp:
            root = Path(temp)
            usage_root = root / "usage"
            marker = root / "holder-entered.marker"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    child_script,
                    str(usage_root),
                    str(marker),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(92, completed.returncode, completed.stdout + completed.stderr)
            self.assertEqual(b"lock-held-before-process-death", marker.read_bytes())

            recovery_error: Exception | None = None
            recovered_head: dict[str, object] | None = None
            try:
                with usage_ledger._lock(usage_root):
                    recovered_head = usage_ledger.head_snapshot(usage_root)
            except Exception as exc:
                recovery_error = exc
            self.assertIsNone(
                recovery_error,
                "process-death-released or generation-bound lock recovery failed; "
                f"lock_exists={(usage_root / '.writer.lock').exists()}; "
                f"error={type(recovery_error).__name__}: {recovery_error}",
            )
            self.assertIsNotNone(recovered_head)
            self.assertEqual(0, recovered_head["sequence"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
