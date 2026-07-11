#!/usr/bin/env python3
"""Build observation, structural-pre-review, or reviewed-final records without layer upgrades."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from check_captured_output_manifest import PublicationError, atomic_publish_bytes
from check_smoke_matrix_manifest import validate_manifest
from smoke_matrix_registry import ROOT, validate_registry


def build(kind: str, matrix_id: str, *, structural_status: str="PARTIAL", completion_status: str="PARTIAL", reviews: list|None=None, candidate_status: str="CONSUMED_OBSERVED") -> dict:
    if kind=="cycle-observation": return {"schema":"daee-smoke-matrix-v1","kind":kind,"matrix_id":matrix_id,"observation_status":"FINALIZED","candidate_status":candidate_status}
    if kind=="structural-pre-review-verdict": raise ValueError("structural_replay_required: structural PASS is derived only from --registry and --cycle-root")
    if kind=="cycle-verdict": raise ValueError("review_contract_unavailable: final cycle verdict requires the A01 human/cold review join")
    raise ValueError("unsupported verdict kind")


def _contained_relative(path: Path, root: Path, label: str) -> str:
    try:
        lexical_root=root.absolute()
        current=Path(lexical_root.anchor)
        for part in lexical_root.parts[1:]:
            current=current/part;attributes=getattr(current.lstat(),"st_file_attributes",0)
            if current.is_symlink() or bool(attributes&0x400):raise ValueError(f"structural_path: {label} root contains symlink/reparse custody")
        resolved_root=root.resolve(strict=True);relative=path.resolve(strict=True).relative_to(resolved_root)
        current=resolved_root
        for part in relative.parts:
            current=current/part;attributes=getattr(current.lstat(),"st_file_attributes",0)
            if current.is_symlink() or bool(attributes&0x400):raise ValueError(f"structural_path: {label} contains symlink/reparse custody")
        return relative.as_posix()
    except (OSError,ValueError) as exc:raise ValueError(f"structural_path: {label} must resolve beneath the authorized root") from exc


def _external_cycle_binding(cycle_root: Path, manifest: dict, repo_root: Path) -> tuple[Path,str]:
    declared=manifest.get("evidence_custody_root")
    relative=manifest.get("cycle_root")
    if not isinstance(declared,str) or not declared or not isinstance(relative,str) or not relative:
        raise ValueError("structural_cycle_manifest: evidence custody root and relative cycle root are required")
    custody_root=Path(declared)
    if not custody_root.is_absolute():raise ValueError("structural_path: evidence custody root must be absolute")
    # `_contained_relative` performs the lexical reparse walk before resolving.
    observed=_contained_relative(cycle_root,custody_root,"cycle root")
    custody_root=custody_root.resolve(strict=True)
    resolved_repo=repo_root.resolve(strict=True);resolved_cycle=cycle_root.resolve(strict=True)
    overlaps=False
    for child,parent in ((custody_root,resolved_repo),(resolved_repo,custody_root),(resolved_cycle,resolved_repo)):
        try:child.relative_to(parent);overlaps=True
        except ValueError:pass
    if overlaps:raise ValueError("structural_path: evidence custody and resolved cycle roots must not overlap the mutable checkout")
    if observed!=relative:raise ValueError("structural_path: cycle root differs from its authorization-bound custody path")
    return custody_root,observed


def publish_verdict(path: Path, data: dict) -> str:
    raw=(json.dumps(data,indent=2,sort_keys=True)+"\n").encode()
    try:atomic_publish_bytes(path,raw)
    except PublicationError as exc:raise ValueError("structural_verdict_exists: verdict destination must be fresh and unused") from exc
    try:readback=path.read_bytes()
    except OSError as exc:raise ValueError(f"structural_verdict_readback: {exc}") from exc
    expected=hashlib.sha256(raw).hexdigest()
    if readback!=raw or hashlib.sha256(readback).hexdigest()!=expected:raise ValueError("structural_verdict_readback: published verdict bytes/hash drifted")
    return expected


def validate_output_destination(path: Path, cycle_root: Path) -> None:
    try:resolved_cycle=cycle_root.resolve(strict=True)
    except OSError as exc:raise ValueError(f"structural_output_path: cycle root unavailable: {exc}") from exc
    if path.name!="structural-pre-review-verdict.json" or path.absolute().parent!=cycle_root.absolute():raise ValueError("structural_output_path: --out must be the exact cycle-root structural-pre-review-verdict.json")
    current=Path(cycle_root.absolute().anchor)
    for part in cycle_root.absolute().parts[1:]:
        current=current/part;attributes=getattr(current.lstat(),"st_file_attributes",0)
        if current.is_symlink() or bool(attributes&0x400):raise ValueError("structural_output_path: cycle/output custody contains symlink or reparse")
    try:path.absolute().parent.resolve(strict=True).relative_to(resolved_cycle)
    except (OSError,ValueError) as exc:raise ValueError("structural_output_path: output escapes bound cycle root") from exc
    if path.exists() or path.is_symlink():raise ValueError("structural_verdict_exists: verdict destination must be fresh and unused")


def build_structural_verdict(registry_path: Path, cycle_root: Path, *, root: Path=ROOT) -> dict:
    try:registry_raw=registry_path.read_bytes();registry=json.loads(registry_raw)
    except (OSError,json.JSONDecodeError) as exc:raise ValueError(f"structural_registry_binding: {exc}") from exc
    registry_errors=validate_registry(registry,root)
    if registry_errors:raise ValueError(f"{registry_errors[0]['failure_class']}: {registry_errors[0]['message']}")
    registry_relative=_contained_relative(registry_path,root,"registry")
    manifest_path=cycle_root/"cycle-manifest.json"
    try:raw=manifest_path.read_bytes();manifest=json.loads(raw)
    except (OSError,json.JSONDecodeError) as exc:raise ValueError(f"structural_cycle_manifest: {exc}") from exc
    if not isinstance(manifest,dict):raise ValueError("structural_cycle_manifest: cycle manifest must be an object")
    custody_root,cycle_relative=_external_cycle_binding(cycle_root,manifest,root)
    required_identity=("cycle_id","candidate_id","source_commit","package_sha256","package_tree_sha256","package_root","registry_sha256","campaign_authorization_sha256","matrix_authorization_sha256")
    if any(not manifest.get(field) for field in required_identity):raise ValueError("structural_cycle_manifest: complete root identity is required")
    registry_sha256=hashlib.sha256(registry_raw).hexdigest()
    if manifest["registry_sha256"]!=registry_sha256:raise ValueError("structural_registry_binding: cycle manifest registry hash mismatch")
    artifact_fields=("matrix_authorization","ci_readback","candidate_maturity","dispatch_manifest","candidate_record","cycle_claim","candidate_consumption","usage_ledger","usage_receipt","observation_finalizer","evidence_export","package_harness_parity")
    if any(not isinstance(manifest.get(field),dict) for field in artifact_fields) or not isinstance(manifest.get("cases"),list):
        raise ValueError("structural_cycle_manifest: prerequisite references are incomplete")
    verdict={
        "schema":"daee-smoke-matrix-v1","kind":"structural-pre-review-verdict",
        "matrix_id":manifest["cycle_id"],"structural_matrix_status":"PASS","completion_status":"PARTIAL",
        "source_commit":manifest["source_commit"],"candidate_id":manifest["candidate_id"],
        "package_sha256":manifest["package_sha256"],"package_tree_sha256":manifest["package_tree_sha256"],
        "package_root":manifest["package_root"],
        "campaign_authorization_sha256":manifest["campaign_authorization_sha256"],
        "matrix_authorization_sha256":manifest["matrix_authorization_sha256"],
        "registry":{"path":registry_relative,"sha256":registry_sha256},
        "evidence_custody_root":str(custody_root),
        "cycle_root":cycle_relative,
        "cycle_manifest":{"path":"cycle-manifest.json","sha256":hashlib.sha256(raw).hexdigest()},
        **{field:manifest[field] for field in artifact_fields},
        "cases":manifest["cases"],
        "non_claims":["structural PASS is not semantic truth","structural pre-review PASS cannot authorize cold review or final completion by itself"],
    }
    errors=validate_manifest(verdict,root=root)
    if errors:raise ValueError(f"{errors[0]['failure_class']}: {errors[0]['message']}")
    if [row["case_id"] for row in registry["cases"]]!=[row["case_id"] for row in verdict["cases"]]:raise ValueError("five_case_set: structural verdict cases differ from canonical registry")
    return verdict


def self_test() -> int:
    obs=build("cycle-observation","m")
    forged={"schema":"daee-smoke-matrix-v1","kind":"structural-pre-review-verdict","matrix_id":"m","structural_matrix_status":"PASS","non_claims":["structural PASS is not semantic truth"]}
    structural_blocked=bool(validate_manifest(forged))
    try:
        build("cycle-verdict","m",structural_status="PASS",completion_status="PASS",reviews=[{"status":"PASS"} for _ in range(5)])
        final_blocked=False
    except ValueError as exc:
        final_blocked="review_contract_unavailable" in str(exc)
    checks=[("observation neutral",not validate_manifest(obs) and "completion_status" not in obs),("unbound structural PASS rejected",structural_blocked),("reviewed final blocked pending A01 join",final_blocked)]
    for n,o in checks:print(f"  self-test {'PASS' if o else 'FAIL'}: {n}")
    return 0 if all(o for _,o in checks) else 1


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("structural-pre-review","completion"));p.add_argument("--registry",type=Path);p.add_argument("--cycle-root",type=Path);p.add_argument("--out",type=Path);p.add_argument("--self-test",action="store_true");a=p.parse_args()
    if a.self_test:return self_test()
    if not a.mode or not a.out:p.error("--mode --out required")
    try:
        if a.mode=="completion":raise ValueError("review_contract_unavailable: final cycle verdict requires the A01 human/cold review join")
        if not a.registry or not a.cycle_root:raise ValueError("structural_replay_required: --registry and --cycle-root are required")
        validate_output_destination(a.out,a.cycle_root)
        data=build_structural_verdict(a.registry,a.cycle_root)
    except ValueError as exc:
        failure_class=str(exc).split(":",1)[0]
        print(json.dumps({"status":"FAIL","errors":[{"failure_class":failure_class,"message":str(exc)}]},sort_keys=True));return 1
    try:publish_verdict(a.out,data)
    except ValueError as exc:
        print(json.dumps({"status":"FAIL","errors":[{"failure_class":str(exc).split(":",1)[0],"message":str(exc)}]},sort_keys=True));return 1
    return 0


if __name__=="__main__":sys.exit(main())
