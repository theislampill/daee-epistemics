#!/usr/bin/env python3
"""Shared secret-safe contract for retained credential-residue scan records."""
from __future__ import annotations

from datetime import datetime
from typing import Any


PASS_V1_SCHEMA = "reviewed-campaign-credential-residue-scan-v1"
PASS_V2_SCHEMA = "reviewed-campaign-credential-residue-scan-v2"
MANAGED_AUTH_SCAN_MODE = "MANAGED_AUTH_STRUCTURAL_MARKERS"
MANAGED_AUTH_MARKER_FAMILIES = (
    "credential-json-keys",
    "authorization-bearer",
    "compact-jwt",
    "openai-key-prefix",
)
ENCODING_FORMS = ("utf-8", "utf-16-le", "utf-16-be")


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
    return False


__all__ = [
    "MANAGED_AUTH_MARKER_FAMILIES",
    "MANAGED_AUTH_SCAN_MODE",
    "valid_failed_credential_scan",
    "valid_pass_credential_scan",
]
