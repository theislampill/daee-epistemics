from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools" / "check_state_capsule.py"
FIXTURES = Path(__file__).resolve().parent
GENERATOR_PATH = FIXTURES / "build_fixtures.py"
SPEC = importlib.util.spec_from_file_location("state_capsule_v2_fixture_builder", GENERATOR_PATH)
assert SPEC and SPEC.loader
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def run_checker(path: Path, *, release_bearing: bool = True) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-B", str(CHECKER), "--capsule", str(path)]
    if release_bearing:
        command.append("--release-bearing")
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8")


def write_payload(directory: Path, name: str, payload: dict) -> Path:
    path = directory / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


class StateCapsuleV2CheckerTests(unittest.TestCase):
    def test_embedded_operation_capsule_is_congruent_with_primary_owner(self) -> None:
        state_schema = json.loads((ROOT / "schema" / "state-capsule-v2.schema.json").read_text(encoding="utf-8"))
        operation_schema = json.loads((ROOT / "schema" / "operation-capsule.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state_schema["$defs"]["operation_capsule"],
            operation_schema["$defs"]["operation_capsule"],
            "embedded Plan05 contract drifted from the standalone primary owner",
        )

    def test_candidate_dispositions_are_exact_a07_contract(self) -> None:
        state_schema = json.loads((ROOT / "schema" / "state-capsule-v2.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(
            set(state_schema["$defs"]["candidate_event"]["properties"]["disposition"]["enum"]),
            {"activate_held", "instantiate_generated", "defer_preempted", "non_load_bearing", "hold_partial"},
        )

    def test_all_five_a07_candidate_dispositions_have_release_bearing_neighbors(self) -> None:
        observed: set[str] = set()
        for fixture in sorted((FIXTURES / "valid").glob("candidate-disposition-*.json")):
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            observed.update(
                row["disposition"]
                for cycle in payload["burden_cycles"]
                for row in cycle["reread"]["raw_exit"]["candidate_events"]
            )
            result = run_checker(fixture)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(observed, {"activate_held", "instantiate_generated", "defer_preempted", "non_load_bearing", "hold_partial"})

    def test_reread_signature_changes_with_performed_operation_land_delta(self) -> None:
        payload = BUILDER.base_payload(stage="stage-05-mrp-reread-terminal-state")
        before = payload["reread_signature_history"][0]["reread_signature_sha256"]
        payload["operation_capsules"][0]["performed_operation"]["application"] += " with a materially changed post-Land effect"
        payload["operation_capsules"][0]["delta"]["result"] += " materially changed"
        payload["operation_capsules"][0]["after_state"]["state"] += " materially changed"
        payload["operation_capsules"][0]["delta"]["recoverability_evidence"][0]["value"] = payload["operation_capsules"][0]["after_state"]["state"]
        payload["burden_cycles"][0]["post_land_delta"]["basis_refs"] = ["basis:C1:materially-changed-delta"]
        BUILDER.rehash_payload(payload)
        after = payload["reread_signature_history"][0]["reread_signature_sha256"]
        self.assertNotEqual(before, after)
        with tempfile.TemporaryDirectory() as temporary:
            path = write_payload(Path(temporary), "delta-sensitive.json", payload)
            result = run_checker(path)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_closure_owner_is_called_with_independent_authority(self) -> None:
        source = CHECKER.read_text(encoding="utf-8")
        self.assertNotIn("derive_closure_decision(trace)", source)
        self.assertIn("upstream_universe=", source)
        self.assertIn("upstream_inventory_sha256=", source)

    def test_plan03_and_plan06_are_bound_to_independent_authority(self) -> None:
        payload = BUILDER.base_payload()
        self.assertEqual(
            payload["partition_derivative_mappings_sha256"],
            BUILDER.canonical_sha(payload["partition_derivative_mappings"]),
        )
        authority = payload["topology_mass_evidence_authority"]
        self.assertEqual(payload["topology_mass_evidence_authority_sha256"], BUILDER.canonical_sha(authority))
        self.assertEqual(
            payload["topology_mass_accounting"]["staged_handoff_sha256"],
            payload["upstream_obligation_set_sha256"],
        )
        self.assertTrue(authority["artifacts"])
        self.assertTrue(authority["validator_receipts"])
        with tempfile.TemporaryDirectory() as temporary:
            path = write_payload(Path(temporary), "authority-bound.json", payload)
            result = run_checker(path)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_valid_fixtures_bind_reread_signature_history_and_resource_policy_hash(self) -> None:
        for fixture in sorted((FIXTURES / "valid").glob("*.json")):
            with self.subTest(fixture=fixture.name):
                payload = json.loads(fixture.read_text(encoding="utf-8"))
                self.assertIn("reread_signature_history", payload)
                self.assertIn("reread_signature_history_sha256", payload)
                for cycle in payload["burden_cycles"]:
                    if "reread" in cycle:
                        self.assertIn("reread_signature_sha256", cycle["reread"])
                expected = BUILDER.self_sha(payload["resource_policy"], "policy_sha256")
                self.assertEqual(payload["resource_policy"]["policy_sha256"], expected)

    def test_fixture_lattice_is_fresh(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(GENERATOR_PATH), "--check"],
            cwd=ROOT, text=True, capture_output=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_neighboring_valids_are_release_bearing(self) -> None:
        for fixture in sorted((FIXTURES / "valid").glob("*.json")):
            with self.subTest(fixture=fixture.name):
                result = run_checker(fixture)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_overlapping_candidate_hyperedges_are_valid(self) -> None:
        fixture = FIXTURES / "valid" / "overlapping-candidate-hyperedges.json"
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        memberships = [
            row["partition_id"] for row in payload["candidate_state_partitions"]
            if "N2" in row["member_state_ids"]
        ]
        self.assertEqual(memberships, ["NP1", "NP2"])
        result = run_checker(fixture)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_wide_v2_topology_has_no_fixed_candidate_or_byte_cap(self) -> None:
        payload = BUILDER.base_payload()
        for index in range(250):
            state_id = f"wide-candidate-{index}"
            partition_id = f"wide-partition-{index}"
            payload["candidate_states"].append({
                "state_id": state_id, "frame": f"topic-neutral capacity row {index} " + ("x" * 160),
                "frame_token": state_id, "observation_unit_ids": ["U1"], "pressure_ids": ["P1"],
                "live_registers": ["Omega"], "read_status": "distributed", "confidence": "low",
                "status": "rejected", "partition_ids": [partition_id], "merged_into": None,
                "decisive_missing_differentiator": None, "hold_gate": None, "next_review_point": None,
                "basis": "bounded non-fit basis",
            })
            payload["candidate_state_partitions"].append({
                "partition_id": partition_id, "member_state_ids": [state_id],
                "shared_observation_unit_ids": ["U1"], "decision": "reject_nonfit",
                "selected_state_id": None, "held_state_ids": [], "merged_state_ids": [],
                "rejected_state_ids": [state_id],
                "comparison": {"pressure_set_relation":"distinct","register_relation":"distinct","owner_eligibility_relation":"distinct","held_route_relation":"distinct","closure_consequence_relation":"distinct"},
                "decisive_differentiator": "bounded non-fit", "basis_unit_ids": ["U1"], "basis": "bounded non-fit",
            })
        payload["input_pressures"][0]["candidate_state_ids"] = [row["state_id"] for row in payload["candidate_states"]]
        payload["burden_partition_decisions"][0]["candidate_state_ids"] = list(payload["input_pressures"][0]["candidate_state_ids"])
        BUILDER.rehash_payload(payload)
        with tempfile.TemporaryDirectory() as temporary:
            path = write_payload(Path(temporary), "wide-valid-v2.json", payload)
            self.assertGreater(path.stat().st_size, 91_000)
            result = run_checker(path)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_capacity_probes_do_not_become_cardinality_laws(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for burden_count in (1, 10, 20):
                with self.subTest(burden_count=burden_count):
                    payload = BUILDER.multi_generation_payload(burden_count - 1)
                    result = run_checker(write_payload(root, f"burdens-{burden_count}.json", payload))
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for submove_count in (1, 3, 6, 8):
                with self.subTest(submove_count=submove_count):
                    payload = BUILDER.multi_capsule_payload(submove_count)
                    result = run_checker(write_payload(root, f"submoves-{submove_count}.json", payload))
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_historical_v1_is_readable_but_not_release_bearing(self) -> None:
        fixture = FIXTURES / "invalid" / "release-bearing-v1.json"
        historical = run_checker(fixture, release_bearing=False)
        self.assertEqual(historical.returncode, 0, historical.stdout + historical.stderr)
        release = run_checker(fixture, release_bearing=True)
        self.assertEqual(release.returncode, 1, release.stdout + release.stderr)
        self.assertIn("release-bearing-v1", release.stdout + release.stderr)

    def test_active_invalids_fail_for_exact_stage_class_and_subcode(self) -> None:
        for expectation_path in sorted((FIXTURES / "invalid").glob("*.expectation.json")):
            with self.subTest(expectation=expectation_path.name):
                expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
                self.assertIn("expected_failure_subcode", expectation)
                fixture = expectation_path.with_name(expectation["fixture"])
                result = run_checker(fixture)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, expectation["expected_exit_code"], output)
                self.assertIn(expectation["expected_failure_class"], output)
                self.assertIn(expectation["expected_failure_subcode"], output)
                self.assertIn(f"stage={expectation['expected_earliest_stage']}", output)
                for marker in expectation["required_diagnostic_markers"]:
                    self.assertIn(marker.lower(), output.lower())
                for forbidden in expectation["forbidden_artifacts"]:
                    self.assertFalse((fixture.parent / forbidden).exists(), forbidden)

    def test_v2_replay_freezes_trace_and_stage02_baseline(self) -> None:
        first = BUILDER.base_payload(stage="stage-07-release-output")
        second = BUILDER.base_payload(stage="stage-08-verifier-sidecars")
        first["capsule_id"] = "capsule-v2-replay-001"
        second["capsule_id"] = "capsule-v2-replay-002"
        BUILDER.rehash_payload(first)
        BUILDER.rehash_payload(second)
        first_bytes = (json.dumps(first, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        second["previous_capsule_sha256"] = hashlib.sha256(first_bytes).hexdigest()
        BUILDER.set_projections(second)
        with tempfile.TemporaryDirectory() as temporary:
            replay_dir = Path(temporary)
            (replay_dir / "capsule-001.json").write_bytes(first_bytes)
            write_payload(replay_dir, "capsule-002.json", second)
            command = [sys.executable, "-B", str(CHECKER), "--replay", str(replay_dir), "--release-bearing"]
            green = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8")
            self.assertEqual(green.returncode, 0, green.stdout + green.stderr)

            second["trace_id"] = "mutated-trace"
            BUILDER.set_projections(second)
            write_payload(replay_dir, "capsule-002.json", second)
            red = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8")
            self.assertEqual(red.returncode, 1, red.stdout + red.stderr)
            self.assertIn("replay-history-mutation", red.stdout + red.stderr)

    def test_v2_replay_rejects_candidate_event_disappearance(self) -> None:
        first = BUILDER.base_payload(stage="stage-05-mrp-reread-terminal-state")
        first["capsule_id"] = "capsule-v2-candidate-history-001"
        raw = first["burden_cycles"][0]["reread"]["raw_exit"]
        raw["candidate_events"] = [BUILDER.candidate_event("CE-HISTORY", "runtime-candidate", 10, "non_load_bearing", kind="escape_route")]
        raw["field_diagnostics"][0]["event_index"] = 11
        raw["field_diagnostics"][1]["event_index"] = 12
        raw["event_index"] = 13
        BUILDER.rehash_payload(first)
        second = json.loads(json.dumps(first))
        second["capsule_id"] = "capsule-v2-candidate-history-002"
        second["burden_cycles"][0]["reread"]["raw_exit"]["candidate_events"] = []
        BUILDER.rehash_payload(second)
        first_bytes = (json.dumps(first, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        second["previous_capsule_sha256"] = hashlib.sha256(first_bytes).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            replay_dir = Path(temporary)
            (replay_dir / "capsule-001.json").write_bytes(first_bytes)
            write_payload(replay_dir, "capsule-002.json", second)
            result = subprocess.run(
                [sys.executable, "-B", str(CHECKER), "--replay", str(replay_dir), "--release-bearing"],
                cwd=ROOT, text=True, capture_output=True, encoding="utf-8",
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("candidate-transition-invalid", result.stdout + result.stderr)
            self.assertIn("disappeared", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
