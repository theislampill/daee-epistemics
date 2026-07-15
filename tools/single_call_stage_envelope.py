#!/usr/bin/env python3
"""Parse and validate the exact-byte DAEE single-call stage envelope.

This module is deterministic no-model custody code.  It does not invoke a
provider, produce Stage 08 evidence, declare semantic truth, or promote one
capture to campaign success.  Stage 08 remains private-source-bound checker
work over the exact Stage 07 output tail returned here.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from contract_validation import validate_schema_subset


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "single-call-stage-envelope.schema.json"
MODEL_STAGE_ORDER = (
    "stage-01-intake",
    "stage-02-layer-a-diagnostic-ir",
    "stage-03-routing-owner-gate",
    "stage-04-burden-execution-act",
    "stage-05-mrp-reread-terminal-state",
    "stage-06-field-witness-nar",
)
STAGE_ORDER = MODEL_STAGE_ORDER + ("stage-07-release-output",)
REQUIRED_NON_CLAIMS = (
    "stage08_checker_owned_not_model_authored",
    "structural_pass_not_semantic_truth",
    "one_capture_not_campaign_success",
)
OUTPUT_CONTRACT_SCHEMA = "daee-single-call-output-envelope-contract-v1"
_MARKER_PREFIXES = (
    b"DAEE-SINGLE-CALL-ENVELOPE-V1 ",
    b"BEGIN-STAGE-JSON ",
    b"END-STAGE-JSON ",
    b"BEGIN-FINAL-OUTPUT ",
)


class EnvelopeValidationError(ValueError):
    """Fail-closed single-call envelope validation error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class _DuplicateJsonKey(ValueError):
    pass


@dataclass(frozen=True)
class ParsedSingleCallEnvelope:
    """Immutable exact-byte capture view returned after deterministic checks."""

    envelope_nonce: str
    payload: dict[str, Any]
    raw_bytes: bytes
    raw_sha256: str
    raw_byte_count: int
    stage_json_bytes: bytes
    stage_json_sha256: str
    stage_json_start: int
    stage_json_end: int
    final_output_bytes: bytes
    final_output_sha256: str
    final_output_start: int
    final_output_end: int


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_envelope_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EnvelopeValidationError("schema", f"cannot load envelope schema: {exc}") from exc
    if not isinstance(payload, dict):
        raise EnvelopeValidationError("schema", "envelope schema root must be an object")
    return payload


def validate_output_envelope_contract(contract: Any) -> dict[str, Any]:
    """Validate one pre-dispatch contract; returned bytes are safe to prompt-bind."""

    envelope_schema = load_envelope_schema()
    selected = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema",
            "envelope_nonce",
            "case_id",
            "cycle_id",
            "candidate_binding",
            "input_binding",
            "transport",
            "stage08_owner",
        ],
        "properties": {
            "schema": {"const": OUTPUT_CONTRACT_SCHEMA},
            "envelope_nonce": {"$ref": "#/$defs/nonce"},
            "case_id": {"type": "string", "minLength": 1},
            "cycle_id": {"type": "string", "minLength": 1},
            "candidate_binding": {"$ref": "#/$defs/candidate_binding"},
            "input_binding": {"$ref": "#/$defs/input_binding"},
            "transport": {"const": "daee-single-call-stage-envelope-v1"},
            "stage08_owner": {"const": "private-source-bound-checker"},
        },
        "$defs": copy.deepcopy(envelope_schema["$defs"]),
    }
    issues = validate_schema_subset(contract, selected)
    if issues:
        summary = "; ".join(
            f"{issue.path} [{issue.keyword}] {issue.message}"
            for issue in issues[:8]
        )
        raise EnvelopeValidationError("output-contract", summary)
    return copy.deepcopy(contract)


