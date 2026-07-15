#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import inspect
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import checker_execution_snapshot as checker_snapshot
import execution_tooling_manifest as tooling_manifest
import finalize_single_call_stage_capture as strict_finalizer
import run_staged_current_skill_smoke as stage_runner


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)
    return completed.stdout.strip()


class ExecutionToolingManifestContract(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="daee-tooling-manifest-")
        self.root = Path(self.temporary.name)
        plan = stage_runner.stage07_release_invocation_plan(
            ROOT,
            ROOT / ".daee" / "execution-tooling-manifest-test-output.md",
        )
        sources = checker_snapshot.execution_snapshot_sources(root=ROOT, plan=plan)
        for relative, source in sources.items():
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        _git(self.root, "init", "--quiet")
        _git(self.root, "config", "core.autocrlf", "false")
        _git(self.root, "config", "user.email", "tooling-manifest-test@example.invalid")
        _git(self.root, "config", "user.name", "Tooling Manifest Test")
        _git(self.root, "add", "--all")
        _git(self.root, "commit", "--quiet", "-m", "fixture")
        self.source_commit = _git(self.root, "rev-parse", "HEAD")
        (self.root / "evidence").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_create_once_manifest_binds_git_blobs_and_exact_live_bytes(self) -> None:
        manifest_ref = tooling_manifest.publish_execution_tooling_manifest(
            root=self.root,
            source_commit=self.source_commit,
            output_path="evidence/stage07-execution-tooling.json",
        )
        observed = tooling_manifest.load_and_verify_execution_tooling_manifest(
            root=self.root,
            manifest_ref=manifest_ref,
            expected_source_commit=self.source_commit,
        )
        self.assertEqual("daee-stage07-execution-tooling-manifest-v1", observed["schema"])
        self.assertEqual("stage07-release", observed["profile"])
        self.assertEqual(len(observed["files"]), observed["file_count"])
        self.assertTrue(any(row["path"] == "tools/finalize_single_call_stage_capture.py" for row in observed["files"]))
        self.assertTrue(any(row["path"] == "schema/producer-capture-complete.schema.json" for row in observed["files"]))
        self.assertTrue(any(row["path"].startswith("tests/") for row in observed["files"]))
        with self.assertRaisesRegex(tooling_manifest.ExecutionToolingManifestError, "already exists"):
            tooling_manifest.publish_execution_tooling_manifest(
                root=self.root,
                source_commit=self.source_commit,
                output_path="evidence/stage07-execution-tooling.json",
            )

    def test_dirty_checker_dependency_fails_closed(self) -> None:
        manifest_ref = tooling_manifest.publish_execution_tooling_manifest(
            root=self.root,
            source_commit=self.source_commit,
            output_path="evidence/stage07-execution-tooling.json",
        )
        dependency = self.root / "tools" / "checker_execution_snapshot.py"
        dependency.write_bytes(dependency.read_bytes() + b"\n# unauthorized drift\n")
        with self.assertRaisesRegex(tooling_manifest.ExecutionToolingManifestError, "working byte drift"):
            tooling_manifest.load_and_verify_execution_tooling_manifest(
                root=self.root,
                manifest_ref=manifest_ref,
                expected_source_commit=self.source_commit,
            )

    def test_tracked_governed_member_deleted_after_source_commit_fails_closed(self) -> None:
        deleted = self.root / "tools" / "committed-governed-member.txt"
        deleted.write_text("committed execution dependency\n", encoding="utf-8")
        _git(self.root, "add", "tools/committed-governed-member.txt")
        _git(self.root, "commit", "--quiet", "-m", "add governed member")
        source_commit = _git(self.root, "rev-parse", "HEAD")
        deleted.unlink()

        with self.assertRaisesRegex(tooling_manifest.ExecutionToolingManifestError, "file membership drift"):
            tooling_manifest.publish_execution_tooling_manifest(
                root=self.root,
                source_commit=source_commit,
                output_path="evidence/stage07-execution-tooling.json",
            )

    def test_source_substitution_and_manifest_tamper_fail_closed(self) -> None:
        manifest_ref = tooling_manifest.publish_execution_tooling_manifest(
            root=self.root,
            source_commit=self.source_commit,
            output_path="evidence/stage07-execution-tooling.json",
        )
        with self.assertRaisesRegex(tooling_manifest.ExecutionToolingManifestError, "source commit"):
            tooling_manifest.load_and_verify_execution_tooling_manifest(
                root=self.root,
                manifest_ref=manifest_ref,
                expected_source_commit="f" * 40,
            )
        manifest_path = self.root / str(manifest_ref["path"])
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
        value["files"][0]["sha256"] = "0" * 64
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        manifest_path.write_bytes(raw)
        tampered_ref = {
            "path": manifest_ref["path"],
            "byte_count": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        with self.assertRaisesRegex(tooling_manifest.ExecutionToolingManifestError, "aggregate"):
            tooling_manifest.load_and_verify_execution_tooling_manifest(
                root=self.root,
                manifest_ref=tampered_ref,
                expected_source_commit=self.source_commit,
            )

    def test_authorization_capture_and_finalizer_surfaces_require_manifest(self) -> None:
        matrix_schema = json.loads((ROOT / "schema" / "smoke-matrix.schema.json").read_text(encoding="utf-8"))
        matrix = matrix_schema["$defs"]["matrixAuthorization"]
        self.assertIn("execution_tooling_manifest", matrix["required"])
        self.assertEqual({"$ref": "#/$defs/artifactRef"}, matrix["properties"]["execution_tooling_manifest"])

        capture_schema = json.loads((ROOT / "schema" / "producer-capture-complete.schema.json").read_text(encoding="utf-8"))
        custody = capture_schema["$defs"]["execution_custody"]
        self.assertIn("execution_tooling_manifest", custody["required"])
        self.assertEqual({"$ref": "#/$defs/artifact_ref"}, custody["properties"]["execution_tooling_manifest"])

        finalize_parameters = inspect.signature(strict_finalizer.finalize_single_call_stage_capture).parameters
        revalidate_parameters = inspect.signature(strict_finalizer.revalidate_single_call_stage_capture).parameters
        self.assertIn("execution_tooling_manifest", finalize_parameters)
        self.assertIn("expected_execution_tooling_manifest", revalidate_parameters)

    def test_dirty_dependency_blocks_capture_finalization_before_run_root_creation(self) -> None:
        manifest_ref = tooling_manifest.publish_execution_tooling_manifest(
            root=self.root,
            source_commit=self.source_commit,
            output_path="evidence/stage07-execution-tooling.json",
        )
        dependency = self.root / "tools" / "checker_execution_snapshot.py"
        dependency.write_bytes(dependency.read_bytes() + b"\n# unauthorized post-capture drift\n")
        run_root = "evidence/finalized-case"
        with self.assertRaisesRegex(strict_finalizer.FinalizationError, "execution-tooling-manifest"):
            strict_finalizer.finalize_single_call_stage_capture(
                root=self.root,
                run_root=run_root,
                raw_envelope=b"retained raw provider output\n",
                raw_input=b"retained input\n",
                expected_envelope_nonce="1" * 32,
                expected_case_id="gate88-secularism",
                expected_cycle_id="fixture-cycle",
                expected_candidate_binding={"source_commit": self.source_commit},
                expected_input_binding={
                    "sha256": hashlib.sha256(b"retained input\n").hexdigest(),
                    "byte_count": len(b"retained input\n"),
                },
                capture_complete_record={"path": "capture.json"},
                capture_input_refs={"raw_output": {"path": "raw-output.bin"}},
                execution_tooling_manifest=manifest_ref,
            )
        self.assertFalse((self.root / run_root).exists())


if __name__ == "__main__":
    unittest.main()
