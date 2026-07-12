#!/usr/bin/env python3
"""Validate and consume the locked v0.4.6.0 release-package build boundary."""
from __future__ import annotations

import argparse
import getpass
import json
import os
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from a16_immutable_custody import (
    CustodyError,
    append_claim_before_cas,
    iter_immutable_records,
    publish_terminal_receipt,
    read_cas_pointer,
    sha256_bytes,
)
from contract_validation import PathCustodyError, resolve_repo_path, validate_schema_subset
from source_provenance import DuplicateObjectKey, strict_json_loads


ROOT = Path(__file__).resolve().parents[1]
RUN_REL = Path(".IMPLEMENTAUDIT/runs/daee-v046-runtime-footprint-b10-sxsMU5")
AUTH_ROOT = ROOT / RUN_REL / "evidence/release-action/authorizations"
CUSTODY_ROOT = ROOT / RUN_REL / "evidence/release-action"
SCHEMA_PATH = ROOT / "schema/release-action-authorization.schema.json"
EXPECTATION_SCHEMA_PATH = ROOT / "schema/negative-fixture-expectation.schema.json"
FIXTURE_ROOT = ROOT / "tests/release-action-authorization"
CHECKER_ID = "release-action-authorization"
ACTION = "build-release-package"
DOWNSTREAM = ["release-package", "tag", "upload", "publish", "release"]


@dataclass(frozen=True)
class Finding:
    failure_class: str
    failure_subcode: str
    message: str


def diagnostic(finding: Finding, artifact: str) -> dict[str, Any]:
    return {
        "artifact": artifact, "checker_id": CHECKER_ID,
        "downstream_invalidated": DOWNSTREAM, "earliest_stage": "release-action",
        "exit_category": "structural-rejection", "exit_code": 1,
        "failure_class": finding.failure_class, "failure_subcode": finding.failure_subcode,
        "message": finding.message,
    }


def _load(path: Path) -> tuple[dict[str, Any] | None, bytes, Finding | None]:
    try:
        raw = path.read_bytes(); value = strict_json_loads(raw, label=str(path))
    except DuplicateObjectKey as exc:
        return None, b"", Finding("malformed_json", "duplicate-key", f"duplicate JSON object key nonce: {exc}")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return None, b"", Finding("malformed_json", "malformed-json", str(exc))
    if not isinstance(value, dict):
        return None, raw, Finding("authorization_family", "root-shape", "release authorization root must be an object")
    return value, raw, None


def _schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = strict_json_loads(path.read_bytes(), label=str(path))
    if not isinstance(value, dict):
        raise ValueError(f"schema root must be an object: {path}")
    return value


def _time(value: Any, field: str) -> tuple[datetime | None, Finding | None]:
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc), None
    except ValueError:
        return None, Finding("validity_window", "timestamp", f"{field} must be RFC3339 UTC seconds")


def _expected_locator(value: dict[str, Any], leaf: str) -> str:
    area = "claims" if leaf == "claim" else "receipts"
    suffix = "claim" if leaf == "claim" else "receipt"
    return (RUN_REL / "evidence/release-action" / area / f"{value['authorization_id']}.{suffix}.json").as_posix()


def resolve_live_authorization_path(candidate:Path,*,authority_root:Path=AUTH_ROOT)->Path:
    root=authority_root.resolve(strict=True);resolved=candidate.resolve(strict=True)
    try:resolved.relative_to(root)
    except ValueError as exc:raise ValueError(f"resolved authorization leaves protected root: {candidate} -> {resolved}") from exc
    if not resolved.is_file() or resolved.is_symlink():raise ValueError("authorization must be one resolved regular file")
    return resolved


def find_existing_action_records(custody_root:Path,authorization_sha256:str,nonce:str)->list[tuple[Path,dict[str,Any],str]]:
    matches=[]
    for namespace in ("claims","receipts"):
        root=custody_root/namespace
        if not root.is_dir():continue
        for row in iter_immutable_records(root):
            record=row[1]
            if record.get("schema") not in {"release-action-claim-v1","release-action-receipt-v1"}:continue
            if record.get("authorization_sha256")==authorization_sha256 or record.get("nonce")==nonce:matches.append(row)
    return matches


