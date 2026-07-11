#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from contract_validation import PathCustodyError, resolve_repo_path, validate_schema_subset

ROOT = Path(__file__).resolve().parents[1]
CHECKER_ID = "captured-output-custody"
CAPTURE_SCHEMA = ROOT / "schema/captured-output-manifest.schema.json"
COMPARISON_SCHEMA = ROOT / "schema/captured-output-comparison.schema.json"


@dataclass(frozen=True)
class Finding:
    failure_class: str
    failure_subcode: str
    message: str
    earliest_stage: str = "preflight"
    downstream_invalidated: tuple[str, ...] = ("structural-replay", "topology-review", "cold-review", "promotion")


@dataclass(frozen=True)
class ArtifactSnapshot:
    """Contained artifact bytes captured once for validation and all later use."""

    canonical_path: Path
    relative_path: str
    data: bytes
    sha256: str
    byte_count: int

    @property
    def parent(self) -> Path:
        return self.canonical_path.parent

    def read_bytes(self) -> bytes:
        return self.data

    def read_text(self, encoding: str = "utf-8") -> str:
        return self.data.decode(encoding)

    def resolve(self) -> Path:
        return self.canonical_path


@dataclass(frozen=True)
class PublicationIdentity:
    """Identity receipt for deleting only the object this publisher created."""

    kind: str
    device: int
    inode: int
    ctime_ns: int
    payload_sha256: str


def _publication_identity(path: Path, kind: str, payload_sha256: str) -> PublicationIdentity:
    stat = path.stat(follow_symlinks=False)
    return PublicationIdentity(kind, stat.st_dev, stat.st_ino, stat.st_ctime_ns, payload_sha256)


ArtifactSource = Path | ArtifactSnapshot


def is_snapshot(value: Any) -> bool:
    return isinstance(value, ArtifactSnapshot) or (
        hasattr(value, "canonical_path") and hasattr(value, "data") and hasattr(value, "sha256")
    )


def snapshot_file(path: Path, root: Path) -> ArtifactSnapshot:
    resolved_root = root.resolve()
    if path.is_absolute():
        canonical = path.resolve(strict=True)
        try:
            canonical.relative_to(resolved_root)
        except ValueError as exc:
            raise PathCustodyError(
                f"resolved path escapes custody root: {path}", subcode="resolved-escape"
            ) from exc
        if not canonical.is_file():
            raise PathCustodyError(f"artifact is not a file: {path}", subcode="not-file")
    else:
        canonical = resolve_repo_path(resolved_root, path, must_exist=True, expect_file=True)
    data = canonical.read_bytes()
    return ArtifactSnapshot(
        canonical_path=canonical,
        relative_path=canonical.relative_to(resolved_root).as_posix(),
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
        byte_count=len(data),
    )


def read_json(source: ArtifactSource) -> Any:
    if is_snapshot(source):
        return json.loads(source.data.decode("utf-8"))
    return json.loads(source.read_text(encoding="utf-8"))


def schema_finding(value: Any, schema_path: Path, *, stage: str = "preflight", downstream: tuple[str, ...] = ()) -> list[Finding]:
    issues = validate_schema_subset(value, read_json(schema_path))
    if not issues:
        return []
    issue = issues[0]
    return [Finding("schema_contract", issue.keyword.replace("_", "-"), f"{issue.path}: {issue.message}", stage, downstream)]


