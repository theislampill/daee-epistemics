#!/usr/bin/env python3
"""Prove producer-visible law and checker obligations share canonical owners."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from check_runtime_context_delivery import validate_expectation_contract  # noqa: E402
from runtime_context_resolver import ResolutionError, resolve_context  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "tools" / "producer-contract-registry.json"
FIXTURES = ROOT / "tests" / "producer-checker-parity"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SEMANTIC_FIELDS = {"route", "route_targets", "burden", "burdens", "owner", "owners", "operation", "land", "delta", "graph", "terminal_state", "closure"}
TAINT = {"case_id", "case_name", "topic", "smoke_id", "expected_answer", "expected_topology"}
SCENARIO_FAILURES = {"canonical-package-clause-missing", "checker-only-semantic-law", "semantic-normalizer-invention",
                     "prompt-projection-hash-mismatch", "ambiguous-clause-ownership", "tainted-clause-selection",
                     "producer-obligation-not-visible", "unregistered-model-visible-clause",
                     "projection-section-hash-mismatch", "transitive-helper-omission", "non-prompt-anchor",
                     "scenario-schema-invalid"}


class ParityFailure(ValueError):
    def __init__(self, cls: str, clause: str, detail: str):
        super().__init__(detail); self.cls, self.clause, self.detail = cls, clause, detail
    def diagnostic(self) -> dict[str, Any]:
        return {"checker_id": "producer-checker-parity", "status": "fail", "exit_category": "structural-rejection", "exit_code": 1,
                "failure_class": self.cls, "failure_subcode": self.clause, "earliest_stage": "preflight",
                "downstream_invalidated": ["model-call", "promotion"], "detail": self.detail, "message": self.detail}


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_file(relative: str) -> Path:
    path = (ROOT / relative).resolve(strict=True)
    try: path.relative_to(ROOT.resolve(strict=True))
    except ValueError as exc: raise ParityFailure("canonical-package-clause-missing", relative, "registry path escapes repository") from exc
    return path


def _prompt_surface_inventory(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    encoded = text.encode("utf-8"); line_offsets = [0]
    for line in encoded.splitlines(keepends=True): line_offsets.append(line_offsets[-1] + len(line))

    def source(node: ast.AST) -> str:
        start = line_offsets[node.lineno - 1] + node.col_offset  # type: ignore[attr-defined]
        end = line_offsets[node.end_lineno - 1] + node.end_col_offset  # type: ignore[attr-defined]
        return encoded[start:end].decode("utf-8")

    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    bindings: dict[str, ast.AST] = {}
    for node in tree.body:
        targets: list[ast.AST] = []
        if isinstance(node, (ast.Assign, ast.AnnAssign)): targets = list(node.targets) if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name): bindings[target.id] = node
    inventory: dict[str, dict[str, Any]] = {}
    visible_text: dict[str, str] = {}
    roots = sorted(name for name in functions if name.endswith("_prompt") and name in {"stage_prompt", "release_prompt", "release_section_prompt", "release_section_expansion_prompt"})
    for root_name in roots:
            reachable_functions: set[str] = set(); pending = [root_name]
            while pending:
                name = pending.pop()
                if name in reachable_functions: continue
                reachable_functions.add(name)
                pending.extend(item.func.id for item in ast.walk(functions[name]) if isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id in functions)
            reachable_bindings: set[str] = set(); binding_pending = [item.id for name in reachable_functions for item in ast.walk(functions[name]) if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id in bindings]
            while binding_pending:
                name = binding_pending.pop()
                if name in reachable_bindings: continue
                reachable_bindings.add(name)
                binding_pending.extend(item.id for item in ast.walk(bindings[name]) if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id in bindings)
            nodes = [("function", name, functions[name]) for name in sorted(reachable_functions)] + [("binding", name, bindings[name]) for name in sorted(reachable_bindings)]
            sources = [(kind, name, source(node)) for kind, name, node in nodes]
            root_node = functions[root_name]; root_source = source(root_node)
            literals = [item.value for item in ast.walk(root_node) if isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value]
            transitive_literals = [item.value for _, _, node in nodes for item in ast.walk(node) if isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value]
            inventory[root_name] = {
                "source_sha256": hashlib.sha256(root_source.encode()).hexdigest(),
                "literal_count": len(literals),
                "literal_inventory_sha256": hashlib.sha256(json.dumps(literals, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(),
                "reachable_function_count": len(reachable_functions),
                "reachable_binding_count": len(reachable_bindings),
                "transitive_source_sha256": hashlib.sha256(json.dumps([(kind, name, hashlib.sha256(data.encode()).hexdigest()) for kind, name, data in sources], separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(),
                "rendered_literal_inventory_sha256": hashlib.sha256(json.dumps(transitive_literals, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(),
            }
            visible_text[root_name] = "\n".join(data for _, _, data in sources)
    return inventory, visible_text


def _validate_prompt_surfaces(registry: dict[str, Any], harness_path: Path, clause_ids: set[str]) -> None:
    declared_rows = registry.get("prompt_surfaces")
    if not isinstance(declared_rows, list):
        raise ParityFailure("unregistered-model-visible-clause", "prompt-surfaces", "prompt surface inventory is absent")
    declared: dict[str, dict[str, Any]] = {}
    referenced: set[str] = set()
    for row in declared_rows:
        name = row.get("function") if isinstance(row, dict) else None
        if not isinstance(name, str) or name in declared:
            raise ParityFailure("unregistered-model-visible-clause", str(name), "prompt surface identity is missing or duplicated")
        clauses = row.get("clause_ids")
        if not isinstance(clauses, list) or not clauses or any(item not in clause_ids for item in clauses):
            raise ParityFailure("unregistered-model-visible-clause", name, "prompt surface has an absent or unknown clause projection")
        referenced.update(clauses)
        declared[name] = row
    actual, visible_text = _prompt_surface_inventory(harness_path)
    if set(declared) != set(actual):
        raise ParityFailure("unregistered-model-visible-clause", "prompt-surfaces", "prompt constructor inventory differs from the registry")
    for name, observed in actual.items():
        row = declared[name]
        mismatched = {key for key, value in observed.items() if row.get(key) != value}
        if mismatched:
            transitive = {"reachable_function_count", "reachable_binding_count", "transitive_source_sha256", "rendered_literal_inventory_sha256"}
            failure_class = "transitive-helper-omission" if mismatched & transitive else "unregistered-model-visible-clause"
            raise ParityFailure(failure_class, name, f"prompt source or transitive inventory drifted: {sorted(mismatched)}")
    visible = {row["clause_id"] for row in registry["clauses"] if row.get("class") in {"canonical_semantic_law", "transport_adapter"}}
    if referenced != visible:
        raise ParityFailure("unregistered-model-visible-clause", "prompt-surfaces", "model-visible clause inventory is not exhaustive")
    for clause in registry["clauses"]:
        if clause.get("delivery_projection", {}).get("visible_before_call") is not True:
            continue
        anchor = clause.get("harness_anchor")
        observed_surfaces = sorted(name for name, rendered in visible_text.items() if isinstance(anchor, str) and anchor in rendered)
        if not observed_surfaces:
            raise ParityFailure("non-prompt-anchor", clause.get("clause_id", "<missing>"), "registered clause anchor is outside all model-visible prompt closures")
        if clause.get("visible_surfaces") != observed_surfaces:
            raise ParityFailure("transitive-helper-omission", clause.get("clause_id", "<missing>"), "clause visible-surface projection differs from rendered/transitive prompt inventory")
    for surface_name, surface in declared.items():
        expected_clauses = sorted(clause["clause_id"] for clause in registry["clauses"] if surface_name in clause.get("visible_surfaces", []))
        if sorted(surface.get("clause_ids", [])) != expected_clauses:
            raise ParityFailure("transitive-helper-omission", surface_name, "prompt surface clause IDs differ from exact visible anchor inventory")


def validate_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema") != "daee-producer-contract-registry-v1" or not isinstance(registry.get("clauses"), list):
        raise ParityFailure("schema-invalid", "registry", "wrong registry schema or clauses type")
    harness = registry.get("harness_source", {})
    harness_path = repo_file(harness.get("path", ""))
    if file_sha(harness_path) != harness.get("sha256"):
        raise ParityFailure("prompt-projection-hash-mismatch", "harness-source", "staged harness source hash drifted")
    ids: set[str] = set(); owner_keys: set[tuple[str, str]] = set(); counts = {"canonical": 0, "harness": 0, "custody": 0}
    for row in registry["clauses"]:
        clause = row.get("clause_id") if isinstance(row, dict) else None
        if not isinstance(clause, str) or not clause or clause in ids:
            raise ParityFailure("ambiguous-clause-ownership", str(clause), "missing or duplicate stable clause id")
        ids.add(clause)
    _validate_prompt_surfaces(registry, harness_path, ids)
    ids.clear()
    for row in registry["clauses"]:
        clause = row.get("clause_id", "<missing>")
        if clause in ids:
            raise ParityFailure("ambiguous-clause-ownership", clause, "duplicate stable clause id")
        ids.add(clause)
        checker = row.get("checker", {})
        checker_path = repo_file(checker.get("path", ""))
        if file_sha(checker_path) != checker.get("sha256"):
            raise ParityFailure("checker-only-semantic-law", clause, "checker source hash drifted from registry")
        normalizer = row.get("normalizer", {})
        if SEMANTIC_FIELDS.intersection(normalizer.get("semantic_fields", [])):
            raise ParityFailure("semantic-normalizer-invention", clause, "answer normalizer may not create semantic state")
        if TAINT.intersection(row.get("selection_inputs", [])):
            raise ParityFailure("tainted-clause-selection", clause, "case/topic/answer input used to select clause")
        cls = row.get("class")
        projection = row.get("delivery_projection", {})
        if cls == "canonical_semantic_law":
            source, generated = row.get("canonical_owner"), row.get("generated_owner")
            if not isinstance(source, dict) or not isinstance(generated, dict) or generated.get("package_member") is not True:
                raise ParityFailure("canonical-package-clause-missing", clause, "canonical law lacks atomics/generated package owners")
            source_path, generated_path = repo_file(source.get("path", "")), repo_file(generated.get("path", ""))
            if file_sha(source_path) != source.get("sha256") or source.get("anchor") not in source_path.read_text(encoding="utf-8"):
                raise ParityFailure("canonical-package-clause-missing", clause, "canonical atomics owner/hash/anchor mismatch")
            if file_sha(generated_path) != generated.get("sha256") or generated.get("anchor") not in generated_path.read_text(encoding="utf-8"):
                raise ParityFailure("canonical-package-clause-missing", clause, "generated package owner/hash/anchor mismatch")
            owner_key = (source["path"], source["anchor"])
            if owner_key in owner_keys:
                raise ParityFailure("ambiguous-clause-ownership", clause, "two clauses claim the same canonical anchor")
            owner_keys.add(owner_key)
            selection = row.get("resolver_selection")
            if not isinstance(selection, dict) or not isinstance(selection.get("validated_state"), dict):
                raise ParityFailure("prompt-projection-hash-mismatch", clause, "canonical projection lacks resolver selection inputs")
            try:
                resolved = resolve_context(ROOT / "skill", str(selection.get("stage", "")), selection["validated_state"], b"{}")
            except (OSError, ResolutionError) as exc:
                raise ParityFailure("prompt-projection-hash-mismatch", clause, f"resolver could not reproduce projection: {exc}") from exc
            components = {item["component_id"]: item for item in resolved.get("components", [])}
            component = components.get(projection.get("component_id"))
            if resolved.get("status") != "selected" or component is None or component.get("sha256") != projection.get("component_sha256") or projection.get("delivery") != "prompt-bound":
                mismatch_class = "projection-section-hash-mismatch" if str(projection.get("component_id", "")).startswith("owner:") else "prompt-projection-hash-mismatch"
                raise ParityFailure(mismatch_class, clause, "prompt projection does not match exact resolver component bytes")
            alternate_projections = row.get("alternate_delivery_projections", [])
            if not isinstance(alternate_projections, list):
                raise ParityFailure("schema-invalid", clause, "alternate delivery projections must be an array")
            alternate_ids: set[str] = set()
            for alternate in alternate_projections:
                required = {
                    "component_id", "component_sha256", "delivery", "visible_before_call",
                    "anchor", "resolver_selection",
                }
                if not isinstance(alternate, dict) or set(alternate) != required:
                    raise ParityFailure("schema-invalid", clause, "alternate delivery projection shape is not closed")
                alternate_id = alternate.get("component_id")
                if not isinstance(alternate_id, str) or alternate_id in alternate_ids or alternate_id == projection.get("component_id"):
                    raise ParityFailure("ambiguous-clause-ownership", clause, "alternate delivery component is absent or duplicated")
                alternate_ids.add(alternate_id)
                alternate_selection = alternate["resolver_selection"]
                if not isinstance(alternate_selection, dict) or set(alternate_selection) != {"stage", "validated_state"} or not isinstance(alternate_selection.get("validated_state"), dict):
                    raise ParityFailure("schema-invalid", clause, "alternate resolver selection shape is invalid")
                alternate_stage = str(alternate_selection.get("stage", ""))
                try:
                    alternate_resolved = resolve_context(
                        ROOT / "skill",
                        alternate_stage,
                        alternate_selection["validated_state"],
                        None if alternate_stage == "01" else b"{}",
                        raw_input=b"registry-owned-stage01-input" if alternate_stage == "01" else None,
                    )
                except (OSError, ResolutionError) as exc:
                    raise ParityFailure("prompt-projection-hash-mismatch", clause, f"alternate resolver projection failed: {exc}") from exc
                alternate_component = next(
                    (item for item in alternate_resolved.get("components", []) if item.get("component_id") == alternate_id),
                    None,
                )
                if (
                    alternate_resolved.get("status") != "selected"
                    or alternate_component is None
                    or alternate_component.get("sha256") != alternate.get("component_sha256")
                    or alternate.get("delivery") != "prompt-bound"
                    or alternate.get("visible_before_call") is not True
                    or not isinstance(alternate.get("anchor"), str)
                    or alternate["anchor"].encode("utf-8") not in alternate_component.get("bytes", b"")
                ):
                    raise ParityFailure("prompt-projection-hash-mismatch", clause, "alternate prompt projection does not match exact resolver component bytes")
            if checker.get("obligation") == "pre-producer-semantic" and projection.get("visible_before_call") is not True:
                raise ParityFailure("producer-obligation-not-visible", clause, "checker semantic obligation was not visible before call")
            if row.get("proof_class") != "package-faithful":
                raise ParityFailure("canonical-package-clause-missing", clause, "canonical package law has wrong proof class")
            counts["canonical"] += 1
        elif cls == "transport_adapter":
            if projection.get("component_sha256") != harness.get("sha256"):
                raise ParityFailure("prompt-projection-hash-mismatch", clause, "transport projection does not bind exact harness source bytes")
            if projection.get("visible_before_call") is not True or row.get("proof_class") != "harness-assisted":
                raise ParityFailure("producer-obligation-not-visible", clause, "transport adapter classification is inconsistent")
            counts["harness"] += 1
        elif cls == "instrumentation_only":
            if projection.get("component_sha256") != harness.get("sha256"):
                raise ParityFailure("prompt-projection-hash-mismatch", clause, "instrumentation projection does not bind exact harness source bytes")
            if projection.get("visible_before_call") is not False or not str(checker.get("obligation", "")).startswith("post-producer"):
                raise ParityFailure("checker-only-semantic-law", clause, "instrumentation must be post-producer/non-semantic")
            counts["custody"] += 1
        else:
            raise ParityFailure("schema-invalid", clause, f"unknown clause class: {cls}")
    return {"status": "pass", "clauses": len(ids), **counts}


def scenario_result(path: Path) -> tuple[int, dict[str, Any]]:
    row = json.loads(path.read_text(encoding="utf-8"))
    common = {"schema", "scenario", "expected_valid"}
    expected_valid = row.get("expected_valid")
    allowed = common | ({"kind"} if expected_valid is True else {"mutation"} if expected_valid is False else set())
    required = allowed
    shape_errors: list[str] = []
    if row.get("schema") != "daee-producer-checker-scenario-v1": shape_errors.append("wrong canonical scenario schema")
    if not isinstance(row.get("scenario"), str) or not row.get("scenario", "").strip(): shape_errors.append("scenario identity missing")
    if not isinstance(expected_valid, bool): shape_errors.append("expected_valid must be boolean")
    missing = sorted(required - set(row)); unknown = sorted(set(row) - allowed)
    if missing: shape_errors.append(f"missing scenario fields: {missing}")
    if unknown: shape_errors.append(f"unknown scenario fields: {unknown}")
    if expected_valid is True and (not isinstance(row.get("kind"), str) or not row.get("kind", "").strip()): shape_errors.append("valid scenario kind missing")
    if expected_valid is False and (not isinstance(row.get("mutation"), str) or not row.get("mutation", "").strip()): shape_errors.append("invalid scenario mutation missing")
    if shape_errors:
        subcode = "wrong-scenario-schema" if row.get("schema") != "daee-producer-checker-scenario-v1" else "scenario-shape-invalid"
        diagnostic = ParityFailure("scenario-schema-invalid", subcode, "; ".join(shape_errors)).diagnostic()
        exp_path = path.with_suffix(".expectation.json")
        if expected_valid is False and exp_path.is_file():
            with tempfile.TemporaryDirectory(prefix="daee-producer-scenario-schema-") as tmp:
                errors = validate_expectation_contract(json.loads(exp_path.read_text(encoding="utf-8")), "producer-checker-parity", 1,
                                                       diagnostic, Path(tmp), path.name)
            if errors: return 1, ParityFailure("expectation-contract-mismatch", path.stem, "; ".join(errors)).diagnostic()
        return 1, diagnostic
    cls = row.get("mutation")
    if row.get("expected_valid") is not True:
        if cls not in SCENARIO_FAILURES: return 1, ParityFailure("schema-invalid", path.stem, "unknown fixture mutation").diagnostic()
        exp_path = path.with_suffix(".expectation.json")
        if not exp_path.is_file(): return 1, ParityFailure("schema-invalid", path.stem, "missing same-stem expectation").diagnostic()
        exp = json.loads(exp_path.read_text(encoding="utf-8"))
        if exp.get("expected_failure_class") != cls: return 1, ParityFailure("schema-invalid", path.stem, "expectation mismatch").diagnostic()
    registry = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    if cls == "canonical-package-clause-missing": registry["clauses"][0]["generated_owner"]["package_member"] = False
    elif cls == "checker-only-semantic-law": registry["clauses"][0]["checker"]["sha256"] = "f" * 64
    elif cls == "semantic-normalizer-invention": registry["clauses"][0]["normalizer"]["semantic_fields"] = ["route"]
    elif cls == "prompt-projection-hash-mismatch": registry["clauses"][0]["delivery_projection"]["component_sha256"] = "f" * 64
    elif cls == "ambiguous-clause-ownership": registry["clauses"].append(copy.deepcopy(registry["clauses"][0]))
    elif cls == "tainted-clause-selection": registry["clauses"][0]["selection_inputs"].append("case_id")
    elif cls == "producer-obligation-not-visible": registry["clauses"][0]["delivery_projection"]["visible_before_call"] = False
    elif cls == "unregistered-model-visible-clause": registry["prompt_surfaces"].pop()
    elif cls == "projection-section-hash-mismatch": registry["clauses"][3]["delivery_projection"]["component_sha256"] = registry["clauses"][3]["generated_owner"]["sha256"]
    elif cls == "transitive-helper-omission":
        registry["prompt_surfaces"][0]["transitive_source_sha256"] = "0" * 64
        registry["prompt_surfaces"][0]["reachable_function_count"] = 0
    elif cls == "non-prompt-anchor": registry["clauses"][0]["harness_anchor"] = "staged current-skill harness self-test: PASS"
    try:
        result = validate_registry(registry); return 0, result | {"scenario": row.get("scenario")}
    except ParityFailure as exc:
        diagnostic = exc.diagnostic()
        diagnostic["failure_subcode"] = path.stem
        exp_path = path.with_suffix(".expectation.json")
        if exp_path.is_file():
            with tempfile.TemporaryDirectory(prefix="daee-producer-expectation-") as tmp:
                errors = validate_expectation_contract(json.loads(exp_path.read_text(encoding="utf-8")), "producer-checker-parity", 1,
                                                       diagnostic, Path(tmp), path.name)
            if errors:
                return 1, ParityFailure("expectation-contract-mismatch", path.stem, "; ".join(errors)).diagnostic()
        return 1, diagnostic


def fixture_sweep() -> tuple[bool, int, int]:
    valid = sorted((FIXTURES / "valid").glob("*.json")); invalid = [p for p in sorted((FIXTURES / "invalid").glob("*.json")) if not p.name.endswith(".expectation.json")]
    ok = all(scenario_result(p)[0] == 0 for p in valid)
    for path in invalid:
        code, diag = scenario_result(path); exp = json.loads(path.with_suffix(".expectation.json").read_text(encoding="utf-8"))
        ok &= code == 1 and diag["failure_class"] == exp["expected_failure_class"]
    return ok, len(valid), len(invalid)


def self_test() -> int:
    registry = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8")); checks: list[tuple[str, bool]] = []
    try: live = validate_registry(registry); checks.append(("live registry binds current source/package/checkers", live["clauses"] >= 8))
    except ParityFailure as exc: print(json.dumps(exc.diagnostic(), sort_keys=True)); checks.append(("live registry binds current source/package/checkers", False))
    def drift_stage01_kernel_projection(candidate: dict[str, Any]) -> None:
        clause = next(row for row in candidate["clauses"] if row.get("clause_id") == "stage04.owner-act-execution")
        clause["alternate_delivery_projections"][0]["component_sha256"] = "f" * 64

    def drift_harness_projection(candidate: dict[str, Any], clause_id: str) -> None:
        clause = next(row for row in candidate["clauses"] if row.get("clause_id") == clause_id)
        clause["delivery_projection"]["component_sha256"] = "f" * 64

    mutations = [
        ("harness clause absent from package", lambda r: r["clauses"][0]["generated_owner"].update(package_member=False), "canonical-package-clause-missing"),
        ("checker-only secret law", lambda r: r["clauses"][0]["delivery_projection"].update(visible_before_call=False), "producer-obligation-not-visible"),
        ("normalizer semantic invention", lambda r: r["clauses"][0]["normalizer"].update(semantic_fields=["route"]), "semantic-normalizer-invention"),
        ("prompt projection drift", lambda r: r["clauses"][0]["delivery_projection"].update(component_sha256="f" * 64), "prompt-projection-hash-mismatch"),
        ("named case routing taint", lambda r: r["clauses"][0]["selection_inputs"].append("case_id"), "tainted-clause-selection"),
        ("unregistered prompt surface", lambda r: r["prompt_surfaces"].pop(), "unregistered-model-visible-clause"),
        ("owner section uses bundle hash", lambda r: r["clauses"][3]["delivery_projection"].update(component_sha256=r["clauses"][3]["generated_owner"]["sha256"]), "projection-section-hash-mismatch"),
        ("Stage01 kernel alternate projection drift", drift_stage01_kernel_projection, "prompt-projection-hash-mismatch"),
        ("transport adapter harness projection drift", lambda r: drift_harness_projection(r, "transport.json-only"), "prompt-projection-hash-mismatch"),
        ("instrumentation harness projection drift", lambda r: drift_harness_projection(r, "custody.raw-response-retention"), "prompt-projection-hash-mismatch"),
    ]
    for name, mutate, expected in mutations:
        candidate = copy.deepcopy(registry); mutate(candidate)
        try: validate_registry(candidate); caught = False
        except ParityFailure as exc: caught = exc.cls == expected
        checks.append((name, caught))
    fixture_ok, valid, invalid = fixture_sweep(); checks.append((f"fixture lattice ({valid} valid/{invalid} invalid)", fixture_ok))
    expectation_path = FIXTURES / "invalid" / "checker-only-clause.expectation.json"
    expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
    _, diagnostic = scenario_result(FIXTURES / "invalid" / "checker-only-clause.json")
    with tempfile.TemporaryDirectory(prefix="daee-producer-expectation-selftest-") as tmp:
        root = Path(tmp)
        checks.append(("A11 expectation baseline accepted", not validate_expectation_contract(expectation, "producer-checker-parity", 1, diagnostic, root, "checker-only-clause.json")))
        sabotages: list[dict[str, Any]] = []
        for key, value in (
            ("schema", "wrong"), ("kind", "wrong"), ("fixture", "wrong.json"),
            ("expected_checker_id", "wrong"), ("expected_exit_category", "wrong"), ("expected_exit_code", 9),
            ("expected_earliest_stage", "wrong"), ("expected_failure_class", "wrong"),
            ("expected_failure_subcode", "wrong"), ("expected_downstream_invalidated", ["wrong"]),
            ("required_diagnostic_markers", ["absent-marker"]), ("provenance", ""),
        ):
            candidate = copy.deepcopy(expectation); candidate[key] = value; sabotages.append(candidate)
        missing = copy.deepcopy(expectation); missing.pop("expected_checker_id"); sabotages.append(missing)
        unknown = copy.deepcopy(expectation); unknown["review_unknown"] = True; sabotages.append(unknown)
        caught = [bool(validate_expectation_contract(candidate, "producer-checker-parity", 1, diagnostic, root, "checker-only-clause.json")) for candidate in sabotages]
        (root / "model-invocation.json").write_text("sabotage", encoding="utf-8")
        caught.append(bool(validate_expectation_contract(expectation, "producer-checker-parity", 1, diagnostic, root, "checker-only-clause.json")))
        checks.append((f"A11 expectation field sabotage rejected ({len(caught)} variants)", all(caught)))
    ok = all(v for _, v in checks)
    for name, passed in checks: print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"producer/checker parity self-test: {'PASS' if ok else 'FAIL'} ({sum(v for _, v in checks)}/{len(checks)})")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true"); p.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY); p.add_argument("--scenario", type=Path); p.add_argument("--explain", action="store_true"); args = p.parse_args(argv)
    if args.self_test: return self_test()
    if args.scenario:
        code, diag = scenario_result(args.scenario); print(json.dumps(diag, sort_keys=True)); return code
    try: print(json.dumps(validate_registry(json.loads(args.registry.read_text(encoding="utf-8"))), sort_keys=True)); return 0
    except ParityFailure as exc: print(json.dumps(exc.diagnostic(), sort_keys=True)); return 1


if __name__ == "__main__": sys.exit(main())
