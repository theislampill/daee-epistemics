#!/usr/bin/env python3
"""Validate DAEE state-capsule v1 historical replay and composed v2 execution.

A state capsule is the small, structured hand-off meant to let a single model
call receive kernel + capsule + selected shards instead of replaying a full
150-300KB output.md or a 300k-token runtime. This checker validates ONE
capsule's shape + cross-field/reference invariants (--capsule), an ORDERED capsule sequence
against an artifact.md for cross-capsule replay invariants (--replay), and
runs an embedded + fixture self-test (--self-test).

Scope discipline: this is structural, referential, and replay validation of the
capsule contract only. It never infers semantic truth from structural validity
and does not certify interlocutor uptake, semantic faithfulness,
or release provenance, and it does not replace the harness emission wave that
will actually produce capsules at runtime (that is the next wave, not this one).

Stdlib-only; no jsonschema dependency, following the repo's existing custom
validation style (see tools/check_collapse_certificate_schema.py).

Usage:
  python tools/check_state_capsule.py --capsule <path.json> [--release-bearing]
  python tools/check_state_capsule.py --replay <dir>
  python tools/check_state_capsule.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from operation_capsule_contract import (
    validate_operation_capsule as validate_owned_operation_capsule,
    validate_operation_record as validate_owned_operation_record,
)
from owner_obligation_coverage import obligation_set_sha256, stable_obligation_id, validate_owner_obligation_coverage
from stage_projection_contract import canonical_json_bytes, canonical_json_sha256
from closure_state_lib import (
    FINAL_RENDER_ORDER,
    ClosureUniverseAuthorityError,
    build_closure_witness_projection,
    canonical_universe_sha256,
    derive_closure_decision,
    validate_trace as validate_closure_trace,
)
from mrp_recursion_lib import validate_lifecycle_record
from topology_mass_accounting import validate_accounting as validate_topology_mass_accounting


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "state-capsule.schema.json"
FIXTURE_ROOT = ROOT / "tests" / "state-capsule-fixtures"
V2_SCHEMA_PATH = ROOT / "schema" / "state-capsule-v2.schema.json"
V2_FIXTURE_ROOT = ROOT / "tests" / "state-capsule-v2"
NEGATIVE_EXPECTATION_SCHEMA_PATH = ROOT / "schema" / "negative-fixture-expectation.schema.json"
CONTRACT_REGISTRY_PATH = ROOT / "docs" / "audits" / "v0.4.6.0-wip-andon-contract-registry.json"
V2_MIGRATION_LEDGER_PATH = ROOT / "docs" / "audits" / "v0.4.6.0-wip-state-capsule-v2-migration-ledger.json"

SCHEMA_CONST = "daee-state-capsule-v1"
SCHEMA_V2_CONST = "daee-state-capsule-v2"
V2_SCHEMA_OWNER = "A16"

V2_STAGE_ORDER = [
    "stage-01-intake",
    "stage-02-layer-a-diagnostic-ir",
    "stage-03-routing-owner-gate",
    "stage-04-burden-execution-act",
    "stage-05-mrp-reread-terminal-state",
    "stage-06-field-witness-nar",
    "stage-07-release-output",
    "stage-08-verifier-sidecars",
]
V2_STAGE_INDEX = {stage: index for index, stage in enumerate(V2_STAGE_ORDER)}

STAGE_ORDER = ["01", "02", "03", "04", "05", "06", "07", "08"]
STAGE_INDEX = {stage: index for index, stage in enumerate(STAGE_ORDER)}

LIVE_REGISTER_TOKENS = {
    "N", "m", "tau", "sigma", "heart", "xi", "Omega", "mu", "kappa", "H",
    "τ",  # tau
    "σ",  # sigma
    "♥",  # heart
    "ξ",  # xi
    "Ω",  # Omega
    "μ",  # mu
    "κ",  # kappa
}

# FIX 4: alias-normalize live_registers/register_state keys onto a single
# canonical spelling per register (mirrors tools/register_axis_contract.py's
# REGISTER_AXIS_ALIASES, without importing it, to avoid coupling this
# schema-adjacent checker to the Stage 04 owner/register-axis contract
# module). Both the plain-name and Unicode glyph alias forms are legitimate
# live-register spellings; this map just collapses them so "tau" and "τ"
# are recognized as the SAME register when checking register_state coverage.
REGISTER_TOKEN_CANONICAL = {
    "N": "N",
    "m": "m",
    "tau": "tau",
    "τ": "tau",
    "sigma": "sigma",
    "σ": "sigma",
    "heart": "heart",
    "♥": "heart",
    "xi": "xi",
    "ξ": "xi",
    "Omega": "Omega",
    "Ω": "Omega",
    "mu": "mu",
    "μ": "mu",
    "kappa": "kappa",
    "κ": "kappa",
    "H": "H",
}

# FIX 4: registers exempt from requiring their own register_state entry.
# N is carried by n_frame (the selected/held-candidates n-frame slot IS its
# state); m and H are carried by dedicated capsule fields elsewhere in the
# pipeline (mode/held-set semantics) rather than by a per-register
# register_state annotation. Every OTHER live register must have a
# register_state entry or the capsule is claiming register liveness it
# never actually recorded state for.
REGISTER_STATE_EXEMPT_CANONICAL = {"N", "m", "H"}

ROUTE_RESULT_TYPES = {
    "held_burden_activation",
    "generated_burden_instantiation",
    "no_new_resultant",
    "loopbreak",
    "hold_partial",
    "none",
}

DIVERGENCE_STATES = {"neutral", "settled", "bounded", "non-neutral"}
CURL_STATES = {"null-state", "resolved", "held", "non-null"}
TRANSPORT_VALUES = {"chat", "file-retained"}

FINGERPRINT_RE = re.compile(r"^sha256:[A-Fa-f0-9]{64}$")
SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")
# Bare join-key body_ref: optional leading Unicode superscript digits, then
# B<digits>, optional _<digits> submove suffix. No '[' (owner/operation
# pollution) and no '.' beyond this pattern. Superscript digits 0-9 are NOT a
# contiguous Unicode range (0xB9/0xB2/0xB3 sit outside the 0x2070-0x2079
# block used for 0,4-9), so they are listed explicitly -- same set as SUP in
# tools/check_mrp_route_invariants.py.
SUPERSCRIPT_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
BODY_REF_RE = re.compile(rf"^[{SUPERSCRIPT_DIGITS}]*B[0-9]+(?:_[0-9]+)?$")

# G1: subscript digits, used by the harness's public submove notation
# (e.g. `¹B₁`: superscript burden digit before B, subscript submove digit
# after B). Same non-contiguous-range caveat as SUPERSCRIPT_DIGITS applies
# (subscript 0-9 spans 0x2080-0x2089 contiguously, unlike superscript, but
# both are spelled out explicitly here for a single shared translate table).
SUBSCRIPT_DIGITS = "₀₁₂₃₄₅₆₇₈₉"

WARN_BYTES = 16_000
# Hard smuggling line. The law's own capsule-relevant surface targets roughly
# ~4k estimated tokens (~16KB); 24KB gives headroom above WARN_BYTES while
# still refusing capsules that have clearly absorbed law/runtime prose rather
# than staying a small structured hand-off (was 40_000; adversarial audit
# found that ceiling loose enough to launder a meaningful prose-smuggling
# payload without ever tripping FAIL).
FAIL_BYTES = 24_000

NEXT_REQUIRED_ACTION_MAX_LEN = 400
NOTES_MAX_LEN = 1200

# FIX 2: closed-state whole-token vocabulary. A state is closed iff it matches
# ^(land|rejected|merged)\b optionally followed by (...) and NOTHING ELSE
# except an optional trailing '+'. This deliberately rejects qualifier
# suffixes (': PARTIAL', ': HOLD', '(pending') and compound words
# (landless, unmerged, Landmark, rejected-pending) that a bare substring
# check ("marker in lowered") would misclassify as closed.
CLOSED_TERMINAL_MARKERS = ("land", "rejected", "merged")
CLOSED_STATE_RE = re.compile(r"^(?:land|rejected|merged)\b(?:\([^)]*\))?\+?$", re.IGNORECASE)

# tools/run_staged_current_skill_smoke.py's Stage 05 CONTROLLED_STAGE05_TERMINAL_STATES
# vocabulary is a SEPARATE, exact-token controlled vocabulary from the
# Land(...)/rejected/merged artifact-prose family above (the harness never
# emits "Land(B1)" into a capsule's terminal_states -- it stores the raw
# Stage 05 head word, e.g. "landed"). Of that vocabulary, "landed",
# "cleared", and "discharged-as-derivative" are closed; "held-with-reason",
# "carried-PARTIAL", and "carried-RECURSE" are explicitly open/non-closed
# and must NOT be added here. This is an exact-token allowlist (not a
# prefix/regex match) so it cannot be widened by a near-miss the way a
# substring check could.
CLOSED_STAGE05_TERMINAL_STATES = {"landed", "cleared", "discharged-as-derivative"}

# FIX 1: ACT-row grammar family (mirrors tools/run_staged_current_skill_smoke.py
# fixture-observed ACT rows and tools/check_act_surface_syntax.py's compact
# ⟦ACT ...⟧ form). A line only counts as a real ACT row -- for replay parity
# purposes -- if it is anchored to one of these two surface grammars, not
# merely because a token happens to appear somewhere on the line (which is
# defeated by code fences, quotations, or negated mentions).
ACT_ROW_LOOSE_RE = re.compile(r"^\s*(?:[-*]\s*)?ACT\s+\S.*::")
ACT_ROW_COMPACT_RE = re.compile(r"⟦ACT\b[^⟧\n]*⟧")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)

# G1: candidate body_ref token extractors for an already-confirmed real
# ACT-row line (ACT_ROW_LOOSE_RE / ACT_ROW_COMPACT_RE above). The row-head
# token is whatever immediately follows `ACT`/`⟦ACT` up to the first
# bracket/colon/space (the public submove ref, e.g. `¹B₁` in
# `⟦ACT ¹B₁[owner.op] :: ...⟧` or `B1_1` in `ACT B1_1 :: op :: ...`); the
# `body_ref=` field is the harness's canonical explicit carrier. Both are
# collected as candidates and compared via normalize_burden_token()
# EQUALITY (not substring) against the capsule's body_ref.
ACT_ROW_HEAD_TOKEN_RE = re.compile(r"⟦?ACT\s+([^\s\[:]+)")
ACT_ROW_BODY_REF_FIELD_RE = re.compile(r"\bbody_ref=([^\s:⟧]+)")

# G1: Land(<token>) token family, used both to look up a burden's landing
# token by literal substring (legacy call sites already anchored to a
# specific literal) and, via normalize_burden_token(), to find every
# Land(...) occurrence whose inner token denotes the SAME burden under
# either harness-sanctioned notation (ASCII `Land(B1)` or superscript
# `Land(¹B)`).
LAND_TOKEN_RE = re.compile(r"Land\(([^)]*)\)")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    if not path.exists():
        return None, [f"{rel(path)}: file not found"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)}: invalid JSON: {exc}"]


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_v2_schema() -> dict[str, Any]:
    return json.loads(V2_SCHEMA_PATH.read_text(encoding="utf-8"))


def _resolve_local_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None
    current: Any = root_schema
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            return None
        current = current[token]
    return current if isinstance(current, dict) else None


def _json_identity(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def json_schema_errors(
    label: str,
    value: Any,
    root_schema: dict[str, Any],
    node_schema: dict[str, Any] | None = None,
    path: str = "$",
) -> list[str]:
    """Validate the JSON-Schema subset used by state-capsule-v2.

    This remains stdlib-only and intentionally does not claim general Draft
    2020-12 conformance. It covers the frozen schema's refs, anyOf, const,
    enums, types, object/array constraints, lengths, patterns, and minima.
    """
    schema = root_schema if node_schema is None else node_schema
    if "$ref" in schema:
        resolved = _resolve_local_ref(root_schema, schema["$ref"])
        if resolved is None:
            return [f"{label}: {path}: unresolved schema ref {schema['$ref']!r}"]
        return json_schema_errors(label, value, root_schema, resolved, path)

    if "anyOf" in schema:
        branches = schema["anyOf"]
        if not any(not json_schema_errors(label, value, root_schema, branch, path) for branch in branches):
            return [f"{label}: {path}: value does not satisfy anyOf"]

    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{label}: {path}: must equal {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{label}: {path}: must be one of {schema['enum']!r}, got {value!r}")

    expected_type = schema.get("type")
    if expected_type is not None and not _type_ok(value, expected_type):
        return errors + [f"{label}: {path}: expected type {expected_type!r}, got {type(value).__name__}"]

    if isinstance(value, dict):
        required = set(schema.get("required", []))
        missing = sorted(required - set(value))
        if missing:
            errors.append(f"{label}: {path}: missing required field(s): {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                errors.append(f"{label}: {path}: unknown field(s) (additionalProperties=false): {unknown}")
        minimum_properties = schema.get("minProperties")
        if isinstance(minimum_properties, int) and len(value) < minimum_properties:
            errors.append(f"{label}: {path}: requires at least {minimum_properties} properties")
        for key, child in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                errors.extend(json_schema_errors(label, child, root_schema, child_schema, f"{path}.{key}"))

    if isinstance(value, list):
        minimum_items = schema.get("minItems")
        if isinstance(minimum_items, int) and len(value) < minimum_items:
            errors.append(f"{label}: {path}: requires at least {minimum_items} item(s)")
        if schema.get("uniqueItems") is True:
            identities = [_json_identity(item) for item in value]
            if len(identities) != len(set(identities)):
                errors.append(f"{label}: {path}: array items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(json_schema_errors(label, item, root_schema, item_schema, f"{path}[{index}]"))

    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        if isinstance(minimum_length, int) and len(value) < minimum_length:
            errors.append(f"{label}: {path}: string length must be at least {minimum_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{label}: {path}: value {value!r} does not match {pattern!r}")

    if isinstance(value, int) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{label}: {path}: value {value} is less than minimum {minimum}")
        maximum = schema.get("maximum")
        if isinstance(maximum, (int, float)) and value > maximum:
            errors.append(f"{label}: {path}: value {value} is greater than maximum {maximum}")
    return errors


def v2_schema_owner_errors(label: str, payload: dict[str, Any]) -> list[str]:
    if "schema_owner" in payload:
        return [
            f"{label}: competing-schema-owner: {V2_SCHEMA_OWNER} is the sole state-capsule-v2 schema owner; "
            f"payload proposed {payload.get('schema_owner')!r}"
        ]
    try:
        registry = json.loads(CONTRACT_REGISTRY_PATH.read_text(encoding="utf-8"))
        migration = json.loads(V2_MIGRATION_LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{label}: competing-schema-owner: cannot read frozen A16 ownership evidence: {exc}"]
    registry_v2 = registry.get("state_capsule_v2", {})
    release_contract = migration.get("release_bearing_contract", {})
    observed = {
        registry_v2.get("single_owner"),
        migration.get("integration_owner"),
        release_contract.get("single_schema_owner"),
    }
    if observed != {V2_SCHEMA_OWNER}:
        return [
            f"{label}: competing-schema-owner: frozen ownership must resolve only to {V2_SCHEMA_OWNER}; "
            f"observed {sorted(str(item) for item in observed)!r}"
        ]
    if registry_v2.get("schema_path") != "schema/state-capsule-v2.schema.json":
        return [f"{label}: competing-schema-owner: registry points to a noncanonical v2 schema path"]
    return []


def _duplicate_id_errors(label: str, collection: str, rows: Any, key: str) -> list[str]:
    if not isinstance(rows, list):
        return []
    seen: set[Any] = set()
    errors: list[str] = []
    for row in rows:
        value = row.get(key) if isinstance(row, dict) else None
        if value in seen:
            errors.append(f"{label}: duplicate-id: {collection}.{key} {value!r} appears more than once")
        seen.add(value)
    return errors


def _row_map(rows: Any, key: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        return {}
    return {
        row[key]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get(key), str)
    }


def _dangling_errors(
    label: str,
    owner: str,
    field: str,
    values: Any,
    known: set[str],
) -> list[str]:
    if not isinstance(values, list):
        return []
    missing = [value for value in values if value not in known]
    return [f"{label}: dangling-reference: {owner}.{field} references missing ID {value!r}" for value in missing]


# Frozen additive v2 interface (ADR-046-001/014/015/016 and Plan 21).
# These validators adapt to the existing semantic owners instead of cloning
# their acceptance logic.  A07's public reducer core is composed through a
# lossless corrected-state projection; its provisional state-v2 adapter remains
# a read-only follow-up boundary recorded by the migration ledger.
def _v2_diag(label: str, stage: str, failure_class: str, subcode: str, message: str) -> str:
    return f"{label}: [stage={stage} class={failure_class} subcode={subcode}] {message}"


def _v2_self_hash(value: dict[str, Any], field: str) -> str:
    return canonical_json_sha256({key: item for key, item in value.items() if key != field})


def _v2_map(rows: Any, key: str) -> dict[str, dict[str, Any]]:
    return {row[key]: row for row in rows if isinstance(row, dict) and isinstance(row.get(key), str)} if isinstance(rows, list) else {}


def _v2_duplicate(values: list[Any]) -> Any | None:
    seen: set[Any] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None


def _v2_control_preflight_errors(label: str, payload: dict[str, Any]) -> list[str]:
    if "schema_owner" in payload:
        return [_v2_diag(label, "control-plane", "competing-schema-owner", "competing-schema-owner",
            f"A16 is the sole schema owner; competing owner {payload.get('schema_owner')!r} is forbidden")]
    owner_errors = v2_schema_owner_errors(label, payload)
    if owner_errors:
        return [_v2_diag(label, "control-plane", "competing-schema-owner", "competing-schema-owner", owner_errors[0])]
    if payload.get("canonicalization") != "daee-canonical-json-v1":
        return [_v2_diag(label, "preflight", "state-capsule-custody", "canonicalization-mismatch",
            "canonicalization must be daee-canonical-json-v1")]
    for collection, key in (("observation_units", "unit_id"), ("candidate_states", "state_id"),
                            ("input_pressures", "pressure_id"), ("candidate_state_partitions", "partition_id")):
        values = [row.get(key) for row in payload.get(collection, []) if isinstance(row, dict)]
        duplicate = _v2_duplicate(values)
        if duplicate is not None:
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"duplicate {collection}.{key} {duplicate!r}")]
    resource_policy = payload.get("resource_policy")
    if isinstance(resource_policy, dict) and resource_policy.get("semantic_depth_cap") is not None:
        return [_v2_diag(label, "preflight", "semantic-depth-cap", "semantic-depth-cap",
            f"semantic_depth_cap must be null; fixed cap {resource_policy.get('semantic_depth_cap')!r} is forbidden")]
    for cycle in payload.get("burden_cycles", []):
        raw = cycle.get("reread", {}).get("raw_exit", {}) if isinstance(cycle, dict) else {}
        if isinstance(raw, dict) and raw.get("exit_disposition") == "COMPLETE":
            return [_v2_diag(label, "05", "mrp", "raw-complete-forbidden",
                "raw exit COMPLETE is forbidden; only the Stage07 derived closure oracle may yield COMPLETE")]
        loop = raw.get("loopbreak") if isinstance(raw, dict) else None
        if isinstance(loop, dict):
            required = {"loopbreak_id", "observed_loop", "observed_loop_event_index", "pre_break_graph",
                "owner_ground_ref", "performed_operation_ref", "local_delta_ref", "interruption_event_index",
                "post_break_graph", "post_break_reread", "loopbreak_sha256"}
            missing = sorted(required - set(loop))
            if missing:
                return [_v2_diag(label, "05", "mrp", "incomplete-loopbreak",
                    f"LoopBreak evidence is incomplete; missing {missing!r}")]
    projection = payload.get("projection", {})
    stage_number = V2_STAGE_INDEX.get(str(payload.get("stage")), -1) + 1
    if stage_number >= 7 and isinstance(projection, dict) and projection.get("public_field_witness_sha256") is None:
        return [_v2_diag(label, "07", "witness-binding", "public-witness-hash-missing",
            "Stage07 requires public_field_witness_sha256; ambiguous field_witness_sha256 is not accepted")]
    return []


def _v2_topology_errors(label: str, payload: dict[str, Any]) -> list[str]:
    specs = [
        ("observation_units", "unit_id"), ("candidate_states", "state_id"),
        ("input_pressures", "pressure_id"), ("candidate_state_partitions", "partition_id"),
        ("burden_partition_decisions", "decision_id"), ("owner_routes", "obligation_id"),
        ("operation_capsules", "capsule_id"), ("burden_cycles", "cycle_id"),
    ]
    for collection, key in specs:
        values = [row.get(key) for row in payload.get(collection, []) if isinstance(row, dict)]
        duplicate = _v2_duplicate(values)
        if duplicate is not None:
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"duplicate {collection}.{key} {duplicate!r}")]
    observations = _v2_map(payload.get("observation_units"), "unit_id")
    candidates = _v2_map(payload.get("candidate_states"), "state_id")
    pressures = _v2_map(payload.get("input_pressures"), "pressure_id")
    partitions = _v2_map(payload.get("candidate_state_partitions"), "partition_id")
    decisions = _v2_map(payload.get("burden_partition_decisions"), "decision_id")
    known_units = set(observations)
    for unit_id, row in observations.items():
        parent = row.get("parent_unit_id")
        if parent is not None and parent not in observations:
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"observation unit {unit_id} parent_unit_id {parent!r} is dangling")]
        if row.get("source_start", 0) >= row.get("source_end", 0):
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"observation unit {unit_id} has an empty or reversed source range")]
    for state_id, row in candidates.items():
        for field, known in (("observation_unit_ids", known_units), ("pressure_ids", set(pressures)), ("partition_ids", set(partitions))):
            missing = sorted(set(row.get(field, [])) - known)
            if missing:
                return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                    f"candidate {state_id} {field} has dangling reference(s) {missing!r}")]
        merged_into = row.get("merged_into")
        if merged_into is not None and merged_into not in candidates:
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"candidate {state_id} merged_into {merged_into!r} is dangling")]
    for pressure_id, row in pressures.items():
        for field, known in (("observation_unit_ids", known_units), ("candidate_state_ids", set(candidates))):
            missing = sorted(set(row.get(field, [])) - known)
            if missing:
                return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                    f"pressure {pressure_id} {field} has dangling reference(s) {missing!r}")]
        decision_id = row.get("decision_id")
        if decision_id is not None and decision_id not in decisions:
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"pressure {pressure_id} decision_id {decision_id!r} is dangling")]
    memberships: dict[str, set[str]] = {state_id: set() for state_id in candidates}
    for partition_id, row in partitions.items():
        members = row.get("member_state_ids", [])
        missing = sorted(set(members) - set(candidates))
        if missing:
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"partition {partition_id} member_state_ids has dangling reference(s) {missing!r}")]
        for state_id in members:
            memberships[state_id].add(partition_id)
        declared = {
            "selected": set([row["selected_state_id"]]) if row.get("selected_state_id") else set(),
            "held": set(row.get("held_state_ids", [])), "merged": set(row.get("merged_state_ids", [])),
            "rejected": set(row.get("rejected_state_ids", [])),
        }
        if any(not values.issubset(set(members)) for values in declared.values()):
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"partition {partition_id} terminal sets must be subsets of member_state_ids")]
        for status, values in declared.items():
            for state_id in values:
                actual = candidates[state_id].get("status")
                if actual != status and not (status == "held" and actual == "underdetermined"):
                    return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                        f"overlapping hyperedge {partition_id} assigns {state_id}={status} but global status is {actual!r}")]
    for state_id, actual_memberships in memberships.items():
        if not actual_memberships or actual_memberships != set(candidates[state_id].get("partition_ids", [])):
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"candidate {state_id} partition_ids do not equal overlapping hyperedge memberships {sorted(actual_memberships)!r}")]
    selected = [row for row in candidates.values() if row.get("status") == "selected"]
    if payload.get("selection_status") == "licensed":
        if len(selected) != 1 or payload.get("selected_n_frame") != selected[0].get("frame_token"):
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                "licensed selection must name exactly one selected candidate frame_token")]
    elif selected or payload.get("selected_n_frame") is not None:
        return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
            "not_licensed selection requires no selected candidate and selected_n_frame null")]
    pressure_decisions: dict[str, list[str]] = {pressure_id: [] for pressure_id in pressures}
    edges: dict[str, list[str]] = {pressure_id: [] for pressure_id in pressures}
    for decision_id, row in decisions.items():
        for pressure_id in row.get("pressure_ids", []):
            if pressure_id not in pressures:
                return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                    f"burden partition {decision_id} pressure_id {pressure_id!r} is dangling")]
            pressure_decisions[pressure_id].append(decision_id)
        for edge in row.get("pressure_to_burden", []):
            pressure_id = edge.get("pressure_id")
            if pressure_id not in pressures:
                return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                    f"burden partition {decision_id} edge pressure_id {pressure_id!r} is dangling")]
            edges[pressure_id].append(str(edge.get("burden_id")))
    for pressure_id, owners in pressure_decisions.items():
        if len(owners) != 1:
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"pressure {pressure_id} must appear in exactly one burden partition; got {owners!r}")]
        row = pressures[pressure_id]
        if row.get("status") in {"routed", "merged"} and edges[pressure_id] != [row.get("burden_id")]:
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
                f"pressure {pressure_id} route does not match pressure_to_burden")]
    produced_burdens = [burden for routes in edges.values() for burden in routes]
    if set(produced_burdens) != set(payload.get("burden_floor", [])):
        return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
            f"burden_floor must equal partition-produced burdens; produced={sorted(set(produced_burdens))!r}")]
    coverage = payload.get("input_coverage", {})
    if set(coverage.get("all_observation_unit_ids", [])) != known_units or coverage.get("unaccounted_unit_ids"):
        return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-missing",
            "input_coverage must exactly account for all observation unit IDs with no unaccounted IDs")]
    freeze = payload.get("stage02_freeze", {})
    observation_ids = [row.get("unit_id") for row in payload.get("observation_units", [])]
    candidate_ids = [row.get("state_id") for row in payload.get("candidate_states", [])]
    pressure_ids = [row.get("pressure_id") for row in payload.get("input_pressures", [])]
    candidate_partition_ids = [row.get("partition_id") for row in payload.get("candidate_state_partitions", [])]
    burden_partition_ids = [row.get("decision_id") for row in payload.get("burden_partition_decisions", [])]
    topology = {"candidate_states": payload.get("candidate_states", []), "input_pressures": payload.get("input_pressures", []),
        "candidate_state_partitions": payload.get("candidate_state_partitions", []),
        "burden_partition_decisions": payload.get("burden_partition_decisions", []), "B_LA": freeze.get("B_LA", [])}
    expected_hashes = {
        "observation_unit_set_sha256": canonical_json_sha256(sorted(observation_ids)),
        "candidate_state_set_sha256": canonical_json_sha256(sorted(candidate_ids)),
        "input_pressure_set_sha256": canonical_json_sha256(sorted(pressure_ids)),
        "candidate_partition_set_sha256": canonical_json_sha256(sorted(candidate_partition_ids)),
        "burden_partition_decision_set_sha256": canonical_json_sha256(sorted(burden_partition_ids)),
        "B_LA_sequence_sha256": canonical_json_sha256(freeze.get("B_LA", [])),
        "topology_state_sha256": canonical_json_sha256(topology),
    }
    sequence_fields = {
        "observation_unit_ids": observation_ids, "candidate_state_ids": candidate_ids,
        "input_pressure_ids": pressure_ids, "candidate_partition_ids": candidate_partition_ids,
        "burden_partition_decision_ids": burden_partition_ids,
    }
    if any(freeze.get(field) != values for field, values in sequence_fields.items()):
        return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-hash",
            "stage02_freeze independent observation/candidate/pressure/partition universes do not preserve canonical source sequences")]
    for field, expected in expected_hashes.items():
        if freeze.get(field) != expected:
            return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-hash",
                f"stage02_freeze {field} mismatch: expected {expected}")]
    if freeze.get("record_sha256") != _v2_self_hash(freeze, "record_sha256"):
        return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "baseline-freeze-hash",
            "stage02_freeze record_sha256 mismatch")]
    initial_burdens = [row.get("burden_id") for row in payload.get("burden_cycles", []) if row.get("origin") == "B_LA"]
    late = [burden for burden in initial_burdens if burden not in freeze.get("B_LA", [])]
    if late:
        return [_v2_diag(label, "02", "stage02-input-pressure-coverage", "b-la-late-append",
            f"B_LA burden(s) {late!r} appear after stage02_freeze")]
    return []


def _v2_obligation_errors(label: str, payload: dict[str, Any]) -> list[str]:
    routes = payload.get("owner_routes", [])
    if routes:
        record = {
            "topology_contract": payload["topology_contract"],
            "upstream_obligation_ids": payload["upstream_obligation_ids"],
            "upstream_obligation_set_sha256": payload["upstream_obligation_set_sha256"],
            "owner_routes": routes,
            "act_row_details": payload["act_row_details"],
            "owner_execution_dispositions": payload["owner_execution_dispositions"],
            "partition_derivative_mappings": payload["partition_derivative_mappings"],
            "stage04_status": "pass",
            "downstream_release_state": payload.get("closure_state", {}).get("derived_decision"),
        }
        findings = validate_owner_obligation_coverage(
            record,
            upstream_obligation_ids=[row["obligation_id"] for row in routes],
            upstream_pressure_ids=[row["pressure_id"] for row in payload["input_pressures"]],
            upstream_partition_decision_ids=[row["decision_id"] for row in payload["burden_partition_decisions"]],
            upstream_derivative_inventory=payload["partition_derivative_mappings"],
            upstream_derivative_inventory_sha256=payload["partition_derivative_mappings_sha256"],
        )
        if findings:
            finding = findings[0]
            return [_v2_diag(label, "03", finding["failure_class"], finding["failure_subcode"], finding["message"])]
    elif any(payload.get(field) for field in ("upstream_obligation_ids", "act_row_details", "owner_execution_dispositions")):
        return [_v2_diag(label, "03", "owner-obligation-coverage", "obligation-universe-mismatch",
            "empty owner route universe cannot carry obligations, ACT rows, or dispositions")]
    dispositions = payload.get("owner_execution_dispositions", [])
    expected_state = {
        "declared_ids": [row["obligation_id"] for row in routes],
        "executed_ids": [row["obligation_id"] for row in dispositions if row["disposition"] == "executed"],
        "held_ids": [row["obligation_id"] for row in dispositions if row["disposition"] == "held"],
        "partial_ids": [row["obligation_id"] for row in dispositions if row["disposition"] == "partial"],
        "terminal_disposition_sha256": canonical_json_sha256(dispositions),
    }
    if payload.get("owner_obligation_state") != expected_state:
        return [_v2_diag(label, "04", "owner-obligation-coverage", "owner-obligation-state-projection",
            "owner_obligation_state is not the exact declared/executed/held/partial disposition projection")]
    for cycle in payload.get("burden_cycles", []):
        expected = obligation_set_sha256(cycle.get("obligation_ids", []))
        if cycle.get("obligation_set_sha256") != expected:
            return [_v2_diag(label, "03", "owner-obligation-coverage", "obligation-universe-hash",
                f"cycle {cycle.get('cycle_id')} obligation_set_sha256 mismatch; expected {expected}")]
    return []


def _v2_event_hash_error(label: str, stage: str, failure_class: str, subcode: str,
                         row: dict[str, Any], hash_field: str, identity: str) -> list[str]:
    expected = _v2_self_hash(row, hash_field)
    if row.get(hash_field) != expected:
        return [_v2_diag(label, stage, failure_class, subcode,
            f"{identity} {hash_field} mismatch; expected {expected}")]
    return []


def _v2_operation_errors(label: str, payload: dict[str, Any]) -> list[str]:
    obligations = _v2_map(payload.get("owner_routes"), "obligation_id")
    acts = _v2_map(payload.get("act_row_details"), "obligation_id")
    operations = _v2_map(payload.get("operation_capsules"), "capsule_id")
    cycles = _v2_map(payload.get("burden_cycles"), "cycle_id")
    body_hashes: dict[str, str] = {}
    for capsule_id, capsule in operations.items():
        expected_hash = "sha256:" + _v2_self_hash(capsule, "operation_capsule_sha256")
        if capsule.get("operation_capsule_sha256") != expected_hash:
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                f"operation capsule {capsule_id} operation_capsule_sha256 mismatch; expected {expected_hash}")]
        owner_findings = validate_owned_operation_capsule(capsule)
        if owner_findings:
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                f"operation capsule {capsule_id} fails operation owner: {owner_findings[0]}")]
        cycle = cycles.get(str(capsule.get("cycle_id")))
        capsule_obligation_ids = capsule.get("obligation_ids", [])
        joined = [obligations.get(str(value)) for value in capsule_obligation_ids]
        if cycle is None or not capsule_obligation_ids or any(value is None for value in joined):
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                f"operation capsule {capsule_id} has dangling obligation_ids/cycle reference")]
        for obligation in joined:
            assert obligation is not None
            for field in ("burden_id", "pressure_ids", "owner_id", "operation", "register_axis"):
                if capsule.get(field) != obligation.get(field):
                    return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                        f"operation capsule {capsule_id} {field} does not match obligation {obligation.get('obligation_id')}")]
            act = acts.get(str(obligation["obligation_id"]))
            if act is None or act.get("body_ref") != capsule.get("body_ref"):
                return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                    f"operation capsule {capsule_id} does not exactly join ACT body_ref for {obligation['obligation_id']}")]
        if capsule.get("burden_id") != cycle.get("burden_id"):
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                f"operation capsule {capsule_id} burden_id does not match cycle {cycle.get('cycle_id')}")]
        body_ref, body_sha = str(capsule.get("body_ref")), str(capsule.get("body_sha256"))
        if body_ref in body_hashes and body_hashes[body_ref] != body_sha:
            return [_v2_diag(label, "04", "act_body_evidence", "body-hash-conflict",
                f"body_ref {body_ref!r} has conflicting body_sha256 values {body_hashes[body_ref]!r} and {body_sha!r}")]
        body_hashes[body_ref] = body_sha
    executed = {row["obligation_id"] for row in payload.get("owner_execution_dispositions", []) if row.get("disposition") == "executed"}
    for obligation_id in executed:
        matches = [row for row in operations.values() if obligation_id in row.get("obligation_ids", [])]
        if not matches:
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                f"executed obligation {obligation_id} maps to no operation capsule")]
    executed_routes = [row for row in payload.get("owner_routes", []) if row.get("obligation_id") in executed]
    if not executed_routes:
        if payload.get("operation_capsules") or payload.get("operation_body_artifacts"):
            return [_v2_diag(label, "04", "act_body_evidence", "obligation-capsule-cardinality",
                "an empty executed-obligation universe cannot carry operation capsules or body artifacts")]
        return []
    independent_inventory = {
        "obligation_ids": [row["obligation_id"] for row in executed_routes],
        "pressure_ids": [row["pressure_id"] for row in payload.get("input_pressures", [])],
        "cycle_ids": [row["cycle_id"] for row in payload.get("burden_cycles", [])],
    }
    operation_record = {
        "execution_contract": "operation-capsule-v1",
        "hydration_policy": "projection-only",
        "operation_capsules": payload.get("operation_capsules", []),
        "events": [
            {
                "event_id": event["event_id"], "capsule_id": event["operation_capsule_id"],
                "sequence": event["sequence"], "kind": event["kind"], "ref": event["ref"],
            }
            for cycle in payload.get("burden_cycles", []) for event in cycle.get("operation_events", [])
        ],
        "obligations": executed_routes,
        "pressures": payload.get("input_pressures", []),
        "owner_routes": executed_routes,
        "act_row_details": [row for row in payload.get("act_row_details", []) if row.get("obligation_id") in executed],
        "cycles": [{"cycle_id": row["cycle_id"], "burden_id": row["burden_id"],
                    "obligation_ids": row["obligation_ids"], "operation_capsule_ids": row["operation_capsule_ids"]}
                   for row in payload.get("burden_cycles", [])],
        "body_artifacts": payload.get("operation_body_artifacts"),
        "release_state": payload.get("closure_state", {}).get("derived_decision"),
        "operation_capsule_hashes": {row["body_ref"]: row["operation_capsule_sha256"]
                                     for row in payload.get("operation_capsules", [])},
    }
    owner_findings = validate_owned_operation_record(
        operation_record,
        upstream_inventory=independent_inventory,
        upstream_inventory_sha256=canonical_json_sha256(independent_inventory),
    )
    if owner_findings:
        finding = owner_findings[0]
        return [_v2_diag(label, "04", finding["failure_class"], finding["failure_subcode"], finding["message"])]
    return []


def _v2_topology_mass_errors(label: str, payload: dict[str, Any]) -> list[str]:
    if payload.get("partition_derivative_mappings_sha256") != canonical_json_sha256(payload.get("partition_derivative_mappings", [])):
        return [_v2_diag(label, "03", "owner-obligation-coverage", "derivative-inventory-hash",
            "partition_derivative_mappings_sha256 does not bind the independent Plan03 derivative inventory")]
    authority = payload.get("topology_mass_evidence_authority")
    authority_sha256 = payload.get("topology_mass_evidence_authority_sha256")
    findings = validate_topology_mass_accounting(
        payload.get("topology_mass_accounting"),
        upstream_obligation_ids=[row["obligation_id"] for row in payload.get("owner_routes", [])],
        upstream_inventory_sha256=payload.get("upstream_obligation_set_sha256"),
        evidence_authority=authority,
        evidence_authority_sha256=authority_sha256,
    )
    if findings:
        finding = findings[0]
        return [_v2_diag(label, "06", finding["failure_class"], finding["failure_subcode"], finding["message"])]
    return []


def _v2_graph_hash_error(label: str, graph: dict[str, Any], identity: str) -> list[str]:
    return _v2_event_hash_error(label, "05", "mrp", "incomplete-loopbreak", graph, "graph_sha256", identity)


def _v2_has_cycle(nodes: list[str], edges: list[dict[str, str]]) -> bool:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edges:
        adjacency.setdefault(str(edge.get("from")), []).append(str(edge.get("to")))
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in adjacency.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False
    return any(visit(node) for node in list(adjacency))


def _v2_cycle_errors(label: str, payload: dict[str, Any]) -> list[str]:
    operations = _v2_map(payload.get("operation_capsules"), "capsule_id")
    obligations = _v2_map(payload.get("owner_routes"), "obligation_id")
    cycles = payload.get("burden_cycles", [])
    cycles_by_id = _v2_map(cycles, "cycle_id")
    all_indices: list[int] = [payload.get("stage02_freeze", {}).get("event_index")]
    all_event_ids: list[str] = [str(payload.get("stage02_freeze", {}).get("record_id"))]
    candidate_events_by_id: dict[str, dict[str, Any]] = {}
    indexed_nodes: list[tuple[int, str]] = [(payload["stage02_freeze"]["event_index"], payload["stage02_freeze"]["record_id"])]
    extra_edges: list[dict[str, str]] = []
    seen_cycles: dict[str, dict[str, Any]] = {}
    for cycle in cycles:
        cycle_id = str(cycle.get("cycle_id"))
        origin, depth, parent_id = cycle.get("origin"), cycle.get("generation_depth"), cycle.get("parent_cycle_id")
        if origin == "B_LA":
            if depth != 0 or parent_id is not None:
                return [_v2_diag(label, "05", "mrp", "generation-parentage",
                    f"B_LA cycle {cycle_id} must have generation_depth 0 and parent null")]
        else:
            parent = seen_cycles.get(str(parent_id))
            if parent is None or depth != parent.get("generation_depth", -1) + 1:
                return [_v2_diag(label, "05", "mrp", "generation-parentage",
                    f"B_MRP cycle {cycle_id} requires an earlier parent and generation_depth parent+1")]
            parent_events = parent.get("reread", {}).get("raw_exit", {}).get("candidate_events", [])
            generators = [event for event in parent_events if event.get("disposition") == "instantiate_generated"
                and event.get("target_burden_id") == cycle.get("burden_id") and event.get("next_cycle_id") == cycle_id]
            if len(generators) != 1:
                return [_v2_diag(label, "05", "mrp", "generation-parentage",
                    f"B_MRP cycle {cycle_id} is not bound to exactly one parent candidate generation event")]
        seen_cycles[cycle_id] = cycle
        phase = cycle.get("phase")
        phase_rank = {"ROUTED": 1, "EXECUTED": 2, "LANDED": 3, "REREAD_EVALUATED": 4}[phase]
        phase_fields = (("route_gradient", 1), ("operation_events", 2), ("land", 3), ("post_land_delta", 3), ("reread", 4))
        for field, required_rank in phase_fields:
            present = field in cycle
            if phase_rank >= required_rank and not present:
                return [_v2_diag(label, "05", "mrp", "replay-history-mutation",
                    f"cycle {cycle_id} phase {phase} requires {field}")]
            if phase_rank < required_rank and present:
                return [_v2_diag(label, "05", "mrp", "replay-history-mutation",
                    f"cycle {cycle_id} phase {phase} cannot assert later field {field}")]
        route = cycle["route_gradient"]
        if route.get("target_burden_id") != cycle.get("burden_id"):
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                f"route target {route.get('target_burden_id')!r} does not match cycle burden {cycle.get('burden_id')!r}")]
        for row, field, identity in ((route, "event_sha256", f"cycle {cycle_id} route"),):
            errors = _v2_event_hash_error(label, "04", "act_body_evidence", "operation-capsule-join", row, field, identity)
            if errors: return errors
        expected_route_record = canonical_json_sha256({key: route[key] for key in ("record_id", "target_burden_id", "source_refs", "basis_refs")})
        if route.get("record_sha256") != expected_route_record:
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join", "route record_sha256 mismatch")]
        event_rows = cycle.get("operation_events", [])
        expected_capsules = [row.get("capsule_id") for row in payload.get("operation_capsules", []) if row.get("cycle_id") == cycle_id]
        if cycle.get("operation_capsule_ids") != expected_capsules:
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                f"cycle {cycle_id} operation_capsule_ids do not match embedded operations")]
        expected_obligations = [obligation_id for capsule_id in expected_capsules for obligation_id in operations[capsule_id].get("obligation_ids", [])]
        if cycle.get("obligation_ids") != expected_obligations:
            return [_v2_diag(label, "03", "owner-obligation-coverage", "obligation-universe-hash",
                f"cycle {cycle_id} obligation_ids do not equal its obligation universe")]
        expected_kinds = ["before_state", "owner.operation", "performed_evidence", "local_delta", "residual", "land_contribution"]
        if len(event_rows) != 6 * len(expected_capsules):
            return [_v2_diag(label, "04", "act_body_evidence", "performed-event-order",
                f"cycle {cycle_id} operation event cardinality does not equal six per capsule")]
        for ordinal, capsule_id in enumerate(expected_capsules):
            capsule = operations[capsule_id]
            group = event_rows[ordinal * 6:(ordinal + 1) * 6]
            expected_refs = [
                f"capsule:{capsule_id}#before_state",
                f"route:{capsule['obligation_ids'][0]}#owner.operation",
                f"capsule:{capsule_id}#performed_operation",
                f"capsule:{capsule_id}#delta",
                f"capsule:{capsule_id}#residual",
                f"capsule:{capsule_id}#land_contribution",
            ]
            if [row.get("sequence") for row in group] != list(range(1, 7)) or [row.get("kind") for row in group] != expected_kinds:
                return [_v2_diag(label, "04", "act_body_evidence", "performed-event-order",
                    "operation chronology must be before_state, owner.operation, performed_evidence, local_delta, residual, land_contribution")]
            if [row.get("ref") for row in group] != expected_refs or any(row.get("operation_capsule_id") != capsule_id for row in group):
                return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join",
                    f"operation events for {capsule_id} do not bind distinct state/delta/residual identities")]
            for row in group:
                errors = _v2_event_hash_error(label, "04", "act_body_evidence", "operation-capsule-join", row, "event_sha256", row["event_id"])
                if errors: return errors
        route_index = route["event_index"]
        operation_indices = [row["event_index"] for row in event_rows]
        if operation_indices and not (route_index < min(operation_indices) and operation_indices == sorted(operation_indices)):
            return [_v2_diag(label, "04", "act_body_evidence", "performed-event-order", "route must precede ordered operation events")]
        land = cycle["land"]
        if operation_indices and land["event_index"] <= max(operation_indices):
            return [_v2_diag(label, "04", "act_body_evidence", "land-before-operation", "Land event occurs before operation chronology completes")]
        if land.get("operation_capsule_ids") != expected_capsules or land.get("contribution_refs") != [f"capsule:{item}#land_contribution" for item in expected_capsules]:
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join", "Land does not join operation capsules/contributions")]
        expected_land_record = canonical_json_sha256({key: land[key] for key in ("record_id", "status", "operation_capsule_ids", "contribution_refs")})
        if land.get("record_sha256") != expected_land_record or land.get("event_sha256") != _v2_self_hash(land, "event_sha256"):
            return [_v2_diag(label, "04", "act_body_evidence", "operation-capsule-join", "Land record/event hash mismatch")]
        delta = cycle["post_land_delta"]
        if delta["event_index"] <= land["event_index"]:
            return [_v2_diag(label, "05", "mrp", "post-land-order", "post-Land delta event_index must be after Land")]
        if delta.get("source_land_event_id") != land.get("event_id") or delta.get("source_operation_capsule_ids") != expected_capsules:
            return [_v2_diag(label, "05", "mrp", "post-land-order", "post-Land delta references do not join Land/operation capsules")]
        expected_delta = canonical_json_sha256({key: delta[key] for key in ("delta_id", "source_land_event_id", "source_operation_capsule_ids", "basis_refs")})
        if delta.get("delta_sha256") != expected_delta or delta.get("event_sha256") != _v2_self_hash(delta, "event_sha256"):
            return [_v2_diag(label, "05", "mrp", "post-land-order", "post-Land delta hash mismatch")]
        reread = cycle["reread"]
        raw = reread["raw_exit"]
        if reread.get("source_land_event_id") != land.get("event_id") or reread.get("source_delta_event_id") != delta.get("event_id"):
            return [_v2_diag(label, "05", "mrp", "post-land-order", "reread does not reference Land and post-Land delta")]
        post_rows: list[tuple[int, str]] = []
        for candidate in raw.get("candidate_events", []):
            if candidate.get("candidate_event_sha256") != _v2_self_hash(candidate, "candidate_event_sha256"):
                return [_v2_diag(label, "05", "mrp", "candidate-transition-invalid", f"candidate event {candidate.get('candidate_event_id')} hash mismatch")]
            event_id = str(candidate.get("candidate_event_id"))
            if event_id in candidate_events_by_id:
                return [_v2_diag(label, "05", "mrp", "candidate-transition-invalid", f"duplicate candidate_event_id {event_id!r}")]
            previous = candidate.get("previous_candidate_event_id")
            if previous is not None and previous not in candidate_events_by_id:
                return [_v2_diag(label, "05", "mrp", "candidate-transition-invalid", f"candidate event {event_id} previous ID {previous!r} is unresolved")]
            candidate_events_by_id[event_id] = candidate
            post_rows.append((candidate["event_index"], event_id))
            if candidate.get("next_cycle_id") in cycles_by_id:
                extra_edges.append({"from": event_id, "to": cycles_by_id[candidate["next_cycle_id"]]["route_gradient"]["event_id"]})
        for diagnostic in raw.get("field_diagnostics", []):
            if diagnostic.get("event_sha256") != _v2_self_hash(diagnostic, "event_sha256"):
                return [_v2_diag(label, "05", "mrp", "post-land-order", f"diagnostic {diagnostic.get('diagnostic_id')} event hash mismatch")]
            post_rows.append((diagnostic["event_index"], diagnostic["diagnostic_id"]))
        graph = raw.get("noetic_dependency_graph")
        errors = _v2_graph_hash_error(label, graph, "noetic dependency graph")
        if errors: return errors
        loop = raw.get("loopbreak")
        if loop is not None:
            for key in ("pre_break_graph", "post_break_graph"):
                errors = _v2_graph_hash_error(label, loop[key], key)
                if errors: return errors
            post = loop["post_break_reread"]
            for diagnostic in post.get("field_diagnostics", []):
                if diagnostic.get("event_sha256") != _v2_self_hash(diagnostic, "event_sha256"):
                    return [_v2_diag(label, "05", "mrp", "incomplete-loopbreak", "LoopBreak post-reread diagnostic hash mismatch")]
                post_rows.append((diagnostic["event_index"], diagnostic["diagnostic_id"]))
            if post.get("record_sha256") != _v2_self_hash(post, "record_sha256") or loop.get("loopbreak_sha256") != _v2_self_hash(loop, "loopbreak_sha256"):
                return [_v2_diag(label, "05", "mrp", "incomplete-loopbreak", "LoopBreak reread or evidence hash mismatch")]
            post_rows.extend([(loop["observed_loop_event_index"], f"{loop['loopbreak_id']}:observed"),
                (loop["interruption_event_index"], f"{loop['loopbreak_id']}:interruption"),
                (post["event_index"], f"{loop['loopbreak_id']}:reread")])
        if any(index <= delta["event_index"] for index, _ in post_rows) or raw["event_index"] <= max([delta["event_index"]] + [i for i, _ in post_rows]):
            return [_v2_diag(label, "05", "mrp", "post-land-order",
                "candidate/diagnostic/LoopBreak events must follow post-Land delta and precede exactly one raw exit")]
        if raw.get("exit_disposition") == "STOP" and not isinstance(raw.get("no_new_resultant"), dict):
            return [_v2_diag(label, "05", "mrp", "raw-exit-cardinality", "STOP requires a hash-bound no_new_resultant")]
        if isinstance(raw.get("no_new_resultant"), dict) and raw["no_new_resultant"].get("sha256") != _v2_self_hash(raw["no_new_resultant"], "sha256"):
            return [_v2_diag(label, "05", "mrp", "raw-exit-cardinality", "no_new_resultant hash mismatch")]
        if raw.get("raw_exit_sha256") != _v2_self_hash(raw, "raw_exit_sha256") or reread.get("record_sha256") != _v2_self_hash(reread, "record_sha256"):
            return [_v2_diag(label, "05", "mrp", "raw-exit-cardinality", "raw exit or reread hash mismatch")]
        if cycle.get("cycle_sha256") != _v2_self_hash(cycle, "cycle_sha256"):
            return [_v2_diag(label, "05", "state-capsule-custody", "replay-history-mutation", f"cycle {cycle_id} cycle_sha256 mismatch")]
        event_pairs = [(route["event_index"], route["event_id"])] + [(row["event_index"], row["event_id"]) for row in event_rows]
        event_pairs += [(land["event_index"], land["event_id"]), (delta["event_index"], delta["event_id"])] + post_rows + [(raw["event_index"], raw["event_id"])]
        indexed_nodes.extend(event_pairs)
        all_indices.extend(index for index, _ in event_pairs)
        all_event_ids.extend(identity for _, identity in event_pairs)
    duplicate_index = _v2_duplicate(all_indices)
    if duplicate_index is not None:
        return [_v2_diag(label, "05", "mrp", "post-land-order", f"global event_index {duplicate_index!r} is duplicated")]
    duplicate_event = _v2_duplicate(all_event_ids)
    if duplicate_event is not None:
        return [_v2_diag(label, "05", "mrp", "event-dag-cycle", f"global event identity {duplicate_event!r} is duplicated")]
    ordered = [identity for _, identity in sorted(indexed_nodes)]
    dag_edges = [{"from": ordered[index], "to": ordered[index + 1]} for index in range(len(ordered) - 1)] + extra_edges
    if _v2_has_cycle(ordered, dag_edges):
        return [_v2_diag(label, "05", "mrp", "event-dag-cycle",
            "provenance/event DAG is cyclic; noetic dependency graph cycles remain allowed")]
    return []


def _a07_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _v2_reducer_errors(label: str, payload: dict[str, Any]) -> list[str]:
    expected_policy_hash = _a07_hash({key:value for key,value in payload["resource_policy"].items() if key != "policy_sha256"})
    if payload["resource_policy"].get("policy_sha256") != expected_policy_hash:
        return [_v2_diag(label, "preflight", "mrp", "resource-policy-hash-mismatch",
            f"resource_policy policy_sha256 mismatch; expected {expected_policy_hash}")]
    if not payload["burden_cycles"]:
        if payload["reread_signature_history"] or payload["reread_signature_history_sha256"] != canonical_json_sha256([]):
            return [_v2_diag(label, "05", "mrp", "reread-signature-history", "empty cycle sequence requires an empty hash-bound reread history")]
        return []
    state = validate_lifecycle_record(payload, release_bearing=True)
    if not state.valid:
        finding = state.findings[0]
        subcode = "reread-signature-mismatch" if finding.subcode == "state_v2_reread_signature_mismatch" else finding.subcode
        return [_v2_diag(label, "05", finding.failure_class, subcode, finding.message)]
    capsules = _v2_map(payload["operation_capsules"], "capsule_id")
    cycles = _v2_map(payload["burden_cycles"], "cycle_id")
    expected_history: list[dict[str, Any]] = []
    for cycle_id, event_id, a07_signature in state.reread_signature_history:
        cycle = cycles[cycle_id]
        signature = canonical_json_sha256({
            "a07_reducer_signature_sha256":a07_signature,
            "performed_operation_capsule_sha256s":[capsules[value]["operation_capsule_sha256"] for value in cycle["operation_capsule_ids"]],
            "land_record_sha256":cycle["land"]["record_sha256"], "land_event_sha256":cycle["land"]["event_sha256"],
            "post_land_delta_sha256":cycle["post_land_delta"]["delta_sha256"], "post_land_delta_event_sha256":cycle["post_land_delta"]["event_sha256"],
        })
        expected_history.append({"cycle_id":cycle_id,"raw_exit_event_id":event_id,"a07_reducer_signature_sha256":a07_signature,"reread_signature_sha256":signature})
        reread = cycle["reread"]
        if reread.get("a07_reducer_signature_sha256") != a07_signature or reread.get("reread_signature_sha256") != signature:
            return [_v2_diag(label, "05", "mrp", "reread-signature-mismatch",
                f"cycle {cycle_id} reread signature does not bind A07 state plus performed operation, Land, and post-Land delta")]
    if payload.get("reread_signature_history") != expected_history or payload.get("reread_signature_history_sha256") != canonical_json_sha256(expected_history):
        return [_v2_diag(label, "05", "mrp", "reread-signature-history",
            "reread_signature_history is not the exact ordered delta-sensitive reducer projection")]
    return []


def _v2_event_dag(payload: dict[str, Any]) -> dict[str, Any]:
    indexed: list[tuple[int, str]] = [(payload["stage02_freeze"]["event_index"], payload["stage02_freeze"]["record_id"])]
    extra_edges: list[dict[str, str]] = []
    cycles = _v2_map(payload.get("burden_cycles"), "cycle_id")
    for cycle in payload.get("burden_cycles", []):
        indexed.append((cycle["route_gradient"]["event_index"], cycle["route_gradient"]["event_id"]))
        indexed.extend((row["event_index"], row["event_id"]) for row in cycle.get("operation_events", []))
        indexed.append((cycle["land"]["event_index"], cycle["land"]["event_id"]))
        indexed.append((cycle["post_land_delta"]["event_index"], cycle["post_land_delta"]["event_id"]))
        raw = cycle["reread"]["raw_exit"]
        indexed.extend((row["event_index"], row["candidate_event_id"]) for row in raw.get("candidate_events", []))
        indexed.extend((row["event_index"], row["diagnostic_id"]) for row in raw.get("field_diagnostics", []))
        loop = raw.get("loopbreak")
        if loop:
            indexed.extend([(loop["observed_loop_event_index"], f"{loop['loopbreak_id']}:observed"),
                (loop["interruption_event_index"], f"{loop['loopbreak_id']}:interruption"),
                (loop["post_break_reread"]["event_index"], f"{loop['loopbreak_id']}:reread")])
            indexed.extend((row["event_index"], row["diagnostic_id"]) for row in loop["post_break_reread"].get("field_diagnostics", []))
        indexed.append((raw["event_index"], raw["event_id"]))
        for candidate in raw.get("candidate_events", []):
            target = cycles.get(str(candidate.get("next_cycle_id")))
            if target:
                extra_edges.append({"from": candidate["candidate_event_id"], "to": target["route_gradient"]["event_id"]})
    ordered = [identity for _, identity in sorted(indexed)]
    return {"nodes": ordered, "edges": [{"from": ordered[index], "to": ordered[index + 1]} for index in range(len(ordered) - 1)] + extra_edges}


def _v2_projection_values(payload: dict[str, Any]) -> dict[str, str | None]:
    stage_number = V2_STAGE_INDEX[str(payload["stage"])] + 1
    b_mrp = [cycle["burden_id"] for cycle in payload["burden_cycles"] if cycle["origin"] == "B_MRP"]
    stage04 = {"upstream_obligation_ids": payload["upstream_obligation_ids"], "owner_routes": payload["owner_routes"],
        "act_row_details": payload["act_row_details"], "owner_execution_dispositions": payload["owner_execution_dispositions"],
        "owner_obligation_state": payload["owner_obligation_state"], "operation_capsules": payload["operation_capsules"],
        "operation_events": [event for cycle in payload["burden_cycles"] for event in cycle.get("operation_events", [])]}
    stage05 = {"burden_cycles": payload["burden_cycles"]}
    reducer = {"B_LA": payload["stage02_freeze"]["B_LA"], "B_MRP": b_mrp,
        "current_live_burdens": payload["current_live_burdens"], "held": payload["held"], "closure_state": payload["closure_state"],
        "reread_signature_history": payload["reread_signature_history"]}
    dag = _v2_event_dag(payload)
    activation = {"owner_routes": payload["owner_routes"], "act_row_details": payload["act_row_details"],
        "owner_execution_dispositions": payload["owner_execution_dispositions"], "operation_capsules": payload["operation_capsules"],
        "burden_cycles": payload["burden_cycles"]}
    release = {"stage04": stage04, "stage05": stage05, "reducer": reducer, "event_dag": dag}
    public = {"trace_id": payload["trace_id"], "B_LA": payload["stage02_freeze"]["B_LA"], "B_MRP": b_mrp,
        "burden_cycles": payload["burden_cycles"], "closure_state": payload["closure_state"]}
    values: dict[str, str | None] = {
        "stage04_activation_projection_sha256": canonical_json_sha256(stage04) if stage_number >= 4 else None,
        "stage05_lifecycle_projection_sha256": canonical_json_sha256(stage05) if stage_number >= 5 else None,
        "reducer_state_sha256": canonical_json_sha256(reducer) if stage_number >= 5 else None,
        "event_dag_sha256": canonical_json_sha256(dag) if stage_number >= 5 else None,
        "activation_lifecycle_fingerprint_sha256": canonical_json_sha256(activation) if stage_number >= 4 else None,
        "stage06_projection_sha256": canonical_json_sha256(release) if stage_number >= 6 else None,
        "stage07_projection_sha256": canonical_json_sha256(release) if stage_number >= 7 else None,
        "public_field_witness_sha256": canonical_json_sha256(public) if stage_number >= 7 else None,
        "field_witness_envelope_sha256": None,
    }
    if stage_number >= 8:
        values["field_witness_envelope_sha256"] = canonical_json_sha256({
            "capsule_id": payload["capsule_id"], "source_commit": payload["source_commit"], "trace_id": payload["trace_id"],
            "public_field_witness_sha256": values["public_field_witness_sha256"],
            "activation_lifecycle_fingerprint_sha256": values["activation_lifecycle_fingerprint_sha256"],
        })
    return values


def _v2_closure_inputs(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Project state-v2 plus an independently derived upstream authority."""
    burdens = []
    lands = []
    rereads = []
    diagnostics = []
    loopbreak_owner: dict[str, Any] | None = None
    no_new: dict[str, Any] | None = None
    for cycle in payload.get("burden_cycles", []):
        burden = {"burden_id": cycle["burden_id"], "origin": cycle["origin"],
            "terminal_state": cycle["terminal_state"], "load_bearing": True}
        if cycle["terminal_state"] == "recurse":
            burden["next_action"] = "continue generated cycle"
        burdens.append(burden)
        reread = cycle.get("reread")
        if isinstance(reread, dict):
            rereads.append({"reread_id": reread["record_id"], "status": "evaluated", "post_break": bool(reread["raw_exit"].get("loopbreak"))})
            operations = _v2_map(payload.get("operation_capsules"), "capsule_id")
            lands.append({"burden_id": cycle["burden_id"], "reread_id": reread["record_id"],
                "body_refs": [operations[item]["body_ref"] for item in cycle.get("operation_capsule_ids", [])],
                "delta_ref": cycle["post_land_delta"]["delta_id"]})
            raw = reread["raw_exit"]
            diagnostics.extend(raw.get("field_diagnostics", []))
            if raw.get("exit_disposition") == "STOP" and isinstance(raw.get("no_new_resultant"), dict):
                no_new = {"stop_licensed": raw["no_new_resultant"].get("stop_licensed") is True,
                    "candidate_ids": list(raw["no_new_resultant"].get("unresolved_candidate_ids", []))}
            loop = raw.get("loopbreak")
            if isinstance(loop, dict):
                if diagnostics:
                    diagnostics[-1] = dict(diagnostics[-1])
                    diagnostics[-1]["dependency_refs"] = [loop["pre_break_graph"]["graph_id"]]
                loopbreak_owner = {
                    "loopbreak_id": loop["loopbreak_id"], "observed_loop_ref": loop["pre_break_graph"]["graph_id"],
                    "owner_ground_ref": loop["owner_ground_ref"]["id"],
                    "performed_operation_ref": loop["performed_operation_ref"]["id"],
                    "delta_ref": loop["local_delta_ref"]["delta_id"],
                    "post_break_graph_ref": loop["post_break_graph"]["graph_id"],
                    "full_reread_ref": loop["post_break_reread"]["record_id"],
                }
                rereads.append({"reread_id":loop["post_break_reread"]["record_id"],"status":"evaluated","post_break":True})
    if not diagnostics:
        closure = payload.get("closure_state", {})
        # Before Stage05, an unevaluated field is not evidence of a loop.
        diagnostics = [{"operator":"divergence","target":payload["trace_id"],"status":closure.get("divergence", "unknown"),"basis_refs":["opening-state"],"delta_ref":"none"},
            {"operator":"curl","target":payload["trace_id"],"status":"null" if not burdens else closure.get("curl", "unknown"),"basis_refs":["opening-state"],"delta_ref":"none"}]
    candidates = [{"candidate_id": row["state_id"], "status": row["status"], "basis": row["basis"]}
                  for row in payload.get("candidate_states", [])]
    all_body_refs = [row["body_ref"] for row in payload.get("operation_capsules", [])]
    dispositions = [{"obligation_id":row["obligation_id"],"disposition":row["disposition"],"basis":row["basis"]}
                    for row in payload.get("owner_execution_dispositions", [])]
    burdens = list({row["burden_id"]: row for row in burdens}.values())
    lands = list({row["burden_id"]: row for row in lands}.values())
    if lands:
        current_delta_refs = {row["delta_ref"] for row in lands}
        diagnostics = [row for row in diagnostics if row.get("delta_ref") in current_delta_refs]
    transitions = ["INTAKE", "OPEN"]
    if payload.get("burden_cycles"):
        transitions.append("REREAD_EVALUATED")
    if any(cycle.get("reread", {}).get("raw_exit", {}).get("exit_disposition") == "RECURSE" for cycle in payload.get("burden_cycles", [])):
        transitions.append("RECURSE")
    raw_exit = payload.get("burden_cycles", [{}])[-1].get("reread", {}).get("raw_exit", {}).get("exit_disposition") if payload.get("burden_cycles") else None
    post_break_graphs = [{"graph_id":cycle["reread"]["raw_exit"]["loopbreak"]["post_break_graph"]["graph_id"]}
                         for cycle in payload.get("burden_cycles", []) if isinstance(cycle.get("reread", {}).get("raw_exit", {}).get("loopbreak"), dict)]
    trace = {"opening":{"opening_state_contract":"opening-state-v2","phase":"ENTRY","state":"OPEN","closure_claim":"PENDING","trace_id":payload["trace_id"]},
        "transitions":transitions, "raw_exit_disposition":raw_exit, "proposed_closure_claim":None,
        "burdens": burdens, "candidate_states": candidates, "owner_obligations": dispositions,
        "diagnostics": diagnostics, "lands": lands, "rereads": rereads, "no_new_resultant": no_new,
        "loopbreak": loopbreak_owner, "post_break_graphs":post_break_graphs,
        "witness": {"body_refs": all_body_refs}, "render_order": FINAL_RENDER_ORDER}
    authority = {
        "burden_ids": list(dict.fromkeys(payload.get("stage02_freeze", {}).get("B_LA", []) + [cycle["burden_id"] for cycle in payload.get("burden_cycles", []) if cycle.get("origin") == "B_MRP"])),
        "candidate_state_ids": [row["state_id"] for row in payload.get("candidate_states", [])],
        "owner_obligation_ids": [row["obligation_id"] for row in payload.get("owner_routes", [])],
    }
    return trace, authority, canonical_universe_sha256(authority)


