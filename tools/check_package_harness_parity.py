#!/usr/bin/env python3
"""Classify package-faithful, harness-assisted, and unverified ambient evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path: sys.path.insert(0, str(TOOLS))
from check_runtime_context_delivery import (Failure as RuntimeContextFailure, compose_actual_fixture,
                                            _schema_errors, sha256_bytes, validate as validate_runtime_context,
                                            validate_expectation_contract)
from check_producer_checker_parity import DEFAULT_REGISTRY, validate_registry

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "package-harness-parity.schema.json"
FIXTURES = ROOT / "tests" / "package-harness-parity"
REQUIRED_KINDS = {"skill-root", "build-manifest", "cold-law-manifest", "module-map", "call-context", "prompt", "checker", "normalizer"}
ARTIFACT_OWNERS = {
    "skill-root": ("package", "SKILL.md"),
    "build-manifest": ("package", "build-manifest.json"),
    "cold-law-manifest": ("package", "cold-law-manifest.json"),
    "module-map": ("package", "compiled-module-map.json"),
    "call-context": ("run", "context.json"),
    "checker": ("repo", "tools/check_runtime_context_delivery.py"),
    "normalizer": ("repo", "tools/runtime_context_resolver.py"),
}
SCENARIO_FAILURES = {"package-harness-hash-mismatch", "membership-is-not-delivery", "harness-supplement-unbound", "lane-mislabel",
                     "unverified-host-ambient", "prompt-projection-hash-mismatch", "checker-hash-mismatch", "normalizer-hash-mismatch",
                     "runtime-context-invalid", "package-clause-unproven", "context-supplement-inventory-mismatch",
                     "lane-context-drift", "schema-invalid", "package-profile-invalid", "artifact-kind-duplicate",
                     "artifact-owner-mismatch", "delivery-proof-mode-mismatch"}


class Failure(ValueError):
    def __init__(self, cls: str, subcode: str, detail: str): super().__init__(detail); self.cls, self.subcode, self.detail = cls, subcode, detail
    def diagnostic(self) -> dict[str, Any]:
        return {"checker_id": "package-harness-parity", "status": "fail", "exit_category": "structural-rejection", "exit_code": 1,
                "failure_class": self.cls, "failure_subcode": self.subcode, "earliest_stage": "preflight",
                "downstream_invalidated": ["model-call", "promotion"], "detail": self.detail, "message": self.detail}


def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(root: Path) -> str:
    base = root.resolve(strict=True); out = hashlib.sha256()
    for path in sorted((p for p in base.rglob("*") if p.is_file()), key=lambda p: p.relative_to(base).as_posix()):
        rel = path.relative_to(base).as_posix().encode(); out.update(len(rel).to_bytes(4, "big")); out.update(rel); out.update(bytes.fromhex(sha(path)))
    return out.hexdigest()


def contained(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute(): raise Failure("package-harness-hash-mismatch", "path-not-relative", f"invalid path: {relative!r}")
    base = root.resolve(strict=True)
    try: path = (base / relative).resolve(strict=True); path.relative_to(base)
    except (OSError, ValueError) as exc: raise Failure("package-harness-hash-mismatch", "path-escape", f"path escapes scope: {relative}") from exc
    if not path.is_file(): raise Failure("package-harness-hash-mismatch", "artifact-not-file", f"not a file: {relative}")
    return path


def schema_errors(record: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return _schema_errors(record, schema, schema)


def validate(record: dict[str, Any], package_root: Path, run_root: Path, repo_root: Path = ROOT) -> dict[str, Any]:
    errors = schema_errors(record)
    if errors:
        if any("package_profile" in item for item in errors):
            raise Failure("package-profile-invalid", "audit-full-profile", "; ".join(errors))
        subcode = "unknown-record-field" if any("unexpected property" in item for item in errors) else "package-harness-schema"
        raise Failure("schema-invalid", subcode, "; ".join(errors))
    if tree_sha(package_root) != record["package_tree_sha256"]:
        raise Failure("package-harness-hash-mismatch", "package-harness-hash-mismatch", "package tree bytes differ")
    roots = {"package": package_root, "run": run_root, "repo": repo_root}
    kinds: set[str] = set(); artifact_paths: dict[str, Path] = {}; artifact_rows: dict[str, dict[str, Any]] = {}
    for artifact in record["artifacts"]:
        kind, scope = artifact.get("kind"), artifact.get("scope")
        if kind not in REQUIRED_KINDS or scope not in roots: raise Failure("schema-invalid", "artifact-kind-scope", f"invalid artifact: {kind}/{scope}")
        if kind in kinds:
            raise Failure("artifact-kind-duplicate", "duplicate-artifact-kind", f"duplicate artifact kind: {kind}")
        expected_owner = ARTIFACT_OWNERS.get(kind)
        if expected_owner is not None and (scope, artifact.get("path")) != expected_owner:
            subcode = f"{kind}-path-substitution" if kind in {"checker", "normalizer"} else f"{kind}-owner-mismatch"
            raise Failure("artifact-owner-mismatch", subcode, f"artifact owner differs for {kind}: {scope}/{artifact.get('path')}")
        path = contained(roots[scope], artifact.get("path", "")); kinds.add(kind); artifact_paths[kind] = path; artifact_rows[kind] = artifact
        if sha(path) != artifact.get("sha256") or path.stat().st_size != artifact.get("byte_count"):
            cls = {"prompt": "prompt-projection-hash-mismatch", "checker": "checker-hash-mismatch", "normalizer": "normalizer-hash-mismatch"}.get(kind, "package-harness-hash-mismatch")
            subcode = {"prompt": "prompt-projection-drift", "checker": "checker-hash-mismatch", "normalizer": "normalizer-hash-mismatch"}.get(kind, "package-harness-hash-mismatch")
            raise Failure(cls, subcode, f"artifact hash/size differs: {artifact.get('path')}")
    missing = REQUIRED_KINDS - kinds
    if missing: raise Failure("package-harness-hash-mismatch", "required-artifact-missing", f"missing artifact kinds: {sorted(missing)}")

    try:
        context = json.loads(artifact_paths["call-context"].read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Failure("runtime-context-invalid", "empty-runtime-context", "call-context artifact is not valid JSON") from exc
    if not isinstance(context, dict) or context.get("schema") != "daee-runtime-call-context-v1":
        raise Failure("runtime-context-invalid", "empty-runtime-context", "call-context artifact is empty or nonconforming")
    try:
        context_result = validate_runtime_context(context, package_root, run_root)
    except RuntimeContextFailure as exc:
        subcode = "nonconforming-context-prompt" if exc.failure_class in {"prompt-hash-mismatch", "undeclared-prompt-envelope", "selected-component-not-delivered"} else f"runtime-context:{exc.subcode}"
        raise Failure("runtime-context-invalid", subcode, f"runtime context failed: {exc.failure_class}/{exc.subcode}: {exc.detail}") from exc
    prompt_row = artifact_rows["prompt"]
    if prompt_row["scope"] != "run" or prompt_row["path"] != context["prompt"]["path"] or prompt_row["sha256"] != context["prompt"]["sha256"]:
        raise Failure("runtime-context-invalid", "nonconforming-context-prompt", "parity prompt artifact does not equal context prompt projection")
    if context["runtime"]["package_sha256"] != record["package_tree_sha256"]:
        raise Failure("package-harness-hash-mismatch", "context-package-mismatch", "context and parity record bind different package trees")

    registry_path = DEFAULT_REGISTRY
    if sha(registry_path) != record["producer_registry_sha256"]:
        raise Failure("package-clause-unproven", "producer-registry-hash-mismatch", "producer registry hash differs")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    try: validate_registry(registry)
    except Exception as exc:
        raise Failure("package-clause-unproven", "producer-registry-invalid", str(exc)) from exc
    clause_rows = {row.get("clause_id"): row for row in registry["clauses"] if isinstance(row, dict)}
    context_components = {row["component_id"]: row for row in context["components"]}
    visible_ids = record["model_visible_clause_ids"]
    if len(visible_ids) != len(set(visible_ids)):
        raise Failure("package-clause-unproven", "duplicate-model-visible-clause", "model-visible clause IDs must be unique")
    for clause_id in visible_ids:
        clause = clause_rows.get(clause_id)
        if not clause or clause.get("class") != "canonical_semantic_law":
            raise Failure("package-clause-unproven", "package-clause-unproven", f"model-visible DAEE clause is not canonical package law: {clause_id}")
        projection = clause["delivery_projection"]; component = context_components.get(projection["component_id"])
        if component is None or component.get("sha256") != projection["component_sha256"] or component.get("delivery") == "not-delivered":
            raise Failure("package-clause-unproven", "package-clause-unproven", f"clause projection is not delivered from bound package: {clause_id}")
    projected_live = {row["clause_id"] for row in registry["clauses"] if row.get("class") == "canonical_semantic_law" and row.get("delivery_projection", {}).get("component_id") in context_components}
    if projected_live != set(visible_ids):
        raise Failure("package-clause-unproven", "model-visible-clause-inventory-mismatch", "record does not exhaustively inventory package clause projections visible in context")

    supplements = record["harness_supplements"]
    context_supplements = {row["component_id"]: row for row in context["components"] if row.get("kind") == "harness-supplement"}
    record_supplements = {row.get("supplement_id"): row for row in supplements}
    if len(record_supplements) != len(supplements) or set(record_supplements) != set(context_supplements):
        if record["classification"] == "harness-assisted":
            raise Failure("harness-supplement-unbound", "harness-supplement-not-enumerated",
                          "harness-assisted record does not enumerate exact validated context supplements")
        raise Failure("context-supplement-inventory-mismatch", "context-supplement-omit-and-relabel",
                      "parity supplement inventory differs from validated context harness components")
    for item in supplements:
        path = contained(run_root, item.get("path", ""))
        if sha(path) != item.get("sha256") or path.stat().st_size != item.get("byte_count"):
            raise Failure("harness-supplement-unbound", item.get("supplement_id", "unknown"), "supplement bytes are not exactly bound")
        if item.get("claimed_package_bound"):
            raise Failure("lane-mislabel", item.get("supplement_id", "unknown"), "harness supplement cannot be relabeled package-bound")
        context_component = context_components.get(item.get("supplement_id"))
        if (context_component is None or context_component.get("sha256") != item.get("sha256")
                or context_component.get("byte_count") != item.get("byte_count")
                or context_component.get("source_path") != f"run://{item.get('path')}"
                or context_component.get("kind") != "harness-supplement"):
            raise Failure("harness-supplement-unbound", item.get("supplement_id", "unknown"), "supplement is not model-visible in validated context")

    lane, proof = record["classification"], record["delivery_proof"]
    context_lane, runtime_lane = context["proof_mode"], context["runtime"]["evidence_lane"]
    if proof == "opaque-ambient" or lane == "unverified-host-ambient":
        raise Failure("unverified-host-ambient", "opaque-host-ambient", "host ambient context has no exact receipt")
    if lane == "package-faithful" and supplements:
        raise Failure("lane-mislabel", "supplement-relabeled-package-bound", "package-faithful lane contains harness supplements")
    if lane != context_lane or lane != runtime_lane:
        raise Failure("lane-context-drift", "cross-lane-drift", "record classification, context proof mode, and runtime evidence lane differ")
    if proof == "membership-only": raise Failure("membership-is-not-delivery", "package-membership-only-claim", "package membership cannot prove model delivery")
    expected_delivery_proof = {
        "explicit-prompt-components": "exact-component-binding",
        "host-skill-context-receipt": "exact-host-receipt",
    }.get(context["runtime"]["delivery_mode"])
    if expected_delivery_proof is not None and proof != expected_delivery_proof:
        subcode = ("explicit-context-exact-host-receipt" if context["runtime"]["delivery_mode"] == "explicit-prompt-components"
                   else "host-context-exact-component-binding")
        raise Failure("delivery-proof-mode-mismatch", subcode,
                      f"delivery proof {proof!r} does not match validated context mode {context['runtime']['delivery_mode']!r}")
    if record["semantic_repair_count"]:
        raise Failure("lane-mislabel", "semantic-repair-present", "semantic repair is not package-faithful evidence")
    if lane == "harness-assisted" and not supplements:
        raise Failure("harness-supplement-unbound", "harness-supplement-not-enumerated", "harness-assisted lane must enumerate supplements")
    expected = "harness-assisted" if supplements else "package-faithful"
    if lane != expected: raise Failure("lane-mislabel", "classification-content-mismatch", "lane label does not match bound components")
    return {"status": "pass", "classification": lane, "artifact_count": len(record["artifacts"]), "supplement_count": len(supplements),
            "runtime_context_status": context_result["status"], "model_visible_clause_count": len(visible_ids)}


def scenario_result(path: Path) -> tuple[int, dict[str, Any]]:
    row = json.loads(path.read_text(encoding="utf-8"))
    cls = row.get("mutation")
    if row.get("expected_valid") is not True:
        if cls not in SCENARIO_FAILURES: return 1, Failure("schema-invalid", path.stem, "unknown fixture mutation").diagnostic()
        exp_path = path.with_suffix(".expectation.json")
        if not exp_path.is_file(): return 1, Failure("schema-invalid", path.stem, "same-stem expectation missing").diagnostic()
        exp = json.loads(exp_path.read_text(encoding="utf-8"))
        if exp.get("expected_failure_class") != cls: return 1, Failure("schema-invalid", path.stem, "expectation mismatch").diagnostic()
    assisted = row.get("kind") == "harness-assisted" or cls in {"harness-supplement-unbound", "lane-mislabel", "context-supplement-inventory-mismatch"}
    with tempfile.TemporaryDirectory(prefix="daee-parity-scenario-") as tmp:
        run = Path(tmp); (run / "context.json").write_text("{}\n", encoding="utf-8"); (run / "prompt.md").write_text("prompt\n", encoding="utf-8"); (run / "supplement.md").write_text("harness semantic guidance\n", encoding="utf-8")
        record = build_record(ROOT / "skill", run, assisted)
        if cls == "package-harness-hash-mismatch": record["package_tree_sha256"] = "f" * 64
        elif cls == "membership-is-not-delivery": record["delivery_proof"] = "membership-only"
        elif cls == "harness-supplement-unbound": record["harness_supplements"] = []
        elif cls == "lane-mislabel": record["classification"] = "package-faithful"
        elif cls == "unverified-host-ambient": record["classification"] = "unverified-host-ambient"; record["delivery_proof"] = "opaque-ambient"
        elif cls in {"prompt-projection-hash-mismatch", "checker-hash-mismatch", "normalizer-hash-mismatch"}:
            kind = {"prompt-projection-hash-mismatch": "prompt", "checker-hash-mismatch": "checker", "normalizer-hash-mismatch": "normalizer"}[cls]
            next(x for x in record["artifacts"] if x["kind"] == kind)["sha256"] = "f" * 64
        elif cls == "runtime-context-invalid":
            context_path = run / "context.json"
            if path.stem == "empty-runtime-context": context_path.write_text("{}\n", encoding="utf-8")
            else:
                context = json.loads(context_path.read_text(encoding="utf-8")); context["prompt"]["sha256"] = "f" * 64
                context_path.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            context_artifact = next(x for x in record["artifacts"] if x["kind"] == "call-context")
            context_artifact["sha256"] = sha(context_path); context_artifact["byte_count"] = context_path.stat().st_size
        elif cls == "package-clause-unproven": record["model_visible_clause_ids"].append("stage02.diagnostic-ir")
        elif cls == "context-supplement-inventory-mismatch":
            record["harness_supplements"] = []; record["classification"] = "package-faithful"
        elif cls == "lane-context-drift":
            context_path = run / "context.json"; context = json.loads(context_path.read_text(encoding="utf-8"))
            context["runtime"]["evidence_lane"] = "harness-assisted"
            context_path.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            artifact = next(x for x in record["artifacts"] if x["kind"] == "call-context")
            artifact["sha256"] = sha(context_path); artifact["byte_count"] = context_path.stat().st_size
        elif cls == "schema-invalid": record["review_unknown"] = True
        elif cls == "package-profile-invalid": record["package_profile"] = "audit-full"
        elif cls == "artifact-kind-duplicate": record["artifacts"].append(copy.deepcopy(record["artifacts"][0]))
        elif cls == "artifact-owner-mismatch":
            kind = "normalizer" if path.stem.startswith("normalizer") else "checker"
            target = next(x for x in record["artifacts"] if x["kind"] == kind)
            prompt = next(x for x in record["artifacts"] if x["kind"] == "prompt")
            target.update(scope=prompt["scope"], path=prompt["path"], sha256=prompt["sha256"], byte_count=prompt["byte_count"])
        elif cls == "delivery-proof-mode-mismatch":
            if path.stem == "explicit-context-exact-host-receipt":
                record["delivery_proof"] = "exact-host-receipt"
            else:
                context_path = run / "context.json"; context = json.loads(context_path.read_text(encoding="utf-8"))
                receipt_rows = []
                for component in context["components"]:
                    component["delivery"] = "host-receipt-bound"; component["prompt_start_byte"] = None; component["prompt_end_byte"] = None
                    receipt_rows.append({"component_id": component["component_id"], "sha256": component["sha256"]})
                prompt_path = run / context["prompt"]["path"]; prompt = b"DAEE host-receipt transport frame\n"; prompt_path.write_bytes(prompt)
                context["prompt"]["sha256"] = hashlib.sha256(prompt).hexdigest(); context["prompt"]["byte_count"] = len(prompt)
                context["budget_telemetry"]["effective_context_bytes"] = len(prompt)
                context["runtime"]["delivery_mode"] = "host-skill-context-receipt"
                context["host_receipt"] = {"opaque": False, "self_attested": False, "package_sha256": context["runtime"]["package_sha256"], "components": receipt_rows}
                context_path.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                for kind, artifact_path in (("call-context", context_path), ("prompt", prompt_path)):
                    artifact = next(x for x in record["artifacts"] if x["kind"] == kind)
                    artifact["sha256"] = sha(artifact_path); artifact["byte_count"] = artifact_path.stat().st_size
                record["delivery_proof"] = "exact-component-binding"
        try:
            result = validate(record, ROOT / "skill", run); return 0, result | {"scenario": row.get("scenario")}
        except Failure as exc:
            diagnostic = exc.diagnostic()
            if row.get("expected_valid") is not True:
                errors = validate_expectation_contract(exp, "package-harness-parity", 1, diagnostic, run, path.name)
                if errors: return 1, Failure("expectation-contract-failure", "a11-expectation-mismatch", "; ".join(errors)).diagnostic()
            return 1, diagnostic


def fixture_sweep() -> tuple[bool, int, int]:
    valid = sorted((FIXTURES / "valid").glob("*.json")); invalid = [p for p in sorted((FIXTURES / "invalid").glob("*.json")) if not p.name.endswith(".expectation.json")]
    ok = all(scenario_result(x)[0] == 0 for x in valid)
    for path in invalid:
        code, diag = scenario_result(path); exp = json.loads(path.with_suffix(".expectation.json").read_text(encoding="utf-8"))
        ok &= code == 1 and diag["failure_class"] == exp["expected_failure_class"]
    return ok, len(valid), len(invalid)


def build_record(package_root: Path, run_root: Path, assisted: bool) -> dict[str, Any]:
    context = compose_actual_fixture(package_root, run_root, stage="03")
    if assisted:
        supplement_path = run_root / "supplement.md"
        if not supplement_path.exists(): supplement_path.write_text("harness semantic guidance\n", encoding="utf-8")
        data = supplement_path.read_bytes(); component_id = "harness:diagnostic-guidance"; digest = hashlib.sha256(data).hexdigest()
        prompt_path = run_root / context["prompt"]["path"]; prompt = prompt_path.read_bytes()
        header = f"----- BEGIN DAEE COMPONENT: {component_id}; sha256={digest} -----\n".encode(); footer = f"\n----- END DAEE COMPONENT: {component_id} -----".encode()
        start = len(prompt) + len(header); prompt += header + data + footer + b"\n"; prompt_path.write_bytes(prompt)
        context["components"].append({"component_id": component_id, "kind": "harness-supplement", "source_path": "run://supplement.md",
                                      "source_slice": {"kind": "whole-file", "start": 0, "end": 0}, "sha256": digest, "byte_count": len(data),
                                      "delivery": "prompt-bound", "prompt_start_byte": start, "prompt_end_byte": start + len(data)})
        context["prompt"]["sha256"] = hashlib.sha256(prompt).hexdigest(); context["prompt"]["byte_count"] = len(prompt)
        context["budget_telemetry"]["effective_context_bytes"] = len(prompt); context["proof_mode"] = "harness-assisted"; context["runtime"]["evidence_lane"] = "harness-assisted"
    (run_root / "context.json").write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    mapping = [
        ("skill-root", "package", "SKILL.md"), ("build-manifest", "package", "build-manifest.json"),
        ("cold-law-manifest", "package", "cold-law-manifest.json"), ("module-map", "package", "compiled-module-map.json"),
        ("call-context", "run", "context.json"), ("prompt", "run", "prompt.md"),
        ("checker", "repo", "tools/check_runtime_context_delivery.py"), ("normalizer", "repo", "tools/runtime_context_resolver.py")]
    roots = {"package": package_root, "run": run_root, "repo": ROOT}; artifacts = []
    for kind, scope, rel in mapping:
        path = roots[scope] / rel; artifacts.append({"kind": kind, "scope": scope, "path": rel, "sha256": sha(path), "byte_count": path.stat().st_size})
    supplements = []
    if assisted:
        path = run_root / "supplement.md"; supplements = [{"supplement_id": "harness:diagnostic-guidance", "path": "supplement.md", "sha256": sha(path), "byte_count": path.stat().st_size, "semantic": True, "claimed_package_bound": False}]
    return {"schema": "daee-package-harness-parity-v1", "classification": "harness-assisted" if assisted else "package-faithful", "package_profile": "execution-mini",
            "package_tree_sha256": tree_sha(package_root), "producer_registry_sha256": sha(DEFAULT_REGISTRY),
            "model_visible_clause_ids": ["stage03.routing-precedence"], "artifacts": artifacts, "harness_supplements": supplements,
            "delivery_proof": "exact-component-binding", "semantic_repair_count": 0,
            "non_claims": ["structural parity is not semantic truth", "package shape is not model attention"]}


def self_test() -> int:
    checks: list[tuple[str, bool]] = []
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8")); checks.append(("schema identity", schema.get("title") == "DAEE package harness parity v1"))
    with tempfile.TemporaryDirectory(prefix="daee-parity-") as tmp:
        base = Path(tmp); faithful_run = base / "faithful"; assisted_run = base / "assisted"; faithful_run.mkdir(); assisted_run.mkdir()
        (assisted_run / "supplement.md").write_text("harness semantic guidance\n", encoding="utf-8")
        faithful = build_record(ROOT / "skill", faithful_run, False); assisted = build_record(ROOT / "skill", assisted_run, True)
        checks.append(("neighbor package-faithful record", validate(faithful, ROOT / "skill", faithful_run)["classification"] == "package-faithful"))
        checks.append(("neighbor harness-assisted record", validate(assisted, ROOT / "skill", assisted_run)["classification"] == "harness-assisted"))
        drift = copy.deepcopy(faithful); next(x for x in drift["artifacts"] if x["kind"] == "prompt")["sha256"] = "f" * 64
        try: validate(drift, ROOT / "skill", faithful_run); caught = False
        except Failure as exc: caught = exc.cls == "prompt-projection-hash-mismatch"
        checks.append(("prompt projection drift rejected", caught))
        relabel = copy.deepcopy(assisted); relabel["classification"] = "package-faithful"
        try: validate(relabel, ROOT / "skill", assisted_run); caught = False
        except Failure as exc: caught = exc.cls == "lane-mislabel"
        checks.append(("harness supplement cannot be relabeled", caught))
        membership = copy.deepcopy(faithful); membership["delivery_proof"] = "membership-only"
        try: validate(membership, ROOT / "skill", faithful_run); caught = False
        except Failure as exc: caught = exc.cls == "membership-is-not-delivery"
        checks.append(("package membership alone rejected", caught))
    fixture_ok, valid, invalid = fixture_sweep(); checks.append((f"fixture lattice ({valid} valid/{invalid} invalid)", fixture_ok))
    expectation = json.loads((FIXTURES / "invalid" / "package-membership-only-claim.expectation.json").read_text(encoding="utf-8"))
    _, diagnostic = scenario_result(FIXTURES / "invalid" / "package-membership-only-claim.json")
    with tempfile.TemporaryDirectory(prefix="daee-package-expectation-selftest-") as tmp:
        root = Path(tmp)
        checks.append(("A11 expectation baseline accepted", not validate_expectation_contract(expectation, "package-harness-parity", 1, diagnostic, root, "package-membership-only-claim.json")))
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
        caught = [bool(validate_expectation_contract(candidate, "package-harness-parity", 1, diagnostic, root, "package-membership-only-claim.json")) for candidate in sabotages]
        (root / "model-invocation.json").write_text("sabotage", encoding="utf-8")
        caught.append(bool(validate_expectation_contract(expectation, "package-harness-parity", 1, diagnostic, root, "package-membership-only-claim.json")))
        checks.append((f"A11 expectation field sabotage rejected ({len(caught)} variants)", all(caught)))
    ok = all(v for _, v in checks)
    for name, passed in checks: print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
    print(f"package/harness parity self-test: {'PASS' if ok else 'FAIL'} ({sum(v for _, v in checks)}/{len(checks)})")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true"); p.add_argument("--record", type=Path); p.add_argument("--package-root", type=Path); p.add_argument("--run-root", type=Path); p.add_argument("--scenario", type=Path); p.add_argument("--explain", action="store_true"); args = p.parse_args(argv)
    if args.self_test: return self_test()
    if args.scenario:
        code, diag = scenario_result(args.scenario); print(json.dumps(diag, sort_keys=True)); return code
    if args.record:
        if not args.package_root or not args.run_root: p.error("--record requires --package-root and --run-root")
        try: print(json.dumps(validate(json.loads(args.record.read_text(encoding="utf-8")), args.package_root, args.run_root), sort_keys=True)); return 0
        except Failure as exc: print(json.dumps(exc.diagnostic(), sort_keys=True)); return 1
    p.error("choose --self-test, --scenario, or --record")


if __name__ == "__main__": sys.exit(main())
