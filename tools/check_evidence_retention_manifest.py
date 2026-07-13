#!/usr/bin/env python3
"""Validate A16 retained-evidence manifests, CAS objects, and export receipts."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import stat
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Mapping

from a16_immutable_custody import (
    CustodyError,
    canonical_json_bytes,
    resolve_contained_path,
    sha256_bytes,
    strict_snapshot,
)
from contract_validation import SchemaDefinitionError, validate_schema_subset
from source_provenance import strict_json_loads


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema/evidence-retention-manifest.schema.json"
SCHEMA_ID = "daee-evidence-retention-manifest-v1"
CHECKER_ID = "evidence-retention-manifest"
INVENTORY_ALGORITHM = "daee-retention-inventory-sha256-v1"
TREE_ALGORITHM = "daee-retained-tree-sha256-v1"
PUBLICATION_MODE = "ATOMIC_DIRECTORY_NO_REPLACE_WITH_CAS_POINTER"
NON_CLAIMS = [
    "retention export is not candidate maturity",
    "retention export is not model execution authorization",
    "retention export is not owner acceptance",
]
RETENTION_POLICY = {
    "mode": "RETAIN_INDEFINITELY",
    "pruning_authorized": False,
    "separate_owner_authorization_required": True,
    "permanent_removal_residue_required": True,
}
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_WINDOWS_DEVICES = {
    "CON", "PRN", "AUX", "NUL", "CLOCK$",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


@dataclass(frozen=True)
class Finding:
    failure_class: str
    failure_subcode: str
    message: str


def _finding(subcode: str, message: str, failure_class: str = "retention_contract") -> Finding:
    return Finding(failure_class, subcode, message)


def _schema() -> dict[str, Any]:
    value = strict_json_loads(SCHEMA_PATH.read_bytes(), label=str(SCHEMA_PATH))
    if not isinstance(value, dict):
        raise ValueError("retention schema root must be an object")
    return value


def content_hash(value: Mapping[str, Any], field: str) -> str:
    unsigned = {key: copy.deepcopy(item) for key, item in value.items() if key != field}
    return sha256_bytes(canonical_json_bytes(unsigned))


def custody_root_fingerprint(root: Path) -> str:
    resolved = root.resolve(strict=True)
    return sha256_bytes(b"daee-evidence-custody-root-v1\0" + os.fsencode(str(resolved)))


def _relative_path_error(value: Any, *, label: str) -> Finding | None:
    if not isinstance(value, str) or not value or "\x00" in value:
        return _finding("path-shape", f"{label} must be nonempty text")
    if value != unicodedata.normalize("NFC", value):
        return _finding("path-normalization", f"{label} must use NFC path bytes")
    windows = PureWindowsPath(value)
    posix = PurePosixPath(value)
    if (
        value.startswith(("/", "\\"))
        or windows.is_absolute()
        or bool(windows.drive)
        or "\\" in value
        or ":" in value
    ):
        return _finding("path-absolute", f"{label} must be a portable relative POSIX path: {value}")
    if posix.as_posix() != value or any(part in {"", ".", ".."} for part in posix.parts):
        return _finding("path-traversal", f"{label} is not canonical or contains traversal: {value}")
    for part in posix.parts:
        if any(ord(character) < 32 for character in part):
            return _finding("path-control-character", f"{label} contains a control character")
        if part.endswith((" ", ".")) or part.split(".", 1)[0].upper() in _WINDOWS_DEVICES:
            return _finding("path-portability", f"{label} is not portable to Windows: {value}")
    return None


def _alias(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def inventory_sha256(rows: list[dict[str, Any]]) -> str:
    return sha256_bytes(canonical_json_bytes(rows))


def retained_tree_sha256(rows: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["retained_path"]):
        path = row["retained_path"].encode("utf-8")
        digest.update(len(path).to_bytes(4, "big"))
        digest.update(path)
        digest.update(b"\x01" if row["present"] else b"\x00")
        if row["present"]:
            digest.update(bytes.fromhex(row["sha256"]))
    return digest.hexdigest()


def _required_identity_rows(value: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], Finding | None]:
    references = {
        "source_commit_receipt": value["source_identity"]["source_commit_receipt"],
        "ci_readback": value["source_identity"]["ci_readback"],
        "candidate_record": value["candidate_identity"]["candidate_record"],
        "candidate_readiness": value["candidate_identity"]["candidate_readiness"],
    }
    if value.get("cycle_identity") is not None:
        references["cycle_claim"] = value["cycle_identity"]["cycle_claim"]
    paths = [reference["path"] for reference in references.values()]
    if len(paths) != len(set(paths)):
        return {}, _finding("identity-reference-alias", "retention identity references must use distinct paths")
    bound: dict[str, dict[str, Any]] = {}
    for label, reference in references.items():
        matches = [
            row
            for row in value["inventory"]
            if row["source_path"] == reference["path"]
            and row["retained_path"] == reference["path"]
        ]
        if len(matches) != 1:
            return {}, _finding(
                "identity-reference-unretained",
                f"{label} must bind exactly one same-path retained inventory row",
            )
        row = matches[0]
        if (
            row["classification"] != "CONTROL_RECORD"
            or row["required"] is not True
            or row["present"] is not True
            or row["sha256"] != reference["sha256"]
            or row["byte_count"] != reference["byte_count"]
        ):
            return {}, _finding(
                "identity-reference-binding",
                f"{label} retained row must be required/present CONTROL_RECORD with exact hash and byte count",
            )
        bound[label] = row
    return bound, None


def _is_reparse(path: Path) -> bool:
    observed = path.lstat()
    return path.is_symlink() or bool(getattr(observed, "st_file_attributes", 0) & _REPARSE_POINT)


def _snapshot_regular(path: Path) -> tuple[bytes, str, int]:
    if _is_reparse(path) or not path.is_file():
        raise ValueError(f"retained object is not a regular non-reparse file: {path}")
    before = path.stat(follow_symlinks=False)
    raw = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or len(raw) != after.st_size:
        raise ValueError(f"retained object changed during readback: {path}")
    return raw, sha256_bytes(raw), len(raw)


def _contained_regular_path(
    root: Path,
    relative: str,
    *,
    label: str,
    expect_directory: bool = False,
) -> Path:
    finding = _relative_path_error(relative, label=label)
    if finding:
        raise ValueError(finding.message)
    root_resolved = root.resolve(strict=True)
    current = root_resolved
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current /= part
        try:
            current.lstat()
        except FileNotFoundError as exc:
            raise ValueError(f"{label} required path is absent: {relative}") from exc
        if _is_reparse(current):
            raise ValueError(f"{label} rejects symlink or reparse content: {relative}")
        if index < len(parts) - 1 and not current.is_dir():
            raise ValueError(f"{label} parent is not a directory: {relative}")
    try:
        current.resolve(strict=True).relative_to(root_resolved)
    except (OSError, ValueError) as exc:
        raise ValueError(f"{label} escapes custody root: {relative}") from exc
    if expect_directory:
        if not current.is_dir():
            raise ValueError(f"{label} is not a directory: {relative}")
    elif not current.is_file():
        raise ValueError(f"{label} is not a regular file: {relative}")
    return current


def _contained_regular_snapshot(
    root: Path,
    relative: str,
    *,
    label: str,
) -> tuple[dict[str, Any], bytes, str]:
    path = _contained_regular_path(root, relative, label=label)
    return strict_snapshot(path)


def _schema_finding(value: Any) -> Finding | None:
    try:
        issues = validate_schema_subset(value, _schema())
    except (OSError, ValueError, SchemaDefinitionError) as exc:
        return _finding("schema-definition", str(exc), "schema_contract")
    if not issues:
        return None
    issue = issues[0]
    return _finding(
        f"schema-{issue.keyword.lower()}",
        f"{issue.path}: {issue.message}",
        "schema_contract",
    )


def validate_manifest(value: Any, *, custody_root: Path | None = None) -> list[Finding]:
    # Path custody is a pre-schema boundary so a malicious locator cannot hide
    # behind a generic oneOf dispatch failure.
    if isinstance(value, dict) and isinstance(value.get("inventory"), list):
        for index, row in enumerate(value["inventory"]):
            if not isinstance(row, dict):
                continue
            for field in ("source_path", "retained_path", "cas_object_path"):
                candidate = row.get(field)
                if candidate is None:
                    continue
                finding = _relative_path_error(candidate, label=f"inventory[{index}].{field}")
                if finding:
                    return [finding]
    if isinstance(value, dict) and isinstance(value.get("custody"), dict):
        for field in ("staging_path", "claim_path", "final_path", "receipt_path", "pointer_path"):
            candidate = value["custody"].get(field)
            if candidate is None:
                continue
            finding = _relative_path_error(candidate, label=f"custody.{field}")
            if finding:
                return [finding]
    schema_finding = _schema_finding(value)
    if schema_finding:
        return [schema_finding]
    if not isinstance(value, dict) or value.get("kind") == "evidence-export-receipt":
        return [_finding("manifest-kind", "artifact is not a retention manifest")]

    rows = value["inventory"]
    path_fields = ("source_path", "retained_path")
    seen: dict[str, set[str]] = {field: set() for field in path_fields}
    artifact_ids: set[str] = set()
    for row in rows:
        artifact_id = row["artifact_id"]
        if artifact_id in artifact_ids:
            return [_finding("duplicate-artifact-id", f"inventory repeats artifact_id {artifact_id}")]
        artifact_ids.add(artifact_id)
        for field in path_fields:
            finding = _relative_path_error(row[field], label=f"inventory.{artifact_id}.{field}")
            if finding:
                return [finding]
            alias = _alias(row[field])
            if alias in seen[field]:
                return [_finding("path-alias", f"inventory {field} aliases another row: {row[field]}")]
            seen[field].add(alias)
        if row["present"]:
            finding = _relative_path_error(row["cas_object_path"], label=f"inventory.{artifact_id}.cas_object_path")
            if finding:
                return [finding]
            expected_object = f"objects/sha256/{row['sha256'][:2]}/{row['sha256']}"
            if row["cas_object_path"] != expected_object:
                return [_finding("cas-object-path", f"{artifact_id} CAS locator is not content-addressed")]
    if rows != sorted(rows, key=lambda row: row["artifact_id"]):
        return [_finding("inventory-order", "inventory rows must be sorted by artifact_id")]

    custody = value["custody"]
    for field in ("staging_path", "claim_path", "final_path", "receipt_path", "pointer_path"):
        finding = _relative_path_error(custody[field], label=f"custody.{field}")
        if finding:
            return [finding]
    export_id = value["export_id"]
    scope_id = value["scope_id"]
    expected_paths = {
        "staging_path": f".staging/{export_id}",
        "claim_path": f"claims/{export_id}.json",
        "receipt_path": f"receipts/{export_id}.json",
        "pointer_path": f"pointers/{scope_id}/head.json",
    }
    for field, expected in expected_paths.items():
        if custody[field] != expected:
            return [_finding("custody-locator", f"custody.{field} must equal {expected}")]
    if value["kind"] == "candidate-readiness-final-manifest":
        expected_final = f"candidates/{value['candidate_identity']['candidate_id']}/retention/{export_id}"
    else:
        expected_final = f"cycles/{value['cycle_identity']['cycle_id']}/exports/{export_id}"
    if custody["final_path"] != expected_final:
        return [_finding("final-locator", "final path differs from the exact candidate/cycle export locator")]

    source = value["source_identity"]
    if source["ref"] != f"refs/heads/{source['branch']}":
        return [_finding("source-identity", "source ref does not equal refs/heads/<branch>")]
    cycle = value["cycle_identity"]
    if value["kind"] == "candidate-readiness-final-manifest" and cycle is not None:
        return [_finding("cycle-identity", "candidate readiness retention must not invent a cycle")]
    if value["kind"] == "observation-cycle-export" and cycle["phase"] != "OBSERVATION":
        return [_finding("cycle-phase", "observation export must bind the OBSERVATION phase")]
    if value["kind"] == "final-reviewed-cycle-manifest" and cycle["phase"] != "REVIEWED_FINAL":
        return [_finding("cycle-phase", "final reviewed export must bind REVIEWED_FINAL")]
    if cycle is not None and cycle["cycle_id"] != scope_id:
        return [_finding("cycle-scope", "cycle_id differs from pointer scope_id")]
    identity_rows, identity_finding = _required_identity_rows(value)
    if identity_finding:
        return [identity_finding]

    missing = sorted(row["artifact_id"] for row in rows if row["required"] and not row["present"])
    if value["missing_required_artifact_ids"] != missing:
        return [_finding("missing-inventory-accounting", "missing-required list is not the exact required/absent set")]
    completeness = "PARTIAL" if missing else "COMPLETE"
    status = "RETENTION_PARTIAL" if missing else "RETENTION_GREEN"
    if value["completeness"] != completeness or value["status"] != status:
        return [_finding("completeness-status", "completeness/status do not derive from required absent rows")]
    if value["kind"] != "observation-cycle-export" and missing:
        return [_finding("final-required-missing", "final retention manifests cannot omit a required artifact")]
    if value["inventory_digest_algorithm"] != INVENTORY_ALGORITHM or value["inventory_sha256"] != inventory_sha256(rows):
        return [_finding("inventory-hash", "inventory digest differs from exact canonical rows")]
    if value["retained_tree_digest_algorithm"] != TREE_ALGORITHM or value["retained_tree_sha256"] != retained_tree_sha256(rows):
        return [_finding("retained-tree-hash", "retained tree digest differs from framed retained paths/content")]
    unique_objects = {row["sha256"] for row in rows if row["present"]}
    if value["cas_object_count"] != len(unique_objects):
        return [_finding("cas-object-count", "CAS object count differs from unique retained hashes")]
    if value["retained_byte_count"] != sum(row["byte_count"] for row in rows if row["present"]):
        return [_finding("retained-byte-count", "retained byte count differs from inventory")]
    if value["retention_policy"] != RETENTION_POLICY:
        return [_finding("retention-policy", "retention policy is not indefinite and non-pruning")]
    if value["non_claims"] != NON_CLAIMS or value["terminal_claim"] is not False:
        return [_finding("nonclaims", "retention nonclaims or terminal boundary drifted")]
    if value["model_execution_authorized"] is not False:
        return [_finding("model-authorization", "retention must not authorize model execution")]
    if value["cas_readback_status"] != "PASS" or value["publication_mode"] != PUBLICATION_MODE:
        return [_finding("custody-mode", "retention custody/readback mode drifted")]
    if value["manifest_sha256"] != content_hash(value, "manifest_sha256"):
        return [_finding("manifest-hash", "manifest_sha256 differs from canonical manifest content")]

    if custody_root is None:
        return []
    try:
        root = custody_root.resolve(strict=True)
        if custody["root_fingerprint_sha256"] != custody_root_fingerprint(root):
            return [_finding("custody-root-fingerprint", "manifest belongs to a different custody root")]
        for label, row in identity_rows.items():
            try:
                identity_path = _contained_regular_path(
                    root,
                    row["cas_object_path"],
                    label=f"{label} retained CAS object",
                )
                _raw, digest, size = _snapshot_regular(identity_path)
            except (CustodyError, OSError, ValueError) as exc:
                return [_finding("identity-reference-readback", f"{label} retained CAS proof failed: {exc}", "evidence_custody")]
            if digest != row["sha256"] or size != row["byte_count"]:
                return [_finding("identity-reference-readback", f"{label} retained CAS proof hash/bytes drifted", "evidence_custody")]
        for row in rows:
            if not row["present"]:
                continue
            path = _contained_regular_path(
                root,
                row["cas_object_path"],
                label=f"{row['artifact_id']} CAS object",
            )
            raw, digest, size = _snapshot_regular(path)
            del raw
            if digest != row["sha256"]:
                return [_finding("cas-object-hash", f"CAS object hash drifted for {row['artifact_id']}")]
            if size != row["byte_count"]:
                return [_finding("cas-object-byte-count", f"CAS object byte count drifted for {row['artifact_id']}")]
    except (CustodyError, OSError, ValueError) as exc:
        return [_finding("cas-readback", str(exc), "evidence_custody")]
    return []


def validate_receipt(value: Any, manifest: Mapping[str, Any]) -> list[Finding]:
    schema_finding = _schema_finding(value)
    if schema_finding:
        return [schema_finding]
    if not isinstance(value, dict) or value.get("kind") != "evidence-export-receipt":
        return [_finding("receipt-kind", "artifact is not an evidence-export receipt")]
    if value["receipt_sha256"] != content_hash(value, "receipt_sha256"):
        return [_finding("receipt-hash", "receipt_sha256 differs from canonical receipt content")]
    equal_fields = (
        "export_id", "scope_id", "authorization_sha256", "authorization_file_sha256",
        "claim_receipt", "source_identity", "candidate_identity", "cycle_identity",
        "completeness", "retained_byte_count", "retained_tree_sha256", "non_claims",
    )
    for field in equal_fields:
        if value[field] != manifest[field]:
            return [_finding("receipt-binding", f"receipt {field} differs from the manifest")]
    if value["status"] != manifest["status"] or value["object_count"] != manifest["cas_object_count"]:
        return [_finding("receipt-binding", "receipt status/object count differs from manifest")]
    if value["final_path"] != manifest["custody"]["final_path"] or value["pointer_path"] != manifest["custody"]["pointer_path"]:
        return [_finding("receipt-locator", "receipt final/pointer locator differs from manifest")]
    if value["expected_pointer_sha256"] != manifest["custody"]["expected_pointer_sha256"]:
        return [_finding("receipt-predecessor", "receipt expected predecessor differs from manifest")]
    if value["final_readback_status"] != "PASS" or value["pointer_readback_status"] != "PASS":
        return [_finding("receipt-readback", "receipt does not prove final and pointer readback")]
    if value["terminal"] is not True or value["terminal_claim"] is not False or value["one_use"] is not True:
        return [_finding("receipt-terminal", "receipt create-once/terminal flags drifted")]
    return []


def _pointer_shape_findings(pointer: Mapping[str, Any]) -> list[Finding]:
    expected_keys = {
        "schema", "scope_id", "sequence", "export_id", "manifest", "claim_receipt",
        "authorization_sha256", "source_commit", "candidate_id", "status",
        "predecessor_pointer_sha256", "pointer_sha256",
    }
    if set(pointer) != expected_keys or pointer.get("schema") != "daee-evidence-retention-pointer-v1":
        return [_finding("pointer-shape", "pointer record has the wrong closed shape")]
    if pointer.get("pointer_sha256") != content_hash(pointer, "pointer_sha256"):
        return [_finding("pointer-hash", "pointer_sha256 differs from canonical pointer content")]
    sequence = pointer.get("sequence")
    predecessor = pointer.get("predecessor_pointer_sha256")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        return [_finding("pointer-sequence", "pointer sequence must be a positive integer")]
    if predecessor is None:
        if sequence != 1:
            return [_finding("pointer-sequence", "genesis pointer sequence must equal one")]
    elif (
        not isinstance(predecessor, str)
        or len(predecessor) != 64
        or any(character not in "0123456789abcdef" for character in predecessor)
        or sequence <= 1
    ):
        return [_finding("pointer-sequence", "non-genesis pointer requires a valid predecessor and sequence above one")]
    return []


def _pointer_findings(pointer: Mapping[str, Any], manifest: Mapping[str, Any], receipt: Mapping[str, Any]) -> list[Finding]:
    if findings := _pointer_shape_findings(pointer):
        return findings
    expected = {
        "scope_id": manifest["scope_id"],
        "export_id": manifest["export_id"],
        "authorization_sha256": manifest["authorization_sha256"],
        "source_commit": manifest["source_identity"]["commit_sha"],
        "candidate_id": manifest["candidate_identity"]["candidate_id"],
        "status": manifest["status"],
        "predecessor_pointer_sha256": manifest["custody"]["expected_pointer_sha256"],
    }
    for field, required in expected.items():
        if pointer.get(field) != required:
            return [_finding("pointer-binding", f"pointer {field} differs from manifest")]
    if pointer.get("manifest") != receipt["manifest"] or pointer.get("claim_receipt") != manifest["claim_receipt"]:
        return [_finding("pointer-reference", "pointer manifest/claim references drifted")]
    return []


def _pointer_chain_findings(root: Path, pointer: Mapping[str, Any]) -> list[Finding]:
    current = pointer
    seen = {str(pointer.get("pointer_sha256"))}
    while current.get("predecessor_pointer_sha256") is not None:
        predecessor = str(current["predecessor_pointer_sha256"])
        if predecessor in seen:
            return [_finding("pointer-cycle", "pointer predecessor chain contains a replay cycle")]
        seen.add(predecessor)
        relative = f"pointers/{pointer['scope_id']}/records/{predecessor}.json"
        try:
            previous, _raw, _file_sha = _contained_regular_snapshot(
                root,
                relative,
                label="pointer predecessor record",
            )
        except (CustodyError, OSError, ValueError) as exc:
            return [_finding("pointer-predecessor-readback", str(exc), "evidence_custody")]
        if findings := _pointer_shape_findings(previous):
            return findings
        if previous.get("pointer_sha256") != predecessor:
            return [_finding("pointer-predecessor-hash", "pointer predecessor record has the wrong content hash")]
        if previous.get("scope_id") != pointer.get("scope_id"):
            return [_finding("pointer-predecessor-scope", "pointer predecessor belongs to another scope")]
        if previous.get("sequence") != current.get("sequence") - 1:
            return [_finding("pointer-sequence", "pointer predecessor sequence is not contiguous")]
        current = previous
    return []


def _pointer_chain_contains(root: Path, pointer: Mapping[str, Any], target_sha256: str) -> tuple[bool, list[Finding]]:
    current = pointer
    while True:
        if current.get("pointer_sha256") == target_sha256:
            return True, []
        predecessor = current.get("predecessor_pointer_sha256")
        if predecessor is None:
            return False, []
        relative = f"pointers/{pointer['scope_id']}/records/{predecessor}.json"
        try:
            current, _raw, _file_sha = _contained_regular_snapshot(
                root,
                relative,
                label="pointer ancestry record",
            )
        except (CustodyError, OSError, ValueError) as exc:
            return False, [_finding("pointer-predecessor-readback", str(exc), "evidence_custody")]


def _historical_receipt_chain_findings(root: Path, pointer: Mapping[str, Any]) -> list[Finding]:
    current = pointer
    while current.get("predecessor_pointer_sha256") is not None:
        predecessor = str(current["predecessor_pointer_sha256"])
        record_relative = f"pointers/{pointer['scope_id']}/records/{predecessor}.json"
        try:
            previous, _raw, _file_sha = _contained_regular_snapshot(
                root,
                record_relative,
                label="historical receipt pointer record",
            )
        except (CustodyError, OSError, ValueError) as exc:
            return [_finding("pointer-history-record", str(exc), "evidence_custody")]
        manifest_ref = previous.get("manifest")
        manifest_path = manifest_ref.get("path") if isinstance(manifest_ref, dict) else None
        finding = _relative_path_error(manifest_path, label="historical receipt manifest path")
        if finding or not str(manifest_path).endswith("/manifest.json"):
            return [_finding("pointer-history-manifest", "historical pointer has an invalid manifest locator")]
        final_directory = Path(str(PurePosixPath(str(manifest_path)).parent))
        findings = validate_export(
            root,
            final_directory,
            _validate_historical_receipts=False,
        )
        if findings:
            return [_finding(
                "pointer-history-receipt",
                f"historical receipt chain is incomplete at {previous.get('export_id')}: {findings[0].message}",
            )]
        current = previous
    return []


def validate_export(
    custody_root: Path,
    final_directory: Path,
    *,
    _validate_historical_receipts: bool = True,
) -> list[Finding]:
    try:
        root = custody_root.resolve(strict=True)
        requested_final = Path(final_directory)
        lexical_final = requested_final if requested_final.is_absolute() else root / requested_final
        try:
            final_relative = lexical_final.relative_to(root).as_posix()
        except ValueError as exc:
            return [_finding("final-directory", f"final export is outside custody: {exc}", "evidence_custody")]
        final = _contained_regular_path(
            root,
            final_relative,
            label="final export directory",
            expect_directory=True,
        )
        entries = sorted(path.name for path in final.iterdir())
        if entries != ["export-claim.json", "manifest.json"]:
            return [_finding("partial-publication", f"final export has unexpected or missing members: {entries}", "evidence_custody")]
        manifest, manifest_raw, manifest_file_sha = _contained_regular_snapshot(
            root,
            f"{final_relative}/manifest.json",
            label="final manifest",
        )
        claim, claim_raw, claim_file_sha = _contained_regular_snapshot(
            root,
            f"{final_relative}/export-claim.json",
            label="final claim copy",
        )
    except (CustodyError, OSError, ValueError) as exc:
        return [_finding("final-readback", str(exc), "evidence_custody")]
    findings = validate_manifest(manifest, custody_root=root)
    if findings:
        return findings
    try:
        manifest_final = _contained_regular_path(
            root,
            manifest["custody"]["final_path"],
            label="manifest final directory",
            expect_directory=True,
        )
    except ValueError as exc:
        return [_finding("final-locator", str(exc), "evidence_custody")]
    if final != manifest_final:
        return [_finding("final-locator", "validated directory differs from manifest final locator")]
    try:
        external_claim, external_claim_raw, external_claim_sha = _contained_regular_snapshot(
            root,
            manifest["custody"]["claim_path"],
            label="external claim receipt",
        )
    except (CustodyError, OSError, ValueError) as exc:
        return [_finding("claim-readback", str(exc), "evidence_custody")]
    if external_claim != claim or external_claim_raw != claim_raw or external_claim_sha != claim_file_sha:
        return [_finding("claim-collision", "final claim copy differs from create-once external claim")]
    if manifest["claim_receipt"] != {
        "path": manifest["custody"]["claim_path"],
        "sha256": claim_file_sha,
        "byte_count": len(claim_raw),
    }:
        return [_finding("claim-reference", "manifest claim reference differs from exact claim bytes")]

    try:
        receipt, receipt_raw, receipt_file_sha = _contained_regular_snapshot(
            root,
            manifest["custody"]["receipt_path"],
            label="export receipt",
        )
    except (CustodyError, OSError, ValueError) as exc:
        return [_finding("receipt-readback", str(exc), "evidence_custody")]
    findings = validate_receipt(receipt, manifest)
    if findings:
        return findings
    manifest_ref = {
        "path": f"{manifest['custody']['final_path']}/manifest.json",
        "sha256": manifest_file_sha,
        "byte_count": len(manifest_raw),
    }
    if receipt["manifest"] != manifest_ref:
        return [_finding("manifest-reference", "receipt does not bind exact final manifest bytes")]

    pointer_record_ref = receipt["pointer_record"]
    record_relative = pointer_record_ref["path"]
    finding = _relative_path_error(record_relative, label="receipt.pointer_record.path")
    if finding:
        return [finding]
    expected_record_prefix = f"pointers/{manifest['scope_id']}/records/"
    if not record_relative.startswith(expected_record_prefix) or not record_relative.endswith(".json"):
        return [_finding("pointer-reference", "receipt pointer record is outside the exact scope record directory")]
    try:
        pointer, pointer_raw, pointer_file_sha = _contained_regular_snapshot(
            root,
            record_relative,
            label="receipt-bound pointer record",
        )
    except (CustodyError, OSError, ValueError) as exc:
        return [_finding("pointer-record-readback", str(exc), "evidence_custody")]
    if pointer_record_ref != {
        "path": record_relative,
        "sha256": pointer_file_sha,
        "byte_count": len(pointer_raw),
    }:
        return [_finding("pointer-reference", "receipt does not bind the exact pointer record")]
    if record_relative != f"pointers/{manifest['scope_id']}/records/{pointer.get('pointer_sha256')}.json":
        return [_finding("pointer-reference", "receipt pointer record locator differs from its content hash")]
    findings = _pointer_findings(pointer, manifest, receipt)
    if findings:
        return findings
    findings = _pointer_chain_findings(root, pointer)
    if findings:
        return findings
    if _validate_historical_receipts:
        findings = _historical_receipt_chain_findings(root, pointer)
        if findings:
            return findings

    try:
        head, head_raw, head_file_sha = _contained_regular_snapshot(
            root,
            manifest["custody"]["pointer_path"],
            label="pointer head",
        )
    except (CustodyError, OSError, ValueError) as exc:
        return [_finding("pointer-readback", str(exc), "evidence_custody")]
    if findings := _pointer_shape_findings(head):
        return findings
    if head.get("scope_id") != manifest["scope_id"]:
        return [_finding("pointer-head-scope", "current pointer head belongs to another scope")]
    findings = _pointer_chain_findings(root, head)
    if findings:
        return findings
    head_record_relative = f"pointers/{manifest['scope_id']}/records/{head['pointer_sha256']}.json"
    try:
        head_record, head_record_raw, head_record_file_sha = _contained_regular_snapshot(
            root,
            head_record_relative,
            label="current pointer record",
        )
    except (CustodyError, OSError, ValueError) as exc:
        return [_finding("pointer-record-readback", str(exc), "evidence_custody")]
    if head_record != head or head_record_raw != head_raw or head_record_file_sha != head_file_sha:
        return [_finding("pointer-record-drift", "mutable pointer head differs from its immutable pointer record")]
    contained, chain_findings = _pointer_chain_contains(root, head, pointer["pointer_sha256"])
    if chain_findings:
        return chain_findings
    if not contained:
        return [_finding("pointer-lineage", "receipt-bound export pointer is not in current head ancestry")]
    if receipt["receipt_sha256"] != content_hash(receipt, "receipt_sha256") or receipt_file_sha != sha256_bytes(receipt_raw):
        return [_finding("receipt-readback", "external receipt bytes changed after publication")]
    if claim.get("export_id") != manifest["export_id"] or claim.get("authorization_sha256") != manifest["authorization_sha256"]:
        return [_finding("claim-binding", "claim does not bind manifest export/authorization")]
    return []


def diagnostic(finding: Finding, artifact: str) -> dict[str, Any]:
    return {
        "artifact": artifact,
        "checker_id": CHECKER_ID,
        "status": "FAIL",
        "failure_class": finding.failure_class,
        "failure_subcode": finding.failure_subcode,
        "message": finding.message,
        "downstream_invalidated": ["candidate-maturity", "reviewed-five-smoke-campaign"],
        "terminal_claim": False,
    }


def _fixture_ref(path: str) -> dict[str, Any]:
    return {"path": path, "sha256": "a" * 64, "byte_count": 1}


def _self_test_manifest() -> dict[str, Any]:
    identity_paths = {
        "candidate-readiness": "candidates/self-test-candidate/readiness.json",
        "candidate-record": "candidates/self-test-candidate/record.json",
        "ci-readback": "receipts/ci.json",
        "source-commit-receipt": "receipts/source.json",
    }
    rows = [
        {
            "artifact_id": artifact_id,
            "source_path": path,
            "retained_path": path,
            "classification": "CONTROL_RECORD",
            "required": True,
            "present": True,
            "sha256": "a" * 64,
            "byte_count": 1,
            "cas_object_path": f"objects/sha256/aa/{'a' * 64}",
        }
        for artifact_id, path in identity_paths.items()
    ]
    rows.append({
        "artifact_id": "declared-absent",
        "source_path": "review/not-yet-created.json",
        "retained_path": "review/not-yet-created.json",
        "classification": "SANITIZED_REVIEW",
        "required": False,
        "present": False,
        "sha256": None,
        "byte_count": None,
        "cas_object_path": None,
    })
    rows.sort(key=lambda row: row["artifact_id"])
    value = {
        "schema": SCHEMA_ID,
        "kind": "candidate-readiness-final-manifest",
        "status": "RETENTION_GREEN",
        "export_id": "self-test-export",
        "scope_id": "self-test-candidate",
        "authorization_sha256": "b" * 64,
        "authorization_file_sha256": "c" * 64,
        "claim_receipt": _fixture_ref("claims/self-test-export.json"),
        "source_identity": {
            "repository": "theislampill/daee-epistemics",
            "branch": "branch",
            "ref": "refs/heads/branch",
            "commit_sha": "d" * 40,
            "tree_sha": "e" * 40,
            "source_commit_receipt": _fixture_ref("receipts/source.json"),
            "ci_readback": _fixture_ref("receipts/ci.json"),
        },
        "candidate_identity": {
            "candidate_id": "self-test-candidate",
            "candidate_record": _fixture_ref("candidates/self-test-candidate/record.json"),
            "candidate_readiness": _fixture_ref("candidates/self-test-candidate/readiness.json"),
            "package_sha256": "f" * 64,
            "package_tree_sha256": "1" * 64,
            "tree_digest_algorithm": "daee-tree-sha256-v1",
            "status": "READY_UNUSED",
        },
        "cycle_identity": None,
        "inventory": rows,
        "inventory_digest_algorithm": INVENTORY_ALGORITHM,
        "inventory_sha256": inventory_sha256(rows),
        "retained_tree_digest_algorithm": TREE_ALGORITHM,
        "retained_tree_sha256": retained_tree_sha256(rows),
        "cas_object_count": 1,
        "retained_byte_count": 4,
        "cas_readback_status": "PASS",
        "publication_mode": PUBLICATION_MODE,
        "completeness": "COMPLETE",
        "missing_required_artifact_ids": [],
        "retention_policy": copy.deepcopy(RETENTION_POLICY),
        "custody": {
            "root_fingerprint_sha256": "2" * 64,
            "object_store_path": "objects/sha256",
            "staging_path": ".staging/self-test-export",
            "claim_path": "claims/self-test-export.json",
            "final_path": "candidates/self-test-candidate/retention/self-test-export",
            "receipt_path": "receipts/self-test-export.json",
            "pointer_path": "pointers/self-test-candidate/head.json",
            "expected_pointer_sha256": None,
        },
        "exported_at": "2026-07-12T12:00:00Z",
        "model_execution_authorized": False,
        "terminal_claim": False,
        "non_claims": list(NON_CLAIMS),
    }
    value["manifest_sha256"] = content_hash(value, "manifest_sha256")
    return value


def self_test() -> int:
    manifest = _self_test_manifest()
    problems: list[str] = []
    if findings := validate_manifest(manifest):
        problems.append(f"valid manifest rejected: {findings[0]}")
    mutations = {
        "path-escape": ("inventory.0.cas", lambda value: value["inventory"][0].update({"present": True, "sha256": "3" * 64, "byte_count": 1, "cas_object_path": "../escape"})),
        "manifest-hash": ("manifest hash", lambda value: value["source_identity"].update({"commit_sha": "4" * 40})),
        "retention-policy": ("retention policy", lambda value: value["retention_policy"].update({"pruning_authorized": True})),
        "self-maturity": ("status", lambda value: value.update({"status": "NO_MODEL_CANDIDATE_MATURE"})),
    }
    for name, (_marker, mutate) in mutations.items():
        value = copy.deepcopy(manifest)
        mutate(value)
        if not validate_manifest(value):
            problems.append(f"{name} mutation survived")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print("evidence retention manifest self-test: PASS (1 valid, 4 invalid; no model/candidate/cycle execution)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--manifest")
    parser.add_argument("--custody-root")
    parser.add_argument("--final-directory")
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        if args.manifest or args.custody_root or args.final_directory:
            parser.error("--self-test cannot be combined with live custody paths")
        return self_test()
    if args.final_directory:
        if not args.custody_root:
            parser.error("--final-directory requires --custody-root")
        findings = validate_export(Path(args.custody_root), Path(args.final_directory))
        artifact = args.final_directory
    elif args.manifest:
        path = Path(args.manifest)
        try:
            value, _raw, _digest = strict_snapshot(path)
        except (CustodyError, OSError, ValueError) as exc:
            findings = [_finding("manifest-read", str(exc), "evidence_custody")]
        else:
            findings = validate_manifest(value, custody_root=Path(args.custody_root) if args.custody_root else None)
        artifact = args.manifest
    else:
        parser.error("--manifest or --final-directory is required")
    if findings:
        finding = findings[0]
        print(json.dumps(diagnostic(finding, artifact), sort_keys=True) if args.explain else f"evidence retention manifest: FAIL [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}")
        return 1
    print(json.dumps({"checker_id": CHECKER_ID, "status": "PASS", "terminal_claim": False}, sort_keys=True) if args.explain else "evidence retention manifest: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