def _v2_owner_closure_decision(payload: dict[str, Any]) -> str:
    trace, upstream_universe, upstream_inventory_sha256 = _v2_closure_inputs(payload)
    owned = derive_closure_decision(
        trace,
        upstream_universe=upstream_universe,
        upstream_inventory_sha256=upstream_inventory_sha256,
    )
    build_closure_witness_projection(
        trace,
        upstream_universe=upstream_universe,
        upstream_inventory_sha256=upstream_inventory_sha256,
    )
    stage_number = V2_STAGE_INDEX[str(payload["stage"])] + 1
    return "CLOSURE_CANDIDATE" if owned == "COMPLETE" and stage_number < 7 else owned


def _v2_lifecycle_and_closure_errors(label: str, payload: dict[str, Any]) -> list[str]:
    lifecycle_pairs = {
        "candidate": {"open"}, "active": {"open"}, "generated": {"open", "recurse"},
        "recurse": {"recurse"}, "held": {"held"}, "partial": {"partial"},
        "preempted": {"preempted"}, "landed": {"landed"},
    }
    for cycle in payload.get("burden_cycles", []):
        if cycle.get("terminal_state") not in lifecycle_pairs.get(str(cycle.get("lifecycle_status")), set()):
            return [_v2_diag(label, "05", "state-capsule-custody", "derived-live-held-mismatch",
                f"cycle {cycle.get('cycle_id')} lifecycle_status {cycle.get('lifecycle_status')!r} conflicts with terminal_state {cycle.get('terminal_state')!r}")]
    derived_live = [cycle["burden_id"] for cycle in payload.get("burden_cycles", []) if cycle.get("terminal_state") in {"open", "recurse", "held", "partial"}]
    expected_held: set[tuple[str, str]] = set()
    expected_held |= {("candidate", row["state_id"]) for row in payload.get("candidate_states", []) if row.get("status") in {"held", "underdetermined"}}
    expected_held |= {("pressure", row["pressure_id"]) for row in payload.get("input_pressures", []) if row.get("status") in {"held", "unresolved"}}
    expected_held |= {("burden", row["burden_id"]) for row in payload.get("burden_cycles", []) if row.get("terminal_state") in {"held", "partial"}}
    expected_held |= {("obligation", row["obligation_id"]) for row in payload.get("owner_execution_dispositions", []) if row.get("disposition") in {"held", "partial"}}
    expected_held |= {("candidate", row["candidate_id"]) for cycle in payload.get("burden_cycles", [])
                      for row in cycle.get("reread", {}).get("raw_exit", {}).get("candidate_events", [])
                      if row.get("disposition") in {"defer_preempted", "hold_partial"}}
    actual_held = {(str(row.get("kind")), str(row.get("item_id"))) for row in payload.get("held", [])}
    if payload.get("current_live_burdens") != derived_live or actual_held != expected_held:
        cycle_projection = [(row.get("burden_id"), row.get("lifecycle_status"), row.get("terminal_state"))
                            for row in payload.get("burden_cycles", [])]
        return [_v2_diag(label, "05", "state-capsule-custody", "derived-live-held-mismatch",
            f"current_live_burdens/held are not exact projections; actual live={payload.get('current_live_burdens')!r}, "
            f"actual held={sorted(actual_held)!r}, live expected {derived_live!r}, held expected {sorted(expected_held)!r}; "
            f"lifecycle_status/terminal_state rows={cycle_projection!r}")]
    expected_open = set(derived_live) | {item_id for kind, item_id in expected_held if kind != "burden"}
    closure = payload.get("closure_state", {})
    if set(closure.get("remaining_open_ids", [])) != expected_open:
        return [_v2_diag(label, "07", "public-projection", "coverage-predicate-mismatch",
            f"remaining_open_ids must equal live/held projection {sorted(expected_open)!r}; got {closure.get('remaining_open_ids')!r}")]
    coverage_complete = not payload.get("input_coverage", {}).get("unaccounted_unit_ids")
    trace, upstream_universe, upstream_inventory_sha256 = _v2_closure_inputs(payload)
    expected_authority = dict(upstream_universe)
    expected_authority["inventory_sha256"] = upstream_inventory_sha256
    if payload.get("closure_authority") != expected_authority:
        return [_v2_diag(label, "02", "topology-accounting", "closure-universe-source-mismatch",
            "closure_authority is not the exact independently recomputed Stage02/cycle/Plan04 universe")]
    try:
        owner_raw_decision = derive_closure_decision(
            trace,
            upstream_universe=upstream_universe,
            upstream_inventory_sha256=upstream_inventory_sha256,
        )
    except ClosureUniverseAuthorityError as exc:
        finding = exc.finding
        return [_v2_diag(label, finding["earliest_stage"], finding["failure_class"], finding["failure_subcode"], finding["message"])]
    validation_trace = dict(trace)
    validation_trace["proposed_closure_claim"] = owner_raw_decision
    validation_trace["transitions"] = list(trace["transitions"])
    if owner_raw_decision == "COMPLETE":
        validation_trace["transitions"].extend(["CLOSURE_CANDIDATE", "CLOSURE_CONFIRMED"])
    validation_trace["coverage"] = {
        "initial_coverage_complete": closure.get("initial_coverage_complete"),
        "lifecycle_accounting_complete": closure.get("lifecycle_accounting_complete"),
        "collapse_positive": owner_raw_decision == "COMPLETE",
        "closure_confirmed": True,
    }
    closure_findings = validate_closure_trace(validation_trace, upstream_universe=upstream_universe,
        upstream_inventory_sha256=upstream_inventory_sha256)
    if closure_findings:
        finding = closure_findings[0]
        return [_v2_diag(label, finding["earliest_stage"], finding["failure_class"], finding["failure_subcode"], finding["message"])]
    try:
        derived_decision = _v2_owner_closure_decision(payload)
    except ClosureUniverseAuthorityError as exc:
        finding = exc.finding
        return [_v2_diag(label, finding["earliest_stage"], finding["failure_class"], finding["failure_subcode"], finding["message"])]
    expected_closure = {
        "opening_state": "OPEN", "opening_closure_claim": "PENDING", "derived_decision": derived_decision,
        "initial_coverage_complete": coverage_complete, "lifecycle_accounting_complete": True,
        "collapse_positive": derived_decision == "COMPLETE", "closure_confirmed": derived_decision == "COMPLETE",
        "remaining_open_ids": closure.get("remaining_open_ids"), "divergence": closure.get("divergence"),
        "curl": closure.get("curl"), "loopbreak": closure.get("loopbreak"),
    }
    predicate_fields = ("opening_state", "opening_closure_claim", "initial_coverage_complete", "lifecycle_accounting_complete",
        "collapse_positive", "closure_confirmed")
    mismatch = [field for field in predicate_fields if closure.get(field) != expected_closure[field]]
    if mismatch:
        return [_v2_diag(label, "07", "public-projection", "coverage-predicate-mismatch",
            f"closure coverage predicates mismatch derived values for {mismatch!r}")]
    if closure.get("derived_decision") != derived_decision:
        return [_v2_diag(label, "07", "public-projection", "producer-oracle-mismatch",
            f"producer asserted {closure.get('derived_decision')!r}; derived Stage07 oracle yields {derived_decision}")]
    return []


