#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
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

import verify_candidate_output as candidate  # noqa: E402
from checker_execution_snapshot import create_execution_snapshot  # noqa: E402
from validation_registry import Finding, load_registry, profile_invocations, validate_verdict  # noqa: E402


SOURCE_COMMIT = "a" * 40


class CandidateHardeningTests(unittest.TestCase):
    def _verify(self, run_process, *, root: Path = ROOT):
        return candidate.verify(
            Path("tests/validation-integrity/artifacts/input.txt"),
            Path("tests/validation-integrity/artifacts/output.md"),
            profile_id="captured-output-structural",
            verdict_id="candidate-case",
            source_commit=SOURCE_COMMIT,
            root=root,
            run_process=run_process,
            timeout_seconds=1,
        )

    def _scratch_root(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity")
        root = Path(temp.name)
        (root / "schema").mkdir()
        (root / "tools").mkdir()
        (root / "tests/validation-integrity/artifacts").mkdir(parents=True)
        for relative in (
            "schema/validation-registry.schema.json",
            "schema/checker-replay-verdict.schema.json",
            "tools/validation-registry.json",
            "tests/validation-integrity/artifacts/input.txt",
            "tests/validation-integrity/artifacts/output.md",
        ):
            shutil.copy2(ROOT / relative, root / relative)
        registry = json.loads((ROOT / "tools/validation-registry.json").read_text(encoding="utf-8"))
        for row in registry["checkers"]:
            source = Path(row["source_path"])
            shutil.copy2(ROOT / source, root / source)
        for row in registry["consumers"]:
            source = Path(row["source_path"])
            if not (root / source).exists():
                shutil.copy2(ROOT / source, root / source)
        for resource in sorted({
            str(value)
            for row in registry["checkers"]
            for value in row.get("runtime_resources", [])
        }):
            source = ROOT / resource
            target = root / resource
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        return temp

    def test_canonical_verdict_runs_exact_nonempty_plan_on_private_output_snapshot(self) -> None:
        commands: list[list[str]] = []
        snapshot_paths: list[Path] = []
        original_output = ROOT / "tests/validation-integrity/artifacts/output.md"

        def accepted(command: list[str], **kwargs) -> SimpleNamespace:
            commands.append(command)
            self.assertEqual(1, kwargs["timeout"])
            snapshot = Path(command[command.index("--outputs") + 1])
            snapshot_paths.append(snapshot)
            self.assertNotEqual(original_output.resolve(), snapshot.resolve())
            self.assertEqual(original_output.read_bytes(), snapshot.read_bytes())
            return SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")

        verdict = self._verify(accepted)
        self.assertEqual("daee-checker-replay-verdict-v1", verdict["schema"])
        self.assertEqual("PASS_STRUCTURAL", verdict["aggregate_status"])
        self.assertEqual(12, len(verdict["checker_results"]))
        self.assertEqual(12, len(commands))
        self.assertEqual(
            "daee-checker-execution-snapshot-v1",
            verdict["execution_snapshot"]["schema"],
        )
        self.assertTrue(all(path == snapshot_paths[0] for path in snapshot_paths))
        self.assertFalse(snapshot_paths[0].exists())
        self.assertEqual([], validate_verdict(verdict, load_registry(), root=ROOT, verify_files=True))
        self.assertTrue(all(row["diagnostic_adapter_id"] is None for row in verdict["checker_results"]))

    def test_canonical_checker_plan_has_complete_private_runtime_resources(self) -> None:
        verdict = self._verify(subprocess.run)
        unsupported = [
            (row["checker_id"], row["exit_category"], row.get("diagnostic"))
            for row in verdict["checker_results"]
            if row["exit_category"] not in {"accepted", "structural-rejection"}
        ]
        self.assertEqual([], unsupported)
        self.assertTrue(
            all(
                "Traceback" not in str(row.get("diagnostic") or {})
                and "FileNotFoundError" not in str(row.get("diagnostic") or {})
                for row in verdict["checker_results"]
            )
        )

    def test_all_checker_sources_dependencies_and_resources_execute_private_verified_snapshots(self) -> None:
        temp = self._scratch_root()
        try:
            root = Path(temp.name)
            fixture_root = ROOT / "tests/validation-integrity/fixtures/candidate-source-custody"
            scratch_fixture_root = root / "tests/validation-integrity/fixtures/candidate-source-custody"
            scratch_fixture_root.mkdir(parents=True)
            shutil.copy2(fixture_root / "probe_resource.txt", scratch_fixture_root / "probe_resource.txt")
            shutil.copy2(fixture_root / "candidate_source_helper.py", root / "tools/candidate_source_helper.py")
            helper_path = root / "tools/candidate_source_helper.py"
            resource_path = scratch_fixture_root / "probe_resource.txt"
            probe = (fixture_root / "probe_checker.py").read_bytes()
            competitor_prefix = (fixture_root / "competitor_checker.py").read_bytes()
            self.assertLessEqual(len(competitor_prefix), len(probe))
            competitor = competitor_prefix + b"#" * (len(probe) - len(competitor_prefix))

            registry_path = root / "tools/validation-registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            plan = profile_invocations(registry, candidate.PROFILE_ID, root=root)
            expected_names = [Path(row["source_path"]).name for row in plan]
            expected_name_set = set(expected_names)
            required_ids = {str(row["checker_id"]) for row in plan}
            for checker in registry["checkers"]:
                if checker["checker_id"] not in required_ids:
                    continue
                tool = root / checker["source_path"]
                tool.write_bytes(probe)
                checker["source_sha256"] = candidate.sha256_bytes(probe)
                checker["runtime_resources"] = [
                    "tests/validation-integrity/fixtures/candidate-source-custody/probe_resource.txt"
                ]
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

            observed_names: list[str] = []
            observed_stdout: list[bytes] = []
            snapshot_paths: list[Path] = []

            def replace_execute_restore(command: list[str], **kwargs) -> subprocess.CompletedProcess[bytes]:
                snapshot = Path(command[5])
                self.assertIn(snapshot.name, expected_name_set)
                canonical = root / "tools" / snapshot.name
                observed_names.append(canonical.name)
                self.assertNotEqual(snapshot.resolve(), canonical.resolve())
                self.assertEqual(probe, snapshot.read_bytes())
                snapshot_paths.append(snapshot)
                original = canonical.read_bytes()
                original_helper = helper_path.read_bytes()
                original_resource = resource_path.read_bytes()
                self.assertEqual(probe, original)
                canonical.write_bytes(competitor)
                helper_path.write_text('VALUE = "live-helper-competitor"\n', encoding="utf-8")
                resource_path.write_text("live-resource-competitor\n", encoding="utf-8")
                try:
                    completed = subprocess.run(command, **kwargs)
                finally:
                    canonical.write_bytes(original)
                    helper_path.write_bytes(original_helper)
                    resource_path.write_bytes(original_resource)
                observed_stdout.append(completed.stdout)
                return completed

            verdict = self._verify(replace_execute_restore, root=root)
            self.assertEqual(expected_names, observed_names)
            self.assertEqual(
                [b"custody-source:helper-ok:resource-ok"] * 12,
                [value.strip() for value in observed_stdout],
            )
            self.assertEqual(12, len(snapshot_paths))
            self.assertTrue(all(path.name == name for path, name in zip(snapshot_paths, expected_names)))
            self.assertTrue(all(not path.exists() for path in snapshot_paths))
            self.assertEqual("PASS_STRUCTURAL", verdict["aggregate_status"])
            self.assertEqual(required_ids, {row["checker_id"] for row in verdict["checker_results"]})
            self.assertTrue(
                all((root / row["tool_path"]).read_bytes() == probe for row in verdict["checker_results"])
            )
        finally:
            temp.cleanup()

    def test_execution_snapshot_manifest_fails_closed_under_identity_mutations(self) -> None:
        verdict = self._verify(
            lambda *_args, **_kwargs: SimpleNamespace(
                returncode=0,
                stdout=b"accepted\n",
                stderr=b"",
            )
        )
        registry = load_registry()

        cases: list[tuple[str, str, object]] = []
        missing = copy.deepcopy(verdict)
        del missing["execution_snapshot"]
        cases.append(("missing", "execution_snapshot_missing", missing))

        count = copy.deepcopy(verdict)
        count["execution_snapshot"]["file_count"] += 1
        cases.append(("count", "execution_snapshot_count_mismatch", count))

        reordered = copy.deepcopy(verdict)
        reordered["execution_snapshot"]["files"].reverse()
        reordered["execution_snapshot"]["sha256"] = candidate.canonical_sha256(
            reordered["execution_snapshot"]["files"]
        )
        cases.append(("order", "execution_snapshot_order_mismatch", reordered))

        incomplete = copy.deepcopy(verdict)
        incomplete["execution_snapshot"]["files"].pop()
        incomplete["execution_snapshot"]["file_count"] -= 1
        incomplete["execution_snapshot"]["sha256"] = candidate.canonical_sha256(
            incomplete["execution_snapshot"]["files"]
        )
        cases.append(("incomplete", "execution_snapshot_incomplete", incomplete))

        file_drift = copy.deepcopy(verdict)
        file_drift["execution_snapshot"]["files"][0]["sha256"] = "0" * 64
        file_drift["execution_snapshot"]["sha256"] = candidate.canonical_sha256(
            file_drift["execution_snapshot"]["files"]
        )
        cases.append(("file-drift", "execution_snapshot_file_drift", file_drift))

        unbound = copy.deepcopy(verdict)
        unbound["checker_results"][0]["tool_sha256"] = "0" * 64
        cases.append(("checker-unbound", "execution_snapshot_checker_unbound", unbound))

        for case_id, expected, mutated in cases:
            with self.subTest(case_id=case_id):
                findings = validate_verdict(mutated, registry, root=ROOT, verify_files=True)
                self.assertEqual(expected, findings[0].failure_class, findings)

    def test_execution_snapshot_rejects_destination_escape_and_resource_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "schema").mkdir()
            output = root / "output.md"
            output.write_text("output\n", encoding="utf-8")
            outside = root.parent / f"{root.name}-outside-snapshot"
            with self.assertRaisesRegex(ValueError, "destination must remain"):
                create_execution_snapshot(
                    root=root,
                    destination=outside,
                    plan=[],
                    output_path=output,
                )

            target = root / "resource.txt"
            target.write_text("resource\n", encoding="utf-8")
            link = root / "resource-link.txt"
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "rejects symlink source"):
                create_execution_snapshot(
                    root=root,
                    destination=root / "snapshot",
                    plan=[{"runtime_resources": ["resource-link.txt"]}],
                    output_path=output,
                )

    def test_child_rejects_private_source_snapshot_swap_before_execution(self) -> None:
        competitor = (
            ROOT
            / "tests/validation-integrity/fixtures/candidate-source-custody/competitor_checker.py"
        ).read_bytes()
        calls = 0

        def swap_private_snapshot(command: list[str], **kwargs):
            nonlocal calls
            calls += 1
            if calls != 1:
                return SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")
            snapshot = Path(command[5])
            original = snapshot.read_bytes()
            snapshot.chmod(0o600)
            snapshot.write_bytes(competitor)
            try:
                completed = subprocess.run(command, **kwargs)
            finally:
                snapshot.write_bytes(original)
                snapshot.chmod(0o444)
            self.assertEqual(86, completed.returncode)
            self.assertNotIn(b"canonical-path-competitor", completed.stdout)
            return completed

        verdict = self._verify(swap_private_snapshot)
        self.assertEqual(12, calls)
        self.assertEqual(12, len(verdict["checker_results"]))
        self.assertEqual("crash", verdict["checker_results"][0]["exit_category"])
        self.assertEqual("INFRASTRUCTURE_ERROR", verdict["aggregate_status"])

    def test_candidate_independently_rejects_empty_or_non_exact_plan(self) -> None:
        with patch.object(candidate, "profile_invocations", return_value=[]):
            with self.assertRaisesRegex(ValueError, "exact non-empty checker plan"):
                self._verify(lambda *_args, **_kwargs: None)

        duplicate = [
            {
                "result_key": "duplicate",
                "invocation_kind": "checker",
                "checker_id": "act-surface-syntax",
                "source_path": "tools/check_act_surface_syntax.py",
                "source_sha256": load_registry()["checkers"][0]["source_sha256"],
                "arguments": ["--outputs", "{output}"],
            }
        ] * 2
        with patch.object(candidate, "profile_invocations", return_value=duplicate):
            with self.assertRaisesRegex(ValueError, "exact non-empty checker plan"):
                self._verify(lambda *_args, **_kwargs: None)

        reordered = list(reversed(profile_invocations(load_registry(), "captured-output-structural")))
        with patch.object(candidate, "profile_invocations", return_value=reordered):
            with self.assertRaisesRegex(ValueError, "exact non-empty checker plan"):
                self._verify(lambda *_args, **_kwargs: None)

    def test_structural_and_infrastructure_outcomes_are_canonical_and_roundtrip(self) -> None:
        cases = {
            "structural": (lambda: SimpleNamespace(returncode=1, stdout=b"act surface syntax check: FAIL\n", stderr=b""), "structural-rejection", "FAIL_STRUCTURAL"),
            "traceback": (lambda: SimpleNamespace(returncode=1, stdout=b"", stderr=b"Traceback (most recent call last):\nboom"), "malformed-diagnostic", "INFRASTRUCTURE_ERROR"),
            "empty-exit-one": (lambda: SimpleNamespace(returncode=1, stdout=b"", stderr=b""), "malformed-diagnostic", "INFRASTRUCTURE_ERROR"),
            "usage-exit-one": (lambda: SimpleNamespace(returncode=1, stdout=b"usage: checker\n", stderr=b""), "malformed-diagnostic", "INFRASTRUCTURE_ERROR"),
            "fatal-exit-one": (lambda: SimpleNamespace(returncode=1, stdout=b"fatal internal error\n", stderr=b""), "malformed-diagnostic", "INFRASTRUCTURE_ERROR"),
            "usage": (lambda: SimpleNamespace(returncode=2, stdout=b"usage: checker", stderr=b""), "usage-error", "INFRASTRUCTURE_ERROR"),
            "signal": (lambda: SimpleNamespace(returncode=-11, stdout=b"", stderr=b""), "crash", "INFRASTRUCTURE_ERROR"),
            "timeout": (lambda: (_ for _ in ()).throw(subprocess.TimeoutExpired(["checker"], 1)), "timeout", "INFRASTRUCTURE_ERROR"),
            "unavailable": (lambda: (_ for _ in ()).throw(OSError("missing checker")), "unavailable", "INFRASTRUCTURE_ERROR"),
        }
        for label, (first_result, expected_category, expected_aggregate) in cases.items():
            with self.subTest(label=label):
                calls = 0

                def run(_command: list[str], **_kwargs) -> SimpleNamespace:
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        return first_result()
                    return SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")

                verdict = self._verify(run)
                self.assertEqual(expected_category, verdict["checker_results"][0]["exit_category"])
                self.assertEqual(expected_aggregate, verdict["aggregate_status"])
                self.assertEqual([], validate_verdict(verdict, load_registry(), root=ROOT, verify_files=True))

    def test_aggregate_precedence_is_directional_and_retains_all_results(self) -> None:
        cases = {
            "structural-then-infrastructure": (
                ["structural", "timeout"],
                "FAIL_STRUCTURAL",
            ),
            "infrastructure-then-structural": (
                ["timeout", "structural"],
                "INFRASTRUCTURE_ERROR",
            ),
        }
        markers = {
            "check_act_surface_syntax.py": b"act surface syntax check: FAIL\n",
            "check_concealment_mode.py": b"concealment-mode check: FAIL\n",
        }
        for label, (sequence, expected) in cases.items():
            with self.subTest(label=label):
                outcomes = iter([*sequence, *(["accepted"] * 10)])

                def run(command: list[str], **_kwargs) -> SimpleNamespace:
                    outcome = next(outcomes)
                    if outcome == "timeout":
                        raise subprocess.TimeoutExpired(command, 1)
                    if outcome == "structural":
                        return SimpleNamespace(
                            returncode=1,
                            stdout=markers[Path(command[6]).name],
                            stderr=b"",
                        )
                    return SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")

                verdict = self._verify(run)
                self.assertEqual(expected, verdict["aggregate_status"])
                self.assertEqual(12, len(verdict["checker_results"]))
                self.assertEqual([], validate_verdict(verdict, load_registry(), root=ROOT, verify_files=True))

    def test_structural_verdict_requires_checker_owned_marker_in_bound_diagnostic(self) -> None:
        calls = 0

        def run(_command: list[str], **_kwargs) -> SimpleNamespace:
            nonlocal calls
            calls += 1
            if calls == 1:
                return SimpleNamespace(
                    returncode=1,
                    stdout=b"detail\nact surface syntax check: FAIL\n",
                    stderr=b"",
                )
            return SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")

        verdict = self._verify(run)
        self.assertEqual("act surface syntax check: FAIL", verdict["checker_results"][0]["diagnostic"]["message"])
        forged = copy.deepcopy(verdict)
        forged["checker_results"][0]["diagnostic"]["message"] = "arbitrary fatal exit"
        findings = validate_verdict(forged, load_registry(), root=ROOT, verify_files=True)
        self.assertTrue(any(finding.failure_class == "malformed_diagnostic" for finding in findings))

    def test_wrong_reason_rejection_does_not_shield_later_infrastructure(self) -> None:
        outcomes = iter(["structural", "timeout", *("accepted" for _ in range(10))])

        def run(command: list[str], **_kwargs) -> SimpleNamespace:
            outcome = next(outcomes)
            if outcome == "structural":
                return SimpleNamespace(
                    returncode=1,
                    stdout=b"act surface syntax check: FAIL\n",
                    stderr=b"",
                )
            if outcome == "timeout":
                raise subprocess.TimeoutExpired(command, 1)
            return SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")

        verdict = self._verify(run)
        verdict["checker_results"][0]["expectation_status"] = "REJECTED_WRONG_REASON"
        verdict["aggregate_status"] = "INFRASTRUCTURE_ERROR"
        self.assertEqual([], validate_verdict(verdict, load_registry(), root=ROOT, verify_files=True))

    def test_candidate_profile_rejects_extra_registered_checker_result(self) -> None:
        verdict = self._verify(
            lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")
        )
        registry = load_registry()
        extra_checker = next(row for row in registry["checkers"] if row["checker_id"] == "shannon-finite-fold")
        extra = copy.deepcopy(verdict["checker_results"][0])
        extra.update(
            checker_id=extra_checker["checker_id"],
            tool_path=extra_checker["source_path"],
            tool_sha256=extra_checker["source_sha256"],
        )
        verdict["checker_results"].append(extra)
        findings = validate_verdict(verdict, registry, root=ROOT, verify_files=True)
        self.assertTrue(findings)
        self.assertEqual("profile_result_not_exact", findings[0].failure_class)

    def test_original_output_registry_and_tool_mutations_fail_closed(self) -> None:
        for target_kind in ("output", "registry", "tool"):
            with self.subTest(target_kind=target_kind):
                temp = self._scratch_root()
                try:
                    root = Path(temp.name)
                    calls = 0

                    def mutate(_command: list[str], **_kwargs) -> SimpleNamespace:
                        nonlocal calls
                        calls += 1
                        if calls == 1:
                            if target_kind == "output":
                                target = root / "tests/validation-integrity/artifacts/output.md"
                            elif target_kind == "registry":
                                target = root / "tools/validation-registry.json"
                            else:
                                target = root / "tools/check_act_surface_syntax.py"
                            target.write_bytes(target.read_bytes() + b"\n")
                        return SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")

                    with self.assertRaisesRegex(ValueError, "changed during candidate verification"):
                        self._verify(mutate, root=root)
                finally:
                    temp.cleanup()

    def test_outside_repo_paths_and_publication_collisions_or_faults_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / "output.md"
            path.write_text("outside", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "repository"):
                candidate.verify(
                    Path("tests/validation-integrity/artifacts/input.txt"),
                    path,
                    profile_id="captured-output-structural",
                    verdict_id="outside",
                    source_commit=SOURCE_COMMIT,
                    root=ROOT,
                    run_process=lambda *_args, **_kwargs: None,
                )

        verdict = self._verify(
            lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")
        )
        with self.assertRaisesRegex(ValueError, "collides with protected evidence"):
            candidate.publish_verdict(
                verdict,
                Path("tests/validation-integrity/artifacts/output.md"),
                root=ROOT,
            )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            target = Path(temp) / "verdict.json"
            with self.assertRaisesRegex(ValueError, "injected publication failure"):
                candidate.publish_verdict(verdict, target.relative_to(ROOT), root=ROOT, fault_at="after-stage-write")
            self.assertFalse(target.exists())
            candidate.publish_verdict(verdict, target.relative_to(ROOT), root=ROOT)
            before = target.read_bytes()
            with self.assertRaisesRegex(ValueError, "already exists"):
                candidate.publish_verdict(verdict, target.relative_to(ROOT), root=ROOT)
            self.assertEqual(before, target.read_bytes())

    def test_wrapper_cleanup_never_deletes_swapped_file_competitor(self) -> None:
        verdict = self._verify(
            lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            target = Path(temp) / "verdict.json"
            competitor = b"competitor-owned\n"
            calls = 0

            def validate_then_swap(*_args, **_kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    target.unlink()
                    target.write_bytes(competitor)
                    return [Finding("evidence_drift", "swapped", "competitor")]
                return []

            with patch.object(candidate, "validate_verdict", side_effect=validate_then_swap):
                with self.assertRaisesRegex(ValueError, "changed during publication"):
                    candidate.publish_verdict(verdict, target.relative_to(ROOT), root=ROOT)
            self.assertEqual(competitor, target.read_bytes())


if __name__ == "__main__":
    unittest.main()