def result_requires_live_observation(result:str)->bool:return result=="PASS"


def resolve_live_custody_path(locator:str,namespace:str,*,must_exist:bool)->Path:
    target=resolve_repo_path(ROOT,locator,must_exist=must_exist,expect_file=must_exist)
    namespace_root=(CUSTODY_ROOT/namespace).resolve()
    try:target.relative_to(namespace_root)
    except ValueError as exc:raise PathCustodyError(f"{namespace} locator leaves fixed release custody namespace: {locator}",subcode="custody-namespace") from exc
    return target


def _authority_file_protected(path:Path)->bool:
    if not path.is_file() or path.is_symlink():return False
    for protected in (path,path.parent):
        mode=protected.stat(follow_symlinks=False).st_mode
        if (mode & stat.S_IWRITE) if os.name=="nt" else (mode & 0o222):return False
    return True


def validate_authorization(value: dict[str, Any], observed: dict[str, Any]) -> list[Finding]:
    if value.get("schema") != "release-action-authorization-v1" or value.get("kind") != "release-action-authorization":
        return [Finding("authorization_family", "wrong-family", "record is not a release-action-authorization")]
    if value.get("action") != ACTION:
        return [Finding("action_family", "action-family", f"only build-release-package is permitted; got {value.get('action')}")]
    if value.get("reusable") is not False:
        return [Finding("reusable_authorization", "reusable", "reusable must be false")]
    if value.get("revoked") is True:
        return [Finding("authorization_revoked", "revoked", "revoked must remain false")]
    try:
        for field in ("output_directory", "claim_locator", "action_receipt_locator"):
            resolve_repo_path(ROOT, value.get(field, ""), must_exist=False)
    except PathCustodyError as exc:
        message = str(exc)
        if exc.subcode == "path-traversal":
            message = f"parent traversal is forbidden: {value.get('output_directory')}"
        return [Finding("path_custody", exc.subcode, message)]
    ref_check=subprocess.run(["git","check-ref-format",str(value.get("target_ref",""))],cwd=ROOT,capture_output=True)
    if ref_check.returncode:return [Finding("ref_drift","ref-format",f"target_ref is not a valid full Git ref: {value.get('target_ref')}")]
    if value.get("allowed_actions") != [ACTION]:
        return [Finding("extra_actions", "allowed-actions", "allowed_actions must contain only build-release-package")]
    issues = validate_schema_subset(value, _schema())
    if issues:
        issue = issues[0]
        return [Finding("schema_contract", f"schema-{issue.keyword.lower()}", f"{issue.path}: {issue.message}")]
    denied = ["commit", "force", "publish", "push", "release", "tag", "upload"]
    if value["denied_actions"] != denied:
        return [Finding("extra_actions", "denied-actions", "denied commit/push/force/tag/upload/publish/release actions must be exact")]
    if value["version"] != "v0.4.6.0" or value["profile"] != "execution-mini":
        return [Finding("release_scope", "version-profile", "only v0.4.6.0 execution-mini is permitted")]
    expected_output = f"build/release-authorized/{value['authorization_id']}"
    if value["output_directory"] != expected_output:
        return [Finding("output_collision", "output-identity", "output_directory must be unique and derived from authorization_id")]
    if value["claim_locator"] != _expected_locator(value, "claim") or value["action_receipt_locator"] != _expected_locator(value, "receipt"):
        return [Finding("claim_locator", "claim-locator", "claim/receipt locators must be authorization-derived fixed custody paths")]
    issued, error = _time(value["issued_at"], "issued_at")
    if error: return [error]
    not_before, error = _time(value["valid_not_before"], "valid_not_before")
    if error: return [error]
    not_after, error = _time(value["valid_not_after"], "valid_not_after")
    if error: return [error]
    now, error = _time(observed.get("now"), "observed now")
    if error: return [error]
    assert issued and not_before and not_after and now
    if not (issued <= not_before < not_after):
        return [Finding("validity_window", "window-order", "issued_at <= valid_not_before < valid_not_after is required")]
    if now < not_before:
        return [Finding("validity_window", "not-yet-valid", "valid_not_before is in the future; authorization is not yet valid")]
    if now > not_after:
        return [Finding("validity_window", "expired", "valid_not_after has passed; authorization is expired")]
    for field, cls, sub in (
        ("repository", "repository_drift", "repository"),
        ("target_branch", "branch_drift", "target-branch"),
        ("target_ref", "ref_drift", "target-ref"),
        ("writer_boundary_identity", "writer_boundary", "writer-identity"),
    ):
        if value[field] != observed.get(field):
            return [Finding(cls, sub, f"{field} differs from observed source/writer boundary")]
    if value["source_commit"] != observed.get("source_commit"):
        return [Finding("source_drift", "source-commit", "source_commit differs from observed HEAD")]
    if observed.get("source_clean") is not True or value["clean_tree_sha256"] != observed.get("clean_tree_sha256"):
        return [Finding("source_drift", "clean-tree", "clean_tree_sha256 differs or source state is not clean")]
    if observed.get("output_directory_exists") is True:
        return [Finding("output_collision", "output-exists", "output_directory must be unused")]
    if value["expected_claim_predecessor_sha256"] != observed.get("claim_head_sha256"):
        return [Finding("cas_predecessor", "predecessor-mismatch", "expected claim predecessor differs from custody head")]
    return []


