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
from pathlib import Path

from check_captured_output_manifest import PublicationError, _rename_directory_noreplace, atomic_publish_bytes

TERMINAL = {"CONSUMED_NO_DISPATCH", "CONSUMED_OBSERVED", "CONSUMED_DISPATCH_UNKNOWN", "QUARANTINED"}
WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL", "CLOCK$", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


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


def _validated_archive_entries(zf: zipfile.ZipFile, *, declared_total_bytes: int, max_total_bytes: int) -> list[tuple[zipfile.ZipInfo, tuple[str,...]]]:
    entries=[]; exact=set(); folded=set(); regular_paths=[]; total=0
    for info in zf.infolist():
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
    rows=[]
    for path in sorted((p for p in root.rglob("*") if p.is_file()),key=lambda p:p.relative_to(root).as_posix().casefold()):
        raw=path.read_bytes(); rows.append({"path":path.relative_to(root).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})
    digest=hashlib.sha256((json.dumps(rows,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
    return digest,rows


def safe_extract_zip(archive: Path, destination: Path, *, declared_total_bytes: int, max_total_bytes: int, allowed_root: Path | None = None) -> dict:
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
            entries=_validated_archive_entries(zf,declared_total_bytes=declared_total_bytes,max_total_bytes=max_total_bytes)
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
        return {"schema":"candidate-extraction-receipt-v1","archive_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"destination":str(destination),"declared_total_bytes":declared_total_bytes,"actual_total_bytes":actual,"file_count":len(rows),"tree_sha256":tree_sha,"files":rows,"publication":"NO_REPLACE_HASH_READBACK"}
    finally:
        if not published and staging.exists() and staging.parent==destination.parent: shutil.rmtree(staging)


def self_test() -> int:
    r={"status":"READY_UNUSED"}
    checks=[("preclaim",derive_transition(r,claimed=False,dispatch_count=None)=="READY_UNUSED"),("zero",derive_transition(r,claimed=True,dispatch_count=0)=="CONSUMED_NO_DISPATCH"),("observed",derive_transition(r,claimed=True,dispatch_count=1)=="CONSUMED_OBSERVED"),("unknown",derive_transition(r,claimed=True,dispatch_count=None)=="CONSUMED_DISPATCH_UNKNOWN")]
    try: derive_transition({"status":"CONSUMED_OBSERVED"},claimed=True,dispatch_count=0); checks.append(("terminal reuse",False))
    except ValueError: checks.append(("terminal reuse",True))
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); archive=root/"safe.zip"
        with zipfile.ZipFile(archive,"w") as zf: zf.writestr("skill/SKILL.md","ok\n")
        receipt=safe_extract_zip(archive,root/"out",declared_total_bytes=3,max_total_bytes=32)
        checks.append(("safe extraction hash readback",receipt["actual_total_bytes"]==3 and receipt["publication"]=="NO_REPLACE_HASH_READBACK"))
    for n,o in checks: print(f"  self-test {'PASS' if o else 'FAIL'}: {n}")
    return 0 if all(o for _,o in checks) else 1


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--record",type=Path); p.add_argument("--claimed",action="store_true"); p.add_argument("--dispatch-count",type=int); p.add_argument("--out",type=Path); p.add_argument("--extract-archive",type=Path); p.add_argument("--extract-destination",type=Path); p.add_argument("--allowed-root",type=Path); p.add_argument("--declared-total-bytes",type=int); p.add_argument("--max-total-bytes",type=int); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test:return self_test()
    if a.extract_archive:
        if not a.extract_destination or a.declared_total_bytes is None or a.max_total_bytes is None or not a.out:p.error("archive extraction requires --extract-destination --declared-total-bytes --max-total-bytes --out")
        if not a.allowed_root:p.error("archive extraction requires --allowed-root")
        receipt=safe_extract_zip(a.extract_archive,a.extract_destination,declared_total_bytes=a.declared_total_bytes,max_total_bytes=a.max_total_bytes,allowed_root=a.allowed_root);publish_extraction_receipt(receipt,a.out);return 0
    if not a.record or not a.out:p.error("--record and --out are required")
    data=json.loads(a.record.read_text(encoding="utf-8")); publish_transition_record(data,a.out,claimed=a.claimed,dispatch_count=a.dispatch_count); return 0


if __name__=="__main__":sys.exit(main())
