#!/usr/bin/env python3
"""Fixture anti-evasion mutation sweep — Plan 12 Phase 3 (Lane D) + Plan 13 Slice H.

Two independent mutation families live in this file:

1. TEXT-mutation family (original, Plan 12 Phase 3 Lane D): scripted structural
   removal mutations applied to Markdown `mrp-route-invariants` fixtures. See the
   ``terminal_mrp_collapse`` / ``witness_strip`` operators and ``sweep()`` below.
   Unchanged behavior; still exercised by ``--self-test``.

2. STAGE-RECORD mutation family (Plan 13, Slice H): a per-stage mutation sweep
   over ``staged-runtime-handshake-v1`` JSON records. Each operator takes a
   VALID staged record and returns a mutated record plus expected-failure
   metadata (stage, failure_class_hint, checker). This proves each stage
   checker fails FOR THE RIGHT REASON before any model spend. See
   ``STAGE_RECORD_OPERATORS`` / ``run_stage_record_sweep()`` below, and
   ``--sweep`` / ``--self-test`` (extended) for the CLI surface.

NEVER writes under tests/. Mutants go to a temp dir (default: a fresh tempdir).
Exit codes: 0 = every applied mutant rejected; 3 = at least one SURVIVOR (mutant
accepted by its owning checker) -> a FINDING, not a crash; 2 = usage/internal error.

Usage:
  python tools/gen_fixture_mutations.py --self-test
  python tools/gen_fixture_mutations.py [--emit-dir <dir outside tests/>]
  python tools/gen_fixture_mutations.py --sweep <valid-record.json> --out-dir <dir>
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_mid_reread_pressure as _mr  # for MRP_BLOCK_RE

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

FENCE_FW_RE = re.compile(r"```[^\n]*\n.*?field_witness.*?```", re.S)

# family valid-dir glob -> owning checker
FAMILY_DETECTORS = {
    "tests/mrp-route-invariants/valid/*.md": "check_mrp_route_invariants",
}


def terminal_mrp_collapse(text: str) -> str | None:
    blocks = list(_mr.MRP_BLOCK_RE.finditer(text))
    if len(blocks) < 2:
        return None
    out, last = [], 0
    for b in blocks[:-1]:
        out.append(text[last:b.start()])
        last = b.end()
    out.append(text[last:])
    return "".join(out)


def witness_strip(text: str) -> str | None:
    m = FENCE_FW_RE.search(text)
    if not m:
        return None
    return text[:m.start()] + text[m.end():]


OPERATORS = {
    "terminal-mrp-collapse": terminal_mrp_collapse,
    "witness-strip": witness_strip,
}


def _run_checker(detector: str, content: str, emit_dir: Path, tag: str) -> int:
    path = emit_dir / f"mut_{tag}.md"
    path.write_text(content, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / f"{detector}.py"), "--outputs", str(path)],
        capture_output=True,
    )
    return proc.returncode


def sweep(emit_dir: Path) -> tuple[list[dict], list[dict]]:
    """Return (applied_rows, skipped_rows). applied row verdict: 'rejected' | 'survivor'."""
    applied, skipped = [], []
    for family_glob, detector in FAMILY_DETECTORS.items():
        for src in sorted(glob.glob(str(ROOT / family_glob))):
            text = Path(src).read_text(encoding="utf-8")
            name = Path(src).name
            for op_name, op in OPERATORS.items():
                mutated = op(text)
                if mutated is None:
                    skipped.append({"fixture": name, "operator": op_name})
                    continue
                code = _run_checker(detector, mutated, emit_dir, f"{op_name}_{name}")
                applied.append({
                    "fixture": name, "operator": op_name,
                    "verdict": "rejected" if code != 0 else "survivor",
                })
    return applied, skipped


def _safe_emit_dir(raw: str | None) -> Path:
    if raw is None:
        return Path(tempfile.mkdtemp(prefix="daee_mut_"))
    p = Path(raw).resolve()
    tests_root = (ROOT / "tests").resolve()
    if tests_root == p or tests_root in p.parents:
        raise SystemExit(f"--emit-dir must not be under tests/: {p}")
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# STAGE-RECORD mutation family (Plan 13, Slice H)
# ---------------------------------------------------------------------------
#
# Each operator is a pure function: (record: dict) -> dict | None. Returning
# None means "not applicable to this record" (the caller skips it, mirroring
# the TEXT-mutation family's None-means-skip convention).
#
# Every operator carries metadata used to build the sweep manifest:
#   stage               : the stage id this mutation targets (or "cross-stage")
#   failure_class_hint  : a short, stable phrase describing the expected defect
#   checker             : "check_staged_runtime_handshake" (record-checkable)
#                         or "render-family" (needs a rendered artifact file;
#                         verified only at the record/schema level here)
#
# verification depth (see STAGE_RECORD_OPERATORS[*]["checker"]):
#   - "check_staged_runtime_handshake": the sweep invokes
#     tools/check_staged_runtime_handshake.py --records <mutated.json> via
#     subprocess and REQUIRES a nonzero exit (full rejection verification).
#   - "render-family": the owning checker validates a rendered Markdown
#     artifact (visible_governed_output_errors / mrp_route_invariants) that
#     this sweep does not render. These operators are verified at the record
#     level only: (a) the mutated record must differ from the source, and
#     (b) where mechanically checkable, the record must already be schema-
#     inconsistent (e.g. release_output pointing at a path whose on-disk text
#     no longer satisfies the shrink). Manifest entries for these operators
#     are marked expected_checker: "render-family" and are NOT claimed as
#     full checker-rejection evidence.


def _find_stage(record: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    stages = record.get("stages")
    if not isinstance(stages, list):
        return None
    for stage in stages:
        if isinstance(stage, dict) and stage.get("id") == stage_id:
            return stage
    return None


STAGE_REQUIRED_FIELDS: dict[str, str] = {
    "stage-01-intake": "input_digest",
    "stage-02-layer-a-diagnostic-ir": "burden_floor",
    "stage-03-routing-owner-gate": "route_targets",
    "stage-04-burden-execution-act": "act_rows",
    "stage-05-mrp-reread-terminal-state": "terminal_states",
    "stage-06-field-witness-nar": "field_witness_body_refs",
}


def op_delete_required_field(record: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    field = STAGE_REQUIRED_FIELDS.get(stage_id)
    if field is None:
        return None
    mutated = copy.deepcopy(record)
    stage = _find_stage(mutated, stage_id)
    if stage is None or field not in stage:
        return None
    del stage[field]
    return mutated


def op_corrupt_body_ref(record: dict[str, Any]) -> dict[str, Any] | None:
    """Inject owner/op pollution into a stage-04 body_ref token."""
    mutated = copy.deepcopy(record)
    stage04 = _find_stage(mutated, "stage-04-burden-execution-act")
    if stage04 is None:
        return None
    refs = stage04.get("act_body_refs")
    if not isinstance(refs, list) or not refs:
        return None
    polluted = f"source-status-repair.source-order::{refs[0]}"
    refs[0] = polluted
    rows = stage04.get("act_rows")
    if isinstance(rows, list) and rows:
        rows[0] = rows[0].replace(f"body_ref={_first_body_ref(rows[0])}", f"body_ref={polluted}")
    return mutated


def _first_body_ref(row: str) -> str:
    match = re.search(r"\bbody_ref=([^\s:⟧]+)", row)
    return match.group(1) if match else ""


def op_swap_owner_operation(record: dict[str, Any]) -> dict[str, Any] | None:
    """Swap owner_id <-> operation values in stage-03 owner_routes."""
    mutated = copy.deepcopy(record)
    stage03 = _find_stage(mutated, "stage-03-routing-owner-gate")
    if stage03 is None:
        return None
    routes = stage03.get("owner_routes")
    if not isinstance(routes, list) or not routes:
        return None
    changed = False
    for route in routes:
        if not isinstance(route, dict):
            continue
        owner_id = route.get("owner_id")
        operation = route.get("eligibility")
        if isinstance(owner_id, str) and isinstance(operation, str):
            route["owner_id"], route["eligibility"] = operation, owner_id
            changed = True
    return mutated if changed else None


def op_replace_controlled_delta_with_prose(record: dict[str, Any]) -> dict[str, Any] | None:
    """Replace a stage-06 NAR per_burden delta_result with free prose."""
    mutated = copy.deepcopy(record)
    stage06 = _find_stage(mutated, "stage-06-field-witness-nar")
    if stage06 is None:
        return None
    nar_details = stage06.get("normalized_activation_record_details")
    if not isinstance(nar_details, dict):
        return None
    per_burden = nar_details.get("per_burden")
    if not isinstance(per_burden, list) or not per_burden:
        return None
    changed = False
    for row in per_burden:
        if isinstance(row, dict) and "delta_result" in row:
            row["delta_result"] = (
                "this is just free-form prose describing what happened instead of a controlled delta token"
            )
            changed = True
    return mutated if changed else None


def op_drop_mrp_block(record: dict[str, Any]) -> dict[str, Any] | None:
    """Remove a stage-05 per_burden_reread entry while its burden stays landed."""
    mutated = copy.deepcopy(record)
    stage05 = _find_stage(mutated, "stage-05-mrp-reread-terminal-state")
    if stage05 is None:
        return None
    entries = stage05.get("per_burden_reread")
    if not isinstance(entries, list) or not entries:
        return None
    terminal_states = stage05.get("terminal_states")
    if not isinstance(terminal_states, dict) or len(terminal_states) < 2:
        return None
    dropped = entries.pop(0)
    if not entries:
        return None
    return mutated


def op_fake_no_new_resultant(record: dict[str, Any]) -> dict[str, Any] | None:
    """route_result_type -> no_new_resultant while unresolved burdens/live pressure remain."""
    mutated = copy.deepcopy(record)
    stage05 = _find_stage(mutated, "stage-05-mrp-reread-terminal-state")
    if stage05 is None:
        return None
    reread_state = stage05.get("reread_state")
    if not isinstance(reread_state, dict):
        reread_state = {}
        stage05["reread_state"] = reread_state
    reread_state["route_result_type"] = "no_new_resultant"
    reread_state["route"] = "STOP"
    stage05["unresolved_burdens"] = list(
        set(stage05.get("unresolved_burdens") or []) | {"B9"}
    )
    proof = stage05.get("no_new_resultant_proof")
    if isinstance(proof, dict):
        proof["proved"] = True
        proof["unresolved_burdens"] = []
    else:
        stage05["no_new_resultant_proof"] = True
    return mutated


def op_move_burden_bmrp_to_bla(record: dict[str, Any]) -> dict[str, Any] | None:
    """Relocate a generated (BMRP) burden into the baseline floor (BLA)."""
    mutated = copy.deepcopy(record)
    stage05 = _find_stage(mutated, "stage-05-mrp-reread-terminal-state")
    stage02 = _find_stage(mutated, "stage-02-layer-a-diagnostic-ir")
    if stage05 is None or stage02 is None:
        return None
    generated = stage05.get("generated_burdens")
    if not isinstance(generated, list) or not generated:
        return None
    generated_id = None
    for item in generated:
        if isinstance(item, dict):
            generated_id = item.get("id") or item.get("burden_id")
        elif isinstance(item, str):
            generated_id = item
        if generated_id:
            break
    if not generated_id:
        return None
    burden_floor = stage02.get("burden_floor")
    if not isinstance(burden_floor, list):
        return None
    if generated_id in burden_floor:
        return None
    burden_floor.append(generated_id)
    return mutated


def op_omit_generated_by(record: dict[str, Any]) -> dict[str, Any] | None:
    """Strip generation provenance (generated_by) from a stage-05 generated burden."""
    mutated = copy.deepcopy(record)
    stage05 = _find_stage(mutated, "stage-05-mrp-reread-terminal-state")
    if stage05 is None:
        return None
    generated = stage05.get("generated_burdens")
    if not isinstance(generated, list) or not generated:
        return None
    changed = False
    for item in generated:
        if isinstance(item, dict) and "generated_by" in item:
            del item["generated_by"]
            changed = True
    return mutated if changed else None


def op_remove_owner_activations_mirror(record: dict[str, Any]) -> dict[str, Any] | None:
    """Empty stage-06 owner_activations while ACT rows remain."""
    mutated = copy.deepcopy(record)
    stage06 = _find_stage(mutated, "stage-06-field-witness-nar")
    stage04 = _find_stage(mutated, "stage-04-burden-execution-act")
    if stage06 is None or stage04 is None:
        return None
    if not stage04.get("act_rows"):
        return None
    if not stage06.get("owner_activations"):
        return None
    stage06["owner_activations"] = []
    return mutated


def op_slim_public_while_sidecar_rich(record: dict[str, Any]) -> dict[str, Any] | None:
    """Stage-07: shrink public output text below structural minimum while sidecar stays rich.

    This mutation targets the rendered release_output Markdown, which this
    record-only sweep does not rewrite. It is a render-family mutation: the
    record itself is left schema-consistent (release_output still points at
    the real, rich artifact) but with a documented instruction for a render
    pass to shrink the text. We mark the record with a probe field so a
    render-stage tool can pick it up; the checker verification for this
    operator is manifest-only (see docstring at top of this section).
    """
    mutated = copy.deepcopy(record)
    stage07 = _find_stage(mutated, "stage-07-release-output")
    if stage07 is None:
        return None
    release_output = stage07.get("release_output")
    if not isinstance(release_output, dict):
        return None
    # Record-level probe: mark the mutation intent without fabricating a fake
    # artifact file (this sweep never writes under tests/, and inventing an
    # artifact path here would misrepresent what stage-07 rendering owns).
    mutated["_mutation_probe"] = {
        "operator": "slim-public-while-sidecar-rich",
        "target": "release_output.path rendered text",
        "instruction": (
            "shrink the rendered release_output text below the structural minimum "
            "(drop ACT rows / Land / MRP / field_witness sections) while sidecar "
            "fields (b5_full_ir_projection_sidecar, artifact_bindings) stay rich"
        ),
    }
    return mutated


def op_set_coverage_complete_despite_unresolved(record: dict[str, Any]) -> dict[str, Any] | None:
    """Force closure_claim=complete while stage-05 carries unresolved burdens."""
    mutated = copy.deepcopy(record)
    stage05 = _find_stage(mutated, "stage-05-mrp-reread-terminal-state")
    stage07 = _find_stage(mutated, "stage-07-release-output")
    if stage05 is None or stage07 is None:
        return None
    stage05["unresolved_burdens"] = list(set(stage05.get("unresolved_burdens") or []) | {"B9"})
    proof = stage05.get("no_new_resultant_proof")
    if isinstance(proof, dict):
        proof["proved"] = True
        proof["unresolved_burdens"] = []
    else:
        stage05["no_new_resultant_proof"] = True
    stage07["closure_claim"] = "complete"
    return mutated


def op_absolute_sidecar_path(record: dict[str, Any]) -> dict[str, Any] | None:
    """Stage-08/artifact path made absolute in a claimed proof_sidecars set."""
    mutated = copy.deepcopy(record)
    stage08 = _find_stage(mutated, "stage-08-verifier-sidecars")
    if stage08 is None:
        return None
    verifier_sidecars = stage08.get("verifier_sidecars")
    if not isinstance(verifier_sidecars, dict):
        verifier_sidecars = {}
        stage08["verifier_sidecars"] = verifier_sidecars
    verifier_sidecars["proof_sidecars"] = {
        "claimed": True,
        "paths": ["C:/Windows/System32/evil.json"],
    }
    return mutated


# Registry: operator name -> (stage id or "cross-stage", failure_class_hint, applier)
# applier signature is (record) -> mutated record | None. Stage-parameterized
# appliers (delete-required-field) are expanded per applicable stage below.
StageRecordOperator = Callable[[dict[str, Any]], "dict[str, Any] | None"]

# Known, CONFIRMED gaps in tools/check_staged_runtime_handshake.py discovered
# by this sweep: the checker validates that stages[].produces/requires are
# string lists, but never cross-checks that a stage's declared `produces`
# field actually exists as a key on that stage object. Stages 01-06 each have
# a dedicated stageNN_*_errors() function that re-derives this requirement
# from field-specific validation (e.g. stage-05 requires terminal_states
# directly; stage-01 requires input_digest directly via
# stage01_intake_errors()), so deleting their required field is caught.
#
# Formerly stage-01-intake had no such dedicated validator (its only checks
# were the generic stage-shape checks in sequence_errors()), so deleting
# stage-01's input_digest was NOT caught. That gap was closed by adding
# stage01_intake_errors() to tools/check_staged_runtime_handshake.py; the
# delete-required-field-stage-01-intake operator below is now fully rejected
# like every other stage. This dict is kept (empty) as the documented home
# for any future confirmed gap of this shape.
KNOWN_CHECKER_GAPS: dict[str, str] = {}


def _build_stage_record_operators() -> dict[str, dict[str, Any]]:
    ops: dict[str, dict[str, Any]] = {}
    for stage_id, field in STAGE_REQUIRED_FIELDS.items():
        short = stage_id.split("-", 2)[1]  # e.g. "01" from "stage-01-intake"
        op_name = f"delete-required-field-{stage_id}"
        ops[op_name] = {
            "stage": stage_id,
            "failure_class_hint": f"missing required field '{field}'",
            "checker": "check_staged_runtime_handshake",
            "apply": (lambda rec, sid=stage_id: op_delete_required_field(rec, sid)),
            "known_gap": KNOWN_CHECKER_GAPS.get(op_name),
        }
    ops["corrupt-body_ref"] = {
        "stage": "stage-04-burden-execution-act",
        "failure_class_hint": "body_ref polluted with owner/operation token",
        "checker": "check_staged_runtime_handshake",
        "apply": op_corrupt_body_ref,
    }
    ops["swap-owner-operation"] = {
        "stage": "stage-03-routing-owner-gate",
        "failure_class_hint": "owner_id and eligibility/operation values swapped",
        "checker": "check_staged_runtime_handshake",
        "apply": op_swap_owner_operation,
    }
    ops["replace-controlled-delta-with-prose"] = {
        "stage": "stage-06-field-witness-nar",
        "failure_class_hint": "delta_result replaced with free prose (not a controlled vocabulary token)",
        "checker": "check_staged_runtime_handshake",
        "apply": op_replace_controlled_delta_with_prose,
    }
    ops["drop-mrp-block"] = {
        "stage": "stage-05-mrp-reread-terminal-state",
        "failure_class_hint": "per_burden_reread missing a landed burden's entry",
        "checker": "check_staged_runtime_handshake",
        "apply": op_drop_mrp_block,
    }
    ops["fake-no-new-resultant"] = {
        "stage": "stage-05-mrp-reread-terminal-state",
        "failure_class_hint": "no_new_resultant claimed while unresolved burdens/live pressure remain",
        "checker": "check_staged_runtime_handshake",
        "apply": op_fake_no_new_resultant,
    }
    ops["move-burden-bmrp-to-bla"] = {
        "stage": "stage-05-mrp-reread-terminal-state",
        "failure_class_hint": "MRP-generated burden relocated into stage-02 baseline burden_floor",
        "checker": "check_staged_runtime_handshake",
        "apply": op_move_burden_bmrp_to_bla,
    }
    ops["omit-generated-by"] = {
        "stage": "stage-05-mrp-reread-terminal-state",
        "failure_class_hint": "generated burden missing generated_by provenance",
        "checker": "check_staged_runtime_handshake",
        "apply": op_omit_generated_by,
    }
    ops["remove-owner-activations-mirror"] = {
        "stage": "stage-06-field-witness-nar",
        "failure_class_hint": "owner_activations emptied while ACT rows remain",
        "checker": "check_staged_runtime_handshake",
        "apply": op_remove_owner_activations_mirror,
    }
    ops["slim-public-while-sidecar-rich"] = {
        "stage": "stage-07-release-output",
        "failure_class_hint": "public release text shrunk below structural minimum while sidecar stays rich",
        "checker": "render-family",
        "apply": op_slim_public_while_sidecar_rich,
    }
    ops["set-coverage-complete-despite-unresolved"] = {
        "stage": "stage-07-release-output",
        "failure_class_hint": "closure_claim=complete despite unresolved burdens",
        "checker": "check_staged_runtime_handshake",
        "apply": op_set_coverage_complete_despite_unresolved,
    }
    ops["absolute-sidecar-path"] = {
        "stage": "stage-08-verifier-sidecars",
        "failure_class_hint": "proof_sidecars path is absolute instead of repo-relative",
        "checker": "check_staged_runtime_handshake",
        "apply": op_absolute_sidecar_path,
    }
    return ops


STAGE_RECORD_OPERATORS: dict[str, dict[str, Any]] = _build_stage_record_operators()


def _run_handshake_checker(record_path: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "check_staged_runtime_handshake.py"),
            "--records",
            str(record_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def run_stage_record_sweep(source_path: Path, out_dir: Path) -> list[dict[str, Any]]:
    """Apply every stage-record operator to the record at source_path.

    Writes one mutated JSON per applicable operator into out_dir plus a
    sweep-manifest.json. Returns the manifest row list (also written to disk).
    """
    source = json.loads(source_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for op_name, meta in sorted(STAGE_RECORD_OPERATORS.items()):
        mutated = meta["apply"](source)
        if mutated is None:
            manifest.append({
                "operator": op_name,
                "expected_stage": meta["stage"],
                "expected_class_hint": meta["failure_class_hint"],
                "expected_checker": meta["checker"],
                "applicable": False,
                "output_file": None,
                "verdict": "skipped-not-applicable",
            })
            continue
        if mutated == source:
            manifest.append({
                "operator": op_name,
                "expected_stage": meta["stage"],
                "expected_class_hint": meta["failure_class_hint"],
                "expected_checker": meta["checker"],
                "applicable": True,
                "output_file": None,
                "verdict": "no-op-identical-to-source",
            })
            continue
        out_name = f"{op_name}.json"
        out_path = out_dir / out_name
        out_path.write_text(
            json.dumps(mutated, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        row: dict[str, Any] = {
            "operator": op_name,
            "expected_stage": meta["stage"],
            "expected_class_hint": meta["failure_class_hint"],
            "expected_checker": meta["checker"],
            "applicable": True,
            "output_file": str(out_path),
            "known_gap": meta.get("known_gap"),
        }
        if meta["checker"] == "check_staged_runtime_handshake":
            code, output = _run_handshake_checker(out_path)
            row["checker_exit_code"] = code
            row["verdict"] = "rejected" if code != 0 else "survivor"
            row["verification_depth"] = "full"
        else:
            row["verdict"] = "manifest-only-not-checker-verified"
            row["verification_depth"] = "manifest-only"
        manifest.append(row)
    manifest_path = out_dir / "sweep-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def stage_record_self_test() -> tuple[bool, list[str]]:
    """Run the stage-record sweep against the golden record and verify honestly.

    Checks:
      (a) every applicable mutated record differs from the source record.
      (b) every mutation whose checker is check_staged_runtime_handshake is
          REJECTED (nonzero exit) by that checker -- UNLESS it is pinned in
          KNOWN_CHECKER_GAPS, in which case a survivor is expected and
          reported as a finding, not a self-test failure (see that dict's
          docstring for why: this tool may not edit the checker).
      (c) render-family mutations are honestly marked manifest-only and are
          NOT claimed as full-rejection evidence.
      (d) every declared operator produced a manifest row (no silent drops).
    """
    golden = ROOT / "tests" / "staged-runtime-handshake" / "valid" / "retained-a9-science-source.json"
    out_dir = Path(tempfile.mkdtemp(prefix="daee_stage_mut_selftest_"))
    manifest = run_stage_record_sweep(golden, out_dir)

    problems: list[str] = []
    findings: list[str] = []
    seen_operators = {row["operator"] for row in manifest}
    missing_operators = sorted(set(STAGE_RECORD_OPERATORS) - seen_operators)
    if missing_operators:
        problems.append(f"operators missing from manifest: {missing_operators}")

    applicable_rows = [row for row in manifest if row.get("applicable")]
    if not applicable_rows:
        problems.append("no operator was applicable to the golden record")

    full_rows = [row for row in applicable_rows if row.get("verification_depth") == "full"]
    manifest_only_rows = [row for row in applicable_rows if row.get("verification_depth") == "manifest-only"]

    if not full_rows:
        problems.append("no operator reached full checker-rejection verification")

    for row in full_rows:
        known_gap = row.get("known_gap")
        if row.get("verdict") == "survivor":
            if known_gap:
                findings.append(
                    f"KNOWN CHECKER GAP (documented, not a self-test failure): "
                    f"{row['operator']} -> {row['output_file']}: {known_gap}"
                )
            else:
                problems.append(f"SURVIVOR (mutation not rejected): {row['operator']} -> {row['output_file']}")
        elif row.get("verdict") != "rejected":
            problems.append(f"unexpected verdict for {row['operator']}: {row.get('verdict')}")
        if row.get("checker_exit_code", 1) == 0 and not known_gap:
            problems.append(f"{row['operator']}: expected nonzero checker exit, got 0")

    for row in manifest_only_rows:
        if row.get("expected_checker") != "render-family":
            problems.append(
                f"{row['operator']}: manifest-only verdict but expected_checker is "
                f"{row.get('expected_checker')!r}, not 'render-family' (would misrepresent verification depth)"
            )

    # No mutant may be written under tests/.
    tests_root = (ROOT / "tests").resolve()
    for row in manifest:
        output_file = row.get("output_file")
        if output_file and tests_root in Path(output_file).resolve().parents:
            problems.append(f"mutant written under tests/: {output_file}")

    return (len(problems) == 0, problems, findings)


def self_test() -> int:
    emit_dir = Path(tempfile.mkdtemp(prefix="daee_mut_selftest_"))
    applied, skipped = sweep(emit_dir)
    survivors = [r for r in applied if r["verdict"] == "survivor"]
    collapse_applied = [r for r in applied if r["operator"] == "terminal-mrp-collapse"]
    checks = [
        ("terminal-mrp-collapse applied to >=1 fixture", len(collapse_applied) >= 1),
        ("no survivors (all applied mutants rejected)", len(survivors) == 0),
        ("witness-strip skips where no field_witness",
         any(s["operator"] == "witness-strip" for s in skipped)),
        ("no mutant written under tests/",
         not any(str((ROOT / "tests").resolve()) in str(p.resolve())
                 for p in emit_dir.glob("*.md"))),
        ("emit-dir guard rejects a tests/ path",
         _emit_guard_rejects()),
    ]
    ok = all(p for _, p in checks)
    for name, p in checks:
        print(f"  self-test {'PASS' if p else 'FAIL'}: {name}")
    print(f"  (applied={len(applied)} skipped={len(skipped)} survivors={len(survivors)})")

    stage_ok, stage_problems, stage_findings = stage_record_self_test()
    print(f"  stage-record self-test {'PASS' if stage_ok else 'FAIL'}: "
          f"per-stage mutation sweep on golden record")
    if stage_problems:
        for problem in stage_problems:
            print(f"    - {problem}")
    if stage_findings:
        for finding in stage_findings:
            print(f"    - {finding}")
    ok = ok and stage_ok

    print(f"gen-fixture-mutations self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def _emit_guard_rejects() -> bool:
    try:
        _safe_emit_dir(str(ROOT / "tests" / "x"))
        return False
    except SystemExit:
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixture anti-evasion mutation sweep (Plan 12 Phase 3 / Plan 13 Slice H)")
    parser.add_argument("--self-test", action="store_true", help="run the deterministic sweep self-test")
    parser.add_argument("--emit-dir", help="where to write text-mutation mutants (must be outside tests/); default: fresh tempdir")
    parser.add_argument("--sweep", metavar="VALID_RECORD_JSON", help="run the per-stage mutation sweep against a valid staged record")
    parser.add_argument("--out-dir", help="output directory for --sweep (must be outside tests/)")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    if args.sweep:
        if not args.out_dir:
            raise SystemExit("--out-dir is required with --sweep")
        source_path = Path(args.sweep).resolve()
        if not source_path.exists():
            raise SystemExit(f"--sweep record not found: {source_path}")
        out_dir = _safe_emit_dir(args.out_dir)
        manifest = run_stage_record_sweep(source_path, out_dir)
        applicable = [row for row in manifest if row.get("applicable")]
        all_survivors = [row for row in applicable if row.get("verdict") == "survivor"]
        known_gap_survivors = [row for row in all_survivors if row.get("known_gap")]
        unexpected_survivors = [row for row in all_survivors if not row.get("known_gap")]
        for row in manifest:
            print(f"  {row['operator']}: stage={row['expected_stage']} "
                  f"checker={row['expected_checker']} verdict={row['verdict']}")
        print(f"applicable={len(applicable)} survivors={len(all_survivors)} "
              f"(known-gap={len(known_gap_survivors)} unexpected={len(unexpected_survivors)}) "
              f"manifest={out_dir / 'sweep-manifest.json'}")
        for row in known_gap_survivors:
            print(f"KNOWN GAP (documented): {row['operator']} on {source_path}: {row['known_gap']}")
        if unexpected_survivors:
            for row in unexpected_survivors:
                print(f"FINDING: mutation survived: {row['operator']} on {source_path}")
            return 3
        return 0

    emit_dir = _safe_emit_dir(args.emit_dir)
    applied, skipped = sweep(emit_dir)
    survivors = [r for r in applied if r["verdict"] == "survivor"]
    for r in applied:
        print(f"  {r['operator']} {r['fixture']}: {r['verdict']}")
    print(f"applied={len(applied)} skipped={len(skipped)} survivors={len(survivors)} emit_dir={emit_dir}")
    if survivors:
        for r in survivors:
            print(f"FINDING: mutation survived: {r['operator']} on {r['fixture']}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
