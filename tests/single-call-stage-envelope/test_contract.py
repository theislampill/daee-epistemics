#!/usr/bin/env python3
"""Permanent no-model contract tests for the single-call stage envelope.

These tests never invoke a provider.  They prove only deterministic transport,
binding, staged-record, and exact-byte custody behavior.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import single_call_stage_envelope as envelope


NONCE = "0123456789abcdef0123456789abcdef"
CASE_ID = "gate88-secularism"
CYCLE_ID = "b11-single-call-envelope-contract"
CANDIDATE_BINDING = {
    "candidate_id": "b10-2ddd4d9-candidate-01",
    "source_commit": "2ddd4d9efab2b437331b3f5d6247cb8f02abcfdf",
    "candidate_record_sha256": "1" * 64,
    "candidate_maturity_sha256": "2" * 64,
    "archive_sha256": "3" * 64,
    "package_tree_sha256": "4" * 64,
    "skill_sha256": "5" * 64,
    "build_manifest_sha256": "6" * 64,
}
FINAL_OUTPUT = (
    "## Layer A - bounded diagnostic\n\n"
    "The retained answer continues through the exact final byte.\n\n"
    "## Restoration\n\nReturn the burden to sound reason.\n"
).encode("utf-8")


def canonical_stage_records() -> list[dict[str, object]]:
    source = json.loads(
        (
            ROOT
            / "tests"
            / "staged-runtime-handshake"
            / "valid"
            / "retained-a9-science-source.json"
        ).read_text(encoding="utf-8")
    )
    stages = copy.deepcopy(source["stages"][:6])
    stages[0]["input_digest"] = stages[0]["input_digest"].lower()

    stage04 = stages[3]
    stage04["act_row_details"] = [
        {
            "act_row": stage04["act_rows"][0],
            "body_ref": "¹B₁",
            "burden_id": "B1",
            "owner_id": "source-status-repair",
            "operation": "source-order",
            "pressure": "scientific-explanations-only-knowledge-source",
            "delta": "Δ¹B",
            "delta_result": "science-source-bounded",
            "land": "Land(¹B)+",
            "register_axis": "σ",
        },
        {
            "act_row": stage04["act_rows"][1],
            "body_ref": "¹B₂",
            "burden_id": "B1",
            "owner_id": "M1",
            "operation": "self-grounding-test",
            "pressure": "only-science-counts-standard",
            "delta": "Δ¹B",
            "delta_result": "self-authorizing-standard-invalidated",
            "land": "Land(¹B)+",
            "register_axis": "H",
        },
    ]
    stages[4]["produces"] = [
        "terminal_states",
        "dependency_graph_edges",
        "no_new_resultant_proof",
        "per_burden_reread",
    ]
    stages[5]["produces"] = [
        "field_witness_body_refs",
        "nar_burdens",
        "owner_activations",
        "normalized_activation_record",
        "register_deltas",
    ]
    stages.append(
        {
            "id": "stage-07-release-output",
            "status": "pass",
            "produces": ["release_output", "release_terminal_states"],
            "requires": ["field_witness_body_refs", "nar_burdens"],
            "release_output_transport": "exact-tail-after-marker",
            "release_terminal_states": copy.deepcopy(stages[4]["terminal_states"]),
            "closure_claim": "complete",
            "output_is_full_governed_answer": True,
        }
    )
    return stages


def valid_payload() -> dict[str, object]:
    stages = canonical_stage_records()
    return {
        "schema": "daee-single-call-stage-envelope-v1",
        "envelope_nonce": NONCE,
        "case_id": CASE_ID,
        "cycle_id": CYCLE_ID,
        "candidate_binding": copy.deepcopy(CANDIDATE_BINDING),
        "input_binding": {
            "sha256": stages[0]["input_digest"],
            "byte_count": 37,
        },
        "stage_records": stages,
        "stage08_request": {
            "id": "stage-08-verifier-sidecars",
            "status": "pending-checker",
            "owner": "private-source-bound-checker",
            "input": "exact-stage07-tail",
        },
        "non_claims": list(envelope.REQUIRED_NON_CLAIMS),
    }


def encode_envelope(
    payload: dict[str, object] | None = None,
    *,
    output: bytes = FINAL_OUTPUT,
    nonce: str = NONCE,
    json_bytes: bytes | None = None,
) -> bytes:
    if json_bytes is None:
        json_bytes = json.dumps(
            payload or valid_payload(),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    return (
        f"DAEE-SINGLE-CALL-ENVELOPE-V1 {nonce}\n"
        f"BEGIN-STAGE-JSON {nonce}\n"
    ).encode("ascii") + json_bytes + (
        f"\nEND-STAGE-JSON {nonce}\n"
        f"BEGIN-FINAL-OUTPUT {nonce}\n"
    ).encode("ascii") + output


def parse(raw: bytes, **overrides: object) -> envelope.ParsedSingleCallEnvelope:
    payload = valid_payload()
    arguments = {
        "expected_envelope_nonce": NONCE,
        "expected_case_id": CASE_ID,
        "expected_cycle_id": CYCLE_ID,
        "expected_candidate_binding": CANDIDATE_BINDING,
        "expected_input_binding": payload["input_binding"],
    }
    arguments.update(overrides)
    return envelope.parse_single_call_stage_envelope(raw, **arguments)


class SingleCallStageEnvelopeContract(unittest.TestCase):
    def assert_rejected(self, raw: bytes, code: str, **overrides: object) -> None:
        with self.assertRaises(envelope.EnvelopeValidationError) as caught:
            parse(raw, **overrides)
        self.assertEqual(caught.exception.code, code, str(caught.exception))

    def test_schema_and_valid_exact_byte_capture(self) -> None:
        payload = valid_payload()
        schema = envelope.load_envelope_schema()
        envelope.validate_envelope_payload_schema(payload, schema=schema)

        raw = encode_envelope(payload)
        parsed = parse(raw)
        self.assertEqual(parsed.raw_bytes, raw)
        self.assertEqual(parsed.raw_sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(parsed.stage_json_bytes, raw[parsed.stage_json_start : parsed.stage_json_end])
        self.assertEqual(parsed.final_output_bytes, FINAL_OUTPUT)
        self.assertEqual(parsed.final_output_start + len(FINAL_OUTPUT), len(raw))
        self.assertEqual(parsed.final_output_sha256, hashlib.sha256(FINAL_OUTPUT).hexdigest())
        envelope.verify_envelope_readback(parsed, raw)

    def test_transport_rejects_non_exact_bytes_and_marker_forms(self) -> None:
        valid = encode_envelope()
        mutations = {
            "preamble": (b"preamble\n" + valid, "preamble"),
            "bom": (b"\xef\xbb\xbf" + valid, "bom"),
            "nul": (valid + b"\x00", "nul"),
            "invalid-utf8": (valid + b"\x80", "utf8"),
            "crlf": (valid.replace(b"\n", b"\r\n", 1), "line-ending"),
            "missing-header": (valid.split(b"\n", 1)[1], "marker"),
            "wrong-begin-nonce": (
                valid.replace(
                    f"BEGIN-STAGE-JSON {NONCE}".encode("ascii"),
                    b"BEGIN-STAGE-JSON ffffffffffffffffffffffffffffffff",
                    1,
                ),
                "marker",
            ),
            "missing-end-marker": (
                valid.replace(f"END-STAGE-JSON {NONCE}\n".encode("ascii"), b"", 1),
                "marker",
            ),
            "duplicate-marker": (
                valid + f"BEGIN-STAGE-JSON {NONCE}\n".encode("ascii"),
                "marker-count",
            ),
            "closing-output-marker": (valid + b"END-FINAL-OUTPUT\n", "closing-marker"),
            "empty-output": (encode_envelope(output=b""), "empty-output"),
            "whitespace-output": (encode_envelope(output=b" \n\t"), "empty-output"),
            "truncated-before-final": (
                valid.split(f"BEGIN-FINAL-OUTPUT {NONCE}\n".encode("ascii"), 1)[0],
                "marker",
            ),
        }
        for label, (raw, code) in mutations.items():
            with self.subTest(label=label):
                self.assert_rejected(raw, code)

    def test_json_transport_is_strict(self) -> None:
        payload = valid_payload()
        valid_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        duplicate_key = valid_json.replace(
            b'"case_id":"gate88-secularism",',
            b'"case_id":"gate88-secularism","case_id":"gate88-secularism",',
            1,
        )
        mutations = {
            "malformed": b"[" + valid_json[1:],
            "duplicate-key": duplicate_key,
            "leading-space": b" " + valid_json,
            "trailing-space": valid_json + b" ",
            "trailing-object": valid_json + b"{}",
        }
        for label, encoded in mutations.items():
            with self.subTest(label=label):
                self.assert_rejected(encode_envelope(json_bytes=encoded), "json")

    def test_external_bindings_are_exact(self) -> None:
        raw = encode_envelope()
        wrong_candidate = copy.deepcopy(CANDIDATE_BINDING)
        wrong_candidate["archive_sha256"] = "f" * 64
        wrong_input = copy.deepcopy(valid_payload()["input_binding"])
        wrong_input["byte_count"] += 1
        mutations = {
            "nonce": {"expected_envelope_nonce": "f" * 32},
            "case": {"expected_case_id": "gate88-khaybar"},
            "cycle": {"expected_cycle_id": "another-cycle"},
            "candidate": {"expected_candidate_binding": wrong_candidate},
            "input": {"expected_input_binding": wrong_input},
        }
        for label, overrides in mutations.items():
            with self.subTest(label=label):
                self.assert_rejected(raw, "binding", **overrides)

    def test_payload_shape_stage_order_and_checker_boundary_fail_closed(self) -> None:
        mutations: dict[str, tuple[dict[str, object], str]] = {}

        extra = valid_payload(); extra["unexpected"] = True
        mutations["top-level-extra"] = (extra, "schema")

        missing = valid_payload(); missing["stage_records"].pop(2)
        mutations["missing-stage"] = (missing, "schema")

        duplicate = valid_payload(); duplicate["stage_records"][2] = copy.deepcopy(duplicate["stage_records"][1])
        mutations["duplicate-stage"] = (duplicate, "stage-order")

        reordered = valid_payload(); reordered["stage_records"][1:3] = reversed(reordered["stage_records"][1:3])
        mutations["reordered-stage"] = (reordered, "stage-order")

        model_stage08 = valid_payload(); model_stage08["stage_records"][5]["id"] = "stage-08-verifier-sidecars"
        mutations["model-stage08"] = (model_stage08, "stage-order")

        checker_drift = valid_payload(); checker_drift["stage08_request"]["owner"] = "model"
        mutations["checker-owner-drift"] = (checker_drift, "schema")

        nonclaim_drift = valid_payload(); nonclaim_drift["non_claims"].pop()
        mutations["nonclaim-drift"] = (nonclaim_drift, "schema")

        transport_drift = valid_payload(); transport_drift["stage_records"][-1]["release_output_transport"] = "copied-text"
        mutations["stage07-transport-drift"] = (transport_drift, "schema")

        payload_nonce_drift = valid_payload(); payload_nonce_drift["envelope_nonce"] = "f" * 32
        mutations["payload-nonce-drift"] = (payload_nonce_drift, "binding")

        for label, (payload, code) in mutations.items():
            with self.subTest(label=label):
                self.assert_rejected(encode_envelope(payload), code)

    def test_normalizer_rewrite_handoff_drift_and_terminal_drift_fail_closed(self) -> None:
        normalization = valid_payload()
        normalization["stage_records"][3]["act_row_details"][0]["register_axis"] = "sigma"

        handoff = valid_payload()
        handoff["stage_records"][2]["route_targets"] = ["B2"]

        terminal = valid_payload()
        terminal["stage_records"][-1]["release_terminal_states"] = {"B1": "held-with-reason"}

        input_handoff = valid_payload()
        input_handoff["stage_records"][0]["input_digest"] = "f" * 64

        mutations = {
            "normalizer-rewrite": (normalization, "normalization-rewrite"),
            "handoff": (handoff, "stage-semantics"),
            "terminal": (terminal, "stage07-terminal-drift"),
            "input-handoff": (input_handoff, "input-handoff"),
        }
        for label, (payload, code) in mutations.items():
            with self.subTest(label=label):
                self.assert_rejected(encode_envelope(payload), code)

    def test_each_declared_stage_product_is_present(self) -> None:
        payload = valid_payload()
        del payload["stage_records"][0]["retained_input"]
        self.assert_rejected(encode_envelope(payload), "stage-products")

    def test_output_tail_is_immutable_after_parse(self) -> None:
        raw = encode_envelope()
        parsed = parse(raw)
        mutated = raw[:-1] + (b"X" if raw[-1:] != b"X" else b"Y")
        with self.assertRaises(envelope.EnvelopeValidationError) as caught:
            envelope.verify_envelope_readback(parsed, mutated)
        self.assertEqual(caught.exception.code, "readback-drift")


if __name__ == "__main__":
    unittest.main(verbosity=2)