def _v2_projection_errors(label: str, payload: dict[str, Any]) -> list[str]:
    expected = _v2_projection_values(payload)
    actual = payload.get("projection", {})
    stage_number = V2_STAGE_INDEX[str(payload["stage"])] + 1
    for field, expected_hash in expected.items():
        if actual.get(field) != expected_hash:
            if field == "public_field_witness_sha256":
                return [_v2_diag(label, "07", "witness-binding", "public-witness-hash-missing",
                    f"{field} does not equal the recomputed public witness-role hash {expected_hash}")]
            stage = "08" if field == "field_witness_envelope_sha256" else ("07" if stage_number >= 7 else "06")
            failure_class = "witness-binding" if field == "field_witness_envelope_sha256" else "projection-parity"
            subcode = "field-witness-envelope-hash" if field == "field_witness_envelope_sha256" else "projection-hash-mismatch"
            return [_v2_diag(label, stage, failure_class, subcode, f"{field} mismatch; expected {expected_hash}")]
    expected_refs = [{"id": "context-stage", "sha256": "7" * 64}]
    if stage_number >= 7:
        expected_refs.append({"id": "public-field-witness", "sha256": expected["public_field_witness_sha256"]})
    if stage_number >= 8:
        expected_refs.append({"id": "field-witness-envelope", "sha256": expected["field_witness_envelope_sha256"]})
    if payload.get("runtime_call_context_refs") != expected_refs:
        return [_v2_diag(label, "08" if stage_number >= 8 else "07", "witness-binding", "witness-context-reference",
            "runtime_call_context_refs do not equal the stage-specific witness-role bindings")]
    return []


