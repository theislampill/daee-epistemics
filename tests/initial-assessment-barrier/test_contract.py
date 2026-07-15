#!/usr/bin/env python3
"""No-model contract tests for the human pre-disclosure assessment barrier."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from reviewed_campaign_orchestrator import (
    CampaignError,
    _expected_success_completion,
    _validate_packet_set,
    claim_initial_assessments,
)
from check_initial_assessment_barrier import AssessmentBarrierError, _load_artifact


CASES = [
    "gate88-secularism",
    "gate88-khaybar",
    "gate88-trinitarian-j173",
    "gate88-tst-lillard",
    "gate88-torah-quran-source-authentication",
]
STAGES = [
    "stage-01-intake",
    "stage-02-layer-a-diagnostic-ir",
    "stage-03-routing-owner-gate",
    "stage-04-burden-execution-act",
    "stage-05-mrp-reread-terminal-state",
    "stage-06-field-witness-nar",
    "stage-07-release-output",
    "stage-08-verifier-sidecars",
]
SOURCE_COMMIT = "a" * 40
CANDIDATE_ID = "candidate-assessment-contract"
CYCLE_ID = "cycle-assessment-contract"
HUMAN = "human:bounded-assessor"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def artifact(root: Path, path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def record_sha256(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


class BarrierFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.protocol = root / "review/reviewed-five-smoke-protocol.json"
        write_json(
            self.protocol,
            {
                "schema": "daee-smoke-matrix-v1",
                "kind": "review-protocol",
                "protocol_id": "reviewed-five-smoke-v1",
                "case_ids": CASES,
                "human_initial_assessment": {
                    "required_count": 5,
                    "all_hash_claimed_before_cold_review": True,
                    "cold_review_disclosure_forbidden_before_claim": True,
                },
            },
        )
        self.protocol_ref = artifact(root, self.protocol)
        self.results: list[dict[str, object]] = []
        self.case_surfaces: dict[str, dict[str, dict[str, object]]] = {}
        for case_id in CASES:
            case_root = root / "producer/structural-evidence" / case_id
            raw_capture = case_root / "capture/raw-envelope.bin"
            raw_input = case_root / "capture/raw-input.bin"
            output = case_root / "capture/stage07-output.md"
            raw_capture.parent.mkdir(parents=True, exist_ok=True)
            raw_capture.write_bytes(f"raw-envelope:{case_id}\n".encode())
            producer_capture = root / "producer/results" / f"{case_id}.txt"
            producer_capture.parent.mkdir(parents=True, exist_ok=True)
            producer_capture.write_bytes(raw_capture.read_bytes())
            raw_input.write_bytes(f"raw-input:{case_id}\n".encode())
            output.write_bytes(f"stage07-output:{case_id}\n".encode())
            handoff = case_root / "records/staged-handoff-record.json"
            write_json(
                handoff,
                {
                    "schema": "staged-runtime-handshake-v1",
                    "case_id": case_id,
                    "stage_order": STAGES,
                    "stages": [{"id": stage_id, "status": "pass"} for stage_id in STAGES],
                },
            )
            surfaces = {
                "raw_capture": artifact(root, producer_capture),
                "finalizer_raw_capture": artifact(root, raw_capture),
                "input": artifact(root, raw_input),
                "output": artifact(root, output),
                "staged_handoff": artifact(root, handoff),
            }
            finalization = case_root / "structural-finalization.json"
            write_json(
                finalization,
                {
                    "schema": "daee-single-call-stage-finalization-v1",
                    "verdict": "SINGLE_CALL_STRUCTURAL_FINALIZATION_PASS",
                    "case_id": case_id,
                    "cycle_id": CYCLE_ID,
                    "bindings": {
                        "candidate": {
                            "candidate_id": CANDIDATE_ID,
                            "source_commit": SOURCE_COMMIT,
                        },
                        "input": {
                            "sha256": surfaces["input"]["sha256"],
                            "byte_count": surfaces["input"]["byte_count"],
                        },
                    },
                    "capture": {
                        "raw_envelope": surfaces["finalizer_raw_capture"],
                        "raw_input": surfaces["input"],
                        "stage07_output": {
                            **surfaces["output"],
                            "start": 0,
                            "end": surfaces["output"]["byte_count"],
                        },
                    },
                    "checker_owned": {"staged_handoff_record": surfaces["staged_handoff"]},
                },
            )
            surfaces["structural_finalization"] = artifact(root, finalization)
            self.case_surfaces[case_id] = surfaces
            self.results.append(
                {
                    "case_id": case_id,
                    "capture_status": "CAPTURED",
                    "structural_status": "PASS",
                    "output": surfaces["raw_capture"],
                    "structural_finalization": surfaces["structural_finalization"],
                }
            )
        self.production_auth: dict[str, object] = {
            "candidate_id": CANDIDATE_ID,
            "execution_mode": "LIVE_CODEX",
            "test_only": False,
            "cycle_or_review_batch_id": CYCLE_ID,
            "source_commit": SOURCE_COMMIT,
            "package_sha256": "7" * 64,
            "package_tree_sha256": "8" * 64,
            "review_protocol": copy.deepcopy(self.protocol_ref),
            "case_ids": CASES,
            "isolated_root_prefix": "isolated/producer",
        }
        self.completion = _expected_success_completion(
            self.production_auth,
            "1" * 64,
            {
                "protocol_sha256": self.protocol_ref["sha256"],
                "registry_sha256": "2" * 64,
                "package_sha256": "3" * 64,
                "candidate_sha256": "4" * 64,
            },
            self.results,
            lane="producer",
            reservation_sha256="5" * 64,
            settlement_sha256="6" * 64,
        )
        # This focused barrier fixture starts after structural promotion; the
        # live orchestrator constructor above deliberately stops at raw capture.
        self.completion["status"] = "PRODUCER_STRUCTURAL_COMPLETE"
        completion_sha = record_sha256(self.completion)
        self.assessment_rows: list[dict[str, object]] = []
        for case_id in CASES:
            surfaces = self.case_surfaces[case_id]
            assessment_path = root / "human-initial-assessments" / f"{case_id}.json"
            write_json(
                assessment_path,
                {
                    "schema": "daee-topology-initial-assessment-v2",
                    "assessment_id": f"initial-{case_id}",
                    "candidate_id": CANDIDATE_ID,
                    "source_commit": SOURCE_COMMIT,
                    "case_id": case_id,
                    "cycle_id": CYCLE_ID,
                    "producer_completion_sha256": completion_sha,
                    "review_protocol_sha256": self.protocol_ref["sha256"],
                    "structural_finalization": surfaces["structural_finalization"],
                    "raw_capture": surfaces["raw_capture"],
                    "input": surfaces["input"],
                    "output": surfaces["output"],
                    "staged_handoff": surfaces["staged_handoff"],
                    "reviewer_identity_or_accountable_role": HUMAN,
                    "relationship_to_producer": "independent",
                    "independence_basis": "synthetic test-only human fixture; not a production identity assertion",
                    "recorded_utc": "2026-01-01T12:00:00Z",
                    "question_answers": [
                        {
                            "question_id": "bounded-adequacy",
                            "answer": "PASS in this explicit no-model contract fixture",
                            "target_ids": [case_id],
                            "basis": "hash-bound synthetic fixture surfaces",
                        }
                    ],
                    "findings": [],
                    "verdict": "PASS",
                    "non_claims": ["synthetic fixture is not a real human assessment"],
                },
            )
            self.assessment_rows.append({"case_id": case_id, "assessment": artifact(root, assessment_path)})

    def rewrite_assessment(self, case_id: str, mutate) -> None:
        row = next(row for row in self.assessment_rows if row["case_id"] == case_id)
        path = self.root / row["assessment"]["path"]
        value = json.loads(path.read_text(encoding="utf-8"))
        mutate(value)
        write_json(path, value)
        row["assessment"] = artifact(self.root, path)


class InitialAssessmentBarrierTests(unittest.TestCase):
    def setUp(self) -> None:
        # These focused assessment fixtures synthesize the former structural
        # completion shape. Aggregate custody is exercised with real artifacts
        # by tests/producer-structural-completion/test_contract.py.
        self.aggregate_patcher = mock.patch(
            "check_initial_assessment_barrier.revalidate_producer_structural_completion",
            side_effect=lambda _root, completion: completion,
        )
        self.aggregate_patcher.start()

    def tearDown(self) -> None:
        self.aggregate_patcher.stop()

    def test_retained_assessment_json_rejects_duplicate_verdict_and_identity_keys(self) -> None:
        duplicates = {
            "verdict": b'{"verdict":"PARTIAL","verdict":"PASS"}\n',
            "reviewer_identity_or_accountable_role": (
                b'{"reviewer_identity_or_accountable_role":"human:other",'
                b'"reviewer_identity_or_accountable_role":"human:bounded-assessor"}\n'
            ),
        }
        for key, raw in duplicates.items():
            with self.subTest(key=key), tempfile.TemporaryDirectory(
                prefix=f"daee-assessment-duplicate-{key}-"
            ) as temp:
                root = Path(temp)
                path = root / "human-initial-assessments" / "assessment.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                self.assertIn(key, json.loads(raw.decode("utf-8")))
                with self.assertRaisesRegex(AssessmentBarrierError, "JSON_DUPLICATE_KEY"):
                    _load_artifact(
                        root,
                        artifact(root, path),
                        "RETAINED_ASSESSMENT",
                        json_required=True,
                    )

    def test_production_completion_constructor_carries_immutable_protocol_artifact_ref(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-assessment-completion-shape-") as temp:
            fixture = BarrierFixture(Path(temp))
            expected = copy.deepcopy(fixture.protocol_ref)
            self.assertEqual(fixture.completion["review_protocol"], expected)
            fixture.production_auth["review_protocol"]["sha256"] = "0" * 64
            self.assertEqual(fixture.completion["review_protocol"], expected)
            self.assertEqual(fixture.completion["review_protocol_sha256"], expected["sha256"])

    def test_production_rejects_hash_only_rows_without_creating_claim(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-assessment-hash-only-") as temp:
            fixture = BarrierFixture(Path(temp))
            hashes = [
                {"case_id": case_id, "assessment_sha256": "1" * 64}
                for case_id in CASES
            ]
            with self.assertRaisesRegex(CampaignError, "ASSESSMENT_ARTIFACT_REQUIRED"):
                claim_initial_assessments(
                    fixture.root,
                    fixture.completion,
                    hashes,
                    claimant=HUMAN,
                )
            self.assertFalse((fixture.root / "human-initial-assessments/claim.json").exists())

    def test_production_opens_validates_and_claims_exact_five_v2_artifacts_once(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-assessment-valid-") as temp:
            fixture = BarrierFixture(Path(temp))
            claim = claim_initial_assessments(
                fixture.root,
                fixture.completion,
                fixture.assessment_rows,
                claimant=HUMAN,
            )
            self.assertEqual(claim["schema"], "reviewed-campaign-initial-assessment-claim-v2")
            self.assertEqual(claim["status"], "ALL_FIVE_INITIAL_ASSESSMENTS_HASH_CLAIMED")
            self.assertEqual(claim["assessments"], fixture.assessment_rows)
            self.assertEqual(claim["source_commit"], SOURCE_COMMIT)
            self.assertEqual(claim["review_protocol_sha256"], fixture.protocol_ref["sha256"])
            with self.assertRaisesRegex(CampaignError, "CREATE_ONCE"):
                claim_initial_assessments(
                    fixture.root,
                    fixture.completion,
                    fixture.assessment_rows,
                    claimant=HUMAN,
                )

    def test_production_rejects_identity_binding_handoff_and_material_finding_drift(self) -> None:
        mutations = {
            "source": lambda value: value.update({"source_commit": "b" * 40}),
            "identity": lambda value: value.update({"reviewer_identity_or_accountable_role": "human:other"}),
            "independence": lambda value: value.update({"relationship_to_producer": "producer"}),
            "material": lambda value: value["findings"].append(
                {"finding_id": "material-1", "target_ids": [CASES[0]], "severity": "material", "basis": "fixture"}
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix=f"daee-assessment-{name}-") as temp:
                fixture = BarrierFixture(Path(temp))
                fixture.rewrite_assessment(CASES[0], mutate)
                with self.assertRaises(CampaignError):
                    claim_initial_assessments(
                        fixture.root,
                        fixture.completion,
                        fixture.assessment_rows,
                        claimant=HUMAN,
                    )
                self.assertFalse((fixture.root / "human-initial-assessments/claim.json").exists())

        with tempfile.TemporaryDirectory(prefix="daee-assessment-handoff-") as temp:
            fixture = BarrierFixture(Path(temp))
            handoff = fixture.root / fixture.case_surfaces[CASES[0]]["staged_handoff"]["path"]
            value = json.loads(handoff.read_text(encoding="utf-8"))
            value["stages"].pop()
            write_json(handoff, value)
            with self.assertRaisesRegex(CampaignError, "STAGED_HANDOFF"):
                claim_initial_assessments(
                    fixture.root,
                    fixture.completion,
                    fixture.assessment_rows,
                    claimant=HUMAN,
                )

    def test_every_production_identity_and_evidence_join_is_fail_closed(self) -> None:
        def substitute(surface: str):
            return lambda fixture, value: value.update(
                {surface: copy.deepcopy(fixture.case_surfaces[CASES[1]][surface])}
            )

        mutations = {
            "candidate": lambda _fixture, value: value.update({"candidate_id": "other-candidate"}),
            "case": lambda _fixture, value: value.update({"case_id": "other-case"}),
            "cycle": lambda _fixture, value: value.update({"cycle_id": "other-cycle"}),
            "producer-completion": lambda _fixture, value: value.update({"producer_completion_sha256": "0" * 64}),
            "review-protocol": lambda _fixture, value: value.update({"review_protocol_sha256": "0" * 64}),
            "structural-finalization": substitute("structural_finalization"),
            "raw-capture": substitute("raw_capture"),
            "input": substitute("input"),
            "output": substitute("output"),
            "staged-handoff": substitute("staged_handoff"),
            "verdict": lambda _fixture, value: value.update({"verdict": "PARTIAL"}),
            "recorded-time": lambda _fixture, value: value.update({"recorded_utc": "not-rfc3339"}),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix=f"daee-assessment-join-{name}-") as temp:
                fixture = BarrierFixture(Path(temp))
                fixture.rewrite_assessment(CASES[0], lambda value: mutate(fixture, value))
                with self.assertRaises(CampaignError):
                    claim_initial_assessments(
                        fixture.root,
                        fixture.completion,
                        fixture.assessment_rows,
                        claimant=HUMAN,
                    )
                self.assertFalse((fixture.root / "human-initial-assessments/claim.json").exists())

    def test_assessment_ref_hash_drift_and_nonpassing_structural_row_create_nothing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-assessment-ref-drift-") as temp:
            fixture = BarrierFixture(Path(temp))
            fixture.assessment_rows[0]["assessment"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(CampaignError, "CONTENT_ADDRESS"):
                claim_initial_assessments(
                    fixture.root,
                    fixture.completion,
                    fixture.assessment_rows,
                    claimant=HUMAN,
                )
            self.assertFalse((fixture.root / "human-initial-assessments/claim.json").exists())

        with tempfile.TemporaryDirectory(prefix="daee-assessment-missing-case-") as temp:
            fixture = BarrierFixture(Path(temp))
            fixture.completion["results"][0].pop("case_id")
            with self.assertRaisesRegex(CampaignError, "PRODUCER_STRUCTURAL_COMPLETION_REQUIRED"):
                claim_initial_assessments(
                    fixture.root,
                    fixture.completion,
                    fixture.assessment_rows,
                    claimant=HUMAN,
                )
            self.assertFalse((fixture.root / "human-initial-assessments/claim.json").exists())

        with tempfile.TemporaryDirectory(prefix="daee-assessment-structural-fail-") as temp:
            fixture = BarrierFixture(Path(temp))
            fixture.completion["results"][0]["structural_status"] = "FAIL"
            with self.assertRaisesRegex(CampaignError, "PRODUCER_STRUCTURAL_COMPLETION_REQUIRED"):
                claim_initial_assessments(
                    fixture.root,
                    fixture.completion,
                    fixture.assessment_rows,
                    claimant=HUMAN,
                )
            self.assertFalse((fixture.root / "human-initial-assessments/claim.json").exists())

    def test_hash_only_compatibility_requires_explicit_fake_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-assessment-fake-") as temp:
            fixture = BarrierFixture(Path(temp))
            fake_completion = copy.deepcopy(fixture.completion)
            fake_completion.update(
                {
                    "execution_mode": "DETERMINISTIC_FAKE_NO_DISPATCH",
                    "test_only": True,
                }
            )
            hashes = [
                {"case_id": case_id, "assessment_sha256": hashlib.sha256(case_id.encode()).hexdigest()}
                for case_id in CASES
            ]
            with self.assertRaisesRegex(CampaignError, "ASSESSMENT_ARTIFACT_REQUIRED"):
                claim_initial_assessments(
                    fixture.root,
                    fake_completion,
                    hashes,
                    claimant=HUMAN,
                )
            claim = claim_initial_assessments(
                fixture.root,
                fake_completion,
                hashes,
                claimant=HUMAN,
                allow_test_fixture=True,
            )
            self.assertEqual(claim["schema"], "reviewed-campaign-initial-assessment-claim-v1")
            self.assertEqual(claim["compatibility_mode"], "DETERMINISTIC_FAKE_HASH_ONLY")

    def test_cold_path_reopens_v2_assessments_before_packet_disclosure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-assessment-cold-readback-") as temp:
            fixture = BarrierFixture(Path(temp))
            claim = claim_initial_assessments(
                fixture.root,
                fixture.completion,
                fixture.assessment_rows,
                claimant=HUMAN,
            )
            first = fixture.root / fixture.assessment_rows[0]["assessment"]["path"]
            first.write_bytes(first.read_bytes() + b" ")
            auth = {
                "candidate_id": CANDIDATE_ID,
                "producer_cycle_id": CYCLE_ID,
                "execution_mode": "LIVE_CODEX",
                "test_only": False,
                "packet_set": [],
            }
            with self.assertRaisesRegex(CampaignError, "CONTENT_ADDRESS"):
                _validate_packet_set(
                    fixture.root,
                    auth,
                    fixture.completion,
                    claim,
                    allow_test_fixture=False,
                )


if __name__ == "__main__":
    unittest.main()