def _claim_id(auth_sha: str, nonce: str) -> str:
    return sha256_bytes(b"release-action-claim-v1\0" + bytes.fromhex(auth_sha) + b"\0" + nonce.encode())


def _receipt_id(claim_sha: str, result: str) -> str:
    return sha256_bytes(b"release-action-receipt-v1\0" + bytes.fromhex(claim_sha) + b"\0" + result.encode("ascii"))


def consume_authorization(value: dict[str, Any], raw: bytes, observed: dict[str, Any], *, custody_root: Path, claim_target: Path, claimed_at: str) -> tuple[dict[str, Any] | None, Finding | None]:
    findings = validate_authorization(value, observed)
    if findings: return None, findings[0]
    auth_sha = sha256_bytes(raw)
    matching=find_existing_action_records(custody_root,auth_sha,value["nonce"])
    if matching:
        record_path,record,_record_digest=matching[0];head=read_cas_pointer(custody_root)
        adoptable=len(matching)==1 and record_path.resolve()==claim_target.resolve() and record.get("schema")=="release-action-claim-v1" and record.get("authorization_sha256")==auth_sha and record.get("authorization_id")==value["authorization_id"] and record.get("nonce")==value["nonce"] and record.get("predecessor_record_sha256")==value["expected_claim_predecessor_sha256"] and head["last_record_sha256"]==value["expected_claim_predecessor_sha256"]
        if adoptable:
            try:append_claim_before_cas(custody_root,claim_target,record,expected_predecessor_sha256=value["expected_claim_predecessor_sha256"])
            except CustodyError as exc:return None,Finding("claim_custody",exc.subcode,str(exc))
            return record,None
        return None, Finding("authorization_replay", "authorization-replay", "authorization digest/nonce already claimed")
    claim = {
        "schema":"release-action-claim-v1", "kind":"release-action-claim",
        "claim_id":_claim_id(auth_sha, value["nonce"]), "authorization_sha256":auth_sha,
        "authorization_id":value["authorization_id"], "nonce":value["nonce"], "action":ACTION,
        "claim_locator":value["claim_locator"], "action_receipt_locator":value["action_receipt_locator"],
        "output_directory":value["output_directory"], "writer_boundary_identity":value["writer_boundary_identity"],
        "claimed_at":claimed_at, "predecessor_record_sha256":value["expected_claim_predecessor_sha256"],
        "status":"CLAIMED", "terminal_claim":False,
    }
    if validate_schema_subset(claim, _schema()):
        return None, Finding("claim_schema", "claim-schema", "generated release claim failed schema")
    try:
        append_claim_before_cas(custody_root, claim_target, claim, expected_predecessor_sha256=value["expected_claim_predecessor_sha256"])
    except CustodyError as exc:
        return None, Finding("claim_custody", exc.subcode, str(exc))
    return claim, None