def validate_v2_capsule_payload(label: str, payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label}: state-capsule-v2 must be a JSON object"]
    errors = _v2_control_preflight_errors(label, payload)
    if errors:
        return errors
    errors = json_schema_errors(label, payload, load_v2_schema())
    if errors:
        return errors
    for validator in (
        _v2_topology_errors,
        _v2_obligation_errors,
        _v2_operation_errors,
        _v2_cycle_errors,
        _v2_reducer_errors,
        _v2_topology_mass_errors,
        _v2_lifecycle_and_closure_errors,
        _v2_projection_errors,
    ):
        errors = validator(label, payload)
        if errors:
            return errors
    return []


def validate_capsule_payload_dispatch(label: str, payload: Any, *, release_bearing: bool = False) -> list[str]:
    identity = payload.get("schema") if isinstance(payload, dict) else None
    if identity == SCHEMA_CONST:
        if release_bearing:
            return [
                _v2_diag(label, "preflight", "release-bearing-v1", "release-bearing-v1",
                    f"{SCHEMA_CONST} is historical replay only; new release-bearing execution requires {SCHEMA_V2_CONST}")
            ]
        return validate_capsule_payload(label, payload, load_schema())
    if identity == SCHEMA_V2_CONST:
        return validate_v2_capsule_payload(label, payload)
    return [
        f"{label}: unsupported-schema-identity: expected {SCHEMA_CONST!r} or {SCHEMA_V2_CONST!r}, got {identity!r}"
    ]


def validate_capsule_file_dispatch(path: Path, *, release_bearing: bool = False) -> list[str]:
    payload, errors = load_json(path)
    if errors:
        return errors
    label = rel(path)
    errors = validate_capsule_payload_dispatch(label, payload, release_bearing=release_bearing)
    raw_bytes = path.read_bytes()
    if isinstance(payload, dict) and payload.get("schema") == SCHEMA_V2_CONST:
        if len(raw_bytes) > WARN_BYTES:
            print(
                f"  WARNING: {label}: v2 capsule is {len(raw_bytes)} bytes; size is telemetry only and "
                "must not act as a semantic topology limit"
            )
    else:
        warnings, failures = capsule_size_errors(label, raw_bytes)
        for warning in warnings:
            print(f"  WARNING: {warning}")
        errors.extend(failures)
    return errors


# ---------------------------------------------------------------------------
# Structural (schema) validation
# ---------------------------------------------------------------------------

def schema_required_optional(schema: dict[str, Any]) -> tuple[set[str], set[str]]:
    required = set(schema.get("required", []))
    optional = set(schema.get("properties", {})) - required
    return required, optional


