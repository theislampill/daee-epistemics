#!/usr/bin/env python3
"""Project one exact manifest-bound cohort of canonical replay verdicts."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from check_captured_output_manifest import PublicationError, atomic_publish_directory
from contract_validation import PathCustodyError, resolve_repo_path
from smoke_matrix_registry import load_registry as load_case_registry
from validation_registry import (
    canonical_sha256,
    profile_invocations,
    profile_map,
    sha256_bytes,
    snapshot_registry,
    validate_verdict,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_V1 = "model-compliance-scorecard-v1"
SCHEMA_V2 = "model-compliance-scorecard-v2"
MANIFEST_SCHEMA = "daee-scorecard-case-manifest-v1"
PROFILE_ID = "scorecard"
SOURCE_PROFILE = "captured-output-structural"
CASE_REGISTRY_REL = Path("tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json")
COMPLETENESS_STATUS = "COMPLETE_EXACT_CANONICAL_FIVE_CASE_AUTHORITY"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class JsonSnapshot:
    path: Path
    relative_path: str
    data: bytes
    sha256: str
    value: dict[str, Any]


def _snapshot_json(path: Path, root: Path, label: str) -> JsonSnapshot:
    try:
        resolved = resolve_repo_path(root, path, must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        raise ValueError(f"{label} must be a repository-relative file: {exc}") from exc
    data = resolved.read_bytes()
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} must be UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} root must be an object")
    return JsonSnapshot(
        path=resolved,
        relative_path=resolved.relative_to(root).as_posix(),
        data=data,
        sha256=sha256_bytes(data),
        value=value,
    )


def _manifest(snapshot: JsonSnapshot, registry_sha256: str) -> dict[str, Any]:
    value = snapshot.value
    required = {
        "schema",
        "cohort_id",
        "source_commit",
        "source_profile",
        "registry_path",
        "registry_sha256",
        "cases",
    }
    if set(value) != required:
        raise ValueError(f"case manifest must have exact keys {sorted(required)}")
    if value.get("schema") != MANIFEST_SCHEMA:
        raise ValueError(f"case manifest schema must be {MANIFEST_SCHEMA}")
    if not isinstance(value.get("cohort_id"), str) or not value["cohort_id"]:
        raise ValueError("case manifest cohort_id must be non-empty")
    if not isinstance(value.get("source_commit"), str) or not HEX40.fullmatch(value["source_commit"]):
        raise ValueError("case manifest source_commit must be exact lowercase 40-hex")
    if not isinstance(value.get("source_profile"), str) or not value["source_profile"]:
        raise ValueError("case manifest source_profile must be non-empty")
    if value["source_profile"] != SOURCE_PROFILE:
        raise ValueError(f"case manifest source_profile must be {SOURCE_PROFILE}")
    if value.get("registry_path") != "tools/validation-registry.json":
        raise ValueError("case manifest registry_path must name the canonical registry")
    if value.get("registry_sha256") != registry_sha256:
        raise ValueError("case manifest registry_sha256 differs from frozen canonical registry")
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("case manifest cases must be a non-empty array")
    case_ids: list[str] = []
    paths: list[str] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict) or set(case) != {"case_id", "source_verdict_path"}:
            raise ValueError(f"case manifest cases[{index}] must have exact case/path keys")
        case_id = case.get("case_id")
        source_path = case.get("source_verdict_path")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"case manifest cases[{index}].case_id must be non-empty")
        if not isinstance(source_path, str) or not source_path:
            raise ValueError(f"case manifest cases[{index}].source_verdict_path must be non-empty")
        case_ids.append(case_id)
        paths.append(source_path)
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("case manifest contains duplicate case_id")
    if len(paths) != len(set(paths)):
        raise ValueError("case manifest contains duplicate source_verdict_path")
    return value


def _cohort_authority(
    path: Path,
    root: Path,
) -> tuple[JsonSnapshot, dict[str, Any]]:
    snapshot = _snapshot_json(path, root, "cohort authorization case registry")
    if snapshot.relative_path != CASE_REGISTRY_REL.as_posix():
        raise ValueError(
            f"cohort authorization must be the canonical case registry {CASE_REGISTRY_REL.as_posix()}"
        )
    try:
        authority = load_case_registry(snapshot.path, root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"cohort authorization case registry rejected: {exc}") from exc
    if authority != snapshot.value or snapshot.path.read_bytes() != snapshot.data:
        raise ValueError("cohort authorization case registry changed during snapshot")
    return snapshot, authority


def _structural_result(row: dict[str, Any]) -> str:
    if row["exit_category"] == "accepted":
        return "accepted"
    if row["exit_category"] == "structural-rejection":
        return "structural-rejection"
    if row["exit_category"] == "not-run":
        return "not-run"
    return "indeterminate"


def _project_row(
    replay: JsonSnapshot,
    *,
    case_id: str,
    authority_case: dict[str, Any],
    cohort_id: str,
    source_commit: str,
    source_profile: str,
    registry: dict[str, Any],
    registry_sha256: str,
    root: Path,
) -> dict[str, Any]:
    verdict = replay.value
    findings = validate_verdict(verdict, registry, root=root, verify_files=True)
    if findings:
        first = findings[0]
        raise ValueError(
            f"{replay.relative_path}: replay verdict rejected "
            f"[{first.failure_class}/{first.failure_subcode}] {first.message}"
        )
    if verdict["verdict_id"] != case_id:
        raise ValueError(f"{replay.relative_path}: verdict_id differs from case manifest case_id")
    if verdict["source_commit"] != source_commit:
        raise ValueError(f"{replay.relative_path}: source_commit differs from case manifest")
    if verdict["selected_profile"] != source_profile:
        raise ValueError(f"{replay.relative_path}: selected_profile differs from case manifest source_profile")
    if verdict["registry_path"] != "tools/validation-registry.json" or verdict["registry_sha256"] != registry_sha256:
        raise ValueError(f"{replay.relative_path}: registry identity differs from cohort manifest")
    profile = profile_map(registry).get(source_profile)
    if profile is None:
        raise ValueError(f"case manifest source_profile is unknown: {source_profile}")
    required_checker_ids = [
        str(requirement["checker_id"])
        for requirement in profile["requirements"]
        if requirement["required"]
    ]
    observed = {str(result["checker_id"]) for result in verdict["checker_results"]}
    missing = [checker_id for checker_id in required_checker_ids if checker_id not in observed]
    projected_results = [
        {**json.loads(json.dumps(result)), "structural_result": _structural_result(result)}
        for result in verdict["checker_results"]
    ]
    artifacts = {str(row["role"]): row for row in verdict["artifacts"]}
    input_artifact = artifacts["input"]
    if (
        input_artifact["path"] != authority_case["input_path"]
        or str(input_artifact["sha256"]).upper() != authority_case["raw_sha256"]
    ):
        raise ValueError(
            f"{replay.relative_path}: input artifact differs from canonical cohort authorization custody"
        )
    return {
        "case_id": case_id,
        "cohort_id": cohort_id,
        "source_commit": source_commit,
        "source_profile": source_profile,
        "source_verdict_path": replay.relative_path,
        "input_path": input_artifact["path"],
        "input_sha256": input_artifact["sha256"],
        "output_sha256": artifacts["output"]["sha256"],
        "verdict_sha256": replay.sha256,
        "canonical_verdict_sha256": canonical_sha256(verdict),
        "registry_sha256": registry_sha256,
        "structural_status": verdict["aggregate_status"],
        "required_checker_ids": required_checker_ids,
        "required_checks": len(required_checker_ids),
        "missing_required_checker_ids": missing,
        "accepted_checks": sum(row["structural_result"] == "accepted" for row in projected_results),
        "rejected_checks": sum(row["structural_result"] == "structural-rejection" for row in projected_results),
        "not_run_checks": sum(row["structural_result"] == "not-run" for row in projected_results) + len(missing),
        "indeterminate_checks": sum(row["structural_result"] == "indeterminate" for row in projected_results),
        "topology_review_ref": None,
        "topology_review_status": "NOT_REVIEWED",
        "semantic_truth_status": "NOT_CLAIMED",
        "checker_results": projected_results,
    }


def build_scorecard(
    manifest_path: Path,
    host: str = "reference",
    *,
    root: Path = ROOT,
    case_registry_path: Path = CASE_REGISTRY_REL,
) -> dict[str, Any]:
    """Build a deterministic scorecard from one exact expected-case manifest."""

    root = root.resolve(strict=True)
    registry_snapshot = snapshot_registry(root=root)
    if profile_invocations(registry_snapshot.value, PROFILE_ID, root=root):
        raise ValueError("scorecard profile must remain projection-only with zero invocations")
    authority_snapshot, authority = _cohort_authority(case_registry_path, root)
    manifest_snapshot = _snapshot_json(manifest_path, root, "case manifest")
    manifest = _manifest(manifest_snapshot, registry_snapshot.sha256)
    authorized_case_ids = [str(case["case_id"]) for case in authority["cases"]]
    manifest_case_ids = [str(case["case_id"]) for case in manifest["cases"]]
    if manifest_case_ids != authorized_case_ids:
        raise ValueError(
            "cohort authorization requires the exact ordered canonical five-case registry IDs"
        )
    rows: list[dict[str, Any]] = []
    replay_snapshots: list[JsonSnapshot] = []
    for case, authority_case in zip(manifest["cases"], authority["cases"], strict=True):
        replay = _snapshot_json(Path(case["source_verdict_path"]), root, "replay verdict")
        replay_snapshots.append(replay)
        rows.append(
            _project_row(
                replay,
                case_id=str(case["case_id"]),
                authority_case=authority_case,
                cohort_id=str(manifest["cohort_id"]),
                source_commit=str(manifest["source_commit"]),
                source_profile=str(manifest["source_profile"]),
                registry=registry_snapshot.value,
                registry_sha256=registry_snapshot.sha256,
                root=root,
            )
        )
    if manifest_snapshot.path.read_bytes() != manifest_snapshot.data:
        raise ValueError("case manifest changed during scorecard projection")
    if registry_snapshot.canonical_path.read_bytes() != registry_snapshot.data:
        raise ValueError("validation registry changed during scorecard projection")
    if authority_snapshot.path.read_bytes() != authority_snapshot.data:
        raise ValueError("cohort authorization case registry changed during scorecard projection")
    try:
        authority_readback = load_case_registry(authority_snapshot.path, root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"cohort authorization input custody changed during projection: {exc}") from exc
    if authority_readback != authority:
        raise ValueError("cohort authorization case registry changed during scorecard projection")
    for replay in replay_snapshots:
        if replay.path.read_bytes() != replay.data:
            raise ValueError(f"replay verdict changed during scorecard projection: {replay.relative_path}")
    return {
        "schema": SCHEMA_V2,
        "selected_profile": PROFILE_ID,
        "registry_path": registry_snapshot.relative_path,
        "registry_sha256": registry_snapshot.sha256,
        "case_registry_path": authority_snapshot.relative_path,
        "case_registry_sha256": authority_snapshot.sha256,
        "cohort_manifest_path": manifest_snapshot.relative_path,
        "cohort_manifest_sha256": manifest_snapshot.sha256,
        "cohort_id": manifest["cohort_id"],
        "source_commit": manifest["source_commit"],
        "source_profile": manifest["source_profile"],
        "completeness_status": COMPLETENESS_STATUS,
        "capture_meta": {
            "host": host,
            "captured_from": "checker-replay-verdicts",
            "verdict_count": len(rows),
        },
        "rows": rows,
        "non_claims": [
            "record projection only; no detector or model execution",
            "structural replay is not semantic truth or uptake",
            "scorecard projection is not provenance, topology review, candidate maturity, or release readiness",
        ],
    }


def _validate_v1(scorecard: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(scorecard.get("capture_meta"), dict):
        errors.append("v1 scorecard capture_meta must be an object")
    rows = scorecard.get("rows")
    if not isinstance(rows, list):
        return errors + ["v1 scorecard rows must be an array"]
    required = {"failure_shape", "detector", "mode", "verdict"}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not required.issubset(row):
            errors.append(f"v1 row {index} is missing renderer fields")
            continue
        if row["verdict"] not in {"PASS", "FAIL", "NOT-RUN"}:
            errors.append(f"v1 row {row['failure_shape']!r} has invalid verdict")
    return errors


def _validate_v2(scorecard: dict[str, Any], root: Path) -> list[str]:
    expected_keys = {
        "schema",
        "selected_profile",
        "registry_path",
        "registry_sha256",
        "case_registry_path",
        "case_registry_sha256",
        "cohort_manifest_path",
        "cohort_manifest_sha256",
        "cohort_id",
        "source_commit",
        "source_profile",
        "completeness_status",
        "capture_meta",
        "rows",
        "non_claims",
    }
    if set(scorecard) != expected_keys:
        return [f"v2 scorecard must have exact keys {sorted(expected_keys)}"]
    capture_meta = scorecard.get("capture_meta")
    if not isinstance(capture_meta, dict) or set(capture_meta) != {"host", "captured_from", "verdict_count"}:
        return ["v2 capture_meta must have exact host/source/count keys"]
    if scorecard.get("selected_profile") != PROFILE_ID:
        return [f"v2 selected_profile must be {PROFILE_ID}"]
    if scorecard.get("completeness_status") != COMPLETENESS_STATUS:
        return ["v2 scorecard cannot claim completeness without exact canonical five-case authority"]
    try:
        rebuilt = build_scorecard(
            Path(str(scorecard["cohort_manifest_path"])),
            host=str(capture_meta["host"]),
            root=root,
            case_registry_path=Path(str(scorecard["case_registry_path"])),
        )
    except (KeyError, OSError, PathCustodyError, ValueError, json.JSONDecodeError) as exc:
        return [f"v2 source readback failed: {exc}"]
    if rebuilt != scorecard:
        return ["v2 scorecard differs from frozen manifest/replay/registry/artifact/tool projection"]
    return []


def validate_scorecard(scorecard: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    if not isinstance(scorecard, dict):
        return ["scorecard root must be an object"]
    errors: list[str] = []
    if not isinstance(scorecard.get("non_claims"), list) or not scorecard["non_claims"]:
        errors.append("scorecard must carry a non-empty non_claims block")
    if scorecard.get("schema") == SCHEMA_V1:
        return errors + _validate_v1(scorecard)
    if scorecard.get("schema") == SCHEMA_V2:
        return errors + _validate_v2(scorecard, root.resolve(strict=True))
    return errors + [f"unsupported scorecard schema {scorecard.get('schema')!r}"]


def to_markdown(scorecard: dict[str, Any]) -> str:
    host = scorecard.get("capture_meta", {}).get("host", "unknown")
    lines = [f"# Model-compliance scorecard ({host})", ""]
    if scorecard.get("schema") == SCHEMA_V1:
        lines.extend(["| failure_shape | detector | mode | verdict |", "| --- | --- | --- | --- |"])
        for row in scorecard["rows"]:
            lines.append(f"| {row['failure_shape']} | {row['detector']} | {row['mode']} | {row['verdict']} |")
    else:
        lines.extend(
            [
                "| case | structural_status | accepted | rejected | not_run | indeterminate |",
                "| --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in scorecard["rows"]:
            lines.append(
                f"| {row['case_id']} | {row['structural_status']} | {row['accepted_checks']} | "
                f"{row['rejected_checks']} | {row['not_run_checks']} | {row['indeterminate_checks']} |"
            )
    lines.extend(["", "non_claims:"])
    lines.extend(f"- {claim}" for claim in scorecard["non_claims"])
    return "\n".join(lines) + "\n"


def _protected_paths(scorecard: dict[str, Any], root: Path) -> set[Path]:
    case_registry_path = resolve_repo_path(
        root, scorecard["case_registry_path"], must_exist=True, expect_file=True
    )
    case_registry = load_case_registry(case_registry_path, root)
    protected = {
        resolve_repo_path(root, scorecard["registry_path"], must_exist=True, expect_file=True),
        case_registry_path,
        resolve_repo_path(root, scorecard["cohort_manifest_path"], must_exist=True, expect_file=True),
    }
    protected.update(
        resolve_repo_path(root, row["input_path"], must_exist=True, expect_file=True)
        for row in case_registry["cases"]
    )
    for row in scorecard["rows"]:
        replay_path = resolve_repo_path(root, row["source_verdict_path"], must_exist=True, expect_file=True)
        protected.add(replay_path)
        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        for artifact in replay["artifacts"]:
            protected.add(resolve_repo_path(root, artifact["path"], must_exist=True, expect_file=True))
        for result in replay["checker_results"]:
            protected.add(resolve_repo_path(root, result["tool_path"], must_exist=True, expect_file=True))
    return protected


def publish_scorecard(
    scorecard: dict[str, Any],
    out_dir: Path,
    *,
    root: Path = ROOT,
    fault_at: str | None = None,
) -> None:
    root = root.resolve(strict=True)
    errors = validate_scorecard(scorecard, root=root)
    if errors:
        raise ValueError(errors[0])
    try:
        target = resolve_repo_path(root, out_dir, must_exist=False)
    except PathCustodyError as exc:
        raise ValueError(f"out-dir must be repository-relative: {exc}") from exc
    if target in _protected_paths(scorecard, root):
        raise ValueError("out-dir collides with protected evidence")
    errors = validate_scorecard(scorecard, root=root)
    if errors:
        raise ValueError(f"scorecard evidence changed before publication: {errors[0]}")
    files = {
        "scorecard.json": (json.dumps(scorecard, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        "scorecard.md": to_markdown(scorecard).encode("utf-8"),
    }
    try:
        atomic_publish_directory(target, files, fault_at=fault_at)
    except PublicationError as exc:
        raise ValueError(str(exc)) from exc
    post_errors = validate_scorecard(scorecard, root=root)
    if post_errors:
        raise ValueError(f"scorecard evidence changed during publication: {post_errors[0]}")


def _legacy_sample() -> dict[str, Any]:
    return {
        "schema": SCHEMA_V1,
        "capture_meta": {"host": "legacy", "captured_from": "fixtures", "output_count": 0},
        "rows": [
            {"failure_shape": "legacy-shape", "detector": "check_legacy.py", "mode": "structural", "verdict": "NOT-RUN"}
        ],
        "non_claims": ["historical structural scorecard only"],
    }


def self_test() -> int:
    import tempfile
    from types import SimpleNamespace
    from verify_candidate_output import verify

    checks: list[tuple[str, bool]] = []
    legacy = _legacy_sample()
    checks.append(("v1 remains readable", validate_scorecard(legacy) == [] and "legacy-shape" in to_markdown(legacy)))
    authority = load_case_registry(ROOT / CASE_REGISTRY_REL, ROOT)
    source_commit = "a" * 40
    with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
        directory = Path(temp)
        cases = []
        for case in authority["cases"]:
            verdict = verify(
                Path(str(case["input_path"])),
                Path("tests/validation-integrity/artifacts/output.md"),
                profile_id=SOURCE_PROFILE,
                verdict_id=str(case["case_id"]),
                source_commit=source_commit,
                root=ROOT,
                run_process=lambda *_args, **_kwargs: SimpleNamespace(
                    returncode=0, stdout=b"accepted\n", stderr=b""
                ),
            )
            replay = directory / f"{verdict['verdict_id']}.json"
            replay.write_text(json.dumps(verdict), encoding="utf-8")
            cases.append(
                {
                    "case_id": verdict["verdict_id"],
                    "source_verdict_path": replay.relative_to(ROOT).as_posix(),
                }
            )
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "cohort_id": "self-test-cohort",
            "source_commit": source_commit,
            "source_profile": SOURCE_PROFILE,
            "registry_path": "tools/validation-registry.json",
            "registry_sha256": snapshot_registry().sha256,
            "cases": cases,
        }
        manifest_path = directory / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        projected = build_scorecard(manifest_path.relative_to(ROOT), host="self-test")
        checks.append(("v2 exact manifest projection", validate_scorecard(projected) == []))
        checks.append(("canonical five replay rows", len(projected["rows"]) == 5))
    ok = all(passed for _name, passed in checks)
    for name, passed in checks:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"model-compliance-scorecard self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-manifest", type=Path)
    parser.add_argument("--case-registry", type=Path, default=CASE_REGISTRY_REL)
    parser.add_argument("--read-scorecard", type=Path)
    parser.add_argument("--host", default="reference")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    try:
        if args.read_scorecard:
            scorecard = _snapshot_json(args.read_scorecard, ROOT, "scorecard").value
        elif args.case_manifest:
            scorecard = build_scorecard(
                args.case_manifest,
                host=args.host,
                case_registry_path=args.case_registry,
            )
        else:
            parser.error("provide --case-manifest, --read-scorecard, or --self-test")
        errors = validate_scorecard(scorecard)
        if errors:
            for error in errors:
                print(f"scorecard invalid: {error}", file=sys.stderr)
            return 1
        if args.out_dir:
            publish_scorecard(scorecard, args.out_dir)
    except (KeyError, OSError, PathCustodyError, ValueError, json.JSONDecodeError) as exc:
        print(f"scorecard failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(scorecard, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
