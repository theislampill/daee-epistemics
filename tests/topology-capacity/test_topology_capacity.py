from __future__ import annotations

import importlib.util
import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
INVALID = Path(__file__).parent / "specs" / "invalid"
VALID = Path(__file__).parent / "specs" / "valid"
PROBE_SET = Path(__file__).parent / "probe-set.json"
POSITIVE_RELATIONS = (
    "alpha-rename",
    "permutation",
    "split-conservation",
    "merge-with-proof",
    "irrelevant-filler",
    "payload-length",
    "valid-hold",
    "generated-child",
    "preempt-resultant",
)


def load_tool(name: str):
    path = TOOLS / f"{name}.py"
    tools_text = str(TOOLS)
    if tools_text not in sys.path:
        sys.path.insert(0, tools_text)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TopologyCapacityContractTest(unittest.TestCase):
    @staticmethod
    def _write_json(path: Path, payload: object, library: object) -> None:
        path.write_bytes(library.canonical_bytes(payload))

    @staticmethod
    def _refresh_stage08_hashes(
        output: Path, generator: object, library: object, names: tuple[str, ...]
    ) -> None:
        stage08_path = output / generator.STAGE_FILES["08"]
        stage08 = json.loads(stage08_path.read_text(encoding="utf-8"))
        for name in names:
            stage08["artifact_sha256"][name] = hashlib.sha256(
                (output / name).read_bytes()
            ).hexdigest()
        stage08_path.write_bytes(library.canonical_bytes(stage08))

    @staticmethod
    def _shared_operation_case(
        output: Path,
        generator: object,
        library: object,
        mutation: str | None,
    ) -> None:
        stage03_path = output / generator.STAGE_FILES["03"]
        stage04_path = output / generator.STAGE_FILES["04"]
        stage07_path = output / generator.STAGE_FILES["07"]
        stage02 = json.loads(
            (output / generator.STAGE_FILES["02"]).read_text(encoding="utf-8")
        )
        stage03 = json.loads(stage03_path.read_text(encoding="utf-8"))
        stage04 = json.loads(stage04_path.read_text(encoding="utf-8"))
        stage07 = json.loads(stage07_path.read_text(encoding="utf-8"))
        submoves = 3
        first, second = stage04["acts"][0], stage04["acts"][submoves]
        decision_id = "shared-neutral-operation-proof"
        second["semantic_payload"] = first["semantic_payload"] + " neutral filler " * 20
        second["semantic_body_sha256"] = library.canonical_sha256(
            second["semantic_payload"]
        )
        second["normalized_evidence_sha256"] = first["normalized_evidence_sha256"]
        first["shared_operation_decision_id"] = decision_id
        second["shared_operation_decision_id"] = decision_id
        relation = {
            "relation_schema": "daee-shared-operation-relation-v1",
            "source_relation": "same-function-source-frame-restoration-vector",
            "decision_id": decision_id,
            "obligation_ids": sorted([first["obligation_id"], second["obligation_id"]]),
            "pressure_ids": sorted([first["pressure_id"], second["pressure_id"]]),
            "owner_id": first["owner_id"],
            "operation": first["operation"],
            "register_id": first["register_id"],
            "target_burden_ids": sorted([first["burden_id"], second["burden_id"]]),
            "normalized_evidence_sha256": first["normalized_evidence_sha256"],
        }
        upstream = stage02.get("shared_operation_authorizations", [])
        if upstream:
            authority = upstream[0]
            relation.update(
                {
                    "upstream_shared_authorization_id": authority[
                        "shared_authorization_id"
                    ],
                    "upstream_shared_authorization_sha256": authority[
                        "authorization_sha256"
                    ],
                    "upstream_partition_decision_ids": authority[
                        "upstream_partition_decision_ids"
                    ],
                    "upstream_partition_authorization_sha256": authority[
                        "upstream_partition_authorization_sha256"
                    ],
                }
            )
        relation["authorization_sha256"] = library.canonical_sha256(relation)
        if mutation == "fabricated":
            relation.pop("authorization_sha256")
        elif mutation == "wrong-hash":
            relation["authorization_sha256"] = "0" * 64
        elif mutation == "cross-upstream":
            relation["upstream_partition_decision_ids"] = list(
                reversed(relation["upstream_partition_decision_ids"])
            )
        elif mutation == "mismatched-relation":
            relation["owner_id"] = stage04["acts"][1]["owner_id"]
            relation_without_hash = {
                key: value
                for key, value in relation.items()
                if key != "authorization_sha256"
            }
            relation["authorization_sha256"] = library.canonical_sha256(
                relation_without_hash
            )
        stage03["shared_operation_decisions"] = [relation]
        first["shared_operation_authorization_sha256"] = relation.get(
            "authorization_sha256"
        )
        second["shared_operation_authorization_sha256"] = relation.get(
            "authorization_sha256"
        )
        if mutation == "act-wrong-authorization":
            second["shared_operation_authorization_sha256"] = "0" * 64
        stage07["operations"] = copy.deepcopy(stage04["acts"])
        stage03_path.write_bytes(library.canonical_bytes(stage03))
        stage04_path.write_bytes(library.canonical_bytes(stage04))
        stage07_path.write_bytes(library.canonical_bytes(stage07))
        generator.refresh_case_bindings(output)

    @staticmethod
    def _write_source_authorized_spec(
        source: Path, destination: Path, library: object
    ) -> None:
        payload = library.validate_spec(json.loads(source.read_text(encoding="utf-8")))
        evidence_identity = library.canonical_sha256(
            library.normalized_evidence_body(
                "performed evidence axis 1 operation neutral-operation-1"
            )
        )
        payload["shared_operation_authorizations"] = [
            library.make_shared_operation_authorization(
                authorization_key="shared-operation-source-1",
                upstream_partition_keys=[
                    "pressure-partition-1",
                    "pressure-partition-2",
                ],
                pressure_ordinals=[1, 2],
                receiving_burden_ordinals=[1, 2],
                owner_ordinal=1,
                evidence_identity=evidence_identity,
            )
        ]
        destination.write_bytes(library.canonical_bytes(payload))

    def test_generated_child_without_reread_fails_at_stage05(self) -> None:
        checker = load_tool("check_topology_capacity_properties")
        spec_path = INVALID / "generated-child-missing-reread.json"
        expectation = json.loads(
            (INVALID / "generated-child-missing-reread.expectation.json").read_text(
                encoding="utf-8"
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            diagnostic = checker.check_spec_path(spec_path, Path(directory))
            self.assertEqual(diagnostic["exit_code"], expectation["expected_exit_code"])
            self.assertEqual(
                diagnostic["earliest_stage"], expectation["expected_earliest_stage"]
            )
            self.assertEqual(
                diagnostic["failure_class"], expectation["expected_failure_class"]
            )
            self.assertEqual(
                diagnostic["failure_subcode"], expectation["expected_failure_subcode"]
            )
            self.assertEqual(
                diagnostic["downstream_invalidated"],
                expectation["expected_downstream_invalidated"],
            )
            artifact_root = Path(diagnostic["artifact_root"])
            for relative in expectation["forbidden_artifacts"]:
                self.assertFalse((artifact_root / relative).exists(), relative)

    def test_historical_eligible_owner_omission_is_already_green_neighbor(self) -> None:
        owner = load_tool("owner_obligation_coverage")
        fixture = json.loads(
            (Path(__file__).parent / "current-false-pass" / "eligible-owner-unexecuted.json").read_text(
                encoding="utf-8"
            )
        )
        findings = owner.validate_owner_obligation_coverage(
            fixture,
            upstream_obligation_ids=fixture["upstream_obligation_ids"],
            upstream_pressure_ids=["P1"],
            upstream_partition_decision_ids=["BP1"],
            upstream_derivative_inventory=[],
            upstream_derivative_inventory_sha256=owner._canonical_sha256([]),
        )
        self.assertEqual(len(findings), 1, findings)
        self.assertEqual(findings[0]["failure_class"], "owner-obligation-coverage")
        self.assertEqual(findings[0]["failure_subcode"], "eligible-obligation-unpaid")

    def test_schema_has_no_cardinality_maximum(self) -> None:
        schema = json.loads(
            (ROOT / "schema" / "topology-capacity-spec.schema.json").read_text(
                encoding="utf-8"
            )
        )
        encoded = json.dumps(schema, sort_keys=True)
        self.assertNotIn('"maximum"', encoded)
        self.assertNotIn('"maxItems"', encoded)

    def test_spec_validation_rejects_nonpositive_required_cardinality(self) -> None:
        library = load_tool("topology_capacity_lib")
        payload = json.loads((VALID / "chain-b10-s3.json").read_text(encoding="utf-8"))
        payload["dimensions"]["baseline_burdens"] = 0
        with self.assertRaisesRegex(ValueError, "baseline_burdens"):
            library.validate_spec(payload)

    def test_spec_validation_rejects_unknown_dimension_policy(self) -> None:
        library = load_tool("topology_capacity_lib")
        payload = json.loads((VALID / "chain-b10-s3.json").read_text(encoding="utf-8"))
        payload["dimensions"]["maximum_burdens"] = 20
        with self.assertRaisesRegex(ValueError, "unknown dimension"):
            library.validate_spec(payload)

    def test_same_seed_is_byte_deterministic_and_alternate_seed_is_structural(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        source = VALID / "diamond-b4-s3.json"
        with tempfile.TemporaryDirectory() as parent:
            parent_path = Path(parent)
            first = parent_path / "first"
            second = parent_path / "second"
            alternate = parent_path / "alternate"
            generator.generate_case(source, first)
            generator.generate_case(source, second)
            self.assertEqual(generator.directory_digest(first), generator.directory_digest(second))
            payload = json.loads(source.read_text(encoding="utf-8"))
            payload["seed"] += 1
            alt_spec = parent_path / "alternate.json"
            alt_spec.write_text(json.dumps(payload), encoding="utf-8")
            generator.generate_case(alt_spec, alternate)
            self.assertNotEqual(generator.directory_digest(first), generator.directory_digest(alternate))
            checker = load_tool("check_topology_capacity_properties")
            self.assertEqual(checker.check_generated_directory(first)["exit_code"], 0)
            self.assertEqual(checker.check_generated_directory(alternate)["exit_code"], 0)
            self.assertEqual(
                checker.dimension_signature(first), checker.dimension_signature(alternate)
            )

    def test_output_directory_must_be_absent(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        with tempfile.TemporaryDirectory() as parent:
            occupied = Path(parent) / "occupied"
            occupied.mkdir()
            with self.assertRaisesRegex(FileExistsError, "absent"):
                generator.generate_case(VALID / "independent-b1-s1.json", occupied)

    def test_repeated_filler_cannot_reuse_operation_body_identity(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        with tempfile.TemporaryDirectory() as parent:
            output = Path(parent) / "case"
            generator.generate_case(VALID / "chain-b10-s3.json", output)
            stage04_path = output / generator.STAGE_FILES["04"]
            stage04 = json.loads(stage04_path.read_text(encoding="utf-8"))
            stage04["acts"][0]["semantic_payload"] = "neutral filler " * 40
            stage04_path.write_bytes(library.canonical_bytes(stage04))
            generator.refresh_case_bindings(output)
            diagnostic = checker.check_generated_directory(output)
            self.assertEqual(diagnostic["earliest_stage"], "04")
            self.assertEqual(diagnostic["failure_class"], "operation-body-identity")
            self.assertEqual(diagnostic["failure_subcode"], "semantic-body-hash-mismatch")

    def test_pairwise_probe_set_and_21_burden_neighbor_pass(self) -> None:
        checker = load_tool("check_topology_capacity_properties")
        report = checker.check_probe_set(Path(__file__).parent / "probe-set.json")
        self.assertEqual(report["exit_code"], 0, report)
        self.assertTrue({1, 10, 20, 21}.issubset(set(report["observed"]["burdens"])))
        self.assertTrue({1, 3, 6, 8}.issubset(set(report["observed"]["submoves"])))
        self.assertEqual(report["non_claim"], "structural probes are not semantic truth")

    def test_metamorphic_cli_executes_real_siblings_for_supplied_probe_set(self) -> None:
        checker = load_tool("check_topology_capacity_properties")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = checker.main(["--metamorphic", "--probe-set", str(PROBE_SET)])
        self.assertEqual(code, 0)
        report = json.loads(stdout.getvalue())
        selected = len(json.loads(PROBE_SET.read_text(encoding="utf-8"))["specs"]) * len(POSITIVE_RELATIONS)
        self.assertEqual(report.get("selected_relation_rows"), selected)
        self.assertEqual(
            report.get("executed_positive_relations")
            + report.get("not_applicable_relations"),
            selected,
        )
        self.assertEqual(report.get("probe_set"), str(PROBE_SET.resolve()))
        for row in report["relations"]:
            self.assertIn("base_spec", row)
            self.assertRegex(row.get("sibling_sha256", ""), r"^[0-9a-f]{64}$")
            self.assertIn("oracle_before", row)
            self.assertIn("oracle_after", row)

    def test_every_positive_relation_has_executed_sabotage_detection(self) -> None:
        checker = load_tool("check_topology_capacity_properties")
        evaluate = getattr(checker, "evaluate_metamorphic_relation", None)
        self.assertTrue(callable(evaluate), "executed metamorphic evaluator is absent")
        for relation in POSITIVE_RELATIONS:
            with self.subTest(relation=relation):
                result = evaluate(VALID / "mixed-b10-s6.json", relation, sabotage=True)
                if result.get("status") == "not-applicable":
                    self.assertEqual(relation, "permutation")
                    self.assertFalse(result["transformed"])
                    continue
                self.assertEqual(result["exit_code"], 1, result)
                self.assertEqual(result["failure_class"], "metamorphic-oracle-sabotage-detected")

    def test_probe_suite_reports_graph_oracles_and_sabotage_for_every_relation(self) -> None:
        checker = load_tool("check_topology_capacity_properties")
        specs = json.loads(PROBE_SET.read_text(encoding="utf-8"))["specs"]
        selected = len(specs) * len(POSITIVE_RELATIONS)
        report = checker.run_metamorphic_suite(PROBE_SET)
        self.assertEqual(report["exit_code"], 0, report)
        expected = report["executed_positive_relations"]
        self.assertEqual(report.get("selected_relation_rows"), selected, report)
        self.assertEqual(selected, 108)
        self.assertEqual(report.get("executed_positive_relations"), 98, report)
        self.assertEqual(report.get("not_applicable_relations"), 10, report)
        self.assertEqual(report.get("executed_sabotage_relations"), 98, report)
        self.assertEqual(report.get("executed_sabotage_relations"), expected, report)
        sabotage_rows = report.get("sabotage_relations", [])
        self.assertEqual(len(sabotage_rows), expected, report)
        self.assertEqual(
            {(Path(row["base_spec"]).name, row["relation"]) for row in sabotage_rows},
            {
                (Path(row["base_spec"]).name, row["relation"])
                for row in report["applicability_matrix"]
                if row["applicable"]
            },
        )
        generated = checker.evaluate_metamorphic_relation(
            VALID / "diamond-b4-s3.json", "generated-child"
        )
        self.assertEqual(generated["exit_code"], 0, generated)
        for key in (
            "dependency_graph",
            "generation_graph",
            "parent_relations",
            "projection_relations",
            "event_relations",
            "lifecycle_relations",
        ):
            self.assertIn(key, generated["oracle_before"], key)
            self.assertIn(key, generated["oracle_after"], key)
        self.assertEqual(
            generated.get("base_dependency_shape"),
            generated.get("sibling_dependency_shape"),
        )

    def test_diamond_generated_child_wrong_parent_is_rejected(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        with tempfile.TemporaryDirectory() as parent:
            parent_path = Path(parent)
            spec = json.loads((VALID / "diamond-b4-s3.json").read_text(encoding="utf-8"))
            spec["dimensions"]["generated_burdens"] = 1
            spec["dimensions"]["generation_depth"] = 1
            spec_path = parent_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            output = parent_path / "case"
            generator.generate_case(spec_path, output)
            stage03_path = output / generator.STAGE_FILES["03"]
            stage05_path = output / generator.STAGE_FILES["05"]
            stage03 = json.loads(stage03_path.read_text(encoding="utf-8"))
            stage05 = json.loads(stage05_path.read_text(encoding="utf-8"))
            generated = next(row for row in stage05["burden_cycles"] if row["origin"] == "B_MRP")
            wrong_parent = [row for row in stage05["burden_cycles"] if row["origin"] == "B_LA"][1]
            generated["parent_cycle_id"] = wrong_parent["cycle_id"]
            next(row for row in stage05["lifecycle"] if row["burden_id"] == generated["burden_id"])[
                "parent_id"
            ] = wrong_parent["burden_id"]
            next(row for row in stage03["burden_cycles"] if row["cycle_id"] == generated["cycle_id"])[
                "parent_cycle_id"
            ] = wrong_parent["cycle_id"]
            stage03_path.write_bytes(library.canonical_bytes(stage03))
            stage05_path.write_bytes(library.canonical_bytes(stage05))
            generator.refresh_case_bindings(output)
            diagnostic = checker.check_generated_directory(output)
            self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
            self.assertEqual(diagnostic["earliest_stage"], "03", diagnostic)
            self.assertEqual(diagnostic["failure_class"], "burden-cycle-reentry", diagnostic)

    def test_generated_case_retains_canonical_source_spec_and_hash(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        with tempfile.TemporaryDirectory() as parent:
            output = Path(parent) / "case"
            generator.generate_case(VALID / "diamond-b4-s3.json", output)
            retained = output / "topology-spec.json"
            self.assertTrue(retained.is_file(), "canonical source spec was not retained")
            payload = json.loads(retained.read_text(encoding="utf-8"))
            manifest = json.loads((output / "topology-dimensions.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_spec_sha256"], library.canonical_sha256(payload))

    def test_lockstep_manifest_and_record_corruption_is_rejected_against_source_spec(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        with tempfile.TemporaryDirectory() as parent:
            output = Path(parent) / "case"
            generator.generate_case(VALID / "diamond-b4-s3.json", output)
            retained = output / "topology-spec.json"
            self.assertTrue(retained.exists(), "source-spec custody precondition missing")
            manifest_path = output / "topology-dimensions.json"
            stage01_path = output / generator.STAGE_FILES["01"]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            stage01 = json.loads(stage01_path.read_text(encoding="utf-8"))
            manifest["source_observation_ids"] = manifest["source_observation_ids"][1:]
            stage01["observations"] = stage01["observations"][1:]
            manifest_path.write_bytes(library.canonical_bytes(manifest))
            stage01_path.write_bytes(library.canonical_bytes(stage01))
            generator.refresh_case_bindings(output)
            diagnostic = checker.check_generated_directory(output)
            self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
            self.assertEqual(diagnostic["failure_class"], "source-spec-parity")

    def test_generated_and_held_burdens_have_ordered_reentry_cycles(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        with tempfile.TemporaryDirectory() as parent:
            output = Path(parent) / "case"
            generator.generate_case(VALID / "mixed-b10-s6.json", output)
            stages = {
                number: json.loads((output / generator.STAGE_FILES[number]).read_text(encoding="utf-8"))
                for number in ("03", "04", "05")
            }
            for number in ("03", "04", "05"):
                self.assertTrue(stages[number].get("burden_cycles"), f"Stage{number} burden cycles absent")
            generated = [row for row in stages["05"]["burden_cycles"] if row["origin"] == "B_MRP"]
            self.assertEqual([row["generation_depth"] for row in generated], [1, 2])
            held = [row for row in stages["05"]["burden_cycles"] if row.get("activated_from_hold")]
            self.assertEqual(len(held), 1)
            for row in generated + held:
                self.assertIn("stage03_cycle_ref", row)
                self.assertIn("stage04_cycle_ref", row)
                self.assertEqual(row["event_kinds"][-2:], ["land", "reread"])

    def test_cycle_sabotage_missing_out_of_order_and_nonincrementing_fails(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        checker = load_tool("check_topology_capacity_properties")
        self.assertTrue(callable(getattr(generator, "sabotage_case", None)), "cycle sabotage helper absent")
        self.assertTrue(callable(getattr(generator, "refresh_case_bindings", None)), "binding refresh helper absent")
        for sabotage in ("missing-stage04-cycle", "out-of-order-cycle", "nonincrementing-depth"):
            with self.subTest(sabotage=sabotage), tempfile.TemporaryDirectory() as parent:
                output = Path(parent) / "case"
                generator.generate_case(VALID / "generated-chain.json", output)
                self.assertTrue((output / generator.STAGE_FILES["05"]).exists())
                generator.sabotage_case(output, sabotage)
                generator.refresh_case_bindings(output)
                diagnostic = checker.check_generated_directory(output)
                self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
                self.assertEqual(diagnostic["failure_class"], "burden-cycle-reentry")

    def test_recomputed_repeated_padded_body_requires_shared_operation_decision(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        self.assertTrue(callable(getattr(generator, "refresh_case_bindings", None)), "binding refresh helper absent")
        with tempfile.TemporaryDirectory() as parent:
            output = Path(parent) / "case"
            generator.generate_case(VALID / "chain-b10-s3.json", output)
            stage04_path = output / generator.STAGE_FILES["04"]
            stage04 = json.loads(stage04_path.read_text(encoding="utf-8"))
            first, second = stage04["acts"][:2]
            second["semantic_payload"] = first["semantic_payload"] + " neutral filler " * 20
            second["semantic_body_sha256"] = library.canonical_sha256(second["semantic_payload"])
            second["normalized_evidence_sha256"] = first.get("normalized_evidence_sha256")
            stage04_path.write_bytes(library.canonical_bytes(stage04))
            generator.refresh_case_bindings(output)
            diagnostic = checker.check_generated_directory(output)
            self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
            self.assertEqual(diagnostic["failure_subcode"], "repeated-body-without-shared-decision")

    def test_repeated_normalized_body_with_shared_operation_proof_passes(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        with tempfile.TemporaryDirectory() as parent:
            parent_path = Path(parent)
            source = parent_path / "source-authorized.json"
            self._write_source_authorized_spec(
                VALID / "chain-b10-s3.json", source, library
            )
            output = parent_path / "case"
            generator.generate_case(source, output)
            self._shared_operation_case(output, generator, library, None)
            diagnostic = checker.check_generated_directory(output)
            self.assertEqual(diagnostic["exit_code"], 0, diagnostic)

    def test_shared_operation_authorization_rejects_fabricated_hash_and_relation(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        expected = {
            "fabricated": "shared-decision-authorization-missing",
            "wrong-hash": "shared-decision-authorization-hash-mismatch",
            "mismatched-relation": "shared-decision-relation-mismatch",
        }
        for mutation, subcode in expected.items():
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as parent:
                parent_path = Path(parent)
                source = parent_path / "source-authorized.json"
                self._write_source_authorized_spec(
                    VALID / "chain-b10-s3.json", source, library
                )
                output = parent_path / "case"
                generator.generate_case(source, output)
                self._shared_operation_case(output, generator, library, mutation)
                diagnostic = checker.check_generated_directory(output)
                self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
                self.assertEqual(diagnostic["earliest_stage"], "04", diagnostic)
                self.assertEqual(diagnostic["failure_class"], "operation-body-identity", diagnostic)
                self.assertEqual(diagnostic["failure_subcode"], subcode, diagnostic)

    def test_shared_operation_without_upstream_partition_authority_is_rejected(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        with tempfile.TemporaryDirectory() as parent:
            output = Path(parent) / "case"
            generator.generate_case(VALID / "chain-b10-s3.json", output)
            self._shared_operation_case(output, generator, library, None)
            diagnostic = checker.check_generated_directory(output)
            self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
            self.assertEqual(diagnostic["earliest_stage"], "03", diagnostic)
            self.assertEqual(diagnostic["failure_class"], "split-merge-conservation", diagnostic)
            self.assertEqual(
                diagnostic["failure_subcode"],
                "shared-operation-upstream-authority-missing",
                diagnostic,
            )

    def test_fabricated_free_form_merge_proof_is_rejected_at_stage02(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        with tempfile.TemporaryDirectory() as parent:
            parent_path = Path(parent)
            source = parent_path / "source-authorized.json"
            self._write_source_authorized_spec(
                VALID / "chain-b10-s3.json", source, library
            )
            output = parent_path / "case"
            generator.generate_case(source, output)
            stage02_path = output / generator.STAGE_FILES["02"]
            stage02 = json.loads(stage02_path.read_text(encoding="utf-8"))
            stage02["hyperedges"][0]["incoming_pressure_ids"] = [
                row["pressure_id"] for row in stage02["pressures"][:2]
            ]
            stage02["hyperedges"][0]["decision"] = "merge-with-derivative-proof"
            stage02["hyperedges"][0]["derivative_proof"] = "fabricated-non-hash-text"
            stage02_path.write_bytes(library.canonical_bytes(stage02))
            generator.refresh_case_bindings(output)
            diagnostic = checker.check_generated_directory(output)
            self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
            self.assertEqual(diagnostic["earliest_stage"], "02", diagnostic)
            self.assertEqual(diagnostic["failure_class"], "split-merge-conservation", diagnostic)
            self.assertEqual(
                diagnostic["failure_subcode"],
                "partition-authorization-missing",
                diagnostic,
            )

    def test_canonical_shared_operation_authorization_passes(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        with tempfile.TemporaryDirectory() as parent:
            parent_path = Path(parent)
            source = parent_path / "source-authorized.json"
            self._write_source_authorized_spec(
                VALID / "chain-b10-s3.json", source, library
            )
            output = parent_path / "case"
            generator.generate_case(source, output)
            self._shared_operation_case(output, generator, library, None)
            diagnostic = checker.check_generated_directory(output)
            self.assertEqual(diagnostic["exit_code"], 0, diagnostic)

    def test_source_authority_hash_has_hand_frozen_golden_value(self) -> None:
        library = load_tool("topology_capacity_lib")
        authority = library.make_partition_authorization(
            authorization_key="golden-partition",
            relation_type="merge_same_function",
            pressure_ordinals=[2, 1],
            receiving_burden_ordinals=[1],
            owner_ordinal=1,
            evidence_identity="f" * 64,
        )
        self.assertEqual(
            authority["authorization_sha256"],
            "d0102bc238424ac1b35b555aaed1110e798e9d70771dcf95153307ef2d8049b4",
        )
        self.assertEqual(authority["pressure_ordinals"], [2, 1])

    def test_missing_or_wrong_source_partition_hash_rejects_at_stage01(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        for mutation in ("missing", "wrong"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as parent:
                output = Path(parent) / "case"
                generator.generate_case(VALID / "chain-b10-s3.json", output)
                source_path = output / generator.SPEC_FILE
                source = json.loads(source_path.read_text(encoding="utf-8"))
                if mutation == "missing":
                    source["partition_authorizations"][0].pop("authorization_sha256")
                else:
                    source["partition_authorizations"][0]["authorization_sha256"] = "0" * 64
                source_path.write_bytes(library.canonical_bytes(source))
                generator.refresh_case_bindings(output)
                diagnostic = checker.check_generated_directory(output)
                self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
                self.assertEqual(diagnostic["earliest_stage"], "01", diagnostic)
                self.assertEqual(diagnostic["failure_class"], "source-spec-parity", diagnostic)

    def test_unused_cross_substituted_and_act_mismatched_authorities_reject(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        with tempfile.TemporaryDirectory() as parent:
            parent_path = Path(parent)
            source = parent_path / "source-authorized.json"
            self._write_source_authorized_spec(
                VALID / "chain-b10-s3.json", source, library
            )
            unused = parent_path / "unused"
            generator.generate_case(source, unused)
            diagnostic = checker.check_generated_directory(unused)
            self.assertEqual(diagnostic["earliest_stage"], "03", diagnostic)
            self.assertEqual(
                diagnostic["failure_subcode"],
                "shared-operation-upstream-authority-unused",
                diagnostic,
            )
        for mutation, stage, subcode in (
            ("cross-upstream", "03", "shared-operation-upstream-authority-mismatch"),
            ("act-wrong-authorization", "04", "act-shared-authorization-mismatch"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as parent:
                parent_path = Path(parent)
                source = parent_path / "source-authorized.json"
                self._write_source_authorized_spec(
                    VALID / "chain-b10-s3.json", source, library
                )
                output = parent_path / "case"
                generator.generate_case(source, output)
                self._shared_operation_case(output, generator, library, mutation)
                diagnostic = checker.check_generated_directory(output)
                self.assertEqual(diagnostic["earliest_stage"], stage, diagnostic)
                self.assertEqual(diagnostic["failure_subcode"], subcode, diagnostic)

    def test_permutation_is_component_aware_and_truthfully_applicable(self) -> None:
        checker = load_tool("check_topology_capacity_properties")
        chain = checker.evaluate_metamorphic_relation(
            VALID / "chain-b10-s3.json", "permutation"
        )
        self.assertEqual(chain["exit_code"], 0, chain)
        self.assertEqual(chain["status"], "not-applicable", chain)
        self.assertEqual(
            chain["reason"],
            "fewer-than-two-independent-components",
            chain,
        )

        independent = checker.evaluate_metamorphic_relation(
            VALID / "unknown-route-hold.json", "permutation"
        )
        self.assertEqual(independent["exit_code"], 0, independent)
        self.assertEqual(independent["status"], "preserved", independent)
        self.assertTrue(independent.get("declaration_order_changed"), independent)
        self.assertNotEqual(
            independent.get("base_declaration_order"),
            independent.get("sibling_declaration_order"),
            independent,
        )
        self.assertEqual(
            independent["oracle_before"]["component_semantics"],
            independent["oracle_after"]["component_semantics"],
        )

        sabotage = checker.evaluate_metamorphic_relation(
            VALID / "unknown-route-hold.json", "permutation", sabotage=True
        )
        self.assertEqual(
            sabotage.get("failure_class"),
            "metamorphic-oracle-sabotage-detected",
            sabotage,
        )
        self.assertEqual(sabotage["diagnostic"]["earliest_stage"], "04", sabotage)
        self.assertEqual(
            sabotage["diagnostic"]["failure_class"],
            "burden-cycle-reentry",
            sabotage,
        )

    def test_metamorphic_suite_reports_applicable_and_not_applicable_counts(self) -> None:
        checker = load_tool("check_topology_capacity_properties")
        report = checker.run_metamorphic_suite(PROBE_SET)
        selected = len(json.loads(PROBE_SET.read_text(encoding="utf-8"))["specs"]) * len(
            POSITIVE_RELATIONS
        )
        self.assertEqual(report.get("selected_relation_rows"), selected, report)
        self.assertGreater(report.get("not_applicable_relations", 0), 0, report)
        self.assertEqual(
            report["executed_positive_relations"] + report["not_applicable_relations"],
            selected,
            report,
        )
        self.assertEqual(
            report["executed_sabotage_relations"],
            report["executed_positive_relations"],
            report,
        )
        self.assertEqual(len(report["applicability_matrix"]), selected, report)
        self.assertTrue(
            all(row.get("reason") for row in report["applicability_matrix"]), report
        )

    def test_arbitrary_unrecognized_route_is_hold_partial(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        with tempfile.TemporaryDirectory() as parent:
            parent_path = Path(parent)
            payload = json.loads((VALID / "independent-b1-s1.json").read_text(encoding="utf-8"))
            payload["dimensions"]["route_candidate_kinds"].append("renamed-unrecognized-route")
            spec_path = parent_path / "spec.json"
            spec_path.write_text(json.dumps(payload), encoding="utf-8")
            output = parent_path / "case"
            generator.generate_case(spec_path, output)
            stage03 = json.loads((output / generator.STAGE_FILES["03"]).read_text(encoding="utf-8"))
            route = next(row for row in stage03["routes"] if row["kind"] == "renamed-unrecognized-route")
            self.assertIn(route["disposition"], {"HOLD", "PARTIAL"})
            self.assertTrue(route.get("differentiator"))
            self.assertTrue(route.get("next_action"))

    def test_stage08_binds_every_sidecar_and_exact_public_output(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        with tempfile.TemporaryDirectory() as parent:
            output = Path(parent) / "case"
            generator.generate_case(VALID / "diamond-b4-s3.json", output)
            stage08 = json.loads((output / generator.STAGE_FILES["08"]).read_text(encoding="utf-8"))
            required = {
                "topology-spec.json",
                "topology-dimensions.json",
                "state-capsule.json",
                "field-witness.json",
                "stage-projection.json",
                "public-output.txt",
            }
            self.assertTrue(required.issubset(stage08.get("artifact_sha256", {})))

    def test_each_stage08_bound_artifact_tamper_is_rejected(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        checker = load_tool("check_topology_capacity_properties")
        expected = {
            "state-capsule.json": ("08", "sidecar-structure"),
            "field-witness.json": ("08", "sidecar-structure"),
            "stage-projection.json": ("08", "sidecar-structure"),
            "public-output.txt": ("07", "public-projection-parity"),
        }
        for name, (stage, failure_class) in expected.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as parent:
                output = Path(parent) / "case"
                generator.generate_case(VALID / "diamond-b4-s3.json", output)
                stage08 = json.loads((output / generator.STAGE_FILES["08"]).read_text(encoding="utf-8"))
                self.assertIn(name, stage08.get("artifact_sha256", {}), "artifact is not Stage08-bound")
                path = output / name
                path.write_bytes(path.read_bytes() + b"tamper")
                diagnostic = checker.check_generated_directory(output)
                self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
                self.assertEqual(diagnostic["earliest_stage"], stage, diagnostic)
                self.assertEqual(diagnostic["failure_class"], failure_class, diagnostic)

    def test_stage07_public_hash_and_reconstruction_resist_self_rehash(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        for mutation, expected_subcode in (
            ("stale-stage07", "public-output-hash-stale"),
            ("rehashed-truncated", "public-output-reconstruction-mismatch"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as parent:
                output = Path(parent) / "case"
                generator.generate_case(VALID / "diamond-b4-s3.json", output)
                public_path = output / generator.PUBLIC_OUTPUT_FILE
                public_path.write_bytes(b"{}\n")
                names = [generator.PUBLIC_OUTPUT_FILE]
                if mutation == "rehashed-truncated":
                    stage07_path = output / generator.STAGE_FILES["07"]
                    stage07 = json.loads(stage07_path.read_text(encoding="utf-8"))
                    stage07["public_output_sha256"] = hashlib.sha256(public_path.read_bytes()).hexdigest()
                    stage07_path.write_bytes(library.canonical_bytes(stage07))
                    names.append(generator.STAGE_FILES["07"])
                self._refresh_stage08_hashes(output, generator, library, tuple(names))
                diagnostic = checker.check_generated_directory(output)
                self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
                self.assertEqual(diagnostic["earliest_stage"], "07", diagnostic)
                self.assertEqual(diagnostic["failure_class"], "public-projection-parity", diagnostic)
                self.assertEqual(diagnostic["failure_subcode"], expected_subcode, diagnostic)

    def test_rehashed_sidecars_require_structural_parity_before_custody(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        mutations = {
            generator.STATE_FILE: ("terminal_states", {}, "state-capsule-parity"),
            generator.WITNESS_FILE: ("nar_rows", [], "field-witness-parity"),
            generator.PROJECTION_FILE: ("equal", False, "stage-projection-parity"),
        }
        for name, (field, value, expected_subcode) in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as parent:
                output = Path(parent) / "case"
                generator.generate_case(VALID / "diamond-b4-s3.json", output)
                path = output / name
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload[field] = value
                path.write_bytes(library.canonical_bytes(payload))
                self._refresh_stage08_hashes(output, generator, library, (name,))
                diagnostic = checker.check_generated_directory(output)
                self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
                self.assertEqual(diagnostic["earliest_stage"], "08", diagnostic)
                self.assertEqual(diagnostic["failure_class"], "sidecar-structure", diagnostic)
                self.assertEqual(diagnostic["failure_subcode"], expected_subcode, diagnostic)

    def test_cycle_fields_are_exactly_bound_to_source_spec(self) -> None:
        generator = load_tool("generate_topology_capacity_cases")
        library = load_tool("topology_capacity_lib")
        checker = load_tool("check_topology_capacity_properties")
        for mutation in ("depth", "event", "burden", "order"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as parent:
                output = Path(parent) / "case"
                source = VALID / ("generated-chain.json" if mutation in {"depth", "event"} else "diamond-b4-s3.json")
                generator.generate_case(source, output)
                stage_paths = {number: output / generator.STAGE_FILES[number] for number in ("03", "04", "05")}
                stages = {number: json.loads(path.read_text(encoding="utf-8")) for number, path in stage_paths.items()}
                if mutation == "depth":
                    generated = [row for row in stages["05"]["burden_cycles"] if row["origin"] == "B_MRP"]
                    target = generated[-1]
                    baseline = next(row for row in stages["05"]["burden_cycles"] if row["origin"] == "B_LA")
                    target["parent_cycle_id"] = baseline["cycle_id"]
                    target["generation_depth"] = 1
                    cycle03 = next(row for row in stages["03"]["burden_cycles"] if row["cycle_id"] == target["cycle_id"])
                    cycle03["parent_cycle_id"] = baseline["cycle_id"]
                    cycle03["generation_depth"] = 1
                    lifecycle = next(row for row in stages["05"]["lifecycle"] if row["burden_id"] == target["burden_id"])
                    lifecycle["parent_id"] = baseline["burden_id"]
                    lifecycle["generation_depth"] = 1
                elif mutation == "event":
                    target03 = next(row for row in stages["03"]["burden_cycles"] if row["origin"] == "B_MRP")
                    target04 = next(row for row in stages["04"]["burden_cycles"] if row["cycle_id"] == target03["cycle_id"])
                    target03["route_event_id"] = stages["05"]["event_ids"][-1]
                    target04["execution_event_id"] = stages["05"]["event_ids"][0]
                elif mutation == "burden":
                    left, right = stages["05"]["burden_cycles"][:2]
                    left_id, right_id = left["burden_id"], right["burden_id"]
                    for number in ("03", "04", "05"):
                        rows = stages[number]["burden_cycles"]
                        next(row for row in rows if row["cycle_id"] == left["cycle_id"])["burden_id"] = right_id
                        next(row for row in rows if row["cycle_id"] == right["cycle_id"])["burden_id"] = left_id
                    for row in stages["05"]["lifecycle"]:
                        if row["cycle_id"] == left["cycle_id"]:
                            row["burden_id"] = right_id
                        elif row["cycle_id"] == right["cycle_id"]:
                            row["burden_id"] = left_id
                else:
                    for number in ("03", "04", "05"):
                        stages[number]["burden_cycles"].reverse()
                    stages["05"]["lifecycle"].reverse()
                for number, path in stage_paths.items():
                    path.write_bytes(library.canonical_bytes(stages[number]))
                generator.refresh_case_bindings(output)
                diagnostic = checker.check_generated_directory(output)
                self.assertEqual(diagnostic["exit_code"], 1, diagnostic)
                self.assertEqual(diagnostic["earliest_stage"], "03", diagnostic)
                self.assertEqual(diagnostic["failure_class"], "burden-cycle-reentry", diagnostic)

    def test_full_matrix_is_distinct_and_reports_resource_telemetry(self) -> None:
        checker = load_tool("check_topology_capacity_properties")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = checker.main(["--full-matrix"])
        self.assertEqual(code, 0)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report.get("mode"), "full-matrix")
        self.assertGreater(report.get("matrix_cases", 0), 14)
        telemetry = report.get("resource_telemetry", {})
        self.assertGreater(telemetry.get("generated_bytes", 0), 0)
        self.assertGreaterEqual(telemetry.get("peak_traced_bytes", 0), 0)
        self.assertIn("telemetry_only", telemetry)

    def test_metamorphic_oracles_pin_right_reason(self) -> None:
        checker = load_tool("check_topology_capacity_properties")
        report = checker.run_metamorphic_suite(VALID / "mixed-b10-s6.json")
        self.assertEqual(report["exit_code"], 0, report)
        names = {row["name"] for row in report["relations"]}
        self.assertTrue(
            {
                "alpha-rename",
                "split-conservation",
                "merge-with-proof",
                "irrelevant-filler",
                "payload-length",
                "valid-hold",
                "generated-child",
                "preempt-resultant",
                "delete-owner",
                "delete-act",
                "delete-reread",
                "delete-nar",
                "delete-projection-join",
            }.issubset(names)
        )
        self.assertEqual(report["not_applicable_relations"], 1, report)
        self.assertEqual(
            report["not_applicable_rows"][0]["relation"], "permutation", report
        )

    def test_floor_scanner_and_registry_taint_self_tests(self) -> None:
        floor = load_tool("check_no_fixed_topology_floors")
        taint = load_tool("check_case_registry_taint")
        self.assertEqual(floor.scan_repository(ROOT)["exit_code"], 0)
        report = taint.run_taint_check(ROOT)
        self.assertEqual(report["exit_code"], 0, report)
        self.assertEqual(report["taint_variants"], 5)
        self.assertEqual(
            report["a15_surfaces"],
            ["expected topology", "dimension signature", "generator records", "property verdict"],
        )
        self.assertEqual(report["a14_checks"], 8)
        self.assertEqual(report["a14_rejections_before_manifest"], 8)

    def test_pure_library_has_no_orchestration_imports(self) -> None:
        source = (TOOLS / "topology_capacity_lib.py").read_text(encoding="utf-8")
        forbidden = ("subprocess", "socket", "requests", "urllib", "http", "openai")
        for token in forbidden:
            self.assertNotIn(f"import {token}", source)
            self.assertNotIn(f"from {token}", source)


if __name__ == "__main__":
    unittest.main()
