#!/usr/bin/env python3
"""Shared secret-safe contract for retained credential-residue scan records."""
from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any


PASS_V1_SCHEMA = "reviewed-campaign-credential-residue-scan-v1"
PASS_V2_SCHEMA = "reviewed-campaign-credential-residue-scan-v2"
PASS_V3_SCHEMA = "reviewed-campaign-credential-residue-scan-v3"
MANAGED_AUTH_SCAN_MODE = "MANAGED_AUTH_STRUCTURAL_MARKERS"
MANAGED_AUTH_MARKER_FAMILIES = (
    "credential-json-keys",
    "authorization-bearer",
    "compact-jwt",
    "openai-key-prefix",
)
ENCODING_FORMS = ("utf-8", "utf-16-le", "utf-16-be")
MANAGED_AUTH_PASS_CLASSIFICATIONS = (
    "NO_CREDENTIAL_MARKERS",
    "EXPECTED_TRANSPORT_STRUCTURE",
)
MANAGED_AUTH_FAILURE_CLASSIFICATIONS = (
    "CREDENTIAL_VALUE_RESIDUE",
    "AMBIGUOUS_OR_UNAVAILABLE",
)
SAFE_CARRIER_ROLES = ("raw_event_log", "stderr", "raw_output")
SAFE_CARRIER_OUTCOMES = (
    "RETAINED_SECRET_SAFE",
    "SOURCE_ABSENT",
    "UNSAFE_OR_UNPROVEN",
    "PUBLICATION_FAILED",
)
_MANAGED_AUTH_SENSITIVE_KEYS = frozenset(
    {"access_token", "refresh_token", "id_token", "agent_identity", "openai_api_key"}
)
_MANAGED_AUTH_REDACTED_VALUES = frozenset(
    {"", "[redacted]", "<redacted>", "redacted"}
)
_COMPACT_JWT_RE = re.compile(
    r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"
)
_OPENAI_KEY_RE = re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{16,}")
_AUTHORIZATION_BEARER_RE = re.compile(
    r"(?i)\bauthorization\b[\"']?\s*[:=]\s*[\"']?\s*bearer"
    r"(?:\s+[\"']?([^\s\"'\\,}]+)[\"']?)?"
)
_QUOTED_SENSITIVE_KEY_RE = re.compile(
    r'[\"\'](?:access_token|refresh_token|id_token|agent_identity|OPENAI_API_KEY)[\"\']\s*:',
    re.IGNORECASE,
)
_JSON_KEY_TOKEN_RE = re.compile(
    r'\"((?:[^\"\\]|\\(?:[\"\\/bfnrt]|u[0-9a-fA-F]{4}))*)\"\s*:'
)
_SINGLE_QUOTED_KEY_TOKEN_RE = re.compile(
    r"'((?:[^'\\]|\\u[0-9a-fA-F]{4})*)'\s*:"
)


class _SensitiveJsonKeyAmbiguity(ValueError):
    pass


class CredentialResidueError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        semantic_classification: str = "CREDENTIAL_VALUE_RESIDUE",
        marker_families: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.semantic_classification = semantic_classification
        self.marker_families = marker_families


class ManagedCredentialScanAmbiguousError(RuntimeError):
    def __init__(self, marker_families: tuple[str, ...]) -> None:
        super().__init__("managed credential structure could not be classified safely")
        self.semantic_classification = "AMBIGUOUS_OR_UNAVAILABLE"
        self.marker_families = marker_families


def _ordered_managed_auth_families(families: set[str]) -> tuple[str, ...]:
    return tuple(family for family in MANAGED_AUTH_MARKER_FAMILIES if family in families)


def _managed_auth_text_candidates(raw: bytes) -> list[str]:
    candidates: list[str] = []
    encodings = ["utf-8"]
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or raw.count(b"\x00") >= max(
        1, len(raw) // 8
    ):
        encodings.extend(("utf-16-le", "utf-16-be"))
    for encoding in encodings:
        try:
            decoded = raw.decode(encoding, errors="strict").lstrip("\ufeff")
        except UnicodeDecodeError:
            continue
        if decoded not in candidates:
            candidates.append(decoded)
    return candidates


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    sensitive_keys: set[str] = set()
    for key, item in pairs:
        normalized = key.casefold()
        if key in value:
            if normalized in _MANAGED_AUTH_SENSITIVE_KEYS:
                raise _SensitiveJsonKeyAmbiguity(
                    "duplicate sensitive JSON key in managed credential scan input"
                )
            raise ValueError("duplicate JSON key in managed credential scan input")
        if normalized in _MANAGED_AUTH_SENSITIVE_KEYS:
            if normalized in sensitive_keys:
                raise _SensitiveJsonKeyAmbiguity(
                    "aliased sensitive JSON key in managed credential scan input"
                )
            sensitive_keys.add(normalized)
        value[key] = item
    return value


