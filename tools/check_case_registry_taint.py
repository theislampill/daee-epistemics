#!/usr/bin/env python3
"""Prove A15 topology invariance and A14 registry-taint rejection at fake selection."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable

from check_topology_capacity_properties import check_generated_directory, dimension_signature
from generate_topology_capacity_cases import directory_digest, generate_case
from run_five_smoke_matrix import simulate_fake_cycle
from run_paired_cross_model_matrix import simulate_fake_paired_cycle
from smoke_matrix_registry import load_registry
from topology_capacity_lib import canonical_bytes, expected_dimension_manifest


# Explicitly quarantined inputs. They are test taint, never route or topology policy.
TOPIC_WORDS = ("secularism", "khaybar", "trinitarian", "lillard", "torah", "quran")
SCAN_PATHS = (
    "schema/topology-capacity-spec.schema.json",
    "tools/topology_capacity_lib.py",
    "tools/generate_topology_capacity_cases.py",
    "tools/check_topology_capacity_properties.py",
    "tests/topology-capacity/probe-set.json",
)


def _write(path: Path, value: Any) -> None:
    path.write_bytes(canonical_bytes(value))


def _a14_consumer_checks(root: Path, registry: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    consumers = (
        ("fake-five", "deterministic-fake", lambda path, prompt_root: simulate_fake_cycle(["ok"] * 5, registry_path=path, registry_root=prompt_root)),
        ("fake-paired", "deterministic-fake", lambda path, prompt_root: simulate_fake_paired_cycle(["ok"] * 5, ["ok"] * 5, registry_path=path, registry_root=prompt_root)),
    )
    registry_path = root / "tests" / "smoke-matrix" / "v0.4.6.0-wip-five-smoke.json"
    with tempfile.TemporaryDirectory(prefix="daee-a14-registry-taint-") as parent:
        temporary = Path(parent)
        mutations: list[tuple[str, Path, Path, str]] = []
        for dimension, mutate in (
            ("registry_id", lambda data: data["cases"][0].__setitem__("case_id", data["cases"][0]["case_id"] + "-tainted")),
            ("input_path", lambda data: data["cases"][0].__setitem__("input_path", data["cases"][1]["input_path"])),
            ("raw_sha256", lambda data: data["cases"][0].__setitem__("raw_sha256", "0" * 64)),
        ):
            changed = copy.deepcopy(registry)
            mutate(changed)
            changed_path = temporary / f"{dimension}.json"
            _write(changed_path, changed)
            mutations.append((dimension, changed_path, root, "registry_identity"))

        prompt_root = temporary / "prompt-root"
        for row in registry["cases"]:
            source = root / row["input_path"]
            target = prompt_root / row["input_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        prompt_path = prompt_root / registry["cases"][0]["input_path"]
        prompt = bytearray(prompt_path.read_bytes())
        prompt_bytes_before = len(prompt)
        prompt[0] = 33 if prompt[0] != 33 else 35
        prompt_path.write_bytes(prompt)
        prompt_bytes_after = prompt_path.stat().st_size
        if prompt_bytes_after != prompt_bytes_before:
            raise AssertionError("prompt-text taint mutation must preserve exact byte length")
        mutations.append(("prompt_text", registry_path, prompt_root, "registry_input_hash"))

        for dimension, selected_registry, prompt_source, expected_failure in mutations:
            for consumer_name, execution_kind, consumer in consumers:
                returned_manifest = False
                failure_class = None
                try:
                    consumer(selected_registry, prompt_source)
                    returned_manifest = True
                except ValueError as exc:
                    try:
                        failure_class = json.loads(str(exc)).get("failure_class")
                    except (json.JSONDecodeError, AttributeError):
                        failure_class = None
                rejected = not returned_manifest and failure_class == expected_failure
                check = {
                    "consumer": consumer_name,
                    "dimension": dimension,
                    "execution_kind": execution_kind,
                    "failure_class": failure_class,
                    "manifest_returned": returned_manifest,
                    "output_interpreted": False,
                    "rejected_before_manifest": rejected,
                }
                if dimension == "prompt_text":
                    check["mutation_bytes_before"] = prompt_bytes_before
                    check["mutation_bytes_after"] = prompt_bytes_after
                checks.append(check)
                if not rejected:
                    findings.append({"surface": "A14 route/owner/output selection", **check})
    return checks, findings


def run_taint_check(root: Path) -> dict[str, Any]:
    root = root.resolve()
    registry = load_registry(
        root / "tests" / "smoke-matrix" / "v0.4.6.0-wip-five-smoke.json",
        root,
    )
    registered_case_ids = tuple(row["case_id"] for row in registry["cases"])
    leaked: list[dict[str, Any]] = []
    needles = tuple(item.lower() for item in (*registered_case_ids, *TOPIC_WORDS))
    for relative in SCAN_PATHS:
        text = (root / relative).read_text(encoding="utf-8").lower()
        for needle in needles:
            if needle in text:
                leaked.append({"path": relative, "taint": needle})
    for path in sorted((root / "tests" / "topology-capacity" / "specs").rglob("*.json")):
        if path.name.endswith(".expectation.json"):
            continue
        text = path.read_text(encoding="utf-8").lower()
        for needle in needles:
            if needle in text:
                leaked.append({"path": path.relative_to(root).as_posix(), "taint": needle})
    base_path = root / "tests" / "topology-capacity" / "specs" / "valid" / "mixed-b10-s6.json"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    variants = []
    for case_id, topic in zip(registered_case_ids, TOPIC_WORDS):
        variant = copy.deepcopy(base)
        variant["taint"] = {"case_id": case_id, "topic_words": [topic, topic.upper()]}
        variants.append(variant)
    removed = copy.deepcopy(base)
    expected = expected_dimension_manifest(base)
    mismatch: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="daee-topology-taint-") as parent:
        parent_path = Path(parent)
        signatures = []
        directory_hashes = []
        for index, variant in enumerate([removed, *variants]):
            if expected_dimension_manifest(variant) != expected:
                mismatch.append({"variant": index, "surface": "expected topology"})
                continue
            spec_path = parent_path / f"spec-{index}.json"
            output = parent_path / f"case-{index}"
            _write(spec_path, variant)
            generate_case(spec_path, output)
            diagnostic = check_generated_directory(output)
            if diagnostic["exit_code"]:
                mismatch.append({"variant": index, "surface": "verdict", "diagnostic": diagnostic})
            signatures.append(dimension_signature(output))
            directory_hashes.append(directory_digest(output))
        if signatures and any(item != signatures[0] for item in signatures[1:]):
            mismatch.append({"surface": "dimension signature"})
        if directory_hashes and any(item != directory_hashes[0] for item in directory_hashes[1:]):
            mismatch.append({"surface": "generator records"})
    a14_checks, a14_findings = _a14_consumer_checks(root, registry)
    findings = leaked + mismatch + a14_findings
    return {
        "checker_id": "case-registry-taint",
        "status": "PASS" if not findings else "FAIL",
        "exit_code": 0 if not findings else 1,
        "taint_variants": len(variants),
        "a15_surfaces": ["expected topology", "dimension signature", "generator records", "property verdict"],
        "a14_dimensions": ["registry_id", "input_path", "raw_sha256", "prompt_text"],
        "a14_surfaces": ["route selection", "owner binding", "output selection"],
        "a14_consumers": ["fake-five", "fake-paired"],
        "a14_checks": len(a14_checks),
        "a14_rejections_before_manifest": sum(item["rejected_before_manifest"] for item in a14_checks),
        "same_length_prompt_proven": all(
            item["mutation_bytes_before"] == item["mutation_bytes_after"]
            for item in a14_checks
            if item["dimension"] == "prompt_text"
        ),
        "a14_results": a14_checks,
        "execution_boundary": {
            "fake_consumers_only": all(item["execution_kind"] == "deterministic-fake" for item in a14_checks),
            "live_runtime_invoked": any(item["execution_kind"] == "live" for item in a14_checks),
            "manifest_returned_on_taint": any(item["manifest_returned"] for item in a14_checks),
            "paired_output_interpreted": any(
                item["consumer"] == "fake-paired" and item["output_interpreted"]
                for item in a14_checks
            ),
        },
        "findings": findings,
        "proof": "changing or removing quarantined labels preserves expected topology, generated dimension signature, and property verdict",
        "a14_proof": "registry and prompt taint is rejected by fake five and paired consumers before route/owner/output selection",
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = run_taint_check(args.root)
    print(json.dumps(result, sort_keys=True))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
