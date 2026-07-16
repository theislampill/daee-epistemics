#!/usr/bin/env python3
"""Fail-closed reviewed five-smoke orchestration interfaces.

The production surface deliberately has no live provider implementation.  Tests may
inject a deterministic fake/no-dispatch adapter after exact custody and preflight
validation.  All durable mutations are create-once or delegated to the existing
CAS-governed campaign usage ledger.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from campaign_usage_ledger import (
    PRODUCER_OBSERVATION_PROTOCOL,
    PRODUCER_WORKER_DEADLINE_RULE,
    head_snapshot,
    reserve,
    settle,
)
from check_cold_comprehensiveness_review import validate_packet_manifest
from check_initial_assessment_barrier import (
    AssessmentBarrierError,
    revalidate_assessment_claim,
    validate_initial_assessment_set,
)
from check_parallel_dispatch_manifest import chain_dispatch_events, validate_dispatch_manifest
import execution_tooling_manifest as tooling_manifest
from source_provenance import strict_json_loads


SHA256_RE = re.compile(r"[0-9a-f]{64}")
GIT_OID_RE = re.compile(r"[0-9a-f]{40}")
HUMAN_ID_RE = re.compile(r"human:[a-z0-9][a-z0-9._-]*")
TASK_IDENTITY_RE = re.compile(r"/root(?:/[a-z0-9][a-z0-9_-]{0,63})*")
WINDOWS_DEVICE_NAMES = {
    "CON", "PRN", "AUX", "NUL", "CLOCK$",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
MATRIX_GOVERNED_SOURCE_JSON_ROLES = frozenset({"input_registry", "review_protocol"})
TASK6_IMPLEMENTATION_OWNER = "/root/task6_no_dispatch"
CONTINUATION_ISSUER = "/root"
TEST_EXECUTION_MODE = "DETERMINISTIC_FAKE_NO_DISPATCH"
SCRIPTED_CODEX_TEST_MODE = "SCRIPTED_CODEX_TEST_NO_PROVIDER"
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


class _AttemptClaimSetError(CampaignError):
    """A consumed attempt claim-set that must terminalize without dispatch."""

    def __init__(self, message: str, claims: dict[str, Any]) -> None:
        super().__init__(message)
        self.claims = claims


class ProviderAdapter(Protocol):
    def capability(self) -> dict[str, object]: ...
    def submit(self, execution_custody: dict[str, object]) -> dict[str, object]: ...
    def submit_tail(self, execution_custodies: list[dict[str, object]]) -> list[dict[str, object]]: ...
    def observe(self, handle: str, execution_custody: dict[str, object]) -> dict[str, object]: ...
    def observe_many(self, handles: list[str], execution_custodies: list[dict[str, object]]) -> tuple[list[dict[str, object] | None], BaseException | None]: ...


def _producer_capture_mode(auth: dict[str, Any]) -> bool:
    return auth.get("kind") == "producer-cohort" and auth.get("execution_mode") in {
        "LIVE_CODEX",
        SCRIPTED_CODEX_TEST_MODE,
    }


def _production_live_mode(auth: dict[str, Any]) -> bool:
    return auth.get("kind") == "producer-cohort" and auth.get("execution_mode") == "LIVE_CODEX"


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


def _attempt_claim_set_path(lane: str, attempt_index: int, authorization_sha256: str) -> str:
    return (
        f"claims/attempt-claim-sets/{lane}-attempt-{attempt_index:02d}-"
        f"{authorization_sha256}.json"
    )


def _claim_projection(role: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "path": path,
        "payload_sha256": record_sha256(payload),
        "payload": payload,
    }


def _recover_claim_projections(
    root: Path,
    projections: list[dict[str, Any]],
    refs: dict[str, dict[str, object] | list[dict[str, object]] | None],
) -> list[dict[str, object]]:
    ref_keys = {
        "authorization": "authorization_claim",
        "candidate": "candidate_claim",
        "retry_continuation": "continuation_claim",
    }
    states: list[dict[str, object]] = []
    for projection in projections:
        role = projection["role"]
        ref_key = ref_keys[role]
        observed: dict[str, object] | None = None
        status = "MISSING"
        try:
            observed = _publish_or_adopt_exact_json(
                root,
                projection["path"],
                projection["payload"],
                f"{role}_claim_projection_recovery",
            )
            refs[ref_key] = observed
            status = "EXACT"
        except Exception:
            refs[ref_key] = None
            path = _contained(
                root,
                projection["path"],
                f"{role}_claim_projection_observation",
                must_exist=False,
            )
            if path.exists():
                status = "COLLISION"
                if path.is_file():
                    observed = _existing_ref(
                        root,
                        projection["path"],
                        f"{role}_claim_projection_collision",
                    )
        states.append(
            {
                "role": role,
                "path": projection["path"],
                "expected_payload_sha256": projection["payload_sha256"],
                "status": status,
                "observed": observed,
            }
        )
    return states


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
    retry = bindings["retry"]
    candidate_claim_path = auth.get("candidate_claim_path") if lane == "producer" else "claims/candidate.json"
    continuation_claim: dict[str, Any] | None = None
    candidate_claim: dict[str, Any] | None = None
    candidate_claim_ref: dict[str, object] | None = None
    if retry["attempt_index"] == 1:
        if lane == "producer":
            candidate_claim = {
                "schema": "reviewed-campaign-candidate-claim-v1",
                "candidate_id": auth["candidate_id"],
                "candidate_maturity_sha256": bindings["candidate_sha256"],
                "authorization_sha256": auth_sha,
                "cycle_id": auth["cycle_or_review_batch_id"],
                "state_before": "READY_UNUSED",
                "irreversible": True,
            }
        else:
            candidate_claim_ref = _existing_ref(root, candidate_claim_path, "candidate_claim")
    else:
        continuation = retry["continuation"]
        assert isinstance(continuation, dict)
        try:
            candidate_claim_ref = _existing_ref(root, candidate_claim_path, "candidate_claim")
            retained_candidate_claim, candidate_path, candidate_claim_sha = _load_ref(
                root,
                candidate_claim_ref,
                "candidate_claim",
            )
            prior_finalizer, finalizer_path, finalizer_sha = _load_ref(root, continuation["prior_finalizer"], "retry_prior_finalizer_recheck")
        except CampaignError as exc:
            raise CampaignError(f"RETRY_CONTINUATION_CANDIDATE_CLAIM_UNAVAILABLE: {exc}") from exc
        expected_candidate_status = "CONSUMED_NO_DISPATCH" if lane == "producer" else "CONSUMED_OBSERVED"
        if retained_candidate_claim.get("schema") != "reviewed-campaign-candidate-claim-v1" or retained_candidate_claim.get("candidate_id") != auth["candidate_id"] or retained_candidate_claim.get("candidate_maturity_sha256") != bindings["candidate_sha256"] or retained_candidate_claim.get("irreversible") is not True:
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
    projections: list[dict[str, Any]] = []
    if continuation_claim is not None:
        projections.append(
            _claim_projection(
                "retry_continuation",
                retry["continuation"]["claim_path"],
                continuation_claim,
            )
        )
    projections.append(_claim_projection("authorization", auth_claim_path, authorization_claim))
    if candidate_claim is not None:
        projections.append(_claim_projection("candidate", candidate_claim_path, candidate_claim))

    attempt_index = retry["attempt_index"]
    claim_set = {
        "schema": "reviewed-campaign-attempt-claim-set-v1",
        "lane": lane,
        "attempt_index": attempt_index,
        "candidate_id": auth["candidate_id"],
        "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
        "authorization_sha256": auth_sha,
        "claim_projections": projections,
        "retained_candidate_claim": candidate_claim_ref,
        "status": "CONSUMED",
        "one_use": True,
    }
    claim_set_relative = _attempt_claim_set_path(lane, attempt_index, auth_sha)
    claim_set_path = _contained(root, claim_set_relative, "attempt_claim_set", must_exist=False)
    recovering = claim_set_path.exists()
    if recovering:
        retained_set, retained_raw = _load_canonical_json(claim_set_path, "attempt_claim_set")
        if retained_set != claim_set or retained_raw != canonical_bytes(claim_set):
            raise CampaignError("ATTEMPT_CLAIM_SET_SUBSTITUTION")
        claim_set_ref = _existing_ref(root, claim_set_relative, "attempt_claim_set")
    else:
        for projection in projections:
            projection_path = _contained(
                root,
                projection["path"],
                f"{projection['role']}_claim_projection",
                must_exist=False,
            )
            if projection_path.exists():
                if projection["role"] == "authorization":
                    raise CampaignError(
                        f"CREATE_ONCE_{lane.upper().replace('-', '_')}_AUTHORIZATION_CLAIM: "
                        "destination already exists"
                    )
                if projection["role"] == "candidate":
                    raise CampaignError("CANDIDATE_ALREADY_CLAIMED")
                raise CampaignError("CREATE_ONCE_RETRY_CONTINUATION_CLAIM: destination already exists")
        claim_set_ref = _publish_once_json(
            root,
            claim_set_relative,
            claim_set,
            "attempt_claim_set",
        )

    refs: dict[str, dict[str, object] | list[dict[str, object]] | None] = {
        "authorization_claim": None,
        "candidate_claim": candidate_claim_ref,
        "continuation_claim": None,
        "attempt_claim_set": claim_set_ref,
    }
    projection_ref_keys = {
        "authorization": "authorization_claim",
        "candidate": "candidate_claim",
        "retry_continuation": "continuation_claim",
    }

    if recovering:
        states = _recover_claim_projections(root, projections, refs)
        if any(state["status"] != "EXACT" for state in states):
            refs["claim_projection_states"] = states
            raise _AttemptClaimSetError(
                "ATTEMPT_CLAIM_PROJECTION_INCOMPLETE: exact claim set has non-exact projections",
                refs,
            )
        raise _AttemptClaimSetError(
            "ATTEMPT_CLAIM_SET_RECOVERY: exact claim set terminalized",
            refs,
        )

    try:
        for projection in projections:
            refs[projection_ref_keys[projection["role"]]] = _publish_once_json(
                root,
                projection["path"],
                projection["payload"],
                (
                    f"{lane}_authorization_claim"
                    if projection["role"] == "authorization"
                    else "candidate_claim"
                    if projection["role"] == "candidate"
                    else "retry_continuation_claim"
                ),
            )
    except Exception as exc:
        states = _recover_claim_projections(root, projections, refs)
        if any(state["status"] != "EXACT" for state in states):
            refs["claim_projection_states"] = states
            raise _AttemptClaimSetError(
                f"ATTEMPT_CLAIM_PROJECTION_INCOMPLETE: {type(exc).__name__}: {exc}",
                refs,
            ) from exc
        raise _AttemptClaimSetError(
            f"ATTEMPT_CLAIM_PROJECTION_FAILURE: {type(exc).__name__}: {exc}",
            refs,
        ) from exc

    return refs


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
    if lane == "producer" and _producer_capture_mode(auth):
        first, *tail = workers
        raw_events.extend(
            (
                {"event": "request_submit_started", "worker": first["worker"], "case_id": first["case_id"]},
                {"event": "call_entered_in_flight", "worker": first["worker"], "case_id": first["case_id"]},
            )
        )
        raw_events.extend(
            {"event": "request_submit_started", "worker": worker["worker"], "case_id": worker["case_id"]}
            for worker in tail
        )
        raw_events.extend(
            {"event": "call_entered_in_flight", "worker": worker["worker"], "case_id": worker["case_id"]}
            for worker in tail
        )
    else:
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
    producer_usage_reservation_sha256s: list[str] | None = None,
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
        completion = {
            "schema": "reviewed-campaign-producer-completion-v1",
            "status": (
                "PRODUCER_CAPTURE_COMPLETE"
                if _producer_capture_mode(auth)
                else "PRODUCER_STRUCTURAL_COMPLETE"
            ),
            "execution_mode": auth["execution_mode"],
            "test_only": auth["test_only"],
            **common,
            "cycle_id": auth["cycle_or_review_batch_id"],
            "source_commit": auth["source_commit"],
            "review_protocol": dict(auth["review_protocol"]),
            "registry_sha256": bindings["registry_sha256"],
            "package_record_sha256": bindings["package_sha256"],
            "candidate_maturity_sha256": bindings["candidate_sha256"],
            "cold_review_authorized": False,
        }
        if _producer_capture_mode(auth):
            completion.update(
                {
                    "package_sha256": auth["package_sha256"],
                    "package_tree_sha256": auth["package_tree_sha256"],
                    "producer_usage_reservation_sha256s": producer_usage_reservation_sha256s,
                }
            )
        return completion
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
    historical_usage: bool = False,
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
    expected_dispatch_status = (
        "LIVE_RAW_CAPTURE_COMPLETE"
        if lane == "producer" and _producer_capture_mode(auth)
        else "DETERMINISTIC_FAKE_COMPLETE"
    )
    if (
        value.get("terminal") is not True
        or value.get("dispatch_status") != expected_dispatch_status
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
    if historical_usage and "usage_unresolved" in value:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_USAGE_HEAD")
    usage_value = {
        **value,
        "usage_unresolved": False if historical_usage else snapshot["unresolved_usage"],
    }
    reservation, settlement = _validate_failure_usage(
        usage_root,
        usage_value,
        auth,
        auth_sha,
        snapshot,
        lane=lane,
        historical=historical_usage,
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
        producer_usage_reservation_sha256s=(
            [row["reservation_sha256"] for row in reservation["reservation_members"]]
            if reservation.get("kind") == "reservation-set" else None
        ),
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


def _validate_attempt_claim_set(
    root: Path,
    payload: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    *,
    lane: str,
    attempt_index: int,
) -> dict[str, str] | None:
    claim_set_ref = payload.get("attempt_claim_set")
    if claim_set_ref is None:
        # Historical v1 finalizers predate atomic attempt claim sets.
        if payload.get("claim_projection_states") is not None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_STATES_WITHOUT_SET")
        return None
    expected_path = _attempt_claim_set_path(lane, attempt_index, auth_sha)
    claim_set = _validate_retained_json_ref(
        root,
        claim_set_ref,
        expected_path,
        "attempt_claim_set",
    )
    required = {
        "schema",
        "lane",
        "attempt_index",
        "candidate_id",
        "cycle_or_review_batch_id",
        "authorization_sha256",
        "claim_projections",
        "retained_candidate_claim",
        "status",
        "one_use",
    }
    expected = {
        "schema": "reviewed-campaign-attempt-claim-set-v1",
        "lane": lane,
        "attempt_index": attempt_index,
        "candidate_id": auth["candidate_id"],
        "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
        "authorization_sha256": auth_sha,
        "status": "CONSUMED",
        "one_use": True,
    }
    if set(claim_set) != required or any(
        claim_set.get(key) != value for key, value in expected.items()
    ):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_ATTEMPT_CLAIM_SET_BINDING")
    expected_roles = (
        ["retry_continuation", "authorization"]
        if attempt_index > 1
        else ["authorization", "candidate"]
        if lane == "producer"
        else ["authorization"]
    )
    projections = claim_set.get("claim_projections")
    if (
        not isinstance(projections, list)
        or [row.get("role") for row in projections if isinstance(row, dict)] != expected_roles
        or len(projections) != len(expected_roles)
    ):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_ATTEMPT_CLAIM_SET_PROJECTIONS")
    ref_fields = {
        "authorization": "authorization_claim",
        "candidate": "candidate_claim",
        "retry_continuation": "continuation_claim",
    }
    explicit_states = payload.get("claim_projection_states")
    if explicit_states is not None and (
        not isinstance(explicit_states, list)
        or len(explicit_states) != len(projections)
    ):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_STATES")
    observed_statuses: dict[str, str] = {}
    for index, projection in enumerate(projections):
        if not isinstance(projection, dict) or set(projection) != {
            "role",
            "path",
            "payload_sha256",
            "payload",
        }:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_ATTEMPT_CLAIM_SET_PROJECTIONS")
        role = projection["role"]
        retained_ref = payload.get(ref_fields[role])
        state = None if explicit_states is None else explicit_states[index]
        if state is None:
            status = "EXACT"
            observed_ref = retained_ref
        else:
            if not isinstance(state, dict) or set(state) != {
                "role",
                "path",
                "expected_payload_sha256",
                "status",
                "observed",
            }:
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_STATES")
            if (
                state.get("role") != role
                or state.get("path") != projection["path"]
                or state.get("expected_payload_sha256") != projection["payload_sha256"]
                or state.get("status") not in {"EXACT", "COLLISION", "MISSING"}
            ):
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_STATES")
            status = state["status"]
            observed_ref = state["observed"]

        if status == "EXACT":
            if retained_ref != observed_ref:
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_EXACT_REF")
            retained = _validate_retained_json_ref(
                root,
                retained_ref,
                projection["path"],
                f"attempt_claim_set_{role}_projection",
            )
            if (
                retained != projection["payload"]
                or projection["payload_sha256"] != record_sha256(retained)
            ):
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_ATTEMPT_CLAIM_SET_PROJECTIONS")
        elif status == "COLLISION":
            if retained_ref is not None:
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_COLLISION_REF")
            path = _contained(
                root,
                projection["path"],
                f"attempt_claim_set_{role}_projection_collision",
                must_exist=False,
            )
            if not path.exists():
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_COLLISION_MISSING")
            if path.is_file():
                expected_observed = _existing_ref(
                    root,
                    projection["path"],
                    f"attempt_claim_set_{role}_projection_collision",
                )
                if observed_ref != expected_observed or path.read_bytes() == canonical_bytes(projection["payload"]):
                    raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_COLLISION_BINDING")
            elif observed_ref is not None:
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_COLLISION_KIND")
        else:
            if retained_ref is not None or observed_ref is not None:
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_MISSING_REF")
            path = _contained(
                root,
                projection["path"],
                f"attempt_claim_set_{role}_projection_missing",
                must_exist=False,
            )
            if path.exists():
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_MISSING_COLLISION")
        observed_statuses[role] = status
    if explicit_states is not None and all(status == "EXACT" for status in observed_statuses.values()):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLAIM_PROJECTION_STATES_REDUNDANT")
    expected_retained_candidate = (
        None if "candidate" in expected_roles else payload.get("candidate_claim")
    )
    if claim_set.get("retained_candidate_claim") != expected_retained_candidate:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_ATTEMPT_CLAIM_SET_CANDIDATE")
    return observed_statuses


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
    projection_states = _validate_attempt_claim_set(
        root,
        payload,
        auth,
        auth_sha,
        lane=lane,
        attempt_index=attempt_index,
    )

    def projection_incomplete(role: str) -> bool:
        return (
            projection_states is not None
            and role in projection_states
            and projection_states[role] != "EXACT"
        )

    auth_claim = None
    if projection_incomplete("authorization"):
        if payload.get("authorization_claim") is not None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_AUTHORIZATION_CLAIM_COLLISION_REF")
    else:
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
        "execution_mode": auth["execution_mode"],
        "live_dispatch": auth.get("execution_mode") == "LIVE_CODEX",
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
    if auth_claim is not None and auth_claim != expected_auth_claim:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_AUTHORIZATION_CLAIM_BINDING")

    candidate_path = auth.get("candidate_claim_path") if lane == "producer" else "claims/candidate.json"
    candidate_claim = None
    if projection_incomplete("candidate"):
        if payload.get("candidate_claim") is not None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CANDIDATE_CLAIM_COLLISION_REF")
    else:
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
    if candidate_claim is not None:
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
    continuation_claim = None
    if projection_incomplete("retry_continuation"):
        if payload.get("continuation_claim") is not None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CONTINUATION_CLAIM_COLLISION_REF")
    else:
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
    if continuation_claim is not None and continuation_claim != expected_continuation_claim:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CONTINUATION_CLAIM_BINDING")


def _historical_usage_resulting_head(
    usage_root: Path,
    snapshot: dict[str, Any],
    transaction_sha256: str,
) -> str:
    """Return the recorded head immediately after a canonical ancestor transaction."""

    current = snapshot.get("last_transaction_sha256")
    child: dict[str, Any] | None = None
    visited: set[str] = set()
    while isinstance(current, str):
        if current in visited:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_USAGE_ANCESTRY_CYCLE")
        visited.add(current)
        path = usage_root / "transactions" / f"{current}.json"
        transaction, raw = _load_canonical_json(path, "historical_usage_transaction")
        if hashlib.sha256(raw).hexdigest() != current:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_USAGE_ANCESTRY_CONTENT_ADDRESS")
        if current == transaction_sha256:
            if child is None:
                head_sha = snapshot.get("head_sha256")
            else:
                head_sha = child.get("predecessor_usage_head_sha256")
            if not isinstance(head_sha, str) or SHA256_RE.fullmatch(head_sha) is None:
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_USAGE_ANCESTRY_HEAD")
            return head_sha
        child = transaction
        current = transaction.get("predecessor_transaction_sha256")
    raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_NOT_USAGE_ANCESTOR")


def _validate_failure_usage(
    usage_root: Path,
    payload: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    snapshot: dict[str, Any],
    *,
    lane: str,
    historical: bool = False,
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
        producer_set = lane == "producer" and _producer_capture_mode(auth)
        expected_reservation = {
            "schema": "campaign-usage-transaction-v2" if producer_set else "campaign-usage-transaction-v1",
            "kind": "reservation-set" if producer_set else "reservation",
            "authorization_sha256": auth_sha,
            "candidate_id": auth["candidate_id"],
            "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
            "lane": lane,
            "reserved_calls": 5,
        }
        if any(reservation.get(key) != expected for key, expected in expected_reservation.items()):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESERVATION_BINDING")
        if producer_set:
            member_shas = [row.get("reservation_sha256") for row in reservation.get("reservation_members", []) if isinstance(row, dict)]
            if len(member_shas) != 5 or payload.get("producer_usage_reservation_sha256s") != member_shas:
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESERVATION_MEMBER_BINDING")

    if settlement_sha is None:
        settlement = None
    else:
        if not isinstance(settlement_sha, str) or SHA256_RE.fullmatch(settlement_sha) is None:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_SHA")
        settlement_path = usage_root / "transactions" / f"{settlement_sha}.json"
        settlement, settlement_raw = _load_canonical_json(settlement_path, "resume_settlement")
        if hashlib.sha256(settlement_raw).hexdigest() != settlement_sha:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_CONTENT_ADDRESS")
        producer_set = lane == "producer" and _producer_capture_mode(auth)
        expected_settlement = {
            "schema": "campaign-usage-transaction-v2" if producer_set else "campaign-usage-transaction-v1",
            "kind": "settlement-set" if producer_set else "settlement",
            "authorization_sha256": auth_sha,
            "candidate_id": auth["candidate_id"],
            "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
            "lane": lane,
            "reservation_transaction_sha256": reservation_sha,
            "reserved_calls": 5,
        }
        if any(settlement.get(key) != expected for key, expected in expected_settlement.items()):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_BINDING")
        if producer_set and settlement.get("reservation_members") != reservation.get("reservation_members"):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_MEMBER_BINDING")
        if not historical and snapshot.get("last_transaction_sha256") != settlement_sha:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_SETTLEMENT_NOT_USAGE_HEAD")

    if snapshot.get("open_reservations"):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_OPEN_RESERVATION")
    if historical and snapshot.get("unresolved_usage") is not False:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_UNRESOLVED_USAGE")
    expected_head = snapshot.get("head_sha256")
    expected_unresolved = snapshot.get("unresolved_usage")
    if historical and settlement is not None and isinstance(settlement_sha, str):
        expected_head = _historical_usage_resulting_head(usage_root, snapshot, settlement_sha)
        expected_unresolved = settlement.get("unknown", 0) > 0
    if payload.get("resulting_usage_head_sha256") != expected_head or payload.get("usage_unresolved") is not expected_unresolved:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_USAGE_HEAD")
    return reservation, settlement


def _load_retained_bytes_ref(
    root: Path,
    value: object,
    role: str,
) -> tuple[Path, bytes, str]:
    if not isinstance(value, dict) or set(value) != {"path", "byte_count", "sha256"}:
        raise CampaignError(f"{role.upper()}_REF_SHAPE")
    expected_sha = value.get("sha256")
    if not isinstance(expected_sha, str) or SHA256_RE.fullmatch(expected_sha) is None:
        raise CampaignError(f"{role.upper()}_REF_HASH")
    path = _contained(root, value.get("path"), role, must_exist=True)
    raw = path.read_bytes()
    if value.get("byte_count") != len(raw) or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise CampaignError(f"{role.upper()}_CONTENT_ADDRESS")
    return path, raw, expected_sha


def _strict_jsonl_object(line: bytes, role: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise CampaignError(f"{role.upper()}_DUPLICATE_KEY")
            value[key] = item
        return value

    def reject_nonfinite(constant: str) -> object:
        raise CampaignError(f"{role.upper()}_NONFINITE_NUMBER: {constant}")

    try:
        value = json.loads(
            line,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignError(f"{role.upper()}_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise CampaignError(f"{role.upper()}_OBJECT_REQUIRED")
    return value


def _rederive_live_provider_facts(
    root: Path,
    capture: dict[str, Any],
    receipt: dict[str, Any],
    result: dict[str, Any],
    auth: dict[str, Any],
    *,
    case_id: str,
    index: int,
) -> None:
    """Derive provider facts from retained JSONL/capture bytes before trusting receipts."""

    events_path, events_raw, _events_sha = _load_retained_bytes_ref(
        root,
        capture.get("raw_event_log"),
        f"producer_raw_event_log_{index}",
    )
    retained_relative = events_path.relative_to(Path(os.path.abspath(root))).as_posix()
    if not retained_relative.startswith(f"{auth['provider_receipt_root']}/"):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_EVENT_CUSTODY")
    lines = events_raw.splitlines()
    if not lines or any(not line for line in lines):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_EVENT_JSONL")
    events = [
        _strict_jsonl_object(line, f"producer_raw_event_{index}_{ordinal}")
        for ordinal, line in enumerate(lines, 1)
    ]
    thread_rows = [row for row in events if row.get("type") == "thread.started"]
    completed_rows = [row for row in events if row.get("type") == "turn.completed"]
    failed_rows = [row for row in events if row.get("type") in {"turn.failed", "error"}]
    if (
        len(thread_rows) != 1
        or len(completed_rows) != 1
        or failed_rows
        or not isinstance(thread_rows[0].get("thread_id"), str)
        or not thread_rows[0]["thread_id"]
    ):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_IDENTITY")
    try:
        admission_path, admission_raw, _admission_sha = _load_retained_bytes_ref(
            root,
            capture.get("in_flight_admission"),
            f"producer_in_flight_admission_{index}",
        )
        admission_relative = admission_path.relative_to(Path(os.path.abspath(root))).as_posix()
        if (
            not admission_relative.startswith(f"{auth['provider_receipt_root']}/")
            or not admission_raw
            or not admission_raw.endswith(b"\n")
            or not events_raw.startswith(admission_raw)
        ):
            raise CampaignError("admission prefix custody or binding invalid")
        admission_lines = admission_raw.splitlines()
        if any(not line for line in admission_lines):
            raise CampaignError("admission prefix JSONL invalid")
        admission_events = [
            _strict_jsonl_object(line, f"producer_in_flight_admission_{index}_{ordinal}")
            for ordinal, line in enumerate(admission_lines, 1)
        ]
        admission_threads = [row for row in admission_events if row.get("type") == "thread.started"]
        if (
            len(admission_threads) != 1
            or admission_threads[0].get("thread_id") != thread_rows[0]["thread_id"]
            or any(row.get("type") in {"turn.completed", "turn.failed", "error"} for row in admission_events)
        ):
            raise CampaignError("admission prefix semantics invalid")
    except (CampaignError, ValueError) as exc:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_ADMISSION") from exc
    derived_provider_call_id = f"codex-thread:{thread_rows[0]['thread_id']}"
    raw_usage = completed_rows[0].get("usage")
    if not isinstance(raw_usage, dict):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_USAGE")
    input_tokens = raw_usage.get("input_tokens")
    cached_tokens = raw_usage.get("cached_input_tokens")
    output_tokens = raw_usage.get("output_tokens")
    token_values = (input_tokens, cached_tokens, output_tokens)
    if (
        any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in token_values)
        or cached_tokens > input_tokens
    ):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_USAGE")
    derived_usage = {
        "status": "RECORDED",
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
    if any("cost" in row for row in events):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_COST")
    derived_cost = dict(LIVE_COST_UNAVAILABLE)

    identity = capture.get("completion_identity")
    if not isinstance(identity, dict) or set(identity) != {
        "provider_call_id", "host_invocation_id", "started_at", "ended_at",
    }:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_IDENTITY")
    if identity.get("provider_call_id") != derived_provider_call_id:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_IDENTITY")
    host_invocation_id = identity.get("host_invocation_id")
    if (
        not isinstance(host_invocation_id, str)
        or re.fullmatch(rf"codex-host:[1-9][0-9]*:{re.escape(case_id)}", host_invocation_id) is None
    ):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_HOST_IDENTITY")
    try:
        started_at = _parse_utc(identity.get("started_at"), "producer_dispatch_started_at")
        ended_at = _parse_utc(identity.get("ended_at"), "producer_dispatch_ended_at")
    except CampaignError as exc:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_HOST_TIMESTAMPS") from exc
    if ended_at < started_at:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_HOST_TIMESTAMPS")
    window = auth.get("authorization_window")
    if not isinstance(window, dict) or set(window) != {
        "launch_not_before", "launch_not_after", "parent_valid_not_before", "parent_valid_not_after",
    }:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_DISPATCH_AUTHORIZATION_WINDOW")
    child_start = _parse_utc(window["launch_not_before"], "historical_launch_not_before")
    child_end = _parse_utc(window["launch_not_after"], "historical_launch_not_after")
    parent_start = _parse_utc(window["parent_valid_not_before"], "historical_parent_valid_not_before")
    parent_end = _parse_utc(window["parent_valid_not_after"], "historical_parent_valid_not_after")
    if not parent_start <= child_start <= started_at <= child_end <= parent_end:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_DISPATCH_AUTHORIZATION_WINDOW")

    if capture.get("usage") != derived_usage or receipt.get("usage") != derived_usage:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_USAGE")
    if capture.get("cost") != derived_cost or receipt.get("cost") != derived_cost:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_COST")
    if receipt.get("provider_call_id") != derived_provider_call_id:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_PROVIDER_IDENTITY")
    if receipt.get("host_invocation_id") != host_invocation_id:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_HOST_IDENTITY")
    if receipt.get("started_at") != identity["started_at"] or receipt.get("ended_at") != identity["ended_at"]:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_HOST_TIMESTAMPS")
    if (
        receipt.get("accepted") is not None
        or receipt.get("in_flight") is not False
        or receipt.get("acknowledgment_origin") != "ADAPTER_IN_FLIGHT"
        or receipt.get("status") != "COMPLETED"
        or receipt.get("unknown_kind") is not None
        or receipt.get("terminal_transport_status") != "COMPLETED"
    ):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_HOST_TRANSPORT")
    _output_path, raw_output, _output_sha = _load_retained_bytes_ref(
        root,
        capture.get("raw_output"),
        f"producer_raw_output_{index}",
    )
    projection_failed = result.get("projection_status") == "FAILED"
    expected_result_path = (
        capture.get("raw_output", {}).get("path")
        if projection_failed and isinstance(capture.get("raw_output"), dict)
        else f"producer/results/{case_id}.txt"
    )
    _result_path, result_output = _validate_retained_ref(
        root,
        result.get("output"),
        expected_result_path,
        f"producer_resume_result_{index}",
    )
    try:
        raw_output.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_OUTPUT_UTF8") from exc
    if not raw_output or raw_output != result_output:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RAW_OUTPUT_BINDING")


def _derive_terminal_receipt_state(
    settlement: dict[str, Any] | None,
    auth: dict[str, Any],
) -> dict[str, Any]:
    if settlement is None:
        return {
            "classification": "PROVED_NO_DISPATCH",
            "completed": 0,
            "dispatch_unknown": 0,
            "outcome_unknown": 0,
            "not_dispatched": 0,
            "completed_receipts": [],
        }
    receipts = settlement.get("provider_usage_receipts")
    if not isinstance(receipts, list) or len(receipts) != 5:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RECEIPT_STATE_INVENTORY")
    completed_receipts: list[tuple[int, dict[str, Any]]] = []
    dispatch_unknown = 0
    outcome_unknown = 0
    not_dispatched = 0
    batch_id = settlement.get("cycle_or_review_batch_id")
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RECEIPT_STATE_INVENTORY")
        if receipt.get("call_id") != f"{batch_id}:call-{index + 1:02d}":
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RECEIPT_CALL_IDENTITY")
        status = receipt.get("status")
        unknown_kind = receipt.get("unknown_kind")
        if status == "COMPLETED" and unknown_kind is None:
            completed_receipts.append((index, receipt))
        elif status == "UNKNOWN" and unknown_kind == "DISPATCH_UNKNOWN":
            dispatch_unknown += 1
        elif status == "UNKNOWN" and unknown_kind == "OUTCOME_UNKNOWN":
            outcome_unknown += 1
        elif status == "NOT_DISPATCHED" and unknown_kind is None:
            not_dispatched += 1
        else:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RECEIPT_STATE_INVENTORY")
    completed = len(completed_receipts)
    unknown = dispatch_unknown + outcome_unknown
    expected_counts = {
        "completed": completed,
        "unknown": unknown,
        "not_dispatched": not_dispatched,
        "failed": 0,
        "cancelled": 0,
    }
    if any(settlement.get(field) != value for field, value in expected_counts.items()):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RECEIPT_STATE_COUNTS")
    if completed + unknown + not_dispatched != 5:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RECEIPT_STATE_COUNTS")
    if outcome_unknown:
        classification = "OUTCOME_UNKNOWN"
    elif dispatch_unknown:
        classification = "DISPATCH_UNKNOWN"
    elif completed == 5:
        classification = "OBSERVED"
    elif not_dispatched == 5:
        classification = "PROVED_NO_DISPATCH"
    else:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RECEIPT_STATE_CLASSIFICATION")
    return {
        "classification": classification,
        "completed": completed,
        "dispatch_unknown": dispatch_unknown,
        "outcome_unknown": outcome_unknown,
        "not_dispatched": not_dispatched,
        "completed_receipts": completed_receipts,
    }


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
    receipt_state = _derive_terminal_receipt_state(settlement, auth)
    completed_receipts = receipt_state["completed_receipts"]
    if len(results) != len(completed_receipts):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULTS_COMPLETED_RECEIPTS")
    expected_cases = [auth["case_ids"][index] for index, _receipt in completed_receipts]
    if [row.get("case_id") for row in results] != expected_cases:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULTS_COMPLETED_RECEIPTS")
    packet_by_case = {
        row.get("case_id"): row.get("manifest_sha256")
        for row in packet_disclosure.get("packet_set", [])
        if isinstance(row, dict)
    } if isinstance(packet_disclosure, dict) else {}
    for row, (call_index, completed_receipt) in zip(results, completed_receipts):
        case_id = auth["case_ids"][call_index]
        index = call_index + 1
        if lane == "producer":
            if _producer_capture_mode(auth):
                normal_fields = {
                    "case_id", "capture_status", "structural_status", "output",
                    "capture_evidence", "provider_receipt", "provider_receipt_sha256",
                }
                failed_projection_fields = {*normal_fields, "projection_status"}
                projection_failed = row.get("projection_status") == "FAILED"
                if (
                    set(row) != (failed_projection_fields if projection_failed else normal_fields)
                    or row.get("capture_status") != "CAPTURED"
                    or row.get("structural_status") != "UNVERIFIED"
                ):
                    raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PRODUCER_RESULT_STATE")
                capture, _capture_path, _capture_sha = _load_ref(
                    root,
                    row.get("capture_evidence"),
                    f"producer_resume_capture_{index}",
                )
                capture_expected = {
                    "schema": "reviewed-campaign-live-capture-v1",
                    "status": "CAPTURED",
                    "candidate_id": auth["candidate_id"],
                    "source_commit": auth["source_commit"],
                    "case_id": case_id,
                    "package_sha256": auth["package_sha256"],
                    "package_tree_sha256": auth["package_tree_sha256"],
                    "structural_status": "UNVERIFIED",
                }
                if any(capture.get(key) != expected for key, expected in capture_expected.items()):
                    raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PRODUCER_CAPTURE_BINDING")
                capture_output = capture.get("raw_output")
                if (
                    not isinstance(capture_output, dict)
                    or _existing_ref(
                        root,
                        capture_output.get("path"),
                        f"producer_resume_capture_output_{index}",
                    ) != capture_output
                    or not isinstance(row.get("output"), dict)
                    or capture_output.get("sha256") != row["output"].get("sha256")
                    or capture_output.get("byte_count") != row["output"].get("byte_count")
                    or (projection_failed and capture_output != row["output"])
                ):
                    raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PRODUCER_CAPTURE_OUTPUT")
                custody, _custody_path, custody_sha = _load_ref(
                    root,
                    capture.get("execution_custody"),
                    f"producer_resume_custody_{index}",
                )
                custody_expected = {
                    "schema": "reviewed-campaign-execution-custody-v1",
                    "lane": "producer",
                    "candidate_id": auth["candidate_id"],
                    "source_commit": auth["source_commit"],
                    "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
                    "case_id": case_id,
                    "model": "gpt-5.5",
                    "reasoning_effort": "high",
                    "authorization_sha256": payload.get("authorization_sha256"),
                }
                reservation_members = settlement.get("reservation_members")
                if not isinstance(reservation_members, list) or len(reservation_members) != 5:
                    raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PRODUCER_RESERVATION_MEMBERS")
                usage_reservation_sha = reservation_members[index - 1].get("reservation_sha256")
                custody_expected["usage_reservation_sha256"] = usage_reservation_sha
                if (
                    any(custody.get(key) != expected for key, expected in custody_expected.items())
                    or capture.get("execution_custody_sha256") != custody_sha
                    or completed_receipt.get("usage_reservation_sha256") != usage_reservation_sha
                ):
                    raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PRODUCER_CUSTODY_BINDING")
                if projection_failed:
                    if row.get("provider_receipt") is not None:
                        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULT_RECEIPT")
                    receipt = completed_receipt
                    receipt_path = None
                    receipt_sha = record_sha256(receipt)
                else:
                    receipt, receipt_path, receipt_sha = _load_ref(
                        root,
                        row.get("provider_receipt"),
                        f"producer_resume_receipt_{index}",
                    )
                _rederive_live_provider_facts(
                    root,
                    capture,
                    receipt,
                    row,
                    auth,
                    case_id=case_id,
                    index=index,
                )
                if (
                    receipt != completed_receipt
                    or row.get("provider_receipt_sha256") != receipt_sha
                    or capture.get("completion_identity", {}).get("provider_call_id")
                    != receipt.get("provider_call_id")
                ):
                    raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULT_RECEIPT")
                if not projection_failed:
                    expected_receipt_path = (
                        f"{auth['provider_receipt_root']}/{receipt_sha}.receipt.json"
                    )
                    if (
                        receipt_path is None
                        or receipt_path.relative_to(Path(os.path.abspath(root))).as_posix()
                        != expected_receipt_path
                    ):
                        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULT_RECEIPT")
            elif set(row) != {"case_id", "structural_status", "output", "provider_receipt_sha256"} or row.get("structural_status") != "PASS":
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PRODUCER_RESULT_STATE")
            if not (_producer_capture_mode(auth) and row.get("projection_status") == "FAILED"):
                _validate_retained_ref(root, row.get("output"), f"producer/results/{case_id}.txt", f"producer_resume_result_{index}")
        else:
            if set(row) != {"case_id", "review_status", "packet_manifest_sha256", "review_output", "provider_receipt_sha256"} or row.get("review_status") != "PASS":
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COLD_RESULT_STATE")
            if row.get("packet_manifest_sha256") != packet_by_case.get(case_id):
                raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COLD_RESULT_PACKET")
            _validate_retained_ref(root, row.get("review_output"), f"cold-review/results/{case_id}.txt", f"cold_resume_result_{index}")
        if row.get("provider_receipt_sha256") != record_sha256(completed_receipt):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_RESULT_RECEIPT")
    return results


_FAILURE_PHASE_CLASSIFICATIONS = {
    "reservation": frozenset({"PROVED_NO_DISPATCH"}),
    "pre-dispatch": frozenset({"PROVED_NO_DISPATCH"}),
    "provider-execution": frozenset({"DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN"}),
    "result-publication": frozenset({"DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN", "OBSERVED"}),
    "provider-receipt-publication": frozenset(
        {"DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN", "OBSERVED"}
    ),
    "observation-validation": frozenset({"OBSERVED"}),
    "after-observation-validation": frozenset({"OBSERVED"}),
    "settlement": frozenset({"OBSERVED"}),
    "after-settlement": frozenset({"OBSERVED"}),
    "completion-publication": frozenset({"OBSERVED"}),
    "after-completion": frozenset({"OBSERVED"}),
    "finalizer-publication": frozenset({"OBSERVED"}),
}


def _terminal_failure_class(phase: object, classification: object) -> str | None:
    allowed = _FAILURE_PHASE_CLASSIFICATIONS.get(phase)
    if allowed is None or classification not in allowed:
        return None
    return (
        "post-observation-terminal-failure"
        if classification == "OBSERVED"
        else "reservation-or-provider-failure"
    )


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
        "producer_usage_reservation_sha256s": payload.get("producer_usage_reservation_sha256s"),
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
    expected_failure_class = _terminal_failure_class(phase, classification)
    if expected_failure_class is None:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_PHASE_CLASSIFICATION")
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
    receipt_state = _derive_terminal_receipt_state(settlement, auth)
    if classification != receipt_state["classification"]:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_CLASSIFICATION_RECEIPTS")
    results = _validate_failure_results(root, payload, auth, settlement, packet_disclosure, lane=lane)
    if classification != "PROVED_NO_DISPATCH" and (reservation is None or settlement is None):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_TERMINAL_USAGE_REQUIRED")
    if classification == "OBSERVED" and (settlement.get("completed") != 5 or settlement.get("unknown") != 0):
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_OBSERVED_SETTLEMENT")
    if classification in {"DISPATCH_UNKNOWN", "OUTCOME_UNKNOWN"}:
        completed = settlement.get("completed")
        unknown = settlement.get("unknown")
        not_dispatched = settlement.get("not_dispatched")
        if (
            not all(isinstance(value, int) and not isinstance(value, bool) for value in (completed, unknown, not_dispatched))
            or unknown < 1
            or completed + unknown + not_dispatched != 5
            or snapshot.get("unresolved_usage") is not True
        ):
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
        if lane == "producer":
            expected_completion.update(
                {
                    "review_protocol": dict(auth["review_protocol"]),
                    "review_protocol_sha256": bindings["protocol_sha256"],
                }
            )
        if any(completion.get(key) != expected for key, expected in expected_completion.items()):
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COMPLETION_BINDING")
        batch_field = "cycle_id" if lane == "producer" else "review_batch_id"
        if completion.get(batch_field) != auth["cycle_or_review_batch_id"]:
            raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COMPLETION_BATCH")
    elif completion_ref is not None:
        raise CampaignError("TERMINAL_PUBLICATION_PREFLIGHT_COMPLETION_PHASE")

    expected_resumable = (
        classification == "PROVED_NO_DISPATCH"
        and not snapshot.get("unresolved_usage")
        and (lane != "producer" or payload.get("candidate_claim") is not None)
    )
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
    failure_class = _terminal_failure_class(failure_phase, dispatch_classification)
    if failure_class is None:
        raise CampaignError("FAILURE_FINALIZER_PHASE_CLASSIFICATION")
    producer_usage_reservation_sha256s: list[str] | None = None
    if lane == "producer" and isinstance(reservation_sha256, str):
        reservation_path = usage_root / "transactions" / f"{reservation_sha256}.json"
        reservation_record, reservation_raw = _load_canonical_json(
            reservation_path,
            "failure_finalizer_reservation",
        )
        if hashlib.sha256(reservation_raw).hexdigest() != reservation_sha256:
            raise CampaignError("FAILURE_FINALIZER_RESERVATION_CONTENT_ADDRESS")
        if reservation_record.get("kind") == "reservation-set":
            producer_usage_reservation_sha256s = [
                row.get("reservation_sha256")
                for row in reservation_record.get("reservation_members", [])
                if isinstance(row, dict)
            ]
            if len(producer_usage_reservation_sha256s) != 5:
                raise CampaignError("FAILURE_FINALIZER_RESERVATION_MEMBER_BINDING")
    finalizer_payload = {
        "schema": "reviewed-campaign-observation-finalizer-v1",
        "lane": lane,
        "attempt_index": attempt_index,
        "candidate_id": auth["candidate_id"],
        "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
        "authorization_sha256": auth_sha,
        "attempt_claim_set": claims.get("attempt_claim_set"),
        "authorization_claim": claims.get("authorization_claim"),
        "candidate_claim": claims.get("candidate_claim"),
        "continuation_claim": claims.get("continuation_claim"),
        **(
            {"claim_projection_states": claims["claim_projection_states"]}
            if claims.get("claim_projection_states") is not None
            else {}
        ),
        "packet_disclosure": packet_disclosure,
        "failure_phase": failure_phase,
        "observed_results": observed_results or [],
        "completion": completion,
        "candidate_status": candidate_status,
        "review_status": "NO_DISPATCH" if lane == "cold-review" and dispatch_classification == "PROVED_NO_DISPATCH" else "OBSERVED" if lane == "cold-review" and dispatch_classification == "OBSERVED" else "DISPATCH_UNKNOWN" if lane == "cold-review" else None,
        "dispatch_status": "PROVED_NOT_DISPATCHED" if dispatch_classification == "PROVED_NO_DISPATCH" else dispatch_classification,
        "dispatch_classification": dispatch_classification,
        "reservation_sha256": reservation_sha256,
        **(
            {"producer_usage_reservation_sha256s": producer_usage_reservation_sha256s}
            if producer_usage_reservation_sha256s is not None else {}
        ),
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
        "failure_class": failure_class,
        "failure_phase": failure_phase,
        "error_type": type(error).__name__,
        "dispatch_classification": dispatch_classification,
        "reservation_sha256": reservation_sha256,
        **(
            {"producer_usage_reservation_sha256s": producer_usage_reservation_sha256s}
            if producer_usage_reservation_sha256s is not None else {}
        ),
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
            if hashlib.sha256(raw).hexdigest() == open_sha and candidate_reservation.get("kind") in {"reservation","reservation-set"} and candidate_reservation.get("candidate_id") == auth["candidate_id"] and candidate_reservation.get("authorization_sha256") == auth_sha and candidate_reservation.get("cycle_or_review_batch_id") == auth["cycle_or_review_batch_id"]:
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
    resumable = (
        not snapshot["open_reservations"]
        and not snapshot["unresolved_usage"]
        and (lane != "producer" or claims.get("candidate_claim") is not None)
    )
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


LIVE_PROVIDER_CAPABILITY_KEYS = {
    "schema", "adapter_kind", "adapter_version", "host_application_version",
    "codex_executable_sha256", "model", "reasoning_effort", "test_only",
    "paid_provider_reachable", "live_execution_authorized",
}


def _probe_producer_capability(adapter: ProviderAdapter) -> dict[str, object]:
    """Probe before any authorization read/claim; this probe must produce no model output."""
    try:
        capability = adapter.capability()
    except Exception as exc:
        raise CampaignError("PROVIDER_CAPABILITY_UNAVAILABLE") from exc
    if not isinstance(capability, dict):
        raise CampaignError("PROVIDER_CAPABILITY_INVALID")
    if capability.get("adapter_kind") == "deterministic-fake-no-dispatch":
        if set(capability) != PROVIDER_CAPABILITY_KEYS:
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
            raise CampaignError("PROVIDER_CAPABILITY_INVALID")
        return capability
    if capability.get("adapter_kind") == "codex-scripted-test-no-provider":
        if set(capability) != LIVE_PROVIDER_CAPABILITY_KEYS:
            raise CampaignError("PROVIDER_CAPABILITY_INVALID")
        exact_scripted = {
            "schema": "reviewed-campaign-provider-capability-v1",
            "adapter_kind": "codex-scripted-test-no-provider",
            "adapter_version": "codex-scripted-test-v1",
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "test_only": True,
            "paid_provider_reachable": False,
            "live_execution_authorized": False,
        }
        if any(capability.get(key) != value for key, value in exact_scripted.items()):
            raise CampaignError("PROVIDER_CAPABILITY_INVALID")
        if not isinstance(capability.get("host_application_version"), str) or not capability["host_application_version"]:
            raise CampaignError("PROVIDER_CAPABILITY_INVALID")
        if not isinstance(capability.get("codex_executable_sha256"), str) or SHA256_RE.fullmatch(capability["codex_executable_sha256"]) is None:
            raise CampaignError("PROVIDER_CAPABILITY_INVALID")
        return capability
    if set(capability) != LIVE_PROVIDER_CAPABILITY_KEYS:
        if capability.get("paid_provider_reachable") or not capability.get("test_only"):
            raise CampaignError("LIVE_PROVIDER_UNSUPPORTED")
        raise CampaignError("PROVIDER_CAPABILITY_INVALID")
    exact_live = {
        "schema": "reviewed-campaign-provider-capability-v1",
        "adapter_kind": "codex-live",
        "adapter_version": "codex-live-v1",
        "model": "gpt-5.5",
        "reasoning_effort": "high",
        "test_only": False,
        "paid_provider_reachable": True,
        "live_execution_authorized": True,
    }
    if any(capability.get(key) != value for key, value in exact_live.items()):
        raise CampaignError("PROVIDER_CAPABILITY_INVALID")
    if not isinstance(capability.get("host_application_version"), str) or not capability["host_application_version"]:
        raise CampaignError("PROVIDER_CAPABILITY_INVALID")
    if not isinstance(capability.get("codex_executable_sha256"), str) or SHA256_RE.fullmatch(capability["codex_executable_sha256"]) is None:
        raise CampaignError("PROVIDER_CAPABILITY_INVALID")
    return capability


def _matrix_ref(root: Path, value: object, role: str) -> tuple[dict[str, Any], dict[str, object], bytes]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise CampaignError(f"{role.upper()}_REF_SHAPE")
    path = _contained(root, value.get("path"), role, must_exist=True)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != value.get("sha256"):
        raise CampaignError(f"{role.upper()}_CONTENT_ADDRESS")
    try:
        record = strict_json_loads(raw, label=str(path))
    except ValueError as exc:
        raise CampaignError(f"{role.upper()}_JSON_INVALID") from exc
    if not isinstance(record, dict) or (
        role not in MATRIX_GOVERNED_SOURCE_JSON_ROLES
        and raw != canonical_bytes(record)
    ):
        raise CampaignError(f"{role.upper()}_CANONICAL_JSON_REQUIRED")
    internal = {"path": value["path"], "byte_count": len(raw), "sha256": value["sha256"]}
    return record, internal, raw


def _parse_utc(value: object, role: str) -> datetime:
    if not isinstance(value, str):
        raise CampaignError(f"{role.upper()}_INVALID")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise CampaignError(f"{role.upper()}_INVALID") from exc
    return parsed


def _normalize_live_producer_authorization(
    root: Path,
    authorization: dict[str, Any],
    raw: bytes,
    *,
    require_active_window: bool = True,
    allow_test_fixture: bool = False,
) -> tuple[dict[str, Any], str]:
    try:
        from check_smoke_matrix_manifest import validate_manifest
    except Exception as exc:
        raise CampaignError("MATRIX_AUTHORIZATION_CHECKER_UNAVAILABLE") from exc
    findings = validate_manifest(authorization, root=root)
    if findings:
        raise CampaignError(f"MATRIX_AUTHORIZATION_INVALID: {findings[0]['failure_class']}")
    parent, parent_ref, parent_raw = _matrix_ref(root, authorization["campaign_authorization"], "campaign_authorization")
    parent_keys = {
        "schema", "kind", "authorization_id", "status", "revoked", "valid_not_before", "valid_not_after",
        "branch", "source_commit", "source_preflight", "candidate_id", "candidate_state",
        "candidate_claim_status", "package_profile", "package_sha256", "package_tree_sha256",
        "input_registry", "review_protocol", "action", "lane", "model_runner", "producer_model",
        "producer_reasoning_effort", "authorized_calls", "case_inputs", "automatic_retry_authorized",
        "optional_opus_authorized", "authorization_sha256",
    }
    if set(parent) != parent_keys or parent.get("schema") != "reviewed-campaign-owner-authorization-v1" or parent.get("kind") != "reviewed-five-smoke-campaign":
        raise CampaignError("PARENT_CAMPAIGN_AUTHORIZATION_SHAPE")
    unsigned_parent = {key: value for key, value in parent.items() if key != "authorization_sha256"}
    if parent.get("authorization_sha256") != record_sha256(unsigned_parent):
        raise CampaignError("PARENT_CAMPAIGN_AUTHORIZATION_SELF_HASH")
    parent_sha = hashlib.sha256(parent_raw).hexdigest()
    if parent_ref["sha256"] != parent_sha or authorization.get("campaign_authorization_sha256") != parent_sha:
        raise CampaignError("PARENT_CAMPAIGN_AUTHORIZATION_BINDING")
    parent_exact = {
        "status": "ACTIVE", "revoked": False, "branch": authorization["branch"],
        "source_commit": authorization["source_commit"], "source_preflight": authorization["source_preflight"],
        "candidate_id": authorization["candidate_id"], "candidate_state": "READY_UNUSED",
        "candidate_claim_status": "UNCLAIMED", "package_profile": "execution-mini",
        "package_sha256": authorization["package_sha256"], "package_tree_sha256": authorization["package_tree_sha256"],
        "input_registry": authorization["input_registry"], "review_protocol": authorization["review_protocol"],
        "action": "RUN_REVIEWED_FIVE_SMOKE", "lane": "producer", "model_runner": "codex",
        "producer_model": "gpt-5.5", "producer_reasoning_effort": "high", "authorized_calls": 5,
        "case_inputs": authorization["case_inputs"], "automatic_retry_authorized": False,
        "optional_opus_authorized": False,
    }
    if any(parent.get(key) != expected for key, expected in parent_exact.items()):
        raise CampaignError("PARENT_CAMPAIGN_AUTHORIZATION_SCOPE")
    child_start = _parse_utc(authorization["launch_not_before"], "launch_not_before")
    child_end = _parse_utc(authorization["launch_not_after"], "launch_not_after")
    parent_start = _parse_utc(parent["valid_not_before"], "parent_valid_not_before")
    parent_end = _parse_utc(parent["valid_not_after"], "parent_valid_not_after")
    if not parent_start <= child_start < child_end <= parent_end:
        raise CampaignError("LIVE_AUTHORIZATION_WINDOW")
    if require_active_window:
        now = datetime.now(timezone.utc)
        if not child_start <= now <= child_end:
            raise CampaignError("LIVE_AUTHORIZATION_WINDOW")
    refs: dict[str, dict[str, object]] = {}
    for internal_name, field in (
        ("candidate_readiness", "candidate_readiness"),
        ("candidate_maturity", "candidate_maturity"),
        ("package_record", "candidate_record"),
        ("source_commit_receipt", "source_commit_receipt"),
        ("source_preflight", "source_preflight"),
        ("execution_tooling_manifest", "execution_tooling_manifest"),
        ("registry", "input_registry"), ("review_protocol", "review_protocol"),
    ):
        _record, refs[internal_name], _raw = _matrix_ref(root, authorization[field], field)
    normalized: dict[str, Any] = {
        "schema": "reviewed-campaign-cohort-authorization-v1",
        "kind": "producer-cohort",
        "authorization_id": authorization["authorization_id"],
        "one_use": True,
        "execution_mode": "LIVE_CODEX",
        "test_only": False,
        "live_execution_authorized": True,
        "campaign_authorization_sha256": parent_sha,
        "campaign_authorization": parent_ref,
        "candidate_id": authorization["candidate_id"],
        "candidate_state_at_authorization": authorization["candidate_state_at_authorization"],
        "candidate_claim_status_at_authorization": authorization["candidate_claim_status_at_authorization"],
        "cycle_or_review_batch_id": authorization["cycle_id"],
        "source_commit": authorization["source_commit"],
        "package_sha256": authorization["package_sha256"],
        "package_tree_sha256": authorization["package_tree_sha256"],
        "tree_digest_algorithm": authorization["tree_digest_algorithm"],
        **refs,
        "model": "gpt-5.5",
        "reasoning_effort": "high",
        "adapter_version": authorization["adapter_version"],
        "host_application_version": authorization["host_application_version"],
        "codex_executable_sha256": authorization["codex_executable_sha256"],
        "provider_settings": authorization["provider_settings"],
        "cohort_size": 5,
        "cohort_protocol": "barrier-five-submit-before-await-v1",
        "case_ids": authorization["case_ids"],
        "case_inputs": authorization["case_inputs"],
        "candidate_package_root": authorization["candidate_package_root"],
        "isolated_root_prefix": authorization["isolated_root_prefix"],
        "usage_ledger_root": authorization["usage_ledger_root"],
        "authorization_claim_path": authorization["authorization_claim_path"],
        "candidate_claim_path": authorization["candidate_claim_path"],
        "observation_finalizer_path": authorization["observation_finalizer_path"],
        "prompt_retention_root": authorization["prompt_retention_root"],
        "output_retention_root": authorization["output_retention_root"],
        "provider_receipt_root": authorization["provider_receipt_root"],
        "structural_evidence_root": authorization["structural_evidence_root"],
        "expected_campaign_usage_sequence": authorization["expected_campaign_usage_sequence"],
        "expected_campaign_usage_head_sha256": authorization["expected_campaign_usage_head_sha256"],
        "authorization_window": {
            "launch_not_before": authorization["launch_not_before"],
            "launch_not_after": authorization["launch_not_after"],
            "parent_valid_not_before": parent["valid_not_before"],
            "parent_valid_not_after": parent["valid_not_after"],
        },
        "retry_lineage": {"attempt_index": 1, "continuation_authorization": None},
        "matrix_authorization_sha256": authorization["authorization_sha256"],
    }
    if allow_test_fixture:
        normalized.update(
            {
                "execution_mode": SCRIPTED_CODEX_TEST_MODE,
                "test_only": True,
                "live_execution_authorized": False,
                "adapter_version": "codex-scripted-test-v1",
            }
        )
    return normalized, hashlib.sha256(raw).hexdigest()


def _load_producer_authorization(
    root: Path,
    path: Path,
    *,
    require_active_window: bool = True,
    allow_test_fixture: bool = False,
) -> tuple[dict[str, Any], str]:
    relative = _relative_to_root(root, path, "producer_authorization")
    authorization, raw = _load_canonical_json(_contained(root, relative, "producer_authorization", must_exist=True), "producer_authorization")
    if authorization.get("schema") == "daee-smoke-matrix-v1" and authorization.get("kind") == "matrix-authorization":
        return _normalize_live_producer_authorization(
            root,
            authorization,
            raw,
            require_active_window=require_active_window,
            allow_test_fixture=allow_test_fixture,
        )
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


def _recheck_live_authorization(
    root: Path,
    path: Path,
    expected: dict[str, Any],
    expected_sha256: str,
    *,
    allow_test_fixture: bool = False,
) -> None:
    observed, observed_sha256 = _load_producer_authorization(
        root,
        path,
        allow_test_fixture=allow_test_fixture,
    )
    if observed_sha256 != expected_sha256 or observed != expected:
        raise CampaignError("LIVE_AUTHORIZATION_RECHECK_DRIFT")


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
        return {
            "attempt_index": 1,
            "continuation": None,
            "continuation_sha256": None,
            "claim_set_recovery": False,
        }
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
    claim_set_recovery = False
    if claim.exists():
        current_finalizer = _contained(
            root,
            _attempt_finalizer_path(lane, attempt),
            "retry_current_attempt_finalizer",
            must_exist=False,
        )
        if current_finalizer.exists():
            raise CampaignError("RETRY_CONTINUATION_REPLAY")
        current_auth_sha = record_sha256(current_auth)
        claim_set_path = _contained(
            root,
            _attempt_claim_set_path(lane, attempt, current_auth_sha),
            "retry_attempt_claim_set",
            must_exist=False,
        )
        if not claim_set_path.is_file():
            raise CampaignError("RETRY_CONTINUATION_REPLAY")
        try:
            claim_set, claim_set_raw = _load_canonical_json(
                claim_set_path,
                "retry_attempt_claim_set",
            )
            retained_claim, retained_claim_raw = _load_canonical_json(
                claim,
                "retry_continuation_claim",
            )
        except CampaignError as exc:
            raise CampaignError(f"RETRY_CONTINUATION_CLAIM_SET_RECOVERY_INVALID: {exc}") from exc
        expected_continuation_claim = {
            "schema": "reviewed-campaign-retry-continuation-claim-v1",
            "authorization_id": authorization["authorization_id"],
            "authorization_sha256": authorization_sha,
            "candidate_id": current_auth["candidate_id"],
            "lane": lane,
            "prior_batch_id": authorization["prior_batch_id"],
            "next_batch_id": current_auth["cycle_or_review_batch_id"],
            "next_attempt_index": attempt,
            "successor_cohort_authorization_sha256": current_auth_sha,
            "status": "CONSUMED",
            "one_use": True,
        }
        projections = claim_set.get("claim_projections")
        continuation_projection = (
            next(
                (
                    row
                    for row in projections
                    if isinstance(row, dict) and row.get("role") == "retry_continuation"
                ),
                None,
            )
            if isinstance(projections, list)
            else None
        )
        if (
            claim_set_raw != canonical_bytes(claim_set)
            or retained_claim_raw != canonical_bytes(retained_claim)
            or claim_set.get("schema") != "reviewed-campaign-attempt-claim-set-v1"
            or claim_set.get("lane") != lane
            or claim_set.get("attempt_index") != attempt
            or claim_set.get("candidate_id") != current_auth["candidate_id"]
            or claim_set.get("cycle_or_review_batch_id") != current_auth["cycle_or_review_batch_id"]
            or claim_set.get("authorization_sha256") != current_auth_sha
            or claim_set.get("status") != "CONSUMED"
            or claim_set.get("one_use") is not True
            or not isinstance(continuation_projection, dict)
            or continuation_projection.get("path") != expected_claim_path
            or continuation_projection.get("payload") != expected_continuation_claim
            or continuation_projection.get("payload_sha256")
            != record_sha256(expected_continuation_claim)
            or retained_claim != expected_continuation_claim
        ):
            raise CampaignError("RETRY_CONTINUATION_CLAIM_SET_RECOVERY_INVALID")
        claim_set_recovery = True
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
        "claim_set_recovery": claim_set_recovery,
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
    optional_refs = {
        "candidate_readiness": identity.get("candidate_readiness"),
        "source_commit_receipt": candidate.get("ci_receipt"),
    }
    for role, ref in optional_refs.items():
        if ref is not None:
            if not isinstance(ref, dict) or set(ref) != {"path", "byte_count", "sha256"}:
                raise CampaignError(f"CANDIDATE_MATURITY_{role.upper()}_REF")
            refs[role] = ref
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
    if allow_test_fixture and _production_live_mode(auth):
        raise CampaignError("TEST_FIXTURE_LIVE_AUTHORITY_FORBIDDEN")
    readiness_ref = auth.get("candidate_readiness", auth["candidate_maturity"])
    source_receipt_ref = auth.get("source_commit_receipt", auth["source_preflight"])
    readiness, _readiness_path, readiness_sha = _load_ref(root, readiness_ref, "candidate_readiness")
    candidate, _candidate_path, candidate_sha = _load_ref(root, auth["candidate_maturity"], "candidate_maturity")
    package, _package_path, package_sha = _load_ref(root, auth["package_record"], "package_record")
    source_receipt, _source_receipt_path, source_receipt_sha = _load_ref(root, source_receipt_ref, "source_commit_receipt")
    preflight, _preflight_path, preflight_sha = _load_ref(root, auth["source_preflight"], "source_preflight")
    registry, _registry_path, registry_sha = _load_ref(root, auth["registry"], "registry")
    protocol, _protocol_path, protocol_sha = _load_ref(root, auth["review_protocol"], "review_protocol")
    execution_tooling: dict[str, Any] | None = None
    if _producer_capture_mode(auth):
        try:
            if allow_test_fixture:
                execution_tooling, _tooling_path, _tooling_sha = _load_ref(
                    root,
                    auth.get("execution_tooling_manifest"),
                    "execution_tooling_manifest",
                )
                execution_tooling = tooling_manifest.validate_execution_tooling_manifest_identity(
                    manifest=execution_tooling,
                    expected_source_commit=auth["source_commit"],
                )
            else:
                execution_tooling = tooling_manifest.load_and_verify_execution_tooling_manifest(
                    root=root,
                    manifest_ref=auth.get("execution_tooling_manifest"),
                    expected_source_commit=auth["source_commit"],
                )
        except tooling_manifest.ExecutionToolingManifestError as exc:
            raise CampaignError(f"EXECUTION_TOOLING_MANIFEST_INVALID: {exc}") from exc
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
        for role in ("candidate_readiness", "package_record", "source_commit_receipt", "source_preflight", "registry", "review_protocol"):
            if role not in mature or auth[role] != mature[role]:
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
    if _producer_capture_mode(auth):
        readiness_state = readiness.get("candidate_state") if allow_test_fixture else readiness.get("status")
        readiness_claim = readiness.get("claim_status")
        if (
            readiness.get("candidate_id") != auth["candidate_id"]
            or readiness_state != "READY_UNUSED"
            or auth.get("candidate_state_at_authorization") != "READY_UNUSED"
            or auth.get("candidate_claim_status_at_authorization") != "UNCLAIMED"
        ):
            raise CampaignError("CANDIDATE_READINESS_AUTHORIZATION_BINDING")
        if allow_test_fixture:
            if readiness_claim != "UNCLAIMED":
                raise CampaignError("CANDIDATE_READINESS_AUTHORIZATION_BINDING")
        elif candidate.get("candidate", {}).get("claim_status") != "UNCLAIMED":
            raise CampaignError("CANDIDATE_READINESS_AUTHORIZATION_BINDING")
        receipt_commit = source_receipt.get("source_commit")
        if receipt_commit is None and isinstance(source_receipt.get("source"), dict):
            receipt_commit = source_receipt["source"].get("commit_sha")
        if receipt_commit != auth["source_commit"]:
            raise CampaignError("SOURCE_COMMIT_RECEIPT_AUTHORIZATION_BINDING")
        package_archive_sha = package.get("package_sha256")
        if package_archive_sha is None and isinstance(package.get("archive"), dict):
            package_archive_sha = package["archive"].get("sha256")
        package_tree_sha = package.get("package_tree_sha256", package.get("extracted_tree_sha256"))
        if (
            package_archive_sha != auth.get("package_sha256")
            or package_tree_sha != auth.get("package_tree_sha256")
            or readiness.get("package_sha256", readiness.get("archive_sha256")) != auth.get("package_sha256")
            or readiness.get("package_tree_sha256", readiness.get("extracted_tree_sha256")) != auth.get("package_tree_sha256")
        ):
            raise CampaignError("PACKAGE_AUTHORIZATION_BINDING")
        cases = registry.get("cases")
        exact_case_inputs = (
            [
                {
                    "case_id": row.get("case_id"),
                    "input_sha256": str(row.get("raw_sha256")).lower(),
                }
                for row in cases
            ]
            if isinstance(cases, list) else None
        )
        if auth.get("case_inputs") != exact_case_inputs or [row["case_id"] for row in auth["case_inputs"]] != case_ids:
            raise CampaignError("CANONICAL_CASE_INPUT_BINDING")
        expected_package_root = f"{package.get('candidate_root')}/{package.get('extracted_root')}"
        if auth.get("candidate_package_root") != expected_package_root:
            raise CampaignError("CANDIDATE_PACKAGE_ROOT_BINDING")
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
        "readiness": readiness,
        "readiness_sha256": readiness_sha,
        "package": package,
        "package_sha256": package_sha,
        "source_receipt": source_receipt,
        "source_receipt_sha256": source_receipt_sha,
        "preflight": preflight,
        "preflight_sha256": preflight_sha,
        "registry": registry,
        "registry_sha256": registry_sha,
        "protocol": protocol,
        "protocol_sha256": protocol_sha,
        "execution_tooling_manifest": execution_tooling,
        "retry": retry,
    }


def _recheck_execution_tooling_binding(
    root: Path,
    auth: dict[str, Any],
    *,
    allow_test_fixture: bool,
) -> None:
    try:
        if allow_test_fixture:
            value, _path, _sha = _load_ref(
                root,
                auth.get("execution_tooling_manifest"),
                "execution_tooling_manifest",
            )
            tooling_manifest.validate_execution_tooling_manifest_identity(
                manifest=value,
                expected_source_commit=auth["source_commit"],
            )
        else:
            tooling_manifest.load_and_verify_execution_tooling_manifest(
                root=root,
                manifest_ref=auth.get("execution_tooling_manifest"),
                expected_source_commit=auth["source_commit"],
            )
    except tooling_manifest.ExecutionToolingManifestError as exc:
        raise CampaignError(f"EXECUTION_TOOLING_MANIFEST_DRIFT: {exc}") from exc


def _producer_output_contracts(
    auth: dict[str, Any],
    authorization_sha256: str,
    bindings: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Derive the exact pre-dispatch one-call envelope contracts."""

    package = bindings["package"]
    registry = bindings["registry"]
    skill = package.get("skill_root")
    build_manifest = package.get("build_manifest")
    cases = registry.get("cases")
    if (
        not isinstance(skill, dict)
        or SHA256_RE.fullmatch(str(skill.get("sha256", ""))) is None
        or not isinstance(build_manifest, dict)
        or SHA256_RE.fullmatch(str(build_manifest.get("sha256", ""))) is None
        or not isinstance(cases, list)
    ):
        raise CampaignError("PRODUCER_OUTPUT_CONTRACT_PACKAGE_BINDING")
    candidate_binding = {
        "candidate_id": auth["candidate_id"],
        "source_commit": auth["source_commit"],
        "candidate_record_sha256": bindings["package_sha256"],
        "candidate_maturity_sha256": bindings["candidate_sha256"],
        "archive_sha256": auth["package_sha256"],
        "package_tree_sha256": auth["package_tree_sha256"],
        "skill_sha256": skill["sha256"],
        "build_manifest_sha256": build_manifest["sha256"],
    }
    contracts: dict[str, dict[str, Any]] = {}
    for row in cases:
        if not isinstance(row, dict):
            raise CampaignError("PRODUCER_OUTPUT_CONTRACT_CASE_BINDING")
        case_id = row.get("case_id")
        raw_sha256 = row.get("raw_sha256")
        normalized_raw_sha256 = str(raw_sha256).lower()
        raw_bytes = row.get("raw_bytes")
        if (
            not isinstance(case_id, str)
            or not case_id
            or SHA256_RE.fullmatch(normalized_raw_sha256) is None
            or not isinstance(raw_bytes, int)
            or isinstance(raw_bytes, bool)
            or raw_bytes < 1
        ):
            raise CampaignError("PRODUCER_OUTPUT_CONTRACT_CASE_BINDING")
        nonce_seed = canonical_bytes(
            {
                "schema": "daee-single-call-envelope-nonce-seed-v1",
                "authorization_sha256": authorization_sha256,
                "candidate_id": auth["candidate_id"],
                "cycle_id": auth["cycle_or_review_batch_id"],
                "case_id": case_id,
            }
        )
        contracts[case_id] = {
            "schema": "daee-single-call-output-envelope-contract-v1",
            "envelope_nonce": hashlib.sha256(nonce_seed).hexdigest()[:32],
            "case_id": case_id,
            "cycle_id": auth["cycle_or_review_batch_id"],
            "candidate_binding": dict(candidate_binding),
            "input_binding": {"sha256": normalized_raw_sha256, "byte_count": raw_bytes},
            "transport": "daee-single-call-stage-envelope-v1",
            "stage08_owner": "private-source-bound-checker",
        }
    if list(contracts) != auth["case_ids"]:
        raise CampaignError("PRODUCER_OUTPUT_CONTRACT_CASE_ORDER")
    return contracts


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


