#!/usr/bin/env python3
"""Plan 13 Slice 8: no-model Stage 01-08 dry-run emulator.

Executes the staged handoff contract over a synthetic/golden staged-runtime
record WITHOUT any model call, so architecture failures (broken stage
handoffs, malformed capsules, dead dispatch shards, prompt-budget blowups)
surface before any model spend. This does NOT replace model smokes (it never
calls a model and never claims interlocutor uptake, semantic faithfulness, or
release provenance) -- it exists so a model smoke failure is never spent
re-diagnosing an architecture bug this emulator could have caught for free.

For each stage 01..08 in order, this tool:
  1. validates the stage payload shape by re-running the staged-runtime
     handshake checker's record_errors() over the full record and mapping
     its errors onto the failed stage via classify_record_errors() (both
     reused, not reimplemented -- see check_staged_runtime_handshake.py);
  2. verifies the stage->next-stage handoff keys via the checker's own
     HANDOFF_CHECKS contract (reused);
  3. builds the state capsule for the prefix of stages completed so far by
     calling tools/run_staged_current_skill_smoke.py's build_state_capsule()
     (reused; that module is a plain, side-effect-free import -- see the
     "judgment calls" note in this file's __main__ docstring-adjacent
     comment below) and validates it with check_state_capsule.py (reused);
  4. simulates the output-append protocol: once stage-07 is reached, treats
     the record's own release_output artifact as the "growing artifact" and
     checks the final capsule's output_offset_bytes/output_sha256 replay
     invariants against it (mirrors check_state_capsule.py replay semantics
     without needing an ordered capsule-NNN.json directory on disk);
  5. verifies route-shard selection preconditions by reusing
     check_route_shard_selection.py's live-repo dispatch index parse +
     shard-existence check (availability preflight only; this is a repo-wide
     invariant, not a per-record one, so it runs once per emulator run);
  6. verifies no-full-replay: the compact_state() JSON composed for each
     stage prefix must stay under a byte budget, and once the tracked
     artifact exceeds 10KB, no per-stage compact_state may embed the full
     artifact text;
  7. on any failure, stops at the FIRST failed stage and prints the same
     explain-stage-failure JSON shape the handshake checker emits
     ({stage, failure_class, earliest_stage, downstream_invalidated,
     requires_model_rerun, repair_lane}), then exits nonzero.

This tool proves no model behavior and makes no interlocutor-uptake,
semantic-faithfulness, or release-provenance claim. It is a no-model
architecture preflight only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

# Reused, not reimplemented. Both modules are plain stdlib-only Python with no
# module-level side effects (no network, no filesystem writes, no argv
# parsing at import time) -- verified by direct import timing (~0.14s) before
# wiring this in. See the "judgment calls" note at the bottom of this file.
import check_staged_runtime_handshake as handshake_check  # noqa: E402
import check_state_capsule as capsule_check  # noqa: E402
import check_route_shard_selection as route_shard_check  # noqa: E402
import run_staged_current_skill_smoke as harness  # noqa: E402


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_RECORD = ROOT / "tests" / "staged-runtime-handshake" / "valid" / "retained-a9-science-source.json"
STAGE_ORDER = handshake_check.STAGE_ORDER
STAGE_ID_TO_CODE = {stage_id: f"{index + 1:02d}" for index, stage_id in enumerate(STAGE_ORDER)}

# Plan 13 Slice 8 mission budget: 20,000 est-tok ceiling for any synthetic
# per-stage "prompt equivalent" (the compact_state() JSON for a stage
# prefix), at an est-tok:byte ratio of 1:4 (mirrors the ratio used elsewhere
# in this repo's budget tooling, e.g. tools/load-path-budget.config.json).
NO_FULL_REPLAY_EST_TOK_CEILING = 20_000
NO_FULL_REPLAY_BYTE_CEILING = NO_FULL_REPLAY_EST_TOK_CEILING * 4
# Once the tracked synthetic artifact exceeds this many bytes, no per-stage
# compact_state may embed a full copy of the artifact text.
ARTIFACT_EMBED_TRIPWIRE_BYTES = 10_000


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stage_id_for_code(code: str) -> str:
    for stage_id, stage_code in STAGE_ID_TO_CODE.items():
        if stage_code == code:
            return stage_id
    return STAGE_ORDER[0]


# ---------------------------------------------------------------------------
# Step 1+2+7: stage-shape + handoff validation, reusing the handshake checker.
# ---------------------------------------------------------------------------

def handshake_diagnostic(record: dict[str, Any], record_path: Path) -> dict[str, Any]:
    """Run the handshake checker's own record_errors()+classify_record_errors()
    over the full record. Returns {"status": "pass"} or the explain-stage-
    failure diagnostic dict. This is a straight reuse of the checker's own
    taxonomy -- no local re-implementation of stage-shape/handoff rules."""
    errors = handshake_check.record_errors(record_path, record)
    return handshake_check.classify_record_errors(errors)


# ---------------------------------------------------------------------------
# Step 3: state capsule build + validate per stage prefix, reusing the
# harness's build_state_capsule() and the capsule checker's validation.
# ---------------------------------------------------------------------------

def capsule_for_prefix(
    record: dict[str, Any],
    stages_prefix: list[dict[str, Any]],
    output_path: Path | None,
) -> dict[str, Any]:
    stage_id = stages_prefix[-1]["id"]
    first_stage = stages_prefix[0] if stages_prefix else {}
    input_digest = str(first_stage.get("input_digest") or ("0" * 64))
    retained_input = first_stage.get("retained_input")
    raw_input_path = (ROOT / retained_input) if isinstance(retained_input, str) else ROOT
    return harness.build_state_capsule(
        case_id=str(record.get("case_id") or "dry-run-emulator"),
        input_digest=input_digest,
        stage_id=stage_id,
        stages=stages_prefix,
        raw_input_path=raw_input_path,
        output_path=output_path,
        run_dir=ROOT,
        root=ROOT,
    )


def capsule_errors_for_prefix(
    record: dict[str, Any],
    stages_prefix: list[dict[str, Any]],
    output_path: Path | None,
) -> tuple[dict[str, Any], list[str]]:
    schema = capsule_check.load_schema()
    capsule = capsule_for_prefix(record, stages_prefix, output_path)
    errors = capsule_check.validate_capsule_payload("dry-run-emulator capsule", capsule, schema)
    return capsule, errors


# ---------------------------------------------------------------------------
# Step 4: output-append / replay simulation. Once stage-07 is reached, the
# record's own release_output artifact is the "growing artifact"; the final
# capsule's output_offset_bytes/output_sha256 must match it byte-for-byte and
# hash-for-hash, mirroring check_state_capsule.py's replay_sequence_errors
# final-capsule check without needing an on-disk capsule-NNN.json sequence.
# ---------------------------------------------------------------------------

def release_output_path(record: dict[str, Any]) -> Path | None:
    stages = {stage.get("id"): stage for stage in record.get("stages", []) if isinstance(stage, dict)}
    stage07 = stages.get("stage-07-release-output")
    if not isinstance(stage07, dict):
        return None
    release_output = stage07.get("release_output")
    if not isinstance(release_output, dict):
        return None
    path_value = release_output.get("path")
    if not isinstance(path_value, str):
        return None
    candidate = (ROOT / path_value).resolve()
    return candidate if candidate.is_file() else None


def replay_errors_for_final_capsule(capsule: dict[str, Any], artifact_path: Path) -> list[str]:
    artifact_bytes = artifact_path.read_bytes()
    errors: list[str] = []
    expected_offset = len(artifact_bytes)
    actual_offset = capsule.get("output_offset_bytes")
    if actual_offset != expected_offset:
        errors.append(
            f"dry-run emulator: final capsule output_offset_bytes {actual_offset!r} "
            f"!= len(artifact) {expected_offset}"
        )
    expected_sha = hashlib.sha256(artifact_bytes).hexdigest()
    actual_sha = capsule.get("output_sha256")
    if actual_sha != expected_sha:
        errors.append(
            f"dry-run emulator: final capsule output_sha256 {actual_sha!r} != sha256(artifact) {expected_sha!r}"
        )
    return errors


# ---------------------------------------------------------------------------
# Step 5: route-shard selection preflight. This is a repo-wide dispatch-index
# invariant (not a per-record one), so it is checked once per emulator run by
# reusing check_route_shard_selection.py's live-repo layout + run_layout().
# ---------------------------------------------------------------------------

def route_shard_preflight_errors() -> list[str]:
    layout = route_shard_check.live_layout()
    return list(route_shard_check.run_layout(layout))


# ---------------------------------------------------------------------------
# Step 6: no-full-replay tripwire over compact_state() per stage prefix.
# ---------------------------------------------------------------------------

def _contains_full_text_copy(value: Any, needle: str) -> bool:
    """Walk a JSON-shaped value looking for any string leaf that literally
    contains `needle`. Checked against the raw structure (not the
    json.dumps()-serialized text) because JSON string-escaping of quotes/
    backslashes/newlines in the artifact would otherwise defeat a naive
    substring match against the serialized form."""
    if isinstance(value, str):
        return needle in value
    if isinstance(value, dict):
        return any(_contains_full_text_copy(item, needle) for item in value.values())
    if isinstance(value, list):
        return any(_contains_full_text_copy(item, needle) for item in value)
    return False


def no_full_replay_errors(
    stage_id: str,
    stages_prefix: list[dict[str, Any]],
    artifact_text: str | None,
) -> list[str]:
    errors: list[str] = []
    compact = harness.compact_state(stages_prefix)
    encoded = json.dumps(compact, ensure_ascii=False).encode("utf-8")
    if len(encoded) > NO_FULL_REPLAY_BYTE_CEILING:
        errors.append(
            f"dry-run emulator: {stage_id} compact_state is {len(encoded)} bytes, exceeds "
            f"no-full-replay ceiling {NO_FULL_REPLAY_BYTE_CEILING} bytes "
            f"({NO_FULL_REPLAY_EST_TOK_CEILING} est-tok)"
        )
    if artifact_text is not None and len(artifact_text.encode("utf-8")) > ARTIFACT_EMBED_TRIPWIRE_BYTES:
        if _contains_full_text_copy(compact, artifact_text):
            errors.append(
                f"dry-run emulator: {stage_id} compact_state embeds the full "
                f">{ARTIFACT_EMBED_TRIPWIRE_BYTES}-byte artifact text (no-full-replay violation)"
            )
    return errors


# ---------------------------------------------------------------------------
# Orchestration: run all stages 01..08 for one record, first-failed-stage.
# ---------------------------------------------------------------------------

def run_record(record: dict[str, Any], record_path: Path, *, verbose: bool = True) -> tuple[int, list[str]]:
    """Returns (exit_code, ledger_lines). On failure, prints the
    explain-stage-failure diagnostic JSON and returns nonzero."""
    ledger: list[str] = []

    # Step 1+2: whole-record shape/handoff validation, reused wholesale from
    # the handshake checker. This also gives FIRST-FAILED-STAGE classification
    # for free via the checker's own classify_record_errors() taxonomy.
    diagnostic = handshake_diagnostic(record, record_path)
    if diagnostic.get("status") != "pass":
        failed_code = str(diagnostic.get("earliest_stage") or "01")
        failed_index = STAGE_ORDER.index(stage_id_for_code(failed_code))
        for stage_id in STAGE_ORDER[:failed_index]:
            ledger.append(f"  PASS  {stage_id}")
        ledger.append(f"  FAIL  {stage_id_for_code(failed_code)} (handshake/handoff contract)")
        if verbose:
            for line in ledger:
                print(line)
            print(json.dumps(diagnostic, sort_keys=True))
        return 1, ledger

    # Step 5: route-shard selection availability preflight (repo-wide, runs
    # once; a failure here is an architecture failure independent of which
    # record is being replayed, so it is attributed to stage-07/stage-08
    # (release/verifier custody), the stages that actually consume the
    # dispatch index at runtime).
    shard_errors = route_shard_preflight_errors()
    if shard_errors:
        for stage_id in STAGE_ORDER[:-1]:
            ledger.append(f"  PASS  {stage_id}")
        ledger.append("  FAIL  stage-08-verifier-sidecars (route-shard dispatch preflight)")
        diag = {
            "stage": "08",
            "failure_class": "sidecar",
            "earliest_stage": "08",
            "downstream_invalidated": [],
            "requires_model_rerun": False,
            "repair_lane": "no-model fixture/checker/runtime-contract repair",
        }
        if verbose:
            for line in ledger:
                print(line)
            for error in shard_errors:
                print(f"    - {error}")
            print(json.dumps(diag, sort_keys=True))
        return 1, ledger

    stages = record.get("stages", [])
    artifact_path = release_output_path(record)
    artifact_text = artifact_path.read_text(encoding="utf-8", errors="replace") if artifact_path else None

    prefix: list[dict[str, Any]] = []
    for stage in stages:
        stage_id = stage.get("id")
        prefix.append(stage)

        # Step 3: capsule build + validate for the prefix so far.
        output_path_for_prefix = artifact_path if stage_id == "stage-07-release-output" or (
            artifact_path is not None and STAGE_ORDER.index(stage_id) >= STAGE_ORDER.index("stage-07-release-output")
        ) else None
        capsule, capsule_errors = capsule_errors_for_prefix(record, prefix, output_path_for_prefix)
        if capsule_errors:
            ledger.append(f"  FAIL  {stage_id} (state capsule)")
            stage_code = STAGE_ID_TO_CODE[stage_id]
            downstream = [code for code in STAGE_ID_TO_CODE.values() if code > stage_code]
            diag = {
                "stage": stage_code,
                "failure_class": "custody",
                "earliest_stage": stage_code,
                "downstream_invalidated": downstream,
                "requires_model_rerun": False,
                "repair_lane": "no-model fixture/checker/runtime-contract repair",
            }
            if verbose:
                for line in ledger[:-1]:
                    print(line)
                print(ledger[-1])
                for error in capsule_errors:
                    print(f"    - {error}")
                print(json.dumps(diag, sort_keys=True))
            return 1, ledger

        # Step 4: output-append / replay simulation once stage-07 is reached.
        if stage_id == "stage-07-release-output" and artifact_path is not None:
            replay_errs = replay_errors_for_final_capsule(capsule, artifact_path)
            if replay_errs:
                ledger.append(f"  FAIL  {stage_id} (output replay)")
                diag = {
                    "stage": "07",
                    "failure_class": "public-projection",
                    "earliest_stage": "07",
                    "downstream_invalidated": ["08"],
                    "requires_model_rerun": False,
                    "repair_lane": "no-model fixture/checker/runtime-contract repair",
                }
                if verbose:
                    for line in ledger[:-1]:
                        print(line)
                    print(ledger[-1])
                    for error in replay_errs:
                        print(f"    - {error}")
                    print(json.dumps(diag, sort_keys=True))
                return 1, ledger

        # Step 6: no-full-replay tripwire for this stage prefix.
        replay_budget_errors = no_full_replay_errors(stage_id, prefix, artifact_text)
        if replay_budget_errors:
            ledger.append(f"  FAIL  {stage_id} (no-full-replay tripwire)")
            stage_code = STAGE_ID_TO_CODE[stage_id]
            downstream = [code for code in STAGE_ID_TO_CODE.values() if code > stage_code]
            diag = {
                "stage": stage_code,
                "failure_class": "custody",
                "earliest_stage": stage_code,
                "downstream_invalidated": downstream,
                "requires_model_rerun": False,
                "repair_lane": "no-model fixture/checker/runtime-contract repair",
            }
            if verbose:
                for line in ledger[:-1]:
                    print(line)
                print(ledger[-1])
                for error in replay_budget_errors:
                    print(f"    - {error}")
                print(json.dumps(diag, sort_keys=True))
            return 1, ledger

        ledger.append(f"  PASS  {stage_id}")

    if verbose:
        for line in ledger:
            print(line)
        print("dry-run emulator: PASS")
    return 0, ledger


# ---------------------------------------------------------------------------
# --self-test
# ---------------------------------------------------------------------------

def _deepcopy_record(record: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(record)


def _stage_by_id(record: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    for stage in record.get("stages", []):
        if isinstance(stage, dict) and stage.get("id") == stage_id:
            return stage
    return None


def self_test_golden(record: dict[str, Any], record_path: Path) -> tuple[str, bool]:
    exit_code, _ledger = run_record(record, record_path, verbose=False)
    return "golden record passes end-to-end", exit_code == 0


def self_test_corruption_stage04_body_ref(record: dict[str, Any], record_path: Path) -> tuple[str, bool]:
    corrupted = _deepcopy_record(record)
    stage04 = _stage_by_id(corrupted, "stage-04-burden-execution-act")
    assert stage04 is not None
    refs = stage04.get("act_body_refs")
    if isinstance(refs, list) and refs:
        stage04["act_body_refs"] = ["BROKEN_REF"] + list(refs[1:])
    exit_code, _ledger = run_record(corrupted, record_path, verbose=False)
    diagnostic = handshake_diagnostic(corrupted, record_path)
    ok = exit_code != 0 and diagnostic.get("earliest_stage") == "04" and diagnostic.get("failure_class") == "act_body_ref"
    return "stage-04 broken body_ref fails at stage-04 with act_body_ref class", ok


def self_test_corruption_stage05_dropped_field(record: dict[str, Any], record_path: Path) -> tuple[str, bool]:
    corrupted = _deepcopy_record(record)
    stage05 = _stage_by_id(corrupted, "stage-05-mrp-reread-terminal-state")
    assert stage05 is not None
    stage05.pop("terminal_states", None)
    exit_code, _ledger = run_record(corrupted, record_path, verbose=False)
    diagnostic = handshake_diagnostic(corrupted, record_path)
    ok = exit_code != 0 and diagnostic.get("earliest_stage") == "05" and diagnostic.get("failure_class") == "mrp"
    return "stage-05 dropped terminal_states fails at stage-05 with mrp class", ok


def self_test_corruption_stage06_empty_owner_activations(record: dict[str, Any], record_path: Path) -> tuple[str, bool]:
    corrupted = _deepcopy_record(record)
    stage06 = _stage_by_id(corrupted, "stage-06-field-witness-nar")
    assert stage06 is not None
    stage06["owner_activations"] = []
    exit_code, _ledger = run_record(corrupted, record_path, verbose=False)
    diagnostic = handshake_diagnostic(corrupted, record_path)
    ok = (
        exit_code != 0
        and diagnostic.get("earliest_stage") == "06"
        and diagnostic.get("failure_class") == "field_witness"
    )
    return "stage-06 empty owner_activations fails at stage-06 with field_witness class", ok


def self_test_no_full_replay_tripwire(record: dict[str, Any], record_path: Path) -> tuple[str, bool]:
    """(c): a synthetic record whose stage-06 payload embeds a >10KB copy of
    the release output text must trip the no-full-replay tripwire."""
    corrupted = _deepcopy_record(record)
    artifact_path = release_output_path(corrupted)
    assert artifact_path is not None
    artifact_text = artifact_path.read_text(encoding="utf-8", errors="replace")
    if len(artifact_text.encode("utf-8")) <= ARTIFACT_EMBED_TRIPWIRE_BYTES:
        # Pad to exceed the tripwire threshold deterministically without
        # touching the retained golden artifact on disk.
        artifact_text = artifact_text + ("x" * (ARTIFACT_EMBED_TRIPWIRE_BYTES + 1 - len(artifact_text)))
    stage06 = _stage_by_id(corrupted, "stage-06-field-witness-nar")
    assert stage06 is not None
    # Embed the full artifact text verbatim into a stage-06 field so the
    # per-stage compact_state() for stage-06 (and onward) carries a literal
    # copy of the >10KB artifact -- this is the smuggling shape the tripwire
    # exists to catch. Field name is additive/unused elsewhere so it cannot
    # alter any other checker's semantics.
    stage06["_dry_run_self_test_embedded_artifact_copy"] = artifact_text

    prefix: list[dict[str, Any]] = []
    tripped = False
    for stage in corrupted.get("stages", []):
        prefix.append(stage)
        errors = no_full_replay_errors(stage.get("id"), prefix, artifact_text)
        if errors:
            tripped = True
            break
    return "no-full-replay tripwire fires on >10KB embedded artifact copy in stage-06", tripped


def self_test_large_output_preservation(record: dict[str, Any], record_path: Path) -> tuple[str, bool]:
    """(d): a synthetic 150KB+ artifact keeps the final capsule small (<16KB)
    and replay-consistent; the emulator itself never truncates or complains
    about artifact size (honoring Stage-08's no-model boundary)."""
    synthetic_record = _deepcopy_record(record)
    stage04 = _stage_by_id(synthetic_record, "stage-04-burden-execution-act")
    assert stage04 is not None
    act_rows = stage04.get("act_rows") or []
    act_lines = "\n".join(str(row) for row in act_rows)
    filler = ("y" * 200 + "\n") * 800  # ~160KB
    large_artifact_text = filler + act_lines + "\n"
    large_artifact_bytes = large_artifact_text.encode("utf-8")
    if len(large_artifact_bytes) <= 150_000:
        return "large-output preservation setup produced an artifact <=150KB", False

    scratch_dir = ROOT / "tests" / "dry-run-emulator" / "_self_test_scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    scratch_artifact = scratch_dir / "large-output.md"
    scratch_artifact.write_bytes(large_artifact_bytes)
    try:
        stage07 = _stage_by_id(synthetic_record, "stage-07-release-output")
        assert stage07 is not None
        stage07["release_output"] = {
            "path": rel(scratch_artifact),
            "sha256": hashlib.sha256(large_artifact_bytes).hexdigest().upper(),
        }

        stages = synthetic_record.get("stages", [])
        capsule, capsule_errors = capsule_errors_for_prefix(synthetic_record, stages, scratch_artifact)
        if capsule_errors:
            return f"large-output preservation: final capsule invalid: {capsule_errors[:2]}", False
        capsule_bytes = len(json.dumps(capsule, ensure_ascii=False).encode("utf-8"))
        if capsule_bytes >= 16_000:
            return f"large-output preservation: final capsule is {capsule_bytes} bytes, not <16KB", False
        replay_errs = replay_errors_for_final_capsule(capsule, scratch_artifact)
        if replay_errs:
            return f"large-output preservation: replay mismatch: {replay_errs}", False
        # Emulator must never truncate/complain about artifact size: the
        # no-full-replay tripwire governs *compact_state per-stage prompt
        # equivalents*, not the retained artifact file itself, and the
        # capsule build path above must have completed without raising.
        return "large-output preservation: 150KB+ artifact keeps final capsule <16KB and replay-consistent", True
    finally:
        try:
            scratch_artifact.unlink()
            scratch_dir.rmdir()
        except OSError:
            pass


def run_self_test(record_path: Path) -> int:
    record = read_json(record_path)
    cases = [
        self_test_golden(record, record_path),
        self_test_corruption_stage04_body_ref(record, record_path),
        self_test_corruption_stage05_dropped_field(record, record_path),
        self_test_corruption_stage06_empty_owner_activations(record, record_path),
        self_test_no_full_replay_tripwire(record, record_path),
        self_test_large_output_preservation(record, record_path),
    ]
    ok = True
    for name, passed in cases:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
        ok = ok and passed
    print(f"dry-run emulator self-test: {'PASS' if ok else 'FAIL'} ({sum(p for _, p in cases)}/{len(cases)})")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--record",
        type=Path,
        default=DEFAULT_RECORD,
        help="Staged-runtime-handshake record JSON to replay (default: golden retained record)",
    )
    parser.add_argument("--self-test", action="store_true", help="Run embedded self-test cases")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test(DEFAULT_RECORD)

    record_path = args.record
    record = read_json(record_path)
    exit_code, _ledger = run_record(record, record_path, verbose=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# Judgment calls (import vs mirror)
# ---------------------------------------------------------------------------
#
# IMPORTED wholesale (not mirrored):
#   - check_staged_runtime_handshake.record_errors / classify_record_errors /
#     STAGE_ORDER: this is the single source of truth for stage-shape,
#     handoff-key, and non-claim validation, plus the failure-class taxonomy.
#     Mirroring any of it would create a second copy of a large, actively
#     maintained rule set that would silently drift from the checker's own
#     fixture suite. It is a pure checker module (argparse only runs under
#     __main__), so importing it has no side effects.
#   - check_state_capsule.load_schema / validate_capsule_payload: same
#     reasoning -- the capsule schema/semantic-invariant rules are owned by
#     that module and its schema/state-capsule.schema.json.
#   - check_route_shard_selection.live_layout / run_layout: the dispatch
#     index parser + shard-existence preflight is intricate (table parsing,
#     lockstep byte comparison across four copies) and repo-wide, not
#     per-record; reusing it guarantees this emulator's Step 5 never drifts
#     from what actually gates a real run.
#   - run_staged_current_skill_smoke.build_state_capsule / compact_state /
#     stage_by_id: build_state_capsule() is the ~150-line function that
#     turns a stage-payload prefix into a schema-legal capsule (register
#     coverage, ACT/body_ref bare-join-key conversion, closed-terminal-state
#     grammar, etc.). It was verified importable in isolation (~0.14s import,
#     no argv/network/filesystem access at module scope) before relying on
#     it, and is documented in that module as "a pure function over the
#     `stages` accumulator" that "never mutates stages". Reimplementing it
#     would duplicate real domain logic (e.g. the Unicode superscript
#     body_ref -> bare-ASCII-join-key conversion) that already has to stay in
#     lockstep with schema/state-capsule.schema.json's BODY_REF_RE.
#
# MIRRORED (small, local, commented at the call site):
#   - The no-full-replay byte budget (20,000 est-tok / 80,000 bytes) and the
#     10KB artifact-embed tripwire are this emulator's OWN mission-specified
#     invariant (Plan 13 SS8), not a rule owned by any existing checker, so
#     there is nothing to import; no_full_replay_errors() above is the one
#     and only implementation.
#   - The output-append/replay check in replay_errors_for_final_capsule()
#     mirrors (in ~10 lines) the tail of check_state_capsule.py's
#     replay_sequence_errors() final-capsule offset/sha256 comparison, rather
#     than importing that function directly, because the real function
#     expects an ordered capsule-NNN.json sequence discovered from a
#     directory (discover_capsule_sequence()) and a case-id/fingerprint-drift
#     walk across that whole sequence; this emulator only ever has one
#     synthetic in-memory final capsule per run, so driving the full
#     multi-capsule replay contract through a fake single-entry directory
#     would be more indirection than the ~10 lines of offset/hash comparison
#     it mirrors.
