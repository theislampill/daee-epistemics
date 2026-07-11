#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_model_compliance_scorecard as scorecard  # noqa: E402
import verify_candidate_output as candidate  # noqa: E402
from smoke_matrix_registry import load_registry as load_case_registry  # noqa: E402
from validation_registry import registry_hash  # noqa: E402


SOURCE_COMMIT = "a" * 40
SOURCE_PROFILE = "captured-output-structural"
CASE_REGISTRY = load_case_registry()
CASE_IDS = tuple(row["case_id"] for row in CASE_REGISTRY["cases"])
CASE_BY_ID = {row["case_id"]: row for row in CASE_REGISTRY["cases"]}


class ScorecardHardeningTests(unittest.TestCase):
    def _verdict(
        self,
        verdict_id: str = CASE_IDS[0],
        source_commit: str = SOURCE_COMMIT,
        *,
        input_path: Path | None = None,
    ) -> dict:
        return candidate.verify(
            input_path or Path(CASE_BY_ID[verdict_id]["input_path"]),
            Path("tests/validation-integrity/artifacts/output.md"),
            profile_id=SOURCE_PROFILE,
            verdict_id=verdict_id,
            source_commit=source_commit,
            root=ROOT,
            run_process=lambda *_args, **_kwargs: SimpleNamespace(
                returncode=0, stdout=b"accepted\n", stderr=b""
            ),
        )

    def _verdicts(self, source_commit: str = SOURCE_COMMIT) -> list[dict]:
        return [self._verdict(case_id, source_commit) for case_id in CASE_IDS]

    def _write_cohort(self, directory: Path, verdicts: list[dict]) -> tuple[Path, list[Path]]:
        replay_paths: list[Path] = []
        cases: list[dict[str, str]] = []
        for verdict in verdicts:
            path = directory / f"{verdict['verdict_id']}.verdict.json"
            path.write_text(json.dumps(verdict), encoding="utf-8")
            replay_paths.append(path)
            cases.append(
                {
                    "case_id": verdict["verdict_id"],
                    "source_verdict_path": path.relative_to(ROOT).as_posix(),
                }
            )
        manifest = {
            "schema": "daee-scorecard-case-manifest-v1",
            "cohort_id": "cohort-alpha",
            "source_commit": SOURCE_COMMIT,
            "source_profile": SOURCE_PROFILE,
            "registry_path": "tools/validation-registry.json",
            "registry_sha256": registry_hash(),
            "cases": cases,
        }
        manifest_path = directory / "case-manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path, replay_paths

    def test_manifest_bound_projection_roundtrips_without_detector_execution(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            manifest, _replays = self._write_cohort(Path(temp), self._verdicts())
            with patch.object(subprocess, "run", side_effect=AssertionError("detector execution forbidden")):
                projected = scorecard.build_scorecard(manifest.relative_to(ROOT), host="fixture", root=ROOT)
            self.assertEqual("model-compliance-scorecard-v2", projected["schema"])
            self.assertEqual("cohort-alpha", projected["cohort_id"])
            self.assertEqual(SOURCE_COMMIT, projected["source_commit"])
            self.assertEqual(SOURCE_PROFILE, projected["source_profile"])
            self.assertEqual("COMPLETE_EXACT_CANONICAL_FIVE_CASE_AUTHORITY", projected["completeness_status"])
            self.assertEqual(5, len(projected["rows"]))
            row = projected["rows"][0]
            self.assertEqual("cohort-alpha", row["cohort_id"])
            self.assertEqual(SOURCE_COMMIT, row["source_commit"])
            self.assertEqual(SOURCE_PROFILE, row["source_profile"])
            self.assertEqual(12, row["required_checks"])
            self.assertEqual(12, len(row["required_checker_ids"]))
            self.assertEqual("PASS_STRUCTURAL", row["structural_status"])
            self.assertEqual([], scorecard.validate_scorecard(projected, root=ROOT))

    def test_newly_authored_subset_manifest_cannot_self_authorize_completeness(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            directory = Path(temp)
            manifest, _replays = self._write_cohort(directory, self._verdicts())
            full = scorecard.build_scorecard(manifest.relative_to(ROOT), root=ROOT)
            self.assertEqual(5, len(full["rows"]))
            for label, mutate in (
                ("subset", lambda value: value.update(cases=value["cases"][:-1])),
                ("reorder", lambda value: value.update(cases=list(reversed(value["cases"])))),
            ):
                with self.subTest(label=label):
                    unauthorized = json.loads(manifest.read_text(encoding="utf-8"))
                    mutate(unauthorized)
                    unauthorized_path = directory / f"{label}-manifest.json"
                    unauthorized_path.write_text(json.dumps(unauthorized), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "cohort authorization"):
                        scorecard.build_scorecard(unauthorized_path.relative_to(ROOT), root=ROOT)

    def test_authority_input_custody_is_reloaded_before_projection_returns(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            manifest, _replays = self._write_cohort(Path(temp), self._verdicts())
            with patch.object(
                scorecard,
                "load_case_registry",
                side_effect=[copy.deepcopy(CASE_REGISTRY), ValueError("registry_input_hash")],
            ):
                with self.assertRaisesRegex(ValueError, "input custody changed"):
                    scorecard.build_scorecard(manifest.relative_to(ROOT), root=ROOT)

    def test_canonical_case_id_cannot_relabel_another_authorized_input(self) -> None:
        verdicts = self._verdicts()
        verdicts[0] = self._verdict(
            CASE_IDS[0],
            input_path=Path(CASE_BY_ID[CASE_IDS[1]]["input_path"]),
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            manifest, _replays = self._write_cohort(Path(temp), verdicts)
            with self.assertRaisesRegex(ValueError, "canonical cohort authorization custody"):
                scorecard.build_scorecard(manifest.relative_to(ROOT), root=ROOT)

    def test_readback_rejects_forged_status_counts_paths_hashes_results_and_subsets(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            manifest, _replays = self._write_cohort(Path(temp), self._verdicts())
            projected = scorecard.build_scorecard(manifest.relative_to(ROOT), root=ROOT)
            mutations = {
                "status": lambda value: value["rows"][0].update(structural_status="FAIL_STRUCTURAL"),
                "count": lambda value: value["rows"][0].update(required_checks=999),
                "path": lambda value: value["rows"][0].update(source_verdict_path="missing.json"),
                "hash": lambda value: value["rows"][0].update(verdict_sha256="0" * 64),
                "result": lambda value: value["rows"][0]["checker_results"].pop(),
                "source": lambda value: value["rows"][0].update(source_commit="b" * 40),
                "subset": lambda value: value.update(rows=[]),
            }
            for label, mutate in mutations.items():
                with self.subTest(label=label):
                    forged = copy.deepcopy(projected)
                    mutate(forged)
                    self.assertTrue(scorecard.validate_scorecard(forged, root=ROOT))

    def test_manifest_rejects_duplicate_cases_paths_and_mixed_source_identity(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            directory = Path(temp)
            manifest, _replays = self._write_cohort(directory, self._verdicts())
            value = json.loads(manifest.read_text(encoding="utf-8"))
            for label, mutation in (
                ("duplicate-case", lambda item: item["cases"].append(copy.deepcopy(item["cases"][0]))),
                ("duplicate-path", lambda item: item["cases"].append({"case_id": "case-extra", "source_verdict_path": item["cases"][0]["source_verdict_path"]})),
            ):
                with self.subTest(label=label):
                    mutated = copy.deepcopy(value)
                    mutation(mutated)
                    manifest.write_text(json.dumps(mutated), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "manifest"):
                        scorecard.build_scorecard(manifest.relative_to(ROOT), root=ROOT)
            manifest.write_text(json.dumps(value), encoding="utf-8")
            mixed = self._verdict(CASE_IDS[-1], source_commit="b" * 40)
            replay = directory / "mixed.verdict.json"
            replay.write_text(json.dumps(mixed), encoding="utf-8")
            value["cases"][-1] = {
                "case_id": CASE_IDS[-1],
                "source_verdict_path": replay.relative_to(ROOT).as_posix(),
            }
            manifest.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source_commit"):
                scorecard.build_scorecard(manifest.relative_to(ROOT), root=ROOT)

    def test_directory_publication_is_collision_safe_no_replace_and_crash_atomic(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            directory = Path(temp)
            manifest, replays = self._write_cohort(directory, self._verdicts())
            projected = scorecard.build_scorecard(manifest.relative_to(ROOT), root=ROOT)
            for protected in (
                Path("tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json"),
                Path(CASE_REGISTRY["cases"][0]["input_path"]),
            ):
                with self.subTest(protected=protected), self.assertRaisesRegex(ValueError, "protected evidence"):
                    scorecard.publish_scorecard(projected, protected, root=ROOT)
            with self.assertRaisesRegex(ValueError, "protected evidence"):
                scorecard.publish_scorecard(projected, replays[0].relative_to(ROOT), root=ROOT)
            target = directory / "published"
            with self.assertRaisesRegex(ValueError, "injected publication failure"):
                scorecard.publish_scorecard(
                    projected,
                    target.relative_to(ROOT),
                    root=ROOT,
                    fault_at="after-stage-file-0",
                )
            self.assertFalse(target.exists())
            scorecard.publish_scorecard(projected, target.relative_to(ROOT), root=ROOT)
            self.assertEqual({"scorecard.json", "scorecard.md"}, {path.name for path in target.iterdir()})
            before = {path.name: path.read_bytes() for path in target.iterdir()}
            with self.assertRaisesRegex(ValueError, "target already exists"):
                scorecard.publish_scorecard(projected, target.relative_to(ROOT), root=ROOT)
            self.assertEqual(before, {path.name: path.read_bytes() for path in target.iterdir()})

    def test_wrapper_cleanup_never_deletes_swapped_directory_competitor(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            directory = Path(temp)
            manifest, _replays = self._write_cohort(directory, self._verdicts())
            projected = scorecard.build_scorecard(manifest.relative_to(ROOT), root=ROOT)
            target = directory / "published"
            calls = 0

            def validate_then_swap(*_args, **_kwargs):
                nonlocal calls
                calls += 1
                if calls == 3:
                    shutil.rmtree(target)
                    target.mkdir()
                    (target / "owner.txt").write_bytes(b"competitor-owned\n")
                    return ["swapped evidence"]
                return []

            with patch.object(scorecard, "validate_scorecard", side_effect=validate_then_swap):
                with self.assertRaisesRegex(ValueError, "changed during publication"):
                    scorecard.publish_scorecard(projected, target.relative_to(ROOT), root=ROOT)
            self.assertEqual(b"competitor-owned\n", (target / "owner.txt").read_bytes())

    def test_readback_rejects_artifact_tool_and_registry_drift(self) -> None:
        verdicts = self._verdicts()
        for target_kind in ("artifact", "tool", "registry", "case-registry"):
            with self.subTest(target_kind=target_kind), tempfile.TemporaryDirectory(
                dir=ROOT / "tests/validation-integrity"
            ) as temp:
                scratch = Path(temp)
                for directory in ("schema", "tools", "tests/validation-integrity/artifacts", "evidence"):
                    (scratch / directory).mkdir(parents=True, exist_ok=True)
                authority_files = [
                    "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json",
                    *(row["input_path"] for row in CASE_REGISTRY["cases"]),
                ]
                for relative in (
                    "schema/validation-registry.schema.json",
                    "schema/checker-replay-verdict.schema.json",
                    "tools/validation-registry.json",
                    "tests/validation-integrity/artifacts/input.txt",
                    "tests/validation-integrity/artifacts/output.md",
                    *authority_files,
                ):
                    (scratch / relative).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(ROOT / relative, scratch / relative)
                for snapshot_row in verdicts[0]["execution_snapshot"]["files"]:
                    relative = Path(snapshot_row["path"])
                    (scratch / relative).parent.mkdir(parents=True, exist_ok=True)
                    if not (scratch / relative).exists():
                        shutil.copy2(ROOT / relative, scratch / relative)
                registry = json.loads((ROOT / "tools/validation-registry.json").read_text(encoding="utf-8"))
                for row in [*registry["checkers"], *registry["consumers"]]:
                    source = Path(row["source_path"])
                    if not (scratch / source).exists():
                        shutil.copy2(ROOT / source, scratch / source)
                cases = []
                for verdict in verdicts:
                    replay = scratch / f"evidence/{verdict['verdict_id']}.json"
                    replay.write_text(json.dumps(verdict), encoding="utf-8")
                    cases.append(
                        {
                            "case_id": verdict["verdict_id"],
                            "source_verdict_path": replay.relative_to(scratch).as_posix(),
                        }
                    )
                manifest = scratch / "evidence/manifest.json"
                manifest.write_text(
                    json.dumps(
                        {
                            "schema": "daee-scorecard-case-manifest-v1",
                            "cohort_id": "cohort-alpha",
                            "source_commit": SOURCE_COMMIT,
                            "source_profile": SOURCE_PROFILE,
                            "registry_path": "tools/validation-registry.json",
                            "registry_sha256": registry_hash(root=scratch),
                            "cases": cases,
                        }
                    ),
                    encoding="utf-8",
                )
                projected = scorecard.build_scorecard(Path("evidence/manifest.json"), root=scratch)
                if target_kind == "artifact":
                    target = scratch / "tests/validation-integrity/artifacts/output.md"
                elif target_kind == "tool":
                    target = scratch / verdicts[0]["checker_results"][0]["tool_path"]
                elif target_kind == "case-registry":
                    target = scratch / "tests/smoke-matrix/v0.4.6.0-wip-five-smoke.json"
                else:
                    target = scratch / "tools/validation-registry.json"
                target.write_bytes(target.read_bytes() + b"\n")
                self.assertTrue(scorecard.validate_scorecard(projected, root=scratch))

    def test_v1_validator_requires_every_renderer_field(self) -> None:
        legacy = {
            "schema": "model-compliance-scorecard-v1",
            "capture_meta": {"host": "legacy"},
            "rows": [{"verdict": "NOT-RUN"}],
            "non_claims": ["legacy"],
        }
        self.assertTrue(scorecard.validate_scorecard(legacy, root=ROOT))


if __name__ == "__main__":
    unittest.main()
