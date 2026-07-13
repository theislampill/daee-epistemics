#!/usr/bin/env python3
"""Fail-closed reviewed five-smoke orchestration interfaces.

The production surface deliberately has no live provider implementation.  Tests may
inject a deterministic fake/no-dispatch adapter after exact custody and preflight
validation.  All durable mutations are create-once or delegated to the existing
CAS-governed campaign usage ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Protocol

from campaign_usage_ledger import head_snapshot, reserve, settle
from check_cold_comprehensiveness_review import validate_packet_manifest
from check_parallel_dispatch_manifest import chain_dispatch_events, validate_dispatch_manifest


SHA256_RE = re.compile(r"[0-9a-f]{64}")
GIT_OID_RE = re.compile(r"[0-9a-f]{40}")
HUMAN_ID_RE = re.compile(r"human:[a-z0-9][a-z0-9._-]*")
TASK_IDENTITY_RE = re.compile(r"/root(?:/[a-z0-9][a-z0-9_-]{0,63})*")
WINDOWS_DEVICE_NAMES = {
    "CON", "PRN", "AUX", "NUL", "CLOCK$",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
TASK6_IMPLEMENTATION_OWNER = "/root/task6_no_dispatch"
CONTINUATION_ISSUER = "/root"
TEST_EXECUTION_MODE = "DETERMINISTIC_FAKE_NO_DISPATCH"
PROVIDER_CAPABILITY_KEYS = {
    "schema",
    "adapter_kind",
    "adapter_version",
    "host_application_version",
    "test_only",
    "paid_provider_reachable",
    "live_execution_authorized",
}
PRODUCER_AUTH_KEYS = {
    "schema",
    "kind",
    "authorization_id",
    "one_use",
    "execution_mode",
    "test_only",
    "live_execution_authorized",
    "campaign_authorization_sha256",
    "candidate_id",
    "cycle_or_review_batch_id",
    "source_commit",
    "candidate_maturity",
    "package_record",
    "source_preflight",
    "registry",
    "review_protocol",
    "model",
    "reasoning_effort",
    "adapter_version",
    "host_application_version",
    "provider_settings",
    "cohort_size",
    "cohort_protocol",
    "case_ids",
    "isolated_root_prefix",
    "usage_ledger_root",
    "authorization_claim_path",
    "candidate_claim_path",
    "retry_lineage",
}
COLD_REVIEW_AUTH_KEYS = {
    "schema",
    "kind",
    "authorization_id",
    "one_use",
    "execution_mode",
    "test_only",
    "live_execution_authorized",
    "campaign_authorization_sha256",
    "candidate_id",
    "cycle_or_review_batch_id",
    "producer_cycle_id",
    "source_commit",
    "candidate_maturity",
    "package_record",
    "source_preflight",
    "registry",
    "review_protocol",
    "producer_completion",
    "assessment_claim",
    "packet_set",
    "model",
    "reasoning_effort",
    "adapter_version",
    "host_application_version",
    "provider_settings",
    "cohort_size",
    "cohort_protocol",
    "dispatch_barrier_protocol",
    "case_ids",
    "isolated_root_prefix",
    "usage_ledger_root",
    "authorization_claim_path",
    "packet_disclosure_path",
    "retry_lineage",
}
PRODUCER_PROVIDER_SETTINGS = {
    "response_surface": "package-faithful",
    "parallelism": 5,
    "fresh_context_per_case": True,
    "submit_before_observe": True,
}
COLD_REVIEW_PROVIDER_SETTINGS = {
    "response_surface": "cold-review-packet",
    "parallelism": 5,
    "fresh_context_per_case": True,
    "prior_conversation_supplied": False,
    "cross_case_context_supplied": False,
    "submit_before_observe": True,
}


class CampaignError(RuntimeError):
    """A deterministic orchestration contract rejection."""


class ProviderAdapter(Protocol):
    def capability(self) -> dict[str, object]: ...
    def submit(self, execution_custody: dict[str, object]) -> dict[str, object]: ...
    def observe(self, handle: str, execution_custody: dict[str, object]) -> dict[str, object]: ...


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def record_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _is_reparse(path: Path) -> bool:
    try:
        stat = path.lstat()
    except OSError as exc:
        raise CampaignError(f"PATH_CUSTODY_UNAVAILABLE: {path}") from exc
    return path.is_symlink() or bool(getattr(stat, "st_file_attributes", 0) & 0x400)


def _portable_relative_parts(relative: object, role: str) -> tuple[str, ...]:
    invalid = not isinstance(relative, str) or not relative
    if invalid:
        raise CampaignError(f"PATH_CUSTODY_{role.upper()}_PORTABLE_RELATIVE_PATH_REQUIRED")
    assert isinstance(relative, str)
    parts = tuple(relative.split("/"))
    invalid = (
        relative.startswith(("/", "\\"))
        or "\\" in relative
        or re.match(r"^[A-Za-z]:", relative) is not None
        or any(part in {"", ".", ".."} for part in parts)
        or any(":" in part for part in parts)
        or any(part.endswith((".", " ")) for part in parts)
        or any(part.split(".", 1)[0].upper() in WINDOWS_DEVICE_NAMES for part in parts)
        or any(any(ord(character) < 32 for character in part) for part in parts)
    )
    if invalid:
        raise CampaignError(f"PATH_CUSTODY_{role.upper()}_PORTABLE_RELATIVE_PATH_REQUIRED: {relative!r}")
    return parts


def _contained(root: Path, relative: object, role: str, *, must_exist: bool) -> Path:
    parts = _portable_relative_parts(relative, role)
    root_abs = Path(os.path.abspath(root))
    joined_abs = Path(os.path.abspath(root_abs.joinpath(*parts)))
    try:
        joined_abs.relative_to(root_abs)
    except ValueError as exc:
        raise CampaignError(f"PATH_CUSTODY_{role.upper()}: path escapes custody root")
    if joined_abs == root_abs:
        raise CampaignError(f"PATH_CUSTODY_{role.upper()}_PORTABLE_RELATIVE_PATH_REQUIRED")
    current = root_abs
    if root_abs.exists() and _is_reparse(root_abs):
        raise CampaignError(f"PATH_CUSTODY_{role.upper()}: custody root is symlink/reparse")
    for part in parts:
        current = current / part
        if current.exists() and _is_reparse(current):
            raise CampaignError(f"PATH_CUSTODY_{role.upper()}: symlink/reparse component")
    if current != joined_abs:
        raise CampaignError(f"PATH_CUSTODY_{role.upper()}: lexical path escapes custody root")
    if must_exist and not current.is_file():
        raise CampaignError(f"PATH_CUSTODY_{role.upper()}: file is unavailable")
    return current


def _relative_to_root(root: Path, path: Path, role: str) -> str:
    root_abs = Path(os.path.abspath(root))
    path_abs = Path(os.path.abspath(path))
    try:
        relative = path_abs.relative_to(root_abs)
    except ValueError as exc:
        raise CampaignError(f"PATH_CUSTODY_{role.upper()}: path escapes custody root") from exc
    _contained(root_abs, relative.as_posix(), role, must_exist=True)
    return relative.as_posix()


def _load_canonical_json(path: Path, role: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignError(f"{role.upper()}_JSON_INVALID") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise CampaignError(f"{role.upper()}_CANONICAL_JSON_REQUIRED")
    return value, raw


def _load_ref(root: Path, value: object, role: str) -> tuple[dict[str, Any], Path, str]:
    if not isinstance(value, dict) or set(value) != {"path", "byte_count", "sha256"}:
        raise CampaignError(f"{role.upper()}_REF_SHAPE")
    expected = value.get("sha256")
    if not isinstance(expected, str) or SHA256_RE.fullmatch(expected) is None:
        raise CampaignError(f"{role.upper()}_REF_HASH")
    path = _contained(root, value.get("path"), role, must_exist=True)
    raw = path.read_bytes()
    if value.get("byte_count") != len(raw) or hashlib.sha256(raw).hexdigest() != expected:
        raise CampaignError(f"{role.upper()}_CONTENT_ADDRESS")
    try:
        record = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignError(f"{role.upper()}_JSON_INVALID") from exc
    if not isinstance(record, dict):
        raise CampaignError(f"{role.upper()}_JSON_OBJECT_REQUIRED")
    return record, path, expected


def _publish_once_json(root: Path, relative: str, value: object, role: str) -> dict[str, object]:
    path = _contained(root, relative, role, must_exist=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    _contained(root, path.parent.relative_to(Path(os.path.abspath(root))).as_posix(), f"{role}_parent", must_exist=False)
    raw = canonical_bytes(value)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise CampaignError(f"CREATE_ONCE_{role.upper()}: destination already exists") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if path.read_bytes() != raw:
        raise CampaignError(f"CREATE_ONCE_{role.upper()}: readback differs")
    return {"path": relative, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _publish_or_adopt_exact_json(root: Path, relative: str, value: object, role: str) -> dict[str, object]:
    raw = canonical_bytes(value)
    path = _contained(root, relative, role, must_exist=False)
    if path.exists():
        if not path.is_file() or path.read_bytes() != raw:
            raise CampaignError(f"TERMINAL_PUBLICATION_SUBSTITUTION_{role.upper()}")
        return {"path": relative, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    try:
        return _publish_once_json(root, relative, value, role)
    except CampaignError as exc:
        if path.is_file() and path.read_bytes() == raw:
            return {"path": relative, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        raise CampaignError(f"TERMINAL_PUBLICATION_SUBSTITUTION_{role.upper()}: {exc}") from exc


def _publish_once_bytes(root: Path, relative: str, raw: bytes, role: str) -> dict[str, object]:
    path = _contained(root, relative, role, must_exist=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise CampaignError(f"CREATE_ONCE_{role.upper()}: destination already exists") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if path.read_bytes() != raw:
        raise CampaignError(f"CREATE_ONCE_{role.upper()}: readback differs")
    return {"path": relative, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _existing_ref(root: Path, relative: str, role: str) -> dict[str, object]:
    path = _contained(root, relative, role, must_exist=True)
    raw = path.read_bytes()
    return {"path": relative, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _attempt_finalizer_path(lane: str, attempt_index: int) -> str:
    if attempt_index == 1:
        return f"{lane}/observation-finalizer.json"
    return f"{lane}/retry-finalizers/attempt-{attempt_index:02d}.json"


def _consume_attempt_claims(
    root: Path,
    auth: dict[str, Any],
    auth_sha: str,
    bindings: dict[str, Any],
    *,
    lane: str,
    authorization_claim: dict[str, Any],
) -> dict[str, Any]:
    auth_claim_path = auth["authorization_claim_path"]
    if _contained(root, auth_claim_path, f"{lane}_authorization_claim", must_exist=False).exists():
        raise CampaignError(f"CREATE_ONCE_{lane.upper().replace('-', '_')}_AUTHORIZATION_CLAIM: destination already exists")
    retry = bindings["retry"]
    continuation_claim_ref = None
    candidate_claim_ref = None
    candidate_claim_path = auth.get("candidate_claim_path") if lane == "producer" else "claims/candidate.json"
    if retry["attempt_index"] == 1:
        if lane == "producer" and _contained(root, candidate_claim_path, "candidate_claim", must_exist=False).exists():
            raise CampaignError("CANDIDATE_ALREADY_CLAIMED")
    else:
        continuation = retry["continuation"]
        assert isinstance(continuation, dict)
        try:
            candidate_claim_ref = _existing_ref(root, candidate_claim_path, "candidate_claim")
            candidate_claim, candidate_path, candidate_claim_sha = _load_ref(root, candidate_claim_ref, "candidate_claim")
            prior_finalizer, finalizer_path, finalizer_sha = _load_ref(root, continuation["prior_finalizer"], "retry_prior_finalizer_recheck")
        except CampaignError as exc:
            raise CampaignError(f"RETRY_CONTINUATION_CANDIDATE_CLAIM_UNAVAILABLE: {exc}") from exc
        expected_candidate_status = "CONSUMED_NO_DISPATCH" if lane == "producer" else "CONSUMED_OBSERVED"
        if candidate_claim.get("schema") != "reviewed-campaign-candidate-claim-v1" or candidate_claim.get("candidate_id") != auth["candidate_id"] or candidate_claim.get("candidate_maturity_sha256") != bindings["candidate_sha256"] or candidate_claim.get("irreversible") is not True:
            raise CampaignError("RETRY_CONTINUATION_CANDIDATE_CLAIM_BINDING")
        if finalizer_sha != retry["finalizer_sha256"] or prior_finalizer.get("schema") != "reviewed-campaign-observation-finalizer-v1" or prior_finalizer.get("candidate_id") != auth["candidate_id"] or prior_finalizer.get("lane") != lane or prior_finalizer.get("cycle_or_review_batch_id") != continuation["prior_batch_id"] or prior_finalizer.get("attempt_index") != continuation["prior_attempt_index"] or prior_finalizer.get("candidate_status") != expected_candidate_status or prior_finalizer.get("candidate_claim") != candidate_claim_ref:
            raise CampaignError("RETRY_CONTINUATION_CANDIDATE_CLAIM_FINALIZER_BINDING")
        # Re-read both retained artifacts immediately before consuming the one-use
        # continuation so a concurrent replacement cannot strand the authority.
        fresh_candidate_ref = _existing_ref(root, candidate_path.relative_to(root).as_posix(), "candidate_claim_recheck")
        fresh_finalizer_ref = _existing_ref(root, finalizer_path.relative_to(root).as_posix(), "retry_prior_finalizer_recheck")
        if fresh_candidate_ref["sha256"] != candidate_claim_sha or fresh_candidate_ref != candidate_claim_ref or fresh_finalizer_ref["sha256"] != finalizer_sha or fresh_finalizer_ref != continuation["prior_finalizer"]:
            raise CampaignError("RETRY_CONTINUATION_CANDIDATE_CLAIM_TOCTOU")
        continuation_claim = {
            "schema": "reviewed-campaign-retry-continuation-claim-v1",
            "authorization_id": continuation["authorization_id"],
            "authorization_sha256": retry["continuation_sha256"],
            "candidate_id": auth["candidate_id"],
            "lane": lane,
            "prior_batch_id": continuation["prior_batch_id"],
            "next_batch_id": auth["cycle_or_review_batch_id"],
            "next_attempt_index": retry["attempt_index"],
            "successor_cohort_authorization_sha256": auth_sha,
            "status": "CONSUMED",
            "one_use": True,
        }
        continuation_claim_ref = _publish_once_json(root, continuation["claim_path"], continuation_claim, "retry_continuation_claim")
    authorization_claim_ref = _publish_once_json(root, auth_claim_path, authorization_claim, f"{lane}_authorization_claim")
    if lane == "producer" and retry["attempt_index"] == 1:
        candidate_claim = {
            "schema": "reviewed-campaign-candidate-claim-v1",
            "candidate_id": auth["candidate_id"],
            "candidate_maturity_sha256": bindings["candidate_sha256"],
            "authorization_sha256": auth_sha,
            "cycle_id": auth["cycle_or_review_batch_id"],
            "state_before": "READY_UNUSED",
            "irreversible": True,
        }
        candidate_claim_ref = _publish_once_json(root, candidate_claim_path, candidate_claim, "candidate_claim")
    elif candidate_claim_ref is None and _contained(root, candidate_claim_path, "candidate_claim", must_exist=False).is_file():
        candidate_claim_ref = _existing_ref(root, candidate_claim_path, "candidate_claim")
    return {
        "authorization_claim": authorization_claim_ref,
        "candidate_claim": candidate_claim_ref,
        "continuation_claim": continuation_claim_ref,
    }


def _terminal_publication_paths(lane: str, auth: dict[str, Any], attempt_index: int) -> tuple[str, str]:
    return (
        f"incidents/{lane}-{auth['cycle_or_review_batch_id']}.json",
        _attempt_finalizer_path(lane, attempt_index),
    )


def _require_terminal_common(
    value: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    *,
    lane: str,
    attempt_index: int,
    role: str,
) -> None:
    expected = {
        "lane": lane,
        "attempt_index": attempt_index,
        "candidate_id": auth["candidate_id"],
        "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
        "authorization_sha256": auth_sha,
    }
    if value.get("schema") not in {
        "reviewed-campaign-incident-v1",
        "reviewed-campaign-observation-finalizer-v1",
    } or any(value.get(key) != expected_value for key, expected_value in expected.items()):
        raise CampaignError(f"TERMINAL_PUBLICATION_PREFLIGHT_{role.upper()}_BINDING")


def _expected_success_dispatch_manifest(auth: dict[str, Any], *, lane: str) -> dict[str, Any]:
    workers = _worker_inventory(auth, lane)
    raw_events: list[dict[str, object]] = [
        *(
            {"event": "worker_ready", "worker": row["worker"], "case_id": row["case_id"]}
            for row in workers
        ),
        {"event": "barrier_release"},
    ]
    for worker in workers:
        raw_events.extend(
            (
                {"event": "request_submit_started", "worker": worker["worker"], "case_id": worker["case_id"]},
                {"event": "call_entered_in_flight", "worker": worker["worker"], "case_id": worker["case_id"]},
            )
        )
    raw_events.append({"event": "all_five_in_flight"})
    for worker in workers:
        raw_events.append(
            {"event": "terminal_result_observed", "worker": worker["worker"], "case_id": worker["case_id"]}
        )
    manifest = {
        "schema": "daee-smoke-matrix-v1",
        "kind": "dispatch-manifest" if lane == "producer" else "cold-review-dispatch-manifest",
        "protocol": "barrier-five-submit-before-await-v1",
        "expected_workers": 5,
        "workers": workers,
        "events": chain_dispatch_events(raw_events),
    }
    if lane == "cold-review":
        manifest["cohort_protocol"] = "independent-cold-review-v1"
    return manifest


def _expected_success_completion(
    auth: dict[str, Any],
    auth_sha: str,
    bindings: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    lane: str,
    reservation_sha256: object,
    settlement_sha256: object,
) -> dict[str, Any]:
    common = {
        "candidate_id": auth["candidate_id"],
        "review_protocol_sha256": bindings["protocol_sha256"],
        "authorization_sha256": auth_sha,
        "reservation_sha256": reservation_sha256,
        "settlement_sha256": settlement_sha256,
        "dispatch_manifest": _expected_success_dispatch_manifest(auth, lane=lane),
        "results": results,
    }
    if lane == "producer":
        return {
            "schema": "reviewed-campaign-producer-completion-v1",
            "status": "PRODUCER_STRUCTURAL_COMPLETE",
            **common,
            "cycle_id": auth["cycle_or_review_batch_id"],
            "source_commit": auth["source_commit"],
            "registry_sha256": bindings["registry_sha256"],
            "package_record_sha256": bindings["package_sha256"],
            "candidate_maturity_sha256": bindings["candidate_sha256"],
            "cold_review_authorized": False,
        }
    return {
        "schema": "reviewed-campaign-cold-review-completion-v1",
        "status": "COLD_REVIEW_COHORT_COMPLETE",
        **common,
        "producer_cycle_id": auth["producer_cycle_id"],
        "review_batch_id": auth["cycle_or_review_batch_id"],
        "producer_completion_sha256": auth["producer_completion"]["sha256"],
        "assessment_claim_sha256": auth["assessment_claim"]["sha256"],
        "final_owner_acceptance": False,
    }


def _validate_success_finalizer(
    root: Path,
    usage_root: Path,
    value: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    bindings: dict[str, Any],
    *,
    lane: str,
    attempt_index: int,
) -> None:
    _require_terminal_common(
        value,
        auth,
        auth_sha,
        lane=lane,
        attempt_index=attempt_index,
        role="success_finalizer",
    )
    expected_review_status = None if lane == "producer" else "OBSERVED"
    if (
        value.get("terminal") is not True
        or value.get("dispatch_status") != "DETERMINISTIC_FAKE_COMPLETE"
        or value.get("candidate_status") != "CONSUMED_OBSERVED"
        or value.get("review_status") != expected_review_status
    ):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SUCCESS_FINALIZER_STATE")

    _validate_failure_claims(
        root,
        value,
        auth,
        auth_sha,
        bindings,
        lane=lane,
        attempt_index=attempt_index,
    )
    packet_disclosure = None
    if lane == "producer":
        if value.get("packet_disclosure") is not None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SUCCESS_PRODUCER_PACKET_DISCLOSURE")
    else:
        packet_disclosure = _validate_retained_json_ref(
            root,
            value.get("packet_disclosure"),
            auth["packet_disclosure_path"],
            "success_packet_disclosure",
        )
        if packet_disclosure.get("schema") != "reviewed-campaign-packet-disclosure-v1" or packet_disclosure.get("candidate_id") != auth["candidate_id"] or packet_disclosure.get("review_batch_id") != auth["cycle_or_review_batch_id"]:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SUCCESS_PACKET_DISCLOSURE_BINDING")

    snapshot = head_snapshot(usage_root)
    usage_value = {**value, "usage_unresolved": snapshot["unresolved_usage"]}
    reservation, settlement = _validate_failure_usage(
        usage_root,
        usage_value,
        auth,
        auth_sha,
        snapshot,
        lane=lane,
    )
    if reservation is None or settlement is None or settlement.get("completed") != 5 or settlement.get("unknown") != 0 or snapshot.get("unresolved_usage") is not False:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SUCCESS_USAGE_STATE")
    results = _validate_failure_results(
        root,
        {**value, "dispatch_classification": "OBSERVED"},
        auth,
        settlement,
        packet_disclosure,
        lane=lane,
    )

    completion_path = "producer/completion.json" if lane == "producer" else "cold-review/completion.json"
    completion = _validate_retained_json_ref(
        root,
        value.get("completion"),
        completion_path,
        "success_finalizer_completion",
    )
    expected_completion = _expected_success_completion(
        auth,
        auth_sha,
        bindings,
        results,
        lane=lane,
        reservation_sha256=value.get("reservation_sha256"),
        settlement_sha256=value.get("settlement_sha256"),
    )
    if completion != expected_completion:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SUCCESS_COMPLETION_EXACT_BINDING")


def _validate_retained_ref(
    root: Path,
    value: object,
    expected_path: str,
    role: str,
) -> tuple[Path, bytes]:
    expected = _existing_ref(root, expected_path, role)
    if value != expected:
        raise CampaignError(f"TERMINAL_PUBLICATION_PREFLIGHT_{role.upper()}_REF")
    path = _contained(root, expected_path, role, must_exist=True)
    return path, path.read_bytes()


def _validate_retained_json_ref(
    root: Path,
    value: object,
    expected_path: str,
    role: str,
) -> dict[str, Any]:
    path, raw = _validate_retained_ref(root, value, expected_path, role)
    record, canonical_raw = _load_canonical_json(path, role)
    if raw != canonical_raw:
        raise CampaignError(f"TERMINAL_PUBLICATION_PREFLIGHT_{role.upper()}_CANONICAL")
    return record


def _validate_failure_claims(
    root: Path,
    payload: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    bindings: dict[str, Any],
    *,
    lane: str,
    attempt_index: int,
) -> None:
    auth_claim = _validate_retained_json_ref(
        root,
        payload.get("authorization_claim"),
        auth["authorization_claim_path"],
        f"{lane}_resume_authorization_claim",
    )
    expected_auth_claim = {
        "schema": "reviewed-campaign-authorization-claim-v1",
        "kind": "producer-cohort" if lane == "producer" else "cold-review-cohort",
        "authorization_sha256": auth_sha,
        "candidate_id": auth["candidate_id"],
        "execution_mode": TEST_EXECUTION_MODE,
        "live_dispatch": False,
    }
    if lane == "producer":
        expected_auth_claim["cycle_or_review_batch_id"] = auth["cycle_or_review_batch_id"]
    else:
        expected_auth_claim.update(
            {
                "review_batch_id": auth["cycle_or_review_batch_id"],
                "producer_completion_sha256": auth["producer_completion"]["sha256"],
                "assessment_claim_sha256": auth["assessment_claim"]["sha256"],
            }
        )
    if auth_claim != expected_auth_claim:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_AUTHORIZATION_CLAIM_BINDING")

    candidate_path = auth.get("candidate_claim_path") if lane == "producer" else "claims/candidate.json"
    candidate_claim = _validate_retained_json_ref(
        root,
        payload.get("candidate_claim"),
        candidate_path,
        "resume_candidate_claim",
    )
    candidate_common = {
        "schema": "reviewed-campaign-candidate-claim-v1",
        "candidate_id": auth["candidate_id"],
        "candidate_maturity_sha256": bindings["candidate_sha256"],
        "state_before": "READY_UNUSED",
        "irreversible": True,
    }
    if any(candidate_claim.get(key) != expected for key, expected in candidate_common.items()):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CANDIDATE_CLAIM_BINDING")
    if set(candidate_claim) != {*candidate_common, "authorization_sha256", "cycle_id"}:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CANDIDATE_CLAIM_SHAPE")
    if attempt_index == 1 and lane == "producer":
        if candidate_claim.get("authorization_sha256") != auth_sha or candidate_claim.get("cycle_id") != auth["cycle_or_review_batch_id"]:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CANDIDATE_CLAIM_AUTHORIZATION")
    elif not isinstance(candidate_claim.get("authorization_sha256"), str) or SHA256_RE.fullmatch(candidate_claim["authorization_sha256"]) is None or not isinstance(candidate_claim.get("cycle_id"), str) or not candidate_claim["cycle_id"]:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CANDIDATE_CLAIM_LINEAGE")

    retry = bindings["retry"]
    if attempt_index == 1:
        if payload.get("continuation_claim") is not None or retry.get("continuation") is not None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CONTINUATION_CLAIM_UNEXPECTED")
        return
    continuation = retry.get("continuation")
    if not isinstance(continuation, dict):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CONTINUATION_AUTHORIZATION")
    continuation_claim = _validate_retained_json_ref(
        root,
        payload.get("continuation_claim"),
        continuation["claim_path"],
        "resume_continuation_claim",
    )
    expected_continuation_claim = {
        "schema": "reviewed-campaign-retry-continuation-claim-v1",
        "authorization_id": continuation["authorization_id"],
        "authorization_sha256": retry["continuation_sha256"],
        "candidate_id": auth["candidate_id"],
        "lane": lane,
        "prior_batch_id": continuation["prior_batch_id"],
        "next_batch_id": auth["cycle_or_review_batch_id"],
        "next_attempt_index": attempt_index,
        "successor_cohort_authorization_sha256": auth_sha,
        "status": "CONSUMED",
        "one_use": True,
    }
    if continuation_claim != expected_continuation_claim:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CONTINUATION_CLAIM_BINDING")


def _validate_failure_usage(
    usage_root: Path,
    payload: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    snapshot: dict[str, Any],
    *,
    lane: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    reservation_sha = payload.get("reservation_sha256")
    settlement_sha = payload.get("settlement_sha256")
    if reservation_sha is None:
        if settlement_sha is not None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_WITHOUT_RESERVATION")
        reservation = None
    else:
        if not isinstance(reservation_sha, str) or SHA256_RE.fullmatch(reservation_sha) is None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESERVATION_SHA")
        reservation_path = usage_root / "transactions" / f"{reservation_sha}.json"
        reservation, reservation_raw = _load_canonical_json(reservation_path, "resume_reservation")
        if hashlib.sha256(reservation_raw).hexdigest() != reservation_sha:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESERVATION_CONTENT_ADDRESS")
        expected_reservation = {
            "schema": "campaign-usage-transaction-v1",
            "kind": "reservation",
            "authorization_sha256": auth_sha,
            "candidate_id": auth["candidate_id"],
            "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
            "lane": lane,
            "reserved_calls": 5,
        }
        if any(reservation.get(key) != expected for key, expected in expected_reservation.items()):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESERVATION_BINDING")

    if settlement_sha is None:
        settlement = None
    else:
        if not isinstance(settlement_sha, str) or SHA256_RE.fullmatch(settlement_sha) is None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_SHA")
        settlement_path = usage_root / "transactions" / f"{settlement_sha}.json"
        settlement, settlement_raw = _load_canonical_json(settlement_path, "resume_settlement")
        if hashlib.sha256(settlement_raw).hexdigest() != settlement_sha:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_CONTENT_ADDRESS")
        expected_settlement = {
            "schema": "campaign-usage-transaction-v1",
            "kind": "settlement",
            "authorization_sha256": auth_sha,
            "candidate_id": auth["candidate_id"],
            "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
            "lane": lane,
            "reservation_transaction_sha256": reservation_sha,
            "reserved_calls": 5,
        }
        if any(settlement.get(key) != expected for key, expected in expected_settlement.items()):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_BINDING")
        if snapshot.get("last_transaction_sha256") != settlement_sha:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_NOT_USAGE_HEAD")

    if snapshot.get("open_reservations"):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_OPEN_RESERVATION")
    if payload.get("resulting_usage_head_sha256") != snapshot.get("head_sha256") or payload.get("usage_unresolved") is not snapshot.get("unresolved_usage"):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_USAGE_HEAD")
    return reservation, settlement


def _validate_failure_results(
    root: Path,
    payload: dict[str, Any],
    auth: dict[str, Any],
    settlement: dict[str, Any] | None,
    packet_disclosure: dict[str, Any] | None,
    *,
    lane: str,
) -> list[dict[str, Any]]:
    results = payload.get("observed_results")
    if not isinstance(results, list) or any(not isinstance(row, dict) for row in results):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULTS_SHAPE")
    classification = payload.get("dispatch_classification")
    expected_count = 0 if classification == "PROVED_NO_DISPATCH" else 5 if classification == "OBSERVED" else None
    if expected_count is not None and len(results) != expected_count:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULTS_COUNT")
    if classification in {"DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN"} and len(results) > 4:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_UNKNOWN_RESULTS_COUNT")
    if [row.get("case_id") for row in results] != auth["case_ids"][:len(results)]:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULTS_CASE_ORDER")

    receipts = settlement.get("provider_usage_receipts") if isinstance(settlement, dict) else None
    if results and (not isinstance(receipts, list) or len(receipts) != 5):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULTS_RECEIPTS")
    packet_by_case = {
        row.get("case_id"): row.get("manifest_sha256")
        for row in packet_disclosure.get("packet_set", [])
        if isinstance(row, dict)
    } if isinstance(packet_disclosure, dict) else {}
    for index, row in enumerate(results):
        case_id = auth["case_ids"][index]
        if lane == "producer":
            if set(row) != {"case_id", "structural_status", "output", "provider_receipt_sha256"} or row.get("structural_status") != "PASS":
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PRODUCER_RESULT_STATE")
            _validate_retained_ref(root, row.get("output"), f"producer/results/{case_id}.txt", f"producer_resume_result_{index + 1}")
        else:
            if set(row) != {"case_id", "review_status", "packet_manifest_sha256", "review_output", "provider_receipt_sha256"} or row.get("review_status") != "PASS":
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COLD_RESULT_STATE")
            if row.get("packet_manifest_sha256") != packet_by_case.get(case_id):
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COLD_RESULT_PACKET")
            _validate_retained_ref(root, row.get("review_output"), f"cold-review/results/{case_id}.txt", f"cold_resume_result_{index + 1}")
        if row.get("provider_receipt_sha256") != record_sha256(receipts[index]):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULT_RECEIPT")
    return results


def _validate_failure_resume_payload(
    root: Path,
    usage_root: Path,
    incident: dict[str, Any],
    payload: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    bindings: dict[str, Any],
    *,
    lane: str,
    attempt_index: int,
) -> None:
    if incident.get("terminal") is not True or payload.get("terminal") is not True:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_TERMINAL_STATE")
    mirrored = {
        "failure_phase": payload.get("failure_phase"),
        "dispatch_classification": payload.get("dispatch_classification"),
        "reservation_sha256": payload.get("reservation_sha256"),
        "settlement_sha256": payload.get("settlement_sha256"),
        "resulting_usage_head_sha256": payload.get("resulting_usage_head_sha256"),
        "completion": payload.get("completion"),
        "observed_result_count": len(payload.get("observed_results", [])) if isinstance(payload.get("observed_results"), list) else None,
    }
    if any(incident.get(key) != expected for key, expected in mirrored.items()):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_INCIDENT_PAYLOAD_BINDING")
    if incident.get("continuation_authorized") is not False or incident.get("retry_policy") != "external-owner-issued-one-use-continuation-required":
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_INCIDENT_RETRY_STATE")

    phase = payload.get("failure_phase")
    classification = payload.get("dispatch_classification")
    phase_classes = {
        "reservation": {"PROVED_NO_DISPATCH"},
        "pre-dispatch": {"PROVED_NO_DISPATCH"},
        "provider-execution": {"DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN"},
        "observation-validation": {"OBSERVED"},
        "after-observation-validation": {"OBSERVED"},
        "settlement": {"OBSERVED"},
        "after-settlement": {"OBSERVED"},
        "completion-publication": {"OBSERVED"},
        "after-completion": {"OBSERVED"},
        "finalizer-publication": {"OBSERVED"},
    }
    if phase not in phase_classes or classification not in phase_classes[phase]:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PHASE_CLASSIFICATION")
    expected_failure_class = "post-observation-terminal-failure" if classification == "OBSERVED" else "reservation-or-provider-failure"
    if incident.get("failure_class") != expected_failure_class:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_FAILURE_CLASS")
    expected_candidate = (
        "CONSUMED_NO_DISPATCH"
        if lane == "producer" and classification == "PROVED_NO_DISPATCH"
        else "CONSUMED_DISPATCH_UNKNOWN"
        if lane == "producer" and classification in {"DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN"}
        else "CONSUMED_OBSERVED"
    )
    expected_review = None if lane == "producer" else "NO_DISPATCH" if classification == "PROVED_NO_DISPATCH" else "OBSERVED" if classification == "OBSERVED" else "DISPATCH_UNKNOWN"
    expected_dispatch = "PROVED_NOT_DISPATCHED" if classification == "PROVED_NO_DISPATCH" else classification
    if payload.get("candidate_status") != expected_candidate or payload.get("review_status") != expected_review or payload.get("dispatch_status") != expected_dispatch:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PHASE_STATE")

    _validate_failure_claims(root, payload, auth, auth_sha, bindings, lane=lane, attempt_index=attempt_index)
    packet_disclosure = None
    if lane == "producer":
        if payload.get("packet_disclosure") is not None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PRODUCER_PACKET_DISCLOSURE")
    elif payload.get("packet_disclosure") is not None:
        packet_disclosure = _validate_retained_json_ref(
            root,
            payload.get("packet_disclosure"),
            auth["packet_disclosure_path"],
            "resume_packet_disclosure",
        )
        if packet_disclosure.get("schema") != "reviewed-campaign-packet-disclosure-v1" or packet_disclosure.get("candidate_id") != auth["candidate_id"] or packet_disclosure.get("review_batch_id") != auth["cycle_or_review_batch_id"]:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PACKET_DISCLOSURE_BINDING")
    elif classification != "PROVED_NO_DISPATCH":
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PACKET_DISCLOSURE_REQUIRED")

    snapshot = head_snapshot(usage_root)
    reservation, settlement = _validate_failure_usage(usage_root, payload, auth, auth_sha, snapshot, lane=lane)
    results = _validate_failure_results(root, payload, auth, settlement, packet_disclosure, lane=lane)
    if classification != "PROVED_NO_DISPATCH" and (reservation is None or settlement is None):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_TERMINAL_USAGE_REQUIRED")
    if classification == "OBSERVED" and (settlement.get("completed") != 5 or settlement.get("unknown") != 0):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_OBSERVED_SETTLEMENT")
    if classification in {"DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN"} and (settlement.get("unknown") != 5 or snapshot.get("unresolved_usage") is not True):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_UNKNOWN_SETTLEMENT")
    if classification == "PROVED_NO_DISPATCH" and settlement is not None and (settlement.get("not_dispatched") != 5 or settlement.get("unknown") != 0):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_NO_DISPATCH_SETTLEMENT")

    completion_ref = payload.get("completion")
    if phase in {"after-completion", "finalizer-publication"}:
        completion_path = "producer/completion.json" if lane == "producer" else "cold-review/completion.json"
        completion = _validate_retained_json_ref(root, completion_ref, completion_path, "resume_completion")
        expected_completion = {
            "schema": "reviewed-campaign-producer-completion-v1" if lane == "producer" else "reviewed-campaign-cold-review-completion-v1",
            "status": "PRODUCER_STRUCTURAL_COMPLETE" if lane == "producer" else "COLD_REVIEW_COHORT_COMPLETE",
            "candidate_id": auth["candidate_id"],
            "authorization_sha256": auth_sha,
            "reservation_sha256": payload.get("reservation_sha256"),
            "settlement_sha256": payload.get("settlement_sha256"),
            "results": results,
        }
        if any(completion.get(key) != expected for key, expected in expected_completion.items()):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COMPLETION_BINDING")
        batch_field = "cycle_id" if lane == "producer" else "review_batch_id"
        if completion.get(batch_field) != auth["cycle_or_review_batch_id"]:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COMPLETION_BATCH")
    elif completion_ref is not None:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COMPLETION_PHASE")

    expected_resumable = classification == "PROVED_NO_DISPATCH" and not snapshot.get("unresolved_usage")
    if payload.get("resumable_retry") is not expected_resumable or payload.get("usage_unresolved") is not snapshot.get("unresolved_usage"):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RETRY_USAGE_STATE")


def _preflight_terminal_publications(
    root: Path,
    usage_root: Path,
    auth: dict[str, Any],
    auth_sha: str,
    bindings: dict[str, Any],
    *,
    lane: str,
    attempt_index: int,
) -> None:
    incident_relative, finalizer_relative = _terminal_publication_paths(lane, auth, attempt_index)
    incident_path = _contained(root, incident_relative, f"{lane}_incident_preflight", must_exist=False)
    finalizer_path = _contained(root, finalizer_relative, f"{lane}_finalizer_preflight", must_exist=False)
    if not incident_path.exists() and not finalizer_path.exists():
        return
    if not incident_path.exists():
        try:
            finalizer, _raw = _load_canonical_json(finalizer_path, f"{lane}_success_finalizer_preflight")
            _validate_success_finalizer(
                root,
                usage_root,
                finalizer,
                auth,
                auth_sha,
                bindings,
                lane=lane,
                attempt_index=attempt_index,
            )
        except (CampaignError, OSError, ValueError) as exc:
            raise CampaignError(f"TERMINAL_PUBLICATION_PREFLIGHT_FINALIZER_SUBSTITUTION: {exc}") from exc
        raise CampaignError("ATTEMPT_ALREADY_TERMINALIZED_CREATE_ONCE")
    try:
        incident, incident_raw = _load_canonical_json(incident_path, f"{lane}_incident_preflight")
        _require_terminal_common(
            incident,
            auth,
            auth_sha,
            lane=lane,
            attempt_index=attempt_index,
            role="incident",
        )
        payload = incident.get("finalizer_payload")
        if not isinstance(payload, dict) or "incident" in payload:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_INCIDENT_PAYLOAD")
        _require_terminal_common(
            payload,
            auth,
            auth_sha,
            lane=lane,
            attempt_index=attempt_index,
            role="finalizer_payload",
        )
        _validate_failure_resume_payload(
            root,
            usage_root,
            incident,
            payload,
            auth,
            auth_sha,
            bindings,
            lane=lane,
            attempt_index=attempt_index,
        )
        incident_ref = {
            "path": incident_relative,
            "byte_count": len(incident_raw),
            "sha256": hashlib.sha256(incident_raw).hexdigest(),
        }
        expected_finalizer = {**payload, "incident": incident_ref}
        if finalizer_path.exists():
            finalizer, finalizer_raw = _load_canonical_json(finalizer_path, f"{lane}_finalizer_preflight")
            if finalizer != expected_finalizer or finalizer_raw != canonical_bytes(expected_finalizer):
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_FINALIZER_SUBSTITUTION")
        else:
            _publish_or_adopt_exact_json(
                root,
                finalizer_relative,
                expected_finalizer,
                f"{lane}_finalizer_resume",
            )
    except (CampaignError, OSError, ValueError) as exc:
        raise CampaignError(f"TERMINAL_PUBLICATION_PREFLIGHT_INCIDENT_SUBSTITUTION: {exc}") from exc
    raise CampaignError("ATTEMPT_ALREADY_TERMINALIZED")


def _publish_failure_finalizer(
    root: Path,
    usage_root: Path,
    auth: dict[str, Any],
    auth_sha: str,
    *,
    lane: str,
    attempt_index: int,
    claims: dict[str, Any],
    packet_disclosure: dict[str, object] | None,
    dispatch_classification: str,
    candidate_status: str,
    reservation_sha256: str | None,
    settlement_sha256: str | None,
    error: Exception,
    resumable_retry: bool,
    failure_phase: str,
    observed_results: list[dict[str, object]] | None = None,
    completion: dict[str, object] | None = None,
    interrupt_after_incident: bool = False,
) -> dict[str, Any]:
    snapshot = head_snapshot(usage_root)
    finalizer_payload = {
        "schema": "reviewed-campaign-observation-finalizer-v1",
        "lane": lane,
        "attempt_index": attempt_index,
        "candidate_id": auth["candidate_id"],
        "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
        "authorization_sha256": auth_sha,
        "authorization_claim": claims.get("authorization_claim"),
        "candidate_claim": claims.get("candidate_claim"),
        "continuation_claim": claims.get("continuation_claim"),
        "packet_disclosure": packet_disclosure,
        "failure_phase": failure_phase,
        "observed_results": observed_results or [],
        "completion": completion,
        "candidate_status": candidate_status,
        "review_status": "NO_DISPATCH" if lane == "cold-review" and dispatch_classification == "PROVED_NO_DISPATCH" else "OBSERVED" if lane == "cold-review" and dispatch_classification == "OBSERVED" else "DISPATCH_UNKNOWN" if lane == "cold-review" else None,
        "dispatch_status": "PROVED_NOT_DISPATCHED" if dispatch_classification == "PROVED_NO_DISPATCH" else dispatch_classification,
        "dispatch_classification": dispatch_classification,
        "reservation_sha256": reservation_sha256,
        "settlement_sha256": settlement_sha256,
        "resulting_usage_head_sha256": snapshot["head_sha256"],
        "usage_unresolved": snapshot["unresolved_usage"],
        "resumable_retry": resumable_retry,
        "terminal": True,
    }
    incident = {
        "schema": "reviewed-campaign-incident-v1",
        "incident_id": f"{lane}-{auth['cycle_or_review_batch_id']}",
        "lane": lane,
        "attempt_index": attempt_index,
        "candidate_id": auth["candidate_id"],
        "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
        "authorization_sha256": auth_sha,
        "failure_class": (
            "post-observation-terminal-failure"
            if failure_phase in TERMINAL_PHASE_FAULTS or failure_phase in {
                "observation-validation",
                "settlement",
                "completion-publication",
                "finalizer-publication",
            }
            else "reservation-or-provider-failure"
        ),
        "failure_phase": failure_phase,
        "error_type": type(error).__name__,
        "dispatch_classification": dispatch_classification,
        "reservation_sha256": reservation_sha256,
        "settlement_sha256": settlement_sha256,
        "resulting_usage_head_sha256": snapshot["head_sha256"],
        "continuation_authorized": False,
        "retry_policy": "external-owner-issued-one-use-continuation-required",
        "observed_result_count": len(observed_results or []),
        "completion": completion,
        "terminal": True,
        "finalizer_payload": finalizer_payload,
    }
    incident_relative, finalizer_relative = _terminal_publication_paths(lane, auth, attempt_index)
    incident_ref = _publish_or_adopt_exact_json(root, incident_relative, incident, f"{lane}_incident")
    if interrupt_after_incident:
        raise CampaignError("INJECTED_TERMINAL_PUBLICATION_INTERRUPTION")
    finalizer = {**finalizer_payload, "incident": incident_ref}
    _publish_or_adopt_exact_json(root, finalizer_relative, finalizer, f"{lane}_finalizer")
    return finalizer


def _finalize_no_dispatch_failure(
    root: Path,
    usage_root: Path,
    auth: dict[str, Any],
    auth_sha: str,
    *,
    lane: str,
    attempt_index: int,
    claims: dict[str, Any],
    packet_disclosure: dict[str, object] | None,
    reservation: dict[str, Any] | None,
    error: Exception,
    failure_phase: str = "pre-dispatch",
) -> dict[str, Any]:
    terminal = None
    if reservation is None:
        current = head_snapshot(usage_root)
        if len(current["open_reservations"]) == 1:
            open_sha = current["open_reservations"][0]
            transaction_path = usage_root / "transactions" / f"{open_sha}.json"
            try:
                candidate_reservation, raw = _load_canonical_json(transaction_path, "open_reservation")
            except (CampaignError, OSError) as exc:
                raise CampaignError(f"RESERVATION_FAILURE_OPEN_STATE_INVALID: {exc}") from exc
            if hashlib.sha256(raw).hexdigest() == open_sha and candidate_reservation.get("kind") == "reservation" and candidate_reservation.get("candidate_id") == auth["candidate_id"] and candidate_reservation.get("authorization_sha256") == auth_sha and candidate_reservation.get("cycle_or_review_batch_id") == auth["cycle_or_review_batch_id"]:
                reservation = {**candidate_reservation, "transaction_sha256": open_sha}
    reservation_sha = reservation.get("transaction_sha256") if isinstance(reservation, dict) else None
    if reservation_sha is not None:
        current = head_snapshot(usage_root)
        if current["open_reservations"] == [reservation_sha]:
            receipts = _not_dispatched_receipts(reservation)
            terminal = settle(
                usage_root,
                reservation_sha,
                completed=0,
                failed=0,
                cancelled=0,
                not_dispatched=5,
                unknown=0,
                provider_usage_receipts=receipts,
                measured_cost={"unit": "usd", "value": "0"},
                candidate_id=auth["candidate_id"],
                authorization_sha256=auth_sha,
            )
    snapshot = head_snapshot(usage_root)
    resumable = not snapshot["open_reservations"] and not snapshot["unresolved_usage"]
    return _publish_failure_finalizer(
        root,
        usage_root,
        auth,
        auth_sha,
        lane=lane,
        attempt_index=attempt_index,
        claims=claims,
        packet_disclosure=packet_disclosure,
        dispatch_classification="PROVED_NO_DISPATCH",
        candidate_status="CONSUMED_NO_DISPATCH" if lane == "producer" else "CONSUMED_OBSERVED",
        reservation_sha256=reservation_sha,
        settlement_sha256=terminal.get("transaction_sha256") if isinstance(terminal, dict) else None,
        error=error,
        resumable_retry=resumable,
        failure_phase=failure_phase,
    )


def _require_fake_capability(adapter: ProviderAdapter) -> dict[str, object]:
    try:
        capability = adapter.capability()
    except Exception as exc:
        raise CampaignError("PROVIDER_CAPABILITY_UNAVAILABLE") from exc
    if not isinstance(capability, dict) or set(capability) != PROVIDER_CAPABILITY_KEYS:
        raise CampaignError("PROVIDER_CAPABILITY_INVALID")
    exact = {
        "schema": "reviewed-campaign-provider-capability-v1",
        "adapter_kind": "deterministic-fake-no-dispatch",
        "adapter_version": "deterministic-fake-v1",
        "host_application_version": "deterministic-test-host-v1",
        "test_only": True,
        "paid_provider_reachable": False,
        "live_execution_authorized": False,
    }
    if capability != exact:
        if capability.get("paid_provider_reachable") or not capability.get("test_only"):
            raise CampaignError("LIVE_PROVIDER_UNSUPPORTED: no paid provider adapter exists in this lane")
        raise CampaignError("PROVIDER_CAPABILITY_INVALID")
    return capability


def _load_producer_authorization(root: Path, path: Path) -> tuple[dict[str, Any], str]:
    relative = _relative_to_root(root, path, "producer_authorization")
    authorization, raw = _load_canonical_json(_contained(root, relative, "producer_authorization", must_exist=True), "producer_authorization")
    if set(authorization) != PRODUCER_AUTH_KEYS:
        raise CampaignError("PRODUCER_AUTHORIZATION_SHAPE")
    exact = {
        "schema": "reviewed-campaign-cohort-authorization-v1",
        "kind": "producer-cohort",
        "one_use": True,
        "execution_mode": TEST_EXECUTION_MODE,
        "test_only": True,
        "live_execution_authorized": False,
        "model": "gpt-5.5",
        "reasoning_effort": "high",
        "adapter_version": "deterministic-fake-v1",
        "host_application_version": "deterministic-test-host-v1",
        "cohort_size": 5,
        "cohort_protocol": "barrier-five-submit-before-await-v1",
    }
    if any(authorization.get(key) != expected for key, expected in exact.items()):
        raise CampaignError("PRODUCER_AUTHORIZATION_CONTRACT")
    if authorization.get("provider_settings") != PRODUCER_PROVIDER_SETTINGS:
        raise CampaignError("PRODUCER_AUTHORIZATION_PROVIDER_SETTINGS")
    for field in ("authorization_id", "candidate_id", "cycle_or_review_batch_id"):
        if not isinstance(authorization.get(field), str) or not authorization[field]:
            raise CampaignError(f"PRODUCER_AUTHORIZATION_{field.upper()}")
    if not isinstance(authorization.get("campaign_authorization_sha256"), str) or SHA256_RE.fullmatch(authorization["campaign_authorization_sha256"]) is None:
        raise CampaignError("PRODUCER_AUTHORIZATION_CAMPAIGN_HASH")
    if not isinstance(authorization.get("source_commit"), str) or GIT_OID_RE.fullmatch(authorization["source_commit"]) is None:
        raise CampaignError("PRODUCER_AUTHORIZATION_SOURCE_COMMIT")
    return authorization, hashlib.sha256(raw).hexdigest()


def retry_continuation_authorization_id(value: dict[str, Any]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "authorization_id"}
    return hashlib.sha256(b"daee-reviewed-campaign-retry-continuation-v1\0" + canonical_bytes(unsigned)).hexdigest()


def validate_retry_lineage(
    root: Path,
    value: object,
    *,
    current_auth: dict[str, Any] | None = None,
    lane: str | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"attempt_index", "continuation_authorization"}:
        raise CampaignError("RETRY_LINEAGE_SHAPE")
    attempt = value.get("attempt_index")
    continuation = value.get("continuation_authorization")
    if isinstance(attempt, int) and not isinstance(attempt, bool) and attempt == 1 and continuation is None:
        return {"attempt_index": 1, "continuation": None, "continuation_sha256": None}
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 2:
        raise CampaignError("RETRY_LINEAGE_INDEX")
    if not isinstance(continuation, dict):
        raise CampaignError("RETRY_LINEAGE_CONTINUATION_AUTHORIZATION_REQUIRED")
    if not isinstance(current_auth, dict) or lane not in {"producer", "cold-review"}:
        raise CampaignError("RETRY_CONTINUATION_CURRENT_ATTEMPT_REQUIRED")
    try:
        authorization, path, authorization_sha = _load_ref(root, continuation, "retry_continuation_authorization")
        canonical, raw = _load_canonical_json(path, "retry_continuation_authorization")
    except CampaignError as exc:
        raise CampaignError(f"RETRY_CONTINUATION_AUTHORIZATION_INVALID: {exc}") from exc
    if canonical != authorization or hashlib.sha256(raw).hexdigest() != authorization_sha:
        raise CampaignError("RETRY_CONTINUATION_AUTHORIZATION_CONTENT_ADDRESS")
    required = {
        "schema", "kind", "authorization_id", "issuer_identity", "implementation_owner_identity",
        "candidate_id", "lane", "prior_batch_id", "prior_attempt_index", "next_batch_id",
        "next_attempt_index", "prior_cohort_authorization", "prior_cohort_authorization_sha256", "prior_incident",
        "prior_finalizer", "expected_usage_head_sha256", "claim_path", "one_use",
    }
    if set(authorization) != required or authorization.get("schema") != "reviewed-campaign-retry-continuation-authorization-v1" or authorization.get("kind") != "retry-continuation" or authorization.get("one_use") is not True:
        raise CampaignError("RETRY_CONTINUATION_AUTHORIZATION_SHAPE")
    if authorization.get("authorization_id") != retry_continuation_authorization_id(authorization):
        raise CampaignError("RETRY_CONTINUATION_AUTHORIZATION_ID")
    expected_owner_path = f"authorizations/retry-continuations/owner-issued/{lane}-{current_auth['cycle_or_review_batch_id']}-attempt-{attempt:02d}.authorization.json"
    if path.relative_to(root).as_posix() != expected_owner_path:
        raise CampaignError("RETRY_CONTINUATION_OWNER_ISSUED_LOCATOR")
    for field in ("issuer_identity", "implementation_owner_identity"):
        if not isinstance(authorization.get(field), str) or TASK_IDENTITY_RE.fullmatch(authorization[field]) is None:
            raise CampaignError(f"RETRY_CONTINUATION_{field.upper()}_IDENTITY")
    if authorization["issuer_identity"] != CONTINUATION_ISSUER or authorization["implementation_owner_identity"] != TASK6_IMPLEMENTATION_OWNER:
        raise CampaignError("RETRY_CONTINUATION_OWNER_AUTHORITY")
    if authorization.get("candidate_id") != current_auth.get("candidate_id") or authorization.get("lane") != lane:
        raise CampaignError("RETRY_CONTINUATION_CANDIDATE_LANE_BINDING")
    if authorization.get("next_batch_id") != current_auth.get("cycle_or_review_batch_id") or authorization.get("next_attempt_index") != attempt:
        raise CampaignError("RETRY_CONTINUATION_SUCCESSOR_BINDING")
    if authorization.get("prior_attempt_index") != attempt - 1 or not isinstance(authorization.get("prior_batch_id"), str) or not authorization["prior_batch_id"] or authorization["prior_batch_id"] == authorization["next_batch_id"]:
        raise CampaignError("RETRY_CONTINUATION_PREDECESSOR_ORDER")
    prior_auth_sha = authorization.get("prior_cohort_authorization_sha256")
    expected_head_sha = authorization.get("expected_usage_head_sha256")
    if not isinstance(prior_auth_sha, str) or SHA256_RE.fullmatch(prior_auth_sha) is None or not isinstance(expected_head_sha, str) or SHA256_RE.fullmatch(expected_head_sha) is None:
        raise CampaignError("RETRY_CONTINUATION_HASH_BINDING")
    try:
        prior_authorization, prior_authorization_path, observed_prior_auth_sha = _load_ref(root, authorization.get("prior_cohort_authorization"), "retry_prior_cohort_authorization")
        incident, _incident_path, incident_sha = _load_ref(root, authorization.get("prior_incident"), "retry_prior_incident")
        finalizer, _finalizer_path, finalizer_sha = _load_ref(root, authorization.get("prior_finalizer"), "retry_prior_finalizer")
    except CampaignError as exc:
        raise CampaignError(f"RETRY_CONTINUATION_PREDECESSOR_ARTIFACT: {exc}") from exc
    if observed_prior_auth_sha != prior_auth_sha:
        raise CampaignError("RETRY_CONTINUATION_PRIOR_AUTHORIZATION_HASH")
    prior_kind = "producer-cohort" if lane == "producer" else "cold-review-cohort"
    prior_retry = prior_authorization.get("retry_lineage") if isinstance(prior_authorization, dict) else None
    if prior_authorization.get("schema") != "reviewed-campaign-cohort-authorization-v1" or prior_authorization.get("kind") != prior_kind or prior_authorization.get("candidate_id") != current_auth["candidate_id"] or prior_authorization.get("cycle_or_review_batch_id") != authorization["prior_batch_id"] or not isinstance(prior_retry, dict) or prior_retry.get("attempt_index") != authorization["prior_attempt_index"]:
        raise CampaignError("RETRY_CONTINUATION_PRIOR_AUTHORIZATION_BINDING")
    if hashlib.sha256(prior_authorization_path.read_bytes()).hexdigest() != prior_auth_sha:
        raise CampaignError("RETRY_CONTINUATION_PRIOR_AUTHORIZATION_CONTENT_ADDRESS")
    expected_incident_path = f"incidents/{lane}-{authorization['prior_batch_id']}.json"
    expected_finalizer_path = _attempt_finalizer_path(lane, authorization["prior_attempt_index"])
    if authorization["prior_incident"].get("path") != expected_incident_path or authorization["prior_finalizer"].get("path") != expected_finalizer_path:
        raise CampaignError("RETRY_CONTINUATION_PREDECESSOR_LOCATOR")
    common = {
        "candidate_id": current_auth["candidate_id"],
        "lane": lane,
        "cycle_or_review_batch_id": authorization["prior_batch_id"],
        "attempt_index": authorization["prior_attempt_index"],
        "authorization_sha256": prior_auth_sha,
    }
    if incident.get("schema") != "reviewed-campaign-incident-v1" or any(incident.get(key) != expected for key, expected in common.items()):
        raise CampaignError("RETRY_CONTINUATION_INCIDENT_BINDING")
    if finalizer.get("schema") != "reviewed-campaign-observation-finalizer-v1" or any(finalizer.get(key) != expected for key, expected in common.items()):
        raise CampaignError("RETRY_CONTINUATION_FINALIZER_BINDING")
    if finalizer.get("incident", {}).get("sha256") != incident_sha or finalizer.get("dispatch_classification") != "PROVED_NO_DISPATCH" or finalizer.get("resumable_retry") is not True or finalizer.get("resulting_usage_head_sha256") != expected_head_sha:
        raise CampaignError("RETRY_CONTINUATION_FINALIZER_NOT_RESUMABLE")
    expected_claim_path = f"claims/retry-continuations/{lane}-{current_auth['cycle_or_review_batch_id']}-attempt-{attempt:02d}.claim.json"
    if authorization.get("claim_path") != expected_claim_path:
        raise CampaignError("RETRY_CONTINUATION_CLAIM_PATH")
    claim = _contained(root, expected_claim_path, "retry_continuation_claim", must_exist=False)
    if claim.exists():
        raise CampaignError("RETRY_CONTINUATION_REPLAY")
    usage_root = _contained(root, current_auth.get("usage_ledger_root"), "retry_usage_ledger_root", must_exist=False)
    try:
        live_head_sha = head_snapshot(usage_root)["head_sha256"]
    except (ValueError, OSError) as exc:
        raise CampaignError(f"RETRY_CONTINUATION_LATEST_HEAD_INVALID: {exc}") from exc
    if live_head_sha != expected_head_sha:
        raise CampaignError("RETRY_CONTINUATION_STALE_HEAD")
    return {
        "attempt_index": attempt,
        "continuation": authorization,
        "continuation_sha256": authorization_sha,
        "incident_sha256": incident_sha,
        "finalizer_sha256": finalizer_sha,
    }


def extract_mature_candidate_identity(candidate: object) -> dict[str, Any]:
    """Extract the exact dispatch bindings from a Task5 mature-candidate verdict."""
    if not isinstance(candidate, dict) or candidate.get("schema") != "daee-no-model-candidate-maturity-v1" or candidate.get("kind") != "candidate-maturity" or candidate.get("status") != "NO_MODEL_CANDIDATE_MATURE":
        raise CampaignError("CANDIDATE_MATURITY_SHAPE")
    source = candidate.get("source")
    identity = candidate.get("candidate")
    registries = candidate.get("registries")
    if not isinstance(source, dict) or not isinstance(identity, dict) or not isinstance(registries, dict):
        raise CampaignError("CANDIDATE_MATURITY_SHAPE")
    candidate_id = identity.get("candidate_id")
    source_commit = source.get("commit_sha")
    if not isinstance(candidate_id, str) or not candidate_id or not isinstance(source_commit, str) or GIT_OID_RE.fullmatch(source_commit) is None:
        raise CampaignError("CANDIDATE_MATURITY_IDENTITY")
    if identity.get("status") != "READY_UNUSED" or identity.get("claim_status") != "UNCLAIMED":
        raise CampaignError("CANDIDATE_ALREADY_CONSUMED")
    refs = {
        "package_record": identity.get("candidate_record"),
        "source_preflight": candidate.get("source_preflight"),
        "registry": registries.get("input"),
        "review_protocol": registries.get("review_protocol"),
    }
    for role, ref in refs.items():
        if not isinstance(ref, dict) or set(ref) != {"path", "byte_count", "sha256"}:
            raise CampaignError(f"CANDIDATE_MATURITY_{role.upper()}_REF")
    package_tree_sha256 = identity.get("package_tree_sha256")
    if not isinstance(package_tree_sha256, str) or SHA256_RE.fullmatch(package_tree_sha256) is None:
        raise CampaignError("CANDIDATE_MATURITY_PACKAGE_TREE")
    return {
        "candidate_id": candidate_id,
        "source_commit": source_commit,
        "package_tree_sha256": package_tree_sha256,
        **refs,
    }


def _validate_common_bindings(root: Path, auth: dict[str, Any], *, allow_test_fixture: bool) -> dict[str, Any]:
    candidate, _candidate_path, candidate_sha = _load_ref(root, auth["candidate_maturity"], "candidate_maturity")
    package, _package_path, package_sha = _load_ref(root, auth["package_record"], "package_record")
    preflight, _preflight_path, preflight_sha = _load_ref(root, auth["source_preflight"], "source_preflight")
    registry, _registry_path, registry_sha = _load_ref(root, auth["registry"], "registry")
    protocol, _protocol_path, protocol_sha = _load_ref(root, auth["review_protocol"], "review_protocol")
    if not allow_test_fixture:
        try:
            from check_no_model_candidate_maturity import validate_candidate_maturity
        except Exception as exc:
            raise CampaignError("CANDIDATE_MATURITY_CHECKER_UNAVAILABLE") from exc
        findings = validate_candidate_maturity(candidate, root=root)
        if findings:
            raise CampaignError(f"CANDIDATE_MATURITY_INVALID: {findings[0].failure_class}/{findings[0].failure_subcode}")
        mature = extract_mature_candidate_identity(candidate)
        if mature["candidate_id"] != auth["candidate_id"] or mature["source_commit"] != auth["source_commit"]:
            raise CampaignError("CANDIDATE_AUTHORIZATION_BINDING")
        for role in ("package_record", "source_preflight", "registry", "review_protocol"):
            if auth[role] != mature[role]:
                raise CampaignError(f"CANDIDATE_{role.upper()}_BINDING")
        if preflight.get("schema") != "daee-no-model-candidate-maturity-v1" or preflight.get("kind") != "source-preflight" or preflight.get("status") != "NO_MODEL_SOURCE_PREFLIGHT_GREEN":
            raise CampaignError("SOURCE_PREFLIGHT_INVALID")
    else:
        test_candidate = {
            "schema": "reviewed-campaign-test-candidate-maturity-v1",
            "kind": "candidate-maturity",
            "status": "NO_MODEL_CANDIDATE_MATURE",
            "candidate_state": "READY_UNUSED",
            "claim_status": "UNCLAIMED",
            "model_execution_authorized": False,
            "test_fixture_only": True,
        }
        if any(candidate.get(key) != expected for key, expected in test_candidate.items()):
            raise CampaignError("CANDIDATE_MATURITY_TEST_FIXTURE_INVALID")
        test_preflight = {
            "schema": "reviewed-campaign-test-preflight-v1",
            "kind": "source-preflight",
            "status": "NO_MODEL_SOURCE_PREFLIGHT_GREEN",
            "model_execution_authorized": False,
            "test_fixture_only": True,
        }
        if any(preflight.get(key) != expected for key, expected in test_preflight.items()):
            raise CampaignError("SOURCE_PREFLIGHT_TEST_FIXTURE_INVALID")
    case_ids = auth.get("case_ids")
    if not isinstance(case_ids, list) or len(case_ids) != 5 or len(set(case_ids)) != 5 or case_ids != protocol.get("case_ids"):
        raise CampaignError("CANONICAL_CASE_SET_BINDING")
    producer = protocol.get("producer")
    if not isinstance(producer, dict) or producer.get("cohort_size") != 5 or producer.get("model") != "gpt-5.5" or producer.get("reasoning_effort") != "high" or producer.get("protocol") != "barrier-five-submit-before-await-v1" or producer.get("paid_execution_authorized") is not False:
        raise CampaignError("REVIEW_PROTOCOL_PRODUCER_CONTRACT")
    if protocol.get("input_registry", {}).get("sha256") != registry_sha:
        raise CampaignError("REGISTRY_PROTOCOL_BINDING")
    if allow_test_fixture:
        shared = {"candidate_id": auth["candidate_id"], "source_commit": auth["source_commit"], "registry_sha256": registry_sha}
        if any(candidate.get(key) != expected for key, expected in shared.items()):
            raise CampaignError("CANDIDATE_AUTHORIZATION_BINDING")
        if candidate.get("package_record_sha256") != package_sha or candidate.get("source_preflight_sha256") != preflight_sha or candidate.get("review_protocol_sha256") != protocol_sha:
            raise CampaignError("CANDIDATE_EVIDENCE_BINDING")
        for record, role in ((package, "PACKAGE"), (preflight, "PREFLIGHT")):
            if record.get("source_commit") != auth["source_commit"] or record.get("registry_sha256") != registry_sha:
                raise CampaignError(f"{role}_AUTHORIZATION_BINDING")
        if package.get("candidate_id") != auth["candidate_id"] or package.get("package_sha256") != candidate.get("package_sha256") or package.get("package_tree_sha256") != candidate.get("package_tree_sha256"):
            raise CampaignError("PACKAGE_CANDIDATE_BINDING")
        if preflight.get("review_protocol_sha256") != protocol_sha:
            raise CampaignError("PREFLIGHT_PROTOCOL_BINDING")
    lane = "producer" if auth.get("kind") == "producer-cohort" else "cold-review" if auth.get("kind") == "cold-review-cohort" else None
    retry = validate_retry_lineage(root, auth["retry_lineage"], current_auth=auth, lane=lane)
    return {
        "candidate": candidate,
        "candidate_sha256": candidate_sha,
        "package": package,
        "package_sha256": package_sha,
        "preflight": preflight,
        "preflight_sha256": preflight_sha,
        "registry": registry,
        "registry_sha256": registry_sha,
        "protocol": protocol,
        "protocol_sha256": protocol_sha,
        "retry": retry,
    }


def _worker_inventory(auth: dict[str, Any], lane: str) -> list[dict[str, str]]:
    prefix = auth.get("isolated_root_prefix")
    parts = _portable_relative_parts(prefix, f"{lane}_isolated_root_prefix")
    prefix = "/".join(parts)
    rows = []
    for index, case_id in enumerate(auth["case_ids"], 1):
        worker = f"{lane}-{index:02d}"
        base = f"{prefix}/{worker}"
        rows.append({"worker": worker, "case_id": case_id, "home": f"{base}/home", "cache": f"{base}/cache", "run_root": f"{base}/run"})
    return rows


def _execution_custody(
    auth: dict[str, Any],
    auth_sha: str,
    worker: dict[str, str],
    call_contract: dict[str, Any],
    *,
    lane: str,
    packet: dict[str, Any] | None,
) -> dict[str, Any]:
    packet_custody = None
    if lane == "cold-review":
        if not isinstance(packet, dict):
            raise CampaignError("EXECUTION_CUSTODY_PACKET_REQUIRED")
        packet_custody = {
            "packet_root": packet["packet_root"],
            "manifest": packet["manifest"],
            "payload": packet["payload"],
            "packet_id": packet["packet_id"],
            "input_sha256": packet["input_sha256"],
            "output_sha256": packet["output_sha256"],
        }
    envelope = {
        "schema": "reviewed-campaign-execution-custody-v1",
        "lane": lane,
        "candidate_id": auth["candidate_id"],
        "source_commit": auth["source_commit"],
        "candidate_maturity": auth["candidate_maturity"],
        "package_record": auth["package_record"],
        "source_preflight": auth["source_preflight"],
        "registry": auth["registry"],
        "review_protocol": auth["review_protocol"],
        "authorization_sha256": auth_sha,
        "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
        "case_id": worker["case_id"],
        "subject_id": call_contract["subject_id"],
        "model": call_contract["model"],
        "reasoning_effort": call_contract["reasoning_effort"],
        "provider_settings": auth["provider_settings"],
        "isolated_worker_root": {key: worker[key] for key in ("worker", "home", "cache", "run_root")},
        "packet": packet_custody,
    }
    if lane == "producer" and packet_custody is not None:
        raise CampaignError("EXECUTION_CUSTODY_PRODUCER_PACKET_FORBIDDEN")
    return envelope


def _submit_with_custody(adapter: ProviderAdapter, envelope: dict[str, Any]) -> str:
    expected_sha = record_sha256(envelope)
    acknowledgment = adapter.submit(envelope)
    required = {"handle_id", "execution_custody_sha256", "accepted", "in_flight"}
    if not isinstance(acknowledgment, dict) or set(acknowledgment) != required:
        raise CampaignError("EXECUTION_CUSTODY_SUBMIT_ACK_SHAPE")
    if acknowledgment.get("execution_custody_sha256") != expected_sha:
        raise CampaignError("EXECUTION_CUSTODY_SUBMIT_ACK_BINDING")
    if acknowledgment.get("accepted") is not True or acknowledgment.get("in_flight") is not True:
        raise CampaignError("EXECUTION_CUSTODY_SUBMIT_ACK_STATE")
    handle = acknowledgment.get("handle_id")
    if not isinstance(handle, str) or not handle:
        raise CampaignError("EXECUTION_CUSTODY_SUBMIT_HANDLE")
    return handle


def _provider_receipt(reservation: dict[str, Any], index: int, result: dict[str, object], execution_custody_sha256: str) -> dict[str, object]:
    contract = reservation["call_contract"][index - 1]
    required_result = {"content_utf8", "structural_status", "provider_call_id", "execution_custody_sha256", "usage", "cost"}
    if not isinstance(result, dict) or "execution_custody_sha256" not in result:
        raise CampaignError("EXECUTION_CUSTODY_OBSERVE_SHAPE")
    if set(result) != required_result or result.get("structural_status") != "PASS" or not isinstance(result.get("content_utf8"), str):
        raise CampaignError("PRODUCER_STRUCTURAL_RESULT_INVALID")
    if result.get("execution_custody_sha256") != execution_custody_sha256:
        raise CampaignError("EXECUTION_CUSTODY_OBSERVE_BINDING")
    provider_id = result.get("provider_call_id")
    if not isinstance(provider_id, str) or not provider_id:
        raise CampaignError("PROVIDER_RECEIPT_IDENTITY")
    return {
        "call_id": f"{reservation['cycle_or_review_batch_id']}:call-{index:02d}",
        **contract,
        "cycle_or_review_batch_id": reservation["cycle_or_review_batch_id"],
        "started_at": "2026-07-12T00:00:00Z",
        "ended_at": "2026-07-12T00:00:01Z",
        "host_invocation_id": f"task6-{reservation['cycle_or_review_batch_id']}-{index:02d}",
        "accepted": True,
        "in_flight": True,
        "status": "COMPLETED",
        "unknown_kind": None,
        "acknowledgment_origin": "BOTH",
        "terminal_transport_status": "COMPLETED",
        "provider_call_id": provider_id,
        "usage": result["usage"],
        "cost": result["cost"],
    }


def _not_dispatched_receipts(reservation: dict[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, contract in enumerate(reservation["call_contract"], 1):
        rows.append(
            {
                "call_id": f"{reservation['cycle_or_review_batch_id']}:call-{index:02d}",
                **contract,
                "cycle_or_review_batch_id": reservation["cycle_or_review_batch_id"],
                "started_at": None,
                "ended_at": None,
                "host_invocation_id": None,
                "accepted": False,
                "in_flight": False,
                "status": "NOT_DISPATCHED",
                "unknown_kind": None,
                "acknowledgment_origin": "NONE",
                "terminal_transport_status": "NOT_STARTED",
                "provider_call_id": None,
                "usage": {"status": "UNAVAILABLE"},
                "cost": {"unit": "usd", "value": "0"},
            }
        )
    return rows


def _unknown_receipts(reservation: dict[str, Any], *, positive_dispatch_evidence: bool, handles: list[str] | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    exact_handles = handles if positive_dispatch_evidence and isinstance(handles, list) and len(handles) == 5 else [None] * 5
    for index, (contract, handle) in enumerate(zip(reservation["call_contract"], exact_handles), 1):
        rows.append(
            {
                "call_id": f"{reservation['cycle_or_review_batch_id']}:call-{index:02d}",
                **contract,
                "cycle_or_review_batch_id": reservation["cycle_or_review_batch_id"],
                "started_at": "2026-07-12T00:00:00Z" if positive_dispatch_evidence else None,
                "ended_at": None,
                "host_invocation_id": f"task6-unknown-{reservation['cycle_or_review_batch_id']}-{index:02d}" if positive_dispatch_evidence else None,
                "accepted": True if positive_dispatch_evidence else None,
                "in_flight": True if positive_dispatch_evidence else None,
                "status": "UNKNOWN",
                "unknown_kind": "OUTCOME_UNKNOWN" if positive_dispatch_evidence else "DISPATCH_UNKNOWN",
                "acknowledgment_origin": "BOTH" if positive_dispatch_evidence else "NONE",
                "terminal_transport_status": "IN_FLIGHT" if positive_dispatch_evidence else "UNKNOWN",
                "provider_call_id": handle,
                "usage": {"status": "UNAVAILABLE"},
                "cost": {"unit": "usd", "value": "unknown"},
            }
        )
    return rows


def _finalize_provider_failure(
    root: Path,
    usage_root: Path,
    reservation: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    *,
    handles: list[str],
    lane: str,
    error: Exception,
    attempt_index: int,
    claims: dict[str, Any],
    packet_disclosure: dict[str, object] | None,
    failure_phase: str = "provider-execution",
    observed_results: list[dict[str, object]] | None = None,
) -> None:
    positive = len(handles) == 5
    receipts = _unknown_receipts(reservation, positive_dispatch_evidence=positive, handles=handles)
    terminal = settle(
        usage_root,
        reservation["transaction_sha256"],
        completed=0,
        failed=0,
        cancelled=0,
        not_dispatched=0,
        unknown=5,
        provider_usage_receipts=receipts,
        measured_cost={"unit": "usd", "value": "unknown"},
        candidate_id=auth["candidate_id"],
        authorization_sha256=auth_sha,
    )
    _publish_failure_finalizer(
        root,
        usage_root,
        auth,
        auth_sha,
        lane=lane,
        attempt_index=attempt_index,
        claims=claims,
        packet_disclosure=packet_disclosure,
        dispatch_classification="OUTCOME_UNKNOWN" if positive else "DISPATCH_UNKNOWN",
        candidate_status="CONSUMED_DISPATCH_UNKNOWN" if lane == "producer" else "CONSUMED_OBSERVED",
        reservation_sha256=reservation["transaction_sha256"],
        settlement_sha256=terminal["transaction_sha256"],
        error=error,
        resumable_retry=False,
        failure_phase=failure_phase,
        observed_results=observed_results,
    )


def _finalize_observed_failure(
    root: Path,
    usage_root: Path,
    reservation: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    *,
    lane: str,
    error: Exception,
    failure_phase: str,
    attempt_index: int,
    claims: dict[str, Any],
    packet_disclosure: dict[str, object] | None,
    receipts: list[dict[str, object]],
    observed_results: list[dict[str, object]],
    completion: dict[str, object] | None,
    interrupt_after_incident: bool = False,
) -> None:
    if len(receipts) != 5 or len(observed_results) != 5:
        raise CampaignError("OBSERVED_FAILURE_REQUIRES_EXACT_FIVE_RESULTS")
    reservation_sha = reservation["transaction_sha256"]
    snapshot = head_snapshot(usage_root)
    terminal: dict[str, Any]
    if snapshot["open_reservations"] == [reservation_sha]:
        terminal = settle(
            usage_root,
            reservation_sha,
            completed=5,
            failed=0,
            cancelled=0,
            not_dispatched=0,
            unknown=0,
            provider_usage_receipts=receipts,
            measured_cost={"unit": "usd", "value": "0"},
            candidate_id=auth["candidate_id"],
            authorization_sha256=auth_sha,
        )
    elif not snapshot["open_reservations"]:
        terminal_sha = snapshot.get("last_transaction_sha256")
        if not isinstance(terminal_sha, str):
            raise CampaignError("OBSERVED_FAILURE_TERMINAL_MISSING")
        terminal_path = usage_root / "transactions" / f"{terminal_sha}.json"
        terminal, _raw = _load_canonical_json(terminal_path, "observed_failure_terminal")
        if terminal.get("kind") != "settlement" or terminal.get("reservation_transaction_sha256") != reservation_sha:
            raise CampaignError("OBSERVED_FAILURE_TERMINAL_BINDING")
        terminal = {**terminal, "transaction_sha256": terminal_sha}
    else:
        raise CampaignError("OBSERVED_FAILURE_OPEN_RESERVATION_DRIFT")
    _publish_failure_finalizer(
        root,
        usage_root,
        auth,
        auth_sha,
        lane=lane,
        attempt_index=attempt_index,
        claims=claims,
        packet_disclosure=packet_disclosure,
        dispatch_classification="OBSERVED",
        candidate_status="CONSUMED_OBSERVED",
        reservation_sha256=reservation_sha,
        settlement_sha256=terminal["transaction_sha256"],
        error=error,
        resumable_retry=False,
        failure_phase=failure_phase,
        observed_results=observed_results,
        completion=completion,
        interrupt_after_incident=interrupt_after_incident,
    )


TERMINAL_PHASE_FAULTS = {
    "after-observation-validation",
    "after-settlement",
    "after-completion",
    "after-incident-publication",
}


def _validate_fault_injection(fault_at: str | None, allow_test_fixture: bool) -> None:
    allowed_faults = {
        None,
        "after-claims-before-reservation",
        "after-reservation-before-submit",
        "reservation-exception-after-open",
        *TERMINAL_PHASE_FAULTS,
    }
    if fault_at not in allowed_faults or (fault_at is not None and not allow_test_fixture):
        raise CampaignError("UNSUPPORTED_FAULT_INJECTION")


def run_producer_cohort(
    custody_root: Path,
    authorization_path: Path,
    adapter: ProviderAdapter,
    *,
    allow_test_fixture: bool = False,
    fault_at: str | None = None,
) -> dict[str, Any]:
    """Run one fake-only producer cohort after every exact preflight gate."""
    root = Path(os.path.abspath(custody_root))
    _require_fake_capability(adapter)  # Must precede authorization reads/claims.
    _validate_fault_injection(fault_at, allow_test_fixture)
    auth, auth_sha = _load_producer_authorization(root, authorization_path)
    bindings = _validate_common_bindings(root, auth, allow_test_fixture=allow_test_fixture)
    _contained(
        root,
        auth.get("isolated_root_prefix"),
        "producer_isolated_root_prefix",
        must_exist=False,
    )
    attempt_index = bindings["retry"]["attempt_index"]
    auth_claim = {
        "schema": "reviewed-campaign-authorization-claim-v1",
        "kind": "producer-cohort",
        "authorization_sha256": auth_sha,
        "candidate_id": auth["candidate_id"],
        "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
        "execution_mode": TEST_EXECUTION_MODE,
        "live_dispatch": False,
    }
    usage_root = _contained(root, auth["usage_ledger_root"], "usage_ledger_root", must_exist=False)
    _preflight_terminal_publications(
        root,
        usage_root,
        auth,
        auth_sha,
        bindings,
        lane="producer",
        attempt_index=attempt_index,
    )
    claims = _consume_attempt_claims(root, auth, auth_sha, bindings, lane="producer", authorization_claim=auth_claim)
    if fault_at == "after-claims-before-reservation":
        error = CampaignError("INJECTED_RESERVATION_FAILURE_AFTER_CLAIMS")
        _finalize_no_dispatch_failure(
            root,
            usage_root,
            auth,
            auth_sha,
            lane="producer",
            attempt_index=attempt_index,
            claims=claims,
            packet_disclosure=None,
            reservation=None,
            error=error,
        )
        raise error
    subjects = [f"producer:{case_id}" for case_id in auth["case_ids"]]
    reservation: dict[str, Any] | None = None
    handles: list[str] = []
    results: list[dict[str, object]] = []
    receipts: list[dict[str, object]] = []
    completion_ref: dict[str, object] | None = None
    failure_phase = "reservation"
    try:
        snapshot = head_snapshot(usage_root)
        reservation = reserve(
            usage_root,
            cohort="gpt-producer",
            calls=5,
            expected_sequence=snapshot["sequence"],
            expected_head_sha256=snapshot["head_sha256"],
            campaign_authorization_sha256=auth["campaign_authorization_sha256"],
            authorization_sha256=auth_sha,
            candidate_id=auth["candidate_id"],
            cycle_or_review_batch_id=auth["cycle_or_review_batch_id"],
            call_subject_ids=subjects,
        )
        if fault_at == "reservation-exception-after-open":
            raise CampaignError("INJECTED_RESERVATION_EXCEPTION_AFTER_OPEN")
        failure_phase = "pre-dispatch"
        if fault_at == "after-reservation-before-submit":
            raise CampaignError("INJECTED_PRE_DISPATCH_FAILURE")
        workers = _worker_inventory(auth, "producer")
        envelopes = [
            _execution_custody(auth, auth_sha, worker, contract, lane="producer", packet=None)
            for worker, contract in zip(workers, reservation["call_contract"])
        ]
        raw_events: list[dict[str, object]] = [
            *({"event": "worker_ready", "worker": row["worker"], "case_id": row["case_id"]} for row in workers),
            {"event": "barrier_release"},
        ]
        failure_phase = "provider-execution"
        for worker, envelope in zip(workers, envelopes):
            raw_events.append({"event": "request_submit_started", "worker": worker["worker"], "case_id": worker["case_id"]})
            handles.append(_submit_with_custody(adapter, envelope))
            raw_events.append({"event": "call_entered_in_flight", "worker": worker["worker"], "case_id": worker["case_id"]})
        raw_events.append({"event": "all_five_in_flight"})
        for index, (worker, envelope, handle) in enumerate(zip(workers, envelopes, handles), 1):
            result = adapter.observe(handle, envelope)
            receipt = _provider_receipt(reservation, index, result, record_sha256(envelope))
            content = str(result["content_utf8"]).encode("utf-8")
            output_ref = _publish_once_bytes(root, f"producer/results/{worker['case_id']}.txt", content, f"producer_result_{index}")
            results.append({"case_id": worker["case_id"], "structural_status": "PASS", "output": output_ref, "provider_receipt_sha256": record_sha256(receipt)})
            receipts.append(receipt)
            raw_events.append({"event": "terminal_result_observed", "worker": worker["worker"], "case_id": worker["case_id"]})
        failure_phase = "observation-validation"
        manifest = {
            "schema": "daee-smoke-matrix-v1",
            "kind": "dispatch-manifest",
            "protocol": "barrier-five-submit-before-await-v1",
            "expected_workers": 5,
            "workers": workers,
            "events": chain_dispatch_events(raw_events),
        }
        issues = validate_dispatch_manifest(manifest, 5)
        if issues:
            raise CampaignError(f"DISPATCH_BARRIER_INVALID: {issues[0]['failure_class']}")
        if fault_at in {"after-observation-validation", "after-incident-publication"}:
            failure_phase = "after-observation-validation"
            raise CampaignError(f"INJECTED_TERMINAL_PHASE_FAILURE: {fault_at}")
        failure_phase = "settlement"
        settlement = settle(
            usage_root,
            reservation["transaction_sha256"],
            completed=5,
            failed=0,
            cancelled=0,
            not_dispatched=0,
            unknown=0,
            provider_usage_receipts=receipts,
            measured_cost={"unit": "usd", "value": "0"},
            candidate_id=auth["candidate_id"],
            authorization_sha256=auth_sha,
        )
        if fault_at == "after-settlement":
            failure_phase = fault_at
            raise CampaignError(f"INJECTED_TERMINAL_PHASE_FAILURE: {fault_at}")
        completion: dict[str, Any] = {
            "schema": "reviewed-campaign-producer-completion-v1",
            "status": "PRODUCER_STRUCTURAL_COMPLETE",
            "candidate_id": auth["candidate_id"],
            "cycle_id": auth["cycle_or_review_batch_id"],
            "source_commit": auth["source_commit"],
            "registry_sha256": bindings["registry_sha256"],
            "review_protocol_sha256": bindings["protocol_sha256"],
            "package_record_sha256": bindings["package_sha256"],
            "candidate_maturity_sha256": bindings["candidate_sha256"],
            "authorization_sha256": auth_sha,
            "reservation_sha256": reservation["transaction_sha256"],
            "settlement_sha256": settlement["transaction_sha256"],
            "dispatch_manifest": manifest,
            "results": results,
            "cold_review_authorized": False,
        }
        failure_phase = "completion-publication"
        completion_ref = _publish_once_json(root, "producer/completion.json", completion, "producer_completion")
        if fault_at == "after-completion":
            failure_phase = fault_at
            raise CampaignError(f"INJECTED_TERMINAL_PHASE_FAILURE: {fault_at}")
        failure_phase = "finalizer-publication"
        _publish_once_json(
            root,
            _attempt_finalizer_path("producer", attempt_index),
            {
                "schema": "reviewed-campaign-observation-finalizer-v1",
                "lane": "producer",
                "attempt_index": attempt_index,
                "candidate_id": auth["candidate_id"],
                "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
                "authorization_sha256": auth_sha,
                "authorization_claim": claims.get("authorization_claim"),
                "candidate_claim": claims.get("candidate_claim"),
                "continuation_claim": claims.get("continuation_claim"),
                "candidate_status": "CONSUMED_OBSERVED",
                "dispatch_status": "DETERMINISTIC_FAKE_COMPLETE",
                "reservation_sha256": reservation["transaction_sha256"],
                "settlement_sha256": settlement["transaction_sha256"],
                "observed_results": results,
                "completion": completion_ref,
                "resulting_usage_head_sha256": head_snapshot(usage_root)["head_sha256"],
                "terminal": True,
            },
            "producer_finalizer",
        )
        return completion
    except Exception as exc:
        try:
            if reservation is None or failure_phase in {"reservation", "pre-dispatch"}:
                _finalize_no_dispatch_failure(
                    root,
                    usage_root,
                    auth,
                    auth_sha,
                    lane="producer",
                    attempt_index=attempt_index,
                    claims=claims,
                    packet_disclosure=None,
                    reservation=reservation,
                    error=exc,
                    failure_phase=failure_phase,
                )
            elif len(receipts) == 5 and len(results) == 5:
                _finalize_observed_failure(
                    root,
                    usage_root,
                    reservation,
                    auth,
                    auth_sha,
                    lane="producer",
                    error=exc,
                    failure_phase=failure_phase,
                    attempt_index=attempt_index,
                    claims=claims,
                    packet_disclosure=None,
                    receipts=receipts,
                    observed_results=results,
                    completion=completion_ref,
                    interrupt_after_incident=fault_at == "after-incident-publication",
                )
            else:
                _finalize_provider_failure(
                    root,
                    usage_root,
                    reservation,
                    auth,
                    auth_sha,
                    handles=handles,
                    lane="producer",
                    error=exc,
                    attempt_index=attempt_index,
                    claims=claims,
                    packet_disclosure=None,
                    failure_phase=failure_phase,
                    observed_results=results,
                )
        except Exception as cleanup_exc:
            raise CampaignError(
                f"TRIGGERING_PHASE_ERROR: {type(exc).__name__}: {exc}; "
                f"CLEANUP_PUBLICATION_ERROR: {type(cleanup_exc).__name__}: {cleanup_exc}"
            ) from exc
        if isinstance(exc, CampaignError) and str(exc).startswith("INJECTED_"):
            raise
        if failure_phase == "reservation":
            raise CampaignError(f"RESERVATION_FAILURE: {exc}") from exc
        if failure_phase == "provider-execution":
            raise CampaignError(f"PROVIDER_EXECUTION_FAILED: {exc}") from exc
        raise CampaignError(f"CAMPAIGN_TERMINALIZATION_FAILED[{failure_phase}]: {exc}") from exc


def claim_initial_assessments(
    custody_root: Path,
    producer_completion: dict[str, Any],
    assessments: list[dict[str, str]],
    *,
    claimant: str,
) -> dict[str, Any]:
    root = Path(os.path.abspath(custody_root))
    if producer_completion.get("schema") != "reviewed-campaign-producer-completion-v1" or producer_completion.get("status") != "PRODUCER_STRUCTURAL_COMPLETE":
        raise CampaignError("PRODUCER_STRUCTURAL_COMPLETION_REQUIRED")
    results = producer_completion.get("results")
    if not isinstance(results, list) or len(results) != 5 or any(not isinstance(row, dict) or row.get("structural_status") != "PASS" for row in results):
        raise CampaignError("PRODUCER_STRUCTURAL_COMPLETION_REQUIRED")
    if not isinstance(claimant, str) or HUMAN_ID_RE.fullmatch(claimant) is None:
        raise CampaignError("HUMAN_CLAIMANT_IDENTITY")
    if not isinstance(assessments, list) or len(assessments) != 5:
        raise CampaignError("ASSESSMENT_COUNT: exact five assessments required")
    expected_cases = [row["case_id"] for row in results]
    if [row.get("case_id") for row in assessments if isinstance(row, dict)] != expected_cases:
        raise CampaignError("ASSESSMENT_CASE_BINDING")
    for row in assessments:
        if set(row) != {"case_id", "assessment_sha256"} or SHA256_RE.fullmatch(str(row.get("assessment_sha256", ""))) is None:
            raise CampaignError("ASSESSMENT_HASH_BINDING")
    claim: dict[str, Any] = {
        "schema": "reviewed-campaign-initial-assessment-claim-v1",
        "status": "ALL_FIVE_INITIAL_ASSESSMENTS_HASH_CLAIMED",
        "candidate_id": producer_completion["candidate_id"],
        "cycle_id": producer_completion["cycle_id"],
        "producer_completion_sha256": record_sha256(producer_completion),
        "review_protocol_sha256": producer_completion["review_protocol_sha256"],
        "human_claimant": claimant,
        "assessments": assessments,
        "count": 5,
        "cold_review_disclosure_permitted": True,
    }
    _publish_once_json(root, "human-initial-assessments/claim.json", claim, "assessment_claim")
    return claim


def _load_cold_authorization(root: Path, path: Path) -> tuple[dict[str, Any], str]:
    relative = _relative_to_root(root, path, "cold_review_authorization")
    authorization, raw = _load_canonical_json(_contained(root, relative, "cold_review_authorization", must_exist=True), "cold_review_authorization")
    if set(authorization) != COLD_REVIEW_AUTH_KEYS:
        raise CampaignError("COLD_REVIEW_AUTHORIZATION_SHAPE")
    exact = {
        "schema": "reviewed-campaign-cohort-authorization-v1",
        "kind": "cold-review-cohort",
        "one_use": True,
        "execution_mode": TEST_EXECUTION_MODE,
        "test_only": True,
        "live_execution_authorized": False,
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "adapter_version": "deterministic-fake-v1",
        "host_application_version": "deterministic-test-host-v1",
        "cohort_size": 5,
        "cohort_protocol": "independent-cold-review-v1",
        "dispatch_barrier_protocol": "barrier-five-submit-before-await-v1",
    }
    if any(authorization.get(key) != expected for key, expected in exact.items()):
        raise CampaignError("COLD_REVIEW_AUTHORIZATION_CONTRACT")
    if authorization.get("provider_settings") != COLD_REVIEW_PROVIDER_SETTINGS:
        raise CampaignError("COLD_REVIEW_AUTHORIZATION_PROVIDER_SETTINGS")
    for field in ("authorization_id", "candidate_id", "cycle_or_review_batch_id", "producer_cycle_id"):
        if not isinstance(authorization.get(field), str) or not authorization[field]:
            raise CampaignError(f"COLD_REVIEW_AUTHORIZATION_{field.upper()}")
    if not isinstance(authorization.get("campaign_authorization_sha256"), str) or SHA256_RE.fullmatch(authorization["campaign_authorization_sha256"]) is None:
        raise CampaignError("COLD_REVIEW_AUTHORIZATION_CAMPAIGN_HASH")
    if not isinstance(authorization.get("source_commit"), str) or GIT_OID_RE.fullmatch(authorization["source_commit"]) is None:
        raise CampaignError("COLD_REVIEW_AUTHORIZATION_SOURCE_COMMIT")
    return authorization, hashlib.sha256(raw).hexdigest()


def _validate_packet_set(
    root: Path,
    auth: dict[str, Any],
    producer: dict[str, Any],
    assessment: dict[str, Any],
) -> list[dict[str, Any]]:
    if assessment.get("schema") != "reviewed-campaign-initial-assessment-claim-v1" or assessment.get("status") != "ALL_FIVE_INITIAL_ASSESSMENTS_HASH_CLAIMED" or assessment.get("count") != 5 or assessment.get("cold_review_disclosure_permitted") is not True:
        raise CampaignError("ASSESSMENT_CLAIM_REQUIRED_BEFORE_DISCLOSURE")
    if assessment.get("candidate_id") != auth["candidate_id"] or assessment.get("cycle_id") != auth["producer_cycle_id"] or assessment.get("producer_completion_sha256") != record_sha256(producer):
        raise CampaignError("ASSESSMENT_PRODUCER_BINDING")
    packet_set = auth.get("packet_set")
    if not isinstance(packet_set, list) or len(packet_set) != 5:
        raise CampaignError("PACKET_SET_COUNT")
    if [row.get("case_id") for row in packet_set if isinstance(row, dict)] != auth["case_ids"]:
        raise CampaignError("PACKET_SET_CASE_BINDING")
    producer_results = producer.get("results")
    if not isinstance(producer_results, list) or len(producer_results) != 5:
        raise CampaignError("PRODUCER_STRUCTURAL_COMPLETION_REQUIRED")
    validated: list[dict[str, Any]] = []
    for index, (packet_ref, result) in enumerate(zip(packet_set, producer_results), 1):
        required = {"case_id", "packet_root", "manifest", "input_sha256", "output_sha256"}
        if not isinstance(packet_ref, dict) or set(packet_ref) != required:
            raise CampaignError("PACKET_SET_SHAPE")
        packet_root = _contained(root, packet_ref["packet_root"], f"packet_root_{index}", must_exist=False)
        if not packet_root.is_dir() or _is_reparse(packet_root):
            raise CampaignError("PACKET_ROOT_CUSTODY")
        manifest, manifest_path, manifest_sha = _load_ref(packet_root, packet_ref["manifest"], f"packet_manifest_{index}")
        output = result.get("output") if isinstance(result, dict) else None
        if not isinstance(output, dict) or packet_ref["output_sha256"] != output.get("sha256"):
            raise CampaignError("PACKET_PRODUCER_OUTPUT_BINDING")
        issues = validate_packet_manifest(
            manifest_path,
            packet_root,
            packet_ref["case_id"],
            auth["producer_cycle_id"],
            "reviewed-five-smoke-v1",
            packet_ref["input_sha256"],
            packet_ref["output_sha256"],
        )
        if issues:
            raise CampaignError(f"PACKET_INVALID: {issues[0].failure_class}/{issues[0].failure_subcode}")
        validated.append({**packet_ref, "manifest_sha256": manifest_sha, "packet_id": manifest.get("packet_id"), "payload": manifest.get("payload")})
    return validated


def run_cold_review_cohort(
    custody_root: Path,
    authorization_path: Path,
    adapter: ProviderAdapter,
    *,
    allow_test_fixture: bool = False,
    fault_at: str | None = None,
) -> dict[str, Any]:
    """Run the fake-only cold cohort after all five assessment hashes exist."""
    root = Path(os.path.abspath(custody_root))
    _require_fake_capability(adapter)
    _validate_fault_injection(fault_at, allow_test_fixture)
    auth, auth_sha = _load_cold_authorization(root, authorization_path)
    bindings = _validate_common_bindings(root, auth, allow_test_fixture=allow_test_fixture)
    _contained(
        root,
        auth.get("isolated_root_prefix"),
        "cold_review_isolated_root_prefix",
        must_exist=False,
    )
    attempt_index = bindings["retry"]["attempt_index"]
    producer, _producer_path, producer_sha = _load_ref(root, auth["producer_completion"], "producer_completion")
    assessment, _assessment_path, assessment_sha = _load_ref(root, auth["assessment_claim"], "assessment_claim")
    if producer.get("schema") != "reviewed-campaign-producer-completion-v1" or producer.get("status") != "PRODUCER_STRUCTURAL_COMPLETE" or producer.get("candidate_id") != auth["candidate_id"] or producer.get("cycle_id") != auth["producer_cycle_id"]:
        raise CampaignError("PRODUCER_COMPLETION_BINDING")
    if producer.get("review_protocol_sha256") != bindings["protocol_sha256"] or producer.get("registry_sha256") != bindings["registry_sha256"]:
        raise CampaignError("PROTOCOL_DRIFT_INVALIDATES_FULL_REVIEW_COHORT")
    packets = _validate_packet_set(root, auth, producer, assessment)
    auth_claim = {
        "schema": "reviewed-campaign-authorization-claim-v1",
        "kind": "cold-review-cohort",
        "authorization_sha256": auth_sha,
        "candidate_id": auth["candidate_id"],
        "review_batch_id": auth["cycle_or_review_batch_id"],
        "producer_completion_sha256": producer_sha,
        "assessment_claim_sha256": assessment_sha,
        "execution_mode": TEST_EXECUTION_MODE,
        "live_dispatch": False,
    }
    usage_root = _contained(root, auth["usage_ledger_root"], "usage_ledger_root", must_exist=False)
    _preflight_terminal_publications(
        root,
        usage_root,
        auth,
        auth_sha,
        bindings,
        lane="cold-review",
        attempt_index=attempt_index,
    )
    claims = _consume_attempt_claims(root, auth, auth_sha, bindings, lane="cold-review", authorization_claim=auth_claim)
    disclosure = {
        "schema": "reviewed-campaign-packet-disclosure-v1",
        "candidate_id": auth["candidate_id"],
        "producer_cycle_id": auth["producer_cycle_id"],
        "review_batch_id": auth["cycle_or_review_batch_id"],
        "review_protocol_sha256": bindings["protocol_sha256"],
        "assessment_claim_sha256": assessment_sha,
        "packet_set": packets,
        "all_five_assessments_preceded_disclosure": True,
    }
    try:
        packet_disclosure_ref = _publish_once_json(root, auth["packet_disclosure_path"], disclosure, "packet_disclosure")
    except Exception as exc:
        _finalize_no_dispatch_failure(
            root,
            usage_root,
            auth,
            auth_sha,
            lane="cold-review",
            attempt_index=attempt_index,
            claims=claims,
            packet_disclosure=None,
            reservation=None,
            error=exc,
        )
        raise CampaignError(f"PACKET_DISCLOSURE_FAILURE: {exc}") from exc
    if fault_at == "after-claims-before-reservation":
        error = CampaignError("INJECTED_RESERVATION_FAILURE_AFTER_CLAIMS")
        _finalize_no_dispatch_failure(
            root,
            usage_root,
            auth,
            auth_sha,
            lane="cold-review",
            attempt_index=attempt_index,
            claims=claims,
            packet_disclosure=packet_disclosure_ref,
            reservation=None,
            error=error,
        )
        raise error
    subjects = [f"cold-review:{row['case_id']}:{row['manifest_sha256']}" for row in packets]
    reservation: dict[str, Any] | None = None
    handles: list[str] = []
    results: list[dict[str, object]] = []
    receipts: list[dict[str, object]] = []
    completion_ref: dict[str, object] | None = None
    failure_phase = "reservation"
    try:
        snapshot = head_snapshot(usage_root)
        reservation = reserve(
            usage_root,
            cohort="gpt-review",
            calls=5,
            expected_sequence=snapshot["sequence"],
            expected_head_sha256=snapshot["head_sha256"],
            campaign_authorization_sha256=auth["campaign_authorization_sha256"],
            authorization_sha256=auth_sha,
            candidate_id=auth["candidate_id"],
            cycle_or_review_batch_id=auth["cycle_or_review_batch_id"],
            call_subject_ids=subjects,
        )
        if fault_at == "reservation-exception-after-open":
            raise CampaignError("INJECTED_RESERVATION_EXCEPTION_AFTER_OPEN")
        failure_phase = "pre-dispatch"
        if fault_at == "after-reservation-before-submit":
            raise CampaignError("INJECTED_PRE_DISPATCH_FAILURE")
        workers = _worker_inventory(auth, "cold-review")
        envelopes = [
            _execution_custody(auth, auth_sha, worker, contract, lane="cold-review", packet=packet)
            for worker, contract, packet in zip(workers, reservation["call_contract"], packets)
        ]
        raw_events: list[dict[str, object]] = [
            *({"event": "worker_ready", "worker": row["worker"], "case_id": row["case_id"]} for row in workers),
            {"event": "barrier_release"},
        ]
        failure_phase = "provider-execution"
        for worker, envelope in zip(workers, envelopes):
            raw_events.append({"event": "request_submit_started", "worker": worker["worker"], "case_id": worker["case_id"]})
            handles.append(_submit_with_custody(adapter, envelope))
            raw_events.append({"event": "call_entered_in_flight", "worker": worker["worker"], "case_id": worker["case_id"]})
        raw_events.append({"event": "all_five_in_flight"})
        for index, (worker, packet, envelope, handle) in enumerate(zip(workers, packets, envelopes, handles), 1):
            result = adapter.observe(handle, envelope)
            receipt = _provider_receipt(reservation, index, result, record_sha256(envelope))
            raw = str(result["content_utf8"]).encode("utf-8")
            output_ref = _publish_once_bytes(root, f"cold-review/results/{worker['case_id']}.txt", raw, f"cold_review_result_{index}")
            results.append({"case_id": worker["case_id"], "review_status": "PASS", "packet_manifest_sha256": packet["manifest_sha256"], "review_output": output_ref, "provider_receipt_sha256": record_sha256(receipt)})
            receipts.append(receipt)
            raw_events.append({"event": "terminal_result_observed", "worker": worker["worker"], "case_id": worker["case_id"]})
        failure_phase = "observation-validation"
        manifest = {
            "schema": "daee-smoke-matrix-v1",
            "kind": "cold-review-dispatch-manifest",
            "protocol": "barrier-five-submit-before-await-v1",
            "cohort_protocol": "independent-cold-review-v1",
            "expected_workers": 5,
            "workers": workers,
            "events": chain_dispatch_events(raw_events),
        }
        issues = validate_dispatch_manifest(manifest, 5)
        if issues:
            raise CampaignError(f"COLD_REVIEW_BARRIER_INVALID: {issues[0]['failure_class']}")
        if fault_at in {"after-observation-validation", "after-incident-publication"}:
            failure_phase = "after-observation-validation"
            raise CampaignError(f"INJECTED_TERMINAL_PHASE_FAILURE: {fault_at}")
        failure_phase = "settlement"
        settlement = settle(
            usage_root,
            reservation["transaction_sha256"],
            completed=5,
            failed=0,
            cancelled=0,
            not_dispatched=0,
            unknown=0,
            provider_usage_receipts=receipts,
            measured_cost={"unit": "usd", "value": "0"},
            candidate_id=auth["candidate_id"],
            authorization_sha256=auth_sha,
        )
        if fault_at == "after-settlement":
            failure_phase = fault_at
            raise CampaignError(f"INJECTED_TERMINAL_PHASE_FAILURE: {fault_at}")
        completion: dict[str, Any] = {
            "schema": "reviewed-campaign-cold-review-completion-v1",
            "status": "COLD_REVIEW_COHORT_COMPLETE",
            "candidate_id": auth["candidate_id"],
            "producer_cycle_id": auth["producer_cycle_id"],
            "review_batch_id": auth["cycle_or_review_batch_id"],
            "review_protocol_sha256": bindings["protocol_sha256"],
            "producer_completion_sha256": producer_sha,
            "assessment_claim_sha256": assessment_sha,
            "authorization_sha256": auth_sha,
            "reservation_sha256": reservation["transaction_sha256"],
            "settlement_sha256": settlement["transaction_sha256"],
            "dispatch_manifest": manifest,
            "results": results,
            "final_owner_acceptance": False,
        }
        failure_phase = "completion-publication"
        completion_ref = _publish_once_json(root, "cold-review/completion.json", completion, "cold_review_completion")
        if fault_at == "after-completion":
            failure_phase = fault_at
            raise CampaignError(f"INJECTED_TERMINAL_PHASE_FAILURE: {fault_at}")
        failure_phase = "finalizer-publication"
        _publish_once_json(
            root,
            _attempt_finalizer_path("cold-review", attempt_index),
            {
                "schema": "reviewed-campaign-observation-finalizer-v1",
                "lane": "cold-review",
                "attempt_index": attempt_index,
                "candidate_id": auth["candidate_id"],
                "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
                "authorization_sha256": auth_sha,
                "authorization_claim": claims.get("authorization_claim"),
                "candidate_claim": claims.get("candidate_claim"),
                "continuation_claim": claims.get("continuation_claim"),
                "packet_disclosure": packet_disclosure_ref,
                "candidate_status": "CONSUMED_OBSERVED",
                "review_status": "OBSERVED",
                "dispatch_status": "DETERMINISTIC_FAKE_COMPLETE",
                "reservation_sha256": reservation["transaction_sha256"],
                "settlement_sha256": settlement["transaction_sha256"],
                "observed_results": results,
                "completion": completion_ref,
                "resulting_usage_head_sha256": head_snapshot(usage_root)["head_sha256"],
                "terminal": True,
            },
            "cold_review_finalizer",
        )
        return completion
    except Exception as exc:
        try:
            if reservation is None or failure_phase in {"reservation", "pre-dispatch"}:
                _finalize_no_dispatch_failure(
                    root,
                    usage_root,
                    auth,
                    auth_sha,
                    lane="cold-review",
                    attempt_index=attempt_index,
                    claims=claims,
                    packet_disclosure=packet_disclosure_ref,
                    reservation=reservation,
                    error=exc,
                    failure_phase=failure_phase,
                )
            elif len(receipts) == 5 and len(results) == 5:
                _finalize_observed_failure(
                    root,
                    usage_root,
                    reservation,
                    auth,
                    auth_sha,
                    lane="cold-review",
                    error=exc,
                    failure_phase=failure_phase,
                    attempt_index=attempt_index,
                    claims=claims,
                    packet_disclosure=packet_disclosure_ref,
                    receipts=receipts,
                    observed_results=results,
                    completion=completion_ref,
                    interrupt_after_incident=fault_at == "after-incident-publication",
                )
            else:
                _finalize_provider_failure(
                    root,
                    usage_root,
                    reservation,
                    auth,
                    auth_sha,
                    handles=handles,
                    lane="cold-review",
                    error=exc,
                    attempt_index=attempt_index,
                    claims=claims,
                    packet_disclosure=packet_disclosure_ref,
                    failure_phase=failure_phase,
                    observed_results=results,
                )
        except Exception as cleanup_exc:
            raise CampaignError(
                f"TRIGGERING_PHASE_ERROR: {type(exc).__name__}: {exc}; "
                f"CLEANUP_PUBLICATION_ERROR: {type(cleanup_exc).__name__}: {cleanup_exc}"
            ) from exc
        if isinstance(exc, CampaignError) and str(exc).startswith("INJECTED_"):
            raise
        if failure_phase == "reservation":
            raise CampaignError(f"RESERVATION_FAILURE: {exc}") from exc
        if failure_phase == "provider-execution":
            raise CampaignError(f"PROVIDER_EXECUTION_FAILED: {exc}") from exc
        raise CampaignError(f"CAMPAIGN_TERMINALIZATION_FAILED[{failure_phase}]: {exc}") from exc


def ingest_final_adjudication(
    custody_root: Path,
    cold_review_completion: dict[str, Any],
    adjudication: dict[str, Any],
) -> dict[str, Any]:
    root = Path(os.path.abspath(custody_root))
    required = {
        "schema",
        "adjudication_id",
        "human_adjudicator",
        "candidate_id",
        "producer_cycle_id",
        "review_batch_id",
        "review_completion_sha256",
        "decisions",
        "owner_acceptance_requested",
    }
    if not isinstance(adjudication, dict) or set(adjudication) != required or adjudication.get("schema") != "reviewed-campaign-final-human-adjudication-v1" or adjudication.get("owner_acceptance_requested") is not False:
        raise CampaignError("ADJUDICATION_SHAPE")
    if cold_review_completion.get("schema") != "reviewed-campaign-cold-review-completion-v1" or cold_review_completion.get("status") != "COLD_REVIEW_COHORT_COMPLETE":
        raise CampaignError("COLD_REVIEW_COMPLETION_REQUIRED")
    completion_path = _contained(root, "cold-review/completion.json", "cold_review_completion", must_exist=True)
    if hashlib.sha256(completion_path.read_bytes()).hexdigest() != adjudication.get("review_completion_sha256") or json.loads(completion_path.read_bytes()) != cold_review_completion:
        raise CampaignError("ADJUDICATION_REVIEW_COMPLETION_BINDING")
    joins = ("candidate_id", "producer_cycle_id", "review_batch_id")
    if any(adjudication.get(field) != cold_review_completion.get(field) for field in joins):
        raise CampaignError("ADJUDICATION_CAMPAIGN_BINDING")
    decisions = adjudication.get("decisions")
    expected_cases = [row["case_id"] for row in cold_review_completion.get("results", [])]
    if not isinstance(decisions, list) or len(decisions) != 5 or [row.get("case_id") for row in decisions if isinstance(row, dict)] != expected_cases:
        raise CampaignError("ADJUDICATION_CASE_SET")
    if any(set(row) != {"case_id", "decision"} or row.get("decision") not in {"ACCEPT", "REJECT", "REVIEW_INVALID"} for row in decisions):
        raise CampaignError("ADJUDICATION_DECISION")
    if not isinstance(adjudication.get("human_adjudicator"), str) or HUMAN_ID_RE.fullmatch(adjudication["human_adjudicator"]) is None:
        raise CampaignError("ADJUDICATION_HUMAN_IDENTITY")
    adjudication_ref = _publish_once_json(root, "final-adjudication/adjudication.json", adjudication, "final_adjudication")
    receipt = {
        "schema": "reviewed-campaign-final-adjudication-receipt-v1",
        "status": "HUMAN_ADJUDICATION_INGESTED_OWNER_ACCEPTANCE_OPEN",
        "candidate_id": adjudication["candidate_id"],
        "review_completion_sha256": adjudication["review_completion_sha256"],
        "adjudication": adjudication_ref,
        "owner_acceptance": False,
        "model_execution_authorized": False,
    }
    _publish_once_json(root, "final-adjudication/receipt.json", receipt, "final_adjudication_receipt")
    return receipt


def simulate_paired_gpt_opus_canary(gpt_results: list[str], opus_results: list[str]) -> dict[str, Any]:
    if len(gpt_results) != 5 or len(opus_results) != 5 or any(not isinstance(item, str) for item in gpt_results + opus_results):
        raise CampaignError("PAIRED_FAKE_CANARY_REQUIRES_EXACT_FIVE_PLUS_FIVE")
    workers: list[dict[str, str]] = []
    for family in ("GPT", "OPUS"):
        for index, case_id in enumerate((
            "gate88-secularism",
            "gate88-khaybar",
            "gate88-trinitarian-j173",
            "gate88-tst-lillard",
            "gate88-torah-quran-source-authentication",
        ), 1):
            worker = f"{family.lower()}-{index:02d}"
            base = f"paired-fake/{family.lower()}/{worker}"
            workers.append({"worker": worker, "case_id": case_id, "model_family": family, "home": f"{base}/home", "cache": f"{base}/cache", "run_root": f"{base}/run"})
    events: list[dict[str, object]] = [
        *({"event": "worker_ready", "worker": row["worker"], "case_id": row["case_id"], "model_family": row["model_family"]} for row in workers),
        {"event": "barrier_release"},
    ]
    for row in workers:
        identity = {"worker": row["worker"], "case_id": row["case_id"], "model_family": row["model_family"]}
        events.extend(({"event": "request_submit_started", **identity}, {"event": "call_entered_in_flight", **identity}))
    events.append({"event": "all_ten_in_flight"})
    for row in workers:
        events.append({"event": "terminal_result_observed", "worker": row["worker"], "case_id": row["case_id"], "model_family": row["model_family"]})
    manifest = {"protocol": "barrier-ten-submit-before-await-v1", "expected_workers": 10, "workers": workers, "events": chain_dispatch_events(events)}
    issues = validate_dispatch_manifest(manifest, 10)
    if issues:
        raise CampaignError(f"PAIRED_FAKE_CANARY_INVALID: {issues[0]['failure_class']}")
    return {
        "schema": "reviewed-campaign-paired-fake-canary-v1",
        "dispatch_manifest": manifest,
        "gpt_fake_results": len(gpt_results),
        "opus_fake_results": len(opus_results),
        "live_opus_reachable": False,
        "live_opus_authorized": False,
        "authorization_consumed": False,
    }


def disabled_live_provider_message() -> dict[str, str]:
    return {
        "status": "BLOCKED",
        "error": "LIVE_PROVIDER_UNSUPPORTED: paid/live provider adapters are intentionally absent from the deterministic Task6 lane",
    }


def self_test() -> int:
    canary = simulate_paired_gpt_opus_canary(["gpt"] * 5, ["opus"] * 5)
    ok = (
        not validate_dispatch_manifest(canary["dispatch_manifest"], 10)
        and canary["live_opus_reachable"] is False
        and canary["live_opus_authorized"] is False
        and canary["authorization_consumed"] is False
        and disabled_live_provider_message()["status"] == "BLOCKED"
    )
    print(f"reviewed campaign orchestrator self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    print(json.dumps(disabled_live_provider_message(), sort_keys=True))
    return 2


if __name__ == "__main__":
    sys.exit(main())