def _type_ok(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_type_ok(value, item) for item in expected)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def structural_errors(label: str, payload: Any, schema: dict[str, Any]) -> list[str]:
    """Pure core: validate `payload` is a well-shaped capsule per the schema's
    top-level contract. Deliberately hand-rolled (no jsonschema dependency)
    mirroring tools/check_collapse_certificate_schema.py's local style."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{label}: capsule must be a JSON object"]

    required, optional = schema_required_optional(schema)
    allowed = required | optional
    keys = set(payload)

    missing = sorted(required - keys)
    if missing:
        errors.append(f"{label}: missing required field(s): {missing}")
    unknown = sorted(keys - allowed)
    if unknown:
        errors.append(f"{label}: unknown top-level field(s) (additionalProperties=false): {unknown}")

    if payload.get("schema") != SCHEMA_CONST:
        errors.append(f"{label}: schema must be {SCHEMA_CONST!r}, got {payload.get('schema')!r}")

    if "case_id" in payload and not (isinstance(payload["case_id"], str) and payload["case_id"]):
        errors.append(f"{label}: case_id must be a non-empty string")

    fp = payload.get("input_fingerprint")
    if "input_fingerprint" in payload and not (isinstance(fp, str) and FINGERPRINT_RE.match(fp)):
        errors.append(f"{label}: input_fingerprint must match sha256:<64 hex>")

    stage = payload.get("stage")
    if "stage" in payload and stage not in STAGE_INDEX:
        errors.append(f"{label}: stage must be one of {STAGE_ORDER}, got {stage!r}")

    errors.extend(_n_frame_errors(label, payload.get("n_frame")))
    errors.extend(_live_registers_errors(label, payload.get("live_registers")))

    if "register_state" in payload and not isinstance(payload["register_state"], dict):
        errors.append(f"{label}: register_state must be an object")

    for key in ("B_LA", "B_MRP", "B_total", "cold_law_refs_used", "shards_loaded"):
        if key in payload:
            errors.extend(_string_array_errors(label, key, payload[key]))

    errors.extend(_held_set_errors(label, payload.get("held_set_H")))
    errors.extend(_completed_acts_errors(label, payload.get("completed_acts")))
    errors.extend(_last_terminal_errors(label, payload.get("last_terminal")))

    if "last_delta" in payload and not (payload["last_delta"] is None or isinstance(payload["last_delta"], str)):
        errors.append(f"{label}: last_delta must be a string or null")

    errors.extend(_last_mrp_resultant_errors(label, payload.get("last_mrp_resultant")))

    rrt = payload.get("route_result_type")
    if "route_result_type" in payload and rrt not in ROUTE_RESULT_TYPES:
        errors.append(f"{label}: route_result_type must be one of {sorted(ROUTE_RESULT_TYPES)}, got {rrt!r}")

    errors.extend(_field_diagnostics_errors(label, payload.get("field_diagnostics")))

    transport = payload.get("transport")
    if "transport" in payload and transport not in TRANSPORT_VALUES:
        errors.append(f"{label}: transport must be one of {sorted(TRANSPORT_VALUES)}, got {transport!r}")

    if "terminal_states" in payload and not isinstance(payload["terminal_states"], dict):
        errors.append(f"{label}: terminal_states must be an object")

    if "next_burden" in payload and not (payload["next_burden"] is None or isinstance(payload["next_burden"], str)):
        errors.append(f"{label}: next_burden must be a string or null")

    errors.extend(_current_owner_route_errors(label, payload.get("current_owner_route")))

    if "coverage_complete" in payload and not isinstance(payload["coverage_complete"], bool):
        errors.append(f"{label}: coverage_complete must be a boolean")

    nra = payload.get("next_required_action")
    if "next_required_action" in payload and not isinstance(nra, str):
        errors.append(f"{label}: next_required_action must be a string")
    elif isinstance(nra, str) and len(nra) > NEXT_REQUIRED_ACTION_MAX_LEN:
        errors.append(
            f"{label}: next_required_action is {len(nra)} chars, exceeds max {NEXT_REQUIRED_ACTION_MAX_LEN} "
            "(prose-smuggling bound)"
        )

    oap = payload.get("output_artifact_path")
    if "output_artifact_path" in payload and not (oap is None or isinstance(oap, str)):
        errors.append(f"{label}: output_artifact_path must be a string or null")

    osha = payload.get("output_sha256")
    if "output_sha256" in payload and not (osha is None or (isinstance(osha, str) and (osha == "" or SHA256_RE.match(osha)))):
        errors.append(f"{label}: output_sha256 must be a 64-hex sha256 string, empty string, or null")

    oob = payload.get("output_offset_bytes")
    if "output_offset_bytes" in payload and not (isinstance(oob, int) and not isinstance(oob, bool) and oob >= 0):
        errors.append(f"{label}: output_offset_bytes must be an integer >= 0")

    notes = payload.get("notes")
    if "notes" in payload and not isinstance(notes, str):
        errors.append(f"{label}: notes must be a string")
    elif isinstance(notes, str) and len(notes) > NOTES_MAX_LEN:
        errors.append(f"{label}: notes is {len(notes)} chars, exceeds max {NOTES_MAX_LEN} (prose-smuggling bound)")

    return errors


def _string_array_errors(label: str, key: str, value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return [f"{label}: {key} must be an array of non-empty strings"]
    return []


def _n_frame_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: n_frame must be an object"]
    errors: list[str] = []
    required = {"selected", "held_candidates"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: n_frame missing field(s): {missing}")
    unknown = sorted(set(value) - required)
    if unknown:
        errors.append(f"{label}: n_frame has unknown field(s): {unknown}")
    if "selected" in value and not (isinstance(value["selected"], str) and value["selected"]):
        errors.append(f"{label}: n_frame.selected must be a non-empty string")
    if "held_candidates" in value:
        errors.extend(_string_array_errors(label, "n_frame.held_candidates", value["held_candidates"]))
    return errors


def _live_registers_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        return [f"{label}: live_registers must be an array"]
    errors: list[str] = []
    if len(value) != len(set(value)):
        errors.append(f"{label}: live_registers must have unique entries")
    unknown = [item for item in value if item not in LIVE_REGISTER_TOKENS]
    if unknown:
        errors.append(f"{label}: live_registers has unrecognized register token(s): {unknown}")
    return errors


def _held_set_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        return [f"{label}: held_set_H must be an array"]
    errors: list[str] = []
    for index, entry in enumerate(value):
        item_label = f"{label}: held_set_H[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{item_label}: must be an object")
            continue
        required = {"burden", "reason"}
        missing = sorted(required - set(entry))
        if missing:
            errors.append(f"{item_label}: missing field(s): {missing}")
        unknown = sorted(set(entry) - required)
        if unknown:
            errors.append(f"{item_label}: unknown field(s): {unknown}")
        if "burden" in entry and not (isinstance(entry["burden"], str) and entry["burden"]):
            errors.append(f"{item_label}: burden must be a non-empty string")
        if "reason" in entry and not (isinstance(entry["reason"], str) and entry["reason"]):
            errors.append(f"{item_label}: reason must be a non-empty string")
    return errors


def _completed_acts_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        return [f"{label}: completed_acts must be an array"]
    errors: list[str] = []
    required = {"body_ref", "owner_id", "operation", "register_axis", "delta_result", "land"}
    for index, entry in enumerate(value):
        item_label = f"{label}: completed_acts[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{item_label}: must be an object")
            continue
        missing = sorted(required - set(entry))
        if missing:
            errors.append(f"{item_label}: missing field(s): {missing}")
        unknown = sorted(set(entry) - required)
        if unknown:
            errors.append(f"{item_label}: unknown field(s): {unknown}")
        for key in required:
            if key in entry and not (isinstance(entry[key], str) and entry[key]):
                errors.append(f"{item_label}.{key} must be a non-empty string")
        errors.extend(body_ref_pollution_errors(item_label, entry.get("body_ref")))
    return errors


def body_ref_pollution_errors(label: str, body_ref: Any) -> list[str]:
    """Pure core: body_ref must be a bare join key (no owner/operation
    pollution). Reject '[' anywhere, and reject '.' entirely since the bare
    burden/submove shape (B1, B1_1, superscript-prefixed forms) never uses '.'.
    """
    if not isinstance(body_ref, str) or not body_ref:
        return [f"{label}.body_ref must be a non-empty string"]
    if "[" in body_ref or "." in body_ref:
        return [f"{label}.body_ref {body_ref!r} is polluted with owner/operation syntax ('[' or '.')"]
    if not BODY_REF_RE.match(body_ref):
        return [f"{label}.body_ref {body_ref!r} is not a bare join key (expected form like 'B1_1')"]
    return []


def _last_terminal_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: last_terminal must be an object"]
    errors: list[str] = []
    required = {"burden", "state"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: last_terminal missing field(s): {missing}")
    unknown = sorted(set(value) - required)
    if unknown:
        errors.append(f"{label}: last_terminal has unknown field(s): {unknown}")
    for key in ("burden", "state"):
        if key in value and not (value[key] is None or isinstance(value[key], str)):
            errors.append(f"{label}: last_terminal.{key} must be a string or null")
    return errors


def _last_mrp_resultant_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: last_mrp_resultant must be an object"]
    errors: list[str] = []
    required = {"source", "route_result_type"}
    optional = {"generated_by", "next_burden"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: last_mrp_resultant missing field(s): {missing}")
    unknown = sorted(set(value) - required - optional)
    if unknown:
        errors.append(f"{label}: last_mrp_resultant has unknown field(s): {unknown}")
    if "source" in value and not (value["source"] is None or isinstance(value["source"], str)):
        errors.append(f"{label}: last_mrp_resultant.source must be a string or null")
    rrt = value.get("route_result_type")
    if "route_result_type" in value and rrt not in ROUTE_RESULT_TYPES:
        errors.append(f"{label}: last_mrp_resultant.route_result_type must be one of {sorted(ROUTE_RESULT_TYPES)}")
    if "generated_by" in value and not (isinstance(value["generated_by"], str) and value["generated_by"]):
        errors.append(f"{label}: last_mrp_resultant.generated_by must be a non-empty string")
    if "next_burden" in value and not (value["next_burden"] is None or isinstance(value["next_burden"], str)):
        errors.append(f"{label}: last_mrp_resultant.next_burden must be a string or null")
    return errors


def _field_diagnostics_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: field_diagnostics must be an object"]
    errors: list[str] = []
    required = {"divergence_state", "curl_state"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: field_diagnostics missing field(s): {missing}")
    unknown = sorted(set(value) - required)
    if unknown:
        errors.append(f"{label}: field_diagnostics has unknown field(s): {unknown}")
    if "divergence_state" in value and value["divergence_state"] not in DIVERGENCE_STATES:
        errors.append(f"{label}: field_diagnostics.divergence_state must be one of {sorted(DIVERGENCE_STATES)}")
    if "curl_state" in value and value["curl_state"] not in CURL_STATES:
        errors.append(f"{label}: field_diagnostics.curl_state must be one of {sorted(CURL_STATES)}")
    return errors


def _current_owner_route_errors(label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: current_owner_route must be an object"]
    errors: list[str] = []
    required = {"burden", "owner_id", "shards"}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label}: current_owner_route missing field(s): {missing}")
    unknown = sorted(set(value) - required)
    if unknown:
        errors.append(f"{label}: current_owner_route has unknown field(s): {unknown}")
    for key in ("burden", "owner_id"):
        if key in value and not (value[key] is None or isinstance(value[key], str)):
            errors.append(f"{label}: current_owner_route.{key} must be a string or null")
    if "shards" in value:
        errors.extend(_string_array_errors(label, "current_owner_route.shards", value["shards"]))
    return errors


# ---------------------------------------------------------------------------
# Semantic invariants (single capsule)
# ---------------------------------------------------------------------------

def semantic_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: cross-field invariants a schema alone can't express."""
    errors: list[str] = []

    b_la = payload.get("B_LA")
    b_mrp = payload.get("B_MRP")
    b_total = payload.get("B_total")
    if isinstance(b_la, list) and isinstance(b_mrp, list) and isinstance(b_total, list):
        errors.extend(union_errors(label, b_la, b_mrp, b_total))

    current_burden = payload.get("current_burden")
    if isinstance(b_total, list) and isinstance(current_burden, str) and current_burden:
        if current_burden not in b_total:
            last_terminal = payload.get("last_terminal") or {}
            is_terminal = isinstance(last_terminal, dict) and last_terminal.get("burden") == current_burden
            if not is_terminal:
                errors.append(
                    f"{label}: current_burden {current_burden!r} is not in B_total and is not "
                    "the explicit last_terminal burden"
                )

    next_burden = payload.get("next_burden")
    if isinstance(b_total, list) and isinstance(next_burden, str) and next_burden:
        if next_burden not in b_total:
            terminal_states = payload.get("terminal_states") or {}
            explicitly_terminal = isinstance(terminal_states, dict) and next_burden in terminal_states
            if not explicitly_terminal:
                errors.append(f"{label}: next_burden {next_burden!r} is not in B_total or explicitly terminal")

    errors.extend(mrp_provenance_errors(label, payload))
    errors.extend(coverage_complete_errors(label, payload))
    errors.extend(partial_hold_errors(label, payload))
    errors.extend(output_artifact_errors(label, payload))
    errors.extend(register_state_fidelity_errors(label, payload))

    return errors


def register_state_fidelity_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core (FIX 4): every live_registers entry (alias-normalized) except
    N/m/H must have a key in register_state, else the capsule is claiming a
    register is live without ever recording what its state is. N is carried
    by n_frame; m/H are carried by dedicated capsule fields; those three are
    exempt from needing their own register_state entry."""
    live_registers = payload.get("live_registers")
    register_state = payload.get("register_state")
    if not isinstance(live_registers, list) or not isinstance(register_state, dict):
        return []
    register_state_canonical_keys = {
        REGISTER_TOKEN_CANONICAL.get(str(key), str(key)) for key in register_state
    }
    errors: list[str] = []
    for raw in live_registers:
        if not isinstance(raw, str):
            continue
        canonical = REGISTER_TOKEN_CANONICAL.get(raw, raw)
        if canonical in REGISTER_STATE_EXEMPT_CANONICAL:
            continue
        if canonical not in register_state_canonical_keys:
            errors.append(
                f"{label}: live register {raw!r} has no register_state entry "
                "(live register without register_state entry)"
            )
    return errors


def union_errors(label: str, b_la: list[Any], b_mrp: list[Any], b_total: list[Any]) -> list[str]:
    """Pure core: B_total must equal the order-preserving union of B_LA and
    B_MRP with no duplicates (B_LA entries first in their order, then any
    B_MRP entries not already present, in their order)."""
    errors: list[str] = []
    if len(set(b_la)) != len(b_la):
        errors.append(f"{label}: B_LA contains duplicate entries")
    if len(set(b_mrp)) != len(b_mrp):
        errors.append(f"{label}: B_MRP contains duplicate entries")
    if len(set(b_total)) != len(b_total):
        errors.append(f"{label}: B_total contains duplicate entries")

    expected: list[Any] = []
    seen: set[Any] = set()
    for burden in list(b_la) + list(b_mrp):
        if burden not in seen:
            expected.append(burden)
            seen.add(burden)
    if b_total != expected:
        errors.append(
            f"{label}: B_total {b_total!r} is not the order-preserving union of B_LA and B_MRP "
            f"(expected {expected!r})"
        )
    return errors


def mrp_provenance_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: every B_MRP entry must have MRP provenance -- either a
    matching completed_acts entry (via body_ref burden prefix) whose act
    chain is backed by a generated_burden_instantiation resultant, or the
    capsule's own last_mrp_resultant naming it via generated_by/next_burden
    with route_result_type generated_burden_instantiation. Generated burdens
    are created ONLY by MRP, never predeclared."""
    b_mrp = payload.get("B_MRP")
    if not isinstance(b_mrp, list):
        return []

    errors: list[str] = []
    last_mrp = payload.get("last_mrp_resultant") or {}
    provenanced: set[str] = set()
    if isinstance(last_mrp, dict) and last_mrp.get("route_result_type") == "generated_burden_instantiation":
        for key in ("generated_by", "next_burden"):
            value = last_mrp.get(key)
            if isinstance(value, str) and value:
                provenanced.add(value)
        source = last_mrp.get("source")
        if isinstance(source, str) and source:
            provenanced.add(source)

    completed_acts = payload.get("completed_acts")
    if isinstance(completed_acts, list):
        for entry in completed_acts:
            if not isinstance(entry, dict):
                continue
            body_ref = entry.get("body_ref")
            if not isinstance(body_ref, str):
                continue
            burden_id = burden_id_from_body_ref(body_ref)
            if burden_id:
                provenanced.add(burden_id)
                provenanced.add(body_ref)

    for burden in b_mrp:
        if burden in provenanced:
            continue
        errors.append(
            f"{label}: generated burden {burden!r} in B_MRP has no MRP provenance "
            "(no matching completed_acts entry and no generated_burden_instantiation "
            "last_mrp_resultant naming it); generated burdens must be created only by MRP"
        )
    return errors


def burden_id_from_body_ref(body_ref: str) -> str:
    match = re.match(rf"^[{SUPERSCRIPT_DIGITS}]*(B[0-9]+)", body_ref)
    return match.group(1) if match else ""


def coverage_complete_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: coverage_complete=true requires held_set_H empty AND all
    B_total burdens present in terminal_states with a closed state. False
    coverage claims are a fail, not a warning."""
    if payload.get("coverage_complete") is not True:
        return []
    errors: list[str] = []
    held = payload.get("held_set_H")
    if isinstance(held, list) and held:
        errors.append(f"{label}: coverage_complete=true but held_set_H is non-empty (false coverage)")

    b_total = payload.get("B_total")
    terminal_states = payload.get("terminal_states")
    if isinstance(b_total, list) and isinstance(terminal_states, dict):
        for burden in b_total:
            state = terminal_states.get(burden)
            if state is None:
                errors.append(
                    f"{label}: coverage_complete=true but burden {burden!r} has no terminal_states entry "
                    "(false coverage)"
                )
            elif not is_closed_state(state):
                errors.append(
                    f"{label}: coverage_complete=true but burden {burden!r} terminal state {state!r} "
                    "is not closed (false coverage)"
                )
    return errors


def is_closed_state(state: Any) -> bool:
    """A state is closed iff it matches the controlled grammar
    ^(land|rejected|merged)\\b optionally followed by (...) and NOTHING ELSE
    except an optional trailing '+' (the artifact-prose Land(...)/rejected/
    merged family), OR it is an exact match against
    CLOSED_STAGE05_TERMINAL_STATES (the harness's separate Stage 05
    controlled terminal-state vocabulary, e.g. "landed"). A bare substring
    test ("marker in lowered") is defeated by qualifier suffixes
    (': PARTIAL', ': HOLD', '(pending') and compound words (landless,
    unmerged, Landmark, rejected-pending) -- all of which must NOT count as
    closed."""
    if not isinstance(state, str):
        return False
    stripped = state.strip()
    return bool(CLOSED_STATE_RE.match(stripped)) or stripped in CLOSED_STAGE05_TERMINAL_STATES


def partial_hold_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: hold_partial/PARTIAL states require next_required_action
    non-empty."""
    errors: list[str] = []
    is_partial = payload.get("route_result_type") == "hold_partial" or payload.get("coverage_complete") is False
    if not is_partial:
        return errors
    action = payload.get("next_required_action")
    if not (isinstance(action, str) and action.strip()):
        errors.append(
            f"{label}: coverage_complete=false/hold_partial requires a non-empty next_required_action"
        )
    return errors


def output_artifact_errors(label: str, payload: dict[str, Any]) -> list[str]:
    """Pure core: when output_artifact_path is set, output_sha256 must be
    present (non-null, non-empty) and output_offset_bytes >= 0 (schema already
    enforces >=0 when present as int; here we enforce the presence coupling)."""
    errors: list[str] = []
    path = payload.get("output_artifact_path")
    if path:
        sha = payload.get("output_sha256")
        if not (isinstance(sha, str) and sha):
            errors.append(f"{label}: output_artifact_path is set but output_sha256 is missing/empty")
        offset = payload.get("output_offset_bytes")
        if not (isinstance(offset, int) and not isinstance(offset, bool) and offset >= 0):
            errors.append(f"{label}: output_artifact_path is set but output_offset_bytes is missing/invalid")
    return errors


def capsule_size_errors(label: str, raw_bytes: bytes) -> tuple[list[str], list[str]]:
    """Return (warnings, failures) for capsule byte-size discipline."""
    size = len(raw_bytes)
    warnings: list[str] = []
    failures: list[str] = []
    if size > FAIL_BYTES:
        failures.append(f"{label}: capsule is {size} bytes, exceeds hard cap {FAIL_BYTES} bytes")
    elif size > WARN_BYTES:
        warnings.append(f"{label}: capsule is {size} bytes, exceeds warning threshold {WARN_BYTES} bytes")
    return warnings, failures


def validate_capsule_payload(label: str, payload: Any, schema: dict[str, Any]) -> list[str]:
    errors = structural_errors(label, payload, schema)
    if isinstance(payload, dict) and not errors:
        errors.extend(semantic_errors(label, payload))
    elif isinstance(payload, dict):
        # Still run semantic checks even with minor structural issues elsewhere,
        # as long as the core ledger fields are usable, to surface as many
        # independent problems as possible in one pass.
        core_present = all(key in payload for key in ("B_LA", "B_MRP", "B_total"))
        if core_present:
            errors.extend(semantic_errors(label, payload))
    return errors


