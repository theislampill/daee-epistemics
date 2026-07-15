#!/usr/bin/env python3
"""Permanent no-model contract for one live producer capture finalization."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import finalize_producer_capture_complete as capture_finalizer
import execution_tooling_manifest as tooling_manifest


CASE_ID = "gate88-secularism"
CYCLE_ID = "b11-reviewed-five-smoke-01"
CANDIDATE_ID = "b11-candidate-01"
SOURCE_COMMIT = "2" * 40
NONCE = "0123456789abcdef0123456789abcdef"
USAGE_RESERVATION_SHA256S = [f"{index:064x}" for index in range(10, 15)]
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


class ProducerCaptureFinalizationContract(unittest.TestCase):
    def setUp(self) -> None:
        self.relative_root = Path(".daee") / "producer-capture-finalization-test" / uuid.uuid4().hex
        self.scratch = ROOT / self.relative_root
        self.scratch.mkdir(parents=True)
        self.run_relative = Path("finalized")
        self.run_root = self.scratch / self.run_relative

    def tearDown(self) -> None:
        shutil.rmtree(self.scratch, ignore_errors=True)

    def retain(self, role: str, raw: bytes, suffix: str) -> dict[str, object]:
        digest = hashlib.sha256(raw).hexdigest()
        path = self.scratch / "artifacts" / role / f"{digest}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {
            "path": path.relative_to(self.scratch).as_posix(),
            "byte_count": len(raw),
            "sha256": digest,
        }

    def retain_json(self, role: str, value: object) -> dict[str, object]:
        return self.retain(role, canonical(value), ".json")

    def fixture(self) -> tuple[dict[str, object], dict[str, bytes]]:
        raw_input = b"Why should revelation govern public reason?\n"
        prompt = b"DAEE validated runtime call context\n\n" + raw_input
        raw_output = (
            f"DAEE-SINGLE-CALL-ENVELOPE-V1 {NONCE}\n"
            f"BEGIN-STAGE-JSON {NONCE}\n{{}}\n"
            f"END-STAGE-JSON {NONCE}\n"
            f"BEGIN-FINAL-OUTPUT {NONCE}\nanswer\n"
        ).encode("utf-8")
        raw_input_ref = self.retain("raw-input", raw_input, ".input.bin")
        prompt_ref = self.retain("prompt", prompt, ".prompt.md")
        raw_output_ref = self.retain("raw-output", raw_output, ".output.md")
        producer_output_path = self.scratch / "producer" / "results" / f"{CASE_ID}.txt"
        producer_output_path.parent.mkdir(parents=True, exist_ok=True)
        producer_output_path.write_bytes(raw_output)
        producer_output_ref = {
            "path": producer_output_path.relative_to(self.scratch).as_posix(),
            "byte_count": len(raw_output),
            "sha256": hashlib.sha256(raw_output).hexdigest(),
        }

        context = {
            "schema": "daee-runtime-call-context-v1",
            "case_id": CASE_ID,
            "stage": "01-08",
            "call_index": 1,
            "runtime": {
                "delivery_mode": "explicit-prompt-components",
                "evidence_lane": "package-faithful",
                "package_profile": "execution-mini",
                "package_sha256": CANDIDATE_BINDING["package_tree_sha256"],
                "build_manifest_sha256": CANDIDATE_BINDING["build_manifest_sha256"],
                "skill_root_sha256": CANDIDATE_BINDING["skill_sha256"],
                "source_commit": SOURCE_COMMIT,
            },
            "input": {
                "path": "raw-input.bin",
                "sha256": raw_input_ref["sha256"],
                "byte_count": raw_input_ref["byte_count"],
                "included": True,
            },
            "state_capsule": {
                "bootstrap": True,
                "path": None,
                "sha256": None,
                "included": False,
                "validated": False,
            },
            "validated_state": {
                "route_shards": [],
                "owner_module_ids": [],
                "cold_clause_ids": [],
                "live_pressure": False,
                "ambiguous": False,
            },
            "selection": {
                "basis_kind": "stage-policy",
                "basis_ids": ["runtime-stage-01-08"],
                "candidate_components": ["raw-input", "package:SKILL.md"],
                "selected_components": ["raw-input", "package:SKILL.md"],
                "status": "selected",
                "hold_reason": None,
                "candidate_cap": 16,
            },
            "components": [
                {
                    "component_id": "raw-input",
                    "kind": "raw-input",
                    "source_path": "raw-input.bin",
                    "source_slice": {"kind": "whole-file", "start": 0, "end": len(raw_input)},
                    "sha256": raw_input_ref["sha256"],
                    "byte_count": len(raw_input),
                    "delivery": "prompt-bound",
                    "prompt_start_byte": len(prompt) - len(raw_input),
                    "prompt_end_byte": len(prompt),
                },
                {
                    "component_id": "package:SKILL.md",
                    "kind": "kernel",
                    "source_path": "SKILL.md",
                    "source_slice": {"kind": "whole-file", "start": 0, "end": 1},
                    "sha256": CANDIDATE_BINDING["skill_sha256"],
                    "byte_count": 1,
                    "delivery": "prompt-bound",
                    "prompt_start_byte": 0,
                    "prompt_end_byte": 1,
                },
            ],
            "cold_law_clauses_delivered": [],
            "producer_declared_used": [],
            "operation_bound_components": [],
            "prompt": {
                "path": "prompt.md",
                "sha256": prompt_ref["sha256"],
                "byte_count": prompt_ref["byte_count"],
                "includes_full_runtime": False,
                "includes_prior_full_output": False,
            },
            "delivery_status": "DELIVERED",
            "usage_status": "NOT_DECLARED",
            "proof_mode": "package-faithful",
            "host_receipt": None,
            "budget_telemetry": {
                "transport_frame_bytes": len(prompt) - len(raw_input) - 1,
                "runtime_component_bytes": 1,
                "capsule_bytes": 0,
                "local_excerpt_bytes": 0,
                "effective_context_bytes": len(prompt),
                "effective_context_limit": 500000,
                "selected_component_count": 2,
            },
            "non_claims": [
                "delivery does not prove internal model attention or semantic truth",
                "single-call context delivery does not prove Stage01-Stage08 completion",
            ],
        }
        context_ref = self.retain_json("runtime-context", context)
        package_parity = {
            "schema": "daee-package-harness-parity-v1",
            "classification": "package-faithful",
            "package_profile": "execution-mini",
            "package_tree_sha256": CANDIDATE_BINDING["package_tree_sha256"],
        }
        parity_ref = self.retain_json("package-parity", package_parity)
        capture_bindings = {
            "raw_input": raw_input_ref,
            "exact_prompt": prompt_ref,
            "composite_runtime_context": context_ref,
            "package_harness_parity": parity_ref,
        }
        output_contract = {
            "schema": "daee-single-call-output-envelope-contract-v1",
            "envelope_nonce": NONCE,
            "case_id": CASE_ID,
            "cycle_id": CYCLE_ID,
            "candidate_binding": copy.deepcopy(CANDIDATE_BINDING),
            "input_binding": {
                "sha256": raw_input_ref["sha256"],
                "byte_count": raw_input_ref["byte_count"],
            },
            "transport": "daee-single-call-stage-envelope-v1",
            "stage08_owner": "private-source-bound-checker",
        }
        tooling_manifest_value = {
            "schema": "daee-stage07-execution-tooling-manifest-v1",
            "kind": "execution-tooling-manifest",
            "source_commit": SOURCE_COMMIT,
            "source_tree": "7" * 40,
            "profile": "stage07-release",
            "membership": {
                "snapshot_roots": ["tools", "schema"],
                "runtime_resources": ["tests/fixture"],
            },
            "result_order": ["fixture-check"],
            "file_count": 1,
            "aggregate_algorithm": "sha256-domain-canonical-json-stage07-tooling-v1",
            "aggregate_sha256": "",
            "files": [
                {
                    "path": "tools/fixture.py",
                    "git_mode": "100644",
                    "blob_oid": "8" * 40,
                    "byte_count": 8,
                    "sha256": "9" * 64,
                }
            ],
        }
        tooling_manifest_value["aggregate_sha256"] = tooling_manifest._aggregate_sha256(
            tooling_manifest_value
        )
        tooling_manifest_ref = self.retain_json(
            "execution-tooling-manifest",
            tooling_manifest_value,
        )
        execution_custody = {
            "schema": "reviewed-campaign-execution-custody-v1",
            "lane": "producer",
            "candidate_id": CANDIDATE_ID,
            "source_commit": SOURCE_COMMIT,
            "cycle_or_review_batch_id": CYCLE_ID,
            "case_id": CASE_ID,
            "subject_id": f"producer:{CASE_ID}",
            "usage_reservation_sha256": USAGE_RESERVATION_SHA256S[0],
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "provider_settings": {
                "effective_context_limit_bytes": 500000,
                "command_timeout_seconds": 30,
                "observation_protocol": "concurrent-five-shared-deadline-v1",
            },
            "execution_tooling_manifest": tooling_manifest_ref,
            "single_call_output_contract": output_contract,
            "capture_bindings": capture_bindings,
        }
        execution_ref = self.retain_json("execution-custody", execution_custody)
        credential_ref = self.retain_json(
            "credential-scan",
            {"schema": "reviewed-campaign-credential-residue-scan-v1", "status": "PASS"},
        )
        provider_receipt = {
            "call_id": f"{CYCLE_ID}:call-01",
            "candidate_id": CANDIDATE_ID,
            "cycle_or_review_batch_id": CYCLE_ID,
            "case_id": CASE_ID,
            "subject_id": f"producer:{CASE_ID}",
            "usage_reservation_sha256": USAGE_RESERVATION_SHA256S[0],
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "status": "COMPLETED",
            "terminal_transport_status": "COMPLETED",
            "provider_call_id": "codex-thread:test-call-01",
            "usage": {"status": "RECORDED", "input_tokens": 1, "output_tokens": 1},
            "cost": {"unit": "usd", "value": "unknown", "status": "UNAVAILABLE"},
        }
        provider_ref = self.retain_json("provider-receipt", provider_receipt)
        capture_evidence = {
            "schema": "reviewed-campaign-live-capture-v1",
            "status": "CAPTURED",
            "candidate_id": CANDIDATE_ID,
            "source_commit": SOURCE_COMMIT,
            "case_id": CASE_ID,
            "prompt": prompt_ref,
            "raw_input": raw_input_ref,
            "runtime_context": context_ref,
            "package_harness_parity": parity_ref,
            "raw_output": raw_output_ref,
            "completion_identity": {"provider_call_id": provider_receipt["provider_call_id"]},
            "credential_residue_scan": credential_ref,
            "execution_custody_sha256": execution_ref["sha256"],
            "execution_custody": execution_ref,
            "structural_status": "UNVERIFIED",
        }
        capture_ref = self.retain_json("capture-evidence", capture_evidence)
        producer_completion = {
            "schema": "reviewed-campaign-producer-completion-v1",
            "status": "PRODUCER_CAPTURE_COMPLETE",
            "execution_mode": "LIVE_CODEX",
            "test_only": False,
            "candidate_id": CANDIDATE_ID,
            "cycle_id": CYCLE_ID,
            "source_commit": SOURCE_COMMIT,
            "package_record_sha256": CANDIDATE_BINDING["candidate_record_sha256"],
            "candidate_maturity_sha256": CANDIDATE_BINDING["candidate_maturity_sha256"],
            "package_sha256": CANDIDATE_BINDING["archive_sha256"],
            "package_tree_sha256": CANDIDATE_BINDING["package_tree_sha256"],
            "reservation_sha256": "f" * 64,
            "producer_usage_reservation_sha256s": list(USAGE_RESERVATION_SHA256S),
            "results": [
                {
                    "case_id": CASE_ID,
                    "capture_status": "CAPTURED",
                    "structural_status": "UNVERIFIED",
                    "output": producer_output_ref,
                    "capture_evidence": capture_ref,
                    "provider_receipt": provider_ref,
                    "provider_receipt_sha256": provider_ref["sha256"],
                }
            ],
            "cold_review_authorized": False,
        }
        completion_ref = self.retain_json("producer-completion", producer_completion)
        payload = {
            "schema": "daee-producer-capture-complete-v1",
            "status": "PRODUCER_CAPTURE_COMPLETE",
            "candidate_id": CANDIDATE_ID,
            "source_commit": SOURCE_COMMIT,
            "cycle_id": CYCLE_ID,
            "case_id": CASE_ID,
            "usage_reservation_sha256": USAGE_RESERVATION_SHA256S[0],
            "envelope_nonce": NONCE,
            "candidate_binding": copy.deepcopy(CANDIDATE_BINDING),
            "input_binding": {
                "sha256": raw_input_ref["sha256"],
                "byte_count": raw_input_ref["byte_count"],
            },
            "refs": {
                "producer_completion": completion_ref,
                "capture_evidence": capture_ref,
                "raw_input": raw_input_ref,
                "exact_prompt": prompt_ref,
                "composite_runtime_context": context_ref,
                "package_harness_parity": parity_ref,
                "raw_output": raw_output_ref,
                "execution_custody": execution_ref,
                "provider_receipt": provider_ref,
            },
            "non_claims": [
                "capture completion is not structural finalization",
                "structural finalization is not campaign success or semantic review",
            ],
        }
        return payload, {"raw_input": raw_input, "prompt": prompt, "raw_output": raw_output}

    def publish(self, payload: dict[str, object]) -> Path:
        return capture_finalizer.publish_capture_complete_record(
            root=self.scratch,
            directory="capture-records",
            payload=payload,
        )

    def test_exact_capture_record_derives_only_bound_strict_finalizer_inputs(self) -> None:
        payload, raw = self.fixture()
        record_path = self.publish(payload)
        expected_digest = hashlib.sha256(canonical(payload)).hexdigest()
        self.assertEqual(record_path.name, f"{expected_digest}.producer-capture-complete.json")

        def strict_call(**kwargs):
            self.assertEqual(kwargs["raw_envelope"], raw["raw_output"])
            self.assertEqual(kwargs["raw_input"], raw["raw_input"])
            self.assertEqual(kwargs["expected_envelope_nonce"], NONCE)
            self.assertEqual(kwargs["expected_case_id"], CASE_ID)
            self.assertEqual(kwargs["expected_cycle_id"], CYCLE_ID)
            self.assertEqual(kwargs["expected_candidate_binding"], CANDIDATE_BINDING)
            self.assertEqual(kwargs["expected_input_binding"], payload["input_binding"])
            self.assertEqual(kwargs["capture_input_refs"], payload["refs"])
            return SimpleNamespace(run_root=self.run_root)

        with mock.patch.object(
            capture_finalizer.strict_finalizer,
            "finalize_single_call_stage_capture",
            side_effect=strict_call,
        ) as called:
            result = capture_finalizer.finalize_capture_complete_record(
                root=self.scratch,
                record_path=record_path,
                run_root=self.run_relative,
            )
        self.assertEqual(result.run_root, self.run_root)
        called.assert_called_once()

    def test_output_or_context_substitution_rejects_before_finalizer_or_run_root(self) -> None:
        expected_failure = {
            "raw_output": "producer output bytes differ from captured raw output",
            "composite_runtime_context": "capture evidence runtime_context artifact ref mismatch",
            "authorization_context_limit": "authorization-bound context limit mismatch",
            "authorization_command_timeout": "authorization-bound command timeout invalid",
            "observation_protocol": "authorization-bound concurrent observation protocol invalid",
            "reservation_completion": "producer completion usage reservation binding mismatch",
            "reservation_custody": "execution custody usage reservation mismatch",
            "reservation_receipt": "provider receipt case/subject/reservation mismatch",
            "package_parity": "package harness parity is not package-faithful",
            "provider_subject": "provider receipt case/subject/reservation mismatch",
        }
        for role in (
            "raw_output",
            "composite_runtime_context",
            "authorization_context_limit",
            "authorization_command_timeout",
            "observation_protocol",
            "reservation_completion",
            "reservation_custody",
            "reservation_receipt",
            "package_parity",
            "provider_subject",
        ):
            with self.subTest(role=role):
                payload, _raw = self.fixture()
                if role == "raw_output":
                    payload["refs"][role] = self.retain("substituted-output", b"substituted\n", ".output.md")
                elif role == "composite_runtime_context":
                    context = json.loads(
                        (self.scratch / payload["refs"][role]["path"]).read_text(encoding="utf-8")
                    )
                    context["budget_telemetry"]["effective_context_limit"] += 1
                    payload["refs"][role] = self.retain_json("substituted-context", context)
                elif role == "reservation_completion":
                    completion = json.loads(
                        (self.scratch / payload["refs"]["producer_completion"]["path"]).read_text(encoding="utf-8")
                    )
                    completion["producer_usage_reservation_sha256s"][0] = "9" * 64
                    payload["refs"]["producer_completion"] = self.retain_json(
                        "substituted-completion-reservation", completion
                    )
                elif role in {"authorization_context_limit", "authorization_command_timeout", "observation_protocol", "reservation_custody"}:
                    custody = json.loads(
                        (self.scratch / payload["refs"]["execution_custody"]["path"]).read_text(encoding="utf-8")
                    )
                    if role == "authorization_context_limit":
                        custody["provider_settings"]["effective_context_limit_bytes"] -= 1
                    elif role == "authorization_command_timeout":
                        custody["provider_settings"]["command_timeout_seconds"] = 0
                    elif role == "observation_protocol":
                        custody["provider_settings"]["observation_protocol"] = "serial-five-v1"
                    else:
                        custody["usage_reservation_sha256"] = "9" * 64
                    substituted = self.retain_json("substituted-custody-limit", custody)
                    payload["refs"]["execution_custody"] = substituted
                    capture = json.loads(
                        (self.scratch / payload["refs"]["capture_evidence"]["path"]).read_text(encoding="utf-8")
                    )
                    capture["execution_custody"] = substituted
                    capture["execution_custody_sha256"] = substituted["sha256"]
                    payload["refs"]["capture_evidence"] = self.retain_json(
                        "substituted-capture-limit", capture
                    )
                    completion = json.loads(
                        (self.scratch / payload["refs"]["producer_completion"]["path"]).read_text(encoding="utf-8")
                    )
                    completion["results"][0]["capture_evidence"] = payload["refs"]["capture_evidence"]
                    payload["refs"]["producer_completion"] = self.retain_json(
                        "substituted-completion-limit", completion
                    )
                elif role == "package_parity":
                    parity = json.loads(
                        (self.scratch / payload["refs"]["package_harness_parity"]["path"]).read_text(encoding="utf-8")
                    )
                    parity["package_tree_sha256"] = "9" * 64
                    substituted = self.retain_json("substituted-parity", parity)
                    payload["refs"]["package_harness_parity"] = substituted
                    custody = json.loads(
                        (self.scratch / payload["refs"]["execution_custody"]["path"]).read_text(encoding="utf-8")
                    )
                    custody["capture_bindings"]["package_harness_parity"] = substituted
                    substituted_custody = self.retain_json("substituted-custody-parity", custody)
                    payload["refs"]["execution_custody"] = substituted_custody
                    capture = json.loads(
                        (self.scratch / payload["refs"]["capture_evidence"]["path"]).read_text(encoding="utf-8")
                    )
                    capture["package_harness_parity"] = substituted
                    capture["execution_custody"] = substituted_custody
                    capture["execution_custody_sha256"] = substituted_custody["sha256"]
                    payload["refs"]["capture_evidence"] = self.retain_json(
                        "substituted-capture-parity", capture
                    )
                    completion = json.loads(
                        (self.scratch / payload["refs"]["producer_completion"]["path"]).read_text(encoding="utf-8")
                    )
                    completion["results"][0]["capture_evidence"] = payload["refs"]["capture_evidence"]
                    payload["refs"]["producer_completion"] = self.retain_json(
                        "substituted-completion-parity", completion
                    )
                else:
                    receipt = json.loads(
                        (self.scratch / payload["refs"]["provider_receipt"]["path"]).read_text(
                            encoding="utf-8"
                        )
                    )
                    if role == "reservation_receipt":
                        receipt["usage_reservation_sha256"] = "9" * 64
                    else:
                        receipt["subject_id"] = "producer:wrong-case"
                    substituted = self.retain_json("substituted-provider-subject", receipt)
                    payload["refs"]["provider_receipt"] = substituted
                    completion = json.loads(
                        (self.scratch / payload["refs"]["producer_completion"]["path"]).read_text(
                            encoding="utf-8"
                        )
                    )
                    completion["results"][0]["provider_receipt"] = substituted
                    completion["results"][0]["provider_receipt_sha256"] = substituted["sha256"]
                    payload["refs"]["producer_completion"] = self.retain_json(
                        "substituted-completion-provider-subject", completion
                    )
                record_path = self.publish(payload)
                with mock.patch.object(
                    capture_finalizer.strict_finalizer,
                    "finalize_single_call_stage_capture",
                ) as called:
                    with self.assertRaisesRegex(
                        capture_finalizer.CaptureFinalizationError,
                        expected_failure[role],
                    ):
                        capture_finalizer.finalize_capture_complete_record(
                            root=self.scratch,
                            record_path=record_path,
                            run_root=self.run_relative,
                        )
                called.assert_not_called()
                self.assertFalse(self.run_root.exists())


if __name__ == "__main__":
    unittest.main()