def finalize_authorization(value: dict[str, Any], raw: bytes, claim_path: Path, result: str, *, custody_root: Path, receipt_target: Path, finalized_at: str) -> tuple[dict[str, Any] | None, Finding | None]:
    try:
        claim_raw=claim_path.read_bytes(); claim=strict_json_loads(claim_raw,label=str(claim_path))
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        return None,Finding("claim_custody","claim-read",str(exc))
    auth_sha=sha256_bytes(raw)
    if validate_schema_subset(claim,_schema()) or any(claim.get(k)!=v for k,v in (("authorization_sha256",auth_sha),("authorization_id",value["authorization_id"]),("nonce",value["nonce"]))):
        return None,Finding("claim_custody","claim-binding","release claim differs from authorization")
    package_path=None;package_sha=None;package_bytes=None
    if result=="PASS":
        candidate=Path(value["output_directory"])/"daee-epistemics-v0.4.6.0-execution-mini.skill.zip"
        try: candidate=resolve_repo_path(ROOT,candidate,must_exist=True,expect_file=True)
        except PathCustodyError as exc:return None,Finding("action_result","package-missing",str(exc))
        package_path=candidate.relative_to(ROOT).as_posix();data=candidate.read_bytes();package_sha=sha256_bytes(data);package_bytes=len(data)
    claim_sha=sha256_bytes(claim_raw)
    receipt={"schema":"release-action-receipt-v1","kind":"release-action-receipt","receipt_id":_receipt_id(claim_sha,result),"claim_sha256":claim_sha,"authorization_sha256":auth_sha,"authorization_id":value["authorization_id"],"nonce":value["nonce"],"action":ACTION,"result":result,"writer_boundary_identity":value["writer_boundary_identity"],"finalized_at":finalized_at,"output_directory":value["output_directory"],"package_path":package_path,"package_sha256":package_sha,"package_bytes":package_bytes,"terminal":True,"terminal_claim":False}
    if validate_schema_subset(receipt,_schema()):return None,Finding("receipt_schema","receipt-schema","generated release receipt failed schema")
    try:publish_terminal_receipt(custody_root,receipt_target,receipt)
    except CustodyError as exc:return None,Finding("receipt_custody",exc.subcode,str(exc))
    return receipt,None


def _git(*args: str, binary: bool=False) -> bytes|str:
    result=subprocess.run(["git",*args],cwd=ROOT,capture_output=True,check=False)
    if result.returncode:raise ValueError(result.stderr.decode(errors="replace").strip() or f"git {' '.join(args)} failed")
    return result.stdout if binary else result.stdout.decode().strip()


def _repository(remote_url: str) -> str:
    text=remote_url.rstrip("/");text=text[:-4] if text.endswith(".git") else text
    if ":" in text and not text.startswith(("http://","https://")):return text.rsplit(":",1)[-1]
    parts=text.split("/");return "/".join(parts[-2:])


def collect_live_observation(value: dict[str,Any]) -> dict[str,Any]:
    branch=str(_git("branch","--show-current"));commit=str(_git("rev-parse","HEAD"));status=bytes(_git("status","--porcelain=v2","-z","--untracked-files=all",binary=True))
    clean=not status;clean_digest=sha256_bytes(b"daee-clean-tree-v1\0"+bytes.fromhex(commit)+b"\0"+status)
    return {"now":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"repository":_repository(str(_git("remote","get-url","origin"))),"target_branch":branch,"target_ref":f"refs/heads/{branch}","writer_boundary_identity":f"os-user:{getpass.getuser()}","source_commit":commit,"source_clean":clean,"clean_tree_sha256":clean_digest,"output_directory_exists":(ROOT/value["output_directory"]).exists(),"claim_head_sha256":read_cas_pointer(CUSTODY_ROOT)["last_record_sha256"]}


def _fixture_observed() -> dict[str,Any]:
    value=strict_json_loads((FIXTURE_ROOT/"support/observations.json").read_bytes(),label="release observations");return dict(value["observed"])