def validate_capsule_file(path: Path, schema: dict[str, Any]) -> list[str]:
    payload, errors = load_json(path)
    if errors:
        return errors
    label = rel(path)
    errors = validate_capsule_payload(label, payload, schema)
    raw_bytes = path.read_bytes()
    warnings, failures = capsule_size_errors(label, raw_bytes)
    for warning in warnings:
        print(f"  WARNING: {warning}")
    errors.extend(failures)
    return errors


# ---------------------------------------------------------------------------
# Replay (ordered capsule sequence + artifact.md)
# ---------------------------------------------------------------------------

CAPSULE_NAME_RE = re.compile(r"^capsule-(\d+)\.json$")


def discover_capsule_sequence(directory: Path) -> list[Path]:
    entries = []
    for path in sorted(directory.glob("capsule-*.json")):
        match = CAPSULE_NAME_RE.match(path.name)
        if match:
            entries.append((int(match.group(1)), path))
    entries.sort(key=lambda item: item[0])
    return [path for _, path in entries]


def strip_fenced_code_blocks(text: str) -> str:
    """FIX 1: strip fenced code blocks (``` ... ```) before any ACT/Land
    substring or line-anchored parity check, so a token that appears ONLY
    inside a code fence (or a quotation reproduced verbatim in a fence)
    cannot be used to satisfy replay parity. Fences are replaced with
    newline-preserving blanks so line numbers / offsets used elsewhere in
    error messages are not disturbed by this pass."""
    def _blank(match: "re.Match[str]") -> str:
        return "\n" * match.group(0).count("\n")

    return FENCE_RE.sub(_blank, text)


SUP_SUB_TO_ASCII = str.maketrans(SUPERSCRIPT_DIGITS + SUBSCRIPT_DIGITS, "01234567890123456789")
_PUBLIC_SUBMOVE_TOKEN_RE = re.compile(rf"^([{SUPERSCRIPT_DIGITS}]+)B([{SUBSCRIPT_DIGITS}]+)$")
_PUBLIC_BURDEN_TOKEN_RE = re.compile(rf"^([{SUPERSCRIPT_DIGITS}]+)B$")


def normalize_burden_token(value: str) -> str:
    """G1: canonicalize a burden/body_ref/Land(...) token to the ASCII
    join-key form (`B1`, `B1_1`) so parity checks compare the SAME notation
    on both sides, regardless of which of the two harness-sanctioned
    surfaces produced it:
      - the capsule builder's ASCII join key (`B1_1`), and
      - the harness's own prompts/scaffolds/act_partition public Unicode
        surface (superscript burden digit before B, subscript submove
        digit after B: `¹B₁` == burden 1 submove 1; `¹B` == burden 1 with
        no submove).
    Independently mirrors tools/run_staged_current_skill_smoke.py's
    _capsule_bare_join_key_body_ref (that function converts at emission
    time when building a capsule; this one normalizes at validation time
    on both the capsule value AND whatever token appears in the artifact
    text) so this schema-adjacent checker does not import the harness
    module. Idempotent: B1_1 -> B1_1, ¹B₁ -> B1_1, ¹B -> B1, B1 -> B1.
    Unrecognized/malformed input is returned with only its literal
    superscript/subscript digits translated to ASCII, so a genuine
    mismatch still surfaces as a mismatch rather than being silently
    coerced into a false match."""
    text = (value or "").strip()
    match = _PUBLIC_SUBMOVE_TOKEN_RE.match(text)
    if match:
        burden = match.group(1).translate(SUP_SUB_TO_ASCII)
        submove = match.group(2).translate(SUP_SUB_TO_ASCII)
        return f"B{burden}_{submove}"
    match = _PUBLIC_BURDEN_TOKEN_RE.match(text)
    if match:
        return f"B{match.group(1).translate(SUP_SUB_TO_ASCII)}"
    return text.translate(SUP_SUB_TO_ASCII)


def act_row_lines(text: str) -> list[str]:
    """FIX 1: return only the lines of `text` that satisfy the real ACT-row
    grammar family (either the loose `ACT ... ::` row form or the compact
    `⟦ACT ...⟧` form), mirroring tools/run_staged_current_skill_smoke.py
    fixture-observed ACT rows and tools/check_act_surface_syntax.py's
    ACT_HEADING/compact-form parsing. A bare token mention elsewhere on a
    line (inside a code fence, a quotation, or a negated aside) does not
    qualify."""
    rows: list[str] = []
    for line in text.splitlines():
        if "ACT" not in line:
            continue
        if ACT_ROW_LOOSE_RE.match(line) or ACT_ROW_COMPACT_RE.search(line):
            rows.append(line)
    return rows


def _act_row_candidate_tokens(line: str) -> list[str]:
    """G1: extract the candidate body_ref tokens off an already-confirmed
    real ACT-row line -- the row-head token immediately after ACT/⟦ACT, and
    every explicit body_ref=<tok> field. These are the ONLY two places a
    body_ref legitimately appears on a real ACT row; a token elsewhere on
    the line does not count."""
    tokens: list[str] = []
    head_match = ACT_ROW_HEAD_TOKEN_RE.search(line)
    if head_match:
        tokens.append(head_match.group(1))
    tokens.extend(match.group(1) for match in ACT_ROW_BODY_REF_FIELD_RE.finditer(line))
    return tokens


def body_ref_has_act_row_parity(body_ref: str, act_lines: list[str]) -> bool:
    """FIX 1: body_ref must appear within a line matching the real ACT-row
    grammar, not merely anywhere in the artifact text (which is defeated by
    the token appearing only in a code fence, a quotation, or a negation).

    G1: comparison is by normalize_burden_token() EQUALITY against each
    candidate token extracted from the ACT-row line (the row-head token
    and/or the body_ref= field), not a raw substring test -- the capsule's
    ASCII join key (`B1_1`) and the harness's own public superscript/
    subscript surface (`¹B₁`) are the SAME token under two harness-
    sanctioned notations (schema/state-capsule.schema.json documents both).
    Equality (rather than "normalized body_ref in normalized line") also
    avoids a near-miss token like `B1_1` false-matching inside a longer
    token such as `B11_1`."""
    target = normalize_burden_token(body_ref)
    for line in act_lines:
        for token in _act_row_candidate_tokens(line):
            if normalize_burden_token(token) == target:
                return True
    return False


def land_token_has_row_parity(land_token: str, text_lines: list[str]) -> bool:
    """FIX 2 replay half: the Land(<burden>) token must appear on some line,
    and that line must not immediately suffix it with a qualifier such as
    ': PARTIAL' or ': HOLD' that would make the claim of closure false. This
    mirrors is_closed_state's grammar: after the Land(...) token, the line
    (once trimmed of a trailing '+') must not continue with a colon-qualifier
    before end of line/sentence.

    Literal-token primitive: `land_token` must be the exact `Land(<token>)`
    string to look for. See land_token_has_row_parity_for_burden() for the
    G1 normalized-notation analogue used by replay_sequence_errors."""
    suffix_re = re.compile(re.escape(land_token) + r"\)?\s*\+?\s*:\s*(PARTIAL|HOLD)\b", re.IGNORECASE)
    found = False
    for line in text_lines:
        if land_token not in line:
            continue
        found = True
        if suffix_re.search(line):
            return False
    return found


def any_land_token_for_burden(burden: str, text: str) -> bool:
    """G1: does `text` contain a Land(<token>) occurrence whose inner token
    normalizes (per normalize_burden_token) to the same burden id as
    `burden`? This is still whole-token (LAND_TOKEN_RE only captures the
    literal content between the parens of a real `Land(...)` occurrence,
    it does not do substring search across arbitrary text) and
    equality-based, so it satisfies a superscript artifact token like
    `Land(¹B)` against an ASCII capsule burden `B1` without reintroducing
    substring laundering."""
    target = normalize_burden_token(burden)
    return any(normalize_burden_token(match.group(1)) == target for match in LAND_TOKEN_RE.finditer(text))


def land_token_has_row_parity_for_burden(burden: str, text_lines: list[str]) -> bool:
    """G1: normalized-notation analogue of land_token_has_row_parity --
    checks every Land(...) occurrence, on every line, whose inner token
    normalizes to the same burden id (across BOTH the ASCII `Land(B1)` and
    superscript `Land(¹B)` surfaces), rather than a single literal string.
    Preserves the original semantics exactly for the pure-ASCII case (one
    literal token -> this degenerates to land_token_has_row_parity's
    behavior) and extends it, per-occurrence, to the superscript surface:
    at least one qualifying occurrence must exist, and any qualifying
    occurrence immediately suffixed with a PARTIAL/HOLD qualifier fails
    closure (mirrors is_closed_state's grammar)."""
    target = normalize_burden_token(burden)
    found = False
    for line in text_lines:
        for match in LAND_TOKEN_RE.finditer(line):
            if normalize_burden_token(match.group(1)) != target:
                continue
            found = True
            literal = f"Land({match.group(1)})"
            suffix_re = re.compile(re.escape(literal) + r"\)?\s*\+?\s*:\s*(PARTIAL|HOLD)\b", re.IGNORECASE)
            if suffix_re.search(line):
                return False
    return found


INITIAL_BURDEN_SET_RE = re.compile(r"Initial burden set:\s*\[([^\]]*)\]")
LEDGER_B_LA_RE = re.compile(r"(?:𝔅_LA|B_LA)\s*\(?[Bb]?_?LA\)?\s*=\s*\{([^}]*)\}")
SUP_TO_ASCII = str.maketrans(SUPERSCRIPT_DIGITS, "0123456789")


def parse_artifact_initial_burden_set(text: str) -> list[str] | None:
    """FIX 3: parse the artifact for an 'Initial burden set: [...]' line
    (and/or the ledger line with B_LA = {...}), normalizing both ASCII (B1)
    and Unicode superscript burden tokens the way the harness does. Returns
    None when the artifact carries no such line (fixtures without it stay
    valid / unaffected), else the ordered-unique list of burden ids found."""
    match = INITIAL_BURDEN_SET_RE.search(text)
    if match is None:
        match = LEDGER_B_LA_RE.search(text)
    if match is None:
        return None
    raw = match.group(1)
    tokens = re.findall(rf"[{SUPERSCRIPT_DIGITS}]*B[0-9]+(?:_[0-9]+)?", raw)
    normalized: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        ascii_token = token.translate(SUP_TO_ASCII)
        if ascii_token not in seen:
            seen.add(ascii_token)
            normalized.append(ascii_token)
    return normalized


def replay_errors(directory: Path, schema: dict[str, Any], artifact_path: Path | None = None) -> list[str]:
    """`artifact_path` defaults to `directory / "artifact.md"` (the fixture
    convention) for backward compatibility; callers with a real run's
    output.md living elsewhere (e.g. FIX 6's Stage-07 completion gate in
    tools/run_staged_current_skill_smoke.py) pass it explicitly instead of
    needing to copy/rename the artifact into the capsules directory."""
    if artifact_path is None:
        artifact_path = directory / "artifact.md"
    capsule_paths = discover_capsule_sequence(directory)

    if not capsule_paths:
        return [f"{rel(directory)}: no capsule-NNN.json files found"]
    if not artifact_path.is_file():
        return [f"{rel(directory)}: missing {rel(artifact_path)}"]

    artifact_bytes = artifact_path.read_bytes()
    artifact_text = artifact_bytes.decode("utf-8", errors="replace")

    capsules: list[dict[str, Any]] = []
    for index, path in enumerate(capsule_paths, start=1):
        payload, load_errs = load_json(path)
        if load_errs:
            return [f"{rel(directory)}: capsule index {index} ({rel(path)}): " + "; ".join(load_errs)]
        errs = validate_capsule_file(path, schema)
        if errs:
            return [f"{rel(directory)}: capsule index {index} ({rel(path)}): " + "; ".join(errs)]
        capsules.append(payload)

    errors = replay_sequence_errors(rel(directory), capsules, artifact_text, artifact_bytes)
    return errors


def replay_sequence_errors(
    label: str,
    capsules: list[dict[str, Any]],
    artifact_text: str,
    artifact_bytes: bytes,
) -> list[str]:
    """Pure core: cross-capsule replay invariants over an already-validated
    ordered capsule sequence. Fails with the earliest offending capsule index
    (1-based) + reason, per the mission's fail-fast contract."""
    if not capsules:
        return [f"{label}: empty capsule sequence"]

    case_id = capsules[0].get("case_id")
    fingerprint = capsules[0].get("input_fingerprint")

    # FIX 1: strip fenced code blocks before any ACT/Land substring or
    # line-anchored parity check, so a token appearing only inside a code
    # fence, a quotation, or a negated aside cannot satisfy replay parity.
    fence_stripped_text = strip_fenced_code_blocks(artifact_text)
    artifact_act_lines = act_row_lines(fence_stripped_text)
    fence_stripped_lines = fence_stripped_text.splitlines()

    # FIX 3: first-capsule B_LA ground truth. When the artifact states an
    # explicit initial burden set (either the prose 'Initial burden set:
    # [...]' line or the 𝔅_LA/B_LA = {...} ledger line), capsule-001's B_LA
    # must be a superset of it. Skip silently when the artifact carries no
    # such line at all (fixtures without it stay valid/unaffected).
    initial_burden_set = parse_artifact_initial_burden_set(fence_stripped_text)
    if initial_burden_set is not None:
        first_b_la = capsules[0].get("B_LA")
        first_b_la_set = set(first_b_la) if isinstance(first_b_la, list) else set()
        missing_initial = [b for b in initial_burden_set if b not in first_b_la_set]
        if missing_initial:
            return [
                f"{label}: capsule index 1: B_LA incomplete at first capsule vs artifact initial burden set "
                f"(missing {missing_initial}, artifact declares {initial_burden_set!r}, "
                f"capsule B_LA is {first_b_la!r})"
            ]

    prev_offset = -1
    prev_stage_index = -1
    prev_b_la: list[Any] = []
    prev_b_mrp: list[Any] = []
    prev_acts: list[Any] = []

    for index, capsule in enumerate(capsules, start=1):
        if capsule.get("case_id") != case_id:
            return [f"{label}: capsule index {index}: case_id drift ({capsule.get('case_id')!r} != {case_id!r})"]
        if capsule.get("input_fingerprint") != fingerprint:
            return [
                f"{label}: capsule index {index}: input_fingerprint drift "
                f"({capsule.get('input_fingerprint')!r} != {fingerprint!r})"
            ]

        stage = capsule.get("stage")
        stage_index = STAGE_INDEX.get(stage, -1)
        if stage_index < prev_stage_index:
            return [
                f"{label}: capsule index {index}: stage {stage!r} moves backward "
                f"(previous stage index {prev_stage_index})"
            ]
        prev_stage_index = stage_index

        offset = capsule.get("output_offset_bytes")
        if not isinstance(offset, int) or offset < prev_offset:
            return [
                f"{label}: capsule index {index}: output_offset_bytes {offset!r} is not "
                f"monotonic non-decreasing (previous {prev_offset})"
            ]
        prev_offset = offset

        b_la = capsule.get("B_LA") or []
        missing_la = [b for b in prev_b_la if b not in b_la]
        if missing_la:
            return [
                f"{label}: capsule index {index}: B_LA shrank; missing burden(s) {missing_la} "
                "present in a prior capsule (anti-slimming violation)"
            ]
        prev_b_la = list(b_la)

        b_mrp = capsule.get("B_MRP") or []
        if len(b_mrp) < len(prev_b_mrp) or b_mrp[: len(prev_b_mrp)] != prev_b_mrp:
            return [
                f"{label}: capsule index {index}: B_MRP is not append-only "
                f"(previous {prev_b_mrp!r}, current {b_mrp!r})"
            ]
        prev_b_mrp = list(b_mrp)

        acts = capsule.get("completed_acts") or []
        if len(acts) < len(prev_acts) or acts[: len(prev_acts)] != prev_acts:
            return [
                f"{label}: capsule index {index}: completed_acts is not append-only "
                "(earlier entries must be preserved verbatim)"
            ]
        prev_acts = list(acts)

        for entry in acts:
            body_ref = entry.get("body_ref") if isinstance(entry, dict) else None
            if isinstance(body_ref, str) and not body_ref_has_act_row_parity(body_ref, artifact_act_lines):
                return [
                    f"{label}: capsule index {index}: completed_acts body_ref {body_ref!r} "
                    "does not appear within a real ACT-row line in artifact.md (capsule-artifact parity "
                    "violation; fenced-code/quoted/negated mentions do not count)"
                ]

        terminal_states = capsule.get("terminal_states") or {}
        if isinstance(terminal_states, dict):
            for burden, state in terminal_states.items():
                if isinstance(state, str) and "land" in state.lower():
                    land_token = f"Land({burden})"
                    # G1: existence + row-parity are checked by normalized
                    # burden-token EQUALITY (any_land_token_for_burden /
                    # land_token_has_row_parity_for_burden), not a literal
                    # substring, so a superscript artifact token like
                    # `Land(¹B)` satisfies an ASCII capsule burden `B1`
                    # without reintroducing substring laundering (matching
                    # is still whole-token via LAND_TOKEN_RE).
                    if not any_land_token_for_burden(burden, fence_stripped_text):
                        return [
                            f"{label}: capsule index {index}: terminal_states burden {burden!r} "
                            f"marked Land but no {land_token!r} token (in either harness-sanctioned "
                            "burden notation) appears in artifact.md"
                        ]
                    if is_closed_state(state) and not land_token_has_row_parity_for_burden(
                        burden, fence_stripped_lines
                    ):
                        return [
                            f"{label}: capsule index {index}: terminal_states burden {burden!r} claims closed "
                            f"state {state!r} but the artifact line carrying its Land(...) token is suffixed "
                            "with a PARTIAL/HOLD qualifier (false coverage vs artifact replay)"
                        ]

    final = capsules[-1]
    final_offset = final.get("output_offset_bytes")
    if final_offset != len(artifact_bytes):
        return [
            f"{label}: capsule index {len(capsules)}: final output_offset_bytes {final_offset} "
            f"!= len(artifact.md bytes) {len(artifact_bytes)}"
        ]
    actual_sha = hashlib.sha256(artifact_bytes).hexdigest()
    final_sha = final.get("output_sha256")
    if final_sha != actual_sha:
        return [
            f"{label}: capsule index {len(capsules)}: final output_sha256 {final_sha!r} "
            f"!= sha256(artifact.md) {actual_sha!r}"
        ]

    return []


# ---------------------------------------------------------------------------
# CLI entrypoints
# ---------------------------------------------------------------------------