def render_output_envelope_contract(contract: Mapping[str, Any]) -> bytes:
    """Render the exact checker-reconstructible output-only transport suffix."""

    exact = validate_output_envelope_contract(dict(contract))
    nonce = exact["envelope_nonce"]
    binding = {
        "schema": "daee-single-call-stage-envelope-v1",
        "envelope_nonce": nonce,
        "case_id": exact["case_id"],
        "cycle_id": exact["cycle_id"],
        "candidate_binding": exact["candidate_binding"],
        "input_binding": exact["input_binding"],
        "stage08_request": {
            "id": "stage-08-verifier-sidecars",
            "status": "pending-checker",
            "owner": "private-source-bound-checker",
            "input": "exact-stage07-tail",
        },
        "non_claims": list(REQUIRED_NON_CLAIMS),
    }
    binding_json = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    schema_json = json.dumps(load_envelope_schema(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return (
        "\nDAEE CHECKER-BOUND SINGLE-CALL OUTPUT CONTRACT\n"
        "Return only the exact transport below; do not add Markdown fences or text outside it. "
        "The JSON span MUST be one strict object satisfying the supplied schema and exact binding. "
        "Author Stage01 through Stage07 exactly once in order. Stage08 remains checker-owned: include "
        "only the exact pending stage08_request from the binding. The final governed answer is the "
        "immutable tail through EOF after BEGIN-FINAL-OUTPUT.\n"
        f"EXACT-BINDING {binding_json}\n"
        f"ENVELOPE-SCHEMA {schema_json}\n"
        "EXACT-TRANSPORT-SHAPE\n"
        f"DAEE-SINGLE-CALL-ENVELOPE-V1 {nonce}\n"
        f"BEGIN-STAGE-JSON {nonce}\n"
        "<STRICT-JSON-OBJECT-MATCHING-EXACT-BINDING-AND-ENVELOPE-SCHEMA>\n"
        f"END-STAGE-JSON {nonce}\n"
        f"BEGIN-FINAL-OUTPUT {nonce}\n"
        "<COMPLETE-GOVERNED-MARKDOWN-ANSWER-THROUGH-EOF>\n"
    ).encode("utf-8")


def validate_envelope_payload_schema(
    payload: Any,
    *,
    schema: dict[str, Any] | None = None,
) -> None:
    selected = schema if schema is not None else load_envelope_schema()
    issues = validate_schema_subset(payload, selected)
    if issues:
        summary = "; ".join(
            f"{issue.path} [{issue.keyword}] {issue.message}"
            for issue in issues[:8]
        )
        raise EnvelopeValidationError("schema", summary)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(f"duplicate JSON member {key!r}")
        result[key] = value
    return result


def _reject_nonfinite(token: str) -> Any:
    raise ValueError(f"non-finite JSON number {token!r} is forbidden")


def _strict_json_object(raw: bytes) -> dict[str, Any]:
    if not raw or raw[:1] != b"{" or raw[-1:] != b"}":
        raise EnvelopeValidationError(
            "json",
            "stage JSON span must begin with '{' and end with '}' without surrounding bytes",
        )
    try:
        text = raw.decode("utf-8", errors="strict")
        payload = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateJsonKey, ValueError) as exc:
        raise EnvelopeValidationError("json", f"stage JSON is not one strict object: {exc}") from exc
    if not isinstance(payload, dict):
        raise EnvelopeValidationError("json", "stage JSON root must be an object")
    return payload


def _require_exact_bindings(
    payload: dict[str, Any],
    *,
    marker_nonce: str,
    expected_envelope_nonce: str,
    expected_case_id: str,
    expected_cycle_id: str,
    expected_candidate_binding: Mapping[str, Any],
    expected_input_binding: Mapping[str, Any],
) -> None:
    comparisons = (
        ("marker nonce", marker_nonce, expected_envelope_nonce),
        ("payload envelope_nonce", payload.get("envelope_nonce"), expected_envelope_nonce),
        ("case_id", payload.get("case_id"), expected_case_id),
        ("cycle_id", payload.get("cycle_id"), expected_cycle_id),
        ("candidate_binding", payload.get("candidate_binding"), dict(expected_candidate_binding)),
        ("input_binding", payload.get("input_binding"), dict(expected_input_binding)),
    )
    for label, actual, expected in comparisons:
        if actual != expected:
            raise EnvelopeValidationError("binding", f"{label} does not match the dispatch binding")


def _validate_stage_records(payload: dict[str, Any]) -> None:
    records = payload.get("stage_records")
    if not isinstance(records, list):
        raise EnvelopeValidationError("stage-order", "stage_records must be a list")
    ids = tuple(
        record.get("id") if isinstance(record, dict) else None
        for record in records
    )
    if ids != STAGE_ORDER:
        raise EnvelopeValidationError(
            "stage-order",
            "model records must contain Stage01 through Stage07 exactly once and in order",
        )

    stage01 = records[0]
    input_binding = payload["input_binding"]
    if stage01.get("input_digest") != input_binding.get("sha256"):
        raise EnvelopeValidationError(
            "input-handoff",
            "Stage01 input_digest must equal the exact input binding sha256",
        )

    for record in records[:6]:
        missing_products = [
            field
            for field in record.get("produces", [])
            if field not in record
        ]
        if missing_products:
            raise EnvelopeValidationError(
                "stage-products",
                f"{record['id']} is missing declared product(s): {missing_products}",
            )

    # Current runner normalizers are deliberately used as an identity check,
    # never as a repair path.  Any rewrite means the model bytes were not the
    # canonical stage bytes and the envelope fails closed.
    try:
        import run_staged_current_skill_smoke as stage_runner
    except ImportError as exc:
        raise EnvelopeValidationError("stage-dependency", f"stage normalizer unavailable: {exc}") from exc
    for expected_id, record in zip(MODEL_STAGE_ORDER, records[:6]):
        try:
            normalized = stage_runner.normalized_stage(expected_id, copy.deepcopy(record))
        except Exception as exc:  # runner exposes HarnessError, kept dependency-local
            raise EnvelopeValidationError(
                "stage-normalization",
                f"{expected_id} is not accepted by the current canonical normalizer: {exc}",
            ) from exc
        if normalized != record:
            raise EnvelopeValidationError(
                "normalization-rewrite",
                f"{expected_id} would require normalization; rewriting captured model bytes is forbidden",
            )

    try:
        import check_staged_runtime_handshake as handshake
    except ImportError as exc:
        raise EnvelopeValidationError("stage-dependency", f"stage handshake validator unavailable: {exc}") from exc
    first_six = records[:6]
    stage_map = {record["id"]: record for record in first_six}
    semantic_errors = handshake.semantic_errors(
        ROOT / ".daee" / "single-call-envelope-in-memory.json",
        {"mode": "staged-current-skill-smoke", "stages": first_six},
        stage_map,
    )
    if semantic_errors:
        raise EnvelopeValidationError(
            "stage-semantics",
            "; ".join(semantic_errors[:8]),
        )

    stage05_terminal = records[4].get("terminal_states")
    stage07_terminal = records[6].get("release_terminal_states")
    if not isinstance(stage05_terminal, dict) or not stage05_terminal:
        raise EnvelopeValidationError("stage07-terminal-drift", "Stage05 terminal_states must be non-empty")
    if stage07_terminal != stage05_terminal:
        raise EnvelopeValidationError(
            "stage07-terminal-drift",
            "Stage07 release_terminal_states must exactly equal Stage05 terminal_states",
        )

    held_or_partial = any(
        record.get("status") in {"held", "partial"}
        for record in records[:6]
    ) or any(
        str(value) in handshake.HELD_TERMINAL_STATES
        for value in stage05_terminal.values()
    )
    if held_or_partial and records[6].get("closure_claim") == "complete":
        raise EnvelopeValidationError(
            "stage07-closure",
            "Stage07 cannot claim complete closure after a held or partial stage state",
        )


def _parse_transport(raw: bytes) -> tuple[str, bytes, int, int, bytes, int]:
    if not isinstance(raw, bytes):
        raise EnvelopeValidationError("type", "envelope input must be immutable bytes")
    if b"\xef\xbb\xbf" in raw:
        raise EnvelopeValidationError("bom", "UTF-8 BOM bytes are forbidden")
    if b"\x00" in raw:
        raise EnvelopeValidationError("nul", "NUL bytes are forbidden")
    if b"\r" in raw:
        raise EnvelopeValidationError("line-ending", "only LF line endings are accepted")
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise EnvelopeValidationError("utf8", f"envelope is not strict UTF-8: {exc}") from exc
    if b"END-FINAL-OUTPUT" in raw:
        raise EnvelopeValidationError(
            "closing-marker",
            "the final output is the immutable tail through EOF and has no closing marker",
        )

    for prefix in _MARKER_PREFIXES:
        count = raw.count(prefix)
        if count == 0:
            raise EnvelopeValidationError("marker", f"required marker {prefix.decode('ascii').strip()!r} is missing")
        if count != 1:
            raise EnvelopeValidationError(
                "marker-count",
                f"marker {prefix.decode('ascii').strip()!r} must occur exactly once",
            )

    first_lf = raw.find(b"\n")
    header_prefix = _MARKER_PREFIXES[0]
    if first_lf < 0 or not raw.startswith(header_prefix):
        raise EnvelopeValidationError("preamble", "envelope header must start at byte 0")
    header = raw[:first_lf]
    nonce_bytes = header[len(header_prefix) :]
    if len(nonce_bytes) != 32 or any(byte not in b"0123456789abcdef" for byte in nonce_bytes):
        raise EnvelopeValidationError("marker", "header nonce must be exactly 32 lowercase hex characters")
    nonce = nonce_bytes.decode("ascii")

    cursor = first_lf + 1
    begin_json = f"BEGIN-STAGE-JSON {nonce}\n".encode("ascii")
    if raw[cursor : cursor + len(begin_json)] != begin_json:
        raise EnvelopeValidationError("marker", "BEGIN-STAGE-JSON must carry the header nonce")
    stage_json_start = cursor + len(begin_json)

    end_json_line = f"\nEND-STAGE-JSON {nonce}\n".encode("ascii")
    end_line_start = raw.find(end_json_line, stage_json_start)
    if end_line_start < 0:
        raise EnvelopeValidationError("marker", "END-STAGE-JSON must carry the header nonce")
    stage_json_end = end_line_start
    cursor = end_line_start + len(end_json_line)

    begin_output = f"BEGIN-FINAL-OUTPUT {nonce}\n".encode("ascii")
    if raw[cursor : cursor + len(begin_output)] != begin_output:
        raise EnvelopeValidationError("marker", "BEGIN-FINAL-OUTPUT must carry the header nonce")
    final_output_start = cursor + len(begin_output)
    final_output = raw[final_output_start:]
    if not final_output or not final_output.strip():
        raise EnvelopeValidationError("empty-output", "final governed Markdown tail must be non-empty")

    return (
        nonce,
        raw[stage_json_start:stage_json_end],
        stage_json_start,
        stage_json_end,
        final_output,
        final_output_start,
    )


def parse_single_call_stage_envelope(
    raw: bytes,
    *,
    expected_envelope_nonce: str,
    expected_case_id: str,
    expected_cycle_id: str,
    expected_candidate_binding: Mapping[str, Any],
    expected_input_binding: Mapping[str, Any],
) -> ParsedSingleCallEnvelope:
    """Parse one exact envelope and reject every repair or identity drift."""

    (
        marker_nonce,
        stage_json_bytes,
        stage_json_start,
        stage_json_end,
        final_output_bytes,
        final_output_start,
    ) = _parse_transport(raw)
    payload = _strict_json_object(stage_json_bytes)
    records = payload.get("stage_records")
    if isinstance(records, list) and len(records) == len(STAGE_ORDER):
        ids = tuple(
            record.get("id") if isinstance(record, dict) else None
            for record in records
        )
        if ids != STAGE_ORDER:
            raise EnvelopeValidationError(
                "stage-order",
                "model records must contain Stage01 through Stage07 exactly once and in order",
            )
    validate_envelope_payload_schema(payload)
    _require_exact_bindings(
        payload,
        marker_nonce=marker_nonce,
        expected_envelope_nonce=expected_envelope_nonce,
        expected_case_id=expected_case_id,
        expected_cycle_id=expected_cycle_id,
        expected_candidate_binding=expected_candidate_binding,
        expected_input_binding=expected_input_binding,
    )
    _validate_stage_records(payload)

    return ParsedSingleCallEnvelope(
        envelope_nonce=marker_nonce,
        payload=copy.deepcopy(payload),
        raw_bytes=raw,
        raw_sha256=_sha256(raw),
        raw_byte_count=len(raw),
        stage_json_bytes=stage_json_bytes,
        stage_json_sha256=_sha256(stage_json_bytes),
        stage_json_start=stage_json_start,
        stage_json_end=stage_json_end,
        final_output_bytes=final_output_bytes,
        final_output_sha256=_sha256(final_output_bytes),
        final_output_start=final_output_start,
        final_output_end=len(raw),
    )


def verify_envelope_readback(parsed: ParsedSingleCallEnvelope, raw: bytes) -> None:
    """Verify a retained readback still contains the exact parsed bytes/spans."""

    if not isinstance(raw, bytes) or raw != parsed.raw_bytes:
        raise EnvelopeValidationError("readback-drift", "retained envelope bytes changed after parse")
    if len(raw) != parsed.raw_byte_count or _sha256(raw) != parsed.raw_sha256:
        raise EnvelopeValidationError("readback-drift", "retained envelope length or hash changed")
    stage_json = raw[parsed.stage_json_start : parsed.stage_json_end]
    if stage_json != parsed.stage_json_bytes or _sha256(stage_json) != parsed.stage_json_sha256:
        raise EnvelopeValidationError("readback-drift", "retained Stage JSON span changed")
    output = raw[parsed.final_output_start : parsed.final_output_end]
    if output != parsed.final_output_bytes or _sha256(output) != parsed.final_output_sha256:
        raise EnvelopeValidationError("readback-drift", "retained Stage07 output tail changed")
