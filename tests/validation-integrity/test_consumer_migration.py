#!/usr/bin/env python3
from __future__ import annotations

import ast
import copy
import hashlib
import json
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
import run_local_ci as local_ci  # noqa: E402
import run_staged_current_skill_smoke as staged_smoke  # noqa: E402
import verify_candidate_output as candidate  # noqa: E402
from smoke_matrix_registry import load_registry as load_case_registry  # noqa: E402
from validation_registry import (  # noqa: E402
    MAX_STATIC_FORMATTED_FRAGMENT_CHARS,
    _format_static_string,
    _source_has_private_policy,
    _source_uses_profile_projection,
    _string_concatenation_fragments,
    discover_validation_consumers,
    load_registry,
    profile_invocations,
    registry_hash,
    sha256_file,
    validate_registry,
)


class ValidationConsumerMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry()

    def test_stage07_plan_is_registry_ordered_with_exact_arguments_and_two_adapters(self) -> None:
        expected = [
            ("visible_opening_header", "in-process-adapter", None, "visible-governed-output", ()),
            ("nla_semantic_faithfulness", "checker", "nla-decode-semantic-faithfulness", None, ("--outputs", "{output}")),
            ("field_witness_convergence", "checker", "field-witness-convergence", None, ("--outputs", "{output}")),
            ("formal_reread_state_semantics", "checker", "formal-reread-state-semantics", None, ("--outputs", "{output}")),
            ("mid_reread_pressure", "checker", "mid-reread-pressure", None, ("--outputs", "{output}")),
            ("mrp_record_surface_parity", "in-process-adapter", None, "mrp-record-surface-parity", ()),
            ("mrp_route_invariants", "checker", "mrp-route-invariants", None, ("--outputs", "{output}")),
            ("mrp_generated_burden", "checker", "mrp-generated-burden", None, ("--outputs", "{output}", "--show-advisories")),
            ("graph_completeness_json", "checker", "graph-completeness", None, ("--outputs", "{output}", "--json")),
            ("manual_smoke_render_contract", "checker", "manual-smoke-render-contract", None, ("--outputs", "{output}")),
            ("public_burden_grouping", "checker", "public-burden-grouping", None, ("--outputs", "{output}")),
            ("owner_activation_ordering", "checker", "owner-activation-ordering", None, ("--require-plan", "--outputs", "{output}")),
            ("act_surface_syntax", "checker", "act-surface-syntax", None, ("--outputs", "{output}")),
        ]
        projected = profile_invocations(self.registry, "stage07-release")
        actual = [
            (
                row["result_key"],
                row["invocation_kind"],
                row.get("checker_id"),
                row.get("adapter_id"),
                tuple(row["arguments"]),
            )
            for row in projected
        ]
        self.assertEqual(expected, actual)

        output = ROOT / "tests/validation-integrity/artifacts/output.md"
        plan = staged_smoke.stage07_release_invocation_plan(ROOT, output)
        self.assertEqual([row[0] for row in expected], [row["result_key"] for row in plan])
        self.assertEqual(2, sum(row["invocation_kind"] == "in-process-adapter" for row in plan))
        self.assertEqual(
            ["--require-plan", "--outputs", str(output)],
            plan[-2]["arguments"],
        )
        required_output = {
            row["checker_id"]
            for row in self.registry["checkers"]
            if row["requirement_status"] == "required" and "output-md" in row["artifact_applicability"]
        }
        self.assertTrue(required_output.issubset({row.get("checker_id") for row in projected}))

    def test_consumer_bound_executable_profiles_fail_closed_on_non_exact_invocations(self) -> None:
        captured = next(
            profile
            for profile in self.registry["profiles"]
            if profile["profile_id"] == "captured-output-structural"
        )
        mutations = {
            "empty": lambda profile: profile.update(invocations=[]),
            "missing": lambda profile: profile["invocations"].pop(),
            "duplicate": lambda profile: profile["invocations"].append(copy.deepcopy(profile["invocations"][0])),
            "unrequired": lambda profile: profile["invocations"].append(
                {
                    "result_key": "retained_advisory",
                    "invocation_kind": "checker",
                    "checker_id": "retained-corpus-advisory",
                    "adapter_id": None,
                    "arguments": ["--outputs", "{output}"],
                }
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                registry = copy.deepcopy(self.registry)
                profile = next(
                    row for row in registry["profiles"]
                    if row["profile_id"] == "captured-output-structural"
                )
                mutate(profile)
                findings = validate_registry(registry, root=ROOT, scan_repo=False)
                self.assertTrue(findings, label)
                with self.assertRaisesRegex(ValueError, "validation registry rejected"):
                    profile_invocations(registry, "captured-output-structural", root=ROOT)

        registry = copy.deepcopy(self.registry)
        profile = next(
            row for row in registry["profiles"]
            if row["profile_id"] == "captured-output-structural"
        )
        checker = next(row for row in registry["checkers"] if row["checker_id"] == "act-surface-syntax")
        checker["artifact_applicability"] = ["retained-case-manifest"]
        findings = validate_registry(registry, root=ROOT, scan_repo=False)
        self.assertTrue(any(finding.failure_class == "profile_invocation_inapplicable" for finding in findings))
        with self.assertRaisesRegex(ValueError, "validation registry rejected"):
            profile_invocations(registry, "captured-output-structural", root=ROOT)

        self.assertGreater(len(captured["invocations"]), 0)

        registry = copy.deepcopy(self.registry)
        consumer = next(
            row for row in registry["consumers"]
            if row["consumer_id"] == "stage07-release-runner"
        )
        consumer["policy_source"] = "legacy-private-list"
        profile = next(row for row in registry["profiles"] if row["profile_id"] == "stage07-release")
        profile["invocations"] = []
        self.assertTrue(validate_registry(registry, root=ROOT, scan_repo=False))
        with self.assertRaisesRegex(ValueError, "validation registry rejected"):
            profile_invocations(registry, "stage07-release", root=ROOT)

        registry = copy.deepcopy(self.registry)
        duplicate_adapter = copy.deepcopy(registry["diagnostic_adapters"][0])
        duplicate_adapter["adapter_id"] = "duplicate-coverage-probe"
        registry["diagnostic_adapters"].append(duplicate_adapter)
        findings = validate_registry(registry, root=ROOT, scan_repo=False)
        self.assertTrue(any(finding.failure_class == "duplicate_diagnostic_adapter_coverage" for finding in findings))

        registry = copy.deepcopy(self.registry)
        registry["diagnostic_adapters"][0]["required_markers"].append("ambiguous second marker")
        self.assertTrue(validate_registry(registry, root=ROOT, scan_repo=False))

    def test_captured_output_profile_covers_every_required_output_checker_with_exact_argv(self) -> None:
        expected = {
            "act-surface-syntax": ("--outputs", "{output}"),
            "concealment-mode": ("--outputs", "{output}"),
            "field-witness-convergence": ("--outputs", "{output}"),
            "formal-reread-state-semantics": ("--outputs", "{output}"),
            "graph-completeness": ("--outputs", "{output}", "--json"),
            "manual-smoke-render-contract": ("--outputs", "{output}"),
            "mid-reread-pressure": ("--outputs", "{output}"),
            "mrp-generated-burden": ("--outputs", "{output}", "--show-advisories"),
            "mrp-route-invariants": ("--outputs", "{output}"),
            "nla-decode-semantic-faithfulness": ("--outputs", "{output}"),
            "owner-activation-ordering": ("--require-plan", "--outputs", "{output}"),
            "public-burden-grouping": ("--outputs", "{output}"),
        }
        plan = profile_invocations(self.registry, "captured-output-structural", root=ROOT)
        self.assertEqual(expected, {row["checker_id"]: tuple(row["arguments"]) for row in plan})
        required_output = {
            row["checker_id"]
            for row in self.registry["checkers"]
            if row["requirement_status"] == "required" and "output-md" in row["artifact_applicability"]
        }
        self.assertTrue(required_output.issubset(expected))

    def test_consumers_have_unique_sources_and_positive_profile_bound_projection(self) -> None:
        self.assertEqual([], validate_registry(self.registry, root=ROOT, scan_repo=False))
        for consumer_id in (
            "stage07-release-runner",
            "candidate-output-verifier",
            "model-compliance-scorecard",
        ):
            for scan_repo in (False, True):
                with self.subTest(consumer_id=consumer_id, scan_repo=scan_repo):
                    registry = copy.deepcopy(self.registry)
                    consumer = next(
                        row for row in registry["consumers"]
                        if row["consumer_id"] == consumer_id
                    )
                    consumer["source_path"] = "tools/contract_validation.py"
                    consumer["source_sha256"] = sha256_file(ROOT / consumer["source_path"])
                    findings = validate_registry(registry, root=ROOT, scan_repo=scan_repo)
                    self.assertTrue(
                        any(
                            finding.failure_class == "consumer_set_mismatch"
                            for finding in findings
                        ),
                        findings,
                    )
                    self.assertFalse(
                        _source_uses_profile_projection(
                            ROOT / "tools/contract_validation.py",
                            str(consumer["profile_id"]),
                        )
                    )

        registry = copy.deepcopy(self.registry)
        candidate_consumer = next(
            row for row in registry["consumers"]
            if row["consumer_id"] == "candidate-output-verifier"
        )
        candidate_consumer["source_path"] = "tools/build_model_compliance_scorecard.py"
        candidate_consumer["source_sha256"] = sha256_file(ROOT / candidate_consumer["source_path"])
        findings = validate_registry(registry, root=ROOT, scan_repo=False)
        self.assertTrue(
            any(finding.failure_class == "consumer_set_mismatch" for finding in findings)
        )
        self.assertFalse(
            _source_uses_profile_projection(
                ROOT / "tools/build_model_compliance_scorecard.py",
                "captured-output-structural",
            )
        )

        registry = copy.deepcopy(self.registry)
        registry["consumers"][1]["source_path"] = registry["consumers"][0]["source_path"]
        registry["consumers"][1]["source_sha256"] = registry["consumers"][0]["source_sha256"]
        findings = validate_registry(registry, root=ROOT, scan_repo=False)
        self.assertTrue(any(finding.failure_class == "consumer_set_mismatch" for finding in findings))

    def test_registry_requires_exact_three_consumer_tuples_and_source_hashes(self) -> None:
        expected = {
            "stage07-release-runner": (
                "tools/run_staged_current_skill_smoke.py",
                "stage07-release",
            ),
            "candidate-output-verifier": (
                "tools/verify_candidate_output.py",
                "captured-output-structural",
            ),
            "model-compliance-scorecard": (
                "tools/build_model_compliance_scorecard.py",
                "scorecard",
            ),
        }
        self.assertEqual(expected, {
            row["consumer_id"]: (row["source_path"], row["profile_id"])
            for row in self.registry["consumers"]
        })
        for row in self.registry["consumers"]:
            self.assertEqual(
                sha256_file(ROOT / row["source_path"]),
                row.get("source_sha256"),
                row["consumer_id"],
            )

        for consumer_id in expected:
            with self.subTest(consumer_id=consumer_id):
                registry = copy.deepcopy(self.registry)
                registry["consumers"] = [
                    row for row in registry["consumers"]
                    if row["consumer_id"] != consumer_id
                ]
                for scan_repo in (False, True):
                    findings = validate_registry(registry, root=ROOT, scan_repo=scan_repo)
                    self.assertTrue(
                        any(
                            finding.failure_class == "consumer_set_mismatch"
                            for finding in findings
                        ),
                        findings,
                    )

        registry = copy.deepcopy(self.registry)
        registry["consumers"].append({
            "consumer_id": "extra-validation-consumer",
            "source_path": "tools/contract_validation.py",
            "source_sha256": sha256_file(ROOT / "tools/contract_validation.py"),
            "profile_id": "advisory",
            "policy_source": "registry",
        })
        findings = validate_registry(registry, root=ROOT, scan_repo=False)
        self.assertTrue(
            any(finding.failure_class == "consumer_set_mismatch" for finding in findings),
            findings,
        )

    def test_stage07_executes_checker_and_output_from_one_private_snapshot(self) -> None:
        output = ROOT / "tests/validation-integrity/artifacts/output.md"
        source = ROOT / "tools/check_act_surface_syntax.py"
        plan = [{
            "result_key": "act_surface_syntax",
            "invocation_kind": "checker",
            "checker_id": "act-surface-syntax",
            "adapter_id": None,
            "source_path": "tools/check_act_surface_syntax.py",
            "source_sha256": sha256_file(source),
            "runtime_resources": [],
            "arguments": ["--outputs", str(output)],
        }]
        policy = {
            "selected_profile": "stage07-release",
            "registry_path": "tools/validation-registry.json",
            "registry_sha256": "a" * 64,
            "result_order": ["act_surface_syntax"],
        }
        observed: list[list[str]] = []

        def capture(command: list[str], *, cwd: Path, input_text=None) -> str:
            observed.append(command)
            self.assertEqual(["-I", "-B", "-c"], command[1:4])
            private_source = Path(command[5])
            self.assertNotEqual(source.resolve(), private_source.resolve())
            frozen_output = Path(command[command.index("--outputs") + 1])
            self.assertNotEqual(output.resolve(), frozen_output.resolve())
            self.assertEqual(output.read_bytes(), frozen_output.read_bytes())
            self.assertNotEqual(ROOT.resolve(), cwd.resolve())
            original = private_source.read_bytes()
            private_source.chmod(0o600)
            private_source.write_bytes(original + b"\n# staged competitor\n")
            try:
                rejected = subprocess.run(
                    command,
                    cwd=cwd,
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
            finally:
                private_source.write_bytes(original)
                private_source.chmod(0o444)
            self.assertEqual(86, rejected.returncode)
            return ""

        with patch.object(staged_smoke, "_stage07_release_projection", return_value=(plan, policy)):
            with patch.object(staged_smoke, "require_command_success", side_effect=capture):
                results, actual_policy = staged_smoke.run_release_validators_with_policy(
                    ROOT,
                    output,
                    [],
                )

        self.assertEqual({"act_surface_syntax": "pass"}, results)
        self.assertEqual(1, len(observed))
        snapshot = actual_policy.get("execution_snapshot")
        self.assertIsInstance(snapshot, dict)
        self.assertRegex(str(snapshot.get("sha256")), r"^[0-9a-f]{64}$")
        self.assertGreater(int(snapshot.get("file_count", 0)), 1)

    def test_stage07_canonical_checker_executes_with_private_skill_resources(self) -> None:
        output = ROOT / "tests/validation-integrity/artifacts/output.md"
        plan = [
            row
            for row in profile_invocations(
                self.registry,
                "stage07-release",
                bindings={"output": str(output)},
                root=ROOT,
            )
            if row.get("checker_id") == "manual-smoke-render-contract"
        ]
        self.assertEqual(1, len(plan))
        policy = {
            "selected_profile": "stage07-release",
            "registry_path": "tools/validation-registry.json",
            "registry_sha256": registry_hash(),
            "result_order": [plan[0]["result_key"]],
        }
        observed: list[subprocess.CompletedProcess[bytes]] = []

        def execute_private(command: list[str], *, cwd: Path, input_text=None) -> str:
            completed = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                timeout=10,
                check=False,
            )
            observed.append(completed)
            self.assertIn(completed.returncode, {0, 1})
            self.assertNotIn(b"FileNotFoundError", completed.stderr)
            self.assertNotIn(b"Traceback", completed.stderr)
            return completed.stdout.decode("utf-8", errors="replace")

        with patch.object(staged_smoke, "_stage07_release_projection", return_value=(plan, policy)):
            with patch.object(staged_smoke, "require_command_success", side_effect=execute_private):
                results, actual_policy = staged_smoke.run_release_validators_with_policy(
                    ROOT,
                    output,
                    [],
                )
        self.assertEqual({plan[0]["result_key"]: "pass"}, results)
        self.assertEqual(1, len(observed))
        snapshot_paths = {
            row["path"] for row in actual_policy["execution_snapshot"]["files"]
        }
        self.assertIn(
            "atomics/skill/references/diagnostics/delta-result-vocabulary.json",
            snapshot_paths,
        )

    def test_stage07_dispatch_stops_at_first_failure(self) -> None:
        plan = [
            {"result_key": "adapter-a", "invocation_kind": "in-process-adapter"},
            {"result_key": "checker-a", "invocation_kind": "checker"},
            {"result_key": "checker-b", "invocation_kind": "checker"},
        ]
        observed: list[str] = []

        def run_adapter(row: dict) -> None:
            observed.append(row["result_key"])

        def run_checker(row: dict) -> None:
            observed.append(row["result_key"])
            raise staged_smoke.HarnessError("expected first failure")

        with self.assertRaisesRegex(staged_smoke.HarnessError, "expected first failure"):
            staged_smoke.execute_release_invocation_plan(
                plan,
                run_adapter=run_adapter,
                run_checker=run_checker,
            )
        self.assertEqual(["adapter-a", "checker-a"], observed)

    def test_stage07_and_retained_stage08_policy_identity_is_exact_and_order_bound(self) -> None:
        policy = staged_smoke.stage07_release_validation_policy(ROOT)
        expected_order = list(staged_smoke.stage07_release_validation_order(ROOT))
        self.assertEqual(
            {
                "selected_profile": "stage07-release",
                "registry_path": "tools/validation-registry.json",
                "registry_sha256": registry_hash(),
                "result_order": expected_order,
            },
            policy,
        )
        results = {key: "pass" for key in expected_order}
        self.assertEqual(
            [],
            staged_smoke.staged_handshake_check.release_validation_policy_errors(
                "probe", policy, results
            ),
        )
        for field, value in (
            ("selected_profile", "captured-output-structural"),
            ("registry_path", "tools/other.json"),
            ("registry_sha256", "0" * 64),
            ("result_order", list(reversed(expected_order))),
        ):
            with self.subTest(field=field):
                drifted = copy.deepcopy(policy)
                drifted[field] = value
                self.assertTrue(
                    staged_smoke.staged_handshake_check.release_validation_policy_errors(
                        "probe", drifted, results
                    )
                )

    def test_candidate_verification_is_registry_derived_structured_and_hash_bound(self) -> None:
        input_path = ROOT / "tests/validation-integrity/artifacts/input.txt"
        output = ROOT / "tests/validation-integrity/artifacts/output.md"
        observed: list[list[str]] = []

        def fake_run(command: list[str], **_kwargs) -> SimpleNamespace:
            observed.append(command)
            return SimpleNamespace(returncode=0, stdout=b"accepted\n", stderr=b"")

        verdict = candidate.verify(
            Path("tests/validation-integrity/artifacts/input.txt"),
            Path("tests/validation-integrity/artifacts/output.md"),
            profile_id="captured-output-structural",
            verdict_id="consumer-migration",
            source_commit="a" * 40,
            root=ROOT,
            run_process=fake_run,
        )
        expected_plan = profile_invocations(
            self.registry,
            "captured-output-structural",
            bindings={"output": str(output)},
        )
        self.assertEqual("daee-checker-replay-verdict-v1", verdict["schema"])
        self.assertEqual("captured-output-structural", verdict["selected_profile"])
        self.assertEqual(registry_hash(), verdict["registry_sha256"])
        artifacts = {row["role"]: row for row in verdict["artifacts"]}
        self.assertEqual(sha256_file(input_path), artifacts["input"]["sha256"])
        self.assertEqual(sha256_file(output), artifacts["output"]["sha256"])
        self.assertEqual("PASS_STRUCTURAL", verdict["aggregate_status"])
        self.assertEqual(len(expected_plan), len(verdict["checker_results"]))
        private_sources = [Path(command[5]) for command in observed]
        self.assertEqual(
            [Path(row["source_path"]).name for row in expected_plan],
            [path.name for path in private_sources],
        )
        self.assertTrue(all(command[5] == command[6] for command in observed))
        self.assertTrue(
            all(
                path.resolve() != (ROOT / row["source_path"]).resolve()
                for path, row in zip(private_sources, expected_plan, strict=True)
            )
        )
        self.assertTrue(all(not path.exists() for path in private_sources))
        for expected, result in zip(expected_plan, verdict["checker_results"], strict=True):
            self.assertEqual(expected["checker_id"], result["checker_id"])
            self.assertEqual(expected["source_path"], result["tool_path"])
            self.assertEqual(expected["source_sha256"], result["tool_sha256"])
            self.assertEqual(artifacts["output"]["sha256"], result["artifact_sha256"])
            self.assertEqual(hashlib.sha256(b"accepted\n").hexdigest(), result["stdout_sha256"])

    def test_candidate_verification_preserves_structural_and_infrastructure_outcomes(self) -> None:
        output = ROOT / "tests/validation-integrity/artifacts/output.md"
        exit_codes = iter([0, 1, 2, *([0] * 9)])

        def fake_run(_command: list[str], **_kwargs) -> SimpleNamespace:
            returncode = next(exit_codes)
            return SimpleNamespace(
                returncode=returncode,
                stdout=b"concealment-mode check: FAIL\n" if returncode == 1 else b"",
                stderr=b"",
            )

        verdict = candidate.verify(
            Path("tests/validation-integrity/artifacts/input.txt"),
            Path("tests/validation-integrity/artifacts/output.md"),
            profile_id="captured-output-structural",
            verdict_id="consumer-outcomes",
            source_commit="a" * 40,
            root=ROOT,
            run_process=fake_run,
        )
        self.assertEqual("FAIL_STRUCTURAL", verdict["aggregate_status"])
        self.assertEqual("structural-rejection", verdict["checker_results"][1]["exit_category"])
        self.assertEqual("completed", verdict["checker_results"][1]["execution_status"])
        self.assertEqual("usage-error", verdict["checker_results"][2]["exit_category"])
        self.assertEqual("completed", verdict["checker_results"][2]["execution_status"])

    def test_scorecard_v2_projects_existing_replay_without_detector_execution(self) -> None:
        template = Path("tests/validation-integrity/valid/right-reason-stage04.verdict.json")
        with self.assertRaisesRegex(ValueError, "case manifest"):
            scorecard.build_scorecard(template, host="fixture", root=ROOT)
        authority_cases = load_case_registry()["cases"]
        case_ids = [row["case_id"] for row in authority_cases]
        verdicts = [
            candidate.verify(
                Path(case["input_path"]),
                Path("tests/validation-integrity/artifacts/output.md"),
                profile_id="captured-output-structural",
                verdict_id=str(case["case_id"]),
                source_commit="a" * 40,
                root=ROOT,
                run_process=lambda *_args, **_kwargs: SimpleNamespace(
                    returncode=0, stdout=b"accepted\n", stderr=b""
                ),
            )
            for case in authority_cases
        ]
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            directory = Path(temp)
            cases = []
            replay_paths = []
            for verdict in verdicts:
                replay = directory / f"{verdict['verdict_id']}.json"
                replay.write_text(json.dumps(verdict), encoding="utf-8")
                replay_paths.append(replay)
                cases.append(
                    {
                        "case_id": verdict["verdict_id"],
                        "source_verdict_path": replay.relative_to(ROOT).as_posix(),
                    }
                )
            manifest = Path(temp) / "case-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "daee-scorecard-case-manifest-v1",
                        "cohort_id": "fixture-cohort",
                        "source_commit": "a" * 40,
                        "source_profile": "captured-output-structural",
                        "registry_path": "tools/validation-registry.json",
                        "registry_sha256": registry_hash(),
                        "cases": cases,
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(subprocess, "run", side_effect=AssertionError("detector execution forbidden")):
                projected = scorecard.build_scorecard(manifest.relative_to(ROOT), host="fixture", root=ROOT)
            self.assertEqual("model-compliance-scorecard-v2", projected["schema"])
            self.assertEqual(registry_hash(), projected["registry_sha256"])
            self.assertEqual(5, projected["capture_meta"]["verdict_count"])
            self.assertEqual(5, len(projected["rows"]))
            row = projected["rows"][0]
            self.assertEqual(case_ids[0], row["case_id"])
            self.assertEqual(sha256_file(replay_paths[0]), row["verdict_sha256"])
            self.assertRegex(row["canonical_verdict_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(registry_hash(), row["registry_sha256"])
            self.assertEqual("PASS_STRUCTURAL", row["structural_status"])
            self.assertEqual(12, row["required_checks"])
            self.assertEqual(12, row["accepted_checks"])
            self.assertEqual(0, row["rejected_checks"])
            self.assertEqual(0, row["not_run_checks"])
            self.assertEqual(0, row["indeterminate_checks"])
            self.assertIsNone(row["topology_review_ref"])
            self.assertEqual("NOT_REVIEWED", row["topology_review_status"])
            self.assertEqual("NOT_CLAIMED", row["semantic_truth_status"])
            self.assertEqual("act-surface-syntax", row["checker_results"][0]["checker_id"])
            self.assertEqual("accepted", row["checker_results"][0]["structural_result"])
            self.assertEqual([], scorecard.validate_scorecard(projected))

    def test_scorecard_v1_remains_readable(self) -> None:
        legacy = {
            "schema": "model-compliance-scorecard-v1",
            "capture_meta": {"host": "legacy", "captured_from": "fixtures", "output_count": 1},
            "rows": [
                {
                    "failure_shape": "legacy-shape",
                    "detector": "check_legacy.py",
                    "mode": "structural",
                    "verdict": "NOT-RUN",
                }
            ],
            "non_claims": ["legacy structural projection only"],
        }
        self.assertEqual([], scorecard.validate_scorecard(legacy))
        self.assertIn("legacy-shape", scorecard.to_markdown(legacy))

    def test_private_policy_scan_catches_renamed_and_obfuscated_collections(self) -> None:
        sources = {
            "renamed": 'checks_to_run = ["check_mrp_route_invariants", "check_public_burden_grouping"]\n',
            "obfuscated": 'selection = ("check_" + "mrp_route_invariants", "check_" + "public_burden_grouping")\n',
            "nested": 'policy = {"required": ("mrp-route-invariants", "public-burden-grouping")}\n',
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            for label, source in sources.items():
                with self.subTest(label=label):
                    path = Path(temp) / f"{label}.py"
                    path.write_text(source, encoding="utf-8")
                    self.assertTrue(_source_has_private_policy(path, self.registry))

            benign = Path(temp) / "benign.py"
            benign.write_text(
                'command = [sys.executable, "tools/check_mrp_route_invariants.py", "--outputs", output]\n',
                encoding="utf-8",
            )
            self.assertFalse(_source_has_private_policy(benign, self.registry))

    def test_private_policy_scan_tracks_executable_dataflow_without_unknown_label_false_positives(self) -> None:
        sources = {
            "one_checker_loop": (
                'checks = ["check_mrp_route_invariants"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, checker, "--outputs", output])\n'
            ),
            "concat_alias": (
                'left = ["check_mrp_route_invariants"]\n'
                'right = ["check_public_burden_grouping"]\n'
                'checks = left + right\n'
                'alias = checks\n'
                'for checker in alias:\n    subprocess.run([sys.executable, checker, "--outputs", output])\n'
            ),
            "append_extend": (
                'checks = []\nchecks.append("check_mrp_route_invariants")\n'
                'more = ["check_public_burden_grouping"]\nchecks.extend(more)\n'
                'for checker in checks:\n    subprocess.run([sys.executable, checker, "--outputs", output])\n'
            ),
            "registry_plus_private": (
                'from validation_registry import profile_invocations\n'
                'plan = profile_invocations(registry, "captured-output-structural")\n'
                'checks = ["check_mrp_route_invariants"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, checker, "--outputs", output])\n'
            ),
            "slice_copy_enumerate_command": (
                'base = ["check_mrp_route_invariants", "check_public_burden_grouping"]\n'
                'checks = base.copy()[:1]\n'
                'for _index, checker in enumerate(checks):\n'
                '    command = [sys.executable, checker, "--outputs", output]\n'
                '    subprocess.run(command)\n'
            ),
            "direct_literal_loop": (
                'for checker in ["check_mrp_route_invariants.py"]:\n'
                '    subprocess.run([sys.executable, checker, "--outputs", output])\n'
            ),
            "indexed_single": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'subprocess.run([sys.executable, checks[0], "--outputs", output])\n'
            ),
            "keyword_command": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'command = [sys.executable, checks[0], "--outputs", output]\n'
                'subprocess.run(args=command)\n'
            ),
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            scratch = Path(temp)
            for label, source in sources.items():
                with self.subTest(label=label):
                    path = scratch / f"{label}.py"
                    path.write_text(source, encoding="utf-8")
                    self.assertTrue(_source_has_private_policy(path, self.registry))

            unknown = scratch / "unknown.py"
            unknown.write_text(
                'labels = ["check_save_button", "check_dark_theme"]\n'
                'for label in labels:\n    render(label)\n',
                encoding="utf-8",
            )
            self.assertFalse(_source_has_private_policy(unknown, self.registry))

            direct = scratch / "direct.py"
            direct.write_text(
                'subprocess.run([sys.executable, "tools/check_mrp_route_invariants.py", "--outputs", output])\n',
                encoding="utf-8",
            )
            self.assertFalse(_source_has_private_policy(direct, self.registry))

            echo = scratch / "echo.py"
            echo.write_text(
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["echo", checker])\n',
                encoding="utf-8",
            )
            self.assertFalse(_source_has_private_policy(echo, self.registry))

    def test_private_policy_scan_covers_comprehensions_and_process_import_aliases(self) -> None:
        positives = {
            "list_comprehension": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                '[subprocess.run([sys.executable, checker]) for checker in checks]\n'
            ),
            "set_comprehension": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                '{subprocess.run([sys.executable, checker]) for checker in checks}\n'
            ),
            "dict_comprehension": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                '{checker: subprocess.run([sys.executable, checker]) for checker in checks}\n'
            ),
            "generator_expression": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'tuple(subprocess.run([sys.executable, checker]) for checker in checks)\n'
            ),
            "imported_process_alias": (
                'from subprocess import run as launch\n'
                'checks = ["check_mrp_route_invariants.py"]\n'
                '[launch([sys.executable, checker]) for checker in checks]\n'
            ),
            "assigned_process_alias": (
                'import subprocess as sp\nlaunch = sp.check_call\n'
                'checks = ["check_mrp_route_invariants.py"]\n'
                '[launch([sys.executable, checker]) for checker in checks]\n'
            ),
            "multi_generator_taint": (
                'from subprocess import run as launch\n'
                'checks = ["check_mrp_route_invariants.py"]\n'
                '[launch([sys.executable, checker]) '
                'for source in checks for checker in [source]]\n'
            ),
        }
        negatives = {
            "data_only_comprehension": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'labels = [checker.upper() for checker in checks]\n'
            ),
            "unrelated_run_method": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                '[renderer.run(checker) for checker in checks]\n'
            ),
            "independent_later_generator": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                '[subprocess.run(["echo", label]) '
                'for source in checks for label in ["theme"]]\n'
            ),
            "canonical_projection": (
                'from validation_registry import profile_invocations\n'
                'profile_invocations(registry, "captured-output-structural")\n'
            ),
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            scratch = Path(temp)
            for label, source in positives.items():
                with self.subTest(label=label):
                    path = scratch / f"positive-{label}.py"
                    path.write_text(source, encoding="utf-8")
                    self.assertTrue(_source_has_private_policy(path, self.registry))
            for label, source in negatives.items():
                with self.subTest(label=label):
                    path = scratch / f"negative-{label}.py"
                    path.write_text(source, encoding="utf-8")
                    self.assertFalse(_source_has_private_policy(path, self.registry))

    def test_private_policy_scan_parses_python_launcher_and_interpreter_argv(self) -> None:
        positives = {
            "windows_py": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["py", checker, "--outputs", output])\n'
            ),
            "windows_py_selector": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["py", "-3", checker])\n'
            ),
            "windows_py_tag_selector": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["py.exe", "-V:PythonCore/3.12", checker])\n'
            ),
            "sys_flag": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "-B", checker])\n'
            ),
            "simple_executable_alias": (
                'PY = sys.executable\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([PY, checker])\n'
            ),
            "versioned_python": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["python3.12", checker])\n'
            ),
            "free_threaded_versioned_python": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["python3.13t", checker])\n'
            ),
            "free_threaded_windows_python_path": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([r"C:\\Python313\\python3.13t.exe", checker])\n'
            ),
            "windows_pythonw_path": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([r"C:\\Python312\\pythonw.exe", checker])\n'
            ),
            "option_with_value": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "-X", "dev", checker])\n'
            ),
            "long_option_with_value": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, "--check-hash-based-pycs", "always", checker])\n'
            ),
            "end_of_options": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "--", checker])\n'
            ),
            "registered_module_position": (
                'checks = ["check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, "-m", checks[0]])\n'
            ),
            "unresolved_launcher_fails_closed": (
                'PY = choose_launcher()\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([PY, checker])\n'
            ),
            "unresolved_python_option_fails_closed": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "--future-option", checker])\n'
            ),
            "aliased_flag": (
                'OPTION = "-B"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, OPTION, checker])\n'
            ),
            "chained_aliased_flag": (
                'BASE_OPTION = "-B"\nOPTION = BASE_OPTION\n'
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, OPTION, checker])\n'
            ),
            "aliased_consuming_option_with_value": (
                'OPTION = "-X"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, OPTION, "dev", checker])\n'
            ),
            "unresolved_dynamic_option": (
                'OPTION = choose_option()\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, OPTION, checker])\n'
            ),
            "starred_literal_flags": (
                'FLAGS = ["-B"]\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, *FLAGS, checker])\n'
            ),
            "starred_unresolved_flags": (
                'FLAGS = choose_flags()\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, *FLAGS, checker])\n'
            ),
            "aliased_py_selector": (
                'SELECTOR = "-3"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["py", SELECTOR, checker])\n'
            ),
            "unresolved_dynamic_py_selector": (
                'SELECTOR = choose_selector()\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["py", SELECTOR, checker])\n'
            ),
            "qualified_exact_module_index": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, "-m", modules[0]])\n'
            ),
            "qualified_exact_module_alias": (
                'modules = ["tools.check_mrp_route_invariants"]\nmodule = modules[0]\n'
                'subprocess.run([sys.executable, "-m", module])\n'
            ),
            "qualified_exact_module_loop": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'for module in modules:\n    subprocess.run([sys.executable, "-m", module])\n'
            ),
            "qualified_attached_module_index": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, "-m" + modules[0]])\n'
            ),
            "aliased_prefix_attached_qualified_module_index": (
                'PREFIX = "-m"\nmodules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, PREFIX + modules[0]])\n'
            ),
            "chained_prefix_attached_qualified_module_index": (
                'BASE_PREFIX = "-m"\nPREFIX = BASE_PREFIX\n'
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, PREFIX + modules[0]])\n'
            ),
            "fstring_attached_qualified_module_index": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, f"-m{modules[0]}"])\n'
            ),
            "fstring_aliased_prefix_attached_qualified_module_index": (
                'PREFIX = "-m"\nmodules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, f"{PREFIX}{modules[0]}"])\n'
            ),
            "fstring_chained_prefix_attached_qualified_module_index": (
                'BASE_PREFIX = "-m"\nPREFIX = BASE_PREFIX\n'
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, f"{PREFIX}{modules[0]}"])\n'
            ),
            "fstring_converted_payload_attached_qualified_module_index": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, f"-m{modules[0]!s}"])\n'
            ),
            "fstring_string_formatted_payload_attached_qualified_module_index": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, f"-m{modules[0]:s}"])\n'
            ),
            "fstring_converted_payload_attached_qualified_module_loop": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'for module in modules:\n'
                '    subprocess.run([sys.executable, f"-m{module!s}"])\n'
            ),
            "unresolved_prefix_attached_qualified_module_index": (
                'PREFIX = choose_prefix()\nmodules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, PREFIX + modules[0]])\n'
            ),
            "unsupported_format_attached_module_fails_closed": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'token = "-m{}".format(modules[0])\n'
                'subprocess.run([sys.executable, token])\n'
            ),
            "unsupported_percent_attached_module_fails_closed": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'token = "-m%s" % modules[0]\n'
                'subprocess.run([sys.executable, token])\n'
            ),
            "unsupported_join_attached_module_fails_closed": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'token = "".join(("-m", modules[0]))\n'
                'subprocess.run([sys.executable, token])\n'
            ),
            "oversized_formatted_prefix_fails_closed": (
                'PREFIX = "-m"\nmodules = ["tools.check_mrp_route_invariants"]\n'
                'token = f"{PREFIX:>4097}{modules[0]}"\n'
                'subprocess.run([sys.executable, token])\n'
            ),
            "attached_known_flag": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "-Xdev", checker])\n'
            ),
            "keyword_command_with_flag_alias": (
                'OPTION = "-B"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'command = [sys.executable, OPTION, checks[0]]\nsubprocess.run(args=command)\n'
            ),
            "unknown_attached_option_fails_closed": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "--future=value", checker])\n'
            ),
        }
        negatives = {
            "option_consumes_checker": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "-X", checker])\n'
            ),
            "command_terminal": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "-c", "print(1)", checker])\n'
            ),
            "unrelated_module_terminal": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "-m", "http.server", checker])\n'
            ),
            "known_non_python_later_argument": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["echo", "prefix", checker])\n'
            ),
            "known_non_python_alias": (
                'ECHO = "echo"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([ECHO, checker])\n'
            ),
            "near_miss_free_threaded_launcher": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["python3.13tx", checker])\n'
            ),
            "arbitrary_cpython_launcher": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["cpython3.13t", checker])\n'
            ),
            "aliased_option_consumes_checker": (
                'OPTION = "-X"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, OPTION, checker])\n'
            ),
            "attached_command_terminal": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "-cprint(1)", checker])\n'
            ),
            "aliased_command_terminal": (
                'OPTION = "-c"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, OPTION, "print(1)", checker])\n'
            ),
            "attached_unrelated_module_terminal": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "-mhttp.server", checker])\n'
            ),
            "aliased_prefix_attached_command_terminal": (
                'PREFIX = "-c"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, PREFIX + "print(1)", checker])\n'
            ),
            "aliased_prefix_attached_unrelated_module_terminal": (
                'PREFIX = "-m"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, PREFIX + "http.server", checker])\n'
            ),
            "fstring_aliased_prefix_attached_command_terminal": (
                'PREFIX = "-c"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"{PREFIX}print(1)", checker])\n'
            ),
            "fstring_chained_prefix_attached_command_terminal": (
                'BASE_PREFIX = "-c"\nPREFIX = BASE_PREFIX\n'
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"{PREFIX}print(1)", checker])\n'
            ),
            "fstring_literal_prefix_converted_command_payload_terminal": (
                'code = choose_code()\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"-c{code!r}", checker])\n'
            ),
            "fstring_literal_prefix_formatted_command_payload_terminal": (
                'code = choose_code()\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"-c{code:>10}", checker])\n'
            ),
            "oversized_formatted_command_payload_keeps_literal_terminal_prefix": (
                'code = "print(1)"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"-c{code:>4097}", checker])\n'
            ),
            "fstring_converted_alias_prefix_attached_command_terminal": (
                'PREFIX = "-c"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"{PREFIX!s}print(1)", checker])\n'
            ),
            "fstring_aliased_prefix_attached_unrelated_module_terminal": (
                'PREFIX = "-m"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"{PREFIX}http.server", checker])\n'
            ),
            "fstring_chained_prefix_attached_unrelated_module_terminal": (
                'BASE_PREFIX = "-m"\nPREFIX = BASE_PREFIX\n'
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"{PREFIX}http.server", checker])\n'
            ),
            "fstring_literal_prefix_converted_unrelated_module_terminal": (
                'MODULE = "http.server"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"-m{MODULE!s}", checker])\n'
            ),
            "fstring_repr_payload_is_not_exact_registered_module": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'checks = ["check_public_burden_grouping.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"-m{modules[0]!r}", checker])\n'
            ),
            "fstring_aligned_payload_is_not_exact_registered_module": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'checks = ["check_public_burden_grouping.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"-m{modules[0]:>64}", checker])\n'
            ),
            "fstring_repr_loop_value_is_not_exact_registered_module": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'for module in modules:\n'
                '    subprocess.run([sys.executable, f"-m{module!r}"])\n'
            ),
            "fstring_aligned_loop_value_is_not_exact_registered_module": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'for module in modules:\n'
                '    subprocess.run([sys.executable, f"-m{module:>64}"])\n'
            ),
            "fstring_suffix_loop_value_is_not_exact_registered_module": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'for module in modules:\n'
                '    subprocess.run([sys.executable, f"-m{module}.suffix"])\n'
            ),
            "fstring_prefix_loop_value_is_not_exact_registered_module": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'for module in modules:\n'
                '    subprocess.run([sys.executable, f"-mX{module}"])\n'
            ),
            "concatenated_suffix_loop_value_is_not_exact_registered_module": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'for module in modules:\n'
                '    subprocess.run([sys.executable, "-m" + module + ".suffix"])\n'
            ),
            "fstring_suffix_index_is_not_exact_registered_module": (
                'modules = ["tools.check_mrp_route_invariants"]\n'
                'subprocess.run([sys.executable, f"-m{modules[0]}.suffix"])\n'
            ),
            "fstring_repr_alias_prefix_is_not_an_option": (
                'PREFIX = "-m"\nmodules = ["tools.check_mrp_route_invariants"]\n'
                'checks = ["check_public_burden_grouping.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, f"{PREFIX!r}{modules[0]}", checker])\n'
            ),
            "aliased_unrelated_module_terminal": (
                'OPTION = "-m"\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, OPTION, "http.server", checker])\n'
            ),
            "stdin_terminal": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "-", checker])\n'
            ),
            "version_terminal": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run([sys.executable, "--version", checker])\n'
            ),
            "py_list_terminal": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["py", "--list", checker])\n'
            ),
            "known_non_python_starred": (
                'FLAGS = ["--verbose"]\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["echo", *FLAGS, checker])\n'
            ),
            "known_non_python_unresolved_argument": (
                'OPTION = choose_option()\nchecks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n    subprocess.run(["echo", OPTION, checker])\n'
            ),
            "exact_direct_registered_module_ignores_later_checker_argument": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, "-m", "tools.check_public_burden_grouping", checker])\n'
            ),
            "attached_direct_registered_module_ignores_later_checker_argument": (
                'checks = ["check_mrp_route_invariants.py"]\n'
                'for checker in checks:\n'
                '    subprocess.run([sys.executable, "-mtools.check_public_burden_grouping", checker])\n'
            ),
        }
        self.assertGreaterEqual(len(positives) + len(negatives), 42)
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            scratch = Path(temp)
            for label, source in positives.items():
                with self.subTest(label=label):
                    path = scratch / f"positive-{label}.py"
                    path.write_text(source, encoding="utf-8")
                    self.assertTrue(_source_has_private_policy(path, self.registry))
            for label, source in negatives.items():
                with self.subTest(label=label):
                    path = scratch / f"negative-{label}.py"
                    path.write_text(source, encoding="utf-8")
                    self.assertFalse(_source_has_private_policy(path, self.registry))

    def test_static_fstring_fragment_evaluation_is_resource_bounded(self) -> None:
        bound = MAX_STATIC_FORMATTED_FRAGMENT_CHARS
        self.assertEqual(bound, len(_format_static_string("-c", -1, f">{bound}") or ""))
        self.assertIsNone(_format_static_string("-c", -1, f">{bound + 1}"))
        with patch("builtins.format") as formatter:
            self.assertIsNone(_format_static_string("-c", -1, ">999999999999999999999999"))
            formatter.assert_not_called()
        with patch("builtins.format", side_effect=MemoryError):
            self.assertIsNone(_format_static_string("-c", -1, ""))

    def test_static_fragment_budget_is_aggregate_across_joined_and_add_paths(self) -> None:
        assignments = {"PREFIX": [ast.Constant("-c")]}
        joined = ast.parse(
            'f"' + "{PREFIX:>4096}" * 256 + '"', mode="eval"
        ).body
        added = ast.parse(
            " + ".join(['f"{PREFIX:>4096}"'] * 64), mode="eval"
        ).body
        real_format = format
        for expression in (joined, added):
            with self.subTest(node=type(expression).__name__):
                with patch("builtins.format", wraps=real_format) as formatter:
                    fragments = _string_concatenation_fragments(expression, assignments)
                self.assertIsNotNone(fragments)
                self.assertLessEqual(
                    sum(len(fragment) for fragment in fragments or () if isinstance(fragment, str)),
                    MAX_STATIC_FORMATTED_FRAGMENT_CHARS,
                )
                self.assertTrue(any(isinstance(fragment, ast.AST) for fragment in fragments or ()))
                self.assertLessEqual(formatter.call_count, 1)

        deep_source = " + ".join(['"x"'] * 1100)
        deep = ast.parse(deep_source, mode="eval").body
        fragments = _string_concatenation_fragments(deep, assignments)
        self.assertIsNotNone(fragments)
        self.assertTrue(any(isinstance(fragment, ast.AST) for fragment in fragments or ()))
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            path = Path(temp) / "deep-add.py"
            path.write_text(
                "token = " + deep_source + "\n"
                'checks = ["check_mrp_route_invariants.py"]\n'
                "for checker in checks:\n"
                "    subprocess.run([sys.executable, token, checker])\n",
                encoding="utf-8",
            )
            self.assertTrue(_source_has_private_policy(path, self.registry))

    def test_discovery_catches_profile_clone_and_comment_cannot_fake_registry_derivation(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            scratch = Path(temp)
            tools = scratch / "tools"
            tools.mkdir()
            (tools / "renamed_profile.py").write_text(
                "selection = (\n"
                '    "check_" + "mrp_route_invariants",\n'
                '    "public-burden-grouping",\n'
                '    "mid-reread-pressure",\n'
                '    "manual-smoke-render-contract",\n'
                '    "concealment-mode",\n'
                '    "act-surface-syntax",\n'
                ")\n",
                encoding="utf-8",
            )
            (tools / "comment_bypass.py").write_text(
                "# profile_invocations( is inert text, not registry derivation\n"
                'BATTERY = ["fixture-a", "fixture-b"]\n',
                encoding="utf-8",
            )
            (tools / "mixed_private.py").write_text(
                "from validation_registry import profile_invocations\n"
                "profile_invocations({}, 'fixture')\n"
                'BATTERY = ["fixture-a", "fixture-b"]\n',
                encoding="utf-8",
            )
            self.assertEqual(
                {"tools/renamed_profile.py", "tools/comment_bypass.py", "tools/mixed_private.py"},
                discover_validation_consumers(scratch, self.registry),
            )

    def test_live_registry_has_zero_private_consumers(self) -> None:
        findings = validate_registry(self.registry, root=ROOT, scan_repo=True)
        private = [finding for finding in findings if finding.failure_class == "private_consumer_battery"]
        self.assertEqual([], private)
        self.assertTrue(all(row["policy_source"] == "registry" for row in self.registry["consumers"]))

    def test_local_ci_wires_all_three_validation_integrity_suites(self) -> None:
        required = {
            "python -B tests/validation-integrity/test_hardening.py",
            "python -B tests/validation-integrity/test_candidate_hardening.py",
            "python -B tests/validation-integrity/test_consumer_migration.py",
            "python -B tests/validation-integrity/test_scorecard_hardening.py",
        }
        self.assertTrue(required.issubset(set(local_ci.COMMANDS)))


if __name__ == "__main__":
    unittest.main()
