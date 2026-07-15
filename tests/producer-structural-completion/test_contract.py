#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import finalize_producer_capture_complete as capture_finalizer
import check_initial_assessment_barrier as assessment_barrier

try:
    import promote_producer_structural_completion as promoter
except ModuleNotFoundError:
    promoter = None


CASES = [
    "gate88-secularism",
    "gate88-khaybar",
    "gate88-trinitarian-j173",
    "gate88-tst-lillard",
    "gate88-torah-quran-source-authentication",
]
CANDIDATE_ID = "b11-test-candidate-01"
SOURCE_COMMIT = "2" * 40
CYCLE_ID = "b11-five-smoke-cycle-01"
NONCLAIMS = {
    "not_human_pre_disclosure_assessment": True,
    "not_cold_review": True,
    "not_campaign_success": True,
    "not_release_or_owner_acceptance": True,
}
CANDIDATE_BINDING = {
    "candidate_id": CANDIDATE_ID,
    "source_commit": SOURCE_COMMIT,
    "candidate_record_sha256": "1" * 64,
    "candidate_maturity_sha256": "2" * 64,
    "archive_sha256": "3" * 64,
    "package_tree_sha256": "4" * 64,
    "skill_sha256": "5" * 64,
    "build_manifest_sha256": "6" * 64,
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def load_test_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load test helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_execution_tooling_manifest_contract = load_test_module(
    "execution_tooling_manifest_contract",
    ROOT / "tests" / "execution-tooling-manifest" / "test_contract.py",
)
ExecutionToolingManifestContract = (
    _execution_tooling_manifest_contract.ExecutionToolingManifestContract
)


class Fixture:
    def __init__(self) -> None:
        self.relative = Path(".daee") / "producer-structural-completion-test" / uuid.uuid4().hex
        self.root = ROOT / self.relative
        self.root.mkdir(parents=True)
        self.capture_completion_path = self.root / "producer" / "completion.json"
        self.aggregate_path = self.root / "producer" / "structural-completion.json"
        self.authorization_path = self.root / "authorizations" / "producer.json"
        self.assessment_claim = self.root / "human-initial-assessments" / "claim.json"
        self.disclosure = self.root / "cold-review" / "packet-disclosure.json"
        self.rows: list[dict[str, object]] = []
        self.payloads: list[dict[str, object]] = []
        self.capture_refs: list[dict[str, object]] = []
        self.finalization_refs: list[dict[str, object]] = []
        self.raw_completion: dict[str, object] = {}
        self.raw_completion_bytes = b""
        self.tooling_ref = self.retain_json(
            "execution-tooling-manifest",
            {
                "schema": "producer-structural-completion-test-tooling-stub-v1",
                "test_fixture_only": True,
            },
        )
        self._build()

    def close(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def retain(self, role: str, raw: bytes, suffix: str) -> dict[str, object]:
        digest = hashlib.sha256(raw).hexdigest()
        path = self.root / "artifacts" / role / f"{digest}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            self.assert_bytes(path, raw)
        else:
            path.write_bytes(raw)
        return {"path": path.relative_to(self.root).as_posix(), "byte_count": len(raw), "sha256": digest}

    @staticmethod
    def assert_bytes(path: Path, expected: bytes) -> None:
        if path.read_bytes() != expected:
            raise AssertionError(f"fixture content-address collision: {path}")

    def retain_json(self, role: str, value: object) -> dict[str, object]:
        return self.retain(role, canonical(value), ".json")

    def write_json(self, relative: str | Path, value: object) -> dict[str, object]:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = canonical(value)
        path.write_bytes(raw)
        return {"path": path.relative_to(self.root).as_posix(), "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    def _case_artifacts(self, case_id: str, index: int) -> dict[str, object]:
        raw_input = f"canonical input {index} for {case_id}\n".encode()
        prompt = f"exact prompt {index}\n".encode() + raw_input
        raw_output = f"raw single-call envelope {index} for {case_id}\n".encode()
        raw_input_ref = self.retain(f"raw-input-{index}", raw_input, ".bin")
        prompt_ref = self.retain(f"prompt-{index}", prompt, ".md")
        output_ref = self.retain(f"raw-output-{index}", raw_output, ".md")
        result_path = self.root / "producer" / "results" / f"{case_id}.txt"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_bytes(raw_output)
        result_output_ref = {
            "path": result_path.relative_to(self.root).as_posix(),
            "byte_count": len(raw_output),
            "sha256": hashlib.sha256(raw_output).hexdigest(),
        }
        context = {
            "schema": "daee-runtime-call-context-v1",
            "case_id": case_id,
            "stage": "01-08",
            "runtime": {
                "source_commit": SOURCE_COMMIT,
                "package_sha256": CANDIDATE_BINDING["package_tree_sha256"],
                "skill_root_sha256": CANDIDATE_BINDING["skill_sha256"],
                "build_manifest_sha256": CANDIDATE_BINDING["build_manifest_sha256"],
            },
            "input": {"sha256": raw_input_ref["sha256"], "byte_count": raw_input_ref["byte_count"]},
            "prompt": {"sha256": prompt_ref["sha256"], "byte_count": prompt_ref["byte_count"]},
            "budget_telemetry": {
                "effective_context_bytes": len(prompt),
                "effective_context_limit": 500000,
            },
        }
        context_ref = self.retain_json(f"runtime-context-{index}", context)
        parity_ref = self.retain_json(
            f"package-parity-{index}",
            {
                "schema": "daee-package-harness-parity-v1",
                "classification": "package-faithful",
                "package_tree_sha256": CANDIDATE_BINDING["package_tree_sha256"],
            },
        )
        capture_bindings = {
            "raw_input": raw_input_ref,
            "exact_prompt": prompt_ref,
            "composite_runtime_context": context_ref,
            "package_harness_parity": parity_ref,
        }
        nonce = f"{index:032x}"
        custody = {
            "schema": "reviewed-campaign-execution-custody-v1",
            "lane": "producer",
            "candidate_id": CANDIDATE_ID,
            "source_commit": SOURCE_COMMIT,
            "cycle_or_review_batch_id": CYCLE_ID,
            "case_id": case_id,
            "subject_id": f"producer:{case_id}",
            "usage_reservation_sha256": f"{index:064x}",
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "provider_settings": {
                "effective_context_limit_bytes": 500000,
                "command_timeout_seconds": 30,
                "observation_protocol": "concurrent-five-shared-deadline-v1",
            },
            "execution_tooling_manifest": copy.deepcopy(self.tooling_ref),
            "single_call_output_contract": {
                "schema": "daee-single-call-output-envelope-contract-v1",
                "envelope_nonce": nonce,
                "case_id": case_id,
                "cycle_id": CYCLE_ID,
                "candidate_binding": copy.deepcopy(CANDIDATE_BINDING),
                "input_binding": {"sha256": raw_input_ref["sha256"], "byte_count": raw_input_ref["byte_count"]},
                "transport": "daee-single-call-stage-envelope-v1",
                "stage08_owner": "private-source-bound-checker",
            },
            "capture_bindings": capture_bindings,
        }
        custody_ref = self.retain_json(f"execution-custody-{index}", custody)
        credential_ref = self.retain_json(
            f"credential-scan-{index}",
            {"schema": "reviewed-campaign-credential-residue-scan-v1", "status": "PASS"},
        )
        receipt = {
            "call_id": f"{CYCLE_ID}:call-{index:02d}",
            "candidate_id": CANDIDATE_ID,
            "cycle_or_review_batch_id": CYCLE_ID,
            "case_id": case_id,
            "subject_id": f"producer:{case_id}",
            "usage_reservation_sha256": f"{index:064x}",
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "status": "COMPLETED",
            "terminal_transport_status": "COMPLETED",
            "provider_call_id": f"codex-thread:test-{index:02d}",
            "usage": {"status": "RECORDED", "input_tokens": index, "output_tokens": index},
            "cost": {"unit": "usd", "value": "unknown", "status": "UNAVAILABLE"},
        }
        receipt_ref = self.retain_json(f"provider-receipt-{index}", receipt)
        capture = {
            "schema": "reviewed-campaign-live-capture-v1",
            "status": "CAPTURED",
            "candidate_id": CANDIDATE_ID,
            "source_commit": SOURCE_COMMIT,
            "cycle_id": CYCLE_ID,
            "case_id": case_id,
            "prompt": prompt_ref,
            "raw_input": raw_input_ref,
            "runtime_context": context_ref,
            "package_harness_parity": parity_ref,
            "raw_output": output_ref,
            "credential_residue_scan": credential_ref,
            "execution_custody_sha256": custody_ref["sha256"],
            "execution_custody": custody_ref,
            "completion_identity": {"provider_call_id": receipt["provider_call_id"]},
            "structural_status": "UNVERIFIED",
        }
        capture_ref = self.retain_json(f"capture-evidence-{index}", capture)
        return {
            "nonce": nonce,
            "raw_input": raw_input_ref,
            "prompt": prompt_ref,
            "output": result_output_ref,
            "captured_output": output_ref,
            "context": context_ref,
            "parity": parity_ref,
            "custody": custody_ref,
            "receipt": receipt_ref,
            "capture": capture_ref,
            "usage_reservation_sha256": f"{index:064x}",
        }

    def _build(self) -> None:
        artifacts = [self._case_artifacts(case_id, index) for index, case_id in enumerate(CASES, 1)]
        registry = {
            "schema": "daee-smoke-matrix-v1",
            "kind": "input-registry",
            "matrix_id": "v0.4.6.0-wip-five-smoke",
            "cases": [
                {
                    "case_id": case_id,
                    "input_path": row["raw_input"]["path"],
                    "raw_bytes": row["raw_input"]["byte_count"],
                    "raw_sha256": row["raw_input"]["sha256"],
                }
                for case_id, row in zip(CASES, artifacts)
            ],
            "forbidden_case_fields": ["expected_answer"],
        }
        registry_ref = self.write_json("inputs/registry.json", registry)
        protocol = {
            "schema": "daee-smoke-matrix-v1",
            "kind": "review-protocol",
            "protocol_id": "reviewed-five-smoke-v1",
            "input_registry": registry_ref,
            "case_ids": list(CASES),
            "human_initial_assessment": {
                "required_count": 5,
                "all_hash_claimed_before_cold_review": True,
                "cold_review_disclosure_forbidden_before_claim": True,
            },
        }
        protocol_ref = self.write_json("inputs/review-protocol.json", protocol)
        results = [
            {
                "case_id": case_id,
                "capture_status": "CAPTURED",
                "structural_status": "UNVERIFIED",
                "output": row["output"],
                "capture_evidence": row["capture"],
                "provider_receipt": row["receipt"],
                "provider_receipt_sha256": row["receipt"]["sha256"],
            }
            for case_id, row in zip(CASES, artifacts)
        ]
        authorization_value = {
            "schema": "fabricated-producer-authorization-v1",
            "test_only": True,
            "purpose": "aggregate unit-contract dependency mock",
            "candidate_id": CANDIDATE_ID,
            "source_commit": SOURCE_COMMIT,
            "registry": registry_ref,
            "review_protocol": protocol_ref,
            "structural_evidence_root": "producer/structural-evidence",
            "observation_finalizer_path": "producer/observation-finalizer.json",
            "execution_tooling_manifest": copy.deepcopy(self.tooling_ref),
        }
        authorization_ref = self.write_json("authorizations/producer.json", authorization_value)
        observation_finalizer_ref = self.write_json(
            "producer/observation-finalizer.json",
            {"schema": "fabricated-observation-finalizer-v1", "test_only": True},
        )
        self.raw_completion = {
            "schema": "reviewed-campaign-producer-completion-v1",
            "status": "PRODUCER_CAPTURE_COMPLETE",
            "execution_mode": "LIVE_CODEX",
            "test_only": False,
            "candidate_id": CANDIDATE_ID,
            "cycle_id": CYCLE_ID,
            "source_commit": SOURCE_COMMIT,
            "registry_sha256": registry_ref["sha256"],
            "review_protocol": protocol_ref,
            "review_protocol_sha256": protocol_ref["sha256"],
            "package_record_sha256": CANDIDATE_BINDING["candidate_record_sha256"],
            "candidate_maturity_sha256": CANDIDATE_BINDING["candidate_maturity_sha256"],
            "package_sha256": CANDIDATE_BINDING["archive_sha256"],
            "package_tree_sha256": CANDIDATE_BINDING["package_tree_sha256"],
            "authorization_sha256": authorization_ref["sha256"],
            "reservation_sha256": "8" * 64,
            "producer_usage_reservation_sha256s": [
                row["usage_reservation_sha256"] for row in artifacts
            ],
            "settlement_sha256": "9" * 64,
            "dispatch_manifest": {"protocol": "barrier-five-submit-before-await-v1", "expected_workers": 5},
            "results": results,
            "cold_review_authorized": False,
        }
        completion_ref = self.write_json("producer/completion.json", self.raw_completion)
        self.raw_completion_bytes = self.capture_completion_path.read_bytes()

        for index, (case_id, row) in enumerate(zip(CASES, artifacts), 1):
            payload = {
                "schema": "daee-producer-capture-complete-v1",
                "status": "PRODUCER_CAPTURE_COMPLETE",
                "candidate_id": CANDIDATE_ID,
                "source_commit": SOURCE_COMMIT,
                "cycle_id": CYCLE_ID,
                "case_id": case_id,
                "usage_reservation_sha256": row["usage_reservation_sha256"],
                "envelope_nonce": row["nonce"],
                "candidate_binding": copy.deepcopy(CANDIDATE_BINDING),
                "input_binding": {"sha256": row["raw_input"]["sha256"], "byte_count": row["raw_input"]["byte_count"]},
                "refs": {
                    "producer_completion": completion_ref,
                    "capture_evidence": row["capture"],
                    "raw_input": row["raw_input"],
                    "exact_prompt": row["prompt"],
                    "composite_runtime_context": row["context"],
                    "package_harness_parity": row["parity"],
                    "raw_output": row["captured_output"],
                    "execution_custody": row["custody"],
                    "provider_receipt": row["receipt"],
                },
                "non_claims": [
                    "capture completion is not structural finalization",
                    "structural finalization is not campaign success or semantic review",
                ],
            }
            record_path = capture_finalizer.publish_capture_complete_record(
                root=self.root,
                directory="producer/capture-records",
                payload=payload,
            )
            record_raw = record_path.read_bytes()
            record_ref = {
                "path": record_path.relative_to(self.root).as_posix(),
                "byte_count": len(record_raw),
                "sha256": hashlib.sha256(record_raw).hexdigest(),
            }
            stage07 = self.retain(f"stage07-{index}", f"answer {index}\n".encode(), ".md")
            handoff = self.retain_json(
                f"handoff-{index}",
                {"schema": "staged-runtime-handshake-v1", "case_id": case_id, "stage_order": [], "stages": []},
            )
            finalization = {
                "schema": "daee-single-call-stage-finalization-v1",
                "verdict": "SINGLE_CALL_STRUCTURAL_FINALIZATION_PASS",
                "case_id": case_id,
                "cycle_id": CYCLE_ID,
                "envelope_nonce": row["nonce"],
                "bindings": {
                    "candidate": copy.deepcopy(CANDIDATE_BINDING),
                    "input": copy.deepcopy(payload["input_binding"]),
                    "capture_complete_record": record_ref,
                    "capture_input_refs": copy.deepcopy(payload["refs"]),
                    "execution_tooling_manifest": copy.deepcopy(self.tooling_ref),
                },
                "capture": {
                    "raw_envelope": row["captured_output"],
                    "raw_input": row["raw_input"],
                    "stage07_output": {**stage07, "start": 0, "end": stage07["byte_count"]},
                },
                "checker_owned": {"staged_handoff_record": handoff},
                "non_claims": copy.deepcopy(NONCLAIMS),
            }
            finalization_ref = self.write_json(
                f"producer/structural-evidence/finalized/{case_id}/structural-finalization.json",
                finalization,
            )
            self.payloads.append(payload)
            self.capture_refs.append(record_ref)
            self.finalization_refs.append(finalization_ref)
            self.rows.append(
                {"case_id": case_id, "capture_record": record_ref, "structural_finalization": finalization_ref}
            )
        self.authority = {
            "authorization": copy.deepcopy(authorization_value),
            "authorization_sha256": authorization_ref["sha256"],
            "bindings": {},
            "output_contracts": {
                payload["case_id"]: {
                    "envelope_nonce": payload["envelope_nonce"],
                    "candidate_binding": copy.deepcopy(payload["candidate_binding"]),
                    "input_binding": copy.deepcopy(payload["input_binding"]),
                }
                for payload in self.payloads
            },
            "observation_finalizer": observation_finalizer_ref,
        }

    def replacement_finalization(self, index: int, mutate) -> dict[str, object]:
        original = json.loads((self.root / self.finalization_refs[index]["path"]).read_text(encoding="utf-8"))
        mutate(original)
        return self.write_json(f"producer/mutations/{uuid.uuid4().hex}.json", original)


@unittest.skipIf(promoter is None, "promotion module is not implemented")
class ProducerStructuralCompletionContract(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def _fixture_finalization(self, *, root: Path, finalization_ref: dict[str, object], **_kwargs):
        return json.loads((root / str(finalization_ref["path"])).read_text(encoding="utf-8"))

    def _dependency_mocks(self):
        assert promoter is not None
        return (
            mock.patch.object(
                promoter,
                "_revalidate_live_producer_completion",
                return_value=(
                    copy.deepcopy(self.fixture.raw_completion),
                    copy.deepcopy(self.fixture.authority),
                ),
            ),
            mock.patch.object(
                promoter.strict_finalizer,
                "revalidate_single_call_stage_capture",
                side_effect=self._fixture_finalization,
            ),
        )

    def promote(self, rows: list[dict[str, object]] | None = None) -> dict[str, object]:
        assert promoter is not None
        first, second = self._dependency_mocks()
        with first, second:
            return promoter.create_producer_structural_completion(
                custody_root=self.fixture.root,
                rows=copy.deepcopy(self.fixture.rows if rows is None else rows),
                authorization_path=self.fixture.authorization_path,
            )

    def revalidate(self, aggregate: dict[str, object], function=None) -> dict[str, object]:
        assert promoter is not None
        target = function or promoter.revalidate_producer_structural_completion
        first, second = self._dependency_mocks()
        with first, second:
            return target(self.fixture.root, aggregate)

    def test_exact_five_promotes_without_mutating_raw_completion(self) -> None:
        aggregate = self.promote()
        self.assertEqual("PRODUCER_STRUCTURAL_COMPLETE", aggregate["status"])
        self.assertEqual(CASES, aggregate["case_ids"])
        self.assertEqual(["PASS"] * 5, [row["structural_status"] for row in aggregate["results"]])
        self.assertEqual(self.fixture.raw_completion_bytes, self.fixture.capture_completion_path.read_bytes())
        self.assertEqual(aggregate, self.revalidate(aggregate))

    def test_exact_ordered_usage_reservation_members_survive_promotion(self) -> None:
        aggregate = self.promote()
        expected = self.fixture.raw_completion["producer_usage_reservation_sha256s"]
        self.assertEqual(expected, aggregate["producer_usage_reservation_sha256s"])
        self.assertEqual(
            expected,
            [row["usage_reservation_sha256"] for row in aggregate["results"]],
        )

    def test_per_case_usage_reservation_substitution_blocks_promotion(self) -> None:
        original = promoter.validate_capture_complete_record

        def substitute_first_member(*, root, record_path):
            validated = original(root=root, record_path=record_path)
            if validated["payload"]["case_id"] == CASES[0]:
                validated = copy.deepcopy(validated)
                validated["payload"]["usage_reservation_sha256"] = (
                    self.fixture.raw_completion["producer_usage_reservation_sha256s"][1]
                )
            return validated

        first, second = self._dependency_mocks()
        with first, second, mock.patch.object(
            promoter,
            "validate_capture_complete_record",
            side_effect=substitute_first_member,
        ):
            with self.assertRaisesRegex(
                promoter.StructuralCompletionError,
                "capture record identity mismatch",
            ):
                promoter.create_producer_structural_completion(
                    custody_root=self.fixture.root,
                    rows=copy.deepcopy(self.fixture.rows),
                    authorization_path=self.fixture.authorization_path,
                )
        self.assertFalse(self.fixture.aggregate_path.exists())

    def test_cardinality_duplicate_and_order_fail_before_publication(self) -> None:
        mutations = {
            "four": self.fixture.rows[:4],
            "six": [*self.fixture.rows, copy.deepcopy(self.fixture.rows[-1])],
            "duplicate": [*self.fixture.rows[:4], copy.deepcopy(self.fixture.rows[0])],
            "permuted": list(reversed(self.fixture.rows)),
        }
        for label, rows in mutations.items():
            with self.subTest(label=label), self.assertRaises(promoter.StructuralCompletionError):
                self.promote(rows)
            self.assertFalse(self.fixture.aggregate_path.exists())

    def test_identity_ref_crosslink_and_output_drift_fail(self) -> None:
        cases: list[tuple[str, list[dict[str, object]]]] = []
        for field, value in (
            ("candidate_id", "wrong"),
            ("source_commit", "f" * 40),
            ("archive_sha256", "f" * 64),
        ):
            rows = copy.deepcopy(self.fixture.rows)
            rows[0]["structural_finalization"] = self.fixture.replacement_finalization(
                0, lambda item, field=field, value=value: item["bindings"]["candidate"].__setitem__(field, value)
            )
            cases.append((field, rows))
        for field, value in (("cycle_id", "wrong"), ("case_id", CASES[1])):
            rows = copy.deepcopy(self.fixture.rows)
            rows[0]["structural_finalization"] = self.fixture.replacement_finalization(
                0, lambda item, field=field, value=value: item.__setitem__(field, value)
            )
            cases.append((field, rows))
        rows = copy.deepcopy(self.fixture.rows)
        rows[0]["capture_record"] = self.fixture.capture_refs[1]
        cases.append(("capture substitution", rows))
        rows = copy.deepcopy(self.fixture.rows)
        rows[0]["structural_finalization"] = self.fixture.finalization_refs[1]
        cases.append(("finalizer substitution", rows))
        rows = copy.deepcopy(self.fixture.rows)
        rows[0]["structural_finalization"] = self.fixture.replacement_finalization(
            0, lambda item: item["bindings"].__setitem__("capture_complete_record", self.fixture.capture_refs[1])
        )
        cases.append(("crosslink", rows))
        rows = copy.deepcopy(self.fixture.rows)
        rows[0]["structural_finalization"] = self.fixture.replacement_finalization(
            0, lambda item: item["capture"].__setitem__("raw_envelope", self.fixture.payloads[1]["refs"]["raw_output"])
        )
        cases.append(("output drift", rows))
        for label, rows in cases:
            with self.subTest(label=label), self.assertRaises(promoter.StructuralCompletionError):
                self.promote(rows)
            self.assertFalse(self.fixture.aggregate_path.exists())

    def test_collision_and_identical_replay_never_replace(self) -> None:
        aggregate = self.promote()
        frozen = self.fixture.aggregate_path.read_bytes()
        with self.assertRaises(promoter.StructuralCompletionError):
            self.promote()
        self.assertEqual(frozen, self.fixture.aggregate_path.read_bytes())
        self.fixture.aggregate_path.unlink()
        self.fixture.aggregate_path.write_bytes(b"preexisting-collision\n")
        with self.assertRaises(promoter.StructuralCompletionError):
            self.promote()
        self.assertEqual(b"preexisting-collision\n", self.fixture.aggregate_path.read_bytes())
        self.assertEqual("PRODUCER_STRUCTURAL_COMPLETE", aggregate["status"])

    def test_failed_promotion_leaves_no_aggregate_assessment_or_disclosure(self) -> None:
        with self.assertRaises(promoter.StructuralCompletionError):
            self.promote(self.fixture.rows[:4])
        self.assertFalse(self.fixture.aggregate_path.exists())
        self.assertFalse(self.fixture.assessment_claim.exists())
        self.assertFalse(self.fixture.disclosure.exists())
        self.assertEqual(self.fixture.raw_completion_bytes, self.fixture.capture_completion_path.read_bytes())

    def test_post_publication_revalidation_failure_rolls_back_exact_owned_aggregate(self) -> None:
        original = promoter.revalidate_producer_structural_completion
        with mock.patch.object(
            promoter,
            "revalidate_producer_structural_completion",
            side_effect=promoter.StructuralCompletionError("injected post-publication failure"),
        ):
            with self.assertRaisesRegex(
                promoter.StructuralCompletionError,
                "injected post-publication failure",
            ):
                self.promote()
        self.assertFalse(self.fixture.aggregate_path.exists())
        self.assertEqual(self.fixture.raw_completion_bytes, self.fixture.capture_completion_path.read_bytes())
        aggregate = self.promote()
        self.assertEqual(aggregate, self.revalidate(aggregate, original))

    def test_post_publication_failure_preserves_same_byte_path_replacement(self) -> None:
        replacement: dict[str, bytes] = {}

        def replace_then_fail(*_args, **_kwargs):
            raw = self.fixture.aggregate_path.read_bytes()
            self.fixture.aggregate_path.unlink()
            self.fixture.aggregate_path.write_bytes(raw)
            replacement["raw"] = raw
            raise promoter.StructuralCompletionError("injected after same-byte replacement")

        with mock.patch.object(
            promoter,
            "revalidate_producer_structural_completion",
            side_effect=replace_then_fail,
        ):
            with self.assertRaisesRegex(
                promoter.StructuralCompletionError,
                "exact owned rollback is unsafe",
            ):
                self.promote()
        self.assertTrue(self.fixture.aggregate_path.is_file())
        self.assertEqual(replacement["raw"], self.fixture.aggregate_path.read_bytes())

    def test_assessment_barrier_revalidates_aggregate_before_human_files(self) -> None:
        aggregate = self.promote()
        finalization = self.fixture.root / self.fixture.finalization_refs[0]["path"]
        finalization.write_bytes(finalization.read_bytes() + b"drift")
        with self.assertRaisesRegex(
            assessment_barrier.AssessmentBarrierError,
            "PRODUCER_STRUCTURAL_AGGREGATE_INVALID",
        ):
            assessment_barrier.validate_initial_assessment_set(
                self.fixture.root,
                aggregate,
                [],
                claimant="human:bounded-assessor",
            )


@unittest.skipIf(promoter is None, "promotion module is not implemented")
class ProductionShapedPromotionIntegration(unittest.TestCase):
    def test_scripted_five_capture_retains_tooling_and_cannot_cross_production_finalizer(self) -> None:
        import reviewed_campaign_orchestrator as orchestrator

        live_contract = load_test_module(
            "producer_structural_live_contract_helper",
            ROOT / "tests" / "reviewed-campaign-orchestration" / "test_contract.py",
        )
        single_call = load_test_module(
            "producer_structural_single_call_helper",
            ROOT / "tests" / "single-call-stage-finalization" / "test_contract.py",
        )

        with tempfile.TemporaryDirectory(prefix="daee-production-shaped-promotion-") as temp:
            root = Path(temp)
            fixture, authorization_path, executable, _skill_bytes = (
                live_contract.LiveProducerContractTests()._live_fixture(root, full_tooling=True)
            )
            auth, auth_sha = orchestrator._load_producer_authorization(
                root,
                authorization_path,
                allow_test_fixture=True,
            )
            bindings = orchestrator._validate_common_bindings(
                root,
                auth,
                allow_test_fixture=True,
            )
            contracts = orchestrator._producer_output_contracts(auth, auth_sha, bindings)
            registry_cases = bindings["registry"]["cases"]
            final_output = single_call.current_output_bytes()
            outputs: dict[str, bytes] = {}
            for case in registry_cases:
                case_id = case["case_id"]
                raw_input = (root / case["input_path"]).read_bytes()
                stages = single_call.canonical_stage_records()
                stages[0]["input_digest"] = hashlib.sha256(raw_input).hexdigest()
                contract = contracts[case_id]
                payload = {
                    "schema": "daee-single-call-stage-envelope-v1",
                    "envelope_nonce": contract["envelope_nonce"],
                    "case_id": case_id,
                    "cycle_id": auth["cycle_or_review_batch_id"],
                    "candidate_binding": copy.deepcopy(contract["candidate_binding"]),
                    "input_binding": copy.deepcopy(contract["input_binding"]),
                    "stage_records": stages,
                    "stage08_request": {
                        "id": "stage-08-verifier-sidecars",
                        "status": "pending-checker",
                        "owner": "private-source-bound-checker",
                        "input": "exact-stage07-tail",
                    },
                    "non_claims": list(single_call.envelope.REQUIRED_NON_CLAIMS),
                }
                nonce = contract["envelope_nonce"]
                stage_json = json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
                outputs[case_id] = (
                    f"DAEE-SINGLE-CALL-ENVELOPE-V1 {nonce}\n"
                    f"BEGIN-STAGE-JSON {nonce}\n"
                ).encode("ascii") + stage_json + (
                    f"\nEND-STAGE-JSON {nonce}\n"
                    f"BEGIN-FINAL-OUTPUT {nonce}\n"
                ).encode("ascii") + final_output

            class EnvelopeHost(live_contract._ScriptedCodexHost):
                def start(self, command, **kwargs):
                    process = super().start(command, **kwargs)
                    ordinal = len(self.starts) - 1
                    kwargs["output_path"].write_bytes(outputs[auth["case_ids"][ordinal]])
                    return process

            adapter = live_contract._ScriptedCodexTestAdapter(
                custody_root=root,
                codex_executable=executable,
                host=EnvelopeHost(),
                command_timeout_seconds=30,
            )
            completion = orchestrator.run_producer_cohort(
                root,
                authorization_path,
                adapter,
                allow_test_fixture=True,
            )
            self.assertEqual(
                completion,
                orchestrator.revalidate_live_producer_completion(
                    root,
                    authorization_path,
                    completion,
                    allow_test_fixture=True,
                ),
            )
            self.assertEqual(
                orchestrator.SCRIPTED_CODEX_TEST_MODE,
                completion["execution_mode"],
            )
            self.assertIs(completion["test_only"], True)
            tooling_ref = auth["execution_tooling_manifest"]
            for result in completion["results"]:
                capture = json.loads(
                    (root / result["capture_evidence"]["path"]).read_text(encoding="utf-8")
                )
                custody = json.loads(
                    (root / capture["execution_custody"]["path"]).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    tooling_ref,
                    custody["execution_tooling_manifest"],
                )

            completion_raw = (root / "producer/completion.json").read_bytes()
            completion_ref = {
                "path": "producer/completion.json",
                "byte_count": len(completion_raw),
                "sha256": hashlib.sha256(completion_raw).hexdigest(),
            }
            result = completion["results"][0]
            case_id = result["case_id"]
            capture = json.loads(
                (root / result["capture_evidence"]["path"]).read_text(encoding="utf-8")
            )
            contract = contracts[case_id]
            payload = {
                "schema": "daee-producer-capture-complete-v1",
                "status": "PRODUCER_CAPTURE_COMPLETE",
                "candidate_id": auth["candidate_id"],
                "source_commit": auth["source_commit"],
                "cycle_id": auth["cycle_or_review_batch_id"],
                "case_id": case_id,
                "usage_reservation_sha256": completion[
                    "producer_usage_reservation_sha256s"
                ][0],
                "envelope_nonce": contract["envelope_nonce"],
                "candidate_binding": copy.deepcopy(contract["candidate_binding"]),
                "input_binding": copy.deepcopy(contract["input_binding"]),
                "refs": {
                    "producer_completion": completion_ref,
                    "capture_evidence": copy.deepcopy(result["capture_evidence"]),
                    "raw_input": copy.deepcopy(capture["raw_input"]),
                    "exact_prompt": copy.deepcopy(capture["prompt"]),
                    "composite_runtime_context": copy.deepcopy(capture["runtime_context"]),
                    "package_harness_parity": copy.deepcopy(capture["package_harness_parity"]),
                    "raw_output": copy.deepcopy(capture["raw_output"]),
                    "execution_custody": copy.deepcopy(capture["execution_custody"]),
                    "provider_receipt": copy.deepcopy(result["provider_receipt"]),
                },
                "non_claims": [
                    "capture completion is not structural finalization",
                    "structural finalization is not campaign success or semantic review",
                ],
            }
            record_path = capture_finalizer.publish_capture_complete_record(
                root=root,
                directory="producer/capture-records",
                payload=payload,
            )
            run_relative = f"{auth['structural_evidence_root']}/finalized/{case_id}"
            with self.assertRaisesRegex(
                capture_finalizer.CaptureFinalizationError,
                "not an immutable live capture completion",
            ):
                capture_finalizer.finalize_capture_complete_record(
                    root=root,
                    record_path=record_path,
                    run_root=run_relative,
                )
            self.assertFalse((root / run_relative).exists())
            self.assertFalse((root / "producer/structural-completion.json").exists())


class PromotionModuleRedContract(unittest.TestCase):
    def test_promotion_module_exists(self) -> None:
        self.assertIsNotNone(promoter, "producer structural-completion promotion is not implemented")

    @unittest.skipIf(promoter is None, "promotion module is not implemented")
    def test_shallow_fabricated_finalizations_cannot_mint_structural_completion(self) -> None:
        fixture = Fixture()
        try:
            with mock.patch.object(
                promoter,
                "_revalidate_live_producer_completion",
                return_value=(
                    copy.deepcopy(fixture.raw_completion),
                    copy.deepcopy(fixture.authority),
                ),
            ):
                with self.assertRaisesRegex(
                    promoter.StructuralCompletionError,
                    "retained Stage01-08 finalization invalid",
                ):
                    promoter.create_producer_structural_completion(
                        custody_root=fixture.root,
                        rows=copy.deepcopy(fixture.rows),
                        authorization_path=fixture.authorization_path,
                    )
            self.assertFalse(fixture.aggregate_path.exists())
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