def _live_producer_reservation_bindings(
    auth: dict[str, Any],
    auth_sha: str,
) -> list[dict[str, object]]:
    if not _producer_capture_mode(auth):
        raise CampaignError("LIVE_PRODUCER_RESERVATION_BINDINGS_REQUIRED")
    case_inputs = auth.get("case_inputs")
    provider_settings = auth.get("provider_settings")
    window = auth.get("authorization_window")
    if (
        not isinstance(case_inputs, list)
        or len(case_inputs) != 5
        or not isinstance(provider_settings, dict)
        or provider_settings.get("observation_protocol") != PRODUCER_OBSERVATION_PROTOCOL
        or not isinstance(window, dict)
    ):
        raise CampaignError("LIVE_PRODUCER_RESERVATION_BINDING_INVALID")
    timeout = provider_settings.get("command_timeout_seconds")
    deadline = window.get("launch_not_after")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise CampaignError("LIVE_PRODUCER_RESERVATION_TIMEOUT_INVALID")
    _parse_utc(deadline, "producer_cohort_deadline")
    shared = {
        "schema": "campaign-usage-reservation-member-v1",
        "campaign_authorization_sha256": auth["campaign_authorization_sha256"],
        "matrix_authorization_sha256": auth["matrix_authorization_sha256"],
        "authorization_sha256": auth_sha,
        "candidate_id": auth["candidate_id"],
        "candidate_maturity_sha256": auth["candidate_maturity"]["sha256"],
        "candidate_record_sha256": auth["package_record"]["sha256"],
        "source_commit": auth["source_commit"],
        "package_sha256": auth["package_sha256"],
        "package_tree_sha256": auth["package_tree_sha256"],
        "execution_tooling_manifest_sha256": auth["execution_tooling_manifest"]["sha256"],
        "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
        "cohort": "gpt-producer",
        "model": "gpt-5.5",
        "reasoning_effort": "high",
        "cohort_deadline_utc": deadline,
        "worker_timeout_seconds": timeout,
        "worker_deadline_rule": PRODUCER_WORKER_DEADLINE_RULE,
        "observation_protocol": PRODUCER_OBSERVATION_PROTOCOL,
    }
    rows: list[dict[str, object]] = []
    for index, case_input in enumerate(case_inputs, 1):
        if not isinstance(case_input, dict) or set(case_input) != {"case_id", "input_sha256"}:
            raise CampaignError("LIVE_PRODUCER_RESERVATION_CASE_INPUT_INVALID")
        case_id = case_input.get("case_id")
        input_sha = case_input.get("input_sha256")
        if (
            case_id != auth["case_ids"][index - 1]
            or not isinstance(input_sha, str)
            or SHA256_RE.fullmatch(input_sha) is None
        ):
            raise CampaignError("LIVE_PRODUCER_RESERVATION_CASE_INPUT_INVALID")
        rows.append(
            {
                **shared,
                "reservation_ordinal": index,
                "case_id": case_id,
                "subject_id": f"producer:{case_id}",
                "input_sha256": input_sha,
            }
        )
    return rows


