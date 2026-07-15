#!/usr/bin/env python3
"""Append-only campaign usage journal with a single CAS-governed head."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path

from check_captured_output_manifest import PublicationError, atomic_publish_bytes
from smoke_matrix_registry import DEFAULT_REGISTRY, load_registry

EXACT_CALLS = {"gpt-producer": 5, "gpt-review": 5, "paired-producer": 10, "paired-review": 10}
HEAD_KEYS = {"schema", "sequence", "campaign_authorization_sha256", "last_transaction_sha256", "unresolved_usage", "open_reservations", "totals", "measured_cost"}
TOTAL_KEYS = {"attempted", "accepted", "in_flight", "completed", "failed", "cancelled", "not_dispatched", "unknown", "producer_invocations", "cold_review_invocations"}
CALL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED", "NOT_DISPATCHED", "UNKNOWN"}
COHORT_PROTOCOLS = {"gpt-producer":"barrier-five-submit-before-await-v1","paired-producer":"barrier-ten-submit-before-await-v1","gpt-review":"independent-cold-review-v1","paired-review":"paired-independent-cold-review-v1"}
TRANSPORT_STATUSES={"NOT_STARTED","PROVIDER_ACCEPTED","ADAPTER_IN_FLIGHT","IN_FLIGHT","COMPLETED","FAILED","CANCELLED","TIMEOUT","CONNECTION_LOST","UNKNOWN"}
ACK_ORIGINS={"NONE","PROVIDER_ACCEPTED","ADAPTER_IN_FLIGHT","BOTH"}


def _canonical(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _digest(value: dict) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _initial() -> dict:
    return {"schema":"campaign-usage-head-v1","sequence":0,"campaign_authorization_sha256":None,"last_transaction_sha256":None,"unresolved_usage":False,"open_reservations":[],"totals":{key:0 for key in TOTAL_KEYS},"measured_cost":{"unit":"usd","value":"0"}}


def _load_unchecked(root: Path) -> dict:
    path=root/"head.json"
    if not path.is_file(): return _initial()
    raw=path.read_bytes()
    try: head=json.loads(raw)
    except json.JSONDecodeError as exc: raise ValueError(f"usage_head_canonical: {exc}") from exc
    if raw!=_canonical(head): raise ValueError("usage_head_canonical: head bytes are not canonical")
    return head


def head_snapshot(root: Path) -> dict:
    head=validate_head(root)
    return {**head,"head_sha256":_digest(head)}


def _atomic_write(path: Path, value: dict) -> None:
    raw=_canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as handle: handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        os.replace(name,path)
        try: readback=path.read_bytes()
        except OSError as exc: raise ValueError(f"usage_head_readback: {exc}") from exc
        if readback!=raw or hashlib.sha256(readback).hexdigest()!=hashlib.sha256(raw).hexdigest():
            raise ValueError("usage_head_readback: atomically replaced head did not hash-read back exactly")
    finally:
        if os.path.exists(name): os.unlink(name)


@contextmanager
def _lock(root: Path):
    root.mkdir(parents=True,exist_ok=True); lock=root/".writer.lock"
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError as exc: raise ValueError("usage_head_conflict: exclusive writer is held") from exc
    try: yield
    finally: os.close(fd); lock.unlink(missing_ok=True)


def _append(root: Path, tx: dict) -> str:
    _validate_transaction(tx)
    raw=_canonical(tx);digest=hashlib.sha256(raw).hexdigest();path=root/"transactions"/f"{digest}.json";path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError("usage_transaction_collision: final content address contains different bytes")
    else:
        try:atomic_publish_bytes(path,raw)
        except PublicationError as exc:
            if not path.is_file() or path.read_bytes()!=raw:raise ValueError("usage_transaction_collision: transaction publication lost no-replace race") from exc
    readback=path.read_bytes()
    if readback!=raw or hashlib.sha256(readback).hexdigest()!=digest:raise ValueError("usage_transaction_readback: immutable transaction readback mismatch")
    return digest


def _sha(value: object, field: str) -> str:
    if not isinstance(value,str) or re.fullmatch(r"[a-f0-9]{64}",value) is None:
        raise ValueError(f"usage_binding: {field} must be a lowercase SHA-256")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value,str) or not value:
        raise ValueError(f"usage_binding: {field} must be nonempty text")
    return value


def _decimal_text(value: object, field: str, *, allow_unknown: bool=True) -> str:
    if allow_unknown and value=="unknown":return "unknown"
    if not isinstance(value,str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?",value):raise ValueError(f"usage_provider_metadata: {field} must be canonical nonnegative decimal text or unknown")
    try:number=Decimal(value)
    except InvalidOperation as exc:raise ValueError(f"usage_provider_metadata: {field} is not decimal") from exc
    if number<0:raise ValueError(f"usage_provider_metadata: {field} cannot be negative")
    return value


def _cost(value: object, field: str="measured_cost") -> dict:
    if not isinstance(value,dict) or value.get("unit")!="usd":raise ValueError(f"usage_provider_metadata: {field} requires exact usd cost custody")
    keys=set(value)
    if keys=={"unit","value"}:
        pass
    elif keys=={"unit","value","status","reason","source"}:
        if value.get("value")!="unknown" or value.get("status")!="UNAVAILABLE" or not isinstance(value.get("reason"),str) or not value["reason"] or not isinstance(value.get("source"),str) or not value["source"]:raise ValueError(f"usage_provider_metadata: {field} governed unavailability is invalid")
    else:raise ValueError(f"usage_provider_metadata: {field} requires exact usd cost custody")
    _decimal_text(value.get("value"),f"{field}.value")
    return value


def _paired_parent_contract(value: object, cohort: str) -> dict|None:
    paired=cohort in {"paired-producer","paired-review"}
    if not paired:
        if value is not None:raise ValueError("usage_binding: paired parent authorization is valid only for paired cohorts")
        return None
    required={"schema","test_only","live_execution_authorized","parent_id","cohort","source_commit","package_sha256","archive_sha256","extracted_tree_sha256","build_manifest_sha256","registry_sha256","paired_protocol_core_sha256","protocol_authorization_sha256","gpt_child_authorization_sha256","opus_child_authorization_sha256","gpt_candidate_id","opus_candidate_id","gpt_candidate_record_sha256","opus_candidate_record_sha256","gpt_child_cycle_id","opus_child_cycle_id","gpt_child_protocol_sha256","opus_child_protocol_sha256","gpt_subject_ids","opus_subject_ids","gpt_case_ids","opus_case_ids","gpt_output_sha256s","opus_output_sha256s"}
    if not isinstance(value,dict) or set(value)!=required or value.get("schema")!="campaign-usage-fake-paired-parent-authorization-v1" or value.get("test_only") is not True or value.get("live_execution_authorized") is not False or value.get("cohort")!=cohort:raise ValueError("usage_binding: paired cohort requires an exact test-only parent authorization")
    for field in ("parent_id","gpt_candidate_id","opus_candidate_id"):_text(value.get(field),field)
    if value["gpt_candidate_id"]==value["opus_candidate_id"]:raise ValueError("usage_binding: paired sibling candidates must be distinct")
    if not isinstance(value.get("source_commit"),str) or re.fullmatch(r"[a-f0-9]{40}",value["source_commit"]) is None:raise ValueError("usage_binding: paired source commit is invalid")
    for field in ("package_sha256","archive_sha256","extracted_tree_sha256","build_manifest_sha256","registry_sha256","paired_protocol_core_sha256","protocol_authorization_sha256","gpt_child_authorization_sha256","opus_child_authorization_sha256","gpt_candidate_record_sha256","opus_candidate_record_sha256","gpt_child_protocol_sha256","opus_child_protocol_sha256"):_sha(value.get(field),field)
    for field in ("gpt_child_cycle_id","opus_child_cycle_id"):_text(value.get(field),field)
    for field in ("gpt_subject_ids","opus_subject_ids"):
        subjects=value.get(field)
        if not isinstance(subjects,list) or len(subjects)!=5 or any(not isinstance(item,str) or not item for item in subjects) or len(set(subjects))!=5:raise ValueError(f"usage_binding: {field} must contain exact unique subjects")
    if set(value["gpt_subject_ids"])&set(value["opus_subject_ids"]):raise ValueError("usage_binding: paired sibling subjects must be disjoint")
    canonical_cases=[row["case_id"] for row in load_registry()["cases"]]
    if value.get("gpt_case_ids")!=canonical_cases or value.get("opus_case_ids")!=canonical_cases:raise ValueError("usage_binding: paired siblings must each bind the exact canonical five cases")
    for field in ("gpt_output_sha256s","opus_output_sha256s"):
        outputs=value.get(field)
        if not isinstance(outputs,list) or len(outputs)!=5 or any(item is not None and (not isinstance(item,str) or re.fullmatch(r"[a-f0-9]{64}",item) is None) for item in outputs):raise ValueError(f"usage_binding: {field} must be exact hash-or-null rows")
    return value


def _authorization_lexical_path(root: Path, path: Path, label: str) -> Path:
    root_abs=Path(os.path.abspath(root));path_abs=Path(os.path.abspath(path))
    try:relative=path_abs.relative_to(root_abs)
    except ValueError as exc:raise ValueError(f"usage_binding: {label} must be lexically contained in the ledger custody root") from exc
    current=root_abs
    for part in (Path("."),*relative.parts):
        if part!=Path("."):current=current/part
        try:stat=current.lstat()
        except OSError as exc:raise ValueError(f"usage_binding: {label} lexical component is unavailable") from exc
        if current.is_symlink() or bool(getattr(stat,"st_file_attributes",0)&0x400):raise ValueError(f"usage_binding: {label} lexical path traverses symlink/reparse component")
    return path_abs


def _read_fake_authorization(root: Path, path: Path|None, expected_sha256: str|None, label: str) -> tuple[dict,tuple[Path,bytes,str,str]]:
    if not isinstance(path,Path) or not isinstance(expected_sha256,str):raise ValueError(f"usage_binding: externally supplied {label} path/hash is required")
    _sha(expected_sha256,f"{label}_sha256")
    lexical=_authorization_lexical_path(root,path,label);resolved_root=root.resolve(strict=True)
    try:resolved=path.resolve(strict=True);resolved.relative_to(resolved_root)
    except (OSError,ValueError) as exc:raise ValueError(f"usage_binding: {label} must be contained in the ledger custody root") from exc
    if resolved.is_symlink() or bool(getattr(resolved.lstat(),"st_file_attributes",0)&0x400):raise ValueError(f"usage_binding: {label} cannot be symlink/reparse")
    raw=resolved.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError(f"usage_binding: {label} external content address mismatch")
    try:value=json.loads(raw)
    except json.JSONDecodeError as exc:raise ValueError(f"usage_binding: {label} is not JSON") from exc
    if not isinstance(value,dict) or raw!=_canonical(value):raise ValueError(f"usage_binding: {label} must be canonical JSON")
    return value,(lexical,raw,expected_sha256,label)


def _verify_authorization_snapshots(root: Path, snapshots: list[tuple[Path,bytes,str,str]]) -> None:
    for path,expected_raw,expected_sha,label in snapshots:
        lexical=_authorization_lexical_path(root,path,label)
        current=lexical.read_bytes()
        if current!=expected_raw or hashlib.sha256(current).hexdigest()!=expected_sha:raise ValueError(f"usage_authorization_toctou: {label} bytes drifted before transaction publication")


def _finalize_quarantine_intake(root: Path, intake_dir: Path, expected_sha: str, label: str) -> None:
    """Content-address a private collision intake before removing its last copy."""
    quarantine_root=root/"quarantine"/"authorization-custody"
    _authorization_lexical_path(root,intake_dir,f"{label}_quarantine_intake")
    if not intake_dir.is_dir() or re.fullmatch(rf"\.{re.escape(expected_sha)}\.intake-[A-Za-z0-9_-]+",intake_dir.name) is None:raise ValueError(f"usage_authorization_custody_quarantine_intake: {label} intake identity differs")
    entries=list(intake_dir.iterdir())
    if not entries:
        intake_dir.rmdir();return
    if len(entries)!=1 or entries[0].name!="collision.bin" or not entries[0].is_file():raise ValueError(f"usage_authorization_custody_quarantine_intake: {label} intake shape differs")
    intake=_authorization_lexical_path(root,entries[0],f"{label}_quarantine_intake_bytes")
    raw=intake.read_bytes();actual_sha=hashlib.sha256(raw).hexdigest();quarantine=quarantine_root/f"{expected_sha}.{actual_sha}.json"
    if quarantine.exists():
        _authorization_lexical_path(root,quarantine,f"{label}_quarantine")
        if quarantine.read_bytes()!=raw:raise ValueError(f"usage_authorization_custody_quarantine_collision: {label} quarantine bytes differ")
    else:
        try:atomic_publish_bytes(quarantine,raw)
        except PublicationError as exc:raise ValueError(f"usage_authorization_custody_quarantine_collision: {label} quarantine destination exists") from exc
    if quarantine.read_bytes()!=raw:raise ValueError(f"usage_authorization_custody_quarantine_readback: {label} bytes were not preserved")
    intake.unlink();intake_dir.rmdir()


def _recover_quarantine_intakes(root: Path, expected_sha: str, label: str) -> None:
    quarantine_root=root/"quarantine"/"authorization-custody"
    if not quarantine_root.exists():return
    _authorization_lexical_path(root,quarantine_root,f"{label}_quarantine_root")
    for intake_dir in sorted(quarantine_root.glob(f".{expected_sha}.intake-*")):
        _finalize_quarantine_intake(root,intake_dir,expected_sha,label)


def _quarantine_custody_collision(root: Path, path: Path, expected_sha: str, label: str) -> None:
    """Atomically remove a collision from its live address before classifying it."""
    path=_authorization_lexical_path(root,path,f"{label}_collision")
    quarantine_root=root/"quarantine"/"authorization-custody";quarantine_root.mkdir(parents=True,exist_ok=True);_authorization_lexical_path(root,quarantine_root,f"{label}_quarantine_root")
    intake_dir=Path(tempfile.mkdtemp(prefix=f".{expected_sha}.intake-",dir=quarantine_root));intake=intake_dir/"collision.bin"
    try:
        os.replace(path,intake)
    except OSError as exc:
        intake_dir.rmdir();raise ValueError(f"usage_authorization_custody_quarantine_transfer: {label} collision was not atomically moved") from exc
    _finalize_quarantine_intake(root,intake_dir,expected_sha,label)


def _quarantine_drifted_custody(root: Path, refs: list[dict]) -> None:
    for row in refs:
        path=root/row["path"]
        if path.is_file() and path.read_bytes()!=_canonical(row["record"]):
            _quarantine_custody_collision(root,path,row["sha256"],row["role"])


def _transfer_authorization_custody(root: Path, snapshots: list[tuple[Path,bytes,str,str]]) -> list[dict]:
    """Materialize exact inputs while embedding their authority in the transaction."""
    verified=[]
    for path,expected_raw,expected_sha,label in snapshots:
        lexical=_authorization_lexical_path(root,path,label);current=lexical.read_bytes()
        if current!=expected_raw or hashlib.sha256(current).hexdigest()!=expected_sha:raise ValueError(f"usage_authorization_toctou: {label} bytes drifted before immutable custody transfer")
        verified.append((expected_raw,expected_sha,label))
    refs=[]
    for raw,digest,label in verified:
        record=json.loads(raw)
        _recover_quarantine_intakes(root,digest,label)
        relative=f"authorization-custody/{digest}.json";destination=root/relative
        destination.parent.mkdir(parents=True,exist_ok=True);_authorization_lexical_path(root,destination.parent,f"{label}_custody_parent")
        if destination.exists():
            _authorization_lexical_path(root,destination,f"{label}_custody")
            if destination.read_bytes()!=raw:
                _quarantine_custody_collision(root,destination,digest,label)
            else:
                refs.append({"role":label,"path":relative,"sha256":digest,"record":record});continue
        try:atomic_publish_bytes(destination,raw)
        except PublicationError as exc:raise ValueError(f"usage_authorization_custody_exists: immutable {label} destination already exists") from exc
        readback=destination.read_bytes()
        if readback!=raw or hashlib.sha256(readback).hexdigest()!=digest:raise ValueError(f"usage_authorization_custody_readback: immutable {label} bytes did not hash-read back")
        refs.append({"role":label,"path":relative,"sha256":digest,"record":record})
    return refs


def _validate_authorization_custody(root: Path, tx: dict, *, materialized: bool=False) -> None:
    refs=tx.get("authorization_custody")
    paired=tx.get("cohort") in {"paired-producer","paired-review"}
    if not paired:
        if refs!=[]:raise ValueError("usage_authorization_custody_binding: non-paired transaction cannot carry paired authority custody")
        return
    parent=tx.get("paired_parent_contract")
    expected={"outer_parent_authorization":tx.get("authorization_sha256"),"paired_protocol_authorization":parent.get("protocol_authorization_sha256") if isinstance(parent,dict) else None,"gpt_child_authorization":parent.get("gpt_child_authorization_sha256") if isinstance(parent,dict) else None,"opus_child_authorization":parent.get("opus_child_authorization_sha256") if isinstance(parent,dict) else None}
    if not isinstance(refs,list) or len(refs)!=4 or {row.get("role") for row in refs if isinstance(row,dict)}!=set(expected):raise ValueError("usage_authorization_custody_binding: exact four authorization custody roles are required")
    records={}
    for row in refs:
        if not isinstance(row,dict) or set(row)!={"role","path","sha256","record"} or row.get("sha256")!=expected[row.get("role")]:raise ValueError("usage_authorization_custody_binding: custody role/hash differs from transaction authority")
        digest=_sha(row.get("sha256"),"authorization_custody_sha256");relative=f"authorization-custody/{digest}.json"
        if row.get("path")!=relative:raise ValueError("usage_authorization_custody_binding: custody path is not its content address")
        value=row.get("record")
        if not isinstance(value,dict) or hashlib.sha256(_canonical(value)).hexdigest()!=digest:raise ValueError("usage_authorization_custody_content_address: transaction-embedded custody differs from its authority hash")
        records[row["role"]]=value
        if materialized:
            path=_authorization_lexical_path(root,root/relative,"authorization_custody");raw=path.read_bytes()
            if raw!=_canonical(value) or hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("usage_authorization_custody_content_address: materialized custody bytes drifted before reservation publication")
    outer=records["outer_parent_authorization"];protocol=records["paired_protocol_authorization"];gpt=records["gpt_child_authorization"];opus=records["opus_child_authorization"]
    schemas=((outer,"campaign-usage-fake-outer-parent-authorization-v1"),(protocol,"campaign-usage-fake-paired-protocol-authorization-v1"),(gpt,"campaign-usage-fake-gpt-child-authorization-v1"),(opus,"campaign-usage-fake-opus-child-authorization-v1"))
    if any(record.get("schema")!=schema or record.get("deterministic_fake_only") is not True or record.get("live_execution_authorized") is not False for record,schema in schemas):raise ValueError("usage_authorization_custody_binding: embedded authority is not exact fake-only custody")
    if protocol.get("outer_parent_authorization_sha256")!=tx.get("authorization_sha256") or outer.get("paired_protocol_core_sha256")!=_digest({key:value for key,value in protocol.items() if key!="outer_parent_authorization_sha256"}):raise ValueError("usage_authorization_custody_binding: outer/protocol authority join differs")
    if protocol.get("gpt_child_authorization_sha256")!=expected["gpt_child_authorization"] or protocol.get("opus_child_authorization_sha256")!=expected["opus_child_authorization"]:raise ValueError("usage_authorization_custody_binding: protocol child authority join differs")
    shared=("source_commit","package_sha256","archive_sha256","extracted_tree_sha256","build_manifest_sha256","registry_sha256")
    if any(record.get(field)!=parent.get(field) for record in (outer,protocol,gpt,opus) for field in shared):raise ValueError("usage_authorization_custody_binding: embedded shared custody differs from paired parent")
    outer_parent_fields=("parent_id","cohort","gpt_child_authorization_sha256","opus_child_authorization_sha256","gpt_candidate_id","opus_candidate_id","gpt_candidate_record_sha256","opus_candidate_record_sha256","gpt_child_cycle_id","opus_child_cycle_id","gpt_child_protocol_sha256","opus_child_protocol_sha256","gpt_subject_ids","opus_subject_ids","gpt_case_ids","opus_case_ids","gpt_output_sha256s","opus_output_sha256s")
    if any(outer.get(field)!=parent.get(field) for field in outer_parent_fields):raise ValueError("usage_authorization_custody_binding: embedded outer authority differs from paired parent")
    for child,prefix in ((gpt,"gpt"),(opus,"opus")):
        joins=(("parent_id","parent_id"),("candidate_id",f"{prefix}_candidate_id"),("candidate_record_sha256",f"{prefix}_candidate_record_sha256"),("child_cycle_id",f"{prefix}_child_cycle_id"),("child_protocol_sha256",f"{prefix}_child_protocol_sha256"),("subject_ids",f"{prefix}_subject_ids"),("case_ids",f"{prefix}_case_ids"),("output_sha256s",f"{prefix}_output_sha256s"))
        if any(child.get(child_field)!=parent.get(parent_field) for child_field,parent_field in joins):raise ValueError(f"usage_authorization_custody_binding: embedded {prefix} child differs from paired parent")
    opus_contract=tx.get("paired_opus_contract")
    if opus_contract is not None and any(opus.get(field)!=opus_contract.get(field) for field in ("candidate_id","model","reasoning_effort","protocol","settings","subject_ids")):raise ValueError("usage_authorization_custody_binding: embedded Opus execution contract differs")


def _load_paired_authorizations(root: Path, cohort: str, parent_id: str, subjects: list[str], authorization_sha256: str, *, outer_path: Path|None, protocol_path: Path|None, protocol_sha256: str|None, gpt_path: Path|None, gpt_sha256: str|None, opus_path: Path|None, opus_sha256: str|None) -> tuple[dict,dict|None,list[tuple[Path,bytes,str,str]]]:
    outer,outer_snapshot=_read_fake_authorization(root,outer_path,authorization_sha256,"outer_parent_authorization");protocol,protocol_snapshot=_read_fake_authorization(root,protocol_path,protocol_sha256,"paired_protocol_authorization");gpt,gpt_snapshot=_read_fake_authorization(root,gpt_path,gpt_sha256,"gpt_child_authorization");opus,opus_snapshot=_read_fake_authorization(root,opus_path,opus_sha256,"opus_child_authorization")
    shared=("source_commit","package_sha256","archive_sha256","extracted_tree_sha256","build_manifest_sha256","registry_sha256")
    protocol_required={"schema","deterministic_fake_only","live_execution_authorized","parent_id","cohort","outer_parent_authorization_sha256",*shared,"gpt_child_authorization_sha256","opus_child_authorization_sha256"}
    outer_required={"schema","deterministic_fake_only","live_execution_authorized","parent_id","cohort","paired_protocol_core_sha256",*shared,"gpt_child_authorization_sha256","opus_child_authorization_sha256","gpt_candidate_id","opus_candidate_id","gpt_candidate_record_sha256","opus_candidate_record_sha256","gpt_child_cycle_id","opus_child_cycle_id","gpt_child_protocol_sha256","opus_child_protocol_sha256","gpt_subject_ids","opus_subject_ids","gpt_case_ids","opus_case_ids","gpt_output_sha256s","opus_output_sha256s"}
    child_common={"schema","deterministic_fake_only","live_execution_authorized","parent_id","child_cycle_id","candidate_id","candidate_record_sha256",*shared,"child_protocol_sha256","subject_ids","case_ids","output_sha256s"}
    if set(outer)!=outer_required or outer.get("schema")!="campaign-usage-fake-outer-parent-authorization-v1" or set(protocol)!=protocol_required or protocol.get("schema")!="campaign-usage-fake-paired-protocol-authorization-v1" or set(gpt)!=child_common or gpt.get("schema")!="campaign-usage-fake-gpt-child-authorization-v1":raise ValueError("usage_binding: outer parent/protocol/GPT child authorization shape mismatch")
    opus_required=child_common|{"model","reasoning_effort","protocol","settings"}
    if set(opus)!=opus_required or opus.get("schema")!="campaign-usage-fake-opus-child-authorization-v1":raise ValueError("usage_binding: Opus child authorization shape mismatch")
    for record in (outer,protocol,gpt,opus):
        if record.get("deterministic_fake_only") is not True or record.get("live_execution_authorized") is not False or record.get("parent_id")!=parent_id:raise ValueError("usage_binding: paired authorization is not exact fake-only parent custody")
    protocol_core={key:value for key,value in protocol.items() if key!="outer_parent_authorization_sha256"}
    if protocol.get("cohort")!=cohort or protocol.get("outer_parent_authorization_sha256")!=authorization_sha256 or outer.get("paired_protocol_core_sha256")!=_digest(protocol_core) or protocol.get("gpt_child_authorization_sha256")!=gpt_sha256 or protocol.get("opus_child_authorization_sha256")!=opus_sha256:raise ValueError("usage_binding: paired protocol does not bind exact outer parent authority and external child authorizations")
    outer_exact={"parent_id":parent_id,"cohort":cohort,**{field:protocol[field] for field in shared},"gpt_child_authorization_sha256":gpt_sha256,"opus_child_authorization_sha256":opus_sha256,"gpt_candidate_id":gpt["candidate_id"],"opus_candidate_id":opus["candidate_id"],"gpt_candidate_record_sha256":gpt["candidate_record_sha256"],"opus_candidate_record_sha256":opus["candidate_record_sha256"],"gpt_child_cycle_id":gpt["child_cycle_id"],"opus_child_cycle_id":opus["child_cycle_id"],"gpt_child_protocol_sha256":gpt["child_protocol_sha256"],"opus_child_protocol_sha256":opus["child_protocol_sha256"],"gpt_subject_ids":gpt["subject_ids"],"opus_subject_ids":opus["subject_ids"],"gpt_case_ids":gpt["case_ids"],"opus_case_ids":opus["case_ids"],"gpt_output_sha256s":gpt["output_sha256s"],"opus_output_sha256s":opus["output_sha256s"]}
    if any(outer.get(field)!=value for field,value in outer_exact.items()):raise ValueError("usage_binding: outer parent authorization does not bind exact paired sibling custody")
    if protocol.get("registry_sha256")!=hashlib.sha256(DEFAULT_REGISTRY.read_bytes()).hexdigest():raise ValueError("usage_binding: paired protocol registry differs from canonical five-case registry")
    if any(gpt.get(field)!=protocol.get(field) or opus.get(field)!=protocol.get(field) for field in shared):raise ValueError("usage_binding: paired siblings do not share exact source/package/tree/build/registry custody")
    if gpt.get("candidate_id")==opus.get("candidate_id") or gpt.get("subject_ids")!=subjects[:5] or opus.get("subject_ids")!=subjects[5:]:raise ValueError("usage_binding: paired sibling candidates/subjects are not exact 5+5")
    canonical_cases=[row["case_id"] for row in load_registry()["cases"]]
    if gpt.get("case_ids")!=canonical_cases or opus.get("case_ids")!=canonical_cases:raise ValueError("usage_binding: paired child authorizations do not bind the canonical five cases")
    for child in (gpt,opus):
        outputs=child.get("output_sha256s")
        if not isinstance(outputs,list) or len(outputs)!=5 or any(item is not None and (not isinstance(item,str) or re.fullmatch(r"[a-f0-9]{64}",item) is None) for item in outputs):raise ValueError("usage_binding: child output inventory must contain exact hash-or-null rows")
    if cohort=="paired-review" and any(item is None for item in gpt["output_sha256s"]+opus["output_sha256s"]):raise ValueError("usage_binding: paired review requires exact ten producer output hashes")
    if cohort=="paired-producer" and any(item is not None for item in gpt["output_sha256s"]+opus["output_sha256s"]):raise ValueError("usage_binding: producer authorization cannot predeclare output hashes")
    parent={"schema":"campaign-usage-fake-paired-parent-authorization-v1","test_only":True,"live_execution_authorized":False,"parent_id":parent_id,"cohort":cohort,**{field:protocol[field] for field in shared},"paired_protocol_core_sha256":outer["paired_protocol_core_sha256"],"protocol_authorization_sha256":protocol_sha256,"gpt_child_authorization_sha256":gpt_sha256,"opus_child_authorization_sha256":opus_sha256,"gpt_candidate_id":gpt["candidate_id"],"opus_candidate_id":opus["candidate_id"],"gpt_candidate_record_sha256":gpt["candidate_record_sha256"],"opus_candidate_record_sha256":opus["candidate_record_sha256"],"gpt_child_cycle_id":gpt["child_cycle_id"],"opus_child_cycle_id":opus["child_cycle_id"],"gpt_child_protocol_sha256":gpt["child_protocol_sha256"],"opus_child_protocol_sha256":opus["child_protocol_sha256"],"gpt_subject_ids":gpt["subject_ids"],"opus_subject_ids":opus["subject_ids"],"gpt_case_ids":gpt["case_ids"],"opus_case_ids":opus["case_ids"],"gpt_output_sha256s":gpt["output_sha256s"],"opus_output_sha256s":opus["output_sha256s"]}
    opus_unsigned={"schema":"campaign-usage-fake-opus-child-authorization-v1","test_only":True,"parent_id":parent_id,"parent_authorization_sha256":protocol_sha256,"candidate_id":opus["candidate_id"],"cohort":cohort,"package_sha256":protocol["package_sha256"],"archive_sha256":protocol["archive_sha256"],"extracted_tree_sha256":protocol["extracted_tree_sha256"],"registry_sha256":protocol["registry_sha256"],"model":opus["model"],"reasoning_effort":opus["reasoning_effort"],"protocol":opus["protocol"],"settings":opus["settings"],"subject_ids":opus["subject_ids"]}
    return parent,{**opus_unsigned,"authorization_sha256":_digest(opus_unsigned)} if cohort=="paired-producer" else None,[outer_snapshot,protocol_snapshot,gpt_snapshot,opus_snapshot]


def _opus_contract(value: object, cohort: str) -> dict|None:
    if cohort!="paired-producer":
        if value is not None:raise ValueError("usage_binding: separate Opus contract is valid only for paired-producer")
        return None
    required={"schema","test_only","parent_id","parent_authorization_sha256","candidate_id","cohort","package_sha256","archive_sha256","extracted_tree_sha256","registry_sha256","model","reasoning_effort","protocol","settings","subject_ids","authorization_sha256"}
    if not isinstance(value,dict) or set(value)!=required or value.get("schema")!="campaign-usage-fake-opus-child-authorization-v1" or value.get("test_only") is not True or value.get("cohort")!=cohort or value.get("protocol")!=COHORT_PROTOCOLS[cohort] or not isinstance(value.get("candidate_id"),str) or not value["candidate_id"] or not isinstance(value.get("model"),str) or not value["model"] or not isinstance(value.get("reasoning_effort"),str) or not value["reasoning_effort"] or not isinstance(value.get("settings"),dict):raise ValueError("usage_binding: paired producer requires an exact separately authorized test-only Opus model/settings contract")
    for field in ("parent_authorization_sha256","package_sha256","archive_sha256","extracted_tree_sha256","registry_sha256"):_sha(value.get(field),f"paired_opus_{field}")
    subjects=value.get("subject_ids")
    if not isinstance(subjects,list) or len(subjects)!=5 or len(set(subjects))!=5 or any(not isinstance(item,str) or not item for item in subjects):raise ValueError("usage_binding: paired Opus authorization requires exact unique subjects")
    supplied=_sha(value.get("authorization_sha256"),"paired_opus_authorization_sha256")
    unsigned={key:item for key,item in value.items() if key!="authorization_sha256"}
    if supplied!=_digest(unsigned):raise ValueError("usage_binding: paired Opus authorization content address does not bind exact subjects/model/settings")
    return value


def _make_call_contract(cohort: str, reserved_calls: int, subject_ids: list[str]|None=None, paired_opus_contract: dict|None=None, paired_parent_contract: dict|None=None, candidate_id: str|None=None) -> list[dict]:
    if not isinstance(subject_ids,list):raise ValueError("usage_binding: explicit call subject manifest must be a list")
    subjects=subject_ids
    if len(subjects)!=reserved_calls or any(not isinstance(item,str) or not item for item in subjects) or len(subjects)!=len(set(subjects)):raise ValueError("usage_binding: call subject manifest must contain exact unique identities")
    parent=_paired_parent_contract(paired_parent_contract,cohort);opus=_opus_contract(paired_opus_contract,cohort);models=[];efforts=[];candidates=[];child_cycles=[];child_protocols=[];case_ids=[];output_hashes=[]
    if parent is not None:
        if candidate_id!=parent["parent_id"] or subjects!=parent["gpt_subject_ids"]+parent["opus_subject_ids"]:raise ValueError("usage_binding: paired parent/candidate/subject inventory mismatch")
        if cohort=="paired-producer":
            opus_exact={"parent_id":parent["parent_id"],"parent_authorization_sha256":parent["protocol_authorization_sha256"],"candidate_id":parent["opus_candidate_id"],"package_sha256":parent["package_sha256"],"archive_sha256":parent["archive_sha256"],"extracted_tree_sha256":parent["extracted_tree_sha256"],"registry_sha256":parent["registry_sha256"],"subject_ids":parent["opus_subject_ids"]}
            if opus is None or any(opus.get(field)!=value for field,value in opus_exact.items()):raise ValueError("usage_binding: Opus child contract differs from externally anchored parent/sibling custody")
        candidates=[parent["gpt_candidate_id"]]*5+[parent["opus_candidate_id"]]*5
        child_cycles=[parent["gpt_child_cycle_id"]]*5+[parent["opus_child_cycle_id"]]*5
        child_protocols=[parent["gpt_child_protocol_sha256"]]*5+[parent["opus_child_protocol_sha256"]]*5
        case_ids=parent["gpt_case_ids"]+parent["opus_case_ids"]
        output_hashes=parent["gpt_output_sha256s"]+parent["opus_output_sha256s"]
    else:
        _text(candidate_id,"candidate_id");candidates=[candidate_id]*reserved_calls;child_cycles=[None]*reserved_calls;child_protocols=[None]*reserved_calls;case_ids=[None]*reserved_calls;output_hashes=[None]*reserved_calls
    for index in range(reserved_calls):
        if cohort=="paired-producer" and index>=reserved_calls//2:
            if subjects[index]!=opus["subject_ids"][index-reserved_calls//2]:raise ValueError("usage_binding: paired Opus subject differs from child authorization")
            models.append(opus["model"]);efforts.append(opus["reasoning_effort"])
        elif cohort in {"gpt-review","paired-review"}:models.append("gpt-5.6-sol");efforts.append("xhigh")
        else:models.append("gpt-5.5");efforts.append("high")
    return [{"parent_id":parent["parent_id"] if parent else None,"child_cycle_id":child_cycle,"candidate_id":candidate,"child_protocol_sha256":child_protocol,"case_id":case_id,"subject_id":subject,"subject_output_sha256":output_hash,"model":model,"reasoning_effort":effort,"protocol":COHORT_PROTOCOLS[cohort]} for child_cycle,candidate,child_protocol,case_id,subject,output_hash,model,effort in zip(child_cycles,candidates,child_protocols,case_ids,subjects,output_hashes,models,efforts)]


def _validate_call_contract(value: object, cohort: str, reserved_calls: int, paired_opus_contract: dict|None, paired_parent_contract: dict|None, candidate_id: str) -> list[dict]:
    if not isinstance(value,list) or len(value)!=reserved_calls:raise ValueError("usage_binding: exact cohort call contract is required")
    expected=_make_call_contract(cohort,reserved_calls,[row.get("subject_id") if isinstance(row,dict) else None for row in value],paired_opus_contract,paired_parent_contract,candidate_id)
    if value!=expected:raise ValueError("usage_binding: subject/model/effort/protocol contract differs from exact cohort manifest")
    return value


def _provider_facts(rows: object, *, candidate_id: str, batch_id: str, cohort: str, reserved_calls: int, call_contract: list[dict], paired_opus_contract: dict|None, paired_parent_contract: dict|None=None) -> tuple[dict[str,int],dict]:
    if not isinstance(rows,list) or len(rows)!=reserved_calls:raise ValueError("usage_provider_metadata: exactly one provider row per reserved call is required")
    expected_ids=[f"{batch_id}:call-{index:02d}" for index in range(1,reserved_calls+1)]
    contract=_validate_call_contract(call_contract,cohort,reserved_calls,paired_opus_contract,paired_parent_contract,candidate_id)
    statuses=[];cost_values=[];cost_records=[];subjects=[];provider_ids=[];host_ids=[];attempted=accepted_count=in_flight_count=0
    for index,(row,call_id,authorized) in enumerate(zip(rows,expected_ids,contract),1):
        required={"call_id","parent_id","child_cycle_id","candidate_id","child_protocol_sha256","cycle_or_review_batch_id","case_id","subject_id","subject_output_sha256","model","reasoning_effort","protocol","started_at","ended_at","host_invocation_id","accepted","in_flight","status","unknown_kind","acknowledgment_origin","terminal_transport_status","provider_call_id","usage","cost"}
        if not isinstance(row,dict) or set(row)!=required:raise ValueError(f"usage_provider_metadata: provider row {index} has wrong shape")
        if row.get("call_id")!=call_id or row.get("candidate_id")!=authorized["candidate_id"] or row.get("cycle_or_review_batch_id")!=batch_id:raise ValueError(f"usage_provider_metadata: provider row {index} identity binding mismatch")
        subject=row.get("subject_id")
        if {field:row.get(field) for field in ("parent_id","child_cycle_id","candidate_id","child_protocol_sha256","case_id","subject_id","subject_output_sha256","model","reasoning_effort","protocol") }!=authorized:raise ValueError(f"usage_provider_metadata: provider row {index} parent/child/candidate/case/subject/output/model/protocol differs from reservation contract")
        subjects.append(subject)
        status=row.get("status")
        if status not in CALL_STATUSES:raise ValueError(f"usage_provider_metadata: provider row {index} status is invalid")
        transport=row.get("terminal_transport_status")
        if transport not in TRANSPORT_STATUSES:raise ValueError(f"usage_provider_metadata: provider row {index} terminal transport status is invalid")
        unknown_kind=row.get("unknown_kind")
        if status=="UNKNOWN" and unknown_kind not in {"DISPATCH_UNKNOWN","OUTCOME_UNKNOWN"}:raise ValueError(f"usage_provider_metadata: unknown row {index} requires an exact evidence discriminator")
        if status!="UNKNOWN" and unknown_kind is not None:raise ValueError(f"usage_provider_metadata: non-unknown row {index} cannot carry unknown_kind")
        started,ended=row.get("started_at"),row.get("ended_at")
        timestamp_pattern=r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
        if started is not None and (not isinstance(started,str) or re.fullmatch(timestamp_pattern,started) is None):raise ValueError(f"usage_provider_metadata: provider row {index} started_at is invalid")
        if ended is not None and (not isinstance(ended,str) or re.fullmatch(timestamp_pattern,ended) is None):raise ValueError(f"usage_provider_metadata: provider row {index} ended_at is invalid")
        if started is not None and ended is not None and ended<started:raise ValueError(f"usage_provider_metadata: provider row {index} timing is reversed")
        if ended is not None and started is None:raise ValueError(f"usage_provider_metadata: provider row {index} ended_at requires started_at")
        host_id=row.get("host_invocation_id")
        if host_id is not None and (not isinstance(host_id,str) or not host_id):raise ValueError(f"usage_provider_metadata: provider row {index} host invocation id is invalid")
        if host_id is not None:host_ids.append(host_id)
        accepted,in_flight=row.get("accepted"),row.get("in_flight")
        if not (isinstance(accepted,bool) or accepted is None) or not (isinstance(in_flight,bool) or in_flight is None):raise ValueError(f"usage_provider_metadata: provider row {index} accepted/in-flight shape is invalid")
        origin=row.get("acknowledgment_origin")
        if origin not in ACK_ORIGINS:raise ValueError(f"usage_provider_metadata: provider row {index} acknowledgment origin is invalid")
        origin_shape={"NONE":accepted in {None,False} and in_flight in {None,False},"PROVIDER_ACCEPTED":accepted is True and in_flight in {None,False},"ADAPTER_IN_FLIGHT":accepted is None and in_flight in {True,False},"BOTH":accepted is True and in_flight is True}[origin]
        if origin=="ADAPTER_IN_FLIGHT" and status=="COMPLETED" and in_flight is not False:raise ValueError(f"usage_provider_metadata: provider row {index} must clear adapter in-flight state after terminal completion")
        if not origin_shape:raise ValueError(f"usage_provider_metadata: provider row {index} acknowledgment facts contradict their origin")
        if status in {"COMPLETED","FAILED","CANCELLED"} and (origin=="NONE" or started is None or ended is None):raise ValueError(f"usage_provider_metadata: dispatched row {index} requires positive acknowledgment timing")
        if status=="NOT_DISPATCHED" and (accepted is not False or in_flight is not False or started is not None or ended is not None):raise ValueError(f"usage_provider_metadata: proved-zero row {index} has contradictory transport evidence")
        compatible={"COMPLETED":{"COMPLETED"},"FAILED":{"FAILED","TIMEOUT","CONNECTION_LOST"},"CANCELLED":{"CANCELLED"},"NOT_DISPATCHED":{"NOT_STARTED"},"UNKNOWN":{"UNKNOWN","TIMEOUT","CONNECTION_LOST"} if unknown_kind=="DISPATCH_UNKNOWN" else {"PROVIDER_ACCEPTED","ADAPTER_IN_FLIGHT","IN_FLIGHT","TIMEOUT","CONNECTION_LOST","UNKNOWN"}}
        if transport not in compatible[status]:raise ValueError(f"usage_provider_metadata: provider row {index} transport/outcome combination is incompatible")
        provider_id=row.get("provider_call_id")
        if provider_id is not None and (not isinstance(provider_id,str) or not provider_id):raise ValueError(f"usage_provider_metadata: provider row {index} provider_call_id is invalid")
        if provider_id is not None:provider_ids.append(provider_id)
        usage=row.get("usage")
        if status in {"COMPLETED","FAILED","CANCELLED"} and (not isinstance(provider_id,str) or not provider_id):raise ValueError(f"usage_provider_metadata: dispatched row {index} requires provider_call_id")
        if status=="NOT_DISPATCHED" and provider_id is not None:raise ValueError(f"usage_provider_metadata: not-dispatched row {index} cannot name provider_call_id")
        if not isinstance(usage,dict) or usage.get("status") not in {"RECORDED","UNAVAILABLE"}:raise ValueError(f"usage_provider_metadata: provider row {index} usage is invalid")
        if usage.get("status")=="RECORDED":
            if set(usage) not in ({"status","input_tokens","output_tokens","total_tokens"},{"status","input_tokens","cached_input_tokens","output_tokens","total_tokens"}):raise ValueError(f"usage_provider_metadata: recorded usage row {index} has wrong shape")
            token_values=[usage[name] for name in ("input_tokens","output_tokens","total_tokens")]
            if any(not isinstance(item,int) or isinstance(item,bool) or item<0 for item in token_values) or usage["total_tokens"]!=usage["input_tokens"]+usage["output_tokens"]:raise ValueError(f"usage_provider_metadata: provider row {index} token arithmetic mismatch")
            if "cached_input_tokens" in usage and (not isinstance(usage["cached_input_tokens"],int) or isinstance(usage["cached_input_tokens"],bool) or usage["cached_input_tokens"]<0 or usage["cached_input_tokens"]>usage["input_tokens"]):raise ValueError(f"usage_provider_metadata: provider row {index} cached token usage is invalid")
        elif set(usage)!={"status"}:raise ValueError(f"usage_provider_metadata: unavailable usage row {index} has wrong shape")
        cost=_cost(row.get("cost"),f"provider row {index} cost");cost_values.append(cost["value"]);cost_records.append(cost);statuses.append(status)
        if status=="NOT_DISPATCHED" and (usage!={"status":"UNAVAILABLE"} or cost["value"]!="0"):raise ValueError(f"usage_provider_metadata: proved not-dispatched row {index} requires unavailable usage and zero cost")
        if status=="UNKNOWN" and usage.get("status")!="UNAVAILABLE":raise ValueError(f"usage_provider_metadata: unknown row {index} must explicitly mark usage unavailable")
        if status=="UNKNOWN":
            if accepted is False or (in_flight is False and origin!="ADAPTER_IN_FLIGHT"):raise ValueError(f"usage_provider_metadata: unknown row {index} cannot contradict or manufacture dispatch evidence")
            if cost["value"]!="unknown":raise ValueError(f"usage_provider_metadata: unknown row {index} must explicitly mark cost unavailable")
            if unknown_kind=="DISPATCH_UNKNOWN" and any(value is not None for value in (accepted,in_flight,started,ended,host_id,provider_id)):raise ValueError(f"usage_provider_metadata: dispatch-unknown row {index} cannot manufacture transport evidence")
        positive=origin!="NONE"
        if status=="UNKNOWN" and unknown_kind=="OUTCOME_UNKNOWN" and not positive:raise ValueError(f"usage_provider_metadata: outcome-unknown row {index} requires positive dispatch evidence")
        attempted+=int(positive);accepted_count+=int(accepted is True);in_flight_count+=int(in_flight is True)
    if len(subjects)!=len(set(subjects)):raise ValueError("usage_provider_metadata: call subject identities must be unique")
    if len(provider_ids)!=len(set(provider_ids)) or len(host_ids)!=len(set(host_ids)):raise ValueError("usage_provider_metadata: provider and host invocation identities must be unique")
    counts={"completed":statuses.count("COMPLETED"),"failed":statuses.count("FAILED"),"cancelled":statuses.count("CANCELLED"),"not_dispatched":statuses.count("NOT_DISPATCHED"),"unknown":statuses.count("UNKNOWN")}
    counts.update({"attempted":attempted,"accepted":accepted_count,"in_flight":in_flight_count})
    dispatch_unknown=sum(row["status"]=="UNKNOWN" and row["unknown_kind"]=="DISPATCH_UNKNOWN" for row in rows);outcome_unknown=counts["unknown"]-dispatch_unknown
    if attempted+counts["not_dispatched"]+dispatch_unknown!=reserved_calls or counts["completed"]+counts["failed"]+counts["cancelled"]+outcome_unknown!=attempted:raise ValueError("usage_arithmetic: reservation partition or proved-attempt outcome partition is inconsistent")
    aggregate="unknown" if "unknown" in cost_values else format(sum((Decimal(item) for item in cost_values),Decimal("0")),"f")
    if "." in aggregate:aggregate=aggregate.rstrip("0").rstrip(".") or "0"
    if aggregate=="unknown":
        unknown_records=[record for record in cost_records if record["value"]=="unknown"]
        if unknown_records and all(set(record)=={"unit","value","status","reason","source"} and record==unknown_records[0] for record in unknown_records):return counts,dict(unknown_records[0])
    return counts,{"unit":"usd","value":aggregate}


def _merge_cost(left: dict, right: dict) -> dict:
    _cost(left);_cost(right)
    if "unknown" in {left["value"],right["value"]}:
        governed=[value for value in (left,right) if value["value"]=="unknown" and set(value)=={"unit","value","status","reason","source"}]
        if governed and all(value==governed[0] for value in governed):return dict(governed[0])
        return {"unit":"usd","value":"unknown"}
    value=format(Decimal(left["value"])+Decimal(right["value"]),"f")
    if "." in value:value=value.rstrip("0").rstrip(".") or "0"
    return {"unit":"usd","value":value}


def _unknown_rows(reservation: dict) -> list[dict]:
    return [{"call_id":f"{reservation['cycle_or_review_batch_id']}:call-{index:02d}","candidate_id":reservation["candidate_id"],"cycle_or_review_batch_id":reservation["cycle_or_review_batch_id"],**authorized,"started_at":None,"ended_at":None,"host_invocation_id":None,"accepted":None,"in_flight":None,"status":"UNKNOWN","unknown_kind":"DISPATCH_UNKNOWN","acknowledgment_origin":"NONE","terminal_transport_status":"UNKNOWN","provider_call_id":None,"usage":{"status":"UNAVAILABLE"},"cost":{"unit":"usd","value":"unknown"}} for index,authorized in enumerate(reservation["call_contract"],1)]


def _load_recovery_evidence(root: Path, authorization: dict, reservation: dict) -> tuple[list[dict],str|None]:
    relative=authorization.get("dispatch_provider_evidence_path");expected_sha=authorization.get("dispatch_provider_evidence_sha256")
    if relative is None and expected_sha is None:return _unknown_rows(reservation),None
    if not isinstance(relative,str) or not relative or not isinstance(expected_sha,str):raise ValueError("recovery_authorization_invalid: dispatch/provider evidence path and SHA must both be set or null")
    _sha(expected_sha,"dispatch_provider_evidence_sha256")
    rel=Path(relative)
    if rel.is_absolute() or ".." in rel.parts:raise ValueError("recovery_authorization_invalid: dispatch/provider evidence path must be contained")
    resolved_root=root.resolve(strict=True)
    try:path=(root/rel).resolve(strict=True);path.relative_to(resolved_root)
    except (OSError,ValueError) as exc:raise ValueError("recovery_authorization_invalid: dispatch/provider evidence path escapes ledger") from exc
    current=root.resolve(strict=True)
    for part in rel.parts:
        current=current/part;attributes=getattr(current.lstat(),"st_file_attributes",0)
        if current.is_symlink() or bool(attributes&0x400):raise ValueError("recovery_authorization_invalid: dispatch/provider evidence cannot traverse symlink/reparse")
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha:raise ValueError("recovery_evidence_content_address: dispatch/provider evidence hash mismatch")
    try:evidence=json.loads(raw)
    except json.JSONDecodeError as exc:raise ValueError(f"recovery_evidence_invalid: {exc}") from exc
    required={"schema","reservation_sha256","campaign_authorization_sha256","authorization_sha256","candidate_id","cycle_or_review_batch_id","rows"}
    if not isinstance(evidence,dict) or set(evidence)!=required or evidence.get("schema")!="campaign-usage-dispatch-provider-evidence-v1":raise ValueError("recovery_evidence_invalid: exact evidence shape required")
    for field in ("campaign_authorization_sha256","authorization_sha256","candidate_id","cycle_or_review_batch_id"):
        if evidence.get(field)!=reservation[field]:raise ValueError(f"recovery_evidence_binding: {field} differs from reservation")
    if evidence.get("reservation_sha256")!=authorization["reservation_sha256"]:raise ValueError("recovery_evidence_binding: reservation differs from authorization")
    _provider_facts(evidence.get("rows"),candidate_id=reservation["candidate_id"],batch_id=reservation["cycle_or_review_batch_id"],cohort=reservation["cohort"],reserved_calls=reservation["reserved_calls"],call_contract=reservation["call_contract"],paired_opus_contract=reservation["paired_opus_contract"],paired_parent_contract=reservation["paired_parent_contract"])
    return evidence["rows"],expected_sha


def _load_transaction(root: Path, digest: str) -> dict:
    _sha(digest,"transaction_sha256")
    path=root/"transactions"/f"{digest}.json"
    try: raw=path.read_bytes()
    except FileNotFoundError as exc: raise ValueError(f"usage_chain_gap: missing transaction {digest}") from exc
    except OSError as exc: raise ValueError(f"usage_transaction_bytes: {exc}") from exc
    if hashlib.sha256(raw).hexdigest()!=digest: raise ValueError("usage_transaction_content_address: filename/reservation SHA does not match transaction bytes")
    try:tx=json.loads(raw)
    except json.JSONDecodeError as exc:raise ValueError(f"usage_transaction_canonical: {exc}") from exc
    if not isinstance(tx,dict) or raw!=_canonical(tx): raise ValueError("usage_transaction_canonical: transaction bytes are not canonical")
    _validate_transaction(tx)
    _validate_authorization_custody(root,tx)
    return tx


def _reservation_digests_for_authorization(root: Path, authorization_sha256: str) -> set[str]:
    transaction_dir=root/"transactions"
    if not transaction_dir.is_dir():return set()
    matches=set()
    for path in transaction_dir.glob("*.json"):
        if re.fullmatch(r"[a-f0-9]{64}\.json",path.name) is None:continue
        tx=_load_transaction(root,path.stem)
        if tx.get("kind")=="reservation" and tx.get("authorization_sha256")==authorization_sha256:matches.add(path.stem)
    return matches


def _terminal_digests_for_reservation(root: Path, reservation_sha256: str) -> set[str]:
    transaction_dir=root/"transactions"
    if not transaction_dir.is_dir():return set()
    matches=set()
    for path in transaction_dir.glob("*.json"):
        if re.fullmatch(r"[a-f0-9]{64}\.json",path.name) is None:continue
        tx=_load_transaction(root,path.stem)
        if tx.get("kind") in {"settlement","orphan-recovery"} and tx.get("reservation_transaction_sha256")==reservation_sha256:matches.add(path.stem)
    return matches


def _require_exact_terminal_adoption(root: Path, reservation_sha256: str, tx: dict) -> str:
    intended=_digest(tx);existing=_terminal_digests_for_reservation(root,reservation_sha256)
    if existing and existing!={intended}:raise ValueError("usage_terminal_replay: only the byte-identical terminal transaction may be adopted")
    return intended


def _validate_transaction(tx: dict) -> None:
    common={"schema","kind","sequence","predecessor_usage_head_sha256","predecessor_transaction_sha256","campaign_authorization_sha256","authorization_sha256","candidate_id","cycle_or_review_batch_id","cohort","lane","call_contract","paired_opus_contract","paired_parent_contract","authorization_custody"}
    kind=tx.get("kind")
    required={
        "reservation": common|{"reserved_calls"},
        "settlement": common|{"reservation_transaction_sha256","reserved_calls","attempted","accepted","in_flight","completed","failed","cancelled","not_dispatched","unknown","provider_usage_receipts","measured_cost"},
        "orphan-recovery": common|{"reservation_transaction_sha256","reserved_calls","recovery_authorization_sha256","orphan_id","dispatch_provider_evidence_sha256","attempted","accepted","in_flight","completed","failed","cancelled","not_dispatched","unknown","provider_usage_receipts","measured_cost"},
    }.get(kind)
    if tx.get("schema")!="campaign-usage-transaction-v1" or required is None or set(tx)!=required:
        raise ValueError("usage_transaction_shape: exact discriminator and fields are required")
    custody=tx.get("authorization_custody")
    if not isinstance(custody,list) or any(not isinstance(row,dict) for row in custody):
        raise ValueError("usage_transaction_shape: authorization custody must be an exact record list")
    if not isinstance(tx.get("sequence"),int) or isinstance(tx.get("sequence"),bool) or tx["sequence"]<1: raise ValueError("usage_chain_sequence: transaction sequence must be positive")
    for field in ("predecessor_usage_head_sha256","campaign_authorization_sha256","authorization_sha256"):
        _sha(tx.get(field),field)
    predecessor=tx.get("predecessor_transaction_sha256")
    if predecessor is not None:_sha(predecessor,"predecessor_transaction_sha256")
    _text(tx.get("candidate_id"),"candidate_id");_text(tx.get("cycle_or_review_batch_id"),"cycle_or_review_batch_id")
    required_calls=EXACT_CALLS.get(tx.get("cohort"));expected_lane="producer" if tx.get("cohort") in {"gpt-producer","paired-producer"} else "cold-review" if required_calls else None
    if required_calls is None or tx.get("reserved_calls")!=required_calls or tx.get("lane")!=expected_lane:
        raise ValueError("usage_binding: cohort, lane, and exact reservation count mismatch")
    _opus_contract(tx.get("paired_opus_contract"),tx["cohort"])
    _paired_parent_contract(tx.get("paired_parent_contract"),tx["cohort"])
    if tx.get("paired_opus_contract") is not None and tx["paired_opus_contract"].get("candidate_id")!=tx["paired_parent_contract"].get("opus_candidate_id"):raise ValueError("usage_binding: paired Opus child authorization candidate differs from sibling custody")
    _validate_call_contract(tx.get("call_contract"),tx["cohort"],tx["reserved_calls"],tx.get("paired_opus_contract"),tx.get("paired_parent_contract"),tx["candidate_id"])
    if kind in {"settlement","orphan-recovery"}:
        _sha(tx.get("reservation_transaction_sha256"),"reservation_transaction_sha256")
        count_fields=("attempted","accepted","in_flight","completed","failed","cancelled","not_dispatched","unknown")
        if any(not isinstance(tx.get(field),int) or isinstance(tx.get(field),bool) or tx[field]<0 for field in count_fields):
            raise ValueError("usage_transaction_shape: terminal counts must be nonnegative integers")
        derived,aggregate=_provider_facts(tx.get("provider_usage_receipts"),candidate_id=tx["candidate_id"],batch_id=tx["cycle_or_review_batch_id"],cohort=tx["cohort"],reserved_calls=tx["reserved_calls"],call_contract=tx["call_contract"],paired_opus_contract=tx["paired_opus_contract"],paired_parent_contract=tx["paired_parent_contract"])
        if any(tx.get(field)!=derived[field] for field in derived):raise ValueError("usage_arithmetic: terminal counts differ from provider/dispatch rows")
        if tx.get("measured_cost")!=aggregate:raise ValueError("usage_provider_metadata: measured cost does not equal per-call aggregation")
    if kind=="orphan-recovery":
        _sha(tx.get("recovery_authorization_sha256"),"recovery_authorization_sha256")
        _text(tx.get("orphan_id"),"orphan_id")
        evidence_sha=tx.get("dispatch_provider_evidence_sha256")
        if evidence_sha is not None:_sha(evidence_sha,"dispatch_provider_evidence_sha256")


def _apply_transaction(state: dict, digest: str, tx: dict, transactions: dict[str,dict]) -> dict:
    if tx["sequence"]!=state["sequence"]+1: raise ValueError("usage_chain_sequence: transaction order has a gap or reorder")
    if tx["predecessor_transaction_sha256"]!=state["last_transaction_sha256"]: raise ValueError("usage_chain_predecessor: transaction predecessor is not unique and monotonic")
    if tx["predecessor_usage_head_sha256"]!=_digest(state): raise ValueError("usage_chain_predecessor: predecessor head hash mismatch")
    campaign=state["campaign_authorization_sha256"]
    if campaign not in {None,tx["campaign_authorization_sha256"]}: raise ValueError("usage_binding: campaign cross-binding mismatch")
    if tx["kind"]=="reservation":
        if state["open_reservations"] or state["unresolved_usage"]: raise ValueError("unresolved_usage: reservation cannot advance an open or unresolved head")
        return {**state,"sequence":tx["sequence"],"campaign_authorization_sha256":tx["campaign_authorization_sha256"],"last_transaction_sha256":digest,"open_reservations":[digest]}
    reservation_sha=tx["reservation_transaction_sha256"]
    if state["open_reservations"]!=[reservation_sha]: raise ValueError("usage_head_conflict: terminal transaction does not settle the canonical reservation")
    reservation=transactions.get(reservation_sha)
    if reservation is None or reservation.get("kind")!="reservation": raise ValueError("usage_chain_gap: terminal transaction references no reservation")
    for field in ("campaign_authorization_sha256","authorization_sha256","candidate_id","cycle_or_review_batch_id","cohort","lane","reserved_calls","call_contract","paired_opus_contract","paired_parent_contract","authorization_custody"):
        if tx[field]!=reservation[field]: raise ValueError(f"usage_binding: {field} differs from reservation")
    counts=[tx[name] for name in ("completed","failed","cancelled","not_dispatched","unknown")]
    if any(not isinstance(value,int) or isinstance(value,bool) or value<0 for value in counts) or sum(counts)!=tx["reserved_calls"]:
        raise ValueError("usage_arithmetic: terminal transaction must account for every reserved call")
    attempted=tx["attempted"]
    if attempted<tx["accepted"] or attempted<tx["in_flight"]:raise ValueError("usage_arithmetic: accepted/in-flight evidence dimensions cannot exceed proved attempts")
    totals=dict(state["totals"])
    for key in ("attempted","accepted","in_flight","completed","failed","cancelled","not_dispatched","unknown"): totals[key]+=tx[key]
    if tx["lane"]=="producer":totals["producer_invocations"]+=attempted
    else:totals["cold_review_invocations"]+=attempted
    return {**state,"sequence":tx["sequence"],"campaign_authorization_sha256":tx["campaign_authorization_sha256"],"last_transaction_sha256":digest,"open_reservations":[],"unresolved_usage":tx["unknown"]>0,"totals":totals,"measured_cost":_merge_cost(state["measured_cost"],tx["measured_cost"])}


def validate_head(root: Path) -> dict:
    head=_load_unchecked(root)
    if not isinstance(head,dict) or set(head)!=HEAD_KEYS or head.get("schema")!="campaign-usage-head-v1" or not isinstance(head.get("totals"),dict) or set(head["totals"])!=TOTAL_KEYS:
        raise ValueError("usage_head_shape: canonical head discriminator/fields mismatch")
    sequence=head.get("sequence")
    if not isinstance(sequence,int) or isinstance(sequence,bool) or sequence<0:raise ValueError("usage_head_shape: sequence must be a nonnegative integer")
    campaign=head.get("campaign_authorization_sha256");last=head.get("last_transaction_sha256")
    if sequence==0:
        if campaign is not None or last is not None:raise ValueError("usage_head_shape: initial head cannot name campaign or transaction")
    else:
        _sha(campaign,"campaign_authorization_sha256");_sha(last,"last_transaction_sha256")
    open_reservations=head.get("open_reservations")
    if not isinstance(open_reservations,list) or len(open_reservations)>1 or len(open_reservations)!=len(set(open_reservations)):raise ValueError("usage_head_shape: open reservations must be a unique zero-or-one SHA list")
    for reservation_sha in open_reservations:_sha(reservation_sha,"open_reservation_sha256")
    if not isinstance(head.get("unresolved_usage"),bool):raise ValueError("usage_head_shape: unresolved_usage must be boolean")
    if any(not isinstance(head["totals"][key],int) or isinstance(head["totals"][key],bool) or head["totals"][key]<0 for key in TOTAL_KEYS): raise ValueError("usage_head_shape: totals must be nonnegative integers")
    _cost(head.get("measured_cost"),"head measured_cost")
    transaction_dir=root/"transactions"
    paths=sorted(transaction_dir.glob("*.json")) if transaction_dir.is_dir() else []
    transactions={}
    for path in paths:
        if re.fullmatch(r"[a-f0-9]{64}\.json",path.name) is None: raise ValueError("usage_transaction_filename: transaction filename must be its SHA-256")
        digest=path.stem
        if digest in transactions: raise ValueError("usage_chain_fork: duplicate transaction identity")
        transactions[digest]=_load_transaction(root,digest)
    # Validate every retained immutable DAG node, including unreachable
    # append-before-head residues. Competing valid children are retained; an
    # invalid predecessor/head/reservation/binding anywhere is corruption.
    memo:dict[str,dict]={};visiting:set[str]=set()
    def replay(digest: str) -> dict:
        if digest in memo:return memo[digest]
        if digest in visiting:raise ValueError("usage_chain_fork: transaction DAG contains a cycle")
        tx=transactions.get(digest)
        if tx is None:raise ValueError("usage_chain_gap: transaction predecessor is missing")
        visiting.add(digest);predecessor=tx["predecessor_transaction_sha256"]
        state_before=_initial() if predecessor is None else replay(predecessor)
        state_after=_apply_transaction(state_before,digest,tx,transactions)
        visiting.remove(digest);memo[digest]=state_after;return state_after
    for digest in transactions:replay(digest)
    state=_initial() if last is None else replay(last)
    if state["sequence"]!=sequence:raise ValueError("usage_chain_gap: canonical chain length differs from head sequence")
    if state!=head: raise ValueError("usage_head_chain: canonical head does not equal complete transaction replay")
    return head


def reserve(root: Path, *, cohort: str, calls: int, expected_sequence: int, expected_head_sha256: str,
            campaign_authorization_sha256: str | None = None, authorization_sha256: str | None = None,
            candidate_id: str | None = None, cycle_or_review_batch_id: str | None = None,
            call_subject_ids: list[str] | None = None, paired_opus_contract: dict|None=None, paired_parent_contract: dict|None=None,
            outer_parent_authorization_path: Path|None=None,
            paired_protocol_authorization_path: Path|None=None, paired_protocol_authorization_sha256: str|None=None,
            gpt_child_authorization_path: Path|None=None, gpt_child_authorization_sha256: str|None=None,
            opus_child_authorization_path: Path|None=None, opus_child_authorization_sha256: str|None=None) -> dict:
    required=EXACT_CALLS.get(cohort)
    if required is None: raise ValueError("reservation_cohort: unknown cohort")
    if calls!=required: raise ValueError(f"reservation_count: {cohort} must reserve exactly {required} calls")
    if campaign_authorization_sha256 is None: raise ValueError("campaign_authorization_required: reservation requires a hash-bound campaign authorization")
    campaign=_sha(campaign_authorization_sha256,"campaign_authorization_sha256")
    authorization=_sha(authorization_sha256,"authorization_sha256")
    candidate=_text(candidate_id,"candidate_id"); batch=_text(cycle_or_review_batch_id,"cycle_or_review_batch_id")
    lane="producer" if cohort in {"gpt-producer","paired-producer"} else "cold-review"
    if cohort in {"paired-producer","paired-review"}:
        if paired_parent_contract is not None or paired_opus_contract is not None:raise ValueError("usage_binding: paired custody must come from externally hash-anchored authorization artifacts")
        paired_parent_contract,opus_contract,authorization_snapshots=_load_paired_authorizations(root,cohort,candidate_id,call_subject_ids,authorization,outer_path=outer_parent_authorization_path,protocol_path=paired_protocol_authorization_path,protocol_sha256=paired_protocol_authorization_sha256,gpt_path=gpt_child_authorization_path,gpt_sha256=gpt_child_authorization_sha256,opus_path=opus_child_authorization_path,opus_sha256=opus_child_authorization_sha256)
    else:
        paired_parent_contract=None;opus_contract=_opus_contract(paired_opus_contract,cohort);authorization_snapshots=[]
    with _lock(root):
        head=validate_head(root)
        if head.get("unresolved_usage") or head.get("open_reservations"):
            raise ValueError("unresolved_usage: reconcile open or unknown usage before more paid calls")
        actual_head_sha256=_digest(head)
        if head.get("sequence")!=expected_sequence or actual_head_sha256!=expected_head_sha256: raise ValueError("usage_head_conflict: expected sequence/hash does not match canonical head")
        existing_campaign=head.get("campaign_authorization_sha256")
        if existing_campaign not in {None,campaign}:raise ValueError("campaign_authorization_binding: reservation campaign hash mismatch")
        prior_authorization_reservations=_reservation_digests_for_authorization(root,authorization)
        authorization_custody=[]
        try:
            _verify_authorization_snapshots(root,authorization_snapshots)
            authorization_custody=_transfer_authorization_custody(root,authorization_snapshots)
            call_contract=_make_call_contract(cohort,calls,call_subject_ids,opus_contract,paired_parent_contract,candidate_id)
            tx={"schema":"campaign-usage-transaction-v1","kind":"reservation","sequence":expected_sequence+1,
                "predecessor_usage_head_sha256":actual_head_sha256,"predecessor_transaction_sha256":head.get("last_transaction_sha256"),
                "campaign_authorization_sha256":campaign,"authorization_sha256":authorization,"candidate_id":candidate,
                "cycle_or_review_batch_id":batch,"cohort":cohort,"lane":lane,"call_contract":call_contract,"paired_opus_contract":opus_contract,"paired_parent_contract":paired_parent_contract,"authorization_custody":authorization_custody,"reserved_calls":calls}
            intended_digest=_digest(tx)
            if prior_authorization_reservations and prior_authorization_reservations!={intended_digest}:raise ValueError("usage_authorization_replay: only the byte-identical append-before-head reservation may be adopted")
            _validate_authorization_custody(root,tx,materialized=True)
            digest=_append(root,tx)
            _validate_authorization_custody(root,tx,materialized=True)
            head={**head,"sequence":expected_sequence+1,"campaign_authorization_sha256":campaign,"last_transaction_sha256":digest,"open_reservations":[digest]}
            _atomic_write(root/"head.json",head)
            if validate_head(root)!=head: raise ValueError("usage_head_readback: reservation head chain readback mismatch")
            return {**tx,"transaction_sha256":digest,"resulting_usage_head_sha256":_digest(head)}
        except Exception:
            if authorization_custody:_quarantine_drifted_custody(root,authorization_custody)
            raise


def settle(root: Path, reservation_sha256: str, *, completed: int, failed: int, cancelled: int, not_dispatched: int, unknown: int,
           provider_usage_receipts: list[dict] | None = None, measured_cost: dict | None = None,
           candidate_id: str | None = None, authorization_sha256: str | None = None) -> dict:
    values=(completed,failed,cancelled,not_dispatched,unknown)
    if any(not isinstance(v,int) or isinstance(v,bool) or v<0 for v in values): raise ValueError("usage_arithmetic: settlement counts must be nonnegative integers")
    with _lock(root):
        head=validate_head(root)
        if head.get("open_reservations")!=[reservation_sha256]: raise ValueError("usage_head_conflict: reservation is not the canonical open reservation")
        reservation=_load_transaction(root,reservation_sha256)
        if reservation.get("kind")!="reservation":raise ValueError("usage_binding: settlement target is not a reservation")
        if candidate_id!=reservation["candidate_id"] or authorization_sha256!=reservation["authorization_sha256"]:
            raise ValueError("usage_binding: settlement candidate/authorization differs from reservation")
        if sum(values)!=reservation["reserved_calls"]: raise ValueError("usage_arithmetic: settlement must account for every reserved call")
        receipts=provider_usage_receipts;cost=measured_cost
        derived,aggregate=_provider_facts(receipts,candidate_id=reservation["candidate_id"],batch_id=reservation["cycle_or_review_batch_id"],cohort=reservation["cohort"],reserved_calls=reservation["reserved_calls"],call_contract=reservation["call_contract"],paired_opus_contract=reservation["paired_opus_contract"],paired_parent_contract=reservation["paired_parent_contract"])
        _cost(cost)
        caller={"completed":completed,"failed":failed,"cancelled":cancelled,"not_dispatched":not_dispatched,"unknown":unknown}
        if any(caller[field]!=derived[field] for field in caller):raise ValueError("usage_arithmetic: settlement counts differ from per-call provider facts")
        if cost!=aggregate:raise ValueError("usage_provider_metadata: measured cost does not equal per-call aggregation")
        tx={"schema":"campaign-usage-transaction-v1","kind":"settlement","sequence":head["sequence"]+1,
            "predecessor_usage_head_sha256":_digest(head),"predecessor_transaction_sha256":head["last_transaction_sha256"],
            "campaign_authorization_sha256":reservation["campaign_authorization_sha256"],"authorization_sha256":reservation["authorization_sha256"],
            "candidate_id":reservation["candidate_id"],"cycle_or_review_batch_id":reservation["cycle_or_review_batch_id"],
            "cohort":reservation["cohort"],"lane":reservation["lane"],"call_contract":reservation["call_contract"],"paired_opus_contract":reservation["paired_opus_contract"],"paired_parent_contract":reservation["paired_parent_contract"],"authorization_custody":reservation["authorization_custody"],"reservation_transaction_sha256":reservation_sha256,
            "reserved_calls":reservation["reserved_calls"],"attempted":derived["attempted"],"accepted":derived["accepted"],"in_flight":derived["in_flight"],"completed":completed,"failed":failed,
            "cancelled":cancelled,"not_dispatched":not_dispatched,"unknown":unknown,"provider_usage_receipts":receipts,"measured_cost":cost}
        _require_exact_terminal_adoption(root,reservation_sha256,tx)
        digest=_append(root,tx); totals=dict(head["totals"])
        for key in ("attempted","accepted","in_flight","completed","failed","cancelled","not_dispatched","unknown"): totals[key]=totals.get(key,0)+tx[key]
        attempted=tx["attempted"]
        if reservation["cohort"] in {"gpt-producer","paired-producer"}: totals["producer_invocations"]=totals.get("producer_invocations",0)+attempted
        else: totals["cold_review_invocations"]=totals.get("cold_review_invocations",0)+attempted
        head={**head,"sequence":tx["sequence"],"last_transaction_sha256":digest,"open_reservations":[],"unresolved_usage":unknown>0,"totals":totals,"measured_cost":_merge_cost(head["measured_cost"],tx["measured_cost"])}
        _atomic_write(root/"head.json",head)
        if validate_head(root)!=head: raise ValueError("usage_head_readback: settlement head chain readback mismatch")
        return {**tx,"transaction_sha256":digest,"resulting_usage_head_sha256":_digest(head)}


def recover_orphan(root: Path, reservation_sha256: str, *, recovery_authorization: Path,
                   orphan_id: str, candidate_id: str, completed: int, failed: int,
                   cancelled: int, not_dispatched: int, unknown: int) -> dict:
    """Conservatively settle one canonical orphan without erasing its reservation."""
    values=(completed,failed,cancelled,not_dispatched,unknown)
    if any(not isinstance(value,int) or isinstance(value,bool) or value<0 for value in values):
        raise ValueError("usage_arithmetic: recovery counts must be nonnegative integers")
    try:raw=recovery_authorization.read_bytes();authorization=json.loads(raw)
    except (OSError,json.JSONDecodeError) as exc:raise ValueError(f"recovery_authorization_invalid: {exc}") from exc
    required={"schema","kind","authorization_id","campaign_authorization_sha256","authorization_sha256","reservation_sha256","orphan_id","candidate_id","expected_usage_head_sha256","claim_path","dispatch_provider_evidence_path","dispatch_provider_evidence_sha256"}
    if not isinstance(authorization,dict) or set(authorization)!=required or authorization.get("schema")!="campaign-usage-recovery-authorization-v1" or authorization.get("kind")!="orphan-recovery-authorization":raise ValueError("recovery_authorization_invalid: exact authorization shape required")
    if authorization.get("reservation_sha256")!=reservation_sha256 or authorization.get("orphan_id")!=orphan_id or authorization.get("candidate_id")!=candidate_id:raise ValueError("recovery_authorization_binding: reservation, orphan, and candidate must match")
    for field in ("campaign_authorization_sha256","authorization_sha256","reservation_sha256","expected_usage_head_sha256"):
        value=authorization.get(field)
        if not isinstance(value,str) or re.fullmatch(r"[a-f0-9]{64}",value) is None:raise ValueError(f"recovery_authorization_invalid: {field} must be SHA-256")
    if not isinstance(authorization.get("claim_path"),str) or not authorization["claim_path"]:raise ValueError("recovery_authorization_invalid: claim_path must be nonempty text")
    claim_rel=Path(authorization["claim_path"])
    if claim_rel.is_absolute() or ".." in claim_rel.parts:raise ValueError("recovery_authorization_invalid: claim path must be contained")
    claim=(root/claim_rel).resolve(strict=False);resolved_root=root.resolve(strict=True)
    if resolved_root not in claim.parents:raise ValueError("recovery_authorization_invalid: claim path escapes ledger")
    authorization_sha256=hashlib.sha256(raw).hexdigest()
    claim_preexists=claim.exists()
    head_before=head_snapshot(root)
    if claim_preexists and head_before.get("open_reservations")!=[reservation_sha256]:raise ValueError("recovery_authorization_replay: authorization claim belongs to an already-finalized recovery")
    if head_before.get("campaign_authorization_sha256")!=authorization["campaign_authorization_sha256"] or head_before["head_sha256"]!=authorization["expected_usage_head_sha256"]:raise ValueError("recovery_authorization_binding: campaign or expected head mismatch")
    reservation_before=_load_transaction(root,reservation_sha256)
    if reservation_before.get("kind")!="reservation" or authorization["authorization_sha256"]!=reservation_before["authorization_sha256"] or candidate_id!=reservation_before["candidate_id"]:
        raise ValueError("recovery_authorization_binding: authorization or candidate differs from reservation")
    with _lock(root):
        head=validate_head(root)
        if head.get("open_reservations")!=[reservation_sha256]:
            raise ValueError("usage_head_conflict: reservation is not the canonical orphan")
        reservation=_load_transaction(root,reservation_sha256)
        if reservation.get("kind")!="reservation" or authorization["authorization_sha256"]!=reservation["authorization_sha256"] or authorization["campaign_authorization_sha256"]!=reservation["campaign_authorization_sha256"] or candidate_id!=reservation["candidate_id"]:
            raise ValueError("recovery_authorization_binding: authorization/campaign/candidate differs from reservation")
        rows,evidence_sha=_load_recovery_evidence(root,authorization,reservation)
        derived,cost=_provider_facts(rows,candidate_id=reservation["candidate_id"],batch_id=reservation["cycle_or_review_batch_id"],cohort=reservation["cohort"],reserved_calls=reservation["reserved_calls"],call_contract=reservation["call_contract"],paired_opus_contract=reservation["paired_opus_contract"],paired_parent_contract=reservation["paired_parent_contract"])
        caller={"completed":completed,"failed":failed,"cancelled":cancelled,"not_dispatched":not_dispatched,"unknown":unknown}
        if evidence_sha is not None and any(caller[field]!=derived[field] for field in caller):raise ValueError("usage_arithmetic: recovery caller counts differ from immutable dispatch/provider evidence")
        completed,failed,cancelled,not_dispatched,unknown=(derived[field] for field in ("completed","failed","cancelled","not_dispatched","unknown"))
        tx={"schema":"campaign-usage-transaction-v1","kind":"orphan-recovery","sequence":head["sequence"]+1,
            "predecessor_usage_head_sha256":_digest(head),"predecessor_transaction_sha256":head["last_transaction_sha256"],
            "campaign_authorization_sha256":reservation["campaign_authorization_sha256"],"authorization_sha256":reservation["authorization_sha256"],
            "candidate_id":candidate_id,"cycle_or_review_batch_id":reservation["cycle_or_review_batch_id"],"lane":reservation["lane"],"call_contract":reservation["call_contract"],"paired_opus_contract":reservation["paired_opus_contract"],"paired_parent_contract":reservation["paired_parent_contract"],"authorization_custody":reservation["authorization_custody"],
            "reservation_transaction_sha256":reservation_sha256,
            "reserved_calls":reservation["reserved_calls"],"recovery_authorization_sha256":authorization_sha256,"orphan_id":orphan_id,"dispatch_provider_evidence_sha256":evidence_sha,
            "cohort":reservation["cohort"],"attempted":derived["attempted"],"accepted":derived["accepted"],"in_flight":derived["in_flight"],
            "completed":completed,"failed":failed,"cancelled":cancelled,
            "not_dispatched":not_dispatched,"unknown":unknown,"provider_usage_receipts":rows,"measured_cost":cost}
        _validate_transaction(tx)
        _require_exact_terminal_adoption(root,reservation_sha256,tx)
        claim_record={"schema":"campaign-usage-recovery-claim-v1","authorization_sha256":authorization_sha256,"reservation_sha256":reservation_sha256,"orphan_id":orphan_id,"candidate_id":candidate_id,"dispatch_provider_evidence_sha256":evidence_sha}
        claim_raw=_canonical(claim_record)
        if claim.exists():
            claim_path=_authorization_lexical_path(root,claim,"recovery_claim")
            if claim_path.read_bytes()!=claim_raw:raise ValueError("recovery_authorization_replay: existing authorization claim differs from exact retry")
        else:
            try:atomic_publish_bytes(claim,claim_raw)
            except PublicationError as exc:
                if not claim.is_file() or claim.read_bytes()!=claim_raw:raise ValueError("recovery_authorization_replay: authorization claim already exists with different bytes") from exc
        if claim.read_bytes()!=claim_raw:raise ValueError("recovery_authorization_replay: authorization claim readback differs from exact retry")
        digest=_append(root,tx); totals=dict(head["totals"])
        for key in ("attempted","accepted","in_flight","completed","failed","cancelled","not_dispatched","unknown"): totals[key]=totals.get(key,0)+tx[key]
        attempted=tx["attempted"]
        if reservation["cohort"] in {"gpt-producer","paired-producer"}: totals["producer_invocations"]=totals.get("producer_invocations",0)+attempted
        else: totals["cold_review_invocations"]=totals.get("cold_review_invocations",0)+attempted
        head={**head,"sequence":tx["sequence"],"last_transaction_sha256":digest,
              "open_reservations":[],"unresolved_usage":unknown>0,"totals":totals,"measured_cost":_merge_cost(head["measured_cost"],tx["measured_cost"])}
        _atomic_write(root/"head.json",head)
        if validate_head(root)!=head: raise ValueError("usage_head_readback: recovery head chain readback mismatch")
        return {**tx,"transaction_sha256":digest,"resulting_usage_head_sha256":_digest(head)}


def self_test() -> int:
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);campaign="c"*64;authorization="a"*64
        def rows(reservation: dict, statuses: list[str]) -> list[dict]:
            return [{"call_id":f"{reservation['cycle_or_review_batch_id']}:call-{index:02d}","candidate_id":reservation["candidate_id"],"cycle_or_review_batch_id":reservation["cycle_or_review_batch_id"],**contract,"started_at":"2026-07-10T12:00:00Z" if status=="COMPLETED" else None,"ended_at":"2026-07-10T12:00:01Z" if status=="COMPLETED" else None,"host_invocation_id":f"self-{index:02d}" if status=="COMPLETED" else None,"accepted":True if status=="COMPLETED" else None,"in_flight":True if status=="COMPLETED" else None,"status":status,"unknown_kind":"DISPATCH_UNKNOWN" if status=="UNKNOWN" else None,"acknowledgment_origin":"BOTH" if status=="COMPLETED" else "NONE","terminal_transport_status":"COMPLETED" if status=="COMPLETED" else "UNKNOWN","provider_call_id":f"provider-{index:02d}" if status=="COMPLETED" else None,"usage":{"status":"UNAVAILABLE"},"cost":{"unit":"usd","value":"unknown"}} for index,(contract,status) in enumerate(zip(reservation["call_contract"],statuses),1)]
        subjects5=[f"subject-{index:02d}" for index in range(1,6)];subjects10=[f"subject-{index:02d}" for index in range(1,11)]
        r=reserve(root,cohort="gpt-producer",calls=5,expected_sequence=0,expected_head_sha256=head_snapshot(root)["head_sha256"],campaign_authorization_sha256=campaign,authorization_sha256=authorization,candidate_id="c1",cycle_or_review_batch_id="cycle1",call_subject_ids=subjects5)
        settle(root,r["transaction_sha256"],completed=5,failed=0,cancelled=0,not_dispatched=0,unknown=0,provider_usage_receipts=rows(r,["COMPLETED"]*5),measured_cost={"unit":"usd","value":"unknown"},candidate_id="c1",authorization_sha256=authorization)
        auth=root/"self-auth";auth.mkdir();shared={"source_commit":"6"*40,"package_sha256":"d"*64,"archive_sha256":"a"*64,"extracted_tree_sha256":"b"*64,"build_manifest_sha256":"7"*64,"registry_sha256":hashlib.sha256(DEFAULT_REGISTRY.read_bytes()).hexdigest()};common={"deterministic_fake_only":True,"live_execution_authorized":False,"parent_id":"c2",**shared}
        case_ids=[row["case_id"] for row in load_registry()["cases"]];gpt={"schema":"campaign-usage-fake-gpt-child-authorization-v1",**common,"child_cycle_id":"c2-gpt-cycle","candidate_id":"c2-gpt","candidate_record_sha256":"8"*64,"child_protocol_sha256":"9"*64,"subject_ids":subjects10[:5],"case_ids":case_ids,"output_sha256s":[None]*5};opus={"schema":"campaign-usage-fake-opus-child-authorization-v1",**common,"child_cycle_id":"c2-opus-cycle","candidate_id":"c2-opus","candidate_record_sha256":"a"*64,"child_protocol_sha256":"b"*64,"subject_ids":subjects10[5:],"case_ids":case_ids,"output_sha256s":[None]*5,"model":"test-only-opus-exact","reasoning_effort":"high","protocol":COHORT_PROTOCOLS["paired-producer"],"settings":{"adapter":"never-reachable-fake"}}
        gpt_sha=_digest(gpt);opus_sha=_digest(opus);protocol_core={"schema":"campaign-usage-fake-paired-protocol-authorization-v1","deterministic_fake_only":True,"live_execution_authorized":False,"parent_id":"c2","cohort":"paired-producer",**shared,"gpt_child_authorization_sha256":gpt_sha,"opus_child_authorization_sha256":opus_sha};outer={"schema":"campaign-usage-fake-outer-parent-authorization-v1","deterministic_fake_only":True,"live_execution_authorized":False,"parent_id":"c2","cohort":"paired-producer","paired_protocol_core_sha256":_digest(protocol_core),**shared,"gpt_child_authorization_sha256":gpt_sha,"opus_child_authorization_sha256":opus_sha,"gpt_candidate_id":"c2-gpt","opus_candidate_id":"c2-opus","gpt_candidate_record_sha256":"8"*64,"opus_candidate_record_sha256":"a"*64,"gpt_child_cycle_id":"c2-gpt-cycle","opus_child_cycle_id":"c2-opus-cycle","gpt_child_protocol_sha256":"9"*64,"opus_child_protocol_sha256":"b"*64,"gpt_subject_ids":subjects10[:5],"opus_subject_ids":subjects10[5:],"gpt_case_ids":case_ids,"opus_case_ids":case_ids,"gpt_output_sha256s":[None]*5,"opus_output_sha256s":[None]*5};outer_sha=_digest(outer);protocol={**protocol_core,"outer_parent_authorization_sha256":outer_sha};protocol_sha=_digest(protocol)
        paths=[auth/"outer.json",auth/"protocol.json",auth/"gpt.json",auth/"opus.json"]
        for path,value in zip(paths,(outer,protocol,gpt,opus)):path.write_bytes(_canonical(value))
        p=reserve(root,cohort="paired-producer",calls=10,expected_sequence=2,expected_head_sha256=head_snapshot(root)["head_sha256"],campaign_authorization_sha256=campaign,authorization_sha256=outer_sha,candidate_id="c2",cycle_or_review_batch_id="cycle2",call_subject_ids=subjects10,outer_parent_authorization_path=paths[0],paired_protocol_authorization_path=paths[1],paired_protocol_authorization_sha256=protocol_sha,gpt_child_authorization_path=paths[2],gpt_child_authorization_sha256=gpt_sha,opus_child_authorization_path=paths[3],opus_child_authorization_sha256=opus_sha)
        settle(root,p["transaction_sha256"],completed=9,failed=0,cancelled=0,not_dispatched=0,unknown=1,provider_usage_receipts=rows(p,["COMPLETED"]*9+["UNKNOWN"]),measured_cost={"unit":"usd","value":"unknown"},candidate_id="c2",authorization_sha256=outer_sha)
        checks=[("five reservation",r["reserved_calls"]==5),("ten reservation",p["reserved_calls"]==10),("single monotonic head",validate_head(root)["sequence"]==4)]
        try: reserve(root,cohort="gpt-review",calls=5,expected_sequence=4,expected_head_sha256=head_snapshot(root)["head_sha256"],campaign_authorization_sha256=campaign,authorization_sha256="d"*64,candidate_id="c3",cycle_or_review_batch_id="review1",call_subject_ids=subjects5); checks.append(("unknown blocks",False))
        except ValueError as exc: checks.append(("unknown blocks","unresolved_usage" in str(exc)))
    for n,o in checks: print(f"  self-test {'PASS' if o else 'FAIL'}: {n}")
    return 0 if all(o for _,o in checks) else 1


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); sub=p.add_subparsers(dest="command")
    r=sub.add_parser("reserve"); r.add_argument("--root",type=Path,required=True); r.add_argument("--cohort",choices=sorted(EXACT_CALLS),required=True); r.add_argument("--calls",type=int,required=True); r.add_argument("--expected-sequence",type=int,required=True); r.add_argument("--expected-head-sha256",required=True); r.add_argument("--campaign-authorization-sha256",required=True); r.add_argument("--authorization-sha256",required=True); r.add_argument("--candidate-id",required=True); r.add_argument("--cycle-or-review-batch-id",required=True);r.add_argument("--call-subjects",type=Path);r.add_argument("--paired-opus-contract",type=Path)
    r.add_argument("--outer-parent-authorization",type=Path)
    for name in ("paired-protocol-authorization","gpt-child-authorization","opus-child-authorization"):r.add_argument(f"--{name}",type=Path);r.add_argument(f"--{name}-sha256")
    s=sub.add_parser("settle"); s.add_argument("--root",type=Path,required=True); s.add_argument("--reservation-sha256",required=True); s.add_argument("--authorization-sha256",required=True); s.add_argument("--candidate-id",required=True);s.add_argument("--provider-usage-receipts",type=Path,required=True);s.add_argument("--measured-cost",type=Path,required=True); [s.add_argument(f"--{n.replace('_','-')}",type=int,default=0) for n in ("completed","failed","cancelled","not_dispatched","unknown")]
    q=sub.add_parser("recover-orphan"); q.add_argument("--root",type=Path,required=True); q.add_argument("--reservation-sha256",required=True); q.add_argument("--recovery-authorization",type=Path,required=True); q.add_argument("--orphan-id",required=True); q.add_argument("--candidate-id",required=True); [q.add_argument(f"--{n.replace('_','-')}",type=int,default=0) for n in ("completed","failed","cancelled","not_dispatched","unknown")]
    a=p.parse_args();
    if a.self_test:return self_test()
    try:
        if a.command=="reserve": result=reserve(a.root,cohort=a.cohort,calls=a.calls,expected_sequence=a.expected_sequence,expected_head_sha256=a.expected_head_sha256,campaign_authorization_sha256=a.campaign_authorization_sha256,authorization_sha256=a.authorization_sha256,candidate_id=a.candidate_id,cycle_or_review_batch_id=a.cycle_or_review_batch_id,call_subject_ids=json.loads(a.call_subjects.read_text(encoding="utf-8")) if a.call_subjects else None,paired_opus_contract=json.loads(a.paired_opus_contract.read_text(encoding="utf-8")) if a.paired_opus_contract else None,outer_parent_authorization_path=a.outer_parent_authorization,paired_protocol_authorization_path=a.paired_protocol_authorization,paired_protocol_authorization_sha256=a.paired_protocol_authorization_sha256,gpt_child_authorization_path=a.gpt_child_authorization,gpt_child_authorization_sha256=a.gpt_child_authorization_sha256,opus_child_authorization_path=a.opus_child_authorization,opus_child_authorization_sha256=a.opus_child_authorization_sha256)
        elif a.command=="recover-orphan": result=recover_orphan(a.root,a.reservation_sha256,recovery_authorization=a.recovery_authorization,orphan_id=a.orphan_id,candidate_id=a.candidate_id,completed=a.completed,failed=a.failed,cancelled=a.cancelled,not_dispatched=a.not_dispatched,unknown=a.unknown)
        elif a.command=="settle": result=settle(a.root,a.reservation_sha256,completed=a.completed,failed=a.failed,cancelled=a.cancelled,not_dispatched=a.not_dispatched,unknown=a.unknown,provider_usage_receipts=json.loads(a.provider_usage_receipts.read_text(encoding="utf-8")),measured_cost=json.loads(a.measured_cost.read_text(encoding="utf-8")),candidate_id=a.candidate_id,authorization_sha256=a.authorization_sha256)
        else:p.error("choose reserve, settle, or recover-orphan")
    except (OSError,ValueError,json.JSONDecodeError) as exc: print(json.dumps({"status":"FAIL","error":str(exc)},sort_keys=True)); return 1
    print(json.dumps({"status":"PASS","record":result},sort_keys=True)); return 0


if __name__=="__main__":sys.exit(main())