def verify_artifact(ref: Any, root: Path, label: str) -> tuple[ArtifactSnapshot | None, list[Finding]]:
    if not isinstance(ref, dict):
        return None, [Finding("evidence_custody", "artifact-ref-shape", f"{label} must be a path/hash/byte_count object")]
    missing = [key for key in ("path", "sha256", "byte_count") if key not in ref]
    if missing:
        return None, [Finding("evidence_custody", f"missing-{label.replace('_','-')}-{missing[0]}", f"{label} missing {missing[0]}")]
    try:
        path = resolve_repo_path(root, ref["path"], must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        return None, [Finding("path_custody", exc.subcode, f"{label}: {exc}")]
    snapshot = snapshot_file(path, root)
    if snapshot.sha256 != ref.get("sha256"):
        return None, [Finding("evidence_custody", f"{label.replace('_','-')}-hash-drift", f"{label} hash readback differs")]
    if snapshot.byte_count != ref.get("byte_count"):
        return None, [Finding("evidence_custody", f"{label.replace('_','-')}-byte-count", f"{label} byte count differs")]
    return snapshot, []


class PublicationError(ValueError):
    pass


def _rename_directory_noreplace_windows(
    source: Path, target: Path, *, rename: Any = os.rename
) -> None:
    try:
        rename(source, target)
    except OSError as exc:
        if isinstance(exc, FileExistsError) or exc.errno in {errno.EEXIST, errno.ENOTEMPTY}:
            raise PublicationError("publication target already exists") from exc
        raise PublicationError(
            f"atomic no-replace directory publication failed on Windows: {exc}"
        ) from exc


def _rename_directory_noreplace_linux(
    source: Path, target: Path, *, renameat2: Any | None = None
) -> None:
    if renameat2 is None:
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            renameat2 = libc.renameat2
            renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
            renameat2.restype = ctypes.c_int
        except (AttributeError, OSError) as exc:
            raise PublicationError(
                "atomic no-replace directory publication is unavailable on this Linux runtime"
            ) from exc
    try:
        result = renameat2(
            -100,
            os.fsencode(source),
            -100,
            os.fsencode(target),
            1,
        )
    except OSError as exc:
        raise PublicationError(
            f"atomic no-replace directory publication failed on Linux: {exc}"
        ) from exc
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        raise PublicationError("publication target already exists")
    unsupported = {errno.ENOSYS, errno.EINVAL}
    unsupported.update(
        value for value in (getattr(errno, "EOPNOTSUPP", None), getattr(errno, "ENOTSUP", None)) if value is not None
    )
    if error in unsupported:
        raise PublicationError(
            "atomic no-replace directory publication is unavailable on this Linux filesystem"
        )
    raise PublicationError(
        f"atomic no-replace directory publication failed on Linux: errno {error}"
    )


def _rename_directory_noreplace(source: Path, target: Path) -> None:
    if os.name == "nt":
        _rename_directory_noreplace_windows(source, target)
        return
    if os.name == "posix" and sys.platform.startswith("linux"):
        _rename_directory_noreplace_linux(source, target)
        return
    raise PublicationError(
        f"atomic no-replace directory publication is unsupported platform: {sys.platform}"
    )


def _write_new_file(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def atomic_publish_bytes(
    target: Path, data: bytes, *, fault_at: str | None = None
) -> PublicationIdentity:
    """Stage, CAS-check, and publish a file without replacing an existing target."""
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = target.parent / f".{target.name}.stage-{uuid.uuid4().hex}"
    try:
        _write_new_file(stage, data)
        if fault_at == "after-stage-write":
            raise PublicationError("injected publication failure after stage write")
        if stage.read_bytes() != data:
            raise PublicationError("staged bytes changed before publication")
        if fault_at == "after-stage-verify":
            raise PublicationError("injected publication failure after stage verification")
        try:
            os.link(stage, target)
        except FileExistsError as exc:
            raise PublicationError("publication target already exists") from exc
        identity = _publication_identity(target, "file", hashlib.sha256(data).hexdigest())
        if fault_at == "after-publish":
            raise PublicationError("injected publication failure after publish")
        if target.read_bytes() != data:
            raise PublicationError("published bytes changed during final CAS readback")
        return identity
    finally:
        stage.unlink(missing_ok=True)


def atomic_publish_directory(
    target: Path, files: dict[str, bytes], *, fault_at: str | None = None
) -> PublicationIdentity:
    """Publish a complete same-parent directory without replacing a competitor."""
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = target.parent / f".{target.name}.stage-{uuid.uuid4().hex}"
    identity: PublicationIdentity | None = None
    try:
        stage.mkdir()
        for index, (name, data) in enumerate(files.items()):
            _write_new_file(stage / name, data)
            if fault_at == f"after-stage-file-{index}":
                raise PublicationError(f"injected publication failure after staged file {index}")
        if fault_at == "after-stage-write":
            raise PublicationError("injected publication failure after directory staging")
        if any((stage / name).read_bytes() != data for name, data in files.items()):
            raise PublicationError("staged directory bytes changed before publication")
        if fault_at == "after-stage-verify":
            raise PublicationError("injected publication failure after directory verification")
        _rename_directory_noreplace(stage, target)
        payload_sha256 = hashlib.sha256(
            b"".join(
                name.encode("utf-8") + b"\0" + hashlib.sha256(data).digest()
                for name, data in files.items()
            )
        ).hexdigest()
        identity = _publication_identity(target, "directory", payload_sha256)
        if fault_at == "after-publish":
            raise PublicationError("injected publication failure after directory publish")
        if any((target / name).read_bytes() != data for name, data in files.items()):
            raise PublicationError("published directory changed during final CAS readback")
        return identity
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def _refs(value: Any, prefix: str = "artifact"):
    if isinstance(value, dict):
        if {"path", "sha256", "byte_count"} <= set(value):
            yield prefix, value
            return
        for key, child in value.items():
            yield from _refs(child, f"{prefix}-{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _refs(child, f"{prefix}-{index}")


def validate_capture_manifest(path: ArtifactSource, custody_root: Path | None = None) -> list[Finding]:
    root = (custody_root or path.parent).resolve()
    source = path if is_snapshot(path) else snapshot_file(path, root)
    value = read_json(source)
    schema_issues = validate_schema_subset(value, read_json(CAPTURE_SCHEMA))
    if not isinstance(value.get("input"), dict) or "sha256" not in value["input"]:
        return [Finding("evidence_custody", "missing-input-hash", "input sha256 is required")]
    replay_shape=value.get("structural_replay",{})
    rows=replay_shape.get("checker_results") if isinstance(replay_shape,dict) else None
    checker_required={"checker_id","command","checker_source","checker_source_sha256","exit_code","stdout","stderr","first_failure"}
    if not isinstance(rows,list) or any(not isinstance(row,dict) or not checker_required <= set(row) for row in rows):
        return [Finding("structural_replay","checker-row-shape","each checker row requires command/source hash/exit/stdout/stderr/first-failure")]
    if value.get("runtime", {}).get("identity_source") != "external-custodian":
        return [Finding("evidence_custody", "self-attested-package", "package identity must come from an external custodian")]
    if schema_issues:
        issue=schema_issues[0];return [Finding("schema_contract",issue.keyword.replace("_","-"),f"{issue.path}: {issue.message}")]
    runtime=value.get("runtime",{});execution=value.get("execution",{});replay=value.get("structural_replay",{});historical=value.get("historical_provenance",{})
    groups=((runtime,("version_label","source_commit","package","build_manifest","identity_source"),"runtime"),(execution,("operator","model_runner","model","host","session_id","started_utc","fresh_session","tool_policy","output_budget","retry_policy","continuation_policy","retry_count","continuation_count","truncated","invocation"),"execution"),(replay,("verifier_commit","aggregate_status","first_failed_checker","checker_results","verdict"),"structural-replay"),(historical,("status","missing_fields","promotable"),"historical-provenance"))
    for group,required,label in groups:
        missing=[key for key in required if key not in group]
        if missing:return [Finding("evidence_custody",f"missing-{label}-{missing[0]}",f"{label} missing {missing[0]}")]
    snapshots: dict[tuple[Any, Any, Any], ArtifactSnapshot] = {}
    def held(ref: Any, label: str) -> tuple[ArtifactSnapshot | None,list[Finding]]:
        key=(ref.get("path"),ref.get("sha256"),ref.get("byte_count")) if isinstance(ref,dict) else (None,None,None)
        if key in snapshots:return snapshots[key],[]
        snapshot,ref_issues=verify_artifact(ref,root,label)
        if snapshot is not None:snapshots[key]=snapshot
        return snapshot,ref_issues
    for label, ref in _refs(value):
        _, issues = held(ref, label)
        if issues:
            return issues
    provenance = value["historical_provenance"]
    if provenance.get("status") == "incomplete" and provenance.get("promotable") is not False:
        return [Finding("claim_overreach", "incomplete-provenance-promotable", "incomplete historical provenance must remain nonpromotable")]
    replay = value["structural_replay"]
    checker_ids=[row["checker_id"] for row in replay["checker_results"]]
    if len(checker_ids)!=len(set(checker_ids)):return [Finding("structural_replay","duplicate-checker-id","checker IDs must be unique")]
    failed=[row for row in replay["checker_results"] if row["exit_code"]!=0]
    first=[row for row in replay["checker_results"] if row["first_failure"]]
    if replay["aggregate_status"]=="PASS" and (failed or first or replay["first_failed_checker"] is not None):return [Finding("structural_replay","aggregate-pass-inconsistent","PASS replay cannot contain failures")]
    if replay["aggregate_status"]=="FAIL":
        if not failed or len(first)!=1 or first[0]["checker_id"]!=replay["first_failed_checker"] or first[0] is not failed[0]:return [Finding("structural_replay","first-failure-inconsistent","FAIL replay must bind the ordered first failed checker exactly once")]
    if replay.get("aggregate_status") == "FAIL" and not replay.get("first_failed_checker"):
        return [Finding("structural_replay", "first-failure-missing", "failed replay requires first_failed_checker")]
    build_path,_=held(value["runtime"]["build_manifest"],"build-manifest");build=read_json(build_path)
    if build.get("schema")!="daee-package-build-manifest-v1" or build.get("source_commit")!=value["runtime"]["source_commit"]:return [Finding("runtime_identity","build-manifest-mismatch","build manifest does not bind the declared source commit")]
    if build.get("package_sha256")!=value["runtime"]["package"]["sha256"]:return [Finding("runtime_identity","package-build-binding","build manifest does not bind the exact package bytes")]
    if replay.get("verifier_commit")!=value["runtime"]["source_commit"]:return [Finding("structural_replay","verifier-source-binding","verifier commit differs from the captured runtime source commit")]
    checker_tuples=[]
    for row in replay["checker_results"]:
        source_snapshot,source_issues=held(row["checker_source"],"checker-source")
        if source_issues:return source_issues
        if source_snapshot.sha256!=row["checker_source_sha256"]:return [Finding("structural_replay","checker-source-binding","checker source artifact and declared source hash differ")]
        checker_tuples.append({"checker_id":row["checker_id"],"command":row["command"],"checker_source_sha256":row["checker_source_sha256"],"exit_code":row["exit_code"],"stdout_sha256":row["stdout"]["sha256"],"stderr_sha256":row["stderr"]["sha256"],"first_failure":row["first_failure"]})
    verdict_path,_=held(replay["verdict"],"verifier-verdict");verdict=read_json(verdict_path)
    if verdict.get("schema")!="daee-checker-replay-verdict-v1" or verdict.get("verifier_commit")!=replay["verifier_commit"] or verdict.get("output_sha256")!=value["output"]["sha256"] or verdict.get("aggregate_status")!=replay["aggregate_status"] or verdict.get("first_failed_checker")!=replay["first_failed_checker"] or verdict.get("checker_results")!=checker_tuples:return [Finding("structural_replay","verdict-identity-mismatch","verifier verdict does not bind verifier, output, aggregate, first failure, and ordered checker tuples")]
    topology_path,_=held(value["topology_review"],"topology-review")
    cold_path,_=held(value["cold_comprehensiveness_review"],"cold-review")
    from check_topology_review import validate_topology_review
    from check_cold_comprehensiveness_review import validate_cold_review
    nested=validate_topology_review(topology_path,root)
    if nested:return [Finding("cross_object","topology-review-invalid",f"topology review invalid: {nested[0].failure_class}/{nested[0].failure_subcode}")]
    nested=validate_cold_review(cold_path,root)
    if nested:return [Finding("cross_object","cold-review-invalid",f"cold review invalid: {nested[0].failure_class}/{nested[0].failure_subcode}")]
    topology=read_json(topology_path);cold=read_json(cold_path)
    for label,obj in (("topology",topology),("cold",cold)):
        if obj.get("case_id")!=value["case_id"] or obj.get("cycle_id")!=value["cycle_id"]:return [Finding("cross_object",f"{label}-identity-mismatch",f"{label} case/cycle differs from capture")]
    if topology["input"]["sha256"]!=value["input"]["sha256"] or topology["artifacts"]["stage07_output"]["sha256"]!=value["output"]["sha256"] or cold["input"]["sha256"]!=value["input"]["sha256"] or cold["output"]["sha256"]!=value["output"]["sha256"]:return [Finding("cross_object","review-artifact-mismatch","review input/output differs from capture")]
    expected_runtime=(value["runtime"]["source_commit"],value["runtime"]["package"]["sha256"])
    review_stage_refs=[*cold.get("stage_records",[]),*[topology.get("artifacts",{}).get(key) for key in ("stage02","stage04","stage05")]]
    for index,ref in enumerate(review_stage_refs):
        snapshot,stage_issues=verify_artifact(ref,root,f"review-stage-{index}")
        if stage_issues:return stage_issues
        try:stage=read_json(snapshot)
        except (UnicodeDecodeError,json.JSONDecodeError):return [Finding("cross_object","review-stage-shape","review stage is not canonical JSON")]
        if (stage.get("source_commit"),stage.get("package_sha256"))!=expected_runtime:return [Finding("cross_object","review-runtime-binding","review stage source/package identity differs from capture runtime")]
    required_nonclaims = {"structural PASS is not semantic truth", "one capture is not a cross-host behavior claim"}
    if not required_nonclaims <= set(value["non_claims"]):
        return [Finding("claim_overreach", "structural-nonclaims-missing", "required structural-only nonclaims are missing")]
    return []


def _controls(capture: dict[str, Any]) -> tuple[Any, ...]:
    execution = capture["execution"]
    return tuple(execution.get(key) for key in ("model_runner", "model", "host", "fresh_session", "tool_policy", "output_budget", "retry_policy", "continuation_policy", "retry_count", "continuation_count", "truncated"))


def validate_comparison_manifest(path: ArtifactSource, custody_root: Path | None = None) -> list[Finding]:
    root = (custody_root or path.parent).resolve()
    source = path if is_snapshot(path) else snapshot_file(path, root)
    value = read_json(source)
    issues = schema_finding(value, COMPARISON_SCHEMA, stage="control-plane", downstream=("causal-verdict", "promotion"))
    if issues:
        return issues
    cells = value["cells"]
    if [row.get("cell_id") for row in cells] != ["v45", "inherited-main", "pr9-base", "pr9-head"]:
        return [Finding("comparison_lineage", "cell-stack", "comparison cells must preserve the four-layer stack", "control-plane", ("causal-verdict", "promotion"))]
    captures: dict[str, dict[str, Any]] = {}
    by_cell: dict[str, list[dict[str, Any]]] = {}
    for cell in cells:
        rows = cell.get("captures", [])
        if (cell.get("status") == "not-run") != (rows == []):
            return [Finding("comparison_lineage", "not-run-cell-shape", "not-run cells must have an empty captures array", "control-plane", ("causal-verdict", "promotion"))]
        by_cell[cell["cell_id"]] = []
        for ref in rows:
            capture_path, ref_issues = verify_artifact(ref, root, "capture-manifest")
            if ref_issues:
                return ref_issues
            assert capture_path
            capture_issues = validate_capture_manifest(capture_path, root)
            if capture_issues:
                return capture_issues
            capture = read_json(capture_path)
            if capture["capture_id"] in captures:return [Finding("comparison_lineage","duplicate-capture-id","capture IDs must be unique before indexing","control-plane",("causal-verdict","promotion"))]
            if capture["runtime"]["source_commit"]!=cell.get("expected_source_commit") or capture["runtime"]["package"]["sha256"]!=cell.get("expected_package_sha256") or cell.get("source_layer")!=cell["cell_id"]:return [Finding("comparison_lineage","cell-source-binding","cell source layer/package/commit binding differs from capture","control-plane",("causal-verdict","promotion"))]
            captures[capture["capture_id"]] = capture
            by_cell[cell["cell_id"]].append(capture)
    pairings = value["pairings"]
    pair_ids=[row.get("pair_id") for row in pairings]
    if len(pair_ids)!=len(set(pair_ids)):return [Finding("comparison_lineage","duplicate-pair-id","pair IDs must be unique before indexing","control-plane",("causal-verdict","promotion"))]
    paired = []
    pair_keys=set()
    for pair in pairings:
        base, head = captures.get(pair.get("base_capture_id")), captures.get(pair.get("head_capture_id"))
        if base is None or head is None:
            return [Finding("comparison_lineage", "pair-capture-missing", "pairing references an absent capture", "control-plane", ("causal-verdict", "promotion"))]
        if base["input"]["sha256"] != head["input"]["sha256"]:
            return [Finding("comparison_join", "input-mismatch", "paired inputs differ", "control-plane", ("causal-verdict", "promotion"))]
        pair_key=(pair.get("base_capture_id"),pair.get("head_capture_id"))
        if pair_key in pair_keys:return [Finding("comparison_lineage","pair-reuse","one base/head capture pair cannot be counted repeatedly","control-plane",("causal-verdict","promotion"))]
        pair_keys.add(pair_key)
        paired.append((base, head))
    confounded = any(_controls(base) != _controls(head) for base, head in paired)
    status = value["regression_status"]
    if confounded and status != "confounded":
        return [Finding("comparison_confounder", "changed-control-unmarked", "changed execution control requires confounded status", "control-plane", ("causal-verdict", "promotion"))]
    if status == "replicated-candidate" and len(paired) < 2:
        return [Finding("claim_overreach", "regression-status-overclaim", "replicated-candidate requires at least two admissible pairs", "control-plane", ("causal-verdict", "promotion"))]
    if status == "candidate-observed" and len(paired) != 1:
        return [Finding("claim_overreach", "candidate-observed-pair-count", "candidate-observed requires exactly one admissible pair", "control-plane", ("causal-verdict", "promotion"))]
    directions=[]
    for base,head in paired:
        base_pass=base["structural_replay"]["aggregate_status"]=="PASS" and read_json(verify_artifact(base["topology_review"],root,"base-topology")[0]).get("verdict")=="PASS"
        head_pass=head["structural_replay"]["aggregate_status"]=="PASS" and read_json(verify_artifact(head["topology_review"],root,"head-topology")[0]).get("verdict")=="PASS"
        directions.append(base_pass and not head_pass)
    if value["attribution_target"]=="pr9":
        base_ids={c["capture_id"] for c in by_cell["pr9-base"]};head_ids={c["capture_id"] for c in by_cell["pr9-head"]}
        if any(pair.get("base_capture_id") not in base_ids or pair.get("head_capture_id") not in head_ids for pair in pairings):return [Finding("comparison_lineage","pr9-pair-layer","pr9 attribution requires pr9-base to pr9-head pairs","control-plane",("causal-verdict","promotion"))]
    if status=="candidate-observed" and directions!=[True]:return [Finding("claim_overreach","candidate-status-without-direction","candidate-observed requires one base-PASS/head-FAIL pair under the same controls","control-plane",("causal-verdict","promotion"))]
    if status=="replicated-candidate" and (len(directions)<2 or not all(directions)):return [Finding("claim_overreach","replicated-status-without-direction","replicated-candidate requires repeated same-direction admissible pairs","control-plane",("causal-verdict","promotion"))]
    if status=="not-observed" and any(base["structural_replay"]["aggregate_status"]=="PASS" or head["structural_replay"]["aggregate_status"]=="PASS" for base,head in paired):return [Finding("comparison_lineage","not-observed-direction","not-observed requires admissible paired observations that do not contain a passing causal endpoint","control-plane",("causal-verdict","promotion"))]
    return []


def diagnostic(finding: Finding, path: Path) -> dict[str, Any]:
    return {"checker_id": CHECKER_ID, "manifest_path": str(path), "exit_category": "structural-rejection", "exit_code": 1, "earliest_stage": finding.earliest_stage, "failure_class": finding.failure_class, "failure_subcode": finding.failure_subcode, "downstream_invalidated": list(finding.downstream_invalidated), "message": finding.message}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path); parser.add_argument("--comparison", type=Path); parser.add_argument("--custody-root", type=Path); parser.add_argument("--explain", action="store_true"); parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return subprocess.run([sys.executable, str(ROOT / "tests/captured-output-custody/test_contract.py")], cwd=ROOT).returncode
    raw = args.manifest or args.comparison
    if raw is None: parser.error("--manifest or --comparison required")
    root = (args.custody_root or ROOT).resolve()
    try:path=resolve_repo_path(root,raw,must_exist=True,expect_file=True)
    except PathCustodyError as exc:
        finding=Finding("path_custody",exc.subcode,str(exc));print(json.dumps(diagnostic(finding,Path(str(raw))),sort_keys=True) if args.explain else str(exc));return 1
    findings = validate_capture_manifest(path, root) if args.manifest else validate_comparison_manifest(path, root)
    if findings:
        print(json.dumps(diagnostic(findings[0], path), sort_keys=True) if args.explain else f"captured output custody: FAIL [{findings[0].failure_class}/{findings[0].failure_subcode}]: {findings[0].message}")
        return 1
    print(json.dumps({"checker_id":CHECKER_ID,"status":"PASS","manifest_path":str(path)},sort_keys=True) if args.explain else "captured output custody: PASS")
    return 0


if __name__ == "__main__": raise SystemExit(main())