def _expectation_ok(path:Path,finding:Finding)->tuple[bool,str]:
    sidecar=path.with_suffix(".expectation.json")
    if not sidecar.is_file():return False,"missing same-stem expectation"
    exp=strict_json_loads(sidecar.read_bytes(),label=str(sidecar))
    if validate_schema_subset(exp,_schema(EXPECTATION_SCHEMA_PATH)):return False,"expectation schema invalid"
    actual=diagnostic(finding,path.as_posix())
    for a,e in (("checker_id","expected_checker_id"),("exit_category","expected_exit_category"),("exit_code","expected_exit_code"),("earliest_stage","expected_earliest_stage"),("failure_class","expected_failure_class"),("failure_subcode","expected_failure_subcode"),("downstream_invalidated","expected_downstream_invalidated")):
        if actual[a]!=exp[e]:return False,f"wrong reason {a}: {actual[a]!r}"
    text=json.dumps(actual,sort_keys=True)
    for marker in exp["required_diagnostic_markers"]:
        if marker.lower() not in text.lower():return False,f"missing marker {marker!r}"
    return True,""


def self_test()->int:
    problems=[];observed=_fixture_observed();valid=sorted((FIXTURE_ROOT/"valid").glob("*.json"));invalid=sorted(p for p in (FIXTURE_ROOT/"invalid").glob("*.json") if not p.name.endswith(".expectation.json"))
    for path in valid:
        value,_raw,error=_load(path);findings=[error] if error else validate_authorization(value,observed)
        if any(findings):problems.append(f"{path.name}: valid rejected: {next(x for x in findings if x)}")
    for path in invalid:
        value,_raw,error=_load(path);local=dict(observed)
        if path.name=="nonunique-output.json":local["output_directory_exists"]=True
        finding=error
        if finding is None and value.get("schema")=="release-action-receipt-v1":
            issues=validate_schema_subset(value,_schema())
            if issues:
                issue=issues[0];finding=Finding("receipt_schema",f"schema-{issue.keyword.lower()}",f"terminal PASS receipt rejected: {issue.path}: {issue.message}")
        elif finding is None:
            findings=validate_authorization(value,local);finding=findings[0] if findings else None
        if finding is None:problems.append(f"{path.name}: invalid survived");continue
        ok,problem=_expectation_ok(path,finding)
        if not ok:problems.append(f"{path.name}: {problem}; got {finding}")
    value,raw,error=_load(FIXTURE_ROOT/"valid/exact-release-package-build.json")
    if error is None:
        with tempfile.TemporaryDirectory(prefix="daee-release-claim-") as directory:
            root=Path(directory);claim_path=root/"claims/release.claim.json";claim,first=consume_authorization(value,raw,observed,custody_root=root,claim_target=claim_path,claimed_at=observed["now"]);_again,replay=consume_authorization(value,raw,observed,custody_root=root,claim_target=claim_path,claimed_at=observed["now"])
            if first or claim is None or replay is None:problems.append("release claim replay was not rejected")
            receipt_path=root/"receipts/release.receipt.json";receipt,final_error=finalize_authorization(value,raw,claim_path,"UNKNOWN",custody_root=root,receipt_target=receipt_path,finalized_at=observed["now"]);_second,terminal_error=finalize_authorization(value,raw,claim_path,"FAILED",custody_root=root,receipt_target=receipt_path,finalized_at=observed["now"])
            if final_error or receipt is None or terminal_error is None:problems.append("release UNKNOWN/FAILED terminal receipt behavior failed")
    if problems:
        for problem in problems:print(f"FAIL: {problem}")
        return 1
    print(f"release action authorization self-test: PASS ({len(valid)} valid, {len(invalid)} invalid; injected observations only; no live authority)");return 0