def run_capsule(path: Path, *, release_bearing: bool = False) -> int:
    errors = validate_capsule_file_dispatch(path, release_bearing=release_bearing)
    if errors:
        print(f"state-capsule --capsule {rel(path)}: FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"state-capsule --capsule {rel(path)}: PASS")
    return 0


def v2_replay_sequence_errors(paths: list[Path], capsules: list[dict[str, Any]]) -> list[str]:
    """Validate v2 replay as append-only evidence with frozen Stage02 custody."""
    if not capsules:
        return ["state-capsule-v2 replay: empty capsule sequence"]
    first = capsules[0]
    frozen_topology = {key: first.get(key) for key in (
        "trace_id", "source_commit", "topology_contract", "observation_units", "candidate_states",
        "input_pressures", "candidate_state_partitions", "burden_partition_decisions", "input_coverage",
        "selection_status", "selected_n_frame", "burden_floor", "stage02_freeze",
    )}
    prior_stage = -1
    seen_capsule_ids: set[str] = set()
    previous: dict[str, Any] | None = None
    phase_rank = {"ROUTED": 1, "EXECUTED": 2, "LANDED": 3, "REREAD_EVALUATED": 4}
    for index, (path, capsule) in enumerate(zip(paths, capsules), 1):
        capsule_id = str(capsule.get("capsule_id"))
        if capsule_id in seen_capsule_ids:
            return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation",
                f"duplicate replay capsule_id {capsule_id!r}")]
        seen_capsule_ids.add(capsule_id)
        stage = V2_STAGE_INDEX.get(str(capsule.get("stage")), -1)
        if stage < prior_stage:
            return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation", "replay stage regressed")]
        prior_stage = stage
        for key, frozen in frozen_topology.items():
            if capsule.get(key) != frozen:
                subcode = "b-la-late-append" if key in {"burden_floor", "stage02_freeze"} else "replay-history-mutation"
                failure_class = "stage02-input-pressure-coverage" if subcode == "b-la-late-append" else "state-capsule-custody"
                failure_stage = "02" if subcode == "b-la-late-append" else "05"
                return [_v2_diag(rel(path), failure_stage, failure_class, subcode,
                    f"frozen replay field {key} changed within trace {first.get('trace_id')!r}")]
        if index == 1:
            if capsule.get("previous_capsule_sha256") is not None:
                return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation",
                    "first replay capsule previous_capsule_sha256 must be null")]
        else:
            expected_previous = hashlib.sha256(paths[index - 2].read_bytes()).hexdigest()
            if capsule.get("previous_capsule_sha256") != expected_previous:
                return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation",
                    f"previous_capsule_sha256 mismatch; expected {expected_previous}")]
        if previous is not None:
            for collection, id_key in (("owner_routes", "obligation_id"), ("act_row_details", "obligation_id"),
                                       ("owner_execution_dispositions", "obligation_id"), ("operation_capsules", "capsule_id"),
                                       ("burden_cycles", "cycle_id")):
                old = _v2_map(previous.get(collection), id_key)
                new = _v2_map(capsule.get(collection), id_key)
                missing = sorted(set(old) - set(new))
                if missing:
                    return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation",
                        f"{collection} lost prior IDs {missing!r}")]
                for row_id, old_row in old.items():
                    new_row = new[row_id]
                    if collection in {"owner_routes", "act_row_details", "owner_execution_dispositions", "operation_capsules"} and new_row != old_row:
                        return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation",
                            f"immutable {collection} row {row_id!r} changed")]
                    if collection == "burden_cycles":
                        old_rank, new_rank = phase_rank[old_row["phase"]], phase_rank[new_row["phase"]]
                        if new_rank < old_rank:
                            return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation",
                                f"cycle {row_id} phase regressed")]
                        phase_fields = (("route_gradient", 1), ("obligation_ids", 1), ("obligation_set_sha256", 1),
                            ("operation_capsule_ids", 2), ("operation_events", 2), ("land", 3), ("post_land_delta", 3))
                        for field, rank in phase_fields:
                            if old_rank >= rank and new_row.get(field) != old_row.get(field):
                                return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation",
                                    f"cycle {row_id} mutated frozen phase evidence {field}")]
                        if old_rank >= 4:
                            old_raw = old_row["reread"]["raw_exit"]
                            new_raw = new_row["reread"]["raw_exit"]
                            old_candidates = old_raw.get("candidate_events", [])
                            new_candidates = new_raw.get("candidate_events", [])
                            if new_candidates[:len(old_candidates)] != old_candidates:
                                return [_v2_diag(rel(path), "05", "mrp", "candidate-transition-invalid",
                                    f"cycle {row_id} candidate-event history changed or disappeared")]
                            immutable_reread = {key: value for key, value in old_row["reread"].items() if key != "raw_exit"}
                            if {key: value for key, value in new_row["reread"].items() if key != "raw_exit"} != immutable_reread:
                                return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation",
                                    f"cycle {row_id} reread custody changed")]
                            old_raw_without_candidates = {key: value for key, value in old_raw.items() if key not in {"candidate_events", "raw_exit_sha256"}}
                            new_raw_without_candidates = {key: value for key, value in new_raw.items() if key not in {"candidate_events", "raw_exit_sha256"}}
                            if old_raw_without_candidates != new_raw_without_candidates:
                                return [_v2_diag(rel(path), "05", "state-capsule-custody", "replay-history-mutation",
                                    f"cycle {row_id} raw exit history changed")]
            if previous.get("closure_state", {}).get("closure_confirmed") is True:
                semantic_keys = ("owner_routes", "act_row_details", "owner_execution_dispositions", "operation_capsules",
                                 "burden_cycles", "reread_signature_history", "current_live_burdens", "held", "closure_state")
                changed = [key for key in semantic_keys if capsule.get(key) != previous.get(key)]
                if changed:
                    return [_v2_diag(rel(path), "07", "public-projection", "producer-oracle-mismatch",
                        f"terminal COMPLETE trace cannot append or mutate semantic events; changed {changed!r}")]
        previous = capsule
    return []


def replay_errors_dispatch(
    directory: Path,
    *,
    artifact_path: Path | None = None,
    release_bearing: bool = False,
) -> list[str]:
    paths = discover_capsule_sequence(directory)
    if not paths:
        return [f"{rel(directory)}: no capsule-NNN.json files found"]
    first, first_errors = load_json(paths[0])
    if first_errors:
        return first_errors
    if isinstance(first, dict) and first.get("schema") == SCHEMA_V2_CONST:
        capsules: list[dict[str, Any]] = []
        for index, path in enumerate(paths, start=1):
            payload, load_errors = load_json(path)
            if load_errors:
                return [f"{rel(directory)}: capsule index {index}: {'; '.join(load_errors)}"]
            errors = validate_capsule_file_dispatch(path, release_bearing=release_bearing)
            if errors:
                return [f"{rel(directory)}: capsule index {index}: {'; '.join(errors)}"]
            if not isinstance(payload, dict) or payload.get("schema") != SCHEMA_V2_CONST:
                return [f"{rel(path)}: mixed-schema-replay: v2 replay cannot contain another schema identity"]
            capsules.append(payload)
        return v2_replay_sequence_errors(paths, capsules)
    if release_bearing:
        return [
            f"{rel(paths[0])}: release-bearing-v1: {SCHEMA_CONST} is historical replay only; "
            f"new release-bearing execution requires {SCHEMA_V2_CONST}"
        ]
    return replay_errors(directory, load_schema(), artifact_path=artifact_path)


def run_replay(
    directory: Path,
    artifact_path: Path | None = None,
    *,
    release_bearing: bool = False,
) -> int:
    errors = replay_errors_dispatch(
        directory,
        artifact_path=artifact_path,
        release_bearing=release_bearing,
    )
    if errors:
        print(f"state-capsule --replay {rel(directory)}: FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"state-capsule --replay {rel(directory)}: PASS")
    return 0


# ---------------------------------------------------------------------------
# Self-test: embedded pure-core cases + fixture directory cases
# ---------------------------------------------------------------------------

def _base_capsule(**overrides: Any) -> dict[str, Any]:
    capsule: dict[str, Any] = {
        "schema": SCHEMA_CONST,
        "case_id": "case-001",
        "input_fingerprint": "sha256:" + ("a" * 64),
        "stage": "04",
        "n_frame": {"selected": "authority-order", "held_candidates": []},
        "live_registers": ["N", "m", "tau", "sigma"],
        "register_state": {"tau": "live per stage-02 diagnostic", "sigma": "live per stage-02 diagnostic"},
        "B_LA": ["B1", "B2"],
        "B_MRP": [],
        "B_total": ["B1", "B2"],
        "current_burden": "B1",
        "held_set_H": [],
        "completed_acts": [],
        "last_terminal": {"burden": None, "state": None},
        "last_delta": None,
        "last_mrp_resultant": {"source": None, "route_result_type": "none"},
        "route_result_type": "none",
        "field_diagnostics": {"divergence_state": "neutral", "curl_state": "null-state"},
        "transport": "chat",
        "terminal_states": {},
        "next_burden": "B2",
        "current_owner_route": {"burden": "B1", "owner_id": "M3", "shards": []},
        "coverage_complete": False,
        "next_required_action": "activate B1",
        "output_artifact_path": None,
        "output_sha256": None,
        "output_offset_bytes": 0,
        "cold_law_refs_used": [],
        "shards_loaded": [],
    }
    capsule.update(overrides)
    return capsule


def embedded_self_test_cases() -> list[tuple[str, bool]]:
    schema = load_schema()
    cases: list[tuple[str, bool]] = []

    good = _base_capsule()
    cases.append(("valid minimal capsule passes", validate_capsule_payload("t", good, schema) == []))

    missing_field = dict(good)
    del missing_field["stage"]
    cases.append((
        "missing required field fails",
        any("missing required" in e for e in structural_errors("t", missing_field, schema)),
    ))

    extra_field = dict(good)
    extra_field["bogus_extra_field"] = 1
    cases.append((
        "unknown top-level field fails",
        any("unknown top-level" in e for e in structural_errors("t", extra_field, schema)),
    ))

    bad_schema_const = dict(good)
    bad_schema_const["schema"] = "wrong-v1"
    cases.append((
        "wrong schema const fails",
        any("schema must be" in e for e in structural_errors("t", bad_schema_const, schema)),
    ))

    bad_fp = dict(good)
    bad_fp["input_fingerprint"] = "not-a-fingerprint"
    cases.append((
        "malformed input_fingerprint fails",
        any("input_fingerprint" in e for e in structural_errors("t", bad_fp, schema)),
    ))

    # B_total union invariant
    cases.append((
        "B_total union ok",
        union_errors("t", ["B1", "B2"], ["B3"], ["B1", "B2", "B3"]) == [],
    ))
    cases.append((
        "B_total union mismatch fails",
        any("not the order-preserving union" in e for e in union_errors("t", ["B1", "B2"], ["B3"], ["B1", "B3", "B2"])),
    ))
    cases.append((
        "B_total duplicate fails",
        any("duplicate" in e for e in union_errors("t", ["B1"], [], ["B1", "B1"])),
    ))

    # current_burden / next_burden membership
    bad_current = _base_capsule(current_burden="B9")
    cases.append((
        "current_burden outside B_total fails",
        any("current_burden" in e for e in semantic_errors("t", bad_current)),
    ))
    ok_terminal_current = _base_capsule(
        current_burden="B9", last_terminal={"burden": "B9", "state": "Land(B9)"}
    )
    cases.append((
        "current_burden matching explicit last_terminal passes",
        not any("current_burden" in e for e in semantic_errors("t", ok_terminal_current)),
    ))

    # MRP provenance
    no_provenance = _base_capsule(B_MRP=["B7"], B_total=["B1", "B2", "B7"])
    cases.append((
        "generated burden without MRP provenance fails",
        any("no MRP provenance" in e for e in mrp_provenance_errors("t", no_provenance)),
    ))
    with_provenance = _base_capsule(
        B_MRP=["B7"],
        B_total=["B1", "B2", "B7"],
        last_mrp_resultant={
            "source": "B2",
            "route_result_type": "generated_burden_instantiation",
            "generated_by": "B2",
            "next_burden": "B7",
        },
    )
    cases.append((
        "generated burden with last_mrp_resultant provenance passes",
        mrp_provenance_errors("t", with_provenance) == [],
    ))
    with_act_provenance = _base_capsule(
        B_MRP=["B7"],
        B_total=["B1", "B2", "B7"],
        completed_acts=[
            {
                "body_ref": "B7_1",
                "owner_id": "M3",
                "operation": "op",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B7)",
            }
        ],
    )
    cases.append((
        "generated burden with completed_acts provenance passes",
        mrp_provenance_errors("t", with_act_provenance) == [],
    ))

    # coverage_complete
    false_coverage_held = _base_capsule(coverage_complete=True, held_set_H=[{"burden": "B2", "reason": "r"}])
    cases.append((
        "coverage_complete=true with non-empty held_set_H fails",
        any("held_set_H" in e for e in coverage_complete_errors("t", false_coverage_held)),
    ))
    false_coverage_open = _base_capsule(
        coverage_complete=True,
        terminal_states={"B1": "Land(B1)"},
    )
    cases.append((
        "coverage_complete=true with unclosed/missing terminal burden fails",
        any("false coverage" in e for e in coverage_complete_errors("t", false_coverage_open)),
    ))
    true_coverage_ok = _base_capsule(
        coverage_complete=True,
        held_set_H=[],
        terminal_states={"B1": "Land(B1)", "B2": "Land(B2)"},
        next_required_action="",
    )
    cases.append((
        "coverage_complete=true with all closed passes",
        coverage_complete_errors("t", true_coverage_ok) == [],
    ))

    # partial hold / next_required_action
    partial_missing_action = _base_capsule(coverage_complete=False, next_required_action="")
    cases.append((
        "coverage_complete=false with empty next_required_action fails",
        any("next_required_action" in e for e in partial_hold_errors("t", partial_missing_action)),
    ))
    partial_with_action = _base_capsule(coverage_complete=False, next_required_action="resume B2")
    cases.append((
        "coverage_complete=false with non-empty next_required_action passes",
        partial_hold_errors("t", partial_with_action) == [],
    ))

    # body_ref pollution
    cases.append((
        "clean body_ref passes",
        body_ref_pollution_errors("t", "B1_1") == [],
    ))
    cases.append((
        "body_ref with bracket fails",
        any("polluted" in e for e in body_ref_pollution_errors("t", "B1[M3.op]")),
    ))
    cases.append((
        "body_ref with dot fails",
        any("polluted" in e for e in body_ref_pollution_errors("t", "B1.op")),
    ))
    cases.append((
        "unicode superscript body_ref passes",
        body_ref_pollution_errors("t", "¹B") == [] or body_ref_pollution_errors("t", "¹B1") == [],
    ))

    # output artifact coupling
    missing_sha = _base_capsule(output_artifact_path="out/artifact.md", output_sha256=None, output_offset_bytes=10)
    cases.append((
        "output_artifact_path without sha256 fails",
        any("output_sha256" in e for e in output_artifact_errors("t", missing_sha)),
    ))

    # size discipline
    warn_bytes = b"x" * (WARN_BYTES + 1)
    warnings, failures = capsule_size_errors("t", warn_bytes)
    cases.append(("capsule over warn threshold warns not fails", bool(warnings) and not failures))
    fail_bytes = b"x" * (FAIL_BYTES + 1)
    warnings2, failures2 = capsule_size_errors("t", fail_bytes)
    cases.append(("capsule over hard cap fails", bool(failures2)))

    # replay sequence invariants (pure core, synthetic)
    # NOTE: these lines must satisfy the real ACT-row grammar (FIX 1) --
    # "ACT <ref> ... :: ... " with a `::` field separator -- not just contain
    # the ACT/body_ref tokens anywhere, since replay parity is now anchored
    # to actual ACT rows.
    artifact_text = "ACT B1_1 :: op :: Land(B1)+\nACT B2_1 :: op :: Land(B2)+\n"
    artifact_bytes = artifact_text.encode("utf-8")
    cap1 = _base_capsule(
        stage="04",
        output_offset_bytes=0,
        output_artifact_path=None,
        output_sha256=None,
        completed_acts=[],
        terminal_states={},
    )
    cap2 = _base_capsule(
        stage="04",
        current_burden="B2",
        next_burden=None,
        output_offset_bytes=len(artifact_bytes),
        output_artifact_path="artifact.md",
        output_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
        completed_acts=[
            {
                "body_ref": "B1_1",
                "owner_id": "M3",
                "operation": "op",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B1)",
            },
            {
                "body_ref": "B2_1",
                "owner_id": "M3",
                "operation": "op",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B2)",
            },
        ],
        terminal_states={"B1": "Land(B1)", "B2": "Land(B2)"},
        coverage_complete=True,
        next_required_action="",
        held_set_H=[],
    )
    cases.append((
        "replay sequence: valid two-capsule sequence passes",
        replay_sequence_errors("t", [cap1, cap2], artifact_text, artifact_bytes) == [],
    ))

    cap2_bad_offset = dict(cap2)
    cap2_bad_offset["output_offset_bytes"] = 0
    cap1_high_offset = dict(cap1)
    cap1_high_offset["output_offset_bytes"] = 999
    cases.append((
        "replay sequence: non-monotonic offset fails",
        any(
            "not monotonic" in e
            for e in replay_sequence_errors("t", [cap1_high_offset, cap2_bad_offset], artifact_text, artifact_bytes)
        ),
    ))

    cap1_extra_la = dict(cap1)
    cap1_extra_la["B_LA"] = ["B1", "B2", "B3"]
    cap1_extra_la["B_total"] = ["B1", "B2", "B3"]
    cases.append((
        "replay sequence: B_LA shrink fails",
        any(
            "B_LA shrank" in e
            for e in replay_sequence_errors("t", [cap1_extra_la, cap2], artifact_text, artifact_bytes)
        ),
    ))

    # FIX 1: ACT parity anchoring -- a body_ref present ONLY inside a fenced
    # code block (or a bare mention outside the real ACT-row grammar) must
    # NOT satisfy replay parity.
    fenced_only_artifact = (
        "# Case\n\n"
        "Discussion of the format:\n"
        "```\nACT B1_1 :: example only, not a real row :: Land(B1)+\n```\n"
        "No real ACT row appears outside the fence.\n"
    )
    fenced_only_bytes = fenced_only_artifact.encode("utf-8")
    cap_fenced = _base_capsule(
        completed_acts=[
            {
                "body_ref": "B1_1",
                "owner_id": "M3",
                "operation": "op",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B1)",
            }
        ],
        output_offset_bytes=len(fenced_only_bytes),
        output_artifact_path="artifact.md",
        output_sha256=hashlib.sha256(fenced_only_bytes).hexdigest(),
    )
    cases.append((
        "replay sequence: body_ref only inside code fence fails",
        any(
            "does not appear within a real ACT-row line" in e
            for e in replay_sequence_errors("t", [cap_fenced], fenced_only_artifact, fenced_only_bytes)
        ),
    ))

    real_act_artifact = "# Case\n\nACT B1_1 :: M3.activation :: Land(B1)+\nLand(B1): closed.\n"
    real_act_bytes = real_act_artifact.encode("utf-8")
    cap_real_act = _base_capsule(
        completed_acts=[
            {
                "body_ref": "B1_1",
                "owner_id": "M3",
                "operation": "op",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B1)",
            }
        ],
        terminal_states={"B1": "Land(B1)"},
        output_offset_bytes=len(real_act_bytes),
        output_artifact_path="artifact.md",
        output_sha256=hashlib.sha256(real_act_bytes).hexdigest(),
    )
    cases.append((
        "replay sequence: body_ref inside real ACT row passes",
        replay_sequence_errors("t", [cap_real_act], real_act_artifact, real_act_bytes) == [],
    ))

    # G1: normalize_burden_token direct cases.
    cases.append(("normalize_burden_token: ASCII join key is idempotent", normalize_burden_token("B1_1") == "B1_1"))
    cases.append(("normalize_burden_token: bare ASCII burden is idempotent", normalize_burden_token("B1") == "B1"))
    cases.append(("normalize_burden_token: superscript+subscript submove", normalize_burden_token("¹B₁") == "B1_1"))
    cases.append(("normalize_burden_token: superscript bare burden", normalize_burden_token("¹B") == "B1"))
    cases.append((
        "normalize_burden_token: multi-digit superscript+subscript",
        normalize_burden_token("¹²B₃") == "B12_3",
    ))
    cases.append((
        "normalize_burden_token: distinct burdens stay distinct",
        normalize_burden_token("²B₁") != normalize_burden_token("B1_1"),
    ))

    # G1: superscript ACT row satisfies ASCII capsule body_ref (real-world
    # regression shape: harness renders `⟦ACT ¹B₁[...] :: ... body_ref=¹B₁
    # ... :: Land(¹B)+⟧`, capsule stores the ASCII join key `B1_1`).
    superscript_row_artifact = (
        "# Case\n\n"
        "⟦ACT ¹B₁[M3.activation] :: π=pressure :: body_ref=¹B₁ :: "
        "Δ=Δ¹B:uptake-recorded :: Land(¹B)+⟧\n"
        "Land(¹B): closed on sound-reason ground.\n"
    )
    superscript_row_bytes = superscript_row_artifact.encode("utf-8")
    cap_superscript_row = _base_capsule(
        completed_acts=[
            {
                "body_ref": "B1_1",
                "owner_id": "M3",
                "operation": "activation",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B1)",
            }
        ],
        terminal_states={"B1": "Land(B1)"},
        output_offset_bytes=len(superscript_row_bytes),
        output_artifact_path="artifact.md",
        output_sha256=hashlib.sha256(superscript_row_bytes).hexdigest(),
    )
    cases.append((
        "G1: superscript ACT row + ASCII capsule body_ref satisfies parity",
        replay_sequence_errors("t", [cap_superscript_row], superscript_row_artifact, superscript_row_bytes) == [],
    ))
    cases.append((
        "G1: superscript Land(<burden>) token satisfies ASCII terminal_states burden",
        any_land_token_for_burden("B1", superscript_row_artifact),
    ))
    cases.append((
        "G1: superscript Land(<burden>) token has row parity for ASCII burden",
        land_token_has_row_parity_for_burden("B1", superscript_row_artifact.splitlines()),
    ))

    # G1: body_ref genuinely absent still fails with the same message, even
    # though the artifact carries a superscript ACT row for a DIFFERENT
    # burden.
    superscript_absent_artifact = (
        "# Case\n\n⟦ACT ²B₁[M3.activation] :: π=pressure :: body_ref=²B₁ :: "
        "Δ=Δ²B:uptake-recorded :: Land(²B)+⟧\n"
    )
    superscript_absent_bytes = superscript_absent_artifact.encode("utf-8")
    cap_superscript_absent = _base_capsule(
        completed_acts=[
            {
                "body_ref": "B1_1",
                "owner_id": "M3",
                "operation": "activation",
                "register_axis": "xi",
                "delta_result": "d",
                "land": "Land(B1)",
            }
        ],
        output_offset_bytes=len(superscript_absent_bytes),
        output_artifact_path="artifact.md",
        output_sha256=hashlib.sha256(superscript_absent_bytes).hexdigest(),
    )
    cases.append((
        "G1: body_ref genuinely absent (different burden's superscript row present) still fails",
        any(
            "does not appear within a real ACT-row line" in e
            for e in replay_sequence_errors(
                "t", [cap_superscript_absent], superscript_absent_artifact, superscript_absent_bytes
            )
        ),
    ))

    # G1: near-miss token (capsule B1_1 vs row ONLY ²B₁, i.e. a different
    # burden's submove-1, not a genuine match) still fails -- guards against
    # normalized-substring laundering (equality, not "in", is required).
    cases.append((
        "G1: near-miss superscript token (different burden) does not satisfy parity",
        not body_ref_has_act_row_parity("B1_1", ["⟦ACT ²B₁[M3.op] :: body_ref=²B₁ :: Land(²B)+⟧"]),
    ))
    cases.append((
        "G1: near-miss ASCII substring token (B1_1 vs B11_1) does not satisfy parity",
        not body_ref_has_act_row_parity("B1_1", ["ACT B11_1 :: op :: Land(B11)+"]),
    ))

    # FIX 2: closed-state whole-token vocabulary.
    cases.append(("is_closed_state accepts bare Land(...)", is_closed_state("Land(B1)")))
    cases.append(("is_closed_state accepts bare Land(...)+", is_closed_state("Land(B1)+")))
    cases.append(("is_closed_state accepts rejected", is_closed_state("rejected")))
    cases.append(("is_closed_state accepts merged", is_closed_state("merged(B2)")))
    cases.append(("is_closed_state rejects PARTIAL suffix", not is_closed_state("Land(B2): PARTIAL")))
    cases.append(("is_closed_state rejects HOLD suffix", not is_closed_state("Land(B2): HOLD")))
    cases.append(("is_closed_state rejects compound landless", not is_closed_state("landless")))
    cases.append(("is_closed_state rejects compound Landmark", not is_closed_state("Landmark")))
    cases.append(("is_closed_state rejects compound unmerged", not is_closed_state("unmerged")))
    cases.append(("is_closed_state rejects rejected-pending", not is_closed_state("rejected-pending")))
    cases.append(("is_closed_state accepts Stage05 landed", is_closed_state("landed")))
    cases.append(("is_closed_state accepts Stage05 cleared", is_closed_state("cleared")))
    cases.append((
        "is_closed_state accepts Stage05 discharged-as-derivative",
        is_closed_state("discharged-as-derivative"),
    ))
    cases.append(("is_closed_state rejects Stage05 held-with-reason", not is_closed_state("held-with-reason")))
    cases.append(("is_closed_state rejects Stage05 carried-PARTIAL", not is_closed_state("carried-PARTIAL")))
    cases.append(("is_closed_state rejects Stage05 carried-RECURSE", not is_closed_state("carried-RECURSE")))

    # FIX 3: first-capsule B_LA ground truth vs artifact initial burden set.
    cases.append((
        "parse_artifact_initial_burden_set finds bracketed prose form",
        parse_artifact_initial_burden_set("Initial burden set: [B1, B2, B3]") == ["B1", "B2", "B3"],
    ))
    cases.append((
        "parse_artifact_initial_burden_set returns None when absent",
        parse_artifact_initial_burden_set("no such line here") is None,
    ))
    bla_incomplete_artifact = "Initial burden set: [B1, B2, B3]\nACT B1_1 :: Land(B1)+\n"
    bla_incomplete_bytes = bla_incomplete_artifact.encode("utf-8")
    cap_bla_incomplete = _base_capsule(
        B_LA=["B1"],
        B_total=["B1"],
        output_offset_bytes=len(bla_incomplete_bytes),
        output_artifact_path="artifact.md",
        output_sha256=hashlib.sha256(bla_incomplete_bytes).hexdigest(),
    )
    cases.append((
        "replay sequence: B_LA incomplete at first capsule vs artifact fails",
        any(
            "B_LA incomplete at first capsule" in e
            for e in replay_sequence_errors(
                "t", [cap_bla_incomplete], bla_incomplete_artifact, bla_incomplete_bytes
            )
        ),
    ))

    # FIX 4: register_state fidelity.
    cases.append((
        "register_state fidelity: complete registers pass",
        register_state_fidelity_errors(
            "t", _base_capsule(live_registers=["N", "m", "tau"], register_state={"tau": "x"})
        )
        == [],
    ))
    cases.append((
        "register_state fidelity: N/m/H exempt without entries",
        register_state_fidelity_errors(
            "t", _base_capsule(live_registers=["N", "m", "H"], register_state={})
        )
        == [],
    ))
    cases.append((
        "register_state fidelity: missing live register entry fails",
        any(
            "live register without register_state entry" in e
            for e in register_state_fidelity_errors(
                "t", _base_capsule(live_registers=["N", "m", "xi"], register_state={})
            )
        ),
    ))
    cases.append((
        "register_state fidelity: alias glyph key satisfies canonical name",
        register_state_fidelity_errors(
            "t", _base_capsule(live_registers=["tau"], register_state={"τ": "x"})
        )
        == [],
    ))

    # FIX 7: prose-smuggling bounds.
    long_action = "x" * 401
    cases.append((
        "next_required_action over 400 chars fails",
        any(
            "exceeds max 400" in e
            for e in structural_errors("t", _base_capsule(next_required_action=long_action), schema)
        ),
    ))
    cases.append((
        "next_required_action at 400 chars passes",
        not any(
            "exceeds max 400" in e
            for e in structural_errors("t", _base_capsule(next_required_action="x" * 400), schema)
        ),
    ))
    long_notes = "x" * 1201
    cases.append((
        "notes over 1200 chars fails",
        any(
            "exceeds max 1200" in e
            for e in structural_errors("t", _base_capsule(notes=long_notes), schema)
        ),
    ))

    return cases