def _managed_auth_json_documents(text: str) -> list[Any] | None:
    stripped = text.strip()
    if not stripped:
        return []
    try:
        return [json.loads(stripped, object_pairs_hook=_strict_json_object)]
    except _SensitiveJsonKeyAmbiguity:
        raise
    except (json.JSONDecodeError, ValueError):
        documents: list[Any] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                documents.append(
                    json.loads(line, object_pairs_hook=_strict_json_object)
                )
            except _SensitiveJsonKeyAmbiguity:
                raise
            except (json.JSONDecodeError, ValueError):
                return None
        return documents


def _has_semantic_sensitive_json_key(text: str) -> bool:
    candidates = (
        (match.group(1), False) for match in _JSON_KEY_TOKEN_RE.finditer(text)
    )
    single_quoted = (
        (match.group(1), True)
        for match in _SINGLE_QUOTED_KEY_TOKEN_RE.finditer(text)
    )
    for token, single_quote in (*candidates, *single_quoted):
        try:
            encoded = token.replace('"', '\\"') if single_quote else token
            key = json.loads(f'\"{encoded}\"')
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(key, str) and key.casefold() in _MANAGED_AUTH_SENSITIVE_KEYS:
            return True
    return False


def _json_string_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_json_string_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_json_string_values(item))
    elif isinstance(value, str):
        values.append(value)
    return values


def _record_credential_value_signatures(
    text: str,
    families: set[str],
    value_families: set[str],
) -> set[str]:
    structural_families: set[str] = set()
    if _COMPACT_JWT_RE.search(text):
        families.add("compact-jwt")
        value_families.add("compact-jwt")
    if _OPENAI_KEY_RE.search(text):
        families.add("openai-key-prefix")
        value_families.add("openai-key-prefix")
    bearer_matches = list(_AUTHORIZATION_BEARER_RE.finditer(text))
    if bearer_matches:
        families.add("authorization-bearer")
        if all(
            match.group(1) is None
            or match.group(1).strip().casefold() in _MANAGED_AUTH_REDACTED_VALUES
            for match in bearer_matches
        ):
            structural_families.add("authorization-bearer")
        else:
            value_families.add("authorization-bearer")
    return structural_families


def _classify_sensitive_json_value(value: Any) -> str:
    if value is None:
        return "EXPECTED_TRANSPORT_STRUCTURE"
    if isinstance(value, str):
        if value.strip().casefold() in _MANAGED_AUTH_REDACTED_VALUES:
            return "EXPECTED_TRANSPORT_STRUCTURE"
        return "CREDENTIAL_VALUE_RESIDUE"
    if isinstance(value, dict):
        classifications = [
            _classify_sensitive_json_value(item) for item in value.values()
        ]
    elif isinstance(value, list):
        classifications = [_classify_sensitive_json_value(item) for item in value]
    else:
        return "AMBIGUOUS_OR_UNAVAILABLE"
    if "CREDENTIAL_VALUE_RESIDUE" in classifications:
        return "CREDENTIAL_VALUE_RESIDUE"
    if "AMBIGUOUS_OR_UNAVAILABLE" in classifications:
        return "AMBIGUOUS_OR_UNAVAILABLE"
    return "EXPECTED_TRANSPORT_STRUCTURE"


def _sensitive_json_classifications(value: Any) -> list[str]:
    classifications: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() in _MANAGED_AUTH_SENSITIVE_KEYS:
                classifications.append(_classify_sensitive_json_value(item))
            else:
                classifications.extend(_sensitive_json_classifications(item))
    elif isinstance(value, list):
        for item in value:
            classifications.extend(_sensitive_json_classifications(item))
    return classifications