def _execution_custody(
    auth: dict[str, Any],
    auth_sha: str,
    worker: dict[str, str],
    call_contract: dict[str, Any],
    *,
    lane: str,
    packet: dict[str, Any] | None,
    producer_output_contract: dict[str, Any] | None = None,
    producer_capture_bindings: dict[str, Any] | None = None,
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
    if lane == "producer" and _producer_capture_mode(auth):
        if not isinstance(producer_output_contract, dict) or not isinstance(producer_capture_bindings, dict):
            raise CampaignError("EXECUTION_CUSTODY_PRODUCER_CAPTURE_BINDING_REQUIRED")
        usage_reservation_sha = call_contract.get("usage_reservation_sha256")
        if not isinstance(usage_reservation_sha, str) or SHA256_RE.fullmatch(usage_reservation_sha) is None:
            raise CampaignError("EXECUTION_CUSTODY_PRODUCER_USAGE_RESERVATION_REQUIRED")
        envelope["usage_reservation_sha256"] = usage_reservation_sha
        envelope["single_call_output_contract"] = producer_output_contract
        envelope["capture_bindings"] = producer_capture_bindings
        envelope["execution_tooling_manifest"] = copy.deepcopy(auth["execution_tooling_manifest"])
    elif producer_output_contract is not None or producer_capture_bindings is not None:
        raise CampaignError("EXECUTION_CUSTODY_PRODUCER_CAPTURE_BINDING_FORBIDDEN")
    return envelope


def _validate_submit_acknowledgment(
    envelope: dict[str, Any],
    acknowledgment: object,
    *,
    live: bool,
) -> str:
    expected_sha = record_sha256(envelope)
    required = (
        {"handle_id", "execution_custody_sha256", "accepted", "in_flight", "acknowledgment_origin", "started_at", "host_invocation_id"}
        if live else {"handle_id", "execution_custody_sha256", "accepted", "in_flight"}
    )
    if not isinstance(acknowledgment, dict) or set(acknowledgment) != required:
        raise CampaignError("EXECUTION_CUSTODY_SUBMIT_ACK_SHAPE")
    if acknowledgment.get("execution_custody_sha256") != expected_sha:
        raise CampaignError("EXECUTION_CUSTODY_SUBMIT_ACK_BINDING")
    if live:
        if acknowledgment.get("accepted") is not None or acknowledgment.get("in_flight") is not True or acknowledgment.get("acknowledgment_origin") != "ADAPTER_IN_FLIGHT":
            raise CampaignError("EXECUTION_CUSTODY_SUBMIT_ACK_STATE")
        if not isinstance(acknowledgment.get("started_at"), str) or not isinstance(acknowledgment.get("host_invocation_id"), str):
            raise CampaignError("EXECUTION_CUSTODY_SUBMIT_ACK_STATE")
    elif acknowledgment.get("accepted") is not True or acknowledgment.get("in_flight") is not True:
        raise CampaignError("EXECUTION_CUSTODY_SUBMIT_ACK_STATE")
    handle = acknowledgment.get("handle_id")
    if not isinstance(handle, str) or not handle:
        raise CampaignError("EXECUTION_CUSTODY_SUBMIT_HANDLE")
    return handle


def _submit_with_custody(adapter: ProviderAdapter, envelope: dict[str, Any], *, live: bool = False) -> str:
    return _validate_submit_acknowledgment(envelope, adapter.submit(envelope), live=live)


def _submit_tail_with_custody(
    adapter: ProviderAdapter,
    envelopes: list[dict[str, Any]],
) -> list[str]:
    if len(envelopes) != 4:
        raise CampaignError("EXACT_FOUR_CASE_PRODUCER_TAIL_REQUIRED")
    submit_tail = getattr(adapter, "submit_tail", None)
    if not callable(submit_tail):
        raise CampaignError("STRUCTURED_IN_FLIGHT_TAIL_SUBMISSION_UNAVAILABLE")
    acknowledgments = submit_tail(envelopes)
    if not isinstance(acknowledgments, list) or len(acknowledgments) != 4:
        raise CampaignError("EXECUTION_CUSTODY_TAIL_ACK_SHAPE")
    return [
        _validate_submit_acknowledgment(envelope, acknowledgment, live=True)
        for envelope, acknowledgment in zip(envelopes, acknowledgments)
    ]


def _provider_receipt(reservation: dict[str, Any], index: int, result: dict[str, object], execution_custody_sha256: str, *, live: bool = False) -> dict[str, object]:
    contract = reservation["call_contract"][index - 1]
    required_result = (
        {"content_utf8", "capture_status", "capture_evidence", "provider_call_id", "execution_custody_sha256", "execution_custody", "usage", "cost", "started_at", "ended_at", "host_invocation_id", "accepted", "in_flight", "acknowledgment_origin", "raw_event_log", "raw_output", "stderr", "prompt", "credential_residue_scan"}
        if live else {"content_utf8", "structural_status", "provider_call_id", "execution_custody_sha256", "usage", "cost"}
    )
    if not isinstance(result, dict) or "execution_custody_sha256" not in result:
        raise CampaignError("EXECUTION_CUSTODY_OBSERVE_SHAPE")
    if set(result) != required_result or not isinstance(result.get("content_utf8"), str):
        raise CampaignError("PRODUCER_STRUCTURAL_RESULT_INVALID")
    if live and result.get("capture_status") != "CAPTURED":
        raise CampaignError("PRODUCER_CAPTURE_RESULT_INVALID")
    if not live and result.get("structural_status") != "PASS":
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
        "started_at": result["started_at"] if live else "2026-07-12T00:00:00Z",
        "ended_at": result["ended_at"] if live else "2026-07-12T00:00:01Z",
        "host_invocation_id": result["host_invocation_id"] if live else f"task6-{reservation['cycle_or_review_batch_id']}-{index:02d}",
        "accepted": result["accepted"] if live else True,
        "in_flight": result["in_flight"] if live else True,
        "status": "COMPLETED",
        "unknown_kind": None,
        "acknowledgment_origin": result["acknowledgment_origin"] if live else "BOTH",
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


LIVE_COST_UNAVAILABLE = {
    "unit": "usd",
    "value": "unknown",
    "status": "UNAVAILABLE",
    "reason": "provider-cost-not-present-in-retained-jsonl",
    "source": "codex-cli-jsonl-v1",
}


def _live_partial_observations(
    reservation: dict[str, Any],
    attempt_states: object,
    completed_receipts: list[dict[str, object]],
    completed_results: list[dict[str, object]],
    execution_custodies: list[dict[str, Any]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if (
        not isinstance(attempt_states, list)
        or len(attempt_states) != 5
        or len(execution_custodies) != 5
    ):
        raise CampaignError("LIVE_ATTEMPT_STATE_INVENTORY_INVALID")
    completed_by_id = {row.get("call_id"): row for row in completed_receipts if isinstance(row, dict)}
    result_by_case = {row.get("case_id"): row for row in completed_results if isinstance(row, dict)}
    rows: list[dict[str, object]] = []
    results: list[dict[str, object]] = []
    observed_cases: list[str] = []
    for index, (contract, state_row, execution_custody) in enumerate(
        zip(reservation["call_contract"], attempt_states, execution_custodies),
        1,
    ):
        if not isinstance(state_row, dict) or set(state_row) != {"case_id", "state", "started_at", "ended_at", "host_invocation_id", "result"}:
            raise CampaignError("LIVE_ATTEMPT_STATE_INVENTORY_INVALID")
        case_id = state_row.get("case_id")
        if (
            not isinstance(case_id, str)
            or not case_id
            or contract.get("case_id") != case_id
            or not isinstance(execution_custody, dict)
        ):
            raise CampaignError("LIVE_ATTEMPT_STATE_INVENTORY_INVALID")
        observed_cases.append(case_id)
        call_id = f"{reservation['cycle_or_review_batch_id']}:call-{index:02d}"
        if state_row.get("state") == "COMPLETED":
            retained_result = state_row.get("result")
            reconstructed = _provider_receipt(
                reservation,
                index,
                retained_result,
                record_sha256(execution_custody),
                live=True,
            )
            completed = completed_by_id.get(call_id)
            if completed is not None and completed != reconstructed:
                raise CampaignError("LIVE_COMPLETED_RECEIPT_RECONSTRUCTION_MISMATCH")
            receipt = completed or reconstructed
            rows.append(receipt)
            projected = result_by_case.get(case_id)
            if projected is None:
                assert isinstance(retained_result, dict)
                projected = {
                    "case_id": case_id,
                    "capture_status": "CAPTURED",
                    "structural_status": "UNVERIFIED",
                    "projection_status": "FAILED",
                    "output": copy.deepcopy(retained_result["raw_output"]),
                    "capture_evidence": copy.deepcopy(retained_result["capture_evidence"]),
                    "provider_receipt": None,
                    "provider_receipt_sha256": record_sha256(receipt),
                }
            elif projected.get("provider_receipt_sha256") != record_sha256(receipt):
                raise CampaignError("LIVE_COMPLETED_RESULT_RECEIPT_RECONSTRUCTION_MISMATCH")
            results.append(projected)
            continue
        common = {
            "call_id": call_id,
            **contract,
            "cycle_or_review_batch_id": reservation["cycle_or_review_batch_id"],
        }
        if state_row.get("state") == "NOT_SUBMITTED":
            rows.append(
                {
                    **common, "started_at": None, "ended_at": None, "host_invocation_id": None,
                    "accepted": False, "in_flight": False, "status": "NOT_DISPATCHED",
                    "unknown_kind": None, "acknowledgment_origin": "NONE",
                    "terminal_transport_status": "NOT_STARTED", "provider_call_id": None,
                    "usage": {"status": "UNAVAILABLE"}, "cost": {"unit": "usd", "value": "0"},
                }
            )
        elif state_row.get("state") in {"DISPATCH_UNKNOWN", "SUBMITTING", "PENDING_STRUCTURED_ADMISSION"}:
            rows.append(
                {
                    **common, "started_at": None, "ended_at": None, "host_invocation_id": None,
                    "accepted": None, "in_flight": None, "status": "UNKNOWN",
                    "unknown_kind": "DISPATCH_UNKNOWN", "acknowledgment_origin": "NONE",
                    "terminal_transport_status": "UNKNOWN", "provider_call_id": None,
                    "usage": {"status": "UNAVAILABLE"}, "cost": dict(LIVE_COST_UNAVAILABLE),
                }
            )
        elif state_row.get("state") == "OUTCOME_UNKNOWN":
            started_at = state_row.get("started_at")
            ended_at = state_row.get("ended_at")
            host_invocation_id = state_row.get("host_invocation_id")
            if not all(isinstance(value, str) and value for value in (started_at, ended_at, host_invocation_id)):
                raise CampaignError("LIVE_OUTCOME_UNKNOWN_LACKS_POSITIVE_DISPATCH_EVIDENCE")
            rows.append(
                {
                    **common, "started_at": started_at, "ended_at": ended_at,
                    "host_invocation_id": host_invocation_id, "accepted": None,
                    "in_flight": False, "status": "UNKNOWN", "unknown_kind": "OUTCOME_UNKNOWN",
                    "acknowledgment_origin": "ADAPTER_IN_FLIGHT", "terminal_transport_status": "UNKNOWN",
                    "provider_call_id": None, "usage": {"status": "UNAVAILABLE"},
                    "cost": dict(LIVE_COST_UNAVAILABLE),
                }
            )
        else:
            raise CampaignError("LIVE_ATTEMPT_STATE_INVENTORY_INVALID")
    if len(set(observed_cases)) != 5:
        raise CampaignError("LIVE_ATTEMPT_STATE_INVENTORY_INVALID")
    return rows, results


def _finalize_provider_failure(
    root: Path,
    usage_root: Path,
    reservation: dict[str, Any],
    auth: dict[str, Any],
    auth_sha: str,
    *,
    handles: list[str],
    lane: str,
    error: BaseException,
    attempt_index: int,
    claims: dict[str, Any],
    packet_disclosure: dict[str, object] | None,
    failure_phase: str = "provider-execution",
    observed_results: list[dict[str, object]] | None = None,
    completed_receipts: list[dict[str, object]] | None = None,
    live_attempt_states: object = None,
    execution_custodies: list[dict[str, Any]] | None = None,
) -> None:
    live = _producer_capture_mode(auth)
    if live:
        receipts, retained_results = _live_partial_observations(
            reservation,
            live_attempt_states,
            completed_receipts or [],
            observed_results or [],
            execution_custodies or [],
        )
        completed = sum(row["status"] == "COMPLETED" for row in receipts)
        unknown = sum(row["status"] == "UNKNOWN" for row in receipts)
        not_dispatched = sum(row["status"] == "NOT_DISPATCHED" for row in receipts)
        measured_cost = dict(LIVE_COST_UNAVAILABLE) if completed or unknown else {"unit": "usd", "value": "0"}
        if completed == 5 and unknown == 0 and not_dispatched == 0:
            classification = "OBSERVED"
        elif any(row["unknown_kind"] == "OUTCOME_UNKNOWN" for row in receipts):
            classification = "OUTCOME_UNKNOWN"
        else:
            classification = "DISPATCH_UNKNOWN"
    else:
        positive = len(handles) == 5
        receipts = _unknown_receipts(reservation, positive_dispatch_evidence=positive, handles=handles)
        retained_results = observed_results or []
        completed, unknown, not_dispatched = 0, 5, 0
        measured_cost = {"unit": "usd", "value": "unknown"}
        classification = "OUTCOME_UNKNOWN" if positive else "DISPATCH_UNKNOWN"
    terminal = settle(
        usage_root,
        reservation["transaction_sha256"],
        completed=completed,
        failed=0,
        cancelled=0,
        not_dispatched=not_dispatched,
        unknown=unknown,
        provider_usage_receipts=receipts,
        measured_cost=measured_cost,
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
        dispatch_classification=classification,
        candidate_status=(
            "CONSUMED_OBSERVED"
            if lane != "producer" or classification == "OBSERVED"
            else "CONSUMED_DISPATCH_UNKNOWN"
        ),
        reservation_sha256=reservation["transaction_sha256"],
        settlement_sha256=terminal["transaction_sha256"],
        error=error,
        resumable_retry=False,
        failure_phase=failure_phase,
        observed_results=retained_results,
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
            measured_cost=dict(LIVE_COST_UNAVAILABLE) if _producer_capture_mode(auth) else {"unit": "usd", "value": "0"},
            candidate_id=auth["candidate_id"],
            authorization_sha256=auth_sha,
        )
    elif not snapshot["open_reservations"]:
        terminal_sha = snapshot.get("last_transaction_sha256")
        if not isinstance(terminal_sha, str):
            raise CampaignError("OBSERVED_FAILURE_TERMINAL_MISSING")
        terminal_path = usage_root / "transactions" / f"{terminal_sha}.json"
        terminal, _raw = _load_canonical_json(terminal_path, "observed_failure_terminal")
        if terminal.get("kind") not in {"settlement","settlement-set"} or terminal.get("reservation_transaction_sha256") != reservation_sha:
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
    """Run one exact producer cohort; live mode stops at immutable raw capture."""
    root = Path(os.path.abspath(custody_root))
    capability = _probe_producer_capability(adapter)  # Must precede authorization reads/claims.
    if allow_test_fixture and (
        capability.get("adapter_kind") == "codex-live"
        or capability.get("paid_provider_reachable") is not False
        or capability.get("test_only") is not True
        or capability.get("live_execution_authorized") is not False
    ):
        raise CampaignError("TEST_FIXTURE_PAID_PROVIDER_FORBIDDEN")
    _validate_fault_injection(fault_at, allow_test_fixture)
    auth, auth_sha = _load_producer_authorization(
        root,
        authorization_path,
        allow_test_fixture=allow_test_fixture,
    )
    live = _producer_capture_mode(auth)
    if live:
        expected_adapter_kind = (
            "codex-live"
            if _production_live_mode(auth)
            else "codex-scripted-test-no-provider"
        )
        if capability.get("adapter_kind") != expected_adapter_kind:
            raise CampaignError("LIVE_PROVIDER_CAPABILITY_REQUIRED")
        if (
            capability.get("adapter_version") != auth.get("adapter_version")
            or capability.get("host_application_version") != auth.get("host_application_version")
            or capability.get("codex_executable_sha256") != auth.get("codex_executable_sha256")
        ):
            raise CampaignError("LIVE_PROVIDER_IDENTITY_MISMATCH")
        configured_timeout = getattr(adapter, "configured_command_timeout_seconds", None)
        try:
            actual_timeout = configured_timeout() if callable(configured_timeout) else None
        except Exception as exc:
            raise CampaignError("LIVE_PROVIDER_COMMAND_TIMEOUT_UNAVAILABLE") from exc
        authorized_timeout = auth.get("provider_settings", {}).get("command_timeout_seconds")
        if actual_timeout != authorized_timeout:
            raise CampaignError("LIVE_PROVIDER_COMMAND_TIMEOUT_MISMATCH")
    elif capability.get("adapter_kind") != "deterministic-fake-no-dispatch":
        raise CampaignError("LIVE_PROVIDER_UNSUPPORTED: fake authorization cannot reach a live adapter")
    bindings = _validate_common_bindings(root, auth, allow_test_fixture=allow_test_fixture)
    producer_output_contracts: dict[str, dict[str, Any]] = {}
    producer_capture_bindings: dict[str, dict[str, Any]] = {}
    if live:
        producer_output_contracts = _producer_output_contracts(auth, auth_sha, bindings)
        bindings["producer_output_contracts"] = producer_output_contracts
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
        "execution_mode": auth["execution_mode"],
        "live_dispatch": _production_live_mode(auth),
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
    if live:
        expected_sequence = auth["expected_campaign_usage_sequence"]
        expected_head = auth["expected_campaign_usage_head_sha256"]
        snapshot = head_snapshot(usage_root)
        if snapshot["sequence"] != expected_sequence or snapshot["head_sha256"] != expected_head:
            raise CampaignError("EXPECTED_CAMPAIGN_USAGE_HEAD_DRIFT")
    if live and auth.get("observation_finalizer_path") != _attempt_finalizer_path("producer", attempt_index):
        raise CampaignError("LIVE_OBSERVATION_FINALIZER_LOCATOR_BINDING")
    if live:
        if auth.get("provider_settings", {}).get("observation_protocol") != PRODUCER_OBSERVATION_PROTOCOL:
            raise CampaignError("LIVE_PROVIDER_CONCURRENT_OBSERVATION_PROTOCOL")
        if not callable(getattr(adapter, "observe_many", None)):
            raise CampaignError("LIVE_PROVIDER_CONCURRENT_OBSERVATION_UNAVAILABLE")
        prepare = getattr(adapter, "prepare", None)
        if not callable(prepare):
            raise CampaignError("LIVE_PROVIDER_PREPARATION_UNAVAILABLE")
        try:
            prepare(auth, bindings, allow_test_fixture=allow_test_fixture)
        except Exception as exc:
            raise CampaignError(f"LIVE_PROVIDER_PREPARATION_FAILED: {exc}") from exc
        prepared_bindings = getattr(adapter, "execution_bindings", None)
        if (
            not callable(getattr(adapter, "attempt_states", None))
            or not callable(getattr(adapter, "abort_all", None))
            or not callable(prepared_bindings)
        ):
            raise CampaignError("LIVE_PROVIDER_TERMINALIZATION_INTERFACE_UNAVAILABLE")
        try:
            producer_capture_bindings = prepared_bindings()
        except Exception as exc:
            raise CampaignError(f"LIVE_PROVIDER_CAPTURE_BINDINGS_UNAVAILABLE: {exc}") from exc
        if list(producer_capture_bindings) != auth["case_ids"]:
            raise CampaignError("LIVE_PROVIDER_CAPTURE_BINDINGS_CASE_ORDER")
        _recheck_live_authorization(
            root,
            authorization_path,
            auth,
            auth_sha,
            allow_test_fixture=allow_test_fixture,
        )
        _recheck_execution_tooling_binding(root, auth, allow_test_fixture=allow_test_fixture)
    try:
        claims = _consume_attempt_claims(
            root,
            auth,
            auth_sha,
            bindings,
            lane="producer",
            authorization_claim=auth_claim,
        )
    except _AttemptClaimSetError as error:
        if live:
            abort = getattr(adapter, "abort_all", None)
            if callable(abort):
                try:
                    abort()
                except Exception as abort_exc:
                    raise CampaignError(
                        f"{error}; OWNED_PROCESS_TEARDOWN_FAILED: {abort_exc}"
                    ) from error
        _finalize_no_dispatch_failure(
            root,
            usage_root,
            auth,
            auth_sha,
            lane="producer",
            attempt_index=attempt_index,
            claims=error.claims,
            packet_disclosure=None,
            reservation=None,
            error=error,
            failure_phase="pre-dispatch",
        )
        raise
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
    envelopes: list[dict[str, Any]] = []
    completion_ref: dict[str, object] | None = None
    failure_phase = "reservation"
    try:
        snapshot = head_snapshot(usage_root)
        reserve_sequence = auth["expected_campaign_usage_sequence"] if live else snapshot["sequence"]
        reserve_head = auth["expected_campaign_usage_head_sha256"] if live else snapshot["head_sha256"]
        if live:
            _recheck_live_authorization(
                root,
                authorization_path,
                auth,
                auth_sha,
                allow_test_fixture=allow_test_fixture,
            )
            _recheck_execution_tooling_binding(root, auth, allow_test_fixture=allow_test_fixture)
        reservation = reserve(
            usage_root,
            cohort="gpt-producer",
            calls=5,
            expected_sequence=reserve_sequence,
            expected_head_sha256=reserve_head,
            campaign_authorization_sha256=auth["campaign_authorization_sha256"],
            authorization_sha256=auth_sha,
            candidate_id=auth["candidate_id"],
            cycle_or_review_batch_id=auth["cycle_or_review_batch_id"],
            call_subject_ids=subjects,
            producer_reservation_bindings=(
                _live_producer_reservation_bindings(auth, auth_sha) if live else None
            ),
        )
        if fault_at == "reservation-exception-after-open":
            raise CampaignError("INJECTED_RESERVATION_EXCEPTION_AFTER_OPEN")
        failure_phase = "pre-dispatch"
        if fault_at == "after-reservation-before-submit":
            raise CampaignError("INJECTED_PRE_DISPATCH_FAILURE")
        workers = _worker_inventory(auth, "producer")
        envelopes = [
            _execution_custody(
                auth,
                auth_sha,
                worker,
                contract,
                lane="producer",
                packet=None,
                producer_output_contract=producer_output_contracts.get(worker["case_id"]) if live else None,
                producer_capture_bindings=producer_capture_bindings.get(worker["case_id"]) if live else None,
            )
            for worker, contract in zip(workers, reservation["call_contract"])
        ]
        raw_events: list[dict[str, object]] = [
            *({"event": "worker_ready", "worker": row["worker"], "case_id": row["case_id"]} for row in workers),
            {"event": "barrier_release"},
        ]
        if live:
            _recheck_live_authorization(
                root,
                authorization_path,
                auth,
                auth_sha,
                allow_test_fixture=allow_test_fixture,
            )
            _recheck_execution_tooling_binding(root, auth, allow_test_fixture=allow_test_fixture)
        failure_phase = "provider-execution"
        if live:
            first_worker, first_envelope = workers[0], envelopes[0]
            raw_events.append({"event": "request_submit_started", "worker": first_worker["worker"], "case_id": first_worker["case_id"]})
            handles.append(_submit_with_custody(adapter, first_envelope, live=True))
            raw_events.append({"event": "call_entered_in_flight", "worker": first_worker["worker"], "case_id": first_worker["case_id"]})
            for worker in workers[1:]:
                raw_events.append({"event": "request_submit_started", "worker": worker["worker"], "case_id": worker["case_id"]})
            tail_handles = _submit_tail_with_custody(adapter, envelopes[1:])
            handles.extend(tail_handles)
            for worker in workers[1:]:
                raw_events.append({"event": "call_entered_in_flight", "worker": worker["worker"], "case_id": worker["case_id"]})
        else:
            for worker, envelope in zip(workers, envelopes):
                raw_events.append({"event": "request_submit_started", "worker": worker["worker"], "case_id": worker["case_id"]})
                handles.append(_submit_with_custody(adapter, envelope, live=False))
                raw_events.append({"event": "call_entered_in_flight", "worker": worker["worker"], "case_id": worker["case_id"]})
        raw_events.append({"event": "all_five_in_flight"})
        observation_error: BaseException | None = None
        if live:
            observed_batch = adapter.observe_many(handles, envelopes)
            if (
                not isinstance(observed_batch, tuple)
                or len(observed_batch) != 2
                or not isinstance(observed_batch[0], list)
                or len(observed_batch[0]) != 5
                or not (observed_batch[1] is None or isinstance(observed_batch[1], BaseException))
            ):
                raise CampaignError("LIVE_PROVIDER_CONCURRENT_OBSERVATION_SHAPE")
            observed_results, observation_error = observed_batch
        else:
            observed_results = [adapter.observe(handle, envelope) for handle, envelope in zip(handles, envelopes)]
        for index, (worker, envelope, result) in enumerate(zip(workers, envelopes, observed_results), 1):
            if result is None:
                continue
            receipt = _provider_receipt(reservation, index, result, record_sha256(envelope), live=live)
            content = str(result["content_utf8"]).encode("utf-8")
            failure_phase = "result-publication" if live else "provider-execution"
            output_ref = _publish_once_bytes(root, f"producer/results/{worker['case_id']}.txt", content, f"producer_result_{index}")
            if live:
                capture_evidence = result["capture_evidence"]
                receipt_raw = canonical_bytes(receipt)
                receipt_sha = hashlib.sha256(receipt_raw).hexdigest()
                failure_phase = "provider-receipt-publication"
                receipt_ref = _publish_once_bytes(
                    root,
                    f"{auth['provider_receipt_root']}/{receipt_sha}.receipt.json",
                    receipt_raw,
                    f"producer_provider_receipt_{index}",
                )
                results.append({"case_id": worker["case_id"], "capture_status": "CAPTURED", "structural_status": "UNVERIFIED", "output": output_ref, "capture_evidence": capture_evidence, "provider_receipt": receipt_ref, "provider_receipt_sha256": receipt_sha})
            else:
                results.append({"case_id": worker["case_id"], "structural_status": "PASS", "output": output_ref, "provider_receipt_sha256": record_sha256(receipt)})
            receipts.append(receipt)
            raw_events.append({"event": "terminal_result_observed", "worker": worker["worker"], "case_id": worker["case_id"]})
            failure_phase = "provider-execution"
        if observation_error is not None:
            raise observation_error
        if len(results) != 5 or len(receipts) != 5:
            raise CampaignError("LIVE_PROVIDER_CONCURRENT_OBSERVATION_INCOMPLETE")
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
            measured_cost=dict(LIVE_COST_UNAVAILABLE) if live else {"unit": "usd", "value": "0"},
            candidate_id=auth["candidate_id"],
            authorization_sha256=auth_sha,
        )
        if fault_at == "after-settlement":
            failure_phase = fault_at
            raise CampaignError(f"INJECTED_TERMINAL_PHASE_FAILURE: {fault_at}")
        completion: dict[str, Any] = {
            "schema": "reviewed-campaign-producer-completion-v1",
            "status": "PRODUCER_CAPTURE_COMPLETE" if live else "PRODUCER_STRUCTURAL_COMPLETE",
            "execution_mode": auth["execution_mode"],
            "test_only": auth["test_only"],
            "candidate_id": auth["candidate_id"],
            "cycle_id": auth["cycle_or_review_batch_id"],
            "source_commit": auth["source_commit"],
            "registry_sha256": bindings["registry_sha256"],
            "review_protocol": dict(auth["review_protocol"]),
            "review_protocol_sha256": bindings["protocol_sha256"],
            "package_record_sha256": bindings["package_sha256"],
            "candidate_maturity_sha256": bindings["candidate_sha256"],
            "authorization_sha256": auth_sha,
            "reservation_sha256": reservation["transaction_sha256"],
            **(
                {
                    "producer_usage_reservation_sha256s": [
                        row["reservation_sha256"] for row in reservation["reservation_members"]
                    ]
                }
                if live else {}
            ),
            "settlement_sha256": settlement["transaction_sha256"],
            "dispatch_manifest": manifest,
            "results": results,
            "cold_review_authorized": False,
        }
        if live:
            completion.update(
                {
                    "package_sha256": auth["package_sha256"],
                    "package_tree_sha256": auth["package_tree_sha256"],
                }
            )
        failure_phase = "completion-publication"
        completion_ref = _publish_once_json(root, "producer/completion.json", completion, "producer_completion")
        if fault_at == "after-completion":
            failure_phase = fault_at
            raise CampaignError(f"INJECTED_TERMINAL_PHASE_FAILURE: {fault_at}")
        failure_phase = "finalizer-publication"
        _publish_once_json(
            root,
            auth["observation_finalizer_path"] if live else _attempt_finalizer_path("producer", attempt_index),
            {
                "schema": "reviewed-campaign-observation-finalizer-v1",
                "lane": "producer",
                "attempt_index": attempt_index,
                "candidate_id": auth["candidate_id"],
                "cycle_or_review_batch_id": auth["cycle_or_review_batch_id"],
                "authorization_sha256": auth_sha,
                "attempt_claim_set": claims.get("attempt_claim_set"),
                "authorization_claim": claims.get("authorization_claim"),
                "candidate_claim": claims.get("candidate_claim"),
                "continuation_claim": claims.get("continuation_claim"),
                "candidate_status": "CONSUMED_OBSERVED",
                "dispatch_status": "LIVE_RAW_CAPTURE_COMPLETE" if live else "DETERMINISTIC_FAKE_COMPLETE",
                "reservation_sha256": reservation["transaction_sha256"],
                **(
                    {
                        "producer_usage_reservation_sha256s": [
                            row["reservation_sha256"] for row in reservation["reservation_members"]
                        ]
                    }
                    if live else {}
                ),
                "settlement_sha256": settlement["transaction_sha256"],
                "observed_results": results,
                "completion": completion_ref,
                "resulting_usage_head_sha256": head_snapshot(usage_root)["head_sha256"],
                "terminal": True,
            },
            "producer_finalizer",
        )
        return completion
    except BaseException as exc:
        interrupted = isinstance(exc, KeyboardInterrupt)
        live_attempt_states: object = None
        if live:
            abort_error: Exception | None = None
            try:
                abort = getattr(adapter, "abort_all", None)
                if callable(abort):
                    abort()
            except Exception as abort_exc:
                abort_error = abort_exc
            try:
                live_attempt_states = adapter.attempt_states()
            except Exception as state_exc:
                if abort_error is None:
                    abort_error = state_exc
                else:
                    abort_error = CampaignError(f"{abort_error}; ATTEMPT_STATE_READBACK_FAILED: {state_exc}")
            if abort_error is not None:
                exc = CampaignError(f"{exc}; OWNED_PROCESS_TEARDOWN_FAILED: {abort_error}")
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
                    completed_receipts=receipts,
                    live_attempt_states=live_attempt_states,
                    execution_custodies=envelopes,
                )
        except Exception as cleanup_exc:
            raise CampaignError(
                f"TRIGGERING_PHASE_ERROR: {type(exc).__name__}: {exc}; "
                f"CLEANUP_PUBLICATION_ERROR: {type(cleanup_exc).__name__}: {cleanup_exc}"
            ) from exc
        if isinstance(exc, CampaignError) and str(exc).startswith("INJECTED_"):
            raise
        if interrupted:
            raise
        if failure_phase == "reservation":
            raise CampaignError(f"RESERVATION_FAILURE: {exc}") from exc
        if failure_phase == "provider-execution":
            raise CampaignError(f"PROVIDER_EXECUTION_FAILED: {exc}") from exc
        raise CampaignError(f"CAMPAIGN_TERMINALIZATION_FAILED[{failure_phase}]: {exc}") from exc


def revalidate_live_producer_completion_context(
    custody_root: Path,
    authorization_path: Path,
    completion: dict[str, Any],
    *,
    allow_test_fixture: bool = False,
) -> dict[str, Any]:
    """Reopen a historical live completion and return its validated promotion context."""

    root = Path(os.path.abspath(custody_root))
    auth, auth_sha = _load_producer_authorization(
        root,
        authorization_path,
        require_active_window=False,
        allow_test_fixture=allow_test_fixture,
    )
    expected_mode = SCRIPTED_CODEX_TEST_MODE if allow_test_fixture else "LIVE_CODEX"
    if auth.get("execution_mode") != expected_mode:
        raise CampaignError("LIVE_PRODUCER_COMPLETION_REQUIRED")
    if not allow_test_fixture and (
        auth.get("test_only") is not False
        or auth.get("live_execution_authorized") is not True
    ):
        raise CampaignError("LIVE_PRODUCER_AUTHORIZATION_REQUIRED")
    bindings = _validate_common_bindings(
        root,
        auth,
        allow_test_fixture=allow_test_fixture,
    )
    attempt_index = bindings["retry"]["attempt_index"]
    finalizer_path = _contained(
        root,
        auth["observation_finalizer_path"],
        "live_producer_observation_finalizer",
        must_exist=True,
    )
    finalizer, _finalizer_raw = _load_canonical_json(
        finalizer_path,
        "live_producer_observation_finalizer",
    )
    usage_root = _contained(
        root,
        auth["usage_ledger_root"],
        "live_producer_usage_root",
        must_exist=False,
    )
    _validate_success_finalizer(
        root,
        usage_root,
        finalizer,
        auth,
        auth_sha,
        bindings,
        lane="producer",
        attempt_index=attempt_index,
        historical_usage=True,
    )
    retained_path = _contained(
        root,
        "producer/completion.json",
        "live_producer_completion",
        must_exist=True,
    )
    retained, _retained_raw = _load_canonical_json(
        retained_path,
        "live_producer_completion",
    )
    if retained != completion or finalizer.get("completion") != _existing_ref(
        root,
        "producer/completion.json",
        "live_producer_completion",
    ):
        raise CampaignError("LIVE_PRODUCER_COMPLETION_EXACT_READBACK")
    output_contracts = _producer_output_contracts(auth, auth_sha, bindings)
    return {
        "completion": copy.deepcopy(retained),
        "authorization": copy.deepcopy(auth),
        "authorization_sha256": auth_sha,
        "bindings": copy.deepcopy(bindings),
        "producer_output_contracts": copy.deepcopy(output_contracts),
    }


def revalidate_live_producer_completion(
    custody_root: Path,
    authorization_path: Path,
    completion: dict[str, Any],
    *,
    allow_test_fixture: bool = False,
) -> dict[str, Any]:
    """Reopen the live producer auth, evidence, usage, and finalizer chain."""

    context = revalidate_live_producer_completion_context(
        custody_root,
        authorization_path,
        completion,
        allow_test_fixture=allow_test_fixture,
    )
    return context["completion"]


def claim_initial_assessments(
    custody_root: Path,
    producer_completion: dict[str, Any],
    assessments: list[dict[str, object]],
    *,
    claimant: str,
    allow_test_fixture: bool = False,
) -> dict[str, Any]:
    root = Path(os.path.abspath(custody_root))
    if producer_completion.get("schema") != "reviewed-campaign-producer-completion-v1" or producer_completion.get("status") != "PRODUCER_STRUCTURAL_COMPLETE":
        raise CampaignError("PRODUCER_STRUCTURAL_COMPLETION_REQUIRED")
    results = producer_completion.get("results")
    if not isinstance(results, list) or len(results) != 5 or any(
        not isinstance(row, dict)
        or not isinstance(row.get("case_id"), str)
        or not row.get("case_id")
        or row.get("structural_status") != "PASS"
        for row in results
    ):
        raise CampaignError("PRODUCER_STRUCTURAL_COMPLETION_REQUIRED")
    if not isinstance(claimant, str) or HUMAN_ID_RE.fullmatch(claimant) is None:
        raise CampaignError("HUMAN_CLAIMANT_IDENTITY")
    expected_cases = [row["case_id"] for row in results]
    fake_compatibility = (
        allow_test_fixture
        and producer_completion.get("execution_mode") == TEST_EXECUTION_MODE
        and producer_completion.get("test_only") is True
    )
    if fake_compatibility:
        if not isinstance(assessments, list) or len(assessments) != 5:
            raise CampaignError("ASSESSMENT_COUNT: exact five assessments required")
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
            "compatibility_mode": "DETERMINISTIC_FAKE_HASH_ONLY",
        }
    else:
        if not isinstance(assessments, list) or any(not isinstance(row, dict) or set(row) != {"case_id", "assessment"} for row in assessments):
            raise CampaignError("ASSESSMENT_ARTIFACT_REQUIRED")
        try:
            validated = validate_initial_assessment_set(root, producer_completion, assessments, claimant=claimant)
        except AssessmentBarrierError as exc:
            raise CampaignError(str(exc)) from exc
        claim = {
            "schema": "reviewed-campaign-initial-assessment-claim-v2",
            "status": "ALL_FIVE_INITIAL_ASSESSMENTS_HASH_CLAIMED",
            **validated,
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
    *,
    allow_test_fixture: bool = False,
) -> list[dict[str, Any]]:
    if assessment.get("schema") == "reviewed-campaign-initial-assessment-claim-v2":
        try:
            revalidate_assessment_claim(root, producer, assessment)
        except AssessmentBarrierError as exc:
            raise CampaignError(str(exc)) from exc
    else:
        fake_compatibility = (
            allow_test_fixture
            and auth.get("execution_mode") == TEST_EXECUTION_MODE
            and auth.get("test_only") is True
            and producer.get("execution_mode") == TEST_EXECUTION_MODE
            and producer.get("test_only") is True
            and assessment.get("schema") == "reviewed-campaign-initial-assessment-claim-v1"
            and assessment.get("compatibility_mode") == "DETERMINISTIC_FAKE_HASH_ONLY"
        )
        if not fake_compatibility:
            raise CampaignError("ASSESSMENT_CLAIM_REQUIRED_BEFORE_DISCLOSURE")
    if assessment.get("status") != "ALL_FIVE_INITIAL_ASSESSMENTS_HASH_CLAIMED" or assessment.get("count") != 5 or assessment.get("cold_review_disclosure_permitted") is not True:
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
    packets = _validate_packet_set(root, auth, producer, assessment, allow_test_fixture=allow_test_fixture)
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
    try:
        claims = _consume_attempt_claims(
            root,
            auth,
            auth_sha,
            bindings,
            lane="cold-review",
            authorization_claim=auth_claim,
        )
    except _AttemptClaimSetError as error:
        _finalize_no_dispatch_failure(
            root,
            usage_root,
            auth,
            auth_sha,
            lane="cold-review",
            attempt_index=attempt_index,
            claims=error.claims,
            packet_disclosure=None,
            reservation=None,
            error=error,
            failure_phase="pre-dispatch",
        )
        raise
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
                "attempt_claim_set": claims.get("attempt_claim_set"),
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
