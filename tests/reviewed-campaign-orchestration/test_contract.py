from __future__ import annotations

import hashlib
import json
import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from check_parallel_dispatch_manifest import validate_dispatch_manifest
from campaign_usage_ledger import head_snapshot, recover_orphan, reserve, validate_head
from reviewed_campaign_orchestrator import (
    CampaignError,
    _contained,
    claim_initial_assessments,
    extract_mature_candidate_identity,
    ingest_final_adjudication,
    run_cold_review_cohort,
    run_producer_cohort,
    simulate_paired_gpt_opus_canary,
    validate_retry_lineage,
    record_sha256,
)
from build_cold_review_packet import build as build_cold_review_packet


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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(root: Path, path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


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

    def test_cli_live_provider_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-task6-cli-") as temp:
            fixture = Fixture(Path(temp))
            proc = subprocess.run(
                [
                    sys.executable,
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
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("LIVE_PROVIDER_UNSUPPORTED", proc.stdout)
            self.assertFalse((fixture.root / "claims").exists())

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
            [sys.executable, str(TOOLS / "reviewed_campaign_orchestrator.py"), "--self-test"],
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