def main(argv:Iterable[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--self-test",action="store_true");parser.add_argument("--manifest");parser.add_argument("--require-action",choices=[ACTION]);parser.add_argument("--consume-once",action="store_true");parser.add_argument("--claim-receipt");parser.add_argument("--finalize",action="store_true");parser.add_argument("--action-receipt");parser.add_argument("--result",choices=["PASS","FAILED","UNKNOWN"]);parser.add_argument("--test-observations",help=argparse.SUPPRESS);parser.add_argument("--explain",action="store_true");args=parser.parse_args(argv)
    if args.consume_once and args.finalize:parser.error("--consume-once and --finalize are separate state transitions")
    if args.finalize and (not args.claim_receipt or not args.action_receipt or not args.result):parser.error("--finalize requires claim/action receipt and result")
    if args.self_test:
        if any((args.manifest,args.consume_once,args.finalize,args.claim_receipt,args.action_receipt,args.test_observations)):parser.error("--self-test cannot emit authority")
        return self_test()
    if not args.manifest or not args.require_action:parser.error("--manifest and --require-action are required")
    manifest=Path(args.manifest);manifest=manifest if manifest.is_absolute() else ROOT/manifest
    finding:Finding|None=None;value:dict[str,Any]|None=None;raw=b""
    if args.consume_once or args.finalize:
        try:manifest=resolve_live_authorization_path(manifest)
        except (OSError,ValueError) as exc:finding=Finding("authority_custody","authorization-root",f"live release authority must resolve beneath the protected A16 root: {exc}")
    else:
        try:manifest=manifest.resolve(strict=True)
        except OSError:pass
    if finding is None:value,raw,finding=_load(manifest)
    if finding is None and value is not None:
        if value.get("action")!=args.require_action:finding=Finding("action_family","required-action","--require-action differs from immutable release authorization")
        elif args.finalize:
            issues=validate_schema_subset(value,_schema())
            if issues:
                issue=issues[0];finding=Finding("schema_contract",f"schema-{issue.keyword.lower()}",f"{issue.path}: {issue.message}")
    if finding is None and value is not None and (args.consume_once or args.finalize) and not _authority_file_protected(manifest):finding=Finding("authority_custody","writer-protection","live release authorization must be immutable at owner-protected writer boundary")
    observed:dict[str,Any]={}
    if finding is None and value is not None:
        if args.test_observations:
            if args.consume_once or args.finalize:parser.error("test observations are validation-only")
            try:manifest.relative_to(FIXTURE_ROOT.resolve())
            except ValueError:parser.error("test observations require a tracked release fixture")
            support=Path(args.test_observations);support=support if support.is_absolute() else ROOT/support;observed=dict(strict_json_loads(support.read_bytes(),label=str(support))["observed"])
        else:
            try:observed=collect_live_observation(value) if not args.finalize or result_requires_live_observation(str(args.result)) else {}
            except (OSError,ValueError,subprocess.SubprocessError) as exc:finding=Finding("live_observation","observation-failed",str(exc))
        if finding is None and not args.finalize:
            findings=validate_authorization(value,observed);finding=findings[0] if findings else None
        if finding is None and args.consume_once:
            if args.claim_receipt!=value["claim_locator"]:finding=Finding("claim_locator","claim-locator","--claim-receipt must equal predetermined locator")
            else:
                try:claim_path=resolve_live_custody_path(args.claim_receipt,"claims",must_exist=False)
                except PathCustodyError as exc:finding=Finding("claim_locator",exc.subcode,str(exc))
                else:_claim,finding=consume_authorization(value,raw,observed,custody_root=CUSTODY_ROOT,claim_target=claim_path,claimed_at=observed["now"])
        if finding is None and args.finalize:
            if args.claim_receipt!=value["claim_locator"]:finding=Finding("claim_locator","claim-locator","--claim-receipt must equal predetermined locator")
            elif args.action_receipt!=value["action_receipt_locator"]:finding=Finding("claim_locator","receipt-locator","--action-receipt differs")
            else:
                try:
                    claim_path=resolve_live_custody_path(args.claim_receipt,"claims",must_exist=True);receipt_path=resolve_live_custody_path(args.action_receipt,"receipts",must_exist=False)
                except PathCustodyError as exc:finding=Finding("claim_locator",exc.subcode,str(exc))
                else:_receipt,finding=finalize_authorization(value,raw,claim_path,args.result,custody_root=CUSTODY_ROOT,receipt_target=receipt_path,finalized_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    if finding:
        payload=diagnostic(finding,str(manifest));print(json.dumps(payload,sort_keys=True) if args.explain else f"release action authorization: FAIL [{finding.failure_class}/{finding.failure_subcode}]: {finding.message}");return 1
    print(json.dumps({"checker_id":CHECKER_ID,"status":"PASS"},sort_keys=True) if args.explain else "release action authorization: PASS");return 0


if __name__=="__main__":raise SystemExit(main())