def _write_fixture_capsule(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fixture_self_test(root: Path) -> tuple[list[str], int, int]:
    schema = load_schema()
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0

    valid_root = root / "valid"
    invalid_root = root / "invalid"

    # valid/multi-call-append and valid/partial-hold-resume: --replay style
    # directories (each contains capsule-NNN.json + artifact.md).
    for name in ("multi-call-append", "partial-hold-resume", "superscript-act-row-parity"):
        directory = valid_root / name
        if not directory.is_dir():
            errors.append(f"{rel(directory)}: expected valid replay fixture directory missing")
            continue
        found = replay_errors(directory, schema)
        if found:
            errors.extend(f"valid fixture {name} unexpectedly failed replay: {e}" for e in found)
        else:
            valid_checked += 1

    # valid/large-artifact-small-capsule: single-capsule fixture exercising a
    # large (>150KB) artifact with a small capsule; artifact generated inline
    # here rather than committed, per the mission's size-discipline judgment
    # call (committing 150KB is unreasonable for a fixture).
    large_dir = valid_root / "large-artifact-small-capsule"
    if not large_dir.is_dir():
        errors.append(f"{rel(large_dir)}: expected valid fixture directory missing")
    else:
        found = large_artifact_fixture_errors(large_dir, schema)
        if found:
            errors.extend(f"valid fixture large-artifact-small-capsule unexpectedly failed: {e}" for e in found)
        else:
            valid_checked += 1

    # invalid/*: each single-capsule fixture must fail for its own named reason.
    invalid_specs = {
        "offset-nonmonotonic": "not monotonic",
        "act-not-in-artifact": "does not appear within a real ACT-row line in artifact.md",
        "false-coverage-complete": "false coverage",
        "generated-burden-without-mrp-provenance": "no MRP provenance",
        "partial-without-next-action": "next_required_action",
        "bla-shrinks": "B_LA shrank",
        "body-ref-polluted": "polluted",
        "artifact-hash-mismatch": "output_sha256",
        "act-only-in-code-fence": "does not appear within a real ACT-row line in artifact.md",
        "false-coverage-partial-suffix": "false coverage",
        "closed-state-near-miss": "false coverage",
        "bla-incomplete-at-first-capsule": "B_LA incomplete at first capsule",
        "capsule-missing-live-register": "live register without register_state entry",
        "next-required-action-prose-smuggling": "exceeds max 400",
        "act-row-near-miss-different-burden": "does not appear within a real ACT-row line in artifact.md",
    }
    for name, expected_substring in invalid_specs.items():
        directory = invalid_root / name
        if not directory.is_dir():
            errors.append(f"{rel(directory)}: expected invalid fixture directory missing")
            continue
        found = replay_errors(directory, schema) if (directory / "artifact.md").is_file() else None
        if found is None:
            capsule_path = directory / "capsule-001.json"
            if not capsule_path.is_file():
                errors.append(f"{rel(directory)}: no capsule-001.json or artifact.md found")
                continue
            found = validate_capsule_file(capsule_path, schema)
        if not found:
            errors.append(f"invalid fixture {name} unexpectedly passed")
            continue
        blob = "\n".join(found)
        if expected_substring not in blob:
            errors.append(
                f"invalid fixture {name} failed for the wrong reason; expected substring "
                f"{expected_substring!r} not found in: {blob}"
            )
        else:
            invalid_checked += 1

    return errors, valid_checked, invalid_checked


def large_artifact_fixture_errors(directory: Path, schema: dict[str, Any]) -> list[str]:
    """valid/large-artifact-small-capsule ships a small capsule.json + a
    generator note; the >150KB artifact.md is synthesized here in a temp
    location rather than committed to the repo."""
    capsule_path = directory / "capsule-001.json"
    payload, errs = load_json(capsule_path)
    if errs:
        return errs
    label = rel(capsule_path)
    errors = validate_capsule_file(capsule_path, schema)
    if errors:
        return errors

    # Synthesize a >150KB artifact body containing the recorded ACT/Land
    # tokens so capsule-artifact parity can be exercised without committing
    # a large fixture file.
    filler = ("x" * 200 + "\n") * 800  # ~160KB of filler
    acts = payload.get("completed_acts") or []
    act_lines = "\n".join(
        f"ACT {entry.get('body_ref')} :: {entry.get('land')}" for entry in acts if isinstance(entry, dict)
    )
    artifact_text = filler + act_lines + "\n"
    artifact_bytes = artifact_text.encode("utf-8")
    if len(artifact_bytes) <= 150_000:
        return [f"{label}: generated inline artifact is not >150KB ({len(artifact_bytes)} bytes)"]

    expected_offset = payload.get("output_offset_bytes")
    expected_sha = payload.get("output_sha256")
    actual_sha = hashlib.sha256(artifact_bytes).hexdigest()

    # The fixture capsule's output_offset_bytes/output_sha256 are pinned to
    # match this generator's deterministic output; if the generator ever
    # changes, the fixture capsule must be regenerated to match.
    local_errors: list[str] = []
    if expected_offset != len(artifact_bytes):
        local_errors.append(
            f"{label}: fixture output_offset_bytes {expected_offset} != generated artifact length "
            f"{len(artifact_bytes)}"
        )
    if expected_sha != actual_sha:
        local_errors.append(f"{label}: fixture output_sha256 {expected_sha!r} != generated sha256 {actual_sha!r}")
    return local_errors


def v2_fixture_self_test(root: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []
    valid_checked = 0
    invalid_checked = 0
    expectation_schema = json.loads(NEGATIVE_EXPECTATION_SCHEMA_PATH.read_text(encoding="utf-8"))

    valid_dir = root / "valid"
    for fixture in sorted(valid_dir.glob("*.json")):
        valid_checked += 1
        found = validate_capsule_file_dispatch(fixture, release_bearing=True)
        if found:
            errors.extend(f"v2 valid fixture {fixture.name} unexpectedly failed: {item}" for item in found)

    invalid_dir = root / "invalid"
    fixture_paths = sorted(
        path for path in invalid_dir.glob("*.json") if not path.name.endswith(".expectation.json")
    )
    expectation_paths = sorted(invalid_dir.glob("*.expectation.json"))
    expected_sidecars = {path.with_name(path.stem + ".expectation.json") for path in fixture_paths}
    orphan_sidecars = sorted(set(expectation_paths) - expected_sidecars)
    missing_sidecars = sorted(expected_sidecars - set(expectation_paths))
    for path in missing_sidecars:
        errors.append(f"v2 invalid fixture is missing canonical sidecar: {rel(path)}")
    for path in orphan_sidecars:
        errors.append(f"v2 expectation has no same-stem fixture: {rel(path)}")

    for fixture in fixture_paths:
        invalid_checked += 1
        sidecar = fixture.with_name(fixture.stem + ".expectation.json")
        if not sidecar.is_file():
            continue
        expectation, load_errors = load_json(sidecar)
        if load_errors:
            errors.extend(load_errors)
            continue
        shape_errors = json_schema_errors(rel(sidecar), expectation, expectation_schema)
        if shape_errors:
            errors.extend(f"canonical expectation shape failed: {item}" for item in shape_errors)
            continue
        if not isinstance(expectation, dict):
            errors.append(f"{rel(sidecar)}: expectation must be an object")
            continue
        if expectation.get("fixture") != fixture.name:
            errors.append(
                f"{rel(sidecar)}: fixture field {expectation.get('fixture')!r} does not equal {fixture.name!r}"
            )
        if expectation.get("expected_checker_id") != "state-capsule":
            errors.append(f"{rel(sidecar)}: expected_checker_id must be 'state-capsule'")
        if expectation.get("expected_exit_code") != 1:
            errors.append(f"{rel(sidecar)}: state-capsule invalid fixtures must expect exit code 1")
        if not isinstance(expectation.get("expected_failure_subcode"), str) or not expectation["expected_failure_subcode"]:
            errors.append(f"{rel(sidecar)}: expected_failure_subcode is required by the state-capsule-v2 fixture lattice")

        found = validate_capsule_file_dispatch(fixture, release_bearing=True)
        if not found:
            errors.append(f"v2 invalid fixture {fixture.name} unexpectedly passed")
            continue
        diagnostic = "\n".join(found)
        failure_class = str(expectation.get("expected_failure_class"))
        failure_subcode = str(expectation.get("expected_failure_subcode"))
        earliest_stage = str(expectation.get("expected_earliest_stage"))
        if failure_class not in diagnostic:
            errors.append(
                f"v2 invalid fixture {fixture.name} failed for wrong class; expected {failure_class!r}, got {diagnostic!r}"
            )
        if failure_subcode not in diagnostic:
            errors.append(
                f"v2 invalid fixture {fixture.name} failed for wrong subcode; expected {failure_subcode!r}, got {diagnostic!r}"
            )
        if f"stage={earliest_stage}" not in diagnostic:
            errors.append(
                f"v2 invalid fixture {fixture.name} failed at wrong stage; expected {earliest_stage!r}, got {diagnostic!r}"
            )
        for marker in expectation.get("required_diagnostic_markers", []):
            if str(marker).lower() not in diagnostic.lower():
                errors.append(
                    f"v2 invalid fixture {fixture.name} missing diagnostic marker {marker!r}; got {diagnostic!r}"
                )

    historical = invalid_dir / "release-bearing-v1.json"
    historical_errors = validate_capsule_file_dispatch(historical, release_bearing=False)
    if historical_errors:
        errors.extend(f"historical v1 control unexpectedly failed: {item}" for item in historical_errors)
    return errors, valid_checked, invalid_checked


def self_test() -> int:
    cases = embedded_self_test_cases()
    ok = True
    for name, passed in cases:
        print(f"  self-test {'PASS' if passed else 'FAIL'}: {name}")
        ok = ok and passed

    fixture_errors, valid_checked, invalid_checked = fixture_self_test(FIXTURE_ROOT)
    for error in fixture_errors:
        print(f"  self-test FAIL: {error}")
    ok = ok and not fixture_errors

    v2_errors, v2_valid_checked, v2_invalid_checked = v2_fixture_self_test(V2_FIXTURE_ROOT)
    for error in v2_errors:
        print(f"  self-test FAIL: {error}")
    ok = ok and not v2_errors

    print(
        f"state-capsule self-test: {'PASS' if ok else 'FAIL'} "
        f"({len(cases)} embedded case(s), {valid_checked} v1 valid fixture(s), {invalid_checked} v1 invalid fixture(s), "
        f"{v2_valid_checked} v2 valid fixture(s), {v2_invalid_checked} v2 invalid fixture(s))"
    )
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--capsule", type=Path, help="Validate a single capsule JSON file")
    group.add_argument("--replay", type=Path, help="Validate an ordered capsule sequence directory + artifact.md")
    group.add_argument("--self-test", action="store_true", help="Run embedded + fixture self-tests")
    parser.add_argument(
        "--artifact",
        type=Path,
        default=None,
        help=(
            "With --replay: explicit path to the artifact/output.md to replay against, "
            "overriding the default of <replay-dir>/artifact.md (for real runs whose "
            "output.md lives alongside the case, not inside the capsules directory)."
        ),
    )
    parser.add_argument(
        "--release-bearing",
        action="store_true",
        help=(
            "Require the composed daee-state-capsule-v2 contract. Historical v1 remains readable "
            "without this flag but cannot satisfy a new release-bearing execution."
        ),
    )
    args = parser.parse_args()

    if args.artifact is not None and args.replay is None:
        parser.error("--artifact is only valid together with --replay")
    if args.release_bearing and args.self_test:
        parser.error("--release-bearing is only valid together with --capsule or --replay")

    if args.self_test:
        return self_test()
    if args.capsule is not None:
        return run_capsule(args.capsule, release_bearing=args.release_bearing)
    return run_replay(args.replay, artifact_path=args.artifact, release_bearing=args.release_bearing)


if __name__ == "__main__":
    sys.exit(main())
