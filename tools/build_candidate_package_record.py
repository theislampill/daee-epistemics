#!/usr/bin/env python3
"""Build neutral, claim-sensitive candidate custody records."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import unicodedata
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from a16_immutable_custody import (
    CustodyError,
    canonical_json_bytes,
    claim_json_once,
    exclusive_writer_lock,
    resolve_contained_path,
    strict_snapshot,
)
from artifact_tree import TREE_DIGEST_ALGORITHM, build_tree_receipt
from check_captured_output_manifest import PublicationError, _rename_directory_noreplace, atomic_publish_bytes
from contract_validation import validate_schema_subset
from package_skill import build_archive
from source_provenance import strict_json_loads

TERMINAL = {"CONSUMED_NO_DISPATCH", "CONSUMED_OBSERVED", "CONSUMED_DISPATCH_UNKNOWN", "QUARANTINED"}
WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL", "CLOCK$", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCHEMA = ROOT / "schema/smoke-matrix.schema.json"


def derive_transition(record: dict, *, claimed: bool, dispatch_count: int | None) -> str:
    current = record.get("status")
    if current in TERMINAL:
        raise ValueError("terminal_candidate_reuse: terminal candidate cannot transition or return to READY_UNUSED")
    if current != "READY_UNUSED": raise ValueError("candidate_state: transition requires READY_UNUSED")
    if not claimed: return "READY_UNUSED"
    if dispatch_count is None: return "CONSUMED_DISPATCH_UNKNOWN"
    if dispatch_count < 0: raise ValueError("dispatch_evidence: dispatch_count cannot be negative")
    return "CONSUMED_NO_DISPATCH" if dispatch_count == 0 else "CONSUMED_OBSERVED"


def _canonical_record(record: dict) -> bytes:
    return (json.dumps(record,sort_keys=True,separators=(",",":"))+"\n").encode()


def build_transition_record(record: dict, *, claimed: bool, dispatch_count: int | None) -> dict:
    for field in ("candidate_id","authorization_sha256","claim_receipt_sha256"):
        value=record.get(field)
        if not isinstance(value,str) or not value:raise ValueError(f"candidate_transition_binding: {field} is required")
    if any(len(record[field])!=64 or re.fullmatch(r"[a-f0-9]{64}",record[field]) is None for field in ("authorization_sha256","claim_receipt_sha256")):
        raise ValueError("candidate_transition_binding: authorization and claim hashes must be lowercase SHA-256")
    predecessor=hashlib.sha256(_canonical_record(record)).hexdigest()
    result={**record,"status":derive_transition(record,claimed=claimed,dispatch_count=dispatch_count),"predecessor_record_sha256":predecessor}
    unsigned={key:value for key,value in result.items() if key!="record_sha256"}
    result["record_sha256"]=hashlib.sha256(_canonical_record(unsigned)).hexdigest()
    return result


def publish_transition_record(record: dict, out: Path, *, claimed: bool, dispatch_count: int | None) -> dict:
    result=build_transition_record(record,claimed=claimed,dispatch_count=dispatch_count)
    encoded=_canonical_record(result)
    atomic_publish_bytes(out,encoded)
    if out.read_bytes()!=encoded:raise PublicationError("published transition changed during hash readback")
    return result


def publish_extraction_receipt(receipt: dict, out: Path) -> None:
    encoded=(json.dumps(receipt,indent=2,sort_keys=True)+"\n").encode()
    atomic_publish_bytes(out,encoded)
    if out.read_bytes()!=encoded:raise PublicationError("published extraction receipt changed during hash readback")


def assert_fresh_contained_path(root: Path, destination: Path) -> None:
    """Reject path escape, existing destination, and symlinked existing ancestors."""
    resolved_root=root.resolve(strict=True)
    destination=destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("destination_exists: exclusive fresh destination required")
    cursor=destination.parent
    while cursor!=resolved_root and cursor!=cursor.parent:
        if cursor.exists() and cursor.is_symlink():
            raise ValueError("candidate_symlink_escape: candidate ancestor is a symlink or junction")
        cursor=cursor.parent
    resolved_destination=destination.resolve(strict=False)
    if resolved_root not in resolved_destination.parents:
        if any(part.is_symlink() for part in destination.parents if part.exists() and part!=resolved_root):
            raise ValueError("candidate_symlink_escape: resolved candidate path escapes through a symlink or junction")
        raise ValueError("candidate_path_escape: candidate destination must remain beneath the authorized root")


def _validated_archive_entries(zf: zipfile.ZipFile, *, declared_total_bytes: int, max_total_bytes: int, max_entries: int | None = None) -> list[tuple[zipfile.ZipInfo, tuple[str,...]]]:
    entries=[]; exact=set(); folded=set(); regular_paths=[]; total=0
    all_entries=zf.infolist()
    if max_entries is not None and len(all_entries)>max_entries:raise ValueError("archive_entry_limit: central-directory entry count exceeds limit")
    for info in all_entries:
        raw=info.filename
        if raw.startswith(("//","\\\\")): raise ValueError("archive_unc_path: UNC member")
        if raw.startswith(("/","\\")): raise ValueError("archive_absolute_path: absolute or rooted member")
        if re.match(r"^[A-Za-z]:",raw): raise ValueError("archive_drive_path: drive-qualified member")
        normalized=raw.replace("\\","/"); parts=tuple(normalized.split("/"))
        if parts and parts[-1]=="" and info.is_dir(): parts=parts[:-1]
        if not parts or any(part in {"",".",".."} for part in parts):
            cls="archive_traversal" if ".." in parts else "archive_path_alias"
            raise ValueError(f"{cls}: invalid member components")
        if any(":" in part for part in parts): raise ValueError("archive_ads_name: colon/ADS member")
        if any(part.endswith(("."," ")) for part in parts): raise ValueError("archive_trailing_alias: trailing dot/space member")
        if any(part.split(".",1)[0].upper() in WINDOWS_DEVICES for part in parts): raise ValueError("archive_device_name: reserved device member")
        exact_key="/".join(parts)
        folded_key="/".join(unicodedata.normalize("NFC",part).casefold() for part in parts)
        if exact_key in exact: raise ValueError("archive_duplicate_entry: duplicate member")
        if folded_key in folded: raise ValueError("archive_casefold_collision: case-fold or Unicode collision")
        exact.add(exact_key); folded.add(folded_key)
        mode=(info.external_attr>>16)&0xFFFF; kind=stat.S_IFMT(mode)
        if info.flag_bits & 0x1: raise ValueError("archive_encrypted_entry: encrypted member")
        if info.external_attr & 0x400 or kind not in (0,stat.S_IFREG,stat.S_IFDIR): raise ValueError("archive_link_entry: link, device, or reparse metadata")
        if info.is_dir() or kind==stat.S_IFDIR: continue
        regular_paths.append(parts); total+=info.file_size; entries.append((info,parts))
    for parts in regular_paths:
        for other in regular_paths:
            if len(parts)<len(other) and other[:len(parts)]==parts: raise ValueError("archive_path_collision: file is parent of another member")
    if not isinstance(declared_total_bytes,int) or declared_total_bytes<0 or declared_total_bytes!=total: raise ValueError("archive_declared_size_mismatch: declared and central-directory sizes differ")
    if total>max_total_bytes: raise ValueError("archive_size_bomb: declared/actual archive size exceeds limit")
    return entries


def _tree_receipt(root: Path) -> tuple[str,list[dict]]:
    receipt = build_tree_receipt(root)
    return str(receipt["tree_sha256"]), list(receipt["files"])


def safe_extract_zip(archive: Path, destination: Path, *, declared_total_bytes: int, max_total_bytes: int, allowed_root: Path | None = None, max_entries: int | None = None, receipt_destination: str | None = None) -> dict:
    """Extract regular files to a fresh sibling staging dir, publish no-replace, hash-read back."""
    archive=archive.resolve(); destination=destination.absolute()
    if allowed_root is not None: assert_fresh_contained_path(allowed_root,destination)
    elif destination.exists() or destination.is_symlink(): raise FileExistsError("destination_exists: exclusive fresh destination required")
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=destination.with_name(f".{destination.name}.staging-{uuid.uuid4().hex}")
    os.mkdir(staging)
    published=False
    try:
        with zipfile.ZipFile(archive,"r") as zf:
            entries=_validated_archive_entries(zf,declared_total_bytes=declared_total_bytes,max_total_bytes=max_total_bytes,max_entries=max_entries)
            actual=0
            for info,parts in entries:
                target=staging.joinpath(*parts); target.parent.mkdir(parents=True,exist_ok=True)
                with zf.open(info,"r") as source, open(target,"xb") as sink:
                    while chunk:=source.read(1024*1024):
                        actual+=len(chunk)
                        if actual>max_total_bytes: raise ValueError("archive_size_bomb: streamed bytes exceed limit")
                        sink.write(chunk)
                    sink.flush(); os.fsync(sink.fileno())
                if target.stat().st_size!=info.file_size: raise ValueError("archive_actual_size_mismatch: extracted member size differs")
        if actual!=declared_total_bytes: raise ValueError("archive_actual_size_mismatch: extracted total differs from declaration")
        tree_sha,rows=_tree_receipt(staging)
        _rename_directory_noreplace(staging,destination); published=True
        readback_sha,readback_rows=_tree_receipt(destination)
        if readback_sha!=tree_sha or readback_rows!=rows: raise ValueError("archive_hash_readback_mismatch: published tree changed")
        locator=str(destination) if receipt_destination is None else receipt_destination
        if receipt_destination is not None:
            relative=Path(receipt_destination)
            if not receipt_destination or relative.is_absolute() or ".." in relative.parts:raise ValueError("receipt_destination: stable extraction locator must be relative and contained")
            locator=relative.as_posix()
        return {"schema":"candidate-extraction-receipt-v1","archive_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"destination":locator,"declared_total_bytes":declared_total_bytes,"actual_total_bytes":actual,"file_count":len(rows),"tree_digest_algorithm":TREE_DIGEST_ALGORITHM,"tree_sha256":tree_sha,"files":rows,"publication":"NO_REPLACE_HASH_READBACK"}
    finally:
        if not published and staging.exists() and staging.parent==destination.parent: shutil.rmtree(staging)


def _record_content_sha(value: dict, field: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def _validate_build_authorization(value: dict) -> None:
    schema = json.loads(SMOKE_SCHEMA.read_text(encoding="utf-8"))
    selected = {"$ref": "#/$defs/candidateBuildAuthorization", "$defs": schema["$defs"]}
    errors = validate_schema_subset(value, selected)
    if errors:
        raise ValueError(f"candidate authorization schema: {errors[0]}")
    if value["authorization_sha256"] != _record_content_sha(value, "authorization_sha256"):
        raise ValueError("candidate authorization content hash drift")
    if value["ref"] != f"refs/heads/{value['branch']}":
        raise ValueError("candidate authorization branch/ref drift")


def _parse_utc(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("candidate authorization timestamp is invalid") from exc


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve(strict=True).relative_to(root.resolve(strict=True)).as_posix()
    except ValueError as exc:
        raise ValueError(f"candidate custody path escapes repository root: {path}") from exc


def _verify_bound_reference(repo_root: Path, reference: dict, label: str) -> Path:
    path = resolve_contained_path(repo_root, reference["path"], must_exist=True)
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"candidate {label} reference is not one regular file")
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != reference["sha256"]:
        raise ValueError(f"candidate {label} reference hash drift")
    return path


def _artifact_ref(repo_root: Path, path: Path) -> dict[str, str]:
    return {
        "path": _relative_to_root(path, repo_root),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def validate_candidate_readiness(candidate_root: Path, *, repo_root: Path) -> dict:
    """Revalidate every bound candidate byte before any readiness consumer proceeds."""
    repo_root=repo_root.resolve(strict=True);candidate_root=candidate_root.resolve(strict=True)
    record,record_raw,_record_file_sha=strict_snapshot(candidate_root/"candidate-record.json")
    schema=json.loads(SMOKE_SCHEMA.read_text(encoding="utf-8"))
    for value,definition,label in (
        (record,"candidateRecordBound","candidate record"),
    ):
        errors=validate_schema_subset(value,{"$ref":f"#/$defs/{definition}","$defs":schema["$defs"]})
        if errors:raise ValueError(f"{label} schema drift: {errors[0]}")
    if record["record_sha256"]!=_record_content_sha(record,"record_sha256"):
        raise ValueError("candidate readiness record hash drift")
    if _relative_to_root(candidate_root,repo_root)!=record["candidate_root"]:
        raise ValueError("candidate readiness root drift")

    readiness_path=resolve_contained_path(candidate_root,record["readiness_marker_path"],must_exist=False)
    if not readiness_path.is_file() or readiness_path.is_symlink():
        raise ValueError("candidate readiness marker is absent")
    readiness,_readiness_raw,_readiness_file_sha=strict_snapshot(readiness_path)
    errors=validate_schema_subset(readiness,{"$ref":"#/$defs/candidateReadinessMarker","$defs":schema["$defs"]})
    if errors:raise ValueError(f"candidate readiness marker schema drift: {errors[0]}")
    if readiness["marker_sha256"]!=_record_content_sha(readiness,"marker_sha256"):
        raise ValueError("candidate readiness marker hash drift")

    archive=resolve_contained_path(candidate_root,record["archive"]["path"],must_exist=True)
    if not archive.is_file() or archive.is_symlink() or archive.stat().st_size!=record["archive"]["byte_count"] or hashlib.sha256(archive.read_bytes()).hexdigest()!=record["archive"]["sha256"]:
        raise ValueError("candidate readiness archive drift")
    extraction_path=resolve_contained_path(candidate_root,record["extraction_receipt"]["path"],must_exist=True)
    extraction_raw=extraction_path.read_bytes()
    if hashlib.sha256(extraction_raw).hexdigest()!=record["extraction_receipt"]["sha256"]:
        raise ValueError("candidate readiness extraction receipt drift")
    try:extraction=strict_json_loads(extraction_raw,label=str(extraction_path))
    except (UnicodeDecodeError,json.JSONDecodeError,ValueError) as exc:raise ValueError(f"candidate readiness extraction receipt invalid: {exc}") from exc
    if not isinstance(extraction,dict) or extraction.get("destination")!="extracted" or extraction.get("archive_sha256")!=record["archive"]["sha256"] or extraction.get("tree_digest_algorithm")!=TREE_DIGEST_ALGORITHM or extraction.get("tree_sha256")!=record["extracted_tree_sha256"] or extraction.get("file_count")!=record["extracted_file_count"]:
        raise ValueError("candidate readiness extraction binding drift")
    extracted=resolve_contained_path(candidate_root,extraction["destination"],must_exist=True)
    tree=build_tree_receipt(extracted)
    if tree["algorithm"]!=TREE_DIGEST_ALGORITHM or tree["tree_sha256"]!=record["extracted_tree_sha256"] or tree["file_count"]!=record["extracted_file_count"]:
        raise ValueError("candidate readiness extracted tree drift")
    for field in ("build_manifest","skill_root","compiled_module_map","cold_law_manifest"):
        path=resolve_contained_path(candidate_root,record[field]["path"],must_exist=True)
        if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=record[field]["sha256"]:
            raise ValueError(f"candidate readiness {field} drift")
    for field in ("source_commit_receipt","ci_readback","source_preflight","input_registry","validation_registry","producer_registry","escape_registry","usage_writer","review_protocol","build_authorization","build_claim"):
        _verify_bound_reference(repo_root,record[field],field)
    expected_marker={
        "candidate_id":record["candidate_id"],"candidate_root":record["candidate_root"],"status":"READY_UNUSED",
        "record_sha256":record["record_sha256"],"archive_sha256":record["archive"]["sha256"],
        "tree_digest_algorithm":record["tree_digest_algorithm"],"extracted_tree_sha256":record["extracted_tree_sha256"],
    }
    if any(readiness.get(field)!=value for field,value in expected_marker.items()):
        raise ValueError("candidate readiness marker/record binding drift")
    return record


def build_authorized_candidate(
    *,
    repo_root: Path,
    authorization_path: Path,
    now: datetime | None = None,
    archive_builder: Callable[[Path, Path, str], tuple[int, str]] = build_archive,
) -> dict:
    """Consume one exact build authorization and atomically publish a bound candidate.

    This builder performs no model or provider call.  A consumed authorization is never
    reusable, including when package construction later fails.
    """

    repo_root = repo_root.resolve(strict=True)
    authorization_path = authorization_path.resolve(strict=True)
    authorization, _authorization_raw, authorization_file_sha = strict_snapshot(
        authorization_path
    )
    _validate_build_authorization(authorization)

    custody_root = resolve_contained_path(
        repo_root, authorization["custody_root"], must_exist=True
    )
    authorization_root = (custody_root / "authorizations").resolve(strict=True)
    try:
        authorization_path.relative_to(authorization_root)
    except ValueError as exc:
        raise ValueError("candidate authorization leaves protected authority root") from exc
    if authorization_path.is_symlink():
        raise ValueError("candidate authorization must not be a symlink")

    candidate_root = resolve_contained_path(
        repo_root, authorization["candidate_root"], must_exist=False
    )
    claim_path = resolve_contained_path(
        repo_root, authorization["claim_path"], must_exist=False
    )
    if claim_path.exists():
        raise ValueError("candidate claim replay: authorization was already consumed")
    assert_fresh_contained_path(custody_root, candidate_root)
    try:
        claim_path.relative_to((custody_root / "claims").resolve(strict=False))
    except ValueError as exc:
        raise ValueError("candidate claim leaves the protected claims root") from exc
    if claim_path.name != f"{authorization['authorization_id']}.claim.json":
        raise ValueError("candidate claim locator is not authorization-derived")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("candidate build time must be timezone-aware")
    current = current.astimezone(timezone.utc)
    if not (_parse_utc(authorization["issued_at"]) <= current < _parse_utc(authorization["expires_at"])):
        raise ValueError("candidate authorization is outside its validity window")

    reference_snapshots = {}
    for field in (
        "source_commit_receipt",
        "ci_readback",
        "source_preflight",
        "input_registry",
        "validation_registry",
        "producer_registry",
        "escape_registry",
        "usage_writer",
        "review_protocol",
    ):
        path=_verify_bound_reference(repo_root, authorization[field], field)
        reference_snapshots[field]=(path,authorization[field]["sha256"])

    def revalidate_bound_references() -> None:
        for field,(path,expected) in reference_snapshots.items():
            if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError(f"candidate {field} reference hash drift")

    claimed_at = current.strftime("%Y-%m-%dT%H:%M:%SZ")
    claim = {
        "schema": "daee-smoke-matrix-v1",
        "kind": "candidate-build-claim",
        "claim_id": f"{authorization['authorization_id']}-claim",
        "authorization_id": authorization["authorization_id"],
        "authorization_sha256": authorization["authorization_sha256"],
        "candidate_id": authorization["candidate_id"],
        "claimed_at": claimed_at,
        "one_use": True,
        "terminal_claim": False,
    }
    claim["claim_sha256"] = _record_content_sha(claim, "claim_sha256")
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_file_sha = claim_json_once(custody_root, claim_path, claim)

    candidate_root.parent.mkdir(parents=True, exist_ok=True)
    staging = candidate_root.parent / f".{candidate_root.name}.staging-{uuid.uuid4().hex}"
    os.mkdir(staging)
    published = False
    try:
        archive_path = staging / authorization["archive_name"]
        archive_builder(repo_root, archive_path, profile="execution-mini")
        if not archive_path.is_file() or not archive_path.read_bytes():
            raise ValueError("candidate archive builder did not produce nonempty bytes")
        if archive_path.stat().st_size>authorization["max_archive_bytes"]:
            raise ValueError("candidate archive byte limit exceeded")
        archive_byte_count=archive_path.stat().st_size
        archive_sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest()

        def verify_archive_snapshot(path: Path) -> None:
            if not path.is_file() or path.is_symlink() or path.stat().st_size!=archive_byte_count or path.stat().st_size>authorization["max_archive_bytes"] or hashlib.sha256(path.read_bytes()).hexdigest()!=archive_sha256:
                raise ValueError("candidate archive snapshot drift")

        with zipfile.ZipFile(archive_path, "r") as archive:
            archive_entries=archive.infolist()
            if len(archive_entries)>authorization["max_archive_entries"]:
                raise ValueError("candidate archive entry limit exceeded")
            declared_total = sum(row.file_size for row in archive_entries if not row.is_dir())
        if declared_total>authorization["max_extracted_bytes"]:
            raise ValueError("candidate extracted byte limit exceeded")
        revalidate_bound_references()
        extracted_root = staging / "extracted"
        extraction = safe_extract_zip(
            archive_path,
            extracted_root,
            declared_total_bytes=declared_total,
            max_total_bytes=authorization["max_extracted_bytes"],
            allowed_root=staging,
            max_entries=authorization["max_archive_entries"],
            receipt_destination="extracted",
        )
        if extraction["archive_sha256"]!=archive_sha256:
            raise ValueError("candidate extraction receipt archive snapshot drift")
        extraction_path = staging / "candidate-extraction-receipt.json"
        publish_extraction_receipt(extraction, extraction_path)
        extraction_raw=extraction_path.read_bytes()
        verify_archive_snapshot(archive_path)

        required = {
            "build_manifest": extracted_root / "build-manifest.json",
            "skill_root": extracted_root / "SKILL.md",
            "compiled_module_map": extracted_root / "compiled-module-map.json",
            "cold_law_manifest": extracted_root / "cold-law-manifest.json",
        }
        for label, path in required.items():
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"candidate archive is missing required {label}")

        record = {
            "schema": "daee-smoke-matrix-v1",
            "kind": "candidate-package-record-bound",
            "candidate_id": authorization["candidate_id"],
            "status": "READY_UNUSED",
            "branch": authorization["branch"],
            "ref": authorization["ref"],
            "source_commit": authorization["source_commit"],
            "source_commit_receipt": authorization["source_commit_receipt"],
            "ci_readback": authorization["ci_readback"],
            "source_preflight": authorization["source_preflight"],
            "package_profile": "execution-mini",
            "archive": {
                "path": authorization["archive_name"],
                "sha256": archive_sha256,
                "byte_count": archive_byte_count,
            },
            "extraction_receipt": {
                "path": "candidate-extraction-receipt.json",
                "sha256": hashlib.sha256(extraction_path.read_bytes()).hexdigest(),
            },
            "extracted_root": "extracted",
            "tree_digest_algorithm": TREE_DIGEST_ALGORITHM,
            "extracted_tree_sha256": extraction["tree_sha256"],
            "extracted_file_count": extraction["file_count"],
            **{
                label: {
                    "path": path.relative_to(staging).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                for label, path in required.items()
            },
            "input_registry": authorization["input_registry"],
            "validation_registry": authorization["validation_registry"],
            "producer_registry": authorization["producer_registry"],
            "escape_registry": authorization["escape_registry"],
            "usage_writer": authorization["usage_writer"],
            "review_protocol": authorization["review_protocol"],
            "custody_root": authorization["custody_root"],
            "candidate_root": authorization["candidate_root"],
            "readiness_marker_path": "candidate-readiness.json",
            "build_authorization": {
                "path": _relative_to_root(authorization_path, repo_root),
                "sha256": authorization_file_sha,
            },
            "build_claim": {
                "path": _relative_to_root(claim_path, repo_root),
                "sha256": claim_file_sha,
            },
            "build_authorization_sha256": authorization["authorization_sha256"],
            "build_claim_sha256": claim["claim_sha256"],
            "claim_status": "UNCLAIMED",
            "promotion_eligible": False,
            "model_execution_authorized": False,
            "invalidation_conditions": [
                "source or CI receipt drift",
                "candidate byte drift",
                "registry or review protocol drift",
            ],
            "non_claims": [
                "READY_UNUSED is not candidate maturity",
                "READY_UNUSED is not model execution authorization",
                "READY_UNUSED is not owner acceptance",
            ],
        }
        record["record_sha256"] = _record_content_sha(record, "record_sha256")
        record_path = staging / "candidate-record.json"
        record_raw=canonical_json_bytes(record)
        atomic_publish_bytes(record_path, record_raw)
        revalidate_bound_references()
        verify_archive_snapshot(archive_path)
        _rename_directory_noreplace(staging, candidate_root)
        published = True
        with exclusive_writer_lock(custody_root):
            published_record = candidate_root / "candidate-record.json"
            published_archive=candidate_root/authorization["archive_name"]
            if not published_archive.is_file() or hashlib.sha256(published_archive.read_bytes()).hexdigest()!=record["archive"]["sha256"] or published_archive.stat().st_size!=record["archive"]["byte_count"]:
                raise ValueError("candidate archive publication readback drift")
            published_extraction=candidate_root/"candidate-extraction-receipt.json"
            if published_extraction.read_bytes()!=extraction_raw or hashlib.sha256(extraction_raw).hexdigest()!=record["extraction_receipt"]["sha256"]:
                raise ValueError("candidate extraction receipt publication readback drift")
            if extraction["archive_sha256"]!=record["archive"]["sha256"]:
                raise ValueError("candidate extraction receipt/archive identity drift")
            if published_record.read_bytes() != record_raw:
                raise ValueError("candidate record publication readback drift")
            for label,reference in required.items():
                published_path=candidate_root/reference.relative_to(staging)
                if not published_path.is_file() or published_path.is_symlink() or hashlib.sha256(published_path.read_bytes()).hexdigest()!=record[label]["sha256"]:
                    raise ValueError(f"candidate {label} publication readback drift")
            if extraction.get("destination")!="extracted" or not (candidate_root/extraction["destination"]).is_dir():
                raise ValueError("candidate extraction locator publication readback drift")
            if build_tree_receipt(candidate_root / "extracted")["tree_sha256"] != record["extracted_tree_sha256"]:
                raise ValueError("candidate extracted tree publication readback drift")
            revalidate_bound_references()
            readiness={
                "schema":"daee-smoke-matrix-v1",
                "kind":"candidate-readiness-marker",
                "candidate_id":record["candidate_id"],
                "candidate_root":record["candidate_root"],
                "status":"READY_UNUSED",
                "record_sha256":record["record_sha256"],
                "archive_sha256":record["archive"]["sha256"],
                "tree_digest_algorithm":record["tree_digest_algorithm"],
                "extracted_tree_sha256":record["extracted_tree_sha256"],
                "readback_status":"VERIFIED",
                "promotion_eligible":False,
                "model_execution_authorized":False,
                "terminal_claim":False,
                "non_claims":[
                    "readback verification is not candidate maturity",
                    "readback verification is not model execution authorization",
                    "readback verification is not owner acceptance",
                ],
            }
            readiness["marker_sha256"]=_record_content_sha(readiness,"marker_sha256")
            readiness_path=candidate_root/record["readiness_marker_path"]
            readiness_raw=canonical_json_bytes(readiness)
            marker_identity=None
            try:
                atomic_publish_bytes(readiness_path,readiness_raw)
                marker_stat=readiness_path.stat(follow_symlinks=False)
                marker_identity=(marker_stat.st_dev,marker_stat.st_ino,marker_stat.st_ctime_ns)
                if readiness_path.read_bytes()!=readiness_raw:
                    raise ValueError("candidate readiness marker publication readback drift")
                validate_candidate_readiness(candidate_root,repo_root=repo_root)
            except Exception:
                if marker_identity is not None and readiness_path.is_file() and not readiness_path.is_symlink():
                    current=readiness_path.stat(follow_symlinks=False)
                    current_identity=(current.st_dev,current.st_ino,current.st_ctime_ns)
                    if current_identity==marker_identity and readiness_path.read_bytes()==readiness_raw:
                        readiness_path.unlink()
                raise
            return record
    finally:
        if not published and staging.exists() and staging.parent == candidate_root.parent:
            shutil.rmtree(staging)


def self_test() -> int:
    r={"status":"READY_UNUSED"}
    checks=[("preclaim",derive_transition(r,claimed=False,dispatch_count=None)=="READY_UNUSED"),("zero",derive_transition(r,claimed=True,dispatch_count=0)=="CONSUMED_NO_DISPATCH"),("observed",derive_transition(r,claimed=True,dispatch_count=1)=="CONSUMED_OBSERVED"),("unknown",derive_transition(r,claimed=True,dispatch_count=None)=="CONSUMED_DISPATCH_UNKNOWN")]
    try: derive_transition({"status":"CONSUMED_OBSERVED"},claimed=True,dispatch_count=0); checks.append(("terminal reuse",False))
    except ValueError: checks.append(("terminal reuse",True))
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); archive=root/"safe.zip"
        with zipfile.ZipFile(archive,"w") as zf: zf.writestr("skill/SKILL.md","ok\n")
        receipt=safe_extract_zip(archive,root/"out",declared_total_bytes=3,max_total_bytes=32)
        checks.append(("safe extraction hash readback",receipt["actual_total_bytes"]==3 and receipt["publication"]=="NO_REPLACE_HASH_READBACK" and receipt["tree_digest_algorithm"]==TREE_DIGEST_ALGORITHM))
    for n,o in checks: print(f"  self-test {'PASS' if o else 'FAIL'}: {n}")
    return 0 if all(o for _,o in checks) else 1


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--record",type=Path); p.add_argument("--claimed",action="store_true"); p.add_argument("--dispatch-count",type=int); p.add_argument("--out",type=Path); p.add_argument("--extract-archive",type=Path); p.add_argument("--extract-destination",type=Path); p.add_argument("--allowed-root",type=Path); p.add_argument("--declared-total-bytes",type=int); p.add_argument("--max-total-bytes",type=int); p.add_argument("--build-authorization",type=Path); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test:return self_test()
    if a.build_authorization:
        authorization=a.build_authorization if a.build_authorization.is_absolute() else ROOT/a.build_authorization
        record=build_authorized_candidate(repo_root=ROOT,authorization_path=authorization)
        print(json.dumps({"status":"READY_UNUSED","candidate_id":record["candidate_id"],"record_sha256":record["record_sha256"],"terminal_claim":False},sort_keys=True))
        return 0
    if a.extract_archive:
        if not a.extract_destination or a.declared_total_bytes is None or a.max_total_bytes is None or not a.out:p.error("archive extraction requires --extract-destination --declared-total-bytes --max-total-bytes --out")
        if not a.allowed_root:p.error("archive extraction requires --allowed-root")
        receipt=safe_extract_zip(a.extract_archive,a.extract_destination,declared_total_bytes=a.declared_total_bytes,max_total_bytes=a.max_total_bytes,allowed_root=a.allowed_root);publish_extraction_receipt(receipt,a.out);return 0
    if not a.record or not a.out:p.error("--record and --out are required")
    data=json.loads(a.record.read_text(encoding="utf-8")); publish_transition_record(data,a.out,claimed=a.claimed,dispatch_count=a.dispatch_count); return 0


if __name__=="__main__":sys.exit(main())