def classify_managed_auth_bytes(raw: bytes) -> dict[str, object]:
    if not isinstance(raw, bytes):
        raise TypeError("managed credential scan input must be bytes")
    families: set[str] = set()
    value_families: set[str] = set()
    detected_structural_families: set[str] = set()
    structural_families: set[str] = set()
    texts = _managed_auth_text_candidates(raw)
    detection_texts = list(
        dict.fromkeys(
            raw.decode(encoding, errors="ignore")
            for encoding in ENCODING_FORMS
        )
    )
    for text in detection_texts:
        detected_structural_families.update(
            _record_credential_value_signatures(text, families, value_families)
        )
        if _QUOTED_SENSITIVE_KEY_RE.search(text) or _has_semantic_sensitive_json_key(
            text
        ):
            families.add("credential-json-keys")
            detected_structural_families.add("credential-json-keys")
    for text in texts:
        bearer_matches = list(_AUTHORIZATION_BEARER_RE.finditer(text))
        if bearer_matches and all(
            match.group(1) is None
            or match.group(1).strip().casefold() in _MANAGED_AUTH_REDACTED_VALUES
            for match in bearer_matches
        ):
            structural_families.add("authorization-bearer")
        try:
            documents = _managed_auth_json_documents(text)
        except _SensitiveJsonKeyAmbiguity as exc:
            families.add("credential-json-keys")
            raise ManagedCredentialScanAmbiguousError(
                _ordered_managed_auth_families(families)
            ) from exc
        if documents is not None:
            classifications = [
                classification
                for document in documents
                for classification in _sensitive_json_classifications(document)
            ]
            decoded_structural_families = {
                family
                for document in documents
                for value in _json_string_values(document)
                for family in _record_credential_value_signatures(
                    value,
                    families,
                    value_families,
                )
            }
            detected_structural_families.update(decoded_structural_families)
            structural_families.update(decoded_structural_families)
            if classifications:
                families.add("credential-json-keys")
                detected_structural_families.add("credential-json-keys")
                if "CREDENTIAL_VALUE_RESIDUE" in classifications:
                    raise CredentialResidueError(
                        "managed credential value residue detected",
                        marker_families=_ordered_managed_auth_families(families),
                    )
                if "AMBIGUOUS_OR_UNAVAILABLE" in classifications:
                    raise ManagedCredentialScanAmbiguousError(
                        _ordered_managed_auth_families(families)
                    )
                structural_families.add("credential-json-keys")
    if value_families:
        raise CredentialResidueError(
            "managed credential value residue detected",
            marker_families=_ordered_managed_auth_families(families),
        )
    if detected_structural_families - structural_families:
        raise ManagedCredentialScanAmbiguousError(
            _ordered_managed_auth_families(families)
        )
    return {
        "semantic_classification": (
            "EXPECTED_TRANSPORT_STRUCTURE"
            if structural_families
            else "NO_CREDENTIAL_MARKERS"
        ),
        "observed_structure_families": list(
            _ordered_managed_auth_families(structural_families)
        ),
    }


def _strict_utc(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def valid_pass_credential_scan(scan: dict[str, Any], expected_worker: str) -> bool:
    counters_valid = all(
        isinstance(scan.get(field), int)
        and not isinstance(scan.get(field), bool)
        and scan[field] >= 0
        for field in ("scanned_file_count", "scanned_byte_count")
    )
    common_valid = (
        scan.get("status") == "PASS"
        and scan.get("worker") == expected_worker
        and counters_valid
        and scan.get("encoding_forms_checked") == list(ENCODING_FORMS)
        and _strict_utc(scan.get("completed_at"))
    )
    if scan.get("schema") == PASS_V1_SCHEMA:
        return common_valid and set(scan) == {
            "schema",
            "status",
            "worker",
            "scanned_file_count",
            "scanned_byte_count",
            "encoding_forms_checked",
            "completed_at",
        }
    if scan.get("schema") == PASS_V2_SCHEMA:
        return (
            common_valid
            and set(scan)
            == {
                "schema",
                "status",
                "worker",
                "scan_mode",
                "credential_value_loaded_by_adapter",
                "scanned_file_count",
                "scanned_byte_count",
                "marker_families_checked",
                "encoding_forms_checked",
                "completed_at",
            }
            and scan.get("scan_mode") == MANAGED_AUTH_SCAN_MODE
            and scan.get("credential_value_loaded_by_adapter") is False
            and scan.get("marker_families_checked") == list(MANAGED_AUTH_MARKER_FAMILIES)
        )
    if scan.get("schema") == PASS_V3_SCHEMA:
        observed = scan.get("observed_structure_families")
        semantic = scan.get("semantic_classification")
        expected_observed = (
            [
                family
                for family in MANAGED_AUTH_MARKER_FAMILIES
                if isinstance(observed, list) and family in observed
            ]
            if isinstance(observed, list)
            else None
        )
        return (
            common_valid
            and set(scan)
            == {
                "schema",
                "status",
                "worker",
                "scan_mode",
                "credential_value_loaded_by_adapter",
                "scanned_file_count",
                "scanned_byte_count",
                "semantic_classification",
                "observed_structure_families",
                "marker_families_checked",
                "encoding_forms_checked",
                "completed_at",
            }
            and scan.get("scan_mode") == MANAGED_AUTH_SCAN_MODE
            and scan.get("credential_value_loaded_by_adapter") is False
            and scan.get("marker_families_checked") == list(MANAGED_AUTH_MARKER_FAMILIES)
            and semantic in MANAGED_AUTH_PASS_CLASSIFICATIONS
            and observed == expected_observed
            and (
                (semantic == "NO_CREDENTIAL_MARKERS" and observed == [])
                or (
                    semantic == "EXPECTED_TRANSPORT_STRUCTURE"
                    and isinstance(observed, list)
                    and bool(observed)
                )
            )
        )
    return False


def valid_failed_credential_scan(scan: dict[str, Any], expected_worker: str) -> bool:
    common_valid = (
        scan.get("status") == "FAIL_CLOSED"
        and scan.get("cleanup_status") == "OWNED_WORKER_PURGED"
        and scan.get("failure_class") in {"CREDENTIAL_RESIDUE", "SCAN_UNAVAILABLE"}
        and scan.get("worker") == expected_worker
        and _strict_utc(scan.get("completed_at"))
    )
    if scan.get("schema") == PASS_V1_SCHEMA:
        return common_valid and set(scan) == {
            "schema",
            "status",
            "worker",
            "failure_class",
            "cleanup_status",
            "completed_at",
        }
    if scan.get("schema") == PASS_V2_SCHEMA:
        return (
            common_valid
            and set(scan)
            == {
                "schema",
                "status",
                "worker",
                "scan_mode",
                "credential_value_loaded_by_adapter",
                "failure_class",
                "cleanup_status",
                "completed_at",
            }
            and scan.get("scan_mode") == MANAGED_AUTH_SCAN_MODE
            and scan.get("credential_value_loaded_by_adapter") is False
        )
    if scan.get("schema") == PASS_V3_SCHEMA:
        observed = scan.get("observed_marker_families")
        expected_observed = (
            [
                family
                for family in MANAGED_AUTH_MARKER_FAMILIES
                if isinstance(observed, list) and family in observed
            ]
            if isinstance(observed, list)
            else None
        )
        outcomes = scan.get("safe_carrier_outcomes")
        failure_class = scan.get("failure_class")
        semantic = scan.get("semantic_classification")
        semantic_valid = (
            failure_class == "CREDENTIAL_RESIDUE"
            and semantic == "CREDENTIAL_VALUE_RESIDUE"
            and isinstance(observed, list)
            and bool(observed)
            or failure_class == "AMBIGUOUS_SCAN_RESULT"
            and semantic == "AMBIGUOUS_OR_UNAVAILABLE"
            and isinstance(observed, list)
            and bool(observed)
            or failure_class == "SCAN_UNAVAILABLE"
            and semantic == "AMBIGUOUS_OR_UNAVAILABLE"
            and observed == []
        )
        return (
            scan.get("status") == "FAIL_CLOSED"
            and scan.get("worker") == expected_worker
            and set(scan)
            == {
                "schema",
                "status",
                "worker",
                "scan_mode",
                "credential_value_loaded_by_adapter",
                "failure_class",
                "semantic_classification",
                "observed_marker_families",
                "safe_carrier_outcomes",
                "cleanup_status",
                "completed_at",
            }
            and scan.get("scan_mode") == MANAGED_AUTH_SCAN_MODE
            and scan.get("credential_value_loaded_by_adapter") is False
            and scan.get("cleanup_status")
            in {"OWNED_WORKER_PURGED", "OWNED_WORKER_PURGE_INCOMPLETE"}
            and _strict_utc(scan.get("completed_at"))
            and observed == expected_observed
            and semantic_valid
            and isinstance(outcomes, dict)
            and set(outcomes) == set(SAFE_CARRIER_ROLES)
            and all(value in SAFE_CARRIER_OUTCOMES for value in outcomes.values())
        )
    return False


__all__ = [
    "CredentialResidueError",
    "MANAGED_AUTH_MARKER_FAMILIES",
    "MANAGED_AUTH_FAILURE_CLASSIFICATIONS",
    "MANAGED_AUTH_PASS_CLASSIFICATIONS",
    "MANAGED_AUTH_SCAN_MODE",
    "PASS_V3_SCHEMA",
    "SAFE_CARRIER_OUTCOMES",
    "SAFE_CARRIER_ROLES",
    "ManagedCredentialScanAmbiguousError",
    "classify_managed_auth_bytes",
    "valid_failed_credential_scan",
    "valid_pass_credential_scan",
]
